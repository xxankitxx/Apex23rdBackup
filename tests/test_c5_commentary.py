"""Council 5: the commentary core with all three content modules loaded.  python tests/test_c5_commentary.py"""
import json
import os
import re
import sys
import tempfile
import time

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c5com_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta  # noqa: E402

from apex import config  # noqa: E402
from apex.engine import commentary as cm  # noqa: E402

MODS = cm.load_content(print)
TEMPLATES = cm.all_templates(MODS)
ALL_FACTS = list(cm.FACT_KEYS) + [k for m in MODS for k in getattr(m, "FACTS", [])]
T0 = datetime(2026, 10, 21, 10, 0, tzinfo=config.IST)
IMPERATIVE = re.compile(r"(^|[.!?]\s+)(Hold|Exit|Sell|Buy|Book|Square off|Get out|Stay in|Cut)\b(?![- ]leads| it)")


def _ctx(s):
    return {"now_s": 1000.0 + s, "now_dt": T0 + timedelta(seconds=s)}


def _full_facts(s=60.0):
    """A plausible, fully populated facts dict (base + every module key set to something non-None)."""
    f = {k: None for k in ALL_FACTS}
    f.update(trade_id=1792382221, rr="CE", strike=25100, dir=1, lots=12, qty=780, entry=128.45, capital_deployed=100191.0,
             hold_s=s, hold_min=s / 60.0, time_hms="10:01:00", zero_dte=False, ltp=137.5, bid=137.3, ask=137.7,
             pnl_pts=9.05, pnl_rs=7059.0, ret_pct=7.0, best_pts=10.0, best_pct=7.8, giveback_pts=0.95, giveback_pct=0.7,
             giveback_frac=0.095, spot=25095.0, spot_in=25080.0, spot_fav=15.0, best_spot_fav=16.0, stop_spot=25084.0,
             stop_dist=11.0, trail_armed=True, locked_pts=4.0, delta=0.6, delta_in=0.55, theta_min=-0.04, vega=12.0,
             iv=14.4, iv_in=14.2, iv_chg=0.2, iv_pts=2.4, iv_share=0.26, sync_for=0.6, sync_against=0.1, z_for=1.5,
             top_helper="HDFCBANK", top_helper_pts=4.0, n_helping=5, top_hurter="RELIANCE", top_hurter_pts=-1.0, n_hurting=2,
             contrib=[{"sym": "HDFCBANK", "pts": 4.0, "z15": 1.0, "w": 10.4}], helpers=["HDFCBANK"], hurters=["RELIANCE"],
             sellers_q="HOLDING", sellers_o="HOLDING", min_to_flatten=300.0, flatten_hms="15:35", trades_today=3,
             wins_today=2, streak=2, realised_rs=12000.0, capital=112000.0, day_pct=12.0, gap_on=False, exit_pending=False,
             quote_age=0.2, spot_age=0.3, regime="DIRECTIONAL", regime_with=1)
    for k in ALL_FACTS:
        if f[k] is None:
            f[k] = 1.0 if not k.endswith(("_txt", "_hms", "_sym", "_why", "_kind", "_state", "_text", "_grade", "_verdict")) else "x"
    return f


def test_catalogue_shape():
    keys = [t.key for t in TEMPLATES]
    assert len(TEMPLATES) >= 200 and len(set(keys)) == len(keys), (len(TEMPLATES), len(keys) - len(set(keys)))
    assert sum(len(t.phrasings) for t in TEMPLATES) >= 600
    for t in TEMPLATES:
        assert t.kind in cm.KINDS and t.tone in cm.TONES and len(t.phrasings) >= 2 and 0 <= t.prio <= 100, t.key


def test_every_predicate_and_phrasing_survive_empty_and_full_facts():
    empty = {k: None for k in ALL_FACTS}
    empty.update(trade_id=1, hold_s=0.0)
    full = _full_facts()
    core_keys = {t.key for t in cm.TEMPLATES}
    for t in TEMPLATES:
        # the modules' own suites feed each one a properly typed synthetic dict; here the full dict is typed for the core
        for f in ((empty, full) if t.key in core_keys else (empty,)):
            try:
                t.when(f)                                        # must not raise on empty facts
            except Exception as e:
                raise AssertionError(f"{t.key}: when() raised {type(e).__name__}: {e}")
            slots = dict(f)
            if t.slots:
                try:
                    slots.update(t.slots(f))
                except Exception:
                    assert f is empty, f"{t.key}: slots() raised on a full facts dict"   # the core tolerates it on empty facts
            for ph in t.phrasings:
                try:
                    ph.format(**slots)
                except KeyError as e:
                    raise AssertionError(f"{t.key}: missing slot {e} in {ph!r}")
                except (ValueError, TypeError):
                    pass                                         # a None into a numeric format on the empty dict is tolerated by the core


def test_no_imperatives_in_phrasings():
    bad = [(t.key, ph) for t in TEMPLATES for ph in t.phrasings if IMPERATIVE.search(ph)]
    assert not bad, bad[:5]


def test_selector_rate_limits_and_warning_cooldown():
    c = cm.Commentary("2026-10-21", templates=TEMPLATES, paper_dir=None)
    f = _full_facts()
    fired = []
    for s in range(0, 120):
        f2 = dict(f, hold_s=float(s), hold_min=s / 60.0)
        c._verdict(_ctx(s), f2, 12.0)
        c._select(_ctx(s), f2)
        fired.append(len(c.items))
    items = list(c.items)
    assert items, "nothing fired on a fully populated trade"
    # at most 3 non-warning remarks in any 10-s window
    ts = sorted(it["t"] for it in items if it["tone"] != "warning")
    for i, t0 in enumerate(ts):
        assert sum(1 for x in ts[i:] if x < t0 + 10.0) <= 3
    # the same key never twice inside its cool-down unless a step fact moved (the facts here do not move)
    by_key = {}
    for it in sorted(items, key=lambda x: x["t"]):
        tp = next(t for t in TEMPLATES if t.key == it["key"])
        if it["key"] in by_key:
            assert it["t"] - by_key[it["key"]] >= tp.cooldown_s or tp.step, it["key"]
        by_key[it["key"]] = it["t"]


def test_phrasing_choice_is_deterministic_per_trade():
    for t in TEMPLATES[:50]:
        assert t.pick(1792382221, 0) == t.pick(1792382221, 0)
        assert t.pick(1792382221, 0) in t.phrasings


def test_blob_and_tape():
    d = tempfile.mkdtemp()
    c = cm.Commentary("2026-10-21", templates=TEMPLATES, paper_dir=d)
    f = _full_facts()
    for s in range(0, 30):
        c._verdict(_ctx(s), f, 12.0)
        c._select(_ctx(s), f)
    v = c.view()
    assert v["verdict"]["state"] == v["verdict"]["level"] in cm.LEVELS
    assert len(json.dumps(v)) < 40_000
    lines = open(os.path.join(d, "commentary_2026-10-21.jsonl"), encoding="utf-8").read().splitlines()
    assert lines and all(json.loads(x) for x in lines)


def test_performance():
    c = cm.Commentary("2026-10-21", templates=TEMPLATES, paper_dir=None)
    f = _full_facts()
    t0 = time.perf_counter()
    for s in range(0, 500):
        c._verdict(_ctx(s), f, 12.0)
        c._select(_ctx(s), f)
    per = (time.perf_counter() - t0) / 500 * 1000
    assert per < 1.5, f"{per:.2f} ms per evaluation"


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"):
            fn(); print("ok", k)
