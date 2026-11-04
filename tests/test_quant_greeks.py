"""apex.quant.greeks_hi: every Greek against a central finite difference of the exact Black-76 price."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex.quant import greeks_hi as G  # noqa: E402

CASES = [(23810.0, 23800.0, 2.4 / 24 / 365, 0.14, True),     # expiry-day ATM call, 2.4 h left
         (23810.0, 23850.0, 3.0 / 365, 0.12, False),         # 3-day ITM put
         (23810.0, 23700.0, 6.0 / 365, 0.11, True)]          # 6-day ITM call


def _fd(f, x, h):
    return (f(x + h) - f(x - h)) / (2 * h)


@pytest.mark.parametrize("F,K,T,s,c", CASES)
def test_first_and_second_order(F, K, T, s, c):
    g = G.all_greeks(F, K, T, s, c)
    P = lambda F_=F, T_=T, s_=s: float(G.price(F_, K, T_, s_, c))  # noqa: E731
    assert float(g["delta"]) == pytest.approx(_fd(lambda x: P(F_=x), F, 0.01), rel=1e-5, abs=1e-7)
    assert float(g["gamma"]) == pytest.approx(_fd(lambda x: float(G.all_greeks(x, K, T, s, c)["delta"]), F, 0.01), rel=1e-4)
    assert float(g["vega"]) == pytest.approx(_fd(lambda x: P(s_=x), s, 1e-5), rel=1e-5)
    assert float(g["theta"]) == pytest.approx(-_fd(lambda x: P(T_=x), T, T * 1e-4), rel=1e-4)


@pytest.mark.parametrize("F,K,T,s,c", CASES)
def test_higher_order(F, K, T, s, c):
    g = G.all_greeks(F, K, T, s, c)
    gk = lambda k, **kw: float(G.all_greeks(kw.get("F", F), K, kw.get("T", T), kw.get("s", s), c)[k])  # noqa: E731
    assert float(g["vanna"]) == pytest.approx(_fd(lambda x: gk("delta", s=x), s, 1e-5), rel=1e-4)
    assert float(g["vomma"]) == pytest.approx(_fd(lambda x: gk("vega", s=x), s, 1e-5), rel=1e-4, abs=1e-6)
    assert float(g["charm"]) == pytest.approx(-_fd(lambda x: gk("delta", T=x), T, T * 1e-4), rel=1e-4, abs=1e-9)
    assert float(g["speed"]) == pytest.approx(_fd(lambda x: gk("gamma", F=x), F, 0.01), rel=1e-3)
    assert float(g["color"]) == pytest.approx(-_fd(lambda x: gk("gamma", T=x), T, T * 1e-4), rel=1e-4)
    assert float(g["zomma"]) == pytest.approx(_fd(lambda x: gk("gamma", s=x), s, 1e-5), rel=1e-4)
    assert float(g["ultima"]) == pytest.approx(_fd(lambda x: gk("vomma", s=x), s, 1e-5), rel=1e-3, abs=1e-5)


def test_parity_and_agreement_with_engine_pricer():
    from apex import greeks as old
    F, K, T, s = 23810.0, 23800.0, 1.0 / 365, 0.13
    c, p = float(G.price(F, K, T, s, True)), float(G.price(F, K, T, s, False))
    assert c - p == pytest.approx(F - K, abs=1e-9)
    assert c == pytest.approx(float(old.b76_price(F, K, T, s, True)), abs=1e-3)   # the engine's erf approximation


def test_taylor_beats_delta_gamma_on_a_joint_move():
    F, K, T, s = 23810.0, 23800.0, 2.0 / 24 / 365, 0.14
    g = G.all_greeks(F, K, T, s, True)
    dF, ds, dt = 40.0, -0.02, 600.0 / G.YEAR_S
    true = float(G.price(F + dF, K, T - dt, s + ds, True) - G.price(F, K, T, s, True))
    dg = float(g["delta"] * dF + 0.5 * g["gamma"] * dF * dF + g["vega"] * ds + g["theta"] * dt)
    assert abs(float(G.taylor(g, dF, ds, dt)) - true) < abs(dg - true)


def test_forward_for_premium_inverts_the_price():
    F, K, T, s = 23810.0, 23800.0, 1.0 / 365, 0.13
    for c in (True, False):
        p0 = float(G.price(F, K, T, s, c))
        f_up = G.forward_for_premium(p0 * 1.1, K, T, s, c, F * 0.8, F * 1.2)
        assert float(G.price(f_up, K, T, s, c)) == pytest.approx(p0 * 1.1, abs=1e-3)
        assert (f_up > F) == c
    assert np.isnan(G.forward_for_premium(1e9, K, T, s, True, F * 0.8, F * 1.2))


def test_scalar_price_and_delta_match_the_vector_ones():
    for (F, K, T, s, c) in CASES:
        assert G.price_s(F, K, T, s, c) == pytest.approx(float(G.price(F, K, T, s, c)), abs=1e-9)
        assert G.delta_s(F, K, T, s, c) == pytest.approx(float(G.all_greeks(F, K, T, s, c)["delta"]), abs=1e-12)
