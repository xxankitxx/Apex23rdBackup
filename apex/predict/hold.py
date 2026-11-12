"""11 Nov 2026 (docs/49, owner: book higher, re-enter if the run is still strong): the held-position continuation model
and the re-entry model. ONE feature function for the offline data (research/predict/build_hold.py) and the engine's
twins (apex/engine/council, apex/engine/paper), so both see the same numbers.

Two frozen linear models (fitted offline, JSON; no fitting at run time):
  hold     at a held position's 15-second checkpoint: the expected value, in per cent of the entry premium, of holding
           to what the parent book would do, against selling at the bid now. Below the model's line: sell now.
  reenter  in the 15 minutes after the parent's exit, on the same contract: the expected result, in per cent, of
           buying at the ask now under a fixed exit (8 % off the peak bid, 15 minutes, or 15:20). Above its line: buy.

Inputs are histories the engine already keeps at 1 Hz (ctx["ohist"]: the future, and each option's mid and IV).
Missing inputs give None: no decision (the parent's own rules carry on). Shadow only."""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HOLD_FILE = os.path.join(HERE, "hold_v1.json")
REENTER_FILE = os.path.join(HERE, "reenter_v1.json")
CHECK_S = 15                       # a decision every 15 s
REENTER_WINDOW_S = 900             # re-entry considered for 15 minutes after an exit
RE_TRAIL, RE_HOLD_S = 0.08, 900    # the re-entry leg's fixed exit
TRADE_S_YEAR = 252.0 * 22500.0

HOLD_FEATS = ("gain", "peak", "dd", "held", "since_pk", "m30", "m120", "m300", "pm60", "ratio", "dte", "tod", "spread")
RE_FEATS = ("since_exit", "chg_exit", "vs_peak", "exit_gain", "m30", "m120", "m300", "pm60", "ratio", "dte", "tod", "spread")


def _at(hist, t, tol=3.0):
    """Value of a [(t, v)] history at time t (nearest within tol seconds), or None. hist is in time order."""
    if not hist:
        return None
    lo, hi = 0, len(hist) - 1
    while lo < hi:
        m = (lo + hi) // 2
        if hist[m][0] < t:
            lo = m + 1
        else:
            hi = m
    best = None
    for j in (lo - 1, lo):
        if 0 <= j < len(hist) and abs(hist[j][0] - t) <= tol and hist[j][1] is not None:
            if best is None or abs(hist[j][0] - t) < abs(best[0] - t):
                best = hist[j]
    return None if best is None else float(best[1])


def market(now, fut_hist, direction, iv, F=None):
    """Signed futures momentum over 30/120/300 s in units of realised volatility, and realised over implied variance
    (the gamma-rent idea) from the last 10 minutes of 5-s increments. fut_hist: [(t, F)] at about 1 Hz."""
    if not fut_hist or len(fut_hist) < 120:
        return None
    pts = [(t, f) for t, f in fut_hist if t >= now - 600 and f]
    if len(pts) < 60:
        return None
    arr = np.array(pts, float)
    t0 = arr[0, 0]
    grid = np.arange(t0, now + 1e-9, 5.0)
    f5 = np.interp(grid, arr[:, 0], arr[:, 1])
    d = np.diff(f5)
    if len(d) < 10:
        return None
    sig = float(np.std(d)) / math.sqrt(5.0)                   # points per sqrt(second)
    if not sig > 0:
        return None
    Fn = float(arr[-1, 1]) if F is None else F
    out = {}
    for k in (30, 120, 300):
        x = _at(fut_hist, now - k)
        out[f"m{k}"] = float(np.clip(direction * (Fn - x) / (sig * math.sqrt(k)), -5, 5)) if x is not None else 0.0
    impl = (iv * Fn / math.sqrt(TRADE_S_YEAR)) if iv and iv > 0 else None
    out["ratio"] = float(np.clip((sig / impl) ** 2, 0, 10)) if impl else 1.0
    return out


def hold_features(now, entry, bid, ask, mid_hist, peak_bid, t_in, t_peak, fut_hist, direction, iv, dte, tod_s):
    """The held-position state, HOLD_FEATS order, or None when an input is missing."""
    if not (entry and bid and ask and entry > 0 and bid > 0 and ask >= bid):
        return None
    mk = market(now, fut_hist, direction, iv)
    if mk is None:
        return None
    m60 = _at(mid_hist, now - 60)
    mid = 0.5 * (bid + ask)
    pk = max(peak_bid or bid, bid)
    x = dict(gain=bid / entry - 1.0, peak=pk / entry - 1.0, dd=(pk - bid) / entry,
             held=math.log1p(max(now - t_in, 0) / 60.0), since_pk=math.log1p(max(now - (t_peak or now), 0) / 60.0),
             pm60=(mid - m60) / entry if m60 is not None else 0.0, dte=float(dte), tod=tod_s / 22500.0,
             spread=(ask - bid) / mid, **mk)
    return np.array([x[k] for k in HOLD_FEATS], float)


def re_features(now, exit_t, exit_px, exit_gain, prior_peak, bid, ask, mid_hist, fut_hist, direction, iv, dte, tod_s):
    """The state after an exit, RE_FEATS order, or None."""
    if not (exit_px and bid and ask and bid > 0 and ask >= bid):
        return None
    mk = market(now, fut_hist, direction, iv)
    if mk is None:
        return None
    m60 = _at(mid_hist, now - 60)
    mid = 0.5 * (bid + ask)
    x = dict(since_exit=math.log1p(max(now - exit_t, 0) / 60.0), chg_exit=bid / exit_px - 1.0,
             vs_peak=bid / prior_peak - 1.0 if prior_peak else 0.0, exit_gain=exit_gain,
             pm60=(mid - m60) / exit_px if m60 is not None else 0.0, dte=float(dte), tod=tod_s / 22500.0,
             spread=(ask - bid) / mid, **mk)
    return np.array([x[k] for k in RE_FEATS], float)


class Linear:
    """A frozen standardised linear model from JSON: dict(feats, med, sd, w (intercept first), line, hash, ...)."""

    def __init__(self, path=None, art=None):
        self.art = art
        if art is None and path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.art = json.load(f)
        a = self.art or {}
        self.ok = bool(a.get("w"))
        if self.ok:
            self.med, self.sd = np.array(a["med"], float), np.array(a["sd"], float)
            self.w = np.array(a["w"], float)
            self.line = float(a["line"])
            self.hash = a.get("hash")

    def predict(self, x):
        if not self.ok or x is None:
            return None
        z = np.clip(np.nan_to_num((np.asarray(x, float) - self.med) / self.sd), -5, 5)
        return float(self.w[0] + z @ self.w[1:])


_MODELS = {}


def model(name):
    """The frozen model by name ('hold' or 'reenter'), loaded once."""
    if name not in _MODELS:
        _MODELS[name] = Linear(HOLD_FILE if name == "hold" else REENTER_FILE)
    return _MODELS[name]
