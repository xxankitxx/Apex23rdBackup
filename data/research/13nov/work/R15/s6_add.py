import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import time
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from simlib import *
t0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R15"
bd = pd.read_parquet(W + r"\book_day.parquet"); bd = bd[bd.fam != "meta"]
P = bd.pivot(index="book", columns="day", values="ret")[DAYS]
# 1. persistence: does yesterday's book ranking predict today's?
rho = [spearmanr(P[DAYS[i - 1]], P[DAYS[i]])[0] for i in range(1, len(DAYS))]
rho3 = [spearmanr(P[DAYS[i - 3:i]].sum(1), P[DAYS[i]])[0] for i in range(3, len(DAYS))]
print("day-to-day rank corr across books:", np.round(rho, 2), "mean", np.mean(rho))
print("last-3-days vs today:", np.round(rho3, 2), "mean", np.mean(rho3))
F = P.groupby([family(b) for b in P.index]).median()
rf = [spearmanr(F[DAYS[i - 1]], F[DAYS[i]])[0] for i in range(1, len(DAYS))]
print("family-level day-to-day corr:", np.round(rf, 2), "mean", np.nanmean(rf))
# oracle: best book each day ex post (upper bound, not tradeable)
print("oracle best book per day sum:", P.max().sum(), "pool sum 17d: 1092.5", "| oracle late:", P[LATE].max().sum())
# 2. static additions chosen on EARLY, tested on LATE
df = load(); df = df[df.fam != "meta"]
books = sorted(df.book.unique()); BID = {b: i for i, b in enumerate(books)}; BOOKS = np.array(books, dtype=object)
g = {d: DayArr(x, BID) for d, x in df.groupby("day")}
def rank_of(lst):
    r = np.full(len(books), 10 ** 6, dtype=np.int64)
    for j, b in enumerate(lst): r[BID[b]] = j
    return r
def mask_of(D, lst): return np.isin(D.bid, [BID[b] for b in lst])
rows = []
cand = [b for b in books if family(b) not in ("council", "control")]
for b in cand:
    for mode in ("low", "high"):
        lst = POOL + [b] if mode == "low" else [b] + POOL
        rk = rank_of(lst)
        rec = {d: sim_fast(g[d], mask_of(g[d], lst), rk) for d in DAYS}
        e = [rec[d] for d in EARLY]; l = [rec[d] for d in LATE]
        rows.append({"book": b, "mode": mode,
                     "E_sum": sum(r["ret"] for r in e), "E_sr": 100 * sum(r["wins"] for r in e) / max(1, sum(r["n"] for r in e)),
                     "E_lose": sum(r["ret"] < 0 for r in e),
                     "L_sum": sum(r["ret"] for r in l), "L_sr": 100 * sum(r["wins"] for r in l) / max(1, sum(r["n"] for r in l)),
                     "L_lose": sum(r["ret"] < 0 for r in l), "L_worst": min(r["ret"] for r in l), "L_n": sum(r["n"] for r in l),
                     "L_days": " ".join(f"{r['ret']:+.0f}" for r in l)})
A = pd.DataFrame(rows)
A.to_csv(W + r"\pool_additions.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
print("variants", len(A))
for mode in ("low", "high"):
    x = A[A["mode"] == mode].sort_values("E_sum", ascending=False)
    print("==== mode", mode, "| pool alone EARLY sum 949.9 (in-sample) LATE 142.5 SR 51.4 lose 2")
    print("additions improving LATE sum:", int((x.L_sum > 142.5).sum()), "of", len(x), "| improving LATE sr:", int((x.L_sr > 51.43).sum()))
    print(x.head(10).round(1).to_string(index=False))
    print("spearman E_sum vs L_sum over additions", spearmanr(x.E_sum, x.L_sum)[0])
print("time", time.time() - t0)
