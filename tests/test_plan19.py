"""Plan after the first live day (docs/09, D-110 … D-115): python tests/test_plan19.py  (numpy only)."""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_plan19_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

import numpy as np  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False   # D-126: these suites test the exit/entry logic itself on same-step fills; D-126 has its own suite
from apex.engine import diagnostics, learning, paper  # noqa: E402
from apex.engine.market import Market  # noqa: E402
from apex.table import ROW_DTYPE  # noqa: E402

T0 = datetime(2026, 10, 21, 11, 0, tzinfo=config.IST)
OPT = {"id": 5, "key": "NIFTY|OPT|2026-10-27|25150|CE", "strike": 25150, "rr": "CE", "expiry": "2026-10-27",
       "ltp": 150.0, "bid": 149.9, "ask": 150.1, "delta": 0.6, "iv": 14.0, "age": 0.1, "week": 0, "ltt": None}


def _entry_ctx(now_s=1000.0, d=1, **kw):
    ctx = {"now_s": now_s, "now_dt": T0, "fut": 25220.0, "fut_ltp": 25222.0, "advisors": {},
           "blackout": {"on": False},
           "domino": {"dir": d, "z": 3.0 * d, "r15": 25.0 * d, "S_up": 0.8 if d > 0 else 0.0,
                      "S_dn": 0.8 if d < 0 else 0.0, "S_up_nv": 0.9, "S_dn_nv": 0.9, "sigma15": 8.0, "gap": 0.0},
           "episode": {"id": 77, "dir": d, "type": "BASKET-LED", "fut0": 25210.0, "first": "HDFCBANK", "gap": False},
           "iv_rise_since_onset": 0.2, "regime": {"state": "DIRECTIONAL", "dir": d, "text": "directional"},
           "trend30": 40.0 * d, "range5": 30.0}
    ctx.update(kw)
    return ctx


def test_d110_market_price_of_the_future_is_the_mid():
    m = Market()
    m.mid_rows = (0,)
    snap = np.zeros(config.MAX_ROWS, dtype=ROW_DTYPE)
    snap["ltp"][0], snap["bid"][0], snap["ask"][0] = 25212.0, 25200.0, 25206.0    # print at the far side
    snap["ltp"][1], snap["bid"][1], snap["ask"][1] = 100.0, 99.0, 101.0           # any other row: untouched
    m.push(snap, 1.0)
    assert m.ltp[0, m.k] == 25203.0 and m.ltp[1, m.k] == 100.0
    assert snap["ltp"][0] == 25212.0                                              # the caller's copy is not mutated
    snap["bid"][0], snap["ask"][0] = 25150.0, 25250.0                             # a 100-pt quote: not a mid
    m.push(snap, 1.1)
    assert m.ltp[0, m.k] == 25212.0
    snap["bid"][0] = 0.0                                                          # one-sided
    m.push(snap, 1.2)
    assert m.ltp[0, m.k] == 25212.0


def test_d111_sigma_floor():
    assert config.SIGMA15_FLOOR >= 5.0
    import inspect
    from apex.engine import domino
    assert "SIGMA15_FLOOR" in inspect.getsource(domino.Domino.update)


def test_d112_regime_gate_blocks_unclear_markets_for_real_books_only():
    b = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-21")
    for st in config.REGIME_BLOCK:
        ok, why = paper.evaluate_entry(b, _entry_ctx(regime={"state": st, "dir": None, "text": st.lower()}), [])
        assert not ok and why.startswith("gate regime"), (st, why)
    ok, why = paper.evaluate_entry(b, _entry_ctx(regime={"state": "DIRECTIONAL", "dir": -1, "text": "directional ↓"}), [])
    assert not ok and "other way" in why
    ok, why = paper.evaluate_entry(b, _entry_ctx(), [])
    assert ok, why
    raw = paper.Book("RAW", config.VARIANTS["m2.0_s0.5"], "2026-10-21")            # RAW: ungated by design
    assert paper.evaluate_entry(raw, _entry_ctx(regime={"state": "RANGE", "dir": None}), [])[0]
    fo = paper.Book("futures_only", config.VARIANTS["futures_only"], "2026-10-21")  # controls: exempt
    assert paper.base_gate(fo, _entry_ctx(regime={"state": "RANGE"}), 1) == ""
    sp = paper.Book("straddle_spike", config.VARIANTS["straddle_spike"], "2026-10-21")
    assert paper.base_gate(sp, _entry_ctx(regime={"state": "BREAKOUT", "dir": 1}), -1).endswith("the other way")


def _with(**kw):
    """Run a test with brake numbers set (D-123: they are OFF by default; the owner turns them on)."""
    import contextlib

    @contextlib.contextmanager
    def cm():
        old = {k: getattr(config, k) for k in kw}
        for k, v in kw.items():
            setattr(config, k, v)
        try:
            yield
        finally:
            for k, v in old.items():
                setattr(config, k, v)
    return cm()


def test_d123_brakes_are_off_by_default():
    assert config.DAILY_LOSS_STOP_PCT == 0 and config.LOSS_STREAK_N == 0
    assert config.MAX_ENTRIES_PER_DAY == 0 and config.EXPIRY_ENTRY_END is None
    b = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-19")
    b.capital = 10_000.0
    b.trades = [{"ret_pct": -3.0, "t_out": 900.0}] * 10
    late = _entry_ctx(now_dt=datetime(2026, 10, 19, 14, 0, tzinfo=config.IST), w0="2026-10-19")
    assert paper._daily_brake(b, late) == ""


def test_d113_daily_stop_and_losing_streak_pause_when_the_owner_turns_them_on():
    b = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-21")
    with _with(DAILY_LOSS_STOP_PCT=15.0, LOSS_STREAK_N=3, LOSS_STREAK_PAUSE_S=0, MAX_ENTRIES_PER_DAY=6):
        b.capital = config.START_CAPITAL * (1 - 15.0 / 100.0) - 1
        ok, why = paper.evaluate_entry(b, _entry_ctx(), [])
        assert not ok and why.startswith("DAILY STOP")
        b.capital = config.START_CAPITAL
        b.trades = [{"ret_pct": -3.0, "t_out": 900.0}] * 3
        ok, why = paper.evaluate_entry(b, _entry_ctx(now_s=1000.0), [])
        assert not ok and "losses in a row" in why                                  # D-117: stopped for the day
        ok, why = paper.evaluate_entry(b, _entry_ctx(now_s=900.0 + 3600), [])
        assert not ok and "losses in a row" in why
        b.trades[-1] = {"ret_pct": 2.0, "t_out": 900.0}                                # a win breaks the streak
        assert paper.evaluate_entry(b, _entry_ctx(now_s=1000.0), [])[0]
        b.trades = [{"ret_pct": 1.0, "t_out": 900.0}] * 6                              # D-117 entry cap
        ok, why = paper.evaluate_entry(b, _entry_ctx(now_s=1000.0), [])
        assert not ok and "entries taken" in why
        ctl = paper.Book("futures_only", config.VARIANTS["futures_only"], "2026-10-21")
        ctl.capital = 10_000.0
        assert paper._daily_brake(ctl, _entry_ctx()) == ""


def test_d117_expiry_entry_end_and_kill_switch():
    b = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-19")
    late = _entry_ctx(now_dt=datetime(2026, 10, 19, 11, 31, tzinfo=config.IST), w0="2026-10-19")
    with _with(EXPIRY_ENTRY_END=(11, 30)):
        ok, why = paper.evaluate_entry(b, late, [])
        assert not ok and "11:30" in why
    assert paper.evaluate_entry(b, late, [])[0]                                     # off by default (D-123)
    open(config.KILL_FILE, "w").close()
    try:
        ok, why = paper.evaluate_entry(b, _entry_ctx(), [])
        assert not ok and why.startswith("KILL")
    finally:
        os.remove(config.KILL_FILE)
    assert paper.evaluate_entry(b, _entry_ctx(), [])[0]


def test_d118_shadow_books():
    assert config.VARIANTS["m2.0_s0.5_d20"]["d_star"] == 20.0
    v = config.VARIANTS["m2.0_s0.5_tvfast"]
    b = paper.Book("m2.0_s0.5_tvfast", v, "2026-10-21")
    ctx = _entry_ctx()
    paper.open_trade(b, ctx, dict(OPT), "t")
    q = dict(OPT, ltp=151.0, age=0.1)
    flip = dict(ctx, by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1,
                domino={"S_up": 0.0, "S_dn": 0.0, "S_up_nv": 0.0, "S_dn_nv": 0.35, "z": -1.5, "sigma15": 5.0})
    assert paper.check_exit(b, dict(flip, now_s=1001.0)) is None
    t = paper.check_exit(b, dict(flip, now_s=1002.1))
    assert t and t["reason"].startswith("THESIS-VOID")


def test_d114_trend_variant():
    v = config.VARIANTS["m2.0_s0.5_trend"]
    assert v["trend"] and v["m_star"] == 2.0 and v["s_star"] == 0.5 and "m2.0_s0.5_trend" not in config.CONTROLS
    b = paper.Book("m2.0_s0.5_trend", v, "2026-10-21")
    assert "not ready" in paper.evaluate_entry(b, _entry_ctx(trend30=None), [])[1]
    ok, why = paper.evaluate_entry(b, _entry_ctx(trend30=-60.0), [])
    assert not ok and why.startswith("trend:")
    assert paper.evaluate_entry(b, _entry_ctx(trend30=+60.0), [])[0]
    champ = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-21")
    assert paper.evaluate_entry(champ, _entry_ctx(trend30=-60.0), [])[0]          # the champion ignores trend


def test_d115_signal_recorded_on_the_trade_and_in_the_learning_record():
    b = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-21")
    ctx = _entry_ctx()
    paper.open_trade(b, ctx, dict(OPT), "t")
    sg = b.pos["signal"]
    assert sg["r15"] == 25.0 and sg["z"] == 3.0 and sg["trend30"] == 40.0 and sg["regime"] == "DIRECTIONAL"
    assert sg["fut_mid"] == 25220.0 and sg["fut_ltp"] == 25222.0
    t = paper.close_trade(b, dict(ctx, now_s=1100.0), 155.0, "TRAIL", dict(OPT, ltp=155.0))
    assert t["signal"] == sg and t["t_out"] == 1100.0
    learning.record_day("2026-10-21", {"m2.0_s0.5": b})
    rows = [r for r in learning._read_days_rows()[0] if r["book"] == "m2.0_s0.5"]
    assert rows and rows[0]["trades"][0]["signal"]["z"] == 3.0


def test_new_reasons_have_their_own_class():
    rc = lambda w: diagnostics.reason_class({"decision_at_cross": w, "fired": False})   # noqa: E731
    assert rc("DAILY STOP: book is -16.0 % on the day (limit -15 %)") == "daily stop"
    assert rc("pause: 3 losses in a row, 12 min left") == "loss pause"
    assert rc("gate regime: range (efficiency 0.10)") == "regime says no"
    assert rc("impulse 9 pts < 15 pt floor") == "impulse too small"
    assert rc("trend: 30-min move -40 pts is not with the UP impulse") == "against trend"
    assert rc("cool-down: 40 s after the last exit") == "cool-down"


def test_config_still_valid():
    assert config.validate() == []
    assert config.START_CAPITAL == 100_000.0                                     # fresh ₹1,00,000 every day


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
