import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import json, time, itertools
import numpy as np, pandas as pd
from simlib import *
t0 = time.time()
PART = sys.argv[1]
W = r"D:\ApexOptions\data\research\13nov\work\R15"
df = load()
df = df[(df.fam != "meta") & (df.entry < 1000)]
books = sorted(df.book.unique()); BID = {b: i for i, b in enumerate(books)}
BOOKS = np.array(books, dtype=object)
g = {d: DayArr(x, BID) for d, x in df.groupby("day")}
FAMB = np.array([family(b) for b in books], dtype=object)
def rank_of(lst):
    r = np.full(len(books), 10 ** 6, dtype=np.int64)
    for j, b in enumerate(lst):
        r[BID[b]] = j
    return r
def mask_of(D, lst):
    return np.isin(D.bid, [BID[b] for b in lst])
bd = pd.read_parquet(W + r"\book_day.parquet")
bd = bd[(bd.fam != "meta") & (bd.book.isin(books))]
RET = bd.pivot(index="day", columns="book", values="ret").reindex(index=DAYS, columns=books).fillna(0.0)
NN = bd.pivot(index="day", columns="book", values="n").reindex(index=DAYS, columns=books).fillna(0)
WW = bd.pivot(index="day", columns="book", values="wins").reindex(index=DAYS, columns=books).fillna(0)

pool_order = rank_of(POOL)
results = {}            # name -> {day: rec}
variants = 0


def run(name, fn, days=DAYS):
    global variants
    variants += 1
    recs = {}
    for i, d in enumerate(DAYS):
        if d not in days:
            continue
        out = fn(i, d)
        if out is None:
            continue
        recs[d] = out
    results[name] = recs


# baseline: the current pool
run("POOL", lambda i, d: sim_fast(g[d], mask_of(g[d], POOL), pool_order, BOOKS))


SC = {}
def score(i, N, metric, minn=3):
    k = (i, N, metric, minn)
    if k not in SC:
        SC[k] = _score(i, N, metric, minn)
    return SC[k]


def _score(i, N, metric, minn=3):
    lo = 0 if N is None else max(0, i - N)
    r = RET.iloc[lo:i]; n = NN.iloc[lo:i]; w = WW.iloc[lo:i]
    if metric == "sum":
        s = r.sum()
    elif metric == "logsum":
        s = np.log1p(r.clip(lower=-99) / 100).sum()
    elif metric == "median":
        s = r.median()
    elif metric == "posdays":
        s = (r > 0).sum() + 0.001 * r.sum()
    elif metric == "sr":
        s = w.sum() / n.sum().replace(0, np.nan)
        s = s.where(n.sum() >= minn, -1)
    elif metric == "worst":           # maximin: best worst-day
        s = r.min() + 0.001 * r.sum()
    s = s.where(n.sum() >= minn, -1e9)  # must have traded
    return s.sort_values(ascending=False)


# best-of-recent
print("pool", time.time()-t0, flush=True)
for N, metric, K in (itertools.product([2, 3, 5, None], ["sum", "logsum", "median", "posdays", "sr", "worst"], [1, 3, 5, 10]) if PART == "A" else []):
    def fn(i, d, N=N, metric=metric, K=K):
        if i < 3:
            return None
        s = score(i, N, metric)
        top = list(s.index[:K])
        return sim_fast(g[d], mask_of(g[d], top), rank_of(top), BOOKS) | {"pick": top}
    run(f"BEST_N{N}_{metric}_K{K}", fn)
print("best", time.time()-t0, flush=True)

# pool first, then the best recent non-council books fill the idle time
for N, metric, K in (itertools.product([3, 5, None], ["sum", "median", "posdays", "worst"], [1, 3]) if PART == "B" else []):
    def fn(i, d, N=N, metric=metric, K=K):
        if i < 3:
            return None
        s = score(i, N, metric)
        s = s[[b for b in s.index if family(b) != "council"]]
        top = POOL + list(s.index[:K])
        return sim_fast(g[d], mask_of(g[d], top), rank_of(top), BOOKS) | {"pick": top}
    run(f"POOLFILL_N{N}_{metric}_K{K}", fn)
print("fill", time.time()-t0, flush=True)

# family rotation: each family is a one-account pool of its own books, priority = trailing book score within family
fams = sorted(set(family(b) for b in books) - {"control"}) if PART == "B" else []
FAMREC = {}
for f in fams:
    fb = [b for b in books if family(b) == f]
    for i, d in enumerate(DAYS):
        s = score(i, None, "sum") if i >= 1 else pd.Series(0, index=books)
        FAMREC[(f, d)] = sim_fast(g[d], mask_of(g[d], fb), rank_of([b for b in s.index if b in fb]), BOOKS)
if fams:
  FR = pd.DataFrame({f: [FAMREC[(f, d)]["ret"] for d in DAYS] for f in fams}, index=DAYS)
  FR.to_csv(W + r"\family_account_day.csv")
for N, metric in (itertools.product([2, 3, 5, None], ["sum", "median", "posdays", "worst"]) if PART == "B" else []):
    def fn(i, d, N=N, metric=metric):
        if i < 3:
            return None
        lo = 0 if N is None else max(0, i - N)
        r = FR.iloc[lo:i]
        s = {"sum": r.sum(), "median": r.median(), "posdays": (r > 0).sum() + 0.001 * r.sum(), "worst": r.min() + 0.001 * r.sum()}[metric]
        f = s.sort_values(ascending=False).index[0]
        return FAMREC[(f, d)] | {"pick": [f]}
    run(f"FAMROT_N{N}_{metric}", fn)
print("fam", time.time()-t0, flush=True)


# ensemble vote: enter only when K distinct families fired the same side within Wsec; take the confirming trade
def fam_count(D, Wsec, sub=None):
    """For each row: number of distinct families with a same-side trigger in [t - Wsec, t] (rows in sub only)."""
    ok = np.ones(len(D.trig), bool) if sub is None else sub
    cnt = np.zeros(len(D.trig), np.int32)
    for f in np.unique(D.fam[ok]):
        for sd in (0, 1):
            m = ok & (D.fam == f) & (D.side == sd)
            tf = np.sort(D.trig[m])
            if len(tf) == 0:
                continue
            j = np.searchsorted(tf, D.trig, side="right") - 1
            has = (j >= 0) & (tf[np.clip(j, 0, None)] >= D.trig - Wsec) & (D.side == sd)
            cnt += has
    return np.where(ok, cnt, 0)


VM = {}
for d in (DAYS if PART == "C" else []):
    for Wsec in (60, 180, 300):
        c = fam_count(g[d], Wsec)
        for K in (2, 3, 4):
            VM[(d, K, Wsec)] = c >= K
print("votes", time.time() - t0, flush=True)
for K, Wsec, univ in (itertools.product([2, 3, 4], [60, 180, 300], ["all", "pool_conf"]) if PART == "C" else []):
    def fn(i, d, K=K, Wsec=Wsec, univ=univ):
        keep = VM[(d, K, Wsec)]
        if univ == "pool_conf":      # a pool trigger taken only when K-1 other families agree (the pool's family counts as one)
            keep = keep & mask_of(g[d], POOL)
        return sim_fast(g[d], keep, pool_order, BOOKS)
    run(f"VOTE_K{K}_W{Wsec}_{univ}", fn)
# vote among the recently best books only (top 20 by trailing sum), distinct families
for K, Wsec, M in (itertools.product([2, 3], [60, 180, 300], [10, 20, 40]) if PART == "C" else []):
    def fn(i, d, K=K, Wsec=Wsec, M=M):
        if i < 3:
            return None
        top = list(score(i, None, "sum").index[:M])
        keep = fam_count(g[d], Wsec, mask_of(g[d], top)) >= K
        return sim_fast(g[d], keep, rank_of(top), BOOKS)
    run(f"VOTETOP_M{M}_K{K}_W{Wsec}", fn)

print("variants", variants, "time", time.time() - t0)
# summaries
ROLL = DAYS[3:]
rows = []
for name, recs in results.items():
    for wname, wd in (("LATE", LATE), ("ROLL", ROLL)):
        dd = [d for d in wd if d in recs]
        if len(dd) < len(wd):
            continue
        s = summarize(recs, dd)
        s.update({"name": name, "win": wname, "days": len(dd)})
        rows.append(s)
S = pd.DataFrame(rows)
S.to_csv(W + r"\meta_summary_" + PART + ".csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
for wname in ("LATE", "ROLL"):
    x = S[S.win == wname].sort_values("sum_day_pct", ascending=False)
    print("====", wname)
    print(x.head(40).round(1).to_string(index=False))
    print(x[x.name == "POOL"].round(1).to_string(index=False))
    print("share of variants beating POOL on sum:", (x.sum_day_pct > float(x[x.name == "POOL"].sum_day_pct.iloc[0])).mean())
    print("share beating POOL on sr:", (x.sr > float(x[x.name == "POOL"].sr.iloc[0])).mean())
# day tables for later use
DT = {name: {d: {"ret": r["ret"], "n": r["n"], "wins": r["wins"], "pick": r.get("pick"),
                 "trades": r["trades"]}
             for d, r in recs.items()} for name, recs in results.items()}
json.dump(DT, open(W + r"\meta_days_" + PART + ".json", "w"), default=str)
print("time", time.time() - t0)
