import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R18"); import sim
t=pd.read_parquet('t_b.parquet')
P=t[t.book.isin(sim.PRIO)].copy(); P['trigger_t']=P.trigger_t.fillna(P.t_in)
hm=P.hm; d0=P.wx_dte==0
R={'base':pd.Series(True,index=P.index),
 'exp_cut_1330':~(d0&(hm>=810)),'exp_cut_1400':~(d0&(hm>=840)),
 'gap_with_unfilled':~((P.gap_raw.abs()>=30)&(P.wx_gap_pts>0)&(P.wx_gap_filled==False)),
 'gap_with_30':~((P.gap_raw.abs()>=30)&(P.wx_gap_pts>0)),
 'orb30_against':P.or30!='broken_against'}
R['exp1330+gapunf']=R['exp_cut_1330']&R['gap_with_unfilled']
R['exp1330+orb30']=R['exp_cut_1330']&R['orb30_against']
alld=sorted(P.day.unique())
cols={}
for k,m in R.items():
    tk=sim.run(P,m); r=sim.dayret(tk,alld)
    cols[k]=r.ret.round(1).astype(str)+' ('+r.n.astype(int).astype(str)+'/'+r.wins.astype(int).astype(str)+')'
    if k!='base':
        s=sim.summ(tk,alld); print(k,'ALL17',s)
    else: print('base ALL17',sim.summ(tk,alld))
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(pd.DataFrame(cols).to_string())
# which trades does the expiry cut remove from the base account?
b=sim.run(P)
x=b[(b.wx_dte==0)&(b.hm>=810)][['day','book','time_in','rr','ret_pct','reason']]
print(x.to_string())
g=b[(b.gap_raw.abs()>=30)&(b.wx_gap_pts>0)&(b.wx_gap_filled==False)][['day','book','time_in','rr','gap_raw','ret_pct','reason']]
print(g.to_string())
