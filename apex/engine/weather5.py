"""
Photo version 5 (10 Nov, docs/38 section 6): the first instrumentation batch, ten items.

  R  the system itself      105 engine service delay · 106 persistence health · 107 cross-input synchronisation ·
                            108 fresh weighted coverage
  S  the models' footing    109 flow-sign uncertainty · 110 response-model reliability · 128 research lineage
  T  the request            120 opportunity survival · 121 contract-path continuity · 122 fill evidence

Units are in the names: _s seconds, _ms milliseconds, _pts points, _w a share of index weight (0-1), _share a share of
volume (0-1), _n a count. None of these fields has a direction: nothing is flipped for a put. A field that could not be
measured is None, never 0, and `v5_missing` (housekeeping, not weather) says why, by item number.

An OBSERVER. No book, rule or exit reads these fields. Items 105 (the millisecond fields), 106 and 128 describe the
machine and the provenance, not the market: they are wall-clock or text, differ between a live session and a replay of
the same tape, and so are recorded but kept out of the nightly rule search (search.TELEMETRY). docs/38: "not automatic
trade gates".

Items 123-126 (the held position) are a SEPARATE continuation photograph (hold_photo below), stored on the trade as
`weather_hold`. They are never written into the entry photograph.

No look-ahead: everything read is the state at this step. The lapsed-request log holds only earlier requests.
"""
import zlib

from .weather import _fin, _r

NEW_ITEMS = (105, 106, 107, 108, 109, 110, 120, 121, 122, 128)
HOLD_ITEMS_N = (123, 124, 125, 126)
FRESH_S = 5.0                 # an input older than this is stale (gen2.HW_FRESH_S, the same number)
CLUSTER_S = 60.0              # requests of one book and side closer than this are one opportunity, retried
PATH_GAP_S = 3.0              # a hole this long in a contract's 1-Hz history is a missing segment
ATM_LOG_MAX = 400


def tick(W, now_s, atm):
    """Once per engine step: remember when the ATM strike changed (item 121). Cheap: one comparison."""
    if W is None or atm is None:
        return
    log = getattr(W, "atm_log", None)
    if log is None:
        log = W.atm_log = []
    if not log:
        log.append((float(now_s), atm, True))          # the first ATM of the day is not a switch
    elif log[-1][1] != atm:
        log.append((float(now_s), atm, False))
        if len(log) > ATM_LOG_MAX:
            del log[:ATM_LOG_MAX // 2]


def photo_v5(out, ctx, d, opt, book, b, sp):
    t = ctx.get("now_s")
    errs, miss = [], {}
    for fn in (_p_engine, _p_save, _p_sync, _p_cover, _p_sign, _p_resp, _p_opp, _p_path, _p_fill, _p_lineage):
        try:
            fn(out, ctx, d, opt or {}, book, t, miss)
        except Exception:                           # noqa: BLE001  (an observer: never stops the entry)
            errs.append(fn.__name__)
    if errs:
        out["v5_error"] = ",".join(errs)
    if miss:
        out["v5_missing"] = " | ".join(f"{k}: {v}" for k, v in sorted(miss.items()))


def _age(snap, i, now_s):
    """Seconds since row i's last quote packet, or None (no packet yet)."""
    if snap is None or i is None:
        return None
    rn = int(snap["recv_ns"][i])
    return (now_s * 1e9 - rn) / 1e9 if rn > 0 else None


def _snap(ctx):
    m = ctx.get("_m")
    return getattr(m, "snap", None) if m is not None else None


# ── 105 engine service delay ─────────────────────────────────────────────────────────────────────────────────────────
E105 = ("eng_step_gap_s", "eng_feed_age_s", "eng_p50_ms", "eng_p95_ms", "eng_max_ms", "eng_over300_n")


def _p_engine(out, ctx, d, o, book, t, miss):
    eng = ctx.get("_eng") or {}
    out["eng_step_gap_s"] = _r(_fin(ctx.get("step_gap")), 3)       # market seconds since the previous engine step
    out["eng_feed_age_s"] = _r(_fin(eng.get("feed_age")), 3)       # age of the newest packet on any row
    pf = eng.get("perf") or {}
    out["eng_p50_ms"], out["eng_p95_ms"], out["eng_max_ms"] = pf.get("p50"), pf.get("p95"), pf.get("max")
    out["eng_over300_n"] = pf.get("over300")                       # the last FINISHED minute: no partial minute
    if not pf:
        miss[105] = "no finished minute of step times yet"


# ── 106 persistence health ───────────────────────────────────────────────────────────────────────────────────────────
E106 = ("save_lag_n", "save_pending_s", "save_last_ms", "save_ok_age_s", "save_errors_n", "save_fails_row_n")


def _p_save(out, ctx, d, o, book, t, miss):
    for k in E106:
        out[k] = None
    from . import paper
    st = paper.save_status()
    out["save_lag_n"] = st.get("lag")                              # states requested and not yet on disk (0, 1 or 2)
    out["save_pending_s"] = st.get("pending_s")                    # how long the oldest of them has waited
    out["save_last_ms"] = st.get("last_ms")                        # the last write: text to disk, fsync, replace
    out["save_ok_age_s"] = st.get("last_ok_age_s")                 # seconds since a state last reached the disk
    out["save_errors_n"], out["save_fails_row_n"] = st.get("errors"), st.get("fails_row")
    if st.get("last_ms") is None:
        miss[106] = "no background save has completed yet"


# ── 107 cross-input synchronisation ──────────────────────────────────────────────────────────────────────────────────
E107 = ("sync_spot_age_s", "sync_fut_age_s", "sync_opt_age_s", "sync_opp_age_s", "sync_oldest_s", "sync_newest_s",
        "sync_spread_s", "sync_n")


def _p_sync(out, ctx, d, o, book, t, miss):
    for k in E107:
        out[k] = None
    snap = _snap(ctx)
    if snap is None or t is None:
        miss[107] = "no market snapshot"
        return
    from .weather4 import _other_leg
    oth = _other_leg(ctx, o) if o else None
    ages = {"spot": _age(snap, (ctx.get("_eng") or {}).get("spot_id"), t), "fut": _age(snap, ctx.get("fut_id"), t),
            "opt": _age(snap, o.get("id"), t), "opp": _age(snap, (oth or {}).get("id"), t)}
    for k, v in ages.items():
        out[f"sync_{k}_age_s"] = _r(v, 3)
    xs = [v for v in ages.values() if v is not None]
    out["sync_n"] = len(xs)                                        # inputs with a known receive time, of four
    if xs:
        out["sync_oldest_s"], out["sync_newest_s"] = _r(max(xs), 3), _r(min(xs), 3)
        out["sync_spread_s"] = _r(max(xs) - min(xs), 3)            # how far apart in time the inputs were seen
    else:
        miss[107] = "no input has a receive time"


# ── 108 fresh weighted coverage ──────────────────────────────────────────────────────────────────────────────────────
E108 = ("hw_fresh_w", "hwf_fresh_w", "hw_stale_top5_n", "hw_stale_max_s", "hw_cover60_w", "hw_cover300_w",
        "grp_cover_min300_w")


def _p_cover(out, ctx, d, o, book, t, miss):
    import numpy as np
    for k in E108:
        out[k] = None
    snap, ef = _snap(ctx), ctx.get("eq_fut")
    why = []
    if snap is not None and ef is not None and t is not None and len(ef[1]):
        fids, w, ids = ef
        w = np.asarray(w, float)
        tot = float(w.sum())
        now_ns = t * 1e9
        rc = snap["recv_ns"][np.asarray(ids, int)].astype(float)
        age = np.where(rc > 0, (now_ns - rc) / 1e9, np.inf)
        if tot > 0:
            out["hw_fresh_w"] = _r(float(w[age <= FRESH_S].sum()) / tot, 4)          # cash, share of index weight
            fi = np.asarray(fids, int)
            okf = fi >= 0
            if okf.any():
                rf = np.where(okf, snap["recv_ns"][np.where(okf, fi, 0)].astype(float), 0.0)
                agf = np.where(rf > 0, (now_ns - rf) / 1e9, np.inf)
                out["hwf_fresh_w"] = _r(float(w[agf <= FRESH_S].sum()) / tot, 4)     # stock futures, same weights
            else:
                why.append("no stock futures on the tape")
            top = np.argsort(-w)[:5]
            out["hw_stale_top5_n"] = int((age[top] > FRESH_S).sum())                 # stale among the five heaviest
            mx = float(age[top].max())
            out["hw_stale_max_s"] = _r(min(mx, 9999.0), 1)                           # 9999 = never seen today
    else:
        why.append("no heavyweight table")
    g = ctx.get("gen2")
    hw = getattr(g, "hw", None) if g is not None else None
    if hw and getattr(g, "hw_w", None):
        wt = sum(g.hw_w)
        for lag in (60, 300):
            r = g._hw_ret(lag)
            if r is not None and wt > 0 and len(r) == len(g.hw_w):
                out[f"hw_cover{lag}_w"] = _r(sum(wi for ri, wi in zip(r, g.hw_w) if ri is not None) / wt, 4)
        r = g._hw_ret(300)
        if r is not None and g.hw_g and len(r) == len(g.hw_g):
            cov = {}
            for ri, wi, gi in zip(r, g.hw_w, g.hw_g):
                c = cov.setdefault(gi, [0.0, 0.0])
                c[1] += wi
                c[0] += wi if ri is not None else 0.0
            vals = [a / z for a, z in cov.values() if z > 0]
            out["grp_cover_min300_w"] = _r(min(vals), 4) if vals else None           # the worst-covered group
        if out["hw_cover300_w"] is None:
            why.append("under 300 s of heavyweight history")
    else:
        why.append("no fresh-price history (gen2 off)")
    if why:
        miss[108] = "; ".join(why)


# ── 109 flow-sign uncertainty ────────────────────────────────────────────────────────────────────────────────────────
E109 = ("sign_out_share60", "sign_tick_share60", "sign_none_share60", "sign_out_share300", "sign_none_share300")


def _p_sign(out, ctx, d, o, book, t, miss):
    for k in E109:
        out[k] = None
    g = ctx.get("gen2")
    sv = g.sign_view() if g is not None and hasattr(g, "sign_view") else None
    if not sv:
        miss[109] = "no classified futures volume yet"
        return
    for k in E109:
        out[k] = _r(sv.get(k), 4)


# ── 110 response-model reliability ───────────────────────────────────────────────────────────────────────────────────
E110 = ("resp_beta10", "resp_beta60", "resp_h_ratio", "resp_resid_sd60_pts", "resp_fit60_n", "resp_clean_s", "resp_ready",
        "n02_cond", "n02_se_fast", "n02_se_slow", "n02_sum_sd", "n02_ready")


def _p_resp(out, ctx, d, o, book, t, miss):
    for k in E110:
        out[k] = None
    g = ctx.get("gen2")
    if g is None:
        miss[110] = "gen2 off"
        return
    v = g.view()
    b10, b60 = _fin(v.get("beta")), _fin(v.get("beta60"))
    out["resp_beta10"], out["resp_beta60"] = _r(b10, 4), _r(b60, 4)        # points per unit pressure, 10-s and 60-s fits
    out["resp_h_ratio"] = _r(b60 / b10, 3) if b10 and b60 else None        # 1 = the two horizons agree
    out["resp_resid_sd60_pts"] = _r(_fin(v.get("beta60_resid_sd")), 3)
    out["resp_fit60_n"], out["resp_clean_s"] = v.get("n_fit60"), v.get("clean_s")
    out["resp_ready"] = bool(v.get("warm")) and b60 is not None
    cond, se = _fin(v.get("n02_cond")), v.get("n02_se")
    out["n02_cond"] = _r(min(cond, 1e9), 1) if cond is not None else None  # conditioning of the two-kernel system
    if se:
        out["n02_se_fast"], out["n02_se_slow"] = _r(_fin(se[0]), 4), _r(_fin(se[1]), 4)
    out["n02_sum_sd"] = _r(_fin(v.get("n02_sum_sd")), 4)                   # how much the summed response has moved
    out["n02_ready"] = bool((v.get("ready") or {}).get("n02_relax"))
    if not out["resp_ready"]:
        miss[110] = "response model not ready (warming, or no positive 60-s response)"


# ── 120 opportunity survival ─────────────────────────────────────────────────────────────────────────────────────────
E120 = ("req_first", "req_retry_n", "req_cluster_s", "req_lapsed_n", "sig_age_s")


def _cluster(log, t, d):
    """The chain of this side's earlier lapsed requests ending within CLUSTER_S of now: (count, first time)."""
    n, first, last = 0, None, t
    for ts, ds in reversed(log):
        if ds != d:
            continue
        if last - ts > CLUSTER_S:
            break
        n, first, last = n + 1, ts, ts
    return n, first


def _p_opp(out, ctx, d, o, book, t, miss):
    for k in E120:
        out[k] = None
    if book is None or t is None:
        miss[120] = "no book"
        return
    log = [x for x in ((getattr(book, "ctl", None) or {}).get("req_log") or ()) if x[0] < t]
    n, first = _cluster(log, t, d)
    out["req_first"], out["req_retry_n"] = (n == 0), n             # retries of one opportunity are not new setups
    out["req_cluster_s"] = _r(t - first, 1) if first is not None else 0.0
    out["req_lapsed_n"] = len(log)                                 # this book's lapsed requests since its last fill
    gen = (getattr(book, "p", None) or {}).get("gen")
    g = ctx.get("gen2")
    sg = (getattr(g, "sig", None) or {}).get(gen) if gen and g is not None else None
    if sg and sg.get("t") is not None:
        out["sig_age_s"] = _r(t - sg["t"], 2)                      # second-generation books: the signal's own age
    else:
        ep = ctx.get("episode") or {}
        t0 = _fin(ep.get("t0"))
        out["sig_age_s"] = _r(t - t0, 2) if t0 is not None and t >= t0 else None
        if out["sig_age_s"] is None:
            miss[120] = "signal age unknown (no episode start on this trigger)"


# ── 121 contract-path continuity ─────────────────────────────────────────────────────────────────────────────────────
E121 = ("opt_path_s", "opt_path_gap_n300", "opt_path_gap_max_s", "atm_switch_s", "atm_switch_n15", "opt_is_atm")


def _p_path(out, ctx, d, o, book, t, miss):
    for k in E121:
        out[k] = None
    why = []
    hist = (ctx.get("ohist") or {}).get(o.get("id")) if o.get("id") is not None else None
    if hist and t is not None:
        ts = [rec[0] for rec in hist if rec[0] <= t and len(rec) > 3 and rec[3]]
        if ts:
            end = len(ts) - 1                                      # the unbroken stretch ending now
            k = end
            while k > 0 and ts[k] - ts[k - 1] <= PATH_GAP_S:
                k -= 1
            out["opt_path_s"] = _r(ts[end] - ts[k], 1) if t - ts[end] <= PATH_GAP_S else 0.0
            w = [x for x in ts if x >= t - 300.0]
            gaps = [b_ - a_ for a_, b_ in zip(w, w[1:]) if b_ - a_ > PATH_GAP_S]
            if w and t - w[-1] > PATH_GAP_S:
                gaps.append(t - w[-1])
            out["opt_path_gap_n300"] = len(gaps)                   # missing segments in the last five minutes
            out["opt_path_gap_max_s"] = _r(max(gaps), 1) if gaps else 0.0
        else:
            why.append("contract has no priced history")
    else:
        why.append("contract has no history")
    W = ctx.get("_wx")
    log = getattr(W, "atm_log", None) if W is not None else None
    atm = (ctx.get("_eng") or {}).get("atm")
    if log and t is not None:
        sw = [x for x in log if not x[2] and x[0] <= t]
        out["atm_switch_s"] = _r(t - sw[-1][0], 1) if sw else None     # None = the ATM strike has not changed today
        out["atm_switch_n15"] = sum(1 for x in sw if t - x[0] <= 900.0)
    else:
        why.append("no ATM log")
    if atm is not None and o.get("strike") is not None:
        out["opt_is_atm"] = bool(float(o["strike"]) == float(atm))
    if why:
        miss[121] = "; ".join(why)


# ── 122 fill evidence (what the trigger could know; the fill itself is recorded on the trade as fill_ev) ──────────────
E122 = ("trig_print_age_s", "trig_ltp_vs_mid_pts", "trig_quote_ok")


def _p_fill(out, ctx, d, o, book, t, miss):
    for k in E122:
        out[k] = None
    if not o:
        miss[122] = "no contract"
        return
    out["trig_print_age_s"] = _r(_fin(o.get("age")), 2)            # age of the print on the screen at the trigger
    bid, ask, ltp = _fin(o.get("bid")), _fin(o.get("ask")), _fin(o.get("ltp"))
    ok = bool(bid and ask and ask >= bid)
    out["trig_quote_ok"] = ok
    out["trig_ltp_vs_mid_pts"] = _r(ltp - (bid + ask) / 2, 2) if ok and ltp else None   # + = the print is above the quote
    if out["trig_print_age_s"] is None:
        miss[122] = "the contract has no print age"


def fill_evidence(pe, o, waited, ctx):
    """Item 122 at the FILL, stored on the trade (never in the entry photograph): how the fill was observed."""
    try:
        d = 1 if (o or {}).get("rr") == "CE" else -1
        fut, f0 = _fin(ctx.get("fut")), _fin(pe.get("fut_trig"))
        age = _fin((o or {}).get("age"))
        return {"gap_s": _r(waited, 3),                            # request to the observation that filled it
                "print_age_s": _r(age, 3),                         # that observation's own age at the fill step
                "post_request": bool(age is not None and age < waited),
                "max_step_gap_s": _r(_fin(pe.get("max_gap")) or 0.0, 3),
                "fut_move_pts": _r((fut - f0) * d, 2) if fut is not None and f0 is not None else None}   # + = our way
    except Exception:                               # noqa: BLE001
        return None


# ── 128 research lineage and support ─────────────────────────────────────────────────────────────────────────────────
E128 = ("lin_schema", "lin_rule_hash", "lin_art_cutoff", "lin_in_support", "lin_eff_n")


def rule_hash(book):
    p = getattr(book, "p", None) or {}
    txt = repr(sorted((str(k), repr(v)) for k, v in p.items()))
    return f"{zlib.crc32(txt.encode('utf-8')) & 0xffffffff:08x}"


def _p_lineage(out, ctx, d, o, book, t, miss):
    for k in E128:
        out[k] = None
    from . import gen2 as _g2, weather as _w
    out["lin_schema"] = f"w{_w.VERSION}.g{_g2.VERSION}"            # photo version and signal-engine version
    if book is None:
        miss[128] = "no book"
        return
    out["lin_rule_hash"] = rule_hash(book)                         # the book's parameters as they are right now
    p = getattr(book, "p", None) or {}
    g = ctx.get("gen2")
    if p.get("gen") and g is not None:
        out["lin_in_support"] = bool(g.ready(p["gen"])) if p["gen"] in ("n02_relax", "n06_lead") else bool(g.warm)
        out["lin_eff_n"] = int((getattr(g, "n_sig", None) or {}).get(p["gen"], 0))   # this signal's episodes today
        miss[128] = "no artifact cutoff: a frozen specification, never fitted to a tape"
    else:
        cut = (ctx.get("_eng") or {}).get("pool_cutoff")
        out["lin_art_cutoff"] = cut
        miss[128] = ("support and independent episodes are not defined for a hand-written book"
                     + ("" if cut else "; no pool cutoff"))


ITEMS5 = {
    105: ("Engine service delay", E105),
    106: ("Persistence health", E106),
    107: ("Cross-input synchronisation", E107),
    108: ("Fresh weighted coverage", E108),
    109: ("Flow-sign uncertainty", E109),
    110: ("Response-model reliability", E110),
    120: ("Opportunity survival", E120),
    121: ("Contract-path continuity", E121),
    122: ("Fill evidence", E122),
    128: ("Research lineage and support", E128),
}
# recorded, never searched: the machine's own timing and the provenance text (see the module note)
TELEMETRY = frozenset(E105[2:] + E106 + ("lin_schema", "lin_rule_hash", "lin_art_cutoff"))


# ── 123-126: the CONTINUATION photograph (a held position; never part of the entry photograph) ───────────────────────
# A few snapshots per trade: at fixed ages, at the exit request and at the close. Stored on the trade as `weather_hold`.
# Points are premium points of the held option unless the name says fut. "with" / "against" are relative to the trade.
HOLD_MARKS = (60.0, 300.0, 900.0, 1800.0)
H123 = ("hold_s", "gain_pts", "gain_pct", "peak_pts", "time_to_peak_s", "peak_age_s", "gain_vs_peak")
H124 = ("giveback_pts", "giveback_share", "giveback_rate_pts_min", "worst_pts", "fut_fav_pts", "fut_best_fav_pts",
        "fut_giveback_pts")
H125 = ("attr_delta_pts", "attr_theta_pts", "attr_iv_chg", "attr_resid_pts")
H126 = ("thesis_ep_against", "thesis_fires_with_n", "thesis_fires_against_n", "thesis_held_with_n",
        "thesis_held_against_n", "thesis_impact_with")
HOLD_ITEMS = {123: ("Held gain maturity", H123), 124: ("Held giveback dynamics", H124),
              125: ("Held premium attribution", H125), 126: ("Live thesis disagreement", H126)}


def hold_photo(pos, ctx, o, mark):
    """One continuation snapshot. Reads only the position and this step's state. None for what cannot be measured."""
    out = {"mark": mark, "time": ctx["now_dt"].strftime("%H:%M:%S") if ctx.get("now_dt") is not None else None}
    for k in H123 + H124 + H125 + H126:
        out[k] = None
    errs = []
    t, d = ctx.get("now_s"), pos.get("dir") or (1 if pos.get("rr") == "CE" else -1)
    px = _fin((o or {}).get("ltp")) or _fin(pos.get("last"))
    entry = _fin(pos.get("entry"))
    try:                                                # 123, 124
        hold = t - pos["t_in"]
        out["hold_s"] = _r(hold, 1)
        gain = px - entry if px is not None and entry else None
        peak, pt = _fin(pos.get("peak_pts")) or 0.0, pos.get("peak_t")
        out["gain_pts"], out["peak_pts"] = _r(gain, 2), _r(peak, 2)
        out["gain_pct"] = _r(100.0 * gain / entry, 3) if gain is not None else None
        out["worst_pts"] = _r(_fin(pos.get("worst_pts")), 2)
        if pt is not None and peak > 0:                 # None = the trade has never been in profit
            out["time_to_peak_s"], out["peak_age_s"] = _r(pt - pos["t_in"], 1), _r(t - pt, 1)
            if gain is not None:
                gb = peak - gain
                out["gain_vs_peak"] = _r(gain / peak, 3)
                out["giveback_pts"], out["giveback_share"] = _r(gb, 2), _r(gb / peak, 3)
                out["giveback_rate_pts_min"] = _r(gb / ((t - pt) / 60.0), 3) if t - pt >= 1.0 else 0.0
        fut, f0, best = _fin(ctx.get("fut")), _fin(pos.get("fut_in_ltp")), _fin(pos.get("best"))
        fi = _fin(pos.get("fut_in"))
        if fut is not None and f0 is not None:
            out["fut_fav_pts"] = _r((fut - f0) * d, 2)  # + = the future has gone the trade's way
        if best is not None and fi is not None:
            out["fut_best_fav_pts"] = _r((best - fi) * d, 2)
            if out["fut_fav_pts"] is not None:
                out["fut_giveback_pts"] = _r(out["fut_best_fav_pts"] - out["fut_fav_pts"], 2)
    except Exception:                               # noqa: BLE001
        errs.append("gain")
    try:                                                # 125: where the premium change came from (first order)
        fut, f0 = _fin(ctx.get("fut")), _fin(pos.get("fut_in_ltp"))
        d0, d1 = _fin(pos.get("delta_in")), _fin((o or {}).get("delta"))
        if fut is not None and f0 is not None and d0 is not None:
            dl = 0.5 * (d0 + d1) if d1 is not None else d0          # the option's own signed delta, start and now
            out["attr_delta_pts"] = _r(dl * (fut - f0), 2)
        th = _fin((o or {}).get("theta_min"))
        if th is not None and t is not None:
            out["attr_theta_pts"] = _r(th * (t - pos["t_in"]) / 60.0, 2)    # today's decay rate over the holding time
        iv0, iv1 = _fin(pos.get("iv_in")), _fin((o or {}).get("iv"))
        out["attr_iv_chg"] = _r(iv1 - iv0, 3) if iv0 is not None and iv1 is not None else None
        if out["gain_pts"] is not None and out["attr_delta_pts"] is not None and out["attr_theta_pts"] is not None:
            # what delta and time do not explain: implied volatility, curvature and the quote itself
            out["attr_resid_pts"] = _r(out["gain_pts"] - out["attr_delta_pts"] - out["attr_theta_pts"], 2)
    except Exception:                               # noqa: BLE001
        errs.append("attr")
    try:                                                # 126: does the rest of the system still agree with the trade?
        rr = pos.get("rr")
        orr = "PE" if rr == "CE" else "CE"
        ed = (ctx.get("episode") or {}).get("dir")
        out["thesis_ep_against"] = bool(ed == -d) if ed in (1, -1) else None
        prev = (ctx.get("fires") or {}).get("prev")
        if prev is not None:
            out["thesis_fires_with_n"], out["thesis_fires_against_n"] = int(prev.get(rr, 0)), int(prev.get(orr, 0))
        books = ctx.get("_books")
        if books:
            w_n = a_n = 0
            for b in books.values():
                bp = getattr(b, "pos", None)
                if bp and bp is not pos:
                    w_n += bp.get("rr") == rr
                    a_n += bp.get("rr") == orr
            out["thesis_held_with_n"], out["thesis_held_against_n"] = int(w_n), int(a_n)
        g = ctx.get("gen2")
        imp = g.impact() if g is not None and g.ready("n02_relax") else None
        out["thesis_impact_with"] = bool(imp * d > 0) if imp else None
    except Exception:                               # noqa: BLE001
        errs.append("thesis")
    if errs:
        out["hold_error"] = ",".join(errs)
    return out


def hold_tick(pos, ctx, o):
    """Once per step for a held position, after its peak was updated: remember WHEN the peak was made, and take the
    snapshot when the position reaches the next age mark. One comparison on an ordinary step."""
    t = ctx.get("now_s")
    px = _fin((o or {}).get("ltp"))
    if t is None or px is None or not pos.get("entry"):
        return
    g = px - pos["entry"]
    if g > 0 and g >= (pos.get("peak_pts") or 0.0) - 1e-9 and g > pos.get("peak_seen", 0.0):
        pos["peak_seen"], pos["peak_t"] = g, t
    i = pos.get("hold_i", 0)
    if i < len(HOLD_MARKS) and t - pos["t_in"] >= HOLD_MARKS[i]:
        while i < len(HOLD_MARKS) and t - pos["t_in"] >= HOLD_MARKS[i]:
            i += 1
        pos["hold_i"] = i
        pos.setdefault("weather_hold", []).append(hold_photo(pos, ctx, o, int(HOLD_MARKS[i - 1])))


def hold_mark(pos, ctx, o, mark):
    """The snapshot at the exit request ("exit_req") or, for an exit that had no request, at the close ("exit")."""
    wh = pos.setdefault("weather_hold", [])
    if mark == "exit" and any(x.get("mark") == "exit_req" for x in wh):
        return
    if not any(x.get("mark") == mark for x in wh):
        wh.append(hold_photo(pos, ctx, o, mark))
