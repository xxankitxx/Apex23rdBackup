"""Runner analysis on the 14 taped days (ChatGPT 6 Nov proposal). Writes analysis.json and prints tables.

1. ONSETS (real vs fake move): every candidate move start (forward +-8 pts in 60 s, one per direction per 5 min).
   Label: buying the nearest-ITM option of that side became a RUNNER (+20 % before -10 % within 15 min) or a DUD
   (-10 % first, or never above +5 %). Each feature: AUC overall, per day, and how many days agree in sign.
   All features together: gradient boosting trained leave-one-day-out (every prediction is on an unseen day),
   AUC, calibration, and a label-shuffle baseline.
2. RUNNERS caught vs missed by c20_9x (kit trades): a runner event is caught when a c20_9x trade of the same side
   entered between 60 s before its start and its end.
3. c20_9x DEAD LOSERS (peak < +5 %, P&L < 0) vs its WINNERS, features at the entry second.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from events import day_data, outcomes, runner_events, onsets, features  # noqa: E402

DAYS = ["2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28",
        "2026-10-29", "2026-10-30", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"]
EXPIRY = {"2026-10-19", "2026-10-27", "2026-11-03"}
KIT = r"C:\Users\ANKITM~1\AppData\Local\Temp\claude\D--ApexOptions\4fc710fd-915d-4b6c-be6c-118168a8b13b\scratchpad\team"


def kit_trades():
    """c20_9x trades per day from the 12-day kit baseline, plus 5-6 Nov run on the kit if it has been built."""
    b = json.load(open(os.path.join(KIT, "C12_baseline.json"), encoding="utf-8"))
    out = {d: v["trades"] for d, v in b.items()}
    p = os.path.join(HERE, "kit_trades_56.json")
    if os.path.exists(p):
        out.update(json.load(open(p, encoding="utf-8")))
    return out


def _row(A, hms):
    from datetime import datetime, timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    h, m, s = (int(x) for x in hms.split(":"))
    y, mo, d = (int(x) for x in A["day"].split("-"))
    t = datetime(y, mo, d, h, m, s, tzinfo=IST).timestamp()
    return int(np.clip(np.searchsorted(A["T"], t), 0, len(A["T"]) - 1))


def auc(y, x):
    from sklearn.metrics import roc_auc_score
    ok = np.isfinite(x)
    if ok.sum() < 10 or len(set(y[ok])) < 2:
        return np.nan
    return float(roc_auc_score(y[ok], x[ok]))


def build():
    tabs, runners, deads = [], [], []
    kt = kit_trades()
    for d in DAYS:
        A = day_data(d)
        O = outcomes(A)
        R = runner_events(A, O)
        r, s = onsets(A)
        Fm = features(A, r, s)
        w20 = O["win20"][r, s]
        dud = ((np.isfinite(O["tdn"][r, s]) & ~(O["t10"][r, s] < O["tdn"][r, s])) | (O["mfe"][r, s] < 0.05))
        lab = np.where(w20 > 0, 1, np.where(dud, 0, -1))           # -1: in between (neither runner nor dud)
        tabs.append({"day": d, "rows": r, "sides": s, "y": lab, "F": Fm,
                     "mfe": O["mfe"][r, s], "r300": O["r300"][r, s], "valid": O["valid"][r, s]})
        trades = kt.get(d, [])
        tr = [(_row(A, t["t_in"]), 0 if t["rr"] == "CE" else 1, t) for t in trades]
        for e in R:
            caught = any(t[1] == e["side"] and e["start"] - 60 <= t[0] <= e["end"] for t in tr)
            runners.append(dict(e, day=d, caught=caught, have_trades=d in kt))
        for i, sd, t in tr:
            deads.append({"day": d, "row": i, "side": sd, "dead": t["peak_pct"] < 5 and t["pnl"] < 0,
                          "win": t["pnl"] > 0, "pnl": t["pnl"]})
        print(d, "onsets", len(r), "runners", int((lab == 1).sum()), "duds", int((lab == 0).sum()),
              "runner events", len(R), "c20_9x trades", len(trades), flush=True)
    return tabs, runners, deads


def main():
    tabs, runners, deads = build()
    keys = list(tabs[0]["F"].keys())
    X = np.vstack([np.column_stack([t["F"][k] for k in keys]) for t in tabs])
    y = np.concatenate([t["y"] for t in tabs])
    dayv = np.concatenate([[t["day"]] * len(t["y"]) for t in tabs])
    sel = y >= 0
    X, y, dayv = X[sel], y[sel], dayv[sel]
    res = {"n_onsets": int(sel.sum()), "n_runner": int(y.sum()), "n_dud": int((y == 0).sum()), "features": {}}
    print(f"\nONSETS used: {sel.sum()} (runner {y.sum()}, dud {(y == 0).sum()}), base runner rate {y.mean():.3f}")
    # ---- single features: overall AUC, per-day AUC, sign agreement
    rows = []
    for c, k in enumerate(keys):
        a = auc(y, X[:, c])
        per = [auc(y[dayv == d], X[dayv == d, c]) for d in DAYS]
        per = [p for p in per if np.isfinite(p)]
        agree = sum(1 for p in per if (p - 0.5) * (a - 0.5) > 0) if np.isfinite(a) else 0
        rows.append((k, a, agree, len(per), float(np.nanmedian(per)) if per else np.nan))
        res["features"][k] = {"auc": a, "days_agree": agree, "days": len(per)}
    rows.sort(key=lambda r: -abs((r[1] if np.isfinite(r[1]) else 0.5) - 0.5))
    print("\nfeature              AUC   days same side / days   median day AUC")
    for k, a, ag, nd, md in rows:
        print(f"{k:18s} {a:6.3f}   {ag:2d} / {nd:2d}              {md:6.3f}")
    # ---- all features together, leave-one-day-out
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    p = np.full(len(y), np.nan)
    for d in DAYS:
        te = dayv == d
        if te.sum() == 0 or len(set(y[~te])) < 2:
            continue
        m = HistGradientBoostingClassifier(max_depth=3, max_iter=150, learning_rate=0.05, min_samples_leaf=20,
                                           l2_regularization=1.0, random_state=0)
        m.fit(X[~te], y[~te])
        p[te] = m.predict_proba(X[te])[:, 1]
    ok = np.isfinite(p)
    lodo_auc = float(roc_auc_score(y[ok], p[ok]))
    rng = np.random.default_rng(0)
    null = []
    for b in range(20):                                   # the same procedure on shuffled labels (within each day)
        ys = y.copy()
        for d in DAYS:
            ix = np.nonzero(dayv == d)[0]
            ys[ix] = rng.permutation(ys[ix])
        q = np.full(len(y), np.nan)
        for d in DAYS:
            te = dayv == d
            if te.sum() == 0 or len(set(ys[~te])) < 2:
                continue
            m = HistGradientBoostingClassifier(max_depth=3, max_iter=150, learning_rate=0.05, min_samples_leaf=20,
                                               l2_regularization=1.0, random_state=b)
            m.fit(X[~te], ys[~te])
            q[te] = m.predict_proba(X[te])[:, 1]
        null.append(float(roc_auc_score(ys[ok], q[ok])))
    res["lodo_auc"], res["null_auc"] = lodo_auc, null
    print(f"\nALL FEATURES, leave-one-day-out AUC {lodo_auc:.3f}; shuffled-label AUC "
          f"{np.mean(null):.3f} +- {np.std(null):.3f} (max {np.max(null):.3f})")
    per_day = {d: auc(y[(dayv == d) & ok], p[(dayv == d) & ok]) for d in DAYS}
    res["lodo_auc_by_day"] = per_day
    print("by held-out day:", {d[5:]: round(v, 3) for d, v in per_day.items() if np.isfinite(v)})
    print("\ncalibration on unseen days (predicted runner chance -> actual):")
    cal = []
    for lo, hi in ((0, .1), (.1, .2), (.2, .3), (.3, .4), (.4, .6), (.6, 1.01)):
        mm = ok & (p >= lo) & (p < hi)
        if mm.sum():
            cal.append((lo, hi, int(mm.sum()), float(p[mm].mean()), float(y[mm].mean())))
            print(f"  {lo:.1f}-{min(hi, 1):.1f}: n={mm.sum():4d} predicted {p[mm].mean():.2f} actual {y[mm].mean():.2f}")
    res["calibration"] = cal
    # ---- runners caught vs missed
    have = [e for e in runners if e["have_trades"]]
    cau = [e for e in have if e["caught"]]
    print(f"\nRUNNER EVENTS (+20 % before -10 %, one per move): {len(runners)} on {len(DAYS)} days; on days with "
          f"c20_9x trades: {len(have)}, caught {len(cau)}, missed {len(have) - len(cau)}")
    res["runners"] = {"total": len(runners), "with_trades": len(have), "caught": len(cau)}
    big = [e for e in have if e["mfe_best"] >= 0.40]
    print(f"  of which big (best possible >= +40 %): {len(big)}, caught {sum(e['caught'] for e in big)}")
    if have:
        Fr = {}
        for d in DAYS:
            ev = [e for e in have if e["day"] == d]
            if not ev:
                continue
            A = day_data(d)
            Fd = features(A, np.array([e["start"] for e in ev]), np.array([e["side"] for e in ev]))
            for k, v in Fd.items():
                Fr.setdefault(k, []).extend(v.tolist())
        cflag = np.array([e["caught"] for d in DAYS for e in have if e["day"] == d], float)
        print("  features that differ most at the runner's start, caught vs missed (AUC, + = higher when caught):")
        diffs = sorted(((k, auc(cflag, np.array(v))) for k, v in Fr.items()), key=lambda r: -abs((r[1] if np.isfinite(r[1]) else .5) - .5))
        for k, a in diffs[:10]:
            print(f"    {k:18s} {a:.3f}")
        res["caught_vs_missed"] = diffs
    # ---- dead losers vs winners (c20_9x entries)
    dl = [x for x in deads if x["dead"] or x["win"]]
    if dl:
        Fd_all = {}
        lab = []
        for d in DAYS:
            ev = [x for x in dl if x["day"] == d]
            if not ev:
                continue
            A = day_data(d)
            Fd = features(A, np.array([x["row"] for x in ev]), np.array([x["side"] for x in ev]))
            for k, v in Fd.items():
                Fd_all.setdefault(k, []).extend(v.tolist())
            lab += [0.0 if x["dead"] else 1.0 for x in ev]
        lab = np.array(lab)
        print(f"\nc20_9x DEAD LOSERS {int((lab == 0).sum())} vs WINNERS {int(lab.sum())}: features at entry (AUC, + = higher on winners):")
        diffs = sorted(((k, auc(lab, np.array(v))) for k, v in Fd_all.items()), key=lambda r: -abs((r[1] if np.isfinite(r[1]) else .5) - .5))
        for k, a in diffs[:10]:
            print(f"    {k:18s} {a:.3f}")
        res["dead_vs_win"] = diffs
    json.dump(res, open(os.path.join(HERE, "analysis.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
