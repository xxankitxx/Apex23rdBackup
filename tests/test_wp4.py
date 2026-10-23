"""WP-4 checks (paper books): python tests/test_wp4.py  (or python -m pytest tests/test_wp4.py)."""
import json
import math
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_wp4_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

import numpy as np  # noqa: E402

from apex import config  # noqa: E402
config.FILL_NEXT_PRINT = False   # D-126: these suites test the exit/entry logic itself on same-step fills; D-126 has its own suite
from apex.engine import paper  # noqa: E402

IST = config.IST


def _dt(day, hh, mm, ss=0):
    y, m, d = (int(x) for x in day.split("-"))
    return datetime(y, m, d, hh, mm, ss, tzinfo=IST)


# ── (a) corrupt books are preserved, not overwritten ──────────────────────────
def test_corrupt_books_preserved():
    day = "2026-10-19"
    path = os.path.join(config.PAPER_DIR, f"{day}.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"x": {"name": "x", "p": {}, "da')        # torn write
    assert paper.load_books(day) is None
    assert not os.path.exists(path)                       # the next save cannot overwrite it
    bad = [n for n in os.listdir(config.PAPER_DIR) if n.startswith(f"{day}.json.corrupt-")]
    assert len(bad) == 1
    with open(os.path.join(config.PAPER_DIR, bad[0]), encoding="utf-8") as f:
        assert f.read().startswith('{"x"')                 # evidence intact
    assert paper.LAST_LOAD_ERROR and day in paper.LAST_LOAD_ERROR
    # a good file loads and clears the error; a missing file is not an error
    b = paper.Book("x", config.TRIGGER, day)
    paper.save_books({"x": b}, day)
    got = paper.load_books(day)
    assert got and got["x"].capital == config.START_CAPITAL and paper.LAST_LOAD_ERROR == ""
    assert paper.load_books("2026-10-18") is None and paper.LAST_LOAD_ERROR == ""
    # structurally wrong JSON (parses, but is not books) is also kept as evidence
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"x": {"name": "x"}}, f)
    assert paper.load_books(day) is None and not os.path.exists(path)
    bad2 = [n for n in os.listdir(config.PAPER_DIR) if n.startswith(f"{day}.json.corrupt-")]
    assert len(bad2) == 2                                 # the second quarantine did not overwrite the first


# ── (b) a transient Windows lock on replace does not lose the save ────────────
def test_save_books_retries_permission_error():
    day = "2026-10-21"
    b = paper.Book("x", config.TRIGGER, day)
    b.capital = 123456.0
    real, calls = os.replace, {"n": 0}
    sleeps = []

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] == 1:
            raise PermissionError("locked by antivirus")
        return real(src, dst)

    real_sleep = paper.time.sleep
    os.replace = flaky
    paper.time.sleep = lambda s: sleeps.append(s)
    try:
        paper.save_books({"x": b}, day)
    finally:
        os.replace = real
        paper.time.sleep = real_sleep
    assert calls["n"] == 2 and sleeps                     # retried once, after a pause
    got = paper.load_books(day)
    assert got["x"].capital == 123456.0
    assert not os.path.exists(os.path.join(config.PAPER_DIR, f"{day}.json.tmp"))
    # a lock that never clears still raises (the engine loop logs it), and the old file survives
    os.replace = lambda s, d: (_ for _ in ()).throw(PermissionError("locked"))
    paper.time.sleep = lambda s: None
    try:
        b.capital = 1.0
        try:
            paper.save_books({"x": b}, day)
            raise AssertionError("expected PermissionError")
        except PermissionError:
            pass
    finally:
        os.replace = real
        paper.time.sleep = real_sleep
    assert paper.load_books(day)["x"].capital == 123456.0


# ── (c) observers: trade age, mid, exit Greeks ───────────────────────────────
def test_trade_age_mid_and_exit_greeks_recorded():
    b = paper.Book("x", config.TRIGGER, "2026-10-21")
    now = _dt("2026-10-21", 10, 0)
    t0 = now.timestamp()
    opt = {"id": 5, "key": "k", "strike": 25150, "rr": "CE", "week": 0, "expiry": "2026-10-27", "ltp": 150.0,
           "bid": 149.0, "ask": 151.0, "delta": 0.6, "iv": 0.14, "age": 0.2, "ltt": t0 - 4.0}
    ctx = {"now_s": t0, "now_dt": now, "fut": 25200.0, "advisors": {}, "w0": "2026-10-27",
           "episode": {"id": 1, "dir": 1, "type": "BASKET-LED"},
           "iv_rise_since_onset": 0.4, "iv_rise_interp": 0.3}
    pos = paper.open_trade(b, ctx, opt, "test")
    assert abs(pos["trade_age_in"] - 4.0) < 1e-6 and pos["mid_in"] == 150.0
    assert pos["iv_rise_in"] == 0.4 and pos["iv_rise_interp_in"] == 0.3
    assert pos["dte_in"] == 6 and pos["band_fallback"] is False
    out = dict(opt, ltp=139.0, bid=138.0, ask=141.0, delta=0.52, iv=0.15, age=0.3, ltt=t0 + 25.0)
    c2 = dict(ctx, fut=25185.0, now_s=t0 + 30, by_id={5: out}, by_key={"k": out},
              domino={"S_up": 0, "S_dn": 0, "z": 0}, fut_age=0.1)
    t = paper.check_exit(b, c2)
    assert t and t["reason"] == "STOP" and t["exit"] == 139.0
    assert abs(t["trade_age_out"] - 5.0) < 1e-6 and t["mid_out"] == 139.5
    assert t["iv_out"] == 0.15 and t["delta_out"] == 0.52
    assert abs(t["ret_pct_mid"] - round(100.0 * (139.5 - 150.0) / 150.0, 3)) < 1e-9
    assert t["trade_age_in"] == pos["trade_age_in"]       # entry observers travel with the trade
    # missing inputs give None, never an exception (no ltt, no bid, NaN ltt, exit without a row)
    b2 = paper.Book("y", config.TRIGGER, "2026-10-21")
    o2 = {"id": 6, "key": "k2", "strike": 25150, "rr": "CE", "expiry": "bad-date", "ltp": 150.0,
          "bid": None, "ask": 151.0, "ltt": float("nan")}
    p2 = paper.open_trade(b2, dict(ctx, episode={"id": 2, "dir": 1, "type": "X"}), o2, "t")
    assert p2["trade_age_in"] is None and p2["mid_in"] is None and p2["dte_in"] is None
    t2 = paper.close_trade(b2, dict(ctx, now_s=t0 + 5), 150.0, "TIME (15:25 flatten)", None)
    for k in ("trade_age_out", "mid_out", "iv_out", "delta_out", "ret_pct_mid"):
        assert t2[k] is None, k
    # a position restored from a pre-WP-4 books file (no observer fields) still closes
    b3 = paper.Book("z", config.TRIGGER, "2026-10-21")
    paper.open_trade(b3, dict(ctx, episode={"id": 3, "dir": 1, "type": "X"}), opt, "t")
    for k in ("trade_age_in", "mid_in", "iv_rise_in", "iv_rise_interp_in", "dte_in", "band_fallback"):
        b3.pos.pop(k)
    t3 = paper.close_trade(b3, dict(ctx, now_s=t0 + 9), 151.0, "STOP", out)
    assert t3["mid_out"] == 139.5 and t3["ret_pct_mid"] is None and t3["pnl_pts"] == 1.0


def test_band_fallback_flag_set_on_copy_only():
    now = _dt("2026-10-21", 10, 0)
    row = {"id": 1, "key": "a", "strike": 24900, "rr": "CE", "week": 0, "expiry": "2026-10-27",
           "ltp": 320.0, "delta": 0.9, "age": 0.1}
    ctx = {"now_dt": now, "w0": "2026-10-27", "options": [row]}
    opt, why = paper.choose_contract(ctx, 1)
    assert opt["id"] == 1 and why == "" and opt.get("_fallback") is True
    assert "_fallback" not in row                         # the shared chain row is untouched
    row2 = dict(row, delta=0.6)
    opt, _ = paper.choose_contract(dict(ctx, options=[row2]), 1)
    assert opt is row2 and not opt.get("_fallback")
    b = paper.Book("x", config.TRIGGER, "2026-10-21")
    c = {"now_s": now.timestamp(), "now_dt": now, "fut": 25200.0, "advisors": {}, "episode": {"id": 1, "dir": 1, "type": "X"}}
    assert paper.open_trade(b, c, dict(row, _fallback=True), "t")["band_fallback"] is True
    assert "_fallback" not in b.pos


# ── (e) the trades CSV carries the analysis columns ──────────────────────────
def test_trades_csv_columns():
    import csv
    b = paper.Book("x", config.TRIGGER, "2026-10-22")
    now = _dt("2026-10-22", 10, 0)
    opt = {"id": 5, "key": "k", "strike": 25150, "rr": "CE", "expiry": "2026-10-27", "ltp": 150.0,
           "bid": 149.0, "ask": 151.0, "delta": 0.6, "iv": 0.14, "ltt": now.timestamp() - 1}
    ctx = {"now_s": now.timestamp(), "now_dt": now, "fut": 25200.0, "advisors": {},
           "episode": {"id": 9, "dir": 1, "type": "BASKET-LED"}}
    paper.open_trade(b, ctx, opt, "t")
    paper.close_trade(b, dict(ctx, now_s=ctx["now_s"] + 10), 155.0, "STOP", dict(opt, ltp=155.0, bid=154.0, ask=156.0))
    path = paper.write_trades_csv(b, "2026-10-22")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    head = rows[0]
    old = ["time_in", "time_out", "rr", "strike", "expiry", "lots", "qty", "entry", "exit",
           "pnl_pts", "ret_pct", "pnl_rs", "capital_after", "reason", "ep_type", "regime", "gap", "stale_exit", "why",
           "entry_bid", "entry_ask", "exit_bid", "exit_ask", "fut_in", "fut_out", "hold_s"]
    new = ["episode", "delta_in", "iv_in", "iv_out", "delta_out", "trade_age_in", "trade_age_out", "mid_in",
           "mid_out", "ret_pct_mid", "stop_fut", "peak_pts", "exit_quote_age", "band_fallback",
           "spot_in", "best_spot", "stop_spot", "lock_armed", "lock_armed_at", "lock_floor", "best_prem",
           "trigger_ltp", "fill_delay_s", "fill_slip", "exit_trigger_px"]
    assert head == old + new                              # existing columns keep their order
    r = dict(zip(head, rows[1]))
    assert r["episode"] == "9" and r["mid_out"] == "155.0" and r["band_fallback"] == "False"


# ── (d) behaviour lock: selection, entry and exit are unchanged from baseline ──
def _ref_choose_contract(ctx, d):
    """FROZEN copy of baseline paper.choose_contract (85b65ed), book=None path. Do not edit."""
    now = ctx["now_dt"]
    opts = ctx["options"]
    rr = "CE" if d > 0 else "PE"
    w0_exp = ctx["w0"]
    zero_dte = now.date().isoformat() == w0_exp
    hmn = config.hm(now)
    week, band = 0, None
    if zero_dte:
        if hmn >= config.mins(config.ZERO_DTE_NO_ENTRY):
            week, band = 1, config.DELTA_BANDS["nextweek"]
        elif hmn >= config.mins(config.ZERO_DTE_NEXTWEEK_FROM):
            week, band = 1, config.DELTA_BANDS["nextweek"]
        else:
            band = config.DELTA_BANDS["zero_am"]
    else:
        dte = (np.datetime64(w0_exp) - np.datetime64(now.date().isoformat())).astype(int)
        band = config.DELTA_BANDS["ge3"] if dte >= 3 else config.DELTA_BANDS["1to2"]
    lo, hi = band
    cands = [o for o in opts if o["rr"] == rr and o["week"] == week and o.get("delta") is not None
             and o["ltp"] and config.MIN_PREMIUM <= o["ltp"] <= config.MAX_PREMIUM and o["age"] < 15]
    inband = [o for o in cands if lo <= abs(o["delta"]) <= hi]
    if inband:
        return min(inband, key=lambda o: abs(o["delta"])), ""
    above = [o for o in cands if abs(o["delta"]) >= lo]
    if above:
        return min(above, key=lambda o: abs(o["delta"])), ""
    return None, f"no {rr} in delta band {lo:.2f}-{hi:.2f}"


def _chain(F, exps, width=80.0, age=0.3, now_s=0.0, skip=()):
    """A synthetic two-week chain: logistic CE delta, PE = CE - 1, intrinsic + time value premium."""
    rows, i = [], 0
    for week, (exp, w) in enumerate(zip(exps, (width, width * 1.6))):
        for K in range(24600, 25801, 50):
            for rr in ("CE", "PE"):
                i += 1
                x = (K - F) / w
                dce = 1.0 / (1.0 + math.exp(x))
                delta = round(dce if rr == "CE" else dce - 1.0, 4)
                intr = max(F - K, 0.0) if rr == "CE" else max(K - F, 0.0)
                ltp = round(intr + 60.0 * math.exp(-abs(K - F) / (2.5 * w)) + 3.0, 2)
                key = f"NIFTY|OPT|{exp}|{K}|{rr}"
                if key in skip:
                    continue
                rows.append({"id": i, "key": key, "strike": float(K), "rr": rr, "week": week, "expiry": exp,
                             "ltp": ltp, "bid": round(ltp - 0.5, 2), "ask": round(ltp + 0.5, 2),
                             "delta": delta, "iv": 0.14, "age": age, "ltt": now_s - 2.0})
    return rows


def _selection_fixtures():
    out = []
    for (day, hh, mm, w0, w1) in [
        ("2026-10-19", 10, 0, "2026-10-19", "2026-10-27"),   # 0DTE morning
        ("2026-10-19", 13, 30, "2026-10-19", "2026-10-27"),  # 0DTE 13:30 (next week)
        ("2026-10-19", 14, 50, "2026-10-19", "2026-10-27"),  # 0DTE after 14:45
        ("2026-10-26", 11, 0, "2026-10-27", "2026-11-03"),   # 1 DTE
        ("2026-10-21", 11, 0, "2026-10-27", "2026-11-03"),   # >= 3 DTE
    ]:
        for F in (25190.0, 25230.0, 25377.0):
            for width in (80.0, 25.0, 300.0):              # 25: band empty -> fallback; 300: nothing deep
                out.append({"now_dt": _dt(day, hh, mm), "w0": w0, "options": _chain(F, (w0, w1), width)})
    # band empty AND no fallback (only cheap OTM rows), stale rows, missing deltas, premium limits
    ctx = out[-1]
    out.append(dict(ctx, options=[dict(o, delta=0.3 if o["rr"] == "CE" else -0.3) for o in ctx["options"]]))
    out.append(dict(ctx, options=[dict(o, age=15.0) for o in ctx["options"]]))
    out.append(dict(ctx, options=[dict(o, delta=None) if o["strike"] % 100 == 0 else o for o in ctx["options"]]))
    out.append(dict(ctx, options=[dict(o, ltp=700.0) if abs(o["delta"]) > 0.6 else o for o in ctx["options"]]))
    out.append(dict(ctx, options=[]))
    return out


def test_choose_contract_matches_frozen_baseline():
    old_nw = config.ZERO_DTE_USE_NEXTWEEK
    config.ZERO_DTE_USE_NEXTWEEK = True          # the frozen baseline is the D-021 rule; D-108 is tested below
    try:
        _choose_contract_lock()
    finally:
        config.ZERO_DTE_USE_NEXTWEEK = old_nw


def _choose_contract_lock():
    n_fallback = n_none = 0
    for ctx in _selection_fixtures():
        for d in (1, -1):
            ref, rwhy = _ref_choose_contract(ctx, d)
            got, gwhy = paper.choose_contract(ctx, d)
            assert (ref["id"] if ref else None) == (got["id"] if got else None), (ctx["now_dt"], d)
            assert rwhy == gwhy
            if got is not None:
                assert {k: v for k, v in got.items() if k != "_fallback"} == ref
                if got.get("_fallback"):
                    n_fallback += 1
            else:
                n_none += 1
    assert n_fallback > 0 and n_none > 0                  # the grid really covers both edges


# A scripted path through every entry gate and every exit. Each step is applied, in order, to
# a book: flat -> evaluate_entry (and on fire choose_contract + open_trade); holding -> check_exit.
_EP = lambda i, d, fut0, **k: dict({"id": i, "dir": d, "type": "BASKET-LED", "fut0": fut0, "first": "HDFCBANK", "gap": False}, **k)
_D = lambda d, z, su, sd, **k: dict({"dir": d, "z": z, "S_up": su, "S_dn": sd, "sigma15": 10.0, "gap": 0.0}, **k)
PATH = [
    # day, hh:mm:ss, fut, domino, episode, extras
    ("2026-10-21", "09:20:00", 25200.0, _D(1, 3.0, 0.7, 0.0), _EP(1, 1, 25195.0), {}),
    ("2026-10-21", "09:30:00", 25200.0, _D(1, 3.0, 0.7, 0.0), _EP(1, 1, 25195.0), {"blackout": {"on": True, "why": "feed stale"}}),
    ("2026-10-21", "09:31:00", 25200.0, _D(1, 3.0, 0.7, 0.0), None, {}),
    ("2026-10-21", "09:32:00", 25200.0, _D(1, 3.0, 0.7, 0.0), _EP(2, 1, 25195.0, gap=True), {}),
    ("2026-10-21", "09:33:00", 25200.0, _D(-1, -3.0, 0.0, 0.7), _EP(3, 1, 25195.0), {}),
    ("2026-10-21", "09:34:00", 25200.0, _D(1, 1.6, 0.7, 0.0, gap=4.0), _EP(3, 1, 25195.0), {}),
    ("2026-10-21", "09:35:00", 25200.0, _D(1, 2.5, 0.45, 0.0, gap=2.0), _EP(3, 1, 25195.0), {}),
    ("2026-10-21", "09:36:00", 25236.0, _D(1, 2.5, 0.7, 0.0, gap=6.0), _EP(3, 1, 25195.0), {}),
    ("2026-10-21", "09:37:00", 25205.0, _D(1, 2.5, 0.7, 0.0, gap=6.0), _EP(3, 1, 25195.0), {"iv_rise": 2.0}),
    ("2026-10-21", "09:38:00", 25205.0, _D(1, 2.5, 0.7, 0.0, gap=6.0), _EP(3, 1, 25195.0), {"iv_rise": 0.5, "veto": True}),
    ("2026-10-21", "09:39:00", 25205.0, _D(1, 2.5, 0.7, 0.0, gap=6.0), _EP(3, 1, 25195.0), {"iv_rise": 0.5}),
    ("2026-10-21", "09:40:00", 25210.0, _D(1, 0.5, 0.3, 0.1), _EP(3, 1, 25195.0), {"book": (1, 1)}),
    ("2026-10-21", "09:41:00", 25218.0, _D(1, 0.5, 0.3, 0.1), _EP(3, 1, 25195.0), {"book": (1, 0)}),
    ("2026-10-21", "09:42:00", 25230.0, _D(1, 0.5, 0.3, 0.1), _EP(3, 1, 25195.0), {}),
    ("2026-10-21", "09:43:00", 25222.0, _D(-1, -1.2, 0.1, 0.65), _EP(3, 1, 25195.0), {}),
    ("2026-10-21", "09:44:00", 25222.0, _D(1, 2.5, 0.7, 0.0, gap=6.0), _EP(3, 1, 25195.0), {}),
    ("2026-10-21", "10:10:00", 25190.0, _D(-1, -3.0, 0.0, 0.7, gap=-6.0), _EP(4, -1, 25195.0), {}),
    ("2026-10-21", "10:11:00", 25204.0, _D(1, 0.3, 0.2, 0.1), _EP(4, -1, 25195.0), {"fut_age": 9.0}),
    ("2026-10-21", "10:11:01", 25204.0, _D(1, 0.3, 0.2, 0.1), _EP(4, -1, 25195.0), {"age": 8.0}),
    ("2026-10-21", "10:11:04", 25190.0, _D(1, 0.3, 0.2, 0.1), _EP(4, -1, 25195.0), {"age": 8.0}),
    ("2026-10-21", "10:11:05", 25190.0, _D(1, 0.3, 0.2, 0.1), _EP(4, -1, 25195.0), {}),
    ("2026-10-21", "14:00:00", 25200.0, _D(1, 2.2, 0.66, 0.0, gap=5.5), _EP(5, 1, 25196.0), {}),
    ("2026-10-21", "14:00:30", 25150.0, _D(1, 0.3, 0.2, 0.1), _EP(5, 1, 25196.0), {"blackout": {"on": True, "why": "jump"}}),
    ("2026-10-21", "14:01:00", 25201.0, _D(1, 0.3, 0.2, 0.1), _EP(5, 1, 25196.0), {}),
    ("2026-10-21", "15:26:00", 25205.0, _D(1, 0.3, 0.2, 0.1), _EP(5, 1, 25196.0), {"age": 40.0}),
    ("2026-10-21", "15:16:00", 25205.0, _D(1, 3.0, 0.7, 0.0, gap=6.0), _EP(6, 1, 25200.0), {}),
    ("2026-10-27", "10:00:00", 25300.0, _D(1, 2.4, 0.8, 0.0, gap=7.0), _EP(7, 1, 25296.0), {}),
    ("2026-10-27", "15:01:00", 25310.0, _D(1, 0.3, 0.2, 0.1), _EP(7, 1, 25296.0), {"held_delta": 0.95}),
    ("2026-10-27", "15:02:00", 25311.0, _D(1, 0.3, 0.2, 0.1), _EP(7, 1, 25296.0), {"held_delta": 0.85}),
    ("2026-10-27", "15:03:00", 25311.0, _D(1, 3.0, 0.8, 0.0, gap=7.0), _EP(7, 1, 25296.0), {}),
]
_W = {"2026-10-21": ("2026-10-27", "2026-11-03"), "2026-10-27": ("2026-10-27", "2026-11-03")}


def _run_path(book_name):
    b = paper.Book(book_name, config.VARIANTS[book_name], "2026-10-21")
    out = []
    for day, hms, fut, dom, ep, ex in PATH:
        hh, mm, ss = (int(x) for x in hms.split(":"))
        now = _dt(day, hh, mm, ss)
        now_s = now.timestamp()
        w0, w1 = _W[day]
        opts = _chain(fut, (w0, w1), 80.0, ex.get("age", 0.3), now_s)
        if b.pos is not None and "held_delta" in ex:
            opts = [dict(o, delta=ex["held_delta"]) if o["key"] == b.pos["key"] else o for o in opts]
        by_key = {o["key"]: o for o in opts}
        by_id = {o["id"]: o for o in opts}
        held = by_key.get(b.pos["key"]) if b.pos else None
        ctx = {"now_s": now_s, "now_dt": now, "fut": fut, "domino": dom, "episode": ep, "w0": w0,
               "options": opts, "by_key": by_key, "by_id": by_id, "fut_age": ex.get("fut_age", 0.2),
               "blackout": ex.get("blackout", {"on": False}), "iv_rise_since_onset": ex.get("iv_rise"),
               "advisors": {"room": {"veto": bool(ex.get("veto")), "why": "wall close"}},
               "book_state": ({held["id"]: {"opp_q": ex["book"][0], "opp_o": ex["book"][1]}}
                              if held and ex.get("book") else {}),
               "regime": {"state": "TREND"}}
        if b.pos is None:
            fire, why = paper.evaluate_entry(b, ctx, ["room"])
            rec = ["E", fire, why]
            if fire:
                opt, msg = paper.choose_contract(ctx, paper.entry_dir(b, ctx), b)
                pos = paper.open_trade(b, ctx, opt, why) if opt else None
                rec += [msg, pos and (pos["key"], pos["lots"], pos["entry"], pos["delta_in"])]
        else:
            t = paper.check_exit(b, ctx)
            if t:
                rec = ["X", t["reason"], t["exit"], t["pnl_pts"], t["ret_pct"], round(t["capital_after"], 2),
                       bool(t.get("stale_exit")), bool(t.get("gap")), t["hold_s"]]
            else:
                p = b.pos
                rec = ["H", p["trail"], p.get("stop_fut"), p["best"], p["peak_pts"], (p.get("pending") or {}).get("reason"), p["gap"]]
        out.append(rec)
    return [json.loads(json.dumps(r)) for r in out]


# Recorded from the BASELINE paper.py (85b65ed) with _run_path(); see the WP-4 commit message.
GOLDEN = {
    'm2.0_s0.5': [
        ["E", False, "outside entry window"],
        ["E", False, "DATA GAP: feed stale"],
        ["E", False, "no episode"],
        ["E", False, "episode began in a data gap"],
        ["E", False, "impulse against the episode"],
        ["E", False, "impulse z 1.6 < 2.0"],
        ["E", False, "synchrony 0.45 < 0.5"],
        ["E", False, "LATE: futures already 41 pts since onset"],
        ["E", False, "LATE: ATM IV +2.0 since onset"],
        ["E", False, "gate room: wall close"],
        ["E", True, "basket-led move UP: futures z 2.5, synchrony 70%, first mover HDFCBANK, 10 pts since onset", "", ["NIFTY|OPT|2026-10-27|25150|CE", 14, 103.57, 0.6654]],
        ["H", False, 25193.0, 25210.0, 3.8800000000000097, None, False],
        ["H", True, 25206.0, 25218.0, 10.14, None, False],
        ["H", True, 25218.0, 25230.0, 19.650000000000006, None, False],
        ["X", "THESIS-VOID (synchrony flipped)", 116.86, 13.29, 12.832, 112093.9, False, False, 240.0],
        ["E", False, "already traded this episode"],
        ["E", True, "basket-led move DOWN: futures z 3.0, synchrony 70%, first mover HDFCBANK, 5 pts since onset", "", ["NIFTY|OPT|2026-10-27|25200|PE", 24, 70.07, -0.5312]],
        ["H", False, 25202.0, 25190.0, 0.0, None, False],
        ["H", False, 25202.0, 25190.0, 0.0, "STOP", False],
        ["H", False, 25202.0, 25190.0, 0.0, "STOP", False],
        ["X", "STOP", 70.07, 0.0, 0.0, 112093.9, False, False, 65.0],
        ["E", True, "basket-led move UP: futures z 2.2, synchrony 66%, first mover HDFCBANK, 4 pts since onset", "", ["NIFTY|OPT|2026-10-27|25150|CE", 17, 99.73, 0.6514]],
        ["H", False, 25188.0, 25200.0, 0.0, None, True],
        ["H", False, 25188.0, 25201.0, 0.7599999999999909, None, True],
        ["X", "TIME (15:25 flatten)", 103.57, 3.84, 3.85, 116337.1, True, True, 5160.0],
        ["E", False, "outside entry window"],
        ["E", True, "basket-led move UP: futures z 2.4, synchrony 80%, first mover HDFCBANK, 4 pts since onset", "", ["NIFTY|OPT|2026-10-27|25250|CE", 17, 99.73, 0.6514]],
        ["H", False, 25288.0, 25310.0, 7.719999999999999, None, False],
        ["X", "TIME (0DTE 15:00)", 108.23, 8.5, 8.523, 125729.6, False, False, 18120.0],
        ["E", False, "already traded this episode"],
    ],
    'gap3_s0.4': [
        ["E", False, "outside entry window"],
        ["E", False, "DATA GAP: feed stale"],
        ["E", False, "no episode"],
        ["E", False, "episode began in a data gap"],
        ["E", False, "impulse against the episode"],
        ["E", True, "basket-led move UP: futures z 1.6, synchrony 70%, first mover HDFCBANK, 5 pts since onset", "", ["NIFTY|OPT|2026-10-27|25150|CE", 15, 99.73, 0.6514]],
        ["H", False, 25188.0, 25200.0, 0.0, None, False],
        ["H", True, 25224.0, 25236.0, 28.299999999999997, None, False],
        ["X", "TRAIL", 103.57, 3.84, 3.85, 103744.0, False, False, 180.0],
        ["E", False, "already traded this episode"],
        ["E", False, "already traded this episode"],
        ["E", False, "already traded this episode"],
        ["E", False, "already traded this episode"],
        ["E", False, "already traded this episode"],
        ["E", False, "already traded this episode"],
        ["E", False, "already traded this episode"],
        ["E", True, "basket-led move DOWN: futures z 3.0, synchrony 70%, first mover HDFCBANK, 5 pts since onset", "", ["NIFTY|OPT|2026-10-27|25200|PE", 22, 70.07, -0.5312]],
        ["H", False, 25202.0, 25190.0, 0.0, None, False],
        ["H", False, 25202.0, 25190.0, 0.0, "STOP", False],
        ["H", False, 25202.0, 25190.0, 0.0, "STOP", False],
        ["X", "STOP", 70.07, 0.0, 0.0, 103744.0, False, False, 65.0],
        ["E", True, "basket-led move UP: futures z 2.2, synchrony 66%, first mover HDFCBANK, 4 pts since onset", "", ["NIFTY|OPT|2026-10-27|25150|CE", 16, 99.73, 0.6514]],
        ["H", False, 25188.0, 25200.0, 0.0, None, True],
        ["H", False, 25188.0, 25201.0, 0.7599999999999909, None, True],
        ["X", "TIME (15:25 flatten)", 103.57, 3.84, 3.85, 107737.6, True, True, 5160.0],
        ["E", False, "outside entry window"],
        ["E", True, "basket-led move UP: futures z 2.4, synchrony 80%, first mover HDFCBANK, 4 pts since onset", "", ["NIFTY|OPT|2026-10-27|25250|CE", 16, 99.73, 0.6514]],
        ["H", False, 25288.0, 25310.0, 7.719999999999999, None, False],
        ["X", "TIME (0DTE 15:00)", 108.23, 8.5, 8.523, 116577.6, False, False, 18120.0],
        ["E", False, "already traded this episode"],
    ],
    'm2.0_s0.5_bookexit': [
        ["E", False, "outside entry window"],
        ["E", False, "DATA GAP: feed stale"],
        ["E", False, "no episode"],
        ["E", False, "episode began in a data gap"],
        ["E", False, "impulse against the episode"],
        ["E", False, "impulse z 1.6 < 2.0"],
        ["E", False, "synchrony 0.45 < 0.5"],
        ["E", False, "LATE: futures already 41 pts since onset"],
        ["E", False, "LATE: ATM IV +2.0 since onset"],
        ["E", False, "gate room: wall close"],
        ["E", True, "basket-led move UP: futures z 2.5, synchrony 70%, first mover HDFCBANK, 10 pts since onset", "", ["NIFTY|OPT|2026-10-27|25150|CE", 14, 103.57, 0.6654]],
        ["X", "BOOK (sellers refilled on the held contract)", 107.45, 3.88, 3.746, 103530.8, False, False, 60.0],
        ["E", False, "already traded this episode"],
        ["E", False, "already traded this episode"],
        ["E", False, "already traded this episode"],
        ["E", False, "already traded this episode"],
        ["E", True, "basket-led move DOWN: futures z 3.0, synchrony 70%, first mover HDFCBANK, 5 pts since onset", "", ["NIFTY|OPT|2026-10-27|25200|PE", 22, 70.07, -0.5312]],
        ["H", False, 25202.0, 25190.0, 0.0, None, False],
        ["H", False, 25202.0, 25190.0, 0.0, "STOP", False],
        ["H", False, 25202.0, 25190.0, 0.0, "STOP", False],
        ["X", "STOP", 70.07, 0.0, 0.0, 103530.8, False, False, 65.0],
        ["E", True, "basket-led move UP: futures z 2.2, synchrony 66%, first mover HDFCBANK, 4 pts since onset", "", ["NIFTY|OPT|2026-10-27|25150|CE", 15, 99.73, 0.6514]],
        ["H", False, 25188.0, 25200.0, 0.0, None, True],
        ["H", False, 25188.0, 25201.0, 0.7599999999999909, None, True],
        ["X", "TIME (15:25 flatten)", 103.57, 3.84, 3.85, 107274.8, True, True, 5160.0],
        ["E", False, "outside entry window"],
        ["E", True, "basket-led move UP: futures z 2.4, synchrony 80%, first mover HDFCBANK, 4 pts since onset", "", ["NIFTY|OPT|2026-10-27|25250|CE", 16, 99.73, 0.6514]],
        ["H", False, 25288.0, 25310.0, 7.719999999999999, None, False],
        ["X", "TIME (0DTE 15:00)", 108.23, 8.5, 8.523, 116114.8, False, False, 18120.0],
        ["E", False, "already traded this episode"],
    ],
}


def test_entry_and_exit_path_matches_baseline():
    names = ("m2.0_s0.5", "gap3_s0.4", "m2.0_s0.5_bookexit")
    # the golden path was recorded on the v1 production clock; the owner's CAS test (D-094) moves
    # LAST_ENTRY/FLATTEN_AT, so the lock pins the v1 clock and proves the LOGIC is unchanged
    old = (config.LAST_ENTRY, config.FLATTEN_AT, config.EXIT_FUT_STALE_S, config.ZERO_DTE_USE_NEXTWEEK)
    config.LAST_ENTRY, config.FLATTEN_AT, config.EXIT_FUT_STALE_S = (15, 15), (15, 25), 3.0   # D-094/D-097 moved these
    config.ZERO_DTE_USE_NEXTWEEK = True                                                         # D-108 changed this
    old109 = (config.FUT_EXIT_ON_MID, config.THESIS_VOID_HOLD_S, config.REENTRY_COOLDOWN_S, config.MIN_IMPULSE_PTS,
              config.DAILY_LOSS_STOP_PCT, config.LOSS_STREAK_N)
    config.FUT_EXIT_ON_MID, config.THESIS_VOID_HOLD_S, config.REENTRY_COOLDOWN_S, config.MIN_IMPULSE_PTS = False, 0.0, 0.0, 0.0
    config.DAILY_LOSS_STOP_PCT, config.LOSS_STREAK_N = 0.0, 0                                     # D-113 brake off for the lock
    old117 = (config.EXPIRY_ENTRY_END, config.MAX_ENTRIES_PER_DAY)
    config.EXPIRY_ENTRY_END, config.MAX_ENTRIES_PER_DAY = None, 0                                  # D-117 off for the lock
    try:
        got_all = {n: _run_path(n) for n in names}
    finally:
        config.LAST_ENTRY, config.FLATTEN_AT, config.EXIT_FUT_STALE_S, config.ZERO_DTE_USE_NEXTWEEK = old
        (config.FUT_EXIT_ON_MID, config.THESIS_VOID_HOLD_S, config.REENTRY_COOLDOWN_S, config.MIN_IMPULSE_PTS,
         config.DAILY_LOSS_STOP_PCT, config.LOSS_STREAK_N) = old109
        config.EXPIRY_ENTRY_END, config.MAX_ENTRIES_PER_DAY = old117
    for n in names:
        got = got_all[n]
        assert len(got) == len(PATH) == 30
        for i, (g, w) in enumerate(zip(got, GOLDEN[n])):
            assert g == w, (n, i, PATH[i][1], g, w)
    # the path really reaches every exit and the main entry rejections
    kinds = {r[1].split(" ")[0] for n in names for r in GOLDEN[n] if r[0] == "X"}
    assert {"STOP", "TRAIL", "THESIS-VOID", "TIME", "BOOK"} <= kinds, kinds


def test_anti_churn_rules():
    """D-109 (owner, 19 Oct 13:14): exits on the futures mid, thesis-void must persist 5 s, 60-s cool-down
    after an exit, and a 15-pt floor on the 15-s impulse."""
    b = paper.Book("m2.0_s0.5", config.VARIANTS["m2.0_s0.5"], "2026-10-21")
    opt = {"id": 5, "key": "k", "strike": 25150, "rr": "CE", "expiry": "2026-10-27", "ltp": 150.0}
    t0 = datetime(2026, 10, 21, 11, 0, tzinfo=config.IST)
    ctx = {"now_s": 0.0, "now_dt": t0, "fut": 25200.0, "fut_mid": 25200.0, "advisors": {},
           "episode": {"id": 1, "dir": 1, "type": "BASKET-LED"}}
    paper.open_trade(b, ctx, opt, "t")
    q = dict(opt, ltp=151.0, age=0.1)
    base = dict(ctx, by_id={5: q}, by_key={"k": q}, fut_age=0.1,
                domino={"S_up": 0.0, "S_dn": 0.0, "z": 0.0})
    # a last print 12 pts down while the mid is only 4 down: no stop
    assert paper.check_exit(b, dict(base, now_s=1.0, fut=25188.0, fut_mid=25196.0)) is None
    # the heavyweights flip against us: not on the first reading, only after 5 s
    flip = dict(base, domino={"S_up": 0.0, "S_dn": 0.9, "z": -2.0})
    assert paper.check_exit(b, dict(flip, now_s=2.0)) is None
    assert paper.check_exit(b, dict(flip, now_s=6.0)) is None
    t = paper.check_exit(b, dict(flip, now_s=7.1))
    assert t and t["reason"].startswith("THESIS-VOID")
    # 60-s cool-down after that exit
    ectx = {"domino": {"dir": 1, "z": 3.0, "r15": 30.0, "S_up": 0.9, "S_dn": 0.0, "sigma15": 10.0},
            "episode": {"id": 2, "dir": 1, "fut0": 25200.0, "type": "BASKET-LED"}, "advisors": {},
            "blackout": {"on": False}, "now_dt": t0, "fut": 25200.0}
    ok, why = paper.evaluate_entry(b, dict(ectx, now_s=30.0), [])
    assert not ok and "cool-down" in why
    # 15-pt floor: z 3 but only 9 pts in 15 s
    ok, why = paper.evaluate_entry(b, dict(ectx, now_s=100.0, domino=dict(ectx["domino"], r15=9.0)), [])
    assert not ok and "pt floor" in why


def test_expiry_day_trades_the_expiring_weekly_only():
    """D-108 (owner, 19 Oct 13:06): on expiry day the book buys this week's expiring contract all day,
    never next week's / the monthly; no entries after 14:45."""
    assert config.ZERO_DTE_USE_NEXTWEEK is False
    seen = 0
    for ctx in _selection_fixtures():
        if ctx["now_dt"].date().isoformat() != ctx["w0"]:
            continue
        for d in (1, -1):
            got, why = paper.choose_contract(ctx, d)
            if config.hm(ctx["now_dt"]) >= config.mins(config.ZERO_DTE_NO_ENTRY):
                assert got is None and "no entries after" in why
            elif got is not None:
                assert got["expiry"] == ctx["w0"] and got["week"] == 0, (ctx["now_dt"], got["key"])
                seen += 1
    assert seen > 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--dump-golden"]:
        print(json.dumps({n: _run_path(n) for n in ("m2.0_s0.5", "gap3_s0.4", "m2.0_s0.5_bookexit")}, indent=1))
        sys.exit(0)
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
