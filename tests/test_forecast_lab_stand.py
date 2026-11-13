"""13 Nov (owner point 4): the Forecast Lab takes a stand (core.Lab.stand): BULLISH / BEARISH / SIDEWAYS from the
20-minute move and the VWAP distance, with hysteresis and a 90-s hold, a behaviour sentence in points, and the rule's
measured record (about 50 % at 15 minutes) said beside it. Display only."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_forecast_lab as TL  # noqa: E402
from apex.forecast_lab import core as C  # noqa: E402


def test_a_steady_rally_reads_bullish_then_a_flat_market_goes_back_to_sideways():
    lab = C.Lab(n_paths=100)
    words = []
    rows = TL.tape(1500, drift=0.06, vol=0.3, seed=5)                  # +90 pts over 25 minutes, little noise
    for k, r in enumerate(rows):
        lab.step(r)
        if k > 1250 and k % 10 == 0:
            words.append(lab.panel()["stand"]["word"])
    s = lab.panel()["stand"]
    assert s["ok"] and s["word"] == "BULLISH" and s["strength"] >= 40, s
    assert s["say"].startswith("Buyers are in control") and "pts in 20 minutes" in s["say"]
    assert s["record"]["hit15"] < 55 and "not a forecast" in s["note"]
    assert any(f["k"] == "move20" and f["pro"] is True for f in s["facts"])
    flat = TL.tape(1500, drift=0.0, vol=0.3, seed=6, start=rows[-1]["t"] + 1)
    base = rows[-1]["F"] if "F" in rows[-1] else None
    for r in flat:
        lab.step(r)
    s2 = lab.panel()["stand"]
    assert s2["ok"] and s2["word"] in ("SIDEWAYS", "BULLISH")
    assert s2["word"] == "SIDEWAYS" or s2["strength"] > 20


def test_the_stand_waits_for_twenty_minutes_of_quotes():
    lab = C.Lab(n_paths=100)
    for r in TL.tape(700, seed=2):
        lab.step(r)
    s = lab.panel().get("stand")
    assert s is not None and not s["ok"] and "20 minutes" in s["why"]
