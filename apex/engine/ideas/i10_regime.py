"""Market regime (owner, 28 Oct: keep an idea of whether the market is trending, sideways or breaking out).

Spot only (futures if spot is missing), all causal:
  ER15      Kaufman efficiency ratio over the last 15 min on 30-s samples: |net move| / sum |30-s moves| (0..1)
  anchor    running time-weighted mean of spot since the card's first second (from 09:15 when the engine starts on
            time) -- a "VWAP-like" anchor; spot has no volume
  xings     crossings of the anchor in the last 30 min, 30-s samples, 3-pt band (as R3-02 features.py)
  rng ratio last-15-min high-low vs the median 15-min range so far today (sampled each minute)

Labels with threshold hysteresis + a confirm time + a minimum hold so a label lasts minutes:
  BREAKOUT UP/DOWN  range >= 1.5x typical, ER15 >= 0.45, spot at the 15-min extreme
  TREND UP/DOWN     ER15 >= 0.40 (stays while >= 0.28), net 15-min move and spot vs anchor on the same side
  CHOP              >= 4 anchor crossings in 30 min with a normal-or-wide range, or ER15 < 0.20 with a wide range
  RANGE             the rest (low efficiency, ordinary/small range)
"""
import bisect
import math
from collections import deque

import numpy as np

NAME = "regime"
TITLE = "Market regime (ER15)"
IDEA = "Keep an idea of the regime: trend up / trend down / range / chop / breakout, from spot alone."
VERDICT = ("Rejected as a gate 28 Oct (R3-02): regime vetoes lost ~Rs 2 L on 7 days; pullback entries run against "
           "the trend by design. Display only.")
EVERY_S = 5

ER_TREND_IN, ER_TREND_OUT = 0.40, 0.28
ER_BO_IN, ER_BO_OUT = 0.45, 0.30
RNG_BO_IN, RNG_BO_OUT = 1.5, 1.2
ER_CHOP = 0.20
XING_BAND = 3.0
CHOP_XINGS = 4
CONFIRM_S = 60          # a new label must hold this long before it is shown
CONFIRM_BO_S = 20       # breakouts are shown faster
MIN_HOLD_S = 180        # a shown label stays at least this long (breakouts may cut in)
MAX_ALERTS = 8


def _fin(x):
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x)


class Idea:
    def __init__(self):
        self.key = None
        self.sum = {}            # key -> [sum, count, last t]
        self.dev_side = 0
        self.xs = deque()        # crossing times
        self.last_xs = None
        self.ranges = []         # 15-min ranges, one per minute (kept sorted)
        self.last_rng_t = None
        self.label = None
        self.since_t = None
        self.cand = None
        self.cand_t = None
        self.alerts = 0

    # ── anchor ───────────────────────────────────────────────────────────
    def _anchor(self, env, key):
        a = self.sum.get(key)
        T, V = env.hist.series(key, since=a[2] if a else None)
        if a is None:
            a = self.sum[key] = [0.0, 0, -1e18]
        if len(T):
            ok = np.isfinite(V)
            a[0] += float(V[ok].sum())
            a[1] += int(ok.sum())
            a[2] = float(T[-1])
        return a[0] / a[1] if a[1] else math.nan

    def update(self, env):
        now = env.t
        ka = self._anchor(env, "SPOT")
        kf = self._anchor(env, "FUT")
        # spot first; futures only if spot is missing for > 30 s
        key = "SPOT" if _fin(env.spot) or (self.key == "SPOT" and now - self.sum.get("SPOT", [0, 0, -1e18])[2] < 30) \
            else "FUT"
        if key != self.key:
            self.key = key
            self.dev_side, self.xs, self.last_xs = 0, deque(), None
            self.ranges, self.last_rng_t = [], None
        anchor = ka if key == "SPOT" else kf
        T, S = env.hist.series(key, secs=900)
        ok = np.isfinite(S)
        T, S = T[ok], S[ok]
        if len(S) < 60 or not _fin(anchor):
            return {"state": "WARMING", "text": "needs spot"}
        px = float(S[-1])
        dev = px - anchor

        # anchor crossings on 30-s samples with a 3-pt band
        if self.last_xs is None or now - self.last_xs >= 30:
            self.last_xs = now
            s = 1 if dev > XING_BAND else -1 if dev < -XING_BAND else self.dev_side
            if s != self.dev_side and self.dev_side != 0:
                self.xs.append(now)
            self.dev_side = s
        while self.xs and now - self.xs[0] > 1800:
            self.xs.popleft()
        xings = len(self.xs)

        span = T[-1] - T[0]
        if span < 840:
            return {"state": "WARMING", "value": None,
                    "text": f"{span / 60:.0f} of 15 min of spot; anchor {anchor:,.0f}, spot {dev:+.0f} pts from it"}

        # 15-min range, and its typical size today
        hi, lo = float(S.max()), float(S.min())
        rng = hi - lo
        if self.last_rng_t is None or now - self.last_rng_t >= 60:
            self.last_rng_t = now
            bisect.insort(self.ranges, rng)
        n = len(self.ranges)
        typ = 0.5 * (self.ranges[(n - 1) // 2] + self.ranges[n // 2]) if n >= 5 else math.nan
        ratio = rng / typ if _fin(typ) and typ > 0 else math.nan

        # ER15 on 30-s samples ending now
        smp = S[::-1][::30][::-1]
        path = float(np.abs(np.diff(smp)).sum())
        net = float(smp[-1] - smp[0])
        er = abs(net) / path if path > 0 else 0.0
        d = 1 if net > 0 else -1

        cur = self.label or ""
        bo_er = ER_BO_OUT if cur.startswith("BREAKOUT") else ER_BO_IN
        bo_rng = RNG_BO_OUT if cur.startswith("BREAKOUT") else RNG_BO_IN
        tr_er = ER_TREND_OUT if (cur.startswith("TREND") or cur.startswith("BREAKOUT")) else ER_TREND_IN
        at_ext = (hi - px) <= 0.2 * rng if d > 0 else (px - lo) <= 0.2 * rng
        if _fin(ratio) and ratio >= bo_rng and er >= bo_er and at_ext:
            raw = "BREAKOUT UP" if d > 0 else "BREAKOUT DOWN"
        elif er >= tr_er and d * dev > 0:
            raw = "TREND UP" if d > 0 else "TREND DOWN"
        elif (xings >= CHOP_XINGS and not (ratio < 0.8)) or (er < ER_CHOP and _fin(ratio) and ratio >= 1.2):
            raw = "CHOP"
        else:
            raw = "RANGE"

        # confirm + minimum hold
        alert = False
        if self.label is None:
            self.label, self.since_t = raw, now
        elif raw == self.label:
            self.cand = None
        else:
            if raw != self.cand:
                self.cand, self.cand_t = raw, now
            bo = raw.startswith("BREAKOUT")
            need = CONFIRM_BO_S if bo else CONFIRM_S
            held = now - self.since_t
            if now - self.cand_t >= need and (bo or held >= MIN_HOLD_S):
                self.label, self.since_t, self.cand = raw, now, None
                if bo and self.alerts < MAX_ALERTS:
                    self.alerts += 1
                    alert = True
        lab = self.label
        side = "CE" if lab.endswith("UP") else "PE" if lab.endswith("DOWN") else None
        rtxt = f"{ratio:.1f}x typical" if _fin(ratio) else "typical n/a"
        text = (f"ER15 {er:.2f}, 15m {net:+.0f} pts, range {rng:.0f} ({rtxt}), {xings} anchor crossings/30m, "
                f"spot {dev:+.0f} vs anchor {anchor:,.0f}")
        plan = ""
        if lab.startswith("BREAKOUT"):
            plan = f"breakout {'above' if d > 0 else 'below'} {hi if d > 0 else lo:,.0f}; fades if ER15 < {ER_BO_OUT}"
        elif lab.startswith("TREND"):
            plan = f"trend holds while ER15 >= {ER_TREND_OUT} and spot stays {'above' if dev > 0 else 'below'} anchor"
        elif lab == "RANGE" and _fin(typ):
            plan = f"15m box {lo:,.0f}-{hi:,.0f}; breakout needs range > {RNG_BO_IN * typ:.0f} pts"
        if self.cand and self.cand != lab:
            plan = (plan + f" | turning {self.cand}?")[:80] if plan else f"turning {self.cand}?"
        return {"state": lab, "side": side, "value": er, "unit": "ER15", "text": text, "plan": plan, "alert": alert}
