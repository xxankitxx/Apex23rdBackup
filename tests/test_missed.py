"""apex.engine.missed (docs/29): the flat twin observes, never touches the real book; episodes dedupe; the real
trade's own signal is not counted as missed; counterfactual outcomes settle; the shared LiveDay is never copied."""
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.engine import missed, paper  # noqa: E402

T0 = datetime(2026, 11, 6, 10, 0, tzinfo=config.IST)


def _ctx(k):
    dt = T0 + timedelta(seconds=k)
    return {"now_s": dt.timestamp(), "now_dt": dt, "episode": {"id": 7}, "by_key": {}, "blackout": {}}


def _opt(rr):
    return {"key": f"NIFTY|OPT|2026-11-10|24500|{rr}", "id": 3, "strike": 24500.0, "rr": rr, "ltp": 100.0,
            "bid": 99.5, "ask": 100.5, "expiry": "2026-11-10", "delta": 0.55, "age": 0.2}


class _Eng:
    """Fires the given side from second `start` on, every second (a signal that never consumes itself)."""
    gates = []

    def __init__(self, side, start):
        self.side, self.start, self.k = side, start, 0

    def _entry_choice(self, b, ctx, gates):
        b.ctl["fire_id"] = "x"
        if self.k >= self.start:
            return True, _opt(self.side), "TEST fire", None
        return False, None, "quiet", "quiet"


def _real_book():
    b = paper.Book("bk", {}, "2026-11-06")
    b.pos = {"key": "NIFTY|OPT|2026-11-10|24500|CE", "rr": "CE", "time_in": "09:59:00", "id": 3}
    b.ctl["swing_last"] = {"d": 1}
    b.fired_episodes.add(1)
    return b


def test_off_unless_switched_on(monkeypatch):
    monkeypatch.delenv("APEX_RECORD_MISSED", raising=False)
    assert not missed.enabled()
    monkeypatch.setenv("APEX_RECORD_MISSED", "1")
    assert missed.enabled()


def test_twin_never_touches_the_real_book_and_episodes_dedupe(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "FILL_NEXT_PRINT", True)    # other suites switch it off at import
    rec = missed.MissedRecorder("2026-11-06", str(tmp_path))
    b = _real_book()
    before = (json.dumps(b.to_json(), default=str, sort_keys=True), dict(b.ctl), set(b.fired_episodes))
    eng = _Eng("PE", start=2)
    for k in range(0, 40):
        eng.k = k
        rec.step_paper(eng, "bk", b, _ctx(k))
    after = (json.dumps(b.to_json(), default=str, sort_keys=True), dict(b.ctl), set(b.fired_episodes))
    assert after == before                                      # the real book is untouched
    eps = [e for e in rec.live if e.eid]
    assert len(eps) == 1                                        # 38 consecutive fires = one episode
    ep = eps[0]
    assert ep.side == "PE" and ep.relation == "opposite" and ep.count == 38
    assert ep.cf is not None and ep.cf.ctl.get("pending_entry")   # the counterfactual waits for its first print
    assert ep.cf is not b and ep.cf.pos is None


def test_the_real_trades_own_signal_is_not_a_missed_trade(tmp_path):
    rec = missed.MissedRecorder("2026-11-06", str(tmp_path))
    b = _real_book()                                            # real book holds a CE
    eng = _Eng("CE", start=0)                                   # the twin keeps seeing the same CE signal
    for k in range(0, 20):
        eng.k = k
        rec.step_paper(eng, "bk", b, _ctx(k))
    assert [e for e in rec.live if e.eid] == []


def test_twin_is_dropped_when_the_real_book_is_free(tmp_path):
    rec = missed.MissedRecorder("2026-11-06", str(tmp_path))
    b = _real_book()
    eng = _Eng("PE", start=99)
    rec.step_paper(eng, "bk", b, _ctx(0))
    assert "bk" in rec.twins
    b.pos = None
    rec.step_paper(eng, "bk", b, _ctx(1))
    assert "bk" not in rec.twins


class _Cf:
    def __init__(self, trades=(), pos=None, pending=None):
        self.trades, self.pos, self.ctl = list(trades), pos, ({"pending_entry": pending} if pending else {})


def test_settle_and_write(tmp_path):
    rec = missed.MissedRecorder("2026-11-06", str(tmp_path))
    ep = rec._fire("bk", "PE", _ctx(0), "TEST", 1.5, {"rr": "CE", "key": "k", "time_in": "09:59:00"})
    rec._settle(ep, _Cf(trades=[{"time_in": "10:00:02", "time_out": "10:07:00", "entry": 100.0, "exit": 112.0,
                                 "hold_s": 418, "pnl_rs": 7800.0, "ret_pct": 12.0, "peak_pts": 14.0,
                                 "reason": "TRAIL", "strike": 24500.0, "rr": "PE"}]))
    assert ep.done and ep.cf_status == "closed"
    rec.close()
    row = json.loads(open(tmp_path / "missed_2026-11-06.jsonl", encoding="utf-8").read())
    assert row["is_counterfactual"] is True and row["snapshot_id"] is None
    assert row["relation"] == "opposite" and row["cf_pnl_rs"] == 7800.0 and row["fire_count"] == 1
    ep2 = rec._fire("bk", "CE", _ctx(100), "TEST", None, None)
    rec._settle(ep2, _Cf())                                     # no fill, no position: the entry lapsed
    assert ep2.cf_status == "lapsed"


class _D:
    def __init__(self):
        self.t_open = T0.timestamp() - 600
        self.T = list(range(30000))
        self.i = -1
        self.big = list(range(100000))                          # stands in for the shared arrays


class _Strat:
    def __init__(self, D):
        self.D = D                                               # a strategy may hold the LiveDay
        self.state = 0

    def on_second(self, i, D, pos):
        self.state += 1
        return ("BUY", 24500, "PE", "TEST v=+20") if pos is None else None


class _Ad:
    def __init__(self, D):
        self.D, self.day, self.strat, self.last_i = D, "2026-11-06", _Strat(D), -1


def test_council_twin_copies_the_strategy_not_the_live_day(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "FILL_NEXT_PRINT", True)
    rec = missed.MissedRecorder("2026-11-06", str(tmp_path))
    D = _D()
    ad = _Ad(D)
    b = _real_book()
    ctx = _ctx(0)
    ctx.update(w0="2026-11-10", by_key={_opt("PE")["key"]: _opt("PE")})
    i0 = int(ctx["now_s"] - D.t_open)
    D.i = i0
    rec.step_council(None, "c20", ad, b, ctx)                   # creates the twin, does not step it
    tw = rec.twins["c20"]
    assert tw is not ad.strat and tw.D is D and tw.state == 0
    ctx1 = _ctx(1)
    ctx1.update(w0="2026-11-10", by_key={_opt("PE")["key"]: _opt("PE")})
    D.i = i0 + 1
    rec.step_council(None, "c20", ad, b, ctx1)
    eps = [e for e in rec.live if e.eid]
    assert len(eps) == 1 and eps[0].side == "PE" and eps[0].relation == "opposite"
    assert ad.strat.state == 0                                  # the real strategy was never stepped by the twin
    cfb, cfa = eps[0].cf
    assert cfa.strat is not tw and cfa.D is D and cfb.ctl.get("pending_entry")


def test_a_counterfactual_never_resets_the_real_books_gain_trail_window():
    """7 Nov: paper._GT_BUF kept one smoothing window per book NAME; a counterfactual copy (same name) wiped the
    real book's window, so the real gt_peak differed (3 Nov replay). A counterfactual now has its own gt_id."""
    paper._GT_BUF.clear()
    p = {"gt_arm_pct": 20.0, "gt_smooth_s": 30.0, "gt_keep": 0.8}
    real, cf = paper.Book("t28_gap", p, "2026-11-03"), paper.Book("t28_gap", p, "2026-11-03")
    cf.gt_id = "t28_gap#1"
    rp = {"entry": 100.0, "t_in": 0.0}
    cp = {"entry": 100.0, "t_in": 5.0}
    for k, px in enumerate([101, 103, 106, 108, 110]):
        ctx = {"now_s": 10.0 + k}
        paper._hard_stop_gain_trail(real, ctx, rp, px, {"age": 0.1})
        paper._hard_stop_gain_trail(cf, ctx, cp, 90.0, {"age": 0.1})
    alone = {"entry": 100.0, "t_in": 0.0}
    b2 = paper.Book("solo", p, "2026-11-03")
    for k, px in enumerate([101, 103, 106, 108, 110]):
        paper._hard_stop_gain_trail(b2, {"now_s": 10.0 + k}, alone, px, {"age": 0.1})
    assert rp["gt_peak"] == alone["gt_peak"]              # identical to a book that ran alone
