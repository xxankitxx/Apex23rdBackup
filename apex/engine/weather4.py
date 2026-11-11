"""
Photo version 4 (9 Nov, owner: "67-68 items ... are not enough to identify a bad trade from a good trade. So add some
more ... at least 30-40 more different kind of items"). 36 new items, docs/27 numbers 69-104, six new groups:

  L  the tape's structure   69 yesterday's shape · 70 pivot levels · 71 strike grid · 72 the last bars · 73 bar runs ·
                            74 position in recent windows · 75 oscillators · 76 moving averages · 77 compression ·
                            78 the day's net move · 79 persistence · 80 the adverse path
  M  across markets         81 sister divergence · 82 the VIX path · 83 breadth at other horizons ·
                            84 dispersion and concentration · 85 the leaders
  N  the option and chain   86 moneyness · 87 gearing · 88 implied move used · 89 the opposite leg ·
                            90 the premium's own path · 91 entry liquidity · 92 the IV path · 93 the wings ·
                            94 own-strike OI · 95 futures OI build-up
  O  flow through time      96 volume acceleration · 97 up-volume share · 98 VWAP stretch · 99 call/put flow tilt
  P  the books around it    100 other books' positions (and the family's busy / free count, docs/35 §7) ·
                            101 other books' results today · 102 trigger density
  Q  this book's day        103 re-entry context · 104 the day's P&L shape

An OBSERVER, like the rest of the photograph: no book reads it. No look-ahead: every history read is by value_at /
bisect on the arrival stamp at or before the trigger second; the books' trades and positions are those already closed
or open at this step; the trigger log holds only earlier triggers. The direction-free part (base4) is computed only
when a photograph is taken, once per market second. Each block is guarded on its own: a failure leaves that block's
fields absent and names the block in `v4_error`; it never stops the entry and never writes 0 for "no data".
"""
import math
from bisect import bisect_right

import numpy as np

from .weather import TOL_S, _atm_iv, _fin, _r, _sg, breadth, change, value_at, window

N_ITEMS = 104


def _corr(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 5 or len(a) != len(b) or np.std(a) <= 0 or np.std(b) <= 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


# ── the direction-free part, once per market second, only when a photograph is taken ─────────────────────────
def base4(W, now_s):
    sec = int(now_s)
    if getattr(W, "_b4_s", None) == sec:
        return W._b4
    t, out, errs = float(now_s), {}, []
    for fn in (_b_bars, _b_cross, _b_flow):
        try:
            fn(W, t, out)
        except Exception:                           # noqa: BLE001  (an observer)
            errs.append(fn.__name__)
    if errs:
        out["errors"] = errs
    W._b4_s, W._b4 = sec, out
    return out


def _b_bars(W, t, out):
    """Bars, runs, oscillators, averages, persistence from the trusted 1-Hz spot."""
    ts, ps = W.spot_t, W.spot_p
    sp = value_at(ts, ps, t)
    if sp is None:
        return
    m = [value_at(ts, ps, t - 60 * k) for k in range(61)]            # 1-min marks, newest first
    n_ok = next((k for k, x in enumerate(m) if x is None), len(m))    # marks available without a hole
    df = [m[k - 1] - m[k] for k in range(1, n_ok)]                    # 1-min moves, newest first (+ = up)
    rng = {}
    for name, span in (("5", 300), ("15", 900), ("60", 3600)):
        xs = window(ts, ps, t, span)
        if xs and value_at(ts, ps, t - span) is not None:             # only a complete window
            rng[name] = (max(xs), min(xs))
    out["rng"] = rng
    # 72 the last bars (rolling windows ending at the trigger second)
    for name, span in (("5", 300), ("1", 60)):
        xs, op = window(ts, ps, t, span), value_at(ts, ps, t - span)
        if xs and op is not None:
            hi, lo = max(max(xs), op), min(min(xs), op)
            out[f"bar{name}"] = (op, hi, lo, sp)
    r1 = []
    for k in range(16):                                               # 1-min ranges, newest first
        xs = window(ts, ps, t - 60 * k, 60)
        if len(xs) < 30:
            break
        r1.append(max(xs) - min(xs))
    if len(r1) >= 15:
        out["atr1_15"] = float(np.mean(r1[:15]))
    if len(r1) == 16 and np.mean(r1[1:]) > 0:
        out["bar1_range_vs15"] = r1[0] / float(np.mean(r1[1:]))
    # 73 runs
    if df:
        nz = [x for x in df if x != 0]
        run = 0
        for x in nz:
            if (x > 0) != (nz[0] > 0):
                break
            run += 1
        out["run1"] = run if nz and nz[0] > 0 else -run
    if len(df) >= 30:
        out["up_share30"] = sum(1 for x in df[:30] if x > 0) / 30.0
        out["dn_share30"] = sum(1 for x in df[:30] if x < 0) / 30.0
    hl = []
    for j in range(6):
        xs = window(ts, ps, t - 300 * j, 300)
        if len(xs) < 150:
            break
        hl.append((max(xs), min(xs)))
    if len(hl) == 6:
        out["hh5_up"] = sum(1 for j in range(5) if hl[j][0] > hl[j + 1][0] and hl[j][1] > hl[j + 1][1])
        out["hh5_dn"] = sum(1 for j in range(5) if hl[j][0] < hl[j + 1][0] and hl[j][1] < hl[j + 1][1])
    # 75 oscillators
    if len(df) >= 14:
        g, l = sum(x for x in df[:14] if x > 0), -sum(x for x in df[:14] if x < 0)
        out["rsi1"] = 100.0 * g / (g + l) if g + l > 0 else None
    m5 = [value_at(ts, ps, t - 300 * k) for k in range(15)]
    if all(x is not None for x in m5):
        d5 = [m5[k - 1] - m5[k] for k in range(1, 15)]
        g, l = sum(x for x in d5 if x > 0), -sum(x for x in d5 if x < 0)
        out["rsi5"] = 100.0 * g / (g + l) if g + l > 0 else None
    if n_ok >= 20:
        sd = float(np.std(m[:20]))
        out["z20"] = (sp - float(np.mean(m[:20]))) / sd if sd > 0 else None
    # 76 moving averages of the 1-min marks
    for n in (5, 20, 60):
        if n_ok >= n:
            out[f"ma{n}"] = float(np.mean(m[:n]))
    if n_ok >= 25:
        out["ma20_prev"] = float(np.mean(m[5:25]))
    # 78 the day's net move
    i = bisect_right(ts, t)
    if i:
        first = ps[0]
        out["first"] = first
        a = np.asarray(ps[:i], float) - first
        cur = np.sign(a[-1])
        if cur != 0:
            other = np.nonzero(np.sign(a) != cur)[0]
            out["open_side_min"] = (t - ts[int(other[-1]) + 1]) / 60.0 if len(other) and other[-1] + 1 < i else \
                (t - ts[0]) / 60.0
    # 79 persistence
    if len(df) >= 30:
        out["ac1_30"] = _corr(df[:29], df[1:30])
    if n_ok == 61:
        v1 = float(np.var(df))
        v5 = float(np.var([m[5 * k] - m[5 * k + 5] for k in range(12)]))
        out["vr5_60"] = v5 / (5.0 * v1) if v1 > 0 else None
    # 80 the adverse path
    if len(df) >= 15:
        out["max_up1_15"] = max(0.0, max(df[:15]))
        out["max_dn1_15"] = max(0.0, -min(df[:15]))
        out["n_up15"] = sum(1 for x in df[:15] if x > 0)
        out["n_dn15"] = sum(1 for x in df[:15] if x < 0)


def _b_cross(W, t, out):
    """Bank Nifty against Nifty, the VIX's day, breadth at 1 and 15 minutes, dispersion, the leaders."""
    ts, ps = W.spot_t, W.spot_p
    sp, s300 = value_at(ts, ps, t), value_at(ts, ps, t - 300)
    out["nifty300"] = 100 * (sp / s300 - 1) if sp and s300 else None
    bn, b300 = value_at(W.bn_t, W.bn_p, t), value_at(W.bn_t, W.bn_p, t - 300)
    out["bn300"] = 100 * (bn / b300 - 1) if bn and b300 else None
    a = [value_at(ts, ps, t - 10 * k) for k in range(181)]
    c = [value_at(W.bn_t, W.bn_p, t - 10 * k) for k in range(181)]
    if all(x is not None for x in a) and all(x is not None for x in c):
        out["bn_corr30"] = _corr(np.diff(np.log(a)), np.diff(np.log(c)))
    k = bisect_right(W.vix_t, t)
    if k >= 2:
        hi, lo = max(W.vix_p[:k]), min(W.vix_p[:k])
        out["vix_day_pos"] = (W.vix_p[k - 1] - lo) / (hi - lo) if hi > lo else None
    hw = (W.hw_t, W.hw_a, W.hw_w)
    out["b60"] = breadth(*hw, t, lag=60)
    out["b900"] = breadth(*hw, t, lag=900)
    out["b300"] = breadth(*hw, t)
    out["b300_prev"] = breadth(*hw, t - 300)
    if not W.hw_t or W.hw_w is None:
        return
    i1 = bisect_right(W.hw_t, t) - 1
    if i1 < 0 or t - W.hw_t[i1] > TOL_S:
        return
    w, a1 = np.asarray(W.hw_w, float), W.hw_a[i1]

    def ret(lag):
        i0 = bisect_right(W.hw_t, t - lag) - 1
        if i0 < 0 or (t - lag) - W.hw_t[i0] > TOL_S:
            return None
        with np.errstate(divide="ignore", invalid="ignore"):
            return a1 / W.hw_a[i0] - 1.0
    c300, c60 = ret(300), ret(60)
    if c300 is not None:
        ok = np.isfinite(c300) & (w > 0)
        if ok.sum() >= 3:
            ww, cc = w[ok], c300[ok]
            mu = float(np.sum(ww * cc) / ww.sum())
            out["hw_disp300"] = 100.0 * math.sqrt(float(np.sum(ww * (cc - mu) ** 2) / ww.sum()))
            con = np.abs(ww * cc)
            out["hw_top3_share"] = float(np.sort(con)[-3:].sum() / con.sum()) if con.sum() > 0 else None
            out["hw_n_up"], out["hw_n_dn"] = int((cc > 0).sum()), int((cc < 0).sum())
    order = np.argsort(-w)[:3]
    for name, c_ in (("60", c60), ("300", c300)):
        if c_ is not None and np.isfinite(c_[order[0]]):
            out[f"lead1_{name}"] = 100.0 * float(c_[order[0]])
    if c60 is not None and np.isfinite(c60[order]).all():
        out["lead_up3"], out["lead_dn3"] = int((c60[order] > 0).sum()), int((c60[order] < 0).sum())
    i0 = bisect_right(W.hw_t, t - 1800)
    if i0 > 0 and i1 - i0 >= 600:                                      # a full 30 minutes of the heavyweights
        blk = np.vstack(W.hw_a[i0:i1 + 1])
        with np.errstate(all="ignore"):
            hi, lo = np.nanmax(blk, axis=0), np.nanmin(blk, axis=0)
        ok = np.isfinite(a1) & np.isfinite(hi) & (w > 0)
        if ok.any():
            out["hw_at_hi30"] = float(w[ok & (a1 >= hi * 0.999)].sum() / w[ok].sum())
            out["hw_at_lo30"] = float(w[ok & (a1 <= lo * 1.001)].sum() / w[ok].sum())


def _b_flow(W, t, out):
    """Volume acceleration, up-volume share, the VWAP stretch, call/put volume, the ATM IV's path, the straddle."""
    S = W._s
    for name in ("fut_ttq", "hw_ttq"):
        v0, v1 = change(*S(name), t, 60), change(*S(name), t - 60, 60)
        out[name + "_accel"] = v0 / v1 if v0 is not None and v1 else None
    out["fut_vol300"] = change(*S("fut_ttq"), t, 300)
    ce60, pe60 = change(*S("ce_ttq"), t, 60), change(*S("pe_ttq"), t, 60)
    ce60b, pe60b = change(*S("ce_ttq"), t - 60, 60), change(*S("pe_ttq"), t - 60, 60)
    out["ce_vol60"], out["pe_vol60"] = ce60, pe60
    if None not in (ce60, pe60, ce60b, pe60b) and ce60b + pe60b > 0:
        out["band_vol_accel"] = (ce60 + pe60) / (ce60b + pe60b)
    ft, fv = S("fut_ttq")
    wt, wv = S("fwd")
    for lag in (60, 300):
        i0, i1 = bisect_right(ft, t - lag) - 1, bisect_right(ft, t) - 1
        if i0 < 0 or i1 <= i0 or (t - lag) - ft[i0] > TOL_S:
            continue
        up = dn = 0.0
        for j in range(i0 + 1, i1 + 1):
            p1, p0 = value_at(wt, wv, ft[j]), value_at(wt, wv, ft[j - 1])
            dv = fv[j] - fv[j - 1]
            if p1 is None or p0 is None or dv <= 0:
                continue
            if p1 > p0:
                up += dv
            elif p1 < p0:
                dn += dv
        out[f"upvol{lag}"] = up / (up + dn) if up + dn > 0 else None
    et, ev = S("ext")
    k = bisect_right(et, t)
    ext = value_at(et, ev, t)
    if k >= 60 and ext is not None:
        xs = np.asarray(ev[:k], float)
        sd = float(np.std(xs))
        out["vwap_z"] = ext / sd if sd > 0 else None
        sg = np.sign(xs[xs != 0])
        out["vwap_cross_n"] = int(np.sum(sg[1:] != sg[:-1])) if len(sg) > 1 else 0
        far = float(xs.max()) if ext > 0 else float(-xs.min()) if ext < 0 else None
        out["vwap_stretch_share"] = abs(ext) / far if far and far > 0 else None
    it, iv = S("atm_iv")
    k = bisect_right(it, t)
    if k >= 60:
        hi, lo, cur = max(iv[:k]), min(iv[:k]), value_at(it, iv, t)
        out["atm_iv_day_pos"] = (cur - lo) / (hi - lo) if cur is not None and hi > lo else None
    a = [value_at(it, iv, t - 60 * j) for j in range(16)]
    b = [value_at(W.spot_t, W.spot_p, t - 60 * j) for j in range(16)]
    if all(x is not None for x in a) and all(x is not None for x in b):
        out["iv_spot_corr15"] = _corr(np.diff(a), np.diff(b))
    ac, ap = value_at(*S("atm_ce"), t), value_at(*S("atm_pe"), t)
    out["strad_now"] = ac + ap if ac and ap else None
    c0, p0 = S("atm_ce"), S("atm_pe")
    if c0[0] and p0[0] and c0[0][0] <= t and p0[0][0] <= t:
        out["strad_open"] = c0[1][0] + p0[1][0]


# ── the photograph's part: in the trade's direction, the contract, the books ────────────────────────────────
def photo_v4(out, ctx, d, opt, book, b, sp):
    W = ctx.get("_wx")
    t = ctx.get("now_s")
    b4 = base4(W, t) if W is not None and t is not None else {}
    errs = list(b4.get("errors") or [])
    for fn in (_p_structure, _p_cross, _p_option, _p_chain, _p_flow, _p_books, _p_own):
        try:
            fn(out, ctx, d, opt or {}, book, b, b4, sp, t)
        except Exception:                           # noqa: BLE001  (an observer: never stops the entry)
            errs.append(fn.__name__)
    if errs:
        out["v4_error"] = ",".join(errs)


def _pos(x, hl, d):
    if x is None or not hl or hl[0] <= hl[1]:
        return None
    v = (x - hl[1]) / (hl[0] - hl[1])
    return _r(v if d > 0 else 1.0 - v)


def _pick(up, dn, d):
    return up if d > 0 else dn


def _p_structure(out, ctx, d, o, book, b, b4, sp, t):
    dv = ctx.get("day") or {}
    pdh, pdl, pdc = _fin(dv.get("pdh")), _fin(dv.get("pdl")), _fin(dv.get("pdc"))
    rn = b.get("range_now")
    # 69 yesterday's shape, 70 floor pivots
    if pdh and pdl and pdh > pdl:
        out["pd_range"] = _r(pdh - pdl, 2)
        out["range_vs_pd"] = _r(rn / (pdh - pdl), 3) if rn is not None else None
        if sp is not None:
            out["inside_pd"] = bool(pdl <= sp <= pdh)
        if pdc:
            x = (pdc - pdl) / (pdh - pdl)
            out["pd_close_pos"] = _r(x if d > 0 else 1.0 - x)
            if sp is not None:
                P = (pdh + pdl + pdc) / 3.0
                levels = (P - (pdh - pdl), 2 * P - pdh, P, 2 * P - pdl, P + (pdh - pdl))      # S2 S1 P R1 R2
                out["pivot_dist"] = _r((sp - P) * d, 2)
                ahead = [(lv - sp) * d for lv in levels if (lv - sp) * d > 0]
                out["piv_next_ahead"] = _r(min(ahead), 2) if ahead else None
    if sp is None:
        return
    # 71 the strike grid (spot against the 50-point strikes)
    nxt = (math.floor(sp / 50.0) + 1) * 50.0 if d > 0 else (math.ceil(sp / 50.0) - 1) * 50.0
    out["strike50_ahead"] = _r((nxt - sp) * d, 2)
    out["strike_pin"] = _r(abs(sp - round(sp / 50.0) * 50.0), 2)
    # 72 the last bars
    for name in ("5", "1"):
        bar = b4.get("bar" + name)
        if bar:
            op, hi, lo, cl = bar
            out[f"bar{name}_body"] = _r((cl - op) * d, 2)
            if name == "5" and hi > lo:
                out["bar5_body_share"] = _r(abs(cl - op) / (hi - lo), 3)
                out["bar5_wick_ahead"] = _r(((hi - cl) if d > 0 else (cl - lo)) / (hi - lo), 3)
    out["bar1_range_vs15"] = _r(b4.get("bar1_range_vs15"), 3)
    # 73 runs
    out["run1_with"] = b4["run1"] * d if b4.get("run1") is not None else None
    out["with_share30"] = _r(_pick(b4.get("up_share30"), b4.get("dn_share30"), d), 3)
    out["hh_hl5"] = _pick(b4.get("hh5_up"), b4.get("hh5_dn"), d)
    # 74 position in the recent windows (1 = at the extreme in the trade's direction)
    rng = b4.get("rng") or {}
    for name in ("5", "15", "60"):
        out[f"pos{name}"] = _pos(sp, rng.get(name), d)
    # 75 oscillators
    for k_, name in (("rsi1", "rsi14_1m"), ("rsi5", "rsi14_5m")):
        v = b4.get(k_)
        out[name] = _r(v if d > 0 else 100.0 - v, 1) if v is not None else None
    out["z20"] = _sg(b4.get("z20"), d, 2)
    # 76 moving averages
    n_with = n_ma = 0
    for n in (5, 20, 60):
        ma = b4.get(f"ma{n}")
        out[f"ma{n}_dist"] = _r((sp - ma) * d, 2) if ma is not None else None
        if ma is not None:
            n_ma += 1
            n_with += 1 if (sp - ma) * d > 0 else 0
    out["ma_stack"] = n_with if n_ma == 3 else None
    out["ma20_slope"] = _r((b4["ma20"] - b4["ma20_prev"]) * d, 2) if b4.get("ma20_prev") is not None else None
    # 77 compression
    r = {k: (v[0] - v[1]) for k, v in rng.items()}
    out["range5"], out["range15"], out["range60"] = _r(r.get("5"), 2), _r(r.get("15"), 2), _r(r.get("60"), 2)
    out["squeeze"] = _r(r["15"] / r["60"], 3) if r.get("15") is not None and r.get("60") else None
    out["atr1_15"] = _r(b4.get("atr1_15"), 2)
    out["rv_ratio"] = _r(b["rv1"] / b["rv15"], 3) if b.get("rv1") is not None and b.get("rv15") else None
    # 78 the day's net move
    if b4.get("first") is not None:
        mv = (sp - b4["first"]) * d
        out["day_move"] = _r(mv, 2)
        out["day_move_share"] = _r(mv / rn, 3) if rn else None
    out["open_side_min"] = _r(b4.get("open_side_min"), 1)
    # 79 persistence
    out["ac1_30"], out["vr5_60"] = _r(b4.get("ac1_30"), 3), _r(b4.get("vr5_60"), 3)
    # 80 the adverse path
    out["max_adv1_15"] = _r(_pick(b4.get("max_dn1_15"), b4.get("max_up1_15"), d), 2)
    out["adv_bars15"] = _pick(b4.get("n_dn15"), b4.get("n_up15"), d)


def _p_cross(out, ctx, d, o, book, b, b4, sp, t):
    # 81 sister divergence
    if b.get("bn60") is not None and b.get("nifty60") is not None:
        out["bn_minus_nifty60"] = _r((b["bn60"] - b["nifty60"]) * d, 3)
    if b4.get("bn300") is not None and b4.get("nifty300") is not None:
        out["bn_minus_nifty300"] = _r((b4["bn300"] - b4["nifty300"]) * d, 3)
    out["bn_corr30"] = _r(b4.get("bn_corr30"), 3)
    # 82 the VIX path
    out["vix_day_pos"] = _r(b4.get("vix_day_pos"), 3)
    vc, mv = b.get("vix_chg5"), b.get("mv300")
    out["vix_spot_same5"] = bool((vc > 0) == (mv > 0)) if vc and mv else None
    # 83 breadth at other horizons
    for name, key in (("breadth60_dir", "b60"), ("breadth900_dir", "b900")):
        v = b4.get(key)
        out[name] = _r(_pick(v[0], v[1], d)) if v else None
    now_, prev = b4.get("b300"), b4.get("b300_prev")
    if now_ and now_[0] is not None:
        out["breadth_net"] = _r((now_[0] - now_[1]) * d)
        if prev and prev[0] is not None:
            out["breadth_chg5"] = _r(_pick(now_[0] - prev[0], now_[1] - prev[1], d))
    # 84 dispersion and concentration
    out["hw_disp300"], out["hw_top3_share"] = _r(b4.get("hw_disp300"), 4), _r(b4.get("hw_top3_share"), 3)
    out["hw_n_with"] = _pick(b4.get("hw_n_up"), b4.get("hw_n_dn"), d)
    out["hw_at_ext30"] = _r(_pick(b4.get("hw_at_hi30"), b4.get("hw_at_lo30"), d), 3)
    # 85 the leaders (the three heaviest stocks)
    out["lead1_move60"], out["lead1_move300"] = _sg(b4.get("lead1_60"), d, 3), _sg(b4.get("lead1_300"), d, 3)
    out["lead3_agree"] = _pick(b4.get("lead_up3"), b4.get("lead_dn3"), d)


def _hat(hist, t, lag, idx):
    """The history record at or before t - lag (at most TOL_S older), field idx; None if missing."""
    tgt = t - lag
    for rec in reversed(hist):
        if rec[0] <= tgt:
            return rec[idx] if tgt - rec[0] <= TOL_S and len(rec) > idx else None
    return None


def _mid(o):
    bid, ask, ltp = _fin(o.get("bid")), _fin(o.get("ask")), _fin(o.get("ltp"))
    return (bid + ask) / 2 if bid and ask and ask >= bid else ltp


def _other_leg(ctx, o):
    if o.get("strike") is None or o.get("rr") not in ("CE", "PE"):
        return None
    key = f"NIFTY|OPT|{ctx.get('w0')}|{int(o['strike'])}|{'PE' if o['rr'] == 'CE' else 'CE'}"
    return (ctx.get("by_key") or {}).get(key)


def _p_option(out, ctx, d, o, book, b, b4, sp, t):
    F = _fin(ctx.get("fwd")) or _fin(ctx.get("fut"))
    K, mid = _fin(o.get("strike")), _mid(o)
    s = 1 if o.get("rr") == "CE" else -1 if o.get("rr") == "PE" else d
    dl, gm, th = _fin(o.get("delta")), _fin(o.get("gamma")), _fin(o.get("theta_min"))
    # 86 moneyness
    if F and K:
        mny = (F - K) * s
        out["moneyness_pts"], out["moneyness_pct"] = _r(mny, 2), _r(100.0 * mny / F, 3)
        if mid:
            intr = max(mny, 0.0)
            out["intrinsic"], out["extrinsic"] = _r(intr, 2), _r(mid - intr, 2)
            out["extrinsic_pct"] = _r(100.0 * (mid - intr) / mid, 2)
    # 87 gearing
    if F and mid and dl:
        out["gearing"] = _r(abs(dl) * F / mid, 2)
    if gm is not None and th:
        out["gamma_theta"] = _r(gm / abs(th), 5)
    if gm is not None and F:
        out["gamma_1pct"] = _r(gm * F / 100.0, 4)
    bid, ask = _fin(o.get("bid")), _fin(o.get("ask"))
    if bid and ask and ask >= bid and dl and abs(dl) > 0.05:
        out["spread_be_pts"] = _r((ask - bid) / abs(dl), 2)
    # 88 how much of the implied move is used
    so, sn = b4.get("strad_open"), b4.get("strad_now")
    out["strad_now"] = _r(sn, 2)
    out["strad_vs_open_pct"] = _r(100.0 * (sn / so - 1), 2) if sn and so else None
    if so:
        rn = b.get("range_now")
        out["range_vs_strad"] = _r(rn / so, 3) if rn is not None else None
        if sp is not None and b4.get("first") is not None:
            out["day_move_vs_strad"] = _r((sp - b4["first"]) * d / so, 3)
    # 89 the opposite leg, 90 the premium's own path (16 minutes of 1-Hz history per contract)
    oh = ctx.get("ohist") or {}
    hist = oh.get(o.get("id")) if o.get("id") is not None else None
    own1 = None
    if hist and t is not None and mid:
        m60, m300, m900 = _hat(hist, t, 60, 3), _hat(hist, t, 300, 3), _hat(hist, t, 900, 3)
        own1 = mid - m60 if m60 else None
        out["prem_chg5_pct"] = _r(100.0 * (mid / m300 - 1), 2) if m300 else None
        out["prem_chg15_pct"] = _r(100.0 * (mid / m900 - 1), 2) if m900 else None
        xs = [rec[3] for rec in hist if t - 900 <= rec[0] <= t and rec[3]]
        if m900 and len(xs) >= 450:
            hi, lo = max(max(xs), mid), min(min(xs), mid)
            out["prem_pos15"] = _r((mid - lo) / (hi - lo)) if hi > lo else None
            out["prem_off_hi15_pct"] = _r(100.0 * (hi - mid) / hi, 2)
        x10 = [_hat(hist, t, 10 * j, 3) for j in range(31)]
        if all(x10):
            out["prem_rv5"] = _r(100.0 * float(np.std(np.diff(np.log(x10)))), 3)
    oth = _other_leg(ctx, o)
    if oth and t is not None:
        ohh, omid = oh.get(oth.get("id")), _mid(oth)
        if ohh and omid:
            o60, o300, oiv60 = _hat(ohh, t, 60, 3), _hat(ohh, t, 300, 3), _hat(ohh, t, 60, 1)
            out["opp_prem_chg1_pct"] = _r(100.0 * (omid / o60 - 1), 2) if o60 else None
            out["opp_prem_chg5_pct"] = _r(100.0 * (omid / o300 - 1), 2) if o300 else None
            out["opp_iv_chg1"] = _r(oth["iv"] - oiv60, 2) if oth.get("iv") and oiv60 else None
            out["pair_chg1"] = _r(own1 + (omid - o60), 2) if own1 is not None and o60 else None   # + = both legs bid
    # 92 the IV path
    out["atm_iv_day_pos"], out["iv_spot_corr15"] = _r(b4.get("atm_iv_day_pos"), 3), _r(b4.get("iv_spot_corr15"), 3)
    out["opt_iv_vs_atm"] = _r(o["iv"] - b["atm_iv_now"], 2) if o.get("iv") and b.get("atm_iv_now") else None


def _p_chain(out, ctx, d, o, book, b, b4, sp, t):
    m, fid, own = ctx.get("_m"), ctx.get("fut_id"), o.get("id")
    snap = getattr(m, "snap", None) if m is not None else None
    # 91 entry liquidity: the rupees resting against an all-in buyer
    if snap is not None and own is not None:
        ask, aq = _fin(snap["ask"][own]), _fin(snap["aqty"][own])
        if ask and aq is not None and ask > 0:
            out["opt_ask_rs"] = _r(ask * max(aq, 0.0), 0)
        side = {}
        for name, px, qty in (("ask", "apx", "aq"), ("bid", "bpx", "bq")):
            lp, lq = np.asarray(snap[px][own], float), np.asarray(snap[qty][own], float)
            ok = np.isfinite(lp) & np.isfinite(lq) & (lp > 0) & (lq > 0)
            side[name] = float(np.sum(lp[ok] * lq[ok])) if ok.any() else None
        out["opt_ask5_rs"], out["opt_bid5_rs"] = _r(side["ask"], 0), _r(side["bid"], 0)
        out["opt_depth_ratio"] = _r(side["bid"] / side["ask"], 3) if side["bid"] and side["ask"] else None
        # 94 own-strike OI
        oi, tq = _fin(snap["oi"][own]), _fin(snap["ttq"][own])
        if oi and oi > 0:
            out["own_oi"] = _r(oi, 0)
            out["own_vol_oi"] = _r(tq / oi, 3) if tq is not None and tq >= 0 else None
            band = [_fin(snap["oi"][i]) for i, rr in ctx.get("hero_ids") or () if rr == o.get("rr")]
            tot = sum(x for x in band if x and x > 0)
            out["own_oi_share"] = _r(oi / tot, 4) if tot > 0 else None
            oth = _other_leg(ctx, o)
            ooi = _fin(snap["oi"][oth["id"]]) if oth and oth.get("id") is not None else None
            out["own_vs_opp_oi"] = _r(oi / ooi, 3) if ooi and ooi > 0 else None
    # 93 the wings: put IV 100 below spot minus call IV 100 above; their mean against the ATM
    if sp is not None:
        rows = [x for x in ctx.get("options") or () if x.get("week", 0) == 0 and x.get("iv")]
        pv = min((x for x in rows if x.get("rr") == "PE"), key=lambda x: abs(x["strike"] - (sp - 100)), default=None)
        cv = min((x for x in rows if x.get("rr") == "CE"), key=lambda x: abs(x["strike"] - (sp + 100)), default=None)
        if pv and cv and abs(pv["strike"] - (sp - 100)) <= 30 and abs(cv["strike"] - (sp + 100)) <= 30:
            out["rr100"] = _r(pv["iv"] - cv["iv"], 3)
            ce0, pe0 = _atm_iv(rows, sp, 0)
            if ce0 is not None and pe0 is not None:
                out["fly100"] = _r((pv["iv"] + cv["iv"]) / 2 - (ce0 + pe0) / 2, 3)
    # 95 futures OI build-up (price and OI together over 5 minutes)
    ohist = ctx.get("oi_hist")
    if ohist and fid is not None and t is not None:
        cur = next((dct for ts_, dct in reversed(ohist) if ts_ <= t), None)
        for lag, name in ((300, "5"), (1800, "30")):
            past = None
            for ts_, dct in ohist:
                if ts_ <= t - lag:
                    past = dct
                else:
                    break
            if cur and past and fid in cur and fid in past:
                out[f"fut_oi_chg{name}"] = _r(cur[fid] - past[fid], 0)
        doi, dp = out.get("fut_oi_chg5"), b.get("fmv300")
        if doi and dp:
            out["fut_buildup"] = ("LONG-BUILD" if doi > 0 else "SHORT-COVER") if dp > 0 else \
                ("SHORT-BUILD" if doi > 0 else "LONG-UNWIND")
            out["fut_buildup_with"] = bool(doi > 0 and dp * d > 0)          # fresh positions in our direction


def _p_flow(out, ctx, d, o, book, b, b4, sp, t):
    # 96 volume acceleration
    out["fut_vol_accel"], out["hw_vol_accel"] = _r(b4.get("fut_ttq_accel"), 3), _r(b4.get("hw_ttq_accel"), 3)
    out["band_vol_accel"], out["fut_vol300"] = _r(b4.get("band_vol_accel"), 3), _r(b4.get("fut_vol300"), 0)
    # 97 up-volume share (futures volume in the seconds the forward moved our way)
    for lag in (60, 300):
        v = b4.get(f"upvol{lag}")
        out[f"with_vol_share{lag}"] = _r(v if d > 0 else 1.0 - v, 3) if v is not None else None
    # 98 the VWAP stretch
    out["vwap_z"], out["vwap_cross_n"] = _sg(b4.get("vwap_z"), d, 2), b4.get("vwap_cross_n")
    out["vwap_stretch_share"] = _r(b4.get("vwap_stretch_share"), 3)
    # 99 the call/put flow tilt over the last minute, and against the last five
    ce, pe = b4.get("ce_vol60"), b4.get("pe_vol60")
    if ce is not None and pe is not None and ce + pe > 0:
        tilt = (ce if d > 0 else pe) / (ce + pe)
        out["cp_vol_tilt60"] = _r(tilt, 3)
        c5, p5 = b.get("ce_vol300"), b.get("pe_vol300")
        if c5 is not None and p5 is not None and c5 + p5 > 0:
            out["cp_vol_tilt_chg"] = _r(tilt - (c5 if d > 0 else p5) / (c5 + p5), 3)


def _side_of(key):
    s = str(key or "").rsplit("|", 1)[-1]
    return s if s in ("CE", "PE") else None


def _p_books(out, ctx, d, o, book, b, b4, sp, t):
    side = "CE" if d > 0 else "PE"
    books = ctx.get("_books")
    if books:
        me = getattr(book, "name", None)
        fam = str(me).split("_")[0] if me else None
        by_key = ctx.get("by_key") or {}
        hs = ho = win = fn = fbusy = 0
        closed = []
        for name, bk in books.items():
            if name == me:
                continue
            bp, mp = (getattr(bk, "p", None) or {}), (getattr(book, "p", None) or {})
            if (bp.get("gen") or bp.get("twin")) and not (mp.get("gen") or mp.get("twin")):
                continue          # 9 Nov (docs/37): the second-generation books are not among "the books around" an
                                  # older book, so items 100-101 keep the meaning they had when the rules were frozen
            in_fam = fam is not None and str(name).split("_")[0] == fam
            fn += 1 if in_fam else 0
            p = getattr(bk, "pos", None)
            if p:
                fbusy += 1 if in_fam else 0
                ps = _side_of(p.get("key"))
                if ps == side:
                    hs += 1
                    cur = _mid(by_key.get(p.get("key")) or {})
                    win += 1 if cur and p.get("entry") and cur > float(p["entry"]) else 0
                elif ps:
                    ho += 1
            for tr in getattr(bk, "trades", None) or ():
                if tr.get("pnl_rs") is not None and tr.get("t_out") is not None:
                    closed.append(tr)
        # 100 other books' positions; the family's busy and free members (docs/35 §7: an absent vote is not a veto)
        out["held_same"], out["held_other"] = hs, ho
        out["held_same_winning"] = _r(win / hs, 3) if hs else None
        out["fam_n"], out["fam_busy"], out["fam_free"] = fn, fbusy, fn - fbusy
        # 101 other books' results today
        out["all_n_today"] = len(closed)
        out["all_win_today"] = _r(sum(1 for x in closed if x["pnl_rs"] > 0) / len(closed), 3) if closed else None
        same = sorted((x for x in closed if (x.get("rr") or _side_of(x.get("key"))) == side), key=lambda x: x["t_out"])
        if same and t is not None:
            out["all_last_same_s"] = _r(t - same[-1]["t_out"], 1)
            out["all_last_same_won"] = bool(same[-1]["pnl_rs"] > 0)
            out["all_last5_same_win"] = sum(1 for x in same[-5:] if x["pnl_rs"] > 0) if len(same) >= 5 else None
    # 102 trigger density: seconds with a trigger (any book, taken or not) before this one
    W = ctx.get("_wx")
    if W is not None and t is not None:
        log = getattr(W, "fire_log", None)
        if log is None:
            log = W.fire_log = []
        sec = int(t)
        seen = [(s_, d_) for s_, d_ in log if s_ < sec]
        for lag, name in ((300, "5"), (1800, "30")):
            out[f"fires{name}_same"] = len({s_ for s_, d_ in seen if d_ == d and sec - s_ <= lag})
            out[f"fires{name}_other"] = len({s_ for s_, d_ in seen if d_ == -d and sec - s_ <= lag})
        last15 = [d_ for s_, d_ in seen if sec - s_ <= 900]
        out["flip_n15"] = sum(1 for k in range(1, len(last15)) if last15[k] != last15[k - 1])
        opp = [s_ for s_, d_ in seen if d_ == -d]
        out["last_fire_other_s"] = sec - opp[-1] if opp else None
        if (sec, d) not in log[-200:]:
            log.append((sec, d))


def _p_own(out, ctx, d, o, book, b, b4, sp, t):
    if book is None:
        return
    side = "CE" if d > 0 else "PE"
    trades = [x for x in (getattr(book, "trades", None) or []) if x.get("pnl_rs") is not None]
    # 103 re-entry context
    out["n_same_side_today"] = sum(1 for x in trades if x.get("rr") == side)
    losses = [x for x in trades if x["pnl_rs"] <= 0]
    out["n_losses_today"] = len(losses)
    if losses and t is not None and losses[-1].get("t_out") is not None:
        out["since_last_loss_s"] = _r(t - losses[-1]["t_out"], 1)
    if trades:
        last = trades[-1]
        out["last_ret_pct"] = _r(_fin(last.get("ret_pct")), 3)
        out["last_peak_pts"] = _r(_fin(last.get("peak_pts")), 2)
        if last.get("t_in") is not None and last.get("t_out") is not None:
            out["last_hold_s"] = _r(last["t_out"] - last["t_in"], 1)
        same = bool(o.get("key")) and last.get("key") == o.get("key")
        out["same_key_as_last"] = same if o.get("key") else None
        px = _fin(o.get("ask")) or _fin(o.get("ltp"))
        if same and px:
            ex, en = _fin(last.get("exit")), _fin(last.get("entry"))
            out["prem_vs_last_exit_pct"] = _r(100.0 * (px / ex - 1), 2) if ex else None
            out["prem_vs_last_entry_pct"] = _r(100.0 * (px / en - 1), 2) if en else None
    # 104 the day's P&L shape
    rets = [_fin(x.get("ret_pct")) or 0.0 for x in trades]
    if rets:
        out["best_today"], out["worst_today"] = _r(max(rets), 3), _r(min(rets), 3)
        out["ret_last3"] = _r(sum(rets[-3:]), 3)
        out["win_share_today"] = _r(sum(1 for x in trades if x["pnl_rs"] > 0) / len(trades), 3)
        cum = np.cumsum(rets)
        out["dd_today"] = _r(float(cum[-1] - max(0.0, float(cum.max()))), 3)        # below the day's high-water mark
    else:
        out["dd_today"] = 0.0
