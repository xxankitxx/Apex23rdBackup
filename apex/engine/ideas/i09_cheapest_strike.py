"""Cheapest strike (owner, 28 Oct: "which strike, what price"; CHEAPNESS_AND_REGIME_SPEC A7 lag cheapness).

For each side, the eligible strikes (ATM to 2 ITM, |delta| >= 0.52) are priced against what the forward's move over the
last 60 s already justifies:  V = mid0 + d0*dF + 1/2*g0*dF^2 + theta0*dt/min  (all taken 60 s ago, dF from "FUT"),
cheap% = 100 * (V - ask) / ask -- the same formula as paper.lag_cheapness. The card shows the cheapest buy per side.
On normal (6 DTE) days the strikes sit within about a spread of each other (R4-01), so the number matters mostly on
expiry day."""
import collections
import math

from ... import config

NAME = "cheapest_strike"
TITLE = "Cheapest strike (lag cheapness)"
IDEA = "Which strike, what price: the eligible strike whose ask lags most behind the forward's last-60-s move."
VERDICT = ("R4-01: no pattern as a veto; as an expiry-day strike chooser +Rs10k on 2 days (shadow t28_cheapK); "
           "on normal days strikes are within a spread.")
EVERY_S = 5

ANCHOR_S = 60
MIN_DELTA = 0.52
EMA_A = 0.2           # per-side smoothing of the best cheap% (5-s samples -> ~25 s memory)
CHEAP_MIN = 1.0       # % : a side turns CHEAP when its smoothed best reaches max(this, NOISE_X x the day's noise) ...
NOISE_X = 2.0         # noise = median |best cheap%| over the last NOISE_S (expiry days swing ~4x more, R4-01)
NOISE_S = 1800
OFF_FRAC = 0.4        # ... and stays CHEAP until it falls below OFF_FRAC x that bar
SWITCH_PP = 0.4       # a new strike replaces the held one only when it is this many pp cheaper
HOLD_S = 60           # a state must be wanted for this long before it is shown
ALERT_X = 2.0         # alert when a side becomes CHEAP at ALERT_X x the bar or more ...
ALERT_GAP_S = 1200    # ... at most once per 20 min
KEEP_S = 90           # own sample history kept per contract


def _ok(x):
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x)


def _at(dq, t):
    """the newest sample at or before t, or None (dq oldest -> newest)"""
    for x in reversed(dq):
        if x[0] <= t:
            return x
    return None


class Idea:
    def __init__(self):
        self.shown = "WARMING"
        self.cand = None
        self.cand_t = None
        self.pick = {"CE": None, "PE": None}     # sticky strike per side
        self.ema = {"CE": None, "PE": None}
        self.cheap = {"CE": False, "PE": False}  # per-side hysteresis
        self.last_alert = -1e9
        self.prev_state = None
        self.noise = collections.deque()         # (t, |best cheap%|)
        self.h = {}                              # key -> deque of (t, mid, delta, gamma, theta); "FUT" -> (t, f)

    def _record(self, env):
        now = env.t
        lo = now - KEEP_S
        if _ok(env.fut):
            dq = self.h.setdefault("FUT", collections.deque())
            dq.append((now, float(env.fut)))
        for key, r in env.chain.items():
            dq = self.h.setdefault(key, collections.deque())
            dq.append((now, r.get("mid"), r.get("delta"), r.get("gamma"), r.get("theta")))
        for key in list(self.h):
            dq = self.h[key]
            while dq and dq[0][0] < lo:
                dq.popleft()
            if not dq:
                del self.h[key]

    def _lag(self, env, k, rr, f0, f_now):
        r = env.chain.get((k, rr))
        if not r:
            return None
        ask, age, d_now = r.get("ask"), r.get("age"), r.get("delta")
        if not _ok(ask) or ask <= 0 or (_ok(age) and age > config.EXIT_QUOTE_STALE_S):
            return None
        if not _ok(d_now) or abs(d_now) < MIN_DELTA:
            return None
        now = env.t
        s0 = _at(self.h.get((k, rr)) or (), now - ANCHOR_S)
        if s0 is None or now - s0[0] > ANCHOR_S + 5:
            return None
        _, mid0, d0, g0, th0 = s0
        if not (_ok(mid0) and mid0 > 0 and _ok(d0) and _ok(g0) and _ok(th0)):
            return None
        dF = f_now - f0
        v = mid0 + d0 * dF + 0.5 * g0 * dF * dF + th0 * (now - s0[0]) / 60.0
        return 100.0 * (v - ask) / ask, ask

    def _best(self, env, rr, f0, f_now):
        ks = env.strikes()
        if not ks:
            return None, {}
        ref = env.spot or env.fut
        atm = min(ks, key=lambda k: abs(k - ref))
        i = ks.index(atm)
        elig = ks[max(0, i - 2): i + 1] if rr == "CE" else ks[i: i + 3]
        res = {}
        for k in elig:
            x = self._lag(env, k, rr, f0, f_now)
            if x is not None:
                res[k] = x
        if not res:
            return None, res
        kb = max(res, key=lambda k: res[k][0])
        held = self.pick[rr]
        if held in res and kb != held and res[kb][0] - res[held][0] < SWITCH_PP:
            kb = held
        self.pick[rr] = kb
        return kb, res

    def update(self, env):
        self._record(env)
        if env.hm < 9 * 60 + 17 or not (env.spot or env.fut):
            return {"state": "WARMING", "text": "needs a minute of quotes after the open"}
        f_now = env.fut
        fs = _at(self.h.get("FUT") or (), env.t - ANCHOR_S)
        if not _ok(f_now) or fs is None or env.t - fs[0] > ANCHOR_S + 5:
            return {"state": "WARMING", "text": "needs 60 s of futures prices"}
        nz = [x for _, x in self.noise]
        bar = max(CHEAP_MIN, NOISE_X * sorted(nz)[len(nz) // 2]) if len(nz) >= 12 else max(CHEAP_MIN, 2.5)
        best = {}
        for rr in ("CE", "PE"):
            k, res = self._best(env, rr, fs[1], f_now)
            if k is None:
                self.pick[rr] = None
                self.ema[rr] = None
                self.cheap[rr] = False
                continue
            c, ask = res[k]
            e = self.ema[rr]
            e = c if e is None else e + EMA_A * (c - e)
            self.ema[rr] = e
            best[rr] = (k, c, ask, e)
            self.cheap[rr] = e >= (OFF_FRAC * bar if self.cheap[rr] else bar)
            self.noise.append((env.t, abs(c)))
        while self.noise and self.noise[0][0] < env.t - NOISE_S:
            self.noise.popleft()
        if not best:
            return {"state": "WARMING", "text": "no eligible strike (|delta| >= 0.52) with 60 s of history"}

        ch = [rr for rr in ("CE", "PE") if rr in best and self.cheap[rr]]
        if ch:
            rr = self.shown[:2] if self.shown[:2] in ch and self.shown.endswith("CHEAP") else max(ch, key=lambda s: best[s][3])
            want = f"{rr} CHEAP"
        elif all(best[s][3] < -bar for s in best):
            want = "ALL DEAR"
        else:
            want = "NOTHING CHEAP"

        # persistence: a new state must be wanted for HOLD_S before it is shown
        if want != self.shown:
            if self.cand != want:
                self.cand, self.cand_t = want, env.t
            if env.t - self.cand_t >= HOLD_S or self.shown == "WARMING":
                self.shown = want
                self.cand = None
        else:
            self.cand = None
        state = self.shown
        side = state[:2] if state in ("CE CHEAP", "PE CHEAP") else None

        parts = []
        for s in ("CE", "PE"):
            if s in best:
                k, c, ask, e = best[s]
                parts.append(f"{s} {k:.0f} {c:+.1f}% (ask {ask:.1f})")
            else:
                parts.append(f"{s} n/a")
        top = max(best.values(), key=lambda b: b[1])
        text = "cheapest vs 60-s fwd move: " + ", ".join(parts)
        text += f"; bar {bar:.1f}%"
        text += "; expiry day: strikes differ" if env.dte0 else "; normal day: ~1 spread apart"
        plan, alert = "", False
        if side and side in best:
            k, c, ask, e = best[side]
            plan = f"buy {side} {k:.0f} at <= {ask:.1f}"
            if state != self.prev_state and e >= ALERT_X * bar and env.t - self.last_alert >= ALERT_GAP_S:
                alert = True
                self.last_alert = env.t
        self.prev_state = state
        return {"state": state, "side": side, "value": top[1], "unit": "%", "text": text, "plan": plan,
                "alert": alert}
