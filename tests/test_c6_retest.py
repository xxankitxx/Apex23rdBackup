"""Council 6 (21 Oct): the retest entry (D-131). python tests/test_c6_retest.py  (numpy only)"""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c6rt_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config  # noqa: E402
from apex.engine import paper  # noqa: E402

T0 = datetime(2026, 10, 21, 10, 0, tzinfo=config.IST)
HI, LO = 25200.0, 25150.0


def _ctx(spot, s, hi=HI, lo=LO, **kw):
    c = {"now_s": 1000.0 + s, "now_dt": T0, "w0": "2026-10-27", "spot": spot, "spot_hi": hi, "spot_lo": lo, "spot_age": 0.3,
         "fut": spot + 10, "fut_ltp": spot + 10, "advisors": {}, "blackout": {"on": False},
         "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
         "episode": None, "regime": {"state": "RANGE", "dir": None}}
    c.update(kw)
    return c


def _book(name="spot_dc12_t12"):
    return paper.Book(name, config.VARIANTS[name], "2026-10-21")


def _ev(b, spot, s, **kw):
    return paper.evaluate_entry(b, _ctx(spot, s, **kw), [])


def test_config_and_twin():
    p, q = config.VARIANTS["spot_dc12_t12"], config.VARIANTS["spot_dc12_t12_first"]
    assert (p["retest_ext"], p["retest_tol"], p["retest_fail"], p["retest_window_s"]) == (5.0, 2.0, 3.0, 300)
    assert q["retest_ext"] == 0.0 and q["lock_pct"] == p["lock_pct"] and q["spot_trail"] == p["spot_trail"]
    assert config.CHAMPION_DEFAULT == "spot_dual_lvl" and config.validate() == []   # D-142: dual + range mode + level booking
    bad = dict(p, retest_tol=6.0)
    old = config.VARIANTS["_x"] = bad
    try:
        assert any("retest" in x for x in config.validate())
    finally:
        del config.VARIANTS["_x"]
    assert config.validate() == []


def test_a_break_alone_does_not_buy():
    b = _book()
    ok, why = _ev(b, 25201.0, 0)
    assert not ok and "armed" in why and b.ctl["rt"]["L"] == HI and b.ctl["rt"]["d"] == 1
    ok, why = _ev(b, 25203.0, 1)
    assert not ok and "waiting for spot to run" in why


def test_run_then_pullback_buys_the_ce():
    b = _book()
    _ev(b, 25201.0, 0)
    ok, why = _ev(b, 25206.0, 5)                               # 6 beyond the level: extension reached
    assert not ok and "waiting for the pullback" in why
    assert not _ev(b, 25204.0, 6)[0]                           # +4 beyond: not back yet
    ok, why = _ev(b, 25201.5, 7)                               # +1.5: within 2 of the level and the level held
    assert ok and "held" in why and b.ctl["dir"] == 1 and b.ctl["ep_type"] == "SPOT-RETEST" and "rt" not in b.ctl


def test_put_side_is_symmetric():
    b = _book()
    _ev(b, 25149.0, 0)
    assert b.ctl["rt"]["d"] == -1 and b.ctl["rt"]["L"] == LO
    assert not _ev(b, 25143.0, 4)[0]
    ok, why = _ev(b, 25148.5, 6)
    assert ok and b.ctl["dir"] == -1


def test_no_run_means_no_trade_and_a_lost_level_cancels():
    b = _book()
    _ev(b, 25201.0, 0)
    ok, why = _ev(b, 25196.0, 3)                               # fell 4 below the level before any run: cancelled
    assert not ok and "cancelled" in why and "rt" not in b.ctl
    b2 = _book()
    _ev(b2, 25201.0, 0); _ev(b2, 25207.0, 2)
    ok, why = _ev(b2, 25196.5, 4)                              # ran, then lost the level by 3.5
    assert not ok and "cancelled" in why and "rt" not in b2.ctl


def test_window_expires():
    b = _book()
    _ev(b, 25201.0, 0); _ev(b, 25207.0, 2)
    ok, why = _ev(b, 25206.0, 301)                             # 300 s passed without a retest
    assert not ok and "within 300 s" in why


def test_stale_spot_or_a_hole_drops_the_armed_break():
    b = _book()
    _ev(b, 25201.0, 0); _ev(b, 25207.0, 2)
    ok, why = paper.evaluate_entry(b, _ctx(25201.5, 3, spot_age=9.0), [])
    assert not ok and "old" in why and "rt" not in b.ctl
    b2 = _book()
    _ev(b2, 25201.0, 0)
    assert not paper.evaluate_entry(b2, _ctx(25201.0, 1, spot_hi=None, spot_lo=None), [])[0] and "rt" not in b2.ctl


def test_swing_rule_is_checked_when_the_break_is_armed():
    b = _book()
    b.ctl["swing_last"] = {"d": 1, "best": 25230.0}
    ok, why = _ev(b, 25201.0, 0)
    assert not ok and "same swing" in why and "rt" not in b.ctl
    assert _ev(b, 25149.0, 1)[0] is False and b.ctl["rt"]["d"] == -1      # the other side is a new swing: armed


def test_an_opposite_break_replaces_an_armed_one():
    b = _book()
    _ev(b, 25201.0, 0)
    ok, why = _ev(b, 25147.0, 10, hi=25210.0, lo=25150.0)       # crashed through the level and the low
    assert not ok and b.ctl["rt"]["d"] == -1 and b.ctl["rt"]["L"] == 25150.0


def test_first_touch_twin_is_unchanged():
    b = _book("spot_dc12_t12_first")
    ok, why = _ev(b, 25201.0, 0)
    assert ok and "high" in why and b.ctl["ep_type"] == "SPOT-BREAKOUT" and "rt" not in b.ctl


def test_armed_state_is_not_persisted_and_roundtrip_is_clean():
    b = _book()
    _ev(b, 25201.0, 0)
    b2 = paper.Book.from_json(b.to_json())
    assert "rt" not in b2.ctl and b2.p["retest_ext"] == 5.0


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"):
            fn(); print("ok", k)
