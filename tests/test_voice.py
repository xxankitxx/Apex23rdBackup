"""13 Nov (owner point 4): the Conductor's first-person voice (apex/engine/voice.py). It reads the lead pool book's
real c20 strategy object and the Conductor's position; it never writes either. The trigger is driven here through the
real c20_9y class on a synthetic forward: flat, a 50-pt impulse, a 60 % pullback, a turn back up."""
import os
import sys
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.engine import paper  # noqa: E402
from apex.engine.council import LiveDay  # noqa: E402
from apex.engine.council import c20_9y  # noqa: E402
from apex.engine.voice import Voice  # noqa: E402

DAY, EXP = "2026-11-06", "2026-11-11"


def _path():
    f = [25000.0] * 1300
    f += list(25000 + np.linspace(0, 50, 600)[1:])          # impulse +50 in 10 min
    f += list(25050 - np.linspace(0, 30, 240)[1:])          # pullback 30 (60 %)
    f += list(25020 + np.linspace(0, 8, 40)[1:])            # resumption +8
    return f


def _rig():
    D = LiveDay(DAY, EXP)
    D.K = np.array([25000.0])                                # one strike, no quotes: the picker finds nothing
    s = c20_9y.Strategy()
    cb = paper.Book("conductor", config.VARIANTS["conductor"], DAY)
    lead = paper.Book("c20_9y", config.VARIANTS["conductor"], DAY)
    eng = SimpleNamespace(books={"conductor": cb, "c20_9y": lead},
                          conductor=SimpleNamespace(members=[{"book": "c20_9y"}], recent=[]),
                          _council_ad={"c20_9y": SimpleNamespace(strat=s, D=D)})
    return D, s, eng


def _ctx(D, i):
    return {"now_s": D.t_open + i, "by_key": {}, "w0": EXP, "blackout": {"on": False}}


def test_the_voice_follows_the_real_trigger_and_speaks_in_the_first_person():
    D, s, eng = _rig()
    v = Voice()
    seen = {}
    snap_s = None
    for i, f in enumerate(_path()):
        D.fwd[i] = f
        D.i = i
        s.on_second(i, D, None)
        if i % 5 == 0 or i > 2130:
            before = (None if s.arm is None else list(s.arm), len(s.qmax))
            out = v.view(eng, _ctx(D, i))
            assert before == (None if s.arm is None else list(s.arm), len(s.qmax)), "the voice wrote strategy state"
            if i >= 1250:                                    # after the 20-min warm-up
                seen.setdefault(out["mode"], out)
            if out["mode"] == "ZONE" and snap_s is None:
                snap_s = out
    assert {"WAITING", "ARMED", "ZONE"} <= set(seen), sorted(seen)
    w = seen["WAITING"]
    assert w["headline"].startswith("I ") and "40-pt move" in w["headline"]
    a = seen["ARMED"]
    assert a["headline"].startswith("Armed for a CALL") and "of the" in a["headline"]
    arm = a["trigger"]["arm"]
    assert arm["side"] == "CE" and 45 <= arm["impulse_pts"] <= 52 and arm["need_pct"] == 50
    z = snap_s
    assert "I buy the moment the forward turns up" in z["headline"]
    assert z["trigger"]["arm"]["fire_level"] > z["trigger"]["arm"]["pullback_pts"]
    for out in seen.values():
        assert all(" you" not in (ln or "").lower() for ln in [out["headline"]] + out["lines"])


def test_holding_shows_the_real_exit_ladder_and_a_held_level():
    D, s, eng = _rig()
    cb = eng.books["conductor"]
    key = f"NIFTY|OPT|{EXP}|25000|CE"
    cb.pos = {"key": key, "rr": "CE", "strike": 25000.0, "lots": 6, "entry": 200.0, "time_in": "11:02:03", "src": "c20_9y",
              "rules": {"mode": "normal", "sl_pct": 15.0, "sl_px": 170.0, "trail_px": 25010.0, "trail_pts": 40.0,
                        "trail_give": 12.0, "fwd_now": 25038.0, "peak_pct": 8.0, "held_s": 600, "clock_left_s": 4800,
                        "flat_at": "15:20", "floor_px": None, "be_arm_pct": 15.0}}
    ctx = {"now_s": D.t_open + 7000, "by_key": {key: {"bid": 210.0, "delta": 0.6}}, "w0": EXP}
    out = Voice().view(eng, ctx)
    assert out["mode"] == "HOLDING" and out["headline"].startswith("I hold 6 lots of the 25000 CE")
    h = out["hold"]
    kinds = [x["kind"] for x in h["exits"]]
    assert kinds[:2] == ["SL", "FWD_TRAIL"] and "TIME" in kinds
    tr = h["exits"][1]
    assert tr["away_fwd"] == 28.0 and abs(tr["away_px"] - 16.8) < 1e-6
    assert h["level"] == "HOLD" and h["floor_arms_pct"] == 15
    assert any("I sell at the first of" in ln for ln in out["lines"])
    cb.pos["pending"] = {"why": "COUNCIL FWD_TRAIL"}
    out = Voice().view(eng, dict(ctx, now_s=ctx["now_s"] + 1))
    assert out["mode"] == "EXITING" and "selling at the next print" in out["lines"][0]


# ── 15 Nov review: the card never states an old price as "now", and says plainly when it cannot act ──
KEY = f"NIFTY|OPT|{EXP}|25000|CE"


def _held(eng, t_in=1.0, **rules):
    r = {"mode": "normal", "sl_pct": 15.0, "sl_px": 170.0, "trail_px": 25010.0, "trail_pts": 40.0, "trail_give": 12.0,
         "fwd_now": 25038.0, "peak_pct": 8.0, "held_s": 600, "clock_left_s": 4800, "flat_at": "15:20", "floor_px": None,
         "be_arm_pct": 15.0}
    r.update(rules)
    eng.books["conductor"].pos = {"key": KEY, "rr": "CE", "strike": 25000.0, "lots": 6, "entry": 200.0, "t_in": t_in,
                                  "time_in": "11:02:03", "src": "c20_9y", "rules": r}


def test_a_held_price_that_is_old_is_never_called_now():
    D, s, eng = _rig()
    _held(eng)
    q = {"bid": 210.0, "delta": 0.6, "age": 0.4}
    ctx = {"now_s": D.t_open + 7000, "by_key": {KEY: q}, "w0": EXP, "blackout": {"on": False}}
    out = Voice().view(eng, ctx)
    assert "+5.0 % now" in out["headline"] and out["hold"]["stale"] is None and "Nothing says sell yet. I hold." in out["lines"]
    out = Voice().view(eng, dict(ctx, blackout={"on": True}))                       # a feed gap while holding
    assert out["hold"]["stale"] == "gap" and " now" not in out["headline"] and "at the last price I have" in out["headline"]
    assert out["lines"][0].startswith("The data has a gap") and not any("Nothing says sell" in x for x in out["lines"])
    out = Voice().view(eng, dict(ctx, by_key={KEY: dict(q, age=120.0)}))            # a quote two minutes old
    assert out["hold"]["stale"] == "old" and out["hold"]["quote_age_s"] == 120 and "120 s old" in out["lines"][0]
    assert " now" not in out["headline"]
    out = Voice().view(eng, dict(ctx, by_key={}))                                   # no quote at all
    assert out["hold"]["stale"] == "no_bid" and " now" not in out["headline"] and "no bid" in out["lines"][0]
    assert out["hold"]["ret_pct"] is None


def test_the_clock_is_named_when_the_clock_is_the_near_exit_and_a_new_trade_starts_clean():
    D, s, eng = _rig()
    _held(eng, clock_left_s=200)                                                    # price exits far, 200 s on the clock
    ctx = {"now_s": D.t_open + 7000, "by_key": {KEY: {"bid": 210.0, "delta": 0.6}}, "w0": EXP}
    v = Voice()
    out = v.view(eng, ctx)
    assert out["hold"]["level"] == "NEAR" and out["hold"]["nearest"] == "CLOCK"
    assert any("Nearest exit: the hold clock" in x for x in out["lines"]) and not any("FWD_TRAIL" in x for x in out["lines"])
    eng.books["conductor"].pos["pending"] = {"why": "COUNCIL TIME"}
    assert v.view(eng, dict(ctx, now_s=ctx["now_s"] + 1))["mode"] == "EXITING"
    _held(eng, t_in=2.0)                                                            # another book takes over on the same step
    out = v.view(eng, dict(ctx, now_s=ctx["now_s"] + 2))
    assert out["mode"] == "HOLDING" and out["hold"]["level"] == "HOLD", out["hold"]["level"]


def test_kill_switch_session_edges_and_a_restart_are_said_plainly():
    import time
    from apex.engine import voice as voice_mod
    assert voice_mod._mins(150) == 2.5 and voice_mod._mins(1200) == 20 and voice_mod._mins(600) == 10
    D, s, eng = _rig()
    for i in range(1300):
        D.fwd[i] = 25000.0
        D.i = i
        s.on_second(i, D, None)
    assert Voice().view(eng, _ctx(D, 1299))["mode"] == "WAITING"
    out = Voice().view(eng, dict(_ctx(D, 1299), kill=True))
    assert out["mode"] == "PAUSED" and "kill switch" in out["headline"]
    out = Voice().view(eng, {"now_s": D.t_open + len(D.hm) + 5, "by_key": {}, "w0": EXP})
    assert out["mode"] == "STOOD_DOWN" and "session is over" in out["headline"]      # not "warming up" after 15:30
    out = Voice().view(eng, {"now_s": D.t_open - 60, "by_key": {}, "w0": EXP})
    assert out["mode"] == "STOOD_DOWN" and "not open yet" in out["headline"]
    D, s, eng = _rig()                                                              # a restart at row 5000
    for i in range(5000, 5100):
        D.fwd[i] = 25000.0
        D.i = i
        s.on_second(i, D, None)
    out = Voice().view(eng, _ctx(D, 5099))
    ready = time.strftime("%H:%M", time.localtime(D.t_open + 5000 + 1200))
    assert out["trigger"]["warm"] and out["mode"] == "WAITING" and ready in out["headline"], out["headline"]
    assert "learning the 20-min range" in out["headline"] and "p_fire" not in out["trigger"]


def test_a_fault_leaves_no_card_instead_of_the_last_seconds_card():
    D, s, eng = _rig()
    _held(eng)
    ctx = {"now_s": D.t_open + 7000, "by_key": {KEY: {"bid": 210.0, "delta": 0.6}}, "w0": EXP}
    v = Voice()
    assert v.view(eng, ctx)["mode"] == "HOLDING"

    def boom(*a, **k):
        raise RuntimeError("x")
    v._hold = boom
    nxt = dict(ctx, now_s=ctx["now_s"] + 1)
    try:
        v.view(eng, nxt)
        raise AssertionError("the fault must reach engine._safe")
    except RuntimeError:
        pass
    assert v.v is None and v.view(eng, nxt) is None                                 # once a second, no stale card
