import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R03 part 3: regime fields at the trigger of the c20 pool trades. Terciles cut on the discovery days (19 Oct - 4 Nov),
the worst discovery tercile becomes a veto, the veto is replayed through the one-account simulator on all days and
judged on the test days (5 - 12 Nov). Also the Conductor's own trades by regime bucket."""
import os, time, warnings, pickle
warnings.filterwarnings("ignore")
t00 = time.time()
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R03"
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500); pd.set_option("display.max_columns", 60)
lap = lambda m: print(f"[{time.time()-t00:6.1f}s] {m}", flush=True)
base = pd.read_pickle(os.path.join(W, "base.pkl"))
wx = pd.read_pickle(os.path.join(W, "wx.pkl"))
assert len(base) == len(wx) and (base.book.values == wx.book.values).all()
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
P0 = {b: i for i, b in enumerate(POOL)}
df = pd.concat([base, wx.drop(columns=[c for c in wx.columns if c in base.columns])], axis=1)
df["trig"] = df["trigger_t"].fillna(df["t_in"])
df = df[df.book.isin(POOL)].dropna(subset=["entry", "exit", "t_out", "trig"]).copy()
df["early"] = df.day < "2026-11-05"
lap(f"pool trades {len(df)}")
DAYS = sorted(df.day.unique())
# derived, direction-relative
df["with_day"] = np.sign(df["wx_day_move"])            # +1 trade is with the day's move so far
df["with_gap"] = np.sign(df["wx_gap_pts"])
df["abs_gap"] = df["wx_gap_pts"].abs()
df["with_vwap"] = np.sign(df["wx_vwap_ext"])
df = df.reset_index(drop=True)
df["_p"] = df.book.map(P0)
ARRS = {}
for d, g in df.groupby("day"):
    g = g.sort_values(["trig", "_p"], kind="stable")
    ARRS[d] = (g.index.values, g.trig.values, g.t_out.values, g._p.values, g.entry.values, g.exit.values, g.ret_pct.values, g.book.values)


def sim(d, veto_mask=None):
    ix, tg, to, pb, en, ex, rp, bk = ARRS[d]
    keep = np.ones(len(ix), bool) if veto_mask is None else ~np.asarray(veto_mask)[ix]
    cap = 1e5; held = None; out = []
    for k in np.nonzero(keep)[0]:
        t = tg[k]
        if held is not None:
            if t <= held[0] or t < held[1] or (t == held[1] and pb[k] == held[2]):
                continue
            held = None
        lots = int(cap // (en[k] * 65))
        if lots < 1:
            continue
        pnl = (ex[k] - en[k]) * lots * 65; cap += pnl
        held = (t, to[k], pb[k]); out.append((bk[k], t, rp[k], pnl))
    return out, (cap / 1e5 - 1) * 100


cond = {d: sim(d) for d in DAYS}
print("Conductor check sum %", round(sum(v[1] for v in cond.values()), 1))
# the Conductor's own trades with their photo
ck = {(d, b, t) for d in DAYS for (b, t, _, _) in cond[d][0]}
df["is_cond"] = [(d, b, t) in ck for d, b, t in zip(df.day, df.book, df.trig)]
CT = df[df.is_cond].copy()
print("Conductor trades matched", len(CT))
NUM = ["wx_er_day", "wx_er30", "wx_er60", "wx_pos_in_range", "wx_or_pos", "wx_day_move", "abs_gap", "wx_gap_pts", "wx_vwap_ext",
       "wx_vwap_z", "wx_range_vs_norm", "wx_range_now", "wx_mins_open", "wx_vix_chg_open", "wx_vix_day_pos", "wx_chop60",
       "wx_reversals60", "wx_vwap_cross_n", "wx_day_move_vs_strad", "wx_range_vs_strad", "wx_atm_iv_day_pos", "wx_e_iv_rv",
       "wx_breadth900_dir", "wx_hw_disp300", "wx_bn300", "wx_fn300", "wx_bn_minus_nifty300", "wx_wmove60", "wx_hmm_drift",
       "wx_ma20_slope", "wx_rsi14_5m", "wx_dist_hi", "wx_dist_lo", "wx_give", "wx_new_highs", "wx_new_lows", "wx_range_vs_pd",
       "wx_strad_vs_open_pct", "wx_pcr", "wx_gex_balance", "wx_day_move_share", "wx_vwap_side_min", "wx_open_side_min"]
NUM = [c for c in NUM if c in df and df[c].notna().mean() > 0.6]
CAT = ["wx_regime", "wx_gex_regime", "wx_hmm_state", "with_day", "with_gap", "with_vwap", "wx_dte", "wx_inside_pd", "wx_range_on", "wx_ma_stack"]
CAT = [c for c in CAT if c in df]
# ---- 1. pool-trade terciles cut on early days, early vs late
rows = []
E = df[df.early]; L = df[~df.early]
for c in NUM:
    v = E[c].dropna()
    if len(v) < 60:
        continue
    q1, q2 = np.quantile(v, [1 / 3, 2 / 3])
    for nm, lo, hi in (("low", -np.inf, q1), ("mid", q1, q2), ("high", q2, np.inf)):
        r = dict(feat=c, bucket=nm, cut_lo=round(lo, 3), cut_hi=round(hi, 3))
        for tag, X in (("E", E), ("L", L), ("C", CT)):
            s = X[(X[c] > lo) & (X[c] <= hi)]["ret_pct"]
            r[f"{tag}_n"] = len(s); r[f"{tag}_strike"] = round(100 * (s > 0).mean(), 0) if len(s) else np.nan
            r[f"{tag}_mean"] = round(s.mean(), 1) if len(s) else np.nan
            r[f"{tag}_days"] = X[(X[c] > lo) & (X[c] <= hi)].day.nunique()
        rows.append(r)
for c in CAT:
    for val in sorted(df[c].dropna().unique(), key=str):
        r = dict(feat=c, bucket=str(val), cut_lo=np.nan, cut_hi=np.nan)
        for tag, X in (("E", E), ("L", L), ("C", CT)):
            s = X[X[c] == val]["ret_pct"]
            r[f"{tag}_n"] = len(s); r[f"{tag}_strike"] = round(100 * (s > 0).mean(), 0) if len(s) else np.nan
            r[f"{tag}_mean"] = round(s.mean(), 1) if len(s) else np.nan
            r[f"{tag}_days"] = X[X[c] == val].day.nunique()
        rows.append(r)
TB = pd.DataFrame(rows); TB.to_csv(os.path.join(W, "pool_trades_by_regime_bucket.csv"), index=False)
lap("buckets")
# ---- 2. veto replay: the worst early bucket (by mean, needs >= 40 early trades on >= 5 days) vetoed in the simulator
cand = TB[(TB.E_n >= 40) & (TB.E_days >= 5)].copy()
res = []
for _, r in cand.iterrows():
    c = r.feat
    if np.isfinite(r.cut_lo) or np.isfinite(r.cut_hi):
        m = ((df[c] > r.cut_lo) & (df[c] <= r.cut_hi)).values
    else:
        m = (df[c].astype(str) == r.bucket).values
    if m.mean() > 0.6:
        continue
    out = {d: sim(d, m) for d in DAYS}
    ret = np.array([out[d][1] for d in DAYS]); cr = np.array([cond[d][1] for d in DAYS])
    early = np.array([d < "2026-11-05" for d in DAYS])
    n = sum(len(out[d][0]) for d in DAYS); w = sum(sum(1 for x in out[d][0] if x[3] > 0) for d in DAYS)
    nL = sum(len(out[d][0]) for d in DAYS if d >= "2026-11-05"); wL = sum(sum(1 for x in out[d][0] if x[3] > 0) for d in DAYS if d >= "2026-11-05")
    res.append(dict(feat=c, bucket=r.bucket, lo=r.cut_lo, hi=r.cut_hi, share_vetoed=round(m.mean(), 2), E_mean=r.E_mean, E_strike=r.E_strike,
                    early_sum=round(ret[early].sum(), 1), c_early=round(cr[early].sum(), 1),
                    late_sum=round(ret[~early].sum(), 1), c_late=round(cr[~early].sum(), 1),
                    late_strike=round(100 * wL / max(nL, 1), 1), late_n=nL, late_lose_days=int((ret[~early] < 0).sum()),
                    c_late_lose=int((cr[~early] < 0).sum()), all_strike=round(100 * w / max(n, 1), 1), all_n=n,
                    late_days=" ".join(f"{x:.0f}" for x in ret[~early])))
VR = pd.DataFrame(res)
VR["early_gain"] = VR.early_sum - VR.c_early; VR["late_gain"] = VR.late_sum - VR.c_late
VR = VR.sort_values("early_gain", ascending=False)
VR.to_csv(os.path.join(W, "veto_walkforward.csv"), index=False)
cn = sum(len(cond[d][0]) for d in DAYS if d >= "2026-11-05"); cw = sum(sum(1 for x in cond[d][0] if x[3] > 0) for d in DAYS if d >= "2026-11-05")
print("Conductor late days: strike", round(100 * cw / cn, 1), "n", cn, "per day", " ".join(f"{cond[d][1]:.0f}" for d in DAYS if d >= "2026-11-05"))
print("\nVETO walk-forward (veto chosen by early days; ranked by early gain); variants:", len(VR))
print(VR.head(25).to_string())
print("\nTop-5 by early gain, how many also gain late:", int((VR.head(5).late_gain > 0).sum()), "of 5;  top-10:", int((VR.head(10).late_gain > 0).sum()))
print("All variants: late gain > 0 in", int((VR.late_gain > 0).sum()), "of", len(VR))
# Conductor trades by the strongest regime cuts
print("\nCONDUCTOR trades by bucket for chosen features")
show = TB[TB.feat.isin(["wx_er_day", "wx_pos_in_range", "wx_day_move", "wx_range_vs_norm", "wx_regime", "with_day", "with_gap", "wx_dte", "wx_mins_open", "wx_hmm_state", "wx_gex_regime"])]
print(show.to_string())
lap("done")
