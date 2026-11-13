import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R03 part 2: early-day classifier (declared rule, LODO stump, LODO 3-NN) and the adaptive pool, walk-forward
(leave-one-day-out over 17 days, and the fixed split: discover 19 Oct - 4 Nov, test 5 - 12 Nov)."""
import os, time, json, traceback, itertools
t00 = time.time()
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R03"
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500); pd.set_option("display.max_columns", 60)


def lap(m):
    print(f"[{time.time() - t00:6.1f}s] {m}", flush=True)


DT = pd.read_csv(os.path.join(W, "day_types.csv")).set_index("day")
FE = pd.read_csv(os.path.join(W, "cp_features.csv")); FE["cp"] = FE["cp"].astype(int).map(lambda x: f"{x:04d}")
BD = pd.read_csv(os.path.join(W, "book_day.csv"))
AC = pd.read_csv(os.path.join(W, "book_day_after_cp.csv")); AC["cp"] = AC["cp"].astype(int).map(lambda x: f"{x:04d}")
base = pd.read_pickle(os.path.join(W, "base.pkl"))
base["trig"] = base["trigger_t"].fillna(base["t_in"])
base["trig_hm"] = ((base["trig"] + 19800.0) % 86400.0) / 60.0
base = base.dropna(subset=["entry", "exit", "t_out", "trig"])
fam = BD.groupby("book")["fam"].first()
DAYS = sorted(DT.index)
TEST_FIXED = [d for d in DAYS if d >= "2026-11-05"]
CPS = {"0945": 585, "1015": 615, "1100": 660}
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
lap("loaded")

# ---------------------------------------------------------------- targets
DT["y_trend"] = (DT["shape"].isin(["trend_up", "trend_down"]) | (DT["gapk"] == "gap_go")).astype(int)
FE["y_trend"] = FE["day"].map(DT["y_trend"])
FE["y_rest_trend"] = (FE["rest_D"].abs() >= 0.5).astype(int)
FE["y_cont"] = (np.sign(FE["rest_net_pct"]) == np.sign(FE["mv_pct"])).astype(int)
FE["absD"] = FE["Dc"].abs(); FE["absmv"] = FE["mv_pct"].abs(); FE["absgap"] = FE["gap_pct"].abs()
FE["abs15"] = FE["mv15_pct"].abs(); FE["ext"] = (FE["pos"] - 0.5).abs(); FE["orout"] = FE["or_out"].abs()
FE["wx_vwap_abs"] = FE["wx_vwap_ext_u"].abs() if "wx_vwap_ext_u" in FE else np.nan
FE["declared"] = ((FE["er"] >= 0.30) & (FE["absD"] >= 0.60)).astype(int)        # open-drive / trend-day test, untuned
FEATS = ["er", "absD", "ext", "chop", "rng_pct", "rng_vs_prev", "absmv", "absgap", "abs15", "orout", "wx_er_day",
         "wx_range_vs_norm", "wx_vwap_abs", "wx_vix_chg_open"]
FEATS = [f for f in FEATS if f in FE and FE[f].notna().sum() >= 10]


def stump_fit(X, y):
    """best (feature, threshold, sign) by training accuracy; ties -> fewer errors on the minority class."""
    best = None; tried = 0
    for f in X.columns:
        v = X[f].values.astype(float); ok = np.isfinite(v)
        if ok.sum() < 8:
            continue
        u = np.unique(v[ok]); th = (u[1:] + u[:-1]) / 2
        for t in th:
            for s in (1, -1):
                tried += 1
                p = np.where(ok, (s * (v - t) > 0).astype(int), 0)
                acc = (p == y).mean()
                if best is None or acc > best[0] + 1e-12:
                    best = (acc, f, t, s)
    return best, tried


def stump_pred(m, x):
    acc, f, t, s = m
    v = float(x[f])
    return int(s * (v - t) > 0) if np.isfinite(v) else 0


res = []; preds = {}
for cp in CPS:
    S = FE[FE.cp == cp].set_index("day").loc[DAYS]
    for tgt in ("y_trend", "y_rest_trend", "y_cont"):
        y = S[tgt].values
        maj = max(y.mean(), 1 - y.mean())
        # declared rule
        dec_acc = (S["declared"].values == y).mean()
        # LODO stump
        ps, tried_all, chosen = [], 0, []
        for i, d in enumerate(DAYS):
            tr = [k for k in range(len(DAYS)) if k != i]
            m, tried = stump_fit(S[FEATS].iloc[tr], y[tr])
            tried_all = max(tried_all, tried)
            ps.append(stump_pred(m, S[FEATS].iloc[i])); chosen.append(m[1])
        ps = np.array(ps)
        # LODO 3-NN on standardised core features
        core = [f for f in ["er", "absD", "chop", "rng_pct", "absgap"] if f in S]
        Xc = S[core].values.astype(float)
        pk = []
        for i in range(len(DAYS)):
            tr = [k for k in range(len(DAYS)) if k != i]
            mu = np.nanmean(Xc[tr], 0); sd = np.nanstd(Xc[tr], 0) + 1e-9
            Zt = (Xc[tr] - mu) / sd; zi = (Xc[i] - mu) / sd
            dist = np.nansum((Zt - zi) ** 2, 1)
            nn = np.argsort(dist)[:3]
            pk.append(int(y[tr][nn].mean() > 0.5))
        pk = np.array(pk)
        # fixed split: fit on the discovery days only, predict the test days
        tr = [k for k, d in enumerate(DAYS) if d < "2026-11-05"]
        mf, _ = stump_fit(S[FEATS].iloc[tr], y[tr])
        psf = np.array([stump_pred(mf, S[FEATS].iloc[k]) for k in range(len(DAYS))])
        res.append(dict(cp=cp, target=tgt, base_rate=round(y.mean(), 2), majority_acc=round(maj, 2),
                        declared_acc=round(dec_acc, 2), lodo_stump_acc=round((ps == y).mean(), 2),
                        lodo_3nn_acc=round((pk == y).mean(), 2), stump_variants_per_fold=tried_all,
                        stump_feature_mode=pd.Series(chosen).value_counts().index[0],
                        fixed_test_declared=round((S["declared"].values[-len(TEST_FIXED):] == y[-len(TEST_FIXED):]).mean(), 2),
                        fixed_test_stump=round((psf[-len(TEST_FIXED):] == y[-len(TEST_FIXED):]).mean(), 2),
                        fixed_stump=f"{mf[1]} {'>' if mf[3] > 0 else '<'} {mf[2]:.3f}"))
        preds[(cp, tgt)] = dict(y=y, dec=S["declared"].values, stump=ps, knn=pk, stump_fixed=psf)
R = pd.DataFrame(res)
R.to_csv(os.path.join(W, "classifier_lodo.csv"), index=False)
print("\nCLASSIFIER (17 days, leave-one-day-out)\n", R.to_string())
# per-day view of the declared rule and the stump at each checkpoint
pv = []
for d_i, d in enumerate(DAYS):
    r = {"day": d, "shape": DT.loc[d, "shape"], "gapk": DT.loc[d, "gapk"], "cal": DT.loc[d, "cal"], "y_trend": DT.loc[d, "y_trend"]}
    for cp in CPS:
        r[f"dec{cp}"] = int(preds[(cp, "y_trend")]["dec"][d_i]); r[f"stump{cp}"] = int(preds[(cp, "y_trend")]["stump"][d_i])
        r[f"rest_trend{cp}"] = int(preds[(cp, "y_rest_trend")]["y"][d_i]); r[f"cont{cp}"] = int(preds[(cp, "y_cont")]["y"][d_i])
    pv.append(r)
PV = pd.DataFrame(pv).set_index("day")
PV.to_csv(os.path.join(W, "classifier_per_day.csv"))
print(PV.to_string())
# intraday momentum (Gao et al.): does the rest of the day continue the move so far?
for cp in CPS:
    S = FE[FE.cp == cp]
    print(f"continuation at {cp}: {int(S.y_cont.sum())}/{len(S)} days; mean rest move when continuing vs reversing",
          round(S.loc[S.y_cont == 1, 'rest_net_pct'].abs().mean(), 3), round(S.loc[S.y_cont == 0, 'rest_net_pct'].abs().mean(), 3))
lap("classifier")

# ---------------------------------------------------------------- the account simulator (account_sim without rules)
BYDAY = {d: g for d, g in base.groupby("day")}


def sim_day(day, before, after, cut_hm, prio):
    """before: books allowed for triggers before cut_hm, after: books allowed from cut_hm on; held trades run to exit."""
    g = BYDAY[day]
    m = (g.book.isin(before) & (g.trig_hm < cut_hm)) | (g.book.isin(after) & (g.trig_hm >= cut_hm))
    tr = g[m].assign(_p=lambda x: x.book.map(prio).fillna(999)).sort_values(["trig", "_p"], kind="stable")
    cap = 1e5; held = None; out = []
    for r in tr.itertuples(index=False):
        trig = float(r.trig)
        if held is not None:
            if trig <= held[0] or trig < held[1] or (trig == held[1] and r.book == held[2]):
                continue
            held = None
        px = float(r.entry); lots = int(cap // (px * 65))
        if lots < 1:
            continue
        pnl = (float(r.exit) - px) * lots * 65; cap += pnl
        held = (trig, float(r.t_out), r.book)
        out.append((r.book, trig, float(r.ret_pct), pnl))
    return out, (cap / 1e5 - 1) * 100


P0 = {b: i for i, b in enumerate(POOL)}
cond = {}
for d in DAYS:
    out, ret = sim_day(d, POOL, POOL, 0, P0)
    cond[d] = (out, ret)
print("\nConductor check: total day-% sum", round(sum(v[1] for v in cond.values()), 1),
      "trades", sum(len(v[0]) for v in cond.values()))

# c20 pool by day type (Conductor)
cd = pd.DataFrame([{"day": d, "ret": cond[d][1], "n": len(cond[d][0]), "w": sum(1 for x in cond[d][0] if x[3] > 0)} for d in DAYS]).set_index("day").join(DT[["shape", "gapk", "cal", "y_trend"]])
print("\nCONDUCTOR by shape\n", cd.groupby("shape").agg(days=("ret", "size"), mean=("ret", "mean"), med=("ret", "median"), pos=("ret", lambda s: int((s > 0).sum())), n=("n", "sum"), w=("w", "sum")).to_string())
print(cd.groupby("y_trend").agg(days=("ret", "size"), mean=("ret", "mean"), med=("ret", "median"), pos=("ret", lambda s: int((s > 0).sum())), n=("n", "sum"), w=("w", "sum")).to_string())
print(cd.groupby("cal").agg(days=("ret", "size"), mean=("ret", "mean"), med=("ret", "median"), pos=("ret", lambda s: int((s > 0).sum())), n=("n", "sum"), w=("w", "sum")).to_string())
cd.to_csv(os.path.join(W, "conductor_by_day.csv"))
lap("conductor")

# ---------------------------------------------------------------- adaptive pool
ELIG = sorted(b for b in fam.index if fam[b] not in ("conductor", "control"))
REPS = {}
for b in ELIG:                                    # one representative per family: the book with most trades
    REPS.setdefault(fam[b], []).append(b)
ntr = base.groupby("book").size()
REPS = {f: max(bs, key=lambda b: ntr.get(b, 0)) for f, bs in REPS.items()}
ACp = {cp: AC[AC.cp == cp].pivot(index="book", columns="day", values="ret") for cp in CPS}
mean_rpt = {}                                     # per-trade mean return by book and day, for priority


def train_stats(cp, train_days, typ_of, typ, cands):
    """mean after-checkpoint book-day return, share of positive days, n days, on training days of the same type"""
    ds = [d for d in train_days if typ_of[d] == typ]
    if len(ds) < 3:
        return None, ds
    M = ACp[cp].loc[cands, ds]
    st = pd.DataFrame({"mean": M.mean(1), "pos": (M > 0).mean(1), "nd": len(ds)})
    return st, ds


def rpt(books, days):
    g = base[base.book.isin(books) & base.day.isin(days)]
    return g.groupby("book")["ret_pct"].mean()


def policy(name, cp, test_day, train_days, typ_of):
    cut = CPS[cp]; typ = typ_of[test_day]
    if name == "P0":
        return POOL, POOL, P0
    if name == "P1":                              # c20 gate: flat after the checkpoint if the c20 books lost there on such days
        st, ds = train_stats(cp, train_days, typ_of, typ, POOL)
        if st is None or st["mean"].mean() > 0:
            return POOL, POOL, P0
        return POOL, [], P0
    cands = ELIG if name in ("P2", "P4") else sorted(REPS.values())
    st, ds = train_stats(cp, train_days, typ_of, typ, cands)
    if st is None:
        return POOL, POOL, P0
    q = st[(st["mean"] > 0) & (st["pos"] >= 0.6)].sort_values("mean", ascending=False)
    if name in ("P2", "P3"):
        top = list(q.index[:3])
        if not top:
            return POOL, POOL, P0
        r = rpt(top, train_days).reindex(top).fillna(0).sort_values(ascending=False)
        pr = dict(P0); pr.update({b: 10 + i for i, b in enumerate(r.index)})
        return POOL, top, pr
    if name == "P4":                              # c20 keeps priority; up to two additions that qualify
        add = [b for b in q.index if b not in POOL][:2]
        pr = dict(P0); pr.update({b: 10 + i for i, b in enumerate(add)})
        return POOL, POOL + add, pr


def run(name, cp, scheme, detector):
    rows = []
    for i, d in enumerate(DAYS):
        if scheme == "fixed" and d not in TEST_FIXED:
            continue
        train = [x for x in DAYS if x != d] if scheme == "lodo" else [x for x in DAYS if x < "2026-11-05"]
        typ_of = {x: int(preds[(cp, "y_trend")][detector][j]) for j, x in enumerate(DAYS)}
        if detector == "stump":
            # training days grouped by their true (after-the-day) label; the test day by the stump fitted without it
            typ_of = {x: int(preds[(cp, "y_trend")]["y"][j]) for j, x in enumerate(DAYS)}
            typ_of[d] = int(preds[(cp, "y_trend")]["stump" if scheme == "lodo" else "stump_fixed"][i])
        before, after, pr = policy(name, cp, d, train, typ_of)
        out, ret = sim_day(d, before, after, CPS[cp], pr)
        rows.append(dict(day=d, ret=ret, n=len(out), w=sum(1 for x in out if x[3] > 0), typ=typ_of[d],
                         cond=cond[d][1], added=",".join(b for b in after if b not in POOL), flat_after=len(after) == 0,
                         best_trade=max([x[2] for x in out], default=0.0),
                         took=set((x[0], x[1]) for x in out)))
    return pd.DataFrame(rows)


def score(df):
    r = df["ret"].values; c = df["cond"].values
    tot = r.sum(); n = df.n.sum(); w = df.w.sum()
    bd = r.max() if len(r) else 0
    return dict(days=len(df), strike=round(100 * w / max(n, 1), 1), trades=int(n), sum_day_pct=round(tot, 1),
                cond_sum=round(c.sum(), 1), diff=round(tot - c.sum(), 1), losing_days=int((r < 0).sum()),
                cond_losing=int((c < 0).sum()), worst=round(r.min(), 1), cond_worst=round(c.min(), 1),
                ex_best_day=round(tot - bd, 1), cond_ex_best_day=round(c.sum() - c.max(), 1),
                days_better=int((r > c + 1e-9).sum()), days_worse=int((r < c - 1e-9).sum()))


# top Conductor trades (top 10 % by return) kept?
allc = [(d, x) for d in DAYS for x in cond[d][0]]
thr = np.percentile([x[2] for _, x in allc], 90)
top = [(d, x[0], x[1]) for d, x in allc if x[2] >= thr]
summ = []; per_day = {}
for name in ("P1", "P2", "P3", "P4"):
    for cp in CPS:
        for det in ("dec", "stump"):
            for scheme in ("lodo", "fixed"):
                try:
                    df = run(name, cp, scheme, det)
                    s = score(df)
                    tk = [t for t in top if t[0] in set(df.day)]
                    kept = sum(1 for (d, b, tg) in tk if (b, tg) in df.set_index("day").loc[d, "took"])
                    s.update(policy=name, cp=cp, detector=det, scheme=scheme, top_kept=f"{kept}/{len(tk)}")
                    summ.append(s); per_day[(name, cp, det, scheme)] = df
                except Exception:
                    traceback.print_exc()
SM = pd.DataFrame(summ)
cols = ["policy", "cp", "detector", "scheme", "days", "strike", "trades", "sum_day_pct", "cond_sum", "diff", "losing_days",
        "cond_losing", "worst", "cond_worst", "ex_best_day", "cond_ex_best_day", "days_better", "days_worse", "top_kept"]
SM = SM[cols]
SM.to_csv(os.path.join(W, "adaptive_pool_summary.csv"), index=False)
print("\nADAPTIVE POOL (sum of daily % returns; each day starts at 1 lakh)\n", SM.to_string())
print("variants tried:", len(SM))
# conductor strike for reference
cn = sum(len(cond[d][0]) for d in DAYS); cw = sum(sum(1 for x in cond[d][0] if x[3] > 0) for d in DAYS)
print("Conductor strike all days", round(100 * cw / cn, 1), cn)
ft = [d for d in TEST_FIXED]; fn_ = sum(len(cond[d][0]) for d in ft); fw_ = sum(sum(1 for x in cond[d][0] if x[3] > 0) for d in ft)
print("Conductor strike fixed test days", round(100 * fw_ / max(fn_, 1), 1), fn_)
for k in [("P4", "1015", "dec", "lodo"), ("P4", "1015", "dec", "fixed"), ("P1", "1015", "dec", "lodo"), ("P2", "1015", "dec", "lodo"),
          ("P3", "1015", "dec", "lodo"), ("P4", "1100", "dec", "lodo"), ("P4", "0945", "dec", "lodo")]:
    if k in per_day:
        df = per_day[k].drop(columns=["took"])
        print("\nPER DAY", k, "\n", df.round(1).to_string())
        df.to_csv(os.path.join(W, "per_day_" + "_".join(k) + ".csv"), index=False)
lap("adaptive pool")

# ---------------------------------------------------------------- family results after the checkpoint, by detected type
out = []
for cp in CPS:
    typ = {x: int(preds[(cp, "y_trend")]["dec"][j]) for j, x in enumerate(DAYS)}
    M = ACp[cp].loc[sorted(REPS.values())]
    for b in M.index:
        for t in (0, 1):
            ds = [d for d in DAYS if typ[d] == t]
            v = M.loc[b, ds]
            out.append(dict(cp=cp, fam=fam[b], book=b, detected="trend" if t else "rotation", days=len(ds),
                            mean=round(v.mean(), 1), median=round(v.median(), 1), pos_days=int((v > 0).sum()),
                            early_mean=round(M.loc[b, [d for d in ds if d < "2026-11-05"]].mean(), 1),
                            late_mean=round(M.loc[b, [d for d in ds if d >= "2026-11-05"]].mean(), 1)))
FT = pd.DataFrame(out)
FT.to_csv(os.path.join(W, "family_after_cp_by_detected.csv"), index=False)
print("\nFAMILY REPRESENTATIVES after the checkpoint, by the declared detector\n", FT[FT.cp == "1015"].to_string())
lap("done")
