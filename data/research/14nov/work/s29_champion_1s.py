"""The champion's real per-second pattern on every downloaded session of broker 1-second futures (normal days, model
option, checked 0.98 against real quotes on the recorded sessions), against the recorded window."""
import os, sys, glob
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import lab1s, hist1s

REC = set(FL.days())


def one(day):
    if day in REC:                                      # the recorded sessions: their own tape forward, same model
        D = lab1s.session(day, fwd=FL.load_day(day)["fwd"].copy())
    else:
        D = lab1s.session(day)
    if D is None or D["dte0"]:
        return []
    return lab1s.play(D)


if __name__ == "__main__":
    have = sorted({os.path.basename(p).split("_")[-1][:10] for p in glob.glob(os.path.join(hist1s.OUT, "fut_*.parquet"))})
    days = sorted(set(have) | REC)
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, days):
            rows += r
    T = pd.DataFrame(rows)
    T.to_parquet(os.path.join(hist1s.OUT, "champion_1s.parquet"))
    T["window"] = np.where(T.day >= "2026-10-19", "recorded window (19 Oct to 13 Nov 2026)", "before it (broker 1-second history)")
    pd.set_option("display.width", 230)

    def tab(G, by):
        out = []
        for k, g in G.groupby(by, sort=True):
            dd = g.groupby("day").apply(lambda d: 100 * (np.prod(1 + d.ret.to_numpy() / 100) - 1))
            ds = g.groupby("day").ret.sum()
            t = ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))) if len(ds) > 3 else np.nan
            out.append(dict(key=k, sessions=g.day.nunique(), trades=len(g), per_day=round(len(g) / g.day.nunique(), 1), winners=round(100 * (g.ret > 0).mean()), per_trade=round(g.ret.mean(), 2),
                            t=round(t, 1), days_up=f"{int((dd > 0).sum())}/{len(dd)}", worst_day=round(dd.min()), best_day=round(dd.max()), median_day=round(dd.median(), 1),
                            top3_share=round(100 * g.ret.nlargest(3).sum() / g.ret.sum()) if g.ret.sum() > 0 else None))
        return pd.DataFrame(out).to_string(index=False)
    n_sess = len([d for d in days if d not in REC])
    print(f"sessions downloaded: {n_sess} ({min(have)} to {max(have)}); normal days with at least one trade below")
    print(tab(T, "window"))
    print("\nby month:"); print(tab(T.assign(m=T.day.str[:7]), "m"))
    print("\nby sessions to expiry, before the recorded window:"); B = T[T.day < "2026-10-19"]
    if len(B):
        print(tab(B.assign(d=np.where(B.dte == 1, "1", np.where(B.dte == 2, "2", "3+"))), "d"))
        print("\nby side, before the window:", {s: (len(g), round(100 * (g.ret > 0).mean()), round(g.ret.mean(), 2)) for s, g in B.groupby("side")})
        print("exit reasons, before the window:", B.groupby("why").ret.agg(["size", "mean"]).round(1).to_dict("index"))
