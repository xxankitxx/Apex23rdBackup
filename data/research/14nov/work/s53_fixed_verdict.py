"""Champion, its side-swapped twin (r2_timing_vs_side F2) and the finalists on the FIXED harness (work/arena_fixed.py, from agents/r2_harness_fix/
arena_fixed.py: causal IV of the last completed minute, 09:20 basis, model fallback), every split incl. the holdout.
    py -3.13 s53_fixed_verdict.py gen_path[:name] ...
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np
import arena_fixed as AF
from concurrent.futures import ProcessPoolExecutor
OUT = "D:/ApexOptions/data/research/14nov/agents/_finalists"
SPL = ("found", "judged", "window", "holdout")


def one(a):
    path, name, sp = a
    g = AF.load_gen(path)
    T = AF.trades(g, AF.sessions(sp))
    if len(T):
        T["split"] = sp; T["gen"] = name
    return T


if __name__ == "__main__":
    jobs = []
    for a in sys.argv[1:]:
        p, _, n = a.partition("=")
        jobs += [(p, n or os.path.basename(p)[4:-3], sp) for sp in SPL]
    with ProcessPoolExecutor(max_workers=4) as ex:
        T = pd.concat([t for t in ex.map(one, jobs) if len(t)], ignore_index=True)
    T["dte0"] = T.day.map(AF.is_expiry)
    T.to_parquet(f"{OUT}/fixed_trades_{'_'.join(sorted(set(T.gen)))[:80]}.parquet")
    comp = lambda r: 100 * (np.prod(1 + np.asarray(r) / 100) - 1)
    rows = []
    for (g, sp, d0), x in T.groupby(["gen", "split", "dte0"]):
        dd = x.groupby("day").ret.apply(comp)
        rows.append(dict(gen=g, split=sp, days="expiry" if d0 else "normal", trades=len(x), sessions=x.day.nunique(),
                         winners=round(100 * (x.ret > 0).mean(), 1), per_trade=round(x.ret.mean(), 2), day_sum=round(dd.sum(), 1),
                         t=round(dd.mean() / dd.std() * np.sqrt(len(dd)), 2) if len(dd) > 2 else np.nan))
    R = pd.DataFrame(rows)
    R.to_csv(f"{OUT}/fixed_verdict.csv", mode="a", index=False, header=not os.path.exists(f"{OUT}/fixed_verdict.csv"))
    pd.set_option("display.width", 200); print(R.to_string())
