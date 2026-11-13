"""R06 phase B: walk-forward test of ex-ante strike / expiry POLICIES on the Conductor's own trades, using the repriced
returns from a3_reprice.py (same entry and exit seconds; exits that depend on the premium path would differ in a
real replay, so a policy that passes here still needs a shadow book). Discover on days <= 4 Nov, test on 5 Nov on.
    py -3.13 phaseB_strike_policy.py            (after phaseB_reprice_all.py; also runs on any days already repriced)
"""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import glob
import numpy as np, pandas as pd
pd.set_option("display.width", 250)
W = r"D:\ApexOptions\data\research\13nov\work\R06"
R = pd.concat([pd.read_csv(f) for f in glob.glob(W + r"\reprice_*.csv")], ignore_index=True)
R = R[R.book == "CONDUCTOR"].drop_duplicates(["day", "t_in", "K", "rr"]).sort_values(["day", "t_in"]).reset_index(drop=True)
J = pd.read_csv(W + r"\conductor_joined.csv")
J = J[["day", "t_in", "strike", "rr", "dtype", "wx_iv_vs_med", "iv_in", "wx_theta_ratio", "wx_e_iv_rv", "wx_mins_open",
       "wx_opt_iv_chg5", "rent_cal"]].rename(columns={"strike": "K"})
R = R.merge(J, on=["day", "t_in", "K", "rr"], how="left")
R["exp"] = R["dtype"] == "expiry"
R["th_pct_hr"] = 100 * 60 * R["base_th_cal"].abs() / R["base_ask"]
R["late"] = R["day"] >= "2026-11-05"
print("Conductor trades repriced:", len(R), "days", R.day.nunique(), "| discovery", int((~R.late).sum()), "test", int(R.late.sum()))


def pick(alt, mask):
    """returns per-trade pct return: alt where mask (and alt priced), else base; base missing -> recorded"""
    base = R["base_ret"].fillna(R["rec_ret"])
    a = R.get(f"{alt}_ret")
    if a is None:
        return base
    return np.where(mask & a.notna(), a, base)


POL = {
    "P0 base (as traded)": pick("base", np.zeros(len(R), bool)),
    "P1 one deeper ITM always": pick("itm1", np.ones(len(R), bool)),
    "P2 two deeper ITM always": pick("itm2", np.ones(len(R), bool)),
    "P3 one OTM-ward always (reference)": pick("otm1", np.ones(len(R), bool)),
    "P4 deeper ITM on expiry day only": pick("itm1", R.exp.values),
    "P5 deeper ITM on normal days only": pick("itm1", ~R.exp.values),
    "P6 CE deeper ITM, PE as is (spot-vol)": pick("itm1", (R.rr == "CE").values),
    "P7 next weekly delta-matched on expiry day": pick("nw_dm", R.exp.values),
    "P8 next weekly same strike on expiry day": pick("nw_same", R.exp.values),
    "P9 next weekly delta-matched always": pick("nw_dm", np.ones(len(R), bool)),
}
# threshold policies: choose the threshold on discovery days only
for name, col, alt in (("P10 deeper ITM when IV vs median > x", "wx_iv_vs_med", "itm1"),
                       ("P11 deeper ITM when theta %/hr > x", "th_pct_hr", "itm1"),
                       ("P12 deeper ITM when theta_ratio > x", "wx_theta_ratio", "itm1")):
    E = ~R.late.values
    best = None
    vals = R.loc[E, col].dropna()
    for th in np.unique(np.nanquantile(vals, np.linspace(0.1, 0.9, 9))) if len(vals) > 5 else []:
        r = pick(alt, (R[col] > th).values)
        lr = np.log1p(np.asarray(r)[E] / 100).sum()
        if best is None or lr > best[0]:
            best = (lr, th)
    if best:
        POL[f"{name} (x={best[1]:.3g}, chosen on discovery)"] = pick(alt, (R[col] > best[1]).values)


def report(mask, label):
    rows = []
    for nm, r in POL.items():
        r = np.asarray(r, float)[mask]
        d = R.loc[mask, "day"].values
        lr = pd.Series(np.log1p(r / 100)).groupby(d).sum()
        best_trade = np.argmax(r) if len(r) else None
        lr_wo_bt = np.log1p(np.delete(r, best_trade) / 100).sum() if len(r) > 1 else np.nan
        rows.append(dict(policy=nm, n=len(r), win=round(100 * (r > 0).mean(), 1), mean=round(r.mean(), 2),
                         comp_pct=round(100 * (np.exp(lr.sum()) - 1), 1), loss_days=int((lr < 0).sum()), days=len(lr),
                         worst_day_pct=round(100 * (np.exp(lr.min()) - 1), 1),
                         wo_best_trade_pct=round(100 * (np.exp(lr_wo_bt) - 1), 1),
                         wo_best_day_pct=round(100 * (np.exp(lr.sum() - lr.max()) - 1), 1)))
    print(f"\n== {label} ==")
    print(pd.DataFrame(rows).to_string(index=False))


report(~R.late.values, "DISCOVERY days (19 Oct - 4 Nov)")
report(R.late.values, "TEST days (5 Nov on)")
print("\n== TEST days, per day compounded % ==")
out = {}
for nm, r in POL.items():
    out[nm[:40]] = pd.Series(np.log1p(np.asarray(r, float)[R.late.values] / 100)).groupby(R.loc[R.late, "day"].values).sum().map(
        lambda v: round(100 * (np.exp(v) - 1), 1))
print(pd.DataFrame(out).T.to_string())
print("\nvariants tried: 10 fixed policies + 3 x 9 thresholds = 37 (multiple testing: treat any single winner with caution)")
