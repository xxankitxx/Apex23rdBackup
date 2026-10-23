"""WP-7 checks (advisor and observer correctness): python tests/test_wp7.py"""
import json
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_wp7_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta  # noqa: E402

import numpy as np  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False   # D-126: these suites test the exit/entry logic itself on same-step fills; D-126 has its own suite
from apex.table import ROW_DTYPE  # noqa: E402

# Mon 19 Oct 2026 (a weekly expiry day: Tue 20 is Dussehra), 10:00 IST
T_EXP_1000 = datetime(2026, 10, 19, 10, 0, tzinfo=config.IST).timestamp()


def _push_series(values_at, i=7, secs=70.0, t0=T_EXP_1000, depth_ns_fn=None, field="ask"):
    """Drive a Market + Flow at 10 Hz; values_at(t) gives the standing qty on `field`'s side.
    depth_ns_fn(t_abs) -> the row's depth_ns (default: fresh every step)."""
    from apex.engine.flow import Flow
    from apex.engine.market import Market
    m, f = Market(), Flow(config.MAX_ROWS)
    snap = np.zeros(config.MAX_ROWS, dtype=ROW_DTYPE)
    for step in range(int(secs * 10) + 1):
        t = step / 10.0
        ta = t0 + t
        snap = snap.copy()
        snap["ltp"][i] = 100.0; snap["bid"][i] = 99.95; snap["ask"][i] = 100.05
        snap["ttq"][i] = 1000                                  # no trades
        q = float(values_at(t))
        snap["bq"][i] = [500] * 5; snap["bo"][i] = [20] * 5
        snap["aq"][i] = [q / 5] * 5; snap["ao"][i] = [max(q / 25, 1) / 5] * 5
        snap["depth_ns"][i] = int((depth_ns_fn(ta) if depth_ns_fn else ta) * 1e9)
        snap["tbq"][i] = 50000; snap["tsq"][i] = 30000
        m.push(snap, ta); f.update(m, 0.1)
    return m, f


def test_a_refill_after_drain_is_refill():
    """C-35: 60 s ago 1000, fell 70 % to 300 by 10 s ago, then +50 % to 450 in 10 s.
    Old code classed it DRAIN-SLOW (the DSLOW mask overwrote REFILL)."""
    from apex.engine.flow import CLS, REFILL

    def q(t):                                   # t runs 0..70 s
        if t <= 10:
            return 1000.0
        if t <= 60:
            return 1000.0 - 700.0 * (t - 10) / 50.0      # slow 50-s drain to 300
        return 300.0 + 150.0 * (t - 60) / 10.0           # +50 % in the last 10 s
    _, f = _push_series(q)
    assert int(f.cls_s[7]) == REFILL, CLS[int(f.cls_s[7])]


def test_a2_slow_drain_still_dslow():
    """The guard does not swallow a real slow drain (the last 10 s still falling)."""
    from apex.engine.flow import CLS, DSLOW
    _, f = _push_series(lambda t: 1000.0 - 600.0 * t / 70.0)
    assert int(f.cls_s[7]) == DSLOW, CLS[int(f.cls_s[7])]


def test_b_stale_depth_is_unknown():
    """C-18 (advisor side): depth last refreshed 5 s ago gives no class. Old code read HOLDING."""
    from apex.engine.flow import CLS, UNK, HOLD
    t_end = T_EXP_1000 + 70.0
    _, f = _push_series(lambda t: 1000.0, depth_ns_fn=lambda ta: min(ta, t_end - 5.0))
    for c in (f.cls_b, f.cls_s, f.cls_bo, f.cls_so):
        assert int(c[7]) == UNK, CLS[int(c[7])]
    _, f2 = _push_series(lambda t: 1000.0)                 # fresh depth, same book -> HOLDING
    assert int(f2.cls_s[7]) == HOLD, CLS[int(f2.cls_s[7])]


def test_b2_depth_age_accessor():
    from apex.engine.market import Market
    m = Market()
    assert m.depth_age(0.0) is None
    snap = np.zeros(config.MAX_ROWS, dtype=ROW_DTYPE)
    snap["depth_ns"][3] = int((T_EXP_1000 - 4.0) * 1e9)
    snap["depth_ns"][4] = 1                                # a bare flag, not a time
    m.push(snap, T_EXP_1000)
    a = m.depth_age(T_EXP_1000)
    assert abs(a[3] - 4.0) < 1e-3 and np.isnan(a[4]) and np.isnan(a[0])


class _FakeTable:
    def __init__(self, version, chain_ns, now_ns):
        self.ctrl = {"chain_version": version, "chain_ns": chain_ns}
        self._now = now_ns

    def c(self, k):
        return self.ctrl[k]

    def now_ns(self):
        return self._now


def _write_chain(expiry, oi_scale=1.0):
    ks = [25000 + 50 * i for i in range(17)]
    oi = {str(k): {"call": 10000.0 * oi_scale, "put": 10000.0 * oi_scale} for k in ks}
    oi["25300"]["call"] = 90000.0 * oi_scale                  # a CE wall above
    oi["25100"]["put"] = 90000.0 * oi_scale                   # a PE wall below
    with open(os.path.join(config.DATA_DIR, "chain_latest.json"), "w") as f:
        json.dump({"expiry": expiry, "oi": oi}, f)


def test_c_expired_or_old_chain_has_no_walls():
    """C-50: last week's chain on disk -> no OI and no destination; a fresh chain gives walls;
    a chain older than 3 x CHAIN_POLL_S gives destination None. Old code trusted all three."""
    from apex.engine.levels import Pressure
    now_ns = int(T_EXP_1000 * 1e9)
    spot = 25200.0
    # (1) a chain file from last week, at engine start (table chain_version 0, chain_ns set)
    _write_chain("2026-10-13")
    p = Pressure()
    p.refresh(_FakeTable(0, now_ns - int(10e9), now_ns), spot)
    assert not p.oi and not p.oi0 and p.destination(spot, 1) is None
    assert p.rejected and "before" in p.rejected
    # (1b) a file on disk but no chain published in this table yet (chain_ns 0)
    _write_chain("2026-10-19")
    p = Pressure()
    p.refresh(_FakeTable(0, 0, now_ns), spot)
    assert not p.oi and p.destination(spot, 1) is None
    # ... and the same version IS loaded once chain_ns appears (not skipped as "seen")
    p.refresh(_FakeTable(0, now_ns - int(5e9), now_ns), spot)
    assert p.oi and p.oi0 and p.destination(spot, 1)["level"] == 25300.0
    # (2) fresh, today: walls and a destination
    # (3) the same chain 271 s later: no wall data
    later = now_ns + int(266e9)
    p.refresh(_FakeTable(0, now_ns - int(5e9), later), spot)
    assert p.chain_age > 3 * config.CHAIN_POLL_S
    assert p.destination(spot, 1) is None and p.destination(spot, -1) is None
    assert p.view(spot)["dest_up"] is None


def test_c2_oi0_only_from_today():
    from apex.engine.levels import Pressure
    now_ns = int(T_EXP_1000 * 1e9)
    _write_chain("2026-10-19")
    p = Pressure()
    p.refresh(_FakeTable(1, now_ns - int(86400e9), now_ns), 25200.0)   # published yesterday
    assert p.oi and not p.oi0
    _write_chain("2026-10-19", oi_scale=2.0)
    p.refresh(_FakeTable(2, now_ns - int(1e9), now_ns), 25200.0)
    assert p.oi0 and p.oi0["25300"]["call"] == 180000.0 and p.version == 2


def test_c3_rejected_chain_keeps_previous():
    """An expired chain arriving mid-session is ignored; the held chain keeps its own age."""
    from apex.engine.levels import Pressure
    now_ns = int(T_EXP_1000 * 1e9)
    _write_chain("2026-10-19")
    p = Pressure()
    p.refresh(_FakeTable(1, now_ns, now_ns), 25200.0)
    _write_chain("2026-10-13", oi_scale=5.0)
    p.refresh(_FakeTable(2, now_ns + int(90e9), now_ns + int(91e9)), 25200.0)
    assert p.version == 1 and p.oi["25300"]["call"] == 90000.0 and p.expiry == "2026-10-19"
    assert abs(p.chain_age - 91.0) < 1e-6


def _gex_chain():
    ks = [25000 + 50 * i for i in range(9)]
    calls = [10000] * 9; calls[6] = 90000
    return {str(k): {"call": c, "put": 10000} for k, c in zip(ks, calls)}


def test_d_gex_map_stale():
    """A gamma map whose chain is older than 3 x CHAIN_POLL_S gives (False, 'gamma map stale').
    Old code kept vetoing on it. A forward move on the same chain does not refresh the age."""
    from apex.engine.gex import GexMap
    now = datetime(2026, 10, 19, 10, 0, tzinfo=config.IST)
    g = GexMap()
    v = g.update(5, _gex_chain(), "2026-10-27", now, 25200.0, {}, 0.13)
    assert v["ok"] and v["regime"] == "DAMPEN"
    assert g.advise(+1, 25200.0)[0] is True                        # fresh: the advisor speaks
    g.update(5, _gex_chain(), "2026-10-27", now + timedelta(seconds=200), 25260.0, {}, 0.13)  # F moved
    assert g.advise(+1, 25260.0)[0] is True
    g.update(5, _gex_chain(), "2026-10-27", now + timedelta(seconds=271), 25260.0, {}, 0.13)
    assert g.advise(+1, 25260.0) == (False, "gamma map stale")
    g.update(6, _gex_chain(), "2026-10-27", now + timedelta(seconds=280), 25260.0, {}, 0.13)  # new chain
    assert g.advise(+1, 25260.0)[0] is True


def test_e_banklead_sigma_session_only():
    """C-56: 15-s changes at 09:05 (pre-open) leave sigma unchanged; at 10:00 they move it."""
    from apex.engine.extras import BankLead
    from apex.engine.market import Market
    t_pre = datetime(2026, 10, 19, 9, 5, tzinfo=config.IST).timestamp()

    def run(t0):
        m, b = Market(), BankLead()
        snap = np.zeros(config.MAX_ROWS, dtype=ROW_DTYPE)
        for step in range(300):                                  # 30 s, bank flat at 56000 (zero changes)
            snap = snap.copy(); snap["ltp"][2] = 56000.0
            m.push(snap, t0 + step / 10.0)
            b.update(m, 2, t0 + step / 10.0, None)
        return b
    pre = run(t_pre)
    assert pre.sig == 60.0 and pre.n == 0
    live = run(T_EXP_1000)
    assert live.sig < 60.0 and live.n > 0


def _watch_run(day_dt, theta=-0.30):
    from apex.engine.straddle_watch import StraddleWatch
    w = StraddleWatch()
    t0 = day_dt.timestamp()
    g = {"CE": {"delta": 0.5, "gamma": 0.002, "theta_min": theta}, "PE": {"delta": -0.5, "gamma": 0.002, "theta_min": theta}}
    states, spikes = [], []
    for t in range(900):                                         # flat straddle 15 min, then CE +12 in 2 min
        ce = 45.0 + (12.0 * min(1.0, (t - 600) / 120) if t >= 600 else 0.0)
        pe = 45.0 - (4.0 * min(1.0, (t - 600) / 120) if t >= 600 else 0.0)
        w.update(t0 + t, day_dt + timedelta(seconds=t), 25200,
                 {"CE": (ce, ce - .1, ce + .1), "PE": (pe, pe - .1, pe + .1)}, g, 25200.0, 50.0)
        states.append(w.state); spikes.append(bool(w.spike))
    return w, states, spikes


def test_f_straddle_0dte_observer():
    """O-3 observer: on 0DTE expected5_0dte / expected5 = 375/1440; on a non-expiry day they
    are equal; the spike decision is identical to the baseline (expected5 still drives it)."""
    w, states, spikes = _watch_run(datetime(2026, 10, 19, 14, 0, tzinfo=config.IST))
    assert w.zero_dte is True
    assert abs(w.expected5_0dte / w.expected5 - 375.0 / 1440.0) < 1e-9
    assert abs(w.excess_0dte - (w.chg5 - w.expected5_0dte)) < 1e-9
    assert abs(w.expected5 - (-0.60 * 5)) < 1e-9                  # baseline: theta_min x 5
    assert abs(w.excess - (w.chg5 - w.expected5)) < 1e-9
    v = w.view(series=False)
    assert "expected5_0dte" in v and "excess_0dte" in v
    # baseline decision: recompute the spike/state path with the pre-WP-7 formula by
    # monkeypatching the observer away; the trajectories must be identical
    from apex.engine import straddle_watch as sw
    orig = sw.StraddleWatch._observe_0dte
    sw.StraddleWatch._observe_0dte = lambda self, *a: None
    try:
        _, st0, sp0 = _watch_run(datetime(2026, 10, 19, 14, 0, tzinfo=config.IST))
    finally:
        sw.StraddleWatch._observe_0dte = orig
    assert st0 == states and sp0 == spikes and any(spikes)
    sp = w.spikes[0]
    assert sp["expected5_0dte"] is not None and sp["excess0_0dte"] < sp["excess0"]
    w2, _, _ = _watch_run(datetime(2026, 10, 21, 14, 0, tzinfo=config.IST))   # Wed: not an expiry
    assert w2.zero_dte is False and w2.expected5_0dte == w2.expected5


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
