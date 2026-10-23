"""
Market history sampled from the shared table at 10 Hz.

Rings (per instrument row): ltp, ttq, standing buy/sell quantity AND order
counts over the last 60 s, whole-book buy/sell totals, plus the sample time.
Every derived number in the engine reads from here, so "15 seconds ago" means
the same thing everywhere (time-based, so replay at any speed is identical).
"""
import numpy as np

from .. import config

HZ = 10
WIN = 60 * HZ          # 60 s of 10 Hz samples
DEPTH_NS_EPOCH_MIN = 1e18   # ~Sep 2001 in epoch ns: anything smaller is not a timestamp


class Market:
    def __init__(self):
        n = config.MAX_ROWS
        self.n = n
        self.t = np.zeros(WIN)                       # seconds (virtual clock)
        self.ltp = np.full((n, WIN), np.nan)
        self.ttq = np.full((n, WIN), np.nan)
        self.sb = np.full((n, WIN), np.nan)          # standing buy qty (5-level total, else best)
        self.ss = np.full((n, WIN), np.nan)          # standing sell qty
        self.sbo = np.full((n, WIN), np.nan)         # standing buy orders (depth only)
        self.sso = np.full((n, WIN), np.nan)         # standing sell orders
        self.tbq = np.full((n, WIN), np.nan)         # whole-book total buy qty (every quote)
        self.tsq = np.full((n, WIN), np.nan)
        self.k = -1
        self.count = 0
        self.snap = None
        self.prev_snap = None
        self.now = 0.0
        self._ago = {}

    mid_rows = ()          # D-110: rows whose price series is the bid/ask MID (the Nifty future)

    def push(self, snap, now_s: float):
        if len(self.mid_rows):
            # D-110: the engine's futures price is the bid/ask mid. The last print bounces across a
            # 4-10-pt spread and manufactured 15-s "impulses" out of nothing on 19 Oct; the mid does
            # not. A one-sided or wide quote falls back to the last print. The raw print stays in
            # snap["ltp"] of the shared table for the record (the feed never sees this copy).
            snap = snap.copy()
            for i in self.mid_rows:
                b, a = float(snap["bid"][i]), float(snap["ask"][i])
                if b > 0 and a >= b and (a - b) <= config.FUT_MID_MAX_SPREAD:
                    snap["ltp"][i] = (a + b) / 2.0
        self.prev_snap = self.snap
        self.snap = snap
        self.now = now_s
        self.k = (self.k + 1) % WIN
        self.count += 1
        self._ago = {}                               # T02: ago(secs) is a pure function of (now, ring) until the next push
        k = self.k
        self.t[k] = now_s
        ltp = snap["ltp"].astype(float)
        ltp[ltp <= 0] = np.nan
        self.ltp[:, k] = ltp
        ttq = snap["ttq"].astype(float)
        ttq[ttq <= 0] = np.nan              # council m19: a 0 count is "no data", not a real level
        self.ttq[:, k] = ttq
        has_depth = np.isfinite(snap["bq"][:, 0]) & (snap["depth_ns"] > 0)
        bq = np.nansum(snap["bq"], axis=1)
        aq = np.nansum(snap["aq"], axis=1)
        bo = np.nansum(snap["bo"], axis=1)
        ao = np.nansum(snap["ao"], axis=1)
        self.sb[:, k] = np.where(has_depth, bq, snap["bqty"])
        self.ss[:, k] = np.where(has_depth, aq, snap["aqty"])
        self.sbo[:, k] = np.where(has_depth, bo, np.nan)
        self.sso[:, k] = np.where(has_depth, ao, np.nan)
        tb, ts = snap["tbq"].astype(float), snap["tsq"].astype(float)
        self.tbq[:, k] = np.where(tb > 0, tb, np.nan)
        self.tsq[:, k] = np.where(ts > 0, ts, np.nan)

    def depth_age(self, now_s: float):
        """Seconds since each row's last depth packet (NaN where the row has no depth),
        or None before the first sample. Read-only: has_depth and the rings are unchanged.
        Every feed (live, replay, sim) stamps depth_ns with epoch nanoseconds; a value below
        DEPTH_NS_EPOCH_MIN is a bare "has depth" flag with no usable time, so its age is NaN."""
        if self.snap is None:
            return None
        dn = self.snap["depth_ns"].astype(float)
        with np.errstate(invalid="ignore"):
            return np.where(dn >= DEPTH_NS_EPOCH_MIN, now_s - dn / 1e9, np.nan)

    def ago(self, secs: float) -> int:
        """Ring slot whose timestamp is closest to `secs` before now."""
        j = self._ago.get(secs)
        if j is not None:
            return j
        j = self._ago_calc(secs)
        self._ago[secs] = j
        return j

    def _ago_calc(self, secs: float) -> int:
        if self.count <= 1:
            return self.k
        n = min(self.count, WIN)
        target = self.now - secs
        idx = np.arange(n) if n < WIN else np.arange(WIN)
        j = idx[np.argmin(np.abs(self.t[idx] - target))]
        return int(j)

    def change(self, arr, secs):
        return arr[:, self.k] - arr[:, self.ago(secs)]

    def ratio(self, arr, secs):
        old = arr[:, self.ago(secs)]
        with np.errstate(divide="ignore", invalid="ignore"):
            return arr[:, self.k] / old

    def imb_t_ago(self, secs):
        j = self.ago(secs)
        a, b = self.tbq[:, j], self.tsq[:, j]
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where((a + b) > 0, (a - b) / (a + b), np.nan)
