"""C20_20 — the synthesiser: C20_08's two-mode parity-forward buyer plus the colleagues' parts as switchable layers.

Core (C20_08, imported read-only, its parameters unchanged):
  EXP  (expiry day, D.dte0): smoothed forward breaks its 10-min range with >= 20 pts in 150 s -> buy |delta|~0.65
       (1-ITM); exits: 25-pt forward trail, -15 % premium stop, 15-min theta clock.
  NORM (>= 1 DTE): 40-pt forward impulse in 20 min, 50 % pullback, 5-pt resumption -> buy |delta|~0.60; 40-pt forward
       trail, -15 % stop, 90-min clock.
Layers (each a switch in `parts`; every one reads rows <= i only):
  "oi"   C20_10 writers' agreement: over ATM +-4 strikes, net OI change of PE minus CE over the last OI_W s as % of
         near-money OI; a CE needs flow >= +OI_THR, a PE needs flow <= -OI_THR.
  "iv"   C20_09 vega guard: skip if the contract's 30-s mean IV, or the ATM straddle's, is > IV_UP vol pts above its
         value 3 min ago (IV popping with the move -> crush).
  "gr"   C20_03 gamma-rent gate (normal days only): 0.5*gamma*RV_min / |theta_min| >= GT, RV_min = realised variance
         of the forward per minute over the last 15 min.
  "orb"  C20_07 direction lock (normal days only): after the forward breaks its 09:15-09:45 range by ORB_BUF pts,
         only trade that side (flips if the other edge breaks); no lock before the first break.
  "cap"  C20_15 profit cap: once the bid gain has reached CAP_ARM, exit if more than CAP_Q of the peak gain is lost.
  "pm"   expiry-afternoon cut: no new expiry-day entries at/after PM_T (13:30) (C20_08's stated weak spot).
Parameters for the core: see C20_08/strategy.py (EXP, NORM). Owner's rules (all-in, buy-only, |delta| >= 0.52) are
enforced by the kit and the core's strike picker.
"""
import importlib.util
import os

import numpy as np

from . import c20_08 as _c08   # engine copy: the C20_08 core, unchanged

ALL_PARTS = ("exp", "norm", "oi", "iv", "gr", "orb", "cap", "pm")
DEFAULT_PARTS = ("exp", "norm", "iv", "orb")   # final set, chosen by ablation (report.md); other layers stay switchable

PAR = dict(
    OI_W=300, OI_N=4, OI_THR=1.0,     # writers' flow window (s), strikes each side, % threshold   (C20_10)
    IV_UP=0.3,                        # vol pts, 3-min rise allowed at entry                        (C20_09)
    GT=0.7, RVW=900,                  # gamma-rent ratio, realised-variance window (s)              (C20_03)
    ORB_END=585.0, ORB_BUF=5.0,       # opening range 09:15-09:45 (minutes since midnight), break buffer (C20_07)
    CAP_ARM=0.30, CAP_Q=0.5,          # profit cap: armed at +30 %, give back at most half of peak gain (C20_15)
    PM_T=13 * 60 + 30,                # expiry: no new entry from 13:30
)


def _m(a):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    return float(a.mean()) if len(a) else float("nan")


class Strategy(_c08.Strategy):
    def __init__(self, parts=DEFAULT_PARTS, exp=None, norm=None, **kw):
        super().__init__(exp=exp, norm=norm)
        self.parts = set(parts)
        self.q = dict(PAR, **kw)
        self.ks = None
        self.blocked = {}

    def _reset(self, D):
        super()._reset(D)
        self.ks = np.unique(D.K)
        self.or_hi = self.or_lo = None
        self.lock = None
        self.pk_gain = 0.0

    # ---------- layers ----------
    def _flow(self, i, D):
        q = self.q
        i0 = i - int(q["OI_W"])
        if i0 < 0 or not np.isfinite(D.fwd[i]):
            return 0.0
        a = int(np.argmin(np.abs(self.ks - D.fwd[i])))
        pe = ce = tot = 0.0
        for k in self.ks[max(0, a - q["OI_N"]):a + q["OI_N"] + 1]:
            for rr in ("CE", "PE"):
                j = D.col.get((int(k), rr))
                if j is None:
                    continue
                o1, o0 = D.oi[i, j], D.oi[i0, j]
                if not (np.isfinite(o1) and np.isfinite(o0)) or o0 <= 0:
                    continue
                tot += o1
                if rr == "PE":
                    pe += o1 - o0
                else:
                    ce += o1 - o0
        return 100.0 * (pe - ce) / tot if tot > 0 else 0.0

    def _atm_iv(self, D, i):
        k = D.atm(i)
        jc, jp = D.col.get((int(k), "CE")), D.col.get((int(k), "PE"))
        if jc is None or jp is None:
            return float("nan")
        return 0.5 * (_m(D.iv[max(0, i - 29):i + 1, jc]) + _m(D.iv[max(0, i - 29):i + 1, jp]))

    def _iv_ok(self, i, D, j):
        if i < 210:
            return True
        own = 100 * (_m(D.iv[i - 29:i + 1, j]) - _m(D.iv[i - 209:i - 179, j]))
        atm = 100 * (self._atm_iv(D, i) - self._atm_iv(D, i - 180))
        if np.isfinite(own) and own > self.q["IV_UP"]:
            return False
        if np.isfinite(atm) and atm > self.q["IV_UP"]:
            return False
        return True

    def _gr_ok(self, i, D, j):
        g, th = float(D.gamma[i, j]), float(D.theta[i, j])
        if not (np.isfinite(g) and np.isfinite(th)):
            return False
        y = np.asarray(D.fwd[max(0, i - self.q["RVW"]):i + 1], dtype=float)
        dy = np.diff(y[np.isfinite(y)])
        if len(dy) < 60:
            return False
        rv_min = float(np.sum(dy * dy)) / (len(dy) / 60.0)
        return 0.5 * g * rv_min / max(abs(th), 1e-9) >= self.q["GT"]

    def _orb_update(self, i, D):
        f = D.fwd[i]
        if not np.isfinite(f):
            return
        if D.hm[i] < self.q["ORB_END"]:
            self.or_hi = f if self.or_hi is None else max(self.or_hi, f)
            self.or_lo = f if self.or_lo is None else min(self.or_lo, f)
        elif self.or_hi is not None:
            if f > self.or_hi + self.q["ORB_BUF"]:
                self.lock = "CE"
            elif f < self.or_lo - self.q["ORB_BUF"]:
                self.lock = "PE"

    def _veto(self, why):
        self.blocked[why] = self.blocked.get(why, 0) + 1
        return None

    # ---------- per second ----------
    def on_second(self, i, D, pos):
        if self.day != D.day:
            self._reset(D)
        P = self.parts
        if not D.dte0 and "orb" in P:
            self._orb_update(i, D)
        if pos is not None and "cap" in P:
            bid = D.bid[i, pos["j"]]
            if np.isfinite(bid):
                g = bid / pos["entry"] - 1.0
                self.pk_gain = max(self.pk_gain, g)
                if self.pk_gain >= self.q["CAP_ARM"] and g <= self.pk_gain * (1 - self.q["CAP_Q"]):
                    super().on_second(i, D, pos)          # keep the core's state (smoother/queues) in step
                    self.pk_gain = 0.0
                    return self._exit(i, "PCAP")
        if pos is None:
            self.pk_gain = 0.0
        sig = super().on_second(i, D, pos)               # the core always runs: its smoother needs every row
        if sig is None or sig[0] != "BUY":
            return sig
        # mode switches
        if D.dte0 and "exp" not in P:
            return None
        if not D.dte0 and "norm" not in P:
            return None
        _, k, rr, why = sig
        j = D.col.get((int(k), rr))
        if j is None:
            return None
        if D.dte0 and "pm" in P and D.hm[i] >= self.q["PM_T"]:
            return self._veto("pm")
        if not D.dte0 and "orb" in P and self.lock is not None and rr != self.lock:
            return self._veto("orb")
        if "oi" in P:
            fl = self._flow(i, D)
            if (fl if rr == "CE" else -fl) < self.q["OI_THR"]:
                return self._veto("oi")
        if "iv" in P and not self._iv_ok(i, D, j):
            return self._veto("iv")
        if not D.dte0 and "gr" in P and not self._gr_ok(i, D, j):
            return self._veto("gr")
        return sig
