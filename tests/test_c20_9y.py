"""c20_9y: c20_9x + the IV-rich and OI-wall entry vetoes (panel C12, 4 Nov 2026 night); shadow book."""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from apex import config  # noqa: E402
from apex.engine.council import c20_9x, c20_9y  # noqa: E402


def test_registered_as_shadow_beside_c20_9x():
    assert config.VARIANTS["c20_9y"]["council"] == "c20_9y" and config.CHAMPION_DEFAULT == "c20_9x"
    assert issubclass(c20_9y.Strategy, c20_9x.LiveStrategy) and issubclass(c20_9y.KitStrategy, c20_9x.KitStrategy)
    assert c20_9y.Strategy.IV_SCALE == 1.0 and c20_9y.KitStrategy.IV_SCALE == 100.0
    assert c20_9y.Y == dict(IVR=3.5, IV_AVG=30, IV_MIN_S=300, W=250, DMAX=25)


class _D:
    """Two strikes (23800, 23850), CE and PE; N seconds from 09:15."""
    def __init__(self, N=1200, dte0=False, fwd=23810.0):
        self.day, self.dte0 = "2026-11-05", dte0
        self.T = np.arange(N, dtype=float)
        self.K = np.array([23800, 23800, 23850, 23850])
        self.col = {(23800, "CE"): 0, (23800, "PE"): 1, (23850, "CE"): 2, (23850, "PE"): 3}
        self.fwd = np.full(N, fwd)
        self.spot = self.fwd.copy()
        self.iv = np.full((N, 4), 12.0)
        self.oi = np.full((N, 4), 1000.0)

    def i_at(self, hh, mm, ss=0):
        return (hh * 3600 + mm * 60 + ss) - (9 * 3600 + 15 * 60)


class _Core:
    def __init__(self):
        self.blocked = {}

    def _veto(self, why):
        self.blocked[why] = self.blocked.get(why, 0) + 1
        return None

    def on_second(self, i, D, pos):
        return ("BUY", 23800, "CE", "NORM pb v=+25")


class _S(c20_9y._YMixin, _Core):
    IV_SCALE = 1.0


def _run(D, upto):
    s = _S()
    out = None
    for i in range(upto + 1):
        out = s.on_second(i, D, None)
    return s, out


def test_iv_spike_refuses_the_buy():
    D = _D()
    D.iv[1000:, :2] = 16.0                                  # ATM IV +4 vol pts above its median since 09:20
    s, out = _run(D, 1100)
    assert out is None and set(s.blocked) == {"iv_rich"}           # the fake core offers a BUY every second


def test_calm_iv_and_no_wall_lets_the_buy_through():
    D = _D()
    s, out = _run(D, 1100)
    assert out[0] == "BUY" and s.blocked == {}


def test_call_wall_just_ahead_refuses_a_ce_buy_on_normal_days_only():
    D = _D()
    D.oi[:, 2] = 9000.0                                     # 23850 CE wall, 40 pts ahead: too far, allowed
    assert _run(D, 900)[1][0] == "BUY"
    D.fwd[:] = D.spot[:] = 23830.0                          # now 20 pts ahead: refused
    s, out = _run(D, 900)
    assert out is None and set(s.blocked) == {"oi_wall"}
    D.dte0 = True                                           # expiry days: no wall veto
    assert _run(D, 900)[1][0] == "BUY"


def test_wall_ahead_sign():
    D = _D(fwd=23830.0)
    D.oi[:, 2] = 9000.0
    D.oi[:, 1] = 9000.0
    assert c20_9y.wall_ahead(D, 0, "CE", 250) == 20.0       # call wall above a CE buy: ahead
    assert c20_9y.wall_ahead(D, 0, "PE", 250) == 30.0       # put wall 30 pts below a PE buy: ahead


def test_runs_on_the_engines_live_day():
    """5 Nov: the engine's LiveDay lacked i_at, so c20_9y faulted on its first second in the engine."""
    from apex.engine.council import LiveDay
    D = LiveDay("2026-11-05", "2026-11-10")
    assert D.i_at(9, 15) == 0 and D.i_at(9, 20) == 300 and D.i_at(15, 30) == len(D.T) - 1
    s = c20_9y.Strategy()
    for i in range(400):                     # empty rows: no quotes yet, the strategy must simply stay flat
        assert s.on_second(i, D, None) is None
