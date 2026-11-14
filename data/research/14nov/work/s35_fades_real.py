"""The three-fades account on REAL 1-minute option bars (the sessions that have them), against the model on the same
sessions; and each fade alone."""
import os, sys
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import lab1, h4
from s24_fade import attach_real
ALL = [D for D in h4.load() if not D["dte0"]]
attach_real(ALL)
R = [D for D in ALL if D["opt"]]
G = {"fade20": lambda D: h4.fam(D, "fade", W=20, z=0.6), "fade60": lambda D: h4.fam(D, "fade", W=60, z=0.7), "orbfade": lambda D: h4.fam(D, "orb", n=15, fade=True),
     "pattern": lambda D: h4.fam(D, "pb", W=20, pb=0.4)}
SETS = {"the three fades": ("fade20", "fade60", "orbfade"), "fade20": ("fade20",), "fade60": ("fade60",), "orbfade": ("orbfade",), "pattern alone": ("pattern",)}
rows = []
for D in R:
    sig = {k: [(b, s, k) for b, s, _ in f(D)] for k, f in G.items()}
    for name, ks in SETS.items():
        ss = sorted(sum((sig[k] for k in ks), []))
        for model in (False, True):
            for t in lab1.run(D, ss, model=model):
                t["set"] = name; t["kind"] = "model" if model else "real"; rows.append(t)
T = pd.DataFrame(rows)
print(f"sessions with real option bars: {len(R)} ({R[0]['day']} to {R[-1]['day']})")
out = []
for name in SETS:
    r = dict(account=name)
    for kind in ("real", "model"):
        g = T[(T.set == name) & (T.kind == kind)]
        ds = g.groupby("day").ret.sum().reindex([D["day"] for D in R]).fillna(0)
        r[f"{kind} trades"] = len(g); r[f"{kind} win"] = round(100 * (g.ret > 0).mean()); r[f"{kind} per trade"] = round(g.ret.mean(), 2); r[f"{kind} total"] = round(g.ret.sum())
        r[f"{kind} t"] = round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1)
        if kind == "real":
            r["real CE"] = round(g[g.side == "CE"].ret.mean(), 2); r["real PE"] = round(g[g.side == "PE"].ret.mean(), 2)
            mm = g.assign(m=g.day.str[:7]).groupby("m").ret.sum()
            r["months up"] = f"{int((mm > 0).sum())}/{len(mm)}"
    out.append(r)
pd.set_option("display.width", 240)
print(pd.DataFrame(out).to_string(index=False))
