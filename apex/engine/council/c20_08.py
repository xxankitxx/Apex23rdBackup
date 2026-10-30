"""C20_08 — Two-mode forward-momentum gamma buyer (expiry-day mode + normal-day mode).

Idea in one line: trade the PARITY FORWARD (not spot): when the smoothed forward breaks out of its recent range with
velocity, buy the ATM/ITM option (|delta| >= 0.52) that gives the most expected premium % per rupee for the move
(delta*m + 0.5*gamma*m^2 + theta*hold) / ask; exit on a forward-point trailing stop measured from the best forward
since entry (underlying noise, not premium noise), a premium hard stop, and a theta clock (time stop) that is short on
expiry day (theta per minute is 10x a normal day) and long on normal days.

Inputs per second (all at rows <= i, nothing ahead): D.fwd (parity forward), D.hm, D.bid/D.ask/D.age, D.delta,
D.gamma, D.theta (per minute), D.K/D.rr, D.dte0. All are live in the engine at 1 Hz.

Modes (selected by D.dte0, i.e. the day IS the weekly's expiry):
  EXP  (0-DTE):  shorter breakout window, faster velocity test, short max hold, tight forward trail.
  NORM (>=1 DTE): longer window, wider trail, no theta clock until late.
"""
from collections import deque

import numpy as np

# Parameters chosen on a small grid (sweep2.py) and checked one notch either side (nb_exp.py, nb_norm.py).
EXP = dict(          # 0-DTE: breakout + velocity; ITM delta 0.65 (lowest theta per directional point); 15-min theta clock
    tau=5.0,         # s   causal EMA smoothing of the parity forward
    W=600,           # s   breakout window: smoothed forward must exceed max/min of the previous W seconds
    L=150,           # s   velocity lookback
    vmin=20.0,       # pts forward move over L seconds required
    trail=25.0,      # pts forward give-back from the best forward since entry -> exit
    sl=0.15,         # premium hard stop (fraction of entry ask)
    hold=900,        # s   max hold (theta clock: 0-DTE ATM theta is 0.35-1.8 pts/min)
    cool=60,         # s   wait after an exit before a new entry
    t0=556.0,        # 09:16 first entry (forward exists from 09:16)
    t1=14 * 60 + 40, # last new entry 14:40
    tp=9.9,          # premium take-profit (fraction); 9.9 = off
    dt=0.65,         # target |delta| of the bought option (>= 0.52 always enforced); 0 = expected-return score
    pb=0.0,          # 0 = breakout entry; >0 = pullback entry (retrace fraction of the impulse)
    rs=5.0,          # pts resumption from the pullback extreme (pullback entry only)
)
NORM = dict(         # >= 1 DTE: impulse of 40 pts in 20 min, wait for a 50 % pullback, enter on 5-pt resumption
    tau=5.0, W=1200, L=1200, vmin=40.0, pb=0.5, rs=5.0,
    trail=40.0,      # wide forward trail: normal-day theta is ~0.04-0.14 pts/min, time is cheap
    sl=0.15, hold=5400, cool=60, t0=556.0, t1=15 * 60, tp=9.9, dt=0.60,
)


class Strategy:
    def __init__(self, exp=None, norm=None, dmin=0.52):
        self.pe = dict(EXP, **(exp or {}))
        self.pn = dict(NORM, **(norm or {}))
        self.dmin = dmin
        self.day = None

    def _reset(self, D):
        self.day = D.day
        self.p = self.pe if D.dte0 else self.pn
        N = len(D.T)
        self.fs = np.full(N, np.nan)   # smoothed forward, filled causally as we go
        self.last_exit = -10 ** 9
        self.best = None
        self.side = None
        self.qmax, self.qmin = deque(), deque()   # monotonic queues: rolling max/min of fs over [i-W, i-1]
        self.arm = None       # pullback state: [side, impulse start level, extreme, pullback extreme, armed_at]

    def _pick(self, i, D, side, m, hold_min):
        """strike with the best expected % gain for a forward move m in `hold_min` minutes, |delta| >= dmin"""
        best, bk = -1e9, None
        k0 = D.atm(i)
        for k in (k0 - 150, k0 - 100, k0 - 50, k0, k0 + 50, k0 + 100, k0 + 150):
            j = D.col.get((int(k), side))
            if j is None or not np.isfinite(D.ask[i, j]) or D.age[i, j] > 5 or D.ask[i, j] <= 0:
                continue
            dl = abs(float(D.delta[i, j]))
            if not np.isfinite(dl) or dl < self.dmin:
                continue
            g, th = float(D.gamma[i, j]), float(D.theta[i, j])
            if not np.isfinite(g):
                g = 0.0
            if not np.isfinite(th):
                th = 0.0
            ev = (dl * m + 0.5 * g * m * m + th * hold_min) / float(D.ask[i, j])
            if self.p["dt"] > 0:
                ev = -abs(dl - self.p["dt"])
            if ev > best:
                best, bk = ev, k
        return bk

    def on_second(self, i, D, pos):
        if self.day != D.day:
            self._reset(D)
        p = self.p
        f = D.fwd[i]
        if not np.isfinite(f):
            return None
        a = 1.0 / p["tau"]
        prev = self.fs[i - 1] if i > 0 else np.nan
        self.fs[i] = f if not np.isfinite(prev) else prev + a * (f - prev)
        fs = self.fs[i]
        W = p["W"]
        if i > 0 and np.isfinite(prev):            # push row i-1 (the window excludes the current row)
            x = prev
            while self.qmax and self.qmax[-1][1] <= x:
                self.qmax.pop()
            self.qmax.append((i - 1, x))
            while self.qmin and self.qmin[-1][1] >= x:
                self.qmin.pop()
            self.qmin.append((i - 1, x))
        while self.qmax and self.qmax[0][0] < i - W:
            self.qmax.popleft()
        while self.qmin and self.qmin[0][0] < i - W:
            self.qmin.popleft()

        if pos is not None:
            j = pos["j"]
            if self.best is None:
                self.best = fs
            ce = pos["rr"] == "CE"
            self.best = max(self.best, fs) if ce else min(self.best, fs)
            give = (self.best - fs) if ce else (fs - self.best)
            bid = D.bid[i, j]
            held = D.T[i] - D.T[pos["i_in"]]
            if np.isfinite(bid) and bid <= pos["entry"] * (1 - p["sl"]):
                return self._exit(i, "SL")
            if np.isfinite(bid) and bid >= pos["entry"] * (1 + p["tp"]):
                return self._exit(i, "TP")
            if give >= p["trail"]:
                return self._exit(i, "FWD_TRAIL")
            if held >= p["hold"]:
                return self._exit(i, "TIME")
            return None

        if D.hm[i] < p["t0"] or D.hm[i] >= p["t1"] or i - self.last_exit < p["cool"]:
            return None
        L = p["L"]
        if i < W + 2 or not np.isfinite(self.fs[i - W]) or not self.qmax:
            return None
        hi, lo = self.qmax[0][1], self.qmin[0][1]
        v = fs - self.fs[i - L]
        side = None
        if fs > hi and v >= p["vmin"]:
            side = "CE"
        elif fs < lo and -v >= p["vmin"]:
            side = "PE"
        if p["pb"] > 0:
            side = self._pullback(i, fs, v, side, p)
        if side is None:
            return None
        k = self._pick(i, D, side, abs(v), p["hold"] / 60.0 * 0.5)
        if k is None:
            return None
        self.best = None
        return ("BUY", k, side, f"{'EXP' if D.dte0 else 'NORM'} {'pb' if p['pb'] > 0 else 'brk'} v={v:+.0f}")

    def _pullback(self, i, fs, v, side, p):
        """impulse (breakout + velocity) arms; enter after a retrace of pb*impulse and a resumption of rs pts"""
        a = self.arm
        if side is not None:                          # fresh breakout: (re)arm, record impulse
            if a is None or a[0] != side:
                self.arm = [side, self.fs[i - p["L"]], fs, fs, i]
            else:
                a[2] = max(a[2], fs) if side == "CE" else min(a[2], fs)
                a[3] = a[2]
            return None
        if a is None:
            return None
        if i - a[4] > p["W"]:
            self.arm = None
            return None
        sd, base, ext, pbx = a[0], a[1], a[2], a[3]
        up = sd == "CE"
        a[2] = max(ext, fs) if up else min(ext, fs)
        a[3] = min(pbx, fs) if up else max(pbx, fs)
        imp = abs(a[2] - base)
        ret = (a[2] - a[3]) if up else (a[3] - a[2])
        if imp <= 0 or ret < p["pb"] * imp:
            return None
        if ret > 0.9 * imp:                         # impulse fully undone: disarm
            self.arm = None
            return None
        res = (fs - a[3]) if up else (a[3] - fs)
        if res >= p["rs"]:
            self.arm = None
            return sd
        return None

    def _exit(self, i, why):
        self.last_exit = i
        self.best = None
        return ("SELL", why)
