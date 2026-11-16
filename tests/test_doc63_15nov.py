"""15 Nov (owner: "Yes, start"; docs/63, docs/64): the first step of the outside review's plan. No live rule changes.

1. conductor_rt: a shadow account with the live pool and the rent-trail book c20_9t FIRST on a same-tick tie;
2. the opportunity funnel: where the account's day went and what became of every pool trigger, from its own log;
3. with no futures and no index price, a champion-family position still leaves on the rules that need no forward
   (hold clock, premium stop, forced flat) when the held option is quoted; nothing can be bought in that state.
"""
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config, engine_main, greeks  # noqa: E402
from apex.conductor import account_sim as sim, funnel  # noqa: E402
from apex.engine import conductor as cond, learning, paper  # noqa: E402


# ── 1. the rent-trail-first shadow account ──────────────────────────────────────
def test_rent_trail_first_is_a_shadow_account_with_the_live_pool_reordered():
    names = list(config.VARIANTS)
    v = config.VARIANTS["conductor_rt"]
    assert names[-2:] == ["conductor_rt", "lw_c20_9y"] and v.get("shadow_policy") == "rtfirst" and v.get("twin") and config.validate() == []
    live = cond.Conductor("2026-11-16", names, log_dir="")
    rt = cond.AdaptiveConductor("2026-11-16", names, "rtfirst", "conductor_rt", log_dir="")
    pool = [m["book"] for m in live.members]
    assert pool[-1] == "c20_9t" and [m["book"] for m in rt.members] == ["c20_9t"] + pool[:-1]
    assert all(m["standing"] == "low" for m in live.members)                 # the live pool's own rows are not edited
    assert sorted(rt.members, key=lambda e: cond.priority_key(e, rt.order)) == rt.members   # the offline order agrees
    assert rt.admit(rt.members[1], {"key": "NIFTY|OPT|2026-11-17|25000|CE"}, None, {}, {"now_s": 0.0}) is None
    assert cond.offline_admit("rtfirst")(0.0, None, {}, [], {}) is None
    assert "conductor_rt" in learning.SHADOW_ACCOUNTS and cond.FIRST_BOOK == {"rtfirst": "c20_9t"}


def test_on_a_same_tick_tie_the_shadow_copies_the_rent_trail_book_and_the_live_account_does_not():
    t0 = 1794887400.0 - 86400.0                                             # 2026-11-16 09:20 IST

    def tr(t_out, px_out):
        return {"t_in": t0 + 2.0, "trigger_t": t0, "t_out": t_out, "entry": 184.1, "exit": px_out,
                "key": "NIFTY|OPT|2026-11-17|25200|PE", "ret_pct": 100.0 * (px_out / 184.1 - 1.0)}
    names = list(config.VARIANTS)
    books = {n: {"trades": []} for n in names}
    for b in ("c20_9y", "c20_9v", "c20_9x"):
        books[b]["trades"] = [tr(t0 + 2555.0, 170.95)]                       # the forward trail, 42 minutes later
    books["c20_9t"]["trades"] = [tr(t0 + 911.0, 193.30)]                     # the rent trail, 15 minutes later
    pool = cond.load_pool()
    live = sim.simulate({"2026-11-16": books}, pool)["2026-11-16"]
    rt = sim.simulate({"2026-11-16": books}, pool, policy="rtfirst")["2026-11-16"]
    assert [x["src"] for x in live["trades"]] == ["c20_9y"] and live["ret_day_pct"] < 0
    assert [x["src"] for x in rt["trades"]] == ["c20_9t"] and rt["ret_day_pct"] > 0 and rt["pool_n"] == live["pool_n"]


# ── 2. the opportunity funnel ───────────────────────────────────────────────────
def _log(tmp_path, day, rows, account="conductor"):
    y, m, d = (int(x) for x in day.split("-"))
    base = datetime(y, m, d, tzinfo=config.IST).timestamp()
    p = tmp_path / f"{account}_{day}.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        for hhmmss, ev, kw in rows:
            h, mi, s = (int(x) for x in hhmmss.split(":"))
            fh.write(json.dumps(dict({"t": base + h * 3600 + mi * 60 + s, "time": hhmmss, "event": ev}, **kw)) + "\n")
        fh.write("not json\n")                                               # a torn line is skipped
    return str(tmp_path)


def test_the_funnel_says_where_the_day_went_and_what_became_of_each_trigger(tmp_path):
    day = "2026-11-17"
    K = "NIFTY|OPT|2026-11-17|25000|PE"
    rows = [("09:00:00", "flat", {"why": "flat: data blackout"}),
            ("09:20:00", "flat", {"why": "flat: no eligible trigger"}),
            ("10:00:00", "lost_priority", {"book": "c20_9t", "to": "c20_9y", "key": K}),
            ("10:00:00", "owner", {"book": "c20_9y", "key": K}),
            ("10:00:03", "release", {"book": "c20_9y", "key": K, "why": "entry lapsed: no print on 25000 PE within 3 s"}),
            ("10:10:00", "owner", {"book": "c20_9y", "key": K}),
            ("10:10:02", "entry", {"book": "c20_9y", "key": K}),
            ("10:12:00", "occupied", {"book": "c20_9t", "key": K, "by": "c20_9y"}),
            ("10:40:02", "exit", {"book": "c20_9y", "key": K, "ret_pct": 12.5}),
            ("10:40:02", "flat", {"why": "flat: no eligible trigger"}),
            ("11:00:00", "rule_block", {"book": "c20_9y", "key": K, "why": "expiry switch: fade mode today"})]
    pd = _log(tmp_path, day, rows)
    f = funnel.funnel(funnel.read_log(day, "conductor", pd), day)
    s = f["seconds"]
    assert s["flat: data blackout"] == 300.0                                 # 09:15 to 09:20: the session starts at 09:15
    assert s["holding a trade"] == 1800.0 and s["waiting for a fill"] == 5.0
    assert abs(sum(s.values()) - (funnel.CLOSE_S - funnel.OPEN_S)) < 1e-6    # every second of 09:15-15:30 is in one state
    assert funnel.NOT_RUNNING in s and s[funnel.NOT_RUNNING] > 4 * 3600      # the log stops at 11:00: the engine stopped
    assert f["moments"] == 4 and f["events"]["owner"] == 2 and f["events"]["entry"] == 1 and f["events"]["release"] == 1
    assert f["closed"] == 1 and f["winners"] == 1 and f["lapse_why"] == {funnel.LAPSE_QUIET: 1}
    assert f["engine_late"] == 0 and f["lapse_waits"] == [3.0]
    assert f["fired"]["c20_9y"] == 3 and f["fired"]["c20_9t"] == 2 and f["took"] == {"c20_9y": 1}
    out = "\n".join(funnel.lines(day, "conductor", pd))
    assert "| Holding a trade | 30 | 8 % |" in out and "| ... released without a fill | 1 |" in out
    assert "Of 2 triggers the account took, 1 filled (50 %)" in out and "| c20_9y | 3 | 2 | 1 |" in out
    assert "fired no pool book is not counted" in out
    assert funnel.lines("2026-11-18", "conductor", pd)[-1] == "No log for this account on this day."
    assert "engine's own delay" not in out


def test_the_funnel_tells_an_engine_late_lapse_from_a_quiet_option(tmp_path):
    """15 Nov, later (docs/64 section 6): on 9 Nov every lapse read "no print within 3 s" and every one was the engine's
    own 3 to 7 s step. The report must not blame the market for it again."""
    day = "2026-11-17"
    K = "NIFTY|OPT|2026-11-17|25000|PE"
    lapsed = "entry lapsed: no print on 25000 PE within 3 s"
    rows = [("09:20:00", "flat", {"why": "flat: no eligible trigger"}),
            ("10:00:00", "owner", {"book": "c20_9y", "key": K}),
            ("10:00:03", "release", {"book": "c20_9y", "key": K, "why": lapsed}),                  # a quiet option
            ("10:05:00", "owner", {"book": "c20_9y", "key": K}),
            ("10:05:06", "release", {"book": "c20_9y", "key": K, "why": lapsed}),                  # released 3 s too late
            ("10:10:00", "owner", {"book": "c20_9y", "key": K}),
            ("10:10:03", "release", {"book": "c20_9y", "key": K, "why": lapsed + " [engine stalled 2.4 s]"}),   # tagged
            ("10:15:00", "owner", {"book": "c20_9y", "key": K}),
            ("10:15:01", "release", {"book": "c20_9y", "key": K, "why": "entry lapsed: data gap"}),
            ("10:20:00", "owner", {"book": "c20_9y", "key": K}),
            ("10:20:09", "release", {"book": "c20_9y", "key": K, "why": "premium unaffordable"}),
            ("15:29:00", "flat", {"why": "flat: no eligible trigger"})]
    pd = _log(tmp_path, day, rows)
    f = funnel.funnel(funnel.read_log(day, "conductor", pd), day)
    assert f["lapse_why"] == {funnel.LAPSE_QUIET: 1, funnel.LAPSE_LATE: 2, funnel.LAPSE_GAP: 1, "premium unaffordable": 1}
    assert f["engine_late"] == 2 and f["lapse_waits"] == [3.0, 3.0, 6.0]      # the gap and the rejection are not waits
    assert funnel.lapse_kind(lapsed, None) == funnel.LAPSE_QUIET                # no trigger time known: as written
    assert funnel.lapse_kind(lapsed, 3.0 + funnel.LATE_S) == funnel.LAPSE_QUIET and funnel.lapse_kind(None, 9.0) == "released"
    out = "\n".join(funnel.lines(day, "conductor", pd))
    assert "**2 of these were lost to the engine's own delay, not to the market.**" in out
    assert "let go 3.0 to 6.0 s after the trigger" in out and "tick-time lines" in out


# ── 3. exits that need no underlying price ──────────────────────────────────────
def _engine(tag, day="2026-10-21"):
    from tests import test_wp2
    rig = test_wp2.Rig(tag, day)
    rig.warm()
    live = engine_main.Engine(rig.t, rig.blob, "live")
    live.load_registry()
    rig.eng = live
    return rig, live, test_wp2.EXP


def _options_only(rig, exp, F=25210.0, scale=1.0):
    """the feed has restarted: the futures and index rows are empty; the options still quote."""
    r = rig.t.rows
    ns = int(rig.now * 1e9)
    rig.t.set("now_ns", ns)
    for i in (rig.fut, rig.spot):
        for f in ("ltp", "bid", "ask"):
            r[f][i] = 0.0
        r["recv_ns"][i] = 0
    T = greeks.years_to_expiry(exp, datetime.fromtimestamp(rig.now, config.IST))
    for (k, rr), i in rig.opt.items():
        px = scale * float(greeks.b76_price(F, np.array([float(k)]), T, 0.13, np.array([rr == "CE"]))[0])
        r["ltp"][i] = px; r["bid"][i] = px - 0.05; r["ask"][i] = px + 0.05
        r["recv_ns"][i] = ns; r["ltt"][i] = rig.now - 2.0


def _hold(rig, live, exp, age_s, entry_scale=1.0):
    k = 25200
    px = float(rig.t.rows["ltp"][rig.opt[(k, "CE")]])
    pos = {"key": f"NIFTY|OPT|{exp}|{k}|CE", "rr": "CE", "strike": float(k), "expiry": exp, "entry": px * entry_scale,
           "qty": 65, "lots": 1, "slices": 1, "t_in": rig.now - age_s, "time_in": "10:00:00", "dir": 1, "why": "test",
           "id": rig.opt[(k, "CE")]}
    live.books["c20_9y"].pos = dict(pos)
    live.books["conductor"].pos = dict(pos, src="c20_9y")
    return px


def test_with_no_underlying_price_a_champion_position_still_leaves_on_its_hold_clock(monkeypatch):
    rig, live, exp = _engine("d63a")
    lines = []
    monkeypatch.setattr(engine_main, "log", lines.append)
    try:
        rig.now += 0.1; rig.write(25210.0)
        assert live.tick_nopublish()
        rig.now += 6000.0; rig.write(25210.0)                              # 11:40: a position can now be 92 minutes old
        assert live.tick_nopublish()
        px = _hold(rig, live, exp, age_s=5500.0)                           # past the 5,400-second clock of a normal day
        b, cb = live.books["c20_9y"], live.books["conductor"]
        ran = {"n": 0}
        real = live.run_books
        live.run_books = lambda ctx: (ran.__setitem__("n", ran["n"] + 1), real(ctx))[1]
        rig.now += 1.0
        _options_only(rig, exp)
        live.step()
        assert ran["n"] == 0 and live.guard.on                             # the normal step did not run; blackout
        assert b.pos is None and b.trades and b.trades[-1]["reason"].startswith("COUNCIL TIME"), (b.pos, b.blocked)
        assert abs(b.trades[-1]["exit"] - px) < 1.0 and not b.trades[-1].get("stale_exit")   # a fresh option quote
        assert cb.pos is None and cb.trades[-1]["exit"] == b.trades[-1]["exit"]             # the account followed
        assert not any(x.pos for n, x in live.books.items() if n not in ("c20_9y", "conductor"))   # and nothing was bought
        assert any("no futures and no index price" in x and "hold clock" in x for x in lines)
    finally:
        rig.close()


def test_with_no_underlying_price_the_premium_stop_still_works_and_is_tagged_stale(monkeypatch):
    rig, live, exp = _engine("d63b")
    monkeypatch.setattr(engine_main, "log", lambda m: None)
    try:
        rig.now += 0.1; rig.write(25210.0)
        assert live.tick_nopublish()
        rig.now += 600.0; rig.write(25210.0)
        assert live.tick_nopublish()
        _hold(rig, live, exp, age_s=300.0)
        b, cb = live.books["c20_9y"], live.books["conductor"]
        for _ in range(3):                                                 # the option holds its price: no exit
            rig.now += 1.0
            _options_only(rig, exp)
            live.step()
        assert b.pos is not None and cb.pos is not None and not b.pos.get("pending")
        for _ in range(14):                                                # the premium falls 30 %: the stop, then the fill
            rig.now += 1.0
            _options_only(rig, exp, scale=0.70)
            live.step()
            if b.pos is None:
                break
        t = b.trades[-1]
        assert b.pos is None and t["reason"] == "COUNCIL SL" and t["stale_exit"] is True    # a blackout fill says so
        assert t["exit"] < 0.75 * t["entry"] and cb.pos is None and cb.trades[-1]["stale_exit"] is True
    finally:
        rig.close()


def test_the_risk_step_does_nothing_outside_a_blackout_and_nothing_when_no_position_is_held():
    rig, live, exp = _engine("d63c")
    try:
        rig.now += 0.1; rig.write(25210.0)
        assert live.tick_nopublish()
        snap = rig.t.snapshot()
        _hold(rig, live, exp, age_s=5500.0)
        live.guard.on = False
        assert live._risk_step(rig.now, snap) is False and live.books["c20_9y"].pos is not None   # never outside a blackout
        live.books["c20_9y"].pos = live.books["conductor"].pos = None
        live.guard.on = True
        assert live._risk_step(rig.now, snap) is False                                      # nobody holds anything
    finally:
        rig.close()


# ── 4. a late look keeps the entry (owner: "Yes, change it"; docs/64 section 6.6) ─
LW_OPT = {"id": 7, "key": "NIFTY|OPT|2026-11-17|25000|PE", "strike": 25000, "rr": "PE", "expiry": "2026-11-17",
          "ltp": 104.0, "bid": 103.9, "ask": 104.1, "delta": -0.55, "iv": 14.0, "age": 0.1, "week": 0, "ltt": None}
EXP_DT = datetime(2026, 11, 17, 13, 11, 33, tzinfo=config.IST)                # the option's own expiry day
NORM_DT = datetime(2026, 11, 16, 13, 11, 33, tzinfo=config.IST)               # the day before


def _fill_ctx(now_s, now_dt, q, **kw):
    c = {"now_s": now_s, "now_dt": now_dt, "w0": q["expiry"], "spot": 25000.0, "spot_hi": 25050.0, "spot_lo": 24950.0,
         "fut": 25010.0, "fut_mid": 25010.0, "fut_ltp": 25010.0, "advisors": {}, "blackout": {"on": False},
         "domino": {"dir": -1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
         "episode": None, "regime": {"state": "RANGE", "dir": None}, "fut_age": 0.1, "spot_age": 0.3,
         "by_id": {q["id"]: q}, "by_key": {q["key"]: q}}
    c.update(kw)
    return c


def _looks(name, dt, *looks, **kw):
    """the book asks to buy at dt; the engine then looks at each (seconds after the trigger, age of the option's row
    [, the engine's own step gap: the time since the previous look when left out]). Returns the last look's pos and
    why, and the book."""
    b = paper.Book(name, config.VARIANTS[name], dt.strftime("%Y-%m-%d"))
    paper.request_entry(b, _fill_ctx(1000.0, dt, LW_OPT), LW_OPT, "t")
    res, prev = (None, ""), 0.0
    for wait, age, *gap in looks:
        q = dict(LW_OPT, ltp=106.0, bid=105.9, ask=106.1, age=age)
        res = paper.try_fill_entry(b, _fill_ctx(1000.0 + wait, dt + timedelta(seconds=wait), q,
                                                step_gap=gap[0] if gap else wait - prev, **kw))
        prev = wait
        if res[0] or res[1].startswith("entry lapsed"):
            break
    return res[0], res[1], b


def test_a_late_look_fills_an_entry_whose_option_has_printed():
    """9 Nov: the engine's first look came 3.0 to 7.4 s after the trigger and 36 entries were dropped, each with a fresh
    price on the screen. The print is now checked before the window, for every book."""
    assert config.ENTRY_FILL_MAX_S == 3.0 and config.ENTRY_LATE_LOOK_MAX_S == 10.0 and config.validate() == []
    for name in ("c20_9y", "c20_9t", "spot_dc12_t12_first"):                 # the live pool and an older book alike
        pos, why, b = _looks(name, NORM_DT, (5.7, 0.3))                      # looked at 5.7 s; the row is 0.3 s old
        assert pos and pos["entry"] == 106.0 and pos["late_entry"] is True and pos["fill_delay_s"] == 5.7, (name, why)
        assert pos["late_gap_s"] == 5.7 and pos["trigger_ltp"] == 104.0 and "pending_entry" not in b.ctl
    pos, why, b = _looks("c20_9y", NORM_DT, (2.0, 0.3))                      # inside the window: an ordinary fill
    assert pos and "late_entry" not in pos and "late_gap_s" not in pos
    pos, why, b = _looks("c20_9y", NORM_DT, (5.7, 9.0))                      # late look, but the option never printed
    assert pos is None and why.startswith("entry lapsed: no print on 25000 PE within 3 s") and "[engine stalled 5.7 s]" in why
    pos, why, b = _looks("c20_9y", NORM_DT, (5.7, 5.8))                      # its last print is older than the trigger
    assert pos is None and "no print" in why
    pos, why, b = _looks("c20_9y", NORM_DT, (3.1, 9.0, 0.1), (5.7, 0.3))     # a healthy engine and a quiet option: gone
    assert pos is None and "within 3 s" in why and "engine stalled" not in why      # at 3.1 s, as before the change
    # 16 Nov (independent review): an engine that KEEPS UP gets no late fill. The champion-family books look once a
    # second; an option silent for 3 s that prints at 3.5 s was bought at the 4 s look by the first version.
    pos, why, b = _looks("c20_9y", NORM_DT, (0.98, 9.0, 0.1), (1.98, 9.0, 0.1), (2.98, 9.0, 0.1), (3.98, 0.48, 0.1))
    assert pos is None and why == "entry lapsed: no print on 25000 PE within 3 s"
    pos, why, b = _looks("c20_9y", NORM_DT, (3.05, 0.02, 0.1))               # a print just after the window: D-126 as it was
    assert pos is None and "within 3 s" in why and b.blocked == why
    pos, why, b = _looks("c20_9y", NORM_DT, (3.05, 0.02, 0.9))               # a step gap under 1 s is not "the engine was late"
    assert pos is None and "within 3 s" in why
    pos, why, b = _looks("c20_9y", NORM_DT, (3.05, 0.02, 1.0))               # at 1 s it is (paper.ENGINE_STALL_S)
    assert pos and pos["late_entry"] is True and pos["late_gap_s"] == 1.0
    pos, why, b = _looks("c20_9y", NORM_DT, (1.0, 0.3, 0.1), kill=True)      # the kill switch ends a waiting entry at once
    assert pos is None and why == "entry lapsed: kill switch" and "pending_entry" not in b.ctl and "req_log" not in b.ctl
    pos, why, b = _looks("c20_9y", NORM_DT, (5.7, 0.3), kill=True)           # and a late look cannot buy through it
    assert pos is None and "kill switch" in why
    pos, why, b = _looks("c20_9y", NORM_DT, (0.5, 9.0), (6.5, 0.4))          # looked once in time, then stood still
    assert pos and pos["late_entry"] is True and pos["late_gap_s"] == 6.0
    pos, why, b = _looks("c20_9y", NORM_DT, (10.5, 0.3))                     # bounded: never over 10 s after the signal
    assert pos is None and "the engine looked 10.5 s after the trigger, over the 10 s limit" in why
    assert b.blocked == why and b.ctl["req_log"][-1][0] == 1000.0            # remembered as a lapse, like any other
    pos, why, b = _looks("c20_9y", NORM_DT, (5.7, 0.3), blackout={"on": True, "why": "feed silent"})
    assert pos is None and "data gap" in why                                 # a blackout still drops it at once
    cut = datetime(2026, 11, 16, config.LAST_ENTRY[0], config.LAST_ENTRY[1] - 1, 58, tzinfo=config.IST)
    pos, why, b = _looks("c20_9y", cut, (5.7, 0.3))                          # and nothing is bought after the entry window
    assert pos is None and why.startswith("entry lapsed")


def test_the_account_follows_its_owner_into_a_late_fill(tmp_path):
    names = list(config.VARIANTS)
    c = cond.Conductor("2026-11-16", names, log_dir=str(tmp_path))
    bs = {n: paper.Book(n, config.VARIANTS[n], "2026-11-16") for n in ("c20_9y", "conductor")}
    t0 = NORM_DT.timestamp()
    ctx = _fill_ctx(t0, NORM_DT, LW_OPT)
    paper.request_entry(bs["c20_9y"], ctx, LW_OPT, "COUNCIL pb")
    assert c.step(bs["conductor"], bs, ctx)[0] == "owner"
    q = dict(LW_OPT, ltp=106.0, bid=105.9, ask=106.1, age=0.3)
    late = _fill_ctx(t0 + 5.7, NORM_DT + timedelta(seconds=5.7), q, step_gap=5.7)   # the engine's next look, 5.7 s on
    pos, why = paper.try_fill_entry(bs["c20_9y"], late)
    assert pos and pos["late_entry"], why
    r = c.step(bs["conductor"], bs, late)
    assert r[0] == "entry" and bs["conductor"].pos["late_entry"] is True and bs["conductor"].pos["entry"] == 106.0
    rows = [json.loads(x) for x in open(tmp_path / "conductor_2026-11-16.jsonl", encoding="utf-8")]
    assert [x["event"] for x in rows if x["event"] in ("owner", "entry", "release")] == ["owner", "entry"]
    assert [x["fill_delay_s"] for x in rows if x["event"] == "entry"] == [5.7]
    f = funnel.funnel(funnel.read_log("2026-11-16", "conductor", str(tmp_path)), "2026-11-16")
    assert f["late_fills"] == [5.7] and f["events"].get("release", 0) == 0
    out = "\n".join(funnel.lines("2026-11-16", "conductor", str(tmp_path)))
    assert "**1 of the 1 fills came from a late look**" in out and "5.7 to 5.7 s after its trigger" in out


def test_the_funnel_counts_a_look_past_the_limit_as_the_engine_being_late():
    why = "entry lapsed: the engine looked 10.5 s after the trigger, over the 10 s limit"
    assert funnel.lapse_kind(why, None) == funnel.LAPSE_LATE


# ── 5. the long-wait expiry twin (owner: "Yes, build it"; docs/64 section 6) ────
def test_the_long_wait_twin_keeps_an_expiry_day_entry_on_a_quiet_option():
    """lw_c20_9y waits 10 s for a print on the option's own expiry day. Since the late-look rule every book keeps an
    entry the ENGINE looked at late; the twin now differs only when the OPTION is quiet."""
    v = config.VARIANTS["lw_c20_9y"]
    assert v["council"] == "c20_9y" and v.get("twin") and v["entry_wait_exp"] == 10.0 and config.validate() == []
    assert [n for n, p in config.VARIANTS.items() if p.get("entry_wait_exp")] == ["lw_c20_9y"]   # one book, a shadow
    assert "lw_c20_9y" in learning.SHADOW_BOOKS
    assert "lw_c20_9y" not in [m["book"] for m in cond.Conductor("2026-11-17", list(config.VARIANTS), log_dir="").members]
    quiet = ((3.1, 9.0, 0.1), (5.7, 0.3, 0.1))                               # no print by 3.1 s; one arrives at 5.4 s
    pos, why, b = _looks("c20_9y", EXP_DT, *quiet)                           # the live book: lapsed at 3.1 s
    assert pos is None and "within 3 s" in why
    pos, why, b = _looks("lw_c20_9y", EXP_DT, *quiet)                        # the twin: still waiting, then filled
    assert pos and pos["entry"] == 106.0 and pos["late_entry"] is True and pos["fill_delay_s"] == 5.7
    pos, why, b = _looks("lw_c20_9y", EXP_DT, (2.0, 0.3))                    # inside the usual window: an ordinary fill
    assert pos and "late_entry" not in pos
    pos, why, b = _looks("lw_c20_9y", EXP_DT, (5.7, 9.0))                    # no print yet: it keeps waiting
    assert pos is None and why.startswith("entry pending")
    pos, why, b = _looks("lw_c20_9y", EXP_DT, (5.7, 9.0), (10.5, 20.0))      # its own window is bounded
    assert pos is None and "within 10 s" in why
    pos, why, b = _looks("lw_c20_9y", NORM_DT, *quiet)                       # not the option's expiry day: 3 s
    assert pos is None and "within 3 s" in why
    pos, why, b = _looks("lw_c20_9y", EXP_DT, (5.7, 0.3), blackout={"on": True, "why": "feed silent"})
    assert pos is None and "data gap" in why
    assert paper.entry_wait_s(paper.Book("c20_9y", config.VARIANTS["c20_9y"], "2026-11-17"), LW_OPT, {"now_dt": EXP_DT}) == 3.0


def test_a_longer_entry_wait_is_refused_on_anything_but_a_bounded_shadow_twin(monkeypatch):
    monkeypatch.setitem(config.VARIANTS, "c20_9y", dict(config.VARIANTS["c20_9y"], entry_wait_exp=10.0))
    assert any("c20_9y: entry_wait_exp needs twin=True" in m for m in config.validate())      # never a live book
    monkeypatch.setitem(config.VARIANTS, "c20_9y", dict(config.VARIANTS["c20_9y"]))
    monkeypatch.setitem(config.VARIANTS, "lw_c20_9y", dict(config.VARIANTS["lw_c20_9y"], entry_wait_exp=120.0))
    assert any("lw_c20_9y: entry_wait_exp" in m for m in config.validate())                   # and never unbounded
    monkeypatch.setitem(config.VARIANTS, "lw_c20_9y", dict(config.VARIANTS["lw_c20_9y"]))
    monkeypatch.setattr(config, "ENTRY_LATE_LOOK_MAX_S", 120.0)
    assert any("ENTRY_LATE_LOOK_MAX_S" in m for m in config.validate())                       # the late look is bounded too
