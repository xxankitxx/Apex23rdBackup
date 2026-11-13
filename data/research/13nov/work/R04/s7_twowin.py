import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 step 7: (a) the strict out-of-sample bar applied to EVERY line (BH or not): is the BH pass rate any higher?
(b) two-window consistency: does a line that helps in BOTH discovery halves (19-28 Oct, 29 Oct-4 Nov: growth up AND
strike rate up) help more often on 5-12 Nov than the rest?  (c) list the lines passing two windows + test, per group."""
import json, os, time
t0 = time.time()
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r04lib as L
d = L.load()
o = json.load(open(os.path.join(L.HERE, "out_s6_replicate.json")))
CONTROLS = {"random_entry", "futures_only", "premium_momentum", "RAW", "conductor"}
fam = np.array([L.family(b) for b in d.book])
ni = {n: i for i, n in enumerate(d.names)}
W1 = d.day < "2026-10-29"; W2 = (d.day >= "2026-10-29") & ~d.test
res = {}; passes = []
def strictbar(x):
    return (x["dG_test"] > 0 and x["sr_test"] > x["base_sr_test"] and x["days_pos"] >= 2 and x["days_pos"] > x["days_neg"]
            and x["big_frac"] >= 2 / 3 and x["kept_frac_test"] >= 0.3)
for grp, v in o["groups"].items():
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
    r1 = np.flatnonzero(ok & W1); r2 = np.flatnonzero(ok & W2)
    tw, ntw = [], []
    for x in v["rows"]:
        km = L.keep_mask(d.X[:, ni[x["f"]]].astype(float), x["op"], x["line"])
        good = True
        for r in (r1, r2):
            k = r[km[r]]
            if len(k) < 5 or not (d.g[k].sum() > d.g[r].sum() and d.win[k].mean() > d.win[r].mean()):
                good = False
        x["two_win"] = good
        (tw if good else ntw).append(x)
    bh = [x for x in v["rows"] if x["bh"]]; nb = [x for x in v["rows"] if not x["bh"]]
    f = lambda xs, k: round(float(np.mean([k(x) for x in xs])), 3) if xs else None
    up = lambda x: float(x["dG_test"] > 0)
    S = {"strict_rate_bh": f(bh, strictbar), "strict_rate_nonbh": f(nb, strictbar),
         "n_two_win": len(tw), "two_win_up": f(tw, up), "rest_up": f(ntw, up),
         "two_win_strict": f(tw, strictbar), "rest_strict": f(ntw, strictbar),
         "n_tw_bh": sum(1 for x in tw if x["bh"]), "tw_bh_strict": f([x for x in tw if x["bh"]], strictbar)}
    res[grp] = S
    for x in tw:
        if x["bh"] and strictbar(x) and (x["dG_disc"] or 0) > 0:
            passes.append(dict(x, group=grp))
    print(grp, S, flush=True)
print("PASS (BH + two windows + strict test):", len(passes))
for x in sorted(passes, key=lambda x: (x["group"], -x["dG_test"])):
    print(" ", x["group"], x["f"], x["op"], round(x["line"], 4), "dGd", x["dG_disc"], "dGt", x["dG_test"], "sr", x["sr_test"], "vs",
          x["base_sr_test"], "days", x["days_pos"], "/", x["days_neg"], "big", x["big_kept"], "kept", x["kept_frac_test"])
json.dump({"summary": res, "passes": passes}, open(os.path.join(L.HERE, "out_s7_twowin.json"), "w"), default=float)
print("done", round(time.time() - t0, 1))
