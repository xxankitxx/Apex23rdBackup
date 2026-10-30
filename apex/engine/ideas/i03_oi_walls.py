"""OI walls (owner, 28 Oct: "PE/CE OI writers ... show who is pulling the market or whether it is sideways").

Ceiling = the CE strike with the most OI above spot; floor = the PE strike with the most OI below spot, both inside
the ATM +- 9 strikes (of the 10-strike band) of the nearest weekly. Shows how many points spot has to the nearer wall and whether a wall
is retreating: its OI cut >= 4 % from its 15-min high (writers covering), or the wall migrated away from spot.

Hysteresis: a new max-OI strike must hold 2 minutes before it becomes the wall (unless spot crossed the old one);
"near" enters at <= 60 pts and leaves at > 90 pts; retreat enters at a 4 % cut and leaves below 2 %; a migration
counts for 10 min; any new state must be seen on 2 consecutive calls. OI updates about once a minute, so only the
max-over-15-min vs latest OI is used (a repeated value is never treated as new)."""
import math

import numpy as np

NAME = "oi_walls"
TITLE = "OI walls (ceiling / floor)"
IDEA = ("Max CE OI above spot is the writers' ceiling, max PE OI below is the floor: how far is spot from them, "
        "and are the writers retreating (room for the move)?")
VERDICT = ("Rejected as an entry rule 28-29 Oct (R2-02): wall short-covering lift 0.72, wall shift 0.90, all-in "
           "trades red on 6/7 days; shown for watching.")
EVERY_S = 5

NEAR_IN, NEAR_OUT = 60.0, 90.0      # pts: wall "near" enters / leaves
CUT_IN, CUT_OUT = 0.04, 0.02        # wall OI cut from its 15-min high: retreat enters / leaves
CUT_WIN = 900                       # s, window for the wall's OI high
CONFIRM_S = 120                     # s a new max-OI strike must hold before it is the wall
MIGRATE_S = 600                     # s a wall migration (away from spot) counts as a retreat
EDGE = 9                            # strikes from ATM considered for a wall (band is 10)
MIN_OI = 1000.0                     # ignore a wall with less OI than this (start of day / empty strikes)


def _ok(x):
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x) and x > 0


class _Wall:
    """One wall (rr "CE" ceiling above spot / "PE" floor below spot) with a confirmed strike."""

    def __init__(self, rr):
        self.rr = rr
        self.k = None           # confirmed wall strike
        self.k_since = None     # t the wall was confirmed
        self.cand = None
        self.cand_t = None
        self.moved_t = None     # t of the last migration away from spot
        self.moved_from = None
        self.retreat = False

    def update(self, env, ref):
        best_k, best_oi = None, 0.0
        for (k, rr), r in env.chain.items():
            if rr != self.rr:
                continue
            if (self.rr == "CE" and k <= ref) or (self.rr == "PE" and k >= ref):
                continue
            if abs(k - env.atm) > EDGE * env.step:     # band-edge strikes flicker in and out of the band
                continue
            oi = r.get("oi")
            if _ok(oi) and oi > best_oi:
                best_k, best_oi = k, oi
        if best_k is None or best_oi < MIN_OI:
            self.cand = None
            if self.k is not None and not self._valid(ref):
                self.k = None
            return None
        t = env.t
        if best_k != self.cand:
            self.cand, self.cand_t = best_k, t
        if self.k is None or not self._valid(ref):
            self._set(best_k, t, migrate=False)
        elif best_k != self.k and t - self.cand_t >= CONFIRM_S:
            away = best_k > self.k if self.rr == "CE" else best_k < self.k
            # a migration counts only if the old wall's writers really cut (not just a strike entering the band)
            self._set(best_k, t, migrate=away and self.cut(env)[0] >= CUT_OUT)
        return self.k

    def _valid(self, ref):
        return self.k is not None and ((self.k > ref) if self.rr == "CE" else (self.k < ref))

    def _set(self, k, t, migrate):
        if migrate:
            self.moved_t, self.moved_from = t, self.k
        self.k, self.k_since = k, t

    def cut(self, env):
        """-> (cut fraction of the wall OI vs its 15-min high, current OI)."""
        _, V = env.hist.series((self.k, self.rr), "oi", secs=CUT_WIN)
        V = V[np.isfinite(V) & (V > 0)] if len(V) else V
        if len(V) == 0:
            return 0.0, math.nan
        hi, now = float(V.max()), float(V[-1])
        return (1.0 - now / hi) if hi > 0 else 0.0, now

    def retreating(self, env, cut):
        migrated = self.moved_t is not None and env.t - self.moved_t <= MIGRATE_S
        self.retreat = migrated or (cut >= (CUT_OUT if self.retreat else CUT_IN))
        return self.retreat, migrated


class Idea:
    def __init__(self):
        self.ce = _Wall("CE")
        self.pe = _Wall("PE")
        self.near_c = False
        self.near_f = False
        self.shown = None       # (state, side) on screen
        self.pend = None
        self.last = None
        self.alerts = 0
        self.broken = set()

    def update(self, env):
        ref = env.spot
        if not _ok(ref):
            if self.last is not None:
                return dict(self.last, text="spot untrusted; walls as of last good spot")
            return {"state": "WARMING", "text": "waiting for a trusted spot"}
        if env.hm < 9 * 60 + 17:
            return {"state": "WARMING", "text": "OI settles after the open"}
        # break alerts: spot through a wall that held >= 15 min
        alert, alert_txt = False, ""
        for w, crossed in ((self.ce, self.ce.k is not None and ref > self.ce.k + 5),
                           (self.pe, self.pe.k is not None and ref < self.pe.k - 5)):
            if crossed and w.k_since is not None and env.t - w.k_since >= 900 and (w.rr, w.k) not in self.broken \
                    and self.alerts < 10:
                self.broken.add((w.rr, w.k))
                self.alerts += 1
                alert = True
                alert_txt = f"spot {ref:,.0f} broke the {'ceiling CE' if w.rr == 'CE' else 'floor PE'} {w.k}; "
        kc = self.ce.update(env, ref)
        kf = self.pe.update(env, ref)
        if kc is None and kf is None:
            return {"state": "WARMING", "text": "no OI in the band yet"}
        dc = (kc - ref) if kc is not None else math.inf
        df = (ref - kf) if kf is not None else math.inf
        self.near_c = dc <= (NEAR_OUT if self.near_c else NEAR_IN)
        self.near_f = df <= (NEAR_OUT if self.near_f else NEAR_IN)
        cc, oic = self.ce.cut(env) if kc is not None else (0.0, math.nan)
        cf, oif = self.pe.cut(env) if kf is not None else (0.0, math.nan)
        rc, mc = self.ce.retreating(env, cc) if kc is not None else (False, False)
        rf, mf = self.pe.retreating(env, cf) if kf is not None else (False, False)

        if rc and (not rf or cc >= cf):
            st, side = "CEILING RETREATING", "CE"
        elif rf:
            st, side = "FLOOR RETREATING", "PE"
        elif self.near_c and self.near_f:
            st, side = "BOXED IN", None
        elif self.near_c:
            st, side = "CEILING NEAR", None
        elif self.near_f:
            st, side = "FLOOR NEAR", None
        elif dc >= df:
            st, side = "ROOM UP", None
        else:
            st, side = "ROOM DOWN", None
        # ROOM UP / ROOM DOWN flip only on a clear (1.3x) imbalance
        if self.shown and self.shown[0] in ("ROOM UP", "ROOM DOWN") and st in ("ROOM UP", "ROOM DOWN") \
                and st != self.shown[0] and max(dc, df) < 1.3 * min(dc, df):
            st = self.shown[0]
        # persistence: a new state must be seen twice in a row
        if self.shown is None:
            self.shown = (st, side)
        elif (st, side) != self.shown:
            if self.pend == (st, side):
                self.shown, self.pend = (st, side), None
            else:
                self.pend = (st, side)
        else:
            self.pend = None
        st, side = self.shown

        def wtxt(name, k, d, oi, cut):
            if k is None:
                return f"no {name} in band"
            s = f"{name} {k} ({d:+.0f} pts, OI {oi / 1e5:.1f} L" if math.isfinite(oi) else f"{name} {k} ({d:+.0f} pts"
            return s + (f", cut {cut * 100:.0f}%)" if cut >= 0.01 else ")")
        txt = alert_txt + wtxt("ceiling CE", kc, dc, oic, cc) + "; " + wtxt("floor PE", kf, -df, oif, cf)
        if mc and self.ce.moved_from:
            txt += f"; ceiling moved {self.ce.moved_from}->{kc}"
        if mf and self.pe.moved_from:
            txt += f"; floor moved {self.pe.moved_from}->{kf}"
        plan = ""
        if st == "CEILING RETREATING" and kc is not None:
            plan = f"watch CE {int(round(ref / env.step) * env.step)} if spot clears {kc}"
        elif st == "FLOOR RETREATING" and kf is not None:
            plan = f"watch PE {int(round(ref / env.step) * env.step)} if spot breaks {kf}"
        elif st == "BOXED IN":
            plan = f"range {kf}-{kc}: buyers wait for a break"
        val = min(dc, df)
        out = {"state": st, "side": side, "value": None if not math.isfinite(val) else val, "unit": "pts",
               "text": txt, "plan": plan, "alert": alert}
        self.last = dict(out, alert=False)
        return out
