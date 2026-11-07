"""
Compare two replay run folders (7 Nov, stakeholder round 2, 6.1) — the other half of the gate in docs/29.

  python -m apex.replay_compare RUN_A RUN_B [--books-only] [--skip-data-events] [--with-straddle]

Per day present in both runs (paper/<day>.json on each side):
  * the books: every book, every trade, every field, EXACT (no float tolerance). The first difference is reported as
    (book, trade #, field, a, b), with the number of books that differ. Field-level comparison is what caught the
    step-1 gain-trail leak.
  * decisions_, strikes_ and missed_<day>.jsonl line by line; events_<day>.jsonl with counterfactual (#cf) lines
    removed (and DATA lines with --skip-data-events); straddle_<day>.jsonl with --with-straddle.
  * missed_summary_<day>.json: any counterfactual error or recorder fault on either side fails the day.
A file present on one side only is reported and skipped (recorder off vs on: missed_* exists on one side).
--books-only compares the books and the summaries only (recorder off vs on: everything else may differ by design).
One verdict line per day; the exit code is non-zero on any difference.
"""
import argparse
import json
import os
import sys

TAPES = ("decisions", "strikes", "missed", "events")


def _paper(run):
    p = os.path.join(run, "paper")
    return p if os.path.isdir(p) else run


def days(run):
    out = []
    for f in os.listdir(_paper(run)):
        if f.endswith(".json") and len(f) == 15 and f[4] == "-" and f[7] == "-":
            out.append(f[:-5])
    return sorted(out)


def first_book_diff(a, b):
    """(n_books_differing, first difference as a tuple or None)."""
    names = list(a) + [n for n in b if n not in a]
    n, first = 0, None
    for name in names:
        if name not in a or name not in b:
            n += 1
            first = first or (name, None, "book present", name in a, name in b)
            continue
        x, y = a[name], b[name]
        if x == y:
            continue
        n += 1
        if first:
            continue
        tx, ty = x.get("trades") or [], y.get("trades") or []
        if len(tx) != len(ty):
            first = (name, None, "trade count", len(tx), len(ty))
        for i, (u, v) in enumerate(zip(tx, ty)):
            if first:
                break
            for k in list(u) + [k for k in v if k not in u]:
                if u.get(k, "<absent>") != v.get(k, "<absent>"):
                    first = (name, i, k, u.get(k, "<absent>"), v.get(k, "<absent>"))
                    break
        if not first:
            for k in list(x) + [k for k in y if k not in x]:
                if k != "trades" and x.get(k, "<absent>") != y.get(k, "<absent>"):
                    first = (name, None, k, x.get(k, "<absent>"), y.get(k, "<absent>"))
                    break
    return n, first


def _lines(path, kind, skip_data):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if kind == "events":
                if "#cf" in line:
                    continue
                if skip_data:
                    try:
                        if json.loads(line).get("k") == "DATA":
                            continue
                    except Exception:
                        pass
            out.append(line.rstrip("\n"))
    return out


def compare_day(ra, rb, day, books_only=False, skip_data=False, with_straddle=False):
    """[(ok, message)] for one day."""
    pa, pb = _paper(ra), _paper(rb)
    res = []
    A = json.load(open(os.path.join(pa, f"{day}.json"), encoding="utf-8"))
    B = json.load(open(os.path.join(pb, f"{day}.json"), encoding="utf-8"))
    n, first = first_book_diff(A, B)
    res.append((n == 0, f"books: {len(A)} vs {len(B)}, identical" if n == 0 else
                f"books: {n} differ; first: book={first[0]} trade={first[1]} field={first[2]} a={first[3]!r} b={first[4]!r}"))
    for side, p in (("A", pa), ("B", pb)):
        sp = os.path.join(p, f"missed_summary_{day}.json")
        if os.path.exists(sp):
            s = json.load(open(sp, encoding="utf-8"))
            bad = int(s.get("cf_errors") or 0) + int(s.get("recorder_faults") or 0)
            res.append((bad == 0, f"recorder {side}: {s.get('rows')} rows, {s.get('cf_errors')} errors, "
                                  f"{s.get('recorder_faults')} faults"))
    if books_only:
        return res
    kinds = TAPES + (("straddle",) if with_straddle else ())
    for kind in kinds:
        fa, fb = os.path.join(pa, f"{kind}_{day}.jsonl"), os.path.join(pb, f"{kind}_{day}.jsonl")
        ea, eb = os.path.exists(fa), os.path.exists(fb)
        if not ea and not eb:
            continue
        if ea != eb:
            res.append((True, f"{kind}: only in {'A' if ea else 'B'} (skipped)"))
            continue
        la, lb = _lines(fa, kind, skip_data), _lines(fb, kind, skip_data)
        if la == lb:
            res.append((True, f"{kind}: {len(la)} lines identical"))
            continue
        i = next((k for k, (x, y) in enumerate(zip(la, lb)) if x != y), min(len(la), len(lb)))
        res.append((False, f"{kind}: {len(la)} vs {len(lb)} lines; first difference at line {i + 1}: "
                           f"a={(la[i] if i < len(la) else '<end>')[:160]!r} b={(lb[i] if i < len(lb) else '<end>')[:160]!r}"))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--books-only", action="store_true")
    ap.add_argument("--skip-data-events", action="store_true")
    ap.add_argument("--with-straddle", action="store_true")
    a = ap.parse_args(argv)
    da, db = days(a.run_a), days(a.run_b)
    both = [d for d in da if d in db]
    for d in sorted(set(da) ^ set(db)):
        print(f"{d}: only in {'A' if d in da else 'B'} (skipped)")
    if not both:
        print("no day present in both runs")
        return 1
    all_ok = True
    for d in both:
        res = compare_day(a.run_a, a.run_b, d, a.books_only, a.skip_data_events, a.with_straddle)
        ok = all(r[0] for r in res)
        all_ok &= ok
        print(f"{d}: {'IDENTICAL' if ok else 'DIFFERENT'}")
        for good, msg in res:
            print(f"   {'ok ' if good else 'BAD'} {msg}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
