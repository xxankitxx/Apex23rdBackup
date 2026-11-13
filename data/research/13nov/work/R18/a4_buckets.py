import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
pd.set_option('display.width',200); pd.set_option('display.max_columns',30)
c=pd.read_parquet('cond_wx.parquet'); t=pd.read_parquet('t_small.parquet')
POOL=['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t']
def prep(x):
    x=x.copy()
    hm=x.time_in.str.slice(0,2).astype(int)*60+x.time_in.str.slice(3,5).astype(int)
    x['hm']=hm
    x['tb']=pd.cut(hm,[0,9*60+45,11*60,13*60,14*60+30,24*60],right=False,labels=['a0915','b0945','c1100','d1300','e1430'])
    x['first30']=np.where(hm<9*60+45,'first30','rest')
    sg=np.where(x.rr=='CE',1,-1)
    x['gap_raw']=x.wx_gap_pts*sg
    x['gapc']=pd.cut(x.gap_raw.abs(),[-1,30,150,1e4],labels=['flat<30','mid30-150','big>150'])
    x['gapdir']=np.where(x.gap_raw.abs()<30,'flat',np.where(x.wx_gap_pts>0,'with_gap','against_gap'))
    x['dteb']=pd.cut(x.wx_dte,[-1,0,1,4,9],labels=['0','1','2-4','5-6'])
    p=x.wx_or30_pos
    x['or30']=np.where(p.isna(),'na',np.where(((p>1)&(sg>0))|((p<0)&(sg<0)),'broken_with',np.where(((p<0)&(sg>0))|((p>1)&(sg<0)),'broken_against','inside')))
    room=np.where(sg>0,x.wx_to_pdh,-x.wx_to_pdl)  # >0 = level still ahead
    x['room_pd']=room
    x['pdlvl']=pd.cut(pd.Series(room,index=x.index),[-1e5,0,50,150,1e5],labels=['beyond','<50 ahead','50-150','>150'])
    x['win']=x.ret_pct>0
    x['lr']=np.log1p(x.ret_pct/100)
    return x
def tab(x,g):
    r=x.groupby(g,observed=True).agg(n=('ret_pct','size'),days=('day','nunique'),win=('win','mean'),mean=('ret_pct','mean'),med=('ret_pct','median'),comp=('lr','sum'))
    r['win']=(r.win*100).round(0); r['comp']=((np.exp(r.comp)-1)*100).round(1); r['mean']=r['mean'].round(2); r['med']=r.med.round(2)
    return r
c=prep(c); t=prep(t); pl=t[t.book.isin(POOL)]
c.to_parquet('cond_b.parquet'); t.to_parquet('t_b.parquet')
for name,x in [('CONDUCTOR',c),('POOL5',pl),('ALL107',t)]:
    print('=====',name,len(x))
    for g in ['tb','first30','gapc','gapdir','dteb','or30','pdlvl','wx_gap_filled','wx_day_before_expiry']:
        print(tab(x,g)); print()
# conductor per-day x bucket
print(c.pivot_table(index='day',columns='tb',values='ret_pct',aggfunc='sum',observed=True).round(1))
print(c.pivot_table(index='day',columns='tb',values='ret_pct',aggfunc='count',observed=True))
