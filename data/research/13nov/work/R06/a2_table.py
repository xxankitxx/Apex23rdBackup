"""R06: greeks / IV / strike / expiry buckets on the trade table, IV drift, and walk-forward threshold tests.
Read-only: reads t_small.parquet + t_extra.parquet (extracted from trades_all_books.parquet) and the Conductor sims."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json
import numpy as np, pandas as pd
pd.set_option("display.width", 250)
W = r"D:\ApexOptions\data\research\13nov\work\R06"
B = r"D:\ApexOptions\data\replay\batch"
SIMR = {"2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03"}
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
CAL = 375.0 / 1440.0
a = pd.read_parquet(W + r"\t_small.parquet")
x = pd.read_parquet(W + r"\t_extra.parquet")
assert (a["day"].values == x["day"].values).all() and (a["book"].values == x["book"].values).all()
x = x.drop(columns=[c for c in x.columns if c in a.columns])
df = pd.concat([a, x], axis=1)
df["r"] = df["ret_pct"] / 100.0
df["lr"] = np.log1p(df["r"].clip(lower=-0.99))
df["adelta"] = df["delta_in"].abs()
df["dtype"] = np.where(df["wx_expiry_day"] == True, "expiry", np.where(df["wx_day_before_expiry"] == True, "day_before", "normal"))
df["late"] = df["day"] >= "2026-11-05"
df["ivchg"] = df["iv_out"] - df["iv_in"]
df["hold_min"] = df["hold_s"] / 60.0
df["spread"] = df["entry_ask"] - df["entry_bid"]
df["th_kit"] = df["wx_theta_min"].abs()
df["th_cal"] = df["th_kit"] * CAL
df["rms1"] = 1.2533 * df["wx_speed15"]                      # Gaussian: RMS = mean|x| * sqrt(pi/2)
df["rent_kit"] = 0.5 * df["wx_gamma"] * df["rms1"] ** 2 / df["th_kit"]
df["rent_cal"] = df["rent_kit"] / CAL
df["be_gamma_kit"] = np.sqrt(2 * df["th_kit"] / df["wx_gamma"])  # per-minute RMS move that pays the kit theta
df["be_gamma_cal"] = np.sqrt(2 * df["th_cal"] / df["wx_gamma"])
df["theta_paid_kit_pct"] = 100 * df["th_kit"] * df["hold_min"] / df["entry"]
df["theta_paid_cal_pct"] = 100 * df["th_cal"] * df["hold_min"] / df["entry"]
df["spread_pct_entry"] = 100 * df["spread"] / df["entry"]
df["fmove_with"] = (df["fut_out"] - df["fut_in"]) * np.where(df["rr"] == "CE", 1, -1)
df["gear_pct_pt"] = 100 * df["adelta"] / df["entry"]


def summ(g):
    r = g["ret_pct"]
    return pd.Series(dict(n=len(r), win=round(100 * (r > 0).mean(), 1), mean=round(r.mean(), 2), med=round(r.median(), 2),
                          comp=round(100 * (np.exp(g["lr"].sum()) - 1), 1), days=g["day"].nunique()))


def bucket(d, col, bins, label=None):
    c = pd.cut(d[col], bins)
    out = d.groupby([c], observed=True).apply(summ, include_groups=False)
    print(f"\n-- {label or col} --")
    print(out.to_string())


P = df[df.book.isin(POOL)].copy()
print("pool trades", len(P), "all", len(df))
print("\n== 1. greeks at entry, pool books, medians by day type ==")
cols = ["entry", "adelta", "wx_gamma", "th_kit", "th_cal", "wx_theta_be", "wx_speed15", "wx_theta_ratio", "rent_kit", "rent_cal",
        "be_gamma_kit", "be_gamma_cal", "spread", "spread_pct_entry", "wx_spread_be_pts", "hold_min", "theta_paid_kit_pct",
        "theta_paid_cal_pct", "iv_in", "ivchg", "wx_moneyness_pts", "gear_pct_pt", "fmove_with"]
print(P.groupby("dtype")[cols].median().T.round(4).to_string())
print(P.groupby("dtype").apply(summ, include_groups=False).to_string())

print("\n== 2. buckets, pool books (5 books pooled; trades overlap across books) ==")
bucket(P, "adelta", [0, 0.55, 0.6, 0.65, 0.7, 0.8, 1.0], "|delta| at entry")
bucket(P, "wx_moneyness_pts", [-200, 0, 25, 50, 75, 100, 400], "ITM depth (fwd pts)")
bucket(P, "iv_in", [0, 9, 10, 11, 12, 13, 15, 100], "IV at entry (vol pts)")
bucket(P, "wx_iv_vs_med", [-20, -1, -0.3, 0.3, 1, 3, 50], "IV vs day median at entry")
bucket(P, "ivchg", [-50, -2, -1, -0.3, 0.3, 1, 2, 50], "IV change entry->exit (ex post)")
bucket(P, "wx_theta_ratio", [0, 0.01, 0.02, 0.04, 0.08, 10], "theta_ratio = theta_be/speed15")
bucket(P, "rent_cal", [0, 1, 2, 4, 8, 1000], "gamma rent (calendar theta)")
bucket(P, "wx_e_iv_rv", [0, 0.6, 0.8, 1.0, 1.25, 1.6, 100], "implied/realised (e_iv_rv)")
bucket(P, "wx_opt_iv_chg5", [-20, -0.5, -0.1, 0.1, 0.5, 20], "own IV change last 5 min")
bucket(P, "wx_atm_iv_chg5", [-20, -0.5, -0.1, 0.1, 0.5, 20], "ATM IV change last 5 min")
bucket(P, "dte_in", [-1, 0, 1, 2, 3, 4, 8], "DTE")
bucket(P, "spread_pct_entry", [0, 0.25, 0.5, 1, 2, 100], "spread % of entry")
print("\n-- by side --")
print(P.groupby("rr").apply(summ, include_groups=False).to_string())
print(P.groupby(["dtype", "rr"]).apply(summ, include_groups=False).to_string())
print("\n-- by side, IV change entry->exit (median) and its premium effect (vega x dIV / entry) --")
P["vega_eff_pct"] = 100 * P["wx_vega"] * P["ivchg"] / P["entry"]
print(P.groupby(["dtype", "rr"])[["ivchg", "vega_eff_pct", "ret_pct", "fmove_with", "hold_min"]].median().round(3).to_string())

print("\n== 3. IV drift on held trades, ALL books: ivchg ~ a + b*hold_min + c*fmove (signed for the option) ==")
for dt in ("normal", "day_before", "expiry"):
    for rr in ("CE", "PE"):
        g = df[(df.dtype == dt) & (df.rr == rr)].dropna(subset=["ivchg", "hold_min", "fut_out", "fut_in"])
        g = g[(g.hold_min > 1) & (g.ivchg.abs() < 20)]
        if len(g) < 30:
            continue
        dF = (g["fut_out"] - g["fut_in"]).values
        X = np.c_[np.ones(len(g)), g["hold_min"].values, dF]
        coef, *_ = np.linalg.lstsq(X, g["ivchg"].values, rcond=None)
        res = g["ivchg"].values - X @ coef
        se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * res.var())
        print(f"{dt:10s} {rr}: n={len(g):5d} a={coef[0]:+.3f} b(per hour)={60 * coef[1]:+.3f} (se {60 * se[1]:.3f}) "
              f"c(per 100 fut pts)={100 * coef[2]:+.3f} (se {100 * se[2]:.3f}); days={g.day.nunique()}")

print("\n== 4. all 107 books: |delta| and ITM depth (wider sample) ==")
bucket(df, "adelta", [0, 0.55, 0.6, 0.65, 0.7, 0.8, 1.0], "ALL books |delta|")
for dt in ("normal", "day_before", "expiry"):
    bucket(df[df.dtype == dt], "adelta", [0, 0.55, 0.6, 0.65, 0.7, 0.8, 1.0], f"ALL books |delta|, {dt}")
bucket(df, "wx_moneyness_pts", [-300, -25, 0, 25, 50, 100, 150, 600], "ALL books ITM depth")
bucket(df, "iv_in", [0, 9, 10, 11, 12, 13, 15, 100], "ALL books IV level")
bucket(df, "ivchg", [-50, -2, -1, -0.3, 0.3, 1, 2, 50], "ALL books IV change (ex post)")

# ---------------------------------------------------------------- Conductor trades joined to the weather
ct = []
for f, days in ((B + r"\p44_sim\conductor_sim.json", None), (B + r"\p44_simr\conductor_sim.json", SIMR)):
    d = json.load(open(f, encoding="utf-8"))["days"]
    for day, v in d.items():
        if (days is None and day in SIMR) or (days is not None and day not in days):
            continue
        for t in v.get("trades") or []:
            ct.append(dict(day=day, book=t["src"], t_in=float(t["t_in"]), strike=float(t["strike"]), rr=t["rr"],
                           c_ret=t["ret_pct"], c_entry=t["entry"]))
ct = pd.DataFrame(ct)
m = ct.merge(df.drop_duplicates(["day", "book", "t_in", "strike", "rr"]), on=["day", "book", "t_in", "strike", "rr"], how="left")
print("\n== 5. Conductor trades", len(ct), "joined", int(m["ret_pct"].notna().sum()), "ret match",
      float((m["ret_pct"] - m["c_ret"]).abs().lt(0.01).mean()))
m["ret_pct"] = m["c_ret"]
m["r"] = m["ret_pct"] / 100
m["lr"] = np.log1p(m["r"])
print(m.groupby("dtype").apply(summ, include_groups=False).to_string())
bucket(m, "adelta", [0, 0.55, 0.6, 0.65, 0.7, 1.0], "Conductor |delta|")
bucket(m, "iv_in", [0, 10, 11, 12, 13, 100], "Conductor IV")
bucket(m, "wx_iv_vs_med", [-20, -0.3, 0.3, 1, 50], "Conductor IV vs median")
bucket(m, "wx_theta_ratio", [0, 0.01, 0.02, 0.04, 10], "Conductor theta_ratio")
bucket(m, "ivchg", [-50, -1, -0.3, 0.3, 1, 50], "Conductor IV change (ex post)")
m.to_csv(W + r"\conductor_joined.csv", index=False)

# ---------------------------------------------------------------- walk-forward threshold search
FEATS = ["adelta", "wx_moneyness_pts", "iv_in", "wx_iv_vs_med", "wx_theta_ratio", "rent_cal", "wx_e_iv_rv", "wx_opt_iv_chg5",
         "wx_atm_iv_chg5", "wx_opt_iv_chg1", "wx_atm_iv_chg1", "wx_theta_be", "wx_speed15", "wx_gamma_theta", "wx_vega",
         "wx_extrinsic_pct", "wx_strad_excess", "wx_strad_vs_open_pct", "wx_skew_atm", "wx_term_atm", "wx_atm_iv_day_pos",
         "wx_iv_spot_corr15", "wx_range_vs_strad", "wx_day_move_vs_strad", "wx_po_up15", "wx_vanna", "wx_charm_min",
         "spread_pct_entry", "gear_pct_pt", "wx_vix"]


def day_comp(g):
    return g.groupby("day")["lr"].sum()


def wf(d, label, min_keep=0.6):
    E, L = d[~d.late], d[d.late]
    rows = []
    tried = 0
    for f in FEATS:
        if f not in d or E[f].notna().mean() < 0.8:
            continue
        qs = np.nanquantile(E[f], np.linspace(0.1, 0.9, 9))
        best = None
        for th in np.unique(qs):
            for side in ("ge", "lt"):
                tried += 1
                keep = (E[f] >= th) if side == "ge" else (E[f] < th)
                keep = keep & E[f].notna() | E[f].isna()
                if keep.mean() < min_keep:
                    continue
                score = E.loc[keep, "lr"].sum() - E["lr"].sum()        # log-growth added on discovery days
                if best is None or score > best[0]:
                    best = (score, th, side)
        if best is None:
            continue
        sc, th, side = best
        kl = ((L[f] >= th) if side == "ge" else (L[f] < th)) & L[f].notna() | L[f].isna()
        dk = day_comp(L[kl]).reindex(sorted(L.day.unique())).fillna(0)
        da = day_comp(L)
        rows.append(dict(feat=f, side=side, th=round(float(th), 4), disc_gain_lr=round(sc, 3),
                         test_n_all=len(L), test_n_kept=int(kl.sum()),
                         test_win_all=round(100 * (L.ret_pct > 0).mean(), 1), test_win_kept=round(100 * (L[kl].ret_pct > 0).mean(), 1),
                         test_lr_all=round(L.lr.sum(), 3), test_lr_kept=round(L[kl].lr.sum(), 3),
                         test_days_better=int((dk > da + 1e-9).sum()), test_days_worse=int((dk < da - 1e-9).sum()),
                         test_loss_days_kept=int((dk < 0).sum()), test_loss_days_all=int((da < 0).sum())))
    out = pd.DataFrame(rows).sort_values("disc_gain_lr", ascending=False)
    print(f"\n== 6. walk-forward thresholds: {label} (discover 19 Oct-4 Nov, test 5-12 Nov); variants tried {tried} ==")
    print(out.to_string(index=False))
    return out


wf(m, "Conductor trades (drop = stay flat; approximation)")
wf(P[P.book == "c20_9y"], "c20_9y trades")
wf(P, "5 pool books pooled")
P.to_parquet(W + r"\pool_trades.parquet")
