"""9 Nov 2026 (docs/36, docs/37): the second-generation shadow books' shared signal engine.

Owner: "substantially different shadow books, rather than more variants of the existing books". Three independent
entry mechanisms that no existing book has (docs/37 novelty audit), each with its matched control:

  N01  liquidity absorption -> reversal ("n01_rev") and absorption -> release ("n01_rel", a separately frozen
       hypothesis). Signal: the futures' price RESPONSE to signed flow, against a causal response model
       dF_hat = beta * flow / depth. Controls: the same price confirmation alone ("ctl_price"), flow imbalance
       alone ("ctl_flow").
  N02  transient-impact relaxation ("n02_relax"). Two-timescale propagator (5-s and 30-s half-lives) fitted online;
       trade the measured decay of the transient part once new pressure has stopped. Control: ordinary 30-s
       mean reversion ("ctl_mr").
  N06  leadership transfer ("n06_lead"): heavyweight groups disagree while the index is still; the opposing group
       starts joining the leader. Control: breadth alone ("ctl_breadth").

What this is NOT: proof of anything. Every threshold below is frozen a priori on 9 Nov 2026 BEFORE any evaluation
(docs/36 proof package step 1) and has never been fitted to a tape. The flow is a PROXY: the tape carries ~0.7-s
snapshots with cumulative volume, not trades; a volume step is signed by the last price against the previous
bid / ask (tick rule inside the spread). Depth is the 5-level standing quantity; cancellations and replenishment
are not observable.

Causality: one update per market second from that second's snapshot; every model coefficient used at second t was
estimated from seconds < t; nothing is smoothed backwards. A data gap (> GAP_S between updates, or the engine's
blackout) clears the short windows and every open episode: nothing is stitched across a hole.

Bounded work: fixed-length deques, O(window) sums once a second, a 2x2 solve; no allocation growth over the day.
State is not saved: after a restart the models warm up again (WARM_S) and no signal fires until then; open positions
keep their own bracket in pos["gx"] (saved with the book).
"""
import math
from collections import deque

VERSION = 3            # 10 Nov (docs/38 O4, O5, O6): exit readiness, per-instrument freshness, depth tag, real-time decay;
                       # O6: N01 response fitted on the pressure window itself, two-sided absorption test, confirmation
                       # re-checks strength and sign, an independent price-only control, N02 fit diagnostics
GAP_S = 5.0            # a hole longer than this between two updates restarts the windows
WARM_S = 600           # seconds of clean data before any signal
Q_FRESH_S = 3.0        # the future's own quote older than this = a data gap for these models (whatever the feed says)
HW_FRESH_S = 5.0       # a heavyweight whose last packet is older than this has no valid price this second

# ── frozen parameters (9 Nov 2026, a priori; docs/37 manifest) ───────────────────────────────────────────────────────
P = {
    # shared
    "depth_hl_s": 60.0,          # EW half-life of the effective depth
    "beta_hl_s": 600.0,          # EW half-life of the response regression
    "resp_win_s": 10,            # regression window: 10-s flow sum against 10-s mid change
    "press_win_s": 60,           # pressure window
    # N01
    "n01_press_sd": 2.0,         # pressure >= this many of its own EW standard deviations
    "n01_clear_sd": 1.0,         # the episode resets only after pressure falls below this
    "n01_exp_min": 8.0,          # expected response of the pressure, points
    "n01_resp_max": 0.35,        # actual response <= this share of the expected one = absorbed
    "n01_resp_pass": 0.80,       # actual response >= this share = no absorption (normal impact)
    "n01_hold_s": 20,            # candidate must persist this long to be confirmed
    "n01_depth_keep": 0.80,      # absorbing side's depth >= this share of its 60-s mean
    "n01_depth_gone": 0.60,      # release: absorbing depth below this share of its level at confirmation
    "n01_rev_min": 3.0,          # reversal: mid this far off the episode extreme (or n01_rev_k of the expected move)
    "n01_rev_k": 0.25,
    "n01_brk": 2.0,              # release: mid this far beyond the absorption zone
    "n01_max_s": 300,            # a confirmed absorption with no outcome expires
    "n01_tp_k": 0.6, "n01_tp_lo": 8.0, "n01_tp_hi": 25.0,
    "n01_fail_pts": 2.0,         # thesis stop: beyond the episode extreme by this much
    "n01_sl": 10.0, "n01_hold": 600,
    # N01 controls
    "cp_drop": 8.0, "cp_rev": 3.0, "cp_recent_s": 30,
    # N02
    "n02_hl_fast": 5.0, "n02_hl_slow": 30.0, "n02_fit_hl_s": 900.0,
    "n02_i_min": 5.0,            # transient displacement, points
    "n02_i_left": 3.0,           # still present at entry
    "n02_decay": 0.80,           # confirmed decay: |I| <= this share of the episode peak
    "n02_quiet_sd": 0.5,         # new pressure has stopped: 10-s flow below this many sd (or opposite)
    "n02_px_rev": 1.0,           # the price has started back, points
    "n02_perm_k": 3.0,           # abstain when the 5-min move exceeds this multiple of the transient peak
    "n02_end": 1.5,              # the episode ends when |I| falls below this
    "n02_tp_k": 0.8, "n02_tp_lo": 4.0, "n02_tp_hi": 15.0,
    "n02_sl_k": 0.8, "n02_sl_lo": 5.0, "n02_sl_hi": 12.0,
    "n02_rebuild": 1.2,          # exit: the transient part rebuilds beyond this multiple of its peak
    "n02_hold": 180,
    # N02 control
    "mr_disp": 8.0, "mr_rev": 1.0, "mr_rearm": 3.0, "mr_tp": 8.0, "mr_sl": 8.0, "mr_hold": 180,
    # N06
    "n06_long_s": 120, "n06_short_s": 30, "n06_frag_s": 60,
    "n06_cover": 0.80,           # share of tracked weight with a valid price at both ends
    "n06_grp_w": 0.12,           # a group needs this share of the tracked weight
    "n06_lead_pct": 0.10,        # leader's 120-s return, per cent
    "n06_opp_pct": 0.04,         # opposer's 120-s return against the leader, per cent
    "n06_join_pct": 0.04,        # opposer's 30-s return WITH the leader = joining
    "n06_quiet_pts": 10.0,       # index 120-s displacement while the groups disagree
    "n06_span_pts": 15.0,        # index displacement since the disagreement began, at the transfer
    "n06_max_s": 240,            # a disagreement with no transfer expires
    "n06_frag_pct": 0.05,        # exit: the leader's 60-s return turns this far against the trade
    "n06_tp": 20.0, "n06_sl": 10.0, "n06_hold": 600,
    # N06 control
    "br_share": 0.70, "br_rearm": 0.55, "br_quiet_pts": 6.0, "br_win_s": 60,
    "ctl_tp": 12.0, "ctl_sl": 10.0, "ctl_hold": 300,
}
NAMES = ("n01_rev", "n01_rel", "ctl_price", "ctl_flow", "n02_relax", "ctl_mr", "n06_lead", "ctl_breadth", "ctl_price_ind")


def _ew(hl, dt=1.0):
    """EW decay over dt REAL seconds (10 Nov, O5: an update 3 s after the last one decays 3 s, not 1)."""
    return 0.5 ** (dt / hl)


class Gen2:
    def __init__(self, params=None):
        self.p = dict(P, **(params or {}))
        self.sig = {}                 # name -> the latest signal dict (valid for the second it carries)
        self.fired = {}               # (name, id) -> signal, for the books' exits
        self.why = {}                 # name -> why there is no signal (the dashboard / decision text)
        self.n_sig = {n: 0 for n in NAMES}
        self.sgn_v = [0.0] * 6        # 10 Nov (photo item 109): EW volume signed outside the spread / by tick / unsigned,
        #                               60-s then 300-s half-life. Never read by a signal
        self._reset(full=True)

    # ── state ────────────────────────────────────────────────────────────────────────────────────────────────────────
    def _reset(self, full=False):
        n = 900
        was_warm = (not full) and getattr(self, "clean_s", 0) >= WARM_S
        self.t = deque(maxlen=n); self.mid = deque(maxlen=n); self.x = deque(maxlen=n)
        self.bd = deque(maxlen=n); self.ad = deque(maxlen=n)
        self.prev = None              # (t, bid, ask, ltp, ttq)
        self.depth_lvl = None         # 5 = five-level depth, 1 = best level only (two different scales, never mixed)
        self.clean_s = (WARM_S - 300) if was_warm else 0   # after a gap the windows (<= 300 s) refill; the fits are kept
        self.e1 = None                # N01 episode
        self.i2 = None                # N02 episode
        self.z1 = self.z2 = 0.0
        self.e6 = None                # N06 episode
        self.hw = deque(maxlen=330)   # (t, price vector)
        self.cp_last = None; self.cp2_last = None; self.cf_armed = True; self.mr = None; self.br_armed = True
        if full:
            self.last_sec = None
            self.depth = None
            self.depth_by = {}        # the EW effective depth, one per depth scale
            self.lvl_t = -1e18        # when the depth scale last changed
            self.hw_fresh = None      # share of heavyweight weight with a fresh price this second
            self.sxx = self.sxy = self.srr = 0.0; self.beta = None; self.n_fit = 0
            self.sxx60 = self.sxy60 = self.srr60 = 0.0; self.beta60 = None; self.n_fit60 = 0   # O6: the 60-s response
            self.n02_cond = None; self.n02_se = None; self.n02_s2 = 0.0; self.a_raw = None    # O6: N02 fit diagnostics
            self.a_m = self.a_v = 0.0
            self.p_m = self.p_v = 0.0; self.x10_v = 0.0; self.n_p = 0
            self.A = [[0.0, 0.0], [0.0, 0.0]]; self.b = [0.0, 0.0]; self.a = None; self.r2 = 0.0
            self.gaps = 0
            self.hw_w = self.hw_g = None

    @property
    def warm(self):
        return self.clean_s >= WARM_S and self.beta is not None

    def sign_view(self):
        """Shares of recent futures volume by how its side was decided (photo item 109), or None with no volume."""
        sv = self.sgn_v
        a, b = sv[0] + sv[1] + sv[2], sv[3] + sv[4] + sv[5]
        if a <= 0 or b <= 0:
            return None
        return {"sign_out_share60": sv[0] / a, "sign_tick_share60": sv[1] / a, "sign_none_share60": sv[2] / a,
                "sign_out_share300": sv[3] / b, "sign_none_share300": sv[5] / b}

    def view(self):
        """For the dashboard and the tests: the models' current numbers (no decision reads this)."""
        e, i, l = self.e1, self.i2, self.e6
        return {"v": VERSION, "warm": self.warm, "clean_s": self.clean_s, "beta": self.beta, "a": self.a,
                "beta60": self.beta60, "beta60_resid_sd": math.sqrt(self.srr60) if self.srr60 > 0 else None,
                "n_fit60": self.n_fit60, "a_raw": self.a_raw, "n02_cond": self.n02_cond, "n02_se": self.n02_se,
                "n02_sum_sd": math.sqrt(self.a_v) if self.a_v > 0 else None,
                "depth": self.depth, "depth_lvl": self.depth_lvl, "hw_fresh": self.hw_fresh,
                "ready": {n: self.ready(n) for n in ("n02_relax", "n06_lead")},
                "gaps": self.gaps, "n_sig": dict(self.n_sig),
                "n01": e and {k: e[k] for k in ("state", "side", "t0", "exp", "zone")},
                "n02": i and {k: i[k] for k in ("sign", "peak")}, "impact": self.impact(),
                "n06": l and {k: l[k] for k in ("lead", "opp", "dir", "t0")}}

    # ── helpers ──────────────────────────────────────────────────────────────────────────────────────────────────────
    def _ago(self, s):
        """Index of the newest sample at least s seconds old, or None (bounded linear walk from the end)."""
        t, now = self.t, self.t[-1]
        for k in range(len(t) - 1, -1, -1):
            if now - t[k] >= s - 1e-9:
                return k
        return None

    def _sum_x(self, s):
        now, tot = self.t[-1], 0.0
        for k in range(len(self.t) - 1, -1, -1):
            if now - self.t[k] >= s - 1e-9:
                break
            tot += self.x[k]
        return tot

    def impact(self):
        return None if self.a is None else self.a[0] * self.z1 + self.a[1] * self.z2

    def _emit(self, name, now, d, why, tp, sl, hold, **aux):
        s = {"name": name, "id": int(now), "t": now, "dir": int(d), "why": why, "tp": round(float(tp), 2),
             "sl": round(float(sl), 2), "hold": int(hold), "ep": "G2-" + name.upper().replace("_", "-")}
        s.update(aux)
        self.sig[name] = s
        self.fired[(name, s["id"])] = s
        self.n_sig[name] += 1
        if len(self.fired) > 4000:                       # bounded: a day never comes near this
            for k in sorted(self.fired, key=lambda q: q[1])[:2000]:
                del self.fired[k]

    # ── the per-second update ────────────────────────────────────────────────────────────────────────────────────────
    def update(self, now_s, bid, ask, ltp, ttq, bid_depth, ask_depth, hw_px=None, hw_w=None, hw_g=None, ok=True,
               q_age=None, depth_lvl=5, hw_age=None):
        """One market second. bid / ask / ltp / ttq: the Nifty future's quote; *_depth: its standing 5-level quantity;
        hw_*: the heavyweights' last prices, index weights and group labels. ok=False: the engine's data blackout.
        10 Nov (O5): q_age = seconds since the future's last packet (older than Q_FRESH_S = a gap); depth_lvl = 5 or 1,
        which depth the two quantities are; hw_age = seconds since each heavyweight's last packet (a stale one has no
        price this second, so it is invalid at whichever end of a return window it falls)."""
        sec = int(now_s)
        if self.last_sec is not None and sec <= self.last_sec:
            return
        gap = self.last_sec is not None and (now_s - self.t[-1] > GAP_S if self.t else False)
        self.last_sec = sec
        vals = (bid, ask, ltp, ttq, bid_depth, ask_depth)
        bad = (not ok) or any(v is None or not math.isfinite(v) for v in vals) or bid <= 0 or ask <= 0 or ask < bid
        bad = bad or (q_age is not None and not (q_age <= Q_FRESH_S))
        if bad or gap:
            if self.t or self.prev:
                self.gaps += 1
            self._reset()
            if bad:
                for n in NAMES:
                    self.why[n] = "data gap: windows restarted"
                return
        mid = 0.5 * (bid + ask)
        pv = self.prev
        self.prev = (now_s, bid, ask, ltp, ttq)
        if pv is None:
            self.t.append(now_s); self.mid.append(mid); self.x.append(0.0); self.bd.append(bid_depth); self.ad.append(ask_depth)
            return
        dt = min(max(now_s - pv[0], 1e-3), GAP_S)          # real seconds since the last accepted update
        if self.depth_lvl is not None and depth_lvl != self.depth_lvl:
            self.lvl_t = now_s                             # the depth scale changed: an N01 episode measured on the
            self.e1 = None                                 # other scale is dropped, never compared across the two
        self.depth_lvl = depth_lvl
        self.depth = self.depth_by.get(depth_lvl)
        dq = ttq - pv[4]
        if dq < 0 or dq > 1e9:
            dq = 0.0
        sgn = 1 if ltp >= pv[2] else (-1 if ltp <= pv[1] else (1 if ltp > pv[3] else (-1 if ltp < pv[3] else 0)))
        cls = 0 if (ltp >= pv[2] or ltp <= pv[1]) else (1 if ltp != pv[3] else 2)   # at/through the quote, tick rule, none
        k60, k300, sv = _ew(60.0, dt), _ew(300.0, dt), self.sgn_v
        for q in range(3):
            sv[q] *= k60; sv[3 + q] *= k300
        sv[cls] += dq; sv[3 + cls] += dq
        dep = 0.5 * (bid_depth + ask_depth)
        if dep > 0:
            k = _ew(self.p["depth_hl_s"], dt)
            self.depth = dep if self.depth is None else k * self.depth + (1 - k) * dep
            self.depth_by[depth_lvl] = self.depth
        x = sgn * dq / self.depth if self.depth else 0.0
        z1p, z2p = self.z1, self.z2
        self.z1 = _ew(self.p["n02_hl_fast"], dt) * self.z1 + x
        self.z2 = _ew(self.p["n02_hl_slow"], dt) * self.z2 + x
        d_mid = mid - self.mid[-1]
        self.t.append(now_s); self.mid.append(mid); self.x.append(x); self.bd.append(bid_depth); self.ad.append(ask_depth)
        self.clean_s += dt if dt != 1.0 else 1
        for n in NAMES:
            self.why[n] = "no setup" if self.warm else f"warming ({self.clean_s:.0f}/{WARM_S} s)"
        beta, a, beta60 = self.beta, self.a, self.beta60  # the coefficients known BEFORE this second
        w = self.p["resp_win_s"]
        j = self._ago(w)
        x10 = self._sum_x(w)
        p60 = self._sum_x(self.p["press_win_s"])
        j60 = self._ago(self.p["press_win_s"])
        if self.clean_s >= WARM_S and j60 is not None:
            # O6: the INDEPENDENT price-only control never looks at the flow model: it runs whether or not a
            # response coefficient exists. "ctl_price" below stays the matched control (same gate as N01)
            self._ctl_px(now_s, mid, j60, "ctl_price_ind", "cp2_last")
            # O6: the expected response of 60-s pressure comes from a fit of 60-s pressure against the 60-s move
            # (version 2 applied a coefficient fitted on 10-s windows to 60-s pressure). An open episode keeps the
            # coefficient it formed with: the absorbed seconds themselves pull the running fit towards zero
            if beta60 is not None or self.e1 is not None:
                self._n01(now_s, mid, p60, x10, self.mid[j60], beta60)
            if beta60 is not None:
                self._controls_1(now_s, mid, p60, j60)
        if a is not None and self.clean_s >= WARM_S:
            self._n02(now_s, mid, x10, a)
        if self.clean_s >= WARM_S:
            self._ctl_mr(now_s, mid)
        if hw_px is not None:
            self._hw(now_s, mid, hw_px, hw_w, hw_g, hw_age)
        # ── learn from this second (used from the next one) ──
        if j is not None:
            kb = _ew(self.p["beta_hl_s"], dt)
            d10 = mid - self.mid[j]
            self.sxx = kb * self.sxx + x10 * x10
            self.sxy = kb * self.sxy + x10 * d10
            if self.sxx > 1e-12:
                b = self.sxy / self.sxx
                self.srr = kb * self.srr + (1 - kb) * (d10 - b * x10) ** 2
                self.n_fit += 1
                self.beta = b if (b > 0 and self.n_fit >= 120) else None   # a non-positive response: the proxy explains
            kx = _ew(600.0, dt)                                            # nothing, so no flow book may read it
            self.x10_v = kx * self.x10_v + (1 - kx) * x10 * x10
        if j60 is not None:
            kb = _ew(self.p["beta_hl_s"], dt)
            d60 = mid - self.mid[j60]
            self.sxx60 = kb * self.sxx60 + p60 * p60
            self.sxy60 = kb * self.sxy60 + p60 * d60
            if self.sxx60 > 1e-12:
                b60 = self.sxy60 / self.sxx60
                self.srr60 = kb * self.srr60 + (1 - kb) * (d60 - b60 * p60) ** 2
                self.n_fit60 += 1
                self.beta60 = b60 if (b60 > 0 and self.n_fit60 >= 300) else None
            kp = _ew(900.0, dt)
            self.p_m = kp * self.p_m + (1 - kp) * p60
            self.p_v = kp * self.p_v + (1 - kp) * (p60 - self.p_m) ** 2
            self.n_p += 1
        kf = _ew(self.p["n02_fit_hl_s"], dt)
        u1, u2 = self.z1 - z1p, self.z2 - z2p
        A, bv = self.A, self.b
        A[0][0] = kf * A[0][0] + u1 * u1; A[0][1] = kf * A[0][1] + u1 * u2; A[1][1] = kf * A[1][1] + u2 * u2
        bv[0] = kf * bv[0] + u1 * d_mid; bv[1] = kf * bv[1] + u2 * d_mid
        rg = 1e-6 * (A[0][0] + A[1][1]) + 1e-12
        det = (A[0][0] + rg) * (A[1][1] + rg) - A[0][1] * A[0][1]
        if det > 1e-18 and self.clean_s >= 120:
            a1 = (bv[0] * (A[1][1] + rg) - bv[1] * A[0][1]) / det
            a2 = (bv[1] * (A[0][0] + rg) - bv[0] * A[0][1]) / det
            self.a = (a1, a2) if (a1 + a2) > 0 else None     # the summed response must be positive to mean anything
            # O6 diagnostics (no decision reads them): the unconstrained pair, the conditioning of the 2x2 system,
            # the coefficients' standard errors and how much their sum has been moving
            self.a_raw = (a1, a2)
            tr = A[0][0] + A[1][1] + 2 * rg
            disc = math.sqrt(max(tr * tr - 4 * det, 0.0))
            self.n02_cond = (tr + disc) / max(tr - disc, 1e-300)
            self.n02_s2 = kf * self.n02_s2 + (1 - kf) * (d_mid - a1 * u1 - a2 * u2) ** 2
            self.n02_se = (math.sqrt(max(self.n02_s2 * (A[1][1] + rg) / det, 0.0)),
                           math.sqrt(max(self.n02_s2 * (A[0][0] + rg) / det, 0.0)))
            ks = _ew(300.0, dt)
            self.a_m = ks * self.a_m + (1 - ks) * (a1 + a2)
            self.a_v = ks * self.a_v + (1 - ks) * (a1 + a2 - self.a_m) ** 2
        else:
            self.a = None; self.a_raw = None; self.n02_cond = None; self.n02_se = None

    # ── N01: absorption -> reversal / release ────────────────────────────────────────────────────────────────────────
    def _n01(self, now, mid, p60, x10, mid60, beta):
        p = self.p
        sd = math.sqrt(self.p_v) if self.p_v > 0 else 0.0
        if sd <= 0 or self.n_p < 300:
            self.why["n01_rev"] = self.why["n01_rel"] = "pressure scale warming"
            return
        if now - self.lvl_t < p["press_win_s"]:           # O5: 5-level and best-level depth are different scales
            self.e1 = None
            self.why["n01_rev"] = self.why["n01_rel"] = "depth scale changed (5-level / best level): 60 s of one scale first"
            return
        e = self.e1
        z = (p60 - self.p_m) / sd
        if e is not None and e.get("beta"):
            beta = e["beta"]                              # O6: the response known when the episode formed
        if beta is None:
            return
        exp = beta * p60                                  # the response this pressure would normally have, points
        act = mid - mid60
        if e is None:
            if abs(z) >= p["n01_press_sd"] and abs(exp) >= p["n01_exp_min"]:
                side = 1 if p60 > 0 else -1
                if abs(act) <= p["n01_resp_max"] * abs(exp):     # O6: absorbed = the price barely moved EITHER way
                    self.e1 = {"state": "cand", "side": side, "t0": now, "exp": exp, "zone": mid, "zc": None, "beta": beta,
                               "t_conf": None, "dep_conf": None}
            return
        side = e["side"]
        if e["state"] == "spent":
            if abs(z) < p["n01_clear_sd"]:
                self.e1 = None                            # the pressure has cleared: a new episode may form
            else:
                self.why["n01_rev"] = self.why["n01_rel"] = "episode used; waiting for the pressure to clear"
            return
        if abs(exp) > abs(e["exp"]) and exp * side > 0:
            e["exp"] = exp
        j = self._ago(p["press_win_s"])
        hist = list(self.ad if side > 0 else self.bd)[j:] if j is not None else []
        dep_now = (self.ad if side > 0 else self.bd)[-1]                      # buying is absorbed by the ASK side
        dep_mean = sum(hist) / len(hist) if hist else 0.0
        if e["state"] == "cand":
            if act * side >= p["n01_resp_pass"] * abs(exp) and abs(exp) >= p["n01_exp_min"]:
                e["state"] = "spent"                      # the price did respond: no absorption
                return
            if z * side < p["n01_clear_sd"]:               # O6: signed. Pressure of the OTHER sign ends the candidate
                self.e1 = None
                return
            e["zone"] = max(e["zone"], mid) if side > 0 else min(e["zone"], mid)   # how far the push got
            # O6: at confirmation the pressure must still have its original strength and sign, and the price must
            # still be absorbed against the response expected NOW (version 2 checked neither)
            still = z * side >= p["n01_press_sd"] and exp * side >= p["n01_exp_min"] \
                and abs(act) <= p["n01_resp_max"] * abs(exp)
            if still and now - e["t0"] >= p["n01_hold_s"] and dep_mean > 0 and dep_now >= p["n01_depth_keep"] * dep_mean:
                e["state"], e["t_conf"], e["dep_conf"], e["zc"] = "conf", now, dep_now, e["zone"]
            self.why["n01_rev"] = self.why["n01_rel"] = f"absorption candidate ({'buying' if side > 0 else 'selling'} pressure)"
            return
        # confirmed
        if now - e["t_conf"] > p["n01_max_s"]:
            e["state"] = "spent"
            return
        x_sd = math.sqrt(self.x10_v) if self.x10_v > 0 else 0.0
        stopped = x10 * side <= p["n02_quiet_sd"] * x_sd
        rev = max(p["n01_rev_min"], p["n01_rev_k"] * abs(e["exp"]))
        tp = min(max(p["n01_tp_k"] * abs(e["exp"]), p["n01_tp_lo"]), p["n01_tp_hi"])
        if (e["zone"] - mid) * side >= rev and stopped:
            # the absorbed push has given way: price is `rev` points back from where the push got to
            self._emit("n01_rev", now, -side, f"{'buying' if side > 0 else 'selling'} pressure absorbed "
                       f"(expected {e['exp']:+.1f} pts, got {mid - mid60:+.1f}); price turned {rev:.1f} pts",
                       tp, p["n01_sl"], p["n01_hold"], stop_px=e["zone"] + side * p["n01_fail_pts"], exp=round(e["exp"], 2))
            e["state"] = "spent"
            return
        if (mid - e["zc"]) * side >= p["n01_brk"] and e["dep_conf"] and dep_now <= p["n01_depth_gone"] * e["dep_conf"]:
            self._emit("n01_rel", now, side, f"absorbing {'offers' if side > 0 else 'bids'} gave way "
                       f"({dep_now:.0f} vs {e['dep_conf']:.0f}); price {p['n01_brk']:.0f} pts through the zone",
                       tp, p["n01_sl"], p["n01_hold"], stop_px=e["zc"] - side * p["n01_fail_pts"], exp=round(e["exp"], 2))
            e["state"] = "spent"
            return
        e["zone"] = max(e["zone"], mid) if side > 0 else min(e["zone"], mid)
        self.why["n01_rev"] = self.why["n01_rel"] = "absorption confirmed; waiting for the turn or the release"

    def _ctl_px(self, now, mid, j60, name, attr):
        """The price confirmation alone: a 60-s move then a turn. One rule, two books: "ctl_price" runs only where N01
        can run (matched), "ctl_price_ind" runs on price alone (independent of the flow model; docs/38 O6)."""
        p = self.p
        seg = list(self.mid)[j60:]
        ts = list(self.t)[j60:]
        for d in (1, -1):                                 # d = +1: a fall then a turn up (buy CE)
            ext = min(seg) if d > 0 else max(seg)
            k = seg.index(ext)
            if (seg[0] - ext) * d >= p["cp_drop"] and (mid - ext) * d >= p["cp_rev"] and now - ts[k] <= p["cp_recent_s"] \
                    and getattr(self, attr) != (d, int(ts[k])):
                setattr(self, attr, (d, int(ts[k])))
                self._emit(name, now, d, f"60-s move {ext - seg[0]:+.1f} then {p['cp_rev']:.0f}-pt turn (price only)",
                           p["ctl_tp"], p["ctl_sl"], p["ctl_hold"])

    def _controls_1(self, now, mid, p60, j60):
        p = self.p
        self._ctl_px(now, mid, j60, "ctl_price", "cp_last")
        sd = math.sqrt(self.p_v) if self.p_v > 0 else 0.0
        if sd > 0 and self.n_p >= 300:
            z = (p60 - self.p_m) / sd
            if self.cf_armed and abs(z) >= p["n01_press_sd"]:
                self.cf_armed = False
                self._emit("ctl_flow", now, 1 if z > 0 else -1, f"60-s flow imbalance {z:+.1f} sd (flow only)",
                           p["ctl_tp"], p["ctl_sl"], p["ctl_hold"])
            elif abs(z) < p["n01_clear_sd"]:
                self.cf_armed = True

    # ── N02: transient-impact relaxation ─────────────────────────────────────────────────────────────────────────────
    def _n02(self, now, mid, x10, a):
        p = self.p
        I = a[0] * self.z1 + a[1] * self.z2               # the transient displacement still in the price, points
        e = self.i2
        if e is None:
            if abs(I) >= p["n02_i_min"]:
                self.i2 = {"sign": 1 if I > 0 else -1, "peak": abs(I), "ext": mid, "done": False}
            return
        s = e["sign"]
        if I * s < p["n02_end"]:
            self.i2 = None                                # the displacement has gone: the episode is over
            return
        e["peak"] = max(e["peak"], abs(I))
        e["ext"] = max(e["ext"], mid) if s > 0 else min(e["ext"], mid)
        if e["done"]:
            self.why["n02_relax"] = "episode used"
            return
        x_sd = math.sqrt(self.x10_v) if self.x10_v > 0 else 0.0
        j5 = self._ago(300)
        if abs(I) > p["n02_decay"] * e["peak"]:
            self.why["n02_relax"] = f"displacement {I:+.1f} pts still building"
        elif abs(I) < p["n02_i_left"]:
            self.why["n02_relax"] = "too little displacement left"
        elif not (x10 * s <= p["n02_quiet_sd"] * x_sd):
            self.why["n02_relax"] = "pressure has not stopped"
        elif (e["ext"] - mid) * s < p["n02_px_rev"]:
            self.why["n02_relax"] = "price has not started back"
        elif j5 is None or abs(mid - self.mid[j5]) > p["n02_perm_k"] * e["peak"]:
            self.why["n02_relax"] = "5-min move dominates: read as a lasting repricing"
        else:
            e["done"] = True
            tp = min(max(p["n02_tp_k"] * abs(I), p["n02_tp_lo"]), p["n02_tp_hi"])
            sl = min(max(p["n02_sl_k"] * e["peak"], p["n02_sl_lo"]), p["n02_sl_hi"])
            self._emit("n02_relax", now, -s, f"transient displacement {I:+.1f} pts (peak {s * e['peak']:+.1f}) decaying, "
                       f"flow stopped", tp, sl, p["n02_hold"], i_sign=s, i_peak=round(e["peak"], 2), i_in=round(I, 2),
                       a=a, cond=self.n02_cond, se=self.n02_se)

    def _ctl_mr(self, now, mid):
        p = self.p
        j = self._ago(30)
        if j is None:
            return
        disp = mid - self.mid[j]
        m = self.mr
        if m is None:
            if abs(disp) >= p["mr_disp"]:
                self.mr = {"s": 1 if disp > 0 else -1, "ext": mid, "done": False}
            return
        m["ext"] = max(m["ext"], mid) if m["s"] > 0 else min(m["ext"], mid)
        if abs(disp) < p["mr_rearm"]:
            self.mr = None
            return
        if not m["done"] and (m["ext"] - mid) * m["s"] >= p["mr_rev"]:
            m["done"] = True
            self._emit("ctl_mr", now, -m["s"], f"30-s move {disp:+.1f} pts, 1-pt turn (plain mean reversion)",
                       p["mr_tp"], p["mr_sl"], p["mr_hold"])

    # ── N06: leadership transfer ─────────────────────────────────────────────────────────────────────────────────────
    def _hw_ret(self, s):
        """Per-stock return (per cent) over s seconds and the validity mask, or None."""
        hw = self.hw
        now = hw[-1][0]
        old = None
        for k in range(len(hw) - 1, -1, -1):
            if now - hw[k][0] >= s - 1e-9:
                old = hw[k][1]
                break
        if old is None:
            return None
        cur = hw[-1][1]
        return [(100.0 * (c / o - 1.0)) if (o and c and o > 0 and c > 0 and math.isfinite(o) and math.isfinite(c)) else None
                for c, o in zip(cur, old)]

    def group_ret(self, g, s, cover=None):
        """Weighted mean return (per cent) of group g over s seconds, or None. cover: the share of the group's weight
        that must have a fresh price at BOTH ends of the window (None = any)."""
        r = self._hw_ret(s) if self.hw else None
        if r is None or self.hw_w is None or self.hw_g is None:
            return None
        num = den = tot = 0.0
        for ri, wi, gi in zip(r, self.hw_w, self.hw_g):
            if gi == g:
                tot += wi
                if ri is not None:
                    num += wi * ri; den += wi
        if den <= 0 or (cover is not None and den < cover * tot):
            return None
        return num / den

    def _hw(self, now, mid, px, w, g, age=None):
        p = self.p
        if w is not None:
            self.hw_w = [float(v) for v in w]
        if g is not None:
            self.hw_g = [str(v) for v in g]
        row = [float(v) for v in px]
        if age is not None:                               # O5: a stale stock has no price this second
            row = [v if (a is not None and a == a and a <= HW_FRESH_S) else float("nan") for v, a in zip(row, age)]
        self.hw.append((now, row))
        if self.hw_w is not None and len(self.hw_w) == len(row):
            wt = sum(self.hw_w)
            self.hw_fresh = (sum(wi for v, wi in zip(row, self.hw_w) if v == v and v > 0) / wt) if wt > 0 else None
        if self.hw_w is None or self.hw_g is None or len(self.hw_w) != len(px) or self.clean_s < WARM_S:
            return
        rl, rs = self._hw_ret(p["n06_long_s"]), self._hw_ret(p["n06_short_s"])
        jl = self._ago(p["n06_long_s"])
        if rl is None or rs is None or jl is None:
            return
        wt = sum(self.hw_w)
        cov = sum(wi for ri, wi in zip(rl, self.hw_w) if ri is not None) / wt if wt > 0 else 0.0
        if cov < p["n06_cover"]:
            self.why["n06_lead"] = self.why["ctl_breadth"] = f"heavyweight coverage {cov:.0%}"
            self.e6 = None
            return
        G = {}
        for ri, si, wi, gi in zip(rl, rs, self.hw_w, self.hw_g):
            if ri is None or si is None:
                continue
            a = G.setdefault(gi, [0.0, 0.0, 0.0])
            a[0] += wi; a[1] += wi * ri; a[2] += wi * si
        G = {k: (v[0] / wt, v[1] / v[0], v[2] / v[0]) for k, v in G.items() if v[0] / wt >= p["n06_grp_w"]}
        self._ctl_breadth(now, mid)
        e = self.e6
        if e is None:
            if len(G) < 2 or abs(mid - self.mid[jl]) > p["n06_quiet_pts"]:
                return
            lead = max(G, key=lambda k: abs(G[k][0] * G[k][1]))
            if abs(G[lead][1]) < p["n06_lead_pct"]:
                return
            d = 1 if G[lead][1] > 0 else -1
            opp = [k for k in G if k != lead and G[k][1] * d <= -p["n06_opp_pct"]]
            if not opp:
                return
            o = max(opp, key=lambda k: G[k][0])
            self.e6 = {"lead": lead, "opp": o, "dir": d, "t0": now, "mid0": mid, "state": "split"}
            return
        if e["state"] == "spent":
            lead_ok = e["lead"] in G and e["opp"] in G and G[e["opp"]][1] * e["dir"] <= -p["n06_opp_pct"]
            if not lead_ok:
                self.e6 = None                            # the disagreement is over: a new one may form
            return
        if now - e["t0"] > p["n06_max_s"] or e["lead"] not in G or e["opp"] not in G:
            e["state"] = "spent"
            return
        d = e["dir"]
        if G[e["lead"]][2] * d < -p["n06_opp_pct"]:       # the leader itself has turned: no transfer to trade
            e["state"] = "spent"
            return
        j30 = self._ago(p["n06_short_s"])
        self.why["n06_lead"] = f"{e['lead']} leads {'up' if d > 0 else 'down'}, {e['opp']} against; waiting for it to join"
        if G[e["opp"]][2] * d >= p["n06_join_pct"] and G[e["lead"]][2] * d >= 0 and abs(mid - e["mid0"]) <= p["n06_span_pts"] \
                and j30 is not None and (mid - self.mid[j30]) * d >= 0:
            e["state"] = "spent"
            self._emit("n06_lead", now, d, f"{e['lead']} led {'up' if d > 0 else 'down'} ({G[e['lead']][1]:+.2f} %), "
                       f"{e['opp']} was against and is joining ({G[e['opp']][2]:+.2f} % in {p['n06_short_s']} s); "
                       f"index moved {mid - e['mid0']:+.1f} pts", p["n06_tp"], p["n06_sl"], p["n06_hold"], lead=e["lead"])

    def _ctl_breadth(self, now, mid):
        p = self.p
        r = self._hw_ret(p["br_win_s"])
        j = self._ago(p["br_win_s"])
        if r is None or j is None:
            return
        up = sum(wi for ri, wi in zip(r, self.hw_w) if ri is not None and ri > 0)
        dn = sum(wi for ri, wi in zip(r, self.hw_w) if ri is not None and ri < 0)
        tot = sum(wi for ri, wi in zip(r, self.hw_w) if ri is not None)
        if tot <= 0:
            return
        share, d = (up / tot, 1) if up >= dn else (dn / tot, -1)
        if self.br_armed and share >= p["br_share"] and abs(mid - self.mid[j]) <= p["br_quiet_pts"]:
            self.br_armed = False
            self._emit("ctl_breadth", now, d, f"{share:.0%} of heavyweight weight {'up' if d > 0 else 'down'} over "
                       f"{p['br_win_s']} s, index still (breadth only)", p["ctl_tp"], p["ctl_sl"], p["ctl_hold"])
        elif share < p["br_rearm"]:
            self.br_armed = True

    # ── thesis exits (the books' check_exit asks; None = the thesis still stands) ────────────────────────────────────
    def ready(self, name):
        """10 Nov (docs/38 O4): may this mechanism's model speak (an entry or a model-driven exit)? Each mechanism has
        its own test; none speaks before WARM_S seconds of clean data, exactly as for entries. After a restart or a
        data gap a held position therefore keeps its bracket, its thesis price and its clock (all stored on the
        position at the fill) and gets no model exit until the model is ready again."""
        if self.clean_s < WARM_S:
            return False
        if name == "n02_relax":
            return self.a is not None
        if name == "n06_lead":
            return bool(self.hw) and self.hw_w is not None and self.hw_g is not None \
                and self.hw[-1][0] - self.hw[0][0] >= self.p["n06_frag_s"] - 1e-9
        return False

    def void(self, name, gx, d):
        if not self.ready(name):
            return None
        if name == "n02_relax" and gx.get("i_sign"):
            I = self.impact()
            if I is not None and I * gx["i_sign"] >= self.p["n02_rebuild"] * (gx.get("i_peak") or 9e9):
                return f"REBUILD (transient impact {I:+.1f} pts, beyond its {gx['i_peak']:.1f}-pt peak)"
        if name == "n06_lead" and gx.get("lead"):
            r = self.group_ret(gx["lead"], self.p["n06_frag_s"], cover=self.p["n06_cover"])
            if r is not None and r * d <= -self.p["n06_frag_pct"]:
                return f"FRAGMENT ({gx['lead']} {r:+.2f} % in {self.p['n06_frag_s']} s, against the trade)"
        return None
