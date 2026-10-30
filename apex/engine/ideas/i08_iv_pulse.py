"""IV pulse (owner spec CHEAPNESS_AND_REGIME_SPEC.md A3 "implied vs realised", M9 IV module).

Are options dear or cheap right now, and is implied volatility being bid up or crushed?

* ATM IV: CE+PE IV averaged at the two strikes around spot, interpolated to spot (so an ATM roll does not jump),
  sampled every 5 s and median-smoothed over 30 s. Compared with itself 5 and 15 minutes ago.
* Same units: the engine's IV runs on a calendar clock (365 x 24 h). It is converted to "session vol": the implied
  variance to expiry is spread over the trading seconds left (each night until expiry counted as 1.5 session hours of
  gap risk, weekends skipped, holidays ignored). Realised vol = RMS of 5-s log returns of the futures mid (the spot
  print freezes for minutes at a time) over the last 20 min, annualised on 252 x 6.25 h, with single jumps clipped. Value = session IV - realised, in vol points.
* Skew: IV of the PE two strikes below ATM minus the CE two strikes above. Rising = put buyers paying up.

Observer only: never trades, never vetoes."""
import math
from collections import deque
from datetime import timedelta

import numpy as np

NAME = "iv_pulse"
TITLE = "IV pulse (dear / cheap)"
IDEA = "Are options dear or cheap vs how much Nifty is really moving, and is IV being bid up or crushed?"
VERDICT = ("Rejected as a gate 28-29 Oct: IV-vs-realised sorted days not trades (LODO -92.9k); IV-fall book "
           "t28_ivfall was weak. Shown for watching.")
EVERY_S = 5

SESSION_S = 22500.0             # 09:15-15:30
NIGHT_EQ_S = 5400.0             # one overnight gap ~ 1.5 session hours of variance
YEAR_SESS_S = 252 * SESSION_S
RV_WIN_S = 1200                 # realised window (20 min)
RV_STEP = 5                     # 5-s returns
SMOOTH_S = 30
CONFIRM = 3                     # a new state must show 3 updates running (15 s)
MIN_DWELL_S = 60                # and the old one must have lasted 60 s

# thresholds (vol points = %)
D5_IN, D5_OUT = 0.6, 0.3        # 5-min ATM IV change (also >= 5 % / 2.5 % of IV)
DEAR_IN, DEAR_OUT = 1.45, 1.30  # session IV / realised
CHEAP_IN, CHEAP_OUT = 1.00, 1.12
SKEW_SIDE = 0.4                 # 5-min skew change that names a side


def _ok(v):
    return v is not None and isinstance(v, (int, float)) and math.isfinite(v) and 0.005 < v < 3.0


def _warm():
    """Touch the numpy paths once at import so the first live call is not slowed by numpy's lazy loading."""
    x = np.linspace(1.0, 2.0, 400)
    j = np.searchsorted(x, np.arange(2.0, 1.0, -0.01)[::-1], side="right") - 1
    r = np.diff(np.log(x[j[j >= 0]]))
    a = np.abs(r)
    a.sort()
    float(np.sqrt(np.mean(np.minimum(np.maximum(r, -a[0]), a[-1]) ** 2)))


_warm()


class Idea:
    def __init__(self):
        self.ivs = deque()          # (t, raw ATM IV %, raw skew pts or nan)
        self.state = "WARMING"
        self.side = None
        self.since_t = None
        self.cand = None
        self.cand_n = 0
        self.alerts = 0
        self.day = None
        self.last = None

    # ── helpers ──────────────────────────────────────────────────────────
    def _sess_left(self, env):
        """Trading seconds (incl. night equivalents) from now to 15:30 on expiry day."""
        dt = env.dt
        close = dt.replace(hour=15, minute=30, second=0, microsecond=0)
        today = max(0.0, (close - dt).total_seconds())
        try:
            exp = dt.date().fromisoformat(env.expiry)
        except (TypeError, ValueError):
            return None
        d, extra, n = dt.date(), 0.0, 0
        while d < exp and n < 40:
            d += timedelta(days=1)
            n += 1
            if d.weekday() < 5:
                extra += NIGHT_EQ_S + SESSION_S
        return max(today + extra, 600.0)

    def _cal_left(self, env):
        try:
            exp = env.dt.replace(hour=15, minute=30, second=0, microsecond=0) + timedelta(
                days=(env.dt.date().fromisoformat(env.expiry) - env.dt.date()).days)
        except (TypeError, ValueError):
            return None
        floor = 600.0 if env.dte0 else 60.0
        return max((exp - env.dt).total_seconds(), floor)

    def _atm_iv(self, env):
        s = env.spot or env.fut
        if not s:
            return math.nan
        st = env.step or 50
        lo = int(math.floor(s / st) * st)
        hi = lo + st
        vals = []
        for k in (lo, hi):
            xs = [r["iv"] for r in (env.row(k, "CE"), env.row(k, "PE")) if r is not None and _ok(r.get("iv"))]
            vals.append(sum(xs) / len(xs) if xs else math.nan)
        a, b = vals
        if math.isfinite(a) and math.isfinite(b):
            w = (s - lo) / st
            return 100.0 * (a * (1 - w) + b * w)
        v = a if math.isfinite(a) else b
        return 100.0 * v if math.isfinite(v) else math.nan

    def _skew(self, env):
        st = env.step or 50
        p, c = env.row(env.atm - 2 * st, "PE"), env.row(env.atm + 2 * st, "CE")
        if p is None or c is None or not _ok(p.get("iv")) or not _ok(c.get("iv")):
            return math.nan
        return 100.0 * (p["iv"] - c["iv"])

    def _med(self, t0, t1, col):
        xs = [x[col] for x in self.ivs if t0 <= x[0] <= t1 and math.isfinite(x[col])]
        if len(xs) < 2:
            return math.nan
        xs.sort()
        return xs[len(xs) // 2]

    def _rv(self, env):
        T, S = env.hist.series("FUT", secs=RV_WIN_S)
        if len(S) < 300:
            T, S = env.hist.series("SPOT", secs=RV_WIN_S)
        ok = np.isfinite(S) & (S > 0)
        T, S = T[ok], S[ok]
        if len(S) < 300 or T[-1] - T[0] < 0.75 * RV_WIN_S:
            return math.nan
        # sample every RV_STEP seconds on the clock (newest value at or before each grid point)
        grid = np.arange(T[-1], T[0], -RV_STEP)[::-1]
        j = np.searchsorted(T, grid, side="right") - 1
        x = np.log(S[j[j >= 0]])
        r = np.diff(x)
        if len(r) < 60:
            return math.nan
        a = np.abs(r)
        a.sort()
        cap = 6.0 * 1.4826 * float(a[len(a) // 2]) + 1e-5            # clip feed jumps / re-syncs
        r = np.minimum(np.maximum(r, -cap), cap)
        return 100.0 * float(np.sqrt(np.mean(r * r) * YEAR_SESS_S / RV_STEP))

    def _set(self, want, side, now):
        """Hysteresis + persistence. Returns True when the state changed."""
        key = (want, side)
        if key == (self.state, self.side):
            self.cand, self.cand_n = None, 0
            return False
        if key == self.cand:
            self.cand_n += 1
        else:
            self.cand, self.cand_n = key, 1
        dwell = now - (self.since_t or -1e9)
        if self.state == "WARMING" or (self.cand_n >= CONFIRM and dwell >= MIN_DWELL_S):
            self.state, self.side, self.since_t = want, side, now
            self.cand, self.cand_n = None, 0
            return True
        return False

    # ── main ─────────────────────────────────────────────────────────────
    def update(self, env):
        now = env.t
        d = env.dt.date()
        if d != self.day:
            self.__init__()
            self.day = d
        iv_raw = self._atm_iv(env)
        sk_raw = self._skew(env)
        if math.isfinite(iv_raw):
            self.ivs.append((now, iv_raw, sk_raw))
        while self.ivs and self.ivs[0][0] < now - 1200:
            self.ivs.popleft()

        iv = self._med(now - SMOOTH_S, now, 1)
        iv5 = self._med(now - 300 - SMOOTH_S, now - 300, 1)
        iv15 = self._med(now - 900 - SMOOTH_S, now - 900, 1)
        sk = self._med(now - SMOOTH_S, now, 2)
        sk5 = self._med(now - 300 - SMOOTH_S, now - 300, 2)
        rv = self._rv(env)
        if env.dte0 and env.hm >= 15 * 60 + 10 and self.last:
            return dict(self.last, alert=False, text="expiry: last 20 min, IV solver unreliable - card frozen")
        if not (math.isfinite(iv) and math.isfinite(iv5) and math.isfinite(rv) and rv > 0):
            if self.last:
                return dict(self.last, alert=False, text="data gap (no fresh futures / ATM quotes) - last reading held")
            return {"state": "WARMING", "value": None, "unit": "vol pts",
                    "text": "needs 5 min of ATM IV and 15 min of spot"}

        sl, cl = self._sess_left(env), self._cal_left(env)
        if not sl or not cl:
            return {"state": "WARMING", "text": "no expiry"}
        siv = iv * math.sqrt((cl / (365.0 * 86400.0)) / (sl / YEAR_SESS_S))     # session-equivalent IV
        gap = siv - rv
        ratio = siv / rv
        d5 = iv - iv5
        d15 = iv - iv15 if math.isfinite(iv15) else math.nan
        dsk = sk - sk5 if (math.isfinite(sk) and math.isfinite(sk5)) else math.nan

        # ── classify with hysteresis ───────────────────────────────────
        cur = self.state
        tin, tout = max(D5_IN, 0.05 * iv), max(D5_OUT, 0.025 * iv)
        if (cur == "IV EXPANDING" and d5 > tout) or d5 >= tin:
            want = "IV EXPANDING"
        elif (cur == "IV CRUSHING" and d5 < -tout) or d5 <= -tin:
            want = "IV CRUSHING"
        elif (cur == "OPTIONS DEAR" and ratio > DEAR_OUT) or ratio >= DEAR_IN:
            want = "OPTIONS DEAR"
        elif (cur == "OPTIONS CHEAP" and ratio < CHEAP_OUT) or ratio <= CHEAP_IN:
            want = "OPTIONS CHEAP"
        else:
            want = "STEADY"
        side = None
        if want == "IV EXPANDING":
            if cur == "IV EXPANDING":
                side = self.side            # the side is named when expansion starts and kept while it lasts
            elif math.isfinite(dsk) and dsk >= SKEW_SIDE:
                side = "PE"
            elif math.isfinite(dsk) and dsk <= -SKEW_SIDE:
                side = "CE"
        changed = self._set(want, side, now)

        alert = False
        if changed and self.state in ("IV EXPANDING", "IV CRUSHING") and math.isfinite(d15) \
                and abs(d15) >= max(1.5, 0.10 * iv) and (d15 > 0) == (self.state == "IV EXPANDING") \
                and self.alerts < 10:
            alert = True
            self.alerts += 1

        st = self.state
        label = st + (f" {self.side}" if (st == "IV EXPANDING" and self.side) else "")
        sk_txt = ""
        if math.isfinite(dsk):
            sk_txt = f"; skew {sk:+.1f} ({dsk:+.1f}/5m, {'puts' if dsk > 0 else 'calls'} bid)" if abs(dsk) >= 0.2 \
                else f"; skew {sk:+.1f} flat"
        d15_txt = f", {d15:+.1f}/15m" if math.isfinite(d15) else ""
        text = (f"ATM IV {iv:.1f}% ({d5:+.1f}/5m{d15_txt}); session IV {siv:.1f} vs realised 20m {rv:.1f} "
                f"= x{ratio:.2f}{sk_txt}")
        plan = {"IV EXPANDING": "premiums get vega help: buy the side IV is rising on, don't chase spread",
                "IV CRUSHING": "premium can fall even if spot is right: keep holds short",
                "OPTIONS DEAR": "move must beat priced vol: need a clean break, not drift",
                "OPTIONS CHEAP": "Nifty moving more than options charge: a buyer's premium is fair",
                "STEADY": ""}.get(st, "")
        self.last = {"state": label, "side": self.side if st == "IV EXPANDING" else None, "value": round(gap, 2),
                "unit": "vol pts", "text": text, "plan": plan, "alert": alert}
        return self.last
