"""Exit geometry on four years, for three entry sets: the fade (20m, 0.5 sigma), the champion's pattern (1-minute
high/low version) and a blind buy. Chosen on sessions before 2025, judged on 2025-2026."""
import os, sys, time, itertools
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
import lab1, h4
EX = []
for sl, tp, trail, hold, floor in itertools.product((0.06, 0.10, 0.15), (None, 0.08, 0.15, 0.30), (25.0, 40.0, 70.0), (20, 45, 90), ("ramp", "none")):
    EX.append(dict(sl=sl, tp=tp, trail=trail, hold=hold, floor=floor))
SETS = {"fade": ("fade", dict(W=20, z=0.5)), "pattern": ("pb", dict(W=20, pb=0.5)), "blind": ("blind", dict(bars=(30, 105, 195, 285)))}


def work(idx):
    ALL = h4.load()
    rows = []
    sigs = {nm: [(D, h4.fam(D, f, **p)) for D in ALL if not D["dte0"]] for nm, (f, p) in SETS.items()}
    for i in idx:
        e = EX[i]
        for nm, lst in sigs.items():
            for half, sel in (("D", lambda d: d < h4.SPLIT), ("T", lambda d: d >= h4.SPLIT)):
                rets = []; days = {}
                for D, sig in lst:
                    if not sel(D["day"]):
                        continue
                    for t in lab1.run(D, sig, model=True, **e):
                        rets.append(t["ret"]); days[D["day"]] = days.get(D["day"], 0.0) + t["ret"]
                r = np.array(rets); dd = np.array(list(days.values()))
                rows.append(dict(i=i, set=nm, half=half, n=len(r), win=100 * (r > 0).mean() if len(r) else np.nan, mean=r.mean() if len(r) else np.nan,
                                 t=dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))) if len(dd) > 5 else np.nan, **{k: (v if v is not None else 0) for k, v in e.items()}))
    return rows


if __name__ == "__main__":
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(work, [list(range(len(EX)))[k::8] for k in range(8)]):
            rows += r
    R = pd.DataFrame(rows)
    R.to_parquet(os.path.join(lab1.W, "exits.parquet"))
    print(len(EX), "exit sets x 3 entry sets in", round(time.time() - t0), "s")
    pd.set_option("display.width", 250)
    for nm in SETS:
        g = R[R.set == nm]
        P = g.pivot_table(index=["sl", "tp", "trail", "hold", "floor"], columns="half", values=["n", "win", "mean", "t"]).round(2)
        P.columns = [f"{b}_{a}" for a, b in P.columns]
        P = P.reset_index()
        base = P[(P.sl == 0.15) & (P.tp == 0) & (P.trail == 40) & (P.hold == 90) & (P.floor == "ramp")]
        print(f"\n=== {nm} === champion exits today:", base[["D_n", "D_win", "D_mean", "D_t", "T_n", "T_win", "T_mean", "T_t"]].to_dict("records"))
        print("best 8 on the FOUND-ON sessions, and what they did on the JUDGED-ON sessions:")
        print(P.sort_values("D_t", ascending=False).head(8)[["sl", "tp", "trail", "hold", "floor", "D_n", "D_win", "D_mean", "D_t", "T_n", "T_win", "T_mean", "T_t"]].to_string(index=False))
        print(f"correlation across the {len(P)} exit sets between found-on and judged-on mean: {np.corrcoef(P.D_mean, P.T_mean)[0, 1]:.2f}; exit sets positive in both: {int(((P.D_mean > 0) & (P.T_mean > 0)).sum())}")
        for col in ("sl", "tp", "trail", "hold", "floor"):
            m = P.groupby(col)[["D_mean", "T_mean", "D_win", "T_win"]].mean().round(2)
            print(f"  by {col}: " + "  ".join(f"{k}: {r.D_mean:+.2f}/{r.T_mean:+.2f} ({r.D_win:.0f}/{r.T_win:.0f}% win)" for k, r in m.iterrows()))
