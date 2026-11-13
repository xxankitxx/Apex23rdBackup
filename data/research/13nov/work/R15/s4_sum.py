import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np, json
W = r"D:\ApexOptions\data\research\13nov\work\R15"
S = pd.concat([pd.read_csv(W + f"\meta_summary_{p}.csv") for p in "ABC"]).drop_duplicates(["name","win"])
S["grp"] = S.name.str.split("_").str[0]
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
cols = ["name","n","sr","sum_day_pct","median_day_pct","losing_days","worst_day","sum_wo_best_day","mean_trade_pct"]
for w in ("LATE","ROLL"):
    x = S[S.win == w]
    base = x[x.name == "POOL"].iloc[0]
    print("=====", w, "variants", len(x)); print(base[cols].to_frame().T.round(1).to_string(index=False))
    for gname, gx in x.groupby("grp"):
        print("--", gname, len(gx), "variants | beat POOL sum:", int((gx.sum_day_pct > base.sum_day_pct).sum()),
              "| beat sr:", int((gx.sr > base.sr).sum()), "| beat both + fewer/equal losing days + wo_best_day>0:",
              int(((gx.sum_day_pct > base.sum_day_pct) & (gx.sr > base.sr) & (gx.losing_days <= base.losing_days) & (gx.sum_wo_best_day > 0)).sum()),
              "| median sum", round(gx.sum_day_pct.median(),1), "| median sr", round(gx.sr.median(),1))
        print(gx.sort_values("sum_day_pct", ascending=False)[cols].head(5).round(1).to_string(index=False))
# rank correlation of variant performance ROLL-early part vs LATE: does a variant good on 23 Oct-4 Nov stay good later?
