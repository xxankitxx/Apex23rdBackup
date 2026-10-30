"""A8_10 — member 08's two-mode forward buyer with EVERY colleague add-on as a switch (factorial study).

Core = C20_08 (unchanged).  Layers from C20_20 (iv, orb, gr, cap, pm) plus two exits added here:
  "exh"  C20_13 exhaustion: on the smoothed forward, within the last 1200 s a >= EX_IMP-pt impulse (low before high for
         an up-move), extreme printed <= 240 s ago, 30-s velocity <= 0 (turned) and >= EX_PB pts given back from the
         extreme.  Exit a position on that side; block new entries on that side while it holds (or fired <= EX_BLK s ago
         without a new extreme since).
  "lvl"  t28_gap level booking (D-141): spot levels ahead fixed at entry (prior-day H/L/C from day_levels.json, round
         100s); when the best spot since entry came within LV_NEAR of the next level without breaking it by more than
         LV_BRK and spot then gives back LV_REJ from the best -> BOOK.
All causal: rows <= i only.  FINAL = seq+pex (expiry) + pbg+d52 (normal): the minimal combination that survives LODO.
"""
import importlib.util
import json
import os

import numpy as np

from . import c20_20 as _c20   # engine copy: C20_20 -> C20_08 core, unchanged

LEVELS_PATH = r"D:\ApexOptions\data\learning\day_levels.json"
ADDONS = ("iv", "orb", "gr", "cap", "pm", "exh", "lvl", "rw", "pbg", "d52", "seq", "th1", "orbx", "pex")
# pex = A8_06 premium exits: once bid >= +60 %, exit below entry*(1+0.7*peak gain); once bid >= +15 %, exit at entry.
# round-8 colleagues: rw = A8_01 expiry range-width guard (prev-600-s range of fs >= RW_MULT*vmin, vetoed breakout stays
# vetoed while it keeps signalling, gaps < 30 s); pbg = A8_02 normal pullback geometry (disarm retrace > 0.75 impulse or
# arm older than 900 s); d52 = A8_07 normal-day |delta| target 0.52; seq = A8_08 after a loser, an OTHER-side entry within
# 900 s needs rent = 0.5*G*RV(600 s, 60-s changes)/|Theta_kit| >= 0.25; th1 = A8_07 expiry: no entry if |theta|/ask > 1 %/min;
# orbx = opening-range (09:16-09:31) direction lock on EXPIRY days (A8_07).
EXTRA = dict(RW_MULT=2.0, RW_GAP=30, PB_DMAX=0.75, PB_AMAX=900, SEQ_S=900, SEQ_C=0.25, TH_PCT=1.0, OX_END=571.0, OX_BUF=5.0, GB_ARM=0.6, GB_KEEP=0.7, BE_ARM=0.15, BE_LOCK=0.0,
             EX_W=1200, EX_IMP=90.0, EX_FRESH=240, EX_PB=18.0, EX_V=30, EX_BLK=300,
             LV_NEAR=5.0, LV_REJ=10.0, LV_BRK=5.0)


def _prior(day):
    try:
        L = json.load(open(LEVELS_PATH, encoding="utf-8"))
        ks = sorted(k for k in L if k < day)
        if ks:
            p = L[ks[-1]]
            return [(p["hi"], "PDH"), (p["lo"], "PDL"), (p["close"], "PDC")]
    except Exception:
        pass
    return []


class Strategy(_c20.Strategy):
    def __init__(self, parts=None, exp=None, norm=None, **kw):
        parts = FINAL if parts is None else parts   # engine: the autopsy team's final combination
        ex = {k: kw.pop(k) for k in list(kw) if k in EXTRA}
        if "d52" in parts:
            norm = dict(norm or {}, dt=0.52)
        super().__init__(parts=parts, exp=exp, norm=norm, **kw)
        self.x = dict(EXTRA, **ex)
        self.exits = {}

    def _reset(self, D):
        super()._reset(D)
        self.levels = _prior(D.day)
        self.blk = None
        self.last = None            # (ret, side, i) of the last exit
        self.ox_hi = self.ox_lo = None
        self.ox_lock = None
        self.exh = {+1: -10 ** 9, -1: -10 ** 9}     # last second each direction's exhaustion held
        self.exh_ext = {+1: None, -1: None}
        self.lv = None
        self.best_sp = None
        self.exf = self._exh_pre(D) if "exh" in self.parts else None
        self.exh = {+1: -10 ** 9, -1: -10 ** 9}
        self.exh_ext = {+1: None, -1: None}

    _CACHE = {}

    def _exh_pre(self, D):
        """the exhaustion flags depend only on D.fwd (same EMA as the core): compute once per day and parameter set"""
        key = (D.day, tuple(sorted(self.x.items())))
        if key in Strategy._CACHE:
            return Strategy._CACHE[key]
        Strategy._CACHE.clear()
        N = len(D.T)
        fs = np.full(N, np.nan)
        a = 1.0 / self.pe["tau"]
        for i in range(N):
            f = D.fwd[i]
            if not np.isfinite(f):
                continue
            prev = fs[i - 1] if i > 0 else np.nan
            fs[i] = f if not np.isfinite(prev) else prev + a * (f - prev)
        fire = {+1: np.zeros(N, bool), -1: np.zeros(N, bool)}
        ext = {+1: np.full(N, np.nan), -1: np.full(N, np.nan)}
        save = self.fs
        self.fs = fs
        self.exh = {+1: -1, -1: -1}
        self.exh_ext = {+1: None, -1: None}
        for i in range(1, N):
            self._exh_update(i)
            for sg in (+1, -1):
                if self.exh[sg] == i:
                    fire[sg][i] = True
                    ext[sg][i] = self.exh_ext[sg]
        self.fs = save
        Strategy._CACHE[key] = (fire, ext)
        return fire, ext

    def _exh_step(self, i):
        for sg in (+1, -1):
            if self.exf[0][sg][i]:
                self.exh[sg] = i
                self.exh_ext[sg] = float(self.exf[1][sg][i])

    def _exh_update(self, i):
        x = self.x
        W, V = int(x["EX_W"]), int(x["EX_V"])
        if i < V + 5:
            return
        seg = self.fs[max(0, i - W):i + 1]
        if not np.isfinite(seg[-1]) or not np.isfinite(self.fs[i - V]):
            return
        ok = np.isfinite(seg)
        if ok.sum() < 60:
            return
        s = np.where(ok, seg, np.nan)
        ih, il = int(np.nanargmax(s)), int(np.nanargmin(s))
        hi, lo = s[ih], s[il]
        n = len(s) - 1
        v = (self.fs[i] - self.fs[i - V]) / V
        f = self.fs[i]
        for sg, ie, io, ext in ((+1, ih, il, hi), (-1, il, ih, lo)):
            if io < ie and abs(hi - lo) >= x["EX_IMP"] and n - ie <= x["EX_FRESH"] and sg * (ext - f) >= x["EX_PB"] \
                    and sg * v <= 0:
                self.exh[sg] = i
                self.exh_ext[sg] = ext

    def _exh_block(self, i, rr):
        sg = +1 if rr == "CE" else -1
        if i - self.exh[sg] > self.x["EX_BLK"]:
            return False
        e = self.exh_ext[sg]
        return e is None or sg * (self.fs[i] - e) <= 0        # no new extreme since the turn

    def _lv_init(self, i, D, rr):
        sp = float(D.spot[i])
        d = 1 if rr == "CE" else -1
        lv = [(a, b) for a, b in self.levels]
        base = np.floor(sp / 100.0) * 100.0
        lv += [(base + 100.0 * k, "R100") for k in range(-3, 5)]
        ahead = sorted([(a, b) for a, b in lv if (a - sp) * d > 0], key=lambda t: (t[0] - sp) * d)
        self.lv = (d, ahead)
        self.best_sp = sp

    def _lv_check(self, i, D):
        d, ahead = self.lv
        sp = float(D.spot[i])
        if not np.isfinite(sp):
            return False
        self.best_sp = max(self.best_sp, sp) if d > 0 else min(self.best_sp, sp)
        best = self.best_sp
        for lvv, _ in ahead:
            g = (best - lvv) * d
            if -self.x["LV_NEAR"] <= g <= self.x["LV_BRK"]:
                return (best - sp) * d >= self.x["LV_REJ"]
            if g < -self.x["LV_NEAR"]:
                return False
        return False

    # ---- round-8 add-ons ----
    def _pick(self, i, D, side, m, hold_min):
        if "rw" in self.parts and D.dte0:
            if self.blk is not None and self.blk[0] == side and i - self.blk[1] <= self.x["RW_GAP"]:
                self.blk = (side, i)
                self.blocked["rw"] = self.blocked.get("rw", 0) + 1
                return None
            hi, lo = self.qmax[0][1], self.qmin[0][1]
            if hi - lo < self.x["RW_MULT"] * self.p["vmin"]:
                self.blk = (side, i)
                self.blocked["rw"] = self.blocked.get("rw", 0) + 1
                return None
        return super()._pick(i, D, side, m, hold_min)

    def _pullback(self, i, fs, v, side, p):
        if "pbg" not in self.parts or p["pb"] <= 0:
            return super()._pullback(i, fs, v, side, p)
        a = self.arm
        if side is not None:
            if a is None or a[0] != side:
                self.arm = [side, self.fs[i - p["L"]], fs, fs, i]
            else:
                a[2] = max(a[2], fs) if side == "CE" else min(a[2], fs)
                a[3] = a[2]
            return None
        if a is None:
            return None
        if i - a[4] > min(p["W"], self.x["PB_AMAX"]):
            self.arm = None
            return None
        sd, base, ext, pbx = a[0], a[1], a[2], a[3]
        up = sd == "CE"
        a[2] = max(ext, fs) if up else min(ext, fs)
        a[3] = min(pbx, fs) if up else max(pbx, fs)
        imp = abs(a[2] - base)
        ret = (a[2] - a[3]) if up else (a[3] - a[2])
        if imp <= 0 or ret < p["pb"] * imp:
            return None
        if ret > self.x["PB_DMAX"] * imp:
            self.arm = None
            return None
        if (fs - a[3] if up else a[3] - fs) >= p["rs"]:
            self.arm = None
            return sd
        return None

    def _rent(self, i, D, j):
        g, th = float(D.gamma[i, j]), abs(float(D.theta[i, j]))
        seg = np.asarray(D.fwd[max(0, i - 600):i + 1], float)
        d1 = seg[60:] - seg[:-60]
        rv = float(np.nanmean(d1 ** 2)) if len(d1) else np.nan
        return 0.5 * g * rv / th if th > 0 and np.isfinite(g) else np.nan

    def _r8_veto(self, i, D, sig):
        P = self.parts
        _, k, rr, _w = sig
        j = D.col.get((int(k), rr))
        if "orbx" in P and D.dte0 and self.ox_lock is not None and rr != self.ox_lock:
            return "orbx"
        if "th1" in P and D.dte0 and abs(float(D.theta[i, j])) / float(D.ask[i, j]) * 100 > self.x["TH_PCT"]:
            return "th1"
        if "seq" in P and self.last is not None and self.last[0] < 0 and rr != self.last[1]                 and i - self.last[2] < self.x["SEQ_S"]:
            r = self._rent(i, D, j)
            if np.isfinite(r) and r < self.x["SEQ_C"]:
                return "seq"
        return None

    def _ox_update(self, i, D):
        f = D.fwd[i]
        if not np.isfinite(f):
            return
        if D.hm[i] < self.x["OX_END"]:
            self.ox_hi = f if self.ox_hi is None else max(self.ox_hi, f)
            self.ox_lo = f if self.ox_lo is None else min(self.ox_lo, f)
        elif self.ox_hi is not None:
            if f > self.ox_hi + self.x["OX_BUF"]:
                self.ox_lock = "CE"
            elif f < self.ox_lo - self.x["OX_BUF"]:
                self.ox_lock = "PE"

    def _x(self, i, why):
        self.exits[why] = self.exits.get(why, 0) + 1
        return self._exit(i, why)

    def on_second(self, i, D, pos):
        if self.day != D.day:
            self._reset(D)
        P = self.parts
        if "orbx" in P and D.dte0:
            self._ox_update(i, D)
        sig = self._inner(i, D, pos)
        if pos is not None and sig is not None and sig[0] == "SELL":
            bid = D.bid[i, pos["j"]]
            self.last = ((bid / pos["entry"] - 1) if np.isfinite(bid) else 0.0, pos["rr"], i)
        if pos is None and sig is not None and sig[0] == "BUY":
            v = self._r8_veto(i, D, sig)
            if v:
                return self._veto(v)
        return sig

    def _inner(self, i, D, pos):
        P = self.parts
        sig = super().on_second(i, D, pos)          # core + C20_20 layers (keeps smoother/queues in step)
        if "exh" in P and i > 0:
            self._exh_step(i)
        if pos is None:
            self.lv = None
        if pos is not None:
            if sig is not None:
                return sig
            if "lvl" in P:
                if self.lv is None:
                    self._lv_init(pos["i_in"], D, pos["rr"])
                if self._lv_check(i, D):
                    return self._x(i, "LVL_BOOK")
            if "pex" in P and np.isfinite(D.bid[i, pos["j"]]):
                bid, e = float(D.bid[i, pos["j"]]), pos["entry"]
                pg = pos["peak_bid"] / e - 1
                if pg >= self.x["GB_ARM"] and bid <= e * (1 + self.x["GB_KEEP"] * pg):
                    return self._x(i, "GIVEBACK")
                if pg >= self.x["BE_ARM"] and bid <= e * (1 + self.x["BE_LOCK"]):
                    return self._x(i, "BE_LOCK")
            if "exh" in P:
                sg = +1 if pos["rr"] == "CE" else -1
                if self.exh[sg] == i:
                    return self._x(i, "EXH")
            return None
        if sig is not None and sig[0] == "BUY" and "exh" in P and self._exh_block(i, sig[2]):
            return self._veto("exh")
        return sig
FINAL = ("exp", "norm", "seq", "pex", "pbg", "d52")   # alt with rw instead of seq: see reply (cliff at RW_MULT 2.1)
