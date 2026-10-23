"""WP-2 checks (engine loop): python tests/test_wp2.py  (or python -m pytest tests/test_wp2.py)."""
import json
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

import numpy as np  # noqa: E402

from apex import config, greeks  # noqa: E402
config.FILL_NEXT_PRINT = False   # D-126: these suites test the exit/entry logic itself on same-step fills; D-126 has its own suite
from apex import engine_main  # noqa: E402
from apex.engine import paper  # noqa: E402
from apex.engine.flow import DFAST, HOLD, REFILL  # noqa: E402
from apex.feed_core import Registry  # noqa: E402
from apex.table import StateBlob, Table  # noqa: E402

EXP = "2026-10-27"
STRIKES = (25200, 25250)


class Rig:
    """A private shared-memory table and blob, a hand-built registry (NIFTY|FUT, SPOT, two w0
    strikes CE/PE, two stocks) and a virtual clock that advances 0.1 s per step."""

    def __init__(self, tag, day):
        self.t = Table(create=True, name=f"t_wp2_{tag}_{os.getpid()}")
        self.blob = StateBlob(create=True, name=f"t_wp2_b_{tag}_{os.getpid()}")
        reg = Registry()
        self.fut = reg.add("NIFTY|FUT", "fut", "NIFTY", "4.1!1", seg="fo")
        self.spot = reg.add("NIFTY|SPOT", "spot", "NIFTY", "4.1!2", seg="eq")
        self.opt = {}
        for k in STRIKES:
            for right, rr in (("call", "CE"), ("put", "PE")):
                key = f"NIFTY|OPT|{EXP}|{k}|{rr}"
                self.opt[(k, rr)] = reg.add(key, "opt", "NIFTY", f"4.1!{len(reg.items) + 10}", k, right, EXP,
                                            depth=True, rr=rr, week=0)
        self.eq = [reg.add(f"S{j}|EQ", "eq", f"S{j}", f"4.1!{100 + j}", seg="eq", wn=10.0, wb=0.0, wf=0.0)
                   for j in range(2)]
        reg.save(self.t)
        self.t.set("feed_state", 5)
        self.now = datetime.fromisoformat(f"{day}T10:00:00").replace(tzinfo=config.IST).timestamp()
        self.vol = 0.0
        self.eng = engine_main.Engine(self.t, self.blob, "sim")
        self.eng.load_registry()

    def write(self, F):
        r = self.t.rows
        ns = int(self.now * 1e9)
        self.t.set("now_ns", ns)
        self.vol += 75
        for i, px in ((self.fut, F), (self.spot, F - 10.0)):
            r["ltp"][i] = px; r["bid"][i] = px - 0.5; r["ask"][i] = px + 0.5
            r["recv_ns"][i] = ns; r["ttq"][i] = self.vol; r["close"][i] = 25100.0; r["ltt"][i] = self.now
        T = greeks.years_to_expiry(EXP, datetime.fromtimestamp(self.now, config.IST))
        for (k, rr), i in self.opt.items():
            px = float(greeks.b76_price(F, np.array([float(k)]), T, 0.13, np.array([rr == "CE"]))[0])
            r["ltp"][i] = px; r["bid"][i] = px - 0.05; r["ask"][i] = px + 0.05
            r["recv_ns"][i] = ns; r["ttq"][i] = self.vol; r["ltt"][i] = self.now - 2.0
        for j, i in enumerate(self.eq):
            r["ltp"][i] = 1000.0 + j; r["close"][i] = 990.0; r["recv_ns"][i] = ns; r["ttq"][i] = self.vol

    def step(self, F, n=1):
        for _ in range(n):
            self.now += 0.1
            self.write(F)
            self.eng.step()

    def warm(self, F=25210.0):
        self.step(F, 230)                     # > RESUME_S of fresh data: the start-up blackout lifts
        assert not self.eng.guard.on, self.eng.guard.reason
        assert getattr(self.eng, "atm", None) is not None

    def champ(self):
        return self.eng.books[self.eng.champion]

    def open_ce(self, strike=25200):
        o = self.eng.ctx["by_key"][f"NIFTY|OPT|{EXP}|{strike}|CE"]
        pos = paper.open_trade(self.champ(), self.eng.ctx, o, "test entry")
        assert pos
        paper.save_books(self.eng.books, self.eng.day)        # as run_books does on an entry
        return pos

    def close(self):
        for x in (self.t, self.blob):
            x.close(); x.unlink()


def _fake_episode(rig):
    view = {"id": 99, "age": 5.0, "dir": 1, "type": "BASKET-LED", "first": "S0", "fut0": 25210.0,
            "n_cross": 1, "max_S": 0.1, "gap": False}
    rig.eng.domino.episode_view = lambda now_s: dict(view)


def test_failing_advisor_cannot_skip_stop():
    """C-07: advise() raising (and, separately, force.update raising) must not skip the exits."""
    for which, day in (("advise", "2026-10-21"), ("force", "2026-10-22")):
        rig = Rig(which, day)
        try:
            rig.warm()
            _fake_episode(rig)                                 # so advise() is really called
            rig.open_ce()

            def boom(*a, **k):
                raise RuntimeError("probe")
            if which == "advise":
                rig.eng.advise = boom
            else:
                rig.eng.force.update = boom
            rig.step(25210.0, 3)
            assert rig.champ().pos is not None
            rig.step(25197.0, 3)                               # 13 pts against a 12-pt stop
            assert rig.champ().pos is None, which
            assert rig.champ().trades[-1]["reason"] == "STOP", rig.champ().trades[-1]["reason"]
        finally:
            rig.close()


def test_one_faulting_advisor_is_marked_not_fatal():
    rig = Rig("adv", "2026-10-21")
    try:
        rig.warm()
        _fake_episode(rig)
        rig.eng.regime.advise = lambda d: 1 / 0
        rig.step(25210.0)
        a = rig.eng.ctx["advisors"]
        assert a["regime"] == {"veto": False, "why": "advisor faulted", "faulted": True}
        assert "faulted" not in a["coherence"] and "iv_late" in a
    finally:
        rig.close()


def test_trail_survives_restart():
    """C-11: an armed trail and its best price are on disk within ~1 s, so a restart keeps them."""
    day = "2026-10-23"
    rig = Rig("trail", day)
    try:
        rig.warm()
        # the futures trail belongs to the domino books (D-124: the champion is a spot book, which trails on spot)
        name = "m2.0_s0.5"
        rig.eng.champion = name                                # only this book: no other book's entry
        rig.eng.books = {name: rig.eng.books[name]}            # or exit may trigger a save by coincidence
        rig.open_ce()
        rig.step(25225.0, 15)                                  # +15 >= d* 12: trail arms; 1.5 s pass
        p = rig.champ().pos
        assert p and p["trail"] and p["best"] == 25225.0
        eng2 = engine_main.Engine(rig.t, rig.blob, "sim")      # the restarted engine
        eng2.start_day(day)
        p2 = eng2.books[name].pos
        assert p2 is not None and p2["trail"] is True and p2["best"] == 25225.0, p2
    finally:
        rig.close()


def test_pe_book_side_reads_asks():
    """C-12: a bought PE is opposed by the asks, like a CE."""
    rig = Rig("side", "2026-10-21")
    try:
        rig.warm()
        f = rig.eng.flow
        for rr in ("CE", "PE"):
            i = rig.opt[(25200, rr)]
            f.cls_b[i] = REFILL; f.cls_bo[i] = REFILL          # bids refilling
            f.cls_s[i] = DFAST; f.cls_so[i] = HOLD             # asks draining
        bs = rig.eng.book_state()
        for rr in ("CE", "PE"):
            e = bs[rig.opt[(25200, rr)]]
            assert e["opp_q"] == DFAST and e["opp_o"] == HOLD and e["side_fix"] == 1, (rr, e)
    finally:
        rig.close()


def test_gex_gets_weekly_forward():
    """C-14: gex_room measures the walls from the w0 forward, not the monthly future."""
    rig = Rig("gex", "2026-10-21")
    try:
        rig.warm()
        _fake_episode(rig)
        rig.step(25210.0)
        seen = []
        rig.eng.gex.advise = lambda d, F: (seen.append(F), (False, "spy"))[1]
        rig.eng.fwd = 25260.0
        rig.eng.advise(rig.eng.ctx, 1)
        assert seen == [25260.0], seen
    finally:
        rig.close()


def test_event_tape_on_disk():
    """C-34: ev() appends to events_DAY.jsonl with the market time."""
    rig = Rig("ev", "2026-10-21")
    try:
        rig.warm()
        rig.eng.ev("TEST", "hello tape")
        path = os.path.join(config.PAPER_DIR, f"events_{rig.eng.day}.jsonl")
        rows = [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]
        last = rows[-1]
        assert last["k"] == "TEST" and last["x"] == "hello tape" and abs(last["mkt_t"] - rig.now) < 1e-3
        assert set(last) == {"t", "k", "x", "mkt_t"}
    finally:
        rig.close()


def test_decision_tape_on_reason_class_change():
    rig = Rig("dec", "2026-10-21")
    try:
        rig.warm()
        rig.eng.champion = "m2.0_s0.5"                         # the tape follows the champion; this test is about the domino path
        rig.step(25210.0, 3)
        path = os.path.join(config.PAPER_DIR, f"decisions_{rig.eng.day}.jsonl")
        n0 = sum(1 for _ in open(path, encoding="utf-8")) if os.path.exists(path) else 0
        rig.step(25210.0, 5)                                   # same reason: no new lines
        n1 = sum(1 for _ in open(path, encoding="utf-8"))
        assert n1 == n0 and n1 >= 1
        _fake_episode(rig)
        rig.step(25210.0, 2)                                   # "no episode" -> an impulse/synchrony reason
        rows = [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]
        assert len(rows) == n1 + 1 and rows[-1]["ep"] == 99
        assert {"t", "reason", "cls", "z", "S", "moved", "ep"} <= set(rows[-1])
    finally:
        rig.close()


def test_heartbeat_not_advanced_on_raising_step():
    """C-08: engine_hb_ns and engine_ok_s advance only when step() completes."""
    rig = Rig("hb", "2026-10-21")
    try:
        rig.warm()
        rig.now += 0.1; rig.write(25210.0)
        assert rig.eng.tick() is True
        hb, ok = int(rig.t.c("engine_hb_ns")), rig.eng.engine_ok_s
        assert hb > 0 and ok is not None
        rig.t.set("engine_hb_ns", 0)

        def boom():
            raise RuntimeError("probe")
        rig.eng.step = boom
        assert rig.eng.tick() is False
        assert int(rig.t.c("engine_hb_ns")) == 0 and rig.eng.engine_ok_s == ok
    finally:
        rig.close()


def test_state_blob_fields_and_ltt():
    rig = Rig("blob", "2026-10-21")
    try:
        rig.warm()
        o = rig.eng.ctx["by_key"][f"NIFTY|OPT|{EXP}|25200|CE"]
        assert abs(o["ltt"] - (rig.now - 2.0)) < 1e-6                 # O-7 observer input for WP-4
        rig.t.rows["ltt"][rig.opt[(25200, "CE")]] = 0.0
        assert rig.eng.option_rows(rig.t.snapshot())[0]["ltt"] is None
        rig.eng.publish()
        _, data = rig.blob.read()
        st = json.loads(data)
        assert abs(st["engine_ok_s"] - rig.eng.engine_ok_s) < 1e-9 if rig.eng.engine_ok_s else st["engine_ok_s"] is None
        assert "atm_iv_interp" in st and "iv_rise_interp" in st
        assert st["atm_iv_interp"] is not None and abs(st["atm_iv_interp"] - 13.0) < 0.2
    finally:
        rig.close()


def test_interp_atm_iv():
    """O-1 observer: linear in strike between the bracketing strikes, CE/PE mean per strike."""
    K = np.array([25200., 25200., 25250., 25250.])
    iv = np.array([0.12, 0.14, 0.15, np.nan])
    assert abs(engine_main._interp_atm_iv([25200., 25250.], K, iv, 25225.0) - 0.14) < 1e-12
    assert abs(engine_main._interp_atm_iv([25200., 25250.], K, iv, 25200.0) - 0.13) < 1e-12
    assert engine_main._interp_atm_iv([25200., 25250.], K, iv, 25300.0) is None


def test_iv_rise_interp_is_observer_only():
    rig = Rig("ivr", "2026-10-21")
    try:
        rig.warm()
        rig.eng.domino.episode = {"id": 5, "iv0": rig.eng.atm_iv, "iv0_interp": rig.eng.atm_iv_interp - 0.01,
                                  "t0": rig.now, "dir": 1, "type": "BASKET-LED", "first": "S0", "fut0": 25210.0,
                                  "stock_cross": {}, "max_S": 0.0}
        orig = rig.eng.domino.update
        rig.eng.domino.update = lambda *a, **k: None            # keep the hand-made episode alive
        rig.step(25210.0)
        rig.eng.domino.update = orig
        assert abs(rig.eng.ctx["iv_rise_interp"] - 1.0) < 0.05
        assert abs(rig.eng.ctx["iv_rise_since_onset"]) < 0.05    # the trigger's input is unchanged
    finally:
        rig.close()


def test_log_has_market_time():
    lines = []
    engine_main.MKT["dt"] = datetime(2026, 10, 21, 11, 22, 33, tzinfo=config.IST)
    real = print
    try:
        import builtins
        builtins.print = lambda s, **k: lines.append(s)
        engine_main.log("hello")
    finally:
        builtins.print = real
    assert "mkt=11:22:33 ENGINE hello" in lines[-1]


def test_end_day_cannot_break_stop_path():
    rig = Rig("stop", "2026-10-21")
    try:
        rig.warm()

        def boom():
            raise RuntimeError("probe")
        rig.eng.end_day = boom
        rig.t.set("stop", 1)
        rig.eng.run()                                           # must return, not raise
    finally:
        rig.close()


def test_d124_live_mode_tick_and_warm_state_round_trip():
    """The D-123 edit dropped WARM_SAVE_S / WARM_MAX_AGE_S from config; only live mode reads them, so every
    suite passed while the live engine would have raised on every tick. This runs the live-only path."""
    rig = Rig("live", "2026-10-21")
    try:
        rig.warm()
        live = engine_main.Engine(rig.t, rig.blob, "live")
        live.load_registry()
        live.start_day("2026-10-21")
        rig.eng = live
        for _ in range(5):
            rig.now += 0.1; rig.write(25210.0)
            assert live.tick() is True                             # no exception anywhere on the live path
        live._last_warm = 0.0                                      # force a warm save now
        rig.now += 0.1; rig.write(25210.0)
        assert live.tick() is True
        assert os.path.exists(live._warm_path("2026-10-21"))
        assert len(live.spot_hist) >= 1
        again = engine_main.Engine(rig.t, rig.blob, "live")        # a same-day restart restores the histories
        again.load_registry()
        real_time = engine_main.time.time
        engine_main.time.time = lambda: rig.now + 5.0              # the rig runs on a fake 10:00 clock; the restore ages the file by wall time
        try:
            again.start_day("2026-10-21")
        finally:
            engine_main.time.time = real_time
        assert len(again.spot_hist) == len(live.spot_hist) and again.regime is not None
    finally:
        rig.close()


def test_d124_spot_range_needs_coverage_not_just_span():
    rig = Rig("cov", "2026-10-21")
    try:
        rig.warm()
        e = rig.eng
        e.now_s = 10_000.0
        e.spot_hist.clear()
        for t in (9_280.0, 9_281.0, 9_282.0, 9_283.0):              # 4 stale samples 12 min ago ...
            e.spot_hist.append((t, 25200.0))
        for t in range(9_940, 10_000):                             # ... and 60 fresh ones: spans 12 min, covers 1
            e.spot_hist.append((float(t), 25210.0 + (t % 3)))
        assert e._spot_range() == (None, None)
        e.spot_hist.clear()
        for t in range(9_270, 10_000):                             # a covered window
            e.spot_hist.append((float(t), 25200.0 + (t % 40)))
        hi, lo = e._spot_range()
        assert hi == 25239.0 and lo == 25200.0
    finally:
        rig.close()


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
