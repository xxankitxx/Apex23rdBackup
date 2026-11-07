"""7 Nov code review, round 2: compare tool (6.1), tape parts (6.4), full config hash (3.1), clustered quarantine
windows (7.1 / 7.3), the opening range after a late start (8.2), the day-state continuous values (8.3)."""
import json
import os
import tempfile

from apex import config, feed_core, replay_batch, replay_compare
from apex.engine import defects
from apex.engine.daystate import DayState


def _run(root, books, events=None):
    p = os.path.join(root, "paper")
    os.makedirs(p, exist_ok=True)
    json.dump(books, open(os.path.join(p, "2026-11-06.json"), "w"))
    if events is not None:
        with open(os.path.join(p, "events_2026-11-06.jsonl"), "w") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")
    return root


def _books(pnl=1.5):
    return {"c20_9x": {"name": "c20_9x", "trades": [{"time_in": "10:00:00", "pnl_pts": pnl}]},
            "RAW": {"name": "RAW", "trades": []}}


def test_compare_identical_and_first_difference():
    a = _run(tempfile.mkdtemp(), _books(), [{"k": "INFO", "x": "a"}, {"k": "INFO", "x": "sp#cf fired"}])
    b = _run(tempfile.mkdtemp(), _books(), [{"k": "INFO", "x": "a"}])
    assert replay_compare.main([a, b]) == 0                     # #cf lines are not compared
    c = _run(tempfile.mkdtemp(), _books(pnl=1.50000001), [{"k": "INFO", "x": "a"}])
    res = replay_compare.compare_day(a, c, "2026-11-06")
    bad = [m for ok, m in res if not ok]
    assert bad and "book=c20_9x trade=0 field=pnl_pts" in bad[0]   # exact, no float tolerance
    assert replay_compare.main([a, c]) == 1


def test_compare_fails_on_recorder_errors_and_skips_one_sided_files():
    a = _run(tempfile.mkdtemp(), _books())
    b = _run(tempfile.mkdtemp(), _books())
    open(os.path.join(b, "paper", "missed_2026-11-06.jsonl"), "w").write("{}\n")
    assert replay_compare.main([a, b]) == 0                     # recorder off vs on: missed_* on one side only
    json.dump({"rows": 1, "cf_errors": 1, "recorder_faults": 0},
              open(os.path.join(b, "paper", "missed_summary_2026-11-06.json"), "w"))
    assert replay_compare.main([a, b, "--books-only"]) == 1


def test_tape_parts_are_all_listed():
    d = tempfile.mkdtemp()
    for f in ("2026-10-19.jsonl.gz", "2026-10-19.p2.jsonl.gz", "2026-10-19.p3.jsonl.gz", "2026-10-20.jsonl.gz"):
        open(os.path.join(d, f), "wb").write(b"x")
    parts = [os.path.basename(p) for p in replay_batch.tape_parts(os.path.join(d, "2026-10-19.jsonl.gz"))]
    assert parts == ["2026-10-19.jsonl.gz", "2026-10-19.p2.jsonl.gz", "2026-10-19.p3.jsonl.gz"]


def test_full_config_hash_sees_the_clock(monkeypatch):
    h0, old = feed_core.config_hash_full(), feed_core.config_hash()
    monkeypatch.setattr(config, "LAST_ENTRY", (15, 29))
    assert feed_core.config_hash_full() != h0 and feed_core.config_hash() == old
    monkeypatch.setattr(config, "LAST_ENTRY", (15, 15))
    monkeypatch.setattr(config, "PORT", 9999)                  # plumbing does not change a trade
    assert feed_core.config_hash_full() == h0


def _t(tin, tout, age=900):
    return {"time_in": tin, "time_out": tout, "trade_age_in": age, "trade_age_out": 1}


def test_quarantine_windows_cluster_by_time():
    rows = [{"day": "2026-11-06", "book": "a", "trades": [_t("09:40:00", "09:50:00"), _t("10:05:00", "10:10:00")]},
            {"day": "2026-11-06", "book": "b", "trades": [_t("14:50:00", "14:55:00")]}]
    q = defects.Quarantine(rows, declared={})
    w = q.windows("2026-11-06")
    assert [(defects._hms(a), defects._hms(b)) for a, b, _, _ in w] == [("09:40:00", "10:10:00"), ("14:50:00", "14:55:00")]
    assert q.reason("2026-11-06", {"time_in": "12:00:00"}) is None        # old code: 09:40-14:55, all quarantined
    assert q.reason("2026-11-06", {"time_in": "14:52:00"})
    assert not q.whole_day("2026-11-06")


def test_session_long_auto_window_is_a_whole_day():
    prior = {"time_in": "15:00:00", "time_out": "15:20:00", "trade_age_in": 86400 * 2, "trade_age_out": 1}
    q = defects.Quarantine([{"day": "2026-11-06", "book": "a", "trades": [prior]}], declared={})
    old = config.MARKET_CLOSE
    try:
        config.MARKET_CLOSE = (15, 20)
        assert q.whole_day("2026-11-06")
    finally:
        config.MARKET_CLOSE = old


def _feed(ds, start_hm, n=3000):
    h, m = start_hm
    for k in range(n):
        mm = h * 60 + m + k // 60
        ds.add(1.8e9 + k, 24000.0 + (k % 50), mm)


def test_opening_range_unknown_after_a_late_start():
    on_time = DayState("2026-11-06")
    _feed(on_time, (9, 15))
    assert on_time.or_hi is not None and on_time.or_done(1.8e9 + 2999) and not on_time.or_late
    late = DayState("2026-11-06")
    _feed(late, (11, 40))                                          # a cold restart at 11:40
    assert late.or_late and late.or_hi is None and not late.or_done(1.8e9 + 2999)
    assert not any("OR " in lab for _, lab in late.levels(24010.0))
    assert late.hi is not None                                      # the rest of the day state still works
    back = DayState.load(json.loads(json.dumps(late.dump())))
    assert back.or_late


def test_day_view_has_give_and_position():
    ds = DayState("2026-11-06")
    for k, sp in enumerate([100.0, 140.0, 120.0]):
        ds.add(1.8e9 + k, sp, 9 * 60 + 20)
    v = ds.view()
    assert v["give"] == 0.5 and v["pos_in_range"] == 0.5 and v["or_late"] is False
