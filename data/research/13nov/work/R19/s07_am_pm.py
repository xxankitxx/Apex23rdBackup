import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19"); import harness as H
import numpy as np, pandas as pd
from scipy import stats
df=H.load()
days=sorted(df.day.unique()); post=[d for d in days if d>="2026-10-30"]
pool=df[df.book.isin(H.POOL)]
c=H.conductor(pool,days=days)
noon=df.day.map(lambda d: pd.Timestamp(d+" 06:30:00", tz="UTC").timestamp())  # 12:00 IST
df["noon"]=noon
am=df[df.t_out<df.noon]
am_sig=am.groupby("day").ret_pct.mean()
am_win=am.groupby("day").win.mean()
pm={}
for d in days:
    tk=[i for i in c[d][1] if pool.at[i,"trig"]>=df[df.day==d].noon.iloc[0]]
    pm[d]=100*(np.prod(1+pool.loc[tk,"ret_pct"]/100)-1) if tk else 0.0
pm=pd.Series(pm)
t=pd.DataFrame({"am_all_books_mean":am_sig,"am_win":am_win,"pm_cond":pm}).round(2)
print(t)
for sel,lab in [(days,"all"),(post,"post")]:
    s=stats.spearmanr(t.loc[sel,"am_all_books_mean"],t.loc[sel,"pm_cond"]); print(lab,"am mean vs pm",round(s.statistic,2),round(s.pvalue,3))
    s=stats.spearmanr(t.loc[sel,"am_win"],t.loc[sel,"pm_cond"]); print(lab,"am win vs pm",round(s.statistic,2),round(s.pvalue,3))
# pre-declared rule: stand down after noon if am all-book mean < 0
for sel,lab in [(days,"all"),(post,"post")]:
    x=t.loc[sel]; bad=x.am_all_books_mean<0
    print(lab,"pm when am<0:",x.pm_cond[bad].round(1).tolist(),"| pm when am>=0:",x.pm_cond[~bad].round(1).tolist())
cd=pd.Series({d:c[d][0] for d in days})
sd=cd[post].std(ddof=1); mu=cd[post].mean()
print("post mean",round(mu,1),"sd",round(sd,1),"days for t=2:",round((2*sd/mu)**2,0))
lg=np.log1p(cd[post]/100); print("log mean",round(lg.mean(),3),"log sd",round(lg.std(ddof=1),3),"days for t=2 (log):",round((2*lg.std(ddof=1)/lg.mean())**2,0))
# per-trade tail concentration
tk=pool.loc[[i for d in days for i in c[d][1]]]
for sel,lab in [(days,"all"),(post,"post")]:
    r=tk[tk.day.isin(sel)].ret_pct.sort_values(ascending=False)
    lr=np.log1p(r/100); top=max(1,int(round(0.1*len(r))))
    print(lab,"n",len(r),"win",round((r>0).mean(),2),"mean",round(r.mean(),2),"median",round(r.median(),2),"top10% share of log growth",round(lr.iloc[:top].sum()/lr.sum(),2), "p90",round(r.quantile(.9),1))

