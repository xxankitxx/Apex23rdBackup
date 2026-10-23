"""
apex/engine/commentary.py — the live-trade commentary panel (council 5, team T05).

PURPOSE   While the champion holds a position, say TRUE, evidence-based things about it, once a
          second at most, with a huge template space, and keep a one-line VERDICT (HOLD / WATCH /
          EXIT-SOON) that is derived from facts only. At the exit, one TRADE REVIEW remark.

WHERE     Engine.step(): after run_books(ctx), `self._safe("commentary", lambda: self.commentary.update(ctx, self))`.
          Engine.publish(): `state["commentary"] = self.commentary.view()`.
          Engine.start_day(): `self.commentary = Commentary(day)`.
          It is an OBSERVER: it never reads anything a decision could not, and nothing reads it.

LAYERS    facts  : build_facts(ctx, eng, book)  -> dict   (~70 keys, listed in FACT_KEYS)
          rules  : TEMPLATES: list[Template]          (content teams T06/T07/T08 fill this; format below)
          select : Commentary._select(facts)          (1 per second, 3 per 10 s, warnings bypass cool-downs)
          verdict: verdict_of(facts)                  (never from mood: thresholds in trail units)
          review : review_of(trade, last_facts)       (one 'review' remark at the exit)
          tape   : paper/commentary_<day>.jsonl       (one line per remark and per verdict change)

DETERMINISM  Everything is keyed to MARKET time (ctx["now_s"]), never the wall clock. The phrasing of a
          template is chosen by crc32(f"{trade_id}:{key}:{n}") — a replay reproduces the same text.

PERFORMANCE  one evaluation = one facts build (one numpy op over 14 stocks + ~60 scalars) + ~N predicate
          lambdas. Measured in the self-test at the bottom: well under 1 ms for 150 templates.
"""
import json
import math
import os
import zlib
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

# ── tones and priorities ─────────────────────────────────────────────────────────────────────────
TONES = ("warning", "caution", "confidence", "praise", "lesson", "information")
TONE_RANK = {t: i for i, t in enumerate(TONES)}            # lower = wins a tie first
KINDS = ("entry", "premium", "trail", "basket", "greeks", "book", "structure", "time", "day", "data", "review")

MAX_PER_SEC = 1          # at most one new remark per evaluation second
MAX_PER_10S = 3          # non-warning remarks in any 10-s window
WARN_MIN_GAP_S = 15.0    # the same warning key never twice inside this, even if its watched number moved
WARN_ANY_GAP_S = 5.0     # and no two warnings of any key inside this (the panel flashes once, not continuously)
PANEL_ITEMS = 12         # remarks carried in the state blob (the panel shows 6, keeps 12 for scroll-back)
TAPE_MAX_LINES = 5000    # per day; a flapping predicate cannot fill the disk


# ── the template record (the format T06/T07/T08 must use) ──────────────────────────────────────────
@dataclass
class Template:
    key: str                                   # unique id; also the cool-down key, e.g. "iv_share"
    kind: str                                  # one of KINDS
    tone: str                                  # one of TONES
    prio: int                                  # 0..100 — ties among candidates go to the higher prio
    when: Callable[[dict], bool]               # predicate over the facts dict; must never raise on None (use f.get)
    phrasings: List[str]                       # >= 2 str.format strings over facts + slots; chosen deterministically
    cooldown_s: float = 90.0                   # the same key is silent this long after it fired ...
    step: Dict[str, float] = field(default_factory=dict)   # ... unless a watched fact moved by >= step since it fired
    min_hold_s: float = 0.0                    # not before this many seconds in the trade
    once: bool = False                         # at most once per trade
    score: Optional[Callable[[dict], float]] = None        # strength 0..1 shown to the panel (default prio/100)
    slots: Optional[Callable[[dict], dict]] = None         # extra named values for the phrasings (strings ready to print)
    note: str = ""                             # one line for the content reviewer: what evidence this remark rests on

    def pick(self, trade_id: int, n: int) -> str:
        h = zlib.crc32(f"{trade_id}:{self.key}:{n}".encode())
        return self.phrasings[h % len(self.phrasings)]


# ── formatting helpers available to every phrasing (as slots) ───────────────────────────────────────
def rs(x):
    """₹ with Indian grouping and sign: ₹1,23,456 / −₹4,560."""
    if x is None or not math.isfinite(x):
        return "—"
    n = int(round(abs(x)))
    s = str(n)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("−" if x < 0 else "") + "₹" + s


def pts(x, nd=1):
    return "—" if x is None else f"{x:+.{nd}f} pts"


def pct(x, nd=1):
    return "—" if x is None else f"{x:+.{nd}f} %"


def mins(s):
    if s is None:
        return "—"
    s = int(round(s))
    return f"{s // 60} min {s % 60:02d} s" if s >= 60 else f"{s} s"


def _n(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ── FACT LAYER ───────────────────────────────────────────────────────────────────────────────────────
FACT_KEYS = """
trade_id rr strike dir lots qty entry capital_deployed hold_s hold_min time_hms zero_dte
ltp bid ask pnl_pts pnl_rs ret_pct best_pts best_pct giveback_pts giveback_pct giveback_frac
prem_avg5 prem_vs_avg5 prem_slope60 entry_over_mid spread_in spread_now spread_typical entry_cost_rs
spot spot_in spot_fav best_spot_fav stop_spot stop_dist trail_armed locked_pts locked_rs_est stop_rs_est
spot_retrace spot_age spot_r60
delta delta_in theta_min theta_rs_min vega iv iv_in iv_chg iv_pts iv_rs iv_share theta_pts_so_far theta_rs_so_far
spot_pts_per_min_flat delta_pts atm_iv atm_iv_in atm_iv_chg
contrib helpers hurters top_helper top_helper_pts top_helper_share top_hurter top_hurter_pts n_helping n_hurting
basket_pts basket_vs_spot sync_for sync_against z_for first_mover ep_type
basis basis_in basis_chg oi_held oi_held_chg sellers_q sellers_o book_imb book_lead run_score
straddle_state straddle_px straddle_vwap straddle_in regime regime_dir regime_with wall_level wall_room wall_room_in
fut_r60 bank_z
min_to_flatten min_to_0dte flatten_hms
trades_today wins_today streak realised_rs capital day_pct best_trade_today
gap_on quote_age exit_pending pending_reason
""".split()


class _TradeMemo:
    """What the facts need from the ENTRY moment (built once per trade, keyed by pos['t_in'])."""

    def __init__(self, ctx, eng, pos):
        self.t_in = pos["t_in"]
        self.trade_id = int(round(pos["t_in"]))
        m = eng.m
        dm = eng.domino
        import numpy as np
        self.eq_px_in = m.ltp[dm.eq_ids, m.k].astype(float).copy() if len(dm.eq_ids) else np.zeros(0)
        self.N_in = float(ctx.get("spot") or ctx.get("fut") or 0.0)
        self.atm_iv_in = eng.atm_iv
        self.basis_in = (ctx["fut"] - ctx["spot"]) if ctx.get("spot") else None
        g = eng.greek.get(pos["id"], {}) or {}
        self.theta_in, self.vega_in = g.get("theta_min"), g.get("vega")
        o = (ctx.get("by_key") or {}).get(pos["key"]) or {}
        b, a = _n(o.get("bid")), _n(o.get("ask"))
        self.spread_in = (a - b) if (a and b and a >= b) else None
        # "typical" spread = median bid/ask spread across the hero contracts at entry (same chain, same minute)
        sp = []
        for i, _rr, _k in eng.heroes():
            r = (ctx.get("by_id") or {}).get(i) or {}
            bb, aa = _n(r.get("bid")), _n(r.get("ask"))
            if bb and aa and aa >= bb:
                sp.append(aa - bb)
        sp.sort()
        self.spread_typical = sp[len(sp) // 2] if sp else None
        snap = m.snap
        self.oi_in = float(snap["oi"][pos["id"]]) if snap is not None else None
        sv = eng.straddle.view()
        self.straddle_in = sv.get("px")
        dest = eng.pressure.destination(ctx.get("spot") or ctx["fut"], pos["dir"])
        self.wall_room_in = dest["room"] if dest else None
        self.prem = deque()             # (t, ltp) 1 Hz, 300 s, for the 5-min average
        self.prem_sum = 0.0


def build_facts(ctx, eng, book, memo: _TradeMemo) -> dict:
    """~70 facts, every one of them from ctx / the engine's own objects. Missing data -> None, never a guess."""
    import numpy as np
    p = book.pos
    f = {}
    now = ctx["now_s"]
    d = p["dir"]
    o = (ctx.get("by_key") or {}).get(p["key"]) or {}
    ltp = _n(o.get("ltp")) or _n(p.get("last")) or p["entry"]
    entry = p["entry"]
    qty = p["qty"]
    # identity
    f.update(trade_id=memo.trade_id, rr=p["rr"], strike=int(p["strike"]), dir=d, lots=p["lots"], qty=qty, entry=entry,
             capital_deployed=entry * qty, hold_s=now - p["t_in"], hold_min=(now - p["t_in"]) / 60.0,
             time_hms=ctx["now_dt"].strftime("%H:%M:%S"),
             zero_dte=(p["expiry"] == ctx["now_dt"].date().isoformat()))
    # premium
    best_pts = max(float(p.get("peak_pts") or 0.0), 0.0)
    pnl_pts = ltp - entry
    f.update(ltp=ltp, bid=_n(o.get("bid")), ask=_n(o.get("ask")), pnl_pts=pnl_pts, pnl_rs=pnl_pts * qty,
             ret_pct=100.0 * pnl_pts / entry, best_pts=best_pts, best_pct=100.0 * best_pts / entry,
             giveback_pts=best_pts - pnl_pts, giveback_pct=100.0 * (best_pts - pnl_pts) / entry,
             giveback_frac=((best_pts - pnl_pts) / best_pts) if best_pts > 0 else 0.0)
    # 5-min average of the held premium since entry (1 Hz samples kept by the caller) and the 60-s slope
    while memo.prem and now - memo.prem[0][0] > 300:
        memo.prem_sum -= memo.prem.popleft()[1]
    avg5 = (memo.prem_sum / len(memo.prem)) if memo.prem else None
    old60 = next((px for t, px in memo.prem if now - t <= 60), None)
    f.update(prem_avg5=avg5, prem_vs_avg5=(ltp - avg5) if avg5 else None,
             prem_slope60=(ltp - old60) if old60 is not None else None)
    mid_in = _n(p.get("mid_in"))
    b, a = f["bid"], f["ask"]
    f.update(entry_over_mid=(entry - mid_in) if mid_in else None, spread_in=memo.spread_in,
             spread_now=(a - b) if (a and b and a >= b) else None, spread_typical=memo.spread_typical,
             entry_cost_rs=((entry - mid_in) * qty) if mid_in else None)
    # spot and the stop (the champion trails SPOT: pos['best_spot'], pos['stop_spot'] are the book's own numbers)
    sp = _n(ctx.get("spot"))
    sp_in = _n(p.get("spot_in"))
    stop = _n(p.get("stop_spot"))
    best_sp = _n(p.get("best_spot"))
    spot_fav = (sp - sp_in) * d if (sp is not None and sp_in is not None) else None
    best_fav = (best_sp - sp_in) * d if (best_sp is not None and sp_in is not None) else None
    stop_dist = (sp - stop) * d if (sp is not None and stop is not None) else None
    locked = (stop - sp_in) * d if (stop is not None and sp_in is not None) else None
    g = eng.greek.get(p["id"], {}) or {}
    delta = _n(g.get("delta")); adelta = abs(delta) if delta is not None else None
    f.update(spot=sp, spot_in=sp_in, spot_fav=spot_fav, best_spot_fav=best_fav, stop_spot=stop, stop_dist=stop_dist,
             trail_armed=bool(locked is not None and locked > 0), locked_pts=locked,
             locked_rs_est=(locked * adelta * qty) if (locked is not None and adelta) else None,
             stop_rs_est=(-stop_dist * adelta * qty) if (stop_dist is not None and adelta) else None,
             spot_retrace=(best_fav - spot_fav) if (best_fav is not None and spot_fav is not None) else None,
             spot_age=_n(ctx.get("spot_age")), spot_r60=None)
    if eng.spot_hist and len(eng.spot_hist) > 1 and sp is not None:
        old = next((px for t, px in eng.spot_hist if now - t <= 60), None)
        f["spot_r60"] = (sp - old) * d if old is not None else None
    # greeks and the attribution of the gain: iv part = Δiv × vega, theta part = theta/min × minutes, rest = spot
    theta = _n(g.get("theta_min")); vega = _n(g.get("vega")); iv = _n(g.get("iv")); iv_in = _n(p.get("iv_in"))
    iv_chg = (iv - iv_in) if (iv is not None and iv_in is not None) else None
    iv_pts = (iv_chg * vega) if (iv_chg is not None and vega is not None) else None
    theta_pts = (theta * f["hold_min"]) if theta is not None else None
    f.update(delta=delta, delta_in=_n(p.get("delta_in")), theta_min=theta, theta_rs_min=(theta * qty) if theta is not None else None,
             vega=vega, iv=iv, iv_in=iv_in, iv_chg=iv_chg, iv_pts=iv_pts, iv_rs=(iv_pts * qty) if iv_pts is not None else None,
             iv_share=(iv_pts / pnl_pts) if (iv_pts is not None and pnl_pts > 0.5) else None,
             theta_pts_so_far=theta_pts, theta_rs_so_far=(theta_pts * qty) if theta_pts is not None else None,
             spot_pts_per_min_flat=(abs(theta) / adelta) if (theta is not None and adelta) else None,
             delta_pts=(pnl_pts - (iv_pts or 0.0) - (theta_pts or 0.0)),
             atm_iv=(eng.atm_iv * 100 if eng.atm_iv else None), atm_iv_in=(memo.atm_iv_in * 100 if memo.atm_iv_in else None),
             atm_iv_chg=((eng.atm_iv - memo.atm_iv_in) * 100) if (eng.atm_iv and memo.atm_iv_in) else None)
    # heavyweights since ENTRY, in Nifty points, signed in the trade's favour (+ = helping)
    dm = eng.domino
    contrib = []
    if len(dm.eq_ids) and memo.N_in and len(memo.eq_px_in) == len(dm.eq_ids):
        px = eng.m.ltp[dm.eq_ids, eng.m.k]
        with np.errstate(divide="ignore", invalid="ignore"):
            c = (dm.eq_w / 100.0) * (px / memo.eq_px_in - 1.0) * memo.N_in * d
        tiles = (dm.state or {}).get("tiles") or []
        for j, sym in enumerate(dm.eq_sym):
            v = float(c[j]) if np.isfinite(c[j]) else None
            z = (tiles[j].get("z") if j < len(tiles) else None)
            contrib.append({"sym": sym, "pts": v, "z15": (z * d) if z is not None else None, "w": float(dm.eq_w[j])})
    valid = [x for x in contrib if x["pts"] is not None]
    valid.sort(key=lambda x: -x["pts"])
    helpers = [x for x in valid if x["pts"] > 0.5][:3]
    hurters = [x for x in reversed(valid) if x["pts"] < -0.5][:3]
    basket = sum(x["pts"] for x in valid) if valid else None
    dom = ctx.get("domino") or {}
    ep = ctx.get("episode") or {}
    f.update(contrib=contrib, helpers=[x["sym"] for x in helpers], hurters=[x["sym"] for x in hurters],
             top_helper=helpers[0]["sym"] if helpers else None, top_helper_pts=helpers[0]["pts"] if helpers else None,
             top_helper_share=(helpers[0]["pts"] / basket) if (helpers and basket and basket > 0) else None,
             top_hurter=hurters[0]["sym"] if hurters else None, top_hurter_pts=hurters[0]["pts"] if hurters else None,
             n_helping=sum(1 for x in valid if x["pts"] > 0.5), n_hurting=sum(1 for x in valid if x["pts"] < -0.5),
             basket_pts=basket, basket_vs_spot=(basket - spot_fav) if (basket is not None and spot_fav is not None) else None,
             sync_for=dom.get("S_up") if d > 0 else dom.get("S_dn"), sync_against=dom.get("S_dn") if d > 0 else dom.get("S_up"),
             z_for=(dom.get("z") or 0.0) * d, first_mover=ep.get("first"), ep_type=p.get("ep_type"))
    # structure: basis, OI on the held strike, the sellers on the held contract, straddle, regime, walls
    fut = _n(ctx.get("fut"))
    basis = (fut - sp) if (fut is not None and sp is not None) else None
    snap = eng.m.snap
    oi = float(snap["oi"][p["id"]]) if snap is not None else None
    bk = (ctx.get("book_state") or {}).get(p["id"]) or {}
    from .flow import CLS
    sv = eng.straddle.view()
    rg = ctx.get("regime") or {}
    dest = eng.pressure.destination(sp or fut, d) if (sp or fut) else None
    f.update(basis=basis, basis_in=memo.basis_in, basis_chg=(basis - memo.basis_in) if (basis is not None and memo.basis_in is not None) else None,
             oi_held=oi, oi_held_chg=(oi - memo.oi_in) if (oi is not None and memo.oi_in is not None) else None,
             sellers_q=CLS[int(bk.get("opp_q", 0))], sellers_o=CLS[int(bk.get("opp_o", 0))],
             book_imb=_n(bk.get("imb")), book_lead=_n(bk.get("lead")),
             run_score=_n(eng.flow.run_score(p["id"], 1, eng.m)),
             straddle_state=sv.get("state"), straddle_px=sv.get("px"), straddle_vwap=sv.get("vwap"), straddle_in=memo.straddle_in,
             regime=rg.get("state"), regime_dir=rg.get("dir"),
             regime_with=(0 if rg.get("state") not in ("DIRECTIONAL", "BREAKOUT") else (1 if rg.get("dir") == d else -1)),
             wall_level=dest["level"] if dest else None, wall_room=dest["room"] if dest else None, wall_room_in=memo.wall_room_in,
             fut_r60=((ctx.get("fut_r60") or 0.0) * d) if ctx.get("fut_r60") is not None else None,
             bank_z=_n(getattr(eng.bank, "z", None)))
    # clocks
    from .. import config
    hm_now = config.hm(ctx["now_dt"]) + ctx["now_dt"].second / 60.0
    flat = config.ZERO_DTE_FLATTEN if f["zero_dte"] else config.FLATTEN_AT
    f.update(min_to_flatten=config.mins(flat) - hm_now, flatten_hms="%02d:%02d" % flat,
             min_to_0dte=(config.mins(config.ZERO_DTE_FLATTEN) - hm_now) if f["zero_dte"] else None)
    # the day so far
    tr = book.trades
    pnls = [t["pnl_rs"] for t in tr]
    streak = 0
    for t in reversed(tr):
        s = 1 if t["pnl_pts"] > 0 else -1
        if streak == 0 or (streak > 0) == (s > 0):
            streak += s
        else:
            break
    f.update(trades_today=len(tr), wins_today=sum(1 for x in pnls if x > 0), streak=streak, realised_rs=sum(pnls),
             capital=book.capital, day_pct=100.0 * (book.capital / config.START_CAPITAL - 1.0),
             best_trade_today=max([t["ret_pct"] for t in tr], default=None))
    # data
    f.update(gap_on=bool((ctx.get("blackout") or {}).get("on")), quote_age=_n(o.get("age")),
             exit_pending=bool(p.get("pending")), pending_reason=(p.get("pending") or {}).get("reason"))
    return f


# ── VERDICT (facts only; thresholds in units of the trail so they follow the owner's number) ─────────
LEVELS = ("HOLD", "WATCH", "EXIT-SOON")


def verdict_of(f: dict, trail: float) -> dict:
    """Returns {level, reason, score}. Each rule yields (level, strength, reason); the highest level wins,
    then the strongest reason at that level. A HOLD is ONLY ever justified by named evidence."""
    rules = []
    sd, gf, bp = f.get("stop_dist"), f.get("giveback_frac") or 0.0, f.get("best_pts") or 0.0
    if f.get("exit_pending"):
        rules.append(("EXIT-SOON", 1.0, f"exit already triggered ({f.get('pending_reason')}), waiting for a fresh quote"))
    if sd is not None and sd <= 0.25 * trail:
        rules.append(("EXIT-SOON", 0.95, f"spot is {sd:.1f} pts from the stop {f['stop_spot']:.1f}"))
    mf = f.get("min_to_flatten")
    if mf is not None and mf <= 3:
        rules.append(("EXIT-SOON", 0.9, f"{mins(mf * 60)} to the {f['flatten_hms']} flatten"))
    if bp >= 0.5 * trail and gf >= 0.6:
        rules.append(("EXIT-SOON", 0.8, f"{gf:.0%} of the best gain (+{f['best_pct']:.0f} %) is gone"))
    if (f.get("sync_against") or 0.0) >= 0.5 and f.get("z_for", 0.0) <= -1.0:
        rules.append(("EXIT-SOON", 0.75, f"the basket flipped against you: {f['sync_against']:.0%} of the weight the other way"))
    if sd is not None and sd <= 0.5 * trail:
        rules.append(("WATCH", 0.7, f"spot {sd:.1f} pts from the stop"))
    if bp >= 0.5 * trail and gf >= 0.35:
        rules.append(("WATCH", 0.6, f"given back {f['giveback_pct']:.0f} % of {f['best_pct']:.0f} %"))
    if f.get("sellers_q") == "REFILLING" and f.get("sellers_o") == "REFILLING" and (f.get("prem_slope60") or 0.0) < 0:
        rules.append(("WATCH", 0.55, "sellers are refilling on your contract and the premium is slipping"))
    if (f.get("top_hurter_pts") or 0.0) <= -3.0 and f.get("n_hurting", 0) > f.get("n_helping", 0):
        rules.append(("WATCH", 0.5, f"{f['top_hurter']} is dragging ({f['top_hurter_pts']:+.1f} pts) and more stocks hurt than help"))
    if (f.get("iv_share") or 0.0) >= 0.5:
        rules.append(("WATCH", 0.45, f"{f['iv_share']:.0%} of the gain is IV, not spot — it can leave as fast as it came"))
    if f.get("regime_with") == -1:
        rules.append(("WATCH", 0.4, f"the regime is {f['regime'].lower()} the other way"))
    if f.get("gap_on"):
        rules.append(("WATCH", 0.4, "data gap: the stop cannot be trusted until fresh quotes arrive"))
    # evidence FOR holding (only these can justify a HOLD)
    if f.get("trail_armed") and (f.get("locked_pts") or 0.0) > 0:
        rules.append(("HOLD", 0.8, f"the trail locks {f['locked_pts']:+.1f} spot pts; the stop is past your entry"))
    if (f.get("sync_for") or 0.0) >= 0.5 and f.get("z_for", 0.0) >= 0:
        rules.append(("HOLD", 0.7, f"{f['sync_for']:.0%} of the index weight is moving your way"))
    if f.get("sellers_q") in ("PULLED", "DRAIN-FAST") or f.get("sellers_o") in ("PULLED", "DRAIN-FAST"):
        rules.append(("HOLD", 0.65, f"sellers on your contract are {f['sellers_q'].lower()}"))
    if f.get("top_helper") and (f.get("top_helper_pts") or 0.0) >= 3.0 and f.get("n_helping", 0) >= f.get("n_hurting", 0):
        rules.append(("HOLD", 0.6, f"{f['top_helper']} carries {f['top_helper_pts']:+.1f} pts of this move"))
    if (f.get("spot_fav") or 0.0) > 0 and (f.get("spot_r60") or 0.0) > 0:
        rules.append(("HOLD", 0.5, f"spot {f['spot_fav']:+.1f} pts in your favour and still moving ({f['spot_r60']:+.1f} in 60 s)"))
    if not rules:
        return {"level": "WATCH", "score": 0.3, "reason": "no evidence either way yet"}
    lvl = max(rules, key=lambda r: (LEVELS.index(r[0]), r[1]))
    return {"level": lvl[0], "score": round(lvl[1], 2), "reason": lvl[2]}


# ── REVIEW at the exit ───────────────────────────────────────────────────────────────────────────────
def review_of(t: dict, f: Optional[dict]) -> str:
    """One sentence-group from the closed trade record `t` (paper.close_trade) and the last facts `f`."""
    bits = []
    mid_in = _n(t.get("mid_in"))
    if mid_in:
        over = t["entry"] - mid_in
        bits.append(f"entered {over:+.2f} over the mid" if over > 0.05 else "entered at the mid" if abs(over) <= 0.05 else f"entered {abs(over):.2f} under the mid")
    best = 100.0 * max(t.get("peak_pts") or 0.0, 0.0) / t["entry"]
    bits.append(f"best {best:+.0f} %, closed {t['ret_pct']:+.0f} % ({rs(t['pnl_rs'])}, {t['lots']} lots)")
    gb = best - t["ret_pct"]
    if gb >= 3:
        bits.append(f"gave back {gb:.0f} %")
    if f:
        if f.get("top_helper") and (f.get("top_helper_pts") or 0) >= 2:
            bits.append(f"{f['top_helper']} did the work ({f['top_helper_pts']:+.1f} pts)")
        if f.get("top_hurter") and (f.get("top_hurter_pts") or 0) <= -2:
            bits.append(f"{f['top_hurter']} fought it ({f['top_hurter_pts']:+.1f} pts)")
        if f.get("iv_pts") is not None and abs(f["iv_pts"]) >= 1.0:
            bits.append(f"IV {'gave' if f['iv_pts'] > 0 else 'took'} {abs(f['iv_pts']):.1f} pts")
        if f.get("theta_pts_so_far") is not None and f["theta_pts_so_far"] <= -0.5:
            bits.append(f"theta took {abs(f['theta_pts_so_far']):.1f} pts over {mins(t.get('hold_s'))}")
    bits.append(f"out on {t['reason'].split(' ')[0]}")
    return "This trade: " + "; ".join(bits) + "."


# ── the engine-side object ───────────────────────────────────────────────────────────────────────────
# ── CONTENT MODULES (council 5: T06 entry quality, T07 heavyweights, T08 hold/exit) ─────────────────
# Each module exports: TEMPLATES (list[Template]); optional extend_memo(memo, ctx, eng, pos),
# extend_facts(f, ctx, eng, book, memo) -> adds keys to f, entry_card(f) -> {"grade","lines"} (one module),
# review_card(t, f) -> {"lines"} (one module). A broken module is logged and skipped, never fatal.
CONTENT_MODULES = ("apex.engine.cmt_entry", "apex.engine.cmt_basket", "apex.engine.cmt_hold")


def load_content(log=None):
    import importlib
    mods = []
    for name in CONTENT_MODULES:
        try:
            mods.append(importlib.import_module(name))
        except Exception as e:                                   # pragma: no cover - content missing/broken
            if log:
                log(f"commentary: content module {name} not loaded ({type(e).__name__}: {e})")
    return mods


def all_templates(mods) -> List[Template]:
    out = list(TEMPLATES)
    seen = {t.key for t in out}
    for m in mods:
        for t in getattr(m, "TEMPLATES", []):
            if t.key in seen:
                t = Template(**{**t.__dict__, "key": f"{m.__name__.rsplit('.', 1)[-1]}.{t.key}"})
            seen.add(t.key)
            out.append(t)
    return out


class Commentary:
    def __init__(self, day: str, templates: Optional[List[Template]] = None, paper_dir: Optional[str] = None, log=None):
        self.day = day
        self.log = log
        self.mods = load_content(log) if templates is None else []
        self.templates = templates if templates is not None else all_templates(self.mods)
        self.entry_card = None
        self.review_card = None
        self.paper_dir = paper_dir
        self.items: deque = deque(maxlen=PANEL_ITEMS)
        self.verdict = None
        self.review = None
        self.memo: Optional[_TradeMemo] = None
        self.last_facts: Optional[dict] = None
        self._last_eval_s = -1e9
        self._fired: Dict[str, dict] = {}          # key -> {t, n, watch:{fact: value}}
        self._recent: deque = deque()               # market times of recent non-warning remarks
        self._n_today = 0
        self._tape_n = 0
        self._hold_since = None
        self.eval_ms = 0.0

    # ── lifecycle ────────────────────────────────────────────────────────────
    def update(self, ctx, eng):
        import time
        book = eng.books.get(eng.champion)
        if book is None:
            return
        now = ctx["now_s"]
        if book.pos is None:
            if self.memo is not None:                       # the trade just closed: review it once
                t = book.trades[-1] if book.trades else None
                if t and int(round(t["t_in"])) == self.memo.trade_id:
                    self._emit(ctx, Template("review", "review", "lesson", 100, lambda f: True,
                                             ["{text}"], once=True), self.last_facts or {}, {"text": review_of(t, self.last_facts)})
                    self.review = self.items[0] if self.items else None
                    for m in self.mods:
                        fn = getattr(m, "review_card", None)
                        if fn and self.review_card is None:
                            try:
                                card = fn(t, self.last_facts or {})
                                if card:
                                    self.review_card = dict(card, pnl_rs=t.get("pnl_rs"), ret_pct=t.get("ret_pct"),
                                                            time=ctx["now_dt"].strftime("%H:%M:%S"), t=round(ctx["now_s"], 1))
                                    for m2 in self.mods:            # the basket's "who made / who ruined it" lines
                                        fn2 = getattr(m2, "review_lines", None)
                                        if fn2:
                                            try:
                                                extra = [x for x in fn2(t, self.last_facts or {}, limit=2) if x]
                                                self.review_card["lines"] = list(self.review_card.get("lines") or []) + extra
                                            except Exception as e:
                                                self._warn(m2, "review_lines", e)
                                    self._tape(ctx, {"kind": "review_card", "trade_id": self.memo.trade_id, **card})
                            except Exception as e:
                                self._warn(m, "review_card", e)
                self.memo = None
                self._fired.clear(); self._recent.clear(); self._hold_since = None
            return
        t0 = time.perf_counter()
        new_trade = self.memo is None or self.memo.t_in != book.pos["t_in"]
        if new_trade:
            self.memo = _TradeMemo(ctx, eng, book.pos)       # a new trade: snapshot the entry
            for m in self.mods:
                fn = getattr(m, "extend_memo", None)
                if fn:
                    try:
                        fn(self.memo, ctx, eng, book.pos)
                    except Exception as e:
                        self._warn(m, "extend_memo", e)
            self.items.clear(); self.review = None; self.verdict = None; self.entry_card = None; self.review_card = None
            self._fired.clear(); self._recent.clear(); self._hold_since = None
            self._last_eval_s = -1e9                          # evaluate on the entry tick itself
        if now - self._last_eval_s < 1.0:
            return
        self._last_eval_s = math.floor(now)
        o = (ctx.get("by_key") or {}).get(book.pos["key"]) or {}
        px = _n(o.get("ltp"))
        if px:
            self.memo.prem.append((now, px)); self.memo.prem_sum += px
        f = build_facts(ctx, eng, book, self.memo)
        for m in self.mods:
            fn = getattr(m, "extend_facts", None)
            if fn:
                try:
                    fn(f, ctx, eng, book, self.memo)
                except Exception as e:
                    self._warn(m, "extend_facts", e)
        self.last_facts = f
        if new_trade:
            for m in self.mods:
                fn = getattr(m, "entry_card", None)
                if fn and self.entry_card is None:
                    try:
                        card = fn(f)
                        if card:
                            self.entry_card = dict(card, time=ctx["now_dt"].strftime("%H:%M:%S"))
                            self._tape(ctx, {"kind": "entry_card", "trade_id": f["trade_id"], **card})
                    except Exception as e:
                        self._warn(m, "entry_card", e)
        self._verdict(ctx, f, float(book.p.get("spot_trail") or book.p.get("d_star") or 12.0))
        self._select(ctx, f)
        self.eval_ms = (time.perf_counter() - t0) * 1000.0

    # ── verdict with upward-only hysteresis (a warning is immediate; a calm-down needs 3 s) ─────
    def _verdict(self, ctx, f, trail):
        v = verdict_of(f, trail)
        prev = self.verdict
        if prev and LEVELS.index(v["level"]) < LEVELS.index(prev["level"]):
            self._hold_since = self._hold_since if self._hold_since is not None else ctx["now_s"]
            if ctx["now_s"] - self._hold_since < 3.0:
                v = dict(prev, reason=prev["reason"])        # keep the stricter verdict a little longer
            else:
                self._hold_since = None
        else:
            self._hold_since = None
        if prev is None or prev["level"] != v["level"]:
            v["since"] = ctx["now_dt"].strftime("%H:%M:%S")
            self._tape(ctx, {"kind": "verdict", "trade_id": f["trade_id"], "level": v["level"], "reason": v["reason"], "score": v["score"]})
        else:
            v["since"] = prev.get("since")
        self.verdict = v

    # ── the selector ───────────────────────────────────────────────────────────
    def _select(self, ctx, f):
        now = ctx["now_s"]
        while self._recent and now - self._recent[0] > 10.0:
            self._recent.popleft()
        budget_ok = len(self._recent) < MAX_PER_10S
        cands = []
        for tp in self.templates:
            if tp.kind == "review" or f["hold_s"] < tp.min_hold_s:
                continue
            fired = self._fired.get(tp.key)
            if fired:
                if tp.once:
                    continue
                moved = any(abs((f.get(k) or 0.0) - (fired["watch"].get(k) or 0.0)) >= st for k, st in tp.step.items())
                # a warning jumps the 10-s budget, but it still respects its own cool-down (else it chatters every
                # second while its evidence holds — T08's review); a watched fact moving by `step` re-fires it
                if now - fired["t"] < tp.cooldown_s and not moved:
                    continue
                if tp.tone == "warning" and now - fired["t"] < WARN_MIN_GAP_S:
                    continue
            if tp.tone == "warning" and now - getattr(self, "_last_warn_t", -1e9) < WARN_ANY_GAP_S:
                continue
            if tp.tone != "warning" and not budget_ok:
                continue
            try:
                if not tp.when(f):
                    continue
            except Exception:
                continue                                     # a content bug silences one template, never the panel
            cands.append(tp)
        if not cands:
            return
        best = min(cands, key=lambda tp: (TONE_RANK[tp.tone] if tp.tone == "warning" else 1, -tp.prio, tp.key))
        self._emit(ctx, best, f)

    def _emit(self, ctx, tp: Template, f: dict, extra: Optional[dict] = None):
        fired = self._fired.setdefault(tp.key, {"t": -1e9, "n": 0, "watch": {}})
        n = fired["n"]
        slots = dict(f)
        if tp.slots:
            try:
                slots.update(tp.slots(f))
            except Exception:
                pass
        if extra:
            slots.update(extra)
        try:
            text = tp.pick(f.get("trade_id", 0), n).format(**slots)
        except Exception as e:                               # a bad slot name in content: show the key, not a crash
            text = f"[{tp.key}: {type(e).__name__}]"
        score = tp.score(f) if tp.score else tp.prio / 100.0
        item = {"t": round(ctx["now_s"], 1), "time": ctx["now_dt"].strftime("%H:%M:%S"), "kind": tp.kind, "tone": tp.tone,
                "text": text, "score": round(float(score), 2), "key": tp.key, "n": n}
        self.items.appendleft(item)
        fired.update(t=ctx["now_s"], n=n + 1, watch={k: f.get(k) for k in tp.step})
        if tp.tone != "warning":
            self._recent.append(ctx["now_s"])
        else:
            self._last_warn_t = ctx["now_s"]
        self._n_today += 1
        self._tape(ctx, dict(item, trade_id=f.get("trade_id"), slots={k: f.get(k) for k in tp.step}))

    # ── the tape ──────────────────────────────────────────────────────────────
    def _tape(self, ctx, rec):
        if not self.paper_dir or self._tape_n >= TAPE_MAX_LINES:
            return
        self._tape_n += 1
        rec = dict(rec, t=round(ctx["now_s"], 1), time=ctx["now_dt"].strftime("%H:%M:%S"))
        try:
            with open(os.path.join(self.paper_dir, f"commentary_{self.day}.jsonl"), "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, default=str, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ── what the dashboard receives ─────────────────────────────────────────
    def _warn(self, m, where, e):
        key = (m.__name__, where)
        if key not in getattr(self, "_warned", set()):
            self._warned = getattr(self, "_warned", set()) | {key}
            if self.log:
                self.log(f"commentary: {m.__name__}.{where} failed ({type(e).__name__}: {e})")

    def view(self):
        v = dict(self.verdict, state=self.verdict["level"]) if self.verdict else None
        return {"trade_id": self.memo.trade_id if self.memo else None, "verdict": v,
                "items": list(self.items), "review": self.review, "entry_card": self.entry_card,
                "review_card": self.review_card, "n_today": self._n_today, "eval_ms": round(self.eval_ms, 3)}


# ── TEN WORKED TEMPLATES (the content teams add theirs to this list in the same format) ─────────────
def _help_list(f):
    hs = [x for x in (f.get("contrib") or []) if x.get("pts") is not None and x["pts"] > 0.5][:3]
    hs.sort(key=lambda x: -x["pts"])
    return {"helpers_txt": " and ".join(f"{x['sym']} ({x['pts']:+.1f})" for x in hs[:2]) or "nobody",
            "hurter_txt": f"{f['top_hurter']} ({f['top_hurter_pts']:+.1f})" if f.get("top_hurter") else "nobody"}


TEMPLATES: List[Template] = [
    Template(
        key="entry_costly", kind="entry", tone="lesson", prio=70, once=True, min_hold_s=0,
        when=lambda f: (f.get("entry_over_mid") or 0) > 0 and f.get("spread_in") and f["entry_over_mid"] >= 0.5 * f["spread_in"] + 0.05,
        phrasings=["You entered costly: {entry:.2f} is {entry_over_mid:+.2f} over the mid, that is {entry_cost_rs_txt} paid to the spread before the trade starts.",
                   "Costly fill — {entry_over_mid:+.2f} above the mid on a {spread_in:.2f} spread; the trade starts {entry_cost_rs_txt} behind.",
                   "The ask took you: {entry:.2f} vs mid {mid_txt}; {entry_cost_rs_txt} went to the spread."],
        slots=lambda f: {"entry_cost_rs_txt": rs(f.get("entry_cost_rs")), "mid_txt": (f"{f['entry'] - f['entry_over_mid']:.2f}" if f.get("entry") is not None and f.get("entry_over_mid") is not None else "—")},
        note="paper.open_trade fills at LTP; mid_in is the entry observer. Fires once, on the entry tick."),
    Template(
        key="entry_fair", kind="entry", tone="praise", prio=40, once=True,
        when=lambda f: f.get("entry_over_mid") is not None and abs(f["entry_over_mid"]) <= 0.05,
        phrasings=["Clean fill: {entry:.2f} is the mid, nothing paid to the spread.",
                   "You got the mid ({entry:.2f}); the spread cost you nothing on the way in."],
        note="the praise version of entry_costly; same observer."),
    Template(
        key="trail_lock", kind="trail", tone="confidence", prio=85, cooldown_s=60, step={"locked_pts": 3.0},
        when=lambda f: f.get("trail_armed") and (f.get("locked_pts") or 0) > 0,
        phrasings=["The premium is {ret_pct:+.0f} %; the trail now locks {locked_pts:+.0f} spot pts (≈ {locked_rs_txt}) — the stop {stop_spot:.0f} is on the right side of your entry {spot_in:.0f}.",
                   "Stop moved to {stop_spot:.0f}: {locked_pts:+.0f} spot pts are yours whatever happens next (≈ {locked_rs_txt} at delta {delta:.2f}).",
                   "Locked in: spot can come back {stop_dist:.0f} pts before the trail fires, and it fires {locked_pts:+.0f} pts beyond where you got in."],
        slots=lambda f: {"locked_rs_txt": rs(f.get("locked_rs_est"))},
        note="pos.stop_spot / pos.spot_in are the book's own numbers (D-116); the rupee figure is delta × qty, an estimate."),
    Template(
        key="basket_carry", kind="basket", tone="confidence", prio=75, cooldown_s=120, step={"top_helper_pts": 2.0}, min_hold_s=20,
        when=lambda f: f.get("top_helper") and (f.get("top_helper_pts") or 0) >= 2.0 and f.get("n_helping", 0) >= f.get("n_hurting", 0),
        phrasings=["{helpers_txt} are carrying this move; {hurter_txt} is fighting it.",
                   "The weight is with you: {n_helping} heavyweights help, {n_hurting} hurt — {top_helper} alone is {top_helper_pts:+.1f} pts of it.",
                   "{top_helper} did {top_helper_share:.0%} of the basket's {basket_pts:+.1f} pts since you entered."],
        slots=_help_list,
        note="contrib = per-stock index-weight × move since entry × Nifty level, signed in the trade's direction (domino.eq_w, m.ltp)."),
    Template(
        key="basket_turn", kind="basket", tone="warning", prio=90, cooldown_s=45, step={"top_hurter_pts": 2.0}, min_hold_s=20,
        when=lambda f: (f.get("top_hurter_pts") or 0) <= -3.0 and f.get("n_hurting", 0) > f.get("n_helping", 0),
        phrasings=["{top_hurter} is pulling the index against you ({top_hurter_pts:+.1f} pts) and {n_hurting} of the heavyweights now hurt — the move has lost its sponsors.",
                   "The basket turned: {hurter_txt} leads {n_hurting} stocks against you, only {n_helping} still help."],
        slots=_help_list,
        note="warning: bypasses the 3-per-10-s budget and the cool-down; the owner must see the evidence turn."),
    Template(
        key="sellers_pull", kind="book", tone="confidence", prio=65, cooldown_s=90,
        when=lambda f: f.get("sellers_q") in ("PULLED", "DRAIN-FAST") or f.get("sellers_o") == "PULLED",
        phrasings=["Sellers on your {strike} {rr} are {sellers_q_l} (orders {sellers_o_l}): the ask side is leaving, not being eaten.",
                   "The asks on your contract are {sellers_q_l} — quantity {sellers_q_l}, orders {sellers_o_l}, imbalance {book_imb:+.2f}."],
        slots=lambda f: {"sellers_q_l": (f.get("sellers_q") or "—").lower(), "sellers_o_l": (f.get("sellers_o") or "—").lower()},
        note="flow.side(id,+1): the asks oppose a bought contract (C-12). PULLED = shrank fast with < 25 % explained by trades."),
    Template(
        key="theta_bill", kind="greeks", tone="information", prio=50, cooldown_s=180, min_hold_s=60, step={"hold_min": 5.0},
        when=lambda f: f.get("theta_min") is not None and f.get("spot_pts_per_min_flat") is not None and f["theta_min"] < 0,
        phrasings=["Theta is eating {theta_abs:.2f} pts a minute ({theta_rs_txt}/min at {qty} qty): spot has to move {need:.1f} pts a minute your way just to stay flat.",
                   "The clock costs {theta_abs:.2f} pts/min; so far {theta_so_far:.1f} pts in {held}. Delta {delta:.2f} means {need:.1f} spot pts a minute pay for it."],
        slots=lambda f: {"theta_abs": abs(f.get("theta_min") or 0.0), "theta_rs_txt": rs(abs(f.get("theta_rs_min") or 0.0)),
                         "need": f.get("spot_pts_per_min_flat") or 0.0,
                         "theta_so_far": abs(f.get("theta_pts_so_far") or 0.0), "held": mins(f.get("hold_s"))},
        note="greeks.theta_min from compute_greeks (4 Hz). 'need' = |theta|/|delta|."),
    Template(
        key="iv_share", kind="greeks", tone="caution", prio=70, cooldown_s=120, step={"iv_share": 0.15},
        when=lambda f: (f.get("iv_share") or 0) >= 0.4 and (f.get("pnl_pts") or 0) >= 3,
        phrasings=["IV rose {iv_chg:+.1f} pts since entry — that is {iv_pts:.1f} of your {pnl_pts:.1f}-pt gain ({iv_share:.0%}). Spot earned the rest; IV can leave faster than spot.",
                   "{iv_share:.0%} of this gain is vol, not direction: contract IV {iv_in:.1f} → {iv:.1f} is worth {iv_pts:.1f} pts at vega {vega:.1f}."],
        note="iv_pts = Δiv × vega on the held contract. Caution, not warning: IV can also keep rising."),
    Template(
        key="giveback", kind="premium", tone="warning", prio=88, cooldown_s=30, step={"giveback_frac": 0.1},
        when=lambda f: (f.get("best_pts") or 0) >= 6 and (f.get("giveback_frac") or 0) >= 0.35,
        phrasings=["You have given back {giveback_pct:.0f} % of a {best_pct:+.0f} % best — the premium is {ltp:.2f} against a peak of {peak:.2f}; the trail sits {stop_dist:.0f} spot pts away.",
                   "Peak was {best_pct:+.0f} %, now {ret_pct:+.0f} %: {giveback_frac:.0%} of the gain is gone. The stop at {stop_spot:.0f} is the only thing deciding, {stop_dist:.0f} pts away."],
        slots=lambda f: {"peak": (f.get("entry") or 0.0) + (f.get("best_pts") or 0.0)},
        note="warning: the honesty rule — the panel must say when the gain is leaving, with the numbers."),
    Template(
        key="flatten_soon", kind="time", tone="warning", prio=95, cooldown_s=60, step={"min_to_flatten": 1.0},
        when=lambda f: f.get("min_to_flatten") is not None and f["min_to_flatten"] <= 5,
        phrasings=["{left} to the {flatten_hms} flatten — the book will close this at the market whatever the premium.",
                   "Clock exit in {left}: {flatten_hms} is a TIME exit, not a price one."],
        slots=lambda f: {"left": mins(max(f.get("min_to_flatten") or 0.0, 0) * 60)},
        note="config.FLATTEN_AT / ZERO_DTE_FLATTEN; same clock paper.check_exit reads."),
]


# ── self-test and benchmark (python -I commentary.py) ────────────────────────────────────────────────
if __name__ == "__main__":
    import random, time
    from datetime import datetime

    # 1. deterministic phrasing
    tp = TEMPLATES[2]
    assert tp.pick(1792382221, 0) == tp.pick(1792382221, 0) and tp.pick(1792382221, 0) != tp.pick(1792382221, 1) or len(tp.phrasings) == 1
    # 2. the selector on a synthetic facts stream (no engine needed)
    base = {k: None for k in FACT_KEYS}
    base.update(trade_id=1792382221, rr="CE", strike=25100, dir=1, lots=12, qty=780, entry=128.45, capital_deployed=100191.0,
                hold_s=0.0, hold_min=0.0, time_hms="10:19:44", zero_dte=False, ltp=128.45, bid=128.0, ask=128.5, pnl_pts=0.0,
                pnl_rs=0.0, ret_pct=0.0, best_pts=0.0, best_pct=0.0, giveback_pts=0.0, giveback_pct=0.0, giveback_frac=0.0,
                entry_over_mid=0.4, spread_in=0.5, entry_cost_rs=312.0, spot=25080.0, spot_in=25080.0, spot_fav=0.0, best_spot_fav=0.0,
                stop_spot=25068.0, stop_dist=12.0, trail_armed=False, locked_pts=-12.0, delta=0.55, theta_min=-0.04, theta_rs_min=-31.2,
                vega=12.7, iv=14.2, iv_in=14.2, iv_chg=0.0, iv_pts=0.0, spot_pts_per_min_flat=0.073, contrib=[], helpers=[], hurters=[],
                n_helping=0, n_hurting=0, sync_for=0.3, sync_against=0.0, z_for=1.2, sellers_q="HOLDING", sellers_o="HOLDING",
                min_to_flatten=300.0, flatten_hms="15:35", trades_today=3, wins_today=2, streak=2, realised_rs=12000.0,
                capital=112000.0, day_pct=12.0, gap_on=False, exit_pending=False)

    class _Ctx(dict):
        pass

    c = Commentary("2026-10-19", paper_dir=None)
    out = []
    # drive the selector directly (bypassing build_facts, which needs the engine)
    t0s = 1792385984.0
    rng = random.Random(7)
    timings = []
    for s in range(0, 400):
        f = dict(base)
        f["hold_s"], f["hold_min"] = float(s), s / 60.0
        spot = 25080 + 0.12 * s + rng.uniform(-2, 2)
        f["spot"] = spot; f["spot_fav"] = spot - 25080; f["best_spot_fav"] = max(f["best_spot_fav"] or 0, f["spot_fav"]) if s else 0
        f["best_spot_fav"] = max((base.get("best_spot_fav") or 0), 0.12 * s + 2)
        f["stop_spot"] = 25080 + f["best_spot_fav"] - 12; f["stop_dist"] = spot - f["stop_spot"]
        f["locked_pts"] = f["stop_spot"] - 25080; f["trail_armed"] = f["locked_pts"] > 0; f["locked_rs_est"] = f["locked_pts"] * 0.55 * 780
        f["ltp"] = 128.45 + 0.55 * f["spot_fav"]; f["pnl_pts"] = f["ltp"] - 128.45; f["ret_pct"] = 100 * f["pnl_pts"] / 128.45
        f["best_pts"] = 0.55 * f["best_spot_fav"]; f["best_pct"] = 100 * f["best_pts"] / 128.45
        f["giveback_pts"] = f["best_pts"] - f["pnl_pts"]; f["giveback_frac"] = f["giveback_pts"] / f["best_pts"] if f["best_pts"] > 0 else 0
        f["giveback_pct"] = 100 * f["giveback_pts"] / 128.45
        f["contrib"] = [{"sym": "HDFCBANK", "pts": 0.02 * s, "z15": 1.0, "w": 10.4}, {"sym": "RELIANCE", "pts": -0.01 * s, "z15": -0.5, "w": 7.6}]
        f["top_helper"], f["top_helper_pts"], f["n_helping"] = "HDFCBANK", 0.02 * s, 1
        f["top_hurter"], f["top_hurter_pts"], f["n_hurting"] = "RELIANCE", -0.01 * s, 1
        f["basket_pts"] = 0.01 * s; f["top_helper_share"] = 2.0
        f["iv"] = 14.2 + 0.004 * s; f["iv_chg"] = f["iv"] - 14.2; f["iv_pts"] = f["iv_chg"] * 12.7
        f["iv_share"] = f["iv_pts"] / f["pnl_pts"] if f["pnl_pts"] > 0.5 else None
        f["theta_pts_so_far"] = -0.04 * s / 60
        f["sellers_q"] = "PULLED" if 120 <= s < 150 else "HOLDING"
        ctx = _Ctx(now_s=t0s + s, now_dt=datetime(2026, 10, 19, 10, 19, 44 + 0).replace(second=(44 + s) % 60, minute=19 + (44 + s) // 60))
        t0 = time.perf_counter()
        c._verdict(ctx, f, 12.0)
        c._select(ctx, f)
        timings.append((time.perf_counter() - t0) * 1e6)
    timings.sort()
    print(f"templates {len(TEMPLATES)} · selector+verdict µs p50 {timings[len(timings)//2]:.0f} p99 {timings[int(len(timings)*0.99)]:.0f}")
    for it in reversed(list(c.items)):
        print(f"{it['time']} [{it['tone']:<11}] {it['text']}")
    print("verdict:", c.verdict)
    # 3. with 150 templates (clones) the cost must still be < 1 ms
    many = [Template(f"{t.key}_{i}", t.kind, t.tone, t.prio, t.when, t.phrasings, t.cooldown_s, t.step, t.min_hold_s, t.once, t.score, t.slots)
            for i in range(15) for t in TEMPLATES]
    c2 = Commentary("2026-10-19", templates=many)
    f = dict(base); f.update(hold_s=200.0, hold_min=3.3, trail_armed=True, locked_pts=8.0, best_pts=10.0, pnl_pts=9.0, giveback_frac=0.1, ltp=137.45)
    ts = []
    for s in range(300):
        ctx = _Ctx(now_s=t0s + s, now_dt=datetime(2026, 10, 19, 10, 25, s % 60))
        t0 = time.perf_counter(); c2._verdict(ctx, f, 12.0); c2._select(ctx, f); ts.append((time.perf_counter() - t0) * 1e6)
    ts.sort()
    print(f"{len(many)} templates · µs p50 {ts[len(ts)//2]:.0f} p99 {ts[int(len(ts)*0.99)]:.0f}")
    # 4. review text
    t = {"entry": 128.45, "mid_in": 128.225, "peak_pts": 20.35, "ret_pct": 8.8, "pnl_rs": 8775.0, "lots": 12, "reason": "TRAIL", "hold_s": 39.0}
    print(review_of(t, {"top_helper": "HDFCBANK", "top_helper_pts": 4.2, "top_hurter": "RELIANCE", "top_hurter_pts": -1.1, "iv_pts": 2.3, "theta_pts_so_far": -0.03}))
    print("state-blob bytes:", len(json.dumps(c.view(), ensure_ascii=False)))
