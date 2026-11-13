"""The Conductor's own voice (13 Nov, owner point 4: "I still have not seen the system's personal commentary on what it
would do at that point of time"). Display only: nothing here is read by any decision.

Once a second, after the Conductor's step, `Voice.view(eng, ctx)` reads (never writes) the lead pool book's c20
strategy object (the smoothed forward, the rolling 20-minute high and low, the pullback arm), the Conductor's own book
(its position and pos["rules"], the real exit levels) and the pool books' veto state, and says in the first person
what the system is waiting for, how close it is, what it would buy, and when it would sell.

Design: docs/research/13nov/R12 (data contract) and R11 (card). The strategy objects are read only: nothing here calls
a strategy method that writes state (c20_8x "rw" writes self.blk inside _pick, so the strike shown is a display copy of
the picker). A fault in here is caught by engine._safe and only empties state["voice"].
"""
import math
import time
from collections import deque

import numpy as np

from .. import config

# "How close am I": chance the trigger fires within 5 / 10 / 15 minutes from each phase and progress bucket.
# R12 pilot (4 to 6 Nov, every second counted, so the seconds are dependent): a rough guide, not a forecast.
# phaseB_arm_phases.py writes the walk-forward calibration; replace this table with its output when it lands.
P_FIRE = {
    # R12 Phase B (13 Nov): normal days 19 Oct to 11 Nov, every 5th second, fit 19 Oct to 4 Nov and checked 5 to 11 Nov
    # (Brier better than a constant on all 4 test days), pooled here weighted by samples. In the test week ARMED fired
    # about half as often as in the fit window, so these odds lean high.
    "IDLE": [(0.5, (0.01, 0.06, 0.12)), (0.8, (0.02, 0.09, 0.19)), (9.0, (0.02, 0.14, 0.25))],
    "ARMED": [(0.5, (0.09, 0.18, 0.24)), (0.8, (0.22, 0.35, 0.39)), (9.0, (0.25, 0.31, 0.33))],
    "ZONE": [(0.5, (0.74, 0.74, 0.78)), (0.8, (0.92, 0.92, 0.94)), (9.0, (0.95, 0.95, 0.97))],
}
P_FIRE_NOTE = "normal days 19 Oct to 11 Nov; slower in the last week"

MODES = ("WAITING", "IMPULSE", "ARMED", "ZONE", "PENDING", "HOLDING", "EXITING", "CLOSED", "STOOD_DOWN", "PAUSED", "OFF")


def _f(x, nd=1):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, nd) if math.isfinite(x) else None


def _fin(x):
    try:
        return x is not None and math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def _clock(t_open, i):
    return time.strftime("%H:%M", time.localtime(t_open + i)) if _fin(t_open) else None


def _hm(m):
    """minutes since midnight -> HH:MM"""
    m = int(round(m))
    return f"{m // 60:02d}:{m % 60:02d}"


def _p_fire(phase, progress):
    for top, row in P_FIRE.get(phase, ()):
        if progress < top:
            return {"m5": row[0], "m10": row[1], "m15": row[2]}
    return None


def _odds_words(p):
    if p is None:
        return None
    n = p["m10"]
    if n >= 0.75:
        return "almost every time"
    if n >= 0.15:
        return f"about {max(1, round(n * 10))} times in 10"
    if n >= 0.05:
        return "about 1 time in 10"
    return "rarely"


class Voice:
    def __init__(self):
        self.v = None
        self._last_i = None
        self._med = (None, None)          # (second, median of c20_9y's IV series) cached every 10 s
        self._level = (None, None, 0.0)   # (shown level, candidate, candidate since) for the exit ladder
        self._closed = None               # the last closed trade, said for 2 minutes after the exit

    # ── reading the strategy objects (read only) ────────────────────────────────
    @staticmethod
    def _adapter(eng, name):
        return (getattr(eng, "_council_ad", None) or {}).get(name)

    def _lead(self, eng):
        c = getattr(eng, "conductor", None)
        for m in (c.members if c is not None else ()):
            ad = self._adapter(eng, m["book"])
            if ad is not None and getattr(ad, "strat", None) is not None:
                return m["book"], ad
        return None, None

    def _trigger(self, s, D, i):
        """The lead book's trigger state at row i, in points."""
        p = getattr(s, "p", None) or {}
        fs_arr = getattr(s, "fs", None)
        if fs_arr is None or getattr(s, "day", None) != D.day or not (0 <= i < len(fs_arr)):
            return None
        fs = float(fs_arr[i])
        x = getattr(s, "x", None) or {}
        W, L, vmin = int(p.get("W", 1200)), int(p.get("L", 1200)), float(p.get("vmin", 40.0))
        tr = {"mode": "expiry" if D.dte0 else "normal", "pb_entry": float(p.get("pb", 0)) > 0,
              "need_pts": vmin, "window_min": round(W / 60), "vel_min": round(L / 60),
              "fwd": _f(fs), "t0": _hm(p.get("t0", 556)), "t1": _hm(p.get("t1", 900)),
              "hm": float(D.hm[i])}
        if not math.isfinite(fs):
            tr["no_forward"] = True
            return tr
        qmax, qmin = getattr(s, "qmax", None), getattr(s, "qmin", None)
        hi = float(qmax[0][1]) if qmax else None
        lo = float(qmin[0][1]) if qmin else None
        v = None
        if i >= L and math.isfinite(fs_arr[i - L]):
            v = fs - float(fs_arr[i - L])
        tr.update(hi=_f(hi), lo=_f(lo), range_pts=_f(hi - lo) if hi is not None and lo is not None else None,
                  move_pts=_f(v), gap_hi=_f(hi - fs) if hi is not None else None,
                  gap_lo=_f(fs - lo) if lo is not None else None,
                  warm=i < W + 2, ready_at=_clock(D.t_open, W + 2))
        cool = int(p.get("cool", 60)) - (i - int(getattr(s, "last_exit", -10 ** 9)))
        tr["cool_left_s"] = cool if cool > 0 else 0
        a = getattr(s, "arm", None)
        if a is not None and float(p.get("pb", 0)) > 0:
            sd, base, ext, pbx, t_arm = a[0], float(a[1]), float(a[2]), float(a[3]), int(a[4])
            up = sd == "CE"
            imp = abs(ext - base)
            ret = (ext - pbx) if up else (pbx - ext)
            need = float(p["pb"]) * imp
            mx = float(x.get("PB_DMAX", 0.9)) * imp
            life = min(W, int(x.get("PB_AMAX", W)))
            rs = float(p.get("rs", 5.0))
            res = (fs - pbx) if up else (pbx - fs)
            tr["arm"] = {"side": sd, "impulse_pts": _f(imp), "pullback_pts": _f(ret), "need_pts": _f(need),
                         "max_pts": _f(mx), "pullback_pct": _f(100 * ret / imp, 0) if imp > 0 else None,
                         "need_pct": round(100 * float(p["pb"])), "max_pct": round(100 * float(x.get("PB_DMAX", 0.9))),
                         "since": _clock(D.t_open, t_arm), "age_s": i - t_arm, "expires": _clock(D.t_open, t_arm + life),
                         "left_s": t_arm + life - i, "resume_pts": _f(res), "resume_need": rs,
                         "in_zone": ret >= need,
                         "fire_level": _f(pbx + rs if up else pbx - rs),
                         "drop_level": _f(ext - mx if up else ext + mx),
                         "printing": ret <= 1.0}
        return tr

    def _vetoes(self, eng, D, i, side):
        """Each pool book: ready, busy, or the veto it would apply to a buy on `side` now, with its margin."""
        out = []
        c = getattr(eng, "conductor", None)
        for m in (c.members if c is not None else ()):
            name = m["book"]
            b = eng.books.get(name)
            ad = self._adapter(eng, name)
            row = {"book": name, "ready": True, "veto": None, "text": "ready"}
            if b is None or ad is None:
                row.update(ready=False, text="not running")
                out.append(row)
                continue
            s = ad.strat
            if b.pos or b.ctl.get("pending_entry"):
                row.update(ready=False, text="holding its own copy")
            if hasattr(s, "_y_avg") and getattr(s, "_y_day", None) == D.day and 0 <= i < len(s._y_avg):
                st = int(getattr(s, "_y_st", 0))
                if i - st >= 300 and math.isfinite(s._y_avg[i]):
                    if self._med[0] is None or i - self._med[0] >= 10:
                        h = s._y_avg[st:i]
                        h = h[np.isfinite(h)]
                        self._med = (i, float(np.median(h)) if len(h) else None)
                    if self._med[1] is not None:
                        ex = float(s._y_avg[i]) - self._med[1]
                        row["iv_vs_median"] = _f(ex, 2)
                        if ex > 3.5:
                            row.update(ready=False, veto="iv_rich",
                                       text=f"would refuse: ATM IV {ex:+.1f} pts over its median (limit +3.5)")
                if side and not D.dte0 and row["veto"] is None:
                    try:
                        from .council.c20_9y import wall_ahead
                        d = wall_ahead(D, i, side, 250)
                        if math.isfinite(d):
                            row["wall_pts"] = _f(d)
                            if 0 < d <= 25:
                                row.update(ready=False, veto="oi_wall",
                                           text=f"would refuse: the biggest {'call' if side == 'CE' else 'put'} OI wall is {d:.0f} pts ahead (limit 25)")
                    except Exception:
                        pass
            if hasattr(s, "_si_arm_i") and not D.dte0 and getattr(s, "arm", None) is not None:
                age = i - int(s.arm[4])
                if age > 660 and row["veto"] is None:
                    row.update(ready=False, veto="stale_impulse",
                               text=f"would refuse: the impulse is {age // 60} min old (limit 11)")
            out.append(row)
        return out

    def _would_buy(self, eng, ctx, D, i, side, cb):
        """Display copy of the c20 picker: |delta| >= 0.52, nearest to the target delta, within 3 strikes of ATM."""
        if side not in ("CE", "PE"):
            return None
        k0 = D.atm(i)
        if not _fin(k0):
            return None
        target = 0.65 if D.dte0 else 0.52
        w0 = ctx.get("w0")
        best = None
        for k in (k0 - 150, k0 - 100, k0 - 50, k0, k0 + 50, k0 + 100, k0 + 150):
            o = (ctx.get("by_key") or {}).get(f"NIFTY|OPT|{w0}|{int(k)}|{side}")
            if not o or not o.get("ask") or (o.get("age") or 9e9) > 5:
                continue
            dl = abs(o.get("delta") or 0.0)
            if dl < 0.52:
                continue
            sc = abs(dl - target)
            if best is None or sc < best[0]:
                best = (sc, int(k), o)
        if best is None:
            return None
        _, k, o = best
        ask = float(o["ask"])
        cap = float(getattr(cb, "capital", 0.0) or 0.0)
        lots = int(cap // (ask * config.LOT_SIZE)) if ask > 0 else 0
        return {"strike": k, "rr": side, "ask": _f(ask, 2), "delta": _f(o.get("delta"), 2), "lots": lots,
                "cost_rs": round(lots * ask * config.LOT_SIZE), "approx": bool(D.dte0)}

    # ── the held position ──────────────────────────────────────────────────────
    def _hold(self, ctx, pos, now):
        r = pos.get("rules") or {}
        o = (ctx.get("by_key") or {}).get(pos.get("key")) or {}
        bid = o.get("bid")
        e = float(pos["entry"])
        dl = abs(o.get("delta") or 0.5)
        ret = 100.0 * (bid / e - 1.0) if bid else None
        ex = []
        if _fin(r.get("sl_px")):
            ex.append({"kind": "SL", "label": f"premium stop -{r.get('sl_pct') or 15:.0f} %", "px": _f(r["sl_px"], 2),
                       "away_px": _f(bid - r["sl_px"], 2) if bid else None})
        if _fin(r.get("trail_px")):
            give, tp = r.get("trail_give"), r.get("trail_pts")
            away_f = (tp - give) if _fin(give) and _fin(tp) else None
            ex.append({"kind": "FWD_TRAIL", "label": f"forward trail {tp:.0f} pts" if _fin(tp) else "forward trail",
                       "fwd_level": _f(r["trail_px"]), "fwd_now": _f(r.get("fwd_now")), "away_fwd": _f(away_f),
                       "away_px": _f(away_f * dl, 2) if away_f is not None else None})
        if _fin(r.get("floor_px")):
            ex.append({"kind": "FLOOR", "label": f"profit floor ({(r.get('floor_kind') or 'floor').lower()})",
                       "px": _f(r["floor_px"], 2), "away_px": _f(bid - r["floor_px"], 2) if bid else None})
        if r.get("pt_armed") and _fin(r.get("pt_trail_px")):
            ex.append({"kind": "PREM_TRAIL", "label": f"premium trail {r.get('pt_give_pct') or 8:.0f} % off the peak",
                       "px": _f(r["pt_trail_px"], 2), "away_px": _f(bid - r["pt_trail_px"], 2) if bid else None})
        if _fin(r.get("clock_left_s")):
            ex.append({"kind": "CLOCK", "label": "hold clock", "left_s": int(max(0, r["clock_left_s"]))})
        ex.append({"kind": "TIME", "label": "forced flat", "at": r.get("flat_at") or "15:20"})
        near = [x for x in ex if x.get("away_px") is not None]
        nearest = min(near, key=lambda x: x["away_px"]) if near else None
        pending = bool(pos.get("pending"))
        if pending:
            cand = "EXITING"
        elif nearest is not None and nearest["away_px"] <= 0.04 * e:
            cand = "NEAR"
        elif _fin(r.get("clock_left_s")) and r["clock_left_s"] < 300:
            cand = "NEAR"
        elif _fin(r.get("floor_px")) and r["floor_px"] >= e:
            cand = "PROTECTED"
        else:
            cand = "HOLD"
        shown, c0, since = self._level
        if cand == "EXITING" or shown is None:
            self._level = (cand, cand, now)
        elif cand != shown:
            if cand != c0:
                self._level = (shown, cand, now)
            elif now - since >= 10:              # a new level must hold 10 s before it is shown (no flicker)
                self._level = (cand, cand, now)
        else:
            self._level = (shown, cand, now)
        floor_arm = r.get("be_arm_pct")
        return {"key": pos.get("key"), "rr": pos.get("rr"), "strike": pos.get("strike"), "lots": pos.get("lots"),
                "entry": _f(e, 2), "bid": _f(bid, 2), "ret_pct": _f(ret), "peak_pct": _f(r.get("peak_pct")),
                "since": pos.get("time_in"), "src": pos.get("src"), "held_s": _f(r.get("held_s"), 0),
                "exits": ex, "nearest": nearest["kind"] if nearest else None, "level": self._level[0],
                "floor_arms_pct": _f(floor_arm, 0) if not _fin(r.get("floor_px")) else None,
                "mode": r.get("mode")}

    # ── words ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _say_hold(h):
        side = "CALL" if h["rr"] == "CE" else "PUT"
        head = (f"I hold {h['lots']} lots of the {h['strike']:.0f} {h['rr']} ({side}), "
                f"{h['ret_pct']:+.1f} % now" if h["ret_pct"] is not None else
                f"I hold {h['lots']} lots of the {h['strike']:.0f} {h['rr']}")
        if h["peak_pct"] is not None:
            head += f", best {h['peak_pct']:+.1f} %"
        head += "."
        lines = []
        firsts = []
        for x in h["exits"]:
            if x["kind"] == "SL":
                firsts.append(f"bid {x['px']:.2f} (my -15 % stop)")
            elif x["kind"] == "FWD_TRAIL":
                firsts.append(f"forward back to {x['fwd_level']:,.0f}" +
                              (f" ({x['away_fwd']:.0f} pts away)" if x.get("away_fwd") is not None else ""))
            elif x["kind"] == "FLOOR":
                firsts.append(f"bid {x['px']:.2f} (my profit floor)")
            elif x["kind"] == "PREM_TRAIL":
                firsts.append(f"bid {x['px']:.2f} (my premium trail)")
            elif x["kind"] == "CLOCK":
                firsts.append(f"{x['left_s'] // 60} min more on the clock")
            elif x["kind"] == "TIME":
                firsts.append(x["at"])
        lines.append("I sell at the first of: " + "; ".join(firsts) + ".")
        if h["floor_arms_pct"] is not None:
            lines.append(f"My profit floor arms once the bid is {h['floor_arms_pct']:+.0f} % over my entry.")
        if h["level"] == "EXITING":
            lines.insert(0, "An exit rule has fired. I am selling at the next print.")
        elif h["level"] == "NEAR":
            lines.append(f"Nearest exit: {h['nearest'] or 'the clock'}. I am close to selling.")
        elif h["level"] == "PROTECTED":
            lines.append("My floor is above my entry: this trade can no longer lose much.")
        else:
            lines.append("Nothing says sell yet. I hold.")
        return head, lines

    @staticmethod
    def _say_flat(tr, wb, books, mode):
        lines = []
        arm = tr.get("arm")
        if mode == "ZONE":
            side = "CALL" if arm["side"] == "CE" else "PUT"
            head = (f"Ready to buy a {side}. The pullback is {arm['pullback_pts']:.0f} pts ({arm['pullback_pct']:.0f} %). "
                    f"I buy the moment the forward turns {'up' if arm['side'] == 'CE' else 'down'} to {arm['fire_level']:,.1f}.")
        elif mode == "ARMED":
            side = "CALL" if arm["side"] == "CE" else "PUT"
            head = (f"Armed for a {side} since {arm['since']} (impulse {arm['impulse_pts']:.0f} pts). "
                    f"The pullback is {arm['pullback_pts']:.0f} of the {arm['need_pts']:.0f} pts I need.")
            lines.append(f"If it falls back more than {arm['max_pts']:.0f} pts (past {arm['drop_level']:,.0f}) I drop the idea. "
                         f"The arm expires at {arm['expires']}.")
        elif mode == "IMPULSE":
            side = "CALL" if arm["side"] == "CE" else "PUT"
            head = (f"An impulse is printing: forward {tr['move_pts']:+.0f} pts in {tr['vel_min']} min. "
                    f"I do not buy the breakout. I wait for a pullback of about "
                    f"{0.5 * (arm['impulse_pts'] or 0):.0f} pts, then a {arm['resume_need']:.0f}-pt turn back.")
        elif tr.get("mode") == "expiry":
            mv = tr.get("move_pts")
            up = mv is None or mv >= 0
            gap = tr.get("gap_hi") if up else tr.get("gap_lo")
            head = (f"Expiry day. I am flat. I buy a {'CALL' if up else 'PUT'} when the forward breaks its "
                    f"{tr['window_min']}-min {'high' if up else 'low'} with {tr['need_pts']:.0f} pts of speed in "
                    f"{tr['vel_min']} min.")
            if mv is not None:
                lines.append(f"Now: {abs(mv):.0f} of {tr['need_pts']:.0f} pts of speed, "
                             f"{max(gap or 0, 0):.0f} pts from the {'high' if up else 'low'}.")
        else:
            mv = tr.get("move_pts")
            head = f"I am flat. I need a {tr['need_pts']:.0f}-pt move of the forward in {tr['vel_min']} min to a new {tr['window_min']}-min high or low."
            if mv is not None:
                up = mv >= 0
                gap = tr.get("gap_hi") if up else tr.get("gap_lo")
                lines.append(f"The forward has moved {mv:+.0f} pts and sits {max(gap or 0, 0):.0f} pts "
                             f"{'under its high' if up else 'over its low'}. 20-min range {tr.get('range_pts') or 0:.0f} pts.")
        if wb and mode in ("ZONE", "ARMED"):
            lines.append(f"I would buy the {wb['strike']} {wb['rr']} at about {wb['ask']:.2f}, {wb['lots']} lots "
                         f"(Rs {wb['cost_rs']:,}). I would sell at -15 %, on a "
                         + ("25-pt forward trail or after 15 minutes." if tr.get("mode") == "expiry"
                            else "40-pt forward trail or after 90 minutes."))
        vet = [b for b in books if b.get("veto")]
        if vet:
            v = vet[0]
            lines.append(f"{v['book']} {v['text']}." + (" Another pool book would still take it." if len(vet) < len(books) else ""))
        p = tr.get("p_fire")
        if p:
            lines.append(f"From here I fired within 10 minutes {_odds_words(p)} ({P_FIRE_NOTE}).")
        return head, lines[:4]

    # ── once a second ──────────────────────────────────────────────────────────
    def view(self, eng, ctx):
        from . import conductor as conductor_mod
        now = float(ctx.get("now_s") or time.time())
        cb = eng.books.get(conductor_mod.BOOK) if getattr(eng, "books", None) else None
        name, ad = self._lead(eng)
        if cb is None or ad is None:
            self.v = {"v": 1, "mode": "OFF", "headline": "The Conductor is not running.", "lines": []}
            return self.v
        D, s = ad.D, ad.strat
        i = int(now - D.t_open)
        if self._last_i == i and self.v is not None:
            return self.v
        self._last_i = i
        out = {"v": 1, "t": now, "time": time.strftime("%H:%M:%S", time.localtime(now)), "lead": name,
               "capital": round(float(cb.capital)), "day": self._day(cb)}
        c = eng.conductor
        out["recent"] = list(getattr(c, "recent", ()) or ())[-5:]
        if cb.pos:
            h = self._hold(ctx, cb.pos, now)
            out["hold"] = h
            out["mode"] = "EXITING" if h["level"] == "EXITING" else "HOLDING"
            out["headline"], out["lines"] = self._say_hold(h)
            self._closed = None
        elif cb.ctl.get("owner"):
            own = cb.ctl["owner"]
            out["mode"] = "PENDING"
            out["headline"] = f"My trigger fired at {own.get('time') or ''} via {own.get('book')}. I am buying at the next print."
            out["lines"] = [str(own.get("why") or "")]
        else:
            self._level = (None, None, 0.0)
            t = cb.trades[-1] if cb.trades else None
            if t is not None and (self._closed is None or self._closed[0] != t.get("t_out")):
                self._closed = (t.get("t_out"), t)
            tr = self._trigger(s, D, i) if 0 <= i else None
            out["trigger"] = tr
            bo = (ctx.get("blackout") or {}).get("on")
            if tr is None:
                out["mode"], out["headline"], out["lines"] = "OFF", "My trigger is warming up.", []
            elif bo:
                out["mode"], out["headline"] = "PAUSED", "The data has a gap. I take no entry until it is clean."
                out["lines"] = []
            elif tr["hm"] < (9 * 60 + 16):
                out["mode"], out["headline"], out["lines"] = "STOOD_DOWN", f"I start watching at {tr['t0']}.", []
            elif tr["hm"] >= float((s.p or {}).get("t1", 900)):
                out["mode"] = "STOOD_DOWN"
                out["headline"] = f"I take no new entries after {tr['t1']}. I am done for today."
                out["lines"] = []
            elif tr.get("no_forward"):
                out["mode"], out["headline"], out["lines"] = "PAUSED", "The parity forward is missing. I wait.", []
            elif tr.get("warm"):
                out["mode"] = "WAITING"
                out["headline"] = f"I am learning the {tr['window_min']}-min range. My trigger is ready at {tr['ready_at']}."
                out["lines"] = []
            else:
                arm = tr.get("arm")
                if arm is not None:
                    mode = "ZONE" if arm["in_zone"] else ("IMPULSE" if arm["printing"] else "ARMED")
                    side = arm["side"]
                    prog = (arm["resume_pts"] or 0) / max(arm["resume_need"], 1e-9) if mode == "ZONE" else \
                        (arm["pullback_pts"] or 0) / max(arm["need_pts"] or 1e-9, 1e-9)
                    tr["p_fire"] = _p_fire("ZONE" if mode == "ZONE" else "ARMED", prog)
                else:
                    mode = "WAITING"
                    mv = tr.get("move_pts")
                    side = ("CE" if mv >= 0 else "PE") if mv is not None else None
                    prog = abs(mv) / tr["need_pts"] if mv is not None else 0.0
                    tr["p_fire"] = _p_fire("IDLE", prog) if tr["mode"] == "normal" else None
                tr["progress"] = _f(min(prog, 1.5), 2)
                books = self._vetoes(eng, D, i, side)
                wb = self._would_buy(eng, ctx, D, i, side, cb) if mode in ("ZONE", "ARMED", "IMPULSE") else None
                out.update(mode=mode, books=books, would_buy=wb)
                out["headline"], out["lines"] = self._say_flat(tr, wb, books, mode)
                if tr.get("cool_left_s"):
                    out["lines"].insert(0, f"I just closed a trade. I wait {tr['cool_left_s']} s more.")
            if self._closed is not None and now - float(self._closed[0] or 0) < 120 and _fin(self._closed[1].get("exit")):
                t = self._closed[1]
                out["closed"] = {"exit": t.get("exit"), "ret_pct": _f(t.get("ret_pct")), "reason": t.get("reason"),
                                 "time": t.get("time_out")}
                out["lines"].insert(0, f"I sold at {t.get('exit'):.2f} ({_f(t.get('ret_pct')) or 0.0:+.1f} %) at {t.get('time_out')}, "
                                       f"{_reason_words(t.get('reason'))}.")
        out["lines"] = [x for x in out.get("lines") or [] if x][:5]
        self.v = out
        return out

    @staticmethod
    def _day(cb):
        ts = [t for t in cb.trades if not t.get("adjustment")]
        w = sum(1 for t in ts if (t.get("pnl_rs") or 0) > 0)
        return {"trades": len(ts), "won": w, "pnl_rs": round(sum(t.get("pnl_rs") or 0 for t in ts))}


def _reason_words(r):
    r = (r or "").replace("COUNCIL ", "")
    return {"FWD_TRAIL": "my forward trail", "SL": "my premium stop", "TIME": "my hold clock", "TP": "my take-profit",
            "GIVEBACK": "my profit floor", "BE_LOCK": "my break-even floor", "RAMP": "my profit floor",
            "PREM_TRAIL": "my premium trail", "STALE_PTRAIL": "my premium trail (forward stale)"}.get(
        r.split(" ")[0], r.lower() or "an exit rule")
