"""9 Nov: the books file is written from cached closed-trade text (paper._books_text). On 9 Nov live, re-serialising
every closed trade on every save froze the engine for up to 8 s and every council entry after 12:05 lapsed."""
import json
import time

from apex import config
from apex.engine import paper


def _book(name, n, day="2026-11-09"):
    b = paper.Book(name, dict(config.VARIANTS["m2.0_s0.5"]), day)
    for i in range(n):
        b.trades.append({"key": f"K{i}", "entry": 100.0 + i, "exit": 101.0, "t_in": 1.0 * i, "t_out": 2.0 * i + 1,
                         "pnl_rs": 65.0, "weather_trig": {f"f{k}": k * 0.5 for k in range(400)}})
    return b


def test_text_equals_plain_dump_and_loads():
    books = {"a": _book("a", 3), "b": _book("b", 0)}
    books["a"].pos = {"key": "P", "entry": 5.0, "pending": None}
    want = json.loads(json.dumps({n: b.to_json() for n, b in books.items()}, default=str))
    assert json.loads(paper._books_text(books, "2026-11-09")) == want
    assert json.loads(paper._books_text(books, "2026-11-09")) == want          # second call: from the cache


def test_added_field_and_open_trade_are_not_stale():
    b = _book("a", 2)
    paper._books_text({"a": b}, "2026-11-09")
    b.trades[0]["note"] = "added after the close"                              # a new field re-serialises the trade
    b.trades.append({"key": "open", "entry": 1.0, "exit": None})               # never cached while open
    got = json.loads(paper._books_text({"a": b}, "2026-11-09"))
    assert got["a"]["trades"][0]["note"] == "added after the close"
    b.trades[-1].update(exit=2.0, t_out=9.0)
    assert json.loads(paper._books_text({"a": b}, "2026-11-09"))["a"]["trades"][-1]["exit"] == 2.0


def test_new_day_drops_the_cache_and_save_roundtrips():
    b = _book("a", 2)
    paper._books_text({"a": b}, "2026-11-09")
    assert paper._TRADE_JSON["m"]
    paper._books_text({"a": _book("a", 1, "2026-11-10")}, "2026-11-10")
    assert len(paper._TRADE_JSON["m"]) == 1
    paper.save_books({"a": b}, "2026-11-09")
    loaded = paper.load_books("2026-11-09")
    assert loaded and len(loaded["a"].trades) == 2


def test_repeat_save_is_cheap():
    books = {f"b{i}": _book(f"b{i}", 8) for i in range(80)}                    # 640 closed trades with photographs
    paper._books_text(books, "2026-11-09")
    t0 = time.perf_counter()
    paper._books_text(books, "2026-11-09")
    assert time.perf_counter() - t0 < 0.25


def test_async_save_writes_the_latest_state_and_survives_a_failed_write(monkeypatch):
    b = _book("a", 2)
    paper.save_books_async({"a": b}, "2026-11-09")
    b.trades.append({"key": "late", "entry": 1.0, "exit": 2.0, "t_in": 1.0, "t_out": 2.0})
    paper.save_books_async({"a": b}, "2026-11-09")                             # latest wins
    assert paper.save_flush(10.0)
    assert len(paper.load_books("2026-11-09")["a"].trades) == 3
    # 10 Nov (docs/38 O3): a failed write is not forgotten. flush() says "not on disk" while it fails, the state is
    # retried, and it lands by itself once the disk works again
    real, n0 = paper._write_tmp, paper._SAVER.errors
    monkeypatch.setattr(paper, "_write_tmp", lambda *a: (_ for _ in ()).throw(OSError("disk")))
    b.trades.append({"key": "during", "entry": 1.0, "exit": 2.0, "t_in": 3.0, "t_out": 4.0})
    paper.save_books_async({"a": b}, "2026-11-09")
    assert paper.save_flush(1.2) is False
    st = paper.save_status()
    assert st["errors"] > n0 and st["fails_row"] >= 1 and "disk" in st["last_error"] and st["lag"] >= 1
    monkeypatch.setattr(paper, "_write_tmp", real)
    assert paper.save_flush(10.0)                                              # the retry wrote it: nothing was lost
    assert paper.save_status()["fails_row"] == 0 and paper.save_status()["lag"] == 0
    assert len(paper.load_books("2026-11-09")["a"].trades) == 4 and paper.LAST_LOAD_NOTE == ""


def test_changed_existing_field_is_never_served_from_the_cache():
    """docs/38 O2: the Conductor rewrites exit_bid / t_out / hold_s on a trade that is already closed and cached."""
    b = _book("a", 0)
    b.pos = {"key": "K", "entry": 100.0, "qty": 65, "t_in": 1.0, "dir": 1}
    ctx = {"now_s": 50.0, "now_dt": __import__("datetime").datetime(2026, 11, 9, 10, 0, 0), "fut": 25000.0}
    closed = paper.close_trade(b, ctx, 110.0, "TEST", {"bid": 109.0, "ask": 111.0, "age": 0.1})
    assert isinstance(closed, paper.ClosedTrade) and b.trades[-1] is closed
    first = json.loads(paper._books_text({"a": b}, "2026-11-09"))["a"]["trades"][0]
    assert first["exit_bid"] == 109.0
    n = len(closed)
    closed["exit_bid"], closed["t_out"], closed["hold_s"] = 105.5, 44.0, 43.0  # same field count, new values
    assert len(closed) == n
    got = json.loads(paper._books_text({"a": b}, "2026-11-09"))["a"]["trades"][0]
    assert (got["exit_bid"], got["t_out"], got["hold_s"]) == (105.5, 44.0, 43.0)
    closed.update(exit_ask=112.0)
    assert json.loads(paper._books_text({"a": b}, "2026-11-09"))["a"]["trades"][0]["exit_ask"] == 112.0
    paper.save_books({"a": b}, "2026-11-09")
    back = paper.load_books("2026-11-09")["a"].trades[0]                       # a loaded trade is tracked too
    assert isinstance(back, paper.ClosedTrade) and back == json.loads(json.dumps(closed, default=str))
    import copy
    assert copy.deepcopy(closed) == closed and isinstance(copy.deepcopy(closed), paper.ClosedTrade)


def test_nested_change_is_caught_by_touch_the_audit_and_the_full_save():
    b = _book("a", 3)
    b.trades = [paper.ClosedTrade(t) for t in b.trades]
    books = {"a": b}
    paper._CACHE_AUDIT["ptr"] = 0
    paper._books_text(books, "2026-11-09")
    b.trades[0]["weather_trig"]["f1"] = 99.0                                   # inside a nested value: the dict cannot see it
    paper.touch(b.trades[0])
    paper._CACHE_AUDIT["ptr"] = 10 ** 9
    assert json.loads(paper._books_text(books, "2026-11-09"))["a"]["trades"][0]["weather_trig"]["f1"] == 99.0
    s0 = paper._CACHE_AUDIT["stale"]
    b.trades[1]["weather_trig"]["f1"] = 77.0                                   # and one nobody announced
    paper._CACHE_AUDIT["ptr"] = 0
    got = json.loads(paper._books_text(books, "2026-11-09"))                   # the rolling audit reaches it
    assert got["a"]["trades"][1]["weather_trig"]["f1"] == 77.0 and paper._CACHE_AUDIT["stale"] == s0 + 1
    b.trades[2]["weather_trig"]["f2"] = 55.0
    paper._CACHE_AUDIT["ptr"] = 10 ** 9                                        # the audit is elsewhere this save ...
    assert json.loads(paper._books_text(books, "2026-11-09"))["a"]["trades"][2]["weather_trig"]["f2"] == 1.0
    paper.save_books(books, "2026-11-09", full=True)                           # ... the final save never trusts the cache
    assert paper.load_books("2026-11-09")["a"].trades[2]["weather_trig"]["f2"] == 55.0
    assert paper.save_status()["stale_fixed"] == s0 + 2


def test_older_state_never_replaces_a_newer_one_and_sync_save_does_not_share_the_tmp(monkeypatch):
    """docs/38 O3: a direct save while the background writer is in the middle of an older state."""
    import os, threading
    b = _book("a", 1)
    path = os.path.join(config.PAPER_DIR, "2026-11-09.json")
    paper.save_books({"a": b}, "2026-11-09")
    gate, inside, real = threading.Event(), threading.Event(), paper._write_tmp

    def slow(p, chunks, suffix=".tmp"):
        tmp = real(p, chunks, suffix)
        if suffix == ".tmp":                                                   # the background writer stops before its replace
            inside.set()
            assert gate.wait(10.0)
        return tmp

    monkeypatch.setattr(paper, "_write_tmp", slow)
    paper.save_books_async({"a": b}, "2026-11-09")                             # the older state (1 trade)
    assert inside.wait(10.0)
    b.trades.append({"key": "newer", "entry": 1.0, "exit": 2.0, "t_in": 1.0, "t_out": 2.0})
    paper.save_books({"a": b}, "2026-11-09")                                   # the newer state, written directly, no waiting
    assert len(json.load(open(path, encoding="utf-8"))["a"]["trades"]) == 2
    gate.set()
    assert paper.save_flush(10.0)
    assert len(json.load(open(path, encoding="utf-8"))["a"]["trades"]) == 2    # the older state was thrown away
    assert not os.path.exists(path + ".tmp") and not os.path.exists(path + ".tmp.sync")


def test_stale_tmp_from_a_killed_run_is_removed_at_start_and_fresh_ones_are_left():
    import os
    old = os.path.join(config.PAPER_DIR, "2026-11-08.json.tmp")
    new = os.path.join(config.PAPER_DIR, "2026-11-09.json.tmp.sync")
    keep = os.path.join(config.PAPER_DIR, "2026-11-08.json")
    for p in (old, new, keep):
        with open(p, "w") as f:
            f.write('{"torn')
    os.utime(old, (time.time() - 3600, time.time() - 3600))
    notes = paper.clean_stale_tmp()
    assert len(notes) == 1 and "2026-11-08.json.tmp" in notes[0]
    assert not os.path.exists(old) and os.path.exists(new) and os.path.exists(keep)
    os.remove(new); os.remove(keep)


def test_lapse_during_an_engine_stall_says_so():
    from datetime import datetime
    b = _book("a", 0)
    for gap, tag in ((0.3, False), (6.5, True)):
        b.ctl["pending_entry"] = {"t": 100.0, "time": "12:10:00", "key": "NIFTY|2026-11-10|25000|CE", "id": 1,
                                  "why": "x", "trigger_ltp": 10.0, "ctl": {}}
        ctx = {"now_s": 100.5, "now_dt": datetime(2026, 11, 9, 12, 10, 0), "by_key": {}, "step_gap": gap}
        assert paper.try_fill_entry(b, ctx)[1].startswith("entry pending")
        ctx = dict(ctx, now_s=107.0, step_gap=0.3)
        why = paper.try_fill_entry(b, ctx)[1]
        assert why.startswith("entry lapsed: no print on") and ("[engine stalled 6.5 s]" in why) == tag
        assert b.blocked == why


def test_the_step_side_of_a_full_day_save_is_small():
    books = {f"b{i}": _book(f"b{i}", 8) for i in range(80)}
    paper._books_chunks(books, "2026-11-09")
    t0 = time.perf_counter()
    paper.save_books_async(books, "2026-11-09")
    dt = time.perf_counter() - t0
    assert paper.save_flush(20.0)
    assert dt < 0.2
