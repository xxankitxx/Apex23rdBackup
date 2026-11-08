"""
rule_lab — the team's shared toolkit (8 Nov 2026). READ-ONLY on D:/ApexOptions/data. Never run replays or pytest.

    import sys; sys.path.insert(0, r"C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/team")
    import rule_lab as rl
    T = rl.load_book("c20_9y")            # every trade of the book on the 14 replayed days, with its trigger photograph
    X, names, y = rl.matrix(T)            # numeric fields (+ derived features you add) as an array, winners = 1
    disc, hold = rl.split_days(T)         # discovery = first 10 trading days, holdout = last 4 (indices into T)

A RULE is a list of clauses [(feature, op, line), ...] AND-combined, op in (">=", "<"); a trade is KEPT when every clause
is true (a missing value fails the clause, as the engine does). Use rl.evaluate(T, rule) for the full card and
rl.shuffle_p(...) for the honesty test. The standard the owner's register demands before a rule is proposed:
  1. kept side profitable in mean and in rupees on the DISCOVERY days, with at least 20 kept trades there;
  2. the search that found it, re-run on >= 200 shufflings of the discovery outcomes, beats the real score in < 5 %
     of shufflings (rl.shuffle_p with the SAME search function you used);
  3. on the HOLDOUT days (never looked at while searching) the kept side's win rate is not below the book's own and
     the removed side is not profitable — report the holdout numbers whatever they say.
Derived features ("every kind of mathematics") are welcome: ratios, differences, products, z-scores within the day,
ranks, time-of-day buckets, interactions — rl.add_feature(T, name, fn) where fn(weather_dict, trade_dict) -> float|None.
Fitted-model fields (hmm_*, hk_*) are excluded from search (parameters fitted on 5 Nov over these very days).
"""
import glob
import json
import os
import random
import statistics as st
import sys

import numpy as np

sys.path.insert(0, "D:/ApexOptions")
from apex.conductor import diary  # noqa: E402

RUNS = sorted(glob.glob("D:/ApexOptions/data/replay/batch/v3_*"))
_DAYS = None
EXCLUDE_PREFIX = ("hmm_", "hk_")


def days():
    global _DAYS
    if _DAYS is None:
        _DAYS = {}
        for rd in RUNS:
            b, _ = diary.load_days(rd)
            _DAYS.update(b)
    return _DAYS


def books(min_trades=30):
    d = days()
    names = sorted({n for v in d.values() for n, x in v.items() if isinstance(x, dict) and "trades" in x})
    return [n for n in names if sum(len((d[dd].get(n) or {}).get("trades") or []) for dd in d) >= min_trades]


def load_book(book):
    """Trades of one book on all 14 days, each with: day, y (1 winner / 0 loser), ret_pct, pnl_rs, w (photograph),
    t (the full trade record), and _feat (derived features you add)."""
    out = []
    for dday in sorted(days()):
        for t in (days()[dday].get(book) or {}).get("trades") or []:
            if t.get("pnl_rs") is None or not t.get("weather_trig"):
                continue
            out.append({"day": dday, "y": 1 if t["pnl_rs"] > 0 else 0, "ret_pct": float(t.get("ret_pct") or 0.0),
                        "pnl_rs": float(t["pnl_rs"]), "w": t["weather_trig"], "t": t, "_feat": {}})
    return out


def add_feature(T, name, fn):
    """Derived feature: fn(weather_dict, trade_dict) -> number or None. Stored under T[i]['_feat'][name]."""
    for x in T:
        try:
            v = fn(x["w"], x["t"])
        except Exception:
            v = None
        if isinstance(v, bool):
            v = int(v)
        x["_feat"][name] = float(v) if isinstance(v, (int, float)) and np.isfinite(v) else None


def value(x, feature):
    v = x["_feat"].get(feature) if feature in x["_feat"] else x["w"].get(feature)
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, str) and "=" in feature:               # indicator "field=VALUE"
        pass
    if "=" in feature and feature not in x["_feat"]:
        f, val = feature.split("=", 1)
        return 1.0 if str(x["w"].get(f)) == val else 0.0
    return float(v) if isinstance(v, (int, float)) else None


def numeric_features(T, min_fill=0.8, min_distinct=4):
    names = set()
    for x in T:
        names.update(k for k, v in x["w"].items() if isinstance(v, (int, float)) and not isinstance(v, bool))
        names.update(x["_feat"].keys())
    out = []
    for f in sorted(names):
        if f.startswith(EXCLUDE_PREFIX):
            continue
        vs = [value(x, f) for x in T]
        vs = [v for v in vs if v is not None]
        if len(vs) >= min_fill * len(T) and len(set(vs)) >= min_distinct:
            out.append(f)
    return out


def text_features(T):
    names = sorted({k for x in T for k, v in x["w"].items() if isinstance(v, str)})
    out = []
    for f in names:
        vals = sorted({str(x["w"].get(f)) for x in T})
        if 2 <= len(vals) <= 8:
            out += [f"{f}={v}" for v in vals]
    return out


def matrix(T, features=None):
    features = features if features is not None else numeric_features(T)
    X = np.full((len(T), len(features)), np.nan)
    for i, x in enumerate(T):
        for j, f in enumerate(features):
            v = value(x, f)
            if v is not None:
                X[i, j] = v
    y = np.array([x["y"] for x in T], dtype=float)
    return X, features, y


def split_days(T, n_disc=10):
    ds = sorted({x["day"] for x in T})
    disc_days = set(sorted(days())[:n_disc])
    disc = [i for i, x in enumerate(T) if x["day"] in disc_days]
    hold = [i for i, x in enumerate(T) if x["day"] not in disc_days]
    return disc, hold


def keep_mask(T, rule):
    m = np.ones(len(T), dtype=bool)
    for f, op, line in rule:
        for i, x in enumerate(T):
            v = value(x, f)
            ok = v is not None and (v >= line if op == ">=" else v < line)
            m[i] &= ok
    return m


def side_stats(T, idx):
    idx = list(idx)
    n = len(idx)
    if n == 0:
        return {"n": 0, "win": None, "mean": None, "pnl": 0.0, "losers": 0}
    w = sum(T[i]["y"] for i in idx)
    return {"n": n, "win": w / n, "mean": sum(T[i]["ret_pct"] for i in idx) / n,
            "pnl": sum(T[i]["pnl_rs"] for i in idx), "losers": n - w}


def evaluate(T, rule, disc=None, hold=None):
    """The card of a rule: kept / removed on discovery and on holdout."""
    if disc is None or hold is None:
        disc, hold = split_days(T)
    m = keep_mask(T, rule)
    out = {"rule": rule}
    for nm, idx in (("discovery", disc), ("holdout", hold), ("all", range(len(T)))):
        idx = list(idx)
        kept = [i for i in idx if m[i]]
        removed = [i for i in idx if not m[i]]
        out[nm] = {"book": side_stats(T, idx), "kept": side_stats(T, kept), "removed": side_stats(T, removed)}
    return out


def score_masks(M, y, min_keep):
    """M: masks x trades (bool/float), y: winners. Score per mask = share of losers removed - share of winners removed."""
    M = M.astype(np.float32)
    kept = M.sum(1)
    kw = M @ y.astype(np.float32)
    kl = kept - kw
    tw, tl = y.sum(), len(y) - y.sum()
    sc = (tl - kl) / max(tl, 1) - (tw - kw) / max(tw, 1)
    sc[kept < min_keep] = -9
    return sc, kept, kw, kl


def single_masks(X, features, n_lines=5):
    """Every single clause at quantile lines, both directions. Returns (masks, clauses)."""
    masks, clauses = [], []
    for j, f in enumerate(features):
        col = X[:, j]
        v = col[~np.isnan(col)]
        if len(v) < 5:
            continue
        qs = sorted(set(np.quantile(v, np.linspace(0.1, 0.9, n_lines)).tolist()))
        for q in qs:
            ok = ~np.isnan(col)
            masks.append(ok & (col >= q)); clauses.append((f, ">=", float(q)))
            masks.append(ok & (col < q)); clauses.append((f, "<", float(q)))
    return np.array(masks, dtype=bool), clauses


def best_single(X, features, y, min_keep=20, n_lines=5):
    M, clauses = single_masks(X, features, n_lines)
    sc, kept, kw, kl = score_masks(M, y, min_keep)
    k = int(np.argmax(sc))
    return float(sc[k]), [clauses[k]], int(kept[k]), int(kw[k]), int(kl[k])


def best_pair(X, features, y, min_keep=20, n_lines=5, max_masks=2500):
    M, clauses = single_masks(X, features, n_lines)
    if len(clauses) > max_masks:                           # keep the strongest singles, then pair them
        sc1, *_ = score_masks(M, y, min_keep)
        top = np.argsort(-sc1)[:max_masks]
        M, clauses = M[top], [clauses[i] for i in top]
    Mf = M.astype(np.float32)
    kept = Mf @ Mf.T
    kw = (Mf * y.astype(np.float32)) @ Mf.T
    kl = kept - kw
    tw, tl = y.sum(), len(y) - y.sum()
    sc = (tl - kl) / max(tl, 1) - (tw - kw) / max(tw, 1)
    sc[kept < min_keep] = -9
    fld = np.array([c[0] for c in clauses])
    sc[fld[:, None] == fld[None, :]] = -9
    k = int(np.argmax(sc)); a, b = divmod(k, sc.shape[1])
    return float(sc[a, b]), [clauses[a], clauses[b]], int(kept[a, b]), int(kw[a, b]), int(kl[a, b])


def shuffle_p(search_fn, X, features, y, real_score, n=200, seed=7, **kw):
    """Re-run the SAME search on n shufflings of y; returns (p, median_best, max_best)."""
    rng = np.random.default_rng(seed)
    best = []
    for _ in range(n):
        yy = y.copy(); rng.shuffle(yy)
        best.append(search_fn(X, features, yy, **kw)[0])
    better = sum(1 for b in best if b >= real_score)
    return better / n, float(np.median(best)), float(max(best))


def rule_text(rule):
    return " AND ".join(f"{f} {op} {line:.4g}" for f, op, line in rule)


def card_markdown(book, ev, p=None, note=""):
    r = ev["rule"]
    L = [f"### {book}: `{rule_text(r)}`", ""]
    if p is not None:
        L.append(f"Shuffle test p = {p:.3f} ({'beats luck' if p < 0.05 else 'does NOT beat luck'}). {note}")
    L += ["", "| window | side | trades | win % | mean % | P&L Rs | losers |", "|---|---|---|---|---|---|---|"]
    for win in ("discovery", "holdout", "all"):
        for side in ("book", "kept", "removed"):
            s = ev[win][side]
            win_s = "" if s["win"] is None else f"{s['win']:.0%}"
            mean_s = "" if s["mean"] is None else f"{s['mean']:+.1f}"
            L.append(f"| {win} | {side} | {s['n']} | {win_s} | {mean_s} | {s['pnl']:+,.0f} | {s['losers']} |")
    return "\n".join(L) + "\n"


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        if path.endswith(".json"):
            json.dump(obj, fh, indent=1, default=str)
        else:
            fh.write(obj)
