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
LOG = open(os.path.join(W, "analysis3.txt"), "w", encoding="utf-8")
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
            if only is None or (only == "FWD" and str(r.reason).startswith("FWD_TRAIL")) or \
                    (only == "FWDpos" and str(r.reason).startswith("FWD_TRAIL") and r.ret_pct > 0):
                k2 = k1 + int(h)
                if k2 < len(b) and np.isfinite(b[k2]):
                    rr, hh, f = 100 * g[k2], tt[k2], True
        ret2.append(rr); hold2.append(hh); fired.append(f)
    return np.array(ret2), np.array(hold2), np.array(fired)


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
RULES += [("P", a, q) for a in (0.10, 0.20, 0.30, 0.50) for q in (0.10, 0.20, 0.30)]
RULES += [("K", a, k) for a in (0.10, 0.20, 0.30) for k in (0.3, 0.5, 0.7)]
RULES += [("T", m, x) for m in (120, 300, 600) for x in (0.05, 0.10)]
RULES += [("L", h, o) for h in (120, 300, 600) for o in ("FWD", "FWDpos")]
pool_m = A.book.isin(PRI).values
rows = []
for rule in RULES:
    if rule[0] == "base":
        r2, h2, f = A.ret_pct.values, (A.t_out - A.t_in).values, np.zeros(len(A), bool)
    else:
        r2, h2, f = overlay(rule)
    dl = r2 - A.ret_pct.values
    g = A.assign(ret2=r2, tout2=A.t_in.values + h2)
    acc = {}
    for day, gd in g[pool_m].groupby("day"):
        a = account(gd, "ret2", "tout2")
        acc[day] = (100 * (a[-1][2] / 1e5 - 1) if a else 0.0, len(a), sum(1 for x in a if x[1] > 0),
                    max((x[1] for x in a), default=0.0))
    top = A.ret_pct.values >= np.quantile(A.ret_pct.values, 0.9)
    kept = (r2[top] >= 0.67 * A.ret_pct.values[top]).mean()
    per = pd.Series(dl).groupby(A.day.values).mean()
    rows.append(dict(rule=":".join(str(x) for x in rule), fired=int(f.sum()), n=len(A),
                     win=f"{(r2 > 0).mean():.3f}", d_all=round(dl.mean(), 3), d_pool=round(dl[pool_m].mean(), 3),
                     d_days=";".join(f"{k[5:]}:{v:+.2f}" for k, v in per.items()), top_kept=round(kept, 2),
                     cond=";".join(f"{k[5:]}:{v[0]:+.1f}% {v[2]}/{v[1]}" for k, v in acc.items()),
                     cond_mean=round(np.mean([v[0] for v in acc.values()]), 2)))
RA = pd.DataFrame(rows)
say("\nA. per-second overlays, c20 trades on", PARTS, "(n trades", len(A), "pool", int(pool_m.sum()), ")\n", RA.to_string(index=False))
OUT["A"] = RA.to_dict("records")
# what the price did after each exit reason (bid h s after the exit minus the exit bid, % of entry)
rr_ = []
for idx, r in A.iterrows():
    tt, b, k1 = paths[idx]
    e = r.entry
    row = dict(reason=str(r.reason).split(" ")[0].split("(")[0], ret=r.ret_pct)
    for h in (60, 300, 600, 1800):
        k2 = k1 + h
        row[f"after{h}"] = 100 * (b[k2] - b[k1]) / e if k2 < len(b) and np.isfinite(b[k2]) and np.isfinite(b[k1]) else np.nan
        seg = b[k1:min(k2 + 1, len(b))]
        row[f"best{h}"] = 100 * (np.nanmax(seg) - b[k1]) / e if np.isfinite(seg).any() else np.nan
    rr_.append(row)
AR = pd.DataFrame(rr_).groupby("reason").agg(n=("ret", "size"), ret=("ret", "mean"),
                                             after60=("after60", "mean"), after300=("after300", "mean"),
                                             after600=("after600", "mean"), after1800=("after1800", "mean"),
                                             best300=("best300", "mean"), best1800=("best1800", "mean"))
say("\nA2. the held contract's bid after the book's exit, % of entry (mean), by exit reason\n", AR.round(2).to_string())
OUT["A2"] = AR.round(3).reset_index().to_dict("records")
say("  t", round(time.time() - T0, 1))


# ── B. non-council natural rules, owner's standard ─────────────────────────────────────────────────────────────
def fam(b):
    for p in ("rx_", "hx_", "fx_", "fh_"):
        if b.startswith(p):
            return "twin"
    if b.startswith("c20"):
        return "c20"
    return b.split("_")[0] if "_" in b else b


df["fam"] = df.book.map(fam)
nonc = df[(df.fam != "c20") & (df.fam != "twin") & (df.fam != "conductor")]
NAT = [("gain_pct", "<=", 0.0), ("gain_pct", "<=", -5.0), ("peak_pct", "<=", 5.0), ("peak_pct", "<=", 10.0),
       ("giveback_share", ">=", 0.5), ("fut_fav_pts", "<=", 0.0), ("fut_fav_pts", "<=", -10.0),
       ("thesis_ep_against", ">=", 1.0), ("held_net", "<=", -1.0), ("fires_net", "<=", -1.0),
       ("attr_iv_chg", "<=", -1.0), ("gain_pct", ">=", 20.0), ("peak_age_s", ">=", 120.0)]
rows = []
for m in (60, 300, 900, 1800):
    d = nonc[nonc[f"h{m}_gain_pct"].notna()]
    X = hold_frame(d, m)
    ret = d.ret_pct.values
    alt0 = X.gain_pct.values
    for h in NAT:
        f = fire(d, X, ("H",) + h)
        alt = np.where(f, alt0, ret)
        dl = alt - ret
        rec = dict(mark=m, rule=f"{h[0]}{h[1]}{h[2]:g}")
        for part, mk in (("disc", (d.day < SPLIT).values), ("test", (d.day >= SPLIT).values)):
            dd = d[mk]
            per = pd.Series(dl[mk]).groupby(dd.day.values).mean()
            top = ret[mk] >= np.quantile(ret[mk], 0.9)
            kept = (~f[mk][top] | (alt[mk][top] >= 0.67 * ret[mk][top])).mean()
            rnd = f[mk].mean() * (alt0[mk] - ret[mk]).mean()       # a random rule firing as often
            byday_sum = pd.Series(dl[mk]).groupby(dd.day.values).sum()
            rec.update({f"{part}_n": int(mk.sum()), f"{part}_fired": int(f[mk].sum()),
                        f"{part}_win": f"{(ret[mk] > 0).mean():.3f}->{(alt[mk] > 0).mean():.3f}",
                        f"{part}_gain": round(dl[mk].mean(), 3), f"{part}_vs_random": round(dl[mk].mean() - rnd, 3),
                        f"{part}_days": f"{int((per > 0).sum())}/{len(per)}",
                        f"{part}_nobestday": round((dl[mk].sum() - byday_sum.max()) / mk.sum(), 3),
                        f"{part}_topkept": round(kept, 3)})
            if part == "test":
                rec["test_per_day"] = ";".join(f"{k[5:]}:{v:+.2f}" for k, v in per.items())
                wd0 = pd.Series(ret[mk]).groupby(dd.day.values).mean().min()
                wd1 = pd.Series(alt[mk]).groupby(dd.day.values).mean().min()
                rec["test_worstday"] = f"{wd0:+.2f}->{wd1:+.2f}"
        rows.append(rec)
RB = pd.DataFrame(rows)
say("\nB. natural hold rules on the non-council books (alternative = gain at the mark)\n",
    RB[["mark", "rule", "disc_fired", "disc_win", "disc_gain", "disc_vs_random", "disc_days", "test_fired", "test_win",
        "test_gain", "test_vs_random", "test_days", "test_nobestday", "test_topkept", "test_worstday"]].to_string(index=False))
say(RB[["mark", "rule", "test_per_day"]].to_string(index=False))
OUT["B"] = RB.to_dict("records")
say("  t", round(time.time() - T0, 1))

# ── C. thesis / giveback / attribution at the marks: the rest of the trade (ret - gain at mark) ────────────────────
rows = []
for m in (60, 300, 900):
    d = nonc[nonc[f"h{m}_gain_pct"].notna()]
    X = hold_frame(d, m)
    rest = d.ret_pct.values - X.gain_pct.values
    big = d.ret_pct.values >= 30
    groups = {
        "all": np.ones(len(d), bool),
        "ep_against": X.thesis_ep_against.values == 1, "ep_with_or_none": X.thesis_ep_against.values != 1,
        "held_net<0": X.held_net.values < 0, "held_net>0": X.held_net.values > 0,
        "fires_against>0": X.thesis_fires_against_n.values > 0, "fires_with>0": X.thesis_fires_with_n.values > 0,
        "impact_with": X.thesis_impact_with.values == 1, "impact_against": X.thesis_impact_with.values == 0,
        "gbr_top25": X.gbr_pct_min.values >= np.nanquantile(X.gbr_pct_min.values, 0.75),
        "theta>delta": (np.abs(X.at_pct.values) > np.abs(X.ad_pct.values)),
        "iv_down1": X.attr_iv_chg.values <= -1, "iv_up1": X.attr_iv_chg.values >= 1,
        "gain<0&ep_against": (X.gain_pct.values < 0) & (X.thesis_ep_against.values == 1),
        "gain>10&ep_against": (X.gain_pct.values > 10) & (X.thesis_ep_against.values == 1),
    }
    for nm, g in groups.items():
        for part, mk in (("disc", (d.day < SPLIT).values), ("test", (d.day >= SPLIT).values)):
            s = g & mk & np.isfinite(rest)
            if s.sum() < 20:
                continue
            rows.append(dict(mark=m, group=nm, part=part, n=int(s.sum()), rest_mean=round(np.mean(rest[s]), 3),
                             rest_pos=round(np.mean(rest[s] > 0), 3), final_win=round(np.mean(d.ret_pct.values[s] > 0), 3),
                             big_share=round(big[s].mean(), 3)))
RC = pd.DataFrame(rows)
say("\nC. rest of the trade after the mark (final ret - gain at mark, % of entry), non-council\n", RC.to_string(index=False))
OUT["C"] = RC.to_dict("records")
json.dump(OUT, open(os.path.join(W, "analysis3.json"), "w"), indent=1, default=str)
say("done", round(time.time() - T0, 1))
