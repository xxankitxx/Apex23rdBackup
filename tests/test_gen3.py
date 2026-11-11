"""10 Nov (docs/38 section 7, docs/39): the third batch of shadow signals (apex/engine/gen3.py) on synthetic tapes, the
book plumbing in paper.py and the registration. Nothing here says the books make money: these tests pin the
definitions, the freshness rules, causality and the frozen manifest."""
import hashlib
import json

import numpy as np

from apex import config
from apex.engine import gen2, gen3, paper

T0 = 1_794_196_800.0
W = [30.0, 25.0, 25.0, 20.0]


class Tape:
    """Four heavyweights, each with a cash price and a stock future, and the Nifty future."""

    def __init__(self):
        self.g = gen3.Gen3()
        self.t, self.mid = T0, 25000.0
        self.cash = np.array([1000.0, 2000.0, 1500.0, 500.0])
        self.sf = self.cash * 1.002
        self.seen = []

    def step(self, cash=0.0, sf=0.0, idx=0.0, ok=True, dt=1.0, sf_age=0.3, cash_age=0.3, q_age=0.2, n=1):
        """Moves are index points per second: a basket move of x points is every stock moving x / 25000."""
        for _ in range(n):
            self.t += dt
            self.cash = self.cash * (1.0 + np.asarray(cash) / 25000.0)
            self.sf = self.sf * (1.0 + np.asarray(sf) / 25000.0)
            self.mid += idx
            age = lambda a: np.full(4, a) if np.isscalar(a) else np.asarray(a, float)
            self.g.update(self.t, self.mid - 0.5, self.mid + 0.5, q_age, self.cash.copy(), age(cash_age),
                          self.sf - 0.05, self.sf + 0.05, age(sf_age), W, ok=ok)
            for nm, s in self.g.sig.items():
                if s["t"] == self.t:
                    self.seen.append((nm, s))

    def warm(self):
        self.step(n=gen3.WARM_S + 40)
        assert self.g.ready("s01_trans") and not self.seen

    def names(self):
        return [n for n, _ in self.seen]


def test_registration_and_frozen_manifest():
    assert set(config.GEN3_BOOKS.values()) == set(gen3.NAMES) and gen3.VERSION == 1
    for b, sgn in config.GEN3_BOOKS.items():
        v = config.VARIANTS[b]
        assert v["gen"] == sgn and v["no_trade_cap"] and v["expiry_window_exempt"]
    assert not set(gen3.NAMES) & set(config.GEN2_BOOKS.values())          # gen2 stays frozen, no shared name
    pool = json.dumps(getattr(config, "CONDUCTOR_POOL", "")) + json.dumps(getattr(config, "POOL", ""))
    assert not any(b in pool for b in config.GEN3_BOOKS)                   # shadow only
    h = hashlib.sha256(json.dumps(gen3.P, sort_keys=True).encode()).hexdigest()[:12]
    assert h == MANIFEST, f"gen3.P changed ({h}): a new manifest needs a new VERSION and a note in docs/39"


MANIFEST = "6fc9150866a1"            # gen3.P as frozen on 10 Nov 2026 (VERSION 1)


def test_nothing_before_warm_up_and_nothing_on_a_flat_tape():
    tp = Tape()
    tp.step(sf=1.0, n=gen3.WARM_S - 35)             # a big stock-futures move, but the model is not warm
    assert not tp.seen and not tp.g.ready("s01_trans")


def test_transmission_fires_once_with_the_stock_futures_and_needs_cash_to_follow():
    tp = Tape()
    tp.warm()
    tp.step(sf=0.5, cash=0.1, n=40)                 # stock futures +15 pts in 30 s, cash +3, index flat: z = 13.6
    assert tp.names().count("s01_trans") == 1
    s = dict(tp.seen)["s01_trans"]
    assert s["dir"] == 1 and s["tp"] == 12.0 and s["sl"] == 10.0 and s["hold"] == 120
    # the same gap with cash going the other way: no signal
    tp = Tape()
    tp.warm()
    tp.step(sf=0.5, cash=-0.05, n=40)
    assert "s01_trans" not in tp.names() and "not following" in tp.g.why["s01_trans"]
    # downward, mirrored
    tp = Tape()
    tp.warm()
    tp.step(sf=-0.5, cash=-0.1, n=40)
    assert dict(tp.seen)["s01_trans"]["dir"] == -1


def test_no_transmission_when_the_index_already_moved_or_the_move_is_explained():
    tp = Tape()
    tp.warm()
    tp.step(cash=0.1, idx=0.5, n=22)                # the index moves first: +11 pts
    tp.step(sf=3.0, cash=0.1, idx=0.5, n=6)         # then the stock futures: z about 10, but the index already moved
    assert "s01_trans" not in tp.names() and "already moved" in tp.g.why["s01_trans"]
    tp = Tape()
    tp.warm()
    tp.step(sf=0.3, cash=0.3, idx=0.3, n=40)        # everything moved together: z = 9 * (1 - 0.4554 - 0.4359) = 1
    assert "s01_trans" not in tp.names()


def test_controls_fire_on_their_own_size_only():
    tp = Tape()
    tp.warm()
    tp.step(cash=0.8, sf=0.8, idx=0.8, n=40)        # 24 pts each in 30 s
    assert "s01_ctl_cash" in tp.names() and "s01_ctl_sfut" in tp.names() and "s01_trans" not in tp.names()
    assert tp.names().count("s01_ctl_cash") == 1    # once until it re-arms


def test_stale_stock_futures_or_a_gap_silence_the_model():
    tp = Tape()
    tp.warm()
    tp.step(sf=0.5, cash=0.1, n=40, sf_age=[0.3, 9.0, 9.0, 0.3])     # half the weight has a stale future
    assert not tp.seen and "heavyweight weight" in tp.g.why["s01_trans"] and not tp.g.ready("s01_trans")
    tp = Tape()
    tp.warm()
    tp.step(n=10)
    tp.step(ok=False)                               # blackout: windows restart
    t_gap = tp.t
    tp.step(sf=0.5, cash=0.1, n=60)
    assert not [x for x in tp.seen if x[1]["t"] > t_gap] and tp.g.gaps == 1 and not tp.g.ready("s01_trans")
    tp = Tape()
    tp.warm()
    tp.step(sf=0.5, cash=0.1, n=40, q_age=8.0)      # the Nifty future's own quote is stale
    assert not tp.seen
    assert tp.g.h == type(tp.g.h)(maxlen=80) or len(tp.g.h) == 0     # nothing is kept across a stale index quote


def test_breadth_recruitment_needs_joining_weight_futures_agreement_and_a_quiet_index():
    def run(sfv, idx=0.0):
        tp = Tape()
        tp.warm()
        tp.step(cash=[-0.02, -0.02, -0.02, -0.02], sf=[-0.02] * 4, n=35)          # everyone slightly down: b = -1
        up, f = np.array([0.0, 0.0, 0.0, 0.0]), np.array(sfv, float)
        for k in range(4):                           # one more stock turns up every 10 s
            up[k] = 0.1
            tp.step(cash=up - 0.02 * (up == 0), sf=f * up * 10 - 0.02 * (up == 0), idx=idx, n=10)
        return tp
    ups = lambda tp: [s for n, s in tp.seen if n == "s03_recruit" and s["dir"] == 1]
    tp = run([1, 1, 1, 1])
    assert len(ups(tp)) == 1 and ups(tp)[0]["hold"] == 300 and "over 30 s" in ups(tp)[0]["why"]
    assert not ups(run([-1, -1, -1, -1]))                            # the stock futures disagree
    assert not ups(run([1, 1, 1, 1], idx=0.5))                       # the index already moved


def test_thesis_exits():
    tp = Tape()
    tp.warm()
    tp.step(sf=0.5, cash=0.1, n=40)
    assert tp.g.void("s01_trans", {}, 1) is None
    tp.step(sf=-0.6, cash=0.0, n=30)                # the gap reverses
    assert "REVERSAL" in tp.g.void("s01_trans", {}, 1)
    assert tp.g.void("s01_ctl_cash", {}, 1) is None                  # controls have no thesis exit
    tp.step(n=5, sf_age=9.0)                        # coverage lost
    assert "COVERAGE" in tp.g.void("s01_trans", {}, 1)
    tp = Tape()
    tp.warm()
    tp.step(cash=-0.1, sf=-0.1, n=40)
    assert "RECRUITMENT REVERSED" in tp.g.void("s03_recruit", {}, 1) and tp.g.void("s03_recruit", {}, -1) is None


def test_causal_the_past_does_not_change_when_the_future_does():
    rng = np.random.default_rng(5)
    mv = rng.normal(0, 0.25, (400, 3))

    def run(n):
        tp = Tape()
        tp.warm()
        for k in range(n):
            tp.step(cash=mv[k, 0], sf=mv[k, 1] + (0.5 if 100 <= k < 140 else 0.0), idx=mv[k, 2] * 0.3)
        return [(nm, s["t"], s["dir"]) for nm, s in tp.seen]
    a, b = run(400), run(250)
    assert b == [x for x in a if x[1] <= T0 + gen3.WARM_S + 40 + 250] and len(a) >= 1


def test_the_book_reads_gen3_and_carries_the_bracket():
    tp = Tape()
    tp.warm()
    tp.step(sf=0.5, cash=0.1, n=40)
    s = dict(tp.seen)["s01_trans"]

    class B:
        p = config.VARIANTS["s01_transmit"]
        fired_episodes = set()
        ctl = {}
    ctx = {"gen3": tp.g, "gen2": gen2.Gen2(), "now_s": s["t"] + 0.5}
    ok, why = paper.evaluate_gen(B, ctx)
    assert ok and B.ctl["dir"] == 1 and B.ctl["ep_type"] == "G3-S01-TRANS" and "stock futures" in why
    gx = paper.gen_bracket(B, ctx, B.ctl["fire_id"])
    assert gx["tp"] == 12.0 and gx["sl"] == 10.0 and gx["hold"] == 120
    ctx["now_s"] = s["t"] + 2.0                      # a stale signal is not traded
    assert not paper.evaluate_gen(B, ctx)[0]
    ctx["gen3"] = None
    assert paper.evaluate_gen(B, ctx) == (False, "second-generation signals are off")
