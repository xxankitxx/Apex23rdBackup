"""fastlab: a per-second research simulator on the recorded sessions (data/research/ds_v2). Seconds per day, not hours.

14 Nov (owner: "why does the replay run for hours. Can't you run them at superfast speeds?"). The engine replay steps
every book of the live system through every second in Python; a study of ONE entry idea does not need that. fastlab
loads a session once into arrays on a 1-second grid (09:15:00 to 15:30:00), and an entry idea is a list of
(row, side) signals scored by the champion's exit ladder with vectorised maths. 17 sessions run in a few seconds.

It is a research tool, not the engine: fills are the ask one second after the signal and the bid one second after the
exit decision (the engine's own delay), strikes come from the parity forward, exits are the c20 ladder
(normal day: -15 % premium stop, 40-pt forward trail, ramp floors, 90-min clock, flat 15:20;
expiry day: -15 %, 25-pt trail, +15 % -> entry / +60 % -> 70 % of peak, premium trail after +70 %, 15-min clock).
Anything that passes here still has to run in the engine as a shadow book before it can be believed.

    from apex import fastlab as FL
    D = FL.load_day("2026-11-06")                 # cached under data/research/fastlab/
    tr = FL.run(D, [(row, "CE", "why"), ...])     # one position at a time, the ladder exits
"""
import glob
import json
import os

import numpy as np
from scipy.special import ndtr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS = os.path.join(ROOT, "data", "research", "ds_v2")
SIS = os.path.join(ROOT, "data", "research", "13nov", "work", "R09", "sister")
CACHE = os.path.join(ROOT, "data", "research", "fastlab")
IST = 19800
N = 6 * 3600 + 15 * 60 + 1            # rows 09:15:00 .. 15:30:00
T_FLAT = 365 * 60                     # 15:20, forced flat
YEAR_S = 365.0 * 86400.0

NORM = dict(sl=0.15, trail=40.0, hold=5400, floor="ramp", ptrail=False, t0=60, t1=345 * 60, dt=0.52, cool=60)
EXP = dict(sl=0.15, trail=25.0, hold=900, floor="pex", ptrail=True, t0=60, t1=325 * 60, dt=0.65, cool=60)
RAMP = dict(R_ARM=0.15, R0=0.25, R1=0.50, K0=0.45, K1=0.70)
PEX = dict(BE_ARM=0.15, GB_ARM=0.60, GB_KEEP=0.70)
PT = dict(PA=0.70, PQ=0.08)


def days():
    out = set()
    for m in glob.glob(os.path.join(DS, "*.manifest.json")):
        try:
            j = json.load(open(m, encoding="utf-8"))
        except Exception:
            continue
        if j.get("rows", 0) > 0:
            out.add(str(j["part"])[:10])
    return sorted(out)


def hm(i):
    m = 555 + int(i) // 60
    return f"{m // 60:02d}:{m % 60:02d}"


def row_of(hhmm):
    h, m = hhmm.split(":")
    return (int(h) * 60 + int(m) - 555) * 60


def _ffill0(a):
    """forward-fill NaN along axis 0 (1-D or 2-D)."""
    a = np.asarray(a, float)
    one = a.ndim == 1
    if one:
        a = a[:, None]
    ok = np.isfinite(a)
    idx = np.where(ok, np.arange(len(a))[:, None], 0)
    np.maximum.accumulate(idx, axis=0, out=idx)
    out = a[idx, np.arange(a.shape[1])[None, :]]
    out[~np.maximum.accumulate(ok, axis=0)] = np.nan
    return out[:, 0] if one else out


def ema(x, tau):
    """causal EMA, a = 1 / tau; NaN rows carry the last value (the engine's fs)."""
    out = np.empty(len(x))
    a = 1.0 / tau
    prev = np.nan
    for i, v in enumerate(x):
        if v == v:
            prev = v if prev != prev else prev + a * (v - prev)
        out[i] = prev
    return out


# ── Black-76 on the parity forward (r = 0) ──────────────────────────────────────────────────────────────────────────
def b76(F, K, T, s, call):
    sq = s * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sq * sq) / sq
    d2 = d1 - sq
    c = F * ndtr(d1) - K * ndtr(d2)
    return np.where(call, c, c - F + K)


def iv_of(F, K, T, px, call):
    lo = np.full(np.shape(px), 0.01)
    hi = np.full(np.shape(px), 6.0)
    for _ in range(42):
        mid = 0.5 * (lo + hi)
        up = b76(F, K, T, mid, call) < px
        lo = np.where(up, mid, lo)
        hi = np.where(up, hi, mid)
    v = 0.5 * (lo + hi)
    intr = np.where(call, np.maximum(F - K, 0), np.maximum(K - F, 0))
    return np.where((px > intr + 1e-6) & np.isfinite(px), v, np.nan)


def greeks(F, K, T, s, call):
    """delta, gamma (per forward point), theta (premium points per minute of calendar time, negative)."""
    sq = s * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sq * sq) / sq
    pdf = np.exp(-0.5 * d1 * d1) / np.sqrt(2 * np.pi)
    delta = np.where(call, ndtr(d1), ndtr(d1) - 1.0)
    gamma = pdf / (F * sq)
    theta = -F * pdf * s / (2 * np.sqrt(T)) / (YEAR_S / 60.0)
    return delta, gamma, theta


# ── loading ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def _build(day):
    parts = []
    for p in sorted(glob.glob(os.path.join(DS, day + "*.npz"))):
        z = np.load(p, allow_pickle=True)
        if z["t"].ndim == 1 and len(z["t"]) and z["opt"].ndim == 4:
            parts.append(z)
    if not parts:
        return None
    K = np.array(sorted({int(k) for z in parts for k in z["strikes"]}))
    kix = {k: i for i, k in enumerate(K)}
    T, FU, FA, Q, AG, HW, SF = [], [], [], [], [], [], []
    for z in parts:
        n = len(z["strikes"])
        t = z["t"].astype(float)
        q = np.full((len(t), len(K), 2, 2), np.nan, np.float32)
        ag = np.full((len(t), len(K), 2), 1e9, np.float32)
        for j, k in enumerate(z["strikes"]):
            q[:, kix[int(k)]] = z["opt"][:, j]
            ag[:, kix[int(k)]] = z["age"][:, j]
        hw = np.where((z["hw"] > 0) & (z["hwa"] <= 30), z["hw"], np.nan).astype(float)
        sf = z["sf"].astype(float)
        sfm = np.where((sf[:, :, 0] > 0) & (sf[:, :, 1] >= sf[:, :, 0]) & (z["sfa"] <= 30), 0.5 * (sf[:, :, 0] + sf[:, :, 1]), np.nan)
        T.append(t); FU.append(z["fut"].astype(float)); FA.append(z["fa"].astype(float)); Q.append(q); AG.append(ag)
        HW.append(hw); SF.append(sfm)
    t = np.concatenate(T); fu = np.concatenate(FU); fa = np.concatenate(FA); q = np.concatenate(Q); ag = np.concatenate(AG)
    hw = np.concatenate(HW); sf = np.concatenate(SF)
    o = np.argsort(t, kind="stable")
    t, fu, fa, q, ag, hw, sf = t[o], fu[o], fa[o], q[o], ag[o], hw[o], sf[o]
    d0 = int(np.floor((t[0] + IST) / 86400) * 86400 - IST)
    t_open = d0 + 9 * 3600 + 15 * 60
    grid = t_open + np.arange(N)
    idx = np.searchsorted(t, grid, side="right") - 1
    ok = idx >= 0
    ix = np.where(ok, idx, 0)
    lag = np.where(ok, grid - t[ix], 1e9)                       # s since the last recorded row (a feed gap shows here)
    fut = fu[ix]
    fok = ok & (fut[:, 0] > 0) & (fut[:, 1] >= fut[:, 0]) & (fa[ix, 0] + lag <= 5)
    fmid = np.where(fok, 0.5 * (fut[:, 0] + fut[:, 1]), np.nan)
    opt = q[ix].copy(); opt[~ok] = np.nan
    oage = (ag[ix] + lag[:, None, None]).astype(np.float32)
    opt[oage > 30] = np.nan                                     # a quote older than 30 s is not a price
    hwg = np.where((ok & (lag <= 30))[:, None], hw[ix], np.nan)
    sfg = np.where((ok & (lag <= 30))[:, None], sf[ix], np.nan)
    z0 = parts[0]
    exp = str(z0["expiry"])
    # sister panel (R09 extractor): BANKNIFTY futures mid, FINNIFTY index, NIFTY spot, VIX
    sis = np.full((N, 4), np.nan)
    for p in sorted(glob.glob(os.path.join(SIS, day + "*.npz"))):
        s = np.load(p)
        st, X, A = s["t"].astype(float), s["X"], s["A"]
        r = np.round(st - t_open).astype(int)
        m = (r >= 0) & (r < N)
        bf = np.where((X[:, 6] > 0) & (X[:, 7] >= X[:, 6]) & (A[:, 3] <= 5), 0.5 * (X[:, 6] + X[:, 7]), np.nan)
        fn = np.where((X[:, 8] > 0) & (A[:, 4] <= 5), X[:, 8], np.nan)
        ns = np.where((X[:, 0] > 0) & (A[:, 0] <= 5), X[:, 0], np.nan)
        vx = np.where((X[:, 12] > 0) & (A[:, 6] <= 60), X[:, 12], np.nan)
        cur = sis[r[m]]
        new = np.stack([bf, fn, ns, vx], 1)[m]
        sis[r[m]] = np.where(np.isfinite(new), new, cur)
    # parity forward: median over near-the-money strikes of K + C - P (mids)
    cm = 0.5 * (opt[:, :, 0, 0] + opt[:, :, 0, 1]).astype(float)
    pm = 0.5 * (opt[:, :, 1, 0] + opt[:, :, 1, 1]).astype(float)
    syn = K[None, :] + cm - pm
    with np.errstate(all="ignore"):
        rough = np.nanmedian(syn, axis=1)
        near = np.abs(K[None, :] - rough[:, None]) <= 150
        fwd = np.nanmedian(np.where(near, syn, np.nan), axis=1)
    return dict(day=day, expiry=exp, dte0=np.array(exp == day), t_open=np.array(t_open), K=K, fmid=fmid, fwd=fwd,
                fbq=np.where(fok, fut[:, 4], np.nan), faq=np.where(fok, fut[:, 5], np.nan),
                fvol=np.where(ok, fut[:, 3], np.nan), opt=opt.astype(np.float32), lag=lag.astype(np.float32),
                hw=hwg.astype(np.float32), sf=sfg.astype(np.float32), w=z0["w"].astype(float)[:hw.shape[1]],
                g=np.array([str(x) for x in z0["g"]][:hw.shape[1]]), sym=np.array([str(x) for x in z0["sym"]][:hw.shape[1]]),
                sis=sis.astype(np.float32))


class Day(dict):
    __getattr__ = dict.__getitem__


def load_day(day, rebuild=False):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, day + ".npz")
    if rebuild or not os.path.exists(p):
        d = _build(day)
        if d is None:
            return None
        np.savez(p + ".tmp.npz", **d)
        os.replace(p + ".tmp.npz", p)
    z = np.load(p, allow_pickle=False)
    D = Day({k: z[k] for k in z.files})
    D["day"] = str(D["day"]); D["expiry"] = str(D["expiry"]); D["dte0"] = bool(D["dte0"]); D["t_open"] = int(D["t_open"])
    D["fs"] = ema(D["fwd"], 5.0)                               # the champion's smoothed forward
    D["T"] = np.maximum(_expiry_s(D) - (D["t_open"] + np.arange(N)), 60.0) / YEAR_S
    D["P"] = EXP if D["dte0"] else NORM
    return D


def _expiry_s(D):
    import datetime as dt
    y, m, d = (int(x) for x in D["expiry"].split("-"))
    return (dt.datetime(y, m, d, 15, 30) - dt.datetime(1970, 1, 1)).total_seconds() - IST


# ── contract choice and the exit ladder ─────────────────────────────────────────────────────────────────────────────
def pick(D, i, side, dt=None):
    """strike index with |delta| >= 0.52 closest to the target delta (0.52 normal, 0.65 expiry), from live quotes."""
    dt = D["P"]["dt"] if dt is None else dt
    F = D["fwd"][i]
    if not np.isfinite(F):
        return None
    c = 0 if side == "CE" else 1
    K = D["K"]
    j0 = int(np.argmin(np.abs(K - F)))
    js = np.arange(max(0, j0 - 5), min(len(K), j0 + 6))
    q = D["opt"][i, js, c].astype(float)
    mid = 0.5 * (q[:, 0] + q[:, 1])
    ok = np.isfinite(mid) & (q[:, 0] > 0) & (q[:, 1] >= q[:, 0])
    if not ok.any():
        return None
    T = D["T"][i]
    call = c == 0
    iv = iv_of(F, K[js].astype(float), T, mid, call)
    dl, _, _ = greeks(F, K[js].astype(float), T, np.where(np.isfinite(iv), iv, 0.15), call)
    ad = np.abs(dl)
    itm = (K[js] < F) if call else (K[js] > F)
    ad = np.where(np.isfinite(iv), ad, np.where(itm, 0.99, 0.0))     # no time value left: deep in the money
    good = ok & (ad >= 0.52)
    if not good.any():
        return None
    k = int(np.argmin(np.where(good, np.abs(ad - dt), 9.0)))
    return int(js[k])


def _floor(e, g, kind):
    """profit floor as a price, NaN where not armed. g = peak gain so far (fraction of entry)."""
    if kind == "ramp":
        R = RAMP
        u = np.clip((g - R["R0"]) / (R["R1"] - R["R0"]), 0, 1)
        k = R["K0"] + (R["K1"] - R["K0"]) * u
        f = np.where(g < R["R0"], e, e * (1 + g * k))
        return np.where(g >= R["R_ARM"], f, np.nan)
    if kind == "pex":
        f = np.where(g >= PEX["GB_ARM"], e * (1 + PEX["GB_KEEP"] * g), e)
        return np.where(g >= PEX["BE_ARM"], f, np.nan)
    return np.full(np.shape(g), np.nan)


def exit_ladder(D, i, side, j, P=None, extra=None):
    """Buy at the ask of row i+1, walk the ladder, sell at the bid one row after the decision.
    extra: optional f(ctx) -> row offsets (bool array over the hold) of an added exit rule, or None.
    Returns dict(i_in, i_out, ret, why, peak, e) or None when there is no fill."""
    P = D["P"] if P is None else P
    c = 0 if side == "CE" else 1
    a = i + 1
    if a >= N - 2:
        return None
    e = float(D["opt"][a, j, c, 1])
    if not (e == e and e > 0):
        return None
    b_end = min(N - 2, a + P["hold"], max(T_FLAT, a))
    bid = _ffill0(D["opt"][a:b_end + 2, j, c, 0].astype(float))
    bid = np.where(np.isfinite(bid), bid, e)                     # no bid yet: carry the entry (rare, first seconds)
    fs = D["fs"][a:b_end + 2]
    sg = 1.0 if c == 0 else -1.0
    L = b_end - a + 1
    b = bid[:L]
    f = sg * fs[:L]
    best = np.maximum.accumulate(np.maximum(f, sg * D["fs"][i]))
    pk = np.maximum.accumulate(np.maximum(b, e))
    g = pk / e - 1.0
    fl = _floor(e, g, P["floor"])
    conds = [("SL", b <= e * (1 - P["sl"])), ("FLOOR", np.isfinite(fl) & (b <= fl))]
    tr = (best - f) >= P["trail"]
    if P.get("ptrail"):
        on = g >= PT["PA"]
        conds.append(("PREM_TRAIL", on & (b <= pk * (1 - PT["PQ"]))))
        tr = tr & ~on
    conds.append(("TRAIL", tr))
    if P.get("tp"):
        conds.append(("TP", b >= e * (1 + P["tp"])))
    if extra is not None:
        x = extra(dict(D=D, i=i, a=a, side=side, sg=sg, e=e, b=b, f=f, g=g, pk=pk, best=best, L=L, j=j, c=c))
        if x is not None:
            conds.append(x)
    k, why = L - 1, ("FLAT" if b_end >= T_FLAT else "TIME")
    for name, m in conds:
        w = np.flatnonzero(m)
        if len(w) and w[0] < k:
            k, why = int(w[0]), name
    xb = float(bid[min(k + 1, len(bid) - 1)])
    return dict(i_in=a, i_out=a + k + 1, side=side, K=int(D["K"][j]), e=e, x=xb, ret=100.0 * (xb / e - 1.0), why=why,
                peak=100.0 * (float(pk[k]) / e - 1.0), hold_s=k + 1)


def run(D, signals, P=None, extra=None, cool=None, dt=None):
    """One position at a time. signals: iterable of (row, side, tag) sorted by row. Returns the trades."""
    P = D["P"] if P is None else P
    cool = P["cool"] if cool is None else cool
    out = []
    free = P["t0"]
    for i, side, tag in signals:
        if i < free or i < P["t0"] or i > P["t1"]:
            continue
        j = pick(D, i, side, dt)
        if j is None:
            continue
        t = exit_ladder(D, i, side, j, P, extra)
        if t is None:
            continue
        t["tag"] = tag
        t["day"] = D["day"]
        out.append(t)
        free = t["i_out"] + cool
    return out


# ── rolling helpers (causal: row i sees rows <= i) ──────────────────────────────────────────────────────────────────
def lagdiff(x, L):
    o = np.full(len(x), np.nan)
    o[L:] = x[L:] - x[:-L]
    return o


def roll_ext(x, W):
    """max and min of x over rows i-W .. i-1 (the current row excluded)."""
    import pandas as pd
    s = pd.Series(x).shift(1)
    return s.rolling(W, min_periods=max(2, W // 4)).max().to_numpy(), s.rolling(W, min_periods=max(2, W // 4)).min().to_numpy()


def roll_sum(x, W):
    c = np.cumsum(np.where(np.isfinite(x), x, 0.0))
    o = c.copy()
    o[W:] = c[W:] - c[:-W]
    return o


def stats(trades):
    r = np.array([t["ret"] for t in trades], float)
    if not len(r):
        return dict(n=0, sr=float("nan"), mean=float("nan"), sum=0.0)
    return dict(n=len(r), sr=float((r > 0).mean()), mean=float(r.mean()), sum=float(r.sum()))


# ── features: one value per second, row i reads rows <= i only ──────────────────────────────────────────────────────
def _wbasket(lp, w, L, mask=None):
    """weighted mean log return over L s; NaN when under 70 % of the weight has a price."""
    d = np.full(lp.shape, np.nan)
    d[L:] = lp[L:] - lp[:-L]
    ww = w if mask is None else w * mask
    ok = np.isfinite(d) & (ww > 0)
    num = np.where(ok, d * ww, 0.0).sum(1)
    den = np.where(ok, ww, 0.0).sum(1)
    return np.where(den >= 0.7 * ww.sum(), num / np.where(den > 0, den, 1.0), np.nan), d


def features(D):
    """dict of per-second arrays. Directional ones are signed up = positive; flip the sign for a PE."""
    import pandas as pd
    X = {}
    fs = D["fs"]
    fm = _ffill0(D["fmid"])
    X["tod"] = np.arange(N) / 60.0
    for L in (30, 60, 180, 300, 450, 600, 750, 900, 1200, 1800, 2400, 3600):
        X[f"mom{L}"] = lagdiff(fs, L)
    for W in (300, 450, 600, 750, 900, 1200, 1800, 3600):
        hi, lo = roll_ext(fs, W)
        X[f"hi{W}"], X[f"lo{W}"] = hi, lo
        X[f"brk{W}"] = np.where(fs > hi, fs - hi, np.where(fs < lo, fs - lo, 0.0))     # signed distance beyond the range
        X[f"rng{W}"] = hi - lo
        X[f"pos{W}"] = (fs - lo) / np.where(hi - lo > 0, hi - lo, np.nan) - 0.5          # -0.5 at the low, +0.5 at the high
    s = pd.Series(fs)
    dhi, dlo = s.cummax().to_numpy(), s.cummin().to_numpy()
    X["dhi"], X["dlo"] = dhi, dlo
    X["day_rng"] = dhi - dlo
    X["day_pos"] = (fs - dlo) / np.where(dhi - dlo > 0, dhi - dlo, np.nan) - 0.5
    first = fs[np.isfinite(fs)][0] if np.isfinite(fs).any() else np.nan
    X["mv_open"] = fs - first
    r1 = np.diff(fs, prepend=np.nan)
    for W in (60, 300, 900, 1800):
        X[f"rv{W}"] = np.sqrt(roll_sum(r1 * r1, W))                                     # realised move, points over W s
    d15 = np.abs(lagdiff(fs, 15))
    for W in (300, 1200, 3600):
        path = roll_sum(d15, W) / 15.0
        X[f"er{W}"] = np.abs(lagdiff(fs, W)) / np.where(path > 0, path, np.nan)
        X[f"ser{W}"] = lagdiff(fs, W) / np.where(path > 0, path, np.nan)                 # signed efficiency
    X["squeeze"] = X["rng300"] / np.where(X["rng3600"] > 0, X["rng3600"], np.nan)
    X["twap_d"] = fs - (s.expanding(min_periods=60).mean().to_numpy())
    dv = np.clip(np.diff(_ffill0(D["fvol"]), prepend=np.nan), 0, None)
    dv = np.where(np.isfinite(dv), dv, 0.0)
    cv = np.cumsum(dv)
    vwap = np.cumsum(np.where(np.isfinite(fm), fm, 0.0) * dv) / np.where(cv > 0, cv, np.nan)
    X["vwap_d"] = fm - vwap
    v60 = roll_sum(dv, 60)
    X["vr60"] = v60 / np.where(cv > 0, cv / np.maximum(np.arange(N), 1) * 60.0, np.nan)   # volume now vs the day's pace
    imb = (D["fbq"] - D["faq"]) / np.where(D["fbq"] + D["faq"] > 0, D["fbq"] + D["faq"], np.nan)
    im = pd.Series(imb)
    X["imb10"] = im.rolling(10, min_periods=3).mean().to_numpy()
    X["imb60"] = im.rolling(60, min_periods=10).mean().to_numpy()
    for L in (10, 60, 300):
        X[f"nf{L}"] = lagdiff(fm, L)
    # heavyweights, weighted by Nifty weight, in Nifty points
    w = D["w"]
    lc = np.log(_ffill0(D["hw"].astype(float)))
    ls = np.log(_ffill0(D["sf"].astype(float)))
    bank = np.isin(D["g"], ("bank", "nbfc")).astype(float)
    F0 = np.where(np.isfinite(fs), fs, np.nan)
    for L in (10, 60, 300, 1200):
        b, d = _wbasket(lc, w, L)
        X[f"hw{L}"] = F0 * b
        if L in (60, 300, 1200):
            ok = np.isfinite(d)
            den = np.where(ok, w, 0.0).sum(1)
            X[f"brd{L}"] = (np.sign(np.where(ok, d, 0.0)) * w).sum(1) / np.where(den > 0, den, np.nan)
        if L in (60, 300):
            bb, _ = _wbasket(lc, w, L, bank)
            bn, _ = _wbasket(lc, w, L, 1.0 - bank)
            X[f"bank_x{L}"] = F0 * (bb - bn)                                             # banks ahead of the rest
    for L in (10, 60):
        b, _ = _wbasket(ls, w, L)
        X[f"sfb{L}"] = F0 * b
    X["hw_gap10"] = X["hw10"] - X["nf10"]
    X["hw_gap60"] = X["hw60"] - X["nf60"]
    X["hw_gap300"] = X["hw300"] - X["nf300"]
    X["hw_gap1200"] = X["hw1200"] - X["mom1200"]
    X["sf_gap10"] = X["sfb10"] - X["nf10"]
    # sisters, in Nifty points
    sis = _ffill0(D["sis"].astype(float))
    with np.errstate(all="ignore"):
        lb, lf = np.log(sis[:, 0]), np.log(sis[:, 1])
    for L in (10, 60, 300):
        X[f"bn{L}"] = F0 * lagdiff(lb, L)
        X[f"fin{L}"] = F0 * lagdiff(lf, L)
        X[f"sis_gap{L}"] = 0.5 * (X[f"bn{L}"] + X[f"fin{L}"]) - X[f"nf{L}"]
    X["vix"] = sis[:, 3]
    X["vix300"] = lagdiff(sis[:, 3], 300)
    # at-the-money implied volatility from the straddle at the two strikes around the forward
    K = D["K"].astype(float)
    cm = 0.5 * (D["opt"][:, :, 0, 0] + D["opt"][:, :, 0, 1]).astype(float)
    pm = 0.5 * (D["opt"][:, :, 1, 0] + D["opt"][:, :, 1, 1]).astype(float)
    st = cm + pm
    j = np.clip(np.searchsorted(K, np.where(np.isfinite(fs), fs, K[len(K) // 2])) - 1, 0, len(K) - 2)
    r = np.arange(N)
    u = np.clip((fs - K[j]) / (K[j + 1] - K[j]), 0, 1)
    sa = st[r, j] * (1 - u) + st[r, j + 1] * u
    sa = np.where(np.isfinite(sa), sa, np.where(np.isfinite(st[r, j]), st[r, j], st[r, j + 1]))
    X["straddle"] = sa
    iv = sa / (0.7979 * fs * np.sqrt(D["T"]))
    iv = pd.Series(iv).rolling(30, min_periods=5).mean().to_numpy()
    X["iv"] = 100.0 * iv
    X["iv300"] = lagdiff(X["iv"], 300)
    X["iv_rich"] = X["iv"] - pd.Series(X["iv"]).expanding(min_periods=300).median().to_numpy()
    em15 = fs * iv * np.sqrt(900.0 / YEAR_S)                                             # implied 15-minute move, points
    X["em15"] = em15
    X["rent"] = (X["rv900"] / np.where(em15 > 0, em15, np.nan)) ** 2                     # realised / implied variance
    X["gap"] = (D["lag"] > 5).astype(float)
    return X



# ── the engine's own strategy classes, replayed fast ────────────────────────────────────────────────────────────────
def live_day(D):
    """A council LiveDay with every row filled from a fastlab day (strategies only ever read rows <= i), so the REAL
    strategy class of a council book can be stepped through a recorded session in seconds."""
    from .engine.council import LiveDay
    L = LiveDay(D["day"], D["expiry"])
    cols = []
    for j, k in enumerate(D["K"]):
        for c, rr in ((0, "CE"), (1, "PE")):
            L.col[(int(k), rr)] = len(cols)
            cols.append((j, c, float(k), rr))
    L.K = np.array([x[2] for x in cols])
    L.rr = np.array([x[3] for x in cols])
    L.fwd[:] = D["fwd"]
    L.spot[:] = D["sis"][:, 2]
    L.fut[:] = D["fmid"]
    T = D["T"]
    for q, (j, c, k, rr) in enumerate(cols):
        bid = D["opt"][:, j, c, 0].astype(float)
        ask = D["opt"][:, j, c, 1].astype(float)
        mid = 0.5 * (bid + ask)
        L.bid[:, q], L.ask[:, q] = _ffill0(bid), _ffill0(ask)
        L.mid[:, q] = _ffill0(mid)
        L.ltp[:, q] = L.mid[:, q]
        L.age[:, q] = np.where(np.isfinite(bid), 0.5, 9e9)
        with np.errstate(all="ignore"):
            iv = _ffill0(iv_of(D["fwd"], k, T, mid, c == 0))
            dl, gm, th = greeks(D["fwd"], k, T, np.where(np.isfinite(iv), iv, 0.15), c == 0)
        L.iv[:, q], L.delta[:, q], L.gamma[:, q], L.theta[:, q] = 100.0 * iv, dl, gm, th
    L.bnf[:] = _ffill0(D["sis"][:, 0].astype(float))
    L.fin[:] = _ffill0(D["sis"][:, 1].astype(float))
    with np.errstate(all="ignore"):
        L.hwl = np.log(_ffill0(D["hw"].astype(float))).astype(np.float32)
    L.hww = D["w"].astype(float)
    return L


def play(D, L, council):
    """Step the council strategy module `council` (e.g. "c20_9y") through the session: a BUY fills at the ask of the
    next second, a SELL at the bid of the next second, forced flat as the adapter does. Open interest is not in the
    recorded set, so a rule that reads it (c20_9y's wall veto) does not fire here. Returns the trades."""
    import importlib
    s = importlib.import_module(f"apex.engine.council.{council}").Strategy()
    pos = None
    pend = None
    trades = []
    flat = (15 * 60) if L.dte0 else (15 * 60 + 20)
    for i in range(N - 2):
        L.i = i
        if pend is not None:                                   # the fill second: the strategy is not stepped
            kind, a = pend
            pend = None
            if kind == "BUY":
                k, rr, why = a
                j = L.col.get((int(k), rr))
                ask = L.ask[i, j] if j is not None else np.nan
                if np.isfinite(ask) and ask > 0:
                    b = L.bid[i, j]
                    pos = {"rr": rr, "strike": float(k), "j": j, "i_in": i, "entry": float(ask), "qty": 65,
                           "peak_bid": float(b) if np.isfinite(b) else float(ask), "st": {}, "why": why}
            else:
                bid = float(L.bid[i, pos["j"]])
                trades.append(dict(day=D["day"], i_in=pos["i_in"], i_out=i, t_in=hm(pos["i_in"]), t_out=hm(i), side=pos["rr"],
                                   K=pos["strike"], e=pos["entry"], x=bid, ret=100.0 * (bid / pos["entry"] - 1.0), why=a,
                                   tag=pos["why"], peak=100.0 * (pos["peak_bid"] / pos["entry"] - 1.0)))
                pos = None
            continue
        if pos is not None:
            b = L.bid[i, pos["j"]]
            if np.isfinite(b):
                pos["peak_bid"] = max(pos["peak_bid"], float(b))
            if L.hm[i] >= flat:
                pend = ("SELL", "TIME (forced flat)")
                continue
        act = s.on_second(i, L, pos)
        if not act:
            continue
        if act[0] == "BUY" and pos is None:
            j = L.col.get((int(act[1]), act[2]))
            if j is not None and abs(L.delta[i, j]) >= 0.5:
                pend = ("BUY", (act[1], act[2], act[3] if len(act) > 3 else ""))
        elif act[0] == "SELL" and pos is not None:
            pend = ("SELL", act[1] if len(act) > 1 else "")
    return trades


def _play_day(a):
    day, councils = a
    D = load_day(day)
    if D is None:
        return day, {}
    L = live_day(D)
    return day, {c: play(D, L, c) for c in councils}


def main(argv):
    """py -3.13 -m apex.fastlab play <council module> [more ...] [--days YYYY-MM-DD ...]   every recorded session by default"""
    if len(argv) < 2 or argv[0] != "play":
        print(main.__doc__)
        return 2
    import time
    from concurrent.futures import ProcessPoolExecutor
    a = argv[1:]
    ds = a[a.index("--days") + 1:] if "--days" in a else days()
    cs = a[:a.index("--days")] if "--days" in a else a
    t0 = time.time()
    res = {}
    with ProcessPoolExecutor(max_workers=max(1, min(8, (os.cpu_count() or 4) - 2))) as ex:
        for day, r in ex.map(_play_day, [(d, cs) for d in ds]):
            res[day] = r
    for c in cs:
        print(f"\n{c}")
        tot = wins = 0
        for day in sorted(res):
            tr = res[day].get(c) or []
            comp = 100.0 * (np.prod([1 + t["ret"] / 100.0 for t in tr]) - 1.0) if tr else 0.0
            tot += len(tr)
            wins += sum(t["ret"] > 0 for t in tr)
            print(f"  {day}  trades {len(tr):2d}  winners {sum(t['ret'] > 0 for t in tr):2d}  day {comp:+7.1f} %   "
                  + " ".join(f"{t['t_in']}{t['side'][0]}{t['ret']:+.0f}" for t in tr))
        print(f"  total trades {tot}, winners {wins} ({100.0 * wins / max(tot, 1):.0f} %)")
    print(f"\n{len(ds)} sessions x {len(cs)} book(s) in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
