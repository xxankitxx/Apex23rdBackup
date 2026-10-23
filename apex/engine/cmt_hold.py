"""
apex/engine/cmt_hold.py — commentary content, team T08 (council 5): HOLD vs EXIT, anticipation, time,
discipline and the exit review.

WHAT       69 templates / 276 phrasings in seven groups (CONFIDENCE 13 · ANTICIPATION 11 · CAUTION 12 · WARNING 12 ·
           TIME 7 · DISCIPLINE 7 · EXIT REVIEW 7), ported from work_T08/11_COMMENTARY.md. The 7 EXIT templates carry
           kind="review": the selector never fires them live; `review_card(t, f)` composes three of them at the exit.

FACTS      extend_facts() adds the `hold_*` keys listed in FACTS (stall clock, 0-DTE theta on the calendar clock, the
           sellable (bid) P&L, the profit lock, walls / round numbers / day extremes, 1-min volume on the held strike,
           breadth with a 0.03 % stock threshold, the clock windows, the ladder reference rates from 19 Oct).

HONESTY    * no phrasing instructs: hold / sell / buy never appear as bare words; "exit" only as a noun, never at the
             head of a clause. The verdict line (core) is the only place a level is named.
           * every confidence remark cites a number; every number in a phrasing is a {slot} (no literal digits).
           * every confidence template is wrapped in _honest(): silent when spot is within a quarter trail of the stop,
             when the bid shows a loss while the last print shows a gain, or when the held quote is stale.
           * 19 Oct base rates are REF constants (HOLD_REF), quoted with the date, never as laws.

THETA      The engine's theta_min spreads year-theta/365 over 375 trading minutes; on expiry day the remaining time
           is the session itself, so the calendar clock (/1440) is the honest rate: hold_theta_cal = theta × 375/1440
           on a 0-DTE contract (display only — the engine's number is untouched).
"""
import math
from collections import deque
from typing import List

from .commentary import Template, rs, pct, mins, _n

# ── reference numbers from the 19 Oct 2026 replay (32 trades, spot_dc12_t12). Quoted, dated, never laws. ──────
HOLD_REF = {
    "date": "19 Oct", "n_trades": 32,
    "ladder_5_10": (21, 28), "ladder_10_15": (13, 21), "ladder_10_20": (8, 21), "ladder_15_25": (7, 13),
    "ladder_20_25": (7, 8), "ladder_20_30": (5, 8), "ladder_25_30": (5, 7),
    "gb5_recover": (23, 49),            # 5 % give-backs that made a new best
    "stall_60": 65, "stall_90": 75, "stall_120": 73, "stall_180": 50, "stall_max_s": 272,
    "first10_median_s": 44, "first10_fast": (13, 21),
    "with_trend_mean": 12.0, "with_trend_median": 8.1, "against_trend_mean": 3.2, "against_trend_median": -0.9,
    "against_trend_winners": (4, 19), "range_regime_mean": 1.3,
    "basket_win_with": 10.0, "basket_win_against": 1.3, "basket_lose_with": 4.2, "basket_lose_against": 5.2,
    "giveback_mean": 9.9, "best_mean": 15.6, "realised_mean": 5.6,
    "gb_half_flat": (4, 21),            # ex-+10 % trades that ended near flat after giving back more than half
    "losers_no10": (8, 13), "longest_winner_min": 11,
    "big3": "+31, +28 and +27 %", "top_trade": "+30 % at 09:55", "last_hour_trade": "+20 % in 110 s at 14:43",
    "lull_pts": "3–6", "round_tests": 4, "lesson_trade": "13:44", "lesson_pts": 13, "lesson_rs": "−₹16.6 k",
}
# thresholds (doc §3)
GB_CAUTION, GB_WARN_BEST = 5.0, 10.0
STALL_WATCH_S, STALL_WARN_S = 120.0, 180.0
STOP_NEAR_PTS, STOP_IMMINENT_PTS = 4.0, 2.0
IV_OFF, IV_WITH = -3.0, 2.0
PREM_LAG_PCT = 3.0
BASKET_WITH, BASKET_SPLIT, BASKET_TURNED_MARGIN = 6, 4, 3
THETA_IDLE_S = 180.0
TIME_NEAR_MIN, TIME_IMMINENT_MIN = 15.0, 5.0
LULL_SIGMA, LULL_SPEED = 5.0, 4.0
THIN_PCT = 10.0
LONG_HOLD_S = 600.0
STOCK_MOVE_PCT = 0.03
LUNCH = (12 * 60, 13 * 60 + 15)
LAST_HOUR, LAST_HOUR_0DTE = 14 * 60 + 30, 14 * 60

FACTS = """
hold_trail_pts hold_stall_s hold_stall_m hold_new_best_recent hold_theta_cal hold_theta_cal_abs hold_flat_speed
hold_theta_rs_min hold_theta_3m_rs hold_spot_speed_1m hold_theta_idle hold_idle_s
hold_bid_sellable hold_ret_bid hold_bid_rs hold_giveback_bid hold_prem_lag hold_bid_loss_ltp_gain hold_best_ret_bid
hold_ladder_rung hold_ladder_p5_10 hold_ladder_p10_15 hold_ladder_p10_20 hold_ladder_p15_25 hold_ladder_p20_25
hold_ladder_p20_30 hold_ladder_p25_30 hold_ref_date
hold_lock_on hold_lock_floor hold_lock_q hold_lock_rs hold_lock_gap hold_lock_pct hold_lock_trail_pct hold_best_prem
hold_room_pct hold_wall_rs hold_wall_prem hold_round_next hold_round_dist hold_day_level hold_day_room hold_hi_lo
hold_vol_1m hold_pos_vs_vol hold_thin hold_agg_b hold_agg_s hold_spread_pct hold_spread_x hold_spread_wide
hold_delta_rs hold_vega_rs hold_resid_rs hold_delta_only_pct hold_iv_off hold_iv_with
hold_n_with hold_n_against hold_n_eq hold_best_stock hold_worst_stock hold_worst_move hold_basket_with hold_basket_split
hold_basket_turned
hold_trend30 hold_with_trend hold_regime_in hold_regime_dir_in hold_regime_flipped hold_regime_text
hold_r15_in hold_sigma15_in hold_sigma15 hold_late_entry hold_lull hold_costly_entry hold_mid_in
hold_straddle_state hold_straddle_leg hold_straddle_slope hold_straddle_px hold_move_vs_straddle hold_straddle_spike_with
hold_gex_ok hold_gex_flip hold_gex_call hold_gex_put hold_gex_regime hold_gex_wall hold_gex_room hold_gex_tendency
hold_fut_confirm hold_fut_best_fav hold_basis_chg_dir
hold_lunch hold_last_hour hold_no_reentry hold_last_entry_hms hold_time_room_pts hold_exit_est_rs
hold_stop_rs hold_rs_per_spot hold_stop_rs_entry hold_giveback_rs hold_trail_prem_pts hold_delta_abs
hold_biggest_today hold_day_best_rs hold_data_bad hold_stop_near hold_stop_imminent hold_fast_start
""".split()


# ── memo: what the hold facts need to remember between seconds ────────────────────────────────────────
def extend_memo(memo, ctx, eng, pos):
    now = ctx["now_s"]
    memo.hold_best_fav = None            # best spot excursion seen (trade direction) ...
    memo.hold_best_t = now               # ... and when it last improved
    memo.hold_fut_best = None            # best futures excursion since entry (trade direction)
    memo.hold_fut_best_t = now
    memo.hold_idle_since = None          # when spot speed fell below the theta flat speed
    memo.hold_ret_bid_max = 0.0          # best sellable return seen (bid)
    memo.hold_ladder_rung = 0
    memo.hold_fast_start = False
    memo.hold_ttq = deque()              # (t, ttq) 1 Hz, 90 s, on the held row: volume over the last minute
    sig = pos.get("signal") or {}
    memo.hold_r15_in = _n(sig.get("r15"))
    memo.hold_sigma15_in = _n(sig.get("sigma15"))
    memo.hold_regime_in = sig.get("regime") or pos.get("regime")
    memo.hold_regime_dir_in = sig.get("regime_dir")


def _ensure_memo(memo, ctx):
    if not hasattr(memo, "hold_best_t"):
        extend_memo(memo, ctx, None, {})


def _ladder_rung(ret):
    r = 0
    for rung in (10, 15, 20, 25):
        if ret >= rung:
            r = rung
    return r


# ── the facts ───────────────────────────────────────────────────────────────────────────────────────────
def extend_facts(f, ctx, eng, book, memo):
    """Adds the hold_* keys. Reads only ctx / engine objects / the book; None where the data is missing."""
    _ensure_memo(memo, ctx)
    now = ctx["now_s"]
    p = book.pos
    d = f.get("dir") or 1
    entry = f.get("entry") or p.get("entry") or 0.0
    qty = f.get("qty") or 0
    bp = book.p or {}
    trail = _n(bp.get("spot_trail")) or _n(bp.get("d_star")) or 12.0
    f["hold_trail_pts"] = trail
    # the stall clock: seconds since the best spot last improved (kept here; the book only keeps the level)
    bf = f.get("best_spot_fav")
    if bf is not None and (memo.hold_best_fav is None or bf > memo.hold_best_fav + 1e-9):
        memo.hold_best_fav = bf
        memo.hold_best_t = now
    f["hold_stall_s"] = now - memo.hold_best_t
    f["hold_stall_m"] = f["hold_stall_s"] / 60.0
    f["hold_new_best_recent"] = bool(bf is not None and bf > 0 and f["hold_stall_s"] <= 3.0)
    # futures confirmation: a new futures extreme within 10 s of the new spot extreme
    fut = _n(ctx.get("fut"))
    fut_in = _n(p.get("fut_in"))
    ffav = (fut - fut_in) * d if (fut is not None and fut_in is not None) else None
    if ffav is not None and (memo.hold_fut_best is None or ffav > memo.hold_fut_best + 1e-9):
        memo.hold_fut_best = ffav
        memo.hold_fut_best_t = now
    f["hold_fut_best_fav"] = memo.hold_fut_best
    f["hold_fut_confirm"] = bool(ffav is not None and (ffav or 0) > 0 and now - memo.hold_fut_best_t <= 10.0
                                 and now - memo.hold_best_t <= 10.0)
    # theta on the calendar clock (0-DTE), the flat speed and the idle clock
    theta = f.get("theta_min")
    tc = (theta * 375.0 / 1440.0) if (theta is not None and f.get("zero_dte")) else theta
    delta = f.get("delta")
    ad = abs(delta) if delta is not None else None
    f["hold_delta_abs"] = ad
    f["hold_theta_cal"] = tc
    f["hold_theta_cal_abs"] = abs(tc) if tc is not None else None
    f["hold_flat_speed"] = (abs(tc) / ad) if (tc is not None and ad) else None
    f["hold_theta_rs_min"] = (abs(tc) * qty) if tc is not None else None
    f["hold_theta_3m_rs"] = (abs(tc) * qty * 3) if tc is not None else None
    r60 = f.get("spot_r60")
    speed = abs(r60) if r60 is not None else None
    f["hold_spot_speed_1m"] = speed
    if speed is not None and f["hold_flat_speed"] is not None and speed < f["hold_flat_speed"]:
        memo.hold_idle_since = memo.hold_idle_since if memo.hold_idle_since is not None else now
    else:
        memo.hold_idle_since = None
    f["hold_idle_s"] = (now - memo.hold_idle_since) if memo.hold_idle_since is not None else 0.0
    f["hold_theta_idle"] = bool(f["hold_idle_s"] >= THETA_IDLE_S)
    # the sellable P&L: the bid, not the last print
    bid = f.get("bid")
    ltp = f.get("ltp")
    pnl_pts = f.get("pnl_pts")
    bs = (bid - entry) if (bid is not None and entry) else None
    f["hold_bid_sellable"] = bs
    f["hold_ret_bid"] = (100.0 * bs / entry) if (bs is not None and entry) else None
    f["hold_bid_rs"] = (bs * qty) if bs is not None else None
    best_pct = f.get("best_pct") or 0.0
    f["hold_giveback_bid"] = (best_pct - f["hold_ret_bid"]) if f["hold_ret_bid"] is not None else None
    f["hold_prem_lag"] = f["hold_giveback_bid"]
    f["hold_bid_loss_ltp_gain"] = bool(bs is not None and bs < 0 and (pnl_pts or 0) > 0)
    if f["hold_ret_bid"] is not None:
        memo.hold_ret_bid_max = max(memo.hold_ret_bid_max, f["hold_ret_bid"])
        rung = _ladder_rung(f["hold_ret_bid"])
        memo.hold_ladder_rung = max(memo.hold_ladder_rung, rung)
        if f["hold_ret_bid"] >= 10 and (f.get("hold_s") or 0) <= 60:
            memo.hold_fast_start = True
    f["hold_best_ret_bid"] = memo.hold_ret_bid_max
    f["hold_ladder_rung"] = memo.hold_ladder_rung
    f["hold_fast_start"] = memo.hold_fast_start
    for k in ("5_10", "10_15", "10_20", "15_25", "20_25", "20_30", "25_30"):
        a, b = HOLD_REF["ladder_" + k]
        f["hold_ladder_p" + k] = a / b
    f["hold_ref_date"] = HOLD_REF["date"]
    # the profit lock (D-127): pos['lock_armed'], pos['lock_floor'], pos['best_prem']; None = no lock
    lock_on = bool(p.get("lock_armed")) and p.get("lock_floor") is not None
    floor = _n(p.get("lock_floor")) if lock_on else None
    f["hold_lock_on"] = lock_on
    f["hold_lock_floor"] = floor
    f["hold_lock_q"] = (100.0 * (floor / entry - 1.0)) if (floor is not None and entry) else None
    f["hold_lock_rs"] = ((floor - entry) * qty) if floor is not None else None
    f["hold_lock_gap"] = (f["hold_ret_bid"] - f["hold_lock_q"]) if (floor is not None and f["hold_ret_bid"] is not None) else None
    f["hold_lock_pct"] = _n(bp.get("lock_pct")) or None
    f["hold_lock_trail_pct"] = _n(bp.get("lock_trail_pct")) or None
    f["hold_best_prem"] = _n(p.get("best_prem"))
    # room: walls, round numbers, the day's extreme (futures high / low: the engine's own high-water marks)
    room = f.get("wall_room")
    f["hold_room_pct"] = (100.0 * room * ad / ltp) if (room is not None and ad and ltp) else None
    f["hold_wall_rs"] = (room * ad * qty) if (room is not None and ad) else None
    f["hold_wall_prem"] = (ltp + room * ad) if (room is not None and ad and ltp) else None
    sp = f.get("spot")
    if sp is not None:
        rn = (math.floor(sp / 100.0) + 1) * 100.0 if d > 0 else (math.ceil(sp / 100.0) - 1) * 100.0
        f["hold_round_next"] = rn
        f["hold_round_dist"] = abs(rn - sp)
    else:
        f["hold_round_next"] = f["hold_round_dist"] = None
    dh, dl = _n(getattr(eng, "_day_hi", None)), _n(getattr(eng, "_day_lo", None))
    lvl = dh if d > 0 else dl
    f["hold_hi_lo"] = "high" if d > 0 else "low"
    f["hold_day_level"] = lvl
    f["hold_day_room"] = ((lvl - fut) * d) if (lvl is not None and fut is not None) else None
    # volume on the held strike over the last minute (ttq is cumulative); the engine ring is 60 s, we keep 90 s
    vol = None
    try:
        m = eng.m
        tq = float(m.ttq[p["id"], m.k])
        if math.isfinite(tq):
            memo.hold_ttq.append((now, tq))
            while memo.hold_ttq and now - memo.hold_ttq[0][0] > 90:
                memo.hold_ttq.popleft()
            old = next((v for t, v in memo.hold_ttq if now - t <= 60), None)
            if old is not None and tq >= old and now - memo.hold_ttq[0][0] >= 30:
                vol = tq - old
    except Exception:
        vol = None
    f["hold_vol_1m"] = vol
    f["hold_pos_vs_vol"] = (100.0 * qty / vol) if vol else None
    f["hold_thin"] = bool(f["hold_pos_vs_vol"] is not None and f["hold_pos_vs_vol"] > THIN_PCT)
    try:
        f["hold_agg_b"] = float(eng.flow.agg_b[p["id"]]); f["hold_agg_s"] = float(eng.flow.agg_s[p["id"]])
    except Exception:
        f["hold_agg_b"] = f["hold_agg_s"] = None
    spn, spi = f.get("spread_now"), f.get("spread_in")
    f["hold_spread_pct"] = (100.0 * spn / ltp) if (spn is not None and ltp) else None
    f["hold_spread_x"] = (spn / spi) if (spn is not None and spi) else None
    f["hold_spread_wide"] = bool((f["hold_spread_pct"] or 0) > 1.0 or (f["hold_spread_x"] or 0) > 3.0)
    # attribution in rupees: delta (entry delta × spot move), vega (Δiv × vega), the rest
    din = f.get("delta_in")
    sp_in = f.get("spot_in")
    drs = (din * (sp - sp_in) * qty) if (din is not None and sp is not None and sp_in is not None) else None
    f["hold_delta_rs"] = drs
    f["hold_vega_rs"] = f.get("iv_rs")
    pnl_rs = f.get("pnl_rs")
    f["hold_resid_rs"] = (pnl_rs - drs - (f["hold_vega_rs"] or 0.0)) if (pnl_rs is not None and drs is not None) else None
    f["hold_delta_only_pct"] = (100.0 * drs / (entry * qty)) if (drs is not None and entry and qty) else None
    ivc = f.get("iv_chg")
    f["hold_iv_off"] = bool(ivc is not None and ivc <= IV_OFF and (f.get("spot_fav") or 0) > 0)
    f["hold_iv_with"] = bool(ivc is not None and ivc >= IV_WITH)
    # breadth with the 0.03 % stock threshold (T08's measure), from the entry snapshot the core memo keeps
    n_with = n_against = None
    best_sym = worst_sym = None
    worst_move = None
    try:
        import numpy as np
        dm = eng.domino
        px_in = memo.eq_px_in
        if len(dm.eq_ids) and len(px_in) == len(dm.eq_ids):
            px = eng.m.ltp[dm.eq_ids, eng.m.k]
            with np.errstate(divide="ignore", invalid="ignore"):
                mv = (px / px_in - 1.0) * 100.0 * d
            ok = np.isfinite(mv)
            n_with = int(np.sum(ok & (mv > STOCK_MOVE_PCT)))
            n_against = int(np.sum(ok & (mv < -STOCK_MOVE_PCT)))
            if ok.any():
                mvf = np.where(ok, mv, 0.0)
                j, k = int(np.argmax(mvf)), int(np.argmin(mvf))
                best_sym = dm.eq_sym[j] if mvf[j] > STOCK_MOVE_PCT else None
                worst_sym = dm.eq_sym[k] if mvf[k] < -STOCK_MOVE_PCT else None
                worst_move = float(mvf[k]) if worst_sym else None
        f["hold_n_eq"] = int(len(dm.eq_ids))
    except Exception:
        f["hold_n_eq"] = None
    f.update(hold_n_with=n_with, hold_n_against=n_against, hold_best_stock=best_sym, hold_worst_stock=worst_sym,
             hold_worst_move=worst_move)
    nw, na = n_with or 0, n_against or 0
    f["hold_basket_with"] = bool(n_with is not None and nw - na >= BASKET_WITH)
    f["hold_basket_turned"] = bool(n_against is not None and na >= nw + BASKET_TURNED_MARGIN)
    f["hold_basket_split"] = bool(n_against is not None and na >= BASKET_SPLIT and not f["hold_basket_turned"])
    # trend, regime, the entry context
    tr = _n(ctx.get("trend30"))
    f["hold_trend30"] = (tr * d) if tr is not None else None
    f["hold_with_trend"] = None if tr is None else (1 if f["hold_trend30"] >= 5 else (-1 if f["hold_trend30"] <= -5 else 0))
    f["hold_regime_in"] = memo.hold_regime_in
    f["hold_regime_dir_in"] = memo.hold_regime_dir_in
    rg = ctx.get("regime") or {}
    f["hold_regime_text"] = rg.get("text")
    rs_now, rd_now = f.get("regime"), f.get("regime_dir")
    weak = ("RANGE", "EXHAUSTION")
    f["hold_regime_flipped"] = bool(rs_now and ((rd_now is not None and rd_now == -d and memo.hold_regime_dir_in != -d)
                                                or (rs_now in weak and memo.hold_regime_in not in weak)))
    f["hold_r15_in"] = memo.hold_r15_in
    f["hold_sigma15_in"] = memo.hold_sigma15_in
    dom = ctx.get("domino") or {}
    f["hold_sigma15"] = _n(dom.get("sigma15"))
    f["hold_late_entry"] = bool(memo.hold_r15_in is not None and memo.hold_sigma15_in and abs(memo.hold_r15_in) > 2 * memo.hold_sigma15_in)
    f["hold_lull"] = bool(f["hold_sigma15"] is not None and f["hold_sigma15"] <= LULL_SIGMA and speed is not None and speed < LULL_SPEED)
    eom = f.get("entry_over_mid")
    f["hold_mid_in"] = (entry - eom) if eom is not None else None
    f["hold_costly_entry"] = bool((eom or 0) > 0.5 or (spi is not None and entry and 100.0 * spi / entry > 1.0))
    # the fixed-strike straddle watch and the dealer-gamma map (read-only views)
    try:
        sw = eng.watch.view(series=False) if getattr(eng, "watch", None) else {}
    except Exception:
        sw = {}
    f["hold_straddle_state"] = sw.get("state")
    f["hold_straddle_leg"] = sw.get("leg")
    f["hold_straddle_slope"] = _n(sw.get("chg5"))
    spx = f.get("straddle_px") or _n(sw.get("px"))
    f["hold_straddle_px"] = spx
    f["hold_move_vs_straddle"] = (abs(sp - sp_in) / spx) if (sp is not None and sp_in is not None and spx) else None
    st = (sw.get("state") or "")
    f["hold_straddle_spike_with"] = None if not st.startswith("SPIKE") else (sw.get("leg") == f.get("rr"))
    gv = getattr(getattr(eng, "gex", None), "v", None) or {}
    f["hold_gex_ok"] = bool(gv.get("ok"))
    f["hold_gex_flip"] = _n(gv.get("flip")); f["hold_gex_call"] = _n(gv.get("call_wall")); f["hold_gex_put"] = _n(gv.get("put_wall"))
    f["hold_gex_regime"] = gv.get("regime") if gv.get("ok") else None
    gw = f["hold_gex_call"] if d > 0 else f["hold_gex_put"]
    f["hold_gex_wall"] = gw
    f["hold_gex_room"] = ((gw - sp) * d) if (gw is not None and sp is not None) else None
    f["hold_gex_tendency"] = {"DAMPEN": "damp", "AMPLIFY": "accelerate"}.get(f["hold_gex_regime"] or "", "do either")
    bc = f.get("basis_chg")
    f["hold_basis_chg_dir"] = (bc * d) if bc is not None else None
    # the clock
    from .. import config
    dt = ctx["now_dt"]
    hm = dt.hour * 60 + dt.minute
    zd = bool(f.get("zero_dte"))
    f["hold_lunch"] = bool(LUNCH[0] <= hm < LUNCH[1])
    f["hold_last_hour"] = bool(hm >= (LAST_HOUR_0DTE if zd else LAST_HOUR))
    le = config.ZERO_DTE_NO_ENTRY if zd else config.LAST_ENTRY
    f["hold_no_reentry"] = bool(hm >= config.mins(le))
    f["hold_last_entry_hms"] = "%02d:%02d" % le
    mtf = f.get("min_to_flatten")
    f["hold_time_room_pts"] = (speed * mtf) if (speed is not None and mtf is not None and mtf > 0) else None
    f["hold_exit_est_rs"] = ((ltp - trail * ad - entry) * qty) if (ltp and ad) else None
    sd = f.get("stop_dist")
    f["hold_stop_rs"] = (sd * ad * qty) if (sd is not None and ad) else None
    f["hold_rs_per_spot"] = (ad * qty) if ad else None
    f["hold_stop_rs_entry"] = (trail * abs(din) * qty) if din is not None else None
    f["hold_giveback_rs"] = ((f.get("giveback_pts") or 0.0) * qty)
    f["hold_trail_prem_pts"] = (trail * ad) if ad else None
    f["hold_stop_near"] = bool(sd is not None and sd <= STOP_NEAR_PTS)
    f["hold_stop_imminent"] = bool(sd is not None and sd <= STOP_IMMINENT_PTS)
    # the day
    best_rs = max([t.get("pnl_rs") or 0.0 for t in (book.trades or [])], default=None)
    f["hold_day_best_rs"] = best_rs
    f["hold_biggest_today"] = bool(pnl_rs is not None and pnl_rs > 0 and (best_rs is None or pnl_rs > best_rs))
    qa = f.get("quote_age")
    f["hold_data_bad"] = bool(f.get("gap_on") or f.get("exit_pending") or (qa is not None and qa > 5.0))


# ── slots: every number a phrasing prints, ready as a string ────────────────────────────────────────────
def _f0(x):
    return "—" if x is None else f"{x:,.0f}"


def _f1(x):
    return "—" if x is None else f"{x:.1f}"


def _f2(x):
    return "—" if x is None else f"{x:.2f}"


def _s1(x):
    return "—" if x is None else f"{x:+.1f}"


def _ratio(k):
    a, b = HOLD_REF[k]
    return f"{a} of {b}"


def _pct_of(k):
    a, b = HOLD_REF[k]
    return f"{100.0 * a / b:.0f} %"


def _common(f):
    g = f.get
    ret_bid = g("hold_ret_bid")
    lq = g("hold_lock_q")
    return {
        "ref_date": HOLD_REF["date"], "ref_n": str(HOLD_REF["n_trades"]),
        "ref_l5_10": _ratio("ladder_5_10"), "ref_l10_15": _ratio("ladder_10_15"), "ref_l10_20": _ratio("ladder_10_20"),
        "ref_l15_25": _ratio("ladder_15_25"), "ref_l20_25": _ratio("ladder_20_25"), "ref_l20_30": _ratio("ladder_20_30"),
        "ref_l25_30": _ratio("ladder_25_30"), "ref_p10_20": _pct_of("ladder_10_20"),
        "ref_gb5": _pct_of("gb5_recover"), "ref_gb5_n": _ratio("gb5_recover"),
        "ref_stall_120": f"{HOLD_REF['stall_120']} %", "ref_stall_180": f"{HOLD_REF['stall_180']} %",
        "ref_stall_max": mins(HOLD_REF["stall_max_s"]), "ref_first10": f"{HOLD_REF['first10_median_s']} s",
        "ref_first10_fast": _ratio("first10_fast"),
        "ref_with_mean": pct(HOLD_REF["with_trend_mean"], 0), "ref_with_median": pct(HOLD_REF["with_trend_median"], 0),
        "ref_against_mean": pct(HOLD_REF["against_trend_mean"], 0), "ref_against_median": pct(HOLD_REF["against_trend_median"], 0),
        "ref_against_winners": _ratio("against_trend_winners"), "ref_range_mean": pct(HOLD_REF["range_regime_mean"], 0),
        "ref_bw": f"{HOLD_REF['basket_win_with']:.0f}", "ref_bl": f"{HOLD_REF['basket_lose_with']:.0f}",
        "ref_bl_against": f"{HOLD_REF['basket_lose_against']:.0f}",
        "ref_gb_mean": f"{HOLD_REF['giveback_mean']:.0f} %", "ref_gb_half_flat": _ratio("gb_half_flat"),
        "ref_losers_no10": _ratio("losers_no10"), "ref_longest_winner": f"{HOLD_REF['longest_winner_min']} min",
        "ref_big3": HOLD_REF["big3"], "ref_top_trade": HOLD_REF["top_trade"], "ref_last_hour_trade": HOLD_REF["last_hour_trade"],
        "ref_lull": HOLD_REF["lull_pts"], "ref_round_tests": str(HOLD_REF["round_tests"]),
        "ref_lesson": HOLD_REF["lesson_trade"], "ref_lesson_pts": str(HOLD_REF["lesson_pts"]), "ref_lesson_rs": HOLD_REF["lesson_rs"],
        "ten": "10", "fifteen": "15", "twenty": "20", "twentyfive": "25", "thirty": "30", "five": "5", "idle_min": "3",
        "stall_watch_min": "2", "stall_warn_min": "3", "no_survive_min": "5", "delta_run": "0.9", "flat_0dte": "15:00",
        "dte_clock": "expiry-day clock" if g("zero_dte") else "engine clock",
        "trail": _f0(g("hold_trail_pts")), "stop_pts": _f1(g("stop_dist")), "stop_spot": _f0(g("stop_spot")),
        "spot_txt": _f0(g("spot")), "spot_in_txt": _f0(g("spot_in")), "fut_txt": _f0(g("fut")),
        "fav_pts": _s1(g("best_spot_fav")), "now_pts": _s1(g("spot_fav")),
        "pnl_rs": rs(g("pnl_rs")), "ret_pct": pct(g("ret_pct")), "best_ret": pct(g("best_pct")),
        "giveback": _f1(g("giveback_pct")), "giveback_rs": rs(g("hold_giveback_rs")),
        "ret_bid": pct(ret_bid), "bid_rs": rs(g("hold_bid_rs")), "prem_lag": _f1(g("hold_prem_lag")),
        "last": _f2(g("ltp")), "bid": _f2(g("bid")), "ask": _f2(g("ask")), "entry": _f2(g("entry")),
        "spread": _f2(g("spread_now")), "spread_pct": _f2(g("hold_spread_pct")), "spread_x": _f1(g("hold_spread_x")),
        "entry_spread": _f2(g("spread_in")), "mid_in": _f2(g("hold_mid_in")), "entry_vs_mid": _s1(g("entry_over_mid")),
        "entry_vs_mid_pct": _f1((100.0 * g("entry_over_mid") / g("entry")) if (g("entry_over_mid") is not None and g("entry")) else None),
        "entry_quality": ("fair" if not g("hold_costly_entry") else f"{_s1(g('entry_over_mid'))} pts over the mid"),
        "hold_s_txt": _f0(g("hold_s")), "hold_m": _f1(g("hold_min")), "held": mins(g("hold_s")),
        "stall_m": _f1(g("hold_stall_m")), "stall_s_txt": _f0(g("hold_stall_s")),
        "theta_cal": _f2(g("hold_theta_cal_abs")), "flat_speed": _f2(g("hold_flat_speed")),
        "theta_rs_min": rs(g("hold_theta_rs_min")), "theta_3m_rs": rs(g("hold_theta_3m_rs")),
        "speed": _f1(g("hold_spot_speed_1m")), "sigma15": _f1(g("hold_sigma15")),
        "delta": _f2(g("delta")), "delta_abs": _f2(g("hold_delta_abs")), "vega": _f1(g("vega")),
        "iv_in": _f1(g("iv_in")), "iv_now": _f1(g("iv")), "d_iv": _s1(g("iv_chg")),
        "vega_rs": rs(g("hold_vega_rs")), "delta_rs": rs(g("hold_delta_rs")), "resid_rs": rs(g("hold_resid_rs")),
        "delta_only_pct": pct(g("hold_delta_only_pct")),
        "vega_rs_per_pt": rs((g("vega") or 0) * (g("qty") or 0) if g("vega") is not None else None),
        "vega_3pt": _f1(3 * g("vega") if g("vega") is not None else None),
        "lock_q": pct(lq), "lock_rs": rs(g("hold_lock_rs")), "lock_gap": _f1(g("hold_lock_gap")),
        "lock_floor": _f2(g("hold_lock_floor")), "lock_P": _f0(g("hold_lock_pct")), "lock_R": _f0(g("hold_lock_trail_pct")),
        "lock_status": (f"holds {pct(lq)} ({rs(g('hold_lock_rs'))})" if g("hold_lock_on") else "is not armed"),
        "wall_level": _f0(g("wall_level")), "wall_room": _f0(g("wall_room")), "wall_prem_pct": _f1(g("hold_room_pct")),
        "wall_rs": rs(g("hold_wall_rs")), "wall_prem": _f2(g("hold_wall_prem")),
        "round_next": _f0(g("hold_round_next")), "round_room": _f0(g("hold_round_dist")),
        "day_level": _f0(g("hold_day_level")), "day_room": _f0(g("hold_day_room")), "hi_lo": g("hold_hi_lo") or "extreme",
        "n_with": "—" if g("hold_n_with") is None else str(g("hold_n_with")),
        "n_against": "—" if g("hold_n_against") is None else str(g("hold_n_against")),
        "n_against_minus1": "—" if g("hold_n_against") is None else str(max(g("hold_n_against") - 1, 0)),
        "n_eq": "—" if g("hold_n_eq") is None else str(g("hold_n_eq")),
        "best_stock": g("hold_best_stock") or "no one", "worst_stock": g("hold_worst_stock") or "no one",
        "worst_move": pct(g("hold_worst_move"), 2),
        "trend30": _s1(g("hold_trend30")), "regime": (g("regime") or "—").lower(), "regime_in": (g("hold_regime_in") or "—").lower(),
        "regime_dir": "—" if g("regime_dir") is None else ("up" if g("regime_dir") > 0 else "down"),
        "regime_text": g("hold_regime_text") or "—",
        "r15": _s1(g("hold_r15_in")), "sigma15_in": _f1(g("hold_sigma15_in")),
        "straddle": _f1(g("hold_straddle_px")), "straddle_state": g("hold_straddle_state") or "—",
        "straddle_leg": g("hold_straddle_leg") or "—", "straddle_slope": _s1(g("hold_straddle_slope")),
        "move_vs_straddle_pct": _f0((g("hold_move_vs_straddle") or 0) * 100 if g("hold_move_vs_straddle") is not None else None),
        "gex_flip": _f0(g("hold_gex_flip")), "gex_call": _f0(g("hold_gex_call")), "gex_put": _f0(g("hold_gex_put")),
        "gex_regime": (g("hold_gex_regime") or "—").lower(), "gex_wall": _f0(g("hold_gex_wall")), "gex_room": _f0(g("hold_gex_room")),
        "gex_tendency": g("hold_gex_tendency") or "do either",
        "basis": _s1(g("basis")), "basis_in": _s1(g("basis_in")), "basis_chg": _s1(g("hold_basis_chg_dir")),
        "vol_1m": _f0(g("hold_vol_1m")), "pos_vs_vol": _f1(g("hold_pos_vs_vol")),
        "lead": _f2(g("book_lead")), "imb_o": _s1(g("book_imb")) if g("book_imb") is not None else "—",
        "cls_so": (g("sellers_o") or "—").lower(), "cls_sq": (g("sellers_q") or "—").lower(),
        "mins_to_exit": _f0(g("min_to_flatten")), "time_exit": g("flatten_hms") or "—",
        "time_room_pts": _f0(g("hold_time_room_pts")), "last_entry": g("hold_last_entry_hms") or "—",
        "time_in": g("time_hms") or "—",
        "stop_rs": rs(g("hold_stop_rs")), "exit_est_rs": rs(g("hold_exit_est_rs")), "rs_per_spot": rs(g("hold_rs_per_spot")),
        "stop_rs_entry": rs(g("hold_stop_rs_entry")), "rs_per_pt": rs(g("qty")), "trail_pts_prem": _f1(g("hold_trail_prem_pts")),
        "cap_deployed": rs(g("capital_deployed")), "capital": rs(g("capital")),
        "day_pnl": rs(g("realised_rs")), "day_best": rs(g("hold_day_best_rs")),
        "swings_used": "—" if g("trades_today") is None else str(g("trades_today") + 1),
        "wins": "—" if g("wins_today") is None else str(g("wins_today")),
        "quote_age": _f1(g("quote_age")), "pending_text": (f", exit pending ({g('pending_reason')})" if g("exit_pending") else ""),
        "pending_reason": g("pending_reason") or "—", "blackout_why": "data gap" if g("gap_on") else "quote stale",
        "ladder_rung": str(g("hold_ladder_rung") or 0),
        "exit": "—", "reason": "—", "vega_share_pct": "—",          # filled by review_card at the close
    }


def S(fn=None):
    if fn is None:
        return _common
    return lambda f: {**_common(f), **fn(f)}


# ── the honesty guard on every confidence remark ───────────────────────────────────────────────────────
def _honest(f):
    """False when confidence would be a lie: spot within a quarter trail of the stop, the bid showing a loss while
    the last print shows a gain, or the held quote stale / an exit pending."""
    sd = f.get("stop_dist")
    trail = f.get("hold_trail_pts") or 12.0
    if sd is not None and sd <= 0.25 * trail:
        return False
    if f.get("hold_bid_loss_ltp_gain"):
        return False
    if f.get("hold_data_bad"):
        return False
    return True


def C(key, kind, prio, when, phrasings, **kw):
    """A CONFIDENCE template: the honesty guard is part of the predicate."""
    return Template(key=key, kind=kind, tone="confidence", prio=prio, when=lambda f: _honest(f) and when(f),
                    phrasings=phrasings, slots=kw.pop("slots", _common), **kw)


def T(key, kind, tone, prio, when, phrasings, **kw):
    return Template(key=key, kind=kind, tone=tone, prio=prio, when=when, phrasings=phrasings,
                    slots=kw.pop("slots", _common), **kw)


_g = lambda f, k, d=0.0: (f.get(k) if f.get(k) is not None else d)


# ── TEMPLATES ─────────────────────────────────────────────────────────────────────────────────────────
TEMPLATES: List[Template] = [
    # ── 5.1 CONFIDENCE (13) ──────────────────────────────────────────────────────────────────────────
    C("conf.trail_room_sellers", "book", 60, cooldown_s=45, min_hold_s=10, step={"stop_dist": 3.0},
      when=lambda f: _g(f, "stop_dist", -1) >= 8 and f.get("sellers_o") in ("PULLED", "DRAIN-FAST") and _g(f, "ret_pct") > 0,
      phrasings=["The trail is {stop_pts} points away and sellers on your {strike} {rr} are pulling their orders ({cls_so}) — the evidence favours staying.",
                 "{stop_pts} points of room to the stop, and the sellers' order count on {strike} {rr} reads {cls_so}. Nothing here argues for leaving.",
                 "Room: {stop_pts} pts. Sellers on your strike: {cls_so}. Both on your side.",
                 "Your stop sits at {stop_spot}, {stop_pts} points behind the action, while the other side of your book is walking away ({cls_so})."],
      note="stop_dist from the book's stop_spot; sellers_o = flow.side(id,+1) orders class on the held contract."),
    C("conf.basket_with", "basket", 55, cooldown_s=60, min_hold_s=20, step={"hold_n_with": 2.0},
      when=lambda f: f.get("hold_basket_with"),
      phrasings=["{n_with} of {n_eq} heavyweights are moving with you since entry — {best_stock} leads. On {ref_date} winners averaged {ref_bw} with, losers {ref_bl}.",
                 "The basket agrees: {n_with} with, {n_against} against. {best_stock} is doing the pulling.",
                 "This is not one index tick; {n_with} of the {n_eq} big names moved your way since {time_in}.",
                 "Breadth is with you — {n_with} stocks in step, only {n_against} leaning the other way ({worst_stock})."],
      note="n_with/n_against: cash stocks moved > 0.03 % since entry, signed in the trade's direction (memo.eq_px_in)."),
    C("conf.with_trend", "structure", 45, cooldown_s=120, min_hold_s=5,
      when=lambda f: f.get("hold_with_trend") == 1 and f.get("regime") == "DIRECTIONAL",
      phrasings=["You are riding the half-hour trend ({trend30} pts) in a {regime} regime. Trades entered this way averaged {ref_with_mean} on {ref_date}; against the trend, {ref_against_mean}.",
                 "Trend and trade point the same way: half-hour drift {trend30} pts, regime {regime}. The odds you started with are the good ones.",
                 "The regime is {regime} and the half-hour drift is {trend30} pts your way. The rule is doing its work.",
                 "With-trend entries: median {ref_with_median} on {ref_date}. That is the pool this trade is drawn from ({trend30} pts of drift)."],
      note="trend30 = ctx['trend30'] (futures 30-min move) signed in the trade direction; regime from ctx."),
    C("conf.iv_with", "greeks", 50, cooldown_s=90, step={"iv_chg": 1.0},
      when=lambda f: f.get("hold_iv_with"),
      phrasings=["IV on your strike is up {d_iv} points since entry — vega has added {vega_rs} on top of the move itself.",
                 "The market is paying up for your side: IV {iv_in} → {iv_now}. That is {vega_rs} of your P&L that spot did not have to earn.",
                 "Fear is being bid into your leg ({d_iv} IV pts). It came off fast on {ref_date} too, so the lock matters — but right now it is a tailwind.",
                 "Vega is working for you: {vega_rs} from IV, {delta_rs} from the move."],
      note="iv_chg on the held contract; vega_rs = Δiv × vega × qty."),
    C("conf.new_best", "trail", 65, cooldown_s=20, step={"best_spot_fav": 3.0},
      when=lambda f: f.get("hold_new_best_recent") and _g(f, "hold_ret_bid", -1) >= 5,
      phrasings=["New high: spot {spot_txt}, your best so far — the trail steps to {stop_spot}.",
                 "Fresh best. The stop moves with it: {stop_spot}, locking more of the {pnl_rs}.",
                 "{fav_pts} points of excursion now; the trail follows at {trail}.",
                 "Another new best at {spot_txt}. The rule is doing the holding for you."],
      note="hold_stall_s <= 3 s and the sellable return >= 5 %."),
    C("conf.fast_start", "premium", 50, once=True,
      when=lambda f: f.get("hold_fast_start") and _g(f, "hold_s") <= 90,
      phrasings=["+{ten} % on the bid inside {hold_s_txt} s. {ref_first10_fast} of the trades that got here on {ref_date} did it this fast, and {ref_l10_20} went on to +{twenty} %.",
                 "A quick start: +{ten} % in {hold_s_txt} s. Fast starts were the rule on the winning trades of {ref_date} (median {ref_first10}).",
                 "The premium answered immediately — {ret_pct} in {hold_s_txt} s. That is what a real break looks like.",
                 "You are +{ten} % at {hold_s_txt} s. Median on {ref_date} was {ref_first10}; you are in the good half."],
      note="bid return >= 10 % within 60 s of entry (memo flag)."),
    C("conf.straddle_with", "structure", 45, cooldown_s=120,
      when=lambda f: f.get("hold_straddle_spike_with") is True,
      phrasings=["The ATM straddle ({straddle}) is spiking and your leg is carrying it — the market is buying the move, not fading it.",
                 "Straddle {straddle}, up on the {rr} side: the move is being priced as it happens, not after.",
                 "Expansion on your leg ({straddle_state}). On {ref_date} the two biggest winners both had IV rising into the move.",
                 "The straddle agrees with you: {straddle_state}, led by the {rr}, {straddle} on the ATM."],
      note="straddle_watch.state SPIKE <leg> with leg == the held rr."),
    C("conf.fresh_ground", "structure", 40, cooldown_s=180,
      when=lambda f: f.get("hold_day_room") is not None and f["hold_day_room"] <= 0 and _g(f, "wall_room", -1) >= 40,
      phrasings=["You are on fresh ground — the day {hi_lo} ({day_level}) is behind the price and the next OI wall is {wall_room} points away.",
                 "Nothing on today's chart stands between here and {wall_level}; the day's {hi_lo} at {day_level} is behind you.",
                 "Beyond the day's {hi_lo} ({day_level}): whoever sold there is under water, and the next wall is {wall_room} pts off.",
                 "Open air: day {hi_lo} broken, wall at {wall_level}, {wall_room} pts of room."],
      note="day high/low = the engine's futures high-water marks (eng._day_hi/_day_lo) vs the futures mid."),
    C("conf.lock_armed", "trail", 55, cooldown_s=120, step={"hold_lock_q": 2.0},
      when=lambda f: f.get("hold_lock_on") and _g(f, "hold_lock_q") > 0,
      phrasings=["The lock is on: whatever happens now, {lock_q} ({lock_rs}) is kept. Everything above it is free to run.",
                 "You cannot give it all back from here — the lock holds {lock_rs}. That stays in your pocket whatever follows.",
                 "Locked: {lock_q}. The trail sits at {stop_spot}, {stop_pts} pts away; the worst case is a paid trade.",
                 "{lock_rs} is banked by rule (floor {lock_floor}). The rest is upside you do not have to protect by hand."],
      note="pos['lock_armed'], pos['lock_floor'] (D-127): lock_q = floor over entry in %."),
    C("conf.book_leads", "book", 40, cooldown_s=90,
      when=lambda f: _g(f, "book_lead", -1) >= 0.3 and _g(f, "book_imb") > 0.1,
      phrasings=["The order book on {strike} {rr} has been predicting its next tick (lead {lead}) and it leans your way ({imb_o}).",
                 "The standing orders on your strike are ahead of the price (lead {lead}), and they are on your side ({imb_o}).",
                 "Book-leads-price {lead}, imbalance {imb_o} toward buyers — the people queuing on your contract want it.",
                 "The queue agrees: buyers heavier by {imb_o}, and this book has been right lately (lead {lead})."],
      note="book_lead / book_imb from book_state (flow.lead, imbalance for the bought side)."),
    C("conf.futures_confirm", "structure", 40, cooldown_s=120,
      when=lambda f: f.get("hold_fut_confirm"),
      phrasings=["Futures confirmed the new spot {hi_lo}: {fut_txt}, basis {basis}. Not a cash-only flicker.",
                 "Spot ({spot_txt}) and futures ({fut_txt}) printed the new {hi_lo} together. The move is in both markets.",
                 "The futures are leading now (basis {basis}); the index is being pulled, not pushed.",
                 "Both legs of the market agree: fut {fut_txt}, spot {spot_txt}."],
      note="a new futures extreme since entry within 10 s of the new spot extreme (memo clocks)."),
    C("conf.volume_with", "book", 35, cooldown_s=120, min_hold_s=30,
      when=lambda f: _g(f, "hold_vol_1m") >= 1_000_000 and _g(f, "hold_agg_b") > _g(f, "hold_agg_s"),
      phrasings=["{vol_1m} units traded on your strike in the last minute, more at the ask than the bid. Buyers are chasing it.",
                 "Heavy and one-sided: {vol_1m} units a minute, aggressors buying. Your {qty} is {pos_vs_vol} % of that.",
                 "The contract is liquid ({vol_1m} units/min) and being bought. Nobody is forcing anything.",
                 "Volume {vol_1m}/min on {strike} {rr}, buyers in control."],
      note="hold_vol_1m = Δttq over 60 s on the held row; agg_b/agg_s = flow aggressor EWMA."),
    C("conf.capital_small_risk", "trail", 35, cooldown_s=300,
      when=lambda f: f.get("hold_stop_rs") is not None and _g(f, "pnl_rs") > 0 and f["hold_stop_rs"] < 0.4 * f["pnl_rs"],
      phrasings=["The trail can only cost {stop_rs} of the {pnl_rs} on the table. The risk is a fraction of the reward now.",
                 "Worst case at the stop: give back {stop_rs}, keep the rest of {pnl_rs}. That is the shape of a trade worth staying in.",
                 "Risk to the trail {stop_rs}; unrealised {pnl_rs}. The ratio is on your side.",
                 "The stop is {stop_pts} pts × {delta_abs} × {qty} = {stop_rs}. Measured against {pnl_rs}, that is a cheap wait."],
      note="hold_stop_rs = stop_dist × |delta| × qty."),
    # ── 5.2 ANTICIPATION (11) ────────────────────────────────────────────────────────────────────────
    T("ant.next_wall", "structure", "information", 45, cooldown_s=180, step={"wall_room": 15.0},
      when=lambda f: _g(f, "wall_room", -1) >= 20 and f.get("hold_room_pct") is not None,
      phrasings=["The next wall is {wall_level}, {wall_room} points away; at your delta that is about +{wall_prem_pct} % on the premium. The rule will trail it — you don't have to decide.",
                 "Room to {wall_level}: {wall_room} pts, worth roughly {wall_rs} if it gets there. Nothing to do but let the trail follow.",
                 "If spot reaches the {wall_level} wall your premium is near {wall_prem}. That is the size of the \"what if\"; the trail keeps the \"what is\".",
                 "{wall_room} pts to the OI wall. The arithmetic: × {delta_abs} × {qty} = {wall_rs}. The decision: none, the rule carries it."],
      note="pressure.destination in the trade direction; room × |delta| / premium."),
    T("ant.round_number", "structure", "information", 40, cooldown_s=180, step={"hold_round_dist": 20.0},
      when=lambda f: f.get("hold_round_dist") is not None and 10 <= f["hold_round_dist"] <= 60,
      phrasings=["{round_next} is {round_room} points away. Round numbers draw stops and targets; expect a fight there, not a wall.",
                 "Next round level {round_next}, {round_room} pts. On {ref_date} a round line was tested {ref_round_tests} times before it gave.",
                 "{round_room} pts to {round_next}. If it breaks, the trail follows; if it holds, the trail decides.",
                 "The crowd watches {round_next}. You are {round_room} away with a stop {stop_pts} behind."],
      note="next 100-multiple of spot in the trade direction."),
    T("ant.day_extreme", "structure", "information", 40, cooldown_s=180, step={"hold_day_room": 15.0},
      when=lambda f: f.get("hold_day_room") is not None and 0 < f["hold_day_room"] <= 60,
      phrasings=["The day's {hi_lo} is {day_room} pts ahead. Breaking it would put everyone who sold there under water.",
                 "{day_room} points to the day {hi_lo} at {day_level}. Beyond it is open air.",
                 "Target of record: the session {hi_lo}, {day_room} pts off. Not a promise, a landmark.",
                 "Between here and the day's {hi_lo}: {day_room} pts. Between here and your stop: {stop_pts}."],
      note="engine futures day high/low vs the futures mid, in the trade direction."),
    T("ant.ladder", "premium", "information", 50, cooldown_s=86400.0, step={"hold_ladder_rung": 5.0},
      when=lambda f: _g(f, "hold_ladder_rung") >= 10 and _honest(f),
      phrasings=["+{ladder_rung} % on the bid. On {ref_date}: from +{ten} %, {ref_l10_20} trades went on to +{twenty} % and {ref_l10_15} to +{fifteen} %; from +{twenty} %, {ref_l20_25} reached +{twentyfive} %. The rule holds for the ones that run; the lock protects you from the rest.",
                 "+{ladder_rung} % now. The {ref_date} ladder: +{fifteen} → +{twentyfive} {ref_l15_25}, +{twenty} → +{thirty} {ref_l20_30}. Better than a coin above +{twenty}, worse than a certainty below.",
                 "Rung +{ladder_rung} %. +{twenty} → +{twentyfive} was {ref_l20_25} on {ref_date}; +{twentyfive} → +{thirty} was {ref_l25_30}. Momentum in the premium was real above +{twenty} %.",
                 "+{ladder_rung} % reached. The trail is now {stop_pts} pts away: that is the whole cost of finding out whether the next rung comes ({ref_p10_20} did from +{ten} %)."],
      slots=S(lambda f: {"ladder_rung": str(f.get("hold_ladder_rung") or 0)}),
      note="hold_ladder_rung = highest of 10/15/20/25 % reached on the BID; re-fires on each new rung (step), not on time."),
    T("ant.straddle_room", "structure", "information", 35, cooldown_s=240, min_hold_s=30,
      when=lambda f: f.get("hold_move_vs_straddle") is not None and f["hold_move_vs_straddle"] < 0.5 and _g(f, "spot_fav") > 0,
      phrasings=["Spot has moved {now_pts} pts since entry against a straddle of {straddle}: the market priced more than this for the day.",
                 "The move so far is {move_vs_straddle_pct} % of the straddle ({straddle}). The expected range has not been used up.",
                 "{now_pts} pts done; the straddle says the day is worth {straddle}. Plenty of range unspent.",
                 "Against an ATM straddle of {straddle}, this {now_pts}-pt move is still small."],
      note="|spot − spot_in| / ATM straddle premium."),
    T("ant.vega_tailwind", "greeks", "information", 35, cooldown_s=240,
      when=lambda f: f.get("rr") == "PE" and _g(f, "hold_straddle_slope") > 0 and f.get("vega") is not None,
      phrasings=["Puts gain twice on a fall: delta and the IV that comes with fear. The straddle is rising ({straddle_slope} over five minutes) — if it keeps going, vega adds {vega} pts per IV point, {vega_rs_per_pt} per point.",
                 "Each IV point is worth {vega_rs_per_pt} to you at vega {vega}. The straddle is drifting up ({straddle_slope}).",
                 "A fall that frightens pays twice. Vega {vega} pts per vol point, {qty} units.",
                 "If IV runs another three points the premium gains about {vega_3pt} pts before spot moves at all."],
      note="straddle_watch.chg5 > 0 on a held PE."),
    T("ant.gex_room", "structure", "information", 30, cooldown_s=300,
      when=lambda f: f.get("hold_gex_ok") and _g(f, "hold_gex_room", -1) > 0,
      phrasings=["Dealer gamma: flip {gex_flip}, call wall {gex_call}, put wall {gex_put}. In {gex_regime} gamma, moves tend to {gex_tendency}.",
                 "The gamma map says {gex_regime}: hedging flows {gex_tendency}. The next dealer wall in your direction is {gex_wall}.",
                 "{gex_room} pts to the dealers' {gex_wall}. Expect hedging to {gex_tendency} until then.",
                 "Gamma regime {gex_regime} (flip {gex_flip}). That is the weather, not the trade."],
      note="eng.gex.v: ok / flip / call_wall / put_wall / regime (DAMPEN | AMPLIFY | MIXED)."),
    T("ant.time_room", "time", "information", 35, cooldown_s=300, min_hold_s=60,
      when=lambda f: _g(f, "min_to_flatten") > 30 and _g(f, "hold_spot_speed_1m") > 0,
      phrasings=["At the last minute's pace ({speed} pts/min) the flatten at {time_exit} leaves room for another {time_room_pts} pts. The trail will decide long before the clock does.",
                 "Clock: {mins_to_exit} min. Pace: {speed} pts/min. Time is not what ends this trade; the trail is.",
                 "{mins_to_exit} minutes of session left — a lot of trail steps.",
                 "The clock is generous today: {mins_to_exit} min to the flatten at {time_exit}."],
      note="speed × minutes to the flatten."),
    T("ant.rule_holds", "trail", "information", 40, cooldown_s=180, min_hold_s=15,
      when=lambda f: _g(f, "ret_pct") > 0 and _g(f, "stop_dist", -1) >= 6,
      phrasings=["You do not have to call the top. The trail is {stop_pts} pts back and will follow every new high at {trail}.",
                 "The rule does the selling, at {stop_spot} or wherever the trail is by then. Your job is to let it.",
                 "Anticipate all you like — the exit is already placed, at {stop_spot}, and it only moves one way.",
                 "The hardest part of holding is already automated: the stop at {stop_spot}, {stop_pts} away, rising with the price."],
      note="plain description of the trail; no number is a forecast."),
    T("ant.basis_lead", "structure", "information", 30, cooldown_s=300, step={"hold_basis_chg_dir": 5.0},
      when=lambda f: _g(f, "hold_basis_chg_dir") >= 5,
      phrasings=["The futures basis has moved {basis_chg} pts your way since entry ({basis_in} → {basis}): the futures crowd is leaning in before cash.",
                 "Basis {basis} now, {basis_in} at entry. Futures are running ahead of the index.",
                 "The futures are pricing more of this move than spot has delivered yet: basis {basis}.",
                 "Basis widening in your direction ({basis_chg} pts) — the derivative crowd expects spot to catch up."],
      note="basis_chg (core) × dir."),
    T("ant.bigger_than_best", "day", "information", 35, cooldown_s=300,
      when=lambda f: _g(f, "pnl_rs") > 0 and f.get("hold_day_best_rs") is not None and f["hold_day_best_rs"] > 0
      and f["pnl_rs"] > 0.8 * f["hold_day_best_rs"] and not f.get("hold_biggest_today"),
      phrasings=["This trade is within reach of the day's best ({day_best}). The rule does not care; the number is for you.",
                 "Open {pnl_rs}; best realised today {day_best}. Close.",
                 "If the trail takes it here it is nearly the biggest trade of the day ({pnl_rs} vs {day_best}). If it runs, more so. Either way the rule carries it.",
                 "{pnl_rs} on the table against a day best of {day_best}."],
      note="book.trades pnl_rs max vs the open P&L."),
    # ── 5.3 CAUTION (12) ─────────────────────────────────────────────────────────────────────────────
    T("cau.giveback", "premium", "caution", 60, cooldown_s=60, step={"giveback_pct": 3.0},
      when=lambda f: _g(f, "giveback_pct") >= GB_CAUTION and not (_g(f, "best_pct") >= GB_WARN_BEST and _g(f, "giveback_frac") > 0.5),
      phrasings=["You are {ret_pct} but have given back {giveback} % from the best; the lock {lock_status}. On {ref_date} {ref_gb5} of {five} % give-backs recovered to a new high.",
                 "Off the best by {giveback} %. About half of these ({ref_gb5_n}) came back on {ref_date}; half did not. The stop is {stop_pts} pts away either way.",
                 "{giveback} % given back from {best_ret}. Not a signal, a cost — the trail is paid for in exactly this currency.",
                 "Best was {best_ret}, now {ret_pct}. The lock {lock_status}; the trail keeps the decision."],
      note="giveback_pct (core) >= 5 and not GB_WARN."),
    T("cau.stall", "trail", "caution", 55, cooldown_s=90, step={"hold_stall_s": 60.0},
      when=lambda f: STALL_WATCH_S <= _g(f, "hold_stall_s") < STALL_WARN_S,
      phrasings=["No new high for {stall_m} minutes. {ref_stall_120} of two-minute stalls on {ref_date} still made a new best — but the clock is now charging {theta_cal} pts/min ({dte_clock}).",
                 "{stall_m} min since the last best. Spot needs {flat_speed} pts/min just to pay theta. Watching, not flinching.",
                 "The move has paused for {stall_m} min at {now_pts} pts. Most pauses resumed; the stop is {stop_pts} pts back if this one doesn't.",
                 "Quiet for {stall_m} min. The trail has not moved; neither has the risk."],
      note="hold_stall_s: seconds since best_spot_fav last improved."),
    T("cau.basket_split", "basket", "caution", 55, cooldown_s=90, min_hold_s=20, step={"hold_n_against": 2.0},
      when=lambda f: f.get("hold_basket_split"),
      phrasings=["The basket is split: {n_with} with you, {n_against} against — {worst_stock} is the one pulling the other way.",
                 "{n_against} heavyweights leaning against you ({worst_stock} {worst_move}). Losers on {ref_date} averaged {ref_bl_against} against.",
                 "Not everyone agrees: {worst_stock} and {n_against_minus1} others are going the other way.",
                 "The index is being carried by {n_with} names while {n_against} fight it. Thinner than it looks."],
      note="n_against >= 4 and not turned."),
    T("cau.iv_easing", "greeks", "caution", 50, cooldown_s=120, step={"iv_chg": 1.0},
      when=lambda f: f.get("iv_chg") is not None and -3 < f["iv_chg"] <= -1.5 and _g(f, "spot_fav") > 0,
      phrasings=["IV has eased {d_iv} points since entry; vega has taken {vega_rs} off a move that is otherwise yours.",
                 "The premium is lagging the index a little: IV {iv_in} → {iv_now}. Delta gave {delta_rs}, vega took {vega_rs}.",
                 "Vol is coming off ({d_iv}) as the move matures. Expect the premium to track spot less than one-for-one from here.",
                 "IV off {d_iv}. Not a turn — a tax."],
      note="−3 < iv_chg <= −1.5 with spot in favour."),
    T("cau.against_trend", "structure", "caution", 45, cooldown_s=300, min_hold_s=5,
      when=lambda f: f.get("hold_with_trend") == -1 and f.get("regime") != "DIRECTIONAL",
      phrasings=["This is a counter-trend trade (half-hour drift {trend30} pts the other way) in a {regime} regime. Such entries averaged {ref_against_mean} on {ref_date}, median {ref_against_median}. The rule is the same; expect less.",
                 "You are fighting the half-hour drift ({trend30} pts). It can work — {ref_against_winners} did on {ref_date} — but the base rate is thin.",
                 "Against the half-hour trend ({trend30}), regime {regime}. The trail is the same; the odds are not.",
                 "Counter-trend ({trend30} pts): the median outcome on {ref_date} was a scratch ({ref_against_median}). The trail stays strict."],
      note="trend30 against by >= 5 pts and the regime not DIRECTIONAL."),
    T("cau.sellers_refilling", "book", "caution", 50, cooldown_s=90,
      when=lambda f: f.get("sellers_o") == "REFILLING" and _g(f, "book_imb") < -0.1 and _g(f, "book_lead") >= 0.2,
      phrasings=["Sellers are refilling on your {strike} {rr} (orders {cls_so}, imbalance {imb_o}) and this book has been leading price (lead {lead}). Supply is coming back.",
                 "The other side of your contract is restocking ({cls_so}). On a book with lead {lead}, that has been meaning something.",
                 "Seller orders {cls_so}, imbalance {imb_o}. The queue is turning against you.",
                 "Fresh offers stacking on {strike} {rr} ({cls_so}). The trail is {stop_pts} pts away; the book is the early warning."],
      note="sellers_o REFILLING, imbalance against, lead >= 0.2."),
    T("cau.premium_lag", "premium", "caution", 60, cooldown_s=60, step={"hold_prem_lag": 2.0},
      when=lambda f: _g(f, "hold_stall_s", 999) <= 60 and _g(f, "best_spot_fav") > 0 and _g(f, "hold_prem_lag") > PREM_LAG_PCT and _g(f, "best_pct") >= 5,
      phrasings=["Spot just made a new best but your premium on the bid is {prem_lag} % below its own best. IV {d_iv} pts — the option is not following the index.",
                 "New spot high, no new premium high ({prem_lag} % off). Something in the vol surface is leaning against you ({d_iv} IV pts).",
                 "The index moved; the option didn't ({prem_lag} % behind its best). On {ref_date} the {ref_lesson} trade lost on a {ref_lesson_pts}-point winning move this way.",
                 "Divergence: spot best {fav_pts} pts, premium {prem_lag} % off its best. Watch the IV ({d_iv})."],
      note="a new spot best within 60 s while the bid return trails the best return by > 3 %."),
    T("cau.near_wall", "structure", "caution", 45, cooldown_s=180, step={"wall_room": 5.0},
      when=lambda f: f.get("wall_room") is not None and 0 < f["wall_room"] <= 15,
      phrasings=["The {wall_level} OI wall is {wall_room} pts ahead. Walls stall moves more often than they stop them, but expect the trail to be tested here.",
                 "Into the wall: {wall_level}, {wall_room} pts. Give-backs cluster at levels like this.",
                 "{wall_room} pts to {wall_level}. If spot stalls here for {stall_warn_min} min, the odds drop to even ({ref_stall_180}).",
                 "Approaching the wall at {wall_level}. The stop is {stop_pts} behind: a {trail}-pt rejection takes it."],
      note="pressure.destination room <= 15."),
    T("cau.spread_wide", "data", "caution", 50, cooldown_s=120,
      when=lambda f: f.get("hold_spread_wide"),
      phrasings=["The spread on {strike} {rr} has widened to {spread} ({spread_pct} % of premium). The bid, not the last, is what can actually be realised: {bid}.",
                 "Can you actually get out at this? The bid is {bid}, {spread} below the ask. Your real return is {ret_bid}.",
                 "Wide market: {bid} / {ask}. The engine fills at last; a live order would get the bid ({ret_bid}).",
                 "Spread {spread} pts, {spread_x}× what it was at entry. Liquidity is thinning on this strike."],
      note="spread > 1 % of premium or > 3× the entry spread."),
    T("cau.lull", "time", "caution", 40, cooldown_s=300, min_hold_s=60,
      when=lambda f: f.get("hold_lull") and _g(f, "ret_pct") > 0,
      phrasings=["The lull: fifteen-minute σ {sigma15} pts, last minute {speed}. Between late morning and mid-afternoon the median minute moved {ref_lull} pts on {ref_date}. Theta runs; spot idles.",
                 "Midday pace ({speed} pts/min). The trail is safe at {stop_pts} pts, but every idle minute costs {theta_cal} pts.",
                 "Quiet tape ({speed} pts/min, σ {sigma15}). Nothing wrong, nothing happening.",
                 "The market has gone quiet ({speed} pts/min). Your stop ({stop_spot}) has not."],
      note="sigma15 <= 5 and 1-min speed < 4."),
    T("cau.costly_entry", "entry", "caution", 45, once=True,
      when=lambda f: f.get("hold_costly_entry") and _g(f, "hold_s") <= 30,
      phrasings=["You paid {entry} against a mid of {mid_in} — {entry_vs_mid} pts above fair. Not a stupidity, a cost; the trade needs {entry_vs_mid_pct} % just to be flat on the mid.",
                 "Entered {entry_vs_mid} pts over the mid on a {entry_spread} spread. Remember it when you read the P&L.",
                 "The fill was on the costly side of the quote ({entry} vs mid {mid_in}). The first {entry_vs_mid_pct} % of this trade is paying for that.",
                 "Entry at the ask on a {entry_spread} spread: that is where the first part of the give-back went before the trade began."],
      note="entry − mid_in > 0.5 pt or entry spread > 1 % of the premium; first 30 s only."),
    T("cau.late_entry_wave", "entry", "caution", 45, once=True,
      when=lambda f: f.get("hold_late_entry") and _g(f, "hold_s") <= 60,
      phrasings=["You entered after a {r15}-pt fifteen-minute move (σ {sigma15_in}). Late entries on {ref_date} ran less: the fuel was partly spent.",
                 "This break came at the end of a {r15}-pt run. Expect a shorter leg and a quicker trail.",
                 "The fifteen-minute return before entry was {r15} pts against a σ of {sigma15_in}. Some of the move happened before you.",
                 "Entered into an extended move ({r15} pts). The trail is the same; the runway may be shorter."],
      note="|r15 at entry| > 2 × sigma15 at entry (pos['signal'])."),
    # ── 5.4 WARNING (12) ─────────────────────────────────────────────────────────────────────────────
    T("warn.theta_stall", "greeks", "warning", 75, cooldown_s=60, step={"hold_idle_s": 120.0},
      when=lambda f: f.get("hold_theta_idle") and f.get("hold_theta_cal") is not None,
      phrasings=["Theta is now eating {theta_cal} pts a minute ({dte_clock}) and spot has not outrun it for {idle_min} minutes — the clock is against you.",
                 "{idle_min} idle minutes. At {theta_cal} pts/min that is {theta_3m_rs} gone with the index flat. The stop is {stop_pts} pts away.",
                 "Spot needs {flat_speed} pts/min in your favour to stand still; it is giving {speed}. The premium is bleeding.",
                 "Idle index, running clock: {theta_cal} pts/min × {qty} = {theta_rs_min}/min."],
      note="1-min spot speed below |theta_cal|/|delta| for 3 consecutive minutes."),
    T("warn.vega_eating", "greeks", "warning", 80, cooldown_s=60, step={"iv_chg": 1.0},
      when=lambda f: f.get("hold_iv_off"),
      phrasings=["Spot has moved {now_pts} pts your way but IV is off {d_iv} points: vega has taken {vega_rs} against delta's {delta_rs}. The premium is not following the index.",
                 "This is the {ref_lesson} pattern from {ref_date}: a winning move in spot, a losing option. IV {iv_in} → {iv_now} ({vega_rs}).",
                 "Vol crush on your leg: {d_iv} IV pts = {vega_rs}. The move has to keep going just to stand still.",
                 "IV has come off {d_iv}. Your premium is {ret_pct} on a {now_pts}-pt move that should have been worth {delta_only_pct}."],
      note="iv_chg <= −3 with spot in favour — the 13:44 / 14:24 / 13:36 pattern of 19 Oct."),
    T("warn.basket_turned", "basket", "warning", 75, cooldown_s=60, min_hold_s=20, step={"hold_n_against": 2.0},
      when=lambda f: f.get("hold_basket_turned"),
      phrasings=["The basket has turned: {n_against} heavyweights against you, {n_with} with. {worst_stock} ({worst_move}) is the one ruining this trade.",
                 "Breadth has flipped. {worst_stock} led the turn; {n_against} of {n_eq} now lean the other way.",
                 "The index is being held up by {n_with} names only. The rest — {worst_stock} first — are leaving.",
                 "{n_against} against, {n_with} with. On {ref_date} that was the loser's profile ({ref_bl} with, {ref_bl_against} against)."],
      note="n_against >= n_with + 3."),
    T("warn.stop_near", "trail", "warning", 85, cooldown_s=20, step={"stop_dist": 1.0},
      when=lambda f: f.get("hold_stop_near") and not f.get("hold_stop_imminent"),
      phrasings=["The stop is {stop_pts} pts away at {stop_spot}. One ordinary minute of this tape ({speed} pts) can reach it.",
                 "{stop_pts} points of trail left. If it goes, it goes at {stop_spot} for about {exit_est_rs}.",
                 "Close to the trail: {stop_pts} pts. The rule is about to speak.",
                 "Spot {spot_txt}, stop {stop_spot}. The gap is {stop_pts}."],
      note="2 < stop_dist <= 4 pts."),
    T("warn.lock_near", "trail", "warning", 85, cooldown_s=20, step={"hold_lock_gap": 1.0},
      when=lambda f: f.get("hold_lock_on") and f.get("hold_lock_gap") is not None and f["hold_lock_gap"] <= 3,
      phrasings=["You are {ret_bid} on the bid; the lock fires at {lock_q}. {lock_gap} % of give-back left before the rule takes {lock_rs}.",
                 "The lock is {lock_gap} % away. It would close this at about {lock_floor} for {lock_rs}.",
                 "Near the lock: {ret_bid} vs {lock_q}. Nothing to do; it is the rule's exit, not yours.",
                 "{lock_gap} % between you and the lock. It protects {lock_rs} either way."],
      note="bid return within 3 % of the lock floor's return."),
    T("warn.giveback_half", "premium", "warning", 80, cooldown_s=60, step={"giveback_frac": 0.1},
      when=lambda f: _g(f, "best_pct") >= GB_WARN_BEST and _g(f, "giveback_frac") > 0.5,
      phrasings=["You have given back more than half of the best: {best_ret} → {ret_pct}. On {ref_date} {ref_gb_half_flat} trades that saw +{ten} % ended near flat this way.",
                 "Half the gain is gone ({giveback} % of {best_ret}). The shape of this trade has changed.",
                 "Best {best_ret}, now {ret_pct}. This is where \"it will come back\" costs the most.",
                 "More than half the best has been returned ({giveback} %). The trail at {stop_spot} is the floor; the lock {lock_status}."],
      note="best >= 10 % and more than half of it gone."),
    T("warn.regime_flip", "structure", "warning", 70, cooldown_s=120,
      when=lambda f: f.get("hold_regime_flipped"),
      phrasings=["The regime has changed since entry: {regime_in} → {regime}, direction {regime_dir}. Range-regime trades averaged {ref_range_mean} on {ref_date}.",
                 "The engine now reads the market as {regime} ({regime_text}). The thesis you entered on is weaker.",
                 "Regime turned {regime} (was {regime_in}). It does not exit you; it tells you what the trail is likely to meet.",
                 "{regime_in} at entry, {regime} now. The tape has changed character."],
      note="regime dir flipped to −dir, or state fell into RANGE / EXHAUSTION since entry."),
    T("warn.straddle_against", "structure", "warning", 70, cooldown_s=120,
      when=lambda f: f.get("hold_straddle_spike_with") is False,
      phrasings=["The ATM straddle ({straddle}) is spiking on the other leg ({straddle_leg}) — the market is buying protection against your direction.",
                 "Vol is being bought on the {straddle_leg} side ({straddle_state}). That is money betting the other way.",
                 "Straddle spike, wrong leg: {straddle_leg}. Your {rr} is not the one being chased.",
                 "The straddle expansion is against you ({straddle_leg}, {straddle})."],
      note="straddle_watch SPIKE on the leg that is not the held rr."),
    T("warn.stall_long", "trail", "warning", 70, cooldown_s=60, step={"hold_stall_s": 60.0},
      when=lambda f: _g(f, "hold_stall_s") >= STALL_WARN_S,
      phrasings=["No new high for {stall_m} minutes. On {ref_date} the odds of another best from here were even ({ref_stall_180}), and no trade survived a {no_survive_min}-minute stall.",
                 "{stall_m} min since the best. The trail took every stalled trade within {ref_stall_max} on {ref_date}.",
                 "{stall_m} minutes flat at {now_pts} pts. The stop is {stop_pts} away; theta is {theta_cal}/min.",
                 "Stalled {stall_m} min. Even odds now ({ref_stall_180}). The rule is close to deciding."],
      note="hold_stall_s >= 180."),
    T("warn.data", "data", "warning", 90, cooldown_s=10, step={"quote_age": 5.0},
      when=lambda f: f.get("hold_data_bad"),
      phrasings=["Data: the held quote is {quote_age} s old{pending_text}. No verdict on a frozen number — the rule is waiting for a fresh print.",
                 "Feed gap ({quote_age} s). The trail does not move on stale data and neither does this panel.",
                 "An exit is pending ({pending_reason}) — waiting for a quote fresher than {five} s (this one is {quote_age} s).",
                 "The engine is in blackout ({blackout_why}, quote {quote_age} s). Decisions resume when the data does."],
      note="gap_on, exit_pending, or the held quote older than 5 s."),
    T("warn.thin", "data", "warning", 65, cooldown_s=120, min_hold_s=30,
      when=lambda f: f.get("hold_thin"),
      phrasings=["Your {qty} units are {pos_vs_vol} % of the last minute's volume on {strike} {rr}. A market exit would move the price.",
                 "Thin strike: {vol_1m} units/min against your {qty}. The rule's fill at last is optimistic here.",
                 "Liquidity warning. The exchange traded {vol_1m} on this contract in the last minute; your position is {qty}.",
                 "{pos_vs_vol} % of a minute's volume — expect slippage beyond the {spread} spread."],
      note="qty > 10 % of the last minute's volume on the held strike."),
    T("warn.spot_fut_split", "structure", "warning", 65, cooldown_s=120, step={"hold_basis_chg_dir": 4.0},
      when=lambda f: _g(f, "hold_basis_chg_dir") <= -8,
      phrasings=["The futures have stopped confirming: basis {basis_in} → {basis}. Spot is making the move alone.",
                 "Futures are leaning the other way (basis {basis_chg} pts against you). Cash moves that futures do not follow tend to fade.",
                 "Spot moving, futures not ({basis_chg} pts of basis against) — the derivative crowd is not buying this leg.",
                 "Basis divergence {basis_chg} pts against the trade."],
      note="basis moved >= 8 pts against the trade since entry."),
    # ── 5.5 TIME (7) ─────────────────────────────────────────────────────────────────────────────────
    T("time.flatten_countdown", "time", "caution", 70, cooldown_s=60, step={"min_to_flatten": 5.0},
      when=lambda f: f.get("min_to_flatten") is not None and TIME_IMMINENT_MIN < f["min_to_flatten"] <= TIME_NEAR_MIN,
      phrasings=["{mins_to_exit} minutes to the flatten at {time_exit}; a timed exit is coming whatever spot does.",
                 "The clock closes this at {time_exit}. {mins_to_exit} min left; after that the rule takes the last print.",
                 "{mins_to_exit} min. On expiry the engine flattens at {flat_0dte} unless delta ≥ {delta_run} (yours: {delta}).",
                 "Time, not price, may end this one: {mins_to_exit} min to {time_exit}."],
      note="5 < min_to_flatten <= 15."),
    T("time.imminent", "time", "warning", 94, cooldown_s=15, step={"min_to_flatten": 1.0},
      when=lambda f: f.get("min_to_flatten") is not None and f["min_to_flatten"] <= TIME_IMMINENT_MIN,
      phrasings=["{mins_to_exit} min. The timed exit will take this at the next print after {time_exit}.",
                 "Under {five} minutes ({mins_to_exit}). Expect a TIME exit at about {last} for {pnl_rs}.",
                 "The session is ending for this trade: {mins_to_exit} min to {time_exit}.",
                 "{time_exit} is {mins_to_exit} min away. The rule does not wait for a better price."],
      note="min_to_flatten <= 5; the core's flatten_soon says the same from the config clock."),
    T("time.first_minute", "time", "information", 40, once=True,
      when=lambda f: _g(f, "hold_s") < 60 and f.get("stop_spot") is not None,
      phrasings=["First minute. Winners on {ref_date} reached +{ten} % at a median {ref_first10}; the stop is at {stop_spot}, {trail} pts from your entry.",
                 "Just in at {entry}, {lots} lots, {cap_deployed} deployed. The break gets a minute to prove itself.",
                 "{hold_s_txt} s in. Every winner of {ref_date} was already moving by {ref_first10} — but so were some losers.",
                 "Entry done. Stop {stop_spot}. The next sixty seconds usually tell."],
      note="fires once in the first minute."),
    T("time.long_hold", "time", "information", 45, cooldown_s=300,
      when=lambda f: _g(f, "hold_s") > LONG_HOLD_S,
      phrasings=["Held {hold_m} min. The longest winner on {ref_date} ran {ref_longest_winner}; long holds that were not already paid tended to end as scratches.",
                 "{hold_m} minutes in at {ret_pct}. Slow trades were the thin ones on {ref_date}.",
                 "{hold_m} min. The trail is {stop_pts} pts away; the clock is {theta_cal} pts/min against you.",
                 "A long one: {hold_m} min. Not wrong, just rarer than it feels."],
      note="hold_s > 600."),
    T("time.last_hour", "time", "information", 45, cooldown_s=600,
      when=lambda f: f.get("hold_last_hour"),
      phrasings=["Last hour. Entries close at {last_entry}; this is the last swing you can be in today. Gamma is highest, theta too ({theta_cal} pts/min).",
                 "The final hour: your delta is {delta}; on expiry, above {delta_run} the engine lets it run past {flat_0dte}.",
                 "Late session. On {ref_date} the last-hour trade made {ref_last_hour_trade} — the last hour moves, it just moves fast both ways.",
                 "Clock: {mins_to_exit} min to {time_exit}. Pace picks up late; the flatten comes first."],
      note="now >= 14:30 (14:00 on expiry)."),
    T("time.lunch", "time", "information", 35, cooldown_s=900,
      when=lambda f: f.get("hold_lunch") and f.get("hold_lull"),
      phrasings=["Lunch tape: median minute {ref_lull} pts on {ref_date}; right now {speed}. Trails survive; premiums leak.",
                 "Midday ({speed} pts/min). Expect stalls to run longer and mean less.",
                 "The market thins over lunch. Patience is cheaper now, but not free: {theta_cal} pts/min.",
                 "Lull hours. The stop is {stop_pts} away and nothing ({speed} pts/min) is pushing toward it."],
      note="12:00–13:15 and the lull facts true."),
    T("time.no_reentry", "time", "information", 50, once=True,
      when=lambda f: f.get("hold_no_reentry"),
      phrasings=["Entries are closed for the day ({last_entry}). Whatever this trade becomes, there is no next one.",
                 "This is the last trade of the day by rule (no entries after {last_entry}). The same rule carries it.",
                 "No re-entry after {last_entry}. The trail is the only decision left today.",
                 "Final position of the session (entries closed at {last_entry})."],
      note="now past LAST_ENTRY (ZERO_DTE_NO_ENTRY on expiry)."),
    # ── 5.6 DISCIPLINE (7) ───────────────────────────────────────────────────────────────────────────
    T("disc.rule_exits", "trail", "lesson", 50, cooldown_s=240, min_hold_s=45,
      when=lambda f: f.get("stop_spot") is not None and f.get("stop_dist") is not None,
      phrasings=["The rule exits at the trail, not at a feeling — the stop is at {stop_spot}, {stop_pts} points away.",
                 "Your exit is already placed: {stop_spot}. The only way out is spot coming {trail} pts off its best.",
                 "Nothing on this panel is a button. The trail at {stop_spot} is.",
                 "The decision was made at entry: {trail} pts behind the best. Everything since ({stop_pts} pts of room now) is bookkeeping."],
      note="always true in a trade; low priority."),
    T("disc.no_target", "premium", "lesson", 45, cooldown_s=300,
      when=lambda f: _g(f, "ret_pct") >= 15,
      phrasings=["There is no target. On {ref_date} the three biggest trades ({ref_big3}) all ran past the point where a target would have closed them.",
                 "Anticipating a price is fine; closing at one is not the rule. The trail took {ref_top_trade} by waiting.",
                 "Targets cap winners; the trail caps give-backs. Only one of those pays for the losers. You are {ret_pct}.",
                 "You are {ret_pct}. The rule does not know that number; it knows {stop_spot}."],
      note="ret_pct >= 15."),
    T("disc.biggest", "day", "lesson", 45, cooldown_s=300,
      when=lambda f: f.get("hold_biggest_today") and f.get("hold_day_best_rs") is not None,
      phrasings=["This is already the biggest trade of the day ({pnl_rs} vs {day_best} realised). Size does not change the rule.",
                 "Day's largest open P&L ({pnl_rs}). The stop is still {stop_pts} pts away; the number does not move it.",
                 "{pnl_rs} on {qty} units — larger than anything booked today. The trail is doing the holding.",
                 "Big one ({pnl_rs}). Same rule."],
      note="open pnl_rs > the day's best realised trade."),
    T("disc.swings", "day", "lesson", 35, cooldown_s=600, min_hold_s=120,
      when=lambda f: f.get("trades_today") is not None,
      phrasings=["Swing {swings_used} of the day. One trade per swing: when this closes, the next needs a new break.",
                 "Trade {swings_used} today; realised {day_pnl}. This one is {pnl_rs} on top.",
                 "Day so far: {swings_used} trades counting this one, {wins} won, {day_pnl}. This is the open one.",
                 "{swings_used} swings used. Capital now {capital}; deployed in this trade {cap_deployed}."],
      note="book.trades count + the open one."),
    T("disc.size", "entry", "lesson", 40, once=True,
      when=lambda f: _g(f, "hold_s") < 30 and f.get("qty"),
      phrasings=["{lots} lots = {qty} units; every premium point is {rs_per_pt}. The {trail}-pt trail is about {stop_rs_entry} at your delta.",
                 "Capital deployed {cap_deployed} of {capital}. At {delta} delta, one spot point ≈ {rs_per_spot}.",
                 "All-in: {lots} lots at {entry}. One premium point = {rs_per_pt}; one spot point ≈ {rs_per_spot}.",
                 "Size: {qty} units ({lots} lots). The arithmetic of the day is set; only the price moves now."],
      note="fires once in the first 30 s."),
    T("disc.day_context", "day", "lesson", 35, cooldown_s=600, min_hold_s=30,
      when=lambda f: _g(f, "realised_rs") < 0 and _g(f, "pnl_rs") > 0,
      phrasings=["The day is {day_pnl} realised; this trade is {pnl_rs}. Do not ask it to repair the day — ask it to follow the rule.",
                 "Down on the day ({day_pnl}), up on the trade ({pnl_rs}). The trail does not know either number.",
                 "{pnl_rs} open against {day_pnl} booked. Staying in to \"get back to flat\" is the feeling the rule exists to replace.",
                 "Day context: {day_pnl}. Trade context: {stop_pts} pts to the stop."],
      note="realised_rs < 0 with an open gain."),
    T("disc.entered_well", "entry", "praise", 35, once=True,
      when=lambda f: f.get("entry_over_mid") is not None and not f.get("hold_costly_entry") and _g(f, "hold_s") < 30,
      phrasings=["Entered at {entry} on a {entry_spread} spread, {entry_vs_mid} from the mid. Clean fill.",
                 "No \"entered costly\" today: {entry} vs mid {mid_in}.",
                 "The fill was fair ({entry_vs_mid} vs the mid). Whatever happens next is the market, not the entry.",
                 "Good entry price ({entry}, mid {mid_in}). The rest is the rule's."],
      note="the praise twin of cau.costly_entry."),
    # ── 5.7 EXIT REVIEW (7) — kind 'review': never selected live; review_card composes them ─────────
    T("exit.summary", "review", "lesson", 100, once=True, when=lambda f: True,
      phrasings=["Closed {ret_pct} ({pnl_rs}) at {exit}: best was {best_ret} — {giveback} % given back, {vega_share_pct} % of it IV coming off, the rest the trail's {trail} points.",
                 "Closed {lots} lots at {exit} on {reason}. Peak {best_ret}, realised {ret_pct}. Held {hold_m} min.",
                 "{reason} at {exit}. Attribution: delta {delta_rs}, vega {vega_rs}, theta and spread {resid_rs}.",
                 "Out: {pnl_rs}. Best seen {best_ret}; the trail cost {giveback} %, which on {ref_date} was about the average price ({ref_gb_mean}) of letting winners run."],
      note="line 1 of the review card."),
    T("exit.trail_cost", "review", "lesson", 60, once=True, when=lambda f: True,
      phrasings=["The trail took {giveback} % from the best. The same trail gave {ref_date}'s {ref_big3}. It is one rule, both ways.",
                 "Give-back {giveback} %: {trail} spot pts × {delta_abs} ≈ {trail_pts_prem} premium pts. That is the rule working, not failing.",
                 "From best to exit: {giveback} %. The average on {ref_date} was {ref_gb_mean}.",
                 "A trail is paid for at the end. This one cost {giveback_rs}."],
      note="TRAIL exit with best >= 10 %."),
    T("exit.stop_review", "review", "lesson", 60, once=True, when=lambda f: True,
      phrasings=["Stopped at {exit} for {pnl_rs}. Best was only {best_ret}: the break did not travel. On {ref_date} {ref_losers_no10} losers never saw +{ten} spot pts.",
                 "A loser that never worked: best {fav_pts} spot pts, trail at {trail}. Nothing to learn except that it was a losing break.",
                 "{pnl_rs}. Entry {entry}, exit {exit}, {hold_m} min. The basket was {n_with} with / {n_against} against — {worst_stock} led the other way.",
                 "Loss {pnl_rs}. The entry was {entry_quality}; the move was not there."],
      note="STOP exit or ret < −3 %."),
    T("exit.time_review", "review", "lesson", 60, once=True, when=lambda f: True,
      phrasings=["Flattened by the clock at {exit} for {pnl_rs}. The trail was {stop_pts} pts away; time got there first.",
                 "TIME exit. Best {best_ret}, closed {ret_pct}. No price decision was made — the session ended.",
                 "The clock closed this one. {pnl_rs}.",
                 "Timed out at {time_exit} with {ret_pct}."],
      note="reason starts with TIME."),
    T("exit.winning_move_lost", "review", "lesson", 70, once=True, when=lambda f: True,
      phrasings=["Spot moved {fav_pts} pts your way and the trade still lost {pnl_rs}: IV came off {d_iv} pts (vega {vega_rs}) and the trail gave back the rest. A right call, a wrong instrument today.",
                 "The index did what you said ({fav_pts} pts); the premium did not. Vega {vega_rs} against delta {delta_rs}.",
                 "Lost on a winning move ({fav_pts} pts, {pnl_rs}). {ref_lesson} on {ref_date} was the same: {ref_lesson_pts} pts in favour, {ref_lesson_rs}.",
                 "Direction right, vol wrong. {d_iv} IV pts cost {vega_rs}."],
      note="pnl < 0 with a best spot excursion >= 10 pts."),
    T("exit.what_followed", "review", "lesson", 50, once=True, when=lambda f: True,
      phrasings=["Where it went after the exit is for the tape to say: the rule is judged over a season, not a minute. Closed at {exit}.",
                 "Hindsight is allowed later, not now. Out at {exit}; the next minute will show whether the trail was early or right.",
                 "The receipt stops at {exit}. What the {strike} {rr} does next is noted on the tape, not acted on.",
                 "Closed at {exit}. The minute after is information, not a verdict on the rule."],
      note="the core gives no 60-s-later hook; this is the honest stand-in (see docs)."),
    T("exit.day_tally", "review", "lesson", 40, once=True, when=lambda f: True,
      phrasings=["Day: {swings_used} trades, {wins} won, {day_pnl}. Capital {capital}. Biggest {day_best}.",
                 "Booked. Running total {day_pnl} on {swings_used} swings.",
                 "{day_pnl} for the day ({wins} of {swings_used} won). The next entry needs a new break.",
                 "Tally: {wins}/{swings_used}, {day_pnl}."],
      note="line 3 of the review card."),
]

_BY_KEY = {t.key: t for t in TEMPLATES}


# ── the exit review card ────────────────────────────────────────────────────────────────────────────────
def _grade(t, f):
    """A..E for the trade's outcome against its own best (documented in docs/11_COMMENTARY.md):
    A realised >= 15 %; B >= 5 %; C a scratch (−3 .. 5 %); D lost >= 3 % after a best of >= 10 % (gave it back /
    vol took it); E lost >= 3 % and never saw +10 %."""
    ret = _n(t.get("ret_pct")) or 0.0
    entry = _n(t.get("entry")) or 0.0
    best = 100.0 * max(_n(t.get("peak_pts")) or 0.0, 0.0) / entry if entry else 0.0
    if ret >= 15:
        return "A"
    if ret >= 5:
        return "B"
    if ret > -3:
        return "C"
    return "D" if best >= 10 else "E"


def review_card(t: dict, f: dict) -> dict:
    """Three lines from the closed trade record `t` and the last facts `f`: the summary, the line that fits the
    exit (winning move lost > stop > time > trail cost > summary again), and the day tally."""
    f = dict(f or {})
    entry = _n(t.get("entry")) or f.get("entry") or 0.0
    qty = t.get("qty") or f.get("qty") or 0
    ret = _n(t.get("ret_pct")) or 0.0
    pnl_rs = _n(t.get("pnl_rs")) or 0.0
    best_pts = max(_n(t.get("peak_pts")) or 0.0, 0.0)
    best_pct = 100.0 * best_pts / entry if entry else 0.0
    gb = best_pct - ret
    gb_rs = (best_pts - (pnl_rs / qty if qty else 0.0)) * qty
    vega_rs = f.get("hold_vega_rs")
    share = None
    if vega_rs is not None and vega_rs < 0 and gb_rs > 0:
        share = max(0.0, min(100.0, 100.0 * (-vega_rs) / gb_rs))
    reason = str(t.get("reason") or "—")
    f.update(ret_pct=ret, pnl_rs=pnl_rs, best_pct=best_pct, giveback_pct=gb, hold_giveback_rs=gb_rs, entry=entry, qty=qty,
             lots=t.get("lots", f.get("lots")), strike=t.get("strike", f.get("strike")), rr=t.get("rr", f.get("rr")),
             hold_s=t.get("hold_s", f.get("hold_s")), hold_min=((t.get("hold_s") or 0.0) / 60.0),
             realised_rs=(f.get("realised_rs") or 0.0) + pnl_rs,
             wins_today=(f.get("wins_today") or 0) + (1 if pnl_rs > 0 else 0),
             capital=t.get("capital_after", f.get("capital")),
             hold_day_best_rs=max(f.get("hold_day_best_rs") or -1e18, pnl_rs) if (f.get("hold_day_best_rs") is not None or pnl_rs) else None)
    f.setdefault("hold_trail_pts", 12.0)
    extra = {"exit": _f2(_n(t.get("exit"))), "reason": reason.split(" ")[0], "vega_share_pct": _f0(share) if share is not None else "—"}
    tid = int(round(t.get("t_in") or 0))

    def line(key, n=0):
        tp = _BY_KEY[key]
        slots = {**f, **_common(f), **extra}
        try:
            return tp.pick(tid, n).format(**slots)
        except Exception as e:                                   # a bad slot shows the key, never breaks the exit
            return f"[{key}: {type(e).__name__}]"

    fav = f.get("best_spot_fav")
    if pnl_rs < 0 and fav is not None and fav >= 10:
        second = line("exit.winning_move_lost")
    elif reason.startswith("STOP") or ret < -3:
        second = line("exit.stop_review")
    elif reason.startswith("TIME"):
        second = line("exit.time_review")
    elif reason.startswith("TRAIL") and best_pct >= 10:
        second = line("exit.trail_cost")
    elif reason.startswith("LOCK"):
        second = line("exit.trail_cost", 1)
    else:
        second = line("exit.summary", 1)
    return {"grade": _grade(t, f), "lines": [line("exit.summary"), second, line("exit.day_tally")]}
