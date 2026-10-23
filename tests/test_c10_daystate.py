"""Council 9 (22 Oct): day state, range mode, level booking, premium booking, ORB (D-141). python tests/test_c10_daystate.py"""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c10_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False
from apex.engine import paper  # noqa: E402
from apex.engine.daystate import DayState, load_prior, save_day  # noqa: E402
from apex.engine.impulse import ImpulseWindow  # noqa: E402

T0 = datetime(2026, 10, 22, 11, 50, tzinfo=config.IST)
OPT = {"id": 5, "key": "NIFTY|OPT|2026-10-27|22700|CE", "strike": 22700, "rr": "CE", "expiry": "2026-10-27",
       "ltp": 200.0, "bid": 199.9, "ask": 200.1, "delta": 0.55, "iv": 14.0, "age": 0.1, "week": 0, "ltt": None}


def _feed(ds, path, t0=0.0):
    for k, px in enumerate(path):
        ds.add(t0 + k, px, 600)
    return ds


def test_champion_and_registry():
    assert config.CHAMPION_DEFAULT == "spot_dual_lvl" and config.CHAMPION_OWNER == ("spot_dual_lvl", "2026-10-22")
    p = config.VARIANTS["spot_dual_rg"]
    assert p["range_gate"] and p["dte0_retest"] and p["entry_mode"] == "pullback"
    for n in ("spot_dual_lvl", "spot_ft_prem10", "spot_orb45"):
        assert n in config.VARIANTS
    assert config.validate() == []


def test_range_mode_turns_on_after_a_618_giveback_and_off_at_a_new_extreme():
    ds = DayState("2026-10-22")
    up = [22600.0 + k * 0.2 for k in range(1000)]          # 22600 -> 22799.8: a 200-pt up leg
    _feed(ds, up)
    assert not ds.range_on
    down = [22799.8 - k * 0.2 for k in range(1, 700)]      # back to 22660: gave back 70 %
    _feed(ds, down, 1000)
    assert ds.range_on and ds.range_since is not None
    _feed(ds, [22661.0 + k for k in range(0, 160)], 2000)  # rallies to a new day high 22820
    assert not ds.range_on
    ds2 = _feed(DayState("x"), [22600.0 + (k % 80) for k in range(3000)])   # an 80-pt box: never a 100-pt leg
    assert not ds2.range_on


def test_pullback_book_stands_aside_in_range_mode_but_dual_retest_on_expiry_day_does_not():
    w = ImpulseWindow(config.PB_WINDOW_S)
    path = [23100.0] * 600 + [23100.0 - k / 6.0 for k in range(600)] + [23000.0] * 120 + [23000.0 + k / 10 for k in range(620)]
    for k, px in enumerate(path):
        w.add(k, px)
    ctx = {"now_s": len(path) - 1, "now_dt": T0, "w0": "2026-10-27", "spot": path[-1], "spot_age": 0.3, "pb": w.view(),
           "day": {"range_on": True, "range_since": 1792664000.0, "hi": 23100.0, "lo": 22990.0},
           "advisors": {}, "blackout": {"on": False}, "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0,
                                                                  "sigma15": 5.0, "gap": 0.0}, "episode": None, "regime": {}}
    b = paper.Book("spot_dual_rg", config.VARIANTS["spot_dual_rg"], "2026-10-22")
    ok, why = paper.evaluate_entry(b, ctx, [])
    assert not ok and "range mode" in why
    b2 = paper.Book("spot_dual", config.VARIANTS["spot_dual"], "2026-10-22")          # the ungated twin takes it
    assert paper.evaluate_entry(b2, ctx, [])[0]
    ctx3 = dict(ctx, day=dict(ctx["day"], range_on=False))
    assert paper.evaluate_entry(paper.Book("spot_dual_rg", config.VARIANTS["spot_dual_rg"], "2026-10-22"), ctx3, [])[0]


def _ctx(sp, s, ds, **kw):
    c = {"now_s": float(s), "now_dt": T0, "w0": "2026-10-27", "spot": sp, "spot_age": 0.3, "fut": sp + 15, "fut_ltp": sp + 15,
         "day": dict(ds.view(), or_done=ds.or_done(s), t0=ds.t0), "day_obj": ds, "advisors": {}, "blackout": {"on": False},
         "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0}, "episode": None,
         "regime": {}}
    c.update(kw)
    return c


def test_level_booking_books_a_stall_under_a_level():
    ds = DayState("2026-10-22", prior={"hi": 22811.0, "lo": 22560.0, "close": 22738.45})
    _feed(ds, [22650.0] * 50)
    b = paper.Book("spot_dual_lvl", config.VARIANTS["spot_dual_lvl"], "2026-10-22")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK"})
    paper.open_trade(b, _ctx(22700.0, 100, ds), dict(OPT), "t")
    labs = [x[1] for x in b.pos["lv_ahead"]]
    assert "PDC" in labs and b.pos["lv_ahead"][0][0] > 22700.0
    q = dict(OPT, ltp=215.0)
    held = lambda sp, s: dict(_ctx(sp, s, ds), by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1)   # noqa: E731
    assert paper.check_exit(b, held(22735.0, 110)) is None      # 3.45 below the prior close: at the level
    t = paper.check_exit(b, held(22724.0, 120))                  # gave back 11 without breaking it
    assert t and t["reason"].startswith("BOOK at PDC"), t and t["reason"]


def test_premium_booking_book():
    b = paper.Book("spot_ft_prem10", config.VARIANTS["spot_ft_prem10"], "2026-10-22")
    ds = _feed(DayState("x"), [22650.0] * 10)
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-BREAKOUT"})
    paper.open_trade(b, _ctx(22700.0, 100, ds), dict(OPT), "t")
    q = dict(OPT, ltp=208.0)
    held = lambda sp, s, q: dict(_ctx(sp, s, ds), by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1)   # noqa: E731
    assert paper.check_exit(b, held(22680.0, 110, q)) is None    # a 20-pt spot drop would trail out a 12-pt book; not this one
    t = paper.check_exit(b, held(22720.0, 120, dict(OPT, ltp=221.0)))
    assert t and t["reason"].startswith("TARGET (premium")


def test_orb_entry_stop_and_booking_and_one_per_direction():
    ds = DayState("2026-10-22", prior={"hi": 22811.0, "lo": 22560.0, "close": 22738.45})
    _feed(ds, [22600.0 + (k % 60) for k in range(config.OR_WINDOW_S + 5)])   # opening range 22600-22659
    s = config.OR_WINDOW_S + 10
    b = paper.Book("spot_orb45", config.VARIANTS["spot_orb45"], "2026-10-22")
    ok, why = paper.evaluate_entry(b, _ctx(22650.0, s, ds), [])
    assert not ok and "inside the opening range" in why
    ok, why = paper.evaluate_entry(b, _ctx(22661.0, s + 1, ds), [])
    assert ok and b.ctl["dir"] == 1 and b.ctl["orb_trade"]["stop"] == 22600.0
    paper.open_trade(b, _ctx(22661.0, s + 1, ds), dict(OPT), why)
    assert b.pos["orb"]["stop"] == 22600.0
    q = dict(OPT, ltp=205.0)
    held = lambda sp, t: dict(_ctx(sp, t, ds), by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1)   # noqa: E731
    assert paper.check_exit(b, held(22690.0, s + 50)) is None
    t = paper.check_exit(b, held(22701.0, s + 60))               # first classic level >= 15 pts beyond entry: 22700
    assert t and t["reason"].startswith("BOOK at 22700"), t and t["reason"]
    ok, why = paper.evaluate_entry(b, _ctx(22665.0, s + 70, ds), [])
    assert not ok and "already taken" in why


def test_day_levels_saved_and_loaded_and_warm_roundtrip():
    ds = _feed(DayState("2026-10-22"), [22600.0, 22784.25, 22555.1, 22660.2])
    save_day(ds)
    pr = load_prior("2026-10-23")
    assert pr["day"] == "2026-10-22" and pr["hi"] == 22784.25 and pr["lo"] == 22555.1 and pr["close"] == 22660.2
    assert load_prior("2026-10-22") == {} or load_prior("2026-10-22").get("day") != "2026-10-22"
    ds2 = DayState.load(ds.dump())
    assert ds2.view() == ds.view()


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"):
            fn(); print("ok", k)
