"""Premium continuation (owner's PREMIUM_CONTINUATION_ENGINE_SPEC.md, 29 Oct 2026: buy only when the premium is about
to KEEP moving, not break down or fade).

Per side, on the ATM CE and the ATM PE (mid quotes, 1-Hz history), five hard yes/no conditions -- never a score:
  HH     premium's last-60-s high > its high 60-180 s ago (+0.5 %) and it sits within 3 % of its 3-min high
  delta  |delta| up >= 0.02 over 3 min
  vol    traded qty (delta ttq) in the last 60 s >= the strike's median 1-min volume of the last 15 min
  IV     IV not collapsing: change over 3 min >= -0.5 vol pts
  spot   Nifty followed: in the side's direction over 3 min by >= 5 pts AND >= 40 % of its 15-min high-low range

States: CONTINUATION CE/PE (all five pass and premium >= +3 % in 3 min), EXHAUSTING CE/PE (premium >= +3 % in 3 min
and still making highs with spot following, but volume or IV fails), BREAKING DOWN CE/PE (a side shown as
CONTINUATION/EXHAUSTING had run >= 5 % off its 3-min low and is now >= 4 % off its 3-min high AND has given back half
of that run; held 2-5 min), NONE. Other states
are held >= 60 s unless a breakdown cuts in. The strike is locked while a side is shown (no jump when ATM moves).
A new state must show on 3 checks in a row (15 s) from NONE, 2 checks otherwise, before the card flips.
Value = the shown side's premium % move over 3 min."""
import math

import numpy as np

NAME = "continuation"
TITLE = "Premium continuation (PCE)"
IDEA = ("Is the ATM premium move going to continue or break down? Higher highs, rising delta, volume, IV holding, "
        "spot following -- each a hard yes/no.")
VERDICT = ("R3 29 Oct: PCE vetoes V1-V4, V6 failed on the champion's pullback entries; only 'required move > 15-min "
           "range' survived (now in champion). Shown for watching.")
EVERY_S = 5

WIN = 180          # s, the 1-3 min window
RISE = 3.0         # % premium move in 3 min to call it a move
BRK_RUN = 5.0      # % run off the 3-min low before a breakdown can be called
BRK_OFF = 4.0      # % off the 3-min high = breaking down
EXH_FRESH = 5.0    # % 3-min move needed to show EXHAUSTING straight from NONE
GIVE_BACK = 0.5    # breaking down = also gave back >= half of the 3-min run
BRK_HOLD = 120     # s a BREAKING DOWN state is held
BRK_MAX = 300      # s ... and dropped to NONE after this unless a fresh move starts
SPOT_MIN = 5.0     # Nifty pts the spot must follow over 3 min
SPOT_SHARE = 0.4   # ... and this share of the 15-min spot range
MIN_DWELL = 60     # s any other state is held (a breakdown may still cut in)
PERSIST = 3        # consecutive checks before a flip
ALERT_MOVE = 10.0  # alert on entering CONTINUATION with >= 10 % in 3 min ...
ALERT_GAP = 1200   # ... at most once per 20 min
_AGOS = np.array([float(a) for a in range(0, 901, 60)] + [float(WIN)])


def _fin(x):
    return x is not None and x == x and x not in (math.inf, -math.inf)


def _side(env, rr, ds, strike=None, need=5.0):
    """-> dict of conditions for the ATM option of one side, or None if the data is too thin."""
    k = env.atm if strike is None else strike
    key = (k, rr)
    h = env.hist
    tab = h.table(key)
    if tab is None or h.now is None or len(tab) < 120:
        return None
    tab = tab[-1000:]                               # 1 Hz: ~16 min, enough for the 15-min volume median
    TT = np.ascontiguousarray(tab[:, 0])
    nowt = h.now

    # one vectorised lookup: rows at now - [0, 60, ..., 900] s and now - WIN
    agos = _AGOS
    J = np.searchsorted(TT, nowt - agos, side="right") - 1
    J = np.where(J >= 0, J, -1)
    R = np.where((J >= 0)[:, None], tab[np.maximum(J, 0)], np.nan)     # (len(agos), ncol)

    j0 = int(np.searchsorted(TT, nowt - WIN - 5, side="left"))
    T, M = TT[j0:], tab[j0:, 4]
    ok = np.isfinite(M) & (M > 0)
    if ok.sum() < 120:
        return None
    T, M = T[ok], M[ok]
    if T[-1] - T[0] < WIN - 30 or nowt - T[-1] > 30:
        return None
    now = float(M[-1])
    p0 = float(R[-1, 4])
    if not _fin(p0) or p0 <= 0:
        p0 = float(M[0])
    move = 100.0 * (now - p0) / p0
    rec = T >= nowt - 60
    nrec = int(rec.sum())
    if nrec < 20 or len(M) - nrec < 40:
        return None
    hi1, hi_old = M[rec].max(), M[~rec].max()
    hi3, lo3 = float(M.max()), float(M.min())
    hh = bool(hi1 > hi_old * 1.005 and now >= hi3 * 0.97)
    # delta
    d_now, d_0 = float(R[0, 10]), float(R[-1, 10])
    dd = abs(d_now) - abs(d_0) if (_fin(d_now) and _fin(d_0)) else math.nan
    delta_up = bool(_fin(dd) and dd >= 0.02)
    # volume: last 60 s vs median 1-min volume over the last 15 min (ttq is cumulative)
    q = R[:-1, 7]
    dq = q[:-1] - q[1:]
    good = np.isfinite(dq) & (dq >= 0)
    if good.sum() >= 4 and good[0]:
        med = float(np.sort(dq[good])[good.sum() // 2])
        vol_ok = bool(dq[0] > 0 and dq[0] >= med)
        vol_x = float(dq[0]) / med if med > 0 else math.nan
    else:
        vol_ok, vol_x = False, math.nan
    # IV
    iv_now, iv_0 = float(R[0, 9]), float(R[-1, 9])
    div = (iv_now - iv_0) * 100 if (_fin(iv_now) and _fin(iv_0)) else math.nan
    iv_ok = bool(_fin(div) and div >= -0.5)
    # spot
    spot_ok = bool(_fin(ds) and (ds >= need if rr == "CE" else ds <= -need))
    run = 100.0 * (hi3 - lo3) / lo3 if lo3 > 0 else 0.0
    off = 100.0 * (hi3 - now) / hi3 if hi3 > 0 else 0.0
    return {"rr": rr, "k": k, "now": now, "move": move, "hh": hh, "delta": delta_up, "dd": dd,
            "vol": vol_ok, "vol_x": vol_x, "iv": iv_ok, "div": div, "spot": spot_ok, "ds": ds, "run": run,
            "off": off, "hi3": hi3, "lo3": lo3}


def _all(c):
    return c["move"] >= RISE and c["hh"] and c["delta"] and c["vol"] and c["iv"] and c["spot"]


def _exh(c):
    return c["move"] >= RISE and c["hh"] and c["spot"] and (not c["vol"] or not c["iv"])


def _ticks(c):
    m = lambda b: "✓" if b else "✗"  # noqa: E731
    return f"HH {m(c['hh'])} delta↑ {m(c['delta'])} vol {m(c['vol'])} IV {m(c['iv'])} spot {m(c['spot'])}"


def _gave(c):
    """share of the 3-min run (low -> high) already given back"""
    rng = c["hi3"] - c["lo3"]
    return (c["hi3"] - c["now"]) / rng if rng > 0 else 0.0


def _broke(c):
    return c["off"] >= BRK_OFF and c["run"] >= BRK_RUN and _gave(c) >= GIVE_BACK


class Idea:
    def __init__(self):
        self.shown = ("NONE", None)  # (kind, rr)
        self.k = None                # strike locked while a side is shown
        self.t_shown = None
        self.cand = None
        self.cand_k = None
        self.n = 0
        self.last = None
        self.t_alert = -1e9

    def _candidate(self, cs, lock, now):
        kind, rr = self.shown
        c = lock
        if kind in ("CONTINUATION", "EXHAUSTING") and c is not None:
            if _broke(c):
                return ("BREAKING DOWN", rr), c["k"]
            sgn = 1 if rr == "CE" else -1
            alive = c["move"] > 0 and _gave(c) < GIVE_BACK and _fin(c["ds"]) and sgn * c["ds"] >= 0
            if kind == "CONTINUATION" and alive:
                return self.shown, c["k"]
            if kind == "EXHAUSTING":
                if _all(c):
                    return ("CONTINUATION", rr), c["k"]
                if alive:
                    return self.shown, c["k"]
        if self.t_shown is not None and now - self.t_shown < (BRK_HOLD if kind == "BREAKING DOWN" else MIN_DWELL):
            return self.shown, self.k
        # fresh look at the ATM pair: the side that qualifies, bigger 3-min premium move first
        best = None
        for r in ("CE", "PE"):
            x = cs.get(r)
            if x is None:
                continue
            k = "CONTINUATION" if _all(x) else "EXHAUSTING" if (_exh(x) and x["move"] >= EXH_FRESH) else None
            if k and (best is None or (k == "CONTINUATION", x["move"]) > (best[0] == "CONTINUATION", best[2])):
                best = (k, r, x["move"], x["k"])
        if best:
            return best[:2], best[3]
        if kind == "BREAKING DOWN" and self.t_shown is not None and now - self.t_shown < BRK_MAX:
            return self.shown, self.k
        return ("NONE", None), None

    def update(self, env):
        if not env.atm or env.hm < 9 * 60 + 15 + 3:
            return {"state": "WARMING", "text": "needs 3 min of ATM premium"}
        s_now, s_0 = env.hist.at("SPOT", "v", 0), env.hist.at("SPOT", "v", WIN)
        ds = (s_now - s_0) if (_fin(s_now) and _fin(s_0)) else math.nan
        _, S15 = env.hist.series("SPOT", secs=900)
        S15 = S15[np.isfinite(S15)]
        rng15 = float(S15.max() - S15.min()) if len(S15) else 0.0
        need = max(SPOT_MIN, SPOT_SHARE * rng15)
        cs = {rr: _side(env, rr, ds, None, need) for rr in ("CE", "PE")}
        if cs["CE"] is None and cs["PE"] is None:
            if self.last is not None:          # a mid-day gap (new ATM, thin quotes): keep the last view
                return dict(self.last, alert=False, text=f"ATM {env.atm}: quotes thin, last view kept")
            return {"state": "WARMING", "text": f"ATM {env.atm}: under 3 min of quotes yet"}
        lock = None
        if self.shown[1] is not None and self.k is not None:
            rr = self.shown[1]
            lock = cs[rr] if (cs.get(rr) and cs[rr]["k"] == self.k) else _side(env, rr, ds, self.k, need)
        cand, ck = self._candidate(cs, lock, env.t)
        checks = PERSIST if self.shown[0] == "NONE" else 2
        if cand == self.shown:
            self.cand, self.n = cand, 0
        elif cand == self.cand:
            self.n += 1
        else:
            self.cand, self.cand_k, self.n = cand, ck, 1
        alert = False
        if self.cand != self.shown and self.n >= checks:
            self.shown, self.t_shown, self.k = self.cand, env.t, self.cand_k
            if self.shown[0] == "CONTINUATION":
                c = cs.get(self.shown[1]) if (cs.get(self.shown[1]) and cs[self.shown[1]]["k"] == self.k) else (
                    lock if (lock and lock["rr"] == self.shown[1]) else None)
                alert = bool(c and c["move"] >= ALERT_MOVE and env.t - self.t_alert >= ALERT_GAP)
                if alert:
                    self.t_alert = env.t
                if c is not None:
                    self.k = c["k"]
            if self.shown[1] is None:
                self.k = None
        if self.shown[1] is not None and self.k is not None:
            rr = self.shown[1]
            got = cs[rr] if (cs.get(rr) and cs[rr]["k"] == self.k) else (
                lock if (lock and lock["k"] == self.k and lock["rr"] == rr) else _side(env, rr, ds, self.k, need))
            if got is not None:
                cs = dict(cs)
                cs[rr] = got
        kind, srr = self.shown
        if srr is None or cs.get(srr) is None:
            srr = max((r for r in cs if cs[r] is not None), key=lambda r: cs[r]["move"])
        c = cs[srr]
        state = "NONE" if kind == "NONE" else f"{kind} {srr}"
        text = (f"{c['rr']} {c['k']} {c['now']:.1f} {c['move']:+.1f}% 3m, {c['off']:.1f}% off high · " + _ticks(c)
                + (f" · Δ {c['dd']:+.3f}" if _fin(c["dd"]) else "")
                + (f" vol x{c['vol_x']:.1f}" if _fin(c["vol_x"]) else "")
                + (f" IV {c['div']:+.1f}" if _fin(c["div"]) else "")
                + (f" spot {c['ds']:+.0f}" if _fin(c["ds"]) else ""))
        plan = ""
        if kind == "CONTINUATION":
            brk = min(c["hi3"] * (1 - BRK_OFF / 100), c["hi3"] - GIVE_BACK * (c["hi3"] - c["lo3"]))
            plan = f"{srr} {c['k']}: breaking down if < {brk:.1f} (3-min high {c['hi3']:.1f})"
        elif kind == "BREAKING DOWN":
            plan = f"{srr} {c['k']} fading from {c['hi3']:.1f}: don't chase"
        out = {"state": state, "side": srr if kind == "CONTINUATION" else None, "value": c["move"], "unit": "% 3m",
               "text": text, "plan": plan, "alert": alert}
        self.last = out
        return out
