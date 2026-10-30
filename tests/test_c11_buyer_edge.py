"""27 Oct: buyer edge — gamma/theta gate, premium bracket + max hold, partial sizing, per-book daily stop
(docs/18_BUYER_EDGE.md). python tests/test_c11_buyer_edge.py"""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c11_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False
from apex.engine import paper  # noqa: E402
from apex.engine.edge import var_per_min  # noqa: E402

T0 = datetime(2026, 10, 23, 10, 30, tzinfo=config.IST)
# 22700 CE, ~ATM on a 4-DTE day: gamma 0.0012 / pt, theta -0.12 premium pts per trading minute
OPT = {"id": 5, "key": "NIFTY|OPT|2026-10-27|22700|CE", "strike": 22700, "rr": "CE", "expiry": "2026-10-27",
       "ltp": 200.0, "bid": 199.9, "ask": 200.1, "delta": 0.55, "iv": 14.0, "age": 0.1, "week": 0, "ltt": None,
       "gamma": 0.0012, "theta_min": -0.12}


def _ctx(s, v_min=None, **kw):
    c = {"now_s": float(s), "now_dt": T0, "w0": "2026-10-27", "spot": 22700.0, "spot_age": 0.3, "fut": 22715.0,
         "fut_ltp": 22715.0, "day": {}, "day_obj": None, "advisors": {}, "blackout": {"on": False},
         "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
         "episode": None, "regime": {}, "edge": {"v_min30": v_min}}
    c.update(kw)
    return c


def _held(b, s, ltp):
    q = dict(OPT, ltp=ltp)
    return _ctx(s, by_id={5: q}, by_key={OPT["key"]: q}, fut_age=0.1)


def test_registered_and_champion():
    p = config.VARIANTS["apex_edge"]
    assert config.CHAMPION_DEFAULT == "c20_9x" and config.validate() == []
    assert p["gt_min"] == 0.5 and (p["prem_stop"], p["prem_tgt"], p["max_hold_s"]) == (10.0, 20.0, 1800)
    assert p["lock_pct"] == 0.0 and not p["lvl_book"] and "alloc_pct" not in p and p["day_stop_pct"] == 20.0
    assert p["entry_mode"] == "pullback" and p["dte0_retest"]              # same entries as spot_dual_lvl
    for n in ("edge_gate_only", "edge_bracket_only", "edge_breakout", "spot_dual_lvl"):
        assert n in config.VARIANTS


def test_var_per_min_from_one_hz_samples():
    xs = [(float(t), 22700.0 + (3.0 if (t // 60) % 2 else -3.0)) for t in range(0, 1801)]   # +-3 pts each minute
    v = var_per_min(xs, 1800)
    assert v is not None and abs(v - 36.0) < 1e-6                         # every 1-min change is 6 pts
    assert var_per_min(xs[:301], 1800) == 36.0                             # 5 one-minute changes are enough (09:20 on)
    assert var_per_min(xs[:300], 1800) is None                             # 4 are not
    assert var_per_min([], 1800) is None


def test_gate_math_blocks_dear_and_passes_cheap_gamma():
    b = paper.Book("apex_edge", config.VARIANTS["apex_edge"], "2026-10-23")
    # ratio = 0.5 * 0.0012 * v / 0.12 = v / 200
    why = paper.buyer_edge_gate(b, _ctx(100, v_min=40.0), dict(OPT))      # ratio 0.2
    assert why.startswith("buyer edge: gamma pays 0.20") and b.ctl["gt_ratio"] == 0.2
    assert paper.buyer_edge_gate(b, _ctx(100, v_min=120.0), dict(OPT)) == ""   # ratio 0.6
    assert "not ready" in paper.buyer_edge_gate(b, _ctx(100, v_min=None), dict(OPT))
    assert "not ready" in paper.buyer_edge_gate(b, _ctx(100, v_min=120.0), dict(OPT, gamma=None))
    plain = paper.Book("spot_dual_lvl", config.VARIANTS["spot_dual_lvl"], "2026-10-23")
    assert paper.buyer_edge_gate(plain, _ctx(100, v_min=1.0), dict(OPT)) == ""   # no gt_min: no gate


def test_always_all_in():
    b = paper.Book("apex_edge", config.VARIANTS["apex_edge"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK"})
    pos = paper.open_trade(b, _ctx(100), dict(OPT), "t")
    assert pos["lots"] == int(config.START_CAPITAL // (200.0 * config.LOT_SIZE))   # owner's rule: all-in, every book
    a = paper.Book("spot_dual_lvl", config.VARIANTS["spot_dual_lvl"], "2026-10-23")
    a.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK"})
    assert paper.open_trade(a, _ctx(100), dict(OPT), "t")["lots"] == int(config.START_CAPITAL // (200.0 * config.LOT_SIZE))


def test_bracket_ignores_spot_trail_and_stops_on_premium():
    b = paper.Book("apex_edge", config.VARIANTS["apex_edge"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-BREAKOUT"})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    c = _held(b, 110, 185.0)
    c["spot"] = 22680.0                                                    # 20 pts against: a 12-pt trail would be out
    assert paper.check_exit(b, c) is None                                  # premium -7.5 %: inside the bracket
    t = paper.check_exit(b, _held(b, 120, 179.0))                          # -10.5 %
    assert t and t["reason"].startswith("STOP (premium"), t and t["reason"]


def test_bracket_target():
    b = paper.Book("apex_edge", config.VARIANTS["apex_edge"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-BREAKOUT"})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    t = paper.check_exit(b, _held(b, 200, 241.0))
    assert t and t["reason"].startswith("TARGET (premium")


def test_max_hold_exit():
    b = paper.Book("apex_edge", config.VARIANTS["apex_edge"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-BREAKOUT"})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    assert paper.check_exit(b, _held(b, 100 + 1799, 204.0)) is None
    t = paper.check_exit(b, _held(b, 100 + 1800, 204.0))
    assert t and t["reason"] == "TIME (max hold 30 min)"


def test_fade_switch_keeps_its_own_clock():
    b = paper.Book("fade_switch", config.VARIANTS["fade_switch"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "FADE"})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    c = _held(b, 100 + 200, 204.0)
    c["blackout"] = {"on": True}                                           # in a gap its bracket is frozen ...
    assert paper.check_exit(b, c) is None                                  # ... and the generic max hold does not fire


def test_per_book_daily_stop():
    b = paper.Book("apex_edge", config.VARIANTS["apex_edge"], "2026-10-23")
    b.capital = config.START_CAPITAL * 0.79
    assert paper._daily_brake(b, _ctx(100, kill=False)).startswith("DAILY STOP")
    b.capital = config.START_CAPITAL * 0.81
    assert paper._daily_brake(b, _ctx(100, kill=False)) == ""
    a = paper.Book("spot_dual_lvl", config.VARIANTS["spot_dual_lvl"], "2026-10-23")
    a.capital = config.START_CAPITAL * 0.5
    assert paper._daily_brake(a, _ctx(100, kill=False)) == ""             # the global brake stays OFF for the others


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)
