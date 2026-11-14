import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1"); os.environ.setdefault("MKL_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions")
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL

def one(day):
    t0 = time.time()
    D = FL.load_day(day, rebuild=True)
    import numpy as np
    return day, round(time.time() - t0, 1), bool(D["dte0"]), int(np.isfinite(D["fwd"]).sum()), int(np.isfinite(D["sis"][:, 0]).sum()), float(np.nanmedian(D["fmid"] - D["fwd"]))

if __name__ == "__main__":
    t0 = time.time()
    ds = FL.days()
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, ds):
            print(r, flush=True)
    print("days", len(ds), "total", round(time.time() - t0, 1), "s")
