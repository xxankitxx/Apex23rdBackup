import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
t=pd.read_parquet('t_b.parquet'); c=pd.read_parquet('cond_b.parquet')
POOL=['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t']
EARLY=set(['2026-10-19','2026-10-21','2026-10-22','2026-10-23','2026-10-26','2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-11-02','2026-11-03','2026-11-04'])
def paired(x, flag, name):
    rows=[]
    for d,g in x.groupby('day'):
        a=g[flag.loc[g.index]]; b=g[~flag.loc[g.index]]
        if len(a)>=3 and len(b)>=3:
            rows.append(dict(day=d,nA=len(a),winA=(a.ret_pct>0).mean()*100,meanA=a.ret_pct.mean(),nB=len(b),winB=(b.ret_pct>0).mean()*100,meanB=b.ret_pct.mean()))
    r=pd.DataFrame(rows)
    if r.empty: print(name,'none'); return
    r['A_worse']=r.meanA<r.meanB; r['A_lower_win']=r.winA<r.winB
    e=r[r.day.isin(EARLY)]; l=r[~r.day.isin(EARLY)]
    print(f"{name}: days={len(r)} A worse mean on {r.A_worse.sum()} (early {e.A_worse.sum()}/{len(e)}, late {l.A_worse.sum()}/{len(l)}); A lower win on {r.A_lower_win.sum()}; "
          f"A n={r.nA.sum()} win={np.average(r.winA,weights=r.nA):.1f} mean={np.average(r.meanA,weights=r.nA):.2f} | B n={r.nB.sum()} win={np.average(r.winB,weights=r.nB):.1f} mean={np.average(r.meanB,weights=r.nB):.2f}")
    return r
for nm,x in [('ALL107',t),('POOL5',t[t.book.isin(POOL)])]:
    print('=====',nm)
    sg=np.where(x.rr=='CE',1,-1)
    paired(x, x.or30=='broken_against', 'or30 broken_against vs rest')
    paired(x, (((x.wx_or15_pos<0)&(sg>0))|((x.wx_or15_pos>1)&(sg<0))), 'or15 broken_against vs rest')
    paired(x, (x.gap_raw.abs()>=30)&(x.wx_gap_pts>0), 'with gap>=30 vs rest')
    paired(x, (x.gap_raw.abs()>=30)&(x.wx_gap_pts>0)&(x.wx_gap_filled==False), 'with gap unfilled vs rest')
    paired(x, (x.wx_dte==0)&(x.hm>=810), 'expiry >=13:30 vs rest (expiry days)')
    paired(x, x.hm<585, 'first 30 vs rest')
    paired(x, (x.hm>=585)&(x.hm<660), '09:45-11:00 vs rest')
    paired(x, x.hm>=870, '>=14:30 vs rest')
    paired(x, x.pdlvl=='beyond', 'beyond PDH/PDL vs rest')
    paired(x, x.wx_day_move<0, 'against day move vs with')
r=paired(t, t.or30=='broken_against','or30 all107 detail'); print(r.round(2).to_string())
r=paired(t[t.book.isin(POOL)], (t.wx_dte==0)&(t.hm>=810),'exp pm pool detail'); print(r.round(2).to_string())
