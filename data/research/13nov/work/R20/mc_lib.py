"""R20 meta-controller library: one-account all-in simulator with online (causal) state, families, BOCPD."""
import math
import re
from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd

IST = timezone(timedelta(hours=5, minutes=30))
POOL = ['c20_9y', 'c20_9s', 'c20_9v', 'c20_9x', 'c20_9t']          # pool.json priority (ret_per_trade order)
EARLY_END = '2026-11-04'
CTL = {'conductor', 'futures_only', 'random_entry', 'premium_momentum', 'RAW'}


def family(b):
    if b in POOL:
        return 'c20pool'
    if b in CTL or '_ctl' in b:
        return None
    if 'c20' in b:
        return 'c20ext'
    if b.startswith('t28'):
        return 't28'
    if b.startswith('lvl_trail'):
        return 'lvl'
    if b.startswith(('spot_pb45', 'spot_dual', 'spot_orb45')):
        return 'spotpb'
    if b.startswith('spot_dc12'):
        return 'spotdc'
    if b.startswith('fade_switch'):
        return 'fade'
    if b.startswith(('apex_edge', 'edge_')):
        return 'edge'
    if re.match(r'^(m\d|gap\d)', b):
        return 'mgrid'
    if b.startswith(('n01', 'n02', 'n06', 's01', 's03')):
        return 'flow'
    if b.startswith(('p02', 'p05')):
        return 'pred'
    if b.startswith(('straddle', 'spot_ft')):
        return 'straddle'
    return 'other'


def load(path='trades_small.pkl'):
    df = pd.read_pickle(path)
    df['trig'] = df.trigger_t.fillna(df.t_in).astype(float)
    df['fam'] = df.book.map(family)
    df['win'] = (df.ret_pct > 0).astype(int)
    df['dirn'] = np.where(df.rr == 'CE', 1, -1)
    return df


def open_epoch(day):
    d = datetime.strptime(day, '%Y-%m-%d').replace(hour=9, minute=15, tzinfo=IST)
    return d.timestamp()


# ---------------------------------------------------------------- futures path + BOCPD
def minute_path(dd, day):
    """1-min futures path rebuilt from every book's entry and exit futures prints (a print counts at its own time).
    Index 0 = the minute 09:15:00-09:15:59; value = last print inside or before that minute."""
    t0 = open_epoch(day)
    pts = pd.concat([pd.DataFrame({'t': dd.t_in.values, 'f': dd.fut_in.values}),
                     pd.DataFrame({'t': dd.t_out.values, 'f': dd.fut_out.values})]).dropna()
    pts = pts[pts.f > 1000].sort_values('t')
    m = ((pts.t - t0) // 60).astype(int)
    last = pts.groupby(m).f.last()
    idx = np.arange(0, 376)
    return last.reindex(idx).ffill().values


_LG = math.lgamma


def bocpd(x, hazard=1 / 60., mu0=0.0, kappa0=1.0, alpha0=1.0, beta0=None, rmax=300):
    """Adams and MacKay (2007) online change-point detection, Normal-Gamma prior, Student-t predictive.
    x: 1-min returns (points). Per step: [P(run length < 10), MAP run length, segment mean, segment sd]."""
    x = np.asarray(x, float)
    if beta0 is None:
        beta0 = 25.0
    R = np.array([1.0]); mu = np.array([mu0]); ka = np.array([kappa0]); al = np.array([alpha0]); be = np.array([beta0])
    out = np.full((len(x), 4), np.nan)
    lg = np.vectorize(_LG)
    for t, xt in enumerate(x):
        if not np.isfinite(xt):
            continue
        sc = np.sqrt(be * (ka + 1) / (al * ka))
        nu = 2 * al
        z = (xt - mu) / sc
        lp = lg((nu + 1) / 2) - lg(nu / 2) - 0.5 * np.log(nu * np.pi) - np.log(sc) - (nu + 1) / 2 * np.log1p(z * z / nu)
        pp = np.exp(lp - lp.max())
        grow = R * pp * (1 - hazard)
        cp = (R * pp * hazard).sum()
        R = np.concatenate([[cp], grow]); R /= R.sum()
        mu_n = (ka * mu + xt) / (ka + 1); ka_n = ka + 1; al_n = al + 0.5
        be_n = be + ka * (xt - mu) ** 2 / (2 * (ka + 1))
        mu = np.concatenate([[mu0], mu_n]); ka = np.concatenate([[kappa0], ka_n])
        al = np.concatenate([[alpha0], al_n]); be = np.concatenate([[beta0], be_n])
        if len(R) > rmax:
            R = R[:rmax] / R[:rmax].sum(); mu, ka, al, be = mu[:rmax], ka[:rmax], al[:rmax], be[:rmax]
        k = int(np.argmax(R))
        out[t] = [R[:10].sum(), k, mu[k], math.sqrt(be[k] / max(al[k] - 1, 0.5))]
    return out


# ---------------------------------------------------------------- one-account simulator
def sim_day(dd, accept=None, books=None, prio=None):
    """dd: one day's trades. books: allowed books (None = all rows given). prio: book -> rank (same tick).
    accept(row) -> bool decides at the trigger, with state the caller keeps causal.
    Same one-position rules as apex/conductor/account_sim.py. Returns the taken row labels."""
    c = dd if books is None else dd[dd.book.isin(books)]
    c = c.assign(_p=c.book.map(prio).fillna(999) if prio else 0).sort_values(['trig', '_p'])
    held = None
    taken = []
    for i, r in zip(c.index, c.itertuples()):
        if held is not None:
            h_trig, h_out, h_book = held
            if r.trig <= h_trig or r.trig < h_out or (r.trig == h_out and r.book == h_book):
                continue
            held = None
        if accept is not None and not accept(r):
            continue
        held = (r.trig, r.t_out, r.book)
        taken.append(i)
    return taken


def day_ret(rets):
    rets = np.asarray(rets, float)
    return 100 * (np.prod(1 + rets / 100) - 1) if len(rets) else 0.0


def score(df, taken_by_day, label=''):
    rows = []
    for d, ix in sorted(taken_by_day.items()):
        t = df.loc[ix]
        rows.append({'day': d, 'n': len(t), 'w': int((t.ret_pct > 0).sum()), 'ret': day_ret(t.ret_pct.values)})
    s = pd.DataFrame(rows).set_index('day').sort_index()

    def part(m):
        x = s[m]
        n = x.n.sum()
        return {'strike': 100 * x.w.sum() / n if n else float('nan'), 'n': int(n), 'sum': x.ret.sum(),
                'lose': int((x.ret < 0).sum()), 'worst': x.ret.min(), 'woBD': x.ret.sum() - x.ret.max()}
    e = s.index <= EARLY_END
    out = {'label': label}
    for k, m in (('all', np.ones(len(s), bool)), ('early', e), ('late', ~e)):
        for kk, v in part(m).items():
            out[f'{k}_{kk}'] = v
    out['_perday'] = s.ret.round(1).to_dict()
    return out


def top_kept(df, taken_by_day, cond_taken_by_day, top_frac=0.10):
    ct = df.loc[[i for v in cond_taken_by_day.values() for i in v]]
    thr = ct.ret_pct.quantile(1 - top_frac)
    top = ct[ct.ret_pct >= thr]
    kept = 0
    for _, r in top.iterrows():
        p = df.loc[taken_by_day.get(r.day, [])]
        ok = ((p.rr == r.rr) & (((p.t_in - r.t_in).abs() <= 60) | ((p.t_in <= r.t_in) & (p.t_out > r.t_in)))).any()
        kept += int(ok)
    return kept, len(top)


def fmt(sc):
    keys = ['all_strike', 'all_n', 'all_sum', 'all_lose', 'all_worst', 'all_woBD', 'late_strike', 'late_n', 'late_sum',
            'late_lose', 'late_worst', 'early_sum']
    return sc['label'] + ' | ' + ' '.join(f"{k}={sc[k]:.1f}" if isinstance(sc[k], float) else f"{k}={sc[k]}" for k in keys)
