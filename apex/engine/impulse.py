"""D-134 (council 7, member C06): the 45-minute impulse window of Nifty spot for the pullback book.

One sample per second of TRUSTED in-session spot (the D-132 guard already filtered it). Keeps the rolling max and min
with their timestamps in O(1) per second (monotonic deques) and, for the current impulse, the deepest pullback since its
extreme. The window starts at the session's first sample (so at 09:25 it spans 10 minutes, as in the council's harness)
and is only valid when at least 80 % of its seconds are present.

view() -> {"ok", "hi", "lo", "t_hi", "t_lo", "d", "ext_t", "pbx", "rng", "n", "span"}
  d = +1 when the high came after the low (an up impulse), -1 when the low came last, 0 on a tie.
  pbx = the deepest price since the impulse extreme (lowest for an up impulse, highest for a down one).
"""
from collections import deque


class ImpulseWindow:
    def __init__(self, window_s):
        self.W = float(window_s)
        self.samples = deque()          # (t, px)
        self.mx = deque()               # (t, px), px non-increasing from the front: front = earliest maximum
        self.mn = deque()               # (t, px), px non-decreasing: front = earliest minimum
        self.t_first = None
        self._key = None
        self._pbx = None

    def add(self, t, px):
        t, px = float(t), float(px)
        if self.t_first is None:
            self.t_first = t
        self.samples.append((t, px))
        while self.mx and self.mx[-1][1] < px:
            self.mx.pop()
        self.mx.append((t, px))
        while self.mn and self.mn[-1][1] > px:
            self.mn.pop()
        self.mn.append((t, px))
        lim = t - self.W
        for dq in (self.samples, self.mx, self.mn):
            while dq and dq[0][0] < lim:
                dq.popleft()
        self._update_pbx(px)

    def _impulse(self):
        if not self.mx or not self.mn:
            return 0, None
        (th, _), (tl, _) = self.mx[0], self.mn[0]
        if th > tl:
            return 1, th
        if tl > th:
            return -1, tl
        return 0, None

    def _update_pbx(self, px):
        d, ext_t = self._impulse()
        key = (d, ext_t)
        if key != self._key:            # a new impulse (new extreme, or the old one aged out): rescan from its extreme
            self._key = key
            if d == 0:
                self._pbx = None
                return
            xs = [p for t, p in self.samples if t >= ext_t]
            self._pbx = (min(xs) if d > 0 else max(xs)) if xs else None
        elif d and self._pbx is not None:
            self._pbx = min(self._pbx, px) if d > 0 else max(self._pbx, px)

    def view(self, now_s=None):
        if not self.samples:
            return {"ok": False}
        t_last = self.samples[-1][0]
        span = min(self.W, t_last - self.t_first) + 1.0
        n = len(self.samples)
        d, ext_t = self._impulse()
        hi, lo = self.mx[0][1], self.mn[0][1]
        return {"ok": n >= 0.8 * span, "hi": hi, "lo": lo, "t_hi": self.mx[0][0], "t_lo": self.mn[0][0], "d": d,
                "ext_t": ext_t, "pbx": self._pbx, "rng": hi - lo, "n": n, "span": span}

    # warm state
    def dump(self):
        return {"W": self.W, "t_first": self.t_first, "samples": list(self.samples)}

    @classmethod
    def load(cls, st, window_s):
        w = cls(window_s)
        for t, px in st.get("samples") or []:
            w.add(t, px)
        if st.get("t_first") is not None:
            w.t_first = st["t_first"]
        return w
