import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 step 7: the Forecast Lab forecasts the FUTURES MID (core.py:638). Option premiums follow the parity FORWARD.
Does the Lab's skill survive when the target is the forward? Walk-forward ridge on the Lab's own 46 features,
same rows, two targets. Plus the 'univariate' IC of the Lab's dbasis and r-features on both targets."""
import os
import numpy as np, joblib

W = r"D:\ApexOptions\data\research\13nov\work\R07"
COL = r"D:\ApexOptions\data\forecast_lab\collect"
HZ = [10, 30, 60, 120, 180, 300]
LABN = ["r5", "r15", "r30", "r60", "r120", "r300", "r600", "r1800", "lv30", "lv120", "lv600", "lv1800", "lviv", "lv120_600",
        "lv600_iv", "jump120", "absr5", "vr", "er300", "slope120", "kf", "imb", "micro", "ofi30", "ofi120", "spr", "vwap",
        "rng", "dhi", "dlo", "div60", "div300", "skew", "dskew300", "dstr60", "dbasis", "hw30", "hw120", "hwlead30",
        "bank120", "up60", "tod", "tod2", "left", "dte", "exp"]


def rank(a):
    o = np.argsort(a, kind="stable"); r = np.empty(len(a)); r[o] = np.arange(len(a)); return r


def spear(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 30 or np.std(x[m]) == 0 or np.std(y[m]) == 0:
        return np.nan
    return float(np.corrcoef(rank(x[m]), rank(y[m]))[0, 1])


def at_time(t, y, tq):
    j = np.searchsorted(t, tq, side="right") - 1
    return np.where(j >= 0, y[np.clip(j, 0, None)], np.nan), j


def fit(Xtr, ytr, lam=50.0):
    med = np.nanmedian(Xtr, 0); sd = np.nanstd(Xtr, 0); sd[~(sd > 0)] = 1
    Z = np.clip(np.nan_to_num((Xtr - med) / sd), -6, 6); m = np.isfinite(ytr)
    w = np.linalg.solve(Z[m].T @ Z[m] + lam * np.eye(Z.shape[1]), Z[m].T @ (ytr[m] - ytr[m].mean()))
    return med, sd, w, ytr[m].mean()


def pred(mdl, X):
    med, sd, w, c = mdl
    return np.clip(np.nan_to_num((X - med) / sd), -6, 6) @ w + c


def topdir(p, y, q=0.2):
    m = np.isfinite(p) & np.isfinite(y) & (y != 0); p, y = p[m], y[m]
    k = max(1, int(q * len(p))); idx = np.argsort(-np.abs(p))[:k]
    return float(np.mean(np.sign(p[idx]) == np.sign(y[idx])))


parts = sys.argv[1:]
D = {}
for p in parts:
    f = np.load(os.path.join(W, f"feat_{p}.npz"))
    t = f["t"]; fm = f["fm"].astype(float); fwd = f["fwd"].astype(float)
    lab = joblib.load(os.path.join(COL, p[:10] + ".joblib"))
    LX = np.asarray(lab["X"], float); lt = LX[:, 0]; vref = LX[:, 2]; LF = LX[:, 3:]
    j = np.searchsorted(t, lt, side="right") - 1
    ok = (j >= 0) & (np.abs(t[np.clip(j, 0, None)] - lt) <= 1); j = j[ok]
    ys = {}
    for nm, s in (("fut", fm), ("fwd", fwd)):
        cols = []
        for h in HZ:
            y, jh = at_time(t, s, t + h)
            gp = (t + h) - t[np.clip(jh, 0, len(t) - 1)]
            cols.append(np.where(gp > 3, np.nan, y - s)[j])
        ys[nm] = np.vstack(cols).T / np.sqrt(np.maximum(vref[ok], 1e-9)[:, None] * np.array(HZ)[None, :])
    D[p] = dict(X=LF[ok], y=ys)
print("horizons", HZ)
for k in ("dbasis", "r15", "r60", "ofi30", "kf", "hwlead30"):
    i = LABN.index(k)
    for tg in ("fut", "fwd"):
        print(f"IC {k:9s}->{tg}", "  ".join(f"{p[5:10]}:" + ",".join(f"{spear(D[p]['X'][:, i], D[p]['y'][tg][:, hi]):+.3f}" for hi in range(len(HZ))) for p in parts))
print("\nWALK-FORWARD ridge on the Lab's 46 features: test IC / top-fifth direction hit")
for ti in range(1, len(parts)):
    tr, te = parts[:ti], parts[ti]
    for hi, h in enumerate(HZ):
        s = []
        for tg in ("fut", "fwd"):
            mdl = fit(np.vstack([D[p]["X"] for p in tr]), np.concatenate([D[p]["y"][tg][:, hi] for p in tr]))
            pt = pred(mdl, D[te]["X"]); yt = D[te]["y"][tg][:, hi]; m = np.isfinite(yt)
            s.append(f"target {tg}: {np.corrcoef(pt[m], yt[m])[0, 1]:+.3f}/{topdir(pt, yt):.3f}")
        # cross: model trained for the future, scored on the forward (what the display implies for premiums)
        mdl = fit(np.vstack([D[p]["X"] for p in tr]), np.concatenate([D[p]["y"]["fut"][:, hi] for p in tr]))
        pt = pred(mdl, D[te]["X"]); yt = D[te]["y"]["fwd"][:, hi]; m = np.isfinite(yt)
        s.append(f"fut-model on fwd: {np.corrcoef(pt[m], yt[m])[0, 1]:+.3f}/{topdir(pt, yt):.3f}")
        print(f"test {te[5:10]} h={h:4d}  " + "   ".join(s))
