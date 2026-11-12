"""Reproduce the 9-Nov saved-book audit without modifying trading state."""
import ast
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'data/paper/2026-11-09.json'
books = json.loads(SOURCE.read_text(encoding='utf-8'))
trades = books['conductor']['trades']
events = [json.loads(x) for x in (ROOT / 'data/paper/conductor_2026-11-09.jsonl').read_text(encoding='utf-8').splitlines()]

def stats(ts):
    return {'n': len(ts), 'wins': sum(t['pnl_rs'] > 0 for t in ts), 'losses': sum(t['pnl_rs'] < 0 for t in ts),
            'pnl': round(sum(t['pnl_rs'] for t in ts), 2)}

ledger = []
features = ['day_move', 'mv300', 'breadth60_dir', 'breadth900_dir', 'agree_same', 'fam_busy', 'fam_free', 'quote_age', 'fut_age', 'depth_age_fut']
for t in trades:
    ledger.append({k: t.get(k) for k in ['src', 'time_in', 'time_out', 'key', 'rr', 'entry', 'exit', 'qty', 'pnl_rs', 'ret_pct', 'reason', 'peak_pts', 'worst_pts', 'fill_delay_s', 'exit_fill_delay_s']} |
                  {'peak_return_pct': round(100 * t['peak_pts'] / t['entry'], 3),
                   'exit_trigger_price_effect': round((t['exit'] - t['exit_trigger_px']) * t['qty'], 2),
                   'weather': {k: t['weather_trig'].get(k) for k in features}})
best = max(trades, key=lambda t: t['pnl_rs'])
cap = 100000.
for t in trades:
    if t is best:
        continue
    qty = int(cap // (t['entry'] * 65)) * 65
    cap = round(cap + round((t['exit'] - t['entry']) * qty, 2), 2)
all_trades = [t for b in books.values() for t in b['trades']]
keys = sorted(set().union(*(t.get('weather_trig', {}).keys() for t in all_trades)))
quality = {k: {'present': sum(k in t.get('weather_trig', {}) for t in all_trades),
               'nonnull': sum(t.get('weather_trig', {}).get(k) is not None for t in all_trades)} for k in keys}
ranked = sorted([{'book': n, **stats(b['trades'])} for n, b in books.items()], key=lambda r: -r['pnl'])
releases = [e for e in events if e['event'] == 'release']
summary = {'session': '2026-11-09', 'review_date': '2026-11-10', 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           'books': len(books), 'stored_trades': len(all_trades), 'champion': stats(trades),
           'positive_pnl': sum(t['pnl_rs'] for t in trades if t['pnl_rs'] > 0),
           'negative_pnl': sum(t['pnl_rs'] for t in trades if t['pnl_rs'] < 0),
           'best_trade': best['time_in'], 'best_trade_pnl': best['pnl_rs'],
           'fixed_size_remove_best_pnl': round(sum(t['pnl_rs'] for t in trades) - best['pnl_rs'], 2),
           'fixed_remaining_decisions_remove_best_recompound_pnl': round(cap - 100000, 2),
           'releases': len(releases), 'releases_after_last_exit': sum(e['t'] > trades[-1]['t_out'] for e in releases),
           'exit_trigger_price_effect': round(sum(x['exit_trigger_price_effect'] for x in ledger), 2),
           'event_counts': dict(collections.Counter(e['event'] for e in events)),
           'gen2_trades_present': any(n.startswith(('n01_', 'n02_', 'n06_')) for n in books)}

# Demonstrate the serializer's mutation case without importing the trading runtime.
tree = ast.parse((ROOT / 'apex/engine/paper.py').read_text(encoding='utf-8'))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_trade_text')
ns = {'json': json, '_TRADE_JSON': {'day': None, 'm': {}}}
exec(compile(ast.Module(body=[fn], type_ignores=[]), '<cache-probe>', 'exec'), ns)
t = {'exit': 10., 't_out': 1., 'weather': {'x': 1}}
ns['_trade_text'](t)
t['exit'], t['weather']['x'] = 11., 2
probe = {'expected': t, 'actual': json.loads(ns['_trade_text'](t))}
result = {'summary': summary, 'champion_ledger': ledger, 'all_books': ranked, 'weather_completeness': quality,
          'release_events': releases, 'cache_mutation_probe': probe}
(OUT / 'analysis.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
lines = ['# Saved-book results: 9 November 2026', '', '| Book | Trades | Wins | Losses | Gross P&L |', '|---|---:|---:|---:|---:|']
for r in ranked:
    lines.append(f"| {r['book']} | {r['n']} | {r['wins']} | {r['losses']} | {r['pnl']:,.2f} |")
(OUT / 'ALL_BOOKS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
