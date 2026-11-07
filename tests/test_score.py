"""The rule score (docs/28 §2, §6): windows, the seven tests, verdicts, the e-value watch. Synthetic books only."""
import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.conductor import score  # noqa: E402


def _days(start, n):
    d, out = date.fromisoformat(start), []
    while len(out) < n:
        if config.is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _tr(day, k, ret, rr="CE"):
    t0 = 1.8e9 + hash(day) % 10 ** 6 + 600 * k
    return {"time_in": f"{10 + k // 6:02d}:{(k % 6) * 10:02d}:00", "t_in": t0, "ret_pct": ret, "pnl_rs": ret * 1000,
            "rr": rr, "phase_in": "CTS", "trade_age_in": 1.0, "trade_age_out": 1.0}


def _books(days, good=True, seed=5, per_day=4):
    """Free book: per_day trades a day, half winners. Restricted: the winners plus (if not good) the losers too, and
    (if good) skips most losers."""
    rng = random.Random(seed)
    books = {}
    for d in days:
        free, res = [], []
        for k in range(per_day):
            win = rng.random() < 0.5
            ret = rng.uniform(3, 9) if win else -rng.uniform(2, 6)
            t = _tr(d, k, ret)
            free.append(t)
            if good and (win or rng.random() < 0.15):
                res.append(dict(t))
            if not good and (not win or rng.random() < 0.3):
                res.append(dict(t))
        books[d] = {"free": {"trades": free}, "restricted": {"trades": res}}
    return books


RULE = {"id": "R-T", "name": "test rule", "kind": "entry", "restricted_book": "restricted", "free_book": "free",
        "first_test_day": "2026-11-09"}


def test_windows_take_whichever_comes_later():
    days = _days("2026-11-09", 40)
    ev = {d: ([1] * (1 if i < 20 else 3), []) for i, d in enumerate(days)}     # 1 trade a day for 20 days, then 3
    ws = score.windows(list(ev), ev, "2026-11-09")
    (w1, c1), (w2, c2) = ws
    n1 = sum(len(ev[d][0]) for d in w1)
    assert c1 and n1 >= 30 and len(w1) >= 15 and len(w1) == 24            # 20 x 1 + 4 x 3 = 32 trades on day 24
    assert c2 and len(w2) == 15                                             # 15 days x 3 = 45 >= 30: the days decide
    short = score.windows(days[:10], {d: ([1] * 5, []) for d in days[:10]}, "2026-11-09")
    assert short[0][1] is False and len(short) == 1                         # 50 trades but only 10 days: not complete


def test_a_good_rule_passes_its_first_window_and_a_bad_one_fails():
    days = _days("2026-11-09", 22)
    good = score.score_rule(RULE, _books(days, good=True), perms=400)
    w1 = good["windows"][0]
    assert w1["complete"] and w1["passed"], w1["tests"]
    assert good["verdict"] == "passed_first_window" and "watch" in good
    bad = score.score_rule(RULE, _books(days, good=False), perms=400)
    assert bad["verdict"] == "failed" and not bad["windows"][0]["tests"]["1_strike_rate"]["pass"]


def test_only_test_days_count_and_cas_trades_are_not_evidence():
    days = _days("2026-11-02", 30)
    books = _books(days)
    for d in days[:5]:                                                       # before the first test day
        books[d]["restricted"]["trades"] = [_tr(d, 0, -50.0)]
    for d in days:
        books[d]["restricted"]["trades"].append(dict(_tr(d, 9, -80.0), phase_in="CAS-ENTRY"))
    r = score.score_rule(RULE, books, perms=200)
    assert r["test_days"] == len([d for d in days if d >= "2026-11-09"])
    assert r["windows"][0]["passed"], r["windows"][0]["tests"]


def test_big_wins_are_matched_by_side_and_time():
    days = _days("2026-11-09", 16)
    books = _books(days, per_day=4)
    best = max(((d, t) for d in days for t in books[d]["free"]["trades"]), key=lambda x: x[1]["ret_pct"])
    for d in days:                                                            # the restricted book misses every big win
        books[d]["restricted"]["trades"] = [t for t in books[d]["restricted"]["trades"] if t["ret_pct"] < 6]
    r = score.score_rule(RULE, books, perms=200)
    assert not r["windows"][0]["tests"]["5_big_wins"]["pass"]
    assert best[1]["ret_pct"] >= 6


def test_the_watch_switches_a_rule_off():
    days = _days("2026-11-09", 40)
    ev = {d: ([{"ret_pct": -40.0}], [{"ret_pct": 1.0}]) for d in days}
    w = score.watch(ev, days[0])
    assert w["switch_off"] and w["e_switch_off"] >= 20 and w["e_earning"] < 1
    ev2 = {d: ([{"ret_pct": 5.0}], [{"ret_pct": 1.0}]) for d in days}
    assert not score.watch(ev2, days[0])["switch_off"]


def test_family_rules_expand_to_their_restricted_books():
    from apex.conductor import register
    reg = score.expand_family_rules(register.load())
    ids = [r["id"] for r in reg["rules"]]
    assert "R-002/spot_pb45" in ids and "R-005/spot_orb45" in ids and "R-001" in ids
    r = next(x for x in reg["rules"] if x["id"] == "R-004/c20_9x")
    assert r["restricted_book"] == "c20_9x_r004" and r["free_book"] == "c20_9x"
    assert sum(1 for i in ids if i.startswith("R-00") and "/" in i) == 14      # spot_pb45_r003 off 8 Nov
    assert "R-003/spot_pb45" not in ids
