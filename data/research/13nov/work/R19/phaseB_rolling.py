"""R19 rolling-origin walk-forward with re-fitting (13 Nov). Small runs (one or two factors) are fine now; a long
candidate list is PHASE B (after 15:30).

For a factor and a grid of lines, on each test day D (from FIRST_TEST on): pick the line (and the side, >= or <)
that maximised the Conductor's sum of daily % on all days BEFORE D (ties -> no rule), apply it to D, record the
Conductor's day with and without. The choice is re-made every day, so the result includes the cost of choosing.
Every factor x line x side counts as a trial (printed). Benjamini-Hochberg over factors at the end.

    py -3.13 phaseB_rolling.py wx_er60 wx_vix wx_range_now         # factors, pool books, default grid = deciles
    options: --apply-to c20_9y   --first 2026-10-30   --min-keep 0.3
"""
import sys
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R19")
import argparse, time
import numpy as np, pandas as pd
import harness as H


def run(factor, apply_to, first, min_keep, t_budget):
    df = H.load([factor], books=H.POOL)
    days = sorted(df.day.unique())
    test_days = [d for d in days if d >= first]
    x = pd.to_numeric(df[factor], errors="coerce").astype(float)   # booleans too
    scope = df.book.isin(apply_to)
    grid = np.unique(np.nanpercentile(x[scope], np.arange(10, 100, 10)))
    pp = H.prep(df, H.POOL)
    base = H.conductor(None, H.POOL, prepped=pp, days=days)
    cand = []
    for line in grid:
        for side in (">=", "<"):
            m = (x >= line) if side == ">=" else (x < line)
            keep = ((~scope) | m.fillna(False)).to_numpy()
            if m[scope].mean() < min_keep:
                continue
            c = H.conductor(None, H.POOL, keep=keep, prepped=pp, days=days)
            cand.append((line, side, {d: c[d][0] for d in days}))
    rows = []
    for D in test_days:
        prior = [d for d in days if d < D]
        bsum = sum(base[d][0] for d in prior)
        best = max(cand, key=lambda c_: sum(c_[2][d] for d in prior)) if cand else None
        if best is None or sum(best[2][d] for d in prior) <= bsum:
            rows.append({"day": D, "line": None, "side": None, "base": base[D][0], "rule": base[D][0]})
        else:
            rows.append({"day": D, "line": round(float(best[0]), 4), "side": best[1], "base": base[D][0], "rule": best[2][D]})
    r = pd.DataFrame(rows)
    r["diff"] = r["rule"] - r["base"]
    p = H.sign_flip_p(r["diff"].to_numpy())
    return r, p, len(cand)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("factors", nargs="+")
    ap.add_argument("--apply-to", nargs="*", default=H.POOL)
    ap.add_argument("--first", default="2026-10-30")
    ap.add_argument("--min-keep", type=float, default=0.3)
    ap.add_argument("--budget", type=float, default=160)
    ap.add_argument("--brief", action="store_true", help="one line per factor")
    a = ap.parse_args()
    t0 = time.time()
    ps, trials = [], 0
    for f in a.factors:
        try:
            r, p, n = run(f, a.apply_to, a.first, a.min_keep, 170)
        except Exception as e:
            print(f"=== {f}: skipped ({type(e).__name__}: {e})")
            continue
        trials += n
        ps.append((f, p))
        if a.brief:
            print(f"=== {f}: {n} trials, days ruled {int(r.line.notna().sum())};", end="")
        else:
            print(f"\n=== {f}: rolling re-fit, {n} line x side trials, test days {len(r)} ===")
            print(r.round(2).to_string(index=False))
        print(f"   sum of day %: base {r.base.sum():+.1f}  rule {r.rule.sum():+.1f}; days better {int((r['diff'] > 0).sum())},"
              f" worse {int((r['diff'] < 0).sum())}; losing days base {int((r.base < 0).sum())} rule {int((r.rule < 0).sum())};"
              f" sign-flip p {p:.3f}")
        if time.time() - t0 > a.budget:
            print("time budget reached")
            break
    ps.sort(key=lambda z: z[1])
    m = len(ps)
    print(f"\ntrials in this run: {trials}. Benjamini-Hochberg over {m} factors (q = 0.10):")
    for k, (f, p) in enumerate(ps, 1):
        print(f"   {f}: p {p:.3f}, BH line {0.10 * k / m:.3f} -> {'discovery' if p <= 0.10 * k / m else 'no'}")
    print(f"({time.time() - t0:.1f} s)")


if __name__ == "__main__":
    main()
