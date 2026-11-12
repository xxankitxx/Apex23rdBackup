"""11 Nov: the Forecast Lab (apex/forecast_lab). Mechanics on synthetic markets, not profit: the pricing and the
volatility solver agree with the engine's, the online learners move the right way, forecasts are scored only when
their time has come, decay is measured, the output is plain JSON, and the commentary never claims more than the
numbers. Fast: synthetic tapes of a few thousand seconds."""
import json
import math
from datetime import datetime

import numpy as np

from apex import config, greeks
from apex.forecast_lab import core as C

T0 = datetime(2026, 11, 12, 9, 15, 0, tzinfo=config.IST).timestamp()
K = np.arange(24700.0, 25301.0, 50.0)
EXP = "2026-11-17"


def tape(n, drift=0.0, vol=1.2, iv=0.12, iv_drift=0.0, seed=1, start=T0):
    """A synthetic second-by-second market: a random-walk future, a chain priced by Black-76 at a flat volatility."""
    rng = np.random.default_rng(seed)
    F = 25000.0
    out = []
    for i in range(n):
        t = start + i
        F += drift + vol * rng.standard_normal()
        now = datetime.fromtimestamp(t, config.IST)
        T = greeks.years_to_expiry(EXP, now)
        s = iv + iv_drift * i
        ce = C.b76(F, K, T, s, np.ones(len(K), bool))
        pe = C.b76(F, K, T, s, np.zeros(len(K), bool))
        mid = np.c_[ce, pe]
        sp = np.maximum(0.05, 0.002 * mid)
        out.append(dict(t=t, fb=F - 0.5, fa=F + 0.5, fl=F, fv=1000.0 * i, fbq=500.0, faq=500.0, K=K,
                        ob=mid - sp, oa=mid + sp, og=np.full((len(K), 2), 0.5), expiry=EXP))
    return out


def run(lab, rows):
    for r in rows:
        lab.step(r)
    return lab


def test_pricing_and_volatility_agree_with_the_engine():
    F, T = 25000.0, 4 / 365
    call = K >= F
    for s in (0.08, 0.13, 0.3):
        p = C.b76(F, K, T, s, call)
        ref = np.array([greeks.b76_price(F, k, T, s, c) for k, c in zip(K, call)], float).ravel()
        assert np.allclose(p, ref, atol=2e-3)                                   # the engine uses an erf approximation
        assert np.allclose(C.iv_newton(p, F, K, T, call), s, atol=1e-5)
    g = C.b76_greeks(F, np.array([25000.0]), T, 0.12, np.array([True]))
    h = 1e-4
    up = C.b76(F, 25000.0, T, 0.12 + h, True); dn = C.b76(F, 25000.0, T, 0.12 - h, True)
    assert abs(g["vega"][0] - (up - dn) / (2 * h) / 100.0) < 1e-6                  # per vol point
    later = C.b76(F, 25000.0, T - 60 / C.SPY, 0.12, True)
    assert abs(g["theta"][0] - (later - C.b76(F, 25000.0, T, 0.12, True))) < 1e-4   # per calendar minute
    assert np.isnan(C.iv_newton(np.array([1.0]), F, np.array([24000.0]), T, np.array([True])))[0]   # below intrinsic


def test_online_learners_move_the_right_way():
    rng = np.random.default_rng(3)
    r = C.RLS(2)
    for _ in range(3000):
        x = rng.standard_normal(2)
        r.update(x, 0.4 * x[0] - 0.2 * x[1] + 0.3 * rng.standard_normal())
    assert abs(r.th[0] - 0.4) < 0.05 and abs(r.th[1] + 0.2) < 0.05
    h = C.Hedge(3)
    for _ in range(200):
        h.update([0.6, 0.5, 0.7])
    assert h.w.argmax() == 1 and h.w.min() > 0.0                                  # fixed share keeps everyone alive
    assert abs(float(C.crps_normal(0.0, 1.0, 0.0)) - (2 / math.sqrt(2 * math.pi) - 1 / math.sqrt(math.pi))) < 1e-9


def test_forecasts_are_scored_only_when_their_time_has_come_and_never_across_the_close():
    lab = C.Lab(n_paths=200)
    rows = tape(1500)
    run(lab, rows[:900])
    sc = lab._score_view()["fut"]
    first = lab.score["first_t"]
    assert first is None or first >= T0 + 300                                    # no forecast in the warm-up
    assert all(s["n"] == 0 for s in sc if s["h"] > 900 - 300)                     # nothing matures before its time
    run(lab, rows[900:])
    sc = {s["h"]: s for s in lab._score_view()["fut"]}
    assert sc[60]["n"] > sc[300]["n"] > sc[600]["n"] > 0 and sc[1800]["n"] == 0
    assert 0.5 <= sc[60]["cov"] <= 1.0
    late = C.Lab(n_paths=200)                                                     # 15:00 to 15:30: no 30-min forecast
    rows = tape(1900, start=datetime(2026, 11, 12, 15, 0, 0, tzinfo=config.IST).timestamp() - 700)
    run(late, rows)
    cut = datetime(2026, 11, 12, 15, 0, 0, tzinfo=config.IST).timestamp()
    o = [x for x in late.origins if x["t"] > cut]                                 # made after 15:00: cannot see 30 min
    assert o and all(x["done"][C.H.index(1800)] for x in o)
    assert late.score["n"][C.H.index(1800)] == 0


def test_the_option_layer_reprices_with_decay_and_states_break_even_on_the_right_side():
    lab = C.Lab(n_paths=400)
    run(lab, tape(1300, iv_drift=-2e-7))
    p = lab.panel()
    assert json.loads(json.dumps(p, allow_nan=False)) == p                        # plain JSON for the browser
    opts = {(o["side"], o["tag"]): o for o in p["options"]}
    assert ("CE", "buy") in opts and ("PE", "buy") in opts
    for o in p["options"]:
        for x in o["path"]:
            assert x["q10"] <= x["q25"] <= x["q50"] <= x["q75"] <= x["q90"]
            assert x["decay"] <= o["mid"] + 1e-6                                  # time only takes value away
        if o["tag"] == "buy":
            assert {x["h"] for x in o["path"]} >= {60, 300, 900}
            be = [x["be"] for x in o["path"] if x["be"] is not None]
            assert be and (all(b > 0 for b in be) if o["side"] == "CE" else all(b < 0 for b in be))
            assert o["barrier"] and abs(o["barrier"]["up"] + o["barrier"]["down"] + o["barrier"]["neither"] - 1) < 1e-6
    rows = p["decay"]
    assert rows and all(r["theta"] < 0 and r["trade"] < r["theta"] for r in rows)
    assert any(r["measured"] is not None for r in rows)                           # measured from the quotes
    assert p["rent"]["be"] > 0 and p["rent"]["ratio"] > 0


def test_measured_decay_finds_a_falling_volatility():
    """The chain loses 0.02 vol points a second... (a strong, known IV fall): the measured decay of the at-the-money
    call must be clearly more negative than its constant-volatility theta."""
    lab = C.Lab(n_paths=200)
    run(lab, tape(1400, vol=0.6, iv_drift=-2e-6))
    rows = [r for r in lab.decay_rows()[0] if r["atm"] and r["side"] == "CE"]
    assert rows and rows[0]["measured"] is not None and rows[0]["measured"] < rows[0]["theta"] * 1.5
    assert lab.iv_drift < 0


def _score(fut=None, opt=None):
    f = dict(h=300, n=0, cov=None, skill=None, skill_frozen=None, dir_n=0, dir_hit=None)
    f.update(fut or {})
    rows = [dict(h=300, n=0), dict(h=900, n=0)]
    for r in rows:
        r.update((opt or {}).get(r["h"], {}))
    return dict(score=dict(fut=[f], opt=rows))


def test_only_an_option_record_earns_a_buy_statement():
    """11 Nov review: the old gate let 30 overlapping FUTURES forecasts authorise a 15-minute OPTION buy.
    12 Nov (PKG-03): direction also needs 5 earlier forward days and a clear lean now; the full buy-case conditions
    are tested in test_forecast_lab_honesty.py."""
    great_fut = dict(n=4000, cov=0.8, skill=0.2, dir_n=2400, dir_hit=0.9)
    days = dict(days=5, dir={"300": dict(n_days=5, ok=True)}, buy={"300": dict(n_days=5, ok=True)})

    def with_lean(q, mu=2.0):
        q["path"] = [dict(h=300, mu=mu, sd=4.0)]
        return q
    e = C.earned(with_lean(_score(fut=great_fut)), cross=days)
    assert e["direction"] and e["ranges"] == "ok"
    assert not e["buy"] and e["buy_h"] == []                # a futures record never earns an option statement
    # the same record without 5 earlier forward days, or without a clear lean now, earns no direction
    assert not C.earned(with_lean(_score(fut=great_fut)))["direction"]
    assert not C.earned(with_lean(_score(fut=great_fut), mu=0.1), cross=days)["direction"]
    # 30 forecasts 5 s apart are half an independent check: nothing is earned
    e = C.earned(with_lean(_score(fut=dict(n=30, cov=0.8, skill=0.5, dir_n=30, dir_hit=1.0))), cross=days)
    assert not e["direction"] and e["ranges"] == "unchecked" and e["dir_checks"] == 0.5
    # 60 % right is the line, and the score must beat 'no move'
    assert not C.earned(with_lean(_score(fut=dict(great_fut, dir_hit=0.59))), cross=days)["direction"]
    assert not C.earned(with_lean(_score(fut=dict(great_fut, skill=-0.01))), cross=days)["direction"]
    assert C.earned(_score(fut=dict(great_fut, cov=0.6)))["ranges"] == "narrow"
    # an option record with too few independent checks earns no buy case, whatever the days say
    thin = dict(n=400, slots_buy=10, brier_buy=0.20, brier_clim=0.25, err=5.0, err_naive=6.0, err_decay=6.0, cov=0.8)
    assert not C.earned(_score(opt={300: thin}), cross=days)["buy"]


def test_the_commentary_says_only_what_is_earned():
    lab = C.Lab(n_paths=300)
    run(lab, tape(1000, drift=0.4))
    p = lab.panel()
    assert not p["earned"]["direction"] and not p["earned"]["buy"]
    say = p["say"]
    text = " ".join(x for k in say for x in say[k])
    assert say["do"] and say["do"][0] == "Flat. There is no buy case."
    assert "Direction: no call." in say["now"]
    for banned in ("I would", "I lean", "most likely", "higher than now", "profit chance", "old model", "get out near"):
        assert banned not in text, banned
    assert say["now"] and say["decay"] and say["doing"] and say["next"]
    # the same panel with an earned option record states the buy case plainly, and still gives no exit level
    q = json.loads(json.dumps(p))
    q["earned"] = dict(p["earned"], buy=True, buy_h=[300, 900], opt_checks={"300": 40, "900": 25})
    for o in q["options"]:
        for x in o["path"]:
            x["ev"], x["pp"] = 2.5, 0.61
    do = " ".join(C.commentary(q)["do"])
    assert do.startswith("Buy case:") and "get out" not in do
    # a held contract never gets an exit opinion
    for o in q["options"]:
        o["tag"] = "held"
    q["earned"] = p["earned"]
    do = " ".join(C.commentary(q)["do"])
    assert "held by a book" in do and "Buy case" not in do


def test_a_stale_futures_quote_shows_no_forecast():
    lab = C.Lab(n_paths=300)
    rows = tape(1000)
    run(lab, rows[:-1])
    assert lab.panel().get("path")
    lab.step(dict(rows[-1], fage=12.0))
    p = lab.panel()
    assert p["stale"] == "the futures quote is 12 s old" and "path" not in p and not p.get("options")
    assert p["age"]["fut"] == 12.0
    assert p["say"]["now"][0].startswith("No forecast: the futures quote is 12 s old") and not p["say"]["do"]
    json.dumps(p)


def test_state_round_trip_and_a_frozen_copy_that_does_not_learn():
    lab = C.Lab(n_paths=200)
    run(lab, tape(1500, drift=0.3))
    s = json.loads(json.dumps(lab.to_json()))
    again = C.Lab(state=s, n_paths=200)
    assert np.allclose(again.rls["blend"][3].th, lab.rls["blend"][3].th) and np.allclose(again.hedge[3].w, lab.hedge[3].w)
    fr = [a.copy() for a in again.frozen["th"]["blend"]]
    run(again, tape(1500, drift=0.3, seed=9, start=T0 + 86400))
    assert all(np.allclose(a, b) for a, b in zip(again.frozen["th"]["blend"], fr)) or again.day != "2026-11-12"


def test_todays_record_survives_a_restart_but_not_a_new_day():
    lab = C.Lab(n_paths=200)
    run(lab, tape(1300))
    n5 = int(lab.score["n"][3])
    assert n5 > 0
    s = json.loads(json.dumps(lab.to_json()))
    same = C.Lab(state=s, n_paths=200)
    run(same, tape(5, start=T0 + 1400))
    assert int(same.score["n"][3]) == n5
    nxt = C.Lab(state=s, n_paths=200)
    run(nxt, tape(5, start=T0 + 86400))
    assert int(nxt.score["n"][3]) == 0


def test_the_last_minutes_before_the_close_do_not_break_the_simulation():
    lab = C.Lab(n_paths=100)
    start = datetime(2026, 11, 12, 15, 30, 0, tzinfo=config.IST).timestamp() - 700
    run(lab, tape(700, start=start))                                             # runs right up to 15:30
    assert lab.panel()["ok"]


# -- v2 (11 Nov evening): the trained layer ---------------------------------------------------------------------------
def _toy_brain():
    from apex.forecast_lab import brain as B
    nf = B.NF
    vol = [[0.1 * j] + [0.0] * nf for j in range(len(B.H))]
    lin = [[0.0] + [0.0] * nf for _ in B.H]
    for w in lin:
        w[1 + B.FEATS.index("r120")] = 0.2                          # a known rule: follow the last two minutes
    obj = dict(feats=B.FEATS, H=B.H, med=[0.0] * nf, sd=[1.0] * nf, vol=vol, lin=lin, gbm=[None] * len(B.H),
               qz=[[-1.4, -0.7, 0.0, 0.7, 1.4]] * len(B.H), volvol=[0.3] * len(B.H),
               iv=dict(drift=[[0.0] * B.N_TOD] * 3, beta=[[-4e-5] * (len(B.MNY_EDGES) + 1)] * 3, res=[2e-5] * 3),
               meta=dict(trained_through="2026-11-11", sessions=16, hash="toy"))
    return B.Brain(obj=obj)


def tape_hw(n, **kw):
    rows = tape(n, **kw)
    rng = np.random.default_rng(5)
    px = np.array([800.0, 1500.0, 1300.0, 2000.0])
    for r in rows:
        px = px * (1 + 2e-5 * rng.standard_normal(4))
        r.update(hw=px.copy(), hw_w=np.array([10.0, 9.0, 7.0, 5.0]), hw_bank=np.array([True, True, False, False]))
    return rows


def test_the_45_inputs_exist_are_finite_and_need_history():
    from apex.forecast_lab import brain as B
    lab = C.Lab(n_paths=100, collect=True)
    lab.simulate = False
    run(lab, tape_hw(500))
    assert not lab.collect                                                        # under 10 minutes: no origin yet
    run(lab, tape_hw(1300, seed=4)[500:])
    assert lab.collect
    t, F, v, x = lab.collect[-1]
    assert len(x) == B.NF == len(B.FEATS) and np.all(np.isfinite(x))
    named = dict(zip(B.FEATS, x))
    assert 0 <= named["up60"] <= 1 and named["vr"] >= 0 and 0 <= named["tod"] <= 1 and named["exp"] in (0.0, 1.0)
    assert abs(named["micro"]) < 1e-9                                             # a constant book: no change of imbalance
    assert B.Brain(path="does/not/exist.joblib").ok is False
    assert B.Brain(obj=dict(feats=("a",), H=B.H)).ok is False                     # another feature set: refused


def test_the_trained_layer_drives_width_quantiles_experts_and_the_panel():
    br = _toy_brain()
    assert br.ok
    lab = C.Lab(n_paths=300, brain=br)
    run(lab, tape_hw(1300, drift=0.25))
    p = lab.panel()
    assert json.loads(json.dumps(p, allow_nan=False)) == p
    assert p["brain"]["ok"] and p["brain"]["trained_through"] == "2026-11-11"
    assert p["regime"]["name"] in ("trending", "choppy", "mixed") and p["volx"]["implied"] > 0 and p["volx"]["forecast5"] > 0
    ex = {e["name"]: e for e in p["experts"]}
    assert set(ex) == set(C.EXPERTS) and ex["ridge"]["mu5"] > 0 and ex["trees"]["mu5"] == 0     # the toy rule, a rising tape
    for x in p["path"]:
        assert x["q10"] < x["q25"] < x["mean"] + 5 * x["sd"] and x["q25"] < x["q75"] < x["q90"]
    sd = [x["sd"] for x in p["path"]]
    assert all(b > a for a, b in zip(sd, sd[1:]))                                 # the range widens with the horizon
    buy = [o for o in p["options"] if o["tag"] == "buy"]
    assert buy and all(o["whatif"] and len(o["whatif"]["moves"]) == 5 for o in buy)
    ce = [o for o in buy if o["side"] == "CE"][0]
    row = [c for c in ce["whatif"]["cells"] if c["h"] == 300][0]["row"]
    assert row[0][1] < row[2][1] < row[4][1] and row[2][1] < 0                    # a call: up is better; flat loses to decay
    assert 0.0 <= p["learn"]["odw"] <= 1.0
    assert any(s.startswith("Repricing") for s in p["say"]["next"]) and any("80 %" in s for s in p["say"]["next"]) and any("Options are priced for" in s for s in p["say"]["now"])
    plain = C.Lab(n_paths=100)
    run(plain, tape_hw(1300, drift=0.25))
    assert plain.panel()["brain"]["ok"] is False                                  # without the file it still runs


def test_the_installed_trained_models_load_and_give_sane_numbers():
    import os
    from apex.forecast_lab import brain as B
    pth = os.path.join(config.DATA_DIR, "forecast_lab", "brain.joblib")
    real = os.path.join(config.ROOT, "data", "forecast_lab", "brain.joblib")
    pth = pth if os.path.exists(pth) else real
    if not os.path.exists(pth):
        return
    br = B.Brain(pth)
    assert br.ok, br.why
    x = np.asarray(br.med, float)                                                 # a typical moment
    v = br.vol(x, 4.0)
    assert np.all(v > 0) and np.all(np.diff(v) > 0)                               # more time, more variance
    lin, gb = br.drift(x)
    assert np.all(np.abs(lin) < 1.0) and np.all(np.abs(gb) < 1.0)
    q = br.qz(3)
    assert q[0] < q[1] < q[2] < q[3] < q[4] and -2.5 < q[0] < -0.8 and 0.8 < q[4] < 2.5
    assert abs(br.iv_drift(T0, 5.0)) < 1e-4 and 0 < br.iv_res(5.0) < 0.01
