"""14 Nov (docs/59): the declared champion's first day counts in the scoreboard and the challengers' paired test;
an evening promotion still starts the next session; the nightly side-by-side of the shadow accounts."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.engine import learning as L  # noqa: E402


def test_owner_declared_champion_counts_from_its_own_date():
    book, since = config.CHAMPION_OWNER
    s = {"champion": book, "champion_since": since}
    assert L._first_counted(s) == since and L._counts(since, s) and not L._counts("2026-01-01", s)
    promoted = {"champion": "c20_9x", "champion_since": "2026-11-20"}           # an evening promotion
    assert L._first_counted(promoted) is None and not L._counts("2026-11-20", promoted) and L._counts("2026-11-23", promoted)


def test_paired_test_includes_the_first_day_when_asked():
    days = {"a": {"2026-11-09": [{"ret_pct": 10.0}], "2026-11-11": [{"ret_pct": 5.0}]},
            "b": {"2026-11-09": [{"ret_pct": 0.0}], "2026-11-11": [{"ret_pct": 0.0}]}}
    assert L.paired_test(days, "a", "b", "2026-11-09", 0.05)[0] == 1
    assert L.paired_test(days, "a", "b", "2026-11-09", 0.05, first="2026-11-09")[0] == 2


def test_shadow_side_by_side_compounds_each_day():
    days = {"conductor": {"2026-11-16": [{"ret_pct": 10.0}, {"ret_pct": -5.0}], "2026-11-13": [{"ret_pct": -50.0}]},
            "fade20": {"2026-11-17": [{"ret_pct": 4.0}]}}
    out = chr(10).join(L.shadow_lines(days))
    assert "| **conductor** (live) | 1 | 2 | 1 | +4.5 " in out and "| fade20 | 1 | 1 | 1 | +4.0 " in out
    assert "11-13" not in out                                                      # before the shadows ran: left out
    assert L.shadow_lines({})[-1] == "No session since then yet."


def test_shadow_total_adds_the_days_because_capital_is_fresh_every_day():
    """15 Nov review: +50 % then -50 % is 0 over two fresh-capital days, not the -25 % of one compounding account."""
    days = {"conductor": {"2026-11-16": [{"ret_pct": 50.0}], "2026-11-17": [{"ret_pct": -50.0}]}}
    out = chr(10).join(L.shadow_lines(days))
    assert "| **conductor** (live) | 2 | 2 | 1 | +0.0 | +50.0 | -50.0 |" in out and "sum of day %" in out


def test_observers_and_the_gate_test_count_the_declared_first_day():
    book, since = config.CHAMPION_OWNER
    s = {"champion": book, "champion_since": since, "registered": "2026-10-01", "log": []}
    from datetime import date, timedelta
    d0 = date.fromisoformat(since)
    before, after = (d0 - timedelta(days=3)).isoformat(), (d0 + timedelta(days=2)).isoformat()
    days = {book: {since: [{"ret_pct": 1.0}], after: [{"ret_pct": 2.0}], before: [{"ret_pct": 9.0}]}}
    text = chr(10).join(L.observer_lines(s, days, [1.0, 2.0]))
    assert "evening looks: 2 for this champion" in text, text[:300]      # the declared day and the later one
    promoted = dict(s, champion_since=before)                              # an evening promotion: its own day is out
    promoted["champion"] = "c20_9x"
    days["c20_9x"] = days[book]
    assert "evening looks: 2 for this champion" in chr(10).join(L.observer_lines(promoted, days, [1.0, 2.0]))
