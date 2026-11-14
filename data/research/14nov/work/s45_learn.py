"""Entries learned from the captured data, judged month by month on months the model never saw.

For each test month M: fit on every earlier month (at least two), one model per side (gradient-boosted trees on the
inputs of s44_wxfeat.py; target = the trade's result with the champion's exits, clipped to [-20, +60] %), then trade
M: at each minute, when flat and a side's score is above that side's training quantile q, buy it; the trade's result
and hold come from the label (the same exits), so one position at a time. Compared on the same months with the
champion class (c20_9x, per second), the three fades, and a blind buy at every minute.

    py -3.13 s45_learn.py               all quantiles, both feature sets (all inputs / price-only)
"""
import os, sys, glob
os.environ.setdefault("OMP_NUM_THREADS", "4")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

FE = r"D:\ApexOptions\data\research\hist_wx\feat"
HS = r"D:\ApexOptions\data\research\hist1s"
comp = lambda r: 100 * (np.prod(1 + np.asarray(r, float) / 100) - 1)


def load():
    X = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(os.path.join(FE, "*.parquet")))], ignore_index=True)
    X["month"] = X.day.str[:7]
    return X


def feature_sets(X):
    allf = [c for c in X.columns if c[:2] in ("f_", "c_", "hw", "si", "o_")]
    price = [c for c in allf if c.startswith(("f_", "c_"))]
    return {"all captured inputs": allf, "price of the future only": price}


def trade_day(g, sc_ce, sc_pe, th_ce, th_pe):
    out = []; free = -1
    for n, r in enumerate(g.itertuples()):
        if r.i <= free:
            continue
        a, b = sc_ce[n] - th_ce, sc_pe[n] - th_pe
        side = None
        if a > 0 or b > 0:
            side = "CE" if a >= b else "PE"
        if side:
            y = getattr(r, "y_" + side); h = getattr(r, "y_" + side + "_hold")
            if y == y:
                out.append(dict(day=r.day, minute=r.minute, side=side, ret=float(y)))
                free = r.i + int(h) + 60
    return out


def walk(X, feats, qs=(0.90, 0.95, 0.98), min_months=2):
    months = sorted(X.month.unique())
    res = {q: [] for q in qs}
    imp = []
    for k, M in enumerate(months):
        if k < min_months:
            continue
        tr = X[X.month < M]; te = X[X.month == M]
        models = {}
        for side in ("CE", "PE"):
            t = tr[tr["y_" + side].notna()]
            m = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=200, l2_regularization=1.0)
            m.fit(t[feats], t["y_" + side].clip(-20, 60))
            models[side] = (m, m.predict(t[feats]))
        for q in qs:
            th = {s: np.quantile(models[s][1], q) for s in models}
            for d, g in te.groupby("day"):
                res[q] += trade_day(g, models["CE"][0].predict(g[feats]), models["PE"][0].predict(g[feats]), th["CE"], th["PE"])
        imp.append((M, models))
    return {q: pd.DataFrame(v) for q, v in res.items()}, imp, months[min_months:]


def summary(name, T, days):
    if not len(T):
        return dict(entries=name, trades=0)
    ds = T.groupby("day").ret.sum().reindex(days).fillna(0)
    dd = T.groupby("day").ret.apply(comp)
    mm = T.assign(m=T.day.str[:7]).groupby("m").ret.sum()
    return dict(entries=name, trades=len(T), per_day=round(len(T) / len(days), 1), winners=round(100 * (T.ret > 0).mean()), per_trade=round(T.ret.mean(), 2),
                t=round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1), days_up=f"{int((dd > 0).sum())}/{len(days)}", months_up=f"{int((mm > 0).sum())}/{len(mm)}",
                total=round(T.ret.sum()), mean_log=round(100 * float(np.mean(np.log1p(T.ret / 100))), 2))


if __name__ == "__main__":
    X = load()
    print(f"sessions {X.day.nunique()} ({X.day.min()} to {X.day.max()}), rows {len(X)}, months {X.month.nunique()}")
    print(f"a blind buy at any minute: CE {X.y_CE.mean():+.2f} %, PE {X.y_PE.mean():+.2f} %, winners {100 * ((X.y_CE > 0).mean() + (X.y_PE > 0).mean()) / 2:.0f} %")
    rows = []
    for fsname, feats in feature_sets(X).items():
        R, imp, test_months = walk(X, feats)
        days = sorted(X[X.month.isin(test_months)].day.unique())
        for q, T in R.items():
            rows.append(summary(f"learned on {fsname}, top {100 * (1 - q):.0f} %", T, days))
            T.to_parquet(os.path.join(FE, "..", f"learned_{fsname.split()[0]}_{int(q * 100)}.parquet"))
        if fsname.startswith("all"):
            last_M, models = imp[-1]
            te = X[X.month == last_M]
            from sklearn.inspection import permutation_importance
            groups = {"future (price)": [c for c in feats if c.startswith(("f_", "c_"))], "heavyweights": [c for c in feats if c.startswith("hw")],
                      "sister indices": [c for c in feats if c.startswith("si")], "option chain (IV, OI)": [c for c in feats if c.startswith("o_")]}
            print("\nwhat the models use, per input group (test months, rank skill lost when the group is shuffled):")
            rng = np.random.default_rng(0)
            for k2, (M, models) in enumerate(imp):
                te = X[X.month == M]
                for side in ("CE", "PE"):
                    t = te[te["y_" + side].notna()]
                    if len(t) < 200:
                        continue
                    base = pd.Series(models[side][0].predict(t[feats])).corr(t["y_" + side].reset_index(drop=True), method="spearman")
                    for gname, cols in groups.items():
                        tt = t[feats].copy()
                        for c in cols:
                            tt[c] = rng.permutation(tt[c].to_numpy())
                        drop = base - pd.Series(models[side][0].predict(tt)).corr(t["y_" + side].reset_index(drop=True), method="spearman")
                        rows.append(dict(entries=f"__imp {gname}", trades=M, per_day=side, winners=round(base, 3), per_trade=round(drop, 3)))
    # the same months: the champion class, the fades, one account of both
    K = pd.read_parquet(os.path.join(HS, "classes_run.parquet")); K = K[(K.src == "model chain")]
    from s38_year_summary import one_account
    test_days = sorted(X[X.month.isin(test_months)].day.unique())
    K = K[K.day.isin(test_days)]
    for nm, bs in (("champion class c20_9x", ["c20_9x"]), ("the three fades", ["fade20", "fade60", "orbfade"]), ("champion + three fades", ["c20_9x", "fade20", "fade60", "orbfade"])):
        rows.append(summary(nm + " (same months)", one_account(K[K.book.isin(bs)])[["day", "ret"]], test_days))
    pd.set_option("display.width", 240); pd.set_option("display.max_colwidth", 60)
    R = pd.DataFrame(rows)
    imp_rows = R[R.entries.astype(str).str.startswith("__imp")]
    print(R[~R.entries.astype(str).str.startswith("__imp")].to_string(index=False))
    if len(imp_rows):
        I = imp_rows.assign(group=imp_rows.entries.str[6:], skill=imp_rows.winners, lost=imp_rows.per_trade)
        print("\nrank skill of the models on their test month (mean over months and sides):", round(I.drop_duplicates(["trades", "per_day"]).skill.mean(), 3))
        print(I.groupby("group").lost.agg(["mean", "count"]).round(3).sort_values("mean", ascending=False).to_string())
    print("test months:", test_months)
