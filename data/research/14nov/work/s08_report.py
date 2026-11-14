"""Family report: per variant, both halves of the normal days, days positive, CE/PE split, how often the Conductor was flat."""
import sys, json; sys.path.insert(0, r"D:\ApexOptions")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
W = r"D:\ApexOptions\data\research\14nov\work"
which = sys.argv[1] if len(sys.argv) > 1 else "normal"
T = pd.read_parquet(W + rf"\fam_{which}.parquet")
C = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))["days"]
days = sorted(T.day.unique())
half = {d: (0 if k < len(days) / 2 else 1) for k, d in enumerate(days)}
T["h"] = T.day.map(half)
occ = {}
for d in days:
    t0 = int(np.load(FL.CACHE + "\\" + d + ".npz")["t_open"])
    occ[d] = [(t["t_in"] - t0, t["t_out"] - t0) for t in (C.get(d, {}).get("trades") or [])]
T["free"] = [not any(a <= r.i_in <= b for a, b in occ[r.day]) for r in T.itertuples()]
rows = []
for v, g in T.groupby("variant"):
    a, b = g[g.h == 0], g[g.h == 1]
    dd = g.groupby("day").ret.sum().reindex(days).fillna(0)
    ce = g[g.side == "CE"]; pe = g[g.side == "PE"]
    rows.append(dict(variant=v, n=len(g), per_day=round(len(g) / len(days), 1), win=round(100 * (g.ret > 0).mean(), 1), mean=round(g.ret.mean(), 2), sum=round(g.ret.sum()),
                     n1=len(a), win1=round(100 * (a.ret > 0).mean(), 0) if len(a) else np.nan, mean1=round(a.ret.mean(), 1) if len(a) else np.nan,
                     n2=len(b), win2=round(100 * (b.ret > 0).mean(), 0) if len(b) else np.nan, mean2=round(b.ret.mean(), 1) if len(b) else np.nan,
                     days_pos=int((dd > 0).sum()), days_neg=int((dd < 0).sum()), worst_day=round(dd.min()), best_day=round(dd.max()),
                     ce_mean=round(ce.ret.mean(), 1) if len(ce) else np.nan, pe_mean=round(pe.ret.mean(), 1) if len(pe) else np.nan, pe_n=len(pe),
                     free_pct=round(100 * g.free.mean()), top_share=round(100 * g.ret.max() / max(g.ret.sum(), 1e-9)) if g.ret.sum() > 0 else np.nan))
R = pd.DataFrame(rows)
R["score"] = np.minimum(R.mean1, R.mean2)
pd.set_option("display.width", 320); pd.set_option("display.max_rows", 200)
print(f"{which}: {len(days)} days; halves = {days[:len(days) // 2][0]}..{days[:len(days) // 2][-1]} | {days[len(days) // 2:][0]}..{days[-1]}")
print(R.sort_values("score", ascending=False).drop(columns=["score"]).to_string(index=False))
R.to_csv(W + rf"\fam_{which}_report.csv", index=False)
