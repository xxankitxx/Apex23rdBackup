"""Read-only audit of p41 saved trades and forecast-to-contract linkage."""
import collections
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/research/codex_forecast_audit_2026-11-11'
OUT.mkdir(parents=True, exist_ok=True)
names = ['c20_9y','fr_c20_9y','fx_c20_9y','p02_clock','p02_top1','p02_ctl_mom','p05_adaptive','conductor']
summary = {n: collections.Counter() for n in names}
daily, mismatches, forecast_coverage = [], [], []
seen_days = set()
for f in sorted((ROOT / 'data/replay/batch').glob('p41_g*/paper/2026-*.json')):
    day = f.stem
    assert day not in seen_days, day
    seen_days.add(day)
    books = json.loads(f.read_text(encoding='utf-8'))
    signals = {}
    fp = f.parent / ('forecasts_' + day + '.jsonl')
    if fp.exists():
        for line in fp.open(encoding='utf-8'):
            r = json.loads(line)
            sid = r.get('extra',{}).get('signal_id')
            if sid is not None:
                signals[(r['role'], sid)] = r
    for name in names:
        ts = books.get(name,{}).get('trades',[])
        s = summary[name]
        s['trades'] += len(ts)
        s['wins'] += sum(t['pnl_rs'] > 0 for t in ts)
        s['losses'] += sum(t['pnl_rs'] < 0 for t in ts)
        s['zero'] += sum(t['pnl_rs'] == 0 for t in ts)
        pnl = sum(t['pnl_rs'] for t in ts)
        rsum = sum((t['exit']/t['entry']-1)*100 for t in ts)
        s['pnl_rs'] += pnl
        s['profit_days'] += pnl > 0
        s['loss_days'] += pnl < 0
        s['fc_present'] += sum(t.get('fc',{}).get('edge') is not None for t in ts)
        s['forecast_exits'] += sum('FORECAST' in t.get('reason','') for t in ts)
        s['defer_count'] += sum(t.get('fc_defer',0) for t in ts)
        daily.append(dict(day=day,book=name,n=len(ts),pnl_rs=round(pnl,2),sum_return_pct=round(rsum,4),
                          sign_disagrees=(pnl>0)!=(rsum>0) if ts else False))
        for t in ts:
            if name.startswith(('p02','p05')):
                sid = -int(t.get('episode',0)) - 5*10**10
                r = signals.get((name,sid))
                s['linked_signals'] += r is not None
                if r:
                    predicted = r['instrument'].split('|')
                    same = float(predicted[0]) == float(t['strike']) and predicted[1] == t['rr']
                    s['different_contract'] += not same
                    if not same and len(mismatches)<12:
                        mismatches.append(dict(day=day,book=name,time=t['time_in'],predicted=r['instrument'],actual=t['key'],pnl=t['pnl_rs']))
    parent = books.get('c20_9y',{}).get('trades',[])
    runner = books.get('fr_c20_9y',{}).get('trades',[])
    identity = lambda t:(t['key'],t['t_in'],t['t_out'],t['entry'],t['exit'])
    assert [identity(t) for t in parent] == [identity(t) for t in runner], day

result = dict(days=len(seen_days),summary={n:dict(v) for n,v in summary.items()},daily=daily,
              mismatched_contract_examples=mismatches,
              accounting_sign_disagreements=[r for r in daily if r['sign_disagrees']])
(OUT/'replay_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='daily'},indent=2))
