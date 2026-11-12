"""11 Nov 2026 (owner: "we are giving away a lot of points from the peak ... could have booked higher and re-entered the
same direction if the conviction to run was still strong"): giveback and tighter-trail counterfactuals on the
champion family's REAL trades, on the recorded quotes.

Source: the 15-day replay p41 (10 Nov code), books c20_9y (the Conductor's main source) and the other pool members
c20_9s, c20_9v, c20_9x, c20_9t. For each trade the held contract's bid and ask are read second by second from
data/research/ds_v2 between the fill and the actual exit.

Variants, applied ON TOP of the book's own exits (the variant can only exit EARLIER than the real exit):
  trail g after arm a   once the bid has been >= entry x (1 + a), exit when the bid <= its peak x (1 - g)
  lock k after arm a    once the peak gain is >= a, exit when the gain <= k x the peak gain
  + re-entry            after a variant exit, if before the real exit the bid makes a NEW HIGH above the peak seen
                        before the variant exit (the run resumed: a price confirmation, the conviction proxy), buy
                        again at that second's ask, same contract, same quantity; that leg exits by the same variant
                        or at the real exit, whichever first; at most 3 re-entries a trade
Fills: sell at the bid of the exit second, buy at the ask; no slippage or costs (owner's rule). Quantity: the trade's
own quantity for every leg (all-in compounding is not re-simulated: rupees are per-trade sums).

Selection discipline: variants are RANKED on the first 10 sessions (19 Oct - 2 Nov) only; the last 5 (3 - 9 Nov) are
the hold-out. Both are reported for every variant. In-sample for the books themselves (they were built on these days).

Output: data/research/predict/trail_study.json and tables on screen. Usage: py -3.13 research/predict/trail_study.py"""
import glob, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DS = os.path.join(ROOT, 'data', 'research', 'ds_v2')
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
BOOKS = ('c20_9y', 'c20_9s', 'c20_9v', 'c20_9x', 'c20_9t')
SPLIT = '2026-11-03'                      # sessions before this date rank the variants; the rest are held out


def load_day(day):
    out = []
    for p in sorted(glob.glob(os.path.join(DS, f'{day}*.npz'))):
        z = np.load(p)
        n = len(z['strikes']); order = np.argsort(z['strikes'])
        o = z['opt'][:, :n].astype(float)[:, order]
        out.append(dict(t=z['t'].astype(float), K=z['strikes'][order].astype(float), bid=o[..., 0], ask=o[..., 1],
                        age=z['age'][:, :n].astype(float)[:, order], exp=str(z['expiry'])))
    return out


def path(parts, tr):
    """Seconds, bid, ask of the trade's contract from the fill to the real exit (stale or one-sided quotes dropped)."""
    rr = 0 if tr['rr'] == 'CE' else 1
    for P in parts:
        if P['exp'] != tr['expiry'] or not (P['t'][0] <= tr['t_in'] <= P['t'][-1]):
            continue
        j = np.where(P['K'] == float(tr['strike']))[0]
        if not len(j):
            return None
        a, b = np.searchsorted(P['t'], tr['t_in']), np.searchsorted(P['t'], tr['t_out'], side='right')
        bid, ask, age = P['bid'][a:b, j[0], rr], P['ask'][a:b, j[0], rr], P['age'][a:b, j[0], rr]
        ok = (bid > 0) & (ask >= bid) & (age <= 15)
        return P['t'][a:b][ok], bid[ok], ask[ok]
    return None


def simulate(tr, pth, kind, a, g, reenter):
    """Rupee P&L and legs of one trade under a variant. kind: 'trail' (g = giveback fraction of the peak bid) or
    'lock' (g = fraction of the peak gain kept)."""
    t, bid, ask = pth
    q = tr['qty']
    legs = []
    entry = tr['entry']
    i = 0
    n = len(t)
    real_exit = tr['exit']
    while True:
        peak = -np.inf
        armed = False
        out = None
        for k in range(i, n):
            peak = max(peak, bid[k])
            gain_pk = peak / entry - 1.0
            if gain_pk >= a:
                armed = True
            if armed:
                hit = bid[k] <= peak * (1 - g) if kind == 'trail' else (bid[k] / entry - 1.0) <= g * gain_pk
                if hit:
                    out = k
                    break
        if out is None:                                    # the variant never fired: the real exit stands
            legs.append((entry, real_exit))
            break
        legs.append((entry, bid[out]))
        if not reenter or len(legs) > 3:
            break
        ref = peak                                         # re-enter only on a new high above the peak before exit
        nxt = None
        for k in range(out + 1, n):
            if bid[k] > ref:
                nxt = k
                break
        if nxt is None:
            break
        entry, i = ask[nxt], nxt
    pnl = sum((x - e) * q for e, x in legs)
    ret = sum((x / e - 1.0) * 100.0 for e, x in legs)
    return pnl, ret, len(legs)


def main():
    trades = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'replay', 'batch', 'p41_g*', 'paper', '2026-*.json'))):
        day = os.path.basename(f)[:10]
        books = json.load(open(f, encoding='utf-8'))
        sel = {b: [t for t in books.get(b, {}).get('trades', []) if t.get('exit') is not None] for b in BOOKS}
        if not any(sel.values()):
            continue
        parts = load_day(day)
        for b, ts in sel.items():
            for tr in ts:
                p = path(parts, tr)
                if p is None or len(p[0]) < 3:
                    continue
                t, bid, ask = p
                pk = float(np.max(bid))
                trades.append(dict(book=b, day=day, tr=tr, p=p, peak=pk, peak_g=pk / tr['entry'] - 1.0,
                                   exit_g=tr['exit'] / tr['entry'] - 1.0, reason=str(tr.get('reason', '?')).split(' (')[0]))
    print('trades with a recorded path:', len(trades), {b: sum(1 for x in trades if x['book'] == b) for b in BOOKS})
    # 1. giveback from the peak
    rows = []
    for b in BOOKS:
        T = [x for x in trades if x['book'] == b]
        if not T:
            continue
        gb_rs = [(x['peak'] - x['tr']['exit']) * x['tr']['qty'] for x in T]
        win = [x for x in T if x['tr']['pnl_rs'] > 0]
        pk_rs = sum(max(x['peak'] - x['tr']['entry'], 0) * x['tr']['qty'] for x in T)
        rows.append(dict(book=b, trades=len(T), pnl_rs=round(sum(x['tr']['pnl_rs'] for x in T)),
                         peak_rs=round(pk_rs), giveback_rs=round(sum(gb_rs)),
                         captured_pct_of_peak=round(100 * sum(x['tr']['pnl_rs'] for x in T) / pk_rs, 1) if pk_rs else None,
                         median_peak_gain=round(100 * float(np.median([x['peak_g'] for x in T])), 1),
                         median_exit_gain=round(100 * float(np.median([x['exit_g'] for x in T])), 1),
                         winners_giveback_median_pct=round(100 * float(np.median([(x['peak'] - x['tr']['exit']) / x['tr']['entry'] for x in win])), 1) if win else None,
                         losers_that_were_up_5=sum(1 for x in T if x['tr']['pnl_rs'] <= 0 and x['peak_g'] >= 0.05),
                         losers_that_were_up_10=sum(1 for x in T if x['tr']['pnl_rs'] <= 0 and x['peak_g'] >= 0.10),
                         losers=sum(1 for x in T if x['tr']['pnl_rs'] <= 0)))
    print('\n1. GIVEBACK FROM THE PEAK (rupees per trade summed; peak = best bid between fill and exit)')
    for r in rows:
        print(' ', r)
    # giveback by exit reason, c20_9y
    T = [x for x in trades if x['book'] == 'c20_9y']
    by = {}
    for x in T:
        d = by.setdefault(x['reason'], [0, 0.0, 0.0])
        d[0] += 1; d[1] += (x['peak'] - x['tr']['exit']) * x['tr']['qty']; d[2] += x['tr']['pnl_rs']
    print('  c20_9y by exit reason (trades, giveback Rs, P&L Rs):', {k: (v[0], round(v[1]), round(v[2])) for k, v in sorted(by.items(), key=lambda kv: -kv[1][1])})
    # 2. variants
    grid = [('trail', a, g) for a in (0.05, 0.10, 0.15, 0.25) for g in (0.03, 0.05, 0.08, 0.12, 0.18)] + \
           [('lock', a, k) for a in (0.05, 0.10, 0.15, 0.25) for k in (0.5, 0.6, 0.7, 0.8)]
    res = []
    for kind, a, g in grid:
        for re_ in (False, True):
            rec = dict(kind=kind, arm=a, param=g, reenter=re_)
            for b in BOOKS:
                T = [x for x in trades if x['book'] == b]
                if not T:
                    continue
                d = dict(disc=[0.0, 0.0, 0, 0], hold=[0.0, 0.0, 0, 0], days_up=0, days=0)
                byday = {}
                for x in T:
                    pnl, ret, legs = simulate(x['tr'], x['p'], kind, a, g, re_)
                    s = 'disc' if x['day'] < SPLIT else 'hold'
                    d[s][0] += pnl; d[s][1] += x['tr']['pnl_rs']; d[s][2] += legs; d[s][3] += 1
                    bd = byday.setdefault(x['day'], [0.0, 0.0]); bd[0] += pnl; bd[1] += x['tr']['pnl_rs']
                rec[b] = dict(disc_rs=round(d['disc'][0]), disc_base=round(d['disc'][1]), hold_rs=round(d['hold'][0]),
                              hold_base=round(d['hold'][1]), legs=d['disc'][2] + d['hold'][2], trades=d['disc'][3] + d['hold'][3],
                              days_better=sum(1 for v in byday.values() if v[0] > v[1] + 1),
                              days_worse=sum(1 for v in byday.values() if v[0] < v[1] - 1))
            res.append(rec)
    base = {b: next(r[b] for r in res if b in r) for b in BOOKS if any(b in r for r in res)}
    print('\n2. VARIANTS on c20_9y, ranked by the DISCOVERY sessions only (19 Oct - 2 Nov); hold-out = 3 - 9 Nov')
    print(f"   baseline: discovery Rs {base['c20_9y']['disc_base']:,}, hold-out Rs {base['c20_9y']['hold_base']:,}")
    rk = sorted(res, key=lambda r: -(r['c20_9y']['disc_rs'] - r['c20_9y']['disc_base']))
    for r in rk[:12] + rk[-4:]:
        c = r['c20_9y']
        others = sum(1 for b in BOOKS if b != 'c20_9y' and b in r and r[b]['hold_rs'] > r[b]['hold_base'])
        print(f"   {r['kind']:5s} arm {r['arm']:.2f} {'g' if r['kind'] == 'trail' else 'k'} {r['param']:.2f} re-entry {'yes' if r['reenter'] else 'no '}"
              f" | disc {c['disc_rs'] - c['disc_base']:+,.0f} | hold-out {c['hold_rs'] - c['hold_base']:+,.0f} | days better/worse {c['days_better']}/{c['days_worse']}"
              f" | legs {c['legs']} for {c['trades']} trades | other pool books better in hold-out: {others}/4")
    json.dump(dict(split=SPLIT, giveback=rows, variants=res), open(os.path.join(OUT, 'trail_study.json'), 'w'), indent=1)


if __name__ == '__main__' and len(sys.argv) == 1:
    main()


def after_exit():
    """3. After the champion's OWN exit: did the run continue? For each c20_9y trade, the same contract's best bid in
    the 5 and 15 minutes after the exit, against the exit price, and a re-entry rule: buy again at the ask when the bid
    makes a new high above the trade's own peak within 15 minutes of the exit, sell at the bid when it falls 8 % from
    its new peak or after 15 minutes, whichever first."""
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'replay', 'batch', 'p41_g*', 'paper', '2026-*.json'))):
        day = os.path.basename(f)[:10]
        ts = [t for t in json.load(open(f, encoding='utf-8')).get('c20_9y', {}).get('trades', []) if t.get('exit') is not None]
        if not ts:
            continue
        parts = load_day(day)
        for tr in ts:
            full = path(parts, dict(tr, t_out=tr['t_out'] + 900))
            if full is None:
                continue
            t, bid, ask = full
            inside = t <= tr['t_out']
            if inside.sum() < 2 or (~inside).sum() < 30:
                continue
            pk = float(bid[inside].max())
            post_t, post_b, post_a = t[~inside], bid[~inside], ask[~inside]
            m5 = float(post_b[post_t <= tr['t_out'] + 300].max()) if (post_t <= tr['t_out'] + 300).any() else np.nan
            m15 = float(post_b.max())
            re = None
            k = np.where(post_b > pk)[0]
            if len(k):
                e = post_a[k[0]]; hi = post_b[k[0]]; x = post_b[-1]
                for j in range(k[0], len(post_b)):
                    hi = max(hi, post_b[j])
                    if post_b[j] <= hi * 0.92:
                        x = post_b[j]
                        break
                re = (x - e) * tr['qty']
            rows.append(dict(day=day, reason=str(tr.get('reason')).split(' (')[0], won=tr['pnl_rs'] > 0, exit=tr['exit'],
                             up5=(m5 / tr['exit'] - 1) * 100, up15=(m15 / tr['exit'] - 1) * 100, re=re))
    print('\n3. AFTER THE CHAMPION\'S OWN EXIT (c20_9y, same contract, next 15 minutes)')
    for nm, sel in (('all', lambda r: True), ('profitable exits', lambda r: r['won']), ('losing exits', lambda r: not r['won'])):
        R = [r for r in rows if sel(r)]
        if not R:
            continue
        reent = [r['re'] for r in R if r['re'] is not None]
        print(f"   {nm:17s} n {len(R)}: bid went >5 % above the exit within 5 min on {sum(r['up5'] > 5 for r in R)}, within 15 min on {sum(r['up15'] > 5 for r in R)};"
              f" re-entry on a new high fired {len(reent)} times, {sum(x > 0 for x in reent)} won, total Rs {sum(reent):+,.0f}")
    by = {}
    for r in rows:
        if r['re'] is not None:
            d = by.setdefault(r['reason'], [0, 0, 0.0]); d[0] += 1; d[1] += r['re'] > 0; d[2] += r['re']
    print('   re-entry by the exit that preceded it (n, won, Rs):', {k: (v[0], v[1], round(v[2])) for k, v in by.items()})
    d1 = [r for r in rows if r['re'] is not None and r['day'] < SPLIT]; d2 = [r for r in rows if r['re'] is not None and r['day'] >= SPLIT]
    print(f"   discovery Rs {sum(r['re'] for r in d1):+,.0f} on {len(d1)}; hold-out Rs {sum(r['re'] for r in d2):+,.0f} on {len(d2)}")


def be_rules():
    """4. Rules aimed only at trades that were up and then went to a loss: once the peak gain reached a, never let
    the bid fall below entry x (1 + f)."""
    trades = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'replay', 'batch', 'p41_g*', 'paper', '2026-*.json'))):
        day = os.path.basename(f)[:10]
        ts = [t for t in json.load(open(f, encoding='utf-8')).get('c20_9y', {}).get('trades', []) if t.get('exit') is not None]
        if ts:
            parts = load_day(day)
            trades += [(day, tr, path(parts, tr)) for tr in ts]
    print('\n4. FLOOR RULES on c20_9y: once the peak gain reached a, exit if the bid falls to entry x (1 + f)')
    for a in (0.08, 0.10, 0.12, 0.15, 0.20):
        for fl in (0.0, 0.02, 0.04):
            dd = {'disc': 0.0, 'hold': 0.0}; fired = saved = cut = 0
            for day, tr, p in trades:
                if p is None or len(p[0]) < 2:
                    continue
                t, bid, ask = p
                pk = np.maximum.accumulate(bid)
                hit = np.where((pk >= tr['entry'] * (1 + a)) & (bid <= tr['entry'] * (1 + fl)))[0]
                new = (bid[hit[0]] - tr['entry']) * tr['qty'] if len(hit) else tr['pnl_rs']
                if len(hit):
                    fired += 1
                    saved += new > tr['pnl_rs']
                    cut += new < tr['pnl_rs']
                dd['disc' if day < SPLIT else 'hold'] += new - tr['pnl_rs']
            print(f"   arm {a:.2f} floor {fl:+.2f}: fired {fired}, helped {saved}, hurt {cut}; change discovery Rs {dd['disc']:+,.0f}, hold-out Rs {dd['hold']:+,.0f}")


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'more':
    after_exit()
    be_rules()
