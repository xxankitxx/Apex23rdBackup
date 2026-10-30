"""Writer squeeze / writer flood (owner's OI_ACCELERATION_VWAP_SPEC.md, 29 Oct 2026).

Per strike and side (ATM +- 2, CE and PE), the spec's state machine, computed causally from the live chain rows
(sampled every second by this card itself; no History copies, so it stays cheap):

  VWAP (spec 3.3): the option's own session VWAP = sum(ltp x d(ttq)) / sum(d(ttq)) since the board first saw the
      contract (09:15 for the ATM +- 10 band).  Only ttq increases count.
  OI (spec 3.1): only a REAL OI print counts (the value changed); rolling 3-min intervals ending now, re-evaluated
      every 5 s.  v%_k = 100 (OI(t) - OI(t-180)) / OI(t-180), v%_{k-1} likewise 180 s earlier, AR = v_k / v_{k-1}.
  OI ACCEL (spec stages 1+2): same sign, AR >= 1.5, z(v%_{k-1}) beyond 1 and z(a) beyond 1.5, |v%_k| >= 0.5 %.
      z is against TODAY's pool of prints so far (same side, ATM +- 2; >= 30 prints; median/MAD z) because the spec's 20-session
      time-of-day baselines do not exist yet (as in R5-01).  Falling OI -> squeeze candidate, rising -> flood
      candidate.  The window W = 6 min opens.
  SQUEEZE / FLOOD (stage 3): price above its VWAP for every second of the last 20 s and 120-s slope > 0 (squeeze),
      below and < 0 (flood), within W.  If the price was already across VWAP before the acceleration, the order is
      REVERSED (tier B, "price-first").  A+ = acceleration first + consecutive + dual-side; otherwise A.
  MONITOR: shown until the price is back across VWAP by 0.5 % or 15 min pass (owner's 10-15 min rule); the OI move
      slowing (AR < 1) shows as "exhausting" (spec 5.7).  Tiers are labels only, never a score."""
from collections import deque
from datetime import timedelta
import math

import numpy as np

NAME = "writer_squeeze"
TITLE = "Writer squeeze / flood"
IDEA = ("OI change accelerating on a strike (writers rushing out or in), then the option crosses its own day VWAP: "
        "squeeze = buy that side, flood = buy the other side")
VERDICT = ("Rejected as a trigger 29 Oct: -Rs 1.04 L on 7 days, 0/7 green; 25/32 fired price-first (OI lags price); "
           "as veto/exit also red. Shown for watching")
EVERY_S = 1          # samples the chain every second (VWAP, acceptance); the machine runs every 5 s

IV = 180            # interval (spec: oi_interval_min = 3)
W = 360             # confirm window (2 intervals)
AR_M = 1.5
VMIN = 0.5          # |v%_k| floor, % of OI per 3 min
Z_TREND = 1.0       # spec stage 1: z(v%_{k-1}) beyond 1
Z_ACC = 1.5         # spec stage 2: z(a) beyond 1.5
ZMIN_N = 30         # prints in today's pool before z is trusted
VTREND = 0.25       # |v%_{k-1}| floor (stage 1: OI already moving that way)
ACC_S = 20          # VWAP acceptance seconds
SLOPE_S = 120
BUF = 0.005         # back across VWAP by 0.5 % ends the trigger
HOLD = 900          # a trigger is shown at most 15 min
NBAND = 2           # strikes each side of ATM run the machine
EVAL_S = 5


def _ok(x):
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x) and x > 0


class _C:
    __slots__ = ("q_last", "pv", "vol", "vwap", "ltp", "px", "ois", "oi_last", "sgn", "t_cross", "stage", "dir",
                 "t_acc", "v_acc", "v_prev", "ar", "consec", "rev", "t_trig", "exh")

    def __init__(self):
        self.q_last = None
        self.pv = 0.0
        self.vol = 0.0
        self.vwap = None
        self.ltp = None
        self.px = deque()       # (t, ltp) last ~SLOPE_S s
        self.ois = deque()      # (t, oi) REAL prints only, last ~3 intervals
        self.oi_last = None
        self.sgn = 0
        self.t_cross = None     # last time the price changed side of VWAP
        self.stage = "IDLE"
        self.dir = 0            # -1 OI falling (squeeze), +1 OI rising (flood)
        self.t_acc = None
        self.v_acc = 0.0
        self.v_prev = 0.0
        self.ar = 0.0
        self.consec = False
        self.rev = False
        self.t_trig = None
        self.exh = False

    def oi_at(self, t):
        """last real OI print at or before t (None if none)"""
        v = None
        for tt, o in self.ois:
            if tt > t:
                break
            v = o
        return v

    def px_at(self, t):
        v = None
        for tt, p in self.px:
            if tt > t:
                break
            v = p
        return v


class Idea:
    def __init__(self):
        self.c = {}
        self.shown = None
        self.last_eval = -1e9
        self.out = None
        self.pending = set()
        self.samp = {"CE": ([], []), "PE": ([], [])}     # today's (v%_{k-1}, a) per side, ATM +- 2 prints
        self.st = {}

    # ── every second: VWAP, price ring, OI prints ───────────────────────
    def _sample(self, now, row, c):
        ltp, q, oi = row.get("ltp"), row.get("ttq"), row.get("oi")
        if _ok(q):
            if c.q_last is not None and q > c.q_last and _ok(ltp):
                dq = q - c.q_last
                c.pv += ltp * dq
                c.vol += dq
            if c.q_last is None or q > c.q_last:
                c.q_last = q
        if c.vol > 0:
            c.vwap = c.pv / c.vol
        if _ok(ltp):
            c.ltp = ltp
            c.px.append((now, ltp))
            while c.px and c.px[0][0] < now - SLOPE_S - 5:
                c.px.popleft()
            if c.vwap:
                s = 1 if ltp > c.vwap else (-1 if ltp < c.vwap else 0)
                if s and s != c.sgn:
                    c.sgn, c.t_cross = s, now
        if _ok(oi) and oi != c.oi_last:          # a repeated OI value is not new information
            c.oi_last = oi
            c.ois.append((now, oi))
            while len(c.ois) > 2 and c.ois[1][0] < now - 3 * IV - 30:
                c.ois.popleft()

    def _accepted(self, c, now, want):
        if not c.vwap or not c.px or c.px[0][0] > now - SLOPE_S + 5:
            return False
        n = 0
        for tt, p in reversed(c.px):
            if tt < now - ACC_S:
                break
            n += 1
            if (p - c.vwap) * want <= 0:
                return False
        if n < ACC_S // 2:
            return False
        old = c.px_at(now - SLOPE_S)
        return old is not None and (c.ltp - old) * want > 0

    # ── every 5 s: the spec's machine for one contract ──────────────────
    def _stats(self):
        """robust centre/scale (median, 1.4826 MAD) of today's v%_{k-1} and a per side, from prints BEFORE this
        evaluation (causal).  Robust because OI % moves are fat-tailed: a few chain-wide re-marks (+40 %/3m) would
        blow up a plain std and silence the card."""
        self.st = {}
        for rr, (V, A) in self.samp.items():
            if len(V) < ZMIN_N:
                self.st[rr] = None
                continue
            v, a = np.asarray(V), np.asarray(A)
            mv, ma = float(np.median(v)), float(np.median(a))
            sv, sa = 1.4826 * float(np.median(np.abs(v - mv))), 1.4826 * float(np.median(np.abs(a - ma)))
            self.st[rr] = (mv, max(sv, 0.05), ma, max(sa, 0.05))

    def _z(self, rr, v1, a):
        """z of v%_{k-1} and of the acceleration a against today's pool so far (same side, ATM +- 2 prints) --
        the spec's 20-session baselines do not exist yet (R5-01 did the same, with a plain std)"""
        st = self.st.get(rr)
        if st is None:
            return None, None
        mv, sv, ma, sa = st
        return (v1 - mv) / sv, (a - ma) / sa

    def _step(self, rr, c, now, new_print):
        if new_print and c.oi_last:
            o1, o2, o3 = c.oi_at(now - IV), c.oi_at(now - 2 * IV), c.oi_at(now - 3 * IV)
            if o1 and o2:
                oi0 = c.oi_last
                v0, v1 = 100 * (oi0 - o1) / o1, 100 * (o1 - o2) / o2
                ar = v0 / v1 if (v1 != 0 and v0 * v1 > 0) else None
                a = v0 - v1
                zv1, za = self._z(rr, v1, a)
                V, A = self.samp[rr]
                V.append(v1)
                A.append(a)
                sg = 1 if v0 > 0 else -1
                zok = zv1 is not None and zv1 * sg >= Z_TREND and za * sg >= Z_ACC
                if c.stage == "IDLE":
                    if zok and ar is not None and ar >= AR_M and abs(v0) >= VMIN and abs(v1) >= VTREND:
                        c.stage, c.dir, c.t_acc = "ACCEL", (1 if v0 > 0 else -1), now
                        c.v_acc, c.v_prev, c.ar = v0, v1, ar
                        v2 = 100 * (o2 - o3) / o3 if o3 else None
                        c.consec = bool(v2 is not None and v1 * v2 > 0 and abs(v1) >= abs(v2))
                        want = 1 if c.dir < 0 else -1          # squeeze wants above VWAP, flood below
                        c.rev = bool(c.sgn == want and c.t_cross is not None and c.t_cross < now)
                        c.exh = False
                elif c.stage == "ACCEL":
                    if v0 * c.dir < 0 and abs(v0) >= VTREND:   # OI reversed -> invalidated
                        c.stage = "IDLE"
                    elif v0 * c.dir > 0 and abs(v0) > abs(c.v_acc):
                        c.v_acc = v0
                elif c.stage == "TRIG":
                    c.exh = bool(v0 * c.dir <= 0 or (ar is not None and ar < 1))
        if c.stage == "ACCEL":
            if now - c.t_acc > W:
                c.stage = "IDLE"
            elif self._accepted(c, now, 1 if c.dir < 0 else -1):
                c.stage, c.t_trig = "TRIG", now
                return True
        elif c.stage == "TRIG":
            want = 1 if c.dir < 0 else -1
            back = c.ltp and c.vwap and ((want > 0 and c.ltp < c.vwap * (1 - BUF)) or
                                         (want < 0 and c.ltp > c.vwap * (1 + BUF)))
            if back or now - c.t_trig > HOLD:
                c.stage = "IDLE"
        return False

    def update(self, env):
        now, atm, step = env.t, env.atm, env.step or 50
        for key, row in (env.chain or {}).items():
            c = self.c.get(key)
            if c is None:
                c = self.c[key] = _C()
            last0 = c.oi_last
            self._sample(now, row, c)
            if c.oi_last != last0:
                self.pending.add(key)
        if self.out is not None and now - self.last_eval < EVAL_S:
            return dict(self.out, alert=False)
        self.last_eval = now
        prints, self.pending = self.pending, set()
        self.out = self._eval(env, now, atm, step, prints)
        return self.out

    def _eval(self, env, now, atm, step, prints):
        if env.hm < 555 + 7 or atm is None:
            return {"state": "WARMING", "text": "needs ~7 min of OI prints (two 3-min intervals)"}
        if prints:
            self._stats()
        fresh, live = [], set()
        for dk in range(-NBAND, NBAND + 1):
            for rr in ("CE", "PE"):
                key = (int(atm + dk * step), rr)
                c = self.c.get(key)
                if c is None:
                    continue
                live.add(key)
                if self._step(rr, c, now, key in prints):
                    fresh.append(key)
        for key, c in self.c.items():          # out of the ATM band: stop that machine
            if key not in live and c.stage != "IDLE":
                c.stage = "IDLE"
        trig = [(c.t_trig, key) for key, c in self.c.items() if c.stage == "TRIG"]
        acc = [(c.t_acc, key) for key, c in self.c.items() if c.stage == "ACCEL"]

        def kind(key):
            return ("SQUEEZE " if self.c[key].dir < 0 else "FLOOD ") + key[1]

        def favour(key):
            rr = key[1]
            return rr if self.c[key].dir < 0 else ("PE" if rr == "CE" else "CE")

        if trig:
            keys = [k for _, k in trig]
            key = self.shown if self.shown in keys else max(trig)[1]   # stick with the shown one: no flicker
            self.shown = key
            c = self.c[key]
            side = favour(key)
            dual = any(favour(k) == side and k[1] != key[1] for k in keys)
            tier = "B" if c.rev else ("A+" if (dual and c.consec) else "A")
            others = sum(1 for k in keys if k != key and favour(k) == side)
            age = (now - c.t_trig) / 60
            txt = (f"{key[1]} {key[0]} OI {c.v_prev:+.1f}%->{c.v_acc:+.1f}%/3m (AR {c.ar:.1f}); "
                   f"{c.ltp or 0:.1f} vs VWAP {c.vwap or 0:.1f}, {age:.0f} min; tier {tier}"
                   f"{' price-first' if c.rev else ''}{' dual' if dual else ''}"
                   f"{f' +{others} strikes' if others else ''}{'; exhausting' if c.exh else ''}")
            lim = (c.vwap or 0) * ((1 - BUF) if c.dir < 0 else (1 + BUF))
            plan = f"{side} near ATM {atm}; over if {key[1]} {key[0]} {'<' if c.dir < 0 else '>'} {lim:.1f}"
            return {"state": kind(key), "side": side, "value": c.v_acc, "unit": "%OI/3m", "text": txt,
                    "plan": plan, "alert": key in fresh}
        self.shown = None
        if acc:
            _, key = max(acc)
            c = self.c[key]
            by = (env.dt + timedelta(seconds=max(0.0, W - (now - c.t_acc)))).strftime("%H:%M")
            n = len(acc)
            txt = (f"{key[1]} {key[0]} OI {'falling' if c.dir < 0 else 'rising'} faster: {c.v_prev:+.1f}%->"
                   f"{c.v_acc:+.1f}%/3m (AR {c.ar:.1f}); {c.ltp or 0:.1f} vs VWAP {c.vwap or 0:.1f}"
                   f"{f'; {n} contracts at once (chain-wide print?)' if n >= 4 else ''}")
            plan = (f"{kind(key)} if {key[1]} {key[0]} holds {'above' if c.dir < 0 else 'below'} "
                    f"{c.vwap or 0:.1f} by {by}")
            return {"state": f"OI ACCEL {key[1]}", "side": None, "value": c.v_acc, "unit": "%OI/3m",
                    "text": txt, "plan": plan}
        early = " (first 15 min: OI includes overnight adjustments)" if env.hm < 555 + 15 else ""
        nmin = min(len(self.samp["CE"][0]), len(self.samp["PE"][0]))
        if nmin < ZMIN_N:
            early = f"; building today's OI baseline ({nmin}/{ZMIN_N} prints)"
        return {"state": "QUIET", "side": None, "value": None, "unit": "%OI/3m",
                "text": f"no strike ATM+-{NBAND} with OI accelerating (AR>={AR_M}, z(a)>={Z_ACC}){early}"}
