"""11 Nov (docs/44 section 2, M0): one forecast order end to end through the books' real request and fill functions.

  1. a forecast signal -> evaluate_entry -> choose_contract (bound) -> request_entry -> a delayed fill on the first
     print after the trigger: the position is on the scored contract and both the position and the ledger say so;
  2. a restart while the order is pending: the order is gone (the policy: a pending entry is not carried over a
     restart), nothing fills later, the forecast gets a terminal record, and the next signal has a new number;
  3. a restart with the position already open: the position keeps the identity of its forecast and its bracket.

Synthetic tape, hand-made artefact. Behaviour only."""
import json
import os
import sys
import tempfile
from datetime import datetime

import numpy as np

os.environ.setdefault("APEX_DATA", tempfile.mkdtemp(prefix="apex_test_fclife_"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apex import config  # noqa: E402
from apex.engine import gen2, paper, pred  # noqa: E402
from apex.predict import features as F  # noqa: E402
from test_pred import K, T0, W, artefact  # noqa: E402

W0 = "2026-11-17"
DAY = "2026-11-12"
NOW = datetime(2026, 11, 12, 11, 0, tzinfo=config.IST)
EXE = [(24950.0, 0, "exe"), (25050.0, 1, "exe")]


class Rig:
    """A forecaster on a synthetic tape plus the context the books read, second by second."""

    def __init__(self, folder):
        self.folder = folder
        self.p = pred.Pred(artefact=artefact(), ledger_dir=folder, day=DAY)
        self.t, self.mid = T0, 25000.0

    def restart(self):
        self.p.flush()
        self.p = pred.Pred(artefact=artefact(), ledger_dir=self.folder, day=DAY)     # features start cold, as live

    def step(self, n=1, drift=0.0):
        for _ in range(n):
            self.t += 1.0
            self.mid += drift
            cash = np.array([1000.0, 2000.0, 1500.0, 500.0])
            ce, pe = np.maximum(self.mid - K, 0) + 100.0, np.maximum(K - self.mid, 0) + 100.0
            self.p.update(self.t, self.mid - 0.5, self.mid + 0.5, 0.2, cash, np.full(4, 0.3), cash - 0.05, cash + 0.05,
                          np.full(4, 0.3), W, K, np.c_[ce - 0.1, pe - 0.1], np.c_[ce + 0.1, pe + 0.1], np.full((5, 2), 0.3),
                          2, False, 3600 + (self.t - T0), extra=EXE, expiry=W0)

    def ctx(self, dt=0.0, age=0.1, shift=0.0):
        """The books' context `dt` seconds after the forecaster's last second; every option printed `age` s ago."""
        opts = []
        for j, k in enumerate(K):
            for rr, px in (("CE", max(self.mid - k, 0) + 100.0), ("PE", max(k - self.mid, 0) + 100.0)):
                key = f"NIFTY|OPT|{W0}|{int(k)}|{rr}"
                itm = (self.mid - k) if rr == "CE" else (k - self.mid)
                opts.append({"id": 10 * j + (rr == "PE"), "key": key, "strike": float(k), "rr": rr, "expiry": W0, "week": 0,
                             "ltp": px + shift, "bid": px + shift - 0.1, "ask": px + shift + 0.1, "age": age, "ltt": None,
                             "delta": (0.5 + itm / 200.0) * (1 if rr == "CE" else -1), "iv": 12.0})
        return {"now_s": self.t + dt, "now_dt": NOW, "w0": W0, "spot": self.mid, "spot_hi": self.mid, "spot_lo": self.mid,
                "fut": self.mid, "fut_mid": self.mid, "fut_ltp": self.mid, "advisors": {}, "blackout": {"on": False},
                "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
                "episode": None, "regime": {"state": "RANGE", "dir": None}, "fut_age": 0.1, "spot_age": 0.3,
                "pred": self.p, "gen2": gen2.Gen2(), "gen3": None, "options": opts,
                "by_key": {o["key"]: o for o in opts}, "by_id": {o["id"]: o for o in opts}}


def _signal(rig):
    rig.step(F.WARM_S + 5)
    for _ in range(60):
        rig.step(1, drift=0.3)
        s = rig.p.sig.get("p02_clock")
        if s and s["t"] == rig.t:
            return s
    raise AssertionError("no forecast signal on the synthetic tape")


def _request(rig, b):
    """The engine's entry path for one book, as engine_main._entry_choice then request_entry."""
    c = rig.ctx(dt=0.2)
    fire, why = paper.evaluate_entry(b, c, [])
    assert fire, why
    opt, msg = paper.choose_contract(c, paper.entry_dir(b, c), b)
    assert opt is not None, msg
    paper.request_entry(b, c, opt, why)
    return opt


def _rows(path):
    return [json.loads(x) for x in open(path, encoding="utf-8")] if os.path.exists(path) else []


def test_a_forecast_order_fills_later_on_the_scored_contract_and_both_records_say_so(tmp_path):
    rig = Rig(str(tmp_path))
    s = _signal(rig)
    assert s["key"] == f"NIFTY|OPT|{W0}|24950|CE"                 # the executable call, with its expiry
    b = paper.Book("p02_clock", config.VARIANTS["p02_clock"], DAY)
    opt = _request(rig, b)
    pe = b.ctl["pending_entry"]
    assert opt["key"] == s["key"] == pe["key"] and pe["want"][2] == s["forecast_id"] and pe["want"][3] == W0
    assert b.pos is None
    pos, why = paper.try_fill_entry(b, rig.ctx(dt=0.4, age=0.5))  # the only print is older than the trigger: wait
    assert pos is None and "pending" in why
    rig.step(1, drift=0.3)                                        # a second passes; the market moved; a new print
    pos, why = paper.try_fill_entry(b, rig.ctx(dt=0.3, age=0.1, shift=1.5))
    assert pos, why
    assert pos["key"] == s["key"] and pos["fc_sig"] == {"id": s["forecast_id"], "key": s["key"], "same": True, "signal": s["id"]}
    assert pos["gx"]["tp_prem"] and pos["fill_delay_s"] > 1.0     # the bracket of the signal, a delayed fill
    rig.p.flush()
    fills = [r for r in _rows(rig.p.led.opath) if r["kind"] == "fill"]
    assert len(fills) == 1 and fills[0]["forecast_id"] == s["forecast_id"] and fills[0]["key"] == s["key"]
    assert fills[0]["same_contract"] is True and fills[0]["book"] == "p02_clock" and fills[0]["entry"] == pos["entry"]
    fc = [r for r in _rows(rig.p.led.fpath) if r["forecast_id"] == s["forecast_id"]][0]
    assert fc["extra"]["key"] == s["key"] and fc["extra"]["exe"] is True and fc["instrument"] == "24950|CE"


def test_a_restart_with_a_pending_order_cancels_it_for_good(tmp_path):
    rig = Rig(str(tmp_path))
    s = _signal(rig)
    b = paper.Book("p02_clock", config.VARIANTS["p02_clock"], DAY)
    _request(rig, b)
    assert b.ctl.get("pending_entry")
    saved = json.loads(json.dumps(b.to_json(), default=str))      # what a restart reads back
    b2 = paper.Book.from_json(saved)
    rig.restart()
    assert "pending_entry" not in b2.ctl and b2.pos is None       # the order did not survive, by design
    for _ in range(5):                                            # prints keep coming: nothing may fill
        rig.step(1, drift=0.3)
        pos, why = paper.try_fill_entry(b2, rig.ctx(dt=0.3, age=0.1))
        assert pos is None and why == ""
    rig.p.flush()
    outs = [r for r in _rows(rig.p.led.opath) if r["forecast_id"] == s["forecast_id"]]
    assert [(r["kind"], r["status"]) for r in outs] == [("outcome", "restart")]       # a terminal record, once
    assert not [r for r in _rows(rig.p.led.opath) if r["kind"] == "fill"]
    assert rig.p.n_sig >= s["id"]                                 # numbering continues after the restart
    s2 = _signal(rig)                                             # the forecaster warms up again, then signals
    assert s2["id"] > s["id"] and s2["forecast_id"] != s["forecast_id"]
    c = rig.ctx(dt=0.2)
    fire, why = paper.evaluate_entry(b2, c, [])
    assert fire, why                                              # a new number: not "already traded"
    rig.restart()
    again = [r for r in _rows(rig.p.led.opath) if r["forecast_id"] == s["forecast_id"]]
    assert len(again) == 1                                        # a second restart does not report it twice


def test_a_restart_with_an_open_position_keeps_the_forecast_identity_and_the_bracket(tmp_path):
    rig = Rig(str(tmp_path))
    s = _signal(rig)
    b = paper.Book("p02_clock", config.VARIANTS["p02_clock"], DAY)
    _request(rig, b)
    rig.step(1, drift=0.3)
    pos, why = paper.try_fill_entry(b, rig.ctx(dt=0.3, age=0.1))
    assert pos, why
    b2 = paper.Book.from_json(json.loads(json.dumps(b.to_json(), default=str)))
    rig.restart()
    assert b2.pos["key"] == s["key"] and b2.pos["fc_sig"]["id"] == s["forecast_id"] and b2.pos["fc_sig"]["same"] is True
    assert b2.pos["gx"]["tp_prem"] == pos["gx"]["tp_prem"] and b2.pos["gx"]["hold"] == 300
    assert s["id"] in {-int(e) - paper.GEN_ID0 for e in b2.fired_episodes if isinstance(e, int) and e < 0} \
        or paper.evaluate_entry(b2, rig.ctx(dt=0.2), [])[1] == "in position"
    key = b2.pos["key"]
    c = rig.ctx(dt=5.0)
    c["by_key"][key] = dict(c["by_key"][key], bid=b2.pos["entry"] * 1.06, age=0.2)    # +6 % on the bid after the restart
    assert paper._gen_exit(b2, c, b2.pos, rig.mid) == "TARGET (premium)"
    rig.p.flush()
    outs = [r for r in _rows(rig.p.led.opath) if r["forecast_id"] == s["forecast_id"]]
    assert [r["kind"] for r in outs] == ["fill"]                  # the signal's forecast was filled, not orphaned... and
    assert all(r.get("status") != "restart" for r in outs)        # ...a filled forecast is not marked as a restart orphan
