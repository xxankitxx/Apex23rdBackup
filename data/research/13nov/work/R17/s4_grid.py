import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R17")
import sim, guards as G, numpy as np, pandas as pd, json, itertools
df=sim.load()
base=sim.sim(df)
def stats(res, days, basres):
    ds=[d for d in days]
    n=sum(res[d]['n'] for d in ds); w=sum(res[d]['w'] for d in ds)
    dr={d:res[d]['ret_day'] for d in ds}
    tot=sum(dr.values())
    bestd=max(dr, key=dr.get)
    # best trade removed: divide its factor out of its day
    allt=[(d,x['ret']) for d in ds for x in res[d]['taken']]
    bt=max(allt,key=lambda z:z[1]) if allt else None
    tot_nbt=tot - dr[bt[0]] + 100*((1+dr[bt[0]]/100)/(1+bt[1]/100)-1) if bt else 0
    # blocked winners/losers relative to base (trades in base not in res)
    bidx={x['idx'] for d in ds for x in basres[d]['taken']}; ridx={x['idx'] for d in ds for x in res[d]['taken']}
    lost=[x for d in ds for x in basres[d]['taken'] if x['idx'] not in ridx]
    new=[x for d in ds for x in res[d]['taken'] if x['idx'] not in bidx]
    # top 10% base trades kept
    bt_all=sorted([x for d in ds for x in basres[d]['taken']], key=lambda x:-x['ret']); k=max(1,int(round(0.1*len(bt_all))))
    kept=sum(1 for x in bt_all[:k] if x['idx'] in ridx)/k
    return dict(n=n, sr=round(100*w/max(n,1),1), tot=round(tot,1), ldays=sum(v<0 for v in dr.values()), worst=round(min(dr.values()),1),
                no_best_day=round(tot-dr[bestd],1), no_best_tr=round(tot_nbt,1),
                lostW=sum(x['ret']>0 for x in lost), lostL=sum(x['ret']<0 for x in lost), new=len(new), top_kept=round(kept,2))
GR={}
for N in (1,2,3):
    for M in (10,20,30,60,999): GR[f'cool{N}L_{M}m']=G.cool_after_losses(N,M)
for K in (2,3,4,5): GR[f'maxloss{K}']=G.max_losses_day(K)
for X in (10,15,20,25,30): GR[f'daystop{X}']=G.day_stop(X)
for N in (1,2):
    for M in (20,30,60):
        for er in (0.05,0.08,0.12): GR[f'chopL{N}_{M}m_er{er}']=G.chop_after_losses(N,M,er)
for M in (5,10,20,30): GR[f'flipafterL_{M}m']=G.flip_after_loss(M); GR[f'sameafterL_{M}m']=G.same_after_loss(M); GR[f'anyafterL_{M}m']=G.any_after_loss(M)
for er in (0.03,0.05,0.08,0.12):
    GR[f'chopday{er}_s']=G.chop(er,True); GR[f'chopday{er}']=G.chop(er,False)
for er in (0.05,0.1,0.15): GR[f'chop60_{er}_s']=G.chop(er,True,'wx_er60')
for Y in (50,100,150,200): GR[f'against{Y}']=G.against_trend(Y); GR[f'against{Y}_er.1']=G.against_trend(Y,0.1)
for t in ('13:30','14:00','14:15','14:30'): GR[f'late{t}']=G.late(t)
for t in ('09:30','09:45'): GR[f'early{t}']=G.early(t)
for s in (0.25,0.3,0.35): GR[f'spread{s}']=G.spread(s)
for q in (0.8,1.0,1.5): GR[f'qage{q}']=G.quote_age(q)
for th in (-0.3,-0.15,0.0): GR[f'ivfall{th}']=G.iv_falling(th)
for th in (-3,-1,0): GR[f'stradflat{th}']=G.strad_flat(th)
rows=[]
for name,g in GR.items():
    r=sim.sim(df,g)
    e=stats(r,sim.EARLY,base); l=stats(r,sim.LATE,base)
    rows.append(dict(guard=name, **{'E_'+k:v for k,v in e.items()}, **{'L_'+k:v for k,v in l.items()}))
B=pd.DataFrame(rows)
b0e=stats(base,sim.EARLY,base); b0l=stats(base,sim.LATE,base)
print('BASE early',b0e); print('BASE late',b0l)
B.to_csv('grid1.csv',index=False)
pd.set_option('display.width',300); pd.set_option('display.max_rows',300)
print(len(GR),'variants')
cols=['guard','E_n','E_sr','E_tot','E_ldays','E_worst','E_no_best_day','E_lostW','E_lostL','E_top_kept','L_n','L_sr','L_tot','L_ldays','L_worst','L_no_best_day','L_lostW','L_lostL','L_top_kept']
print(B[cols].to_string())
