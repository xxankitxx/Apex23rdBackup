"""R02 per-second exit simulator on ds_v2 (numpy only). Shared by the pilot (a4_paths.py) and phase B.

A trade's held contract is read from the fill to the forced-flat time (15:00 expiry, 15:20 normal), so a variant may
exit EARLIER or LATER than the book did. The c20_9x exit stack is rebuilt on that path (sim with V = {}) and every
variant changes one part of it. Exit fill: the bid one row after the trigger (the engine fills on the next print)."""
import math, os
from datetime import datetime, timezone, timedelta
import numpy as np
DS = r"D:\ApexOptions\data\research\ds_v2"
IST = timezone(timedelta(hours=5, minutes=30))
SQ2 = math.sqrt(2.0)


def ncdf(x):
    """standard normal CDF, Abramowitz-Stegun 7.1.26 on erf (|err| < 1.5e-7)"""
    z = np.abs(x) / SQ2
    t = 1.0 / (1.0 + 0.3275911 * z)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-z * z)
    return 0.5 * (1.0 + np.sign(x) * y)


def b76(F, K, T, s, ce):
    sT = s * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sT * sT) / sT
    d2 = d1 - sT
    if ce:
        return F * ncdf(d1) - K * ncdf(d2), ncdf(d1)
    return K * ncdf(-d2) - F * ncdf(-d1), ncdf(d1) - 1.0


def implied(px, F, K, T, ce, it=26):
    lo, hi = np.full(px.shape, 0.005), np.full(px.shape, 2.5)
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        p, _ = b76(F, K, T, mid, ce)
        up = p > px
        hi = np.where(up, mid, hi)
        lo = np.where(up, lo, mid)
    s = 0.5 * (lo + hi)
    _, d = b76(F, K, T, s, ce)
    return s, d


def ema(x, a):
    """y[i] = y[i-1] + a (x[i] - y[i-1]), y[0] = x[0]"""
    from scipy.signal import lfilter
    x = np.asarray(x, float)
    y, _ = lfilter([a], [1.0, -(1.0 - a)], x[1:], zi=[(1.0 - a) * x[0]])
    return np.r_[x[0], y]


def ts(day, hh, mm):
    y, m, d = (int(x) for x in day.split("-"))
    return datetime(y, m, d, hh, mm, tzinfo=IST).timestamp()


def ffill(a, first=np.nan):
    a = np.asarray(a, float).copy()
    ok = np.isfinite(a)
    if not ok.any():
        return np.full_like(a, first)
    idx = np.where(ok, np.arange(len(a)), 0)
    np.maximum.accumulate(idx, out=idx)
    out = a[idx]
    k0 = int(np.argmax(ok))
    out[:k0] = first if np.isfinite(first) else a[k0]
    return out


def load_part(part):
    z = np.load(os.path.join(DS, part + ".npz"))
    t = z["t"].astype(float)
    ks = z["strikes"]
    n = len(ks)
    order = np.argsort(ks)
    K = ks[order].astype(float)
    opt = z["opt"][:, :n][:, order].astype(np.float32)      # (N, n, 2 rr, 2 bid/ask)
    age = z["age"][:, :n][:, order].astype(np.float32)      # (N, n, 2)
    fut = ffill(z["fut"][:, 2].astype(float))
    bid, ask = opt[..., 0], opt[..., 1]
    ok = (bid > 0) & (ask >= bid) & (age <= 10)
    mid = np.where(ok, 0.5 * (bid + ask), np.nan)
    par = K[None, :] + mid[:, :, 0] - mid[:, :, 1]           # parity forward at each strike
    ix = np.clip(np.searchsorted(K, fut), 1, max(n - 2, 1))
    rows = np.arange(len(t))
    cand = np.stack([par[rows, np.clip(ix + d, 0, n - 1)] for d in (-1, 0, 1)], 1)
    with np.errstate(all="ignore"):
        F = np.nanmedian(cand, 1)
    F = ffill(F)
    fs = ema(F, 0.2)                                        # the core's tau = 5 s EMA
    return dict(t=t, K=K, bid=bid, ask=ask, age=age, F=F, fs=fs, fut=fut, exp=str(z["expiry"]))


def trade_path(P, tr):
    day, ce = tr["day"], tr["rr"] == "CE"
    if P["exp"] != tr["expiry"]:
        return None
    j = np.where(P["K"] == float(tr["strike"]))[0]
    if not len(j):
        return None
    j, r = int(j[0]), 0 if ce else 1
    t = P["t"]
    a = int(np.searchsorted(t, tr["t_in"]))
    expd = day == tr["expiry"]
    flat = ts(day, 15, 0) if expd else ts(day, 15, 20)
    b = int(np.searchsorted(t, flat, side="right"))
    if b - a < 5 or a >= len(t):
        return None
    bid, ask, ag = P["bid"][a:b, j, r].astype(float), P["ask"][a:b, j, r].astype(float), P["age"][a:b, j, r]
    ok = (bid > 0) & (ask >= bid) & (ag <= 15)
    bid = ffill(np.where(ok, bid, np.nan), tr.get("entry_bid") or tr["entry"])
    ask = ffill(np.where(ok, ask, np.nan), tr["entry"])
    tt = t[a:b]
    F, fs = P["F"][a:b], P["fs"][a:b]
    T = np.maximum((ts(tr["expiry"], 15, 30) - tt) / (365.0 * 86400.0), 1e-6)
    s, d = implied(0.5 * (bid + ask), F, float(tr["strike"]), T, ce)
    a0 = int(np.searchsorted(t, tr["t_in"] - 900))
    m1 = P["F"][a0:a + 1][::60]
    atr = float(np.mean(np.abs(np.diff(m1)))) if len(m1) > 3 else np.nan    # mean |1-min forward move|, 15 min before entry
    ia = int(min(np.searchsorted(tt, tr["t_out"]), len(tt) - 1))
    return dict(t=tt, bid=bid, ask=ask, F=F, fs=fs, iv=s, delta=d, T=T, ce=ce, exp=expd, atr=atr, ia=ia,
                e=float(tr["entry"]), ok=float(ok.mean()))


def first(mask):
    if not mask.size:
        return None
    k = int(np.argmax(mask))
    return k if mask[k] else None


def sim(p, V, book="c20_9x"):
    """c20_9x exit stack (normal: SL 15 %, forward trail 40 pts x delta factor, 90-min clock, ramp floors;
    expiry: SL, 25-pt trail, 15-min clock, break-even / give-back floors, premium trail after +70 %) with overrides V.
    c20_9v adds PGB. Not rebuilt: LVL_BOOK (9v), RENT_TRAIL (9t), the stale-forward premium trail. -> (row, reason)"""
    e, bid, fs, t = p["e"], p["bid"], p["fs"], p["t"]
    n = len(t)
    ce, expd = p["ce"], p["exp"]
    held = t - t[0]
    pk = np.maximum.accumulate(bid)
    g = pk / e - 1.0
    hits = {}
    sl = V.get("sl", 0.15)
    if sl is not None:
        sbid = ema(bid, 1.0 / V["sl_tau"]) if V.get("sl_tau") else bid     # stop on a smoothed bid (no 1-s flicker)
        hits["SL"] = first(sbid <= e * (1 - sl))
    if V.get("fsl") is not None and (expd or not V.get("fsl_exp_only", True)):   # thesis stop in forward points
        adv = (fs[0] - fs) if ce else (fs - fs[0])
        hits["FSL"] = first(adv >= V["fsl"])
    if V.get("tp_fix") is not None and (expd or not V.get("tp_exp_only", True)):
        hits["TPX"] = first(bid >= e * (1 + V["tp_fix"]))
    best = np.maximum.accumulate(fs) if ce else np.minimum.accumulate(fs)
    give = (best - fs) if ce else (fs - best)
    base = V.get("trail", 25.0 if expd else 40.0)
    if V.get("trail_atr") is not None:
        base = V["trail_atr"] * p["atr"] if np.isfinite(p["atr"]) else base
    if V.get("trail_mult") is not None:
        base = base * V["trail_mult"]
    fac = np.ones(n)
    if not expd and V.get("dtr", True):
        dn = np.abs(p["delta"])
        de = abs(float(p["delta"][0]))
        fac = np.clip(de / np.maximum(dn, 1e-6), 0.8, 1.0)
    trail = base * fac
    pt_arm = np.zeros(n, bool)
    if expd and V.get("ptre", True):
        pa, pq = V.get("pt_pa", 0.7), V.get("pt_pq", 0.08)
        pt_arm = pk >= e * (1 + pa)
        hits["PREM_TRAIL"] = first(pt_arm & (bid <= pk * (1 - pq)))
    if V.get("fwd_trail", True):
        hits["FWD_TRAIL"] = first((give >= trail) & ~pt_arm)
    hold = V.get("hold", 900 if expd else 5400)
    if hold is not None:
        hits["TIME"] = first(held >= hold)
    if V.get("floors", True):
        if not expd:
            RA, R0, R1, K0, K1 = V.get("r_arm", 0.15), 0.25, 0.50, 0.45, V.get("k1", 0.70)
            u = np.clip((g - R0) / (R1 - R0), 0, 1)
            fl = np.where(g < RA, -np.inf, np.where(g < R0, e * (1 + V.get("be_lock", 0.0)),
                          np.where(g < R1, e * (1 + np.maximum(0.0, g * (K0 + (K1 - K0) * u))), e * (1 + K1 * g))))
        else:
            fl = np.where(g >= 0.6, e * (1 + 0.7 * g), np.where(g >= V.get("be_arm_x", 0.15), e, -np.inf))
        hits["FLOOR"] = first(bid <= fl)
    if (book == "c20_9v" or V.get("pgb_all")) and not expd and V.get("pgb", True):
        sb = ema(bid, 1.0 / 20.0)
        spk = np.maximum.accumulate(sb)
        gg = spk / e - 1
        hits["PGB"] = first((gg >= 0.15) & (sb <= e * (1 + 0.6 * gg)))
    # ---- variant-only exits ----
    if V.get("np_T") is not None:                           # no-progress clock: at np_T s, peak gain still < np_x
        hits["NOPROG"] = first((held >= V["np_T"]) & (g < V["np_x"]))
    if V.get("ec_T") is not None:                           # early cut: at ec_T s still below ec_x and never above ec_pk
        hits["ECUT"] = first((held >= V["ec_T"]) & (held < V["ec_T"] + 30) & (bid / e - 1 < V["ec_x"]) & (g < V["ec_pk"]))
    if V.get("tp_sig") is not None:                         # take profit at k x the IV 1-sigma premium move in 30 min
        sig = abs(float(p["delta"][0])) * float(p["F"][0]) * float(p["iv"][0]) * math.sqrt(30.0 / (252 * 375.0))
        hits["TP"] = first(bid >= e + V["tp_sig"] * sig)
    if V.get("stall_S") is not None:                        # no new peak bid for S s and the gain below x
        newpk = np.r_[True, bid[1:] > pk[:-1]]
        last = np.where(newpk, np.arange(n), 0)
        np.maximum.accumulate(last, out=last)
        hits["STALL"] = first((held - held[last] >= V["stall_S"]) & (bid / e - 1 < V["stall_x"]))
    if V.get("pchand") is not None and np.isfinite(p["atr"]):   # premium chandelier in volatility units
        w = V["pchand"] * abs(float(p["delta"][0])) * p["atr"]
        hits["PCHAND"] = first((bid <= pk - w) & (g > V.get("pchand_arm", 0.0)))
    if V.get("theta_k") is not None:                        # decay-aware: time since peak x |theta/min| > k x gain held
        th = np.abs(p["theta_min"]) if "theta_min" in p else None
        if th is not None:
            newpk = np.r_[True, bid[1:] > pk[:-1]]
            last = np.where(newpk, np.arange(n), 0)
            np.maximum.accumulate(last, out=last)
            paid = th * (held - held[last]) / 60.0
            hits["THETA"] = first((paid > V["theta_k"] * np.maximum(bid - e, 0.5)) & (held >= 300))
    hits = {k: v for k, v in hits.items() if v is not None}
    if not hits:
        return n - 1, "FLAT"
    k = min(hits, key=lambda q: (hits[q], q != "SL"))
    return hits[k], k


def exit_ret(p, row):
    r = min(row + 1, len(p["bid"]) - 1)                     # fill on the next print
    return p["bid"][r] / p["e"] - 1.0


def add_theta(p, tr):
    """Black-76 theta per TRADING minute of the held option (calendar decay of a day spread over 375 minutes)"""
    ce = p["ce"]
    F, K, T, s = p["F"], float(tr["strike"]), p["T"], p["iv"]
    sT = s * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sT * sT) / sT
    phi = np.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
    th_year = -F * phi * s / (2 * np.sqrt(T))
    p["theta_min"] = th_year / 365.0 / 375.0
    return p
