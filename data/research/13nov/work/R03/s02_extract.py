import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import time, glob, os
t0 = time.time()
import numpy as np, pandas as pd, pyarrow.parquet as pq, joblib
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
W = r"D:\ApexOptions\data\research\13nov\work\R03"
names = set(pq.ParquetFile(P).schema.names)
want = """mins_open dte expiry_day day_before_expiry weekday er60 er_day dir60 pos_in_range give range_on dist_hi dist_lo
or_pos gap_pts gap_filled or15_pos or30_pos or45_pos er30 new_highs new_lows vwap_ext to_pdh to_pdl to_pdc hi_age_min
lo_age_min vix vix_chg_open vix_day_pos range_now range_vs_norm rv5_vs_norm norm_days fut_vol_vs_norm hw_vol_vs_norm
vwap_side_min vwap_cross_n vwap_z vwap_stretch_share pd_range range_vs_pd inside_pd pd_close_pos day_move day_move_share
open_side_min reversals60 chop30 chop60 regime hmm_state hmm_drift breadth900_dir breadth60_dir breadth_net hw_disp300
strad_vs_open_pct day_move_vs_strad range_vs_strad strad_now atm_iv_day_pos atm_iv_med e_iv_rv term_atm skew_atm pcr
max_pain_dist bn300 fn300 bn_minus_nifty300 wmove60 wmove60_bank gex_regime gex_balance rv15_spot sigma15 speed15
ma20_slope ma_stack rsi14_5m""".split()
cols = ["day", "book", "trigger_t", "t_in", "dir", "rr"] + ["wx_" + w for w in want if "wx_" + w in names]
print("missing", [w for w in want if "wx_" + w not in names], flush=True)
df = pd.read_parquet(P, columns=cols)
df.to_pickle(os.path.join(W, "wx.pkl"))
print("wx", df.shape, round(time.time() - t0, 1), flush=True)
S = {}
for f in sorted(glob.glob(r"D:\ApexOptions\data\forecast_lab\collect\*.joblib")):
    d = joblib.load(f)
    s = np.asarray(d["S"], float)
    ivt = np.asarray(d["IVT"], float)
    S[d["day"] + "_t"] = s[:, 0]
    S[d["day"] + "_F"] = s[:, 1].astype(np.float32)
    if len(ivt):
        S[d["day"] + "_ivt"] = ivt[::6, 0]
        S[d["day"] + "_iv"] = ivt[::6, 2].astype(np.float32)
    print(d["day"], s.shape, ivt.shape, round(time.time() - t0, 1), flush=True)
np.savez_compressed(os.path.join(W, "fut_paths.npz"), **S)
print("done", round(time.time() - t0, 1))
