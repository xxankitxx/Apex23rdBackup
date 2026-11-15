"""15 Nov (owner: "Yes, fix them"): the live-path defects that the reviewer brief's surveys confirmed in older code
(docs/62 sections 4, 5, 9, 16; docs/61 section 6).

1. the parity forward's reference is the GUARDED index (a rejected index print could replace a sound forward);
2. a day that fails to start is not a started day: the engine refuses to run and retries;
3. the close is marked done only after the day's record is on disk, and a failed close is retried;
4. "no futures and no index price" is said while it lasts (it was a silent state with no exit checks);
5. an unreadable pool file is reported by the configuration check and said at the day's start;
6. the configuration check runs at every live start, not only in the optional preflight command;
7. the supervisor restarts a hung engine, backs off in a crash loop, and can read the process list again.
"""
import os
import sys
import time
import types

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config, engine_main, greeks  # noqa: E402
from apex.engine import conductor as cond  # noqa: E402

import run_apex  # noqa: E402


# ── 1. the forward's reference ──────────────────────────────────────────────────
def test_the_forward_reference_is_the_trusted_index_else_the_future():
    ref = engine_main.forward_ref
    assert ref(25010.0, 25060.0, "") == 25010.0                      # a trusted index: as before
    assert ref(25511.0, 25060.0, "spot is +501 pts off") == 25060.0  # a rejected print: the future
    assert ref(float("nan"), 25060.0, "") == 25060.0                 # no index yet: the future, as before
    assert np.isnan(ref(25511.0, float("nan"), "bad")) and np.isnan(ref(float("nan"), float("nan"), ""))


def test_a_rejected_index_print_no_longer_replaces_a_sound_parity_forward():
    """The hazard itself: synthetic_forward returns its reference when parity is more than 150 points from it."""
    F, T = 25055.0, 2.0 / 365.0
    K = np.arange(24400.0, 25701.0, 50.0)
    ce = greeks.b76_price(F, K, T, 0.12, np.ones(len(K), bool))
    pe = greeks.b76_price(F, K, T, 0.12, np.zeros(len(K), bool))
    bad_index = 25010.0 + 501.0                                      # the vendor index has printed this
    assert greeks.synthetic_forward(K, ce, pe, bad_index) == bad_index          # what the engine used to feed in
    good = greeks.synthetic_forward(K, ce, pe, engine_main.forward_ref(bad_index, 25060.0, "off its usual spread"))
    assert abs(good - F) < 0.5                                       # with the guarded reference: the real forward


# ── the engine on its rig (2, 3, 4) ─────────────────────────────────────────────
def _engine(tag, day="2026-10-21"):
    from tests import test_wp2
    rig = test_wp2.Rig(tag, day)
    rig.warm()
    live = engine_main.Engine(rig.t, rig.blob, "live")
    live.load_registry()
    rig.eng = live
    return rig, live


def test_a_day_that_fails_to_start_is_not_started_and_nothing_trades_until_it_does(monkeypatch):
    rig, live = _engine("lp1")
    lines = []
    monkeypatch.setattr(engine_main, "log", lines.append)
    try:
        monkeypatch.setattr(engine_main.weather_mod, "static_check", lambda: ["item 7 is missing"])
        rig.now += 0.1; rig.write(25210.0)
        hb0 = int(rig.t.c("engine_hb_ns"))
        assert live.tick_nopublish() is False                         # the start raises: no heartbeat
        assert live.day is None and live.books == {} and int(rig.t.c("engine_hb_ns")) == hb0
        assert any("refusing to run" in x for x in lines)
        n0 = len(lines)
        for _ in range(5):                                            # inside the retry wait: refused, said once, no traceback
            rig.now += 0.1; rig.write(25210.0)
            assert live.tick_nopublish() is False
        said = [x for x in lines[n0:] if "ENGINE NOT RUNNING" in x]
        assert len(said) == 1 and "item 7 is missing" in said[0] and not any("Traceback" in x for x in lines[n0:])
        try:
            live.step()
            raise AssertionError("the step must refuse")
        except engine_main.DayNotStarted:
            pass
        monkeypatch.setattr(engine_main.weather_mod, "static_check", lambda: [])   # the cause is fixed
        live._start_fail = (live._start_fail[0], time.monotonic() - 1.0, live._start_fail[2])   # the wait is over
        rig.now += 0.1; rig.write(25210.0)
        assert live.tick_nopublish() is True and live.day == "2026-10-21" and live.books and live._start_fail is None
        assert int(rig.t.c("engine_hb_ns")) > hb0 and getattr(live, "ledger", None) is not None
    finally:
        rig.close()


def test_the_close_is_marked_done_only_after_the_record_is_written_and_is_retried(monkeypatch):
    rig, live = _engine("lp2")
    lines = []
    monkeypatch.setattr(engine_main, "log", lines.append)
    try:
        rig.now += 0.1; rig.write(25210.0)
        assert live.tick_nopublish()
        calls = {"n": 0}
        real = engine_main.learning.record_day

        def flaky(day, books):
            calls["n"] += 1
            if calls["n"] == 1:
                raise PermissionError("days.jsonl is locked")
            return real(day, books)
        monkeypatch.setattr(engine_main.learning, "record_day", flaky)
        monkeypatch.setattr(engine_main.learning, "already_learned", lambda day: True)   # the learning step is not under test
        live.end_day()                                                # the first attempt fails: logged, NOT marked done
        assert calls["n"] == 1 and getattr(live, "_learned", "") != live.day
        assert any("attempt 1 of 5 failed" in x and "retried in 30 s" in x for x in lines)
        live.end_day()                                                # inside the wait: not tried again yet
        assert calls["n"] == 1
        live.end_day(force=True)                                      # the stop path: one more try, now
        assert calls["n"] == 2 and live._learned == live.day
        live.end_day(force=True)                                      # done is done
        assert calls["n"] == 2
        assert engine_main.END_DAY_TRIES == 5 and engine_main.END_DAY_RETRY_S == 30.0
    finally:
        rig.close()


def test_no_price_at_all_is_said_not_silent(monkeypatch):
    rig, live = _engine("lp3")
    lines = []
    monkeypatch.setattr(engine_main, "log", lines.append)
    try:
        rig.now += 0.1; rig.write(25210.0)
        assert live.tick_nopublish()
        ran = {"n": 0}
        real = live.run_books
        live.run_books = lambda ctx: (ran.__setitem__("n", ran["n"] + 1), real(ctx))[1]
        monkeypatch.setattr(live, "px", lambda i: float("nan"))       # the feed restarted: the table has no price yet
        for _ in range(3):
            rig.now += 0.1; rig.write(25210.0)
            live.step()
        said = [x for x in lines if "no futures and no index price" in x]
        assert ran["n"] == 0 and len(said) == 1, (ran, said)          # no book stepped; said once a minute, not every step
        assert any("no futures and no index price" in e["x"] for e in live.events)
    finally:
        rig.close()


# ── 5. the pool file ────────────────────────────────────────────────────────────
def test_an_unreadable_pool_file_is_reported_not_read_as_an_empty_pool(tmp_path, monkeypatch):
    p = tmp_path / "pool.json"
    p.write_text('{"entries": [', encoding="utf-8")                   # torn
    pool = cond.load_pool(str(p))
    assert pool["entries"] == [] and "error" in pool
    probs = cond.pool_problems(pool)
    assert len(probs) == 1 and "unreadable" in probs[0]
    assert "error" in cond.load_pool(str(tmp_path / "missing.json"))
    p.write_text("[1, 2]", encoding="utf-8")                          # readable JSON, not a pool
    assert "error" in cond.load_pool(str(p))
    assert "error" not in cond.load_pool() and cond.pool_problems(cond.load_pool()) == []   # the shipped pool is sound
    monkeypatch.setattr(cond, "load_pool", lambda *a, **k: pool)
    assert any("pool.json" in x and "unreadable" in x for x in config.validate())          # the config check now sees it
    c = cond.Conductor("2026-11-16", list(config.VARIANTS), pool=pool, log_dir="")
    assert c.members == [] and c.reason == "pool empty"


# ── 6. the configuration check at a live start ──────────────────────────────────
def test_live_does_not_start_on_a_configuration_problem():
    said = []
    assert run_apex.config_gate(validate=lambda: [], env={}, out=said.append) is True and said == []
    assert run_apex.config_gate(validate=lambda: ["pool.json: the file is unreadable"], env={}, out=said.append) is False
    assert any("pool.json" in x for x in said) and any("Not starting" in x for x in said)
    said.clear()
    assert run_apex.config_gate(validate=lambda: ["x"], env={"APEX_ALLOW_BAD_CONFIG": "1"}, out=said.append) is True
    assert any("starting anyway" in x for x in said)

    def boom():
        raise RuntimeError("cannot import")
    assert run_apex.config_gate(validate=boom, env={}, out=said.append) is False          # a failed check is not a pass
    assert run_apex.config_gate(env={}, out=said.append) is True                           # the shipped configuration passes


# ── 7. the supervisor ───────────────────────────────────────────────────────────
def test_a_hung_engine_is_restarted_and_a_crash_loop_backs_off():
    s = 10 ** 9
    spawned, now = 1000 * s, 2000 * s
    hung = run_apex.engine_hung
    assert hung(now, now - 119 * s, spawned) is None                  # under two minutes: only the STALE warning
    assert hung(now, now - 120 * s, spawned) == 120.0                 # beat after its start, then stood still: hung
    assert hung(now, 0, spawned) is None and hung(now, spawned - 5 * s, spawned) is None   # never beat since ITS start
    assert hung(now, spawned, spawned) is None
    assert run_apex.ENGINE_HUNG_S == 120.0 and run_apex.ENGINE_HUNG_S > run_apex.STALE_S
    w = run_apex.engine_wait
    assert [w(n) for n in (1, 2, 3, 12, 13, 99)] == [0.0, 5.0, 10.0, 55.0, 60.0, 60.0]


def test_the_process_list_is_read_by_powershell_and_unknown_is_not_nothing():
    out = "1234|py -3.13 -m apex.replay_batch tapes\n77|C:\\Python\\python.exe run_apex.py live\n\nnot a row\n4|\n"
    assert run_apex.parse_ps_processes(out) == [(1234, "py -3.13 -m apex.replay_batch tapes"),
                                                (77, "C:\\Python\\python.exe run_apex.py live"), (4, "")]
    assert run_apex.parse_wmic_processes("Node,CommandLine,ProcessId\nPC,py a,b.py,55\n") == [(55, "py a,b.py")]
    calls = []

    def ok(cmd, **k):
        calls.append(cmd[0])
        return types.SimpleNamespace(returncode=0, stdout=out)
    rows = run_apex.busy_python(own_pids={4}, run=ok)
    assert rows == [(1234, "py -3.13 -m apex.replay_batch tapes")] and calls == ["powershell"]   # own and supervisor rows dropped

    def none(cmd, **k):
        raise FileNotFoundError(cmd[0])
    assert run_apex.busy_python(run=none) is None                     # neither tool: "could not look", never "nothing runs"

    def only_wmic(cmd, **k):
        if cmd[0] == "powershell":
            raise FileNotFoundError("powershell")
        return types.SimpleNamespace(returncode=0, stdout="Node,CommandLine,ProcessId\nPC,pytest tests,901\n")
    assert run_apex.busy_python(run=only_wmic) == [(901, "pytest tests")]


# ── 8. the fill rule stays the owner's (last traded price); its cost is recorded every evening ─────────
def test_the_nightly_record_carries_each_trade_at_the_ask_and_the_bid():
    from apex.engine import learning as L
    assert L._net_pct({"entry_ask": 100.0, "exit_bid": 110.0}) == 10.0
    assert L._net_pct({"entry_ask": None, "exit_bid": 110.0}) is None and L._net_pct({"entry_ask": 0.0, "exit_bid": 5.0}) is None
    assert L._net_pct({}) is None
    days = {"conductor": {"2026-11-16": [{"ret_pct": 10.0, "net_pct": 9.0}, {"ret_pct": -5.0, "net_pct": -5.5}],
                          "2026-11-13": [{"ret_pct": 3.0}]}}                      # an older row: no quotes recorded
    out = chr(10).join(L.net_lines(days, "conductor"))
    assert "| 2026-11-16 | 2 | 2 | +4.5 | +3.0 |" in out and "2026-11-13" not in out and "report only" in out
    assert L.net_lines({}, "conductor")[-1].startswith("No day with recorded quotes yet")
