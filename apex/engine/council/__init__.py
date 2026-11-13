"""Council books (29 Oct 2026, owner: "a 20-member council ... few winners ... will be implemented in the system").

A council strategy is the exact class the member tested in the offline kit (scratchpad/team/kit.py): it is called
once per second with (i, D, pos) and answers None, ("BUY", strike, rr, why) or ("SELL", why). This adapter gives it
a LIVE `D` with the same fields the kit had, filled from the engine's own data each second:

    D.T, D.hm        row i = seconds since 09:15:00 IST today
    D.fwd[i]         the engine's put-call-parity forward of the nearest weekly (self.fwd), nan when stale
    D.bid/ask/age/delta/gamma/theta[i, j]   the CURRENT row only (j = the option's row id); a strategy may read
                     past rows only of the arrays it keeps itself (all council strategies keep their own history)
    D.col[(strike, rr)] -> j for the nearest weekly; D.atm(i); D.dte0; D.day; D.expiry

Orders go through the engine's own paper.open_trade / close_trade: all-in, entry/exit bid and ask recorded, so the
real-fill scoring (ask in, bid out) is the same as for every other book.
"""
import importlib
import math
from datetime import datetime

import numpy as np

from ... import config
from .. import paper

N_ROWS = 6 * 3600 + 15 * 60 + 1          # 09:15:00 .. 15:30:00


MAXC = 96                                  # option columns kept (the nearest weekly is ~60-80 contracts)
FIELDS = ("bid", "ask", "ltp", "mid", "age", "iv", "delta", "gamma", "theta", "vega", "oi", "ttq", "tbq", "tsq")


class LiveDay:
    """The kit's D, filled live: every field is a real (N_ROWS, MAXC) float32 array, forward-filled each second,
    so a strategy may read past rows exactly as it did offline (never future rows: they are still nan).
    Note: fwd[i] is NOT nan when the engine's forward is stale (> 2 s); the last value is carried forward unchanged,
    which the l2 / catch parts rely on. Do not "correct" this to nan."""

    def __init__(self, day, expiry):
        self.day, self.expiry = day, expiry
        self.dte0 = day == expiry
        y, m, d = (int(x) for x in day.split("-"))
        self.t_open = datetime(y, m, d, 9, 15, 0, tzinfo=config.IST).timestamp()
        self.T = self.t_open + np.arange(N_ROWS, dtype=float)
        self.hm = 555.0 + np.arange(N_ROWS, dtype=float) / 60.0
        self.fwd = np.full(N_ROWS, np.nan)
        self.spot = np.full(N_ROWS, np.nan)
        self.fut = np.full(N_ROWS, np.nan)
        # 14 Nov (docs/57): the sister indices and the heavyweights, one row a second, for the pre-expiry thrust books
        self.bnf = np.full(N_ROWS, np.nan)      # BANKNIFTY futures mid (quote at most PEER_AGE_S old)
        self.fin = np.full(N_ROWS, np.nan)      # FINNIFTY index
        self.hwl = None                         # (N_ROWS, stocks) log last prices; a stock older than HW_AGE_S keeps its last
        self.hww = None                         # their Nifty weights
        for f in FIELDS:
            setattr(self, f, np.full((N_ROWS, MAXC), np.nan, dtype=np.float32))
        self.col, self.ids = {}, {}            # (strike, rr) -> column; option row id -> column
        self.K = np.zeros(0)
        self.rr = np.array([], dtype="<U2")
        self.i = -1

    def i_at(self, hh, mm, ss=0):
        """Row index of the IST clock time hh:mm:ss (row 0 = 09:15:00), as the kit's D.i_at."""
        return int(min(max((hh * 3600 + mm * 60 + ss) - (9 * 3600 + 15 * 60), 0), N_ROWS - 1))

    def atm(self, i, ref=None):
        r = ref if ref is not None else (self.fwd[i] if np.isfinite(self.fwd[i]) else self.spot[i])
        if not len(self.K) or not np.isfinite(r):
            return float("nan")
        ks = np.unique(self.K)
        return float(ks[np.argmin(np.abs(ks - r))])

    def put(self, i, eng, ctx, w0, snap):
        """Write row i (forward-filled from the last row written)."""
        last = self.i
        if 0 <= last < i:                       # carry every field forward over skipped seconds
            for f in FIELDS:
                a = getattr(self, f)
                a[last + 1:i + 1] = a[last]
            for a in (self.fwd, self.spot, self.fut, self.bnf, self.fin):
                a[last + 1:i + 1] = a[last]
            if self.hwl is not None:
                self.hwl[last + 1:i + 1] = self.hwl[last]
        self.i = i
        if snap is not None:
            try:
                self._peers(i, eng, ctx, snap)
            except Exception:
                pass
        F, ft = getattr(eng, "fwd", None), getattr(eng, "_fwd_t", None)
        if F is not None and ft is not None and np.isfinite(F) and ctx["now_s"] - ft <= 2.0:
            self.fwd[i] = float(F)
        if ctx.get("spot"):
            self.spot[i] = float(ctx["spot"])
        if ctx.get("fut"):
            self.fut[i] = float(ctx["fut"])
        new = False
        for o in ctx.get("options") or ():
            if o.get("expiry") != w0 or o.get("rr") not in ("CE", "PE"):
                continue
            key = (int(o["strike"]), o["rr"])
            c = self.col.get(key)
            if c is None:
                if len(self.col) >= MAXC:
                    if not getattr(self, "_full_warned", False):     # 7 Nov: never drop contracts silently
                        self._full_warned = True
                        try:
                            from ...engine_main import log
                            log(f"council LiveDay: {MAXC} option columns full on {self.day}; "
                                f"{key[0]} {key[1]} and later contracts are not tracked")
                        except Exception:
                            pass
                    continue
                c = self.col[key] = len(self.col)
                new = True
            self.ids[o["id"]] = c
            b, a_, ltp = o.get("bid"), o.get("ask"), o.get("ltp")
            vals = {"bid": b, "ask": a_, "ltp": ltp, "age": o.get("age"), "iv": o.get("iv"),
                    "delta": o.get("delta"), "gamma": o.get("gamma"), "theta": o.get("theta_min"),
                    "vega": (eng.greek.get(o["id"]) or {}).get("vega")}
            vals["mid"] = (b + a_) / 2 if (b and a_ and a_ >= b > 0) else ltp
            if snap is not None:
                q = o["id"]
                vals.update(oi=float(snap["oi"][q]), ttq=float(snap["ttq"][q]), tbq=float(snap["tbq"][q]),
                            tsq=float(snap["tsq"][q]))
            for f, v in vals.items():
                if v is not None and v == v and not (f in ("bid", "ask", "ltp", "mid") and v <= 0):
                    getattr(self, f)[i, c] = v
            if self.age[i, c] != self.age[i, c] or vals["age"] is None:
                self.age[i, c] = 9e9
        if new:
            ks = sorted(self.col, key=self.col.get)
            self.K = np.array([float(k) for k, _ in ks])
            self.rr = np.array([r for _, r in ks])


    PEER_AGE_S, HW_AGE_S = 5.0, 30.0

    def _peers(self, i, eng, ctx, snap):
        """14 Nov (docs/57): BANKNIFTY futures mid, the FINNIFTY index and the heavyweights' last prices for row i.
        A quote older than its limit is not written, so the row keeps the last good value (as the research set did)."""
        now_ns = ctx["now_s"] * 1e9
        rn = snap["recv_ns"]
        key = getattr(eng, "key", None) or {}
        b = key.get("BANKNIFTY|FUT")
        if b is not None and rn[b] > 0 and (now_ns - float(rn[b])) / 1e9 <= self.PEER_AGE_S:
            bb, ba = float(snap["bid"][b]), float(snap["ask"][b])
            if bb > 0 and ba >= bb:
                self.bnf[i] = 0.5 * (bb + ba)
        f = key.get("FINNIFTY|SPOT")
        if f is not None and rn[f] > 0 and (now_ns - float(rn[f])) / 1e9 <= self.PEER_AGE_S and float(snap["ltp"][f]) > 0:
            self.fin[i] = float(snap["ltp"][f])
        dm = getattr(eng, "domino", None)
        if dm is not None and len(dm.eq_ids):
            ids = dm.eq_ids
            if self.hwl is None or self.hwl.shape[1] != len(ids):
                self.hwl = np.full((N_ROWS, len(ids)), np.nan, dtype=np.float32)
                self.hww = np.asarray(dm.eq_w, float)
            px = snap["ltp"][ids].astype(float)
            r = rn[ids].astype(float)
            ok = (px > 0) & (r > 0) & ((now_ns - r) / 1e9 <= self.HW_AGE_S)
            if ok.any():
                self.hwl[i, ok] = np.log(px[ok])


_DAYS = {}                                 # (day, expiry) -> the one LiveDay every council book reads


def shared_day(day, expiry):
    """5 Nov (speed): every council book used to fill its own identical LiveDay each second; they now share one
    (strategies only read D, never write it), so the row is written once per second instead of once per book."""
    key = (day, expiry)
    D = _DAYS.get(key)
    if D is None:
        for k in [k for k in _DAYS if k[0] != day]:
            del _DAYS[k]
        D = _DAYS[key] = LiveDay(day, expiry)
    return D


class Adapter:
    def __init__(self, name, day, expiry):
        mod = importlib.import_module(f"{__name__}.{name}")
        self.strat = mod.Strategy()
        self.D = shared_day(day, expiry)
        self.day, self.last_i = day, -1

    def step(self, eng, book, ctx):
        """True if the book traded this second."""
        D = self.D
        i = int(ctx["now_s"] - D.t_open)
        if i < 0 or i >= N_ROWS or i == self.last_i:
            return False
        self.last_i = i
        if D.i != i:                                         # the first council book this second writes the row
            D.put(i, eng, ctx, ctx.get("w0"), getattr(eng.m, "snap", None) if getattr(eng, "m", None) else None)
        w0 = ctx.get("w0")
        # D-126 (30 Oct review): fills wait for the first print AFTER the trigger, like every other book. While a fill
        # is pending the strategy is not stepped — the kit skipped its 2-s fill lag the same way ("catch" bridges the
        # smoothed forward through the skipped seconds).
        if book.pos:                                        # 31 Oct: the dashboard's "Best" tile and the trade record read
            o = ctx["by_key"].get(book.pos["key"])          # last / peak_pts, which only check_exit used to maintain
            ltp = (o or {}).get("ltp")
            if ltp and not (ctx.get("blackout") or {}).get("on"):
                book.pos["last"] = ltp
                book.pos["peak_pts"] = max(book.pos.get("peak_pts") or 0.0, ltp - book.pos["entry"])
                book.pos["worst_pts"] = min(book.pos.get("worst_pts") or 0.0, ltp - book.pos["entry"])   # 7 Nov
        if book.pos and book.pos.get("pending"):
            tr = paper.try_fill_exit(book, ctx)
            if tr is not None and book.p.get("reenter"):     # 11 Nov (docs/49): the re-entry twin remembers its exits
                from .. import holdtwin as _ht
                _ht.note_exit(book, tr)
            return tr is not None
        if book.ctl.get("pending_entry"):
            pos, _why = paper.try_fill_entry(book, ctx)
            if pos:
                pos["ep_type"] = "COUNCIL"
                if book.ctl.pop("re_leg_req", None):          # 11 Nov (docs/49): a re-entry leg, fixed exit
                    pos["re_leg"], pos["re_peak"], pos["ep_type"] = True, pos["entry"], "RE-ENTRY"
            return bool(pos)
        spos = None
        if book.pos:
            p = book.pos
            o = ctx["by_key"].get(p["key"])
            bid = (o or {}).get("bid")
            pk = (p["key"], p["t_in"])
            if getattr(self, "_pk", None) != pk:            # a new position (or a restart): resume the saved peak bid
                self._pk = pk
                self._peak = p.get("peak_bid") or (bid if bid else p["entry"])
                p.setdefault("peak_t", p["t_in"])
            elif bid:
                if bid > self._peak:
                    p["peak_t"] = ctx["now_s"]                 # 11 Nov (docs/49): when the peak was set (hold model input)
                self._peak = max(self._peak, bid)
            p["peak_bid"] = self._peak                       # saved with the book: an armed floor survives a restart
            flat = (15 * 60) if D.dte0 else (15 * 60 + 20)
            if p.get("re_leg"):                                # 11 Nov (docs/49): the re-entry twin's own leg
                from .. import holdtwin as _ht
                act = self.strat.on_second(i, D, None)       # the strategy keeps running as if flat
                if act and act[0] == "BUY":
                    book.ctl["rx_skipped_buys"] = int(book.ctl.get("rx_skipped_buys") or 0) + 1
                why = _ht.leg_exit(ctx, p, o, D.hm[i] >= flat)
                return bool(why) and paper.request_exit(book, ctx, why, o) is not None
            if D.hm[i] >= flat:
                return paper.request_exit(book, ctx, "TIME (council forced flat)", o) is not None
            j = D.col.get((int(p["strike"]), p["rr"]))
            if j is None:                                    # never read another contract's quote for the stop
                self._warn(f"council {book.name}: held {p['key']} has no column this second; strategy not stepped")
                return False
            spos = {"rr": p["rr"], "strike": p["strike"], "j": j,
                    "i_in": int(p["t_in"] - D.t_open), "entry": p["entry"], "qty": p["qty"],
                    "peak_bid": self._peak,                    # the kit's pos field (the premium exits read it)
                    "st": p.setdefault("st", {})}              # 1 Nov (c20_9v): a strategy's own per-position state,
                                                               # saved with the book so it survives a restart
            if book.p.get("fc_exit"):                       # 10 Nov (docs/41, P04): the forecast-exit twin
                from .. import pred as _pred
                fx = _pred.held_exit(ctx, p, self._peak)
                if fx:
                    return paper.request_exit(book, ctx, fx, o) is not None
            if book.p.get("hold_exit"):                     # 11 Nov (docs/49): the hold-or-sell twin
                from .. import holdtwin as _ht
                hx = _ht.sell_now(ctx, book, p, o, self._peak)
                if hx:
                    return paper.request_exit(book, ctx, hx, o) is not None
        act = self.strat.on_second(i, D, spos)
        if spos is not None and book.pos:
            try:
                book.pos["rules"] = self._rules(i, D, book.pos, spos)   # dashboard only (3 Nov): the real exit rules
            except Exception:
                book.pos.pop("rules", None)
        if not act:
            if book.p.get("reenter") and not book.pos and not (ctx.get("blackout") or {}).get("on") and not ctx.get("kill"):
                from .. import holdtwin as _ht                  # 11 Nov (docs/49): buy the last exit back?
                ro, rwhy = _ht.want_reentry(ctx, book)
                if ro is not None and abs(ro.get("delta") or 0) >= 0.5 and D.hm[i] < ((15 * 60) if D.dte0 else (15 * 60 + 5)):
                    book.ctl["re_leg_req"] = True
                    paper.request_entry(book, ctx, ro, rwhy)
            return False
        if act[0] == "SELL" and book.pos:
            o = ctx["by_key"].get(book.pos["key"])
            if book.p.get("fc_hold"):                       # 10 Nov (docs/41, P03): the runner twin
                from .. import pred as _pred
                if _pred.held_keep(ctx, book.pos, (o or {}).get("bid")):
                    book.pos["fc_defer"] = int(book.pos.get("fc_defer") or 0) + 1   # seconds the strategy's SELL was held back
                    return False
            why = f"COUNCIL {act[1] if len(act) > 1 else ''}".strip()
            tr = paper.request_exit(book, ctx, why, o)
            if tr is not None and book.p.get("reenter"):
                from .. import holdtwin as _ht
                _ht.note_exit(book, tr)
            return tr is not None
        if act[0] == "BUY" and not book.pos:
            if (ctx.get("blackout") or {}).get("on") or ctx.get("kill"):
                return False
            book.ctl.pop("rx_last", None)                     # a fresh strategy entry replaces any pending buy-back
            k, rr = int(act[1]), act[2]
            opt = ctx["by_key"].get(f"NIFTY|OPT|{w0}|{k}|{rr}")
            if not opt or not opt.get("ltp") or (opt.get("age") or 9e9) > config.EXIT_QUOTE_STALE_S:
                return False
            if abs(opt.get("delta") or 0) < 0.5:          # owner's ATM/ITM rule (|delta| >= 0.52 at the signal)
                return False
            why = f"COUNCIL {act[3] if len(act) > 3 else ''}".strip()
            if book.p.get("rules"):                   # 7 Nov (stage 5): a restricted council book's frozen rules
                from .. import rules as rules_mod
                if rules_mod.check(book, ctx, opt, why):
                    return False
            if config.FILL_NEXT_PRINT:
                paper.request_entry(book, ctx, opt, why)   # filled by try_fill_entry on a later second
                return False
            pos = paper.open_trade(book, ctx, opt, why)
            if pos:
                pos["ep_type"] = "COUNCIL"
            return bool(pos)
        return False

    def _rules(self, i, D, p, spos):
        """What the strategy will do with this position, for the dashboard (nothing here feeds a decision).

        3 Nov 2026: the band used to show the spot-trail / profit-lock story of the t28 books, which council books
        inherit as parameters but never run. This reads the strategy's own state: premium stop, forward trail from
        its best, the hold clock, the premium floors (break-even / give-back / rent) and the premium trail."""
        s = self.strat
        e, ce = float(p["entry"]), p["rr"] == "CE"
        sp = getattr(s, "p", None) or {}
        parts = getattr(s, "parts", ()) or ()
        x, r = getattr(s, "x", None) or {}, getattr(s, "r", None) or {}
        pk = float(spos["peak_bid"])
        g = pk / e - 1.0
        held = float(D.T[i] - D.T[spos["i_in"]])
        v = {"book": "council", "mode": "expiry" if D.dte0 else "normal",
             "sl_pct": 100.0 * sp["sl"] if sp.get("sl") else None,
             "sl_px": e * (1.0 - sp["sl"]) if sp.get("sl") else None,
             "hold_s": sp.get("hold"), "held_s": held,
             "clock_left_s": (sp["hold"] - held) if sp.get("hold") else None,
             "flat_at": "15:00" if D.dte0 else "15:20",
             "peak_bid": pk, "peak_pct": 100.0 * g}
        # the forward trail: give-back from the best smoothed forward since entry
        best = getattr(s, "best", None)
        fs = getattr(s, "fs", None)
        fnow = None
        if fs is not None and 0 <= i < len(fs) and np.isfinite(fs[i]):
            fnow = float(fs[i])
        tr = getattr(s, "trail_now", None) or sp.get("trail")
        if tr and "dtr" in parts and not D.dte0 and hasattr(s, "_fac") and hasattr(s, "_dfac"):
            tr = tr * float(getattr(s, "_fac", 1.0) or 1.0)      # the delta-scaled trail (already computed this second)
        pt_on = ("ptr" in parts) or ("ptre" in parts and D.dte0)
        spk = getattr(s, "spk", None)
        pt_arm = bool(pt_on and spk is not None and r.get("PT_PA") is not None and spk >= e * (1.0 + r["PT_PA"]))
        v.update(fwd_best=best, fwd_now=fnow, trail_pts=(tr if (tr and not pt_arm) else None),
                 trail_px=((best - tr) if ce else (best + tr)) if (best is not None and tr and not pt_arm) else None,
                 trail_give=((best - fnow) if ce else (fnow - best)) if (best is not None and fnow is not None) else None)
        # premium floors (exit when the bid is at or below the floor)
        fl = kind = None
        if hasattr(s, "_floor"):
            fl, kind = s._floor(e, g, D.dte0)
        elif x.get("GB_ARM") is not None and x.get("BE_ARM") is not None:
            if g >= x["GB_ARM"]:
                fl, kind = e * (1.0 + x["GB_KEEP"] * g), "GIVEBACK"
            elif g >= x["BE_ARM"]:
                fl, kind = e * (1.0 + x["BE_LOCK"]), "BE_LOCK"
        ramp = "ramp" in parts and not D.dte0 and r.get("R_ARM") is not None
        v.update(floor_px=fl, floor_kind=kind,
                 be_arm_pct=(100.0 * r["R_ARM"]) if ramp else ((100.0 * x["BE_ARM"]) if x.get("BE_ARM") is not None else None),
                 gb_arm_pct=None if ramp else ((100.0 * x["GB_ARM"]) if x.get("GB_ARM") is not None else None),
                 pt_arm_pct=(100.0 * r["PT_PA"]) if (pt_on and r.get("PT_PA") is not None) else None,
                 pt_armed=pt_arm,
                 pt_peak=float(spk) if pt_arm else None,
                 pt_trail_px=(float(spk) * (1.0 - r["PT_PQ"])) if (pt_arm and r.get("PT_PQ") is not None) else None,
                 pt_give_pct=(100.0 * r["PT_PQ"]) if (pt_arm and r.get("PT_PQ") is not None) else None)
        return {k: (round(val, 2) if isinstance(val, float) else val) for k, val in v.items()}

    _warned = 0

    def _warn(self, msg):
        self._warned += 1
        if self._warned <= 3:                                # at most three lines a day per book
            try:
                from ...engine_main import log
                log(msg)
            except Exception:
                pass
