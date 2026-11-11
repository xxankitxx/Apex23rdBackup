"""Small models that can be shown wrong (docs/40 section 6 stage A and B). Numpy only. A model is a plain dict so it
can be saved as JSON, hashed, and loaded by the engine with no fitting at run time.

  fit_logit   regularised logistic regression on standardised, clipped features (missing = the training median)
  predict     probability from a saved model
  Calibrator  binned reliability map with shrinkage to the identity; can be updated from matured labels only
  scores      Brier, log loss, AUC, reliability table, pinball loss"""
import bisect
import hashlib
import json

import numpy as np

CLIP = 4.0


def standardise(X):
    med = np.nanmedian(X, 0)
    sd = np.nanstd(X, 0)
    sd = np.where(np.isfinite(sd) & (sd > 0), sd, 1.0)
    return np.where(np.isfinite(med), med, 0.0), sd


def _z(X, med, sd):
    return np.clip(np.nan_to_num((np.asarray(X, float) - med) / sd, nan=0.0, posinf=CLIP, neginf=-CLIP), -CLIP, CLIP)


def fit_logit(X, y, names, l2=10.0, iters=40, meta=None):
    """Newton steps on the penalised log-likelihood. y in {0, 1}. Returns the model dict."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    med, sd = standardise(X)
    A = np.c_[np.ones(len(X)), _z(X, med, sd)]
    w = np.zeros(A.shape[1])
    w[0] = np.log(max(y.mean(), 1e-6) / max(1 - y.mean(), 1e-6))
    pen = l2 * np.r_[0.0, np.ones(A.shape[1] - 1)]

    def loss(v):
        u = np.clip(A @ v, -30.0, 30.0)
        return float((np.log1p(np.exp(u)) - y * u).sum() + 0.5 * (pen * v * v).sum())
    cur = loss(w)
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(A @ w, -30.0, 30.0)))
        g = A.T @ (p - y) + pen * w
        H = (A * (p * (1 - p))[:, None]).T @ A + np.diag(pen + 1e-6)
        step = np.linalg.solve(H, g)
        k = 1.0
        while k > 1e-4 and loss(w - k * step) > cur:      # damped: a full Newton step may overshoot (10 Nov, A30 fold)
            k *= 0.5
        w = w - k * step
        new = loss(w)
        if cur - new < 1e-9 * max(1.0, abs(cur)):
            cur = new
            break
        cur = new
    m = dict(kind="logit", names=list(names), med=med.tolist(), sd=sd.tolist(), w=w.tolist(), l2=l2,
             n=int(len(y)), base=float(y.mean()), meta=meta or {})
    m["hash"] = model_hash(m)
    return m


def model_hash(m):
    body = {k: v for k, v in m.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:12]


def predict(m, X):
    X = np.atleast_2d(np.asarray(X, float))
    A = np.c_[np.ones(len(X)), _z(X, np.array(m["med"]), np.array(m["sd"]))]
    return 1.0 / (1.0 + np.exp(-np.clip(A @ np.array(m["w"]), -30.0, 30.0)))


class Calibrator:
    """Reliability map on fixed probability bins. Each bin's output is the observed rate shrunk towards the raw
    forecast by `prior` pseudo-observations, so an empty bin returns the forecast unchanged. update() accepts only
    outcomes that have matured: the caller hands over (forecast, outcome) pairs, never an open position."""

    def __init__(self, edges=None, prior=50.0):
        self.edges = list(edges) if edges is not None else [i / 20.0 for i in range(21)]
        self.prior = float(prior)
        self.n = [0.0] * (len(self.edges) - 1)
        self.s = [0.0] * (len(self.edges) - 1)        # sum of outcomes
        self.p = [0.0] * (len(self.edges) - 1)        # sum of raw forecasts
        self.updates = 0

    def _bin(self, p):
        return min(len(self.n) - 1, max(0, bisect.bisect_right(self.edges, p) - 1))

    def update(self, p, y):
        for a, b in zip(np.atleast_1d(p), np.atleast_1d(y)):
            k = self._bin(float(a))
            self.n[k] += 1.0
            self.s[k] += float(b)
            self.p[k] += float(a)
        self.updates += 1

    def one(self, p):
        """The calibrated value of one forecast (no array work: this runs every second)."""
        k = self._bin(float(p))
        return (self.s[k] + self.prior * float(p)) / (self.n[k] + self.prior)

    def __call__(self, p):
        out = []
        for a in np.atleast_1d(p):
            k = self._bin(float(a))
            out.append((self.s[k] + self.prior * float(a)) / (self.n[k] + self.prior))
        return np.array(out)

    def to_json(self):
        return dict(edges=self.edges, prior=self.prior, n=self.n, s=self.s, p=self.p, updates=self.updates)

    @classmethod
    def from_json(cls, j):
        c = cls(j["edges"], j["prior"])
        c.n, c.s, c.p, c.updates = list(j["n"]), list(j["s"]), list(j["p"]), int(j.get("updates", 0))
        return c


# -- scores ---------------------------------------------------------------------------------------------------------
def brier(p, y):
    p, y = np.asarray(p, float), np.asarray(y, float)
    return float(((p - y) ** 2).mean()) if len(p) else float("nan")


def logloss(p, y):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()) if len(p) else float("nan")


def auc(s, y):
    """Rank AUC with ties averaged."""
    s, y = np.asarray(s, float), np.asarray(y).astype(bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    r = np.empty(len(s))
    r[order] = np.arange(1, len(s) + 1)
    ss = s[order]
    i = 0
    while i < len(ss):                               # average the ranks of equal scores
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = 0.5 * (i + j) + 1
        i = j + 1
    return float((r[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def reliability(p, y, bins=10):
    """Rows of (bin low, bin high, count, mean forecast, observed rate) on equal-count bins."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    if not len(p):
        return []
    q = np.quantile(p, np.linspace(0, 1, bins + 1))
    rows = []
    for a, b in zip(q[:-1], q[1:]):
        m = (p >= a) & (p <= b) if b == q[-1] else (p >= a) & (p < b)
        if m.sum():
            rows.append((round(float(a), 4), round(float(b), 4), int(m.sum()), round(float(p[m].mean()), 4),
                         round(float(y[m].mean()), 4)))
    return rows


def pinball(q_pred, y, q):
    d = np.asarray(y, float) - np.asarray(q_pred, float)
    return float(np.maximum(q * d, (q - 1) * d).mean()) if len(d) else float("nan")
