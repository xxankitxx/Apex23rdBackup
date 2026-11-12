"""11 Nov (docs/42, the audit's first block): the forecast books buy the contract that was scored, the entry line and
the engine use one scoring function, held contracts are covered with a reason when they are not, the twins count
how often they were asked and acted, and a quote age of zero is a fresh quote. Behaviour only, not profit."""
import json
import os
from datetime import datetime

import numpy as np

from apex import config
from apex.engine import paper, pred
from apex.predict import features as F, ledger as L, models as Mo, targets as T
from test_pred import K, Tape, T0, W, artefact


def _feed(tp, n, drift=0.0, extra=None):
    for _ in range(n):
        tp.t += 1.0
        tp.mid += drift
        cash = np.array([1000.0, 2000.0, 1500.0, 500.0])
        ce = np.maximum(tp.mid - K, 0) + 100.0
        pe = np.maximum(K - tp.mid, 0) + 100.0
        tp.p.update(tp.t, tp.mid - 0.5, tp.mid + 0.5, 0.2, cash, np.full(4, 0.3), cash - 0.05, cash + 0.05, np.full(4, 0.3),
                    W, K, np.c_[ce - 0.1, pe - 0.1], np.c_[ce + 0.1, pe + 0.1], np.full((5, 2), 0.3), 2, False,
                    3600 + (tp.t - T0), extra=extra)
        for nm, s in tp.p.sig.items():
            if s["t"] == tp.t:
                tp.seen.append((nm, s))


# -- finding B: one scoring function ---------------------------------------------------------------------------------
def test_the_vectorised_score_is_the_engine_score_row_for_row():
    rng = np.random.default_rng(4)
    art = artefact(w_mom=0.9)
    for k in art["models"]:                                   # make the horizons disagree, so the projection has work
        art["models"][k]["w"][0] = float(rng.normal(-0.5, 1.2))
    fc = L.Forecaster(artefact=art)
    X = rng.normal(0, 2.0, (400, len(F.NAMES)))
    pT, pA = fc.score(X)
    assert (np.diff(pT, axis=1) >= -1e-12).all() and (np.diff(pA, axis=1) >= -1e-12).all() and (pT + pA <= 1 + 1e-12).all()
    e = fc.edges(X)
    raw = Mo.predict(art["models"]["T300"], X) - Mo.predict(art["models"]["A300"], X)
    assert np.abs(e - raw).max() > 0.01                       # the projection really changes the score here
    for i in range(0, 400, 7):
        f = fc.forecast(X[i])
        assert abs(f["edge"] - e[i]) < 1e-12
        assert all(abs(f["pT"][h] - pT[i, j]) < 1e-12 and abs(f["pA"][h] - pA[i, j]) < 1e-12 for j, h in enumerate(T.HORIZONS))
    P = fc.raw(X)
    assert np.allclose(P[:, 3], Mo.predict(art["models"]["T300"], X), atol=1e-12)


def test_the_installed_artefact_takes_its_lines_from_the_deployed_score():
    assert os.path.basename(config.PREDICT_MODEL) == "model_v2.json"
    v2 = json.load(open(config.PREDICT_MODEL))
    v1 = json.load(open(os.path.join(os.path.dirname(config.PREDICT_MODEL), "model_v1.json")))
    assert v2["score_pipeline"] == "project_v1" and v2["parent"] == v1["hash"] and v2["hash"] == Mo.model_hash(v2)
    assert v2["models"] == v1["models"]                       # the same fitted weights: only the lines moved
    assert v2["edge_quantiles"] != v1["edge_quantiles"]
    npz = os.path.join(config.ROOT, "data", "research", "predict", "origins_v1.npz")
    if os.path.exists(npz):                                   # the research file is not in every checkout
        z = np.load(npz)
        mc = {str(n): i for i, n in enumerate(z["mcols"])}
        obs = (z["M"][:, mc["st"]] == 1) & (z["M"][:, mc["first300"]] != 3)
        # model_v2 was fitted on label version 1; the engine now refuses it (docs/46 finding 3), so the lines are
        # reproduced with a forecaster told to accept that older specification
        e = L.Forecaster(artefact=dict(v2, target_spec=T.SPEC)).edges(z["X"][obs].astype(float))
        assert not L.Forecaster(artefact=v2).ok                      # the old labels are not loaded any more
        for q, v in v2["edge_quantiles"].items():
            assert abs(float(np.quantile(e, float(q))) - v) < 1e-9, q


# -- finding A: the contract scored is the contract bought ----------------------------------------------------------
def test_signals_choose_only_among_the_contracts_the_engine_would_buy():
    tp = Tape()
    exe = [(24950.0, 0, "exe"), (25050.0, 1, "exe")]          # one strike in the money on each side
    _feed(tp, F.WARM_S + 5, extra=exe)
    _feed(tp, 40, drift=0.3, extra=exe)
    s = dict(tp.seen)["p02_clock"]
    assert (s["strike"], s["rr"]) == (24950.0, 0)             # the executable call, not the at-the-money call
    assert set(tp.p.exe) == {(24950.0, 0), (25050.0, 1)}
    tp = Tape()
    _feed(tp, F.WARM_S + 5, extra=[(30000.0, 0, "exe")])      # a strike the forecaster cannot see
    _feed(tp, 40, drift=0.3, extra=[(30000.0, 0, "exe")])
    assert not tp.seen and "could buy" in tp.p.why["p02_clock"] and "grid" in tp.p.why["p02_clock"]
    assert tp.p.edge_of(30000.0, 0) is None and "grid" in tp.p.why_none(30000.0, 0)
    tp = Tape()                                               # no engine behind it: the four near contracts, as before
    tp.step(F.WARM_S + 5)
    tp.step(40, drift=0.3)
    assert tp.seen and tp.p.exe is None


def _ctx(now=None, **opts):
    now = now or datetime(2026, 11, 12, 11, 0, tzinfo=config.IST)
    w0 = "2026-11-17"
    by = {}
    for (k, rr), o in opts.get("o", {}).items():
        key = f"NIFTY|OPT|{w0}|{int(k)}|{rr}"
        by[key] = dict(dict(key=key, strike=float(k), rr=rr, week=0, ltp=120.0, bid=119.9, ask=120.1, age=0.4, delta=0.6), **o)
    return {"now_dt": now, "w0": w0, "by_key": by, "options": list(by.values())}


def test_a_forecast_book_buys_the_scored_contract_or_nothing():
    class B:
        p = dict(config.VARIANTS["p02_clock"])
        ctl = {}
    ctx = _ctx(o={(24950, "CE"): {}, (24900, "CE"): {"delta": 0.7}, (25000, "CE"): {"delta": 0.5}})
    B.ctl = {"want": (24950.0, "CE", "f1")}
    o, msg = paper.choose_contract(ctx, 1, B)
    assert o["key"].endswith("|24950|CE") and msg == ""
    o2, _ = paper.choose_contract(ctx, 1, B)                  # the missed-signal twin asks again in the same step
    assert o2 is o
    for want, o_over, word in (((25000.0, "CE", "f"), {}, "ATM/ITM"),               # delta 0.50: below the owner's floor
                               ((24950.0, "CE", "f"), {"age": 20.0}, "stale"),
                               ((24950.0, "CE", "f"), {"ltp": 5.0}, "premium"),
                               ((24950.0, "CE", "f"), {"delta": None}, "delta"),
                               ((24850.0, "CE", "f"), {}, "no quote")):
        c = _ctx(o={(24950, "CE"): o_over, (24900, "CE"): {"delta": 0.7}, (25000, "CE"): {"delta": 0.5}})
        B.ctl = {"want": want}
        got, msg = paper.choose_contract(c, 1, B)
        assert got is None and word in msg and "no other contract is substituted" in msg, (want, msg)
    late = _ctx(now=datetime(2026, 11, 17, 15, 20, tzinfo=config.IST), o={(24950, "CE"): {}})
    B.ctl = {"want": (24950.0, "CE", "f")}
    assert "cut-off" in paper.choose_contract(late, 1, B)[1]


def test_evaluate_gen_carries_the_contract_of_the_signal():
    from apex.engine import gen2
    tp = Tape()
    exe = [(24950.0, 0, "exe"), (25050.0, 1, "exe")]
    _feed(tp, F.WARM_S + 5, extra=exe)
    _feed(tp, 40, drift=0.3, extra=exe)
    s = dict(tp.seen)["p02_clock"]

    class B:
        p = config.VARIANTS["p02_clock"]
        fired_episodes = set()
        ctl = {}
    ctx = {"pred": tp.p, "gen2": gen2.Gen2(), "gen3": None, "now_s": s["t"] + 0.5, "w0": "2026-11-17"}
    assert paper.evaluate_gen(B, ctx)[0] and B.ctl["want"][:2] == (24950.0, "CE")


# -- finding C: coverage of held contracts, and a reason when there is none -----------------------------------------
def test_held_contracts_are_scored_and_a_missing_forecast_says_why():
    tp = Tape()
    held = [(24900.0, 0, "held"), (24950.0, 0, "exe"), (25050.0, 1, "exe")]
    _feed(tp, F.WARM_S + 5, extra=held)
    assert tp.p.edge_of(24900.0, 0) is not None and tp.p.why_none(24900.0, 0) is None      # two strikes in: outside the old four
    assert tp.p.view()["scored"] >= 5 and tp.p.view()["in_sample"] is False
    assert tp.p.why_none(25100.0, 0) == "not among the contracts scored this second"
    cold = Tape()
    _feed(cold, 5, extra=held)
    assert "warming" in cold.p.why_none(24900.0, 0)


def test_the_model_says_when_it_has_seen_the_day(tmp_path):
    a = artefact()
    assert pred.Pred(artefact=a, ledger_dir=str(tmp_path), day="2026-11-09").in_sample          # the cut-off day itself
    assert not pred.Pred(artefact=a, ledger_dir=str(tmp_path), day="2026-11-10").in_sample


# -- the twins count what they did ----------------------------------------------------------------------------------
def test_the_twins_count_asked_answered_and_acted():
    tp = Tape()
    tp.step(F.WARM_S + 5)
    tp.step(40, drift=0.3)
    ctx = {"pred": tp.p, "w0": "2026-11-17"}
    call = {"strike": 25000.0, "rr": "CE", "expiry": "2026-11-17", "entry": 100.0}
    put = dict(call, rr="PE")
    assert pred.held_keep(ctx, call, 104.0) and not pred.held_keep(ctx, call, 99.0) and not pred.held_keep(ctx, put, 104.0)
    assert not pred.held_keep(ctx, dict(call, strike=23000.0), 104.0)
    st = tp.p.stats
    assert (st["keep_asked"], st["keep_held"], st["keep_not_in_profit"], st["keep_edge_below_line"], st["keep_no_forecast"]) == (4, 1, 1, 1, 1)
    assert pred.held_exit(ctx, put, 104.0) is None and "FORECAST EXIT" in pred.held_exit(ctx, put, 106.0)
    assert pred.held_exit(ctx, dict(put, strike=23000.0), 106.0) is None
    assert (st["exit_asked"], st["exit_eligible"], st["exit_spoke"], st["exit_no_forecast"]) == (3, 1, 1, 1)


# -- finding G: a quote age of exactly zero ------------------------------------------------------------------------
def test_a_quote_age_of_zero_is_a_fresh_quote_for_the_premium_barrier():
    class B:
        p = config.VARIANTS["p02_ctl_mom"]
    key = "NIFTY|OPT|2026-11-17|25000|CE"
    gx = {"tp": 1e9, "sl": 1e9, "hold": 300, "tp_prem": T.BARRIER, "sl_prem": T.BARRIER}
    pos = {"gx": gx, "fut_in": 25000.0, "dir": 1, "t_in": 0.0, "entry": 100.0, "key": key, "strike": 25000.0, "rr": "CE",
           "expiry": "2026-11-17", "episode": 0}
    ctx = lambda age, bid: {"pred": None, "gen2": None, "gen3": None, "now_s": 5.0, "w0": "2026-11-17",
                            "by_key": {key: {"bid": bid, "age": age}}}
    assert paper._gen_exit(B, ctx(0, 106.0), pos, 25000.0) == "TARGET (premium)"
    assert paper._gen_exit(B, ctx(0.0, 94.0), pos, 25000.0) == "STOP (premium)"
    assert paper._gen_exit(B, ctx(None, 106.0), pos, 25000.0) is None        # no age: not trusted
    assert paper._gen_exit(B, ctx(20.0, 106.0), pos, 25000.0) is None        # stale: not trusted


# -- the second review (11 Nov): full identity through the pending entry and the fill, capacity, life cycle ---------
def test_the_signal_and_the_binding_carry_the_expiry():
    tp = Tape()
    exe = [(24950.0, 0, "exe"), (25050.0, 1, "exe")]
    for n, drift in ((F.WARM_S + 5, 0.0), (40, 0.3)):
        for _ in range(n):
            tp.t += 1.0
            tp.mid += drift
            cash = np.array([1000.0, 2000.0, 1500.0, 500.0])
            ce, pe = np.maximum(tp.mid - K, 0) + 100.0, np.maximum(K - tp.mid, 0) + 100.0
            tp.p.update(tp.t, tp.mid - 0.5, tp.mid + 0.5, 0.2, cash, np.full(4, 0.3), cash - 0.05, cash + 0.05,
                        np.full(4, 0.3), W, K, np.c_[ce - 0.1, pe - 0.1], np.c_[ce + 0.1, pe + 0.1], np.full((5, 2), 0.3),
                        2, False, 3600 + (tp.t - T0), extra=exe, expiry="2026-11-17")
    s = tp.p.sig["p02_clock"]
    assert s["expiry"] == "2026-11-17" and s["key"] == "NIFTY|OPT|2026-11-17|24950|CE"

    class B:
        p = dict(config.VARIANTS["p02_clock"])
        ctl = {}
    ctx = _ctx(o={(24950, "CE"): {}})
    B.ctl = {"want": (24950.0, "CE", "f1", "2026-11-17", 7)}
    assert paper.choose_contract(ctx, 1, B)[0]["key"] == "NIFTY|OPT|2026-11-17|24950|CE"
    B.ctl = {"want": (24950.0, "CE", "f1", "2026-11-10", 7)}                 # forecast made before the week rolled
    got, msg = paper.choose_contract(ctx, 1, B)
    assert got is None and "expiry 2026-11-10 is not the near week" in msg


def test_the_queue_evicts_unfilled_first_and_says_so():
    mt = L.Maturity(cap=2)
    assert mt.add("a", "CE", 0.0) is None
    mt.fill("a", 1.0, 100.0)
    assert mt.add("b", "CE", 5.0) is None
    out = mt.add("c", "CE", 6.0)                              # full: the unfilled b goes, not the older filled a
    assert out["forecast_id"] == "b" and out["status"] == "C" and "a" in mt.open and mt.dropped == 1
    mt.fill("c", 7.0, 100.0)
    out = mt.add("d", "CE", 8.0)                              # all filled: the oldest goes, and it is reported
    assert out["forecast_id"] == "a" and out["entry"] == 100.0


def test_a_fill_later_than_the_next_second_is_no_fill():
    mt = L.Maturity()
    mt.add("x", "CE", 10.0)
    mt.fill("x", 12.5, 100.0)                                 # 2.5 s later: offline would have no entry either
    assert mt.open["x"]["entry"] is None
    assert [o["status"] for o in mt.step(12.5, lambda k: 100.0)] == ["L"]
    mt.add("y", "CE", 20.0)
    mt.fill("y", 21.0, 100.0)
    assert mt.open["y"]["entry"] == 100.0 and mt.step(21.5, lambda k: 100.0) == []


def test_a_restart_keeps_signal_numbers_closes_a_torn_line_and_resolves_the_orphans(tmp_path):
    d = str(tmp_path)
    led = L.Ledger(d, "2026-11-11")
    x = np.zeros(len(F.NAMES))
    a = led.issue(1.0, "25000|CE", x, None, "enter", "r", "p02_clock", "h", "2026-11-09", extra=dict(signal_id=7))
    b = led.issue(2.0, "25000|PE", x, None, "sample", "r", "sample", "h", "2026-11-09")
    led.link(a, "outcome", 9.0, status="ok")
    led.flush()
    with open(led.fpath, "a", encoding="utf-8") as f:
        f.write('{"sequence": 3, "forecast_id": "torn')         # the process died inside a write
    p = pred.Pred(artefact=artefact(), ledger_dir=d, day="2026-11-11")
    assert p.n_sig == 7 and p.led.torn == 1 and p.led.seq == 2
    c = p.led.issue(3.0, "25000|CE", x, None, "sample", "r", "sample", "h", "2026-11-09")
    p.led.flush()
    rows = [json.loads(l) for l in open(led.fpath, encoding="utf-8") if l.strip() and not l.startswith('{"sequence": 3, "forecast_id": "torn')]
    assert [r["forecast_id"] for r in rows] == [a, b, c]       # the new record is a whole line of its own
    outs = [json.loads(l) for l in open(led.opath, encoding="utf-8")]
    assert [(o["forecast_id"], o["status"]) for o in outs] == [(a, "ok"), (b, "restart")]
    again = pred.Pred(artefact=artefact(), ledger_dir=d, day="2026-11-11")
    assert again.led.pending() == 1 and not again.led.unresolved      # only c is still open; b is not reported twice


# -- docs/44 section 2: the registry validates what it hands out ----------------------------------------------------
def test_the_registry_never_gives_a_model_its_own_day_and_checks_the_file(tmp_path):
    from apex.predict import registry as R
    d = str(tmp_path)
    os.makedirs(os.path.join(d, "artefacts"))
    rows = []
    for cut, eff in (("2026-11-05", "2026-11-06"), ("2026-11-06", "2026-11-09"), ("2026-11-09", None)):
        a = dict(artefact(), training_cutoff=cut, trained_through=cut, effective_from=eff)
        a["hash"] = Mo.model_hash(a)
        json.dump(a, open(os.path.join(d, "artefacts", f"m_{cut}.json"), "w"))
        rows.append(dict(file=f"artefacts/m_{cut}.json", hash=a["hash"], trained_through=cut, effective_from=eff))
    reg = os.path.join(d, "registry.json")
    json.dump(dict(artefacts=rows), open(reg, "w"))
    assert R.validated("2026-11-05", reg)[0] is None and "no artefact fitted before" in R.validated("2026-11-05", reg)[1]
    for day, cut in (("2026-11-06", "2026-11-05"), ("2026-11-09", "2026-11-06"), ("2026-11-10", "2026-11-09"), ("2026-12-01", "2026-11-09")):
        art, why, row = R.validated(day, reg)
        assert art["training_cutoff"] == cut and cut < day and "simulated" in why, day
    p = os.path.join(d, "artefacts", "m_2026-11-06.json")
    a = json.load(open(p))
    a["edge_quantiles"]["0.95"] += 0.01                     # the file was changed after it was registered
    json.dump(a, open(p, "w"))
    art, why, _ = R.validated("2026-11-09", reg)
    assert art is None and "does not match its hash" in why
    os.remove(p)
    assert "missing" in R.validated("2026-11-09", reg)[1]
    rows[2]["trained_through"] = "2026-11-08"                # registry and file disagree on the cut-off
    json.dump(dict(artefacts=rows), open(reg, "w"))
    assert "cut-off" in R.validated("2026-11-10", reg)[1]
    assert R.validated("2026-11-10", os.path.join(d, "none.json"))[1] == "no artefact registry"


# -- 11 Nov: the dashboard's forecast panel (display only) ----------------------------------------------------------
def test_the_forecast_panel_says_what_is_forecast_and_is_plain_json():
    tp = Tape()
    exe = [(24950.0, 0, "exe"), (25050.0, 1, "exe"), (24900.0, 0, "held"), (30000.0, 1, "held")]
    _feed(tp, 5, extra=exe)
    cold = tp.p.panel()
    assert cold["rows"] == [] and "warming" in cold["why"] and json.loads(json.dumps(cold)) == cold
    _feed(tp, F.WARM_S + 5, extra=exe)
    _feed(tp, 40, drift=0.3, extra=exe)
    v = tp.p.panel()
    assert json.loads(json.dumps(v)) == v                     # nothing a browser cannot read
    assert v["horizon_s"] == 300 and v["barrier_pct"] == 5.0 and v["ok"] and v["signals"] >= 1
    assert [(r["strike"], r["side"], r["tag"]) for r in v["rows"]] == [(24950.0, "CE", "exe"), (25050.0, "PE", "exe"), (24900.0, "CE", "held")]
    for r in v["rows"]:
        assert 0 <= r["up"] <= 1 and 0 <= r["down"] <= 1 and abs(r["up"] + r["down"] + r["flat"] - 1) < 1e-3
        assert r["up60"] <= r["up"] + 1e-9 and r["down60"] <= r["down"] + 1e-9      # the short horizon is inside the long one
    call = v["rows"][0]
    assert call["above_line"] and call["up"] > call["down"]   # the tape drifts up: the call leads
    assert v["last"]["side"] == "CE" and v["last"]["strike"] == 24950.0
    assert any(m["strike"] == 30000.0 and "grid" in m["why"] for m in v["missing"])
    assert tp.p.panel() is v                                  # built once a second
    assert pred.Pred(artefact=dict(artefact(), feature_schema="other")).panel()["ok"] is False


def test_the_panel_headline_compares_one_event_and_never_speaks_for_the_books():
    """11 Nov, review of the first panel: the reviewer's two cases (a put with the higher gain chance but the lower
    gain-minus-loss; held contracts only) and three more, run against the page's own function with node."""
    import shutil
    import subprocess
    node = shutil.which("node")
    if node is None:
        import pytest
        pytest.skip("node is not installed")
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([node, os.path.join(here, "js", "forecast_headline_test.js"), os.path.join(config.ROOT, "apex", "static", "app.js")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and "passed: 5" in r.stdout, r.stdout + r.stderr


def test_the_panel_names_the_range_model_and_each_book_and_carries_no_invented_score():
    tp = Tape()
    v = tp.p.panel()
    assert set(v["books"]) == set(pred.NAMES) and v["evaluation"] is None and v["range_model"] is None
    js = open(os.path.join(config.ROOT, "apex", "static", "app.js"), encoding="utf-8").read()
    a, b = js.index("function forecastHeadline("), js.index("function renderIdeas(")
    panel = js[a:b]
    for banned in ("0.54", "more likely to rise", "Strong enough", "most likely between"):
        assert banned not in panel, banned
    for needed in ("10th to 90th percentile", "Raw entry level", "separate model", "No out-of-sample evaluation is attached", "about ₹"):
        assert needed in panel, needed


# -- docs/46 (11 Nov, before the open): findings 1, 2 and 5 ---------------------------------------------------------
def _feed_q(tp, n, drift=0.0, extra=None, o_age=0.3, atm_shift=0.0):
    for _ in range(n):
        tp.t += 1.0
        tp.mid += drift
        cash = np.array([1000.0, 2000.0, 1500.0, 500.0])
        ce = np.maximum(tp.mid - K, 0) + 100.0
        pe = np.maximum(K - tp.mid, 0) + 100.0
        tp.p.update(tp.t, tp.mid - 0.5, tp.mid + 0.5, 0.2, cash, np.full(4, 0.3), cash - 0.05, cash + 0.05, np.full(4, 0.3),
                    W, K, np.c_[ce - 0.1, pe - 0.1], np.c_[ce + 0.1, pe + 0.1], np.full((5, 2), o_age), 2, False,
                    3600 + (tp.t - T0), extra=extra, expiry="2026-11-17")
        for nm, s in tp.p.sig.items():
            if s["t"] == tp.t:
                tp.seen.append((nm, dict(s)))


def test_a_signal_dies_when_its_contract_loses_its_current_forecast():
    from apex.engine import gen2
    exe = [(24950.0, 0, "exe"), (25050.0, 1, "exe")]

    class B:
        p = config.VARIANTS["p02_clock"]
        fired_episodes = set()
        ctl = {}
    tp = Tape()
    _feed_q(tp, F.WARM_S + 5, extra=exe)
    for _ in range(60):
        _feed_q(tp, 1, drift=0.3, extra=exe)
        if "p02_clock" in tp.p.sig and tp.p.sig["p02_clock"]["t"] == tp.t:
            break
    s = dict(tp.p.sig["p02_clock"])
    ctx = {"pred": tp.p, "gen2": gen2.Gen2(), "gen3": None, "now_s": s["t"] + 0.5, "w0": "2026-11-17"}
    assert paper.evaluate_gen(B, ctx)[0]                           # fresh: accepted
    _feed_q(tp, 1, drift=0.3, extra=exe, o_age=9.0)                # the next second every option quote is stale
    assert not tp.p.cur and "p02_clock" not in tp.p.sig            # no current forecast: the signal is withdrawn
    B.ctl, B.fired_episodes = {}, set()
    ok, why = paper.evaluate_gen(B, dict(ctx, now_s=s["t"] + 1.2)) # still inside the old 1.5-s life of the signal
    assert not ok and "want" not in B.ctl
    tp.p.sig["p02_clock"] = s                                      # even if a stale signal object were still around,
    ok, why = paper.evaluate_gen(B, dict(ctx, now_s=s["t"] + 1.2)) # the entry check asks for a CURRENT forecast
    assert not ok and "signal dropped" in why and "fresh two-sided quote" in why
    tp.p.now = s["t"] - 5.0                                        # and a forecaster that has not updated is not current
    assert "signal dropped" in paper.evaluate_gen(B, dict(ctx, now_s=s["t"] + 1.2))[1]


def test_the_chain_edge_does_not_silence_buyable_and_held_contracts():
    for start, exe in ((24905.0, [(24900.0, 1, "exe"), (24950.0, 0, "held")]),       # at-the-money = the first strike
                       (25095.0, [(25100.0, 0, "exe"), (25050.0, 1, "held")])):      # at-the-money = the last strike
        tp = Tape()
        tp.mid = start
        _feed_q(tp, F.WARM_S + 5, extra=exe)
        assert tp.p.fs.atm() in (0, len(K) - 1)
        assert len(tp.p.cur) >= 3 and all(tp.p.edge_of(s, r) is not None for s, r, _ in exe)
        assert "edge of the recorded chain" not in str(tp.p.why["p02_clock"])
        v = tp.p.panel()
        assert {(r["strike"], r["tag"]) for r in v["rows"]} == {(s, t) for s, _, t in exe}


def test_published_means_before_that_sessions_open(tmp_path):
    from apex.predict import registry as R
    d = str(tmp_path)
    os.makedirs(os.path.join(d, "artefacts"))
    a = dict(artefact(), training_cutoff="2026-11-09", trained_through="2026-11-09", effective_from=None)
    a["hash"] = Mo.model_hash(a)
    json.dump(a, open(os.path.join(d, "artefacts", "m.json"), "w"))
    reg = os.path.join(d, "registry.json")

    def why(pub, day):
        row = dict(file="artefacts/m.json", hash=a["hash"], trained_through="2026-11-09", effective_from=None)
        if pub is not None:
            row["published"] = pub
        json.dump(dict(artefacts=[row]), open(reg, "w"))
        return R.validated(day, reg)[1]
    assert "before the open of 2026-11-11" in why("2026-11-11 08:22:19", "2026-11-11") and "simulated" not in why("2026-11-10 20:00:00", "2026-11-11")
    assert "not before the open" in why("2026-11-11 09:15:00", "2026-11-11") and "simulated" in why("2026-11-11 11:00:00", "2026-11-11")
    assert "simulated" in why("2026-11-12 08:00:00", "2026-11-10")       # published later than the day it is asked about
    assert "simulated" in why("yes", "2026-11-11") and "simulated" in why(True, "2026-11-11") and why(None, "2026-11-11").endswith("availability simulated")


# -- 11 Nov evening: the hazard artefact, and the engine's session-based loading (docs/46 findings 3 and 4) ----------
def _hazard_art(cut="2026-11-09", bias_up=0.5):
    from apex.predict import hazard as Hz
    p = len(F.NAMES)
    W = []
    for j in range(len(T.HORIZONS)):
        up, dn = [-2.0 + 0.2 * j] + [0.0] * p, [-2.0 + 0.2 * j] + [0.0] * p
        up[1 + F.NAMES.index("mom30")], dn[1 + F.NAMES.index("mom30")] = bias_up, -bias_up
        W.append([up, dn])
    a = dict(version=3, kind=Hz.KIND, feature_schema=F.SCHEMA, target_spec=T.SPEC, med=[0.0] * p, sd=[1.0] * p, W=W,
             training_cutoff=cut, trained_through=cut, effective_from=None,
             edge_quantiles={"0.5": 0.0, "0.95": 0.2, "0.99": 0.5}, mom30_q95=5.0)
    a["hash"] = Mo.model_hash(a)
    return a


def test_the_hazard_forecaster_is_coherent_by_construction():
    fc = L.Forecaster(artefact=_hazard_art())
    assert fc.ok and fc.kind == "hazard"
    rng = np.random.default_rng(1)
    X = rng.normal(0, 2.0, (300, len(F.NAMES)))
    pT, pA = fc.score(X)
    assert (np.diff(pT, axis=1) >= 0).all() and (np.diff(pA, axis=1) >= 0).all()       # cumulative: never falling
    assert (pT + pA <= 1 + 1e-12).all() and (pT >= 0).all() and (pA >= 0).all()         # the three outcomes sum to one
    up = X.copy(); up[:, F.NAMES.index("mom30")] = 3.0
    dn = X.copy(); dn[:, F.NAMES.index("mom30")] = -3.0
    assert (fc.edges(up) > fc.edges(dn)).all()                                          # the input moves the edge the right way
    f = fc.forecast(X[0])
    assert abs(f["edge"] - (pT[0, -1] - pA[0, -1])) < 1e-12 and abs(f["pT"][300] + f["pA"][300] + f["pN"][300] - 1) < 1e-12
    bad = dict(_hazard_art(), W=[[[0.0]]])
    assert not L.Forecaster(artefact=bad).ok


def test_the_engine_loads_by_session_and_never_a_model_that_saw_it(tmp_path):
    from apex.predict import registry as R
    d = str(tmp_path)
    os.makedirs(os.path.join(d, "artefacts"))
    rows = []
    for cut, eff in (("2026-11-06", "2026-11-09"), ("2026-11-09", None)):
        a = _hazard_art(cut)
        a["effective_from"] = eff
        a["hash"] = Mo.model_hash(a)
        json.dump(a, open(os.path.join(d, "artefacts", f"h_{cut}.json"), "w"))
        rows.append(dict(file=f"artefacts/h_{cut}.json", hash=a["hash"], trained_through=cut, effective_from=eff))
    reg = os.path.join(d, "registry.json")
    json.dump(dict(artefacts=rows), open(reg, "w"))
    art, why = R.for_session("2026-11-09", "chronological", None, reg)
    assert art["training_cutoff"] == "2026-11-06" and why.startswith("chronological")
    art, why = R.for_session("2026-11-12", "chronological", None, reg)
    assert art["training_cutoff"] == "2026-11-09"
    art, why = R.for_session("2026-11-05", "chronological", "anything.json", reg)
    assert art is None and "no artefact fitted before" in why                           # silent, never a fallback
    disc = os.path.join(d, "artefacts", "h_2026-11-09.json")
    art, why = R.for_session("2026-11-05", "discovery", disc, reg)
    assert art["training_cutoff"] == "2026-11-09" and why.startswith("discovery")       # only when asked for
    assert R.for_session("2026-11-05", "discovery", os.path.join(d, "none.json"), reg)[0] is None
    p = pred.Pred(None, None, "2026-11-05", artefact=art)
    assert p.in_sample                                                                  # and it says so


def test_the_installed_registry_serves_the_next_live_session():
    from apex.predict import registry as R
    if not os.path.exists(R.PATH):
        return
    rows = R.load()
    assert rows and all(r.get("kind") == "hazard" for r in rows)
    last = max(rows, key=lambda r: r["trained_through"])
    nxt = "2099-01-01"
    art, why, row = R.validated(nxt)
    assert art is not None and art["target_spec"] == T.SPEC and L.Forecaster(artefact=art).ok, why
    assert row["trained_through"] == last["trained_through"] and "before the open" in why
    assert config.PREDICT_MODE == "chronological"
