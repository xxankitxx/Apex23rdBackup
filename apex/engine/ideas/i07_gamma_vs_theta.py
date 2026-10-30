"""Gamma vs theta (owner, 28 Oct: "use greeks comprehensively").

The option buyer's ledger right now. A long ATM option earns about 0.5 x gamma x (spot move)^2 and pays |theta| every
minute (theta is the rent for gamma). Gamma income uses spot's realised variance per minute over the last 10 min
(overlapping 60-s changes, min of spot and futures, the same per-minute definition as the engine's buyer-edge gate, which uses 30 min).
Greeks are interpolated between the two strikes around spot so the ratio does not jump when the ATM strike changes.

    ratio = 0.5 x gamma x var_per_min / |theta_per_min|     (straddle: summed over CE and PE)

States: GAMMA PAYS (ratio >= ~1), EVEN, THETA BLEEDS (ratio < ~0.5), with hysteresis + a 2-evaluation persistence.
side = the leg whose own ratio is clearly better (>= 15 %) while gamma pays; otherwise None."""
import math

import numpy as np

NAME = "gamma_theta"
TITLE = "Gamma vs theta (buyer's rent)"
IDEA = "Greeks in full: does Nifty's actual movement (gamma income) pay the theta rent of an ATM option right now?"
VERDICT = ("27-28 Oct: the only test with buyer edge (ratio>=0.5: +3.5 %/trade); as a gate on the champion it cut "
           "too many trades. Watch only.")
EVERY_S = 5

WIN_S = 600          # realised-variance window (10 min)
LAG_S = 60           # per-minute changes
MIN_PAIRS = 240      # need ~5 min of 60-s changes before speaking

# hysteresis bands on the straddle ratio: (enter, leave)
PAYS_IN, PAYS_OUT = 1.10, 0.90
BLEED_IN, BLEED_OUT = 0.45, 0.55
PERSIST = 2          # evaluations a new state must hold before it shows
SIDE_IN, SIDE_OUT = 1.15, 1.05
ALERT_GAP_S = 1800   # at most one "gamma pays" alert per 30 min


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return math.nan
    return v if math.isfinite(v) else math.nan


class Idea:
    def __init__(self):
        self.state = None
        self.cand = None
        self.cand_n = 0
        self.side = None
        self.last_alert_t = -1e9
        self.peak = None

    # ── greeks at spot, interpolated between the two strikes around it ──
    def _leg(self, env, ref, rr):
        step = env.step or 50
        lo = math.floor(ref / step) * step
        hi = lo + step
        w = (ref - lo) / step
        vals = []
        for k, wk in ((int(lo), 1 - w), (int(hi), w)):
            r = env.chain.get((k, rr))
            if r is None:
                continue
            g, th = _num(r.get("gamma")), _num(r.get("theta"))
            if not (g > 0) or not math.isfinite(th) or th == 0:
                continue
            vals.append((wk, g, abs(th), _num(r.get("delta"))))
        if not vals:
            return None
        ws = sum(v[0] for v in vals)
        if ws <= 1e-9:      # only the far strike is valid: use it as is
            ws = len(vals)
            vals = [(1.0,) + v[1:] for v in vals]
        g = sum(v[0] * v[1] for v in vals) / ws
        th = sum(v[0] * v[2] for v in vals) / ws
        return g, th

    def _var_per_min(self, env):
        """min over spot and futures: a glitch in one feed (e.g. the 400-pt spot jump at 15:20 on 23 Oct) cannot
        fake gamma income, while a real move shows in both."""
        vs, ns = self._var_key(env, "SPOT")
        vf, nf = self._var_key(env, "FUT")
        if vs is None or ns < MIN_PAIRS:
            return vf, nf
        if vf is None or nf < MIN_PAIRS:
            return vs, ns
        return min(vs, vf), max(ns, nf)

    def _var_key(self, env, key):
        T, S = env.hist.series(key, secs=WIN_S + LAG_S)
        ok = np.isfinite(S)
        T, S = T[ok], S[ok]
        if len(S) < LAG_S + 10:
            return None, 0
        # overlapping 60-s changes: for each second t, S(t) - S(t-60) (nearest sample at or before t-60)
        j = np.searchsorted(T, T - LAG_S, side="right") - 1
        m = (j >= 0) & (T - T[np.maximum(j, 0)] >= LAG_S - 2) & (T - T[np.maximum(j, 0)] <= LAG_S + 5)
        if m.sum() < 10:
            return None, int(m.sum())
        d = S[m] - S[j[m]]
        return float(np.mean(d * d)), int(m.sum())

    def _settle(self, raw):
        """hysteresis + persistence -> shown state"""
        if raw == self.state:
            self.cand, self.cand_n = None, 0
            return self.state
        if raw == self.cand:
            self.cand_n += 1
        else:
            self.cand, self.cand_n = raw, 1
        if self.state is None or self.state == "WARMING" or self.cand_n >= PERSIST:
            self.state, self.cand, self.cand_n = raw, None, 0
        return self.state

    def update(self, env):
        ref = env.spot or env.fut
        if not ref or env.hm < 9 * 60 + 16:
            return {"state": "WARMING", "text": "waiting for the first minutes of spot"}
        v, n = self._var_per_min(env)
        if v is None or n < MIN_PAIRS:
            self.state = "WARMING"
            return {"state": "WARMING", "text": f"collecting spot moves ({n} of {MIN_PAIRS} one-minute changes)"}
        if env.dte0 and env.hm >= 15 * 60 + 15:
            self.state, self.side = "EXPIRY CLOSE", None
            return {"state": "EXPIRY CLOSE", "value": None,
                    "text": f"expiry last 15 min: greeks are unstable; spot moves {math.sqrt(v):.1f} pts/min (10m)"}
        ce, pe = self._leg(env, ref, "CE"), self._leg(env, ref, "PE")
        if ce is None and pe is None:
            return {"state": "NO GREEKS", "text": "no gamma/theta for the ATM strikes yet"}
        legs = [x for x in (ce, pe) if x is not None]
        G = sum(x[0] for x in legs)
        TH = sum(x[1] for x in legs)
        ratio = 0.5 * G * v / TH
        rc = 0.5 * ce[0] * v / ce[1] if ce else math.nan
        rp = 0.5 * pe[0] * v / pe[1] if pe else math.nan

        # state with hysteresis around the current one
        cur = self.state if self.state not in (None, "WARMING", "NO GREEKS") else None
        if cur == "GAMMA PAYS":
            raw = "GAMMA PAYS" if ratio >= PAYS_OUT else ("THETA BLEEDS" if ratio < BLEED_IN else "EVEN")
        elif cur == "THETA BLEEDS":
            raw = "THETA BLEEDS" if ratio <= BLEED_OUT else ("GAMMA PAYS" if ratio >= PAYS_IN else "EVEN")
        else:
            raw = "GAMMA PAYS" if ratio >= PAYS_IN else ("THETA BLEEDS" if ratio < BLEED_IN else "EVEN")
        prev = self.state
        st = self._settle(raw)

        # side: the leg whose own ratio is clearly better, only while gamma pays
        side = None
        if st == "GAMMA PAYS" and math.isfinite(rc) and math.isfinite(rp) and min(rc, rp) > 0:
            q = rc / rp
            if self.side == "CE":
                side = "CE" if q >= SIDE_OUT else None
            elif self.side == "PE":
                side = "PE" if 1 / q >= SIDE_OUT else None
            if side is None:
                side = "CE" if q >= SIDE_IN else ("PE" if 1 / q >= SIDE_IN else None)
        self.side = side

        alert = False
        if st == "GAMMA PAYS" and prev != "GAMMA PAYS" and env.t - self.last_alert_t >= ALERT_GAP_S:
            alert, self.last_alert_t = True, env.t

        vpm = math.sqrt(v)
        g_avg, th_avg = G / len(legs), TH / len(legs)
        be = math.sqrt(2 * th_avg / g_avg) if g_avg > 0 else math.nan      # pts/min needed to pay the rent
        fx = lambda r: f"{r:.2f}x" if math.isfinite(r) else "n/a"
        text = (f"G {g_avg:.4f}/pt, Theta -{th_avg:.2f}/min (CE {fx(rc)}, PE {fx(rp)}); spot moves {vpm:.1f} pts/min "
                f"(10m) -> gamma earns {0.5 * g_avg * v:.2f} vs rent {th_avg:.2f}/min")
        if st == "GAMMA PAYS":
            plan = f"buying in season; still pays while spot moves >= {be * math.sqrt(PAYS_OUT):.1f} pts/min"
        elif st == "THETA BLEEDS":
            plan = f"buyers bleed: needs >= {be:.1f} pts/min to break even (now {vpm:.1f})"
        else:
            plan = f"break-even {be:.1f} pts/min; now {vpm:.1f}"
        return {"state": st, "side": side, "value": ratio, "unit": "x rent", "text": text, "plan": plan,
                "alert": alert}
