"""Owner decisions of 18 Oct 2026 (O-1, O-4, O-6, O-8): python tests/test_owner.py  (numpy only)."""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_owner_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config, universe  # noqa: E402
config.FILL_NEXT_PRINT = False   # D-126: these suites test the exit/entry logic itself on same-step fills; D-126 has its own suite
from apex.engine import learning, paper  # noqa: E402
from apex.engine.guard import RESUME_S, DataGuard  # noqa: E402


def _open_ce():
    b = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-21")
    opt = {"id": 5, "key": "k", "strike": 25150, "rr": "CE", "expiry": "2026-10-27", "ltp": 150.0}
    ctx = {"now_s": 0, "now_dt": datetime(2026, 10, 21, 10, 0, tzinfo=config.IST), "fut": 25200.0, "advisors": {},
           "episode": {"id": 1, "dir": 1, "type": "BASKET-LED"}}
    paper.open_trade(b, ctx, opt, "t")
    return b, opt, ctx


def test_o4_guard_allows_exits_in_resume_but_not_after_bad_print():
    g = DataGuard()
    for t in range(int(RESUME_S) + 1):
        g.update(float(t), 2, 0.1, True, 25200.0)
    assert not g.on and g.exits_ok()
    g.update(100.0, 3, None)                                     # feed drops
    assert g.on and not g.exits_ok()                             # frozen: no price decision
    g.update(101.0, 2, 0.1, True, 25190.0)                       # fresh quotes again, still resuming
    assert g.on and g.exits_ok()                                 # stops may fire, entries still wait
    g2 = DataGuard()
    for t in range(int(RESUME_S) + 1):
        g2.update(float(t), 2, 0.1, True, 25200.0)
    g2.update(22.0, 2, 0.1, True, 25200.0 * 0.98)                # implausible print
    g2.update(22.1, 2, 0.1, True, 25200.0 * 0.98)                # the wrong price persists
    assert g2.on and not g2.exits_ok()                           # never a stop on a bad print


def test_o4_stop_fires_in_resume_phase_on_fresh_data():
    b, opt, ctx = _open_ce()
    fresh = dict(opt, ltp=140.0, age=0.2)
    c = dict(ctx, fut=25185.0, now_s=30, by_id={5: fresh}, by_key={"k": fresh},
             domino={"S_up": 0, "S_dn": 0, "z": 0}, fut_age=0.1,
             blackout={"on": True, "why": "feed stale", "exits_ok": True})
    t = paper.check_exit(b, c)
    assert t and t["reason"] == "STOP" and t["exit"] == 140.0 and t.get("gap") is True
    b2, opt2, ctx2 = _open_ce()
    c2 = dict(c, blackout={"on": True, "why": "implausible futures jump", "exits_ok": False})
    assert paper.check_exit(b2, c2) is None and b2.pos["best"] == 25200.0


def test_o1_variant_uses_interpolated_iv_rise_champion_does_not():
    assert config.VARIANTS["m2.0_s0.5_ivinterp"]["iv_interp"] is True
    assert "m2.0_s0.5_ivinterp" not in config.CONTROLS and config.validate() == []
    now = datetime(2026, 10, 21, 10, 0, tzinfo=config.IST)
    ctx = {"now_dt": now, "fut": 25205.0, "advisors": {}, "blackout": {"on": False},
           "domino": {"dir": 1, "z": 2.5, "S_up": 0.8, "S_dn": 0.0, "sigma15": 4.0, "gap": 0.0},
           "episode": {"id": 9, "dir": 1, "type": "BASKET-LED", "fut0": 25200.0, "first": "HDFCBANK", "gap": False},
           "iv_rise_since_onset": 2.0, "iv_rise_interp": 0.4,     # strike flip made the nearest-strike rise 2.0
           "regime": {"state": "DIRECTIONAL", "dir": 1}, "now_s": 0.0}   # D-112: an open regime gate
    champ = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-21")
    var = paper.Book("m2.0_s0.5_ivinterp", config.VARIANTS["m2.0_s0.5_ivinterp"], "2026-10-21")
    fc, wc = paper.evaluate_entry(champ, ctx, [])
    fv, wv = paper.evaluate_entry(var, ctx, [])
    assert not fc and "IV" in wc                                 # the frozen trigger is unchanged
    assert fv, wv                                                # the variant sees no real IV rise


def test_o8_no_verdict_before_30_trades_and_sigma_30():
    assert config.SPRT_SIGMA_PCT == 30.0 and config.SPRT_MIN_TRADES == 30
    for f in (learning.STATE, learning.DAYS, learning.REPORT):
        if os.path.exists(f):
            os.remove(f)
    champ = config.CHAMPION_DEFAULT
    day = "2026-11-02"
    books = {}
    for name in list(config.VARIANTS) + ["RAW"]:
        b = paper.Book(name, config.VARIANTS.get(name, config.TRIGGER), day)
        rets = [400.0] * 10 if name == champ else [0.5]           # 10 huge winners: still no GO
        b.trades = [{"pnl_pts": r, "pnl_rs": 0, "ret_pct": r, "entry": 100.0, "advisors": {},
                     "reason": "TRAIL", "time_in": "10:00:00"} for r in rets]
        books[name] = b
    learning.record_day(day, books)
    s = learning.learn(day)
    assert s["scoreboard"]["n"] == 0 or s.get("status") == "COLLECTING", s.get("status")
    assert s.get("status") == "COLLECTING"


def test_o6_tcs_itc_capped_at_top10_floor():
    w = universe.STOCKS
    assert w["TCS"][0] <= 2.52 and w["ITC"][0] <= 2.52


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
