import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 step 3: 2- and 3-item AND filters by beam search (trade level), discovery 19 Oct - 4 Nov, test 5 - 12 Nov.
  py -3.13 -u s3_beam.py GROUP[,GROUP...] [BUDGET_S] [K]
Beam: the K best single lines (constrained dG) -> every other item's every line inside each -> the K best pairs ->
every third item. Null: the SAME beam (same K) re-run on outcomes shuffled within book x day (pool events: day);
the best triple's dG is compared with the null's best triple (max statistic over the whole beam)."""
import json, os, time
t0 = time.time()
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r04lib as L

groups = sys.argv[1].split(",")
budget = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
K = int(sys.argv[3]) if len(sys.argv) > 3 else 12
d = L.load()
CONTROLS = {"random_entry", "futures_only", "premium_momentum", "RAW", "conductor"}
fam = np.array([L.family(b) for b in d.book])
bookid = np.unique(d.book, return_inverse=True)[1]


def group_rows(grp):
    ok = np.isfinite(d.ret) & ~np.isin(d.book, list(CONTROLS))
    if grp in ("pool_events", "pool_trades"):
        ok &= np.isin(d.book, L.POOL)
        if grp == "pool_events":
            prio = {b: i for i, b in enumerate(L.POOL)}
            pr = np.array([prio.get(b, 9) for b in d.book])
            ix = np.flatnonzero(ok)
            ix = ix[np.lexsort((pr[ix], d.trig[ix], d.di[ix]))]
            kv = np.stack([d.di[ix], d.trig[ix]], 1)
            first = np.ones(len(ix), bool); first[1:] = np.any(kv[1:] != kv[:-1], axis=1)
            sel = np.zeros(len(d.ret), bool); sel[ix[first]] = True
            return sel, d.di.copy()
        return ok, d.di * 1000 + bookid
    if grp.startswith("fam:"):
        return ok & (fam == grp[4:]), d.di * 1000 + bookid
    return ok, d.di * 1000 + bookid


class Beam:
    def __init__(self, S):
        self.S = S

    def cond_stats(self, g, win, big, A):
        """Stats of (A and line) for every feature x line x side. A: (n,) 0/1 float."""
        S = self.S
        n, F = S.n, len(S.feats)
        o = S.order
        idx = np.arange(F)
        res = {}
        for nm, a in (("G", g * A), ("W", win * A), ("B", big * A), ("N", A)):
            Cm = np.zeros((n + 1, F))
            np.cumsum(a[o], axis=0, out=Cm[1:])
            pre = Cm[S.pos, idx[:, None]]
            tot = Cm[S.nf, idx][:, None]
            res[nm] = (pre, tot - pre)
        return res

    def best_in(self, g, win, big, A, excl):
        S = self.S
        Gall, Wall, nbig = g.sum(), win.sum(), big.sum()
        st = self.cond_stats(g, win, big, A)
        best = []
        for s in (0, 1):
            k = st["N"][s]
            dG = st["G"][s] - Gall
            sr = np.divide(st["W"][s], k, out=np.zeros_like(k), where=k > 0)
            okm = S.valid & (k >= S.min_keep) & ((S.n - k) >= S.min_drop) & (sr > Wall / S.n)
            okm &= st["B"][s] >= np.ceil(2.0 / 3.0 * nbig - 1e-9)
            okm[list(excl), :] = False
            best.append((np.where(okm, dG, -np.inf), k, sr))
        return best

    def run(self, g, win, big, K):
        S = self.S
        one = np.ones(S.n)
        b1 = self.best_in(g, win, big, one, set())
        cands = []
        for s in (0, 1):
            dGm = b1[s][0]
            fl = np.argsort(-dGm, axis=None)[: 4 * K]
            for q in fl:
                j, t = divmod(int(q), S.T)
                if np.isfinite(dGm[j, t]):
                    cands.append((float(dGm[j, t]), ((j, s, t),)))
        cands = self._dedupe(cands, K)
        singles = cands
        pairs = self._extend(g, win, big, singles, K)
        triples = self._extend(g, win, big, pairs, K)
        return singles, pairs, triples

    def mask(self, conds):
        S = self.S
        m = np.ones(S.n)
        for (j, s, t) in conds:
            x = S.Xs[:, j]
            ln = S.line[j, t]
            m *= (np.isfinite(x) & ((x >= ln) if s == 1 else (x < ln))).astype(float)
        return m

    def _extend(self, g, win, big, base, K):
        out = []
        for _v, conds in base:
            A = self.mask(conds)
            excl = {c[0] for c in conds}
            b = self.best_in(g, win, big, A, excl)
            for s in (0, 1):
                dGm = b[s][0]
                for q in np.argsort(-dGm, axis=None)[:3]:
                    j, t = divmod(int(q), self.S.T)
                    if np.isfinite(dGm[j, t]):
                        out.append((float(dGm[j, t]), conds + ((j, s, t),)))
        return self._dedupe(out, K)

    @staticmethod
    def _dedupe(c, K):
        c.sort(key=lambda x: -x[0])
        out, seen = [], set()
        for v, conds in c:
            key = tuple(sorted(conds))
            feats = tuple(sorted(x[0] for x in conds))
            if key in seen or (len(conds) == 1 and feats in seen):
                continue
            seen.add(key); seen.add(feats)
            out.append((v, conds))
            if len(out) >= K:
                break
        return out


results = {}
per_group_budget = budget / len(groups)
for grp in groups:
    tg = time.time()
    ok, strat_of = group_rows(grp)
    disc = np.flatnonzero(ok & ~d.test)
    test = np.flatnonzero(ok & d.test)
    S = L.Search(d.X, disc, d.kinds)
    g, win, big = d.g[disc], d.win[disc], L.big_mask(d.ret[disc])
    B = Beam(S)
    s1, s2, s3 = B.run(g, win, big, K)
    print(grp, "n", len(disc), "beam real", round(time.time() - tg, 1), "best", [round(x[0][0], 3) if x else None for x in (s1, s2, s3)], flush=True)
    strata = strat_of[disc]
    Aidx = np.argsort(strata, kind="stable")
    rng = np.random.default_rng(1113)
    null = []
    while time.time() - tg < per_group_budget and len(null) < 200:
        Bi = np.argsort(strata + rng.random(len(strata)) * 0.5, kind="stable")
        p = np.empty(len(strata), dtype=np.int64); p[Aidx] = Bi
        n1, n2, n3 = B.run(g[p], win[p], big[p], K)
        null.append([n1[0][0] if n1 else -np.inf, n2[0][0] if n2 else -np.inf, n3[0][0] if n3 else -np.inf])
    null = np.array(null) if null else np.zeros((0, 3))

    def describe(v, conds):
        names = [(d.names[S.feats[j]], ">=" if s == 1 else "<", float(S.line[j, t])) for (j, s, t) in conds]
        km = np.ones(len(d.ret), bool)
        for (nm, op, ln) in names:
            km &= L.keep_mask(d.X[:, d.names.index(nm)].astype(float), op, ln)
        kd = disc[km[disc]]
        out = {"conds": names, "dG_disc": round(v, 4), "disc_kept": len(kd), "disc_sr": round(float(d.win[kd].mean()), 3),
               "disc_mean_g": round(float(d.g[kd].mean()), 4)}
        dd = [float(d.g[r][km[r]].sum() - d.g[r].sum()) for r in [disc[d.di[disc] == di] for di in sorted(set(d.di[disc].tolist()))]]
        out["disc_days_pos"] = sum(1 for x in dd if x > 1e-12); out["disc_days_neg"] = sum(1 for x in dd if x < -1e-12)
        td = []
        for di in sorted(set(d.di[test].tolist())):
            r = test[d.di[test] == di]
            k = r[km[r]]
            bt = L.big_mask(d.ret[r])
            td.append({"day": d.days[di], "n": len(r), "sr": round(float(d.win[r].mean()), 3), "kept": len(k),
                       "kept_sr": round(float(d.win[k].mean()), 3) if len(k) else None,
                       "dG": round(float(d.g[k].sum() - d.g[r].sum()), 4), "big_kept": f"{int(bt[km[r]].sum())}/{int(bt.sum())}"})
        kt = test[km[test]]
        out["test_days"] = td
        out["test"] = {"n": len(test), "sr": round(float(d.win[test].mean()), 3), "kept": len(kt),
                       "kept_sr": round(float(d.win[kt].mean()), 3) if len(kt) else None,
                       "dG": round(float(d.g[kt].sum() - d.g[test].sum()), 4),
                       "days_pos": sum(1 for x in td if x["dG"] > 0), "days_neg": sum(1 for x in td if x["dG"] < 0)}
        return out

    pv = [float((1 + np.sum(null[:, i] >= x[0][0])) / (1 + len(null))) if (x and len(null)) else None for i, x in enumerate((s1, s2, s3))]
    results[grp] = {"n_disc": len(disc), "n_test": len(test), "base_sr": round(float(win.mean()), 3),
                    "base_test_sr": round(float(d.win[test].mean()), 3) if len(test) else None,
                    "K": K, "perms": len(null), "p_best": {"single": pv[0], "pair": pv[1], "triple": pv[2]},
                    "null_q95": [float(np.quantile(null[:, i], 0.95)) if len(null) else None for i in range(3)],
                    "singles": [describe(v, c) for v, c in s1[:6]],
                    "pairs": [describe(v, c) for v, c in s2[:6]],
                    "triples": [describe(v, c) for v, c in s3[:6]], "secs": round(time.time() - tg, 1)}
    r = results[grp]
    print(grp, "perms", r["perms"], "p", r["p_best"], "null95", [round(x, 3) if x is not None else None for x in r["null_q95"]], flush=True)
    for lab in ("singles", "pairs", "triples"):
        for x in r[lab][:2]:
            print(" ", lab, x["conds"], x["dG_disc"], x["disc_kept"], x["disc_sr"], "| test", x["test"], flush=True)
    fn = os.path.join(L.HERE, "out_s3_" + grp.replace(":", "_") + ".json")
    json.dump(r, open(fn, "w"), default=float)
print("done", round(time.time() - t0, 1), flush=True)
