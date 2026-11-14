"""Four years: the champion's pattern (1-minute high/low version) on 984 sessions. Real option bars on the 139
sessions that have them; a model option everywhere (IV = 20-session realised volatility x a factor fitted on the real
days, by sessions to expiry). Output: one row per trade."""
import os, sys, time
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import lab1
t0 = time.time()
days = lab1.sessions()
exp = lab1.expiry_map(days); dte = lab1.dte_map(days, exp)
fut = lab1._tab("fut"); opt = lab1._tab("opt"); spot = lab1._tab("spot")
FG = {d: g for d, g in fut.groupby("day")}
OG = {d: g for d, g in opt.groupby("day")}
SG = {d: g for d, g in spot.groupby("day")}
grid_t = pd.date_range("2000-01-01 09:15:00", periods=lab1.NB, freq="1min").strftime("%H:%M:%S")


def mk(day):
    g = FG[day].drop_duplicates("ts").set_index(FG[day].drop_duplicates("ts").ts.str[11:])
    g = g.reindex(grid_t)
    c = g.c.ffill().bfill().to_numpy(float)
    f = lambda col: np.where(np.isfinite(g[col].to_numpy(float)), g[col].to_numpy(float), c)
    D = lab1.Day(day=day, o=f("o"), h=f("h"), l=f("l"), c=c, v=g.v.fillna(0).to_numpy(float), expiry=exp[day], dte=dte[day], dte0=(dte[day] == 0), vix=None, opt=None, basis=0.0)
    secs = (pd.Timestamp(exp[day] + " 15:30:00") - pd.date_range(day + " 09:15:00", periods=lab1.NB, freq="1min")).total_seconds().to_numpy()
    D["T"] = np.maximum(secs - 60.0, 60.0) / FL.YEAR_S
    if day in SG:
        s = SG[day].drop_duplicates("ts"); s = s.set_index(s.ts.str[11:]).c.reindex(grid_t).ffill().bfill().to_numpy(float)
        if np.isfinite(s).any():
            D["basis"] = float(np.nanmedian(c - s))
    if day in OG:
        q = OG[day]; q = q[q.expiry == q.expiry.min()]
        o = {}
        for (k, r), x in q.groupby(["strike", "right"]):
            x = x.drop_duplicates("ts"); x = x.set_index(x.ts.str[11:]).reindex(grid_t)
            o[(float(k), "CE" if r == "call" else "PE")] = np.stack([x.o.to_numpy(float), x.h.to_numpy(float), x.l.to_numpy(float), x.c.ffill().to_numpy(float)], 1)
        D["opt"] = o
    return D


ALL = {}
closes = []
for d in days:
    ALL[d] = mk(d)
    closes.append(ALL[d]["c"][-1] - ALL[d]["basis"])
closes = np.array(closes)
lr = np.diff(np.log(closes), prepend=np.nan)
rv20 = pd.Series(lr).rolling(20, min_periods=10).std().shift(1).to_numpy() * np.sqrt(252)       # known before the session
print("loaded", len(days), "sessions in", round(time.time() - t0), "s; with option bars:", sum(1 for d in days if ALL[d]["opt"]))
# fit: real at-the-money IV at 11:00 over rv20, by sessions to expiry
rows = []
for i, d in enumerate(days):
    D = ALL[d]
    if not D["opt"] or not np.isfinite(rv20[i]):
        continue
    b = 105
    F = D["c"][b] - D["basis"]
    ks = sorted({k for (k, r) in D["opt"]})
    k = min(ks, key=lambda x: abs(x - F))
    if (k, "CE") in D["opt"] and (k, "PE") in D["opt"]:
        st = D["opt"][(k, "CE")][b, 3] + D["opt"][(k, "PE")][b, 3]
        if np.isfinite(st):
            iv = st / (0.7979 * F * np.sqrt(D["T"][b]))
            rows.append((d, min(D["dte"], 2), iv, rv20[i], iv / rv20[i]))
R = pd.DataFrame(rows, columns=["day", "dte", "iv", "rv", "k"])
print("real ATM IV / 20-session realised volatility, by sessions to expiry:\n", R.groupby("dte").k.agg(["median", "count"]).round(2).to_string(), "\n median IV %:", R.groupby("dte").iv.median().mul(100).round(1).to_dict())
K = R.groupby("dte").k.median().to_dict()
lab1.IVK = {0: 1.0, 1: 1.0}; lab1.IVK_FAR = 1.0
for i, d in enumerate(days):
    rv = rv20[i] if np.isfinite(rv20[i]) else np.nan
    ALL[d]["vix"] = 100.0 * max(0.06, rv * K.get(min(ALL[d]["dte"], 2), 1.2)) if rv == rv else None

V = {"hl": (lab1.sig_pb_hl, {}), "hl_pb0.4": (lab1.sig_pb_hl, dict(pb=0.4)), "hl_v35": (lab1.sig_pb_hl, dict(vmin=35.0)), "closes": (lab1.sig_pb, {}),
     "hl_scaled": (lab1.sig_pb_hl, dict(scale=25000.0)), "hl_pb0.4_scaled": (lab1.sig_pb_hl, dict(pb=0.4, scale=25000.0))}
rows = []
for d in days:
    D = ALL[d]
    if D["vix"] is None:
        continue
    if D["dte0"]:
        sets = {"exp_brk": lab1.sig_brk(D), "exp_brk_scaled": lab1.sig_brk(D, scale=25000.0)}
    else:
        sets = {nm: fn(D, **kw) for nm, (fn, kw) in V.items()}
    for nm, sig in sets.items():
        for t in lab1.run(D, sig, model=True):
            t["variant"] = nm; rows.append(t)
        if D["opt"]:
            for t in lab1.run(D, sig, model=False):
                t["variant"] = nm; rows.append(t)
T = pd.DataFrame(rows)
T.to_parquet(os.path.join(lab1.W, "four_years.parquet"))
print("trades", len(T), "in", round(time.time() - t0), "s")
# model against real on the sessions that have both
for nm in ("hl", "exp_brk"):
    a = T[(T.variant == nm) & (~T.model)]; b = T[(T.variant == nm) & (T.model) & T.day.isin(a.day.unique())]
    da = a.groupby("day").ret.sum(); db = b.groupby("day").ret.sum().reindex(da.index).fillna(0)
    print(f"{nm}: real-option sessions {a.day.nunique()}: real trades {len(a)} win {100 * (a.ret > 0).mean():.0f} % mean {a.ret.mean():+.2f} | model trades {len(b)} win {100 * (b.ret > 0).mean():.0f} % mean {b.ret.mean():+.2f} | day-sum correlation {np.corrcoef(da, db)[0, 1]:.2f}")
