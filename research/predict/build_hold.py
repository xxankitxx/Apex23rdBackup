"""11 Nov 2026 (docs/49 section 6): data, fit and test for the continuation (hold) and re-entry models.

Trades: the five pool books in the 15-day replay p41 (c20_9y, c20_9s, c20_9v, c20_9x, c20_9t). Quotes: ds_v2.
  hold snapshots     every 15 s while a trade is held (from its fill to its real exit). Label: (bid at the real exit -
                     bid now) / entry, in per cent: what holding to the parent's own exit was worth over selling now.
  re-entry snapshots every 15 s for 15 minutes after each real exit, same contract. Label: buy at the ask now, sell
                     at the bid when it falls 8 % from its peak since the buy, after 15 minutes, or at 15:20: result in
                     per cent of the ask.
Features: apex/predict/hold.py, the same functions the engine twins call.

Discipline, fixed before the run:
  - discovery = sessions before 3 Nov; hold-out = 3, 4, 5, 6, 9 Nov.
  - model: ridge regression on standardised features (one alpha), rows weighted so each trade (or each exit window)
    weighs one in total.
  - the decision line is chosen by leave-one-day-out on the discovery sessions (each day's predictions come from a
    model fitted without that day), maximising rupees; the line is then frozen and the final model refitted on all
    discovery sessions; the hold-out is scored once.
  - the hold twin can only sell EARLIER than the parent; the re-entry twin buys at most once per exit window.
Writes apex/predict/hold_v1.json and reenter_v1.json only with --install. Results: data/research/predict/hold_study.json"""
import glob, hashlib, json, os, sys
from datetime import datetime
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT)
os.environ.setdefault('APEX_DATA', os.path.join(ROOT, 'data', 'research', 'predict', '_no_engine_data'))
from apex import config, greeks
from apex.predict import hold as Hd
from apex.forecast_lab.core import iv_newton
DS = os.path.join(ROOT, 'data', 'research', 'ds_v2')
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
BOOKS = ('c20_9y', 'c20_9s', 'c20_9v', 'c20_9x', 'c20_9t')
SPLIT = '2026-11-03'
ALPHA = 10.0
CLOSE_S = 15 * 3600 + 20 * 60


def sod(t):
    return (int(t) + 19800) % 86400


def load_day(day):
    out = []
    for p in sorted(glob.glob(os.path.join(DS, f'{day}*.npz'))):
        z = np.load(p)
        n = len(z['strikes']); order = np.argsort(z['strikes'])
        o = z['opt'][:, :n].astype(float)[:, order]
        fut = z['fut'].astype(float)
        fm = np.where((fut[:, 0] > 0) & (fut[:, 1] >= fut[:, 0]), 0.5 * (fut[:, 0] + fut[:, 1]), fut[:, 2])
        out.append(dict(t=z['t'].astype(float), K=z['strikes'][order].astype(float), bid=o[..., 0], ask=o[..., 1],
                        age=z['age'][:, :n].astype(float)[:, order], exp=str(z['expiry']), fm=fm))
    return out


def part_for(parts, tr, t):
    for P in parts:
        if P['exp'] == tr['expiry'] and P['t'][0] <= t <= P['t'][-1]:
            return P
    return None


def series(P, j, rr, a, b):
    """1-Hz (t, bid, ask, mid) of one contract between rows a and b; stale rows dropped."""
    bid, ask, age = P['bid'][a:b, j, rr], P['ask'][a:b, j, rr], P['age'][a:b, j, rr]
    ok = (bid > 0) & (ask >= bid) & (age <= 15)
    t = P['t'][a:b][ok]
    return t, bid[ok], ask[ok], 0.5 * (bid[ok] + ask[ok])


def opt_iv(P, i, j, rr, mid):
    mids = np.where((P['bid'][i] > 0) & (P['ask'][i] >= P['bid'][i]), 0.5 * (P['bid'][i] + P['ask'][i]), np.nan)
    Fs = greeks.synthetic_forward(P['K'], mids[:, 0], mids[:, 1], P['fm'][i])
    if not Fs or not np.isfinite(Fs):
        return None
    T = greeks.years_to_expiry(P['exp'], datetime.fromtimestamp(P['t'][i], config.IST))
    v = iv_newton(np.array([mid]), float(Fs), np.array([P['K'][j]]), T, np.array([rr == 0]))[0]
    return float(v) if np.isfinite(v) else None


def build():
    H, R = [], []                                         # rows: dict(day, book, tid, x, y, ...)
    files = sorted(glob.glob(os.path.join(ROOT, 'data', 'replay', 'batch', 'p41_g*', 'paper', '2026-*.json')))
    for f in files:
        day = os.path.basename(f)[:10]
        books = json.load(open(f, encoding='utf-8'))
        parts = load_day(day)
        dte = None
        for b in BOOKS:
            for n_t, tr in enumerate(t for t in books.get(b, {}).get('trades', []) if t.get('exit') is not None):
                P = part_for(parts, tr, tr['t_in'])
                if P is None:
                    continue
                j = np.where(P['K'] == float(tr['strike']))[0]
                if not len(j):
                    continue
                j = int(j[0]); rr = 0 if tr['rr'] == 'CE' else 1
                d = 1 if rr == 0 else -1
                dte = (np.datetime64(P['exp']) - np.datetime64(day)).astype(int)
                a = int(np.searchsorted(P['t'], tr['t_in'] - 700))
                e_out = int(np.searchsorted(P['t'], tr['t_out'], side='right'))
                e_post = int(np.searchsorted(P['t'], tr['t_out'] + Hd.REENTER_WINDOW_S + Hd.RE_HOLD_S, side='right'))
                fut_hist = list(zip(P['t'][a:e_post].tolist(), P['fm'][a:e_post].tolist()))
                t, bid, ask, mid = series(P, j, rr, a, e_post)
                if len(t) < 30:
                    continue
                mid_hist = list(zip(t.tolist(), mid.tolist()))
                tid = f"{b}|{day}|{n_t}"
                held = (t >= tr['t_in']) & (t <= tr['t_out'])
                ix = np.where(held)[0]
                if len(ix) < 2:
                    continue
                exit_bid = tr['exit']
                pk, tpk = -np.inf, tr['t_in']
                last_s = -1e9
                for k in ix:
                    if bid[k] > pk:
                        pk, tpk = bid[k], t[k]
                    if t[k] - last_s < Hd.CHECK_S or t[k] < tr['t_in'] + Hd.CHECK_S:
                        continue
                    last_s = t[k]
                    i_row = int(np.searchsorted(P['t'], t[k]))
                    iv = opt_iv(P, min(i_row, len(P['t']) - 1), j, rr, mid[k])
                    x = Hd.hold_features(t[k], tr['entry'], bid[k], ask[k], [m for m in mid_hist if m[0] <= t[k]], pk,
                                         tr['t_in'], tpk, [q for q in fut_hist if q[0] <= t[k]], d, iv, dte, sod(t[k]) - (9 * 3600 + 15 * 60))
                    if x is None:
                        continue
                    H.append(dict(day=day, book=b, tid=tid, t=float(t[k]), x=x, y=100.0 * (exit_bid - bid[k]) / tr['entry'],
                                  bid=float(bid[k]), entry=tr['entry'], exit=exit_bid, qty=tr['qty']))
                # after the exit
                post = np.where((t > tr['t_out']) & (t <= tr['t_out'] + Hd.REENTER_WINDOW_S))[0]
                last_s = -1e9
                for k in post:
                    if t[k] - last_s < Hd.CHECK_S or sod(t[k]) >= CLOSE_S:
                        continue
                    last_s = t[k]
                    # the fixed exit of a leg bought now
                    hi, xb = bid[k], None
                    for m in range(k + 1, len(t)):
                        hi = max(hi, bid[m])
                        if bid[m] <= hi * (1 - Hd.RE_TRAIL) or t[m] - t[k] >= Hd.RE_HOLD_S or sod(t[m]) >= CLOSE_S:
                            xb = bid[m]
                            break
                    if xb is None:
                        continue
                    i_row = int(np.searchsorted(P['t'], t[k]))
                    iv = opt_iv(P, min(i_row, len(P['t']) - 1), j, rr, mid[k])
                    x = Hd.re_features(t[k], tr['t_out'], exit_bid, tr['exit'] / tr['entry'] - 1.0, pk, bid[k], ask[k],
                                       [m for m in mid_hist if m[0] <= t[k]], [q for q in fut_hist if q[0] <= t[k]], d, iv, dte,
                                       sod(t[k]) - (9 * 3600 + 15 * 60))
                    if x is None:
                        continue
                    R.append(dict(day=day, book=b, tid=tid, t=float(t[k]), x=x, y=100.0 * (xb / ask[k] - 1.0),
                                  ask=float(ask[k]), xb=float(xb), qty=tr['qty']))
        print(day, 'hold rows', len(H), 're-entry rows', len(R), flush=True)
    return H, R


def fit(rows, feats):
    from sklearn.linear_model import Ridge
    X = np.array([r['x'] for r in rows]); y = np.clip(np.array([r['y'] for r in rows]), -60, 60)
    tid = np.array([r['tid'] for r in rows])
    _, inv, cnt = np.unique(tid, return_inverse=True, return_counts=True)
    w = 1.0 / cnt[inv]
    med = np.median(X, 0); sd = np.std(X, 0); sd = np.where(sd > 1e-9, sd, 1.0)
    Z = np.clip((X - med) / sd, -5, 5)
    m = Ridge(alpha=ALPHA).fit(Z, y, sample_weight=w)
    return dict(feats=list(feats), med=med.tolist(), sd=sd.tolist(), w=[float(m.intercept_)] + m.coef_.tolist(), alpha=ALPHA)


def predict(mdl, rows):
    return np.array([Hd.Linear(art=dict(mdl, line=0.0)).predict(r['x']) for r in rows])


def hold_policy(rows, pred, line):
    """Rupee change against the parent: per trade, sell at the first check whose prediction is below the line."""
    by = {}
    for r, p in zip(rows, pred):
        by.setdefault(r['tid'], []).append((r['t'], p, r))
    tot, fired, helped, hurt, per_day = 0.0, 0, 0, 0, {}
    for tid, L in by.items():
        L.sort(key=lambda z: z[0])
        for _, p, r in L:
            if p < line:
                ch = (r['bid'] - r['exit']) * r['qty']
                tot += ch; fired += 1; helped += ch > 0; hurt += ch < 0
                per_day[r['day']] = per_day.get(r['day'], 0.0) + ch
                break
    return tot, fired, helped, hurt, per_day


def re_policy(rows, pred, line):
    """Rupees from re-entries: in each exit window, buy at the first check whose prediction is above the line."""
    by = {}
    for r, p in zip(rows, pred):
        by.setdefault(r['tid'], []).append((r['t'], p, r))
    tot, n, won, per_day = 0.0, 0, 0, {}
    for tid, L in by.items():
        L.sort(key=lambda z: z[0])
        for _, p, r in L:
            if p > line:
                g = (r['xb'] - r['ask']) * r['qty']
                tot += g; n += 1; won += g > 0
                per_day[r['day']] = per_day.get(r['day'], 0.0) + g
                break
    return tot, n, won, per_day


def lodo(rows, feats, policy, lines):
    """Leave one discovery day out: predictions for each day from a model fitted without it; rupees by line."""
    days = sorted({r['day'] for r in rows})
    pred = np.zeros(len(rows))
    for d in days:
        tr = [r for r in rows if r['day'] != d]
        mdl = fit(tr, feats)
        ix = [i for i, r in enumerate(rows) if r['day'] == d]
        pred[ix] = predict(mdl, [rows[i] for i in ix])
    return {ln: policy(rows, pred, ln) for ln in lines}, pred


def main():
    H, R = build()
    out = dict(split=SPLIT, alpha=ALPHA, n_hold=len(H), n_re=len(R))
    for name, rows, feats, policy, lines in (
            ('hold', H, Hd.HOLD_FEATS, hold_policy, [-20, -15, -10, -7, -5, -3, -2, -1, 0]),
            ('reenter', R, Hd.RE_FEATS, re_policy, [0, 1, 2, 3, 4, 6, 8])):
        disc = [r for r in rows if r['day'] < SPLIT]
        hold = [r for r in rows if r['day'] >= SPLIT]
        res, _ = lodo(disc, feats, policy, lines)
        best = max(lines, key=lambda ln: res[ln][0])
        mdl = fit(disc, feats)
        ph = predict(mdl, hold)
        ho = policy(hold, ph, best)
        # c20_9y only, the twin's parent
        h9 = [r for r in hold if r['book'] == 'c20_9y']
        ho9 = policy(h9, predict(mdl, h9), best)
        print(f"\n{name.upper()} model: {len(disc)} discovery rows, {len(hold)} hold-out rows")
        for ln in lines:
            v = res[ln]
            print(f"  line {ln:+4}: leave-one-day-out rupees {v[0]:+,.0f}, decisions {v[1]}" + (f", helped {v[2]} hurt {v[3]}" if name == 'hold' else f", won {v[2]}"))
        print(f"  chosen line {best:+}; HOLD-OUT all five books: rupees {ho[0]:+,.0f}, decisions {ho[1]}" +
              (f", helped {ho[2]} hurt {ho[3]}" if name == 'hold' else f", won {ho[2]}") + f"; by day {dict((k, round(v)) for k, v in sorted(ho[-1].items()))}")
        print(f"  hold-out c20_9y only: rupees {ho9[0]:+,.0f}, decisions {ho9[1]}")
        print('  weights:', dict(zip(['intercept'] + list(feats), np.round(mdl['w'], 2))))
        art = dict(mdl, line=float(best), kind=name, trained_days=sorted({r['day'] for r in disc}), books=list(BOOKS),
                   version=1, built=__import__('time').strftime('%Y-%m-%d %H:%M:%S'),
                   evidence=dict(lodo={str(k): [round(v[0]), v[1]] for k, v in res.items()}, holdout_rs=round(ho[0]),
                                 holdout_decisions=ho[1], holdout_c20_9y_rs=round(ho9[0])))
        art['hash'] = hashlib.sha256(json.dumps(art, sort_keys=True).encode()).hexdigest()[:12]
        out[name] = art
        if '--install' in sys.argv:
            json.dump(art, open(Hd.HOLD_FILE if name == 'hold' else Hd.REENTER_FILE, 'w'), indent=1)
            print('  installed', Hd.HOLD_FILE if name == 'hold' else Hd.REENTER_FILE)
    json.dump(out, open(os.path.join(OUT, 'hold_study.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
