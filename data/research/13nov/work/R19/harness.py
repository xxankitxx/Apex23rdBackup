"""R19 evaluation harness (13 Nov 2026). Read-only on the repo. One process, no multiprocessing.

Give it a yes/no ENTRY FILTER or an EXIT RULE as a pandas expression over the trade table
(data/research/13nov/trades_all_books.parquet) and it prints:

  1. a walk-forward table per day (discovery days 19 Oct - 4 Nov, test days 5 - 12 Nov, or your own split),
  2. the Conductor one-position, all-in account (same logic as apex/conductor/account_sim.py) with and without the rule,
  3. the owner's promotion tests (docs/28 section 2) on each window,
  4. permutation tests: trade membership (docs/28 sec 6 luck line for tests 1-2), a trigger-cluster mask shuffle
     run through the Conductor (the headline p for a filter: sibling books' copies of one trigger move together),
     and a daily sign flip of Conductor differences (the headline p for an exit rule),
  5. a multiple-testing ledger (every call is appended to ledger.jsonl; adjusted p-values use the count so far),
  6. a one-line verdict.

Usage (command line):
    py -3.13 harness.py --filter "wx_er60 >= 0.35"                     # keep trades where TRUE (pool books)
    py -3.13 harness.py --filter "wx_agree_same >= 7" --apply-to c20_9y  # restrict only one pool book
    py -3.13 harness.py --exit "h300_gain_pct < -5" --mark 300          # exit at the 300 s mark when TRUE
    py -3.13 harness.py --filter "..." --books spot_pb45 --no-conductor  # any book(s), book level only
    options: --split 2026-11-05  --perms 300  --seed 7  --name "my idea"  --no-ledger

Usage (Python):
    import sys; sys.path.insert(0, r"D:\\ApexOptions\\data\\research\\13nov\\work\\R19"); import harness as H
    res = H.evaluate(filter_expr="time_in < '12:00:00'")

Reading the result honestly:
  * Days before 9 Nov are IN SAMPLE for the c20 pool (the books were found on them). c20_9x itself was frozen on
    30 Oct pre-open, so 30 Oct onward is out of sample for c20_9x only. The default split puts 5 - 12 Nov in the test
    window; a rule you found by looking at those days is not tested by them.
  * An entry filter is applied to the saved trades. Removing a book's trade would, in a real replay, sometimes free the
    BOOK for a later trigger that does not exist in this table. The Conductor account is exact for the saved trades
    (the same approximation account_sim.py makes for rule blocks), the book level is a lower bound on activity.
  * An exit rule exits at a hold mark (60/300/900/1800 s) at the mark's LTP-based gain minus half the entry spread
    (an estimate of the bid). Trades the book would have taken after the earlier exit are not in the table.
"""
import sys
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov")
import lowprio  # noqa: F401,E402  (below-normal priority, one math thread)
import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PARQUET = r"D:\ApexOptions\data\research\13nov\trades_all_books.parquet"
HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.jsonl")
LOT = 65
CAP0 = 100_000.0
# pool.json order: same-tick priority = standing (all low) then ret_per_trade descending, then book order
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
SPLIT = "2026-11-05"
CLUSTER_S = 30.0     # sibling books' copies of one trigger fall within this many seconds
BASE_COLS = ["day", "book", "key", "rr", "strike", "entry", "exit", "entry_bid", "entry_ask", "t_in", "t_out",
             "trigger_t", "time_in", "ret_pct", "pnl_rs", "hold_s", "reason", "ep_type"]
_CACHE = {}


# ── data ────────────────────────────────────────────────────────────────────────────────────────────────────────
def _cols_in(expr, holdfile=None):
    """Column names an expression uses (identifiers that exist in the parquet or the holdfile)."""
    import pyarrow.parquet as pq
    if "schema" not in _CACHE:
        _CACHE["schema"] = set(pq.read_schema(PARQUET).names)
    if holdfile and ("h", holdfile) not in _CACHE:
        _CACHE[("h", holdfile)] = set(pq.read_schema(holdfile).names)
        _CACHE["schema"] |= _CACHE[("h", holdfile)]
    toks = set(re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", expr or ""))
    return sorted(t for t in toks if t in _CACHE["schema"])


def load(extra_cols=(), books=None, holdfile=None):
    """The trade table with the base columns plus `extra_cols`, optionally only `books`. holdfile: a parquet keyed
    by (day, book, key, t_in) with extra per-trade columns (phaseB_holdmarks_council.py writes hb<mark>_* for the
    pool books, which have no h<mark>_* marks of their own)."""
    hcols = []
    if holdfile:
        import pyarrow.parquet as pq
        hn = set(pq.read_schema(holdfile).names)
        hcols = [c for c in extra_cols if c in hn]
    cols = list(dict.fromkeys(BASE_COLS + [c for c in extra_cols if c not in BASE_COLS and c not in hcols]))
    df = pd.read_parquet(PARQUET, columns=cols)
    if hcols:
        h = pd.read_parquet(holdfile, columns=["day", "book", "key", "t_in"] + hcols)
        df = df.merge(h, on=["day", "book", "key", "t_in"], how="left")
    if books is not None:
        df = df[df["book"].isin(list(books))].copy()
    df["trig"] = df["trigger_t"].where(df["trigger_t"].notna(), df["t_in"]).astype(float)
    df = df[df["entry"].notna() & df["exit"].notna() & df["t_in"].notna()].copy()
    df["win"] = (df["exit"] > df["entry"]).astype(int)
    return df.reset_index(drop=True)


# ── the Conductor (apex/conductor/account_sim.py simulate_day, on a DataFrame) ───────────────────────────────────
def conductor_day(rows, pool=POOL, ret_col="ret_pct", tout_col="t_out", exit_col="exit"):
    """rows: one day's pool-book trades (already filtered). Returns (day_return_pct, list of taken row indices)."""
    prio = {b: i for i, b in enumerate(pool)}
    r = rows.assign(_p=rows["book"].map(prio)).sort_values(["trig", "_p"], kind="mergesort")
    cap = CAP0
    held = None
    taken = []
    trig_a = r["trig"].to_numpy(); book_a = r["book"].to_numpy(); ent_a = r["entry"].to_numpy(float)
    ex_a = r[exit_col].to_numpy(float); out_a = r[tout_col].to_numpy(float); idx_a = r.index.to_numpy()
    for i in range(len(r)):
        trig, bk = trig_a[i], book_a[i]
        if held is not None:
            h_trig, h_out, h_book = held
            if trig <= h_trig:
                continue
            if trig < h_out or (trig == h_out and bk == h_book):
                continue
            held = None
        px = ent_a[i]
        lots = int(cap // (px * LOT))
        if lots < 1:
            continue
        cap = cap + (ex_a[i] - px) * lots * LOT
        held = (trig, out_a[i], bk)
        taken.append(idx_a[i])
    return 100.0 * (cap / CAP0 - 1.0), taken


def prep(df, pool=POOL, exit_col="exit", tout_col="t_out"):
    """Pre-sorted numpy arrays per day for fast repeated Conductor runs (permutations)."""
    prio = {b: i for i, b in enumerate(pool)}
    sub = df[df["book"].isin(pool)]
    sub = sub.assign(_p=sub["book"].map(prio)).sort_values(["day", "trig", "_p"], kind="mergesort")
    out = {}
    for day, r in sub.groupby("day", sort=True):
        out[day] = (r["trig"].to_numpy(float), r["_p"].to_numpy(int), r["entry"].to_numpy(float),
                    r[exit_col].to_numpy(float), r[tout_col].to_numpy(float), r.index.to_numpy())
    return out


def sim_arrays(a, keep=None):
    """One day from prep() arrays; keep = boolean array over the df index (None = all). (ret_pct, taken idx)."""
    trig_a, p_a, ent_a, ex_a, out_a, idx_a = a
    cap = CAP0
    h_trig = h_out = None; h_b = -1
    taken = []
    for i in range(len(trig_a)):
        if keep is not None and not keep[idx_a[i]]:
            continue
        trig = trig_a[i]
        if h_trig is not None:
            if trig <= h_trig or trig < h_out or (trig == h_out and p_a[i] == h_b):
                continue
            h_trig = None
        px = ent_a[i]
        lots = int(cap // (px * LOT))
        if lots < 1:
            continue
        cap += (ex_a[i] - px) * lots * LOT
        h_trig, h_out, h_b = trig, out_a[i], p_a[i]
        taken.append(idx_a[i])
    return 100.0 * (cap / CAP0 - 1.0), taken


def conductor(df, pool=POOL, keep=None, prepped=None, days=None, **kw):
    """{day: (ret_pct, taken_idx)} over every day present in df (days with no pool trade return 0)."""
    pp = prepped if prepped is not None else prep(df, pool, **kw)
    days = days if days is not None else sorted(df["day"].unique())
    return {d: (sim_arrays(pp[d], keep) if d in pp else (0.0, [])) for d in days}


def day_ret_without(df, taken, drop_idx, **kw):
    """Compounded day return of a taken list with some trades removed (multiplier approximation)."""
    m = 1.0
    for i in taken:
        if i in drop_idx:
            continue
        m *= 1.0 + df.at[i, kw.get("ret_col", "ret_pct")] / 100.0
    return 100.0 * (m - 1.0)


# ── rule application ───────────────────────────────────────────────────────────────────────────────────────────
def apply_filter(df, expr, apply_to):
    """Rows kept: rows of books not in apply_to, plus rows of apply_to where expr is TRUE (NaN = blocked)."""
    m = df.eval(expr, engine="python")
    m = pd.Series(m, index=df.index).fillna(False).astype(bool)
    scope = df["book"].isin(apply_to)
    return (~scope) | m, m


def apply_exit(df, expr, mark, apply_to):
    """Return a copy with ret/exit/t_out replaced at the mark where expr is TRUE and the trade was still open."""
    d = df.copy()
    bid_based = f"hb{mark}_ret" in d.columns          # rebuilt from bids (phaseB): no spread haircut
    g = f"hb{mark}_ret" if bid_based else f"h{mark}_gain_pct"
    if g not in d.columns:
        raise ValueError(f"load the column {g}")
    m = pd.Series(d.eval(expr, engine="python"), index=d.index).fillna(False).astype(bool)
    still_open = d["hold_s"] > mark
    half_spread_pct = 100.0 * 0.5 * (d["entry_ask"] - d["entry_bid"]).clip(lower=0).fillna(0) / d["entry"]
    hit = m & still_open & d["book"].isin(apply_to) & d[g].notna()
    new_ret = d[g] if bid_based else d[g] - half_spread_pct
    d.loc[hit, "ret_pct"] = new_ret[hit]
    d.loc[hit, "exit"] = d.loc[hit, "entry"] * (1 + new_ret[hit] / 100.0)
    d.loc[hit, "t_out"] = d.loc[hit, "t_in"] + mark
    d["win"] = (d["exit"] > d["entry"]).astype(int)
    d["_changed"] = hit
    return d


# ── statistics ─────────────────────────────────────────────────────────────────────────────────────────────────
def membership_perm(base_ret, k, n=2000, rng=None):
    """95th percentiles of strike rate and mean return of random size-k subsets of base trades (docs/28 sec 6)."""
    rng = rng or np.random.default_rng(7)
    base_ret = np.asarray(base_ret, float)
    if k == 0 or k >= len(base_ret):
        return np.nan, np.nan, np.nan, np.nan
    sr, mr = np.empty(n), np.empty(n)
    for j in range(n):
        s = rng.choice(base_ret, k, replace=False)
        sr[j], mr[j] = (s > 0).mean(), s.mean()
    return np.percentile(sr, 95), np.percentile(mr, 95), sr, mr


def sign_flip_p(diffs, n=20000, rng=None):
    """One-sided p that the mean daily difference is > 0, by random sign flips (exact if few days)."""
    d = np.asarray(diffs, float)
    d = d[~np.isnan(d)]
    if len(d) == 0 or np.allclose(d, 0):
        return 1.0
    obs = d.mean()
    if len(d) <= 16:
        import itertools
        sims = np.array([np.mean(d * np.array(s)) for s in itertools.product((1, -1), repeat=len(d))])
    else:
        rng = rng or np.random.default_rng(11)
        sims = (d[None, :] * rng.choice((1, -1), size=(n, len(d)))).mean(1)
    return float((sims >= obs - 1e-12).mean())


def promotion_tests(base, rule, base_c, rule_c, days, perm_n=2000, rng=None, base_full=None, rule_full=None):
    """docs/28 sec 2 on one window. base/rule: trade frames (book level, scope books); base_c/rule_c: Conductor
    {day: (ret, taken)}. Returns dict of test -> (pass, detail)."""
    out = {}
    bf = base if base_full is None else base_full
    rf = rule if rule_full is None else rule_full
    b = base[base["day"].isin(days)]; r = rule[rule["day"].isin(days)]
    k = len(r)
    p95_sr, p95_mr, _, _ = membership_perm(b["ret_pct"].to_numpy(), k, perm_n, rng)
    sr_b, sr_r = b["win"].mean() if len(b) else np.nan, r["win"].mean() if k else np.nan
    mr_b, mr_r = b["ret_pct"].mean() if len(b) else np.nan, r["ret_pct"].mean() if k else np.nan
    same = k == len(b)
    out["1 wins more often"] = (bool(not same and k > 0 and sr_r > p95_sr),
                                f"strike {sr_r:.0%} vs {sr_b:.0%}, luck line {p95_sr:.0%} (n {k} of {len(b)})"
                                if k and not same else f"rule keeps {k} of {len(b)} trades")
    out["2 makes more"] = (bool(not same and k > 0 and mr_r > p95_mr),
                           f"mean {mr_r:+.2f}% vs {mr_b:+.2f}%, luck line {p95_mr:+.2f}%" if k and not same else "n/a")
    cb = np.array([base_c[d][0] for d in days]); cr = np.array([rule_c[d][0] for d in days])
    tot_r, tot_b = cr.sum(), cb.sum()
    # best trade of the rule's Conductor (by ret), removed from its day
    allr = [(d, i, rf.at[i, "ret_pct"]) for d in days for i in rule_c[d][1]]
    allb = [(d, i, bf.at[i, "ret_pct"]) for d in days for i in base_c[d][1]]
    def wo_best_trade(c, allt, frame):
        if not allt:
            return float(sum(c[d][0] for d in days))
        d0, i0, _ = max(allt, key=lambda x: x[2])
        return float(sum(day_ret_without(frame, c[d][1], {i0}) if d == d0 else c[d][0] for d in days))
    r_wobt = wo_best_trade(rule_c, allr, rf); b_wobt = wo_best_trade(base_c, allb, bf)
    r_wobd = tot_r - cr.max() if len(cr) else 0.0
    b_wobd = tot_b - cb.max() if len(cb) else 0.0
    out["3 makes money at all"] = (bool(tot_r > 0 and r_wobt > 0 and r_wobd > 0),
                                   f"sum of day % {tot_r:+.1f}, without best trade {r_wobt:+.1f}, without best day {r_wobd:+.1f}")
    out["4 not one win"] = (bool(r_wobt > b_wobt and r_wobd > b_wobd),
                            f"w/o best trade {r_wobt:+.1f} vs {b_wobt:+.1f}; w/o best day {r_wobd:+.1f} vs {b_wobd:+.1f}")
    # 5: keeps the big wins: baseline Conductor top 10 % trades; rule Conductor held same side at entry or within 60 s
    bt = sorted(allb, key=lambda x: -x[2]); ntop = max(1, int(round(0.1 * len(bt)))) if bt else 0
    kept = 0
    for d, i, _ in bt[:ntop]:
        t0, side = bf.at[i, "t_in"], bf.at[i, "rr"]
        ok = False
        for j in rule_c[d][1]:
            if rf.at[j, "rr"] != side:
                continue
            if (rf.at[j, "t_in"] <= t0 < rf.at[j, "t_out"]) or abs(rf.at[j, "t_in"] - t0) <= 60:
                ok = True
                break
        kept += ok
    out["5 keeps the big wins"] = (bool(ntop == 0 or kept >= 2 * ntop / 3), f"{kept} of {ntop} top trades kept")
    out["5b no worse on bad days"] = (bool(cr.min() >= cb.min() - 1e-9) if len(cr) else False,
                                     f"worst day {cr.min():+.1f}% vs {cb.min():+.1f}%" if len(cr) else "n/a")
    out["6 sample"] = (bool(k >= 30), f"{k} trades kept in window (rule minimum 30; filters exempt from per-day count)")
    return out


def summarize_window(frame, cdict, days, scope=None):
    f = (frame if scope is None else scope)
    f = f[f["day"].isin(days)]
    cr = np.array([cdict[d][0] for d in days])
    nt = sum(len(cdict[d][1]) for d in days)
    wins = sum(int(frame.at[i, "win"]) for d in days for i in cdict[d][1])
    return {"book_n": len(f), "book_strike": f["win"].mean() if len(f) else np.nan,
            "book_mean": f["ret_pct"].mean() if len(f) else np.nan,
            "c_n": nt, "c_strike": wins / nt if nt else np.nan, "c_sum_day_pct": cr.sum(),
            "c_losing_days": int((cr < 0).sum()), "c_worst": cr.min() if len(cr) else np.nan,
            "c_geo_day": 100 * (np.prod(1 + cr / 100) ** (1 / len(cr)) - 1) if len(cr) else np.nan}


def mask_shuffle_p(df, keep_full, apply_to, pool, days, obs, n=300, rng=None, **kw):
    """Null for the whole system: within each day, shuffle WHICH apply_to trades the rule keeps (same count), re-run
    the Conductor, compare the sum of daily % on `days`. One-sided p = share of shuffles >= observed."""
    # The pool books are near copies: one market trigger is traded by several siblings within seconds. Shuffling
    # single trades would almost always leave a sibling copy of every trigger, so the null shuffles TRIGGER CLUSTERS
    # (same day, same side, triggers within CLUSTER_S of the cluster's first): each cluster gets the rule's
    # majority verdict and the verdicts are shuffled among the day's clusters (same number kept per day).
    rng = rng or np.random.default_rng(3)
    scope = df["book"].isin(apply_to) & df["day"].isin(days)
    sims = np.empty(n)
    clusters = {}
    for d in days:
        s = df[scope & (df["day"] == d)].sort_values("trig")
        cl, cur = [], None
        for i, tr, side in zip(s.index, s["trig"], s["rr"]):
            if cur is None or tr - cur[0] > CLUSTER_S or side != cur[1]:
                cur = (tr, side, [])
                cl.append(cur)
            cur[2].append(i)
        mem = [np.array(c_[2]) for c_ in cl]
        lab = np.array([keep_full[m].mean() >= 0.5 for m in mem], bool)
        clusters[d] = (mem, lab)
    pp = prep(df[df["day"].isin(days)], pool, **kw)
    for j in range(n):
        keep = keep_full.copy()
        for d in days:
            mem, lab = clusters[d]
            if not mem:
                continue
            perm = rng.permutation(lab)
            for m, v in zip(mem, perm):
                keep[m] = v
        c = conductor(None, pool, keep=keep, prepped=pp, days=days)
        sims[j] = sum(c[d][0] for d in days)
    return float((sims >= obs - 1e-9).mean()), sims


def ledger_add(entry):
    try:
        with open(LEDGER, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
        with open(LEDGER, encoding="utf-8") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return None


# ── the evaluation ─────────────────────────────────────────────────────────────────────────────────────────────
def evaluate(filter_expr=None, exit_expr=None, mark=300, books=None, apply_to=None, split=SPLIT, perms=300,
             seed=7, name=None, conductor_on=True, ledger=True, verbose=True, holdfile=None):
    t0 = time.time()
    rng = np.random.default_rng(seed)
    pool = list(POOL)
    books = list(books) if books else pool
    apply_to = list(apply_to) if apply_to else books
    extra = _cols_in(filter_expr, holdfile) + _cols_in(exit_expr, holdfile)
    if exit_expr:
        extra += [f"hb{mark}_ret"] if holdfile else [f"h{mark}_gain_pct"]
    extra = list(dict.fromkeys(extra))                      # 13 Nov: a column named twice made duplicate labels
    df = load(extra, books=sorted(set(books) | (set(pool) if conductor_on else set())), holdfile=holdfile)
    all_days = sorted(df["day"].unique())
    w1 = [d for d in all_days if d < split]; w2 = [d for d in all_days if d >= split]
    if filter_expr:
        keep, raw = apply_filter(df, filter_expr, apply_to)
        rdf = df[keep].copy()
        kind = "filter"
    else:
        rdf = apply_exit(df, exit_expr, mark, apply_to)
        keep = pd.Series(True, index=df.index)
        kind = f"exit@{mark}s"
    base_scope = df[df["book"].isin(apply_to)]
    rule_scope = rdf[rdf["book"].isin(apply_to)]
    cpool = pool if conductor_on else apply_to
    base_c = conductor(df, cpool); rule_c = conductor(rdf, cpool)
    for d in all_days:
        rule_c.setdefault(d, (0.0, []))
    # per-day walk-forward table
    rows = []
    for d in all_days:
        b = base_scope[base_scope["day"] == d]; r = rule_scope[rule_scope["day"] == d]
        rows.append({"day": d, "win": "test" if d >= split else "disc", "book_n": len(b), "rule_n": len(r),
                     "book_sr": b["win"].mean() if len(b) else np.nan, "rule_sr": r["win"].mean() if len(r) else np.nan,
                     "book_mean": b["ret_pct"].mean() if len(b) else np.nan,
                     "rule_mean": r["ret_pct"].mean() if len(r) else np.nan,
                     "cond_n": len(base_c[d][1]), "cond_rule_n": len(rule_c[d][1]),
                     "cond_day%": base_c[d][0], "cond_rule_day%": rule_c[d][0]})
    tab = pd.DataFrame(rows)
    res = {"name": name or (filter_expr or exit_expr), "kind": kind, "expr": filter_expr or exit_expr,
           "apply_to": apply_to, "split": split, "table": tab}
    windows = {"W1 discovery " + (w1[0] + ".." + w1[-1] if w1 else ""): w1,
               "W2 test " + (w2[0] + ".." + w2[-1] if w2 else ""): w2}
    res["windows"] = {}
    for wn, wd in windows.items():
        if not wd:
            continue
        tests = promotion_tests(base_scope, rule_scope, base_c, rule_c, wd, 2000, rng, df, rdf)
        if kind != "filter":       # an exit rule keeps every trade: tests 1-2 compare like for like (paired)
            bb = base_scope[base_scope["day"].isin(wd)]; rr_ = rule_scope[rule_scope["day"].isin(wd)]
            dd = (rr_["ret_pct"].to_numpy() - bb["ret_pct"].to_numpy())
            p_pair = sign_flip_p(dd, rng=rng) if len(dd) else 1.0
            tests["1 wins more often"] = (bool(rr_["win"].mean() > bb["win"].mean() and p_pair < 0.05),
                                          f"strike {rr_['win'].mean():.0%} vs {bb['win'].mean():.0%}")
            tests["2 makes more"] = (bool(p_pair < 0.05 and dd.mean() > 0),
                                     f"paired mean change {dd.mean():+.2f}% per trade, sign-flip p {p_pair:.3f}, "
                                     f"{int(rr_['_changed'].sum())} trades changed")
            tests["6 sample"] = (bool(rr_["_changed"].sum() >= 30), f"{int(rr_['_changed'].sum())} trades changed")
        diffs = [rule_c[d][0] - base_c[d][0] for d in wd]
        p_flip = sign_flip_p(diffs, rng=rng)
        obs = sum(rule_c[d][0] for d in wd)
        if kind == "filter" and perms:
            p_mask, _ = mask_shuffle_p(df, keep.to_numpy().copy(), apply_to, cpool, wd, obs, perms, rng)
        else:
            p_mask = np.nan
        res["windows"][wn] = {"days": wd, "tests": tests, "base": summarize_window(df, base_c, wd, base_scope),
                              "rule": summarize_window(rdf, rule_c, wd, rule_scope), "p_dayflip": p_flip, "p_mask": p_mask,
                              "pass_all": all(v[0] for k_, v in tests.items() if not k_.startswith("6"))}
    test_w = [v for k_, v in res["windows"].items() if k_.startswith("W2")]
    # one pre-declared p per idea (taking the smaller of two would itself be a second test): the cluster mask
    # shuffle for a filter, the daily sign flip for an exit rule
    p_main = 1.0
    if test_w:
        p_main = test_w[0]["p_mask"] if not np.isnan(test_w[0]["p_mask"]) else test_w[0]["p_dayflip"]
    n_tried = None
    if ledger:
        n_tried = ledger_add({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "name": res["name"], "kind": kind,
                              "expr": res["expr"], "apply_to": apply_to, "split": split, "p_test": p_main,
                              "pass_W2": bool(test_w and test_w[0]["pass_all"])})
    res["n_tried"] = n_tried
    res["p_test"] = p_main
    res["p_test_adj"] = min(1.0, p_main * (n_tried or 1))
    w2pass = bool(test_w and test_w[0]["pass_all"])
    w1pass = all(v["pass_all"] for k_, v in res["windows"].items() if k_.startswith("W1"))
    if w2pass and w1pass and res["p_test_adj"] < 0.05:
        verdict = "PROMOTE AS SHADOW: passes both windows and survives the multiple-testing count"
    elif w2pass and w1pass:
        verdict = "SHADOW ONLY: passes both windows by the letter, but not after the multiple-testing count"
    elif w2pass:
        verdict = "WATCH: passes the test window only (W1 failed or is in sample); not evidence yet"
    else:
        verdict = "REJECT: fails the test window"
    res["verdict"] = verdict
    res["secs"] = round(time.time() - t0, 1)
    if verbose:
        print_result(res)
    return res


def print_result(res):
    pd.set_option("display.width", 200)
    print(f"\n=== {res['name']}  [{res['kind']}]  on {', '.join(res['apply_to'])}  (split {res['split']}) ===")
    t = res["table"].copy()
    for c in ("book_sr", "rule_sr"):
        t[c] = (100 * t[c]).round(0)
    for c in ("book_mean", "rule_mean", "cond_day%", "cond_rule_day%"):
        t[c] = t[c].round(1)
    print(t.to_string(index=False))
    for wn, w in res["windows"].items():
        b, r = w["base"], w["rule"]
        print(f"\n-- {wn}: {len(w['days'])} days")
        print(f"   book level  : {b['book_n']} -> {r['book_n']} trades, strike {b['book_strike']:.0%} -> "
              f"{r['book_strike']:.0%}, mean {b['book_mean']:+.2f}% -> {r['book_mean']:+.2f}%")
        print(f"   Conductor   : {b['c_n']} -> {r['c_n']} trades, strike {b['c_strike']:.0%} -> {r['c_strike']:.0%}, "
              f"sum of day % {b['c_sum_day_pct']:+.1f} -> {r['c_sum_day_pct']:+.1f}, geometric day "
              f"{b['c_geo_day']:+.1f}% -> {r['c_geo_day']:+.1f}%, losing days {b['c_losing_days']} -> "
              f"{r['c_losing_days']}, worst {b['c_worst']:+.1f}% -> {r['c_worst']:+.1f}%")
        print(f"   p (daily sign flip) {w['p_dayflip']:.3f}   p (mask shuffle through Conductor) "
              f"{w['p_mask'] if not np.isnan(w['p_mask']) else float('nan'):.3f}")
        for k, (ok, det) in w["tests"].items():
            print(f"   [{'PASS' if ok else 'fail'}] {k}: {det}")
        print(f"   all promotion tests: {'PASS' if w['pass_all'] else 'FAIL'}")
    print(f"\nmultiple testing: {res['n_tried']} ideas in the ledger; test-window p {res['p_test']:.3f}"
          f" -> Bonferroni-adjusted {res['p_test_adj']:.3f}")
    print(f"VERDICT: {res['verdict']}   ({res['secs']} s)")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter"); ap.add_argument("--exit"); ap.add_argument("--mark", type=int, default=300)
    ap.add_argument("--books", nargs="*"); ap.add_argument("--apply-to", nargs="*")
    ap.add_argument("--split", default=SPLIT); ap.add_argument("--perms", type=int, default=300)
    ap.add_argument("--seed", type=int, default=7); ap.add_argument("--name")
    ap.add_argument("--no-conductor", action="store_true"); ap.add_argument("--no-ledger", action="store_true")
    ap.add_argument("--holdfile", help="parquet of extra per-trade columns, e.g. work/R19/pool_holdmarks.parquet")
    a = ap.parse_args(argv)
    if bool(a.filter) == bool(a.exit):
        ap.error("give exactly one of --filter or --exit")
    evaluate(a.filter, a.exit, a.mark, a.books, a.apply_to, a.split, a.perms, a.seed, a.name,
             not a.no_conductor, not a.no_ledger, holdfile=a.holdfile)


if __name__ == "__main__":
    main()
