"""apex.engine.quantview: the live, display-only quant block runs on a fake engine and reports sane numbers."""
import math
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.engine.quantview import QuantView  # noqa: E402
from apex.quant import greeks_hi as G  # noqa: E402


class _Eng:
    def __init__(self):
        self.w0 = "2026-11-10"
        self.atm = 23800
        self.key = {f"NIFTY|OPT|{self.w0}|{k}|{rr}": n for n, (k, rr) in enumerate(
            [(k, rr) for k in range(23500, 24150, 50) for rr in ("CE", "PE")])}
        self.n = len(self.key)
        self.greek = {}
        self.books, self.champion = {}, None
        self.now_s = datetime(2026, 11, 5, 10, 0, tzinfo=config.IST).timestamp()
        self.now_dt = datetime.fromtimestamp(self.now_s, config.IST)
        self.fwd = 23810.0


def _snap(eng, F, ttq_step, t):
    snap = {f: np.zeros(eng.n) for f in ("bid", "ask", "ltp", "ttq")}
    T = G.real_years(eng.w0, eng.now_dt)
    for key, i in eng.key.items():
        k, rr = int(key.split("|")[3]), key.split("|")[4]
        iv = 0.13 + 0.0000004 * (k - F) ** 2                       # a gentle smile
        p = G.price_s(F, k, T, iv, rr == "CE")
        snap["bid"][i], snap["ask"][i] = p - 0.25, p + 0.25
        snap["ltp"][i] = p + (0.25 if rr == "CE" else -0.25)      # calls print at the ask, puts at the bid
        snap["ttq"][i] = ttq_step * t
        eng.greek[i] = {"iv": iv * 100}
    return snap


def test_quantview_runs_and_reads_a_rally():
    eng, q = _Eng(), QuantView()
    rng = np.random.default_rng(0)
    F = 23810.0
    for t in range(400):
        F += 0.15 + rng.normal(0, 0.8)                              # a steady rally
        eng.fwd = F
        eng.now_s += 1.0
        eng.now_dt += timedelta(seconds=1)
        q.step(eng, _snap(eng, F, 650, t))
    v = q.view()
    assert v["kv"] > 0.05 and v["sig"] > 0.3
    ce, pe = v["po"]["CE"], v["po"]["PE"]
    assert all(0 <= x <= 1 for x in ce["up_by"]) and ce["up_by"] == sorted(ce["up_by"])
    assert ce["ever"] > pe["ever"]                                  # the rally favours the call
    assert v["flow"]["CE"]["ratio"] > 1 > v["flow"]["PE"]["ratio"]   # calls lifted, puts hit
    assert "23800CE" in v["greeks"] and math.isfinite(v["greeks"]["23800CE"]["vanna"])
    assert v["smile"] and len(v["smile"]["K"]) >= 5


def test_quantview_without_forward_is_quiet():
    eng, q = _Eng(), QuantView()
    eng.fwd = None
    q.step(eng, {})
    assert q.view() == {}
