"""15 Nov (owner: "Yes, build the shadow"; docs/60 section 7): the expiry-style switch. fade3x (the three fades on
expiry days, 45-minute clock) and the shadow account conductor_xs (the live pool on normal days; on expiry days the
pool or fade3x alone, by the last 6 expiry days). Shadow only: the live Conductor and its pool are untouched."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.engine import conductor as cond, learning  # noqa: E402
from apex.engine.council import fade, fade3x  # noqa: E402
from test_fade_14nov import _buys, _day, _levels, _orb_day  # noqa: E402

NAMES = lambda: list(config.VARIANTS)  # noqa: E731


def _hist(rows, path=None):
    p = path or cond.xs_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(rows, fh)
    return p


def test_registered_last_as_shadows_and_the_live_pool_is_untouched():
    names = NAMES()
    assert names[-2:] == ["fade3x", "conductor_xs"] and config.validate() == []
    assert config.VARIANTS["fade3x"].get("twin") and config.VARIANTS["conductor_xs"].get("shadow_policy") == "xswitch"
    live = cond.Conductor("2026-11-17", names)
    assert "fade3x" not in [m["book"] for m in live.members]
    xs = cond.AdaptiveConductor("2026-11-17", names, "xswitch", "conductor_xs")
    assert [m["book"] for m in xs.members][:-1] == [m["book"] for m in live.members] and xs.members[-1]["book"] == "fade3x"
    assert "conductor_xs" in learning.SHADOW_ACCOUNTS and "fade3x" in learning.SHADOW_BOOKS
    assert cond.xs_path().startswith(config.LEARN_DIR)                       # the test fence redirects it


def test_mode_reads_only_earlier_expiry_days_and_needs_six():
    p = _hist({})
    assert cond.xswitch_mode("2026-11-17", p)[0] == "pool"                   # no history: the pool trades
    days = [f"2026-10-{k:02d}" for k in range(1, 7)]
    _hist({d: {"champ": -10.0, "fade": 5.0} for d in days[:5]}, p)
    assert cond.xswitch_mode("2026-11-17", p)[0] == "pool"                   # five rows are not enough
    _hist({d: {"champ": -10.0, "fade": 5.0} for d in days}, p)
    m, why = cond.xswitch_mode("2026-11-17", p)
    assert m == "fade" and "fade3x +30 %" in why and "pool -60 %" in why
    assert cond.xswitch_mode("2026-10-06", p)[0] == "pool"                   # the day itself and later days are not read
    rows = {d: {"champ": -10.0, "fade": 5.0} for d in days}
    rows["2026-10-07"] = {"champ": 200.0, "fade": 0.0}                       # the newest row turns it back
    _hist(rows, p)
    assert cond.xswitch_mode("2026-11-17", p)[0] == "pool"
    _hist({d: {"champ": 1.0, "fade": 1.0} for d in days}, p)
    assert cond.xswitch_mode("2026-11-17", p)[0] == "pool"                   # a tie keeps the pool


def test_expiry_date_comes_from_the_entry_or_its_key():
    assert cond._expiry_of({"key": "NIFTY|OPT|2026-11-17|25000|CE"}) == "2026-11-17"
    assert cond._expiry_of({"expiry": "2026-11-24", "key": "NIFTY|OPT|2026-11-17|25000|CE"}) == "2026-11-24"
    assert cond._expiry_of({"key": "junk"}) == ""


def test_account_admits_one_style_on_expiry_days_and_the_pool_on_normal_days():
    days = [f"2026-10-{k:02d}" for k in range(1, 7)]
    _hist({d: {"champ": -10.0, "fade": 5.0} for d in days})                  # fade mode
    names = NAMES()
    exp_key = {"key": "NIFTY|OPT|2026-11-17|25000|CE"}
    xs = cond.AdaptiveConductor("2026-11-17", names, "xswitch", "conductor_xs")
    pool_m, fade_m = xs.members[0], xs.members[-1]
    ctx = {"now_s": 0.0}
    assert "fade mode" in xs.admit(pool_m, exp_key, None, {}, ctx) and xs.admit(fade_m, exp_key, None, {}, ctx) is None
    _hist({d: {"champ": 10.0, "fade": 5.0} for d in days})                   # the mode is fixed for the day once decided
    assert "fade mode" in xs.admit(pool_m, exp_key, None, {}, ctx)
    xs2 = cond.AdaptiveConductor("2026-11-17", names, "xswitch", "conductor_xs")
    assert xs2.admit(pool_m, exp_key, None, {}, ctx) is None and "pool mode" in xs2.admit(fade_m, exp_key, None, {}, ctx)
    nd = cond.AdaptiveConductor("2026-11-16", names, "xswitch", "conductor_xs")
    assert nd.admit(pool_m, exp_key, None, {}, ctx) is None                  # a normal day: the pool, as live
    assert "expiry days only" in nd.admit(fade_m, exp_key, None, {}, ctx) and nd.xs_mode is None
    off = cond.offline_admit("xswitch")
    trig = 1794887400.0                                                      # 2026-11-17 09:20 IST (pool mode history)
    assert off(trig, pool_m, exp_key, [], {}) is None and "pool mode" in off(trig, fade_m, exp_key, [], {})
    assert "expiry days only" in off(trig - 86400.0, fade_m, exp_key, [], {})   # 16 Nov: a normal day for this option


def test_nightly_record_writes_expiry_days_only_and_keeps_research_rows(tmp_path):
    p = str(tmp_path / "xs.json")
    _hist({"2026-11-09": {"champ": 1.0, "fade": 2.0, "src": "research"}}, p)
    t_exp = {"key": "NIFTY|OPT|2026-11-17|25000|CE", "ret_pct": 10.0}
    t_norm = {"key": "NIFTY|OPT|2026-11-17|25000|CE", "ret_pct": 5.0}
    days = {"conductor": {"2026-11-16": [t_norm], "2026-11-17": [t_exp, t_exp]},
            "fade3x": {"2026-11-17": [{"key": "NIFTY|OPT|2026-11-17|25000|PE", "ret_pct": -20.0}]}}
    put = learning.xswitch_record(days, path=p)
    H = json.load(open(p, encoding="utf-8"))
    assert put == ["2026-11-17"] and set(H) == {"2026-11-09", "2026-11-17"} and H["2026-11-09"]["src"] == "research"
    assert abs(H["2026-11-17"]["champ"] - 21.0) < 1e-6 and abs(H["2026-11-17"]["fade"] + 20.0) < 1e-6
    assert learning.xswitch_record(days, path=p) == []                      # unchanged: nothing written again


def test_fade3x_trades_the_three_fades_on_expiry_days_only(tmp_path):
    p = _levels(tmp_path)

    class X(fade3x.Strategy):
        LEVELS = p
    s, out = _buys(_day("2026-11-17", "2026-11-17", +400.0, n=5000), X, 4900)    # expiry day, a 400-pt rise
    assert out and all(a[2] == "PE" for _, a in out) and "FADE3X" in out[0][1][3] and s.fd_dte == 0, out
    assert s.p["hold"] == fade3x.HOLD_S == 2700                                  # the expiry ladder, 45-minute clock
    s, out = _buys(_day("2026-11-16", "2026-11-17", +400.0, n=5000), X, 4900)    # a normal day: off
    assert out == []
    s, out = _buys(_orb_day("2026-11-17", "2026-11-17", 25080.0), X, 3000)      # the opening-range break, faded once
    assert len(out) == 1 and out[0][1][2] == "PE" and "ORB" in out[0][1][3] and s.f3_orb_done
    assert issubclass(X, fade._FadeMixin)
