import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""The proposed display rule, frozen before this run: p = Platt(earlier test days) of the fused 2-min stand;
BULLISH when p >= 0.56, BEARISH when p <= 0.44, kept while p stays beyond 0.53 / 0.47; a new word is shown only after
it has held 30 s (as core._feed_step). Scored at 1, 2, 3 min (lag 0) and 2 min with a 30-s delay. Also the lean shown
inside NEUTRAL. Test days 29 Oct - 11 Nov (the first two test days only feed the calibration)."""
import os, glob
import numpy as np
D = r"D:\ApexOptions\data\research\13nov\work\R10"
H = (60, 120, 180, 300, 600, 900); LAGS = (0, 30)
R = np.load(os.path.join(D, "stand_rows.npz"))
cache = {os.path.basename(f)[:10]: np.load(f) for f in sorted(glob.glob(os.path.join(D, "cache", "*.npz")))}
tdays = sorted({k.split("|")[1] for k in R.files if k.startswith("lag0_H120|")})
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
y_of = lambda d, lag, h: cache[d]["dF"][LAGS.index(lag), H.index(h)].astype(float)


def platt(x, y):
    w = np.zeros(2); Xc = np.c_[np.ones(len(x)), x]
    for _ in range(30):
        p = 1 / (1 + np.exp(-(Xc @ w)))
        st = np.linalg.solve((Xc * (p * (1 - p))[:, None]).T @ Xc + 1e-6 * np.eye(2), Xc.T @ (p - y)); w -= st
        if np.abs(st).max() < 1e-8: break
    return w


def display(p, e_in=0.56, e_out=0.53, hold=6):
    raw = np.zeros(len(p), int); cur = 0
    for i, x in enumerate(p):
        if cur == 0:
            cur = 1 if x >= e_in else -1 if x <= 1 - e_in else 0
        elif cur == 1 and x < e_out:
            cur = -1 if x <= 1 - e_in else 0
        elif cur == -1 and x > 1 - e_out:
            cur = 1 if x >= e_in else 0
        raw[i] = cur
    shown = np.zeros(len(p), int); s = raw[0]; cand = None; since = 0; n = 0
    for i, x in enumerate(raw):
        if x != s:
            if cand != x: cand, since = x, i
            elif i - since >= hold: s, cand = x, None; n += 1
        else:
            cand = None
        shown[i] = s
    return shown, n


tab = {}
for k in range(2, len(tdays)):
    d = tdays[k]
    x = np.concatenate([lg(R[f"lag0_H120|{q}"].astype(float)) for q in tdays[:k]])
    y = np.concatenate([y_of(q, 0, 120) for q in tdays[:k]]); ok = np.isfinite(y) & (y != 0)
    w = platt(x[ok], (y[ok] > 0).astype(float))
    p = 1 / (1 + np.exp(-(w[0] + w[1] * lg(R[f"lag0_H120|{d}"].astype(float)))))
    st, n = display(p)
    row = dict(changes_h=n / (len(p) * 5 / 3600))
    for lag, h in ((0, 60), (0, 120), (0, 180), (30, 120), (0, 600)):
        yy = y_of(d, lag, h); ok = np.isfinite(yy) & (yy != 0)
        m = ok & (st != 0); mn = ok & (st == 0)
        row[f"hit{lag}_{h}"] = ((np.sign(st[m]) == np.sign(yy[m])).sum(), m.sum())
        row[f"lean{lag}_{h}"] = ((np.sign(p[mn] - 0.5) == np.sign(yy[mn])).sum(), mn.sum())
        row["cover"] = m.sum() / max(ok.sum(), 1)
    tab[d] = row
print("day   | stand hit 1m / 2m / 3m / 2m after 30 s / 10m | cover | changes/h | NEUTRAL-lean hit 2m")
agg = {}
for d, r in tab.items():
    f = lambda key: r[key][0] / max(r[key][1], 1)
    print(f"{d[5:]} | {f('hit0_60'):.3f} {f('hit0_120'):.3f} {f('hit0_180'):.3f} {f('hit30_120'):.3f} {f('hit0_600'):.3f} | {r['cover']:.2f} | {r['changes_h']:.1f} | {f('lean0_120'):.3f}")
    for kk in r:
        if kk.startswith(("hit", "lean")):
            a = agg.setdefault(("early" if d <= "2026-11-04" else "late", kk), [0, 0]); a[0] += r[kk][0]; a[1] += r[kk][1]
for win in ("early", "late"):
    print(win, {kk: f"{v[0] / max(v[1], 1):.3f} (n={v[1]}, ~{v[1] * 5 / int(kk.split('_')[1]):.0f} indep)" for (w_, kk), v in agg.items() if w_ == win})
