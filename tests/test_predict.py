"""10 Nov (docs/40, docs/41): the prediction service. These tests pin definitions: causality of the features, the
fixed-contract targets with their competing events and gaps, probability consistency, the immutable ledger and the
matured-only rule. Nothing here says a forecast is right."""
import json

import numpy as np
import pytest

from apex.predict import features as F, ledger as L, models as Mo, targets as T

T0 = 1_794_196_800.0
K = np.array([24900.0, 24950.0, 25000.0, 25050.0, 25100.0])
W = np.array([30.0, 25.0, 25.0, 20.0])


def feed(fs, n, mid0=25000.0, drift=0.0, t0=T0, skip=(), opt=None, cash_drift=0.0):
    """n seconds of a tape. opt(i) -> premium of the 25000 call (default: 100 + half the futures move)."""
    out = []
    for i in range(n):
        if i in skip:
            continue
        m = mid0 + drift * i
        cash = np.array([1000.0, 2000.0, 1500.0, 500.0]) * (1 + cash_drift * i / 25000.0)
        ce = np.maximum(m - K, 0) + 100.0 if opt is None else np.full(5, opt(i))
        pe = np.maximum(K - m, 0) + 100.0
        bid = np.c_[ce - 0.1, pe - 0.1]
        ask = np.c_[ce + 0.1, pe + 0.1]
        fs.update(t0 + i, m - 0.5, m + 0.5, 0.2, cash, np.full(4, 0.3), cash - 0.05, cash + 0.05, np.full(4, 0.3), W, K,
                  bid, ask, np.full((5, 2), 0.3), 2, False, 3600 + i)
        out.append(fs.contract(2, 0))
    return out


def test_features_wait_for_the_warm_up_and_restart_after_a_hole():
    fs = F.Features()
    xs = feed(fs, F.WARM_S + 5)
    assert all(x is None for x in xs[:F.WARM_S - 1]) and xs[-1] is not None and len(xs[-1]) == len(F.NAMES)
    fs = F.Features()
    xs = feed(fs, F.WARM_S + 50, skip={F.WARM_S + 10})                   # one quiet second: no restart
    assert xs[F.WARM_S + 5] is not None and xs[-1] is not None and fs.gaps == 1
    fs = F.Features()
    xs = feed(fs, F.WARM_S + 50, skip=set(range(F.WARM_S + 10, F.WARM_S + 20)))   # ten missing seconds: restart
    assert xs[F.WARM_S + 5] is not None and xs[-1] is None
    fs = F.Features()
    feed(fs, F.WARM_S + 100, drift=0.2, skip={F.WARM_S + 69})            # the 30-s window's far end is the hole
    assert np.isnan(fs.contract(2, 0)[F.NAMES.index("mom30")]) and np.isfinite(fs.contract(2, 0)[F.NAMES.index("mom60")])


def test_features_are_signed_by_the_trade_and_use_only_the_past():
    fs = F.Features()
    feed(fs, F.WARM_S + 100, drift=0.2)
    ce, pe = fs.contract(2, 0), fs.contract(2, 1)
    i = F.NAMES.index("mom30")
    assert ce[i] == pytest.approx(6.0) and pe[i] == pytest.approx(-6.0)
    assert ce[F.NAMES.index("tod")] == pe[F.NAMES.index("tod")]              # unsigned features are shared
    # the same first 350 seconds give the same vector whatever comes after them
    a, b = F.Features(), F.Features()
    xa = feed(a, 350, drift=0.1)
    xb = feed(b, 600, drift=0.1)
    assert np.allclose(xa[349], xb[349], equal_nan=True)


def test_a_stale_future_or_a_one_sided_option_quote_gives_no_features():
    fs = F.Features()
    feed(fs, F.WARM_S + 5)
    m = 25000.0
    bid = np.full((5, 2), 99.9)
    ask = np.full((5, 2), 100.1)
    bid[2, 0] = 0.0
    fs.update(T0 + F.WARM_S + 5, m - 0.5, m + 0.5, 0.2, [1000, 2000, 1500, 500], np.full(4, 0.3), [1, 1, 1, 1], [2, 2, 2, 2],
              np.full(4, 0.3), W, K, bid, ask, np.full((5, 2), 0.3), 2, False, 4000)
    assert fs.contract(2, 0) is None and fs.contract(2, 1) is not None
    fs.update(T0 + F.WARM_S + 6, m - 0.5, m + 0.5, 9.0, [1000, 2000, 1500, 500], np.full(4, 0.3), [1, 1, 1, 1], [2, 2, 2, 2],
              np.full(4, 0.3), W, K, bid, ask, np.full((5, 2), 0.3), 2, False, 4001)
    assert fs.market() is None and fs.contract(2, 1) is None


def _path(bids, ask0=100.0, ok=None, t=None):
    n = len(bids) + 2
    t = np.arange(n, dtype=float) if t is None else np.asarray(t, float)
    bid = np.r_[99.8, 99.8, bids].astype(float)
    ask = np.r_[100.0, ask0, np.asarray(bids) + 0.2].astype(float)
    okv = np.ones(n, bool) if ok is None else np.r_[True, True, ok]
    return t, bid, ask, okv, np.full(n, 0.3)


def test_target_first_adverse_first_and_neither():
    up = _path(np.r_[np.full(20, 101.0), 105.5, np.full(300, 90.0)])
    r = T.label(*up, 0)
    assert r["st"] == "ok" and r["entry"] == 100.0 and r["t_hit"] == 21.0
    assert r["first"] == {30: "T", 60: "T", 180: "T", 300: "T"}                # the later fall does not change the label
    dn = _path(np.r_[np.full(40, 99.0), 94.9, np.full(300, 120.0)])
    r = T.label(*dn, 0)
    assert r["first"] == {30: "N", 60: "A", 180: "A", 300: "A"} and r["ret"][30] == pytest.approx(-0.01)
    flat = _path(np.full(330, 101.0))
    r = T.label(*flat, 0)
    assert set(r["first"].values()) == {"N"} and r["t_hit"] is None and r["ret"][300] == pytest.approx(0.01)


def test_a_gap_is_neither_a_stop_nor_a_win_and_a_lapse_is_a_lapse():
    ok = np.ones(330, bool)
    ok[50:80] = False                                    # 30 s with no usable bid, then a "win"
    g = _path(np.r_[np.full(80, 100.5), np.full(250, 110.0)], ok=ok)
    r = T.label(*g, 0)
    assert r["first"][30] == "N" and r["first"][60] == "U" and r["first"][300] == "U" and r["t_hit"] is None
    assert r["ret"][300] is None
    short = _path(np.full(100, 100.5))                   # the data ends 100 s after the fill
    r = T.label(*short, 0)
    assert r["first"][60] == "N" and r["first"][180] == "U"
    t, bid, ask, okv, age = _path(np.full(50, 101.0))
    okv[1] = False
    assert T.label(t, bid, ask, okv, age, 0) == {"st": "L"}
    age[1] = 5.0
    okv[1] = True
    assert T.label(t, bid, ask, okv, age, 0) == {"st": "L"}    # the quote at the fill second was received before the request


def test_policy_exit_matches_the_label():
    t, bid, ask, ok, _ = _path(np.r_[np.full(20, 101.0), 105.5, np.full(300, 90.0)])
    assert T.policy_exit(t, bid, ok, 1, 100.0) == (pytest.approx(0.055), 21.0, "T")
    t, bid, ask, ok, _ = _path(np.full(330, 101.0))
    r = T.policy_exit(t, bid, ok, 1, 100.0)
    assert r[2] == "H" and r[1] == 300.0
    ok[40:80] = False
    assert T.policy_exit(t, bid, ok, 1, 100.0) is None


def _artefact(rng):
    X = rng.normal(size=(4000, len(F.NAMES)))
    art = dict(version=1, feature_schema=F.SCHEMA, target_spec=T.SPEC, training_cutoff="2026-11-09", models={})
    for h in T.HORIZONS:
        art["models"][f"T{h}"] = Mo.fit_logit(X, (X[:, 2] + rng.normal(size=4000) > 1.0 - h / 300.0), F.NAMES)
        art["models"][f"A{h}"] = Mo.fit_logit(X, (-X[:, 2] + rng.normal(size=4000) > 1.0 - h / 300.0), F.NAMES)
    art["hash"] = Mo.model_hash(art)
    return art, X


def test_the_model_learns_a_planted_signal_and_the_forecast_is_a_distribution():
    rng = np.random.default_rng(3)
    art, X = _artefact(rng)
    y = X[:, 2] + rng.normal(size=4000) > 0.0
    assert Mo.auc(Mo.predict(art["models"]["T300"], X), y) > 0.7
    fc = L.Forecaster(art)
    assert fc.ok
    for x in X[:200]:
        f = fc.forecast(x)
        for h in T.HORIZONS:
            assert f["pT"][h] >= 0 and f["pA"][h] >= 0 and f["pT"][h] + f["pA"][h] + f["pN"][h] == pytest.approx(1.0)
        assert all(f["pT"][a] <= f["pT"][b] + 1e-12 for a, b in zip(T.HORIZONS, T.HORIZONS[1:]))
    for x in X[:50]:                                     # the one-pass forecast equals the per-model prediction
        f = fc.forecast(x)
        assert f["pT"][30] == pytest.approx(float(Mo.predict(art["models"]["T30"], x)[0]), abs=1e-12)
        assert f["pA"][30] == pytest.approx(float(Mo.predict(art["models"]["A30"], x)[0]), abs=1e-12)
    bad = dict(art, feature_schema="other")
    f2 = L.Forecaster(bad)
    assert not f2.ok and f2.forecast(X[0]) is None and "schema" in f2.why
    assert not L.Forecaster(None).ok


def test_the_ledger_is_append_only_and_survives_a_restart(tmp_path):
    led = L.Ledger(str(tmp_path), "2026-11-10")
    x = np.arange(len(F.NAMES), dtype=float)
    a = led.issue(T0, "NIFTY|OPT|2026-11-17|25000|CE", x, dict(edge=0.1), "abstain", "edge below the line", "P02", "abc", "2026-11-09")
    b = led.issue(T0 + 1, "NIFTY|OPT|2026-11-17|25000|CE", x, None, "abstain", "no model", "P02", None, None)
    assert a != b and led.pending() == 2
    led.link(a, "outcome", T0 + 311, first={"300": "N"})
    with pytest.raises(KeyError):
        led.link("nope", "outcome", T0)
    led.flush()
    assert led.pending() == 0 and led.written == 3
    rows = [json.loads(s) for s in open(led.fpath, encoding="utf-8")]
    assert [r["sequence"] for r in rows] == [1, 2] and rows[0]["forecast_id"] == a and rows[0]["feature_schema"] == F.SCHEMA
    assert rows[1]["forecast"] is None and rows[1]["reason"] == "no model"       # an abstention is a record too
    before = open(led.fpath, encoding="utf-8").read()
    led2 = L.Ledger(str(tmp_path), "2026-11-10")                                 # restart
    c = led2.issue(T0 + 2, "NIFTY|OPT|2026-11-17|25000|PE", x, dict(edge=0.2), "enter", "edge", "P02", "abc", "2026-11-09")
    led2.link(a, "exit", T0 + 400, px=1.0)                                       # an old forecast can still be linked
    led2.flush()
    after = open(led.fpath, encoding="utf-8").read()
    assert after.startswith(before) and json.loads(after.splitlines()[-1])["sequence"] == 3 and c not in (a, b)


def test_only_matured_outcomes_come_out_and_each_comes_out_once():
    mt = L.Maturity()
    mt.add("f1", "CE", 0.0, p=0.4)
    mt.add("f2", "PE", 0.0, p=0.3)
    mt.add("f3", "XX", 0.0, p=0.2)                        # never filled
    mt.fill("f1", 1.0, 100.0)
    mt.fill("f2", 1.0, 100.0)
    px = {"CE": 101.0, "PE": 99.0}
    out = []
    for s in range(2, 25):
        out += mt.step(float(s), px.get)
    assert [(o["forecast_id"], o["status"]) for o in out] == [("f3", "L")]   # 11 Nov (docs/42 G): not filled at the next
    out = []                                              # second = lapsed, as offline; a favourable path is not yet an outcome
    px["CE"] = 105.5
    out = mt.step(25.0, px.get)
    assert [o["forecast_id"] for o in out] == ["f1"] and out[0]["first"] == {30: "T", 60: "T", 180: "T", 300: "T"}
    assert out[0]["t_hit"] == 24.0 and out[0]["p"] == 0.4
    rest = []
    for s in range(26, 320):
        rest += mt.step(float(s), px.get)
    ids = [o["forecast_id"] for o in rest]
    assert ids.count("f2") == 1 and "f3" not in ids and "f1" not in ids
    f2 = [o for o in rest if o["forecast_id"] == "f2"][0]
    assert f2["matured_t"] >= 1.0 + 300 + T.MAX_GAP_S and set(f2["first"].values()) == {"N"}
    assert not mt.open


def test_a_blind_stretch_makes_the_outcome_unobservable_and_the_queue_is_bounded():
    mt = L.Maturity(cap=3)
    mt.add("g", "CE", 0.0)
    mt.fill("g", 1.0, 100.0)
    px = {"CE": 100.5}
    out = []
    for s in range(2, 330):
        if s == 40:
            px["CE"] = None
        if s == 80:
            px["CE"] = 110.0                              # a "win" seen only after 40 blind seconds
        out += mt.step(float(s), px.get)
    assert len(out) == 1 and out[0]["first"][30] == "N" and out[0]["first"][60] == "U" and out[0]["t_hit"] is None
    for k in range(5):
        mt.add(f"h{k}", "CE", float(k))
    assert len(mt.open) == 3 and mt.dropped == 2


def test_the_calibrator_shrinks_to_the_forecast_and_learns_from_what_it_is_given():
    c = Mo.Calibrator(prior=50.0)
    assert c(0.3)[0] == pytest.approx(0.3)                # nothing seen: the forecast comes back unchanged
    c.update(np.full(1000, 0.32), np.r_[np.ones(100), np.zeros(900)])
    assert 0.10 < c(0.31)[0] < 0.13 and c(0.8)[0] == pytest.approx(0.8)
    c2 = Mo.Calibrator.from_json(json.loads(json.dumps(c.to_json())))
    assert c2(0.31)[0] == c(0.31)[0]
    assert Mo.brier([0.5, 0.5], [1, 0]) == 0.25 and Mo.auc([0.1, 0.2, 0.3, 0.4], [0, 0, 1, 1]) == 1.0
    assert Mo.auc([0.5, 0.5, 0.5, 0.5], [0, 1, 0, 1]) == 0.5
