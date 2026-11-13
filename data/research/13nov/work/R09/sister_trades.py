import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R09: does a sister-index (BANKNIFTY / FINNIFTY / VIX) confirmation at the trigger separate winners?
Walk-forward: thresholds chosen on 19 Oct - 4 Nov (discovery), scored on 5 - 12 Nov (test).
Samples: (a) the Conductor's account trades (p44_sim + p44_simr), joined to the trade table for the photograph;
(b) the five c20 pool books' own trades; (c) all 107 books (pooled)."""
import json
import numpy as np, pandas as pd
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
OUT = r"D:\ApexOptions\data\research\13nov\work\R09\trades_results.json"
F = ["wx_bn60", "wx_bn300", "wx_fn60", "wx_fn300", "wx_bank_z", "wx_bn_minus_nifty60", "wx_bn_minus_nifty300", "wx_bn_corr30",
     "wx_nifty60", "wx_wmove60_bank", "wx_vix", "wx_vix_chg5", "wx_vix_chg15", "wx_vix_chg30", "wx_vix_chg_open", "wx_vix_day_pos",
     "wx_vix_spot_same5", "wx_adv_bank"]
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
cols = ["day", "book", "t_in", "ret_pct", "dir", "rr"] + F
df = pd.read_parquet(P, columns=cols)
for c in ("wx_vix_spot_same5", "wx_adv_bank"):
    df[c] = pd.to_numeric(df[c].map(lambda v: np.nan if v is None else float(v) if not isinstance(v, str) else np.nan), errors="coerce")
# derived: fn minus nifty (signed), sister agreement count, sister composite
df["d_fn_minus_nifty60"] = df["wx_fn60"] - df["wx_nifty60"]
df["d_sis_agree60"] = (df["wx_bn60"] > 0).astype(float) + (df["wx_fn60"] > 0).astype(float)
df.loc[df["wx_bn60"].isna() | df["wx_fn60"].isna(), "d_sis_agree60"] = np.nan
df["d_sis_agree300"] = (df["wx_bn300"] > 0).astype(float) + (df["wx_fn300"] > 0).astype(float)
df.loc[df["wx_bn300"].isna() | df["wx_fn300"].isna(), "d_sis_agree300"] = np.nan
df["d_sis_min60"] = np.minimum(df["wx_bn60"], df["wx_fn60"])
df["d_rs_bank60_w"] = df["wx_bn60"] - 0.75 * df["wx_nifty60"]          # bank relative strength at the measured beta
FEAT = F[:-2] + ["wx_vix_spot_same5", "wx_adv_bank", "d_fn_minus_nifty60", "d_sis_agree60", "d_sis_agree300", "d_sis_min60", "d_rs_bank60_w"]
EARLY = lambda d: d <= "2026-11-04"
days = sorted(df.day.unique())
R = dict(days=days, coverage={f: round(float(df[f].notna().mean()), 3) for f in FEAT})
# Conductor trades
ct = []
for run in ("p44_sim", "p44_simr"):
    d = json.load(open(rf"D:\ApexOptions\data\replay\batch\{run}\conductor_sim.json"))
    for day, v in d["days"].items():
        if (run == "p44_sim") == (day in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03")):
            continue
        for t in v["trades"]:
            ct.append(dict(day=day, book=t["src"], t_in=float(t["t_in"]), ret_c=float(t["ret_pct"])))
ct = pd.DataFrame(ct)
df["t_in"] = df["t_in"].astype(float)
cj = ct.merge(df, on=["day", "book", "t_in"], how="left")
R["conductor"] = dict(trades=len(ct), joined=int(cj["ret_pct"].notna().sum()), days=int(ct.day.nunique()))
cj["ret"] = cj["ret_c"]


DAYIDX = {d: i for i, d in enumerate(days)}


def score(sub, alld):
    """per-day compounded return (all-in), strike, losing days; days with no trade count as 0 (numpy, fast)."""
    r = sub["ret"].values.astype(float)
    di = np.array([DAYIDX[d] for d in sub["day"].values], int) if len(sub) else np.zeros(0, int)
    out = dict(n=int(len(r)), strike=round(float((r > 0).mean()) * 100, 1) if len(r) else None)
    lg = np.bincount(di, weights=np.log1p(r / 100), minlength=len(days)) if len(r) else np.zeros(len(days))
    sel = [DAYIDX[d] for d in alld]
    dr = np.expm1(lg[sel]) * 100
    out["comp_pct"] = round(float(np.expm1(lg[sel].sum())) * 100, 1)
    out["mean_day_pct"] = round(float(dr.mean()), 2)
    out["losing_days"] = int((dr < 0).sum())
    out["worst_day"] = round(float(dr.min()), 1)
    out["per_day"] = [round(float(x), 1) for x in dr]
    if len(r):
        out["sum_wo_best_trade"] = round(float(r.sum() - r.max()), 1)
        out["comp_wo_best_day"] = round(float(np.expm1(lg[sel].sum() - lg[sel].max())) * 100, 1)
    return out


def auc(x, y):
    m = np.isfinite(x)
    x, y = x[m], y[m]
    if len(x) < 10 or y.all() or (~y).all():
        return None
    r = pd.Series(x).rank().values
    n1 = y.sum(); n0 = len(y) - n1
    return round(float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)), 3)


# 1. separation: AUC (winner vs loser) per period
R["auc"] = {}
for name, sub in (("conductor", cj), ("pool_books", df[df.book.isin(POOL)].assign(ret=lambda x: x.ret_pct)),
                  ("all_books", df.assign(ret=lambda x: x.ret_pct))):
    rows = {}
    for f in FEAT:
        e, l = sub[sub.day.map(EARLY)], sub[~sub.day.map(EARLY)]
        rows[f] = dict(early=auc(e[f].values.astype(float), (e.ret > 0).values),
                       late=auc(l[f].values.astype(float), (l.ret > 0).values),
                       n_early=int(e[f].notna().sum()), n_late=int(l[f].notna().sum()),
                       win_med=round(float(sub.loc[sub.ret > 0, f].median()), 4) if sub[f].notna().any() else None,
                       loss_med=round(float(sub.loc[sub.ret <= 0, f].median()), 4) if sub[f].notna().any() else None)
    R["auc"][name] = rows
# 2. walk-forward filters on the Conductor trades and the pool books
QS = (0.2, 0.33, 0.5)
R["wf"] = {}
for name, sub in (("conductor", cj), ("pool_books", df[df.book.isin(POOL)].assign(ret=lambda x: x.ret_pct))):
    e, l = sub[sub.day.map(EARLY)], sub[~sub.day.map(EARLY)]
    dE = [d for d in days if EARLY(d)]; dL = [d for d in days if not EARLY(d)]
    if name == "pool_books":                    # score books separately and average the compounded return
        base = {b: score(l[l.book == b], dL) for b in POOL}
    else:
        base = score(l, dL); baseE = score(e, dE)
    rows = []
    for f in FEAT:
        x = e[f].astype(float)
        if x.notna().sum() < 20:
            continue
        cuts = sorted({round(float(x.quantile(q)), 4) for q in QS} | ({0.0} if (x < 0).any() and (x > 0).any() else set()))
        for side in ("keep_above", "keep_below"):
            for c in cuts:
                qE = (e[f] > c) if side == "keep_above" else (e[f] < c)
                qL = (l[f] > c) if side == "keep_above" else (l[f] < c)
                qE = qE | e[f].isna(); qL = qL | l[f].isna()           # a missing item never blocks a trade
                if name == "pool_books":
                    sE = {b: score(e[qE & (e.book == b)], dE) for b in POOL}
                    sL = {b: score(l[qL & (l.book == b)], dL) for b in POOL}
                    rows.append(dict(f=f, side=side, cut=c,
                                     disc_comp_mean=round(float(np.mean([v["comp_pct"] for v in sE.values()])), 1),
                                     test_comp_mean=round(float(np.mean([v["comp_pct"] for v in sL.values()])), 1),
                                     test_strike=round(float(np.nanmean([v["strike"] or np.nan for v in sL.values()])), 1),
                                     test_n=int(sum(v["n"] for v in sL.values())),
                                     test_losing_days=int(sum(v["losing_days"] for v in sL.values()))))
                else:
                    sE, sL = score(e[qE], dE), score(l[qL], dL)
                    rows.append(dict(f=f, side=side, cut=c, disc=sE, test=sL))
    R["wf"][name] = dict(base=base, base_disc=baseE if name == "conductor" else None, rows=rows, variants=len(rows))
json.dump(R, open(OUT, "w"), indent=1, default=float)
print("coverage", R["coverage"])
print("conductor", R["conductor"])
for name in R["auc"]:
    print("AUC", name)
    for f, v in R["auc"][name].items():
        print(f"  {f:24s} early {v['early']} late {v['late']} n {v['n_early']}/{v['n_late']} win_med {v['win_med']} loss_med {v['loss_med']}")
c = R["wf"]["conductor"]
print("CONDUCTOR base test", {k: c["base"][k] for k in ("n", "strike", "comp_pct", "losing_days", "worst_day", "per_day")})
print("CONDUCTOR base disc", {k: c["base_disc"][k] for k in ("n", "strike", "comp_pct", "losing_days", "worst_day")})
rows = sorted(c["rows"], key=lambda r: -r["disc"]["comp_pct"])
print("top 15 by DISCOVERY compounded return, with their TEST result (variants tried:", c["variants"], ")")
for r in rows[:15]:
    print(f"  {r['f']:24s} {r['side']:10s} {r['cut']:8} | disc n {r['disc']['n']} st {r['disc']['strike']} comp {r['disc']['comp_pct']} ld {r['disc']['losing_days']}"
          f" | test n {r['test']['n']} st {r['test']['strike']} comp {r['test']['comp_pct']} ld {r['test']['losing_days']} worst {r['test']['worst_day']} {r['test']['per_day']}")
tc = np.array([r["test"]["comp_pct"] for r in c["rows"]])
print("test comp over all variants: median", np.median(tc), "share beating base", float((tc > c["base"]["comp_pct"]).mean()))
p = R["wf"]["pool_books"]
print("POOL base test", {b: (v["n"], v["strike"], v["comp_pct"], v["losing_days"]) for b, v in p["base"].items()},
      "mean comp", np.mean([v["comp_pct"] for v in p["base"].values()]))
rows = sorted(p["rows"], key=lambda r: -r["disc_comp_mean"])
for r in rows[:15]:
    print(f"  {r['f']:24s} {r['side']:10s} {r['cut']:8} disc {r['disc_comp_mean']} test {r['test_comp_mean']} st {r['test_strike']} n {r['test_n']} ld {r['test_losing_days']}")
tc = np.array([r["test_comp_mean"] for r in p["rows"]])
print("pool test comp over variants: median", np.median(tc), "share beating base", float((tc > np.mean([v['comp_pct'] for v in p['base'].values()])).mean()))
