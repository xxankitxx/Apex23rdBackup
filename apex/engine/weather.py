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
"""
from bisect import bisect_right

import numpy as np

from .. import config

VERSION = 1
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
        self.vix_t, self.vix_p = [], []            # VIX by its own arrival stamp
        self._vix_ns = None
        self._base_s, self._base = None, {}

    # ── feeding (engine_main, the 1-Hz block) ───────────────────────────────
    def feed_spot(self, now_s, spot):
        if self.spot_t and now_s <= self.spot_t[-1]:
            return
        self.spot_t.append(float(now_s))
        self.spot_p.append(float(spot))

    def feed_hw(self, now_s, px, w):
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
        self._base = {"er60": _r(er60), "dir60": dir60, "er_day": _r(er_day(self.spot_t, self.spot_p, t)),
                      "speed15": _r(speed(self.spot_t, self.spot_p, t), 3),
                      "breadth_up": _r(up), "breadth_dn": _r(dn), "breadth_n": n,
                      "vix": _r(v_now, 2), "vix_chg_open": _r(v_now - v_open, 2) if v_now and v_open else None,
                      "vix_chg15": _r(v_now - v_15, 2) if v_now and v_15 else None}
        self._base_s = sec
        return self._base


def photo(ctx, d, opt=None):
    """The photograph at a trigger: the base for this second plus what depends on the direction d (+1 call, -1 put)
    and on the contract. Reads only ctx (built from data that had arrived by this step)."""
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
    return out
