"""PHASE B (run after 15:30 only; same rules: py -3.13, one script at a time, < 3 min, < 1.5 GB).
R15: second-level walk-forward. Each day, pick the meta-strategy itself (from the 257 variants of s3/s5/s8) by its
trailing N-day record, then trade that variant's day. Tests whether 'choosing the selector' adds anything over the
plain pool. Reads meta_days_A/B/C.json and conf_days.json (written by s3_meta.py and s5_promo.py)."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R15")
import json, itertools
import numpy as np, pandas as pd
from simlib import DAYS, LATE
W = r"D:\ApexOptions\data\research\13nov\work\R15"
M = {}
for p in "ABC":
    M.update(json.load(open(W + f"\meta_days_{p}.json")))
M.update(json.load(open(W + r"\conf_days.json")))
names = [k for k, v in M.items() if all(d in v for d in DAYS[3:])]
R = pd.DataFrame({k: [M[k][d]["ret"] for d in DAYS[3:]] for k in names}, index=DAYS[3:])
rows = []
for N, metric in itertools.product([2, 3, 5, 8], ["sum", "median", "worst"]):
    out = {}
    for i in range(N, len(R)):
        h = R.iloc[i - N:i]
        s = {"sum": h.sum(), "median": h.median(), "worst": h.min() + 0.001 * h.sum()}[metric]
        pick = s.idxmax(); out[R.index[i]] = (pick, R.iloc[i][pick])
    late = [out[d][1] for d in LATE if d in out]
    rows.append({"N": N, "metric": metric, "late_sum": sum(late), "late_lose": sum(x < 0 for x in late),
                 "late_days": " ".join(f"{x:+.0f}" for x in late), "picks": [out[d][0] for d in LATE if d in out]})
print(pd.DataFrame(rows).to_string())
print("POOL late", R.loc[LATE, "POOL"].sum())
