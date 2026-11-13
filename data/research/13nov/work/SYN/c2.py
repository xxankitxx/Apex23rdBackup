import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
M=pd.read_pickle("cond.pkl")
P=r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
A=pd.read_parquet(P,columns=["day","book","rr","trigger_t","t_out","ret_pct"])
M["d"]=np.where(M.rr=="CE",1,-1)
late=M.day>="2026-11-05"
R={}
R["pm1330"]=(M.dte_in==0)&(M.time_in>="13:30:00")
R["vwap_against"]=~M.wx_vwap_side_with.astype(bool)
R["futled_gap1.6"]=M.wx_basket_gap>1.6
R["bank_z<-0.5"]=M.wx_bank_z<-0.5
R["R04A_none<0.0197"]=M.wx_sign_none_share300<0.0197
R["with_gap_unfilled"]=(M.wx_gap_pts>=30)&(M.wx_gap_filled==False)
orb=M.wx_or30_pos
R["or30_broken_against"]=((M.d==1)&(orb<0))|((M.d==-1)&(orb>1))
# whipsaw 60: on actual sequence, skip-only cascade
w=np.zeros(len(M),bool)
for day,g in M.groupby("day"):
    taken=[]
    for i,r in g.iterrows():
        if len(taken)>=2:
            a,b=taken[-2],taken[-1]
            if a.ret<0 and b.ret<0 and a.rr!=b.rr and r.trig-b.t_out<=3600:
                w[i]=True; continue
        taken.append(r)
R["whipsaw60"]=pd.Series(w,index=M.index)
# confirmation: other family same side within 300 s before trigger
fam=A.book.str.extract(r"^(t28|lvl_trail|spot|edge)")[0]
O=A[fam.notna()]
conf=[]
for i,r in M.iterrows():
    o=O[(O.day==r.day)&(O.rr==r.rr)&(O.trigger_t<=r.trig)&(O.trigger_t>=r.trig-300)]
    conf.append(len(o)>0)
R["not_confirmed300"]=~pd.Series(conf,index=M.index)
# side lock N=12
c20=["c20_9y","c20_9s","c20_9v","c20_9x","c20_9t","c20_9h","c20_9e","c20_8x","c20_9x_r002","c20_9x_r004","fr_c20_9y","rx_c20_9y","fx_c20_9y"]
F=A[A.book.isin(c20)]
sl=[]
for i,r in M.iterrows():
    f=F[(F.day==r.day)&(F.rr==r.rr)&(F.t_out<r.trig)].sort_values("t_out").tail(12)
    sl.append(len(f)>=3 and (f.ret_pct<0).sum()>(f.ret_pct>0).sum())
R["sidelock12"]=pd.Series(sl,index=M.index)
def acct(mask):
    out={}
    for win,sel in (("early",~late),("late",late)):
        k=M[sel&~mask]; s=M[sel&mask]
        days=M[sel].day.unique()
        dr=[ (np.prod(1+k[k.day==d].ret/100)-1)*100 for d in days]
        out[win]=dict(kept=len(k),sr=round(100*(k.ret>0).mean(),1),sum=round(sum(dr),1),lose=int(sum(x<0 for x in dr)),worst=round(min(dr),1),
                      cutW=int((s.ret>0).sum()),cutL=int((s.ret<=0).sum()),cut_sumret=round(s.ret.sum(),1))
    return out
base=acct(pd.Series(False,index=M.index))
print("BASE",base)
rows=[]
for k,m in R.items():
    a=acct(m.fillna(False).astype(bool))
    days=M[m.fillna(False).astype(bool)].groupby("day").ret.agg(["count","sum"]).round(1)
    rows.append([k]+[a[w][x] for w in ("early","late") for x in ("kept","sr","sum","lose","worst","cutW","cutL")])
    print(k, "cut by day:", dict(zip(days.index.str[5:], [f"{int(c)}/{s}" for c,s in days.values])))
df=pd.DataFrame(rows,columns=["rule"]+[f"{w}_{x}" for w in ("E","L") for x in ("kept","sr","sum","lose","worst","cutW","cutL")])
pd.set_option("display.width",250); print(df.to_string(index=False))
# overlap of losers cut (>=-5%)
big=M.ret<=-5
names=list(R); mat=pd.DataFrame(index=names,columns=names,dtype=float)
for a in names:
    for b in names:
        x=R[a].fillna(False)&big; y=R[b].fillna(False)&big
        mat.loc[a,b]=round((x&y).sum()/max(1,(x|y).sum()),2)
print("losers <= -5%:",int(big.sum()))
print(mat.to_string())
# which big losers are cut by none of the rules
anyr=np.zeros(len(M),bool)
for m in R.values(): anyr|=m.fillna(False).values
print("big losers cut by no rule:",int((big&~anyr).sum()),"of",int(big.sum()))
print("count of rules cutting each big loser:",np.bincount(sum(R[k].fillna(False).astype(int) for k in R)[big]))
print("top10 winners cut by #rules:", sum(R[k].fillna(False).astype(int) for k in R)[M.ret.nlargest(10).index].tolist(), M.ret.nlargest(10).round(1).tolist())
