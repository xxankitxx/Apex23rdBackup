import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""A slow 10-15 minute stand from slow inputs only (trend, VWAP, range, breadth), walk-forward ridge, then a stable
display rule (EWMA + Schmitt + 5-min dwell). Also: the current verdict words' change rate with the live 30-s hold."""
import os, glob
import numpy as np
D = r"D:\ApexOptions\data\research\13nov\work\R10"
H = (60, 120, 180, 300, 600, 900); LAGS = (0, 30)
FEATS = ("r5", "r15", "r30", "r60", "r120", "r300", "r600", "r1800", "lv30", "lv120", "lv600", "lv1800", "lviv",
         "lv120_600", "lv600_iv", "jump120", "absr5", "vr", "er300", "slope120", "kf", "imb", "micro", "ofi30", "ofi120",
         "spr", "vwap", "rng", "dhi", "dlo", "div60", "div300", "skew", "dskew300", "dstr60", "dbasis", "hw30", "hw120",
         "hwlead30", "bank120", "up60", "tod", "tod2", "left", "dte", "exp")
fi = {f: i for i, f in enumerate(FEATS)}
SLOW = [fi[k] for k in ("r300", "r600", "r1800", "vwap", "rng", "dhi", "dlo", "er300", "vr", "kf", "hw120", "bank120", "up60", "tod", "dte", "lv600_iv")]
days = []
for f in sorted(glob.glob(os.path.join(D, "cache", "*.npz"))):
    z = np.load(f); days.append(dict(day=os.path.basename(f)[:10], X=z["X"].astype(float), dF=z["dF"].astype(float), vref=z["vref"].astype(float)))
X0 = np.vstack([d["X"] for d in days[:5]]); med = np.nanmedian(X0, 0); sd = np.nanstd(X0, 0); sd = np.where(sd > 1e-9, sd, 1)
for d in days:
    d["Z"] = np.c_[np.ones(len(d["X"])), np.clip(np.nan_to_num((d["X"] - med) / sd), -6, 6)[:, SLOW]]


def fit(tr, j, lag=0, alpha=3000.0):
    A = 0; b = 0
    for d in tr:
        y = d["dF"][LAGS.index(lag), j] / np.sqrt(d["vref"] * H[j]); ok = np.isfinite(y)
        A = A + d["Z"][ok].T @ d["Z"][ok]; b = b + d["Z"][ok].T @ np.clip(y[ok], -4, 4)
    A = A.copy(); A[1:, 1:] += alpha * np.eye(A.shape[0] - 1)
    return np.linalg.solve(A, b)


for h in (600, 900):
    j = H.index(h)
    print(f"== slow stand, horizon {h // 60} min (lag 0)")
    tot = {"early": [0, 0], "late": [0, 0]}; tot_st = {"early": [0, 0, 0, 0], "late": [0, 0, 0, 0]}; ics = []
    for i in range(5, len(days)):
        w = fit(days[:i], j); d = days[i]
        s = d["Z"] @ w; y = d["dF"][0, j]; ok = np.isfinite(y) & (y != 0)
        ic = float(np.corrcoef(s[ok], y[ok])[0, 1]); ics.append((d["day"][5:], round(ic, 3)))
        win = "early" if d["day"] <= "2026-11-04" else "late"
        tot[win][0] += int((np.sign(s[ok]) == np.sign(y[ok])).sum()); tot[win][1] += int(ok.sum())
        # stable rule on the standardised score: EWMA half-life 60 s, enter |e| >= 0.10, leave < 0.04, 5-min dwell
        al = 1 - 0.5 ** (1 / 12.0); e = 0.0; cur = 0; since = -999; st = np.zeros(len(s), int)
        for k, x in enumerate(s):
            e += al * (x - e)
            want = cur
            if cur == 0:
                want = 1 if e >= 0.10 else -1 if e <= -0.10 else 0
            elif cur * e < 0.04:
                want = 0
            if want != cur and k - since >= 60:
                cur, since = want, k
            st[k] = cur
        m = ok & (st != 0)
        tot_st[win][0] += int((np.sign(st[m]) == np.sign(y[m])).sum()); tot_st[win][1] += int(m.sum())
        tot_st[win][2] += int((np.diff(st) != 0).sum()); tot_st[win][3] += len(st)
    print("  IC per day:", ics)
    for win in ("early", "late"):
        a = tot[win]; b = tot_st[win]
        print(f"  {win}: sign hit (all rows) {a[0] / a[1]:.3f} (~{a[1] * 5 / h:.0f} indep); stable stand hit {b[0] / max(b[1], 1):.3f}, "
              f"cover {b[1] / a[1]:.2f}, changes/h {b[2] / (b[3] * 5 / 3600):.1f}")
    # base rate of up moves at this horizon by window
    for win, sel in (("early", lambda x: x <= "2026-11-04"), ("late", lambda x: x >= "2026-11-05")):
        ys = np.concatenate([d["dF"][0, j] for d in days if sel(d["day"])]); ys = ys[np.isfinite(ys) & (ys != 0)]
        print(f"  base rate up {win}: {(ys > 0).mean():.3f}")

# the live verdict words with the 30-s hold of core._feed_step: change rate (2-min ridge z, words at 0.15 / 0.35)
R = np.load(os.path.join(D, "stand_rows.npz"))
fl = rows = 0
for k in [k for k in R.files if k.startswith("z120|")]:
    z = R[k].astype(float)
    w = np.where(z >= 0.35, 2, np.where(z >= 0.15, 1, np.where(z <= -0.35, -2, np.where(z <= -0.15, -1, 0))))
    shown = w[0]; cand = None; since = 0; n = 0
    for i, x in enumerate(w):
        if x != shown:
            if cand != x:
                cand, since = x, i
            elif i - since >= 6:
                shown, cand = x, None; n += 1
        else:
            cand = None
    fl += n; rows += len(w)
print(f"\ncurrent words (ridge z at 2 min, 0.15 / 0.35) with the 30-s hold: changes an hour {fl / (rows * 5 / 3600):.1f}")
