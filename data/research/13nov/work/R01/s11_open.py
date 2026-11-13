import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
df = pd.read_pickle(r"D:\ApexOptions\data\research\13nov\work\R01\trades_small.pkl")
df["trig"] = df.trigger_t.fillna(df.t_in)
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
pd.set_option("display.width", 250)
rows = []
for d, g in df.groupby("day"):
    p = g[g.book.isin(POOL)].sort_values("trig")
    f = p.iloc[0]
    ex = bool(g.wx_expiry_day.astype(float).max() > 0)
    o = g[(g.trig < f.trig) & ~g.book.isin(POOL + ["conductor", "RAW"])]
    fam = lambda b: "t28" if b.startswith(("t28", "lvl_trail")) else "orb45" if b.startswith("spot_orb45") else None
    o2 = o[o.book.map(fam).notna()]
    rows.append(dict(day=d, expiry=ex, first_pool=f.time_in, day_move_then=round(float(f.wx_day_move), 1), range_then=round(float(f.wx_range_now), 1) if "wx_range_now" in g else None,
                     side=f.rr, ret=round(f.ret_pct, 1), n_before=len(o), t28_before=int((o2.book.map(fam) == "t28").sum()),
                     t28_sr=round((o2[o2.book.map(fam) == "t28"].ret_pct > 0).mean(), 2) if len(o2) else None,
                     t28_mean=round(o2[o2.book.map(fam) == "t28"].ret_pct.mean(), 1) if len(o2) else None,
                     orb_before=int((o2.book.map(fam) == "orb45").sum()), orb_mean=round(o2[o2.book.map(fam) == "orb45"].ret_pct.mean(), 1) if (o2.book.map(fam) == "orb45").any() else None))
print(pd.DataFrame(rows).to_string(index=False))
g = df[(df.day == "2026-11-12") & (df.time_in < "10:15") & ~df.book.isin(["conductor", "RAW"])]
print("\n12 Nov before 10:15 by book (n, won, mean %):")
print(g.groupby("book").agg(n=("ret_pct", "size"), won=("ret_pct", lambda x: int((x > 0).sum())), mean=("ret_pct", "mean"), first=("time_in", "min")).round(1).sort_values("mean").to_string())
