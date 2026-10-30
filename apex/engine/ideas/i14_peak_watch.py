"""Peak watch (owner, 28 Oct: "tight trailing at or near the peaks", "hold for how long").

While the champion holds a position, follow that option's mid (10-s mean, from env.hist): peak since entry, how far
it has given back from that peak, how long it has been held against the 10-15 min rule, and whether momentum is
fading (1-min mid slope turning against, delta smaller than at the peak). It also marks, once per trade, the moment a
TIGHT trail (keep 90 % of the peak gain, >= 3 pts, once the peak is >= +10 %) WOULD have exited, so the owner can compare that
against the champion's real exit. When flat, it shows the last closed trade's peak vs exit.

Observer only: the champion's own exit (-10 % stop, 30-s gain trail armed +20 % keeping 80 %) is untouched."""
import math

import numpy as np

NAME = "peak_watch"
TITLE = "Peak watch (tight trail?)"
IDEA = "Trail tight at or near the peak and don't overstay 10-15 min: where is the held option vs its peak?"
VERDICT = ("Rejected 28 Oct (R2-05): every tighter trail / stall / flow / max-hold exit lost (-Rs43k to -Rs2.1L); "
           "they cut the +69 % and +72 % winners. Shown for watching.")
EVERY_S = 2

SMOOTH_S = 10          # peak and 'now' use a 10-s mean of the mid (one-tick spikes are not peaks)
TT_ARM = 10.0          # tight trail arms once the peak gain is >= +10 %
TT_KEEP = 0.90         # ... and exits once the gain gives back 10 % of the peak gain
TT_MIN = 3.0           # ... but at least 3 gain points (so tick noise is not a "peak")
NEAR = 2.0             # within 2 % of the peak = NEAR PEAK
FADE_GB = 3.0          # >= 3 % off the peak with the 1-min slope against = FADING
HOLD_CALLS = 8         # a new (non-urgent) state must persist 8 calls (~16 s) before it shows


def _fin(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return math.nan
    return x if math.isfinite(x) else math.nan


def _hhmm(t, env):
    """epoch -> 'HH:MM' in the env's clock (env.dt is IST)."""
    try:
        sod = env.dt.hour * 3600 + env.dt.minute * 60 + env.dt.second
        s = int(round(sod + (t - env.t)))
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}"
    except Exception:
        return "?"


def _epoch(hms, env):
    """'HH:MM:SS' today -> epoch, using env.t / env.dt."""
    try:
        h, m, s = (int(float(x)) for x in str(hms).split(":")[:3])
        sod = env.dt.hour * 3600 + env.dt.minute * 60 + env.dt.second + env.dt.microsecond / 1e6
        return env.t - sod + h * 3600 + m * 60 + s
    except Exception:
        return None


def tt_level(pk_gain):
    """gain % at which the tight trail exits, for a peak gain % (works on numpy arrays too)."""
    return pk_gain - np.maximum(TT_MIN, (1 - TT_KEEP) * pk_gain)


def _tt_hits(sm, e):
    pkg = 100 * (np.maximum.accumulate(sm) / e - 1)
    g = 100 * (sm / e - 1)
    return np.nonzero((pkg >= TT_ARM) & (g <= tt_level(pkg)))[0]


def _smooth(V, w=SMOOTH_S):
    V = V[np.isfinite(V) & (V > 0)] if len(V) else V
    if len(V) == 0:
        return V
    if len(V) < w:
        return np.array([V.mean()])
    c = np.cumsum(np.insert(V, 0, 0.0))
    return (c[w:] - c[:-w]) / w


class Idea:
    def __init__(self):
        self.pos = None          # key of the tracked position
        self.p = {}              # per-position state
        self.shown = None        # displayed state
        self.cand, self.cand_n = None, 0
        self.last = None         # summary of the last tracked position (for FLAT)
        self.flat_cache = {}

    # ── position tracking ────────────────────────────────────────────────
    def _start(self, env, c, key):
        entry = _fin(c.get("entry"))
        t_in = _fin(c.get("t_in"))
        if not math.isfinite(t_in):
            t_in = env.t
        p = {"key": key, "entry": entry, "t_in": t_in, "peak": entry if entry > 0 else math.nan, "peak_t": t_in,
             "peak_delta": math.nan, "tt_t": None, "tt_px": None, "tt_gain": None, "max_gain": 0.0}
        # back-fill the peak from the 1-Hz history (engine restart / card added mid-trade)
        T, V = env.hist.series((int(round(c.get("strike"))), c.get("rr")), "mid", since=t_in - 1)
        if len(V):
            ok = np.isfinite(V) & (V > 0)
            T, V = T[ok], V[ok]
            sm = _smooth(V)
            if len(sm) and len(V) >= SMOOTH_S:
                Ts = T[SMOOTH_S - 1:]
                j = int(np.argmax(sm))
                if not (sm[j] <= p["peak"]):
                    p["peak"], p["peak_t"] = float(sm[j]), float(Ts[j])
                if entry > 0:    # first moment the tight trail would have fired, if already past
                    hit = _tt_hits(sm, entry)
                    if len(hit):
                        h = int(hit[0])
                        p["tt_t"], p["tt_px"] = float(Ts[h]), float(sm[h])
                        p["tt_gain"] = 100 * (sm[h] / entry - 1)
        self.p = p
        self.pos = key

    def _held(self, env, c):
        key = (c.get("rr"), c.get("strike"), round(_fin(c.get("t_in")) or 0, 0))
        if key != self.pos:
            self._start(env, c, key)
        p = self.p
        rr, k = c.get("rr"), c.get("strike")
        entry = p["entry"]
        T, V = env.hist.series((int(round(k)), rr), "mid", secs=75)
        ok = np.isfinite(V) & (V > 0)
        T, V = T[ok], V[ok]
        now_px = float(V[-SMOOTH_S:].mean()) if len(V) else math.nan
        if not math.isfinite(now_px):
            r = _fin(c.get("ret_pct"))
            now_px = entry * (1 + r / 100) if (entry > 0 and math.isfinite(r)) else math.nan
        if not (entry > 0 and math.isfinite(now_px)):
            return {"state": "WARMING", "text": f"holding {rr} {k}: no price yet"}
        row = env.chain.get((int(round(k)), rr)) if k is not None else None
        delta = abs(_fin(row.get("delta"))) if row else math.nan
        if not (now_px <= p["peak"]):       # new peak (also when peak is nan)
            p["peak"], p["peak_t"], p["peak_delta"] = now_px, env.t, delta
        peak = p["peak"]
        gain = 100 * (now_px / entry - 1)
        pk_gain = 100 * (peak / entry - 1)
        p["max_gain"] = max(p["max_gain"], pk_gain)
        gb = 100 * (1 - now_px / peak) if peak > 0 else 0.0
        held = (env.t - p["t_in"]) / 60.0
        since_pk = (env.t - p["peak_t"]) / 60.0
        # 1-min slope of the mid (10-s mean now vs 10-s mean 60 s ago), % of entry per minute
        slope = math.nan
        if len(T) >= 40 and T[-1] - T[0] >= 55:
            old = V[(T >= T[-1] - 70) & (T <= T[-1] - 50)]
            if len(old):
                slope = 100 * (now_px - float(old.mean())) / entry
        d_fade = (math.isfinite(delta) and math.isfinite(p["peak_delta"]) and p["peak_delta"] > 0
                  and delta < 0.9 * p["peak_delta"])
        alert = False
        if p["tt_t"] is None and pk_gain >= TT_ARM and gain <= tt_level(pk_gain):
            p["tt_t"], p["tt_px"], p["tt_gain"] = env.t, now_px, gain
            alert = True
        # state, with hysteresis on the displayed one (enter strict, leave loose)
        cur = self.shown
        sl = slope if math.isfinite(slope) else 0.0
        if p["tt_t"] is not None and gain <= p["tt_gain"] + 1.0:     # at/below where the tight trail sold
            st = "GIVING BACK"
        elif pk_gain >= 5 and gb <= (NEAR + 1.5 if cur == "NEAR PEAK" else NEAR):
            st = "NEAR PEAK"
        elif (gb >= FADE_GB and (sl <= -1.5 or d_fade)) or (cur == "FADING" and gb >= FADE_GB - 1.5 and sl < 1.0):
            st = "FADING"
        elif gain <= (-4 if cur == "UNDER WATER" else -6):
            st = "UNDER WATER"
        else:
            st = "RUNNING"
        urgent = alert or st == "GIVING BACK"
        st = self._settle(st, urgent)
        clock = f"held {held:.0f} min" + (" (past 15)" if held > 15 else "")
        txt = (f"{rr} {k:.0f} {gain:+.1f} %, peak {pk_gain:+.1f} % {since_pk:.0f} min ago, {gb:.1f} % off peak; "
               f"{clock}; 1-min slope {slope:+.1f} %" if math.isfinite(slope) else
               f"{rr} {k:.0f} {gain:+.1f} %, peak {pk_gain:+.1f} %, {gb:.1f} % off peak; {clock}")
        if math.isfinite(delta) and math.isfinite(p["peak_delta"]):
            txt += f"; delta {delta:.2f} (peak {p['peak_delta']:.2f})"
        if p["tt_t"] is not None:
            plan = (f"tight trail would have exited {_hhmm(p['tt_t'], env)} at {p['tt_gain']:+.1f} %"
                    f" (now {gain:+.1f} %)")
        elif pk_gain >= TT_ARM:
            plan = f"tight trail armed: would exit at {tt_level(pk_gain):+.1f} % (peak {pk_gain:+.1f} %)"
        else:
            plan = f"tight trail arms at {entry * (1 + TT_ARM / 100):.1f} (+{TT_ARM:.0f} %)"
        self.last = {"key": self.pos, "rr": rr, "strike": k, "entry": entry, "peak_gain": pk_gain,
                     "peak_t": p["peak_t"], "tt_t": p["tt_t"], "tt_gain": p["tt_gain"], "last_gain": gain}
        return {"state": st, "side": None, "value": round(gb, 2), "unit": "% off pk", "text": txt, "plan": plan,
                "alert": alert}

    def _settle(self, st, urgent):
        if urgent or self.shown is None or st == self.shown:
            self.shown, self.cand, self.cand_n = st, None, 0
            return st
        if st == self.cand:
            self.cand_n += 1
        else:
            self.cand, self.cand_n = st, 1
        if self.cand_n >= HOLD_CALLS:
            self.shown, self.cand, self.cand_n = st, None, 0
        return self.shown

    # ── flat ─────────────────────────────────────────────────────────────
    def _flat(self, env):
        self.pos, self.p = None, {}
        self.shown, self.cand, self.cand_n = "FLAT", None, 0
        trades = env.trades or []
        if not trades:
            return {"state": "FLAT", "text": "no position, no closed trade yet today",
                    "plan": f"tight trail = keep 90 % of the peak gain after +{TT_ARM:.0f} % (watch only)"}
        tr = trades[-1]
        ck = (tr.get("time_in"), tr.get("rr"), tr.get("strike"))
        if ck not in self.flat_cache:
            self.flat_cache[ck] = self._post(env, tr)
        return self.flat_cache[ck]

    def _post(self, env, tr):
        rr, k, ret = tr.get("rr"), tr.get("strike"), _fin(tr.get("ret_pct"))
        t0, t1 = _epoch(tr.get("time_in"), env), _epoch(tr.get("time_out"), env)
        name = f"{rr} {k:.0f}" if k is not None else str(rr)
        held = f"{(t1 - t0) / 60:.0f} min" if (t0 and t1) else "?"
        L = self.last if (self.last and self.last["rr"] == rr and self.last["strike"] == k) else None
        pk_gain, tt = math.nan, None
        if L is not None:
            pk_gain = L["peak_gain"]
            if L["tt_t"] is not None:
                tt = (L["tt_t"], L["tt_gain"])
        elif t0 and t1 and k is not None:     # derive from the history: entry ~ the mid at t_in, peak = max 10-s mean to t_out
            T, V = env.hist.series((int(round(k)), rr), "mid", since=t0 - 1)
            m = (T <= t1) & np.isfinite(V) & (V > 0)
            V = V[m]
            if len(V) >= SMOOTH_S:
                sm = _smooth(V)
                e = float(V[:3].mean())
                pk_gain = 100 * (float(sm.max()) / e - 1)
                hit = _tt_hits(sm, e)
                if len(hit):
                    tt = (T[m][SMOOTH_S - 1 + int(hit[0])], 100 * (sm[int(hit[0])] / e - 1))
        if not math.isfinite(pk_gain):
            return {"state": "FLAT", "text": f"last {name} {ret:+.1f} % in {held}; peak not in history",
                    "plan": ""}
        if math.isfinite(ret):
            pk_gain = max(pk_gain, ret)     # the exit fill can beat the 10-s mean peak
        gb = (pk_gain - ret) if math.isfinite(ret) else None
        txt = (f"last {name}: peak {pk_gain:+.1f} %, exit {ret:+.1f} % ({gb:.1f} pts given back), held {held}"
               if gb is not None else f"last {name}: peak {pk_gain:+.1f} %, held {held}")
        plan = (f"tight trail would have exited {_hhmm(tt[0], env)} at {tt[1]:+.1f} % vs actual {ret:+.1f} %"
                if tt else "tight trail never fired on it")
        return {"state": "FLAT", "value": gb, "unit": "pts gave", "text": txt, "plan": plan}

    # ── entry point ──────────────────────────────────────────────────────
    def update(self, env):
        c = env.champ
        if c and c.get("rr") in ("CE", "PE") and c.get("strike") is not None:
            return self._held(env, c)
        return self._flat(env)
