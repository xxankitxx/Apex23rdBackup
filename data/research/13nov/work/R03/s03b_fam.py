import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import os, json, re, time, numpy as np, pandas as pd
t0=time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R03"
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 60)
DT = pd.read_csv(os.path.join(W,"day_types.csv")).set_index("day")
BD = pd.read_csv(os.path.join(W,"book_day.csv"))
def fam2(b,f):
    if b=="spot_pb45_r002": return "spot 45-min pullback"
    if b in ("n01_ctl_flow","n01_ctl_price","n01_ctl_price_ind","n02_ctl_mr","n06_ctl_breadth","p02_ctl_mom","s01_ctl_cash","s01_ctl_sfut"): return "new-idea controls (n/p/s ctl)"
    if f in ("n01","n02","n06","p02","p05","s01","s03"): return "new-idea books (n/p/s)"
    if f=="apex": return "edge"
    return f
BD["fam"]=[fam2(b,f) for b,f in zip(BD.book,BD.fam)]
BD.to_csv(os.path.join(W,"book_day.csv"),index=False)
AC = pd.read_csv(os.path.join(W,"book_day_after_cp.csv"))
fm=BD.groupby("book")["fam"].first(); AC["fam"]=AC.book.map(fm); AC.to_csv(os.path.join(W,"book_day_after_cp.csv"),index=False)
DT["dtype"]=DT["shape"]
DT.loc[DT.gapk=="gap_go","dtype"]="gap_go"
DT.loc[DT.cal=="expiry","dtype"]=DT.loc[DT.cal=="expiry","dtype"]   # expiry kept as an overlay column
DT.to_csv(os.path.join(W,"day_types.csv"))
BD=BD.drop(columns=[c for c in ("shape","gapk","cal") if c in BD]).merge(DT[["shape","gapk","cal","dtype"]].reset_index(),on="day")
def fam_table(key):
    g = BD[BD.fam!="conductor"].groupby(["fam",key,"day"]).agg(ret=("ret","mean"),n=("n","sum"),w=("w","sum")).reset_index()
    t = g.groupby(["fam",key]).agg(days=("day","nunique"),mean_day_ret=("ret","mean"),pos_days=("ret",lambda s:int((s>0).sum())),trades=("n","sum"),wins=("w","sum")).reset_index()
    t["strike"]=100*t.wins/t.trades.replace(0,np.nan); return t
for key in ("dtype","shape","gapk","cal"):
    t=fam_table(key); t.to_csv(os.path.join(W,f"fam_by_{key}.csv"),index=False)
    print(f"\nFAMILY mean book-day return % by {key}  (days: {DT[key].value_counts().to_dict()})\n", t.pivot(index="fam",columns=key,values="mean_day_ret").round(1).to_string())
    print(f"\nFAMILY strike % by {key}\n", t.pivot(index="fam",columns=key,values="strike").round(0).to_string())
FD=BD[BD.fam!="conductor"].groupby(["fam","day"])["ret"].mean().unstack()
FD.round(1).to_csv(os.path.join(W,"fam_day.csv"))
FD.columns=[c[5:] for c in FD.columns]
print("\nFAMILY x DAY mean book-day %\n", FD.round(0).to_string())
# pool books by day
P=BD[BD.book.isin(["c20_9y","c20_9s","c20_9v","c20_9x","c20_9t","conductor"])].pivot(index="day",columns="book",values="ret").round(1)
cs=json.load(open(r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"))["days"]
csr=json.load(open(r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json"))["days"]
rows=[]
for d in DT.index:
    src=csr if d in ("2026-10-28","2026-10-30","2026-11-02","2026-11-03") else cs
    if d in src: x=src[d]; rows.append(dict(day=d,ship_n=x["n"],ship_w=x["wins"],ship_pnl=x["pnl_rs"],ship_ret=x["ret_day_pct"],occ_min=x.get("occupied_min")))
S=pd.DataFrame(rows).set_index("day")
P=P.join(S).join(DT[["dtype","cal","gapk"]])
P.to_csv(os.path.join(W,"pool_by_day.csv"))
print("\nPOOL books and shipped Conductor by day\n",P.to_string())
print(P.groupby("dtype").agg(days=("ship_ret","size"),mean=("ship_ret","mean"),med=("ship_ret","median"),pos=("ship_ret",lambda s:int((s>0).sum())),n=("ship_n","sum"),w=("ship_w","sum")).to_string())
print(round(time.time()-t0,1))
