"""lab1s: the champion's per-second pattern on broker 1-second futures (data/research/hist1s/), with a model option.

A session = the future's last trade each second (forward-filled), minus the day's futures-spot basis (the parity
forward's stand-in), smoothed as the champion does (EMA 5 s). Entries: fam.sig_pb (normal days) and the expiry
breakout, exactly as on the recorded sessions. Exits: fastlab.exit_ladder on a model option (Black-76; IV = the
20-session realised volatility x the factor fitted on the real-option sessions; bid/ask = the model price -+ half the
recorded median spread). The same model run on the RECORDED sessions' own forward says how far to trust it."""
import os, sys, json, pickle
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import numpy as np, pandas as pd
from apex import fastlab as FL
import fam, hist1s, h4
N = FL.N
HALF = 0.0011
_META = None


def meta():
    """per session: expiry, sessions to expiry, basis, model IV (from the four-year set)."""
    global _META
    if _META is None:
        _META = {d["day"]: d for d in pickle.load(open(h4.PKL, "rb"))}
    return _META


def session(day, fwd=None):
    """a fastlab-style day from the broker's 1-second future (or from a forward you pass), or None."""
    m = meta().get(day)
    if m is None or m["vix"] is None:
        return None
    if fwd is None:
        p = os.path.join(hist1s.OUT, f"fut_{json.load(open(os.path.join(hist1s.OUT, 'fut_expiry.json')))[day]}_x_0_{day}.parquet")
        if not os.path.exists(p):
            return None
        df = pd.read_parquet(p)
        if len(df) < 3000:
            return None
        fwd = hist1s.grid(df, day) - m["basis"]
    D = FL.Day(day=day, expiry=m["expiry"], dte0=bool(m["dte0"]), dte=int(m["dte"]), fwd=fwd, fs=FL.ema(fwd, 5.0), iv=float(m["vix"]) / 100.0)
    import datetime as dt
    y, mo, d_ = (int(x) for x in m["expiry"].split("-"))
    t_open = (dt.datetime.fromisoformat(day + "T09:15:00") - dt.datetime(1970, 1, 1)).total_seconds()
    D["T"] = np.maximum((dt.datetime(y, mo, d_, 15, 30) - dt.datetime(1970, 1, 1)).total_seconds() - (t_open + np.arange(N)), 60.0) / FL.YEAR_S
    D["P"] = FL.EXP if D["dte0"] else FL.NORM
    return D


def feats(D):
    fs = D["fs"]
    X = {"em15": np.full(N, np.nan), "gap": np.zeros(N)}
    for W in (600, 1200):
        X[f"hi{W}"], X[f"lo{W}"] = FL.roll_ext(fs, W)
        X[f"mom{W}"] = FL.lagdiff(fs, W)
    X["mom150"] = FL.lagdiff(fs, 150)
    return X


def sig_exp(D, X, W=600, L=150, vmin=20.0, gap=60):
    """the champion's expiry-day entry: a new W-s extreme of the smoothed forward with vmin points in L s."""
    fs = D["fs"]
    with np.errstate(invalid="ignore"):
        up = (fs > X[f"hi{W}"]) & (X[f"mom{L}"] >= vmin); dn = (fs < X[f"lo{W}"]) & (-X[f"mom{L}"] >= vmin)
    return fam._edges(up, dn, gap)


def trade(D, i, side):
    """model option for this entry: the strike just in the money (delta target 0.52 normal, 0.65 expiry)."""
    F = D["fwd"][i]
    if not np.isfinite(F):
        return None
    call = side == "CE"
    Ks = (np.floor(F / 50.0) * 50.0 + 50.0 * np.arange(-4, 5)).astype(float)
    dl, _, _ = FL.greeks(F, Ks, D["T"][i], D["iv"], call)
    ad = np.abs(dl); ok = ad >= 0.52
    if not ok.any():
        return None
    K = float(Ks[int(np.argmin(np.where(ok, np.abs(ad - D["P"]["dt"]), 9.0)))])
    with np.errstate(all="ignore"):
        px = FL.b76(FL._ffill0(D["fwd"]), K, D["T"], D["iv"], call)
    opt = np.full((N, 1, 2, 2), np.nan, np.float32)
    c = 0 if call else 1
    opt[:, 0, c, 0] = px * (1 - HALF); opt[:, 0, c, 1] = px * (1 + HALF)
    Dm = FL.Day(dict(D)); Dm["opt"] = opt; Dm["K"] = np.array([K])
    return FL.exit_ladder(Dm, i, side, 0)


def run(D, sigs):
    P = D["P"]; out = []; free = P["t0"]
    for i, side, tag in sorted(sigs):
        if i < free or i < P["t0"] or i > P["t1"]:
            continue
        t = trade(D, i, side)
        if t is None:
            continue
        t["day"] = D["day"]; t["dte"] = D["dte"]
        out.append(t)
        free = t["i_out"] + P["cool"]
    return out


def play(D):
    X = feats(D)
    sig = sig_exp(D, X) if D["dte0"] else fam.sig_pb(D, X, W=1200, vmin=40.0, pb=0.5, amax=900, rs=5.0)
    return run(D, sig)


def feats_full(D):
    """the inputs the entry families need that come from the forward alone."""
    fs = D["fs"]
    X = {"gap": np.zeros(N)}
    for L in (60, 150, 300, 600, 900, 1200, 1800, 3600):
        X[f"mom{L}"] = FL.lagdiff(fs, L)
    for W in (300, 600, 900, 1200, 1800, 3600):
        hi, lo = FL.roll_ext(fs, W)
        X[f"hi{W}"], X[f"lo{W}"], X[f"rng{W}"] = hi, lo, hi - lo
    d15 = np.abs(FL.lagdiff(fs, 15))
    for W in (300, 1200, 3600):
        path = FL.roll_sum(d15, W) / 15.0
        X[f"er{W}"] = np.abs(FL.lagdiff(fs, W)) / np.where(path > 0, path, np.nan)
    X["em15"] = fs * D["iv"] * np.sqrt(900.0 / FL.YEAR_S)
    return X


def sig_fade(D, Wmin=20, z=0.6):
    """buy against a Wmin-minute move of z day-sigmas, read at each minute's last second (the fade books' rule)."""
    em = meta()[D["day"]]["em"]
    if not em:
        return []
    fs = D["fs"]; W = Wmin * 60
    out = []; last = {"CE": -10 ** 9, "PE": -10 ** 9}
    for i in range(W + 59, N, 60):
        a, b = fs[i], fs[i - W]
        if a == a and b == b:
            mv = a - b
            side = "PE" if mv >= z * em else ("CE" if mv <= -z * em else None)
            if side and i - last[side] >= W:
                out.append((i, side, "fade")); last[side] = i
    return out
