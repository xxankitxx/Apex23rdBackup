"""D-136 (owner, 21 Oct 19:53, after four external reviews: "make the code a masterpiece in anticipating edges"; council 8):
the EDGE SNAPSHOT — the data the feed captures, condensed once a second into a handful of numbers that every entry, every
trade and the decision tape carry. Nothing here decides a trade (council 8: no data veto passed on the two tapes); it is
the evidence base the evening report ranks, so that a feature that starts to separate winners from losers on new days is
seen — and can then be pre-registered as a gate.

Features (all from data available at that second; None when not available):
  basis_dev   future mid - spot - its 30-min median spread (D-132 reference)  — positioning in the future vs the index
  iv_atm      ATM implied vol (%)                 iv_chg5   ATM IV change over 5 min (vol pts)
  rv15        realised vol of spot over 15 min, annualised (%)   iv_rv  iv_atm / rv15 (rich > 1, cheap < 1)
  fut_imb5    5-level book imbalance of the Nifty future, (bid qty - ask qty) / total, -1..+1
  fut_tot_imb whole-book imbalance (total buy qty - total sell qty) / total
  wall_up / wall_dn   distance (pts) to the nearest CE / PE OI wall above / below spot
  pcr         put-call ratio of OI           imp_rng / imp_d / imp_f   45-min impulse size, direction, pullback fraction
  fut_ofi60   Cont–Kukanov–Stoikov order-flow imbalance of the future's top of book over 60 s, in units of the average
              displayed top-of-book size (net queue change, not static depth — harder to spoof)        (review: Gemini)
  syn_dev     the options-implied (put-call parity) forward minus spot, minus its slow average: a sweep through the
              options book shows here before the index moves                                             (review: Gemini)
  fut_micro   the future's micro-price (size-weighted) minus its mid, in points                          (review: Gemini)
"""
import json
import math
import os

import numpy as np

KEYS = ("basis_dev", "iv_atm", "iv_chg5", "rv15", "iv_rv", "fut_imb5", "fut_tot_imb", "wall_up", "wall_dn", "pcr",
        "imp_rng", "imp_d", "imp_f", "fut_ofi60", "syn_dev", "fut_micro")


def _r(x, n=3):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, n) if math.isfinite(x) else None


def snapshot(eng, snap, spot, fut):
    """One dict per second. Never raises (the caller wraps it too)."""
    out = dict.fromkeys(KEYS)
    sp = float(spot) if spot is not None and np.isfinite(spot) and not getattr(eng, "_spot_bad", "") else None
    fid = getattr(eng, "fut_id", None)
    fmid = None
    if fid is not None:
        b, a = float(snap["bid"][fid]), float(snap["ask"][fid])
        fmid = (a + b) / 2 if (b > 0 and a >= b and a - b <= 30) else (float(fut) if fut is not None and np.isfinite(fut) else None)
        bq, aq = float(np.sum(snap["bq"][fid])), float(np.sum(snap["aq"][fid]))
        if bq + aq > 0:
            out["fut_imb5"] = _r((bq - aq) / (bq + aq))
        _ofi(eng, out, snap, fid)
        tb, ts = float(snap["tbq"][fid]), float(snap["tsq"][fid])
        if tb + ts > 0:
            out["fut_tot_imb"] = _r((tb - ts) / (tb + ts))
    if sp is not None and fmid is not None:
        ref = getattr(eng, "_basis_ref", None)
        if ref is not None:
            out["basis_dev"] = _r(fmid - sp - ref, 2)
    F = getattr(eng, "fwd", None)
    if sp is not None and F is not None and np.isfinite(F):
        b = float(F) - sp
        st = eng.__dict__.setdefault("_syn_state", {"ewma": None})
        if st["ewma"] is None or abs(b - st["ewma"]) > 150:      # first reading, or a re-centred chain
            st["ewma"] = b
        out["syn_dev"] = _r(b - st["ewma"], 2)
        st["ewma"] = 0.98 * st["ewma"] + 0.02 * b                   # ~50-s memory at 1 Hz
    iv = getattr(eng, "atm_iv", None)
    if iv:
        out["iv_atm"] = _r(iv * 100, 2)
        out["iv_chg5"] = _r(eng.iv_change(300), 2)
    imp = getattr(eng, "impulse", None)
    if imp is not None and len(imp.samples) > 60:
        xs = [p for t, p in imp.samples if t >= imp.samples[-1][0] - 900]
        if len(xs) > 300:
            r = np.diff(np.log(np.asarray(xs, dtype=float)))
            rv = float(np.std(r)) * math.sqrt(252 * 22500) * 100
            if rv > 0:
                out["rv15"] = _r(rv, 2)
                if out["iv_atm"]:
                    out["iv_rv"] = _r(out["iv_atm"] / rv, 2)
    pv = getattr(eng, "_pb_view", None) or {}
    if pv.get("ok") and sp is not None and pv.get("rng"):
        out["imp_rng"] = _r(pv["rng"], 1)
        out["imp_d"] = pv.get("d")
        if pv.get("d"):
            ext = pv["hi"] if pv["d"] > 0 else pv["lo"]
            out["imp_f"] = _r((ext - sp) * pv["d"] / pv["rng"])
    pr = getattr(eng, "pressure", None)
    if pr is not None and sp is not None:
        try:
            up, dn = pr.destination(sp, 1), pr.destination(sp, -1)
            out["wall_up"] = _r(up["room"], 1) if up else None
            out["wall_dn"] = _r(dn["room"], 1) if dn else None
            out["pcr"] = _r(pr.pcr)
        except Exception:
            pass
    return out


def _ofi(eng, out, snap, fid):
    """Cont OFI at 1 Hz on the future's top of book (bid, ask, bid qty, ask qty), summed over 60 s and scaled by the average
    displayed size; and the micro-price offset. State lives on the engine (eng._ofi_state)."""
    bid, ask = float(snap["bid"][fid]), float(snap["ask"][fid])
    bq, aq = float(snap["bqty"][fid]), float(snap["aqty"][fid])
    if not (bid > 0 and ask >= bid and bq >= 0 and aq >= 0 and np.isfinite(bq) and np.isfinite(aq)):
        return
    if bq + aq > 0:
        out["fut_micro"] = _r((bid * aq + ask * bq) / (bq + aq) - (bid + ask) / 2, 2)
    st = eng.__dict__.setdefault("_ofi_state", {"prev": None, "hist": []})
    p = st["prev"]
    if p is not None:
        pb, pa, pbq, paq = p
        e_b = bq if bid > pb else (bq - pbq if bid == pb else -pbq)
        e_a = aq if ask < pa else (aq - paq if ask == pa else -paq)
        st["hist"].append((e_b - e_a, (bq + aq) / 2))
        if len(st["hist"]) > 60:
            del st["hist"][:-60]
        if len(st["hist"]) >= 20:
            depth = sum(h[1] for h in st["hist"]) / len(st["hist"])
            if depth > 0:
                out["fut_ofi60"] = _r(sum(h[0] for h in st["hist"]) / depth, 2)
    st["prev"] = (bid, ask, bq, aq)


def signed(edge, d):
    """The snapshot in the trade's direction (positive = with the trade) for the features that have a sign."""
    if not edge:
        return {}
    e = dict(edge)
    for k in ("basis_dev", "fut_imb5", "fut_tot_imb", "fut_ofi60", "syn_dev", "fut_micro"):
        if e.get(k) is not None:
            e[k] = round(e[k] * d, 3)
    if e.get("imp_d") is not None:
        e["imp_with"] = 1 if e["imp_d"] == d else (-1 if e["imp_d"] else 0)
    e["wall_room"] = e.get("wall_up") if d > 0 else e.get("wall_dn")
    return e


def report_lines(paper_dir, min_trades=12):
    """Evening report section: every book's trades on every recorded day that carry an edge snapshot; per feature, the
    median for winners vs losers and the Spearman correlation with the trade's return. Evidence only."""
    rows = []
    try:
        for f in sorted(os.listdir(paper_dir)):
            if not (f.endswith(".json") and f[:4].isdigit() and len(f) == 15):
                continue
            try:
                books = json.load(open(os.path.join(paper_dir, f), encoding="utf-8"))
            except Exception:
                continue
            for name, b in (books or {}).items():
                for t in (b or {}).get("trades", []) if isinstance(b, dict) else []:
                    e = t.get("edge_in")
                    if e and t.get("ret_pct") is not None:
                        rows.append((name, f[:10], float(t["ret_pct"]), e))
    except Exception:
        return []
    out = ["", "## Edge features at entry (D-136: evidence only, nothing here gates a trade)", ""]
    if len(rows) < min_trades:
        out.append(f"{len(rows)} trades carry an edge snapshot so far; the table starts at {min_trades}.")
        return out
    days = sorted({r[1] for r in rows})
    out.append(f"{len(rows)} trades over {len(days)} day(s), all books. Signed features: positive = with the trade.")
    out += ["", "| feature | n | winners median | losers median | Spearman vs return |", "|---|---|---|---|---|"]
    keys = list(KEYS) + ["imp_with", "wall_room"]
    for k in keys:
        pts = [(r[2], r[3].get(k)) for r in rows if r[3].get(k) is not None]
        if len(pts) < min_trades:
            continue
        ret = np.array([p[0] for p in pts]); x = np.array([float(p[1]) for p in pts])
        w, l = x[ret > 0], x[ret <= 0]
        rho = None
        if np.std(x) > 0 and np.std(ret) > 0:
            rx = np.argsort(np.argsort(x)); rr = np.argsort(np.argsort(ret))
            rho = float(np.corrcoef(rx, rr)[0, 1])
        fmt = lambda v: f"{v:.3g}" if v is not None and np.isfinite(v) else "—"   # noqa: E731
        out.append(f"| {k} | {len(pts)} | {fmt(np.median(w)) if len(w) else '—'} | {fmt(np.median(l)) if len(l) else '—'} | "
                   f"{fmt(rho)} |")
    out += ["", "A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, "
            "including an up day (council 8 bar)."]
    return out
