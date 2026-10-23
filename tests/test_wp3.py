"""WP-3 checks (learning record integrity): python tests/test_wp3.py  (numpy only)."""
import glob
import importlib
import json
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_wp3_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apex import config  # noqa: E402
from apex.engine import learning, paper  # noqa: E402


def _fresh():
    """A brand-new APEX_DATA for each test, so no file leaks between them."""
    global config, learning
    os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_wp3_")
    config = importlib.reload(config)
    learning = importlib.reload(learning)


def _book(name, rets, day):
    b = paper.Book(name, config.VARIANTS.get(name, config.TRIGGER), day)
    b.trades = [{"pnl_pts": r, "pnl_rs": 0, "ret_pct": r, "entry": 100.0, "advisors": {},
                 "reason": "STOP", "time_in": "10:00:00"} for r in rets]
    return b


def _books(day, i, challenger="m1.5_s0.4"):
    """Every registered book; one challenger clearly beats the champion."""
    out = {}
    for name in list(config.VARIANTS) + ["RAW"]:
        rets = [3.0 + (i % 3), 2.0] if name == challenger else [1.0, -1.0 + (i % 2) * 0.5]
        out[name] = _book(name, rets, day)
    return out


def _trading_days(start, n):
    from datetime import date, timedelta
    d, out = date.fromisoformat(start), []
    while len(out) < n:
        if config.is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _report():
    return open(learning.REPORT, encoding="utf-8").read()


# (a) C-09: a torn last line no longer stops record_day or learn, and its evidence is kept
def test_torn_line_tolerated():
    _fresh()
    d1, d2 = "2026-10-19", "2026-10-21"
    learning.record_day(d1, _books(d1, 0))
    torn = '{"day": "2026-10-19", "book": "RAW", "trades": [{"pnl_pt'
    with open(learning.DAYS, "a", encoding="utf-8") as f:
        f.write(torn)                                    # killed mid-line, no newline
    learning.record_day(d2, _books(d2, 1))               # old code: JSONDecodeError
    s = learning.learn(d2)
    assert s["learned_day"] == d2
    assert "1 corrupt row(s) skipped" in _report()
    assert torn in open(learning.DAYS + ".corrupt", encoding="utf-8").read()
    days = learning._load_days()
    assert set(days[config.CHAMPION_DEFAULT]) == {d1, d2}
    # learn alone (python run_apex.py learn) on a file that still holds a torn line
    with open(learning.DAYS, "a", encoding="utf-8") as f:
        f.write("not json\n")
    learning.learn(d2)
    assert "1 corrupt row(s) skipped" in _report()
    assert open(learning.DAYS + ".corrupt", encoding="utf-8").read().count(torn) == 1   # kept once, not per read


# (b) C-09: a crash between writing and replacing leaves the old days.jsonl intact
def test_crash_mid_write_keeps_old_file():
    _fresh()
    d1, d2 = "2026-10-19", "2026-10-21"
    learning.record_day(d1, _books(d1, 0))
    before = open(learning.DAYS, encoding="utf-8").read()
    real = os.replace
    calls = {"n": 0}

    def boom(a, b):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("simulated power cut")
        return real(a, b)

    os.replace = boom
    try:
        try:
            learning.record_day(d2, _books(d2, 1))
            raised = False
        except OSError:
            raised = True
    finally:
        os.replace = real
    assert raised
    assert open(learning.DAYS, encoding="utf-8").read() == before    # old code: rewritten in place

    # a serialiser dying half-way through the rows: the old code had already truncated the file
    real_json = learning.json

    class Dying:
        loads = staticmethod(real_json.loads)
        load = staticmethod(real_json.load)
        n = 0

        @staticmethod
        def dumps(*a, **k):
            Dying.n += 1
            if Dying.n > 3:
                raise RuntimeError("killed")
            return real_json.dumps(*a, **k)

    learning.json = Dying
    try:
        try:
            learning.record_day(d2, _books(d2, 1))
        except RuntimeError:
            pass
    finally:
        learning.json = real_json
    assert open(learning.DAYS, encoding="utf-8").read() == before

    # Windows: a reader holding the file makes os.replace raise PermissionError; it is retried
    calls["n"] = 0

    def locked_once(a, b):
        calls["n"] += 1
        if calls["n"] == 1:
            raise PermissionError("in use")
        return real(a, b)

    os.replace = locked_once
    try:
        learning.record_day(d2, _books(d2, 1))
        learning.save_state(learning.load_state())
    finally:
        os.replace = real
    assert d2 in learning._load_days()["RAW"]


# (c) C-10: an idle Saturday records nothing and moves nothing; member 08's promote-on-Saturday cannot happen
def test_non_trading_day_skipped_and_no_saturday_promotion():
    _fresh()
    st = learning.load_state()
    st["registered"] = st["champion_since"] = "2026-10-01"
    learning.save_state(st)
    for i, d in enumerate(_trading_days("2026-10-02", 14)):           # 2 Oct is a holiday; ends Fri 23 Oct
        assert d <= "2026-10-23"
        learning.record_day(d, _books(d, i))
    s = learning.learn("2026-10-23")                                   # first look: the challenger passes once
    assert s["champion"] == config.CHAMPION_DEFAULT
    assert s["streak"]["m1.5_s0.4"] == config.PROMOTE_STREAK - 1
    days_before = open(learning.DAYS, encoding="utf-8").read()
    state_before = open(learning.STATE, encoding="utf-8").read()

    sat = "2026-10-24"
    empty = {n: _book(n, [], sat) for n in list(config.VARIANTS) + ["RAW"]}
    assert learning.record_day(sat, empty) is False                    # old code: 0 % rows for every book
    s2 = learning.learn(sat)                                           # old code: streak 2 -> promoted
    assert open(learning.DAYS, encoding="utf-8").read() == days_before
    assert open(learning.STATE, encoding="utf-8").read() == state_before   # no save at all
    assert s2["champion"] == config.CHAMPION_DEFAULT and s2["streak"] == s["streak"]
    assert "not an NSE trading day" in _report()
    assert learning.load_state()["learned_day"] == "2026-10-23"
    # Tue 20 Oct 2026 is Dussehra: a weekday holiday is skipped the same way
    assert learning.record_day("2026-10-20", {n: _book(n, [], "2026-10-20") for n in empty}) is False
    # a non-trading day that does carry trades (special session / sim data) is kept, never discarded
    assert learning.record_day("2026-10-25", {"RAW": _book("RAW", [1.0], "2026-10-25")}) is True


# (d) C-03: a session stopped before 15:30 is back-filled from paper/<day>.json on the next evening
def test_backfill_unrecorded_day():
    _fresh()
    d = "2026-10-19"
    books = _books(d, 0)
    books[config.CHAMPION_DEFAULT].pos = {"key": "x", "entry": 100.0}   # stopped with a position open
    paper.save_books(books, d)                                          # the engine saved, record_day never ran
    paper.save_books(_books("2026-10-18", 0), "2026-10-18")             # a Sunday file: not a session
    paper.save_books(_books("2026-10-21", 0), "2026-10-21")             # today's own file: not back-filled
    for i, x in enumerate(["2026-10-12", "2026-10-15"]):               # before registration: not evidence
        paper.save_books(_books(x, i), x)
    with open(os.path.join(config.PAPER_DIR, "trades_2026-10-19.csv"), "w") as f:
        f.write("x\n")
    s = learning.learn("2026-10-21")
    days = learning._load_days()
    assert set(days["RAW"]) == {d}                                      # old code: nothing at all
    assert len(days[config.CHAMPION_DEFAULT][d]) == 2
    rows = [json.loads(x) for x in open(learning.DAYS, encoding="utf-8")]
    champ_row = next(r for r in rows if r["book"] == config.CHAMPION_DEFAULT)
    assert champ_row.get("unclosed") is True and champ_row.get("backfilled") is True
    assert not next(r for r in rows if r["book"] == "RAW").get("unclosed")
    assert {"event": "backfilled", "day": d, "on": "2026-10-21"} in s["log"]
    assert "Back-filled" in _report()
    s2 = learning.learn("2026-10-21")                                   # idempotent: nothing to back-fill now
    assert sum(1 for e in s2["log"] if e["event"] == "backfilled") == 1


# (e) the betting e-value: sane at both ends, and it never moves a decision
def test_e_value_sanity():
    _fresh()
    assert learning.e_value_mean_le0([0.0] * 200) <= 1.0
    assert learning.e_value_mean_le0([]) == 1.0
    assert learning.e_value_mean_le0([25.0] * 40) > 20
    assert learning.e_value_mean_le0([-5.0] * 40) < 1.0
    assert learning.e_value_mean_le0([-100.0] * 3 + [1000.0] * 3) < 1e6     # clipped, finite
    # the report carries every observer, and GO / KILL / promotion are exactly today's
    for i, d in enumerate(_trading_days("2026-10-22", 12)):     # D-141: the owner's champion date moved to 22 Oct
        learning.record_day(d, _books(d, i))
        s = learning.learn(d)
    rep = _report()
    for frag in ("Betting e-value", "SPRT on per-trade 100·ln(1+r)", "Wald lines with the observed sd",
                 "Champion #", "evening looks", "Day-level conditions for GO", "≥ 2 expiry days"):
        assert frag in rep, frag
    assert s["champion"] == "m1.5_s0.4"                                 # promoted exactly as the rule says


def test_observers_change_no_decision():
    """The same history learned with the observers stubbed out gives an identical state."""
    states = []
    for stub in (False, True):
        _fresh()
        if stub:
            learning.observer_lines = lambda s, days, ctr: []
        for i, d in enumerate(_trading_days("2026-10-19", 16)):
            learning.record_day(d, _books(d, i))
            learning.learn(d)
        states.append(learning.load_state())
    assert states[0] == states[1]


# (f) C-43: a corrupt state.json is preserved, not silently overwritten
def test_corrupt_state_preserved():
    _fresh()
    with open(learning.STATE, "w") as f:
        f.write('{"champion": "m2.5_s0.6", "log": [')                 # torn
    s = learning.load_state()
    assert s["champion"] == config.CHAMPION_DEFAULT
    kept = glob.glob(learning.STATE + ".corrupt-*")
    assert len(kept) == 1 and open(kept[0]).read().startswith('{"champion"')   # old code: nothing kept
    d = "2026-10-19"
    learning.record_day(d, _books(d, 0))
    learning.learn(d)
    assert "state.json was unreadable" in _report()
    assert len(glob.glob(learning.STATE + ".corrupt-*")) == 1          # the save did not touch the evidence
    assert os.path.exists(os.path.join(config.LEARN_DIR, f"report_{d}.md"))


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
