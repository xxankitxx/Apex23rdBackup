"""OI writers (owner idea 2, 28 Oct: "PE/CE OI writers, long unwinding, short covering show who is pulling the market
or whether it is sideways").

For CE and PE separately over ATM +- 3 strikes, the last ~15 minutes are classified by OI change vs premium change:
    OI up   + premium up   = long build-up        OI up   + premium down = short build-up (writing)
    OI down + premium up   = short covering       OI down + premium down = long unwinding
and the two sides are combined into one plain verdict (bulls / bears pulling, sideways writers, unwinding, mixed).

OI prints about once a minute, so the comparison is always newest print vs the print ~15 min earlier (a repeated OI
value adds nothing), and the verdict must hold 90 s before the card changes."""
import math

from collections import deque

NAME = "oi_writers"
TITLE = "OI writers: who is pulling"
IDEA = ("PE/CE writers, short covering and long unwinding near the money show whether bulls or bears are pulling "
        "the market, or whether it is sideways.")
VERDICT = ("Rejected as an entry rule 28 Oct (R2-02): build-up classes had lift 0.7-1.0 for 10-min moves, all-in "
           "trades red 5-7/7 days; shown for watching.")
EVERY_S = 5

N_STRIKES = 3          # ATM +- 3
LOOK_S = 900           # compare with ~15 min ago
MIN_LOOK_S = 300       # need >= 5 min of history
OI_DEAD = 0.01         # |side OI change| < 1 % of side OI = flat
PX_DEAD = 0.03         # |side premium change| < 3 % = flat
HOLD_S = 90            # a new verdict must persist this long
LAKH = 1e5

# per-side class -> vote (+1 bull, -1 bear)
_VOTE = {("CE", "LB"): 1, ("CE", "SB"): -1, ("CE", "SC"): 1, ("CE", "LU"): -1,
         ("PE", "LB"): -1, ("PE", "SB"): 1, ("PE", "SC"): -1, ("PE", "LU"): 1}
_WORD = {"LB": "long build-up", "SB": "writing", "SC": "short covering", "LU": "long unwinding", "FLAT": "flat"}


class Idea:
    def __init__(self):
        self.state = None        # confirmed verdict
        self.cand = None
        self.cand_t = None
        self.last_dir_alert = {}  # state -> t of last alert
        self.alerts = 0
        self.side = None
        self.value = None
        self.buf = {}            # (strike, rr) -> deque of (t, oi, mid)

    def _record(self, env):
        """Keep my own 5-s samples (t, last good OI, mid) per contract in the band: O(1) per call."""
        now = env.t
        cut = now - LOOK_S
        for key, r in env.chain.items():
            oi, mid = r.get("oi"), r.get("mid")
            dq = self.buf.get(key)
            if dq is None:
                dq = self.buf[key] = deque()
            if oi is None or not math.isfinite(oi) or oi <= 0:
                oi = dq[-1][1] if dq else None       # carry the last print
            if oi is None or mid is None or not math.isfinite(mid) or mid <= 0:
                continue
            dq.append((now, float(oi), float(mid)))
            while len(dq) > 1 and dq[1][0] <= cut:
                dq.popleft()

    def _side(self, env, rr, strikes):
        """-> (class, OI change, OI now, premium change %, look seconds) or None."""
        now = env.t
        d_oi = oi_now = p0 = p1 = 0.0
        look_min = None
        n = 0
        for k in strikes:
            dq = self.buf.get((k, rr))
            if not dq or dq[-1][0] < now - 30:
                continue
            t0, o0, m0 = dq[0]
            _, o1, m1 = dq[-1]
            look = now - t0
            if look < MIN_LOOK_S:
                continue
            d_oi += o1 - o0
            oi_now += o1
            p0 += m0
            p1 += m1
            n += 1
            look_min = look if look_min is None else min(look_min, look)
        if n < 2 or oi_now <= 0 or p0 <= 0:
            return None
        dp = p1 / p0 - 1.0
        oi_up = d_oi > OI_DEAD * oi_now
        oi_dn = d_oi < -OI_DEAD * oi_now
        px_up, px_dn = dp > PX_DEAD, dp < -PX_DEAD
        if oi_up and px_up:
            c = "LB"
        elif oi_up and px_dn:
            c = "SB"
        elif oi_dn and px_up:
            c = "SC"
        elif oi_dn and px_dn:
            c = "LU"
        else:
            c = "FLAT"
        return c, d_oi, oi_now, dp * 100.0, look_min

    def update(self, env):
        if env.atm is None or env.step is None or env.t is None:
            return {"state": "WARMING", "text": "no spot yet"}
        self._record(env)
        strikes = [int(env.atm + i * env.step) for i in range(-N_STRIKES, N_STRIKES + 1)]
        ce = self._side(env, "CE", strikes)
        pe = self._side(env, "PE", strikes)
        if ce is None or pe is None:
            if self.state is None:
                return {"state": "WARMING", "text": "needs 5 min of OI on ATM +- 3 strikes"}
            return {"state": self.state, "side": self.side, "value": self.value, "unit": "L PE-CE OI",
                    "text": "ATM moved to strikes without 5 min of OI yet; holding the last verdict"}
        cc, ce_doi, _, ce_dp, lk1 = ce
        pc, pe_doi, _, pe_dp, lk2 = pe
        look = min(lk1, lk2) / 60.0

        if cc == "SB" and pc == "SB":
            v = "SIDEWAYS: BOTH WRITING"
        elif cc == "LU" and pc == "LU":
            v = "UNWINDING BOTH SIDES"
        elif cc == "FLAT" and pc == "FLAT":
            v = "QUIET"
        else:
            vote = _VOTE.get(("CE", cc), 0) + _VOTE.get(("PE", pc), 0)
            v = "BULLS PULLING" if vote > 0 else "BEARS PULLING" if vote < 0 else "MIXED"

        # persistence: a new verdict must hold HOLD_S before it replaces the shown one
        now = env.t
        alert = False
        if self.state is None:
            self.state = v
        elif v == self.state:
            self.cand = None
        else:
            if v != self.cand:
                self.cand, self.cand_t = v, now
            elif now - self.cand_t >= HOLD_S:
                self.state, self.cand = v, None
                # rare: the textbook pattern, writers on one side + short covering on the other
                classic = (v == "BULLS PULLING" and cc == "SC" and pc == "SB") or \
                          (v == "BEARS PULLING" and cc == "SB" and pc == "SC")
                if classic and self.alerts < 6 and now - self.last_dir_alert.get(v, -1e9) >= 1200:
                    alert = True
                    self.alerts += 1
                    self.last_dir_alert[v] = now
        st = self.state

        net = (pe_doi - ce_doi) / LAKH       # + = put writers adding more than call writers (bullish lean)
        side = "CE" if st == "BULLS PULLING" else "PE" if st == "BEARS PULLING" else None
        text = (f"{look:.0f} min, ATM+-3: CE {_WORD[cc]} (OI {ce_doi / LAKH:+.1f} L, prem {ce_dp:+.0f}%), "
                f"PE {_WORD[pc]} (OI {pe_doi / LAKH:+.1f} L, prem {pe_dp:+.0f}%)")
        if self.cand and self.cand != st:
            text += f"; turning {self.cand.lower()}?"
        plan = ""
        if side and env.spot:
            k = int(env.atm)
            plan = (f"{side} {k} if spot keeps {'above' if side == 'CE' else 'below'} {env.spot:,.0f}"
                    f" (OI lags ~1 min)")
        self.side, self.value = side, net
        return {"state": st, "side": side, "value": net, "unit": "L PE-CE OI",
                "text": text, "plan": plan, "alert": alert}
