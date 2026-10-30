"""30 Oct (D-145): council books — c20_9x champion, c20_8x shadow, run through apex/engine/council.Adapter."""
import importlib

from apex import config


def test_council_books_registered_and_champion():
    assert config.CHAMPION_DEFAULT == "c20_9x" and config.CHAMPION_OWNER == ("c20_9x", "2026-10-30")
    for n in ("c20_8x", "c20_9x"):
        assert config.VARIANTS[n]["council"] == n
        assert n not in config.CONTROLS
    assert "council" in config.VARIANT_KEYS and config.validate() == []
    assert "t28_gap" in config.VARIANTS                # yesterday's champion stays as a shadow


def test_council_strategies_import_and_build():
    for n in ("c20_8x", "c20_9x"):
        m = importlib.import_module(f"apex.engine.council.{n}")
        s = m.Strategy()
        assert hasattr(s, "on_second")
    m = importlib.import_module("apex.engine.council.c20_9x")
    assert set(("l2", "ffirst", "seqcal", "catch", "dtr", "ramp", "ivz", "ptre", "tie")) <= set(m.FINAL_R9)


def test_live_day_shapes():
    from apex.engine import council
    D = council.LiveDay("2026-10-30", "2026-11-03")
    assert D.bid.shape == (council.N_ROWS, council.MAXC) and not D.dte0
    assert abs(D.hm[0] - 555.0) < 1e-9
