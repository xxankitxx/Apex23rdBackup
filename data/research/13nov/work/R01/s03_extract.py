import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time; t0 = time.time(); print("start", flush=True)
import pyarrow.parquet as pq; print("pa", round(time.time()-t0,1), flush=True)
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
base = ["day","book","rr","strike","entry","exit","ret_pct","pnl_rs","t_in","t_out","trigger_t","time_in","time_out",
        "why","reason","ep_type","hold_s","peak_pts","worst_pts","delta_in","spot_in","fut_in","fut_out","dte_in","peak_bid"]
wx = ["mins_open","expiry_day","er60","er_day","er30","dir60","pos_in_range","dist_hi","dist_lo","mv5","mv30","mv60","mv120","mv300",
      "day_move","day_move_share","range_now","range_vs_norm","rv5","rv15_spot","chop30","reversals60","breadth_dir","breadth_net",
      "vwap_ext","gap_pts","hi_age_min","lo_age_min","imp_rng","imp_depth","imp_age_min","imp_with","vix","or_pos","fmv300","bn300",
      "hh_hl5","pos60","ma_stack","ma20_slope","rsi14_5m","z20","regime","hmm_state","strad_vs_open_pct","range_vs_strad",
      "day_move_vs_strad","wmove60","breadth900_dir","new_highs","new_lows","squeeze","vwap_side_with","or30_pos","pos15","range60",
      "range15","atr1_15","rv_ratio","theta_pct","iv_vs_med","atm_iv_med","to_pdh","to_pdl","pd_range","range_vs_pd","vwap_z","ma60_dist"]
hm = [f"h{m}_{k}" for m in (60,300,900,1800) for k in ("hold_s","gain_pct","peak_pts","worst_pts")]
pf = pq.ParquetFile(P); names = set(pf.schema_arrow.names)
cols = [c for c in base if c in names] + ["wx_"+c for c in wx if "wx_"+c in names] + [c for c in hm if c in names]
miss = [c for c in wx if "wx_"+c not in names]
print("missing wx", miss)
tb = pq.read_table(P, columns=cols, use_threads=False)
print("read", round(time.time()-t0,1))
df = tb.to_pandas()
# keep wx_ prefix
df.to_pickle(r"D:\ApexOptions\data\research\13nov\work\R01\trades_small.pkl")
print(df.shape, round(time.time()-t0,1))
