"""R06 a5: the honest break-even. Expected premium change per minute for a long option held a short time:
    E[dV]/dt = |delta|*mu + 0.5*gamma*(sig_m^2 + mu^2*h) - theta_cal
mu = signed drift in the trade direction (pts/min), sig_m = realised per-minute sd of the underlying (pts).
Compares it with the weather's theta_be (= |theta_kit| / |delta|, ignores gamma, uses kit theta = 3.84 x calendar).
Walk-forward: discover 19 Oct - 4 Nov, test 5 - 12 Nov. Also: can the IV change after entry be predicted ex ante?"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
pd.set_option("display.width", 250)
W = r"D:\ApexOptions\data\research\13nov\work\R06"
P_ = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
CAL = 375.0 / 1440.0
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
a = pd.read_parquet(W + r"\t_small.parquet")
x = pd.read_parquet(W + r"\t_extra.parquet")
x = x.drop(columns=[c for c in x.columns if c in a.columns])
more = pd.read_parquet(P_, columns=["wx_mv120", "wx_mv300", "wx_accel15", "wx_rv15_spot"])
more = more.drop(columns=[c for c in more.columns if c in a.columns or c in x.columns])
df = pd.concat([a, x, more], axis=1)
df["lr"] = np.log1p((df["ret_pct"] / 100).clip(lower=-0.99))
df["adelta"] = df["delta_in"].abs()
df["dtype"] = np.where(df["wx_expiry_day"] == True, "expiry", np.where(df["wx_day_before_expiry"] == True, "day_before", "normal"))
df["late"] = df["day"] >= "2026-11-05"
df["ivchg"] = df["iv_out"] - df["iv_in"]
F = df["fut_in"].where(df["fut_in"] > 0, df["spot_in"])
th_kit = df["wx_theta_min"].abs()
th_cal = th_kit * CAL
g = df["wx_gamma"].fillna(0)
ANN = (252 * 22500) ** 0.5 * 100
sig_m = F * (df["wx_rv5"] / ANN) * np.sqrt(60)          # per-minute sd of the underlying, pts (trading-time convention)
sig_iv_m = F * (df["iv_in"] / 100) * np.sqrt(1 / (365 * 1440))    # implied per calendar minute
mu5 = df["wx_mv300"] / 5.0                                # pts/min in the trade direction (mv is signed by direction)
mu1 = df["wx_mv60"] / 1.0
for nm, mu in (("5", mu5), ("1", mu1)):
    df[f"edge{nm}_cal"] = 100 * (df["adelta"] * mu + 0.5 * g * sig_m ** 2 - th_cal) / df["entry"]   # % of premium per min
    df[f"edge{nm}_kit"] = 100 * (df["adelta"] * mu + 0.5 * g * sig_m ** 2 - th_kit) / df["entry"]
df["gcredit_cal"] = 0.5 * g * sig_m ** 2 / th_cal                 # gamma rent: >1 = noise alone pays the calendar theta
df["be_drift_honest"] = (th_cal - 0.5 * g * sig_m ** 2).clip(lower=0) / df["adelta"]
df["be_drift_kit"] = th_kit / df["adelta"]                       # = wx_theta_be
df["rv_iv_m"] = sig_m / sig_iv_m                                  # realised / implied, same per-minute units
df["drift_ratio5"] = mu5 / df["be_drift_kit"]

P = df[df.book.isin(POOL)]
print("== medians by day type, pool trades ==")
cols = ["wx_theta_be", "be_drift_kit", "be_drift_honest", "wx_speed15", "wx_mv300", "gcredit_cal", "rv_iv_m", "edge5_cal",
        "edge5_kit", "edge1_cal", "wx_rv5", "iv_in"]
print(P.groupby("dtype")[cols].median().T.round(4).to_string())
chk = (df["be_drift_kit"] - df["wx_theta_be"]).abs()
print("theta_be reproduces |theta_min|/|delta|: share within 0.01 =", round(float((chk < 0.01).mean()), 3))


def summ(gr):
    r = gr["ret_pct"]
    return pd.Series(dict(n=len(r), win=round(100 * (r > 0).mean(), 1), mean=round(r.mean(), 2), med=round(r.median(), 2),
                          days=gr["day"].nunique()))


def qbuck(d, col, label, q=5, by_late=True):
    E = d[~d.late]
    edges = np.unique(np.nanquantile(E[col], np.linspace(0, 1, q + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    c = pd.cut(d[col], edges)
    print(f"\n-- {label}: quintiles set on discovery days; discovery | test --")
    out = d.groupby([c, d.late], observed=True).apply(summ, include_groups=False).unstack("late")
    print(out.to_string())


for col, lab in (("edge5_cal", "edge rate, 5-min drift, calendar theta (% premium/min)"),
                 ("edge1_cal", "edge rate, 1-min drift"),
                 ("gcredit_cal", "gamma credit / calendar theta"),
                 ("rv_iv_m", "realised/implied per-minute vol"),
                 ("drift_ratio5", "5-min drift / theta_be (kit)"),
                 ("wx_theta_ratio", "weather theta_ratio (theta_be / speed15)")):
    qbuck(P, col, "POOL " + lab)
    qbuck(df, col, "ALL BOOKS " + lab)

# Conductor
m = pd.read_csv(W + r"\conductor_joined.csv", usecols=["day", "book", "t_in", "strike", "rr", "c_ret"])
key = ["day", "book", "t_in", "strike", "rr"]
mm = m.merge(df.drop_duplicates(key), on=key, how="left")
mm["ret_pct"] = mm["c_ret"]
mm["lr"] = np.log1p(mm.ret_pct / 100)
for col in ("edge5_cal", "edge1_cal", "gcredit_cal", "rv_iv_m"):
    qbuck(mm, col, "CONDUCTOR " + col, q=3)

print("\n== Conductor by day type and day ==")
print(mm.groupby(["dtype", "day"]).apply(lambda gr: pd.Series(dict(n=len(gr), win=round(100 * (gr.ret_pct > 0).mean()),
      comp=round(100 * (np.exp(gr.lr.sum()) - 1), 1), dte=gr.dte_in.median(), iv=round(gr.iv_in.median(), 1),
      adelta=round(gr.adelta.median(), 3), ivchg=round(gr.ivchg.median(), 2))), include_groups=False).to_string())

# can the IV change after entry be predicted ex ante?  rank correlation on discovery vs test, all books
print("\n== ex-ante predictors of IV change entry->exit (Spearman), all books; disc | test ==")
cand = ["wx_atm_iv_chg5", "wx_opt_iv_chg5", "wx_opt_iv_chg1", "wx_atm_iv_chg1", "wx_iv_vs_med", "wx_atm_iv_day_pos", "wx_skew_atm",
        "wx_term_atm", "wx_iv_spot_corr15", "wx_e_iv_rv", "rv_iv_m", "wx_mv300", "wx_mv60", "wx_vanna", "wx_mins_open",
        "wx_moneyness_pts", "adelta", "iv_in"]
rows = []
for dt in ("normal", "day_before", "expiry"):
    for rr in ("CE", "PE"):
        d = df[(df.dtype == dt) & (df.rr == rr)].dropna(subset=["ivchg"])
        for c in cand:
            e, l = d[~d.late], d[d.late]
            if e[c].notna().sum() < 50 or l[c].notna().sum() < 50:
                continue
            rows.append(dict(dt=dt, rr=rr, feat=c, n_e=int(e[c].notna().sum()), n_l=int(l[c].notna().sum()),
                             rho_e=round(e[[c, "ivchg"]].corr("spearman").iloc[0, 1], 3),
                             rho_l=round(l[[c, "ivchg"]].corr("spearman").iloc[0, 1], 3)))
R = pd.DataFrame(rows)
R["same_sign"] = np.sign(R.rho_e) == np.sign(R.rho_l)
R["minabs"] = np.where(R.same_sign, np.minimum(R.rho_e.abs(), R.rho_l.abs()), 0)
print(R.sort_values("minabs", ascending=False).head(25).to_string(index=False))
print("tested pairs:", len(R))
print("\n== how much of the return is the IV change? all books, OLS ret_pct ~ ivchg (vega effect) by day type ==")
for dt in ("normal", "day_before", "expiry"):
    d = df[df.dtype == dt].dropna(subset=["ivchg", "ret_pct"])
    d = d[d.ivchg.abs() < 20]
    c = np.corrcoef(d.ivchg, d.ret_pct)[0, 1]
    v = (100 * d["wx_vega"] * d["ivchg"] / d["entry"]).median()
    print(f"{dt:10s} n={len(d)} corr(ivchg, ret)={c:.3f}  median vega effect {v:.2f}%")
df[["day", "book", "t_in", "strike", "rr", "edge5_cal", "edge1_cal", "gcredit_cal", "rv_iv_m", "be_drift_honest"]].to_parquet(W + r"\edge_feats.parquet")
