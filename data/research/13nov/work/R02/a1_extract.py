import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, time
import pandas as pd, pyarrow.parquet as pq
t0 = time.time()
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
names = set(pq.read_schema(P).names)
base = ['day','book','rr','strike','expiry','qty','entry','entry_bid','entry_ask','exit','exit_bid','exit_ask','t_in','t_out',
        'time_in','time_out','hold_s','reason','ret_pct','pnl_rs','peak_pts','worst_pts','peak_bid','peak_t','delta_in','delta_out',
        'iv_in','iv_out','dte_in','why','ep_type','fut_in','fut_out','stale_exit','exit_fill_delay_s','exit_trigger_px','trigger_t']
marks = ['60','300','900','1800','exit_req','exit']
mf = ['hold_s','gain_pts','gain_pct','peak_pts','time_to_peak_s','peak_age_s','gain_vs_peak','giveback_pts','giveback_share',
      'giveback_rate_pts_min','worst_pts','fut_fav_pts','fut_best_fav_pts','fut_giveback_pts','attr_delta_pts','attr_theta_pts',
      'attr_iv_chg','attr_resid_pts']
wx = ['theta_be','theta_min','theta_pct','theta_be15','gamma','delta','vega','premium','spread_pct','rv1','rv5','rv15_spot','sigma15',
      'atr1_15','vix','dte','expiry_day','hrs_to_expiry','mins_to_flat','er60','er30','er_day','chop30','chop60','range_vs_norm',
      'rv5_vs_norm','gamma_theta','spread_be_pts','mins_open','regime','hmm_state','strad_now','range_vs_strad','day_move_vs_strad',
      'atm_iv_med','iv_vs_med','imp_rng','imp_depth','imp_age_min','mv5','mv30','mv60','trig_str','gearing','extrinsic_pct','fut_vol_vs_norm',
      'range_now','day_move','squeeze','vr5_60','ac1_30','charm_min','speed_g','vomma','vanna']
cols = [c for c in base if c in names] + [f"h{m}_{f}" for m in marks for f in mf if f"h{m}_{f}" in names] + \
       [f"wx_{w}" for w in wx if f"wx_{w}" in names]
missing = [c for c in base if c not in names] + [w for w in wx if f"wx_{w}" not in names]
print("missing", missing)
df = pd.read_parquet(P, columns=cols)
print(df.shape, round(time.time()-t0,1))
df.to_pickle(r"D:\ApexOptions\data\research\13nov\work\R02\all_trades_slim.pkl")
pool = ['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t']
# conductor trades
B = r"D:\ApexOptions\data\replay\batch"
c1 = json.load(open(B + r"\p44_sim\conductor_sim.json", encoding="utf-8"))["days"]
c2 = json.load(open(B + r"\p44_simr\conductor_sim.json", encoding="utf-8"))["days"]
rows = []
for day in c1:
    src = c2 if day in ("2026-10-28","2026-10-30","2026-11-02","2026-11-03") else c1
    for t in src[day]["trades"]:
        r = dict(t); r["day"] = day; rows.append(r)
C = pd.DataFrame(rows)
print("conductor trades", len(C), C.groupby("day").size().to_dict())
C.to_pickle(r"D:\ApexOptions\data\research\13nov\work\R02\conductor.pkl")
print("book counts", df.groupby('book').size().sort_values().tail(8).to_dict())
print("days dte", df.groupby('day')['dte_in'].median().to_dict())
print(round(time.time()-t0,1), "s")
