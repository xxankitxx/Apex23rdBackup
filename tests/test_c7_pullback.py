"""Council 7 (21 Oct evening): the pullback book (D-134). python tests/test_c7_pullback.py  (numpy only)"""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c7pb_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False
from apex.engine import paper  # noqa: E402
from apex.engine.impulse import ImpulseWindow  # noqa: E402

T0 = datetime(2026, 10, 21, 10, 30, tzinfo=config.IST)
OPT = {"id": 5, "key": "NIFTY|OPT|2026-10-27|23000|PE", "strike": 23000, "rr": "PE", "expiry": "2026-10-27",
       "ltp": 200.0, "bid": 199.9, "ask": 200.1, "delta": -0.55, "iv": 14.0, "age": 0.1, "week": 0, "ltt": None}


def _win(path, t0=0.0):
    w = ImpulseWindow(config.PB_WINDOW_S)
    for k, px in enumerate(path):
        w.add(t0 + k, px)
    return w


def _ctx(w, sp, now_s, now_dt=T0, **kw):
    c = {"now_s": now_s, "now_dt": now_dt, "w0": "2026-10-27", "spot": sp, "spot_age": 0.3, "pb": w.view(now_s),
         "spot_hi": None, "spot_lo": None, "fut": sp + 15, "fut_ltp": sp + 15, "advisors": {}, "blackout": {"on": False},
         "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
         "episode": None, "regime": {"state": "RANGE", "dir": None}}
    c.update(kw)
    return c


def _book():
    return paper.Book("spot_pb45", config.VARIANTS["spot_pb45"], "2026-10-21")


def _down_impulse_then(pull):
    """23100 flat 10 min, fall 100 pts over 10 min to 23000, flat 2 min, then the given pullback path."""
    path = [23100.0] * 600 + [23100.0 - k / 6.0 for k in range(600)] + [23000.0] * 120 + list(pull)
    return path


def test_champion_and_the_owner_switch_from_the_old_state():
    from apex.engine import learning
    import json
    assert config.CHAMPION_DEFAULT == "spot_dual_lvl" and config.CHAMPION_OWNER == ("spot_dual_lvl", "2026-10-22")
    st = learning._default_state()                   # what the PC holds today: the 20-Oct owner switch already applied
    st["champion"], st["champion_since"] = "spot_dc12_t12", "2026-10-20"
    st["owner_champion"] = ["spot_dc12_t12", "2026-10-20"]
    os.makedirs(config.LEARN_DIR, exist_ok=True)
    with open(learning.STATE, "w", encoding="utf-8") as f:
        json.dump(st, f)
    s1 = learning.load_state()
    assert s1["champion"] == "spot_dual_lvl" and s1["champion_since"] == "2026-10-22"
    os.remove(learning.STATE)


def test_registered_and_valid():
    p = config.VARIANTS["spot_pb45"]
    assert p["entry_mode"] == "pullback" and p["pb_min_range"] == 60.0 and (p["pb_zone_lo"], p["pb_zone_hi"]) == (0.5, 0.78)
    assert p["pb_entry_end"] == (14, 45) and p["pb_flatten"] == (15, 0) and p["lock_pct"] == config.LOCK_PCT
    assert config.validate() == []


def test_window_tracks_extremes_and_the_deepest_pullback():
    w = _win([10, 12, 11, 15, 9, 9, 13, 14])
    v = w.view()
    assert v["hi"] == 15 and v["lo"] == 9 and v["t_lo"] == 4 and v["d"] == -1 and v["pbx"] == 14
    w2 = _win([10, 20, 15, 18, 12])
    v2 = w2.view()
    assert v2["d"] == 1 and v2["pbx"] == 12 and v2["t_hi"] == 1


def test_no_entry_without_an_impulse_or_before_the_zone():
    b = _book()
    w = _win([23000.0 + (k % 40) for k in range(1500)])            # 40-pt chop: no impulse
    ok, why = paper.evaluate_entry(b, _ctx(w, 23020.0, 1500.0), [])
    assert not ok and "no impulse" in why
    path = _down_impulse_then([23000.0 + k / 10 for k in range(300)])   # pulls back 30 pts: 30 %
    w = _win(path)
    ok, why = paper.evaluate_entry(_book(), _ctx(w, path[-1], len(path) - 1), [])
    assert not ok and "waiting for a pullback" in why


def test_buys_the_pe_in_the_zone_once_per_impulse():
    path = _down_impulse_then([23000.0 + k / 10 for k in range(620)])   # back up 62 pts = 62 % of the 100-pt fall
    w = _win(path)
    b = _book()
    ok, why = paper.evaluate_entry(b, _ctx(w, path[-1], len(path) - 1), [])
    assert ok and b.ctl["dir"] == -1 and b.ctl["ep_type"] == "SPOT-PULLBACK", why
    pt = b.ctl["pb_trade"]
    assert pt["origin"] == 23100.0 and pt["ext_px"] == 23000.0 and abs(pt["rng"] - 100.0) < 1e-9
    paper.open_trade(b, _ctx(w, path[-1], len(path) - 1), dict(OPT), why)
    assert b.pos["pb"]["origin"] == 23100.0 and "pb_trade" not in b.ctl
    b.pos = None                                                      # flat again, same impulse
    ok, why = paper.evaluate_entry(b, _ctx(w, path[-1], len(path)), [])
    assert not ok and "already traded" in why


def test_a_pullback_past_78_percent_spends_the_impulse():
    path = _down_impulse_then([23000.0 + k / 10 for k in range(850)] + [23085.0 - k / 10 for k in range(200)])
    w = _win(path)
    ok, why = paper.evaluate_entry(_book(), _ctx(w, path[-1], len(path) - 1), [])
    assert not ok and "spent" in why


def test_structural_exit_stop_and_target_and_holding_through_a_bounce():
    path = _down_impulse_then([23000.0 + k / 10 for k in range(620)])
    w = _win(path)
    b = _book()
    c = _ctx(w, path[-1], len(path) - 1)
    assert paper.evaluate_entry(b, c, [])[0]
    paper.open_trade(b, c, dict(OPT), "t")
    q = dict(OPT, ltp=205.0)
    held = lambda sp, s: dict(_ctx(w, sp, s), by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1)   # noqa: E731
    s0 = len(path)
    assert paper.check_exit(b, held(23040.0, s0)) is None             # fell 22 pts
    assert paper.check_exit(b, held(23095.0, s0 + 60)) is None        # a 55-pt bounce: a 12-pt trail would be out; this holds
    assert b.pos["stop_spot"] == 23100.0 and b.pos["target_spot"] == 22900.0
    t = paper.check_exit(b, held(23101.0, s0 + 120))
    assert t and t["reason"].startswith("STOP (impulse origin")
    b2 = _book(); c2 = _ctx(w, path[-1], len(path) - 1)
    assert paper.evaluate_entry(b2, c2, [])[0]
    paper.open_trade(b2, c2, dict(OPT), "t")
    t = paper.check_exit(b2, held(22899.0, s0 + 600))
    assert t and t["reason"].startswith("TARGET")


def test_entry_window_and_book_flatten():
    path = _down_impulse_then([23000.0 + k / 10 for k in range(620)])
    w = _win(path)
    late = datetime(2026, 10, 21, 14, 46, tzinfo=config.IST)
    ok, why = paper.evaluate_entry(_book(), _ctx(w, path[-1], len(path) - 1, now_dt=late), [])
    assert not ok and "14:45" in why
    b = _book(); c = _ctx(w, path[-1], len(path) - 1)
    assert paper.evaluate_entry(b, c, [])[0]
    paper.open_trade(b, c, dict(OPT), "t")
    q = dict(OPT, ltp=205.0)
    t = paper.check_exit(b, dict(_ctx(w, 23050.0, len(path) + 5, now_dt=datetime(2026, 10, 21, 15, 0, 1, tzinfo=config.IST)),
                                 by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1))
    assert t and "15:00 book flatten" in t["reason"]


def test_one_shot_survives_a_restart_and_warm_state_round_trips():
    path = _down_impulse_then([23000.0 + k / 10 for k in range(620)])
    w = _win(path)
    b = _book()
    assert paper.evaluate_entry(b, _ctx(w, path[-1], len(path) - 1), [])[0]
    b2 = paper.Book.from_json(b.to_json())
    assert b2.ctl["pb_done"] == b.ctl["pb_done"]
    w2 = ImpulseWindow.load(w.dump(), config.PB_WINDOW_S)
    assert w2.view() == w.view()


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"):
            fn(); print("ok", k)
