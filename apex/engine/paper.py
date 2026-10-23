"""
Paper trading — the owner's rule exactly, on paper.

  capital = ₹1,00,000 at the start of each trading day
  lots    = floor(capital / (premium x 65))        all-in, every trade
  after each exit: capital += P&L (gross; slippage and charges ignored — owner,
  17 Oct 2026). Bid/ask at entry and exit are recorded alongside for reference.

v1 trigger (D-033), evaluated every 100 ms by each variant's book:
  1. impulse   : Nifty-futures 15-s z >= m*  (in direction d)
  2. structure : weighted basket synchrony S_d >= s*
  3. not late  : |futures move since episode onset| <= L* x sigma15, and
                 ATM IV up <= 1.5 vol points since onset
  plus: flat, inside 09:25-LAST_ENTRY (v1 15:15; 15:29 during the CAS test) (0DTE: no entries after 14:45), once per episode.
Exits (the only four):
  * stop      : futures moves d* against the entry
  * trail     : once futures is +d* (1R) in favour, stop = best - d*
  * thesis    : synchrony flips — opposite-direction S >= s* with z >= 1 against
  * time      : flat at FLATTEN_AT (v1 15:25; 15:35 during the CAS test); 0DTE flat at 15:00 unless |delta| >= 0.9
Advisors' would-have verdicts are stored with every trade for the learning loop.
"""
import json
import math
import os
import random
import time
from datetime import date

import numpy as np

from .. import config

LAST_LOAD_ERROR = ""        # C-43: why the last load_books() found no usable books ("" = fine)
_REPLACE_TRIES = 5          # C-99: Windows (AV / indexer / OneDrive) can briefly lock the target
_REPLACE_WAIT_S = 0.2


class Book:
    def __init__(self, name, params, day):
        self.name = name
        self.p = dict(params)
        self.day = day
        self.capital = config.START_CAPITAL
        self.pos = None
        self.trades = []
        self.fired_episodes = set()
        self.blocked = ""
        self.ctl = {}              # control-book scratch (not persisted): momentum arming, pending fire

    # ── persistence ────────────────────────────────────────────────────────
    def to_json(self):
        # D-124: what a same-day restart must not forget — the last exit time (cool-down) and the spot
        # book's "one trade per swing" mark — travels with the book
        return {"name": self.name, "p": self.p, "day": self.day, "capital": self.capital,
                "pos": self.pos, "trades": self.trades, "fired": sorted(self.fired_episodes),
                "last_exit_s": getattr(self, "last_exit_s", None), "swing_last": self.ctl.get("swing_last"),
                "pb_done": self.ctl.get("pb_done"), "orb_done": self.ctl.get("orb_done")}

    @classmethod
    def from_json(cls, d):
        b = cls(d["name"], d["p"], d["day"])
        b.capital = d["capital"]; b.pos = d["pos"]; b.trades = d["trades"]
        b.fired_episodes = set(d.get("fired", []))
        if d.get("last_exit_s") is not None:
            b.last_exit_s = d["last_exit_s"]
        if d.get("swing_last"):
            b.ctl["swing_last"] = d["swing_last"]
        if d.get("pb_done"):
            b.ctl["pb_done"] = d["pb_done"]
        if d.get("orb_done"):
            b.ctl["orb_done"] = d["orb_done"]
        return b

    # ── stats ──────────────────────────────────────────────────────────────
    def stats(self):
        pts = [t["pnl_pts"] for t in self.trades]
        wins = [x for x in pts if x > 0]
        return {"name": self.name, "trades": len(pts), "wins": len(wins),
                "pnl_pts": round(sum(pts), 2),
                "pnl_rs": round(sum(t["pnl_rs"] for t in self.trades), 0),
                "capital": round(self.capital, 0),
                "win_rate": round(100.0 * len(wins) / len(pts), 1) if pts else None,
                "open": bool(self.pos)}


def entry_dir(book, ctx):
    """Direction a book would trade now: the spike leg for the straddle_spike book, else the domino's."""
    if book.p.get("spike"):
        sp = (ctx.get("straddle_watch") or {}).get("spike")
        if sp:
            return 1 if sp["leg"] == "CE" else -1
    if book.ctl.get("dir"):                  # control books decide their own direction at fire time
        return book.ctl["dir"]
    return ctx["domino"]["dir"]


def spike_leg(ctx, leg=None):
    """A leg of the anchored straddle as an option row (default: the spiking leg), or (None, reason)."""
    sw = ctx.get("straddle_watch") or {}
    if leg is None:
        sp = sw.get("spike")
        if not sp:
            return None, "no straddle spike"
        leg = sp["leg"]
    if sw.get("K") is None:
        return None, "straddle watch has no strike yet"
    now = ctx.get("now_dt")
    if now is not None and now.date().isoformat() == ctx.get("w0") \
            and config.hm(now) >= config.mins(config.ZERO_DTE_NO_ENTRY):
        # council m26: the watched straddle is this week's; on expiry day after the 0DTE cut-off a
        # leg bought now is flattened at the next step (ZERO_DTE_FLATTEN), burning the spike.
        return None, "expiry day: no 0DTE straddle-leg entries after %02d:%02d" % config.ZERO_DTE_NO_ENTRY
    o = ctx["by_key"].get(f"NIFTY|OPT|{ctx['w0']}|{int(sw['K'])}|{leg}")
    if not o or not o["ltp"]:
        return None, f"no quote for {int(sw['K'])} {leg}"
    if not (config.MIN_PREMIUM <= o["ltp"] <= config.MAX_PREMIUM):
        return None, f"{int(sw['K'])} {leg} premium {o['ltp']:.1f} outside {config.MIN_PREMIUM:.0f}-{config.MAX_PREMIUM:.0f}"
    if o["age"] >= 15:
        return None, f"{int(sw['K'])} {leg} quote is {o['age']:.0f} s old"
    return o, ""


def choose_contract(ctx, d, book=None):
    """v1 rule (D-036): DTE delta band -> nearest-the-money strike inside the band.
    The straddle_spike book buys the spiking leg itself instead.
    Returns the option dict or (None, reason)."""
    if book is not None and book.p.get("spike"):
        return spike_leg(ctx)
    if book is not None and book.p.get("momentum"):
        return spike_leg(ctx, book.ctl.get("leg"))
    now = ctx["now_dt"]
    opts = ctx["options"]                 # list of dicts with id, strike, rr, week, expiry, ltp, delta, age
    rr = "CE" if d > 0 else "PE"
    w0_exp = ctx["w0"]
    zero_dte = now.date().isoformat() == w0_exp
    hmn = config.hm(now)
    week, band = 0, None
    if zero_dte and not config.ZERO_DTE_USE_NEXTWEEK:
        # D-108 (owner): expiry day = this week's expiring contract only, until the 0DTE cut-off
        if hmn >= config.mins(config.ZERO_DTE_NO_ENTRY):
            return None, "expiry day: no entries after %02d:%02d" % config.ZERO_DTE_NO_ENTRY
        band = config.DELTA_BANDS["zero_am"]
    elif zero_dte:
        if hmn >= config.mins(config.ZERO_DTE_NO_ENTRY):
            week, band = 1, config.DELTA_BANDS["nextweek"]
        elif hmn >= config.mins(config.ZERO_DTE_NEXTWEEK_FROM):
            week, band = 1, config.DELTA_BANDS["nextweek"]
        else:
            band = config.DELTA_BANDS["zero_am"]
    else:
        dte = (np.datetime64(w0_exp) - np.datetime64(now.date().isoformat())).astype(int)
        band = config.DELTA_BANDS["ge3"] if dte >= 3 else config.DELTA_BANDS["1to2"]
    lo, hi = band
    cands = [o for o in opts if o["rr"] == rr and o["week"] == week and o.get("delta") is not None
             and o["ltp"] and config.MIN_PREMIUM <= o["ltp"] <= config.MAX_PREMIUM and o["age"] < 15]
    inband = [o for o in cands if lo <= abs(o["delta"]) <= hi]
    if inband:
        return min(inband, key=lambda o: abs(o["delta"])), ""
    above = [o for o in cands if abs(o["delta"]) >= lo]
    if above:
        # observer for O-12 (C-84): flag the out-of-band fallback on a COPY, never on the shared row
        return dict(min(above, key=lambda o: abs(o["delta"])), _fallback=True), ""
    return None, f"no {rr} in delta band {lo:.2f}-{hi:.2f}"


def _signal_snapshot(ctx, d):
    """D-115: the entry conditions as numbers, in the trade's direction, so the next review is a query."""
    dom = ctx.get("domino") or {}
    rg = ctx.get("regime") or {}
    f = lambda x: (round(float(x), 2) if x is not None and x == x else None)
    return {"r15": f((dom.get("r15") or 0.0) * d), "z": f((dom.get("z") or 0.0) * d),
            "sigma15": f(dom.get("sigma15")), "S": f(dom.get("S_up") if d > 0 else dom.get("S_dn")),
            "S_novol": f(dom.get("S_up_nv") if d > 0 else dom.get("S_dn_nv")),
            "trend30": f((ctx.get("trend30") or 0.0) * d) if ctx.get("trend30") is not None else None,
            "range5": f(ctx.get("range5")), "regime": rg.get("state"), "regime_dir": rg.get("dir"),
            "fut_mid": f(ctx.get("fut")), "fut_ltp": f(ctx.get("fut_ltp")),
            "iv_rise": f(ctx.get("iv_rise_since_onset")), "ep_type": (ctx.get("episode") or {}).get("type")}


def evaluate_spot_breakout(book, ctx):
    """D-116 (council 4, member m28 'R2'; red-teamed by m30): Nifty SPOT breaks its previous N-minute
    range -> buy the option in the break's direction. The weekly options price off spot, not off the
    27-Oct future the rest of the engine reads (19 Oct: the future ran 4-30 pts away from spot in the
    afternoon). Two numbers: the look-back (spot_dc seconds) and the spot trail (spot_trail pts, exit).
    'One trade per swing' (no parameter): after a trade, the same direction needs spot beyond that
    trade's best spot. Optional expiry-day entry end (spot_expiry_end)."""
    p = book.p
    if p.get("entry_mode") == "orb":                         # D-141 (council 9 T08): opening-range breakout
        return evaluate_orb(book, ctx)
    if p.get("entry_mode") == "pullback":                    # D-134: the pullback book has its own entry
        expiry_day = ctx["now_dt"].date().isoformat() == ctx.get("w0")
        if not (p.get("dte0_retest") and expiry_day):         # D-137: the dual book uses the retest on expiry day
            return evaluate_pullback(book, ctx)
    hi, lo, sp = ctx.get("spot_hi"), ctx.get("spot_lo"), ctx.get("spot")
    if hi is None or lo is None or sp is None:
        book.ctl.pop("rt", None)                              # D-131: an armed break does not survive a data hole
        return False, "spot range warming"
    age = ctx.get("spot_age")
    if age is not None and age > config.SPOT_STALE_S:        # D-124: a frozen index is not a breakout
        book.ctl.pop("rt", None)
        return False, f"spot quote {age:.0f} s old (limit {config.SPOT_STALE_S:.0f} s)"
    now = ctx["now_dt"]
    end = p.get("spot_expiry_end")
    if end and now.date().isoformat() == ctx.get("w0") and config.hm(now) >= config.mins(tuple(end)):
        book.ctl.pop("rt", None)
        return False, "expiry day: spot breakout stops at %02d:%02d" % tuple(end)
    ext, tol = p.get("retest_ext") or 0.0, p.get("retest_tol") or 0.0
    fail, win = p.get("retest_fail") or 0.0, p.get("retest_window_s") or 0
    rt = book.ctl.get("rt") if ext > 0 else None
    note = ""
    if rt:                                                   # D-131: a break is ARMED at its level; judge it first
        rel = (sp - rt["L"]) * rt["d"]
        side = "CE" if rt["d"] > 0 else "PE"
        if rel < -fail:
            book.ctl.pop("rt", None)
            note = f"; level {rt['L']:.1f} lost by {-rel:.1f} pts, break cancelled"
        elif ctx["now_s"] - rt["t"] > win:
            book.ctl.pop("rt", None)
            note = f"; no retest of {rt['L']:.1f} within {win} s, break cancelled"
        elif not rt["ext"]:
            if rel >= ext:
                rt["ext"] = True
                rt["ext_px"] = sp
                return False, f"{side} armed: spot {sp:.1f} is {rel:.1f} pts beyond {rt['L']:.1f}; waiting for the pullback"
            return False, f"{side} armed: waiting for spot to run {ext:.0f} pts beyond {rt['L']:.1f} (now {rel:+.1f})"
        elif rel <= tol:
            book.ctl.pop("rt", None)
            book.ctl.update({"dir": rt["d"], "fire_id": -(SPOT_ID0 + int(ctx["now_s"])), "ep_type": "SPOT-RETEST"})
            return True, (f"spot {sp:.1f} came back to the broken {p['spot_dc'] // 60}-min "
                          f"{'high' if rt['d'] > 0 else 'low'} {rt['L']:.1f} and held ({rel:+.1f} pts) after running {ext:.0f}+")
        else:
            return False, f"{side} armed: pullback to {rt['L']:.1f} awaited (spot {rel:+.1f} pts beyond, needs <= {tol:.0f})"
    d = 1 if sp > hi else (-1 if sp < lo else 0)
    if d == 0:
        return False, f"spot {sp:.1f} inside its {p['spot_dc'] // 60}-min range {lo:.1f}-{hi:.1f}" + note
    if p.get("swing", True):
        last = book.ctl.get("swing_last")       # D-122: only the LAST trade's swing counts (m28 harness rule)
        lb = last["best"] if (last and last["d"] == d) else None
        if lb is not None and (sp - lb) * d <= 0:
            return False, f"same swing: spot must pass {lb:.1f} before another {'CE' if d > 0 else 'PE'}" + note
    lvl = hi if d > 0 else lo
    if ext > 0:                                  # D-131: arm the break; do not buy the first second of it
        book.ctl["rt"] = {"d": d, "L": lvl, "t": ctx["now_s"], "ext": False}
        return False, (f"{'CE' if d > 0 else 'PE'} armed: spot {sp:.1f} broke its {p['spot_dc'] // 60}-min "
                       f"{'high' if d > 0 else 'low'} {lvl:.1f}; no entry until it runs {ext:.0f} pts and pulls back" + note)
    book.ctl.update({"dir": d, "fire_id": -(SPOT_ID0 + int(ctx["now_s"])), "ep_type": "SPOT-BREAKOUT"})
    return True, (f"spot {sp:.1f} broke its {p['spot_dc'] // 60}-min {'high' if d > 0 else 'low'} "
                  f"{lvl:.1f}")


def evaluate_pullback(book, ctx):
    """D-134 (council 7, C06): buy only the 50-78 % pullback of a >= pb_min_range impulse of the 45-min spot window, once
    per impulse; stop at the impulse origin, target one impulse beyond its extreme (see _spot_trail_exit). The window is
    ctx["pb"] from engine_main (apex/engine/impulse.py)."""
    p = book.p
    sp, v = ctx.get("spot"), ctx.get("pb") or {}
    age = ctx.get("spot_age")
    if age is not None and age > config.SPOT_STALE_S:
        return False, f"spot quote {age:.0f} s old (limit {config.SPOT_STALE_S:.0f} s)"
    end = p.get("pb_entry_end")
    if end and config.hm(ctx["now_dt"]) >= config.mins(tuple(end)):
        return False, "pullback book: no new entries after %02d:%02d" % tuple(end)
    dv = ctx.get("day") or {}
    if p.get("range_gate") and dv.get("range_on"):          # D-141 (council 9 T04): the trend is over; no trend entries
        return False, (f"range mode since {_hhmm(dv.get('range_since'))}: day {dv.get('lo') or 0:.0f}-{dv.get('hi') or 0:.0f} "
                       f"gave back 61.8 % — waiting for a new day high or low")
    if sp is None or not v.get("ok"):
        return False, "45-min spot window warming"
    rng, d = v["rng"], v["d"]
    if rng < p["pb_min_range"]:
        return False, f"no impulse: 45-min range {rng:.0f} pts < {p['pb_min_range']:.0f}"
    if not d or v.get("pbx") is None:
        return False, "no impulse direction yet"
    hi, lo = v["hi"], v["lo"]
    origin, ext_px = (lo, hi) if d > 0 else (hi, lo)
    side = "CE" if d > 0 else "PE"
    if ctx["now_s"] - v["ext_t"] < p.get("pb_min_age_s", 0):
        return False, f"{side} impulse {rng:.0f} pts still extending (extreme {ext_px:.1f})"
    key = [d, round(float(v["ext_t"]), 1)]
    if book.ctl.get("pb_done") == key:
        return False, f"{side} impulse to {ext_px:.1f} already traded; waiting for a new impulse"
    f = (ext_px - sp) * d / rng
    fmax = (ext_px - v["pbx"]) * d / rng
    z0, z1 = p["pb_zone_lo"], p["pb_zone_hi"]
    if fmax > z1 + p.get("pb_zone_slack", 0.0):
        return False, f"{side} impulse spent: the pullback reached {100 * fmax:.0f} % (> {100 * z1:.0f} %)"
    if not (z0 <= f <= z1):
        return False, (f"{side} impulse {rng:.0f} pts ({origin:.1f} -> {ext_px:.1f}): waiting for a pullback into "
                       f"{100 * z0:.0f}-{100 * z1:.0f} % (now {100 * f:.0f} %)")
    book.ctl["pb_done"] = key
    book.ctl["pb_trade"] = {"d": d, "origin": origin, "ext_px": ext_px, "rng": rng, "pbx": v["pbx"], "f": round(f, 3)}
    book.ctl.update({"dir": d, "fire_id": -(SPOT_ID0 + int(ctx["now_s"])), "ep_type": "SPOT-PULLBACK"})
    return True, (f"{side}: {rng:.0f}-pt impulse {origin:.1f} -> {ext_px:.1f} pulled back {100 * f:.0f} % to {sp:.1f}; "
                  f"stop {origin:.1f}, target {ext_px + d * p['pb_ext'] * rng:.1f}")


def _hhmm(t):
    try:
        from datetime import datetime as _dt
        return _dt.fromtimestamp(float(t), config.IST).strftime("%H:%M")
    except Exception:
        return "?"


def evaluate_orb(book, ctx):
    """D-141 (council 9 T08; ideas from Crabel's ORB, OpenAlgo's 09:15 Nifty ORB, Zarattini's ORB, CPR/pivot booking):
    the opening range is 09:15 to 09:15 + OR_WINDOW_S; the first break above it buys a CE, below it a PE; one trade per
    direction; stop when spot crosses back through the opposite edge; book at the first classic level >= orb_gap beyond the
    entry (see _spot_trail_exit). Entries end at pb_entry_end."""
    p = book.p
    sp, dv = ctx.get("spot"), ctx.get("day") or {}
    age = ctx.get("spot_age")
    if age is not None and age > config.SPOT_STALE_S:
        return False, f"spot quote {age:.0f} s old (limit {config.SPOT_STALE_S:.0f} s)"
    end = p.get("pb_entry_end")
    if end and config.hm(ctx["now_dt"]) >= config.mins(tuple(end)):
        return False, "ORB: no new entries after %02d:%02d" % tuple(end)
    hi, lo = dv.get("or_hi"), dv.get("or_lo")
    if sp is None or hi is None or not dv.get("or_done"):
        return False, "opening range forming (09:15-%s)" % _hhmm((dv.get("t0") or 0) + config.OR_WINDOW_S)
    d = 1 if sp > hi else (-1 if sp < lo else 0)
    if not d:
        return False, f"spot {sp:.1f} inside the opening range {lo:.1f}-{hi:.1f}"
    done = book.ctl.setdefault("orb_done", [])
    if d in done:
        return False, f"ORB {'CE' if d > 0 else 'PE'} already taken today"
    done.append(d)
    book.ctl["orb_trade"] = {"d": d, "stop": lo if d > 0 else hi, "or_hi": hi, "or_lo": lo}
    book.ctl.update({"dir": d, "fire_id": -(SPOT_ID0 + int(ctx["now_s"])), "ep_type": "ORB"})
    return True, f"spot {sp:.1f} broke the opening range {'high' if d > 0 else 'low'} {hi if d > 0 else lo:.1f}"


def _level_book_exit(book, ctx, pos):
    """D-141 (council 9 T02/T10): book when the trade stalls at a level it cannot break. Levels ahead are fixed at entry
    (pos["lv_ahead"]). If the best spot came within lvl_near of the next level without going beyond it by more than lvl_brk,
    and spot has since given back lvl_rej from the best, BOOK."""
    p, sp, d = book.p, ctx.get("spot"), pos["dir"]
    best = pos.get("best_spot")
    if sp is None or best is None:
        return None
    for lv, lab in pos.get("lv_ahead") or []:
        g = (best - lv) * d                   # > 0: the best went beyond the level
        if -p.get("lvl_near", 5.0) <= g <= p.get("lvl_brk", 5.0):
            if (best - sp) * d >= p.get("lvl_rej", 10.0):
                return f"BOOK at {lab} {lv:.1f} (best {best:.1f} could not break it)"
            return None
        if g < -p.get("lvl_near", 5.0):
            return None                        # the next level is not reached yet; nothing beyond it matters
    return None


def _premium_book_exit(book, pos, px, o):
    """D-141 (council 9 T06): a fixed premium target / stop (prem_tgt / prem_stop %), on fresh prints only."""
    p = book.p
    if px is None or not pos.get("entry") or (o or {}).get("age") is None or o["age"] > config.EXIT_QUOTE_STALE_S:
        return None
    r = 100.0 * (px / pos["entry"] - 1.0)
    if r >= p["prem_tgt"]:
        return f"TARGET (premium +{r:.1f} %)"
    if r <= -p["prem_stop"]:
        return f"STOP (premium {r:.1f} %)"
    return None


def evaluate_fade_switch(book, ctx):
    """D-121 (council 4, m14 P1): |15-s move on the futures mid| >= imp_pts. If the futures' last-15-min
    high-low range >= range_follow, follow the move; otherwise fade it. No episode chain, no regime gate."""
    p = book.p
    r15 = (ctx.get("domino") or {}).get("r15")
    rng = ctx.get("range15")
    if r15 is None or rng is None:
        return False, "15-min range warming"
    if abs(r15) < p["imp_pts"]:
        return False, f"15-s move {r15:+.1f} < {p['imp_pts']:.0f} pts"
    s = 1 if r15 > 0 else -1
    follow = rng >= p["range_follow"]
    d = s if follow else -s
    book.ctl.update({"dir": d, "fire_id": -(FADE_ID0 + int(ctx["now_s"])),
                     "ep_type": "FOLLOW" if follow else "FADE"})
    return True, (f"15-s move {r15:+.1f}, 15-min range {rng:.0f} {'>=' if follow else '<'} "
                  f"{p['range_follow']:.0f}: {'follow' if follow else 'fade'} -> {'CE' if d > 0 else 'PE'}")


def _bracket_exit(book, ctx, pos, fut):
    """D-121 exit: +tp_pts / -sl_pts on the futures mid, or max_hold_s."""
    p = book.p
    m = (fut - pos["fut_in"]) * pos["dir"]
    if m >= p["tp_pts"]:
        return "TARGET"
    if m <= -p["sl_pts"]:
        return "STOP"
    if ctx["now_s"] - pos["t_in"] >= p["max_hold_s"]:
        return "HOLD-LIMIT"
    return None


def _premium_lock_exit(book, ctx, pos, px, o):
    """D-127 (owner): once the premium is lock_pct over entry the lock arms; from then on exit if the premium falls
    lock_trail_pct from its best. Tracked on fresh prints only. Returns a reason or None."""
    p = book.p
    P, R = p.get("lock_pct") or 0.0, p.get("lock_trail_pct") or 0.0
    if P <= 0 or R <= 0 or px is None or not pos.get("entry"):
        return None
    age = (o or {}).get("age")
    if age is None or age > config.EXIT_QUOTE_STALE_S:
        return None                                   # a stale print neither raises the best nor fires the lock
    best = max(pos.get("best_prem") or pos["entry"], px)
    pos["best_prem"] = best
    ret = 100.0 * (px / pos["entry"] - 1.0)
    pos["lock_ret_pct"] = round(ret, 2)
    if not pos.get("lock_armed") and ret >= P:
        pos["lock_armed"] = True
        pos["lock_armed_at"] = ctx["now_dt"].strftime("%H:%M:%S")
        pos["lock_armed_px"] = px
    if not pos.get("lock_armed"):
        pos["lock_floor"] = None
        return None
    floor = round(best * (1.0 - R / 100.0), 2)
    pos["lock_floor"] = floor
    if px <= floor:
        return f"LOCK ({px:.2f} fell {100.0 * (1 - px / best):.1f} % from best {best:.2f}; armed {P:+.0f} % at {pos['lock_armed_at']})"
    return None


def _spot_trail_exit(book, ctx, pos):
    """D-116 exit: trail spot_trail points behind the best SPOT since entry (also the initial stop)."""
    sp = ctx.get("spot")
    if sp is None:
        return None
    d = pos["dir"]
    pos.setdefault("spot_in", sp)
    best = pos.get("best_spot", pos["spot_in"])
    nb = max(best, sp) if d > 0 else min(best, sp)
    if nb != pos.get("best_spot"):
        pos["best_spot_t"] = ctx["now_s"]            # council 5: when the best was set (stall timer for the panel)
    best = nb
    pos["best_spot"] = best
    ob = pos.get("orb")
    if ob:                                           # D-141: ORB — stop back through the opposite edge, book at a level
        pos["stop_spot"] = ob["stop"]
        if (sp - ob["stop"]) * d <= 0:
            return "STOP (back through the opening range %.1f)" % ob["stop"]
        tgt = next(((lv, lab) for lv, lab in (pos.get("lv_ahead") or [])
                    if (lv - pos["spot_in"]) * d >= book.p.get("orb_gap", 15.0)), None)
        if tgt:
            pos["target_spot"] = tgt[0]
            if (sp - tgt[0]) * d >= 0:
                return "BOOK at %s %.1f" % (tgt[1], tgt[0])
        return None
    pb = pos.get("pb")
    if pb:                                           # D-134: structural exit of the pullback book
        stop = pb["origin"]
        tgt = pb["ext_px"] + d * book.p.get("pb_ext", 1.0) * pb["rng"]
        pos["stop_spot"], pos["target_spot"] = stop, tgt
        if (sp - stop) * d <= 0:
            return "STOP (impulse origin %.1f)" % stop
        if (sp - tgt) * d >= 0:
            return "TARGET (%.1f)" % tgt
        return None
    pos["stop_spot"] = best - d * book.p["spot_trail"]
    if (best - sp) * d >= book.p["spot_trail"]:
        return "TRAIL" if (best - pos["spot_in"]) * d > 0 else "STOP"
    return None


def base_gate(book, ctx, d):
    """D-112 (owner-approved plan, 19 Oct): standing gates for every non-control book except RAW, judged in
    the direction THIS book would trade (a straddle-spike leg has its own direction). Returns a reason
    or ''. The learning loop's gates are separate and add to these."""
    if book.name in config.CONTROLS or book.name == "RAW":
        return ""
    if "regime" in config.BASE_GATES:
        rg = ctx.get("regime") or {}
        st, rd = rg.get("state"), rg.get("dir")
        if st is None:
            return "gate regime: no regime reading yet"
        if st in config.REGIME_BLOCK:
            return f"gate regime: {rg.get('text') or st.lower()}"
        if st in ("DIRECTIONAL", "BREAKOUT") and rd and rd != d:
            return f"gate regime: {rg.get('text') or st.lower()} — the other way"
    return ""


def _daily_brake(book, ctx):
    """D-113 / D-117 (council 4): the reason this book may not enter now, or ''.
    * KILL file present (data/KILL): no new entries in any book (exits keep running);
    * down DAILY_LOSS_STOP_PCT or more on the day's capital: no more entries today;
    * LOSS_STREAK_N consecutive losses: stopped for the day (D-117; was a 15-min pause, which
      sent the book straight back into the same chop — m11);
    * MAX_ENTRIES_PER_DAY entries taken: no more today (D-117);
    * expiry day: no entries after EXPIRY_ENTRY_END (D-117; the 0DTE edge on 19 Oct was the morning only).
    Control books are exempt from all but the kill switch; a book can opt out with its own flags
    (the spot-breakout books measure their own rule: no streak stop, no entry cap)."""
    kill = ctx.get("kill")
    if kill is None:                                   # T02: the engine stats the file once per step
        kill = bool(config.KILL_FILE and os.path.exists(config.KILL_FILE))
    if kill:
        return "KILL switch: no new entries (delete data/KILL to resume)"
    if book.name in config.CONTROLS:
        return ""
    if config.DAILY_LOSS_STOP_PCT > 0:
        dd = 100.0 * (book.capital / config.START_CAPITAL - 1.0)
        if dd <= -config.DAILY_LOSS_STOP_PCT:
            book.blocked = f"daily stop: {dd:+.1f} % on the day"
            return f"DAILY STOP: book is {dd:+.1f} % on the day (limit -{config.DAILY_LOSS_STOP_PCT:.0f} %)"
    n = 0 if book.p.get("no_streak_pause") else config.LOSS_STREAK_N
    if n > 0 and len(book.trades) >= n and all(t["ret_pct"] <= 0 for t in book.trades[-n:]):
        if config.LOSS_STREAK_PAUSE_S <= 0:          # D-117: 0 = stopped for the rest of the day
            book.blocked = f"{n} losses in a row: stopped for the day"
            return f"DAILY STOP: {n} losses in a row, stopped for the day"
        t_out = book.trades[-1].get("t_out")
        if t_out is not None and ctx["now_s"] - t_out < config.LOSS_STREAK_PAUSE_S:
            left = config.LOSS_STREAK_PAUSE_S - (ctx["now_s"] - t_out)
            return f"pause: {n} losses in a row, {left / 60:.0f} min left"
    cap = 0 if book.p.get("no_trade_cap") else config.MAX_ENTRIES_PER_DAY
    if cap > 0 and len(book.trades) + (1 if book.pos else 0) >= cap:
        return f"DAILY STOP: {cap} entries taken today (limit)"
    end = config.EXPIRY_ENTRY_END
    now = ctx.get("now_dt")
    if end and not book.p.get("expiry_window_exempt") and now is not None \
            and now.date().isoformat() == ctx.get("w0") and config.hm(now) >= config.mins(end):
        return "expiry day: no new entries after %02d:%02d" % tuple(end)
    return ""


def _fx(ctx):
    """D-109: the futures price exits are measured on — the bid/ask mid when available."""
    if config.FUT_EXIT_ON_MID and ctx.get("fut_mid"):
        return float(ctx["fut_mid"])
    return ctx["fut"]


def _sync(p, dom, d):
    """Synchrony in direction d. D-100: a `novol` variant reads S without the per-stock volume test."""
    if p.get("novol"):
        return dom.get("S_up_nv", 0.0) if d > 0 else dom.get("S_dn_nv", 0.0)
    return dom["S_up"] if d > 0 else dom["S_dn"]


def evaluate_entry(book, ctx, gates):
    """Returns (fire: bool, reason: str). One composite condition, one reason."""
    p = book.p
    dom = ctx["domino"]
    ep = ctx["episode"]
    now = ctx["now_dt"]
    hmn = config.hm(now)
    if p.get("momentum"):
        _momentum_rearm(book, ctx)
    if book.pos is not None:
        return False, "in position"
    if book.ctl.get("pending_entry"):
        return False, "entry pending"
    if hmn < config.mins(config.SUPPRESS_UNTIL) or hmn >= config.mins(config.LAST_ENTRY):
        return False, "outside entry window"
    bo = ctx.get("blackout") or {}
    if bo.get("on"):                         # D-063: no entry on frozen or just-resumed data
        return False, f"DATA GAP: {bo.get('why') or 'feed recovering'}"
    last_x = getattr(book, "last_exit_s", None)
    cool = p.get("cooldown_s", config.REENTRY_COOLDOWN_S)
    if last_x is not None and cool > 0 and ctx["now_s"] - last_x < cool:
        # D-109 (owner): no re-entry for 60 s after any exit — on 19 Oct the books flipped PE -> CE in 1 s
        return False, f"cool-down: {cool - (ctx['now_s'] - last_x):.0f} s after the last exit"
    brake = _daily_brake(book, ctx)          # D-113: per-book daily loss stop and losing-streak pause
    if brake:
        return False, brake
    if p.get("spot_dc"):                     # D-116: council-4 spot breakout book
        return evaluate_spot_breakout(book, ctx)
    if p.get("fade_switch"):                 # D-121: council-4 m14 follow/fade switch (shadow)
        return evaluate_fade_switch(book, ctx)
    if p.get("spike"):                       # straddle_spike book: the owner's gamma-leg idea
        return evaluate_spike_entry(book, ctx, gates)
    if p.get("random"):                      # control: random entry time, same exits
        return evaluate_random_entry(book, ctx)
    if p.get("momentum"):                    # control: raw premium momentum, no theta model
        return evaluate_momentum_entry(book, ctx, gates)
    if ep is None:
        return False, "no episode"
    if ep.get("gap"):
        return False, "episode began in a data gap"
    if ep["id"] in book.fired_episodes:
        return False, "already traded this episode"
    d = dom["dir"]
    if d != ep["dir"]:
        return False, "impulse against the episode"
    z = dom["z"] * d
    S = _sync(p, dom, d)
    gap = dom.get("gap", 0.0) * d
    if p.get("gap_star"):                    # basket-gap variant: the basket leads, futures lag
        if gap < p["gap_star"]:
            return False, f"basket gap {gap:.1f} < {p['gap_star']}"
        if z < p["m_star"]:
            return False, f"impulse z {z:.1f} < {p['m_star']}"
    elif z < p["m_star"]:
        return False, f"impulse z {z:.1f} < {p['m_star']}"
    r15 = abs(dom["r15"]) if dom.get("r15") is not None else None
    if config.MIN_IMPULSE_PTS > 0 and r15 is not None and r15 < config.MIN_IMPULSE_PTS:
        # D-109 (owner): in a quiet market sigma15 shrinks to ~5 pts and a 10-pt wiggle reads z = 2
        return False, f"impulse {r15:.0f} pts < {config.MIN_IMPULSE_PTS:.0f} pt floor"
    if S < p["s_star"]:
        return False, f"synchrony {S:.2f} < {p['s_star']}"
    if p.get("trend"):                       # D-114 variant: only with the 30-min futures direction
        tr = ctx.get("trend30")
        if tr is None:
            return False, "trend: 30-min history not ready"
        if tr * d < config.TREND_MIN_PTS:
            return False, f"trend: 30-min move {tr:+.0f} pts is not with the {'UP' if d > 0 else 'DOWN'} impulse"
    moved = abs(ctx["fut"] - ep["fut0"])
    if moved > p["L_star"] * dom["sigma15"]:
        return False, f"LATE: futures already {moved:.0f} pts since onset"
    # O-1 (owner, 18 Oct): the trigger keeps the nearest-strike IV rise; the pre-registered variant
    # "iv_interp" applies the same frozen 1.5-pt cap to IV interpolated at the forward instead.
    iv_rise = ctx.get("iv_rise_interp") if p.get("iv_interp") else ctx.get("iv_rise_since_onset")
    if iv_rise is not None and iv_rise > config.IV_RISE_CAP:
        return False, f"LATE: ATM IV +{iv_rise:.1f} since onset"
    bg = base_gate(book, ctx, d)             # D-112
    if bg:
        return False, bg
    for g in gates:                         # advisors promoted by the learning loop
        if ctx["advisors"].get(g, {}).get("veto"):
            return False, f"gate {g}: {ctx['advisors'][g]['why']}"
    return True, (f"{ep['type'].lower()} move {'UP' if d > 0 else 'DOWN'}: futures z {z:.1f}, "
                  f"synchrony {S:.0%}, first mover {ep['first'] or '—'}, "
                  f"{moved:.0f} pts since onset")


def evaluate_spike_entry(book, ctx, gates):
    """straddle_spike book: a directional spike on the anchored straddle, caught early,
    with the carrying leg's delta rising. One trade per spike (spike ids are stored
    negated in fired_episodes so they never collide with episode ids)."""
    sw = ctx.get("straddle_watch") or {}
    sp = sw.get("spike")
    if not sp:
        return False, f"straddle {sw.get('state', 'warming').lower()}"
    if -int(sp["id"]) in book.fired_episodes:
        return False, "already traded this spike"
    if int(sp["id"]) in (ctx.get("tainted_spikes") or ()):
        return False, "spike began in or just after a data gap"
    if sp.get("age", 0.0) > config.SPIKE_ENTRY_MAX_AGE_S:
        return False, f"LATE: spike is {sp['age']:.0f} s old"
    leg = (sw.get("legs") or {}).get(sp["leg"]) or {}
    dd = leg.get("ddelta")
    if dd is None or dd < config.SPIKE_MIN_DDELTA:
        return False, f"{sp['leg']} delta not rising ({dd})"
    bg = base_gate(book, ctx, 1 if sp["leg"] == "CE" else -1)     # D-112
    if bg:
        return False, bg
    for g in gates:
        if ctx["advisors"].get(g, {}).get("veto"):
            return False, f"gate {g}: {ctx['advisors'][g]['why']}"
    return True, (f"straddle {sw['K']:.0f} spiked +{sp['peak_excess']:.1f} over theta; {sp['leg']} leg carries it "
                  f"(delta {leg.get('delta5')}→{leg.get('delta')}, gamma {leg.get('gamma')}), {sp['age']:.0f} s in")


# ── control books (D-065): they can never become champion; they exist to be beaten ──
RANDOM_ID0 = 10 ** 7             # fired ids for control books, negative and clear of spike ids
SPOT_ID0 = 3 * 10 ** 10          # D-116 spot-breakout fire ids
FADE_ID0 = 4 * 10 ** 10          # D-121 fade-switch fire ids
MOMENTUM_ID0 = 2 * 10 ** 7


def _sod(now_dt):
    return now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second


def random_schedule(day, name):
    """Deterministic (per day and book) Poisson schedule of entry times, seconds of day,
    uniformly inside the entry window — reproducible in replay."""
    rng = random.Random(f"{day}:{name}")
    lo = config.mins(config.SUPPRESS_UNTIL) * 60
    hi = config.mins(config.LAST_ENTRY) * 60
    n, t = 0, 0.0
    lam = config.RANDOM_ENTRIES_PER_DAY
    while True:                              # Poisson count by exponential gaps on [0, 1)
        t += rng.expovariate(lam)
        if t >= 1.0:
            break
        n += 1
    return sorted(int(rng.uniform(lo, hi)) for _ in range(n))


def evaluate_random_entry(book, ctx):
    if "sched" not in book.ctl:
        book.ctl["sched"] = random_schedule(book.day, book.name)
    sod = _sod(ctx["now_dt"])
    # council m15: a slot missed while entries were blocked (data gap, in a trade) is deferred to the
    # next allowed moment instead of expiring after 60 s; when several are pending only the latest
    # fires and the older ones are recorded as skipped, so a long block never causes a burst.
    skipped = book.ctl.setdefault("skipped", [])
    due = [t for t in book.ctl["sched"] if t <= sod and -(RANDOM_ID0 + t) not in book.fired_episodes
           and t not in skipped]
    if len(due) > 1:
        skipped.extend(due[:-1])
        due = due[-1:]
    if not due:
        nxt = [t for t in book.ctl["sched"] if t > sod]
        return False, (f"next random entry {nxt[0] // 3600:02d}:{nxt[0] % 3600 // 60:02d}" if nxt else "no more random entries today")
    r60 = ctx.get("fut_r60")
    if (ctx.get("blackout") or {}).get("settling_s", 0.0) > 240.0:
        return False, "DATA GAP: 1-min window settling"
    if not r60:
        return False, "no futures move to take a side from"
    t = due[0]
    book.ctl.update({"dir": 1 if r60 > 0 else -1, "fire_id": -(RANDOM_ID0 + t), "ep_type": "RANDOM"})
    return True, f"random entry (scheduled {t // 3600:02d}:{t % 3600 // 60:02d}), side from futures 1-min move {r60:+.1f}"


def _momentum_thr(sw):
    px = sw.get("px") or 0.0
    return max(config.SPIKE_MIN_PTS, config.SPIKE_MIN_FRAC * px)


def _momentum_rearm(book, ctx):
    sw = ctx.get("straddle_watch") or {}
    legs = sw.get("legs") or {}
    armed = book.ctl.setdefault("armed", {"CE": True, "PE": True})
    thr = _momentum_thr(sw)
    for leg in ("CE", "PE"):
        c = (legs.get(leg) or {}).get("chg5")
        if c is not None and c < 0.5 * thr:
            armed[leg] = True


def evaluate_momentum_entry(book, ctx, gates):
    """Same size floors, entry window and delta-rise filter as straddle_spike, but on the
    leg's RAW 5-min rise: no theta path, no quiet-time scale, no 60/35 attribution."""
    sw = ctx.get("straddle_watch") or {}
    legs = sw.get("legs") or {}
    armed = book.ctl.setdefault("armed", {"CE": True, "PE": True})
    thr = _momentum_thr(sw)
    settle = (ctx.get("blackout") or {}).get("settling_s") or 0.0
    if settle > 0:                             # the 5-min leg change still contains the gap jump
        return False, f"DATA GAP: 5-min window settling, {settle:.0f} s left"
    cands = []
    for leg in ("CE", "PE"):
        lv = legs.get(leg) or {}
        c, dd = lv.get("chg5"), lv.get("ddelta")
        if armed.get(leg) and c is not None and c >= thr and dd is not None and dd >= config.SPIKE_MIN_DDELTA:
            cands.append((c, leg))
    if not cands:
        return False, f"no leg up {thr:.1f}+ pts in 5 min with delta rising"
    for g in gates:
        if ctx["advisors"].get(g, {}).get("veto"):
            return False, f"gate {g}: {ctx['advisors'][g]['why']}"
    c, leg = max(cands)
    armed[leg] = False
    book.ctl.update({"leg": leg, "dir": 1 if leg == "CE" else -1,
                     "fire_id": -(MOMENTUM_ID0 + _sod(ctx["now_dt"])), "ep_type": "PREMIUM-MOMENTUM"})
    return True, f"{leg} leg of {sw.get('K', 0):.0f} up {c:.1f} pts in 5 min (no theta model)"


def request_entry(book, ctx, opt, reason):
    """D-126: an entry is not filled on the print that was on the screen when the trigger fired (it predates the
    move). The book waits for the FIRST print of the contract that arrives after the trigger, at most
    ENTRY_FILL_MAX_S. Returns None (nothing opened yet); try_fill_entry completes or lapses it."""
    book.ctl["pending_entry"] = {"t": ctx["now_s"], "time": ctx["now_dt"].strftime("%H:%M:%S"), "key": opt["key"],
                                 "id": opt["id"], "why": reason, "trigger_ltp": opt.get("ltp"),
                                 "ctl": {k: book.ctl.get(k) for k in ("fire_id", "ep_type", "dir", "leg", "pb_trade", "orb_trade")}}
    return None


def try_fill_entry(book, ctx):
    """D-126: fill a pending entry on the first print after its trigger. Returns (pos|None, reason)."""
    pe = book.ctl.get("pending_entry")
    if not pe:
        return None, ""
    now = ctx["now_s"]
    waited = now - pe["t"]
    bo = ctx.get("blackout") or {}
    o = (ctx.get("by_key") or {}).get(pe["key"])
    if bo.get("on") or waited > config.ENTRY_FILL_MAX_S or (ctx.get("now_dt") is not None and
                                                             config.hm(ctx["now_dt"]) >= config.mins(config.LAST_ENTRY)):
        book.ctl.pop("pending_entry", None)
        for k in ("fire_id", "ep_type", "dir", "leg", "pb_trade", "orb_trade"):
            book.ctl.pop(k, None)
        why = "data gap" if bo.get("on") else f"no print on {pe['key'].split('|')[-2]} {pe['key'].split('|')[-1]} within {config.ENTRY_FILL_MAX_S:.0f} s"
        book.blocked = f"entry lapsed: {why}"
        return None, f"entry lapsed: {why}"
    if o is None or not o.get("ltp") or o.get("age") is None or o["age"] >= waited:
        return None, f"entry pending: waiting for a print on {pe['key'].split('|')[-2]} {pe['key'].split('|')[-1]} ({waited:.1f} s)"
    for k, v in pe["ctl"].items():                    # the direction / fire id the trigger set
        if v is not None:
            book.ctl[k] = v
    book.ctl.pop("pending_entry", None)
    pos = open_trade(book, ctx, o, pe["why"])
    if pos:
        pos["trigger_t"] = pe["t"]
        pos["trigger_time"] = pe["time"]
        pos["trigger_ltp"] = pe["trigger_ltp"]
        pos["fill_delay_s"] = round(waited, 2)
        pos["fill_slip"] = round(pos["entry"] - pe["trigger_ltp"], 2) if pe.get("trigger_ltp") else None
        return pos, pe["why"]
    return None, book.blocked or "entry rejected"


def open_trade(book, ctx, opt, reason):
    px = opt["ltp"]
    lots = int(book.capital // (px * config.LOT_SIZE))
    if lots < 1:
        book.blocked = f"premium ₹{px:.1f} unaffordable"
        return None
    d = 1 if opt["rr"] == "CE" else -1
    qty = lots * config.LOT_SIZE
    ep = ctx.get("episode") or {}
    sp = (ctx.get("straddle_watch") or {}).get("spike") if book.p.get("spike") else None
    ep_id = -int(sp["id"]) if sp else ep.get("id")
    ep_type = "STRADDLE-SPIKE" if sp else ep.get("type")
    if book.ctl.get("fire_id") is not None:          # control books carry their own id
        ep_id, ep_type = book.ctl["fire_id"], book.ctl.get("ep_type")
    book.pos = {
        "key": opt["key"], "id": opt["id"], "strike": opt["strike"], "rr": opt["rr"],
        "expiry": opt["expiry"], "lots": lots, "qty": qty, "slices": -(-qty // config.FREEZE_QTY),
        "entry": px, "entry_bid": opt.get("bid"), "entry_ask": opt.get("ask"),
        "t_in": ctx["now_s"], "time_in": ctx["now_dt"].strftime("%H:%M:%S"),
        "dir": d, "fut_in": _fx(ctx), "best": _fx(ctx), "trail": False, "fut_in_ltp": ctx["fut"], "spot_in": ctx.get("spot"),
        "delta_in": opt.get("delta"), "iv_in": opt.get("iv"),
        "why": reason, "advisors": ctx["advisors"], "episode": ep_id,
        "ep_type": ep_type, "peak_pts": 0.0, "gap": False,
        "regime": (ctx.get("regime") or {}).get("state"),
        "phase_in": config.session_phase(ctx["now_dt"]),    # D-094: CTS / CAS-ENTRY / ... (data only)
        "signal": _signal_snapshot(ctx, d),                  # D-115: what the trigger saw at entry
    }
    book.pos.update(_entry_observers(ctx, opt))
    try:                                             # D-136: the data snapshot at entry, in the trade's direction
        from .edge import signed as _edge_signed
        book.pos["edge_in"] = _edge_signed(ctx.get("edge"), d)
    except Exception:
        pass
    if book.ctl.get("pb_trade"):                     # D-134: the impulse is frozen on the position (stop/target never slide)
        book.pos["pb"] = dict(book.ctl["pb_trade"])
    if book.ctl.get("orb_trade"):                    # D-141: the opening range is frozen on the position
        book.pos["orb"] = dict(book.ctl["orb_trade"])
    if book.p.get("lvl_book") or book.p.get("entry_mode") == "orb":
        try:                                         # D-141: the levels ahead, fixed at entry
            ds, sp0 = ctx.get("day_obj"), ctx.get("spot")
            book.pos["lv_ahead"] = [[round(a, 2), b] for a, b in ds.ahead(sp0, d)] if (ds is not None and sp0) else []
        except Exception:
            book.pos["lv_ahead"] = []
    if ep_id is not None:
        book.fired_episodes.add(ep_id)
    for k in ("fire_id", "ep_type", "dir", "leg", "pb_trade", "orb_trade"):
        book.ctl.pop(k, None)
    return book.pos


def check_exit(book, ctx):
    pos = book.pos
    if pos is None:
        return None
    p = book.p
    d = pos["dir"]
    fut = _fx(ctx)
    o = ctx.get("by_key", {}).get(pos["key"])    # by KEY only: row ids are renumbered on a feed restart
    if o is None:
        cand = ctx.get("by_id", {}).get(pos["id"])
        o = cand if (cand and cand.get("key") == pos["key"]) else None
    if o and o["id"] != pos["id"]:
        pos["id"] = o["id"]                      # the contract's row moved (feed restart / re-centre)
    bo = ctx.get("blackout") or {}
    in_gap = bool(bo.get("on"))
    if in_gap:
        pos["gap"] = True
    # O-4: price decisions are frozen only while the data itself is frozen or implausible; in the resume
    # phase (fresh quotes arriving again, not after a bad print) stops and trails fire as normal.
    blackout = in_gap and not bo.get("exits_ok", False)
    px = o["ltp"] if o and o["ltp"] else None
    if px and not blackout:
        pos["last"] = px
        pos["peak_pts"] = max(pos["peak_pts"], px - pos["entry"])
    fav = (fut - pos["fut_in"]) * d
    if not blackout:                              # a frozen or implausible print must not move the trail
        pos["best"] = max(pos["best"], fut) if d > 0 else min(pos["best"], fut)
    best_fav = (pos["best"] - pos["fut_in"]) * d
    reason = None
    dom = ctx["domino"]
    if p.get("spot_trail"):                       # D-116: spot books exit on the spot trail only
        reason = None if blackout else _spot_trail_exit(book, ctx, pos)
        if p.get("prem_tgt") and not blackout:       # D-141: premium-booking books exit on the premium only
            reason = _premium_book_exit(book, pos, px, o)
        if reason is None and not blackout and p.get("lvl_book"):
            reason = _level_book_exit(book, ctx, pos)
        lock_reason = None if blackout else _premium_lock_exit(book, ctx, pos, px, o)
        if reason is None and lock_reason:
            reason = lock_reason
        elif reason and pos.get("lock_armed"):
            reason = f"{reason} (locked {p['lock_pct']:+.0f} % at {pos['lock_armed_at']})"
        sa = ctx.get("spot_age")
        if reason is None and not blackout and sa is not None and sa > config.SPOT_FROZEN_EXIT_S:
            # D-124 (review): the index has stopped arriving; a trail on a frozen number is no stop at all.
            # Fall back to the futures-mid stop/trail at spot_trail points so the position is never unprotected.
            best_fav = (pos["best"] - pos["fut_in"]) * d
            lvl = (pos["best"] - d * p["spot_trail"]) if best_fav >= p["spot_trail"] else (pos["fut_in"] - d * p["spot_trail"])
            if (fut - lvl) * d <= 0:
                reason = "STOP (futures: spot quote %.0f s old)" % sa
        S_opp = -1.0
    elif p.get("fade_switch"):                    # D-121: bracket only (no trail, no thesis-void)
        reason = None if blackout else _bracket_exit(book, ctx, pos, fut)
        S_opp = -1.0
    else:
        if best_fav >= p["d_star"]:
            pos["trail"] = True
        stop_level = (pos["best"] - d * p["d_star"]) if pos["trail"] else (pos["fut_in"] - d * p["d_star"])
        pos["stop_fut"] = stop_level
        if (fut - stop_level) * d <= 0:
            reason = "TRAIL" if pos["trail"] else "STOP"
        S_opp = _sync(dict(p, novol=True) if p.get("tv_novol") else p, dom, -d)
    if S_opp >= p.get("s_exit", p["s_star"]) and dom["z"] * d <= -1.0:
        # D-109 (owner): the flip must persist THESIS_VOID_HOLD_S, not one 100-ms reading
        pos.setdefault("tv_since", ctx["now_s"])
        if pos["tv_since"] is None:
            pos["tv_since"] = ctx["now_s"]
        if reason is None and ctx["now_s"] - pos["tv_since"] >= p.get("tv_hold_s", config.THESIS_VOID_HOLD_S):
            reason = "THESIS-VOID (synchrony flipped)"
    else:
        pos["tv_since"] = None
    if reason is None and p.get("exit_book") and o is not None:
        bk = ctx.get("book_state", {}).get(o["id"])
        # sellers refilling on the held contract (both qty and orders) while futures have stalled
        if bk and bk["opp_q"] == 1 and bk["opp_o"] == 1 and fav < 0.5 * p["d_star"] and ctx["now_s"] - pos["t_in"] > 20:
            reason = "BOOK (sellers refilled on the held contract)"
    now = ctx["now_dt"]
    hmn = config.hm(now)
    zero_dte = pos["expiry"] == now.date().isoformat()
    if reason is None and p.get("pb_flatten") and hmn >= config.mins(tuple(p["pb_flatten"])):
        reason = "TIME (%02d:%02d book flatten)" % tuple(p["pb_flatten"])
    if reason is None and hmn >= config.mins(config.FLATTEN_AT):
        reason = "TIME (%02d:%02d flatten)" % config.FLATTEN_AT
    if reason is None and zero_dte and hmn >= config.mins(config.ZERO_DTE_FLATTEN):
        if not (o and o.get("delta") is not None and abs(o["delta"]) >= 0.9):
            reason = "TIME (0DTE 15:00)"
    # D-063: never decide on frozen data. Price-driven exits wait while the futures quote is
    # stale or the engine is in blackout; a triggered exit waits (up to EXIT_DEFER_MAX_S) for a
    # fresh quote on the held option.
    timed = bool(reason) and reason.startswith("TIME")
    if reason and not timed and blackout:
        reason = None                             # not a decision: the data is frozen or implausible
    if reason is None and pos.get("pending"):    # a triggered exit is committed even if price bounces
        reason = pos["pending"]["reason"]
        timed = reason.startswith("TIME")
    fut_age = ctx.get("fut_age")
    if p.get("spot_trail") and reason and "futures:" not in reason:
        fut_age = ctx.get("spot_age", fut_age)    # D-124: a spot-priced exit waits for fresh spot; the futures fallback does not
    if reason and not timed and (blackout or (fut_age is not None and fut_age > config.EXIT_FUT_STALE_S)):
        return None
    if reason and not timed:
        age = o.get("age") if o else None
        pend = pos.setdefault("pending", {"reason": reason, "since": ctx["now_s"], "trigger_px": px})
        waited = ctx["now_s"] - pend["since"]
        if config.FILL_NEXT_PRINT:
            # D-126: fill on the first print that arrives AFTER the trigger (age < time since the trigger)
            fresh = age is not None and age < waited
        else:
            fresh = age is not None and age <= config.EXIT_QUOTE_STALE_S
        if not fresh:
            if waited < config.EXIT_DEFER_MAX_S:
                return None
            pos["stale_exit"] = True
        pos["fill_delay_s"] = round(waited, 2)
        pos["exit_trigger_px"] = pend.get("trigger_px")
    if reason and px is None:
        px = pos.get("last", pos["entry"])
        pos["stale_exit"] = True
    if reason and timed and (not o or o.get("age") is None or o["age"] > config.EXIT_QUOTE_STALE_S):
        pos["stale_exit"] = True                 # clock exits never wait, but a stale price is still flagged
    if reason:
        pos.pop("pending", None)
        return close_trade(book, ctx, px, reason, o)
    return None


def close_trade(book, ctx, px, reason, o=None):
    pos = book.pos
    pnl_pts = round(px - pos["entry"], 2)
    pnl_rs = round(pnl_pts * pos["qty"], 2)
    # D-064: under all-in sizing the account earns the RETURN ON PREMIUM, not premium points
    ret_pct = round(100.0 * (px - pos["entry"]) / pos["entry"], 3) if pos["entry"] else 0.0
    book.capital = round(book.capital + pnl_rs, 2)
    t = dict(pos)
    t.update({"exit": px, "exit_bid": (o or {}).get("bid"), "exit_ask": (o or {}).get("ask"),
              "time_out": ctx["now_dt"].strftime("%H:%M:%S"), "t_out": ctx["now_s"], "hold_s": ctx["now_s"] - pos["t_in"],
              "reason": reason, "pnl_pts": pnl_pts, "pnl_rs": pnl_rs, "ret_pct": ret_pct,
              "exit_quote_age": (o or {}).get("age"),
              "fut_out": _fx(ctx), "fut_out_ltp": ctx["fut"], "capital_after": book.capital,
              "phase_out": config.session_phase(ctx["now_dt"])})
    t.update(_exit_observers(pos, ctx, o))
    book.trades.append(t)
    book.pos = None
    book.last_exit_s = ctx["now_s"]          # D-109 cool-down
    if book.p.get("spot_dc") and pos.get("best_spot") is not None:   # D-116 one trade per swing
        book.ctl["swing_last"] = {"d": pos["dir"], "best": pos["best_spot"]}
    return t


# ── observers (C-18 / O-7, O-1, O-12, C-53): recorded only, never read by a decision ──
def _num(x):
    """A finite float, else None (NaN / None / junk never reach the record)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _trade_age(now_s, row):
    ltt = _num((row or {}).get("ltt"))
    now = _num(now_s)
    return round(now - ltt, 3) if (ltt and ltt > 0 and now is not None) else None


def _mid(row):
    bid, ask = _num((row or {}).get("bid")), _num((row or {}).get("ask"))
    return round((bid + ask) / 2.0, 4) if (bid and ask and bid > 0 and ask > 0) else None


def _entry_observers(ctx, opt):
    try:
        try:
            dte = (date.fromisoformat(str(opt.get("expiry"))) - ctx["now_dt"].date()).days   # calendar days
        except Exception:
            dte = None
        return {"trade_age_in": _trade_age(ctx.get("now_s"), opt), "mid_in": _mid(opt),
                "iv_rise_in": ctx.get("iv_rise_since_onset"), "iv_rise_interp_in": ctx.get("iv_rise_interp"),
                "dte_in": dte, "band_fallback": bool(opt.get("_fallback"))}
    except Exception:                                    # an observer must never block an entry
        return {}


def _exit_observers(pos, ctx, o):
    try:
        o = o or {}
        mid_in, mid_out = _num(pos.get("mid_in")), _mid(o)
        return {"trade_age_out": _trade_age(ctx.get("now_s"), o), "mid_out": mid_out,
                "iv_out": o.get("iv"), "delta_out": o.get("delta"),
                "ret_pct_mid": round(100.0 * (mid_out - mid_in) / mid_in, 3) if (mid_in and mid_out) else None}
    except Exception:                                    # an observer must never block an exit
        return {}


# ── persistence (C-43, C-99) ─────────────────────────────────────────────────
def _replace_retry(src, dst):
    """os.replace with a short retry on PermissionError (Windows file locks). Re-raises if it never clears."""
    for i in range(_REPLACE_TRIES):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if i == _REPLACE_TRIES - 1:
                raise
            time.sleep(_REPLACE_WAIT_S)


def save_books(books, day):
    path = os.path.join(config.PAPER_DIR, f"{day}.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({n: b.to_json() for n, b in books.items()}, f, default=str)
        f.flush()
        if not config.REPLAY_FAST:                       # T02: a replay's books need no crash durability
            os.fsync(f.fileno())
    _replace_retry(tmp, path)


def _quarantine(path):
    """Move a bad books file aside so the next save cannot overwrite the evidence. Returns the new name."""
    base = f"{path}.corrupt-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
    bad, k = base, 1
    while os.path.exists(bad):                           # never overwrite earlier evidence
        bad, k = f"{base}-{k}", k + 1
    try:
        _replace_retry(path, bad)
        return bad
    except Exception:
        try:                                             # cannot move it: at least keep a copy
            import shutil
            shutil.copyfile(path, bad)
            return bad
        except Exception:
            return None


def load_books(day):
    global LAST_LOAD_ERROR
    LAST_LOAD_ERROR = ""
    path = os.path.join(config.PAPER_DIR, f"{day}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return {n: Book.from_json(v) for n, v in d.items()}
    except Exception as e:
        bad = _quarantine(path)
        LAST_LOAD_ERROR = (f"paper books {day}.json unreadable ({type(e).__name__}: {e}); "
                           f"kept as {os.path.basename(bad) if bad else 'NOT MOVED'}; starting fresh books")
        return None


def write_trades_csv(book, day):
    import csv
    path = os.path.join(config.PAPER_DIR, f"trades_{day}.csv")
    cols = ["time_in", "time_out", "rr", "strike", "expiry", "lots", "qty", "entry", "exit",
            "pnl_pts", "ret_pct", "pnl_rs", "capital_after", "reason", "ep_type", "regime", "gap", "stale_exit", "why",
            "entry_bid", "entry_ask", "exit_bid", "exit_ask", "fut_in", "fut_out", "hold_s",
            # C-100: analysis columns, appended so the existing order is unchanged
            "episode", "delta_in", "iv_in", "iv_out", "delta_out", "trade_age_in", "trade_age_out",
            "mid_in", "mid_out", "ret_pct_mid", "stop_fut", "peak_pts", "exit_quote_age", "band_fallback",
            "spot_in", "best_spot", "stop_spot",                   # D-124: the spot books' stop path
            "lock_armed", "lock_armed_at", "lock_floor", "best_prem",            # D-127: the profit lock
            "trigger_ltp", "fill_delay_s", "fill_slip", "exit_trigger_px"]       # D-126: next-print fills
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for t in book.trades:
            w.writerow(t)
    return path
