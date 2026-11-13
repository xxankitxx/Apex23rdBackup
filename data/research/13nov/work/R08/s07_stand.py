import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, json, time, os
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R08")
from s04_leadlag_lib import load, basket, breadth, dF, fwd
T0 = time.time()
TRAIN = sys.argv[1] if len(sys.argv) > 1 else "2026-10-26"
TESTS = sys.argv[2:] or ["2026-11-05", "2026-11-09"]
OUT = r"D:\ApexOptions\data\research\13nov\work\R08"


def feats(D):
    F = D["F"]; w = D["w"]
    X = {}
    for L in (10, 30, 60):
        X[f"own{L}"] = dF(F, L)
        X[f"g{L}"] = basket(D["lc"], w, L) * F - X[f"own{L}"]
        X[f"gs{L}"] = basket(D["ls"], w, L) * F - X[f"own{L}"]
    X["b60"] = breadth(D["lc"], w, 60)
    X["b60_30"] = np.r_[np.full(30, np.nan), X["b60"][:-30]]
    X["thr"] = X["b60"] - X["b60_30"]              # weight that joined in the last 30 s
    return X


COLS = ["own10", "g10", "gs10", "own60", "g60", "gs60", "b60", "thr"]
out = {}
data = {}
for p in [TRAIN] + TESTS:
    D = load(p)
    data[p] = (feats(D), D["F"])
    print(p, "loaded", round(time.time() - T0, 1), flush=True)
for h in (10, 30, 60, 180):
    Xtr, Ftr = data[TRAIN]
    def mat(X, F, step):
        A = np.c_[[X[c] for c in COLS]].T
        y = fwd(F, h)
        sl = slice(120, None, step)
        A, y = A[sl], y[sl]
        m = np.isfinite(A).all(1) & np.isfinite(y)
        return A[m], y[m]
    A, y = mat(Xtr, Ftr, max(5, h // 2))
    beta = np.linalg.lstsq(np.c_[np.ones(len(A)), A], y, rcond=None)[0]
    ptr = np.c_[np.ones(len(A)), A] @ beta - beta[0]
    th = np.quantile(np.abs(ptr), 0.8)
    res = {"beta": dict(zip(["c"] + COLS, [round(float(b), 4) for b in beta])), "th80": round(float(th), 2)}
    for p in TESTS:
        Xt, Ft = data[p]
        At, yt = mat(Xt, Ft, 10)
        pt = np.c_[np.ones(len(At)), At] @ beta - beta[0]
        on = np.abs(pt) >= th
        res[p] = dict(cover=round(float(on.mean()), 3), hit=round(float(np.mean(np.sign(pt[on]) == np.sign(yt[on]))), 3),
                      pts=round(float(np.mean(np.sign(pt[on]) * yt[on])), 2),
                      r2=round(float(1 - np.sum((yt - pt - beta[0]) ** 2) / np.sum((yt - yt.mean()) ** 2)), 4),
                      base_abs=round(float(np.mean(np.abs(yt))), 2), n=int(on.sum()))
        # agreement filter: the stand only when the cash gap and the weighted breadth agree with the prediction
        agree = on & (np.sign(At[:, 1]) == np.sign(pt)) & (np.sign(At[:, 6]) == np.sign(pt))
        res[p]["agree"] = dict(cover=round(float(agree.mean()), 3),
                               hit=round(float(np.mean(np.sign(pt[agree]) == np.sign(yt[agree]))), 3) if agree.any() else None,
                               pts=round(float(np.mean(np.sign(pt[agree]) * yt[agree])), 2) if agree.any() else None)
    out[f"h{h}"] = res
    print(h, json.dumps(res), flush=True)
json.dump(out, open(os.path.join(OUT, f"s07_stand_{TRAIN}.json"), "w"), indent=1)
print("secs", round(time.time() - T0, 1))
