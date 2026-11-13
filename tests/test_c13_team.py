"""28 Oct evening, 15-member review: delta-target strike, data-gap and impulse-duration guards on the pullback,
no-progress time stop, retest filler with its own premium bracket. python tests/test_c13_team.py"""
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c13_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False
from apex.engine import paper  # noqa: E402

T0 = datetime(2026, 10, 23, 10, 30, tzinfo=config.IST)      # 4 DTE to 27 Oct
OPT = {"id": 5, "key": "NIFTY|OPT|2026-10-27|22700|CE", "strike": 22700, "rr": "CE", "expiry": "2026-10-27",
       "ltp": 200.0, "bid": 199.9, "ask": 200.1, "delta": 0.55, "iv": 14.0, "age": 0.1, "week": 0, "ltt": None,
       "gamma": 0.0012, "theta_min": -0.12}


def _ctx(s, ltp=200.0, spot=22700.0, now=T0, **kw):
    q = dict(OPT, ltp=ltp)
    c = {"now_s": float(s), "now_dt": now, "w0": "2026-10-27", "spot": spot, "spot_age": 0.3, "fut": 22715.0,
         "fut_ltp": 22715.0, "fut_age": 0.1, "day": {}, "day_obj": None, "advisors": {}, "blackout": {"on": False},
         "domino": {"dir": 1, "z": 0.0, "r15": 0.0, "S_up": 0.0, "S_dn": 0.0, "sigma15": 5.0, "gap": 0.0},
         "episode": None, "regime": {}, "edge": {"v_min30": 200.0}, "by_id": {5: q}, "by_key": {OPT["key"]: q},
         "options": [q]}
    c.update(kw)
    return c


def _chain(*deltas):
    out = []
    for i, dl in enumerate(deltas):
        k = 22600 + 50 * i
        out.append(dict(OPT, id=10 + i, key=f"NIFTY|OPT|2026-10-27|{k}|CE", strike=k, delta=dl, ltp=250.0 - 30 * i))
    return out


def test_registered():
    assert config.validate() == [] and len(config.VARIANTS) == 115       # +2 thrust books, +1 stall twin, +1 shadow Conductor (14 Nov, docs/57); +3 c20_9y exit twins, +2 shadow Conductors (13 Nov, docs/56); +1 re-entry twin (11 Nov, docs/49); +2 forecast twins of c20_9y, +4 forecast shadows (10 Nov, docs/41); +4 third-batch books (10 Nov, docs/39); +8 second-generation books (9 Nov, docs/37); 67 + c20_9e, c20_9h (3 Nov), c20_9s (3 Nov night), c20_9y (4 Nov) + 14 restricted (7 Nov; spot_pb45_r003 off 8 Nov) + conductor (8 Nov)
    names = list(config.VARIANTS)
    assert names[names.index("c20_9e"):names.index("c20_9y") + 1] == ["c20_9e", "c20_9h", "c20_9s", "c20_9y"]
    assert sum(1 for p in config.VARIANTS.values() if p.get("rules")) == 14                 # spot_pb45_r003 off 8 Nov
    assert config.VARIANTS["t28_core"]["delta_target"] == 0.46 and config.CHAMPION_DEFAULT == "c20_9x"
    for k in ("t28_d46", "t28_gap", "t28_dur20", "t28_ts", "t28_fill", "t28_core", "t28_core_fill", "t28_all"):
        assert "alloc_pct" not in config.VARIANTS[k]                         # all-in, owner's rule


def test_delta_target_picks_046_on_normal_days_only():
    ch = _chain(0.66, 0.58, 0.47, 0.38)
    b = paper.Book("t28_d46", config.VARIANTS["t28_d46"], "2026-10-23")
    o, _ = paper.choose_contract(_ctx(100, options=ch), 1, b)
    assert abs(o["delta"]) == 0.47
    base = paper.Book("lvl_trail_re", config.VARIANTS["lvl_trail_re"], "2026-10-23")
    o2, _ = paper.choose_contract(_ctx(100, options=ch), 1, base)
    assert o2["delta"] == 0.58                                               # the old band: lowest >= 0.52
    exp = datetime(2026, 10, 27, 10, 30, tzinfo=config.IST)                  # expiry day: the old rule
    o3, _ = paper.choose_contract(_ctx(100, options=ch, now=exp), 1, b)
    o4, _ = paper.choose_contract(_ctx(100, options=ch, now=exp), 1, base)
    assert o3["strike"] == o4["strike"]


def _pb_ctx(s, t_lo, ext_t, **kw):
    pb = {"ok": True, "hi": 22800.0, "lo": 22700.0, "t_hi": ext_t, "t_lo": t_lo, "d": 1, "ext_t": ext_t,
          "pbx": 22740.0, "rng": 100.0, "n": 2700, "span": 2700}
    return _ctx(s, spot=22740.0, pb=pb, **kw)


def test_impulse_duration_guard():
    b = paper.Book("t28_dur20", config.VARIANTS["t28_dur20"], "2026-10-23")
    fire, why = paper.evaluate_pullback(b, _pb_ctx(10_000, t_lo=10_000 - 1000, ext_t=10_000 - 100))   # 15-min spike
    assert not fire and "spike" in why
    b2 = paper.Book("t28_dur20", config.VARIANTS["t28_dur20"], "2026-10-23")
    fire, why = paper.evaluate_pullback(b2, _pb_ctx(10_000, t_lo=10_000 - 2600, ext_t=10_000 - 100))  # 42-min impulse
    assert fire, why


def test_data_gap_guard():
    b = paper.Book("t28_gap", config.VARIANTS["t28_gap"], "2026-10-23")
    paper._track_gap(b, _ctx(5_000, spot_age=10.0))                         # stale from ~4990
    paper._track_gap(b, _ctx(5_300, spot_age=310.0))
    paper._track_gap(b, _ctx(5_301))                                         # fresh again: a 311-s gap
    assert b.ctl["gap_last"]["e"] == 5301.0
    fire, why = paper.evaluate_pullback(b, _pb_ctx(6_000, t_lo=6_000 - 2600, ext_t=6_000 - 100))
    assert not fire and "data gap" in why
    fire, _ = paper.evaluate_pullback(b, _pb_ctx(5_301 + 2701, t_lo=8_002 - 2600, ext_t=8_002 - 100))
    assert fire                                                              # the gap has left the 45-min window
    c = paper.Book("t28_gap", config.VARIANTS["t28_gap"], "2026-10-23")
    paper._track_gap(c, _ctx(5_000, spot_age=10.0))
    paper._track_gap(c, _ctx(5_030))                                         # 40-s blip: not remembered
    assert "gap_last" not in c.ctl


def test_no_progress_time_stop():
    b = paper.Book("t28_ts", config.VARIANTS["t28_ts"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK"})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    for s in range(101, 339):
        assert paper.check_exit(b, _ctx(s, 203.0)) is None                   # +1.5 %: never +2 %
    t = None
    for s in range(340, 360):
        t = paper.check_exit(b, _ctx(s, 203.0))
        if t:
            break
    assert t and t["reason"].startswith("TIME (no progress"), t
    a = paper.Book("t28_ts", config.VARIANTS["t28_ts"], "2026-10-23")
    a.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK"})
    paper.open_trade(a, _ctx(100), dict(OPT), "t")
    paper.check_exit(a, _ctx(120, 206.0))                                    # +3 % once: it made progress
    for s in range(121, 400):
        assert paper.check_exit(a, _ctx(s, 203.0)) is None


def test_filler_bracket_and_no_reentry_mark():
    b = paper.Book("t28_fill", config.VARIANTS["t28_fill"], "2026-10-23")
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-RETEST-FILL", "fill": True})
    paper.open_trade(b, _ctx(100), dict(OPT), "t")
    assert b.pos["fill"]
    assert paper.check_exit(b, _ctx(101, 215.0)) is None                     # +7.5 %
    t = paper.check_exit(b, _ctx(102, 221.0))                                # +10.5 %
    assert t and t["reason"].startswith("TARGET (filler"), t
    assert "reentry" not in b.ctl                                            # a filler leaves no re-entry chain
    b.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-RETEST-FILL", "fill": True})
    paper.open_trade(b, _ctx(300), dict(OPT), "t")
    t = paper.check_exit(b, _ctx(301, 185.0))                                # -7.5 %
    assert t and t["reason"].startswith("STOP (filler") and "reentry" not in b.ctl


def test_filler_fires_through_the_retest_path_when_the_pullback_has_nothing():
    b = paper.Book("t28_fill", config.VARIANTS["t28_fill"], "2026-10-23")
    base = paper.Book("lvl_trail_re", config.VARIANTS["lvl_trail_re"], "2026-10-23")
    kw = dict(spot_hi=22700.0, spot_lo=22600.0)
    seq = [22702.0, 22708.0, 22701.0]                                        # break, run 5+, back within 2
    fired = []
    for i, sp in enumerate(seq):
        c = _ctx(1000 + i, spot=sp, **kw)
        fired.append(paper.evaluate_spot_breakout(b, c))
        assert not paper.evaluate_spot_breakout(base, _ctx(1000 + i, spot=sp, **kw))[0]   # champion: pullback only
    assert fired[-1][0] and b.ctl["fill"] and b.ctl["ep_type"] == "SPOT-RETEST-FILL", fired


def _filler_run(now=T0, **extra):
    """Break the 12-min high, run 5+, come back within 2: the retest pattern the filler buys."""
    b = paper.Book("t28_fill", config.VARIANTS["t28_fill"], "2026-10-23")
    kw = dict(spot_hi=22700.0, spot_lo=22600.0, **extra)
    out = None
    for i, sp in enumerate([22702.0, 22708.0, 22701.0]):
        out = paper.evaluate_spot_breakout(b, _ctx(1000 + i, spot=sp, now=now, **kw))
    return out, b


def test_filler_never_enters_after_the_pullback_entry_end():
    """7 Nov bug fix: the filler traded on any "no" from the pullback, including "no new entries after 14:45", and
    entered after 14:45 and even after the 15:00 book flatten (closed a second later)."""
    assert tuple(config.VARIANTS["t28_fill"]["pb_entry_end"]) == (14, 45)
    for hm in ((14, 45), (14, 54), (15, 3), (15, 14)):
        fire, why = _filler_run(now=T0.replace(hour=hm[0], minute=hm[1]))[0]
        assert not fire and "no new entries after 14:45" in why, (hm, why)
    assert _filler_run(now=T0.replace(hour=14, minute=44))[0][0]            # one minute before: still allowed


def test_filler_respects_range_mode():
    fire, why = _filler_run(day={"range_on": True, "range_since": 0, "lo": 22500, "hi": 22800})[0]
    assert not fire and "range mode" in why, why


def test_round2_flow_veto():
    from collections import deque
    assert config.VARIANTS["t28_st20"]["spot_trail"] == 20.0 and config.VARIANTS["t28_ivfall"]["pb_gap_block_s"] == 120
    b = paper.Book("t28_ivfall", config.VARIANTS["t28_ivfall"], "2026-10-23")
    h = deque([(t, 14.0 if t < 1100 else 13.6, 1e6) for t in range(0, 1901)])   # IV 14.0 -> 13.6 = -2.9 %
    ctx = _ctx(1900, ohist={5: h})
    assert "IV" in paper.flow_veto(b, ctx, dict(OPT))
    h2 = deque([(t, 14.0 if t < 1100 else 13.8, 1e6) for t in range(0, 1901)])  # -1.4 %: bought
    assert paper.flow_veto(b, _ctx(1900, ohist={5: h2}), dict(OPT)) == ""
    base = paper.Book("t28_gap", config.VARIANTS["t28_gap"], "2026-10-23")
    assert paper.flow_veto(base, ctx, dict(OPT)) == ""                       # the champion never vetoes
    c = paper.Book("t28_bidpile", config.VARIANTS["t28_bidpile"], "2026-10-23")
    h3 = deque([(t, 14.0, 1e6 if t < 1880 else 1.01e6) for t in range(0, 1901)])   # +1 % bids in the last 30 s
    assert "late chase" in paper.flow_veto(c, _ctx(1900, ohist={5: h3}), dict(OPT))
    h4 = deque([(t, 14.0, 1e6 if t < 1880 else 1.005e6) for t in range(0, 1901)])
    assert paper.flow_veto(c, _ctx(1900, ohist={5: h4}), dict(OPT)) == ""
    assert paper.flow_veto(c, _ctx(1900), dict(OPT)) == ""                   # no history yet: never blocks


def test_round3_not_at_high_and_required_move():
    from collections import deque
    b = paper.Book("t28_nohigh", config.VARIANTS["t28_nohigh"], "2026-10-23")
    b.ctl["ep_type"] = "SPOT-PULLBACK"
    h = deque([(t, 14.0, 1e6, 200.0 if t < 1800 else 197.0) for t in range(1500, 1901)])   # 1.5 % under the high
    assert "5-min high" in paper.flow_veto(b, _ctx(1900, ohist={5: h}), dict(OPT))
    h2 = deque([(t, 14.0, 1e6, 200.0 if t < 1800 else 192.0) for t in range(1500, 1901)])  # 4 % under: cheap
    assert paper.flow_veto(b, _ctx(1900, ohist={5: h2}), dict(OPT)) == ""
    b.ctl["ep_type"] = "SPOT-ORB"                                            # breakouts are never vetoed
    assert paper.flow_veto(b, _ctx(1900, ohist={5: h}), dict(OPT)) == ""
    r = paper.Book("t28_req", config.VARIANTS["t28_req"], "2026-10-23")
    o = dict(OPT, ask=200.0, delta=0.55, gamma=0.0012, theta_min=-0.12)     # +10 %: about 37 pts needed
    quiet = deque([(t, 22700.0 + (t % 2) * 20) for t in range(900, 1901)])    # 20-pt 15-min range
    busy = deque([(t, 22700.0 + (t % 2) * 60) for t in range(900, 1901)])     # 60-pt range
    assert "needs" in paper.flow_veto(r, _ctx(1900, ohist={"spot": quiet}), o)
    assert paper.flow_veto(r, _ctx(1900, ohist={"spot": busy}), o) == ""
    assert paper.flow_veto(r, _ctx(1900, ohist={"spot": deque([(1800, 22700.0)])}), o) == ""   # < 14 min of spot: no veto


def test_round4_expiry_day_cheapest_strike():
    from collections import deque
    exp = datetime(2026, 10, 27, 10, 30, tzinfo=config.IST)                  # expiry day
    K = [22600, 22650, 22700]
    ch = [dict(OPT, id=20 + i, key=f"NIFTY|OPT|2026-10-27|{k}|CE", strike=k, delta=0.75 - 0.1 * i,
               ask=200.0 - 30 * i, bid=199.6 - 30 * i, age=0.1) for i, k in enumerate(K)]
    # forward +20 pts in the last 60 s; 22650 (index 1) has not repriced, the others have
    oh = {"fwd": deque([(t, 22700.0 if t < 1850 else 22720.0) for t in range(1700, 1901)])}
    for i, o in enumerate(ch):
        mid0 = o["ask"] - (o["delta"] * 20 if i != 1 else 0.0) - 0.2
        oh[o["id"]] = deque([(t, 14.0, 1e6, mid0, o["delta"], 0.001, -0.1) for t in range(1700, 1901)])
    c = _ctx(1900, options=ch, now=exp, spot=22700.0, ohist=oh)
    b = paper.Book("t28_cheapK", config.VARIANTS["t28_cheapK"], "2026-10-27")
    o, note = paper.cheap_strike(b, c, ch[2])
    assert o["strike"] == 22650 and "cheaper strike" in note, note
    c2 = _ctx(1900, options=ch, now=T0, spot=22700.0, ohist=oh)                # normal day: unchanged
    assert paper.cheap_strike(b, c2, ch[2])[0] is ch[2]


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)
