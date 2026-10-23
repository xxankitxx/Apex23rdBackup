"""Council 5 / T08: the hold-vs-exit commentary content (apex/engine/cmt_hold.py).
python3 tests/test_c5_cmt_hold.py  (numpy only)."""
import os
import re
import sys
import tempfile
import time
from collections import deque
from datetime import datetime
from types import SimpleNamespace

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c5h_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from apex import config  # noqa: E402
from apex.engine import commentary, cmt_hold  # noqa: E402

GROUPS = {"conf": 13, "ant": 11, "cau": 12, "warn": 12, "time": 7, "disc": 7, "exit": 7}
TRAIL = 12.0


# ── a fully populated synthetic facts dict (every base key + every hold key) ───────────────────────────
def synthetic():
    f = {k: None for k in commentary.FACT_KEYS}
    f.update({k: None for k in cmt_hold.FACTS})
    f.update(trade_id=1792382221, rr="PE", strike=23150, dir=-1, lots=28, qty=1820, entry=114.2, capital_deployed=207844.0,
             hold_s=240.0, hold_min=4.0, time_hms="11:28:53", zero_dte=True, ltp=140.0, bid=139.8, ask=140.2, pnl_pts=25.8,
             pnl_rs=46956.0, ret_pct=22.6, best_pts=28.0, best_pct=24.5, giveback_pts=2.2, giveback_pct=1.9, giveback_frac=0.08,
             prem_avg5=132.0, prem_vs_avg5=8.0, prem_slope60=1.5, entry_over_mid=0.1, spread_in=0.3, spread_now=0.4, spread_typical=0.3,
             entry_cost_rs=182.0, spot=23110.0, spot_in=23150.0, spot_fav=40.0, best_spot_fav=44.0, stop_spot=23118.0, stop_dist=8.0,
             trail_armed=True, locked_pts=32.0, locked_rs_est=38000.0, stop_rs_est=-9900.0, spot_retrace=4.0, spot_age=0.3, spot_r60=-3.0,
             delta=-0.68, delta_in=-0.66, theta_min=-0.48, theta_rs_min=-873.6, vega=1.8, iv=36.9, iv_in=34.2, iv_chg=2.7, iv_pts=4.9,
             iv_rs=8900.0, iv_share=0.19, theta_pts_so_far=-1.9, theta_rs_so_far=-3494.0, spot_pts_per_min_flat=0.7, delta_pts=22.8,
             atm_iv=15.1, atm_iv_in=14.4, atm_iv_chg=0.7,
             contrib=[{"sym": "HDFCBANK", "pts": 9.0, "z15": 1.2, "w": 11.0}, {"sym": "RELIANCE", "pts": -1.0, "z15": -0.3, "w": 8.0}],
             helpers=["HDFCBANK"], hurters=["RELIANCE"], top_helper="HDFCBANK", top_helper_pts=9.0, top_helper_share=0.4,
             top_hurter="RELIANCE", top_hurter_pts=-1.0, n_helping=10, n_hurting=1, basket_pts=22.0, basket_vs_spot=-18.0,
             sync_for=0.7, sync_against=0.1, z_for=1.8, first_mover="HDFCBANK", ep_type="SPOT-BREAKOUT",
             basis=6.0, basis_in=8.0, basis_chg=-2.0, oi_held=2.1e6, oi_held_chg=1.2e5, sellers_q="PULLED", sellers_o="DRAIN-FAST",
             book_imb=0.25, book_lead=0.4, run_score=0.5, straddle_state="EXPANDING", straddle_px=110.9, straddle_vwap=118.0,
             straddle_in=112.0, regime="DIRECTIONAL", regime_dir=-1, regime_with=1, wall_level=23000.0, wall_room=110.0,
             wall_room_in=150.0, fut_r60=3.0, bank_z=-1.1, min_to_flatten=211.0, min_to_0dte=211.0, flatten_hms="15:00",
             trades_today=13, wins_today=8, streak=2, realised_rs=215000.0, capital=315000.0, day_pct=215.0, best_trade_today=30.6,
             gap_on=False, quote_age=0.4, exit_pending=False, pending_reason=None)
    f.update(hold_trail_pts=TRAIL, hold_stall_s=2.0, hold_stall_m=0.03, hold_new_best_recent=True, hold_theta_cal=-0.125,
             hold_theta_cal_abs=0.125, hold_flat_speed=0.18, hold_theta_rs_min=227.5, hold_theta_3m_rs=682.5, hold_spot_speed_1m=3.0,
             hold_theta_idle=False, hold_idle_s=0.0, hold_bid_sellable=25.6, hold_ret_bid=22.4, hold_bid_rs=46592.0,
             hold_giveback_bid=2.1, hold_prem_lag=2.1, hold_bid_loss_ltp_gain=False, hold_best_ret_bid=24.0, hold_ladder_rung=20,
             hold_ladder_p5_10=0.75, hold_ladder_p10_15=0.62, hold_ladder_p10_20=0.38, hold_ladder_p15_25=0.54, hold_ladder_p20_25=0.88,
             hold_ladder_p20_30=0.62, hold_ladder_p25_30=0.71, hold_ref_date="19 Oct",
             hold_lock_on=True, hold_lock_floor=132.0, hold_lock_q=15.6, hold_lock_rs=32396.0, hold_lock_gap=6.8, hold_lock_pct=18.0,
             hold_lock_trail_pct=10.0, hold_best_prem=142.2, hold_room_pct=53.4, hold_wall_rs=136136.0, hold_wall_prem=214.8,
             hold_round_next=23100.0, hold_round_dist=10.0, hold_day_level=23090.0, hold_day_room=-20.0, hold_hi_lo="low",
             hold_vol_1m=1255150.0, hold_pos_vs_vol=0.15, hold_thin=False, hold_agg_b=900.0, hold_agg_s=500.0, hold_spread_pct=0.29,
             hold_spread_x=1.3, hold_spread_wide=False, hold_delta_rs=48048.0, hold_vega_rs=8900.0, hold_resid_rs=-9992.0,
             hold_delta_only_pct=23.1, hold_iv_off=False, hold_iv_with=True, hold_n_with=12, hold_n_against=0, hold_n_eq=14,
             hold_best_stock="HDFCBANK", hold_worst_stock=None, hold_worst_move=None, hold_basket_with=True, hold_basket_split=False,
             hold_basket_turned=False, hold_trend30=22.0, hold_with_trend=1, hold_regime_in="DIRECTIONAL", hold_regime_dir_in=-1,
             hold_regime_flipped=False, hold_regime_text="trend down, er5 0.7", hold_r15_in=9.0, hold_sigma15_in=6.0, hold_sigma15=6.5,
             hold_late_entry=False, hold_lull=False, hold_costly_entry=False, hold_mid_in=114.1, hold_straddle_state="SPIKE PE",
             hold_straddle_leg="PE", hold_straddle_slope=3.2, hold_straddle_px=110.9, hold_move_vs_straddle=0.36,
             hold_straddle_spike_with=True, hold_gex_ok=True, hold_gex_flip=23200.0, hold_gex_call=23300.0, hold_gex_put=23000.0,
             hold_gex_regime="AMPLIFY", hold_gex_wall=23000.0, hold_gex_room=110.0, hold_gex_tendency="accelerate", hold_fut_confirm=True,
             hold_fut_best_fav=42.0, hold_basis_chg_dir=2.0, hold_lunch=False, hold_last_hour=False, hold_no_reentry=False,
             hold_last_entry_hms="14:45", hold_time_room_pts=633.0, hold_exit_est_rs=32000.0, hold_stop_rs=9900.0, hold_rs_per_spot=1237.6,
             hold_stop_rs_entry=14414.0, hold_giveback_rs=4004.0, hold_trail_prem_pts=8.2, hold_delta_abs=0.68, hold_biggest_today=False,
             hold_day_best_rs=58331.0, hold_data_bad=False, hold_stop_near=False, hold_stop_imminent=False, hold_fast_start=True)
    return f


def test_shape_and_groups():
    assert len(cmt_hold.TEMPLATES) == 69
    assert sum(len(t.phrasings) for t in cmt_hold.TEMPLATES) == 276
    keys = [t.key for t in cmt_hold.TEMPLATES]
    assert len(set(keys)) == len(keys), "duplicate keys"
    for grp, n in GROUPS.items():
        assert sum(1 for k in keys if k.startswith(grp + ".")) == n, grp
    for t in cmt_hold.TEMPLATES:
        assert len(t.phrasings) >= 2 and t.kind in commentary.KINDS and t.tone in commentary.TONES, t.key
        assert 0 <= t.prio <= 100 and t.note, t.key
        assert (t.kind == "review") == t.key.startswith("exit."), t.key
    assert not (set(cmt_hold.FACTS) & set(commentary.FACT_KEYS)), "a hold fact shadows a base fact"
    assert len(set(cmt_hold.FACTS)) == len(cmt_hold.FACTS)
    assert all(k.startswith("hold_") for k in cmt_hold.FACTS)


def test_predicates_never_raise():
    empty = {k: None for k in commentary.FACT_KEYS}
    empty.update({k: None for k in cmt_hold.FACTS})
    full = synthetic()
    for t in cmt_hold.TEMPLATES:
        for f in (empty, full):
            t.when(f)                                   # must not raise
            if t.slots:
                t.slots(f)
            if t.score:
                t.score(f)


def test_phrasings_format_and_honesty_words():
    full = synthetic()
    empty = {k: None for k in commentary.FACT_KEYS}
    empty.update({k: None for k in cmt_hold.FACTS})
    bad_word = re.compile(r"\b(hold|sell|buy)\b", re.I)
    imperative = re.compile(r"(^|[.:;!?—]\s*)(hold|exit|sell|buy)\b", re.I)
    for t in cmt_hold.TEMPLATES:
        for ph in t.phrasings:
            assert not bad_word.search(ph), (t.key, ph)
            assert not imperative.search(ph), (t.key, ph)
            assert not re.search(r"\d", re.sub(r"\{[^}]*\}", "", ph)), ("literal number outside a slot", t.key, ph)
            for f in (full, empty):
                slots = dict(f)
                if t.slots:
                    slots.update(t.slots(f))
                txt = ph.format(**slots)                 # no KeyError, no formatting error on None
                assert txt
            if t.tone == "confidence":
                slots = dict(full); slots.update(t.slots(full))
                assert re.search(r"\d", ph.format(**slots)), ("a confidence remark must cite a number", t.key, ph)


def test_confidence_honesty_guard():
    """No confidence-tone remark may fire within a quarter trail of the stop, nor when the bid shows a loss while the
    last print shows a gain, nor on stale data."""
    conf = [t for t in cmt_hold.TEMPLATES if t.tone == "confidence"]
    base = synthetic()
    assert any(t.when(base) for t in conf), "the synthetic hold should light some confidence remark"
    near = dict(base, stop_dist=0.25 * TRAIL, hold_stop_near=True, hold_stop_imminent=False)
    assert not any(t.when(near) for t in conf)
    near2 = dict(base, stop_dist=1.0)
    assert not any(t.when(near2) for t in conf)
    bid_loss = dict(base, bid=113.9, hold_bid_sellable=-0.3, hold_ret_bid=-0.26, pnl_pts=0.4, ltp=114.6, hold_bid_loss_ltp_gain=True)
    assert not any(t.when(bid_loss) for t in conf)
    stale = dict(base, quote_age=7.0, hold_data_bad=True)
    assert not any(t.when(stale) for t in conf)
    # the warnings still speak in those states
    assert cmt_hold._BY_KEY["warn.data"].when(stale)
    assert cmt_hold._BY_KEY["warn.stop_near"].when(dict(base, stop_dist=3.0, hold_stop_near=True))


def test_key_predicates():
    f = synthetic()
    B = cmt_hold._BY_KEY
    assert B["conf.trail_room_sellers"].when(f) and B["conf.basket_with"].when(f) and B["conf.lock_armed"].when(f)
    assert B["conf.new_best"].when(f) and B["conf.iv_with"].when(f) and B["conf.with_trend"].when(f)
    assert B["ant.ladder"].when(f) and B["ant.next_wall"].when(f) and B["ant.round_number"].when(f)
    assert not B["warn.vega_eating"].when(f) and not B["cau.giveback"].when(f)
    g = dict(f, iv_chg=-4.0, hold_iv_off=True)
    assert B["warn.vega_eating"].when(g)
    g = dict(f, giveback_pct=6.0, giveback_frac=0.25)
    assert B["cau.giveback"].when(g) and not B["warn.giveback_half"].when(g)
    g = dict(f, giveback_pct=14.0, giveback_frac=0.57)
    assert B["warn.giveback_half"].when(g) and not B["cau.giveback"].when(g)
    g = dict(f, hold_stall_s=150.0)
    assert B["cau.stall"].when(g) and not B["warn.stall_long"].when(g)
    g = dict(f, hold_stall_s=200.0)
    assert B["warn.stall_long"].when(g) and not B["cau.stall"].when(g)
    g = dict(f, min_to_flatten=12.0)
    assert B["time.flatten_countdown"].when(g) and not B["time.imminent"].when(g)
    g = dict(f, min_to_flatten=4.0)
    assert B["time.imminent"].when(g) and not B["time.flatten_countdown"].when(g)
    assert B["warn.lock_near"].when(dict(f, hold_lock_gap=2.0))
    assert B["cau.premium_lag"].when(dict(f, hold_prem_lag=4.5))
    assert B["warn.basket_turned"].when(dict(f, hold_basket_turned=True))
    assert B["cau.basket_split"].when(dict(f, hold_basket_split=True))
    assert B["warn.theta_stall"].when(dict(f, hold_theta_idle=True))
    assert B["warn.straddle_against"].when(dict(f, hold_straddle_spike_with=False))
    assert not B["warn.straddle_against"].when(dict(f, hold_straddle_spike_with=None))
    assert B["disc.no_target"].when(f) and B["disc.rule_exits"].when(f)
    assert B["time.first_minute"].when(dict(f, hold_s=10.0)) and not B["time.first_minute"].when(f)
    # cool-downs and re-fire steps as the doc states
    assert B["warn.stop_near"].step == {"stop_dist": 1.0} and B["ant.ladder"].step == {"hold_ladder_rung": 5.0}
    assert B["conf.fast_start"].once and B["cau.costly_entry"].once and B["time.no_reentry"].once
    # the core picks a phrasing deterministically (crc32 of trade:key:n) and varies it across firings
    t = B["cau.giveback"]
    assert t.pick(1792382221, 0) == t.pick(1792382221, 0) and len({t.pick(1792382221, n) for n in range(12)}) >= 3


# ── a fake engine / ctx that drives extend_facts ─────────────────────────────────────────────────────
class _Market:
    def __init__(self, n=24, win=600):
        self.ltp = np.full((n, win), np.nan); self.ttq = np.full((n, win), np.nan)
        self.bid = np.full((n, win), np.nan); self.ask = np.full((n, win), np.nan)
        self.k = 0
        self.snap = {"oi": np.full(n, 2.0e6), "close": np.full(n, 100.0)}

    def change(self, arr, secs):
        return arr[:, self.k] - arr[:, (self.k - secs) % arr.shape[1]]


def _fake(now_s=1792385984.0, spot=23110.0, n=24):
    m = _Market(n)
    eq_ids = np.arange(14)
    m.ltp[:, 0] = 100.0; m.ttq[:, 0] = 1.0e6
    flow = SimpleNamespace(agg_b=np.full(n, 800.0), agg_s=np.full(n, 500.0), lead=np.full(n, 0.4),
                           run_score=lambda i, d, m: 0.5)
    domino = SimpleNamespace(eq_ids=eq_ids, eq_w=np.full(14, 100 / 14), eq_sym=[f"S{i}" for i in range(14)], state={"tiles": []}, episode=None)
    eng = SimpleNamespace(m=m, flow=flow, domino=domino, greek={20: {"delta": -0.68, "theta_min": -0.48, "vega": 1.8, "iv": 36.9}},
                          atm_iv=0.151, spot_hist=deque([(now_s - s, spot + 0.1 * s) for s in range(600, -1, -1)]),
                          fut_hist=deque(), _day_hi=23280.0, _day_lo=23090.0, books={}, champion="x",
                          watch=SimpleNamespace(view=lambda series=False: {"state": "SPIKE PE", "leg": "PE", "chg5": 3.2, "px": 110.9}),
                          gex=SimpleNamespace(v={"ok": True, "regime": "AMPLIFY", "flip": 23200.0, "call_wall": 23300.0, "put_wall": 23000.0}),
                          straddle=SimpleNamespace(view=lambda: {"px": 110.9, "state": "EXPANDING", "vwap": 118.0}),
                          pressure=SimpleNamespace(destination=lambda px, d: {"level": 23000.0, "room": abs(px - 23000.0)}),
                          bank=SimpleNamespace(z=-1.1), heroes=lambda: [], key={}, items=[])
    pos = {"id": 20, "key": "NIFTY|OPT|2026-10-19|23150|PE", "rr": "PE", "strike": 23150, "expiry": "2026-10-19", "dir": -1,
           "lots": 28, "qty": 1820, "entry": 114.2, "t_in": now_s - 240, "spot_in": 23150.0, "best_spot": 23106.0, "stop_spot": 23118.0,
           "fut_in": 23158.0, "peak_pts": 28.0, "delta_in": -0.66, "iv_in": 34.2, "mid_in": 114.1, "last": 140.0,
           "lock_armed": True, "lock_floor": 132.0, "best_prem": 142.2,
           "signal": {"r15": 9.0, "sigma15": 6.0, "regime": "DIRECTIONAL", "regime_dir": -1, "trend30": 22.0}}
    book = SimpleNamespace(pos=pos, p={"spot_trail": 12.0, "d_star": 12.0, "lock_pct": 18.0, "lock_trail_pct": 10.0},
                           trades=[{"pnl_rs": 58331.0, "pnl_pts": 32.0, "ret_pct": 28.1, "t_in": 1.0}], capital=315000.0)
    ctx = {"now_s": now_s, "now_dt": datetime(2026, 10, 19, 11, 28, 53, tzinfo=config.IST), "spot": spot, "spot_age": 0.3,
           "fut": spot + 6.0, "trend30": -22.0, "by_key": {pos["key"]: {"ltp": 140.0, "bid": 139.8, "ask": 140.2, "age": 0.4}},
           "by_id": {}, "domino": {"S_up": 0.1, "S_dn": 0.7, "z": -1.8, "sigma15": 6.5, "r15": -9.0}, "episode": {"first": "S1"},
           "regime": {"state": "DIRECTIONAL", "dir": -1, "text": "trend down"}, "blackout": {"on": False}, "book_state": {20: {"opp_q": 5, "opp_o": 4, "imb": 0.25, "lead": 0.4}}}
    return eng, book, ctx, pos


def _base_facts(ctx, eng, book, pos, memo):
    """What build_facts would give, without needing the real engine: the base keys this module reads."""
    f = {k: None for k in commentary.FACT_KEYS}
    now = ctx["now_s"]; p = pos; d = p["dir"]
    o = ctx["by_key"][p["key"]]
    f.update(trade_id=memo.trade_id, rr=p["rr"], strike=p["strike"], dir=d, lots=p["lots"], qty=p["qty"], entry=p["entry"],
             capital_deployed=p["entry"] * p["qty"], hold_s=now - p["t_in"], hold_min=(now - p["t_in"]) / 60, time_hms="11:28:53",
             zero_dte=True, ltp=o["ltp"], bid=o["bid"], ask=o["ask"], pnl_pts=o["ltp"] - p["entry"], pnl_rs=(o["ltp"] - p["entry"]) * p["qty"],
             ret_pct=100 * (o["ltp"] / p["entry"] - 1), best_pts=p["peak_pts"], best_pct=100 * p["peak_pts"] / p["entry"],
             giveback_pts=p["peak_pts"] - (o["ltp"] - p["entry"]), giveback_pct=100 * (p["peak_pts"] - (o["ltp"] - p["entry"])) / p["entry"],
             giveback_frac=0.08, entry_over_mid=0.1, spread_in=0.3, spread_now=0.4, spot=ctx["spot"], spot_in=p["spot_in"],
             spot_fav=(ctx["spot"] - p["spot_in"]) * d, best_spot_fav=(p["best_spot"] - p["spot_in"]) * d, stop_spot=p["stop_spot"],
             stop_dist=(ctx["spot"] - p["stop_spot"]) * d, trail_armed=True, locked_pts=32.0, spot_r60=-3.0, delta=-0.68, delta_in=-0.66,
             theta_min=-0.48, vega=1.8, iv=36.9, iv_in=34.2, iv_chg=2.7, iv_pts=4.86, iv_rs=4.86 * p["qty"], basis=6.0, basis_in=8.0,
             basis_chg=-2.0, sellers_q="PULLED", sellers_o="DRAIN-FAST", book_imb=0.25, book_lead=0.4, straddle_px=110.9,
             regime="DIRECTIONAL", regime_dir=-1, wall_level=23000.0, wall_room=110.0, min_to_flatten=211.0, flatten_hms="15:00",
             trades_today=1, wins_today=1, realised_rs=58331.0, capital=315000.0, gap_on=False, quote_age=0.4, exit_pending=False)
    return f


def test_extend_facts_fake_engine():
    eng, book, ctx, pos = _fake()
    memo = SimpleNamespace(t_in=pos["t_in"], trade_id=int(pos["t_in"]), eq_px_in=np.full(14, 99.9), N_in=23150.0)
    cmt_hold.extend_memo(memo, ctx, eng, pos)
    f = _base_facts(ctx, eng, book, pos, memo)
    cmt_hold.extend_facts(f, ctx, eng, book, memo)
    for k in cmt_hold.FACTS:
        assert k in f, k
    assert f["hold_trail_pts"] == 12.0
    assert abs(f["hold_theta_cal"] - (-0.48 * 375 / 1440)) < 1e-9          # 0-DTE: the calendar clock
    assert abs(f["hold_bid_sellable"] - (139.8 - 114.2)) < 1e-9 and f["hold_bid_loss_ltp_gain"] is False
    assert f["hold_lock_on"] and abs(f["hold_lock_q"] - 100 * (132.0 / 114.2 - 1)) < 1e-9 and f["hold_lock_rs"] > 0
    assert f["hold_round_next"] == 23100.0 and f["hold_round_dist"] == 10.0   # PE: the next 100-multiple below
    assert f["hold_hi_lo"] == "low" and f["hold_day_level"] == 23090.0 and abs(f["hold_day_room"] - (23090.0 - 23116.0) * -1) < 1e-9
    assert f["hold_n_with"] == 0 and f["hold_n_against"] == 14                # every stock +0.1 % against a PE
    assert f["hold_basket_turned"] and not f["hold_basket_with"]
    assert f["hold_trend30"] == 22.0 and f["hold_with_trend"] == 1          # ctx trend −22 × dir −1
    assert f["hold_straddle_spike_with"] is True and f["hold_gex_wall"] == 23000.0 and f["hold_gex_tendency"] == "accelerate"
    assert f["hold_room_pct"] is not None and f["hold_wall_rs"] > 0
    assert f["hold_lunch"] is False and f["hold_last_hour"] is False and f["hold_no_reentry"] is False and f["hold_last_entry_hms"] == "14:45"
    assert f["hold_ladder_rung"] == 20 and f["hold_fast_start"] is False
    assert f["hold_stall_s"] == 0.0 and f["hold_new_best_recent"]
    assert f["hold_vol_1m"] is None                                          # one ttq sample: no minute yet
    assert f["hold_day_best_rs"] == 58331.0 and f["hold_biggest_today"] is False
    assert f["hold_stop_near"] is False and f["hold_data_bad"] is False
    # the stall clock ticks when the best does not improve; volume appears after a minute of samples
    for s in range(1, 70):
        c2 = dict(ctx, now_s=ctx["now_s"] + s)
        eng.m.ttq[:, 0] = 1.0e6 + 2000.0 * s
        f2 = _base_facts(c2, eng, book, pos, memo)
        cmt_hold.extend_facts(f2, c2, eng, book, memo)
    assert f2["hold_stall_s"] == 69.0 and not f2["hold_new_best_recent"]
    assert f2["hold_vol_1m"] is not None and abs(f2["hold_vol_1m"] - 120000.0) < 1e-6
    assert f2["hold_pos_vs_vol"] is not None and f2["hold_thin"] is False
    # a new best resets the stall clock
    c3 = dict(ctx, now_s=ctx["now_s"] + 70, spot=23100.0)
    pos["best_spot"] = 23100.0
    f3 = _base_facts(c3, eng, book, pos, memo)
    cmt_hold.extend_facts(f3, c3, eng, book, memo)
    assert f3["hold_stall_s"] == 0.0
    # a lock that is not published reads as "no lock"
    pos2 = dict(pos); pos2.pop("lock_armed"); pos2.pop("lock_floor")
    book2 = SimpleNamespace(pos=pos2, p={"spot_trail": 12.0}, trades=[], capital=100000.0)
    f4 = _base_facts(ctx, eng, book2, pos2, memo)
    cmt_hold.extend_facts(f4, ctx, eng, book2, memo)
    assert f4["hold_lock_on"] is False and f4["hold_lock_q"] is None and f4["hold_lock_pct"] is None
    # bid below entry while ltp above: the honesty flag
    ctx5 = dict(ctx, by_key={pos["key"]: {"ltp": 114.5, "bid": 113.9, "ask": 115.0, "age": 0.4}})
    f5 = _base_facts(ctx5, eng, book, pos, memo)
    cmt_hold.extend_facts(f5, ctx5, eng, book, memo)
    assert f5["hold_bid_loss_ltp_gain"] is True
    assert not any(t.when(f5) for t in cmt_hold.TEMPLATES if t.tone == "confidence")


def test_extend_facts_survives_a_hollow_engine():
    """A minimal engine with nothing in it: every hold fact is set (None where unknown), nothing raises."""
    eng = SimpleNamespace(m=SimpleNamespace(ttq=np.zeros((1, 1)), ltp=np.zeros((1, 1)), k=0), flow=None, domino=None, greek={},
                          spot_hist=deque(), _day_hi=None, _day_lo=None)
    pos = {"id": 0, "key": "k", "rr": "CE", "strike": 25000, "dir": 1, "lots": 1, "qty": 65, "entry": 100.0, "t_in": 0.0}
    book = SimpleNamespace(pos=pos, p={}, trades=[], capital=100000.0)
    ctx = {"now_s": 10.0, "now_dt": datetime(2026, 10, 21, 10, 0, tzinfo=config.IST)}
    memo = SimpleNamespace(t_in=0.0, trade_id=0)
    f = {k: None for k in commentary.FACT_KEYS}
    f.update(dir=1, entry=100.0, qty=65)
    cmt_hold.extend_facts(f, ctx, eng, book, memo)
    for k in cmt_hold.FACTS:
        assert k in f, k
    assert f["hold_trail_pts"] == 12.0 and f["hold_lock_on"] is False and f["hold_n_with"] is None
    for t in cmt_hold.TEMPLATES:
        t.when(f)
        slots = dict(f); slots.update(t.slots(f))
        for ph in t.phrasings:
            ph.format(**slots)


def test_performance():
    eng, book, ctx, pos = _fake()
    memo = SimpleNamespace(t_in=pos["t_in"], trade_id=int(pos["t_in"]), eq_px_in=np.full(14, 99.9), N_in=23150.0)
    cmt_hold.extend_memo(memo, ctx, eng, pos)
    f = _base_facts(ctx, eng, book, pos, memo)
    cmt_hold.extend_facts(f, ctx, eng, book, memo)
    t0 = time.perf_counter()
    for i in range(1000):
        c = dict(ctx, now_s=ctx["now_s"] + i)
        cmt_hold.extend_facts(f, c, eng, book, memo)
    ms = (time.perf_counter() - t0) * 1000
    assert ms < 300, f"1,000 extend_facts calls took {ms:.0f} ms"
    t0 = time.perf_counter()
    for _ in range(200):
        for t in cmt_hold.TEMPLATES:
            t.when(f)
    us = (time.perf_counter() - t0) * 1e6 / 200
    assert us < 1000, f"69 predicates took {us:.0f} µs"
    return ms, us


def test_review_card():
    f = synthetic()
    t = {"t_in": 1792382221.0, "entry": 114.2, "exit": 146.25, "peak_pts": 45.8, "ret_pct": 28.06, "pnl_rs": 58331.0, "lots": 28, "qty": 1820,
         "reason": "TRAIL (spot 23118 vs stop 23118)", "hold_s": 683.0, "strike": 23150, "rr": "PE", "capital_after": 373331.0}
    card = cmt_hold.review_card(t, f)
    assert card["grade"] == "A" and len(card["lines"]) == 3 and all(isinstance(x, str) and x and not x.startswith("[") for x in card["lines"])
    assert "146.25" in card["lines"][0] or "₹58,331" in card["lines"][0]    # every summary phrasing carries the exit or the rupees
    assert "14" in card["lines"][2] and "9" in card["lines"][2]             # 13 + this one, 8 + 1 won
    # the winning-move-lost case (the 13:44 pattern)
    t2 = dict(t, exit=68.0, entry=70.75, peak_pts=5.0, ret_pct=-3.89, pnl_rs=-16623.75, hold_s=199.0, reason="TRAIL")
    f2 = dict(f, best_spot_fav=22.45, hold_vega_rs=-63501.0, iv_chg=-8.3, hold_delta_rs=47059.0)
    card2 = cmt_hold.review_card(t2, f2)
    assert card2["grade"] == "E" and ("vega" in card2["lines"][1].lower() or "vol" in card2["lines"][1].lower() or "IV" in card2["lines"][1])
    # a STOP, a TIME, a LOCK and a scratch: every path formats
    for reason, ret in (("STOP", -7.8), ("TIME 15:00", 2.0), ("LOCK (…)", 12.0), ("TRAIL", 1.0)):
        c = cmt_hold.review_card(dict(t, reason=reason, ret_pct=ret, pnl_rs=ret * 20, peak_pts=8.0), f)
        assert len(c["lines"]) == 3 and not any(x.startswith("[") for x in c["lines"]), (reason, c)
    # a review with no facts at all still produces three lines
    c = cmt_hold.review_card({"entry": 100.0, "exit": 90.0, "ret_pct": -10.0, "pnl_rs": -650.0, "qty": 65, "lots": 1, "reason": "STOP", "t_in": 5.0}, {})
    assert len(c["lines"]) == 3 and c["grade"] == "E"
    # no instruction words in the review either
    for c in (card, card2):
        for x in c["lines"]:
            assert not re.search(r"(^|[.:;!?—]\s*)(hold|exit|sell|buy)\b", x, re.I), x


def test_loads_through_the_core():
    """The core imports content modules by name; ours must load and merge without key collisions."""
    mods = commentary.load_content()
    names = [m.__name__ for m in mods]
    assert "apex.engine.cmt_hold" in names
    ts = commentary.all_templates(mods)
    assert len({t.key for t in ts}) == len(ts)
    assert any(t.key == "warn.vega_eating" for t in ts)
    c = commentary.Commentary("2026-10-19", paper_dir=None)
    assert c.templates and c.review_card is None
    # drive the selector with the synthetic facts: confidence lines appear with numbers, no crash, no '[key: ...]'
    f = synthetic()
    class _Ctx(dict):
        pass
    for s in range(30):
        ctx = _Ctx(now_s=1792385984.0 + s, now_dt=datetime(2026, 10, 19, 11, 28, 53 + s % 7))
        f["hold_s"] = 240.0 + s
        c._verdict(ctx, f, TRAIL)
        c._select(ctx, f)
    assert c.items and not any(it["text"].startswith("[") for it in c.items), list(c.items)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        r = fn()
        print(f"ok  {fn.__name__}" + (f"  ({r[0]:.0f} ms / 1,000 extend_facts; {r[1]:.0f} µs / 69 predicates)" if r else ""))
    print(f"{len(tests)} tests passed · {len(cmt_hold.TEMPLATES)} templates · {sum(len(t.phrasings) for t in cmt_hold.TEMPLATES)} phrasings · {len(cmt_hold.FACTS)} facts")
