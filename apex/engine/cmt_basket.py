"""
apex/engine/cmt_basket.py — commentary content, the HEAVYWEIGHT BASKET (council 5, team T07).

"Which stocks are with me, which stock ruined it." 71 templates / 185 phrasings over ONE new computation —
each tracked heavyweight's Nifty-point contribution SINCE ENTRY — plus facts the engine already has (domino z /
activity tiles, flow classes and aggressive flow, the episode's first mover).

FACTS      extend_facts() adds the `eq_*` keys listed in FACTS (the core's own contrib/helpers/hurters stay as they are).
           Everything is signed IN THE TRADE'S FAVOUR (+ = helping): a PE is helped by stocks falling.
HISTORY    the engine ring is 60 s @ 10 Hz; this module keeps its own 1-Hz per-stock ring (eq ltp, stock-future ltp,
           net aggressive flow) of 960 s in a module-level _Hist, sampled whenever extend_facts / extend_memo run.
           The pre-entry reference ("who made the breakout") is 90 s before entry when the ring has it (a previous trade
           within the last 16 min), else the market ring's 60-s-old slot.
HONESTY    (T07, one day of evidence, 19 Oct) stock futures do not lead cash at 1 Hz (best lag 0 s) and aggressive flow
           does not forecast (corr 0.00 with the next 30 s): the G/H templates are colour / present tense, low prio.
           Breadth has no monotone 60-s edge: breadth remarks DESCRIBE what carries the move; T07 warnings with prio
           >= 75 map to the core's `warning` tone (which outranks every cheer), lower ones to `caution`.
REVIEW     the L group (exit review) is kind "review": the core selector never fires it live; review_lines(t, f) renders
           them from the closed trade and the last facts for whoever builds the review card.
"""
import math
from collections import deque
from typing import List

import numpy as np

from .commentary import Template, pts

# ── knobs (cosmetic: nothing here changes when or whether the champion trades) ───────────────────────
TH_PCT = 0.0003          # "meaningful" = 0.03 % of the stock (HDFCBANK ≈ 0.7 pts, HINDUNILVR ≈ 0.13 pts at 23 000)
AIR_RATIO = 0.4          # basket / print below this with the print >= 5 pts = "air"
HIST_S = 960             # 1-Hz history kept per stock
PRE_REF_S = 90           # the breakout reference before entry
RUN_BLOCK_S = 10         # flow runs are counted in 10-s blocks
RUN_MAX_S = 120

GROUP = {"HDFCBANK": "bank", "ICICIBANK": "bank", "SBIN": "bank", "AXISBANK": "bank", "KOTAKBANK": "bank",
         "BAJFINANCE": "nbfc", "RELIANCE": "ril", "INFY": "it", "TCS": "it", "BHARTIARTL": "telecom", "LT": "infra",
         "M&M": "auto", "ITC": "fmcg", "HINDUNILVR": "fmcg"}
SECTOR_LABEL = {"bank": "Banks", "it": "IT", "ril": "RIL", "telecom": "Telecom", "infra": "L&T", "auto": "Autos",
                "fmcg": "FMCG", "nbfc": "Bajaj", "other": "Other"}
BIG_BANKS = ("HDFCBANK", "ICICIBANK")
DEFENSIVES = ("ITC", "HINDUNILVR")
_PULL, _REFILL = 5, 1    # flow.CLS indices

FACTS: List[str] = """
eq_n eq_rows eq_syms_fresh
eq_breadth_with eq_breadth_against eq_breadth_flat eq_wpct_with eq_with60 eq_breadth_chg60 eq_leavers eq_max_with
eq_spot_pts eq_basket_pts_scaled eq_gap_vs_print eq_ratio eq_basket60 eq_abs_sum
eq_concentration eq_conc_sym eq_air
eq_help_pos eq_help_neg
eq_top_sym eq_top_help eq_top_pct eq_top_share eq_top_run_with eq_top_run_against eq_top60_sym eq_top_help60
eq_top2_sym eq_top2_help eq_top2_share eq_top3_sym eq_top3_help
eq_bot_sym eq_bot_help eq_bot_pct eq_bot_run_against
eq_flips eq_flip_against eq_flip_with eq_pair_flip_banks
eq_turn eq_new_helper
eq_new_best eq_best_t eq_best_hms eq_with_at_best eq_basket_at_best eq_basket_giveback eq_print_giveback
eq_swing_sym eq_swing_giveback eq_swing_at_best eq_swing_now eq_giveback_n eq_giveback_max eq_giveback_max_sym eq_giveback_top
eq_made eq_sector_banks eq_sector_banks_with eq_sector_it eq_sector_it_with eq_sector_ril eq_sector_other eq_sector_rest
eq_sector_against eq_all_sectors_on eq_lone_sector eq_opposite_pair eq_infy eq_tcs eq_hdfc_help eq_big_bank_against
eq_fut_lead eq_basis_bps
eq_flow_with eq_flow_against eq_flow_with_wpct eq_flow_against_wpct eq_pressed_name eq_fought_name eq_top_pulled eq_refilling
eq_first_mover eq_first_mover_t eq_ep_type eq_ep_age eq_ep_ncross eq_ep_with
eq_pre_ref_s eq_pre_rows eq_pre_with eq_pre_against eq_pre_basket eq_pre_spot eq_pre_ratio eq_pre_top eq_pre_bot eq_pre_bank_with eq_pre_makers
eq_day_with eq_day_leader eq_day_leader_chg eq_day_laggard eq_day_laggard_chg
eq_wave_with eq_wave_against eq_vol_dry_n eq_hot
""".split()


# ── the 1-Hz history (module level: it must know the 90 s BEFORE an entry) ────────────────────────────
class _Hist:
    def __init__(self, n):
        self.n = n
        self.t = np.full(HIST_S, np.nan)
        self.eq = np.full((HIST_S, n), np.nan)
        self.fut = np.full((HIST_S, n), np.nan)
        self.agg = np.zeros((HIST_S, n))
        self.ptr = -1
        self.count = 0
        self.last_s = -1e9

    def sample(self, eng, now, eq_ids, fut_ids):
        if math.floor(now) <= self.last_s:
            return
        self.last_s = math.floor(now)
        m = eng.m
        self.ptr = (self.ptr + 1) % HIST_S
        self.count = min(self.count + 1, HIST_S)
        self.t[self.ptr] = now
        self.eq[self.ptr] = m.ltp[eq_ids, m.k] if len(eq_ids) else np.nan
        fl = getattr(eng, "flow", None)
        agg = np.zeros(self.n)
        for j, r in enumerate(fut_ids):
            self.fut[self.ptr, j] = m.ltp[r, m.k] if r is not None else np.nan
        if fl is not None and len(eq_ids):
            try:
                agg = np.asarray(fl.agg_b, float)[eq_ids] - np.asarray(fl.agg_s, float)[eq_ids]
            except Exception:
                agg = np.zeros(self.n)
        self.agg[self.ptr] = np.where(np.isfinite(agg), agg, 0.0)

    def row(self, secs_ago, now, tol=2.5):
        """index of the sample ~secs_ago before now, or None."""
        if self.count <= secs_ago:
            return None
        j = (self.ptr - int(secs_ago)) % HIST_S
        if abs(self.t[j] - (now - secs_ago)) <= tol:
            return j
        return None

    def last_fresh(self, j, max_back=5):
        """for stock column j, the newest finite eq print within max_back samples, or NaN."""
        for b in range(min(max_back + 1, self.count)):
            v = self.eq[(self.ptr - b) % HIST_S, j]
            if np.isfinite(v):
                return float(v)
        return np.nan

    def agg_block(self, k):
        """the last k samples of net aggressive flow, newest first, shape (k, n)."""
        k = min(k, self.count)
        idx = (self.ptr - np.arange(k)) % HIST_S
        return self.agg[idx]


_H = {"eng": None, "h": None}


def _hist(eng, n):
    if _H["eng"] is not eng or _H["h"] is None or _H["h"].n != n:
        _H["eng"], _H["h"] = eng, _Hist(n)
    return _H["h"]


def _ids(eng):
    dm = eng.domino
    eq_ids = np.asarray(dm.eq_ids, int)
    syms = list(dm.eq_sym)
    key = getattr(eng, "key", {}) or {}
    fut_ids = [key.get(f"{s}|FUT") for s in syms]
    return eq_ids, syms, np.asarray(dm.eq_w, float), fut_ids


def _f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ── per-second row maths (shared by the live facts and the pre-entry reference) ──────────────────────
def _rows(syms, w, px, ref, N0, d, px60=None, px30=None):
    """per-stock dicts, signed in the trade's favour. ref/px60/px30 are price arrays (NaN = unknown)."""
    wj = w / 100.0
    with np.errstate(divide="ignore", invalid="ignore"):
        pc = px / ref - 1.0
        pts_ = wj * pc * N0
        h60 = (d * wj * (px60 / ref - 1.0) * N0).tolist() if px60 is not None else None
        h30 = (d * wj * (px30 / ref - 1.0) * N0).tolist() if px30 is not None else None
    ok = np.isfinite(pc).tolist()
    pcl, ptl, thl, wl = (100.0 * pc).tolist(), pts_.tolist(), (wj * TH_PCT * N0).tolist(), w.tolist()
    rows = []
    for j, s in enumerate(syms):
        if not ok[j]:
            continue
        c = ptl[j]
        a60 = h60[j] if h60 is not None else None
        a30 = h30[j] if h30 is not None else None
        rows.append({"sym": s, "j": j, "w": wl[j], "grp": GROUP.get(s, "other"), "pct": pcl[j], "pts": c,
                     "help": d * c, "th": thl[j], "help60": a60 if (a60 is None or a60 == a60) else None,
                     "help30": a30 if (a30 is None or a30 == a30) else None})
    return rows


def _summary(rows, w, d, spot_pts):
    """breadth, basket, gap, conc, air from the rows (fresh names only)."""
    n = len(rows)
    if not n:
        return {"n": 0, "with": 0, "against": 0, "wpct": 0.0, "basket": None, "abs_sum": 0.0, "conc": 0.0, "conc_sym": None,
                "ratio": None, "air": False, "gap": None}
    hv = np.fromiter((r["help"] for r in rows), float, n)
    th = np.fromiter((r["th"] for r in rows), float, n)
    wv = np.fromiter((r["w"] for r in rows), float, n)
    wtot = float(wv.sum()) or 1.0
    with_m = hv > th
    n_with = int(with_m.sum()); n_against = int((hv < -th).sum())
    basket = float(hv.sum() * 100.0 / wtot)
    ab = np.abs(hv)
    abs_sum = float(ab.sum())
    jmax = int(ab.argmax())
    conc = float(ab[jmax] / abs_sum) if abs_sum > 1e-9 else 0.0
    sp = spot_pts if spot_pts is not None else 0.0
    ratio = basket / max(sp, 1.0)
    air = bool(sp >= 5 and (n_with <= 3 or conc >= 0.5 or ratio < AIR_RATIO))
    return {"n": n, "with": n_with, "against": n_against, "wpct": float(100.0 * wv[with_m].sum() / wtot),
            "basket": basket, "abs_sum": abs_sum, "conc": conc, "conc_sym": rows[jmax]["sym"], "ratio": ratio, "air": air,
            "gap": basket - sp}


def _runs(hist):
    """(run_with, run_against) seconds per stock from the 1-Hz net aggressive flow, 10-s blocks, <= 120 s.
    Sign is of the raw flow (+ = net buying); the caller multiplies by d. Recomputed once per block."""
    key = hist.count // RUN_BLOCK_S
    c = getattr(hist, "_runs_cache", None)
    if c is not None and c[0] == key:
        return c[1], c[2]
    a = hist.agg_block(RUN_MAX_S)
    nb = a.shape[0] // RUN_BLOCK_S
    if nb == 0:
        hist._runs_cache = (key, np.zeros(hist.n), np.zeros(hist.n))
        return hist._runs_cache[1], hist._runs_cache[2]
    blocks = a[:nb * RUN_BLOCK_S].reshape(nb, RUN_BLOCK_S, hist.n).sum(axis=1)       # newest block first
    pos = (np.cumprod(blocks > 0, axis=0).sum(axis=0) * RUN_BLOCK_S).astype(float)
    neg = (np.cumprod(blocks < 0, axis=0).sum(axis=0) * RUN_BLOCK_S).astype(float)
    hist._runs_cache = (key, pos, neg)
    return pos, neg


# ── entry snapshot ────────────────────────────────────────────────────────────────────────────────────
def extend_memo(memo, ctx, eng, pos):
    eq_ids, syms, w, fut_ids = _ids(eng)
    n = len(syms)
    now = ctx["now_s"]
    h = _hist(eng, n)
    h.sample(eng, now, eq_ids, fut_ids)
    d = int(pos["dir"])
    N0 = float(ctx.get("spot") or ctx.get("fut") or 0.0)
    m = eng.m
    eq_in = m.ltp[eq_ids, m.k].astype(float).copy() if n else np.zeros(0)
    for j in range(n):                                   # a NaN print at entry: the last fresh one <= 5 s old, else excluded
        if not np.isfinite(eq_in[j]):
            eq_in[j] = h.last_fresh(j)
    fut_in = np.array([m.ltp[r, m.k] if r is not None else np.nan for r in fut_ids], float)
    bk = {"syms": syms, "w": w, "eq_ids": eq_ids, "fut_ids": fut_ids, "d": d, "N0": N0, "t_in": float(pos["t_in"]),
          "eq_in": eq_in, "fut_in": fut_in, "best_fav": -1.0, "best_t": float(pos["t_in"]), "help_best": None,
          "basket_best": None, "with_best": 0, "max_with": 0, "flip_t": {}, "last_s": -1e9, "pre": {}, "day": {}}
    # the breakout reference: 90 s before entry from our ring, else the market ring's 60-s slot
    ref = None; ref_s = None
    j90 = h.row(PRE_REF_S, now, tol=5.0)
    if j90 is not None:
        ref, ref_s = h.eq[j90].copy(), PRE_REF_S
    elif getattr(m, "count", 0) > 1 and n:
        try:
            ref, ref_s = m.ltp[eq_ids, m.ago(60)].astype(float).copy(), 60
        except Exception:
            ref = None
    pre = {"ref_s": ref_s, "rows": [], "with": None, "against": None, "basket": None, "spot": None, "ratio": None,
           "top": [], "bot": [], "bank_with": None, "makers": []}
    if ref is not None and N0:
        rows = _rows(syms, w, eq_in, ref, N0, d)
        sp_old = None
        sh = getattr(eng, "spot_hist", None)
        if sh:
            sp_old = next((px for t, px in sh if now - t <= ref_s + 2), None)
        spot_pts = (N0 - sp_old) * d if sp_old is not None else None
        sm = _summary(rows, w, d, spot_pts)
        rows.sort(key=lambda r: -r["help"])
        pre.update(rows=rows, against=sm["against"], basket=sm["basket"], spot=spot_pts, ratio=sm["ratio"],
                   top=[(r["sym"], r["help"]) for r in rows[:3] if r["help"] > r["th"]],
                   bot=[(r["sym"], r["help"]) for r in rows[::-1][:3] if r["help"] < -r["th"]],
                   bank_with=sum(1 for r in rows if r["grp"] == "bank" and r["help"] > r["th"]),
                   makers=[r["sym"] for r in rows if r["help"] > r["th"]])
        pre["with"] = sm["with"]
    bk["pre"] = pre
    # day context: % vs previous close
    snap = getattr(m, "snap", None)
    day = {"with": None, "leader": None, "leader_chg": None, "laggard": None, "laggard_chg": None}
    if snap is not None and n:
        try:
            close = np.asarray(snap["close"], float)[eq_ids]
            with np.errstate(divide="ignore", invalid="ignore"):
                chg = 100.0 * (eq_in / close - 1.0)
            ok = np.isfinite(chg) & (close > 0)
            if ok.any():
                fav = np.where(ok, chg * d * w, -np.inf)
                day["with"] = int(((chg * d > 0) & ok).sum())
                jl = int(np.argmax(fav)); jg = int(np.argmin(np.where(ok, chg * d * w, np.inf)))
                day.update(leader=syms[jl], leader_chg=float(chg[jl]), laggard=syms[jg], laggard_chg=float(chg[jg]))
        except Exception:
            pass
    bk["day"] = day
    memo.bk = bk


# ── the live facts ────────────────────────────────────────────────────────────────────────────────────
def _blank(f):
    for k in FACTS:
        f.setdefault(k, None)


def extend_facts(f, ctx, eng, book, memo):
    try:
        with np.errstate(divide="ignore", invalid="ignore"):
            _extend(f, ctx, eng, book, memo)
    except Exception:
        _blank(f)


def _extend(f, ctx, eng, book, memo):
    bk = getattr(memo, "bk", None)
    if bk is None:
        extend_memo(memo, ctx, eng, book.pos)
        bk = memo.bk
    now = ctx["now_s"]
    d, N0, syms, w = bk["d"], bk["N0"], bk["syms"], bk["w"]
    eq_ids, fut_ids = bk["eq_ids"], bk["fut_ids"]
    n_all = len(syms)
    h = _hist(eng, n_all)
    h.sample(eng, now, eq_ids, fut_ids)
    m = eng.m
    px = m.ltp[eq_ids, m.k].astype(float) if n_all else np.zeros(0)
    t_in = bk["t_in"]
    age = now - t_in

    def _px_ago(secs):
        if age < secs:                                   # before entry: the entry price (help = 0)
            return bk["eq_in"]
        j = h.row(secs, now)
        return h.eq[j] if j is not None else None

    px60, px30, px15 = _px_ago(60), _px_ago(30), _px_ago(15)
    rows = _rows(syms, w, px, bk["eq_in"], N0, d, px60, px30) if N0 else []
    spot_pts = _f(f.get("spot_fav"))
    sm = _summary(rows, w, d, spot_pts)
    # flow runs (sign in the trade's favour) and book classes
    rw, ra = _runs(h)
    rw, ra = rw.tolist(), ra.tolist()
    fl = getattr(eng, "flow", None)
    tiles = ((getattr(eng.domino, "state", None) or {}).get("tiles") or [])
    try:
        cb, cs = np.asarray(fl.cls_b)[eq_ids].tolist(), np.asarray(fl.cls_s)[eq_ids].tolist()
    except Exception:
        cb = cs = [0] * n_all
    for r in rows:
        j = r["j"]
        r["run_with"] = rw[j] if d > 0 else ra[j]
        r["run_against"] = ra[j] if d > 0 else rw[j]
        tz = tiles[j] if j < len(tiles) else {}
        z, act = tz.get("z"), tz.get("act")
        r["z"] = z if isinstance(z, float) else None
        r["act"] = act if isinstance(act, float) else None
        r["cls_b"], r["cls_s"] = int(cb[j]), int(cs[j])
    by = {r["sym"]: r for r in rows}
    helpers = sorted([r for r in rows if r["help"] > r["th"]], key=lambda r: -r["help"])
    hurters = sorted([r for r in rows if r["help"] < -r["th"]], key=lambda r: r["help"])
    pos_sum = sum(r["help"] for r in rows if r["help"] > 0)
    neg_sum = sum(-r["help"] for r in rows if r["help"] < 0)
    top = helpers[0] if helpers else None
    bot = hurters[0] if hurters else None
    # 60 s ago
    with60 = sum(1 for r in rows if r["help60"] is not None and r["help60"] > r["th"]) if px60 is not None else None
    leavers = [r["sym"] for r in rows if r["help60"] is not None and r["help60"] > r["th"] and r["help"] <= r["th"]]
    top60 = max([r for r in rows if r["help60"] is not None], key=lambda r: r["help60"], default=None)
    basket60 = None
    if px60 is not None and N0 and rows:
        p60 = (w / 100.0) * (px60 / bk["eq_in"] - 1.0) * N0
        ok60 = np.isfinite(p60)
        if ok60.any():
            basket60 = float(d * p60[ok60].sum() * 100.0 / w[ok60].sum())
    # flips and turns
    flips = [{"sym": r["sym"], "was": r["help60"], "now": r["help"]} for r in rows
             if r["help60"] is not None and r["help"] * r["help60"] < 0 and abs(r["help"]) > r["th"] and abs(r["help60"]) > r["th"]]
    flip_against = max([x for x in flips if x["now"] < 0], key=lambda x: abs(x["was"]), default=None)
    flip_with = max([x for x in flips if x["now"] > 0], key=lambda x: abs(x["was"]), default=None)
    for x in flips:
        if x["now"] < 0 and x["sym"] in BIG_BANKS and x["sym"] not in bk["flip_t"]:
            bk["flip_t"][x["sym"]] = now
    ft = bk["flip_t"]
    pair = bool(all(s in ft for s in BIG_BANKS) and abs(ft[BIG_BANKS[0]] - ft[BIG_BANKS[1]]) <= 60)
    turns = [{"sym": r["sym"], "turn": r["help"] - r["help30"], "help": r["help"]} for r in rows if r["help30"] is not None]
    new_helper = max([x for x in turns if x["turn"] >= max(1.0, 3 * by[x["sym"]]["th"]) and x["help"] > by[x["sym"]]["th"]
                      and by[x["sym"]]["help30"] <= by[x["sym"]]["th"]], key=lambda x: x["turn"], default=None)
    # the best: track pos.best_spot through the base fact best_spot_fav
    best_fav = _f(f.get("best_spot_fav"))
    new_best = False
    if best_fav is not None and best_fav > bk["best_fav"] + 1e-9:
        new_best = bk["help_best"] is not None                # the very first sample is not "a new best"
        bk.update(best_fav=best_fav, best_t=now, best_hms=_hms(ctx, now), help_best={r["sym"]: r["help"] for r in rows},
                  basket_best=sm["basket"], with_best=sm["with"])
    bk["max_with"] = max(bk["max_with"], sm["with"])
    hb = bk["help_best"] or {}
    gb = sorted([(r["sym"], hb[r["sym"]] - r["help"], hb[r["sym"]], r["help"]) for r in rows if r["sym"] in hb],
                key=lambda x: -x[1])
    print_gb = _f(f.get("spot_retrace"))
    swing = None
    if gb and gb[0][1] >= max(1.0, 0.25 * (print_gb or 0.0)):
        swing = gb[0]
    gb_pos = [x for x in gb if x[1] > 0]
    basket_gb = (bk["basket_best"] - sm["basket"]) if (bk["basket_best"] is not None and sm["basket"] is not None) else None
    made = sorted([(s, v) for s, v in hb.items()], key=lambda x: -x[1])
    # sectors
    sec = {}
    for r in rows:
        g = sec.get(r["grp"])
        if g is None:
            g = sec[r["grp"]] = {"help": 0.0, "with": 0, "n": 0, "syms": []}
        g["help"] += r["help"]; g["n"] += 1; g["syms"].append(r["sym"])
        if r["help"] > r["th"]:
            g["with"] += 1
    bank = sec.get("bank", {"help": 0.0, "with": 0, "n": 0, "syms": []})
    it = sec.get("it", {"help": 0.0, "with": 0, "n": 0, "syms": []})
    ril = by.get("RELIANCE", {}).get("help")
    rest = sum(v["help"] for g, v in sec.items() if g != "bank")
    other = sum(v["help"] for g, v in sec.items() if g not in ("bank", "it", "ril"))
    sec_against = None
    for g, v in sec.items():
        if v["n"] >= 2 and v["with"] == 0 and v["help"] <= -1.0 and (sec_against is None or v["help"] < sec_against["pts"]):
            sec_against = {"sector": SECTOR_LABEL.get(g, g), "pts": v["help"], "n": v["n"], "syms": v["syms"]}
    all_on = bool(sec) and all(v["help"] >= 0 for v in sec.values())
    lone = next((SECTOR_LABEL.get(g, g) for g, v in sec.items() if pos_sum > 0 and v["help"] >= 0.7 * pos_sum), None)
    opp = None
    for g, v in sec.items():
        if v["n"] < 2:
            continue
        rr = [by[s] for s in v["syms"]]
        hi = max(rr, key=lambda r: r["help"]); lo = min(rr, key=lambda r: r["help"])
        if hi["help"] >= 1.0 and lo["help"] <= -1.0:
            opp = {"sector": SECTOR_LABEL.get(g, g), "a": hi["sym"], "pa": hi["help"], "b": lo["sym"], "pb": lo["help"]}
            break
    bb = min([by[s] for s in BIG_BANKS if s in by and by[s]["help"] <= -1.0], key=lambda r: r["help"], default=None)
    # stock futures vs cash: 15-s lead and the basis since entry (bp, in the trade's favour)
    fut_lead = None; basis_bps = None
    j15 = h.row(15, now)
    fut_now = h.fut[h.ptr] if h.count else None
    if fut_now is not None and px15 is not None and j15 is not None and N0:
        f15 = h.fut[j15]
        lead = (w / 100.0) * ((fut_now / f15 - 1.0) - (px / px15 - 1.0)) * N0
        ok = np.isfinite(lead)
        if ok.any():
            fut_lead = float(lead[ok].sum() * 100.0 / w[ok].sum()) * d
    if fut_now is not None and N0 and rows:
        bas = (fut_now / bk["fut_in"] - 1.0) - (px / bk["eq_in"] - 1.0)
        ok = np.isfinite(bas)
        if ok.any():
            basis_bps = float((bas[ok] * w[ok]).sum() / w[ok].sum()) * 1e4 * d
    # flow lists (sign in the trade's favour)
    wtot = sum(r["w"] for r in rows) or 1.0
    flow_with = sorted([(r["sym"], r["run_with"]) for r in rows if r["run_with"] >= 30], key=lambda x: -x[1])
    flow_against = sorted([(r["sym"], r["run_against"]) for r in rows if r["run_against"] >= 30], key=lambda x: -x[1])
    fw_w = 100.0 * sum(by[s]["w"] for s, _ in flow_with) / wtot
    fa_w = 100.0 * sum(by[s]["w"] for s, _ in flow_against) / wtot
    pressed = next(((r["sym"], r["run_with"], r["help"]) for r in sorted(rows, key=lambda r: -r["run_with"])
                    if r["run_with"] >= 40 and r["help"] > r["th"]), None)
    fought = next(((r["sym"], r["run_against"], r["help"]) for r in sorted(rows, key=lambda r: -r["run_against"])
                   if r["run_against"] >= 40 and r["help"] < -r["th"]), None)
    hold_cls = (lambda r: r["cls_b"]) if d > 0 else (lambda r: r["cls_s"])      # the side that must hold for the trade
    brk_cls = (lambda r: r["cls_s"]) if d > 0 else (lambda r: r["cls_b"])       # the side the trade must eat through
    top_pulled = bool(top and hold_cls(top) == _PULL)
    refilling = [r["sym"] for r in helpers if brk_cls(r) == _REFILL]
    # episode / first mover
    ep = ctx.get("episode") or {}
    ep_ok = bool(ep and ep.get("dir") == d and (now - (ep.get("age") or 0.0)) >= t_in - 120)
    # waves and activity
    wave_with = [r["sym"] for r in rows if r["z"] is not None and r["z"] * d >= 2.0]
    wave_against = [r["sym"] for r in rows if r["z"] is not None and r["z"] * d <= -2.0]
    dry = sum(1 for r in rows if r["act"] is not None and r["act"] < 0.5)
    pre, day = bk["pre"], bk["day"]
    f.update(
        eq_n=sm["n"], eq_rows=rows, eq_syms_fresh=[r["sym"] for r in rows],
        eq_breadth_with=sm["with"], eq_breadth_against=sm["against"], eq_breadth_flat=sm["n"] - sm["with"] - sm["against"],
        eq_wpct_with=sm["wpct"], eq_with60=with60, eq_breadth_chg60=(sm["with"] - with60) if with60 is not None else None,
        eq_leavers=leavers, eq_max_with=bk["max_with"],
        eq_spot_pts=spot_pts, eq_basket_pts_scaled=sm["basket"], eq_gap_vs_print=sm["gap"], eq_ratio=sm["ratio"],
        eq_basket60=basket60, eq_abs_sum=sm["abs_sum"],
        eq_concentration=sm["conc"], eq_conc_sym=sm["conc_sym"], eq_air=sm["air"],
        eq_help_pos=pos_sum, eq_help_neg=neg_sum,
        eq_top_sym=top["sym"] if top else None, eq_top_help=top["help"] if top else None, eq_top_pct=top["pct"] if top else None,
        eq_top_share=(top["help"] / pos_sum) if (top and pos_sum > 0) else None,
        eq_top_run_with=top["run_with"] if top else None, eq_top_run_against=top["run_against"] if top else None,
        eq_top60_sym=top60["sym"] if (top60 and top60["help60"] > top60["th"]) else None,
        eq_top_help60=(top["help60"] if top else None),
        eq_top2_sym=helpers[1]["sym"] if len(helpers) > 1 else None, eq_top2_help=helpers[1]["help"] if len(helpers) > 1 else None,
        eq_top2_share=((helpers[0]["help"] + helpers[1]["help"]) / pos_sum) if (len(helpers) > 1 and pos_sum > 0) else None,
        eq_top3_sym=helpers[2]["sym"] if len(helpers) > 2 else None, eq_top3_help=helpers[2]["help"] if len(helpers) > 2 else None,
        eq_bot_sym=bot["sym"] if bot else None, eq_bot_help=bot["help"] if bot else None, eq_bot_pct=bot["pct"] if bot else None,
        eq_bot_run_against=bot["run_against"] if bot else None,
        eq_flips=flips, eq_flip_against=flip_against, eq_flip_with=flip_with, eq_pair_flip_banks=pair,
        eq_turn=turns, eq_new_helper=new_helper,
        eq_new_best=new_best, eq_best_t=bk["best_t"], eq_best_hms=bk.get("best_hms"), eq_with_at_best=bk["with_best"],
        eq_basket_at_best=bk["basket_best"], eq_basket_giveback=basket_gb, eq_print_giveback=print_gb,
        eq_swing_sym=swing[0] if swing else None, eq_swing_giveback=swing[1] if swing else None,
        eq_swing_at_best=swing[2] if swing else None, eq_swing_now=swing[3] if swing else None,
        eq_giveback_n=len(gb_pos), eq_giveback_max=gb[0][1] if gb else None, eq_giveback_max_sym=gb[0][0] if gb else None,
        eq_giveback_top=[(x[0], x[1]) for x in gb_pos[:2]],
        eq_made=made, eq_sector_banks=bank["help"], eq_sector_banks_with=bank["with"], eq_sector_it=it["help"],
        eq_sector_it_with=it["with"], eq_sector_ril=ril, eq_sector_other=other, eq_sector_rest=rest,
        eq_sector_against=sec_against, eq_all_sectors_on=all_on, eq_lone_sector=lone, eq_opposite_pair=opp,
        eq_infy=by.get("INFY", {}).get("help"), eq_tcs=by.get("TCS", {}).get("help"), eq_hdfc_help=by.get("HDFCBANK", {}).get("help"),
        eq_big_bank_against=({"sym": bb["sym"], "help": bb["help"], "w": bb["w"], "pct": bb["pct"]} if bb else None),
        eq_fut_lead=fut_lead, eq_basis_bps=basis_bps,
        eq_flow_with=flow_with, eq_flow_against=flow_against, eq_flow_with_wpct=fw_w, eq_flow_against_wpct=fa_w,
        eq_pressed_name=pressed, eq_fought_name=fought, eq_top_pulled=top_pulled, eq_refilling=refilling,
        eq_first_mover=ep.get("first") if ep_ok else None, eq_first_mover_t=_hms(ctx, now - (ep.get("age") or 0.0)) if ep_ok else None,
        eq_ep_type=ep.get("type") if ep_ok else None, eq_ep_age=ep.get("age") if ep_ok else None,
        eq_ep_ncross=ep.get("n_cross") if ep_ok else None, eq_ep_with=ep_ok,
        eq_pre_ref_s=pre.get("ref_s"), eq_pre_rows=pre.get("rows"), eq_pre_with=pre.get("with"), eq_pre_against=pre.get("against"),
        eq_pre_basket=pre.get("basket"), eq_pre_spot=pre.get("spot"), eq_pre_ratio=pre.get("ratio"), eq_pre_top=pre.get("top"),
        eq_pre_bot=pre.get("bot"), eq_pre_bank_with=pre.get("bank_with"), eq_pre_makers=pre.get("makers"),
        eq_day_with=day.get("with"), eq_day_leader=day.get("leader"), eq_day_leader_chg=day.get("leader_chg"),
        eq_day_laggard=day.get("laggard"), eq_day_laggard_chg=day.get("laggard_chg"),
        eq_wave_with=wave_with, eq_wave_against=wave_against, eq_vol_dry_n=dry,
    )
    f["eq_hot"] = _hot(f)


def _hot(f):
    """T07 §5 rule 2: a warning with prio >= 75 suppresses every 'confident' remark the same second."""
    for tp in _HOT:
        try:
            if tp.when(f):
                return True
        except Exception:
            continue
    return False


def _hms(ctx, t):
    try:
        from datetime import datetime, timedelta
        dt = ctx["now_dt"] - timedelta(seconds=ctx["now_s"] - t)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return "—"


# ── slots: ready-to-print strings for the phrasings (never raise, never print None) ──────────────────
def _h(x, nd=1):
    v = _f(x)
    return "—" if v is None else f"{v:+.{nd}f}"


def _a(x, nd=1):
    v = _f(x)
    return "—" if v is None else f"{abs(v):.{nd}f}"


def _i(x):
    v = _f(x)
    return "—" if v is None else str(int(round(v)))


def _p(x):
    v = _f(x)
    return "—" if v is None else f"{100 * v:.0f}"


def _lst(xs, k=3):
    xs = [x for x in (xs or []) if x][:k]
    return ", ".join(xs) if xs else "nobody"


def _D(x):
    return x if isinstance(x, dict) else {}


def _L(x):
    return list(x) if isinstance(x, (list, tuple)) else []


def S(f):
    d = f.get("dir") if f.get("dir") in (1, -1) else 1
    pre_top = [x for x in _L(f.get("eq_pre_top")) if isinstance(x, (list, tuple)) and len(x) == 2]
    pre_bot = [x for x in _L(f.get("eq_pre_bot")) if isinstance(x, (list, tuple)) and len(x) == 2]
    bb = _D(f.get("eq_big_bank_against"))
    sa = _D(f.get("eq_sector_against"))
    fa = _D(f.get("eq_flip_against"))
    fw = _D(f.get("eq_flip_with"))
    nh = _D(f.get("eq_new_helper"))
    pr = f.get("eq_pressed_name") if isinstance(f.get("eq_pressed_name"), tuple) else (None, None, None)
    fo = f.get("eq_fought_name") if isinstance(f.get("eq_fought_name"), tuple) else (None, None, None)
    opp = _D(f.get("eq_opposite_pair"))
    made = [x for x in _L(f.get("eq_made")) if isinstance(x, (list, tuple)) and len(x) == 2]
    fl = {x["sym"]: x for x in _L(f.get("eq_flips")) if isinstance(x, dict)}
    gt = [x for x in _L(f.get("eq_giveback_top")) if isinstance(x, (list, tuple)) and len(x) == 2]
    rows = [r for r in _L(f.get("eq_rows")) if isinstance(r, dict)]
    hurt = sorted([r for r in rows if r["help"] < -r["th"]], key=lambda r: r["help"])
    r1 = gt[0][0] if gt else (hurt[0]["sym"] if hurt else "—")
    r2 = gt[1][0] if len(gt) > 1 else (hurt[1]["sym"] if len(hurt) > 1 else "—")
    rp1 = _h(-gt[0][1]) if gt else _h(hurt[0]["help"] if hurt else None)
    rp2 = _h(-gt[1][1]) if len(gt) > 1 else _h(hurt[1]["help"] if len(hurt) > 1 else None)
    pgb = f.get("eq_print_giveback")
    rshare = _p((sum(x[1] for x in gt[:2]) / pgb) if (gt and pgb and pgb > 0) else None)
    day_with = f.get("eq_day_with")
    n = f.get("eq_n")
    return {
        "n": _i(n), "with": _i(f.get("eq_breadth_with")), "against": _i(f.get("eq_breadth_against")), "flat": _i(f.get("eq_breadth_flat")),
        "wpct": _i(f.get("eq_wpct_with")), "with60": _i(f.get("eq_with60")), "gain": _i(f.get("eq_breadth_chg60")),
        "loss": _i(-(f.get("eq_breadth_chg60") or 0)), "leavers": _lst(f.get("eq_leavers")),
        "tot": _h(f.get("eq_basket_pts_scaled")), "spot": _h(f.get("eq_spot_pts")), "gap": _a(f.get("eq_gap_vs_print")),
        "ratio": _p(f.get("eq_ratio")), "tot60": _h(f.get("eq_basket60")), "abs": _a(f.get("eq_abs_sum")),
        "sym": str(f.get("eq_top_sym") or "—"), "pts": _h(f.get("eq_top_help")), "pct": _h(f.get("eq_top_pct"), 2),
        "share": _p(f.get("eq_top_share")), "secs": _i(f.get("eq_top_run_with")), "asecs": _i(f.get("eq_top_run_against")),
        "sym1": f.get("eq_top_sym") or "—", "pts1": _h(f.get("eq_top_help")), "sym2": f.get("eq_top2_sym") or "—",
        "pts2": _h(f.get("eq_top2_help")), "share2": _p(f.get("eq_top2_share")), "sym3": f.get("eq_top3_sym") or "—",
        "pts3": _h(f.get("eq_top3_help")),
        "hsym": f.get("eq_bot_sym") or "—", "hpts": _h(f.get("eq_bot_help")), "hpct": _h(f.get("eq_bot_pct"), 2),
        "hsecs": _i(f.get("eq_bot_run_against")), "neg": _a(f.get("eq_help_neg")), "pos": _a(f.get("eq_help_pos")),
        "csym": f.get("eq_conc_sym") or "—", "cshare": _p(f.get("eq_concentration")),
        "side": "buyers" if d > 0 else "sellers", "oside": "sellers" if d > 0 else "buyers",
        "dirword": "rise" if d > 0 else "fall", "dirword_s": "rises" if d > 0 else "falls",
        "dirword_ing": "rising" if d > 0 else "falling", "dirword_er": "higher" if d > 0 else "lower",
        "level": "bid" if d > 0 else "ask", "olevel": "ask" if d > 0 else "bid", "opt": f.get("rr") or ("CE" if d > 0 else "PE"),
        "sector_a": sa.get("sector") or "—", "sector_a_pts": _h(sa.get("pts")), "sector_a_n": _i(sa.get("n")), "sector_a_list": _lst(sa.get("syms"), 5),
        "pb": _a(f.get("eq_print_giveback")), "bpb": _a(f.get("eq_basket_giveback")), "bbest": _h(f.get("eq_basket_at_best")),
        "ssym": f.get("eq_swing_sym") or "—", "sgb": _a(f.get("eq_swing_giveback")), "satbest": _h(f.get("eq_swing_at_best")),
        "snow": _h(f.get("eq_swing_now")), "besttime": f.get("eq_best_hms") or "—",
        "gbn": _i(f.get("eq_giveback_n")), "gbmax": _a(f.get("eq_giveback_max")), "gbsym": f.get("eq_giveback_max_sym") or "—",
        "fsym": fa.get("sym") or "—", "fwas": _h(fa.get("was")), "fnow": _h(fa.get("now")),
        "gsym": fw.get("sym") or "—", "gwas": _h(fw.get("was")), "gnow": _h(fw.get("now")),
        "nsym": nh.get("sym") or "—", "nturn": _h(nh.get("turn")), "npts": _h(nh.get("help")),
        "bbsym": bb.get("sym") or "—", "bbw": _a(bb.get("w"), 1), "bbpct": _h(bb.get("pct"), 2), "bbpts": _h(bb.get("help")),
        "hflip": _h(fl.get("HDFCBANK", {}).get("now")), "iflip": _h(fl.get("ICICIBANK", {}).get("now")),
        "bpts": _h(f.get("eq_sector_banks")), "bwith": _i(f.get("eq_sector_banks_with")), "rpts": _h(f.get("eq_sector_rest")),
        "rest": _h(f.get("eq_sector_rest")), "infy": _h(f.get("eq_infy")), "tcs": _h(f.get("eq_tcs")), "itpts": _h(f.get("eq_sector_it")),
        "rilpts": _h(f.get("eq_sector_ril")),
        "rilshare": _p((f["eq_sector_ril"] / f["eq_help_pos"]) if (f.get("eq_sector_ril") and (f.get("eq_help_pos") or 0) > 0) else None),
        "lead": _a(f.get("eq_fut_lead")), "bps": _a(f.get("eq_basis_bps"), 0),
        "psym": pr[0] or "—", "psecs": _i(pr[1]), "qsym": fo[0] or "—", "qsecs": _i(fo[1]), "qpts": _h(fo[2]),
        "fwn": _i(len(f.get("eq_flow_with") or [])), "fwpct": _i(f.get("eq_flow_with_wpct")),
        "fan": _i(len(f.get("eq_flow_against") or [])), "fapct": _i(f.get("eq_flow_against_wpct")),
        "refill_list": _lst(f.get("eq_refilling"), 3),
        "fm": f.get("eq_first_mover") or "—", "ft": f.get("eq_first_mover_t") or "—", "eptype": f.get("eq_ep_type") or "—",
        "ncross": _i(f.get("eq_ep_ncross")), "age": _i(f.get("hold_s")), "min": _i((f.get("hold_s") or 0) / 60.0),
        "jsym1": pre_top[0][0] if pre_top else "—", "jpts1": _h(pre_top[0][1] if pre_top else None),
        "jsym2": pre_top[1][0] if len(pre_top) > 1 else "—", "jpts2": _h(pre_top[1][1] if len(pre_top) > 1 else None),
        "jsym3": pre_top[2][0] if len(pre_top) > 2 else "—", "jpts3": _h(pre_top[2][1] if len(pre_top) > 2 else None),
        "jhsym": pre_bot[0][0] if pre_bot else "—", "jhpts": _h(pre_bot[0][1] if pre_bot else None),
        "jwith": _i(f.get("eq_pre_with")), "jagainst": _i(f.get("eq_pre_against")), "jtot": _h(f.get("eq_pre_basket")),
        "jspot": _h(f.get("eq_pre_spot")), "jbwith": _i(f.get("eq_pre_bank_with")), "jref": _i(f.get("eq_pre_ref_s")),
        "daywith": _i(day_with), "leader": f.get("eq_day_leader") or "—", "chg": _h(f.get("eq_day_leader_chg"), 2),
        "laggard": f.get("eq_day_laggard") or "—", "lchg": _h(f.get("eq_day_laggard_chg"), 2),
        "with_or_against": ("with" if (day_with is not None and n and day_with * 2 >= n) else "against"),
        "m1": made[0][0] if made else "—", "mp1": _h(made[0][1] if made else None),
        "m2": made[1][0] if len(made) > 1 else "—", "mp2": _h(made[1][1] if len(made) > 1 else None),
        "r1": r1, "rp1": rp1, "r2": r2, "rp2": rp2, "rshare": rshare,
        "ratbest": _h(f.get("eq_swing_at_best")), "rnow": _h(f.get("eq_swing_now")), "maxwith": _i(f.get("eq_max_with")),
        "bwith_best": _i(f.get("eq_with_at_best")), "pnl": pts(f.get("pnl_pts")),
        "osector": opp.get("sector") or "—", "oa": opp.get("a") or "—", "opa": _h(opp.get("pa")), "ob": opp.get("b") or "—", "opb": _h(opp.get("pb")),
        "hdfc": _h(f.get("eq_hdfc_help")), "dryn": _i(f.get("eq_vol_dry_n")),
        "wlist": _lst(f.get("eq_wave_with"), 4), "wn": _i(len(f.get("eq_wave_with") or [])),
        "alist": _lst(f.get("eq_wave_against"), 4), "an": _i(len(f.get("eq_wave_against") or [])),
        "lone": f.get("eq_lone_sector") or "—",
    }


# ── predicates (every one tolerates None) ─────────────────────────────────────────────────────────────
def _g(f, k, default=0.0):
    v = f.get(k)
    return default if v is None else v


def _tone(t07, prio):
    """T07 tones -> core TONES. T07 warnings >= 75 keep the core's 'warning' (bypasses budget and cool-down,
    outranks every cheer); lower T07 warnings are 'caution'. confident -> confidence, descriptive/colour -> information,
    review -> lesson."""
    return {"warning": "warning" if prio >= 75 else "caution", "confident": "confidence", "descriptive": "information",
            "colour": "information", "review": "lesson"}[t07]


def T(key, t07, prio, when, phr, cd=90.0, step=None, once=False, min_hold_s=0.0, kind="basket", note=""):
    if t07 == "confident":                                # a cheer is silent while a >= 75 warning holds
        when = (lambda w: (lambda f: (not f.get("eq_hot")) and bool(w(f))))(when)
    return Template(key=key, kind=kind, tone=_tone(t07, prio), prio=prio, when=when, phrasings=phr, cooldown_s=cd,
                    step=step or {}, min_hold_s=min_hold_s, once=once, slots=S, note=note)


_SP = lambda f: _g(f, "eq_spot_pts")                 # print move in favour            # noqa: E731
_W = lambda f: _g(f, "eq_breadth_with", 0)                                               # noqa: E731
_A = lambda f: _g(f, "eq_breadth_against", 0)                                            # noqa: E731
_TOT = lambda f: _g(f, "eq_basket_pts_scaled")                                           # noqa: E731
_N = lambda f: f.get("eq_n") or 0                                                        # noqa: E731


def _th_of(f, sym):
    for r in f.get("eq_rows") or []:
        if r["sym"] == sym:
            return r["th"]
    return None


TEMPLATES: List[Template] = [
    # ── A. helpers ───────────────────────────────────────────────────────────────────────────────────
    T("lead_helper", "confident", 60, lambda f: f.get("eq_top_sym") and _g(f, "eq_top_help") >= max(2.0, 0.35 * _g(f, "eq_help_pos")) and _SP(f) >= 6,
      ["{sym} alone has given you {pts} of your {tot} basket points.",
       "The engine room is {sym}: {pts} points of the {tot} the basket has moved for you.",
       "{sym} is carrying this — {pct} % since your entry, worth {pts} Nifty points.",
       "If you want to know who is paying for this trade: {sym}, {pts} points.",
       "{sym} is doing the heavy lifting ({pts} of {tot}). The rest are passengers so far."],
      cd=90, step={"eq_top_help": 2.0}, note="A1: top helper >= max(2, 35 % of the positive help) with the print >= 6 in favour."),
    T("two_helpers", "confident", 55, lambda f: f.get("eq_top2_sym") and _g(f, "eq_top2_share") >= 0.6,
      ["{sym1} and {sym2} are your trade: {pts1} and {pts2} points between them.",
       "Two engines running — {sym1} ({pts1}) and {sym2} ({pts2}). Everyone else is a rounding error.",
       "This is a {sym1}–{sym2} move: {share2} % of the basket's help is those two names.",
       "{sym1} started it, {sym2} is finishing it: {pts1} + {pts2} points."],
      cd=120, step={"eq_top2_share": 0.15}, note="A2: the top two helpers are >= 60 % of the positive help, both meaningful."),
    T("helper_pressed", "confident", 50, lambda f: f.get("eq_top_sym") and _g(f, "eq_top_run_with") >= 30,
      ["{sym} is your best name ({pts}) and {side} have been pressing it for {secs} s.",
       "{sym}: {pts} points for you, and the aggressive flow there has been on your side for {secs} seconds.",
       "Not just drifting — {sym} is being hit by {side} for {secs} s straight, and it is your top contributor."],
      cd=90, step={"eq_top_run_with": 30}, note="A3: top helper with net aggressive flow in the trade's direction for >= 30 s (present tense: flow describes, it does not forecast)."),
    T("new_helper", "confident", 45, lambda f: bool(f.get("eq_new_helper")),
      ["{nsym} just joined the move: {nturn} points in the last 30 s.",
       "A new recruit — {nsym} has come across to your side ({npts} now).",
       "{nsym} woke up: {nturn} points for you in half a minute.",
       "Add {nsym} to the list of names working for you ({npts})."],
      cd=60, step={"eq_breadth_with": 1}, min_hold_s=30, note="A4: 30-s turn >= max(1, 3 th), now meaningful, was not a helper 30 s ago."),
    T("helper_share_small", "confident", 40, lambda f: f.get("eq_top_sym") and _g(f, "eq_top_share", 1.0) < 0.25 and _W(f) >= 8,
      ["No single star — the biggest helper is {sym} at only {pts}; this is {with} names pulling together.",
       "Help is spread thin and wide: {with} names, none above {pts}. A crowd, not a hero.",
       "Nobody owns this move; {with} heavyweights are each giving a little."],
      cd=180, note="A5: top helper < 25 % of the positive help and breadth >= 8."),
    # ── B. hurters ───────────────────────────────────────────────────────────────────────────────────
    T("lead_hurter", "warning", 65, lambda f: f.get("eq_bot_sym") and _g(f, "eq_bot_help") <= -max(1.0, 2 * (_th_of(f, f["eq_bot_sym"]) or 0.5)) and _SP(f) >= 3,
      ["{hsym} is the one fighting you: {hpct} % while the rest of the basket {dirword_s}.",
       "Your drag is {hsym} — {hpts} points against, the biggest in the basket.",
       "{hsym} has not read the memo: {hpct} % against your {opt}.",
       "One name is leaning the other way: {hsym}, costing you {hpts} points.",
       "{hsym} is the anchor on this trade ({hpts})."],
      cd=90, step={"eq_bot_help": 1.0}, note="B1: bottom hurter <= -max(1, 2 th) while the print is >= 3 in favour."),
    T("big_bank_against", "warning", 70, lambda f: bool(f.get("eq_big_bank_against")),
      ["{bbsym} is against you, and it is {bbw} % of the index — the heaviest name you track is on the other side.",
       "Note the weight: {bbsym} ({bbw} % of Nifty) is {bbpct} % the wrong way. It does not take much from it to undo the rest.",
       "The biggest bank is not with you: {bbsym} {bbpts}. The trade is winning in spite of it, not because of it."],
      cd=120, step={"eq_hdfc_help": 1.0}, note="B2: HDFCBANK or ICICIBANK at help <= -1.0 pt."),
    T("hurter_pressed", "warning", 60, lambda f: f.get("eq_bot_sym") and _g(f, "eq_bot_run_against") >= 30,
      ["{hsym} is being pressed against you — aggressive {oside} for {hsecs} s and {hpts} points lost there.",
       "The fight is in {hsym}: {oside} hitting it for {hsecs} seconds, {hpts} against you.",
       "{hsym}: {oside} have been in control for {hsecs} s. That is where your trade is being contested."],
      cd=90, step={"eq_bot_run_against": 30}, note="B3: bottom hurter with aggressive flow against the trade for >= 30 s."),
    T("hurters_outnumber_helpers_pts", "warning", 75, lambda f: _g(f, "eq_help_neg") > _g(f, "eq_help_pos") and _SP(f) > 0 and _N(f) > 0,
      ["The stocks against you now outweigh the stocks with you ({neg} vs {pos} pts); the index is up on names we do not track.",
       "Basket says {tot}, print says {spot}. The heavyweights have stopped paying for this.",
       "More weight is leaning against the trade than for it. The profit on screen is not coming from the basket."],
      cd=60, step={"eq_help_neg": 1.0}, note="B4: Σ|help<0| > Σ help>0 while the print is still in favour."),
    T("sector_against", "warning", 50, lambda f: bool(f.get("eq_sector_against")),
      ["{sector_a} is not playing: {sector_a_n} of {sector_a_n} against you, {sector_a_pts} points.",
       "The whole {sector_a} block is on the other side ({sector_a_pts}).",
       "{sector_a} has decided this is not a {dirword}: {sector_a_list}."],
      cd=150, note="B5: a sector with >= 2 names, none with, sum <= -1.0."),
    # ── C. breadth ───────────────────────────────────────────────────────────────────────────────────
    T("broad_move", "confident", 70, lambda f: _W(f) >= 10 and _A(f) <= 1 and _SP(f) >= 8,
      ["{with} of {n} heavyweights are with you — this is a real move, not an index print.",
       "Breadth {with}/{n}, {against} against. The whole basket is leaning your way.",
       "You are not fighting anyone: {with} names with you, {against} meaningfully against.",
       "This has weight behind it — {with} of the {n} names we track, {wpct} % of tracked weight.",
       "Count them: {with} heavyweights {dirword_ing} with your {opt}."],
      cd=120, step={"eq_breadth_with": 2}, note="C1: with >= 10, against <= 1, print >= 8. Descriptive confidence: no 60-s edge was found on 19 Oct."),
    T("full_house", "confident", 80, lambda f: _W(f) >= 13,
      ["{with} of {n}. Every sector, every bank. As broad as a move gets.",
       "{with}/{n} — the entire basket is on your side right now.",
       "Full house: {with} of {n}, nobody meaningful against."],
      cd=180, note="C2: with >= 13."),
    T("half_breadth", "descriptive", 40, lambda f: 5 <= _W(f) <= 8 and _A(f) <= 3,
      ["A split basket: {with} with you, {against} against, the rest flat.",
       "Half the heavyweights are in ({with}/{n}). Enough to move the index, not enough to call it a stampede.",
       "{with} names are doing the work; {flat} have not chosen a side yet."],
      cd=150, note="C3: 5 <= with <= 8, against <= 3."),
    T("thin_move", "warning", 85, lambda f: bool(f.get("eq_air")) and _W(f) <= 3 and _SP(f) >= 5,
      ["Only {with} names are moving; the index is being dragged by {sym} — a reversal there would undo this.",
       "Thin: {with} of {n}. The print says {spot} but the basket says {tot}. This is {csym}'s move, not the market's.",
       "The index is moving on air — {with} heavyweights with you, {against} against. That is the count, not the print.",
       "You are {spot} up on the print and the stocks have not come: basket {tot}, {with} names."],
      cd=60, step={"eq_breadth_with": 1}, note="C4: AIR with breadth <= 3 and print >= 5. On 19 Oct n = 11 seconds: a warning, never a forecast."),
    T("concentrated", "warning", 65, lambda f: _g(f, "eq_concentration") >= 0.5 and _SP(f) >= 5 and f.get("eq_conc_sym"),
      ["{csym} is {cshare} % of everything the basket has done. One name. If it turns, the trade turns.",
       "Concentration {cshare} % in {csym}. Not a basket move — a single-name move wearing an index costume.",
       "Everything is riding on {csym} ({cshare} % of the basket's net move)."],
      cd=120, step={"eq_concentration": 0.1}, note="C5: max|pts| / Σ|pts| >= 0.5 with the print >= 5."),
    T("breadth_rising", "confident", 55, lambda f: _g(f, "eq_breadth_chg60") >= 3,
      ["The move is spreading: {with} names now, {with60} a minute ago.",
       "Recruitment — {gain} more heavyweights joined in the last minute ({with}/{n}).",
       "Breadth is building, {with60} → {with}. The basket is catching up with the print."],
      cd=90, step={"eq_breadth_with": 2}, min_hold_s=60, note="C6: with(t) - with(t-60) >= 3."),
    T("breadth_falling", "warning", 80, lambda f: _g(f, "eq_breadth_chg60") <= -3 and _SP(f) >= 3,
      ["Names are leaving: {with60} with you a minute ago, {with} now. {leavers} let go.",
       "The basket is thinning out — {with}/{n}, down from {with60}. The print is holding; the stocks are not.",
       "You have lost {loss} heavyweights in a minute ({leavers}). That is how reversals start — not a forecast, a count."],
      cd=60, step={"eq_breadth_with": 1}, min_hold_s=60, note="C7: with(t) - with(t-60) <= -3 with the print >= 3."),
    T("basket_zero", "warning", 90, lambda f: _N(f) > 0 and _W(f) == 0 and _SP(f) >= 0 and _g(f, "hold_s") >= 15,
      ["No heavyweight is past its entry print. The breakout you bought is not in the stocks.",
       "Zero of {n}. Whatever moved the index, it was not these names.",
       "The basket has not moved at all ({tot}). You are long an index print."],
      cd=60, note="C8: with = 0 after 15 s with the print not against."),
    # ── D. basket vs print ───────────────────────────────────────────────────────────────────────────
    T("basket_confirms", "confident", 60, lambda f: _g(f, "eq_ratio") >= 0.8 and _SP(f) >= 8 and _W(f) >= 7,
      ["Basket {tot}, print {spot}: the stocks confirm the breakout.",
       "This is not a futures-only move — the cash names account for {ratio} % of what Nifty printed.",
       "The index says {spot}, the heavyweights say {tot}. They agree."],
      cd=150, step={"eq_basket_pts_scaled": 5.0}, note="D1: basket/print >= 0.8, print >= 8, with >= 7."),
    T("basket_ahead", "confident", 65, lambda f: f.get("eq_gap_vs_print") is not None and f["eq_gap_vs_print"] >= max(4.0, 0.3 * _SP(f)) and _W(f) >= 7,
      ["The stocks are AHEAD of the index: basket {tot} vs print {spot}. The print has {gap} points of catching up to do.",
       "Nifty has not caught up with its own constituents — basket {tot}, spot {spot}.",
       "There is {gap} points of basket move that the index has not printed yet."],
      cd=120, step={"eq_gap_vs_print": 3.0}, note="D2: gap = basket - print >= max(4, 30 % of the print), with >= 7."),
    T("basket_behind", "warning", 75, lambda f: f.get("eq_gap_vs_print") is not None and -f["eq_gap_vs_print"] >= max(4.0, 0.4 * _SP(f)) and _SP(f) >= 6,
      ["The index is ahead of its stocks: print {spot}, basket only {tot}. {gap} points of this is not in the heavyweights.",
       "Spot {spot}, basket {tot}. The names we track explain less than half of this print.",
       "This profit rests on the print — the basket is {tot} and the index is {spot}; the difference is names we cannot see, or air."],
      cd=90, step={"eq_gap_vs_print": 3.0}, note="D3: print - basket >= max(4, 40 % of the print), print >= 6."),
    T("trailing_on_air", "descriptive", 70, lambda f: _g(f, "eq_print_giveback") >= 8 and f.get("eq_basket_at_best") is not None and _TOT(f) >= f["eq_basket_at_best"] - 1 and _W(f) >= 10,
      ["The print has pulled back {pb} from the best but the basket has not — still {tot}, {with} names with you. The stocks did not reverse.",
       "Index pull-back {pb}; basket pull-back {bpb}. This retrace is in the index, not in the heavyweights.",
       "Your trail is being tested by the print, not by the stocks: basket {tot}, {with}/{n} still on side."],
      cd=60, step={"eq_print_giveback": 3.0}, note="D4: print retrace >= 8 while the basket is within 1 pt of its value at the best and with >= 10 (19 Oct 12:04 PE). Colour: the exit rule is the owner's."),
    T("basket_reversed", "warning", 85, lambda f: _g(f, "eq_basket_giveback") >= 8 and _W(f) <= 6,
      ["The basket has given back {bpb} points since your best and {with} names remain. The move is over in the stocks.",
       "Stocks have reversed: basket from {bbest} at the best to {tot} now. The index is following them.",
       "This is a real reversal, not noise — the basket lost {bpb} and {leavers} led it."],
      cd=60, step={"eq_basket_giveback": 3.0}, note="D5: basket(best) - basket(now) >= 8 and with <= 6."),
    # ── E. flips and the swing stock ─────────────────────────────────────────────────────────────────
    T("flip_against", "warning", 80, lambda f: f.get("eq_flip_against") and abs(f["eq_flip_against"]["was"]) >= 1.0,
      ["{fsym} just turned: it was helping ({fwas}), now it is against you ({fnow}).",
       "{fsym} flipped sides — {fwas} a minute ago, {fnow} now.",
       "Lost one: {fsym} crossed from helper to hurter ({fwas} → {fnow}).",
       "{fsym} changed its mind. It gave you {fwas}; it has taken that back and more ({fnow})."],
      cd=60, step={"eq_breadth_against": 1}, min_hold_s=60, note="E1: sign of help changed vs 60 s ago, both sides meaningful, was >= +1.0."),
    T("flip_with", "confident", 50, lambda f: f.get("eq_flip_with") and abs(f["eq_flip_with"]["was"]) >= 0.7,
      ["{gsym} has come over: it was against you ({gwas}), now it is with you ({gnow}).",
       "{gsym} stopped fighting and joined ({gwas} → {gnow}).",
       "A convert — {gsym}, from {gwas} to {gnow}."],
      cd=60, step={"eq_breadth_with": 1}, min_hold_s=60, note="E2: flip the other way, was <= -0.7."),
    T("swing_stock", "warning", 85, lambda f: bool(f.get("eq_swing_sym")) and _g(f, "eq_print_giveback") >= 3,
      ["{ssym} is the one that turned this: {satbest} at your best, {snow} now — {sgb} points given back from one name.",
       "The swing stock is {ssym}: it took back {sgb} of the {pb} points the print has lost since the best.",
       "Your best was built with {ssym} at {satbest}. It is {snow} now. That is the trade's story in one name.",
       "{ssym} reversed the trade: {sgb} points back since {besttime}."],
      cd=90, step={"eq_swing_giveback": 1.0}, note="E3: the stock with the largest give-back since the best, >= max(1, 25 % of the print's give-back), print give-back >= 3."),
    T("swing_spread", "descriptive", 55, lambda f: _g(f, "eq_print_giveback") >= 8 and f.get("eq_giveback_max") is not None and f["eq_giveback_max"] < 0.2 * f["eq_print_giveback"],
      ["No single name took this back — the give-back is spread across {gbn} stocks, biggest {gbsym} at {gbmax}.",
       "The whole basket breathed out together: {gbmax} max from any one name.",
       "Not a reversal in one stock; a general exhale. {with} still with you."],
      cd=120, step={"eq_print_giveback": 3.0}, note="E4: print give-back >= 8 and no stock gave back more than 20 % of it."),
    T("flip_pair_banks", "warning", 90, lambda f: bool(f.get("eq_pair_flip_banks")),
      ["Both big banks turned inside a minute — HDFCBANK {hflip} and ICICIBANK {iflip}. That is 19 % of the index changing sides.",
       "HDFCBANK and ICICIBANK have gone the other way together. On a {opt} that is the worst pair to lose."],
      once=True, note="E5: HDFCBANK and ICICIBANK both flipped against within 60 s of each other."),
    # ── F. sector reads ──────────────────────────────────────────────────────────────────────────────
    T("bank_move", "descriptive", 55, lambda f: _g(f, "eq_help_pos") > 0 and _g(f, "eq_sector_banks") >= 0.6 * f["eq_help_pos"] and _g(f, "eq_sector_banks_with") >= 3,
      ["This is a bank move: {bpts} of your {tot} basket points are the five banks ({bwith}/5).",
       "Banks are the whole story ({bwith} of 5, {bpts} pts). IT and RIL and the rest are {rest}.",
       "Financials are driving — {bpts} points from the banks; the rest of the basket is along for the ride."],
      cd=180, note="F1: the banks are >= 60 % of the positive help with >= 3 of 5 meaningful."),
    T("banks_vs_rest", "warning", 60, lambda f: abs(_g(f, "eq_sector_banks")) >= 2 and abs(_g(f, "eq_sector_rest")) >= 2 and _g(f, "eq_sector_banks") * _g(f, "eq_sector_rest") < 0,
      ["Banks and the rest disagree: banks {bpts}, everything else {rpts}. Somebody is wrong.",
       "A split market — financials {bpts}, non-financials {rpts}. The index is the net of that split.",
       "Banks {bpts}, RIL+IT+rest {rpts}. The index is the net of a tug-of-war."],
      cd=150, note="F2: bank help and non-bank help have opposite signs, both |.| >= 2."),
    T("it_against", "descriptive", 40, lambda f: _g(f, "eq_sector_it") <= -1.0 and _g(f, "eq_sector_it_with") == 0,
      ["IT is fighting you: INFY {infy}, TCS {tcs}. Small weight, but both of them.",
       "The two IT names are the other way ({itpts}). Not enough to matter unless the banks join them."],
      cd=180, note="F3: INFY + TCS <= -1.0 with neither meaningful with."),
    T("ril_alone", "warning", 70, lambda f: f.get("eq_sector_ril") is not None and _g(f, "eq_help_pos") > 0 and f["eq_sector_ril"] >= 0.5 * f["eq_help_pos"] and _W(f) <= 5,
      ["RELIANCE is the move: {rilpts} of {tot}. One stock, 7.6 % of the index, and {with} names with it.",
       "This is RIL and little else ({rilshare} % of the basket's help). It can carry an index for a while, not forever — a count, not a forecast."],
      cd=120, note="F4: RELIANCE >= 50 % of the positive help with breadth <= 5."),
    T("all_sectors", "confident", 75, lambda f: bool(f.get("eq_all_sectors_on")) and _W(f) >= 10,
      ["Every sector we track is on your side: banks, IT, RIL, FMCG, autos.",
       "Banks ✓ IT ✓ RIL ✓ FMCG ✓ autos ✓ — no sector is dissenting.",
       "Across the board: {with} of {n}, not one sector against."],
      cd=180, note="F5: every sector's net help >= 0 and with >= 10."),
    T("defensives_lead", "descriptive", 35, lambda f: f.get("eq_top_sym") in DEFENSIVES and f.get("dir") == -1,
      ["FMCG is leading a fall — {sym} is your top name. Defensives falling first is unusual; note it.",
       "Odd leader: {sym}, a defensive, is the biggest help on a PE."],
      cd=240, note="F6: top helper is ITC or HINDUNILVR on a PE."),
    # ── G. stock futures vs cash (colour only: lag 0 s on 19 Oct) ────────────────────────────────────
    T("stock_futs_ahead", "colour", 15, lambda f: _g(f, "eq_fut_lead") >= 5,
      ["Stock futures are running ahead of cash by {lead} basket points right now. (On 19 Oct this had no edge; colour only.)",
       "The stock-futures basket moved {lead} points more than cash in the last 15 s."],
      cd=300, note="G1: 15-s stock-futures basket move minus cash basket move >= +5 in favour. Colour: best cross-corr lag 0 s."),
    T("stock_futs_behind", "colour", 15, lambda f: _g(f, "eq_fut_lead") <= -5,
      ["Cash is ahead of the stock futures by {lead} points — the futures have not followed yet.",
       "Stock futures are lagging the cash names by {lead} basket points."],
      cd=300, note="G2: the mirror of G1."),
    T("basis_widening", "colour", 20, lambda f: _g(f, "eq_basis_bps") >= 5 and _g(f, "hold_s") >= 120,
      ["The stock-futures basis has widened {bps} bp in your direction since entry — futures traders leaning your way.",
       "Since entry the stock futures have moved {bps} bp more than their cash names, your way."],
      cd=300, min_hold_s=120, note="G3: weight-averaged basis change since entry >= 0.05 % in favour after 120 s."),
    # ── H. flow (present tense only: corr 0.00 with the next 30 s) ───────────────────────────────────
    T("pressed_name", "descriptive", 45, lambda f: bool(f.get("eq_pressed_name")),
      ["Aggressive {side} in {psym} for {psecs} s — the move is being pressed.",
       "{psym}: {psecs} seconds of {side} hitting the {olevel}. Someone wants it {dirword_er}.",
       "{side} are leaning on {psym} ({psecs} s and counting)."],
      cd=90, note="H1: a helper with aggressive flow in the trade's direction for >= 40 s."),
    T("fought_name", "warning", 55, lambda f: bool(f.get("eq_fought_name")),
      ["{qsym} is being hit against you for {qsecs} s — that is where the other side is working.",
       "Aggressive {oside} in {qsym} for {qsecs} s ({qpts}). That is the name where a reversal would show first."],
      cd=90, note="H2: a hurter with aggressive flow against the trade for >= 40 s."),
    T("flow_broad_with", "descriptive", 50, lambda f: _g(f, "eq_flow_with_wpct") >= 40,
      ["The aggressive flow is with you across {fwn} names ({fwpct} % of tracked weight).",
       "{side} are pressing {fwn} heavyweights at once."],
      cd=120, note="H3: names with run_with >= 30 s are >= 40 % of tracked weight."),
    T("flow_broad_against", "warning", 70, lambda f: _g(f, "eq_flow_against_wpct") >= 40,
      ["Aggressive {oside} across {fan} names ({fapct} % of weight) while the print is still {spot}. The flow has turned before the price.",
       "The other side is now pressing {fan} heavyweights. Price has not followed yet; the count has."],
      cd=90, note="H4: names with run_against >= 30 s are >= 40 % of tracked weight."),
    T("book_pulled", "warning", 60, lambda f: bool(f.get("eq_top_pulled")),
      ["The {level} in {sym} was pulled, not eaten — the resting orders walked away.",
       "{sym}'s {level} side: PULLED. Liquidity left; it was not consumed."],
      cd=120, note="H5: the side the trade needs to hold (bids for a CE, asks for a PE) is PULLED on the top helper."),
    T("book_refilling_against", "descriptive", 40, lambda f: len(f.get("eq_refilling") or []) >= 2,
      ["{refill_list} are refilling the {olevel} — the move is being absorbed in the book, not running away.",
       "The {olevel} keeps refilling in {refill_list}: the helpers are being met with fresh orders."],
      cd=120, note="H6: the side the trade must break is REFILLING in >= 2 helpers."),
    T("flow_vs_price", "warning", 65, lambda f: f.get("eq_top_sym") and _g(f, "eq_top_run_against") >= 40,
      ["{sym} is still your best name ({pts}) but the aggressive flow there has been against you for {asecs} s. Price and flow disagree.",
       "{sym} is helping on price and being {oside}-hit on flow ({asecs} s)."],
      cd=90, note="H7: top helper on price, aggressive flow against for >= 40 s."),
    # ── I. first mover / episode ─────────────────────────────────────────────────────────────────────
    T("first_mover", "descriptive", 45, lambda f: bool(f.get("eq_first_mover")),
      ["{fm} moved first — it crossed its 2σ line at {ft}, before the index.",
       "First mover: {fm}. The episode is {eptype}; {ncross} names have crossed since.",
       "This leg started in {fm} ({eptype}). Everyone else followed."],
      once=True, note="I1: episode.first when the episode's direction is the trade's and it began <= 120 s before entry."),
    T("futures_led", "warning", 60, lambda f: f.get("eq_ep_type") == "FUTURES-LED" and _W(f) <= 5 and _g(f, "hold_s") >= 30,
      ["This was a FUTURES-LED episode and the stocks have not followed: {with}/{n} after {age} s.",
       "Futures moved first; the cash names are still thinking about it ({with} with you)."],
      once=True, min_hold_s=30, note="I2: FUTURES-LED episode and with <= 5 at 30 s."),
    T("single_name", "warning", 65, lambda f: f.get("eq_ep_type") == "SINGLE-NAME",
      ["Single-name episode: {fm} is the whole move. The index is {fm} in disguise.",
       "The episode is SINGLE-NAME — {fm} started it and nobody meaningful has joined."],
      once=True, note="I3: episode type SINGLE-NAME."),
    T("basket_led", "confident", 50, lambda f: f.get("eq_ep_type") == "BASKET-LED" and _W(f) >= 7,
      ["BASKET-LED: the stocks moved before the futures, and {with} of them are still with you.",
       "The heavyweights started this one ({fm} first), the index followed. The right way round."],
      once=True, note="I4: BASKET-LED episode with with >= 7."),
    # ── J. the entry moment (reference = the 90 s before entry, or 60 s from the market ring) ─────────
    T("breakout_made_by", "descriptive", 60, lambda f: f.get("eq_pre_top") and f["eq_pre_top"][0][1] >= 2,
      ["This breakout was made by {jsym1} ({jpts1}) and {jsym2} ({jpts2}); {jwith} of {n} moved with it.",
       "The last {jref} s: {jsym1} {jpts1}, {jsym2} {jpts2}, {jsym3} {jpts3}. That is what you just bought.",
       "Who broke the range: {jsym1}, then {jsym2}. {jagainst} names fought it."],
      once=True, note="J1: top pre-entry helper >= 2 pts."),
    T("breakout_fought_by", "warning", 55, lambda f: f.get("eq_pre_bot") and f["eq_pre_bot"][0][1] <= -2,
      ["{jhsym} fought this breakout the whole way ({jhpts}). It will have to give up for the move to extend.",
       "Note {jhsym}: {jhpts} against the breakout you just bought."],
      once=True, note="J2: bottom pre-entry hurter <= -2 pts."),
    T("breakout_on_air", "warning", 75, lambda f: f.get("eq_pre_with") is not None and _g(f, "eq_pre_spot") >= 3 and ((f.get("eq_pre_ratio") is not None and f["eq_pre_ratio"] < AIR_RATIO) or f["eq_pre_with"] <= 4),
      ["This breakout is an index print: the basket we track moved {jtot} vs the index's {jspot}. {jwith} names with it. Needs the stocks to catch up.",
       "Thin breakout — {jwith} heavyweights took part. You are early or you are wrong; the next minute tells which."],
      once=True, note="J3: the print moved >= 3 in favour before entry and basket/print < 0.4 or with <= 4. On 19 Oct: 16 % of winners, 15 % of losers — a warning, not a veto."),
    T("breakout_broad", "confident", 65, lambda f: _g(f, "eq_pre_with") >= 9 and _g(f, "eq_pre_ratio") >= 0.8,
      ["A proper breakout: {jwith} of {n} moved with it, basket {jtot} vs print {jspot}.",
       "The stocks broke out with the index — {jwith} names, {jbwith} of 5 banks."],
      once=True, note="J4: pre-entry with >= 9 and ratio >= 0.8."),
    T("late_to_it", "warning", 60, lambda f: _g(f, "eq_pre_spot") >= 20,
      ["The move you bought is already {jspot} points old — {jsym1} and {jsym2} did most of it before your fill.",
       "You are buying after a {jspot}-point run in {jref} s. The basket made it; what you need is a second leg."],
      once=True, note="J5: the print moved >= 20 pts in favour over the pre-entry window."),
    T("day_context", "descriptive", 30, lambda f: f.get("eq_day_with") is not None and f.get("eq_day_leader"),
      ["On the day the heavyweights are {daywith}/{n} your way; the day's leader your way is {leader} ({chg} %).",
       "Day picture: {leader} {chg} %, {laggard} {lchg} %. Your {opt} is {with_or_against} the day's drift."],
      once=True, note="J6: % vs previous close from snap['close'] at entry."),
    # ── K. holding reassurance (only when the facts hold) ────────────────────────────────────────────
    T("still_broad_after", "confident", 55, lambda f: _g(f, "hold_s") >= 120 and _W(f) >= 9 and f.get("eq_with60") is not None and _W(f) >= f["eq_with60"],
      ["{min} minutes in and still {with} names with you. The basket has not thinned.",
       "Breadth is holding at {with}/{n} after {min} min — the names that started this are still in it."],
      cd=120, min_hold_s=120, step={"hold_s": 120}, note="K1: age >= 120 s, with >= 9 and not below a minute ago."),
    T("helper_holding_at_best", "confident", 50, lambda f: bool(f.get("eq_new_best")) and f.get("eq_top_sym") and f["eq_top_sym"] == f.get("eq_top60_sym") and _g(f, "eq_top_help") > _g(f, "eq_top_help60"),
      ["New best, and {sym} is still the one making it ({pts}, rising).",
       "{sym} pushed the trade to a new best — {pts} and climbing."],
      cd=90, min_hold_s=60, note="K2: at a new best, the top helper is the same as 60 s ago and its help is rising."),
    T("best_without_basket", "warning", 75, lambda f: bool(f.get("eq_new_best")) and f.get("eq_basket60") is not None and _TOT(f) < f["eq_basket60"],
      ["New best on the print, but the basket is LOWER than a minute ago ({tot} vs {tot60}). The stocks did not make this high.",
       "The index made a new best without its heavyweights — basket {tot}, down from {tot60}."],
      cd=60, min_hold_s=60, note="K3: at a new best, basket below its value 60 s ago."),
    T("nothing_meaningful", "descriptive", 50, lambda f: _N(f) > 0 and _W(f) == 0 and _A(f) == 0 and _g(f, "hold_s") >= 20,
      ["Nothing meaningful is carrying this yet: the biggest helper is {csym} at {abs} pts total either way.",
       "The basket is asleep — no name has moved 0.03 % either way since your entry."],
      cd=90, note="K4: with = 0 and against = 0 after 20 s."),
    # ── L. exit review (kind 'review': rendered by review_lines(), never fired live by the selector) ──
    T("made_and_ruined", "review", 100, lambda f: _g(f, "pnl_pts") > 0 and len(f.get("eq_made") or []) >= 2 and f["eq_made"][1][1] >= 1 and _g(f, "eq_giveback_max") >= 1,
      ["This trade was made by {m1} ({mp1}) and {m2} ({mp2}); {r1} ruined the last {gbmax} points.",
       "Credit: {m1}, {m2}. Blame for the give-back: {r1} ({rp1}), {r2} ({rp2}).",
       "Built by {m1} and {m2}, trimmed by {r1}. Net: {pnl} on the print."],
      once=True, kind="review", note="L1: winner, the two names that built the best >= 1 each, some stock gave back >= 1."),
    T("ruined_by", "review", 100, lambda f: _g(f, "pnl_pts") <= 0 and _g(f, "eq_bot_help") <= -1,
      ["Ruined by {r1} ({rp1}) and {r2} ({rp2}): {rshare} % of the give-back came from those two.",
       "{ssym} reversed this trade. It was {ratbest} at your best and {rnow} at the exit.",
       "The loser's name is {hsym}: {hpts} points against from one stock, {against} names against in all."],
      once=True, kind="review", note="L2: loser with a hurter <= -1 at the exit."),
    T("nobody_made_it", "review", 100, lambda f: _g(f, "pnl_pts") <= 0 and (not f.get("eq_made") or f["eq_made"][0][1] < 1),
      ["Nobody made this trade. The basket never confirmed ({maxwith} names at most); it was an index wobble.",
       "No heavyweight ever got going — peak breadth {maxwith}/{n}. There was nothing carrying it."],
      once=True, kind="review", note="L3: loser and no stock ever contributed >= 1 pt at the best."),
    T("spread_exhale", "review", 100, lambda f: _g(f, "pnl_pts") > 0 and _g(f, "eq_print_giveback") >= 3 and f.get("eq_giveback_max") is not None and f["eq_giveback_max"] < 0.2 * f["eq_print_giveback"],
      ["No single name ruined this; the whole basket breathed out together ({gbn} names, max {gbmax}).",
       "The give-back was collective — {gbmax} from {gbsym} at most. A good trade that ran out of {side} everywhere at once."],
      once=True, kind="review", note="L4: winner, no stock gave back more than 20 % of the print's give-back."),
    T("exit_basket_still_with", "review", 95, lambda f: _W(f) >= 10 and f.get("eq_basket_at_best") is not None and _TOT(f) >= f["eq_basket_at_best"] - 2,
      ["You were trailed out by the index print while {with} of {n} names were still with you (basket {tot}). The rule is the rule; the stocks had not turned.",
       "Out on the print, not on the stocks: basket {tot} at the close, {with}/{n} on side."],
      once=True, kind="review", note="L5: at the exit with >= 10 and the basket within 2 pts of its value at the best."),
    T("exit_breadth_collapsed", "review", 95, lambda f: f.get("eq_with_at_best") is not None and _W(f) <= f["eq_with_at_best"] - 5,
      ["Breadth went from {bwith_best} at your best to {with} at the exit. The basket left before the price did.",
       "From {bwith_best} names to {with}. The stocks had already said it before the print did."],
      once=True, kind="review", note="L6: with(exit) <= with(best) - 5."),
    # ── M. rare / colour ─────────────────────────────────────────────────────────────────────────────
    T("heaviest_flat", "descriptive", 35, lambda f: f.get("eq_hdfc_help") is not None and abs(f["eq_hdfc_help"]) < (_th_of(f, "HDFCBANK") or 0.7) and _SP(f) >= 10,
      ["HDFCBANK has not moved at all — the 10 % of the index that matters most is sitting this out.",
       "{spot} points of print and HDFCBANK is flat ({hdfc}). Whatever this is, it is not a bank move."],
      cd=240, note="M1: |HDFCBANK help| < its threshold with the print >= 10."),
    T("opposite_pair", "descriptive", 30, lambda f: bool(f.get("eq_opposite_pair")),
      ["{osector} is split down the middle: {oa} {opa} vs {ob} {opb}.",
       "Within {osector}, {oa} and {ob} are pulling opposite ways."],
      cd=240, note="M2: one name of a sector >= +1, another <= -1."),
    T("unanimous_against", "warning", 95, lambda f: _A(f) >= 10,
      ["{against} of {n} heavyweights are against you. The index print is the only thing on your side.",
       "The basket has voted: {against} names the other way."],
      cd=60, step={"eq_breadth_against": 1}, note="M3: against >= 10."),
    T("basket_quiet", "descriptive", 35, lambda f: f.get("eq_abs_sum") is not None and f["eq_abs_sum"] < 2 and _g(f, "hold_s") >= 60,
      ["Quiet basket — the {n} names have barely moved (total {abs} pts either way) in {min} min.",
       "Nothing is happening in the stocks. The trade is marking time."],
      cd=180, min_hold_s=60, note="M4: Σ|pts| < 2 after 60 s."),
    T("volume_dry", "descriptive", 30, lambda f: _g(f, "eq_vol_dry_n") >= 10,
      ["Volume has dried up in {dryn} of {n} names (under half their 15-s baseline).",
       "The heavyweights are trading thin — {dryn} names below half their normal pace."],
      cd=240, note="M5: domino tiles act < 0.5 for >= 10 names."),
    T("recruit_wave", "confident", 60, lambda f: len(f.get("eq_wave_with") or []) >= 3,
      ["A wave: {wlist} all crossed 2σ in the same 15 s, your way.",
       "{wn} names just jumped together ({wlist})."],
      cd=60, note="M6: >= 3 names with 15-s z >= 2 in the trade's direction."),
    T("recruit_wave_against", "warning", 85, lambda f: len(f.get("eq_wave_against") or []) >= 3,
      ["{an} names just jumped the other way together: {alist}. The print has not reacted yet.",
       "A counter-wave in {alist}. The next 30 s of the print will show whether it matters."],
      cd=60, note="M7: >= 3 names with 15-s z <= -2 against the trade."),
]

_HOT = [t for t in TEMPLATES if t.tone == "warning" and t.kind != "review" and not t.once]


# ── exit review lines (for the review card; the core selector never fires kind 'review') ─────────────
def review_lines(t: dict, f: dict, limit: int = 2) -> List[str]:
    """Render the L-group remarks from the closed trade `t` and the last facts `f`. Highest prio first."""
    if not f:
        return []
    ff = dict(f, pnl_pts=t.get("pnl_pts", f.get("pnl_pts")))
    out = []
    for tp in sorted((x for x in TEMPLATES if x.kind == "review"), key=lambda x: -x.prio):
        try:
            if tp.when(ff):
                out.append(tp.pick(int(round(t.get("t_in") or ff.get("trade_id") or 0)), 0).format(**dict(ff, **S(ff))))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


if __name__ == "__main__":        # a quick count
    ph = sum(len(t.phrasings) for t in TEMPLATES)
    print(f"templates {len(TEMPLATES)} · phrasings {ph} · facts {len(FACTS)}")
