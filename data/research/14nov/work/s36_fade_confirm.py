"""Fade refinement on four years (found before 2025, judged after): wait for the turn. After a stretched W-minute move,
enter only when a 1-minute close has come back r points from the extreme reached since the stretch, within 15 minutes."""
import os, sys
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
import lab1, h4
NB = lab1.NB


def sig(D, W, z, r, wait=15):
    c, h, l = D["c"], D["h"], D["l"]
    em = D["em"]; k = c[0] / 25000.0
    out = []; last = {"CE": -999, "PE": -999}; arm = None
    for b in range(W, 345):
        m = c[b] - c[b - W]
        if arm is None:
            side = "PE" if m >= z * em else ("CE" if m <= -z * em else None)
            if side and b - last[side] >= W:
                if r <= 0:
                    out.append((b, side, "")); last[side] = b
                else:
                    arm = [side, h[b] if side == "PE" else l[b], b]
        else:
            side, ext, b0 = arm
            if b - b0 > wait:
                arm = None; continue
            ext = max(ext, h[b]) if side == "PE" else min(ext, l[b]); arm[1] = ext
            back = (ext - c[b]) if side == "PE" else (c[b] - ext)
            if back >= r * k:
                out.append((b, side, "")); last[side] = b; arm = None
    return out


V = [(W, z, r) for W, z in ((20, 0.5), (20, 0.6), (60, 0.7), (30, 0.6)) for r in (0, 5, 10, 20)]


def work(chunk):
    ALL = [D for D in h4.load() if not D["dte0"]]
    rows = []
    for W, z, r in chunk:
        for D in ALL:
            for t in lab1.run(D, sig(D, W, z, r), model=True):
                t.update(W=W, z=z, r=r); rows.append(t)
    return rows


if __name__ == "__main__":
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for x in ex.map(work, [V[i::8] for i in range(8)]):
            rows += x
    T = pd.DataFrame(rows)
    out = []
    for (W, z, r), g in T.groupby(["W", "z", "r"]):
        rr = dict(fade=f"{W}m {z} sigma", wait_for_turn=f"{r} pts" if r else "no (enter at once)")
        for tag, s in (("2022-24", g[g.day < h4.SPLIT]), ("2025-26", g[g.day >= h4.SPLIT])):
            ds = s.groupby("day").ret.sum()
            rr[f"{tag} trades"] = len(s); rr[f"{tag} win"] = round(100 * (s.ret > 0).mean()); rr[f"{tag} per trade"] = round(s.ret.mean(), 2)
            rr[f"{tag} t"] = round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1)
        out.append(rr)
    pd.set_option("display.width", 220)
    print(pd.DataFrame(out).to_string(index=False))
