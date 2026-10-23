"""Council 5 / T07: the heavyweight-basket commentary content (apex/engine/cmt_basket.py).
python3 tests/test_c5_cmt_basket.py  (numpy only; no engine, a fake Market-like object)."""
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timedelta
from types import SimpleNamespace

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_c5b_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from apex import config  # noqa: E402
from apex.engine import commentary  # noqa: E402
from apex.engine import cmt_basket as B  # noqa: E402

SYMS = ["HDFCBANK", "ICICIBANK", "RELIANCE", "BHARTIARTL", "LT", "SBIN", "AXISBANK", "INFY", "KOTAKBANK", "M&M", "TCS",
        "ITC", "BAJFINANCE", "HINDUNILVR"]
W = [10.38, 9.05, 7.58, 5.10, 4.20, 3.79, 3.37, 3.35, 2.93, 2.52, 2.52, 2.52, 2.20, 1.85]
PX0 = [950.0, 1400.0, 1380.0, 1900.0, 3600.0, 860.0, 1150.0, 1500.0, 2100.0, 3400.0, 3000.0, 410.0, 1000.0, 2500.0]
T0 = datetime(2026, 10, 19, 9, 55, 1, tzinfo=config.IST)
T0S = T0.timestamp()
# an instruction = the verb at the start of a sentence / clause, or "... now" / "... it" / "... this" (the noun "the exit" is fine)
INSTR = re.compile(r"(?:^|[.;:!?—]\s*|\s[-–]\s)(hold|exit|sell|buy)\b|\b(hold|exit|sell|buy)\s+(now|it|this|here|the trade)\b", re.I)


# ── a fake engine: rows 0..13 = EQ, 14..27 = FUT, 28 = NIFTY|SPOT, 29 = NIFTY|FUT ──────────────────
class FakeMarket:
    def __init__(self):
        self.n = 30
        self.ltp = np.full((self.n, 1), np.nan)
        self.k = 0
        self.count = 2
        self.snap = {"close": np.array(PX0 + PX0 + [23000.0, 23010.0]) * 0.995, "oi": np.zeros(self.n)}

    def ago(self, secs):
        return 0


def fake_eng(d=-1):
    eng = SimpleNamespace()
    eng.m = FakeMarket()
    eng.m.ltp[:14, 0] = PX0
    eng.m.ltp[14:28, 0] = np.array(PX0) * 1.001
    eng.m.ltp[28, 0] = 23109.7; eng.m.ltp[29, 0] = 23130.0
    eng.key = {f"{s}|EQ": j for j, s in enumerate(SYMS)}
    eng.key.update({f"{s}|FUT": 14 + j for j, s in enumerate(SYMS)})
    eng.key.update({"NIFTY|SPOT": 28, "NIFTY|FUT": 29})
    eng.domino = SimpleNamespace(eq_ids=np.arange(14), eq_w=np.array(W), eq_sym=list(SYMS),
                                 state={"tiles": [{"sym": s, "w": w, "m": 0.0, "z": 0.0, "act": 1.0} for s, w in zip(SYMS, W)]},
                                 episode=None)
    eng.flow = SimpleNamespace(agg_b=np.zeros(30), agg_s=np.zeros(30), cls_b=np.zeros(30, int), cls_s=np.zeros(30, int),
                               cls_bo=np.zeros(30, int), cls_so=np.zeros(30, int), imb_q=np.zeros(30), imb_o=np.zeros(30), lead=np.zeros(30))
    eng.spot_hist = [(T0S - 90, 23101.5), (T0S - 60, 23104.0), (T0S - 30, 23107.0), (T0S, 23109.7)]
    eng.greek = {}
    eng.atm_iv = 0.14
    return eng


def pos(d=-1):
    return {"t_in": T0S, "id": 99, "key": "NIFTY|OPT|2026-10-21|23200|PE", "dir": d, "rr": "PE" if d < 0 else "CE",
            "strike": 23200, "lots": 12, "qty": 780, "entry": 128.45, "expiry": "2026-10-21", "spot_in": 23109.7,
            "best_spot": 23109.7, "stop_spot": 23121.7}


def ctx(s, spot, episode=None):
    return {"now_s": T0S + s, "now_dt": T0 + timedelta(seconds=s), "spot": spot, "fut": spot + 20, "episode": episode,
            "domino": {}, "by_key": {}, "by_id": {}}


def base_facts(s, spot, d=-1, best=None):
    f = {k: None for k in commentary.FACT_KEYS}
    best = spot if best is None else best
    f.update(trade_id=int(T0S), rr="PE" if d < 0 else "CE", dir=d, hold_s=float(s), hold_min=s / 60.0, spot=spot, spot_in=23109.7,
             spot_fav=(spot - 23109.7) * d, best_spot_fav=(best - 23109.7) * d, spot_retrace=(best - spot) * (-d) if False else (spot - best) * (-d),
             pnl_pts=0.0, entry=128.45, qty=780, lots=12, strike=23200)
    return f


def run_facts(eng, memo, s, spot, d=-1, best=None, episode=None):
    f = base_facts(s, spot, d, best)
    book = SimpleNamespace(pos=pos(d), trades=[], capital=100000.0)
    B.extend_facts(f, ctx(s, spot, episode), eng, book, memo)
    return f


def set_px(eng, moves):
    """moves: {sym: pct change vs PX0}"""
    for j, s in enumerate(SYMS):
        eng.m.ltp[j, 0] = PX0[j] * (1 + moves.get(s, 0.0) / 100.0)
        eng.m.ltp[14 + j, 0] = eng.m.ltp[j, 0] * 1.001


# ── 1. the template contract ─────────────────────────────────────────────────────────────────────────
def test_templates_shape_and_honesty():
    keys = [t.key for t in B.TEMPLATES]
    assert len(keys) == len(set(keys)), "duplicate keys"
    assert len(B.TEMPLATES) == 71, len(B.TEMPLATES)
    assert sum(len(t.phrasings) for t in B.TEMPLATES) >= 185
    core_keys = {t.key for t in commentary.TEMPLATES}
    assert not (set(keys) & core_keys), "collides with the core's keys"
    for t in B.TEMPLATES:
        assert len(t.phrasings) >= 2, t.key
        assert t.kind in commentary.KINDS and t.tone in commentary.TONES, t.key
        assert 0 <= t.prio <= 100
        for p in t.phrasings:
            assert not INSTR.search(p), f"{t.key}: instruction word in {p!r}"
    # T07 honesty: stock futures / flow are low-prio colour or present-tense; warnings >= 75 keep the core's warning tone
    for k in ("stock_futs_ahead", "stock_futs_behind", "basis_widening"):
        t = next(x for x in B.TEMPLATES if x.key == k)
        assert t.tone == "information" and t.prio <= 20
    for t in B.TEMPLATES:
        if t.tone == "warning":
            assert t.prio >= 75, t.key
    assert all(k in B.FACTS for k in ("eq_breadth_with", "eq_breadth_against", "eq_air", "eq_swing_sym", "eq_flips", "eq_fut_lead"))
    assert len(B.FACTS) == len(set(B.FACTS))


def test_predicates_and_phrasings_never_raise():
    empty = {k: None for k in commentary.FACT_KEYS}
    empty.update({k: None for k in B.FACTS})
    for t in B.TEMPLATES:
        t.when(empty)                     # must not raise on None
        sl = dict(empty, **B.S(empty))
        for p in t.phrasings:
            p.format(**sl)
    # a fully populated synthetic dict
    eng = fake_eng(); memo = SimpleNamespace(trade_id=int(T0S), N_in=23109.7)
    B.extend_memo(memo, ctx(0, 23109.7), eng, pos())
    set_px(eng, {"ICICIBANK": -0.9, "HDFCBANK": -0.4, "BHARTIARTL": -0.5, "RELIANCE": +0.15, "INFY": +0.1, "SBIN": -0.3})
    f = run_facts(eng, memo, 60, 23084.2, best=23080.0, episode={"dir": -1, "age": 100.0, "type": "BASKET-LED", "first": "AXISBANK", "n_cross": 4})
    for k in B.FACTS:
        assert k in f, k
    sample = {"eq_flip_against": {"sym": "INFY", "was": 1.2, "now": -0.8}, "eq_flip_with": {"sym": "TCS", "was": -0.9, "now": 0.7},
              "eq_new_helper": {"sym": "SBIN", "turn": 1.1, "help": 1.3}, "eq_sector_against": {"sector": "IT", "pts": -1.4, "n": 2, "syms": ["INFY", "TCS"]},
              "eq_opposite_pair": {"sector": "Banks", "a": "SBIN", "pa": 1.2, "b": "AXISBANK", "pb": -1.1},
              "eq_big_bank_against": {"sym": "HDFCBANK", "help": -1.5, "w": 10.38, "pct": 0.06},
              "eq_pressed_name": ("SBIN", 40.0, 1.3), "eq_fought_name": ("RELIANCE", 50.0, -1.1), "eq_giveback_top": [("ICICIBANK", 2.0), ("HDFCBANK", 1.0)],
              "eq_made": [("ICICIBANK", 8.2), ("HDFCBANK", 3.2)], "eq_pre_top": [("HDFCBANK", 5.7), ("ICICIBANK", 1.2)], "eq_pre_bot": [("RELIANCE", -4.2)],
              "eq_flow_with": [("SBIN", 40.0)], "eq_flow_against": [("RELIANCE", 50.0)], "eq_refilling": ["SBIN", "LT"], "eq_leavers": ["TCS", "ITC"],
              "eq_wave_with": ["SBIN", "LT", "ITC"], "eq_wave_against": ["INFY", "TCS", "M&M"], "eq_flips": [{"sym": "INFY", "was": 1.2, "now": -0.8}],
              "eq_turn": [{"sym": "SBIN", "turn": 1.1, "help": 1.3}], "eq_pre_makers": ["HDFCBANK"], "eq_pre_rows": [], "eq_syms_fresh": list(SYMS),
              "eq_ep_type": "BASKET-LED", "eq_first_mover": "AXISBANK", "eq_first_mover_t": "09:51:22", "eq_best_hms": "09:57:28",
              "eq_top_sym": "ICICIBANK", "eq_top2_sym": "HDFCBANK", "eq_top3_sym": "BHARTIARTL", "eq_bot_sym": "RELIANCE", "eq_conc_sym": "ICICIBANK",
              "eq_top60_sym": "ICICIBANK", "eq_swing_sym": "ICICIBANK", "eq_giveback_max_sym": "ICICIBANK", "eq_lone_sector": "Banks",
              "eq_day_leader": "HDFCBANK", "eq_day_laggard": "INFY", "rr": "PE", "dir": -1, "ep_type": "BASKET-LED", "sellers_q": "HOLDING", "sellers_o": "HOLDING",
              "regime": "RANGE", "first_mover": "AXISBANK", "top_helper": "ICICIBANK", "top_hurter": "RELIANCE", "pending_reason": None,
              "straddle_state": "FLAT", "flatten_hms": "15:05", "time_hms": "09:56:01", "contrib": [], "helpers": [], "hurters": []}
    full = dict(f)
    for k, v in list(full.items()):
        if v is None:
            full[k] = sample.get(k, 1.0)
        elif k in sample:
            full[k] = sample[k]
    for t in B.TEMPLATES:
        t.when(full)
        sl = dict(full, **B.S(full))
        for p in t.phrasings:
            p.format(**sl)
    for t in B.TEMPLATES:                 # and on the real facts
        sl = dict(f, **B.S(f))
        for p in t.phrasings:
            p.format(**sl)


# ── 2. the facts on a hand-built tape (09:55 PE style) ──────────────────────────────────────────────
def test_facts_on_a_bank_led_pe():
    eng = fake_eng(); memo = SimpleNamespace(trade_id=int(T0S), N_in=23109.7)
    B.extend_memo(memo, ctx(0, 23109.7), eng, pos())
    f0 = run_facts(eng, memo, 0, 23109.7)
    assert f0["eq_n"] == 14 and f0["eq_breadth_with"] == 0 and f0["eq_breadth_against"] == 0
    assert f0["eq_pre_ref_s"] == 60 and f0["eq_day_with"] is not None
    # +60 s: six names fall with the PE (ICICIBANK -0.6 % the leader), RELIANCE +0.15 % against it
    MV = {"ICICIBANK": -0.6, "HDFCBANK": -0.35, "BHARTIARTL": -0.3, "SBIN": -0.3, "LT": -0.2, "AXISBANK": -0.2, "RELIANCE": 0.15}
    for s in range(1, 61):
        set_px(eng, {k: v * s / 60 for k, v in MV.items()})
        f = run_facts(eng, memo, s, 23109.7 - 25.5 * s / 60, best=23109.7 - 25.5 * s / 60)
    assert f["eq_top_sym"] == "ICICIBANK", f["eq_top_sym"]
    exp = 0.0905 * 0.006 * 23109.7
    assert abs(f["eq_top_help"] - exp) < 0.05, (f["eq_top_help"], exp)
    assert f["eq_bot_sym"] == "RELIANCE" and f["eq_bot_help"] < 0
    assert f["eq_breadth_with"] == 6 and f["eq_breadth_against"] == 1, (f["eq_breadth_with"], f["eq_breadth_against"])
    assert f["eq_sector_banks_with"] == 4 and f["eq_sector_banks"] > 0
    assert not f["eq_air"] and not f["eq_hot"]
    assert abs(f["eq_basket_pts_scaled"] - (sum(r["pts"] for r in f["eq_rows"]) * -1 * 100 / sum(W))) < 1e-6
    assert f["eq_gap_vs_print"] is not None and f["eq_ratio"] is not None
    assert f["eq_with60"] == 0 and f["eq_breadth_chg60"] == 6
    assert f["eq_first_mover"] is None
    assert f["eq_big_bank_against"] is None
    # the lead_helper / concentrated predicates see it
    assert next(t for t in B.TEMPLATES if t.key == "lead_helper").when(f)
    # 60 s later RELIANCE flips with the trade (it was meaningfully against)
    for s in range(61, 121):
        set_px(eng, dict(MV, RELIANCE=-0.3))
        f = run_facts(eng, memo, s, 23080.0, best=23080.0)
    assert f["eq_flip_with"] and f["eq_flip_with"]["sym"] == "RELIANCE", f["eq_flips"]
    assert "RELIANCE" in [x["sym"] for x in f["eq_flips"]]
    # a give-back: ICICIBANK bounces, the print pulls back 12 -> swing stock ICICIBANK
    for s in range(121, 151):
        set_px(eng, dict(MV, RELIANCE=-0.3, ICICIBANK=-0.25))
        f = run_facts(eng, memo, s, 23092.0, best=23080.0)
    assert f["eq_swing_sym"] == "ICICIBANK" and f["eq_swing_giveback"] > 1.0, (f["eq_swing_sym"], f["eq_swing_giveback"])
    assert abs(f["eq_print_giveback"] - 12.0) < 1e-6
    assert next(t for t in B.TEMPLATES if t.key == "swing_stock").when(f)
    lines = B.review_lines({"pnl_pts": 5.0, "t_in": T0S}, f)
    assert lines and any("ICICIBANK" in x for x in lines), lines
    # a flip AGAINST: ICICIBANK crosses from +help to -help within 60 s -> warning template
    for s in range(151, 181):
        set_px(eng, dict(MV, RELIANCE=-0.3, ICICIBANK=+0.3, HDFCBANK=+0.3))
        f = run_facts(eng, memo, s, 23100.0, best=23080.0)
    assert f["eq_flip_against"] and f["eq_flip_against"]["sym"] in ("ICICIBANK", "HDFCBANK")
    assert f["eq_big_bank_against"] is not None
    assert next(t for t in B.TEMPLATES if t.key == "flip_against").when(f)


def test_honesty_guard_thin_move_suppresses_cheers():
    """T07 §4: with = 2, against = 9, print +12 -> no 'confidence' remark, the warning ones fire."""
    eng = fake_eng(); memo = SimpleNamespace(trade_id=int(T0S), N_in=23109.7)
    B.extend_memo(memo, ctx(0, 23109.7), eng, pos())
    mv = {s: +0.12 for s in SYMS[:9]}
    mv.update({"ITC": -0.2, "HINDUNILVR": -0.2})
    for s in range(1, 31):
        set_px(eng, mv)
        f = run_facts(eng, memo, s, 23109.7 - 12.0, best=23109.7 - 12.0)
    assert f["eq_breadth_with"] == 2 and f["eq_breadth_against"] == 9, (f["eq_breadth_with"], f["eq_breadth_against"])
    assert f["eq_air"]
    fired = [t for t in B.TEMPLATES if t.kind != "review" and t.when(f)]
    assert not [t.key for t in fired if t.tone in ("confidence", "praise")], [t.key for t in fired if t.tone in ("confidence", "praise")]
    assert {"thin_move", "hurters_outnumber_helpers_pts"} <= {t.key for t in fired}, [t.key for t in fired]
    # through the core selector: the warning wins the second
    c = commentary.Commentary("2026-10-19", templates=list(B.TEMPLATES))
    c._select(ctx(30, 23097.7), f)
    assert c.items and c.items[0]["tone"] == "warning", c.items


def test_nan_print_lowers_the_denominator():
    eng = fake_eng(); memo = SimpleNamespace(trade_id=int(T0S), N_in=23109.7)
    eng.m.ltp[SYMS.index("HDFCBANK"), 0] = np.nan            # a NaN at entry with no fresh print behind it
    B.extend_memo(memo, ctx(0, 23109.7), eng, pos())
    f = run_facts(eng, memo, 5, 23105.0)
    assert f["eq_n"] == 13 and "HDFCBANK" not in f["eq_syms_fresh"]
    assert B.S(f)["n"] == "13"
    for t in B.TEMPLATES:
        for p in t.phrasings:
            assert not re.search(r"\bnan\b", p.format(**dict(f, **B.S(f))), re.I)


def test_flow_runs_and_waves():
    eng = fake_eng(); memo = SimpleNamespace(trade_id=int(T0S), N_in=23109.7)
    B.extend_memo(memo, ctx(0, 23109.7), eng, pos())
    j = SYMS.index("SBIN")
    eng.flow.agg_s[j] = 500.0                                  # net selling in SBIN = with a PE
    eng.flow.agg_b[SYMS.index("RELIANCE")] = 300.0             # net buying in RELIANCE = against a PE
    for s in range(1, 100):
        set_px(eng, {"SBIN": -0.3, "RELIANCE": +0.1})
        f = run_facts(eng, memo, s, 23106.0)
    r = {x["sym"]: x for x in f["eq_rows"]}
    assert r["SBIN"]["run_with"] >= 90 and r["SBIN"]["run_against"] == 0, r["SBIN"]
    assert r["RELIANCE"]["run_against"] >= 90, r["RELIANCE"]
    assert f["eq_pressed_name"][0] == "SBIN" and f["eq_fought_name"][0] == "RELIANCE"
    assert f["eq_top_run_with"] >= 90
    assert next(t for t in B.TEMPLATES if t.key == "helper_pressed").when(f)
    eng.domino.state["tiles"][0]["z"] = -2.5; eng.domino.state["tiles"][1]["z"] = -2.1; eng.domino.state["tiles"][2]["z"] = -3.0
    f = run_facts(eng, memo, 100, 23106.0)
    assert len(f["eq_wave_with"]) == 3
    assert next(t for t in B.TEMPLATES if t.key == "recruit_wave").when(f)


def test_extend_facts_never_raises_and_is_fast():
    eng = fake_eng(); memo = SimpleNamespace(trade_id=int(T0S), N_in=23109.7)
    broken = SimpleNamespace(m=None, domino=None, key=None)
    f = base_facts(0, 23109.7)
    B.extend_facts(f, ctx(0, 23109.7), broken, SimpleNamespace(pos=pos(), trades=[]), memo)   # no memo.bk, broken engine
    assert all(k in f for k in B.FACTS)
    B.extend_memo(memo, ctx(0, 23109.7), eng, pos())
    book = SimpleNamespace(pos=pos(), trades=[], capital=100000.0)
    inputs = [(base_facts(s, 23100.0, best=23095.0), ctx(s, 23100.0)) for s in range(1000)]
    set_px(eng, {"ICICIBANK": -0.5, "RELIANCE": 0.1, "SBIN": -0.2, "LT": 0.1})
    best = None
    for _ in range(3):                                   # the box is shared and noisy: best of three
        t0 = time.perf_counter()
        for f, c in inputs:
            B.extend_facts(f, c, eng, book, memo)
        ms = (time.perf_counter() - t0) * 1000
        best = ms if best is None else min(best, ms)
    print(f"  1000 extend_facts: {best:.0f} ms ({best / 1000:.3f} ms each)")
    assert all(k in inputs[-1][0] for k in B.FACTS)
    assert best < 300, best


def test_loaded_by_the_core():
    mods = commentary.load_content()
    assert any(m.__name__ == "apex.engine.cmt_basket" for m in mods)
    allt = commentary.all_templates(mods)
    keys = [t.key for t in allt]
    assert len(keys) == len(set(keys))
    assert "lead_helper" in keys


if __name__ == "__main__":
    n = 0
    for k, fn in list(globals().items()):
        if k.startswith("test_"):
            fn(); n += 1
            print(f"ok  {k}")
    print(f"{n} tests passed · {len(B.TEMPLATES)} templates · {sum(len(t.phrasings) for t in B.TEMPLATES)} phrasings · {len(B.FACTS)} facts")
