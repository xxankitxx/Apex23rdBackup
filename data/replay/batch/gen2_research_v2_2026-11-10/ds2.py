"""Tape -> 1-second research dataset, version 2 (10 Nov 2026; docs/38 section 5 items 6, 8 and 10).

What changed against gen2_research_2026-11-09/ds.py (kept as it was, with its results):
  * a row stamped second B holds ONLY packets received before B (v1 applied the packet that crossed the second and
    then stamped the row int(t): a "10:00:00" row could hold information received at 10:00:00.8);
  * every input carries its own age at the cutoff (future quote, depth, each option, each stock, each stock future);
  * the next weekly expiry and the stock futures are kept too (S01 / S02 capability);
  * IST is explicit (no host-local time), time order is asserted, the end marker of the tape is recorded;
  * the output goes to a durable, configured folder (config.RESEARCH_DIR/ds_v2) with a manifest of hashes.
Read-only on the tape. Usage: py -3.13 ds2.py <part name, e.g. 2026-10-19.p2> [more parts ...]"""
import gzip, hashlib, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex import config
OUT = os.path.join(config.RESEARCH_DIR, 'ds_v2')
IST_S = 19800
MAXK, MAXK2 = 80, 40
NEVER = np.float32(1e9)


def fl(v):
    try:
        return float(v)
    except Exception:
        return np.nan


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def build(part):
    src = os.path.join(config.TICKS_DIR, part + '.jsonl.gz')
    fut_tok = dep_tok = None
    eq, sf, W, G, SYM = {}, {}, [], [], []
    opt, opt2 = {}, {}
    strikes, strikes2 = [], []
    exp = exp2 = None
    fut = np.full(6, np.nan); fut_rt = 0.0; dep_rt = 0.0
    cur = np.full((MAXK, 2, 2), np.nan, np.float32); rcv = np.zeros((MAXK, 2))
    cur2 = np.full((MAXK2, 2, 2), np.nan, np.float32); rcv2 = np.zeros((MAXK2, 2))
    hw = hw_rt = sfp = sf_rt = None
    R = dict(t=[], cut=[], fut=[], fa=[], opt=[], age=[], opt2=[], age2=[], hw=[], hwa=[], sf=[], sfa=[])
    lastB = None; last_t = 0.0; disorder = 0; ended = False; torn = False; npk = 0

    def age(B, rt):
        return np.where(rt > 0, B - rt, NEVER).astype(np.float32)

    with gzip.open(src, 'rt', encoding='utf-8') as f:
        try:
            for l in f:
                if l.startswith('{"k":"meta"'):
                    ended = ended or '"end":1' in l.replace(' ', '')
                    continue
                if l.startswith('{"k":"reg"'):
                    reg = json.loads(l)['d']
                    for r in reg:
                        if r['key'] == 'NIFTY|FUT':
                            fut_tok, dep_tok = r['token'], r.get('depth_token')
                        if r['kind'] in ('eq', 'stock') and (r.get('wn') or 0) > 0 and r['key'].endswith('|EQ') and r['token'] not in eq:
                            eq[r['token']] = len(W); W.append(float(r['wn'])); G.append(r.get('group') or 'other'); SYM.append(r['sym'])
                    for r in reg:
                        if r['kind'] == 'sfut' and r['sym'] in SYM:
                            sf[r['token']] = SYM.index(r['sym'])
                    exps = sorted({r['expiry'] for r in reg if r['kind'] == 'opt' and r['sym'] == 'NIFTY'})
                    if exp is None and exps:
                        exp = exps[0]; exp2 = exps[1] if len(exps) > 1 else None
                    for r in reg:
                        if r['kind'] != 'opt' or r['sym'] != 'NIFTY':
                            continue
                        rr = 0 if (r.get('rr') or r['right'][:1].upper()) in ('CE', 'C') else 1
                        k = int(r['strike'])
                        if r['expiry'] == exp and r['token'] not in opt:
                            if k not in strikes:
                                if len(strikes) >= MAXK:
                                    continue
                                strikes.append(k)
                            opt[r['token']] = (strikes.index(k), rr)
                        elif r['expiry'] == exp2 and r['token'] not in opt2:
                            if k not in strikes2:
                                if len(strikes2) >= MAXK2:
                                    continue
                                strikes2.append(k)
                            opt2[r['token']] = (strikes2.index(k), rr)
                    if hw is None:
                        n = len(W)
                        hw = np.full(n, np.nan); hw_rt = np.zeros(n); sfp = np.full((n, 3), np.nan); sf_rt = np.zeros(n)
                    elif len(W) > len(hw):                      # a later registry added stocks: grow, keep the columns
                        k = len(W) - len(hw)
                        hw = np.r_[hw, np.full(k, np.nan)]; hw_rt = np.r_[hw_rt, np.zeros(k)]
                        sfp = np.r_[sfp, np.full((k, 3), np.nan)]; sf_rt = np.r_[sf_rt, np.zeros(k)]
                    continue
                if not l.startswith('{"k":"p"'):
                    continue
                q = l.find('"d":["') + 6; tok = l[q:l.find('"', q)]
                o = opt.get(tok); o2 = opt2.get(tok) if o is None else None
                if o is None and o2 is None and tok != fut_tok and tok != dep_tok and tok not in eq and tok not in sf:
                    continue
                e = json.loads(l); t = e['t'] / 1e9; d = e['d']
                if t < last_t:
                    disorder += 1
                last_t = max(last_t, t)
                # the boundary row is written BEFORE this packet is applied: it holds only what was received before B
                B = int(last_t)
                hm = ((B + IST_S) % 86400) // 60
                if B != lastB and 555 <= hm < 930 and fut_rt > 0:
                    lastB = B
                    R['t'].append(B); R['cut'].append(B - max(fut_rt, dep_rt, rcv.max(), hw_rt.max()))
                    R['fut'].append(fut.copy()); R['fa'].append([B - fut_rt, B - dep_rt if dep_rt else 1e9])
                    R['opt'].append(cur.copy()); R['age'].append(age(B, rcv))
                    R['opt2'].append(cur2.copy()); R['age2'].append(age(B, rcv2))
                    R['hw'].append(hw.copy()); R['hwa'].append(age(B, hw_rt))
                    R['sf'].append(sfp.copy()); R['sfa'].append(age(B, sf_rt))
                npk += 1
                if o is not None:
                    if len(d) == 23:
                        cur[o[0], o[1], 0] = fl(d[6]); cur[o[0], o[1], 1] = fl(d[8]); rcv[o[0], o[1]] = t
                elif o2 is not None:
                    if len(d) == 23:
                        cur2[o2[0], o2[1], 0] = fl(d[6]); cur2[o2[0], o2[1], 1] = fl(d[8]); rcv2[o2[0], o2[1]] = t
                elif tok == fut_tok:
                    if len(d) == 23:
                        fut[0], fut[1], fut[2], fut[3] = fl(d[6]), fl(d[8]), fl(d[2]), fl(d[14]); fut_rt = t
                elif tok == dep_tok:
                    try:
                        lv = d[2]; fut[4] = sum(fl(b[1]) for b in lv[:5]); fut[5] = sum(fl(b[5]) for b in lv[:5]); dep_rt = t
                    except Exception:
                        pass
                elif tok in eq:
                    if len(d) == 21:
                        hw[eq[tok]] = fl(d[2]); hw_rt[eq[tok]] = t
                elif len(d) == 23:
                    i = sf[tok]; sfp[i] = (fl(d[6]), fl(d[8]), fl(d[2])); sf_rt[i] = t
        except EOFError:
            torn = True
    t = np.array(R['t'], float)
    assert len(t) == 0 or (np.diff(t) > 0).all(), 'rows are not strictly increasing in time'
    n = len(W)

    def pad(rows, shape):                                       # rows written before a registry grew are narrower
        out = np.full((len(rows),) + shape, np.nan, np.float32)
        for i, r in enumerate(rows):
            out[i, :len(r)] = r
        return out
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, part + '.npz')
    np.savez_compressed(dst, t=t, cut=np.array(R['cut'], np.float32), fut=np.array(R['fut']), fa=np.array(R['fa'], np.float32),
                        opt=np.array(R['opt'], np.float32), age=np.array(R['age'], np.float32),
                        opt2=np.array(R['opt2'], np.float32), age2=np.array(R['age2'], np.float32),
                        hw=pad(R['hw'], (n,)), hwa=pad(R['hwa'], (n,)), sf=pad(R['sf'], (n, 3)), sfa=pad(R['sfa'], (n,)),
                        strikes=np.array(strikes), strikes2=np.array(strikes2), w=np.array(W), g=np.array(G), sym=np.array(SYM),
                        expiry=np.array(exp or ''), expiry2=np.array(exp2 or ''))
    man = dict(part=part, version=2, rows=len(t), first=float(t[0]) if len(t) else None, last=float(t[-1]) if len(t) else None,
               packets=npk, disorder=disorder, tape_end_marker=ended, tape_torn=torn, expiry=exp, expiry2=exp2,
               strikes=len(strikes), strikes2=len(strikes2), stocks=len(W), stock_futures=len(sf),
               tape_sha256=sha(src), tape_bytes=os.path.getsize(src), npz_sha256=sha(dst))
    json.dump(man, open(os.path.join(OUT, part + '.manifest.json'), 'w'), indent=1)
    print(json.dumps({k: man[k] for k in ('part', 'rows', 'packets', 'disorder', 'tape_end_marker', 'tape_torn', 'expiry', 'expiry2',
                                          'strikes', 'strikes2', 'stocks', 'stock_futures')}), flush=True)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        build(p)
