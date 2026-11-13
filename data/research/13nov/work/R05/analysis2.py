import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R05 analysis 2: the rules that passed the pre-registered discovery filter in analysis 1, scored on the test days
in full (per day, strike rate, big-winner retention, without best trade / best day, by family); hold-state x weather
pairs; the Conductor account re-simulated from the pool books' trades (check against conductor_sim), and the
transferable rules applied to the c20 trades and the Conductor on the days whose quotes were rebuilt
(c20_paths_<tag>.pkl, ds_v2). Reads work/R05 files only."""
import json, os, time
import numpy as np
import pandas as pd
T0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R05"
TAG = sys.argv[1] if len(sys.argv) > 1 else "pilot"
DO_PAIRS = "--nopairs" not in sys.argv
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
SPLIT = "2026-11-05"
OUT = {}


def say(*a):
    print(*a, flush=True)


df = pd.read_pickle(os.path.join(W, "tr.pkl"))
R = pd.read_pickle(os.path.join(W, "rules_scan1.pkl"))
say("loaded", df.shape, R.shape, round(time.time() - T0, 1))


def fam(b):
    for p in ("rx_", "hx_", "fx_", "fh_"):
        if b.startswith(p):
            return "twin"
    if b.startswith("c20"):
        return "c20"
    return b.split("_")[0] if "_" in b else b


df["fam"] = df.book.map(fam)
nonc = df[(df.fam != "c20") & (df.fam != "twin")]
exec(open(os.path.join(W, "rulelib.py"), encoding="utf-8").read())   # hold_frame, fire()

# ── 1. the rules that passed discovery: full test-day scoring ───────────────────────────────────────────────────
sc = R[R.scope == "non_council"]
passed = sc[(sc.n_disc >= 40) & (sc.days_fire_disc >= 6) & (sc.gain_disc > 0) & (sc.pos_days_disc >= 0.7)]
say("non-council rules scanned", len(sc), "passed discovery", len(passed),
    "share positive on test: passed", round((passed.gain_test > 0).mean(), 3), "all scanned", round((sc.gain_test > 0).mean(), 3))
for m in sorted(sc.mark.unique()):
    a, p = sc[sc.mark == m], passed[passed.mark == m]
    say(f"  m{m}: scanned {len(a)} passed {len(p)}; positive on test: passed {(p.gain_test > 0).mean() if len(p) else np.nan:.2f}"
        f" vs all {(a.gain_test > 0).mean():.2f}; mean test gain passed {p.gain_test.mean() if len(p) else np.nan:+.3f} vs all {a.gain_test.mean():+.3f}")
OUT["scan_summary"] = dict(n_scanned=int(len(sc)), n_passed=int(len(passed)),
                           pos_test_passed=float((passed.gain_test > 0).mean()) if len(passed) else None,
                           pos_test_all=float((sc.gain_test > 0).mean()))
SEL = passed.sort_values("gain_disc", ascending=False).groupby("mark").head(8)


def full_score(d, m, rule, label):
    """every number of the owner's standard for one exit rule on one set of trades (marks present)."""
    d = d[d[f"h{m}_gain_pct"].notna()]
    X = hold_frame(d, m)
    f = fire(d, X, rule)
    alt = np.where(f, X.gain_pct.values, d.ret_pct.values)
    ret = d.ret_pct.values
    dl = alt - ret
    res = {}
    for part, mk in (("disc", (d.day < SPLIT).values), ("test", (d.day >= SPLIT).values)):
        if not mk.any():
            continue
        dd = d[mk]
        per = pd.Series(dl[mk]).groupby(dd.day.values).mean()
        top = ret[mk] >= np.quantile(ret[mk], 0.9)
        kept = ~f[mk][top] | (alt[mk][top] >= 0.67 * ret[mk][top])
        tot = dl[mk].sum()
        by_day = pd.Series(dl[mk]).groupby(dd.day.values).sum()
        res[part] = dict(n=int(mk.sum()), fired=int(f[mk].sum()), win_base=float((ret[mk] > 0).mean()),
                         win_rule=float((alt[mk] > 0).mean()), ret_base=float(ret[mk].mean()), ret_rule=float(alt[mk].mean()),
                         gain=float(dl[mk].mean()), days_pos=int((per > 0).sum()), days=int(len(per)),
                         worst_day_base=float(pd.Series(ret[mk]).groupby(dd.day.values).mean().min()),
                         worst_day_rule=float(pd.Series(alt[mk]).groupby(dd.day.values).mean().min()),
                         no_best_trade=float((tot - dl[mk].max()) / mk.sum()), no_best_day=float((tot - by_day.max()) / mk.sum()),
                         top_kept=float(kept.mean()), per_day={k[5:]: round(v, 3) for k, v in per.items()})
        if part == "test":
            fm_ = pd.Series(dl[mk]).groupby(dd.fam.values).agg(["mean", "size"])
            res["test_by_family"] = {k: (round(v["mean"], 3), int(v["size"])) for k, v in fm_.iterrows()}
    return res


rows = []
for _, r in SEL.iterrows():
    rule = (r.kind, r.feat, r.op, r.thr)
    try:
        s = full_score(nonc, int(r.mark), rule, "")
    except Exception as ex:
        say("score failed", rule, ex)
        continue
    t, dsc = s.get("test", {}), s.get("disc", {})
    rows.append(dict(mark=int(r.mark), kind=r.kind, feat=r.feat, op=r.op, thr=round(r.thr, 4),
                     disc_gain=round(dsc.get("gain", np.nan), 3), disc_days=f"{dsc.get('days_pos')}/{dsc.get('days')}",
                     test_n=t.get("n"), test_fired=t.get("fired"), test_win=f"{t.get('win_base', 0):.3f}->{t.get('win_rule', 0):.3f}",
                     test_gain=round(t.get("gain", np.nan), 3), test_days=f"{t.get('days_pos')}/{t.get('days')}",
                     no_best_day=round(t.get("no_best_day", np.nan), 3), no_best_trade=round(t.get("no_best_trade", np.nan), 3),
                     worst_day=f"{t.get('worst_day_base', 0):+.2f}->{t.get('worst_day_rule', 0):+.2f}",
                     top_kept=round(t.get("top_kept", np.nan), 3), per_day=t.get("per_day"), fam=s.get("test_by_family")))
S1 = pd.DataFrame(rows)
say("\n1. selected non-council rules, full test scoring\n",
    S1.drop(columns=["fam"]).to_string(index=False) if len(S1) else "none")
if len(S1):
    for _, r in S1.iterrows():
        say("   fam", r.mark, r.feat, r.op, r.thr, r.fam)
OUT["selected"] = S1.to_dict("records")

# ── 2. hold-state x weather pairs (marks 300 and 900) ───────────────────────────────────────────────────────────
NAT = [("gain_pct", "<=", 0.0), ("gain_pct", "<=", -5.0), ("peak_pct", "<=", 5.0), ("peak_pct", "<=", 10.0),
       ("giveback_share", ">=", 0.5), ("fut_fav_pts", "<=", 0.0), ("fut_fav_pts", "<=", -10.0),
       ("thesis_ep_against", ">=", 1.0), ("held_net", "<=", -1.0), ("fires_net", "<=", -1.0),
       ("attr_iv_chg", "<=", -1.0), ("gain_pct", ">=", 20.0), ("peak_age_s", ">=", 120.0)]
if DO_PAIRS:
    wxc = [c for c in df.columns if c.startswith("wx_") and not c.startswith(TELE)]
    PR = []
    for m in (300, 900):
        d = nonc[nonc[f"h{m}_gain_pct"].notna()]
        X = hold_frame(d, m)
        dl = (X.gain_pct.values - d.ret_pct.values).astype(np.float32)
        days = sorted(d.day.unique())
        dc = d.day.map({x: i for i, x in enumerate(days)}).values
        Dm = np.zeros((len(d), len(days)), np.float32); Dm[np.arange(len(d)), dc] = 1
        disc = (d.day < SPLIT).values
        dd_ = [i for i, x in enumerate(days) if x < SPLIT]; td_ = [i for i, x in enumerate(days) if x >= SPLIT]
        nd, nt = disc.sum(), (~disc).sum()
        for h in NAT:
            hm = fire(d, X, ("H",) + h)
            if hm[disc].sum() < 40:
                continue
            for s0 in range(0, len(wxc), 80):
                WX = d[wxc[s0:s0 + 80]].astype(float)
                B, L = conds(WX, disc, list(WX.columns), [0.1, 0.25, 0.5, 0.75, 0.9], both=False)
                if B.shape[1] == 0:
                    continue
                Bh = B & hm[:, None]
                per = (Bh.astype(np.float32) * dl[:, None]).T @ Dm
                nf = Bh.astype(np.float32).T @ Dm
                for k, lab in enumerate(L):
                    pdisc, ndisc = per[k, dd_], nf[k, dd_]
                    fd = ndisc > 0
                    if ndisc.sum() < 30 or fd.sum() < 5:
                        continue
                    PR.append(dict(mark=m, h=f"{h[0]}{h[1]}{h[2]}", feat=lab[0], op=lab[1], thr=lab[2], n_disc=int(ndisc.sum()),
                                   days_fire_disc=int(fd.sum()), gain_disc=float(pdisc.sum() / nd),
                                   pos_days_disc=float((pdisc[fd] > 0).mean()), n_test=int(nf[k, td_].sum()),
                                   gain_test=float(per[k, td_].sum() / max(nt, 1)),
                                   pos_days_test=float((per[k, td_][nf[k, td_] > 0] > 0).mean()) if (nf[k, td_] > 0).any() else np.nan,
                                   test_days=";".join(f"{days[i][5:]}:{per[k, i] / max((dc == i).sum(), 1):+.2f}/{int(nf[k, i])}" for i in td_)))
        say("   pairs m", m, "so far", len(PR), round(time.time() - T0, 1))
    P2 = pd.DataFrame(PR)
    P2.to_pickle(os.path.join(W, "rules_pairs.pkl"))
    if len(P2):
        pp = P2[(P2.gain_disc > 0) & (P2.pos_days_disc >= 0.75) & (P2.days_fire_disc >= 6)]
        say(f"\n2. pairs scanned {len(P2)}; passed discovery {len(pp)}; positive on test: passed {(pp.gain_test > 0).mean() if len(pp) else np.nan:.2f}"
            f" vs all {(P2.gain_test > 0).mean():.2f}")
        say(pp.sort_values("gain_disc", ascending=False).groupby("mark").head(12).round(3).to_string(index=False))
        OUT["pairs"] = dict(n=int(len(P2)), passed=int(len(pp)),
                            pos_test_passed=float((pp.gain_test > 0).mean()) if len(pp) else None,
                            pos_test_all=float((P2.gain_test > 0).mean()))

# ── 3. the Conductor account re-simulated from the pool books' trades ───────────────────────────────────────────
POOL = [("c20_9y", 12.088), ("c20_9s", 11.441), ("c20_9v", 9.897), ("c20_9x", 9.605), ("c20_9t", 4.385)]
PRI = {b: i for i, (b, _) in enumerate(POOL)}
pool = df[df.book.isin(PRI)].copy()
pool["trig"] = pool.trigger_t.fillna(pool.t_in)
pool["pri"] = pool.book.map(PRI)


def account(tr, ret_col="ret_pct", tout_col="t_out"):
    """docs/28 s7 / account_sim.simulate_day on one day: first trigger while flat takes the account (priority on the
    same second), held to its (possibly modified) exit; all-in, compounding. Lots from capital // (entry x 65)."""
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
        px_out = t.entry * (1 + t[ret_col] / 100.0)
        pnl = (px_out - t.entry) * lots * 65
        cap += pnl
        held = (t.trig, t[tout_col], t.book)
        out.append(dict(book=t.book, t_in=t.t_in, trig=t.trig, ret=t[ret_col], pnl=pnl, cap=cap))
    return out


C = pd.read_pickle(os.path.join(W, "cond.pkl"))
chk = []
for day, g in pool.groupby("day"):
    a = account(g)
    c = C[C.day == day]
    chk.append(dict(day=day, sim_n=len(a), cond_n=len(c), sim_ret=round(100 * (a[-1]["cap"] / 1e5 - 1), 2) if a else 0.0,
                    cond_ret=round(100 * (c.capital_after.iloc[-1] / 1e5 - 1), 2) if len(c) else 0.0,
                    same=bool(len(a) == len(c) and all(abs(x["t_in"] - y) < 1 for x, y in zip(a, c.t_in)))))
CK = pd.DataFrame(chk)
say("\n3. account re-simulation vs conductor_sim\n", CK.to_string(index=False))
OUT["account_check"] = CK.to_dict("records")

# ── 4. transferable rules on the rebuilt c20 paths (ds_v2) ──────────────────────────────────────────────────────
pp_ = os.path.join(W, f"c20_paths_{TAG}.pkl")
if os.path.exists(pp_):
    Pth = pd.read_pickle(pp_)
    say("\n4. c20 paths", Pth.shape, sorted(Pth.day.unique()))
    # calibration: mid / bid at the exit second against the booked (LTP) exit
    cal = (100 * (Pth.bid_out - Pth.exit) / Pth.entry).describe().round(3).to_dict()
    say("   bid at exit vs booked exit, % of entry:", cal)
    say("   ask at entry vs booked entry, % of entry:", (100 * (Pth.ask_in - Pth.entry) / Pth.entry).describe().round(3).to_dict())
    wx_ = df[df.book.str.startswith("c20")][["day", "book", "t_in"] + [c for c in df.columns if c.startswith("wx_")]]
    PW = Pth.merge(wx_, on=["day", "book", "t_in"], how="left")
    TR = []
    rules_t = [(int(r.mark), (r.kind, r.feat, r.op, r.thr)) for _, r in SEL.iterrows()]
    rules_t += [(m, ("H",) + h) for m in (300, 900) for h in NAT]
    for m, rule in rules_t:
        X = path_frame(PW, m)
        if X is None:
            continue
        ok = X.gain_pct.notna().values
        try:
            f = fire(PW, X, rule) & ok
        except KeyError:
            continue                                  # a feature the rebuilt path does not have (thesis, attribution)
        for basis in ("mid", "bid"):
            alt = np.where(f, X[f"alt_{basis}"].values, PW.ret_pct.values)
            dl = alt - PW.ret_pct.values
            pool_m = PW.book.isin(PRI).values
            TR.append(dict(mark=m, rule=f"{rule[0]}:{rule[1]}{rule[2]}{rule[3]:.4g}", basis=basis, n=int(ok.sum()),
                           fired=int(f.sum()), fired_pool=int((f & pool_m).sum()),
                           gain_all=round(float(dl[ok].mean()), 3) if ok.any() else np.nan,
                           gain_pool=round(float(dl[ok & pool_m].mean()), 3) if (ok & pool_m).any() else np.nan,
                           win=f"{(PW.ret_pct.values[ok] > 0).mean():.2f}->{(alt[ok] > 0).mean():.2f}" if ok.any() else ""))
    T4 = pd.DataFrame(TR)
    say(T4.to_string(index=False))
    OUT["c20_transfer"] = T4.to_dict("records")
    # Conductor on the rebuilt days, every rule (mid basis = the engine's LTP convention; bid = conservative)
    CR = []
    days = sorted(Pth.day.unique())
    base = {d_: account(pool[pool.day == d_]) for d_ in days}
    for m, rule in rules_t:
        for basis in ("mid", "bid"):
            per = {}
            for d_ in days:
                g = pool[pool.day == d_].merge(PW[["day", "book", "t_in"]].assign(_i=np.arange(len(PW))), on=["day", "book", "t_in"], how="left")
                X = path_frame(PW, m)
                if X is None:
                    continue
                try:
                    fA = fire(PW, X, rule) & X.gain_pct.notna().values
                except KeyError:
                    per = None
                    break
                altA = X[f"alt_{basis}"].values
                ii = g._i.values
                has = np.isfinite(ii.astype(float))
                fg = np.zeros(len(g), bool)
                fg[has] = fA[ii[has].astype(int)]
                g["ret2"] = g.ret_pct.values
                g.loc[fg, "ret2"] = altA[ii[fg].astype(int)]
                g["tout2"] = np.where(fg, g.t_in + m, g.t_out)
                a = account(g, "ret2", "tout2")
                b0 = base[d_]
                per[d_] = (round(100 * (a[-1]["cap"] / 1e5 - 1), 2) if a else 0.0, round(100 * (b0[-1]["cap"] / 1e5 - 1), 2) if b0 else 0.0,
                           len(a), sum(1 for x in a if x["ret"] > 0), len(b0), sum(1 for x in b0 if x["ret"] > 0))
            if per:
                CR.append(dict(mark=m, rule=f"{rule[0]}:{rule[1]}{rule[2]}{rule[3]:.4g}", basis=basis,
                               days=";".join(f"{k[5:]}:{v[0]:+.1f}(base {v[1]:+.1f}) {v[3]}/{v[2]} vs {v[5]}/{v[4]}" for k, v in per.items())))
    say("\n   Conductor on the rebuilt days\n", pd.DataFrame(CR).to_string(index=False) if CR else "none")
    OUT["cond_transfer"] = CR
json.dump(OUT, open(os.path.join(W, f"analysis2_{TAG}.json"), "w"), indent=1, default=str)
say("done", round(time.time() - T0, 1))
