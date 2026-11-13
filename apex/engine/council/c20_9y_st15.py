"""st15_c20_9y (14 Nov 2026, shadow twin, docs/57): c20_9y that sells a trade which has gone nowhere.

Owner, 14 Nov: "sometimes the champion holds on to a trade at length without any movement at all ... Why are you not
using the maths here?" On the five pool books' 231 real normal-day entries (per-second, real quotes, apex/fastlab.py):
a trade that after 15 minutes has never been 8 % up and sits within +-4 % of its entry later won 31 % of the time and
averaged -1.7 %; sold there it averages -1.2 % and gives the account back about half an hour. At 10 minutes the same
rule is wrong (those trades later averaged +4.6 %), so the line is 15 minutes, not sooner. At account level the freed
time took new triggers: the pattern's 12 in-sample normal days went from +366 to +431 (sum of day %), and both
untouched days improved (12 Nov +2.5 to +6.8, 13 Nov -26.3 to -16.5).

Rule (normal days only; expiry days are left alone, their clock is 15 minutes already):
    held >= AFTER seconds and peak bid < entry * (1 + PK) and |bid / entry - 1| < BAND  ->  SELL "STALL"
Every other exit is c20_9y's and is checked first.
"""
import numpy as np

from . import c20_9y as _y

ST = dict(AFTER=900, PK=0.08, BAND=0.04)


class _StallMixin:
    def on_second(self, i, D, pos):
        sig = super().on_second(i, D, pos)
        if pos is None or sig is not None or D.dte0:
            return sig
        b = D.bid[i, pos["j"]]
        if not np.isfinite(b):
            return None
        e = pos["entry"]
        if (D.T[i] - D.T[pos["i_in"]] >= ST["AFTER"] and pos["peak_bid"] / e - 1 < ST["PK"]
                and abs(float(b) / e - 1) < ST["BAND"]):
            self._mark_last(i, D, pos)
            return self._x(i, "STALL")
        return None


class Strategy(_StallMixin, _y.Strategy):
    pass
