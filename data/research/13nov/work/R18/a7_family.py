import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R18"); import sim
t=pd.read_parquet('t_b.parquet'); t['trigger_t']=t.trigger_t.fillna(t.t_in)
# give all books a priority by early-days mean ret (discovered on EARLY only)
e=t[t.day.isin(sim.EARLY)].groupby('book').ret_pct.mean().sort_values(ascending=False)
sim.PRIO=dict({b:i for i,b in enumerate(e.index)})
t=t[t.book.isin(sim.PRIO)]
hm=t.hm; d0=t.wx_dte==0
fam={}
od=(hm<585)
fam['OD_all']=od
fam['OD_mv300_with']=od&(t.wx_mv300>0)
fam['OD_or15_with']=od&(((t.wx_or15_pos>1)&(t.rr=='CE'))|((t.wx_or15_pos<0)&(t.rr=='PE')))
fam['OD_daymove_with']=od&(t.wx_day_move>0)
fam['OD_against_gap']=od&(t.wx_gap_pts<0)
fam['OD_with_gap']=od&(t.wx_gap_pts>0)
fam['OD_with_gap_unfilled']=od&(t.wx_gap_pts>0)&(t.wx_gap_filled==False)
fam['OD_against_gap_daywith']=od&(t.wx_gap_pts<0)&(t.wx_day_move>0)
lh=(hm>=885)&(hm<915)
fam['LH_all']=lh
for x in [0.2,0.3,0.4]:
    fam[f'LH_daywith_er{x}']=lh&(t.wx_day_move>0)&(t.wx_er_day>=x)
fam['LH_daywith']=lh&(t.wx_day_move>0)
fam['LH_dayagainst']=lh&(t.wx_day_move<0)
fam['LH_mv300_with']=lh&(t.wx_mv300>0)
fam['LH_or30_with']=lh&(t.or30=='broken_with')
rows=[]
for k,m in fam.items():
    tk=sim.run(t,m)
    a=sim.summ(tk,sim.EARLY); b=sim.summ(tk,sim.LATE)
    # also raw trade-level stats
    raw=t[m]
    re=raw[raw.day.isin(sim.EARLY)]; rl=raw[raw.day.isin(sim.LATE)]
    rows.append(dict(rule=k,raw_E_n=len(re),raw_E_win=round((re.ret_pct>0).mean()*100,1),raw_E_mean=round(re.ret_pct.mean(),2),
      raw_L_n=len(rl),raw_L_win=round((rl.ret_pct>0).mean()*100,1),raw_L_mean=round(rl.ret_pct.mean(),2),
      **{'E_'+x:y for x,y in a.items() if x in('n','win','sum_day_pct','lose_days','worst_day')},**{'L_'+x:y for x,y in b.items() if x in('n','win','sum_day_pct','lose_days','worst_day')}))
df=pd.DataFrame(rows); df.to_csv('wf_family.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(df.to_string())
# raw: expiry-day trades by half-hour after 12:00, pool5 and all books
t2=pd.read_parquet('t_b.parquet')
t2['hh']=(t2.hm//30*30).map(lambda m:f"{m//60:02d}:{m%60:02d}")
for nm,x in [('POOL5',t2[t2.book.isin(['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t'])]),('ALL',t2)]:
    y=x[x.wx_dte==0]
    g=y.groupby('hh').agg(n=('ret_pct','size'),win=('win','mean'),mean=('ret_pct','mean'),sl=('reason',lambda s:s.str.contains('SL').mean()))
    g['win']=(g.win*100).round(0); g['sl']=(g.sl*100).round(0); g['mean']=g['mean'].round(2)
    print(nm,'expiry days by half hour'); print(g.to_string())
    y=x[x.wx_dte!=0]
    g=y.groupby('hh').agg(n=('ret_pct','size'),win=('win','mean'),mean=('ret_pct','mean'))
    g['win']=(g.win*100).round(0); g['mean']=g['mean'].round(2)
    print(nm,'normal days by half hour'); print(g.to_string())
    # per expiry day after 13:30
    z=x[(x.wx_dte==0)]
    print(z.assign(pm=z.hm>=810).groupby(['day','pm']).agg(n=('ret_pct','size'),win=('win','mean'),mean=('ret_pct','mean')).round(2).to_string())
