"""Event dataset (ChatGPT's 6 Nov proposal): per-second option outcomes, runner events, onset candidates, and causal
path / order / derivative features, from raw_<day>.npz (extract_all.py).

    from events import day_data, outcomes, runner_events, onsets, features
    A = day_data(day)            # session arrays: T, hm, fwd, fut book, stocks, options, expiry
    O = outcomes(A)              # per second, per side (0 CE, 1 PE): entry, mfe, mae, ret_h, first-passage flags
    R = runner_events(A, O)      # clusters of seconds where +20 % came before -10 % within 15 min (one per move)
    C = onsets(A)                # candidate "a move is starting" moments (forward burst), both directions
    Fm = features(A, idx, side)  # feature table at rows idx for the given sides (rows <= i only)

Outcome convention (same as the kit): buy the nearest-ITM option of the side at the ASK two seconds after time i,
value it at the BID afterwards. Nearest-ITM: strike just below the forward for a call, just above for a put.
"""
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
F = {f: k for k, f in enumerate(("ltp", "bid", "ask", "bqty", "aqty", "tbq", "tsq", "ttq", "oi", "ltt", "bq5", "aq5"))}
LAG = 2
H = 900
HORIZ = (30, 60, 180, 300, 600, 900)
_A = {}


def _ffill(x):
    """Forward-fill along axis 0 (NaN and non-positive prices count as missing for price fields)."""
    x = np.array(x, float)
    good = np.isfinite(x)
    idx = np.where(good, np.arange(len(x))[:, None] if x.ndim == 2 else np.arange(len(x)), 0)
    np.maximum.accumulate(idx, axis=0, out=idx)
    out = np.take_along_axis(x, idx, axis=0) if x.ndim == 2 else x[idx]
    out[~np.maximum.accumulate(good, axis=0)] = np.nan
    return out


def day_data(day):
    if day in _A:
        return _A[day]
    _A.clear()
    z = np.load(os.path.join(HERE, f"raw_{day}.npz"), allow_pickle=True)
    T, X = z["T"], z["X"]
    names, kind, wn = list(z["names"]), list(z["kind"]), z["wn"]
    from datetime import datetime, timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    y, m, d = (int(v) for v in day.split("-"))
    t0 = datetime(y, m, d, 9, 15, tzinfo=IST).timestamp()
    t1 = datetime(y, m, d, 15, 30, tzinfo=IST).timestamp()
    keep = (T >= t0) & (T <= t1)
    T, X = T[keep], X[keep]
    A = {"day": day, "T": T, "hm": 555.0 + (T - t0) / 60.0, "expiry": str(z["expiry"])}
    A["dte0"] = A["expiry"] == day

    def px(nm, f="ltp"):
        j = names.index(nm)
        v = X[:, j, F[f]].astype(float)
        if f in ("ltp", "bid", "ask"):
            v = np.where(v > 0, v, np.nan)
        return _ffill(v)
    A["spot"] = px("NIFTY|SPOT")
    fb, fa = px("NIFTY|FUT", "bid"), px("NIFTY|FUT", "ask")
    A["fut_bid"], A["fut_ask"] = fb, fa
    A["fut_bq"], A["fut_aq"] = _ffill(X[:, names.index("NIFTY|FUT"), F["bqty"]]), _ffill(X[:, names.index("NIFTY|FUT"), F["aqty"]])
    A["fut_bq5"], A["fut_aq5"] = (_ffill(X[:, names.index("NIFTY|FUT"), F[f]]) for f in ("bq5", "aq5"))
    A["fut_ttq"] = _ffill(X[:, names.index("NIFTY|FUT"), F["ttq"]])
    A["vix"] = px("INDIAVIX|SPOT") if "INDIAVIX|SPOT" in names else np.full(len(T), np.nan)
    A["bank"] = px("BANKNIFTY|FUT") if "BANKNIFTY|FUT" in names else np.full(len(T), np.nan)
    # heavyweights: stock futures mid (5-level depth) and stock ltp, with Nifty weights
    sj = [j for j, k in enumerate(kind) if k == "sfut"]
    A["sfut_w"] = np.array([wn[j] for j in sj])
    sb = _ffill(np.where(X[:, sj, F["bid"]] > 0, X[:, sj, F["bid"]], np.nan))
    sa = _ffill(np.where(X[:, sj, F["ask"]] > 0, X[:, sj, F["ask"]], np.nan))
    A["sfut_mid"] = (sb + sa) / 2
    A["sfut_imb"] = _ffill(X[:, sj, F["bq5"]]) / (_ffill(X[:, sj, F["bq5"]]) + _ffill(X[:, sj, F["aq5"]]) + 1e-9)
    # options: nearest weekly
    oj = [j for j, k in enumerate(kind) if k == "opt"]
    K = np.array([float(names[j][:-2]) for j in oj])
    R = np.array([names[j][-2:] for j in oj])
    A["K"], A["R"] = K, R
    ob = _ffill(np.where(X[:, oj, F["bid"]] > 0, X[:, oj, F["bid"]], np.nan))
    oa = _ffill(np.where(X[:, oj, F["ask"]] > 0, X[:, oj, F["ask"]], np.nan))
    A["obid"], A["oask"] = ob, oa
    A["omid"] = np.where(np.isfinite(ob) & np.isfinite(oa) & (oa >= ob), (ob + oa) / 2, np.nan)
    A["ottq"] = _ffill(X[:, oj, F["ttq"]])
    A["otbq"], A["otsq"] = _ffill(X[:, oj, F["tbq"]]), _ffill(X[:, oj, F["tsq"]])
    # parity forward from the two strikes nearest the futures mid
    fm = (fb + fa) / 2
    ks = np.unique(K)
    col = {(k, r): q for q, (k, r) in enumerate(zip(K, R))}
    fwd = np.full(len(T), np.nan)
    for i in range(len(T)):
        ref = fm[i] if np.isfinite(fm[i]) else A["spot"][i]
        if not np.isfinite(ref):
            continue
        near = ks[np.argsort(np.abs(ks - ref))[:2]]
        v = []
        for k in near:
            c, p = col.get((k, "CE")), col.get((k, "PE"))
            if c is not None and p is not None and np.isfinite(A["omid"][i, c]) and np.isfinite(A["omid"][i, p]):
                v.append(k + A["omid"][i, c] - A["omid"][i, p])
        if v and abs(np.mean(v) - ref) < 150:
            fwd[i] = np.mean(v)
    A["fwd"] = _ffill(fwd)
    A["col"] = col
    # nearest-ITM contract per second and side
    itm = np.full((len(T), 2), -1, int)
    for i in range(len(T)):
        f = A["fwd"][i]
        if not np.isfinite(f):
            continue
        below, above = ks[ks <= f], ks[ks >= f]
        if len(below):
            itm[i, 0] = col.get((below.max(), "CE"), -1)
        if len(above):
            itm[i, 1] = col.get((above.min(), "PE"), -1)
    A["itm"] = itm
    _A[day] = A
    return A


def outcomes(A):
    """Per second i and side s: entry at the ask of row i+LAG on contract itm[i, s]; then the bid path."""
    p = os.path.join(HERE, f"out_{A['day']}.npz")
    if os.path.exists(p):
        z = np.load(p)
        return {k: z[k] for k in z.files}
    N = len(A["T"])
    O = {k: np.full((N, 2), np.nan) for k in ("entry", "mfe", "mae", "t10", "t20", "tdn")}
    for h in HORIZ:
        O[f"r{h}"] = np.full((N, 2), np.nan)
    last = N - 1
    for s in range(2):
        for i in range(N - LAG - 30):
            j = A["itm"][i, s]
            if j < 0:
                continue
            e = A["oask"][i + LAG, j]
            if not np.isfinite(e) or e <= 0:
                continue
            seg = A["obid"][i + LAG + 1:min(i + LAG + 1 + H, last + 1), j] / e - 1.0
            if not len(seg):
                continue
            O["entry"][i, s] = e
            O["mfe"][i, s] = np.nanmax(seg)
            O["mae"][i, s] = np.nanmin(seg)
            for h in HORIZ:
                if h <= len(seg):
                    O[f"r{h}"][i, s] = seg[h - 1]
            for key, lvl in (("t10", 0.10), ("t20", 0.20)):
                w = np.nonzero(seg >= lvl)[0]
                O[key][i, s] = w[0] + 1 if len(w) else np.nan
            w = np.nonzero(seg <= -0.10)[0]
            O["tdn"][i, s] = w[0] + 1 if len(w) else np.nan
    up10 = np.isfinite(O["t10"]) & ~(O["tdn"] <= O["t10"])
    up20 = np.isfinite(O["t20"]) & ~(O["tdn"] <= O["t20"])
    O["win10"], O["win20"] = up10.astype(float), up20.astype(float)
    O["valid"] = np.isfinite(O["entry"]).astype(float)
    np.savez_compressed(p, **O)
    return O


def runner_events(A, O, gap=30):
    """One event per move: consecutive seconds (gaps <= `gap`) where +20 % came before -10 % within 15 min, per side.
    Returns a list of dict(side, start, end, best, mfe_best)."""
    ev = []
    for s in range(2):
        w = np.nonzero(O["win20"][:, s] > 0)[0]
        if not len(w):
            continue
        st = prev = w[0]
        for i in list(w[1:]) + [None]:
            if i is not None and i - prev <= gap:
                prev = i
                continue
            seg = np.arange(st, prev + 1)
            best = seg[np.nanargmax(O["mfe"][seg, s])]
            ev.append({"side": s, "start": int(st), "end": int(prev), "best": int(best),
                       "mfe_best": float(O["mfe"][best, s]), "secs": int(len(seg))})
            if i is not None:
                st = prev = i
    return ev


def onsets(A, pts=8.0, win=60, quiet=300):
    """Candidate 'a move is starting' moments: the forward moved >= pts in `win` seconds in one direction, and no
    candidate in that direction in the previous `quiet` seconds. Returns arrays (rows, side) with side 0 = up (CE),
    1 = down (PE). Purely causal: decided at row i from rows <= i."""
    f = A["fwd"]
    rows, sides = [], []
    last = {0: -10 ** 9, 1: -10 ** 9}
    for i in range(win, len(f) - LAG - 31):
        if not (np.isfinite(f[i]) and np.isfinite(f[i - win])):
            continue
        d = f[i] - f[i - win]
        for s, ok in ((0, d >= pts), (1, d <= -pts)):
            if ok and i - last[s] > quiet:
                rows.append(i)
                sides.append(s)
                last[s] = i
    return np.array(rows, int), np.array(sides, int)


# ------------------------------------------------------------------ features (rows <= i only)
def _ret(x, i, w):
    a = x[i - w] if i - w >= 0 else np.nan
    return x[i] - a


def _ofi(A, i, w):
    """Cont-Kukanov-Stoikov order-flow imbalance on the Nifty future's best level over the last w seconds."""
    b, a, qb, qa = A["fut_bid"], A["fut_ask"], A["fut_bq"], A["fut_aq"]
    e = 0.0
    for t in range(max(i - w + 1, 1), i + 1):
        if not (np.isfinite(b[t]) and np.isfinite(b[t - 1]) and np.isfinite(a[t]) and np.isfinite(a[t - 1])):
            continue
        eb = (qb[t] if b[t] >= b[t - 1] else 0.0) - (qb[t - 1] if b[t] <= b[t - 1] else 0.0)
        ea = (qa[t] if a[t] <= a[t - 1] else 0.0) - (qa[t - 1] if a[t] >= a[t - 1] else 0.0)
        e += eb - ea
    return e


def _iv(A, i, j):
    """Implied vol (vol pts) of option column j at row i from its mid, on the parity forward."""
    import sys
    sys.path.insert(0, r"D:\ApexOptions")
    from apex import greeks
    from datetime import datetime, timezone, timedelta
    mid, F = A["omid"][i, j], A["fwd"][i]
    if not (np.isfinite(mid) and np.isfinite(F)):
        return np.nan
    IST = timezone(timedelta(hours=5, minutes=30))
    y, m, d = (int(x) for x in A["expiry"].split("-"))
    T = max(datetime(y, m, d, 15, 30, tzinfo=IST).timestamp() - A["T"][i], 600.0) / (365.0 * 86400)
    v = greeks.implied_vol(np.array([mid]), F, np.array([A["K"][j]]), T, np.array([A["R"][j] == "CE"]))[0]
    return float(v * 100) if np.isfinite(v) else np.nan


def _hw(A, i, w):
    """Nifty-weighted return (pts of Nifty equivalent) of the heavyweight futures over w seconds."""
    m = A["sfut_mid"]
    if i - w < 0:
        return np.nan
    r = m[i] / m[i - w] - 1.0
    ok = np.isfinite(r)
    if not ok.any():
        return np.nan
    return float(np.sum(A["sfut_w"][ok] * r[ok]) / 100.0 * A["fwd"][i])


def features(A, rows, sides):
    """Feature table (dict of arrays) at the given rows, for the given sides (direction-signed: + favours the side)."""
    f, hm = A["fwd"], A["hm"]
    out = {}
    def put(k, v):
        out.setdefault(k, []).append(v)
    day_hi = np.fmax.accumulate(np.where(np.isfinite(f), f, -np.inf))
    day_lo = np.fmin.accumulate(np.where(np.isfinite(f), f, np.inf))
    for i, s in zip(rows, sides):
        sg = 1.0 if s == 0 else -1.0
        j = A["itm"][i, s]
        # forward path: returns, velocity, acceleration (direction-signed)
        for w in (5, 10, 30, 60, 120, 300):
            put(f"fwd_r{w}", sg * _ret(f, i, w))
        put("fwd_acc30", sg * ((_ret(f, i, 15)) - (f[i - 15] - f[i - 30] if i >= 30 else np.nan)))
        put("fwd_acc60", sg * ((_ret(f, i, 30)) - (f[i - 30] - f[i - 60] if i >= 60 else np.nan)))
        seg = f[max(0, i - 300):i + 1]
        seg = seg[np.isfinite(seg)]
        dd = np.abs(np.diff(seg)).sum() if len(seg) > 2 else np.nan
        put("eff300", abs(seg[-1] - seg[0]) / dd if len(seg) > 2 and dd > 0 else np.nan)
        put("rv300", float(np.sqrt(np.mean(np.diff(seg) ** 2))) if len(seg) > 2 else np.nan)
        put("pos_in_day", sg * ((f[i] - day_lo[i]) / (day_hi[i] - day_lo[i]) - 0.5) if day_hi[i] > day_lo[i] else np.nan)
        put("to_extreme", (day_hi[i] - f[i]) if s == 0 else (f[i] - day_lo[i]))
        put("day_range", day_hi[i] - day_lo[i])
        # futures order flow and its derivative
        o10, o30, o60 = _ofi(A, i, 10), _ofi(A, i, 30), _ofi(A, i, 60)
        put("ofi10", sg * o10)
        put("ofi30", sg * o30)
        put("ofi60", sg * o60)
        put("dofi", sg * (o10 - _ofi(A, i - 10, 10)) if i >= 20 else np.nan)
        bq, aq = A["fut_bq5"][i], A["fut_aq5"][i]
        imb = bq / (bq + aq) if bq + aq > 0 else np.nan
        bq0, aq0 = A["fut_bq5"][i - 30], A["fut_aq5"][i - 30]
        imb0 = bq0 / (bq0 + aq0) if bq0 + aq0 > 0 else np.nan
        put("depth_imb", sg * (imb - 0.5))
        put("d_depth_imb", sg * (imb - imb0))
        v = A["fut_ttq"]
        put("fut_vol60", v[i] - v[i - 60] if i >= 60 else np.nan)
        put("fut_vol_acc", (v[i] - v[i - 30]) - (v[i - 30] - v[i - 60]) if i >= 60 else np.nan)
        # heavyweights: weighted move, breadth, lead over the index, book imbalance
        h30, h60 = _hw(A, i, 30), _hw(A, i, 60)
        put("hw_r30", sg * h30)
        put("hw_r60", sg * h60)
        put("hw_minus_idx30", sg * (h30 - _ret(f, i, 30)) if np.isfinite(h30) else np.nan)
        hlag = _hw(A, i - 30, 30) if i >= 60 else np.nan
        put("hw_lead", sg * (hlag - (f[i - 30] - f[i - 60])) if i >= 60 and np.isfinite(hlag) else np.nan)
        m = A["sfut_mid"]
        r30 = m[i] / m[i - 30] - 1 if i >= 30 else np.full(m.shape[1], np.nan)
        ok = np.isfinite(r30)
        put("hw_breadth", float(np.mean(np.sign(r30[ok]) == sg)) if ok.any() else np.nan)
        wimb = A["sfut_imb"][i]
        okw = np.isfinite(wimb)
        put("hw_book_imb", sg * (float(np.sum(A["sfut_w"][okw] * (wimb[okw] - 0.5)) / max(A["sfut_w"][okw].sum(), 1e-9))) if okw.any() else np.nan)
        # path ordering: signed Levy area between the heavyweight and index paths over 60 s (+ = heavyweights led)
        if i >= 60:
            fi = f[i - 60:i + 1] - f[i - 60]
            hi = np.array([_hw(A, t, t - (i - 60)) if t > i - 60 else 0.0 for t in range(i - 60, i + 1, 5)])
            fi5 = fi[::5]
            if np.all(np.isfinite(hi)) and np.all(np.isfinite(fi5)) and len(hi) == len(fi5):
                sx, sy = hi / (np.abs(hi).max() + 1e-9), fi5 / (np.abs(fi5).max() + 1e-9)
                put("levy_hw_idx", float(0.5 * np.sum(sx[:-1] * np.diff(sy) - sy[:-1] * np.diff(sx))))
            else:
                put("levy_hw_idx", np.nan)
        else:
            put("levy_hw_idx", np.nan)
        # the option itself: premium response, spread, volume, book, time
        if j >= 0:
            mid = A["omid"][:, j]
            put("spread_pct", (A["oask"][i, j] - A["obid"][i, j]) / A["oask"][i, j] if A["oask"][i, j] > 0 else np.nan)
            put("prem_r30", mid[i] / mid[i - 30] - 1 if i >= 30 and mid[i - 30] > 0 else np.nan)
            put("prem_r60", mid[i] / mid[i - 60] - 1 if i >= 60 and mid[i - 60] > 0 else np.nan)
            # premium lag: option move vs a 0.55-delta move of the forward over 60 s, as a share of premium
            put("prem_lag60", ((mid[i] - mid[i - 60]) - 0.55 * sg * (f[i] - f[i - 60])) / mid[i] if i >= 60 and mid[i] > 0 else np.nan)
            tt = A["ottq"][:, j]
            put("opt_vol60", tt[i] - tt[i - 60] if i >= 60 else np.nan)
            put("opt_vol_acc", (tt[i] - tt[i - 30]) - (tt[i - 30] - tt[i - 60]) if i >= 60 else np.nan)
            b_, s_ = A["otbq"][i, j], A["otsq"][i, j]
            put("opt_book", (b_ - s_) / (b_ + s_) if b_ + s_ > 0 else np.nan)
            put("premium", A["oask"][i, j])
        else:
            for k in ("spread_pct", "prem_r30", "prem_r60", "prem_lag60", "opt_vol60", "opt_vol_acc", "opt_book", "premium"):
                put(k, np.nan)
        # implied volatility of the bought option now and 60 s ago (Black-76 on the parity forward, r = 0)
        if j >= 0 and i >= 60:
            ivn, ivp = _iv(A, i, j), _iv(A, i - 60, j)
            put("iv", ivn)
            put("d_iv60", ivn - ivp)
            mv = abs(f[i] - f[i - 60])
            put("iv_per_pt", (ivn - ivp) / mv if mv > 1 else np.nan)       # IV response per point moved
        else:
            put("iv", np.nan)
            put("d_iv60", np.nan)
            put("iv_per_pt", np.nan)
        put("hm", hm[i])
        put("vix", A["vix"][i])
        put("dvix300", A["vix"][i] - A["vix"][i - 300] if i >= 300 else np.nan)
        put("bank_r60", sg * (A["bank"][i] - A["bank"][i - 60]) if i >= 60 else np.nan)
        put("dte0", float(A["dte0"]))
    return {k: np.array(v, float) for k, v in out.items()}
