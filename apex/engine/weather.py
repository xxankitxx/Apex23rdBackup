"""
The weather photograph (Apex Conductor stage 2, docs/28 §11, docs/27). An OBSERVER: no book reads it to decide.

At every entry TRIGGER (paper.request_entry, which paper books, council books and the missed-signal counterfactuals
all go through) the book's pending entry gets `weather_trig`: the eight shortlisted factors, in the trade's direction,
copied to the position and so into paper/<day>.json. The diaries and the search (stage 3) read it from there.

No look-ahead, by construction (the leak test, tests/test_weather.py):
  * every history here is stamped with its ARRIVAL time: the engine's virtual clock when the sample was taken from
    the table (in a replay: the receive stamp of the packets already applied, never the exchange time); VIX with
    ctrl.vix_ns, its own arrival stamp;
  * every function takes the time it is asked about and reads only samples stamped at or before it (bisect), so
    data that arrives later can never change a photo already taken;
  * the per-second base is computed once per market second and describes the last completed second.

The eight factors (docs/28 §13 stage 2):
  1 calendar     mins_open, phase, weekday, dte, expiry_day
  2 efficiency   er60 / dir60 (as rule R-002 defines them, docs/31), er_day (since the first trusted print)
  3 range        pos_in_range, pos_dir (the same in the trade's direction), give, range_on, dist_hi / dist_lo,
                 or_pos (inside the opening range: 0 = low, 1 = high), or_late
  4 breadth      breadth_dir (as rule R-003 defines it), breadth_n (stocks counted)
  5 OI wall      wall_room (pts to the nearest OI wall in the trade's direction), wall_up, wall_dn
  6 straddle     strad_chg5, strad_excess (chg5 minus the expected 5-min change), strad_expanding, strad_state
  7 theta        theta_be (spot pts per minute the contract needs to pay its theta: |theta_min| / |delta|),
                 speed15 (mean |1-min spot move| over the last 15 min), theta_ratio = theta_be / speed15
  8 VIX          vix, vix_chg_open, vix_chg15
Undefined values are None (never 0), so the search can tell "no data" from "zero".

Version 2 (7 Nov, the rest of docs/27 that the engine's data supports; numbers = docs/27 groups):
  A  1 day_before_expiry, after_break (first session after a weekend / holiday), event; 2 hrs_to_expiry;
     3 mins_to_flat; 4 phase_bucket (open30 / morning / midday / afternoon / last_hour)
  B  5 gap_pts (first trusted print minus yesterday's close, in the trade's direction), gap_filled;
     6 or15_pos / or30_pos (spot inside the 15 / 30-min opening range: 0 low, 1 high, beyond = broken);
     9 er30, new_highs / new_lows (new session extremes so far); 10 vwap_ext (futures minus its VWAP, our way);
     11 to_pdh / to_pdl / to_pdc; 12 hi_age_min / lo_age_min
  C  13 mv5 ... mv300 (spot change over 5 s ... 5 min, our way); 14 accel15 (15-s change now minus 15 s ago);
     15 imp_rng, imp_with (impulse direction = ours), imp_age_min, imp_depth (pullback share of the impulse);
     16 swing_ahead / swing_behind (points to the 30-min high / low ahead of and behind the trade);
     17 rv1 / rv5 / rv15 (realised vol of 1-s spot returns, annualised %)
  E  28 wmove10 / 30 / 60 (the heavyweights' weighted move in Nifty points, our way); 30 wmove60_bank / _it /
     _energy / _other; 32 basket_gap (the domino's basket-minus-futures gap, our way); 35 bn60 / bn300 (Bank
     Nifty futures %, our way), nifty60 (Nifty spot %, our way)
  F  42 skew_atm (ATM put IV minus call IV); 43 term_atm (this week's ATM IV minus next week's)
  G  45 premium, spread_pct, quote_age; 46 delta, gamma, theta_min, theta_pct (theta per minute as % of premium);
     48 theta_be15 (spot points needed to beat 15 min of theta)
  H  55 vix_chg5, vix_chg30
  J  64 last_exit_s, last_won, last_reason; 65 last_same_side; 66 n_today, ret_today, streak
  K  68 fut_age, spot_age, gaps_today
Already on every trade elsewhere, so not repeated here: D 21-22 and 20, H 56, F 38 (edge_trig: OFI, depth
imbalance, basis, IV / RV, PCR), I 59-61 (signal_trig regime and episode type, the position's advisors), J 63
(the trigger strength, trig_str). Not built (no data kept for them yet): B 7 (needs earlier days at the same
clock), C 18, D 23-27, E 31 / 33 / 34, F 37 / 39 / 40 / 44, G 47 / 49-54, H 57-58, I 62, J 67.
"""
from bisect import bisect_right

import numpy as np

from .. import config

VERSION = 2
_ANN = (252 * 22500) ** 0.5 * 100   # 1-s return sd -> annualised %, the edge.py rv15 convention
TOL_S = 5.0                 # a mark needs a sample at most this old (the R-002 / R-003 definitions)
HW_LAG_S = 300.0            # breadth: the heavyweights' change over 5 minutes


def _r(x, n=4):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


def value_at(ts, ps, t, tol=TOL_S):
    """The last sample stamped at or before t, if it is at most tol s old; else None."""
    i = bisect_right(ts, t) - 1
    if i < 0 or t - ts[i] > tol:
        return None
    return ps[i]


def er_window(ts, ps, t, window=3600, step=60, tol=TOL_S):
    """(ER, DIR) over the last `window` s on `step`-s marks: |m0 - mN| / sum |m(k-1) - mk|. (None, None) when any
    mark lacks a sample within tol, or the path is flat. R-002 uses window 3600, step 60, and blocks before 10:15."""
    n = int(window // step)
    marks = []
    for k in range(n + 1):
        v = value_at(ts, ps, t - k * step, tol)
        if v is None:
            return None, None
        marks.append(v)
    path = sum(abs(marks[k - 1] - marks[k]) for k in range(1, n + 1))
    if path <= 0:
        return None, None
    net = marks[0] - marks[-1]
    return abs(net) / path, (1 if net > 0 else -1 if net < 0 else 0)


def er_day(ts, ps, t, step=60, min_marks=15):
    """Efficiency since the day's first trusted print, on 1-min marks counted back from t (as many whole minutes
    as the day has). None with fewer than min_marks minutes."""
    i = bisect_right(ts, t)
    if i == 0:
        return None
    n = int((t - ts[0]) // step)
    if n < min_marks:
        return None
    marks = []
    for k in range(n + 1):
        v = value_at(ts, ps, t - k * step, step)        # holes up to a minute are bridged here (a day-long view)
        if v is not None:
            marks.append(v)
    if len(marks) < min_marks:
        return None
    path = sum(abs(marks[k - 1] - marks[k]) for k in range(1, len(marks)))
    return abs(marks[0] - marks[-1]) / path if path > 0 else None


def speed(ts, ps, t, minutes=15, tol=TOL_S):
    """Mean |1-min spot move| over the last `minutes` minutes (pts per minute); None if a mark is missing."""
    marks = []
    for k in range(minutes + 1):
        v = value_at(ts, ps, t - 60 * k, tol)
        if v is None:
            return None
        marks.append(v)
    return sum(abs(marks[k - 1] - marks[k]) for k in range(1, minutes + 1)) / minutes


def change(ts, ps, t, lag, tol=TOL_S):
    """ps(t) - ps(t - lag), both by value_at; None if either is missing."""
    a, b = value_at(ts, ps, t, tol), value_at(ts, ps, t - lag, tol)
    return None if a is None or b is None else a - b


def window(ts, ps, t, span):
    """The samples stamped in (t - span, t]."""
    return ps[bisect_right(ts, t - span):bisect_right(ts, t)]


def rv(ts, ps, t, span):
    """Annualised realised vol (%) of 1-s log returns over the last span s; None with fewer than span/2 samples."""
    xs = window(ts, ps, t, span)
    if len(xs) < max(10, span // 2):
        return None
    r = np.diff(np.log(np.asarray(xs, float)))
    return float(np.std(r)) * _ANN if len(r) > 1 else None


def opening_range(ts, ps, t, minutes, open_s, late_s=600):
    """(hi, lo) of the first `minutes` after the first print, once that window has passed; None if the first print
    is more than late_s after the open (a late start) or the window is not complete."""
    if not ts or ts[0] > t or ts[0] - open_s > late_s or t < ts[0] + 60 * minutes:
        return None
    xs = ps[:bisect_right(ts, ts[0] + 60 * minutes)]
    return (max(xs), min(xs)) if xs else None


def wmove(ts, arrs, w, t, lag, spot, mask=None, tol=TOL_S):
    """The heavyweights' weighted move over lag s in Nifty points: spot x sum(w_i/100 x return_i), over the
    stocks with a price at both ends (w = Nifty weight in %; mask picks a group)."""
    if not ts or w is None or spot is None:
        return None
    i1, i0 = bisect_right(ts, t) - 1, bisect_right(ts, t - lag) - 1
    if i1 < 0 or i0 < 0 or t - ts[i1] > tol or (t - lag) - ts[i0] > tol:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        c = arrs[i1] / arrs[i0] - 1.0
    ok = np.isfinite(c) & (np.asarray(w, float) > 0)
    if mask is not None:
        ok &= mask
    if not ok.any():
        return None
    return float(spot * np.sum(np.asarray(w, float)[ok] / 100.0 * c[ok]))


def breadth(ts, arrs, w, t, lag=HW_LAG_S, tol=TOL_S):
    """(share of weight up, share down, stocks counted) over `lag` s, from the heavyweights' price arrays `arrs`
    stamped `ts` (time order). Only stocks with a price now and lag s ago count; unchanged stocks count in the
    denominator only."""
    if not ts or w is None or not len(w):
        return None, None, 0
    i1, i0 = bisect_right(ts, t) - 1, bisect_right(ts, t - lag) - 1
    if i1 < 0 or i0 < 0 or t - ts[i1] > tol or (t - lag) - ts[i0] > tol:
        return None, None, 0
    a1, a0 = arrs[i1], arrs[i0]
    with np.errstate(divide="ignore", invalid="ignore"):
        c = a1 / a0 - 1.0
    w = np.asarray(w, float)
    ok = np.isfinite(c) & (a0 > 0) & (a1 > 0) & (w > 0)
    n = int(ok.sum())
    tot = float(w[ok].sum())
    if n < 2 or tot <= 0:
        return None, None, n
    return float(w[ok & (c > 0)].sum() / tot), float(w[ok & (c < 0)].sum() / tot), n


class Weather:
    """The engine's histories for the photograph; one per day (engine_main.start_day)."""

    def __init__(self, day=None):
        self.day = day
        self.spot_t, self.spot_p = [], []          # trusted in-session 1-Hz Nifty spot (the day)
        self.hw_t, self.hw_a = [], []              # heavyweight ltp arrays, 1 Hz, the whole day (~7 MB)
        self.hw_w = None
        self.hw_g = None                            # each heavyweight's group (universe.STOCKS), for the sector split
        self.nh, self.nl = [], []                  # cumulative new session highs / lows, parallel to spot_t
        self._hi = self._lo = None
        self.bn_t, self.bn_p = [], []              # Bank Nifty futures, 1 Hz
        self.vix_t, self.vix_p = [], []            # VIX by its own arrival stamp
        self._vix_ns = None
        self._base_s, self._base = None, {}

    # ── feeding (engine_main, the 1-Hz block) ───────────────────────────────
    def feed_spot(self, now_s, spot):
        if self.spot_t and now_s <= self.spot_t[-1]:
            return
        sp = float(spot)
        self.spot_t.append(float(now_s))
        self.spot_p.append(sp)
        h = l = 0
        if self._hi is None:
            self._hi = self._lo = sp
        else:
            if sp > self._hi:
                self._hi, h = sp, 1
            if sp < self._lo:
                self._lo, l = sp, 1
        self.nh.append((self.nh[-1] if self.nh else 0) + h)
        self.nl.append((self.nl[-1] if self.nl else 0) + l)

    def feed_bn(self, now_s, px):
        if px is None or not (px > 0) or (self.bn_t and now_s <= self.bn_t[-1]):
            return
        self.bn_t.append(float(now_s))
        self.bn_p.append(float(px))

    def feed_hw(self, now_s, px, w, groups=None):
        if groups is not None and self.hw_g is None:
            self.hw_g = np.asarray(groups, dtype=object)
        if px is None or not len(px):
            return
        if self.hw_t and now_s <= self.hw_t[-1]:
            return
        a = np.asarray(px, float).copy()
        a[~(a > 0)] = np.nan                        # 0 = no quote yet
        self.hw_t.append(float(now_s))
        self.hw_a.append(a)
        self.hw_w = np.asarray(w, float)

    def feed_vix(self, vix, vix_ns):
        if vix_ns is None or vix_ns <= 0 or not (vix and vix > 0) or vix_ns == self._vix_ns:
            return
        self._vix_ns = vix_ns
        t = vix_ns / 1e9
        if self.vix_t and t <= self.vix_t[-1]:
            return
        self.vix_t.append(t)
        self.vix_p.append(float(vix))

    # ── the per-second base (direction-free), cached per market second ─────
    def base(self, now_s):
        sec = int(now_s)
        if sec == self._base_s:
            return self._base
        t = float(now_s)
        er60, dir60 = er_window(self.spot_t, self.spot_p, t)
        up, dn, n = breadth(self.hw_t, self.hw_a, self.hw_w, t)
        v_now = value_at(self.vix_t, self.vix_p, t, tol=1e9)
        v_15 = value_at(self.vix_t, self.vix_p, t - 900, tol=1e9)
        v_open = self.vix_p[0] if self.vix_t and self.vix_t[0] <= t else None
        v_5 = value_at(self.vix_t, self.vix_p, t - 300, tol=1e9)
        v_30 = value_at(self.vix_t, self.vix_p, t - 1800, tol=1e9)
        ts, ps = self.spot_t, self.spot_p
        sp = value_at(ts, ps, t)
        er30, _d30 = er_window(ts, ps, t, window=1800)
        i = bisect_right(ts, t) - 1
        w30 = window(ts, ps, t, 1800)
        hi30, lo30 = (max(w30), min(w30)) if w30 else (None, None)
        o = config.mins(config.MARKET_OPEN) * 60
        from datetime import datetime
        open_s = None
        if ts:
            d0 = datetime.fromtimestamp(ts[0], config.IST)
            open_s = d0.replace(hour=o // 3600, minute=(o % 3600) // 60, second=0, microsecond=0).timestamp()
        or15 = opening_range(ts, ps, t, 15, open_s) if open_s else None
        or30 = opening_range(ts, ps, t, 30, open_s) if open_s else None
        c15, c15b = change(ts, ps, t, 15), change(ts, ps, t - 15, 15)
        g = self.hw_g
        grp = {}
        for name, sel in (("bank", ("bank",)), ("it", ("it",)), ("energy", ("energy",))):
            grp[name] = None if g is None else np.isin(g, sel)
        if g is not None:
            grp["other"] = ~np.isin(g, ("bank", "it", "energy"))
        bn_now = value_at(self.bn_t, self.bn_p, t)
        bn = {lag: (100 * (bn_now / value_at(self.bn_t, self.bn_p, t - lag) - 1)
                    if bn_now and value_at(self.bn_t, self.bn_p, t - lag) else None) for lag in (60, 300)}
        s60 = value_at(ts, ps, t - 60)
        hw = (self.hw_t, self.hw_a, self.hw_w)
        self._base_v2 = {
            "spot": sp, "first": ps[0] if ts and ts[0] <= t else None, "first_t": ts[0] if ts else None,
            "open_s": open_s, "er30": _r(er30),
            "new_highs": self.nh[i] if i >= 0 else None, "new_lows": self.nl[i] if i >= 0 else None,
            **{f"mv{lag}": _r(change(ts, ps, t, lag), 2) for lag in (5, 10, 30, 60, 120, 300)},
            "accel15": _r(c15 - c15b, 2) if c15 is not None and c15b is not None else None,
            "hi30": hi30, "lo30": lo30, "rv1": _r(rv(ts, ps, t, 60), 2), "rv5": _r(rv(ts, ps, t, 300), 2),
            "rv15": _r(rv(ts, ps, t, 900), 2),
            "or15": or15, "or30": or30,
            **{f"wmove{lag}": _r(wmove(*hw, t, lag, sp), 2) for lag in (10, 30, 60)},
            **{f"wmove60_{k}": (_r(wmove(*hw, t, 60, sp, mask=m), 2) if m is not None else None) for k, m in grp.items()},
            "bn60": _r(bn[60], 3), "bn300": _r(bn[300], 3),
            "nifty60": _r(100 * (sp / s60 - 1), 3) if sp and s60 else None,
            "vix_chg5": _r(v_now - v_5, 2) if v_now and v_5 else None,
            "vix_chg30": _r(v_now - v_30, 2) if v_now and v_30 else None}
        self._base = {"er60": _r(er60), "dir60": dir60, "er_day": _r(er_day(self.spot_t, self.spot_p, t)),
                      "speed15": _r(speed(self.spot_t, self.spot_p, t), 3),
                      "breadth_up": _r(up), "breadth_dn": _r(dn), "breadth_n": n,
                      "vix": _r(v_now, 2), "vix_chg_open": _r(v_now - v_open, 2) if v_now and v_open else None,
                      "vix_chg15": _r(v_now - v_15, 2) if v_now and v_15 else None,
                      **self._base_v2}
        self._base_s = sec
        return self._base


def _sg(x, d, n=2):
    return None if x is None else _r(x * d, n)


def _atm_iv(options, spot, week):
    """(call IV, put IV) at the strike nearest spot, in the given week, from ctx["options"]."""
    if spot is None:
        return None, None
    rows = [o for o in options or () if o.get("week", 0) == week and o.get("iv")]
    if not rows:
        return None, None
    k = min({o["strike"] for o in rows}, key=lambda x: abs(x - spot))
    ce = next((o["iv"] for o in rows if o["strike"] == k and o.get("rr") == "CE"), None)
    pe = next((o["iv"] for o in rows if o["strike"] == k and o.get("rr") == "PE"), None)
    return ce, pe


def photo(ctx, d, opt=None, book=None):
    """The photograph at a trigger: the base for this second plus what depends on the direction d (+1 call, -1 put),
    on the contract and on the book's own day. Reads only ctx (built from data that had arrived by this step) and
    the book's closed trades."""
    b = dict(ctx.get("weather") or {})
    out = {"v": VERSION}
    now = ctx.get("now_dt")
    # 1 calendar
    if now is not None:
        o = config.mins(config.MARKET_OPEN)
        out["mins_open"] = round(now.hour * 60 + now.minute + now.second / 60.0 - o, 2)
        out["phase"] = config.session_phase(now)
        out["weekday"] = now.weekday()
        try:
            from datetime import date
            dte = (date.fromisoformat(str(ctx.get("w0"))) - now.date()).days
        except (TypeError, ValueError):
            dte = None
        out["dte"], out["expiry_day"] = dte, (dte == 0 if dte is not None else None)
    # 2 efficiency
    out["er60"], out["er_day"] = b.get("er60"), b.get("er_day")
    out["dir60"] = (b.get("dir60") * d) if b.get("dir60") is not None else None     # +1 = the hour moved our way
    # 3 range
    dv = ctx.get("day") or {}
    sp = ctx.get("spot")
    pr = dv.get("pos_in_range")
    out["pos_in_range"] = pr
    out["pos_dir"] = (pr if d > 0 else 1.0 - pr) if pr is not None else None
    out["give"], out["range_on"], out["or_late"] = dv.get("give"), dv.get("range_on"), dv.get("or_late")
    hi, lo = dv.get("hi"), dv.get("lo")
    out["dist_hi"] = _r(hi - sp, 2) if sp is not None and hi is not None else None
    out["dist_lo"] = _r(sp - lo, 2) if sp is not None and lo is not None else None
    oh, ol = dv.get("or_hi"), dv.get("or_lo")
    out["or_pos"] = (_r((sp - ol) / (oh - ol)) if sp is not None and oh is not None and ol is not None and oh > ol
                     and dv.get("or_done") else None)
    # 4 breadth
    out["breadth_dir"] = b.get("breadth_up") if d > 0 else b.get("breadth_dn")
    out["breadth_n"] = b.get("breadth_n")
    # 5 OI wall
    e = ctx.get("edge") or {}
    out["wall_up"], out["wall_dn"] = e.get("wall_up"), e.get("wall_dn")
    out["wall_room"] = e.get("wall_up") if d > 0 else e.get("wall_dn")
    # 6 straddle
    sw = ctx.get("straddle_watch") or {}
    out["strad_chg5"], out["strad_excess"], out["strad_state"] = sw.get("chg5"), sw.get("excess"), sw.get("state")
    out["strad_expanding"] = (sw.get("excess") > 0) if sw.get("excess") is not None else None
    # 7 theta breakeven
    s15 = b.get("speed15")
    out["speed15"] = s15
    th, dl = (opt or {}).get("theta_min"), (opt or {}).get("delta")
    be = abs(float(th)) / abs(float(dl)) if th is not None and dl not in (None, 0) and abs(float(dl)) > 0.05 else None
    out["theta_be"] = _r(be, 3)
    out["theta_ratio"] = _r(be / s15, 3) if be is not None and s15 else None
    # 8 VIX
    out["vix"], out["vix_chg_open"], out["vix_chg15"] = b.get("vix"), b.get("vix_chg_open"), b.get("vix_chg15")
    try:
        _photo_v2(out, ctx, d, opt, book, b, dv, sp)
    except Exception:                                  # an observer: never stops the entry
        out["v2_error"] = True
    return out


def _photo_v2(out, ctx, d, opt, book, b, dv, sp):
    from datetime import date, datetime, timedelta
    now = ctx.get("now_dt")
    # A calendar
    if now is not None:
        today = now.date()
        exp = None
        try:
            exp = date.fromisoformat(str(ctx.get("w0")))
        except (TypeError, ValueError):
            pass
        nxt = today + timedelta(days=1)
        while not config.is_trading_day(nxt) and (nxt - today).days < 10:
            nxt += timedelta(days=1)
        prv = today - timedelta(days=1)
        while not config.is_trading_day(prv) and (today - prv).days < 10:
            prv -= timedelta(days=1)
        out["day_before_expiry"] = (exp == nxt) if exp else None
        out["after_break"] = (today - prv).days > 1
        out["event"] = bool(getattr(config, "EVENT_DAYS", {}).get(today.isoformat()))
        if exp:
            close = datetime(exp.year, exp.month, exp.day, 15, 30, tzinfo=now.tzinfo)
            out["hrs_to_expiry"] = _r((close - now).total_seconds() / 3600.0, 3)
        flat = config.ZERO_DTE_FLATTEN if out.get("expiry_day") else config.FLATTEN_AT
        m = now.hour * 60 + now.minute + now.second / 60.0
        out["mins_to_flat"] = _r(flat[0] * 60 + flat[1] - m, 2)
        mo = m - config.mins(config.MARKET_OPEN)
        out["phase_bucket"] = ("open30" if mo < 30 else "morning" if m < 12 * 60 else "midday" if m < 13 * 60 + 30
                               else "afternoon" if m < 14 * 60 + 30 else "last_hour")
    # B the day's shape
    pdc = dv.get("pdc")
    first, first_t, open_s = b.get("first"), b.get("first_t"), b.get("open_s")
    if first is not None and pdc and first_t is not None and open_s is not None and first_t - open_s <= 600:
        gap = first - float(pdc)
        out["gap_pts"] = _sg(gap, d)
        lo, hi = dv.get("lo"), dv.get("hi")
        out["gap_filled"] = (lo is not None and lo <= float(pdc)) if gap > 0 else \
            (hi is not None and hi >= float(pdc)) if gap < 0 else None
    for k, rng in (("or15_pos", b.get("or15")), ("or30_pos", b.get("or30"))):
        out[k] = (_r((sp - rng[1]) / (rng[0] - rng[1])) if rng and sp is not None and rng[0] > rng[1] else None)
    out["er30"], out["new_highs"], out["new_lows"] = b.get("er30"), b.get("new_highs"), b.get("new_lows")
    out["vwap_ext"] = _sg((ctx.get("regime") or {}).get("ext"), d, 1)
    for k, lab in (("to_pdh", "pdh"), ("to_pdl", "pdl"), ("to_pdc", "pdc")):
        v = dv.get(lab)
        out[k] = _r(float(v) - sp, 2) if v and sp is not None else None
    t = ctx.get("now_s")
    for k, lab in (("hi_age_min", "t_hi"), ("lo_age_min", "t_lo")):
        v = dv.get(lab)
        out[k] = _r((t - v) / 60.0, 2) if v is not None and t is not None else None
    # C price action
    for lag in (5, 10, 30, 60, 120, 300):
        out[f"mv{lag}"] = _sg(b.get(f"mv{lag}"), d)
    out["accel15"] = _sg(b.get("accel15"), d)
    pb = ctx.get("pb") or {}
    if pb.get("ok") and pb.get("rng"):
        out["imp_rng"] = _r(pb["rng"], 2)
        out["imp_with"] = (pb.get("d") == d) if pb.get("d") else None
        out["imp_age_min"] = _r((t - pb["ext_t"]) / 60.0, 2) if pb.get("ext_t") is not None and t is not None else None
        if sp is not None and pb.get("d"):
            dep = (pb["hi"] - sp) / pb["rng"] if pb["d"] > 0 else (sp - pb["lo"]) / pb["rng"]
            out["imp_depth"] = _r(dep)
    hi30, lo30 = b.get("hi30"), b.get("lo30")
    if sp is not None and hi30 is not None and lo30 is not None:
        out["swing_ahead"] = _r(hi30 - sp if d > 0 else sp - lo30, 2)
        out["swing_behind"] = _r(sp - lo30 if d > 0 else hi30 - sp, 2)
    out["rv1"], out["rv5"], out["rv15_spot"] = b.get("rv1"), b.get("rv5"), b.get("rv15")
    # E heavyweights
    for k in ("wmove10", "wmove30", "wmove60", "wmove60_bank", "wmove60_it", "wmove60_energy", "wmove60_other"):
        out[k] = _sg(b.get(k), d)
    out["basket_gap"] = _sg((ctx.get("domino") or {}).get("gap"), d, 3)
    out["bn60"], out["bn300"], out["nifty60"] = _sg(b.get("bn60"), d, 3), _sg(b.get("bn300"), d, 3), \
        _sg(b.get("nifty60"), d, 3)
    # F chain
    opts = ctx.get("options")
    ce0, pe0 = _atm_iv(opts, sp, 0)
    ce1, pe1 = _atm_iv(opts, sp, 1)
    out["skew_atm"] = _r(pe0 - ce0, 3) if ce0 is not None and pe0 is not None else None
    a0 = (ce0 + pe0) / 2 if ce0 is not None and pe0 is not None else None
    a1 = (ce1 + pe1) / 2 if ce1 is not None and pe1 is not None else None
    out["term_atm"] = _r(a0 - a1, 3) if a0 is not None and a1 is not None else None
    # G the chosen option
    o = opt or {}
    ltp, bid, ask = o.get("ltp"), o.get("bid"), o.get("ask")
    out["premium"] = ltp
    out["spread_pct"] = (_r(100 * (ask - bid) / ((ask + bid) / 2), 3)
                         if bid and ask and ask >= bid and (ask + bid) > 0 else None)
    out["quote_age"] = _r(o.get("age"), 2) if o.get("age") is not None and o.get("age") < 1e8 else None
    out["delta"], out["gamma"], out["theta_min"] = o.get("delta"), o.get("gamma"), o.get("theta_min")
    th = o.get("theta_min")
    out["theta_pct"] = _r(100 * abs(th) / ltp, 4) if th is not None and ltp else None
    out["theta_be15"] = _r(15 * out["theta_be"], 2) if out.get("theta_be") is not None else None
    # H VIX
    out["vix_chg5"], out["vix_chg30"] = b.get("vix_chg5"), b.get("vix_chg30")
    # J the book's own day
    trades = list(getattr(book, "trades", None) or []) if book is not None else []
    out["n_today"] = len(trades) if book is not None else None
    if trades:
        last = trades[-1]
        out["last_exit_s"] = _r(t - last["t_out"], 1) if last.get("t_out") is not None and t is not None else None
        out["last_won"] = (last.get("pnl_rs") or 0) > 0
        out["last_reason"] = last.get("reason")
        out["last_same_side"] = (last.get("rr") == ("CE" if d > 0 else "PE")) if last.get("rr") else None
        out["ret_today"] = _r(sum(float(x.get("ret_pct") or 0) for x in trades), 3)
        k, sign = 0, None
        for x in reversed(trades):
            w = (x.get("pnl_rs") or 0) > 0
            if sign is None:
                sign = w
            if w != sign:
                break
            k += 1
        out["streak"] = k if sign else -k
    elif book is not None:
        out["ret_today"], out["streak"] = 0.0, 0
    # K data quality
    out["fut_age"] = _r(ctx.get("fut_age"), 2) if ctx.get("fut_age") is not None else None
    out["spot_age"] = _r(ctx.get("spot_age"), 2) if ctx.get("spot_age") is not None and ctx.get("spot_age") < 1e8 else None
    out["gaps_today"] = (ctx.get("blackout") or {}).get("gaps_today")
