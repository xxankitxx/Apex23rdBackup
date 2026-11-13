import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np, json
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R18"); import sim
t=pd.read_parquet('t_b.parquet')
pool=t[t.book.isin(sim.PRIO)].copy(); pool['trigger_t']=pool.trigger_t.fillna(pool.t_in)
P=pool; hm=P.hm; sg=np.where(P.rr=='CE',1,-1); d0=P.wx_dte==0
p15=P.wx_or15_pos
o15_ag=((p15<0)&(sg>0))|((p15>1)&(sg<0))
R={}
R['base']=pd.Series(True,index=P.index)
for b in ['a0915','b0945','c1100','d1300','e1430']: R['skip_'+b]=P.tb!=b
for s in [556,570,585,600,630]:
    for e in [780,840,870,900,915]:
        R[f'win_{s//60:02d}{s%60:02d}_{e//60:02d}{e%60:02d}']=(hm>=s)&(hm<e)
R['orb30_veto_against']=P.or30!='broken_against'
R['orb30_veto_against_norm']=~((P.or30=='broken_against')&~d0)
R['orb30_veto_against_exp']=~((P.or30=='broken_against')&d0)
R['orb15_veto_against']=~o15_ag
R['orb30_need_with']=P.or30.isin(['broken_with','na'])
for G in [30,75,150]: R[f'gap_veto_with_{G}']=~((P.gap_raw.abs()>=G)&(P.wx_gap_pts>0))
R['gap_veto_with_unfilled']=~((P.gap_raw.abs()>=30)&(P.wx_gap_pts>0)&(P.wx_gap_filled==False))
R['gap_veto_with_filled']=~((P.gap_raw.abs()>=30)&(P.wx_gap_pts>0)&(P.wx_gap_filled==True))
R['gap_bigday_off']=P.gap_raw.abs()<150
R['gap_veto_against_30']=~((P.gap_raw.abs()>=30)&(P.wx_gap_pts<0))
R['pd_veto_beyond']=P.pdlvl!='beyond'
R['pd_veto_lt50']=P.pdlvl!='<50 ahead'
R['pd_veto_beyond_lt50']=~P.pdlvl.isin(['beyond','<50 ahead'])
for e in [690,780,810,840]: R[f'exp_cut_{e//60:02d}{e%60:02d}']=~(d0&(hm>=e))
R['exp_skip_first30']=~(d0&(hm<585))
R['norm_skip_first30']=~(~d0&(hm<585))
R['dte56_off']=P.wx_dte<5
R['combo_orb30_gap30']=R['orb30_veto_against']&R['gap_veto_with_30']
R['combo_orb30_pd']=R['orb30_veto_against']&R['pd_veto_beyond']
R['combo_orb30_gap30_pd']=R['combo_orb30_gap30']&R['pd_veto_beyond']
alld=sorted(t.day.unique())
rows=[]
for k,m in R.items():
    tk=sim.run(P,m)
    e=sim.summ(tk,sim.EARLY); l=sim.summ(tk,sim.LATE)
    rows.append(dict(rule=k,**{'E_'+a:b for a,b in e.items()},**{'L_'+a:b for a,b in l.items()}))
df=pd.DataFrame(rows); df.to_csv('wf_rules.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',200); pd.set_option('display.max_columns',30)
print(len(R),'variants')
print(df[['rule','E_n','E_win','E_sum_day_pct','E_lose_days','E_worst_day','E_wo_best_day','L_n','L_win','L_sum_day_pct','L_lose_days','L_worst_day','L_wo_best_day']].to_string())
