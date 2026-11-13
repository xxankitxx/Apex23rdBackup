import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 step 8: at each trade's trigger, the forward-minus-future gap (signed with the trade), the forward's and the
future's own last-5-s move, and what the FORWARD did over the next 30/60/300 s after the fill.
All books and the five pool books, per day. Usage: py -3.13 s8_trade_gap.py <part> ... (feat_<part>.npz needed)"""
import os
import numpy as np, pandas as pd

W = r"D:\ApexOptions\data\research\13nov\work\R07"
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]


def rank(a):
    o = np.argsort(a, kind="stable"); r = np.empty(len(a)); r[o] = np.arange(len(a)); return r


def spear(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 15 or np.std(x[m]) == 0 or np.std(y[m]) == 0:
        return np.nan
    return float(np.corrcoef(rank(x[m]), rank(y[m]))[0, 1])


def at_time(t, y, tq):
    j = np.searchsorted(t, tq, side="right") - 1
    return np.where(j >= 0, y[np.clip(j, 0, None)], np.nan)


def ema_gap(t, x, tau=300.0):
    out = np.full(len(t), np.nan); prev = np.nan; tp = None
    for i in range(len(t)):
        v = x[i]
        if np.isfinite(v):
            prev = v if not np.isfinite(prev) else prev + (1 - np.exp(-(t[i] - tp) / tau)) * (v - prev)
            tp = t[i]
        out[i] = prev
    return out


T = pd.read_parquet(os.path.join(W, "flowcols.parquet"), columns=["day", "book", "t_in", "trigger_t", "ret_pct", "rr"])
T["day"] = T["day"].astype(str)
out = []
for p in sys.argv[1:]:
    g = T[T.day == p[:10]].copy()
    if g.empty:
        continue
    f = np.load(os.path.join(W, f"feat_{p}.npz"))
    t = f["t"]; fm = f["fm"].astype(float); fwd = f["fwd"].astype(float)
    gdev = (fwd - fm) - ema_gap(t, fwd - fm)
    sg = np.where(g.rr.values == "CE", 1.0, -1.0)
    trig = g.trigger_t.fillna(g.t_in).values.astype(float); tin = g.t_in.values.astype(float)
    g["gap_dev_w"] = at_time(t, gdev, trig) * sg
    g["fwd5_w"] = (at_time(t, fwd, trig) - at_time(t, fwd, trig - 5)) * sg
    g["fut5_w"] = (at_time(t, fm, trig) - at_time(t, fm, trig - 5)) * sg
    for h in (30, 60, 300):
        g[f"fwd_after{h}"] = (at_time(t, fwd, tin + h) - at_time(t, fwd, tin)) * sg
        g[f"fut_after{h}"] = (at_time(t, fm, tin + h) - at_time(t, fm, tin)) * sg
    out.append(g)
G = pd.concat(out)
for uni, GG in (("all books", G), ("pool books", G[G.book.isin(POOL)])):
    print(f"\n[{uni}] n by day", GG.groupby("day").size().to_dict())
    for c in ("gap_dev_w", "fwd5_w", "fut5_w"):
        print(f"  {c:10s} Spearman with ret per day:", {d[5:]: round(spear(q[c].values, q.ret_pct.values), 3) for d, q in GG.groupby("day")},
              " median", round(float(GG[c].median()), 2))
    for h in (30, 60, 300):
        print(f"  after the fill +{h:3d}s: forward median {GG[f'fwd_after{h}'].median():+.2f} (share>0 {np.mean(GG[f'fwd_after{h}'] > 0):.2f})"
              f"   future median {GG[f'fut_after{h}'].median():+.2f} (share>0 {np.mean(GG[f'fut_after{h}'] > 0):.2f})")
G.to_parquet(os.path.join(W, "s8_trade_gap.parquet"))
