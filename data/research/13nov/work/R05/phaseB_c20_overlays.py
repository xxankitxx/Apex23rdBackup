import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R05 phase B (after 15:30 only): every exit overlay of analysis3/4 on every ds_v2 day, walk-forward summary.
Discovery 19 Oct - 4 Nov, test 5 - 11 Nov. One part loaded at a time; about 25 parts x 5 s to load, overlays ~2 s each.
Usage: py -3.13 phaseB_c20_overlays.py           (first run: builds paths_all.pkl from ds_v2, ~2 min)
       py -3.13 phaseB_c20_overlays.py --group=KE  (then one group per run: P, K, T, L, KE; RE runs with KE)   -> work/R05/phaseB_c20_overlays.txt / .json"""
"""R05 analysis 3 (13 Nov, market hours, within the 3-part budget: the same three ds_v2 parts as the pilot paths).
A. Per-second exit overlays on the c20 trades and the Conductor account, 5, 6 and 9 Nov (all test days; the grid is
   fixed in advance, every variant reported: no discovery step here, phaseB_c20_overlays.py does the walk-forward).
B. Non-council hold marks: 13 natural rules x 4 marks scored with the owner's standard (discovery / test).
C. Thesis fields, giveback rate and attribution at the marks: what the rest of the trade does after the mark."""
import json, os, time
import numpy as np
import pandas as pd
T0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R05"
DS = r"D:\ApexOptions\data\research\ds_v2"
SPLIT = "2026-11-05"
import glob
PARTS = [a for a in sys.argv[1:] if not a.startswith("--")] or sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(DS, "*.npz")) if json.load(open(p[:-4] + ".manifest.json")).get("rows", 0) > 0)
LOG = open(os.path.join(W, f"phaseB_c20_overlays_{next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--group=')), 'build')}.txt"), "w", encoding="utf-8")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
OUT = {}


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n"); LOG.flush()


df = pd.read_pickle(os.path.join(W, "tr.pkl"))
exec(open(os.path.join(W, "rulelib.py"), encoding="utf-8").read())
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
PRI = {b: i for i, b in enumerate(POOL)}
c20 = df[df.book.str.startswith("c20")][["day", "book", "t_in", "t_out", "trigger_t", "strike", "rr", "entry", "exit",
                                         "ret_pct", "reason", "expiry", "hold_s"]].copy()
c20["trig"] = c20.trigger_t.fillna(c20.t_in)
c20["pri"] = c20.book.map(PRI).fillna(99)


def sod(t):
    return (int(t) + 19800) % 86400


# ── A. per-second paths ─────────────────────────────────────────────────────────────────────────────────────────
POSTMAX = 1800
import pickle
GROUP = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--group=")), None)
PARTS = [a for a in PARTS if not a.startswith("--")] or PARTS
PC = os.environ.get("R05_PATHS") or os.path.join(W, "paths_all.pkl")
LOADED = os.path.exists(PC)
paths = pickle.load(open(PC, "rb")) if LOADED else {}
for part in ([] if LOADED else PARTS):
    day = part[:10]
    tr = c20[c20.day == day]
    if not len(tr):
        continue
    z = np.load(os.path.join(DS, part + ".npz"))
    t = z["t"].astype(float)
    K = z["strikes"].astype(float)
    n = len(K)
    opt = z["opt"][:, :n]
    age = z["age"][:, :n]
    exp = str(z["expiry"])
    flat = (15 * 3600) if exp == day else (15 * 3600 + 20 * 60)
    for idx, r in tr.iterrows():
        if str(r.expiry or exp) != exp or not (t[0] <= r.t_in <= t[-1]):
            continue
        jj = np.where(K == float(r.strike))[0]
        if not len(jj):
            continue
        j, s_ = int(jj[0]), (0 if r.rr == "CE" else 1)
        bid = opt[:, j, s_, 0].astype(float)
        ask = opt[:, j, s_, 1].astype(float)
        ok = (bid > 0) & (ask >= bid) & (age[:, j, s_] <= 15)
        i0 = int(np.searchsorted(t, r.t_in))
        i1 = int(np.searchsorted(t, r.t_out))
        iE = int(np.searchsorted(t, min(r.t_out + POSTMAX, r.t_out - sod(r.t_out) + flat), side="right"))
        if i1 <= i0:
            continue
        b = np.where(ok[i0:iE], bid[i0:iE], np.nan)
        b = pd.Series(b).ffill().values
        paths[idx] = (t[i0:iE] - r.t_in, b, i1 - i0)
    del z, opt, age
say("A paths", len(paths), "trades", round(time.time() - T0, 1), "s")

A = c20.loc[list(paths)].copy()


def overlay(rule):
    """alt ret and alt hold for every trade with a path. Earlier-exit overlays use the bid at the first second the
    condition holds before the book's own exit; 'L' rules hold past the exit (bid h s later, capped by the path)."""
    kind = rule[0]
    ret2, hold2, fired = [], [], []
    for idx, r in A.iterrows():
        tt, b, k1 = paths[idx]
        e = r.entry
        g = b / e - 1
        rr, hh, f = r.ret_pct, r.t_out - r.t_in, False
        isexp = str(r.expiry)[:10] == r.day
        if kind in ("KE", "RE") and not isexp:
            kind_ = None
        else:
            kind_ = kind
        if kind_ in ("KE", "RE", "RA"):
            seg = g[:k1]
            pk = np.fmax.accumulate(np.where(np.isfinite(seg), seg, -9))
            if kind_ == "KE":
                a, k = rule[1], rule[2]
                fl = np.where(pk >= a, k * pk, -9)
            else:                                   # c20_9x ramp (R9_19): 0.15 arm -> entry; 0.25..0.5 -> 0.45..0.70 x g
                u = np.clip((pk - 0.25) / 0.25, 0, 1)
                fl = np.where(pk < 0.15, -9, np.where(pk < 0.25, 0.0, np.where(pk < 0.5, pk * (0.45 + 0.25 * u), 0.7 * pk)))
            w = np.where(seg <= fl)[0]
            if len(w):
                rr, hh, f = 100 * seg[w[0]], tt[w[0]], True
        if kind in ("P", "K", "T"):
            seg = g[:k1]
            pk = np.fmax.accumulate(np.where(np.isfinite(seg), seg, -9))
            if kind == "P":
                a, q = rule[1], rule[2]
                hit = (pk >= a) & (1 + seg <= (1 + pk) * (1 - q))
            elif kind == "K":
                a, k = rule[1], rule[2]
                hit = (pk >= a) & (seg <= k * pk)
            else:
                m, x = rule[1], rule[2]
                hit = (tt[:k1] >= m) & (tt[:k1] < m + 1.5) & (pk < x)
            w = np.where(hit)[0]
            if len(w):
                rr, hh, f = 100 * seg[w[0]], tt[w[0]], True
        elif kind == "L":
            h, only = rule[1], rule[2]
            if only is None or (only == "FWD" and str(r.reason).replace("COUNCIL ", "").startswith("FWD_TRAIL")) or \
                    (only == "FWDpos" and str(r.reason).replace("COUNCIL ", "").startswith("FWD_TRAIL") and r.ret_pct > 0):
                k2 = k1 + int(h)
                if k2 < len(b) and np.isfinite(b[k2]):
                    rr, hh, f = 100 * g[k2], tt[k2], True
        ret2.append(rr); hold2.append(hh); fired.append(f)
    return np.array(ret2), np.array(hold2), np.array(fired)



if not LOADED:
    pickle.dump(paths, open(PC, "wb"))
    if GROUP is None:
        say("paths cached; run again with --group=P|K|T|L|KE (one group per run, 3-minute limit)")
        sys.exit(0)


def account(tr, ret_col, tout_col):
    cap, held, out = 100000.0, None, []
    for _, t in tr.sort_values(["trig", "pri"]).iterrows():
        if held is not None:
            h_trig, h_out, h_book = held
            if t.trig <= h_trig or t.trig < h_out or (t.trig == h_out and t.book == h_book):
                continue
            held = None
        lots = int(cap // (t.entry * 65))
        if lots < 1:
            continue
        cap += t.entry * (t[ret_col] / 100.0) * lots * 65
        held = (t.trig, t[tout_col], t.book)
        out.append((t.book, t[ret_col], cap))
    return out




SPLIT = "2026-11-05"
RULES = [("base",)]
RULES += [("P", a, q) for a in (0.10, 0.20, 0.30, 0.50) for q in (0.10, 0.20, 0.30)]
RULES += [("K", a, k) for a in (0.10, 0.20, 0.30) for k in (0.3, 0.5, 0.7)]
RULES += [("T", m, x) for m in (120, 300, 600) for x in (0.05, 0.10)]
RULES += [("L", h, o) for h in (60, 120, 300, 600) for o in ("FWD", "FWDpos")]
RULES += [("KE", a, k) for a in (0.2, 0.3, 0.4) for k in (0.5, 0.6, 0.7)]
RULES += [("KE",) * 0 + ("RE",)]
RULES = [r for r in RULES if r[0] == "base" or GROUP in (None, "all") or r[0] == GROUP or (GROUP == "KE" and r[0] == "RE")]
say("group", GROUP, "variants tried:", len(RULES) - 1, "(all groups: 46)")
pool_m = A.book.isin(PRI).values
isexp = (A.expiry.astype(str).str[:10] == A.day).values
rows = []
for rule in RULES:
    if rule[0] == "base":
        r2, h2, f = A.ret_pct.values, (A.t_out - A.t_in).values, np.zeros(len(A), bool)
    else:
        r2, h2, f = overlay(rule)
    g = A.assign(ret2=r2, tout2=A.t_in.values + h2)
    acc = {}
    for day, gd in g[pool_m].groupby("day"):
        a = account(gd, "ret2", "tout2")
        b = account(gd, "ret_pct", "t_out")
        acc[day] = (100 * (a[-1][2] / 1e5 - 1) if a else 0.0, len(a), sum(1 for x in a if x[1] > 0),
                    100 * (b[-1][2] / 1e5 - 1) if b else 0.0, len(b), sum(1 for x in b if x[1] > 0))
    rec = dict(rule=":".join(str(x) for x in rule), fired=int(f.sum()))
    for part, sel in (("disc", lambda d: d < SPLIT), ("test", lambda d: d >= SPLIT)):
        z = {d: v for d, v in acc.items() if sel(d)}
        if not z:
            continue
        mk = np.array([sel(d) for d in A.day]) & pool_m
        top = mk & (A.ret_pct.values >= np.quantile(A.ret_pct.values[mk], 0.9))
        rec[f"{part}_strike"] = f"{sum(v[2] for v in z.values())}/{sum(v[1] for v in z.values())} vs {sum(v[5] for v in z.values())}/{sum(v[4] for v in z.values())}"
        rec[f"{part}_days_better"] = f"{sum(v[0] > v[3] for v in z.values())}/{len(z)}"
        rec[f"{part}_losing_days"] = f"{sum(v[0] < 0 for v in z.values())} vs {sum(v[3] < 0 for v in z.values())}"
        rec[f"{part}_worst"] = f"{min(v[0] for v in z.values()):+.1f} vs {min(v[3] for v in z.values()):+.1f}"
        best_d = max(z, key=lambda d: z[d][0] - z[d][3])
        rec[f"{part}_gain_wo_best_day"] = round(np.mean([v[0] - v[3] for d, v in z.items() if d != best_d]) if len(z) > 1 else np.nan, 2)
        rec[f"{part}_top_kept"] = round(float((r2[top] >= 0.67 * A.ret_pct.values[top]).mean()), 2) if top.any() else np.nan
        rec[f"{part}_exp_d"] = round(float((r2 - A.ret_pct.values)[mk & isexp].mean()), 3) if (mk & isexp).any() else np.nan
        rec[f"{part}_norm_d"] = round(float((r2 - A.ret_pct.values)[mk & ~isexp].mean()), 3) if (mk & ~isexp).any() else np.nan
        rec[f"{part}_per_day"] = ";".join(f"{d[5:]}:{v[0]:+.1f}/{v[3]:+.1f}" for d, v in sorted(z.items()))
    rows.append(rec)
R = pd.DataFrame(rows)
say(R.drop(columns=[c for c in R.columns if c.endswith("per_day")]).to_string(index=False))
say(R[["rule"] + [c for c in R.columns if c.endswith("per_day")]].to_string(index=False))
json.dump(R.to_dict("records"), open(os.path.join(W, f"phaseB_c20_overlays_{GROUP}.json"), "w"), indent=1, default=str)
say("done", round(time.time() - T0, 1))
