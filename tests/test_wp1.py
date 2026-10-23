"""WP-1 checks (feed and tick tape): python tests/test_wp1.py  (numpy only)."""
import gzip
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config as _cfg  # noqa: E402
_cfg.REPLAY_LOCKSTEP = False      # these tests run the replay FEED alone, with no engine to step

import numpy as np  # noqa: E402

from apex import config  # noqa: E402
from apex import feed_core, feed_replay  # noqa: E402
from apex.feed_core import Recorder, Registry, apply_packet  # noqa: E402
from apex.table import Table  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = f"wp1_{os.getpid()}"


def _ticks_dir():
    """config.TICKS_DIR is the main data dir (not APEX_DATA): point it at a fresh temp dir."""
    d = tempfile.mkdtemp(prefix="apex_ticks_")
    config.TICKS_DIR = d
    return d


CRASHER = r'''
import os, sys, time
sys.path.insert(0, sys.argv[1])
os.environ["APEX_DATA"] = sys.argv[3]
from apex import config
config.TICKS_DIR = sys.argv[2]
from apex.feed_core import Recorder
rec = Recorder("2026-10-19")
for i in range(1000):
    rec.put("p", i, ["4.1!1", i])
time.sleep(1.6)                 # the writer flushes once a second: part of the data is on disk
for i in range(1000, 1200):
    rec.put("p", i, ["4.1!1", i])
time.sleep(0.05)
os._exit(1)                     # a crash: no gzip trailer, no closing meta
'''


def test_a_restart_writes_a_new_part_and_replay_reads_it():
    d = _ticks_dir()
    script = os.path.join(tempfile.mkdtemp(prefix="apex_crash_"), "crash.py")
    with open(script, "w") as f:
        f.write(CRASHER)
    subprocess.run([sys.executable, script, ROOT, d, os.environ["APEX_DATA"]], check=False, timeout=60)
    p1 = os.path.join(d, "2026-10-19.jsonl.gz")
    assert os.path.exists(p1)
    rec = Recorder("2026-10-19")
    assert rec.path == os.path.join(d, "2026-10-19.p2.jsonl.gz"), rec.path
    for i in range(1000):
        rec.put("p", 10_000 + i, ["4.1!1", i])
    rec.stop()
    assert sorted(os.listdir(d)) == ["2026-10-19.jsonl.gz", "2026-10-19.p2.jsonl.gz"]
    assert feed_replay.expand_parts(p1) == [p1, rec.path]
    got = {1: 0, 2: 0}
    for part, r in feed_replay.iter_records(p1):        # must not raise on the crashed part
        if r.get("k") == "p":
            got[part] += 1
    assert got[2] >= 1000, got
    assert got[1] >= 1, got                               # the crashed part is read up to the crash


def test_b_truncated_part_then_good_part_ends_done():
    d = _ticks_dir()
    p1 = os.path.join(d, "2026-10-20.jsonl.gz")
    reg = [dict(id=0, key="NIFTY|FUT", kind="fut", sym="NIFTY", token="4.1!35001", strike=0.0,
                right="", expiry="", depth=False, hero=False, seg="fo")]
    q = ["4.1!35001", 25000, 25210, 25300, 24990, 0.4, 25209, 75, 25211, 150, 75, 25100,
         14500000, 1000, 2000000, 4000, 5000, 0, "", 0, 0, 1760000000, 25100]
    lines = [json.dumps({"k": "reg", "t": 1_000_000_000, "d": reg})]
    lines += [json.dumps({"k": "p", "t": 1_000_000_000 + i, "d": q}) for i in range(3000)]
    raw = gzip.compress(("\n".join(lines) + "\n").encode())
    with open(p1, "wb") as f:
        f.write(raw[: len(raw) // 2])                     # cut mid-stream, like a killed writer
    with gzip.open(os.path.join(d, "2026-10-20.p2.jsonl.gz"), "wt", encoding="utf-8") as f:
        f.write(json.dumps({"k": "meta", "t": 5, "d": {"schema": 1, "part": 2}}) + "\n")
        f.write(json.dumps({"k": "reg", "t": 2_000_000_000, "d": reg}) + "\n")
        q2 = list(q); q2[2] = 25300.0
        f.write(json.dumps({"k": "p", "t": 2_000_000_001, "d": q2}) + "\n")
    name = f"t_{TAG}_b"
    t = Table(create=True, name=name)
    try:
        orig_sleep = feed_replay.time.sleep
        feed_replay.time.sleep = lambda s: None           # no real-time pacing in the test
        try:
            feed_replay.run(p1, 1000.0, table_name=name)
        finally:
            feed_replay.time.sleep = orig_sleep
        assert int(t.c("feed_state")) == 7
        assert float(t.rows["ltp"][0]) == 25300.0         # the good part was played
    finally:
        t.close(); t.unlink()


def test_b2_replay_sets_done_even_when_it_fails():
    name = f"t_{TAG}_b2"
    t = Table(create=True, name=name)
    try:
        orig = feed_replay.iter_records
        def boom(path):
            yield 1, {"k": "vix", "t": 1, "d": "not a number"}
        feed_replay.iter_records = boom
        orig_sleep = feed_replay.time.sleep
        feed_replay.time.sleep = lambda s: None
        try:
            try:
                feed_replay.run("x.jsonl.gz", 10.0, table_name=name)
            except ValueError:
                pass
        finally:
            feed_replay.iter_records = orig
            feed_replay.time.sleep = orig_sleep
        assert int(t.c("feed_state")) == 7
    finally:
        t.close(); t.unlink()


def test_c_meta_header_and_footer():
    d = _ticks_dir()
    rec = Recorder("2026-10-21", suffix="_sim")
    rec.put("p", 1, ["4.1!1"])
    rec.put("p", 2, ["4.1!1"])
    rec.stop()
    with gzip.open(os.path.join(d, "2026-10-21_sim.jsonl.gz"), "rt", encoding="utf-8") as f:
        rows = [json.loads(x) for x in f]
    h = rows[0]
    assert h["k"] == "meta"
    m = h["d"]
    assert m["schema"] == 1 and m["part"] == 1
    assert m["apex"] == __import__("apex").__version__
    assert "git" in m and (m["git"] is None or isinstance(m["git"], str))
    assert isinstance(m["cfg"], str) and len(m["cfg"]) == 40
    assert m["cfg"] == feed_core.config_hash()
    end = rows[-1]
    assert end["k"] == "meta" and end["d"]["dropped"] == 0 and end["d"]["lines"] == len(rows)
    assert [r["t"] for r in rows if r["k"] == "p"] == [1, 2]


def test_c2_recorder_never_appends():
    d = _ticks_dir()
    r1 = Recorder("2026-10-22"); r1.stop()
    r2 = Recorder("2026-10-22"); r2.stop()
    r3 = Recorder("2026-10-22"); r3.stop()
    assert [os.path.basename(r.path) for r in (r1, r2, r3)] == \
        ["2026-10-22.jsonl.gz", "2026-10-22.p2.jsonl.gz", "2026-10-22.p3.jsonl.gz"]
    with gzip.open(r1.path, "rt") as f:                 # part 1 holds only its own run
        assert sum(1 for _ in f) == 2
    assert feed_replay.expand_parts(r1.path) == [r1.path, r2.path, r3.path]
    assert d


def test_d_depth_level_none_keeps_seq_even():
    t = Table(create=True, name=f"t_{TAG}_d")
    try:
        reg = Registry()
        i = reg.add("NIFTY|FUT", "fut", "NIFTY", "4.1!35001", seg="fo")
        reg.by_token["fo"]["35001"] = i
        good = [25000, 75, 3, "", 25001, 50, 2, ""]
        pkt = ["4.2!35001", 1760000000, [good, None, [1, 2], good, "x"]]
        assert apply_packet(t, reg.by_token, pkt, 5) == i
        assert int(t.rows["seq"][i]) % 2 == 0
        assert float(t.rows["bpx"][i, 0]) == 25000.0 and float(t.rows["bpx"][i, 3]) == 25000.0
        assert np.isnan(t.rows["bpx"][i, 1]) and np.isnan(t.rows["bpx"][i, 2])
        assert np.isnan(t.rows["apx"][i, 4])
        assert int(t.rows["depth_ns"][i]) == 5

        class Boom:                                        # even a mid-write exception ends the row
            def __getitem__(self, k):
                raise RuntimeError("boom")
            def __len__(self):
                return 5
        try:
            apply_packet(t, reg.by_token, ["4.2!35001", 1, Boom()], 6)
        except Exception:
            pass
        assert int(t.rows["seq"][i]) % 2 == 0
    finally:
        t.close(); t.unlink()


def test_e_registry_add_stores_late_depth_token():
    reg = Registry()
    a = reg.add("NIFTY|OPT|x|25500|CE", "opt", "NIFTY", "4.1!1", depth=False, depth_token=None)
    b = reg.add("NIFTY|OPT|x|25500|CE", "opt", "NIFTY", "4.1!1", depth=True, depth_token="4.2!1")
    assert a == b
    it = reg.items[a]
    assert it["depth"] is True and it["depth_token"] == "4.2!1"
    reg.add("NIFTY|OPT|x|25500|CE", "opt", "NIFTY", "4.1!1", depth=True, depth_token="4.2!999")
    assert it["depth_token"] == "4.2!1"                   # an existing token is kept


def _fake_feed(chain_by_right, cache=None):
    from apex import feed_breeze

    class FakeTable:
        def __init__(self):
            self.v = {"chain_version": 0, "chain_ns": 0, "rest_today": 0}
        def c(self, k):
            return self.v.get(k, 0)
        def set(self, k, x):
            self.v[k] = x
        def now_ns(self):
            return time.time_ns()

    class FakeBreeze:
        def get_option_chain_quotes(self, right, **k):
            return chain_by_right[right]

    f = feed_breeze.BreezeFeed.__new__(feed_breeze.BreezeFeed)
    f.t = FakeTable()
    f.ledger = type("L", (), {"take": lambda self, cap=0: True})()
    f.rec = Recorder("x", enabled=False)
    f.breeze = FakeBreeze()
    f.reg = Registry()
    f.cache = cache or {"isec": {}, "index": {}, "fut_exp": {}}
    import datetime as _dt
    f.w0 = _dt.date(2026, 10, 19)
    return f


def test_f_partial_chain_not_published():
    rows = {"Success": [{"strike_price": str(25000 + 50 * k), "open_interest": "100"} for k in range(20)]}
    f = _fake_feed({"call": rows, "put": {}})
    f.poll_chain()
    assert f.t.c("chain_version") == 0
    f = _fake_feed({"call": rows, "put": {"Success": rows["Success"][:10]}})   # half the strikes
    f.poll_chain()
    assert f.t.c("chain_version") == 0
    f = _fake_feed({"call": rows, "put": rows})
    f.poll_chain()
    assert f.t.c("chain_version") == 1


def test_g_build_with_nothing_resolved_exits():
    from apex import feed_breeze
    f = _fake_feed({})

    class DeadBreeze:
        interval = ""
        def get_stock_token_value(self, **k):
            return ("4.1!False", "4.2!False")
        def get_names(self, **k):
            return {}
        def get_quotes(self, **k):
            return {"Success": [{"ltp": 25000}]}
    f.breeze = DeadBreeze()
    try:
        f.build()
    except SystemExit:
        pass
    else:
        raise AssertionError("build() accepted an empty security master")

    class FutOnly(DeadBreeze):                       # futures resolve, options do not
        def get_stock_token_value(self, product_type="", **k):
            return ("4.1!35001", None) if product_type == "futures" else ("4.1!False", None)
    f = _fake_feed({})
    f.breeze = FutOnly()
    try:
        f.build()
    except SystemExit as e:
        assert "weekly options" in str(e)
    else:
        raise AssertionError("build() accepted zero weekly options")
    assert feed_breeze


def test_h_snapshot_retries_a_row_held_odd():
    t = Table(create=True, name=f"t_{TAG}_h")
    stop = threading.Event()

    def writer():
        while not stop.is_set():
            t.begin(3)
            t.rows["ltp"][3] = 1.0
            time.sleep(0.001)                       # row odd for ~1 ms
            t.rows["ltp"][3] = 2.0
            t.end(3, 1)
            time.sleep(0.001)
    th = threading.Thread(target=writer, daemon=True)
    th.start()
    try:
        odd = torn = 0
        n = 200
        for _ in range(n):
            s = t.snapshot()
            if int(s["seq"][3]) & 1:
                odd += 1
                assert t.last_torn >= 1             # any torn row returned is counted
            torn += t.last_torn
            time.sleep(0.0003)
        assert odd <= n * 0.15, (odd, n)            # without yielding retries this is ~50 %
    finally:
        stop.set(); th.join(1)
        t.close(); t.unlink()


def test_replay_zeroes_rows_when_ids_move():
    t = Table(create=True, name=f"t_{TAG}_z")
    try:
        a = [dict(id=0, key="A", token="4.1!1", seg="fo"), dict(id=1, key="B", token="4.1!2", seg="fo")]
        feed_replay.install_registry(t, a, 1)
        t.rows["ttq"][1] = 5e6
        b = a + [dict(id=2, key="C", token="4.1!3", seg="fo")]          # re-centre: ids kept
        feed_replay.install_registry(t, b, 2, prev_items=a)
        assert float(t.rows["ttq"][1]) == 5e6
        c = [dict(id=0, key="A", token="4.1!1", seg="fo"), dict(id=1, key="C", token="4.1!3", seg="fo")]
        feed_replay.install_registry(t, c, 3, prev_items=b)            # restart: ids moved
        assert float(t.rows["ttq"][1]) == 0.0
        t.rows["ttq"][1] = 7.0
        feed_replay.install_registry(t, c, 4, prev_items=c, zero=True)  # a new part = a feed restart
        assert float(t.rows["ttq"][1]) == 0.0
    finally:
        t.close(); t.unlink()


def test_on_message_records_inside_the_lock():
    import inspect
    from apex import feed_breeze
    lines = inspect.getsource(feed_breeze.BreezeFeed.hook).splitlines()
    ind = lambda l: len(l) - len(l.lstrip())
    w = [l for l in lines if "with feed.lock:" in l][0]
    put = [l for l in lines if 'feed.rec.put("p"' in l][0]
    assert lines.index(put) > lines.index(w) and ind(put) > ind(w)   # C-37: put is inside the lock


def test_config_validate_still_clean():
    assert config.validate() == []


def test_engineio_messages_dispatched_in_order_on_the_read_thread():
    """D-106: no thread per websocket message; arrival order kept."""
    try:
        import engineio
        from engineio import packet as P
    except Exception:
        print("  (engineio not installed: skipped)")
        return
    import threading
    from apex import feed_breeze
    feed_breeze.install_sync_dispatch()
    c = engineio.Client()
    seen = []
    c.on("message", lambda d: seen.append((d, threading.current_thread().name)))
    for i in range(5):
        c._receive_packet(P.Packet(P.MESSAGE, f"m{i}"))
    assert [x[0] for x in seen] == [f"m{i}" for i in range(5)]
    assert all(x[1] == threading.current_thread().name for x in seen)


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
