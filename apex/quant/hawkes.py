"""Self-exciting (Hawkes) event intensity, exponential kernel:

    lambda(t) = mu + sum_{t_i < t} alpha * exp(-beta (t - t_i))

Streaming update in O(1): between events the excitation decays by exp(-beta dt); each event adds alpha. The
branching ratio n = alpha / beta is the share of events triggered by earlier events (n -> 1: a chain reaction).

`fit` estimates (mu, alpha, beta) by maximum likelihood on event times (exact continuous-time log-likelihood,
Ozaki recursion), multi-start L-BFGS on log-parameters with the stationarity bound alpha < beta.
`excitation()` = lambda / mu is the live input: how many times its baseline the flow is running now.
"""
import math

import numpy as np
from scipy.optimize import minimize


class Hawkes:
    __slots__ = ("mu", "alpha", "beta", "t", "ex")

    def __init__(self, mu, alpha, beta):
        self.mu, self.alpha, self.beta = float(mu), float(alpha), float(beta)
        self.t = None
        self.ex = 0.0                        # excitation part of the intensity, at time self.t

    def decay_to(self, t):
        if self.t is not None and t > self.t:
            self.ex *= math.exp(-self.beta * (t - self.t))
        if self.t is None or t > self.t:
            self.t = t

    def add(self, t, n=1.0):
        """n events at time t (n may be fractional, e.g. lots / typical lot)."""
        self.decay_to(t)
        self.ex += self.alpha * n

    def intensity(self, t=None):
        if t is not None:
            self.decay_to(t)
        return self.mu + self.ex

    def excitation(self, t=None):
        return self.intensity(t) / self.mu

    @property
    def branching(self):
        return self.alpha / self.beta


def loglik(params, times, T):
    """Exact Hawkes log-likelihood on [0, T] for sorted event times (Ozaki 1979 recursion)."""
    mu, alpha, beta = params
    if mu <= 0 or alpha < 0 or beta <= 0:
        return -np.inf
    times = np.asarray(times, float)
    if len(times) == 0:
        return -mu * T
    A = np.zeros(len(times))
    e = np.exp(-beta * np.diff(times))
    for i in range(1, len(times)):
        A[i] = e[i - 1] * (1.0 + A[i - 1])
    lam = mu + alpha * A
    comp = mu * T + (alpha / beta) * np.sum(1.0 - np.exp(-beta * (T - times)))
    return float(np.sum(np.log(lam)) - comp)


def fit(times, T, starts=((0.5, 0.3), (0.2, 0.05), (0.8, 0.01))):
    """MLE (mu, alpha, beta). `starts` are (branching ratio, beta) pairs; mu starts at the rate they imply.
    Returns (mu, alpha, beta, loglik)."""
    times = np.sort(np.asarray(times, float))
    n = len(times)
    if n < 10 or T <= 0:
        return (max(n, 1) / max(T, 1.0), 0.0, 1.0, float("nan"))
    best = None
    for br, b0 in starts:
        x0 = np.log([n / T * (1 - br), br * b0, b0])

        def nll(x):
            mu, a, b = np.exp(x)
            if a >= b:                         # non-stationary: penalise smoothly
                return 1e12 * (1 + a - b)
            return -loglik((mu, a, b), times, T)
        r = minimize(nll, x0, method="L-BFGS-B")
        if best is None or r.fun < best.fun:
            best = r
    mu, a, b = np.exp(best.x)
    return float(mu), float(a), float(b), float(-best.fun)


def simulate(mu, alpha, beta, T, rng):
    """Ogata thinning (for tests)."""
    t, out, ex = 0.0, [], 0.0
    while True:
        lam_bar = mu + ex
        w = rng.exponential(1.0 / lam_bar)
        t += w
        if t > T:
            return np.array(out)
        ex *= math.exp(-beta * w)
        if rng.uniform() * lam_bar <= mu + ex:
            out.append(t)
            ex += alpha


def excitation_series(counts, alpha, beta, dt=1.0):
    """Excitation part of a binned Hawkes intensity: e_t = sum_{s < t} alpha exp(-beta (t - s) dt) n_s.
    Causal (bin t sees counts up to t - 1). Linear IIR filter, so a whole day costs microseconds."""
    from scipy.signal import lfilter
    n = np.asarray(counts, float)
    d = math.exp(-beta * dt)
    y = lfilter([0.0, alpha], [1.0, -d], n)          # y_t = d y_{t-1} + alpha n_{t-1}
    return y


def fit_binned(counts_list, dt=1.0, starts=((0.5, 0.3), (0.2, 0.05), (0.8, 0.01))):
    """MLE of (mu, alpha, beta) for Poisson counts per bin with intensity mu + excitation (several sequences,
    e.g. one per day, sharing the parameters). Returns (mu, alpha, beta, loglik)."""
    seqs = [np.asarray(c, float) for c in counts_list if len(c) > 10]
    tot, n = sum(c.sum() for c in seqs), sum(len(c) for c in seqs)
    rate = max(tot / (n * dt), 1e-6)
    best = None
    for br, b0 in starts:
        x0 = np.log([rate * (1 - br), br * b0, b0])

        def nll(x):
            mu, a, b = np.exp(x)
            if a >= b:
                return 1e12 * (1 + a - b)
            ll = 0.0
            for c in seqs:
                lam = (mu + excitation_series(c, a, b, dt)) * dt
                ll += float(np.sum(c * np.log(lam) - lam))
            return -ll
        r = minimize(nll, x0, method="L-BFGS-B")
        if best is None or r.fun < best.fun:
            best = r
    mu, a, b = np.exp(best.x)
    return float(mu), float(a), float(b), float(-best.fun)
