"""Conductor account re-simulation from the c20 pool trades with yes/no guards (mirrors apex/conductor/account_sim.py)."""
import pandas as pd, numpy as np, json
ORDER=['c20_9y','c20_9s','c20_9v','c20_9x','c20_9t']   # pool priority: all 'low', ret_per_trade desc
PRI={b:i for i,b in enumerate(ORDER)}
LOT=None
KEEP=None
_CACHE=None
_LC=None
def lot_size():
    global _LC
    if _LC: return _LC
    import sys; sys.path.insert(0, r"D:\ApexOptions")
    from apex import config
    _LC=(config.LOT_SIZE, float(config.START_CAPITAL)); return _LC
def load(pool_only=True, slim=True):
    df=pd.read_pickle(r"D:\ApexOptions\data\research\13nov\work\R17\c20.pkl")
    df['trig']=df['trigger_t'].where(df['trigger_t'].notna(), df['t_in']).astype(float)
    df['pri']=df['book'].map(PRI)
    if pool_only: df=df[df.book.isin(ORDER)]
    df=df.sort_values(['day','trig','pri']).reset_index(drop=True)
    if slim:
        keep=['day','book','rr','entry','exit','trig','t_in','t_out','ret_pct','fut_in','fut_out','iv_in','iv_out','pri']+[c for c in df.columns if c.startswith('wx_')]
        df=df[keep]
    return df
def sim_day(g, guard=None, lot=65, cap0=100000.0):
    """guard(row, acct) -> True = block. acct: dict with the account's history today."""
    cap=cap0; held=None; taken=[]; blocked=[]
    acct={'trades':[], 'cap':cap}
    for r in g:
        idx=r.Index
        if held is not None:
            h_trig,h_out,h_book=held
            if r.trig<=h_trig: continue
            if r.trig<h_out or (r.trig==h_out and r.book==h_book): continue
            held=None
        if guard is not None and guard(r, acct):
            blocked.append(idx); continue
        px=float(r.entry); lots=int(cap//(px*lot))
        if lots<1: continue
        pnl=(float(r.exit)-px)*lots*lot
        cap+=pnl
        held=(r.trig,float(r.t_out),r.book)
        rec={'idx':idx,'book':r.book,'trig':r.trig,'t_out':float(r.t_out),'ret':float(r.ret_pct),'pnl':pnl,'rr':r.rr,'cap':cap,'fut_in':r.fut_in,'fut_out':r.fut_out}
        taken.append(rec); acct['trades'].append(rec); acct['cap']=cap
    return taken, cap, blocked
def sim(df, guard=None, days=None):
    lot,cap0=lot_size()
    out={}
    global _CACHE
    if _CACHE is None: _CACHE={}
    if id(df) not in _CACHE:
        class R: pass
        groups={}
        recs=df.to_dict('records')
        for i,rec in zip(df.index,recs):
            o=R(); o.__dict__.update(rec); o.Index=i
            for k,v in rec.items():
                if isinstance(v,float) and v!=v: setattr(o,k,None)
            groups.setdefault(rec['day'],[]).append(o)
        _CACHE[id(df)]=(df,groups)
    for d,g in sorted(_CACHE[id(df)][1].items()):
        if days and d not in days: continue
        t,c,b=sim_day(g,guard,lot,cap0)
        out[d]={'taken':t,'ret_day':100*(c/cap0-1),'n':len(t),'w':sum(x['pnl']>0 for x in t),'blocked':b}
    return out
EARLY=['2026-10-19','2026-10-21','2026-10-22','2026-10-23','2026-10-26','2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-11-02','2026-11-03','2026-11-04']
LATE=['2026-11-05','2026-11-06','2026-11-09','2026-11-11','2026-11-12']
def summary(res, days=None):
    ds=[d for d in sorted(res) if (days is None or d in days)]
    n=sum(res[d]['n'] for d in ds); w=sum(res[d]['w'] for d in ds)
    rets=[res[d]['ret_day'] for d in ds]
    tr=[x['ret'] for d in ds for x in res[d]['taken']]
    comp=np.prod([1+r/100 for r in rets])  # product of day multipliers (each day restarts at 1 lakh)
    return {'n':n,'w':w,'sr':100*w/max(n,1),'sum_day_pct':sum(rets),'mean_tr':np.mean(tr) if tr else 0,'ldays':sum(r<0 for r in rets),'worst_day':min(rets) if rets else 0,'med_day':float(np.median(rets)) if rets else 0}
