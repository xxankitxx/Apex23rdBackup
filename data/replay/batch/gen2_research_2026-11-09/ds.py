"""Tape -> 1-second research dataset (read-only on the repo; writes scratchpad npz). Nearest weekly expiry only."""
import gzip, json, sys, time
import numpy as np
day = sys.argv[1]
OUT = 'C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/ds/'
def lines():
    with gzip.open(f'D:/ApexOptions/data/ticks/{day}.jsonl.gz', 'rt', encoding='utf-8') as f:
        try:
            for l in f: yield l
        except EOFError: pass
def fl(v):
    try: return float(v)
    except Exception: return np.nan
fut_tok = dep_tok = None; eq = {}; W = []; G = []
opt = {}          # token -> (col, rr)
strikes = []; exp = None
st = dict(bid=np.nan, ask=np.nan, ltp=np.nan, ttq=np.nan, bq=np.nan, aq=np.nan)
MAXK = 80
cur = np.full((MAXK, 2, 3), np.nan, np.float32)      # strike, rr, (bid, ask, recv age base)
rcv = np.zeros((MAXK, 2))
hw = None; last = None
R = dict(t=[], fut=[], opt=[], age=[], hw=[])
for l in lines():
    if l.startswith('{"k":"reg"'):
        reg = json.loads(l)['d']
        for r in reg:
            if r['key'] == 'NIFTY|FUT': fut_tok, dep_tok = r['token'], r.get('depth_token')
            if r['kind'] in ('eq', 'stock') and (r.get('wn') or 0) > 0 and r['key'].endswith('|EQ') and r['token'] not in eq:
                eq[r['token']] = len(W); W.append(float(r['wn'])); G.append(r.get('group') or 'other')
        exps = sorted({r['expiry'] for r in reg if r['kind'] == 'opt' and r['sym'] == 'NIFTY'})
        if exp is None and exps: exp = exps[0]
        for r in reg:
            if r['kind'] == 'opt' and r['sym'] == 'NIFTY' and r['expiry'] == exp and r['token'] not in opt:
                k = int(r['strike'])
                if k not in strikes:
                    if len(strikes) >= MAXK: continue
                    strikes.append(k)
                opt[r['token']] = (strikes.index(k), 0 if (r.get('rr') or r['right'][:1].upper()) in ('CE', 'C') else 1)
        if hw is None: hw = np.full(len(W), np.nan)
        continue
    if not l.startswith('{"k":"p"'): continue
    q = l.find('"d":["') + 6; tok = l[q:l.find('"', q)]
    o = opt.get(tok)
    if o is None and tok != fut_tok and tok != dep_tok and tok not in eq: continue
    e = json.loads(l); t = e['t'] / 1e9; d = e['d']
    if o is not None:
        if len(d) == 23:
            cur[o[0], o[1], 0] = fl(d[6]); cur[o[0], o[1], 1] = fl(d[8]); cur[o[0], o[1], 2] = fl(d[2]); rcv[o[0], o[1]] = t
    elif tok == fut_tok and len(d) == 23:
        st.update(bid=fl(d[6]), ask=fl(d[8]), ltp=fl(d[2]), ttq=fl(d[14]))
    elif tok == dep_tok:
        try:
            lv = d[2]; st['bq'] = sum(fl(b[1]) for b in lv[:5]); st['aq'] = sum(fl(b[5]) for b in lv[:5])
        except Exception: pass
    elif len(d) == 21:
        hw[eq[tok]] = fl(d[2])
    sec = int(t); lt = time.localtime(t); hm = lt.tm_hour * 60 + lt.tm_min
    if sec != last and 555 <= hm < 930:
        last = sec
        R['t'].append(sec); R['fut'].append([st[k] for k in ('bid', 'ask', 'ltp', 'ttq', 'bq', 'aq')])
        R['opt'].append(cur.copy()); R['age'].append((t - rcv).astype(np.float32)); R['hw'].append(hw.copy())
import os
os.makedirs(OUT, exist_ok=True)
np.savez_compressed(OUT + day + '.npz', t=np.array(R['t']), fut=np.array(R['fut']), opt=np.array(R['opt'], np.float32),
                    age=np.array(R['age'], np.float32), hw=np.array(R['hw'], np.float32), strikes=np.array(strikes), w=np.array(W),
                    g=np.array(G), expiry=np.array(exp or ''))
print(day, 'seconds', len(R['t']), 'strikes', len(strikes), 'expiry', exp)
