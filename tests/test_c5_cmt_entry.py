"""Council 5, T06: entry-quality commentary (apex/engine/cmt_entry.py). python3 tests/test_c5_cmt_entry.py (numpy only)."""
import os
import re
import sys
import tempfile
import time
from collections import deque
from datetime import datetime
from types import SimpleNamespace

os.environ.setdefault("APEX_DATA", tempfile.mkdtemp(prefix="apex_test_c5e_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from apex import config  # noqa: E402
from apex.engine import cmt_entry as M  # noqa: E402
from apex.engine import commentary as C  # noqa: E402

T0 = 1792385984.0
DT = datetime(2026, 10, 19, 13, 29, 56, tzinfo=config.IST)


# ── a synthetic, fully populated facts dict (base ∪ T06) ──────────────────────────────────────────
def synthetic():
    f = {k: None for k in C.FACT_KEYS}
    f.update(trade_id=1792382221, rr="PE", strike=22900, dir=-1, lots=93, qty=6045, entry=78.25, capital_deployed=473021.0,
             hold_s=0.0, hold_min=0.0, time_hms="13:29:56", zero_dte=True, ltp=78.25, bid=78.0, ask=78.5, pnl_pts=0.0, pnl_rs=0.0,
             ret_pct=0.0, best_pts=0.0, best_pct=0.0, giveback_pts=0.0, giveback_pct=0.0, giveback_frac=0.0, entry_over_mid=0.65,
             spread_in=0.3, spread_now=0.5, spread_typical=0.25, entry_cost_rs=3929.0, spot=22937.0, spot_in=22937.0, spot_fav=0.0,
             best_spot_fav=0.0, stop_spot=22949.0, stop_dist=12.0, trail_armed=False, locked_pts=-12.0, delta=-0.67, delta_in=-0.67,
             theta_min=-0.09, theta_rs_min=-544.0, vega=4.1, iv=29.8, iv_in=29.8, iv_chg=0.0, iv_pts=0.0, atm_iv=31.0, atm_iv_in=31.0,
             contrib=[], helpers=[], hurters=[], n_helping=0, n_hurting=0, sync_for=0.3, sync_against=0.0, z_for=1.2,
             sellers_q="HOLDING", sellers_o="HOLDING", basis=24.0, basis_in=24.0, straddle_state="EXPANDING", straddle_px=96.0,
             straddle_vwap=92.0, straddle_in=96.0, regime="RANGE", regime_dir=0, regime_with=0, wall_level=22800.0, wall_room=137.0,
             wall_room_in=137.0, min_to_flatten=90.0, flatten_hms="15:00", min_to_0dte=90.0, trades_today=25, wins_today=15,
             streak=1, realised_rs=300000.0, capital=473000.0, day_pct=373.0, best_trade_today=30.6, gap_on=False, quote_age=0.3,
             exit_pending=False)
    f.update({k: None for k in M.FACTS})
    f.update(over_mid=0.65, over_mid_pct=0.83, over_mid_rs=3929.0, mid_in=77.6, entry_bid=77.45, entry_ask=77.75, spread_pct=0.38,
             roundtrip_rs=1813.0, prem_win_s=300.0, lo5=61.0, hi5=78.25, pos_in_range=1.0, p5=66.0, rise5=18.6, vwap5=70.2,
             vwap_kind="VWAP", vs_vwap=8.05, vs_vwap_pct=11.5, iv_run_pct=92.0, iv_day_lo=26.5, iv_day_hi=31.2, iv_day_med=29.0,
             iv_cover_min=240.0, iv_vs30=-0.6, iv_rise=0.4, iv_other=21.0, skew=8.8, iv_late_why="iv +0.4 in 5 min",
             money=37.0, money_fut=61.0, extr_pct=52.7, intr_pct=47.3, band_fallback=False, lot_cost=5086.0, break_level=22944.0,
             chase_pts=7.0, s60=5.0, s300=6.0, s1800=-25.0, sigma15=5.0, range5=22.0, regime_why="range, no direction", hour=13,
             time_in="13:29:56", trail_pts=12.0, stop_rs=48602.0, stop_prem=8.04, rs_per_pt=4050.0, vol_win_s=300.0, vol_win=3400000.0,
             qty_vs_vol=0.0018, ss_in=182000.0, sso_in=410.0, qty_vs_ss=0.033, slices=2, prev_lots=70, prev_ret=8.0, prev_reason="TRAIL",
             prev_key="NIFTY|OPT|2026-10-19|22900|PE", same_key=True, since_exit=428.0, prev_stop_rs=36000.0, strad_5=3.5,
             strad_state_in="EXPANDING", strad_px_in=96.0, strad_vwap_in=92.0, room_in=137.0, wall_in=22800.0, wall_oi_in=4.2e6,
             chain_age_in=45.0, room_why="next wall 22800 is 137 pts away", trade_age_in=0.8, lag_s_in=0.4, vix=15.1, vix_lo=14.2,
             vix_hi=15.4, day_over_mid_rs=18000.0, day_trades=26, day_over_mid_pct=0.3, entry_score=-6, entry_grade="E",
             entry_verdict="poor entry", entry_reasons=["only 37 pts ITM vs spot, 53 % extrinsic", "spot only +6 / 5 min, no push",
                                                       "premium at its 5-min high"],
             entry_fired=[], ret_now=-1.2, spot_vs_in=-3.0, best_vs_in=2.0, entry_look="unproven", cost_status="still owed")
    return f


INSTRUCT = re.compile(r"(?:^|[.!?—:]\s+)(Hold|Exit|Sell|Buy|Add|Cut|Keep|Consider|Watch|Do not|Don't|Book|Square off|Get out|Stay in)\b"
                      r"|\byou should\b|\bguaranteed\b|\bsure to\b|\bwill (?:win|pay off|work out|make money)\b")


def test_shape():
    assert len(M.TEMPLATES) == 59, len(M.TEMPLATES)
    assert sum(len(t.phrasings) for t in M.TEMPLATES) == 198
    keys = [t.key for t in M.TEMPLATES]
    assert len(set(keys)) == len(keys)
    assert not (set(M.FACTS) & set(C.FACT_KEYS)), set(M.FACTS) & set(C.FACT_KEYS)
    for t in M.TEMPLATES:
        assert len(t.phrasings) >= 2, t.key
        assert t.kind in C.KINDS and t.tone in C.TONES, t.key
        assert t.once and t.slots is not None, t.key
        for p in t.phrasings:
            assert not INSTRUCT.search(p), (t.key, p)
        if t.tone == "confidence":
            for p in t.phrasings:
                assert re.search(r"\{[a-z_0-9]+:[^}]*[df]\}|\d", p), ("confidence must cite a number", t.key, p)


def test_predicates_and_phrasings():
    empty = {k: None for k in C.FACT_KEYS}
    empty.update({k: None for k in M.FACTS})
    full = synthetic()
    fired = []
    for t in M.TEMPLATES:
        assert t.when(empty) in (True, False, None) or True       # must not raise
        r = t.when(full)
        assert isinstance(bool(r), bool)
        if r:
            fired.append(t.key)
        sl = dict(full); sl.update(t.slots(full))
        for p in t.phrasings:
            txt = p.format(**sl)
            assert "{" not in txt and "nan" not in txt.lower().split(), (t.key, txt)
        sl0 = dict(empty); sl0.update(t.slots(empty))
        for p in t.phrasings:
            p.format(**sl0)                                        # None renders as "—", never a crash
    assert "entry.stupid" in fired and "strike.lottery" in fired and "chase.no_push" in fired, fired
    assert "entry.clean" not in fired and "fill.clean" not in fired


# ── a fake engine: enough of Market / domino / greek / straddle / pressure to drive extend_memo ─────
def fake_eng(now, row=7, entry=124.0, spot=23290.0):
    m = SimpleNamespace()
    n, WIN = 20, 600
    m.t = np.zeros(WIN); m.ltp = np.full((n, WIN), np.nan); m.ttq = np.full((n, WIN), np.nan)
    m.ss = np.full((n, WIN), np.nan); m.sso = np.full((n, WIN), np.nan)
    m.count = WIN; m.k = WIN - 1
    for j in range(WIN):
        m.t[j] = now - (WIN - 1 - j) * 0.1
        m.ltp[row, j] = entry - 6.0 + 6.0 * j / WIN           # rising into the entry
        m.ttq[row, j] = 3.0e6 + 400.0 * j
    m.ss[row, m.k] = 182000.0; m.sso[row, m.k] = 410.0
    m.snap = {"ltt": np.zeros(n), "recv_ns": np.zeros(n, dtype=np.int64)}

    def ago(secs):
        return int(np.argmin(np.abs(m.t - (now - secs))))
    m.ago = ago
    m.change = lambda arr, secs: arr[:, m.k] - arr[:, ago(secs)]
    eng = SimpleNamespace(m=m)
    eng.domino = SimpleNamespace(eq_ids=np.zeros(0, dtype=int), eq_w=np.zeros(0), eq_sym=[], state={"sigma15": 7.0})
    eng.greek = {row: {"delta": -0.74, "iv": 28.0, "theta_min": -0.06, "vega": 5.0}, 8: {"delta": 0.3, "iv": 22.0}}
    eng.key = {"NIFTY|OPT|2026-10-19|23200|PE": row, "NIFTY|OPT|2026-10-19|23200|CE": 8}
    eng.atm_iv = 0.29
    eng.iv_hist = deque([(now - 900 + i, 0.27 + 0.00002 * i) for i in range(900)], maxlen=900)
    eng.iv_change = lambda secs: 0.6
    eng.spot_hist = deque([(now - 720 + i, spot - 30.0 + 30.0 * i / 720) for i in range(721)])   # +30 over 12 min (down-move for a PE: -30)
    eng.fut_hist = deque([(now - 2100 + i, spot + 3 + 10 * i / 2100) for i in range(2101)])
    eng.straddle = SimpleNamespace(view=lambda: {"px": 96.0, "vwap": 99.0, "state": "COMPRESSING", "slope5": -2.6, "atm": 23300})
    eng.pressure = SimpleNamespace(destination=lambda sp, d: {"level": 22900.0 if d < 0 else 23700.0, "room": abs(sp - (22900.0 if d < 0 else 23700.0))},
                                   walls_up=[(23700.0, 5.0e6)], walls_dn=[(22900.0, 4.2e6)], chain_age=40.0)
    eng.regime = SimpleNamespace(view=lambda: {"state": "DIRECTIONAL", "dir": -1, "text": "down, er5 0.7"})
    eng.heroes = lambda: [(row, "PE", 23200)]
    eng.data_health = lambda snap: {"lag_s": 0.3}
    eng.t = SimpleNamespace(c=lambda k: 14.3 if k == "vix" else None)
    eng.champion = "spot_dc12_t12"
    return eng


def fake_pos(now, row=7, entry=124.0, spot=23290.0):
    return {"key": "NIFTY|OPT|2026-10-19|23200|PE", "id": row, "strike": 23200, "rr": "PE", "expiry": "2026-10-19", "lots": 20, "qty": 1300,
            "slices": 1, "entry": entry, "entry_bid": 124.3, "entry_ask": 124.6, "t_in": now, "time_in": "09:55:01", "dir": -1,
            "fut_in": spot + 3, "spot_in": spot, "delta_in": -0.74, "iv_in": 27.2, "why": "spot 12-min low 23294.0 broke", "advisors": {},
            "peak_pts": 0.0, "trade_age_in": 1.2, "mid_in": 124.45, "band_fallback": False, "best_spot": spot, "stop_spot": spot + 12}


def fake_ctx(now, spot=23290.0, dt=None):
    return {"now_s": now, "now_dt": dt or datetime(2026, 10, 19, 9, 55, 1, tzinfo=config.IST), "spot": spot, "fut": spot + 3,
            "spot_hi": spot + 40, "spot_lo": spot + 4, "domino": {"sigma15": 7.0}, "range5": 24.0, "trend30": -10.0,
            "regime": {"state": "DIRECTIONAL", "dir": -1}, "by_key": {}, "by_id": {}, "iv_rise_since_onset": 0.6}


def test_extend_memo_and_card():
    now = T0
    eng = fake_eng(now)
    pos = fake_pos(now)
    prev = {"key": pos["key"], "lots": 10, "qty": 650, "ret_pct": -3.0, "reason": "STOP", "t_out": now - 200, "delta_in": -0.7,
            "mid_in": 100.0, "entry": 100.3}
    book = SimpleNamespace(pos=pos, trades=[prev], p={"spot_trail": 12.0}, capital=180000.0)
    eng.books = {"spot_dc12_t12": book}
    memo = SimpleNamespace(t_in=now, trade_id=int(now))
    q = M.extend_memo(memo, fake_ctx(now), eng, pos)
    assert set(q) == set(M.FACTS)
    assert abs(q["over_mid"] - (-0.45)) < 1e-9 and q["entry_bid"] == 124.3
    assert q["money"] == -90 and q["extr_pct"] == 100.0          # a 23200 PE with spot 23290 is 90 OTM: all extrinsic → lottery
    assert q["prem_win_s"] is not None and 50 <= q["prem_win_s"] <= 60 and 0.99 <= q["pos_in_range"] <= 1.0
    assert q["vwap_kind"] == "VWAP" and q["vol_win"] > 0 and q["qty_vs_vol"] is not None
    assert q["iv_run_pct"] is not None and q["iv_cover_min"] >= 14 and q["iv_vs30"] is None     # only 15 min of IV history
    assert q["iv_other"] == 22.0 and abs(q["skew"] - 5.2) < 1e-9
    assert q["break_level"] == 23294.0 and abs(q["chase_pts"] - 4.0) < 1e-9
    assert q["s300"] is not None and q["s60"] is not None and q["s1800"] == 10.0
    assert q["sigma15"] == 7.0 and q["range5"] == 24.0 and q["hour"] == 9
    assert q["ss_in"] == 182000.0 and abs(q["qty_vs_ss"] - 1300 / 182000.0) < 1e-12
    assert q["prev_lots"] == 10 and q["same_key"] and q["since_exit"] == 200 and q["prev_stop_rs"] == 12 * 0.7 * 650
    assert q["strad_5"] == -2.6 and q["room_in"] == 390.0 and q["wall_oi_in"] == 4.2e6 and q["chain_age_in"] == 40.0
    assert q["lag_s_in"] == 0.3 and q["vix"] == 14.3 and q["trade_age_in"] == 1.2
    assert q["day_trades"] == 2 and abs(q["day_over_mid_rs"] - (0.3 * 650 - 0.45 * 1300)) < 1e-6
    assert q["entry_grade"] in "ABCDE" and q["entry_reasons"]
    # an in-the-money put: spot below the strike → sweet spot
    pos2 = dict(pos, spot_in=23110.0, fut_in=23135.0)
    q2 = M.extend_memo(memo, fake_ctx(now, spot=23110.0), eng, pos2)
    assert q2["money"] == 90 and q2["money_fut"] == 65 and abs(q2["extr_pct"] - 100 * 34 / 124) < 1e-9
    assert q2["entry_grade"] in ("A", "B"), (q2["entry_score"], q2["entry_reasons"])
    f = synthetic(); f.update(q2)
    card = M.entry_card(f)
    assert card["grade"] == q2["entry_grade"] and len(card["lines"]) == 3 and "19 Oct" in card["lines"][2]
    assert card["lines"][0].startswith("Grade ") and " · " in card["lines"][1]
    # the card is None without a grade; E card names the stop
    assert M.entry_card({"entry_grade": None}) is None
    fe = synthetic(); fe["entry_grade"] = "E"
    ce = M.entry_card(fe)
    assert ce["grade"] == "E" and "0/4 won" in ce["lines"][2] and "poor entry" in ce["lines"][0]
    # every grade's line 3 reads REFS
    for g in "ABCDE":
        r = M.REFS["grades"][g]
        assert f"{r['wins']}/{r['n']} won" in M.entry_card(dict(fe, entry_grade=g))["lines"][2]


def test_extend_facts_never_raises_and_is_fast():
    now = T0
    eng = fake_eng(now)
    pos = fake_pos(now, spot=23110.0)
    book = SimpleNamespace(pos=pos, trades=[], p={"spot_trail": 12.0}, capital=180000.0)
    eng.books = {"spot_dc12_t12": book}
    memo = SimpleNamespace(t_in=now, trade_id=int(now))
    base = synthetic()
    # a broken engine (no attributes at all) must not raise either
    M.extend_facts(dict(base), fake_ctx(now), SimpleNamespace(), book, SimpleNamespace(t_in=now, trade_id=1))
    M.extend_memo(SimpleNamespace(), {"now_dt": None}, SimpleNamespace(), {})
    f = dict(base)
    M.extend_facts(f, fake_ctx(now), eng, book, memo)
    assert f["entry_grade"] and f["ret_now"] == f["ret_pct"] and f["entry_look"] == "unproven"
    t0 = time.perf_counter()
    for i in range(1000):
        f = dict(base); f["ltp"] = 124.0 + 0.01 * i; f["ret_pct"] = 0.1 * i; f["pnl_pts"] = 0.12 * i
        M.extend_facts(f, fake_ctx(now + i), eng, book, memo)
    ms = (time.perf_counter() - t0) * 1000.0
    assert ms < 300, ms
    assert f["entry_look"] == "vindicated" and f["cost_status"] == "earned back"
    assert len(M._HIST[pos["id"]]) >= 500                      # the 1-Hz history is being fed (bounded at 600 s)
    assert len(M._HIST[pos["id"]]) <= 602
    return ms


def test_selector_end_to_end():
    """Drive the core selector with the entry templates over the first 90 s of a trade: the composite fires with
    the card, the groups are spread over the first minute, nothing renders a formatting error, nothing fires twice."""
    c = C.Commentary("2026-10-19", templates=list(C.TEMPLATES) + list(M.TEMPLATES), paper_dir=None)
    base = synthetic()
    seen = []
    for s in range(0, 95):
        f = dict(base); f["hold_s"] = float(s); f["hold_min"] = s / 60.0
        ctx = {"now_s": T0 + s, "now_dt": datetime(2026, 10, 19, 13, 29, 56, tzinfo=config.IST)}
        c._verdict(ctx, f, 12.0)
        c._select(ctx, f)
    items = list(c.items)                                        # the panel keeps the last 12 only
    for it in items:
        assert not it["text"].startswith("["), it
    seen = [k for _, k in sorted((v["t"], k) for k, v in c._fired.items())]
    assert len(seen) == len(set(seen)) and all(v["n"] == 1 for v in c._fired.values())
    assert seen[0] == "entry.stupid", seen                      # the composite fired on the entry tick
    assert "entry.second_look_60s" in seen and "strike.lottery" in seen and "chase.no_push" in seen, seen
    assert 12 <= len(seen) <= 30, len(seen)
    return items


if __name__ == "__main__":
    test_shape()
    test_predicates_and_phrasings()
    test_extend_memo_and_card()
    ms = test_extend_facts_never_raises_and_is_fast()
    items = test_selector_end_to_end()
    print(f"cmt_entry: {len(M.TEMPLATES)} templates, {sum(len(t.phrasings) for t in M.TEMPLATES)} phrasings, {len(M.FACTS)} facts; "
          f"1,000 extend_facts = {ms:.0f} ms")
    for it in reversed(items):
        print(f"  {it['time']} [{it['tone']:<11}] {it['key']:<24} {it['text'][:120]}")
    print("OK")
