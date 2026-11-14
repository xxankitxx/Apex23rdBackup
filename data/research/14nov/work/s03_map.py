"""Opportunity map: at every 10th second, both sides, what the champion's own exits would have made from a buy there."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
OUT = r"D:\ApexOptions\data\research\14nov\work"
STEP = 10
SKIP = ("hi300", "lo300", "hi600", "lo600", "hi1200", "lo1200", "hi3600", "lo3600", "dhi", "dlo")


def one(day):
    t0 = time.time()
    D = FL.load_day(day)
    X = FL.features(D)
    P = D["P"]
    rows = []
    names = [k for k in X if k not in SKIP]
    for i in range(P["t0"] + 60, P["t1"], STEP):
        if X["gap"][i] or not np.isfinite(D["fs"][i]):
            continue
        base = {k: X[k][i] for k in names}
        for side in ("CE", "PE"):
            j = FL.pick(D, i, side)
            if j is None:
                continue
            t = FL.exit_ladder(D, i, side, j)
            if t is None:
                continue
            c = 0 if side == "CE" else 1
            q = D["opt"][i, j, c]
            rows.append(dict(base, day=day, i=i, side=side, dte0=D["dte0"], ret=t["ret"], peak=t["peak"], hold_s=t["hold_s"],
                             why=t["why"], e=t["e"], spr=float((q[1] - q[0]) / q[1]) * 100.0, K=t["K"]))
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(OUT, f"map_{day}.parquet"))
    return day, len(df), round(time.time() - t0, 1)


if __name__ == "__main__":
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, FL.days()):
            print(r, flush=True)
    print("total", round(time.time() - t0, 1), "s")
