"""Stage 2 (docs/28 §13): the weather photograph. The LEAK TEST by arrival time: data that arrives after the moment a
photo describes can never change it. Plus the factor definitions (R-002's ER60, R-003's breadth) and the hook."""
import os
import random
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.engine import paper, weather  # noqa: E402
from apex.engine.weather import Weather  # noqa: E402

T_OPEN = datetime(2026, 11, 6, 9, 15, tzinfo=config.IST).timestamp()


def _fill(w, t0, t1, seed=1, hw=True, vix=True):
    """Feed w with 1-Hz spot / heavyweights and a VIX every 30 s from t0 to t1 (a seeded random walk)."""
    rng = random.Random(seed)
    sp, px = 24000.0, np.linspace(100, 3000, 23)
    for k in range(int(t1 - t0) + 1):
        t = t0 + k
        rng.seed(seed * 1_000_003 + int(t))          # the path depends on t only, so two feeds agree where they overlap
        sp += rng.gauss(0.05, 1.2)
        px = px * (1 + np.array([rng.gauss(0, 4e-4) for _ in range(23)]))
        w.feed_spot(t, sp)
        if hw:
            w.feed_hw(t, px, np.ones(23))
        if vix and k % 30 == 0:
            w.feed_vix(13.0 + 0.01 * (k // 30), int(t * 1e9))
    return w


def test_leak_by_arrival_time_base():
    """The base at T is identical whether the histories stop at T or run on to T + 300 s: nothing after T is read."""
    T = T_OPEN + 2 * 3600 + 0.0
    a = _fill(Weather("2026-11-06"), T_OPEN, T)
    b = _fill(Weather("2026-11-06"), T_OPEN, T + 300)
    ba, bb = a.base(T), b.base(T)
    assert ba == bb
    assert ba["er60"] is not None and ba["breadth_up"] is not None and ba["vix"] is not None   # the test is not vacuous
    for t in (T - 0.5, T - 61, T - 1800):            # also at earlier moments, including between samples
        a2 = _fill(Weather("2026-11-06"), T_OPEN, T + 300)
        b2 = _fill(Weather("2026-11-06"), T_OPEN, t)
        assert a2.base(t) == b2.base(t), t


def test_leak_by_arrival_time_each_function():
    rng = random.Random(7)
    ts = [T_OPEN + k for k in range(5000)]
    ps = [24000 + rng.gauss(0, 30) for _ in ts]
    t = ts[4000] + 0.3
    cut = sum(1 for x in ts if x <= t)
    for fn in (lambda T, P: weather.er_window(T, P, t), lambda T, P: weather.er_day(T, P, t),
               lambda T, P: weather.speed(T, P, t), lambda T, P: weather.value_at(T, P, t)):
        full, trunc = fn(ts, ps), fn(ts[:cut], ps[:cut])
        assert full == trunc
        noisy = ps[:cut] + [p + 500 for p in ps[cut:]]   # wild prints after t change nothing
        assert fn(ts, noisy) == trunc


def test_er60_matches_the_r002_definition():
    ts = [T_OPEN + k for k in range(4000)]
    up = [24000 + 0.1 * k for k in range(4000)]           # a straight line: efficiency 1, direction up
    er, d = weather.er_window(ts, up, ts[-1])
    assert abs(er - 1.0) < 1e-9 and d == 1
    zig = [24000 + (5 if (k // 60) % 2 else 0) for k in range(4000)]   # back and forth each minute: net ~0
    er, d = weather.er_window(ts, zig, ts[-1])
    assert er is not None and er < 0.05
    gap = ts[:1000] + ts[1100:]                           # a 100-s hole inside the hour: undefined, never guessed
    assert weather.er_window(gap, up[:1000] + up[1100:], ts[-1] - 1500) == (None, None)


def test_breadth_matches_the_r003_definition():
    w = Weather("2026-11-06")
    a0 = np.array([100.0, 200, 300, 400])
    w.feed_hw(T_OPEN, a0, [1, 1, 1, 2])
    a1 = np.array([101.0, 199, 300, 404])                 # up, down, unchanged, up (weight 2)
    for k in range(1, 301):
        w.feed_hw(T_OPEN + k, a0 + (a1 - a0) * k / 300.0, [1, 1, 1, 2])
    up, dn, n = weather.breadth(w.hw_t, w.hw_a, w.hw_w, T_OPEN + 300)
    assert n == 4 and abs(up - 3 / 5) < 1e-9 and abs(dn - 1 / 5) < 1e-9   # unchanged counts in the denominator only
    assert weather.breadth(w.hw_t, w.hw_a, w.hw_w, T_OPEN + 100) == (None, None, 0)    # no price 300 s back yet


def _ctx(t, w, rr="CE"):
    dt = datetime.fromtimestamp(t, config.IST)
    o = {"key": f"NIFTY|OPT|2026-11-10|24500|{rr}", "id": 3, "strike": 24500.0, "rr": rr, "ltp": 100.0,
         "bid": 99.5, "ask": 100.5, "expiry": "2026-11-10", "delta": 0.55 if rr == "CE" else -0.55,
         "theta_min": -0.11, "age": 0.0}
    ctx = {"now_s": t, "now_dt": dt, "w0": "2026-11-10", "spot": 24050.0, "by_key": {o["key"]: o}, "blackout": {},
           "episode": {"id": 7}, "advisors": {}, "fut": 24060.0, "domino": {}, "regime": {},
           "day": {"hi": 24100.0, "lo": 24000.0, "pos_in_range": 0.5, "give": 0.5, "range_on": False,
                   "or_hi": 24080.0, "or_lo": 24020.0, "or_done": True, "or_late": False},
           "edge": {"wall_up": 120.0, "wall_dn": 60.0},
           "straddle_watch": {"chg5": 4.0, "excess": 1.5, "state": "EXPANDING"},
           "weather": w.base(t)}
    return ctx, o


def test_photo_direction_and_contract_fields():
    T = T_OPEN + 2 * 3600
    w = _fill(Weather("2026-11-06"), T_OPEN, T)
    ctx, o = _ctx(T, w, "CE")
    ce = weather.photo(ctx, +1, o)
    pe = weather.photo(ctx, -1, dict(o, delta=-0.55))
    assert ce["wall_room"] == 120.0 and pe["wall_room"] == 60.0
    assert ce["breadth_dir"] == ctx["weather"]["breadth_up"] and pe["breadth_dir"] == ctx["weather"]["breadth_dn"]
    assert ce["dir60"] == -pe["dir60"]
    assert ce["pos_dir"] == 0.5 and ce["or_pos"] == 0.5 and ce["dist_hi"] == 50.0
    assert ce["dte"] == 4 and ce["expiry_day"] is False and ce["phase"] == "CTS" and ce["mins_open"] == 120.0
    assert abs(ce["theta_be"] - 0.11 / 0.55) < 1e-3 and ce["strad_expanding"] is True
    nil = weather.photo(ctx, +1, None)                    # no contract (a missed fire): theta fields undefined
    assert nil["theta_be"] is None and nil["theta_ratio"] is None
    import json
    json.dumps(ce, allow_nan=False)                       # JSON-clean (saved in paper/<day>.json)


def test_the_hook_takes_the_photo_at_the_trigger(monkeypatch):
    monkeypatch.setattr(config, "FILL_NEXT_PRINT", True)
    T = T_OPEN + 2 * 3600
    w = _fill(Weather("2026-11-06"), T_OPEN, T + 5)
    b = paper.Book("m2.0_s0.5", {}, "2026-11-06")
    ctx, o = _ctx(T, w)
    paper.request_entry(b, ctx, o, "t")
    wt = b.ctl["pending_entry"]["weather_trig"]
    assert wt is not None and wt["er60"] == ctx["weather"]["er60"]
    ctx1, o1 = _ctx(T + 1, w)                             # the fill a second later sees a newer base ...
    pos, _ = paper.try_fill_entry(b, ctx1)
    assert pos is not None and pos["weather_trig"] == wt  # ... but the position keeps the trigger's photo


def test_missing_data_is_none_not_zero():
    w = Weather("2026-11-06")
    w.feed_spot(T_OPEN, 24000.0)
    b = w.base(T_OPEN + 1)
    assert b["er60"] is None and b["breadth_up"] is None and b["vix"] is None and b["speed15"] is None
    p = weather.photo({"now_dt": datetime.fromtimestamp(T_OPEN, config.IST), "weather": b}, 1, None)
    assert p["er60"] is None and p["breadth_dir"] is None and p["wall_room"] is None


def test_the_real_engine_feeds_and_publishes_the_base():
    """The engine wiring: a real Engine on a private table feeds the histories once a second and puts the base in
    ctx, with no fault logged under the weather names."""
    import test_wp2
    rig = test_wp2.Rig("weather", "2026-10-21")
    try:
        faults = []
        real = rig.eng._fault
        rig.eng._fault = lambda name: (faults.append(name), real(name))
        rig.warm()
        rig.step(25215.0, 50)
        w = rig.eng.weather
        assert w is not None and len(w.hw_t) >= 20 and len(w.spot_t) >= 20
        assert "breadth_n" in (rig.eng.ctx.get("weather") or {})
        assert not [f for f in faults if "weather" in f], faults
    finally:
        rig.t.close(); rig.blob.close(); rig.t.unlink(); rig.blob.unlink()
