"""11 Nov 2026 (docs/44 M1, and the review of docs/45, point 2): does the reconstructed selector name the contract the
engine really chose?

Truth: the 15-day replay p41 (10 Nov code). Its 17 signal books chose their contract with paper.choose_contract
(the default rule) AT THE TRIGGER; the pending order then carried that contract's key to the fill, so request and
fill are the same contract by construction in that code (checked here: the trade's key is the key at the trigger).
What is compared, stage by stage:
  trigger second   the reconstructed pick at int(trigger_t), from the recorded quotes of that second
  one second off   the pick at int(trigger_t) - 1 and + 1: a difference that disappears here is timing, not a defect
  delta            the reconstructed delta of the TRADED contract against the engine's own delta at the fill
                   (trade field delta_in; the fill is fill_delay_s after the trigger, so a small drift is expected)
Reported by days to expiry and by whether the engine itself flagged the out-of-band fallback.

Output: data/research/predict/selector_agreement.json. Usage: py -3.13 research/predict/selector_agreement.py"""
import glob, json, os, sys
from datetime import datetime
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('APEX_DATA', os.path.join(ROOT, 'data', 'research', 'predict', '_no_engine_data'))
from apex import config
import build_candidates as B
OUT = os.path.join(ROOT, 'data', 'research', 'predict')


def main():
    parts = {}
    for p in sorted(glob.glob(os.path.join(B.DS, '*.npz'))):
        parts.setdefault(os.path.basename(p)[:10], []).append(p)
    rows, skipped = [], {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'replay', 'batch', 'p41_g*', 'paper', '2026-*.json'))):
        day = os.path.basename(f)[:10]
        books = json.load(open(f, encoding='utf-8'))
        loaded = []
        for p in parts.get(day, []):
            z = np.load(p)
            n = len(z['strikes']); order = np.argsort(z['strikes'])
            o = z['opt'][:, :n].astype(float)[:, order]
            loaded.append(dict(t=z['t'].astype(float), K=z['strikes'][order].astype(float), bid=o[..., 0], ask=o[..., 1],
                               age=z['age'][:, :n].astype(float)[:, order], fut=z['fut'].astype(float), exp=str(z['expiry'])))
        for name, b in books.items():
            if not isinstance(b, dict) or not (b.get('p') or {}).get('gen'):
                continue
            for tr in b.get('trades', []):
                tt = tr.get('trigger_t')
                if tt is None:
                    skipped['no trigger time'] = skipped.get('no trigger time', 0) + 1
                    continue
                rr = 0 if tr['rr'] == 'CE' else 1
                got = {}
                for off in (0, -1, 1):
                    for L in loaded:
                        if L['exp'] != tr['expiry']:
                            continue
                        i = int(np.searchsorted(L['t'], int(tt) + off))
                        if i >= len(L['t']) or L['t'][i] != int(tt) + off:
                            continue
                        now = datetime.fromtimestamp(L['t'][i], config.IST)
                        delta, mid = B.chain_delta(L['K'], L['bid'][i], L['ask'][i], L['age'][i], L['fut'][i, 0], L['fut'][i, 1], L['exp'], now)
                        kx, fb = B.pick(delta[:, rr], mid[:, rr], L['age'][i, :, rr], B.band_for(day, L['exp'], now))
                        j = np.where(L['K'] == float(tr['strike']))[0]
                        got[off] = dict(pick=None if kx is None else float(L['K'][kx]), fallback=fb,
                                        delta_traded=float(delta[j[0], rr]) if len(j) else None)
                        break
                if 0 not in got:
                    skipped['trigger second not in the recorded set'] = skipped.get('trigger second not in the recorded set', 0) + 1
                    continue
                g = got[0]
                rows.append(dict(day=day, book=name, strike=float(tr['strike']), rr=tr['rr'], dte=tr.get('dte_in'),
                                 engine_fallback=bool(tr.get('band_fallback')), pick=g['pick'], same=g['pick'] == float(tr['strike']),
                                 same_within_1s=any(v['pick'] == float(tr['strike']) for v in got.values()),
                                 steps_off=None if g['pick'] is None else abs(g['pick'] - float(tr['strike'])) / config.STRIKE_STEP,
                                 delta_engine=tr.get('delta_in'), delta_recon=g['delta_traded'], fill_delay=tr.get('fill_delay_s')))
    n = len(rows)

    def agg(sel):
        s = [r for r in rows if sel(r)]
        if not s:
            return None
        dd = np.array([abs(abs(r['delta_engine']) - abs(r['delta_recon'])) for r in s
                       if r['delta_engine'] is not None and r['delta_recon'] is not None and np.isfinite(r['delta_recon'])])
        off = [r['steps_off'] for r in s if not r['same'] and r['steps_off'] is not None]
        return dict(trades=len(s), same_at_trigger=sum(r['same'] for r in s), share=round(sum(r['same'] for r in s) / len(s), 4),
                    same_within_1s=sum(r['same_within_1s'] for r in s), no_pick=sum(r['pick'] is None for r in s),
                    off_by_one_strike=sum(1 for x in off if x == 1), off_by_more=sum(1 for x in off if x > 1),
                    delta_abs_diff_median=float(np.median(dd)) if len(dd) else None,
                    delta_abs_diff_p95=float(np.quantile(dd, 0.95)) if len(dd) else None)
    out = dict(source='p41_g1..g8, the 17 signal books (default contract rule)', linked=n, skipped=skipped, all=agg(lambda r: True),
               by_dte={str(k): agg(lambda r, k=k: r['dte'] == k) for k in sorted({r['dte'] for r in rows if r['dte'] is not None})},
               engine_in_band=agg(lambda r: not r['engine_fallback']), engine_fallback=agg(lambda r: r['engine_fallback']),
               by_day={d: agg(lambda r, d=d: r['day'] == d) for d in sorted({r['day'] for r in rows})})
    json.dump(out, open(os.path.join(OUT, 'selector_agreement.json'), 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('linked', 'skipped', 'all', 'by_dte', 'engine_in_band', 'engine_fallback')}, indent=1))
    print('by day:', {d: (v['same_at_trigger'], v['trades']) for d, v in out['by_day'].items()})


if __name__ == '__main__':
    main()
