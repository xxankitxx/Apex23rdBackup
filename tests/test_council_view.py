"""The dashboard's picture of a council position (3 Nov 2026).

On 3 Nov the band showed the t28 books' spot trail and +18 % profit lock for the c20_9x champion, which never runs
them: "Stop not set yet", "LOCK ARMS AT +18 %", an exit chip that only said "COUNCIL", and 158 commentary lines of
"[giveback: TypeError]". Now the council adapter publishes the strategy's real rules in pos["rules"] (premium stop,
forward trail from its best, hold clock, premium floors, premium trail), the publish drops the spot-trail / lock
fields for council books, the band and the commentary read the rules, and the exit's wait no longer overwrites the
entry's fill_delay_s.
"""
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from apex.engine.council import Adapter  # noqa: E402
from apex.engine import commentary  # noqa: E402


class _D:
    """A LiveDay stand-in: T in seconds, expiry flag."""
    def __init__(self, dte0):
        self.dte0 = dte0
        self.T = np.arange(0, 4000, 1.0)


class _Strat:
    """The attributes the view reads, shaped like c20_9x on an expiry day: EXP params, floors from c20_8x's EXTRA."""
    p = {"sl": 0.15, "trail": 25.0, "hold": 900}
    parts = {"exp", "norm", "seq", "pex", "pbg", "d52", "dtr", "ramp", "ivz", "ptre", "tie"}
    x = {"GB_ARM": 0.6, "GB_KEEP": 0.7, "BE_ARM": 0.15, "BE_LOCK": 0.0}
    r = {"PT_PA": 0.7, "PT_PQ": 0.08, "R_ARM": 0.15}
    best = 23640.0
    spk = None

    def __init__(self, fs_now):
        self.fs = np.full(4000, np.nan)
        self.fs[100] = fs_now

    def _floor(self, e, g, dte0):          # c20_9x._floor0 without the ramp (expiry day)
        if g >= self.x["GB_ARM"]:
            return e * (1 + self.x["GB_KEEP"] * g), "GIVEBACK"
        if g >= self.x["BE_ARM"]:
            return e * (1 + self.x["BE_LOCK"]), "BE_LOCK"
        return None, None


def _adapter(strat):
    a = Adapter.__new__(Adapter)
    a.strat = strat
    return a


def test_rules_view_expiry_day_before_the_floor_arms():
    a = _adapter(_Strat(23630.0))
    p = {"entry": 100.0, "rr": "CE"}
    v = a._rules(100, _D(True), p, {"i_in": 40, "peak_bid": 110.0})
    assert v["book"] == "council" and v["mode"] == "expiry"
    assert v["sl_px"] == 85.0 and v["sl_pct"] == 15.0
    assert v["hold_s"] == 900 and v["held_s"] == 60.0 and v["clock_left_s"] == 840.0
    assert v["flat_at"] == "15:00"
    assert v["fwd_best"] == 23640.0 and v["fwd_now"] == 23630.0 and v["trail_pts"] == 25.0
    assert v["trail_px"] == 23615.0 and v["trail_give"] == 10.0
    assert v["floor_px"] is None and v["floor_kind"] is None       # +10 % peak: nothing armed yet
    assert v["be_arm_pct"] == 15.0 and v["gb_arm_pct"] == 60.0 and v["pt_arm_pct"] == 70.0
    assert v["pt_armed"] is False and v["peak_pct"] == 10.0


def test_rules_view_break_even_floor_and_put_direction():
    a = _adapter(_Strat(23650.0))
    a.strat.best = 23600.0                                           # a PE: the best forward is the lowest
    p = {"entry": 100.0, "rr": "PE"}
    v = a._rules(100, _D(True), p, {"i_in": 40, "peak_bid": 117.0})
    assert (v["floor_px"], v["floor_kind"]) == (100.0, "BE_LOCK")   # +17 % peak: the floor is the entry
    assert v["trail_px"] == 23625.0 and v["trail_give"] == 50.0     # 23600 + 25; the forward is 50 above the best


def test_rules_view_premium_trail_once_armed():
    s = _Strat(23630.0)
    s.spk = 175.0                                                    # smoothed peak bid +75 %: the premium trail is on
    a = _adapter(s)
    v = a._rules(100, _D(True), {"entry": 100.0, "rr": "CE"}, {"i_in": 40, "peak_bid": 176.0})
    assert v["pt_armed"] is True and v["pt_peak"] == 175.0 and v["pt_trail_px"] == 161.0 and v["pt_give_pct"] == 8.0
    assert v["trail_pts"] is None and v["trail_px"] is None          # the forward trail is switched off
    assert v["floor_kind"] == "GIVEBACK" and abs(v["floor_px"] - 153.2) < 1e-6


def test_rules_view_normal_day_uses_the_ramp_arm_and_1520_flat():
    a = _adapter(_Strat(23630.0))
    a.strat.p = {"sl": 0.15, "trail": 40.0, "hold": 5400}
    v = a._rules(100, _D(False), {"entry": 100.0, "rr": "CE"}, {"i_in": 40, "peak_bid": 105.0})
    assert v["mode"] == "normal" and v["flat_at"] == "15:20" and v["hold_s"] == 5400
    assert v["be_arm_pct"] == 15.0 and v["gb_arm_pct"] is None and v["pt_arm_pct"] is None


def test_giveback_commentary_never_formats_none():
    f = {"giveback_pct": 7.0, "best_pct": 16.0, "ltp": 109.0, "ret_pct": 9.0, "giveback_frac": 0.44, "entry": 100.0,
         "best_pts": 16.0, "stop_dist": None, "stop_spot": None,
         "rules": {"floor_px": 100.0, "floor_kind": "BE_LOCK", "sl_px": 85.0, "sl_pct": 15.0, "clock_left_s": 300.0,
                   "trail_px": 23615.0, "fwd_now": 23630.0}}
    tp = next(t for t in commentary.TEMPLATES if t.key == "giveback")
    for n in range(len(tp.phrasings)):
        text = tp.pick(1, n).format(**{**f, **tp.slots(f)})
        assert "TypeError" not in text and "be lock floor at 100.00" in text, text
    assert commentary.guard_text({"stop_dist": 12.0}) == "the trail sits 12 spot pts away"
    assert commentary.guard_text({}) == "no stop level is set"


def test_engine_publish_drops_the_spot_trail_and_lock_for_council_books():
    src = open(os.path.join(ROOT, "apex", "engine_main.py"), encoding="utf-8").read()
    assert 'council = bool((champ.p or {}).get("council"))' in src
    assert "on_spot=bool((champ.p or {}).get(\"spot_trail\")) and not council" in src
    assert "lock_pct=None if council else" in src
    assert 'time_exit=(p.get("rules") or {}).get("flat_at") if council else' in src


def test_exit_wait_has_its_own_column():
    src = open(os.path.join(ROOT, "apex", "engine", "paper.py"), encoding="utf-8").read()
    assert src.count('pos["exit_fill_delay_s"] = round(waited, 2)') == 2
    assert src.count('pos["fill_delay_s"] = round(waited, 2)') == 1          # the entry only
    assert '"exit_fill_delay_s"]' in src


def test_dashboard_reads_the_rules():
    js = open(os.path.join(ROOT, "apex", "static", "app.js"), encoding="utf-8").read()
    assert 'if (p.rules && p.rules.book === "council") return renderCouncilRail(s, p);' in js
    assert "function renderCouncilRail(s, p)" in js
    assert 'w[0] === "COUNCIL" && w[1] ? w[1] : w[0]' in js                  # the exit chip shows BE_LOCK, not COUNCIL
    assert "councilWhy(r) ||" in js and "FLOOR ARMS AT" in js
    assert 'if (p.council) $("champ").textContent = councilText(s);' in js
    for k in ("BE_LOCK", "SL", "TIME", "FWD_TRAIL", "GIVEBACK", "PREM_TRAIL"):
        assert re.search(rf"\b{k}: \"", js), k
