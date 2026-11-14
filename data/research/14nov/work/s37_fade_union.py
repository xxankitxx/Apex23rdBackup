"""More fade trades without thinning them: one account that fades a 0.6-sigma stretch over ANY of several windows.
Four years, 1-minute lab, model option; and real option bars on the sessions that have them."""
import os, sys
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import lab1, h4
from s24_fade import attach_real
ALL = [D for D in h4.load() if not D["dte0"]]
attach_real(ALL)
days = [D["day"] for D in ALL]
SETS = {"20m (fade20)": ((20, 0.6),), "20m + 60m@0.7 (the built pair)": ((20, 0.6), (60, 0.7)), "10m + 20m": ((10, 0.6), (20, 0.6)), "10m + 20m + 60m@0.7": ((10, 0.6), (20, 0.6), (60, 0.7)),
        "10 + 15 + 20m": ((10, 0.6), (15, 0.6), (20, 0.6)), "10 + 15 + 20 + 45 + 60m": ((10, 0.6), (15, 0.6), (20, 0.6), (45, 0.6), (60, 0.6)),
        "all six windows": ((10, 0.6), (15, 0.6), (20, 0.6), (30, 0.6), (45, 0.6), (60, 0.6))}
rows = []
for D in ALL:
    cache = {}
    for name, ws in SETS.items():
        sig = []
        for W, z in ws:
            if (W, z) not in cache:
                cache[(W, z)] = h4.fam(D, "fade", W=W, z=z)
            sig += [(b, s, f"{W}m") for b, s, _ in cache[(W, z)]]
        for model in ((True, False) if D["opt"] else (True,)):
            for t in lab1.run(D, sorted(sig), model=model):
                t["set"] = name; t["kind"] = "model" if model else "real"; rows.append(t)
T = pd.DataFrame(rows)
T["q"] = T.day.str[:4] + "Q" + ((T.day.str[5:7].astype(int) - 1) // 3 + 1).astype(str)
out = []
for name in SETS:
    g = T[(T.set == name) & (T.kind == "model")]; r = dict(account=name)
    for tag, sel in (("2022-24", g.day < h4.SPLIT), ("2025-26", g.day >= h4.SPLIT)):
        s = g[sel]; dd = [d for d in days if (d < h4.SPLIT) == (tag == "2022-24")]
        ds = s.groupby("day").ret.sum().reindex(dd).fillna(0)
        r[f"{tag} per day"] = round(len(s) / len(dd), 2); r[f"{tag} win"] = round(100 * (s.ret > 0).mean()); r[f"{tag} per trade"] = round(s.ret.mean(), 2); r[f"{tag} total"] = round(s.ret.sum())
        r[f"{tag} t"] = round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1)
    qq = g.groupby("q").ret.sum(); r["quarters up"] = f"{int((qq > 0).sum())}/{len(qq)}"; r["worst q"] = round(qq.min())
    a = T[(T.set == name) & (T.kind == "real")]
    r["REAL bars trades"] = len(a); r["REAL per trade"] = round(a.ret.mean(), 2); r["REAL win"] = round(100 * (a.ret > 0).mean())
    out.append(r)
pd.set_option("display.width", 260)
print(pd.DataFrame(out).to_string(index=False))
