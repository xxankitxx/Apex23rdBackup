import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import pandas as pd, numpy as np
p=r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
df=pd.read_parquet(p,columns=['day','book','t_in','t_out','trigger_t','ret_pct','time_in'])
df['lr']=np.log1p(df.ret_pct.clip(lower=-99)/100)
CTL={'conductor','futures_only','random_entry','premium_momentum'}
d=df[~df.book.isin(CTL)]
bd=d.groupby(['book','day']).lr.sum().unstack().fillna(0)  # per-book day log-return (book's own sequence)
days=list(bd.columns)
print('days',days)
# rank persistence day to next day
from scipy.stats import spearmanr
rs=[]
for a,b in zip(days[:-1],days[1:]):
    r=spearmanr(bd[a],bd[b]).correlation; rs.append(r); print(a,b,round(r,3))
print('mean next-day spearman',np.mean(rs))
# trailing 3-day mean vs next day
rs3=[]
for i in range(3,len(days)):
    r=spearmanr(bd[days[i-3:i]].mean(1),bd[days[i]]).correlation; rs3.append(r)
print('trailing3 -> next', np.round(rs3,2), np.mean(rs3))
rsall=[]
for i in range(3,len(days)):
    r=spearmanr(bd[days[:i]].mean(1),bd[days[i]]).correlation; rsall.append(r)
print('expanding -> next', np.round(rsall,2), np.mean(rsall))
# intraday: trades triggered before 12:00 vs after, per book per day
d=d.copy(); d['hr']=pd.to_datetime(d.trigger_t.fillna(d.t_in),unit='s',utc=True).dt.tz_convert('Asia/Kolkata').dt.hour+pd.to_datetime(d.trigger_t.fillna(d.t_in),unit='s',utc=True).dt.tz_convert('Asia/Kolkata').dt.minute/60
am=d[d.hr<11.5].groupby(['day','book']).lr.sum(); pm=d[d.hr>=11.5].groupby(['day','book']).lr.sum()
j=pd.concat([am,pm],axis=1,keys=['am','pm']).dropna()
print('intraday pooled spearman am->pm',spearmanr(j.am,j.pm).correlation, len(j))
for day,g in j.groupby(level=0):
    print(day,len(g),round(spearmanr(g.am,g.pm).correlation,3))
bd.to_pickle('bookday_lr.pkl')
