"""Read-only reconstruction of the published A-E closed-trade simulations.

Run from the repository root. Writes only this audit folder. No tape replay,
runtime imports, rule registration, or modifications to Claude's outputs.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'codex_audit'
summary = json.loads((BASE / 'sim_summary.json').read_text())
cards = json.loads((BASE / 'book_cards.json').read_text())['cards']
proposal = json.loads((BASE / 'pool_proposal.json').read_text())
gates = {e['book']: r for e, r in zip(proposal['entries'], proposal['rules'])}
family = ['c20_9y', 'c20_9s', 'c20_9v', 'c20_9x', 'c20_9t']
pools = [['c20_9x'], family, family + list(gates), list(gates), family + ['c20_8x', 'c20_9e', 'c20_9h']]
days = [d[0] for d in next(iter(summary.values()))['days']]
books_by_day = {d: json.loads((BASE.parent / ('v3_' + d) / 'paper' / (d + '.json')).read_text()) for d in days}

def simulate(books, names):
    priority = {n: gates[n]['card']['kept_ret'] if n in gates else cards[n]['real_mean'] for n in names}
    candidates = sorted([(float(t.get('trigger_t') if t.get('trigger_t') is not None else t['t_in']), -priority[n], n, t)
                         for n in names for t in books[n]['trades']
                         if all(t.get(k) is not None for k in ('entry', 'exit', 't_in'))], key=lambda x: (x[0], x[1]))
    cap, held, taken, blocked = 100000., None, [], []
    for trig, _, n, t in candidates:
        if held and (trig <= held[0] or trig < held[1] or (trig == held[1] and n == held[2])):
            blocked.append({'src': n, 'trigger_t': trig, 'by': held[2], 'entry': t['entry'], 'exit': t['exit']})
            continue
        held = None
        gate = gates.get(n)
        val = (t.get('weather_trig') or {}).get(gate['factor']) if gate else None
        if gate and (val is None or not (val < gate['line'] if gate['op'] == '<' else val >= gate['line'])):
            continue
        lots = int(cap // (float(t['entry']) * 65))
        if lots < 1:
            continue
        pnl = round((float(t['exit']) - float(t['entry'])) * lots * 65, 2)
        cap = round(cap + pnl, 2)
        held = trig, float(t['t_out']), n
        taken.append({k: t.get(k) for k in ('key', 't_in', 't_out', 'time_in', 'time_out', 'entry', 'exit', 'reason', 'peak_pts', 'worst_pts')} |
                     {'src': n, 'trigger_t': trig, 'lots': lots, 'pnl_rs': pnl, 'capital_after': cap,
                      'gate': gate['id'] if gate else None, 'gate_value': val})
    return {'trades': taken, 'blocked': blocked, 'pnl': round(cap - 100000, 2)}

results = {}
for (label, expected), pool in zip(summary.items(), pools):
    res = {d: simulate(books_by_day[d], pool) for d in days}
    actual = {'trades': sum(len(r['trades']) for r in res.values()),
              'wins': sum(t['pnl_rs'] > 0 for r in res.values() for t in r['trades']),
              'losses': sum(t['pnl_rs'] < 0 for r in res.values() for t in r['trades']),
              'pnl': round(sum(r['pnl'] for r in res.values()), 2),
              'losing_days': sum(r['pnl'] < 0 for r in res.values())}
    for k, v in actual.items():
        assert abs(v - expected[k]) < .011, (label, k, v, expected[k])
    for day, n, pnl in expected['days']:
        assert len(res[day]['trades']) == n and abs(res[day]['pnl'] - pnl) < .011, (label, day)
    results[label] = res
    print(label, actual, 'EXACT MATCH')

def identity(t):
    return t['src'], t['trigger_t'], t['t_in'], t['t_out'], t['key']

labels = list(results)
attribution = []
for d in days:
    b = {identity(t): t for t in results[labels[1]][d]['trades']}
    c = {identity(t): t for t in results[labels[2]][d]['trades']}
    common, added, removed = b.keys() & c.keys(), c.keys() - b.keys(), b.keys() - c.keys()
    row = {'day': d, 'shared': len(common), 'added': len(added), 'displaced': len(removed),
           'added_pnl': round(sum(c[k]['pnl_rs'] for k in added), 2),
           'displaced_pnl': round(sum(b[k]['pnl_rs'] for k in removed), 2),
           'size_effect': round(sum(c[k]['pnl_rs'] - b[k]['pnl_rs'] for k in common), 2),
           'net': round(results[labels[2]][d]['pnl'] - results[labels[1]][d]['pnl'], 2)}
    assert abs(row['net'] - (row['added_pnl'] - row['displaced_pnl'] + row['size_effect'])) < .011
    attribution.append(row)
print('C minus B attribution:', json.dumps(attribution, indent=1))
(OUT / 'reconciliation.json').write_text(json.dumps({'verified': True, 'results': results, 'C_minus_B': attribution}, indent=1))
print('Nov5 C:', json.dumps(results[labels[2]]['2026-11-05']['trades'], indent=1))

# Diagnostic ablations only: these configurations are selected after seeing the
# report, so their results are in-sample hypotheses, not promotion evidence.
ablations = {}
for name, names in [('9y_alone', ['c20_9y'])] + [('B_without_' + n, [x for x in family if x != n]) for n in family]:
    rr = {d: simulate(books_by_day[d], names) for d in days}
    trades = [t for x in rr.values() for t in x['trades']]
    ablations[name] = {'trades': len(trades), 'wins': sum(t['pnl_rs'] > 0 for t in trades),
                       'losses': sum(t['pnl_rs'] < 0 for t in trades), 'pnl': round(sum(x['pnl'] for x in rr.values()), 2),
                       'losing_days': sum(x['pnl'] < 0 for x in rr.values())}
(OUT / 'ablations.json').write_text(json.dumps(ablations, indent=1))
print('IN-SAMPLE ABLATIONS:', json.dumps(ablations, indent=1))
