"""
Step 2 of the Conductor plan, THE SEARCH (docs/28 §5): per family, on its representative book, for each weather
number: if a line is drawn here, do the winners fall mostly on one side? The output is each family's WEATHER CARD,
every line marked "found by searching the past". A card line is a candidate; it becomes a rule only when it is
written into the register (register.py), frozen and passed on test days.

  python -m apex.conductor.search DIARY.jsonl [--out DIR] [--perms 200]

A line passes only if ALL of these hold (§5):
  * enough trades both sides: weighted count >= 15 each side (a counterfactual that overlaps the real trade counts
    0.5); for whole-day facts (DAY_FACTORS) at least 5 distinct DAYS each side;
  * the kept side wins more often AND makes more on average (mean ret_pct) than the other side;
  * it holds when the line moves: the neighbouring lines (one quantile step lower and higher) keep the same side ahead;
  * it keeps the big wins: at least two-thirds of the family's top 10 % of trades by return are on the kept side;
  * it beats pure luck: the same whole search run on the same rows with the outcomes shuffled (win and return move
    together) gives the distribution of the BEST line found by luck; a real line must beat its 95th percentile.
The luck arithmetic counts distinct families, not books (variants pass or fail together).
Rows used: real and counterfactual rows of the family's representative, not excluded, never control books.
"""
import argparse
import json
import os
import zlib
from collections import defaultdict

import numpy as np

from .diary import family

# docs/28 §3 / §16a: the least-gated member of each family, in order of preference. A family whose preferred books
# have no rows falls back to its member with the most rows (flagged on the card).
REPRESENTATIVES = ("spot_pb45", "spot_dc12_t12", "spot_dc12_t12_first", "spot_orb45", "m1.5_s0.4", "gap3_s0.4",
                   "straddle_spike", "fade_switch", "c20_9x", "t28_fwd")
DAY_FACTORS = {"expiry_day", "day_before_expiry", "after_break", "event", "weekday", "dte", "gap_pts", "gap_filled"}
SKIP = {"v", "v2_error"}
QUANTILES = tuple(q / 10 for q in range(2, 9))
MIN_N, MIN_DAYS, BIG_SHARE = 15.0, 5, 2.0 / 3.0


def representative(fam_rows):
    """(book, fallback?) for one family's rows."""
    books = defaultdict(int)
    for r in fam_rows:
        books[r["book"]] += 1
    for b in REPRESENTATIVES:
        if books.get(b):
            return b, False
    return (max(books, key=books.get), True) if books else (None, True)


def features(rows):
    """{name: (values float array with nan, kind)}; kind = 'num' or 'ind' (a 0/1 indicator from a bool / category)."""
    keys = set()
    for r in rows:
        keys |= set((r.get("weather") or {}).keys())
    out = {}
    for k in sorted(keys - SKIP):
        vals = [(r.get("weather") or {}).get(k) for r in rows]
        if all(v is None for v in vals):
            continue
        if all(isinstance(v, (bool, type(None))) for v in vals):
            out[k] = (np.array([np.nan if v is None else float(v) for v in vals]), "ind")
        elif all(isinstance(v, (int, float, type(None))) and not isinstance(v, bool) for v in vals):
            out[k] = (np.array([np.nan if v is None else float(v) for v in vals]), "num")
        else:                                            # a category: one indicator per value
            for c in sorted({str(v) for v in vals if v is not None}):
                out[f"{k}={c}"] = (np.array([np.nan if v is None else float(str(v) == c) for v in vals]), "ind")
    return out


def _lines(x, kind):
    ok = x[np.isfinite(x)]
    if kind == "ind":
        return [0.5] if ok.size and 0 < ok.mean() < 1 else []
    if np.unique(ok).size < 10:
        return sorted(set(float(v) for v in np.unique(ok)))[1:]          # few values: every split between them
    return sorted(set(float(np.quantile(ok, q)) for q in QUANTILES))


def _side_stats(mask, w, win, ret):
    n = w[mask].sum()
    if n <= 0:
        return n, np.nan, np.nan
    return n, float((w[mask] * win[mask]).sum() / n), float((w[mask] * ret[mask]).sum() / n)


def evaluate(fx, kind, name, w, win, ret, days, big):
    """Every line of one factor: list of dicts (both sides, every line), with the checks applied except luck."""
    fin = np.isfinite(fx)
    lines = _lines(fx, kind)
    res = []
    for li, line in enumerate(lines):
        hi = fin & (fx >= line)
        lo = fin & (fx < line)
        for op, keep, other in ((">=", hi, lo), ("<", lo, hi)):
            nk, srk, rk = _side_stats(keep, w, win, ret)
            no, sro, ro = _side_stats(other, w, win, ret)
            if not (np.isfinite(srk) and np.isfinite(sro)):
                continue
            score = srk - sro
            dayf = name.split("=")[0] in DAY_FACTORS
            nd = int(days.max()) + 1 if days.size else 0
            dk = int(np.count_nonzero(np.bincount(days[keep], minlength=nd))) if dayf else None
            do = int(np.count_nonzero(np.bincount(days[other], minlength=nd))) if dayf else None
            enough = (dk >= MIN_DAYS and do >= MIN_DAYS) if dayf else (nk >= MIN_N and no >= MIN_N)
            nb = int(big.sum())
            bigk = int((big & keep).sum())
            res.append({"factor": name, "op": op, "line": round(line, 6), "li": li, "n_lines": len(lines),
                        "kept_n": round(float(nk), 1), "kept_sr": round(srk, 4), "kept_ret": round(rk, 4),
                        "other_n": round(float(no), 1), "other_sr": round(sro, 4), "other_ret": round(ro, 4),
                        "score": round(score, 4), "kept_days": dk, "other_days": do,
                        "big_wins_kept": f"{bigk}/{nb}",
                        "ok_count": bool(enough), "ok_better": bool(score > 0 and rk > ro),
                        "ok_big": bool(nb == 0 or bigk >= BIG_SHARE * nb)})
    # robustness: the neighbouring lines (same op) keep the same side ahead
    by = {(r["op"], r["li"]): r for r in res}
    for r in res:
        nbrs = [by.get((r["op"], r["li"] + k)) for k in (-1, 1)]
        nbrs = [x for x in nbrs if x is not None]
        r["ok_robust"] = bool(kind == "ind" or (nbrs and all(x["score"] > 0 and x["kept_ret"] > x["other_ret"]
                                                             for x in nbrs)))
    return res


def _passes(r):
    return r["ok_count"] and r["ok_better"] and r["ok_big"] and r["ok_robust"]


def search_family(rows, perms=200):
    """One family's card (rows = the representative's usable rows)."""
    feats = features(rows)
    w = np.array([float(r["weight"]) for r in rows])
    win = np.array([1.0 if r["win"] else 0.0 for r in rows])
    ret = np.array([float(r["ret_pct"]) for r in rows])
    dlist = sorted({r["day"] for r in rows})
    days = np.array([dlist.index(r["day"]) for r in rows], dtype=int)     # day index, for the day counts

    def run(win_, ret_):
        k = max(1, int(round(0.1 * len(ret_))))
        big = np.zeros(len(ret_), bool)
        big[np.argsort(-ret_, kind="stable")[:k]] = True
        big &= ret_ > 0
        out = []
        for name, (fx, kind) in feats.items():
            out += evaluate(fx, kind, name, w, win_, ret_, days, big)
        return out

    found = run(win, ret)
    cands = [r for r in found if _passes(r)]
    seed = zlib.crc32(("|".join(sorted({r["day"] for r in rows})) + str(len(rows))).encode())
    rng = np.random.default_rng(seed)
    best_luck = []
    for _ in range(perms):
        p = rng.permutation(len(rows))
        lk = [r["score"] for r in run(win[p], ret[p]) if _passes(r)]
        best_luck.append(max(lk) if lk else 0.0)
    luck95 = float(np.quantile(best_luck, 0.95)) if best_luck else None
    lines = sorted([dict(r, beats_luck=luck95 is not None and r["score"] > luck95, found_by="searching the past")
                    for r in cands], key=lambda r: -r["score"])
    return {"n_rows": len(rows), "weighted_n": round(float(w.sum()), 1), "n_days": len(dlist),
            "strike_rate": round(float((w * win).sum() / w.sum()), 4) if w.sum() else None,
            "mean_ret": round(float((w * ret).sum() / w.sum()), 4) if w.sum() else None,
            "n_factors": len(feats), "n_lines_tested": len(found), "perms": perms,
            "luck_best_95": None if luck95 is None else round(luck95, 4),
            "card": [r for r in lines if r["beats_luck"]], "near_misses": [r for r in lines if not r["beats_luck"]][:10]}


def search(diary_rows, perms=200, min_rows=30):
    fams = defaultdict(list)
    for r in diary_rows:
        if r.get("control") or r.get("excluded") or r.get("ret_pct") is None or r.get("win") is None:
            continue
        fams[family(r)].append(r)
    cards = {}
    for fam, rows in sorted(fams.items()):
        rep, fb = representative(rows)
        rr = [r for r in rows if r["book"] == rep]
        c = {"family": fam, "representative": rep, "representative_fallback": fb, "family_books": len({r["book"] for r in rows})}
        if len(rr) < min_rows:
            c.update(n_rows=len(rr), skipped=f"fewer than {min_rows} usable rows on the representative")
        else:
            c.update(search_family(rr, perms))
        cards[fam] = c
    searched = [c for c in cards.values() if "card" in c]
    return {"families": len(cards), "families_searched": len(searched),
            "lines_on_cards": sum(len(c["card"]) for c in searched),
            "expected_lucky_cards": round(0.05 * len(searched), 2),   # each family's 95 % line: 1 in 20 by luck
            "cards": cards}


def card_markdown(res):
    out = ["# Weather cards", "",
           f"{res['families_searched']} of {res['families']} families searched; {res['lines_on_cards']} line(s) beat "
           f"luck. About {res['expected_lucky_cards']} family card(s) would show a line by luck alone. Every line here "
           "was **found by searching the past**: a candidate, not a rule.", ""]
    for fam, c in res["cards"].items():
        out.append(f"## {fam} (representative {c['representative']}{' — fallback' if c.get('representative_fallback') else ''})")
        if c.get("skipped"):
            out += [f"Skipped: {c['skipped']} ({c['n_rows']}).", ""]
            continue
        out.append(f"{c['n_rows']} rows over {c['n_days']} days; strike rate {c['strike_rate']:.0%}, mean return "
                   f"{c['mean_ret']:+.2f} %; {c['n_lines_tested']} lines tested; luck's best (95th pct) "
                   f"{c['luck_best_95']:+.3f}.")
        if not c["card"]:
            out += ["No line beats luck.", ""]
            continue
        out += ["", "| Condition | Kept: trades, strike, mean | Other side | Lift | Big wins kept |", "|---|---|---|---|---|"]
        for r in c["card"]:
            out.append(f"| {r['factor']} {r['op']} {r['line']:g} | {r['kept_n']:g}, {r['kept_sr']:.0%}, "
                       f"{r['kept_ret']:+.2f} % | {r['other_n']:g}, {r['other_sr']:.0%}, {r['other_ret']:+.2f} % | "
                       f"{r['score']:+.3f} | {r['big_wins_kept']} |")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Search each family for weather lines; write the weather cards.")
    ap.add_argument("diary")
    ap.add_argument("--out", default=None)
    ap.add_argument("--perms", type=int, default=200)
    a = ap.parse_args(argv)
    rows = [json.loads(x) for x in open(a.diary, encoding="utf-8") if x.strip()]
    res = search(rows, a.perms)
    out = a.out or os.path.dirname(os.path.abspath(a.diary))
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, "cards.json"), "w", encoding="utf-8"), indent=1, default=str)
    open(os.path.join(out, "cards.md"), "w", encoding="utf-8").write(card_markdown(res))
    print(f"search: {res['families_searched']} / {res['families']} families, {res['lines_on_cards']} line(s) on the "
          f"cards -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
