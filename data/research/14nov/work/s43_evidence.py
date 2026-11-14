"""Evidence for docs/59: recompute every headline figure from the saved result files and list those files (size,
modified time, SHA-256 prefix), so each number in the report can be traced and rerun. Read-only.
    py -3.13 data/research/14nov/work/s43_evidence.py > docs/59_EVIDENCE.txt"""
import os, sys, json, glob, hashlib, datetime as dt
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
W = r"D:\ApexOptions\data\research\14nov\work"
H1 = os.path.join(W, "h1")
HS = r"D:\ApexOptions\data\research\hist1s"
comp = lambda r: 100 * (np.prod(1 + np.asarray(r, float) / 100) - 1)
pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 60)
SRC = []


def src(p):
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    SRC.append((os.path.relpath(p, r"D:\ApexOptions"), os.path.getsize(p), dt.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M"), h))
    return p


def tstat(ds):
    ds = pd.Series(ds).dropna()
    return round(ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds))), 1) if len(ds) > 3 and ds.std(ddof=1) > 0 else np.nan


def line(name, g, days=None):
    ds = g.groupby("day").ret.sum()
    dd = g.groupby("day").ret.apply(comp)
    return dict(set=name, sessions=g.day.nunique(), trades=len(g), winners_pct=round(100 * (g.ret > 0).mean()), per_trade_pct=round(g.ret.mean(), 2), t=tstat(ds),
                days_up=f"{int((dd > 0).sum())}/{len(dd)}", median_day_pct=round(dd.median(), 1), total_pts=round(g.ret.sum()))


print("docs/59 evidence, generated", dt.datetime.now().strftime("%Y-%m-%d %H:%M"))

print("\nE1. LIVE RECORD of the Conductor (data/paper/<day>.json, START_CAPITAL 100,000 fresh each day)")
for p in sorted(glob.glob(r"D:\ApexOptions\data\paper\2026-11-*.json")):
    d = json.load(open(p, encoding="utf-8")); c = (d.get("books") or d).get("conductor")
    if c:
        src(p)
        tr = [t for t in c.get("trades") or [] if not t.get("adjustment")]
        print(f"  {os.path.basename(p)[:10]}  trades {len(tr):2d}  winners {sum((t.get('pnl_rs') or 0) > 0 for t in tr):2d}  end capital {c.get('capital'):>10,.0f}  day {100 * (c.get('capital') / 100000 - 1):+6.1f} %")

print("\nE2. LIVE STEP TIME (data/logs/perf_<day>.jsonl, 09:15-15:30, budget 100 ms a step at 10 Hz)")
for d in ("2026-11-11", "2026-11-12", "2026-11-13"):
    p = rf"D:\ApexOptions\data\logs\perf_{d}.jsonl"
    if not os.path.exists(p):
        continue
    R = [json.loads(l) for l in open(src(p), encoding="utf-8")]
    R = [r for r in R if "09:15" <= r["mkt"] <= "15:30"]
    print(f"  {d}: median step {np.median([r['p50'] for r in R]):.1f} ms, 95th pct {np.median([r['p95'] for r in R]):.0f} ms, steps over 300 ms {sum(r['over300'] for r in R)}, over 1 s {sum(r['over1000'] for r in R)}, steps a minute {int(np.median([r['n'] for r in R]))} of 600")

print("\nE3. FASTLAB FIDELITY: the champion books' recorded trades re-walked per second (s02_fidelity.py)")
sys.stdout.flush(); os.system(f'py -3.13 "{os.path.join(W, "s02_fidelity.py")}" 2>nul | findstr /v "s$"')

print("\nE4. FOUR YEARS, 1-minute bars (h1/four_years.parquet; s22): the pullback pattern, normal days, model option")
T = pd.read_parquet(src(os.path.join(H1, "four_years.parquet"))); Mo = T[T.model]
rows = []
for v in ("hl_pb0.4", "hl", "hl_v35"):
    g = Mo[Mo.variant == v]
    rows += [line(f"{v}: recorded window", g[g.day >= "2026-10-19"]), line(f"{v}: four years before", g[g.day < "2026-10-19"])]
A = T[~T.model]
rows.append(line("hl: REAL option bars, Nov 2024-Jun 2025", A[A.variant == "hl"]))
print(pd.DataFrame(rows).to_string(index=False))

print("\nE5. FOUR YEARS, 65 entry ideas, found 2022-24 / judged 2025-26 (h1/search4y.parquet; s23)")
S = pd.read_parquet(src(os.path.join(H1, "search4y.parquet")))
rows = []
for v, g in S.groupby("variant"):
    a, b = g[g.day < "2025-01-01"], g[g.day >= "2025-01-01"]
    rows.append(dict(idea=v, n_found=len(a), mean_found=round(a.ret.mean(), 2), t_found=tstat(a.groupby("day").ret.sum()), n_judged=len(b), mean_judged=round(b.ret.mean(), 2), t_judged=tstat(b.groupby("day").ret.sum())))
R = pd.DataFrame(rows)
print(f"  ideas positive in both halves: {int(((R.mean_found > 0) & (R.mean_judged > 0)).sum())} of {len(R)}; of those with t >= 1.4 in both: {int(((R.t_found >= 1.4) & (R.t_judged >= 1.4)).sum())}")
print(R.sort_values("t_judged", ascending=False).head(6).to_string(index=False))
print("  ...momentum / breakout ideas on 2025-26:", R[R.idea.str.contains("breakout|opening range 15m break|opening range 30m break|with the day")].mean_judged.round(2).tolist())

print("\nE6. FOUR YEARS, one account (h1/composite.parquet; s34)")
C = pd.read_parquet(src(os.path.join(H1, "composite.parquet")))
rows = []
for s, g in C.groupby("set", sort=False):
    for tag, sel in (("2022-24", g.day < "2025-01-01"), ("2025-26", g.day >= "2025-01-01")):
        rows.append(line(f"{s} {tag}", g[sel]))
print(pd.DataFrame(rows).to_string(index=False))

print("\nE7. THE YEAR PER SECOND, real strategy classes, normal days (hist1s/classes_run.parquet; s32, s38)")
K = pd.read_parquet(src(os.path.join(HS, "classes_run.parquet"))); K = K[K.src == "model chain"]
print(f"  broker 1-second sessions on disk: {len(glob.glob(os.path.join(HS, 'fut_*.parquet')))}; days in this file: {K.day.nunique()} ({K.day.min()} to {K.day.max()})")
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import s38_year_summary
one_account = s38_year_summary.one_account
rows = []
for b in ("c20_9x", "c20_9y_st15", "fade20", "fade60", "orbfade"):
    g = K[K.book == b]
    rows += [line(f"{b}: year before window", g[g.day < "2026-10-19"]), line(f"{b}: recorded window", g[g.day >= "2026-10-19"])]
print(pd.DataFrame(rows).to_string(index=False))

print("\nE8. EXPIRY DAYS, real class + real option seconds (hist1s/expiry_class.parquet; s40) and fades (s41)")
E = pd.read_parquet(src(os.path.join(HS, "expiry_class.parquet")))
EF = pd.read_parquet(src(os.path.join(HS, "expiry_fades.parquet")))
rows = [line("c20_9x expiry breakout, 48 sessions", E)] + [line(f"{v}", g) for v, g in EF.groupby("variant")]
print(pd.DataFrame(rows).to_string(index=False))
dd = E.groupby("day").ret.apply(comp)
print(f"  expiry days below -50 %: {int((dd < -50).sum())}; above +100 %: {int((dd > 100).sum())}; best {dd.max():+.0f} %, worst {dd.min():+.0f} %")

print("\nE9. ACCOUNT PARITY (s48_parity.py, corrected 14 Nov): fresh Rs 1,00,000 EVERY day as the live account, no pause")
print("    between trades (the live Conductor has none), ties in pool order; continuous compounding beside it")
sys.stdout.flush(); os.system(f'py -3.13 "{os.path.join(W, "s48_parity.py")}" 2>nul')

print("\nE10. ONE-SECOND HISTORY CHECK on 6 Nov (s27): broker future vs tape")
sys.stdout.flush(); os.system(f'py -3.13 "{os.path.join(W, "s27_1s_check.py")}" 2026-11-06 2>nul')

print("\nSOURCE FILES (relative path, bytes, modified, sha256 prefix)")
for p, n, m, h in SRC:
    print(f"  {p}  {n:,}  {m}  {h}")
