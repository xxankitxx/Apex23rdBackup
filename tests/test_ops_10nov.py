"""10 Nov: the operational faults of the 9 Nov live session, each pinned by a test (docs/39).

1. the engine stood still for seconds and nothing said where the time went      -> per-phase accounting, SLOW TICK line
2. the supervisor stayed silent (every pause was under its 10-s limit)          -> pause report
3. a second Ctrl+C killed the engine inside its stop save                       -> the second press is ignored
4. the day was stopped at 15:32 and was neither closed nor learned              -> a flat book after 15:25 closes the day
5. the logs carried a time and no date                                          -> dated lines
(the save cache and the saver have their own tests in test_save_fast.py)"""
import json
import os
import re
import time
from datetime import datetime

from apex import config, engine_main
from apex.engine import paper

import run_apex


# ── supervisor ──────────────────────────────────────────────────────────────────
def test_pause_under_the_stale_limit_is_reported_when_the_heartbeat_resumes():
    st, s = {}, 10 ** 9
    hb = 1000 * s
    assert run_apex.pause_report(st, hb + s // 2, hb) is None              # first sight
    for k in range(1, 8):                                                 # the heartbeat stands still for 7 s
        assert run_apex.pause_report(st, hb + k * s, hb) is None
    hb2 = hb + 8 * s
    p = run_apex.pause_report(st, hb2 + s // 10, hb2)                      # it moves again: the pause is reported once
    assert p is not None and 6.5 < p < 8.5
    assert run_apex.pause_report(st, hb2 + s, hb2) is None
    hb3 = hb2 + 2 * s
    assert run_apex.pause_report(st, hb3, hb3) is None                    # a normal 2-s gap is nothing
    assert run_apex.pause_report({}, 5 * s, 0) is None                    # never beaten: stale_report's business
    assert run_apex.PAUSE_S < run_apex.STALE_S


class _Proc:
    """Runs until `stops_after` seconds; poll() raises KeyboardInterrupt at the given poll numbers (a Ctrl+C)."""

    def __init__(self, stops_after, ctrl_c_at=()):
        self.t0, self.after, self.n, self.at = time.time(), stops_after, 0, set(ctrl_c_at)
        self.terminated, self.returncode = False, None

    def poll(self):
        if self.terminated or (self.after is not None and time.time() - self.t0 >= self.after):
            self.returncode = 0
            return 0
        self.n += 1
        if self.n in self.at:
            raise KeyboardInterrupt
        return None

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminated = True


def test_second_ctrl_c_does_not_kill_an_engine_that_is_still_saving():
    msgs = []
    eng = _Proc(0.9, ctrl_c_at=(2,))                                      # one more Ctrl+C while the engine saves
    procs = {"feed": _Proc(0.0), "engine": eng, "gateway": _Proc(None)}
    run_apex.stop_children(procs, msgs.append, feed_s=0.2, engine_s=5.0)
    assert not eng.terminated and eng.returncode == 0, "the engine was killed inside its stop save"
    assert len(msgs) == 1 and "Ctrl+C ignored" in msgs[0] and "ENGINE" in msgs[0]
    assert procs["gateway"].terminated


def test_third_ctrl_c_forces_and_says_so():
    msgs = []
    eng = _Proc(None, ctrl_c_at=(2, 4))
    run_apex.stop_children({"feed": _Proc(0.0), "engine": eng}, msgs.append, feed_s=0.2, engine_s=30.0)
    assert eng.terminated and "Ctrl+C ignored" in msgs[0] and "terminating without waiting" in msgs[1]
    assert run_apex.ENGINE_STOP_S >= 120.0                                # the stop now also closes and learns the day


def test_ctrl_c_while_the_feed_stops_still_leaves_the_engine_its_time():
    msgs = []
    eng = _Proc(1.0)
    run_apex.stop_children({"feed": _Proc(None, ctrl_c_at=(2,)), "engine": eng}, msgs.append, feed_s=0.4, engine_s=5.0)
    assert not eng.terminated and "the FEED is still stopping" in msgs[0]


# ── dated log lines ─────────────────────────────────────────────────────────────
def test_every_log_line_carries_the_date(tmp_path):
    p = tmp_path / "engine.log"
    old = engine_main.LOG
    engine_main.LOG = open(p, "w", encoding="utf-8")
    try:
        engine_main.log("probe")
    finally:
        engine_main.LOG.close()
        engine_main.LOG = old
    line = p.read_text(encoding="utf-8")
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line) and "ENGINE probe" in line and "ENGINE ENGINE" not in line
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for f in ("run_apex.py", "apex/feed_breeze.py", "apex/feed_replay.py", "apex/feed_sim.py", "apex/gateway.py"):
        src = open(os.path.join(root, f), encoding="utf-8").read()
        assert "%Y-%m-%d %H:%M:%S" in src, f


# ── the engine's account of its own time ────────────────────────────────────────
def _live(tag, day="2026-10-21"):
    from tests import test_wp2
    rig = test_wp2.Rig(tag, day)
    rig.warm()
    live = engine_main.Engine(rig.t, rig.blob, "live")
    live.load_registry()
    live.start_day(day)
    rig.eng = live
    return rig, live


def test_slow_tick_is_logged_at_once_with_the_phase_that_took_the_time(tmp_path, monkeypatch):
    rig, live = _live("prof")
    lines = []
    monkeypatch.setattr(engine_main, "log", lines.append)
    try:
        for _ in range(3):
            rig.now += 0.1; rig.write(25210.0)
            t0 = time.perf_counter()
            assert live.tick()
            live._loop_stat((time.perf_counter() - t0) * 1000.0)
        assert not [x for x in lines if "SLOW TICK" in x]
        real = live.run_books

        def slow_books(ctx):
            time.sleep(0.12)
            return real(ctx)
        live.run_books = slow_books
        monkeypatch.setattr(engine_main.Engine, "SLOW_TICK_MS", 100.0)
        rig.now += 0.1; rig.write(25210.0)
        t0 = time.perf_counter()
        assert live.tick()
        live._loop_stat((time.perf_counter() - t0) * 1000.0)
        slow = [x for x in lines if "SLOW TICK" in x]
        assert len(slow) == 1 and re.search(r"step parts \(ms\): books 1\d\d", slow[0]), slow
        assert "save lag 0" in slow[0]
        # the minute: one log line (always, in a live session), one perf record, and the state for the dashboard
        lp = live._lp
        assert lp["slow"] == 1 and len(lp["xs"]) == 4 and lp["ph"]["step:books"] > 0.1
        assert abs(sum(v for k, v in lp["ph"].items() if k.startswith("step:")) * 1000.0 - sum(lp["xs"])) < 0.5 * sum(lp["xs"])
        live._perf_minute(lp, True, True)
        minute = [x for x in lines if x.startswith("tick time last minute")]
        assert len(minute) == 1 and "over 1 s: 1" in minute[0] and "books" in minute[0] and "save lag" in minute[0]
        assert live.perf["n"] == 4 and live.perf["laps"][0][0] == "books" and live.perf["save"]["errors"] is not None
        rec = [json.loads(x) for x in open(os.path.join(config.LOG_DIR, "perf_2026-10-21.jsonl"), encoding="utf-8")][-1]
        assert rec["n"] == 4 and rec["ph"]["step:books"][1] > 100.0 and "save" in rec
        live.publish()
        assert live.ctx["step_gap"] > 0
    finally:
        rig.close()


def test_stopped_flat_after_the_flatten_time_closes_and_learns_the_day(monkeypatch):
    rig, live = _live("stop")
    lines = []
    monkeypatch.setattr(engine_main, "log", lines.append)
    try:
        rig.now += 0.1; rig.write(25210.0)
        assert live.tick()
        day = datetime.fromisoformat("2026-10-21T15:32:53").replace(tzinfo=config.IST)
        live.now_dt = day.replace(hour=14, minute=0)
        assert not live.day_is_over()                                      # mid-session: the day stays open
        live.now_dt = day                                                  # 9 Nov: stopped at 15:32:53, every book flat
        assert all(b.pos is None for b in live.books.values()) and live.day_is_over()
        b = next(iter(live.books.values()))
        b.pos = {"key": "K", "entry": 1.0, "qty": 65, "t_in": 1.0, "dir": 1}
        assert not live.day_is_over()                                      # a book still in a trade: not over
        b.pos = None
        live.now_dt = day.replace(hour=15, minute=41)
        assert live.day_is_over()
        live.now_dt = day
        closed = []
        monkeypatch.setattr(live, "end_day", lambda: closed.append(live.day))
        live.stop_path()
        assert closed == ["2026-10-21"]
        text = "\n".join(lines)
        assert "stop requested: saving the books" in text and "stop: books saved" in text
        assert "stop: closing and learning day 2026-10-21" in text and lines[-1].startswith("stopped (")
        assert os.path.exists(os.path.join(config.PAPER_DIR, "2026-10-21.json"))
        assert not os.path.exists(os.path.join(config.PAPER_DIR, "2026-10-21.json.tmp.sync"))
    finally:
        rig.close()


def test_torn_tmp_of_a_killed_run_is_removed_and_logged_at_the_next_start(monkeypatch):
    from tests import test_wp2
    torn = os.path.join(config.PAPER_DIR, "2026-10-20.json.tmp")
    with open(torn, "w") as f:
        f.write('{"c20_9x": {"name": "c20_9x", "trades": [{"key"')
    os.utime(torn, (time.time() - 7200, time.time() - 7200))
    lines = []
    monkeypatch.setattr(engine_main, "log", lines.append)
    rig = test_wp2.Rig("torn", "2026-10-21")
    try:
        rig.step(25210.0, 2)
        assert not os.path.exists(torn)
        assert any("removed a leftover temporary books file 2026-10-20.json.tmp" in x for x in lines)
    finally:
        rig.close()


def test_the_live_feed_and_engine_run_above_normal_priority_and_nothing_else_does(monkeypatch):
    """10 Nov (docs/41): replays and research on the same machine slowed the engine step 3 to 4 times."""
    import subprocess
    seen = []
    monkeypatch.setattr(run_apex.subprocess, "Popen", lambda cmd, **kw: seen.append((cmd[2], kw.get("creationflags"))) or None)
    for mode, mod in (("live", "apex.feed_breeze"), ("live", "apex.engine_main"), ("live", "apex.gateway"),
                      ("replay", "apex.engine_main"), ("sim", "apex.feed_sim")):
        run_apex.spawn(mod, [], mode, data_dir=os.environ.get("APEX_DATA") or ".")
    hi = getattr(subprocess, "ABOVE_NORMAL_PRIORITY_CLASS", 0)
    assert seen == [("apex.feed_breeze", hi), ("apex.engine_main", hi), ("apex.gateway", 0), ("apex.engine_main", 0),
                    ("apex.feed_sim", 0)]
    assert isinstance(run_apex.busy_python(), list)                          # never raises

