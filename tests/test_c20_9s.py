"""c20_9s: c20_9x + the stale-impulse pullback veto (panel C11, 3 Nov 2026 night); shadow book."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from apex import config  # noqa: E402
from apex.engine.council import c20_9s, c20_9x  # noqa: E402


def test_registered_as_shadow_beside_c20_9x():
    assert config.VARIANTS["c20_9s"]["council"] == "c20_9s" and config.CHAMPION_DEFAULT == "c20_9x"
    assert issubclass(c20_9s.Strategy, c20_9x.LiveStrategy) and issubclass(c20_9s.KitStrategy, c20_9x.KitStrategy)
    assert c20_9s.Strategy().parts == c20_9x.Strategy().parts
    assert c20_9s.SI == {"PB_AGE_MAX": 660}


class _D:
    def __init__(self, dte0):
        self.dte0 = dte0


class _Core:
    """Stands in for c20_9x: _pullback fires with the arm set at `armed_at`; on_second returns a BUY through it."""
    def __init__(self, armed_at):
        self.arm = ["CE", 0.0, 0.0, 0.0, armed_at]
        self.blocked = {}

    def _veto(self, why):
        self.blocked[why] = self.blocked.get(why, 0) + 1
        return None

    def _pullback(self, i, fs, v, side, p):
        self.arm = None                       # the core clears the arm when the pullback fires
        return "CE"

    def on_second(self, i, D, pos):
        self._pullback(i, 0.0, 0.0, None, {})
        return ("BUY", 23000, "CE", "NORM pb v=+25")


class _S(c20_9s._SIMixin, _Core):
    pass


def test_a_pullback_on_an_old_impulse_is_refused_on_normal_days():
    s = _S(armed_at=1000)
    assert s.on_second(1661, _D(False), None) is None                 # impulse 661 s old: refused
    assert s.blocked == {"stale_impulse": 1} and s.si_vetoes == 1


def test_a_fresh_impulse_or_an_expiry_day_is_left_alone():
    s = _S(armed_at=1000)
    assert s.on_second(1660, _D(False), None)[0] == "BUY"             # exactly 660 s: allowed
    s = _S(armed_at=0)
    assert s.on_second(5000, _D(True), None)[0] == "BUY"              # expiry day: c20_9x unchanged
