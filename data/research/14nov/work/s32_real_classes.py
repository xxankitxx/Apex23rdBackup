"""The REAL strategy classes (c20_9x, c20_9y, the stall twin, the fade books) stepped second by second through the
broker's 1-second sessions, on a model option chain (normal days; open interest and a moving IV are not in the model,
so c20_9y's two vetoes cannot fire). First checked on the recorded sessions against the same classes on tape quotes.

    py -3.13 s32_real_classes.py check | run
"""
import os, sys, glob, json, pickle, tempfile
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import lab1s, hist1s, h4
N = FL.N
BOOKS = ("c20_9x", "c20_9y_st15", "fade20", "fade60", "orbfade")
LEVELS = os.path.join(hist1s.OUT, "levels_all.json")


def levels_file():
    if not os.path.exists(LEVELS):
        m = pickle.load(open(h4.PKL, "rb"))
        json.dump({d["day"]: {"close": float(d["c"][-1] - d["basis"]), "hi": float(d["h"].max() - d["basis"]), "lo": float(d["l"].min() - d["basis"])} for d in m}, open(LEVELS, "w"))
    return LEVELS


def model_live(D):
    """a council LiveDay whose option chain is the model (Black-76 on the session's forward, the day's model IV)."""
    from apex.engine.council import LiveDay
    L = LiveDay(D["day"], D["expiry"])
    fw = FL._ffill0(D["fwd"])
    lo, hi = np.nanmin(fw), np.nanmax(fw)
    Ks = np.arange(np.floor(lo / 50.0) * 50.0 - 200.0, np.ceil(hi / 50.0) * 50.0 + 250.0, 50.0)
    cols = [(k, c) for k in Ks for c in (0, 1)]
    cols = cols[:96]
    L.K = np.array([k for k, _ in cols]); L.rr = np.array(["CE" if c == 0 else "PE" for _, c in cols])
    L.fwd[:] = D["fwd"]; L.spot[:] = D["fwd"]; L.fut[:] = D["fwd"]
    iv = D["iv"]
    with np.errstate(all="ignore"):
        for q, (k, c) in enumerate(cols):
            L.col[(int(k), "CE" if c == 0 else "PE")] = q
            px = FL.b76(fw, k, D["T"], iv, c == 0)
            dl, gm, th = FL.greeks(fw, k, D["T"], iv, c == 0)
            L.bid[:, q] = px * (1 - lab1s.HALF); L.ask[:, q] = px * (1 + lab1s.HALF); L.mid[:, q] = px; L.ltp[:, q] = px
            L.age[:, q] = 0.5; L.iv[:, q] = 100.0 * iv; L.delta[:, q] = dl; L.gamma[:, q] = gm; L.theta[:, q] = th
    return L


def one(a):
    day, rec = a
    from apex.engine.council import fade, c20_8x
    lv = levels_file()
    fade._FadeMixin.LEVELS = lv
    c20_8x.LEVELS_PATH = lv                              # prior-day levels for the champion, from the history itself
    out = []
    if rec:
        F = FL.load_day(day)
        if F["dte0"]:
            return []
        D = lab1s.session(day, fwd=F["fwd"].copy())
        Lt = FL.live_day(F)
        for b in BOOKS:
            for t in FL.play(F, Lt, b):
                t.update(book=b, src="tape quotes"); out.append(t)
    else:
        D = lab1s.session(day)
    if D is None or D["dte0"]:
        return out
    Lm = model_live(D)
    for b in BOOKS:
        for t in FL.play(D, Lm, b):
            t.update(book=b, src="model chain"); out.append(t)
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    REC = set(FL.days())
    comp = lambda r: 100 * (np.prod(1 + np.array(r) / 100) - 1)
    levels_file()
    if mode == "check":
        jobs = [(d, True) for d in sorted(REC)]
    else:
        have = sorted({os.path.basename(p).split("_")[-1][:10] for p in glob.glob(os.path.join(hist1s.OUT, "fut_*.parquet"))})
        jobs = [(d, False) for d in have if d not in REC] + [(d, True) for d in sorted(REC)]
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, jobs):
            rows += r
    T = pd.DataFrame(rows)
    T.to_parquet(os.path.join(hist1s.OUT, f"classes_{mode}.parquet"))
    pd.set_option("display.width", 230)
    if mode == "check":
        for b in BOOKS:
            a = T[(T.book == b) & (T.src == "tape quotes")]; m = T[(T.book == b) & (T.src == "model chain")]
            da = a.groupby("day").ret.apply(lambda s: comp(s)); dm = m.groupby("day").ret.apply(lambda s: comp(s))
            idx = sorted(set(da.index) | set(dm.index)); da = da.reindex(idx).fillna(0); dm = dm.reindex(idx).fillna(0)
            cr = np.corrcoef(da, dm)[0, 1] if len(idx) > 2 else np.nan
            print(f"{b:12} tape quotes: {len(a):3d} trades {100 * (a.ret > 0).mean() if len(a) else 0:3.0f} % win {a.ret.mean() if len(a) else 0:+6.2f} % | model chain: {len(m):3d} trades {100 * (m.ret > 0).mean() if len(m) else 0:3.0f} % win {m.ret.mean() if len(m) else 0:+6.2f} % | day corr {cr:.2f}")
    else:
        M = T[T.src == "model chain"].copy()
        M["window"] = np.where(M.day >= "2026-10-19", "recorded window", "before it")
        out = []
        for (b, w), g in M.groupby(["book", "window"]):
            dd = g.groupby("day").ret.apply(lambda s: comp(s)); ds = g.groupby("day").ret.sum()
            out.append(dict(book=b, period=w, sessions=g.day.nunique(), trades=len(g), winners=round(100 * (g.ret > 0).mean()), per_trade=round(g.ret.mean(), 2),
                            t=round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1) if len(ds) > 3 else None, days_up=f"{int((dd > 0).sum())}/{len(dd)}", median_day=round(dd.median(), 1), worst=round(dd.min()), best=round(dd.max())))
        n = len([j for j in jobs if not j[1]])
        print(f"broker sessions {n}; real classes on the model chain, normal days")
        print(pd.DataFrame(out).to_string(index=False))
        g = M[(M.book == "c20_9x") & (M.day < "2026-10-19")]
        if len(g):
            print("\nc20_9x before the window, by month:")
            print(g.assign(m=g.day.str[:7]).groupby("m").ret.agg(trades="size", winners=lambda s: round(100 * (s > 0).mean()), per_trade=lambda s: round(s.mean(), 2)).to_string())
