import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import numpy as np, pandas as pd
M=pd.read_pickle("cond.pkl")
pk=(M.peak_bid/M.entry-1)*100; r=M.ret.values.copy(); e=(M.dte_in==0).values
print("expiry trades",e.sum(),"peak>=30",int((e&(pk>=30)).sum()),"peak>=60",int((e&(pk>=60)).sum()), "peak nan",int(pk.isna().sum()))
def tp(r0,lvl=60):
    r1=r0.copy(); m=e&(pk.values>=lvl); r1[m]=lvl; return r1
def floor(r0,keep=0.6,arm=30,cap=None,bound="up"):
    r1=r0.copy()
    for i in np.where(e&(pk.values>=arm))[0]:
        p=pk.values[i] if cap is None else min(pk.values[i],cap)
        lvl=keep*p
        if bound=="up":
            if r1[i]<lvl: r1[i]=lvl
        else:  # pessimistic: floor fired at the earliest possible level keep*arm
            if r1[i]<keep*arm: r1[i]=keep*arm
            elif r1[i]>keep*arm and r0[i]<lvl: r1[i]=keep*arm
            elif r0[i]>=lvl: r1[i]=min(r0[i],keep*arm) if False else r0[i]
    return r1
def summ(rr,label):
    out=[label]
    for w,sel in (("E",M.day<"2026-11-05"),("L",M.day>="2026-11-05")):
        g=M[sel].assign(r=rr[sel.values])
        dr=g.groupby("day").r.apply(lambda x:(np.prod(1+x/100)-1)*100)
        out+= [f"{w}: SR {100*(g.r>0).mean():.1f} sum {dr.sum():.1f} lose {(dr<0).sum()} worst {dr.min():.1f}"]
    ex=M[e].assign(r=rr[e]).groupby("day").r.apply(lambda x:(np.prod(1+x/100)-1)*100).round(1)
    out.append("expiry days "+str(dict(zip(ex.index.str[5:],ex.values))))
    print(" | ".join(out))
summ(r,"base")
summ(tp(r),"TP60")
summ(floor(r),"floor .6/30 upper")
summ(floor(r,bound="lo"),"floor .6/30 lower")
summ(floor(tp(r),cap=60),"TP60+floor upper")
summ(floor(tp(r),cap=60,bound="lo"),"TP60+floor lower")
for i in np.where(e&(pk.values>=30))[0]:
    print(M.day[i][5:],M.time_in[i],M.rr[i],"peak",round(pk.values[i],1),"ret",round(r[i],1))
