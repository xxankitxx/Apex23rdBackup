import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 step 2: one ds_v2 part -> per-second microstructure features of the Nifty future, targets, the parity forward
and lead-lag statistics; plus per-trade option checks at entry for the trades of that day.
Usage: py -3.13 s2_part.py <part> [<part> ...]   (one part at a time is the rule while the market is open)
Writes work/R07/feat_<part>.npz and prints the lead-lag tables."""
import json, os, time
import numpy as np

DS = r"D:\ApexOptions\data\research\ds_v2"
OUT = r"D:\ApexOptions\data\research\13nov\work\R07"
WINS = (5, 10, 30, 60, 120)
HZN = (30, 60, 120, 300)


def wsum_time(t, x, W):
    """sum of x over rows with t in (t_i - W, t_i] (causal), by cumulative sums."""
    c = np.concatenate([[0.0], np.cumsum(np.nan_to_num(x))])
    j = np.searchsorted(t, t - W, side="right")
    return c[1:] - c[j]


def at_time(t, y, tq):
    """value of y at the last row with t <= tq (nan if before the first row)."""
    j = np.searchsorted(t, tq, side="right") - 1
    out = np.where(j >= 0, y[np.clip(j, 0, None)], np.nan)
    return out, j


def run(part):
    t0 = time.time()
    z = np.load(os.path.join(DS, part + ".npz"))
    t = z["t"].astype(float)
    n = len(t)
    if n == 0:
        print(part, "empty"); return
    fut = z["fut"].astype(float); fa = z["fa"].astype(float)
    bid, ask, ltp, ttq, bq, aq = (fut[:, k] for k in range(6))
    qa, da = fa[:, 0], fa[:, 1]
    okq = (bid > 0) & (ask >= bid) & ((ask - bid) <= 30.0)
    fm = np.where(okq, 0.5 * (bid + ask), ltp)
    spr = np.where(okq, ask - bid, np.nan)
    dep = bq + aq
    I5 = np.where(dep > 0, (bq - aq) / dep, np.nan)
    wmo = 0.5 * spr * I5                                   # weighted-mid minus mid (points), 5-level sizes
    # OFI (Cont, Kukanov, Stoikov 2014) with best prices and 5-level totals as the queue sizes
    pb, pa, pbq, paq = (np.r_[np.nan, x[:-1]] for x in (bid, ask, bq, aq))
    e = (np.where(bid >= pb, bq, 0.0) - np.where(bid <= pb, pbq, 0.0)
         - np.where(ask <= pa, aq, 0.0) + np.where(ask >= pa, paq, 0.0))
    e[~(okq & np.r_[False, okq[:-1]])] = 0.0
    e[~np.isfinite(e)] = 0.0
    # net depth change, price-level blind (queue build-up minus queue build-up)
    ndc = np.r_[0.0, np.diff(bq)] - np.r_[0.0, np.diff(aq)]
    ndc[~np.isfinite(ndc)] = 0.0
    # trade flow: volume each second signed against the previous quote (Lee-Ready style, then tick rule)
    dv = np.r_[0.0, np.diff(ttq)]
    dv = np.where(np.isfinite(dv) & (dv > 0), dv, 0.0)
    pmid = np.r_[np.nan, fm[:-1]]
    pl = np.r_[np.nan, ltp[:-1]]
    sgn = np.where(ltp >= pa, 1.0, np.where(ltp <= pb, -1.0, np.sign(ltp - pmid)))
    sgn = np.where(sgn == 0, np.sign(ltp - pl), sgn)
    sgn = np.nan_to_num(sgn)
    sv = sgn * dv
    depbar = wsum_time(t, np.nan_to_num(dep) / 2.0, 300) / np.maximum(wsum_time(t, np.isfinite(dep).astype(float), 300), 1)
    volbar = wsum_time(t, dv, 300) / 300.0
    F = {}
    F["spr"] = spr
    F["I5"] = I5
    F["wmo"] = wmo
    F["qage"] = qa
    F["dage"] = da
    for W in WINS:
        F[f"ofi{W}"] = wsum_time(t, e, W) / np.maximum(depbar, 1.0)
        F[f"ndc{W}"] = wsum_time(t, ndc, W) / np.maximum(depbar, 1.0)
        F[f"tfi{W}"] = wsum_time(t, sv, W) / np.maximum(volbar * W, 1.0)
    # imbalance change and microprice drift proxies
    I5_10, _ = at_time(t, I5, t - 10)
    F["dI5_10"] = I5 - I5_10
    for W in (10, 30, 60, 120, 300):
        p0, _ = at_time(t, fm, t - W)
        F[f"r{W}"] = fm - p0
    # realised vol of 1-s mid changes over 300 s (points per sqrt s) for scaling
    d1 = np.r_[0.0, np.diff(fm)]
    d1[~np.isfinite(d1)] = 0.0
    rv = np.sqrt(wsum_time(t, d1 * d1, 600) / np.maximum(wsum_time(t, np.ones(n), 600), 1))
    F["rv600"] = rv
    # ---- the parity forward of the weekly from option mids (as the engine does, legs <= 30 s old)
    K = z["strikes"].astype(float)
    nk = len(K)
    o = z["opt"][:, :nk].astype(float); oa = z["age"][:, :nk].astype(float)
    ob, oaK = o[..., 0], o[..., 1]
    om = np.where((ob > 0) & (oaK >= ob), 0.5 * (ob + oaK), np.nan)
    fresh = oa <= 30.0
    om_f = np.where(fresh, om, np.nan)
    C, P = om_f[:, :, 0], om_f[:, :, 1]
    Fk = K[None, :] + C - P
    # ATM by |C-P| smallest; take median of the 3 strikes nearest that ATM
    cp = np.abs(C - P)
    cp = np.where(np.isfinite(cp), cp, np.inf)
    j0 = np.argmin(cp, axis=1)
    fwd = np.full(n, np.nan)
    order = np.argsort(K)
    Ks = K[order]
    pos = np.searchsorted(Ks, K[j0])
    for dj in (-1, 0, 1):
        pass
    rows = np.arange(n)
    cand = []
    for dj in (-1, 0, 1):
        q = np.clip(pos + dj, 0, nk - 1)
        cand.append(Fk[rows, order[q]])
    cand = np.vstack(cand)
    with np.errstate(all="ignore"):
        fwd = np.nanmedian(cand, axis=0)
    fwd[~np.isfinite(cp[rows, j0])] = np.nan
    # 5-s EMA of each (the c20 strategy smooths the forward with tau = 5 s)
    def ema(x, tau=5.0):
        y = np.full(n, np.nan); a = 1.0 / tau; prev = np.nan
        for i in range(n):
            v = x[i]
            if np.isfinite(v):
                prev = v if not np.isfinite(prev) else prev + a * (v - prev)
            y[i] = prev
        return y
    fs_fwd = ema(fwd); fs_fut = ema(fm)
    # ---- lead-lag on a regular 1-s grid
    g = np.arange(t[0], t[-1] + 1)
    fg, _ = at_time(t, fm, g)
    wg, _ = at_time(t, fwd, g)
    dF = np.diff(fg); dW = np.diff(wg)
    ok = np.isfinite(dF) & np.isfinite(dW)
    ll = {}
    for k in range(-5, 6):
        if k >= 0:
            a_, b_ = dF[:len(dF) - k], dW[k:]
        else:
            a_, b_ = dF[-k:], dW[:len(dW) + k]
        m_ = np.isfinite(a_) & np.isfinite(b_)
        ll[k] = float(np.corrcoef(a_[m_], b_[m_])[0, 1]) if m_.sum() > 100 else np.nan
    # ATM CE / PE mid vs future: correlation of the option's 1-s change with the future's change k seconds earlier
    # (ATM by |C-P| at each second, the contract's own mid on both sides of the difference)
    llo = {"CE": {}, "PE": {}}
    jg = np.searchsorted(t, g, side="right") - 1
    jatm = j0[np.clip(jg, 0, n - 1)]
    for s, rr in ((0, "CE"), (1, "PE")):
        mg = om[np.clip(jg, 0, n - 1), jatm, s]                       # option mid at grid second (ATM of that second)
        mg_prev = np.r_[np.nan, om[np.clip(jg[:-1], 0, n - 1), jatm[1:], s]]   # same contract one second earlier
        dO = (mg - mg_prev)[1:]
        for k in range(0, 6):
            a_ = dF[:len(dF) - k] if k > 0 else dF
            b_ = dO[k:]
            m_ = np.isfinite(a_) & np.isfinite(b_)
            llo[rr][k] = float(np.corrcoef(a_[m_], b_[m_])[0, 1]) if m_.sum() > 100 else np.nan
        # staleness: share of seconds the future moved >= 2 pts and the ATM option mid did not change at all
        big = np.isfinite(dF) & (np.abs(dF) >= 2.0) & np.isfinite(dO)
        llo[rr]["stale_share_on_2pt"] = float(np.mean(dO[big] == 0)) if big.sum() else np.nan
        llo[rr]["n_2pt"] = int(big.sum())
    # cumulative response: option mid change over [t, t+k] per 1 pt future move in second t (impulse response)
    # option quote ages at ATM
    a_atm = oa[rows, j0, 0]
    # forward vs future: lag in seconds that maximises correlation of 5-s changes
    dF5 = fg[5:] - fg[:-5]; dW5 = wg[5:] - wg[:-5]
    ll5 = {}
    for k in range(-5, 11):
        if k >= 0:
            a_, b_ = dF5[:len(dF5) - k], dW5[k:]
        else:
            a_, b_ = dF5[-k:], dW5[:len(dW5) + k]
        m_ = np.isfinite(a_) & np.isfinite(b_)
        ll5[k] = float(np.corrcoef(a_[m_], b_[m_])[0, 1]) if m_.sum() > 100 else np.nan
    # c20-style 5-pt resumption timing: when the 5-s EMA crosses a level, which series crosses first?
    # measure: for each grid second where |fs_fut(t) - fs_fut(t-20)| >= 5, the delay until fs_fwd moved the same 5 pts
    fsf_g, _ = at_time(t, fs_fut, g); fsw_g, _ = at_time(t, fs_fwd, g)
    dly = []
    i = 25
    N = len(g)
    while i < N - 30:
        if np.isfinite(fsf_g[i]) and np.isfinite(fsf_g[i - 20]) and abs(fsf_g[i] - fsf_g[i - 20]) >= 5 and np.isfinite(fsw_g[i - 20]):
            sgn_ = np.sign(fsf_g[i] - fsf_g[i - 20])
            base = fsw_g[i - 20]
            # time when the forward first moved 5 pts (same sign) from its own level 20 s earlier... relative to i
            jj = None
            for k in range(-20, 31):
                v = fsw_g[i + k] if 0 <= i + k < N else np.nan
                if np.isfinite(v) and (v - base) * sgn_ >= 5:
                    jj = k; break
            dly.append(jj if jj is not None else 99)
            i += 30
        else:
            i += 1
    dly = np.array(dly, float)
    # targets
    T = {}
    for h in HZN:
        y, jh = at_time(t, fm, t + h)
        gap = (t + h) - t[np.clip(jh, 0, n - 1)]
        y[gap > 5] = np.nan
        T[f"y{h}"] = y - fm
    names = list(F)
    X = np.vstack([F[k] for k in names]).T.astype(np.float32)
    Y = np.vstack([T[k] for k in T]).T.astype(np.float32)
    np.savez_compressed(os.path.join(OUT, f"feat_{part}.npz"), t=t, fm=fm, fwd=fwd, X=X, names=np.array(names), Y=Y,
                        ynames=np.array(list(T)), okq=okq)
    res = dict(part=part, rows=n, spr_pct=np.nanpercentile(spr, [10, 50, 90, 99]).round(2).tolist(),
               qage_pct=np.nanpercentile(qa, [50, 90, 99]).round(2).tolist(),
               dage_pct=np.nanpercentile(np.where(da < 1e8, da, np.nan), [50, 90, 99]).round(2).tolist(),
               atm_ce_age_pct=np.nanpercentile(np.where(a_atm < 1e8, a_atm, np.nan), [50, 90, 99]).round(2).tolist(),
               fut_minus_fwd_med=float(np.nanmedian(fm - fwd)), fut_minus_fwd_sd=float(np.nanstd(fm - fwd)),
               ll_1s_fut_vs_fwd=ll, ll_5s_fut_vs_fwd=ll5, ll_opt=llo,
               resume5_delay_s=dict(n=int(len(dly)), med=float(np.median(dly[dly < 99])) if (dly < 99).any() else None,
                                    p25=float(np.percentile(dly[dly < 99], 25)) if (dly < 99).any() else None,
                                    p75=float(np.percentile(dly[dly < 99], 75)) if (dly < 99).any() else None,
                                    never=int((dly == 99).sum()), fwd_first=int((dly < 0).sum())),
               secs=round(time.time() - t0, 1))
    json.dump(res, open(os.path.join(OUT, f"leadlag_{part}.json"), "w"), indent=1, default=float)
    print(json.dumps(res, default=float), flush=True)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        run(p)
