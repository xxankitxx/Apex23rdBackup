"""Straddle pulse (owner, 17 Oct: "A straddle falls from 9:15 to the close. When it SPIKES, one leg has picked up
gamma ... those are the moments to buy the leg whose gamma and delta are rising").

The ATM straddle at a FIXED strike K (CE mid + PE mid), so a spike is measured on one contract pair:

  K           the ATM when the card starts; re-anchored only after the live ATM has differed from K for > 2 min
  over-theta  S(now) - S(5 min ago) + the decay theta says S should have lost in those 5 min (pts per 5 min).
              > 0: the straddle is beating theta -> energy, a move is on; < 0: sellers in control, buyers bleed.
  leg share   each leg's own 5-min change (its theta added back); the leg with the larger gain is doing the work.

States: WARMING, ENERGY CE LEG, ENERGY PE LEG, VOL BID BOTH, DECAYING, FLAT. Hysteresis on the thresholds plus a
15-s persistence to enter energy,
30 s to leave or switch it, 60 s between FLAT and DECAYING."""
import math

NAME = "straddle_pulse"
TITLE = "Straddle pulse (over theta)"
IDEA = ("ATM straddle at a fixed strike: rising faster than theta = energy, a move is on (which leg is doing it); "
        "falling = sellers in control, buyers bleed.")
VERDICT = ("Engine already has a straddle watch (observer); straddle spikes were never a champion entry and R2 found "
           "straddle change 0.40-0.58 AUC for a coming move. Shown for watching.")
EVERY_S = 5

WIN_S = 300.0          # the 5-min window
REANCHOR_S = 120.0     # ATM must differ from K this long before re-anchoring
HOLD_CALLS = 3         # a new state must be seen on 3 calls in a row (15 s)
HOLD_LEAVE = 6         # leaving / switching an energy state needs 30 s
HOLD_QUIET = 12        # FLAT <-> DECAYING needs 60 s
QUIET = ("FLAT", "DECAYING")
MIN_PTS = 4.0          # minimum energy threshold (pts per 5 min)
MIN_FRAC = 0.025       # ... or 2.5 % of the straddle
BOTH_RATIO = 0.4       # both legs gaining and the smaller >= 40 % of the larger -> VOL BID BOTH
ALERT_GAP_S = 1200.0   # at most one alert per 20 min


def _ok(x):
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x)


class Idea:
    def __init__(self):
        self.K = None
        self.away_since = None
        self.state = "WARMING"
        self.cand = None
        self.cand_n = 0
        self.last_alert = -1e9
        self.mabs = None       # slow EMA of |over-theta|
        self.peak = None       # largest over-theta in the current energy state

    def _leg(self, env, rr, ago):
        h = env.hist
        a = h.at((self.K, rr), "mid", ago)
        if not _ok(a) or a <= 0:
            a = h.at((self.K, rr), "ltp", ago)
        return a if (_ok(a) and a > 0) else math.nan

    def update(self, env):
        atm = env.atm
        if atm is None:
            return {"state": "WARMING", "text": "no ATM yet"}
        now = env.t
        # ── anchor ───────────────────────────────────────────────────────
        if self.K is None:
            self.K = atm
        elif atm != self.K:
            if self.away_since is None:
                self.away_since = now
            elif now - self.away_since > REANCHOR_S:
                self.K, self.away_since = atm, None
        else:
            self.away_since = None
        K = self.K
        if env.hm < 9 * 60 + 20:
            return {"state": "WARMING", "text": f"straddle {K} warming up (first 5 min)"}

        ce0, pe0 = self._leg(env, "CE", 0.0), self._leg(env, "PE", 0.0)
        ce5, pe5 = self._leg(env, "CE", WIN_S), self._leg(env, "PE", WIN_S)
        if not all(math.isfinite(x) for x in (ce0, pe0, ce5, pe5)):
            return {"state": "WARMING", "text": f"straddle {K}: no 5-min quote history yet"}
        rc, rp = env.row(K, "CE"), env.row(K, "PE")
        tc = rc.get("theta") if rc else None
        tp = rp.get("theta") if rp else None
        if not _ok(tc):
            tc = env.hist.at((K, "CE"), "theta", 0.0)
        if not _ok(tp):
            tp = env.hist.at((K, "PE"), "theta", 0.0)
        tc = abs(tc) if _ok(tc) else 0.0
        tp = abs(tp) if _ok(tp) else 0.0
        mins = WIN_S / 60.0
        S, S5 = ce0 + pe0, ce5 + pe5
        dS = S - S5
        decay = (tc + tp) * mins
        over = dS + decay
        xce = (ce0 - ce5) + tc * mins
        xpe = (pe0 - pe5) + tp * mins
        share = xce / (abs(xce) + abs(xpe)) if (abs(xce) + abs(xpe)) > 1e-9 else 0.0

        # threshold: a floor, a share of the straddle, and 1.5 x the day's typical |over-theta| (slow EMA)
        thr = max(MIN_PTS, MIN_FRAC * S, 1.5 * self.mabs) if self.mabs is not None else max(MIN_PTS, MIN_FRAC * S)
        self.mabs = abs(over) if self.mabs is None else self.mabs + (abs(over) - self.mabs) / 360.0
        energy = self.state.startswith("ENERGY") or self.state == "VOL BID BOTH"
        # energy = beating theta AND the straddle itself not falling (on expiry the model theta is large, so a
        # straddle that merely falls slower than theta is not a move). Easier to stay than to enter.
        on = (over >= 0.6 * thr and dS >= -0.25 * thr) if energy else (over >= thr and dS >= 0.25 * thr)
        if on:
            hi, lo = max(xce, xpe), min(xce, xpe)
            if lo > 0 and lo >= BOTH_RATIO * hi:
                c = "VOL BID BOTH"
            else:
                c = "ENERGY CE LEG" if xce >= xpe else "ENERGY PE LEG"
                # keep the current leg unless the other one clearly took over
                if self.state in ("ENERGY CE LEG", "ENERGY PE LEG") and c != self.state:
                    if abs(xce - xpe) < 0.25 * thr:
                        c = self.state
        else:
            was_dec = self.state == "DECAYING"
            if dS <= (-0.15 * thr if was_dec else -max(decay, 0.6 * thr)):
                c = "DECAYING"
            else:
                c = "FLAT"

        # ── persistence ─────────────────────────────────────────────────
        if c == self.state or self.state == "WARMING":
            self.state, self.cand, self.cand_n = c, None, 0
        elif c == self.cand:
            self.cand_n += 1
            if self.state in QUIET:
                need = HOLD_QUIET if c in QUIET else HOLD_CALLS
            else:
                need = HOLD_LEAVE       # leaving an energy state or switching leg: 30 s
            if self.cand_n >= need:
                self.state, self.cand, self.cand_n = c, None, 0
                self.peak = None
        else:
            self.cand, self.cand_n = c, 1
        st = self.state

        alert = False
        if st.startswith("ENERGY") or st == "VOL BID BOTH":
            self.peak = over if self.peak is None else max(self.peak, over)
            if st.startswith("ENERGY") and over >= 2 * thr and now - self.last_alert >= ALERT_GAP_S:
                alert, self.last_alert = True, now
        else:
            self.peak = None

        side = "CE" if st == "ENERGY CE LEG" else "PE" if st == "ENERGY PE LEG" else None
        text = (f"{K} straddle {S:.1f} ({dS:+.1f} in 5 min, theta {-decay:.1f}): over theta {over:+.1f}; "
                f"CE {xce:+.1f} / PE {xpe:+.1f} ex-theta, CE share {share * 100:+.0f}%")
        if st.startswith("ENERGY"):
            plan = (f"{side} {K} is the gamma leg; energy ends if over-theta < {0.6 * thr:.1f}"
                    + (f" (peak {self.peak:.1f})" if self.peak is not None else ""))
        elif st == "VOL BID BOTH":
            plan = "IV bid on both legs: no direction yet"
        elif st == "DECAYING":
            plan = "sellers in control: buyers bleed theta"
        else:
            plan = f"energy if over-theta > {thr:.1f} pts / 5 min"
        return {"state": st, "side": side, "value": over, "unit": "pts/5m", "text": text, "plan": plan,
                "alert": alert}
