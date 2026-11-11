"""10 Nov (docs/40 section 7, docs/41 section 6): the prediction-driven shadow signals (apex/engine/pred.py) on
synthetic tapes with a hand-made artefact. These tests pin behaviour: silence without a usable model or fresh inputs,
one signal per arming, the ledger record behind every signal, the matured-only calibrator. Not that it makes money."""
import json

import numpy as np

from apex.engine import pred
from apex.predict import features as F, models as Mo, targets as T

T0 = 1_794_196_800.0
K = np.array([24900.0, 24950.0, 25000.0, 25050.0, 25100.0])
W = np.array([30.0, 25.0, 25.0, 20.0])


def artefact(w_mom=0.5, line_in=0.2, line_out=0.0, mom_line=5.0):
    """Target-first grows with the signed 30-s futures move, adverse-first falls with it. Nothing else matters."""
    def model(sign, h):
        w = [0.0] * (len(F.NAMES) + 1)
        w[0] = -1.5 + h / 600.0
        w[1 + F.NAMES.index("mom30")] = sign * w_mom
        m = dict(kind="logit", names=list(F.NAMES), med=[0.0] * len(F.NAMES), sd=[1.0] * len(F.NAMES), w=w, l2=0, n=1, base=0.2, meta={})
        m["hash"] = Mo.model_hash(m)
        return m
    art = dict(version=1, feature_schema=F.SCHEMA, target_spec=T.SPEC, training_cutoff="2026-11-09",
               models={**{f"T{h}": model(1, h) for h in T.HORIZONS}, **{f"A{h}": model(-1, h) for h in T.HORIZONS}},
               edge_quantiles={"0.5": line_out, "0.95": line_in, "0.99": line_in + 0.4}, mom30_q95=mom_line)
    art["hash"] = Mo.model_hash(art)
    return art


class Tape:
    def __init__(self, art=None, tmp=None):
        self.p = pred.Pred(artefact=art if art is not None else artefact(), ledger_dir=tmp, day="2026-11-10" if tmp else None)
        self.t, self.mid, self.seen = T0, 25000.0, []
        self.ce_extra = 0.0

    def step(self, n=1, drift=0.0, f_age=0.2, o_age=0.3, ok=True, dt=1.0):
        for _ in range(n):
            self.t += dt
            self.mid += drift
            cash = np.array([1000.0, 2000.0, 1500.0, 500.0])
            ce = np.maximum(self.mid - K, 0) + 100.0 + self.ce_extra
            pe = np.maximum(K - self.mid, 0) + 100.0
            self.p.update(self.t, self.mid - 0.5, self.mid + 0.5, f_age, cash, np.full(4, 0.3), cash - 0.05, cash + 0.05,
                          np.full(4, 0.3), W, K, np.c_[ce - 0.1, pe - 0.1], np.c_[ce + 0.1, pe + 0.1], np.full((5, 2), o_age),
                          2, False, 3600 + (self.t - T0), ok=ok)
            for nm, s in self.p.sig.items():
                if s["t"] == self.t:
                    self.seen.append((nm, s))

    def names(self):
        return [n for n, _ in self.seen]


def test_silent_without_a_model_on_another_schema_before_warm_up_and_on_stale_inputs():
    tp = Tape(art=dict(artefact(), feature_schema="other"))
    tp.step(F.WARM_S + 60, drift=0.3)
    assert not tp.seen and "schema" in tp.p.why["p02_clock"] and not tp.p.ready()
    tp = Tape()
    tp.step(F.WARM_S - 20, drift=0.3)
    assert not tp.seen and "warming" in tp.p.why["p02_clock"]
    tp = Tape()
    tp.step(F.WARM_S + 5)
    tp.step(40, drift=0.3, f_age=9.0)                 # the index future's quote is stale all the way
    assert not tp.seen
    tp = Tape()
    tp.step(F.WARM_S + 5)
    tp.step(40, drift=0.3, o_age=9.0)                 # no option has a fresh quote
    assert not tp.seen and "fresh" in tp.p.why["p02_clock"]
    tp = Tape()
    tp.step(F.WARM_S + 5)
    tp.step(40, drift=0.3, ok=False)
    assert not tp.seen and "feed" in tp.p.why["p02_clock"]


def test_one_signal_per_arming_in_the_forecast_direction_with_the_premium_bracket():
    tp = Tape()
    tp.step(F.WARM_S + 5)
    assert not tp.seen and tp.p.ready()
    tp.step(40, drift=0.3)                            # +9 points in 30 s: the call's edge rises above the line
    assert tp.names().count("p02_clock") == 1 and tp.names().count("p02_ctl_mom") == 1
    top = [x for n, x in tp.seen if n == "p02_top1"]                 # the stricter line: no earlier than the 95 % line
    assert len(top) <= 1 and all(x["t"] >= dict(tp.seen)["p02_clock"]["t"] and x["edge"] >= 0.6 for x in top)
    s = dict(tp.seen)["p02_clock"]
    assert s["dir"] == 1 and s["rr"] == 0 and s["tp_prem"] == T.BARRIER and s["sl_prem"] == T.BARRIER and s["hold"] == 300
    assert s["ep"] == "P-P02-CLOCK" and "entry line" in s["why"] and s["edge"] >= 0.2
    tp.step(100, drift=-0.3)                          # down: the put's edge now leads, after the re-arm time
    d = [x for n, x in tp.seen if n == "p02_clock"]
    assert len(d) == 2 and d[1]["dir"] == -1 and d[1]["t"] - d[0]["t"] >= pred.REARM_S


def test_every_signal_and_every_sample_is_in_the_ledger_before_anything_else(tmp_path):
    tp = Tape(tmp=str(tmp_path))
    tp.step(F.WARM_S + 5)
    tp.step(40, drift=0.3)
    s = dict(tp.seen)["p02_clock"]
    tp.p.flush()
    rows = [json.loads(x) for x in open(tp.p.led.fpath, encoding="utf-8")]
    ent = [r for r in rows if r["decision"] == "enter" and r["role"] == "p02_clock"]
    assert len(ent) == 1 and ent[0]["forecast_id"] == s["forecast_id"] and ent[0]["model"] == tp.p.fc.hash
    assert ent[0]["issued_t"] == s["t"] and len(ent[0]["features"]) == len(F.NAMES) and ent[0]["training_cutoff"] == "2026-11-09"
    smp = [r for r in rows if r["decision"] == "sample"]
    assert len(smp) >= 4 and all(int(r["issued_t"]) % pred.SAMPLE_S == 0 for r in smp)     # traded or not
    assert [r["sequence"] for r in rows] == list(range(1, len(rows) + 1))


def test_the_calibrator_learns_only_from_forecasts_whose_horizon_has_passed(tmp_path):
    tp = Tape(tmp=str(tmp_path))
    tp.step(F.WARM_S + 5)
    tp.step(200)                                      # 200 flat seconds of samples: none has had its 300 s
    assert tp.p.stats["forecasts"] > 40 and tp.p.cal_T.updates == 0 and tp.p.stats["matured"] == 0
    tp.step(130)                                      # now the first samples are 310 s old
    assert tp.p.stats["matured"] > 0 and tp.p.cal_T.updates == tp.p.stats["matured"]
    tp.p.flush()
    outs = [json.loads(x) for x in open(tp.p.led.opath, encoding="utf-8")]
    assert outs and all(o["kind"] == "outcome" for o in outs) and outs[0]["first"]["300"] == "N"
    assert len(tp.p.mat.open) <= tp.p.mat.cap


def test_admission_and_the_forecast_exit_read_the_same_forecast():
    tp = Tape()
    tp.step(F.WARM_S + 5)
    tp.step(40, drift=0.3)
    ok_ce, e_ce, _ = tp.p.admit(25000.0, 0)
    ok_pe, e_pe, _ = tp.p.admit(25000.0, 1)
    assert ok_ce and e_ce > 0 and not ok_pe and e_pe < 0
    assert tp.p.admit(23000.0, 0)[0] and tp.p.admit(23000.0, 0)[1] is None       # no forecast is not a veto
    gx = dict(strike=25000.0, rr=0)
    assert tp.p.void("p02_clock", gx, 1) is None
    tp.step(40, drift=-0.3)                           # the move reverses: the held call's edge is gone
    assert "FORECAST GONE" in tp.p.void("p02_clock", gx, 1)
    assert tp.p.void("p02_ctl_mom", gx, 1) is None    # the control has no forecast exit
    v = tp.p.view()
    assert v["ok"] and v["model"] == tp.p.fc.hash and v["signals"] >= 1


def test_the_real_artefact_loads_when_it_is_there():
    import os
    from apex import config
    path = config.PREDICT_MODEL
    if not os.path.exists(path):
        return
    p = pred.Pred(artefact_path=path)
    assert p.fc.ok, p.fc.why
    assert p.line_in is not None and p.line_out is not None and p.line_in > p.line_out and p.mom_line > 0
    assert set(p.fc.art["models"]) == {f"{k}{h}" for k in "TA" for h in T.HORIZONS}


def test_the_book_reads_the_forecast_signal_and_exits_on_the_premium_or_the_forecast():
    from apex import config
    from apex.engine import gen2, paper
    assert set(config.PRED_BOOKS.values()) == set(pred.NAMES)
    for b, sg in config.PRED_BOOKS.items():
        v = config.VARIANTS[b]
        assert v["gen"] == sg and v["max_hold_s"] == 300 and v["no_trade_cap"]
    pool = json.dumps(getattr(config, "CONDUCTOR_POOL", "")) + json.dumps(getattr(config, "POOL", ""))
    assert not any(b in pool for b in config.PRED_BOOKS)                      # shadow only
    tp = Tape()
    tp.step(F.WARM_S + 5)
    tp.step(40, drift=0.3)
    s = dict(tp.seen)["p02_clock"]

    class B:
        p = config.VARIANTS["p02_clock"]
        fired_episodes = set()
        ctl = {}
    ctx = {"pred": tp.p, "gen2": gen2.Gen2(), "gen3": None, "now_s": s["t"] + 0.5, "w0": "2026-11-17"}
    ok, why = paper.evaluate_gen(B, ctx)
    assert ok and B.ctl["dir"] == 1 and B.ctl["ep_type"] == "P-P02-CLOCK" and "entry line" in why
    gx = paper.gen_bracket(B, ctx, B.ctl["fire_id"])
    assert gx["tp_prem"] == T.BARRIER and gx["sl_prem"] == T.BARRIER and gx["hold"] == 300 and gx["tp"] == 1e9
    key = "NIFTY|OPT|2026-11-17|25000|CE"
    pos = {"gx": gx, "fut_in": 25000.0, "dir": 1, "t_in": s["t"], "entry": 100.0, "key": key, "strike": 25000.0, "rr": "CE",
           "expiry": "2026-11-17", "episode": B.ctl["fire_id"]}
    q = lambda bid: {"by_key": {key: {"bid": bid, "age": 0.5}}}
    at = dict(ctx, now_s=s["t"] + 5, **q(102.0))
    assert paper._gen_exit(B, at, pos, 25010.0) is None                      # +2 %: inside the bracket, the edge still there
    assert paper._gen_exit(B, dict(at, **q(105.5)), pos, 25010.0) == "TARGET (premium)"
    assert paper._gen_exit(B, dict(at, **q(94.5)), pos, 25400.0) == "STOP (premium)"     # the premium decides, not the future
    assert paper._gen_exit(B, dict(at, now_s=s["t"] + 301), pos, 25010.0) == "HOLD-LIMIT"
    tp.step(40, drift=-0.3)                                                   # the forecast for the held call is gone
    assert "FORECAST GONE" in paper._gen_exit(B, dict(at, now_s=tp.t), pos, 24990.0)
    far = dict(pos, expiry="2026-11-24")                                      # a next-week contract: no forecast, no forecast exit
    assert paper._gen_exit(B, dict(at, now_s=tp.t), far, 24990.0) is None
    ctx["pred"] = None
    assert paper.evaluate_gen(B, ctx) == (False, "second-generation signals are off")


def test_the_two_twins_of_the_champion_read_the_forecast_for_the_held_contract():
    from apex import config
    assert config.validate() == []
    for n, k in (("fx_c20_9y", "fc_exit"), ("fr_c20_9y", "fc_hold")):
        v = config.VARIANTS[n]
        assert v["council"] == "c20_9y" and v["twin"] and v[k] and not n.startswith("c20")     # family counts unchanged
    tp = Tape()
    tp.step(F.WARM_S + 5)
    tp.step(40, drift=0.3)                            # the call's edge is high, the put's is low
    ctx = {"pred": tp.p, "w0": "2026-11-17"}
    call = {"strike": 25000.0, "rr": "CE", "expiry": "2026-11-17", "entry": 100.0}
    put = dict(call, rr="PE")
    assert pred.held_keep(ctx, call, 104.0) and not pred.held_keep(ctx, call, 99.0)       # holds only in profit
    assert not pred.held_keep(ctx, put, 104.0)                                            # and only with the forecast
    assert pred.held_exit(ctx, call, 108.0) is None                                       # the edge is still there
    assert pred.held_exit(ctx, put, 104.0) is None                                        # never gained 5 %: not a stop
    assert "FORECAST EXIT" in pred.held_exit(ctx, put, 106.0)
    far = dict(put, expiry="2026-11-24")
    assert pred.held_exit(ctx, far, 106.0) is None and not pred.held_keep(ctx, dict(call, expiry="2026-11-24"), 104.0)
    assert pred.held_exit({"pred": None}, put, 106.0) is None and not pred.held_keep({}, call, 104.0)
    assert pred.held_exit(ctx, dict(put, strike=23000.0), 106.0) is None                  # no forecast: silent
