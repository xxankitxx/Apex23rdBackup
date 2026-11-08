"""The Conductor's account (8 Nov, docs/28 §7; apex/engine/conductor.py, apex/conductor/account_sim.py): it mirrors the
pool books' own trigger, fill and exit; same-tick priority; occupied and lost triggers logged; a lapsed owner released;
register-stated factor rules checked on the trigger photograph; the pool read as of the day; the offline simulator
agrees with the engine path to the trade; the owner survives a restart; the photograph checks."""
import json

import pytest
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.conductor import account_sim  # noqa: E402
from apex.engine import conductor as cond, paper, rules, weather  # noqa: E402

DAY = "2026-11-06"
T0 = datetime(2026, 11, 6, 10, 30, 0, tzinfo=config.IST).timestamp()
EXP = "2026-11-11"


def _opt(strike=24000, rr="CE", ltp=150.0, age=0.5):
    return {"key": f"NIFTY|OPT|{EXP}|{strike}|{rr}", "id": 7, "strike": float(strike), "rr": rr, "expiry": EXP,
            "ltp": ltp, "bid": ltp - 0.5, "ask": ltp + 0.5, "age": age, "delta": 0.55 if rr == "CE" else -0.55, "iv": 14.0}


def _ctx(t, opts=()):
    return {"now_s": t, "now_dt": datetime.fromtimestamp(t, config.IST), "fut": 24010.0, "fut_mid": None, "spot": 24005.0,
            "advisors": {}, "episode": None, "domino": {}, "regime": {}, "by_key": {o["key"]: o for o in opts}}


def _pool(*entries):
    return {"entries": list(entries)}


def _e(book, rule=None, standing="low", rpt=0.0, frm="2026-11-01"):
    return {"book": book, "rule": rule, "standing": standing, "ret_per_trade": rpt, "from": frm}


def _books(*names):
    bs = {n: paper.Book(n, config.VARIANTS["spot_dc12_t12"], DAY) for n in names}
    bs["conductor"] = paper.Book("conductor", config.VARIANTS["conductor"], DAY)
    return bs


def _fire(b, ctx, opt, why="SPOT brk", w=None):
    paper.request_entry(b, ctx, opt, why)
    b.ctl["pending_entry"]["weather_trig"] = w if w is not None else {"v": 3, "er60": 0.5, "dir60": 1, "expiry_day": False, "mins_open": 75}


def _fill(b, t, opt):
    o = dict(opt, age=0.2)
    pos, why = paper.try_fill_entry(b, _ctx(t, [o]))
    assert pos, why
    return pos


def _close(b, t, px, reason="TRAIL"):
    o = dict(b.pos and _opt(ltp=px) or {}, age=0.1)
    return paper.close_trade(b, _ctx(t, [o]), px, reason, o)


def _run(c, bs, ctx):
    return c.step(bs["conductor"], bs, ctx)


def test_mirror_entry_fill_and_exit(tmp_path):
    bs = _books("A")
    c = cond.Conductor(DAY, list(bs), pool=_pool(_e("A")), log_dir=str(tmp_path))
    o = _opt(ltp=100.0)
    _fire(bs["A"], _ctx(T0, [o]), o)
    r = _run(c, bs, _ctx(T0, [o]))
    assert r and r[0] == "owner" and bs["conductor"].ctl["owner"]["book"] == "A"
    assert _run(c, bs, _ctx(T0 + 0.5, [o])) is None            # A still waiting for its print
    pos_a = _fill(bs["A"], T0 + 1.0, dict(o, ltp=101.0))
    r = _run(c, bs, _ctx(T0 + 1.0, [o]))
    cb = bs["conductor"]
    assert r[0] == "entry" and cb.pos["key"] == pos_a["key"] and cb.pos["entry"] == 101.0 and cb.pos["src"] == "A"
    assert cb.pos["lots"] == int(config.START_CAPITAL // (101.0 * config.LOT_SIZE)) and "owner" not in cb.ctl
    assert cb.pos["weather_trig"] == pos_a["weather_trig"] and cb.pos["trigger_t"] == T0
    bs["A"].pos["peak_pts"] = 9.0
    assert _run(c, bs, _ctx(T0 + 30, [o])) is None and cb.pos["peak_pts"] == 9.0   # follows the owner while held
    _close(bs["A"], T0 + 60, 111.0, "TRAIL 10")
    r = _run(c, bs, _ctx(T0 + 60, [o]))
    assert r[0] == "exit" and cb.pos is None and len(cb.trades) == 1
    t = cb.trades[0]
    assert t["exit"] == 111.0 and t["reason"] == "TRAIL 10" and t["pnl_rs"] == round(10.0 * t["qty"], 2)
    assert cb.capital == config.START_CAPITAL + t["pnl_rs"] and t["ret_pct"] == bs["A"].trades[0]["ret_pct"]
    rows = [json.loads(x) for x in open(tmp_path / f"conductor_{DAY}.jsonl", encoding="utf-8")]
    assert [x["event"] for x in rows if x["event"] != "flat"] == ["owner", "entry", "exit"]


def test_same_tick_priority_then_occupied_then_release(tmp_path):
    bs = _books("A", "B", "C")
    pool = _pool(_e("A", standing="low", rpt=9.0), _e("B", standing="full", rpt=1.0), _e("C", standing="full", rpt=2.0, frm="2026-11-09"))
    c = cond.Conductor(DAY, list(bs), pool=pool, log_dir=str(tmp_path))
    assert [m["book"] for m in c.members] == ["B", "A"]            # C is not in the pool before 9 Nov; full before low
    oa, ob = _opt(24000, ltp=100.0), _opt(23900, "PE", ltp=120.0)
    ctx = _ctx(T0, [oa, ob])
    _fire(bs["A"], ctx, oa)
    _fire(bs["B"], ctx, ob)
    r = _run(c, bs, ctx)
    assert r[0] == "owner" and r[1]["book"] == "B"
    _fill(bs["B"], T0 + 1, ob)
    _fill(bs["A"], T0 + 1, oa)                                      # A trades on its own; the Conductor is B's
    r = _run(c, bs, _ctx(T0 + 1, [oa, ob]))
    assert r[0] == "entry" and bs["conductor"].pos["src"] == "B" and bs["conductor"].pos["rr"] == "PE"
    _close(bs["A"], T0 + 20, 90.0, "STOP")
    _fire(bs["A"], _ctx(T0 + 40, [oa]), oa)                       # A fires again while the account is B's
    assert _run(c, bs, _ctx(T0 + 40, [oa, ob])) is None
    bs["A"].ctl.pop("pending_entry")
    _close(bs["B"], T0 + 90, 130.0, "TRAIL")
    r = _run(c, bs, _ctx(T0 + 90, [oa, ob]))
    assert r[0] == "exit" and r[1]["pnl_rs"] > 0 and bs["conductor"].pos is None
    # a lapsed owner releases the account
    _fire(bs["A"], _ctx(T0 + 200, [oa]), oa)
    assert _run(c, bs, _ctx(T0 + 200, [oa]))[0] == "owner"
    pos, why = paper.try_fill_entry(bs["A"], _ctx(T0 + 200 + config.ENTRY_FILL_MAX_S + 1, [dict(oa, age=99.0)]))
    assert pos is None and "lapsed" in why
    assert _run(c, bs, _ctx(T0 + 200 + config.ENTRY_FILL_MAX_S + 1, [oa])) is None and "owner" not in bs["conductor"].ctl
    ev = [json.loads(x)["event"] for x in open(tmp_path / f"conductor_{DAY}.jsonl", encoding="utf-8")]
    assert "lost_priority" in ev and "occupied" in ev and "release" in ev


def test_rules_on_the_trigger_photograph(tmp_path):
    reg = {"R-900": {"id": "R-900", "factor": "er60", "op": ">=", "line": 0.4},
           "R-901": {"id": "R-901", "factor": "regime=TREND", "op": ">=", "line": 0.5}}
    assert rules.generic(reg["R-900"], {"er60": 0.5}) is None
    assert "needs >= 0.4" in rules.generic(reg["R-900"], {"er60": 0.3})
    assert "unknown" in rules.generic(reg["R-900"], {})                     # a missing value blocks
    assert rules.generic(reg["R-901"], {"regime": "TREND"}) is None and rules.generic(reg["R-901"], {"regime": "RANGE"})
    assert rules.check_rule("R-999", {}, None, "X", reg)                     # unknown rule id: never trades
    assert rules.check_rule("R-002", {"expiry_day": False, "mins_open": 120, "er60": 0.5, "dir60": 1},
                            {"now_dt": datetime(2026, 11, 9, 11, 0, tzinfo=config.IST)}, "SPOT-RETEST", reg) is None
    # in the Conductor: the pool pair's rule is checked on the pending entry's photo; blocked -> logged, not taken
    bs = _books("A")
    c = cond.Conductor(DAY, list(bs), pool=_pool(_e("A", rule="R-002")), log_dir=str(tmp_path))
    o = _opt(ltp=100.0)
    _fire(bs["A"], _ctx(T0, [o]), o, w={"v": 3, "er60": 0.1, "dir60": 1, "expiry_day": False, "mins_open": 75})
    bs["A"].ctl["ep_type"] = "SPOT-RETEST"
    assert _run(c, bs, _ctx(T0, [o])) is None and "owner" not in bs["conductor"].ctl
    rows = [json.loads(x) for x in open(tmp_path / f"conductor_{DAY}.jsonl", encoding="utf-8")]
    assert any(r["event"] == "rule_block" and "R-002" in r["why"] for r in rows)


def test_pool_as_of_day_and_problems():
    pool = _pool(_e("spot_dc12_t12", frm="2026-11-09"), _e("c20_9x", rule="R-004", frm="2026-11-01"))
    assert [e["book"] for e in cond.active_entries(pool, "2026-11-06", asof="")] == ["c20_9x"]
    assert len(cond.active_entries(pool, "2026-11-06", asof="all")) == 2
    assert len(cond.active_entries(pool, "2026-11-09", asof="")) == 2
    assert cond.pool_problems(pool) == []
    bad = _pool(_e("nope"), _e("c20_9x", rule="R-999"), _e("random_entry"), dict(_e("c20_9x"), standing="x", **{"from": 3}))
    probs = cond.pool_problems(bad)
    assert len(probs) == 5 and config.validate() == []


def _day_books(bs):
    return {n: b.to_json() for n, b in bs.items()}


def test_offline_simulator_agrees_with_the_engine_path(tmp_path):
    bs = _books("A", "B")
    pool = _pool(_e("A", standing="low", rpt=1.0), _e("B", standing="full", rpt=1.0))
    c = cond.Conductor(DAY, list(bs), pool=pool, log_dir=str(tmp_path))
    oa, ob = _opt(24000, ltp=100.0), _opt(23900, "PE", ltp=120.0)
    # 1. A fires alone, fills, wins; 2. A and B fire on the same tick: B (full) takes it, A's trade is skipped;
    # 3. B fires while A... (A is flat) B loses; 4. A fires while the account holds B: occupied
    def step(t, opts):
        _run(c, bs, _ctx(t, opts))
    _fire(bs["A"], _ctx(T0, [oa]), oa); step(T0, [oa])
    _fill(bs["A"], T0 + 1, oa); step(T0 + 1, [oa])
    _close(bs["A"], T0 + 100, 110.0, "TRAIL"); step(T0 + 100, [oa])
    t1 = T0 + 300
    _fire(bs["A"], _ctx(t1, [oa, ob]), oa); _fire(bs["B"], _ctx(t1, [oa, ob]), ob); step(t1, [oa, ob])
    _fill(bs["A"], t1 + 1, oa); _fill(bs["B"], t1 + 1, ob); step(t1 + 1, [oa, ob])
    _close(bs["A"], t1 + 50, 120.0, "TRAIL"); step(t1 + 50, [oa, ob])
    t2 = t1 + 200
    _fire(bs["A"], _ctx(t2, [oa, ob]), oa); step(t2, [oa, ob])              # occupied by B
    _fill(bs["A"], t2 + 1, oa); step(t2 + 1, [oa, ob])
    _close(bs["B"], t2 + 100, 110.0, "STOP"); step(t2 + 100, [oa, ob])
    _close(bs["A"], t2 + 150, 105.0, "TRAIL"); step(t2 + 150, [oa, ob])
    cb = bs["conductor"]
    assert [t["src"] for t in cb.trades] == ["A", "B"]
    sim = account_sim.simulate({DAY: _day_books(bs)}, pool, "")[DAY]
    assert [(t["src"], t["entry"], t["exit"], t["pnl_rs"]) for t in sim["trades"]] == \
           [(t["src"], t["entry"], t["exit"], t["pnl_rs"]) for t in cb.trades]
    assert sim["capital_end"] == cb.capital and sim["counts"]["lost_priority"] == 1 and sim["counts"]["occupied"] == 1
    md = account_sim.report({DAY: sim}, {DAY: _day_books(bs)}, vs="A")
    assert "| 2026-11-06 | 2 | 2 |" in md


def test_owner_survives_a_restart_and_the_photo_checks():
    b = paper.Book("conductor", config.VARIANTS["conductor"], DAY)
    b.ctl["owner"] = {"book": "A", "t": T0, "key": "k"}
    assert paper.Book.from_json(json.loads(json.dumps(b.to_json()))).ctl["owner"]["book"] == "A"
    assert weather.static_check() == []
    probs, warns = weather.check_photo({"v": 3, "er60": 0.1})
    assert any("fields" in p for p in probs) and len(warns) > 60
    probs, _w = weather.check_photo({"v": 2, "v3_error": "x", **{f"f{i}": 1 for i in range(250)}})
    assert any("version" in p for p in probs) and any("v3_error" in p for p in probs)


def test_release_admits_a_competing_trigger_on_the_same_step(tmp_path):
    """docs/34 F01: when the owner's entry lapses, the account is flat again on THAT step, so another pool book's
    trigger on the same step is admitted (it would otherwise be lost: _fired only sees this step's triggers)."""
    bs = _books("A", "B")
    c = cond.Conductor(DAY, list(bs), pool=_pool(_e("A", rpt=5.0), _e("B", rpt=1.0)), log_dir=str(tmp_path))
    oa, ob = _opt(24000, ltp=100.0), _opt(23900, "PE", ltp=120.0)
    _fire(bs["A"], _ctx(T0, [oa]), oa)
    assert _run(c, bs, _ctx(T0, [oa]))[1]["book"] == "A"
    t1 = T0 + config.ENTRY_FILL_MAX_S + 1
    pos, why = paper.try_fill_entry(bs["A"], _ctx(t1, [dict(oa, age=99.0)]))
    assert pos is None and "lapsed" in why
    _fire(bs["B"], _ctx(t1, [ob]), ob)                              # B fires on the very step A lapses
    r = _run(c, bs, _ctx(t1, [oa, ob]))
    assert r is not None and r[0] == "owner" and r[1]["book"] == "B" and bs["conductor"].ctl["owner"]["book"] == "B"
    _fill(bs["B"], t1 + 1, ob)
    r = _run(c, bs, _ctx(t1 + 1, [ob]))
    assert r[0] == "entry" and bs["conductor"].pos["src"] == "B"
    ev = [json.loads(x) for x in open(tmp_path / f"conductor_{DAY}.jsonl", encoding="utf-8")]
    kinds = [x["event"] for x in ev if x["event"] != "flat"]
    assert kinds == ["owner", "release", "owner", "entry"] and "pending" not in kinds
    # still-pending owner: a competing trigger is logged pending and NOT admitted
    bs2 = _books("A", "B")
    c2 = cond.Conductor(DAY, list(bs2), pool=_pool(_e("A", rpt=5.0), _e("B", rpt=1.0)), log_dir=str(tmp_path / "2"))
    os.makedirs(tmp_path / "2", exist_ok=True)
    _fire(bs2["A"], _ctx(T0, [oa]), oa)
    _run(c2, bs2, _ctx(T0, [oa]))
    _fire(bs2["B"], _ctx(T0 + 1, [ob]), ob)
    assert _run(c2, bs2, _ctx(T0 + 1, [oa, ob])) is None and bs2["conductor"].ctl["owner"]["book"] == "A"


def test_pool_rows_have_an_end_date_and_one_state_per_pair():
    """docs/34 F03: `to` retires a row (inclusive); the latest `from` of a pair is its state as of the day."""
    pool = _pool(dict(_e("spot_dc12_t12", frm="2026-11-01", rpt=1.0), to="2026-11-05"),
                 _e("c20_9x", rule="R-004", frm="2026-11-01", standing="low", rpt=2.0),
                 _e("c20_9x", rule="R-004", frm="2026-11-09", standing="full", rpt=3.0))
    a = cond.active_entries(pool, "2026-11-05", asof="")
    assert [(e["book"], e.get("standing")) for e in a] == [("spot_dc12_t12", "low"), ("c20_9x", "low")]
    a = cond.active_entries(pool, "2026-11-06", asof="")
    assert [(e["book"], e.get("standing")) for e in a] == [("c20_9x", "low")]
    a = cond.active_entries(pool, "2026-11-09", asof="")
    assert [(e["book"], e.get("standing"), e["ret_per_trade"]) for e in a] == [("c20_9x", "full", 3.0)]
    assert len(cond.active_entries(pool, "2026-11-01", asof="all")) == 2            # latest row per pair, in-sample
    assert cond.pool_problems(pool) == []
    bad = _pool(dict(_e("c20_9x", frm="2026-11-09"), to="2026-11-01"))
    assert any("'to'" in p for p in cond.pool_problems(bad))


def test_an_expired_latest_row_retires_the_pair_and_never_revives_an_older_row():
    """docs/34 F03 follow-up (ChatGPT, 8 Nov): low from 9 Nov open-ended; full from 10 through 11 Nov; on 12 Nov the
    pair is RETIRED, not back to the low row."""
    pool = _pool(_e("c20_9x", rule="R-004", frm="2026-11-09", standing="low"),
                 dict(_e("c20_9x", rule="R-004", frm="2026-11-10", standing="full"), to="2026-11-11"))
    assert [e["standing"] for e in cond.active_entries(pool, "2026-11-09", asof="")] == ["low"]
    assert [e["standing"] for e in cond.active_entries(pool, "2026-11-11", asof="")] == ["full"]
    assert cond.active_entries(pool, "2026-11-12", asof="") == []
    assert [e["standing"] for e in cond.active_entries(pool, "2026-11-12", asof="all")] == ["full"]


def test_missing_source_is_an_integrity_fault_then_a_flagged_recovery_exit(tmp_path):
    """docs/34 F04: the owner's position vanishes with no closed trade. No exit at a remembered price: the account
    stays open and unresolved until a fresh quote on its contract exists, then leaves as an adjustment that scoring
    ignores."""
    from apex.conductor import score
    bs = _books("A")
    c = cond.Conductor(DAY, list(bs), pool=_pool(_e("A")), log_dir=str(tmp_path))
    o = _opt(ltp=100.0)
    _fire(bs["A"], _ctx(T0, [o]), o)
    _run(c, bs, _ctx(T0, [o]))
    _fill(bs["A"], T0 + 1, o)
    _run(c, bs, _ctx(T0 + 1, [o]))
    cb = bs["conductor"]
    assert cb.pos and cb.pos["src"] == "A"
    cb.pos["last"] = 130.0                                            # a remembered price that must NOT be used
    bs["A"].pos = None                                                # the source book lost its position (restart, removal)
    assert _run(c, bs, _ctx(T0 + 60, [dict(o, ltp=90.0, age=40.0)])) is None   # stale quote: stays open, unresolved
    assert cb.pos and cb.pos.get("unresolved") == T0 + 60 and "UNRESOLVED" in c.reason
    assert _run(c, bs, _ctx(T0 + 61, [])) is None and cb.pos                  # no quote at all: still open
    r = _run(c, bs, _ctx(T0 + 62, [dict(o, ltp=95.0, age=0.3)]))             # fresh quote: recovery exit at IT
    assert r[0] == "exit" and cb.pos is None and len(cb.trades) == 1
    t = cb.trades[0]
    assert t["exit"] == 95.0 and t["adjustment"] == "recovery" and "RECOVERY" in t["reason"]
    assert cb.capital == config.START_CAPITAL + t["pnl_rs"] and t["pnl_rs"] < 0
    ev = [json.loads(x)["event"] for x in open(tmp_path / f"conductor_{DAY}.jsonl", encoding="utf-8")]
    assert ev.count("integrity") == 1 and "adjustment" in ev and ev.index("integrity") < ev.index("adjustment")
    q = type("Q", (), {"reason": lambda self, d, t: None})()
    assert score._ok_trades(cb.trades, DAY, q, lambda t: False) == []       # an adjustment is not scored


@pytest.mark.owner_champion
def test_the_engine_runs_with_the_conductor_as_the_owners_champion():
    """9 Nov (owner: "Yes, apply pool"): config names the Conductor as champion and the pool file holds the c20 family
    unrestricted. A fresh engine takes the Conductor as champion, loads that pool, and the champion's account mirrors
    a pool book's fill and exit through the engine's own step (events, books saved, dashboard view)."""
    import test_wp2 as W
    assert config.CHAMPION_OWNER == ("conductor", "2026-11-09")
    assert [e["book"] for e in cond.active_entries(cond.load_pool(), "2026-11-09")] == ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
    assert not cond.pool_problems(cond.load_pool()) and not config.validate()
    rig = W.Rig("cchamp", "2026-11-09")
    shipped, config.FILL_NEXT_PRINT = config.FILL_NEXT_PRINT, True      # as shipped (test_wp2 switches it off at import)
    try:
        eng = rig.eng
        rig.warm()
        assert eng.champion == "conductor" and "RAW" in eng.books
        assert [m["book"] for m in eng.conductor.members] == ["c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t"]
        eng.conductor.members = [_e("spot_dc12_t12", frm="2026-11-09")]      # a book this rig can trade
        src, cb = eng.books["spot_dc12_t12"], eng.books["conductor"]
        o = eng.ctx["by_key"][f"NIFTY|OPT|{W.EXP}|25200|CE"]
        _fire(src, eng.ctx, o)
        assert eng._conductor_step(eng.ctx)                  # in the engine a book fires inside the step, and the Conductor runs right after it
        assert cb.ctl["owner"]["book"] == "spot_dc12_t12"
        rig.step(25210.0, 30)
        assert src.pos is not None or src.trades, "the source book never filled"
        assert (cb.pos or cb.trades[-1])["src"] == "spot_dc12_t12"
        if src.pos is not None:
            paper.close_trade(src, eng.ctx, src.pos["entry"] + 5.0, "TEST EXIT", eng.ctx["by_key"][src.pos["key"]])
        rig.step(25210.0, 5)
        assert cb.pos is None and len(cb.trades) == 1 and cb.trades[0]["src"] == "spot_dc12_t12"
        assert cb.trades[0]["pnl_rs"] == round(cb.trades[0]["pnl_pts"] * cb.trades[0]["qty"], 2)
        v = eng._conductor_view()
        assert v and len(v["members"]) == 1
    finally:
        config.FILL_NEXT_PRINT = shipped
        rig.close()
