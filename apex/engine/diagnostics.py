"""
Diagnostics (D-070/D-071) — the learning report's evidence sections, from the candidate ledger
and the trade records:

  * Candidates: how often a candidate reached +1R before -1R ("hit rate"), with a Wilson 95 %
    interval, overall and split by regime, by the champion's decision (taken / rejected), by the
    rejection reason, by impulse size, by each advisor's verdict — so we can see whether a filter
    removes bad candidates or good ones, and whether an advisor's veto actually separates them.
  * Trades by regime: the champion's and RAW's trades, mean return and win rate per regime.

Descriptive only: no model is fitted until there are enough candidates (a few hundred) for an
out-of-sample test. These rates ARE the baseline any later model must beat.
"""
import glob
import json
import math
import os
from collections import defaultdict

from .. import config


def wilson(k, n, z=1.96):
    if n == 0:
        return None, None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def load_candidates(since=None):
    out = []
    for path in sorted(glob.glob(os.path.join(config.PAPER_DIR, "candidates_*.jsonl"))):
        day = os.path.basename(path)[len("candidates_"):-len(".jsonl")]
        if since and day < since:
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    return out


def reason_class(r):
    """Group the champion's free-text reason into a small set of categories."""
    if r.get("fired"):
        return "TAKEN"
    x = (r.get("decision_at_cross") or "").lower()
    if x.startswith("gate ") and not x.startswith("gate regime"):
        return "gate"
    for key, name in (("daily stop", "daily stop"), ("pause:", "loss pause"), ("cool-down", "cool-down"),
                      ("gate regime", "regime says no"), ("pt floor", "impulse too small"), ("trend:", "against trend"),
                      ("inside its", "spot inside range"), ("same swing", "same swing"), ("spot range warming", "spot range warming"),
                      ("spot quote", "spot stale"), ("kill switch", "kill switch"), ("expiry day", "expiry window"),
                      ("began in a data gap", "episode born in gap"), ("data gap", "data gap"), ("synchrony", "basket too thin"),
                      ("late", "late"), ("in position", "already in a trade"),
                      ("outside entry window", "outside window"), ("already traded", "episode used"),
                      ("impulse", "impulse faded"), ("no episode", "episode ended"), ("basket gap", "gap too small")):
        if key in x:
            return name
    return "other"


def _row(name, rs):
    res = [r for r in rs if r.get("label") in ("TARGET", "STOP") or (r.get("label") == "NEITHER" and not r.get("truncated"))]
    n = len(res)
    k = sum(1 for r in res if r["label"] == "TARGET")
    lo, hi = wilson(k, n)
    o5 = [r["opt_ret"].get("300") for r in res if r.get("opt_ret") and r["opt_ret"].get("300") is not None]
    m5 = sum(o5) / len(o5) if o5 else None
    ci = f"{lo:.0%}–{hi:.0%}" if lo is not None else "—"
    return (f"| {name} | {n} | {k / n:.0%} | {ci} | " if n else f"| {name} | 0 | — | — | ") + \
        (f"{m5:+.1f} |" if m5 is not None else "— |")


def _opt_defect(r):
    """D-101: the would-be contract's start price was not a live quote (exchange stamp too old), or a
    follow sample was — its option returns are not evidence (the futures label still is)."""
    a = r.get("opt_age0")
    return bool(r.get("opt_defect")) or (a is not None and a > getattr(config, "QUOTE_DEFECT_AGE_S", 600.0))


def candidate_lines(since=None, quarantine=None):
    cs = load_candidates(since)
    nq = 0
    if quarantine is not None:                # D-101: candidates inside a feed-defect window are quarantined
        keep = [r for r in cs if not quarantine.in_window(r.get("day"), r.get("time"))]
        nq, cs = len(cs) - len(keep), keep
    for r in cs:
        if _opt_defect(r):
            r["opt_ret"], r["opt_best"], r["opt_worst"] = {}, None, None
    lines = ["", "## Candidates (every impulse that reached the champion's m*, taken or not)", "",
             "Hit = futures reached +1R (the champion's d*) before −1R within 15 min. "
             "Option +5m = the would-be contract's return on premium 5 min later, mean.", ""]
    if nq:
        lines += [f"{nq} candidate(s) inside a feed-defect window are quarantined (D-101) and not counted below.", ""]
    if not cs:
        return lines + ["No candidates recorded yet.", ""]
    hdr = ["| group | resolved | hit rate | 95 % interval | option +5m % |", "|---|---|---|---|---|"]
    lines += ["### Overall and by decision", ""] + hdr + [_row("all candidates", cs)]
    by = defaultdict(list)
    for r in cs:
        by[reason_class(r)].append(r)
    for k in sorted(by, key=lambda k: (k != "TAKEN", k)):
        lines.append(_row(("taken" if k == "TAKEN" else f"rejected: {k}"), by[k]))
    lines += ["", "### By regime at the candidate moment", ""] + hdr
    byr = defaultdict(list)
    for r in cs:
        byr[r.get("regime") or "?"].append(r)
    for k in sorted(byr):
        lines.append(_row(k, byr[k]))
    lines += ["", "### By impulse size (z at the crossing)", ""] + hdr
    for lo, hi in ((0, 2.5), (2.5, 3.5), (3.5, 99)):
        lines.append(_row(f"z {lo}–{hi if hi < 99 else '∞'}", [r for r in cs if r.get("z") is not None and lo <= r["z"] < hi]))
    lines += ["", "### Does each advisor's veto separate good candidates from bad?", "",
              "| advisor | vetoed: resolved | vetoed hit rate | passed: resolved | passed hit rate |", "|---|---|---|---|---|"]
    names = sorted({a for r in cs for a in (r.get("advisors") or {})})
    for a in names:
        def hr(rs):
            res = [r for r in rs if r.get("label") in ("TARGET", "STOP") or (r.get("label") == "NEITHER" and not r.get("truncated"))]
            return len(res), (sum(1 for r in res if r["label"] == "TARGET") / len(res) if res else None)
        nv, hv = hr([r for r in cs if (r.get("advisors") or {}).get(a)])
        npass, hp = hr([r for r in cs if not (r.get("advisors") or {}).get(a)])
        f = lambda x: f"{x:.0%}" if x is not None else "—"
        lines.append(f"| {a} | {nv} | {f(hv)} | {npass} | {f(hp)} |")
    return lines + [""]


def regime_trade_lines(days, books, unit):
    """days = learning._load_days(); unit = learning._r."""
    lines = ["", "## Trades by regime at entry", "", "| book | regime | trades | mean return % | win rate |", "|---|---|---|---|---|"]
    any_row = False
    for b in books:
        agg = defaultdict(list)
        for d, tr in days.get(b, {}).items():
            for t in tr:
                agg[t.get("regime") or "?"].append(unit(t))
        for reg in sorted(agg):
            x = agg[reg]
            lines.append(f"| {b} | {reg} | {len(x)} | {sum(x) / len(x):+.2f} | {sum(1 for v in x if v > 0) / len(x):.0%} |")
            any_row = True
    if not any_row:
        lines.append("| — | — | 0 | — | — |")
    return lines + [""]
