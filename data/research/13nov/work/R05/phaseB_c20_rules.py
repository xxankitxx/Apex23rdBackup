import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R05 phase B (after the 15:30 close, after phaseB_c20_paths.py all): hold and exit rules for the council books
themselves, walk-forward, on the marks rebuilt from ds_v2.

  exit-now rules   "at mark m, if X, sell now" on every c20-family trade still held at m. X = one condition on the
                   rebuilt continuation photograph (gain, peak, giveback, time since peak, future's favourable move)
                   or on the entry weather (wx_*), or a pair of one of each. Alternative = the mid at m (the engine
                   books on the LTP; mid stands in) and, conservative, the bid.
  hold-longer      "if the book's exit came with Y, keep the trade h more seconds": alternative = the bid h seconds
                   after the exit (a fixed delay, no look-ahead), Y on the exit-request photograph (hexit_req_*,
                   which the engine does take for council books) or the entry weather.
Discovery = 19 Oct to 4 Nov; test = 5 Nov to 11 Nov (12 Nov has no ds_v2). The pre-registered filter: fires on >= 25
discovery trades over >= 5 discovery days, positive in total and on >= 70 % of the discovery days it fires on. Every
rule that passes is then scored once on the test days, and the best few are run through the Conductor's account
(the five pool books, docs/28 s7 priority) day by day. Reports the number of rules scanned at each step.

Usage: py -3.13 phaseB_c20_rules.py [TAG=all] [--nopairs]   -> work/R05/phaseB_c20_rules_<TAG>.json and .txt"""
import json, os, time
import numpy as np
import pandas as pd
T0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R05"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
TAG = ARGS[0] if ARGS else "all"
PAIRS = "--nopairs" not in sys.argv          # pairs off if a run nears the 3-minute limit
SPLIT = "2026-11-05"
LOG = open(os.path.join(W, f"phaseB_c20_rules_{TAG}.txt"), "w", encoding="utf-8")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n"); LOG.flush()


exec(open(os.path.join(W, "rulelib.py"), encoding="utf-8").read())
P = pd.read_pickle(os.path.join(W, f"c20_paths_{TAG}.pkl"))
df = pd.read_pickle(os.path.join(W, "tr.pkl"))
c20 = df[df.book.str.startswith("c20")]
wxc = [c for c in df.columns if c.startswith("wx_") and not c.startswith(TELE)]
hx = [c for c in df.columns if c.startswith("hexit_req_")]
PW = P.merge(c20[["day", "book", "t_in", "dte_in"] + wxc + hx], on=["day", "book", "t_in"], how="left")
del df
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
PRI = {b: i for i, b in enumerate(POOL)}
say("paths", PW.shape, "days", PW.day.nunique(), "pool trades", int(PW.book.isin(PRI).sum()), round(time.time() - T0, 1))
OUT = {"marks": {}, "longer": {}, "conductor": []}
S = [60, 120, 180, 300, 450, 600, 900, 1200, 1800]
HF = ["gain_pct", "peak_pct", "gain_vs_peak", "giveback_share", "time_to_peak_s", "peak_age_s", "fut_fav_pts",
      "fut_best_fav_pts", "fut_giveback_pts"]


def scan(d, X, delta, label, pairs=True):
    days = sorted(d.day.unique())
    dc = d.day.map({x: i for i, x in enumerate(days)}).values
    Dm = np.zeros((len(d), len(days)), np.float32); Dm[np.arange(len(d)), dc] = 1
    disc = (d.day < SPLIT).values
    dd_ = [i for i, x in enumerate(days) if x < SPLIT]; td_ = [i for i, x in enumerate(days) if x >= SPLIT]
    nd, nt = max(disc.sum(), 1), max((~disc).sum(), 1)
    dl = delta.astype(np.float32)
    res = []

    def add(B, L, tagk):
        if B.shape[1] == 0:
            return
        Bf = B.astype(np.float32)
        per = (Bf * dl[:, None]).T @ Dm
        nf = Bf.T @ Dm
        for k, lab in enumerate(L):
            pdisc, ndisc = per[k, dd_], nf[k, dd_]
            fd = ndisc > 0
            res.append(dict(kind=tagk, rule=lab, n_disc=int(ndisc.sum()), days_fire_disc=int(fd.sum()),
                            gain_disc=float(pdisc.sum() / nd), pos_days_disc=float((pdisc[fd] > 0).mean()) if fd.any() else 0.0,
                            n_test=int(nf[k, td_].sum()), gain_test=float(per[k, td_].sum() / nt),
                            test_days=";".join(f"{days[i][5:]}:{per[k, i] / max((dc == i).sum(), 1):+.2f}/{int(nf[k, i])}" for i in td_)))
    BH, LH = conds(X, disc, [c for c in HF if c in X], [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95])
    add(BH, [("H",) + l for l in LH], "H")
    for s0 in range(0, len(wxc), 80):
        WX = d[wxc[s0:s0 + 80]].astype(float)
        B, L = conds(WX, disc, list(WX.columns), [0.1, 0.25, 0.5, 0.75, 0.9], both=False)
        add(B, [("W",) + l for l in L], "W")
        if pairs and BH.shape[1]:
            for kh in range(BH.shape[1]):
                if BH[disc, kh].sum() < 25:
                    continue
                add(B & BH[:, [kh]], [(("H",) + LH[kh], ("W",) + l) for l in L], "HW")
    R = pd.DataFrame(res)
    if not len(R):
        return R, R
    ok = (R.n_disc >= 25) & (R.days_fire_disc >= 5) & (R.gain_disc > 0) & (R.pos_days_disc >= 0.7)
    sel = R[ok].sort_values("gain_disc", ascending=False)
    say(f"  {label}: scanned {len(R)}; passed {len(sel)}; positive on test: passed "
        f"{(sel.gain_test > 0).mean() if len(sel) else float('nan'):.2f} vs all {(R.gain_test > 0).mean():.2f}")
    return R, sel


def fire_any(d, X, rule):
    if isinstance(rule[0], tuple):                 # a pair
        return fire(d, X, rule[0]) & fire(d, X, rule[1])
    return fire(d, X, rule)


best = []
for m in S:
    X = path_frame(PW, m)
    if X is None:
        continue
    ok = X.gain_pct.notna().values
    d, Xm = PW[ok], X[ok]
    if len(d) < 150:
        continue
    for basis in ("mid", "bid"):
        delta = Xm[f"alt_{basis}"].values - d.ret_pct.values
        R, sel = scan(d, Xm, delta, f"m{m} {basis}", pairs=(basis == "mid" and PAIRS))
        OUT["marks"][f"{m}_{basis}"] = dict(n=int(len(d)), scanned=int(len(R)), passed=int(len(sel)),
                                            pos_test_passed=float((sel.gain_test > 0).mean()) if len(sel) else None,
                                            pos_test_all=float((R.gain_test > 0).mean()) if len(R) else None,
                                            top=sel.head(15).astype(str).to_dict("records"))
        if len(sel):
            say(sel.head(10)[["kind", "rule", "n_disc", "days_fire_disc", "gain_disc", "pos_days_disc", "n_test", "gain_test",
                              "test_days"]].to_string(index=False))
        if basis == "mid":
            for _, r in sel.head(3).iterrows():
                best.append((m, r.rule))
    say("  t", round(time.time() - T0, 1))

# ── hold longer after the book's own exit ───────────────────────────────────────────────────────────────────────
for h in (60, 120, 300, 600, 900):
    col = f"xb{h}"
    if col not in PW:
        continue
    ok = PW[col].notna().values
    d = PW[ok]
    alt = 100 * (d[col] - d.entry) / d.entry
    delta = (alt - d.ret_pct).values
    X = pd.DataFrame(index=d.index)
    e = d.entry.astype(float)
    X["gain_pct"] = d.get("hexit_req_gain_pct")
    X["peak_pct"] = 100 * d.get("hexit_req_peak_pts") / e
    X["giveback_share"] = d.get("hexit_req_giveback_share")
    X["peak_age_s"] = d.get("hexit_req_peak_age_s")
    X["time_to_peak_s"] = d.get("hexit_req_time_to_peak_s")
    X["fut_fav_pts"] = d.get("hexit_req_fut_fav_pts")
    X["hold_s"] = d.hold_s
    X["held_net"] = d.get("hexit_req_thesis_held_with_n") - d.get("hexit_req_thesis_held_against_n")
    X["fires_net"] = d.get("hexit_req_thesis_fires_with_n") - d.get("hexit_req_thesis_fires_against_n")
    X["ep_against"] = pd.to_numeric(d.get("hexit_req_thesis_ep_against"), errors="coerce")
    HF_save = HF
    HF = list(X.columns)
    say(f"\nhold {h}s longer: all trades {delta.mean():+.3f} %/trade (disc {delta[(d.day < SPLIT).values].mean():+.3f}, "
        f"test {delta[(d.day >= SPLIT).values].mean():+.3f})")
    R, sel = scan(d, X, delta, f"longer {h}", pairs=False)
    HF = HF_save
    OUT["longer"][str(h)] = dict(n=int(len(d)), all_gain=float(delta.mean()), scanned=int(len(R)), passed=int(len(sel)),
                                 pos_test_passed=float((sel.gain_test > 0).mean()) if len(sel) else None,
                                 top=sel.head(15).astype(str).to_dict("records"))
    if len(sel):
        say(sel.head(10)[["kind", "rule", "n_disc", "gain_disc", "pos_days_disc", "n_test", "gain_test", "test_days"]].to_string(index=False))

# ── the Conductor on every rebuilt day, best exit-now rules ─────────────────────────────────────────────────────
pool = PW[PW.book.isin(PRI)].copy()
cc = c20[c20.book.isin(PRI)][["day", "book", "t_in", "trigger_t"]]
pool = pool.merge(cc, on=["day", "book", "t_in"], how="left")
pool["trig"] = pool.trigger_t.fillna(pool.t_in)
pool["pri"] = pool.book.map(PRI)


def account(tr, ret_col="ret_pct", tout_col="t_out"):
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


for m, rule in best:
    X = path_frame(pool, m)
    for basis in ("mid", "bid"):
        f = fire_any(pool, X, rule) & X.gain_pct.notna().values
        g = pool.assign(ret2=np.where(f, X[f"alt_{basis}"].values, pool.ret_pct.values),
                        tout2=np.where(f, pool.t_in + m, pool.t_out))
        rows = []
        for day, gd in g.groupby("day"):
            a, b = account(gd, "ret2", "tout2"), account(gd)
            rows.append(dict(day=day, test=day >= SPLIT, rule_ret=100 * (a[-1][2] / 1e5 - 1) if a else 0.0,
                             base_ret=100 * (b[-1][2] / 1e5 - 1) if b else 0.0, n=len(a), won=sum(1 for x in a if x[1] > 0),
                             n0=len(b), won0=sum(1 for x in b if x[1] > 0)))
        Rr = pd.DataFrame(rows)
        for part, q in (("disc", ~Rr.test), ("test", Rr.test)):
            z = Rr[q]
            if not len(z):
                continue
            OUT["conductor"].append(dict(mark=m, rule=str(rule), basis=basis, part=part,
                                         strike=f"{z.won.sum()}/{z.n.sum()} vs {z.won0.sum()}/{z.n0.sum()}",
                                         mean_day=f"{z.rule_ret.mean():+.2f} vs {z.base_ret.mean():+.2f}",
                                         days_better=int((z.rule_ret > z.base_ret).sum()), days=int(len(z)),
                                         losing_days=f"{int((z.rule_ret < 0).sum())} vs {int((z.base_ret < 0).sum())}",
                                         worst=f"{z.rule_ret.min():+.2f} vs {z.base_ret.min():+.2f}",
                                         per_day=";".join(f"{a[5:]}:{b_:+.1f}/{c_:+.1f}" for a, b_, c_ in zip(z.day, z.rule_ret, z.base_ret))))
say("\nConductor with the best rules (rule vs base)\n", pd.DataFrame(OUT["conductor"]).to_string(index=False) if OUT["conductor"] else "none")
json.dump(OUT, open(os.path.join(W, f"phaseB_c20_rules_{TAG}.json"), "w"), indent=1, default=str)
say("done", round(time.time() - T0, 1))
