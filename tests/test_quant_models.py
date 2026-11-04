"""apex.quant: Hawkes, microstructure, regime HMM and SVI against known answers on simulated data."""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex.quant import hawkes, micro, regime, svi  # noqa: E402


# ------------------------------------------------------------------ Hawkes
def test_hawkes_mle_recovers_simulated_parameters():
    rng = np.random.default_rng(3)
    mu, a, b, T = 0.4, 0.6, 1.0, 6000.0
    t = hawkes.simulate(mu, a, b, T, rng)
    m2, a2, b2, _ = hawkes.fit(t, T)
    assert m2 == pytest.approx(mu, rel=0.2)
    assert a2 / b2 == pytest.approx(a / b, abs=0.08)              # branching ratio 0.6


def test_hawkes_streaming_intensity_matches_the_definition():
    h = hawkes.Hawkes(0.5, 0.8, 0.5)
    ev = [1.0, 1.5, 4.0]
    for t in ev:
        h.add(t)
    t = 6.0
    direct = 0.5 + sum(0.8 * math.exp(-0.5 * (t - s)) for s in ev)
    assert h.intensity(t) == pytest.approx(direct)
    assert h.excitation(t) == pytest.approx(direct / 0.5)
    assert h.branching == pytest.approx(1.6)


def test_hawkes_loglik_of_poisson_is_poisson():
    t = np.array([1.0, 2.5, 7.0])
    assert hawkes.loglik((0.3, 0.0, 1.0), t, 10.0) == pytest.approx(3 * math.log(0.3) - 3.0)


# ------------------------------------------------------------------ micro
def test_bipower_ignores_a_jump_that_realised_variance_counts():
    rng = np.random.default_rng(1)
    r = rng.normal(0, 1.0, 300)
    rv = micro.RollingVar(300)
    for x in r:
        rv.add(x)
    s0 = rv.sigma()
    assert s0 == pytest.approx(1.0, rel=0.15)
    assert rv.jump()[1] < 3.0                                      # no jump in pure noise
    rv2 = micro.RollingVar(300)
    r2 = r.copy()
    r2[150] = 25.0                                                 # one 25-sigma jump
    for x in r2:
        rv2.add(x)
    assert rv2.sigma() == pytest.approx(s0, rel=0.15)              # bipower barely moves
    assert rv2.rv() > 2.5 * rv.rv()                                # realised variance explodes
    assert rv2.jump()[1] > 3.0


def test_rolling_window_forgets():
    rv = micro.RollingVar(10)
    for _ in range(10):
        rv.add(5.0)
    for _ in range(10):
        rv.add(1.0)
    assert rv.rv() == pytest.approx(10.0)


def test_cusum_alarms_on_a_drift_and_not_on_noise():
    rng = np.random.default_rng(2)
    c = micro.Cusum(k=0.5, h=5.0)
    assert all(c.add(z) == 0 for z in rng.normal(0, 1, 50))
    c.reset()
    states = [c.add(z) for z in rng.normal(1.5, 1, 30)]
    assert 1 in states and -1 not in states


def test_kyle_lambda_recovers_the_impact_slope():
    rng = np.random.default_rng(4)
    k = micro.KyleLambda(500)
    for q in rng.normal(0, 100, 500):
        k.add(0.02 * q + rng.normal(0, 0.5), q)
    assert k.value() == pytest.approx(0.02, rel=0.1)


def test_kalman_velocity_tracks_a_trend():
    rng = np.random.default_rng(5)
    kv = micro.KalmanVelocity(q_v=1e-4, q_x=0.05, r=0.5)
    for t in range(600):
        kv.add(23800 + 0.1 * t + rng.normal(0, 0.7))
    assert kv.v == pytest.approx(0.1, abs=0.03)
    assert kv.t_stat() > 1.5
    flat = micro.KalmanVelocity(q_v=1e-4, q_x=0.05, r=0.5)
    for t in range(600):
        flat.add(23800 + rng.normal(0, 0.7))
    assert abs(flat.t_stat()) < 1.5 and abs(flat.v) < 0.03


# ------------------------------------------------------------------ regime
def test_hmm_finds_two_planted_regimes_and_filters_causally():
    rng = np.random.default_rng(6)
    seqs, truth = [], []
    for _ in range(6):
        z = np.repeat(rng.integers(0, 2, 12), 20)                  # regimes lasting 20 bars
        x = np.column_stack([np.where(z == 1, 3.0, -3.0) + rng.normal(0, 1, len(z)),
                             np.where(z == 1, 2.0, 1.0) + rng.normal(0, 0.2, len(z))])
        seqs.append(x)
        truth.append(z)
    m = regime.GaussianHMM(K=2, seed=1).fit(seqs, restarts=3)
    path = m.viterbi(seqs[0])
    assert np.mean(path == truth[0]) > 0.95                        # states ordered by mean return
    m.reset()
    post = [m.filter(x)[1] for x in seqs[0]]
    assert np.mean((np.array(post) > 0.5) == (truth[0] == 1)) > 0.9
    runs = []                                                      # true run lengths of state 1 (blocks can merge)
    for z in truth:
        r = 0
        for v in list(z) + [-1]:
            if v == 1:
                r += 1
            elif r:
                runs.append(r)
                r = 0
    runs = np.array(runs, float)
    want = runs[runs > 5].mean() - 5
    assert m.remaining(1, 5) == pytest.approx(want, rel=0.15)      # semi-Markov: E[D - 5 | D > 5]
    assert m.remaining(1, 10 ** 6) == 0.0
    m2 = regime.GaussianHMM.from_dict(m.to_dict())
    assert np.allclose(m2.A, m.A) and m2.remaining(1, 5) == m.remaining(1, 5)


def test_bar_features_shape():
    f = 23800 + np.cumsum(np.ones(601) * 0.1)
    x = regime.bar_features(f, 60)
    assert x.shape == (10, 2) and x[0, 0] == pytest.approx(6.0)


# ------------------------------------------------------------------ SVI
def test_svi_recovers_a_planted_smile_and_flags_a_rich_strike():
    F, T = 23810.0, 2.0 / 365
    p = np.array([0.00002, 0.0004, -0.4, 0.0, 0.01])
    K = np.arange(23300, 24350, 50.0)
    iv = svi.iv_at(p, K, F, T)
    q = svi.fit(K, iv, F, T)
    assert np.max(np.abs(svi.iv_at(q, K, F, T) - iv)) < 1e-3
    iv2 = iv.copy()
    iv2[10] += 0.02                                                # one strike 2 vol pts rich
    q2 = svi.fit(K, iv2, F, T)
    res = svi.residual(q2, K, iv2, F, T)
    assert int(np.argmax(res)) == 10 and res[10] > 1.0


def test_binned_hawkes_fit_recovers_branching_and_filter_is_causal():
    rng = np.random.default_rng(11)
    # 10-s kernel: at 1-s bins little excitation is lost inside a bin (a 1-s kernel would be badly aliased)
    t = hawkes.simulate(0.3, 0.05, 0.1, 20000.0, rng)
    counts = np.bincount(np.floor(t).astype(int), minlength=20000)[:20000]
    mu, a, b, _ = hawkes.fit_binned([counts])
    assert a / b == pytest.approx(0.5, abs=0.12)
    assert mu == pytest.approx(0.3, rel=0.3)
    e = hawkes.excitation_series(np.array([0, 3, 0, 0]), 0.5, 1.0)
    assert e[1] == 0.0 and e[2] == pytest.approx(1.5) and e[3] == pytest.approx(1.5 * math.exp(-1.0))


def test_rolling_var_ignores_repeated_prices_and_scales_by_time():
    rng = np.random.default_rng(9)
    a, b = micro.RollingVar(300), micro.RollingVar(300)
    for x in rng.normal(0, 1.0, 300):
        a.add(x, 1.0)
        b.add(0.0, 1.0)                                            # a frozen feed adds nothing
        b.add(x * math.sqrt(4.0), 4.0)                             # the same noise sampled every 4 s
    assert b.count == 300
    assert b.sigma() == pytest.approx(a.sigma(), rel=0.02)         # per-second noise is unchanged
