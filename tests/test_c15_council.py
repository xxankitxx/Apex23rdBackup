"""30 Oct (D-145): council books — c20_9x champion, c20_8x shadow, run through apex/engine/council.Adapter."""
import importlib

from apex import config


def test_council_books_registered_and_champion():
    assert config.CHAMPION_DEFAULT == "c20_9x" and config.CHAMPION_OWNER == ("c20_9x", "2026-10-30")
    for n in ("c20_8x", "c20_9x"):
        assert config.VARIANTS[n]["council"] == n
        assert n not in config.CONTROLS
    assert "council" in config.VARIANT_KEYS and config.validate() == []
    assert "t28_gap" in config.VARIANTS                # yesterday's champion stays as a shadow


def test_council_strategies_import_and_build():
    for n in ("c20_8x", "c20_9x"):
        m = importlib.import_module(f"apex.engine.council.{n}")
        s = m.Strategy()
        assert hasattr(s, "on_second")
    m = importlib.import_module("apex.engine.council.c20_9x")
    assert set(("l2", "ffirst", "seqcal", "catch", "dtr", "ramp", "ivz", "ptre", "tie")) <= set(m.FINAL_R9)


def test_live_day_shapes():
    from apex.engine import council
    D = council.LiveDay("2026-10-30", "2026-11-03")
    assert D.bid.shape == (council.N_ROWS, council.MAXC) and not D.dte0
    assert abs(D.hm[0] - 555.0) < 1e-9


# ── 30 Oct review: the adapter fills like every other book (D-126) and never reads a wrong column ─────────────────
import os
import tempfile
from datetime import datetime, timedelta

from apex.engine import council, paper

DAY, W0 = "2026-10-30", "2026-11-03"
T0 = datetime(2026, 10, 30, 9, 15, tzinfo=config.IST)
KEY = f"NIFTY|OPT|{W0}|25000|CE"


class _Eng:
    fwd, _fwd_t, greek, m = 25010.0, None, {}, None


def _opt(ltp, age, now_s):
    return {"id": 7, "key": KEY, "strike": 25000, "rr": "CE", "expiry": W0, "ltp": ltp, "bid": ltp - 0.5,
            "ask": ltp + 0.5, "delta": 0.6, "gamma": 0.001, "theta_min": -0.2, "iv": 14.0, "age": age, "ltt": None}


def _ctx(sec, ltp=150.0, age=0.1, blackout=False):
    dt = T0 + timedelta(seconds=sec)
    now_s = dt.timestamp()
    o = _opt(ltp, age, now_s)
    return {"now_s": now_s, "now_dt": dt, "w0": W0, "spot": 25000.0, "fut": 25010.0, "fut_mid": 25010.0,
            "fut_ltp": 25010.0, "advisors": {}, "blackout": {"on": blackout}, "episode": None,
            "regime": {"state": "RANGE", "dir": None}, "fut_age": 0.1, "spot_age": 0.3,
            "options": [o], "by_key": {KEY: o}, "by_id": {7: o}}


class _Script:
    """a stand-in strategy: BUY at second `buy`, SELL at second `sell`; records what it was shown"""
    def __init__(self, buy, sell):
        self.buy, self.sell, self.seen = buy, sell, []

    def on_second(self, i, D, pos):
        self.seen.append((i, None if pos is None else dict(pos)))
        if i == self.buy and pos is None:
            return ("BUY", 25000, "CE", "NORM pb v=+9")
        if i == self.sell and pos is not None:
            return ("SELL", "FWD_TRAIL")
        return None


def _adapter(buy, sell):
    os.environ.setdefault("APEX_DATA", tempfile.mkdtemp(prefix="apex_test_c15_"))
    eng = _Eng()
    eng._fwd_t = T0.timestamp()
    a = council.Adapter("c20_9x", DAY, W0)
    a.strat = _Script(buy, sell)
    b = paper.Book("c20_9x", config.VARIANTS["c20_9x"], DAY)
    return eng, a, b


def test_entry_and_exit_wait_for_the_first_print_after_the_trigger():
    assert config.FILL_NEXT_PRINT
    eng, a, b = _adapter(buy=100, sell=400)
    for s in range(98, 100):
        a.step(eng, b, _ctx(s))
    c = _ctx(100, ltp=150.0, age=0.3)
    eng._fwd_t = c["now_s"]
    assert a.step(eng, b, c) is False and b.pos is None and b.ctl.get("pending_entry")   # trigger second: no fill
    c = _ctx(101, ltp=151.0, age=2.0)                 # a print OLDER than the trigger: still waiting
    eng._fwd_t = c["now_s"]
    assert a.step(eng, b, c) is False and b.pos is None
    c = _ctx(102, ltp=152.0, age=0.4)                 # first print after the trigger -> filled at ITS price
    eng._fwd_t = c["now_s"]
    assert a.step(eng, b, c) is True and b.pos and b.pos["entry"] == 152.0 and b.pos["entry_ask"] == 152.5
    assert b.pos["ep_type"] == "COUNCIL" and b.pos["trigger_ltp"] == 150.0
    assert all(p is None for _, p in a.strat.seen)   # the strategy was not stepped while the fill was pending
    for s in range(103, 400):
        c = _ctx(s, ltp=170.0, age=0.2)
        eng._fwd_t = c["now_s"]
        a.step(eng, b, c)
    assert b.pos["peak_bid"] == 169.5                  # saved on the position
    c = _ctx(400, ltp=165.0, age=0.2)
    eng._fwd_t = c["now_s"]
    assert a.step(eng, b, c) is False and b.pos and b.pos["pending"]["reason"] == "COUNCIL FWD_TRAIL"
    c = _ctx(401, ltp=163.0, age=5.0)                 # stale print: wait
    eng._fwd_t = c["now_s"]
    assert a.step(eng, b, c) is False and b.pos
    c = _ctx(402, ltp=161.0, age=0.3)                 # first print after the exit trigger
    eng._fwd_t = c["now_s"]
    assert a.step(eng, b, c) is True and b.pos is None
    t = b.trades[-1]
    assert t["exit"] == 161.0 and t["exit_bid"] == 160.5 and t["exit_trigger_px"] == 165.0 and t["fill_delay_s"] == 2.0
    assert not t.get("stale_exit")


def test_exit_falls_back_to_the_last_price_after_the_defer_limit():
    eng, a, b = _adapter(buy=10, sell=20)
    c = _ctx(10); eng._fwd_t = c["now_s"]; a.step(eng, b, c)
    c = _ctx(11, ltp=150.0, age=0.2); eng._fwd_t = c["now_s"]; assert a.step(eng, b, c)
    for s in range(12, 20):
        c = _ctx(s, ltp=150.0, age=0.2); eng._fwd_t = c["now_s"]; a.step(eng, b, c)
    c = _ctx(20, ltp=140.0, age=0.2); eng._fwd_t = c["now_s"]
    assert a.step(eng, b, c) is False and b.pos["pending"]
    for s in range(21, 31):                           # no fresh print for 10 s
        c = _ctx(s, ltp=140.0, age=30.0); eng._fwd_t = c["now_s"]
        done = a.step(eng, b, c)
        if b.pos is None:
            break
    assert b.pos is None and b.trades[-1]["stale_exit"] and b.trades[-1]["exit"] == 140.0


def test_forced_flat_fills_at_once_and_a_missing_column_skips_the_strategy():
    eng, a, b = _adapter(buy=10, sell=10 ** 9)
    c = _ctx(10); eng._fwd_t = c["now_s"]; a.step(eng, b, c)
    c = _ctx(11, age=0.2); eng._fwd_t = c["now_s"]; assert a.step(eng, b, c) and b.pos
    # the held contract drops out of the chain this second: the strategy must not see column 0's quote
    a.D.col.pop((25000, "CE"))
    n = len(a.strat.seen)
    c = _ctx(12, age=0.2); c["options"] = []; eng._fwd_t = c["now_s"]
    assert a.step(eng, b, c) is False and len(a.strat.seen) == n and b.pos
    # 15:20 on a normal day: TIME exit, filled this second even on an old print
    sec = (15 * 60 + 20 - 555) * 60
    c = _ctx(sec, ltp=120.0, age=4.0); eng._fwd_t = c["now_s"]
    assert a.step(eng, b, c) is True and b.pos is None and b.trades[-1]["reason"].startswith("TIME")


def test_peak_bid_survives_a_new_adapter():
    eng, a, b = _adapter(buy=10, sell=10 ** 9)
    c = _ctx(10); eng._fwd_t = c["now_s"]; a.step(eng, b, c)
    c = _ctx(11, age=0.2); eng._fwd_t = c["now_s"]; a.step(eng, b, c)
    c = _ctx(12, ltp=200.0, age=0.2); eng._fwd_t = c["now_s"]; a.step(eng, b, c)
    assert b.pos["peak_bid"] == 199.5
    a2 = council.Adapter("c20_9x", DAY, W0)           # an engine restart: fresh adapter, same saved position
    a2.strat = _Script(10 ** 9, 10 ** 9)
    c = _ctx(13, ltp=150.0, age=0.2); eng._fwd_t = c["now_s"]; a2.step(eng, b, c)
    assert a2.strat.seen[-1][1]["peak_bid"] == 199.5
