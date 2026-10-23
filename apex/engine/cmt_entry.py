"""
apex/engine/cmt_entry.py — ENTRY QUALITY and PRICE PAID (council 5, team T06).

"Did I do a stupidity, or did I enter costly?"  Costly = the right idea at a rich price (spread, IV,
premium that already ran, straddle expanding).  Stupid = the wrong contract or the wrong moment
(near-the-money strike at expiry, a break with no 5-min push behind it, a stop inside the noise).
The ENTRY CARD grades both (A..E) once at the fill; the templates say which one it is, with numbers.

CONTRACT  (commentary.py CONTENT_MODULES)
  FACTS            the keys this module adds to the facts dict
  extend_memo      snapshot at entry: everything the grade needs, computed ONCE (O(600) at most)
  extend_facts     copy the snapshot into f each second (+ five cheap dynamic keys for the 60-s second look)
  entry_card(f)    {"grade": "A".."E", "lines": [3 strings]}
  TEMPLATES        59 templates / 198 phrasings in 13 groups (A fill .. M composite), ported from T06

EVIDENCE  19 Oct 2026, 32 champion trades (work_T06/trades32_graded.csv; analyze.py / stats.py / iv2.py / grade.py).
  Every "On {ref_day}" clause reads REFS below; REFS is the first commentary_refs table and is LABELLED 19 Oct.
  The score weights were designed on those 32 trades (in-sample): validate on the next two replays before trusting the letter.

HONESTY   no phrasing instructs; a confidence remark cites a number; "will" only for mechanics; nothing says "sure".
  Windows are reported as they really are: the engine ring is 60 s, so the premium window is {prem_win_txt}
  (5-min only when this module held the contract recently); the ATM IV history covers {iv_cover_min} minutes.
"""
import math
from collections import deque
from typing import Dict, List

from .commentary import Template, _n, rs

# ── reference statistics (the first commentary_refs; regenerate after each replay) ──────────────────
REFS = {
    "day": "19 Oct",                      # every number below is from the 19 Oct 2026 replay, 32 champion trades
    "n_trades": 32, "day_pnl": 368657,
    "grades": {                           # in-sample: the score was designed on these trades
        "A": {"n": 16, "wins": 11, "pnl": 277739, "mean_ret": 9.2, "peak": 21.6},
        "B": {"n": 5, "wins": 4, "pnl": 101794, "mean_ret": 5.2, "peak": 16.2},
        "C": {"n": 3, "wins": 2, "pnl": 37912, "mean_ret": 5.1, "peak": 16.0},
        "D": {"n": 4, "wins": 2, "pnl": 6806, "mean_ret": 2.2, "peak": 13.3},
        "E": {"n": 4, "wins": 0, "pnl": -55591, "mean_ret": -4.1, "peak": 6.2},
    },
    "hours": {                            # entries by hour of day
        9: {"n": 7, "wins": 4, "mean_ret": 5.9, "peak": 19.9, "pnl": 40870},
        10: {"n": 5, "wins": 4, "mean_ret": 8.9, "peak": 21.4, "pnl": 70560},
        11: {"n": 4, "wins": 2, "mean_ret": 11.7, "peak": 25.0, "pnl": 105229},
        12: {"n": 6, "wins": 4, "mean_ret": 3.1, "peak": 13.1, "pnl": 50561},
        13: {"n": 6, "wins": 3, "mean_ret": 2.3, "peak": 12.4, "pnl": 47372},
        14: {"n": 4, "wins": 2, "mean_ret": 3.6, "peak": 13.0, "pnl": 54068},
    },
    "median_over_mid_pct": 0.07, "mean_over_mid_pct": 0.32, "day_over_mid_rs": 24963, "roundtrip_rs": 21899,
    "reentry_record": "5-1",
    "am": {"n": 20, "wins": 12, "mean_ret": 7.4, "peak": 19.9}, "pm": {"n": 12, "wins": 7, "mean_ret": 2.6, "peak": 12.7},
}
_CARD_TAIL = {"A": "Your part is done; now the hold.", "B": "A good start; the hold decides the rest.",
              "C": "Fair start; the trail does the rest.", "D": "The price was rich; let the trail earn it back.",
              "E": "The stop is {trail_pts:.0f} — let it be cheap."}
_VERDICT = {"A": "clean", "B": "good", "C": "fair", "D": "costly", "E": "poor entry"}

# ── the keys this module adds ───────────────────────────────────────────────────────────────────────
FACTS = """
over_mid over_mid_pct over_mid_rs mid_in entry_bid entry_ask spread_pct roundtrip_rs
prem_win_s lo5 hi5 pos_in_range p5 rise5 vwap5 vwap_kind vs_vwap vs_vwap_pct
iv_run_pct iv_day_lo iv_day_hi iv_day_med iv_cover_min iv_vs30 iv_rise iv_other skew iv_late_why
money money_fut extr_pct intr_pct band_fallback lot_cost
break_level chase_pts s60 s300 s1800 sigma15 range5 regime_why
hour time_in trail_pts stop_rs stop_prem rs_per_pt
vol_win_s vol_win qty_vs_vol ss_in sso_in qty_vs_ss slices
prev_lots prev_ret prev_reason prev_key same_key since_exit prev_stop_rs
strad_5 strad_state_in strad_px_in strad_vwap_in
room_in wall_in wall_oi_in chain_age_in room_why
trade_age_in lag_s_in vix vix_lo vix_hi
day_over_mid_rs day_trades day_over_mid_pct
entry_score entry_grade entry_verdict entry_reasons entry_fired
ret_now spot_vs_in best_vs_in entry_look cost_status
""".split()

# ── module histories (the engine ring is 60 s; these are fed only while a trade is held, bounded) ────
_HIST: Dict[int, deque] = {}      # contract row -> deque of (t, ltp, ttq) at 1 Hz, 600 s
_IV_DAY: Dict[str, list] = {}     # day -> [(t, atm_iv_pct)] one sample per 30 s, bounded 800 (6.7 h)
_VIX: Dict[str, list] = {}        # day -> [lo, hi] seen by this module
_HIST_S = 600.0


def _hist(row: int) -> deque:
    h = _HIST.get(row)
    if h is None:
        if len(_HIST) > 40:
            _HIST.clear()
        h = _HIST[row] = deque()
    return h


def _feed_hist(row, now, ltp, ttq):
    h = _hist(row)
    if h and now - h[-1][0] < 0.9:
        return
    h.append((now, ltp, ttq))
    while h and now - h[0][0] > _HIST_S:
        h.popleft()


def _ring_series(eng, row, now, secs):
    """(t, ltp, ttq) from the engine ring for the last `secs` seconds, time-ordered."""
    m = eng.m
    out = []
    try:
        import numpy as np
        n = min(int(m.count), int(m.t.shape[0]))
        if n <= 0:
            return out
        ts = m.t[:n]
        ok = (ts > 0) & (ts >= now - secs) & (ts <= now + 0.5)
        idx = np.nonzero(ok)[0]
        if not len(idx):
            return out
        idx = idx[np.argsort(ts[idx])]
        lt = m.ltp[row, idx]
        tq = m.ttq[row, idx] if getattr(m, "ttq", None) is not None else np.full(len(idx), np.nan)
        for j in range(len(idx)):
            v = float(lt[j])
            if math.isfinite(v) and v > 0:
                q = float(tq[j])
                out.append((float(ts[idx[j]]), v, q if math.isfinite(q) else None))
    except Exception:
        pass
    return out


def _series(eng, row, now, secs=300.0):
    """Module history (older) + ring (newer), de-duplicated to ~1 Hz, within `secs` before now."""
    old = [x for x in _hist(row) if now - x[0] <= secs]
    ring = _ring_series(eng, row, now, secs)
    if not ring:
        return old
    cut = ring[0][0]
    out = [x for x in old if x[0] < cut - 0.5]
    last_t = out[-1][0] if out else -1e9
    for x in ring:
        if x[0] - last_t >= 0.9:
            out.append(x); last_t = x[0]
    return out


def _back(hist, now, secs, lo_frac=0.8, hi_frac=1.35):
    """Value whose stamp is closest to now-secs, accepted only inside [lo_frac, hi_frac] × secs ago."""
    best, bd = None, None
    for t, v in hist:
        if v is None:
            continue
        d = abs((now - t) - secs)
        if bd is None or d < bd:
            best, bd = (t, v), d
    if best is None:
        return None
    age = now - best[0]
    return best[1] if lo_frac * secs <= age <= hi_frac * secs else None


def _pct_rank(values, x):
    vals = [v for v in values if v is not None]
    if not vals or x is None:
        return None
    return 100.0 * sum(1 for v in vals if v <= x) / len(vals)


# ── the ENTRY SNAPSHOT ───────────────────────────────────────────────────────────────────────────────
def extend_memo(memo, ctx, eng, pos):
    """Everything the entry grade needs, computed once at the fill. Each section is guarded: a missing
    engine object leaves its facts None, never the whole snapshot."""
    q = {k: None for k in FACTS}
    memo.entry_q = q
    now = float(ctx.get("now_s") or pos.get("t_in") or 0.0)
    d = int(pos.get("dir") or 1)
    entry = _n(pos.get("entry")) or 0.0
    qty = int(pos.get("qty") or 0)
    row = pos.get("id")
    day = ctx["now_dt"].date().isoformat() if ctx.get("now_dt") else "?"
    q["time_in"] = pos.get("time_in") or (ctx["now_dt"].strftime("%H:%M:%S") if ctx.get("now_dt") else None)
    q["hour"] = ctx["now_dt"].hour if ctx.get("now_dt") else None
    q["slices"] = pos.get("slices")
    q["band_fallback"] = bool(pos.get("band_fallback"))
    q["trade_age_in"] = _n(pos.get("trade_age_in"))
    adv = pos.get("advisors") or {}
    q["iv_late_why"] = (adv.get("iv_late") or {}).get("why")
    q["regime_why"] = (adv.get("regime") or {}).get("why") or ((ctx.get("regime") or {}).get("text"))
    q["room_why"] = (adv.get("room") or {}).get("why")
    # the champion book (trail size, previous trades, day tally)
    book = None
    try:
        book = eng.books.get(eng.champion)
    except Exception:
        pass
    trail = 12.0
    try:
        trail = float(book.p.get("spot_trail") or book.p.get("d_star") or 12.0)
    except Exception:
        pass
    q["trail_pts"] = trail
    # A. fill
    try:
        b, a = _n(pos.get("entry_bid")), _n(pos.get("entry_ask"))
        mid = _n(pos.get("mid_in"))
        if mid is None and b and a and a >= b:
            mid = (a + b) / 2.0
        q.update(entry_bid=b, entry_ask=a, mid_in=mid)
        if mid and entry:
            om = entry - mid
            q.update(over_mid=om, over_mid_pct=100.0 * om / entry, over_mid_rs=om * qty)
        if b and a and a >= b and entry:
            q.update(spread_pct=100.0 * (a - b) / entry, roundtrip_rs=(a - b) * qty)
    except Exception:
        pass
    # B. premium path over the window this module really has (ring 60 s + own history)
    try:
        if row is not None:
            ser = _series(eng, row, now, 300.0)
            if len(ser) >= 2 and now - ser[0][0] >= 20:
                px = [x[1] for x in ser]
                lo, hi = min(min(px), entry), max(max(px), entry)     # the fill itself is part of the window
                q.update(prem_win_s=now - ser[0][0], lo5=lo, hi5=hi, p5=ser[0][1],
                         pos_in_range=((entry - lo) / (hi - lo)) if hi > lo else None,
                         rise5=(100.0 * (entry / ser[0][1] - 1.0)) if ser[0][1] else None)
                pv = v = 0.0
                for (t0, p0, q0), (t1, p1, q1) in zip(ser, ser[1:]):
                    if q0 is not None and q1 is not None and q1 > q0:
                        pv += (q1 - q0) * p1; v += (q1 - q0)
                if v > 0:
                    q.update(vwap5=pv / v, vwap_kind="VWAP")
                else:
                    q.update(vwap5=sum(px) / len(px), vwap_kind="mean")
                q.update(vs_vwap=entry - q["vwap5"], vs_vwap_pct=100.0 * (entry / q["vwap5"] - 1.0))
                # volume over the same window (ttq is cumulative traded qty)
                tq = [x[2] for x in ser if x[2] is not None]
                if len(tq) >= 2 and tq[-1] >= tq[0]:
                    q.update(vol_win=tq[-1] - tq[0], vol_win_s=now - ser[0][0],
                             qty_vs_vol=(qty / (tq[-1] - tq[0])) if tq[-1] > tq[0] else None)
    except Exception:
        pass
    # C. IV paid: contract iv_in vs the ATM IV history (engine iv_hist = 15 min at 1 Hz, + this module's day list)
    try:
        iv_in = _n(pos.get("iv_in"))
        dl = _IV_DAY.setdefault(day, [])
        for t, v in list(getattr(eng, "iv_hist", []) or []):
            if v and (not dl or t - dl[-1][0] >= 30):
                dl.append((t, float(v) * 100.0))
        if len(dl) > 800:
            del dl[:len(dl) - 800]
        vals = [v for t, v in dl]
        if vals and iv_in is not None:
            sv = sorted(vals)
            q.update(iv_run_pct=_pct_rank(vals, iv_in), iv_day_lo=sv[0], iv_day_hi=sv[-1], iv_day_med=sv[len(sv) // 2],
                     iv_cover_min=(dl[-1][0] - dl[0][0]) / 60.0)
            old = _back(dl, now, 1800.0)
            q["iv_vs30"] = (iv_in - old) if old is not None else None
        r5 = None
        try:
            r5 = eng.iv_change(300)
        except Exception:
            pass
        q["iv_rise"] = _n(r5) if r5 is not None else _n(ctx.get("iv_rise_since_onset"))
        key = pos.get("key") or ""
        parts = key.split("|")
        if len(parts) == 5:
            parts[-1] = "PE" if parts[-1] == "CE" else "CE"
            oid = eng.key.get("|".join(parts))
            if oid is not None:
                q["iv_other"] = _n((eng.greek.get(oid) or {}).get("iv"))
                if q["iv_other"] is not None and iv_in is not None:
                    q["skew"] = iv_in - q["iv_other"]
    except Exception:
        pass
    # D. strike: moneyness vs SPOT (options settle on spot; the PM basis was 18-30 pts on 19 Oct)
    try:
        K = float(pos.get("strike") or 0.0)
        sp, fu = _n(pos.get("spot_in")), _n(pos.get("fut_in"))
        if sp is not None and K:
            money = (sp - K) * d
            q.update(money=money, extr_pct=100.0 * (entry - max(0.0, money)) / entry if entry else None)
            q["intr_pct"] = (100.0 - q["extr_pct"]) if q["extr_pct"] is not None else None
        if fu is not None and K:
            q["money_fut"] = (fu - K) * d
        from .. import config
        q["lot_cost"] = entry * config.LOT_SIZE
        delta = _n(pos.get("delta_in"))
        if delta is not None:
            q.update(stop_prem=trail * abs(delta), stop_rs=trail * abs(delta) * qty, rs_per_pt=abs(delta) * qty)
    except Exception:
        pass
    # E. chase / impulse: the 12-min level the trigger broke, and spot change behind the break
    try:
        lvl = ctx.get("spot_hi") if d > 0 else ctx.get("spot_lo")
        sp = _n(pos.get("spot_in")) or _n(ctx.get("spot"))
        if lvl is not None and sp is not None:
            q.update(break_level=float(lvl), chase_pts=(sp - float(lvl)) * d)
        sh = list(getattr(eng, "spot_hist", []) or [])
        if sh and sp is not None:
            for name, secs in (("s60", 60.0), ("s300", 300.0)):
                old = _back(sh, now, secs, 0.8, 1.3)
                q[name] = (sp - old) * d if old is not None else None
        t30 = _n(ctx.get("trend30"))
        if t30 is not None:
            q["s1800"] = t30 * d
        else:
            fh = list(getattr(eng, "fut_hist", []) or [])
            fu = _n(ctx.get("fut"))
            old = _back(fh, now, 1800.0, 0.9, 1.2) if fh else None
            q["s1800"] = (fu - old) * d if (old is not None and fu is not None) else None
        q["sigma15"] = _n((ctx.get("domino") or {}).get("sigma15"))
        q["range5"] = _n(ctx.get("range5"))
    except Exception:
        pass
    # H. size vs the visible book
    try:
        m = eng.m
        if row is not None and m.k >= 0:
            ss, sso = _n(m.ss[row, m.k]), _n(m.sso[row, m.k])
            q.update(ss_in=ss, sso_in=sso, qty_vs_ss=(qty / ss) if ss else None)
    except Exception:
        pass
    try:
        if book is not None and book.trades:
            pt = book.trades[-1]
            q.update(prev_lots=pt.get("lots"), prev_ret=_n(pt.get("ret_pct")), prev_reason=pt.get("reason"),
                     prev_key=pt.get("key"), same_key=(pt.get("key") == pos.get("key")),
                     since_exit=(now - pt["t_out"]) if pt.get("t_out") is not None else None)
            pd_ = _n(pt.get("delta_in"))
            if pd_ is not None:
                q["prev_stop_rs"] = trail * abs(pd_) * int(pt.get("qty") or 0)
    except Exception:
        pass
    # I. straddle, J. room, K. quote, VIX
    try:
        sv = eng.straddle.view() or {}
        q.update(strad_5=_n(sv.get("slope5")), strad_state_in=sv.get("state"), strad_px_in=_n(sv.get("px")),
                 strad_vwap_in=_n(sv.get("vwap")))
    except Exception:
        pass
    try:
        sp = _n(pos.get("spot_in")) or _n(ctx.get("spot")) or _n(ctx.get("fut"))
        dest = eng.pressure.destination(sp, d) if sp else None
        if dest:
            q.update(room_in=_n(dest.get("room")), wall_in=_n(dest.get("level")))
            walls = eng.pressure.walls_up if d > 0 else eng.pressure.walls_dn
            for k, oi in walls:
                if float(k) == float(dest["level"]):
                    q["wall_oi_in"] = float(oi)
        q["chain_age_in"] = _n(getattr(eng.pressure, "chain_age", None))
    except Exception:
        pass
    try:
        h = eng.data_health(eng.m.snap) if eng.m.snap is not None else {}
        q["lag_s_in"] = _n((h or {}).get("lag_s"))
    except Exception:
        pass
    try:
        vix = _n(eng.t.c("vix"))
        if vix:
            r = _VIX.setdefault(day, [vix, vix])
            r[0], r[1] = min(r[0], vix), max(r[1], vix)
            q.update(vix=vix, vix_lo=r[0], vix_hi=r[1])
    except Exception:
        pass
    # day tally of the spread paid (closed trades + this one)
    try:
        tot, pcts = 0.0, []
        for t in (book.trades if book is not None else []):
            mi, e, qq = _n(t.get("mid_in")), _n(t.get("entry")), int(t.get("qty") or 0)
            if mi and e:
                tot += (e - mi) * qq; pcts.append(100.0 * (e - mi) / e)
        if q["over_mid_rs"] is not None:
            tot += q["over_mid_rs"]; pcts.append(q["over_mid_pct"])
        q.update(day_over_mid_rs=tot, day_trades=len(pcts), day_over_mid_pct=(sum(pcts) / len(pcts)) if pcts else None)
    except Exception:
        pass
    # the score, the grade, the reasons (grade.py, T06 §2.3)
    try:
        q.update(_score(q))
    except Exception:
        q.update(entry_score=None, entry_grade=None, entry_verdict=None, entry_reasons=[])
    q["entry_fired"] = []
    return q


def _score(q):
    s = 0
    why, plus = [], []
    om, pr, mo, ex = q.get("over_mid"), q.get("pos_in_range"), q.get("money"), q.get("extr_pct")
    s300, s60, sg, hr, st5, iv30 = q.get("s300"), q.get("s60"), q.get("sigma15"), q.get("hour"), q.get("strad_5"), q.get("iv_vs30")
    trail = q.get("trail_pts") or 12.0
    if om is not None:
        if om <= 0.05:
            s += 2; plus.append(f"fill {om:+.2f} vs mid" if om < -0.005 else "fill at the mid")
        elif om <= 0.30:
            s += 1; plus.append(f"fill {om:+.2f} over mid")
        elif om >= 1.0:
            s -= 2; why.append(f"paid {om:.2f} over the mid")
        else:
            why.append(f"fill {om:+.2f} over the mid")
    if pr is not None:
        if pr < 0.80:
            s += 2; plus.append(f"premium {100 * pr:.0f} % up its {_win_txt(q)} range, not at the top")
        elif pr >= 0.97:
            s -= 1; why.append(f"premium at its {_win_txt(q)} high")
    if mo is not None and ex is not None:
        if 60 <= mo <= 130 and ex <= 40:
            s += 2; plus.append(f"{mo:.0f} pts ITM vs spot, {ex:.0f} % extrinsic")
        elif mo < 40 or ex >= 45:
            s -= 3; why.append(f"only {mo:.0f} pts ITM vs spot, {ex:.0f} % extrinsic")
        elif mo > 150:
            s -= 1; why.append(f"{mo:.0f} pts ITM, heavy")
        else:
            plus.append(f"{mo:.0f} pts ITM vs spot, {ex:.0f} % extrinsic")
    if s300 is not None:
        if s300 < 10:
            s -= 2; why.append(f"spot only {s300:+.0f} / 5 min, no push")
        elif s300 <= 50:
            s += 1; plus.append(f"spot {s300:+.0f} / 5 min")
        else:
            plus.append(f"spot {s300:+.0f} / 5 min")
    if s60 is not None and s60 > 20:
        s -= 1; why.append(f"spot ran {s60:.0f} pts in the last minute")
    if sg is not None:
        if sg > 8:
            s -= 2; why.append(f"σ15 {sg:.1f} > 8: the {trail:.0f}-pt stop sits inside the noise")
        elif 5 <= sg < 7:
            s += 1; plus.append(f"σ15 {sg:.1f}")
        else:
            plus.append(f"σ15 {sg:.1f}")
    if hr is not None and hr >= 13:
        s -= 1; why.append("after 13:00")
    if st5 is not None:
        if st5 > 5:
            s -= 1; why.append(f"straddle +{st5:.0f} in 5 min")
        elif st5 < -2:
            s += 1; plus.append(f"straddle {st5:+.0f} in 5 min")
    if iv30 is not None and iv30 > 3:
        s -= 1; why.append(f"IV +{iv30:.0f} pts vs 30 min ago")
    ta = q.get("trade_age_in")
    if ta is not None and ta > 5:
        why.append(f"last trade {ta:.0f} s before the fill (fill uncertainty)")
    g = "A" if s >= 4 else "B" if s >= 2 else "C" if s >= 0 else "D" if s >= -2 else "E"
    reasons = (why + plus) if g in ("D", "E") else (plus + why)
    return {"entry_score": s, "entry_grade": g, "entry_verdict": _VERDICT[g], "entry_reasons": reasons}


def _win_txt(q):
    w = q.get("prem_win_s")
    return "5-min" if (w is not None and w >= 240) else (f"{w:.0f}-s" if w is not None else "recent")


# ── per-second: copy the snapshot, feed the histories, five dynamic keys ────────────────────────────
def extend_facts(f, ctx, eng, book, memo):
    try:
        q = getattr(memo, "entry_q", None)
        if q is None:
            q = extend_memo(memo, ctx, eng, book.pos)
        f.update(q)
        now = ctx.get("now_s")
        p = book.pos
        if p is not None and now is not None:
            ltp = f.get("ltp")
            ttq = None
            try:
                m = eng.m
                ttq = _n(m.ttq[p["id"], m.k])
            except Exception:
                pass
            if ltp:
                _feed_hist(p["id"], now, float(ltp), ttq)
        try:
            vix = _n(eng.t.c("vix"))
            if vix:
                day = ctx["now_dt"].date().isoformat()
                r = _VIX.setdefault(day, [vix, vix])
                r[0], r[1] = min(r[0], vix), max(r[1], vix)
                f.update(vix=vix, vix_lo=r[0], vix_hi=r[1])
        except Exception:
            pass
        # the 60-s second look: what the market says about the fill so far
        rn, sf, bf = f.get("ret_pct"), f.get("spot_fav"), f.get("best_spot_fav")
        f.update(ret_now=rn, spot_vs_in=sf, best_vs_in=bf,
                 entry_look=("vindicated" if (rn or 0) >= 2 else "expensive" if (rn or 0) <= -2 else "unproven"),
                 cost_status=("earned back" if (f.get("pnl_pts") is not None and f.get("over_mid") is not None
                                                 and f["pnl_pts"] >= max(f["over_mid"], 0)) else "still owed"))
    except Exception:
        pass


# ── the ENTRY CARD ───────────────────────────────────────────────────────────────────────────────────
def entry_card(f):
    g = f.get("entry_grade")
    if not g:
        return None
    om = f.get("over_mid")
    verdict = _VERDICT[g]
    if g == "B" and om is not None and om > 0.30:
        verdict = "good, but you paid up"
    line1 = f"Grade {g} — {verdict}"
    reasons = list(f.get("entry_reasons") or [])
    line2 = " · ".join(reasons[:3]) if reasons else "not enough entry facts yet (first trade on this contract)"
    r = REFS["grades"][g]
    trail = f.get("trail_pts") or 12.0
    line3 = (f"On {REFS['day']}, {g}-entries: {r['wins']}/{r['n']} won, mean {r['mean_ret']:+.1f} %, best excursion {r['peak']:.0f} pts. "
             + _CARD_TAIL[g].format(trail_pts=trail))
    return {"grade": g, "verdict": verdict, "score": f.get("entry_score"), "lines": [line1, line2, line3],
            "ref_day": REFS["day"]}


# ── slots: every phrasing's {name} resolves here; None prints as "—", never a crash ────────────────────
class _V:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __format__(self, spec):
        if self.v is None:
            return "—"
        try:
            return format(self.v, spec)
        except (ValueError, TypeError):
            return str(self.v)

    def __str__(self):
        return "—" if self.v is None else str(self.v)


_NUM_KEYS = """over_mid over_mid_pct over_mid_rs mid_in entry_bid entry_ask spread_in spread_pct roundtrip_rs
lo5 hi5 pos_in_range p5 rise5 vwap5 vs_vwap vs_vwap_pct prem_win_s
iv_in iv_run_pct iv_day_lo iv_day_hi iv_day_med iv_cover_min iv_vs30 iv_rise iv_other skew
money money_fut extr_pct intr_pct lot_cost delta_in lots qty entry strike capital capital_deployed
break_level chase_pts s60 s300 s1800 sigma15 range5 hour trail_pts stop_rs stop_prem rs_per_pt
vol_win vol_win_s qty_vs_vol ss_in sso_in qty_vs_ss slices prev_lots prev_ret since_exit prev_stop_rs
strad_5 strad_px_in strad_vwap_in room_in wall_in wall_oi_in chain_age_in trade_age_in lag_s_in vix vix_lo vix_hi
day_over_mid_rs day_trades day_over_mid_pct entry_score ret_now spot_vs_in best_vs_in basis_in spot_in fut_in
min_to_flatten theta_rs_min""".split()


def _slots(f):
    s = {k: _V(f.get(k)) for k in _NUM_KEYS}
    from .. import config
    LOT = config.LOT_SIZE
    g = lambda k: f.get(k)   # noqa: E731
    d = g("dir") or 1
    rr = g("rr") or "—"
    s.update(ref_day=REFS["day"], rr=rr, other_rr=("PE" if rr == "CE" else "CE"),
             ref_median_over_mid_pct=REFS["median_over_mid_pct"], ref_day_over_mid_rs=rs(REFS["day_over_mid_rs"]),
             ref_roundtrip_rs=rs(REFS["roundtrip_rs"]), reentry_record=REFS["reentry_record"],
             prem_win_txt=_win_txt(f), prem_win_long=("5 minutes" if (g("prem_win_s") or 0) >= 240 else f"{g('prem_win_s') or 0:.0f} seconds"),
             vol_win_txt=("5 min" if (g("vol_win_s") or 0) >= 240 else f"{g('vol_win_s') or 0:.0f} s"),
             vwap_kind=g("vwap_kind") or "mean",
             fut_in=_V(g("fut_in") if g("fut_in") is not None else ((g("spot_in") or 0) + (g("basis_in") or 0) if g("spot_in") is not None else None)),
             delta_abs=_V(abs(g("delta_in")) if g("delta_in") is not None else None),
             delta_in=_V(abs(g("delta_in")) if g("delta_in") is not None else None),   # a put's delta prints unsigned
             x_median=_V((g("over_mid_pct") / REFS["median_over_mid_pct"]) if g("over_mid_pct") else None),
             hi5_minus=_V((g("hi5") - g("entry")) if (g("hi5") is not None and g("entry")) else None),
             pos_in_range_pct=_V(100.0 * g("pos_in_range") if g("pos_in_range") is not None else None),
             range5_prem=_V((g("hi5") - g("lo5")) if (g("hi5") is not None and g("lo5") is not None) else None),
             vs_vwap_word=("less" if (g("vs_vwap") or 0) > 0 else "more"),
             vs_vwap_word_cap=("Dearer" if (g("vs_vwap") or 0) > 0 else "Cheaper"),
             iv_late_why=g("iv_late_why") or "—", regime_why=g("regime_why") or "—", room_why=g("room_why") or "—",
             regime=g("regime") or "—", regime_arrow=("up" if (g("regime_dir") or 0) > 0 else "down" if (g("regime_dir") or 0) < 0 else "flat"),
             dir_word=("long calls" if d > 0 else "long puts"),
             theta_rs_abs=_V(abs(g("theta_rs_min")) if g("theta_rs_min") is not None else None),
             lots_atm_est=_V(int((g("capital_deployed") or 0) // ((75.0 + max((g("entry") or 0) - max(g("money") or 0, 0), 0)) * LOT)) if g("entry") else None),
             ret_per_12=_V((100.0 * (g("trail_pts") or 12) * abs(g("delta_in")) / g("entry")) if (g("delta_in") is not None and g("entry")) else None),
             ret_per_12_sweet=_V((100.0 * (g("trail_pts") or 12) * 0.74 / (75.0 + max((g("entry") or 0) - max(g("money") or 0, 0), 0))) if g("entry") else None),
             delta_pts_per_12=_V(((g("trail_pts") or 12) * abs(g("delta_in"))) if g("delta_in") is not None else None),
             rs_per_12=_V(g("stop_rs")), stop_pct=_V((100.0 * g("stop_rs") / g("capital_deployed")) if (g("stop_rs") is not None and g("capital_deployed")) else None),
             ask_minus=_V((g("entry_ask") - g("entry")) if (g("entry_ask") is not None and g("entry")) else None),
             t_minus30=_hms_minus(g("time_in"), 30),
             qty_vs_vol5_pct=_V(100.0 * g("qty_vs_vol") if g("qty_vs_vol") is not None else None),
             vol5_lots=_V((g("vol_win") / LOT) if g("vol_win") is not None else None),
             qty_vs_ss_pct=_V(100.0 * g("qty_vs_ss") if g("qty_vs_ss") is not None else None),
             ss_lots=_V((g("ss_in") / LOT) if g("ss_in") is not None else None), sso=_V(int(g("sso_in")) if g("sso_in") is not None else None),
             abs_s1800=_V(abs(g("s1800")) if g("s1800") is not None else None),
             deployed_pct=_V((100.0 * g("capital_deployed") / g("capital")) if (g("capital_deployed") and g("capital")) else None),
             prev_reason=g("prev_reason") or "—",
             strad_5ago=_V((g("strad_px_in") - g("strad_5")) if (g("strad_px_in") is not None and g("strad_5") is not None) else None),
             implied_move=_V(g("strad_px_in")),
             wall_oi_lots=_V((g("wall_oi_in") / LOT) if g("wall_oi_in") is not None else None),
             room_prem=_V((g("room_in") * abs(g("delta_in"))) if (g("room_in") is not None and g("delta_in") is not None) else None),
             mins_to_flat=_V(g("min_to_flatten")),
             entry_look=g("entry_look") or "unproven", cost_status=g("cost_status") or "—",
             extr_clause=(f" · extrinsic {g('extr_pct'):.0f} % of the premium (≈ {rs((g('entry') or 0) * (g('extr_pct') or 0) / 100.0 * (g('qty') or 0))} of time value)"
                          if (g("extr_pct") is not None and g("extr_pct") >= 45) else ""))
    hr = REFS["hours"].get(g("hour"))
    s.update(hour_n=_V(hr["n"] if hr else None), hour_wins=_V(hr["wins"] if hr else None),
             hour_mean_ret=_V(hr["mean_ret"] if hr else None), hour_peak=_V(hr["peak"] if hr else None), hour_pnl=_V(hr["pnl"] if hr else None))
    rsn = list(g("entry_reasons") or [])
    while len(rsn) < 3:
        rsn.append("no further entry facts")
    s.update(reason_1=rsn[0], reason_2=rsn[1], reason_3=rsn[2], reason_list="; ".join(rsn[:4]))
    for k in _RS_KEYS:                       # ready-to-print rupee strings
        v = s.get(k)
        s[k + "_txt"] = rs(v.v if isinstance(v, _V) else f.get(k))
    return s


_RS_KEYS = ("over_mid_rs", "roundtrip_rs", "day_over_mid_rs", "stop_rs", "rs_per_pt", "rs_per_12", "prev_stop_rs", "lot_cost",
            "capital_deployed", "capital", "hour_pnl")


def _hms_minus(hms, minutes):
    try:
        h, m, _ = [int(x) for x in hms.split(":")]
        t = h * 60 + m - minutes
        return f"{t // 60:02d}:{t % 60:02d}"
    except Exception:
        return "—"


# ── TEMPLATES ────────────────────────────────────────────────────────────────────────────────────────
# T06 priority 1..5 -> core prio; T06 tones -> core TONES (REASSURE -> confidence when every phrasing cites a
# number, praise otherwise). Every template is once-per-trade (the entry facts do not change); min_hold_s spreads
# the groups over the first minute (card + composite first, then fill, strike, chase, premium, ...).
_P = {1: 85, 2: 70, 3: 55, 4: 40, 5: 25}


def _ok(*vals):
    return all(v is not None for v in vals)


def T(key, kind, tone, p, when, phrasings, hold, note=""):
    return Template(key=key, kind=kind, tone=tone, prio=_P[p], when=when, phrasings=phrasings, cooldown_s=1e9,
                    min_hold_s=hold, once=True, slots=_slots, note=note)


TEMPLATES: List[Template] = [
    # ── A fill ──────────────────────────────────────────────────────────────
    T("fill.clean", "entry", "praise", 2, lambda f: _ok(f.get("over_mid")) and f["over_mid"] <= 0.05, [
        "Clean fill: {over_mid:+.2f} over the mid, spread was {spread_in:.2f}. Nothing given away at the door.",
        "You bought at {entry:.2f} against a {entry_bid:.2f}/{entry_ask:.2f} book — at the mid. That is as good as a fill gets.",
        "Filled {over_mid:+.2f} vs mid. On {ref_day} the 13 fills at or under the mid went 10-3 for ₹2.80 L; the entry cost you nothing.",
        "No spread tax here: entry {entry:.2f}, mid {mid_in:.2f}. Start the trade at zero, not minus."],
        1, "over_mid ≤ 0.05: 13/32 on 19 Oct, 10 wins, +₹2,80,000, mean +10.3 %"),
    T("fill.fair", "entry", "information", 4, lambda f: _ok(f.get("over_mid")) and 0.05 < f["over_mid"] <= 0.30 and (f.get("over_mid_pct") or 0) <= 0.4, [
        "Fill {over_mid:+.2f} over the mid ({over_mid_pct:.2f} % of premium) — normal for a market order on this contract.",
        "You paid {over_mid:.2f} pts of spread: {over_mid_rs_txt} on {qty} qty. Small, but it is the first thing the trade has to earn back.",
        "Ordinary fill: {over_mid:.2f} over mid, within the {spread_in:.2f} spread. Fine.",
        "Spread paid {over_mid:.2f} — about what the book charges anyone who crosses it."],
        1, "0.05-0.30: 11 trades, 5 wins, −₹29k on 19 Oct; not a loss driver by itself"),
    T("fill.costly", "entry", "lesson", 2, lambda f: _ok(f.get("over_mid")) and f["over_mid"] <= 1.0 and (f["over_mid"] > 0.30 or (f.get("over_mid_pct") or 0) > 0.4), [
        "You paid {over_mid:.2f} over the mid — {over_mid_pct:.2f} % of the premium, {over_mid_rs_txt} on this size. The market moved while you were deciding.",
        "Costly fill: {over_mid:.2f} pts above mid. A limit at the mid would have saved {over_mid_rs_txt} or missed the trade — on {ref_day} it would have missed 2 of 32.",
        "{over_mid:.2f} over the mid ({over_mid_pct:.2f} % of premium). Not a disaster, but it is {x_median:.0f}× the {ref_day} median of {ref_median_over_mid_pct:.2f} %.",
        "The ask ran away from you: entry {entry:.2f}, mid {mid_in:.2f}. That is {over_mid_rs_txt} you need the trade to earn first."],
        1, "19 Oct median over-mid 0.07 % of premium; 0.30-1.0 pts: 5 trades, 2 wins"),
    T("fill.chased_ask", "entry", "lesson", 1, lambda f: _ok(f.get("over_mid")) and f["over_mid"] > 1.0, [
        "You were filled {over_mid:.1f} pts above the mid ({over_mid_pct:.1f} % of premium). That is not spread — the premium jumped as you hit it. On {ref_day} this happened twice: 09:36 (−5.0 %) and 10:19 (+8.7 %).",
        "Ouch: {over_mid:.1f} over mid. The quote was {entry_bid:.2f}/{entry_ask:.2f} and you printed {entry:.2f}. Someone got there a second before you.",
        "Entry {entry:.2f} vs a mid of {mid_in:.2f}. You chased the premium, not the spot. {over_mid_rs_txt} given to the seller.",
        "This fill cost {over_mid:.1f} pts more than a patient one. It is the single most expensive thing you did on this trade so far."],
        1, "over_mid > 1.0: 3 trades on 19 Oct (2.97, 2.88, 1.67 pts), ₹7,700 combined"),
    T("fill.spread_wide", "entry", "caution", 3, lambda f: (_ok(f.get("spread_in")) and f["spread_in"] >= 0.35) or (_ok(f.get("spread_pct")) and f["spread_pct"] >= 0.3), [
        "Wide book at entry: {spread_in:.2f} between bid and ask ({spread_pct:.2f} %). Expect the exit to cost the same again.",
        "Spread {spread_in:.2f} — the widest third of the {ref_day} day. Round-trip cost on this size ≈ {roundtrip_rs_txt}.",
        "The bid/ask was {entry_bid:.2f}/{entry_ask:.2f}. Wide for an ATM weekly; the market-maker is nervous, which also means fast moves."],
        2, "19 Oct spreads 0.15-0.35 pts; ≥ 0.35 in 4 trades (all 09:27-09:58); round-trip on 32 trades ₹21,900"),
    T("fill.day_tally", "day", "information", 4, lambda f: _ok(f.get("day_over_mid_rs"), f.get("day_trades")) and f["day_trades"] >= 1, [
        "Spread paid so far today: {day_over_mid_rs_txt} across {day_trades} entries ({day_over_mid_pct:.2f} % of premium on average). On {ref_day} the full day came to {ref_day_over_mid_rs}.",
        "Entry costs today: {day_over_mid_rs_txt}. Small per trade, real by 15:00.",
        "Running tab for crossing the spread: {day_over_mid_rs_txt} in {day_trades} trades."],
        60, "19 Oct: Σ(entry − mid)·qty = ₹24,963; mean 0.32 %, median 0.07 % of premium"),
    # ── B premium path ───────────────────────────────────────────────────────
    T("prem.top_of_range", "premium", "caution", 2, lambda f: _ok(f.get("pos_in_range")) and f["pos_in_range"] >= 0.97, [
        "You bought the premium at its {prem_win_txt} high ({entry:.2f}; range {lo5:.2f}–{hi5:.2f}). On {ref_day} the 11 entries at the 5-min high went 5-6 for −₹20,787; the 4 bought below 80 % of the range went 4-0 for +₹1.92 L.",
        "Premium at the very top of its last {prem_win_long}. A breakout buyer always does this — just know the first pullback is now against you by up to {range5_prem:.1f} pts.",
        "Paid the high of the last {prem_win_long}. The spot break is real; the premium is simply fully priced for it.",
        "Top-tick of the {prem_win_txt} range ({lo5:.2f}–{hi5:.2f}). The trade has to make a NEW premium high to pay."],
        4, "pos_in_range ≥ 0.97: 11 trades, 5 wins, −₹20.8k; < 0.80: 4 trades, 4 wins, +₹1.92 L (mean +23 %)"),
    T("prem.retest_entry", "premium", "confidence", 2, lambda f: _ok(f.get("pos_in_range")) and f["pos_in_range"] < 0.80, [
        "Good price: {entry:.2f} is only {pos_in_range_pct:.0f} % up the last-{prem_win_long} range ({lo5:.2f}–{hi5:.2f}). You bought the retest, not the spike.",
        "You did not pay the top: premium is {hi5_minus:.1f} pts under its {prem_win_txt} high. All four such entries on {ref_day} were winners (+30.6 %, +11.0 %, +23.7 %, +26.8 %).",
        "Entry {pos_in_range_pct:.0f} % up the premium's {prem_win_txt} range. The breakout came without a premium spike — cheap by {ref_day}'s standards.",
        "Below the {prem_win_txt} high by {hi5_minus:.1f}. That is the kind of fill that makes holding easy."],
        4, "see prem.top_of_range"),
    T("prem.ran_already", "premium", "lesson", 1, lambda f: _ok(f.get("rise5")) and f["rise5"] >= 50, [
        "This premium was {p5:.2f} {prem_win_long} ago and you paid {entry:.2f} (+{rise5:.0f} %). The option already made the move you are hoping for.",
        "+{rise5:.0f} % in {prem_win_long} before you entered. You are buying the second half of a spike: on {ref_day} 09:27 and 09:28 did this (+7.9 %, −0.8 %).",
        "The premium ran {rise5:.0f} % into your entry. Expect theta and IV-fade to fight you if the spot pauses.",
        "Late to the premium: +{rise5:.0f} % in {prem_win_long}. The spot level may be fresh; the price you paid is not."],
        4, "rise5 ≥ 50 %: 4 trades (all before 09:40), 3 wins but mean +4.9 % vs +7.3 % for 10-20 %"),
    T("prem.ran_some", "premium", "caution", 3, lambda f: _ok(f.get("rise5")) and 20 <= f["rise5"] < 50, [
        "Premium +{rise5:.0f} % in the last {prem_win_long}. Some of the move is already in the price.",
        "You paid {entry:.2f}; {prem_win_long} ago it was {p5:.2f}. Fair warning: the easy part is in.",
        "+{rise5:.0f} % premium run-up before entry. Normal on a breakout — just not cheap."],
        4, "20-50 %: 3 trades, 2 wins, +₹64k"),
    T("prem.fresh", "premium", "praise", 3, lambda f: _ok(f.get("rise5"), f.get("pos_in_range")) and f["rise5"] < 10 and f["pos_in_range"] < 0.95, [
        "The premium has barely moved before your entry (+{rise5:.0f} % in {prem_win_long}). You are early, not late.",
        "Quiet premium into the break: +{rise5:.0f} % over {prem_win_long}. If the spot follows through, the option still has to re-price — that is your edge.",
        "Fresh entry: the option did not run ahead of the spot (+{rise5:.0f} % in {prem_win_long})."],
        4, "rise5 < 10 %: 7 trades, 4 wins; position in range is the better discriminator"),
    T("prem.vs_vwap", "premium", "information", 4, lambda f: _ok(f.get("vwap5"), f.get("vs_vwap")), [
        "Entry {entry:.2f} vs the contract's {prem_win_txt} {vwap_kind} {vwap5:.2f} ({vs_vwap:+.1f}). Everyone who traded it in the last {prem_win_long} paid {vs_vwap_word} than you.",
        "{vs_vwap_pct:+.1f} % vs the {prem_win_txt} {vwap_kind}. {vs_vwap_word_cap} than the crowd.",
        "You paid {vs_vwap:+.1f} pts vs the recent {vwap_kind} of this strike."],
        6, "informational; on 19 Oct all 32 were above the 5-min VWAP (breakout buying), 3 % to 236 %"),
    # ── C IV paid ────────────────────────────────────────────────────────────
    T("iv.low_third", "greeks", "confidence", 2, lambda f: _ok(f.get("iv_run_pct"), f.get("iv_in")) and f["iv_run_pct"] <= 33 and (f.get("iv_cover_min") or 0) >= 10, [
        "IV paid {iv_in:.1f} % — in the lower third of the ATM range seen so far ({iv_day_lo:.1f}–{iv_day_hi:.1f}, {iv_cover_min:.0f} min of history). On {ref_day} all five such entries won, mean +21.9 %.",
        "Cheap vol: {iv_in:.1f} % is the {iv_run_pct:.0f}th percentile of the ATM IV so far. If the move comes, IV expansion works for you, not against you.",
        "You bought this option at {iv_in:.1f} % IV, under the running ATM median {iv_day_med:.1f}. Good — the premium is not inflated.",
        "IV {iv_in:.1f} %, bottom third of the day so far. One of the three cleanest things an option buyer can do."],
        6, "iv_run_pct ≤ 33: 5 trades, 5 wins, +₹1.96 L, mean +21.9 %, mean peak 37 pts"),
    T("iv.high_vs_day", "greeks", "lesson", 2, lambda f: _ok(f.get("iv_run_pct"), f.get("iv_vs30")) and f["iv_run_pct"] >= 90 and f["iv_vs30"] > 3, [
        "You paid {iv_in:.1f} % IV — the {iv_run_pct:.0f}th percentile of the day so far, and {iv_vs30:+.1f} pts above 30 minutes ago. Vol is expensive here; a stall costs you twice (theta + IV fade).",
        "IV {iv_in:.1f} %, up {iv_vs30:.1f} pts in half an hour. You bought fear. It must turn into movement quickly.",
        "Expensive vol: {iv_in:.1f} % vs a running ATM median of {iv_day_med:.1f}. On {ref_day}, +3 pts-vs-30-min entries averaged +2.9 % against +6.6 % for falling-IV entries.",
        "Top-decile IV for the day so far ({iv_run_pct:.0f}th percentile). Not stupid — but costly, and the premium leaks if the spot goes sideways."],
        6, "iv_vs30 > +3: 10 trades, 5 wins, +2.9 %; < −1: 14 trades, 10 wins, +6.6 %"),
    T("iv.rising_fast", "greeks", "caution", 2, lambda f: _ok(f.get("iv_rise")) and f["iv_rise"] >= 3, [
        "ATM IV jumped {iv_rise:+.1f} pts in the last 5 minutes. The straddle re-priced before you got in; this is the 'late' tax.",
        "IV +{iv_rise:.1f} in 5 min. Both {ref_day} entries with this flag (09:27, 09:28) saw the premium give back IV within a minute — one won small, one lost.",
        "Fast-rising IV into your entry (+{iv_rise:.1f} pts / 5 min). If spot keeps going you are fine; if it pauses, the premium falls even with spot unchanged.",
        "The iv_late advisor read: {iv_late_why} (ATM IV {iv_rise:+.1f} in 5 min). It is an advisor, not a gate — but it is right more often than not."],
        6, "19 Oct: the two trades with +4.4 / +6.3 IV in 5 min: +7.9 % and −0.8 %; both exited within 30 s"),
    T("iv.falling", "greeks", "confidence", 3, lambda f: _ok(f.get("iv_vs30"), f.get("iv_in")) and f["iv_vs30"] <= -1, [
        "IV {iv_in:.1f} %, {iv_vs30:.1f} pts below 30 minutes ago. You bought the option while vol was deflating — the cheapest way to own gamma.",
        "Vol is cooling ({iv_vs30:+.1f} pts / 30 min). Your premium has less air in it.",
        "Falling-IV entry ({iv_vs30:+.1f} pts vs 30 min). 14 of these on {ref_day}: 10 winners, +₹2.06 L."],
        6, "see iv.high_vs_day"),
    T("iv.skew_tax", "greeks", "information", 3, lambda f: _ok(f.get("skew")) and f["skew"] >= 8, [
        "This {rr} is priced at {iv_in:.1f} % IV while the {other_rr} at the same strike trades at {iv_other:.1f} %. You are paying {skew:+.1f} pts of skew — the insurance premium everyone wants on expiry afternoon.",
        "Skew tax: {skew:+.1f} IV pts over the other leg. Not a reason to avoid the trade (14 of these went 10-4 on {ref_day}), but it is why the premium looks fat.",
        "The {rr} carries {skew:+.1f} pts more IV than its twin. If the move fails, this skew unwinds against you faster than theta does."],
        6, "skew ≥ +3: 14 trades, 10 wins, +7.5 % — a cost, not a verdict"),
    T("iv.after_1330", "time", "caution", 3, lambda f: f.get("zero_dte") and _ok(f.get("hour")) and (f["hour"] > 13 or (f["hour"] == 13 and f.get("time_in", "00:00") >= "13:30")), [
        "Expiry afternoon: IV {iv_in:.1f} % and climbing. This is pure gamma now — the option pays only if spot moves, and the premium melts every minute it does not.",
        "0DTE after 13:30. On {ref_day} the ATM IV went from 31 % to 45 % into the close; extrinsic value evaporates at {theta_rs_abs:,.0f} ₹/min on your size.",
        "Late-expiry entry ({time_in}). Nothing wrong with it — but understand the clock is the opponent now, not the spread."],
        16, "19 Oct 13:00-14:45: 10 trades, 5 wins, mean +2.8 %, mean peak 12.6 pts (AM: 19.9)"),
    # ── D strike ─────────────────────────────────────────────────────────────
    T("strike.sweet", "entry", "confidence", 2, lambda f: _ok(f.get("money"), f.get("extr_pct")) and 60 <= f["money"] <= 130 and f["extr_pct"] <= 40, [
        "{strike} {rr}: {money:.0f} pts in the money vs spot, delta {delta_in:.2f}, {extr_pct:.0f} % extrinsic. This is the sweet spot — on {ref_day} 60–130 ITM went 18-9 for +₹4.19 L.",
        "Right strike: {money:.0f} ITM. Enough delta to track the spot (≈ {delta_pts_per_12:.0f} pts of premium per {trail_pts:.0f} of spot), not so deep that you are paying for intrinsic you cannot lever.",
        "Delta {delta_in:.2f}. Each {trail_pts:.0f}-pt spot move is worth ≈ {rs_per_12_txt} to you. Clean.",
        "Strike choice is textbook: {money:.0f} ITM vs spot, extrinsic only {extr_pct:.0f} %."],
        2, "money vs spot 60-90: 20/13 +₹2.77 L; 90-130: 7/5 +₹1.41 L, mean +13.2 %; extrinsic ≤ 30 %: 13/9 +11.0 %"),
    T("strike.lottery", "entry", "lesson", 1, lambda f: _ok(f.get("money"), f.get("extr_pct")) and (f["money"] < 40 or f["extr_pct"] >= 45), [
        "{strike} {rr} is only {money:.0f} pts in the money vs spot — {extr_pct:.0f} % of what you paid is time value. On {ref_day} the five such entries went 1-4 for −₹49,933 while the engine's delta read {delta_in:.2f}; delta flattered them.",
        "This is a lottery ticket, not a delta trade: {extr_pct:.0f} % extrinsic, {money:.0f} ITM. It needs the spot to move AND move fast.",
        "Near-ATM at expiry: delta {delta_in:.2f} now, but it will be 0.5 or 0.95 within the hour. The {trail_pts:.0f}-pt stop does not protect a premium that is mostly air.",
        "Strike choice is the weak point of this entry: {money:.0f} ITM vs spot. The band picked the lowest delta ≥ 0.65; on a skewed expiry afternoon that is a near-the-money {rr}.",
        "Caution on the contract, not the direction: {extr_pct:.0f} % of {entry:.2f} is extrinsic. Theta here is ≈ {theta_rs_abs:,.0f} ₹/min on your size."],
        2, "money vs spot < 40: 5 trades (13:12, 13:29, 13:44, 14:15, 14:24), 1 win, −₹49.9k, mean peak 6.9 pts"),
    T("strike.heavy", "entry", "caution", 3, lambda f: _ok(f.get("money"), f.get("extr_pct")) and (f["money"] > 150 or f["extr_pct"] < 5), [
        "{strike} {rr} is {money:.0f} pts deep. You are buying mostly intrinsic ({intr_pct:.0f} %), so lots are {lots} instead of ≈ {lots_atm_est} at 75 ITM — less leverage for the same spot move.",
        "Deep ITM: delta {delta_in:.2f} is great, but each lot costs {lot_cost_txt}. The trade can still work; it will work slower in % terms.",
        "Heavy strike ({money:.0f} ITM). Fewer lots, fatter spread in ₹ — a {trail_pts:.0f}-pt spot move is ≈ {ret_per_12:.1f} % here vs ≈ {ret_per_12_sweet:.1f} % at 75 ITM."],
        2, "no 19 Oct trade was > 130 pts ITM vs spot; 90-130 was the best bin — a cost statement, not an outcome one"),
    T("strike.band_fallback", "entry", "caution", 2, lambda f: bool(f.get("band_fallback")), [
        "No strike sat inside the delta band; the engine took the nearest one above it (delta {delta_in:.2f}). Expect a deeper, pricier contract than usual.",
        "Band fallback: the usual 0.65–0.85 window had nothing live, so you own a {delta_in:.2f}-delta option. Fine for direction, heavier in ₹.",
        "Fallback contract (delta {delta_in:.2f}). Did not happen once in 32 trades on {ref_day} — worth a look at the chain if it repeats."],
        2, "never fired on 19 Oct"),
    T("strike.delta_vs_money", "entry", "information", 3,
      lambda f: (_ok(f.get("delta_in"), f.get("money")) and abs(f["delta_in"]) >= 0.65 and f["money"] < 40) or (_ok(f.get("basis_in")) and f["basis_in"] >= 15), [
        "Delta {delta_in:.2f} on a strike only {money:.0f} ITM vs spot — the delta flatters it. Treat this as a near-0.55 option for sizing your expectations.",
        "Basis check: future {fut_in:.0f}, spot {spot_in:.0f} ({basis_in:+.0f}). The option settles on spot; it is {money:.0f} ITM, not {money_fut:.0f}.",
        "Quoted delta {delta_in:.2f}, real moneyness {money:.0f} vs spot. This is how the band chose a near-the-money strike on an expiry afternoon; worth the owner's review."],
        3, "all 5 lottery entries on 19 Oct carried delta 0.66-0.73 while 29-39 pts ITM vs spot (basis 24-30 pts)"),
    T("strike.rs_per_point", "entry", "information", 3, lambda f: _ok(f.get("stop_rs"), f.get("stop_prem")), [
        "Your stop ({trail_pts:.0f} pts of spot) is ≈ {stop_prem:.1f} pts of premium ≈ {stop_rs_txt} ({stop_pct:.1f} % of capital). A +{trail_pts:.0f} move is worth about the same the other way.",
        "Translation: 1 pt of Nifty ≈ {delta_abs:.2f} pts of premium ≈ {rs_per_pt_txt} on {qty} qty.",
        "Risk on this entry: {trail_pts:.0f} spot pts × delta {delta_abs:.2f} × {qty} = {stop_rs_txt}. Know the number before the screen shows it."],
        5, "informational"),
    # ── E chase ──────────────────────────────────────────────────────────────
    T("chase.late_entry", "entry", "information", 3, lambda f: _ok(f.get("chase_pts")) and f["chase_pts"] >= 3, [
        "Spot was {chase_pts:.1f} pts past the breakout level ({break_level:.1f}) when you were filled. On {ref_day} that was not a sin — the 4 entries ≥ 3 pts past the level went 3-1, mean +10.8 %. Momentum, not chasing.",
        "You entered {chase_pts:.1f} pts beyond the break. Your stop is still {trail_pts:.0f} from the best, so the late entry costs you premium, not safety.",
        "Filled {chase_pts:.1f} pts past the level. A little late is fine; the data says the breaks that ran 3+ pts immediately were the real ones."],
        3, "chase ≥ 3: 4 trades, 3 wins, +₹71.5k, mean +10.8 %; 0-0.5: 16 trades, 9 wins, +3.9 %"),
    T("chase.spot_sprint", "entry", "caution", 2, lambda f: _ok(f.get("s60")) and f["s60"] >= 20, [
        "Spot sprinted {s60:.0f} pts in the last minute. You are buying into an air-pocket: on {ref_day} the four ≥ 20-pt-in-60-s entries averaged +3.3 % vs +7.7 % for 5–10 pt breaks.",
        "{s60:.0f} pts in 60 seconds before your fill. Fast breaks snap back fast — the {trail_pts:.0f}-pt trail will be tested in the first minute.",
        "Entered after a {s60:.0f}-pt spot sprint. Not wrong, but the premium you paid already contains it.",
        "A one-minute {s60:.0f}-pt move preceded this entry. Expect the first pullback to be sharp; the plan, not the tick, is the thing to watch."],
        3, "s60 ≥ 20: 4 trades, 2 wins, +3.3 %; 5-10: 11 trades, 8 wins, +7.7 %"),
    T("chase.no_push", "entry", "caution", 1, lambda f: _ok(f.get("s300")) and f["s300"] < 10, [
        "The break came with no push behind it: spot only {s300:+.0f} pts in 5 minutes. On {ref_day} the six such entries went 3-3 for −₹28,629 — the weakest group of the day.",
        "Flat 5-minute tape ({s300:+.0f} pts) into a breakout. It can still work; it usually needs a second impulse. The confidence is not there yet.",
        "No momentum behind this entry ({s300:+.0f} pts / 5 min). The level broke on a tick, not on a wave.",
        "Breakout on a quiet tape ({s300:+.0f} pts / 5 min). Half of these fail quickly; the stop is doing its job if it does."],
        3, "s300 < 10: 6 trades, 3 wins, −₹28.6k, mean −0.9 %; 10-50: 21 trades, 13 wins, +₹3.77 L"),
    T("chase.good_push", "entry", "confidence", 3, lambda f: _ok(f.get("s300"), f.get("s60")) and 10 <= f["s300"] <= 50 and 5 <= f["s60"] <= 20, [
        "Good impulse: spot {s300:+.0f} pts over 5 min, {s60:+.0f} in the last minute. The break has a wave behind it, not a single tick.",
        "This is what a breakout should look like underneath: {s300:+.0f} / 5 min, steady, not a sprint. 13 of 21 such entries won on {ref_day}.",
        "Momentum is right-sized ({s60:+.0f} pts in 60 s, {s300:+.0f} in 5 min). Not chasing, not early."],
        3, "see chase.no_push"),
    T("chase.second_try", "entry", "information", 2, lambda f: _ok(f.get("since_exit")) and f["since_exit"] < 600 and bool(f.get("same_key")) and str(f.get("prev_reason") or "").split(" ")[0] in ("STOP", "TRAIL"), [
        "Re-entry on {strike} {rr}, {since_exit:.0f} s after the last exit ({prev_reason}, {prev_ret:+.1f} %). On {ref_day} re-entries within 10 min went {reentry_record}; the second attempt at 09:55 was the day's +30 %.",
        "Second attempt at the same break, {since_exit:.0f} s after the last exit. The rule allows it; just notice you are paying the spread twice for one idea.",
        "Back in after {since_exit:.0f} s. The level is now tested twice — if it holds this time it tends to run."],
        3, "19 Oct re-entries < 10 min: 09:37 +8.8, 09:55 +30.6, 10:39 +25.3, 12:04 +26.8, 12:23 −7.8, 12:46 +1.9 → 5-1"),
    # ── F trend ──────────────────────────────────────────────────────────────
    T("trend.against_30", "structure", "caution", 2, lambda f: _ok(f.get("s1800")) and f["s1800"] <= -20, [
        "You are trading against the last 30 minutes ({s1800:+.0f} pts the other way). On {ref_day}, 7 such entries went 3-4 for ≈ 0 — coin-flip territory.",
        "Counter-trend on the 30-min: the future has moved {abs_s1800:.0f} pts against your direction since {t_minus30}. The break may be the turn, or a pullback inside the trend.",
        "This entry fades the 30-minute move ({s1800:+.0f} pts). Not stupid — the {trail_pts:.0f}-pt stop makes it cheap to be wrong — but expect no help from the wider tape.",
        "Against the half-hour trend ({s1800:+.0f} pts). The {ref_day} replay had the engine's trend30 field null on every trade; this one is read live from the futures history."],
        12, "s1800 ≤ −20: 7 trades, 3 wins, −₹1.2k, +1.8 %; −20..0: 5 trades, 4 wins, +₹1.85 L; not monotonic → CAUTION"),
    T("trend.with_30", "structure", "confidence", 4, lambda f: _ok(f.get("s1800")) and f["s1800"] >= 20, [
        "With the 30-min trend ({s1800:+.0f} pts). Continuation entries went 7-5 on {ref_day} — not magic, but the wind is at your back.",
        "Trend-aligned: the last half-hour already moved {s1800:.0f} pts your way.",
        "The wider tape agrees with you ({s1800:+.0f} over 30 min)."],
        12, "s1800 ≥ 20: 12 trades, 7 wins, +₹1.51 L, mean +5.4 %"),
    T("trend.regime_against", "structure", "caution", 2, lambda f: f.get("regime_with") == -1, [
        "The regime read is directional the other way ({regime_why}). You are buying a counter-move. 3 of these on {ref_day}: 2 wins, so it is not a veto — but it is a reason to let the trail decide, not hope.",
        "Regime says {regime} {regime_arrow}; you are {dir_word}. A short leash is what the trail gives this one.",
        "Against the regime direction ({regime} {regime_arrow}). Fine on a {trail_pts:.0f}-pt stop; just do not expect a trend day to turn for you."],
        12, "regime_align False: 3 trades, 2 wins, +₹59k (small n)"),
    T("trend.regime_range", "structure", "caution", 3, lambda f: f.get("regime") in ("RANGE", "UNCERTAIN", "EXHAUSTION"), [
        "Regime: {regime}. Breakouts in a range regime went 3-5 on {ref_day} (mean +0.3 %) against 7-2 in DIRECTIONAL. Expect a smaller peak — median 11 pts, not 23.",
        "Range regime ({regime}). The break may be the edge of the box, not a trend start. Your trail will probably decide this one, not your target.",
        "{regime} tape. Half of these entries fail; the other half pay 5–20 %. Nothing to do but let the rule work."],
        12, "RANGE/UNCERTAIN/EXHAUSTION: 8 trades, 3 wins, −₹5.4k; DIRECTIONAL: 9 trades, 7 wins, +₹1.86 L"),
    # ── G time ───────────────────────────────────────────────────────────────
    T("time.hour_stats", "time", "information", 3, lambda f: f.get("hour") in REFS["hours"], [
        "Entries in the {hour:02d}:00 hour: {hour_n} trades, {hour_wins} wins, mean {hour_mean_ret:+.1f} %, mean best excursion {hour_peak:.0f} pts ({ref_day}). That is your base rate right now.",
        "Base rate for this hour on {ref_day}: {hour_wins}/{hour_n}, {hour_mean_ret:+.1f} %. Not a prediction — a prior.",
        "The {hour:02d}:xx hour paid {hour_pnl_txt} on {ref_day} across {hour_n} entries."],
        10, "9h 7/4 +5.9 %; 10h 5/4 +8.9 %; 11h 4/2 +11.7 %; 12h 6/4 +3.1 %; 13h 6/3 +2.3 %; 14h 4/2 +3.6 %"),
    T("time.pm_entry", "time", "caution", 3, lambda f: _ok(f.get("time_in")) and f["time_in"] >= "12:30:00", [
        "Afternoon entry ({time_in}). On {ref_day} PM entries averaged +2.6 % with a mean best excursion of 12.7 pts; the morning gave +7.4 % and 19.9 pts. Smaller moves — expect the trail to do the exiting.",
        "PM half ({time_in}). Fewer points per move after 12:30 on {ref_day}; the trade is worth taking, the expectation should be half the morning's.",
        "After 12:30. The tape gets narrower and IV ramps on expiry; good entries still pay (+20 % at 14:43 on {ref_day}), but the median was +1.7 %."],
        16, "AM: 20 trades, 12 wins, +₹2.55 L, +7.4 %; PM: 12 trades, 7 wins, +₹1.13 L, +2.6 %"),
    T("time.opening_burst", "time", "caution", 3, lambda f: _ok(f.get("time_in")) and f["time_in"] < "09:40:00", [
        "Opening burst: σ15 is {sigma15:.1f} pts, spreads are widest and premiums move 50 % in minutes. On {ref_day} the four pre-09:40 entries held a median 31 s and went 2-2.",
        "First 15 minutes of the window. Expect to be trailed out in under a minute either way — the {trail_pts:.0f}-pt trail is tiny against a {sigma15:.1f}-pt σ15.",
        "Early entry ({time_in}). On {ref_day} these fills were 0.35-pt spreads and premiums at their 5-min highs — the market charges most for the first move."],
        16, "pre-09:40: 4 trades, 2 wins, +₹9.9k, median hold 31 s"),
    T("time.last_window", "time", "caution", 2, lambda f: f.get("zero_dte") and _ok(f.get("time_in")) and f["time_in"] >= "14:15:00", [
        "{mins_to_flat:.0f} minutes to the forced flat. The trade cannot be a long one; the trail is your only exit besides the clock.",
        "Late window: entries stop at 14:45 and you are flat at 15:00. Three {ref_day} entries after 14:15: −2.3 %, −7.0 %, +20.1 %.",
        "Clock risk on top of price risk now — {mins_to_flat:.0f} minutes left."],
        16, "after 14:15: 3 trades, 1 win, +₹38.8k (one +20 %)"),
    # ── H size ───────────────────────────────────────────────────────────────
    T("size.vs_volume", "book", "caution", 2, lambda f: _ok(f.get("qty_vs_vol")) and f["qty_vs_vol"] >= 0.02, [
        "Your {qty} qty is {qty_vs_vol5_pct:.1f} % of what this strike traded in the last {vol_win_txt}. Big for the book; the exit will move the price against you.",
        "Size warning: {lots} lots on a strike that traded {vol5_lots:,.0f} lots in {vol_win_txt}. On {ref_day} the largest entry was 0.2 % of 5-min volume — you are at {qty_vs_vol5_pct:.1f} %.",
        "Liquidity is thinner than your order ({qty_vs_vol5_pct:.1f} % of the last {vol_win_txt}). Expect slippage on the way out, not just on the way in."],
        18, "19 Oct max qty/vol5 = 0.2 %; threshold 2 % (caution), 5 % (lesson) from market-maker practice, not data"),
    T("size.vs_book", "book", "caution", 2, lambda f: _ok(f.get("qty_vs_ss")) and f["qty_vs_ss"] >= 0.5, [
        "You lifted {qty_vs_ss_pct:.0f} % of the visible ask size ({ss_lots:,.0f} lots across {sso} orders). The book will refill, but the next trader pays more — and so will you on exit.",
        "Order larger than half the top-of-book ({qty_vs_ss_pct:.0f} %). Fill was {over_mid:+.2f} over mid — that is where the size shows.",
        "Big relative to the visible book ({qty_vs_ss_pct:.0f} % of ask size). Slices are the engine's answer (slices={slices})."],
        18, "19 Oct sizes 650-6,825 qty → 0.4-4 % of a typical 170k visible book; practice threshold"),
    T("size.all_in_ok", "book", "confidence", 4, lambda f: _ok(f.get("qty_vs_vol"), f.get("qty_vs_ss")) and f["qty_vs_vol"] < 0.005 and f["qty_vs_ss"] < 0.2, [
        "{lots} lots ({qty} qty) is {qty_vs_vol5_pct:.2f} % of the last {vol_win_txt} of volume and {qty_vs_ss_pct:.0f} % of the visible ask. Size is invisible to the market. All-in is fine here.",
        "Liquidity check passed: your order is noise against {vol5_lots:,.0f} lots traded in the last {vol_win_txt}.",
        "Size is not your problem on this contract ({qty_vs_vol5_pct:.2f} % of recent volume)."],
        18, "all 32 trades on 19 Oct"),
    T("size.capital_jump", "day", "information", 3,
      lambda f: (_ok(f.get("prev_lots"), f.get("lots")) and f["prev_lots"] > 0 and f["lots"] >= 1.5 * f["prev_lots"]) or (_ok(f.get("capital_deployed"), f.get("capital")) and f["capital"] > 0 and f["capital_deployed"] >= 0.9 * f["capital"]), [
        "{lots} lots this time, up from {prev_lots} — the last win is now at risk on this entry. Same {trail_pts:.0f}-pt stop, {stop_rs_txt} at stake instead of {prev_stop_rs_txt}.",
        "Capital deployed {capital_deployed_txt} of {capital_txt} ({deployed_pct:.0f} %). All-in by design; just see the number.",
        "Size stepped up to {lots} lots after the {prev_ret:+.0f} % trade. The rule compounds; the stop in rupees compounds with it ({stop_rs_txt})."],
        18, "19 Oct lots 10 → 105; the 13:29 trade (93 lots) lost ₹39.6k — largest size on a lottery strike"),
    # ── I straddle ───────────────────────────────────────────────────────────
    T("strad.priced_in", "structure", "caution", 2, lambda f: _ok(f.get("strad_5")) and (f["strad_5"] >= 5 or f.get("strad_state_in") == "EXPANDING"), [
        "The ATM straddle went from {strad_5ago:.1f} to {strad_px_in:.1f} in 5 min ({strad_5:+.1f}). The market is paying up for a move — you are buying after it was priced. {ref_day} 09:27 / 09:28 (+21, +32): +7.9 %, −0.8 %.",
        "Straddle expanding ({strad_5:+.1f} / 5 min). Your option is dearer than it was; if spot delivers, the expansion helps, if not it reverses on you.",
        "Move priced: straddle {strad_px_in:.1f} vs VWAP {strad_vwap_in:.1f}. You need spot to beat what the straddle already implies — about {implied_move:.0f} pts to the close.",
        "The straddle re-priced before you ({strad_5:+.1f} in 5 min). Not a stupid entry — an expensive one."],
        14, "strad_5 ≥ +5: 6 trades, 4 wins, +₹92.9k (mixed); ≤ −2: 13 trades, 9 wins, +₹2.38 L"),
    T("strad.compressing", "structure", "confidence", 3, lambda f: _ok(f.get("strad_5")) and f["strad_5"] <= -2, [
        "Straddle compressing ({strad_5:+.1f} in 5 min, {strad_state_in}). You bought the option while the market was giving vol away — the cheapest state. 13 such entries on {ref_day}: 9 winners, mean +7.8 %.",
        "Vol was deflating into your entry (straddle {strad_px_in:.1f}, VWAP {strad_vwap_in:.1f}). A real move from here gets paid twice: delta and re-expansion.",
        "Straddle {strad_5:+.1f} in 5 min and below VWAP {strad_vwap_in:.1f}. Good moment to own gamma."],
        14, "see strad.priced_in"),
    T("strad.flat", "structure", "information", 5, lambda f: _ok(f.get("strad_5")) and -2 < f["strad_5"] < 2, [
        "Straddle flat ({strad_5:+.1f} / 5 min). The option market has no opinion on this break yet — the 7 flat-straddle entries on {ref_day} averaged +1.0 %.",
        "No vol signal either way (straddle {strad_px_in:.1f}, {strad_5:+.1f} in 5 min). Spot has to do all the work.",
        "The straddle ({strad_5:+.1f} / 5 min) is not confirming or denying the break."],
        14, "−2..2: 7 trades, 4 wins, +₹10k, mean +1.0 %"),
    # ── J room ───────────────────────────────────────────────────────────────
    T("room.into_wall", "structure", "caution", 2, lambda f: _ok(f.get("room_in")) and f["room_in"] <= 25, [
        "Entering {room_in:.0f} pts from the {wall_in:.0f} wall ({wall_oi_lots:,.0f} lots OI). You need ≈ 19 pts to pay; the wall is closer than that. If it holds, you are trailed out at the wall.",
        "The next OI wall is at {wall_in:.0f} — {room_in:.0f} pts away. The room advisor said '{room_why}'. Tight.",
        "Little room: {room_in:.0f} pts to {wall_in:.0f}. Walls break on expiry day, but they break after a fight; the first touch usually rejects.",
        "Wall ahead at {wall_in:.0f}. Your best case before it is ≈ {room_in:.0f} pts × delta {delta_abs:.2f} = {room_prem:.0f} pts of premium."],
        20, "19 Oct: room advisor never vetoed (nearest wall 360-521 pts); threshold 25 = 2× stop + the 'need ~19'"),
    T("room.open_road", "structure", "confidence", 4, lambda f: _ok(f.get("room_in")) and f["room_in"] >= 100, [
        "Open road: next wall {wall_in:.0f} is {room_in:.0f} pts away. Nothing on the chain stands between you and a full run.",
        "{room_in:.0f} pts of room to {wall_in:.0f}. The trail, not a wall, will decide this one.",
        "No OI wall within {room_in:.0f} pts. Good."],
        20, "all 11 logged on 19 Oct"),
    T("room.stale_chain", "data", "information", 5, lambda f: _ok(f.get("chain_age_in")) and f["chain_age_in"] >= 180, [
        "The wall map is {chain_age_in:.0f} s old (chain polls every 90 s). Treat room numbers as approximate.",
        "OI data is {chain_age_in:.0f} s stale; walls may have moved."],
        20, "informational"),
    # ── K quote ──────────────────────────────────────────────────────────────
    T("quote.stale_trade", "data", "caution", 3, lambda f: _ok(f.get("trade_age_in")) and f["trade_age_in"] >= 5, [
        "The contract had not traded for {trade_age_in:.0f} s when you were filled at {entry:.2f}. In paper you got the LTP; live you would have paid the ask ({entry_ask:.2f}) — {ask_minus:+.2f}.",
        "Stale last-trade ({trade_age_in:.0f} s). The paper fill is optimistic by up to the spread. On {ref_day} the two 10 s+ stale entries were the two best trades of the day (+23.7 %, +26.8 %) — so stale is not bad, just uncertain.",
        "No print for {trade_age_in:.0f} s before entry. Your 'entry' is a quote, not a trade — judge this one by the bid/ask ({entry_bid:.2f}/{entry_ask:.2f}), not the LTP.",
        "Quiet contract at entry ({trade_age_in:.0f} s since last trade). The engine refuses quotes ≥ 15 s old; this one was fine, just slow."],
        22, "trade_age 1-5 s: 10/3 (−₹27k); 5-30 s: 7/6 (+₹2.36 L): no direction signal — fill honesty only"),
    T("quote.wide_or_crossed", "data", "caution", 2,
      lambda f: (_ok(f.get("entry_bid")) and f["entry_bid"] <= 0) or (_ok(f.get("entry_bid"), f.get("entry_ask")) and f["entry_ask"] < f["entry_bid"]) or (_ok(f.get("spread_pct")) and f["spread_pct"] > 2.0), [
        "The book was {entry_bid:.2f}/{entry_ask:.2f} at your fill — not a healthy two-sided quote. The entry price is less certain than it looks.",
        "Crossed or one-sided quote at entry. Paper filled you at LTP {entry:.2f}; a live order could have printed anywhere in {entry_bid:.2f}–{entry_ask:.2f}.",
        "Quote quality was poor at the fill ({entry_bid:.2f}/{entry_ask:.2f}). The exit quote age deserves the same look."],
        22, "never on 19 Oct (all spreads 0.15-0.35, two-sided)"),
    T("quote.feed_lag", "data", "caution", 2, lambda f: _ok(f.get("lag_s_in")) and f["lag_s_in"] >= 1.0, [
        "Feed lag was {lag_s_in:.1f} s at entry. The spot break you traded was {lag_s_in:.1f} s old by the time the order went — the premium may already reflect it.",
        "Your fill came on a laggy feed ({lag_s_in:.1f} s). Everything you see is slightly behind; the trail will be slightly late too.",
        "Lag {lag_s_in:.1f} s. Not your fault; it is still your cost."],
        22, "informational; 19 Oct replay lag n/a"),
    # ── L noise ──────────────────────────────────────────────────────────────
    T("noise.stop_inside_sigma", "structure", "caution", 1, lambda f: _ok(f.get("sigma15")) and f["sigma15"] >= 8, [
        "σ15 is {sigma15:.1f} pts; your stop is {trail_pts:.0f}. The noise alone can take you out. On {ref_day} the five σ15 > 7 entries went 2-3 for +₹1,388 — a wash.",
        "Noisy tape ({sigma15:.1f} pts σ15). A {trail_pts:.0f}-pt trail here is a coin, not a stop. Expect a quick exit either way.",
        "Stop is inside the noise band (σ15 {sigma15:.1f}). This is the structural weakness of a fixed {trail_pts:.0f}-pt trail at the open.",
        "σ15 {sigma15:.1f} vs stop {trail_pts:.0f}: the market can hit your stop without changing its mind."],
        8, "sigma15 7-9: 5 trades, 2 wins, +₹1.4k, +0.5 %; 5-7: 5 trades, 5 wins, +12.0 %"),
    T("noise.stop_well_sized", "structure", "confidence", 4, lambda f: _ok(f.get("sigma15")) and 5 <= f["sigma15"] < 7, [
        "σ15 {sigma15:.1f} pts: the {trail_pts:.0f}-pt stop is about 2σ of the 15-min noise — sized right. All five such entries won on {ref_day} (mean +12 %).",
        "Noise is {sigma15:.1f} pts; the stop ({trail_pts:.0f}) is comfortably outside it. The trade will be decided by direction, not by jitter.",
        "Stop vs noise: {trail_pts:.0f} vs {sigma15:.1f}. Good ratio."],
        8, "see noise.stop_inside_sigma"),
    T("noise.range5_wide", "structure", "caution", 3, lambda f: _ok(f.get("range5")) and f["range5"] >= 40, [
        "The last 5 minutes spanned {range5:.0f} pts — three stops' worth. The break is inside a violent bar, not after a tight base.",
        "5-min range {range5:.0f} pts. Big bars give big peaks (mean 17 pts on {ref_day}) and big whips; both are coming.",
        "Wide 5-min range ({range5:.0f}). The rule, not the breath, is the thing to hold."],
        8, "range5 ≥ 40: 7 trades, 5 wins, +₹68k; 15-25: 13 trades, 6 wins, +₹18k"),
    # ── M composite (fires with the card) ────────────────────────────────────
    T("entry.stupid", "entry", "lesson", 1, lambda f: f.get("entry_grade") == "E", [
        "Honest read: this was a poor entry — {reason_1}; {reason_2}. On {ref_day} the four grade-E entries went 0-4 for −₹55,591. The rule still gets its {trail_pts:.0f} pts; expect to need luck.",
        "Grade E. Not the direction — the price and the contract: {reason_1}, {reason_2}. The trail does its work; nothing to add to it in your head.",
        "You know what this is: {reason_1}. Take the lesson now, the result later.",
        "This entry paid for everything at once: {reason_list}. The stop is cheap; the discipline is to let it be cheap."],
        0, "E: 4 trades, 0 wins, −₹55.6k (in-sample)"),
    T("entry.costly_not_stupid", "entry", "lesson", 2,
      lambda f: f.get("entry_grade") in ("C", "D") and _ok(f.get("money"), f.get("extr_pct"), f.get("s300")) and not (f["money"] < 40 or f["extr_pct"] >= 45) and f["s300"] >= 10
      and (((f.get("over_mid") or 0) > 0.30) or ((f.get("iv_run_pct") or 0) >= 90 and (f.get("iv_vs30") or 0) > 3) or ((f.get("rise5") or 0) >= 50) or ((f.get("strad_5") or 0) >= 5)), [
        "Right idea, expensive ticket: {reason_1}. Direction is fine; you simply paid up. Each extra point paid is a point the trail must earn before you see green.",
        "Costly, not stupid — {reason_1}. The {ref_day} grade-C/D entries still went 4-3 (+₹44.7k); the price you paid lowers the average, it does not kill the trade.",
        "The entry is sound, the price is rich ({reason_1}). The edge is smaller, not gone."],
        0, "C: 3/2 +₹38k; D: 4/2 +₹7k on 19 Oct"),
    T("entry.clean", "entry", "confidence", 1, lambda f: f.get("entry_grade") == "A", [
        "Clean entry, grade A: {reason_1}; {reason_2}; {reason_3}. On {ref_day} grade-A entries went 11-5 for +₹2.78 L, mean +9 %, mean best excursion 22 pts. You have done your part — now the holding.",
        "Grade A (score {entry_score:+d}). Nothing to fix about this entry: {reason_list}. If it loses, it loses honestly.",
        "This is what a good entry looks like in numbers (score {entry_score:+d}): {reason_list}. The plan is the thing to hold.",
        "A-grade fill and contract ({reason_1}; {reason_2}). On {ref_day} 11 of 16 A-entries won. The market still decides, but you are not starting from behind."],
        0, "A: 16 trades, 11 wins, +₹2,77,739, mean +9.2 %, mean peak 21.6 pts (in-sample)"),
    T("entry.what_it_cost", "entry", "information", 3, lambda f: _ok(f.get("over_mid_rs"), f.get("day_over_mid_rs")), [
        "This entry's price tag vs ideal: spread {over_mid_rs_txt}{extr_clause}. Day so far: {day_over_mid_rs_txt} of spread. On {ref_day} the whole day's entry tax was ₹24,963 against ₹3.69 L of profit — 6.8 %.",
        "Cost of entering: {over_mid_rs_txt} on the spread. Running total today {day_over_mid_rs_txt}.",
        "Entry tax {over_mid_rs_txt}. Small; the strike and the timing are where the real money is made or lost."],
        30, "19 Oct: Σ over-mid ₹24,963; Σ full-spread round trip ₹21,899; buy@ask/sell@bid would have made ₹3.83 L vs ₹3.69 L"),
    T("entry.second_look_60s", "entry", "information", 3, lambda f: _ok(f.get("ret_now"), f.get("spot_vs_in")), [
        "One minute in: premium {ret_now:+.1f} %, spot {spot_vs_in:+.0f} from entry, best {best_vs_in:+.0f}. The entry price now looks {entry_look} — the market, not the grade, says so.",
        "60-s check: you are {ret_now:+.1f} % from your fill. The entry cost ({over_mid:.2f} over mid) is {cost_status}.",
        "After a minute the fill reads as {entry_look}: spot {spot_vs_in:+.0f}, premium {ret_now:+.1f} %."],
        60, "19 Oct median hold 144 s; 5 of 13 losers were out inside 40 s, the other 8 bled 89-540 s"),
    T("entry.vix_context", "structure", "information", 5, lambda f: _ok(f.get("vix")), [
        "VIX {vix:.2f} (seen {vix_lo:.2f}–{vix_hi:.2f} today). On {ref_day} entries with VIX ≤ 14.7 averaged +9.4 %; above it +1.3 % — mostly a time-of-day effect, but it is the air you are breathing.",
        "VIX {vix:.2f}. Low and steady on {ref_day}; moves were short. Higher VIX days pay more per break and whip more.",
        "Vol context: VIX {vix:.2f}."],
        25, "VIX ≤ 14.7: 17 trades, 11 wins, +₹3.0 L; > 14.7: 15 trades, 8 wins, +₹68.6k"),
]

