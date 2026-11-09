"""Photo v4 (9 Nov, owner: "add at least 30-40 more different kind of items"): items 69-104. The base is leak-free
and filled, the direction and contract fields are right, every field belongs to an item, the books' block reads only
what is closed or open at the trigger, and a real engine writes the whole photograph."""
import json
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_weather as tw  # noqa: E402
import test_weather_v3 as t3  # noqa: E402
from apex.conductor import search  # noqa: E402
from apex.engine import paper, weather, weather4  # noqa: E402

V4_BASE = ("rng", "bar5", "bar1", "atr1_15", "bar1_range_vs15", "run1", "up_share30", "hh5_up", "rsi1", "rsi5", "z20",
           "ma5", "ma20", "ma60", "ma20_prev", "first", "open_side_min", "ac1_30", "vr5_60", "max_up1_15", "n_dn15",
           "nifty300", "bn300", "bn_corr30", "vix_day_pos", "hw_disp300", "hw_top3_share", "hw_n_up", "lead1_60",
           "lead_up3", "hw_at_hi30", "fut_ttq_accel", "fut_vol300", "ce_vol60", "band_vol_accel", "upvol60", "upvol300",
           "vwap_z", "vwap_cross_n", "vwap_stretch_share", "atm_iv_day_pos", "iv_spot_corr15", "strad_now", "strad_open")
# written only with the engine's market object / per-contract histories / other books (the rig test covers them)
V4_MARKET = ("opt_ask_rs", "opt_ask5_rs", "opt_bid5_rs", "opt_depth_ratio", "own_oi", "own_vol_oi", "own_oi_share",
             "own_vs_opp_oi", "rr100", "fly100", "fut_oi_chg5", "fut_oi_chg30", "fut_buildup", "fut_buildup_with",
             "prem_chg5_pct", "prem_chg15_pct", "prem_pos15", "prem_off_hi15_pct", "prem_rv5", "opp_prem_chg1_pct",
             "opp_prem_chg5_pct", "opp_iv_chg1", "pair_chg1", "pd_range", "pd_close_pos", "inside_pd", "range_vs_pd",
             "pivot_dist", "piv_next_ahead", "held_same", "held_other", "held_same_winning", "fam_n", "fam_busy",
             "fam_free", "all_n_today", "all_win_today", "all_last_same_s", "all_last_same_won", "all_last5_same_win",
             "since_last_loss_s", "last_ret_pct", "last_peak_pts", "last_hold_s", "same_key_as_last",
             "prem_vs_last_exit_pct", "prem_vs_last_entry_pct", "best_today", "worst_today", "ret_last3",
             "win_share_today")


def _ctx4(T, w, rr="CE"):
    ctx, o = t3._rich_ctx(T, w, rr)
    ctx["_wx"] = w
    ctx["day"].update(pdh=24120.0, pdl=23920.0, pdc=24010.0)
    return ctx, o


def test_v4_base_is_filled_and_leak_free():
    T = tw.T_OPEN + 2 * 3600
    a = tw._fill(tw._W(), tw.T_OPEN, T)
    b = tw._fill(tw._W(), tw.T_OPEN, T + 300)
    ba, bb = weather4.base4(a, T), weather4.base4(b, T)
    assert "errors" not in ba, ba.get("errors")
    assert json.dumps(ba, sort_keys=True, default=float) == json.dumps(bb, sort_keys=True, default=float)
    for k in V4_BASE:
        assert ba.get(k) is not None, k
    assert ba["strad_open"] == 205.0 and 0 <= ba["upvol60"] <= 1 and 0 <= ba["upvol300"] <= 1
    assert abs(ba["fut_ttq_accel"] - 1.0) < 1e-9 and ba["fut_vol300"] == 300 * 5000.0
    assert 0 <= ba["rsi1"] <= 100 and -60 <= ba["run1"] <= 60 and abs(ba["bn_corr30"]) <= 1.0 + 1e-9
    assert weather4.base4(a, T) is ba                    # once per market second
    early = weather4.base4(tw._fill(tw._W(), tw.T_OPEN, tw.T_OPEN + 120), tw.T_OPEN + 120)
    assert "errors" not in early and early.get("ma60") is None and early.get("rsi5") is None   # no data: None, not 0


def test_photo_v4_direction_contract_and_items():
    T = tw.T_OPEN + 2 * 3600
    w = tw._fill(tw._W(), tw.T_OPEN, T)
    ctx, o = _ctx4(T, w)
    bk = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    ce = weather.photo(ctx, 1, o, bk, "SPOT brk")
    pe = weather.photo(ctx, -1, dict(o, rr="PE", delta=-0.55), bk, "SPOT brk")
    assert ce["v"] == 4 and "v4_error" not in ce and "v4_error" not in pe, (ce.get("v4_error"), pe.get("v4_error"))
    # 69-71: yesterday, pivots, the strike grid (spot 24050, yesterday 23920-24120, close 24010)
    assert ce["pd_range"] == 200.0 and ce["pd_close_pos"] == 0.45 and pe["pd_close_pos"] == 0.55 and ce["inside_pd"] is True
    P = (24120.0 + 23920.0 + 24010.0) / 3
    assert ce["pivot_dist"] == round(24050.0 - P, 2) and pe["pivot_dist"] == -ce["pivot_dist"]
    assert ce["piv_next_ahead"] == round(2 * P - 23920.0 - 24050.0, 2)          # R1 is the next level above
    assert ce["strike50_ahead"] == 50.0 and pe["strike50_ahead"] == 50.0 and ce["strike_pin"] == 0.0
    # signed fields flip, positions mirror
    for k in ("bar5_body", "run1_with", "z20", "ma20_dist", "day_move", "vwap_z", "bn_minus_nifty60", "lead1_move60"):
        assert ce[k] is not None and ce[k] == -pe[k], k
    for k in ("pos5", "pos15", "pos60"):
        assert abs(ce[k] + pe[k] - 1.0) < 1e-3, k
    assert abs(ce["rsi14_1m"] + pe["rsi14_1m"] - 100.0) < 0.11 and ce["ma_stack"] + pe["ma_stack"] == 3
    assert abs(ce["with_vol_share300"] + pe["with_vol_share300"] - 1.0) < 2e-3
    assert abs(ce["cp_vol_tilt60"] - 1000 / 1800.0) < 1e-3 and abs(pe["cp_vol_tilt60"] - 800 / 1800.0) < 1e-3
    assert ce["cp_vol_tilt_chg"] == 0.0 and ce["band_vol_accel"] == 1.0
    # 86-88: a 24500 call with the forward at 24062 is 438 out of the money; the put is 438 in
    assert ce["moneyness_pts"] == -438.0 and ce["intrinsic"] == 0.0 and ce["extrinsic_pct"] == 100.0
    assert pe["moneyness_pts"] == 438.0 and pe["intrinsic"] == 438.0
    assert ce["gearing"] == round(0.55 * 24062.0 / 100.0, 2) and ce["spread_be_pts"] == round(1.0 / 0.55, 2)
    assert ce["gamma_theta"] == round(0.001 / 0.11, 5) and ce["strad_now"] == 205.0 and ce["strad_vs_open_pct"] == 0.0
    assert ce["range_vs_strad"] == round(ctx["weather"]["range_now"] / 205.0, 3)
    assert ce["opt_iv_vs_atm"] == round(14.5 - ctx["weather"]["atm_iv_now"], 2)
    # 103-104: a book with no trades yet
    assert ce["n_same_side_today"] == 0 and ce["n_losses_today"] == 0 and ce["dd_today"] == 0.0
    for k in ("opt_ask_rs", "own_oi", "fut_oi_chg5", "prem_pos15", "held_same"):
        assert k not in ce or ce[k] is None            # no market object / histories / books: None, never 0
    json.dumps(ce, allow_nan=False), json.dumps(pe, allow_nan=False)
    keys = (set(ce) | set(V4_MARKET)) - search.SKIP
    missing = sorted(k for k in keys if search.item_of(k)[0] is None)
    assert not missing, missing
    v4 = {f for n, (_l, fs) in search.ITEMS.items() if n >= 69 for f in fs}
    unbuilt = sorted(v4 - set(ce) - set(V4_MARKET))
    assert not unbuilt, unbuilt                          # every field in the item table is one the photo writes
    assert len(search.ITEMS) == 104 == weather.N_ITEMS == weather4.N_ITEMS and len(v4) >= 130
    assert weather.static_check() == []


def test_the_books_block_the_trigger_log_and_the_contract_histories():
    T = tw.T_OPEN + 2 * 3600
    w = tw._fill(tw._W(), tw.T_OPEN, T)
    ctx, o = _ctx4(T, w)
    key, okey = o["key"], o["key"][:-2] + "PE"
    other = dict(o, key=okey, id=4, rr="PE", ltp=60.0, bid=59.5, ask=60.5, iv=15.0)
    ctx["by_key"][okey] = other
    ctx["ohist"] = {3: deque((T - 960 + k, 14.0, 1.0, 80.0 + k * 20.0 / 960, 0.5, 0.001, -0.1, 10.0 * k) for k in range(961)),
                    4: deque((T - 960 + k, 15.5, 1.0, 70.0 - k * 10.0 / 960, -0.5, 0.001, -0.1, 10.0 * k) for k in range(961))}
    me = paper.Book("c20_9y", {}, "2026-11-06")
    me.trades = [{"t_in": T - 900, "t_out": T - 600, "pnl_rs": 500.0, "ret_pct": 4.0, "rr": "CE", "key": key, "entry": 90.0,
                  "exit": 94.0, "peak_pts": 6.0},
                 {"t_in": T - 500, "t_out": T - 200, "pnl_rs": -900.0, "ret_pct": -6.0, "rr": "CE", "key": key, "entry": 96.0,
                  "exit": 90.0, "peak_pts": 1.0}]
    sib_busy, sib_free, far = (paper.Book(n, {}, "2026-11-06") for n in ("c20_9s", "c20_9t", "spot_pb45"))
    sib_busy.pos = {"key": key, "entry": 95.0}                       # holding our side, in profit at 100
    far.pos = {"key": okey, "entry": 50.0}                           # another family, the other side
    far.trades = [{"t_out": T - 50, "pnl_rs": 100.0, "rr": "CE", "key": key},
                  {"t_out": T + 50, "pnl_rs": None, "rr": "CE", "key": key}]     # not closed: never counted
    ctx["_books"] = {"c20_9y": me, "c20_9s": sib_busy, "c20_9t": sib_free, "spot_pb45": far}
    p = weather.photo(ctx, 1, o, me, "t")
    assert "v4_error" not in p, p.get("v4_error")
    assert (p["held_same"], p["held_other"], p["held_same_winning"]) == (1, 1, 1.0)
    assert (p["fam_n"], p["fam_busy"], p["fam_free"]) == (2, 1, 1)
    assert p["all_n_today"] == 1 and p["all_win_today"] == 1.0 and p["all_last_same_s"] == 50.0 and p["all_last_same_won"] is True
    assert p["n_same_side_today"] == 2 and p["n_losses_today"] == 1 and p["since_last_loss_s"] == 200.0
    assert p["last_ret_pct"] == -6.0 and p["last_hold_s"] == 300.0 and p["same_key_as_last"] is True
    assert p["prem_vs_last_exit_pct"] == round(100 * (100.5 / 90.0 - 1), 2)
    assert p["best_today"] == 4.0 and p["worst_today"] == -6.0 and p["dd_today"] == -6.0 and p["win_share_today"] == 0.5
    # the premium's own path and the opposite leg (own premium rising 80 -> 100, the put falling 70 -> 60)
    assert p["prem_chg5_pct"] > 0 and p["prem_chg15_pct"] > p["prem_chg5_pct"] and p["prem_pos15"] == 1.0
    assert p["prem_off_hi15_pct"] == 0.0 and p["opp_prem_chg1_pct"] < 0 and p["opp_iv_chg1"] == -0.5
    assert p["pair_chg1"] is not None and p["prem_rv5"] is not None
    # the trigger log: only EARLIER seconds are counted, and this trigger is then on the log for the next
    assert p["fires5_same"] == 0 and p["fires5_other"] == 0 and p["last_fire_other_s"] is None
    q = weather.photo(dict(ctx, now_s=T + 30), -1, dict(o, rr="PE", delta=-0.55), me, "t")
    assert q["fires5_other"] == 1 and q["fires5_same"] == 0 and q["last_fire_other_s"] == 30
    r = weather.photo(dict(ctx, now_s=T + 60), 1, o, me, "t")
    assert r["fires5_same"] == 1 and r["fires5_other"] == 1 and r["flip_n15"] == 1
    json.dumps(p, allow_nan=False)


def test_a_broken_block_is_named_and_never_stops_the_photo(monkeypatch):
    T = tw.T_OPEN + 2 * 3600
    w = tw._fill(tw._W(), tw.T_OPEN, T)
    ctx, o = _ctx4(T, w)

    def boom(*a, **k):
        raise ZeroDivisionError

    boom.__name__ = "_p_books"
    monkeypatch.setattr(weather4, "_p_books", boom)       # photo_v4 looks its blocks up by name at call time
    p = weather.photo(ctx, 1, o, None, "t")
    assert p.get("v4_error") == "_p_books" and p["pos15"] is not None and p["er60"] is not None
    assert "dd_today" not in p or p["dd_today"] is None   # no book given: the own-day block writes nothing
    probs, _w = weather.check_photo(p)
    assert any("v4_error" in x for x in probs)


def test_the_real_engine_writes_the_whole_v4_photograph():
    import test_wp2
    rig = test_wp2.Rig("weather4", "2026-10-21")
    try:
        rig.warm()
        rig.step(25215.0, 50)
        ctx = rig.eng.ctx
        assert ctx["_wx"] is rig.eng.weather and ctx["_books"] is rig.eng.books
        o = ctx["by_key"][f"NIFTY|OPT|{test_wp2.EXP}|25200|CE"]
        p = weather.photo(ctx, 1, o, rig.eng.books[rig.eng.champion], "test entry")
        assert "v4_error" not in p and "v3_error" not in p and "v2_error" not in p, p.get("v4_error")
        for k in ("held_same", "fam_n", "all_n_today", "fires5_same", "moneyness_pts", "gearing", "strike50_ahead",
                  "dd_today", "opt_ask5_rs"):
            assert k in p, k
        missing = sorted(k for k in p if k not in search.SKIP and search.item_of(k)[0] is None)
        assert not missing, missing
        json.dumps(p, allow_nan=False)
        print("rig photo fields:", len([k for k in p if k not in weather.SKIP_FIELDS]))
    finally:
        rig.close()
