import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import numpy as np, pandas as pd
from simlib import *
W = r"D:\ApexOptions\data\research\13nov\work\R15"
R = pd.read_csv(W + r"\book_stats.csv", index_col=0)
df = load(); df = df[df.fam != "meta"]
books = sorted(df.book.unique()); BID = {b: i for i, b in enumerate(books)}
g = {d: DayArr(x, BID) for d, x in df.groupby("day")}
def run(lst):
    rk = np.full(len(books), 10 ** 6, dtype=np.int64)
    for j, b in enumerate(lst): rk[BID[b]] = j
    rec = {d: sim_fast(g[d], np.isin(g[d].bid, [BID[b] for b in lst]), rk) for d in DAYS}
    out = []
    for dd in (EARLY, LATE):
        rs = [rec[d]["ret"] for d in dd]; n = sum(rec[d]["n"] for d in dd); w = sum(rec[d]["wins"] for d in dd)
        out.append(f"n {n} sr {100*w/max(1,n):.1f} sum {sum(rs):+.1f} lose {sum(x<0 for x in rs)} worst {min(rs):+.1f} woBD {sum(rs)-max(rs):+.1f}")
    return out, " ".join(f"{rec[d]['ret']:+.0f}" for d in LATE)
X = R[~R.fam.isin(["council", "control", "meta"])]
for crit, sel in [("top5 E_sum", X.sort_values("E_sum", ascending=False).index[:5]),
                  ("top5 E_sum, E_lose<=3", X[X.E_lose <= 3].sort_values("E_sum", ascending=False).index[:5]),
                  ("top5 E_sr, E_n>=60", X[X.E_n >= 60].sort_values("E_sr", ascending=False).index[:5]),
                  ("top5 E_med", X.sort_values("E_med", ascending=False).index[:5]),
                  ("top1 E_sum", X.sort_values("E_sum", ascending=False).index[:1])]:
    sel = list(sel); o, days = run(sel)
    print(crit, sel); print("  EARLY", o[0]); print("  LATE ", o[1], "|", days)
for name, lst in [("POOL", POOL), ("c20_9y alone", ["c20_9y"]), ("c20_9v alone", ["c20_9v"]), ("c20_8x alone", ["c20_8x"]),
                  ("POOL+c20_8x", POOL + ["c20_8x"])]:
    o, days = run(lst); print(name); print("  EARLY", o[0]); print("  LATE ", o[1], "|", days)
