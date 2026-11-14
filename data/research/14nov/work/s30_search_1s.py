"""Per-second entry families on every downloaded session of broker 1-second futures (normal days, model option,
champion exits), split into the sessions before the recorded window and the window itself; and, once enough history
is in, into an older and a newer half of the history."""
import os, sys, glob
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import fam, lab1s, hist1s
REC = set(FL.days())


def variants(D, X):
    V = {}
    V["CHAMPION pullback 20m 40pts 50%"] = fam.sig_pb(D, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0)
    for vm in (30.0, 50.0):
        V[f"pullback 20m {vm:.0f}pts 50%"] = fam.sig_pb(D, X, W=1200, vmin=vm, pb=0.5, amax=900, rs=5.0)
    for pb in (0.33, 0.4, 0.6):
        V[f"pullback 20m 40pts {int(pb * 100)}%"] = fam.sig_pb(D, X, W=1200, vmin=40.0, pb=pb, amax=900, rs=5.0)
    for rs in (3.0, 8.0):
        V[f"pullback 20m 40pts 50% resume {rs:.0f}"] = fam.sig_pb(D, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=rs)
    for W, vm in ((600, 28.3), (900, 34.6), (1800, 49.0)):
        V[f"pullback {W // 60}m {vm:.0f}pts 50%"] = fam.sig_pb(D, X, W=W, vmin=vm, pb=0.5, amax=int(0.75 * W), rs=5.0)
    for vz in (0.7, 1.0, 1.4):
        V[f"pullback 20m {vz} implied 50%"] = fam.sig_pb(D, X, W=1200, vz=vz, pb=0.5, amax=900, rs=5.0)
    for W, vm in ((600, 28.3), (1200, 40.0), (3600, 60.0)):
        V[f"breakout {W // 60}m {vm:.0f}pts"] = fam.sig_brk(D, X, W=W, vmin=vm)
    for age in (900, 1800, 3600):
        V[f"day high/low break, stood {age // 60}m"] = fam.sig_dayx(D, X, age=age)
    V["flag 20m"] = fam.sig_flag(D, X, W=1200, vmin=40.0, er=0.3)
    for Wn, z in ((20, 0.4), (20, 0.6), (60, 0.7), (30, 0.6)):
        V[f"fade {Wn}m {z} sigma"] = lab1s.sig_fade(D, Wn, z)
    V["blind, both sides, every 45 min"] = [(i, s, "") for i in range(1800, 20000, 2700) for s in ("CE", "PE")]
    return V


def one(day):
    D = lab1s.session(day, fwd=FL.load_day(day)["fwd"].copy()) if day in REC else lab1s.session(day)
    if D is None or D["dte0"]:
        return []
    X = lab1s.feats_full(D)
    rows = []
    for name, sig in variants(D, X).items():
        for t in lab1s.run(D, sig):
            t["variant"] = name; rows.append(t)
    return rows


if __name__ == "__main__":
    have = sorted({os.path.basename(p).split("_")[-1][:10] for p in glob.glob(os.path.join(hist1s.OUT, "fut_*.parquet"))})
    days = sorted(set(have) | REC)
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, days):
            rows += r
    T = pd.DataFrame(rows)
    T.to_parquet(os.path.join(hist1s.OUT, "search_1s.parquet"))
    hist = sorted(d for d in have if d not in REC)
    mid = hist[len(hist) // 2] if hist else ""
    print(f"broker history sessions {len(hist)} ({hist[0]} to {hist[-1]}); older half before {mid}; recorded window from 2026-10-19")
    out = []
    for v, g in T.groupby("variant"):
        r = dict(variant=v)
        for tag, s in (("old", g[g.day < mid]), ("new", g[(g.day >= mid) & (g.day < "2026-10-17")]), ("window", g[g.day >= "2026-10-19"])):
            ds = s.groupby("day").ret.sum()
            r[f"{tag}_n"] = len(s); r[f"{tag}_win"] = round(100 * (s.ret > 0).mean()) if len(s) else np.nan; r[f"{tag}_mean"] = round(s.ret.mean(), 2) if len(s) else np.nan
            r[f"{tag}_t"] = round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1) if len(ds) > 3 and ds.std(ddof=1) > 0 else np.nan
        h = g[g.day < "2026-10-17"]
        r["hist_ce"] = round(h[h.side == "CE"].ret.mean(), 2); r["hist_pe"] = round(h[h.side == "PE"].ret.mean(), 2)
        out.append(r)
    R = pd.DataFrame(out)
    R["k"] = np.minimum(R.old_mean.fillna(-99), R.new_mean.fillna(-99))
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 44); pd.set_option("display.max_rows", 100)
    print(R.sort_values("k", ascending=False).drop(columns=["k"]).to_string(index=False))
