"""71 days: thrust and breakout entries by trading days to expiry, on days NOT in the recorded set too (independent).
Index points after the event, and the model option walked through the champion ladder."""
import sys; sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import lab5
DD = lab5.load()
REC = {"2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02", "2026-11-03",
       "2026-11-04", "2026-11-05", "2026-11-06", "2026-11-09", "2026-11-11", "2026-11-12", "2026-11-13"}


def evs(D, X):
    c = D["c"]; E = {}
    def add(name, up, dn, gap=3):
        out = []; last = {1: -99, -1: -99}
        for b in range(2, 67):
            for s, m in ((1, up), (-1, dn)):
                if m[b] and b - last[s] >= gap:
                    out.append((b, "CE" if s > 0 else "PE", name)); last[s] = b
        E[name] = out
    with np.errstate(invalid="ignore"):
        for x in (8, 12, 18):
            add(f"sisters thrust {x} pts in 5 min", (X["bn1"] >= x) & (X["fn1"] >= x), (X["bn1"] <= -x) & (X["fn1"] <= -x))
            add(f"heavyweight thrust {x} pts in 5 min", (X["hw1"] >= x) & (X["brd1"] >= 0.5), (X["hw1"] <= -x) & (X["brd1"] <= -0.5))
            add(f"all agree {x} pts in 5 min", (X["bn1"] >= x) & (X["fn1"] >= x) & (X["hw1"] >= x) & (X["m1"] >= x), (X["bn1"] <= -x) & (X["fn1"] <= -x) & (X["hw1"] <= -x) & (X["m1"] <= -x))
        add("breakout 20 min, 40 pts", (c > X["hi4"]) & (X["m4"] >= 40), (c < X["lo4"]) & (X["m4"] <= -40), gap=6)
        add("breakout 20 min, 1.0 implied", (c > X["hi4"]) & (X["m4"] >= X["em20"]), (c < X["lo4"]) & (X["m4"] <= -X["em20"]), gap=6)
        add("heavyweights ahead of Nifty 15 min (10 pts)", (X["hw3"] - X["m3"] >= 10), (X["hw3"] - X["m3"] <= -10), gap=6)
        add("any 5-minute bar of 15 pts (no confirmation)", X["m1"] >= 15, X["m1"] <= -15)
    return E


rows = []
for D in DD:
    X = lab5.feats(D); c = D["c"]
    for name, ev in evs(D, X).items():
        for b, side, _ in ev:
            s = 1 if side == "CE" else -1
            t = lab5.ladder(D, b, side)
            rows.append(dict(fam=name, day=D["day"], dte=min(D["dte"], 2), rec=D["day"] in REC, side=side, f15=s * (c[min(b + 3, 73)] - c[b]), f30=s * (c[min(b + 6, 73)] - c[b]),
                             ret=t["ret"] if t else np.nan))
T = pd.DataFrame(rows)
T.to_parquet(r"D:\ApexOptions\data\research\14nov\work\dte71.parquet")
pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 60)
lab = {0: "expiry day", 1: "1 day to expiry", 2: "2+ days"}
for nm, T0 in (("ALL 71 days", T), ("only days NOT in the recorded set (independent of everything above)", T[~T.rec])):
    print("\n" + nm + ": days per group", {lab[k]: T0[T0.dte == k].day.nunique() for k in (0, 1, 2)})
    out = []
    for fam, g0 in T0.groupby("fam", sort=False):
        r = dict(event=fam)
        for k in (1, 0, 2):
            g = g0[g0.dte == k]
            dm = g.groupby("day").f30.mean()
            t = dm.mean() / (dm.std(ddof=1) / np.sqrt(len(dm))) if len(dm) > 3 and dm.std(ddof=1) > 0 else np.nan
            dr = g.groupby("day").ret.mean()
            tag = {1: "D1", 0: "D0", 2: "D2+"}[k]
            r[f"{tag}_n"] = len(g); r[f"{tag}_f30"] = round(g.f30.mean(), 1); r[f"{tag}_t"] = round(t, 1)
            r[f"{tag}_opt%"] = round(g.ret.mean(), 1); r[f"{tag}_win"] = round(100 * (g.ret > 0).mean()); r[f"{tag}_days+"] = f"{int((dr > 0).sum())}/{len(dr)}"
            if k == 1:
                r["D1_pe_opt%"] = round(g[g.side == "PE"].ret.mean(), 1)
        out.append(r)
    print(pd.DataFrame(out).to_string(index=False))
