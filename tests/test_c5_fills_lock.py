"""Council 5: D-126 fills on the first print after the trigger, D-127 the premium profit lock.
python tests/test_c5_fills_lock.py  (numpy only)"""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c5_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config  # noqa: E402
from apex.engine import paper  # noqa: E402

assert config.FILL_NEXT_PRINT, "this suite tests D-126 as shipped"

T_NORMAL = datetime(2026, 10, 21, 10, 0, tzinfo=config.IST)
T_FLAT = datetime(2026, 10, 21, config.FLATTEN_AT[0], config.FLATTEN_AT[1], tzinfo=config.IST)
OPT = {"id": 5, "key": "NIFTY|OPT|2026-10-27|25150|CE", "strike": 25150, "rr": "CE", "expiry": "2026-10-27",
       "ltp": 150.0, "bid": 149.9, "ask": 150.1, "delta": 0.7, "iv": 14.0, "age": 0.1, "week": 0, "ltt": None}


def _ctx(spot, hi=25200.0, lo=25150.0, now_s=1000.0, now_dt=T_NORMAL, w0="2026-10-27", **kw):
    c = {"now_s": now_s, "now_dt": now_dt, "w0": w0, "spot": spot, "spot_hi": hi, "spot_lo": lo,
         "fut": spot + 10, "fut_mid": spot + 10, "fut_ltp": spot + 10, "advisors": {}, "blackout": {"on": False},
         "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
         "episode": None, "regime": {"state": "RANGE", "dir": None}, "fut_age": 0.1, "spot_age": 0.3}
    c.update(kw)
    return c


def _book(name="spot_dc12_t12_first"):     # D-131: the first-touch twin; the retest champion is covered in test_c6_retest.py
    return paper.Book(name, config.VARIANTS[name], "2026-10-21")


def _q(ltp, age=0.1):
    return dict(OPT, ltp=ltp, bid=ltp - 0.2, ask=ltp + 0.2, age=age)


def _held(sp, s, ltp=160.0, age=0.1, **kw):
    q = _q(ltp, age)
    return dict(_ctx(sp, now_s=s, **kw), by_id={5: q}, by_key={OPT["key"]: q})


def _open(b, spot=25201.0, s=1000.0, ltp=150.0):
    """Open through the D-126 path: trigger, then the first print after it."""
    c = _ctx(spot, now_s=s)
    assert paper.evaluate_entry(b, c, [])[0]
    paper.request_entry(b, c, _q(ltp), "t")
    pos, why = paper.try_fill_entry(b, dict(_held(spot, s + 0.3, ltp=ltp + 0.5, age=0.1)))
    assert pos, why
    return pos


# ── D-126 entries ──────────────────────────────────────────────────────────────
def test_entry_waits_for_the_first_print_after_the_trigger():
    b = _book()
    c = _ctx(25201.0, now_s=1000.0)
    assert paper.evaluate_entry(b, c, [])[0]
    paper.request_entry(b, c, _q(150.0, age=0.05), "spot broke")
    assert b.pos is None and b.ctl["pending_entry"]["key"] == OPT["key"]
    assert paper.evaluate_entry(b, _ctx(25201.0, now_s=1000.1), [])[1] == "entry pending"
    # the screen print is 0.05 s old at the trigger: at 1000.1 it is 0.15 s old, i.e. BEFORE the trigger -> wait
    pos, why = paper.try_fill_entry(b, _held(25201.0, 1000.1, ltp=150.0, age=0.15))
    assert pos is None and why.startswith("entry pending")
    # a print that arrived 0.1 s ago at 1000.4 (= after the trigger at 1000.0) fills, at ITS price
    pos, why = paper.try_fill_entry(b, _held(25201.0, 1000.4, ltp=153.0, age=0.1))
    assert pos and pos["entry"] == 153.0 and pos["trigger_ltp"] == 150.0 and pos["fill_slip"] == 3.0
    assert pos["fill_delay_s"] == 0.4 and pos["trigger_time"] == "10:00:00" and "pending_entry" not in b.ctl
    assert pos["dir"] == 1 and pos["ep_type"] == "SPOT-BREAKOUT"


def test_entry_lapses_without_a_print_and_in_a_gap():
    b = _book()
    c = _ctx(25201.0, now_s=1000.0)
    assert paper.evaluate_entry(b, c, [])[0]
    paper.request_entry(b, c, _q(150.0), "t")
    pos, why = paper.try_fill_entry(b, _held(25201.0, 1000.0 + config.ENTRY_FILL_MAX_S + 0.1, ltp=150.0, age=9.0))
    assert pos is None and why.startswith("entry lapsed") and "pending_entry" not in b.ctl and "dir" not in b.ctl
    assert paper.evaluate_entry(b, _ctx(25202.0, now_s=1004.0), [])[0]           # free to trigger again
    paper.request_entry(b, _ctx(25202.0, now_s=1004.0), _q(150.0), "t")
    pos, why = paper.try_fill_entry(b, _held(25202.0, 1004.2, ltp=150.0, age=0.1, blackout={"on": True, "why": "feed silent"}))
    assert pos is None and "data gap" in why and "pending_entry" not in b.ctl


def test_entry_pending_does_not_outlive_the_entry_window():
    b = _book()
    late = datetime(2026, 10, 21, config.LAST_ENTRY[0], config.LAST_ENTRY[1] - 1, 59, tzinfo=config.IST)
    c = _ctx(25201.0, now_s=1000.0, now_dt=late)
    assert paper.evaluate_entry(b, c, [])[0]
    paper.request_entry(b, c, _q(150.0), "t")
    after = datetime(2026, 10, 21, config.LAST_ENTRY[0], config.LAST_ENTRY[1], 0, tzinfo=config.IST)
    pos, why = paper.try_fill_entry(b, _held(25201.0, 1001.0, ltp=150.0, age=0.1, now_dt=after))
    assert pos is None and why.startswith("entry lapsed")


# ── D-126 exits ────────────────────────────────────────────────────────────────
def test_exit_fills_on_the_first_print_after_the_trigger_not_the_screen_print():
    b = _book()
    _open(b)                                                    # entry 150.5, spot_in 25201
    assert paper.check_exit(b, _held(25230.0, 1010.0, ltp=170.0)) is None     # best 25230
    # spot snaps back 12 pts in one step: the trigger fires but the screen print (170, 0.1 s old) predates it
    t = paper.check_exit(b, _held(25218.0, 1020.0, ltp=170.0, age=0.1))
    assert t is None and b.pos["pending"]["reason"] == "TRAIL" and b.pos["pending"]["trigger_px"] == 170.0
    # 0.1 s later still no new print (age 0.2 > 0.1 waited): wait; the reason stays committed even if spot bounces
    assert paper.check_exit(b, _held(25225.0, 1020.1, ltp=170.0, age=0.2)) is None
    assert b.pos["pending"]["reason"] == "TRAIL"
    # a print arrives (age 0.05 < 0.3 waited): filled at THAT price
    t = paper.check_exit(b, _held(25225.0, 1020.3, ltp=158.0, age=0.05))
    assert t and t["reason"] == "TRAIL" and t["exit"] == 158.0 and t["exit_trigger_px"] == 170.0 and t["fill_delay_s"] == 0.3
    assert not t.get("stale_exit")


def test_exit_without_any_print_falls_back_after_the_deferral_limit_and_is_flagged():
    b = _book()
    _open(b)
    paper.check_exit(b, _held(25230.0, 1010.0, ltp=170.0))
    assert paper.check_exit(b, _held(25218.0, 1020.0, ltp=170.0, age=0.1)) is None
    assert paper.check_exit(b, _held(25218.0, 1020.0 + config.EXIT_DEFER_MAX_S - 0.1, ltp=170.0, age=9.95)) is None
    t = paper.check_exit(b, _held(25218.0, 1020.0 + config.EXIT_DEFER_MAX_S, ltp=170.0, age=10.0))
    assert t and t["stale_exit"] is True and t["exit"] == 170.0


def test_timed_exits_do_not_wait():
    b = _book()
    _open(b)
    t = paper.check_exit(b, _held(25205.0, 2000.0, ltp=152.0, age=0.3, now_dt=T_FLAT))
    assert t and t["reason"].startswith("TIME") and t["exit"] == 152.0


# ── D-127 the lock ─────────────────────────────────────────────────────────────
def test_lock_params_registered_and_sane():
    p = config.VARIANTS["spot_dc12_t12"]
    assert p["lock_pct"] == config.LOCK_PCT == 18.0 and p["lock_trail_pct"] == config.LOCK_TRAIL_PCT == 10.0
    assert config.VARIANTS["spot_dc12_t12_nolock"]["lock_pct"] == 0.0
    assert config.validate() == []
    bad = dict(config.VARIANTS["spot_dc12_t12"], lock_trail_pct=30.0)
    config.VARIANTS["_bad"] = bad
    try:
        assert any("lock_trail_pct" in x for x in config.validate())
    finally:
        del config.VARIANTS["_bad"]


def _exit_now(b, sp, s, ltp, age=0.1):
    """Trigger and then fill on the next print at the same price (two steps, D-126)."""
    t = paper.check_exit(b, _held(sp, s, ltp=ltp, age=age))
    if t is None and b.pos and b.pos.get("pending"):
        t = paper.check_exit(b, _held(sp, s + 0.3, ltp=ltp, age=0.05))
    return t


def test_lock_arms_at_plus_18_and_exits_10_pct_off_the_best():
    b = _book()
    _open(b)                                                    # entry 150.5
    assert paper.check_exit(b, _held(25210.0, 1010.0, ltp=170.0)) is None     # +13 %: not armed
    assert not b.pos.get("lock_armed") and b.pos["best_prem"] == 170.0 and b.pos.get("lock_floor") is None
    assert paper.check_exit(b, _held(25215.0, 1020.0, ltp=178.0)) is None     # +18.3 %: armed
    assert b.pos["lock_armed"] and b.pos["lock_armed_at"] == "10:00:00" and b.pos["lock_floor"] == 160.2
    assert paper.check_exit(b, _held(25220.0, 1030.0, ltp=190.0)) is None     # best 190, floor 171
    assert b.pos["lock_floor"] == 171.0
    assert paper.check_exit(b, _held(25219.0, 1040.0, ltp=171.5)) is None     # 9.7 % off: holds
    t = _exit_now(b, 25219.0, 1050.0, 171.0)                                  # 10 % off the best: LOCK
    assert t and t["reason"].startswith("LOCK (171.00 fell 10.0 % from best 190.00; armed +18 % at 10:00:00)"), t["reason"]
    assert t["exit"] == 171.0 and t["ret_pct"] > 13


def test_lock_never_fires_before_arming_and_the_spot_trail_still_rules():
    b = _book()
    _open(b)
    assert paper.check_exit(b, _held(25210.0, 1010.0, ltp=175.0)) is None     # +16 %, best 175
    assert paper.check_exit(b, _held(25210.0, 1020.0, ltp=150.0)) is None     # -14 % off the best but NOT armed
    t = _exit_now(b, 25197.0, 1030.0, 140.0)                                  # 13 below the best spot: TRAIL/STOP
    assert t and t["reason"].startswith("TRAIL") and "locked" not in t["reason"]


def test_trail_exit_after_arming_is_labelled_locked():
    b = _book()
    _open(b)
    assert paper.check_exit(b, _held(25230.0, 1010.0, ltp=180.0)) is None     # armed (+19.6 %)
    assert b.pos["lock_armed"]
    t = _exit_now(b, 25218.0, 1020.0, 175.0)                                  # spot trail fires first
    assert t and t["reason"].startswith("TRAIL (locked +18 % at 10:00:00)"), t["reason"]


def test_lock_ignores_stale_prints_and_blackout():
    b = _book()
    _open(b)
    assert paper.check_exit(b, _held(25230.0, 1010.0, ltp=180.0)) is None
    assert paper.check_exit(b, _held(25230.0, 1020.0, ltp=300.0, age=7.0)) is None   # stale print: best stays 180
    assert b.pos["best_prem"] == 180.0
    assert paper.check_exit(b, _held(25230.0, 1030.0, ltp=100.0, blackout={"on": True, "why": "x"})) is None
    assert b.pos["best_prem"] == 180.0 and not b.pos.get("pending")


def test_lock_survives_a_restart_and_the_nolock_twin_has_none():
    b = _book()
    _open(b)
    assert paper.check_exit(b, _held(25230.0, 1010.0, ltp=180.0)) is None
    b2 = paper.Book.from_json(b.to_json())
    assert b2.pos["lock_armed"] and b2.pos["best_prem"] == 180.0
    t = _exit_now(b2, 25230.0, 1020.0, 162.0)
    assert t and t["reason"].startswith("LOCK")
    n = paper.Book("spot_dc12_t12_nolock", dict(config.VARIANTS["spot_dc12_t12_nolock"], retest_ext=0.0), "2026-10-21")   # first-touch, no lock
    _open(n)
    assert paper.check_exit(n, _held(25230.0, 1010.0, ltp=180.0)) is None
    assert not n.pos.get("lock_armed")
    assert paper.check_exit(n, _held(25230.0, 1020.0, ltp=150.0)) is None   # 16.7 % off the best: nothing


def test_csv_has_the_lock_and_fill_columns():
    import csv
    b = _book()
    _open(b)
    paper.check_exit(b, _held(25230.0, 1010.0, ltp=180.0))
    t = _exit_now(b, 25230.0, 1020.0, 162.0)
    assert t
    path = paper.write_trades_csv(b, "2026-10-21")
    rows = list(csv.reader(open(path, encoding="utf-8")))
    for col in ("lock_armed", "lock_armed_at", "lock_floor", "best_prem", "trigger_ltp", "fill_delay_s", "fill_slip", "exit_trigger_px"):
        assert col in rows[0], col


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
