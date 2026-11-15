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


# ── 15 Nov review: the banner never shows a stand worked from an old quote, and its look-backs are by the clock ──
def test_a_stale_futures_quote_takes_the_stand_down():
    lab = C.Lab(n_paths=100)
    rows = TL.tape(1500, drift=0.06, vol=0.3, seed=5)
    for r in rows[:-1]:
        lab.step(r)
    lab.step(dict(rows[-1], fage=0.4))
    assert lab.panel()["stand"]["ok"] and lab.panel()["stand"]["word"] == "BULLISH"
    lab.step(dict(rows[-1], t=rows[-1]["t"] + 1, fage=45.0))                    # the future has not printed for 45 s
    p = lab.panel()
    assert p["stale"] == "the futures quote is 45 s old" and p["stand"] == dict(ok=False, why=p["stale"])


def test_look_backs_are_seconds_not_samples_when_seconds_are_missing():
    lab = C.Lab(n_paths=100)
    rows = TL.tape(2400, drift=0.05, vol=0.0, seed=1)                           # a straight line: +0.05 pts a second
    kept = [r for k, r in enumerate(rows) if k % 10 not in (3, 6, 9)]           # 30 % of the seconds never arrive
    for r in kept:
        lab.step(r)
    last = kept[-1]["fl"]
    assert abs((last - lab._F_ago(1200)) - 60.0) < 0.2                          # 20 minutes = 60 pts (it read 85.6)
    assert abs((last - lab._F_ago(120)) - 6.0) < 0.2 and abs((last - lab._F_ago(10)) - 0.5) < 0.11
    assert lab._F_ago(7000) is None                                             # further back than the history
    w = lab._fm_since(1200)
    assert 800 < len(w) < 860 and abs(min(w) - (last - 60.0)) < 0.2             # 20 minutes of samples, not 1,200 of them
    s = lab.panel()["stand"]
    assert s["ok"] and any(f["k"] == "move20" and "+60 pts in 20 min" in f["text"] for f in s["facts"]), s["facts"]


def test_sister_lead_reads_both_at_the_same_two_times_and_refuses_a_stretched_window():
    lab = C.Lab(n_paths=100)
    rows = TL.tape(1300, drift=0.0, vol=0.0, seed=1)                            # the Nifty future does not move
    for k, r in enumerate(rows):
        up = 1.0 + 0.0004 * max(0, k - 1289) / 10.0                             # both sisters +0.04 % in the last 10 s
        lab.step(dict(r, sis=(55000.0 * up, 24000.0 * up)))
    sl = lab.sister_lead(rows[-1]["t"], rows[-1]["fl"])
    assert sl is not None and abs(sl["sis_pts"] - 10.0) < 0.2 and abs(sl["fut_pts"]) < 0.01 and sl["lead_pts"] > 9
    lab.sis_ring[-11] = (rows[-1]["t"] - 15.0,) + tuple(lab.sis_ring[-11][1:])   # skipped seconds: 15 s under a 10-s label
    assert lab.sister_lead(rows[-1]["t"], rows[-1]["fl"]) is None


def test_banknifty_is_never_mixed_from_two_sources():
    import numpy as np
    from apex.forecast_lab import live as LV
    snap = dict(bid=np.array([55199.0, 0.0, 0.0]), ask=np.array([55201.0, 0.0, 0.0]), ltp=np.array([55200.0, 55050.0, 24000.0]))

    def ages(a):
        return lambda ids: np.array([a[int(i)] for i in ids], float)
    assert LV.sister_prices(snap, (0, 1, 2), ages([1.0, 1.0, 1.0])) == (55200.0, 24000.0)
    bn, fn = LV.sister_prices(snap, (0, 1, 2), ages([9.0, 1.0, 1.0]))            # the future is stale, the index is fresh
    assert np.isnan(bn) and fn == 24000.0                                         # no silent switch to the index (150 pts)
    crossed = dict(snap, bid=np.array([55202.0, 0.0, 0.0]))
    assert np.isnan(LV.sister_prices(crossed, (0, 1, 2), ages([1.0, 1.0, 1.0]))[0])
    assert LV.sister_prices(snap, (None, 1, 2), ages([1.0, 1.0, 1.0]))[0] == 55050.0   # no future in the table: the index, all day
