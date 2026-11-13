"""12 Nov evening: the forecaster's plain-words card (apex.forecast_lab.core.plain), on the real 11 Nov payloads."""
import copy
import importlib.util
import os

from apex.forecast_lab import core as C

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("make_payloads", os.path.join(HERE, "fixtures", "forecast_lab", "make_payloads.py"))
MP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MP)


_CASES = MP.cases()


def _flat():
    return copy.deepcopy(_CASES["flat"]["p"])


def _held():
    return copy.deepcopy(_CASES["held"]["p"])            # with the engine's held position (entry 230.5)


def _rows(p):
    return {r["k"]: r for r in C.plain(p)["rows"]}


def test_flat_has_four_plain_rows_and_a_headline():
    p = _flat()
    pl = C.plain(p)
    assert [r["k"] for r in pl["rows"]] == ["far", "way", "trade", "decay"]
    assert pl["head"].endswith(".") and "points per 5 minutes" in pl["head"]
    r = _rows(p)
    assert r["trade"]["title"] == "If you buy now" and "within 5 minutes" in r["trade"]["text"]
    assert "the Conductor does not read it" in r["trade"]["note"]
    assert all(r[k]["tone"] in ("good", "warn", "bad", "none") for k in r)
    assert p["plain"] == pl                                   # make_payloads adds it exactly as panel() does


def test_held_speaks_of_the_trade_and_never_says_flat():
    p = _held()
    r = _rows(p)
    assert r["trade"]["title"] == "Your trade" and "entry" in r["trade"]["text"]
    assert "own rules" in r["trade"]["note"]
    text = " ".join([C.plain(p)["head"]] + [x["text"] + " " + x["note"] for x in r.values()])
    assert "Flat" not in text and "buy now" not in text


def test_a_losing_held_trade_says_what_nifty_needs():
    p = _held()
    o = next(x for x in p["options"] if x["tag"] == "held")
    p["held"]["entry"] = float(o["bid"]) + 10.0               # 10 below entry
    t = _rows(p)["trade"]
    need = 10.0 / abs(o["delta"])
    assert "below entry" in t["text"] and f"{need:.0f} points to get back to entry" in t["text"]
    assert t["tone"] in ("warn", "bad")


def test_lean_words_follow_the_two_minute_mean():
    p = _flat()
    x = next(y for y in p["path"] if y["h"] == 120)
    x["mu"], x["sd"] = 0.0, 5.0
    assert "no lean" in _rows(p)["way"]["text"]
    x["mu"] = 0.5 * 5.0
    w = _rows(p)["way"]
    assert "clear lean up" in w["text"] and w["tone"] == "good"
    x["mu"] = -0.2 * 5.0
    w = _rows(p)["way"]
    assert "slight lean down" in w["text"] and w["tone"] == "bad"
    assert "not a trade signal" in w["note"] and "coin toss" in w["note"]


def test_range_note_follows_todays_status():
    p = _flat()
    st = p["earned"]["range_h"]["fut"]["300"]
    for status, words in (("unchecked", "Not checked enough yet today"), ("narrow", "bigger than these ranges"),
                          ("wide", "smaller than these ranges"), ("ok", "Reliable today")):
        q = copy.deepcopy(p)
        q["earned"]["range_h"]["fut"]["300"] = dict(st, status=status)
        assert words in _rows(q)["far"]["note"], status


def test_no_forecast_states_give_no_rows():
    assert C.plain(dict(ok=False, why="no data yet")) == dict(head="No forecast: no data yet.", rows=[])
    p = _flat()
    assert C.plain(dict(p, stale="the futures quote is 9 s old"))["rows"] == []
    assert "Warming up" in C.plain(dict(p, warm=True))["head"]
    assert C.plain(dict(ok=True))["rows"] == []


def test_decay_row_says_paid_or_not():
    p = _flat()
    p["rent"] = dict(p.get("rent") or {}, ratio=1.4)
    d = _rows(p)["decay"]
    assert "moving enough to pay" in d["text"] and "has not" not in d["text"] and d["tone"] == "good"
    p["rent"]["ratio"] = 0.6
    assert "not been moving enough" in _rows(p)["decay"]["text"]


# ── 12 Nov late: the read, the ladder, the option board and the feed ──────────────────────────────────────────────
def test_live_panel_has_a_read_a_ladder_and_a_board():
    pl = C.plain(_flat())
    assert pl["verdict"]["word"] in ("WAIT", "CALLS FAVOURED", "PUTS FAVOURED", "TILT TO CALLS", "TILT TO PUTS")
    assert pl["verdict"]["conf"] in ("high", "medium", "low", "untested today")
    hs = [r["h"] for r in pl["ladder"]]                                   # 15:14: no 30-minute horizon left
    assert hs and hs[0] == 300 and set(hs) <= {300, 900, 1800} and hs == sorted(hs)
    assert all(r["lo80"] <= r["lo50"] <= r["mid"] <= r["hi50"] <= r["hi80"] for r in pl["ladder"])
    assert pl["board"] and all(b["tag"] != "held" for b in pl["board"])
    assert all(b["rows"] and {r["h"] for r in b["rows"]} <= {300, 900, 1800} for b in pl["board"])
    assert len({(b["strike"], b["side"]) for b in pl["board"]}) == len(pl["board"])      # each contract once
    assert "verdict" not in C.plain(dict(ok=False, why="x"))


def test_flat_read_follows_the_lean():
    p = _flat()
    x = next(y for y in p["path"] if y["h"] == 120)
    x["mu"], x["sd"] = 0.0, 5.0
    assert C.verdict(p)["word"] == "WAIT"
    x["mu"] = 2.5
    v = C.verdict(p)
    assert v["word"] == "CALLS FAVOURED" and v["tone"] == "good" and "lean up" in v["why"]
    x["mu"] = -1.0
    assert C.verdict(p)["word"] == "TILT TO PUTS"


def test_held_read_and_board_put_the_trade_first():
    p = _held()
    pl = C.plain(p)
    assert pl["board"][0]["tag"] == "held" and pl["board"][0]["entry"] == 230.5
    assert pl["verdict"]["word"] in ("HOLD", "PROTECT GAINS", "WATCH", "UNDER PRESSURE")
    o = next(x for x in p["options"] if x["tag"] == "held")
    p["held"]["entry"] = float(o["bid"]) + 400.0 * abs(o["delta"])          # needs 400 Nifty points back
    assert C.verdict(p)["word"] == "UNDER PRESSURE"
    p["held"]["entry"] = float(o["bid"]) + 2.0
    assert C.verdict(p)["word"] == "WATCH"


def test_feed_writes_a_changed_read_only_after_it_holds():
    lab = C.Lab(options=False)
    p = _flat()
    x = next(y for y in p["path"] if y["h"] == 120)
    x["mu"], x["sd"] = 0.0, 5.0
    t0 = float(p["t"])

    def at(dt, mu):
        q = copy.deepcopy(p)
        next(y for y in q["path"] if y["h"] == 120)["mu"] = mu
        q["t"] = t0 + dt
        q["plain"] = C.plain(q)
        lab._feed_step(q)
        return q["plain"]

    first = at(0, 0.0)
    assert len(first["feed"]) == 1 and first["verdict"]["word"] == "WAIT"
    assert at(5, 2.5)["verdict"]["word"] == "WAIT"                       # a new read is held back
    assert at(20, 0.0)["verdict"]["word"] == "WAIT"                      # it flickered back: nothing written
    at(40, 2.5)
    pl = at(75, 2.5)                                                      # held 35 s: written
    assert pl["verdict"]["word"] == "CALLS FAVOURED" and pl["feed"][0]["text"].startswith("WAIT to CALLS FAVOURED")
    assert len(pl["feed"]) == 2


def test_feed_writes_a_market_change_only_after_a_minute():
    lab = C.Lab(options=False)
    p = _flat()
    t0 = float(p["t"])

    def at(dt, name):
        q = copy.deepcopy(p)
        q["regime"] = dict(q.get("regime") or {}, name=name)
        q["t"] = t0 + dt
        q["plain"] = C.plain(q)
        lab._feed_step(q)
        return q["plain"]["feed"]

    n0 = len(at(0, "mixed"))
    assert len(at(10, "trending")) == n0 and len(at(40, "trending")) == n0      # not yet
    assert len(at(50, "mixed")) == n0                                           # flipped back: nothing
    at(60, "choppy")
    f = at(125, "choppy")
    assert len(f) == n0 + 1 and f[0]["text"] == "The market turned choppy."
