"""10 Nov: the same frozen N03 and N05 picks, split by whether the engine could have taken them: on an expiry day the
engine takes no entry after 14:45 (config.ZERO_DTE_NO_ENTRY), on other days none after 15:15 (config.LAST_ENTRY).
A reporting slice of unchanged predictions, made after the results were seen: evidence about WHERE the return sat,
not a new test."""
import json, os, sys
from datetime import datetime, timezone, timedelta
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
from apex import config
IST = timezone(timedelta(hours=5, minutes=30))
OUT = os.path.join(config.RESEARCH_DIR, 'gen2_v2')
res = {}
for which, key in (('n03', 'n03'), ('n05', 'n05')):
    j = json.load(open(os.path.join(OUT, f'research_v2_{which}.json')))
    if key not in j:
        print(which, 'keys', list(j)); continue
    exp = set(j['expiry_dates'])
    for fs, r in j[key].items():
        inw, outw = [], []
        for p in r['picks']:
            hm = datetime.fromtimestamp(p[1], IST); hm = (hm.hour, hm.minute)
            lim = config.ZERO_DTE_NO_ENTRY if p[0] in exp else config.LAST_ENTRY
            (inw if hm < tuple(lim) else outw).append(p[3])
        f = lambda a: dict(n=len(a), wins=int(sum(v > 0 for v in a)), sum_pct=round(100 * float(np.sum(a)), 1) if a else 0.0,
                           mean_pct=round(100 * float(np.mean(a)), 3) if a else None, best_pct=round(100 * max(a), 1) if a else None)
        res[f'{which}.{fs}'] = dict(tradable=f(inw), outside=f(outw))
        a, b = res[f'{which}.{fs}']['tradable'], res[f'{which}.{fs}']['outside']
        print(f"{which} {fs:10s} engine could trade: {a['n']:4d} picks, {a['wins']:3d} wins, sum {a['sum_pct']:8.1f} %, mean {a['mean_pct']} %, best {a['best_pct']} % | "
              f"outside: {b['n']:3d} picks, sum {b['sum_pct']:8.1f} %, best {b['best_pct']} %")
json.dump(res, open(os.path.join(OUT, 'picks_by_engine_window.json'), 'w'), indent=1)
