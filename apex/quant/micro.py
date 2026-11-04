"""Streaming microstructure statistics (each O(1) per update, fixed memory):

* RollingVar      realised variance RV and jump-robust bipower variation BV of 1-s forward changes over a window;
                  JV = max(RV - BV, 0) is the jump part; the Huang-Tauchen ratio z tells a jump from noise.
* Cusum           two-sided CUSUM on a standardised series: S+ = max(0, S+ + x - k), S- likewise; alarm at h.
* KyleLambda      rolling regression of price change on signed traded volume (price impact per unit flow).
* KalmanVelocity  local-linear-trend Kalman filter: level and velocity (pts/s) of a noisy price, with variance.
"""
import math
from collections import deque

MU43 = 2 ** (2.0 / 3.0) * math.gamma(7.0 / 6.0) / math.gamma(0.5)     # E|Z|^(4/3)
HT_C = (math.pi / 2.0) ** 2 + math.pi - 5.0                          # Huang-Tauchen variance constant


class _RollSum:
    """Sum of the last n values pushed."""
    __slots__ = ("q", "s")

    def __init__(self, n):
        self.q = deque(maxlen=n)
        self.s = 0.0

    def push(self, v):
        if len(self.q) == self.q.maxlen:
            self.s -= self.q[0]
        self.q.append(v)
        self.s += v

    def __len__(self):
        return len(self.q)


class RollingVar:
    """Window of the last n PRICE CHANGES r_i (only real changes: a feed that repeats the last price adds nothing,
    since zeros destroy bipower variation, which multiplies neighbouring changes). `dt` is the time each change
    covers, so sigma() is per second whatever the update rate."""

    def __init__(self, n=300):
        self.n = n
        self.r = deque(maxlen=3)
        self._rv = _RollSum(n)                 # r_i^2
        self._bp = _RollSum(n)                 # |r_i||r_{i-1}|
        self._tq = _RollSum(n)                 # |r_i r_{i-1} r_{i-2}|^(4/3)
        self._dt = _RollSum(n)                 # seconds covered

    def add(self, x, dt=1.0):
        x = float(x)
        if not math.isfinite(x) or x == 0.0:
            return
        self.r.append(x)
        self._rv.push(x * x)
        self._dt.push(float(dt))
        if len(self.r) >= 2:
            self._bp.push(abs(x) * abs(self.r[-2]))
        if len(self.r) == 3:
            self._tq.push(abs(x * self.r[-2] * self.r[-3]) ** (4.0 / 3.0))

    @property
    def count(self):
        return len(self._rv)

    def rv(self):
        return max(self._rv.s, 0.0)

    def bv(self):
        """Bipower variation scaled to the window length."""
        m = len(self._bp)
        return (math.pi / 2.0) * max(self._bp.s, 0.0) * len(self._rv) / m if m else 0.0

    def sigma(self):
        """Jump-robust noise, pts per sqrt(second): sqrt(BV / seconds covered)."""
        t = self._dt.s
        return math.sqrt(self.bv() / t) if len(self._rv) >= 2 and t > 0 else float("nan")

    def jump(self):
        """(jump share of RV, Huang-Tauchen ratio z). z > 3: the window holds a jump."""
        n = len(self._rv)
        rv, bv = self.rv(), self.bv()
        if n < 30 or rv <= 0 or bv <= 0 or len(self._tq) == 0:
            return 0.0, 0.0
        rj = (rv - bv) / rv
        tq = n * MU43 ** -3 * max(self._tq.s, 0.0) * n / len(self._tq)
        z = rj / math.sqrt(HT_C / n * max(1.0, tq / (bv * bv)))
        return max(rj, 0.0), z


class Cusum:
    def __init__(self, k=0.5, h=5.0):
        self.k, self.h = k, h
        self.up = self.dn = 0.0

    def add(self, z):
        self.up = max(0.0, self.up + z - self.k)
        self.dn = max(0.0, self.dn - z - self.k)
        return self.state()

    def state(self):
        return 1 if self.up > self.h else (-1 if self.dn > self.h else 0)

    def reset(self):
        self.up = self.dn = 0.0


class KyleLambda:
    """Rolling OLS through the origin of dP on q (signed volume) over the last n updates."""

    def __init__(self, n=120):
        self.buf = deque(maxlen=n)
        self.sxy = self.sxx = 0.0

    def add(self, dp, q):
        if not (math.isfinite(dp) and math.isfinite(q)):
            return
        if len(self.buf) == self.buf.maxlen:
            a, b = self.buf[0]
            self.sxy -= a * b
            self.sxx -= b * b
        self.buf.append((dp, q))
        self.sxy += dp * q
        self.sxx += q * q

    def value(self):
        return self.sxy / self.sxx if self.sxx > 1e-12 else float("nan")


class KalmanVelocity:
    """Local linear trend: x_k = x_{k-1} + v dt + w_x, v_k = v_{k-1} + w_v; observed y = x + e.
    q_x, q_v: level and velocity diffusion per second; r: observation noise variance (pts^2).
    Plain-float 2x2 algebra (no numpy) so one update costs a few microseconds."""

    def __init__(self, q_v=1e-4, q_x=0.05, r=0.25):
        self.q_v, self.q_x, self.r = q_v, q_x, r
        self.x = None
        self.v = 0.0
        self.p00, self.p01, self.p11 = 1e3, 0.0, 1.0

    def add(self, y, dt=1.0):
        if not math.isfinite(y):
            return
        if self.x is None:
            self.x = float(y)
            return
        # predict
        x = self.x + self.v * dt
        p00 = self.p00 + 2 * dt * self.p01 + dt * dt * self.p11 + self.q_x * dt
        p01 = self.p01 + dt * self.p11
        p11 = self.p11 + self.q_v * dt
        # update
        S = p00 + self.r
        k0, k1 = p00 / S, p01 / S
        e = y - x
        self.x = x + k0 * e
        self.v = self.v + k1 * e
        self.p00 = (1 - k0) * p00
        self.p01 = (1 - k0) * p01
        self.p11 = p11 - k1 * p01

    def t_stat(self):
        return self.v / math.sqrt(max(self.p11, 1e-12))
