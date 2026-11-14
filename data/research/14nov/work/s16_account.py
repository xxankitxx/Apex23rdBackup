"""Account level, normal days: the champion's pattern alone against the same pattern at three time-scales in one
account (one position at a time, same exits), with and without the 15-minute stall exit. 12 and 13 Nov are untouched."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import fam
HOLD = ("2026-11-12", "2026-11-13")
S = {"W1200": dict(W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0), "W900": dict(W=900, vmin=34.6, pb=0.5, amax=675, rs=5.0), "W600": dict(W=600, vmin=28.3, pb=0.5, amax=450, rs=5.0),
     "W750": dict(W=750, vmin=31.6, pb=0.5, amax=560, rs=5.0)}
SETS = {"champion pattern alone (20 min)": ("W1200",), "20 + 15 min": ("W1200", "W900"), "20 + 10 min": ("W1200", "W600"), "20 + 15 + 10 min": ("W1200", "W900", "W600"),
        "20 + 15 + 12.5 + 10 min": ("W1200", "W900", "W750", "W600")}


def one(day):
    D = FL.load_day(day)
    if D["dte0"]:
        return []
    X = FL.features(D)
    sig = {k: [(i, s, k) for i, s, _ in fam.sig_pb(D, X, **kw) if not X["gap"][i]] for k, kw in S.items()}
    rows = []
    for name, ks in SETS.items():
        allsig = sorted(sum((sig[k] for k in ks), []))
        for st, ex in (("", None), (" + stall 15", fam.stall(900, 0.08, 0.04))):
            for t in FL.run(D, allsig, extra=ex):
                t["set"] = name + st
                rows.append(t)
    return rows


if __name__ == "__main__":
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, FL.days()):
            rows += r
    T = pd.DataFrame(rows)
    T.to_parquet(r"D:\ApexOptions\data\research\14nov\work\account.parquet")
    days = sorted(T.day.unique())
    pd.set_option("display.width", 320); pd.set_option("display.max_colwidth", 60)
    out = []
    for name, g in T.groupby("set", sort=False):
        a = g[~g.day.isin(HOLD)]; h = g[g.day.isin(HOLD)]
        def comp(x):
            return 100 * (np.prod([np.prod(1 + d.ret.to_numpy() / 100) for _, d in x.groupby("day")]) - 1) if len(x) else 0.0
        dd = a.groupby("day").apply(lambda d: 100 * (np.prod(1 + d.ret.to_numpy() / 100) - 1)).reindex([d for d in days if d not in HOLD]).fillna(0)
        dh = h.groupby("day").apply(lambda d: 100 * (np.prod(1 + d.ret.to_numpy() / 100) - 1)).reindex(list(HOLD)).fillna(0)
        out.append(dict(account=name, trades=len(a), per_day=round(len(a) / 12, 1), win=round(100 * (a.ret > 0).mean(), 1), mean=round(a.ret.mean(), 2), sum_day_pct=round(dd.sum()),
                        losing_days=int((dd < 0).sum()), worst_day=round(dd.min(), 1), best_day=round(dd.max()), median_day=round(dd.median(), 1),
                        HELD_trades=len(h), HELD_wins=int((h.ret > 0).sum()), HELD_12nov=round(dh.iloc[0], 1), HELD_13nov=round(dh.iloc[1], 1)))
    print("12 normal days in sample, then the two untouched days (each day's trades compounded, all-in):")
    print(pd.DataFrame(out).to_string(index=False))
    for name in ("champion pattern alone (20 min)", "20 + 15 + 10 min", "20 + 15 + 10 min + stall 15"):
        g = T[T.set == name]
        dd = g.groupby("day").apply(lambda d: f"{len(d)}/{100 * (np.prod(1 + d.ret.to_numpy() / 100) - 1):+.0f}")
        print(f"\n{name}: trades/day % ->", "  ".join(f"{d[5:]}:{v}" for d, v in dd.items()))
