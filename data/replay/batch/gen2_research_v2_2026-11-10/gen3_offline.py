"""docs/38 section 7, 10 Nov 2026: the engine's own Gen3 class fed second by second from ds_v2 (read-only).

What this is: a count of signals per day at the frozen manifest, and a futures-level first look (the Nifty future's
mid, entry one second after the signal, the signal's own target / stop / clock in futures points, no thesis exit).
What this is not: a P&L. No option quote is read, so nothing here says a one-leg option trade would have paid. The 15
sessions are discovery material for these signals (the thresholds came from the same sessions, signal side only)."""
import glob, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex import config
from apex.engine import gen3
DS = os.path.join(config.RESEARCH_DIR, 'ds_v2')
OUT = os.path.join(config.RESEARCH_DIR, 'gen2_v2')


def one(path):
    z = np.load(path)
    t, fut, fa, hw, hwa, sf, sfa, w = (z[k] for k in ('t', 'fut', 'fa', 'hw', 'hwa', 'sf', 'sfa', 'w'))
    g = gen3.Gen3()
    mid = np.where((fut[:, 0] > 0) & (fut[:, 1] >= fut[:, 0]) & (fa[:, 0] <= 3.0), 0.5 * (fut[:, 0] + fut[:, 1]), np.nan)
    out, seen = [], set()
    for i in range(len(t)):
        g.update(float(t[i]), float(fut[i, 0]), float(fut[i, 1]), float(fa[i, 0]), hw[i].astype(float), hwa[i],
                 sf[i, :, 0], sf[i, :, 1], sfa[i], w)
        for n, s in g.sig.items():
            if s['t'] == t[i] and (n, s['id']) not in seen:
                seen.add((n, s['id']))
                out.append((n, i, s['dir'], s['tp'], s['sl'], s['hold']))
    rows = []
    for n, i, d, tp, sl, hold in out:
        j0 = i + 1
        while j0 < len(t) and (t[j0] - t[i] < 1.0 or not np.isfinite(mid[j0])):
            j0 += 1
        if j0 >= len(t) or t[j0] - t[i] > 5.0:
            rows.append((n, float(t[i]), d, None, None, 'no entry quote')); continue
        res, why, f60 = None, 'END', None
        for j in range(j0 + 1, len(t)):
            if not np.isfinite(mid[j]):
                continue
            m = (mid[j] - mid[j0]) * d
            if f60 is None and t[j] - t[j0] >= 60.0:
                f60 = m
            if m >= tp: res, why = m, 'TARGET'; break
            if m <= -sl: res, why = m, 'STOP'; break
            if t[j] - t[j0] >= hold: res, why = m, 'HOLD'; break
            res = m
        rows.append((n, float(t[i]), d, None if res is None else round(float(res), 2),
                     None if f60 is None else round(float(f60), 2), why))
    return rows, g.view()


def main():
    days = {}
    for p in sorted(glob.glob(os.path.join(DS, '*.npz'))):
        day = os.path.basename(p)[:10]
        rows, view = one(p)
        days.setdefault(day, []).extend(rows)
        print(os.path.basename(p), len(rows), view['signals'], 'gaps', view['gaps'], flush=True)
    print('\nsignals per day and futures-level first look (points of the Nifty future, mid, entry 1 s later)')
    print(f"{'signal':14s} {'n':>4s} {'days':>4s} {'per day':>7s} {'won':>4s} {'lost':>4s} {'sum pts':>8s} {'mean':>6s} "
          f"{'mean 60s':>8s} {'days +':>6s} {'TP':>3s} {'SL':>3s} {'HOLD':>4s}")
    summ = {}
    for n in gen3.NAMES:
        r = [(d, x) for d, v in days.items() for x in v if x[0] == n and x[3] is not None]
        pts = np.array([x[3] for _, x in r]) if r else np.array([])
        f60 = [x[4] for _, x in r if x[4] is not None]
        dsum = {}
        for d, x in r:
            dsum[d] = dsum.get(d, 0.0) + x[3]
        s = {'n': len(r), 'days_with': len(dsum), 'per_day': round(len(r) / max(1, len(days)), 2),
             'won': int((pts > 0).sum()), 'lost': int((pts <= 0).sum()), 'sum_pts': round(float(pts.sum()), 1),
             'mean_pts': round(float(pts.mean()), 3) if len(pts) else None,
             'mean_60s': round(float(np.mean(f60)), 3) if f60 else None,
             'days_pos': sum(v > 0 for v in dsum.values()),
             'exits': {k: sum(x[5] == k for _, x in r) for k in ('TARGET', 'STOP', 'HOLD', 'END')},
             'per_day_pts': {d: round(v, 1) for d, v in sorted(dsum.items())}}
        summ[n] = s
        print(f"{n:14s} {s['n']:4d} {s['days_with']:4d} {s['per_day']:7.2f} {s['won']:4d} {s['lost']:4d} "
              f"{s['sum_pts']:8.1f} {str(s['mean_pts']):>6s} {str(s['mean_60s']):>8s} {s['days_pos']:6d} "
              f"{s['exits']['TARGET']:3d} {s['exits']['STOP']:3d} {s['exits']['HOLD']:4d}")
    for n in gen3.NAMES:
        print(n, summ[n]['per_day_pts'])
    json.dump({'version': gen3.VERSION, 'manifest': gen3.P, 'note': 'discovery; futures mid; no option quote; no thesis exit',
               'summary': summ, 'rows': {d: v for d, v in days.items()}},
              open(os.path.join(OUT, 'gen3_offline.json'), 'w'), indent=1)
    print('written')


if __name__ == '__main__':
    main()
