import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, pandas as pd, numpy as np
df=sim.load(slim=False); res=sim.sim(df)
L=[];allt=[]
for d in sorted(res):
    tr=res[d]['taken']
    for k,x in enumerate(tr):
        r=df.loc[x['idx']]; p=tr[k-1] if k else None
        rec=dict(day=d,ret=x['ret'],reason=str(r.reason),book=x['book'],rr=x['rr'],prev_loss=bool(p and p['ret']<0),
                 flip=bool(p and p['rr']!=x['rr']), diffbook=bool(p and p['book']!=x['book']), gap=(x['trig']-p['t_out'])/60 if p else None,
                 hold=(x['t_out']-r.t_in)/60, mins=r.wx_mins_open)
        allt.append(rec)
A=pd.DataFrame(allt); Lo=A[A.ret<0]
print('trades',len(A),'losers',len(Lo),'sum of loser ret',round(Lo.ret.sum(),1),'sum of winner ret',round(A[A.ret>0].ret.sum(),1))
print('loser reasons'); print(Lo.reason.str.replace(r'\s*\(.*','',regex=True).value_counts().to_string())
print('losers -10 % or worse', (Lo.ret<=-10).sum(), 'mean hold of SL losers min', round(Lo[Lo.reason.str.contains('SL')].hold.mean(),1))
pl=A[A.prev_loss]
print('after a loss:',len(pl),'flip',pl.flip.sum(),'flip from a different book',(pl.flip&pl.diffbook).sum(),'same side',(~pl.flip).sum())
print('SR after loss flip', round(100*(pl[pl.flip].ret>0).mean(),1), 'same side', round(100*(pl[~pl.flip].ret>0).mean(),1))
print('top 10 trades and what came before:')
for _,x in A.sort_values('ret',ascending=False).head(12).iterrows(): print(x.day[5:], round(x.ret,1), 'prev_loss', x.prev_loss, 'gap', None if x.gap is None else round(x.gap,1), 'mins', x.mins)
# day anatomy: path sensitivity — 9 Nov day % across guard variants already seen; record losing day trades
for d in ['2026-11-03','2026-11-04','2026-10-30','2026-11-05','2026-11-12']:
    print(d, [(x['book'][-2:],x['rr'],round(x['ret'],1)) for x in res[d]['taken']])
