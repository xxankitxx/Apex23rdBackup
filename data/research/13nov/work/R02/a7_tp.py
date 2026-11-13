"""Take-profit rules evaluable exactly from the trade table: a TP at level x fires at the first bid >= entry(1+x),
which happens iff the hold's peak bid reached it (peak_bid). Exit then = x (fill at that bid; a next-print fill is
ignored). Otherwise the trade is unchanged. Discover 19 Oct - 4 Nov, test 5 - 12 Nov. Trade-level only: the book's
later trades are kept as they were (a TP exit could change what follows)."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, math
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R02"
J = pd.read_pickle(W + r"\conductor_joined.pkl")
df = pd.read_pickle(W + r"\all_trades_slim.pkl")
POOL = ['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t']
SPLIT = "2026-11-05"
def prep(d):
    d = d.copy()
    d["ret"] = d["ret_pct"] / 100
    d["pk"] = d["peak_bid"] / d["entry"] - 1
    d["exp"] = d["day"] == d["expiry"]
    iv = d["iv_in"].where(d["iv_in"] < 3, d["iv_in"] / 100)
    d["sig30"] = d["delta_in"].abs() * d["fut_in"] * iv * math.sqrt(30 / (252 * 375)) / d["entry"]   # 1-sigma 30-min premium move, fraction
    return d
C, P = prep(J), prep(df[df.book.isin(POOL)])
print("sig30 median exp %.3f norm %.3f" % (C[C.exp].sig30.median(), C[~C.exp].sig30.median()))
rules = []
for x in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.80, 1.00):
    for mode in ("all", "exp", "norm"):
        rules.append((f"TP {x:.2f} {mode}", mode, lambda d, x=x: pd.Series(x, index=d.index)))
for k in (1.0, 1.5, 2.0, 3.0, 4.0):
    for mode in ("all", "exp", "norm"):
        rules.append((f"TP {k} sigma30 {mode}", mode, lambda d, k=k: k * d["sig30"]))
def apply(d, rule):
    name, mode, lv = rule
    L = lv(d)
    on = (d["exp"] if mode == "exp" else ~d["exp"] if mode == "norm" else pd.Series(True, index=d.index))
    hit = on & (d["pk"] >= L) & (L > 0)
    return np.where(hit, L, d["ret"]), hit
def daycomp(d, r):
    lr = np.log1p(np.clip(r, -0.99, None))
    return np.expm1(pd.Series(lr, index=d.index).groupby(d["day"]).sum())
res = []
for setn, d in (("conductor", C), ("pool5", P)):
    for rule in rules:
        r, hit = apply(d, rule)
        lr, lb = np.log1p(np.clip(r, -0.99, None)), np.log1p(d["ret"].clip(lower=-0.99))
        e, t = (d.day < SPLIT).values, (d.day >= SPLIT).values
        dc, db = daycomp(d, r), daycomp(d, d["ret"].values)
        res.append(dict(set=setn, rule=rule[0], fired=int(hit.sum()), d_dlog=100 * (lr - lb)[e].sum(), t_dlog=100 * (lr - lb)[t].sum(),
                        d_win=100 * ((r > 0)[e].mean() - (d["ret"] > 0)[e].mean()), t_win=100 * ((r > 0)[t].mean() - (d["ret"] > 0)[t].mean()),
                        lose_days=int((dc < 0).sum()), base_lose_days=int((db < 0).sum()),
                        no_best_day=100 * float(np.log1p(dc).sum() - np.log1p(dc).max()), base_no_best_day=100 * float(np.log1p(db).sum() - np.log1p(db).max())))
R = pd.DataFrame(res)
pd.set_option("display.width", 250)
for s in ("conductor", "pool5"):
    x = R[R.set == s].sort_values("d_dlog", ascending=False)
    print(f"\n== {s}: {len(x)} TP rules, top 12 by discovery; both-window positives: {((x.d_dlog > 0) & (x.t_dlog > 0)).sum()}")
    print(x.head(12).round(1).to_string(index=False))
    print(x[(x.d_dlog > 0) & (x.t_dlog > 0)].round(1).to_string(index=False))
R.to_csv(W + r"\a7_tp.csv", index=False)
# per-trade 'what a perfect exit at the peak bid would add' by reason, and capture of the available move
for s, d in (("conductor", C), ("pool5", P)):
    pos = d["pk"].clip(lower=0)
    print(f"\n{s}: realised sum {100*d.ret.sum():.0f} %, peak sum {100*pos.sum():.0f} % -> capture {100*d.ret.sum()/pos.sum():.0f} %; compounded per-day capture by window:")
    for nm, m in (("disc", d.day < SPLIT), ("test", d.day >= SPLIT)):
        print("  ", nm, "realised log %.0f, peak log %.0f, ratio %.2f" % (100*np.log1p(d.ret[m]).sum(), 100*np.log1p(pos[m]).sum(), np.log1p(d.ret[m]).sum()/np.log1p(pos[m]).sum()))
