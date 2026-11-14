"""orbfade (14 Nov 2026 night, shadow, docs/58): buy AGAINST the first break of the 15-minute opening range.

Four years of 1-minute history (model option, champion exits, normal days): buying the break of the opening range
loses (-1.2 % a trade before 2025, -0.3 % on 2025-2026); fading it makes +1.5 % and +1.5 % (400 and 356 trades,
t 1.7 and 1.4, positive in 5 of 5 years). On the 114 sessions with real option bars it made -0.5 % (112 trades), so
this was the weakest of the fades on that set. Per second with the real class on the year before the recorded window
(179 sessions) it made +2.1 % a trade (44 % winners). A shadow; pooled only by the shadow account conductor_fd.

Rule (normal days only): the opening range is the high and low of the smoothed forward from 09:15 to 09:30. From 09:30
to 11:45, at each minute's last second: the first time the smoothed forward is above the range buy a PUT, below it buy
a CALL. One signal a day. Strike: the champion's picker. Exits: c20_9y's ladder unchanged. Rows <= i only.
"""
import numpy as np

from . import c20_9y as _y
from .thr_d1 import days_to_expiry

O = dict(RANGE_S=900, UNTIL_S=150 * 60)


class _OrbFadeMixin:
    def _of_reset(self, D):
        self.of_dte = days_to_expiry(D.day, D.expiry)   # raises on a bad expiry: the marker below stays unset
        self._of_day = D.day
        self.of_hi = self.of_lo = None
        self.of_done = False
        self.of_log = []

    def on_second(self, i, D, pos):
        sig = super().on_second(i, D, pos)               # the champion: its own state and, while holding, its exits
        if getattr(self, "_of_day", None) != D.day:
            self._of_reset(D)
        if self.of_dte < 1:
            return sig if pos is not None else None
        f = self.fs[i]
        edge = None
        if np.isfinite(f):
            if i < O["RANGE_S"]:
                self.of_hi = f if self.of_hi is None else max(self.of_hi, f)
                self.of_lo = f if self.of_lo is None else min(self.of_lo, f)
            elif not self.of_done and self.of_hi is not None and i < O["UNTIL_S"] and i % 60 == 59:
                if f > self.of_hi:
                    edge = "PE"
                elif f < self.of_lo:
                    edge = "CE"
                if edge:
                    self.of_done = True
        if pos is not None:
            if edge:
                self.of_log.append((int(i), edge, False))
            return sig
        if edge is None:
            return None                                  # the champion's own entry is not this book's
        p = self.p
        k = None
        if p["t0"] <= D.hm[i] < p["t1"] and i - self.last_exit >= p["cool"]:
            k = self._pick(i, D, edge, 40.0, p["hold"] / 60.0 * 0.5)
        self.of_log.append((int(i), edge, k is not None))
        if k is None:
            return None
        self.best = None
        self._buy_v = 40.0
        return ("BUY", k, edge, f"ORB FADE range {self.of_lo:.0f}-{self.of_hi:.0f} broken {'up' if edge == 'PE' else 'down'}")


class Strategy(_OrbFadeMixin, _y.Strategy):
    pass
