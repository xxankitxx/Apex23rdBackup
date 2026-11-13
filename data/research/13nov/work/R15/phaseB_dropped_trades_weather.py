"""PHASE B (run after 15:30 only). R15: which pool trades does the curated-family confirmation (CONF_cur_W300_K1:
a pool trigger is taken only if a t28 / lvl / spot / edge book fired the same side in the previous 300 s) drop, and
what did the weather photograph say at those triggers? Joins the dropped and kept Conductor trades to their wx_*
columns (loads ~60 named columns only) and prints the 15 columns with the largest kept-vs-dropped standardized gap,
discovery days only (19 Oct - 4 Nov), then checks the same gaps on 5 - 12 Nov."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import numpy as np, pandas as pd, pyarrow.parquet as pq
from simlib import *
SRC = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
names = pq.ParquetFile(SRC).schema.names
wx = [n for n in names if n.startswith("wx_") and any(k in n for k in ("mom", "er_", "vwap", "orb", "breadth", "vix", "dist", "straddle", "gap"))][:60]
df = load()
x = pd.read_parquet(SRC, columns=["day", "book", "trigger_t", "t_in"] + wx)
x["trig"] = x.trigger_t.fillna(x.t_in)
books = sorted(df[df.fam != "meta"].book.unique()); BID = {b: i for i, b in enumerate(books)}
rows = []
for d, xd in df[df.fam != "meta"].groupby("day"):
    D = DayArr(xd, BID)
    cnt = np.zeros(len(D.trig), np.int32)
    ok = np.isin(D.fam, ["t28", "lvl", "spot", "edge"])
    for sd in (0, 1):
        tf = np.sort(D.trig[ok & (D.side == sd)])
        if len(tf):
            j = np.searchsorted(tf, D.trig, side="right") - 1
            cnt += (j >= 0) & (tf[np.clip(j, 0, None)] >= D.trig - 300) & (D.side == sd)
    rk = np.full(len(books), 10 ** 6, dtype=np.int64)
    for k, b in enumerate(POOL): rk[BID[b]] = k
    base = sim_fast(D, np.isin(D.bid, [BID[b] for b in POOL]), rk, np.array(books, dtype=object))
    conf_t = {float(D.trig[i]) for i in range(len(D.trig)) if cnt[i] > 0}
    for t in base["trades"]:
        rows.append({"day": d, "book": t[0], "trig": t[1], "r": t[6], "confirmed": t[1] in conf_t})
T = pd.DataFrame(rows).merge(x, on=["day", "book", "trig"], how="left")
for wn, dd in (("EARLY", EARLY), ("LATE", LATE)):
    y = T[T.day.isin(dd)]
    print(wn, y.groupby("confirmed").r.agg(["count", "mean", lambda s: (s > 0).mean()]))
    gaps = {c: (y[y.confirmed][c].mean() - y[~y.confirmed][c].mean()) / (y[c].std() + 1e-9) for c in wx if y[c].notna().sum() > 10}
    print(pd.Series(gaps).sort_values(key=abs, ascending=False).head(15).round(2))
