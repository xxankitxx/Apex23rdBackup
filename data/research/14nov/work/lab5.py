"""lab5: the 72-day, 5-minute study. Index bars from the fetched history, a synthetic at-the-money weekly option
(Black-76, IV = India VIX x a factor fitted on the recorded days) and the champion's exit ladder walked on the bars.
Coarser than fastlab (5-minute bars, model premium) but four times the days. Survivors go to fastlab for real prices."""
import os, sys, datetime as dt
sys.path.insert(0, r"D:\ApexOptions")
import numpy as np, pandas as pd
from apex import fastlab as FL

TV = r"D:\ApexOptions\data\research\14nov\work\tv"
HW = ["HDFCBANK", "ICICIBANK", "RELIANCE", "BHARTIARTL", "LT", "SBIN", "AXISBANK", "INFY", "KOTAKBANK", "M&M", "TCS", "ITC", "BAJFINANCE", "HINDUNILVR"]
WT = np.array([10.38, 9.05, 7.58, 5.1, 4.2, 3.79, 3.37, 3.35, 2.93, 2.52, 2.52, 2.52, 2.2, 1.85])
BANK = np.array([1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0], float)
NB = 75                                   # 5-minute bars 09:15 .. 15:25
HALF_SPREAD = 0.0011                      # the recorded median spread is 0.22 % of the premium
IVK = {0: 1.90, 1: 1.08}                  # ATM weekly IV / VIX by trading days to expiry (fitted below), else IVK_FAR
IVK_FAR = 0.93


def load():
    P = pd.read_parquet(os.path.join(TV, "panel_5m.parquet"))
    P = P[(P.index.time >= dt.time(9, 15)) & (P.index.time <= dt.time(15, 25))]
    days = sorted({d for d in P.index.date})
    out = []
    grid = [dt.time(9 + (15 + 5 * k) // 60, (15 + 5 * k) % 60) for k in range(NB)]
    for d in days:
        g = P[P.index.date == d]
        g = g.reindex([dt.datetime.combine(d, t) for t in grid])
        if g["NIFTY_c"].notna().sum() < 60:
            continue
        out.append((d, g))
    # expiry calendar: Tuesday, moved to the previous session when Tuesday has no bars
    dset = [d for d, _ in out]
    exp = {}
    for d in dset:
        e = d + dt.timedelta(days=(1 - d.weekday()) % 7)             # the next Tuesday (today if Tuesday)
        if e <= dset[-1]:
            while e not in dset and e > d:
                e -= dt.timedelta(days=1)
            if e < d:
                e = d
        exp[d] = e
    for known_d, known_e in ((dt.date(2026, 10, 19), dt.date(2026, 10, 19)), (dt.date(2026, 11, 9), dt.date(2026, 11, 9))):
        if known_d in exp:
            exp[known_d] = known_e
    # a session before a moved expiry points at the moved date
    for d in dset:
        if d < exp[d] <= dset[-1] and exp[d] not in dset:
            exp[d] = max(x for x in dset if x <= exp[d])
    D = []
    prev = None
    for d, g in out:
        o, h, l, c = (g[f"NIFTY_{k}"].ffill().bfill().to_numpy(float) for k in "ohlc")
        hw = np.stack([g[f"{s}_c"].ffill().to_numpy(float) for s in HW], 1)
        bn = g["BANKNIFTY_c"].ffill().to_numpy(float); fn = g["CNXFINANCE_c"].ffill().to_numpy(float)
        vix = g["INDIAVIX_c"].ffill().bfill().to_numpy(float)
        vol = g["NIFTY_v"].fillna(0).to_numpy(float)
        e = exp[d]
        dte = len([x for x in dset if d < x <= e]) if e <= dset[-1] else int(np.busday_count(d, e))
        Tsec = (dt.datetime.combine(e, dt.time(15, 30)) - pd.to_datetime([dt.datetime.combine(d, t) for t in grid])).total_seconds().to_numpy() - 300.0
        D.append(dict(day=d.isoformat(), o=o, h=h, l=l, c=c, hw=hw, bn=bn, fn=fn, vix=vix, vol=vol, dte=dte, dte0=(dte == 0),
                      T=np.maximum(Tsec, 300.0) / FL.YEAR_S, prev=prev))
        prev = dict(c=c[-1], h=h.max(), l=l.min(), o=o[0], day=d.isoformat())
    return D


def prem(F, K, T, iv, call):
    return float(FL.b76(F, K, T, iv, call))


def ladder(D, b, side, sl=0.15, tp=None, trail=None, hold=None, floor=None, stall=None):
    """decision at the close of bar b; fill at the open of bar b+1. Returns the trade or None."""
    e0 = b + 1
    if e0 >= NB - 1:
        return None
    x0 = D["dte0"]
    trail = (25.0 if x0 else 40.0) if trail is None else trail
    hold = (3 if x0 else 18) if hold is None else hold
    floor = ("pex" if x0 else "ramp") if floor is None else floor
    call = side == "CE"
    sg = 1.0 if call else -1.0
    F0 = D["o"][e0]
    k = IVK.get(D["dte"], IVK_FAR)
    iv = max(0.05, D["vix"][e0] / 100.0 * k)
    T0 = D["T"][e0]
    # strike with |delta| >= 0.52 nearest the target (0.52 normal, 0.65 expiry)
    Ks = (np.floor(F0 / 50.0) * 50.0 + 50.0 * np.arange(-4, 5)).astype(float)
    dl, _, _ = FL.greeks(F0, Ks, T0, iv, call)
    ad = np.abs(dl)
    tgt = 0.65 if x0 else 0.52
    ok = ad >= 0.52
    if not ok.any():
        return None
    K = float(Ks[int(np.argmin(np.where(ok, np.abs(ad - tgt), 9.0)))])
    e = prem(F0, K, T0, iv, call) * (1 + HALF_SPREAD)
    if not (e > 1.0):
        return None
    best = sg * F0; pk = e
    last = min(NB - 1, e0 + hold, 73)                              # flat by 15:20
    why = "FLAT" if last >= 73 else "TIME"
    xp = None; kx = last
    for i in range(e0, last + 1):
        T = D["T"][i]
        ivn = max(0.05, D["vix"][i] / 100.0 * k)
        adv = D["l"][i] if call else D["h"][i]
        fav = D["h"][i] if call else D["l"][i]
        # the adverse extreme first (pessimistic)
        p_adv = prem(adv, K, T, ivn, call)
        g = pk / e - 1.0
        fl = float(FL._floor(e, np.array(g), floor))
        if p_adv <= e * (1 - sl):
            xp, why, kx = e * (1 - sl), "SL", i; break
        if fl == fl and p_adv <= fl:
            xp, why, kx = fl, "FLOOR", i; break
        if best - sg * adv >= trail:
            xp, why, kx = prem(sg * (best - trail), K, T, ivn, call), "TRAIL", i; break
        # then the favourable extreme and the close
        best = max(best, sg * fav)
        p_fav = prem(fav, K, T, ivn, call)
        if tp is not None and p_fav >= e * (1 + tp):
            xp, why, kx = e * (1 + tp), "TP", i; break
        pk = max(pk, p_fav)
        pc = prem(D["c"][i], K, T, ivn, call)
        g = pk / e - 1.0
        fl = float(FL._floor(e, np.array(g), floor))
        if pc <= e * (1 - sl):
            xp, why, kx = pc, "SL", i; break
        if fl == fl and pc <= fl:
            xp, why, kx = pc, "FLOOR", i; break
        if best - sg * D["c"][i] >= trail:
            xp, why, kx = pc, "TRAIL", i; break
        if stall is not None and i - e0 + 1 >= stall[0] and g < stall[1] and abs(pc / e - 1) < stall[2]:
            xp, why, kx = pc, "STALL", i; break
        if i == last:
            xp = pc
    xp = xp * (1 - HALF_SPREAD)
    return dict(day=D["day"], b_in=e0, b_out=kx, side=side, K=K, e=e, ret=100.0 * (xp / e - 1.0), why=why, peak=100.0 * (pk / e - 1.0), dte=D["dte"])


def run(D, sigs, cool=1, **kw):
    out = []; free = 1
    for b, side, tag in sorted(sigs):
        if b < free or b < 1 or b > (64 if D["dte0"] else 68):
            continue
        t = ladder(D, b, side, **kw)
        if t is None:
            continue
        t["tag"] = tag
        out.append(t)
        free = t["b_out"] + cool
    return out


def feats(D):
    """per-bar arrays known at the close of the bar."""
    c, h, l, o = D["c"], D["h"], D["l"], D["o"]
    X = {}
    def lag(x, n):
        r = np.full(len(x), np.nan); r[n:] = x[n:] - x[:-n]; return r
    for n in (1, 2, 3, 4, 6, 12, 24):
        X[f"m{n}"] = lag(c, n)
    s = pd.Series(c)
    for n in (4, 12, 24):
        X[f"hi{n}"] = pd.Series(h).shift(1).rolling(n, min_periods=2).max().to_numpy()
        X[f"lo{n}"] = pd.Series(l).shift(1).rolling(n, min_periods=2).min().to_numpy()
        path = pd.Series(np.abs(np.diff(c, prepend=c[0]))).rolling(n, min_periods=2).sum().to_numpy()
        X[f"er{n}"] = np.abs(X[f"m{n}"]) / np.where(path > 0, path, np.nan)
    X["dhi"] = pd.Series(h).cummax().shift(1).to_numpy(); X["dlo"] = pd.Series(l).cummin().shift(1).to_numpy()
    lhw = np.log(D["hw"])
    for n in (1, 3, 6, 12):
        d = np.full(lhw.shape, np.nan); d[n:] = lhw[n:] - lhw[:-n]
        ok = np.isfinite(d)
        den = np.where(ok, WT, 0).sum(1)
        X[f"hw{n}"] = c * np.where(ok, d * WT, 0).sum(1) / np.where(den > 0, den, np.nan)
        X[f"brd{n}"] = (np.sign(np.where(ok, d, 0)) * WT).sum(1) / np.where(den > 0, den, np.nan)
        X[f"bn{n}"] = c * lag(np.log(D["bn"]), n); X[f"fn{n}"] = c * lag(np.log(D["fn"]), n)
    X["vix"] = D["vix"]; X["vix3"] = lag(D["vix"], 3)
    cv = np.cumsum(D["vol"]); tp_ = (h + l + c) / 3
    X["vwap"] = np.cumsum(tp_ * D["vol"]) / np.where(cv > 0, cv, np.nan)
    X["em20"] = c * (D["vix"] / 100.0 * IVK.get(D["dte"], IVK_FAR)) * np.sqrt(1200.0 / FL.YEAR_S)
    X["gap"] = np.full(NB, (o[0] - D["prev"]["c"]) if D["prev"] else np.nan)
    X["open"] = np.full(NB, o[0])
    return X
