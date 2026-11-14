"""h4: the four-year set in memory (984 sessions of 1-minute Nifty futures, sessions to expiry, a model option whose
IV is the 20-session realised volatility x the factor fitted on the real-option sessions) and the entry families."""
import os, sys, pickle, time
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import numpy as np, pandas as pd
from apex import fastlab as FL
import lab1
NB = lab1.NB
PKL = os.path.join(lab1.W, "h4.pkl")
KIV = {0: 1.32, 1: 1.27, 2: 1.22}              # real ATM IV / 20-session realised volatility (fitted on 145 sessions)
SPLIT = "2025-01-01"                           # found before, judged from


def build():
    days = lab1.sessions()
    exp = lab1.expiry_map(days); dte = lab1.dte_map(days, exp)
    fut = lab1._tab("fut"); spot = lab1._tab("spot")
    FG = {d: g for d, g in fut.groupby("day")}; SG = {d: g for d, g in spot.groupby("day")}
    grid_t = pd.date_range("2000-01-01 09:15:00", periods=NB, freq="1min").strftime("%H:%M:%S")
    ALL = []; closes = []
    for d in days:
        g = FG[d].drop_duplicates("ts"); g = g.set_index(g.ts.str[11:]).reindex(grid_t)
        c = g.c.ffill().bfill().to_numpy(float)
        f = lambda col: np.where(np.isfinite(g[col].to_numpy(float)), g[col].to_numpy(float), c)
        basis = 0.0
        if d in SG:
            s = SG[d].drop_duplicates("ts"); s = s.set_index(s.ts.str[11:]).c.reindex(grid_t).ffill().bfill().to_numpy(float)
            if np.isfinite(s).any():
                basis = float(np.nanmedian(c - s))
        secs = (pd.Timestamp(exp[d] + " 15:30:00") - pd.date_range(d + " 09:15:00", periods=NB, freq="1min")).total_seconds().to_numpy()
        ALL.append(dict(day=d, o=f("o"), h=f("h"), l=f("l"), c=c, v=g.v.fillna(0).to_numpy(float), expiry=exp[d], dte=dte[d], dte0=(dte[d] == 0), vix=None, opt=None,
                        basis=basis, T=np.maximum(secs - 60.0, 60.0) / FL.YEAR_S))
        closes.append(c[-1] - basis)
    closes = np.array(closes)
    lr = np.diff(np.log(closes), prepend=np.nan)
    rv = pd.Series(lr).rolling(20, min_periods=10).std().shift(1).to_numpy() * np.sqrt(252)
    for i, D in enumerate(ALL):
        D["rv20"] = float(rv[i]) if np.isfinite(rv[i]) else None
        D["vix"] = 100.0 * max(0.06, rv[i] * KIV[min(D["dte"], 2)]) if np.isfinite(rv[i]) else None
        P = ALL[i - 1] if i else None
        D["pc"] = float(P["c"][-1]) if P else None; D["ph"] = float(P["h"].max()) if P else None; D["pl"] = float(P["l"].min()) if P else None
        D["em"] = (D["c"][0] * D["rv20"] / np.sqrt(252)) if D["rv20"] else None        # one-sigma day move in points
        D["prng"] = (D["ph"] - D["pl"]) if P else None
    pickle.dump(ALL, open(PKL, "wb"))
    return len(ALL)


def load():
    lab1.IVK = {0: 1.0, 1: 1.0}; lab1.IVK_FAR = 1.0
    return [lab1.Day(d) for d in pickle.load(open(PKL, "rb")) if d["vix"] is not None]


# ── entries (decision at the close of bar b; everything read is at or before b) ─────────────────────────────────────
def _roll(x, n, fn):
    s = pd.Series(x).shift(1).rolling(n, min_periods=max(2, n // 2))
    return (s.max() if fn == "max" else s.min()).to_numpy()


def _dedupe(ev, gap):
    out = []; last = {"CE": -999, "PE": -999}
    for b, s, t in sorted(ev):
        if b - last[s] >= gap:
            out.append((b, s, t)); last[s] = b
    return out


def _mask(up, dn, gap, lo=5, hi=345):
    ev = [(int(b), "CE", "") for b in np.flatnonzero(up) if lo <= b < hi] + [(int(b), "PE", "") for b in np.flatnonzero(dn) if lo <= b < hi]
    return _dedupe(ev, gap)


def fam(D, name, **p):
    c, h, l, o, v = D["c"], D["h"], D["l"], D["o"], D["v"]
    em = D["em"]; k = c[0] / 25000.0
    if name == "pb":
        W = p.get("W", 20)
        return lab1.sig_pb_hl(D, W=W, vmin=p.get("v", 40.0) * np.sqrt(W / 20.0), pb=p.get("pb", 0.5), amax=max(8, int(0.75 * W)), scale=25000.0)
    if name == "brk":                                   # a new W-bar extreme with a move of z x the day's sigma x sqrt(W/375)
        W = p["W"]; z = p.get("z", 1.0)
        thr = z * em * np.sqrt(W / 375.0)
        m = np.r_[np.full(W, np.nan), c[W:] - c[:-W]]
        with np.errstate(invalid="ignore"):
            return _mask((c > _roll(h, W, "max")) & (m >= thr), (c < _roll(l, W, "min")) & (m <= -thr), p.get("gap", W))
    if name == "dayx":
        age = p.get("age", 30); out = []; hi_ = h[0]; lo_ = l[0]; thi = tlo = 0
        for b in range(1, 345):
            if c[b] > hi_ and b - thi >= age and b >= p.get("t0", 30): out.append((b, "CE", ""))
            if c[b] < lo_ and b - tlo >= age and b >= p.get("t0", 30): out.append((b, "PE", ""))
            if h[b] > hi_: hi_ = h[b]; thi = b
            if l[b] < lo_: lo_ = l[b]; tlo = b
        return _dedupe(out, p.get("gap", 30))
    if name == "orb":
        n = p["n"]; hi_, lo_ = h[:n].max(), l[:n].min(); buf = p.get("buf", 0.0) * k
        for b in range(n, p.get("until", 150)):
            if c[b] > hi_ + buf: return [(b, "CE" if not p.get("fade") else "PE", "")]
            if c[b] < lo_ - buf: return [(b, "PE" if not p.get("fade") else "CE", "")]
        return []
    if name == "gap":
        if D["pc"] is None: return []
        g = o[0] - D["pc"]; z = p.get("z", 0.3)
        if abs(g) < z * em: return []
        s = ("CE" if g > 0 else "PE") if p.get("go", True) else ("PE" if g > 0 else "CE")
        return [(p.get("b", 5), s, "")]
    if name == "trend_at":                              # the move since the open at bar b, if at least z sigma-fractions: go with it (or fade)
        b = p["b"]; m = c[b] - o[0]
        if abs(m) < p.get("z", 0.3) * em: return []
        s = "CE" if m > 0 else "PE"
        if p.get("fade"): s = "PE" if s == "CE" else "CE"
        return [(b, s, "")]
    if name == "vwap":
        cv = np.cumsum(v); vw = np.cumsum((h + l + c) / 3 * v) / np.where(cv > 0, cv, np.nan)
        d = c - vw; pd_ = np.r_[np.nan, d[:-1]]
        m = np.r_[np.full(15, np.nan), c[15:] - c[:-15]]
        with np.errstate(invalid="ignore"):
            if p.get("revert"):                          # stretched from VWAP by z sigma-fractions: buy back toward it
                z = p.get("z", 0.5) * em
                return _mask(d <= -z, d >= z, p.get("gap", 60), lo=30)
            return _mask((d > 0) & (pd_ <= 0) & (m > 0), (d < 0) & (pd_ >= 0) & (m < 0), p.get("gap", 30), lo=30)
    if name == "squeeze":
        W = p.get("W", 30); q = p.get("q", 0.15)
        rng = _roll(h, W, "max") - _roll(l, W, "min")
        with np.errstate(invalid="ignore"):
            t = rng <= q * em
            return _mask(t & (c > _roll(h, W, "max")), t & (c < _roll(l, W, "min")), p.get("gap", W), lo=W + 5)
    if name == "fade":                                  # a stretched W-bar move: buy the other side
        W = p.get("W", 20); z = p.get("z", 0.5)
        m = np.r_[np.full(W, np.nan), c[W:] - c[:-W]]
        thr = z * em
        with np.errstate(invalid="ignore"):
            return _mask(m <= -thr, m >= thr, p.get("gap", W), lo=W)
    if name == "volbrk":                                # a 1-minute bar with volume x times the day's average so far, in its direction
        cv = np.cumsum(v); avg = cv / (np.arange(NB) + 1)
        body = c - o
        with np.errstate(invalid="ignore"):
            big = v >= p.get("x", 4.0) * np.r_[np.nan, avg[:-1]]
            return _mask(big & (body >= p.get("pts", 8.0) * k), big & (body <= -p.get("pts", 8.0) * k), p.get("gap", 15), lo=15)
    if name == "pdx":                                   # the previous day's high / low is taken out
        if D["ph"] is None: return []
        ph, pl = D["ph"], D["pl"]
        up = (c > ph) & (np.r_[c[0], c[:-1]] <= ph); dn = (c < pl) & (np.r_[c[0], c[:-1]] >= pl)
        if p.get("fade"): up, dn = dn, up
        return _mask(up, dn, 60, lo=p.get("lo", 5))[:2]
    if name == "nr":                                    # after a narrow day (range <= q sigma), buy the first 30-minute range break
        if D["prng"] is None or D["prng"] > p.get("q", 0.8) * em: return []
        return fam(D, "orb", n=30)
    if name == "wide":                                  # after a wide day, fade the first 30-minute range break
        if D["prng"] is None or D["prng"] < p.get("q", 1.6) * em: return []
        return fam(D, "orb", n=30, fade=p.get("fade", True))
    if name == "blind":                                 # both sides at fixed bars: the cost of doing nothing clever
        return [(b, s, "") for b in p["bars"] for s in ("CE", "PE")]
    if name == "ema":                                   # 9 / 21-bar EMA cross with the 60-bar slope
        e1 = pd.Series(c).ewm(span=p.get("a", 9), adjust=False).mean().to_numpy(); e2 = pd.Series(c).ewm(span=p.get("b", 21), adjust=False).mean().to_numpy()
        d = e1 - e2; pd_ = np.r_[np.nan, d[:-1]]
        sl = np.r_[np.full(60, np.nan), e2[60:] - e2[:-60]]
        with np.errstate(invalid="ignore"):
            return _mask((d > 0) & (pd_ <= 0) & (sl > 0), (d < 0) & (pd_ >= 0) & (sl < 0), 20, lo=65)
    if name == "lastx":                                 # a new day extreme late in the session
        b0 = p.get("b0", 255); hi_ = h[:b0].max(); lo_ = l[:b0].min()
        for b in range(b0, 340):
            if c[b] > hi_: return [(b, "CE" if not p.get("fade") else "PE", "")]
            if c[b] < lo_: return [(b, "PE" if not p.get("fade") else "CE", "")]
        return []
    raise KeyError(name)
