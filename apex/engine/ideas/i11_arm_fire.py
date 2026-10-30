"""Arm -> fire (owner, 28 Oct: "be prepared in advance, then take the entry only when the time is apt"; "big moves last
10-15 minutes").

QUIET   -> spot's 5-min range is ordinary.
ARMED   -> the 5-min range has shrunk to <= ARM_RATIO x its typical 5-min range (median of the minute-sampled 5-min
           ranges over the last hour). A box is frozen: 5-min high + buffer / 5-min low - buffer, and the plan names the
           option to buy each way (ATM, or 1 ITM if the ATM |delta| < 0.52) at its current ask.
FIRED   -> spot closed outside the box: alert, side = CE (up) / PE (down). Held FIRE_S (12 min, the owner's 10-15 min).
COOLING -> after the fire window, or at once if spot falls back through the far side of the box (failed break);
           lasts COOL_S, then QUIET (or ARMED again if still compressed).

Observer only. Value = compression ratio (5-min range / typical 5-min range)."""
import math

import numpy as np

NAME = "arm_fire"
TITLE = "Arm -> fire (compression break)"
IDEA = ("Be prepared in advance: when spot goes quiet, set the breakout levels and the strike to buy both ways, "
        "then act only when a level breaks; the move lasts 10-15 min.")
VERDICT = ("R2-04 (28 Oct): rejected as an entry rule - compression does not lead moves (pctile ~0.5), fires 8-17 % "
           "precise, LODO -49k; shown for watching.")
EVERY_S = 5

ARM_RATIO = 0.60      # arm when 5-min range <= 0.60 x typical
DISARM_RATIO = 0.90   # an armed box is dropped (no break) once the range is back to 0.90 x typical
WIN_S = 300           # the 5-min window
MIN_SAMPLES = 10      # minute samples of the 5-min range needed for "typical" (=> ~15 min after the open)
BUF_FRAC = 0.15       # breakout buffer = 15 % of the typical 5-min range ...
BUF_MIN = 3.0         # ... at least 3 points
ARM_TTL_S = 1200      # an arm lives at most 20 min
FIRE_S = 720          # fired window: 12 min
COOL_S = 300          # cooling: 5 min
MIN_DELTA = 0.52
LAST_ARM_HM = 15 * 60 + 10
MAX_ALERTS = 10
STALE_S = 60          # spot unchanged this long = stale


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


class Idea:
    def __init__(self):
        self.mode = "QUIET"
        self.mode_t = None
        self.box = None          # (lo, hi, t_armed)
        self.fire = None         # dict(dir, level, t, spot)
        self.r5_samples = []     # (minute, r5)
        self.last_min = None
        self.alerts = 0
        self.plan = ""
        self.fail = False
        self.live_from = None
        self._box_min = None
        # pay numpy's first-call costs here, not inside a timed update()
        z = np.array([1.0, 2.0, np.nan])
        np.nanmax(z), np.nanmin(z), np.searchsorted(z[:2], 1.5)

    # option to buy for one direction: ATM, or 1 ITM if the ATM |delta| is under MIN_DELTA
    def _pick(self, env, rr):
        step = env.step or 50
        itm = env.atm - step if rr == "CE" else env.atm + step
        for k in (env.atm, itm):
            r = env.row(k, rr)
            if not r:
                continue
            d = _num(r.get("delta"))
            if d is not None and abs(d) >= MIN_DELTA:
                return k, _num(r.get("ask"))
        r = env.row(itm, rr) or env.row(env.atm, rr)
        if not r:
            return None, None
        return int(r["strike"]), _num(r.get("ask"))

    def _make_plan(self, env, lo, hi):
        kc, pc = self._pick(env, "CE")
        kp, pp = self._pick(env, "PE")
        up = f"UP>{hi:,.0f} CE{kc}@{pc:.1f}" if kc and pc else f"UP>{hi:,.0f} CE ?"
        dn = f"DN<{lo:,.0f} PE{kp}@{pp:.1f}" if kp and pp else f"DN<{lo:,.0f} PE ?"
        return f"{up} | {dn}"

    def update(self, env):
        T, S = env.hist.series("SPOT", secs=1800)
        if len(S) < 120:
            return {"state": "WARMING", "text": "needs a few minutes of spot"}
        now = float(T[-1])
        spot = float(S[-1])
        if not math.isfinite(spot):
            return {"state": "WARMING", "text": "spot missing"}
        # stale spot (feed gap or a frozen print): drop any plan, re-learn 5 min of live spot before arming again
        k = int(np.searchsorted(T, now - STALE_S))
        stale = (env.t - now > 10) or (len(S) - k > 5 and float(np.nanmax(S[k:]) - np.nanmin(S[k:])) == 0.0)
        if stale or self.live_from is None:
            self.live_from = now
            if stale:
                self.mode, self.mode_t, self.box, self.fire = "QUIET", now, None, None
                return {"state": "SPOT STALE", "text": f"spot has not printed a change for {STALE_S} s; plan dropped"}
        if now - self.live_from < WIN_S:
            return {"state": "WARMING", "text": f"spot live again {(now - self.live_from) / 60:.0f} min; needs 5"}
        j = int(np.searchsorted(T, now - WIN_S))
        w5 = S[j:]
        hi5, lo5 = float(np.nanmax(w5)), float(np.nanmin(w5))
        r5 = hi5 - lo5
        r30 = float(np.nanmax(S) - np.nanmin(S))
        minute = int(now // 60)
        if minute != self.last_min and now - T[0] >= WIN_S - 5:
            self.last_min = minute
            self.r5_samples.append((minute, r5))
            self.r5_samples = [x for x in self.r5_samples if x[0] > minute - 60]
        if len(self.r5_samples) < MIN_SAMPLES:
            return {"state": "WARMING", "value": None,
                    "text": f"learning the typical 5-min range ({len(self.r5_samples)}/{MIN_SAMPLES} min)"}
        v = sorted(x[1] for x in self.r5_samples)
        n = len(v)
        typ = v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])
        if typ <= 0:
            return {"state": "WARMING", "text": "spot has not moved"}
        ratio = r5 / typ
        buf = max(BUF_MIN, BUF_FRAC * typ)
        hm = env.hm
        alert = False

        if self.mode == "FIRED":
            f = self.fire
            failed = (spot < self.box[0]) if f["dir"] > 0 else (spot > self.box[1])
            if failed or now - f["t"] >= FIRE_S:
                self.mode, self.mode_t = "COOLING", now
                self.fail = failed
        elif self.mode == "COOLING":
            if now - self.mode_t >= COOL_S:
                self.mode, self.mode_t, self.box, self.fire = "QUIET", now, None, None
        elif self.mode == "ARMED":
            lo, hi, ta = self.box
            if spot > hi or spot < lo:
                d = 1 if spot > hi else -1
                self.fire = {"dir": d, "level": hi if d > 0 else lo, "t": now, "spot": spot}
                self.mode, self.mode_t = "FIRED", now
                if self.alerts < MAX_ALERTS:
                    alert = True
                    self.alerts += 1
            elif ratio >= DISARM_RATIO or now - ta >= ARM_TTL_S or hm >= LAST_ARM_HM:
                self.mode, self.mode_t, self.box = "QUIET", now, None
            elif minute != getattr(self, "_box_min", None) and ratio <= ARM_RATIO:
                # still tight: re-centre the box on the latest 5-min range once a minute (only ever tightens)
                self._box_min = minute
                nlo, nhi = lo5 - buf, hi5 + buf
                if nhi - nlo < hi - lo and nlo <= spot <= nhi:
                    self.box = (nlo, nhi, ta)
                    self.plan = self._make_plan(env, nlo, nhi)
        if self.mode == "QUIET" and ratio <= ARM_RATIO and hm < LAST_ARM_HM:
            self.box = (lo5 - buf, hi5 + buf, now)
            self._box_min = minute
            self.mode, self.mode_t = "ARMED", now
            self.plan = self._make_plan(env, *self.box[:2])

        rng = f"5-min range {r5:.0f} pts = {ratio:.2f}x typical {typ:.0f} (30-min {r30:.0f})"
        if self.mode == "ARMED":
            lo, hi, ta = self.box
            return {"state": "ARMED", "value": ratio, "unit": "x typ", "plan": self.plan,
                    "text": f"{rng}; box {lo:,.0f}-{hi:,.0f}, armed {(now - ta) / 60:.0f} min"}
        if self.mode == "FIRED":
            f = self.fire
            d = f["dir"]
            pts = (spot - f["level"]) * d
            return {"state": "FIRED UP" if d > 0 else "FIRED DOWN", "side": "CE" if d > 0 else "PE",
                    "value": ratio, "unit": "x typ", "alert": alert, "plan": self.plan,
                    "text": f"spot broke {f['level']:,.0f} {(now - f['t']) / 60:.0f} min ago, now {pts:+.0f} pts "
                            f"beyond; {FIRE_S / 60 - (now - f['t']) / 60:.0f} min left of the 12-min window"}
        if self.mode == "COOLING":
            why = "break failed back through the box" if getattr(self, "fail", False) else "12-min window over"
            return {"state": "COOLING", "value": ratio, "unit": "x typ",
                    "text": f"{why}; {rng}; quiet again in {(COOL_S - (now - self.mode_t)) / 60:.0f} min"}
        return {"state": "QUIET", "value": ratio, "unit": "x typ",
                "text": f"{rng}; arms at <= {ARM_RATIO:.2f}x"}
