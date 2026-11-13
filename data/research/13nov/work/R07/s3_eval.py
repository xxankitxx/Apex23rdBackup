import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 step 3: (a) do microstructure features predict the next 30 s to 5 min of the Nifty future better than the
Forecast Lab's 46 features (walk-forward over the parts given, in date order)? (b) do they separate winning from
losing trades at the trigger? (c) option-quote lag at entry.
Usage: py -3.13 s3_eval.py <part> <part> <part>   (the feat_<part>.npz files from s2_part.py must exist)"""
import json, os, time
import numpy as np

W = r"D:\ApexOptions\data\research\13nov\work\R07"
DS = r"D:\ApexOptions\data\research\ds_v2"
COL = r"D:\ApexOptions\data\forecast_lab\collect"
t00 = time.time()
parts = sys.argv[1:]
MS = ["spr", "I5", "wmo", "dI5_10", "ofi5", "ofi10", "ofi30", "ofi60", "ofi120", "ndc10", "ndc30", "ndc60", "ndc120",
      "tfi10", "tfi30", "tfi60", "tfi120", "qage", "dage"]
HZ = [30, 60, 120, 300]


def rank(a):
    o = np.argsort(a, kind="stable"); r = np.empty(len(a)); r[o] = np.arange(len(a)); return r


def spear(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 30 or np.std(x[m]) == 0 or np.std(y[m]) == 0:
        return np.nan
    return float(np.corrcoef(rank(x[m]), rank(y[m]))[0, 1])


def top_dir(p, y, q=0.2):
    m = np.isfinite(p) & np.isfinite(y) & (y != 0)
    p, y = p[m], y[m]
    if len(p) < 50:
        return np.nan, 0
    k = max(1, int(q * len(p)))
    idx = np.argsort(-np.abs(p))[:k]
    return float(np.mean(np.sign(p[idx]) == np.sign(y[idx]))), k


import joblib
D = {}
for p in parts:
    f = np.load(os.path.join(W, f"feat_{p}.npz"))
    names = list(f["names"]); X = f["X"].astype(float); Y = f["Y"].astype(float); t = f["t"]
    day = p[:10]
    lab = joblib.load(os.path.join(COL, day + ".joblib"))
    LX = np.asarray(lab["X"], float)
    lt = LX[:, 0]; vref = LX[:, 2]; LF = LX[:, 3:]
    j = np.searchsorted(t, lt, side="right") - 1
    ok = (j >= 0) & (np.abs(t[np.clip(j, 0, None)] - lt) <= 1)
    j = j[ok]
    ms = np.vstack([X[j, names.index(k)] for k in MS]).T
    ys = Y[j]
    sc = np.sqrt(np.maximum(vref[ok], 1e-9)[:, None] * np.array(HZ)[None, :])
    D[p] = dict(t=lt[ok], ms=ms, lab=LF[ok], y=ys, ys=ys / sc, fm=f["fm"], tt=t, X=X, names=names)
    print(p, "rows", int(ok.sum()), "lab feats", LF.shape[1], flush=True)
LABN = ["r5", "r15", "r30", "r60", "r120", "r300", "r600", "r1800", "lv30", "lv120", "lv600", "lv1800", "lviv", "lv120_600",
        "lv600_iv", "jump120", "absr5", "vr", "er300", "slope120", "kf", "imb", "micro", "ofi30", "ofi120", "spr", "vwap",
        "rng", "dhi", "dlo", "div60", "div300", "skew", "dskew300", "dstr60", "dbasis", "hw30", "hw120", "hwlead30",
        "bank120", "up60", "tod", "tod2", "left", "dte", "exp"]          # apex/forecast_lab/brain.py FEATS (copied)
assert len(LABN) == LF.shape[1], (len(LABN), LF.shape)
print("lab feature names", LABN[:6], "...", len(LABN))
out = {"parts": parts, "univariate": {}, "wf": []}
# (a1) univariate Spearman IC, per part, every MS feature and the Lab's flow features
labflow = [k for k in ("imb", "micro", "ofi30", "ofi120", "spr", "r5", "r15", "r30", "r60", "kf", "slope120") if k in LABN]
print("\nUNIVARIATE Spearman IC with the future's move (rows every 5 s)")
hdr = "feature".ljust(14) + "".join(f"{p[5:10]}:{h}".rjust(11) for p in parts for h in HZ)
print(hdr)
for k in MS + ["LAB:" + x for x in labflow]:
    row = []
    for p in parts:
        d = D[p]
        x = d["ms"][:, MS.index(k)] if not k.startswith("LAB:") else d["lab"][:, LABN.index(k[4:])]
        for hi, h in enumerate(HZ):
            row.append(spear(x, d["y"][:, hi]))
    out["univariate"][k] = row
    print(k.ljust(14) + "".join(f"{v:11.3f}" for v in row))


# (a2) walk-forward ridge: train on earlier parts only
def fit(Xtr, ytr, lam=50.0):
    med = np.nanmedian(Xtr, 0); sd = np.nanstd(Xtr, 0); sd[sd == 0] = 1
    Z = np.clip(np.nan_to_num((Xtr - med) / sd), -6, 6)
    m = np.isfinite(ytr)
    Z, yy = Z[m], ytr[m]
    A = Z.T @ Z + lam * np.eye(Z.shape[1]); b = Z.T @ (yy - yy.mean())
    w = np.linalg.solve(A, b)
    return med, sd, w, yy.mean()


def pred(model, X):
    med, sd, w, c = model
    return np.clip(np.nan_to_num((X - med) / sd), -6, 6) @ w + c


sets = {"LAB": lambda d: d["lab"], "MS": lambda d: d["ms"], "LAB+MS": lambda d: np.hstack([d["lab"], d["ms"]])}
print("\nWALK-FORWARD ridge (standardised move): test IC (Pearson) / top-fifth direction hit rate")
for ti in range(1, len(parts)):
    tr, te = parts[:ti], parts[ti]
    for hi, h in enumerate(HZ):
        line = {"train": tr, "test": te, "h": h}
        for nm, fx in sets.items():
            Xtr = np.vstack([fx(D[p]) for p in tr]); ytr = np.concatenate([D[p]["ys"][:, hi] for p in tr])
            mdl = fit(Xtr, ytr)
            pt = pred(mdl, fx(D[te])); yt = D[te]["ys"][:, hi]
            m = np.isfinite(yt)
            ic = float(np.corrcoef(pt[m], yt[m])[0, 1]); td, k = top_dir(pt, yt)
            line[nm] = dict(ic=round(ic, 4), top_dir=round(td, 4), n=int(m.sum()), top_n=k)
        out["wf"].append(line)
        print(f"train {','.join(x[5:10] for x in tr)} test {te[5:10]} h={h:4d}  " +
              "  ".join(f"{nm}: ic {line[nm]['ic']:+.3f} top {line[nm]['top_dir']:.3f}" for nm in sets))
# (a3) empirical micro-price (Stoikov 2018 idea): expected 30-s / 60-s mid change by (imbalance decile, spread state),
# learnt on the earlier parts, applied to the next
print("\nEMPIRICAL MICRO-PRICE G(I5 decile, spread state) learnt on earlier parts")
for ti in range(1, len(parts)):
    tr, te = parts[:ti], parts[ti]
    I_tr = np.concatenate([D[p]["ms"][:, MS.index("I5")] for p in tr])
    S_tr = np.concatenate([D[p]["ms"][:, MS.index("spr")] for p in tr])
    qs = np.nanpercentile(I_tr, np.arange(10, 100, 10)); s_med = np.nanmedian(S_tr)
    for hi, h in enumerate(HZ[:2]):
        y_tr = np.concatenate([D[p]["y"][:, hi] for p in tr])
        b_tr = np.searchsorted(qs, I_tr) * 2 + (S_tr > s_med)
        G = np.array([np.nanmean(y_tr[b_tr == b]) if (b_tr == b).sum() > 20 else 0.0 for b in range(20)])
        d = D[te]; I_te = d["ms"][:, MS.index("I5")]; S_te = d["ms"][:, MS.index("spr")]
        b_te = np.searchsorted(qs, I_te) * 2 + (S_te > s_med)
        g = G[b_te]; yt = d["y"][:, hi]
        m = np.isfinite(yt) & np.isfinite(I_te)
        td, k = top_dir(g[m], yt[m])
        print(f"train {','.join(x[5:10] for x in tr)} test {te[5:10]} h={h}: IC {spear(g[m], yt[m]):+.3f}, top-fifth dir {td:.3f} (n {k}); "
              f"G by decile (narrow spread) {np.round(G[0::2], 2).tolist()}")
json.dump(out, open(os.path.join(W, "s3_forecast.json"), "w"), indent=1, default=float)

# (b) trades at the trigger
import pandas as pd
tr = pd.read_parquet(os.path.join(W, "flowcols.parquet"),
                     columns=["day", "book", "t_in", "trigger_t", "ret_pct", "rr", "strike", "entry", "entry_bid", "entry_ask"])
dl = pd.read_parquet(r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet", columns=["delta_in"])
tr["delta_in"] = dl["delta_in"].values
tr["day"] = tr["day"].astype(str)
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
rows = []
for p in parts:
    day = p[:10]
    g = tr[tr.day == day].copy()
    if g.empty:
        continue
    d = D[p]; t = d["tt"]; X = d["X"]; names = d["names"]; fm = d["fm"]
    trig = g["trigger_t"].fillna(g["t_in"]).values.astype(float)
    tin = g["t_in"].values.astype(float)
    j = np.searchsorted(t, trig, side="right") - 1
    okj = (j >= 0) & (np.abs(t[np.clip(j, 0, None)] - trig) <= 3)
    j = np.clip(j, 0, None)
    sg = np.where(g["rr"].values == "CE", 1.0, -1.0)
    for k in ["I5", "wmo", "dI5_10", "ofi5", "ofi10", "ofi30", "ofi60", "ofi120", "ndc10", "ndc30", "ndc60", "tfi10", "tfi30", "tfi60", "tfi120", "r10", "r30", "r60"]:
        g["ms_" + k] = np.where(okj, X[j, names.index(k)] * sg, np.nan)
    for k in ["spr", "qage", "dage", "rv600"]:
        g["ms_" + k] = np.where(okj, X[j, names.index(k)], np.nan)
    # what the future did after the fill, in the trade's direction
    jin = np.clip(np.searchsorted(t, tin, side="right") - 1, 0, None)
    for h in (30, 60, 300):
        jh = np.clip(np.searchsorted(t, tin + h, side="right") - 1, 0, None)
        g[f"fut_after{h}"] = (fm[jh] - fm[jin]) * sg
    # (c) the option quote at entry: its age, its spread and how far it lags the future over the last 5 s
    z = np.load(os.path.join(DS, p + ".npz"))
    K = list(z["strikes"].astype(int)); nk = len(K)
    o = z["opt"][:, :nk]; oa = z["age"][:, :nk]
    kk = np.array([K.index(int(s)) if int(s) in K else -1 for s in g["strike"].values])
    side = np.where(g["rr"].values == "CE", 0, 1)
    j5 = np.clip(np.searchsorted(t, tin - 5, side="right") - 1, 0, None)
    okk = kk >= 0
    kk2 = np.where(okk, kk, 0)
    mid_in = 0.5 * (o[jin, kk2, side, 0] + o[jin, kk2, side, 1]).astype(float)
    mid_5 = 0.5 * (o[j5, kk2, side, 0] + o[j5, kk2, side, 1]).astype(float)
    age_in = oa[jin, kk2, side].astype(float)
    dfut5 = (fm[jin] - fm[j5]) * sg
    dl_ = np.abs(g["delta_in"].values.astype(float))
    g["opt_age_in"] = np.where(okk, age_in, np.nan)
    g["opt_lag5_pct"] = np.where(okk, 100 * (dl_ * dfut5 - (mid_in - mid_5)) / g["entry"].values, np.nan)
    g["dfut5_with"] = dfut5
    g["opt_spr_pct"] = 100 * (g["entry_ask"] - g["entry_bid"]) / ((g["entry_ask"] + g["entry_bid"]) / 2)
    g["ask_vs_mid_ds_pct"] = np.where(okk, 100 * (g["entry"].values - mid_in) / mid_in, np.nan)
    rows.append(g)
G = pd.concat(rows)
G.to_parquet(os.path.join(W, "s3_trades_ms.parquet"))
feats = [c for c in G.columns if c.startswith("ms_")] + ["opt_age_in", "opt_lag5_pct", "dfut5_with", "opt_spr_pct", "ask_vs_mid_ds_pct"]
print("\nTRADES at the trigger (signed: + = with the trade). Spearman with ret_pct per day; all books, then the pool books")
for uni, GG in (("all", G), ("pool", G[G.book.isin(POOL)])):
    print(f"\n[{uni}] n by day:", GG.groupby("day").size().to_dict())
    print("feature".ljust(18) + "".join(d[5:].rjust(9) for d in sorted(GG.day.unique())) + "  | tercile win%: low/mid/high (all days)")
    for f in feats:
        line = f.ljust(18)
        for dday in sorted(GG.day.unique()):
            q = GG[GG.day == dday]
            line += f"{spear(q[f].values.astype(float), q['ret_pct'].values.astype(float)):9.3f}"
        x = GG[f].values.astype(float); y = GG["ret_pct"].values
        m = np.isfinite(x)
        if m.sum() > 30:
            qq = np.nanpercentile(x[m], [33.3, 66.7])
            b = np.digitize(x[m], qq)
            line += "  | " + " / ".join(f"{100*np.mean(y[m][b==i]>0):.0f}%({np.mean(y[m][b==i]):+.1f})" for i in range(3))
        print(line)
    for h in (30, 60, 300):
        print(f"  future after the fill +{h}s (with the trade): median {GG[f'fut_after{h}'].median():+.2f} pts, share > 0 {np.mean(GG[f'fut_after{h}']>0):.2f}")
print("\nOPTION AT ENTRY (all books): age s p50/p90/p99", np.nanpercentile(G.opt_age_in, [50, 90, 99]).round(2).tolist(),
      " lag5 % of premium p10/p50/p90", np.nanpercentile(G.opt_lag5_pct, [10, 50, 90]).round(2).tolist())
print("done", round(time.time() - t00, 1))
