"""Fixed-contract targets (docs/40 section 3, docs/41 section 2). The contract chosen at the forecast is kept for the
whole label: never the new at-the-money strike half way. Quote-aware: the fill is the ASK seen `delay` seconds after
the request (a quote received after the request), every later mark is the BID.

Competing events inside each horizon: 'T' the bid reaches the profit barrier first, 'A' the bid reaches the adverse
barrier first, 'N' neither by the horizon, 'U' unobservable (the bid was missing for more than MAX_GAP_S seconds, or
the data ended, before any event). 'L' = no fill at all (lapse). A gap is neither a stop nor a win."""
import numpy as np

DELAY_S = 1
BARRIER = 0.05                  # 5 % of the entry premium, both sides. Declared before any result was seen.
HORIZONS = (30, 60, 180, 300)   # seconds after the fill
MAX_GAP_S = 10
SPEC = dict(delay_s=DELAY_S, barrier=BARRIER, horizons=list(HORIZONS), max_gap_s=MAX_GAP_S, entry="ask", mark="bid")


def label(t, bid, ask, ok, age, i, delay=DELAY_S, barrier=BARRIER, horizons=HORIZONS, max_gap=MAX_GAP_S):
    """One contract over one recorded part: t (seconds), bid, ask, ok, age all shaped (n,). Request at row i.
    Returns dict(st='L') or dict(st='ok', entry, first={h: 'T'|'A'|'N'|'U'}, ret={h: bid/entry-1 or None},
    t_hit seconds to the first event or None, peak, trough over the longest horizon)."""
    n = len(t)
    a = i + delay
    if a >= n or t[a] - t[i] != delay or not ok[a] or age[a] > delay:
        return dict(st="L")
    e = float(ask[a])
    end = int(np.searchsorted(t, t[a] + max(horizons), side="right"))     # by time, not by row count
    tt = t[a + 1:end] - t[a]
    seen = ok[a + 1:end].astype(bool)
    bb = np.where(seen, bid[a + 1:end], np.nan)
    ts = tt[seen]
    # the first moment after which more than max_gap seconds pass with no usable bid ("blind from")
    edges = np.r_[0.0, ts, (t[end - 1] - t[a]) if end - 1 > a else 0.0]
    gaps = np.where(np.diff(edges) > max_gap)[0]
    blind = float(edges[gaps[0]]) if len(gaps) else np.inf
    data_end = float(edges[-1])
    with np.errstate(invalid="ignore"):
        hT = np.where(bb >= e * (1 + barrier))[0]
        hA = np.where(bb <= e * (1 - barrier))[0]
    tT = tt[hT[0]] if len(hT) else np.inf
    tA = tt[hA[0]] if len(hA) else np.inf
    ev, tev = ("T", tT) if tT < tA else (("A", tA) if tA < np.inf else (None, np.inf))
    if tev > blind:                                   # whatever happened after an unobserved stretch is not counted
        ev, tev = None, np.inf
    out = dict(st="ok", entry=e, first={}, ret={}, t_hit=(float(tev) if ev else None), peak=None, trough=None)
    for h in horizons:
        if ev is not None and tev <= h:
            out["first"][h] = ev
        elif blind < h or data_end < h - max_gap:
            out["first"][h] = "U"
        else:
            out["first"][h] = "N"
        k = np.where(seen & (tt <= h) & (tt > h - max_gap))[0]
        out["ret"][h] = float(bb[k[-1]] / e - 1.0) if len(k) and blind >= h else None
    vis = bb[np.isfinite(bb) & (tt <= blind)]
    if len(vis):
        out["peak"], out["trough"] = float(vis.max() / e - 1.0), float(vis.min() / e - 1.0)
    return out


def policy_exit(t, bid, ok, a, entry, barrier=BARRIER, hold=max(HORIZONS), max_gap=MAX_GAP_S):
    """The frozen exit policy the forecast is about: sell at the bid when it first reaches +barrier or -barrier, else
    at the first usable bid `hold` seconds after the fill. (return, seconds held, 'T'|'A'|'H'), or None when the
    position cannot be followed (a gap over max_gap, or the data ends)."""
    last = t[a]
    for j in range(a + 1, len(t)):
        s = t[j] - t[a]
        if not ok[j]:
            if t[j] - last > max_gap:
                return None
            continue
        if t[j] - last > max_gap:
            return None
        last = t[j]
        r = bid[j] / entry - 1.0
        if r >= barrier:
            return float(r), float(s), "T"
        if r <= -barrier:
            return float(r), float(s), "A"
        if s >= hold:
            return float(r), float(s), "H"
    return None
