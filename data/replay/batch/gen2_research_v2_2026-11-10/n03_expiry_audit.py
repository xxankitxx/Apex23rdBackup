"""10 Nov (docs/38 section 5): contract and quote level audit of the largest N03 picks. Read-only; prints, and writes
data/research/gen2_v2/n03_expiry_audit.json. For every pick above 50 % in any feature set: the date, the time, the
contract, its expiry, the entry ask and exit bid with their quote ages, the spread, the futures move over the holding
time, and the premium path every 20 s. A pick is ordinary only if a tradable quote stood at both ends."""
import importlib.util, json, os, sys
from datetime import datetime
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location('research2', os.path.join(HERE, 'research2.py'))
r2 = importlib.util.module_from_spec(_s); _s.loader.exec_module(r2)

j = json.load(open(os.path.join(r2.OUT, 'research_v2_n03.json')))
days, _man = r2.load_all()
out = []
seen = set()
for fs, r in j['n03'].items():
    for p in r['picks']:
        dte, t, leg, y, ym, K = p
        if y < 0.5:
            continue
        rr = 0 if leg == 'ce' else 1
        d = next(x for x in days if x['date'] == dte and t in x['idx'])
        i = d['idx'][t]; jx = int(np.argmin(np.abs(d['K'] - K)))
        a = r2.at(d, i, r2.DELAY); b = r2.at(d, a, r2.H)
        hh = lambda q: datetime.fromtimestamp(q, r2.IST).strftime('%H:%M:%S')
        path = []
        for s in range(0, r2.H + 1, 20):
            q = r2.at(d, a, s)
            path.append(None if q is None else [s, float(d['bid'][q, jx, rr]), float(d['ask'][q, jx, rr]), float(d['age'][q, jx, rr]), round(float(d['fm'][q]), 1)])
        row = dict(sets=[fs], date=dte, request=hh(t), leg=leg.upper(), strike=K, expiry=d['exp'], part=d['name'],
                   expiry_day=dte in j['expiry_dates'], ret_pct=round(100 * y, 1),
                   entry_ask=float(d['ask'][a, jx, rr]), entry_bid=float(d['bid'][a, jx, rr]), entry_age_s=float(d['age'][a, jx, rr]),
                   exit_bid=float(d['bid'][b, jx, rr]), exit_ask=float(d['ask'][b, jx, rr]), exit_age_s=float(d['age'][b, jx, rr]),
                   fut_entry=round(float(d['fm'][a]), 1), fut_exit=round(float(d['fm'][b]), 1),
                   moneyness_entry_pts=round(float((d['fm'][a] - K) * (1 if rr == 0 else -1)), 1),
                   moneyness_exit_pts=round(float((d['fm'][b] - K) * (1 if rr == 0 else -1)), 1), path=path)
        key = (dte, t, leg, K)
        if key in seen:
            next(o for o in out if (o['date'], o['request'], o['leg'], o['strike']) == (dte, hh(t), leg.upper(), K))['sets'].append(fs)
            continue
        seen.add(key); out.append(row)
out.sort(key=lambda o: -o['ret_pct'])
for o in out:
    print(f"{o['ret_pct']:7.1f} %  {o['date']} {o['request']} {o['leg']} {o['strike']:.0f} exp {o['expiry']} expiry-day {o['expiry_day']} sets {','.join(o['sets'])}")
    print(f"      entry bid/ask {o['entry_bid']}/{o['entry_ask']} (age {o['entry_age_s']:.0f} s)  exit bid/ask {o['exit_bid']}/{o['exit_ask']} (age {o['exit_age_s']:.0f} s)"
          f"  fut {o['fut_entry']} -> {o['fut_exit']}  in-the-money by {o['moneyness_entry_pts']} -> {o['moneyness_exit_pts']} pts")
    print('      path s:bid/ask/age/fut  ' + '  '.join('-' if q is None else f"{q[0]}:{q[1]}/{q[2]}/{q[3]:.0f}/{q[4]}" for q in o['path']))
json.dump(out, open(os.path.join(r2.OUT, 'n03_expiry_audit.json'), 'w'), indent=1)
print('picks above 50 %:', len(out), '| on expiry days:', sum(o['expiry_day'] for o in out))
