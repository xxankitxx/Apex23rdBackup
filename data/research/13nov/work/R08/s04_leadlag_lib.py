import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, json, time, os
ROOT = r"D:\ApexOptions\data\research\ds_v2"
OUT = r"D:\ApexOptions\data\research\13nov\work\R08"
TAG = os.environ.get("R08_TAG", "s04")
BANK = ("bank", "nbfc")


def load(part):
    z = np.load(os.path.join(ROOT, part + ".npz"), allow_pickle=True)
    t = z["t"].astype(np.int64); fut = z["fut"]; fa = z["fa"][:, 0]
    hw = z["hw"].astype(float); hwa = z["hwa"]; sf = z["sf"].astype(float); sfa = z["sfa"]
    w = z["w"].astype(float); g = z["g"]; sym = z["sym"]
    n = int(t[-1] - t[0] + 1); idx = t - t[0]

    def grid(a):
        o = np.full((n,) + a.shape[1:], np.nan); o[idx] = a; return o
    mid = 0.5 * (fut[:, 0] + fut[:, 1]); okf = (fut[:, 0] > 0) & (fut[:, 1] >= fut[:, 0]) & (fa <= 3)
    F = grid(np.where(okf, mid, np.nan))
    cash = np.where((hw > 0) & (hwa <= 5), hw, np.nan)
    sfm = 0.5 * (sf[:, :, 0] + sf[:, :, 1])
    sfm = np.where((sf[:, :, 0] > 0) & (sf[:, :, 1] >= sf[:, :, 0]) & (sfa <= 5), sfm, np.nan)
    return dict(t0=int(t[0]), n=n, F=F, lc=np.log(grid(cash)), ls=np.log(grid(sfm)), w=w, g=g, sym=sym)


def basket(lp, w, L, mask=None):
    """weighted mean log return over L s (index-equivalent fraction); NaN if covered weight < 70 %"""
    d = np.full(lp.shape, np.nan); d[L:] = lp[L:] - lp[:-L]
    ww = w * (mask if mask is not None else 1.0)
    ok = np.isfinite(d) & (ww > 0)
    num = np.where(ok, d * ww, 0).sum(1); den = np.where(ok, ww, 0).sum(1)
    tot = ww.sum()
    return np.where(den >= 0.7 * tot, num / np.where(den > 0, den, 1), np.nan)


def breadth(lp, w, L):
    d = np.full(lp.shape, np.nan); d[L:] = lp[L:] - lp[:-L]
    ok = np.isfinite(d); ww = np.where(ok, w, 0)
    den = ww.sum(1)
    return np.where(den >= 0.7 * w.sum(), (np.sign(np.where(ok, d, 0)) * ww).sum(1) / np.where(den > 0, den, 1), np.nan)


def dF(F, L):
    o = np.full(F.shape, np.nan); o[L:] = F[L:] - F[:-L]; return o


def fwd(F, h):
    o = np.full(F.shape, np.nan); o[:-h] = F[h:] - F[:-h]; return o



