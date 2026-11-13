import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 step 1: every single weather item as a yes/no entry filter, discovery 19 Oct - 4 Nov, test 5 - 12 Nov.
  py -3.13 -u s1_single.py GROUP [BUDGET_S]
GROUP = pool_events | pool_trades | fam:<family> | all.  Within-stratum permutation null (pool events: day;
otherwise book x day), studentised per feature; pooled-null p per feature -> BH; max-stat (FWER) p."""
import json, os, time
t0 = time.time()
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r04lib as L

groups = sys.argv[1].split(",")
budget_all = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
d = L.load()
print("loaded", round(time.time() - t0, 1), flush=True)


def run_group(grp, budget):
    t0 = time.time()
    CONTROLS = {"random_entry", "futures_only", "premium_momentum", "RAW", "conductor"}
    fam = np.array([L.family(b) for b in d.book])
    ok = np.isfinite(d.ret) & ~np.isin(d.book, list(CONTROLS))
    if grp == "pool_events" or grp == "pool_trades":
        ok &= np.isin(d.book, L.POOL)
        if grp == "pool_events":   # one row per trigger event: the highest-priority pool book firing at that second
            prio = {b: i for i, b in enumerate(L.POOL)}
            pr = np.array([prio.get(b, 9) for b in d.book])
            ix = np.flatnonzero(ok)
            o = np.lexsort((pr[ix], d.trig[ix], d.di[ix]))
            ix = ix[o]
            keyv = np.stack([d.di[ix], d.trig[ix]], 1)
            first = np.ones(len(ix), bool)
            first[1:] = np.any(keyv[1:] != keyv[:-1], axis=1)
            sel = np.zeros(len(d.ret), bool)
            sel[ix[first]] = True
            ok = sel
        strat_of = d.di if grp == "pool_events" else d.di * 1000 + np.unique(d.book, return_inverse=True)[1]
    elif grp.startswith("fam:"):
        ok &= fam == grp[4:]
        strat_of = d.di * 1000 + np.unique(d.book, return_inverse=True)[1]
    elif grp == "all":
        strat_of = d.di * 1000 + np.unique(d.book, return_inverse=True)[1]
    else:
        raise SystemExit("bad group")
    disc = np.flatnonzero(ok & ~d.test)
    test = np.flatnonzero(ok & d.test)
    print(grp, "disc", len(disc), "test", len(test), "load", round(time.time() - t0, 1), flush=True)
    # day-type fields are judged in days, not here (they cannot be told from luck on 12 days); they are still listed
    feats = np.array([j for j, nm in enumerate(d.names)])
    S = L.Search(d.X, disc, d.kinds, feats)
    g, win, big = d.g[disc], d.win[disc], L.big_mask(d.ret[disc])
    real, res = S.best(g, win, big)
    print("search built", round(time.time() - t0, 1), "lines", int(S.valid.sum()), flush=True)
    strata = strat_of[disc]
    A = np.argsort(strata, kind="stable")
    rng = np.random.default_rng(13_11_2026)
    nulls = []
    while time.time() - t0 < budget and len(nulls) < 1000:
        B = np.argsort(strata + rng.random(len(strata)) * 0.5, kind="stable")
        p = np.empty(len(strata), dtype=np.int64)
        p[A] = B
        gp, wp = g[p], win[p]
        bp = big[p]
        b_, _ = S.best(gp, wp, bp)
        nulls.append(b_)
    NU = np.array(nulls)                                # (P, F)
    P = len(NU)
    print("perms", P, round(time.time() - t0, 1), flush=True)
    NUf = np.where(np.isfinite(NU), NU, np.nan)
    mu, sd = np.nanmean(NUf, 0), np.nanstd(NUf, 0)
    sd = np.where(sd > 1e-12, sd, np.nan)
    z = (real - mu) / sd
    zn = (NUf - mu) / sd                                # null z's
    pool_null = np.sort(zn[np.isfinite(zn)])
    def pz(v):
        if not np.isfinite(v):
            return 1.0
        k = len(pool_null) - np.searchsorted(pool_null, v, side="left")
        return (1.0 + k) / (1.0 + len(pool_null))
    pv = np.array([pz(v) for v in z])
    # raw (unstandardised) per-feature p too
    praw = np.array([(1 + np.sum(NUf[:, j] >= real[j])) / (1 + P) if np.isfinite(real[j]) else 1.0 for j in range(len(real))])
    # BH at q = 0.10 over the features that had any valid line
    okf = np.isfinite(real)
    m = int(okf.sum())
    order = np.argsort(pv)
    bh = np.zeros(len(pv), bool)
    ranks = np.empty(len(pv)); ranks[order] = np.arange(1, len(pv) + 1)
    thr = [pv[order[k]] <= 0.10 * (k + 1) / m for k in range(len(pv))]
    kmax = max([k for k in range(len(pv)) if thr[k]], default=-1)
    if kmax >= 0:
        bh[order[: kmax + 1]] = True
    bh &= okf
    # max statistics (FWER)
    zmax_null = np.nanmax(zn, 1)
    gmax_null = np.nanmax(NUf, 1)
    jz = int(np.nanargmax(np.where(okf, z, -np.inf)))
    jg = int(np.nanargmax(np.where(okf, real, -np.inf)))
    fwer_z = float((1 + np.sum(zmax_null >= z[jz])) / (1 + P))
    fwer_g = float((1 + np.sum(gmax_null >= real[jg])) / (1 + P))


    def pick(j):
        """The best constrained line of feature j: (op, line, kept n, kept sr, big kept)."""
        bestv, best = -np.inf, None
        for s in (0, 1):
            dGm, k, sr, bk = res[s]
            t = int(np.argmax(dGm[j]))
            if dGm[j, t] > bestv:
                bestv = dGm[j, t]
                best = ("<" if s == 0 else ">=", float(S.line[j, t]), int(k[j, t]), float(sr[j, t]), int(bk[j, t]))
        return best


    def test_eval(jj, op, line):
        x = d.X[:, S.feats[jj]].astype(float)
        km = L.keep_mask(x, op, line)
        out = []
        for di in sorted(set(d.di[test].tolist())):
            r = test[d.di[test] == di]
            k = r[km[r]]
            bigt = L.big_mask(d.ret[r])
            out.append({"day": d.days[di], "n": len(r), "sr": round(float(d.win[r].mean()), 3),
                        "kept": len(k), "kept_sr": round(float(d.win[k].mean()), 3) if len(k) else None,
                        "mean_g": round(float(d.g[r].mean()), 4), "kept_mean_g": round(float(d.g[k].mean()), 4) if len(k) else None,
                        "dG": round(float(d.g[k].sum() - d.g[r].sum()), 4),
                        "big_kept": f"{int(bigt[km[r]].sum())}/{int(bigt.sum())}"})
        kk = test[km[test]]
        tot = {"n": len(test), "sr": round(float(d.win[test].mean()), 3) if len(test) else None,
               "kept": len(kk), "kept_sr": round(float(d.win[kk].mean()), 3) if len(kk) else None,
               "dG": round(float(d.g[kk].sum() - d.g[test].sum()), 4),
               "days_dG_pos": sum(1 for o in out if o["dG"] > 0), "days_dG_neg": sum(1 for o in out if o["dG"] < 0)}
        # discovery per-day consistency
        kd = disc[km[disc]]
        dd = []
        for di in sorted(set(d.di[disc].tolist())):
            r = disc[d.di[disc] == di]
            dd.append(float(d.g[r][km[r]].sum() - d.g[r].sum()))
        tot["disc_days_pos"] = int(sum(1 for v in dd if v > 1e-12)); tot["disc_days_neg"] = int(sum(1 for v in dd if v < -1e-12))
        return out, tot


    rows = []
    for jj in range(len(S.feats)):
        nm = d.names[S.feats[jj]]
        x = d.X[disc, S.feats[jj]].astype(float)
        fin = np.isfinite(x)
        cov = float(fin.mean())
        nuniq = int(np.unique(x[fin]).size) if fin.any() else 0
        # rank information (Spearman with the trade's log return) on discovery and test, finite rows only
        def rho(r):
            xx = d.X[r, S.feats[jj]].astype(float); ff = np.isfinite(xx)
            if ff.sum() < 20 or np.unique(xx[ff]).size < 2:
                return None
            a = np.argsort(np.argsort(xx[ff])).astype(float); b = np.argsort(np.argsort(d.g[r][ff])).astype(float)
            a -= a.mean(); b -= b.mean()
            den = np.sqrt((a * a).sum() * (b * b).sum())
            return round(float((a * b).sum() / den), 4) if den > 0 else None
        row = {"f": nm, "kind": d.kinds[S.feats[jj]], "cov": round(cov, 3), "nuniq": nuniq, "dayf": nm.split("=")[0] in L.DAY_FACTORS,
               "dG": None if not np.isfinite(real[jj]) else round(float(real[jj]), 4),
               "null_mu": None if not np.isfinite(mu[jj]) else round(float(mu[jj]), 4),
               "z": None if not np.isfinite(z[jj]) else round(float(z[jj]), 3), "p": round(float(pv[jj]), 6),
               "p_raw": round(float(praw[jj]), 4), "bh10": bool(bh[jj]), "rho_disc": rho(disc), "rho_test": rho(test)}
        if np.isfinite(real[jj]):
            op, line, kn, ksr, bk = pick(jj)
            row.update(op=op, line=line, kept=kn, kept_sr=round(ksr, 3), big_kept=bk)
        rows.append(row)
    top = sorted([r for r in rows if r["z"] is not None], key=lambda r: -r["z"])[:25]
    for r in top:
        jj = d.names.index(r["f"])
        jl = int(np.flatnonzero(S.feats == jj)[0])
        r["test_days"], r["test"] = test_eval(jl, r["op"], r["line"])
    base = {"n": len(disc), "sr": round(float(win.mean()), 4), "mean_ret": round(float(d.ret[disc].mean()), 3),
            "G": round(float(g.sum()), 4), "n_big": int(big.sum()), "test_n": len(test),
            "test_sr": round(float(d.win[test].mean()), 4) if len(test) else None,
            "test_G": round(float(d.g[test].sum()), 4), "min_keep": S.min_keep}
    out = {"group": grp, "base": base, "perms": P, "n_features": len(S.feats), "n_features_valid": m,
           "n_lines": int(S.valid.sum()) * 2, "fwer_best_z": {"f": d.names[S.feats[jz]], "z": float(z[jz]), "p": fwer_z},
           "fwer_best_dG": {"f": d.names[S.feats[jg]], "dG": float(real[jg]), "p": fwer_g},
           "n_bh10": int(bh.sum()), "top": top, "rows": rows, "secs": round(time.time() - t0, 1)}

    fn = os.path.join(L.HERE, "out_s1_" + grp.replace(":", "_") + ".json")
    json.dump(out, open(fn, "w"), default=float)
    print("base", base)
    print("FWER", out["fwer_best_z"], out["fwer_best_dG"], "BH10", out["n_bh10"])
    for r in top[:12]:
        print(f"{r['f']:28s} {r['op']} {r['line']:.4g} dG {r['dG']:+.3f} z {r['z']:+.2f} p {r['p']:.4f} kept {r['kept']} sr {r['kept_sr']} | test {r['test']}")
    print("done", out["secs"], flush=True)


for grp in groups:
    run_group(grp, budget_all / len(groups))
