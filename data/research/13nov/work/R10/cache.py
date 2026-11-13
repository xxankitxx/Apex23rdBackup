import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""Convert collect/<day>.joblib to a compact npz: t, F, vref, X (float32), dF for lags 0/30 and horizons. Args: day indices."""
import os, glob, time
T0 = time.time()
import numpy as np, joblib
COL = r"D:\ApexOptions\data\forecast_lab\collect"
OUT = r"D:\ApexOptions\data\research\13nov\work\R10\cache"
os.makedirs(OUT, exist_ok=True)
H = (60, 120, 180, 300, 600, 900)
LAGS = (0, 30)
files = sorted(glob.glob(os.path.join(COL, '*.joblib')))
for a in sys.argv[1:]:
    f = files[int(a)]
    day = os.path.basename(f)[:10]
    if os.path.exists(os.path.join(OUT, day + '.npz')):
        continue
    d = joblib.load(f)
    X, S = d['X'], d['S']
    t, F = X[:, 0], X[:, 1]
    st, sf = S[:, 0].astype(np.int64), S[:, 1]
    base = int(st[0])
    arr = np.full(int(st[-1]) - base + 2000, np.nan)
    arr[st - base] = sf

    def at(tt):
        k = np.round(tt).astype(np.int64) - base
        ok = (k >= 0) & (k < len(arr))
        o = np.full(len(tt), np.nan); o[ok] = arr[k[ok]]
        return o
    dF = np.full((len(LAGS), len(H), len(t)), np.nan, np.float32)
    for i, lag in enumerate(LAGS):
        f0 = F if lag == 0 else at(t + lag)
        for j, h in enumerate(H):
            dF[i, j] = at(t + lag + h) - f0
    # past 1-s path for behaviour labels: F at t-60, t-300, t-900
    back = np.stack([at(t - s) for s in (60, 300, 900)]).astype(np.float32)
    np.savez(os.path.join(OUT, day + '.npz'), t=t, F=F, vref=X[:, 2], X=X[:, 3:].astype(np.float32), dF=dF, back=back)
    print(day, len(t), round(time.time() - T0, 1), flush=True)
    if time.time() - T0 > 150:
        break
print('done', round(time.time() - T0, 1))
