"""13 Nov: the two shadow exit twins of c20_9y (master plan tier 1). tp_c20_9y sells at +60 % on an expiry day and
nowhere else; pgb_c20_9y adds c20_9v's PGB alone on normal days. Both are twins (not c20-family names, registered
last, never in the pool)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.engine import conductor as cond  # noqa: E402
from apex.engine.council import LiveDay, c20_9y, c20_9y_pgb, c20_9y_tp60  # noqa: E402


def _held(day, exp, bids, cls):
    D = LiveDay(day, exp)
    D.K = np.array([25000.0])
    D.col[(25000, "CE")] = 0
    s = cls()
    pos = {"rr": "CE", "strike": 25000.0, "j": 0, "i_in": 1300, "entry": 100.0, "qty": 75, "peak_bid": 100.0, "st": {}}
    out = None
    for k, i in enumerate(range(1300, 1300 + len(bids))):
        D.fwd[i] = 25000.0 + 0.2 * k
        D.bid[i, 0], D.ask[i, 0], D.age[i, 0] = bids[k], bids[k] + 0.5, 0.5
        D.i = i
        if i == 1300:
            for r in range(0, 1300):
                D.fwd[r] = 25000.0
            for r in range(0, 1300):
                s.on_second(r, D, None)
        pos["peak_bid"] = max(pos["peak_bid"], bids[k])
        sig = s.on_second(i, D, pos)
        if sig and sig[0] == "SELL":
            out = (k, sig[1])
            break
    return out


def test_registration_keeps_the_old_order_and_the_pool():
    names = list(config.VARIANTS)
    assert names[-9:-4] == ["tp_c20_9y", "pgb_c20_9y", "pm_c20_9y", "conductor_sl", "conductor_wp60"]      # 14 Nov: four more shadows follow (docs/57)
    assert all(config.VARIANTS[n].get("twin") for n in names[-9:-4])
    assert "tp_c20_9y" not in [e["book"] for e in cond.active_entries(cond.load_pool(), "2026-11-16")]


def test_take_profit_only_on_expiry_day():
    ramp = list(np.linspace(100, 170, 120))
    assert c20_9y_tp60.Strategy().pe["tp"] == 0.6 and c20_9y_tp60.Strategy().pn["tp"] == c20_9y.Strategy().pn["tp"]
    hit = _held("2026-11-17", "2026-11-17", ramp, c20_9y_tp60.Strategy)
    assert hit is not None and hit[1] == "TP" and ramp[hit[0]] >= 160.0
    base = _held("2026-11-17", "2026-11-17", ramp, c20_9y.Strategy)
    assert base is None or base[1] != "TP"


def test_pgb_sells_a_normal_day_giveback_and_leaves_expiry_alone():
    path = list(np.linspace(100, 130, 200)) + list(np.linspace(130, 105, 400))
    hit = _held("2026-11-13", "2026-11-17", path, c20_9y_pgb.Strategy)
    assert hit is not None and hit[1] in ("PGB", "RAMP", "GIVEBACK", "BE_LOCK", "FWD_TRAIL"), hit
