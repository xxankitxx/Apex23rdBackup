import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 step 5: do signed trade flow (tfi) and the forward-minus-future gap ADD to the Forecast Lab's 46 features?
Walk-forward over the parts given in date order (train all earlier, test next). Horizons 5 s to 300 s.
Usage: py -3.13 s5_increment.py <part> <part> <part>"""
import os, time
import numpy as np, joblib

W = r"D:\ApexOptions\data\research\13nov\work\R07"
COL = r"D:\ApexOptions\data\forecast_lab\collect"
t00 = time.time()
parts = sys.argv[1:]
HZ = [5, 10, 30, 60, 120, 300]


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


def roll_med(t, x, Wd=300, step=1):
    """causal rolling median over (t-W, t] (slow but n ~ 22k; computed every 5th row then forward filled)."""
    out = np.full(len(t), np.nan)
    j0 = 0
    last = np.nan
    for i in range(len(t)):
        if i % 5 == 0:
            while t[j0] <= t[i] - Wd:
                j0 += 1
            seg = x[j0:i + 1]
            seg = seg[np.isfinite(seg)]
            last = np.median(seg) if len(seg) > 30 else np.nan
        out[i] = last
    return out


D = {}
for p in parts:
    f = np.load(os.path.join(W, f"feat_{p}.npz"))
    names = list(f["names"]); X = f["X"].astype(float); t = f["t"]; fm = f["fm"].astype(float); fwd = f["fwd"].astype(float)
    gap = fwd - fm
    gdev = gap - roll_med(t, gap)
    f5, _ = at_time(t, fwd, t - 5); m5, _ = at_time(t, fm, t - 5)
    lead5 = (fwd - f5) - (fm - m5)                      # the forward moved this much more than the future in 5 s
    f2, _ = at_time(t, fwd, t - 2); m2, _ = at_time(t, fm, t - 2)
    lead2 = (fwd - f2) - (fm - m2)
    Y = {}
    for h in HZ:
        y, jh = at_time(t, fm, t + h)
        gp = (t + h) - t[np.clip(jh, 0, len(t) - 1)]
        y[gp > 3] = np.nan
        Y[h] = y - fm
    lab = joblib.load(os.path.join(COL, p[:10] + ".joblib"))
    LX = np.asarray(lab["X"], float)
    lt = LX[:, 0]; vref = LX[:, 2]; LF = LX[:, 3:]
    j = np.searchsorted(t, lt, side="right") - 1
    ok = (j >= 0) & (np.abs(t[np.clip(j, 0, None)] - lt) <= 1)
    j = j[ok]
    tfi = np.vstack([X[j, names.index(k)] for k in ("tfi10", "tfi30", "tfi60")]).T
    gapf = np.vstack([gdev[j], lead5[j], lead2[j]]).T
    y = np.vstack([Y[h][j] for h in HZ]).T
    sc = np.sqrt(np.maximum(vref[ok], 1e-9)[:, None] * np.array(HZ)[None, :])
    D[p] = dict(lab=LF[ok], tfi=tfi, gap=gapf, y=y, ys=y / sc)
    print(p, "rows", int(ok.sum()), flush=True)

print("\nUNIVARIATE Spearman IC with the future's move")
for nm, k in (("gap_dev", 0), ("lead5", 1), ("lead2", 2)):
    print(nm.ljust(10), "  ".join(f"{p[5:10]}:" + ",".join(f"{spear(D[p]['gap'][:, k], D[p]['y'][:, hi]):+.3f}" for hi in range(len(HZ))) for p in parts))
for nm, k in (("tfi10", 0), ("tfi30", 1), ("tfi60", 2)):
    print(nm.ljust(10), "  ".join(f"{p[5:10]}:" + ",".join(f"{spear(D[p]['tfi'][:, k], D[p]['y'][:, hi]):+.3f}" for hi in range(len(HZ))) for p in parts))
print("(horizons", HZ, ")")


def fit(Xtr, ytr, lam=50.0):
    med = np.nanmedian(Xtr, 0); sd = np.nanstd(Xtr, 0); sd[~(sd > 0)] = 1
    Z = np.clip(np.nan_to_num((Xtr - med) / sd), -6, 6)
    m = np.isfinite(ytr)
    Z, yy = Z[m], ytr[m]
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (yy - yy.mean()))
    return med, sd, w, yy.mean()


def pred(mdl, X):
    med, sd, w, c = mdl
    return np.clip(np.nan_to_num((X - med) / sd), -6, 6) @ w + c


def topdir(p, y, q=0.2):
    m = np.isfinite(p) & np.isfinite(y) & (y != 0)
    p, y = p[m], y[m]
    k = max(1, int(q * len(p))); idx = np.argsort(-np.abs(p))[:k]
    return float(np.mean(np.sign(p[idx]) == np.sign(y[idx])))


sets = {"LAB": lambda d: d["lab"], "LAB+TFI": lambda d: np.hstack([d["lab"], d["tfi"]]),
        "LAB+GAP": lambda d: np.hstack([d["lab"], d["gap"]]), "LAB+TFI+GAP": lambda d: np.hstack([d["lab"], d["tfi"], d["gap"]])}
print("\nWALK-FORWARD ridge: test IC / top-fifth direction hit")
for ti in range(1, len(parts)):
    tr, te = parts[:ti], parts[ti]
    for hi, h in enumerate(HZ):
        s = []
        for nm, fx in sets.items():
            mdl = fit(np.vstack([fx(D[p]) for p in tr]), np.concatenate([D[p]["ys"][:, hi] for p in tr]))
            pt = pred(mdl, fx(D[te])); yt = D[te]["ys"][:, hi]; m = np.isfinite(yt)
            s.append(f"{nm}: {np.corrcoef(pt[m], yt[m])[0, 1]:+.3f}/{topdir(pt, yt):.3f}")
        print(f"test {te[5:10]} h={h:4d}  " + "  ".join(s))
print("done", round(time.time() - t00, 1))
