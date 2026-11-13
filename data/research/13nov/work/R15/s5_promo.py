import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import json, itertools, time
import numpy as np, pandas as pd
from simlib import *
t0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R15"
df = load(); df = df[(df.fam != "meta")]
books = sorted(df.book.unique()); BID = {b: i for i, b in enumerate(books)}; BOOKS = np.array(books, dtype=object)
g = {d: DayArr(x, BID) for d, x in df.groupby("day")}
def rank_of(lst):
    r = np.full(len(books), 10 ** 6, dtype=np.int64)
    for j, b in enumerate(lst): r[BID[b]] = j
    return r
def mask_of(D, lst): return np.isin(D.bid, [BID[b] for b in lst])
PO = rank_of(POOL)
def fam_count(D, Wsec, side_rel=+1, exclude_fam=None):
    """distinct families (other than exclude_fam) with a trigger on the same side (side_rel=+1) or the opposite side
    (side_rel=-1) in [t - Wsec, t]"""
    cnt = np.zeros(len(D.trig), np.int32)
    for f in np.unique(D.fam):
        if f == exclude_fam or f == "control":
            continue
        for sd in (0, 1):
            m = (D.fam == f) & (D.side == sd)
            tf = np.sort(D.trig[m])
            if len(tf) == 0: continue
            j = np.searchsorted(tf, D.trig, side="right") - 1
            want = sd if side_rel > 0 else 1 - sd
            cnt += (j >= 0) & (tf[np.clip(j, 0, None)] >= D.trig - Wsec) & (D.side == want)
    return cnt
strat = {}
strat["POOL"] = {d: sim_fast(g[d], mask_of(g[d], POOL), PO, BOOKS) for d in DAYS}
variants = 0
for Wsec, K in itertools.product([60, 180, 300, 600], [1, 2, 3]):
    variants += 2
    agree = {d: fam_count(g[d], Wsec, +1, "council") for d in DAYS}
    against = {d: fam_count(g[d], Wsec, -1, "council") for d in DAYS}
    strat[f"CONF_W{Wsec}_K{K}"] = {d: sim_fast(g[d], mask_of(g[d], POOL) & (agree[d] >= K), PO, BOOKS) for d in DAYS}
    strat[f"VETO_W{Wsec}_K{K}"] = {d: sim_fast(g[d], mask_of(g[d], POOL) & (against[d] < K), PO, BOOKS) for d in DAYS}
    # net: agree minus against
    variants += 1
    strat[f"NET_W{Wsec}_K{K}"] = {d: sim_fast(g[d], mask_of(g[d], POOL) & (agree[d] - against[d] >= K - 1), PO, BOOKS) for d in DAYS}
print("variants", variants, time.time() - t0, flush=True)
json.dump({k: {d: {"ret": r["ret"], "n": r["n"], "wins": r["wins"], "trades": r["trades"]} for d, r in v.items()} for k, v in strat.items()},
          open(W + r"\conf_days.json", "w"), default=str)

def tests(cand, base, days):
    c = [cand[d] for d in days]; b = [base[d] for d in days]
    ct = [t for r in c for t in r["trades"]]; bt = [t for r in b for t in r["trades"]]
    sr = lambda tt: 100 * sum(1 for t in tt if t[5] > 0) / max(1, len(tt))
    cr = np.array([r["ret"] for r in c]); br = np.array([r["ret"] for r in b])
    # w/o best trade: recompute the day of the best trade with it removed is costly; approximate by removing its compounding share:
    # day ret without trade k = prod(1+r_j/100 for j != k) - 1 (lots re-sized, same trades)
    def wo_best_trade(rs):
        allt = [(i, j, t[6]) for i, r in enumerate(rs) for j, t in enumerate(r["trades"])]
        if not allt: return 0.0
        i0, j0, _ = max(allt, key=lambda x: x[2])
        tot = 0.0
        for i, r in enumerate(rs):
            p = 1.0
            for j, t in enumerate(r["trades"]):
                if (i, j) != (i0, j0): p *= 1 + t[6] / 100
            tot += 100 * (p - 1)
        return tot
    # keeps big wins: base top 10% trades by return
    k = max(1, int(round(0.1 * len(bt))))
    top = sorted([(d, t) for d, r in zip(days, b) for t in r["trades"]], key=lambda x: -x[1][6])[:k]
    kept = 0
    for d, t in top:
        for u in cand[d]["trades"]:
            if (u[1] <= t[1] < u[2] and u[7] == t[7]) or abs(u[1] - t[1]) <= 60:
                kept += 1; break
    # sign flip on daily differences (exact)
    dd = cr - br
    dsr = np.array([(100 * x["wins"] / x["n"] if x["n"] else 0) - (100 * y["wins"] / y["n"] if y["n"] else 0) for x, y in zip(c, b)])
    flips = np.array(list(itertools.product([-1, 1], repeat=len(days))))
    p_ret = float(np.mean((flips * dd).sum(1) >= dd.sum()))
    p_sr = float(np.mean((flips * dsr).sum(1) >= dsr.sum()))
    return {"n": len(ct), "sr": sr(ct), "base_sr": sr(bt), "sum": cr.sum(), "base_sum": br.sum(),
            "wo_best_day": cr.sum() - cr.max(), "wo_best_trade": wo_best_trade(c), "base_wo_best_day": br.sum() - br.max(),
            "lose_days": int((cr < 0).sum()), "base_lose": int((br < 0).sum()), "worst": cr.min(), "base_worst": br.min(),
            "kept_top": f"{kept}/{k}", "p_ret": p_ret, "p_sr": p_sr}

W1 = DAYS[3:12]   # 23 Oct - 4 Nov
rows = []
meta = {}
for p in "ABC":
    meta.update(json.load(open(W + f"\meta_days_{p}.json")))
cands = {k: v for k, v in strat.items() if k != "POOL"}
for k in ["VOTE_K3_W300_pool_conf", "VOTETOP_M20_K3_W300", "VOTETOP_M20_K3_W180", "POOLFILL_N5_worst_K1", "BEST_N2_posdays_K3",
          "FAMROT_N2_sum", "BEST_N3_logsum_K10", "BEST_NNone_sum_K1", "POOLFILL_N3_sum_K1"]:
    cands[k] = meta[k]
for name, rec in cands.items():
    for wn, days in (("W1_23Oct_4Nov", W1), ("W2_5_12Nov", LATE)):
        if not all(d in rec for d in days): continue
        r = tests(rec, strat["POOL"], days); r.update({"name": name, "win": wn}); rows.append(r)
T = pd.DataFrame(rows)
T.to_csv(W + r"\promo_tests.csv", index=False)
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 400)
print(T.round(1).to_string(index=False))
# per-day table for selected
sel = ["POOL", "CONF_W300_K2", "VETO_W300_K2", "VOTE_K3_W300_pool_conf", "VOTETOP_M20_K3_W300", "POOLFILL_N5_worst_K1", "BEST_N2_posdays_K3", "FAMROT_N2_sum", "BEST_NNone_sum_K1"]
allr = dict(strat); allr.update(meta)
PD = pd.DataFrame({s: {d: f'{allr[s][d]["ret"]:+.1f} ({allr[s][d]["wins"]}/{allr[s][d]["n"]})' for d in DAYS if d in allr[s]} for s in sel})
print(PD.to_string())
print("time", time.time() - t0)
