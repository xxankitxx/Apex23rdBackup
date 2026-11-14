"""14 Nov (docs/57): the pre-expiry thrust books, the 15-minute stall twin, the shadow Conductor that pools them, the
live sister / heavyweight rows of LiveDay, and the fastlab maths. All shadow: the live Conductor and its pool are
untouched."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config, fastlab as FL  # noqa: E402
from apex.engine import conductor as cond  # noqa: E402
from apex.engine.council import LiveDay, c20_9y, c20_9y_st15, thr_d1, thr_hw, thr_sis  # noqa: E402

NEW = ["thr_sis", "thr_hw", "st15_c20_9y", "conductor_d1"]


def test_sessions_to_expiry_uses_the_trading_calendar():
    f = thr_d1.days_to_expiry
    assert f("2026-11-17", "2026-11-17") == 0
    assert f("2026-11-16", "2026-11-17") == 1                      # Monday before a Tuesday expiry
    assert f("2026-11-13", "2026-11-17") == 2                      # Friday: Monday and Tuesday are left
    assert f("2026-11-12", "2026-11-17") == 3
    assert f("2026-11-06", "2026-11-09") == 1                      # Friday before a Monday expiry (holiday week)


def test_registered_last_as_twins_and_not_in_the_live_pool():
    names = list(config.VARIANTS)
    i = names.index(NEW[0])
    assert names[i:i + 4] == NEW and config.validate() == []      # later shadows may follow (docs/58)
    assert all(config.VARIANTS[n].get("twin") for n in NEW)
    pool = [e["book"] for e in cond.active_entries(cond.load_pool(), "2026-11-16")]
    assert not set(NEW) & set(pool)
    live = cond.Conductor("2026-11-16", names)
    assert not {m["book"] for m in live.members} & set(NEW)
    d1 = cond.AdaptiveConductor("2026-11-16", names, "prexp", "conductor_d1")
    assert [m["book"] for m in d1.members][-2:] == ["thr_sis", "thr_hw"]            # last on a same-tick tie
    assert [m["book"] for m in d1.members][:-2] == [m["book"] for m in live.members]
    assert d1.admit(d1.members[0], {"key": "NIFTY|OPT|2026-11-17|25000|CE"}, None, {}, {"now_s": 0.0}) is None
    assert cond.offline_admit("prexp")(0.0, None, {}, [], {}) is None


def _day(day, exp, n=2000):
    D = LiveDay(day, exp)
    D.K = np.array([25000.0, 25000.0, 24950.0, 25050.0])
    D.rr = np.array(["CE", "PE", "CE", "PE"])
    D.col = {(25000, "CE"): 0, (25000, "PE"): 1, (24950, "CE"): 2, (25050, "PE"): 3}
    D.fwd[:n] = 25010.0
    for j, (b, dl) in enumerate(((120.0, 0.53), (125.0, -0.49), (150.0, 0.62), (155.0, -0.60))):
        D.bid[:n, j], D.ask[:n, j], D.age[:n, j] = b, b + 0.5, 0.5
        D.delta[:n, j], D.gamma[:n, j], D.theta[:n, j], D.iv[:n, j] = dl, 0.001, -0.05, 12.0
    D.bnf[:n], D.fin[:n] = 58000.0, 27000.0
    D.hwl = np.tile(np.log(np.array([1000.0, 1500.0, 1300.0], dtype=np.float32)), (len(D.fwd), 1))
    D.hww = np.array([10.0, 9.0, 7.5])
    return D


def _run(D, cls, upto):
    s = cls()
    out = []
    for i in range(upto):
        D.i = i
        a = s.on_second(i, D, None)
        if a:
            out.append((i, a))
    return s, out


def test_sister_thrust_buys_only_on_the_session_before_expiry():
    for day, want in (("2026-11-16", True), ("2026-11-13", False), ("2026-11-17", False)):
        D = _day(day, "2026-11-17")
        up = 1 + 12.0 / 25010.0                                   # both sisters +12 Nifty-equivalent points in a minute
        D.bnf[1500:2000] = 58000.0 * up
        D.fin[1500:2000] = 27000.0 * up
        s, out = _run(D, thr_sis.Strategy, 1700)
        buys = [(i, a) for i, a in out if a[0] == "BUY"]
        if want:
            assert len(buys) == 1 and buys[0][0] == 1500 and buys[0][1][2] == "CE" and "THR sisters" in buys[0][1][3], out
            assert buys[0][1][1] == 25000                          # |delta| >= 0.52 nearest 0.52
            assert s.thr_dte == 1 and s.thr_log[0][4] is True
        else:
            assert buys == [], (day, out)


def test_one_sister_alone_is_not_a_thrust_and_a_down_thrust_buys_a_put():
    D = _day("2026-11-16", "2026-11-17")
    D.bnf[1500:2000] = 58000.0 * (1 + 12.0 / 25010.0)             # FINNIFTY did not move
    assert [a for _, a in _run(D, thr_sis.Strategy, 1700)[1] if a[0] == "BUY"] == []
    D = _day("2026-11-16", "2026-11-17")
    dn = 1 - 12.0 / 25010.0
    D.bnf[1500:2000], D.fin[1500:2000] = 58000.0 * dn, 27000.0 * dn
    buys = [a for _, a in _run(D, thr_sis.Strategy, 1700)[1] if a[0] == "BUY"]
    assert len(buys) == 1 and buys[0][2] == "PE" and buys[0][1] == 25050


def test_heavyweight_thrust_needs_the_move_and_the_breadth():
    D = _day("2026-11-16", "2026-11-17")
    D.hwl[1500:] += np.float32(np.log(1 + 12.0 / 25010.0))        # every stock up: 12 points, breadth 1
    buys = [(i, a) for i, a in _run(D, thr_hw.Strategy, 1700)[1] if a[0] == "BUY"]
    assert len(buys) == 1 and buys[0][0] == 1500 and buys[0][1][2] == "CE" and "heavyweights" in buys[0][1][3]
    D = _day("2026-11-16", "2026-11-17")
    D.hwl[1500:, 0] += np.float32(np.log(1 + 40.0 / 25010.0))     # one stock carries it, the others fall a little
    D.hwl[1500:, 1:] -= np.float32(np.log(1 + 1.0 / 25010.0))
    s, mv, b = thr_d1.heavy_thrust(1510, D)
    assert s == 0 and mv > 8 and b < 0.5
    assert [a for _, a in _run(D, thr_hw.Strategy, 1700)[1] if a[0] == "BUY"] == []


def test_one_thrust_per_side_per_gap():
    D = _day("2026-11-16", "2026-11-17", n=3000)
    up = 1 + 12.0 / 25010.0
    D.bnf[1500:3000], D.fin[1500:3000] = 58000.0 * up, 27000.0 * up
    D.bnf[1700:3000], D.fin[1700:3000] = 58000.0 * up * up, 27000.0 * up * up     # a second up-thrust 200 s later
    D.bnf[2200:3000], D.fin[2200:3000] = 58000.0 * up ** 3, 27000.0 * up ** 3     # and a third 700 s after the first
    s, out = _run(D, thr_sis.Strategy, 2400)
    assert [i for i, a in out if a[0] == "BUY"] == [1500, 2200]     # the second is inside GAP seconds: no signal
    assert [r[0] for r in s.thr_log] == [1500, 2200]
    assert thr_d1.T["GAP"] == 600 and thr_d1.T["L"] == 60


def _held(cls, day, exp, bids, i_in=1300):
    D = _day(day, exp, n=i_in + len(bids) + 5)
    s = cls()
    for r in range(i_in):
        D.i = r
        s.on_second(r, D, None)
    pos = {"rr": "CE", "strike": 25000.0, "j": 0, "i_in": i_in, "entry": 100.0, "qty": 65, "peak_bid": 100.0, "st": {}}
    for k, b in enumerate(bids):
        i = i_in + k
        D.bid[i, 0], D.ask[i, 0] = b, b + 0.5
        D.i = i
        pos["peak_bid"] = max(pos["peak_bid"], b)
        a = s.on_second(i, D, pos)
        if a and a[0] == "SELL":
            return k, a[1]
    return None


def test_stall_sells_a_non_mover_at_15_minutes_not_before_and_never_a_mover():
    flat = [100.0 + 0.5 * np.sin(k / 30.0) for k in range(1100)]
    hit = _held(c20_9y_st15.Strategy, "2026-11-13", "2026-11-17", flat)
    assert hit is not None and hit[1] == "STALL" and hit[0] == 900, hit
    assert _held(c20_9y.Strategy, "2026-11-13", "2026-11-17", flat) is None
    was_up = [100.0 + min(k, 60) * 0.2 for k in range(200)] + [112.0 - min(k, 200) * 0.05 for k in range(900)]   # peaked +12 %
    hit = _held(c20_9y_st15.Strategy, "2026-11-13", "2026-11-17", was_up)
    assert hit is None or hit[1] != "STALL", hit
    down = [100.0 - min(k, 300) * 0.02 for k in range(1100)]                       # sits 6 % under: not within the band
    hit = _held(c20_9y_st15.Strategy, "2026-11-13", "2026-11-17", down)
    assert hit is None or hit[1] != "STALL", hit


def test_live_day_writes_fresh_peers_and_keeps_the_last_good_value():
    class Dm:
        eq_ids = np.array([3, 4]); eq_w = np.array([0.6, 0.4])

    class Eng:
        key = {"BANKNIFTY|FUT": 1, "FINNIFTY|SPOT": 2}; domino = Dm(); fwd = None; _fwd_t = None; greek = {}

    D = LiveDay("2026-11-16", "2026-11-17")
    now = D.t_open + 100
    snap = {"recv_ns": np.array([0, now * 1e9 - 1e9, now * 1e9 - 2e9, now * 1e9 - 3e9, now * 1e9 - 40e9]), "bid": np.array([0, 58000.0, 0, 0, 0]),
            "ask": np.array([0, 58002.0, 0, 0, 0]), "ltp": np.array([0, 58001.0, 27000.0, 1000.0, 1500.0])}
    D.put(100, Eng(), {"now_s": now, "options": []}, "2026-11-17", snap)
    assert D.bnf[100] == 58001.0 and D.fin[100] == 27000.0
    assert np.isclose(D.hwl[100, 0], np.log(1000.0)) and np.isnan(D.hwl[100, 1])   # the second stock is 40 s old
    snap["recv_ns"] = snap["recv_ns"] - 60e9                                        # a minute later nothing is fresh
    D.put(102, Eng(), {"now_s": now + 2, "options": []}, "2026-11-17", snap)
    assert D.bnf[102] == 58001.0 and D.fin[101] == 27000.0 and np.isclose(D.hwl[102, 0], np.log(1000.0))
    D.put(103, Eng(), {"now_s": now + 3, "options": []}, "2026-11-17", None)        # no snapshot: nothing breaks
    assert D.bnf[103] == 58001.0


def test_fastlab_maths():
    F, K, T = 25000.0, np.array([24900.0, 25000.0, 25100.0]), 2.0 / 365.0
    for call in (True, False):
        px = FL.b76(F, K, T, 0.14, call)
        assert np.allclose(FL.iv_of(F, K, T, px, call), 0.14, atol=1e-4)
    dc, g, th = FL.greeks(F, K, T, 0.14, True)
    dp, _, _ = FL.greeks(F, K, T, 0.14, False)
    assert np.allclose(dc - dp, 1.0) and (g > 0).all() and (th < 0).all() and dc[0] > dc[1] > dc[2]
    assert np.allclose(FL.b76(F, K, T, 0.14, True) - FL.b76(F, K, T, 0.14, False), F - K)
    e = 100.0
    fl = FL._floor(e, np.array([0.10, 0.15, 0.25, 0.50, 1.00]), "ramp")
    assert np.isnan(fl[0]) and fl[1] == e and np.isclose(fl[2], e * (1 + 0.25 * 0.45)) and np.isclose(fl[3], e * 1.35) and np.isclose(fl[4], e * 1.7)
    fx = FL._floor(e, np.array([0.10, 0.20, 0.60]), "pex")
    assert np.isnan(fx[0]) and fx[1] == e and np.isclose(fx[2], e * 1.42)
    assert FL.hm(0) == "09:15" and FL.row_of("15:20") == FL.T_FLAT and FL.N == 22501
