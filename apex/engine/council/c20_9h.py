"""c20_9h — c20_9x + a HALF-OF-PEAK floor on expiry days (3 Nov 2026); shadow book, the alternative to c20_9e.

docs/21_LIVE_VS_TAPE_3NOV.md §4: c20_9x's expiry floor steps from the entry (+15 %) straight to 70 % of the gain
(+60 %). Rule (expiry days only, yes/no): once the peak bid is >= entry x (1 + ARM) the floor is entry x (1 + KEEP x
peak gain) — half the gain kept (HALF_LOCK). c20_9x's own floors still apply and a higher one wins (GIVEBACK keeps
70 % from +60 %). On the 3 Nov bids: -18,590 against -44,688. Normal days are c20_9x's ramp, untouched.
"""
from . import c20_9x as _x

HL = dict(ARM=0.15, KEEP=0.5)


class _HLMixin:
    def _floor(self, e, g, dte0):
        fl, kind = super()._floor(e, g, dte0)
        if dte0 and g >= HL["ARM"]:
            hf = e * (1 + HL["KEEP"] * g)
            if fl is None or hf > fl:
                fl, kind = hf, "HALF_LOCK"
        return fl, kind


class KitStrategy(_HLMixin, _x.KitStrategy):
    pass


class Strategy(_HLMixin, _x.LiveStrategy):
    pass
