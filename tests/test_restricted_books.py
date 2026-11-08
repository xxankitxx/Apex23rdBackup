"""Stage 5, the restricted books: the frozen rules R-002..R-005 as code (apex/engine/rules.py) match the register,
apply only to their families, and veto an entry exactly like every other entry veto."""
import json
import os
import sys
from datetime import datetime
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config, engine_main  # noqa: E402
from apex.engine import paper, rules  # noqa: E402

REG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apex", "rules", "register.json")


def _reg():
    return {r["id"]: r for r in json.load(open(REG, encoding="utf-8"))["rules"]}


def test_coded_rules_match_the_register():
    reg = _reg()
    for rid in rules.CODED:
        assert rid in reg and reg[rid]["frozen"] == "2026-11-07" and reg[rid]["first_test_day"] == "2026-11-09"
    assert "ER60 >= 0.35" in reg["R-002"]["condition"] and rules.ER60_MIN == 0.35
    assert "BREADTH_DIR >= 0.60" in reg["R-003"]["condition"] and rules.BREADTH_MIN == 0.60
    assert "12:00:00" in reg["R-004"]["condition"] and rules.COUNCIL_NORM_END == (12, 0)
    assert "14:30:00" in reg["R-005"]["condition"] and rules.LONG_HOLD_END == (14, 30)
    assert "ORB only" in reg["R-005"]["family"] and rules.LONG_HOLD_PATTERNS == ("ORB",)
    for p in rules.TREND_PATTERNS:
        assert p in reg["R-002"]["family"], p
    for p in rules.IMPULSE_PATTERNS:
        assert p in reg["R-003"]["family"], p


def test_restricted_books_are_the_free_book_plus_one_rule():
    for rid, reps in config.RESTRICTED.items():
        for rep in reps:
            p = dict(config.VARIANTS[f"{rep}_r{rid[2:]}"])
            assert p.pop("rules") == (rid,) and p == config.VARIANTS[rep]


def _ctx(h, m):
    return {"now_dt": datetime(2026, 11, 9, h, m, tzinfo=config.IST), "episode": None}


def test_r002_trend_filter():
    w = {"expiry_day": False, "mins_open": 120, "er60": 0.5, "dir60": 1}
    assert rules.r002(w, _ctx(11, 0), "SPOT-PULLBACK") is None
    assert rules.r002(dict(w, dir60=-1), _ctx(11, 0), "SPOT-PULLBACK")              # trending the other way
    assert rules.r002(dict(w, er60=0.2), _ctx(11, 0), "SPOT-PULLBACK")              # not trending
    assert rules.r002(dict(w, er60=None), _ctx(11, 0), "SPOT-PULLBACK")             # unknown: blocked
    assert rules.r002(dict(w, mins_open=30), _ctx(9, 45), "SPOT-PULLBACK")          # before 10:15
    assert rules.r002(dict(w, er60=0.1, expiry_day=True), _ctx(11, 0), "SPOT-PULLBACK") is None   # normal days only
    assert rules.r002(dict(w, er60=0.1), _ctx(11, 0), "FADE") is None              # not a trend follower
    assert rules.r002(dict(w, er60=0.1), _ctx(11, 0), "COUNCIL-NORM")


def test_r003_breadth():
    assert rules.r003({"breadth_dir": 0.6}, _ctx(11, 0), "ORB") is None
    assert rules.r003({"breadth_dir": 0.59}, _ctx(11, 0), "ORB")
    assert rules.r003({"breadth_dir": None}, _ctx(11, 0), "CO-FIRST")
    assert rules.r003({"breadth_dir": 0.1}, _ctx(11, 0), "SPOT-RETEST") is None     # not in R-003's families


def test_r004_r005_clock():
    assert rules.r004({"expiry_day": False}, _ctx(11, 59), "COUNCIL-NORM") is None
    assert rules.r004({"expiry_day": False}, _ctx(12, 0), "COUNCIL-NORM")
    assert rules.r004({"expiry_day": True}, _ctx(13, 0), "COUNCIL-EXP") is None
    assert rules.r005({}, _ctx(14, 29), "ORB") is None and rules.r005({}, _ctx(14, 30), "ORB")
    assert rules.r005({}, _ctx(14, 45), "SPOT-PULLBACK") is None


def test_check_through_a_book_and_an_unknown_rule():
    free = paper.Book("spot_orb45", config.VARIANTS["spot_orb45"], "2026-11-09")
    rb = paper.Book("spot_orb45_r005", config.VARIANTS["spot_orb45_r005"], "2026-11-09")
    rb.ctl["ep_type"] = free.ctl["ep_type"] = "ORB"
    ctx = dict(_ctx(14, 40), now_s=0.0, weather={})
    opt = {"rr": "CE", "delta": 0.55, "theta_min": -0.1, "ltp": 100.0}
    assert rules.check(free, ctx, opt) is None
    assert rules.check(rb, ctx, opt).startswith("R-005")
    odd = paper.Book("x", dict(config.VARIANTS["spot_orb45"], rules=("R-999",)), "2026-11-09")
    assert rules.check(odd, ctx, opt) == "R-999: not in the register"   # 8 Nov: register-stated rules are checked too
    c = paper.Book("c20_9x_r004", config.VARIANTS["c20_9x_r004"], "2026-11-09")
    w = dict(_ctx(12, 30), now_s=0.0, weather={}, w0="2026-11-10")              # 10 Nov expiry: a normal day
    assert rules.check(c, w, opt, "COUNCIL NORM pb v=+12").startswith("R-004")
    assert rules.check(c, w, opt, "COUNCIL EXP brk v=+20") is None


def test_the_engine_entry_choice_vetoes_and_clears_the_setup(monkeypatch):
    """The real path (Engine._entry_choice, shared with the missed-signal twins): a refused rule skips the setup."""
    opt = {"rr": "CE", "delta": 0.55, "theta_min": -0.1, "ltp": 100.0, "strike": 24500, "key": "k", "id": 1}

    def fire(b, ctx, gates):
        b.ctl.update(fire_id=-5, ep_type="ORB", dir=1)
        return True, "ORB break"
    monkeypatch.setattr(paper, "evaluate_entry", fire)
    monkeypatch.setattr(paper, "entry_dir", lambda b, ctx: 1)
    monkeypatch.setattr(paper, "choose_contract", lambda ctx, d, b: (dict(opt), ""))
    eng = SimpleNamespace()
    ctx = dict(_ctx(14, 40), now_s=0.0, weather={})
    rb = paper.Book("spot_orb45_r005", config.VARIANTS["spot_orb45_r005"], "2026-11-09")
    fired, o, why, msg = engine_main.Engine._entry_choice(eng, rb, ctx, [])
    assert fired and o is None and msg.startswith("R-005") and "fire_id" not in rb.ctl and "ep_type" not in rb.ctl
    free = paper.Book("spot_orb45", config.VARIANTS["spot_orb45"], "2026-11-09")
    fired, o, why, msg = engine_main.Engine._entry_choice(eng, free, ctx, [])
    assert fired and o is not None
