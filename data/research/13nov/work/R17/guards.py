"""Yes/no entry guards. Each is a factory returning guard(row, acct) -> True to BLOCK."""
import numpy as np, pandas as pd
def _f(v):
    try:
        v=float(v); return v if np.isfinite(v) else None
    except (TypeError, ValueError): return None
def _lossrun(tr):
    n=0
    for p in reversed(tr):
        if p['ret']<0: n+=1
        else: break
    return n
def mins(r): return _f(r.wx_mins_open)
# --- account-history guards
def cool_after_losses(N, M):
    """after N consecutive account losses, no entry for M minutes after the last exit (M=999: rest of day)"""
    def g(r,a):
        tr=a['trades']
        if len(tr)<N or _lossrun(tr)<N: return False
        return (r.trig-tr[-1]['t_out'])<M*60
    return g
def max_losses_day(K):
    def g(r,a): return sum(p['ret']<0 for p in a['trades'])>=K
    return g
def day_stop(X):
    def g(r,a): return 100*(a['cap']/100000.0-1)<=-X
    return g
def chop_after_losses(N, M, er):
    """owner's example: after N consecutive losses, while the day's efficiency < er and the straddle is not expanding, wait M min"""
    def g(r,a):
        tr=a['trades']
        if _lossrun(tr)<N: return False
        if (r.trig-tr[-1]['t_out'])>=M*60: return False
        e=_f(r.wx_er_day)
        return (e is not None and e<er) and not (r.wx_strad_expanding is True)
    return g
def flip_after_loss(M):
    """after a loss, no entry on the OTHER side within M minutes"""
    def g(r,a):
        tr=a['trades']
        if not tr or tr[-1]['ret']>=0: return False
        return tr[-1]['rr']!=r.rr and (r.trig-tr[-1]['t_out'])<M*60
    return g
def same_after_loss(M):
    def g(r,a):
        tr=a['trades']
        if not tr or tr[-1]['ret']>=0: return False
        return tr[-1]['rr']==r.rr and (r.trig-tr[-1]['t_out'])<M*60
    return g
def any_after_loss(M):
    def g(r,a):
        tr=a['trades']
        if not tr or tr[-1]['ret']>=0: return False
        return (r.trig-tr[-1]['t_out'])<M*60
    return g
# --- market-state guards
def chop(er, need_strad=True, col='wx_er_day'):
    def g(r,a):
        e=_f(getattr(r,col))
        if e is None: return False
        if need_strad and r.wx_strad_expanding is True: return False
        return e<er
    return g
def against_trend(Y, er=None):
    """day_move is signed with the trade; block when the trade is Y+ points against the day's move (and the day is efficient)"""
    def g(r,a):
        m=_f(r.wx_day_move)
        if m is None or m>-Y: return False
        if er is None: return True
        e=_f(r.wx_er_day); return e is not None and e>=er
    return g
def late(hhmm):
    h,m=map(int,hhmm.split(':')); lim=(h*60+m)-(9*60+15)
    def g(r,a):
        x=mins(r); return x is not None and x>=lim
    return g
def early(hhmm):
    h,m=map(int,hhmm.split(':')); lim=(h*60+m)-(9*60+15)
    def g(r,a):
        x=mins(r); return x is not None and x<lim
    return g
def spread(s):
    def g(r,a):
        x=_f(r.wx_spread_pct); return x is not None and x>s
    return g
def quote_age(q):
    def g(r,a):
        x=_f(r.wx_quote_age); return x is not None and x>q
    return g
def iv_falling(th, col='wx_atm_iv_chg5'):
    def g(r,a):
        x=_f(getattr(r,col)); return x is not None and x<th
    return g
def strad_flat(th):
    def g(r,a):
        x=_f(r.wx_strad_chg5); return x is not None and x<th
    return g
def AND(*gs):
    def g(r,a): return all(x(r,a) for x in gs)
    return g
def OR(*gs):
    def g(r,a): return any(x(r,a) for x in gs)
    return g
def band(col, lo, hi):
    def g(r,a):
        x=_f(getattr(r,col)); return x is not None and lo<=x<hi
    return g
def after_loss(M, lt=0.0, side='any', diff_book=False):
    """after an account trade that lost more than -lt %, no entry for M min (side: any|flip|same)"""
    def g(r,a):
        tr=a['trades']
        if not tr or tr[-1]['ret']>=lt: return False
        if (r.trig-tr[-1]['t_out'])>=M*60: return False
        if side=='flip' and tr[-1]['rr']==r.rr: return False
        if side=='same' and tr[-1]['rr']!=r.rr: return False
        if diff_book and tr[-1]['book']==r.book: return False
        return True
    return g
def whipsaw(M):
    """the last two account trades both lost and were on opposite sides: no entry for M min"""
    def g(r,a):
        tr=a['trades']
        if len(tr)<2 or tr[-1]['ret']>=0 or tr[-2]['ret']>=0 or tr[-1]['rr']==tr[-2]['rr']: return False
        return (r.trig-tr[-1]['t_out'])<M*60
    return g
def side_ban(N):
    """N consecutive losses on the same side: that side is barred for the rest of the day"""
    def g(r,a):
        tr=a['trades']; n=0
        for p in reversed(tr):
            if p['ret']<0 and p['rr']==r.rr: n+=1
            else: break
        return n>=N
    return g
