"""Tape-reading pilot (NOT an engine replay): drive gen2.Gen2 from one day's recorded futures quote, depth and
heavyweight prices, 1 Hz, and score each signal on the FUTURES with its own bracket (points). No options, no fills."""
import gzip, json, sys, time, math, collections
sys.path.insert(0, 'D:/ApexOptions')
from apex.engine import gen2
day = sys.argv[1]
T0 = time.time()
g = gen2.Gen2()
fut_tok = dep_tok = None; eq = {}; W = []; G = []
st = {"bid": None, "ask": None, "ltp": None, "ttq": None, "bq": None, "aq": None}
hw = []; last_sec = None; sigs = []; mids = []   # (t, mid)
seen = set()
def lines():
    with gzip.open(f'D:/ApexOptions/data/ticks/{day}.jsonl.gz', 'rt', encoding='utf-8') as f:
        try:
            for l in f: yield l
        except EOFError: pass
def f(v):
    try: return float(v)
    except Exception: return float('nan')
for l in lines():
    if l.startswith('{"k":"reg"'):
        if fut_tok: continue
        for r in json.loads(l)['d']:
            if r['key'] == 'NIFTY|FUT': fut_tok, dep_tok = r['token'], r.get('depth_token')
            if r['kind'] in ('eq', 'stock') and (r.get('wn') or 0) > 0 and r['seg'] == 'eq' and r['key'].endswith('|EQ'):
                eq[r['token']] = len(W); W.append(float(r['wn'])); G.append(r.get('group') or 'other')
        hw = [float('nan')] * len(W)
        continue
    if not l.startswith('{"k":"p"'): continue
    q = l.find('"d":["') + 6; tok = l[q:l.find('"', q)]
    if tok != fut_tok and tok != dep_tok and tok not in eq: continue
    e = json.loads(l); t = e['t'] / 1e9; d = e['d']
    if tok == fut_tok and len(d) == 23:
        st.update(bid=f(d[6]), ask=f(d[8]), ltp=f(d[2]), ttq=f(d[14]))
    elif tok == dep_tok:
        lv = d[2]
        try:
            st["bq"] = sum(f(b[1]) for b in lv[:5]); st["aq"] = sum(f(b[5]) for b in lv[:5])
        except Exception: pass
    elif len(d) == 21:
        hw[eq[tok]] = f(d[2])
    sec = int(t)
    lt = time.localtime(t); hm = lt.tm_hour * 60 + lt.tm_min
    if sec != last_sec and 555 <= hm < 930 and st["bid"] and st["bq"]:
        last_sec = sec
        g.update(float(sec), st["bid"], st["ask"], st["ltp"], st["ttq"], st["bq"], st["aq"], list(hw), W, G)
        mids.append((sec, 0.5 * (st["bid"] + st["ask"])))
        for n, s in g.sig.items():
            if s["t"] == sec and (n, s["id"]) not in seen:
                seen.add((n, s["id"])); sigs.append((len(mids) - 1, dict(s)))
print(day, 'seconds', len(mids), 'stocks', len(W), 'groups', dict(collections.Counter(G)), 'gaps', g.gaps, 'beta', g.beta, 'a', g.a, 'read s', round(time.time() - T0))
res = collections.defaultdict(list)
for i, s in sigs:
    t0, m0 = mids[i]; out = None
    for t, m in mids[i + 1:]:
        mv = (m - m0) * s["dir"]
        if mv >= s["tp"]: out = ('TP', mv); break
        if mv <= -s["sl"]: out = ('SL', mv); break
        if s.get("stop_px") is not None and (m - s["stop_px"]) * s["dir"] <= 0: out = ('THESIS', mv); break
        if t - t0 >= s["hold"]: out = ('TIME', mv); break
    if out is None: out = ('EOD', (mids[-1][1] - m0) * s["dir"])
    res[s["name"]].append((time.strftime('%H:%M:%S', time.localtime(t0)), s["dir"], out[0], round(out[1], 1), s["tp"], s["sl"]))
for n in gen2.NAMES:
    r = res.get(n, [])
    pts = [x[3] for x in r]
    print(f"{n:12s} signals {len(r):3d} wins {sum(p > 0 for p in pts):3d} sum pts {sum(pts):+8.1f} | exits {dict(collections.Counter(x[2] for x in r))}")
    if n in ('n01_rev', 'n01_rel', 'n02_relax', 'n06_lead'):
        for x in r[:40]: print('     ', x)
json.dump({n: res.get(n, []) for n in gen2.NAMES}, open(f'C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/pilot_{day}.json', 'w'))
