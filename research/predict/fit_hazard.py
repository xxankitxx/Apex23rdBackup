"""11 Nov 2026 (docs/44 M2, docs/46 findings 3 and 4): the hazard artefacts for the engine, chronological.

Data: origins_v3 rebuilt with label version 2 (a recording that ends inside the horizon is unobservable).
For every session d with at least MIN_TRAIN earlier ones: fit on the sessions BEFORE d, take the lines from the
deployed score on the EXECUTABLE rows of those sessions, score d once. One more artefact fitted through the newest
session is the one a later live session loads. Also the premium-range artefact, refitted on the same data.

Writes (with --install):
  apex/predict/artefacts/hazard_<trained through>.json      one per cut-off
  apex/predict/registry.json                                 the engine reads this (registry.for_session)
  apex/predict/ranges_v2.json                                the range record's model, label version 2
  data/research/predict/hazard_eval.json                     unseen-session evidence
Usage: py -3.13 research/predict/fit_hazard.py [--install]"""
import json, os, sys, time
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('APEX_DATA', os.path.join(ROOT, 'data', 'research', 'predict', '_no_engine_data'))
from apex.predict import features as F, targets as T, models as Mo, hazard as Hz
from apex.predict.ledger import Forecaster
import m2_compare as M2
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
ART = os.path.join(ROOT, 'apex', 'predict', 'artefacts')
MIN_TRAIN = 5
H = list(T.HORIZONS)
QS = ('0.5', '0.9', '0.95', '0.99')


def main():
    z = np.load(os.path.join(OUT, 'origins_v3.npz'))
    man = json.load(open(os.path.join(OUT, 'origins_v3.manifest.json')))
    assert man['target_spec'] == T.SPEC, 'origins_v3 was built with another label version: rebuild it first'
    X, M, D = z['X'].astype(float), z['M'], z['D'].astype(int)
    days, names = [str(d) for d in z['days']], [str(n) for n in z['names']]
    mc = {str(n): i for i, n in enumerate(z['mcols'])}
    filled = M[:, mc['st']] == 1
    first = np.c_[[M[:, mc[f'first{h}']] for h in H]].T.astype(int)
    pop = M[:, mc['pop']].astype(int)
    exe = (pop & 2) > 0
    ret300 = M[:, mc['ret300']]
    key = D.astype(np.int64) * 10 ** 7 + (M[:, mc['t']] % 10 ** 6).astype(np.int64)
    _, inv, cnt = np.unique(key[filled], return_inverse=True, return_counts=True)
    w = np.zeros(len(X)); w[filled] = 1.0 / cnt[inv]
    cols = list(range(len(names)))
    reg, ev = [], {}
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    for d in range(MIN_TRAIN, len(days) + 1):
        t0 = time.time()
        tr = filled & (D < d)
        hz = M2.Hazard(cols).fit(X[tr], first[tr], w[tr])
        art = dict(version=3, kind=Hz.KIND, feature_schema=F.SCHEMA, target_spec=T.SPEC, l2=M2.L2, clip=Hz.CLIP,
                   med=hz.med.tolist(), sd=hz.sd.tolist(), W=[Wj.tolist() for Wj in hz.W], names=names,
                   origins='origins_v3', origins_sha256=man['sha256'], score_pipeline='hazard_v1',
                   population='every 5 s: one strike out to four strikes in, plus the reconstructed engine pick',
                   training_days=days[:d], training_cutoff=days[d - 1], trained_through=days[d - 1],
                   effective_from=days[d] if d < len(days) else None)
        fc = Forecaster(artefact=dict(art, hash='tmp'))
        assert fc.ok, fc.why
        o = tr & exe & (first[:, -1] != 3)
        e = fc.edges(X[o])
        art['edge_quantiles'] = {q: float(np.quantile(e, float(q))) for q in QS}
        art['line_population'] = 'executable rows of the training sessions'
        art['mom30_q95'] = float(np.nanquantile(np.abs(X[o][:, names.index('mom30')]), 0.95))
        if d < len(days):
            te = filled & (D == d) & exe
            pT, pA = fc.score(X[te])
            sc = M2.score(pT, pA, first[te], ret300[te], None, art['edge_quantiles']['0.95'])
            base = np.array([(first[tr & exe][:, -1] == c).mean() for c in (1, 2, 0)])
            ob = first[te][:, -1] != 3
            yy = first[te][ob][:, -1]
            ll_base = float(-np.mean(np.log(np.where(yy == 1, base[0], np.where(yy == 2, base[1], base[2])) / base.sum())))
            ev[days[d]] = dict(trained_through=days[d - 1], logloss3_base_rate=ll_base, **sc)
            art['evaluation'] = dict(text=f"scored once on the next session ({days[d]}): side AUC given a move "
                                          f"{sc['auc_direction_given_event']:.2f}, three-way log loss {sc['logloss3']:.3f} "
                                          f"against {ll_base:.3f} for base rates", session=days[d], logloss3=sc['logloss3'],
                                     logloss3_base=ll_base, auc_side=sc['auc_direction_given_event'])
            print(days[d], 'trained through', days[d - 1], '| rows', sc['rows'], '| logloss3', round(sc['logloss3'], 4), 'base', round(ll_base, 4),
                  '| side AUC', round(sc['auc_direction_given_event'] or 0, 3), '| top 5 %:', sc['top'], f'| {time.time() - t0:.0f} s', flush=True)
        else:
            art['published'] = stamp                 # really in place before any later live session
        art['hash'] = Mo.model_hash(art)
        name = f"hazard_{days[d - 1]}.json"
        reg.append(dict(file='artefacts/' + name, hash=art['hash'], kind=Hz.KIND, trained_through=days[d - 1],
                        effective_from=art['effective_from'], training_sessions=d, feature_schema=F.SCHEMA,
                        label_version=T.LABEL_VERSION, lines=art['edge_quantiles'],
                        **({'published': stamp} if d == len(days) else {})))
        if '--install' in sys.argv:
            os.makedirs(ART, exist_ok=True)
            json.dump(art, open(os.path.join(ART, name), 'w'))
    json.dump(dict(days=days, by_day=ev), open(os.path.join(OUT, 'hazard_eval.json'), 'w'), indent=1)
    R = list(ev.values())
    n = sum(r['top']['n'] for r in R)
    print(f"\nunseen sessions {len(R)}: mean log loss {np.mean([r['logloss3'] for r in R]):.4f} against base rates "
          f"{np.mean([r['logloss3_base_rate'] for r in R]):.4f} (better on {sum(r['logloss3'] < r['logloss3_base_rate'] for r in R)}/{len(R)});"
          f" side AUC {np.mean([r['auc_direction_given_event'] for r in R if r['auc_direction_given_event']]):.3f}"
          f" (above 0.5 on {sum((r['auc_direction_given_event'] or 0) > 0.5 for r in R)}/{len(R)});"
          f" top 5 % n {n}, up {sum(r['top']['n'] * (r['top']['up'] or 0) for r in R) / max(n, 1):.3f},"
          f" down {sum(r['top']['n'] * (r['top']['down'] or 0) for r in R) / max(n, 1):.3f},"
          f" mean 300-s return {sum(r['top']['n'] * (r['top']['ret300_pct'] or 0) for r in R) / max(n, 1):+.3f} %")
    # the premium-range model on the same data (label version 2), fitted on every session: a record only
    rng = dict(version=2, kind='premium return range, direct location-scale', feature_schema=F.SCHEMA, target_spec=T.SPEC,
               training_cutoff=days[-1], training_days=days, l2=10.0, clip=4.0, quantiles=[0.1, 0.5, 0.9], horizons={},
               origins='origins_v3')

    def ridge(A, y, ww):
        med = np.nanmedian(A, 0); sd = np.nanstd(A, 0); sd = np.where(sd > 0, sd, 1.0)
        Z = np.c_[np.ones(len(A)), np.clip(np.nan_to_num((A - med) / sd), -4, 4)]
        P = 10.0 * np.eye(Z.shape[1]); P[0, 0] = 0
        wv = np.linalg.solve((Z * ww[:, None]).T @ Z * len(A) / ww.sum() + P, (Z * ww[:, None]).T @ y * len(A) / ww.sum())
        return med, sd, wv, Z @ wv
    for h in (60, 300):
        y = M[:, mc[f'ret{h}']]
        ok = filled & np.isfinite(y)
        med, sd, w_mu, fit = ridge(X[ok], y[ok], w[ok])
        r = y[ok] - fit
        _, _, w_sc, sfit = ridge(X[ok], np.abs(r), w[ok])
        floor = 0.25 * float(np.abs(r).mean())
        s = np.maximum(sfit, floor)
        zq = [float(v) for v in np.quantile(r / s, [0.1, 0.5, 0.9])]
        q = fit[:, None] + s[:, None] * np.array(zq)[None, :]
        rng['horizons'][str(h)] = dict(n=int(ok.sum()), med=med.tolist(), sd=sd.tolist(), w_mu=w_mu.tolist(), w_sc=w_sc.tolist(),
                                       floor=floor, zq=zq, in_sample_coverage=round(float(((y[ok] >= q[:, 0]) & (y[ok] <= q[:, 2])).mean()), 4))
    import hashlib
    rng['hash'] = hashlib.sha256(json.dumps(rng, sort_keys=True).encode()).hexdigest()[:12]
    if '--install' in sys.argv:
        json.dump(dict(note='chronological hazard artefacts (label version 2): an artefact forecasts only sessions after '
                            'its training cut-off; the last one was published before the next live session',
                       min_train=MIN_TRAIN, artefacts=reg), open(os.path.join(ROOT, 'apex', 'predict', 'registry.json'), 'w'), indent=1)
        json.dump(rng, open(os.path.join(ROOT, 'apex', 'predict', 'ranges_v2.json'), 'w'))
        print('installed', len(reg), 'hazard artefacts, registry.json and ranges_v2.json', rng['hash'])


if __name__ == '__main__':
    main()
