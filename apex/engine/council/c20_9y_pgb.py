"""pgb_c20_9y (13 Nov, shadow twin): c20_9y plus c20_9v's PGB exit alone on normal days (no LVL_BOOK).
PGB: sb = EMA(20 s) of the held bid, spk = max sb since entry; once spk >= entry x 1.15, sell when
sb <= entry x (1 + 0.6 x (spk / entry - 1)). Expiry days are c20_9y unchanged.

Evidence (docs/research/13nov/R02 Phase B, 13 Nov): "PGB on every pool book" better in both windows (discovery +49.5
log pts, strike 52.2 to 53.3 %; test +11.5). The c20_9v twin was the only exit twin better in both windows. Shadow only.
"""
from . import c20_9y as _y
from .c20_9v import GBP


class _PGBMixin:
    def on_second(self, i, D, pos):
        if self.day != D.day:
            self._reset(D)
        sig = super().on_second(i, D, pos)
        if pos is None:
            return sig
        st = pos.get("st")
        if st is None:                                   # the kit: keep the state here, per position
            if getattr(self, "_pg", None) is None or self._pg.get("i_in") != pos["i_in"]:
                self._pg = {"i_in": pos["i_in"]}
            st = self._pg
        b = D.bid[i, pos["j"]]
        if b == b:                                       # finite
            b = float(b)
            g0 = st.get("pg_sb")
            st["pg_sb"] = b if g0 is None else g0 + (b - g0) / GBP["TAU"]
            st["pg_spk"] = st["pg_sb"] if st.get("pg_spk") is None else max(st["pg_spk"], st["pg_sb"])
        if D.dte0 or sig is not None or st.get("pg_spk") is None:
            return sig
        e = pos["entry"]
        g = st["pg_spk"] / e - 1
        if g >= GBP["ARM"] and st["pg_sb"] <= e * (1 + GBP["KEEP"] * g):
            self._mark_last(i, D, pos)
            return self._x(i, "PGB")
        return None


class Strategy(_PGBMixin, _y.Strategy):
    pass
