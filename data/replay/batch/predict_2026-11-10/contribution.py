"""10 Nov 2026, night (docs/40 M5, docs/41 section 13): account contribution of the forecast books, the twins and the
third-generation books against c20_9y and the Conductor, on the overnight replay p41_g1..p41_g8 (15 days, 105 books).

All-in on every trade, no sizing, no costs: a trade's return is exit / entry - 1 on the engine's own fills.
Per book and day: trades, won, lost, the sum of returns in per cent, and the all-in compounded account (start 100).
Reads only finished days (a paper/<day>.json whose group manifest lists that tape as done, or any present file with
--all). Output: data/research/predict/contribution_p41.json and a table on the screen."""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
BATCH = os.path.join(ROOT, 'data', 'replay', 'batch')
BOOKS = ['conductor', 'c20_9y', 'fx_c20_9y', 'fr_c20_9y', 'c20_9x', 'p02_clock', 'p02_top1', 'p02_ctl_mom', 'p05_adaptive',
         's01_transmit', 's01_ctl_cash', 's01_ctl_sfut', 's03_recruit', 'n06_ctl_breadth', 'n01_ctl_price_ind', 'n02_ctl_mr']


def ret(t):
    e, x = t.get('entry'), t.get('exit')
    return (x / e - 1.0) * 100.0 if e and x is not None else None


def main():
    files = sorted(glob.glob(os.path.join(BATCH, 'p41_g*', 'paper', '2026-*.json')))
    days, per, reasons, allbooks = [], {}, {}, {}
    for f in files:
        day = os.path.basename(f)[:10]
        g = f.replace('\\', '/').split('/')[-3]
        # a day is finished when a later tape of the group exists, or the group's manifest says finished
        man = json.load(open(os.path.join(BATCH, g, 'manifest.json'), encoding='utf-8'))
        later = [x for x in glob.glob(os.path.join(BATCH, g, 'paper', '2026-*.json')) if os.path.basename(x)[:10] > day]
        if not (man.get('finished') or later or '--all' in sys.argv):
            print('not finished, skipped:', g, day)
            continue
        d = json.load(open(f, encoding='utf-8'))
        days.append(day)
        for name, b in d.items():
            if not isinstance(b, dict) or 'trades' not in b:
                continue
            rs = [(ret(t), t) for t in b['trades']]
            rs = [(r, t) for r, t in rs if r is not None]
            row = dict(n=len(rs), won=sum(1 for r, _ in rs if r > 0), lost=sum(1 for r, _ in rs if r <= 0),
                       sum=round(sum(r for r, _ in rs), 2), worst=round(min((r for r, _ in rs), default=0.0), 2),
                       best=round(max((r for r, _ in rs), default=0.0), 2))
            acc = 1.0
            for r, _ in rs:
                acc *= 1.0 + r / 100.0
            row['account'] = acc
            allbooks.setdefault(name, {})[day] = row
            if name in BOOKS:
                for r, t in rs:
                    k = str(t.get('reason', '?')).split(' @')[0].split(' (')[0][:28]
                    a = reasons.setdefault(name, {}).setdefault(k, [0, 0, 0.0])
                    a[0] += 1; a[1] += r > 0; a[2] += r
    days = sorted(set(days))
    out = dict(days=days, books={}, reasons={k: {r: dict(n=v[0], won=v[1], sum=round(v[2], 2)) for r, v in rr.items()} for k, rr in reasons.items()})
    print('days read:', len(days), ' '.join(d[5:] for d in days))
    print(f"{'book':20s} {'trades':>6s} {'won':>5s} {'lost':>5s} {'sum %':>9s} {'mean %':>7s} {'days+':>5s} {'days-':>5s} {'worst %':>8s} {'account':>9s}")

    def line(name):
        dd = allbooks.get(name, {})
        n = sum(v['n'] for v in dd.values()); w = sum(v['won'] for v in dd.values()); l = sum(v['lost'] for v in dd.values())
        s = sum(v['sum'] for v in dd.values())
        acc = 100.0
        for day in days:
            acc *= dd.get(day, {}).get('account', 1.0)
        up = sum(1 for v in dd.values() if v['sum'] > 0); dn = sum(1 for v in dd.values() if v['sum'] < 0)
        worst = min((v['worst'] for v in dd.values()), default=0.0)
        return dict(trades=n, won=w, lost=l, sum=round(s, 2), mean=round(s / n, 3) if n else None, days_up=up, days_down=dn,
                    worst_trade=worst, account=round(acc, 1), by_day={day: dd.get(day, {}).get('sum', 0.0) for day in days},
                    trades_by_day={day: dd.get(day, {}).get('n', 0) for day in days})
    for name in BOOKS:
        r = line(name); out['books'][name] = r
        print(f"{name:20s} {r['trades']:6d} {r['won']:5d} {r['lost']:5d} {r['sum']:9.1f} {(r['mean'] or 0):7.2f} {r['days_up']:5d} {r['days_down']:5d} {r['worst_trade']:8.1f} {r['account']:9.1f}")
    print('\nby day, sum of returns %')
    print(f"{'book':20s} " + ' '.join(f'{d[5:]:>6s}' for d in days))
    for name in BOOKS:
        print(f"{name:20s} " + ' '.join(f"{out['books'][name]['by_day'][d]:6.0f}" for d in days))
    print('\nexit reasons (trades, won, sum %)')
    for name in BOOKS:
        if name in out['reasons']:
            print(f"{name:20s} " + '; '.join(f"{k}: {v['n']}/{v['won']}/{v['sum']:+.0f}" for k, v in sorted(out['reasons'][name].items(), key=lambda kv: -kv[1]['n'])[:6]))
    # every book, ranked: how the forecast books stand among all 105
    rank = sorted(((n, line(n)) for n in allbooks), key=lambda kv: -kv[1]['sum'])
    out['rank_by_sum'] = [dict(book=n, trades=r['trades'], won=r['won'], lost=r['lost'], sum=r['sum'], days_up=r['days_up'], days_down=r['days_down']) for n, r in rank]
    print('\nrank by sum of returns among', len(rank), 'books: top 10')
    for i, (n, r) in enumerate(rank[:10]):
        print(f"{i + 1:3d} {n:28s} {r['trades']:5d} {r['won']:4d}W {r['lost']:4d}L {r['sum']:9.1f}")
    for n in ('p02_clock', 'p02_top1', 'p02_ctl_mom', 'p05_adaptive', 'fx_c20_9y', 'fr_c20_9y', 'c20_9y', 'conductor', 's03_recruit', 's01_transmit'):
        i = [k for k, (m, _) in enumerate(rank) if m == n]
        if i:
            print(f"    {n:20s} rank {i[0] + 1}")
    no_loss = [n for n, r in rank if r['trades'] and r['lost'] == 0]
    out['books_without_a_losing_trade'] = no_loss
    print('books with trades and no losing trade:', no_loss or 'none')
    json.dump(out, open(os.path.join(ROOT, 'data', 'research', 'predict', 'contribution_p41.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
