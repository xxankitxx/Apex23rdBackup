import numpy as np, pandas as pd
PRIO={'c20_9y':0,'c20_9s':1,'c20_9v':2,'c20_9x':3,'c20_9t':4}
EARLY=['2026-10-19','2026-10-21','2026-10-22','2026-10-23','2026-10-26','2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-11-02','2026-11-03','2026-11-04']
LATE=['2026-11-05','2026-11-06','2026-11-09','2026-11-11','2026-11-12']
def run(pool, mask=None):
    x=pool if mask is None else pool[np.asarray(mask,bool)]
    pr=x.book.map(PRIO).to_numpy()
    o=np.lexsort((pr, x.trigger_t.to_numpy(), x.day.to_numpy()))
    D=x.day.to_numpy()[o]; TR=x.trigger_t.to_numpy()[o]; TO=x.t_out.to_numpy()[o]; IX=x.index.to_numpy()[o]
    out=[]; cd=None; ht=None; ho=-1
    for k in range(len(o)):
        if D[k]!=cd: cd=D[k]; ht=None; ho=-1
        if ht is not None and (TR[k]<=ht or TR[k]<ho): continue
        out.append(IX[k]); ht=TR[k]; ho=TO[k]
    return pool.loc[out]
def dayret(tk, dl):
    r={d:[0,0,1.0] for d in dl}
    for d,v in zip(tk.day.to_numpy(), tk.ret_pct.to_numpy()):
        if d in r: r[d][0]+=1; r[d][1]+=v>0; r[d][2]*=1+v/100
    return pd.DataFrame({'n':[r[d][0] for d in dl],'wins':[r[d][1] for d in dl],'ret':[(r[d][2]-1)*100 for d in dl]},index=dl)
def days(tk, dl): return dayret(tk, dl)
def summ(tk, dl):
    tk=tk[tk.day.isin(dl)]; r=dayret(tk, dl); n=len(tk)
    w=(tk.ret_pct>0).mean()*100 if n else np.nan
    sday=r.ret.sum()
    wobt=dayret(tk.drop(tk.ret_pct.idxmax()),dl).ret.sum() if n else 0
    return dict(n=n,win=round(w,1),sum_day_pct=round(sday,1),mean_day=round(r.ret.mean(),1),lose_days=int((r.ret<0).sum()),
                worst_day=round(r.ret.min(),1),best_day=round(r.ret.max(),1),wo_best_trade=round(wobt,1),wo_best_day=round(sday-r.ret.max(),1))
