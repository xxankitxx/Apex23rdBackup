"""fade3x (15 Nov 2026, shadow, docs/60 section 7): the three fades on EXPIRY days only.

The expiry book that the expiry-style switch (Conductor policy "xswitch", conductor_xs) hands the account to when the
champion's expiry breakout has done worse than this book over the last 6 expiry days. On its own it is a lean, not an
edge: on 83 expiry days with real option bars and causal prices it made +98 / -46 / +63 / -164 (found, judged, window,
holdout year; docs/60 section 6). The switch between the two is what tested well (+1,186 against -634).

Rules, read at each minute's last second, rows <= i only, expiry days only (no session left before expiry):
    a 20-minute move of 0.6 day-sigmas, faded   (fade.Fade20's rule: a move up buys a PUT, a move down a CALL)
    a 60-minute move of 0.7 day-sigmas, faded   (fade.Fade60's rule)
    the first break of the 15-minute opening range until 11:45, faded (orbfade's rule)
Each stretch fade fires at most once per side per window. Strike: the champion's picker. Exits: the champion's expiry
ladder with a 45-minute clock (hold 2700 s instead of 900), as in the research (agents/exits_fade gen_fade3_rt60).
"""
import numpy as np

from . import c20_9y as _y
from .fade import _FadeMixin
from .orbfade import O as _ORB

HOLD_S = 2700
FADES = ((20, 0.6), (60, 0.7))


class Strategy(_FadeMixin, _y.Strategy):
    EXPIRY_ONLY = True

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.pe = dict(self.pe, hold=HOLD_S)            # the expiry ladder, 45-minute clock

    def _f3_reset(self, D):
        self._f3_day = D.day
        self.f3_last = {(w, s): -10 ** 9 for w, _ in FADES for s in ("CE", "PE")}
        self.f3_hi = self.f3_lo = None
        self.f3_orb_done = False

    def _f3_edge(self, i, em):
        """(side, text) of a trigger at row i, or None. Every rule is updated each second whether or not it is used."""
        f = self.fs[i]
        if np.isfinite(f) and i < _ORB["RANGE_S"]:
            self.f3_hi = f if self.f3_hi is None else max(self.f3_hi, f)
            self.f3_lo = f if self.f3_lo is None else min(self.f3_lo, f)
        if i % 60 != 59:
            return None
        edge = None
        if em:
            for w, z in FADES:
                W = w * 60
                if i < W + 59:
                    continue
                a, b = self.fs[i], self.fs[i - W]
                if not (np.isfinite(a) and np.isfinite(b)):
                    continue
                mv = float(a - b)
                side = "PE" if mv >= z * em else ("CE" if mv <= -z * em else None)
                if side and i - self.f3_last[(w, side)] >= W:
                    self.f3_last[(w, side)] = i
                    edge = edge or (side, f"FADE3X {mv:+.0f} pts in {w} min (line {z * em:.0f})")
        if (not self.f3_orb_done and self.f3_hi is not None and _ORB["RANGE_S"] <= i < _ORB["UNTIL_S"]
                and np.isfinite(f)):
            side = "PE" if f > self.f3_hi else ("CE" if f < self.f3_lo else None)
            if side:
                self.f3_orb_done = True
                edge = edge or (side, f"FADE3X ORB range {self.f3_lo:.0f}-{self.f3_hi:.0f} broken")
        return edge

    def on_second(self, i, D, pos):
        sig = _y.Strategy.on_second(self, i, D, pos)    # the champion: its own state and, while holding, its exits
        if getattr(self, "_fd_day", None) != D.day:
            self._fd_reset(D)                           # raises on a bad expiry: the marker stays unset
        if getattr(self, "_f3_day", None) != D.day:
            self._f3_reset(D)
        if self.fd_dte >= 1:                            # normal days: this book never trades
            return sig if pos is not None else None
        edge = self._f3_edge(i, self._fd_points(i, D))
        if pos is not None:
            return sig
        if edge is None:
            return None                                 # the champion's own breakout entry is not this book's
        p = self.p
        k = None
        if p["t0"] <= D.hm[i] < p["t1"] and i - self.last_exit >= p["cool"]:
            k = self._pick(i, D, edge[0], 40.0, p["hold"] / 60.0 * 0.5)
        self.fd_log.append((int(i), edge[0], 0.0, 0.0, k is not None))
        if k is None:
            return None
        self.best = None
        self._buy_v = 40.0
        return ("BUY", k, edge[0], edge[1])
