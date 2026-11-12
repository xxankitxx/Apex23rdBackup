"""docs/38 section 7, S01 and S02: the fresh-data capability check and a first look, 10 Nov 2026. Read-only on ds_v2.

Everything below was fixed BEFORE the first run of this file. The 15 sessions are discovery material for S01 and S02
(docs/38 section 8): nothing here is a held-out result, and nothing here is a trade.

CAPABILITY (can the hypothesis be measured at all, second by second?)
  S01  share of heavyweight weight whose cash print AND stock-futures two-sided quote are both at most FRESH s old.
  S02  near the forward (five strikes), the number of strikes whose CE and PE both hold a fresh two-sided quote, in
       the current week and in the next week.

FIRST LOOK (does the measured quantity carry any information about what happens next?)
  S01  x  = weight-mean over covered stocks of [ln stock-future mid change - ln cash change] over the last L s, in
            index points (times the Nifty future). Needs COVER of the weight fresh at both ends.
       controls: c_cash = weight-mean cash change, c_sfut = weight-mean stock-future change, c_mom = the Nifty future's
            own change, all over the same L s, same units.
       target: the Nifty future's mid change from t+1 to t+1+H, points.
  S02  x  = change over L s of the next week's total-variance proxy at the strike nearest the forward;
       control c_near = the same change in the current week (near-week IV momentum).
       total-variance proxy = (straddle mid / (0.7979 * forward))^2, a fixed strike over the window, both legs fresh.
       target: the current week's straddle mid (that strike), t+1 to t+1+H, per cent.
  For each: the mean over days of the daily Spearman rank correlation (rows 10 s apart), the number of days it is
  positive, and the same for the part of x that the controls do not explain (ordinary least squares fitted on EARLIER
  days only, so the first MIN_TRAIN days give no residual figure)."""
import glob, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
from apex import config
DS = os.path.join(config.RESEARCH_DIR, 'ds_v2')
OUT = os.path.join(config.RESEARCH_DIR, 'gen2_v2')
FRESH, COVER, MIN_TRAIN, STEP = 5.0, 0.5, 5, 10
LS, HS = (30, 60), (30, 60, 120)


def rank(a):
    r = np.empty(len(a)); r[np.argsort(a, kind='stable')] = np.arange(len(a)); return r


def ic(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 50 or np.std(x[m]) == 0 or np.std(y[m]) == 0:
        return None
    return float(np.corrcoef(rank(x[m]), rank(y[m]))[0, 1])


def grid(z):
    """Per-second arrays on a gap-free clock (missing seconds are NaN rows)."""
    t = z['t'].astype(np.int64); n = int(t[-1] - t[0]) + 1; ix = (t - t[0]).astype(int)

    def g(a, fill=np.nan):
        out = np.full((n,) + a.shape[1:], fill, float); out[ix] = a; return out
    return t[0], n, g


def lag(a, k):
    out = np.full_like(a, np.nan); out[k:] = a[:-k]; return out


def lead(a, k):
    out = np.full_like(a, np.nan); out[:-k] = a[k:]; return out


def one(path):
    z = np.load(path)
    if len(z['t']) < 1800:
        return None
    t0, n, g = grid(z)
    fut = g(z['fut']); fa = g(z['fa'], 1e9)
    fm = np.where((fut[:, 0] > 0) & (fut[:, 1] >= fut[:, 0]) & (fa[:, 0] <= FRESH), 0.5 * (fut[:, 0] + fut[:, 1]), np.nan)
    w = z['w'].astype(float); w = w / w.sum()
    hw, hwa, sf, sfa = g(z['hw']), g(z['hwa'], 1e9), g(z['sf']), g(z['sfa'], 1e9)
    c_ok = np.isfinite(hw) & (hw > 0) & (hwa <= FRESH)
    sfm = 0.5 * (sf[..., 0] + sf[..., 1])
    f_ok = (sf[..., 0] > 0) & (sf[..., 1] >= sf[..., 0]) & (sfa <= FRESH)
    row = np.isfinite(fm)
    cap = dict(rows=int(row.sum()), stocks=int(len(w)), stock_futures=int((np.nanmax(np.where(sf[..., 0] > 0, 1.0, 0.0), axis=0) > 0).sum()),
               cash_w_med=round(float(np.median((c_ok * w).sum(1)[row])), 3), pair_w_med=round(float(np.median(((c_ok & f_ok) * w).sum(1)[row])), 3),
               pair_w_p10=round(float(np.percentile(((c_ok & f_ok) * w).sum(1)[row], 10)), 3),
               pair_cover_share=round(float((((c_ok & f_ok) * w).sum(1)[row] >= COVER).mean()), 3),
               sfut_age_med_s=round(float(np.median(sfa[row][sfa[row] < 1e8])), 2) if (sfa[row] < 1e8).any() else None)
    res = {'cap': cap, 's01': {}, 's02': {}}
    for L in LS:
        ok = c_ok & f_ok & lag(c_ok.astype(float), L).astype(bool) & lag(f_ok.astype(float), L).astype(bool)
        with np.errstate(all='ignore'):
            rc = np.where(ok, np.log(hw / lag(hw, L)), 0.0); rf = np.where(ok, np.log(sfm / lag(sfm, L)), 0.0)
        cw = (ok * w).sum(1)
        good = (cw >= COVER) & np.isfinite(fm) & np.isfinite(lag(fm, L))
        with np.errstate(all='ignore'):
            x = np.where(good, ((rf - rc) * w).sum(1) / cw * fm, np.nan)
            cc = np.where(good, (rc * w).sum(1) / cw * fm, np.nan); cs = np.where(good, (rf * w).sum(1) / cw * fm, np.nan)
        cm = np.where(good, fm - lag(fm, L), np.nan)
        for H in HS:
            y = lead(fm, 1 + H) - lead(fm, 1)
            s = slice(0, n, STEP)
            res['s01'][f'{L}/{H}'] = dict(x=x[s], c_cash=cc[s], c_sfut=cs[s], c_mom=cm[s], y=y[s])
    # S02
    K1, K2 = z['strikes'].astype(float), z['strikes2'].astype(float)
    cap['expiry'], cap['expiry2'] = str(z['expiry']), str(z['expiry2'])
    if len(K2):
        def strad(opt, age, K):
            o, a = g(opt), g(age, 1e9)                      # (n, MAXK, 2 legs, bid/ask)
            o, a = o[:, :len(K)], a[:, :len(K)]
            ok = (o[..., 0] > 0) & (o[..., 1] > o[..., 0]) & (a <= FRESH)
            mid = 0.5 * (o[..., 0] + o[..., 1])
            both = ok[..., 0] & ok[..., 1]
            return np.where(both, mid[..., 0] + mid[..., 1], np.nan), both
        s1, b1 = strad(z['opt'], z['age'], K1); s2, b2 = strad(z['opt2'], z['age2'], K2)
        common = [k for k in K1 if k in set(K2)]
        i1 = np.array([int(np.where(K1 == k)[0][0]) for k in common]); i2 = np.array([int(np.where(K2 == k)[0][0]) for k in common])
        Kc = np.array(common)
        near = np.abs(Kc[None, :] - np.where(np.isfinite(fm), fm, 0)[:, None]) <= 125.0
        cap['near_two_sided_med'] = float(np.median((b1[:, i1] & near).sum(1)[row])) if len(common) else None
        cap['next_two_sided_med'] = float(np.median((b2[:, i2] & near).sum(1)[row])) if len(common) else None
        cap['next_atm_share'] = None
        if len(common):
            j = np.argmin(np.abs(Kc[None, :] - np.where(np.isfinite(fm), fm, 0)[:, None]), axis=1)
            r = np.arange(n)
            a1, a2 = s1[:, i1], s2[:, i2]
            cap['next_atm_share'] = round(float(np.isfinite(a2[r, j])[row].mean()), 3)
            cap['near_atm_share'] = round(float(np.isfinite(a1[r, j])[row].mean()), 3)
            for L in LS:
                jl = lag(j.astype(float), L)
                x = np.full(n, np.nan); cn = np.full(n, np.nan)
                v = np.isfinite(jl) & np.isfinite(fm) & np.isfinite(lag(fm, L)); v[:L] = False
                rr = r[v]; jj = jl[v].astype(int)
                tv = lambda s_now, s_then: (s_now / (0.7979 * fm[rr])) ** 2 - (s_then / (0.7979 * fm[rr - L])) ** 2
                x[rr] = tv(a2[rr, jj], a2[rr - L, jj]); cn[rr] = tv(a1[rr, jj], a1[rr - L, jj])
                for H in HS:
                    y = np.full(n, np.nan)
                    v2 = rr + 1 + H < n
                    r2, j2 = rr[v2], jj[v2]
                    y[r2] = 100.0 * (a1[r2 + 1 + H, j2] / a1[r2 + 1, j2] - 1.0)
                    s = slice(0, n, STEP)
                    res['s02'][f'{L}/{H}'] = dict(x=x[s], c_near=cn[s], y=y[s])
    return res


def summarise(name, per_day, ctrls, rctl=None):
    out = {}
    for key in sorted({k for d in per_day.values() for k in d}):
        dates = sorted(d for d in per_day if key in per_day[d])
        row = {}
        for v in ('x',) + ctrls:
            ics = [ic(per_day[d][key][v], per_day[d][key]['y']) for d in dates]
            ics = [i for i in ics if i is not None]
            row[v] = dict(ic=round(float(np.mean(ics)), 4) if ics else None, days_pos=int(sum(i > 0 for i in ics)), days=len(ics))
        rs = []
        all_ctrls, ctrls = ctrls, (rctl or ctrls)
        for k, d in enumerate(dates):                         # x after the controls, coefficients from earlier days only
            if k < MIN_TRAIN:
                continue
            A = np.concatenate([np.column_stack([per_day[e][key][c] for c in ctrls]) for e in dates[:k]])
            b = np.concatenate([per_day[e][key]['x'] for e in dates[:k]])
            m = np.isfinite(A).all(1) & np.isfinite(b)
            if m.sum() < 500:
                continue
            A1 = np.column_stack([A[m], np.ones(m.sum())])
            coef = np.linalg.lstsq(A1, b[m], rcond=None)[0]
            T = np.column_stack([per_day[d][key][c] for c in ctrls])
            resid = per_day[d][key]['x'] - np.column_stack([T, np.ones(len(T))]) @ coef
            i = ic(resid, per_day[d][key]['y'])
            if i is not None:
                rs.append(i)
        ctrls = all_ctrls
        row['x_after_controls'] = dict(ic=round(float(np.mean(rs)), 4) if rs else None, days_pos=int(sum(i > 0 for i in rs)), days=len(rs))
        out[key] = row
        print(f"{name} window/horizon {key:7s} " + ' | '.join(f"{v} IC {row[v]['ic']} (+{row[v]['days_pos']}/{row[v]['days']})" for v in row))
    return out


def main():
    caps, d1, d2 = {}, {}, {}
    for p in sorted(glob.glob(os.path.join(DS, '*.npz'))):
        r = one(p)
        if r is None:
            continue
        part = os.path.basename(p)[:-4]; date = part[:10]
        caps[part] = r['cap']
        print(part, json.dumps(r['cap']), flush=True)
        for src, dst in ((r['s01'], d1), (r['s02'], d2)):
            for key, v in src.items():
                cur = dst.setdefault(date, {})
                cur[key] = v if key not in cur else {k: np.concatenate([cur[key][k], v[k]]) for k in v}
    # 10 Nov, AFTER the first run: x is exactly c_sfut - c_cash, so with both as controls the residual was rounding
    # noise and its figure meant nothing (first run kept in results_s01_s02_check_run1.txt). The residual now uses
    # c_cash and c_mom only; c_sfut is still reported on its own.
    s1 = summarise('S01', d1, ('c_cash', 'c_sfut', 'c_mom'), rctl=("c_cash", "c_mom"))
    s2 = summarise('S02', d2, ('c_near',))
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(spec='frozen 10 Nov 2026 before the first run', fresh_s=FRESH, cover=COVER, step_s=STEP, min_train_days=MIN_TRAIN,
                   capability=caps, s01=s1, s02=s2), open(os.path.join(OUT, 's01_s02_check.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
