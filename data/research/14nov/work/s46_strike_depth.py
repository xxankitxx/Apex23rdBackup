"""Strike depth against all-in variance drag: the champion's pattern (replica) and the fades per second over the year
of broker sessions, normal days, model option, the strike chosen at |delta| 0.52 (live), 0.65 and 0.80."""
import os, sys, glob
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import fam, lab1s, hist1s
from s39_fade_grid_1s import sig_orb


def one(day):
    D = lab1s.session(day)
    if D is None or D["dte0"]:
        return []
    X = lab1s.feats(D)
    sigs = {"pattern": fam.sig_pb(D, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0),
            "fades": sorted(lab1s.sig_fade(D, 20, 0.6) + lab1s.sig_fade(D, 60, 0.7) + sig_orb(D, 15, 150))}
    rows = []
    for dt in (0.52, 0.65, 0.80):
        D["P"] = dict(FL.NORM, dt=dt)
        for nm, sg in sigs.items():
            for t in lab1s.run(D, sg):
                t.update(entries=nm, delta=dt); rows.append(t)
    return rows


if __name__ == "__main__":
    have = sorted({os.path.basename(p).split("_")[-1][:10] for p in glob.glob(os.path.join(hist1s.OUT, "fut_*.parquet"))})
    rows = []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for r in ex.map(one, have):
            rows += r
    T = pd.DataFrame(rows)
    T.to_parquet(os.path.join(hist1s.OUT, "strike_depth.parquet"))
    out = []
    for (e, dt), g in T.groupby(["entries", "delta"]):
        for per, s in (("year before the window", g[g.day < "2026-10-19"]), ("all 13 months", g)):
            r = s.ret.to_numpy() / 100
            cap = np.prod(1 + r)
            out.append(dict(entries=e, delta=dt, period=per, trades=len(s), winners=round(100 * (r > 0).mean()), mean=round(100 * r.mean(), 2), sd=round(100 * r.std(), 1),
                            mean_log=round(100 * np.mean(np.log1p(r)), 2), all_in_100_becomes=round(100 * cap, 1), premium_paid=round(s.e.median(), 0)))
    pd.set_option("display.width", 220)
    print(pd.DataFrame(out).to_string(index=False))
