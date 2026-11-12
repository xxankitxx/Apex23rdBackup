"""12 Nov (PKG-08): the Forecast Lab's decay register, rent and implied move on one business clock, measured decay
with its standard error, and the Stage B option paths (behind core.PRICING_STAGE_B, off). Built on the real 11 Nov
15:14 payload (tests/fixtures/forecast_lab) and small synthetic chains. Fast: one option simulation at most."""
import copy
import json
import math
import os
from collections import deque
from datetime import datetime

import numpy as np

from apex import config, greeks
from apex.forecast_lab import clock as CK
from apex.forecast_lab import core as C

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "forecast_lab")


def _fixture():
    with open(os.path.join(FIX, "payload_2026-11-11_1514_flat.json"), encoding="utf-8") as f:
        p = json.load(f)
    p["day"] = "2026-11-11"
    return p


def _chain(now, exp, Fs, K, iv, mid=None):
    """A chain dict as Lab._chain builds it, priced by Black-76 at the given strike IVs unless mids are given."""
    K = np.asarray(K, float)
    n = len(K)
    T = greeks.years_to_expiry(exp, now)
    IV = np.c_[iv, iv]
    if mid is None:
        mid = np.c_[C.b76(Fs, K, T, IV[:, 0], np.ones(n, bool)), C.b76(Fs, K, T, IV[:, 1], np.zeros(n, bool))]
    call = np.r_[np.ones(n, bool), np.zeros(n, bool)]
    g = C.b76_greeks(np.full(2 * n, Fs), np.r_[K, K], T, np.r_[IV[:, 0], IV[:, 1]], call)
    G = {k: np.c_[v[:n], v[n:]] for k, v in g.items()}
    atm_iv = float(np.interp(Fs, K, IV[:, 0]))
    sp = np.maximum(0.05, 0.002 * mid)
    return dict(t=now.timestamp(), K=K, ob=mid - sp, oa=mid + sp, og=np.zeros((n, 2)), mid=mid, Fs=Fs, F=Fs, T=T,
                iv=IV, atm_iv=atm_iv, slope=np.nan, g=G, exp=exp, now=now, k_atm=int(np.argmin(np.abs(K - Fs))), basis=0.0)


def _lab_from_payload(p):
    rows = p["decay"]
    K = sorted({r["strike"] for r in rows})
    iv = np.array([next(r["iv"] for r in rows if r["strike"] == k and r["side"] == "CE") / 100.0 for k in K])
    mid = np.array([[next(r["mid"] for r in rows if r["strike"] == k and r["side"] == s) for s in ("CE", "PE")] for k in K])
    now = datetime.fromtimestamp(p["t"], config.IST)
    lab = C.Lab(n_paths=20, options=False)
    lab.day, lab.last_t = p["day"], p["t"]
    lab.chain = _chain(now, p["chain"]["exp"], p["chain"]["Fs"], K, iv, mid=mid)
    lab.chain["atm_iv"] = p["chain"]["atm_iv"] / 100.0
    lab.vol[600] = p["rent"]["d10"] ** 2 / 60.0
    lab.vol[1800] = p["rent"]["d30"] ** 2 / 60.0
    return lab


def test_priced_for_equals_must_move_on_the_11_nov_payload():
    p = _fixture()
    assert abs(p["volx"]["implied"] / p["rent"]["be"] - 1.0) > 0.15         # the old screen: two numbers, 20 % apart
    lab = _lab_from_payload(p)
    rows, rent = lab.decay_rows()
    c = lab.chain
    k, tau, why = lab._clock()
    assert why is None and 5.0 < k < 6.5                                    # Wednesday 15:14 to Tuesday: about 5.7
    priced_for = CK.implied_move_per_min(c["Fs"], c["atm_iv"], c["T"], tau)
    assert abs(priced_for / rent["be"] - 1.0) < 0.02
    assert rent["clock"] == CK.label(k) and rent["k"] == round(k, 3)
    # midweek the old 3.84 clock understated decay: now about k / 3.84 = 1.5 times more
    atm = [r for r in rows if r["atm"] and r["side"] == "CE"][0]
    old = next(r for r in p["decay"] if r["strike"] == atm["strike"] and r["side"] == "CE")
    assert abs(atm["trade"] / old["trade"] - k / C.TRADE_CLOCK) < 0.05
    assert rent["ratio"] < p["rent"]["ratio"]                               # 0.57 shown was too generous
    assert abs(rent["ratio"] - (rent["d10"] / rent["be"]) ** 2) < 0.01


def test_expiry_day_decay_is_a_third_of_the_old_value():
    now, exp = datetime(2026, 11, 17, 11, 0, tzinfo=config.IST), "2026-11-17"
    K = np.arange(25000.0, 25401.0, 50.0)
    lab = C.Lab(n_paths=20, options=False)
    lab.day, lab.last_t = "2026-11-17", now.timestamp()
    lab.chain = _chain(now, exp, 25190.0, K, np.full(len(K), 0.14))
    lab.vol[600] = 9.0 ** 2 / 60.0
    rows, rent = lab.decay_rows()
    assert abs(lab._clock()[0] - 1.0) < 1e-9 and rent["clock"] == "business (k=1.00)"
    c = lab.chain
    for r in rows:
        j, rr = int(np.where(c["K"] == r["strike"])[0][0]), 0 if r["side"] == "CE" else 1
        old_lot = float(c["g"]["theta"][j, rr]) * C.TRADE_CLOCK * 60.0 * config.LOT_SIZE   # what the panel showed
        assert abs(r["lot_hour"] - old_lot / C.TRADE_CLOCK) <= 0.51                 # a third of it, to the rupee
        assert abs(r["trade"] - r["theta"]) < 1e-3                         # on expiry day the calendar rate is the rate
    g = {k: float(v[lab.chain["k_atm"], 0]) for k, v in lab.chain["g"].items()}
    old_be = math.sqrt(2 * abs(g["theta"] * C.TRADE_CLOCK) / g["gamma"])
    assert abs(rent["be"] / old_be - 1.0 / math.sqrt(C.TRADE_CLOCK)) < 0.01
    assert abs(rent["ratio"] / ((9.0 / old_be) ** 2) - C.TRADE_CLOCK) < 0.05   # the old ratio was 3.84 times too low


def test_no_clock_gives_no_decay_rate_and_says_why():
    now, exp = datetime(2026, 12, 30, 11, 0, tzinfo=config.IST), "2027-01-05"
    K = np.arange(25000.0, 25401.0, 50.0)
    lab = C.Lab(n_paths=20, options=False)
    lab.day, lab.last_t = "2026-12-30", now.timestamp()
    lab.chain = _chain(now, exp, 25190.0, K, np.full(len(K), 0.14))
    lab.vol[600] = 1.0
    rows, rent = lab.decay_rows()
    assert rows and all(r["trade"] is None and r["lot_hour"] is None for r in rows)
    assert rent["be"] is None and rent["ratio"] is None and "2027" in rent["why"]
    assert any("business clock unavailable" in e for e in lab.events)
    assert lab.v_sec() == 1.0                                              # the implied part is left out, not guessed


def _history(lab, strike, n=360, noise=0.0, seed=4, iv=0.15):
    """30 minutes of 5-s quotes for both rights of one strike, priced at a constant IV on the calendar clock, ending at
    the chain's time; noise adds a quote error (points) to each mid."""
    c = lab.chain
    rng = np.random.default_rng(seed)
    F = c["Fs"] + np.r_[0.0, np.cumsum(2.5 * rng.standard_normal(n - 1))]
    F = F - F[-1] + c["Fs"]
    ts = c["t"] - 5.0 * np.arange(n)[::-1]
    for rr in (0, 1):
        dq = lab.opt_hist.setdefault((float(strike), rr), deque(maxlen=360))
        for t, f in zip(ts, F):
            T = c["T"] + (c["t"] - t) / C.SPY
            m = float(C.b76(f, strike, T, iv, rr == 0)) + noise * rng.standard_normal()
            dq.append((float(t), m, float(f), m - 0.1, m + 0.1))


def test_measured_decay_is_decay_and_agrees_across_the_pair():
    now, exp = datetime(2026, 11, 12, 13, 0, tzinfo=config.IST), "2026-11-17"
    K = np.arange(25000.0, 25401.0, 50.0)
    lab = C.Lab(n_paths=20, options=False)
    lab.day, lab.last_t = "2026-11-12", now.timestamp()
    lab.chain = _chain(now, exp, 25190.0, K, np.full(len(K), 0.15))
    _history(lab, 25200.0)
    mc, mp = lab._measured_decay(25200.0, 0), lab._measured_decay(25200.0, 1)
    th = float(lab.chain["g"]["theta"][lab.chain["k_atm"], 0])               # this tape decays on the calendar clock
    assert mc["ok"] and mp["ok"] and mc["blocks"] >= 10
    assert abs(mc["value"] / th - 1.0) < 0.25 and abs(mp["value"] / th - 1.0) < 0.25
    assert abs(mc["value"] - mp["value"]) < 0.2 * abs(th)                     # parity: one strike, one decay
    assert mc["gamma_pay"] > 0
    rows, rent = lab.decay_rows()
    r = next(x for x in rows if x["strike"] == 25200.0 and x["side"] == "CE")
    assert r["measured"] is not None and r["measured_se"] is not None
    assert lab._measured_decay(25300.0, 0) is None                            # no history: nothing measured


def test_noisy_measured_decay_is_not_said():
    now, exp = datetime(2026, 11, 12, 13, 0, tzinfo=config.IST), "2026-11-17"
    K = np.arange(25000.0, 25401.0, 50.0)
    clean = C.Lab(n_paths=20, options=False)
    clean.day, clean.last_t = "2026-11-12", now.timestamp()
    clean.chain = _chain(now, exp, 25190.0, K, np.full(len(K), 0.15))
    clean.vol[600] = clean.vol[1800] = 9.0 ** 2 / 60.0
    noisy = C.Lab(n_paths=20, options=False)
    noisy.day, noisy.last_t, noisy.chain, noisy.vol = clean.day, clean.last_t, clean.chain, dict(clean.vol)
    _history(clean, 25200.0)
    _history(noisy, 25200.0, noise=0.8)
    m = noisy._measured_decay(25200.0, 0)
    assert m is not None and not m["ok"] and m["se"] > abs(m["value"])
    p = _fixture()
    for lab, said in ((clean, True), (noisy, False)):
        rows, rent = lab.decay_rows()
        q = copy.deepcopy(p)
        q["decay"], q["rent"] = rows, rent
        k = lab._clock()[0]
        q["clock"] = dict(name="business", k=k, label=CK.label(k), why=None)
        atm = next(r for r in rows if r["atm"] and r["side"] == "CE")
        assert (atm["measured"] is not None) == said and atm["measured_raw"] is not None
        txt = " ".join(C.commentary(q)["decay"])
        assert ("Decay + IV change, measured" in txt) == said
        assert "business (k=" in txt and "trading clock" not in txt


def _sim_lab(stage_b):
    """One option simulation on a synthetic Wednesday chain, built by the Lab's own chain code."""
    now = datetime(2026, 11, 11, 12, 0, tzinfo=config.IST)
    t, exp = now.timestamp(), "2026-11-17"
    K = np.arange(24700.0, 25701.0, 50.0)
    F = 25190.0
    T = greeks.years_to_expiry(exp, now)
    mid = np.c_[C.b76(F, K, T, 0.15, np.ones(len(K), bool)), C.b76(F, K, T, 0.15, np.zeros(len(K), bool))]
    sp = np.maximum(0.05, 0.002 * mid)
    row = dict(t=t, fb=F - 0.5, fa=F + 0.5, fl=F, fv=1000.0, fbq=500.0, faq=500.0, K=K, ob=mid - sp, oa=mid + sp,
               og=np.full((len(K), 2), 0.5), expiry=exp)
    lab = C.Lab(n_paths=400, seed=3)
    lab.stage_b = stage_b
    lab.day = now.date().isoformat()
    lab.last_t = t
    lab._fut(row, t)
    lab._chain(row, t)
    lab.iv_drift = 2e-6                                     # a strong online IV trend: Stage B must ignore it
    lab.iv_beta = -1e-4
    v = 1.0
    lab.fpath = dict(t=t, F=F, mu=np.zeros(len(C.H)), sd=np.sqrt(v * np.array(C.H, float)), cf=np.full(len(C.H), 1.2))
    lab._simulate(t, F)
    return lab


def test_stage_b_paths_use_the_business_clock_and_no_online_drift():
    assert C.PRICING_STAGE_B is False                       # off until the repricing scorecard passes
    a, b = _sim_lab(False), _sim_lab(True)
    oa = {(o["side"], o["tag"]): o for o in a.last["opts"]}
    ob = {(o["side"], o["tag"]): o for o in b.last["opts"]}
    k = b._clock()[0]
    assert 5.0 < k < 6.0 and b.last["pricing"].startswith("stage B") and a.last["pricing"] == "calendar clock"
    for key in ob:
        x, y = oa[key], ob[key]
        mid = y["mid"]
        j = y["hs"].index(1800)
        lost_a, lost_b = mid - x["decay_only"][j], mid - y["decay_only"][j]
        assert abs(lost_b / lost_a - k) < 0.05 * k                            # business-clock decay, k times calendar
        assert y["decay_iv"] == y["decay_only"] and y["beta"] == 0.0          # no IV trend, sticky strike
        assert abs(y["attr"]["theta"] / x["attr"]["theta"] - k) < 1e-6
        assert y["attr"]["vega"] == 0.0
        if key[1] != "atm":                                                   # the race is run on full paths only
            assert abs(sum(y["barrier"].values()) - 1.0) < 1e-9
    assert b.iv_used["drift"] == 0.0 and b.iv_used["beta"] == "sticky strike"
    assert a.iv_used["drift"] == 2e-6
    # the calibrated futures spread: Stage B paths are wider by cf = 1.2 at the 30-minute horizon
    wa = np.mean([o["q"][-1][4] - o["q"][-1][0] for o in a.last["opts"]])
    wb = np.mean([o["q"][-1][4] - o["q"][-1][0] for o in b.last["opts"]])
    assert wb > wa


def test_held_attribution_runs_and_is_kept_in_the_saved_state():
    import time
    lab = _sim_lab(False)
    c = lab.chain
    strike = float(c["K"][c["k_atm"]])
    lab.engine = dict(t=time.time(), expiry=c["exp"], pos=dict(key="p1", strike=strike, rr="CE", expiry=c["exp"],
                                                               entry=float(c["oa"][c["k_atm"], 0])))
    lab._held_attr_step(c["t"])
    assert lab.extra_state["held_attr"]["key"] == f"p1|{strike:.0f}|0"
    c["t"] += 5.0
    c["Fs"] += 3.0
    lab._held_attr_step(c["t"])
    v = lab._hattr.view()
    assert v["steps"] == 1 and v["parts"]["direction"] > 0
    json.dumps(lab.extra_state)                                              # saved with the state as plain JSON
    lab.engine = dict(t=time.time(), pos={})                                 # the position closed
    lab._held_attr_step(c["t"] + 5.0)
    assert "held_attr" not in lab.extra_state and lab._hattr is None


# ── the scorecard and the straddle monitor on a synthetic recorded session ─────────────────────────────────────────
def _load(name):
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "forecast_lab", name)
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tape_npz(folder, day="2026-11-12", exp="2026-11-17", start=(9, 58), secs=4200, iv=0.15, seed=2):
    """A recorded-session file in the ds_v2 layout whose premiums decay on the business clock at a constant IV."""
    y, m, d = (int(x) for x in day.split("-"))
    t0 = datetime(y, m, d, start[0], start[1], tzinfo=config.IST).timestamp()
    K = np.arange(25000.0, 25401.0, 50.0)
    rng = np.random.default_rng(seed)
    F = 25190.0 + np.r_[0.0, np.cumsum(1.0 * rng.standard_normal(secs - 1))]
    now0 = datetime.fromtimestamp(t0, config.IST)
    T0 = greeks.years_to_expiry(exp, now0)
    k, _, _ = CK.k_ts(now0, exp, T0)
    t = t0 + np.arange(secs, dtype=float)
    opt = np.zeros((secs, len(K), 2, 2))
    for i in range(secs):
        T = T0 - i * k / C.SPY
        for rr in (0, 1):
            mid = C.b76(F[i], K, T, iv, np.full(len(K), rr == 0))
            sp = np.maximum(0.05, 0.001 * mid)
            opt[i, :, rr, 0], opt[i, :, rr, 1] = mid - sp, mid + sp
    path = os.path.join(folder, f"{day}.npz")
    np.savez(path, t=t, strikes=K, opt=opt, age=np.zeros((secs, len(K), 2)), fut=np.c_[F - 0.5, F + 0.5],
             fa=np.zeros((secs, 2)), expiry=np.array(exp))
    return path, k


def test_reprice_study_prefers_the_clock_the_market_used(tmp_path):
    rs = _load("reprice_study.py")
    _tape_npz(str(tmp_path))
    res = rs.run(["2026-11-12"], ds=str(tmp_path), log=lambda *_: None)
    t5 = res["pooled"]["2+|300"]
    assert t5["business"]["mae_pct"] < t5["calendar"]["mae_pct"] and t5["business"]["mae_pct"] < t5["trade384"]["mae_pct"]
    assert abs(t5["business"]["bias_pct"]) < 0.1 and t5["calendar"]["bias_pct"] > abs(t5["business"]["bias_pct"])
    assert t5["business"]["mae_pct"] < t5["naive"]["mae_pct"]
    ok, why = res["pr004"]["passed"], res["pr004"]["why"]
    assert not ok and "no expiry-day checks" in why[1]                       # no expiry day on file: not passed
    assert "1 of 1 sessions" in why[0]
    assert json.loads(json.dumps(res)) == res
    rs.write_atomic(str(tmp_path / "out" / "reprice.json"), res)
    assert json.load(open(tmp_path / "out" / "reprice.json", encoding="utf-8"))["days"] == ["2026-11-12"]
    led = str(tmp_path / "ledger.jsonl")
    assert rs.append_ledger(dict(day="2026-11-12", kind="reprice"), led) is True
    assert rs.append_ledger(dict(day="2026-11-12", kind="reprice"), led) is False     # once a day


def test_straddle_clock_measures_the_business_factor(tmp_path):
    sc = _load("straddle_clock.py")
    _, k = _tape_npz(str(tmp_path))
    res = sc.run(["2026-11-12"], ds=str(tmp_path), log=lambda *_: None)
    assert len(res["rows"]) == 1
    r = res["rows"][0]
    assert r["bucket"] == "3+" and r["minutes"] >= 60
    assert abs(r["factor"] / k - 1.0) < 0.1 and abs(r["k_mean"] - k) < 0.2         # k drifts up through the day
    assert res["expiry_ok"] is False and res["why"] == "no expiry-day parts"
    ok, why = sc.judge([dict(bucket="exp", day="2026-11-17", factor=0.8), dict(bucket="3+", day="x", factor=7.0)])
    assert ok and "0.80" in why
    assert sc.judge([dict(bucket="exp", day="2026-11-17", factor=3.84)])[0] is False
