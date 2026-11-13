import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R18 Phase B: a book-independent time-of-day map from the per-second ds_v2 parts.

For each day part (one at a time, sequential):
  A. ATM option buy baseline. Every 60 s from 09:20 to the last entry (15:15, or 14:45 on expiry days) buy the
     nearest-the-money CE and PE at the ask and sell at the bid after H = 10 and 20 minutes (or at the flat time,
     15:25 / 15:00 on expiry). Also the "momentum side" (the side of the last 5-minute futures move) and the
     "fade side". Result by half hour, by day type (expiry / day before / other).
  B. Opening-range follow-through. OR30 = futures high / low 09:15-09:45. After 09:45, the first break by 5 points:
     futures move in the break direction at +5, +15, +30, +60 min and the worst adverse move in 30 min.
  C. Gap. Futures first print versus the previous part's last print; when (if) the gap fills; the futures move from
     09:15 to 09:45 in the gap direction.
Usage (after 15:30 only, one run, about 17 parts): py -3.13 phaseB_tod_baseline.py [part ...]
Default parts: every ds_v2 part with rows > 0. Output: tod_baseline.csv, orb_follow.csv, gap.csv in this folder.
"""
import glob, json, os
import numpy as np, pandas as pd

DS = r"D:\ApexOptions\data\research\ds_v2"
OUT = os.path.dirname(os.path.abspath(__file__))
IST = 19800


def hm_of(t):
    return ((t + IST) % 86400) / 60.0


def parts(argv):
    if argv:
        return argv
    out = []
    for m in sorted(glob.glob(os.path.join(DS, "*.manifest.json"))):
        j = json.load(open(m, encoding="utf-8"))
        if j.get("rows", 0) > 0:
            out.append(j["part"])
    return out


def main(argv):
    A, B, C = [], [], []
    prev_close = None
    prev_day_tag = "none"
    for p in parts(argv):
        z = np.load(os.path.join(DS, p + ".npz"))
        man = json.load(open(os.path.join(DS, p + ".manifest.json"), encoding="utf-8"))
        day = p.split(".")[0]
        exp = str(man.get("expiry") or "")
        dte0 = exp == day
        t = z["t"]; f = z["fut"][:, 0].astype(float)
        opt = z["opt"]; K = z["strikes"].astype(float)
        hm = hm_of(t)
        # bid / ask order check (index 0 should be the lower)
        q = opt[:, :, :, 0] - opt[:, :, :, 1]
        bi, ai = (0, 1) if np.nanmean(q) < 0 else (1, 0)
        flat = 15 * 60 if dte0 else 15 * 60 + 25
        last = 14 * 60 + 45 if dte0 else 15 * 60 + 15
        # C gap
        ok = np.isfinite(f)
        i0 = int(np.argmax(ok & (hm >= 9 * 60 + 15)))
        f0 = f[i0]
        if prev_close is not None and day != prev_day_tag:
            g = f0 - prev_close
            fill = np.where(ok & (hm > hm[i0]) & ((f - prev_close) * np.sign(g) <= 0))[0]
            i45 = int(np.argmax(hm >= 9 * 60 + 45))
            C.append(dict(day=day, gap=round(g, 2), filled=len(fill) > 0,
                          fill_hm=round(hm[fill[0]], 2) if len(fill) else None,
                          mv_0915_0945_with_gap=round((f[i45] - f0) * np.sign(g), 2)))
        # B ORB30
        m30 = ok & (hm >= 9 * 60 + 15) & (hm < 9 * 60 + 45)
        if m30.any():
            hi, lo = np.nanmax(f[m30]), np.nanmin(f[m30])
            aft = np.where(ok & (hm >= 9 * 60 + 45) & ((f > hi + 5) | (f < lo - 5)))[0]
            if len(aft):
                k = aft[0]; d = 1 if f[k] > hi else -1
                row = dict(day=day, dte0=dte0, brk_hm=round(hm[k], 2), side=d, or_rng=round(hi - lo, 1))
                for mn in (5, 15, 30, 60):
                    j = np.searchsorted(t, t[k] + mn * 60)
                    row[f"mv{mn}"] = round((f[min(j, len(f) - 1)] - f[k]) * d, 2)
                j30 = np.searchsorted(t, t[k] + 1800)
                row["worst30"] = round(np.nanmin((f[k:j30] - f[k]) * d), 2)
                B.append(row)
        # A ATM buy baseline
        for s in np.arange(9 * 60 + 20, last, 1.0):
            i = int(np.searchsorted(hm, s))
            if i >= len(t) or not np.isfinite(f[i]):
                continue
            ka = int(np.nanargmin(np.abs(K - f[i])))       # futures-nearest strike (close enough to ATM for a map)
            i5 = int(np.searchsorted(t, t[i] - 300))
            mom = np.sign(f[i] - f[i5]) if np.isfinite(f[i5]) else 0
            for H in (10, 20):
                j = int(np.searchsorted(t, min(t[i] + H * 60, t[i] + (flat - s) * 60)))
                if j >= len(t):
                    continue
                for side, si in (("CE", 0), ("PE", 1)):
                    a = opt[i, ka, si, ai]; b = opt[j, ka, si, bi]
                    if not (np.isfinite(a) and np.isfinite(b) and a > 0):
                        continue
                    r = (b / a - 1) * 100
                    sd = 1 if side == "CE" else -1
                    A.append(dict(day=day, dte0=dte0, hm=s, hh=int(s // 30 * 30), H=H, side=side,
                                  mom=(mom == sd), ret=round(float(r), 3)))
        prev_close = f[ok][-1] if ok.any() else prev_close
        prev_day_tag = day
        del z, opt
    a = pd.DataFrame(A); a.to_csv(os.path.join(OUT, "tod_baseline.csv"), index=False)
    pd.DataFrame(B).to_csv(os.path.join(OUT, "orb_follow.csv"), index=False)
    pd.DataFrame(C).to_csv(os.path.join(OUT, "gap.csv"), index=False)
    if len(a):
        g = a.groupby(["dte0", "H", "mom", "hh"]).ret.agg(["size", "mean", lambda s: (s > 0).mean() * 100])
        g.columns = ["n", "mean", "win"]
        print(g.round(2).to_string())
    print(pd.DataFrame(B).to_string())
    print(pd.DataFrame(C).to_string())


if __name__ == "__main__":
    main(sys.argv[1:])
