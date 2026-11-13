import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R16: walk-forward test of literature ideas (ORB, VWAP, intraday momentum, noise area, OFI, RV/IV,
# GEX, max pain, PCR, OI, trend filters, mean reversion, expiry) as yes/no KEEP filters on
# (a) the five c20 pool books' trades and (b) the Conductor account trades.
# Discovery 19 Oct - 4 Nov, test 5 Nov - 12 Nov. Thresholds = discovery-day tertiles/median only.
import json, numpy as np, pandas as pd
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
OUT = r"D:\ApexOptions\data\research\13nov\work\R16"
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
FEATS = {
 # idea family : columns (direction-signed in the photograph unless marked *)
 "ORB": ["wx_or15_pos*", "wx_or30_pos*", "wx_or45_pos*", "wx_or_pos"],
 "VWAP": ["wx_vwap_ext", "wx_vwap_z", "wx_vwap_side_min", "wx_vwap_cross_n", "wx_vwap_stretch_share"],
 "IntradayMom": ["wx_day_move", "wx_day_move_share", "wx_open_side_min", "wx_gap_pts", "wx_to_pdc", "wx_er_day"],
 "NoiseArea": ["wx_day_move_vs_strad", "wx_range_vs_strad", "wx_range_vs_norm", "wx_rv5_vs_norm", "wx_range_vs_pd"],
 "OFI": ["wx_e_fut_ofi60", "wx_e_fut_imb5", "wx_fut_imb_o", "wx_agg_net", "wx_hw_book_imb", "wx_opt_book_imb"],
 "RV_IV": ["wx_e_iv_rv", "wx_rv_ratio", "wx_squeeze", "wx_iv_vs_med", "wx_atm_iv_day_pos", "wx_atm_iv_chg5", "wx_vix_chg_open"],
 "GEX": ["wx_gex_balance", "wx_gex_flip_ahead", "wx_gex_wall_ahead", "wx_gex_wall_behind"],
 "MaxPainPin": ["wx_max_pain_dist", "wx_strike_pin", "wx_round_dist"],
 "PCR_OI": ["wx_pcr", "wx_pcr_chg30", "wx_oi_net_help15", "wx_oi_net_help30", "wx_fut_oi_chg30"],
 "Trend": ["wx_ma_stack", "wx_ma20_slope", "wx_ma20_dist", "wx_ma60_dist", "wx_er60", "wx_hh_hl5"],
 "MeanRev": ["wx_z20", "wx_rsi14_5m", "wx_rsi14_1m", "wx_pos60", "wx_dist_hi", "wx_dist_lo"],
 "Expiry": ["wx_dte", "wx_hrs_to_expiry", "wx_theta_ratio", "wx_gamma_theta"],
 "Clock": ["wx_mins_open"],
}
def col(c): return c.rstrip("*")
cols = sorted({col(c) for v in FEATS.values() for c in v})
base = ["day", "book", "t_in", "dir", "rr", "ret_pct", "time_in", "wx_gex_regime", "wx_expiry_day"]
df = pd.read_parquet(P, columns=base + cols)
d = np.where(df["rr"].eq("CE"), 1, -1)
for c in ["wx_or15_pos", "wx_or30_pos", "wx_or45_pos"]:
    x = pd.to_numeric(df[c], errors="coerce")
    df[c] = np.where(d > 0, x, 1 - x)              # signed: 1 = at the high side in OUR direction
for c in cols: df[c] = pd.to_numeric(df[c], errors="coerce")
df["day"] = df["day"].astype(str)
EARLY = lambda s: s <= "2026-11-04"

# Conductor account trades
cs = []
for f, excl in ((r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json", True),
                (r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json", False)):
    j = json.load(open(f))
    for day, v in j["days"].items():
        swap = day in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03")
        if excl == swap: continue
        for t in v.get("trades", []):
            cs.append({"day": day, "book": t["src"], "t_in": float(t["t_in"]), "c_ret": t["ret_pct"]})
cd = pd.DataFrame(cs)
pool = df[df.book.isin(POOL)].copy()
pool["t_in"] = pool["t_in"].astype(float)
cm = cd.merge(pool.drop(columns=["ret_pct"]), on=["day", "book", "t_in"], how="left")
print("conductor trades", len(cd), "matched", cm["wx_mins_open"].notna().sum())

def daystats(g, r):
    # all-in compounding per day, percent
    out = {}
    for day, x in g.groupby("day")[r]:
        out[day] = (np.prod(1 + x.values / 100.0) - 1) * 100
    return out

def summ(t, r, days):
    if len(t) == 0: return dict(n=0, sr=np.nan, mean=np.nan, comp=np.nan, lose=np.nan)
    ds = daystats(t, r); v = np.array([ds.get(x, 0.0) for x in days])
    return dict(n=len(t), sr=round((t[r] > 0).mean() * 100, 1), mean=round(t[r].mean(), 2),
                comp=round((np.prod(1 + v / 100) - 1) * 100, 1), lose=int((v < 0).sum()))

rows = []
nvar = 0
for fam, cl in FEATS.items():
    for c0 in cl:
        c = col(c0)
        for U, r, name in ((pool, "ret_pct", "pool"), (cm, "c_ret", "cond")):
            e = U[EARLY(U.day) & U[c].notna()]
            if len(e) < 30: continue
            qs = np.unique(np.nanquantile(e[c], [1/3, 0.5, 2/3]))
            best = None
            for q in qs:
                for side in (">=", "<="):
                    nvar += 1
                    k = e[c] >= q if side == ">=" else e[c] <= q
                    if k.mean() < 0.4 or k.mean() > 0.95: continue
                    sc = np.log1p(e.loc[k, r] / 100).sum()      # compounding value of kept trades
                    if best is None or sc > best[0]: best = (sc, q, side)
            if best is None: continue
            _, q, side = best
            Ld = U[~EARLY(U.day)]
            days_l = sorted(Ld.day.unique()); days_e = sorted(U[EARLY(U.day)].day.unique())
            def keep(X):
                x = X[c]
                k = (x >= q) if side == ">=" else (x <= q)
                return X[k.fillna(True)]                     # missing value: rule silent, trade kept
            be, bl = summ(U[EARLY(U.day)], r, days_e), summ(Ld, r, days_l)
            ke, kl = summ(keep(U[EARLY(U.day)]), r, days_e), summ(keep(Ld), r, days_l)
            rows.append(dict(univ=name, fam=fam, feat=c, rule=f"{c} {side} {q:.3g}",
                             e_n=ke["n"], e_base_n=be["n"], e_sr=ke["sr"], e_base_sr=be["sr"], e_comp=ke["comp"], e_base_comp=be["comp"],
                             t_n=kl["n"], t_base_n=bl["n"], t_sr=kl["sr"], t_base_sr=bl["sr"], t_mean=kl["mean"], t_base_mean=bl["mean"],
                             t_comp=kl["comp"], t_base_comp=bl["comp"], t_lose=kl["lose"], t_base_lose=bl["lose"]))
R = pd.DataFrame(rows)
R["t_sr_gain"] = R.t_sr - R.t_base_sr
R["t_mean_gain"] = R.t_mean - R.t_base_mean
R.to_csv(OUT + r"\wf_lit_results.csv", index=False)
print("variants tried", nvar)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
for u in ("pool", "cond"):
    x = R[R.univ == u].sort_values("t_mean_gain", ascending=False)
    print("\n==", u, "base test:", x.iloc[0][["t_base_n", "t_base_sr", "t_base_mean", "t_base_comp", "t_base_lose"]].to_dict())
    print(x[["fam", "rule", "e_sr", "e_base_sr", "t_n", "t_sr", "t_mean", "t_comp", "t_lose", "t_sr_gain", "t_mean_gain"]].to_string(index=False))
