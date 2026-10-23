"""Council 6 (21 Oct) M10: the NIFTY index sanity guard (D-132). python tests/test_c6_feed.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_wp2 as W  # noqa: E402  (sets APEX_DATA, FILL_NEXT_PRINT and imports the engine)

from apex import config  # noqa: E402


def _feed(rig, F, spot, secs):
    """Advance `secs` seconds (0.1 s steps) with the future at F and the index row forced to `spot`."""
    for _ in range(int(secs * 10)):
        rig.now += 0.1
        rig.write(F)
        r = rig.t.rows
        r["ltp"][rig.spot] = spot; r["bid"][rig.spot] = spot - 0.5; r["ask"][rig.spot] = spot + 0.5
        rig.eng.step()


def test_a_wild_print_is_refused_and_everything_recovers():
    rig = W.Rig("c6a", "2026-10-21")
    try:
        rig.warm()                                       # future 25210, spot 25200 (basis +10)
        eng = rig.eng
        assert eng._spot_bad == "" and eng.ctx["spot"] is not None
        n = len(eng.spot_hist)
        _feed(rig, 25210.0, 25200.0 + 501.0, 3.0)        # the vendor index jumps +501 (19 and 21 Oct, 15:20)
        assert eng._spot_bad and "off its usual spread" in eng._spot_bad
        assert eng.ctx["spot"] is None and eng.ctx["spot_age"] == 9e9
        assert max(px for _, px in eng.spot_hist) < 25300.0, "the wild print must never enter the range history"
        ok, why = W.paper.evaluate_entry(rig.champ(), eng.ctx, [])
        assert not ok, why
        assert "old" in why or "warming" in why, why
        _feed(rig, 25210.0, 25200.0, 2.0)
        assert eng._spot_bad == "" and eng.ctx["spot"] == 25200.0
    finally:
        rig.close()


def test_a_frozen_index_with_a_moving_future_is_refused():
    rig = W.Rig("c6b", "2026-10-21")
    try:
        rig.warm()
        eng = rig.eng
        for k in range(30):                              # 30 s: spot frozen at 25200, future walks up 10 pts
            _feed(rig, 25210.0 + k * 0.4, 25200.0, 1.0)
        assert eng._spot_bad.startswith("spot unchanged"), eng._spot_bad
        assert eng.ctx["spot"] is None
        _feed(rig, 25222.0, 25212.0, 1.5)                # it moves again
        assert eng._spot_bad == ""
    finally:
        rig.close()


def test_a_quiet_but_alive_market_is_never_flagged():
    rig = W.Rig("c6c", "2026-10-21")
    try:
        rig.warm()
        for k in range(60):                              # spot and future both flat for 60 s: not a feed fault
            _feed(rig, 25210.0, 25200.0, 1.0)
            assert rig.eng._spot_bad == ""
    finally:
        rig.close()


def test_an_open_position_falls_back_to_the_futures_stop_when_spot_is_untrusted():
    rig = W.Rig("c6d", "2026-10-21")
    try:
        rig.warm()
        pos = rig.open_ce()
        pos["spot_in"] = 25200.0
        pos["best_spot"] = 25200.0
        _feed(rig, 25210.0, 25200.0 + 501.0, 1.5)        # garbage index; the future has not moved
        assert rig.champ().pos is not None, "a wild index print must not stop a PE/CE out"
        assert rig.champ().pos["best_spot"] == 25200.0, "the wild print must not become the best spot"
        _feed(rig, 25190.0, 25200.0 + 501.0, 1.5)        # now the FUTURE falls 12+ pts below its entry/trail
        assert rig.champ().pos is None, "the futures-mid stop must still protect the position"
    finally:
        rig.close()


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"):
            fn(); print("ok", k)
