"""apex.quant.passage: the two-barrier first-passage profile against closed forms and a Monte Carlo."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex.quant import passage as P  # noqa: E402


@pytest.mark.parametrize("mu", [0.0, 0.05, -0.05, 0.3])
def test_long_horizon_matches_scale_function(mu):
    up, dn, ever = P.two_barrier(20.0, 15.0, mu, 1.2, [1e6])
    assert up[0] == pytest.approx(ever, abs=2e-3)
    assert up[0] + dn[0] == pytest.approx(1.0, abs=2e-3)


def test_driftless_split_is_b_over_a_plus_b():
    assert P.up_first_ever(20.0, 15.0, 0.0, 1.0) == pytest.approx(15.0 / 35.0)
    assert P.up_first_ever(20.0, 15.0, 1e-12, 1.0) == pytest.approx(15.0 / 35.0, abs=1e-9)


def test_one_sided_limit_is_inverse_gaussian():
    from scipy.special import ndtr
    a, mu, s, H = 20.0, 0.04, 1.1, 600.0
    up, _, _ = P.two_barrier(a, 1e4, mu, s, [H])
    ig = ndtr((mu * H - a) / (s * np.sqrt(H))) + np.exp(2 * mu * a / s ** 2) * ndtr((-a - mu * H) / (s * np.sqrt(H)))
    assert up[0] == pytest.approx(ig, abs=2e-3)


def test_against_monte_carlo():
    rng = np.random.default_rng(7)
    a, b, mu, s, dt, H = 12.0, 9.0, 0.02, 1.0, 0.05, 300.0
    n = 4000
    x = np.zeros(n)
    hit = np.zeros(n)                       # +1 up, -1 down, 0 none
    t_hit = np.full(n, np.inf)
    for k in range(int(H / dt)):
        live = hit == 0
        x[live] += mu * dt + s * np.sqrt(dt) * rng.standard_normal(live.sum())
        u = live & (x >= a)
        d = live & (x <= -b)
        hit[u], hit[d] = 1, -1
        t_hit[u | d] = (k + 1) * dt
    hs = [60.0, 180.0, 300.0]
    up, dn, _ = P.two_barrier(a, b, mu, s, hs)
    for h, pu, pd in zip(hs, up, dn):
        assert pu == pytest.approx(np.mean((hit == 1) & (t_hit <= h)), abs=0.03)   # discrete MC overshoots a little
        assert pd == pytest.approx(np.mean((hit == -1) & (t_hit <= h)), abs=0.03)


def test_premium_outcome_theta_is_a_headwind_and_drift_helps():
    F, K, T, s_iv = 23810.0, 23800.0, 3.0 / 24 / 365, 0.14
    from apex.quant import greeks_hi as G
    P0 = float(G.price(F, K, T, s_iv, True))
    flat = P.premium_outcome(F, K, T, s_iv, True, P0, 0.10, 0.10, 0.0, 1.0)
    run = P.premium_outcome(F, K, T, s_iv, True, P0, 0.10, 0.10, 0.08, 1.0)
    assert flat["mu_eff"] < 0                                    # pure decay
    assert run["up_ever"] > flat["up_ever"]
    assert flat["a"] > 0 and flat["b"] > 0
    put = P.premium_outcome(F, K, T, s_iv, False, float(G.price(F, K, T, s_iv, False)), 0.10, 0.10, -0.08, 1.0)
    assert put["up_ever"] > 0.5                                  # falling forward favours the put
