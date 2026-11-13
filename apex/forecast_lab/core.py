"""Forecast Lab core (11 Nov 2026). See apex/forecast_lab/__init__.py and docs/48.

One call a second: Lab.step(inp). The input is plain arrays (the Nifty future's quote and depth totals, the near
weekly chain's bids, asks and quote ages), so the same code runs live (live.py) and on recorded sessions (tape.py).

What it forecasts, every 5 seconds:
  FUTURE   the Nifty future's change over the next 1, 2, 3, 5, 10, 15 and 30 minutes as a distribution: a mean from
           five competing "experts" (still, momentum, order flow, reversion, blend) weighted by how well each has
           ACTUALLY done on matured forecasts (exponentially weighted forecaster with fixed share), and a spread from
           three realised-volatility clocks plus the options' implied volatility, rescaled by its own matured errors.
  OPTIONS  the premium of the contracts the engine would buy now (and the at-the-money pair, and a held contract)
           at the same horizons: 1,000 simulated paths of the future, each with the implied volatility moving by the
           measured spot-vol beta and intraday drift, repriced with Black-76 as time to expiry runs down. So decay,
           volatility drift and the move are all inside one number. Also: P(profit if bought now at the ask and sold
           at the bid later), the break-even move, which comes first (+5 % or -5 % of the premium within 5 minutes),
           and the 5-minute change split into delta, gamma, vega and theta parts.
  DECAY    for the strikes around the money: model theta per minute, decay including the volatility trend, and the
           decay ACTUALLY measured from the quotes (premium change not explained by the future's move), and the
           gamma-rent ratio: realised movement against the movement needed to pay for decay.
  SCORING  every forecast is kept until each horizon has passed; then it is scored against what happened and the
           models learn: expert weights (Hedge), expert coefficients (recursive least squares with forgetting),
           the volatility scale, the interval width (adaptive conformal), the option bands, and the volatility beta.
           A frozen copy of the morning's models is scored beside them, so the learning can be shown to help or not.

All causal: every number at time t uses data up to t only. Display and research only: nothing here trades."""
import math
import os
from collections import deque
from datetime import datetime

import numpy as np
from scipy.special import ndtr

from .. import config, greeks
from . import brain as B
from . import clock as CK

VERSION = 3                                 # 11 Nov night: every sentence gated on its own checked record (earned())
STATE_VERSION = 3                           # the saved learning state's own format, separate from the panel's VERSION
KAPPA_OK = (0.5, 2.0)                       # a saved calibration outside these bounds is reset on load (a stall or a bug
                                            # may have made it); 12 Nov: the rest of the learning is kept, never thrown away
Z80_OK = (0.9, 2.0)
Z80_START = 1.2816
SPY = 365.0 * 86400.0                       # calendar seconds a year: the engine's implied-volatility convention
TRADE_S_YEAR = 252.0 * 22500.0              # trading seconds a year (252 sessions of 6 h 15 min)
TRADE_CLOCK = 1440.0 / 375.0                # a calendar day's decay spread over the 375 trading minutes (the engine's
                                            # and the champion's theta convention): trading-clock theta = calendar x 3.84
# 12 Nov (PKG-08): the panel's decay, rent, implied move and v_sec's implied part use ONE business clock instead
# (clock.py: k = calendar seconds left / trading seconds left; 1 on expiry day). TRADE_CLOCK and TRADE_S_YEAR stay only
# as the old reference. The option paths move to the same clock (Stage B: business-clock repricing, no online IV drift,
# sticky strike, measured IV noise, calibrated futures spread, Brownian-bridge race) only after the repricing scorecard
# (research/forecast_lab/reprice_study.py) passes PR-004 on the recorded tapes. Until then this stays False.
PRICING_STAGE_B = False
H = (60, 120, 180, 300, 600, 900, 1800)     # forecast horizons, seconds
H5 = H.index(300)
ORIGIN_EVERY = 5                            # a scored futures forecast every 5 s
TICKET_EVERY = 15                           # a scored option forecast every 15 s
FULL_EVERY = 5                              # option simulation every 5 s
N_PATHS = 600                               # simulated paths (300 antithetic pairs)
BARRIER = 0.05                              # the old target, kept for a head-to-head: +5 % / -5 % of the premium
EXPERTS = ("still", "momentum", "flow", "reversion", "blend", "ridge", "trees")   # the last two come trained (brain)
RING = 7200                                 # two hours of 1-second history
OPEN_S, CLOSE_S = 9 * 3600 + 15 * 60, 15 * 3600 + 30 * 60
FIRST_ORIGIN_S = OPEN_S + 300               # no forecast is scored in the first five minutes (warm-up)
FRESH_S = 15.0                              # an option quote older than this is not used
SQ2PI = math.sqrt(2.0 * math.pi)
STALE_FUT_S = 5.0                           # a futures quote older than this: no forecast is shown
STALE_SIM_S = 20.0                          # an option simulation older than this is not shown
GRID_S = 10                                 # simulation grid to 5 minutes (the +5 % / -5 % race is checked on it)
M_CLIP = 0.6                                # an expert may claim at most 0.6 sd of drift: shrinkage, not a bet
OVERLAP = {h: ORIGIN_EVERY / h for h in H}  # forecasts 5 s apart over h seconds share most of their outcome
# what the panel may state (earned()): every claim is checked at its own horizon against the right no-skill baseline
RANGE_MIN_CHECKS = 10                       # independent checks before a range's coverage is judged
RANGE_OK = (0.72, 0.88)                     # an 80 % range that caught this share today is stated as '80 %'
LEAN_SD = 0.15                              # one lean threshold (in sd of the move) for scoring, text and the UI colour
DIR_MIN_CHECKS = 20                         # independent clear calls before direction can be earned
DIR_HIT = 0.60                              # share of clear calls right
BUY_H = (300, 900)                          # holding times a buy case is judged at
BUY_MIN_CHECKS = 20                         # independent buy checks (one per 15-s slot over h)
BUY_MARGIN = 0.01                           # the win-chance score must beat min(coin, base rate) by this much
ERR_MARGIN = 0.1                            # the middle premium forecast must beat 'no change' and 'decay only' by this
WILSON_PP = 0.55                            # the bucket of tickets whose win chance was stated at 55 % or more ...
WILSON_MIN = 0.55                           # ... must have realised a win rate whose 95 % Wilson lower bound is this
BUY_MIN_DAYS = 5                            # forward days on record before a direction or buy claim can be made
DAY_ERR_SHARE = 0.70                        # share of those days on which the middle premium error beat 'no change'
ENGINE_FRESH_S = 15.0                       # an engine report older than this (engine time): the account is unknown
DAYS_REFRESH_S = 600.0                      # the daily record (data/forecast_lab/days) is re-read every 10 minutes


# ── Black-76, vectorised (undiscounted, as apex.greeks) ─────────────────────────────────────────────────────────────
def b76(F, K, T, sig, call):
    T = np.maximum(T, 1e-9)
    sT = np.maximum(sig * np.sqrt(T), 1e-6)
    d1 = (np.log(F / K) + 0.5 * sT * sT) / sT
    c = F * ndtr(d1) - K * ndtr(d1 - sT)
    return np.where(call, c, c - F + K)


def b76_greeks(F, K, T, sig, call):
    """delta, gamma (per point), vega (premium per 1 vol POINT), theta (premium per calendar MINUTE, negative),
    vanna (delta per vol point), volga (vega per vol point)."""
    T = np.maximum(T, 1e-9)
    sq = np.sqrt(T)
    s = np.maximum(sig, 1e-4)
    d1 = (np.log(F / K) + 0.5 * s * s * T) / (s * sq)
    d2 = d1 - s * sq
    pdf = np.exp(-0.5 * d1 * d1) / SQ2PI
    delta = np.where(call, ndtr(d1), ndtr(d1) - 1.0)
    gamma = pdf / (F * s * sq)
    vega1 = F * pdf * sq                     # per 1.00 of volatility
    theta_min = -(F * pdf * s) / (2.0 * sq) / (SPY / 60.0)
    vanna = -pdf * d2 / s / 100.0
    volga = vega1 * d1 * d2 / s / 100.0 / 100.0
    return dict(delta=delta, gamma=gamma, vega=vega1 / 100.0, theta=theta_min, vanna=vanna, volga=volga)


def iv_newton(price, F, K, T, call, iters=8):
    """Implied volatility, vectorised Newton on undiscounted Black-76 from a Brenner-Subrahmanyam start. NaN where the
    price is outside the no-arbitrage range or the solve does not settle. About 100 times faster than bisection."""
    price = np.asarray(price, float)
    intr = np.where(call, np.maximum(F - K, 0.0), np.maximum(K - F, 0.0))
    ok = np.isfinite(price) & (price > intr + 1e-6) & (price < np.where(call, F, K))
    T = max(float(T), 1e-9)
    sq = math.sqrt(T)
    sig = np.clip(np.sqrt(2.0 * math.pi / T) * np.where(ok, price, 1.0) / F, 0.02, 2.5)
    for _ in range(iters):
        d1 = (np.log(F / K) + 0.5 * sig * sig * T) / (sig * sq)
        c = F * ndtr(d1) - K * ndtr(d1 - sig * sq)
        model = np.where(call, c, c - F + K)
        vega = F * np.exp(-0.5 * d1 * d1) / SQ2PI * sq
        sig = np.clip(sig - (model - price) / np.maximum(vega, 1e-8), 0.01, 3.0)
    d1 = (np.log(F / K) + 0.5 * sig * sig * T) / (sig * sq)
    c = F * ndtr(d1) - K * ndtr(d1 - sig * sq)
    err = np.abs(np.where(call, c, c - F + K) - price)
    return np.where(ok & (err < np.maximum(1e-3 * price, 0.02)), sig, np.nan)


def crps_normal(mu, sd, y):
    """Continuous ranked probability score of N(mu, sd^2) at y (lower is better); vectorised."""
    sd = np.maximum(sd, 1e-9)
    z = (y - mu) / sd
    return sd * (z * (2.0 * ndtr(z) - 1.0) + 2.0 * np.exp(-0.5 * z * z) / SQ2PI - 1.0 / math.sqrt(math.pi))


# ── online learners ─────────────────────────────────────────────────────────────────────────────────────────────────
class RLS:
    """Recursive least squares with exponential forgetting and a ridge prior; no intercept (a drift must be earned)."""

    def __init__(self, k, lam=0.9995, delta=0.5):
        self.k, self.lam, self.delta = k, lam, delta
        self.th = np.zeros(k)
        self.P = np.eye(k) * delta
        self.n = 0

    def predict(self, x):
        return float(self.th @ x) if self.k else 0.0

    def update(self, x, y, w=1.0):
        """One observation with weight w in (0, 1]: an observation that shares its outcome with many neighbours
        counts as a fraction of one. Forgetting is scaled the same way."""
        if not self.k:
            return
        sw = math.sqrt(w)
        x, y = x * sw, y * sw
        lam = 1.0 - (1.0 - self.lam) * w
        Px = self.P @ x
        g = Px / (lam + float(x @ Px))
        self.th = self.th + g * (y - float(self.th @ x))
        self.P = (self.P - np.outer(g, Px)) / lam
        tr = float(np.trace(self.P))
        if not np.isfinite(tr) or tr > 50.0 * self.k * self.delta:      # forgetting without excitation: reset the size
            self.P = np.eye(self.k) * self.delta
        self.n += 1

    def to_json(self):
        return dict(k=self.k, lam=self.lam, delta=self.delta, th=self.th.tolist(), P=self.P.tolist(), n=self.n)

    @classmethod
    def from_json(cls, d):
        r = cls(d["k"], d["lam"], d["delta"])
        r.th, r.P, r.n = np.array(d["th"], float), np.array(d["P"], float), int(d["n"])
        return r


class Hedge:
    """Exponentially weighted average forecaster with fixed share (Herbster and Warmuth): weights follow the experts'
    cumulative losses, and a small share is spread back each round so a recently good expert can take over."""

    def __init__(self, m, eta=2.0, share=0.01):
        self.m, self.eta, self.share = m, eta, share
        self.w = np.full(m, 1.0 / m)
        self.n = 0

    def update(self, losses, rate=1.0):
        """rate scales both the learning rate and the share for one round (overlapping forecasts count fractionally)."""
        w = self.w * np.exp(-self.eta * rate * (np.asarray(losses, float) - np.min(losses)))
        w = w / w.sum()
        a = self.share * rate
        self.w = (1.0 - a) * w + a / self.m
        self.n += 1


# ── helpers ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def sod(t):
    """Seconds since midnight IST."""
    return (int(t) + 19800) % 86400


def ewma_alpha(half_life):
    return 1.0 - 0.5 ** (1.0 / max(half_life, 1e-9))


def band_for(day, exp, now):
    """The engine's delta band (paper.choose_contract, near week), or None when no near-week entry is allowed."""
    hmn = now.hour * 60 + now.minute
    if day == exp:
        if hmn >= config.mins(config.ZERO_DTE_NO_ENTRY) or config.ZERO_DTE_USE_NEXTWEEK:
            return None
        return config.DELTA_BANDS["zero_am"]
    dte = (np.datetime64(exp) - np.datetime64(day)).astype(int)
    return config.DELTA_BANDS["ge3"] if dte >= 3 else config.DELTA_BANDS["1to2"]


def pick(delta, mid, age, band):
    """Index of the strike the default rule would buy on one side; None when there is none."""
    if band is None:
        return None
    lo, hi = band
    ok = np.isfinite(delta) & np.isfinite(mid) & (mid >= config.MIN_PREMIUM) & (mid <= config.MAX_PREMIUM) & (age < FRESH_S)
    ad = np.abs(delta)
    inb = ok & (ad >= lo) & (ad <= hi)
    if inb.any():
        return int(np.where(inb, ad, np.inf).argmin())
    ab = ok & (ad >= lo)
    return int(np.where(ab, ad, np.inf).argmin()) if ab.any() else None


def time_ok(t_eng, t_now, max_age=20.0):
    """The engine's report is recent enough to trust (live: wall clock); offline there is none."""
    import time as _t
    return t_eng is not None and (t_now is None or abs(_t.time() - float(t_eng)) <= max_age)


def r1(x, d=1):
    return None if x is None or not np.isfinite(x) else round(float(x), d)


# ── the lab ─────────────────────────────────────────────────────────────────────────────────────────────────────────
class Lab:
    def __init__(self, state=None, n_paths=N_PATHS, seed=7, options=True, brain=None, collect=False):
        self.n_paths = n_paths
        self.brain = brain if (brain is not None and brain.ok) else None
        self.collect = [] if collect else None                   # (t, F, v_ref, features) per origin, for training
        self.kf = B.Kalman()
        self.kf_slope = 0.0
        self.ofi_long = deque(maxlen=120)
        self.imb_hist = deque(maxlen=31)
        self.hw_ring = deque(maxlen=121)                         # per second: (index, bank, rest) cumulative log returns
        self.hw_px = deque(maxlen=61)
        self.hw_cum = [0.0, 0.0, 0.0]
        self.hw_syms = None                                      # the heavyweights' symbols, in the order of hw_px
        self.events = deque(maxlen=50)                           # one-line notes for the runner's log
        self.restarts = 0                                        # same-day restarts (counted from the saved state)
        self.extra_state = {}                                    # other modules' persisted sums (saved with the state)
        self.load_status = dict(ok=False, why="no saved state", carried=[])
        self.fspread = self.fbq = self.faq = self.fbb = self.faa = np.nan
        self.options = options
        self.rng = np.random.default_rng(seed)
        nh = len(H)
        # futures history, 1 Hz
        self.ft = np.full(RING, np.nan)
        self.fm = np.full(RING, np.nan)
        self.n = 0
        self.last_t = None
        self.day = None
        self.vol = {120: None, 600: None, 1800: None}            # per-second variance clocks
        self.vwap_pv = self.vwap_v = 0.0
        self.last_ttq = None
        self.hi = self.lo = None
        self.ofi = deque(maxlen=30)
        self.prev_q = None
        self.scale = {}                                          # running abs scale of each raw signal
        # experts: inputs per expert, one RLS per (expert, horizon)
        self.sig_names = ("r30", "r120", "r600", "imb", "micro", "ofi30", "basis", "vwap", "rng")
        self.cols = dict(still=(), momentum=(0, 1, 2), flow=(3, 4, 5, 6), reversion=(7, 8), blend=tuple(range(9)),
                         ridge=(), trees=())
        self.rls = {e: [RLS(len(self.cols[e])) for _ in H] for e in EXPERTS}
        self.hedge = [Hedge(len(EXPERTS)) for _ in H]
        self.kappa = np.ones(nh)                                 # variance calibration per horizon
        self.z80 = np.full(nh, Z80_START)                        # adaptive-conformal multiplier for the 80 % band
        # option layer
        self.iv_beta, self.iv_beta_n = -4e-5, 0                  # vol (decimal) per futures point
        self.iv_drift = 0.0                                      # vol (decimal) per second, intraday trend
        self.iv_res = 2e-5                                       # residual vol sd per sqrt(second)
        self.atm_hist = deque(maxlen=400)                        # (t, Fs, atm iv) every 5 s
        self.opt_hist = {}                                       # (strike, rr) -> deque((t, mid, Fs)), 5-s cadence
        self.odw = 0.5                                           # share of the futures drift the option layer uses (learned)
        self.oe_with, self.oe_without = 1.0, 1.0                 # running errors of the premium median with / without it
        self.obias = np.zeros(nh)                                # option median bias, in band widths
        self.oscale = np.ones(nh)                                # option band scale (adaptive conformal)
        # forecasts waiting to be scored
        self.origins = deque()
        self.tickets = deque()
        self.frozen = None                                       # the morning's models, scored beside the live ones
        self.score = self._new_score()
        self.alltime = dict(fut_n=0, opt_n=0)
        self.last = None                                         # the latest full output
        self.chain = None
        self.engine = None
        self.cost = dict(step_ms=0.0, full_ms=0.0)
        self.fpath = None
        self.simulate = options
        if state:
            self.load(state)
        self._freeze()

    # ── persistence ────────────────────────────────────────────────────────────────────────────────────────────
    def _note(self, msg):
        """A one-line note for the runner's log; the same note twice in a row is kept once."""
        if getattr(self, "_last_note", None) != msg:
            self.events.append(msg)
            self._last_note = msg

    def vol_basis(self):
        """What kappa scales: 'plain' (the realised-variance clock) or 'brain:<hash>' (the trained volatility model).
        kappa and z80 learned against one basis mean nothing against another."""
        if self.brain is None:
            return "plain"
        return "brain:" + str((self.brain.meta or {}).get("hash") or "unknown")

    def to_json(self):
        fz = self.frozen
        return dict(version=STATE_VERSION, state_version=STATE_VERSION, experts=list(EXPERTS), vol_basis=self.vol_basis(),
                    rls={e: [r.to_json() for r in self.rls[e]] for e in EXPERTS},
                    hedge=[h.w.tolist() for h in self.hedge], hedge_n=[h.n for h in self.hedge],
                    kappa=self.kappa.tolist(), z80=self.z80.tolist(), iv_beta=self.iv_beta, iv_beta_n=self.iv_beta_n,
                    _b_sxx=getattr(self, "_b_sxx", None), _b_sxy=getattr(self, "_b_sxy", None),
                    iv_res=self.iv_res, obias=self.obias.tolist(), oscale=self.oscale.tolist(), scale=self.scale,
                    alltime=self.alltime, day=self.day, odw=self.odw, oe=[self.oe_with, self.oe_without],
                    frozen=(dict(day=self.day, th={e: [np.asarray(a).tolist() for a in fz["th"][e]] for e in EXPERTS},
                                 w=[np.asarray(w).tolist() for w in fz["w"]], kappa=np.asarray(fz["kappa"]).tolist())
                            if fz and self.day else None),
                    restarts=self.restarts, extra_state=self.extra_state,
                    score={k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in self.score.items()})

    def load(self, s, bounds=False):
        """Load a saved learning state. Returns (ok, why, carried). bounds=True (the live runner) also handles a state
        whose kappa or z80 is outside KAPPA_OK / Z80_OK by resetting those two only (12 Nov: never the rest);
        offline walks carry any learned value. When ok is False the lab is left exactly as it
        was: every field is checked before any is assigned. Version 1 and 2 files are migrated (migrate()). A current
        file whose volatility basis differs from this lab's (brain added, removed or retrained) keeps the learning
        whose meaning did not change and resets the rest."""
        try:
            res = self._load(s, bounds)
        except (KeyError, ValueError, TypeError, IndexError, AttributeError) as e:
            res = (False, f"unreadable: {type(e).__name__}", [])
        self.load_status = dict(ok=bool(res[0]), why=res[1], carried=list(res[2]))
        return res

    def _load(self, s, bounds=False):
        if not isinstance(s, dict) or not s:
            return False, "empty", []
        ver = s.get("state_version", s.get("version"))
        if ver in (1, 2):
            return self.migrate(s)
        if ver != STATE_VERSION:
            return False, f"discarded: state version {ver} != {STATE_VERSION}", []
        nh = len(H)
        rls = {e: self._rls_rows(s["rls"][e], e) for e in EXPERTS}
        if any(v is None for v in rls.values()):
            return False, "unreadable: expert rows do not match", []
        hedge = self._hedge_rows(s["hedge"], list(s.get("experts") or EXPERTS))
        if hedge is None:
            return False, "unreadable: expert weights do not match", []
        hedge_n = [int(n) for n in (s.get("hedge_n") or [0] * nh)][:nh]
        kappa, z80 = self._vec(s["kappa"]), self._vec(s["z80"])
        obias, oscale = self._vec(s["obias"]), self._vec(s["oscale"])
        if kappa is None or z80 is None or obias is None or oscale is None:
            return False, "unreadable: calibration rows do not match", []
        basis, mine = s.get("vol_basis"), self.vol_basis()
        same = basis == mine
        out_cal = None                                            # 12 Nov: an out-of-bounds calibration is reset, not
        if same and bounds:                                       # a reason to drop the day's learning (z80 0.75 after a
            if kappa.min() < KAPPA_OK[0] or kappa.max() > KAPPA_OK[1]:    # wide-range day made state.json unloadable)
                out_cal = f"kappa {kappa.min():.2f} to {kappa.max():.2f} is outside {KAPPA_OK[0]} to {KAPPA_OK[1]}"
            elif z80.min() < Z80_OK[0] or z80.max() > Z80_OK[1]:
                out_cal = f"z80 {z80.min():.2f} to {z80.max():.2f} is outside {Z80_OK[0]} to {Z80_OK[1]}"
        iv = self._iv_fields(s)
        if iv is None:
            return False, "unreadable: volatility fields are not finite", []
        frozen = self._frozen_from(s.get("frozen")) if same else None
        carried = ["rls", "hedge", "iv_beta", "iv_res", "scale", "odw", "oe", "alltime"]
        if not same:                                              # the trained experts and the scale start again
            fl = self.hedge[0].share / self.hedge[0].m
            for j in range(nh):
                for e in ("ridge", "trees"):
                    hedge[j][EXPERTS.index(e)] = fl
                hedge[j] = hedge[j] / hedge[j].sum()
            kappa, z80, obias, oscale = np.ones(nh), np.full(nh, Z80_START), np.zeros(nh), np.ones(nh)
            why = f"loaded, volatility basis changed ({basis} to {mine}): kappa/z80 reset"
        elif out_cal is not None:                                 # learning kept; only the range calibration restarts
            kappa, z80 = np.ones(nh), np.full(nh, Z80_START)
            carried += ["obias", "oscale", "frozen", "score"]
            why = f"loaded, kappa/z80 reset: {out_cal}"
        else:
            carried += ["kappa", "z80", "obias", "oscale", "frozen", "score"]
            why = "loaded"
        # every field checked: assign
        self.rls = rls
        for h, w, n in zip(self.hedge, hedge, hedge_n + [0] * (nh - len(hedge_n))):
            h.w, h.n = w, n
        self.kappa, self.z80, self.obias, self.oscale = kappa, z80, obias, oscale
        self._set_iv(iv)
        self.scale = dict(s.get("scale") or {})
        self.odw = float(s.get("odw", 0.5))
        self.oe_with, self.oe_without = (float(v) for v in (s.get("oe") or (1.0, 1.0)))
        self.alltime = dict(s.get("alltime") or self.alltime)
        self.extra_state = dict(s.get("extra_state") or {})
        day = s.get("day")
        self._saved_score = (day, s.get("score")) if same else None   # today's record survives a restart
        self._saved_frozen = (day, frozen) if frozen is not None else None
        self._saved_restarts = (day, int(s.get("restarts") or 0))
        self._freeze()
        return True, why, carried

    def migrate(self, s):
        """A version 1 or 2 state (five experts, kappa fitted to the plain clock). Carried: the five shared experts'
        coefficients and weights (the trained experts get the fixed-share floor, then each horizon sums to 1), the
        volatility beta and its sums, iv_res, the signal scales, odw, oe and the all-time counts. Reset: kappa, z80,
        obias and oscale, because v1 kappa scaled sqrt(kappa*v*h) while v3 with a brain scales the trained model, and
        v1 oscale made up for the narrow plain-clock option paths. Today's score and frozen copy are not carried."""
        ver = s.get("state_version", s.get("version"))
        nh = len(H)
        saved_rls = s["rls"]
        names = list(s.get("experts") or saved_rls.keys())
        rows = s["hedge"]
        if len(rows) != nh or any(len(r) != len(names) for r in rows):
            return False, f"unreadable: version {ver} expert weights do not match its {len(names)} experts", []
        rls, shared = {}, []
        for e in EXPERTS:
            r = self._rls_rows(saved_rls[e], e) if (e in saved_rls and e not in ("ridge", "trees")) else None
            if r is not None:
                shared.append(e)
            rls[e] = r if r is not None else [RLS(len(self.cols[e])) for _ in H]
        fl = self.hedge[0].share / self.hedge[0].m
        hedge = []
        for j in range(nh):
            w = np.full(len(EXPERTS), fl)
            for e in shared:
                if e in names:
                    v = float(rows[j][names.index(e)])
                    if not np.isfinite(v) or v < 0:
                        return False, f"unreadable: version {ver} weight for {e} is not a weight", []
                    w[EXPERTS.index(e)] = v
            if not np.isfinite(w.sum()) or w.sum() <= 0:
                return False, f"unreadable: version {ver} weights sum to zero", []
            hedge.append(w / w.sum())
        hedge_n = [int(n) for n in (s.get("hedge_n") or [0] * nh)][:nh]
        iv = self._iv_fields(s)
        if iv is None:
            return False, f"unreadable: version {ver} volatility fields are not finite", []
        self.rls = rls
        for h, w, n in zip(self.hedge, hedge, hedge_n + [0] * (nh - len(hedge_n))):
            h.w, h.n = w, n
        self.kappa, self.z80, self.obias, self.oscale = np.ones(nh), np.full(nh, Z80_START), np.zeros(nh), np.ones(nh)
        self._set_iv(iv)
        self.scale = dict(s.get("scale") or {})
        self.odw = float(s.get("odw", 0.5))
        self.oe_with, self.oe_without = (float(v) for v in (s.get("oe") or (1.0, 1.0)))
        self.alltime = dict(s.get("alltime") or self.alltime)
        self.extra_state = dict(s.get("extra_state") or {})
        self._saved_score = None
        self._saved_frozen = None
        self._saved_restarts = (s.get("day"), int(s.get("restarts") or 0))
        self._freeze()
        carried = [f"rls:{e}" for e in shared] + ["hedge", "iv_beta", "iv_res", "scale", "odw", "oe", "alltime"]
        return True, f"migrated v{ver} (kappa/z80 reset)", carried

    # load helpers: each returns None when the saved rows do not fit this lab
    def _vec(self, v):
        a = np.asarray(v, float)
        return a.copy() if a.shape == (len(H),) and np.isfinite(a).all() else None

    def _rls_rows(self, rows, e):
        if not isinstance(rows, list) or len(rows) != len(H):
            return None
        out = [RLS.from_json(d) for d in rows]
        k = len(self.cols[e])
        for r in out:
            if r.P.size == k * k:
                r.P = r.P.reshape(k, k)                  # an expert with no inputs saves P as an empty list
        if any(r.k != k or r.th.shape != (k,) or r.P.shape != (k, k) or not np.isfinite(r.th).all()
               or not np.isfinite(r.P).all() for r in out):
            return None
        return out

    def _hedge_rows(self, rows, names):
        if list(names) != list(EXPERTS) or not isinstance(rows, list) or len(rows) != len(H):
            return None
        out = []
        for w in rows:
            a = np.asarray(w, float)
            if a.shape != (len(EXPERTS),) or not np.isfinite(a).all() or a.min() < 0 or a.sum() <= 0:
                return None
            out.append(a / a.sum())
        return out

    def _iv_fields(self, s):
        b = float(s["iv_beta"])
        n = int(s["iv_beta_n"])
        res = float(s["iv_res"])
        sxx, sxy = s.get("_b_sxx"), s.get("_b_sxy")
        if sxx is None or sxy is None:                       # older file: rebuild the sums at the prior's size
            sxx = 2.5e5
            sxy = b * sxx
        sxx, sxy = float(sxx), float(sxy)
        if not all(np.isfinite(x) for x in (b, res, sxx, sxy)) or sxx <= 0:
            return None
        return b, n, res, sxx, sxy

    def _set_iv(self, iv):
        self.iv_beta, self.iv_beta_n, self.iv_res, self._b_sxx, self._b_sxy = iv

    def _frozen_from(self, fz):
        """The saved morning copy, or None when there is none or it does not fit."""
        if not isinstance(fz, dict) or not fz.get("day"):
            return None
        try:
            th = {}
            for e in EXPERTS:
                k = len(self.cols[e])
                rows = [np.asarray(a, float) for a in fz["th"][e]]
                if len(rows) != len(H) or any(a.shape != (k,) or not np.isfinite(a).all() for a in rows):
                    return None
                th[e] = rows
            w = [np.asarray(a, float) for a in fz["w"]]
            if len(w) != len(H) or any(a.shape != (len(EXPERTS),) or not np.isfinite(a).all() for a in w):
                return None
            kappa = self._vec(fz["kappa"])
            if kappa is None:
                return None
            return dict(th=th, w=w, kappa=kappa)
        except (KeyError, TypeError, ValueError):
            return None

    def _freeze(self):
        self.frozen = dict(th={e: [r.th.copy() for r in self.rls[e]] for e in EXPERTS},
                           w=[h.w.copy() for h in self.hedge], kappa=self.kappa.copy())

    def _new_score(self):
        z = lambda: np.zeros(len(H))
        return dict(n=z(), cov=z(), crps=z(), crps_still=z(), crps_frozen=z(), crps_plain=z(), width=z(), pin=z(),
                    dir_n=z(), dir_hit=z(), opin=z(), owidth=z(),
                    on=z(), ocov=z(), oerr=z(), oerr_naive=z(), oerr_decay=z(), obrier=z(), obrier_base=z(),
                    b_n=0, b_new=0.0, b_old=0.0, b_old_n=0, b_old_new=0.0, first_t=None)

    # ── one second ─────────────────────────────────────────────────────────────────────────────────────────────
    def step(self, inp):
        import time as _time
        c0 = _time.perf_counter()
        t = float(inp["t"])
        day = datetime.fromtimestamp(t, config.IST).date().isoformat()
        if day != self.day:
            self._new_day(day)
        if self.last_t is not None and t <= self.last_t:
            return self.last
        self.last_t = t
        self.engine = inp.get("engine")
        self.f_age = inp.get("fage")              # seconds since the futures quote arrived (live runner only)
        F = self._fut(inp, t)
        s = sod(t)
        in_session = OPEN_S <= s < CLOSE_S
        if F is not None and in_session:
            if int(t) % ORIGIN_EVERY == 0:
                self._mature_origins(t)
            if self.options:
                self._chain(inp, t)
                if self.simulate:
                    self._barriers(t)
                    if int(t) % ORIGIN_EVERY == 0:
                        self._mature_tickets(t)
            if s >= FIRST_ORIGIN_S and int(t) % ORIGIN_EVERY == 0 and self.n >= 600:
                self._origin(t, F)
            if self.simulate and int(t) % FULL_EVERY == 0 and self.chain is not None and self.n >= 600:
                f0 = _time.perf_counter()
                self._simulate(t, F)
                self.cost["full_ms"] = 0.8 * self.cost["full_ms"] + 0.2 * (_time.perf_counter() - f0) * 1e3
            if self.simulate and s >= FIRST_ORIGIN_S and int(t) % TICKET_EVERY == 0 and self.last and self.last.get("_sim"):
                self._ticket(t)
        self.cost["step_ms"] = 0.9 * self.cost["step_ms"] + 0.1 * (_time.perf_counter() - c0) * 1e3
        return self.last

    def _new_day(self, day):
        self.day = day
        self.ft[:] = np.nan
        self.fm[:] = np.nan
        self.n = 0
        self.vol = {120: None, 600: None, 1800: None}
        self.vwap_pv = self.vwap_v = 0.0
        self.last_ttq = None
        self.hi = self.lo = None
        self.ofi.clear()
        self.ofi_long.clear()
        self.imb_hist.clear()
        self.kf = B.Kalman()
        self.kf_slope = 0.0
        self.hw_ring.clear()
        self.hw_px.clear()
        self.hw_cum = [0.0, 0.0, 0.0]
        self.prev_q = None
        self.atm_hist.clear()
        self.opt_hist = {}
        self.origins.clear()
        self.tickets.clear()
        self.score = self._new_score()
        saved = getattr(self, "_saved_score", None)
        if saved and saved[0] == day and saved[1]:
            for k, v in saved[1].items():
                if k in self.score:
                    self.score[k] = np.array(v, float) if isinstance(self.score[k], np.ndarray) else v
        rs = getattr(self, "_saved_restarts", None)
        self.restarts = rs[1] + 1 if rs and rs[0] == day else 0          # a same-day load is a restart
        self.chain = None
        self.last = None
        self.fpath = None
        fz = getattr(self, "_saved_frozen", None)
        if fz and fz[0] == day:
            self.frozen = fz[1]                  # the true morning copy, so 'vs my morning self' keeps one reference
        else:
            self._freeze()
        self._saved_score = self._saved_frozen = self._saved_restarts = None

    # ── the future ─────────────────────────────────────────────────────────────────────────────────────────────
    def _fut(self, inp, t):
        fb, fa = float(inp.get("fb") or np.nan), float(inp.get("fa") or np.nan)
        fl = float(inp.get("fl") or np.nan)
        ok = np.isfinite(fb) and np.isfinite(fa) and fb > 0 and fa >= fb and (fa - fb) <= config.FUT_MID_MAX_SPREAD
        F = 0.5 * (fb + fa) if ok else (fl if np.isfinite(fl) and fl > 0 else None)
        if F is None:
            return None
        k = self.n % RING
        prev = self.fm[(self.n - 1) % RING] if self.n else np.nan
        self.ft[k], self.fm[k] = t, F
        self.n += 1
        # variance clocks from 5-s increments
        if self.n > 5:
            d5 = F - self.fm[(self.n - 6) % RING]
            if np.isfinite(d5):
                v = d5 * d5 / 5.0
                for hl in self.vol:
                    a = ewma_alpha(hl)
                    self.vol[hl] = v if self.vol[hl] is None else (1 - a) * self.vol[hl] + a * v
        # VWAP from traded volume
        q = float(inp.get("fv") or np.nan)
        if np.isfinite(q) and q > 0:
            if self.last_ttq is not None and q > self.last_ttq:
                dv = q - self.last_ttq
                px = fl if np.isfinite(fl) and fl > 0 else F
                self.vwap_pv += px * dv
                self.vwap_v += dv
            self.last_ttq = q
        self.hi = F if self.hi is None else max(self.hi, F)
        self.lo = F if self.lo is None else min(self.lo, F)
        # order-flow imbalance (Cont, Kukanov, Stoikov) from the best quotes and the depth totals
        bq, aq = float(inp.get("fbq") or np.nan), float(inp.get("faq") or np.nan)
        if ok and np.isfinite(bq) and np.isfinite(aq):
            if self.prev_q is not None:
                pb, pa, pbq, paq = self.prev_q
                e = (bq if fb >= pb else 0.0) - (pbq if fb <= pb else 0.0) - (aq if fa <= pa else 0.0) + (paq if fa >= pa else 0.0)
                self.ofi.append(e)
                self.ofi_long.append(e)
                sc1 = self.scale.get("ofi1")
                self.scale["ofi1"] = abs(e) if sc1 is None else 0.999 * sc1 + 0.001 * abs(e)
            self.prev_q = (fb, fa, bq, aq)
        self.kf_slope = self.kf.step(F, self.vol[600] if self.vol[600] else 1.0)
        self.imb_hist.append((bq - aq) / (bq + aq) if np.isfinite(bq) and np.isfinite(aq) and bq + aq > 0 else 0.0)
        hw = inp.get("hw")
        if hw is not None:                                       # heavyweights: weighted cumulative log returns
            px = np.asarray(hw, float)
            syms = inp.get("hw_syms")
            syms = tuple(syms) if syms is not None else None
            w_in = np.asarray(inp.get("hw_w") if inp.get("hw_w") is not None else [], float)
            b_in = np.asarray(inp.get("hw_bank") if inp.get("hw_bank") is not None else [], bool)
            if w_in.shape != px.shape or b_in.shape != px.shape:
                self._note(f"heavyweight inputs do not match ({px.size} prices, {w_in.size} weights): skipped")
                px = None
            elif self.hw_px and (self.hw_px[-1].shape != px.shape
                                 or (syms is not None and self.hw_syms is not None and syms != self.hw_syms)):
                self._note(f"heavyweight list changed ({len(self.hw_px[-1])} to {len(px)} stocks): breadth reset")
                self.hw_px.clear()
                self.hw_ring.clear()
                self.hw_cum = [0.0, 0.0, 0.0]
            if px is not None and syms is not None:
                self.hw_syms = syms
        if hw is not None and px is not None:
            if self.hw_px:
                last = self.hw_px[-1]
                okk = np.isfinite(px) & np.isfinite(last) & (px > 0) & (last > 0)
                w, bank = w_in, b_in
                r = np.where(okk, np.log(np.where(okk, px, 1.0) / np.where(okk, last, 1.0)), 0.0)
                for i_, m in enumerate((np.ones(len(px), bool), bank, ~bank)):
                    ww = w * m * okk
                    self.hw_cum[i_] += float((r * ww).sum() / ww.sum()) if ww.sum() > 0 else 0.0
            self.hw_px.append(px)
            self.hw_ring.append(tuple(self.hw_cum))
        self.fspread = (fa - fb) if ok else np.nan
        self.fbq, self.faq = bq, aq
        self.fbb, self.faa = fb, fa
        return F

    def tail(self, n):
        """The future's mid for the last n seconds recorded, oldest first (may hold NaN at gaps), or None."""
        if self.n == 0:
            return None
        m = min(n, self.n, RING)
        idx = (np.arange(self.n - m, self.n)) % RING
        return self.fm[idx]

    def hw_tail(self, n):
        """(index, bank, rest) cumulative log returns over the last n+1 seconds and the share of heavyweights up over
        60 s, or None without heavyweight data."""
        if len(self.hw_ring) < n + 1 or len(self.hw_px) < 61:
            return None
        a = np.array(self.hw_ring, float)[-(n + 1):]
        p0, p1 = self.hw_px[0], self.hw_px[-1]
        okk = np.isfinite(p0) & np.isfinite(p1) & (p0 > 0)
        up = float((p1[okk] > p0[okk]).mean()) if okk.any() else 0.5
        return a[:, 0], a[:, 1], a[:, 2], up

    def F_at(self, t):
        """The future's mid at second t (the nearest recorded second within 2 s), or None."""
        if self.n == 0:
            return None
        lo = max(0, self.n - RING)
        k = self.n - 1 - int(round(self.last_t - t))
        for kk in (k, k - 1, k + 1, k - 2, k + 2):
            if lo <= kk < self.n:
                j = kk % RING
                if abs(self.ft[j] - t) <= 2.0 and np.isfinite(self.fm[j]):
                    return float(self.fm[j])
        return None

    def v_sec(self):
        """Predicted variance per second of the future: three realised clocks and the implied volatility, the latter
        as implied variance per TRADING second on the business clock (clock.py). Without a clock (a year the holiday
        list does not cover) the implied part is left out rather than guessed."""
        parts, w = [], []
        for hl, ww in ((120, 0.35), (600, 0.30), (1800, 0.20)):
            if self.vol[hl] is not None:
                parts.append(self.vol[hl]); w.append(ww)
        c = self.chain
        if c is not None and np.isfinite(c.get("atm_iv", np.nan)):
            iv_s = CK.implied_var_per_trade_s(c["Fs"], c["atm_iv"], c["T"], self._clock()[1])
            if iv_s is not None:
                parts.append(iv_s); w.append(0.15)
        if not parts:
            return None
        return float(np.dot(parts, w) / np.sum(w))

    def _signals(self, t, F, v):
        """Raw signals at t, each scaled by its own running size; clipped. Order = self.sig_names."""
        def back(sec):
            x = self.F_at(t - sec)
            return (F - x) / math.sqrt(v * sec) if x is not None else 0.0
        mid = 0.5 * (self.fbb + self.faa) if np.isfinite(self.fspread) else F
        tot = (self.fbq + self.faq) if np.isfinite(self.fbq) and np.isfinite(self.faq) else np.nan
        imb = (self.fbq - self.faq) / tot if np.isfinite(tot) and tot > 0 else 0.0
        micro = ((self.faa * self.fbq + self.fbb * self.faq) / tot - mid) if np.isfinite(tot) and tot > 0 else 0.0
        micro = micro / max(0.5 * self.fspread, 0.05) if np.isfinite(self.fspread) else 0.0
        ofi = float(np.sum(self.ofi)) if self.ofi else 0.0
        basis = 0.0
        if self.chain is not None and len(self.atm_hist) > 12:
            b = np.array([h[1] - h[3] for h in self.atm_hist if len(h) > 3], float)
            if len(b) > 12:
                basis = (b[-1] - float(np.mean(b[-120:]))) / math.sqrt(v * 60.0)
        vw = (F - self.vwap_pv / self.vwap_v) / math.sqrt(v * 1800.0) if self.vwap_v > 0 else 0.0
        rng = (2.0 * (F - self.lo) / (self.hi - self.lo) - 1.0) if self.hi is not None and self.hi - self.lo > 1e-6 else 0.0
        raw = dict(r30=back(30), r120=back(120), r600=back(600), imb=imb, micro=micro, ofi30=ofi, basis=basis,
                   vwap=vw, rng=rng)
        x = []
        for nm in self.sig_names:
            val = raw[nm]
            if nm == "ofi30":                                    # quantity units: scale by its own running size
                sc = self.scale.get(nm)
                self.scale[nm] = abs(val) if sc is None else 0.999 * sc + 0.001 * abs(val)
                val = val / max(self.scale[nm], 1e-9)
            x.append(float(np.clip(val, -5.0, 5.0)))
        return np.array(x), raw

    def _expert_means(self, x, th=None, bx=None):
        """Standardised mean move per expert and horizon, (E, H). bx: the trained experts' outputs (ridge, trees)."""
        m = np.zeros((len(EXPERTS), len(H)))
        if bx is not None:
            m[EXPERTS.index("ridge")] = np.clip(bx[0], -M_CLIP, M_CLIP)
            m[EXPERTS.index("trees")] = np.clip(bx[1], -M_CLIP, M_CLIP)
        for i, e in enumerate(EXPERTS):
            c = self.cols[e]
            if not c:
                continue
            xe = x[list(c)]
            for j in range(len(H)):
                w = self.rls[e][j].th if th is None else th[e][j]
                m[i, j] = float(np.clip(w @ xe, -M_CLIP, M_CLIP))
        return m

    def _origin(self, t, F):
        v = self.v_sec()
        if v is None or v <= 0:
            return
        v_ref = self.vol[600] if self.vol[600] else v
        x, raw = self._signals(t, F, v)
        xf, named = B.features(self, t, F, v_ref)
        if self.collect is not None and xf is not None:
            self.collect.append((t, F, v_ref, xf))
        br = self.brain if xf is not None else None
        hh = np.array(H, float)
        if br is not None:
            sig = np.sqrt(self.kappa * br.vol(xf, v_ref))                  # trained multi-scale volatility model
            bx = br.drift(xf)
            qz = np.array([br.qz(j) for j in range(len(H))])              # (H, 5): fat-tailed standardised quantiles
        else:
            sig = np.sqrt(self.kappa * v * hh)                             # calibrated sd of the move, points
            bx = None
            qz = np.tile(np.array([-1.2816, -0.6745, 0.0, 0.6745, 1.2816]), (len(H), 1))
        m = self._expert_means(x, bx=bx)
        w = np.array([h.w for h in self.hedge]).T                          # (E, H)
        mu_e = m * sig                                                     # points
        mu = (w * mu_e).sum(0)
        sd = np.sqrt(sig ** 2 + (w * (mu_e - mu) ** 2).sum(0))
        mf = self._expert_means(x, self.frozen["th"], bx=bx)
        wf = np.array(self.frozen["w"]).T
        sigf = sig * np.sqrt(self.frozen["kappa"] / self.kappa)
        muf = (wf * mf * sigf).sum(0)
        cf = self.z80 / 1.2816                                             # conformal width factor
        lo80, hi80 = mu + cf * qz[:, 0] * sd, mu + cf * qz[:, 4] * sd
        close_left = CLOSE_S - sod(t)
        self.origins.append(dict(t=t, F=F, v=v, x=x, sig=sig, m=m, mu=mu, sd=sd, z80=self.z80.copy(), muf=muf, sigf=sigf,
                                 lo80=lo80, hi80=hi80, sd_plain=np.sqrt(v * hh),
                                 done=np.array([h > close_left for h in H])))   # past the close: never scored
        drivers = None
        if br is not None:
            wl = np.asarray(br.o["lin"][H5], float)[1:] * br.z(xf) * sig[H5]
            clock = {"tod", "tod2", "left", "dte", "exp", "lv30", "lv120", "lv600", "lv1800", "lviv", "lv120_600", "lv600_iv", "spr"}
            top = [i for i in np.argsort(-np.abs(wl)) if B.FEATS[i] not in clock][:4]     # market inputs, not the clock
            drivers = [(B.FEATS[i], float(wl[i])) for i in top]
        self.fpath = dict(t=t, F=F, mu=mu, sd=sd, sig=sig, mu_e=mu_e, w=w, raw=raw, v=v, qz=qz, cf=cf, named=named,
                          drivers=drivers, v_ref=v_ref)

    def _mature_origins(self, t):
        sc = self.score
        keep = deque()
        for o in self.origins:                                       # oldest first
            if o["done"].all():
                continue
            if t < o.get("due", o["t"] + H[0]):
                keep.append(o)
                continue
            for j, h in enumerate(H):
                if o["done"][j] or t < o["t"] + h:
                    continue
                o["done"][j] = True
                Fh = self.F_at(o["t"] + h)
                if Fh is None:
                    continue                                              # a gap: censored, nothing learned
                y = Fh - o["F"]
                s = o["sig"][j]
                # learn: expert coefficients on the standardised move, expert weights on CRPS, variance scale, band
                z = float(np.clip(y / s, -4.0, 4.0))
                w_ov = OVERLAP[h]
                for i, e in enumerate(EXPERTS):
                    if self.cols[e]:
                        self.rls[e][j].update(o["x"][list(self.cols[e])], z, w_ov)
                losses = crps_normal(o["m"][:, j] * s, s, y) / s
                self.hedge[j].update(losses, w_ov * 6.0)           # half a full step per minute of new outcome
                a = min(1.0, 12.0 * w_ov) / 300.0
                self.kappa[j] = float(np.clip((1 - a) * self.kappa[j] + a * self.kappa[j] * (y / s) ** 2, 0.2, 6.0))
                miss = not (o["lo80"][j] <= y <= o["hi80"][j])
                self.z80[j] = float(np.clip(self.z80[j] + 0.02 * (60.0 / h) * ((1.0 if miss else 0.0) - 0.2), 0.6, 3.5))
                # score
                sc["n"][j] += 1
                sc["cov"][j] += 0.0 if miss else 1.0
                sc["crps"][j] += float(crps_normal(o["mu"][j], o["sd"][j], y))
                sc["crps_still"][j] += float(crps_normal(0.0, s, y))
                sc["crps_frozen"][j] += float(crps_normal(o["muf"][j], o["sigf"][j], y))
                sc["crps_plain"][j] += float(crps_normal(0.0, o["sd_plain"][j], y))
                sc["width"][j] += float(o["hi80"][j] - o["lo80"][j])
                sc["pin"][j] += float(0.1 * max(y - o["lo80"][j], 0) + 0.9 * max(o["lo80"][j] - y, 0)
                                      + 0.9 * max(y - o["hi80"][j], 0) + 0.1 * max(o["hi80"][j] - y, 0))
                if abs(o["mu"][j]) >= 0.15 * o["sd"][j] and abs(y) >= 0.25 * o["sd"][j]:
                    sc["dir_n"][j] += 1
                    sc["dir_hit"][j] += 1.0 if np.sign(y) == np.sign(o["mu"][j]) else 0.0
                if sc["first_t"] is None:
                    sc["first_t"] = o["t"]
                self.alltime["fut_n"] = self.alltime.get("fut_n", 0) + 1
            if not o["done"].all():
                o["due"] = o["t"] + min(h for jj, h in enumerate(H) if not o["done"][jj])
                keep.append(o)
        self.origins = keep

    # ── the options ────────────────────────────────────────────────────────────────────────────────────────────
    def _chain(self, inp, t):
        """Quotes every second (for scoring); forward, volatility and greeks every FULL_EVERY seconds."""
        K = np.asarray(inp.get("K") if inp.get("K") is not None else [], float)
        exp = inp.get("expiry")
        if not len(K) or not exp:
            self.q = None
            self.chain = None
            return
        ob, oa, og = (np.asarray(inp[k], float) for k in ("ob", "oa", "og"))
        two = (ob > 0) & (oa >= ob) & (og <= FRESH_S)
        mid = np.where(two, 0.5 * (ob + oa), np.nan)
        self.q = dict(t=t, idx={float(k): j for j, k in enumerate(K)}, mid=mid, ob=ob, oa=oa)
        if int(t) % FULL_EVERY and self.chain is not None and self.chain.get("exp") == exp:
            return
        now = datetime.fromtimestamp(t, config.IST)
        F = self.fm[(self.n - 1) % RING]
        Fs = greeks.synthetic_forward(K, mid[:, 0], mid[:, 1], F)
        if not Fs or not np.isfinite(Fs):
            self.chain = None
            return
        Fs = float(Fs)
        T = greeks.years_to_expiry(exp, now)
        n = len(K)
        # one volatility per strike, from its out-of-the-money option (the cleaner quote); both rights use it
        callside = K >= Fs
        po = np.where(callside, mid[:, 0], mid[:, 1])
        with np.errstate(all="ignore"):
            otm = iv_newton(po, Fs, K, T, callside)
        ok = np.isfinite(otm)
        atm_iv = float(np.interp(Fs, K[ok], otm[ok])) if ok.sum() >= 2 else np.nan
        slope = np.nan
        near = ok & (np.abs(K - Fs) <= 3.5 * config.STRIKE_STEP)
        if near.sum() >= 3:
            lk = np.log(K[near] / Fs)
            slope = float(np.polyfit(lk, otm[near], 1)[0])
        IV = np.c_[otm, otm]
        IV[~np.isfinite(mid)] = np.nan
        Kc = np.r_[K, K]
        call = np.r_[np.ones(n, bool), np.zeros(n, bool)]
        iv2 = np.r_[IV[:, 0], IV[:, 1]]
        g = b76_greeks(np.full(2 * n, Fs), Kc, T, np.where(np.isfinite(iv2), iv2, 0.15), call)
        G = {k: np.c_[v[:n], v[n:]] for k, v in g.items()}
        self.chain = dict(t=t, K=K, ob=ob, oa=oa, og=og, mid=mid, Fs=Fs, F=F, T=T, iv=IV, atm_iv=atm_iv, slope=slope, g=G,
                          exp=exp, now=now, k_atm=int(np.argmin(np.abs(K - Fs))), basis=Fs - F)
        if np.isfinite(atm_iv):
            ka = int(np.argmin(np.abs(K - Fs)))
            strad = float(mid[ka, 0] + mid[ka, 1]) if np.isfinite(mid[ka, 0]) and np.isfinite(mid[ka, 1]) else None
            self._iv_learn(t, Fs, atm_iv, F, slope if np.isfinite(slope) else None, strad)
        for j, k in enumerate(K):
            for rr in (0, 1):
                if np.isfinite(mid[j, rr]):
                    dq = self.opt_hist.setdefault((float(k), rr), deque(maxlen=360))
                    dq.append((t, float(mid[j, rr]), Fs, float(ob[j, rr]), float(oa[j, rr])))

    def _iv_learn(self, t, Fs, atm_iv, F, slope=None, strad=None):
        """Intraday volatility drift and spot-vol beta from 60-s changes of the at-the-money IV (5-s cadence)."""
        self.atm_hist.append((t, Fs, atm_iv, F, slope, strad))
        if len(self.atm_hist) < 13:
            return
        t0, F0, iv0 = self.atm_hist[-13][:3]
        if abs((t - t0) - 60.0) > 3.0:
            return
        div, dF = atm_iv - iv0, Fs - F0
        a = ewma_alpha(180)                                   # about 15 minutes of 5-s updates
        self.iv_drift = (1 - a) * self.iv_drift + a * (div / 60.0)
        res = div - self.iv_drift * 60.0
        n = self.iv_beta_n
        lam = 0.999
        # one-coefficient recursive least squares, with a prior pulling to -4e-5 when moves are small
        if not hasattr(self, "_b_sxx"):
            self._b_sxx, self._b_sxy = 2.5e5, -10.0                     # prior: 250,000 pt^2 at -4e-5
        self._b_sxx = lam * self._b_sxx + dF * dF
        self._b_sxy = lam * self._b_sxy + dF * res
        self.iv_beta = float(np.clip(self._b_sxy / self._b_sxx, -3e-4, 1e-4))
        self.iv_beta_n = n + 1
        e = res - self.iv_beta * dF
        b = ewma_alpha(240)
        self.iv_res = float(np.sqrt((1 - b) * self.iv_res ** 2 + b * e * e / 60.0))

    def _candidates(self):
        """(index, rr, tag) of the contracts to simulate: the default rule's call and put, the at-the-money pair, and
        the account's held contract when the engine reports one."""
        c = self.chain
        band = band_for(self.day, c["exp"], c["now"])
        out, seen = [], set()
        eng = self.engine or {}
        exe = {}                                     # the engine's own pick, when it reports one: exactly that contract
        if (eng.get("expiry") in (None, c["exp"])) and time_ok(eng.get("t"), self.last_t):
            for r in eng.get("old_rows") or []:
                if r.get("tag") == "exe" and r.get("strike") is not None:
                    exe[0 if r.get("side") == "CE" else 1] = float(r["strike"])
        for rr in (0, 1):
            if rr in exe:
                j = np.where(np.abs(c["K"] - exe[rr]) < 1e-6)[0]
                k = int(j[0]) if len(j) else None
            else:
                k = pick(c["g"]["delta"][:, rr], c["mid"][:, rr], c["og"][:, rr], band)
            if k is not None and np.isfinite(c["iv"][k, rr]):
                out.append((k, rr, "buy")); seen.add((k, rr))
        for rr in (0, 1):
            k = c["k_atm"]
            if (k, rr) not in seen and np.isfinite(c["iv"][k, rr]):
                out.append((k, rr, "atm")); seen.add((k, rr))
        pos = (eng.get("pos") or {}) if time_ok(eng.get("t"), self.last_t, ENGINE_FRESH_S) else {}
        try:
            if pos.get("key") and pos.get("expiry") == c["exp"]:
                kk = int(np.argmin(np.abs(c["K"] - float(pos["strike"]))))
                rr = 0 if pos.get("rr") == "CE" else 1
                if abs(c["K"][kk] - float(pos["strike"])) < 1e-6 and np.isfinite(c["iv"][kk, rr]):
                    if (kk, rr) in seen:
                        out = [(a, b, "held" if (a, b) == (kk, rr) else tg) for a, b, tg in out]
                    else:
                        out.append((kk, rr, "held"))
        except (TypeError, ValueError, KeyError):
            pass
        return out

    def _simulate(self, t, F):
        c = self.chain
        fp = self.fpath
        self._held_attr_step(t)
        if fp is None or t - fp["t"] > 10:
            return
        sb = bool(getattr(self, "stage_b", PRICING_STAGE_B))
        k_bz = self._clock()[0] if sb else None
        k_bz = k_bz if k_bz is not None else 1.0                 # Stage B without a clock: the calendar clock
        close_left = CLOSE_S - sod(t)
        grid = np.array([g for g in list(range(GRID_S, 301, GRID_S)) + [600, 900, 1800] if g <= close_left], float)
        if not len(grid):
            return
        hs = np.array([h for h in H if h <= close_left], float)
        if not len(hs):                                   # the last minute before the close: nothing to forecast
            self.last = None
            return
        # mean and variance of the future's change on the grid, interpolated from the horizon forecasts
        Hh = np.r_[0.0, np.array(H, float)]
        # The recorded future lags the options' own forward (the drift experts lean on that lead), and option prices
        # already contain it. How much of the futures drift helps the PREMIUM forecast is learned from checked
        # forecasts: odw in [0, 1].
        mu = np.interp(grid, Hh, np.r_[0.0, fp["mu"] * self.odw])
        if sb and fp.get("cf") is not None:                      # Stage B: the paths carry the calibrated spread the
            var = np.interp(grid, Hh, np.r_[0.0, (np.asarray(fp["cf"], float) * fp["sd"]) ** 2])   # band shows
        else:
            var = np.interp(grid, Hh, np.r_[0.0, fp["sd"] ** 2])
        dmu = np.diff(np.r_[0.0, mu])
        dvar = np.maximum(np.diff(np.r_[0.0, var]), 0.0)
        half = self.n_paths // 2
        Z = self.rng.standard_normal((half, len(grid)))
        Z = np.r_[Z, -Z]
        br = self.brain
        dte_days = c["T"] * 365.0
        if br is not None:                                       # volatility is itself uncertain: each path draws its
            vv = br.volvol(H5)                                   # own volatility level (fat tails that persist)
            sv = np.exp(vv * self.rng.standard_normal(half) - vv * vv)
            sv = np.r_[sv, sv][:, None]
            iv_drift = 0.5 * (br.iv_drift(t, dte_days) + self.iv_drift)
            iv_res = 0.5 * (br.iv_res(dte_days) + self.iv_res)
        else:
            sv, iv_drift, iv_res = 1.0, self.iv_drift, self.iv_res
        dF = np.cumsum(dmu + sv * np.sqrt(dvar) * Z, axis=1)                    # (paths, grid)
        Zi = self.rng.standard_normal((half, len(grid)))
        Zi = np.r_[Zi, -Zi]
        if sb:
            # Stage B: no online IV drift in any path (it had negative skill at every horizon: L2-B4); the IV noise
            # has the measured sd at each horizon for this days-to-expiry bucket, not sqrt(t) of 60-s changes
            bucket = CK.dte_bucket(dte_days)
            iv_drift, iv_res = 0.0, None
            iv_noise = np.cumsum(CK.iv_increments(grid, bucket, self._iv_sd_table()) * Zi, axis=1)
            self.iv_used = dict(drift=0.0, res=None, noise=bucket, clock=k_bz, beta="sticky strike")
        else:
            dW = np.cumsum(np.sqrt(np.diff(np.r_[0.0, grid])) * Zi, axis=1)
            iv_noise = iv_res * dW
            self.iv_used = dict(drift=iv_drift, res=iv_res)
        hidx = [int(np.where(grid == h)[0][0]) for h in hs]
        bidx = np.where(grid <= 300)[0]
        out = []
        for k, rr, tag in self._candidates():
            K = float(c["K"][k])
            iv0 = float(c["iv"][k, rr])
            mid0, b0, a0 = float(c["mid"][k, rr]), float(c["ob"][k, rr]), float(c["oa"][k, rr])
            hs0 = max(0.5 * (a0 - b0), 0.05)
            call = rr == 0
            if sb:
                beta = 0.0                                       # sticky strike (L2-B8): a fixed strike's IV does not
            elif br is not None:                                 # slide with the at-the-money path
                beta = 0.5 * (br.iv_beta(math.log(K / c["Fs"]), dte_days) + self.iv_beta)
            else:
                beta = self.iv_beta
            dIV = beta * dF + iv_drift * grid + iv_noise
            Tg = CK.T_after(c["T"], grid, k_bz) if sb else np.maximum(c["T"] - grid / SPY, 1e-9)
            T_of = (lambda h: CK.T_after(c["T"], h, k_bz)) if sb else (lambda h: np.maximum(c["T"] - np.asarray(h, float) / SPY, 1e-9))
            full = tag != "atm"
            cols = np.arange(len(grid)) if full else np.array(hidx, int)
            P = b76(c["Fs"] + dF[:, cols], K, Tg[cols], np.maximum(iv0 + dIV[:, cols], 0.01), call)
            P = P + (mid0 - float(b76(c["Fs"], K, c["T"], iv0, call)))      # anchor the model to the quoted mid
            Ph = P[:, hidx] if full else P
            q = np.percentile(Ph, (10, 25, 50, 75, 90), axis=0)
            # learned corrections: bias (in band widths) and band scale, per horizon
            j_of = [H.index(int(h)) for h in hs]
            width = q[4] - q[0]
            q50 = q[2] + self.obias[j_of] * width
            q = q50 + self.oscale[j_of] * (q - q[2])
            bid_h = Ph - hs0
            ev = (bid_h / a0 - 1.0).mean(0) * 100.0
            pp = (bid_h > a0).mean(0)
            decay_only = b76(c["Fs"], K, T_of(hs), iv0, call) + (mid0 - float(b76(c["Fs"], K, c["T"], iv0, call)))
            decay_iv = b76(c["Fs"], K, T_of(hs), np.maximum(iv0 + iv_drift * hs, 0.01), call) \
                + (mid0 - float(b76(c["Fs"], K, c["T"], iv0, call)))
            # break-even move of the future for buying now at the ask and selling at the bid after h
            grid_dF = np.arange(-200.0, 200.5, 1.0)
            be = []
            for h in hs:
                val = b76(c["Fs"] + grid_dF, K, float(T_of(h)),
                          np.maximum(iv0 + iv_drift * h + beta * grid_dF, 0.01), call) \
                    + (mid0 - float(b76(c["Fs"], K, c["T"], iv0, call))) - hs0
                okk = val >= a0
                if call:
                    i = np.argmax(okk) if okk.any() else None
                else:
                    i = (len(okk) - 1 - np.argmax(okk[::-1])) if okk.any() else None
                be.append(None if i is None else float(grid_dF[i]))
            bar = None
            if full and len(bidx):
                bp = P[:, bidx] - hs0
                if sb:                                           # touches between grid points count too (L2-B10)
                    bar = CK.race(bp, mid0 - hs0, a0 * (1 + BARRIER), a0 * (1 - BARRIER), self.rng)
                else:
                    up = bp >= a0 * (1 + BARRIER)
                    dn = bp <= a0 * (1 - BARRIER)
                    fu = np.where(up.any(1), up.argmax(1), 10 ** 6)
                    fd = np.where(dn.any(1), dn.argmax(1), 10 ** 6)
                    bar = dict(up=float((fu < fd).mean()), down=float((fd < fu).mean()), neither=float(((fu == fd)).mean()))
            gk = {kk: float(v[k, rr]) for kk, v in c["g"].items()}
            j5 = H5
            attr = None
            if 300 <= close_left:
                m5, s5 = float(fp["mu"][j5]), float(fp["sd"][j5])
                # Stage B books the clock-driven decline as theta (business clock), with no IV-drift part in vega
                attr = dict(delta=gk["delta"] * m5, gamma=0.5 * gk["gamma"] * (s5 * s5 + m5 * m5),
                            vega=gk["vega"] * 100.0 * (beta * m5 + iv_drift * 300.0),
                            theta=gk["theta"] * (k_bz if sb else 1.0) * 5.0)
            whatif = None
            if full:                                             # what if the future moves by ... within ...: the bid then
                s5 = float(fp["sd"][H5])
                step = max(5.0, round(s5 / 5.0) * 5.0)
                moves = [-2 * step, -step, 0.0, step, 2 * step]
                anchor = mid0 - float(b76(c["Fs"], K, c["T"], iv0, call))
                cells = []
                for h in (60, 300, 900, 1800):
                    if h > close_left:
                        continue
                    row = []
                    for dm in moves:
                        val = float(b76(c["Fs"] + dm, K, float(T_of(h)), max(iv0 + iv_drift * h + beta * dm, 0.01), call)) + anchor - hs0
                        row.append([round(val, 2), round((val / a0 - 1.0) * 100.0, 1)])
                    cells.append(dict(h=h, row=row))
                whatif = dict(moves=moves, cells=cells)
            out.append(dict(k=k, rr=rr, tag=tag, strike=K, side="CE" if call else "PE", bid=b0, ask=a0, mid=mid0,
                            iv=iv0, greeks=gk, hs=[int(h) for h in hs], q=q.T.tolist(), ev=ev.tolist(), pp=pp.tolist(),
                            decay_only=decay_only.tolist(), decay_iv=decay_iv.tolist(), be=be, barrier=bar, attr=attr,
                            whatif=whatif, beta=beta,
                            dmu=[float(gk["delta"] * fp["mu"][H.index(int(h))]) for h in hs]))
        self.last = dict(_sim=True, t=t, opts=out, hs=[int(h) for h in hs],
                         pricing=("stage B: business clock" if sb else "calendar clock"))

    def _iv_sd_table(self):
        """The measured IV noise table (clock.load_iv_sd), read once a day; a read problem is noted, not raised."""
        cache = getattr(self, "_ivsd", None)
        if cache is None or cache[0] != self.day:
            table, flags, note = CK.load_iv_sd()
            if note:
                self._note(note)
            cache = self._ivsd = (self.day, table, flags)
        return cache[1]

    def _held_attr_step(self, t):
        """Held-position attribution (clock.HeldAttribution), every chain update while the account holds a contract
        of this chain: direction, convexity, business-clock decay, the strike's own IV change, residual. The sums live
        in extra_state, so they survive a restart; they are dropped when the position closes."""
        c = self.chain
        eng = self.engine or {}
        pos = (eng.get("pos") or {}) if time_ok(eng.get("t"), self.last_t, ENGINE_FRESH_S) else {}
        if not pos.get("key"):
            if eng and time_ok(eng.get("t"), self.last_t, ENGINE_FRESH_S):
                self.extra_state.pop("held_attr", None)          # a fresh report with no position: nothing is held
                self._hattr = None
            return
        if c is None or pos.get("expiry") != c["exp"]:
            return
        try:
            strike, rr = float(pos["strike"]), (0 if pos.get("rr") == "CE" else 1)
        except (TypeError, ValueError, KeyError):
            return
        j = np.where(np.abs(c["K"] - strike) < 1e-6)[0]
        if not len(j):
            return
        k = int(j[0])
        mid, bid, iv = float(c["mid"][k, rr]), float(c["ob"][k, rr]), float(c["iv"][k, rr])
        kk = self._clock()[0]
        if not (np.isfinite(mid) and np.isfinite(iv)) or kk is None:
            return
        g = {n: float(c["g"][n][k, rr]) for n in ("delta", "gamma", "vega", "theta")}
        g["theta_wall"] = g["theta"] * kk
        key = f"{pos['key']}|{strike:.0f}|{rr}"
        a = getattr(self, "_hattr", None)
        if a is None or a.key != key:
            saved = self.extra_state.get("held_attr")
            a = None
            if saved and saved.get("key") == key:
                try:
                    a = CK.HeldAttribution.from_json(saved)
                except (KeyError, TypeError, ValueError) as e:
                    self._note(f"held attribution not restored: {type(e).__name__}: {e}")
            if a is None:
                a = CK.HeldAttribution(key, pos.get("entry"), c["t"], c["Fs"], mid, iv, g)
            self._hattr = a
        a.step(c["t"], c["Fs"], mid, bid if bid > 0 else None, iv, g)
        self.extra_state["held_attr"] = a.to_json()

    # ── option tickets: scored when each horizon has passed ───────────────────────────────────────────────────
    def _quote(self, strike, rr):
        q = getattr(self, "q", None)
        if q is None:
            return None
        j = q["idx"].get(float(strike))
        if j is None or not np.isfinite(q["mid"][j, rr]):
            return None
        return float(q["mid"][j, rr]), float(q["ob"][j, rr]), float(q["oa"][j, rr])

    def _ticket(self, t):
        old = {}
        for r in ((self.engine or {}).get("old_rows") or []):
            old[(float(r.get("strike", 0)), 0 if r.get("side") == "CE" else 1)] = r
        for o in self.last["opts"]:
            if o["tag"] not in ("buy", "held"):
                continue
            od = old.get((o["strike"], o["rr"]))
            self.tickets.append(dict(t=t, strike=o["strike"], rr=o["rr"], ask=o["ask"], bid=o["bid"], mid=o["mid"],
                                     hs=o["hs"], q=o["q"], pp=o["pp"], dec=o["decay_only"], bar=o["barrier"],
                                     dmu=o["dmu"], odw=self.odw,
                                     old=(od.get("up"), od.get("down")) if od else None,
                                     done=[False] * len(o["hs"]), hi=-np.inf, lo=np.inf, first=None, bdone=False))

    def _barriers(self, t):
        """Every second, for tickets younger than 5 minutes: has the bid touched +5 % or -5 % of the ask yet?"""
        for k in reversed(self.tickets):
            if t > k["t"] + 300:
                break
            if k["first"] is not None:
                continue
            q = self._quote(k["strike"], k["rr"])
            if q is None:
                continue
            if q[1] >= k["ask"] * (1 + BARRIER):
                k["first"] = "up"
            elif q[1] <= k["ask"] * (1 - BARRIER):
                k["first"] = "down"

    def _mature_tickets(self, t):
        sc = self.score
        keep = deque()
        while self.tickets:
            k = self.tickets.popleft()
            q = self._quote(k["strike"], k["rr"])
            if not k["bdone"] and (k["first"] is not None or t > k["t"] + 300):
                k["bdone"] = True
                if k["bar"] is not None:
                    yu = 1.0 if k["first"] == "up" else 0.0
                    sc["b_n"] += 1
                    sc["b_new"] += (k["bar"]["up"] - yu) ** 2
                    if k["old"] and k["old"][0] is not None:
                        sc["b_old_n"] += 1
                        sc["b_old"] += (float(k["old"][0]) - yu) ** 2
                        sc["b_old_new"] += (k["bar"]["up"] - yu) ** 2
            for i, h in enumerate(k["hs"]):
                if k["done"][i] or t < k["t"] + h:
                    continue
                k["done"][i] = True
                if q is None or abs(t - (k["t"] + h)) > 5:
                    continue
                mid, bid, _ = q
                j = H.index(h)
                q10, _, q50, _, q90 = k["q"][i]
                cov = q10 <= mid <= q90
                sc["on"][j] += 1
                sc["ocov"][j] += 1.0 if cov else 0.0
                sc["owidth"][j] += (q90 - q10) / k["mid"] * 100.0
                sc["opin"][j] += (0.1 * max(mid - q10, 0) + 0.9 * max(q10 - mid, 0) + 0.9 * max(mid - q90, 0)
                                  + 0.1 * max(q90 - mid, 0)) / k["mid"] * 100.0
                sc["oerr"][j] += abs(mid - q50) / k["mid"] * 100.0
                sc["oerr_naive"][j] += abs(mid - k["mid"]) / k["mid"] * 100.0
                sc["oerr_decay"][j] += abs(mid - k["dec"][i]) / k["mid"] * 100.0
                win = 1.0 if bid > k["ask"] else 0.0
                sc["obrier"][j] += (k["pp"][i] - win) ** 2
                sc["obrier_base"][j] += (0.5 - win) ** 2
                self._win_sums(sc, j, k, i, win)
                # learn how much of the futures drift to use: the median with all of it against with none of it
                base = q50 - k["dmu"][i] * k["odw"]
                a2 = min(1.0, 15.0 / h * 4.0) / 150.0
                self.oe_with = (1 - a2) * self.oe_with + a2 * abs(mid - (base + k["dmu"][i])) / k["mid"] * 100.0
                self.oe_without = (1 - a2) * self.oe_without + a2 * abs(mid - base) / k["mid"] * 100.0
                self.odw = float(1.0 / (1.0 + math.exp(np.clip(40.0 * (self.oe_with / max(self.oe_without, 1e-9) - 1.0), -30, 30))))
                # learn the option band: bias in band widths, scale by coverage (target 80 %)
                w = max(q90 - q10, 1e-6)
                a = 1.0 / 200.0
                self.obias[j] = float(np.clip((1 - a) * self.obias[j] + a * 0.5 * (mid - q50) / w, -0.5, 0.5))
                self.oscale[j] = float(np.clip(self.oscale[j] + 0.02 * ((0.0 if cov else 1.0) - 0.2), 0.4, 3.0))
                self.alltime["opt_n"] = self.alltime.get("opt_n", 0) + 1
            if not (all(k["done"]) and k["bdone"]):
                keep.append(k)
        self.tickets = keep

    WIN_KEYS = ("oslots", "on_buy", "oslots_buy", "owin", "obrier_buy", "obrier_clim", "on_hi", "oslots_hi", "owin_hi")

    def _win_sums(self, sc, j, k, i, win):
        """The buy record at horizon j, one matured ticket at a time. Only 'buy'-tagged tickets count (a ticket made
        before its tag was stored counts as one). Checks are counted per 15-s slot, not per contract, because the
        call and the put of one slot share their outcome window. The base rate is causal: each ticket is scored
        against the win rate of the buy tickets that matured before it (a coin for the first one)."""
        for kk in self.WIN_KEYS:
            if kk not in sc:
                sc[kk] = np.zeros(len(H))
        last = self.__dict__.setdefault("_slot_last", {})
        if last.get(("all", j)) != k["t"]:
            last[("all", j)] = k["t"]
            sc["oslots"][j] += 1
        if k.get("tag", "buy") != "buy":
            return
        if last.get(("buy", j)) != k["t"]:
            last[("buy", j)] = k["t"]
            sc["oslots_buy"][j] += 1
        p0 = sc["owin"][j] / sc["on_buy"][j] if sc["on_buy"][j] > 0 else 0.5
        pp = float(k["pp"][i])
        sc["obrier_clim"][j] += (p0 - win) ** 2
        sc["obrier_buy"][j] += (pp - win) ** 2
        sc["on_buy"][j] += 1
        sc["owin"][j] += win
        if pp >= WILSON_PP:
            sc["on_hi"][j] += 1
            sc["owin_hi"][j] += win
            if last.get(("hi", j)) != k["t"]:
                last[("hi", j)] = k["t"]
                sc["oslots_hi"][j] += 1

    # ── the decay register ─────────────────────────────────────────────────────────────────────────────────────
    def _clock(self):
        """(k, tau_left_s, why) for the current chain on the business clock (clock.k_ts), once per chain update. k is
        None (and why says so) when the holiday calendar does not cover the expiry's year; that is noted once."""
        c = self.chain
        if c is None:
            return None, None, "no chain"
        memo = getattr(self, "_ck", None)
        if memo is not None and memo[0] == c["t"] and memo[1] == c["exp"]:
            return memo[2]
        r = CK.k_ts(c["now"], c["exp"], c["T"])
        if r[0] is None:
            self._note(f"business clock unavailable: {r[2]}")
        self._ck = (c["t"], c["exp"], r)
        return r

    def decay_rows(self, span=3):
        """The decay register around the money and the gamma rent, all on the business clock (clock.py):
        trade = calendar theta x k (decay a wall minute), lot_hour from it, be = sqrt(2 |trade| / Gamma), and the rent
        ratio = realised variance a second / the at-the-money call's implied variance a trading second (be^2 / 60).
        Without a clock these are None, never a guess."""
        c = self.chain
        if c is None:
            return [], None
        k_bz, tau, why = self._clock()
        sb = bool(getattr(self, "stage_b", PRICING_STAGE_B))
        rows = []
        k0 = c["k_atm"]
        for k in range(max(0, k0 - span), min(len(c["K"]), k0 + span + 1)):
            for rr in (0, 1):
                if not np.isfinite(c["iv"][k, rr]):
                    continue
                g = {kk: float(v[k, rr]) for kk, v in c["g"].items()}
                trade = CK.theta_wall(g["theta"], k_bz)                         # per wall (trading) minute
                if sb:                                                         # Stage B: the online IV trend is an
                    eff = trade                                                # observation only (L2-B4)
                else:
                    eff = g["theta"] + g["vega"] * 100.0 * self.iv_drift * 60.0   # calendar clock + today's IV trend
                m = self._measured_decay(float(c["K"][k]), rr)
                rows.append(dict(strike=float(c["K"][k]), side="CE" if rr == 0 else "PE", mid=r1(c["mid"][k, rr], 2),
                                 iv=r1(c["iv"][k, rr] * 100, 2), theta=r1(g["theta"], 3),
                                 trade=r1(trade, 3) if trade is not None else None, eff=r1(eff, 3) if eff is not None else None,
                                 measured=r1(m["value"], 3) if m and m["ok"] else None,
                                 measured_raw=r1(m["value"], 3) if m else None,
                                 measured_se=r1(m["se"], 3) if m and m["se"] is not None else None,
                                 gamma_pay=r1(m["gamma_pay"], 3) if m else None,
                                 lot_hour=r1(trade * 60.0 * config.LOT_SIZE, 0) if trade is not None else None,
                                 delta=r1(g["delta"], 2), atm=k == k0))
        # gamma rent on the at-the-money call: the per-minute move that pays for decay, against what moved
        g = {kk: float(v[k0, 0]) for kk, v in c["g"].items()}
        trade = CK.theta_wall(g["theta"], k_bz)
        be = CK.be_per_min(trade, g["gamma"])
        d10 = math.sqrt(self.vol[600] * 60.0) if self.vol[600] else None
        d30 = math.sqrt(self.vol[1800] * 60.0) if self.vol[1800] else None
        m = self._measured_decay(float(c["K"][k0]), 0)
        pay = m["gamma_pay"] if m else None
        rent = dict(be=r1(be, 2), d10=r1(d10, 2), d30=r1(d30, 2),
                    ratio=r1((d10 / be) ** 2, 2) if be and d10 else None,
                    ratio30=r1((d30 / be) ** 2, 2) if be and d30 else None,
                    gamma_pay=r1(pay, 3),                                  # 0.5 Gamma dF^2 a minute, measured: the
                    decay=r1(trade, 3) if trade is not None else None,     # rent's numerator, against its decay
                    clock=CK.label(k_bz), k=r1(k_bz, 3) if k_bz is not None else None, why=why)
        return rows, rent

    @staticmethod
    def _iv_steps(price, F, K, T, call, iters=8):
        """iv_newton with one time to expiry per price (the 30-minute history spans a changing T). NaN where it does
        not settle."""
        price, F, T = (np.asarray(x, float) for x in (price, F, T))
        T = np.maximum(T, 1e-9)
        intr = np.maximum(F - K, 0.0) if call else np.maximum(K - F, 0.0)
        ok = np.isfinite(price) & np.isfinite(F) & (price > intr + 1e-6) & (price < (F if call else K))
        sq = np.sqrt(T)
        sig = np.clip(np.sqrt(2.0 * math.pi / T) * np.where(ok, price, 1.0) / F, 0.02, 2.5)
        for _ in range(iters):
            model = b76(F, K, T, sig, call)
            d1 = (np.log(F / K) + 0.5 * sig * sig * T) / (sig * sq)
            vega = F * np.exp(-0.5 * d1 * d1) / SQ2PI * sq
            sig = np.clip(sig - (model - price) / np.maximum(vega, 1e-8), 0.01, 3.0)
        err = np.abs(b76(F, K, T, sig, call) - price)
        return np.where(ok & (err < np.maximum(1e-3 * price, 0.02)), sig, np.nan)

    def _measured_decay(self, strike, rr, window=1800, min_blocks=10):
        """Decay + IV change, measured from the quotes over the last 30 minutes (L2-B6, L1-B8). Per 5-s step, on the
        timestamps both rights of the strike were quoted: residual = d(mid) - Delta d(Fs) - 0.5 Gamma d(Fs)^2, with
        the greeks at the step's START (IV solved from that step's out-of-the-money mid, so a call and a put of one
        strike share it). The rate a minute is the sum of residuals over the sum of time; its standard error comes
        from 1-minute blocks. ok is False when the error exceeds the value (then the sentence is not said).
        gamma_pay = 0.5 Gamma d(Fs)^2 a minute: the movement's gain, the rent's numerator. None with too few steps."""
        c = self.chain
        qa, qb = self.opt_hist.get((strike, 0)), self.opt_hist.get((strike, 1))
        if c is None or not qa or not qb or self.last_t is None:
            return None
        lo = self.last_t - window
        # 13 Nov: the result depends only on the quotes inside the window and the chain's clock, which change every
        # 5 s, while the panel asks every second (and twice for the at-the-money call). An exact cache on those
        # inputs: 12 Nov's panel spent 90 % of its 250 ms here, re-solving the same implied vols.
        na = nb = 0
        for x in qa:
            if x[0] >= lo:
                break
            na += 1
        for x in qb:
            if x[0] >= lo:
                break
            nb += 1
        ck = (id(c), c["t"], c["T"], na, len(qa), qa[-1][0], nb, len(qb), qb[-1][0])
        cache = getattr(self, "_md_cache", None)
        if cache is None or cache.get("_ck") != (id(c), c["t"], c["T"]):
            cache = self._md_cache = {"_ck": (id(c), c["t"], c["T"])}
        key = (strike, rr, window, min_blocks) + ck
        if key in cache:
            return cache[key]
        out = cache[key] = self._measured_decay_calc(strike, rr, qa, qb, lo, min_blocks, cache, (strike,) + ck)
        return out

    def _measured_decay_calc(self, strike, rr, qa, qb, lo, min_blocks, cache, ivkey):
        c = self.chain
        got = cache.get(ivkey)
        if got is None:
            ta = {round(x[0], 1): x for x in qa if x[0] >= lo}
            tb = {round(x[0], 1): x for x in qb if x[0] >= lo}
            ts = sorted(set(ta) & set(tb))
            if len(ts) < 30:
                got = cache[ivkey] = (None,)
            else:
                t_ = np.array([ta[s][0] for s in ts], float)
                mc = np.array([ta[s][1] for s in ts], float)
                mp = np.array([tb[s][1] for s in ts], float)
                Fs = np.array([ta[s][2] for s in ts], float)
                T_ = np.maximum(c["T"] + (c["t"] - t_) / SPY, 1e-9)              # calendar time at each stamp
                with np.errstate(all="ignore"):
                    iv_c = self._iv_steps(mc, Fs, strike, T_, True)        # one solve per strike, both rights
                    iv_p = self._iv_steps(mp, Fs, strike, T_, False)
                got = cache[ivkey] = (ts, t_, mc, mp, Fs, T_, iv_c, iv_p)
        if got[0] is None:
            return None
        ts, t_, mc, mp, Fs, T_, iv_c, iv_p = got
        m = mc if rr == 0 else mp
        otm_call = strike >= Fs
        iv = np.where(otm_call, iv_c, iv_p)
        iv = np.where(np.isfinite(iv), iv, np.where(otm_call, iv_p, iv_c))
        g = b76_greeks(Fs, strike, T_, np.where(np.isfinite(iv), iv, 0.15), np.full(len(ts), rr == 0))
        dt = np.diff(t_)
        dF = np.diff(Fs)
        dm = np.diff(m)
        good = (dt > 3.5) & (dt < 7.5) & np.isfinite(iv[:-1]) & np.isfinite(dm) & np.isfinite(dF)
        if good.sum() < 24:
            return None
        gpay = 0.5 * g["gamma"][:-1] * dF * dF
        res = dm - g["delta"][:-1] * dF - gpay
        dt, res, gpay, t0 = dt[good], res[good], gpay[good], t_[:-1][good]
        tot = float(dt.sum())
        value = float(res.sum()) / tot * 60.0
        pay = float(gpay.sum()) / tot * 60.0
        blk = ((t0 - t0[0]) // 60.0).astype(int)
        rates = []
        for b in np.unique(blk):
            sel = blk == b
            if sel.sum() >= 6:
                rates.append(float(res[sel].sum()) / float(dt[sel].sum()) * 60.0)
        se = float(np.std(rates, ddof=1) / math.sqrt(len(rates))) if len(rates) >= min_blocks else None
        ok = se is not None and se <= abs(value)
        return dict(value=value, se=se, n=int(good.sum()), blocks=len(rates), gamma_pay=pay, ok=bool(ok))

    # ── what the panel shows ───────────────────────────────────────────────────────────────────────────────────
    def panel(self):
        t = self.last_t
        if t is None:
            return dict(ok=False, why="no data yet")
        now = datetime.fromtimestamp(t, config.IST)
        F = self.fm[(self.n - 1) % RING] if self.n else np.nan
        warm = self.n < 600 or self.fpath is None
        out = dict(v=VERSION, ok=True, t=t, day=now.date().isoformat(), now=now.strftime("%H:%M:%S"), warm=warm,
                   F=r1(F, 2), hi=r1(self.hi, 2), lo=r1(self.lo, 2),
                   vwap=r1(self.vwap_pv / self.vwap_v, 2) if self.vwap_v > 0 else None, lean_sd=LEAN_SD,
                   why=("warming up: the forecaster needs 10 minutes of quotes" if warm else None))
        # history for the chart: the future every 15 s, last 30 minutes
        hist = []
        lo = max(0, self.n - 1800)
        for kk in range(lo, self.n, 15):
            j = kk % RING
            if np.isfinite(self.fm[j]):
                hist.append([round(float(self.ft[j]) - t, 0), round(float(self.fm[j]), 2)])
        out["hist"] = hist
        fp = self.fpath
        if fp is not None and t - fp["t"] > 30:
            fp = None
        if fp is not None and not warm:
            path = []
            close_left = CLOSE_S - sod(t)
            # The forecast was made at the last origin (fp['F'], up to 30 s ago). For display it is carried to the
            # price on screen: every quantile moves by the change since then (direction is not called, so the move
            # so far is the honest centre). Scoring stays anchored to the origin.
            d = float(F) - float(fp["F"]) if np.isfinite(F) else 0.0
            for j, h in enumerate(H):
                if h > close_left:
                    continue
                mu, sd = float(fp["mu"][j]), float(fp["sd"][j])
                qq = fp["F"] + d + mu + float(fp["cf"][j]) * np.asarray(fp["qz"][j], float) * sd
                qq = np.maximum.accumulate(qq)
                up, up_txt = _up_from_quantiles(qq, float(F) if np.isfinite(F) else float(fp["F"]) + d)
                path.append(dict(h=h, mean=round(fp["F"] + d + mu, 2), mu=round(mu, 2), sd=round(sd, 2),
                                 q10=round(float(qq[0]), 2), q25=round(float(qq[1]), 2), q50=round(float(qq[2]), 2),
                                 q75=round(float(qq[3]), 2), q90=round(float(qq[4]), 2), up=up, up_txt=up_txt))
            out["path"] = path
            out["path_t"] = fp["t"]
            out["path_F"] = r1(fp["F"], 2)
            out["experts"] = [dict(name=e, w5=round(float(fp["w"][i, H5]), 3), mu5=round(float(fp["mu_e"][i, H5]), 2))
                              for i, e in enumerate(EXPERTS)]
            out["signals"] = {k: r1(v, 2) for k, v in fp["raw"].items()}
            out["vol_min"] = r1(math.sqrt(fp["v"] * 60.0), 2)
            nm = fp.get("named")
            if nm:
                vr, er = nm["vr"], nm["er300"]
                out["regime"] = dict(name=("trending" if (vr > 1.25 and er > 0.3) else "choppy" if vr < 0.8 else "mixed"),
                                     vr=r1(vr, 2), er=r1(er, 2), jump=bool(nm["jump120"] > 0.7),
                                     slope=r1(nm["slope120"], 2), kf=r1(nm["kf"], 2))
                # without a chain (or its at-the-money volatility) the brain's lviv is the 30-min realised move:
                # never shown as what options price
                # 'implied' is the at-the-money IV on the business clock (clock.py), the same number as the rent's
                # break-even move; the brain's own lviv input keeps its trained definition
                iv_ok = self.chain is not None and np.isfinite(self.chain.get("atm_iv", np.nan))
                imp = CK.implied_move_per_min(self.chain["Fs"], self.chain["atm_iv"], self.chain["T"],
                                              self._clock()[1]) if iv_ok else None
                out["volx"] = dict(implied=r1(imp, 2) if imp is not None else None,
                                   realised10=r1(math.sqrt(math.exp(nm["lv600"]) * 60.0), 2),
                                   realised2=r1(math.sqrt(math.exp(nm["lv120"]) * 60.0), 2),
                                   forecast5=r1(float(fp["sig"][H5]) / math.sqrt(5.0), 2),
                                   forecast30=r1(float(fp["sig"][-1]) / math.sqrt(30.0), 2))
                out["breadth"] = dict(up=r1(nm["up60"], 2), hw120=r1(nm["hw120"], 2), bank120=r1(nm["bank120"], 2),
                                      lead=r1(nm["hwlead30"], 2))
            out["brain"] = dict(ok=self.brain is not None, **({k: self.brain.meta.get(k) for k in ("trained_through", "sessions", "built", "hash")} if self.brain is not None else {}))
        c = self.chain
        if c is not None:
            out["chain"] = dict(Fs=r1(c["Fs"], 2), basis=r1(c["basis"], 2), atm_iv=r1(c["atm_iv"] * 100, 2),
                                slope=r1(c["slope"], 3), exp=c["exp"], dte_days=r1(c["T"] * 365.0, 2),
                                iv_drift_min=r1(self.iv_drift * 60.0 * 100.0, 4), iv_beta_100=r1(self.iv_beta * 100.0 * 100.0, 3))
            if getattr(self, "_dr", (None,))[0] != c["t"]:
                self._dr = (c["t"],) + self.decay_rows()
            out["decay"], out["rent"] = self._dr[1], self._dr[2]
            kb, tau, why = self._clock()
            out["clock"] = dict(name="business", k=r1(kb, 3) if kb is not None else None, label=CK.label(kb),
                                tau_s=r1(tau, 0) if tau is not None else None, why=why,
                                pricing=("business clock" if getattr(self, "stage_b", PRICING_STAGE_B) else "calendar clock"))
            ha = getattr(self, "_hattr", None)
            if ha is not None and "held_attr" in self.extra_state:   # dropped when a fresh report shows no position
                dte = c["T"] * 365.0
                sd = float(CK.iv_sd_at(max(ha.t - ha.t0, 0.0), CK.dte_bucket(dte), self._iv_sd_table()))
                out["held_attr"] = ha.view(sd_iv=sd)
        sim = self.last if self.last and self.last.get("_sim") else None
        if sim is not None and t - sim["t"] > STALE_SIM_S:
            sim = None                                           # an old simulation is not shown as a current forecast
        fa = getattr(self, "f_age", None)
        out["age"] = dict(fut=r1(fa, 1) if fa is not None and np.isfinite(fa) else None,
                          path=r1(t - self.fpath["t"], 0) if self.fpath is not None else None,
                          sim=r1(t - self.last["t"], 0) if self.last and self.last.get("_sim") else None)
        if fa is not None and (not np.isfinite(fa) or fa > STALE_FUT_S):
            out["stale"] = (f"the futures quote is {fa:.0f} s old" if np.isfinite(fa) else "no futures quote has arrived")
            for kk in ("path", "path_F", "regime", "volx", "breadth", "experts", "signals"):
                out.pop(kk, None)
            sim = None
        if sim is not None and not warm:
            opts = []
            for o in sim["opts"]:
                hist = [[round(a - t, 0), round(b, 2)] for a, b, _, _, _ in list(self.opt_hist.get((o["strike"], o["rr"]), []))[::3]]
                path = []
                for i, h in enumerate(o["hs"]):
                    q = o["q"][i]
                    path.append(dict(h=h, q10=r1(q[0], 2), q25=r1(q[1], 2), q50=r1(q[2], 2), q75=r1(q[3], 2), q90=r1(q[4], 2),
                                     ev=r1(o["ev"][i], 2), pp=r1(o["pp"][i], 3), decay=r1(o["decay_only"][i], 2),
                                     decay_iv=r1(o["decay_iv"][i], 2), be=r1(o["be"][i], 1)))
                gk = o["greeks"]
                opts.append(dict(strike=o["strike"], side=o["side"], tag=o["tag"], bid=r1(o["bid"], 2), ask=r1(o["ask"], 2),
                                 mid=r1(o["mid"], 2), iv=r1(o["iv"] * 100, 2), delta=r1(gk["delta"], 3), gamma=r1(gk["gamma"], 5),
                                 theta=r1(gk["theta"], 3), vega=r1(gk["vega"], 3), path=path, barrier=o["barrier"],
                                 attr={k: r1(v, 2) for k, v in (o["attr"] or {}).items()} or None, hist=hist,
                                 whatif=o.get("whatif"),
                                 old=self._old_for(o["strike"], o["rr"]), sim_age=round(t - sim["t"], 0)))
            opts.sort(key=lambda o: o["tag"] != "held")         # the account's contract first (stable otherwise)
            out["options"] = opts
        out["score"] = self._score_view()
        out["learn"] = dict(weights={e: [round(float(h.w[i]), 3) for h in self.hedge] for i, e in enumerate(EXPERTS)},
                            kappa=[round(float(k), 2) for k in self.kappa], z80=[round(float(z), 2) for z in self.z80],
                            obias=[round(float(b), 3) for b in self.obias], oscale=[round(float(s), 2) for s in self.oscale],
                            odw=round(self.odw, 3),
                            updates=int(sum(h.n for h in self.hedge)), alltime=self.alltime)
        self._account(out)
        out["held_view"] = self._held_view()
        days = self._days()
        out["record_days"] = days["summary"]
        out["cost_ms"] = {k: round(v, 2) for k, v in self.cost.items()}
        if not hasattr(self, "_earned_memo"):
            self._earned_memo = {}
        out["earned"] = earned(out, cross=days["cross"], memo=self._earned_memo)
        dh = out["earned"].get("dir_h") or {}
        for x in out.get("path") or []:
            x["draw_median"] = bool((dh.get(str(x["h"])) or {}).get("earned"))
        out["say"] = commentary(out)
        out["plain"] = plain(out)                     # 12 Nov: the same numbers in plain words
        self._feed_step(out)
        return out

    def _feed_step(self, out, hold_s=30.0):
        """12 Nov: the running feed of what changed (verdict, market, decay, ranges). A new verdict is written only after
        it has held for hold_s seconds, so a read that flickers for a second never fills the feed. Reset each day."""
        pl = out.get("plain") or {}
        if not pl.get("verdict"):
            pl["feed"] = list(getattr(self, "_feed", []) or [])
            return
        t, day = float(out["t"]), out.get("day")
        if getattr(self, "_feed_day", None) != day:
            self._feed_day, self._feed, self._feed_prev, self._feed_cand, self._feed_rcand = day, [], None, None, None
        en = out.get("earned") or {}
        ratio = (out.get("rent") or {}).get("ratio")
        cur = dict(verdict=pl["verdict"], regime=(out.get("regime") or {}).get("name"),
                   paid=None if ratio is None else float(ratio) >= 1.0,
                   range=((en.get("range_h") or {}).get("fut") or {}).get("300", {}).get("status"))
        prev = self._feed_prev
        if prev is not None and cur["verdict"]["word"] != prev["verdict"]["word"]:
            c = self._feed_cand
            if c is None or c[0] != cur["verdict"]["word"]:
                self._feed_cand = (cur["verdict"]["word"], t)
                cur = dict(cur, verdict=prev["verdict"])          # not yet: keep the old read until it holds
            elif t - c[1] < hold_s:
                cur = dict(cur, verdict=prev["verdict"])
            else:
                self._feed_cand = None
        else:
            self._feed_cand = None
        if prev is not None and cur["regime"] != prev.get("regime"):         # the market word: written once it holds 60 s
            rc = getattr(self, "_feed_rcand", None)
            if rc is None or rc[0] != cur["regime"]:
                self._feed_rcand = (cur["regime"], t)
                cur = dict(cur, regime=prev.get("regime"))
            elif t - rc[1] < 2 * hold_s:
                cur = dict(cur, regime=prev.get("regime"))
            else:
                self._feed_rcand = None
        else:
            self._feed_rcand = None
        ev = feed_events(prev, cur, out.get("now"))
        if ev:
            self._feed = (ev[::-1] + self._feed)[:FEED_MAX]
        self._feed_prev = cur
        pl["verdict"] = cur["verdict"]                            # the page shows the read that has held
        pl["feed"] = list(self._feed)

    def _account(self, out):
        """The account's state, only from an engine report at most ENGINE_FRESH_S old (engine time). An old report
        says the state is unknown and gives no held contract, so no buy case and no held tag are stated on it."""
        eng = self.engine
        if eng is None:
            out["account"] = None                                # offline: there is no account
            return
        if not time_ok(eng.get("t"), self.last_t, ENGINE_FRESH_S):
            import time as _t
            te = eng.get("t")
            why = ((eng.get("account") or {}).get("reason") or "account state unknown (engine not read)") if te is None \
                else f"account state unknown (engine not read for {max(0.0, _t.time() - float(te)):.0f} s)"
            out["account"] = dict(reason=why)
            out["account_known"] = False                         # earned() states no buy case on an unknown account
            return
        out["account"] = eng.get("account")
        pos = eng.get("pos") or {}
        if pos.get("key"):
            acc = eng.get("account") or {}
            out["held"] = dict(strike=pos.get("strike"), side=pos.get("rr"), expiry=pos.get("expiry"),
                               entry=pos.get("entry"), qty=pos.get("qty"), t_in=pos.get("t_in"),
                               book=pos.get("book") or acc.get("owner"), rules=pos.get("rules"))

    def _held_view(self):
        """apex.forecast_lab.held (the held-trade card), when it is installed; None otherwise or on its error."""
        global _HELD
        if _HELD is None:
            try:
                from . import held as _h
                _HELD = _h
            except ImportError:
                _HELD = False
        if not _HELD:
            return None
        try:
            return _HELD.view(self)
        except Exception as e:                                   # the card must never take the panel down: logged
            self._note(f"held card failed: {type(e).__name__}: {e}")
            return None

    def _days(self):
        """The daily record (data/forecast_lab/days/<day>.json), re-read every DAYS_REFRESH_S of wall time: the
        last 10 days' summaries for the panel and the cross-day evidence earned() needs. Unreadable files are
        skipped and noted in the runner's log."""
        import time as _t
        now = _t.time()
        cache = getattr(self, "_days_cache", None)
        if cache is not None and cache["day"] == self.day and now - cache["at"] < DAYS_REFRESH_S:
            return cache
        rows = read_days(getattr(self, "days_dir", None) or os.path.join(config.DATA_DIR, "forecast_lab", "days"),
                         note=self._note)
        cache = dict(at=now, day=self.day, summary=[day_summary(d) for d in rows[-10:]],
                     cross=cross_day(rows, self.day or ""))
        self._days_cache = cache
        return cache

    def _old_for(self, strike, rr):
        for r in ((self.engine or {}).get("old_rows") or []):
            if float(r.get("strike", 0)) == strike and (0 if r.get("side") == "CE" else 1) == rr:
                return dict(up=r.get("up"), down=r.get("down"))
        return None

    def _score_view(self):
        sc = self.score
        fut, opt = [], []
        z = np.zeros(len(H))
        g = lambda k: sc.get(k, z)
        rate = lambda a, b, j, d=3: r1(g(a)[j] / g(b)[j], d) if g(b)[j] else None
        for j, h in enumerate(H):
            n = sc["n"][j]
            fut.append(dict(h=h, n=int(n), cov=r1(sc["cov"][j] / n, 3) if n else None,
                            crps=r1(sc["crps"][j] / n, 4) if n else None, crps_plain=r1(sc["crps_plain"][j] / n, 4) if n else None,
                            width=r1(sc["width"][j] / n, 2) if n else None, pin=r1(sc["pin"][j] / n, 4) if n else None,
                            vol_skill=r1(1.0 - sc["crps_still"][j] / sc["crps_plain"][j], 3) if n and sc["crps_plain"][j] > 0 else None,
                            skill=r1(1.0 - sc["crps"][j] / sc["crps_still"][j], 3) if n and sc["crps_still"][j] > 0 else None,
                            skill_frozen=r1(1.0 - sc["crps"][j] / sc["crps_frozen"][j], 3) if n and sc["crps_frozen"][j] > 0 else None,
                            dir_n=int(sc["dir_n"][j]), dir_hit=r1(sc["dir_hit"][j] / sc["dir_n"][j], 3) if sc["dir_n"][j] else None,
                            lead_lag=h <= 180))                  # 1-3 min direction is mostly feed lead-lag (docs/48)
            on = sc["on"][j]
            opt.append(dict(h=h, n=int(on), cov=r1(sc["ocov"][j] / on, 3) if on else None,
                            pin=r1(sc["opin"][j] / on, 4) if on else None, width=r1(sc["owidth"][j] / on, 2) if on else None,
                            err=r1(sc["oerr"][j] / on, 2) if on else None, err_naive=r1(sc["oerr_naive"][j] / on, 2) if on else None,
                            err_decay=r1(sc["oerr_decay"][j] / on, 2) if on else None,
                            brier=r1(sc["obrier"][j] / on, 3) if on else None, brier_base=r1(sc["obrier_base"][j] / on, 3) if on else None,
                            slots=int(g("oslots")[j]), n_buy=int(g("on_buy")[j]), slots_buy=int(g("oslots_buy")[j]),
                            win=rate("owin", "on_buy", j), brier_buy=rate("obrier_buy", "on_buy", j, 4),
                            brier_clim=rate("obrier_clim", "on_buy", j, 4), n_hi=int(g("on_hi")[j]),
                            slots_hi=int(g("oslots_hi")[j]), win_hi=rate("owin_hi", "on_hi", j)))
        bar = dict(n=sc["b_n"], brier=r1(sc["b_new"] / sc["b_n"], 3) if sc["b_n"] else None)
        return dict(fut=fut, opt=opt, barrier=bar)


# ── plain-English commentary, built only from the numbers above ─────────────────────────────────────────────────────
_HELD = None                                    # apex.forecast_lab.held once imported; False when it is not installed
_PS = np.array([0.10, 0.25, 0.50, 0.75, 0.90])


def _up_from_quantiles(qq, F):
    """P(F_h > F) from the five forecast quantiles (q10, q25, q50, q75, q90), linear between them. Outside q10..q90
    it is only known to be above 90 % or below 10 %: (0.9, '>90 %') or (0.1, '<10 %')."""
    qq = np.asarray(qq, float)
    if not np.all(np.isfinite(qq)) or not np.isfinite(F):
        return None, None
    if F < qq[0]:
        return 0.9, ">90 %"
    if F > qq[4]:
        return 0.1, "<10 %"
    up = float(1.0 - np.interp(F, qq, _PS))
    return round(up, 3), f"{up * 100:.0f} %"


def _rs(x, d=1):
    return "–" if x is None else f"₹{x:,.{d}f}"


def _pts(x):
    return "–" if x is None else f"{x:+.1f} pts"


def _n(x, d=1):
    return "–" if x is None else f"{x:,.{d}f}"


def _pc(x):
    return "–" if x is None else f"{x * 100:.0f} %"


def _mins(h):
    return f"{h // 60} min"


def _wilson_lb(p, n, z=1.96):
    """Lower end of the 95 % Wilson interval for a rate p on n (independent) trials; 0 with no trials."""
    if p is None or n is None or n <= 0:
        return 0.0
    z2 = z * z
    c = p + z2 / (2.0 * n)
    s = z * math.sqrt(max(p * (1.0 - p) / n + z2 / (4.0 * n * n), 0.0))
    return max(0.0, (c - s) / (1.0 + z2 / n))


# ── the daily record: data/forecast_lab/days/<day>.json (written live at the close, back-filled by the walk) ─────────
# Format read here: {"day": "YYYY-MM-DD", "H": [60, ...], "forward": true, "score": {name: [one sum per H]}}, where the
# names are the Lab's score sums (n, cov, crps, crps_still, dir_n, dir_hit, on, ocov, oerr, oerr_naive, oerr_decay,
# on_buy, owin, obrier_buy, obrier_clim, ...). "sums" is accepted for "score". A day marked forward: false (fitted on
# itself) never counts as evidence.
def read_days(folder, note=None):
    import glob
    import json as _json
    out = []
    if not folder or not os.path.isdir(folder):
        return out
    for f in sorted(glob.glob(os.path.join(folder, "*.json"))):
        try:
            with open(f, encoding="utf-8") as fh:
                d = _json.load(fh)
            if not isinstance(d, dict) or not isinstance(d.get("score", d.get("sums")), dict):
                raise ValueError("no score sums")
            d.setdefault("day", os.path.splitext(os.path.basename(f))[0])
            out.append(d)
        except (OSError, ValueError, TypeError) as e:
            if note:
                note(f"daily record {os.path.basename(f)} skipped: {type(e).__name__}: {e}")
    out.sort(key=lambda d: str(d.get("day")))
    return out


def _day_val(d, name, h):
    sc = d.get("score", d.get("sums")) or {}
    hs = list(d.get("H") or H)
    v = sc.get(name)
    if v is None or h not in hs:
        return None
    try:
        x = float(v[hs.index(h)])
    except (IndexError, TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def day_summary(d):
    """One line of the 'record by day' table: the day's own checked numbers at 5 and 15 minutes."""
    def rt(a, b, h, dd=3):
        x, y = _day_val(d, a, h), _day_val(d, b, h)
        return round(x / y, dd) if x is not None and y else None
    bb = "obrier_buy" if _day_val(d, "obrier_buy", 300) is not None else "obrier"
    nb = "on_buy" if _day_val(d, "on_buy", 300) is not None else "on"
    return dict(day=str(d.get("day")), forward=d.get("forward", True) is not False, restarts=d.get("restarts"),
                cov5=rt("cov", "n", 300), cov15=rt("cov", "n", 900), dir5=rt("dir_hit", "dir_n", 300),
                dir5_n=_day_val(d, "dir_n", 300), brier5=rt(bb, nb, 300, 4), clim5=rt("obrier_clim", nb, 300, 4),
                opt5_n=_day_val(d, nb, 300))


def _boot_lb(num, den, B=2000, q=0.05, seed=20261112):
    """Day-block bootstrap: resample whole days, the q-quantile of sum(num)/sum(den). Deterministic."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    n = len(num)
    if den.sum() <= 0:
        return None
    point = float(num.sum() / den.sum())
    if point <= 0:                     # the pooled figure itself shows no skill: no resampling needed (never earns)
        return point
    idx = np.random.default_rng(seed).integers(0, n, (B, n))
    dd = den[idx].sum(1)
    st = np.where(dd > 0, num[idx].sum(1) / np.where(dd > 0, dd, 1.0), np.nan)
    st = st[np.isfinite(st)]
    return float(np.quantile(st, q)) if len(st) else None


def cross_day(days, today, B=2000):
    """The evidence across earlier forward days, per horizon. direction: the pooled share of clear calls right minus
    a coin's 0.5, and (when the days carry crps_still) the CRPS skill against 'no move'; buy: the Brier skill of the
    buy tickets' win chance against each day's causal base rate, and the share of days on which the middle premium
    forecast beat 'no change' by ERR_MARGIN. A claim needs BUY_MIN_DAYS days and a bootstrap lower bound above 0."""
    rows = [d for d in (days or []) if str(d.get("day", "")) < str(today or "9999") and d.get("forward", True) is not False]
    out = dict(days=len(rows), dir={}, buy={})
    for h in H:
        use = [d for d in rows if (_day_val(d, "dir_n", h) or 0) > 0 and _day_val(d, "dir_hit", h) is not None]
        r = dict(n_days=len(use), lb=None, crps_lb=None, ok=False)
        if len(use) >= BUY_MIN_DAYS:
            n_ = np.array([_day_val(d, "dir_n", h) for d in use])
            r["lb"] = _boot_lb(np.array([_day_val(d, "dir_hit", h) for d in use]) - 0.5 * n_, n_, B)
            ok = r["lb"] is not None and r["lb"] > 0
            cs = [(_day_val(d, "crps", h), _day_val(d, "crps_still", h)) for d in use]
            if all(a is not None and b is not None for a, b in cs):
                a, b = np.array(cs).T
                r["crps_lb"] = _boot_lb(b - a, b, B)
                ok = ok and r["crps_lb"] is not None and r["crps_lb"] > 0
            r["ok"] = bool(ok)
        out["dir"][str(h)] = r
    for h in BUY_H:
        use = []
        for d in rows:
            nb = "on_buy" if _day_val(d, "on_buy", h) is not None else "on"
            bb = "obrier_buy" if _day_val(d, "obrier_buy", h) is not None else "obrier"
            vals = (_day_val(d, bb, h), _day_val(d, "obrier_clim", h), _day_val(d, "oerr", h),
                    _day_val(d, "oerr_naive", h), _day_val(d, "on", h), _day_val(d, nb, h))
            if all(v is not None for v in vals) and vals[4] > 0 and vals[5] > 0:
                use.append(vals)
        r = dict(n_days=len(use), lb=None, err_share=None, ok=False)
        if len(use) >= BUY_MIN_DAYS:
            b, c, e, en_, on, _ = np.array(use, float).T
            r["lb"] = _boot_lb(c - b, c, B)
            r["err_share"] = round(float(np.mean(e / on < en_ / on - ERR_MARGIN)), 3)
            r["ok"] = bool(r["lb"] is not None and r["lb"] > 0 and r["err_share"] >= DAY_ERR_SHARE)
        out["buy"][str(h)] = r
    return out


def is_holding(p):
    """The account is in a trade: a held contract is on the panel, or a fresh engine report names a position."""
    return bool(any((o or {}).get("tag") == "held" for o in (p.get("options") or []))
                or p.get("held") or (p.get("account") or {}).get("pos"))


def _hyst(memo, day, key, ok):
    """Same-day hysteresis: a claim withdrawn after being earned stays withdrawn until the next day."""
    if memo is None or not day:
        return ok, False
    if memo.get("day") != day:
        memo.clear()
        memo.update(day=day, had=set(), out=set())
    if ok:
        if key in memo["out"]:
            return False, True
        memo["had"].add(key)
        return True, False
    if key in memo["had"]:
        memo["out"].add(key)
    return False, key in memo["out"]


def earned(p, cross=None, memo=None):
    """What the forecaster may state, decided only by its own checked forecasts, per claim and per horizon.
    Forecasts 5 s apart (futures) or 15 s apart (options) over h seconds share most of their outcome, so counts are
    cut down to roughly independent checks first (n x cadence / h; options per 15-s slot).

      range_h    {fut, opt}[h]: 'ok' when the 80 % range caught 72-88 % on at least 10 independent checks today,
                 'narrow' below, 'wide' above, 'unchecked' before 10 checks
      dir_h[h]   earned only with 20 independent clear calls, 60 % right, a score better than 'no move', a lean of at
                 least LEAN_SD sd now, and BUY_MIN_DAYS earlier forward days whose bootstrap lower bound is above 0
      buy_detail every condition for a buy case at 5 and 15 min: the account is not holding; 20 independent buy
                 checks; win-chance score at most min(coin, causal base rate) - 0.01; middle error below 'no change'
                 and 'decay only' by 0.1; among win chances of 55 % or more a realised rate whose 95 % lower bound is
                 at least 55 %; the cross-day record
    A withdrawn claim is not re-earned the same day (memo, kept by the Lab). The old keys (ranges, direction, buy,
    buy_h, ...) are the 5-minute answers. A futures record never earns an option statement."""
    sc = p.get("score") or {}
    fut = {x["h"]: x for x in (sc.get("fut") or []) if isinstance(x, dict) and "h" in x}
    opt = {x["h"]: x for x in (sc.get("opt") or []) if isinstance(x, dict) and "h" in x}
    path = {x["h"]: x for x in (p.get("path") or []) if isinstance(x, dict) and "h" in x}
    cross = cross or {}
    ndays = int(cross.get("days") or 0)
    day = p.get("day")
    holding = is_holding(p)
    unknown = p.get("account_known") is False                 # the engine report is old: the account may be holding

    def status(n, cov, every, h, slots=None):
        eff = (slots * TICKET_EVERY / float(h)) if slots is not None else (n or 0) * every / float(h)
        if eff < RANGE_MIN_CHECKS or cov is None:
            st = "unchecked"
        else:
            st = "ok" if RANGE_OK[0] <= cov <= RANGE_OK[1] else "narrow" if cov < RANGE_OK[0] else "wide"
        return dict(status=st, cov=cov, checks=round(eff, 1))

    range_h = dict(fut={str(h): status(x.get("n"), x.get("cov"), ORIGIN_EVERY, h) for h, x in fut.items()},
                   opt={str(h): status(x.get("n"), x.get("cov"), TICKET_EVERY, h,
                                       x.get("slots") if x.get("slots") else (x.get("n") or 0) / 2.0)
                        for h, x in opt.items()})
    dir_h = {}
    for h, x in fut.items():
        dn = (x.get("dir_n") or 0) * ORIGIN_EVERY / float(h)
        hit, skill = x.get("dir_hit"), x.get("skill")
        cd = (cross.get("dir") or {}).get(str(h)) or {}
        why = None
        if dn < DIR_MIN_CHECKS:
            why = f"needs {DIR_MIN_CHECKS} independent clear calls, have {dn:.0f}"
        elif (hit or 0) < DIR_HIT:
            why = f"needs {DIR_HIT * 100:.0f} % right, has {_pc(hit)}"
        elif skill is None or skill <= 0:
            why = "its score is not better than 'no move'"
        elif (cd.get("n_days") or 0) < BUY_MIN_DAYS:
            why = f"needs {BUY_MIN_DAYS} forward days, have {cd.get('n_days') or 0}"
        elif not cd.get("ok"):
            why = "the earlier days do not show skill"
        rec, withdrawn = _hyst(memo, day, f"dir:{h}", why is None)
        if why is None and withdrawn:
            why = "withdrawn earlier today"
        row = path.get(h)
        lean = None
        if row and row.get("mu") is not None and row.get("sd"):
            lean = "up" if row["mu"] >= LEAN_SD * row["sd"] else "down" if row["mu"] <= -LEAN_SD * row["sd"] else "flat"
        ok = bool(rec and lean in ("up", "down"))
        if rec and not ok:
            why = "no clear lean"
        dir_h[str(h)] = dict(earned=ok, record=bool(rec), hit=hit, checks=round(dn, 1), lean=lean, why=why,
                             lead_lag=h <= 180)
    buy_detail, buy_h, on = {}, [], {}
    for h in BUY_H:
        o = opt.get(h) or {}
        sb = o.get("slots_buy")
        eff = (sb * TICKET_EVERY / float(h)) if sb is not None else 0.0
        on[str(h)] = round(eff, 1)
        bb, clim = o.get("brier_buy"), o.get("brier_clim")
        target = min(0.25, clim) - BUY_MARGIN if clim is not None else None
        err, en_, ed = o.get("err"), o.get("err_naive"), o.get("err_decay")
        e_target = min(en_, ed) - ERR_MARGIN if en_ is not None and ed is not None else None
        n_hi = (o.get("slots_hi") or 0) * TICKET_EVERY / float(h)
        lb = _wilson_lb(o.get("win_hi"), n_hi)
        cd = (cross.get("buy") or {}).get(str(h)) or {}
        conds = [
            dict(name="checks", ok=eff >= BUY_MIN_CHECKS, have=round(eff, 1), need=BUY_MIN_CHECKS),
            dict(name="brier", ok=bb is not None and target is not None and bb <= target, have=bb,
                 need=round(target, 4) if target is not None else None, clim=clim, win=o.get("win")),
            dict(name="error", ok=err is not None and e_target is not None and err < e_target, have=err,
                 need=round(e_target, 2) if e_target is not None else None),
            dict(name="bucket", ok=lb >= WILSON_MIN, have=round(lb, 3), need=WILSON_MIN, n=round(n_hi, 1)),
            dict(name="days", ok=bool(cd.get("ok")), have=int(cd.get("n_days") or 0), need=BUY_MIN_DAYS,
                 lb=cd.get("lb"), err_share=cd.get("err_share")),
        ]
        rec, withdrawn = _hyst(memo, day, f"buy:{h}", all(c["ok"] for c in conds))
        ok = bool(rec and not holding and not unknown)
        if ok:
            buy_h.append(h)
        buy_detail[str(h)] = dict(earned=ok, record=bool(rec), withdrawn=bool(withdrawn), holding=holding,
                                  account_unknown=unknown, conds=conds)
    f5 = range_h["fut"].get("300") or dict(status="unchecked", checks=0.0)
    d5 = dir_h.get("300") or dict(earned=False, checks=0.0)
    return dict(ranges=f5["status"], range_checks=f5["checks"], direction=bool(d5["earned"]),
                dir_checks=d5["checks"], buy=bool(buy_h), buy_h=buy_h, opt_checks=on, holding=holding,
                account_unknown=unknown, days=ndays,
                lean_sd=LEAN_SD, range_h=range_h, dir_h=dir_h, buy_detail=buy_detail)


def _needs(bd, h):
    """'What a buy case needs' at holding time h, from exactly the conditions earned() checks, with their counts."""
    out = []
    for c in (bd or {}).get("conds") or []:
        if c["ok"]:
            continue
        if c["name"] == "checks":
            out.append(f"{c['need']} independent buy checks (have {c['have']:.0f})")
        elif c["name"] == "brier":
            out.append(f"a win-chance score of {_n(c['need'], 3)} or lower, the better of a coin and the base rate "
                       f"of {_pc(c.get('win'))} less 0.01 (now {_n(c['have'], 3)})")
        elif c["name"] == "error":
            out.append(f"a middle premium error under {_n(c['need'], 2)} %, 0.1 below 'no change' and 'decay only' "
                       f"(now {_n(c['have'], 2)} %)")
        elif c["name"] == "bucket":
            out.append(f"win chances of 55 % or more that came true often enough (lower bound {c['have'] * 100:.0f} %, "
                       f"needs 55 %, on {c['n']:.0f} independent checks)")
        elif c["name"] == "days":
            out.append(f"{c['need']} earlier forward days that show skill (have {c['have']})"
                       if c["have"] >= c["need"] else f"{c['need']} forward days on record (have {c['have']})")
    if (bd or {}).get("withdrawn"):
        out.append("a new day: it was withdrawn earlier today")
    return out


def commentary(p):
    """Sections of short sentences. Every sentence is either a measured fact (a quote, a Greek, a repricing) or a
    forecast the forecaster has earned at that horizon by its own checked record (earned()). What is not earned is
    not said: the forecaster states 'no call', or that a range is unreliable today. While the account holds a
    position no buy case is assessed. Display only: it places no order and changes no book."""
    say = dict(now=[], next=[], decay=[], do=[], change=[], doing=[], account=[], label=["Verdict"])
    if not p.get("ok"):
        say["now"].append("No forecast: " + str(p.get("why")))
        return say
    if p.get("stale"):
        say["now"].append(f"No forecast: {p['stale']}. I do not forecast from an old price.")
        return say
    if p.get("warm"):
        say["now"].append(p.get("why") or "Warming up.")
    en = p.get("earned") or earned(p)
    holding = is_holding(p) or bool(en.get("holding"))
    if holding:
        say["label"] = ["Forecaster's view (display only)"]
    rh, dh = en.get("range_h") or {}, en.get("dir_h") or {}

    def rst(kind, h):
        return (rh.get(kind) or {}).get(str(h)) or dict(status="unchecked", cov=None, checks=0.0)

    def dir_rec(h):
        d = dh.get(str(h))
        return bool(d.get("record")) if d else bool(en.get("direction")) and h == 300

    F = p.get("F")
    path = p.get("path") or []
    by_h = {x["h"]: x for x in path}
    if F is not None and path:
        say["now"].append(f"Nifty futures {F:,.1f}.")
        x5 = by_h.get(300)
        if x5:
            if dir_rec(300):
                mu, sd = x5.get("mu"), x5.get("sd") or 0.0
                lean = None if mu is None else "up" if mu >= LEAN_SD * sd else "down" if mu <= -LEAN_SD * sd else None
                say["now"].append(f"Direction over 5 minutes: {lean}, {mu:+.1f} points expected. This call is earned: "
                                  f"see my record below." if lean else "Direction: no clear lean.")
            else:
                say["now"].append("Direction: no call.")
        rg, vx = p.get("regime"), p.get("volx")
        if rg and rg.get("name") in ("trending", "choppy", "mixed"):
            txt = {"trending": "The market is trending: moves are carrying through.",
                   "choppy": "The market is choppy: moves are being reversed.",
                   "mixed": "The market is neither trending nor reversing clearly."}[rg["name"]]
            say["now"].append(txt + (" A sudden jump happened in the last two minutes." if rg.get("jump") else ""))
        if vx and vx.get("implied") and vx.get("forecast5") and vx.get("realised10") is not None:
            rel = vx["forecast5"] / vx["implied"]
            say["now"].append(f"Options are priced for {vx['implied']:.1f} points a minute. The market delivered "
                              f"{vx['realised10']:.1f} over the last 10 minutes. I forecast {vx['forecast5']:.1f} for "
                              f"the next 5: " + ("more movement than options price." if rel > 1.1 else
                                                 "less movement than options price." if rel < 0.9 else
                                                 "about what options price."))
        for h in (60, 300, 900, 1800):
            x = by_h.get(h)
            if not x or x.get("q10") is None or x.get("q90") is None:
                continue
            st = rst("fut", h)
            if st["status"] == "ok":
                d_ok = bool((dh.get(str(h)) or {}).get("earned")) if dh else bool(en.get("direction"))
                say["next"].append(f"In {_mins(h)}: futures between {x['q10']:,.1f} and {x['q90']:,.1f} (80 %)"
                                   + (f", most likely {x['mean']:,.1f}." if d_ok and x.get("mean") is not None else "."))
            elif st["status"] == "unchecked":
                say["next"].append(f"In {_mins(h)}: range not checked enough yet today ({st['checks']:.0f} of "
                                   f"{RANGE_MIN_CHECKS} checks, aimed at 80 %).")
            else:
                say["next"].append(f"In {_mins(h)}: range unreliable today (caught {_pc(st['cov'])} on "
                                   f"{st['checks']:.0f} checks, aimed at 80 %).")
    opts = p.get("options") or []
    cands = [o for o in opts if o.get("tag") == "buy"]
    held = [o for o in opts if o.get("tag") == "held"]
    so5 = rst("opt", 300)
    for o in held + cands:
        x5 = {x["h"]: x for x in o.get("path") or []}.get(300)
        if not x5:
            continue
        who = "Held " if o["tag"] == "held" else ""
        head = f"{who}{o['strike']:.0f} {o['side']} (bid {_rs(o.get('bid'))}, ask {_rs(o.get('ask'))}): in 5 minutes "
        if x5.get("q10") is None or x5.get("q90") is None:
            rng = "no premium range"
        elif so5["status"] == "ok":
            rng = f"between {_rs(x5['q10'])} and {_rs(x5['q90'])} (80 %)"
        elif so5["status"] == "unchecked":
            rng = f"the premium range is not checked enough yet today ({so5['checks']:.0f} of {RANGE_MIN_CHECKS} checks)"
        else:
            rng = f"the premium range is unreliable today (caught {_pc(so5['cov'])} on {so5['checks']:.0f} checks, aimed at 80 %)"
        say["next"].append(head + rng + f"; time decay alone would make it {_rs(x5.get('decay'))}.")
    if not holding:
        for o in cands[:2]:
            wi = o.get("whatif")
            if wi and wi.get("cells"):
                c5 = next((c for c in wi["cells"] if c["h"] == 300), None)
                if c5:
                    mv, row = wi["moves"], c5["row"]
                    say["next"].append(f"Repricing, {o['strike']:.0f} {o['side']} bought now at {_rs(o.get('ask'))} "
                                       f"(sold at the bid), in 5 minutes: futures {mv[0]:+.0f} gives {row[0][1]:+.1f} %, "
                                       f"flat gives {row[2][1]:+.1f} %, futures {mv[4]:+.0f} gives {row[4][1]:+.1f} %.")
    rows, rent = p.get("decay") or [], p.get("rent") or {}
    atm = [r for r in rows if r.get("atm")]
    if atm:
        a = atm[0]
        ck = p.get("clock") or {}
        if a.get("trade") is not None and a.get("theta") is not None:
            lot = "–" if a.get("lot_hour") is None else f"₹{abs(a['lot_hour']):,.0f}"
            say["decay"].append(f"At the money ({a['strike']:.0f} {a['side']}, {_rs(a.get('mid'), 2)}): time takes "
                                f"{abs(a['trade']):.2f} a minute on the {ck.get('label') or 'trading'} clock "
                                f"({lot} per lot per hour), {abs(a['theta']):.3f} on the calendar clock.")
        elif ck.get("why"):
            say["decay"].append(f"No decay rate a minute: {ck['why']}.")
        if a.get("measured") is not None and "measured_raw" in a:   # None when its standard error exceeds it
            se = a.get("measured_se")
            say["decay"].append(f"Decay + IV change, measured from the quotes over the last 30 minutes after the futures' "
                                f"move and its gamma: {a['measured']:+.2f} a minute"
                                + (f" (give or take {se:.2f})." if se is not None else "."))
        elif a.get("measured") is not None:                      # a payload from before 12 Nov: the old regression
            say["decay"].append(f"Premium change not explained by the futures (decay + gamma + IV), last 30 minutes: "
                                f"{a['measured']:+.2f} a minute.")
    if rent.get("be") and rent.get("d10") and rent.get("ratio") is not None:
        r = rent["ratio"]
        verdict = ("movement is paying for decay" if r >= 1.0 else "movement is not paying for decay")
        say["decay"].append(f"To pay for decay the market must move {rent['be']:.1f} points a minute. Over the last 10 "
                            f"minutes it moved {rent['d10']:.1f} (ratio {r:.2f}, break-even 1.00): {verdict}.")
        if rent.get("gamma_pay") is not None and rent.get("decay") is not None:
            say["decay"].append(f"Measured from the quotes, movement paid {rent['gamma_pay']:.2f} a minute through gamma "
                                f"against {abs(rent['decay']):.2f} of decay.")
    # the verdict (display only)
    bd = en.get("buy_detail") or {}
    if holding:
        hd = p.get("held") or {}
        h0 = held[0] if held else {}
        strike = hd.get("strike") if hd.get("strike") is not None else h0.get("strike")
        side = hd.get("side") or h0.get("side") or ""
        book = hd.get("book") or (p.get("account") or {}).get("owner")
        what = f"the {float(strike):.0f} {side}" if strike is not None else "a position"
        say["do"].append(f"Holding {what}: the account's trade, held by a book" + (f" ({book})" if book else "") +
                         f". Its exit belongs to that book's own rules; no new buy case is assessed while a position "
                         f"is open.")
    elif p.get("account_known") is False or en.get("account_unknown"):
        say["do"].append("The account's state is unknown (the engine report is old), so no buy case is assessed.")
    else:
        best = None
        if en.get("buy"):
            for o in cands:
                for x in o.get("path") or []:
                    if x["h"] in (en.get("buy_h") or []) and x.get("ev") is not None and (best is None or x["ev"] > best[1]["ev"]):
                        best = (o, x)
        if best and best[1]["ev"] > 1.0 and (best[1].get("pp") or 0) > 0.55:
            o, x = best
            say["do"].append(f"Buy case: the {o['strike']:.0f} {o['side']} at {_rs(o.get('ask'))}, held {_mins(x['h'])}: "
                             f"expected {x['ev']:+.1f} % after the spread (bought at the ask, sold at the bid), win chance "
                             f"{x['pp'] * 100:.0f} %. My option record at this holding time beats its base rate today "
                             f"and across {en.get('days', 0)} earlier forward days taken together.")
        elif cands:
            say["do"].append("Flat. There is no buy case.")
            x5f = by_h.get(300)
            f_ok = rst("fut", 300)["status"] == "ok"
            for o in cands:
                x5 = {x["h"]: x for x in o.get("path") or []}.get(300)
                if not (x5 and x5.get("be") is not None):
                    continue
                need = x5["be"]
                head = (f"The {o['strike']:.0f} {o['side']} needs futures {_pts(need)} within 5 minutes to pay after "
                        f"decay and the spread (bought at the ask, sold at the bid). ")
                if f_ok and x5f and F is not None and x5f.get("q90") is not None and x5f.get("q10") is not None:
                    edge = (x5f["q90"] - F) if need >= 0 else (x5f["q10"] - F)
                    inside = abs(need) <= abs(edge)
                    say["do"].append(head + f"My 80 % range reaches {_pts(edge)}: the move is "
                                     + ("inside the range, and its direction is not called." if inside and not dir_rec(300)
                                        else "inside the range." if inside else "outside the range."))
                else:
                    st5 = (rst("fut", 300) or {}).get("status")
                    say["do"].append(head + ("My 5-minute range is not checked enough yet today, so I do not compare it."
                                             if st5 == "unchecked" else
                                             "My 5-minute range is not reliable today, so I do not compare it."))
            for h in BUY_H:
                nd = _needs(bd.get(str(h)), h)
                if nd:
                    say["change"].append(f"A buy case held {_mins(h)} needs " + "; ".join(nd) + ".")
    # the record
    sc = (p.get("score") or {}).get("fut") or []
    s5 = next((x for x in sc if x.get("h") == 300), {})
    if s5.get("n"):
        st = {"ok": "on target", "narrow": "too narrow, being widened", "wide": "too wide, being narrowed",
              "unchecked": "too few checks to judge"}.get(en.get("ranges"), "too few checks to judge")
        say["doing"].append(f"Ranges, 5 minutes: {s5['n']} checked today (about {en.get('range_checks', 0):.0f} "
                            f"independent). The 80 % range caught {_pc(s5.get('cov'))}: {st}.")
        other = []
        for h in (60, 900, 1800):
            r = (rh.get("fut") or {}).get(str(h))
            if r and r.get("cov") is not None:
                other.append(f"{_mins(h)} caught {_pc(r['cov'])} on {r['checks']:.0f} check{'' if round(r['checks']) == 1 else 's'}"
                             + ("" if r["status"] == "ok" else f" ({'too few to judge' if r['status'] == 'unchecked' else 'not stated as 80 %'})"))
        if other:
            say["doing"].append("Other ranges today: " + "; ".join(other) + ".")
        d5 = dh.get("300") or {}
        if s5.get("dir_n"):
            say["doing"].append(f"Direction, 5 minutes: {_pc(s5.get('dir_hit'))} right on {s5['dir_n']} clear calls "
                                f"(about {en.get('dir_checks', 0):.0f} independent). " +
                                ("Earned." if d5.get("record", en.get("direction")) else
                                 f"Not earned: {d5['why']}." if d5.get("why") else "Not earned."))
        else:
            say["doing"].append("Direction, 5 minutes: no clear calls yet. Not earned.")
        sf = s5.get("skill_frozen")
        if sf is not None:
            say["doing"].append(f"Learning since the open: {abs(sf) * 100:.1f} % {'better' if sf >= 0 else 'worse'} "
                                f"than this morning's frozen copy.")
    else:
        say["doing"].append("Nothing is checked yet today: a 5-minute forecast is checked 5 minutes after it is made.")
    so = next((x for x in ((p.get("score") or {}).get("opt") or []) if x.get("h") == 300), {})
    if so.get("n"):
        txt = (f"Option premiums, 5 minutes: {so['n']} checked (about {so5['checks']:.0f} independent). The 80 % range "
               f"caught {_pc(so.get('cov'))}. Middle forecast off by {_n(so.get('err'), 1)} % against "
               f"{_n(so.get('err_naive'), 1)} % for 'no change' and {_n(so.get('err_decay'), 1)} % for 'decay only'.")
        if so.get("brier_buy") is not None:
            txt += (f" Win chance on the buy contracts scored {_n(so['brier_buy'], 3)} against "
                    f"{_n(so.get('brier_clim'), 3)} for the base rate of {_pc(so.get('win'))} (lower is better).")
        rec5 = (bd.get("300") or {}).get("record") if bd else 300 in (en.get("buy_h") or [])
        say["doing"].append(txt + (" Earned." if rec5 else " Not earned."))
    nd = int(en.get("days") or 0)
    if nd < BUY_MIN_DAYS:
        say["doing"].append(f"Forward days on record: {nd}. Direction and buy claims need {BUY_MIN_DAYS}, so they cannot "
                            f"appear yet. That is the honest state, not a fault.")
    br = p.get("brain") or {}
    if br.get("ok"):
        say["doing"].append(f"Trained models: fitted through {br.get('trained_through')} on {br.get('sessions')} sessions.")
    acc = p.get("account") or {}
    if acc.get("reason"):
        say["account"].append(f"The account (Conductor): {acc['reason']}. The Conductor does not read this panel.")
    return say


# ── 12 Nov evening (owner: "not at all intuitive"): the panel in plain words ─────────────────────────────────────────
# Four short rows a trader can read at a glance, built only from the numbers above: how far Nifty usually moves next,
# which way it leans for the next two minutes (with how often that lean has been right), what the held trade or a
# fresh buy needs, and whether movement is paying for time decay. The full commentary stays below it, unchanged.
# Measured out of sample (data/forecast_lab/walk_forward.json, 11 sessions 27 Oct - 11 Nov, models fitted only on
# earlier days): the strongest fifth of leans were right this often. Beyond 5 minutes the lean is a coin toss.
PAST_LEAN_HIT = {60: 0.67, 120: 0.60, 180: 0.59, 300: 0.55}
PAST_RANGE_CAUGHT = 0.80                       # the same test: the 80 % futures ranges caught 77-82 % on unseen days
PLAIN_LEAN_H = 120                             # the lean is stated for 2 minutes (1 minute when 2 is past the close)


def _half(x, F):
    """Half the 80 % range in points, or None."""
    if not x or x.get("q10") is None or x.get("q90") is None:
        return None
    return max(0.0, (float(x["q90"]) - float(x["q10"])) / 2.0)


def plain(p):
    """{head, rows, verdict, ladder, board}: the panel in plain words (rows), plus on a live panel the forecaster's
    read, the Nifty ladder and the option board. tone is good / warn / bad / none (colour only)."""
    res = _plain_rows(p)
    if res["rows"]:
        res.update(verdict=verdict(p), ladder=ladder(p), board=board(p))
    return res


def _plain_rows(p):
    """{head, rows: [{k, title, text, note, tone}]}."""
    if not p.get("ok"):
        return dict(head=f"No forecast: {p.get('why') or 'the forecaster reports a fault'}.", rows=[])
    if p.get("stale"):
        return dict(head=f"No forecast: {p['stale']}.", rows=[])
    if p.get("warm"):
        return dict(head="Warming up: the forecaster needs 10 minutes of prices before it says anything.", rows=[])
    F = p.get("F")
    by_h = {x["h"]: x for x in (p.get("path") or []) if isinstance(x, dict) and "h" in x}
    en = p.get("earned") or {}
    rh = (en.get("range_h") or {}).get("fut") or {}
    rows, head = [], []
    rg = (p.get("regime") or {}).get("name")
    mood = {"trending": "Trending market", "choppy": "Choppy market", "mixed": "Mixed market"}.get(rg)
    if mood:
        head.append(mood + (", with a sudden jump just now" if (p.get("regime") or {}).get("jump") else ""))

    # 1. how far
    h5, h15 = _half(by_h.get(300), F), _half(by_h.get(900), F)
    if h5 is not None:
        txt = f"Next 5 minutes: about ±{h5:.0f} points ({by_h[300]['q10']:,.0f} to {by_h[300]['q90']:,.0f})."
        if h15 is not None:
            txt += f" Next 15 minutes: about ±{h15:.0f}."
        st = (rh.get("300") or {}).get("status", "unchecked")
        cov, ck = (rh.get("300") or {}).get("cov"), (rh.get("300") or {}).get("checks") or 0
        if st == "ok":
            note, tone = f"Reliable today: these ranges held the price {_pc(cov)} of the time ({ck:.0f} checks).", "good"
        elif st == "narrow":
            note, tone = (f"Careful: today moves have been bigger than these ranges (they held only {_pc(cov)}); "
                          f"they are being widened."), "warn"
        elif st == "wide":
            note, tone = f"Today moves have been smaller than these ranges (they held {_pc(cov)}).", "none"
        else:
            note, tone = (f"Not checked enough yet today. On earlier days these ranges held the price about "
                          f"{PAST_RANGE_CAUGHT * 100:.0f} % of the time."), "none"
        rows.append(dict(k="far", title="How far", text=txt, note=note, tone=tone))
        head.append(f"moving about ±{h5:.0f} points per 5 minutes")

    # 2. which way
    hl = PLAIN_LEAN_H if PLAIN_LEAN_H in by_h else 60 if 60 in by_h else None
    x = by_h.get(hl) if hl else None
    if x and x.get("mu") is not None and x.get("sd"):
        z = float(x["mu"]) / float(x["sd"])
        mins = "2 minutes" if hl == 120 else "1 minute"
        sc = next((s for s in ((p.get("score") or {}).get("fut") or []) if s.get("h") == hl), {})
        dn = (sc.get("dir_n") or 0) * ORIGIN_EVERY / float(hl)
        today = (f" Today such leans were right {_pc(sc.get('dir_hit'))} of the time ({dn:.0f} checks)."
                 if dn >= RANGE_MIN_CHECKS and sc.get("dir_hit") is not None else "")
        past = PAST_LEAN_HIT.get(hl)
        if abs(z) < LEAN_SD:
            txt, tone = f"Next {mins}: no lean. Up and down are about equally likely.", "none"
            head.append("no lean")
        else:
            word = "up" if z > 0 else "down"
            size = "Clear" if abs(z) >= 0.35 else "Slight"
            txt = f"Next {mins}: {size.lower()} lean {word}, about {float(x['mu']):+.1f} points.".replace("-", "−")
            txt = txt[0].upper() + txt[1:]
            tone = "good" if word == "up" else "bad"
            head.append(f"{size.lower()} lean {word} for the next {mins}")
        note = (f"On earlier days its strongest leans were right about {past * 100:.0f} % of the time." if past else "")
        # 78 entries: the Conductor's trades 27 Oct - 11 Nov, lean rebuilt out of sample (docs/54_WHY_QUIET_12NOV.md)
        note += today + (" Beyond 5 minutes it is a coin toss. A hint, not a trade signal: on 78 past Conductor "
                         "entries, its agreement did not improve them.")
        rows.append(dict(k="way", title="Which way", text=txt, note=note.strip(), tone=tone))

    # 3. the held trade, or what a fresh buy needs
    opts = p.get("options") or []
    held = next((o for o in opts if o.get("tag") == "held"), None)
    hd = p.get("held") or {}
    if held is not None or hd.get("strike") is not None:
        o = held or {}
        side = o.get("side") or ("CE" if hd.get("side") in (0, "CE") else "PE" if hd.get("side") in (1, "PE") else "")
        strike = o.get("strike") if o.get("strike") is not None else hd.get("strike")
        entry, bid, delta = hd.get("entry"), o.get("bid"), o.get("delta")
        name = f"{float(strike):.0f} {side}" if strike is not None else "position"
        book = hd.get("book") or (p.get("account") or {}).get("owner")
        rule = f" Its exit belongs to {book}'s own rules." if book else " Its exit belongs to the book's own rules."
        if entry and bid is not None and delta and abs(delta) > 0.05:
            d = float(bid) - float(entry)
            pct = d / float(entry) * 100.0
            if d >= 0:
                back = abs(delta) * (h5 or 0.0)
                txt = f"Your {name} is {d:.1f} above entry ({pct:+.1f} %)."
                if h5:
                    txt += (f" A normal 5-minute move against you (about {h5:.0f} points) would take back about "
                            f"{back:.1f}" + (", more than the whole gain." if back > d else " of it."))
                tone = "good"
            else:
                need = -d / abs(delta)
                sign = "+" if side == "CE" else "−"
                txt = f"Your {name} is {-d:.1f} below entry ({pct:+.1f} %). Nifty needs about {sign}{need:.0f} points to get back to entry."
                ref = h15 or h5
                if ref:
                    within = need <= ref
                    txt += (f" A normal {'15' if h15 else '5'}-minute move is about ±{ref:.0f}, so that is "
                            + ("within reach." if within else "more than a normal move."))
                    tone = "warn" if within else "bad"
                else:
                    tone = "warn"
            rows.append(dict(k="trade", title="Your trade", text=txt, note=rule.strip(), tone=tone))
        else:
            rows.append(dict(k="trade", title="Your trade", text=f"Holding the {name}.", note=rule.strip(), tone="none"))
    else:
        cands = [o for o in opts if o.get("tag") == "buy"]
        need = []
        for o in cands:
            x5 = {y["h"]: y for y in o.get("path") or []}.get(300)
            if x5 and x5.get("be") is not None:
                need.append((o, float(x5["be"])))
        if need:
            parts = [f"a {'call' if o['side'] == 'CE' else 'put'} ({o['strike']:.0f} {o['side']}) needs Nifty "
                     + (f"{be:+.0f}" if abs(be) >= 1 else f"{be:+.1f}").replace("-", "−")
                     + (" point" if round(abs(be)) == 1 else " points") for o, be in need[:2]]
            txt = "Bought now, " + " and ".join(parts) + " within 5 minutes to cover decay and the spread."
            big = max(abs(be) for _, be in need[:2])
            if h5:
                if big <= 0.3 * h5:
                    note, tone = (f"That is small next to a normal 5-minute move of ±{h5:.0f}: the cost is not the "
                                  f"problem, the direction is."), "none"
                elif big <= h5:
                    note, tone = f"A normal 5-minute move is ±{h5:.0f}, so it needs a fair part of one in its favour.", "warn"
                else:
                    note, tone = f"That is more than a normal 5-minute move (±{h5:.0f}): buying now needs an unusual move.", "bad"
            else:
                note, tone = "", "none"
            rows.append(dict(k="trade", title="If you buy now", text=txt,
                             note=(note + " The forecaster places no trade; the Conductor does not read it.").strip(), tone=tone))

    # 4. time decay against movement
    rent = p.get("rent") or {}
    atm = next((r for r in (p.get("decay") or []) if r.get("atm")), None)
    if rent.get("ratio") is not None:
        r = float(rent["ratio"])
        cost = f"Time decay costs about ₹{abs(atm['lot_hour']):,.0f} per lot per hour. " if atm and atm.get("lot_hour") is not None else ""
        if r >= 1.0:
            txt, tone = cost + f"Nifty has been moving enough to pay for it ({r:.1f} times the cost, last 10 minutes).", "good"
        else:
            txt, tone = cost + f"Nifty has not been moving enough to pay for it ({r:.1f} times the cost, last 10 minutes).", "bad"
        rows.append(dict(k="decay", title="Decay", text=txt,
                         note="Above 1.0 times the cost, movement beats decay for an option buyer.", tone=tone))
        head.append("decay " + ("paid" if r >= 1.0 else "not paid"))
    if not rows:
        return dict(head="No forecast yet: waiting for prices.", rows=[])
    h = ", ".join(head)
    return dict(head=(h[0].upper() + h[1:] + ".") if h else "", rows=rows)


# ── 12 Nov late (owner: "very intuitive and more comprehensive ... what option will move where ... tell me what to do,
# nothing grasps my attention"): the forecaster's read (a verdict), the Nifty ladder, the option board and a running
# feed of what changed. Display only: it places no order and the Conductor does not read it.
BOARD_H = (300, 900, 1800)                     # 5, 15 and 30 minutes on the board and the ladder
FEED_MAX = 40                                  # feed lines kept for the day (newest first on the page)


def _lean_of(p):
    """(z, mu, h) of the short lean: the 2-minute mean over its sd (1 minute near the close); (None, None, None)."""
    by_h = {x["h"]: x for x in (p.get("path") or []) if isinstance(x, dict) and "h" in x}
    for h in (PLAIN_LEAN_H, 60):
        x = by_h.get(h)
        if x and x.get("mu") is not None and x.get("sd"):
            return float(x["mu"]) / float(x["sd"]), float(x["mu"]), h
    return None, None, None


def _conf(p, h):
    """'high' / 'medium' / 'low' from today's hit rate of the lean at h, or 'untested today'."""
    sc = next((s for s in ((p.get("score") or {}).get("fut") or []) if s.get("h") == h), {})
    dn = (sc.get("dir_n") or 0) * ORIGIN_EVERY / float(h or 120)
    hit = sc.get("dir_hit")
    if hit is None or dn < RANGE_MIN_CHECKS:
        return "untested today"
    return "high" if hit >= 0.60 else "medium" if hit >= 0.55 else "low"


def verdict(p):
    """{word, tone, why, conf}: the forecaster's one-word read. Holding: HOLD / PROTECT GAINS / WATCH / UNDER PRESSURE
    from the held premium's forecast; flat: CALLS FAVOURED / PUTS FAVOURED (clear 2-minute lean), TILT TO CALLS / PUTS
    (slight lean) or WAIT. Built only from the payload's numbers."""
    by_h = {x["h"]: x for x in (p.get("path") or []) if isinstance(x, dict) and "h" in x}
    h5, h15 = _half(by_h.get(300), None), _half(by_h.get(900), None)
    z, mu, hl = _lean_of(p)
    conf = _conf(p, hl) if hl else "untested today"
    ratio = (p.get("rent") or {}).get("ratio")
    paid = None if ratio is None else float(ratio) >= 1.0
    opts = p.get("options") or []
    held = next((o for o in opts if o.get("tag") == "held"), None)
    hd = p.get("held") or {}
    if held is not None and hd.get("entry") and held.get("bid") is not None:
        entry, bid = float(hd["entry"]), float(held["bid"])
        d = bid - entry
        x15 = {y["h"]: y for y in held.get("path") or []}.get(900) or {}
        q50 = x15.get("q50")
        drift = None if q50 is None else float(q50) - bid
        dl = abs(float(held.get("delta") or 0.0))
        side = held.get("side")
        lean_with = z is not None and abs(z) >= LEAN_SD and ((z > 0) == (side == "CE"))
        lean_against = z is not None and abs(z) >= LEAN_SD and not lean_with
        if d >= 0:
            back = dl * (h5 or 0.0)
            if back > d and lean_against:
                return dict(word="PROTECT GAINS", tone="warn", conf=conf,
                            why=f"In profit by {d:.1f}, but a normal 5-minute move against you could take it all back, "
                                f"and the short lean is against you.")
            return dict(word="HOLD", tone="good", conf=conf,
                        why=f"In profit by {d:.1f}." + (" The short lean is with you." if lean_with else "")
                            + ("" if drift is None else f" The 15-minute middle forecast is {_rs(q50)} ({drift:+.1f})."))
        need = -d / dl if dl > 0.05 else None
        if need is not None and h15 and need > h15:
            return dict(word="UNDER PRESSURE", tone="bad", conf=conf,
                        why=f"{-d:.1f} below entry. Getting back needs about {need:.0f} Nifty points, more than a normal "
                            f"15-minute move (±{h15:.0f}).")
        return dict(word="WATCH", tone="warn", conf=conf,
                    why=f"{-d:.1f} below entry." + (f" About {need:.0f} Nifty points gets it back, within a normal "
                                                     f"15-minute move." if need is not None else "")
                        + (" The short lean is with you." if lean_with else " The short lean is against you." if lean_against else ""))
    if held is not None or hd.get("strike") is not None:
        return dict(word="HOLDING", tone="none", conf=conf, why="The account holds a position; its entry price is not known yet.")
    if z is None:
        return dict(word="WAIT", tone="none", conf=conf, why="No short-term forecast yet.")
    up = z > 0
    side = "CALLS" if up else "PUTS"
    move = f"about {mu:+.1f} points in {'2 minutes' if hl == 120 else '1 minute'}".replace("-", "−")
    dec = "" if paid is None else (" Movement is paying for decay." if paid else " But movement is not paying for decay.")
    if abs(z) >= 0.35:
        return dict(word=f"{side} FAVOURED", tone="good" if up else "bad", conf=conf,
                    why=f"Clear short lean {'up' if up else 'down'}, {move}.{dec}")
    if abs(z) >= LEAN_SD:
        return dict(word=f"TILT TO {side}", tone="good" if up else "bad", conf=conf,
                    why=f"Slight short lean {'up' if up else 'down'}, {move}.{dec}")
    return dict(word="WAIT", tone="none", conf=conf,
                why="No lean: up and down are about equally likely." + ("" if paid is None else
                    " Movement is not paying for decay, so waiting costs nothing." if not paid else
                    " Movement is paying for decay; a lean would make a case."))


def ladder(p):
    """Nifty's 5 / 15 / 30-minute ranges for the page: [{h, lo80, lo50, mid, hi50, hi80}] in index points (a
    horizon past the close is not forecast, so after 15:00 the 30-minute row is missing)."""
    out = []
    for x in p.get("path") or []:
        mid = x.get("q50") if x.get("q50") is not None else x.get("mean")       # payloads before 12 Nov: no q50
        if x.get("h") in BOARD_H and mid is not None and all(x.get(k) is not None for k in ("q10", "q25", "q75", "q90")):
            out.append(dict(h=x["h"], lo80=x["q10"], lo50=x["q25"], mid=mid, hi50=x["q75"], hi80=x["q90"]))
    return out


def board(p):
    """Every forecast option, the held one first: where its premium is expected in 5 / 15 / 30 minutes (middle and
    80 % range), the chance it is worth more than its cost, and the 5-minute race to +5 % or -5 %."""
    opts = p.get("options") or []
    hd = p.get("held") or {}
    order = {"held": 0, "buy": 1, "atm": 2}
    seen, out = set(), []
    for o in sorted(opts, key=lambda o: order.get(o.get("tag"), 3)):
        key = (o.get("strike"), o.get("side"))
        if key in seen or o.get("strike") is None:
            continue
        seen.add(key)
        held = o.get("tag") == "held"
        now = o.get("bid") if held else o.get("ask")
        if now is None:
            continue
        rows = []
        for x in o.get("path") or []:
            if x.get("h") in BOARD_H and x.get("q50") is not None:
                rows.append(dict(h=x["h"], mid=x["q50"], chg=r1(float(x["q50"]) - float(now), 1), lo=x.get("q10"),
                                 hi=x.get("q90"), pp=x.get("pp"), decay=x.get("decay")))
        bar = o.get("barrier") or None
        out.append(dict(strike=o["strike"], side=o["side"], tag=o.get("tag"), now=now,
                        basis="bid (what it sells for)" if held else "ask (what it costs)",
                        entry=hd.get("entry") if held else None, delta=o.get("delta"), iv=o.get("iv"),
                        rows=rows, race=dict(up=bar.get("up"), down=bar.get("down")) if bar else None))
    return out


def feed_events(prev, cur, now):
    """What changed between two plain reads, as feed lines {t, tone, text}."""
    ev = []
    if not prev:
        return [dict(t=now, tone=cur["verdict"]["tone"], text=f"Read: {cur['verdict']['word']}. {cur['verdict']['why']}")]
    a, b = prev["verdict"], cur["verdict"]
    if a["word"] != b["word"]:
        ev.append(dict(t=now, tone=b["tone"], text=f"{a['word']} to {b['word']}. {b['why']}"))
    if prev.get("regime") != cur.get("regime") and cur.get("regime"):
        ev.append(dict(t=now, tone="none", text=f"The market turned {cur['regime']}."))
    if prev.get("paid") is not None and cur.get("paid") is not None and prev["paid"] != cur["paid"]:
        ev.append(dict(t=now, tone="good" if cur["paid"] else "bad",
                       text="Movement is now paying for decay." if cur["paid"] else "Movement stopped paying for decay."))
    if prev.get("range") != cur.get("range") and cur.get("range") in ("narrow", "ok"):
        ev.append(dict(t=now, tone="warn" if cur["range"] == "narrow" else "good",
                       text="Moves are bigger than the forecast ranges today; they are being widened." if cur["range"] == "narrow"
                       else "The 5-minute ranges are on target today."))
    return ev
