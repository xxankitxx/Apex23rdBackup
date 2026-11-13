import glob, os
import numpy as np
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sister")


def load(day):
    ts, Xs, As = [], [], []
    for p in sorted(glob.glob(os.path.join(D, day + "*.npz"))):
        z = np.load(p); ts.append(z["t"]); Xs.append(z["X"]); As.append(z["A"])
    t = np.concatenate(ts); X = np.concatenate(Xs); A = np.concatenate(As)
    o = np.argsort(t); t, X, A = t[o], X[o], A[o]
    keep = np.r_[True, np.diff(t) > 0]
    t, X, A = t[keep], X[keep], A[keep]
    g = np.arange(t[0], t[-1] + 1)                         # fill gaps between parts with nan
    k = np.searchsorted(t, g); ok = (k < len(t)) & (t[np.minimum(k, len(t) - 1)] == g)
    XX = np.full((len(g), X.shape[1]), np.nan); AA = np.full((len(g), A.shape[1]), 1e9)
    XX[ok] = X[k[ok]]; AA[ok] = A[k[ok]]
    return g, XX, AA


def mid(X, A, b, ai):
    m = (X[:, b + 1] + X[:, b + 2]) / 2
    bad = ~(X[:, b + 2] >= X[:, b + 1]) | (A[:, ai] > 5)
    m[bad] = np.nan
    return m


