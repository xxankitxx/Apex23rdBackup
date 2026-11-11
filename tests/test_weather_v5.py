"""Photo v5 (10 Nov, docs/38 section 6): the first instrumentation batch, items 105-110, 120-122, 128. Every field is
built and mapped, missing is None with a stated reason, the machine's own timing is recorded but never searched, a
retried request is known to be a retry, and the fill evidence lands on the trade (not in the entry photograph)."""
import json
import os
import sys
from collections import deque
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_weather as tw  # noqa: E402
import test_weather_v3 as t3  # noqa: E402
import test_gen2 as tg  # noqa: E402
from apex import config  # noqa: E402
from apex.conductor import search  # noqa: E402
from apex.engine import gen2, paper, weather, weather5  # noqa: E402

V5 = tuple(f for _l, fs in weather5.ITEMS5.values() for f in fs)


def _bare(rr="CE"):
    T = tw.T_OPEN + 2 * 3600
    w = tw._fill(tw._W(), tw.T_OPEN, T)
    ctx, o = t3._rich_ctx(T, w, rr)
    ctx["_wx"] = w
    return T, w, ctx, o


def test_every_v5_field_is_written_mapped_and_none_when_unmeasured():
    T, w, ctx, o = _bare()
    bk = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    p = weather.photo(ctx, 1, o, bk, "t")
    assert p["v"] == 5 and "v5_error" not in p, p.get("v5_error")
    for k in V5:
        assert k in p, k
        assert search.item_of(k)[0] in weather5.NEW_ITEMS
    json.dumps(p, allow_nan=False)
    # nothing behind the photograph: unmeasured is None (never 0) and the reason is written, by item
    for k in ("eng_p50_ms", "sync_spot_age_s", "hw_fresh_w", "sign_out_share60", "resp_beta60", "opt_path_s", "atm_switch_s"):
        assert p[k] is None, k
    m = p["v5_missing"]
    assert isinstance(m, str) and all(f"{n}: " in m for n in (105, 107, 108, 109, 110, 121))
    assert weather.static_check() == [] and not [x for x in weather.check_photo(p)[0] if "v5" in x]
    assert len(search.ITEMS) == 114 and sorted(search.ITEMS) == list(weather.ITEM_IDS)
    assert set(weather5.TELEMETRY) <= set(V5)


def test_the_machines_own_timing_is_recorded_but_never_searched():
    T, w, ctx, o = _bare()
    bk = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    ctx["step_gap"] = 0.4
    ctx["_eng"] = {"perf": {"p50": 20.0, "p95": 90.0, "max": 310.0, "over300": 1}, "feed_age": 0.2}
    rows = []
    for k in range(4):
        p = weather.photo(ctx, 1, o, bk, "t")
        p["lin_rule_hash"] = f"{k:08x}"
        rows.append({"weather": p})
    assert rows[0]["weather"]["eng_p95_ms"] == 90.0 and rows[0]["weather"]["eng_step_gap_s"] == 0.4
    assert "105: " not in (rows[0]["weather"].get("v5_missing") or "")
    f = search.features(rows)
    names = {k.split("=")[0] for k in f}
    assert not (names & set(weather5.TELEMETRY)) and "v5_missing" not in names and "v5_error" not in names
    assert "eng_step_gap_s" in names                       # market time: the same live and in a replay, so searched


def test_synchronisation_and_coverage_from_the_receive_times():
    T, w, ctx, o = _bare()
    n = 12
    snap = {"recv_ns": np.zeros(n, dtype=np.int64)}
    now = int(T * 1e9)
    snap["recv_ns"][0] = now - int(0.2e9)                  # spot
    snap["recv_ns"][1] = now - int(1.5e9)                  # future
    snap["recv_ns"][3] = now - int(4.0e9)                  # the contract; the other leg (id 4) has never printed
    for i, age in zip((5, 6, 7, 8), (1.0, 2.0, 30.0, 0.5)):
        snap["recv_ns"][i] = now - int(age * 1e9)          # four stocks; the third is stale
    snap["recv_ns"][9] = now - int(1.0e9)                  # one stock future fresh, the others never seen
    ctx["_m"] = SimpleNamespace(snap=snap)
    ctx["fut_id"] = 1
    ctx["_eng"] = {"spot_id": 0, "atm": 24500.0}
    ctx["by_key"][o["key"][:-2] + "PE"] = dict(o, key=o["key"][:-2] + "PE", id=4, rr="PE")
    ctx["eq_fut"] = (np.array([9, 10, -1, 11]), np.array([40.0, 30.0, 20.0, 10.0]), np.array([5, 6, 7, 8]))
    p = weather.photo(ctx, 1, o, None, "t")
    assert "v5_error" not in p, p.get("v5_error")
    assert (p["sync_spot_age_s"], p["sync_fut_age_s"], p["sync_opt_age_s"], p["sync_opp_age_s"]) == (0.2, 1.5, 4.0, None)
    assert (p["sync_n"], p["sync_oldest_s"], p["sync_newest_s"], p["sync_spread_s"]) == (3, 4.0, 0.2, 3.8)
    assert p["hw_fresh_w"] == 0.8 and p["hwf_fresh_w"] == 0.4          # 40+30+10 of 100; one future of weight 40
    assert p["hw_stale_top5_n"] == 1 and p["hw_stale_max_s"] == 30.0
    assert p["opt_is_atm"] is True


def test_sign_uncertainty_and_response_reliability_come_from_gen2_and_no_signal_reads_them():
    tp = tg.Tape(hw=[100.0, 100.0, 100.0, 100.0])
    tp.warm()
    g = tp.g
    sv = g.sign_view()
    assert abs(sv["sign_out_share60"] - 1.0) < 1e-9 and sv["sign_none_share60"] == 0.0     # every print at the quote
    for _ in range(120):
        tp.step(dq=50.0, sign=0, move=0.0)                 # prints at the mid: inside the spread, no tick either way
    sv = g.sign_view()
    assert sv["sign_none_share60"] > 0.5 and sv["sign_none_share300"] < sv["sign_none_share60"]
    T, w, ctx, o = _bare()
    ctx["gen2"] = g
    p = weather.photo(ctx, 1, o, None, "t")
    assert "v5_error" not in p, p.get("v5_error")
    assert p["sign_none_share60"] == round(sv["sign_none_share60"], 4)
    assert p["resp_beta10"] is not None and p["resp_fit60_n"] >= 300 and p["n02_cond"] >= 1.0 and p["n02_se_fast"] >= 0
    assert p["hw_cover60_w"] == 1.0 and p["hw_cover300_w"] == 1.0 and p["grp_cover_min300_w"] == 1.0
    import inspect
    src = inspect.getsource(gen2.Gen2)
    body = src.replace(inspect.getsource(gen2.Gen2.sign_view), "")
    assert body.count("sgn_v") == 2                        # created once, updated once; read only by sign_view


def test_a_retried_request_is_known_and_the_fill_clears_it(monkeypatch):
    monkeypatch.setattr(config, "FILL_NEXT_PRINT", True)
    T = tw.T_OPEN + 2 * 3600
    w = tw._fill(tw._W(), tw.T_OPEN, T + 400)
    b = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    ctx, o = tw._ctx(T, w)
    paper.request_entry(b, ctx, o, "t")
    first = b.ctl["pending_entry"]["weather_trig"]
    assert first["req_first"] is True and first["req_retry_n"] == 0 and first["req_lapsed_n"] == 0
    late, o2 = tw._ctx(T + config.ENTRY_FILL_MAX_S + 1, w)
    late["by_key"][o["key"]]["age"] = 99.0                 # no print since the request: it lapses
    late["step_gap"] = 3.0
    pos, why = paper.try_fill_entry(b, late)
    assert pos is None and "lapsed" in why and b.ctl["req_log"] == [[T, 1]]
    t2 = T + config.ENTRY_FILL_MAX_S + 2
    ctx2, o2 = tw._ctx(t2, w)
    paper.request_entry(b, ctx2, o2, "t")
    again = b.ctl["pending_entry"]["weather_trig"]
    assert again["req_first"] is False and again["req_retry_n"] == 1 and again["req_lapsed_n"] == 1
    assert again["req_cluster_s"] == round(t2 - T, 1)
    other = weather.photo(ctx2, -1, dict(o2, rr="PE"), b, "t")
    assert other["req_first"] is True and other["req_lapsed_n"] == 1      # the other side is a new opportunity
    ctx3, o3 = tw._ctx(t2 + 1, w)
    ctx3["fut"] = ctx2["fut"] + 2.5
    pos, _ = paper.try_fill_entry(b, ctx3)
    assert pos is not None and "req_log" not in b.ctl
    ev = pos["fill_ev"]
    assert ev["gap_s"] == 1.0 and ev["post_request"] is True and ev["fut_move_pts"] == 2.5 and ev["print_age_s"] == 0.0
    assert "fill_ev" not in pos["weather_trig"] and not any(k.startswith("fill_") for k in pos["weather_trig"])
    much_later, o4 = tw._ctx(t2 + 300, w)
    assert weather.photo(much_later, 1, o4, b, "t")["req_first"] is True


def test_contract_path_the_atm_log_and_the_lineage():
    T, w, ctx, o = _bare()
    for t, a in ((T - 3000, 24450.0), (T - 2000, 24450.0), (T - 600, 24500.0), (T - 100, 24550.0), (T - 50, 24500.0)):
        weather5.tick(w, t, a)
    assert [x[2] for x in w.atm_log] == [True, False, False, False]
    hist = deque((T - 400 + k, 14.0, 1.0, 100.0, 0.5, 0.001, -0.1, 10.0 * k) for k in range(401) if not 300 <= k < 340)
    ctx["ohist"] = {3: hist}
    ctx["_eng"] = {"atm": 24500.0, "pool_cutoff": "2026-11-09"}
    bk = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    p = weather.photo(ctx, 1, o, bk, "t")
    assert "v5_error" not in p, p.get("v5_error")
    assert p["opt_path_s"] == 60.0 and p["opt_path_gap_n300"] == 1 and p["opt_path_gap_max_s"] == 41.0
    assert p["atm_switch_s"] == 50.0 and p["atm_switch_n15"] == 3 and p["opt_is_atm"] is True
    assert p["trig_quote_ok"] is True and p["trig_ltp_vs_mid_pts"] == 0.0 and p["trig_print_age_s"] == 0.0
    assert p["lin_schema"] == f"w5.g{gen2.VERSION}" and len(p["lin_rule_hash"]) == 8 and p["lin_art_cutoff"] == "2026-11-09"
    assert p["lin_rule_hash"] == weather5.rule_hash(bk)
    bk.p = dict(bk.p, some_threshold=1.23)
    assert weather5.rule_hash(bk) != p["lin_rule_hash"]     # a changed rule is a different rule
    assert "128: " in p["v5_missing"]


def test_a_broken_block_never_stops_the_photograph(monkeypatch):
    T, w, ctx, o = _bare()
    monkeypatch.setattr(weather5, "_snap", lambda ctx: 1 / 0)
    p = weather.photo(ctx, 1, o, None, "t")
    assert p["v5_error"] == "_p_sync,_p_cover" and p["trig_quote_ok"] is True and p["sync_n"] is None
    assert any("v5_error" in x for x in weather.check_photo(p)[0])


# ── items 123-126: the continuation photograph (on the trade, never in the entry photograph) ─────────────────────────
HOLD = tuple(f for _l, fs in weather5.HOLD_ITEMS.values() for f in fs)


def test_the_continuation_photograph_lives_on_the_trade_and_never_in_the_entry_photograph(monkeypatch):
    monkeypatch.setattr(config, "FILL_NEXT_PRINT", True)
    T = tw.T_OPEN + 2 * 3600
    w = tw._fill(tw._W(), tw.T_OPEN, T + 4000)
    b = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    ctx, o = tw._ctx(T, w)
    paper.request_entry(b, ctx, o, "t")
    c1, _ = tw._ctx(T + 1, w)
    pos, _ = paper.try_fill_entry(b, c1)
    assert pos is not None and "weather_hold" not in pos
    b.pos = pos
    key, e, f0 = pos["key"], pos["entry"], pos["fut_in_ltp"]

    def step(dt, dpx, dfut):
        c, _o = tw._ctx(pos["t_in"] + dt, w)
        c["by_key"][key]["ltp"] = e + dpx
        c["fut"] = f0 + dfut
        weather5.hold_tick(pos, c, c["by_key"][key])
        return c

    pos["peak_pts"] = 0.0
    for dt, dpx in ((10, 1.0), (30, 4.0), (59, 2.0)):
        pos["peak_pts"] = max(pos["peak_pts"], dpx)
        step(dt, dpx, dpx * 2)
    assert "weather_hold" not in pos                       # no age mark reached yet
    step(61, 1.0, 2.0)
    h = pos["weather_hold"][0]
    assert h["mark"] == 60 and set(HOLD) <= set(h) and "hold_error" not in h, h
    assert (h["gain_pts"], h["peak_pts"], h["time_to_peak_s"], h["peak_age_s"]) == (1.0, 4.0, 30.0, 31.0)
    assert (h["giveback_pts"], h["giveback_share"], h["gain_vs_peak"]) == (3.0, 0.75, 0.25)
    assert h["fut_fav_pts"] == 2.0 * pos["dir"] and h["attr_delta_pts"] is not None
    step(1000, -2.0, -4.0)                                 # two marks passed in one step: one snapshot, the later mark
    assert [x["mark"] for x in pos["weather_hold"]] == [60, 900]
    c = step(1010, -2.0, -4.0)
    weather5.hold_mark(pos, c, c["by_key"][key], "exit_req")
    weather5.hold_mark(pos, c, c["by_key"][key], "exit_req")
    weather5.hold_mark(pos, c, c["by_key"][key], "exit")   # a requested exit is photographed once, at the request
    assert [x["mark"] for x in pos["weather_hold"]] == [60, 900, "exit_req"]
    json.dumps(pos["weather_hold"], allow_nan=False)
    assert not (set(HOLD) & set(pos["weather_trig"])) and not (set(HOLD) & set(search.ITEM_OF))
    assert sorted(weather5.HOLD_ITEMS) == list(weather5.HOLD_ITEMS_N) and not (set(weather5.HOLD_ITEMS) & set(search.ITEMS))
    t = paper.close_trade(b, c, e - 2.0, "TEST")
    assert [x["mark"] for x in t["weather_hold"]] == [60, 900, "exit_req"]


def test_a_trade_never_in_profit_has_no_peak_timing_and_a_plain_close_is_photographed():
    T = tw.T_OPEN + 2 * 3600
    w = tw._fill(tw._W(), tw.T_OPEN, T + 400)
    b = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    ctx, o = tw._ctx(T, w)
    b.pos = paper.open_trade(b, ctx, o, "t") if b.pos is None else b.pos
    pos = b.pos
    c, _ = tw._ctx(T + 20, w)
    c["by_key"][pos["key"]]["ltp"] = pos["entry"] - 3.0
    t = paper.close_trade(b, c, pos["entry"] - 3.0, "TEST")
    h = t["weather_hold"]
    assert len(h) == 1 and h[0]["mark"] == "exit" and h[0]["gain_pts"] == -3.0
    assert h[0]["time_to_peak_s"] is None and h[0]["giveback_pts"] is None and h[0]["hold_s"] == 20.0
