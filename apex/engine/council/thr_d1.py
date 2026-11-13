"""thr_d1: the day-before-expiry thrust books (14 Nov 2026, docs/57). SHADOW twins, flags off, never in the live pool.

What the 14 Nov study found (apex/fastlab.py on the recorded sessions, 71 sessions of 5-minute and 215 of 15-minute
history): from August to November 2026, on the trading session BEFORE the weekly expiry a move tended to continue
(seven kinds of momentum event: +7 Nifty points 30 minutes later, positive on 15 of 15 such sessions; nothing further
from expiry), and the champion's own pattern won there (10 of 10 Conductor trades) and not on the other normal days
(12 of 37). On those sessions a THRUST of the sister indices or of the heavyweights was a buy with the champion's
exits (3 recorded sessions, real quotes: with the champion's entries 40 trades, 52 to 60 % winners, the three days'
sum +437 to +588 % against +256 %); on the other normal days the same entry made nothing, so it is switched off.
A LEAD, NOT A LAW: from January to July 2026 the same session showed no continuation (15 of 29, t 0.1). Hence a shadow.

  thr_sis  BANKNIFTY futures (mid) and the FINNIFTY index BOTH moved SIS Nifty-equivalent points in L seconds
  thr_hw   the Nifty-weighted heavyweight basket moved HW Nifty points in L seconds with weighted breadth >= BRD

A thrust is the first second of a stretch where the condition holds, at most one per side per GAP seconds, counted
whether or not the book could take it (as in the study). Entries only when exactly one trading session is left before
expiry. Strike: the champion's picker (|delta| >= 0.52, nearest 0.52). Exits: c20_9y's ladder, unchanged: while
holding this class IS c20_9y. The champion's own pullback entries are not taken by this book.
Every rule reads rows <= i only.
"""
import math
from datetime import date, timedelta

import numpy as np

from ... import config
from . import c20_9y as _y

T = dict(L=60, SIS=8.0, HW=8.0, BRD=0.5, GAP=600, COVER=0.7)


def days_to_expiry(day, expiry):
    """trading sessions after `day` up to and including the expiry day (0 on expiry day itself)."""
    d, d1 = date.fromisoformat(day), date.fromisoformat(expiry)
    n = 0
    while d < d1:
        d += timedelta(days=1)
        if config.is_trading_day(d):
            n += 1
    return n


def sister_thrust(i, D, L=None, pts=None):
    """(sign, BANKNIFTY move, FINNIFTY move) in Nifty points over L s; sign 0 when the two do not both reach pts."""
    L = T["L"] if L is None else L
    pts = T["SIS"] if pts is None else pts
    F = D.fwd[i]
    bnf, fin = getattr(D, "bnf", None), getattr(D, "fin", None)
    if bnf is None or fin is None or i < L or not np.isfinite(F):
        return 0, None, None
    b1, b0, f1, f0 = float(bnf[i]), float(bnf[i - L]), float(fin[i]), float(fin[i - L])
    if not (b1 > 0 and b0 > 0 and f1 > 0 and f0 > 0):
        return 0, None, None
    bn, fn = F * math.log(b1 / b0), F * math.log(f1 / f0)
    s = 1 if (bn >= pts and fn >= pts) else (-1 if (bn <= -pts and fn <= -pts) else 0)
    return s, bn, fn


def heavy_thrust(i, D, L=None, pts=None, brd=None):
    """(sign, weighted move in Nifty points, weighted breadth) over L s; needs 70 % of the weight priced."""
    L = T["L"] if L is None else L
    pts = T["HW"] if pts is None else pts
    brd = T["BRD"] if brd is None else brd
    F = D.fwd[i]
    hwl, w = getattr(D, "hwl", None), getattr(D, "hww", None)
    if hwl is None or w is None or i < L or not np.isfinite(F):
        return 0, None, None
    d = hwl[i].astype(float) - hwl[i - L].astype(float)
    ok = np.isfinite(d)
    den = float(w[ok].sum())
    if den <= 0 or den < T["COVER"] * float(w.sum()):
        return 0, None, None
    mv = F * float((d[ok] * w[ok]).sum()) / den
    b = float((np.sign(d[ok]) * w[ok]).sum()) / den
    s = 1 if (mv >= pts and b >= brd) else (-1 if (mv <= -pts and b <= -brd) else 0)
    return s, mv, b


class _ThrustMixin:
    KIND = "sis"

    def _thr_reset(self, D):
        self._thr_day = D.day
        self.thr_dte = days_to_expiry(D.day, D.expiry)
        self._thr_prev = {"CE": False, "PE": False}
        self._thr_last = {"CE": -10 ** 9, "PE": -10 ** 9}
        self.thr_log = []                               # (row, side, value 1, value 2, taken)

    def on_second(self, i, D, pos):
        sig = super().on_second(i, D, pos)              # the champion: its own state and, while holding, its exits
        if getattr(self, "_thr_day", None) != D.day:
            self._thr_reset(D)
        if self.thr_dte != 1:
            return sig if pos is not None else None
        s, a, b = sister_thrust(i, D) if self.KIND == "sis" else heavy_thrust(i, D)
        edge = None
        for side, sg in (("CE", 1), ("PE", -1)):
            on = s == sg
            if on and not self._thr_prev[side] and i - self._thr_last[side] >= T["GAP"]:
                self._thr_last[side] = i
                edge = side
            self._thr_prev[side] = on
        if pos is not None:
            if edge is not None:
                self.thr_log.append((int(i), edge, a, b, False))
            return sig
        if edge is None:
            return None
        p = self.p
        k = None
        if p["t0"] <= D.hm[i] < p["t1"] and i - self.last_exit >= p["cool"]:
            k = self._pick(i, D, edge, 40.0, p["hold"] / 60.0 * 0.5)
        self.thr_log.append((int(i), edge, a, b, k is not None))
        if k is None:
            return None
        self.best = None
        self._buy_v = 40.0
        if self.KIND == "sis":
            why = f"THR sisters BN {a:+.0f} FIN {b:+.0f} pts/{T['L']}s d1"
        else:
            why = f"THR heavyweights {a:+.0f} pts breadth {b:+.2f}/{T['L']}s d1"
        return ("BUY", k, edge, why)


class SisStrategy(_ThrustMixin, _y.Strategy):
    KIND = "sis"


class HwStrategy(_ThrustMixin, _y.Strategy):
    KIND = "hw"
