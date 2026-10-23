"""Council 4 (19 Oct evening): the spot-breakout books (D-116). python tests/test_c4.py  (numpy only)."""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c4_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False   # D-126: these suites test the exit/entry logic itself on same-step fills; D-126 has its own suite
from apex.engine import paper  # noqa: E402

T_NORMAL = datetime(2026, 10, 21, 10, 0, tzinfo=config.IST)      # not an expiry day
T_EXP_LATE = datetime(2026, 10, 19, 11, 45, tzinfo=config.IST)   # expiry day, after 11:30
OPT = {"id": 5, "key": "NIFTY|OPT|2026-10-27|25150|CE", "strike": 25150, "rr": "CE", "expiry": "2026-10-27",
       "ltp": 150.0, "bid": 149.9, "ask": 150.1, "delta": 0.7, "iv": 14.0, "age": 0.1, "week": 0, "ltt": None}


def _ctx(spot, hi=25200.0, lo=25150.0, now_s=1000.0, now_dt=T_NORMAL, w0="2026-10-27", **kw):
    c = {"now_s": now_s, "now_dt": now_dt, "w0": w0, "spot": spot, "spot_hi": hi, "spot_lo": lo,
         "fut": spot + 10, "fut_ltp": spot + 10, "advisors": {}, "blackout": {"on": False},
         "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
         "episode": None, "regime": {"state": "RANGE", "dir": None}}       # a RANGE regime: this book is not gated
    c.update(kw)
    return c


def _book(name="spot_dc12_t12_first"):     # D-131: the first-touch twin; the retest champion is covered in test_c6_retest.py
    return paper.Book(name, config.VARIANTS[name], "2026-10-21")


def test_registered_and_valid():
    for n in ("spot_dc12_t12", "spot_dc12_t12_1130"):
        v = config.VARIANTS[n]
        assert v["spot_dc"] == 720 and v["spot_trail"] == 12.0 and n not in config.CONTROLS
    assert config.VARIANTS["spot_dc12_t12_1130"]["spot_expiry_end"] == (11, 30)
    assert config.validate() == []


def test_entry_on_a_break_of_the_spot_range_either_way():
    b = _book()
    assert not paper.evaluate_entry(b, _ctx(25180.0), [])[0]                 # inside the range
    ok, why = paper.evaluate_entry(b, _ctx(25201.0), [])
    assert ok and "high" in why and paper.entry_dir(b, _ctx(25201.0)) == 1
    b2 = _book()
    ok, why = paper.evaluate_entry(b2, _ctx(25149.0), [])
    assert ok and "low" in why and b2.ctl["dir"] == -1
    assert "warming" in paper.evaluate_entry(_book(), _ctx(25201.0, hi=None, lo=None), [])[1]


def test_spot_trail_exit_and_one_trade_per_swing():
    b = _book()
    c = _ctx(25201.0)
    assert paper.evaluate_entry(b, c, [])[0]
    paper.open_trade(b, c, dict(OPT), "t")
    assert b.pos["spot_in"] == 25201.0
    q = dict(OPT, ltp=160.0)
    held = lambda sp, s: dict(_ctx(sp, now_s=s), by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1)   # noqa: E731
    assert paper.check_exit(b, held(25230.0, 1010.0)) is None                # best 25230
    assert paper.check_exit(b, held(25219.0, 1020.0)) is None                # 11 below best: hold
    t = paper.check_exit(b, held(25218.0, 1030.0))                           # 12 below best: trail
    assert t and t["reason"] == "TRAIL" and b.ctl["swing_last"] == {"d": 1, "best": 25230.0}
    # same direction again needs spot beyond 25230, even though 25225 is above the 12-min high
    ok, why = paper.evaluate_entry(b, _ctx(25225.0, now_s=1040.0), [])
    assert not ok and "same swing" in why
    assert paper.evaluate_entry(b, _ctx(25231.0, now_s=1041.0), [])[0]
    # D-122: only the LAST trade's swing counts — after a PE trade, a CE at 25225 is a fresh swing
    b.ctl["swing_last"] = {"d": -1, "best": 25100.0}
    b.pos = None
    assert paper.evaluate_entry(b, _ctx(25225.0, now_s=1042.0), [])[0]
    # no cool-down for this book: the other way is allowed at once
    b3 = _book(); b3.last_exit_s = 1039.0
    assert paper.evaluate_entry(b3, _ctx(25149.0, now_s=1040.0), [])[0]


def test_initial_stop_is_the_trail_from_entry():
    b = _book()
    c = _ctx(25201.0)
    paper.evaluate_entry(b, c, [])
    paper.open_trade(b, c, dict(OPT), "t")
    q = dict(OPT, ltp=140.0)
    t = paper.check_exit(b, dict(_ctx(25189.0, now_s=1010.0), by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1))
    assert t and t["reason"] == "STOP"


def test_expiry_day_end_for_the_1130_book_only():
    late = _ctx(25201.0, now_dt=T_EXP_LATE, w0="2026-10-19")
    ok, why = paper.evaluate_entry(_book("spot_dc12_t12_1130"), late, [])
    assert not ok and "11:30" in why
    assert paper.evaluate_entry(_book("spot_dc12_t12_first"), late, [])[0]


def test_no_brake_by_default_and_never_a_streak_stop_for_the_spot_book():
    b = _book()
    b.capital = config.START_CAPITAL * 0.80                                   # D-123: no daily stop unless the owner sets one
    assert paper.evaluate_entry(b, _ctx(25201.0), [])[0]
    b2 = _book()
    b2.trades = [{"ret_pct": -3.0, "t_out": 990.0}] * 4
    old = config.LOSS_STREAK_N
    config.LOSS_STREAK_N = 3                                                   # even when the owner turns it on, this book opts out
    try:
        assert paper.evaluate_entry(b2, _ctx(25201.0), [])[0]
    finally:
        config.LOSS_STREAK_N = old


def test_acceptance_catches_19oct_failure_modes_and_passes_a_clean_day():
    from apex import acceptance
    t = lambda ti, to, r, **k: dict({"time_in": ti, "time_out": to, "ret_pct": r, "hold_s": 120,  # noqa: E731
                                    "expiry": "2026-10-21", "capital_after": 100000.0}, **k)
    clean = {"m2.0_s0.5": {"p": config.VARIANTS["m2.0_s0.5"], "capital": 101000.0,
                           "trades": [t("10:00:00", "10:02:00", 1.0), t("10:30:00", "10:33:00", -1.0)]}}
    f, _ = acceptance.check_books(clean, "2026-10-21", "m2.0_s0.5", "2026-10-28")
    assert f == [], f
    churn = {"m2.0_s0.5": {"p": config.VARIANTS["m2.0_s0.5"], "capital": 48000.0,
                           "trades": [t("12:53:%02d" % i, "12:53:%02d" % (i + 1), -2.0, hold_s=20) for i in range(0, 50, 7)]}}
    f, _ = acceptance.check_books(churn, "2026-10-21", "m2.0_s0.5", "2026-10-28")
    assert any("entries within" in x for x in f) and any("re-entered" in x for x in f) and any("median hold" in x for x in f)
    frozen = {"m2.0_s0.5": {"p": config.VARIANTS["m2.0_s0.5"], "capital": 100000.0,
                            "trades": [t("09:44:11", "09:44:34", 0.0, trade_age_in=237851.0, trade_age_out=237860.0)]}}
    f, _ = acceptance.check_books(frozen, "2026-10-21", "m2.0_s0.5", "2026-10-28")
    assert any("stale quote" in x for x in f)
    exp = {"m2.0_s0.5": {"p": config.VARIANTS["m2.0_s0.5"], "capital": 100000.0,
                         "trades": [t("13:04:38", "13:06:00", 1.0, expiry="2026-10-27")]}}
    f, _ = acceptance.check_books(exp, "2026-10-19", "m2.0_s0.5", "2026-10-19")
    assert any("expiry day" in x for x in f) and not any("expiry entry end" in x for x in f)   # D-123: no 11:30 rule by default
    old = config.EXPIRY_ENTRY_END
    config.EXPIRY_ENTRY_END = (11, 30)
    try:
        f, _ = acceptance.check_books(exp, "2026-10-19", "m2.0_s0.5", "2026-10-19")
        assert any("expiry entry end" in x for x in f)
    finally:
        config.EXPIRY_ENTRY_END = old


def test_d121_fade_switch_follows_in_range_fades_in_chop_and_exits_on_a_bracket():
    b = _book("fade_switch")
    dom = lambda r: {"dir": 1, "z": 0.0, "r15": r, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0}  # noqa: E731
    assert "warming" in paper.evaluate_entry(b, _ctx(25180.0, domino=dom(12.0)), [])[1]          # no range15 yet
    assert not paper.evaluate_entry(b, _ctx(25180.0, domino=dom(9.0), range15=80.0), [])[0]       # move too small
    ok, why = paper.evaluate_entry(b, _ctx(25180.0, domino=dom(12.0), range15=80.0), [])
    assert ok and "follow" in why and paper.entry_dir(b, _ctx(25180.0)) == 1                      # wide range: follow
    b2 = _book("fade_switch")
    ok, why = paper.evaluate_entry(b2, _ctx(25180.0, domino=dom(12.0), range15=40.0), [])
    assert ok and "fade" in why and paper.entry_dir(b2, _ctx(25180.0)) == -1                      # chop: fade
    # bracket on the futures: +12 target, -12 stop, 180-s hold limit; no regime gate (ctx regime is RANGE)
    c = _ctx(25180.0, now_s=1000.0)                                                               # fut = 25190
    paper.open_trade(b, c, dict(OPT), "t")
    q = dict(OPT, ltp=160.0)
    held = lambda sp, s: dict(_ctx(sp, now_s=s), by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1)   # noqa: E731
    assert paper.check_exit(b, held(25191.0, 1010.0)) is None
    t = paper.check_exit(b, held(25192.0, 1020.0))                                                # fut 25202 = +12
    assert t and t["reason"] == "TARGET"
    assert paper.evaluate_entry(b, _ctx(25180.0, now_s=1050.0, domino=dom(12.0), range15=80.0), [])[1].startswith("cool-down")
    paper.open_trade(b, _ctx(25180.0, now_s=1100.0), dict(OPT), "t")
    assert paper.check_exit(b, held(25169.0, 1200.0)) is None                                    # -11
    t = paper.check_exit(b, held(25168.0, 1210.0))
    assert t and t["reason"] == "STOP"
    paper.open_trade(b, _ctx(25180.0, now_s=2000.0), dict(OPT), "t")
    assert paper.check_exit(b, held(25182.0, 2179.0)) is None
    t = paper.check_exit(b, held(25182.0, 2180.0))
    assert t and t["reason"] == "HOLD-LIMIT"


def test_d124_owner_champion_is_applied_once_to_the_stored_state():
    from apex.engine import learning
    import json
    st = learning._default_state()
    st["champion"], st["champion_since"] = "m2.0_s0.5", "2026-10-17"      # what the PC's state.json holds
    st["streak"] = {"m1.5_s0.4": 1}
    st.pop("owner_champion", None)
    os.makedirs(config.LEARN_DIR, exist_ok=True)
    with open(learning.STATE, "w", encoding="utf-8") as f:
        json.dump(st, f)
    s1 = learning.load_state()
    own, since = config.CHAMPION_OWNER                                      # D-134: spot_pb45 since 21 Oct (was spot_dc12_t12)
    assert s1["champion"] == own and s1["champion_since"] == since and s1["streak"] == {}
    assert s1["log"][-1]["event"] == "champion" and s1["log"][-1]["by"].startswith("owner")
    assert json.load(open(learning.STATE, encoding="utf-8"))["champion"] == own      # saved at once
    # the learning loop may later change the champion on evidence; the owner's choice is not re-applied
    s1["champion"] = "m1.5_s0.4"
    learning.save_state(s1)
    assert learning.load_state()["champion"] == "m1.5_s0.4"
    os.remove(learning.STATE)
    assert learning.load_state()["champion"] == config.CHAMPION_DEFAULT                            # fresh state too


def test_d124_restart_keeps_the_swing_mark_and_the_cool_down():
    b = _book()
    b.ctl["swing_last"] = {"d": 1, "best": 25230.0}
    b.last_exit_s = 1030.0
    b2 = paper.Book.from_json(b.to_json())
    assert b2.ctl["swing_last"] == {"d": 1, "best": 25230.0} and b2.last_exit_s == 1030.0
    assert not paper.evaluate_entry(b2, _ctx(25225.0, now_s=1040.0), [])[0]                       # same swing survives
    assert paper.evaluate_entry(b2, _ctx(25231.0, now_s=1041.0), [])[0]


def test_d124_a_stale_spot_quote_neither_enters_nor_exits():
    b = _book()
    ok, why = paper.evaluate_entry(b, _ctx(25201.0, spot_age=6.0), [])
    assert not ok and why.startswith("spot quote 6 s old")
    assert paper.evaluate_entry(b, _ctx(25201.0, spot_age=4.0), [])[0]
    c = _ctx(25201.0)
    paper.open_trade(b, c, dict(OPT), "t")
    q = dict(OPT, ltp=140.0)
    held = lambda sp, s, age: dict(_ctx(sp, now_s=s), by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1, spot_age=age)  # noqa: E731
    assert paper.check_exit(b, held(25150.0, 1010.0, 30.0)) is None        # 51 pts against, but spot is 30 s old: wait
    t = paper.check_exit(b, held(25150.0, 1011.0, 0.5))
    assert t and t["reason"] == "STOP"


def test_d124_acceptance_limits_follow_the_champion_kind():
    from apex import acceptance
    t = lambda tin, tout, ret, **k: dict({"time_in": tin, "time_out": tout, "ret_pct": ret, "hold_s": 20.0, "trade_age_in": 0.3,   # noqa: E731
                                          "trade_age_out": 0.3, "expiry": "2026-10-27", "capital_after": 100000.0}, **k)
    tr = [t(f"10:{m:02d}:00", f"10:{m:02d}:20", 1.0) for m in range(0, 28, 4)]                     # 7 entries in 28 min
    books = {"spot_dc12_t12": {"p": config.VARIANTS["spot_dc12_t12"], "capital": 100000.0, "trades": tr}}
    f, _ = acceptance.check_books(books, "2026-10-21", "spot_dc12_t12", "2026-10-27")
    assert f == [], f
    books = {"m2.0_s0.5": {"p": config.VARIANTS["m2.0_s0.5"], "capital": 100000.0, "trades": tr}}
    f, _ = acceptance.check_books(books, "2026-10-21", "m2.0_s0.5", "2026-10-27")
    assert any("entries within" in x for x in f) and any("median hold" in x for x in f)


def test_d124_frozen_index_falls_back_to_a_futures_stop():
    b = _book()
    c = _ctx(25201.0)
    paper.open_trade(b, c, dict(OPT), "t")                        # fut_in = 25211 (spot + 10)
    q = dict(OPT, ltp=130.0)
    held = lambda sp, fut, s, age: dict(_ctx(sp, now_s=s, fut=fut, fut_mid=fut), by_id={5: q}, by_key={OPT["key"]: q},  # noqa: E731
                                        fut_age=0.1, spot_age=age)
    # spot frozen at 25201 for 2 min while the futures fell 12: the futures stop takes over
    assert paper.check_exit(b, held(25201.0, 25200.0, 1100.0, 120.0)) is None     # -11 on the futures: hold
    t = paper.check_exit(b, held(25201.0, 25199.0, 1101.0, 120.0))
    assert t and t["reason"].startswith("STOP (futures: spot quote 120 s old")
    # a fresh index keeps the spot trail as the only stop
    b2 = _book()
    paper.open_trade(b2, _ctx(25201.0), dict(OPT), "t")
    assert paper.check_exit(b2, held(25201.0, 25150.0, 1100.0, 1.0)) is None      # futures -61, spot unchanged: hold


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
