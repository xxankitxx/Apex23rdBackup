"""c20_9s — c20_9x + the STALE-IMPULSE PULLBACK VETO (panel C11, 3 Nov 2026 night); shadow-book candidate.

Owner, 3 Nov: "We cannot be sitting on a trade for 15 mins or higher if it is not performing ... what is the
problem in entries for those times."

Finding (panel C11 autopsy, 72 kit trades over 11 days): on normal days every 'stuck' trade (held >= 10 min, peak
< +15 %) is a pullback entry ("NORM pb") into an impulse that had already finished — the breakout that armed the
pullback printed a median ~4 min before entry, often far longer. After entry the forward never follows through, the
40-pt trail is wider than any move the trade makes, and it drifts out on FWD_TRAIL at -1..-12 % after 14-53 min.
No exit rule (progress clock, forward stall, theta rent, queue ratio, tight stop) separated these from slow winners
without a cliff, so the fix is at the entry.

Rule (normal days only, yes/no, one parameter): refuse the pullback BUY when the impulse that armed it first
printed more than PB_AGE_MAX seconds earlier (660 s = 11 min). c20_9x already drops an arm after 900 s (PB_AMAX);
this just asks for a fresher impulse. A refused signal consumes the arm exactly as a taken one would (the core has
already cleared it), so the engine does not wait for the same pullback again. Expiry days, every exit, the picker,
the cooldown and the seq veto are c20_9x, untouched.

Causal: the arm's start second (arm[4]) is < the current second i. No scores, no sizing, buy only.
Kit, 11 days: +12,26,193 vs c20_9x +11,49,850 (+76,342); expiry days identical; stuck set 15 / -77,847 -> 10 / -31,307.
Plateau ~650-790 s; 528 s keeps 53 % of the gain, 792 s keeps 95 %. Gain concentrated (29 Oct +35.4 k); LODO +33 k.
"""
from . import c20_9x as _x

SI = dict(PB_AGE_MAX=660)                 # seconds: max age of the arming impulse at a normal-day pullback entry


class _SIMixin:
    _si_arm_i = None
    si_vetoes = 0

    def _pullback(self, i, fs, v, side, p):
        a0 = self.arm[4] if self.arm is not None else None     # the second the impulse first printed
        r = super()._pullback(i, fs, v, side, p)
        self._si_arm_i = a0 if r is not None else None          # only remembered when the pullback fires
        return r

    def on_second(self, i, D, pos):
        self._si_arm_i = None
        sig = super().on_second(i, D, pos)
        if (pos is None and sig is not None and sig[0] == "BUY" and not D.dte0
                and self._si_arm_i is not None and i - self._si_arm_i > SI["PB_AGE_MAX"]):
            self.si_vetoes += 1
            return self._veto("stale_impulse")                  # STALE_IMPULSE: skip this entry (counted in blocked)
        return sig


class KitStrategy(_SIMixin, _x.KitStrategy):
    pass


class Strategy(_SIMixin, _x.LiveStrategy):
    pass
