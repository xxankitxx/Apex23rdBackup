"""The fade family per second over the year of broker sessions (model option, normal days): stretch fades on a grid of
window x stretch, and opening-range fades on a grid of range length x cut-off. Two halves of the year and the window."""
import os, sys, glob
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import lab1s, hist1s
REC = set(FL.days())
N = FL.N


def sig_orb(D, rng_min=15, until_min=150):
    fs = D["fs"]; r = rng_min * 60
    seg = fs[:r]; seg = seg[np.isfinite(seg)]
    if not len(seg):
        return []
    hi, lo = seg.max(), seg.min()
    for i in range(r + 59 - (r % 60), until_min * 60, 60):
        f = fs[i]
        if f == f:
            if f > hi: return [(i, "PE", "orb")]
            if f < lo: return [(i, "CE", "orb")]
    return []


def one(day):
    D = lab1s.session(day, fwd=FL.load_day(day)["fwd"].copy()) if day in REC else lab1s.session(day)
    if D is None or D["dte0"]:
        return []
    rows = []
    for W in (10, 20, 30, 45, 60, 90):
        for z in (0.4, 0.5, 0.6, 0.7, 0.8, 1.0):
            for t in lab1s.run(D, lab1s.sig_fade(D, W, z)):
                t.update(kind="stretch", a=W, b=z); rows.append(t)
    for rm in (5, 10, 15, 30, 60):
        for um in (150, 255):
            for t in lab1s.run(D, sig_orb(D, rm, um)):
                t.update(kind="orb", a=rm, b=um); rows.append(t)
    return rows


if __name__ == "__main__":
    have = sorted({os.path.basename(p).split("_")[-1][:10] for p in glob.glob(os.path.join(hist1s.OUT, "fut_*.parquet"))})
    days = sorted(set(have) | REC)
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, days):
            rows += r
    T = pd.DataFrame(rows)
    T.to_parquet(os.path.join(hist1s.OUT, "fade_grid_1s.parquet"))
    hist = sorted(d for d in T.day.unique() if d < "2026-10-19"); mid = hist[len(hist) // 2]
    pd.set_option("display.width", 220)
    for kind, la, lb in (("stretch", "window (min)", "stretch (day-sigmas)"), ("orb", "opening range (min)", "cut-off (min after open)")):
        G = T[T.kind == kind]
        for tag, s in ((f"older half (to {mid})", G[G.day < mid]), ("newer half", G[(G.day >= mid) & (G.day < "2026-10-19")]), ("recorded window", G[G.day >= "2026-10-19"])):
            print(f"\n{kind} fades, {tag}: % per trade (rows {la}, columns {lb})")
            print(s.pivot_table(index="a", columns="b", values="ret", aggfunc="mean").round(2).to_string())
            if tag.startswith("older"):
                print("trades in that half:"); print(s.pivot_table(index="a", columns="b", values="ret", aggfunc="size").to_string())
    Y = T[T.day < "2026-10-19"]
    print("\nwhole year before the window, cells positive in BOTH halves:")
    o = Y.assign(h=np.where(Y.day < mid, "old", "new")).pivot_table(index=["kind", "a", "b"], columns="h", values="ret", aggfunc="mean")
    print(f"stretch: {int(((o.loc['stretch'].old > 0) & (o.loc['stretch'].new > 0)).sum())} of {len(o.loc['stretch'])}; opening range: {int(((o.loc['orb'].old > 0) & (o.loc['orb'].new > 0)).sum())} of {len(o.loc['orb'])}")
