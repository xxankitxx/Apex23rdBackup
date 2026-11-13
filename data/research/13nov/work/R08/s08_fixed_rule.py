import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, json, os
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R08")
from s04_leadlag_lib import load, basket, breadth, dF, fwd
PARTS = sys.argv[1:] or ["2026-10-26", "2026-11-05", "2026-11-09"]
OUT = r"D:\ApexOptions\data\research\13nov\work\R08"
res = {}
for p in PARTS:
    D = load(p); F = D["F"]; w = D["w"]
    own10 = dF(F, 10)
    g10 = basket(D["lc"], w, 10) * F - own10
    gs10 = basket(D["ls"], w, 10) * F - own10
    b60 = breadth(D["lc"], w, 60)
    # the proposed fixed (unfitted) pressure, in Nifty points: 0.1 x own 10-s move + 0.27 x cash gap + 0.1 x stock-futures gap
    P = 0.1 * own10 + 0.27 * g10 + 0.1 * gs10
    r = {"sd_g10": round(float(np.nanstd(g10)), 2), "sd_P": round(float(np.nanstd(P)), 2)}
    for h in (10, 30, 60, 120, 300):
        y = fwd(F, h)
        for th in (0.5, 1.0, 1.5):
            for bmin in (0.0, 0.3):
                on = np.isfinite(P) & np.isfinite(y) & np.isfinite(b60) & (np.abs(P) >= th) & (b60 * np.sign(P) >= bmin)
                idx = np.where(on)[0][::5]          # thin the overlapping seconds
                s = np.sign(P[idx])
                r[f"h{h}_th{th}_b{bmin}"] = dict(cover=round(float(on.mean()), 3), n=int(len(idx)),
                                                  hit=round(float(np.mean(s * y[idx] > 0)), 3),
                                                  pts=round(float(np.mean(s * y[idx])), 2))
    res[p] = r
    print(p, r["sd_g10"], r["sd_P"])
    for k, v in r.items():
        if k.startswith("h") and ("th1.0" in k):
            print("  ", k, v)
json.dump(res, open(os.path.join(OUT, "s08_fixed_rule.json"), "w"), indent=1)
