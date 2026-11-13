import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R18"); import sim
exec(open('a6_wf.py').read().split("alld=sorted")[0].split("import sim\n",1)[1])   # builds P and R (56 rules)
alld=sorted(P.day.unique())
D={}
for k,m in R.items():
    tk=sim.run(P,m); r=sim.dayret(tk,alld); D[k]=r
rows=[]
for K in range(6,len(alld)):
    tr=alld[:K]; te=alld[K]
    b=D['base'].loc[tr]; bw=b.wins.sum()/max(b.n.sum(),1); bs=b.ret.sum(); bwo=bs-b.ret.max(); bworst=b.ret.min()
    best=('base',0.0)
    for k,r in D.items():
        x=r.loc[tr]; w=x.wins.sum()/max(x.n.sum(),1); s=x.ret.sum()
        # owner-style: strike rate no lower, positive and no worse without best day, worst day no worse
        if k=='base' or w<bw or (s-x.ret.max())<bwo or x.ret.min()<bworst: continue
        sc=s-bs
        if sc>best[1]: best=(k,sc)
    ch=best[0]
    rows.append(dict(test_day=te,chosen=ch,base_ret=round(D['base'].loc[te,'ret'],1),chosen_ret=round(D[ch].loc[te,'ret'],1),
                     base_n=int(D['base'].loc[te,'n']),base_w=int(D['base'].loc[te,'wins']),ch_n=int(D[ch].loc[te,'n']),ch_w=int(D[ch].loc[te,'wins'])))
df=pd.DataFrame(rows); print(df.to_string())
print('sum base',df.base_ret.sum().round(1),'sum chosen',df.chosen_ret.sum().round(1),'lose days base',(df.base_ret<0).sum(),'chosen',(df.chosen_ret<0).sum(),
      'win base',round(df.base_w.sum()/df.base_n.sum()*100,1),'chosen',round(df.ch_w.sum()/df.ch_n.sum()*100,1))
df.to_csv('rolling_wf.csv',index=False)
