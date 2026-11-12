"""Forecast Lab v2 (11 Nov 2026, evening): the trained part. See docs/50.

features()   45 causal inputs at a forecast origin, computed from the lab's own 1-second state. One function for the
             recorded sessions (training) and the live runner.
Brain        models fitted offline on EARLIER sessions only (research/forecast_lab/train.py), loaded from one file:
               vol      per horizon, a log-linear multi-scale (HAR-type) model of the future's realised variance with
                        intraday seasonality, jump-robust inputs and the options' implied variance
               shape    per horizon, the empirical quantiles of the standardised move (fat tails, not a bell curve),
                        and the spread of the volatility error (used as a stochastic-volatility mixture in the paths)
               drift    per horizon, two experts for the standardised move: a ridge model and a gradient-boosted tree
                        model. They join the online expert pool; their weight is earned live
               iv       the implied volatility's expected drift by time of day and days to expiry, its sensitivity to
                        the future's move by moneyness (the skew slide), and its residual noise
Nothing is fitted at run time here; online learning stays in core.py."""
import math
import os

import numpy as np

H = (60, 120, 180, 300, 600, 900, 1800)
OPEN_S = 9 * 3600 + 15 * 60
SESSION_S = 22500.0
TOD_BUCKET_S = 900                               # 25 buckets of 15 minutes
N_TOD = 25
MNY_EDGES = (-0.012, -0.006, -0.002, 0.002, 0.006, 0.012)   # log(K / forward) bucket edges for the skew slide

FEATS = (
    # momentum of the future, in units of its own 10-minute volatility
    "r5", "r15", "r30", "r60", "r120", "r300", "r600", "r1800",
    # volatility state (log variance per second) at four clocks, the implied level, and their relations
    "lv30", "lv120", "lv600", "lv1800", "lviv", "lv120_600", "lv600_iv", "jump120", "absr5",
    # regime: variance ratio (trend against chop), efficiency ratio, local slope, Kalman trend
    "vr", "er300", "slope120", "kf",
    # order flow and the quote
    "imb", "micro", "ofi30", "ofi120", "spr",
    # where the price is
    "vwap", "rng", "dhi", "dlo",
    # the option surface: level changes, skew, straddle, forward basis
    "div60", "div300", "skew", "dskew300", "dstr60", "dbasis",
    # heavyweights: breadth and lead
    "hw30", "hw120", "hwlead30", "bank120", "up60",
    # the clock
    "tod", "tod2", "left", "dte", "exp",
)
NF = len(FEATS)


def sod(t):
    return (int(t) + 19800) % 86400


def tod_bucket(t):
    return int(np.clip((sod(t) - OPEN_S) // TOD_BUCKET_S, 0, N_TOD - 1))


class Kalman:
    """Local linear trend filter on the future's mid, 1 Hz: state (level, slope). Noise sizes follow the running
    variance, so it needs no tuning by hand. slope is points per second."""

    def __init__(self):
        self.x = None
        self.P = np.eye(2)

    def step(self, y, v):
        if self.x is None:
            self.x = np.array([y, 0.0])
            self.P = np.diag([v, v * 1e-4])
            return 0.0
        Fm = np.array([[1.0, 1.0], [0.0, 1.0]])
        Q = np.diag([0.5 * v, v * 2e-5])
        R = 0.5 * v
        x = Fm @ self.x
        P = Fm @ self.P @ Fm.T + Q
        k = P[:, 0] / (P[0, 0] + R)
        self.x = x + k * (y - x[0])
        self.P = P - np.outer(k, P[0, :])
        return float(self.x[1])


def features(lab, t, F, v):
    """FEATS at time t, or None before there is enough history. v: reference variance per second (10-min clock)."""
    tail = lab.tail(1800)
    if tail is None or len(tail) < 600:
        return None, None
    sd1 = math.sqrt(max(v, 1e-12))

    def back(sec):
        if len(tail) <= sec or not np.isfinite(tail[-1 - sec]):
            return 0.0
        return float(np.clip((F - tail[-1 - sec]) / (sd1 * math.sqrt(sec)), -6, 6))
    x = {}
    for k in (5, 15, 30, 60, 120, 300, 600):
        x[f"r{k}"] = back(k)
    x["r1800"] = back(min(1799, len(tail) - 1))
    f5 = tail[::-1][::5][::-1]                                   # 5-s samples ending now
    d5 = np.diff(f5)
    d5 = d5[np.isfinite(d5)]

    def lvar(n):
        if len(d5) < max(6, n // 3):
            return math.log(max(v, 1e-12))
        return math.log(max(float(np.mean(d5[-n:] ** 2)) / 5.0, 1e-12))
    x["lv30"], x["lv120"], x["lv600"], x["lv1800"] = lvar(6), lvar(24), lvar(120), lvar(360)
    c = lab.chain
    impl = None
    if c is not None and np.isfinite(c.get("atm_iv", np.nan)):
        impl = (c["atm_iv"] * c["Fs"]) ** 2 / (252.0 * 22500.0)
    x["lviv"] = math.log(impl) if impl else x["lv1800"]
    x["lv120_600"] = x["lv120"] - x["lv600"]
    x["lv600_iv"] = x["lv600"] - x["lviv"]
    a = np.abs(d5[-24:])
    bv = float(np.mean(a[1:] * a[:-1])) * (math.pi / 2.0) if len(a) > 3 else 0.0     # bipower variation: jump-robust
    rv = float(np.mean(a ** 2)) if len(a) else 0.0
    x["jump120"] = float(np.clip(math.log(max(rv, 1e-12) / max(bv, 1e-12)), -2, 3)) if bv > 0 else 0.0
    x["absr5"] = abs(x["r5"])
    # regime
    if len(d5) >= 120:
        w = d5[-120:]
        d60 = w.reshape(10, 12).sum(1)
        x["vr"] = float(np.clip(np.var(d60) / max(12.0 * np.var(w), 1e-12), 0, 4))
    else:
        x["vr"] = 1.0
    w = d5[-60:] if len(d5) >= 60 else d5
    x["er300"] = float(abs(w.sum()) / max(np.abs(w).sum(), 1e-9)) if len(w) else 0.0
    seg = tail[-120:]
    seg = seg[np.isfinite(seg)]
    if len(seg) > 30:
        tt = np.arange(len(seg), dtype=float)
        x["slope120"] = float(np.clip(np.polyfit(tt, seg, 1)[0] * math.sqrt(120.0) / sd1, -6, 6))
    else:
        x["slope120"] = 0.0
    x["kf"] = float(np.clip(lab.kf_slope * math.sqrt(60.0) / sd1, -6, 6))
    # order flow
    tot = (lab.fbq + lab.faq) if np.isfinite(lab.fbq) and np.isfinite(lab.faq) else np.nan
    spr = lab.fspread if np.isfinite(lab.fspread) else 1.0
    x["imb"] = float((lab.fbq - lab.faq) / tot) if np.isfinite(tot) and tot > 0 else 0.0
    ih = lab.imb_hist                                             # the imbalance's own change over 10 s (with the
    x["micro"] = float(x["imb"] - ih[-11]) if len(ih) > 10 else 0.0   # top-of-book totals the micro-price IS the imbalance)
    o = np.array(lab.ofi_long, float) if len(lab.ofi_long) else np.zeros(1)
    sc = max(lab.scale.get("ofi1", 1.0), 1e-9)
    x["ofi30"] = float(np.clip(o[-30:].sum() / (sc * 30.0), -3, 3))       # signed share of the usual flow
    x["ofi120"] = float(np.clip(o[-120:].sum() / (sc * 120.0), -3, 3))
    x["spr"] = float(np.clip(spr / max(sd1 * 2.24, 1e-6), 0, 5))           # spread against a 5-second move
    # position
    x["vwap"] = float(np.clip((F - lab.vwap_pv / lab.vwap_v) / (sd1 * math.sqrt(1800.0)), -6, 6)) if lab.vwap_v > 0 else 0.0
    rg = (lab.hi - lab.lo) if lab.hi is not None else 0.0
    x["rng"] = float(2.0 * (F - lab.lo) / rg - 1.0) if rg > 1e-6 else 0.0
    x["dhi"] = float(np.clip((lab.hi - F) / (sd1 * math.sqrt(300.0)), 0, 8)) if lab.hi is not None else 0.0
    x["dlo"] = float(np.clip((F - lab.lo) / (sd1 * math.sqrt(300.0)), 0, 8)) if lab.lo is not None else 0.0
    # option surface, from the 5-s history (t, Fs, atm_iv, F, slope, straddle)
    ah = lab.atm_hist

    def ago(n, j):
        return ah[-1 - n][j] if len(ah) > n and ah[-1 - n][j] is not None else None
    cur = ah[-1] if len(ah) else None
    def chg(n, j, scale):
        a0 = ago(n, j)
        return float(np.clip((cur[j] - a0) / scale, -6, 6)) if cur is not None and a0 is not None and cur[j] is not None else 0.0
    ivl = max(cur[2], 0.03) if cur is not None else 0.12
    x["div60"], x["div300"] = chg(12, 2, 0.01 * ivl), chg(60, 2, 0.02 * ivl)        # in per cent of the IV level
    x["skew"] = float(np.clip(cur[4], -5, 5)) if cur is not None and len(cur) > 4 and cur[4] is not None and np.isfinite(cur[4]) else 0.0
    x["dskew300"] = chg(60, 4, 0.5) if cur is not None and len(cur) > 4 else 0.0
    if cur is not None and len(cur) > 5 and cur[5] and ago(12, 5):
        x["dstr60"] = float(np.clip((cur[5] / ago(12, 5) - 1.0) * 100.0, -5, 5))
    else:
        x["dstr60"] = 0.0
    if cur is not None and ago(24, 1) is not None:
        x["dbasis"] = float(np.clip(((cur[1] - cur[3]) - (ago(24, 1) - ago(24, 3))) / (sd1 * math.sqrt(120.0)), -6, 6))
    else:
        x["dbasis"] = 0.0
    # heavyweights
    hw = lab.hw_tail(120)
    if hw is not None:
        idx, bank, rest, up = hw
        fut_r30 = (F / tail[-31] - 1.0) if len(tail) > 31 and np.isfinite(tail[-31]) and tail[-31] > 0 else 0.0
        rel = sd1 / max(F, 1.0)
        x["hw30"] = float(np.clip((idx[-1] - idx[-31]) / (rel * math.sqrt(30.0)), -6, 6))
        x["hw120"] = float(np.clip((idx[-1] - idx[0]) / (rel * math.sqrt(120.0)), -6, 6))
        x["hwlead30"] = float(np.clip(((idx[-1] - idx[-31]) - fut_r30) / (rel * math.sqrt(30.0)), -6, 6))
        x["bank120"] = float(np.clip(((bank[-1] - bank[0]) - (rest[-1] - rest[0])) / (rel * math.sqrt(120.0)), -6, 6))
        x["up60"] = float(up)
    else:
        x["hw30"] = x["hw120"] = x["hwlead30"] = x["bank120"] = 0.0
        x["up60"] = 0.5
    s = sod(t) - OPEN_S
    x["tod"] = s / SESSION_S
    x["tod2"] = (s / SESSION_S - 0.5) ** 2
    x["left"] = math.log1p(max(SESSION_S - s, 0.0) / 600.0)
    x["dte"] = float(min(c["T"] * 365.0, 8.0)) if c is not None else 3.0
    x["exp"] = 1.0 if (c is not None and c["T"] * 365.0 < 1.0) else 0.0
    return np.array([x[k] for k in FEATS], float), x


class Brain:
    """The offline-trained models, read from a file written by research/forecast_lab/train.py."""

    def __init__(self, path=None, obj=None):
        self.ok = False
        self.why = "no brain file"
        self.meta = {}
        if obj is None and path and os.path.exists(path):
            try:
                import joblib
                obj = joblib.load(path)
            except Exception as e:                                # a damaged or foreign file: run without it
                self.why = f"brain file unreadable: {type(e).__name__}"
                obj = None
        if obj is None:
            return
        if tuple(obj.get("feats", ())) != FEATS or tuple(obj.get("H", ())) != H:
            self.why = "brain was fitted on other features or horizons"
            return
        self.o = obj
        self.meta = obj.get("meta", {})
        self.med, self.sd = np.asarray(obj["med"], float), np.asarray(obj["sd"], float)
        self.ok, self.why = True, None

    def z(self, x):
        return np.clip(np.nan_to_num((np.asarray(x, float) - self.med) / self.sd), -6, 6)

    def vol(self, x, v_ref):
        """Predicted variance of the future's move over each horizon (points squared), from the log-variance model.
        v_ref is the lab's own reference variance per second (the model predicts the log ratio to it)."""
        zz = self.z(x)
        out = np.empty(len(H))
        for j, h in enumerate(H):
            w = self.o["vol"][j]
            out[j] = v_ref * h * math.exp(float(np.clip(w[0] + zz @ w[1:], -3.0, 3.0)))
        return out

    def drift(self, x):
        """Standardised expected move per horizon from the two trained experts: (ridge (H,), boosted trees (H,))."""
        zz = self.z(x)
        lin = np.array([float(w[0] + zz @ w[1:]) for w in self.o["lin"]])
        gb = np.zeros(len(H))
        models = self.o.get("gbm")
        if models:
            X = np.asarray(x, float)[None, :]
            for j, m in enumerate(models):
                if m is not None:
                    gb[j] = float(m.predict(X)[0])
        return lin, gb

    def qz(self, j):
        """Standardised quantiles (10, 25, 50, 75, 90) of the move at horizon j."""
        return np.asarray(self.o["qz"][j], float)

    def volvol(self, j):
        return float(self.o["volvol"][j])

    def iv_drift(self, t, dte_days):
        """Expected change of the at-the-money implied volatility per second (decimal vol) at this time of day."""
        tab = self.o["iv"]["drift"]
        k = 0 if dte_days < 1.0 else (1 if dte_days < 3.0 else 2)
        return float(tab[k][tod_bucket(t)])

    def iv_res(self, dte_days):
        k = 0 if dte_days < 1.0 else (1 if dte_days < 3.0 else 2)
        return float(self.o["iv"]["res"][k])

    def iv_beta(self, lk, dte_days):
        """d(strike IV) / d(forward, points) for a strike at log-moneyness lk: the skew slide, by bucket."""
        k = 0 if dte_days < 1.0 else (1 if dte_days < 3.0 else 2)
        b = int(np.searchsorted(MNY_EDGES, lk))
        return float(self.o["iv"]["beta"][k][b])
