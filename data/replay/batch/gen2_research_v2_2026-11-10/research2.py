"""docs/36 N03 / N04 / N05 research, CORRECTED version 2 (10 Nov 2026) after the docs/38 section 5 review.

The specification of every model is the one frozen on 9 Nov (gen2_research_2026-11-09/research.py: same features,
ridge, 99th-percentile threshold, horizons). Nothing was tuned here. What changed is the measurement:

  item 6  rows are boundary snapshots (ds2.py): a row stamped B holds only packets received before B;
  item 6  the entry is the first quote received AFTER the request (age at the fill row <= the delay), not any quote
          up to three seconds old;
  item 7  a position is busy until its actual exit time (request + delay + horizon), not request + horizon;
  item 8  a signal whose entry quote is missing is a LAPSE, a signal whose exit quote is missing is CENSORED; both
          are counted and reported, neither is silently dropped from the test days (training uses labelled rows only);
  item 4  N04 is decomposed over a frozen delay grid (1, 2, 3, 5 s) and horizons 1, 3, 5, 10, 30 s;
  item 5  N05 without expiry days is shown both ways: the frozen full-sample predictions restricted to non-expiry
          dates, and a separately trained non-expiry model, compared on common dates;
  item 9  the quote-aware result (buy at the ask, sell at the bid) is a parallel diagnostic. The mid-to-mid figure
          is printed beside it. Neither is the official gross first-print convention of the books;
  item 10 durable paths (config.RESEARCH_DIR), dataset hashes and every pick are written with the result.
The old outputs stay in gen2_research_2026-11-09 untouched. Read-only on the repo.
Usage: py -3.13 research2.py [n03] [n05] [n04]"""
import glob, importlib.util, json, os, sys
from datetime import datetime, timezone, timedelta
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex import config, greeks
_spec = importlib.util.spec_from_file_location('research_v1', os.path.join(HERE, '..', 'gen2_research_2026-11-09', 'research.py'))
v1 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v1)      # the frozen maths: sig2, ridge, surface

DS = os.path.join(config.RESEARCH_DIR, 'ds_v2')
OUT = os.path.join(config.RESEARCH_DIR, 'gen2_v2')
IST = timezone(timedelta(hours=5, minutes=30))
H, STEP, MIN_TRAIN_DATES, Q, FRESH = v1.H, v1.STEP, v1.MIN_TRAIN_DATES, v1.Q, v1.FRESH
DELAY = 1                    # primary request-to-fill delay, seconds (the v1 value); the grid below is reported too
DELAYS = (1, 2, 3, 5)        # frozen before the first run of this file
HORIZONS = (1, 3, 5, 10, 30)


def load(path):
    z = np.load(path)
    n = len(z['strikes'])
    order = np.argsort(z['strikes'])
    o = z['opt'][:, :n].astype(float)[:, order]; a = z['age'][:, :n].astype(float)[:, order]
    d = dict(t=z['t'].astype(float), fut=z['fut'].astype(float), fa=z['fa'].astype(float), K=z['strikes'][order].astype(float),
             bid=o[..., 0], ask=o[..., 1], age=a, exp=str(z['expiry']), name=os.path.basename(path)[:-4])
    d['date'] = d['name'][:10]
    d['ok'] = (d['bid'] > 0) & (d['ask'] > d['bid']) & (d['age'] <= FRESH)
    d['mid'] = np.where(d['ok'], 0.5 * (d['bid'] + d['ask']), np.nan)
    f = d['fut']; d['fm'] = 0.5 * (f[:, 0] + f[:, 1])
    d['fok'] = (f[:, 0] > 0) & (f[:, 1] >= f[:, 0]) & (d['fa'][:, 0] <= FRESH)
    x = np.zeros(len(f)); dep = None; k = 0.5 ** (1 / 60.0)             # the signed-flow proxy, as v1
    for i in range(1, len(f)):
        dq = f[i, 3] - f[i - 1, 3]
        dq = dq if 0 <= dq < 1e9 else 0.0
        ltp = f[i, 2]
        sg = 1 if ltp >= f[i - 1, 1] else (-1 if ltp <= f[i - 1, 0] else (1 if ltp > f[i - 1, 2] else (-1 if ltp < f[i - 1, 2] else 0)))
        dd = 0.5 * (f[i, 4] + f[i, 5])
        if dd > 0:
            dep = dd if dep is None else k * dep + (1 - k) * dd
        x[i] = sg * dq / dep if dep else 0.0
    d['x'] = x
    d['idx'] = {float(t): i for i, t in enumerate(d['t'])}
    return d


def load_all():
    days = [load(p) for p in sorted(glob.glob(os.path.join(DS, '*.npz')))]
    days = [d for d in days if len(d['t'])]
    days.sort(key=lambda d: d['t'][0])
    allt = np.concatenate([d['t'] for d in days])
    assert (np.diff(allt) > 0).all(), 'dataset parts overlap or are out of order'      # item 10: asserted, not assumed
    man = {}
    for p in sorted(glob.glob(os.path.join(DS, '*.manifest.json'))):
        m = json.load(open(p)); man[m['part']] = dict(rows=m['rows'], npz_sha256=m['npz_sha256'], tape_sha256=m['tape_sha256'],
                                                      end_marker=m['tape_end_marker'], torn=m['tape_torn'])
    return days, man


def contiguous(d, i0, i1):
    return i0 >= 0 and i1 < len(d['t']) and d['t'][i1] - d['t'][i0] == i1 - i0


def at(d, i, s):
    """Row index of the snapshot s seconds after row i, or None when that second has no row."""
    return d['idx'].get(d['t'][i] + s)


def atm(d, i):
    return int(np.argmin(np.abs(d['K'] - d['fm'][i])))


def label(d, i, j, rr, delay=DELAY, h=H):
    """(status, quote-aware return, mid-to-mid return, exit time). The request is made at the cutoff of row i.
    The fill is the ask of a quote RECEIVED AFTER the request and seen `delay` seconds later; the exit is the bid
    seen h seconds after the fill. status: 'ok' | 'lapse' (no post-request entry quote) | 'censored' (no exit quote)."""
    a = at(d, i, delay)
    if a is None or not d['ok'][a, j, rr] or d['age'][a, j, rr] > delay:
        return 'lapse', None, None, None
    t_exit = d['t'][a] + h
    b = at(d, a, h)
    if b is None or not d['ok'][b, j, rr]:
        return 'censored', None, None, t_exit
    y = d['bid'][b, j, rr] / d['ask'][a, j, rr] - 1.0
    m0 = d['mid'][i, j, rr]
    ym = d['mid'][b, j, rr] / m0 - 1.0 if np.isfinite(m0) else None
    return 'ok', y, ym, t_exit


def both(d, i, j):
    """Labels of the two legs at row i. A sample is trainable only when both legs are 'ok' (as v1)."""
    c, p = label(d, i, j, 0), label(d, i, j, 1)
    return dict(st_ce=c[0], st_pe=p[0], y_ce=c[1], y_pe=p[1], m_ce=c[2], m_pe=p[2], x_ce=c[3], x_pe=p[3])


def walk_forward(samples, feats, tag, keep_dates=None):
    """Walk-forward by date. Trains on fully labelled earlier rows; on the test date EVERY feature-valid row is
    scored, so a signal can lapse or be censored. keep_dates: report only these test dates (frozen predictions)."""
    n0 = len(samples)
    samples = [s for s in samples if all(np.isfinite(v).all() for v in s['f'].values())]
    lab = [s for s in samples if s['st_ce'] == 'ok' and s['st_pe'] == 'ok']
    print(f"{tag}: feature-valid rows {len(samples)} of {n0}; both legs labelled {len(lab)}; "
          f"entry missing on a leg {sum(s['st_ce'] == 'lapse' or s['st_pe'] == 'lapse' for s in samples)}; "
          f"exit missing on a leg {sum(s['st_ce'] == 'censored' or s['st_pe'] == 'censored' for s in samples)}")
    dates = sorted({s['date'] for s in lab})
    out = {}
    for fs in feats:
        picks, lapses, cens, ics = [], [], [], []
        for di, dte in enumerate(dates):
            if di < MIN_TRAIN_DATES or (keep_dates is not None and dte not in keep_dates):
                continue
            tr = [s for s in lab if s['date'] < dte]
            te = [s for s in samples if s['date'] == dte]
            if len(tr) < 500 or not te:
                continue
            Xtr = np.array([s['f'][fs] for s in tr]); Xte = np.array([s['f'][fs] for s in te])
            pred = {}
            for leg in ('ce', 'pe'):
                m = v1.ridge_fit(Xtr, np.array([s['y_' + leg] for s in tr]))
                ptr = v1.ridge_pred(m, Xtr); pte = v1.ridge_pred(m, Xte)
                pred[leg] = (pte, max(np.quantile(ptr, Q), 0.0))
                okk = np.array([s['st_' + leg] == 'ok' for s in te])
                if okk.sum() >= 30:
                    ics.append(v1.rank_ic(pte[okk], np.array([s['y_' + leg] for s in te if s['st_' + leg] == 'ok'])))
            busy_until = -1.0
            for k, s in enumerate(te):
                if s['t'] < busy_until:                                   # item 7: busy until the ACTUAL exit time
                    continue
                best = max(('ce', 'pe'), key=lambda L: pred[L][0][k] - pred[L][1])
                if pred[best][0][k] <= pred[best][1]:
                    continue
                st = s['st_' + best]
                if st == 'lapse':
                    lapses.append((dte, float(s['t']), best))             # no fill: the account stays free
                elif st == 'censored':
                    cens.append((dte, float(s['t']), best)); busy_until = s['x_' + best]
                else:
                    picks.append((dte, float(s['t']), best, float(s['y_' + best]),
                                  None if s['m_' + best] is None else float(s['m_' + best]), float(s['K'])))
                    busy_until = s['x_' + best]
        ys = np.array([p[3] for p in picks]) if picks else np.array([])
        ms = np.array([p[4] for p in picks if p[4] is not None]) if picks else np.array([])
        byd = {}
        for p in picks:
            byd[p[0]] = byd.get(p[0], 0.0) + p[3]
        top = float(ys.max()) if len(ys) else 0.0
        out[fs] = dict(n=len(picks), lapsed=len(lapses), censored=len(cens),
                       mean_pct=round(100 * float(ys.mean()), 3) if len(ys) else None,
                       median_pct=round(100 * float(np.median(ys)), 3) if len(ys) else None,
                       mean_without_best_pct=round(100 * float((ys.sum() - top) / (len(ys) - 1)), 3) if len(ys) > 1 else None,
                       mid_mean_pct=round(100 * float(ms.mean()), 3) if len(ms) else None,
                       wins=int((ys > 0).sum()), sum_pct=round(100 * float(ys.sum()), 1) if len(ys) else 0.0,
                       best_pct=round(100 * top, 1), days_up=sum(v > 0 for v in byd.values()), days_down=sum(v < 0 for v in byd.values()),
                       by_day={k: round(100 * v, 1) for k, v in sorted(byd.items())},
                       ic=round(float(np.nanmean(ics)), 4) if ics else None, picks=picks, lapses=lapses, censored_list=cens)
        r = out[fs]
        print(f"{tag:6s} {fs:10s} picks {r['n']:4d} (lapsed {r['lapsed']}, censored {r['censored']}) wins {r['wins']:4d} "
              f"mean {r['mean_pct']} % median {r['median_pct']} % without best {r['mean_without_best_pct']} % "
              f"(best {r['best_pct']} %) mid-to-mid {r['mid_mean_pct']} % sum {r['sum_pct']} % days +{r['days_up']}/-{r['days_down']} | IC {r['ic']}")
    return out


def base_rate(samples, tag):
    y = np.array([s['y_ce'] for s in samples if s['st_ce'] == 'ok'] + [s['y_pe'] for s in samples if s['st_pe'] == 'ok'])
    print(f"{tag}: labelled legs {len(y)}, unconditional quote-aware {H}-s return mean {100 * y.mean():.3f} %, share > 0 {100 * (y > 0).mean():.1f} %")
    return dict(n=len(y), mean_pct=round(100 * float(y.mean()), 3), share_up=round(float((y > 0).mean()), 3))


def n03_samples(d, scale):
    L, B = 60, 5
    out = []
    for i in range(L + 1, len(d['t']), STEP):
        if not contiguous(d, i - L, i) or not d['fok'][i]:
            continue
        j = atm(d, i)
        idx = np.arange(i - L, i + 1, B)
        ce, pe = d['mid'][idx, j, 0], d['mid'][idx, j, 1]
        if np.isnan(ce).any() or np.isnan(pe).any():
            continue
        fx = np.add.reduceat(d['x'][i - L + 1:i + 1], np.arange(0, L, B))
        inc = np.c_[np.diff(d['fm'][idx]), np.diff(ce), np.diff(pe), fx] / scale
        full = np.c_[np.full((len(inc), 1), 1.0 / len(inc)), inc]
        shuf = full[np.random.RandomState(int(d['t'][i]) % 2 ** 31).permutation(len(full))]
        s = dict(date=d['date'], t=d['t'][i], K=d['K'][j], dte0=d['date'] == d['exp'],
                 f=dict(endpoints=inc.sum(0), lags=inc.ravel(), sig2=v1.sig2(full), sig2_shuf=v1.sig2(shuf)))
        s.update(both(d, i, j)); out.append(s)
    return out


def n05_samples(d):
    exp = datetime.fromisoformat(d['exp'] + 'T15:30:00').replace(tzinfo=IST)
    cache = {}

    def sf(i):
        if i not in cache:
            now = datetime.fromtimestamp(d['t'][i], IST)
            cache[i] = v1.surface(d, i, greeks.years_to_expiry(d['exp'], now)) if now < exp else None
        return cache[i]
    out = []
    for i in range(61, len(d['t']), STEP):
        if not contiguous(d, i - 60, i) or not d['fok'][i]:
            continue
        s1, s0 = sf(i), sf(i - 60)
        if s1 is None or s0 is None:
            continue
        j = atm(d, i)
        dl, dsk, dcv, dF = s1[0] - s0[0], s1[1] - s0[1], s1[2] - s0[2], s1[3] - s0[3]
        dstr = (s1[4] / s0[4] - 1.0) * 100.0
        s = dict(date=d['date'], t=d['t'][i], K=d['K'][j], dte0=d['date'] == d['exp'],
                 f=dict(surface=np.array([dl, dsk, dcv, dF / 10.0, s1[0], s1[1]]), iv_mom=np.array([dl]),
                        prem_mom=np.array([dstr, dF / 10.0]), fwd_only=np.array([dF / 10.0])))
        s.update(both(d, i, j)); out.append(s)
    return out


def n04(days):
    """Same signal as v1 (the neighbours' delta-adjusted 2-s move minus the target's own). The outcome is decomposed:
    the target's mid 1/3/5/10/30 s after the signal (no execution), and the quote-aware return for every delay in
    DELAYS and every horizon in HORIZONS (buy at a post-request ask, sell at the bid h seconds after the fill)."""
    rows = []
    for d in days:
        n = len(d['t'])
        for i in range(302, n, 2):
            if not contiguous(d, i - 300, i) or not d['fok'][i]:
                continue
            j = atm(d, i)
            if j < 2 or j > len(d['K']) - 3:
                continue
            fseg = d['fm'][i - 300:i + 1]

            def delta(series):
                a = np.diff(series[::5]); b = np.diff(fseg[::5])
                okm = ~np.isnan(a)
                if okm.sum() < 30 or np.var(b[okm]) <= 0:
                    return None
                return float(np.cov(a[okm], b[okm])[0, 1] / np.var(b[okm]))
            for rr in (0, 1):
                nb = [(j + o, rr) for o in (-2, -1, 1, 2)] + [(j + o, 1 - rr) for o in (-1, 0, 1)]
                tgt = d['mid'][i - 300:i + 1, j, rr]
                if np.isnan(tgt[-3:]).any() or d['age'][i, j, rr] > 1.5:
                    continue
                dt_ = delta(tgt)
                if dt_ is None:
                    continue
                dF = d['fm'][i] - d['fm'][i - 2]
                own = (tgt[-1] - tgt[-3]) - dt_ * dF
                res, raw = [], []
                for (k, r2) in nb:
                    s = d['mid'][i - 300:i + 1, k, r2]
                    if np.isnan(s[-3:]).any() or d['age'][i, k, r2] > 1.5:
                        continue
                    dk = delta(s)
                    if dk is None:
                        continue
                    res.append((s[-1] - s[-3]) - dk * dF); raw.append(s[-1] - s[-3])
                if len(res) < 4:
                    continue
                midf = []                                                # the target's later mid, points, no execution
                for h in HORIZONS:
                    b = at(d, i, h)
                    midf.append(d['mid'][b, j, rr] - tgt[-1] if b is not None else np.nan)
                ex = []                                                  # quote-aware return, delay x horizon
                for L in DELAYS:
                    a = at(d, i, L)
                    fill = a is not None and d['ok'][a, j, rr] and d['age'][a, j, rr] <= L
                    ex.append(d['ask'][a, j, rr] - tgt[-1] if fill else np.nan)       # what the delay costs at the fill, points
                    for h in HORIZONS:
                        b = at(d, a, h) if fill else None
                        ex.append(d['bid'][b, j, rr] / d['ask'][a, j, rr] - 1.0 if b is not None and d['ok'][b, j, rr] else np.nan)
                rows.append((d['date'], d['t'][i], rr, d['K'][j], float(np.mean(res)) - own, own,
                             float(np.mean(raw)) - (tgt[-1] - tgt[-3]), d['ask'][i, j, rr] - d['bid'][i, j, rr], tgt[-1]) + tuple(midf) + tuple(ex))
    dates = np.array([r[0] for r in rows]); ts = np.array([r[1] for r in rows])
    R = np.array([r[4:] for r in rows], float)
    nH = len(HORIZONS)
    MID0, EX0 = 5, 5 + nH                                                 # column offsets inside R
    print(f"N04 rows {len(R)}; median target spread {np.nanmedian(R[:, 3]):.2f} pts")
    res = {}
    for name, col in (('neighbours_minus_own', 0), ('own_momentum', 1), ('raw_cross_avg', 2)):
        sig = R[:, col]
        ud = sorted(set(dates)); pk = []
        prim = EX0 + DELAYS.index(DELAY) * (nH + 1)
        for di, dte in enumerate(ud):
            if di < MIN_TRAIN_DATES:
                continue
            thr = np.quantile(sig[dates < dte], Q)
            busy = -1.0
            for k in np.where(dates == dte)[0]:
                if ts[k] < busy or sig[k] <= thr:
                    continue
                pk.append(k)
                if np.isfinite(R[k, prim]):                               # filled at the primary delay: busy to the exit
                    busy = ts[k] + DELAY + HORIZONS[-1]
        pk = np.array(pk, int)
        r = dict(signals=int(len(pk)), ic_mid={h: round(v1.rank_ic(sig[np.isfinite(R[:, MID0 + q])], R[np.isfinite(R[:, MID0 + q]), MID0 + q]), 4)
                                                 for q, h in enumerate(HORIZONS)},
                 mid_later_pts={h: round(float(np.nanmean(R[pk, MID0 + q])), 3) for q, h in enumerate(HORIZONS)}, by_delay={})
        print(f"N04  {name}: signals {len(pk)}; rank IC against the later mid {r['ic_mid']}")
        print(f"       the target's own mid after the signal, points, no execution: {r['mid_later_pts']}")
        for li, L in enumerate(DELAYS):
            c0 = EX0 + li * (nH + 1)
            filled = np.isfinite(R[pk, c0])
            row = dict(filled=int(filled.sum()), lapsed=int((~filled).sum()),
                       ask_minus_signal_mid_pts=round(float(np.nanmean(R[pk, c0])), 3) if filled.any() else None, ret_pct={}, wins={}, censored={})
            for q, h in enumerate(HORIZONS):
                y = R[pk, c0 + 1 + q]; y = y[filled]
                okk = np.isfinite(y)
                row['ret_pct'][h] = round(100 * float(y[okk].mean()), 3) if okk.any() else None
                row['wins'][h] = int((y[okk] > 0).sum()); row['censored'][h] = int((~okk).sum())
            r['by_delay'][L] = row
            print(f"       delay {L} s: filled {row['filled']}, lapsed {row['lapsed']}, ask at the fill minus the signal mid "
                  f"{row['ask_minus_signal_mid_pts']} pts | quote-aware mean return % by horizon {row['ret_pct']} | wins {row['wins']}")
        r['picks'] = [(dates[k], float(ts[k]), int(rows[k][2]), float(rows[k][3])) + tuple(None if not np.isfinite(v) else float(v) for v in R[k, MID0:]) for k in pk]
        res[name] = r
    return res


def paired(a, b, name_a, name_b):
    """Compare two pick lists on the dates where both traded (docs/38 item 5)."""
    da, db = a['by_day'], b['by_day']
    common = sorted(set(da) & set(db))
    print(f"   paired on {len(common)} common dates: {name_a} sum {sum(da[x] for x in common):+.1f} %, {name_b} sum {sum(db[x] for x in common):+.1f} %, "
          f"{name_a} ahead on {sum(da[x] > db[x] for x in common)} dates")
    return dict(common=common, a_sum=round(sum(da[x] for x in common), 1), b_sum=round(sum(db[x] for x in common), 1),
                a_ahead=sum(da[x] > db[x] for x in common))


if __name__ == '__main__':
    which = sys.argv[1:] or ['n03', 'n05', 'n04']
    days, man = load_all()
    print('parts', len(days), 'dates', len({d['date'] for d in days}), '| delay', DELAY, 's | horizon', H, 's | dataset', DS)
    result = dict(version=2, spec='frozen 9 Nov 2026 (v1 research.py)', delay_s=DELAY, horizon_s=H, datasets=man,
                  expiry_dates=sorted({d['date'] for d in days if d['date'] == d['exp']}))
    if 'n03' in which:
        scale = np.array([5.0, 2.5, 2.5, 0.05])
        sm = [s for d in days for s in n03_samples(d, scale)]
        result['n03_base'] = base_rate(sm, 'N03')
        fs = ('endpoints', 'lags', 'sig2', 'sig2_shuf')
        result['n03'] = walk_forward(sm, fs, 'N03')
        nonexp = {s['date'] for s in sm if not s['dte0']}
        print('N03, the same frozen predictions, non-expiry test dates only:')
        result['n03_frozen_nonexp'] = walk_forward(sm, fs, 'N03f', keep_dates=nonexp)
    if 'n05' in which:
        sm = [s for d in days for s in n05_samples(d)]
        result['n05_base'] = base_rate(sm, 'N05')
        fs = ('fwd_only', 'iv_mom', 'prem_mom', 'surface')
        result['n05'] = walk_forward(sm, fs, 'N05')
        nonexp = {s['date'] for s in sm if not s['dte0']}
        print('N05 (a) the same frozen predictions, non-expiry test dates only:')
        result['n05_frozen_nonexp'] = walk_forward(sm, fs, 'N05a', keep_dates=nonexp)
        print('N05 (b) a separately trained model, expiry days removed before fitting (a DIFFERENT experiment):')
        result['n05_trained_nonexp'] = walk_forward([s for s in sm if not s['dte0']], fs, 'N05b')
        print('N05 surface against IV momentum:')
        result['n05_paired'] = dict(all=paired(result['n05']['surface'], result['n05']['iv_mom'], 'surface', 'iv_mom'),
                                    frozen_nonexp=paired(result['n05_frozen_nonexp']['surface'], result['n05_frozen_nonexp']['iv_mom'], 'surface', 'iv_mom'),
                                    trained_nonexp=paired(result['n05_trained_nonexp']['surface'], result['n05_trained_nonexp']['iv_mom'], 'surface', 'iv_mom'))
    if 'n04' in which:
        result['n04'] = n04(days)
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, 'research_v2_' + '_'.join(which) + '.json')
    json.dump(result, open(dst, 'w'), indent=1, default=float)
    print('written', dst)
