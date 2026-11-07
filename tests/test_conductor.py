"""Stage 3 (docs/28 §4-§6): diaries and loss labels, the family search with its luck check, the rule register code."""
import json
import os
import random
import shutil
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex.conductor import diary, register, search  # noqa: E402


def _t(time_in, ret, peak, reason="TRAIL", rr="CE", ep="SPOT-PULLBACK", why="SPOT pb", dte=3, w=None, **kw):
    t = {"time_in": time_in, "time_out": kw.pop("time_out", time_in[:3] + "59:00"), "ret_pct": ret,
         "pnl_pts": ret, "pnl_rs": ret * 100, "peak_pts": peak, "reason": reason, "rr": rr, "ep_type": ep, "why": why,
         "dte_in": dte, "hold_s": 300, "phase_in": "CTS", "trade_age_in": 1.0, "trade_age_out": 1.0,
         "weather_trig": w or {"expiry_day": dte == 0}}
    t.update(kw)
    return t


def test_diary_rows_labels_and_families():
    books = {"2026-11-09": {
        "spot_pb45": {"trades": [_t("10:00:00", 5.0, 30.0), _t("10:30:00", 3.0, 18.0),
                                 _t("11:00:00", -2.0, 4.0, reason="STOP"),          # never got going
                                 _t("11:30:00", -1.0, 25.0),                        # reached the line, gave it back
                                 _t("15:20:00", 9.0, 40.0, phase_in="CAS-ENTRY")]}, # closing auction: excluded
        "c20_9x": {"trades": [_t("10:05:00", 2.0, 10.0, ep="COUNCIL", why="COUNCIL NORM pb v=+12"),
                              _t("10:40:00", 1.0, 9.0, ep="COUNCIL", why="COUNCIL EXP brk v=+20", dte=0)]},
        "t28_fwd": {"trades": [_t("12:00:00", 1.0, 5.0)]},
        "random_entry": {"trades": [_t("12:30:00", -3.0, 1.0, ep="RANDOM")]}}}
    missed = {"2026-11-09": [
        {"book": "spot_pb45", "episode_id": "spot_pb45#1", "side": "PE", "relation": "opposite", "ep_type": "SPOT-PULLBACK",
         "cf_why": "SPOT pb", "real_time_in": "10:00:00", "cf_time_in": "10:20:00", "cf_time_out": "10:40:00",
         "cf_status": "closed", "cf_ret_pct": 4.0, "cf_peak_pts": 12.0, "cf_hold_s": 1200, "weather": {"expiry_day": False}},
        {"book": "spot_pb45", "episode_id": "spot_pb45#2", "side": "CE", "relation": "same", "ep_type": "SPOT-PULLBACK",
         "real_time_in": "10:00:00", "cf_status": "lapsed", "weather": {"expiry_day": False}}]}
    rows = diary.build(books, missed)
    pb = [r for r in rows if r["book"] == "spot_pb45" and not r["is_counterfactual"]]
    assert [r["win"] for r in pb] == [True, True, False, False, True]
    # family median winning peak = median(30, 18) = 24 (the excluded 40 is not used) -> line max(8, stop 2) = 8
    assert pb[2]["loss_kind"] == "never_worked" and pb[3]["loss_kind"] == "gave_back" and pb[2]["never_line"] == 8.0
    assert pb[4]["excluded"] == "closing auction"
    fams = {(r["book"], diary.family(r)) for r in rows if not r["is_counterfactual"]}
    assert ("c20_9x", "COUNCIL-NORM|NORM") in fams and ("c20_9x", "COUNCIL-EXP|EXP") in fams
    assert ("t28_fwd", "FWD-PULLBACK|NORM") in fams
    assert next(r for r in rows if r["book"] == "random_entry")["control"] is True
    cf = [r for r in rows if r["is_counterfactual"]]
    assert cf[0]["weight"] == 0.5 and cf[0]["excluded"] is None        # entered 10:20; the real trade left 10:59
    assert cf[1]["excluded"] == "counterfactual lapsed"


def test_counterfactual_overlap_weight():
    books = {"2026-11-09": {"b": {"trades": [_t("10:00:00", 1.0, 5.0, time_out="10:10:00")]}}}
    mk = lambda tin: {"book": "b", "episode_id": "b#" + tin, "side": "CE", "real_time_in": "10:00:00",
                      "cf_time_in": tin, "cf_time_out": "10:30:00", "cf_status": "closed", "cf_ret_pct": 1.0,
                      "cf_peak_pts": 3.0, "weather": {}}
    rows = diary.build(books, {"2026-11-09": [mk("10:05:00"), mk("10:12:00")]})
    w = [r["weight"] for r in rows if r["is_counterfactual"]]
    assert w == [0.5, 1.0]                     # overlapping the real trade: half; after it closed: full


def _rows(n_days=20, per_day=20, signal=True, seed=3):
    rng = random.Random(seed)
    rows = []
    for d in range(n_days):
        day = f"2026-11-{d + 1:02d}"
        for k in range(per_day):
            b = rng.random()
            noise = rng.random()
            p = (0.8 if b >= 0.6 else 0.25) if signal else 0.5
            win = rng.random() < p
            ret = (rng.uniform(1, 8) if win else -rng.uniform(1, 5))
            rows.append({"day": day, "book": "spot_pb45", "pattern": "SPOT-PULLBACK", "day_type": "NORM",
                         "is_counterfactual": False, "weight": 1.0, "control": False, "excluded": None,
                         "ret_pct": ret, "win": win, "weather": {"breadth_dir": b, "noise": noise,
                                                                 "phase": "CTS" if k % 2 else "X"}})
    return rows


def test_search_finds_a_planted_condition_and_beats_luck():
    res = search.search(_rows(), perms=60)
    c = res["cards"]["SPOT-PULLBACK|NORM"]
    assert c["representative"] == "spot_pb45" and not c["representative_fallback"]
    found = [(r["factor"], r["op"]) for r in c["card"]]
    assert ("breadth_dir", ">=") in found
    assert all(r["factor"] != "noise" for r in c["card"])
    top = next(r for r in c["card"] if r["factor"] == "breadth_dir")
    assert 0.4 <= top["line"] <= 0.75 and top["kept_sr"] > top["other_sr"] and top["found_by"] == "searching the past"
    assert "breadth_dir >=" in search.card_markdown(res)


def test_search_on_pure_noise_puts_nothing_on_the_card():
    res = search.search(_rows(signal=False), perms=60)
    assert res["cards"]["SPOT-PULLBACK|NORM"]["card"] == []


def test_search_skips_controls_and_small_families():
    rows = _rows(n_days=2, per_day=5)
    for r in rows[:3]:
        r["control"] = True
    res = search.search(rows, perms=10)
    c = res["cards"]["SPOT-PULLBACK|NORM"]
    assert c.get("skipped") and c["n_rows"] == 7


@pytest.fixture
def reg_paths(tmp_path):
    src = register.REGISTER
    p = tmp_path / "register.json"
    shutil.copy(src, p)
    return str(p), str(tmp_path / "status.jsonl")


def test_register_propose_add_and_near_duplicates(reg_paths):
    path, st_path = reg_paths
    reg = register.load(path)
    n0 = len(reg["rules"])
    r = register.propose(reg, "SPOT-PULLBACK|NORM", "breadth_dir", ">=", 0.6, "spot_pb45+R", "spot_pb45",
                         "card 9 Nov", today=date(2026, 11, 7), st={})
    assert r["id"] == f"R-{n0 + 1:03d}" and r["frozen"] == "2026-11-07" and r["first_test_day"] == "2026-11-09"
    register.add(r, path)
    reg = register.load(path)
    assert len(reg["rules"]) == n0 + 1
    with pytest.raises(ValueError, match="already registered"):
        register.propose(reg, "SPOT-PULLBACK|NORM", "breadth_dir", ">=", 0.6, "x", "y", "dup", st={})
    # it fails: the next day's "breadth >= 0.58" is the same idea and is refused; 0.45 is a different line
    register.record_status(r["id"], "failed", "2026-12-18", "second window", path=st_path, reg=reg)
    st = register.statuses(st_path)
    day = date(2026, 12, 21)
    with pytest.raises(ValueError, match="near-duplicate"):          # within 20 % of the factor's range (0..1)
        register.propose(reg, "SPOT-PULLBACK|NORM", "breadth_dir", ">=", 0.58, "x", "y", "again", today=day, st=st,
                         factor_range=1.0)
    with pytest.raises(ValueError, match="near-duplicate"):          # the other direction is the same idea too
        register.propose(reg, "SPOT-PULLBACK|NORM", "breadth_dir", "<", 0.5, "x", "y", "flip", today=day, st=st,
                         factor_range=1.0)
    ok = register.propose(reg, "SPOT-PULLBACK|NORM", "breadth_dir", ">=", 0.35, "x", "y", "wider", today=day, st=st,
                          factor_range=1.0)
    assert ok["line"] == 0.35
    later = register.propose(reg, "SPOT-PULLBACK|NORM", "breadth_dir", ">=", 0.58, "x", "y", "after the block",
                             today=date(2027, 1, 20), st=st, factor_range=1.0)   # 20+ trading days on: allowed
    assert later["line"] == 0.58
    assert register.test_days(r, ["2026-11-06", "2026-11-09", "2026-11-10"]) == ["2026-11-09", "2026-11-10"]
    assert "rules under test" in register.luck_line(reg, st)
    with pytest.raises(ValueError):
        register.record_status(r["id"], "maybe", "2026-12-20", path=st_path, reg=reg)


def test_register_add_never_changes_an_existing_rule(reg_paths):
    path, _ = reg_paths
    before = json.load(open(path, encoding="utf-8"))["rules"]
    reg = register.load(path)
    register.add(register.propose(reg, "ORB|NORM", "er60", ">=", 0.35, "a", "b", "t", st={}), path)
    after = json.load(open(path, encoding="utf-8"))["rules"]
    assert after[:len(before)] == before
