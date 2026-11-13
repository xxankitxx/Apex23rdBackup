"""12 Nov (PKG-02): the Forecast Lab's learning state and its runner's lifecycle. A saved state is loaded, migrated
or rejected honestly and never reported as 'live state' unless it fully loaded; a restart keeps the true morning
copy; a heavyweight list change costs a moment of breadth, not the day; and the runner never holds the shared table,
never trusts an old STOP file or a stale engine report, and writes ok:false instead of leaving an old verdict up."""
import json
import os
import shutil
import uuid
from datetime import datetime

import numpy as np
import pytest

from apex import config
from apex.forecast_lab import core as C
from apex.forecast_lab import live as L

T0 = datetime(2026, 11, 12, 9, 20, 0, tzinfo=config.IST).timestamp()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_V1 = [os.path.join(ROOT, "data", "forecast_lab", n) for n in ("state.v1.2026-11-11.json", "state.json")]


def fut_rows(n, start=T0, hw=None, seed=1):
    rng = np.random.default_rng(seed)
    F = 25000.0
    out = []
    for i in range(n):
        F += rng.standard_normal()
        r = dict(t=start + i, fb=F - 0.5, fa=F + 0.5, fl=F, fv=1000.0 * i, fbq=500.0, faq=500.0)
        if hw is not None:
            k = hw
            r.update(hw=np.full(k, 1000.0) + i, hw_w=np.ones(k), hw_bank=np.zeros(k, bool),
                     hw_syms=tuple(f"S{j}" for j in range(k)))
        out.append(r)
    return out


def step_all(lab, rows):
    for r in rows:
        lab.step(r)
    return lab


def v1_state():
    """A version 1 file as the 11 Nov runner wrote it: five experts, no vol basis, no frozen copy."""
    lab = C.Lab(options=False)
    s = json.loads(json.dumps(lab.to_json()))
    five = ("still", "momentum", "flow", "reversion", "blend")
    rng = np.random.default_rng(4)
    s = dict(version=1, day="2026-11-11",
             rls={e: s["rls"][e] for e in five},
             hedge=[list(w / w.sum()) for w in rng.random((len(C.H), 5)) + 0.1],
             hedge_n=[1000 + j for j in range(len(C.H))],
             kappa=[0.82, 0.89, 0.98, 1.05, 1.03, 1.02, 0.87], z80=[1.32, 1.18, 1.12, 1.37, 1.43, 1.56, 1.55],
             iv_beta=-2.85e-5, iv_beta_n=60672, iv_res=1.1e-4, obias=[0.003] * 7, oscale=[1.94] * 7,
             scale={"ofi30": 9991.3}, alltime={"fut_n": 412401, "opt_n": 4234}, score={"n": [5] * 7})
    s["rls"]["momentum"][3]["th"] = [0.1, -0.2, 0.05]
    return s


class FakeBrain:
    ok = True

    def __init__(self, h):
        self.meta = {"hash": h}


# ── load, migrate, reject ──────────────────────────────────────────────────────────────────────────────────────
def check_migrated(lab, s):
    ok, why = lab.load_status["ok"], lab.load_status["why"]
    assert ok and why.startswith("migrated v1"), why
    names = list(s["rls"].keys())
    for j in range(len(C.H)):
        saved = np.array(s["hedge"][j], float)
        got = np.array([lab.hedge[j].w[C.EXPERTS.index(e)] for e in names])
        assert np.allclose(got / got.sum(), saved / saved.sum())
        assert abs(lab.hedge[j].w.sum() - 1.0) < 1e-12
        fl = lab.hedge[j].share / lab.hedge[j].m
        for e in ("ridge", "trees"):                                  # the fixed-share floor, then renormalised
            assert abs(lab.hedge[j].w[C.EXPERTS.index(e)] - fl / (saved.sum() + 2 * fl)) < 1e-12
    assert np.all(lab.kappa == 1.0) and np.all(lab.z80 == 1.2816)
    assert np.all(lab.oscale == 1.0) and np.all(lab.obias == 0.0)
    assert lab.iv_res == s["iv_res"] and lab.scale == s["scale"] and lab.alltime == s["alltime"]
    assert lab.iv_beta == s["iv_beta"] and abs(lab._b_sxy / lab._b_sxx - s["iv_beta"]) < 1e-12
    assert np.allclose(lab.rls["momentum"][3].th, s["rls"]["momentum"][3]["th"])
    assert getattr(lab, "_saved_score", None) is None                  # a v1 score is not mixed into v3 sums


def test_v1_migrates():
    s = v1_state()
    check_migrated(C.Lab(state=s, options=False), s)


def test_v1_migrates_the_real_11_nov_file(tmp_path):
    src = next((p for p in REAL_V1 if os.path.exists(p)), None)
    if src is None:
        pytest.skip("no 11 Nov v1 state on this machine")
    p = tmp_path / "state.json"
    shutil.copy(src, p)                                               # a scratch copy: the live file is only read
    s = json.load(open(p, encoding="utf-8"))
    if L.state_version_of(s) != 1:
        pytest.skip("the state on this machine is no longer version 1")
    lab = C.Lab(options=False)
    learning, notes, keep = L.pick_state(lab, [(str(p), "state.json")])
    check_migrated(lab, s)
    assert learning["updates"] == sum(s["hedge_n"]) and learning["source"] == "state.json"


def test_v1_never_reports_live_state(tmp_path):
    p = tmp_path / "state.json"
    p.write_text(json.dumps(v1_state()), encoding="utf-8")
    lab = C.Lab(options=False)
    learning, notes, keep = L.pick_state(lab, [(str(p), "state.json"), (str(tmp_path / "w.json"), "state_warm.json")])
    assert learning["ok"] and learning["why"].startswith("migrated v1")
    assert L.state_from_label(learning) != "live state" and "live state" not in " ".join(notes)
    assert keep == [(str(p), 1, "2026-11-11")]
    assert "copied" in L.copy_aside(str(p), 1, "2026-11-11", "2026-11-12")
    assert (tmp_path / "state.v1.2026-11-11.json").exists()
    assert "already" in L.copy_aside(str(p), 1, "2026-11-11", "2026-11-12")      # once only
    full = C.Lab(options=False)
    q = tmp_path / "v3.json"
    q.write_text(json.dumps(full.to_json()), encoding="utf-8")
    learning, _, keep = L.pick_state(C.Lab(options=False), [(str(q), "state.json")])
    assert L.state_from_label(learning) == "live state" and keep == []


def test_unknown_version_and_garbage_are_discarded_not_loaded():
    lab = C.Lab(options=False)
    w0 = lab.hedge[3].w.copy()
    ok, why, _ = lab.load(dict(version=9, rls={}))
    assert not ok and why == "discarded: state version 9 != 3"
    ok, why, _ = lab.load(dict(version=3, rls={"still": []}))
    assert not ok and why.startswith("unreadable")
    assert np.allclose(lab.hedge[3].w, w0)                            # nothing was half-assigned


def test_out_of_bounds_calibration_is_reset_and_the_learning_kept(tmp_path):
    """12 Nov: the live state.json saved at 15:40 had z80 0.75 (a wide-range day) and was rejected whole, so the next
    start would have dropped the day's learning for the older warm file. Now only kappa / z80 restart."""
    good = C.Lab(options=False)
    good.kappa[:] = 1.1
    for h in good.hedge:
        h.w = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.25, 0.25])
        h.n = 1234
    s_good = json.loads(json.dumps(good.to_json()))
    st, warm = tmp_path / "state.json", tmp_path / "state_warm.json"
    warm.write_text(json.dumps(dict(s_good, kappa=[1.4] * 7)), encoding="utf-8")
    cands = [(str(st), "state.json"), (str(tmp_path / "state.prev.json"), "state.prev.json"), (str(warm), "state_warm.json")]
    for bad, word in ((dict(s_good, kappa=[3.0] * 7), "kappa 3.00"), (dict(s_good, z80=[0.75] * 7), "z80 0.75")):
        st.write_text(json.dumps(bad), encoding="utf-8")
        lab = C.Lab(options=False)
        learning, notes, keep = L.pick_state(lab, cands)
        assert learning["source"] == "state.json" and learning["ok"], notes
        assert "kappa/z80 reset" in learning["why"] and word in learning["why"] and "outside" in learning["why"]
        assert np.all(lab.kappa == 1.0) and np.allclose(lab.z80, C.Z80_START)
        assert all(h.n == 1234 for h in lab.hedge) and np.allclose(lab.hedge[0].w[-1], 0.25)   # the learning is kept
        assert learning["updates"] == 1234 * len(lab.hedge) and keep == []
        assert L.state_from_label(learning).startswith("state.json, loaded, kappa/z80 reset")
    # offline walks (no bounds) still carry a large learned kappa
    assert C.Lab(state=dict(s_good, kappa=[3.0] * 7), options=False).load_status["ok"]
    assert np.allclose(C.Lab(state=dict(s_good, kappa=[3.0] * 7), options=False).kappa, 3.0)


def test_brain_hash_change_resets_kappa_z80():
    a = C.Lab(options=False, brain=FakeBrain("aaa"))
    a.kappa[:] = 1.3
    a.z80[:] = 1.5
    a.oscale[:] = 1.2
    for h in a.hedge:
        h.w = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.25, 0.25])
    s = json.loads(json.dumps(a.to_json()))
    assert s["vol_basis"] == "brain:aaa"
    same = C.Lab(state=s, options=False, brain=FakeBrain("aaa"))
    assert same.load_status["why"] == "loaded" and np.allclose(same.kappa, 1.3) and np.allclose(same.z80, 1.5)
    other = C.Lab(state=s, options=False, brain=FakeBrain("bbb"))
    assert other.load_status["ok"] and "volatility basis changed" in other.load_status["why"]
    assert np.all(other.kappa == 1.0) and np.all(other.z80 == 1.2816) and np.all(other.oscale == 1.0)
    fl = other.hedge[0].share / other.hedge[0].m
    w = other.hedge[3].w
    assert abs(w.sum() - 1) < 1e-12 and w[5] < 2 * fl and w[6] < 2 * fl
    assert np.allclose(w[:5] / w[:5].sum(), 0.2)
    plain = C.Lab(state=s, options=False)                             # brain to plain clock: the same reset
    assert "brain:aaa to plain" in plain.load_status["why"] and np.all(plain.kappa == 1.0)


def test_frozen_copy_restored_same_day_and_restart_counted():
    lab = step_all(C.Lab(options=False), fut_rows(20))
    morning = [a.copy() for a in lab.frozen["th"]["blend"]]
    for r in lab.rls["blend"]:
        r.th = r.th + 0.3                                             # the live models learn after the open
    lab.kappa[:] = 1.2
    lab.score["n"][3] = 7
    s = json.loads(json.dumps(lab.to_json()))
    assert s["frozen"]["day"] == "2026-11-12" and s["restarts"] == 0
    again = C.Lab(state=s, options=False)
    step_all(again, fut_rows(3, start=T0 + 4000))
    assert all(np.allclose(a, b) for a, b in zip(again.frozen["th"]["blend"], morning))     # not re-frozen
    assert np.allclose(again.frozen["kappa"], 1.0) and again.restarts == 1 and again.score["n"][3] == 7
    s2 = json.loads(json.dumps(again.to_json()))
    third = step_all(C.Lab(state=s2, options=False), fut_rows(3, start=T0 + 5000))
    assert third.restarts == 2
    nxt = step_all(C.Lab(state=s2, options=False), fut_rows(3, start=T0 + 86400))
    assert nxt.restarts == 0 and np.allclose(nxt.frozen["kappa"], 1.2)  # a new day freezes the models it starts with


def test_iv_beta_sums_survive_a_restart():
    lab = C.Lab(options=False)
    lab._b_sxx, lab._b_sxy, lab.iv_beta = 4.0e5, -80.0, -2.0e-4
    again = C.Lab(state=json.loads(json.dumps(lab.to_json())), options=False)
    assert again._b_sxx == 4.0e5 and again._b_sxy == -80.0
    again._iv_learn(0.0, 25000.0, 0.12, 25000.0)                      # no update yet: needs 13 samples
    assert again.iv_beta == -2.0e-4


def test_extra_state_round_trips():
    lab = C.Lab(options=False)
    lab.extra_state["held"] = {"n": 3, "sum": 1.5}
    again = C.Lab(state=json.loads(json.dumps(lab.to_json())), options=False)
    assert again.extra_state == {"held": {"n": 3, "sum": 1.5}}


def test_heavyweight_list_change_resets():
    lab = step_all(C.Lab(options=False), fut_rows(30, hw=14))
    assert len(lab.hw_px) == 30
    step_all(lab, fut_rows(10, start=T0 + 30, hw=13))                 # a feed restart dropped one stock
    notes = [e for e in lab.events if "heavyweight list changed" in e]
    assert notes == ["heavyweight list changed (14 to 13 stocks): breadth reset"]
    assert len(lab.hw_px) == 10 and all(p.shape == (13,) for p in lab.hw_px)
    assert lab.last_t == T0 + 39                                       # every step ran
    rows = fut_rows(3, start=T0 + 40, hw=13)
    for r in rows:                                                     # same length, different stocks
        r["hw_syms"] = tuple(f"X{j}" for j in range(13))
    step_all(lab, rows)
    assert len([e for e in lab.events if "heavyweight list changed" in e]) == 2 and len(lab.hw_px) == 3


# ── the runner ─────────────────────────────────────────────────────────────────────────────────────────────────
def test_stop_file_older_than_start_ignored(tmp_path):
    p = tmp_path / "STOP"
    p.write_text("")
    old = os.path.getmtime(p)
    started = old + 10.0
    assert not L.stop_requested(str(p), started)
    msg = L.clear_old_stop(str(p), started)
    assert msg.startswith("old STOP file removed") and not p.exists()
    assert L.clear_old_stop(str(p), started) is None
    p.write_text("")
    os.utime(p, (started + 5, started + 5))
    assert L.stop_requested(str(p), started) and L.clear_old_stop(str(p), started) is None


def test_second_runner_refused_by_lock(tmp_path):
    path = str(tmp_path / "live.lock")
    a, b = L.RunLock(path), L.RunLock(path)
    assert a.acquire(1000.0)
    try:
        assert not b.acquire(1001.0)
        info = L.read_lock(path)                                       # readable while locked (run_apex names the pid)
        assert info["pid"] == os.getpid() and info["started"] == 1000.0
    finally:
        a.release()
    assert b.acquire(1002.0)                                           # a stale file from a dead runner never blocks
    b.release()


def test_error_writes_ok_false_payload_nan_cleaned(tmp_path):
    p = L.error_payload("forecaster error: ValueError: x", T0, None, 3, runner=dict(loop_ms=float("nan"), x=np.float64("inf")))
    text = L.dumps_payload(p)
    d = json.loads(text)
    assert d["ok"] is False and d["runner"]["loop_ms"] is None and d["runner"]["x"] is None
    assert d["say"]["now"] == ["forecaster error: ValueError: x"] and d["date"] == "2026-11-12" and d["errors"] == 3
    out = str(tmp_path / "f.json")
    assert L.write_atomic(out, text) and json.load(open(out))["ok"] is False
    pv = dict(ok=True, t=T0, F=float("nan"), path=[dict(q10=np.float32("nan"))])
    assert json.loads(L.dumps_payload(pv))["F"] is None


def test_engine_freshness_uses_engine_age_ms():
    s = dict(engine_age_ms=30000, conductor=dict(reason="holding", owner="c20"),
             pos=dict(key="NIFTY|2026-11-17|25000|CE", strike=25000, rr="CE", expiry="2026-11-17", entry=100.0, qty=75,
                      t_in=1.0, rules=dict(sl_px=90.0, trail_px=95.0, flat_at="15:15", other=1)),
             forecast=dict(rows=[dict(strike=25000, side="CE", tag="exe")], expiry="2026-11-17"))
    info = L.parse_engine(s, now=1000.0)
    assert info["t"] == 970.0 and info["pos"]["rules"]["sl_px"] == 90.0 and "other" not in info["pos"]["rules"]
    v = L.engine_view(info, now=1000.0)
    assert v["pos"] is None and v["old_rows"] == [] and "30 s old" in v["account"]["reason"]
    fresh = L.parse_engine(dict(s, engine_age_ms=500), now=1000.0)
    assert L.engine_view(fresh, now=1000.0) is fresh and fresh["pos"]["qty"] == 75
    none = L.engine_view(None, now=1000.0, err="URLError")
    assert none["pos"] is None and "not reachable" in none["account"]["reason"]


def test_engine_reader_drops_info_after_two_failed_reads(monkeypatch):
    r = L.EngineReader()
    r.info = dict(t=1.0)
    calls = []

    def boom(*a, **k):
        calls.append(1)
        if len(calls) >= 2:
            r.halt.set()
        raise OSError("down")
    monkeypatch.setattr(L.urllib.request, "urlopen", boom)
    r.halt.wait = lambda s: None
    r.run()
    assert r.info is None and r.fails == 2


def test_output_path_per_port(tmp_path):
    assert os.path.basename(L.out_path(8780)) == "forecast_lab.json"
    assert os.path.basename(L.out_path(8808)) == "forecast_lab_8808.json"
    assert os.path.dirname(L.out_path(8802, out_dir=str(tmp_path))) == str(tmp_path)


def test_stop_time_override(monkeypatch):
    monkeypatch.setenv("APEX_LAB_STOP_AT", "none")
    assert L.stop_at() is None
    monkeypatch.setenv("APEX_LAB_STOP_AT", "21:05")
    assert L.stop_at() == (21, 5)
    monkeypatch.delenv("APEX_LAB_STOP_AT")
    assert L.stop_at() == (15, 40)


def test_save_keeps_the_previous_file(tmp_path):
    st, prev = str(tmp_path / "state.json"), str(tmp_path / "state.prev.json")
    lab = C.Lab(options=False)
    assert L.save_state(lab, st, prev) and not os.path.exists(prev)
    lab.kappa[:] = 1.4
    assert L.save_state(lab, st, prev)
    assert json.load(open(prev))["kappa"][0] == 1.0 and json.load(open(st))["kappa"][0] == 1.4


def test_table_is_read_per_call_and_never_held():
    from apex.table import Table
    name = "apex_pkg02_" + uuid.uuid4().hex[:8]
    assert L.read_table(name) == (None, "trading system not running")
    t = Table(create=True, name=name)
    try:
        t.set("now_ns", 123)
        t.col["ltp"][5] = 25000.0
        got, why = L.read_table(name)
        assert why is None and int(got[0]["now_ns"]) == 123 and got[1]["ltp"][5] == 25000.0
        t.set("stop", 1)
        assert L.read_table(name) == (None, "trading system is stopping")
        t.set("stop", 0)
        L.read_table(name)
    finally:
        t.close()
        t.unlink()
    again = Table(create=True, name=name)                             # the supervisor's restart: nothing holds it
    again.close()
    again.unlink()


def test_chain_trusts_instruments_only_at_the_tables_version(tmp_path, monkeypatch):
    items = [dict(id=0, key="NIFTY|FUT", kind="fut", sym="NIFTY"),
             dict(id=1, key="NIFTY|2099-01-01|25000|CE", kind="opt", sym="NIFTY", expiry="2099-01-01", strike=25000, rr="CE"),
             dict(id=2, key="NIFTY|2099-01-01|25000|PE", kind="opt", sym="NIFTY", expiry="2099-01-01", strike=25000, rr="PE"),
             dict(id=3, key="HDFCBANK|EQ", kind="eq", sym="HDFCBANK", wn=12.0, group="bank")]
    p = tmp_path / "instruments.json"
    p.write_text(json.dumps(dict(version=7, items=items)), encoding="utf-8")
    monkeypatch.setattr(config, "INSTRUMENTS_JSON", str(p))
    ch = L.Chain()
    note = ch.maybe_reload(9)                                          # a rig wrote another registry
    assert not ch.ready and "version 7" in note
    assert ch.maybe_reload(9) is None                                  # not retried every second
    assert ch.maybe_reload(7).startswith("chain loaded") and ch.ready and ch.hw_syms == ("HDFCBANK",)
    assert ch.ids.tolist() == [[1, 2]] and ch.maybe_reload(7) is None
    bad = items + [dict(id=4, key="TCS|EQ", kind="eq", sym="TCS", wn="x")]              # a broken weight, version 8
    p.write_text(json.dumps(dict(version=8, items=bad)), encoding="utf-8")
    assert "keeping the previous chain" in ch.maybe_reload(8)
    assert ch.ready and ch.version == 7 and ch.hw_syms == ("HDFCBANK",) and len(ch.hw_ids) == len(ch.hw_w) == 1


def test_heavyweight_weights_missing_is_skipped_not_raised():
    rows = fut_rows(5, hw=14)
    for r in rows:
        r.pop("hw_w")
    lab = step_all(C.Lab(options=False), rows)
    assert lab.last_t == T0 + 4 and len(lab.hw_px) == 0
    assert [e for e in lab.events if "do not match" in e] == ["heavyweight inputs do not match (14 prices, 0 weights): skipped"]


def test_writes_from_two_threads_use_their_own_tmp_files(tmp_path):
    import threading
    out = str(tmp_path / "f.json")
    errs = []

    def go(k):
        for _ in range(50):
            if not L.write_atomic(out, json.dumps(dict(k=k, pad="x" * 5000))):
                errs.append(k)
    th = [threading.Thread(target=go, args=(k,)) for k in range(2)]
    for x in th:
        x.start()
    for x in th:
        x.join()
    assert json.load(open(out))["k"] in (0, 1)                         # never a torn file
    assert [n for n in os.listdir(tmp_path) if n.endswith(".tmp")] == [] or errs
