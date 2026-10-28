"""27 Oct evening: hard premium stop + gain trail on the 30-s average (owner: "giving away too much from the peak"),
and each strike's own support / resistance (strike_levels.py). python tests/test_c12_trail_levels.py"""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c12_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False
from apex.engine import paper  # noqa: E402
from apex.engine import strike_levels as slm  # noqa: E402

T0 = datetime(2026, 10, 23, 10, 30, tzinfo=config.IST)
OPT = {"id": 5, "key": "NIFTY|OPT|2026-10-27|22700|CE", "strike": 22700, "rr": "CE", "expiry": "2026-10-27",
       "ltp": 200.0, "bid": 199.9, "ask": 200.1, "delta": 0.55, "iv": 14.0, "age": 0.1, "week": 0, "ltt": None,
       "gamma": 0.0012, "theta_min": -0.12}


def _ctx(s, ltp=200.0, spot=22700.0):
    q = dict(OPT, ltp=ltp)
    return {"now_s": float(s), "now_dt": T0, "w0": "2026-10-27", "spot": spot, "spot_age": 0.3, "fut": 22715.0,
            "fut_ltp": 22715.0, "fut_age": 0.1, "day": {}, "day_obj": None, "advisors": {}, "blackout": {"on": False},
            "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
            "episode": None, "regime": {}, "edge": {"v_min30": 200.0}, "by_id": {5: q}, "by_key": {OPT["key"]: q}}


def _book(name="edge_gate_trail"):
    b = paper.Book(name, config.VARIANTS[name], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK"})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    return b


def test_champion_and_params():
    p = config.VARIANTS["edge_gate_trail"]
    assert config.CHAMPION_DEFAULT == "lvl_trail_re" and config.validate() == []
    q = config.VARIANTS["lvl_trail_re"]
    assert q["reentry"] and q["reentry_stop"] and not q.get("reentry_any") and "gt_min" not in q and "alloc_pct" not in q
    assert (p["prem_hard_stop"], p["gt_arm_pct"], p["gt_keep"], p["gt_smooth_s"]) == (10.0, 20.0, 0.8, 30.0)
    assert p["gt_min"] == 0.5 and p["lvl_book"] and "alloc_pct" not in p      # edge_gate_only + the two exits, all-in
    assert "lvl_trail" in config.VARIANTS and "edge_gate_only" in config.VARIANTS


def test_hard_stop():
    b = _book()
    assert paper.check_exit(b, _ctx(101, 182.0)) is None                      # -9 %
    t = paper.check_exit(b, _ctx(102, 179.0))                                 # -10.5 %
    assert t and t["reason"].startswith("STOP (premium -10.5 %, hard stop")


def test_gain_trail_keeps_80_pct_of_the_peak_gain():
    b = _book()
    s = 100
    for _ in range(40):                                                       # +30 % held: the 30-s average reaches +30 %
        s += 1
        assert paper.check_exit(b, _ctx(s, 260.0)) is None
    assert b.pos["gt_peak"] >= 29.9
    t = None
    for _ in range(40):                                                       # back to +20 %: the average falls through +24 %
        s += 1
        t = paper.check_exit(b, _ctx(s, 240.0))
        if t:
            break
    assert t and t["reason"].startswith("TRAIL (kept"), t
    assert t["ret_pct"] >= 19.9


def test_gain_trail_ignores_a_one_second_dip():
    b = _book()
    s = 100
    for _ in range(40):
        s += 1
        paper.check_exit(b, _ctx(s, 260.0))
    assert paper.check_exit(b, _ctx(s + 1, 236.0)) is None                    # one print at +18 %: the average holds
    assert paper.check_exit(b, _ctx(s + 2, 262.0)) is None


def test_no_trail_before_arming():
    b = _book()
    for s in range(101, 160):
        assert paper.check_exit(b, _ctx(s, 230.0 if s < 130 else 215.0)) is None   # peak +15 % < arm 20 %


def test_strike_levels_breaks_and_view():
    sl = slm.StrikeLevels("2026-10-23", prior={OPT["key"]: {"hi": 300.0, "lo": 150.0, "close": 210.0}})
    k, t0, hm = OPT["key"], 1_000_000.0, 600
    ev = []
    for i in range(600):                                                      # 10 min oscillating 195..205
        ev += sl.add(t0 + i, k, 200.0 + (5.0 if (i // 60) % 2 else -5.0), hm)
    assert not [e for e in ev if e["label"] == "day low"]
    v = sl.view(k, 200.0)
    assert v["res"][0] == [205.0, "day high"] and v["sup"][0] == [195.0, "day low"]
    assert [210.0, "prior close"] in v["res"] and v["room_up_pct"] == 2.5
    ev = sl.add(t0 + 601, k, 190.0, hm)                                       # 2.6 % under a 9-min-old day low
    assert any(e["label"] == "day low" and e["dir"] == "DOWN" and e["kind"] == "support" for e in ev), ev
    assert not [e for e in sl.add(t0 + 602, k, 189.0, hm) if e["label"] == "day low"]   # once only
    up = sl.add(t0 + 603, k, 213.0, hm)                                       # through the prior close 210 by 1 %+
    assert any(e["label"] == "prior close" and e["dir"] == "UP" for e in up), up


def test_strike_levels_pivots_and_prior_file():
    sl = slm.StrikeLevels("2026-10-23")
    k, t0 = OPT["key"], 1_000_020.0 - (1_000_020.0 % 60)
    for m, (hi, lo) in enumerate([(100, 98), (102, 99), (108, 101), (103, 100), (101, 97), (100, 96)]):
        sl.add(t0 + m * 60, k, lo, 600)
        sl.add(t0 + m * 60 + 30, k, hi, 600)
    sl.add(t0 + 6 * 60, k, 99.0, 600)
    assert sl.s[k]["piv_hi"] and sl.s[k]["piv_hi"][0][0] == 108
    slm.save_day(sl)
    pr = slm.load_prior("2026-10-26")
    assert pr[k] == {"hi": 108, "lo": 96, "close": 99.0}
    assert slm.load_prior("2026-10-23") == {}                                 # same day is not a prior day


def test_trade_carries_levels_at_entry():
    sl = slm.StrikeLevels("2026-10-23")
    for i in range(400):
        sl.add(float(i), OPT["key"], 190.0 + (i % 20), 600)
    b = paper.Book("edge_gate_trail", config.VARIANTS["edge_gate_trail"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK"})
    c = _ctx(400)
    c["strike_lv"] = sl
    pos = paper.open_trade(b, c, dict(OPT), "t")
    assert pos["sr_in"]["px"] == 200.0 and pos["sr_in"]["res"][0][1] == "day high"


def _reentry_book():
    b = paper.Book("lvl_trail_re", config.VARIANTS["lvl_trail_re"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK", "trig_str": 80.0, "trig_unit": "pt impulse"})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    assert b.pos["trig_str"] == 80.0
    t = paper.close_trade(b, _ctx(400, 240.0), 240.0, "TRAIL (kept +20.0 % of a +25.0 % peak gain, 30-s average)")
    assert b.ctl["reentry"]["exit_px"] == 240.0 and b.ctl["reentry"]["str"] == 80.0 and t["ret_pct"] == 20.0
    return b


def _ctx_chain(s, ce22700, ce22750):
    c = _ctx(s, ce22700)
    o2 = dict(OPT, id=6, key="NIFTY|OPT|2026-10-27|22750|CE", strike=22750, ltp=ce22750)
    c["by_key"][o2["key"]] = o2
    c["by_id"][6] = o2
    return c


def test_reentry_within_10_min_needs_a_stronger_trigger():
    b = _reentry_book()
    b.ctl["trig_str"] = 75.0                                                  # a weaker impulse, 5 min later
    opt, why = paper.reentry_check(b, _ctx_chain(700, 230.0, 200.0), 1, dict(OPT, ltp=230.0))
    assert opt is None and "stronger trigger" in why
    b.ctl["trig_str"] = 95.0                                                  # stronger: allowed, and cheaper than 240
    opt, why = paper.reentry_check(b, _ctx_chain(700, 230.0, 200.0), 1, dict(OPT, ltp=230.0))
    assert opt and opt["strike"] == 22700 and why == ""


def test_reentry_moves_one_strike_otm_when_the_old_strike_is_dearer():
    b = _reentry_book()
    b.ctl["trig_str"] = 95.0
    opt, _ = paper.reentry_check(b, _ctx_chain(700, 250.0, 215.0), 1, dict(OPT, ltp=250.0))
    assert opt and opt["strike"] == 22750 and opt["_reentry_otm"]             # 22750 CE at 215 < the 240 exit
    opt, why = paper.reentry_check(b, _ctx_chain(700, 250.0, 245.0), 1, dict(OPT, ltp=250.0))
    assert opt is None and "cheaper than the 240.00 exit" in why


def test_reentry_after_10_min_only_needs_cheaper_and_expires_at_30():
    b = _reentry_book()
    b.ctl["trig_str"] = 10.0                                                  # weak, but 11 min later: allowed
    opt, _ = paper.reentry_check(b, _ctx_chain(400 + 660, 230.0, 200.0), 1, dict(OPT, ltp=230.0))
    assert opt and opt["strike"] == 22700
    opt, _ = paper.reentry_check(b, _ctx_chain(400 + 1900, 260.0, 250.0), 1, dict(OPT, ltp=260.0))
    assert opt and opt["ltp"] == 260.0 and "reentry" not in b.ctl             # 30 min on: rules lapse


def test_reentry_rules_only_after_a_trailing_exit_and_same_direction():
    b = _reentry_book()
    opt, _ = paper.reentry_check(b, _ctx_chain(500, 260.0, 250.0), -1, dict(OPT, rr="PE", ltp=260.0))
    assert opt is not None                                                    # the other direction is a new trade
    b2 = paper.Book("lvl_trail_re", config.VARIANTS["lvl_trail_re"], "2026-10-23")
    b2.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK", "trig_str": 80.0})
    paper.open_trade(b2, _ctx(100), dict(OPT), "t")
    paper.close_trade(b2, _ctx(200, 179.0), 179.0, "STOP (premium -10.5 %, hard stop -10 %)")
    assert b2.ctl["reentry"]["trail"] is False                                # after a stop: stronger only (28 Oct)
    b2.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK", "trig_str": 80.0})
    paper.open_trade(b2, _ctx(300), dict(OPT), "t")
    paper.close_trade(b2, _ctx(400, 215.0), 215.0, "BOOK at 22800 22800.0")
    assert "reentry" not in b2.ctl                                            # a profit booking leaves no mark
    js = paper.Book.from_json(b.to_json())
    assert js.ctl["reentry"]["exit_px"] == 240.0                              # survives a restart


def test_expiry_day_max_hold():
    b = paper.Book("lvl_trail_re", config.VARIANTS["lvl_trail_re"], "2026-10-27")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-RETEST"})
    exp = datetime(2026, 10, 27, 10, 0, tzinfo=config.IST)
    c = _ctx(100)
    c["now_dt"] = exp
    paper.open_trade(b, c, dict(OPT), "t")
    c = _ctx(100 + 599, 205.0); c["now_dt"] = exp
    assert paper.check_exit(b, c) is None
    c = _ctx(100 + 600, 205.0); c["now_dt"] = exp
    t = paper.check_exit(b, c)
    assert t and t["reason"] == "TIME (expiry day, max hold 10 min)"
    a = _book("lvl_trail_re")                                                 # 23 Oct, 4 DTE: no 10-min limit
    assert paper.check_exit(a, _ctx(100 + 700, 205.0)) is None


def test_stronger_trigger_after_any_exit():
    """reentry_any: after a STOP, a same-direction re-entry within 10 min must be stronger; no price rule; lapses at 10."""
    b = paper.Book("lvl_trail_rx", config.VARIANTS["lvl_trail_rx"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK", "trig_str": 80.0, "trig_unit": "pt impulse"})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    paper.close_trade(b, _ctx(200, 179.0), 179.0, "STOP (premium -10.5 %, hard stop -10 %)")
    assert b.ctl["reentry"]["trail"] is False
    b.ctl["trig_str"] = 70.0
    opt, why = paper.reentry_check(b, _ctx_chain(500, 190.0, 160.0), 1, dict(OPT, ltp=190.0))
    assert opt is None and "stop exit needs a stronger trigger" in why, why
    b.ctl["trig_str"] = 90.0                                                  # stronger: allowed even though dearer
    opt, why = paper.reentry_check(b, _ctx_chain(500, 190.0, 160.0), 1, dict(OPT, ltp=190.0))
    assert opt and opt["strike"] == 22700 and why == ""
    b.ctl["trig_str"] = 10.0                                                  # 10 min on: the mark lapses
    opt, _ = paper.reentry_check(b, _ctx_chain(200 + 600, 190.0, 160.0), 1, dict(OPT, ltp=190.0))
    assert opt and "reentry" not in b.ctl
    opt, _ = paper.reentry_check(b, _ctx_chain(500, 190.0, 160.0), -1, dict(OPT, rr="PE", ltp=190.0))
    assert opt                                                                # other direction never limited


def test_breakeven_guard():
    b = paper.Book("lvl_trail_rx_be", config.VARIANTS["lvl_trail_rx_be"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK"})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    s = 100
    for _ in range(40):                                                       # +15 %: armed (10), below the trail arm (20)
        s += 1
        assert paper.check_exit(b, _ctx(s, 230.0)) is None
    t = None
    for _ in range(80):                                                       # back under entry: out near +1 %
        s += 1
        t = paper.check_exit(b, _ctx(s, 196.0))
        if t:
            break
    assert t and t["reason"].startswith("BREAKEVEN"), t
    a = _book("lvl_trail")                                                    # without the guard: still open
    for s in range(101, 141):
        paper.check_exit(a, _ctx(s, 230.0))
    for s in range(141, 221):
        assert paper.check_exit(a, _ctx(s, 196.0)) is None


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)
