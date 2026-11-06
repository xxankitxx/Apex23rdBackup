"""7 Nov code review: DATA events on market time (4.1), the guard's bad-print flag (10.1)."""
from datetime import datetime
from types import SimpleNamespace

import numpy as np

from apex import config, engine_main
from apex.engine.guard import DataGuard


def _eng(now_s, ltt):
    ev = []
    e = SimpleNamespace(now_s=now_s, now_dt=datetime(2026, 11, 6, 11, 0, 0),
                        heroes=lambda: [(0, "CE", 24000.0), (1, "PE", 24000.0)],
                        ev=lambda k, m: ev.append((k, m)))
    return e, ev, {"ltt": np.array(ltt, dtype=float)}


def test_frozen_tape_once_per_market_second_and_once_per_contract():
    t0 = 1.8e9
    e, ev, snap = _eng(t0, [t0 - config.HERO_FROZEN_S - 5, t0 - 1])
    for k in range(25):                                   # 25 steps of 100 ms: at most 3 looks, one event
        e.now_s = t0 + 0.1 * k
        engine_main.Engine._frozen_tape(e, snap)
    assert len(ev) == 1 and ev[0][0] == "DATA" and "24000 CE" in ev[0][1] and "PE" not in ev[0][1]
    snap["ltt"][0] = e.now_s                              # it trades again, then freezes again: a new event
    e.now_s += 1.0
    engine_main.Engine._frozen_tape(e, snap)
    e.now_s += config.HERO_FROZEN_S + 2
    engine_main.Engine._frozen_tape(e, snap)
    assert len(ev) >= 2 and "24000 CE" in ev[-1][1]


def test_data_health_no_longer_writes_events():
    import inspect
    src = inspect.getsource(engine_main.Engine.data_health)
    assert "self.ev(" not in src and "_frozen_prev" not in src


def test_guard_bad_print_flag():
    g = DataGuard()
    assert g.bad_print is False
    g.update(100.0, 2, 0.5, fut_px=24000.0)
    g.update(101.0, 2, 0.5, fut_px=26000.0)               # an implausible jump
    assert g.on and g.bad_print and not g.exits_ok()
    g.update(400.0, 2, 0.5, step_gap=1e6)                 # an engine pause replaces the reason
    assert g.bad_print is False
