"""PR-010: how often does earned() let a forecaster with NO skill make a claim? (PKG-03, 12 Nov 2026)

Simulates S no-skill trading days, each with BUY_MIN_DAYS earlier no-skill forward days behind it, and asks
apex.forecast_lab.core.earned() at 12 moments of the day (every 30 minutes of record) whether a direction claim
(5 and 15 min) or a buy case (5 and 15 min) is earned. A claim counts as a false earn when it is earned at ANY of
those moments. The acceptance line is at most 5 % of days per claim and horizon. The old gates (a coin's 0.25 as
the Brier baseline, one day's record, no margin on the error) are scored on the same days for comparison.

No skill means:
  direction  each independent clear call is right with chance 0.5; the CRPS against 'no move' is level (ratio
             1 + noise of 2 %)
  buy        each day has its own win base rate (uniform 0.30 to 0.50: spread and decay keep it under a half); the
             stated win chance is that base rate plus noise unrelated to the outcome; the middle premium error is
             'no change' plus noise
The lean is set clear (0.5 sd) so it never blocks a claim: the worst case for false earns.

Run:  py -3.13 research/forecast_lab/null_earned.py [--sims 10000] [--out path.json]
Pure numpy on independent units; one process, no files read. The old gates are vectorised over all days. A day on which
every claim fails a condition the new gates cannot do without (pooled skill above 0 on the earlier days, and today's
own hit rate or win-chance score at some moment) is counted as not earned without asking earned(); that shortcut is
exact. The rest go through the real cross_day() and earned(). The time
is printed ('secs'); measure it on an idle machine before quoting it."""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from apex.forecast_lab import core as C  # noqa: E402

HS = (300, 900)
CHECKS = 12                                   # moments of the day earned() is asked (every 30 min of record)
IND_DAY = {300: 75, 900: 25}                  # independent option checks in a full day (one 15-s slot each)
DIR_DAY = {300: 60, 900: 20}                  # independent clear futures calls in a full day


def sim_day_rows(rng, S, h):
    """Cumulative score rows at CHECKS moments for S no-skill days at horizon h: (fut rows, opt rows), each a
    list over moments of dicts as _score_view() gives them."""
    m = IND_DAY[h]
    p0 = rng.uniform(0.30, 0.50, (S, 1))
    win = (rng.random((S, m)) < p0).astype(float)
    pp = np.clip(p0 + 0.08 * rng.standard_normal((S, m)), 0.01, 0.99)
    # causal climatology: the running win rate before each ticket (a coin for the first)
    cw = np.cumsum(win, 1)
    prior = np.c_[np.full((S, 1), 0.5), (cw[:, :-1] / np.arange(1, m))]
    b = (pp - win) ** 2
    bc = (prior - win) ** 2
    hi = pp >= C.WILSON_PP
    naive = 4.5 + 0.3 * rng.standard_normal((S, 1))
    err = naive * (1 + 0.03 * rng.standard_normal((S, m)))
    errn = np.repeat(naive, m, 1) * (1 + 0.03 * rng.standard_normal((S, m)))
    errd = np.repeat(naive, m, 1) * (1 + 0.03 * rng.standard_normal((S, m)))
    dm = DIR_DAY[h]
    dhit = (rng.random((S, dm)) < 0.5).astype(float)
    ratio = 1.0 + 0.02 * rng.standard_normal((S, 1))
    per = h / C.TICKET_EVERY                 # raw tickets (slots) behind one independent check
    out = []
    for c in range(1, CHECKS + 1):
        k = max(1, int(round(m * c / CHECKS)))
        kd = max(1, int(round(dm * c / CHECKS)))
        nh = hi[:, :k].sum(1)
        opt = dict(n=(k * per * 2.0), slots=k * per, slots_buy=k * per, n_buy=k * per * 2.0,
                   brier_buy=b[:, :k].mean(1), brier_clim=bc[:, :k].mean(1), win=win[:, :k].mean(1),
                   brier=b[:, :k].mean(1), brier_base=((0.5 - win[:, :k]) ** 2).mean(1),
                   err=err[:, :k].mean(1), err_naive=errn[:, :k].mean(1), err_decay=errd[:, :k].mean(1),
                   slots_hi=nh * per, win_hi=np.where(nh > 0, (win[:, :k] * hi[:, :k]).sum(1) / np.maximum(nh, 1), np.nan),
                   cov=np.full(S, 0.8))
        fut = dict(n=np.full(S, kd * h / C.ORIGIN_EVERY * 2.0), cov=np.full(S, 0.8),
                   dir_n=np.full(S, kd * h / C.ORIGIN_EVERY), dir_hit=dhit[:, :kd].mean(1),
                   skill=1.0 - ratio[:, 0])
        out.append((fut, opt))
    full = dict(on=m * per * 2.0, on_buy=m * per * 2.0, obrier_buy=b.mean(1) * m * per * 2.0,
                obrier_clim=bc.mean(1) * m * per * 2.0, oerr=err.mean(1) * m * per * 2.0,
                oerr_naive=errn.mean(1) * m * per * 2.0, dir_n=dm * h / C.ORIGIN_EVERY,
                dir_hit=dhit.mean(1) * dm * h / C.ORIGIN_EVERY, crps=ratio[:, 0] * 1000.0, crps_still=1000.0)
    return out, full


def _v(x, i):
    return None if x is None else (float(x[i]) if np.ndim(x) else float(x))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    t0 = time.time()
    rng = np.random.default_rng(a.seed)
    S, D = a.sims, C.BUY_MIN_DAYS
    today = {h: sim_day_rows(rng, S, h)[0] for h in HS}
    prior = [{h: sim_day_rows(rng, S, h)[1] for h in HS} for _ in range(D)]
    new = {f"{c}:{h}": 0 for c in ("dir", "buy") for h in HS}
    old = dict(new)
    hj = {h: C.H.index(h) for h in HS}
    # The old gates, vectorised over all days: earned at ANY of the moments.
    for h in HS:
        od, ob = np.zeros(S, bool), np.zeros(S, bool)
        for fu, op in today[h]:
            od |= (fu["dir_n"] * C.ORIGIN_EVERY / h >= 20) & (fu["dir_hit"] >= 0.6) & (fu["skill"] > 0)
            ob |= ((op["n"] * C.TICKET_EVERY / h / 2 >= 20) & (op["brier"] <= op["brier_base"] - 0.01)
                   & (op["err"] < op["err_naive"]))
        old[f"dir:{h}"], old[f"buy:{h}"] = int(od.sum()), int(ob.sum())
    # Exact pruning: both new claims require cross_day's 'ok', and cross_day's bootstrap is never ok when the pooled
    # point estimate is not above 0 (it returns that point), nor for buy when the error share is under DAY_ERR_SHARE.
    # A day whose earlier days fail every one of these necessary conditions cannot earn anything: earned() is not
    # asked for it. Every other day goes through the real cross_day() and earned().
    maybe = np.zeros(S, bool)
    for h in HS:
        P = [prior[d][h] for d in range(D)]
        dn = sum(np.full(S, p["dir_n"], float) for p in P)
        dpt = sum(p["dir_hit"] - 0.5 * p["dir_n"] for p in P) / dn
        cpt = sum(p["crps_still"] - p["crps"] for p in P) / sum(np.full(S, p["crps_still"], float) for p in P)
        bpt = sum(p["obrier_clim"] - p["obrier_buy"] for p in P)
        esh = np.mean([p["oerr"] / p["on"] < p["oerr_naive"] / p["on"] - C.ERR_MARGIN for p in P], axis=0)
        # ... and today's record must pass its own necessary conditions at some moment
        td, tb = np.zeros(S, bool), np.zeros(S, bool)
        for fu, op in today[h]:
            td |= (fu["dir_n"] * C.ORIGIN_EVERY / h >= C.DIR_MIN_CHECKS) & (fu["dir_hit"] >= C.DIR_HIT) & (fu["skill"] > 0)
            tb |= op["brier_buy"] <= np.minimum(0.25, op["brier_clim"]) - C.BUY_MARGIN
        maybe |= ((dpt > 0) & (cpt > 0) & td) | ((bpt > 0) & (esh >= C.DAY_ERR_SHARE) & tb)
    for i in np.flatnonzero(maybe):
        days = []
        for d in range(D):
            sc = {}
            for name in ("on", "on_buy", "obrier_buy", "obrier_clim", "oerr", "oerr_naive", "dir_n", "dir_hit",
                         "crps", "crps_still"):
                arr = [0.0] * len(C.H)
                for h in HS:
                    arr[hj[h]] = _v(prior[d][h][name], i)
                sc[name] = arr
            days.append(dict(day=f"2026-10-{d + 1:02d}", H=list(C.H), forward=True, score=sc))
        cross = C.cross_day(days, "2026-11-01", B=500)
        memo = {}
        hit_new = set()
        for c in range(CHECKS):
            fut_rows, opt_rows, path = [], [], []
            for h in HS:
                fu, op = today[h][c]
                fut_rows.append(dict(h=h, **{k: _v(v, i) for k, v in fu.items()}))
                opt_rows.append(dict(h=h, **{k: (None if (np.ndim(v) and not np.isfinite(v[i])) else _v(v, i))
                                             for k, v in op.items()}))
                path.append(dict(h=h, mu=5.0, sd=10.0))
            p = dict(day="2026-11-01", score=dict(fut=fut_rows, opt=opt_rows), path=path)
            e = C.earned(p, cross=cross, memo=memo)
            for h in HS:
                if e["dir_h"][str(h)]["earned"]:
                    hit_new.add(f"dir:{h}")
                if h in e["buy_h"]:
                    hit_new.add(f"buy:{h}")
        for k in hit_new:
            new[k] += 1
    res = dict(sims=S, asked=int(maybe.sum()), secs=round(time.time() - t0, 1), limit=0.05,
               new={k: round(v / S, 4) for k, v in new.items()}, old={k: round(v / S, 4) for k, v in old.items()})
    res["pass"] = all(v <= 0.05 for v in res["new"].values())
    print(json.dumps(res, indent=1))
    if a.out:
        tmp = a.out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
        os.replace(tmp, a.out)
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
