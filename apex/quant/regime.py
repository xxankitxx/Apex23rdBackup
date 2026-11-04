"""Gaussian hidden Markov model for the market state, with a semi-Markov duration layer.

The state is never observed; prices, volatility and flow are. A K-state HMM with diagonal-Gaussian emissions on a
feature vector (default: 1-min forward return, log 1-min realised range) is fitted OFFLINE by Baum-Welch (scaled
forward-backward, several seeded restarts, best log-likelihood kept). LIVE, the forward filter gives the posterior
P(state_t | x_1..x_t) in O(K^2) per bar; no look-ahead.

Semi-Markov layer (the reviews' HSMM point: a 30-s expansion and an 8-min one should not be treated alike): the
Viterbi path of the training data gives each state's empirical run-length distribution; `remaining(s, r)` is the
expected further duration of state s given that it has already lasted r bars, E[D - r | D > r].
"""
import math

import numpy as np


class GaussianHMM:
    def __init__(self, K=4, seed=0):
        self.K = K
        self.seed = seed
        self.pi = self.A = self.mu = self.var = None
        self.durations = {}                    # state -> sorted run lengths (bars)
        self._alpha = None                     # live filter state

    # ---------------------------------------------------------------- emissions
    def _logb(self, X):
        X = np.atleast_2d(X)
        d = X[:, None, :] - self.mu[None, :, :]
        return -0.5 * np.sum(np.log(2 * np.pi * self.var)[None, :, :] + d * d / self.var[None, :, :], axis=2)

    # ---------------------------------------------------------------- fitting
    def _init(self, X, rng):
        K, D = self.K, X.shape[1]
        q = np.quantile(X[:, 0], np.linspace(0.1, 0.9, K))
        self.mu = np.column_stack([q] + [np.full(K, np.mean(X[:, j])) for j in range(1, D)])
        self.mu += rng.normal(0, 0.1, self.mu.shape) * X.std(axis=0)
        self.var = np.tile(X.var(axis=0) + 1e-9, (K, 1))
        self.A = np.full((K, K), 0.1 / max(K - 1, 1))
        np.fill_diagonal(self.A, 0.9)
        self.pi = np.full(K, 1.0 / K)

    def _fb(self, X):
        T, K = len(X), self.K
        B = np.exp(np.clip(self._logb(X), -700, 700))
        a = np.zeros((T, K))
        c = np.zeros(T)
        a[0] = self.pi * B[0]
        c[0] = a[0].sum() or 1e-300
        a[0] /= c[0]
        for t in range(1, T):
            a[t] = (a[t - 1] @ self.A) * B[t]
            c[t] = a[t].sum() or 1e-300
            a[t] /= c[t]
        b = np.ones((T, K))
        for t in range(T - 2, -1, -1):
            b[t] = (self.A @ (B[t + 1] * b[t + 1])) / c[t + 1]
        return a, b, c, B

    def fit(self, seqs, iters=60, restarts=5, tol=1e-5):
        """seqs: list of (T_i, D) arrays (one per day; days are separate sequences)."""
        seqs = [np.asarray(s, float) for s in seqs if len(s) > 2]
        Xall = np.vstack(seqs)
        best = None
        for r in range(restarts):
            rng = np.random.default_rng(self.seed + r)
            self._init(Xall, rng)
            prev = -np.inf
            for _ in range(iters):
                ll, g0, xi, gam_sum, num, num2 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                for X in seqs:
                    a, b, c, B = self._fb(X)
                    ll += np.log(c).sum()
                    g = a * b
                    g /= g.sum(axis=1, keepdims=True)
                    g0 = g0 + g[0]
                    x = (a[:-1, :, None] * self.A[None] * (B[1:] * b[1:])[:, None, :]) / c[1:, None, None]
                    xi = xi + x.sum(axis=0)
                    gam_sum = gam_sum + g.sum(axis=0)
                    num = num + g.T @ X
                    num2 = num2 + g.T @ (X * X)
                self.pi = g0 / g0.sum()
                self.A = xi / xi.sum(axis=1, keepdims=True)
                self.mu = num / gam_sum[:, None]
                self.var = np.maximum(num2 / gam_sum[:, None] - self.mu ** 2, 1e-6 * Xall.var(axis=0) + 1e-12)
                if ll - prev < tol * abs(ll):
                    break
                prev = ll
            if best is None or ll > best[0]:
                best = (ll, self.pi.copy(), self.A.copy(), self.mu.copy(), self.var.copy())
        self.ll, self.pi, self.A, self.mu, self.var = best
        order = np.argsort(self.mu[:, 0])            # state 0 = most negative mean return ... K-1 = most positive
        self._reorder(order)
        self.durations = {k: [] for k in range(self.K)}
        for X in seqs:
            path = self.viterbi(X)
            run = 1
            for t in range(1, len(path) + 1):
                if t < len(path) and path[t] == path[t - 1]:
                    run += 1
                else:
                    self.durations[int(path[t - 1])].append(run)
                    run = 1
        self.durations = {k: np.sort(np.array(v, float)) for k, v in self.durations.items()}
        return self

    def _reorder(self, o):
        self.pi, self.mu, self.var = self.pi[o], self.mu[o], self.var[o]
        self.A = self.A[np.ix_(o, o)]

    def viterbi(self, X):
        X = np.asarray(X, float)
        lb = self._logb(X)
        lA = np.log(self.A + 1e-300)
        d = np.log(self.pi + 1e-300) + lb[0]
        bp = np.zeros((len(X), self.K), int)
        for t in range(1, len(X)):
            m = d[:, None] + lA
            bp[t] = m.argmax(axis=0)
            d = m.max(axis=0) + lb[t]
        path = np.zeros(len(X), int)
        path[-1] = int(d.argmax())
        for t in range(len(X) - 1, 0, -1):
            path[t - 1] = bp[t, path[t]]
        return path

    # ---------------------------------------------------------------- live
    def reset(self):
        self._alpha = None

    def filter(self, x):
        """One bar; returns the posterior over states given everything up to and including x."""
        lb = self._logb(np.asarray(x, float)[None, :])[0]
        b = np.exp(lb - lb.max())
        a = (self.pi if self._alpha is None else self._alpha @ self.A) * b
        s = a.sum()
        self._alpha = a / s if s > 0 else np.full(self.K, 1.0 / self.K)
        return self._alpha

    def remaining(self, state, ran):
        """Expected further bars of `state` given it has lasted `ran` bars (empirical, semi-Markov)."""
        d = self.durations.get(int(state))
        if d is None or len(d) == 0:
            return float("nan")
        tail = d[d > ran]
        return float(tail.mean() - ran) if len(tail) else 0.0

    # ---------------------------------------------------------------- persistence
    def to_dict(self):
        return {"K": self.K, "pi": self.pi.tolist(), "A": self.A.tolist(), "mu": self.mu.tolist(),
                "var": self.var.tolist(), "durations": {str(k): v.tolist() for k, v in self.durations.items()}}

    @classmethod
    def from_dict(cls, d):
        m = cls(K=int(d["K"]))
        m.pi, m.A, m.mu, m.var = (np.array(d[k], float) for k in ("pi", "A", "mu", "var"))
        m.durations = {int(k): np.array(v, float) for k, v in d["durations"].items()}
        return m


def bar_features(fwd, step=60):
    """(return over the bar, log of the bar's high-low range + 1) for consecutive `step`-second bars of a 1-Hz
    forward series; NaN or frozen bars skipped. Returns an (N, 2) array."""
    f = np.asarray(fwd, float)
    out = []
    for s in range(0, len(f) - step, step):
        seg = f[s:s + step + 1]
        seg = seg[np.isfinite(seg)]
        if len(seg) < step // 2 or seg.max() == seg.min():       # no data, or a frozen feed: not a market state
            continue
        out.append((seg[-1] - seg[0], math.log1p(seg.max() - seg.min())))
    return np.array(out, float).reshape(-1, 2)
