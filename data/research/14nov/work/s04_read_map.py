"""Read the opportunity map: the baseline of a blind buy, the opportunities per day, and how many the Conductor took."""
import sys, glob, json; sys.path.insert(0, r"D:\ApexOptions")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
W = r"D:\ApexOptions\data\research\14nov\work"
M = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(W + r"\map_*.parquet"))], ignore_index=True)
M["sg"] = np.where(M.side == "CE", 1.0, -1.0)
print("points", len(M), "days", M.day.nunique())
print("\n== a blind buy at any moment, champion exits ==")
for d, g in M.groupby("dte0"):
    print("expiry" if d else "normal", "n", len(g), "win %", round(100 * (g.ret > 0).mean(), 1), "mean %", round(g.ret.mean(), 2), "median", round(g.ret.median(), 2),
          "| >= +20 %:", round(100 * (g.ret >= 20).mean(), 1), "%  <= -10 %:", round(100 * (g.ret <= -10).mean(), 1), "%  median hold min", round(g.hold_s.median() / 60, 1))
print("\n== with or against the recent move (side agrees with the sign of the move) ==")
for L in (60, 300, 1200, 3600):
    a = M[np.sign(M[f"mom{L}"]) == M.sg]; b = M[np.sign(M[f"mom{L}"]) == -M.sg]
    for nm, g in (("with", a), ("against", b)):
        dd = g.groupby("day").ret.mean()
        print(f"mom{L:<5}{nm:8} n {len(g):6} win % {100 * (g.ret > 0).mean():5.1f} mean {g.ret.mean():6.2f}  days positive {int((dd > 0).sum())}/{len(dd)}")

# opportunities: runs of buy points that end >= +20 % on the same side, merged when under 5 minutes apart
C = json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))["days"]
print("\n== opportunities (a stretch where a buy would have ended at +20 % or better) ==")
tot = dict(opp=0, caught=0)
rows = []
for day, g in M.groupby("day"):
    D0 = FL.load_day(day)["t_open"]
    ct = [(int(t["t_in"] - D0), t["rr"], t["ret_pct"]) for t in (C.get(day, {}).get("trades") or [])]
    opps = []
    for side, s in g[g.ret >= 20].groupby("side"):
        ii = np.sort(s.i.to_numpy())
        if not len(ii):
            continue
        st = ii[0]; pv = ii[0]
        for x in ii[1:]:
            if x - pv > 300:
                opps.append((side, st, pv)); st = x
            pv = x
        opps.append((side, st, pv))
    opps = [o for o in opps if o[2] - o[1] >= 60]                 # at least a minute wide, not a lucky second
    caught = sum(1 for (sd, a, b) in opps if any(r == sd and a - 120 <= i <= b + 120 for i, r, _ in ct))
    best = g.groupby("side").ret.max().max()
    tot["opp"] += len(opps); tot["caught"] += caught
    rows.append((day, "exp" if g.dte0.iloc[0] else "", len(opps), caught, len(ct), round(best, 0),
                 round(sum(b - a for _, a, b in opps) / 60), ", ".join(f"{sd} {FL.hm(a)}-{FL.hm(b)}" for sd, a, b in sorted(opps, key=lambda o: o[1]))))
print(pd.DataFrame(rows, columns=["day", "", "opps", "caught", "cond_trades", "best_%", "opp_minutes", "when"]).to_string(index=False))
print("total opportunities", tot["opp"], "caught by the Conductor", tot["caught"])
M.to_parquet(W + r"\map_all.parquet")
