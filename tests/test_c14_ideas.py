"""29 Oct: the Ideas board -- observers only. Every card loads, survives junk input, stays fast, tapes its changes,
and nothing it does can reach a book."""
import json
import math
import os
import tempfile
from datetime import datetime

import numpy as np

from apex import config
from apex.engine import ideas


def _rows(t, spot, k0=25900, n=10, junk=False):
    rows = []
    for j in range(-n, n + 1):
        k = k0 + 50 * j
        for rr in ("CE", "PE"):
            intr = max(spot - k, 0) if rr == "CE" else max(k - spot, 0)
            px = intr + 60 * math.exp(-abs(spot - k) / 120) + 5
            d = 0.5 + (spot - k) / 400 if rr == "CE" else -0.5 + (spot - k) / 400
            d = max(-0.99, min(0.99, d))
            rows.append({"strike": k, "rr": rr, "expiry": "2026-11-03", "ltp": px, "bid": px - 0.3, "ask": px + 0.3,
                         "tbq": 50000 + 100 * (t % 97), "tsq": 52000 - 80 * (t % 89), "ttq": 1000 * t,
                         "oi": 1e6 + 1000 * (t // 60) * (1 if rr == "PE" else -1), "iv": 0.12, "delta": d,
                         "gamma": 0.0012, "theta": -0.08, "vega": 4.0, "age": 0.5})
            if junk and (j + t) % 7 == 0:
                rows[-1].update(ltp=None, bid=float("nan"), ask=0, iv=None, delta=None, oi=None)
    return rows


def _run(board, secs, junk=False, t0=None):
    t0 = t0 or datetime(2026, 10, 29, 9, 15, 5, tzinfo=config.IST).timestamp()
    for s in range(secs):
        t = t0 + s
        spot = 25900 + 40 * math.sin(s / 300) + 0.5 * s / 60
        board.feed_rows(t, datetime.fromtimestamp(t, config.IST), None if (junk and s % 50 == 0) else spot,
                        spot + 30, "2026-11-03", _rows(s, spot, junk=junk))
        board.evaluate()


def test_every_card_loads_and_has_its_fields():
    mods, bad = ideas.discover()
    assert bad == [], bad
    assert len(mods) >= 1
    names = [m.NAME for m in mods]
    assert len(names) == len(set(names))
    for m in mods:
        assert m.TITLE and len(m.TITLE) <= 40 and m.IDEA and m.VERDICT, m.__name__
        assert 1 <= int(getattr(m, "EVERY_S", 5)) <= 60


def test_cards_survive_an_hour_of_junk_fast_and_taped():
    d = tempfile.mkdtemp()
    b = ideas.Board("2026-10-29", out_dir=d)
    _run(b, 3600, junk=True)
    b.close()
    for s in b.slots:
        assert not s.off, (s.name, s.off)
        assert s.errors == 0, s.name
        assert s.calls > 0 and s.ms < config.IDEAS_SLOW_MS, (s.name, s.ms)
    v = b.view()
    json.dumps(v)                                   # the dashboard blob must serialise
    assert len(v["ideas"]) == len(b.slots)
    lines = [json.loads(x) for x in open(os.path.join(d, "ideas_2026-10-29.jsonl"), encoding="utf-8")]
    assert any(r["kind"] == "snap" for r in lines)


def test_a_faulting_card_is_switched_off_not_the_engine():
    class Boom:
        def update(self, env):
            raise ValueError("boom")
    b = ideas.Board("2026-10-29", tape=False)
    s = b.slots[0]
    s.obj, s.every, s.phase = Boom(), 1, 0
    _run(b, 30)
    assert s.off and "5 faults" in s.off
    assert all(not x.off for x in b.slots[1:])


def test_history_series_and_at():
    h = ideas.History(5)
    for i in range(8):
        h.add("SPOT", [100.0 + i, 25000.0 + i])
    h.tick(107.0)
    T, V = h.series("SPOT")
    assert list(T) == [103, 104, 105, 106, 107] and V[-1] == 25007
    assert h.at("SPOT", secs_ago=2) == 25005
    T, V = h.series("SPOT", secs=2)
    assert list(T) == [105, 106, 107]
    T, V = h.series("SPOT", since=105)
    assert list(T) == [106, 107]


def test_books_never_see_the_board():
    """The board is fed after run_books and its view is never put into ctx."""
    src = open(os.path.join(os.path.dirname(config.__file__), "engine_main.py"), encoding="utf-8").read()
    assert 'ctx["ideas"]' not in src and "ctx['ideas']" not in src
    i_books = src.index("self.run_books(ctx)\n")
    i_ideas = src.index("self.ideas.step(self, ctx, snap)")
    assert i_ideas > i_books
    psrc = open(os.path.join(os.path.dirname(config.__file__), "engine", "paper.py"), encoding="utf-8").read()
    assert "import ideas" not in psrc and "ideas_mod" not in psrc and "ctx.get(\"ideas\")" not in psrc
