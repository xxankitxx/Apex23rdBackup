import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_rows',200); pd.set_option('display.max_columns',40)
df=sim.load(); res=sim.sim(df)
rows=[]
for d in sorted(res):
    prev=[]
    for x in res[d]['taken']:
        r=df.loc[x['idx']]
        nl=0
        for p in reversed(prev):
            if p['ret']<0: nl+=1
            else: break
        side=1 if r.rr=='CE' else -1
        rows.append(dict(day=d[5:],t=r.time_in[-8:-3] if isinstance(r.time_in,str) else '',book=r.book[-2:],rr=r.rr,ret=round(r.ret_pct,1),
            nprev=len(prev),lossrun=nl, since_last=round((x['trig']-prev[-1]['t_out'])/60,1) if prev else None,
            last_ret=prev[-1]['ret'] if prev else None, same_side_last=(prev[-1]['rr']==r.rr) if prev else None,
            er60=r.wx_er60, erd=r.wx_er_day, chop60=r.wx_chop60, sexp=r.wx_strad_expanding, sch5=r.wx_strad_chg5,
            daymv=r.wx_day_move*side if pd.notna(r.wx_day_move) else None, mv30=r.wx_mv30*side if pd.notna(r.wx_mv30) else None,
            spr=r.wx_spread_pct, qa=r.wx_quote_age, div=(r.iv_out-r.iv_in) if pd.notna(r.iv_out) else None, mins=r.wx_mins_open,
            hold=round((r.t_out-r.t_in)/60,1), reason=str(r.reason)[:14], rvn=r.wx_rv5_vs_norm, rng=r.wx_range_vs_norm, dte=r.dte_in))
        prev.append(x)
T=pd.DataFrame(rows)
T.to_pickle(r"D:\ApexOptions\data\research\13nov\work\R17\cond_trades.pkl")
print(T.to_string())
