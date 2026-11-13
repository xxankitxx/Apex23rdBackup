import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
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
PARTS = sys.argv[1:] or ["2026-11-05", "2026-11-06", "2026-11-09"]
LOG = open(os.path.join(W, "analysis4.txt"), "w", encoding="utf-8")
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
paths = {}
for part in PARTS:
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


import pickle
pickle.dump(paths, open(os.path.join(W, "paths_pilot.pkl"), "wb"))


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




RULES = [("base",)]
RULES += [("L", h, o) for h in (60, 120, 300, 600) for o in ("FWD", "FWDpos")]
RULES += [("KE", a, k) for a in (0.2, 0.3, 0.4) for k in (0.5, 0.6, 0.7)]
RULES += [("RE",), ("RA",)]
pool_m = A.book.isin(PRI).values
rows, fires = [], {}
for rule in RULES:
    if rule[0] == "base":
        r2, h2, f = A.ret_pct.values, (A.t_out - A.t_in).values, np.zeros(len(A), bool)
    else:
        r2, h2, f = overlay(rule)
    fires[":".join(str(x) for x in rule)] = (r2, f)
    dl = r2 - A.ret_pct.values
    g = A.assign(ret2=r2, tout2=A.t_in.values + h2)
    acc = {}
    for day, gd in g[pool_m].groupby("day"):
        a = account(gd, "ret2", "tout2")
        acc[day] = (100 * (a[-1][2] / 1e5 - 1) if a else 0.0, len(a), sum(1 for x in a if x[1] > 0))
    top = A.ret_pct.values >= np.quantile(A.ret_pct.values, 0.9)
    kept = (r2[top] >= 0.67 * A.ret_pct.values[top]).mean()
    per = pd.Series(dl).groupby(A.day.values).mean()
    rows.append(dict(rule=":".join(str(x) for x in rule), fired=int(f.sum()), n=len(A),
                     win=f"{(r2 > 0).mean():.3f}", d_all=round(dl.mean(), 3), d_pool=round(dl[pool_m].mean(), 3),
                     d_days=";".join(f"{k[5:]}:{v:+.2f}" for k, v in per.items()), top_kept=round(kept, 2),
                     cond=";".join(f"{k[5:]}:{v[0]:+.1f}% {v[2]}/{v[1]}" for k, v in acc.items())))
RA_ = pd.DataFrame(rows)
say("A'. hold-longer and expiry-floor overlays, c20 trades\n", RA_.to_string(index=False))
OUT["A4"] = RA_.to_dict("records")
for nm in ("KE:0.3:0.7", "RE", "KE:0.3:0.6"):
    r2, f = fires[nm]
    x = A.assign(alt=r2, fired=f)[f].copy()
    x["time_in"] = pd.to_datetime(x.t_in + 19800, unit="s").dt.strftime("%H:%M:%S")
    say(f"  {nm} fired on:\n", x[["day", "book", "time_in", "rr", "reason", "ret_pct", "alt"]].round(2).to_string(index=False))

# ── B'. thesis_impact_with and held_net rules on the non-council marks (owner's standard) ──────────────────────
def fam(b):
    for p in ("rx_", "hx_", "fx_", "fh_"):
        if b.startswith(p):
            return "twin"
    if b.startswith("c20"):
        return "c20"
    return b.split("_")[0] if "_" in b else b


df["fam"] = df.book.map(fam)
nonc = df[(df.fam != "c20") & (df.fam != "twin") & (df.fam != "conductor")]
RULES_B = [("thesis_impact_with", ">=", 1.0), ("held_net", "<=", -1.0), ("held_net", "<=", 0.0),
           ("held_with_share", "<=", 0.5)]
rows = []
for m in (60, 300, 900):
    d = nonc[nonc[f"h{m}_gain_pct"].notna()]
    X = hold_frame(d, m)
    ret, alt0 = d.ret_pct.values, X.gain_pct.values
    combos = [(h,) for h in RULES_B] + [(("thesis_impact_with", ">=", 1.0), ("held_net", "<=", 0.0)),
                                       (("thesis_impact_with", ">=", 1.0), ("gain_pct", ">=", 0.0))]
    for cb in combos:
        f = np.ones(len(d), bool)
        for h in cb:
            f &= fire(d, X, ("H",) + h)
        alt = np.where(f, alt0, ret)
        dl = alt - ret
        rec = dict(mark=m, rule=" & ".join(f"{h[0]}{h[1]}{h[2]:g}" for h in cb))
        for part, mk in (("disc", (d.day < SPLIT).values), ("test", (d.day >= SPLIT).values)):
            dd = d[mk]
            per = pd.Series(dl[mk]).groupby(dd.day.values).mean()
            top = ret[mk] >= np.quantile(ret[mk], 0.9)
            kept = (~f[mk][top] | (alt[mk][top] >= 0.67 * ret[mk][top])).mean()
            rnd = f[mk].mean() * (alt0[mk] - ret[mk]).mean()
            bds = pd.Series(dl[mk]).groupby(dd.day.values).sum()
            wd0 = pd.Series(ret[mk]).groupby(dd.day.values).mean().min()
            wd1 = pd.Series(alt[mk]).groupby(dd.day.values).mean().min()
            rec.update({f"{part}_fired": int(f[mk].sum()), f"{part}_win": f"{(ret[mk] > 0).mean():.3f}->{(alt[mk] > 0).mean():.3f}",
                        f"{part}_gain": round(dl[mk].mean(), 3), f"{part}_vs_rnd": round(dl[mk].mean() - rnd, 3),
                        f"{part}_days": f"{int((per > 0).sum())}/{len(per)}",
                        f"{part}_nobestday": round((dl[mk].sum() - bds.max()) / mk.sum(), 3),
                        f"{part}_nobesttrade": round((dl[mk].sum() - dl[mk].max()) / mk.sum(), 3),
                        f"{part}_topkept": round(kept, 3), f"{part}_worst": f"{wd0:+.2f}->{wd1:+.2f}"})
            if part == "test":
                rec["test_per_day"] = ";".join(f"{k[5:]}:{v:+.2f}" for k, v in per.items())
            else:
                rec["disc_per_day"] = ";".join(f"{k[5:]}:{v:+.2f}" for k, v in per.items())
        rows.append(rec)
RB = pd.DataFrame(rows)
cols = ["mark", "rule", "disc_fired", "disc_win", "disc_gain", "disc_vs_rnd", "disc_days", "disc_nobestday", "disc_topkept",
        "test_fired", "test_win", "test_gain", "test_vs_rnd", "test_days", "test_nobestday", "test_nobesttrade",
        "test_topkept", "test_worst"]
say("B'. thesis rules, non-council marks\n", RB[cols].to_string(index=False))
say(RB[["mark", "rule", "disc_per_day", "test_per_day"]].to_string(index=False))
OUT["B4"] = RB.to_dict("records")
json.dump(OUT, open(os.path.join(W, "analysis4.json"), "w"), indent=1, default=str)
say("done", round(time.time() - T0, 1))
