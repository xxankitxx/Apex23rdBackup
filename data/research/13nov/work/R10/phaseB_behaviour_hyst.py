import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""PHASE B (after 15:30, alone; needs work/R10/cache). The 'how the market is behaving' label WITH hysteresis:
a new label is shown only after its condition has held 60 s, and kept at least 120 s. For each label: share of the
day, median run length, what the next 5 / 15 minutes did (follow rate, mean signed move, size of the move against
the 80 % range), early (19 Oct - 4 Nov) against late (5 - 11 Nov). One fixed set of thresholds (labels.py), so a
single variant: the result is a description test, not a search."""
import os, glob
import numpy as np
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R10")
from labels import label, NAMES, DIRN, H, LAGS            # labels.py runs its own study on import: about 20 s
D = r"D:\ApexOptions\data\research\13nov\work\R10"


def held(L, enter=12, keep=24):
    out = np.empty(len(L), int); cur = L[0]; cand = None; since = 0; start = 0
    for i, x in enumerate(L):
        if x != cur:
            if cand != x: cand, since = x, i
            elif i - since >= enter and i - start >= keep: cur, cand, start = x, None, i
        else:
            cand = None
        out[i] = cur
    return out


acc = {}
for fn in sorted(glob.glob(os.path.join(D, "cache", "*.npz"))):
    day = os.path.basename(fn)[:10]; z = np.load(fn); X, dF, vref = z["X"], z["dF"].astype(float), z["vref"].astype(float)
    w = "early" if day <= "2026-11-04" else "late"
    S = held(label(X))
    ch = np.r_[0, np.flatnonzero(np.diff(S)) + 1, len(S)]
    for a, b in zip(ch[:-1], ch[1:]):
        acc.setdefault((w, S[a]), dict(runs=[], f5=[0, 0], f15=[0, 0], m15=[]))["runs"].append((b - a) * 5)
    for k in range(8):
        m = S == k
        if not m.any(): continue
        a = acc.setdefault((w, k), dict(runs=[], f5=[0, 0], f15=[0, 0], m15=[]))
        sg = DIRN.get(k); s = np.full(len(S), float(sg)) if sg else np.sign(X[:, 5].astype(float))
        for key, j in (("f5", H.index(300)), ("f15", H.index(900))):
            y = dF[0, j]; ok = m & np.isfinite(y) & (y != 0) & (s != 0)
            a[key][0] += int((np.sign(y[ok]) == s[ok]).sum()); a[key][1] += int(ok.sum())
        y = dF[0, H.index(900)]; ok = m & np.isfinite(y)
        a["m15"] += list(s[ok] * y[ok] / np.sqrt(vref[ok] * 900))
for w in ("early", "late"):
    print("==", w)
    for k in range(8):
        a = acc.get((w, k))
        if not a: continue
        print(f"  {NAMES[k]:18s} runs {len(a['runs']):4d} median {int(np.median(a['runs'])):5d} s | follow 5m {a['f5'][0] / max(a['f5'][1], 1):.3f} "
              f"15m {a['f15'][0] / max(a['f15'][1], 1):.3f} | mean signed 15m {np.mean(a['m15']) if a['m15'] else float('nan'):+.3f} sd")
