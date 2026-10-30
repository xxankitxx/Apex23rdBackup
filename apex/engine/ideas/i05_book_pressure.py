"""Book pressure (owner, 28 Oct: "the number of sellers and buyers on each strike and the speed of change").

Per side (CE and PE), on the ATM strike and the strike one step in the money (CE: ATM-50, PE: ATM+50), we track the
queued buy vs sell quantity P = log(tbq / tsq) and how fast it CHANGES over 1 and 5 minutes, always on one fixed
contract (never across a strike switch). The level of tbq/tsq is NOT used: Breeze tbq/tsq on options is dominated by
far resting stub orders (median ratio 4-22x, top-5 levels < 0.01 % of tbq; R2_01), so only changes carry anything.
Changes are z-scored against the day's own spread of 5-min changes (causal).

The side whose ratio climbs fastest is "being pulled": BUYERS RUSHING when the climb is mostly tbq growing, SELLERS
PULLING OUT when it is mostly tsq shrinking. Research says this ECHOES price (lags it), it does not lead it."""
import collections
import math

NAME = "book_pressure"
TITLE = "Buyers vs sellers queue speed"
IDEA = "Buyers vs sellers queued on each strike and how fast that changes: the side whose buyers build fastest is pulled."
VERDICT = ("R2_01/R2_06: tbq/tsq level is far stub orders; its speed lags price (rho +0.6-0.7 with past move), "
           "residual ~0 ahead; no gate/exit survived. Changes only, for watching.")
EVERY_S = 5

WARM_S = 15 * 60          # day-so-far spread needs 15 min of samples
Z_IN, Z_OUT = 1.6, 0.7    # enter / leave a pulled state (hysteresis)
Z_GAP = 0.8               # leader must beat the other side by this many z
Z_ALERT = 2.5             # rare: a pull that starts very fast (entry z)
MIN_HOLD = 60.0           # s a state is held before it may change
ALERT_GAP = 30 * 60.0     # s between alerts
TOL = 20.0                # s: a lagged sample must be within this of the wanted time


def _good(x):
    return x is not None and math.isfinite(x) and x > 0


class Idea:
    def __init__(self):
        self.n = 0              # running spread of 5-min dP samples (pooled sides)
        self.s2 = 0.0
        self.t0 = None
        self.state = "WARMING"
        self.side = None
        self.kind = None        # "BUY" / "SELL" (locked while a pulled state is held)
        self.since = -1e9
        self.last_alert = -1e9
        self.buf = {}
        self.last_gc = 0.0

    def _record(self, env):
        """keep our own 5-s samples of (t, tbq, tsq) per contract for ~6 min (cheaper than the 1-Hz history)."""
        now = env.t
        for key, r in env.chain.items():
            b, s = r.get("tbq"), r.get("tsq")
            if not (_good(b) and _good(s)):
                continue
            q = self.buf.get(key)
            if q is None:
                q = self.buf[key] = collections.deque()
            q.append((now, b, s))
            while q and now - q[0][0] > 400:
                q.popleft()
        if now - self.last_gc > 600:
            self.last_gc = now
            for key in [k for k, q in self.buf.items() if not q or now - q[-1][0] > 400]:
                del self.buf[key]

    def _contract(self, env, key):
        """-> (dP1, dP5, d tbq 5m, d tsq 5m) for one fixed contract (log changes for P, absolute qty for tbq/tsq)."""
        q = self.buf.get(key)
        now = env.t
        if not q or now - q[-1][0] > TOL:
            return None
        _, b0, s0 = q[-1]
        b1 = s1 = b5 = s5 = None
        for t, b, s in reversed(q):
            if b1 is None and t <= now - 60:
                b1, s1 = (b, s) if now - 60 - t <= TOL else (0.0, 0.0)
            if t <= now - 300:
                if now - 300 - t <= TOL:
                    b5, s5 = b, s
                break
        p0 = math.log(b0 / s0)
        d1 = p0 - math.log(b1 / s1) if b1 else math.nan
        if b5:
            return d1, p0 - math.log(b5 / s5), b0 - b5, s0 - s5
        return d1, math.nan, math.nan, math.nan

    def _side(self, env, rr):
        atm, step = env.atm, env.step or 50
        itm = atm - step if rr == "CE" else atm + step
        got = [self._contract(env, (k, rr)) for k in (atm, itm)]
        got = [g for g in got if g is not None and math.isfinite(g[1])]
        if not got:
            return None
        n = len(got)
        d1s = [g[0] for g in got if math.isfinite(g[0])]
        return {"d1": sum(d1s) / len(d1s) if d1s else math.nan, "d5": sum(g[1] for g in got) / n,
                "db": sum(g[2] for g in got) / n, "ds": sum(g[3] for g in got) / n}

    def update(self, env):
        now = env.t
        if self.t0 is None:
            self.t0 = now
        if env.atm is None:
            return {"state": "WARMING", "text": "no ATM yet"}
        self._record(env)
        ce, pe = self._side(env, "CE"), self._side(env, "PE")
        for x in (ce, pe):
            if x is not None:
                self.n += 1
                self.s2 += x["d5"] * x["d5"]
        if now - self.t0 < WARM_S or self.n < 60:
            return {"state": "WARMING", "text": "needs 15 min of tbq/tsq on ATM and 1-ITM CE/PE"}
        if ce is None or pe is None:
            # warmed up but no 5-min tbq/tsq on one side (ATM just moved / quotes missing): hold the last state
            return {"state": self.state, "side": self.side, "value": None, "unit": "%/min",
                    "text": f"no fresh 5-min tbq/tsq on {'CE' if ce is None else 'PE'} ATM/1-ITM; holding {self.state}"}
        sd = math.sqrt(self.s2 / self.n) or 1e-9
        zc, zp = ce["d5"] / sd, pe["d5"] / sd
        S = {"CE": (zc, ce), "PE": (zp, pe)}
        lead = "CE" if zc >= zp else "PE"
        zl, xl = S[lead]
        zo = S["PE" if lead == "CE" else "CE"][0]

        held = now - self.since >= MIN_HOLD
        alert = False
        if self.side is None:
            want = lead if (zl >= Z_IN and zl - zo >= Z_GAP and not (xl["d1"] < 0)) else None
        else:
            zs = S[self.side][0]
            other = "PE" if self.side == "CE" else "CE"
            zx = S[other][0]
            if zx >= Z_IN and zx - zs >= Z_GAP and not (S[other][1]["d1"] < 0):
                want = other
            elif zs < Z_OUT:
                want = None
            else:
                want = self.side
        if want != self.side and (held or self.state == "WARMING"):
            self.side, self.since = want, now
            if want is not None:
                x = S[want][1]
                self.kind = "BUY" if x["db"] >= -x["ds"] else "SELL"   # qty added to bids vs qty pulled from offers
                if S[want][0] >= Z_ALERT and now - self.last_alert >= ALERT_GAP:
                    alert, self.last_alert = True, now
            else:
                self.kind = None
        if self.side is None:
            self.state = "BALANCED"
        elif self.kind == "BUY":
            self.state = f"{self.side} BUYERS RUSHING"
        else:
            self.state = f"SELLERS PULLING OUT {self.side}"

        show = self.side or lead
        zs_, x = S[show]
        speed = 100.0 * (math.exp(x["d5"]) - 1.0) / 5.0          # % change of tbq/tsq per minute, 5-min window
        sp1 = 100.0 * (math.exp(x["d1"]) - 1.0) if math.isfinite(x["d1"]) else float("nan")
        txt = (f"{show} tbq/tsq {speed:+.1f}%/min (5m), {sp1:+.1f}% last 1m, z {zs_:+.1f}; 5m: bids {x['db'] / 1e3:+.0f}k"
               f" offers {x['ds'] / 1e3:+.0f}k qty; CE z {zc:+.1f} PE z {zp:+.1f}")
        plan = ""
        if self.side is not None:
            k = env.atm
            plan = f"echoes price (lags): {self.side} {k} only if spot confirms"
        return {"state": self.state, "side": self.side, "value": speed, "unit": "%/min", "text": txt, "plan": plan,
                "alert": alert}
