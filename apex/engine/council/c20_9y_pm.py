"""pm_c20_9y (13 Nov, shadow twin): c20_9y with c20_20's expiry-afternoon cut switched back on: no new expiry-day entry
at or after 13:30 ("pm" part, PM_T). Normal days and every exit are c20_9y unchanged.

Evidence (docs/research/13nov/R18): pool trades after 13:30 on expiry days won 29 % (58 trades) against 63 %, lower on
4 of 4 expiry days; at the Conductor's account the strike rate rises in both windows (56.0 vs 53.6 %, 56.7 vs 51.4 %)
and the worst day improves (-28.5 vs -37.1 %), but the early return falls (it skips 27 Oct 14:36, +79.7 %). Shadow only.
"""
from . import c20_9x as _x
from . import c20_9y as _y


class Strategy(_y.Strategy):
    def __init__(self, parts=None, **kw):
        super().__init__(parts=tuple(_x.FINAL_R9 if parts is None else parts) + ("pm",), **kw)
