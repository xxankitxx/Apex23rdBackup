"""9 Nov (docs/36, docs/37): the second-generation shadow books. The signal engine (apex/engine/gen2.py) on synthetic
tapes, the book mode in paper.py, and the registration. Nothing here says the books make money: these tests pin the
definitions, causality and the reset rules."""
import random
from datetime import datetime

import pytest

from apex import config
from apex.engine import gen2, paper

T0 = 1_794_196_800.0


class Tape:
    """A synthetic Nifty future: price responds to signed flow (20 points per unit of flow / depth)."""

    def __init__(self, seed=3, hw=None):
        self.g = gen2.Gen2()
        self.r = random.Random(seed)
        self.t, self.mid, self.ttq = T0, 25000.0, 1_000_000.0
        self.bid, self.ask = 24999.5, 25000.5
        self.hw = hw
        self.seen = []

    def step(self, dq=0.0, sign=0, move=None, bd=1000.0, ad=1000.0, hw=None, ok=True, dt=1.0, **kw):
        ltp = self.ask if sign > 0 else (self.bid if sign < 0 else 0.5 * (self.bid + self.ask))
        self.ttq += dq
        self.mid += (20.0 * sign * dq / 1000.0) if move is None else move
        self.bid, self.ask = self.mid - 0.5, self.mid + 0.5
        self.t += dt
        if hw is not None:
            self.hw = hw
        px = self.hw
        self.g.update(self.t, self.bid, self.ask, ltp, self.ttq, bd, ad, px,
                      [10.0, 10.0, 10.0, 10.0] if px is not None else None,
                      ["bank", "bank", "it", "it"] if px is not None else None, ok=ok, **kw)
        for n, s in self.g.sig.items():
            if s["t"] == self.t:
                self.seen.append((n, s))

    def warm(self, n=1000):
        for _ in range(n):
            self.step(dq=self.r.uniform(0, 100), sign=self.r.choice((-1, 1)))
        assert self.g.warm and self.g.beta > 0 and self.g.a is not None

    def names(self):
        return [n for n, _ in self.seen]


def test_nothing_before_warm_up_and_beta_is_positive():
    tp = Tape()
    for _ in range(gen2.WARM_S - 5):
        tp.step(dq=tp.r.uniform(0, 100), sign=tp.r.choice((-1, 1)))
    assert not tp.seen and not tp.g.warm
    tp.warm(600)
    assert 10.0 < tp.g.beta < 40.0                       # the tape was built with 20 points per unit


def test_absorbed_buying_then_a_turn_fires_the_reversal_once():
    tp = Tape()
    tp.warm()
    tp.seen.clear()
    for _ in range(70):                                   # heavy buying, the price does not move, offers stay
        tp.step(dq=40.0, sign=1, move=0.0)
    assert tp.g.e1 and tp.g.e1["state"] == "conf" and tp.g.e1["side"] == 1
    assert 10.0 < tp.g.e1["beta"] <= 20.5                 # 10 Nov (O6): the response known when the episode formed
    assert "n01_rev" not in tp.names() and "n01_rel" not in tp.names()
    for _ in range(16):                                   # the buying stops and the price gives way (a quarter of the
        tp.step(dq=5.0, sign=-1, move=-1.0)               # expected 48 points = 12)
    rev = [s for n, s in tp.seen if n == "n01_rev"]
    assert len(rev) == 1 and rev[0]["dir"] == -1 and rev[0]["stop_px"] > tp.mid and 8.0 <= rev[0]["tp"] <= 25.0
    assert "n01_rel" not in tp.names()
    assert tp.g.e1["state"] == "spent"
    for _ in range(30):                                   # the same episode never fires twice
        tp.step(dq=5.0, sign=-1, move=-0.5)
    assert tp.names().count("n01_rev") == 1


def test_absorbed_buying_then_offers_pulled_fires_the_release():
    tp = Tape()
    tp.warm()
    tp.seen.clear()
    for _ in range(70):
        tp.step(dq=300.0, sign=1, move=0.0)
    for _ in range(6):                                    # offers thin out and the price goes through the zone
        tp.step(dq=300.0, sign=1, move=1.0, ad=300.0)
    rel = [s for n, s in tp.seen if n == "n01_rel"]
    assert len(rel) == 1 and rel[0]["dir"] == 1 and rel[0]["stop_px"] < tp.mid
    assert "n01_rev" not in tp.names()


def test_normal_impact_is_not_absorption():
    tp = Tape()
    tp.warm()
    tp.seen.clear()
    for _ in range(90):                                   # heavy buying and the price responds as the model expects
        tp.step(dq=300.0, sign=1)
    for _ in range(12):
        tp.step(dq=5.0, sign=-1, move=-1.0)
    assert "n01_rev" not in tp.names() and "n01_rel" not in tp.names()
    assert "ctl_flow" in tp.names()                       # the flow-only control does fire: that is what it is for


def test_impact_relaxation_needs_decay_and_stopped_flow():
    tp = Tape()
    tp.warm()
    tp.seen.clear()
    for _ in range(8):                                    # a burst of buying moves the price up
        tp.step(dq=250.0, sign=1)
    assert tp.g.i2 and tp.g.i2["sign"] == 1 and "n02_relax" not in tp.names()
    for _ in range(25):                                   # the buying stops; the price starts back
        tp.step(dq=2.0, sign=-1, move=-0.4)
        if "n02_relax" in tp.names():
            break
    s = [x for n, x in tp.seen if n == "n02_relax"]
    assert len(s) == 1 and s[0]["dir"] == -1 and s[0]["i_sign"] == 1 and s[0]["i_peak"] >= gen2.P["n02_i_min"]
    assert tp.g.void("n02_relax", s[0], -1) is None
    for _ in range(12):                                   # the buying comes back harder: the thesis is void
        tp.step(dq=600.0, sign=1)
    assert (tp.g.void("n02_relax", s[0], -1) or "").startswith("REBUILD")


def test_leadership_transfer_and_fragment_exit():
    hw = [1000.0, 1000.0, 1000.0, 1000.0]
    tp = Tape(hw=hw)
    tp.warm()
    tp.seen.clear()
    for _ in range(130):                                  # banks up, IT down, the index still
        hw = [hw[0] * 1.00002, hw[1] * 1.00002, hw[2] * 0.99999, hw[3] * 0.99999]
        tp.step(dq=1.0, sign=0, move=0.0, hw=hw)
    assert tp.g.e6 and tp.g.e6["lead"] == "bank" and tp.g.e6["opp"] == "it" and tp.g.e6["dir"] == 1
    assert "n06_lead" not in tp.names()
    for _ in range(40):                                   # IT turns and joins
        hw = [hw[0] * 1.00002, hw[1] * 1.00002, hw[2] * 1.00003, hw[3] * 1.00003]
        tp.step(dq=1.0, sign=0, move=0.05, hw=hw)
    s = [x for n, x in tp.seen if n == "n06_lead"]
    assert len(s) == 1 and s[0]["dir"] == 1 and s[0]["lead"] == "bank"
    for _ in range(70):                                   # the banks roll over: leadership fragments
        hw = [hw[0] * 0.99998, hw[1] * 0.99998, hw[2], hw[3]]
        tp.step(dq=1.0, sign=0, move=0.0, hw=hw)
    assert (tp.g.void("n06_lead", s[0], 1) or "").startswith("FRAGMENT")


def test_a_gap_drops_every_open_episode_and_nothing_is_stitched():
    tp = Tape()
    tp.warm()
    for _ in range(70):
        tp.step(dq=300.0, sign=1, move=0.0)
    assert tp.g.e1 is not None
    beta = tp.g.beta
    tp.step(ok=False)                                     # the engine's blackout
    assert tp.g.e1 is None and tp.g.i2 is None and len(tp.g.t) == 0 and tp.g.gaps == 1
    assert tp.g.beta == beta and not tp.g.warm            # the fit is kept, the windows refill before any signal
    tp.t += 30.0                                          # a silent hole in the feed
    tp.step(dq=10.0, sign=1)
    assert len(tp.g.t) == 1


def test_truncation_invariance():
    """The state at second N is the same whether or not later seconds exist (no look-ahead)."""
    a, b = Tape(seed=9), Tape(seed=9)
    for _ in range(900):
        a.step(dq=a.r.uniform(0, 100), sign=a.r.choice((-1, 1)))
        b.step(dq=b.r.uniform(0, 100), sign=b.r.choice((-1, 1)))
    va, na = a.g.view(), len(a.seen)
    for _ in range(200):
        b.step(dq=300.0, sign=1, move=0.0)
    assert va == a.g.view() and a.seen == b.seen[:na]


# ── the book mode ────────────────────────────────────────────────────────────────────────────────────────────────────
def _ctx(g, now, fut):
    return {"gen2": g, "now_s": now, "now_dt": datetime.fromtimestamp(now, config.IST), "fut": fut, "fut_mid": fut}


def test_registration():
    assert config.validate() == []
    assert set(config.GEN2_BOOKS.values()) == set(gen2.NAMES)
    for n, g in config.GEN2_BOOKS.items():
        p = config.VARIANTS[n]
        assert p["gen"] == g and not p.get("council") and not p.get("conductor")


def test_evaluate_gen_fires_once_per_signal_and_sets_direction():
    g = gen2.Gen2()
    b = paper.Book("n02_relax", config.VARIANTS["n02_relax"], "2026-11-09")
    assert paper.evaluate_gen(b, _ctx(g, T0, 25000.0)) == (False, "no setup")
    g._emit("n02_relax", T0, -1, "test", 6.0, 5.0, 180, i_sign=1, i_peak=7.0)
    fire, _why = paper.evaluate_gen(b, _ctx(g, T0 + 0.4, 25000.0))
    assert fire and b.ctl["dir"] == -1 and b.ctl["ep_type"] == "G2-N02-RELAX"
    assert b.ctl["fire_id"] == -(paper.GEN_ID0 + int(T0))
    b.fired_episodes.add(b.ctl["fire_id"])
    assert paper.evaluate_gen(b, _ctx(g, T0 + 0.8, 25000.0))[0] is False          # already traded
    late = paper.Book("x", config.VARIANTS["n02_relax"], "2026-11-09")
    assert paper.evaluate_gen(late, _ctx(g, T0 + 2.0, 25000.0))[0] is False       # a signal lives for its second only


@pytest.mark.parametrize("fut,held,want", [(24993.5, 10, "TARGET"), (25005.5, 10, "STOP"), (25004.7, 10, "THESIS"),
                                           (24999.0, 200, "HOLD-LIMIT"), (24999.0, 10, None)])
def test_gen_exit_bracket_thesis_stop_and_clock(fut, held, want):
    g = gen2.Gen2()
    g._emit("n01_rev", T0, -1, "test", 6.0, 5.0, 180, stop_px=25004.6)
    b = paper.Book("n01_absorb", config.VARIANTS["n01_absorb"], "2026-11-09")
    pos = {"dir": -1, "fut_in": 25000.0, "t_in": T0 + 1, "episode": -(paper.GEN_ID0 + int(T0))}
    r = paper._gen_exit(b, _ctx(g, T0 + 1 + held, fut), pos, fut)
    assert (r or "").split(" ")[0] == (want or "") and pos["gx"]["tp"] == 6.0


def test_gen_exit_after_a_restart_uses_the_book_bracket():
    b = paper.Book("n06_lead", config.VARIANTS["n06_lead"], "2026-11-09")
    pos = {"dir": 1, "fut_in": 25000.0, "t_in": T0, "episode": -(paper.GEN_ID0 + 5)}
    assert paper._gen_exit(b, _ctx(gen2.Gen2(), T0 + 5, 25012.0), pos, 25012.0) == "TARGET"
    assert pos["gx"] == {"tp": 12.0, "sl": 10.0, "hold": 300}


# ── 10 Nov (docs/38 O4): model exits wait for the model; the bracket is on the position from the fill ───────────────
def test_model_exit_is_silent_until_the_mechanism_is_ready_exact_boundary():
    tp = Tape()
    for _ in range(300):                                  # a restart: 300 s of data, coefficients already back
        tp.step(dq=tp.r.uniform(0, 100), sign=tp.r.choice((-1, 1)))
    for _ in range(12):
        tp.step(dq=600.0, sign=1)
    gx = {"i_sign": 1, "i_peak": 0.01}
    assert tp.g.a is not None and tp.g.impact() > 0.012 and tp.g.clean_s < gen2.WARM_S
    assert not tp.g.ready("n02_relax") and tp.g.void("n02_relax", gx, -1) is None      # was REBUILD before 10 Nov
    while tp.g.clean_s < gen2.WARM_S - 1:
        tp.step(dq=600.0, sign=1)
    assert tp.g.void("n02_relax", gx, -1) is None                                       # one second short
    tp.step(dq=600.0, sign=1)
    assert tp.g.clean_s == gen2.WARM_S and tp.g.ready("n02_relax")
    assert (tp.g.void("n02_relax", gx, -1) or "").startswith("REBUILD")
    tp.step(ok=False)                                     # a data gap: the windows restart, the model is silent again
    tp.step(dq=600.0, sign=1); tp.step(dq=600.0, sign=1)
    assert not tp.g.ready("n02_relax") and tp.g.void("n02_relax", gx, -1) is None


def test_fragment_exit_is_silent_on_a_cold_model_and_without_fresh_cover_of_the_leader():
    hw = [1000.0, 1000.0, 1000.0, 1000.0]
    tp = Tape(hw=hw)
    for _ in range(90):                                   # cold: 90 s, the banks falling all the way
        hw = [hw[0] * 0.99998, hw[1] * 0.99998, hw[2], hw[3]]
        tp.step(dq=1.0, hw=hw)
    gx = {"lead": "bank"}
    assert tp.g.group_ret("bank", 60) < -gen2.P["n06_frag_pct"]
    assert not tp.g.ready("n06_lead") and tp.g.void("n06_lead", gx, 1) is None          # was FRAGMENT before 10 Nov
    for _ in range(520):
        hw = [hw[0] * 0.99998, hw[1] * 0.99998, hw[2], hw[3]]
        tp.step(dq=tp.r.uniform(0, 100), sign=tp.r.choice((-1, 1)), hw=hw)
    assert tp.g.ready("n06_lead") and (tp.g.void("n06_lead", gx, 1) or "").startswith("FRAGMENT")
    for _ in range(3):                                    # one of the two bank stocks goes stale: 50 % cover of the leader
        hw = [hw[0] * 0.99998, hw[1] * 0.99998, hw[2], hw[3]]
        tp.step(dq=1.0, hw=hw, hw_age=[0.2, 9.0, 0.2, 0.2])
    assert tp.g.hw_fresh == 0.75 and tp.g.group_ret("bank", 60) is not None
    assert tp.g.void("n06_lead", gx, 1) is None
    assert tp.g.why["n06_lead"] == "heavyweight coverage 75%" and tp.g.e6 is None


def test_a_stale_stock_is_invalid_at_the_old_end_of_the_window_too():
    hw = [1000.0, 1000.0, 1000.0, 1000.0]
    tp = Tape(hw=hw)
    tp.warm(700)
    tp.step(dq=1.0, hw_age=[0.1, 0.1, 30.0, float("inf")])
    assert tp.g._hw_ret(30)[2:] == [None, None]
    for _ in range(29):
        tp.step(dq=1.0)
    assert tp.g._hw_ret(29)[2:] == [None, None]           # fresh now, stale 29 s ago: still no return over that window
    assert tp.g._hw_ret(28)[2] is not None


def test_stale_future_quote_is_a_gap_whatever_the_feed_says():
    tp = Tape()
    tp.warm()
    tp.step(dq=10.0, sign=1, q_age=0.4)
    assert tp.g.gaps == 0 and len(tp.g.t) > 100
    tp.step(dq=10.0, sign=1, q_age=gen2.Q_FRESH_S + 0.5)
    assert tp.g.gaps == 1 and len(tp.g.t) == 0 and not tp.g.warm
    assert tp.g.why["n01_rev"] == "data gap: windows restarted"


def test_depth_fallback_is_tagged_and_never_read_as_a_release():
    tp = Tape()
    tp.warm()
    for _ in range(70):
        tp.step(dq=300.0, sign=1, move=0.0)
    assert tp.g.e1 is not None and tp.g.e1["state"] == "conf"
    d5 = tp.g.depth
    tp.seen.clear()
    tp.step(dq=300.0, sign=1, move=3.0, bd=150.0, ad=150.0, depth_lvl=1)    # depth packets stop: best level only
    assert tp.g.e1 is None and "n01_rel" not in tp.names()                  # before 10 Nov: "absorbing offers gave way"
    assert tp.g.depth == 150.0 and tp.g.depth_by[5] == d5                   # two scales, two means, never blended
    for _ in range(30):
        tp.step(dq=45.0, sign=1, move=0.0, bd=150.0, ad=150.0, depth_lvl=1)
    assert tp.g.e1 is None and "depth scale changed" in tp.g.why["n01_rel"] and not tp.names()
    tp.step(dq=300.0, sign=1, move=0.0)                                     # back on five levels: the old mean returns
    assert tp.g.depth_lvl == 5 and abs(tp.g.depth - d5) < 0.05 * d5


def test_decay_follows_real_elapsed_seconds():
    a, b = Tape(), Tape()
    for tp in (a, b):
        for _ in range(200):
            tp.step(dq=100.0, sign=1, move=0.0)
    for _ in range(4):
        a.step(dq=0.0, sign=0, move=0.0)                  # four quiet seconds, one update each
    b.step(dq=0.0, sign=0, move=0.0, dt=4.0)              # the same four seconds in one update
    assert a.g.z1 > 0 and abs(a.g.z1 - b.g.z1) < 1e-9 * a.g.z1 and abs(a.g.z2 - b.g.z2) < 1e-9 * a.g.z2
    assert abs(a.g.clean_s - b.g.clean_s) < 1e-9


def test_the_bracket_is_on_the_position_at_the_fill_and_survives_a_restart():
    import json
    from tests import test_c11_buyer_edge as c11
    g = gen2.Gen2()
    g._emit("n02_relax", 100.0, 1, "test signal", 7.5, 6.5, 170, i_sign=-1, i_peak=9.0)
    b = paper.Book("n02_relax", config.VARIANTS["n02_relax"], "2026-10-23")
    ctx = c11._ctx(100.4, gen2=g)
    fire, why = paper.evaluate_gen(b, ctx)
    assert fire and why == "test signal"
    pos = paper.open_trade(b, ctx, dict(c11.OPT), why)
    want = {"tp": 7.5, "sl": 6.5, "hold": 170, "stop_px": None, "i_sign": -1, "i_peak": 9.0, "lead": None}
    assert pos is b.pos and pos["gx"] == want             # at the fill, before any exit check has run
    assert (want["tp"], want["sl"], want["hold"]) != (b.p["tp_pts"], b.p["sl_pts"], b.p["max_hold_s"])
    back = paper.Book.from_json(json.loads(json.dumps(b.to_json(), default=str)))
    cold = gen2.Gen2()                                    # the restart: the signal is gone and the model is cold
    assert back.pos["gx"] == want
    fut, t_in = back.pos["fut_in"], back.pos["t_in"]
    assert paper._gen_exit(back, _ctx(cold, t_in + 5, fut + 7.0), back.pos, fut + 7.0) is None
    assert paper._gen_exit(back, _ctx(cold, t_in + 5, fut + 7.6), back.pos, fut + 7.6) == "TARGET"
    assert paper._gen_exit(back, _ctx(cold, t_in + 5, fut - 6.6), back.pos, fut - 6.6) == "STOP"
    assert paper._gen_exit(back, _ctx(cold, t_in + 171, fut), back.pos, fut) == "HOLD-LIMIT"
    other = paper.Book("apex_edge", config.VARIANTS["apex_edge"], "2026-10-23")           # no other book gets the field
    other.ctl.update({"dir": 1, "fire_id": -1, "ep_type": "SPOT-PULLBACK"})
    assert "gx" not in paper.open_trade(other, c11._ctx(100), dict(c11.OPT), "t")


def test_the_real_engine_feeds_gen2_and_steps_the_new_books_without_a_fault():
    """The engine rig: the signal engine is fed once a second from the snapshot, every new book is evaluated on every
    step, a signal reaches the book as an entry request, and nothing faults. 10 Nov: the feed also passes each
    input's own age and the depth tag (the rig has no depth packets: best level, tagged 1)."""
    from tests import test_wp2
    rig = test_wp2.Rig("gen2", "2026-10-21")
    try:
        rig.warm()
        rig.step(25215.0, 60)
        eng = rig.eng
        g = eng.ctx["gen2"]
        assert g is eng.gen2 and g.last_sec is not None and len(g.t) >= 4 and g.gaps == 0
        assert g.depth_lvl == 1 and g.view()["ready"] == {"n02_relax": False, "n06_lead": False}
        assert not [k for k in eng._err_t if "gen2" in k or k.split(" ")[-1] in config.GEN2_BOOKS], eng._err_t
        for n in config.GEN2_BOOKS:
            assert n in eng.books and eng.books[n].pos is None
        b = eng.books["n06_lead"]
        g._emit("n06_lead", eng.ctx["now_s"], 1, "test signal", 20.0, 10.0, 600, lead="bank")
        fire, why = paper.evaluate_entry(b, eng.ctx, [])
        assert fire and why == "test signal" and b.ctl["dir"] == 1
        r = rig.t.rows                                    # the future's own quote stops while the feed stays alive
        n0 = g.gaps
        for _ in range(60):
            rig.now += 0.1
            keep = int(r["recv_ns"][rig.fut])
            rig.write(25215.0)
            r["recv_ns"][rig.fut] = keep
            eng.step()
        assert g.gaps > n0 and len(g.t) == 0
    finally:
        rig.close()


# ── 10 Nov (docs/38 O6): the N01 corrections, the independent control, the N02 diagnostics ─────────────────────────────
def test_o6_response_is_fitted_on_the_pressure_window_and_an_episode_keeps_its_own_coefficient():
    tp = Tape()
    tp.warm()
    assert gen2.VERSION == 3 and tp.g.beta60 == pytest.approx(20.0, rel=0.05)
    for _ in range(70):
        tp.step(dq=300.0, sign=1, move=0.0)
    # seventy absorbed seconds drag the running 60-s fit down (to "no response"); the open episode is not re-priced
    assert tp.g.beta60 is None or tp.g.beta60 < 5.0
    assert tp.g.e1["state"] == "conf" and tp.g.e1["beta"] == pytest.approx(20.0, rel=0.05)


def test_o6_a_large_move_against_the_pressure_is_not_absorption():
    tp = Tape()
    tp.warm()
    tp.seen.clear()
    for _ in range(40):                                   # heavy buying while the price FALLS 40 points
        tp.step(dq=40.0, sign=1, move=-1.0)
        assert tp.g.e1 is None or tp.g.e1["t0"] <= T0 + 1000 + 12   # a candidate can form only before the fall is large
    assert tp.g.e1 is None or tp.g.e1["state"] == "cand"  # and it is never confirmed
    assert "n01_rev" not in tp.names() and "n01_rel" not in tp.names()


def test_o6_pressure_of_the_other_sign_ends_the_candidate():
    tp = Tape()
    tp.warm()
    for _ in range(19):
        tp.step(dq=100.0, sign=1, move=0.0)
    assert tp.g.e1 and tp.g.e1["state"] == "cand" and tp.g.e1["side"] == 1
    for _ in range(70):                                   # the buying turns into equally heavy selling
        tp.step(dq=40.0, sign=-1, move=0.0)
        assert not (tp.g.e1 and tp.g.e1["side"] == 1 and tp.g.e1["state"] == "conf")
    assert tp.g.e1 is None or tp.g.e1["side"] == -1


def test_o6_the_independent_price_control_needs_no_flow_model():
    tp = Tape()
    tp.warm()
    tp.g.beta60 = None; tp.g.sxx60 = tp.g.sxy60 = 0.0; tp.g.n_fit60 = 0      # no usable response coefficient
    tp.seen.clear()
    for _ in range(10):
        tp.step(move=-1.0)
    for _ in range(4):
        tp.step(move=1.0)
    assert "ctl_price_ind" in tp.names()
    assert "ctl_price" not in tp.names() and "ctl_flow" not in tp.names()   # the matched controls wait for the model
    assert config.GEN2_BOOKS["n01_ctl_price_ind"] == "ctl_price_ind"


def test_o6_n02_diagnostics_are_published_and_no_decision_reads_them():
    tp = Tape()
    tp.warm()
    v = tp.g.view()
    assert v["n02_cond"] >= 1.0 and len(v["n02_se"]) == 2 and all(x >= 0 for x in v["n02_se"]) and len(v["a_raw"]) == 2
    assert v["beta60"] > 0 and v["n_fit60"] >= 300
    import inspect
    src = inspect.getsource(gen2.Gen2._n02) + inspect.getsource(gen2.Gen2.void) + inspect.getsource(gen2.Gen2.ready)
    assert "n02_cond" not in src.replace("cond=self.n02_cond", "") and "n02_se" not in src.replace("se=self.n02_se", "")
