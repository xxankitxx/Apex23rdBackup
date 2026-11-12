"""One business clock for the Forecast Lab (PKG-08, 12 Nov 2026). Pure functions, no fitted parameters.

The engine solves implied volatility on the calendar clock: greeks.years_to_expiry counts calendar seconds to 15:30 on
the expiry day, over 365 days. An option's total implied variance F^2 iv^2 T_cal runs off only while the market is
open. This clock spreads that total over the trading seconds left to expiry:

    tau_left_s  = seconds left today to 15:30 (from 09:15 at the earliest, today only if it is a trading day)
                  + 22,500 for every trading session after today, up to and including the expiry day
    k_ts        = T_cal * SPY / tau_left_s          (exactly 1 on expiry day; about 2.5 the Monday before a Tuesday
                                                     expiry; about 5 to 6 midweek and on Fridays)

Then, with no fitted number anywhere:
    implied variance per trading second  = F^2 iv^2 T_cal / tau_left_s
    decay per wall minute (theta_wall)   = calendar theta x k_ts
    break-even move per minute           = sqrt(2 |theta_wall| / Gamma)
                                           (for Black-76 this is exactly sqrt(implied variance per trading second x 60))
    rent                                 = realised variance per second / implied variance per trading second

The holiday list is config.NSE_HOLIDAYS (and NSE_HOLIDAYS_EXTRA) through config.is_trading_day. A year that list does
not cover gives no clock (None and the reason), never a guess. The expiry always comes from the chain being priced,
never from weekday arithmetic (the 10 Nov 2026 holiday moved that week's expiry to Monday 9 Nov).

Also here, for the option paths (used only when core.PRICING_STAGE_B is on, after the repricing scorecard has passed):
the measured implied-volatility noise table, the Brownian-bridge barrier race, and the held-position attribution.
Display and research only: nothing here trades and the engine never imports it."""
import json
import math
import os
from datetime import date, datetime

import numpy as np

from .. import config, greeks

SPY = 365.0 * 86400.0                        # calendar seconds a year (the engine's implied-volatility convention)
SESSION_S = 22500                            # one session, 09:15 to 15:30
OPEN_S, CLOSE_S = 9 * 3600 + 15 * 60, 15 * 3600 + 30 * 60
EXPIRY_FLOOR_S = 600.0                       # greeks.years_to_expiry never goes below 10 minutes on expiry day

# Measured implied-volatility noise: the sd of the at-the-money IV change, in vol POINTS, at 5, 15 and 30 minutes, by
# days to expiry (council PKG-08, 16 recorded sessions, residual after the futures move). The 1-2 day row is the
# geometric middle of the other two until research/forecast_lab/reprice_study.py measures it (it writes 'iv_sd' into
# data/forecast_lab/reprice.json, and load_iv_sd() then uses the measured rows).
IV_SD_H = (300, 900, 1800)
IV_SD = {"exp": (1.16, 1.53, 1.85),
         "1-2": (0.44, 0.64, 0.82),
         "3+": (0.17, 0.27, 0.36)}
IV_SD_MEASURED = {"exp": True, "1-2": False, "3+": True}


def _as_date(x):
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return date.fromisoformat(str(x)[:10])


def _covered_years():
    return {h[:4] for h in config.NSE_HOLIDAYS}


def tau_left_s(now, expiry):
    """(trading seconds left to 15:30 on the expiry day, None) or (None, reason). now is a timezone-aware datetime
    (IST); expiry is the chain's expiry date (ISO string or date)."""
    try:
        exp = _as_date(expiry)
    except (TypeError, ValueError):
        return None, f"expiry {expiry!r} is not a date"
    if now is None:
        return None, "no time"
    if now.tzinfo is not None:
        now = now.astimezone(config.IST)
    today = now.date()
    if exp < today:
        return None, f"expiry {exp.isoformat()} has passed"
    have = _covered_years()
    for y in range(today.year, exp.year + 1):
        if str(y) not in have:
            return None, f"the holiday calendar does not cover {y}"
    if not config.is_trading_day(exp):
        return None, f"expiry {exp.isoformat()} is not a trading day"
    s = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1e6
    left = float(CLOSE_S - max(s, OPEN_S)) if (config.is_trading_day(today) and s < CLOSE_S) else 0.0
    n = 0
    d = today.toordinal() + 1
    while d <= exp.toordinal():
        if config.is_trading_day(date.fromordinal(d)):
            n += 1
        d += 1
    tau = left + SESSION_S * n
    if exp == today:
        if left <= 0.0:
            return None, "the expiry session has closed"
        tau = max(tau, EXPIRY_FLOOR_S)               # the same floor as the calendar time the IV was solved on
    if tau <= 0.0:
        return None, "no trading time left"
    return tau, None


def k_ts(now, expiry, T_cal=None):
    """(k, tau_left_s, None) or (None, None, reason). k = calendar seconds left / trading seconds left. T_cal is the
    calendar time (years) the chain's IV was solved on; by default greeks.years_to_expiry(expiry, now)."""
    tau, why = tau_left_s(now, expiry)
    if tau is None:
        return None, None, why
    if T_cal is None:
        try:
            T_cal = greeks.years_to_expiry(_as_date(expiry).isoformat(), now)
        except (TypeError, ValueError) as e:
            return None, None, f"no calendar time: {e}"
    if T_cal is None or not math.isfinite(T_cal) or T_cal <= 0:
        return None, None, "no calendar time"
    return float(T_cal) * SPY / tau, tau, None


def label(k):
    return f"business (k={k:.2f})" if k is not None else "unknown"


def implied_var_per_trade_s(F, iv, T_cal, tau):
    """The option's total implied variance F^2 iv^2 T_cal spread over the trading seconds left (points^2 a second)."""
    if None in (F, iv, T_cal, tau) or tau <= 0 or not all(map(math.isfinite, (F, iv, T_cal))):
        return None
    return F * F * iv * iv * T_cal / tau


def implied_move_per_min(F, iv, T_cal, tau):
    v = implied_var_per_trade_s(F, iv, T_cal, tau)
    return math.sqrt(v * 60.0) if v is not None and v >= 0 else None


def theta_wall(theta_cal, k):
    """Decay per wall (trading) minute from calendar-minute theta."""
    if theta_cal is None or k is None:
        return None
    return theta_cal * k


def be_per_min(theta_wall_min, gamma):
    """The futures move a minute (points) whose gamma gain pays a minute's decay: sqrt(2 |theta_wall| / Gamma)."""
    if theta_wall_min is None or gamma is None or not (gamma > 0) or not (theta_wall_min < 0):
        return None
    return math.sqrt(2.0 * abs(theta_wall_min) / gamma)


def rent_ratio(realised_var_s, implied_var_s):
    """Realised variance a second over implied variance a trading second: 1.00 is break-even for a bought option."""
    if realised_var_s is None or not implied_var_s or implied_var_s <= 0:
        return None
    return realised_var_s / implied_var_s


def T_after(T_cal, h, k):
    """Calendar time (years) left after h wall seconds on the business clock: T - h k / SPY."""
    return np.maximum(T_cal - np.asarray(h, float) * k / SPY, 1e-9)


# ── option paths (Stage B) ──────────────────────────────────────────────────────────────────────────────────────────
def dte_bucket(dte_days):
    if dte_days is None or not math.isfinite(dte_days) or dte_days < 1.0:
        return "exp"
    return "1-2" if dte_days < 3.0 else "3+"


def load_iv_sd(path=None):
    """The IV noise table: IV_SD, with any rows research/forecast_lab/reprice_study.py measured (key 'iv_sd' in
    data/forecast_lab/reprice.json). Returns (table, measured flags, note or None). A missing or bad file keeps the
    defaults and says why."""
    table, flags = {k: tuple(v) for k, v in IV_SD.items()}, dict(IV_SD_MEASURED)
    path = path or os.path.join(config.DATA_DIR, "forecast_lab", "reprice.json")
    if not os.path.exists(path):
        return table, flags, None
    try:
        with open(path, encoding="utf-8") as f:
            got = (json.load(f) or {}).get("iv_sd") or {}
    except (OSError, ValueError) as e:
        return table, flags, f"IV noise table not read ({type(e).__name__}: {e}); defaults used"
    bad = []
    for b, row in got.items():
        if b not in table:
            continue
        try:
            v = tuple(float(x) for x in row)
        except (TypeError, ValueError):
            bad.append(b)
            continue
        if len(v) == len(IV_SD_H) and all(0.0 < x < 20.0 for x in v) and all(a <= c for a, c in zip(v, v[1:])):
            table[b], flags[b] = v, True
        else:
            bad.append(b)
    return table, flags, (f"IV noise rows not used (bad values): {', '.join(sorted(bad))}" if bad else None)


def iv_sd_at(h, bucket, table=None):
    """sd (decimal volatility, not points) of the IV change after h seconds: variance linear in h between the
    table's points (and from 0), extended past 30 minutes along the last segment."""
    row = (table or IV_SD).get(bucket) or IV_SD["3+"]
    hh = np.r_[0.0, np.asarray(IV_SD_H, float)]
    vv = np.r_[0.0, (np.asarray(row, float) / 100.0) ** 2]
    h = np.asarray(h, float)
    v = np.interp(h, hh, vv)
    slope = (vv[-1] - vv[-2]) / (hh[-1] - hh[-2])
    v = np.where(h > hh[-1], vv[-1] + slope * (h - hh[-1]), v)
    return np.sqrt(np.maximum(v, 0.0))


def iv_increments(grid, bucket, table=None):
    """sd of each grid step's IV increment: sqrt(diff(sd(h)^2)), so the path's IV change at h has the measured sd."""
    v = iv_sd_at(grid, bucket, table) ** 2
    return np.sqrt(np.maximum(np.diff(np.r_[0.0, v]), 0.0))


def bridge_hit(x0, x1, level, var_step, up=True):
    """Probability a Brownian path from x0 to x1 over one step (variance var_step) touched the level in between.
    1 where an end is at or past the level."""
    x0, x1 = np.asarray(x0, float), np.asarray(x1, float)
    a, b = (level - x0, level - x1) if up else (x0 - level, x1 - level)
    past = (a <= 0) | (b <= 0)
    vs = np.maximum(np.asarray(var_step, float), 1e-12)
    p = np.exp(-2.0 * np.maximum(a, 0.0) * np.maximum(b, 0.0) / vs)
    return np.where(past, 1.0, p)


def race(bp, start, up_level, down_level, rng, step_s=10.0, monitor_s=1.0):
    """Which level does the bid touch first, as checked every monitor_s seconds (the scoring checks the quoted bid
    every second), from paths on a step_s grid. Between grid points a Brownian bridge gives the touch probability;
    the levels are moved out by 0.5826 sigma sqrt(monitor_s) (Broadie, Glasserman and Kou) so continuous touching
    matches checking once a second. bp: (paths, steps) bid on the grid; start: the bid now. Each step's variance is
    the cross-path variance of its increments. Returns dict(up, down, neither) shares."""
    bp = np.asarray(bp, float)
    n, m = bp.shape
    if m == 0:
        return dict(up=0.0, down=0.0, neither=1.0)
    X =np.c_[np.full(n, float(start)), bp]
    inc = np.diff(X, axis=1)
    var_step = np.var(inc, axis=0)                                   # (steps,)
    shift = 0.5826 * np.sqrt(var_step / max(step_s, 1e-9) * max(monitor_s, 0.0))[None, :]
    pu = bridge_hit(X[:, :-1], X[:, 1:], up_level + shift, var_step[None, :], up=True)
    pd = bridge_hit(X[:, :-1], X[:, 1:], down_level - shift, var_step[None, :], up=False)
    pu = np.where(X[:, 1:] >= up_level, 1.0, pu)                     # a grid point is itself a checked second
    pd = np.where(X[:, 1:] <= down_level, 1.0, pd)
    hu = rng.random((n, m)) < pu
    hd = rng.random((n, m)) < pd
    both = hu & hd                                                   # both touched in one step: which came first is
    pick_up = rng.random((n, m)) < 0.5                               # not known from the ends; split evenly
    hu, hd = np.where(both, pick_up, hu), np.where(both, ~pick_up, hd)
    big = 10 ** 6
    fu = np.where(hu.any(1), hu.argmax(1), big)
    fd = np.where(hd.any(1), hd.argmax(1), big)
    return dict(up=float((fu < fd).mean()), down=float((fd < fu).mean()), neither=float((fu == fd).mean()))


# ── held-position attribution (idea L2-I4): a pure accounting identity with model greeks ───────────────────────────
class HeldAttribution:
    """For one held contract, from the first chain the Lab sees it in: the premium's change split step by step into
    direction (delta x dF), convexity (0.5 Gamma dF^2), decay (theta on the business clock x dt), IV (vega x the
    strike's own IV change) and a residual that closes the sum. Plus what happened before the Lab saw it (entry to the
    first mid) and the exit spread (mid now to bid now), so the parts add up to bid now minus the entry price.
    to_json()/from_json() keep the sums across a restart (core saves them in extra_state)."""
    PARTS = ("before", "direction", "convexity", "decay", "iv", "residual", "exit_spread")

    def __init__(self, key, entry, t, Fs, mid, iv, greeks_now):
        self.key = key
        self.entry = float(entry) if entry is not None else None
        self.t0, self.t = float(t), float(t)
        self.Fs, self.mid, self.iv = float(Fs), float(mid), float(iv)
        self.mid0, self.iv0 = float(mid), float(iv)
        self.g = dict(greeks_now)
        self.sums = dict(direction=0.0, convexity=0.0, decay=0.0, iv=0.0, residual=0.0)
        self.bid = None
        self.steps = 0

    def step(self, t, Fs, mid, bid, iv, greeks_now, max_gap=30.0):
        """One chain update. Greeks are those at the step's START (kept from the last call). A gap longer than
        max_gap seconds books the whole change to the residual (nothing is invented across a gap)."""
        if t <= self.t or not all(map(math.isfinite, (Fs, mid, iv))):
            return
        dt, dF, dm, div = t - self.t, Fs - self.Fs, mid - self.mid, iv - self.iv
        g = self.g
        if dt <= max_gap:
            parts = dict(direction=g["delta"] * dF, convexity=0.5 * g["gamma"] * dF * dF,
                         decay=g["theta_wall"] * dt / 60.0, iv=g["vega"] * div * 100.0)
            for k, v in parts.items():
                self.sums[k] += v
            self.sums["residual"] += dm - sum(parts.values())
        else:
            self.sums["residual"] += dm
        self.t, self.Fs, self.mid, self.iv, self.g = float(t), float(Fs), float(mid), float(iv), dict(greeks_now)
        self.bid = float(bid) if bid is not None and math.isfinite(bid) else None
        self.steps += 1

    def view(self, sd_iv=None):
        """The parts in premium points (per unit), their total, and the IV change since first seen (vol points, with a
        z-score against the measured IV noise sd_iv, decimal, when given)."""
        out = {k: round(v, 2) for k, v in self.sums.items()}
        out["before"] = round(self.mid0 - self.entry, 2) if self.entry is not None else None
        out["exit_spread"] = round(self.bid - self.mid, 2) if self.bid is not None else None
        tot = None
        if self.entry is not None and self.bid is not None:
            tot = round(self.bid - self.entry, 2)
        div = (self.iv - self.iv0) * 100.0
        z = round(div / (sd_iv * 100.0), 1) if sd_iv and sd_iv > 0 else None
        return dict(key=self.key, since=self.t0, t=self.t, steps=self.steps, parts=out, total=tot,
                    iv_change=round(div, 2), iv_z=z)

    def to_json(self):
        return dict(key=self.key, entry=self.entry, t0=self.t0, t=self.t, Fs=self.Fs, mid=self.mid, iv=self.iv,
                    mid0=self.mid0, iv0=self.iv0, g=self.g, sums=self.sums, bid=self.bid, steps=self.steps)

    @classmethod
    def from_json(cls, d):
        a = cls(d["key"], d.get("entry"), d["t0"], d["Fs"], d["mid"], d["iv"], d["g"])
        a.t, a.mid0, a.iv0 = float(d["t"]), float(d["mid0"]), float(d["iv0"])
        a.sums = {k: float(d["sums"].get(k, 0.0)) for k in a.sums}
        a.bid = d.get("bid")
        a.steps = int(d.get("steps", 0))
        return a
