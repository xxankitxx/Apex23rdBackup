"""R06: aggregate the repricing / theta-clock / IV-path CSVs written by a3_reprice.py (any number of tags)."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import glob
import numpy as np, pandas as pd
pd.set_option("display.width", 250)
W = r"D:\ApexOptions\data\research\13nov\work\R06"
tags = sys.argv[1:] or None


def load(prefix):
    fs = sorted(glob.glob(W + f"\\{prefix}_*.csv"))
    if tags:
        fs = [f for f in fs if any(f.endswith(f"_{t}.csv") for t in tags)]
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True).drop_duplicates() if fs else pd.DataFrame()


R = load("reprice")
ALTS = ["base", "itm1", "itm2", "otm1", "nw_same", "nw_itm1", "nw_itm2", "nw_dm"]
print("rows", len(R), "days", sorted(R.day.unique()))
# alignment of the base strike: which row offset reproduces the recorded entry ask / exit bid
for off in (-1, 0, 1):
    e = (R[f"ask_off{off}"] - R["rec_entry"]).abs()
    x = (R[f"bid_out_off{off}"] - R["rec_exit"]).abs()
    print(f"offset {off:+d}: entry ask within 0.1 pt {100 * (e <= 0.1).mean():.0f} %, median |diff| {e.median():.2f}; "
          f"exit bid within 0.1 pt {100 * (x <= 0.1).mean():.0f} %, median |diff| {x.median():.2f}")
R["base_vs_rec"] = R["base_ret"] - R["rec_ret"]
print("repriced base minus recorded return (pct pts): median", round(R.base_vs_rec.median(), 2), "IQR",
      R.base_vs_rec.quantile([.25, .75]).round(2).tolist())


def stats(d, alt):
    r = d[f"{alt}_ret"]
    ok = r.notna()
    rr = r[ok]
    base = d.loc[ok, "base_ret"]
    return dict(alt=alt, n=int(ok.sum()), of=len(d), win=round(100 * (rr > 0).mean(), 1) if ok.any() else np.nan,
                mean=round(rr.mean(), 2), med=round(rr.median(), 2), base_mean_same=round(base.mean(), 2),
                base_win_same=round(100 * (base > 0).mean(), 1) if ok.any() else np.nan,
                comp=round(100 * (np.prod(1 + rr / 100) - 1), 1), base_comp_same=round(100 * (np.prod(1 + base / 100) - 1), 1))


for who, d in (("CONDUCTOR", R[R.book == "CONDUCTOR"]), ("pool books", R[R.book != "CONDUCTOR"])):
    print(f"\n== {who}: same entry and exit seconds, other contracts (ret = exit bid / entry ask - 1) ==")
    print(pd.DataFrame([stats(d, a) for a in ALTS if f"{a}_ret" in d]).to_string(index=False))
    for side in ("CE", "PE"):
        print(f"-- {who} {side} --")
        print(pd.DataFrame([stats(d[d.rr == side], a) for a in ALTS if f"{a}_ret" in d]).to_string(index=False))
    if who == "CONDUCTOR":
        print("\n-- Conductor per day: compounded day % (an alternative with no clean quote keeps the base trade) --")
        rows = []
        for day, g in d.groupby("day"):
            row = dict(day=day, n=len(g), rec=round(100 * (np.prod(1 + g.rec_ret / 100) - 1), 1))
            for a in ALTS:
                if f"{a}_ret" in g:
                    rr = g[f"{a}_ret"].fillna(g["base_ret"]).fillna(g["rec_ret"])
                    row[a] = round(100 * (np.prod(1 + rr / 100) - 1), 1)
                    row[a + "_win"] = int((rr > 0).sum())
            rows.append(row)
        print(pd.DataFrame(rows).to_string(index=False))

print("\n== greeks at entry, by contract (medians, pool + Conductor) ==")
gcols = []
for a in ALTS[:-1]:
    for f in ("delta", "iv", "ask", "sprd_pct", "gear_pct_pt", "th_cal", "gamma", "vega"):
        if f"{a}_{f}" in R:
            gcols.append(f"{a}_{f}")
med = R[gcols].median()
tab = pd.DataFrame({f: [med.get(f"{a}_{f}", np.nan) for a in ALTS[:-1]] for f in
                    ("delta", "iv", "ask", "sprd_pct", "gear_pct_pt", "th_cal", "gamma", "vega")}, index=ALTS[:-1])
tab["th_cal_pct_per_hr"] = 100 * 60 * tab["th_cal"].abs() / tab["ask"]
tab["vega_pct_per_volpt"] = 100 * tab["vega"] / tab["ask"]
print(tab.round(4).to_string())

print("\n== premium attribution of the base contract (mid to mid), pct of entry mid, means ==")
for who, d in (("CONDUCTOR", R[R.book == "CONDUCTOR"]), ("pool", R[R.book != "CONDUCTOR"])):
    d = d.dropna(subset=["base_a_total_mid", "base_a_delta", "base_a_gamma", "base_a_theta_cal", "base_a_vega"])
    mid = d["base_ask"] / (1 + d["base_sprd_pct"] / 200)   # entry mid: ask = mid * (1 + spread%/2)
    out = {}
    for f in ("a_delta", "a_gamma", "a_theta_cal", "a_vega", "a_total_mid", "spread_cost"):
        out[f] = round(float((100 * d[f"base_{f}"] / mid).mean()), 3)
    out["resid"] = round(out["a_total_mid"] - out["a_delta"] - out["a_gamma"] - out["a_theta_cal"] - out["a_vega"], 3)
    out["n"] = len(d)
    out["hold_min_med"] = round(float(d.hold_min.median()), 1)
    out["kit_theta_would_be"] = round(out["a_theta_cal"] * 1440 / 375, 3)
    print(who, out)
    for side in ("CE", "PE"):
        s = d[d.rr == side]
        if len(s):
            m_ = s["base_ask"] / (1 + s["base_sprd_pct"] / 200)
            print("   ", side, {f: round(float((100 * s[f"base_{f}"] / m_).mean()), 3) for f in ("a_delta", "a_gamma", "a_theta_cal", "a_vega")},
                  "IV in->out median", round(float((s.base_iv_out - s.base_iv).median()), 3), "n", len(s))

C = load("clock")
if len(C):
    print("\n== theta clock: 5-min ATM straddle at a fixed strike; decay not explained by delta+gamma vs calendar theta ==")
    C["unexpl"] = C["dS"] - C["expl"]
    C["hr"] = (C["hm"] // 60).astype(int)
    for day, g in C.groupby("day"):
        k = g["unexpl"].sum() / g["th_cal5"].sum()
        se = g["unexpl"].std() / np.sqrt(len(g) / 5) / abs(g["th_cal5"].mean())
        print(f"{day}: windows {len(g)}, straddle {g.S0.median():.1f}, IV {g.iv.median():.2f}, T {g.T_min.median() / 1440:.2f} d, "
              f"calendar theta {g.th_cal5.mean() / 5:+.4f} pts/min, measured {g.unexpl.mean() / 5:+.4f} pts/min, "
              f"multiple of calendar theta {k:.2f} (approx se {se:.2f}); kit = 3.84")
        print("    by hour (measured / calendar):", {int(h): round(float(x.unexpl.sum() / x.th_cal5.sum()), 2) for h, x in g.groupby("hr")})
I = load("ivpath")
if len(I):
    print("\n== ATM IV through the day (calendar time), weekly (w0) and next weekly (w1) ==")
    print(I.pivot_table(index="day", columns="at", values="iv_w0").round(2).to_string())
    print(I.pivot_table(index="day", columns="at", values="iv_w1").round(2).to_string())
