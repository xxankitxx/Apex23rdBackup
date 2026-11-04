"""c20_9y — c20_9x + two yes/no entry vetoes from the 20-member panel C12 (4 Nov 2026 night). Shadow book.

1. IV_RICH (both day types): refuse a BUY when the ATM implied vol — the 30-s trailing mean of (CE IV + PE IV)/2 at
   the strike nearest the parity forward — is more than IVR = 3.5 vol pts above its median since 09:20 (needs 300 s
   of history). Buying an option whose IV just spiked means paying for vol that tends to come back out; on the
   kit it only fired on expiry afternoons (19 Oct 14:33, 3 Nov 13:54 / 14:18 / 14:24 — all losers).
2. OI_WALL (normal days only): refuse a BUY when the strike with the most open interest of the resisting type (call
   OI for a CE buy, put OI for a PE buy) within 250 pts of the forward sits ahead of the trade and no more than
   25 pts away — the breakout runs straight into the wall that writers defend.

Exits, picker, cooldowns and every other rule are c20_9x. Both vetoes read rows <= i only. The IV series is built
second by second from the rows already seen, so kit and engine run the same code (the kit stores IV as a decimal,
the engine in percent: IV_SCALE).

Kit, 12 days (19 Oct - 4 Nov): c20_9x +11,23,538 -> c20_9y +12,32,085; losers 36 / -5.69 L -> 28 / -4.68 L; expiry
days and the 27 Oct runners unchanged or better. Thin evidence: eight vetoed buys on five days (docs/23).
"""
import numpy as np

from . import c20_9x as _x

Y = dict(IVR=3.5, IV_AVG=30, IV_MIN_S=300, W=250, DMAX=25)


def wall_ahead(D, i, side, W):
    """Distance (pts, > 0 = ahead of the trade) from the forward to the max-OI strike of the resisting type."""
    f = float(D.fwd[i]) if np.isfinite(D.fwd[i]) else float(D.spot[i])
    if not np.isfinite(f):
        return np.nan
    best, kb = -1.0, None
    for k in np.unique(D.K):
        if abs(k - f) > W:
            continue
        j = D.col.get((int(k), side))
        if j is None:
            continue
        o = float(D.oi[i, j])
        if np.isfinite(o) and o > best:
            best, kb = o, float(k)
    if kb is None:
        return np.nan
    return (kb - f) if side == "CE" else (f - kb)


class _YMixin:
    IV_SCALE = 100.0          # kit: decimal IV -> vol pts
    y_vetoes = None

    def _y_reset(self, D):
        N = len(D.T)
        self._y_day = D.day
        self._y_raw = np.full(N, np.nan)
        self._y_avg = np.full(N, np.nan)
        self._y_last = -1
        self._y_st = D.i_at(9, 20)
        self.y_vetoes = []

    def _y_upto(self, i, D):
        A = int(Y["IV_AVG"])
        ks = np.unique(D.K) if len(D.K) else None
        for r in range(self._y_last + 1, i + 1):
            ref = D.fwd[r] if np.isfinite(D.fwd[r]) else D.spot[r]
            raw = np.nan
            if ks is not None and np.isfinite(ref):
                k = int(ks[np.argmin(np.abs(ks - ref))])
                jc, jp = D.col.get((k, "CE")), D.col.get((k, "PE"))
                if jc is not None and jp is not None:
                    raw = self.IV_SCALE * 0.5 * (float(D.iv[r, jc]) + float(D.iv[r, jp]))
            self._y_raw[r] = raw
            seg = self._y_raw[max(0, r - A + 1):r + 1]
            seg = seg[np.isfinite(seg)]
            self._y_avg[r] = float(seg.mean()) if len(seg) else np.nan
        self._y_last = max(self._y_last, i)

    def _iv_rich(self, i, D):
        st = self._y_st
        if i - st < Y["IV_MIN_S"] or not np.isfinite(self._y_avg[i]):
            return False
        h = self._y_avg[st:i]
        h = h[np.isfinite(h)]
        return len(h) > 0 and self._y_avg[i] - float(np.median(h)) > Y["IVR"]

    def on_second(self, i, D, pos):
        if getattr(self, "_y_day", None) != D.day:
            self._y_reset(D)
        self._y_upto(i, D)
        sig = super().on_second(i, D, pos)
        if pos is None and sig is not None and sig[0] == "BUY":
            if self._iv_rich(i, D):
                self.y_vetoes.append((D.day, int(i), sig[2], "iv_rich"))
                return self._veto("iv_rich")
            if not D.dte0:
                d = wall_ahead(D, i, sig[2], Y["W"])
                if np.isfinite(d) and 0 < d <= Y["DMAX"]:
                    self.y_vetoes.append((D.day, int(i), sig[2], "oi_wall"))
                    return self._veto("oi_wall")
        return sig


class KitStrategy(_YMixin, _x.KitStrategy):
    pass


class Strategy(_YMixin, _x.LiveStrategy):
    IV_SCALE = 1.0            # the engine stores option IV in percent already
