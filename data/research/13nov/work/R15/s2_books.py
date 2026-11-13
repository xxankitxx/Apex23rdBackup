import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import json, time
import numpy as np, pandas as pd
from simlib import *
t0 = time.time()
df = load()
print("rows", len(df), "entry>1000:", sorted(df[df.entry > 1000].book.unique()))
W = r"D:\ApexOptions\data\research\13nov\work\R15"
g = {d: x for d, x in df.groupby("day")}

# 1. validation of the account rule against conductor_sim.json (pool as of all)
order = {b: i for i, b in enumerate(POOL)}
ref = {}
for p in [r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json", r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json"]:
    d = json.load(open(p, encoding="utf-8"))
    for day, r in d["days"].items():
        if "simr" in p or day not in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"):
            ref[day] = (r["n"], r["wins"], r["ret_day_pct"])
val = []
base = {}
for day in DAYS:
    x = g[day]; rec = sim_day(x[x.book.isin(POOL)], order); base[day] = rec
    val.append((day, rec["n"], rec["wins"], round(rec["ret"], 2), ref.get(day)))
print("validation (mine vs conductor_sim):")
for v in val: print(v)

# 2. per-book per-day compounded return (each book alone, all-in, fresh 1 lakh a day)
rows = []
print("loop start", time.time()-t0, flush=True)
print("val done", time.time()-t0, flush=True)
GG = {k: v for k, v in df.groupby(["book", "day"])}
EMPTY = df.iloc[:0]
for b in sorted(df.book.unique()):
    for day in DAYS:
        x = GG.get((b, day), EMPTY)
        rec = sim_day(x, {b: 0})
        rows.append({"book": b, "fam": family(b), "day": day, "ret": rec["ret"], "n": rec["n"], "wins": rec["wins"]})
print("loop done", time.time()-t0, flush=True)
bd = pd.DataFrame(rows)
bd.to_parquet(W + r"\book_day.parquet")
piv = bd.pivot(index="book", columns="day", values="ret")[DAYS]
res = []
for b in piv.index:
    e = bd[(bd.book == b) & bd.day.isin(EARLY)]; l = bd[(bd.book == b) & bd.day.isin(LATE)]
    re_, rl = e.ret.values, l.ret.values
    res.append({"book": b, "fam": family(b),
                "E_n": int(e.n.sum()), "E_sr": 100 * e.wins.sum() / max(1, e.n.sum()), "E_sum": re_.sum(), "E_med": np.median(re_),
                "E_lose": int((re_ < 0).sum()), "E_worst": re_.min(),
                "L_n": int(l.n.sum()), "L_sr": 100 * l.wins.sum() / max(1, l.n.sum()), "L_sum": rl.sum(), "L_med": np.median(rl),
                "L_lose": int((rl < 0).sum()), "L_worst": rl.min(), "L_wo_best_day": rl.sum() - rl.max(),
                "A_sum": re_.sum() + rl.sum(), "A_lose": int((re_ < 0).sum() + (rl < 0).sum()),
                "A_pos_days": int((np.r_[re_, rl] > 0).sum())})
R = pd.DataFrame(res).round(1)
R.to_csv(W + r"\book_stats.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(R.sort_values("L_sum", ascending=False).to_string(index=False))

# rank stability: Spearman between early sum and late sum, early SR and late SR
from scipy.stats import spearmanr
X = R[R.fam != "meta"]
print("spearman E_sum vs L_sum", spearmanr(X.E_sum, X.L_sum))
print("spearman E_sr vs L_sr", spearmanr(X.E_sr, X.L_sr))
print("spearman E_med vs L_med", spearmanr(X.E_med, X.L_med))
print("spearman E_lose vs L_lose", spearmanr(X.E_lose, X.L_lose))

# 3. correlation between books' daily returns (17 days)
P = piv.drop(index=[b for b in piv.index if family(b) == "meta"])
C = np.corrcoef(P.values)
iu = np.triu_indices_from(C, 1)
print("mean pairwise corr", np.nanmean(C[iu]), "median", np.nanmedian(C[iu]))
fams = [family(b) for b in P.index]
fm = sorted(set(fams))
F = pd.DataFrame(index=fm, columns=fm, dtype=float)
for a in fm:
    for c in fm:
        ia = [i for i, f in enumerate(fams) if f == a]; ic = [i for i, f in enumerate(fams) if f == c]
        vals = [C[i, j] for i in ia for j in ic if i != j]
        F.loc[a, c] = np.nanmean(vals) if vals else np.nan
print(F.round(2).to_string())
# correlation of each book with the pool account
acc = np.array([base[d]["ret"] for d in DAYS])
cw = {b: np.corrcoef(P.loc[b].values, acc)[0, 1] for b in P.index}
R["corr_pool"] = R.book.map(cw).round(2)
R.to_csv(W + r"\book_stats.csv", index=False)
# family daily sums (the family's own one-account pool)
print("time", time.time() - t0)
