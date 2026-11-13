import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""'How the market is behaving' labels with fixed thresholds (set before looking): what each label says about the next
1 to 15 minutes, on all 16 collected days, split early (19 Oct - 4 Nov) and late (5 - 11 Nov)."""
import os, glob, json
import numpy as np
D = r"D:\ApexOptions\data\research\13nov\work\R10"
H = (60, 120, 180, 300, 600, 900); LAGS = (0, 30)
FEATS = ("r5", "r15", "r30", "r60", "r120", "r300", "r600", "r1800", "lv30", "lv120", "lv600", "lv1800", "lviv",
         "lv120_600", "lv600_iv", "jump120", "absr5", "vr", "er300", "slope120", "kf", "imb", "micro", "ofi30", "ofi120",
         "spr", "vwap", "rng", "dhi", "dlo", "div60", "div300", "skew", "dskew300", "dstr60", "dbasis", "hw30", "hw120",
         "hwlead30", "bank120", "up60", "tod", "tod2", "left", "dte", "exp")
f = {k: i for i, k in enumerate(FEATS)}
NAMES = ("breaking out up", "breaking out down", "reversing up", "reversing down", "trending up", "trending down",
         "chopping", "drifting")
DIRN = {0: 1, 1: -1, 2: 1, 3: -1, 4: 1, 5: -1}


def label(X):
    g = lambda k: X[:, f[k]].astype(float)
    r120, r300, r1800, er, vr, kf, dhi, dlo, tod = (g(k) for k in ("r120", "r300", "r1800", "er300", "vr", "kf", "dhi", "dlo", "tod"))
    after = tod * 22500 >= 1800
    L = np.full(len(X), 7)
    L[(er < 0.15) | (vr < 0.7)] = 6
    L[(er >= 0.30) & (r300 <= -0.7) & (kf < 0)] = 5
    L[(er >= 0.30) & (r300 >= 0.7) & (kf > 0)] = 4
    L[(r1800 >= 1.5) & (r120 <= -1.0)] = 3
    L[(r1800 <= -1.5) & (r120 >= 1.0)] = 2
    L[after & (dlo <= 0.05) & (r300 <= -1.0)] = 1
    L[after & (dhi <= 0.05) & (r300 >= 1.0)] = 0
    return L


rows = {w: {n: {"n": 0} for n in NAMES} for w in ("early", "late")}
acc = {w: {} for w in ("early", "late")}
runs = {n: [] for n in NAMES}
for fn in sorted(glob.glob(os.path.join(D, "cache", "*.npz"))):
    day = os.path.basename(fn)[:10]
    z = np.load(fn)
    X, dF, vref = z["X"], z["dF"], z["vref"].astype(float)
    w = "early" if day <= "2026-11-04" else "late"
    L = label(X)
    r300 = X[:, f["r300"]].astype(float)
    # run lengths
    ch = np.r_[0, np.flatnonzero(np.diff(L)) + 1, len(L)]
    for a, b in zip(ch[:-1], ch[1:]):
        runs[NAMES[L[a]]].append((b - a) * 5)
    for k in range(8):
        m = L == k
        a = acc[w].setdefault(k, {})
        a["n"] = a.get("n", 0) + int(m.sum())
        sgn = DIRN.get(k, None)
        for i, lag in enumerate(LAGS):
            for j, h in enumerate(H):
                y = dF[i, j].astype(float)
                ok = m & np.isfinite(y) & (y != 0)
                s = np.full(len(y), np.nan)
                if sgn is not None:
                    s[:] = sgn
                else:
                    s = np.sign(r300)                     # chop / drift: does the last 5-min move continue?
                okk = ok & (s != 0)
                a.setdefault(f"c{lag}_{h}", [0, 0])
                a[f"c{lag}_{h}"][0] += int((np.sign(y[okk]) == s[okk]).sum()); a[f"c{lag}_{h}"][1] += int(okk.sum())
                a.setdefault(f"m{lag}_{h}", [0.0, 0])
                a[f"m{lag}_{h}"][0] += float((s[okk] * y[okk] / np.sqrt(vref[okk] * h)).sum()); a[f"m{lag}_{h}"][1] += int(okk.sum())
                a.setdefault(f"abs{h}", [0.0, 0])
                if lag == 0:
                    a[f"abs{h}"][0] += float((np.abs(y[ok]) / np.sqrt(vref[ok] * h)).sum()); a[f"abs{h}"][1] += int(ok.sum())
out = {}
for w in ("early", "late"):
    tot = sum(acc[w][k]["n"] for k in acc[w])
    print(f"== {w}: rows {tot}")
    print("label              share  | follow-rate lag0 at 1/3/5/10/15 min | lag30 at 3/10 min | mean signed move (sd) 3m/10m | |move| 5m (sd)")
    for k in range(8):
        a = acc[w][k]
        fr = lambda key: a[key][0] / max(a[key][1], 1)
        mm = lambda key: a[key][0] / max(a[key][1], 1)
        line = (f"{NAMES[k]:18s} {a['n'] / tot:5.1%} | " + " ".join(f"{fr(f'c0_{h}'):.3f}" for h in (60, 180, 300, 600, 900))
                + f" | {fr('c30_180'):.3f} {fr('c30_600'):.3f} | {mm('m0_180'):+.3f} {mm('m0_600'):+.3f} | {a['abs300'][0] / max(a['abs300'][1], 1):.2f}")
        print(line)
        out[f"{w}|{NAMES[k]}"] = {kk: (v if not isinstance(v, list) else [v[0], v[1]]) for kk, v in a.items()}
print("median run length (s):", {n: (int(np.median(v)) if v else None) for n, v in runs.items()})
json.dump(out, open(os.path.join(D, "labels.json"), "w"), indent=1)
