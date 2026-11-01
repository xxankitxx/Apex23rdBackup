"""c20_9t — c20_9x + the owner's RENT TRAIL ("rt", 31 Oct 2026).

Owner, after the 30 Oct live session (three c20_9x trades peaked +15.1 %, +13.2 %, +17.6 % and exited +0.7 %, -4.6 %,
0.0 %): "I want a stronger trailing system on days which are not trending and the greeks also do not support holding
for too long. ... If the greeks suggest a trending market, we may trail a little casually as we want to ride the
trend. But if the greeks suggest a choppy or sideways market, we will trail tightly. ... If you want to re-enter,
there should be proper entry again that we get which is a stronger reason than why the trade got trailed."

Rule (see c20_9x.R9P RT_*): once the peak bid is >= +8 % over entry and the market is choppy for the trade — the
held contract's gamma rent (realised / implied variance of the forward, last 600 s, calendar theta) has fallen to
half its value at entry, OR the forward's 10-min trend efficiency (|net move| / sum of |1-min moves|) is < 0.35 —
the trail arms for the rest of the trade: exit when the bid falls below entry + 60 % of the peak gain. Neither
(trending) leaves c20_9x's exits alone. Both day types. A same-side re-entry within 900 s of a RENT_TRAIL exit
needs a faster forward trigger than the booked trade's and trend efficiency >= 0.35. Everything else is c20_9x
(docs/20_C20_9X_STRATEGY_SPEC.md). Calibrated on the 30 Oct tape (owner's choice, 31 Oct): an absolute rent floor
never fires intraday.
"""
from . import c20_9x as _x

FINAL_T = _x.FINAL_R9 + ("rt",)


class KitStrategy(_x.KitStrategy):
    def __init__(self, parts=None, **kw):
        super().__init__(parts=FINAL_T if parts is None else parts, **kw)


class Strategy(_x.LiveStrategy):
    def __init__(self, parts=None, **kw):
        super().__init__(parts=FINAL_T if parts is None else parts, **kw)
