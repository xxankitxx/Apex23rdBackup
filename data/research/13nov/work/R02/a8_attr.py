import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\13nov\work\R02"
J = pd.read_pickle(W + r"\conductor_joined.pkl")
J["exp"] = J.day == J.expiry
f = ["gain_pts","peak_pts","gain_vs_peak","giveback_pts","giveback_rate_pts_min","time_to_peak_s","peak_age_s","fut_fav_pts","fut_best_fav_pts","fut_giveback_pts","attr_delta_pts","attr_theta_pts","attr_iv_chg","attr_resid_pts"]
cols = [f"hexit_req_{x}" for x in f if f"hexit_req_{x}" in J]
J["reason0"] = J["reason0"].astype(str)
g = J.groupby(["exp","reason0"])[cols].median().round(2)
g.columns = [c.replace("hexit_req_","") for c in g.columns]
g["n"] = J.groupby(["exp","reason0"]).size()
pd.set_option("display.width", 250)
print(g.to_string())
# share of the premium change explained: delta vs theta vs iv (sum over trades)
for e in (False, True):
    s = J[J.exp == e]
    print("exp" if e else "norm", "sum gain %.0f pts: delta %.0f theta %.0f resid %.0f; median iv change %.2f" % (s.hexit_req_gain_pts.sum(), s.hexit_req_attr_delta_pts.sum(), s.hexit_req_attr_theta_pts.sum(), s.hexit_req_attr_resid_pts.sum(), s.hexit_req_attr_iv_chg.median()))
# expiry SL trades detail
sl = J[(J.exp) & (J.reason0 == "SL")]
print(sl[["day","time_in","rr","entry","hold_s","peak_bid","worst_pts","hexit_req_fut_fav_pts","hexit_req_fut_best_fav_pts","hexit_req_attr_delta_pts","hexit_req_attr_iv_chg","wx_spread_pct","wx_theta_pct","wx_er30","why"]].to_string())
print("expiry SL: count", len(sl), "hold<=120s", int((sl.hold_s<=120).sum()), "best fav fut pts median", sl.hexit_req_fut_best_fav_pts.median())
# TP 0.6 expiry trades in conductor
J["pk"] = J.peak_bid / J.entry - 1
t = J[J.exp & (J.pk >= 0.6)][["day","time_in","pk","ret_pct","reason0","hold_s"]]
print(t.to_string())
