import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import itertools, time, json
import numpy as np, pandas as pd
from simlib import *
t0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R15"
df = load(); df = df[df.fam != "meta"]
books = sorted(df.book.unique()); BID = {b: i for i, b in enumerate(books)}; BOOKS = np.array(books, dtype=object)
g = {d: DayArr(x, BID) for d, x in df.groupby("day")}
r = np.full(len(books), 10 ** 6, dtype=np.int64)
for j, b in enumerate(POOL): r[BID[b]] = j
PO = r
def pm(D): return np.isin(D.bid, [BID[b] for b in POOL])
CUR = {"t28", "lvl", "spot", "edge"}
def count(D, Wsec, rel, fams, unit):
    cnt = np.zeros(len(D.trig), np.int32)
    keys = D.fam if unit == "fam" else D.bid
    ok = np.isin(D.fam, list(fams))
    for f in np.unique(keys[ok]):
        for sd in (0, 1):
            tf = np.sort(D.trig[ok & (keys == f) & (D.side == sd)])
            if len(tf) == 0: continue
            j = np.searchsorted(tf, D.trig, side="right") - 1
            want = sd if rel > 0 else 1 - sd
            cnt += (j >= 0) & (tf[np.clip(j, 0, None)] >= D.trig - Wsec) & (D.side == want)
    return cnt
base = {d: sim_fast(g[d], pm(g[d]), PO) for d in DAYS}
def summ(rec, dd):
    rs = [rec[d]["ret"] for d in dd]; n = sum(rec[d]["n"] for d in dd); w = sum(rec[d]["wins"] for d in dd)
    return n, 100 * w / max(1, n), sum(rs), sum(x < 0 for x in rs), min(rs), sum(rs) - max(rs)
rows = []
W1 = DAYS[3:12]
for Wsec, K, rel, unit in itertools.product([120, 300, 600], [1, 2], [+1, -1], ["fam", "book"]):
    rec = {}
    for d in DAYS:
        c = count(g[d], Wsec, rel, CUR, unit)
        m = pm(g[d]) & ((c >= K) if rel > 0 else (c < K))
        rec[d] = sim_fast(g[d], m, PO)
    name = f"{'CONF' if rel > 0 else 'VETO'}_cur_{unit}_W{Wsec}_K{K}"
    for wn, dd in (("W1", W1), ("W2", LATE)):
        n, sr, s, lo, wo, wb = summ(rec, dd)
        bn, bsr, bs, blo, bwo, bwb = summ(base, dd)
        rows.append({"name": name, "win": wn, "n": n, "sr": sr, "sum": s, "lose": lo, "worst": wo, "wo_best_day": wb,
                     "base_sr": bsr, "base_sum": bs, "base_lose": blo, "days": " ".join(f"{rec[d]['ret']:+.0f}" for d in dd)})
T = pd.DataFrame(rows)
T.to_csv(W + r"\curated_vote.csv", index=False)
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
print(T.round(1).to_string(index=False))
print("variants", len(T) // 2, "time", time.time() - t0)
