"""One account, one position at a time, four years (1-minute lab, model option, normal days): the pullback pattern
alone, the fades alone, and both in one pool. Per half, per quarter."""
import os, sys
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import lab1, h4
ALL = [D for D in h4.load() if not D["dte0"]]
G = {"pattern": lambda D: h4.fam(D, "pb", W=20, pb=0.4), "fade20": lambda D: h4.fam(D, "fade", W=20, z=0.6), "fade60": lambda D: h4.fam(D, "fade", W=60, z=0.7),
     "orbfade": lambda D: h4.fam(D, "orb", n=15, fade=True)}
SETS = {"pattern alone": ("pattern",), "fade20 + fade60": ("fade20", "fade60"), "the three fades": ("fade20", "fade60", "orbfade"),
        "pattern + fade20 + fade60": ("pattern", "fade20", "fade60"), "pattern + the three fades": ("pattern", "fade20", "fade60", "orbfade")}
rows = []
for D in ALL:
    sig = {k: [(b, s, k) for b, s, _ in f(D)] for k, f in G.items()}
    for name, ks in SETS.items():
        for t in lab1.run(D, sorted(sum((sig[k] for k in ks), [])), model=True):
            t["set"] = name; rows.append(t)
T = pd.DataFrame(rows)
T.to_parquet(os.path.join(lab1.W, "composite.parquet"))
T["q"] = T.day.str[:4] + "Q" + ((T.day.str[5:7].astype(int) - 1) // 3 + 1).astype(str)
pd.set_option("display.width", 240)
out = []
days = [D["day"] for D in ALL]
for name, g in T.groupby("set", sort=False):
    r = dict(account=name)
    for tag, sel in (("2022-24", g.day < h4.SPLIT), ("2025-26", g.day >= h4.SPLIT)):
        s = g[sel]; nd = len([d for d in days if (d < h4.SPLIT) == (tag == "2022-24")])
        ds = s.groupby("day").ret.sum().reindex([d for d in days if (d < h4.SPLIT) == (tag == "2022-24")]).fillna(0)
        r[f"{tag} trades"] = len(s); r[f"{tag} per day"] = round(len(s) / nd, 1); r[f"{tag} win"] = round(100 * (s.ret > 0).mean()); r[f"{tag} per trade"] = round(s.ret.mean(), 2)
        r[f"{tag} total"] = round(s.ret.sum()); r[f"{tag} t"] = round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1)
    qq = g.groupby("q").ret.sum()
    r["quarters up"] = f"{int((qq > 0).sum())}/{len(qq)}"; r["worst quarter"] = round(qq.min()); r["best quarter"] = round(qq.max())
    out.append(r)
print(pd.DataFrame(out).to_string(index=False))
print("\nquarterly totals (% points, sum of trade results):")
print(T.pivot_table(index="set", columns="q", values="ret", aggfunc="sum").round(0).fillna(0).astype(int).loc[list(SETS)].to_string())
g = T[T.set == "pattern + fade20 + fade60"]
print("\nin the pooled account, by which entry took the trade:")
print(g.groupby("tag").ret.agg(trades="size", winners=lambda s: round(100 * (s > 0).mean()), per_trade=lambda s: round(s.mean(), 2), total=lambda s: round(s.sum())).to_string())
