import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R11: does a descriptive "stand" (trend side) agreeing with the trade side change pool-book trades? walk-forward split.
import pandas as pd, numpy as np
cols = ["day", "book", "rr", "ret_pct", "wx_vwap_side_with", "wx_breadth900_dir", "wx_ma20_slope", "wx_vwap_z"]
df = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=cols)
df = df[df.book.isin(["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"])].copy()
df["sg"] = np.where(df.rr == "CE", 1, -1)
print(df[["wx_vwap_side_with", "wx_breadth900_dir", "wx_ma20_slope", "wx_vwap_z"]].describe().T.round(3))
df["day"] = df["day"].astype(str)
df["late"] = df.day >= "2026-11-05"
ms = df.wx_ma20_slope * df.sg
vz = df.wx_vwap_z * df.sg
bd = df.wx_breadth900_dir * df.sg
df["stand_with"] = ((vz > 0) & (ms > 0)).astype(int) - ((vz < 0) & (ms < 0)).astype(int)
df["bd_with"] = np.sign(bd)
for key in ["stand_with", "bd_with"]:
    g = df.groupby(["late", key]).agg(n=("ret_pct", "size"), won=("ret_pct", lambda x: (x > 0).mean() * 100), mean=("ret_pct", "mean"), med=("ret_pct", "median"))
    print(key); print(g.round(1))
    for d, x in df[df.late].groupby("day"):
        print("  ", d, " ".join(f"{k}:{len(v)} {((v.ret_pct>0).mean()*100):.0f}% {v.ret_pct.mean():+.1f}" for k, v in x.groupby(key)))
