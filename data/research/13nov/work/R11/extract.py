import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R11: compact cache of the collect files (every 30 s origin, chosen features, 5 and 15-min forward moves)
import glob, os, time
import numpy as np, joblib
sys.path.insert(0, r"D:\ApexOptions")
from apex.forecast_lab.brain import FEATS
USE = ["r300", "r600", "r1800", "vwap", "rng", "dhi", "dlo", "kf", "er300", "vr", "hw120", "bank120", "up60", "imb", "ofi120", "tod", "left"]
ix = [3 + FEATS.index(k) for k in USE]
OUT = r"D:\ApexOptions\data\research\13nov\work\R11\cache"
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
for day in sys.argv[1:]:
    if os.path.exists(os.path.join(OUT, day + ".npz")):
        continue
    if time.time() - T0 > 140:
        print("time up before", day); break
    d = joblib.load(rf"D:\ApexOptions\data\forecast_lab\collect\{day}.joblib")
    X, S = d["X"], d["S"]
    t, F = X[:, 0], X[:, 1]
    st, sF = S[:, 0], S[:, 1]
    ys = []
    for h in (300, 900):
        j = np.minimum(np.searchsorted(st, t + h), len(st) - 1)
        fut = sF[j] - F
        fut[np.abs(st[j] - (t + h)) > 5] = np.nan
        ys.append(fut)
    Z = X[:, ix].astype(float)
    sod = (t.astype(np.int64) + 19800) % 86400
    keep = (np.arange(len(t)) % 6 == 0) & (sod >= 9 * 3600 + 30 * 60) & (sod <= 15 * 3600 + 15 * 60) & np.all(np.isfinite(Z), 1)
    np.savez(os.path.join(OUT, day + ".npz"), Z=Z[keep], y5=ys[0][keep], y15=ys[1][keep], t=t[keep], F=F[keep])
    print(day, int(keep.sum()), round(time.time() - T0, 1), flush=True)
