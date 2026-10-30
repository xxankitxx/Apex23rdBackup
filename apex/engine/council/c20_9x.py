"""R9_30 — the round-9 integrator: c20_8x (A8_10 Strategy, FINAL parts) + round-9 parts as switches.

Every switch is an extra name in `parts`.  With none of them, this class IS c20_8x (A8_10 FINAL) trade-for-trade.

CORRECTNESS (no P&L change on the 7 kit days, kept because the code is more correct):
  "l2"     R9_01 two-layer loop.  Layer 1 (no forward needed): premium SL and the theta clock are checked every held
           second even when the core returned early for lack of a forward; while the forward is stale (unchanged /
           missing >= FS s) the forward trail becomes a premium trail (bid falls |delta| x remaining trail pts from its
           best since the stale start).  Layer 2: no new BUY while the forward is stale.
  "ffirst" R9_02 floors before trail/time: an armed premium floor (BE_LOCK / GIVEBACK / RAMP) is the binding exit
           whenever the bid is at/below it (SL keeps precedence).  Same seconds -> same trades; only labels change.
  "seqcal" R9_07 seq rent in CALENDAR theta: rent_cal = 0.5*G*RV_min/|Theta_cal| (= realised/implied variance),
           threshold SEQ_CAL = 1.2 (c20_8x's 0.25 kit-theta = 0.96 calendar; 1.2 sits mid-plateau 0.88-1.5).
  "catch"  R9_08: roll the tau=5 s EMA of the forward through the rows the kit skips while an order is pending
           (what a per-second engine loop does) instead of restarting fs at the raw forward (+1 k, kit artefact fix).
GAINS:
  "dtr"    R9_20 normal days: forward trail x clip(|delta_entry| / |delta_now|, DT_LO, DT_HI) (tightens as the option
           goes ITM; a forward point is worth more premium there).
  "ramp"   R9_19 normal days: continuous profit floor instead of the +15 % -> entry / +60 % -> 70 % step:
           peak g in [ARM, R0): entry; [R0, R1): entry*(1 + g*k), k linear K0->K1; >= R1: entry*(1 + K1*g).
  "gbw"    R9_02: once the GIVEBACK floor is armed and the bid is >= floor + GB_MIN*entry, a FWD_TRAIL exit is
           overridden while the forward give-back is < GB_TRW x trail.
  "ivz"    R9_27 expiry days: veto a BUY when the rolling-ATM IV (30-s mean) rose over the last IZ_W s by more than
           IZ_Z x the day's RMS IZ_W-s ATM-IV change since 09:20 (needs IZ_MINH s of history).  No side block.
  "fy"     R9_06 FINAL_Y: seq 'loss' = exit return < FY_LOSS (-3 %); OTHER-side entry within SEQ_S after a non-loss
           needs rent_kit >= FY_FLIP; normal-day post-loss other-side entry needs RV/IV >= FY_RVI.
  "uw"     R9_21 expiry underwater rent stop: held >= UW_T, no new peak bid for UW_NM s, peak gain < UW_PK, bid gain
           < UW_CUR and rent_cal < UW_C -> exit RENT.
  "tie"    R9_24 expiry strike tie-breaker: score = capture% - TIE_LAM*100*|(|delta|) - 0.65| (capture with calendar
           theta, TIE_THM) among |delta| >= 0.52, +-3 strikes.
  "ptr"    R9_23 premium give-back trail (both modes; "ptre" = expiry days only): sb = EMA(PT_TAU s) of the held bid,
           pk = max sb since entry; once pk >= entry*(1+PT_PA) the forward trail is switched off and replaced by
           exit when sb <= pk*(1-PT_PQ) (PREM_TRAIL).  SL / TIME / floors unchanged and checked first.
All causal: rows <= i only.
"""
import importlib.util
import os

import numpy as np

from . import c20_8x as _a8   # engine copy: A8_10 (c20_8x) -> C20_20 -> C20_08, unchanged
FINAL = _a8.FINAL
CAL = 375.0 / 1440.0
ANN = 252 * 375 * 60.0

R9P = dict(FS=5, TRAIL_MODE="prem",
           SEQ_CAL=1.2,
           DT_LO=0.8, DT_HI=1.0,
           R_ARM=0.15, R0=0.25, R1=0.50, K0=0.45, K1=0.70,
           GB_MIN=0.05, GB_TRW=1.25,
           IZ_W=300, IZ_AVG=30, IZ_Z=1.5, IZ_MINH=600,
           FY_LOSS=-0.03, FY_FLIP=0.12, FY_RVI=1.0,
           UW_T=300, UW_NM=180, UW_PK=0.30, UW_CUR=-0.05, UW_C=0.8,
           TIE_LAM=5.0, TIE_THM=0.26,
           PT_PA=0.7, PT_PQ=0.08, PT_TAU=1.0)
FIXES = ("l2", "ffirst", "seqcal", "catch")
GAINS = ("dtr", "ramp", "gbw", "ivz", "fy", "uw", "tie", "ptr", "ptre")
FINAL_R9 = FINAL + FIXES + ("dtr", "ramp", "ivz", "ptre", "tie")   # chosen combination (R9_30)

_SER = {}


def atm_iv_series(D, avg=30):
    """a[i] = mean(IV_CE, IV_PE) (vol pts) at the strike nearest the forward at i; trailing avg-s mean (causal)"""
    key = (D.day, avg)
    if key in _SER:
        return _SER[key]
    _SER.clear()
    N = len(D.T)
    ks = np.unique(D.K)
    ref = np.where(np.isfinite(D.fwd), D.fwd, D.spot)
    kk = ks[np.argmin(np.abs(ks[None, :] - ref[:, None]), axis=1)]
    a = np.full(N, np.nan)
    for k in np.unique(kk):
        jc, jp = D.col.get((int(k), "CE")), D.col.get((int(k), "PE"))
        if jc is None or jp is None:
            continue
        m = kk == k
        a[m] = 100 * 0.5 * (D.iv[m, jc] + D.iv[m, jp])
    ok = np.isfinite(a)
    c = np.concatenate([[0], np.cumsum(np.where(ok, a, 0))])
    n = np.concatenate([[0], np.cumsum(ok)])
    lo = np.maximum(0, np.arange(N) - avg + 1)
    cnt = n[1:] - n[lo]
    s = np.where(cnt > 0, (c[1:] - c[lo]) / np.maximum(cnt, 1), np.nan)
    _SER[key] = s
    return s


class _R9Mixin:
    def __init__(self, parts=FINAL_R9, **kw):
        r = {k: kw.pop(k) for k in list(kw) if k in R9P}
        super().__init__(parts=parts, **kw)
        self.r = dict(R9P, **r)
        self.log = []

    # ------------------------------------------------------------------ state
    def _reset(self, D):
        super()._reset(D)
        self.last_called = None
        self.fage, self.fprev = 10 ** 6, np.nan
        self.stl = None
        self._pin = None
        self._fac = 1.0
        self.pb = self.pb_i = None
        if "ivz" in self.parts and D.dte0:
            W = int(self.r["IZ_W"])
            s = atm_iv_series(D, int(self.r["IZ_AVG"]))
            d = np.full(len(s), np.nan)
            d[W:] = s[W:] - s[:-W]
            d[:D.i_at(9, 20) + W] = np.nan
            ok = np.isfinite(d)
            self.dW = d
            self.cs2 = np.cumsum(np.where(ok, d * d, 0))
            self.cn = np.cumsum(ok)

    # ------------------------------------------------------------------ catch (R9_08)
    def _bridge(self, i, D):
        lc = self.last_called
        if lc is None or lc >= i - 1 or not np.isfinite(self.fs[lc]):
            return
        a = 1.0 / self.p["tau"]
        for r in range(lc + 1, i):
            f = D.fwd[r]
            self.fs[r] = self.fs[r - 1] + a * (f - self.fs[r - 1]) if np.isfinite(f) else self.fs[r - 1]

    # ------------------------------------------------------------------ l2 (R9_01)
    def _age(self, f):
        if not np.isfinite(f) or (np.isfinite(self.fprev) and f == self.fprev):
            self.fage += 1
        else:
            self.fage = 0
        if np.isfinite(f):
            self.fprev = f
        return self.fage >= self.r["FS"]

    # ------------------------------------------------------------------ dtr (R9_20)
    def _dfac(self, i, D, pos):
        if self._pin != pos["i_in"]:
            self._pin = pos["i_in"]
            self._fac = 1.0
            self._de = abs(float(D.delta[pos["i_in"], pos["j"]]))
        dn = abs(float(D.delta[i, pos["j"]]))
        if not (np.isfinite(dn) and dn > 0 and np.isfinite(self._de) and self._de > 0):
            return self._fac
        self._fac = float(np.clip(self._de / dn, self.r["DT_LO"], self.r["DT_HI"]))
        return self._fac

    # ------------------------------------------------------------------ floors (pex / ramp / ffirst / gbw)
    def _floor(self, e, g, dte0):
        x, r = self.x, self.r
        if "ramp" in self.parts and not dte0:
            if g < r["R_ARM"]:
                return None, None
            if g < r["R0"]:
                return e * (1 + x["BE_LOCK"]), "BE_LOCK"
            if g < r["R1"]:
                u = (g - r["R0"]) / max(r["R1"] - r["R0"], 1e-9)
                return e * (1 + max(x["BE_LOCK"], g * (r["K0"] + (r["K1"] - r["K0"]) * u))), "RAMP_LOCK"
            return e * (1 + r["K1"] * g), "GIVEBACK"
        if g >= x["GB_ARM"]:
            return e * (1 + x["GB_KEEP"] * g), "GIVEBACK"
        if g >= x["BE_ARM"]:
            return e * (1 + x["BE_LOCK"]), "BE_LOCK"
        return None, None

    def _inner(self, i, D, pos):
        P = self.parts
        if pos is None or "pex" not in P or not ({"ffirst", "ramp", "gbw"} & P):
            return super()._inner(i, D, pos)
        best0, last0 = self.best, self.last_exit
        self.parts = set(P) - {"pex"}
        try:
            sig = super()._inner(i, D, pos)
        finally:
            self.parts = P
        bid = D.bid[i, pos["j"]]
        if not np.isfinite(bid):
            return sig
        bid, e = float(bid), pos["entry"]
        fl, kind = self._floor(e, pos["peak_bid"] / e - 1, D.dte0)
        if fl is None:
            return sig
        if bid <= fl:
            if sig is None:
                return self._x(i, kind)
            if "ffirst" in P and sig[0] == "SELL" and sig[1] not in ("SL", kind):
                return ("SELL", kind)                 # same second: the floor is the binding reason
            return sig
        if "gbw" in P and kind == "GIVEBACK" and sig is not None and sig[0] == "SELL" and sig[1] == "FWD_TRAIL" \
                and bid >= fl + self.r["GB_MIN"] * e and best0 is not None \
                and abs(best0 - self.fs[i]) < self.p["trail"] * self.r["GB_TRW"]:
            self.best, self.last_exit = best0, last0      # undo the core exit, keep holding
            ce = pos["rr"] == "CE"
            self.best = max(self.best, self.fs[i]) if ce else min(self.best, self.fs[i])
            self.log.append((D.day, int(i), "gbw"))
            return None
        return sig

    # ------------------------------------------------------------------ entry vetoes (seqcal / fy)
    def _r8_veto(self, i, D, sig):
        P = self.parts
        if not ({"seqcal", "fy"} & P):
            return super()._r8_veto(i, D, sig)
        self.parts = set(P) - {"seq"}
        try:
            v = super()._r8_veto(i, D, sig)
        finally:
            self.parts = P
        if v or "seq" not in P:
            return v
        _, k, rr, _w = sig
        j = D.col.get((int(k), rr))
        L, x, r = self.last, self.x, self.r
        if L is None or i - L[2] >= x["SEQ_S"] or rr == L[1]:
            return None
        loss = L[0] < (r["FY_LOSS"] if "fy" in P else 0.0)
        rk = self._rent(i, D, j)                          # kit-theta rent (A8_10)
        thr = r["SEQ_CAL"] * CAL if "seqcal" in P else x["SEQ_C"]
        if loss:
            if np.isfinite(rk) and rk < thr:
                return "seq"
            if "fy" in P and not D.dte0:
                seg = np.asarray(D.fwd[max(0, i - 600):i + 1], float)
                d1 = seg[60:] - seg[:-60]
                rv = float(np.nanmean(d1 ** 2)) if len(d1) else np.nan
                f, iv = float(D.fwd[i]), float(D.iv[i, j])
                if np.isfinite(rv) and np.isfinite(f) and np.isfinite(iv) and iv > 0 and f > 0 \
                        and np.sqrt(rv / 60.0 * ANN) / f / iv < r["FY_RVI"]:
                    return "rvi"
        elif "fy" in P and np.isfinite(rk) and rk < r["FY_FLIP"]:
            return "flip"
        return None

    # ------------------------------------------------------------------ tie (R9_24, expiry picker)
    def _pick(self, i, D, side, m, hold_min):
        if "tie" not in self.parts or not D.dte0:
            return super()._pick(i, D, side, m, hold_min)
        r, dt = self.r, self.p["dt"]
        k0 = D.atm(i)
        cands = []
        for q in range(-3, 4):
            k = k0 + 50 * q
            j = D.col.get((int(k), side))
            if j is None or not np.isfinite(D.ask[i, j]) or D.age[i, j] > 5 or D.ask[i, j] <= 0:
                continue
            dl = abs(float(D.delta[i, j]))
            if not np.isfinite(dl) or dl < self.dmin:
                continue
            g, th = float(D.gamma[i, j]), abs(float(D.theta[i, j]))
            g = g if np.isfinite(g) else 0.0
            th = th if np.isfinite(th) else 0.0
            cap = 100 * (dl * m + 0.5 * g * m * m - th * r["TIE_THM"] * hold_min) / float(D.ask[i, j])
            cands.append((cap - r["TIE_LAM"] * 100 * abs(dl - dt), -abs(dl - dt), int(k)))
        if not cands:
            return None
        cands.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return cands[0][2]

    # ------------------------------------------------------------------ per second
    def _mark_last(self, i, D, pos):
        bid = D.bid[i, pos["j"]]
        self.last = ((bid / pos["entry"] - 1) if np.isfinite(bid) else 0.0, pos["rr"], i)

    def on_second(self, i, D, pos):
        if self.day != D.day:
            self._reset(D)
        P, r = self.parts, self.r
        if "catch" in P:
            self._bridge(i, D)
        self.last_called = i
        stale = self._age(D.fwd[i]) if "l2" in P else False
        give0 = None
        if "l2" in P and pos is not None and self.best is not None and i > 0 and np.isfinite(self.fs[i - 1]):
            give0 = (self.best - self.fs[i - 1]) if pos["rr"] == "CE" else (self.fs[i - 1] - self.best)
        base = self.p["trail"]
        pt_on = pos is not None and ("ptr" in P or ("ptre" in P and D.dte0))
        pt_arm = False
        if pt_on:
            if self._pt_pin != pos["i_in"]:
                self._pt_pin, self.sb, self.spk = pos["i_in"], None, None
            b = D.bid[i, pos["j"]]
            if np.isfinite(b):
                self.sb = float(b) if self.sb is None else self.sb + (float(b) - self.sb) / r["PT_TAU"]
                self.spk = self.sb if self.spk is None else max(self.spk, self.sb)
            pt_arm = self.spk is not None and self.spk >= pos["entry"] * (1 + r["PT_PA"])
        tn0 = getattr(self, "trail_now", None)          # R9_28 unit core: trail frozen at entry
        fac = 1.0
        if "dtr" in P and pos is not None and not D.dte0:
            fac = self._dfac(i, D, pos)
            self.p["trail"] = base * fac
        if pt_arm:
            self.p["trail"] = 1e9
        tn1 = None
        if tn0 is not None and pos is not None and (pt_arm or fac != 1.0):
            tn1 = 1e9 if pt_arm else tn0 * fac
            self.trail_now = tn1
        try:
            sig = super().on_second(i, D, pos)
        finally:
            self.p["trail"] = base
            if tn1 is not None and self.trail_now == tn1:
                self.trail_now = tn0
        if pos is None:
            self.stl = None
            self.pb = None
            if sig is not None and sig[0] == "BUY":
                if "l2" in P and stale:
                    return self._veto("stale")
                if "ivz" in P and D.dte0:
                    n, q = self.cn[i], self.cs2[i]
                    s = np.sqrt(q / n) if n >= r["IZ_MINH"] else np.nan
                    d = self.dW[i]
                    if np.isfinite(s) and s > 0 and np.isfinite(d) and d / s > r["IZ_Z"]:
                        self.log.append((D.day, int(i), "ivz", sig[2], float(d / s)))
                        return self._veto("ivz")
            return sig
        # ---- holding ----
        if self.pb is None or self.pb_i is None or self._pin_uw != pos["i_in"]:
            self._pin_uw, self.pb, self.pb_i = pos["i_in"], pos["peak_bid"], i
        if pos["peak_bid"] > self.pb:
            self.pb, self.pb_i = pos["peak_bid"], i
        if sig is not None:
            self.stl = None
            return sig
        bid = D.bid[i, pos["j"]]
        e = pos["entry"]
        if "l2" in P:
            why = None
            if np.isfinite(bid) and bid <= e * (1 - self.p["sl"]):
                why = "SL"
            elif D.T[i] - D.T[pos["i_in"]] >= self.p["hold"]:
                why = "TIME"
            elif stale:
                b = float(bid) if np.isfinite(bid) else np.nan
                if self.stl is None:
                    self.stl = [b, give0 if give0 is not None else 0.0]
                elif np.isfinite(b):
                    self.stl[0] = max(self.stl[0], b) if np.isfinite(self.stl[0]) else b
                if np.isfinite(b) and np.isfinite(self.stl[0]):
                    dl = abs(float(D.delta[i, pos["j"]]))
                    dl = dl if np.isfinite(dl) and dl > 0.05 else 0.6
                    if self.stl[0] - b >= dl * max(self.p["trail"] - self.stl[1], 0.0):
                        why = "STALE_PTRAIL"
            else:
                self.stl = None
            if why:
                self.stl = None
                self._mark_last(i, D, pos)
                return self._x(i, why)
        if pt_arm and self.sb <= self.spk * (1 - r["PT_PQ"]):
            self._mark_last(i, D, pos)
            return self._x(i, "PREM_TRAIL")
        if "uw" in P and D.dte0 and np.isfinite(bid):
            held = D.T[i] - D.T[pos["i_in"]]
            if held >= r["UW_T"] and pos["peak_bid"] / e - 1 < r["UW_PK"] and i - self.pb_i >= r["UW_NM"] \
                    and bid / e - 1 < r["UW_CUR"]:
                rk = self._rent(i, D, pos["j"])
                if np.isfinite(rk) and rk / CAL < r["UW_C"]:
                    self._mark_last(i, D, pos)
                    return self._x(i, "RENT")
        return None

    _pin_uw = None
    _pt_pin = None


class Strategy(_R9Mixin, _a8.Strategy):
    """c20_8x core (member 08's points/seconds) + the round-9 switches"""


_r28 = None




class LiveStrategy(Strategy):
    """Engine version (29 Oct night): identical to the kit class except the expiry IV-shock veto ("ivz"), whose
    day series the kit precomputes at the day's start. Here it is built second by second from the rows already seen
    (the engine stores option IV in PERCENT, rounded to 0.01 vol pt; the kit multiplied its decimal IV by 100)."""

    def __init__(self, parts=None, **kw):
        super().__init__(parts=FINAL_R9 if parts is None else parts, **kw)

    def _reset(self, D):
        P = self.parts
        had = "ivz" in P
        self.parts = set(P) - {"ivz"}
        try:
            super()._reset(D)
        finally:
            self.parts = P
        self._ivon = had and D.dte0
        if self._ivon:
            N = len(D.T)
            self.dW = np.full(N, np.nan)
            self.cs2 = np.zeros(N)
            self.cn = np.zeros(N, dtype=np.int64)
            self._ivr = np.full(N, np.nan)
            self._ivs = np.full(N, np.nan)
            self._ivl = -1
            self._q2, self._qn = 0.0, 0

    def _ivz_upto(self, i, D):
        W, A = int(self.r["IZ_W"]), int(self.r["IZ_AVG"])
        start = 300 + W                          # the kit blanks d before 09:20 + W
        for r in range(self._ivl + 1, i + 1):
            ref = D.fwd[r] if np.isfinite(D.fwd[r]) else D.spot[r]
            raw = np.nan
            if np.isfinite(ref) and len(D.K):
                ks = np.unique(D.K)
                k = int(ks[np.argmin(np.abs(ks - ref))])
                jc, jp = D.col.get((k, "CE")), D.col.get((k, "PE"))
                if jc is not None and jp is not None:
                    raw = 0.5 * (float(D.iv[r, jc]) + float(D.iv[r, jp]))     # percent already
            self._ivr[r] = raw
            seg = self._ivr[max(0, r - A + 1):r + 1]
            seg = seg[np.isfinite(seg)]
            self._ivs[r] = float(seg.mean()) if len(seg) else np.nan
            d = np.nan
            if r >= start and r - W >= 0:
                d = self._ivs[r] - self._ivs[r - W]
            if np.isfinite(d):
                self._q2 += d * d
                self._qn += 1
            self.dW[r], self.cs2[r], self.cn[r] = d, self._q2, self._qn
        self._ivl = max(self._ivl, i)

    def on_second(self, i, D, pos):
        if self.day != D.day:
            self._reset(D)
        if getattr(self, "_ivon", False):
            self._ivz_upto(i, D)
        return super().on_second(i, D, pos)


KitStrategy = Strategy
Strategy = LiveStrategy   # the adapter builds mod.Strategy()
