"""
Market regime (D-069) — what kind of market is the trigger firing into?

External review (ChatGPT, "Apex v2"): the trigger recognises MOVEMENT, but the same impulse
means different things in a trending, a breaking-out, a range-bound, a compressed or an
exhausted market. This module labels the market at 1 Hz using ONLY information available at
that second (no look-ahead), from five session-aware features of the Nifty futures and the
heavyweight basket:

  ER5      efficiency over 5 min = |P_t - P_t-300| / sum |dP|, on 15-s samples (20 steps).
           1 = straight line, 0 = pure back-and-forth.                    (Kaufman efficiency ratio)
           Sampled, not 1-s: at 1 s the bid/ask bounce dominates the path and even a random walk
           scores ~0.07, so everything would read RANGE. On 20 steps a pure random walk scores
           ER = |Z| x 0.28 (mean ~0.22): ER >= 0.35 happens ~21 % of the time by chance, ER < 0.20
           ~52 %. The thresholds below are set against that baseline.
  ER1      the same over 60 s on 5-s samples (12 steps) — is the move still making progress now?
  rv_pct   percentile of the 5-min realised path length (sum |dP|) within today's own history
  ext_pct  percentile of |futures - session VWAP| within today's own history
  breadth  share of heavyweight index weight whose 5-min move agrees with the futures' 5-min move
  broke    futures beyond the high/low of the 30 minutes that ended 5 minutes ago

States, first match wins (thresholds pre-registered here, 17 Oct 2026; never tuned intraday):
  WARMING      < 10 min of session data
  EXHAUSTION   ext_pct >= 90 and ER1 < 0.25         extended far from VWAP, progress has stalled
  BREAKOUT     broke and ER5 >= 0.35 and rv_pct >= 60   escaping the recent range with energy
  DIRECTIONAL  ER5 >= 0.35 and breadth >= 0.60       a clean move the basket confirms
  COMPRESSION  rv_pct <= 25 and ER5 < 0.35           quiet and contracting
  RANGE        ER5 < 0.20                            back-and-forth, no progress
  UNCERTAIN    anything else (e.g. progress without breadth)

It is ADVISORY (D-033): advisor `regime` vetoes RANGE / COMPRESSION / EXHAUSTION / UNCERTAIN /
WARMING and any DIRECTIONAL or BREAKOUT pointing the other way. It earns a vote only through
the learning loop's gated-book test (D-067). Every trade and every candidate carries the label,
so the report shows results BY REGIME — the main use from day one.
"""
from collections import deque

import numpy as np


WIN5, WIN1, RANGE_LOOK, RANGE_GAP = 300, 60, 30 * 60, 5 * 60
STEP5, STEP1 = 15, 5           # sampling for the efficiency ratios (see ER5 above)
WARM_S = 10 * 60
STATES = ("WARMING", "EXHAUSTION", "BREAKOUT", "DIRECTIONAL", "COMPRESSION", "RANGE", "UNCERTAIN")
VETO_ANY = {"WARMING", "EXHAUSTION", "COMPRESSION", "RANGE", "UNCERTAIN"}


def _pct(hist, x):
    """Percentile (0-100) of x within hist; None until 60 samples exist."""
    if len(hist) < 60 or x is None:
        return None
    a = np.fromiter(hist, float)
    return float(100.0 * np.mean(a <= x))


class Regime:
    def __init__(self):
        self.last_s = None
        self.t0 = None
        self.fut = deque(maxlen=RANGE_LOOK + RANGE_GAP + 5)      # (t, price) at 1 Hz
        self.stk = deque(maxlen=WIN5 + 5)                         # (t, price array)
        self.rv_hist, self.ext_hist = [], []
        self.pv = self.vol = 0.0
        self.last_ttq = None
        self.state, self.dir, self.f = "WARMING", 0, {}
        self.warm_until = None     # after a gap: WARMING until the 5-min windows are full again

    def after_gap(self):
        """A data gap just lifted: drop the price windows so no 5-min feature spans the jump.
        The session VWAP and today's percentile histories are kept (they are not windows)."""
        self.fut.clear()
        self.stk.clear()
        self.warm_until = (self.last_s or 0.0) + WIN5

    def update(self, now_s, fut, fut_ttq, stk_px, stk_w, live=True, in_session=True):
        """Call every engine step; works at 1 Hz. live=False during a data blackout (no learning)."""
        if self.last_s is not None and now_s - self.last_s < 1.0:
            return
        self.last_s = now_s
        if not in_session or not live or fut is None or not np.isfinite(fut):
            return
        if self.t0 is None:
            self.t0 = now_s
        # session VWAP from cumulative traded quantity
        if fut_ttq is not None and np.isfinite(fut_ttq):
            if self.last_ttq is not None and fut_ttq > self.last_ttq:
                dv = fut_ttq - self.last_ttq
                self.pv += fut * dv
                self.vol += dv
            self.last_ttq = fut_ttq
        self.fut.append((now_s, float(fut)))
        if stk_px is not None and len(stk_px):
            a = np.asarray(stk_px, float)
            self.stk.append((now_s, np.where(a > 0, a, np.nan)))      # 0 = no quote yet, not −100 %
        self._classify(now_s, stk_w)

    def _classify(self, now_s, stk_w):
        px = [p for _, p in self.fut]
        f = {}
        if len(px) >= 2:
            p5 = px[-WIN5 - 1:][::-1][::STEP5][::-1]            # 15-s samples ending now
            path5 = float(np.sum(np.abs(np.diff(p5)))) if len(p5) >= 2 else 0.0
            f["move5"] = p5[-1] - p5[0]
            f["er5"] = abs(f["move5"]) / path5 if path5 > 0 else 0.0
            p1 = px[-WIN1 - 1:][::-1][::STEP1][::-1]            # 5-s samples ending now
            path1 = float(np.sum(np.abs(np.diff(p1)))) if len(p1) >= 2 else 0.0
            f["er1"] = abs(p1[-1] - p1[0]) / path1 if path1 > 0 else 0.0
            f["rv5"] = path5
            vwap = self.pv / self.vol if self.vol > 0 else None
            f["vwap"] = vwap
            f["ext"] = (px[-1] - vwap) if vwap else None
            f["rv_pct"] = _pct(self.rv_hist, path5)
            f["ext_pct"] = _pct(self.ext_hist, abs(f["ext"]) if f["ext"] is not None else None)
            if len(p5) > (WIN5 // STEP5) // 2:
                self.rv_hist.append(path5)
            if f["ext"] is not None:
                self.ext_hist.append(abs(f["ext"]))
            # range of the 30 min that ended 5 min ago
            old = [p for t, p in self.fut if now_s - RANGE_LOOK - RANGE_GAP <= t <= now_s - RANGE_GAP]
            f["broke"] = 0
            if len(old) >= RANGE_LOOK // 2:
                hi, lo = max(old), min(old)
                f["range_hi"], f["range_lo"] = hi, lo
                f["broke"] = 1 if px[-1] > hi else (-1 if px[-1] < lo else 0)
            # breadth: heavyweight weight agreeing with the futures' 5-min direction
            f["breadth"] = None
            if len(self.stk) >= 2 and stk_w is not None and len(stk_w):
                (_, a0), (_, a1) = self.stk[0], self.stk[-1]
                with np.errstate(divide="ignore", invalid="ignore"):
                    ch = a1 / a0 - 1.0
                ok = np.isfinite(ch)
                w = np.asarray(stk_w, float)
                d = np.sign(f["move5"])
                if ok.any() and d != 0 and w[ok].sum() > 0:
                    f["breadth"] = float(w[ok & (np.sign(ch) == d)].sum() / w[ok].sum())
        self.f = f
        self.dir = int(np.sign(f.get("move5", 0.0)))
        if self.warm_until is not None and now_s < self.warm_until:
            self.state = "WARMING"
            return
        self.state = self.label(f, now_s - (self.t0 or now_s))

    @staticmethod
    def label(f, elapsed_s):
        if elapsed_s < WARM_S or "er5" not in f:
            return "WARMING"
        er5, er1 = f["er5"], f["er1"]
        rv, ext, br = f.get("rv_pct"), f.get("ext_pct"), f.get("breadth")
        if ext is not None and ext >= 90 and er1 < 0.25:
            return "EXHAUSTION"
        if f.get("broke") and er5 >= 0.35 and rv is not None and rv >= 60:
            return "BREAKOUT"
        if er5 >= 0.35 and br is not None and br >= 0.60:
            return "DIRECTIONAL"
        if rv is not None and rv <= 25 and er5 < 0.35:
            return "COMPRESSION"
        if er5 < 0.20:
            return "RANGE"
        return "UNCERTAIN"

    def advise(self, d):
        s = self.state
        why = self.describe()
        if s in VETO_ANY:
            return True, why
        if s in ("DIRECTIONAL", "BREAKOUT") and self.dir and self.dir != d:
            return True, why + " — the other way"
        return False, why

    def describe(self):
        f, s = self.f, self.state
        arrow = {1: "↑", -1: "↓"}.get(self.dir, "")
        bits = []
        if "er5" in f:
            bits.append(f"efficiency {f['er5']:.2f}")
        if f.get("breadth") is not None:
            bits.append(f"breadth {f['breadth']:.0%}")
        if f.get("ext_pct") is not None:
            bits.append(f"VWAP stretch p{f['ext_pct']:.0f}")
        if f.get("rv_pct") is not None:
            bits.append(f"activity p{f['rv_pct']:.0f}")
        return f"{s.lower()}{(' ' + arrow) if arrow and s in ('DIRECTIONAL', 'BREAKOUT', 'EXHAUSTION') else ''}" + \
            (f" ({', '.join(bits)})" if bits else "")

    def view(self):
        f = self.f
        r = lambda x, n=2: (round(float(x), n) if x is not None and np.isfinite(x) else None)
        return {"state": self.state, "dir": self.dir, "text": self.describe(),
                "er5": r(f.get("er5")), "er1": r(f.get("er1")), "breadth": r(f.get("breadth")),
                "rv_pct": r(f.get("rv_pct"), 0), "ext_pct": r(f.get("ext_pct"), 0),
                "vwap": r(f.get("vwap"), 1), "ext": r(f.get("ext"), 1), "broke": f.get("broke", 0)}
