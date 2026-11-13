"""R04 shared code: load the cache, groups, the vectorised single-item search, the beam, the permutation null, the
exact Conductor account (apex/conductor/account_sim.py semantics, rebuilt on the trade table)."""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = ("c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t")       # priority: ret_per_trade desc (pool.json), all "low"
TEST0 = "2026-11-05"
QS = tuple(round(0.05 * k, 2) for k in range(1, 20))           # 19 quantile lines
LOT, CAP0 = 65, 100_000.0
# whole-day facts (docs/28 s5): judged in days, never by trade counts
DAY_FACTORS = {"expiry_day", "day_before_expiry", "after_break", "event", "weekday", "dte", "gap_pts", "gap_filled",
               "vix_chg_open", "hrs_to_expiry", "norm_days", "pd_range", "pd_close_pos", "inside_pd"}


class D:
    pass


def load():
    z = np.load(os.path.join(HERE, "cache.npz"))
    m = json.load(open(os.path.join(HERE, "cache_meta.json")))
    d = D()
    d.X = z["X"]
    d.names, d.kinds = m["names"], m["kinds"]
    for k, v in m["strs"].items():
        setattr(d, k, np.array(v))
    for k in z.files:
        if k.startswith("b_"):
            setattr(d, k[2:], z[k])
    d.days = sorted(set(d.day.tolist()))
    d.di = np.array([d.days.index(x) for x in d.day])
    d.test = d.day >= TEST0
    d.ret = np.clip(d.ret_pct.astype(float), -99.0, None)
    d.g = np.log1p(d.ret / 100.0)
    d.win = (d.ret > 0).astype(float)
    d.trig = np.where(np.isfinite(d.trigger_t), d.trigger_t, d.t_in)
    return d


def family(book):
    b = book
    if b.startswith("c20_"):
        return "c20"
    if b.startswith("t28_"):
        return "t28"
    if b.startswith("lvl_trail"):
        return "lvl_trail"
    if b.startswith("spot_dc12"):
        return "spot_dc12"
    if b.startswith("spot_dual"):
        return "spot_dual"
    if b.startswith("spot_"):
        return "spot_other"
    if b[0] == "m" and b[1:2].isdigit():
        return "m_grid"
    if b.startswith("gap") and b[3:4].isdigit():
        return "gap"
    if b.startswith("edge"):
        return "edge"
    return b.split("_")[0]


def lines_for(xs, kind):
    """xs: sorted finite values. Candidate lines (a '>= line' / '< line' split)."""
    if xs.size < 2:
        return np.array([])
    if kind == "ind":
        return np.array([0.5]) if xs[0] < 0.5 <= xs[-1] else np.array([])
    u = np.unique(xs)
    if u.size < 2:
        return np.array([])
    if u.size <= 12:
        return u[1:]
    return np.unique(np.quantile(xs, QS))


class Search:
    """Single-item search on rows `rows` (discovery). Every feature, every line, both sides, missing = blocked."""

    def __init__(self, X, rows, kinds, feats=None, min_keep=15, min_drop=15, keep_frac=0.2):
        self.rows = np.asarray(rows)
        self.feats = np.arange(X.shape[1]) if feats is None else np.asarray(feats)
        Xs = X[np.ix_(self.rows, self.feats)].astype(np.float64)
        self.Xs = Xs
        n, F = Xs.shape
        self.n = n
        self.order = np.argsort(Xs, axis=0, kind="stable")           # NaN last
        self.nf = np.isfinite(Xs).sum(0)
        L, P, V = [], [], []
        T = 0
        per = []
        for j in range(F):
            xs = Xs[self.order[: self.nf[j], j], j]
            ln = lines_for(xs, kinds[self.feats[j]])
            pos = np.searchsorted(xs, ln, side="left")
            per.append((ln, pos))
            T = max(T, len(ln))
        T = max(T, 1)
        self.T = T
        self.line = np.full((F, T), np.nan)
        self.pos = np.zeros((F, T), dtype=np.int64)
        self.valid = np.zeros((F, T), dtype=bool)
        for j, (ln, pos) in enumerate(per):
            k = len(ln)
            self.line[j, :k], self.pos[j, :k], self.valid[j, :k] = ln, pos, True
        self.min_keep = max(min_keep, int(np.ceil(keep_frac * n)))
        self.min_drop = min_drop

    def stats(self, g, win, big):
        """Per feature x line x side: kept n, kept G, kept wins, kept big. side 0 = '<', 1 = '>='."""
        n, F = self.n, len(self.feats)
        o = self.order
        idx = np.arange(F)
        out = {}
        for nm, a in (("G", g), ("W", win), ("B", big)):
            C = np.zeros((n + 1, F))
            np.cumsum(a[o], axis=0, out=C[1:])
            pre = C[self.pos, idx[:, None]]                       # (F, T)
            tot = C[self.nf, idx][:, None]
            out[nm] = (pre, tot - pre)
        nk = (self.pos.astype(float), (self.nf[:, None] - self.pos).astype(float))
        return nk, out

    def best(self, g, win, big, need_sr=True):
        """Best constrained dG per feature, and the full arrays. g/win/big are aligned with self.rows."""
        Gall, Wall, nbig = g.sum(), win.sum(), big.sum()
        nk, st = self.stats(g, win, big)
        res = []
        bestv = np.full(len(self.feats), -np.inf)
        for s in (0, 1):
            k = nk[s]
            dG = st["G"][s] - Gall
            sr = np.divide(st["W"][s], k, out=np.zeros_like(k), where=k > 0)
            ok = self.valid & (k >= self.min_keep) & ((self.n - k) >= self.min_drop)
            ok &= st["B"][s] >= np.ceil(2.0 / 3.0 * nbig - 1e-9)
            if need_sr:
                ok &= sr > Wall / self.n
            dGm = np.where(ok, dG, -np.inf)
            bestv = np.maximum(bestv, dGm.max(1))
            res.append((dGm, k, sr, st["B"][s]))
        return bestv, res


def strata_perm(rng, strata):
    """A permutation that shuffles within each stratum (integer labels)."""
    p = np.arange(len(strata))
    for s in np.unique(strata):
        ix = np.flatnonzero(strata == s)
        p[ix] = ix[rng.permutation(len(ix))]
    return p


def big_mask(ret, share=0.10):
    k = max(1, int(round(share * len(ret))))
    b = np.zeros(len(ret))
    b[np.argsort(-ret, kind="stable")[:k]] = 1.0
    b[ret <= 0] = 0.0
    return b


def keep_mask(x, op, line):
    fin = np.isfinite(x)
    if op == ">=":
        return fin & (x >= line)
    return fin & (x < line)


# ── the exact Conductor account on the trade table ──────────────────────────────────────────────────────────────
class Conductor:
    def __init__(self, d):
        prio = {b: i for i, b in enumerate(POOL)}
        ix = np.flatnonzero(np.isin(d.book, POOL) & np.isfinite(d.entry) & np.isfinite(d.exit) & np.isfinite(d.t_in))
        self.byday = {}
        for di, day in enumerate(d.days):
            r = ix[d.di[ix] == di]
            pr = np.array([prio[b] for b in d.book[r]])
            o = np.lexsort((pr, d.trig[r]))
            r = r[o]
            self.byday[day] = (r, d.trig[r], d.t_out[r], d.entry[r], d.exit[r], d.book[r])
        self.d = d

    def day(self, day, keep=None):
        """keep: boolean over ALL table rows (True = the rule lets the trigger through). Returns (ret %, trades)."""
        r, trig, tout, px, ex, bk = self.byday[day]
        cap = CAP0
        held = None
        taken = []
        for j in range(len(r)):
            if held is not None:
                h_trig, h_out, h_book = held
                if trig[j] <= h_trig:
                    continue
                if trig[j] < h_out or (trig[j] == h_out and bk[j] == h_book):
                    continue
                held = None
            if keep is not None and not keep[r[j]]:
                continue
            lots = int(cap // (px[j] * LOT))
            if lots < 1:
                continue
            cap = cap + (ex[j] - px[j]) * lots * LOT
            held = (trig[j], tout[j], bk[j])
            taken.append(r[j])
        return 100.0 * (cap / CAP0 - 1.0), taken

    def run(self, days, keep=None):
        return {dy: self.day(dy, keep) for dy in days}


def summarize_account(res, d):
    """Per-day table rows and totals from Conductor.run output."""
    out = []
    for dy, (rp, taken) in sorted(res.items()):
        t = np.array(taken, dtype=int)
        n = len(t)
        w = int((d.ret[t] > 0).sum()) if n else 0
        out.append({"day": dy, "ret_pct": round(rp, 2), "n": n, "won": w,
                    "sr": round(w / n, 3) if n else None})
    return out
