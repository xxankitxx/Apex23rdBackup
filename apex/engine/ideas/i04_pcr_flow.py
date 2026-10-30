"""Fresh-OI put-call ratio near the money (owner, 28 Oct: "PE/CE OI writers ... show who is pulling the market").

Over ATM +- 5 strikes of the nearest weekly: dPE = change in total PE open interest over the last 15 min, dCE the same
for calls. Fresh PCR = dPE / dCE when both are written; in general it is mapped through the balance
B = (dPE - dCE) / (|dPE| + |dCE|) as (1 + B) / (1 - B), so PE writing + CE unwinding reads as a high PCR (bullish) and
the opposite as a low one. The last 5 min are used the same way to see whether the lead is turning.

OI updates about once a minute per contract: the card recomputes only when some OI value in the band actually
changed (or the ATM moved); repeated values return the previous reading unchanged."""
import bisect
import math

NAME = "pcr_flow"
TITLE = "Fresh-OI PCR (ATM±5, 15 min)"
IDEA = "Who is writing near the money right now: fresh put OI vs fresh call OI over 15 min, and its 5-min turn."
VERDICT = ("Rejected as an entry rule 28-29 Oct: PCR>1.3 up / <0.8 down lift 1.10 (precision 0.22 vs 0.20); "
           "OI gates lost -1.1 L LODO. Shown for watching.")
EVERY_S = 5

BAND = 5            # strikes each side of ATM
WIN = 900           # 15-min window (s)
WIN5 = 300          # turn window (s)
MIN_HIST = 300      # need 5 min of OI before reading anything
SIG15 = 0.004       # |dPE|+|dCE| must be >= 0.4 % of band OI for a lead
SIG5 = 0.002        # same for the 5-min turn
B_IN, B_OUT = 0.25, 0.10    # balance to enter / leave a lead (PCR 1.67 / 1.22 and the inverses)
B_TURN = 0.50               # 5-min balance against the lead that counts as FLIPPING
DWELL = 180         # s a state must stand before it can change (except into WARMING)


def _at(log, t):
    """value of a change-log [(t, v), ...] at time t (first value if t is before it)."""
    j = bisect.bisect_right(log[0], t) - 1
    return log[1][max(j, 0)]


def _pcr(b):
    b = max(-0.98, min(0.98, b))
    return max(0.1, min(10.0, (1 + b) / (1 - b)))


def _q(x):
    """OI quantity in lakh/k with sign."""
    a = abs(x)
    s = "+" if x >= 0 else "-"
    return f"{s}{a / 1e5:.1f}L" if a >= 1e5 else f"{s}{a / 1e3:.0f}k"


class Idea:
    def __init__(self):
        self.logs = {}          # (strike, rr) -> ([t of change], [OI]) ; first entry = first OI seen today
        self.sig = None         # signature of the OI values last computed on
        self.last_calc = -1e9
        self.out = {"state": "WARMING", "text": "waiting for 5 min of OI"}
        self.state = "WARMING"
        self.since_t = None
        self.lead_since = None  # when the current lead (PUT/CALL) began
        self.alerts = 0
        self._flip_from = None

    def _set(self, st, now):
        if st != self.state:
            self.state = st
            self.since_t = now

    def update(self, env):
        hist, atm, step, now = env.hist, env.atm, env.step or 50, env.t
        if atm is None or now is None:
            return {"state": "WARMING", "text": "no ATM yet"}
        # 1) keep our own OI change log per contract (only CHANGED values are new information)
        for key, r in env.chain.items():
            v = r.get("oi")
            if v is None or not (v > 0):
                continue
            log = self.logs.get(key)
            if log is None:
                self.logs[key] = ([now], [float(v)])
            elif log[1][-1] != v:
                log[0].append(now)
                log[1].append(float(v))
        # 2) 15-min / 5-min / since-seen changes over ATM +- BAND
        d = {"CE": [0.0, 0.0, 0.0], "PE": [0.0, 0.0, 0.0]}     # d15, d5, oi now
        dopen = {"CE": 0.0, "PE": 0.0}
        sig, n_ok, span = [atm], 0, 0.0
        for k in range(atm - BAND * step, atm + (BAND + 1) * step, step):
            for rr in ("CE", "PE"):
                log = self.logs.get((k, rr))
                if log is None:
                    continue
                now_v = log[1][-1]
                n_ok += 1
                span = max(span, min(WIN, now - log[0][0]))
                d[rr][0] += now_v - _at(log, now - WIN)
                d[rr][1] += now_v - _at(log, now - WIN5)
                d[rr][2] += now_v
                dopen[rr] += now_v - log[1][0]
                sig.append(now_v)
        if n_ok < 12 or span < MIN_HIST:
            self.out = {"state": "WARMING", "text": f"{n_ok} contracts, {span / 60:.0f} min of OI log (needs 5)"}
            self._set("WARMING", now)
            return self.out
        # OI ticks ~once a minute: same values -> same reading (no new information)
        sig = tuple(sig)
        if sig == self.sig and now - self.last_calc < 90:
            out = dict(self.out)
            out["alert"] = False
            return out
        self.sig, self.last_calc = sig, now

        dce, dpe = d["CE"][0], d["PE"][0]
        tot = d["CE"][2] + d["PE"][2]
        g15 = abs(dce) + abs(dpe)
        b15 = (dpe - dce) / g15 if g15 > 0 else 0.0
        strong = tot > 0 and g15 >= SIG15 * tot
        dce5, dpe5 = d["CE"][1], d["PE"][1]
        g5 = abs(dce5) + abs(dpe5)
        b5 = (dpe5 - dce5) / g5 if g5 > 0 else 0.0
        strong5 = tot > 0 and g5 >= SIG5 * tot
        pcr, pcr5 = _pcr(b15), _pcr(b5)

        prev = self.state
        lead = prev if prev in ("PUT WRITERS LEAD", "CALL WRITERS LEAD", "FLIPPING") else None
        if lead == "FLIPPING":
            lead = self._flip_from
        # target state with hysteresis
        if strong and dce < 0 and dpe < 0:
            want = "BOTH UNWINDING"
        elif lead == "PUT WRITERS LEAD" and strong and b15 >= B_OUT:
            want = lead
        elif lead == "CALL WRITERS LEAD" and strong and b15 <= -B_OUT:
            want = lead
        elif strong and b15 >= B_IN:
            want = "PUT WRITERS LEAD"
        elif strong and b15 <= -B_IN:
            want = "CALL WRITERS LEAD"
        else:
            want = "BALANCED"
        if want in ("PUT WRITERS LEAD", "CALL WRITERS LEAD") and strong5:
            against = b5 <= -B_TURN if want == "PUT WRITERS LEAD" else b5 >= B_TURN
            if against:
                self._flip_from = want
                want = "FLIPPING"
        alert = False
        if want != prev and (prev == "WARMING" or self.since_t is None or now - self.since_t >= DWELL):
            # rare, notable: a lead that stood >= 10 min starts turning or is replaced by the opposite one
            if (prev in ("PUT WRITERS LEAD", "CALL WRITERS LEAD") and self.lead_since is not None
                    and now - self.lead_since >= 600 and want not in ("BALANCED", prev) and self.alerts < 10):
                alert = True
                self.alerts += 1
            if want in ("PUT WRITERS LEAD", "CALL WRITERS LEAD"):
                if prev != "FLIPPING" or getattr(self, "_flip_from", None) != want:
                    self.lead_since = now
            elif want != "FLIPPING":
                self.lead_since = None
            self._set(want, now)
        st = self.state

        side = "CE" if st == "PUT WRITERS LEAD" else "PE" if st == "CALL WRITERS LEAD" else None
        g_open = abs(dopen["PE"]) + abs(dopen["CE"])
        pcr_open = _pcr((dopen["PE"] - dopen["CE"]) / g_open) if g_open > 0 else 1.0
        text = (f"15m: PE {_q(dpe)} CE {_q(dce)} (PCR {pcr:.2f}, {100 * g15 / tot:.1f}% of band OI); "
                f"5m PCR {pcr5:.2f}; since seen PE {_q(dopen['PE'])} CE {_q(dopen['CE'])} (PCR {pcr_open:.2f})")
        plan = ""
        if st == "PUT WRITERS LEAD":
            plan = f"writers back up: CE {atm} if spot holds; watch 5m PCR < {_pcr(-B_TURN):.2f}"
        elif st == "CALL WRITERS LEAD":
            plan = f"writers cap up: PE {atm} if spot holds; watch 5m PCR > {_pcr(B_TURN):.2f}"
        elif st == "FLIPPING":
            plan = f"lead ({getattr(self, '_flip_from', '')}) turning: stand aside or tighten"
        self.out = {"state": st, "side": side, "value": pcr, "unit": "PCR", "text": text, "plan": plan, "alert": alert}
        return self.out
