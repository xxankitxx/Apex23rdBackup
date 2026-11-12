"""docs/36 N03 / N04 / N05 research on the 1-second tape datasets. Protocol frozen 9 Nov 2026 BEFORE the first run
(see docs/37 B8). Walk-forward by DATE: a test date is predicted only from earlier dates. Labels are executable:
buy at the ask one second after the signal, sell at the bid H seconds later. Read-only; prints tables, writes one json.
"""
import glob, json, math, os, sys
from datetime import datetime, timezone, timedelta
import numpy as np
sys.path.insert(0, 'D:/ApexOptions')
from apex import greeks

S = 'C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/'
IST = timezone(timedelta(hours=5, minutes=30))
H = 120            # holding horizon, seconds
STEP = 10          # one sample every 10 s
MIN_TRAIN_DATES = 5
Q = 0.99           # act when the prediction is above this quantile of the TRAINING predictions and above zero
RIDGE = 10.0
FRESH = 3.0


def load(path):
    z = np.load(path)
    n = len(z['strikes'])
    o = z['opt'][:, :n].astype(float); a = z['age'][:, :n].astype(float)
    order = np.argsort(z['strikes'])
    d = dict(t=z['t'].astype(float), fut=z['fut'].astype(float), K=z['strikes'][order].astype(float),
             bid=o[:, order][..., 0], ask=o[:, order][..., 1], age=a[:, order], exp=str(z['expiry']),
             name=os.path.basename(path)[:-4])
    d['date'] = d['name'][:10]
    ok = (d['bid'] > 0) & (d['ask'] > d['bid']) & (d['age'] <= FRESH)
    d['ok'] = ok
    d['mid'] = np.where(ok, 0.5 * (d['bid'] + d['ask']), np.nan)
    f = d['fut']; d['fm'] = 0.5 * (f[:, 0] + f[:, 1])
    # signed-flow proxy, as apex/engine/gen2.py
    x = np.zeros(len(f)); dep = None; k = 0.5 ** (1 / 60.0)
    for i in range(1, len(f)):
        dq = f[i, 3] - f[i - 1, 3]
        dq = dq if 0 <= dq < 1e9 else 0.0
        ltp = f[i, 2]
        sg = 1 if ltp >= f[i - 1, 1] else (-1 if ltp <= f[i - 1, 0] else (1 if ltp > f[i - 1, 2] else (-1 if ltp < f[i - 1, 2] else 0)))
        dd = 0.5 * (f[i, 4] + f[i, 5])
        if dd > 0:
            dep = dd if dep is None else k * dep + (1 - k) * dd
        x[i] = sg * dq / dep if dep else 0.0
    d['x'] = x
    # contiguous-second mask helper
    d['gap'] = np.r_[0.0, np.diff(d['t'])]
    return d


def contiguous(d, i0, i1):
    return i0 >= 0 and i1 < len(d['t']) and abs((d['t'][i1] - d['t'][i0]) - (i1 - i0)) <= 3


def atm(d, i):
    return int(np.argmin(np.abs(d['K'] - d['fm'][i])))


def label(d, i, j, rr):
    """Executable return of buying strike j, right rr one second after i and selling H seconds later."""
    a, b = i + 1, i + 1 + H
    if not contiguous(d, i, b) or not d['ok'][a, j, rr] or not d['ok'][b, j, rr]:
        return None
    return d['bid'][b, j, rr] / d['ask'][a, j, rr] - 1.0


def ridge_fit(X, y, lam=RIDGE):
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = (X - mu) / sd
    A = Z.T @ Z + lam * np.eye(Z.shape[1])
    w = np.linalg.solve(A, Z.T @ (y - y.mean()))
    return mu, sd, w, y.mean()


def ridge_pred(m, X):
    mu, sd, w, b = m
    return ((X - mu) / sd) @ w + b


def rank_ic(p, y):
    if len(p) < 30:
        return float('nan')
    rp, ry = np.argsort(np.argsort(p)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rp, ry)[0, 1])


def walk_forward(samples, feats, tag):
    """samples: list of dicts {date, t, y_ce, y_pe, f: {featset: vector}}. Returns the table rows per feature set."""
    n0 = len(samples)
    samples = [s for s in samples if all(np.isfinite(v).all() for v in s['f'].values())
               and np.isfinite(s['y_ce']) and np.isfinite(s['y_pe'])]
    print(f"{tag}: {n0 - len(samples)} samples dropped for a non-finite feature")
    dates = sorted({s['date'] for s in samples})
    out = {}
    for fs in feats:
        picks = []; ics = []
        for di, dte in enumerate(dates):
            if di < MIN_TRAIN_DATES:
                continue
            tr = [s for s in samples if s['date'] < dte]
            te = [s for s in samples if s['date'] == dte]
            if len(tr) < 500 or not te:
                continue
            Xtr = np.array([s['f'][fs] for s in tr]); Xte = np.array([s['f'][fs] for s in te])
            pred = {}
            for leg in ('y_ce', 'y_pe'):
                m = ridge_fit(Xtr, np.array([s[leg] for s in tr]))
                ptr = ridge_pred(m, Xtr); pte = ridge_pred(m, Xte)
                pred[leg] = (pte, max(np.quantile(ptr, Q), 0.0))
                ics.append(rank_ic(pte, np.array([s[leg] for s in te])))
            busy_until = -1
            for k, s in enumerate(te):
                if s['t'] < busy_until:
                    continue
                best = max(('y_ce', 'y_pe'), key=lambda L: pred[L][0][k] - pred[L][1])
                if pred[best][0][k] > pred[best][1]:
                    picks.append((dte, s['t'], best, s[best]))
                    busy_until = s['t'] + H
        ys = np.array([p[3] for p in picks]) if picks else np.array([])
        byd = {}
        for p in picks:
            byd[p[0]] = byd.get(p[0], 0.0) + p[3]
        out[fs] = dict(n=len(picks), mean_pct=round(100 * float(ys.mean()), 3) if len(ys) else None,
                       wins=int((ys > 0).sum()), sum_pct=round(100 * float(ys.sum()), 1) if len(ys) else 0.0,
                       days_up=sum(v > 0 for v in byd.values()), days_down=sum(v < 0 for v in byd.values()),
                       test_dates=len(dates) - MIN_TRAIN_DATES, ic=round(float(np.nanmean(ics)), 4) if ics else None, picks=[(p[0], float(p[1]), p[2], float(p[3])) for p in picks])
        print(f"{tag:5s} {fs:10s} picks {out[fs]['n']:4d} wins {out[fs]['wins']:4d} mean {out[fs]['mean_pct']} % "
              f"sum {out[fs]['sum_pct']} % days +{out[fs]['days_up']}/-{out[fs]['days_down']} of {out[fs]['test_dates']} | mean rank IC {out[fs]['ic']}")
    return out


def base_rate(samples, tag):
    y = np.array([s['y_ce'] for s in samples] + [s['y_pe'] for s in samples])
    print(f"{tag}: samples {len(samples)}, unconditional executable {H}-s return mean {100 * y.mean():.3f} %, "
          f"share > 0 {100 * (y > 0).mean():.1f} %")
    return dict(n=len(samples), mean_pct=round(100 * float(y.mean()), 3), share_up=round(float((y > 0).mean()), 3))


# ── N03: sequence order ──────────────────────────────────────────────────────────────────────────────────────────────
def sig2(path):
    """Degree-2 signature of a piecewise-linear path (rows = increments, columns = channels): level 1 and level 2."""
    n, c = path.shape
    s1 = np.zeros(c); s2 = np.zeros((c, c))
    for k in range(n):
        dx = path[k]
        s2 += np.outer(s1, dx) + 0.5 * np.outer(dx, dx)
        s1 += dx
    return np.r_[s1, s2.ravel()]


def n03_samples(d, scale):
    L, B = 60, 5
    out = []
    for i in range(L + 1, len(d['t']) - H - 2, STEP):
        if not contiguous(d, i - L, i):
            continue
        j = atm(d, i)
        idx = np.arange(i - L, i + 1, B)
        ce, pe = d['mid'][idx, j, 0], d['mid'][idx, j, 1]
        if np.isnan(ce).any() or np.isnan(pe).any():
            continue
        yc, yp = label(d, i, j, 0), label(d, i, j, 1)
        if yc is None or yp is None:
            continue
        fx = np.add.reduceat(d['x'][i - L + 1:i + 1], np.arange(0, L, B))
        inc = np.c_[np.diff(d['fm'][idx]), np.diff(ce), np.diff(pe), fx] / scale
        tcol = np.full((len(inc), 1), 1.0 / len(inc))
        full = np.c_[tcol, inc]
        shuf = full[np.random.RandomState(int(d['t'][i]) % 2 ** 31).permutation(len(full))]
        out.append(dict(date=d['date'], t=d['t'][i], y_ce=yc, y_pe=yp,
                        f=dict(endpoints=inc.sum(0), lags=inc.ravel(), sig2=sig2(full), sig2_shuf=sig2(shuf))))
    return out


# ── N05: surface migration ───────────────────────────────────────────────────────────────────────────────────────────
def surface(d, i, T):
    j = atm(d, i)
    c, p = d['mid'][i, j, 0], d['mid'][i, j, 1]
    if np.isnan(c) or np.isnan(p) or T <= 0:
        return None
    F = d['K'][j] + c - p                                    # parity forward at the ATM strike
    K = d['K']
    call = K >= F                                            # out-of-the-money side
    m = np.where(call, d['mid'][i, :, 0], d['mid'][i, :, 1])
    use = (np.abs(K - F) <= 300) & ~np.isnan(m) & (m >= 1.0)
    if use.sum() < 7:
        return None
    iv = np.asarray(greeks.implied_vol(m[use], F, K[use], T, call[use]), float).ravel()
    good = (iv > 0.01) & (iv < 3.0)
    xs, ivs = ((K[use] - F) / 100.0)[good], iv[good] * 100.0
    if len(xs) < 7:
        return None
    A = np.c_[np.ones(len(xs)), xs, np.square(xs)]
    coef, *_ = np.linalg.lstsq(A, np.array(ivs), rcond=None)
    return np.r_[coef, F, c + p]                              # level, skew, curvature, forward, straddle


def n05_samples(d):
    exp = datetime.fromisoformat(d['exp'] + 'T15:30:00').replace(tzinfo=IST)
    cache = {}
    def sf(i):
        if i not in cache:
            now = datetime.fromtimestamp(d['t'][i], IST)
            cache[i] = surface(d, i, greeks.years_to_expiry(d['exp'], now)) if now < exp else None
        return cache[i]
    out = []
    for i in range(61, len(d['t']) - H - 2, STEP):
        if not contiguous(d, i - 60, i):
            continue
        s1, s0 = sf(i), sf(i - 60)
        if s1 is None or s0 is None:
            continue
        j = atm(d, i)
        yc, yp = label(d, i, j, 0), label(d, i, j, 1)
        if yc is None or yp is None:
            continue
        dl, dsk, dcv, dF = s1[0] - s0[0], s1[1] - s0[1], s1[2] - s0[2], s1[3] - s0[3]
        dstr = (s1[4] / s0[4] - 1.0) * 100.0
        out.append(dict(date=d['date'], t=d['t'][i], y_ce=yc, y_pe=yp, dte0=d['date'] == d['exp'],
                        f=dict(surface=np.array([dl, dsk, dcv, dF / 10.0, s1[0], s1[1]]), iv_mom=np.array([dl]),
                               prem_mom=np.array([dstr, dF / 10.0]), fwd_only=np.array([dF / 10.0]))))
    return out


# ── N04: cross-strike propagation ────────────────────────────────────────────────────────────────────────────────────
def n04(days):
    """Signal at second i for target (ATM strike, right rr): the mean delta-adjusted 2-s move of the fresh neighbours
    minus the target's own. Outcome: (a) the target's delta-adjusted mid change over the next 3 s and 10 s;
    (b) executable: buy at the ask at i+1, sell at the bid 30 s later."""
    HH = 30
    rows = []
    for d in days:
        n = len(d['t'])
        dF2 = d['fm'][2:] - d['fm'][:-2]
        for i in range(302, n - HH - 3, 2):
            if not contiguous(d, i - 300, i + HH + 1):
                continue
            j = atm(d, i)
            if j < 2 or j > len(d['K']) - 3:
                continue
            for rr in (0, 1):
                nb = [(j + o, rr) for o in (-2, -1, 1, 2)] + [(j + o, 1 - rr) for o in (-1, 0, 1)]
                tgt = d['mid'][i - 300:i + 1, j, rr]
                if np.isnan(tgt[-3:]).any() or not d['ok'][i + 1, j, rr] or not d['ok'][i + 1 + HH, j, rr]:
                    continue
                fseg = d['fm'][i - 300:i + 1]
                def delta(series):
                    a = np.diff(series[::5]); b = np.diff(fseg[::5])
                    okm = ~np.isnan(a)
                    if okm.sum() < 30 or np.var(b[okm]) <= 0:
                        return None
                    return float(np.cov(a[okm], b[okm])[0, 1] / np.var(b[okm]))
                dt_ = delta(tgt)
                if dt_ is None:
                    continue
                dF = d['fm'][i] - d['fm'][i - 2]
                own = (tgt[-1] - tgt[-3]) - dt_ * dF
                res, raw = [], []
                for (k, r2) in nb:
                    s = d['mid'][i - 300:i + 1, k, r2]
                    if np.isnan(s[-3:]).any() or d['age'][i, k, r2] > 1.5:
                        continue
                    dk = delta(s)
                    if dk is None:
                        continue
                    res.append((s[-1] - s[-3]) - dk * dF); raw.append(s[-1] - s[-3])
                if len(res) < 4 or d['age'][i, j, rr] > 1.5:
                    continue
                m3 = d['mid'][i + 3, j, rr]; m10 = d['mid'][i + 10, j, rr]
                if np.isnan(m3) or np.isnan(m10):
                    continue
                f3 = (m3 - tgt[-1]) - dt_ * (d['fm'][i + 3] - d['fm'][i])
                f10 = (m10 - tgt[-1]) - dt_ * (d['fm'][i + 10] - d['fm'][i])
                y = d['bid'][i + 1 + HH, j, rr] / d['ask'][i + 1, j, rr] - 1.0
                spread = (d['ask'][i, j, rr] - d['bid'][i, j, rr])
                rows.append((d['date'], d['t'][i], float(np.mean(res)) - own, own, float(np.mean(raw)) - (tgt[-1] - tgt[-3]),
                             f3, f10, y, spread))
    R = np.array([r[2:] for r in rows]); dates = np.array([r[0] for r in rows]); ts = np.array([r[1] for r in rows])
    print(f"N04 rows {len(R)}; median target spread {np.median(R[:, 6]):.2f} pts; unconditional executable 30-s return "
          f"{100 * R[:, 5].mean():.3f} %")
    res = {}
    for name, col in (('neighbours_minus_own', 0), ('own_momentum', 1), ('raw_cross_avg', 2)):
        sig = R[:, col]
        ic3, ic10 = rank_ic(sig, R[:, 3]), rank_ic(sig, R[:, 4])
        ud = sorted(set(dates)); picks = []
        for di, dte in enumerate(ud):
            if di < MIN_TRAIN_DATES:
                continue
            thr = np.quantile(sig[dates < dte], Q)
            te = np.where(dates == dte)[0]; busy = -1
            for k in te:
                if ts[k] < busy or sig[k] <= thr:
                    continue
                picks.append((dte, R[k, 5], R[k, 3], R[k, 4])); busy = ts[k] + HH
        ys = np.array([p[1] for p in picks]); byd = {}
        for p in picks:
            byd[p[0]] = byd.get(p[0], 0.0) + p[1]
        res[name] = dict(ic3=round(ic3, 4), ic10=round(ic10, 4), n=len(picks), mean_pct=round(100 * float(ys.mean()), 3) if len(ys) else None,
                         wins=int((ys > 0).sum()), fwd3_pts=round(float(np.mean([p[2] for p in picks])), 3) if picks else None,
                         fwd10_pts=round(float(np.mean([p[3] for p in picks])), 3) if picks else None,
                         days_up=sum(v > 0 for v in byd.values()), days_down=sum(v < 0 for v in byd.values()))
        r = res[name]
        print(f"N04  {name:22s} rank IC 3s {r['ic3']} 10s {r['ic10']} | top-1% picks {r['n']} wins {r['wins']} "
              f"executable mean {r['mean_pct']} % | target's own catch-up: {r['fwd3_pts']} pts in 3 s, {r['fwd10_pts']} in 10 s "
              f"| days +{r['days_up']}/-{r['days_down']}")
    return res


if __name__ == '__main__':
    which = sys.argv[1:] or ['n03', 'n05', 'n04']
    days = [load(p) for p in sorted(glob.glob(S + 'ds/*.npz'))]
    print('files', len(days), 'dates', len({d['date'] for d in days}))
    result = {}
    if 'n03' in which:
        scale = np.array([5.0, 2.5, 2.5, 0.05])                  # fixed a priori: points, points, points, flow units
        sm = [s for d in days for s in n03_samples(d, scale)]
        result['n03_base'] = base_rate(sm, 'N03')
        result['n03'] = walk_forward(sm, ('endpoints', 'lags', 'sig2', 'sig2_shuf'), 'N03')
    if 'n05' in which:
        sm = [s for d in days for s in n05_samples(d)]
        result['n05_base'] = base_rate(sm, 'N05')
        result['n05'] = walk_forward(sm, ('fwd_only', 'iv_mom', 'prem_mom', 'surface'), 'N05')
        nz = [s for s in sm if not s['dte0']]
        print('N05 without expiry days:')
        result['n05_no_dte0'] = walk_forward(nz, ('fwd_only', 'iv_mom', 'prem_mom', 'surface'), 'N05x')
    if 'n04' in which:
        result['n04'] = n04(days)
    json.dump(result, open(S + 'research_' + '_'.join(which) + '.json', 'w'), indent=1, default=float)
