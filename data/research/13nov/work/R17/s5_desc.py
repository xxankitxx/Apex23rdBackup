import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, pandas as pd, numpy as np
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
        rows.append(dict(day=d, win=x['ret']>0, ret=x['ret'], lossrun=min(nl,3), prevres=('none' if not prev else 'W' if prev[-1]['ret']>0 else 'L'),
          gap=(x['trig']-prev[-1]['t_out'])/60 if prev else np.nan, flip=(prev[-1]['rr']!=r.rr) if prev else None,
          mins=r.wx_mins_open, erd=r.wx_er_day, er60=r.wx_er60, sexp=r.wx_strad_expanding, dmv=r.wx_day_move, spr=r.wx_spread_pct, qa=r.wx_quote_age,
          ivc=r.wx_atm_iv_chg5, div=(r.iv_out-r.iv_in) if pd.notna(r.iv_out) and pd.notna(r.iv_in) else np.nan, dte=r.wx_dte, late=d in sim.LATE, ntoday=len(prev),
          dayret=100*(prev[-1]['cap']/1e5-1) if prev else 0.0))
        prev.append(x)
T=pd.DataFrame(rows); T.to_pickle('cond_T.pkl')
def tab(col, bins=None, labels=None):
    s=T[col] if bins is None else pd.cut(T[col],bins,labels=labels)
    g=T.groupby(s,observed=True).agg(n=('ret','size'),sr=('win','mean'),mean=('ret','mean'),med=('ret','median'))
    g['sr']=(100*g.sr).round(0); print('\n==',col); print(g.round(2).to_string())
    gl=T.groupby([s,'late'],observed=True).agg(n=('ret','size'),sr=('win','mean'),mean=('ret','mean')); gl['sr']=(100*gl.sr).round(0); print(gl.round(2).unstack().to_string())
tab('prevres'); tab('lossrun')
T['gapb']=pd.cut(T.gap,[0,5,10,20,40,999]); tab('gapb')
T['pl_gap']=np.where(T.prevres=='L', pd.cut(T.gap,[0,5,10,20,999]).astype(str),'n/a'); tab('pl_gap')
T['pl_flip']=np.where(T.prevres=='L', T.flip.astype(str),'n/a'); tab('pl_flip')
tab('mins',[0,30,60,120,180,240,300,400])
tab('erd',[0,0.03,0.05,0.08,0.12,0.2,1])
tab('er60',[0,0.05,0.1,0.15,0.25,1])
tab('sexp')
tab('dmv',[-999,-150,-50,0,50,150,999])
tab('spr',[0,0.15,0.2,0.25,0.3,1])
tab('qa',[0,0.3,0.6,1.0,5])
tab('ivc',[-9,-0.3,-0.1,0,0.1,0.3,9])
tab('div',[-9,-1,-0.3,0,0.3,1,9])
tab('dte',[-1,0.5,2.5,9])
tab('ntoday',[-1,0,2,5,10,30])
tab('dayret',[-99,-10,-0.01,0.01,20,100,9999])
# markov
print(pd.crosstab(T.prevres,T.win,margins=True))
# loss-day anatomy
for d in sorted(res):
    if res[d]['ret_day']<0:
        print(d, [round(x['ret'],1) for x in res[d]['taken']])
