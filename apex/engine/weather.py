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
Version 3 (8 Nov, owner: EVERY docs/27 item is weather; nothing is set aside): the rest of the catalogue, in the
photo itself so one record carries all 68 items (numbers = docs/27):
  B  6 or45_pos; 7 range_vs_norm (today's range so far / the median of EARLIER recorded days at this clock,
     apex/conductor/clock_norms.py); 9 reversals60; 10 vwap_side_with, vwap_side_min; 19 chop30 / chop60
  C  13 fmv60 / fmv300 (the forward's change); 14 accel30; 17 rv5_vs_norm; 18 jump_z, cusum, kv / kvt (Kalman
     velocity and its t-stat), bp_sig; 20 basis, basis_chg60 / 300 and e_basis_dev
  D  21 e_fut_ofi60, e_fut_micro, e_syn_dev; 22 e_fut_imb5, e_fut_tot_imb, fut_imb_q / _o, fut_imb_t_chg30, fut_lead;
     23 rest_with_rs / rest_opp_rs (rupees resting at the best bid / ask), rest_round_rs, round_dist; 24 force_*,
     fut_opp_q / fut_opp_o (REFILLING ... PULLED), fut_pulled; 25 fut_vol_surge (vs its 5-min base), fut_vol60,
     fut_vol_vs_norm (vs earlier days at this clock), agg_with_rs, agg_net; 26 absorb60 (rupees per point);
     27 kyle_lambda, fut_spread
  E  31 ep_first, lead_s (+ = the stocks crossed before the future), ep_n_cross; 33 hw_book_imb / _imb_t / _chg30;
     34 hw_vol_surge, hw_vol60, hw_vol_vs_norm; 35 fn60 / fn300 (Fin Nifty), bank_z
  F  37 oi_own_chg5 / 15 / 30, oi_other_chg*, oi_net_help* (writers adding on the side that helps us),
     oi_own_chg_open; 38 pcr, pcr_chg30, max_pain_dist; 39 gex_regime, gex_balance, gex_flip_ahead, gex_wall_ahead /
     _behind; 40 vol_ratio_with, prem_ratio_with; 42 skew_chg5; 43 term_chg5; 44 svi_res
  G  46 vega; 47 vanna, charm_min, speed_g, color_min, vomma, zomma; 49 iv_vs_med, opt_iv_chg1 / 5, atm_iv_chg1 / 5;
     50 prem_chg1_pct, opt_vol1, opt_vol_chg1; 51 prem_resp1; 52 opt_book_imb, opt_imb_chg30, opt_opp_q / _o,
     opt_lead, opt_run; 53 sl_room_up_pct / _dn_pct, sl_n_res / _sup, sl_next_res; 54 po_up1 / 5 / 15, po_dn15,
     po_ever, po_a / po_b
  H  56 e_iv_rv, e_iv_atm, e_rv15; 57 hmm_state, hmm_p, hmm_run_min, hmm_left_min, hmm_drift; 58 hk_buy / hk_sell /
     hk_ratio (Hawkes on the chosen contract)
  I  59 regime, regime_with, regime_ext_pct, regime_broke; 60 ep_type, ep_with, ep_age_s, sync_dir, dom_z, sigma15;
     61 adv_<name> (each advisor's veto for our direction) and adv_vetoes; 62 force_verdict / _with / _rho / _pi /
     _level_dist
  J  63 trigger, trig_str, trig_unit; 67 agree_same / agree_other (other books firing this step and the last)
  K  68 reconnects, feed_state, chain_age, depth_age_fut, n_hero_stale, n_hero_wide, gap_s_today
Version 4 (9 Nov, owner: "67-68 items ... are not enough ... add at least 30-40 more different kind of items"):
36 more items, docs/27 numbers 69-104, in apex/engine/weather4.py (field list in its docstring and in
apex/conductor/search.py ITEMS): L the tape's structure (69-80), M across markets (81-85), N the option and the chain
(86-95), O flow through time (96-99), P the books around this one (100-102), Q this book's day (103-104).
Not available from the recorded data (said plainly, not skipped quietly): nothing in docs/27 is left unbuilt; the
"vs normal" norms exist only once three earlier days are recorded (norm_days says how many).
"""
from bisect import bisect_right, insort

import numpy as np

from .. import config

VERSION = 5
N_ITEMS = 114                                               # docs/27: 68 (v3) + 36 (v4, 9 Nov) + 10 (v5, 10 Nov)
ITEM_IDS = tuple(range(1, 105)) + (105, 106, 107, 108, 109, 110, 120, 121, 122, 128)   # docs/38 numbers its items;
#                                         111-119 and 127 are later batches, 123-126 the continuation photograph
SKIP_FIELDS = frozenset(("v", "v2_error", "v3_error", "v4_error", "v5_error", "v5_missing"))   # bookkeeping keys, not weather
MIN_FIELDS = 280                                            # v3 wrote about 270 fields on a full engine; v4 about 390


def static_check():
    """8 Nov (owner: 'I don't want to hear in future that the weather items were not captured'). Problems with the
    photograph's definition itself: the version, the 68 docs/27 items, the field map. Empty = fine. The engine refuses
    to start on any problem (engine_main.new_day)."""
    probs = []
    try:
        from ..conductor import search
    except Exception as e:          # noqa: BLE001
        return [f"item map unavailable: {e}"]
    if VERSION != 5:
        probs.append(f"photo version {VERSION}, expected 5")
    if len(search.ITEMS) != N_ITEMS or sorted(search.ITEMS) != list(ITEM_IDS):
        probs.append(f"{len(search.ITEMS)} docs/27 items mapped, expected {N_ITEMS}")
    try:
        from . import weather4
        if weather4.N_ITEMS != 104:
            probs.append(f"weather4 builds {weather4.N_ITEMS} items, expected 104")
    except Exception as e:          # noqa: BLE001
        probs.append(f"weather4 unavailable: {e}")
    try:
        from . import weather5
        if tuple(sorted(weather5.ITEMS5)) != ITEM_IDS[104:] or weather5.NEW_ITEMS != ITEM_IDS[104:]:
            probs.append(f"weather5 builds items {sorted(weather5.ITEMS5)}, expected {list(ITEM_IDS[104:])}")
    except Exception as e:          # noqa: BLE001
        probs.append(f"weather5 unavailable: {e}")
    fields = {f for _label, fs in search.ITEMS.values() for f in fs}
    if len(fields) < MIN_FIELDS:
        probs.append(f"{len(fields)} fields mapped to items, expected at least {MIN_FIELDS}")
    for fn in ("_photo_v2", "_photo_v3", "photo"):
        if fn not in globals():
            probs.append(f"{fn} missing")
    return probs


def check_photo(w):
    """One photograph as recorded: (problems, warnings). Problems: wrong version, a v2/v3 error, too few fields.
    Warnings: docs/27 items with no field present yet (e.g. the 45-60 minute ones before 10:00, the norms before
    three earlier days are on file)."""
    from ..conductor import search
    probs, warns = [], []
    if not isinstance(w, dict):
        return ["no photograph"], []
    if w.get("v") != VERSION:
        probs.append(f"version {w.get('v')}, expected {VERSION}")
    for k in ("v2_error", "v3_error", "v4_error", "v5_error"):
        if k in w:
            probs.append(f"{k}: {w[k]}")
    keys = [k for k in w if k not in SKIP_FIELDS]
    if len(keys) < MIN_FIELDS:
        probs.append(f"{len(keys)} fields, expected at least {MIN_FIELDS}")
    for item, (label, fs) in sorted(search.ITEMS.items()):
        present = any(f in w for f in fs) or (item == 61 and any(k.startswith("adv_") for k in w))
        if not present:
            warns.append(f"{item} {label}")
    return probs, warns
_ANN = (252 * 22500) ** 0.5 * 100   # 1-s return sd -> annualised %, the edge.py rv15 convention
_YEAR_S = 365.0 * 86400.0


def load_norms(day, path=None):
    """Clock norms for `day` from the days recorded BEFORE it (apex/conductor/clock_norms.py writes the file): the
    median range-so-far, rv5, futures volume and heavyweight volume per session minute. None with fewer than three
    earlier days. A day never reads its own values or a later day's (no look-ahead)."""
    import json
    import os
    path = path or os.path.join(config.LEARN_DIR, "clock_norms.json")
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return None
    days = sorted(d for d in data.get("days", {}) if d < str(day))
    if len(days) < 3:
        return None
    out = {"n_days": len(days)}
    n = int(data.get("minutes") or 375)
    for name in ("range", "rv5", "fut_vol", "hw_vol"):
        cols = []
        for j in range(n):
            vals = [data["days"][d][name][j] for d in days if j < len(data["days"][d][name])
                    and data["days"][d][name][j] is not None]
            cols.append(float(np.median(vals)) if len(vals) >= 3 else None)
        out[name] = cols
    return out
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


class _Prefix:
    """10 Nov (docs/41 section 13): the max, min or median of the FIRST k values of an append-only list, kept
    running. The per-second base used to re-scan the whole day for these every second (10 ms at the open, 36 ms by
    the close). Exactly the same numbers as max(v[:k]), min(v[:k]) and numpy.median(v[:k]): if the list is another
    object or k went back, it starts again from nothing."""

    def __init__(self, median=False):
        self.src, self.k, self.hi, self.lo = None, 0, None, None
        self.srt = [] if median else None

    def to(self, vals, k):
        if vals is not self.src or k < self.k:
            self.src, self.k, self.hi, self.lo = vals, 0, None, None
            if self.srt is not None:
                self.srt = []
        if k > self.k:
            seg = vals[self.k:k]
            if self.srt is None:
                hi, lo = max(seg), min(seg)
                self.hi = hi if self.hi is None or hi > self.hi else self.hi
                self.lo = lo if self.lo is None or lo < self.lo else self.lo
            elif len(seg) > 32:
                self.srt = sorted(self.srt + seg)
            else:
                for v in seg:
                    insort(self.srt, v)
            self.k = k
        return self

    def median(self):
        n = len(self.srt)
        m = n // 2
        return self.srt[m] if n % 2 else (self.srt[m - 1] + self.srt[m]) / 2.0


class Weather:
    """The engine's histories for the photograph; one per day (engine_main.start_day)."""

    def __init__(self, day=None, norms=None):
        self.day = day
        self.h = {}                                # v3: named 1-Hz series {name: ([t], [v])}, see feed_misc
        # v3: clock norms from EARLIER days only (None = fewer than three recorded; False = do not load)
        self.norms = norms if norms is not None else (load_norms(day) if day and norms is not False else None)
        if self.norms is False:
            self.norms = None
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
        self._orc = {}                             # finished opening ranges (they never change once complete)
        self._px_rng, self._iv_med = _Prefix(), _Prefix(median=True)

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

    def feed_misc(self, now_s, vals):
        """v3: named per-second series, stamped with the engine clock of the step that read them: fwd, basis
        (future mid - spot), ext (futures minus VWAP), skew / term (ATM IV differences), pcr, atm_iv (%), fn (Fin
        Nifty), ce_ttq / pe_ttq (the hero band's cumulative volume by side), atm_ce / atm_pe (premiums), fut_ttq,
        hw_ttq (the heavyweights' cumulative cash volume). None / non-finite values are not stored (never 0)."""
        t = float(now_s)
        for k, v in vals.items():
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(v):
                continue
            s = self.h.get(k)
            if s is None:
                s = self.h[k] = ([], [])
            if s[0] and t <= s[0][-1]:
                continue
            s[0].append(t)
            s[1].append(v)

    def _s(self, name):
        return self.h.get(name, ([], []))

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
        or15 = self._orange(ts, ps, t, 15, open_s) if open_s else None
        or30 = self._orange(ts, ps, t, 30, open_s) if open_s else None
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
                      **self._base_v2, **self._base3(t, ts, ps, sp, open_s, er30, er60)}
        self._base_s = sec
        return self._base

    def _orange(self, ts, ps, t, minutes, open_s):
        """opening_range(), remembered once its window is complete: from then on it reads only samples stamped
        inside the window, and nothing stamped that early can still arrive."""
        c = self._orc.get(minutes)
        if c is not None and ts and c[0] == ts[0] and c[1] == open_s and t >= c[2]:
            return c[3]
        r = opening_range(ts, ps, t, minutes, open_s)
        if r is not None:
            self._orc[minutes] = (ts[0], open_s, ts[0] + 60 * minutes, r)
        return r

    def _base3(self, t, ts, ps, sp, open_s, er30, er60):
        """v3 (8 Nov): the direction-free part of the rest of docs/27, every read by value_at / change (bisect on
        the arrival stamp), so nothing stamped after t is seen."""
        S = self._s
        chg = lambda k, lag, tol=TOL_S: change(*S(k), t, lag, tol)                       # noqa: E731
        now_ = lambda k, tol=TOL_S: value_at(*S(k), t, tol)                               # noqa: E731
        out = {}
        out["or45"] = self._orange(ts, ps, t, 45, open_s) if open_s else None
        marks = [value_at(ts, ps, t - 60 * k) for k in range(61)]
        rev = None
        if all(m is not None for m in marks):
            sg = [1 if x > 0 else -1 for x in (marks[k - 1] - marks[k] for k in range(1, 61)) if x != 0]
            rev = sum(1 for k in range(1, len(sg)) if sg[k] != sg[k - 1])
        out["reversals60"] = rev
        out["chop30"] = _r(1.0 / er30, 2) if er30 else None                               # path per net point
        out["chop60"] = _r(1.0 / er60, 2) if er60 else None
        c30, c30b = change(ts, ps, t, 30), change(ts, ps, t - 30, 30)
        out["accel30"] = _r(c30 - c30b, 2) if c30 is not None and c30b is not None else None
        out["fmv60"], out["fmv300"] = _r(chg("fwd", 60), 2), _r(chg("fwd", 300), 2)
        out["fwd_lag60"] = value_at(*S("fwd"), t - 60)
        out["basis"] = _r(now_("basis"), 2)
        out["basis_chg60"], out["basis_chg300"] = _r(chg("basis", 60), 2), _r(chg("basis", 300), 2)
        et, ev = S("ext")                                                                 # minutes on this VWAP side
        i = bisect_right(et, t) - 1
        out["vwap_side_min"] = None
        if i >= 0 and t - et[i] <= TOL_S and ev[i] != 0:
            s0, j = (ev[i] > 0), i
            while j > 0 and (ev[j - 1] > 0) == s0 and ev[j - 1] != 0 and et[j] - et[j - 1] <= 120:
                j -= 1
            out["vwap_side_min"] = _r((t - et[j]) / 60.0, 1)
        out["skew_chg300"], out["term_chg300"] = _r(chg("skew", 300), 3), _r(chg("term", 300), 3)
        out["pcr"], out["pcr_chg30"] = _r(now_("pcr", 200), 3), _r(chg("pcr", 1800, 200), 3)
        it, iv = S("atm_iv")
        k = bisect_right(it, t)
        out["atm_iv_now"] = _r(now_("atm_iv"), 2)
        out["atm_iv_med"] = _r(float(self._iv_med.to(iv, k).median()), 2) if k >= 60 else None
        out["atm_iv_chg60"], out["atm_iv_chg300"] = _r(chg("atm_iv", 60), 2), _r(chg("atm_iv", 300), 2)
        fn_now = now_("fn")
        for lag in (60, 300):
            fn_old = value_at(*S("fn"), t - lag)
            out[f"fn{lag}"] = _r(100 * (fn_now / fn_old - 1), 3) if fn_now and fn_old else None
        ce, pe = chg("ce_ttq", 300), chg("pe_ttq", 300)
        out["ce_vol300"], out["pe_vol300"] = _r(ce, 0), _r(pe, 0)
        out["vol_ratio_cp"] = _r(ce / pe, 3) if ce is not None and pe else None
        ac, ap = now_("atm_ce"), now_("atm_pe")
        out["prem_ratio_cp"] = _r(ac / ap, 3) if ac and ap else None
        n_sp = bisect_right(ts, t)
        pr = self._px_rng.to(ps, n_sp) if n_sp else None
        rng_now = (pr.hi - pr.lo) if n_sp else None
        out["range_now"] = _r(rng_now, 2)
        out["fut_vol60"], out["hw_vol60"] = _r(chg("fut_ttq", 60), 0), _r(chg("hw_ttq", 60), 0)
        nm = self.norms
        mi = int((t - open_s) // 60) if open_s is not None else None
        norm = lambda name: (nm[name][mi] if nm and mi is not None and 0 <= mi < len(nm[name]) else None)   # noqa: E731
        out["norm_days"] = nm["n_days"] if nm else None
        rv5 = rv(ts, ps, t, 300)
        for key, val, nmk in (("range_vs_norm", rng_now, "range"), ("rv5_vs_norm", rv5, "rv5"),
                              ("fut_vol_vs_norm", out["fut_vol60"], "fut_vol"), ("hw_vol_vs_norm", out["hw_vol60"], "hw_vol")):
            ref = norm(nmk)
            out[key] = _r(val / ref, 3) if val is not None and ref else None
        return out


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


def photo(ctx, d, opt=None, book=None, why=None):
    """The photograph at a trigger: the base for this second plus what depends on the direction d (+1 call, -1 put),
    on the contract and on the book's own day. Reads only ctx (built from data that had arrived by this step) and
    the book's closed trades. `why` = the trigger text (item 63)."""
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
    try:
        _photo_v3(out, ctx, d, opt, book, b, sp, why)
    except Exception:
        out["v3_error"] = True
    try:                                               # 9 Nov (v4): items 69-104, each block guarded on its own
        from .weather4 import photo_v4
        photo_v4(out, ctx, d, opt, book, b, sp)
    except Exception:
        out["v4_error"] = "photo_v4"
    try:                                               # 10 Nov (v5, docs/38): ten instrumentation items, each guarded
        from .weather5 import photo_v5
        photo_v5(out, ctx, d, opt, book, b, sp)
    except Exception:
        out["v5_error"] = "photo_v5"
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


def _fin(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def _photo_v3(out, ctx, d, opt, book, b, sp, why):
    """v3 (8 Nov): the rest of docs/27 at the trigger, in the trade's direction d. Every input is a per-second view
    the engine built this step from data already arrived (ctx), or a history stamped by arrival (ohist, oi_hist).
    Each block is guarded on its own so a missing input leaves its fields None, never 0 and never the whole photo."""
    import math
    from .flow import CLS, PULL
    o = opt or {}
    t = ctx.get("now_s")
    m, fl, fid = ctx.get("_m"), ctx.get("_flow"), ctx.get("fut_id")
    snap = getattr(m, "snap", None) if m is not None else None
    q = ctx.get("quant") or {}
    F = _fin(ctx.get("fwd")) or _fin(ctx.get("fut"))
    # B / C: shape and price action from the base
    or45 = b.get("or45")
    out["or45_pos"] = (_r((sp - or45[1]) / (or45[0] - or45[1])) if or45 and sp is not None and or45[0] > or45[1] else None)
    for k in ("reversals60", "chop30", "chop60", "range_now", "range_vs_norm", "rv5_vs_norm", "norm_days",
              "fut_vol60", "fut_vol_vs_norm", "hw_vol60", "hw_vol_vs_norm", "vwap_side_min", "skew_chg300",
              "term_chg300", "pcr", "pcr_chg30", "atm_iv_med"):
        out[k] = b.get(k)
    out["skew_chg5"], out["term_chg5"] = out.pop("skew_chg300"), out.pop("term_chg300")
    out["accel30"], out["fmv60"], out["fmv300"] = _sg(b.get("accel30"), d), _sg(b.get("fmv60"), d), _sg(b.get("fmv300"), d)
    out["basis"], out["basis_chg60"], out["basis_chg300"] = b.get("basis"), _sg(b.get("basis_chg60"), d), _sg(b.get("basis_chg300"), d)
    out["atm_iv_chg1"], out["atm_iv_chg5"] = b.get("atm_iv_chg60"), b.get("atm_iv_chg300")
    out["fn60"], out["fn300"] = _sg(b.get("fn60"), d, 3), _sg(b.get("fn300"), d, 3)
    vr, pr = b.get("vol_ratio_cp"), b.get("prem_ratio_cp")
    out["vol_ratio_with"] = _r(vr if d > 0 else (1.0 / vr if vr else None), 3) if vr else None
    out["prem_ratio_with"] = _r(pr if d > 0 else (1.0 / pr if pr else None), 3) if pr else None
    # 18: the forward's state (Kalman velocity, bipower noise, jump z, CUSUM)
    out["kv"], out["kvt"] = _sg(q.get("kv"), d, 3), _sg(q.get("kvt"), d, 2)
    out["bp_sig"], out["jump_z"] = q.get("sig"), q.get("jz")
    cu = q.get("cusum")
    out["cusum"] = cu if isinstance(cu, (int, float, str)) and not isinstance(cu, bool) else \
        (cu.get("alarm") if isinstance(cu, dict) else None)
    out["kyle_lambda"] = q.get("kyle")
    # edge snapshot (20-22, 38, 56), signed where it has a sign
    try:
        from .edge import signed as _es
        for k, v in (_es(ctx.get("edge"), d) or {}).items():
            if k not in ("wall_up", "wall_dn", "wall_room", "imp_rng", "imp_d", "imp_f", "imp_with"):
                out["e_" + k] = v
    except Exception:
        pass
    # D: the Nifty futures book and flow (23-27)
    ltp_f = None
    if snap is not None and fid is not None:
        bid, ask = float(snap["bid"][fid]), float(snap["ask"][fid])
        bq1, aq1 = float(snap["bqty"][fid]), float(snap["aqty"][fid])
        ltp_f = _fin(snap["ltp"][fid])
        if bid > 0 and ask >= bid:
            out["fut_spread"] = _r(ask - bid, 2)
            rb, ra = bid * max(bq1, 0.0), ask * max(aq1, 0.0)
            out["rest_with_rs"] = _r(rb if d > 0 else ra, 0)          # resting rupees on our side of the book
            out["rest_opp_rs"] = _r(ra if d > 0 else rb, 0)           # resting rupees the move must eat
            px = (bid + ask) / 2
            rnd = (math.floor(px / 100.0) + 1) * 100.0 if d > 0 else (math.ceil(px / 100.0) - 1) * 100.0
            out["round_dist"] = _r((rnd - px) * d, 2)
            lp = np.asarray(snap["apx"][fid] if d > 0 else snap["bpx"][fid], float)
            lq = np.asarray(snap["aq"][fid] if d > 0 else snap["bq"][fid], float)
            ok = np.isfinite(lp) & np.isfinite(lq) & (lp > 0)
            sel = ok & ((lp >= rnd) if d > 0 else (lp <= rnd))
            out["rest_round_rs"] = _r(float(np.sum(lp[sel] * lq[sel])), 0) if ok.any() else None
        if fl is not None:
            cq, co, imb = fl.side(fid, d)
            out["fut_opp_q"], out["fut_opp_o"] = CLS[cq], CLS[co]
            out["fut_pulled"] = bool(cq == PULL or co == PULL)
            out["fut_imb_o"] = _r(imb, 3)
            out["fut_imb_q"] = _sg(_fin(fl.imb_q[fid]), d, 3)
            out["fut_imb_t_chg30"] = _sg(_fin(fl.imb_t_chg[fid]), d, 3)
            out["fut_lead"] = _r(fl.lead[fid], 3)
            ab, as_ = float(fl.agg_b[fid]), float(fl.agg_s[fid])
            if ltp_f:
                out["agg_with_rs"] = _r((ab if d > 0 else as_) * ltp_f, 0)
            out["agg_net"] = _sg((ab - as_) / (ab + as_), d, 3) if ab + as_ > 0 else None
            vs, vb = _fin(fl.vol_s[fid]), _fin(fl.vol_base[fid])
            out["fut_vol_surge"] = _r(vs / vb, 3) if vs is not None and vb else None
        if m is not None:
            dq, dp = _fin(m.change(m.ttq, 60)[fid]), _fin(m.change(m.ltp, 60)[fid])
            out["fut_ttq60"] = _r(dq, 0)
            if dq is not None and dp is not None and dq > 0 and ltp_f:
                out["absorb60"] = _r(dq * ltp_f / max(abs(dp), 0.5), 0)      # rupees traded per point of progress
    # E: the heavyweights' books and volume (31, 33, 34, 35)
    eqf = ctx.get("eq_fut")
    if eqf and fl is not None:
        fids, w, eids = eqf
        fids, w, eids = np.asarray(fids, int), np.asarray(w, float), np.asarray(eids, int)

        def wmean(a, ok0):
            k = ok0 & np.isfinite(a)
            return float(np.sum(a[k] * w[k]) / np.sum(w[k])) if k.any() and w[k].sum() > 0 else None
        okf = fids >= 0
        fsafe = np.where(okf, fids, 0)
        out["hw_book_imb"] = _sg(wmean(fl.imb_q[fsafe], okf), d, 3)
        out["hw_book_imb_t"] = _sg(wmean(fl.imb_t[fsafe], okf), d, 3)
        out["hw_book_chg30"] = _sg(wmean(fl.imb_t_chg[fsafe], okf), d, 3)
        with np.errstate(divide="ignore", invalid="ignore"):
            surge = fl.vol_s[eids] / fl.vol_base[eids]
        out["hw_vol_surge"] = _r(wmean(surge, np.ones(len(eids), bool)), 3)
    ep = ctx.get("episode") or {}
    out["ep_type"], out["ep_first"], out["ep_n_cross"] = ep.get("type"), ep.get("first"), ep.get("n_cross")
    out["ep_max_s"], out["ep_age_s"] = _r(ep.get("max_S"), 3), _r(ep.get("age"), 1)
    out["ep_with"] = (ep.get("dir") == d) if ep.get("dir") else None
    ft, st = ep.get("fut_cross_t"), ep.get("first_t")
    out["lead_s"] = _r(ft - st, 1) if ft is not None and st is not None else None   # + = the stocks moved first
    dom = ctx.get("domino") or {}
    out["sync_dir"] = _r(dom.get("S_up") if d > 0 else dom.get("S_dn"), 3)
    out["dom_z"], out["sigma15"] = _sg(dom.get("z"), d, 2), _r(dom.get("sigma15"), 2)
    out["bank_z"] = _sg((ctx.get("bank") or {}).get("z"), d, 2)
    # F: the chain (37-40, 44)
    oh = ctx.get("oi_hist")
    own = o.get("id")
    if oh and own is not None and t is not None:
        hero = ctx.get("hero_ids") or []
        other = None
        if o.get("strike") is not None and o.get("rr") in ("CE", "PE"):
            okey = f"NIFTY|OPT|{ctx.get('w0')}|{int(o['strike'])}|{'PE' if o['rr'] == 'CE' else 'CE'}"
            other = ((ctx.get("by_key") or {}).get(okey) or {}).get("id")
        cur = None
        for ts_, dct in reversed(oh):
            if ts_ <= t:
                cur = dct
                break
        for lag, name in ((300, "5"), (900, "15"), (1800, "30")):
            past = None
            for ts_, dct in oh:
                if ts_ <= t - lag:
                    past = dct
                else:
                    break
            if not past or not cur:
                continue
            dv_ = lambda i: (cur.get(i, np.nan) - past.get(i, np.nan)) if i is not None else np.nan   # noqa: E731
            out[f"oi_own_chg{name}"] = _r(dv_(own), 0)
            out[f"oi_other_chg{name}"] = _r(dv_(other), 0)
            dce = sum(x for x in (dv_(i) for i, rr in hero if rr == "CE") if np.isfinite(x))
            dpe = sum(x for x in (dv_(i) for i, rr in hero if rr == "PE") if np.isfinite(x))
            out[f"oi_net_help{name}"] = _r((dpe - dce) if d > 0 else (dce - dpe), 0)   # writers adding on our side
    for row in ctx.get("chain_view") or ():
        if o.get("strike") is not None and float(row[0]) == float(o["strike"]):
            out["oi_own_chg_open"] = _r(row[3] if o.get("rr") == "CE" else row[4], 0)
            break
    gx = ctx.get("gex") or {}
    if gx.get("ok"):
        out["gex_regime"], out["gex_balance"] = gx.get("regime"), gx.get("balance")
        if F:
            fl_ = gx.get("flip")
            out["gex_flip_ahead"] = _r((fl_ - F) * d, 1) if fl_ is not None else None
            ahead = gx.get("call_wall") if d > 0 else gx.get("put_wall")
            behind = gx.get("put_wall") if d > 0 else gx.get("call_wall")
            out["gex_wall_ahead"] = _r((ahead - F) * d, 1) if ahead is not None else None
            out["gex_wall_behind"] = _r((F - behind) * d, 1) if behind is not None else None
        if sp is not None and gx.get("max_pain") is not None:
            out["max_pain_dist"] = _r((gx["max_pain"] - sp) * d, 1)
    sm = q.get("smile") or {}
    if sm.get("K") and o.get("strike") is not None:
        try:
            out["svi_res"] = sm["res"][sm["K"].index(int(o["strike"]))]
        except (ValueError, IndexError):
            out["svi_res"] = None
    # G: the chosen option (46, 47, 49-54)
    iv, K, w0, now = o.get("iv"), o.get("strike"), ctx.get("w0"), ctx.get("now_dt")
    is_call = o.get("rr") == "CE"
    if F and iv and K and w0 and now is not None:
        from ..quant import greeks_hi, passage
        T = greeks_hi.real_years(str(w0), now)
        g = greeks_hi.all_greeks(float(F), float(K), T, iv / 100.0, is_call)
        out["vega"] = _r(g["vega"] / 100, 3)
        out["vanna"], out["vomma"] = _r(g["vanna"] / 100, 5), _r(g["vomma"] / 1e4, 4)
        out["charm_min"], out["color_min"] = _r(g["charm"] / _YEAR_S * 60, 6), _r(g["color"] / _YEAR_S * 60, 8)
        out["speed_g"], out["zomma"] = _r(g["speed"], 8), _r(g["zomma"] / 100, 7)
        kv, sig, ask = _fin(q.get("kv")), _fin(q.get("sig")), _fin(o.get("ask"))
        if kv is not None and sig and ask and ask > 0:
            po = passage.premium_outcome(float(F), float(K), T, iv / 100.0, is_call, ask, 0.10, 0.10, kv, sig)
            if po:
                ub = list(po["up_by"])
                out["po_up1"], out["po_up5"], out["po_up15"] = _r(ub[0], 3), _r(ub[2], 3), _r(ub[-1], 3)
                out["po_dn15"], out["po_ever"] = _r(po["dn_by"][-1], 3), _r(po["up_ever"], 3)
                out["po_a"], out["po_b"] = _r(po["a"], 1), _r(po["b"], 1)
    out["iv_vs_med"] = _r(iv - b["atm_iv_med"], 2) if iv and b.get("atm_iv_med") else None
    hist = (ctx.get("ohist") or {}).get(own) if own is not None else None
    bid_o, ask_o, ltp_o = _fin(o.get("bid")), _fin(o.get("ask")), _fin(o.get("ltp"))
    mid = (bid_o + ask_o) / 2 if bid_o and ask_o and ask_o >= bid_o else ltp_o
    if hist and t is not None:
        def at(lag, idx):
            tgt = t - lag
            for rec in reversed(hist):
                if rec[0] <= tgt:
                    return rec[idx] if tgt - rec[0] <= TOL_S and len(rec) > idx else None
            return None
        iv60, iv300 = at(60, 1), at(300, 1)
        out["opt_iv_chg1"] = _r(iv - iv60, 2) if iv and iv60 else None
        out["opt_iv_chg5"] = _r(iv - iv300, 2) if iv and iv300 else None
        mid60 = at(60, 3)
        out["prem_chg1_pct"] = _r(100 * (mid / mid60 - 1), 2) if mid and mid60 else None
        q60, q120 = at(60, 7), at(120, 7)
        qn = _fin(snap["ttq"][own]) if snap is not None else None
        if qn is not None and q60 is not None:
            out["opt_vol1"] = _r(qn - q60, 0)
            out["opt_vol_chg1"] = _r((qn - q60) - (q60 - q120), 0) if q120 is not None else None
        f60 = b.get("fwd_lag60")
        if mid and mid60 and F and f60 and o.get("delta") is not None and o.get("gamma") is not None:
            dF = float(F) - float(f60)
            expect = float(o["delta"]) * dF + 0.5 * float(o["gamma"]) * dF * dF + float(o.get("theta_min") or 0.0)
            out["prem_resp1"] = _r((mid - mid60) / expect, 3) if abs(expect) >= 0.05 else None
    if own is not None:
        hk = (q.get("flow_by_id") or {}).get(str(own)) or {}
        out["hk_buy"], out["hk_sell"], out["hk_ratio"] = hk.get("buy"), hk.get("sell"), hk.get("ratio")
    if snap is not None and own is not None:
        tb, tsq = float(snap["tbq"][own]), float(snap["tsq"][own])
        out["opt_book_imb"] = _r((tb - tsq) / (tb + tsq), 3) if tb + tsq > 0 else None
        if fl is not None:
            cq, co, imb = fl.side(own, 1)                      # a buyer needs the premium UP: the asks oppose
            out["opt_opp_q"], out["opt_opp_o"] = CLS[cq], CLS[co]
            out["opt_imb_chg30"] = _r(_fin(fl.imb_t_chg[own]), 3)
            out["opt_lead"] = _r(fl.lead[own], 3)
            if m is not None:
                out["opt_run"] = _r(fl.run_score(own, 1, m), 3)
    sl = ctx.get("strike_lv")
    if sl is not None and o.get("key") and ltp_o:
        v = sl.view(o["key"], ltp_o, t) or {}
        out["sl_room_up_pct"], out["sl_room_dn_pct"] = v.get("room_up_pct"), v.get("room_dn_pct")
        out["sl_n_res"], out["sl_n_sup"] = len(v.get("res") or []), len(v.get("sup") or [])
        out["sl_next_res"] = v["res"][0][1] if v.get("res") else None
    # H 57: the hidden regime
    rg = q.get("regime") or {}
    out["hmm_state"], out["hmm_run_min"], out["hmm_left_min"] = rg.get("state"), rg.get("run_min"), rg.get("left_min")
    out["hmm_p"] = _r(max(rg["post"]), 3) if rg.get("post") else None
    try:
        out["hmm_drift"] = _sg(rg["drift"][rg["state"]], d, 1) if rg.get("drift") and rg.get("state") is not None else None
    except (IndexError, TypeError):
        out["hmm_drift"] = None
    # I: the engine's own verdicts (59-62)
    rv_ = ctx.get("regime") or {}
    out["regime"], out["regime_ext_pct"], out["regime_broke"] = rv_.get("state"), rv_.get("ext_pct"), rv_.get("broke")
    out["regime_with"] = (rv_.get("dir") == d) if rv_.get("dir") else None
    ext = _fin(rv_.get("ext"))
    out["vwap_side_with"] = (ext * d > 0) if ext is not None and ext != 0 else None
    adv = (ctx.get("advisors_dir") or {}).get(d) or {}
    n_veto = 0
    for k, v in adv.items():
        ok = isinstance(v, dict) and not v.get("faulted")
        out[f"adv_{k}"] = bool(v.get("veto")) if ok else None
        n_veto += 1 if ok and v.get("veto") else 0
    out["adv_vetoes"] = n_veto if adv else None
    fv = ctx.get("force") or {}
    out["force_verdict"], out["force_rho"], out["force_pi"] = fv.get("verdict"), _r(fv.get("rho"), 3), _r(fv.get("pi"), 3)
    out["force_with"] = (fv.get("dir") == d) if fv.get("dir") else None
    out["force_level_dist"] = _r((fv["level"] - ltp_f) * d, 1) if fv.get("level") is not None and ltp_f else None
    # J: the trigger and agreement (63, 67)
    ctl = getattr(book, "ctl", None) or {}
    out["trig_str"], out["trig_unit"] = ctl.get("trig_str"), ctl.get("trig_unit")
    out["trigger"] = str(why).split()[0] if why else None
    fires = ctx.get("fires") or {}
    side, oside = ("CE", "PE") if d > 0 else ("PE", "CE")
    if fires:
        out["agree_same"] = (fires.get("prev") or {}).get(side, 0) + (fires.get("cur") or {}).get(side, 0)
        out["agree_other"] = (fires.get("prev") or {}).get(oside, 0) + (fires.get("cur") or {}).get(oside, 0)
    # K 68: feed health
    fh = ctx.get("feed") or {}
    for k in ("reconnects", "feed_state", "chain_age", "depth_age_fut", "n_hero_stale", "n_hero_wide", "gap_s_today"):
        out[k] = fh.get(k)
