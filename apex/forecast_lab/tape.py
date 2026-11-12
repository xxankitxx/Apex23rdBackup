"""Forecast Lab on recorded sessions (data/research/ds_v2): warm start and offline tests.

Usage: py -3.13 -m apex.forecast_lab.tape warm  <first day> <last day>   learn on these sessions (no simulation), save
                                                                           data/forecast_lab/state_warm.json
       py -3.13 -m apex.forecast_lab.tape test  <day> [state file]       full run with simulation and scoring on one
                                                                           session; prints the scoreboard and timing
Reads only the recorded set; writes only under data/forecast_lab/."""
import glob
import json
import os
import sys
import time

import numpy as np

from .. import config
from .core import Lab

ROOT = config.ROOT
DS = os.path.join(ROOT, "data", "research", "ds_v2")
OUT = os.path.join(ROOT, "data", "forecast_lab")


def parts_for(day):
    return sorted(glob.glob(os.path.join(DS, f"{day}*.npz")))


def feed(lab, path, max_s=None, on_second=None):
    """Feed one recorded part to the lab, second by second. Returns the number of seconds fed."""
    z = np.load(path)
    if z["t"].ndim != 1 or len(z["t"]) == 0 or z["opt"].ndim < 4:     # an empty part (a restart with no data): nothing to feed
        return 0
    n = len(z["strikes"])
    order = np.argsort(z["strikes"])
    K = z["strikes"][order].astype(float)
    o = z["opt"][:, :n].astype(float)[:, order]
    age = z["age"][:, :n].astype(float)[:, order]
    t = z["t"].astype(float)
    fut = z["fut"].astype(float)
    fa = z["fa"].astype(float)
    exp = str(z["expiry"])
    hw = z["hw"].astype(float)
    hwa = z["hwa"].astype(float)
    w = z["w"].astype(float)[:hw.shape[1]]
    bank = np.array([str(g) in ("bank", "nbfc") for g in z["g"]][:hw.shape[1]], bool)
    fed = 0
    for i in range(len(t)):
        if max_s is not None and fed >= max_s:
            break
        stale = not (fa[i, 0] <= 3.0)
        inp = dict(t=t[i], fb=np.nan if stale else fut[i, 0], fa=np.nan if stale else fut[i, 1], fl=fut[i, 2], fv=fut[i, 3],
                   fbq=fut[i, 4], faq=fut[i, 5], K=K, ob=o[i, :, :, 0], oa=o[i, :, :, 1], og=age[i], expiry=exp,
                   hw=np.where(hwa[i] <= 30.0, hw[i], np.nan), hw_w=w, hw_bank=bank)
        lab.step(inp)
        fed += 1
        if on_second is not None:
            on_second(lab, t[i])
    return fed


def collect(day):
    """Run one recorded session through the lab (no simulation) and save what training needs:
    X      one row per 5-s origin: t, F, v_ref, then brain.FEATS
    S      the future's mid every second: t, F
    IV     every 5 s: t, forward, at-the-money IV, years to expiry; and the per-strike IV row with its strikes
    -> data/forecast_lab/collect/<day>.joblib"""
    import joblib
    lab = Lab(options=True, collect=True)
    lab.simulate = False
    S, IVT, IVM = [], [], []

    def grab(lb, t):
        if lb.n and lb.last_t == t:
            S.append((t, lb.fm[(lb.n - 1) % len(lb.fm)]))
        c = lb.chain
        if c is not None and c["t"] == t and np.isfinite(c["atm_iv"]):
            IVT.append((t, c["Fs"], c["atm_iv"], c["T"]))
            IVM.append((c["K"].copy(), c["iv"][:, 0].copy()))
    for p in parts_for(day):
        feed(lab, p, on_second=grab)
    X = np.array([np.r_[t, F, v, x] for t, F, v, x in lab.collect], float) if lab.collect else np.zeros((0, 3))
    out = dict(day=day, X=X, S=np.array(S, float), IVT=np.array(IVT, float), IVM=IVM)
    os.makedirs(os.path.join(OUT, "collect"), exist_ok=True)
    joblib.dump(out, os.path.join(OUT, "collect", f"{day}.joblib"), compress=3)
    print(day, "origins", len(X), "seconds", len(S), "iv rows", len(IVT), flush=True)


def walk(tag, use_brain, first=None, last=None):
    """The whole lab, day after day, as it would have run live: online learning carried from one session to the next;
    with use_brain, each session loads the brain fitted on the sessions before it (brains/brain_<previous>.joblib).
    The first MIN sessions without a brain only warm the online part and are not reported.
    -> data/forecast_lab/walk_<tag>.json (per-session scoreboards)"""
    from .brain import Brain
    days = sorted({os.path.basename(p)[:10] for p in glob.glob(os.path.join(DS, "*.npz"))})
    brains = sorted(glob.glob(os.path.join(OUT, "brains", "brain_*.joblib")))
    first_test = days[5] if first is None else first
    state, res = None, {}
    t0 = time.time()
    for i, d in enumerate(days):
        if last and d > last:
            break
        br = None
        if use_brain and i > 0:
            pth = os.path.join(OUT, "brains", f"brain_{days[i - 1]}.joblib")
            br = Brain(pth) if os.path.exists(pth) else None
        test = d >= first_test
        lab = Lab(state=state, options=True, brain=br)
        lab.simulate = test                                  # the warm-up sessions need no option simulation
        for p in parts_for(d):
            feed(lab, p)
        if test:
            sv = lab._score_view()
            res[d] = dict(brain=bool(br is not None and br.ok), score=sv,
                          weights5={e: round(float(lab.hedge[3].w[k]), 3) for k, e in enumerate(__import__("apex.forecast_lab.core", fromlist=["x"]).EXPERTS)})
            f5 = sv["fut"][3]; o5 = sv["opt"][3]
            print(tag, d, "brain" if res[d]["brain"] else "plain", "| fut 5m cov", f5["cov"], "crps", f5["crps"], "width", f5["width"], "pin", f5["pin"],
                  "skill", f5["skill"], "dir", f5["dir_hit"], "of", f5["dir_n"], "| opt 5m cov", o5["cov"], "pin", o5["pin"], "err", o5["err"],
                  "naive", o5["err_naive"], f"| {time.time() - t0:.0f} s", flush=True)
        state = json.loads(json.dumps(lab.to_json()))
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, f"walk_{tag}.json"), "w"), indent=1)


def warm(first, last):
    days = sorted({os.path.basename(p)[:10] for p in glob.glob(os.path.join(DS, "*.npz"))})
    days = [d for d in days if first <= d <= last]
    lab = Lab(options=True)
    lab.simulate = False                     # learning the futures models needs the chain (IV) but no simulation
    t0 = time.time()
    for d in days:
        for p in parts_for(d):
            feed(lab, p)
        s5 = lab._score_view()["fut"][3]
        print(d, "5-min futures forecasts scored", s5["n"], "coverage", s5["cov"], "skill vs still", s5["skill"],
              "direction", s5["dir_hit"], "of", s5["dir_n"], f"{time.time() - t0:.0f} s", flush=True)
    os.makedirs(OUT, exist_ok=True)
    st = lab.to_json()
    st["warm"] = dict(days=days, built=time.strftime("%Y-%m-%d %H:%M:%S"))
    with open(os.path.join(OUT, "state_warm.json"), "w", encoding="utf-8") as f:
        json.dump(st, f)
    print("weights at 5 min:", {e: round(float(lab.hedge[3].w[i]), 3) for i, e in enumerate(("still", "momentum", "flow", "reversion", "blend"))})
    print("saved", os.path.join(OUT, "state_warm.json"))


def test(day, state_file=None):
    from .brain import Brain
    st = None
    if state_file and os.path.exists(state_file):
        st = json.load(open(state_file, encoding="utf-8"))
    bp = os.path.join(OUT, "brain.joblib")
    lab = Lab(state=st, options=True, brain=Brain(bp) if os.path.exists(bp) else None)
    t0 = time.time()
    steps = 0
    worst = 0.0
    for p in parts_for(day):
        z = np.load(p)
        t = z["t"]
        steps += len(t)
        a = time.time()
        feed(lab, p)
        worst = max(worst, lab.cost["full_ms"])
    wall = time.time() - t0
    pv = lab.panel()
    print(json.dumps(dict(day=day, seconds=steps, wall_s=round(wall, 1), per_second_ms=round(wall / max(steps, 1) * 1e3, 2),
                          step_ms=lab.cost, score=pv["score"], learn=pv["learn"], say=pv["say"]), indent=1, default=str))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"test_{day}.json"), "w", encoding="utf-8") as f:
        json.dump(pv, f, default=str)


if __name__ == "__main__":
    from .live import below_normal
    if "--low" in sys.argv:                  # during a live session: never compete with it
        sys.argv.remove("--low")
        below_normal()
    if sys.argv[1] == "walk":
        walk(sys.argv[2], sys.argv[3] == "brain")
    elif sys.argv[1] == "collect":
        for d_ in sys.argv[2:]:
            collect(d_)
    elif sys.argv[1] == "warm":
        warm(sys.argv[2], sys.argv[3])
    else:
        test(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
