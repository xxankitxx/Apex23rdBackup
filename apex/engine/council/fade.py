"""fade: buy AGAINST a stretched move (14 Nov 2026 night, docs/58). SHADOW twins, flags off, never in the live pool.

The four-year test (984 sessions of 1-minute broker history, docs/58): momentum and breakout entries are flat or
negative on 2025-2026 and a blind buy costs 0 to 0.6 % a trade; fading a stretched move is the only family positive
both on the sessions it was found on (before 2025) and on those it was judged on (2025-2026), calls and puts alike:

  fade20   a 20-minute move of 0.6 day-sigmas   +3.5 % a trade (245 trades, t 2.0) then +2.2 % (199 trades, t 1.5)
  fade60   a 60-minute move of 0.7 day-sigmas   +1.9 % (305, t 1.7) then +1.8 % (261, t 1.4)

A LEAN, NOT AN EDGE: across 36 window x stretch settings the typical fade earns about +1 % a trade with 35 % winners,
real option bars on six settings gave +1.2, -0.5, +2.7, +1.9, -1.5, -0.4 %, and with other exits it turns negative.
In the recorded window (Oct-Nov 2026, a momentum quarter) fade20 lost on 5 of 6 trades. Hence a shadow.

Rule (normal days only: at least one session left before expiry), read once a minute at the minute's last second:
    move = smoothed forward now - smoothed forward W minutes ago
    day sigma = the day's first forward x the standard deviation of the last 20 daily log returns
                (data/learning/day_levels.json; with under 10 returns: the forward x ATM IV / 1.26 / sqrt(252))
    move >= +Z x day sigma  ->  buy a PUT;   move <= -Z x day sigma  ->  buy a CALL
At most one signal per side per W minutes (counted whether or not the book could take it). Strike: the champion's
picker. Exits: c20_9y's ladder unchanged (while holding this class IS c20_9y). Every rule reads rows <= i only.
"""
import json
import math

import numpy as np

from . import c20_8x as _a8
from . import c20_9y as _y
from .thr_d1 import days_to_expiry

IV_OVER_RV = 1.26          # ATM implied / 20-session realised volatility, median of 114 real-option sessions (docs/58)


def day_sigma(day, path=None):
    """standard deviation of the last 20 daily log returns of the closes BEFORE `day` (None with under 10)."""
    try:
        L = json.load(open(path or _a8.LEVELS_PATH, encoding="utf-8"))
    except Exception:
        return None
    cs = [float(L[k]["close"]) for k in sorted(L) if k < day and (L[k] or {}).get("close")]
    cs = cs[-21:]
    if len(cs) < 11:
        return None
    r = np.diff(np.log(np.array(cs)))
    s = float(np.std(r, ddof=1))
    return s if s > 0 else None


class _FadeMixin:
    W_MIN = 20
    Z = 0.6
    LEVELS = None                                       # a test may point this at its own file

    def _fd_reset(self, D):
        self.fd_dte = days_to_expiry(D.day, D.expiry)   # raises on a bad expiry: the marker below stays unset
        self._fd_day = D.day
        self.fd_rs = day_sigma(D.day, self.LEVELS)      # daily sigma as a fraction, from the prior closes
        self.fd_em = None                               # the day's sigma in points, fixed at the first forward
        self._fd_last = {"CE": -10 ** 9, "PE": -10 ** 9}
        self.fd_log = []                                # (row, side, move, threshold, taken)

    def _fd_points(self, i, D):
        if self.fd_em is not None:
            return self.fd_em
        f = D.fwd[i]
        if not np.isfinite(f):
            return None
        rs = self.fd_rs
        if rs is None:                                  # no history of closes yet: the options' own estimate
            k = D.atm(i)
            jc, jp = D.col.get((int(k), "CE")) if k == k else None, D.col.get((int(k), "PE")) if k == k else None
            ivs = [float(D.iv[i, j]) for j in (jc, jp) if j is not None and np.isfinite(D.iv[i, j]) and D.iv[i, j] > 0]
            if not ivs:
                return None
            rs = (sum(ivs) / len(ivs)) * getattr(self, "IV_SCALE", 1.0) / 100.0 / IV_OVER_RV / math.sqrt(252.0)
        self.fd_em = float(f) * rs
        return self.fd_em

    def on_second(self, i, D, pos):
        sig = super().on_second(i, D, pos)              # the champion: its own state and, while holding, its exits
        if getattr(self, "_fd_day", None) != D.day:
            self._fd_reset(D)
        if (self.fd_dte < 1) != bool(getattr(self, "EXPIRY_ONLY", False)):    # normal days, or expiry days only
            return sig if pos is not None else None
        em = self._fd_points(i, D)
        edge = None
        W = self.W_MIN * 60
        if em and i % 60 == 59 and i >= W + 59:
            a, b = self.fs[i], self.fs[i - W]
            if np.isfinite(a) and np.isfinite(b):
                mv = float(a - b)
                side = "PE" if mv >= self.Z * em else ("CE" if mv <= -self.Z * em else None)
                if side and i - self._fd_last[side] >= W:
                    self._fd_last[side] = i
                    edge = (side, mv)
        if pos is not None:
            if edge:
                self.fd_log.append((int(i), edge[0], edge[1], self.Z * em, False))
            return sig
        if edge is None:
            return None                                 # the champion's own pullback entry is not this book's
        p = self.p
        k = None
        if p["t0"] <= D.hm[i] < p["t1"] and i - self.last_exit >= p["cool"]:
            k = self._pick(i, D, edge[0], 40.0, p["hold"] / 60.0 * 0.5)
        self.fd_log.append((int(i), edge[0], edge[1], self.Z * em, k is not None))
        if k is None:
            return None
        self.best = None
        self._buy_v = 40.0
        return ("BUY", k, edge[0], f"FADE {edge[1]:+.0f} pts in {self.W_MIN} min (line {self.Z * em:.0f})")


class Fade20(_FadeMixin, _y.Strategy):
    W_MIN, Z = 20, 0.6


class Fade60(_FadeMixin, _y.Strategy):
    W_MIN, Z = 60, 0.7


class Fade60Expiry(_FadeMixin, _y.Strategy):
    """fade60x (14 Nov, docs/59): the same 60-minute 0.7-sigma fade on EXPIRY days only, with the champion's expiry
    ladder (15-minute clock, 25-point trail). A year of real option seconds: 28 trades, 57 % winners, +7.6 % a
    trade (t 1.9) - a lead on few trades."""
    W_MIN, Z = 60, 0.7
    EXPIRY_ONLY = True
