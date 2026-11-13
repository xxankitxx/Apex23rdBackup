import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
P = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
cols = ["day","book","rr","strike","expiry","entry","entry_bid","entry_ask","exit","t_in","t_out","ret_pct","hold_s","reason",
        "delta_in","delta_out","iv_in","iv_out","dte_in","fut_in","fut_out","spot_in","mid_in","mid_out",
        "wx_dte","wx_expiry_day","wx_day_before_expiry","wx_hrs_to_expiry","wx_theta_be","wx_speed15","wx_theta_ratio",
        "wx_strad_chg5","wx_strad_excess","wx_strad_now","wx_strad_vs_open_pct","wx_theta_min","wx_gamma","wx_delta",
        "wx_vega","wx_moneyness_pts","wx_extrinsic_pct","wx_gamma_theta","wx_iv_vs_med","wx_atm_iv_med","wx_e_iv_rv",
        "wx_rv5","wx_rv15_spot","wx_vix","wx_premium","wx_spread_pct","wx_opt_iv_vs_atm",
        "h300_attr_iv_chg","h300_attr_theta_pts","h300_attr_delta_pts","h300_attr_resid_pts","h300_gain_pct",
        "h900_attr_iv_chg","h900_attr_theta_pts","h900_attr_delta_pts","h900_attr_resid_pts","h900_gain_pct",
        "h60_attr_iv_chg","h1800_attr_iv_chg"]
df = pd.read_parquet(P, columns=cols)
df.to_parquet(r"D:\ApexOptions\data\research\13nov\work\R06\t_small.parquet")
print(df.shape)
print(df.groupby("day").agg(n=("ret_pct","size"), dte=("dte_in","median"), wxdte=("wx_dte","median"),
      exp=("expiry","first"), ed=("wx_expiry_day","mean"), dbe=("wx_day_before_expiry","mean"),
      iv=("iv_in","median"), fut=("fut_in","median")).to_string())
pool = ["c20_9y","c20_9s","c20_9v","c20_9x","c20_9t"]
p = df[df.book.isin(pool)]
print(p.groupby("book").agg(n=("ret_pct","size"), win=("ret_pct", lambda x:(x>0).mean()), mean=("ret_pct","mean")).to_string())
print(df[["delta_in","iv_in","iv_out","wx_theta_be","wx_speed15","wx_theta_ratio","wx_theta_min","wx_gamma","wx_moneyness_pts","h300_attr_iv_chg","h300_attr_theta_pts"]].describe().T.to_string())
