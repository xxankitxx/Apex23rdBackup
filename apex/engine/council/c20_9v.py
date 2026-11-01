"""c20_9v — c20_9x + two normal-day exits from the C9 council (1 Nov 2026); shadow book (D-148).

* LVL_BOOK (member 06): the 50-pt round numbers of Nifty ahead of the trade are fixed at entry. Sell when bid >= +6 %,
  peak bid < +20 %, Nifty came within 13 pts of the next level (not broken by > 8 pts) and has given back >= 10 pts.
* PGB (member 09): sb = EMA(20 s) of the held bid, spk = max sb since entry; once spk >= entry*1.15, sell when
  sb <= entry*(1 + 0.6*(spk/entry - 1)).
Expiry days are pure c20_9x. Rows <= i only. 9-day engine replay (real fills, gross): +9.74 L vs c20_9x +9.30 L;
30 Oct +11.6k vs -5.6k, but 23 Oct -22k (LVL_BOOK sold the 09:41 +77 % runner at +9.8 %).

Reference price for the levels: the Nifty print while it is fresh, else forward minus the last known basis. A print
is stale when it is <= 0 (the kit's 29 Oct gap) or unchanged for FREEZE_S seconds (the engine's D-132 guard withholds
a frozen index and the adapter carries the last value forward). When the reference changes source the best-since-entry
is re-based, so a basis jump never counts as a rejection. The exits' state (smoothed bid and its peak, the level list
and the best) lives in pos["st"], which the adapter keeps on the book position, so it survives an engine restart like
c20_9x's own peak_bid; the kit's pos has no "st", so there the state is held on the strategy, keyed by the entry second.
"""
import numpy as np

from . import c20_9x as _x

LVP = dict(LX=0.06, NEAR=13.0, REJ=10.0, BRK=8.0, CAP=0.20, MINAHEAD=3.0)
GBP = dict(ARM=0.15, KEEP=0.6, TAU=20.0)
FREEZE_S = 120          # a Nifty print unchanged this long is frozen: use the forward instead


class _V9Mixin:
    def _reset(self, D):
        super()._reset(D)
        self.basis = np.nan
        self._sp_last, self._sp_i = np.nan, -1      # last distinct Nifty print and the second it changed
        self._st = None                              # exit state when pos carries no "st" (the kit)

    def _ref(self, i, D):
        """(reference price, source): Nifty when fresh ("s"), else forward - basis ("f"), else (nan, "")"""
        s, f = float(D.spot[i]), float(D.fwd[i])
        if s > 0 and np.isfinite(s):
            if s != self._sp_last:
                self._sp_last, self._sp_i = s, i
                if np.isfinite(f):
                    self.basis = f - s               # measured against a new print only, never a carried one
            if i - self._sp_i < FREEZE_S:
                return s, "s"
        if np.isfinite(f) and np.isfinite(self.basis):
            return f - self.basis, "f"
        return np.nan, ""

    def _state(self, pos):
        st = pos.get("st")
        if st is None:                               # no restart-safe slot: keep it here, per position
            if self._st is None or self._st.get("i_in") != pos["i_in"]:
                self._st = {"i_in": pos["i_in"]}
            st = self._st
        return st

    def on_second(self, i, D, pos):
        if self.day != D.day:
            self._reset(D)
        if pos is None:
            self._ref(i, D)                          # keep the basis and the freeze clock current
            return super().on_second(i, D, pos)
        ref, src = self._ref(i, D)
        sig = super().on_second(i, D, pos)
        st = self._state(pos)
        e, j = pos["entry"], pos["j"]
        b = D.bid[i, j]
        # PGB state (updated every held second, as member 09)
        if np.isfinite(b):
            b = float(b)
            gsb = st.get("gsb")
            gsb = b if gsb is None else gsb + (b - gsb) / GBP["TAU"]
            st["gsb"] = gsb
            st["gspk"] = gsb if st.get("gspk") is None else max(st["gspk"], gsb)
        if D.dte0 or sig is not None:
            return sig
        # PGB (member 09 runs inside member 06 in V2's MRO)
        if st.get("gspk") is not None:
            g = st["gspk"] / e - 1
            if g >= GBP["ARM"] and st["gsb"] <= e * (1 + GBP["KEEP"] * g):
                self._mark_last(i, D, pos)
                return self._x(i, "PGB")
        # LVL_BOOK
        if np.isfinite(ref):
            d = 1 if pos["rr"] == "CE" else -1
            lv = st.get("lv")
            if lv is None:
                base = float(np.floor(ref / 50.0) * 50.0)
                cand = [base + 50.0 * k for k in range(-6, 8)]
                ahead = sorted({round(a, 2) for a in cand if (a - ref) * d > LVP["MINAHEAD"]}, key=lambda a: (a - ref) * d)
                lv = st["lv"] = {"ahead": [float(a) for a in ahead], "best": float(ref), "src": src}
            elif lv["src"] != src:                   # the reference changed source: re-base, a basis jump is no rejection
                lv["best"], lv["src"] = float(ref), src
            best = max(lv["best"], ref) if d > 0 else min(lv["best"], ref)
            lv["best"] = float(best)
            ahead = lv["ahead"]
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
