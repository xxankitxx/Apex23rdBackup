import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, numpy as np, pandas as pd
P=r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
cols=["day","book","rr","t_in","trigger_t","ret_pct","peak_bid","entry","dte_in","time_in","reason",
      "wx_vwap_side_with","wx_basket_gap","wx_bank_z","wx_sign_none_share300","wx_gap_pts","wx_gap_filled","wx_or30_pos"]
T=pd.read_parquet(P,columns=cols)
cs=[]
for run,days in (("p44_sim",None),("p44_simr",{"2026-10-28","2026-10-30","2026-11-02","2026-11-03"})):
    j=json.load(open(rf"D:\ApexOptions\data\replay\batch\{run}\conductor_sim.json"))
    for d,v in j["days"].items():
        if (days is None and d in {"2026-10-28","2026-10-30","2026-11-02","2026-11-03"}) or (days is not None and d not in days): continue
        for t in v["trades"]:
            cs.append(dict(day=d,book=t["src"],t_in=t["t_in"],ret=t["ret_pct"],rr=t["rr"],time_in=t["time_in"],trig=t["trigger_t"],t_out=t["t_out"]))
C=pd.DataFrame(cs).sort_values(["day","t_in"]).reset_index(drop=True)
M=C.merge(T,on=["day","book","t_in"],how="left",suffixes=("","_T"))
print("trades",len(C),"joined",M["ret_pct"].notna().sum(), "ret match", np.nanmax(abs(M.ret-M.ret_pct)))
print(M[["wx_vwap_side_with","wx_basket_gap","wx_bank_z"]].describe(include="all").T[["count"]])
print(M.wx_vwap_side_with.value_counts(dropna=False).head())
M.to_pickle("cond.pkl"); C.to_pickle("cond_only.pkl")
