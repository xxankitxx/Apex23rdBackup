"""11 Nov 2026 (docs/44 M2, docs/45): three forecasters compared chronologically on origins_v3.

Roster, fixed here before any result (docs/44 section 8):
  activity   one softmax hazard model per interval on ACTIVITY-ONLY features: premium, spread, days to expiry,
             expiry flag, time of day, realised volatility, straddle change. No signed feature: it cannot know a side.
  logistic   the deployed kind: eight separate binary models on all 33 features, then the horizon projection
             (ledger.project). This is model_v2's method, refitted chronologically.
  hazard     ONE coherent discrete-time competing-risk model: per interval, given no event yet, a three-way softmax
             (up, down, survive) on all 33 features. Cumulative incidence by the formulas of docs/44 section 4A.

Protocol, all inside the allowed past for each test session d (MIN_TRAIN earlier sessions at least):
  standardisation (median, spread), the fit and every line come from sessions before d only. Nothing is selected on
  a result: one l2 for all, no feature selection, no threshold search. Rows are weighted so that all the contracts
  of one moment together weigh one (twelve strikes of one second are not twelve events).
Scored on session d, on two populations: executable (the reconstructed engine pick) and broad.
  proper scores   three-class log loss and Brier at 300 s (up first, down first, neither)
  activity        AUC of P(any event by 300 s)
  direction       AUC of P(up) / (P(up) + P(down)) among origins where an event happened
  time            mean absolute error of the expected event interval, on ALL origins (censored and no-event included
                  as "no event"), as an interval-level log loss
  policy          origins whose edge P(up) - P(down) is in the top 5 % of the TRAINING sessions' edges: how many,
                  up-first share, down-first share, mean 300-s premium return (ask in, bid out)
Uncertainty: every number is given per session; the summary counts sessions won against the activity baseline and
gives a paired day-block bootstrap interval of the mean difference.

Output: data/research/predict/m2_compare.json and a table. Usage: py -3.13 research/predict/m2_compare.py"""
import json, os, sys, time
import numpy as np
from scipy.optimize import minimize
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT)
os.environ.setdefault('APEX_DATA', os.path.join(ROOT, 'data', 'research', 'predict', '_no_engine_data'))
from apex.predict import features as F, targets as T, models as Mo
from apex.predict.ledger import project
OUT = os.path.join(ROOT, 'data', 'research', 'predict')
MIN_TRAIN, L2, CLIP = 5, 10.0, 4.0
H = list(T.HORIZONS)
ACT = ['prem', 'spread_pct', 'dte', 'expd', 'tod', 'rv60', 'rv300', 'fspread', 'strad60', 'strad300', 'prem_strad']


def stdz(X):
    med = np.nanmedian(X, axis=0)
    sd = 1.4826 * np.nanmedian(np.abs(X - med), axis=0)
    sd = np.where(np.isfinite(sd) & (sd > 1e-9), sd, np.where(np.nanstd(X, axis=0) > 1e-9, np.nanstd(X, axis=0), 1.0))
    return np.where(np.isfinite(med), med, 0.0), sd


def zed(X, med, sd):
    return np.clip(np.nan_to_num((X - med) / sd, nan=0.0, posinf=CLIP, neginf=-CLIP), -CLIP, CLIP)


def fit_softmax(A, y, w, k):
    """Weighted L2 softmax, classes 0..k-1, class 0 is the reference (weights zero). A has the intercept column."""
    n, p = A.shape
    Y = np.eye(k)[y]
    pri = np.array([max((w * (y == c)).sum(), 1e-9) for c in range(k)])
    w0 = np.zeros((k - 1, p))
    w0[:, 0] = np.log(pri[1:] / pri[0])
    pen = L2 * np.r_[0.0, np.ones(p - 1)]

    def f(v):
        Wm = v.reshape(k - 1, p)
        U = np.c_[np.zeros(n), A @ Wm.T]
        U -= U.max(1, keepdims=True)
        E = np.exp(U)
        Pm = E / E.sum(1, keepdims=True)
        loss = -(w * np.log(np.maximum(Pm[np.arange(n), y], 1e-300))).sum() + 0.5 * (pen * Wm * Wm).sum()
        G = ((Pm - Y)[:, 1:] * w[:, None]).T @ A + pen * Wm
        return loss, G.ravel()
    r = minimize(f, w0.ravel(), jac=True, method='L-BFGS-B', options=dict(maxiter=300))
    return r.x.reshape(k - 1, p)


def soft(A, Wm):
    U = np.c_[np.zeros(len(A)), A @ Wm.T]
    U -= U.max(1, keepdims=True)
    E = np.exp(U)
    return E / E.sum(1, keepdims=True)


def intervals(first):
    """first: (rows, 4) codes at 30/60/180/300 s (0 none, 1 up, 2 down, 3 unobservable). Returns ev (rows,) the
    interval index of the first event or -1, kind (1 up, 2 down, 0), last (rows,) the last interval observed
    (-1: none), so interval j is 'at risk and observed' when j <= last and (ev < 0 or j <= ev)."""
    n = len(first)
    ev, kind, last = np.full(n, -1), np.zeros(n, int), np.full(n, -1)
    done = np.zeros(n, bool)
    for j in range(first.shape[1]):
        c = first[:, j]
        obs = ~done & (c != 3)
        hit = obs & ((c == 1) | (c == 2))
        ev[hit], kind[hit] = j, c[hit]
        last[obs] = j
        done |= hit | (c == 3)
    return ev, kind, last


class Hazard:
    def __init__(self, cols):
        self.cols = cols

    def fit(self, X, first, w):
        self.med, self.sd = stdz(X[:, self.cols])
        A = np.c_[np.ones(len(X)), zed(X[:, self.cols], self.med, self.sd)]
        ev, kind, last = intervals(first)
        self.W = []
        for j in range(len(H)):
            risk = (last >= j) & ((ev < 0) | (ev >= j))
            y = np.where(ev[risk] == j, kind[risk], 0)          # 0 survive, 1 up, 2 down
            self.W.append(fit_softmax(A[risk], y, w[risk], 3))
        return self

    def predict(self, X):
        """(pUp, pDown) cumulative, each (rows, horizons), and the per-interval hazards (rows, horizons, 3)."""
        A = np.c_[np.ones(len(X)), zed(X[:, self.cols], self.med, self.sd)]
        S = np.ones(len(X))
        up, dn = np.zeros((len(X), len(H))), np.zeros((len(X), len(H)))
        hz = np.zeros((len(X), len(H), 3))
        cu, cd = np.zeros(len(X)), np.zeros(len(X))
        for j in range(len(H)):
            Pm = soft(A, self.W[j])
            hz[:, j] = Pm
            cu, cd = cu + S * Pm[:, 1], cd + S * Pm[:, 2]
            S = S * Pm[:, 0]
            up[:, j], dn[:, j] = cu, cd
        return up, dn, hz


class Logistic:
    """Eight separate binary models, then the projection: the deployed method."""

    def fit(self, X, first, w, names):
        self.m = {}
        for kind, code in (('T', 1), ('A', 2)):
            for j, h in enumerate(H):
                o = first[:, j] != 3
                self.m[f'{kind}{h}'] = Mo.fit_logit(X[o], (first[o, j] == code).astype(float), names, l2=L2)
        return self

    def predict(self, X):
        P = np.c_[[Mo.predict(self.m[f'T{h}'], X) for h in H] + [Mo.predict(self.m[f'A{h}'], X) for h in H]].T
        up, dn = project(P, len(H))
        return up, dn, None


def auc(s, y):
    return float(Mo.auc(s, y)) if len(y) > 30 and 0 < y.mean() < 1 else None


def score(up, dn, first, ret300, hz, line):
    """Everything on rows whose 300-s outcome is observable."""
    o = first[:, -1] != 3
    u, d = np.clip(up[o, -1], 1e-6, 1), np.clip(dn[o, -1], 1e-6, 1)
    nn = np.clip(1 - u - d, 1e-6, 1)
    yu, yd = (first[o, -1] == 1).astype(float), (first[o, -1] == 2).astype(float)
    yn = 1 - yu - yd
    out = dict(rows=int(o.sum()), base_up=float(yu.mean()), base_down=float(yd.mean()),
               logloss3=float(-(yu * np.log(u) + yd * np.log(d) + yn * np.log(nn)).mean()),
               brier3=float(((u - yu) ** 2 + (d - yd) ** 2 + (nn - yn) ** 2).mean()),
               auc_activity=auc(u + d, yu + yd))
    ev = (yu + yd) > 0
    out['auc_direction_given_event'] = auc((u / (u + d))[ev], yu[ev])
    e = up[o, -1] - dn[o, -1]
    m = e >= line
    r = ret300[o]
    out['top'] = dict(n=int(m.sum()), up=float(yu[m].mean()) if m.any() else None, down=float(yd[m].mean()) if m.any() else None,
                      ret300_pct=float(100 * np.nanmean(r[m])) if m.any() and np.isfinite(r[m]).any() else None)
    if hz is not None:                                   # interval-level log loss on every observed at-risk interval
        evj, kind, last = intervals(first)
        tot, cnt = 0.0, 0
        for j in range(len(H)):
            risk = (last >= j) & ((evj < 0) | (evj >= j))
            y = np.where(evj[risk] == j, kind[risk], 0)
            tot += -np.log(np.clip(hz[risk, j][np.arange(risk.sum()), y], 1e-9, 1)).sum()
            cnt += int(risk.sum())
        out['interval_logloss'] = float(tot / max(cnt, 1))
    return out


def main():
    z = np.load(os.path.join(OUT, 'origins_v3.npz'))
    X, M, D = z['X'].astype(float), z['M'], z['D'].astype(int)
    days, names = [str(d) for d in z['days']], [str(n) for n in z['names']]
    mc = {str(n): i for i, n in enumerate(z['mcols'])}
    filled = M[:, mc['st']] == 1
    first = np.c_[[M[:, mc[f'first{h}']] for h in H]].T.astype(int)
    ret300 = M[:, mc['ret300']]
    pop = M[:, mc['pop']].astype(int)
    # one moment weighs one: the contracts of the same second of the same session share its weight
    key = D.astype(np.int64) * 10 ** 7 + (M[:, mc['t']] % 10 ** 6).astype(np.int64)
    _, inv, cnt = np.unique(key[filled], return_inverse=True, return_counts=True)
    w = np.zeros(len(X)); w[filled] = 1.0 / cnt[inv]
    act_cols = [names.index(n) for n in ACT]
    all_cols = list(range(len(names)))
    res = {}
    t0 = time.time()
    for d in range(MIN_TRAIN, len(days)):
        tr = filled & (D < d)
        te = filled & (D == d)
        models = dict(activity=Hazard(act_cols).fit(X[tr], first[tr], w[tr]),
                      hazard=Hazard(all_cols).fit(X[tr], first[tr], w[tr]),
                      logistic=Logistic().fit(X[tr], first[tr], w[tr], names))
        res[days[d]] = {}
        for nm, m in models.items():
            up_tr, dn_tr, _ = m.predict(X[tr])
            otr = first[tr][:, -1] != 3
            line = float(np.quantile((up_tr[:, -1] - dn_tr[:, -1])[otr], 0.95))     # from the training sessions only
            up, dn, hz = m.predict(X[te])
            res[days[d]][nm] = dict(line=line)
            for pname, mask in (('executable', (pop[te] & 2) > 0), ('broad', (pop[te] & 1) > 0)):
                res[days[d]][nm][pname] = score(up[mask], dn[mask], first[te][mask], ret300[te][mask],
                                                None if hz is None else hz[mask], line)
        e = res[days[d]]
        print(days[d], 'train sessions', d, '| executable rows', e['hazard']['executable']['rows'], '| logloss3',
              ' '.join(f"{nm} {e[nm]['executable']['logloss3']:.4f}" for nm in e), '| direction AUC',
              ' '.join(f"{nm} {(e[nm]['executable']['auc_direction_given_event'] or float('nan')):.3f}" for nm in e),
              f'| {time.time() - t0:.0f} s', flush=True)
    # summary: paired by session against the activity baseline
    rng = np.random.default_rng(11)
    summ = {}
    dd = sorted(res)
    for pname in ('executable', 'broad'):
        summ[pname] = {}
        for nm in ('hazard', 'logistic'):
            row = {}
            for metric, better in (('logloss3', -1), ('brier3', -1), ('auc_activity', 1), ('auc_direction_given_event', 1)):
                a = np.array([res[x][nm][pname][metric] if res[x][nm][pname][metric] is not None else np.nan for x in dd], float)
                b = np.array([res[x]['activity'][pname][metric] if res[x]['activity'][pname][metric] is not None else np.nan for x in dd], float)
                okk = np.isfinite(a) & np.isfinite(b)
                diff = (a - b)[okk]
                bs = [diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(2000)] if len(diff) else [np.nan]
                row[metric] = dict(mean=float(np.nanmean(a)), baseline=float(np.nanmean(b)), mean_diff=float(diff.mean()) if len(diff) else None,
                                   ci90=[float(np.quantile(bs, 0.05)), float(np.quantile(bs, 0.95))],
                                   sessions_better=int(((diff * better) > 0).sum()), sessions=int(len(diff)))
            tops = [res[x][nm][pname]['top'] for x in dd]
            n = sum(t['n'] for t in tops)
            row['top5pct'] = dict(n=n, sessions_with_any=int(sum(t['n'] > 0 for t in tops)),
                                  up=float(sum(t['n'] * (t['up'] or 0) for t in tops) / max(n, 1)),
                                  down=float(sum(t['n'] * (t['down'] or 0) for t in tops) / max(n, 1)),
                                  ret300_pct=float(sum(t['n'] * (t['ret300_pct'] or 0) for t in tops) / max(n, 1)),
                                  sessions_positive=int(sum((t['ret300_pct'] or 0) > 0 for t in tops if t['n'])))
            summ[pname][nm] = row
        tops = [res[x]['activity'][pname]['top'] for x in dd]
        n = sum(t['n'] for t in tops)
        summ[pname]['activity_top5pct'] = dict(n=n, ret300_pct=float(sum(t['n'] * (t['ret300_pct'] or 0) for t in tops) / max(n, 1)))
    json.dump(dict(min_train=MIN_TRAIN, l2=L2, days=dd, activity_features=ACT, by_day=res, summary=summ,
                   origins_sha256=json.load(open(os.path.join(OUT, 'origins_v3.manifest.json')))['sha256']),
              open(os.path.join(OUT, 'm2_compare.json'), 'w'), indent=1)
    for pname in ('executable', 'broad'):
        print('\n' + pname.upper(), 'population,', len(dd), 'unseen sessions; difference is model minus the activity-only baseline')
        for nm in ('hazard', 'logistic'):
            for metric, r in summ[pname][nm].items():
                if metric == 'top5pct':
                    print(f"  {nm:9s} top 5 % edge: n {r['n']}, up-first {r['up']:.3f}, down-first {r['down']:.3f}, mean 300-s return {r['ret300_pct']:+.3f} %, positive sessions {r['sessions_positive']}/{r['sessions_with_any']}")
                else:
                    print(f"  {nm:9s} {metric:26s} {r['mean']:.4f} (baseline {r['baseline']:.4f}) diff {r['mean_diff']:+.4f} 90 % [{r['ci90'][0]:+.4f}, {r['ci90'][1]:+.4f}] better on {r['sessions_better']}/{r['sessions']} sessions")
        a = summ[pname]['activity_top5pct']
        print(f"  activity  top 5 % edge: n {a['n']}, mean 300-s return {a['ret300_pct']:+.3f} %")


if __name__ == '__main__':
    main()
