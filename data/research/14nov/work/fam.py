"""Entry families for fastlab. Every generator returns [(row, side, tag)] and reads rows <= row only."""
import numpy as np
from apex import fastlab as FL
N = FL.N


def _em(X, W):
    return X["em15"] * np.sqrt(W / 900.0)


def sig_pb(D, X, W=1200, vmin=40.0, vz=None, pb=0.5, dmax=0.75, amax=900, rs=5.0, trend=None):
    """impulse (new W-s extreme with a move of vmin pts, or vz x the implied W-s move) -> pullback pb..dmax of the
    impulse within amax s -> buy a resumption of rs pts. W=1200, vmin=40, pb=0.5 is the champion's normal-day entry.
    trend=(L, er): only in the direction of the L-s move when its efficiency is at least er."""
    fs = D["fs"]; hi, lo, mom = X[f"hi{W}"], X[f"lo{W}"], X[f"mom{W}"]
    em = _em(X, W)
    out = []; arm = None
    for i in range(max(W // 2, 300), N):
        f = fs[i]
        if f != f or mom[i] != mom[i]:
            continue
        thr = vmin if vz is None else max(8.0, vz * em[i])
        if thr != thr:
            continue
        v = mom[i]
        side = "CE" if (f > hi[i] and v >= thr) else ("PE" if (f < lo[i] and -v >= thr) else None)
        if side:
            if arm is None or arm[0] != side:
                arm = [side, fs[i - W] if i >= W else f - v, f, f, i]
            else:
                arm[2] = max(arm[2], f) if side == "CE" else min(arm[2], f)
                arm[3] = arm[2]
        elif arm is not None:
            if i - arm[4] > amax:
                arm = None
                continue
            up = arm[0] == "CE"
            arm[2] = max(arm[2], f) if up else min(arm[2], f)
            arm[3] = min(arm[3], f) if up else max(arm[3], f)
            imp = abs(arm[2] - arm[1]); ret = (arm[2] - arm[3]) if up else (arm[3] - arm[2])
            if imp > 0 and ret >= pb * imp:
                if ret > dmax * imp:
                    arm = None
                elif ((f - arm[3]) if up else (arm[3] - f)) >= rs:
                    ok = True
                    if trend is not None:
                        L, e = trend
                        m = X[f"mom{L}"][i]; er = X[f"er{L}"][i]
                        ok = (m == m) and (er == er) and er >= e and ((m > 0) == up)
                    if ok:
                        out.append((i, arm[0], "pb"))
                    arm = None
    return out


def sig_flag(D, X, W=1200, vmin=40.0, vz=None, lo_=0.15, pb=0.5, er=0.4, amax=900):
    """efficient impulse, shallow pause (lo_..pb of the impulse), then a NEW extreme: buy the continuation."""
    fs = D["fs"]; hi, lo, mom, ef = X[f"hi{W}"], X[f"lo{W}"], X[f"mom{W}"], X[f"er{W if W in (300, 1200, 3600) else 1200}"]
    em = _em(X, W)
    out = []; fl = None
    for i in range(max(W // 2, 300), N):
        f = fs[i]
        if f != f or mom[i] != mom[i]:
            continue
        thr = vmin if vz is None else max(8.0, vz * em[i])
        v = mom[i]
        side = "CE" if (f > hi[i] and v >= thr) else ("PE" if (f < lo[i] and -v >= thr) else None)
        if side:
            if fl is None or fl[0] != side:
                fl = [side, fs[i - W] if i >= W else f - v, f, f, i]
            else:
                up = side == "CE"
                imp = abs(fl[2] - fl[1]); ret = (fl[2] - fl[3]) if up else (fl[3] - fl[2])
                if imp > 0 and lo_ * imp <= ret < pb * imp and i - fl[4] <= amax and ((f > fl[2]) if up else (f < fl[2])) and ef[i] >= er:
                    out.append((i, side, "flag"))
                fl[2] = max(fl[2], f) if up else min(fl[2], f)
                fl[3] = fl[2]
        elif fl is not None:
            if i - fl[4] > amax:
                fl = None
            else:
                up = fl[0] == "CE"
                fl[3] = min(fl[3], f) if up else max(fl[3], f)
                imp = abs(fl[2] - fl[1]); ret = (fl[2] - fl[3]) if up else (fl[3] - fl[2])
                if imp > 0 and ret >= pb * imp:
                    fl = None
    return out


def _edges(mask_up, mask_dn, gap):
    """first row of each stretch, at most one signal per gap seconds per side."""
    out = []; last = {1: -10 ** 9, -1: -10 ** 9}
    for sg, m in ((1, mask_up), (-1, mask_dn)):
        w = np.flatnonzero(m & ~np.r_[False, m[:-1]])
        for i in w:
            if i - last[sg] >= gap:
                out.append((int(i), "CE" if sg > 0 else "PE", ""))
                last[sg] = i
    return sorted(out)


def _confirm(X, W, kind):
    """heavyweight / sister confirmation masks for an up move and a down move over W s."""
    L = {300: 300, 600: 300, 1200: 1200, 3600: 1200}[W]
    hw, brd, mom = X[f"hw{L}"], X[f"brd{L}"], X[f"mom{L}"]
    up = np.ones(N, bool); dn = np.ones(N, bool)
    if "hw" in kind:
        up &= (hw >= 0.7 * mom) & (brd >= 0.5); dn &= (hw <= 0.7 * mom) & (brd <= -0.5)
    if "sis" in kind:
        up &= (X["bn300"] > 0) & (X["fin300"] > 0); dn &= (X["bn300"] < 0) & (X["fin300"] < 0)
    if "nohw" in kind:                                   # the index moved without its heavyweights
        up = (hw < 0.4 * mom) | (brd < 0.2); dn = (hw > 0.4 * mom) | (brd > -0.2)
    return up, dn


def sig_brk(D, X, W=1200, vmin=40.0, vz=None, confirm="", gap=900):
    """buy the breakout itself: new W-s extreme with the move, no pullback wanted."""
    fs = D["fs"]; hi, lo, mom = X[f"hi{W}"], X[f"lo{W}"], X[f"mom{W}"]
    thr = np.full(N, vmin) if vz is None else np.maximum(8.0, vz * _em(X, W))
    cu, cd = _confirm(X, W, confirm) if confirm else (np.ones(N, bool), np.ones(N, bool))
    with np.errstate(invalid="ignore"):
        up = (fs > hi) & (mom >= thr) & cu
        dn = (fs < lo) & (-mom >= thr) & cd
    return _edges(up, dn, gap)


def sig_dayx(D, X, age=900, buf=0.0, gap=900, t_from=1800):
    """a new day high / low after the old one stood for at least age seconds."""
    fs = D["fs"]
    out = []; hi = lo = None; thi = tlo = 0; last = {"CE": -10 ** 9, "PE": -10 ** 9}
    for i in range(60, N):
        f = fs[i]
        if f != f:
            continue
        if hi is None:
            hi = lo = f; thi = tlo = i
            continue
        if f > hi + buf:
            if i - thi >= age and i >= t_from and i - last["CE"] >= gap:
                out.append((i, "CE", "dayx")); last["CE"] = i
        if f > hi:
            hi = f; thi = i
        if f < lo - buf:
            if i - tlo >= age and i >= t_from and i - last["PE"] >= gap:
                out.append((i, "PE", "dayx")); last["PE"] = i
        if f < lo:
            lo = f; tlo = i
    return out


def sig_sqz(D, X, W=1200, tight=1.0, buf=3.0, gap=900):
    """a tight range (W-s range <= tight x the implied W-s move) breaks."""
    fs = D["fs"]; hi, lo, rng = X[f"hi{W}"], X[f"lo{W}"], X[f"rng{W}"]
    em = _em(X, W)
    with np.errstate(invalid="ignore"):
        t = rng <= tight * em
        return _edges(t & (fs > hi + buf), t & (fs < lo - buf), gap)


def sig_hw(D, X, L=60, pts=10.0, brd=0.6, lead=None, gap=600):
    """heavyweight thrust: the weighted basket moved pts Nifty points in L s with breadth; lead = the index itself
    has moved less than lead x that so far."""
    hw, b, nf = X[f"hw{L}"], X[f"brd{L}"], X[f"nf{L}"]
    with np.errstate(invalid="ignore"):
        up = (hw >= pts) & (b >= brd); dn = (hw <= -pts) & (b <= -brd)
        if lead is not None:
            up &= nf <= lead * hw; dn &= nf >= lead * hw
    return _edges(up, dn, gap)


def sig_sis(D, X, L=60, pts=10.0, lead=None, gap=600):
    """sister thrust: BANKNIFTY futures and the FINNIFTY index both moved pts Nifty-equivalent points in L s."""
    bn, fn, nf = X[f"bn{L}"], X[f"fin{L}"], X[f"nf{L}"]
    with np.errstate(invalid="ignore"):
        up = (bn >= pts) & (fn >= pts); dn = (bn <= -pts) & (fn <= -pts)
        if lead is not None:
            up &= nf <= lead * 0.5 * (bn + fn); dn &= nf >= lead * 0.5 * (bn + fn)
    return _edges(up, dn, gap)


def sig_all3(D, X, L=60, pts=8.0, gap=600):
    """everything agrees: heavyweights, both sisters and the future all moved pts in L s."""
    with np.errstate(invalid="ignore"):
        up = (X[f"hw{L}"] >= pts) & (X[f"bn{L}"] >= pts) & (X[f"fin{L}"] >= pts) & (X[f"nf{L}"] >= pts)
        dn = (X[f"hw{L}"] <= -pts) & (X[f"bn{L}"] <= -pts) & (X[f"fin{L}"] <= -pts) & (X[f"nf{L}"] <= -pts)
    return _edges(up, dn, gap)


def sig_vwap(D, X, buf=3.0, m=10.0, gap=900):
    """the future crosses its VWAP by buf pts with the 5-minute move behind it."""
    v, mom = X["vwap_d"], X["mom300"]
    with np.errstate(invalid="ignore"):
        up = (v >= buf) & (mom >= m); dn = (v <= -buf) & (mom <= -m)
        was_dn = np.r_[False, v[:-1] < buf]; was_up = np.r_[False, v[:-1] > -buf]
    # a cross, not a state: the previous 300 s were on the other side at some point
    import pandas as pd
    below = pd.Series((v < 0).astype(float)).rolling(300, min_periods=60).max().to_numpy() > 0
    above = pd.Series((v > 0).astype(float)).rolling(300, min_periods=60).max().to_numpy() > 0
    return _edges(up & below, dn & above, gap)


def sig_catch(D, X, g=15.0, L=300, gap=900):
    """catch-up: the heavyweight basket is g Nifty points ahead of the index over L s."""
    gp = X[f"hw_gap{L}"]; hw = X[f"hw{L}"]
    with np.errstate(invalid="ignore"):
        return _edges((gp >= g) & (hw > 0), (gp <= -g) & (hw < 0), gap)


# ── added exit rules (the extra hook of fastlab.exit_ladder) ────────────────────────────────────────────────────────
def stall(after=900, pk=0.08, band=0.04):
    """the trade has gone nowhere: after `after` s the peak gain is under pk and the bid is within +-band of entry."""
    def f(c):
        k = np.arange(c["L"])
        r = c["b"] / c["e"] - 1.0
        return ("STALL", (k >= after) & (c["g"] < pk) & (np.abs(r) < band))
    return f


def sprt(m=30.0, tmin=300, bar=-1.5):
    """sequential test of 'the move continues at m forward points per 15 minutes' against 'no drift': exit when the
    evidence for no drift is strong. x = forward gain in the trade's direction, sigma from the hold itself."""
    def f(c):
        L = c["L"]
        k = np.arange(1, L + 1).astype(float)
        x = c["f"] - c["sg"] * c["D"]["fs"][c["i"]]
        d = np.diff(c["f"], prepend=c["f"][0])
        var = np.maximum(np.cumsum(d * d) / k, 1e-4)                 # per-second variance so far
        mu = m / 900.0
        llr = (mu / var) * (x - 0.5 * mu * k)
        return ("SPRT", (k >= tmin) & (llr <= bar * 1.0) & (c["g"] < 0.15))
    return f
