"""External reviews (21 Oct evening): edge snapshot (D-136), dual-mode shadow (D-137), packet-shape canary and parser
fuzzing (D-138). python tests/test_c9_reviews.py"""
import json
import os
import random
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c9_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

import numpy as np  # noqa: E402

from apex import config, feed_core  # noqa: E402
config.FILL_NEXT_PRINT = False
from apex.engine import edge, paper  # noqa: E402
from apex.feed_core import Registry  # noqa: E402
from apex.table import Table  # noqa: E402


# ── D-138: the parser never raises and never writes a wrong field for a random packet ─────────────────────────
def test_parser_fuzz_and_shape_canary():
    t = Table(create=True, name=f"t_c9_{os.getpid()}")
    try:
        reg = Registry()
        fut = reg.add("NIFTY|FUT", "fut", "NIFTY", "4.1!48704", seg="fo", depth=True, depth_token="4.2!48704")
        reg.save(t)
        by = feed_core.Registry.tokens_from_items(reg.items)
        good = ["4.1!48704", 1, 23000.5, 3, 4, 0.1, 23000.0, 75, 23001.0, 150, 75, 23000.2, 1000, 0, 5000, 600, 700, 0, 0,
                0, 0, 1792550000, 22990.0]
        assert feed_core.apply_packet(t, by, good, 1) == fut and t.rows["ltp"][fut] == 23000.5
        rng = random.Random(7)
        junk = [None, "", "x", float("nan"), -1, 1e18, [], {}, "23000", 0]
        feed_core.SHAPE_ODD.clear()
        for _ in range(3000):
            n = rng.choice([1, 2, 3, 6, 10, 21, 22, 23, 24, 30])
            raw = [rng.choice(["4.1!48704", "4.2!48704", "4.1!999", "bad", 5])] + [rng.choice(junk + [rng.uniform(0, 3e4)])
                                                                                  for _ in range(n - 1)]
            if raw[0] == "4.2!48704" and n >= 3:
                raw[2] = [[rng.choice(junk + [1.0]) for _ in range(rng.choice([0, 3, 8]))] for _ in range(rng.choice([0, 2, 5, 7]))]
            feed_core.apply_packet(t, by, raw, 2)              # must never raise
        assert any(k.startswith("quote len") for k in feed_core.SHAPE_ODD), feed_core.SHAPE_ODD
        assert int(t.rows["seq"][fut]) % 2 == 0                 # no torn write left behind
    finally:
        t.close()
        t.unlink()


# ── D-136: the snapshot is computed from the table, signed in the trade's direction, carried by the trade ─────
class _Eng:
    pass


def _snap(bq, aq, tb, ts):
    from apex.table import ROW_DTYPE
    s = np.zeros(4, dtype=ROW_DTYPE)
    s["bid"][1], s["ask"][1] = 23019.0, 23021.0
    s["bq"][1, :] = bq; s["aq"][1, :] = aq; s["tbq"][1] = tb; s["tsq"][1] = ts
    return s


def test_edge_snapshot_and_signing():
    from apex.engine.impulse import ImpulseWindow
    e = _Eng()
    e.fut_id, e._spot_bad, e._basis_ref, e.atm_iv = 1, "", 15.0, 0.146
    e.iv_change = lambda secs: 0.3
    e.impulse = ImpulseWindow(2700)
    for k in range(1200):
        e.impulse.add(k, 23000.0 + 10 * np.sin(k / 30.0) - k * 0.05)
    e._pb_view = e.impulse.view()

    class P:
        pcr = 0.9

        def destination(self, sp, d):
            return {"room": 40.0 if d > 0 else 25.0}
    e.pressure = P()
    snap = _snap(300, 100, 900, 300)
    x = edge.snapshot(e, snap, 23000.0, 23020.0)
    assert x["basis_dev"] == 5.0 and x["fut_imb5"] == 0.5 and x["fut_tot_imb"] == 0.5
    assert x["iv_atm"] == 14.6 and x["rv15"] and x["iv_rv"] and x["wall_up"] == 40.0 and x["wall_dn"] == 25.0
    assert x["imp_rng"] and x["imp_d"] in (-1, 1) and set(edge.KEYS) <= set(x)
    pe = edge.signed(x, -1)
    assert pe["fut_imb5"] == -0.5 and pe["basis_dev"] == -5.0 and pe["wall_room"] == 25.0
    # Gemini review: OFI, synthetic-forward dislocation, micro-price
    e.fwd = 23030.0
    for k in range(25):                                        # the bid steps up each second: buying pressure
        s2 = _snap(300, 100, 900, 300)
        s2["bid"][1], s2["ask"][1] = 23019.0 + k * 0.5, 23021.0 + k * 0.5
        s2["bqty"][1], s2["aqty"][1] = 300.0, 100.0
        z = edge.snapshot(e, s2, 23000.0 + k * 0.5, 23020.0 + k * 0.5)
    assert z["fut_ofi60"] > 0 and z["fut_micro"] > 0 and z["syn_dev"] is not None
    assert edge.signed(z, -1)["fut_ofi60"] == -z["fut_ofi60"]
    e._spot_bad = "garbage"                                    # an untrusted index: no spot-derived feature
    y = edge.snapshot(e, snap, 23000.0, 23020.0)
    assert y["basis_dev"] is None and y["wall_up"] is None


def test_trade_carries_the_edge_and_the_report_ranks_it():
    b = paper.Book("spot_pb45", config.VARIANTS["spot_pb45"], "2026-10-21")
    T0 = datetime(2026, 10, 21, 10, 30, tzinfo=config.IST)
    opt = {"id": 5, "key": "NIFTY|OPT|2026-10-27|23000|PE", "strike": 23000, "rr": "PE", "expiry": "2026-10-27",
           "ltp": 200.0, "bid": 199.9, "ask": 200.1, "delta": -0.55, "iv": 14.0, "age": 0.1}
    ctx = {"now_s": 1000.0, "now_dt": T0, "fut": 23015.0, "fut_mid": 23015.0, "spot": 23000.0, "advisors": {},
           "edge": {"fut_imb5": 0.4, "basis_dev": 2.0, "imp_d": -1, "wall_up": 30.0, "wall_dn": 60.0},
           "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0}, "regime": {}}
    paper.open_trade(b, ctx, dict(opt), "t")
    assert b.pos["edge_in"]["fut_imb5"] == -0.4 and b.pos["edge_in"]["imp_with"] == 1 and b.pos["edge_in"]["wall_room"] == 60.0
    # the report: 14 synthetic trades where fut_imb5 tracks the return
    trades = [{"ret_pct": r, "edge_in": {"fut_imb5": r / 10.0, "iv_rv": 1.2}} for r in range(-7, 7)]
    with open(os.path.join(config.PAPER_DIR, "2026-10-21.json"), "w", encoding="utf-8") as f:
        json.dump({"spot_pb45": {"trades": trades}}, f)
    lines = edge.report_lines(config.PAPER_DIR)
    row = next(x for x in lines if x.startswith("| fut_imb5 |"))
    assert row.rstrip().endswith("1 |"), row                   # Spearman +1


# ── D-137: the dual shadow takes the retest on expiry day and the pullback on other days ──────────────────────
def test_dual_mode_routes_by_expiry_day():
    p = config.VARIANTS["spot_dual"]
    assert p["entry_mode"] == "pullback" and p["dte0_retest"] and p["retest_ext"] == config.RETEST_EXT_PTS
    assert config.validate() == []
    b = paper.Book("spot_dual", p, "2026-10-19")
    exp_day = datetime(2026, 10, 19, 10, 0, tzinfo=config.IST)
    c = {"now_s": 1000.0, "now_dt": exp_day, "w0": "2026-10-19", "spot": 25201.0, "spot_hi": 25200.0, "spot_lo": 25150.0,
         "spot_age": 0.3, "pb": {"ok": False}, "fut": 25211.0, "fut_ltp": 25211.0, "advisors": {}, "blackout": {"on": False},
         "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
         "episode": None, "regime": {"state": "RANGE", "dir": None}}
    ok, why = paper.evaluate_entry(b, c, [])
    assert not ok and "armed" in why                          # expiry day: the retest arms the break
    b2 = paper.Book("spot_dual", p, "2026-10-21")
    c2 = dict(c, now_dt=datetime(2026, 10, 21, 10, 0, tzinfo=config.IST), w0="2026-10-27")
    ok, why = paper.evaluate_entry(b2, c2, [])
    assert not ok and "45-min" in why                         # other days: the pullback book


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"):
            fn(); print("ok", k)
