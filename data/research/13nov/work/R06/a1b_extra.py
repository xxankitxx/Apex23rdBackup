import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, pyarrow.parquet as pq
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
want = ['day','book','t_in','strike','rr','time_in','time_out','exit_bid','exit_ask','peak_pts','worst_pts','why','trigger_t','phase_in','pnl_rs',
 'wx_spread_be_pts','wx_gearing','wx_gamma_theta','wx_gamma_1pct','wx_intrinsic','wx_extrinsic','wx_vanna','wx_charm_min','wx_vomma',
 'wx_po_up5','wx_po_up15','wx_po_ever','wx_e_iv_atm','wx_e_iv_chg5','wx_e_rv15','wx_atm_iv_chg1','wx_atm_iv_chg5','wx_opt_iv_chg1',
 'wx_opt_iv_chg5','wx_skew_atm','wx_term_atm','wx_atm_iv_day_pos','wx_iv_spot_corr15','wx_kv','wx_sigma15','wx_range_vs_strad',
 'wx_day_move_vs_strad','wx_mins_open','wx_rv1','wx_theta_pct','wx_imp_rng','wx_mv5','wx_mv30','wx_mv60','h60_gain_pct','h1800_gain_pct',
 'h300_peak_pts','h900_peak_pts','wx_trig_str','wx_atm_iv_now','wx_strad_open','wx_moneyness_pct','wx_opt_is_atm','wx_range_now','wx_day_move']
have = set(pq.read_schema(P).names)
cols = [c for c in want if c in have]
print("missing:", [c for c in want if c not in have])
df = pd.read_parquet(P, columns=cols)
df.to_parquet(r"D:\ApexOptions\data\research\13nov\work\R06\t_extra.parquet")
print(df.shape)
