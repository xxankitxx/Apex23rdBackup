"""Room to run (owner, 28 Oct: "will it break down after buying?" / "we end up buying at very high prices").

The two entry checks the champion t28_cheap uses (paper.flow_veto: req_move_veto + entry_hi5_veto_pct), shown live for
BOTH the ATM CE and the ATM PE so the owner sees which side is buyable right now:

  1. room:   the spot move needed for +10 % on the ask within 15 min, after 15 min of theta
             (need = 0.10*ask - theta_min*15; solve 0.5*gamma*x^2 + |delta|*x = need), compared with the spot range of
             the last 15 min. Buyable when required move <= the 15-min range (champion: req_move_k = 1.0).
  2. top:    the option's mid within 2 % of its own 5-min high = buying at the top (champion: entry_hi5_veto_pct = 2,
             applied there to pullback/retest entries only; shown here always).

Display only: hysteresis (enter <= 1.00x, leave > 1.10x; at-top enter within 2 %, leave beyond 3 %) plus a 60-s debounce on each
side flag and a 30-s state persistence keep the state from flickering."""
import math

import numpy as np

NAME = "room_to_run"
TITLE = "Room to run (+10 % in 15 min)"
IDEA = ("Will it break down after buying? Needed spot move for +10 % in 15 min vs the last 15-min range, and is the "
        "option at its 5-min high - for ATM CE and PE.")
VERDICT = ("These two checks are IN the champion t28_cheap since 29 Oct (+Rs 87 k on 7 days); the card shows them for "
           "both sides all the time.")
EVERY_S = 5

K_IN, K_OUT = 1.00, 1.10        # required move / 15-min range: buyable at <= K_IN, stops being buyable above K_OUT
TOP_IN, TOP_OUT = 2.0, 3.0      # % below the 5-min high: "at top" within TOP_IN, cleared beyond TOP_OUT
PERSIST = 6                     # readings a new state must hold before it is shown
FLAG_HOLD = 12                  # readings (60 s) a side's room / at-top flag must hold before it changes
ALERT_QUIET_S = 1200            # alert when a side turns buyable after >= 20 min with nothing buyable


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def req_move(ask, delta, gamma, theta_min):
    """Spot points needed for +10 % of the ask in 15 min after theta (same formula as paper.flow_veto)."""
    need = 0.10 * ask - theta_min * 15.0
    a, b = 0.5 * max(gamma, 0.0), abs(delta)
    if a > 0:
        return (-b + (b * b + 4 * a * need) ** 0.5) / (2 * a)
    return need / max(b, 1e-6)


class Idea:
    def __init__(self):
        self.ok = {"CE": False, "PE": False}       # hysteresis memory per side
        self.top = {"CE": False, "PE": False}
        self.shown = None
        self.cand, self.cand_n = None, 0
        self.none_since = None                     # when "nothing buyable" started
        self.pend = {}

    def _flag(self, flags, rr, raw):
        """Debounce: a side's flag changes only after FLAG_HOLD readings in a row disagree with it."""
        key = (id(flags), rr)
        if raw == flags[rr]:
            self.pend[key] = 0
            return
        n = self.pend.get(key, 0) + 1
        if n >= FLAG_HOLD:
            flags[rr], n = raw, 0
        self.pend[key] = n

    def _side(self, env, rr, rng):
        r = env.row(env.atm, rr)
        if not r:
            return None
        ask = _num(r.get("ask")) or _num(r.get("ltp"))
        dl, gm, th = _num(r.get("delta")), _num(r.get("gamma")), _num(r.get("theta"))
        if not ask or ask <= 0 or not dl or gm is None or th is None:
            return None
        req = req_move(ask, dl, gm, th)
        if not math.isfinite(req) or req <= 0:
            return None
        ratio = req / max(rng, 1.0)
        # 5-min high of the mid (needs >= 4 min of this strike's history, like flow_veto)
        T, M = env.hist.series((env.atm, rr), "mid", secs=300)
        ok = np.isfinite(M) & (M > 0)
        mid = _num(r.get("mid"))
        off = None
        if ok.sum() >= 30 and len(T) and T[ok][0] <= env.t - 240 and mid:
            hi = float(M[ok].max())
            off = 100.0 * (1.0 - mid / hi) if hi > 0 else None
        k = K_OUT if self.ok[rr] else K_IN
        self._flag(self.ok, rr, ratio <= k)
        self._flag(self.top, rr, off is not None and off <= (TOP_OUT if self.top[rr] else TOP_IN))
        return {"req": req, "ratio": ratio, "off": off, "ask": ask, "room": self.ok[rr], "top": self.top[rr],
                "buy": self.ok[rr] and not self.top[rr]}

    def update(self, env):
        if not env.spot or not env.atm:
            return {"state": "WARMING", "text": "waiting for a trusted spot"}
        T, S = env.hist.series("SPOT", secs=900)
        ok = np.isfinite(S)
        if ok.sum() < 60 or not len(T) or T[ok][0] > env.t - 840:
            return {"state": "WARMING", "text": "needs 15 min of spot for the range"}
        S = S[ok]
        rng = float(S.max() - S.min())
        sd = {rr: self._side(env, rr, rng) for rr in ("CE", "PE")}
        ce, pe = sd["CE"], sd["PE"]
        if ce is None and pe is None:
            return {"state": "WARMING", "text": f"no ATM {env.atm} quote/greeks yet"}
        cb, pb = bool(ce and ce["buy"]), bool(pe and pe["buy"])
        if cb and pb:
            st = "BOTH OK"
        elif cb:
            st = "CE BUYABLE"
        elif pb:
            st = "PE BUYABLE"
        elif ce and ce["room"] and ce["top"]:
            st = "CE AT TOP"
        elif pe and pe["room"] and pe["top"]:
            st = "PE AT TOP"
        else:
            st = "NEITHER (move too big)"
        # persistence
        if self.shown is None:
            self.shown = st
        elif st != self.shown:
            if st == self.cand:
                self.cand_n += 1
            else:
                self.cand, self.cand_n = st, 1
            if self.cand_n >= PERSIST:
                self.shown, self.cand, self.cand_n = st, None, 0
        else:
            self.cand, self.cand_n = None, 0
        st = self.shown
        buyable = st in ("BOTH OK", "CE BUYABLE", "PE BUYABLE")
        alert = False
        if buyable:
            if self.none_since is not None and env.t - self.none_since >= ALERT_QUIET_S:
                alert = True
            self.none_since = None
        elif self.none_since is None:
            self.none_since = env.t
        side = "CE" if st in ("CE BUYABLE",) else "PE" if st in ("PE BUYABLE",) else None
        cands = [s for s in (("CE", ce), ("PE", pe)) if s[1]]
        best_rr, best = min(cands, key=lambda s: s[1]["ratio"])

        def part(rr, d):
            if not d:
                return f"{rr} n/a"
            top = "" if d["off"] is None else f", {d['off']:.1f}% off 5m hi"
            return f"{rr} {d['ask']:.0f} needs {d['req']:.0f}{top}"

        text = (f"ATM {env.atm}: {part('CE', ce)}; {part('PE', pe)}; spot 15-min range {rng:.0f} pts")
        plan = ""
        if buyable:
            plan = f"{side or best_rr} {env.atm}: +10 % needs {best['req']:.0f} pts (range {rng:.0f})"
        elif st.endswith("AT TOP"):
            rr = st[:2]
            plan = f"{rr} {env.atm}: wait for a dip > {TOP_OUT:.0f} % below its 5-min high"
        else:
            plan = f"wait: range must widen to {best['req']:.0f} pts or premium cheapen"
        return {"state": st, "side": side, "value": best["ratio"], "unit": "x range", "text": text, "plan": plan,
                "alert": alert}
