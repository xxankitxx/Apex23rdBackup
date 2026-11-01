"""c20_9v — c20_9x + two normal-day exits from the C9 council (1 Nov 2026); shadow book (D-148).

* LVL_BOOK (member 06): the 50-pt round numbers of spot ahead of the trade are fixed at entry. Sell when bid >= +6 %,
  peak bid < +20 %, spot came within 13 pts of the next level (not broken by > 8 pts) and has given back >= 10 pts.
* PGB (member 09): sb = EMA(20 s) of the held bid, spk = max sb since entry; once spk >= entry*1.15, sell when
  sb <= entry*(1 + 0.6*(spk/entry - 1)).
Expiry days are pure c20_9x. Rows <= i only. 9-day engine replay (real fills, gross): +9.74 L vs c20_9x +9.30 L;
30 Oct +11.6k vs -5.6k, but 23 Oct -22k (LVL_BOOK sold the 09:41 +77 % runner at +9.8 %).
"""
import numpy as np

from . import c20_9x as _x

LVP = dict(LX=0.06, NEAR=13.0, REJ=10.0, BRK=8.0, CAP=0.20, MINAHEAD=3.0)
GBP = dict(ARM=0.15, KEEP=0.6, TAU=20.0)


class _V9Mixin:
    def _reset(self, D):
        super()._reset(D)
        self.basis = np.nan
        self.lvb_pin = self.lvb = None
        self._g_pin = self.gsb = self.gspk = None

    def _ref(self, i, D):
        s, f = float(D.spot[i]), float(D.fwd[i])
        if s > 0 and np.isfinite(s):
            if np.isfinite(f):
                self.basis = f - s
            return s
        if np.isfinite(f) and np.isfinite(self.basis):
            return f - self.basis
        return np.nan

    def on_second(self, i, D, pos):
        if self.day != D.day:
            self._reset(D)
        ref = self._ref(i, D)
        if pos is None:
            self.lvb_pin = None
            return super().on_second(i, D, pos)
        sig = super().on_second(i, D, pos)
        e, j = pos["entry"], pos["j"]
        b = D.bid[i, j]
        # PGB state (updated every held second, as member 09)
        if self._g_pin != pos["i_in"]:
            self._g_pin, self.gsb, self.gspk = pos["i_in"], None, None
        if np.isfinite(b):
            b = float(b)
            self.gsb = b if self.gsb is None else self.gsb + (b - self.gsb) / GBP["TAU"]
            self.gspk = self.gsb if self.gspk is None else max(self.gspk, self.gsb)
        if D.dte0 or sig is not None:
            return sig
        # PGB (member 09 runs inside member 06 in V2's MRO)
        if self.gspk is not None:
            g = self.gspk / e - 1
            if g >= GBP["ARM"] and self.gsb <= e * (1 + GBP["KEEP"] * g):
                self._mark_last(i, D, pos)
                return self._x(i, "PGB")
        # LVL_BOOK
        if np.isfinite(ref):
            d = 1 if pos["rr"] == "CE" else -1
            if self.lvb_pin != pos["i_in"]:
                self.lvb_pin = pos["i_in"]
                base = np.floor(ref / 50.0) * 50.0
                lv = [base + 50.0 * k for k in range(-6, 8)]
                ahead = sorted({round(a, 2) for a in lv if (a - ref) * d > LVP["MINAHEAD"]}, key=lambda a: (a - ref) * d)
                self.lvb = [d, ahead, ref]
            _, ahead, best = self.lvb
            best = max(best, ref) if d > 0 else min(best, ref)
            self.lvb[2] = best
            while ahead and (best - ahead[0]) * d > LVP["BRK"]:
                ahead.pop(0)
            if ahead and (best - ahead[0]) * d >= -LVP["NEAR"] and (best - ref) * d >= LVP["REJ"]:
                if np.isfinite(b) and b >= e * (1 + LVP["LX"]) and pos["peak_bid"] < e * (1 + LVP["CAP"]):
                    self._mark_last(i, D, pos)
                    return self._x(i, "LVL_BOOK")
        return None


class KitStrategy(_V9Mixin, _x.KitStrategy):
    pass


class Strategy(_V9Mixin, _x.LiveStrategy):
    pass
