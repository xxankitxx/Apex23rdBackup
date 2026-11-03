"""c20_9e — c20_9x + the EXPIRY GIVE-BACK TRAIL (3 Nov 2026); shadow book.

Owner, 3 Nov, after a -44,688 expiry day on which seven c20_9x trades peaked +11..+19 pts and gave back 79,381 of
1,05,752 available: "the code is still not trailing". docs/21_LIVE_VS_TAPE_3NOV.md §2: between +15 % and +60 % the
expiry mode's only floor is the entry (BE_LOCK), its 25-pt forward trail is the size of every peak and its 15-min
clock sold the rest.

Rule (expiry days only, premium points, yes/no): once the peak bid is >= entry + ARM pts the trail is armed for the
rest of the trade; exit when the bid is <= peak bid - GIVE pts (EXP_TRAIL). It is a floor like BE_LOCK / GIVEBACK,
checked by c20_9x's floor layer (SL keeps precedence; a higher armed floor wins). Everything else is c20_9x
(docs/20_C20_9X_STRATEGY_SPEC.md); normal days are untouched. On the 3 Nov bids the rule turns -44,688 into -9,370
(docs/21 §4) — fitted to one day, so it trades only after beating c20_9x on the 19 Oct, 27 Oct and 3 Nov tapes.
"""
from . import c20_9x as _x

XT = dict(ARM=5.0, GIVE=6.0)        # premium points: arm once the peak bid is ARM over entry; give back GIVE from the peak


class _XTMixin:
    def _floor(self, e, g, dte0):
        fl, kind = super()._floor(e, g, dte0)
        if dte0:
            pk = e * (1 + g)                          # g is the peak gain as a fraction of entry
            if pk - e >= XT["ARM"]:
                tf = pk - XT["GIVE"]
                if fl is None or tf > fl:
                    fl, kind = tf, "EXP_TRAIL"
        return fl, kind


class KitStrategy(_XTMixin, _x.KitStrategy):
    pass


class Strategy(_XTMixin, _x.LiveStrategy):
    pass
