"""
Each BOOK's weather card (owner, 8 Nov: "which book performs profitably under which weather conditions", every
docs/27 item, every book). Not one representative per family: every book, on its own trades and missed signals.
For every book with at least MIN_ROWS usable rows, every photo field and every line (search.search_family: 15+
weighted trades each side, day-type fields counted in days, the kept side ahead on strike rate AND mean return, the
neighbouring lines agree, two-thirds of the big wins kept, luck = the same search on 200 shuffles). The card lists
the best line per field (up to 8), the hurt side, how many never-worked losses fall on the hurt side, the docs/27
item each field belongs to, and whether the line beats luck. Everything is "found by searching the past".
    py -3.13 -m apex.conductor.book_cards OUT_DIR (--diary DIARY.jsonl | RUN_DIR [RUN_DIR ...]) [--procs 15]
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from apex.conductor import search  # noqa: E402

MIN_ROWS = 30
PERMS = 200


def _one(args):
    book, rows = args
    real = [r for r in rows if not r["is_counterfactual"]]
    head = {"n_rows": len(rows), "n_real": len(real), "n_days": len({r["day"] for r in rows}),
            "real_win": round(sum(1 for r in real if r["win"]) / max(1, len(real)), 4),
            "real_mean": round(sum(float(r["ret_pct"]) for r in real) / max(1, len(real)), 3),
            "never_worked": sum(1 for r in real if r.get("loss_kind") == "never_worked"),
            "gave_back": sum(1 for r in real if r.get("loss_kind") == "gave_back")}
    if len(rows) < MIN_ROWS:
        return book, dict(head, skipped=True)
    c = search.search_family(rows, perms=PERMS)
    lines, seen = [], set()
    for x in c["card"] + c["near_misses"]:
        if x["factor"] in seen:
            continue
        seen.add(x["factor"])
        lines.append(x)
    feats = search.features(rows)
    nwm = np.array([r.get("loss_kind") == "never_worked" for r in rows])
    for x in lines[:8]:
        fx = feats[x["factor"]][0]
        fin = np.isfinite(fx)
        keep = fin & ((fx >= x["line"]) if x["op"] == ">=" else (fx < x["line"]))
        x["nw_other"], x["nw_all"] = int((nwm & fin & ~keep).sum()), int((nwm & fin).sum())
        x["item"], x["item_label"] = search.item_of(x["factor"])
    return book, dict(head, luck95=c["luck_best_95"], n_lines=c["n_lines_tested"], n_factors=c["n_factors"],
                      lines=lines[:8])


def build(rows, procs=15):
    by = defaultdict(list)
    for r in rows:
        if r.get("control") or r.get("excluded") or r.get("ret_pct") is None or r.get("win") is None:
            continue
        by[r["book"]].append(r)
    items = sorted(by.items(), key=lambda kv: -len(kv[1]))
    if procs > 1 and len(items) > 1:
        with Pool(min(procs, len(items))) as p:
            res = dict(p.map(_one, items, chunksize=1))
    else:
        res = dict(_one(x) for x in items)
    n = sum(1 for c in res.values() if not c.get("skipped"))
    hit = sum(1 for c in res.values() if any(x.get("beats_luck") for x in c.get("lines") or []))
    return {"books": len(res), "searched": n, "beat_luck": hit, "expected_by_luck": round(0.05 * n, 1),
            "min_rows": MIN_ROWS, "perms": PERMS, "cards": res}


def markdown(res, days_text=""):
    L = ["# Each book's weather card", "",
         f"{days_text}Every book on its own trades plus its missed signals; EVERY field of the weather photograph "
         "(all 68 docs/27 items) and every line. Checks: 15+ weighted trades each side (day-type fields: 5 days each "
         "side), kept side ahead on win rate and mean, neighbouring lines agree, two-thirds of big wins kept. Luck: "
         f"the same search on {res['perms']} shuffles; 'beats luck' = better than luck's 95th percentile.", "",
         f"**{res['searched']} of {res['books']} books searched; {res['beat_luck']} have a line that beats luck; about "
         f"{res['expected_by_luck']} would by chance alone.** Every line is a lead found by searching the past; a "
         "line that does not beat luck is not yet distinguishable from luck.", ""]
    order = sorted(res["cards"].items(), key=lambda kv: (bool(kv[1].get("skipped")), -kv[1]["n_real"]))
    for b, c in order:
        if c.get("skipped"):
            continue
        L.append(f"## {b}")
        L.append(f"{c['n_real']} trades on {c['n_days']} days, {c['real_win']:.0%} winners, mean {c['real_mean']:+.1f} %. "
                 f"Losses: {c['never_worked']} never worked (weather), {c['gave_back']} worked then gave it back (exits). "
                 f"{c['n_factors']} fields, {c['n_lines']} lines tested.")
        if not c["lines"]:
            L += ["No condition passes the checks.", ""]
            continue
        L += ["", "| Item | Helped when | Trades, win %, mean | Hurt otherwise | Never-worked losses on the hurt side | Beats luck |",
              "|---|---|---|---|---|---|"]
        for x in c["lines"]:
            L.append(f"| {x.get('item') or '?'} {x.get('item_label', '')} | {x['factor']} {x['op']} {x['line']:g} | "
                     f"{x['kept_n']:g}, {x['kept_sr']:.0%}, {x['kept_ret']:+.1f} % | {x['other_n']:g}, {x['other_sr']:.0%}, "
                     f"{x['other_ret']:+.1f} % | {x.get('nw_other', '?')} of {x.get('nw_all', '?')} | "
                     f"{'**yes**' if x['beats_luck'] else 'no'} |")
        L.append("")
    sk = [f"{b} ({c['n_real']})" for b, c in order if c.get("skipped")]
    if sk:
        L += [f"## Too few trades to search (under {res['min_rows']} rows)", ", ".join(sk), ""]
    return "\n".join(L)


def load_rows(diary_path=None, run_dirs=()):
    rows = []
    if diary_path:
        rows += [json.loads(l) for l in open(diary_path, encoding="utf-8")]
    if run_dirs:
        from apex.engine import defects
        from . import diary
        for r in run_dirs:
            books, missed = diary.load_days(r)
            declared, _ = defects.load_declared(os.path.join(r, "learning", "defects.json"))
            rows += diary.build(books, missed, declared=declared)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Each book's weather card over every docs/27 item.")
    ap.add_argument("out")
    ap.add_argument("runs", nargs="*")
    ap.add_argument("--diary", default=None)
    ap.add_argument("--procs", type=int, default=15)
    a = ap.parse_args(argv)
    rows = load_rows(a.diary, a.runs)
    os.makedirs(a.out, exist_ok=True)
    if a.runs and not a.diary:
        with open(os.path.join(a.out, "diary.jsonl"), "w", encoding="utf-8") as f:
            for x in rows:
                f.write(json.dumps(x, default=str) + "\n")
    res = build(rows, a.procs)
    days = sorted({r["day"] for r in rows})
    txt = f"{len(days)} days ({days[0]} to {days[-1]}). " if days else ""
    json.dump(res, open(os.path.join(a.out, "book_cards.json"), "w", encoding="utf-8"), indent=1, default=str)
    open(os.path.join(a.out, "book_cards.md"), "w", encoding="utf-8").write(markdown(res, txt))
    print(f"{res['books']} books, {res['searched']} searched, {res['beat_luck']} beat luck "
          f"(about {res['expected_by_luck']} expected by luck) -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
