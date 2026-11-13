import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 step 6: does an in-sample 'survivor' replicate? For every group and every feature, take the line found on
19 Oct - 4 Nov (s1 output) and score it on 5 - 12 Nov: test dG (sum log growth kept - all), test strike rate of kept,
per-day signs, big winners kept. Compare BH survivors with the rest (the honest multiple-testing check), and list the
filters that pass a strict out-of-sample bar."""
import glob, json, os, time
t0 = time.time()
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r04lib as L
d = L.load()
CONTROLS = {"random_entry", "futures_only", "premium_momentum", "RAW", "conductor"}
fam = np.array([L.family(b) for b in d.book])
name_ix = {n: i for i, n in enumerate(d.names)}
out = {}
strict = []
for fn in sorted(glob.glob(os.path.join(L.HERE, "out_s1_*.json"))):
    r = json.load(open(fn)); grp = r["group"]
    ok = np.isfinite(d.ret) & ~np.isin(d.book, list(CONTROLS))
    if grp in ("pool_events", "pool_trades"):
        ok &= np.isin(d.book, L.POOL)
        if grp == "pool_events":
            prio = {b: i for i, b in enumerate(L.POOL)}
            pr = np.array([prio.get(b, 9) for b in d.book])
            ix = np.flatnonzero(ok); ix = ix[np.lexsort((pr[ix], d.trig[ix], d.di[ix]))]
            kv = np.stack([d.di[ix], d.trig[ix]], 1)
            first = np.ones(len(ix), bool); first[1:] = np.any(kv[1:] != kv[:-1], axis=1)
            sel = np.zeros(len(d.ret), bool); sel[ix[first]] = True; ok = sel
    elif grp.startswith("fam:"):
        ok &= fam == grp[4:]
    test = np.flatnonzero(ok & d.test)
    tdays = sorted(set(d.di[test].tolist()))
    base_sr = float(d.win[test].mean())
    rows = []
    for row in r["rows"]:
        if row.get("op") is None:
            continue
        x = d.X[:, name_ix[row["f"]]].astype(float)
        km = L.keep_mask(x, row["op"], row["line"])
        kt = test[km[test]]
        per = []
        bigk = bigt = 0
        for di in tdays:
            rr = test[d.di[test] == di]
            per.append(float(d.g[rr][km[rr]].sum() - d.g[rr].sum()))
            b = L.big_mask(d.ret[rr]); bigk += int(b[km[rr]].sum()); bigt += int(b.sum())
        dG = float(d.g[kt].sum() - d.g[test].sum())
        ksr = float(d.win[kt].mean()) if len(kt) else 0.0
        rows.append({"f": row["f"], "op": row["op"], "line": row["line"], "bh": row["bh10"], "p": row["p"], "z": row["z"],
                     "dG_disc": row["dG"], "kept_frac_test": round(len(kt) / max(1, len(test)), 3),
                     "dG_test": round(dG, 4), "sr_test": round(ksr, 3), "base_sr_test": round(base_sr, 3),
                     "days_pos": sum(v > 1e-9 for v in per), "days_neg": sum(v < -1e-9 for v in per),
                     "big_kept": f"{bigk}/{bigt}", "big_frac": bigk / max(1, bigt)})
    bh = [x for x in rows if x["bh"]]; nb = [x for x in rows if not x["bh"]]
    def rate(xs, key):
        return round(float(np.mean([key(x) for x in xs])), 3) if xs else None
    up = lambda x: x["dG_test"] > 0
    both = lambda x: x["dG_test"] > 0 and x["sr_test"] > x["base_sr_test"]
    S = {"n_feats": len(rows), "n_bh": len(bh), "test_n": len(test), "base_sr_test": round(base_sr, 3),
         "bh_up": rate(bh, up), "nonbh_up": rate(nb, up), "bh_up_and_sr": rate(bh, both), "nonbh_up_and_sr": rate(nb, both),
         "bh_mean_dG_test": rate(bh, lambda x: x["dG_test"]), "nonbh_mean_dG_test": rate(nb, lambda x: x["dG_test"]),
         "top10z_up": rate(sorted(rows, key=lambda x: -(x["z"] or -9))[:10], up)}
    # strict out-of-sample bar: BH survivor, test dG>0, kept strike rate above base, no test day hurt more than helped,
    # at least 2 test days helped, >= 2/3 of test big winners kept, keeps >= 30 % of test trades
    for x in bh:
        if (x["dG_test"] > 0 and x["sr_test"] > x["base_sr_test"] and x["days_pos"] >= 2 and x["days_pos"] > x["days_neg"]
                and x["big_frac"] >= 2 / 3 and x["kept_frac_test"] >= 0.3):
            strict.append(dict(x, group=grp))
    out[grp] = {"summary": S, "rows": rows}
    print(grp, S, flush=True)
print("STRICT", len(strict))
for x in sorted(strict, key=lambda x: -x["dG_test"]):
    print(" ", x["group"], x["f"], x["op"], round(x["line"], 4), "dGd", x["dG_disc"], "dGt", x["dG_test"], "sr", x["sr_test"], "vs", x["base_sr_test"],
          "days", x["days_pos"], "/", x["days_neg"], "big", x["big_kept"], "kept", x["kept_frac_test"], "p", x["p"])
json.dump({"groups": out, "strict": strict}, open(os.path.join(L.HERE, "out_s6_replicate.json"), "w"), default=float)
print("done", round(time.time() - t0, 1))
