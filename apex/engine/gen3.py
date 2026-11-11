"""Third batch of shadow signals (docs/38 section 7), 10 Nov 2026. Shadow only: never in the Conductor pool.

  S01  cash_futures_transmission   NEW candidate. The heavyweights' STOCK FUTURES have moved by more than their cash
                                   prices and the Nifty future's own move explain, and the index has not answered yet.
       s01_trans      the signal
       s01_ctl_cash   control: the cash basket's move alone, at the same occupancy (its own 99th percentile)
       s01_ctl_sfut   control: the stock-futures basket's move alone, at the same occupancy
  S03  breadth_recruitment         REDESIGN of N06 / the breadth control, not a new mechanism. Weight has been JOINING
                                   one direction for 30 s (the path), the stock futures agree, the index is still quiet.
       s03_recruit    the signal. Its matched control is the frozen gen2 `ctl_breadth` (breadth level alone).

FROZEN MANIFEST (P below). Coefficients and thresholds were fixed on 10 Nov from the 15 recorded sessions using the
SIGNAL side only (data/research/gen2_v2/s01_s03_calib.json: one regression of the stock-futures basket on the cash
basket and the index future, and percentiles of each quantity). No later price was read to choose a number. The 15
sessions are discovery material for these signals; a result on them is not a held-out result.

Same interface as gen2 for the books (paper.evaluate_gen / gen_bracket / _gen_exit): sig, why, fired, ready, void.
Fixed work per second: two weighted sums over the heavyweights and one look-back, no fitting, no allocation that grows."""
import math
from collections import deque

import numpy as np

VERSION = 1
GAP_S = 5.0            # a hole longer than this between two updates restarts the windows
WARM_S = 120           # seconds of clean data before any signal (the longest look-back is 60 s)
Q_FRESH_S = 3.0        # the Nifty future's own quote
HW_FRESH_S = 5.0       # a stock's cash print and its future's two-sided quote

P = {
    "win_s": 30,                 # every return below is over this window
    "cover": 0.70,               # share of heavyweight weight with fresh cash AND fresh futures at both ends
    # S01: z = stock-futures basket move - b_cash * cash basket move - b_mom * Nifty future's move (index points)
    "s01_b_cash": 0.4554, "s01_b_mom": 0.4359,
    "s01_z": 7.0,                # |z| at or above its 99th percentile (7.24 over the 15 sessions)
    "s01_rearm": 3.5,            # the signal re-arms when |z| falls below this
    "s01_cash10_against": 0.0,   # the cash basket's last 10 s must not be against the signal (points, > this)
    "s01_idx_max": 10.0,         # the index has not already moved this far with the signal in the window
    "s01_rev": 3.5,              # exit: z this far the other way (the gap reversed)
    "s01_cover_exit": 0.50,      # exit: participating coverage below this
    "s01_tp": 12.0, "s01_sl": 10.0, "s01_hold": 120,
    # S01 controls (99th percentiles of their own size, same bracket)
    "c_cash": 22.9, "c_cash_rearm": 11.0, "c_sfut": 21.0, "c_sfut_rearm": 10.0,
    # S03: b = (weight up - weight down) / fresh weight on the cash prices, in [-1, 1]
    "s03_b": 0.60,               # breadth now
    "s03_join": 0.80,            # breadth now minus breadth 30 s ago, with the direction (weight that joined)
    "s03_fut_b": 0.50,           # the same breadth on the stock futures agrees at least this much
    "s03_quiet_pts": 6.0,        # the Nifty future's own move in the window (same as the breadth control)
    "s03_rearm": 0.30,
    "s03_rev": -0.20,            # exit: breadth this far against the trade (recruitment reversed)
    "s03_tp": 12.0, "s03_sl": 10.0, "s03_hold": 300,   # the breadth control's bracket
}
NAMES = ("s01_trans", "s01_ctl_cash", "s01_ctl_sfut", "s03_recruit")


class Gen3:
    def __init__(self, params=None):
        self.p = dict(P, **(params or {}))
        self.sig, self.fired, self.why = {}, {}, {}
        self.n_sig = {n: 0 for n in NAMES}
        self.w = None
        self.gaps = 0
        self._reset()

    def _reset(self):
        self.h = deque(maxlen=80)        # (t, mid, cash vector, stock-futures mid vector, valid mask, breadth)
        self.clean_s = 0
        self.last = None
        self.armed = {n: True for n in NAMES}
        self.z = self.cc = self.cs = self.cm = self.b = self.bf = self.cov = None

    # ── helpers ──────────────────────────────────────────────────────────────────────────────────────────────────────
    def _ago(self, s):
        """The stored second s seconds back (at most 2 s older), or None."""
        now = self.h[-1][0]
        for k in range(len(self.h) - 1, -1, -1):
            dt = now - self.h[k][0]
            if dt >= s - 1e-9:
                return self.h[k] if dt <= s + 2.0 else None
        return None

    def _emit(self, name, now, d, why, tp, sl, hold):
        s = {"name": name, "id": int(now), "t": now, "dir": int(d), "why": why, "tp": float(tp), "sl": float(sl),
             "hold": int(hold), "ep": "G3-" + name.upper().replace("_", "-")}
        self.sig[name] = s
        self.fired[(name, s["id"])] = s
        self.n_sig[name] += 1
        if len(self.fired) > 4000:
            for k in sorted(self.fired, key=lambda q: q[1])[:2000]:
                del self.fired[k]

    def view(self):
        r = lambda v, n=2: None if v is None else round(float(v), n)
        return {"v": VERSION, "warm": self.clean_s >= WARM_S, "z": r(self.z), "cash": r(self.cc), "sfut": r(self.cs),
                "idx": r(self.cm), "breadth": r(self.b, 3), "fut_breadth": r(self.bf, 3), "cover": r(self.cov, 3),
                "signals": dict(self.n_sig), "gaps": self.gaps}

    # ── the per-second update ────────────────────────────────────────────────────────────────────────────────────────
    def update(self, now_s, bid, ask, q_age, cash, cash_age, sf_bid, sf_ask, sf_age, w, ok=True):
        """One second. cash / sf_bid / sf_ask and their ages are aligned vectors over the heavyweights (NaN or inf for
        a stock with no future or no packet). A data gap or a stale index quote restarts the windows."""
        self.z = self.cc = self.cs = self.cm = self.b = self.bf = self.cov = None
        if self.last is not None and now_s - self.last < 0.999:
            return
        fresh_q = bid > 0 and ask >= bid and q_age is not None and q_age <= Q_FRESH_S
        if not ok or not fresh_q or cash is None or w is None or (self.last is not None and now_s - self.last > GAP_S):
            if self.h:
                self.gaps += 1
            self._reset()
            self.last = now_s if (ok and fresh_q) else None
            for n in NAMES:
                self.why[n] = "data gap: the windows restart"
            return
        self.clean_s += 1 if self.last is None else min(GAP_S, now_s - self.last)
        self.last = now_s
        mid = 0.5 * (bid + ask)
        w = np.asarray(w, float)
        if self.w is None or len(self.w) != len(w) or not np.array_equal(self.w, w):
            self.w = w
        cash = np.asarray(cash, float)
        sb, sa = np.asarray(sf_bid, float), np.asarray(sf_ask, float)
        with np.errstate(invalid="ignore"):
            v = (cash > 0) & (np.asarray(cash_age, float) <= HW_FRESH_S) & (sb > 0) & (sa >= sb) \
                & (np.asarray(sf_age, float) <= HW_FRESH_S)
        sfm = 0.5 * (sb + sa)
        self.h.append((now_s, mid, cash, sfm, v, None))
        p = self.p
        old = self._ago(p["win_s"])
        if self.clean_s < WARM_S or old is None:
            for n in NAMES:
                self.why[n] = f"warming up ({int(self.clean_s)} of {WARM_S} s)"
            return
        m = v & old[4]
        tot = float(w.sum())
        cw = float(w[m].sum())
        self.cov = cw / tot if tot > 0 else 0.0
        if cw <= 0 or self.cov < p["cover"]:
            for n in NAMES:
                self.why[n] = f"only {self.cov:.0%} of heavyweight weight has fresh cash and futures"
            return
        rc = np.log(cash[m] / old[2][m]); rf = np.log(sfm[m] / old[3][m]); wm = w[m]
        cc = float((rc * wm).sum() / cw * mid); cs = float((rf * wm).sum() / cw * mid); cm = mid - old[1]
        b = float((np.sign(rc) * wm).sum() / cw); bf = float((np.sign(rf) * wm).sum() / cw)
        z = cs - p["s01_b_cash"] * cc - p["s01_b_mom"] * cm
        self.z, self.cc, self.cs, self.cm, self.b, self.bf = z, cc, cs, cm, b, bf
        self.h[-1] = (now_s, mid, cash, sfm, v, b)
        # S01
        d = 1 if z > 0 else -1
        c10 = None
        o10 = self._ago(10)
        if o10 is not None:
            m10 = v & o10[4]
            w10 = float(w[m10].sum())
            if w10 > 0:
                c10 = float((np.log(cash[m10] / o10[2][m10]) * w[m10]).sum() / w10 * mid)
        if abs(z) < p["s01_rearm"]:
            self.armed["s01_trans"] = True
        if abs(z) < p["s01_z"]:
            self.why["s01_trans"] = f"stock futures beyond cash and index: {z:+.1f} pts (needs {p['s01_z']:.0f})"
        elif not self.armed["s01_trans"]:
            self.why["s01_trans"] = "this transmission was already signalled"
        elif c10 is None or c10 * d <= p["s01_cash10_against"]:
            self.why["s01_trans"] = "the cash prices are not following the stock futures"
        elif cm * d > p["s01_idx_max"]:
            self.why["s01_trans"] = f"the index already moved {cm:+.1f} pts"
        else:
            self.armed["s01_trans"] = False
            self._emit("s01_trans", now_s, d, f"stock futures {cs:+.1f} pts, cash {cc:+.1f}, index {cm:+.1f} in "
                       f"{p['win_s']} s: {z:+.1f} pts not yet in cash or index; cash last 10 s {c10:+.1f}",
                       p["s01_tp"], p["s01_sl"], p["s01_hold"])
        for name, x, th, re, lab in (("s01_ctl_cash", cc, p["c_cash"], p["c_cash_rearm"], "cash basket"),
                                     ("s01_ctl_sfut", cs, p["c_sfut"], p["c_sfut_rearm"], "stock-futures basket")):
            if abs(x) < re:
                self.armed[name] = True
            if abs(x) >= th and self.armed[name]:
                self.armed[name] = False
                self._emit(name, now_s, 1 if x > 0 else -1, f"{lab} {x:+.1f} pts in {p['win_s']} s (control)",
                           p["s01_tp"], p["s01_sl"], p["s01_hold"])
            else:
                self.why[name] = f"{lab} {x:+.1f} pts (needs {th:.0f})"
        # S03
        d = 1 if b > 0 else -1
        b10, b20, b30 = (self._ago(s) for s in (10, 20, 30))
        if abs(b) < p["s03_rearm"]:
            self.armed["s03_recruit"] = True
        if abs(b) < p["s03_b"]:
            self.why["s03_recruit"] = f"breadth {b:+.2f} (needs {p['s03_b']:.2f})"
        elif not self.armed["s03_recruit"]:
            self.why["s03_recruit"] = "this recruitment was already signalled"
        elif any(q is None or q[5] is None for q in (b10, b20, b30)):
            self.why["s03_recruit"] = "no breadth path yet"
        elif (b - b30[5]) * d < p["s03_join"] or not (b * d >= b10[5] * d >= b20[5] * d):
            self.why["s03_recruit"] = f"breadth {b:+.2f} but weight is not joining steadily (30 s ago {b30[5]:+.2f})"
        elif bf * d < p["s03_fut_b"]:
            self.why["s03_recruit"] = f"the stock futures do not agree (breadth {bf:+.2f})"
        elif abs(cm) > p["s03_quiet_pts"]:
            self.why["s03_recruit"] = f"the index already moved {cm:+.1f} pts"
        else:
            self.armed["s03_recruit"] = False
            self._emit("s03_recruit", now_s, d, f"breadth {b30[5]:+.2f} to {b20[5]:+.2f} to {b10[5]:+.2f} to {b:+.2f} "
                       f"over 30 s, stock futures {bf:+.2f}, index {cm:+.1f} pts", p["s03_tp"], p["s03_sl"], p["s03_hold"])

    # ── thesis exits ─────────────────────────────────────────────────────────────────────────────────────────────────
    def ready(self, name):
        """May the model speak this second (same rule as gen2: never before the warm-up, never on a second with no
        valid measurement)? A held position keeps its bracket and clock regardless."""
        return self.clean_s >= WARM_S and self.z is not None and math.isfinite(self.z)

    def void(self, name, gx, d):
        if name not in ("s01_trans", "s03_recruit"):
            return None
        if self.clean_s >= WARM_S and self.cov is not None and self.cov < self.p["s01_cover_exit"] and name == "s01_trans":
            return f"COVERAGE (only {self.cov:.0%} of heavyweight weight is fresh)"
        if not self.ready(name):
            return None
        if name == "s01_trans" and self.z * d <= -self.p["s01_rev"]:
            return f"REVERSAL (stock futures now {self.z:+.1f} pts the other way)"
        if name == "s03_recruit" and self.b * d <= self.p["s03_rev"]:
            return f"RECRUITMENT REVERSED (breadth {self.b:+.2f})"
        return None
