"""Offline checks: python -m pytest tests  (or python tests/test_core.py)."""
import json
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

import numpy as np  # noqa: E402

from apex import config, greeks  # noqa: E402
config.FILL_NEXT_PRINT = False   # D-126: these suites test the exit/entry logic itself on same-step fills; D-126 has its own suite
from apex.engine import learning, paper  # noqa: E402
from apex.feed_core import Registry, apply_packet  # noqa: E402
from apex.table import Table  # noqa: E402


def test_calendar():
    n = datetime(2026, 10, 17, 10, 0, tzinfo=config.IST)
    w = config.weekly_expiries(n, 2)
    assert w[0].isoformat() == "2026-10-19"          # Tue 20 Oct is Dussehra -> Mon 19
    assert w[1].isoformat() == "2026-10-27"
    assert config.ws_expiry(w[0]) == "19-Oct-2026"


def test_apply_packet_segments():
    t = Table(create=True, name="apex_test_tbl")
    try:
        reg = Registry()
        eq = reg.add("HDFCBANK|EQ", "eq", "HDFCBANK", "4.1!1333", seg="eq")
        fo = reg.add("NIFTY|FUT", "fut", "NIFTY", "4.1!1333", seg="fo")   # same number, other segment
        bt = reg.by_token
        q_eq = ["4.1!1333", 1700, 1712.5, 1720, 1690, 0.5, 1712.4, 100, 1712.6, 120, 5, 1705,
                900000, 5000, 6000, 0, "", 0, 0, 1760000000, 1700]
        q_fo = ["4.1!1333", 25000, 25210, 25300, 24990, 0.4, 25209, 75, 25211, 150, 75, 25100,
                14500000, 1000, 2000000, 4000, 5000, 0, "", 0, 0, 1760000000, 25100]
        assert apply_packet(t, bt, q_eq, 1) == eq
        assert apply_packet(t, bt, q_fo, 2) == fo
        assert t.rows["ltp"][eq] == 1712.5 and t.rows["ttq"][eq] == 900000
        assert t.rows["ltp"][fo] == 25210 and t.rows["oi"][fo] == 14500000 and t.rows["ttq"][fo] == 2000000
        old = list(q_fo); old[14] = 1999000; old[2] = 25209
        assert apply_packet(t, bt, old, 3) == fo and t.rows["ttq"][fo] == 2000000   # volume never steps back (D-095)
        d = ["4.2!1333", 1760000000, [[25209, 75, 1, "N", 25211, 150, 2, "N"]] * 5]
        assert apply_packet(t, bt, d, 4) == fo and t.rows["bq"][fo][0] == 75
    finally:
        t.close(); t.unlink()


def test_previous_session_snapshot_does_not_freeze_the_quote():
    """D-095, live 19 Oct 2026: Breeze's first packet after connect is Friday's last quote with
    Friday's whole-day volume (305 M); today's packets start near 22 k. They must be applied."""
    t = Table(create=True, name="apex_test_tbl2")
    try:
        reg = Registry()
        ce = reg.add("NIFTY|OPT|2026-10-19|23050|CE", "opt", "NIFTY", "4.1!47164", seg="fo")
        bt = reg.by_token
        fri = ['4.1!47164', 97, 112.2, 165.5, 47.6, 66.84, 111.3, 780, 112.3, 520, 65, 110.88, 3520140, '',
               305082635, 144105, 251615, '338275.63C', '', 0.05, 943.45, 1792145400, 67.25]
        mon = ['4.1!47164', 138.5, 134.65, 138.75, 129.15, 11.65, 133.45, 650, 134.65, 455, 65, 133.72, 3520140, '',
               22035, 1035580, 30420, '29.47C', '+', 0.05, 943.45, 1792381501, 120.6]
        assert apply_packet(t, bt, fri, 1) == ce and t.rows["ltp"][ce] == 112.2
        # the 09:15:00 packet: today's stamp but still Friday's volume, then the counter resets
        open_ = list(mon); open_[2] = 136.0; open_[14] = 305082635; open_[21] = 1792381500
        assert apply_packet(t, bt, open_, 1) == ce and t.rows["ltp"][ce] == 136.0
        assert apply_packet(t, bt, mon, 2) == ce and t.rows["ltp"][ce] == 134.65      # was dropped all day
        later = list(mon); later[2] = 133.0; later[14] = 64025; later[21] = 1792381503
        assert apply_packet(t, bt, later, 3) == ce and t.rows["ltp"][ce] == 133.0
        # same day, stamped 1 s earlier with MORE volume (Breeze jitter): newer, applied
        newer = list(later); newer[2] = 131.0; newer[14] = 70000; newer[21] = 1792381502
        assert apply_packet(t, bt, newer, 5) == ce and t.rows["ltp"][ce] == 131.0
        # a reordered packet with less volume: its book fields apply, volume never steps back
        back = list(newer); back[6] = 130.0; back[14] = 65000
        assert apply_packet(t, bt, back, 6) == ce and t.rows["ttq"][ce] == 70000 and t.rows["bid"][ce] == 130.0
        # a packet 3 s older than the held quote: book fields only, the price stays
        old3 = list(newer); old3[2] = 90.0; old3[21] = 1792381499
        assert apply_packet(t, bt, old3, 7) == ce and t.rows["ltp"][ce] == 131.0
        # a depth packet must not make the quote look fresh (D-096)
        rn = int(t.rows["recv_ns"][ce])
        prev = list(fri); prev[2] = 50.0                                                  # Friday again: stale
        assert apply_packet(t, bt, prev, 8) == -1 and t.rows["ltp"][ce] == 131.0
        d = ["4.2!47164", 1792381510, [[130, 65, 1, "N", 131, 65, 1, "N"]] * 5]
        assert apply_packet(t, bt, d, 99) == ce and int(t.rows["recv_ns"][ce]) == rn and t.rows["depth_ns"][ce] == 99
    finally:
        t.close(); t.unlink()


def test_greeks_roundtrip():
    F, T = 25200.0, 5 / 365
    K = np.array([25000., 25200., 25400.])
    c = np.array([True, True, False])
    px = greeks.b76_price(F, K, T, 0.13, c)
    iv = greeks.implied_vol(px, F, K, T, c)
    assert np.allclose(iv, 0.13, atol=1e-4)
    g = greeks.greeks(F, K, T, iv, c)
    assert 0.45 < g["delta"][1] < 0.55 and g["theta_min"][1] < 0


def test_paper_sizing_and_exit():
    b = paper.Book("x", config.TRIGGER, "2026-10-19")
    now = datetime(2026, 10, 21, 10, 0, tzinfo=config.IST)
    ep = {"id": 1, "dir": 1, "type": "BASKET-LED"}
    ctx = {"now_s": 0, "now_dt": now, "fut": 25200.0, "advisors": {}, "episode": ep}
    opt = {"id": 5, "key": "k", "strike": 25150, "rr": "CE", "expiry": "2026-10-27", "ltp": 150.0}
    pos = paper.open_trade(b, ctx, opt, "test")
    assert pos["lots"] == int(100000 // (150 * 65)) == 10
    ctx2 = dict(ctx, fut=25200 - 12.5, now_s=30, by_id={5: dict(opt, ltp=142.0, age=0.2)},
                domino={"S_up": 0, "S_dn": 0, "z": 0})
    t = paper.check_exit(b, ctx2)
    assert t and t["reason"] == "STOP" and t["pnl_rs"] == -8 * 650 and b.capital == 100000 - 5200
    assert abs(t["ret_pct"] - (-8 / 150 * 100)) < 1e-3                 # D-064: the learning unit


def test_learning_sprt():
    days = {}
    for i in range(12):
        day = f"2026-11-{i + 1:02d}"
        books = {}
        for name in list(config.VARIANTS) + ["RAW"]:
            b = paper.Book(name, config.VARIANTS.get(name, config.TRIGGER), day)
            edge = 6.0 if name == "m2.5_s0.6" else -2.0
            b.trades = [{"pnl_pts": edge + (k % 3 - 1), "pnl_rs": 0, "advisors": {"room": {"veto": k % 4 == 0}},
                         "reason": "STOP", "time_in": "10:00:00"} for k in range(4)]
            books[name] = b
        learning.record_day(day, books)
        s = learning.learn(day)
    assert s["champion"] != config.CHAMPION_DEFAULT        # the losing champion was replaced
    assert os.path.exists(learning.REPORT)


def test_flow_orders_and_lead():
    """Order-count classes and the book-leads-price score: sellers' ORDERS pulled (not eaten)
    while price rises must read PULLED on the order series and give a positive run score."""
    from apex.engine.flow import Flow, CLS
    from apex.engine.market import Market
    import numpy as np
    from apex.table import ROW_DTYPE
    m = Market(); f = Flow(config.MAX_ROWS)
    snap = np.zeros(config.MAX_ROWS, dtype=ROW_DTYPE)
    i = 7
    for step in range(700):                                   # 70 s at 10 Hz
        t = step / 10.0
        snap = snap.copy()
        px = 100.0 + (max(0.0, t - 55.0) * 1.0)              # price runs in the last 15 s
        snap["ltp"][i] = px; snap["bid"][i] = px - 0.05; snap["ask"][i] = px + 0.05
        snap["ttq"][i] = 1000 + step * 2                      # a trickle of volume only
        sell_orders = 40 if t < 55 else max(5, 40 - int((t - 55) * 4))   # sellers cancel fast
        snap["bq"][i] = [500] * 5; snap["bo"][i] = [20] * 5
        snap["aq"][i] = [sell_orders * 25 / 5] * 5; snap["ao"][i] = [sell_orders / 5] * 5
        snap["depth_ns"][i] = 1; snap["tbq"][i] = 50000; snap["tsq"][i] = 30000
        m.push(snap, t); f.update(m, 0.1)
    assert CLS[int(f.cls_so[i])] in ("PULLED", "DRAIN-FAST"), CLS[int(f.cls_so[i])]
    assert f.imb_o[i] > 0.5 and f.imb_t[i] > 0.2
    assert f.run_score(i, 1, m) > 0.3
    assert -1 <= f.lead[i] <= 1


def test_straddle_watch_spike_and_roll():
    """The owner's straddle idea: pure theta decay is no spike; a directional move whose
    CE leg rises faster than theta while the PE falls is a SPIKE CE (gamma leg CE), the
    advisor vetoes a PE entry and accepts a CE one; after spot settles at the next
    strike the watch re-anchors and logs the roll."""
    from datetime import datetime, timedelta
    from apex.engine.straddle_watch import StraddleWatch
    w = StraddleWatch()
    t0, dt0, K = 1792380900.0, datetime(2026, 10, 19, 9, 15, tzinfo=config.IST), 25200
    g0 = {"CE": {"delta": 0.50, "gamma": 0.0021, "theta_min": -0.30}, "PE": {"delta": -0.50, "gamma": 0.0021, "theta_min": -0.30}}

    def step(t, ce, pe, atm=K, g=g0, fut=25200.0):
        w.update(t0 + t, dt0 + timedelta(seconds=t), atm,
                 {"CE": (ce, ce - .1, ce + .1), "PE": (pe, pe - .1, pe + .1)}, g, fut, 100.0)
    for t in range(600):                                      # 10 min of theta only
        step(t, 45.0 - 0.30 * t / 60, 45.0 - 0.30 * t / 60)
    assert w.spike is None and w.state in ("DECAYING", "FLAT"), w.state
    for t in range(600, 720):                                 # futures +40 in 2 min: CE +14, PE −8
        k = (t - 600) / 120
        g = {"CE": {"delta": 0.50 + 0.18 * k, "gamma": 0.0021, "theta_min": -0.30},
             "PE": {"delta": -0.50 + 0.18 * k, "gamma": 0.0019, "theta_min": -0.30}}
        step(t, 42.0 + 14 * k, 42.0 - 8 * k, g=g, fut=25200 + 40 * k)
    assert w.spike and w.spike["leg"] == "CE" and w.state == "SPIKE CE"
    assert w.legs["CE"]["ddelta"] > 0.03 and w.spike["fut_move"] > 0
    assert w.advise(-1)[0] is True and w.advise(+1)[0] is False
    assert w.drain_events()[0][0] == "SPIKE"
    for t in range(720, 1330):                                # spot settles one strike up
        step(t, 56.0, 34.0, atm=25250, fut=25240)
        if w.wants_roll():
            w.roll(t0 + t, dt0 + timedelta(seconds=t), 25250, {"CE": (40.0, 39.9, 40.1), "PE": (41.0, 40.9, 41.1)})
    assert w.K == 25250 and w.shifts[-1]["from"] == 25200 and w.spike is None
    assert w.drift_min is None and w.state == "WARMING"      # measured on the new strike only
    v = w.view()
    assert v["series"] and v["spikes"][0]["ended"] and "t_s" in v["spikes"][0]


def test_gex_map_regime_walls_flip():
    """Call-heavy chain -> DAMPEN with the call wall at the heavy strike; put-heavy -> AMPLIFY;
    heavy calls above and heavy puts below produce a flip level between them; the advisor vetoes
    chasing into a dampening regime and a close gamma wall."""
    from datetime import datetime
    from apex.engine.gex import GexMap
    now = datetime(2026, 10, 19, 10, 0, tzinfo=config.IST)
    F, ks = 25200.0, [25000 + 50 * i for i in range(9)]            # 25000 .. 25400
    def chain(ce, pe):
        return {str(k): {"call": c, "put": p} for k, c, p in zip(ks, ce, pe)}
    flat = [10000] * 9
    g = GexMap()
    calls = [10000] * 9; calls[6] = 90000                           # wall at 25300
    v = g.compute(chain(calls, flat), "2026-10-27", now, F, {}, 0.13)
    assert v["ok"] and v["regime"] == "DAMPEN" and v["balance"] > 0.1 and v["call_wall"] == 25300.0
    puts = [10000] * 9; puts[2] = 90000                             # heavy puts at 25100
    v2 = g.compute(chain(flat, puts), "2026-10-27", now, F, {}, 0.13)
    assert v2["regime"] == "AMPLIFY" and v2["balance"] < -0.1 and v2["put_wall"] == 25100.0
    both = g.compute(chain(calls, puts), "2026-10-27", now, F, {}, 0.13)
    assert both["flip"] is not None and 24900 < both["flip"] < 25500
    assert 25000 <= both["max_pain"] <= 25400
    g.v = v
    assert g.advise(+1, F)[0] is True                               # dampening, no flip ahead: do not chase
    assert g.advise(+1, 25290.0)[0] is True                         # 10 pts under a call wall: do not chase
    g.v = v2
    assert g.advise(+1, F)[0] is False                              # amplifying, calls flat -> no call wall
    assert v2["call_wall"] is None
    g.v = both                                                      # flip just ahead -> the escape applies
    if both["regime"] == "DAMPEN":
        side = 1 if both["flip"] > F else -1
        assert g.advise(side, both["flip"] - 10 * side)[0] is False
    assert g.compute({}, "2026-10-27", now, F, {}, 0.13)["ok"] is False



# ── external-review fixes (D-063 … D-068) ─────────────────────────────────────
def _reset_learning():
    for f in (learning.STATE, learning.DAYS, learning.REPORT):
        if os.path.exists(f):
            os.remove(f)


def test_guard_states():
    from apex.engine.guard import DataGuard, RESUME_S
    g = DataGuard()
    assert g.on                                                     # starts in blackout
    for t in range(int(RESUME_S)):
        g.update(float(t), 2, 0.2)
    assert g.on                                                     # 19 s fresh: not yet
    g.update(RESUME_S, 2, 0.2)
    assert not g.on                                                 # 20 s fresh: lifted
    g.update(99.0, 2, 4.0, feed_age_s=0.2)                          # D-097: a quiet future, feed alive
    assert not g.on
    g.update(99.5, 2, 4.0, feed_age_s=3.5)                          # nothing on ANY row for 3.5 s: silent
    assert g.on and "silent" in g.reason
    g.update(100.0, 2, 11.0, feed_age_s=0.2)                        # futures alone quiet 11 s
    assert g.on and "stale" in g.reason
    g.update(101.0, 3, None)                                        # RECONNECTING
    assert g.on and "not live" in g.reason
    for t in range(102, 102 + int(RESUME_S) + 1):
        g.update(float(t), 2, 0.1)
    assert not g.on and len(g.gaps) == 1 and g.gaps[0][1] - g.gaps[0][0] > 20
    g.update(200.0, 2, 900.0, in_session=False)                     # quiet futures after the close: fine
    assert not g.on


def test_reconnect_jump_cannot_fire():
    """F1 end to end: a 40-s freeze, then futures and every heavyweight jump together. Without the
    guard this IS a Triangle (big z, full synchrony, fresh episode). With it: the episode is tainted,
    no book can enter, and sigma does not absorb the jump."""
    from datetime import datetime
    from apex.engine.domino import Domino
    from apex.engine.guard import DataGuard
    from apex.engine.market import Market
    from apex.table import ROW_DTYPE
    items = [{"id": 0, "key": "NIFTY|FUT", "kind": "fut", "sym": "NIFTY"}] + \
            [{"id": j, "key": f"S{j}|EQ", "kind": "eq", "sym": f"S{j}", "wn": 10.0} for j in range(1, 6)]
    m, dom, g = Market(), Domino(items, config.MAX_ROWS), DataGuard()
    t0 = datetime(2026, 10, 21, 10, 0, tzinfo=config.IST).timestamp()
    rng = np.random.default_rng(3)
    fut, stk, vol = 25200.0, np.full(5, 1000.0), 0.0
    snap = np.zeros(config.MAX_ROWS, dtype=ROW_DTYPE)
    last_recv, seen = t0, []
    sigma_before = None
    for step in range(int((12 * 60 + 40 + 60) * 10)):              # 12 min live, 40 s frozen, 60 s live
        t = t0 + step / 10.0
        frozen = 12 * 60 <= step / 10.0 < 12 * 60 + 40
        if not frozen:
            dz = rng.normal(0, 0.35)
            fut += dz; stk *= 1 + dz / 25200 + rng.normal(0, 2e-5, 5); vol += 50
            if 12 * 60 + 40 <= step / 10.0 < 12 * 60 + 40.1:      # the resume tick: the outage move lands at once
                fut += 30.0; stk *= 1 + 30.0 / 25200; vol += 50 * 400    # cumulative volume catches up too
            last_recv = t
            snap = snap.copy()
            snap["ltp"][0] = fut; snap["ltp"][1:6] = stk; snap["ttq"][0:6] = vol
        if frozen and sigma_before is None:
            sigma_before = dom.fut_sigma.v
        m.push(snap, t)
        g.update(t, 2, t - last_recv, True)
        dom.update(m, t, learn_scales=not g.on)
        if g.on and dom.episode is not None:
            dom.episode["gap"] = True
        if 12 * 60 + 40 <= step / 10.0 < 12 * 60 + 45:
            seen.append((dom.z, dom.state["S_up"], dom.episode_view(t)))
    zmax = max(z for z, _, _ in seen)
    smax = max(su for _, su, _ in seen)
    assert zmax >= 2.0 and smax >= 0.5, (zmax, smax)               # the artefact really looks like a Triangle
    ev = next(e for _, _, e in seen if e)
    assert ev["gap"] is True                                        # ...but the episode is tainted
    assert abs(dom.fut_sigma.v - sigma_before) < 0.05 * sigma_before                 # the jump did not inflate sigma
    b = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-21")
    ctx = {"now_dt": datetime.fromtimestamp(t0 + 12 * 60 + 41, config.IST), "domino": dict(dom.state, dir=1, z=5.0, S_up=1.0),
           "episode": dict(ev, dir=1), "fut": 25230.0, "advisors": {}, "blackout": {"on": True, "why": "feed stale"}}
    assert paper.evaluate_entry(b, ctx, [])[1].startswith("DATA GAP")
    ctx["blackout"] = {"on": False}
    assert paper.evaluate_entry(b, ctx, [])[1] == "episode began in a data gap"


def test_sigma_frozen_during_blackout():
    from apex.engine.domino import Domino
    from apex.engine.market import Market
    from apex.table import ROW_DTYPE
    from datetime import datetime
    items = [{"id": 0, "key": "NIFTY|FUT", "kind": "fut", "sym": "NIFTY"}]
    m, dom = Market(), Domino(items, config.MAX_ROWS)
    t0 = datetime(2026, 10, 21, 10, 0, tzinfo=config.IST).timestamp()
    snap = np.zeros(config.MAX_ROWS, dtype=ROW_DTYPE)
    for step in range(300):
        snap = snap.copy(); snap["ltp"][0] = 25200 + (step % 7)
        m.push(snap, t0 + step / 10); dom.update(m, t0 + step / 10)
    s0 = dom.fut_sigma.v
    snap = snap.copy(); snap["ltp"][0] = 25300                      # +100 jump while blacked out
    for step in range(300, 600):
        m.push(snap, t0 + step / 10); dom.update(m, t0 + step / 10, learn_scales=False)
    assert dom.fut_sigma.v == s0


def test_exit_waits_for_fresh_quote_and_stays_committed():
    from datetime import datetime
    b = paper.Book("x", config.TRIGGER, "2026-10-21")
    now = datetime(2026, 10, 21, 10, 0, tzinfo=config.IST)
    opt = {"id": 5, "key": "k", "strike": 25150, "rr": "CE", "expiry": "2026-10-27", "ltp": 150.0}
    ctx = {"now_s": 0, "now_dt": now, "fut": 25200.0, "advisors": {}, "episode": {"id": 1, "dir": 1, "type": "BASKET-LED"}}
    paper.open_trade(b, ctx, opt, "test")
    dom = {"S_up": 0, "S_dn": 0, "z": 0}
    stale = dict(opt, ltp=140.0, age=8.0)
    c = dict(ctx, fut=25185.0, now_s=30, by_id={5: stale}, by_key={"k": stale}, domino=dom, fut_age=0.1)
    assert paper.check_exit(b, c) is None and b.pos["pending"]["reason"] == "STOP"   # waits for a fresh quote
    c2 = dict(c, fut=25200.0, now_s=33)                             # futures bounce back above the stop...
    assert paper.check_exit(b, c2) is None and b.pos["pending"]     # ...the stop stays committed
    fresh = dict(opt, ltp=139.0, age=0.3)
    t = paper.check_exit(b, dict(c2, now_s=34, by_id={5: fresh}, by_key={"k": fresh}))
    assert t and t["reason"] == "STOP" and t["exit"] == 139.0 and not t.get("stale_exit")
    paper.open_trade(b, dict(ctx, now_s=100), opt, "again")
    c3 = dict(c, now_s=130)
    assert paper.check_exit(b, c3) is None
    t = paper.check_exit(b, dict(c3, now_s=141))                    # > EXIT_DEFER_MAX_S: last price, tagged
    assert t and t["stale_exit"] and t["exit"] == 140.0
    paper.open_trade(b, dict(ctx, now_s=200), opt, "third")
    assert paper.check_exit(b, dict(c, now_s=230, fut_age=9.0)) is None   # futures stale: no price decision


def test_control_books():
    from datetime import datetime
    s1 = paper.random_schedule("2026-10-21", "random_entry")
    assert s1 == paper.random_schedule("2026-10-21", "random_entry")       # reproducible in replay
    lo, hi = config.mins(config.SUPPRESS_UNTIL) * 60, config.mins(config.LAST_ENTRY) * 60
    assert all(lo <= x < hi for x in s1)
    n = [len(paper.random_schedule(f"2026-11-{d:02d}", "random_entry")) for d in range(1, 29)]
    assert 3 <= sum(n) / len(n) <= 9                                        # Poisson mean ~6
    b = paper.Book("random_entry", config.VARIANTS["random_entry"], "2026-10-21")
    b.ctl["sched"] = [36000]                                                # 10:00:00
    dt = datetime(2026, 10, 21, 10, 0, 20, tzinfo=config.IST)
    ctx = {"now_dt": dt, "domino": {"dir": 1}, "episode": None, "advisors": {}, "fut_r60": -6.0, "blackout": {"on": False}}
    fire, why = paper.evaluate_entry(b, ctx, [])
    assert fire and paper.entry_dir(b, ctx) == -1                           # side from the futures 1-min move
    # premium momentum: raw 5-min rise, delta rising, one trade per burst
    mb = paper.Book("premium_momentum", config.VARIANTS["premium_momentum"], "2026-10-21")
    sw = {"K": 25200, "px": 90.0, "legs": {"CE": {"chg5": 7.0, "ddelta": 0.05}, "PE": {"chg5": -3.0, "ddelta": -0.04}}}
    ctx = dict(ctx, straddle_watch=sw)
    fire, why = paper.evaluate_entry(mb, ctx, [])
    assert fire and paper.entry_dir(mb, ctx) == 1 and mb.ctl["leg"] == "CE"
    mb.ctl.pop("dir"); mb.ctl.pop("leg"); mb.ctl.pop("fire_id")
    assert not paper.evaluate_entry(mb, ctx, [])[0]                         # not re-armed yet
    ctx["straddle_watch"] = dict(sw, legs={"CE": {"chg5": 1.0, "ddelta": 0.0}, "PE": {"chg5": 0.0, "ddelta": 0.0}})
    paper.evaluate_entry(mb, ctx, [])
    ctx["straddle_watch"] = sw
    assert paper.evaluate_entry(mb, ctx, [])[0]                             # re-armed after it cooled off
    assert set(config.CONTROLS) <= set(config.VARIANTS)
    assert config.VARIANTS["futures_only"]["s_star"] == 0.0


def _book(name, rets, day):
    b = paper.Book(name, config.VARIANTS.get(name, config.TRIGGER), day)
    b.trades = [{"pnl_pts": r, "pnl_rs": 0, "ret_pct": r, "entry": 100.0, "advisors": {},
                 "reason": "STOP", "time_in": "10:00:00"} for r in rets]
    return b


def test_learning_percent_controls_bonferroni():
    _reset_learning()
    import math as _m
    assert abs(learning._day_ret([{"ret_pct": 10}, {"ret_pct": -10}]) - 100 * _m.log(0.99)) < 1e-9   # compounding (log)
    g0, k0 = learning.sprt_lines(0)
    assert abs(g0 - 998.2) < 0.1 and abs(k0 + 560.9) < 0.1          # O-8: sigma 30 % (was 110.9 / -62.3 at 10 %)
    assert abs(learning.t_sf(2.5, 9) - 0.0169) < 2e-4
    assert abs(learning.t_crit(0.05 / 12, 9) - 3.364) < 0.01
    for i in range(14):
        day = f"2026-11-{i + 1:02d}"
        books = {}
        for name in list(config.VARIANTS) + ["RAW"]:
            if name == "futures_only":
                rets = [9.0, 11.0, 10.0]                  # a control that crushes everything
            elif name == "m1.5_s0.4":
                rets = [3.0 + (i % 3), 2.0]               # a real but modest challenger
            else:
                rets = [1.0, -1.0 + (i % 2) * 0.5]
            books[name] = _book(name, rets, day)
        learning.record_day(day, books)
        s = learning.learn(day)
    assert s["champion"] not in config.CONTROLS                                  # a control can never be champion
    assert s["champion"] == "m1.5_s0.4"
    rep = open(learning.REPORT, encoding="utf-8").read()
    assert "futures_only" in rep and "control is ahead" in rep
    promo = [e for e in s["log"] if e["event"] == "champion" and not str(e.get("by", "")).startswith("owner")]   # D-124: the owner's entry is not a promotion
    assert promo and promo[0]["day"] >= "2026-11-11"                             # 10 days + 2 evenings in a row


def test_learning_gated_book_decides_advisor():
    _reset_learning()
    champ = config.CHAMPION_DEFAULT
    s = None
    for i in range(30):
        day = f"2026-12-{i + 1:02d}" if i < 28 else f"2027-01-{i - 27:02d}"
        books = {}
        for name in list(config.VARIANTS) + ["RAW"]:
            books[name] = _book(name, [0.5, 0.2], day)
        # RAW: two losers per day that iv_late vetoed, one winner it didn't
        raw = _book("RAW", [-6.0 - (i % 3), -5.0, 4.0 + (i % 2)], day)
        for t, v in zip(raw.trades, (True, True, False)):
            t["advisors"] = {"iv_late": {"veto": v}}
        books["RAW"] = raw
        st = learning.load_state()
        if "iv_late" in st["candidates"]:                                       # the engine would run the gated book
            books["gate:iv_late"] = _book("gate:iv_late", [3.0 + (i % 2), 1.0], day)
        learning.record_day(day, books)
        s = learning.learn(day)
        if "iv_late" in s["gates"]:
            break
    assert any(e["event"] == "candidate+" and e["advisor"] == "iv_late" for e in s["log"])
    assert "iv_late" in s["gates"], s["log"][-3:]                                # promoted by its gated book
    cand_day = next(e["day"] for e in s["log"] if e["event"] == "candidate+")
    gate_day = next(e["day"] for e in s["log"] if e["event"] == "gate+")
    assert gate_day > cand_day and s["champion"] == champ


def test_paper_only_no_order_calls():
    """v1 is paper-only (owner, 17 Oct 2026): no broker order call may exist anywhere in apex/."""
    import re
    assert config.PAPER_ONLY is True
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apex")
    bad = re.compile(r"\.(place_order|modify_order|cancel_order|square_off|place_gtt_order|limit_calculator)\s*\(")
    hits = []
    for d, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".py"):
                with open(os.path.join(d, f), encoding="utf-8") as fh:
                    for n, line in enumerate(fh, 1):
                        if bad.search(line):
                            hits.append(f"{f}:{n}")
    assert not hits, hits



# ── strengthening (D-069 … D-074) ─────────────────────────────────────────────
def test_regime_labels_and_live_classification():
    from apex.engine.regime import Regime
    L = Regime.label
    base = {"er5": 0.5, "er1": 0.5, "rv_pct": 70, "ext_pct": 50, "breadth": 0.8, "broke": 0}
    assert L(base, 60) == "WARMING"
    assert L(base, 3600) == "DIRECTIONAL"
    assert L(dict(base, ext_pct=95, er1=0.1), 3600) == "EXHAUSTION"
    assert L(dict(base, broke=1), 3600) == "BREAKOUT"
    assert L(dict(base, er5=0.1, rv_pct=50), 3600) == "RANGE"
    assert L(dict(base, er5=0.3, rv_pct=10), 3600) == "COMPRESSION"
    assert L(dict(base, breadth=0.3), 3600) == "UNCERTAIN"                     # progress without breadth
    # live: 40 min of chop, then 10 min of a clean basket-confirmed rise
    r = Regime()
    rng = np.random.default_rng(1)
    fut, ttq, stk = 25200.0, 0.0, np.full(5, 1000.0)
    t0 = 1792380900.0
    for t in range(40 * 60):
        fut = 25200 + 6 * np.sin(t / 20) + rng.normal(0, 0.3); ttq += 100
        r.update(t0 + t, fut, ttq, stk * (1 + (fut - 25200) / 25200), np.full(5, 10.0))
    assert r.state in ("RANGE", "COMPRESSION", "UNCERTAIN"), r.state
    assert r.advise(1)[0] is True
    for t in range(40 * 60, 50 * 60):
        fut += 0.12 + rng.normal(0, 0.05); ttq += 300
        r.update(t0 + t, fut, ttq, stk * (1 + (fut - 25200) / 25200), np.full(5, 10.0))
    assert r.state in ("DIRECTIONAL", "BREAKOUT"), (r.state, r.f)
    assert r.dir == 1 and r.advise(1)[0] is False and r.advise(-1)[0] is True     # agrees up, vetoes a PE
    v = r.view()
    assert v["vwap"] and v["breadth"] == 1.0


def test_bad_print_guard():
    from apex.engine.guard import DataGuard, RESUME_S
    g = DataGuard()
    for t in range(int(RESUME_S) + 2):
        g.update(float(t), 2, 0.1, True, 25200.0 + t * 0.1)
    assert not g.on
    g.update(22.0, 2, 0.1, True, 25200.0 * 1.02)                                  # +2 % in one step
    assert g.on and "implausible" in g.reason
    g.update(22.1, 2, 0.1, True, 25203.0)                                         # snaps back: still a bad print
    assert g.on
    for t in range(23, 23 + int(RESUME_S) + 1):
        g.update(float(t), 2, 0.1, True, 25203.0)
    assert not g.on


def test_ledger_labels_and_diagnostics():
    from datetime import datetime, timedelta
    from apex.engine import diagnostics
    from apex.engine.ledger import Ledger
    day = "2026-10-22"
    path = os.path.join(config.PAPER_DIR, f"candidates_{day}.jsonl")
    if os.path.exists(path):
        os.remove(path)
    led = Ledger(day)
    book = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], day)
    t0 = datetime(2026, 10, 22, 10, 0, tzinfo=config.IST)
    opt = {"id": 5, "key": "NIFTY|OPT|2026-10-27|25200|CE", "strike": 25200, "rr": "CE", "week": 0,
           "expiry": "2026-10-27", "ltp": 100.0, "delta": 0.6, "age": 0.2}

    def ctx(sec, fut, ltp, z=2.6, ep=True, eid=7):
        o = dict(opt, ltp=ltp)
        return {"now_s": 1000.0 + sec, "now_dt": t0 + timedelta(seconds=sec), "fut": fut, "w0": "2026-10-27",
                "domino": {"z": z, "dir": 1, "S_up": 0.7, "S_dn": 0.0, "gap": 1.0, "sigma15": 4.0},
                "episode": {"id": eid, "dir": 1, "type": "BASKET-LED", "fut0": 25195.0} if ep else None,
                "options": [o], "by_key": {o["key"]: o}, "advisors": {"regime": {"veto": False}, "iv_late": {"veto": True}}}
    rv = {"state": "DIRECTIONAL", "dir": 1, "er5": 0.5, "breadth": 0.8, "ext_pct": 40, "rv_pct": 70}
    led.update(ctx(0, 25200.0, 100.0), book, "synchrony 0.45 < 0.5", rv)
    assert led.n == 1 and 7 in led.open
    led.update(ctx(1, 25201.0, 101.0), book, "", rv)                              # same episode: no second record
    assert led.n == 1
    for sec, fut, px in ((30, 25205, 104), (60, 25209, 108), (200, 25213, 112), (300, 25220, 118)):
        led.update(ctx(sec, fut, px), book, "", rv)
    r = led.open[7]
    assert r["label"] == "TARGET" and r["t_label"] == 200.0                       # +12 (d*) before -12
    assert r["opt_ret"]["60"] == 8.0 and r["opt_ret"]["300"] == 18.0 and r["fired"] is False
    led.update(ctx(901, 25230, 120, ep=False), book, "", rv)                      # 15 min: written
    assert not led.open and os.path.exists(path)
    led2 = Ledger(day)                                                            # a losing, taken candidate
    book.trades.append({"episode": 8})
    led2.update(ctx(0, 25200.0, 100.0, eid=8), book, "", dict(rv, state="RANGE"))
    led2.update(ctx(50, 25187.0, 90.0, eid=8), book, "", rv)
    led2.close()
    rows = [json.loads(x) for x in open(path, encoding="utf-8")]
    assert [x["label"] for x in rows] == ["TARGET", "STOP"] and rows[1]["fired"] is True
    lines = "\n".join(diagnostics.candidate_lines(day))
    assert "rejected: basket too thin" in lines and "| taken | 1 | 0% |" in lines and "RANGE" in lines
    lo, hi = diagnostics.wilson(8, 10)
    assert abs(lo - 0.490) < 0.01 and abs(hi - 0.943) < 0.01


def test_config_self_check():
    assert config.validate() == []
    saved = dict(config.VARIANTS["m2.0_s0.5"])
    try:
        config.VARIANTS["m2.0_s0.5"]["s_star"] = 5.0
        assert any("out-of-range" in p for p in config.validate())
    finally:
        config.VARIANTS["m2.0_s0.5"].clear(); config.VARIANTS["m2.0_s0.5"].update(saved)
    assert config.validate() == []


def test_settling_after_gap():
    from apex.engine.guard import DataGuard, RESUME_S, SETTLE_S
    g = DataGuard()
    for t in range(int(RESUME_S) + 1):
        g.update(float(t), 2, 0.1)
    assert not g.on and g.settling(25.0) == 0.0
    g.update(100.0, 3, None)                                           # a gap
    for t in range(101, 101 + int(RESUME_S) + 1):
        g.update(float(t), 2, 0.1)
    assert not g.on and abs(g.settling(122.0) - (SETTLE_S - 1.0)) < 1e-6
    assert g.settling(122.0 + SETTLE_S) == 0.0
    b = paper.Book("premium_momentum", config.VARIANTS["premium_momentum"], "2026-10-21")
    from datetime import datetime
    sw = {"K": 25200, "px": 90.0, "legs": {"CE": {"chg5": 7.0, "ddelta": 0.05}, "PE": {"chg5": -3.0, "ddelta": -0.04}}}
    ctx = {"now_dt": datetime(2026, 10, 21, 10, 0, tzinfo=config.IST), "domino": {"dir": 1}, "episode": None,
           "advisors": {}, "straddle_watch": sw, "blackout": {"on": False, "settling_s": 120.0}}
    assert paper.evaluate_entry(b, ctx, [])[1].startswith("DATA GAP")
    ctx["blackout"] = {"on": False, "settling_s": 0.0}
    assert paper.evaluate_entry(b, ctx, [])[0]


def test_time_exit_on_stale_quote_is_tagged():
    from datetime import datetime
    b = paper.Book("x", config.TRIGGER, "2026-10-21")
    opt = {"id": 5, "key": "k", "strike": 25150, "rr": "CE", "expiry": "2026-10-27", "ltp": 150.0}
    ctx = {"now_s": 0, "now_dt": datetime(2026, 10, 21, 10, 0, tzinfo=config.IST), "fut": 25200.0, "advisors": {},
           "episode": {"id": 1, "dir": 1, "type": "BASKET-LED"}}
    paper.open_trade(b, ctx, opt, "t")
    stale = dict(opt, ltp=151.0, age=40.0)
    late = dict(ctx, now_dt=datetime(2026, 10, 21, 15, 26, tzinfo=config.IST), now_s=100, by_id={5: stale}, by_key={"k": stale},
                domino={"S_up": 0, "S_dn": 0, "z": 0}, fut_age=0.1)
    old = config.FLATTEN_AT
    config.FLATTEN_AT = (15, 25)                 # the v1 clock (the CAS test moves it to 15:35, D-094)
    try:
        t = paper.check_exit(b, late)
    finally:
        config.FLATTEN_AT = old
    assert t and t["reason"].startswith("TIME") and t["stale_exit"] is True



# ── independent-review fixes (docs/06_AUDIT.md §4) ─────────────────────────────
def _pos_ctx():
    from datetime import datetime
    b = paper.Book("x", config.TRIGGER, "2026-10-21")
    opt = {"id": 5, "key": "k", "strike": 25150, "rr": "CE", "expiry": "2026-10-27", "ltp": 150.0}
    ctx = {"now_s": 0, "now_dt": datetime(2026, 10, 21, 10, 0, tzinfo=config.IST), "fut": 25200.0, "advisors": {},
           "episode": {"id": 1, "dir": 1, "type": "BASKET-LED"}}
    paper.open_trade(b, ctx, opt, "t")
    return b, opt, ctx


def test_exit_ignores_blackout_prints():
    """R1: a frozen or implausible futures print must not move the trail or fire a stop."""
    b, opt, ctx = _pos_ctx()
    dom = {"S_up": 0, "S_dn": 0, "z": 0}
    fresh = dict(opt, ltp=151.0, age=0.2)
    bad = dict(ctx, fut=25200 * 1.02, now_s=30, by_id={5: fresh}, by_key={"k": fresh}, domino=dom, fut_age=0.1,
               blackout={"on": True, "why": "implausible futures jump"})
    assert paper.check_exit(b, bad) is None and b.pos["best"] == 25200.0 and not b.pos["trail"]
    down = dict(bad, fut=25200 * 0.99)
    assert paper.check_exit(b, down) is None and not b.pos.get("pending")        # no STOP on a bad print
    real = dict(bad, fut=25201.0, now_s=31, blackout={"on": False})
    assert paper.check_exit(b, real) is None and b.pos["gap"] is True


def test_exit_never_prices_off_another_contract():
    """R2: after a feed restart row ids are renumbered; the held key is gone and its old id holds a PE."""
    b, opt, ctx = _pos_ctx()
    other = {"id": 5, "key": "NIFTY|OPT|2026-10-27|24000|PE", "strike": 24000, "rr": "PE", "ltp": 20.0, "age": 0.1}
    c = dict(ctx, fut=25185.0, now_s=30, by_id={5: other}, by_key={other["key"]: other},
             domino={"S_up": 0, "S_dn": 0, "z": 0}, fut_age=0.1, blackout={"on": False})
    assert paper.check_exit(b, c) is None and b.pos["pending"]["reason"] == "STOP"
    t = paper.check_exit(b, dict(c, now_s=41))
    assert t and t["exit"] == 150.0 and t["stale_exit"]                             # last known price, tagged


def test_regime_rewarms_after_gap():
    """R3: after a gap the windows are empty; the label must be WARMING, not COMPRESSION."""
    from apex.engine.regime import Regime, WIN5
    r = Regime()
    rng = np.random.default_rng(2)
    fut, ttq, t0 = 25200.0, 0.0, 1792380900.0
    for t in range(40 * 60):
        fut += rng.normal(0, 0.8); ttq += 100
        r.update(t0 + t, fut, ttq, np.full(5, 1000.0), np.full(5, 10.0))
    before = r.state
    assert before != "WARMING"
    r.after_gap()
    for t in range(40 * 60, 40 * 60 + 10):
        r.update(t0 + t, fut, ttq, np.full(5, 1000.0), np.full(5, 10.0))
    assert r.state == "WARMING"
    for t in range(40 * 60 + 10, 40 * 60 + WIN5 + 5):
        fut += rng.normal(0, 0.8); ttq += 100
        r.update(t0 + t, fut, ttq, np.full(5, 1000.0), np.full(5, 10.0))
    assert r.state != "WARMING"


def test_learn_is_idempotent_per_evening():
    """R4/R7: running learn() twice in one evening moves no streak; the promotion day is excluded."""
    _reset_learning()
    for i in range(12):
        day = f"2027-02-{i + 1:02d}"
        books = {n: _book(n, [3.0 + (i % 2)] if n == "m1.5_s0.4" else [0.5, -0.2], day) for n in list(config.VARIANTS) + ["RAW"]}
        learning.record_day(day, books)
        s1 = learning.learn(day)
        s2 = learning.learn(day)
        assert s1["streak"] == s2["streak"] and s1["gate_streak"] == s2["gate_streak"]
        assert len(s1["log"]) == len(s2["log"])
    s = learning.load_state()
    assert s["champion"] == "m1.5_s0.4"                                             # promoted on evidence
    since = s["champion_since"]
    days = learning._load_days()
    expect = sum(len(tr) for d, tr in days["m1.5_s0.4"].items() if d > since)      # strictly after the promotion day
    assert s["scoreboard"]["n"] == expect and expect < sum(len(tr) for d, tr in days["m1.5_s0.4"].items() if d >= since)


def test_engine_pause_is_a_gap():
    from apex.engine.guard import DataGuard, RESUME_S
    g = DataGuard()
    for t in range(int(RESUME_S) + 1):
        g.update(float(t), 2, 0.1, True, 25200.0, step_gap=0.1)
    assert not g.on
    g.update(60.0, 2, 0.1, True, 25240.0, step_gap=39.0)         # feed fresh, engine was asleep, price moved 40
    assert g.on and "engine paused" in g.reason
    g.update(60.1, 2, 0.1, True, 25240.0, step_gap=0.1)
    assert g.on                                                    # and no bad-print false alarm on the jump
    assert "implausible" not in g.reason


def test_reason_class_gate_not_late():
    from apex.engine.diagnostics import reason_class
    assert reason_class({"decision_at_cross": "gate iv_late: ATM IV +2.1 pts"}) == "gate"
    assert reason_class({"decision_at_cross": "LATE: futures already 20 pts since onset"}) == "late"
    assert reason_class({"decision_at_cross": "synchrony 0.4 < 0.5"}) == "basket too thin"


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
