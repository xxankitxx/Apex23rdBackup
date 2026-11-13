import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R05 analysis 1: fill conventions, mark coverage, the Conductor's exits and the exit-time photograph, and the
walk-forward search of "at mark m, if X, exit now" rules on every trade that has hold marks.
Discovery = 19 Oct to 4 Nov, test = 5 Nov to 12 Nov. Reads work/R05/tr.pkl and cond.pkl only."""
import json, os, time
import numpy as np
import pandas as pd
T0 = time.time()
W = r"D:\ApexOptions\data\research\13nov\work\R05"
OUT = {}
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 40)


def say(*a):
    print(*a, flush=True)


df = pd.read_pickle(os.path.join(W, "tr.pkl"))
C = pd.read_pickle(os.path.join(W, "cond.pkl"))
say("loaded", df.shape, C.shape, round(time.time() - T0, 1))
SPLIT = "2026-11-05"
df["test"] = df.day >= SPLIT
df["exp"] = (df.dte_in.fillna(9) < 0.5).astype(int) if "dte_in" in df else 0


def fam(b):
    for p in ("rx_", "hx_", "fx_", "fh_"):
        if b.startswith(p):
            return "twin"
    if b.startswith("c20"):
        return "c20"
    return b.split("_")[0] if "_" in b else b


df["fam"] = df.book.map(fam)
MARKS = [60, 300, 900, 1800]

# ── A. fill conventions ─────────────────────────────────────────────────────────────────────────────────────────
try:
    e, ea, eb = df.entry, df.entry_ask, df.entry_bid
    x, xb, xa = df.exit, df.exit_bid, df.exit_ask
    ok = ea.notna() & eb.notna() & (ea > 0) & (eb > 0)
    sp = (ea - eb) / e * 100
    A = {"entry_eq_ask": float((np.isclose(e, ea) & ok).mean()), "entry_eq_bid": float((np.isclose(e, eb) & ok).mean()),
         "entry_between": float(((e >= eb - 1e-9) & (e <= ea + 1e-9) & ok).mean()),
         "exit_eq_bid": float((np.isclose(x, xb)).mean()), "exit_eq_ask": float((np.isclose(x, xa)).mean()),
         "spread_pct_med": float(sp[ok].median()), "spread_pct_c20_med": float(sp[ok & (df.fam == "c20")].median()),
         "ret_minus_bidask_ret_med": float((df.ret_pct - 100 * (xb - ea) / ea)[ok & xb.notna()].median())}
    OUT["fill"] = A
    say("A fills", json.dumps(A))
except Exception as ex:
    say("A failed", ex)

# ── B. mark coverage by family ──────────────────────────────────────────────────────────────────────────────────
cov = df.groupby("fam").agg(n=("ret_pct", "size"), books=("book", "nunique"),
                            h60=("h60_gain_pct", lambda s: round(s.notna().mean(), 3)),
                            h300=("h300_gain_pct", lambda s: round(s.notna().mean(), 3)),
                            h900=("h900_gain_pct", lambda s: round(s.notna().mean(), 3)),
                            h1800=("h1800_gain_pct", lambda s: round(s.notna().mean(), 3)),
                            hreq=("hexit_req_gain_pct", lambda s: round(s.notna().mean(), 3)),
                            hexit=("hexit_gain_pct", lambda s: round(s.notna().mean(), 3)),
                            held300=("hold_s", lambda s: round((s >= 300).mean(), 3)),
                            win=("ret_pct", lambda s: round((s > 0).mean(), 3)), ret=("ret_pct", "mean"))
say("B coverage\n", cov.sort_values("n", ascending=False).to_string())
OUT["coverage"] = cov.reset_index().to_dict("records")
c20b = df[df.fam == "c20"]
say("c20 books", c20b.groupby("book").size().to_dict())
say("c20 fut_best_fav at exit_req (should vary if the future best is tracked):",
    c20b.hexit_req_fut_best_fav_pts.describe().round(2).to_dict())
say("c20 hexit_req giveback_share", c20b.hexit_req_giveback_share.describe().round(3).to_dict())

# calibration: the photograph's ltp gain at the exit request against the booked return
for nm in ("hexit_req", "hexit"):
    d = (df[f"{nm}_gain_pct"] - df.ret_pct).dropna()
    say(f"calib {nm}_gain_pct - ret_pct: n={len(d)} med={d.median():.2f} p10={d.quantile(.1):.2f} p90={d.quantile(.9):.2f}")

# ── C. the Conductor's trades with their own book's row ─────────────────────────────────────────────────────────
C["book"] = C.src
key = ["day", "book", "t_in"]
M = C.merge(df.drop(columns=["ret_pct", "entry", "exit", "lots", "qty", "pnl_rs", "reason", "why", "key", "strike", "rr",
                             "time_in", "time_out", "t_out", "trigger_t"], errors="ignore"), on=key, how="left",
            suffixes=("", "_b"))
say("C matched", int(M.hold_s.notna().sum()), "of", len(M))
M["peak_pct"] = 100 * M.peak_pts / M.entry
M["give"] = M.peak_pct - M.ret_pct
M["win"] = M.ret_pct > 0
M["test"] = M.day >= SPLIT
M["rsn"] = M.reason.str.replace("COUNCIL ", "", regex=False).str.replace(r"\(.*\)", "", regex=True).str.strip()
r = M.groupby("rsn").agg(n=("ret_pct", "size"), win=("win", "mean"), ret=("ret_pct", "mean"), peak=("peak_pct", "mean"),
                         give=("give", "mean"), hold_min=("hold_s", lambda s: s.median() / 60))
say("C by exit reason\n", r.round(2).sort_values("n", ascending=False).to_string())
OUT["cond_by_reason"] = r.round(3).reset_index().to_dict("records")
# day compounding
def dayret(g, col="ret_pct"):
    return 100 * (np.prod(1 + g[col].values / 100) - 1)
dd = M.groupby("day").apply(lambda g: pd.Series({"n": len(g), "won": int(g.win.sum()), "ret": dayret(g),
                                                  "peak_mean": g.peak_pct.mean(), "give_mean": g.give.mean(),
                                                  "exp": int((g.dte_in.fillna(9) < 0.5).any())}))
say("C by day\n", dd.round(1).to_string())
OUT["cond_by_day"] = dd.round(3).reset_index().to_dict("records")
M["pk_b"] = pd.cut(M.peak_pct, [-1e9, 0, 5, 10, 15, 25, 50, 1e9])
pk = M.groupby("pk_b", observed=True).agg(n=("ret_pct", "size"), win=("win", "mean"), ret=("ret_pct", "mean"),
                                          give=("give", "mean"))
say("C by peak bucket\n", pk.round(2).to_string())
OUT["cond_by_peak"] = {str(k): v for k, v in pk.round(3).to_dict("index").items()}
# attribution at the exit request (first-order: delta x future move, theta x time, residual = IV, gamma, quote)
for c in ("attr_delta_pts", "attr_theta_pts", "attr_resid_pts"):
    M[c + "_pct"] = 100 * M["hexit_req_" + c] / M.entry
M["attr_iv"] = M.hexit_req_attr_iv_chg
at = M.groupby("win").agg(n=("ret_pct", "size"), ret=("ret_pct", "mean"), d=("attr_delta_pts_pct", "mean"),
                          th=("attr_theta_pts_pct", "mean"), res=("attr_resid_pts_pct", "mean"), iv=("attr_iv", "mean"),
                          futfav=("hexit_req_fut_fav_pts", "mean"), ttp=("hexit_req_time_to_peak_s", "median"),
                          pkage=("hexit_req_peak_age_s", "median"))
say("C attribution at the exit request (per cent of entry premium)\n", at.round(2).to_string())
OUT["cond_attr"] = at.round(3).reset_index().to_dict("records")
at2 = M.groupby(M.dte_in.fillna(9) < 0.5).agg(n=("ret_pct", "size"), ret=("ret_pct", "mean"), d=("attr_delta_pts_pct", "mean"),
                                               th=("attr_theta_pts_pct", "mean"), res=("attr_resid_pts_pct", "mean"),
                                               iv=("attr_iv", "mean"))
say("C attribution by expiry day (True = expiry)\n", at2.round(2).to_string())
# thesis at exit for winners and losers
th = M.groupby("win")[["hexit_req_thesis_ep_against", "hexit_req_thesis_fires_with_n", "hexit_req_thesis_fires_against_n",
                       "hexit_req_thesis_held_with_n", "hexit_req_thesis_held_against_n", "hexit_req_thesis_impact_with"]].mean()
say("C thesis at exit\n", th.round(2).to_string())
# concentration
s = M.sort_values("ret_pct", ascending=False)
say("C top-10 trades by ret:", s[["day", "src", "time_in", "rr", "ret_pct", "peak_pct", "hold_s", "rsn"]].head(12).to_string())
M.to_pickle(os.path.join(W, "cond_m.pkl"))

# ── D. mark rules: "at mark m, if X, exit now" (alternative = the photograph's gain at the mark, the LTP basis the
#       engine books on), walk-forward ─────────────────────────────────────────────────────────────────────────────
wxc = [c for c in df.columns if c.startswith("wx_")]
# drop telemetry / provenance and near-constant items
TELE = ("wx_eng_", "wx_save_", "wx_lin_", "wx_sync_", "wx_req_", "wx_sig_age", "wx_reconnects", "wx_feed_state",
        "wx_chain_age", "wx_depth_age", "wx_fut_age", "wx_spot_age", "wx_quote_age", "wx_n_hero")
wxc = [c for c in wxc if not c.startswith(TELE)]
HF = ["gain_pct", "peak_pct", "gain_vs_peak", "giveback_share", "gbr_pct_min", "time_to_peak_s", "peak_age_s", "worst_pct",
      "fut_fav_pts", "fut_best_fav_pts", "fut_giveback_pts", "ad_pct", "at_pct", "attr_iv_chg", "ares_pct",
      "thesis_ep_against", "thesis_fires_with_n", "thesis_fires_against_n", "fires_net", "thesis_held_with_n",
      "thesis_held_against_n", "held_net", "held_with_share", "thesis_impact_with"]
QS = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95]
ALLRES = []


def hold_frame(d, m):
    p = f"h{m}_"
    X = pd.DataFrame(index=d.index)
    e = d.entry.astype(float)
    X["gain_pct"] = d[p + "gain_pct"]
    X["peak_pct"] = 100 * d[p + "peak_pts"] / e
    X["gain_vs_peak"] = d[p + "gain_vs_peak"]
    X["giveback_share"] = d[p + "giveback_share"]
    X["gbr_pct_min"] = 100 * d[p + "giveback_rate_pts_min"] / e
    X["time_to_peak_s"] = d[p + "time_to_peak_s"]
    X["peak_age_s"] = d[p + "peak_age_s"]
    X["worst_pct"] = 100 * d[p + "worst_pts"] / e
    for c in ("fut_fav_pts", "fut_best_fav_pts", "fut_giveback_pts", "attr_iv_chg"):
        X[c] = d[p + c]
    X["ad_pct"] = 100 * d[p + "attr_delta_pts"] / e
    X["at_pct"] = 100 * d[p + "attr_theta_pts"] / e
    X["ares_pct"] = 100 * d[p + "attr_resid_pts"] / e
    for c in ("thesis_ep_against", "thesis_fires_with_n", "thesis_fires_against_n", "thesis_held_with_n",
              "thesis_held_against_n", "thesis_impact_with"):
        X[c] = pd.to_numeric(d[p + c], errors="coerce").astype(float)
    X["fires_net"] = X.thesis_fires_with_n - X.thesis_fires_against_n
    X["held_net"] = X.thesis_held_with_n - X.thesis_held_against_n
    X["held_with_share"] = X.thesis_held_with_n / (X.thesis_held_with_n + X.thesis_held_against_n).replace(0, np.nan)
    return X


def conds(X, disc_mask, names, qs, both=True):
    """Boolean condition matrix (n x K) with thresholds at discovery quantiles; NaN -> False. both=False: the lower
    quantiles test <=, the upper >=, the median both."""
    cols, labs, seen = [], [], set()
    for c in names:
        v = X[c].values.astype(float)
        vd = v[disc_mask & np.isfinite(v)]
        if len(vd) < 50 or np.nanstd(vd) == 0:
            continue
        for qq in qs:
            q = float(np.round(np.quantile(vd, qq), 6))
            with np.errstate(invalid="ignore"):
                lo, hi = v <= q, v >= q
            ops = (("<=", lo), (">=", hi)) if (both or qq == 0.5) else ((("<=", lo),) if qq < 0.5 else ((">=", hi),))
            for op, b in ops:
                if (c, op, q) in seen:
                    continue
                seen.add((c, op, q))
                fr = b[disc_mask].mean()
                if 0.02 <= fr <= 0.8:
                    cols.append(b & np.isfinite(v))
                    labs.append((c, op, float(q)))
    if not cols:
        return np.zeros((len(X), 0), bool), []
    return np.column_stack(cols), labs


def score(B, delta, dayc, ndays, w=None):
    """per condition: n fired, sum delta, per-day sum (K x ndays)."""
    Bf = B.astype(np.float32)
    dl = delta.astype(np.float32)
    Dm = np.zeros((len(dayc), ndays), np.float32)
    Dm[np.arange(len(dayc)), dayc] = 1.0
    per = (Bf * dl[:, None]).T @ Dm          # K x ndays
    nf = Bf.T @ Dm                            # fires per day
    return per, nf


def run_mark(scope_name, d, m, wx_too=True):
    p = f"h{m}_gain_pct"
    d = d[d[p].notna() & d.ret_pct.notna()].copy()
    if len(d) < 200:
        say(f"D {scope_name} m{m}: only {len(d)} trades with the mark, skipped")
        return
    X = hold_frame(d, m)
    alt = X.gain_pct.values.astype(float)
    ret = d.ret_pct.values.astype(float)
    delta = alt - ret
    days = sorted(d.day.unique())
    dayc = d.day.map({x: i for i, x in enumerate(days)}).values
    disc = (d.day < SPLIT).values
    test = ~disc
    dd_ = [i for i, x in enumerate(days) if x < SPLIT]
    td_ = [i for i, x in enumerate(days) if x >= SPLIT]
    names = [c for c in HF if c in X]

    def blocks():
        B1, L1 = conds(X, disc, names, QS)
        yield B1, [("H",) + l for l in L1]
        if wx_too:
            wl = [c for c in wxc if c in d]
            for s0 in range(0, len(wl), 60):        # chunks: keeps the condition matrix small
                WX = d[wl[s0:s0 + 60]].astype(float)
                B2, L2 = conds(WX, disc, list(WX.columns), [0.1, 0.25, 0.5, 0.75, 0.9], both=False)
                yield B2, [("W",) + l for l in L2]
    res = []
    nU_d, nU_t = disc.sum(), test.sum()
    for B, L in blocks():
        if B.shape[1] == 0:
            continue
        per, nf = score(B, delta, dayc, len(days))
        for k, lab in enumerate(L):
            pdisc, ndisc = per[k, dd_], nf[k, dd_]
            ptest, ntest = per[k, td_], nf[k, td_]
            fd = ndisc > 0
            res.append(dict(scope=scope_name, mark=m, kind=lab[0], feat=lab[1], op=lab[2], thr=lab[3],
                            n_disc=int(ndisc.sum()), days_fire_disc=int(fd.sum()),
                            gain_disc=float(pdisc.sum() / nU_d), pos_days_disc=float((pdisc[fd] > 0).mean()) if fd.any() else 0.0,
                            n_test=int(ntest.sum()), gain_test=float(ptest.sum() / max(nU_t, 1)),
                            pos_days_test=float((ptest[ntest > 0] > 0).mean()) if (ntest > 0).any() else np.nan,
                            test_days=";".join(f"{days[i][5:]}:{per[k, i] / max((dayc == i).sum(), 1):+.2f}/{int(nf[k, i])}" for i in td_)))
    R = pd.DataFrame(res)
    R["nU_disc"], R["nU_test"] = int(nU_d), int(nU_t)
    ALLRES.append(R)
    # pre-registered discovery filter
    sel = R[(R.n_disc >= 40) & (R.days_fire_disc >= 6) & (R.gain_disc > 0) & (R.pos_days_disc >= 0.7)]
    sel = sel.sort_values("gain_disc", ascending=False)
    top = sel.head(25)
    say(f"\nD {scope_name} m{m}: universe disc {nU_d} test {nU_t}; rules scanned {len(R)}; pass discovery filter {len(sel)}; "
        f"of those positive on test {int((sel.gain_test > 0).sum())} ({(sel.gain_test > 0).mean() if len(sel) else 0:.0%})")
    if len(top):
        say(top[["kind", "feat", "op", "thr", "n_disc", "days_fire_disc", "gain_disc", "pos_days_disc", "n_test",
                 "gain_test", "pos_days_test", "test_days"]].round(3).to_string(index=False))
    # baseline: what "exit every trade at m" does
    say(f"   exit-all-at-m: disc {delta[disc].mean():+.3f} %/trade, test {delta[test].mean():+.3f} %/trade; "
        f"win rate held {np.mean(ret[disc] > 0):.3f} vs at m {np.mean(alt[disc] > 0):.3f} (disc)")


# scopes: every non-council book with marks; the 45-min pullback family; and c20 if any marks exist
nonc = df[(df.fam != "c20") & (df.fam != "twin")]
for m in MARKS:
    try:
        run_mark("non_council", nonc, m, wx_too=True)
    except Exception as ex:
        import traceback; traceback.print_exc()
    say("   t", round(time.time() - T0, 1))
for m in MARKS:
    try:
        if df[df.fam == "c20"][f"h{m}_gain_pct"].notna().sum() >= 200:
            run_mark("c20", df[df.fam == "c20"], m, wx_too=True)
    except Exception:
        import traceback; traceback.print_exc()
if ALLRES:
    R = pd.concat(ALLRES)
    R.to_pickle(os.path.join(W, "rules_scan1.pkl"))
    say("saved rules", len(R))
json.dump(OUT, open(os.path.join(W, "analysis1.json"), "w"), indent=1, default=str)
say("done", round(time.time() - T0, 1))
