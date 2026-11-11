"""11 Nov 2026 (docs/44 M1 and section 4C; review of docs/45, point 3): champion decision episodes, EXECUTED ONLY.

One row per fill of the NAMED reference policy (default c20_9y) in the 15-day replay p41. Its own trigger second, its
own contract (the council strategy names its strike itself; it does not use the default delta-band rule), its own
result under its own unchanged exits. Sibling books (other c20* books that bought the same contract within 5 s of
the same trigger) are kept in separate columns and never averaged into the label.

WHAT IS MISSING, stated: triggers the policy saw and did not trade (in position, blocked, vetoed, lapsed fills) are
not in this table. p41 ran with the missed-signal recorder off. Until a recorder-on replay exists this table can
describe the trades taken; it CANNOT answer whether a forecast would improve selection. No admission model is to be
judged on it alone.

Per row:
  identity   day, trigger_t, key, strike, rr, expiry, depth from the forecaster's at-the-money strike, engine delta
  features   the forecaster's 33 features of THAT contract at the trigger second (causal: fed second by second up to it)
  forecast-style label   targets.label from the trigger second: first barrier at 30/60/180/300 s, 300-s return
  policy labels (separate, none replaces another)
             ret_pct (exit/entry - 1), pnl_rs, hold_s, exit reason, profitable, developed5 (best bid-side gain of at
             least 5 % of entry, from the premium path between fill and exit), runner (ret_pct >= 20), peak_pct
  siblings   n_siblings, their mean and best ret_pct, in their own columns

Output: data/research/predict/episodes_<policy>.npz + .json manifest. Usage: py -3.13 build_episodes.py [policy] [workers]"""
import glob, hashlib, json, os, sys, time
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT)
os.environ.setdefault('APEX_DATA', os.path.join(ROOT, 'data', 'research', 'predict', '_no_engine_data'))
from apex.predict import features as F, targets as T
DS = os.path.join(ROOT, 'data', 'research', 'ds_v2')
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
H = T.HORIZONS
FIRST = {'T': 1, 'A': 2, 'N': 0, 'U': 3}
RUNNER_PCT = 20.0
COLS = (['day_i', 'trigger_t', 'strike', 'rr', 'depth', 'delta_in', 'entry', 'fill_delay', 'ret_pct', 'pnl_rs', 'hold_s',
         'profitable', 'developed5', 'runner', 'peak_pct', 'trough_pct', 'has_x', 'st'] + [f'first{h}' for h in H]
        + ['ret300', 'n_siblings', 'sib_mean_ret', 'sib_best_ret', 'fc_edge'])


def day_trades(policy):
    """{day: (policy trades, sibling trades)} from p41."""
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'replay', 'batch', 'p41_g*', 'paper', '2026-*.json'))):
        day = os.path.basename(f)[:10]
        books = json.load(open(f, encoding='utf-8'))
        mine = [t for t in books.get(policy, {}).get('trades', []) if t.get('exit') is not None]
        sib = [(n, t) for n, b in books.items() if isinstance(b, dict) and n.startswith('c20') and n != policy
               for t in b.get('trades', []) if t.get('exit') is not None]
        out[day] = (mine, sib)
    return out


def one(args):
    day, paths, mine, sib = args
    rows, X, reasons, meta = [], [], [], []
    todo = sorted(mine, key=lambda t: t.get('trigger_t') or t['t_in'])
    for path in paths:
        z = np.load(path)
        exp = str(z['expiry'])
        n = len(z['strikes']); order = np.argsort(z['strikes'])
        K = z['strikes'][order].astype(float)
        o = z['opt'][:, :n].astype(float)[:, order]
        age = z['age'][:, :n].astype(float)[:, order]
        bid, ask = o[..., 0], o[..., 1]
        ok = (bid > 0) & (ask > bid) & (age <= F.Q_FRESH_S)
        t = z['t'].astype(float); fut = z['fut'].astype(float); fa = z['fa'].astype(float)
        hw, hwa, sf, sfa, w = z['hw'].astype(float), z['hwa'].astype(float), z['sf'].astype(float), z['sfa'].astype(float), z['w'].astype(float)
        nh = min(hw.shape[1], len(w))
        dte = F.dte_days(day, exp)
        here = [tr for tr in todo if tr['expiry'] == exp and t[0] <= int(tr.get('trigger_t') or tr['t_in']) <= t[-1]]
        want = {}
        for tr in here:
            want.setdefault(int(tr.get('trigger_t') or tr['t_in']), []).append(tr)
        if not want:
            continue
        fs = F.Features()
        last = max(want)
        for i in range(len(t)):
            if t[i] > last:
                break
            fs.update(t[i], fut[i, 0], fut[i, 1], fa[i, 0], hw[i, :nh], hwa[i, :nh], sf[i, :nh, 0], sf[i, :nh, 1], sfa[i, :nh],
                      w[:nh], K, bid[i], ask[i], age[i], dte, dte == 0, F.tod_seconds(t[i]),
                      f_ltp=fut[i, 2], f_vol=fut[i, 3], bq=fut[i, 4], aq=fut[i, 5], d_age=fa[i, 1])
            for tr in want.get(int(t[i]), []):
                rr = 0 if tr['rr'] == 'CE' else 1
                kk = np.where(K == float(tr['strike']))[0]
                k_atm = fs.atm() if fs.ready() else None
                x = fs.contract(int(kk[0]), rr) if len(kk) and fs.ready() else None
                depth = np.nan if k_atm is None or not len(kk) else float((k_atm - kk[0]) if rr == 0 else (kk[0] - k_atm))
                lab = dict(st='L')
                peak = trough = np.nan
                if len(kk):
                    lab = T.label(t, bid[:, kk[0], rr], ask[:, kk[0], rr], ok[:, kk[0], rr], age[:, kk[0], rr], i)
                    a, b = np.searchsorted(t, tr['t_in']), np.searchsorted(t, tr['t_out'], side='right')
                    path_bid = np.where(ok[a:b, kk[0], rr], bid[a:b, kk[0], rr], np.nan)
                    if np.isfinite(path_bid).any():
                        peak = 100.0 * (np.nanmax(path_bid) / tr['entry'] - 1.0)
                        trough = 100.0 * (np.nanmin(path_bid) / tr['entry'] - 1.0)
                ret = 100.0 * (tr['exit'] / tr['entry'] - 1.0)
                tt = tr.get('trigger_t') or tr['t_in']
                ss = [100.0 * (s['exit'] / s['entry'] - 1.0) for _, s in sib
                      if s['key'] == tr['key'] and abs((s.get('trigger_t') or s['t_in']) - tt) <= 5.0]
                fc = (tr.get('fc') or {}).get('edge')
                rows.append([0, tt, float(tr['strike']), rr, depth, tr.get('delta_in') if tr.get('delta_in') is not None else np.nan,
                             tr['entry'], tr.get('fill_delay_s') if tr.get('fill_delay_s') is not None else np.nan, ret,
                             tr['pnl_rs'], tr.get('hold_s') or (tr['t_out'] - tr['t_in']), float(tr['pnl_rs'] > 0),
                             float(peak >= 5.0) if np.isfinite(peak) else np.nan, float(ret >= RUNNER_PCT), peak, trough,
                             float(x is not None), 1.0 if lab['st'] == 'ok' else -1.0]
                            + [(FIRST[lab['first'][h]] if lab['st'] == 'ok' else 3) for h in H]
                            + [(lab['ret'][H[-1]] if lab['st'] == 'ok' and lab['ret'][H[-1]] is not None else np.nan),
                               len(ss), float(np.mean(ss)) if ss else np.nan, float(np.max(ss)) if ss else np.nan,
                               fc if fc is not None else np.nan])
                X.append(x if x is not None else np.full(len(F.NAMES), np.nan))
                reasons.append(str(tr.get('reason', '?')))
                meta.append(dict(key=tr['key'], time_in=tr.get('time_in'), ep_type=tr.get('ep_type'), why=str(tr.get('why'))[:120]))
                todo = [q for q in todo if q is not tr]
    return day, rows, X, reasons, meta, len(todo)


def main():
    policy = sys.argv[1] if len(sys.argv) > 1 else 'c20_9y'
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    parts = {}
    for p in sorted(glob.glob(os.path.join(DS, '*.npz'))):
        parts.setdefault(os.path.basename(p)[:10], []).append(p)
    dt = day_trades(policy)
    days = sorted(dt)
    t0 = time.time()
    from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(one, [(d, parts.get(d, []), dt[d][0], dt[d][1]) for d in days])
    R, X, reasons, meta, unplaced = [], [], [], [], {}
    for d, rows, x, rs, mt, left in res:
        for r in rows:
            r[0] = days.index(d)
        R += rows; X += x; reasons += rs; meta += mt
        if left:
            unplaced[d] = left
    R = np.array(R, float); X = np.array(X, float)
    dst = os.path.join(OUT, f'episodes_{policy}.npz')
    np.savez_compressed(dst, R=R, X=X, cols=np.array(COLS), names=np.array(F.NAMES), days=np.array(days), reasons=np.array(reasons),
                        keys=np.array([m['key'] for m in meta]))
    c = {n: i for i, n in enumerate(COLS)}
    total = sum(len(dt[d][0]) for d in days)
    man = dict(policy=policy, source='p41_g1..g8 (10 Nov code, recorder off)', built=time.strftime('%Y-%m-%d %H:%M:%S'),
               executed_trades=total, rows=int(len(R)), not_in_recorded_seconds=unplaced, sessions=len(days),
               with_features=int(np.nansum(R[:, c['has_x']])), with_first_barrier_label=int((R[:, c['st']] == 1).sum()),
               profitable=int(np.nansum(R[:, c['profitable']])), developed5=int(np.nansum(R[:, c['developed5']])),
               runners=int(np.nansum(R[:, c['runner']])), runner_definition=f'ret_pct >= {RUNNER_PCT}',
               depth_counts={str(int(k)): int(v) for k, v in zip(*np.unique(R[np.isfinite(R[:, c['depth']]), c['depth']], return_counts=True))},
               delta_quantiles=[float(q) for q in np.nanquantile(np.abs(R[:, c['delta_in']]), [0.05, 0.25, 0.5, 0.75, 0.95])],
               had_engine_forecast_at_fill=int(np.isfinite(R[:, c['fc_edge']]).sum()),
               missing='rejected, blocked, vetoed and lapsed triggers are NOT here: the replay ran with the recorder off',
               sha256=hashlib.sha256(open(dst, 'rb').read()).hexdigest(), wall_s=round(time.time() - t0, 1))
    # where the forecast-style label and the policy's own result disagree (docs/44 section 4C)
    lab = R[:, c['st']] == 1
    f300 = R[:, c['first300']]
    tab = {}
    for name, code in (('up_first', 1), ('down_first', 2), ('neither', 0), ('unobservable', 3)):
        m = lab & (f300 == code)
        tab[name] = dict(n=int(m.sum()), profitable=int(np.nansum(R[m, c['profitable']])), runners=int(np.nansum(R[m, c['runner']])),
                         sum_pnl_rs=float(np.nansum(R[m, c['pnl_rs']])), mean_ret_pct=float(np.nanmean(R[m, c['ret_pct']])) if m.any() else None)
    man['first_barrier_vs_policy_result'] = tab
    man['no_first_barrier_label'] = int((~lab).sum())
    json.dump(man, open(os.path.join(OUT, f'episodes_{policy}.json'), 'w'), indent=1)
    print(json.dumps(man, indent=1))


if __name__ == '__main__':
    main()
