"""c20_9e (expiry give-back trail) and c20_9h (half-of-peak expiry floor): shadow books beside c20_9x, 3 Nov 2026."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from apex import config  # noqa: E402
from apex.engine.council import c20_9e, c20_9h, c20_9x  # noqa: E402


def test_registered_as_shadows_beside_c20_9x():
    assert config.VARIANTS["c20_9e"]["council"] == "c20_9e" and config.VARIANTS["c20_9h"]["council"] == "c20_9h"
    assert config.CHAMPION_DEFAULT == "c20_9x"
    for m in (c20_9e, c20_9h):
        assert issubclass(m.Strategy, c20_9x.LiveStrategy) and issubclass(m.KitStrategy, c20_9x.KitStrategy)
        assert m.Strategy().parts == c20_9x.Strategy().parts        # same switches; only the expiry floor added
    assert c20_9e.XT == {"ARM": 5.0, "GIVE": 6.0} and c20_9h.HL == {"ARM": 0.15, "KEEP": 0.5}


def test_expiry_trail_arms_at_plus_5_pts_and_gives_back_6():
    s = c20_9e.Strategy()
    e = 80.0
    assert s._floor(e, 4.9 / e, True) == (None, None)                # peak +4.9 pts: nothing armed (c20_9x: nothing below +15 %)
    fl, kind = s._floor(e, 5.0 / e, True)
    assert kind == "EXP_TRAIL" and abs(fl - 79.0) < 1e-9             # peak 85 -> floor 79
    fl, kind = s._floor(e, 12.0 / e, True)
    assert kind == "EXP_TRAIL" and abs(fl - 86.0) < 1e-9             # peak 92 -> floor 86 (above the BE_LOCK entry floor)
    fl, kind = s._floor(e, 0.70, True)                               # peak +70 % = 136: GIVEBACK keeps 70 % -> 119.2 < 130
    assert kind == "EXP_TRAIL" and abs(fl - 130.0) < 1e-9
    fl, kind = s._floor(400.0, 0.70, True)                           # a 400 premium: GIVEBACK 596, trail 674: the higher floor wins
    assert kind == "EXP_TRAIL" and abs(fl - 674.0) < 1e-9


def test_expiry_trail_leaves_normal_days_to_c20_9x():
    s, x = c20_9e.Strategy(), c20_9x.Strategy()
    for g in (0.03, 0.10, 0.20, 0.40, 0.80):
        assert s._floor(100.0, g, False) == x._floor(100.0, g, False)


def test_half_of_peak_floor_on_expiry_days():
    s = c20_9h.Strategy()
    assert s._floor(100.0, 0.149, True) == (None, None)
    assert s._floor(100.0, 0.15, True) == (107.5, "HALF_LOCK")
    fl, kind = s._floor(100.0, 0.30, True)
    assert kind == "HALF_LOCK" and abs(fl - 115.0) < 1e-9
    fl, kind = s._floor(100.0, 0.60, True)
    assert kind == "GIVEBACK" and abs(fl - 142.0) < 1e-9               # from +60 % c20_9x's 70 % floor is the higher one
    x = c20_9x.Strategy()
    for g in (0.10, 0.20, 0.40):
        assert s._floor(100.0, g, False) == x._floor(100.0, g, False)


def test_dashboard_names_the_new_exits():
    js = open(os.path.join(ROOT, "apex", "static", "app.js"), encoding="utf-8").read()
    assert 'EXP_TRAIL: "' in js and 'HALF_LOCK: "' in js
