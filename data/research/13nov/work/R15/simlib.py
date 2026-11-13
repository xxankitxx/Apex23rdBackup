"""R15 shared helpers: the Conductor's one-account rule (apex/conductor/account_sim.py simulate_day, re-implemented on
the flat trade table so meta-strategies can pick the pool per day). Same rules: walk triggers by (trigger_t, priority),
take the first while flat, hold to the source book's own exit, lots = capital // (entry * 65), compound."""
import numpy as np
import pandas as pd

LOT = 65
CAP0 = 100_000.0
EARLY = ["2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28",
         "2026-10-29", "2026-10-30", "2026-11-02", "2026-11-03", "2026-11-04"]
LATE = ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-11", "2026-11-12"]
DAYS = EARLY + LATE
POOL = ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]   # priority order (ret_per_trade descending)


def family(b):
    if b == "conductor":
        return "meta"
    if b.startswith("c20") or b in ("fr_c20_9y", "fx_c20_9y", "rx_c20_9y"):
        return "council"
    if b.startswith("t28"):
        return "t28"
    if b.startswith("lvl_trail"):
        return "lvl"
    if b.startswith("spot_"):
        return "spot"
    if b.startswith("edge_") or b == "apex_edge":
        return "edge"
    if b.startswith("m1") or b.startswith("m2") or b.startswith("gap"):
        return "mgrid"
    if b[:3] in ("n01", "n02", "n06"):
        return "gen2_n"
    if b[:3] in ("p02", "p05"):
        return "gen2_p"
    if b[:3] in ("s01", "s03"):
        return "gen2_s"
    if b in ("fade_switch", "fade_switch_r002", "straddle_spike", "premium_momentum"):
        return "special"
    return "control"


def load(path=r"D:\ApexOptions\data\research\13nov\work\R15\trades_small.parquet"):
    df = pd.read_parquet(path)
    df = df[df["entry"].notna() & df["exit"].notna() & df["t_in"].notna()].copy()
    df["trig"] = df["trigger_t"].fillna(df["t_in"]).astype(float)
    df["fam"] = df["book"].map(family)
    df["r"] = (df["exit"] / df["entry"] - 1.0) * 100.0          # per-trade return, % of premium
    return df


def sim_day(tr, order, cap0=CAP0):
    """tr: DataFrame of one day's candidate trades (any books); order: {book: priority rank}, lower first.
    Returns dict(ret, n, wins, trades=list)."""
    if tr is None or len(tr) == 0:
        return {"ret": 0.0, "n": 0, "wins": 0, "trades": []}
    pr = tr["book"].map(order).fillna(10 ** 6).values
    idx = np.lexsort((pr, tr["trig"].values))
    trig = tr["trig"].values[idx]; tout = tr["t_out"].values[idx].astype(float)
    ent = tr["entry"].values[idx].astype(float); ex = tr["exit"].values[idx].astype(float)
    bk = tr["book"].values[idx]; rr = tr["rr"].values[idx]
    cap = cap0; held = None; out = []
    for i in range(len(idx)):
        if held is not None:
            h_trig, h_out, h_book = held
            if trig[i] <= h_trig:
                continue
            if trig[i] < h_out or (trig[i] == h_out and bk[i] == h_book):
                continue
            held = None
        lots = int(cap // (ent[i] * LOT))
        if lots < 1:
            continue
        pnl = (ex[i] - ent[i]) * lots * LOT
        cap += pnl
        held = (trig[i], tout[i], bk[i])
        out.append((bk[i], trig[i], tout[i], ent[i], ex[i], pnl, (ex[i] / ent[i] - 1) * 100, rr[i]))
    return {"ret": 100.0 * (cap / cap0 - 1.0), "n": len(out), "wins": sum(1 for o in out if o[5] > 0), "trades": out}


def summarize(recs, days):
    """recs: {day: sim_day result}. Strike rate first."""
    n = sum(recs[d]["n"] for d in days); w = sum(recs[d]["wins"] for d in days)
    rets = [recs[d]["ret"] for d in days]
    tr = [t[6] for d in days for t in recs[d]["trades"]]
    best_day = max(rets) if rets else 0
    sum_ret = sum(rets)
    # without the best trade: remove its rupee effect approximately by recomputing its day without it
    return {"n": n, "sr": 100.0 * w / n if n else float("nan"), "sum_day_pct": sum_ret,
            "mean_day_pct": float(np.mean(rets)) if rets else 0, "median_day_pct": float(np.median(rets)) if rets else 0,
            "losing_days": sum(1 for r in rets if r < 0), "worst_day": min(rets) if rets else 0,
            "sum_wo_best_day": sum_ret - best_day, "mean_trade_pct": float(np.mean(tr)) if tr else float("nan")}


def sim_wo_best_trade(day_trades_df, order, rec):
    """Recompute a day with its single best taken trade removed from the candidates (the account then takes whatever
    else fires)."""
    if not rec["trades"]:
        return rec
    b = max(rec["trades"], key=lambda t: t[6])
    m = ~((day_trades_df["book"] == b[0]) & (day_trades_df["trig"] == b[1]))
    return sim_day(day_trades_df[m], order)


class DayArr:
    """One day's trades as numpy arrays, sorted by trigger time (fast path for many simulations)."""
    def __init__(self, x, book_ids):
        x = x.sort_values(["trig"], kind="stable")
        self.trig = x.trig.values.astype(float); self.tout = x.t_out.values.astype(float)
        self.ent = x.entry.values.astype(float); self.ex = x.exit.values.astype(float)
        self.bid = np.array([book_ids[b] for b in x.book.values], dtype=np.int32)
        self.side = (x.rr.values == "CE").astype(np.int8)
        self.fam = x.fam.values
        self.r = (self.ex / self.ent - 1) * 100


def sim_fast(D, mask, rank, books=None):
    """mask: bool array over D's rows (candidates); rank: int array indexed by book id (lower = higher priority)."""
    ii = np.nonzero(mask)[0]
    if len(ii) == 0:
        return {"ret": 0.0, "n": 0, "wins": 0, "trades": []}
    pr = rank[D.bid[ii]]
    ii = ii[np.lexsort((pr, D.trig[ii]))]
    cap = CAP0; h_trig = h_out = None; h_b = -1; out = []
    for i in ii:
        t = D.trig[i]
        if h_trig is not None:
            if t <= h_trig:
                continue
            if t < h_out or (t == h_out and D.bid[i] == h_b):
                continue
            h_trig = None
        lots = int(cap // (D.ent[i] * LOT))
        if lots < 1:
            continue
        pnl = (D.ex[i] - D.ent[i]) * lots * LOT
        cap += pnl
        h_trig, h_out, h_b = t, D.tout[i], D.bid[i]
        out.append((books[D.bid[i]] if books is not None else int(D.bid[i]), float(t), float(h_out), float(D.ent[i]),
                    float(D.ex[i]), float(pnl), float(D.r[i]), "CE" if D.side[i] else "PE"))
    return {"ret": 100.0 * (cap / CAP0 - 1.0), "n": len(out), "wins": sum(1 for o in out if o[5] > 0), "trades": out}
