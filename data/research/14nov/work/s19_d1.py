"""The day before expiry (D1) against the far days, real prices per second, account level (one position, all-in):
the champion's pattern alone, then with more entries switched on."""
import os, sys
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import fam
import json
D1 = tuple(sorted(d for d, v in json.load(open("D:/ApexOptions/data/research/14nov/work/dte.json")).items() if v == 1))
G = {"champ": (fam.sig_pb, dict(W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0)),
     "shallow": (fam.sig_pb, dict(W=1200, vmin=40.0, pb=0.33, amax=900, rs=5.0)),
     "loose": (fam.sig_pb, dict(W=1200, vz=1.0, pb=0.33, amax=900, rs=5.0)),
     "w600": (fam.sig_pb, dict(W=600, vmin=28.3, pb=0.5, amax=450, rs=5.0)),
     "w900": (fam.sig_pb, dict(W=900, vmin=34.6, pb=0.5, amax=675, rs=5.0)),
     "sis8": (fam.sig_sis, dict(L=60, pts=8.0)), "sis12": (fam.sig_sis, dict(L=60, pts=12.0)),
     "hw8": (fam.sig_hw, dict(L=60, pts=8.0, brd=0.5)), "hw12": (fam.sig_hw, dict(L=60, pts=12.0, brd=0.5)),
     "brk": (fam.sig_brk, dict(W=1200, vmin=40.0))}
SETS = {"1 champion pattern alone": ("champ",), "2 + shallower pullback (33 %)": ("shallow",), "3 + lower impulse and shallower": ("loose",),
        "4 + 10-minute scale": ("champ", "w600"), "5 + 15- and 10-minute scales": ("champ", "w900", "w600"),
        "6 + sister thrust (8 pts / 60 s)": ("champ", "sis8"), "7 + heavyweight thrust (8 pts / 60 s)": ("champ", "hw8"),
        "8 + sister and heavyweight thrusts (12 pts)": ("champ", "sis12", "hw12"), "9 everything": ("shallow", "w900", "w600", "sis8", "hw8"),
        "10 breakouts only (no pullback wanted)": ("brk",)}


def one(day):
    D = FL.load_day(day)
    if D["dte0"]:
        return []
    X = FL.features(D)
    sig = {k: [(i, s, k) for i, s, _ in fn(D, X, **kw) if not X["gap"][i]] for k, (fn, kw) in G.items()}
    rows = []
    for name, ks in SETS.items():
        allsig = sorted(sum((sig[k] for k in ks), []))
        for st, ex in (("", None), (" | stall 15", fam.stall(900, 0.08, 0.04))):
            for t in FL.run(D, allsig, extra=ex):
                t["set"] = name; t["stall"] = bool(st)
                rows.append(t)
    return rows


if __name__ == "__main__":
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, FL.days()):
            rows += r
    T = pd.DataFrame(rows)
    T["d1"] = T.day.isin(D1)
    T.to_parquet(r"D:\ApexOptions\data\research\14nov\work\d1.parquet")
    pd.set_option("display.width", 320); pd.set_option("display.max_colwidth", 60)
    comp = lambda d: 100 * (np.prod(1 + d.ret.to_numpy() / 100) - 1)
    for stall in (False, True):
        out = []
        for name, g in T[T.stall == stall].groupby("set", sort=False):
            a, b = g[g.d1], g[~g.d1]
            da = a.groupby("day").apply(comp).reindex(list(D1)).fillna(0); db = b.groupby("day").apply(comp)
            out.append(dict(account=name, D1_trades=len(a), D1_win=round(100 * (a.ret > 0).mean()), D1_mean=round(a.ret.mean(), 1), D1_pe_mean=round(a[a.side == "PE"].ret.mean(), 1),
                            D1_days=" ".join(f"{d[5:]}:{v:+.0f}" for d, v in da.items()), D1_sum=round(da.sum()),
                            FAR_trades=len(b), FAR_win=round(100 * (b.ret > 0).mean()), FAR_mean=round(b.ret.mean(), 1), FAR_sum=round(db.sum()), FAR_losing_days=int((db < 0).sum()), FAR_worst=round(db.min())))
        print(("\nWITH the 15-minute stall exit" if stall else "champion exits only") + " - D1 = the 3 sessions before expiry; FAR = the 11 other normal days (12 and 13 Nov untouched)")
        print(pd.DataFrame(out).to_string(index=False))
