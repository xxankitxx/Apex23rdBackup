"""Closing Auction Session test (D-094): python tests/test_cas.py  (numpy only)."""
import json
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_cas_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False   # D-126: these suites test the exit/entry logic itself on same-step fills; D-126 has its own suite
from apex.engine import learning, paper  # noqa: E402


def _dt(h, m, s=0):
    return datetime(2026, 10, 21, h, m, s, tzinfo=config.IST)


def test_clock_is_the_cas_test_clock_and_validates():
    assert config.MARKET_CLOSE == (15, 40)          # NSE F&O close since 3 Aug 2026
    assert config.LAST_ENTRY == (15, 29) and config.FLATTEN_AT == (15, 35) and config.CAS_TEST
    assert config.validate() == []


def test_reverting_the_test_is_two_lines_and_still_validates():
    old = (config.LAST_ENTRY, config.FLATTEN_AT, config.CAS_TEST)
    try:
        config.LAST_ENTRY, config.FLATTEN_AT, config.CAS_TEST = (15, 15), (15, 25), False
        assert config.validate() == []
        config.CAS_TEST = True                       # the flag must follow the clock
        assert any("CAS_TEST" in b for b in config.validate())
    finally:
        config.LAST_ENTRY, config.FLATTEN_AT, config.CAS_TEST = old


def test_session_phases():
    want = [((9, 0), "PRE"), ((9, 15), "CTS"), ((15, 14, 59), "CTS"), ((15, 15), "CAS-ENTRY"),
            ((15, 29, 59), "CAS-ENTRY"), ((15, 30), "CAS-MATCH"), ((15, 35), "POST"), ((15, 40), "CLOSED")]
    for t, ph in want:
        assert config.session_phase(_dt(*t)) == ph, (t, ph)


def test_entry_window_runs_to_1529_and_flatten_at_1535():
    b = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-21")
    ctx = {"domino": {"dir": 1}, "episode": None, "advisors": {}, "blackout": {"on": False}}
    assert paper.evaluate_entry(b, dict(ctx, now_dt=_dt(15, 28, 59)), [])[1] != "outside entry window"
    assert paper.evaluate_entry(b, dict(ctx, now_dt=_dt(15, 29)), [])[1] == "outside entry window"
    opt = {"id": 5, "key": "k", "strike": 25150, "rr": "CE", "expiry": "2026-10-27", "ltp": 150.0}
    c = {"now_s": 0, "now_dt": _dt(15, 20), "fut": 25200.0, "advisors": {},
         "episode": {"id": 1, "dir": 1, "type": "BASKET-LED"}}
    paper.open_trade(b, c, opt, "t")
    assert b.pos["phase_in"] == "CAS-ENTRY"
    q = dict(opt, ltp=151.0, age=0.1)
    base = dict(c, by_id={5: q}, by_key={"k": q}, domino={"S_up": 0, "S_dn": 0, "z": 0}, fut_age=0.1)
    assert paper.check_exit(b, dict(base, now_dt=_dt(15, 34, 59), now_s=100)) is None
    t = paper.check_exit(b, dict(base, now_dt=_dt(15, 35), now_s=200))
    assert t and t["reason"] == "TIME (15:35 flatten)" and t["phase_out"] == "POST"


def test_cas_trades_kept_on_file_but_not_evidence():
    tr = lambda ti, ph, r: {"pnl_pts": r, "pnl_rs": r, "ret_pct": r, "reason": "STOP", "time_in": ti, "phase_in": ph}
    rows = [{"day": "2026-10-21", "book": "m2.0_s0.5",
             "trades": [tr("10:00:00", "CTS", 5.0), tr("15:20:00", "CAS-ENTRY", -40.0),
                        {"pnl_pts": 1, "pnl_rs": 1, "ret_pct": 2.0, "reason": "TIME", "time_in": "15:16:00"}]}]
    os.makedirs(os.path.dirname(learning.DAYS), exist_ok=True)
    with open(learning.DAYS, "w") as f:
        f.write("\n".join(json.dumps(r) for r in rows) + "\n")
    ev = learning._load_days()["m2.0_s0.5"]["2026-10-21"]
    assert [t["ret_pct"] for t in ev] == [5.0]          # legacy row without phase_in: by time_in
    allr = learning._load_days(include_cas=True)["m2.0_s0.5"]["2026-10-21"]
    assert len(allr) == 3
    lines = "\n".join(learning.cas_lines(learning._load_days(include_cas=True)))
    assert "study only" in lines and "| m2.0_s0.5 | 2 |" in lines


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
