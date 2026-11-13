import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time, json
t0 = time.time()
import numpy as np, pandas as pd, pyarrow.parquet as pq
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
names = pq.read_schema(P).names
want_num = ["wx_e_fut_ofi60","wx_e_fut_micro","wx_e_fut_imb5","wx_e_fut_tot_imb","wx_e_syn_dev","wx_e_basis_dev",
 "wx_fut_imb_o","wx_fut_imb_q","wx_fut_imb_t_chg30","wx_fut_lead","wx_agg_with_rs","wx_agg_net","wx_fut_vol_surge",
 "wx_fut_ttq60","wx_absorb60","wx_kyle_lambda","wx_fut_spread","wx_spread_pct","wx_quote_age","wx_rest_with_rs",
 "wx_rest_opp_rs","wx_rest_round_rs","wx_hw_book_imb","wx_hw_book_imb_t","wx_hw_book_chg30","wx_hk_buy","wx_hk_sell","wx_hk_ratio",
 "wx_opt_book_imb","wx_opt_imb_chg30","wx_opt_lead","wx_opt_run","wx_prem_resp1","wx_prem_chg1_pct","wx_opt_vol1",
 "wx_opt_vol_chg1","wx_depth_age_fut","wx_fut_age","wx_sync_opt_age_s","wx_sync_spread_s","wx_sync_oldest_s","wx_trig_print_age_s",
 "wx_spread_be_pts","wx_run1_with","wx_lead1_move60","wx_lead1_move300","wx_fut_vol_accel","wx_with_vol_share60",
 "wx_cp_vol_tilt60","wx_force_rho","wx_force_pi","wx_force_level_dist","wx_mv5","wx_mv10","wx_mv30","wx_accel15","wx_kvt",
 "wx_vol_ratio_with","wx_prem_ratio_with","wx_fut_oi_chg5","wx_fut_buildup_with","wx_round_dist","wx_hw_vol_surge"]
want_cat = ["wx_fut_opp_q","wx_fut_opp_o","wx_fut_pulled","wx_force_verdict","wx_force_with","wx_opt_opp_q","wx_opt_opp_o","wx_adv_force","wx_adv_book"]
base = ["day","book","t_in","trigger_t","ret_pct","rr","dir","fill_delay_s","fill_slip","entry","entry_bid","entry_ask","mid_in","reason","hold_s","strike","fut_in"]
cols = [c for c in base + want_num + want_cat if c in names]
miss = [c for c in base + want_num + want_cat if c not in names]
df = pd.read_parquet(P, columns=cols)
print("loaded", df.shape, "missing", miss, round(time.time()-t0,1), flush=True)
df.to_parquet(r"D:\ApexOptions\data\research\13nov\work\R07\flowcols.parquet")
for c in want_num:
    if c in df: df[c] = pd.to_numeric(df[c], errors="coerce")
df["day"] = df["day"].astype(str)
EARLY = df["day"] <= "2026-11-04"
df["win"] = (df["ret_pct"] > 0).astype(int)
df["ent_spr_pct"] = 100*(df["entry_ask"]-df["entry_bid"])/((df["entry_ask"]+df["entry_bid"])/2)
want_num.append("ent_spr_pct"); want_num.append("fill_delay_s"); want_num.append("fill_slip")
POOL = ["c20_9y","c20_9s","c20_9v","c20_9x","c20_9t"]
print("days", sorted(df.day.unique()))
print("rows early/late", int(EARLY.sum()), int((~EARLY).sum()))
print("pool rows", int(df.book.isin(POOL).sum()))
def spear(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 15: return np.nan
    a = pd.Series(x[m]).rank().values; b = pd.Series(y[m]).rank().values
    if a.std()==0 or b.std()==0: return np.nan
    return float(np.corrcoef(a,b)[0,1])
rows = []
for f in want_num:
    if f not in df: continue
    x = df[f].values.astype(float)
    nn = np.isfinite(x)
    per = {}
    for d, g in df.groupby("day"):
        per[d] = spear(g[f].values.astype(float), g["ret_pct"].values.astype(float))
    e = [v for d, v in per.items() if d <= "2026-11-04" and np.isfinite(v)]
    l = [v for d, v in per.items() if d > "2026-11-04" and np.isfinite(v)]
    se = np.sign(np.median(e)) if e else 0
    rows.append(dict(f=f, n=int(nn.sum()), cov=round(nn.mean(),3), rho_all_e=round(spear(x[EARLY.values], df.ret_pct.values[EARLY.values]),3),
                     rho_all_l=round(spear(x[~EARLY.values], df.ret_pct.values[~EARLY.values]),3),
                     med_e=round(np.median(e),3) if e else None, pos_e=f"{sum(v>0 for v in e)}/{len(e)}",
                     med_l=round(np.median(l),3) if l else None, same_sign_l=f"{sum(np.sign(v)==se for v in l)}/{len(l)}"))
R = pd.DataFrame(rows).sort_values("med_e", key=lambda s: -s.abs())
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(R.to_string(index=False))
R.to_csv(r"D:\ApexOptions\data\research\13nov\work\R07\s1_allbooks_spearman.csv", index=False)
# categorical
for c in want_cat:
    if c not in df: continue
    g = df.groupby([df[c].astype(str), EARLY.map({True:"early",False:"late"})])["ret_pct"].agg(["count","mean", lambda s: (s>0).mean()])
    print("\n", c); print(g.round(3).to_string())
print("done", round(time.time()-t0,1))
