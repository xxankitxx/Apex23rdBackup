"""What is learnable? Leave-one-day-out: train on the other days, score the held-out day, then TRADE the held-out day
from the scores (one position at a time, champion exits). Prints rank skill, the decile table and the traded result."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "4")
sys.path.insert(0, r"D:\ApexOptions")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from apex import fastlab as FL
W = r"D:\ApexOptions\data\research\14nov\work"
M = pd.read_parquet(W + r"\map_all.parquet")
DIRL = [c for c in M.columns if c.startswith(("mom", "brk", "pos", "ser", "nf", "hw", "brd", "bank_x", "sfb", "sf_gap", "bn", "fin", "sis_gap", "imb"))] + ["day_pos", "mv_open", "twap_d", "vwap_d"]
NOND = ["tod", "rng300", "rng600", "rng1200", "rng3600", "day_rng", "rv60", "rv300", "rv900", "rv1800", "er300", "er1200", "er3600", "squeeze", "vr60",
        "vix", "vix300", "straddle", "iv", "iv300", "iv_rich", "em15", "rent", "spr", "e"]
which = sys.argv[1] if len(sys.argv) > 1 else "normal"
G = M[M.dte0 == (which == "expiry")].copy()
X = pd.DataFrame({("s_" + c): G[c] * G.sg for c in DIRL})
for c in NOND:
    X[c] = G[c]
X["sg"] = G.sg
# scale-free versions: moves in units of the implied 15-minute move
for c in ("mom300", "mom1200", "mom3600", "brk1200", "twap_d", "vwap_d", "mv_open", "hw300", "hw1200"):
    X["z_" + c] = G[c] * G.sg / G.em15
y = G.ret.clip(-20, 60)
days = sorted(G.day.unique())
t0 = time.time()
pred = pd.Series(np.nan, index=G.index)
thr = {}
for d in days:
    tr = G.day != d
    m = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=150, min_samples_leaf=300, l2_regularization=1.0)
    m.fit(X[tr], y[tr])
    pred[~tr] = m.predict(X[~tr])
    ptr = m.predict(X[tr])
    thr[d] = {q: float(np.quantile(ptr, q)) for q in (0.80, 0.90, 0.95, 0.98)}
G["pred"] = pred
print(which, "days", len(days), "fit", round(time.time() - t0, 1), "s")
ic = G.groupby("day").apply(lambda g: g.pred.corr(g.ret, method="spearman"))
print("rank skill per held-out day:", " ".join(f"{d[5:]}:{v:+.2f}" for d, v in ic.items()), "| mean", round(ic.mean(), 3), "positive days", int((ic > 0).sum()), "/", len(ic))
G["dec"] = G.groupby("day").pred.transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False))
print("held-out decile of the score -> actual result of a buy there")
print(G.groupby("dec").agg(n=("ret", "size"), win=("ret", lambda r: round(100 * (r > 0).mean(), 1)), mean=("ret", lambda r: round(r.mean(), 2))).T.to_string())
# trade the held-out day from the scores
for q in (0.90, 0.95, 0.98):
    allt = []
    for d in days:
        D = FL.load_day(d)
        g = G[(G.day == d) & (G.pred >= thr[d][q])].sort_values(["i", "pred"], ascending=[True, False]).drop_duplicates("i")
        allt += FL.run(D, [(int(r.i), r.side, "ml") for r in g.itertuples()])
    T = pd.DataFrame(allt)
    if not len(T):
        print("q", q, "no trades"); continue
    bd = T.groupby("day").ret.agg(["size", "sum", lambda r: (r > 0).sum()])
    print(f"score >= training {int(q * 100)}th pct: trades {len(T)} win % {100 * (T.ret > 0).mean():.1f} mean {T.ret.mean():+.2f} sum {T.ret.sum():+.0f} | per day:",
          " ".join(f"{d[5:]}:{int(r['size'])}/{r['sum']:+.0f}" for d, r in bd.iterrows()))
G[["day", "i", "side", "ret", "pred"]].to_parquet(W + rf"\pred_{which}.parquet")
# which inputs matter (permutation on the last fold is noisy; use a simple one-tree-depth scan instead)
imp = []
for c in X.columns:
    v = X[c]
    ok = v.notna()
    if ok.sum() < 1000:
        continue
    qs = v[ok].quantile([0.1, 0.9])
    lo, hi = G.ret[ok & (v <= qs.iloc[0])], G.ret[ok & (v >= qs.iloc[1])]
    dl = G[ok & (v <= qs.iloc[0])].groupby("day").ret.mean(); dh = G[ok & (v >= qs.iloc[1])].groupby("day").ret.mean()
    dd = (dh - dl).dropna()
    imp.append((c, round(lo.mean(), 2), round(hi.mean(), 2), round(100 * (lo > 0).mean(), 1), round(100 * (hi > 0).mean(), 1), int((dd > 0).sum()), len(dd)))
I = pd.DataFrame(imp, columns=["input", "mean_low10", "mean_high10", "win_low", "win_high", "days_high_beats_low", "days"])
I["spread"] = I.mean_high10 - I.mean_low10
print(I.reindex(I.spread.abs().sort_values(ascending=False).index).head(28).to_string(index=False))
