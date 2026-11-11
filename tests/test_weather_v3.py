"""Photo v3 (8 Nov, owner: every docs/27 item is weather): the v3 base is filled and leak-free, the norms read only
earlier days, the direction and contract fields, every photo field belongs to a docs/27 item, and a real engine
publishes the views the photo reads."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_weather as tw  # noqa: E402
from apex.conductor import search  # noqa: E402
from apex.engine import paper, weather  # noqa: E402
from apex.engine.weather import Weather  # noqa: E402

V3_BASE = ("or45", "reversals60", "chop30", "chop60", "accel30", "fmv60", "fmv300", "fwd_lag60", "basis", "basis_chg60",
           "basis_chg300", "vwap_side_min", "skew_chg300", "term_chg300", "pcr", "pcr_chg30", "atm_iv_now", "atm_iv_med",
           "atm_iv_chg60", "atm_iv_chg300", "fn60", "fn300", "ce_vol300", "pe_vol300", "vol_ratio_cp", "prem_ratio_cp",
           "range_now", "fut_vol60", "hw_vol60")
# fields the photo writes only with the engine's market object / histories present (covered by the rig test too)
V3_MARKET = ("fut_spread", "rest_with_rs", "rest_opp_rs", "round_dist", "rest_round_rs", "fut_opp_q", "fut_opp_o",
             "fut_pulled", "fut_imb_o", "fut_imb_q", "fut_imb_t_chg30", "fut_lead", "agg_with_rs", "agg_net",
             "fut_vol_surge", "fut_ttq60", "absorb60", "hw_book_imb", "hw_book_imb_t", "hw_book_chg30", "hw_vol_surge",
             "oi_own_chg5", "oi_own_chg15", "oi_own_chg30", "oi_other_chg5", "oi_other_chg15", "oi_other_chg30",
             "oi_net_help5", "oi_net_help15", "oi_net_help30", "oi_own_chg_open", "opt_iv_chg1", "opt_iv_chg5",
             "prem_chg1_pct", "opt_vol1", "opt_vol_chg1", "prem_resp1", "opt_book_imb", "opt_opp_q", "opt_opp_o",
             "opt_imb_chg30", "opt_lead", "opt_run", "hk_buy", "hk_sell", "hk_ratio", "sl_room_up_pct", "sl_room_dn_pct",
             "sl_n_res", "sl_n_sup", "sl_next_res")


def test_v3_base_is_filled_and_leak_free():
    T = tw.T_OPEN + 2 * 3600
    a = tw._fill(tw._W(), tw.T_OPEN, T)
    b = tw._fill(tw._W(), tw.T_OPEN, T + 300)
    ba, bb = a.base(T), b.base(T)
    assert ba == bb                                      # nothing stamped after T is read, v3 series included
    for k in V3_BASE:
        assert ba.get(k) is not None, k
    assert ba["norm_days"] is None and ba["range_vs_norm"] is None and ba["fut_vol_vs_norm"] is None   # no norms: None
    assert ba["vwap_side_min"] > 0 and ba["ce_vol300"] == 300 * 1000.0 and ba["vol_ratio_cp"] == 1.25
    assert ba["fmv60"] == ba["mv60"]                     # the forward here is spot + 12: same moves


def test_norms_come_from_earlier_days_only(tmp_path):
    days = ["2026-10-19", "2026-10-21", "2026-10-22", "2026-11-06"]
    data = {"version": 1, "minutes": 375,
            "days": {d: {"range": [10.0 * (i + 1)] * 375, "rv5": [20.0] * 375, "fut_vol": [100.0] * 375,
                         "hw_vol": [1000.0] * 375} for i, d in enumerate(days)}}
    p = tmp_path / "clock_norms.json"
    p.write_text(json.dumps(data))
    n = weather.load_norms("2026-11-06", str(p))
    assert n["n_days"] == 3 and n["range"][0] == 20.0    # the median of 10, 20, 30: the day's own 40 is never read
    assert weather.load_norms("2026-10-22", str(p)) is None   # two earlier days are not enough
    T = tw.T_OPEN + 2 * 3600
    b = tw._fill(Weather("2026-11-06", norms=n), tw.T_OPEN, T).base(T)
    assert b["norm_days"] == 3 and b["range_vs_norm"] == round(b["range_now"] / 20.0, 3)
    assert b["fut_vol_vs_norm"] == round(b["fut_vol60"] / 100.0, 3)


def _rich_ctx(T, w, rr="CE"):
    ctx, o = tw._ctx(T, w, rr)
    o = dict(o, iv=14.5, gamma=0.001)
    ctx.update(fwd=24062.0,
               quant={"kv": 0.02, "kvt": 1.5, "sig": 0.3, "jz": 0.4, "cusum": 1, "kyle": 1e-6,
                      "smile": {"K": [24500], "res": [0.3]},
                      "regime": {"state": 1, "post": [0.1, 0.7, 0.2], "run_min": 4, "left_min": 6.5, "drift": [-1.0, 2.0, 0.5]},
                      "flow_by_id": {"3": {"buy": 1.2, "sell": 0.4, "ratio": 3.0}}},
               gex={"ok": True, "regime": "DAMPEN", "balance": 0.2, "flip": 24000.0, "call_wall": 24300.0,
                    "put_wall": 23800.0, "max_pain": 24100.0},
               force={"verdict": "TESTING", "dir": 1, "level": 24080.0, "rho": 0.8, "pi": 0.1}, bank={"z": 1.1},
               episode={"id": 7, "dir": 1, "type": "BASKET-LED", "first": "HDFCBANK", "first_t": T - 20,
                        "fut_cross_t": T - 5, "n_cross": 3, "max_S": 0.6, "age": 30.0},
               domino={"S_up": 0.7, "S_dn": 0.1, "z": 2.1, "sigma15": 4.0},
               advisors_dir={1: {"room": {"veto": False, "why": ""}, "bank": {"veto": True, "why": ""}}, -1: {}},
               fires={"prev": {"CE": 2}, "cur": {"CE": 1, "PE": 1}},
               feed={"reconnects": 0, "feed_state": 6, "chain_age": 40.0, "depth_age_fut": 0.2, "n_hero_stale": 0,
                     "n_hero_wide": 1, "gap_s_today": 0.0},
               edge={"wall_up": 120.0, "wall_dn": 60.0, "basis_dev": 1.5, "fut_ofi60": 0.3, "pcr": 0.9, "iv_rv": 1.2})
    return ctx, o


def test_photo_v3_direction_contract_and_none_without_the_market_object():
    T = tw.T_OPEN + 2 * 3600
    w = tw._fill(tw._W(), tw.T_OPEN, T)
    ctx, o = _rich_ctx(T, w)
    bk = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    bk.ctl["trig_str"], bk.ctl["trig_unit"] = 12.0, "pt impulse"
    ce = weather.photo(ctx, 1, o, bk, "SPOT brk v=+20")
    pe = weather.photo(ctx, -1, dict(o, rr="PE", delta=-0.55), bk, "SPOT brk")
    assert ce["v"] == 5 and "v3_error" not in ce and "v2_error" not in ce
    assert ce["gex_flip_ahead"] == -62.0 and pe["gex_flip_ahead"] == 62.0
    assert ce["gex_wall_ahead"] == 238.0 and pe["gex_wall_ahead"] == 262.0 and ce["max_pain_dist"] == 50.0
    assert ce["lead_s"] == 15.0 and ce["ep_with"] is True and pe["ep_with"] is False and ce["sync_dir"] == 0.7
    assert ce["adv_bank"] is True and ce["adv_room"] is False and ce["adv_vetoes"] == 1 and pe["adv_vetoes"] is None
    assert ce["agree_same"] == 3 and ce["agree_other"] == 1 and pe["agree_same"] == 1
    assert ce["trigger"] == "SPOT" and ce["trig_str"] == 12.0
    assert ce["kv"] == 0.02 and pe["kv"] == -0.02 and ce["hmm_drift"] == 2.0 and pe["hmm_drift"] == -2.0
    assert ce["svi_res"] == 0.3 and ce["hk_ratio"] == 3.0 and ce["force_with"] is True and pe["force_with"] is False
    assert ce["vanna"] is not None and ce["vega"] is not None and ce["zomma"] is not None
    assert 0 <= ce["po_up5"] <= 1 and 0 <= ce["po_ever"] <= 1 and ce["po_a"] > 0   # a far strike: near-zero odds are right
    assert ce["e_fut_ofi60"] == 0.3 and pe["e_fut_ofi60"] == -0.3 and ce["e_pcr"] == 0.9 and ce["e_iv_rv"] == 1.2
    assert ce["vol_ratio_with"] == 1.25 and pe["vol_ratio_with"] == 0.8
    assert ce["reversals60"] is not None and ce["chop30"] is not None and ce["or45_pos"] is not None
    for k in ("rest_with_rs", "absorb60", "hw_book_imb", "oi_own_chg5", "opt_book_imb", "sl_n_res"):
        assert k not in ce or ce[k] is None            # no market object / histories: None, never 0
    json.dumps(ce, allow_nan=False)


def test_every_photo_field_belongs_to_a_docs27_item():
    T = tw.T_OPEN + 2 * 3600
    w = tw._fill(tw._W(), tw.T_OPEN, T)
    ctx, o = _rich_ctx(T, w)
    bk = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    bk.trades = [{"t_out": T - 120, "pnl_rs": 50.0, "ret_pct": 3.0, "reason": "TRAIL", "rr": "CE"}]
    keys = set(weather.photo(ctx, 1, o, bk, "t")) | set(V3_MARKET)
    missing = sorted(k for k in keys if k not in search.SKIP and search.item_of(k)[0] is None)
    assert not missing, missing
    assert len(search.ITEMS) == 114 and search.item_of("adv_room") == (61, "Advisors")
    assert len(keys - search.SKIP) >= 200


def test_the_real_engine_publishes_the_v3_views_and_the_photo_is_whole():
    import test_wp2
    rig = test_wp2.Rig("weather3", "2026-10-21")
    try:
        rig.warm()
        rig.step(25215.0, 50)
        ctx = rig.eng.ctx
        for k in ("_m", "_flow", "oi_hist", "quant", "force", "gex", "feed", "advisors_dir", "fires", "chain_view",
                  "hero_ids", "fut_id"):
            assert k in ctx, k
        assert ctx["feed"]["feed_state"] == 5 and isinstance(ctx["advisors_dir"].get(1), dict)
        assert len(ctx["advisors_dir"][1]) >= 10                       # every advisor, for the up direction
        o = ctx["by_key"][f"NIFTY|OPT|{test_wp2.EXP}|25200|CE"]
        p = weather.photo(ctx, 1, o, rig.eng.books[rig.eng.champion], "test entry")
        assert "v3_error" not in p and "v2_error" not in p
        assert p["fut_spread"] == 1.0 and p["rest_with_rs"] is not None and p["fut_opp_q"] in ("—", "REFILLING", "HOLDING",
                                                                                               "DRAIN-SLOW", "DRAIN-FAST", "PULLED")
        for k in ("fut_vol60", "agree_same", "vwap_side_min", "fut_imb_q", "opt_book_imb", "reconnects"):
            assert k in p, k
        missing = sorted(k for k in p if k not in search.SKIP and search.item_of(k)[0] is None)
        assert not missing, missing
        json.dumps(p, allow_nan=False)
    finally:
        rig.close()
