"""11 Nov (docs/49): the hold and re-entry twins of c20_9y (apex/engine/holdtwin.py, apex/predict/hold.py). Behaviour on
hand-made inputs with hand-made frozen models: features exist only with enough history, decisions come every 15 s, a
missing model or input means no decision (the twin then is its parent), the re-entry buys once per exit window and its
leg has the fixed exit."""
from collections import deque
from datetime import datetime

import numpy as np

from apex import config
from apex.engine import holdtwin as HT
from apex.predict import hold as Hd

T0 = datetime(2026, 11, 12, 11, 0, 0, tzinfo=config.IST).timestamp()


def _ctx(now, bid=110.0, ask=111.0, drift=0.3, iv=12.0):
    fwd = deque(((T0 - 900 + s, 25000.0 + drift * s + 3 * np.sin(s / 7.0)) for s in range(int(now - T0) + 900)), maxlen=1000)
    mids = deque(((T0 - 900 + s, 100.0 + 0.01 * s, None, 100.0 + 0.01 * s, None, None, None, None) for s in range(int(now - T0) + 900)), maxlen=1000)
    o = dict(id=7, key="NIFTY|OPT|2026-11-17|25000|CE", bid=bid, ask=ask, iv=iv, age=0.5, delta=0.6, ltp=bid)
    return {"now_s": now, "now_dt": datetime.fromtimestamp(now, config.IST), "ohist": {"fwd": fwd, 7: mids}, "by_key": {o["key"]: o}}, o


def _model(kind, sign, line):
    feats = Hd.HOLD_FEATS if kind == "hold" else Hd.RE_FEATS
    w = [0.0] + [0.0] * len(feats)
    w[1 + feats.index("m30")] = sign                       # the model reads one input: momentum in the trade's direction
    return Hd.Linear(art=dict(feats=list(feats), med=[0.0] * len(feats), sd=[1.0] * len(feats), w=w, line=line))


def test_features_need_history_and_come_in_the_declared_order():
    ctx, o = _ctx(T0 + 600)
    x = Hd.hold_features(T0 + 600, 100.0, o["bid"], o["ask"], [(h[0], h[3]) for h in ctx["ohist"][7]], 115.0, T0, T0 + 300,
                         list(ctx["ohist"]["fwd"]), 1, 0.12, 6, 7000)
    assert x is not None and len(x) == len(Hd.HOLD_FEATS) and np.all(np.isfinite(x))
    assert abs(x[Hd.HOLD_FEATS.index("gain")] - 0.10) < 1e-9 and abs(x[Hd.HOLD_FEATS.index("dd")] - 0.05) < 1e-9
    assert x[Hd.HOLD_FEATS.index("m300")] > 0                                  # the future rose: momentum with a call
    assert Hd.hold_features(T0, 100.0, 110.0, 111.0, [], 115.0, T0, T0, [(T0, 25000.0)] * 5, 1, 0.12, 6, 7000) is None
    put = Hd.hold_features(T0 + 600, 100.0, 110.0, 111.0, [], 115.0, T0, T0, list(ctx["ohist"]["fwd"]), -1, 0.12, 6, 7000)
    assert put[Hd.HOLD_FEATS.index("m300")] < 0                                # the same rise is against a put


def test_the_hold_twin_sells_only_when_the_model_says_so_and_only_every_15_seconds():
    p = dict(entry=100.0, t_in=T0, peak_t=T0 + 100, rr="CE", expiry="2026-11-17")
    Hd._MODELS["hold"] = _model("hold", -1.0, 0.0)       # momentum WITH the trade -> a negative hold value -> sell
    try:
        ctx, o = _ctx(T0 + 600)
        why = HT.sell_now(ctx, None, p, o, 115.0)
        assert why and why.startswith("HOLD MODEL SELL") and p["hx_checks"] == 1
        ctx2, o2 = _ctx(T0 + 605)
        assert HT.sell_now(ctx2, None, p, o2, 115.0) is None and p["hx_checks"] == 1   # 5 s later: no new decision
        Hd._MODELS["hold"] = _model("hold", +1.0, 0.0)
        ctx3, o3 = _ctx(T0 + 620)
        assert HT.sell_now(ctx3, None, p, o3, 115.0) is None and p["hx_checks"] == 2 and p["hx_last"] > 0
        Hd._MODELS["hold"] = Hd.Linear(art={})            # no model: the twin is its parent
        assert HT.sell_now(_ctx(T0 + 700)[0], None, p, _ctx(T0 + 700)[1], 115.0) is None
    finally:
        Hd._MODELS.pop("hold", None)


def test_the_reentry_twin_buys_once_per_exit_and_its_leg_has_a_fixed_exit():
    class B:
        p = dict(reenter=True)
        ctl = {}
    tr = dict(t_out=T0 + 300, exit=108.0, entry=100.0, peak_bid=112.0, key="NIFTY|OPT|2026-11-17|25000|CE", rr="CE",
              expiry="2026-11-17")
    HT.note_exit(B, tr)
    assert B.ctl["rx_last"]["used"] is False and abs(B.ctl["rx_last"]["gain"] - 0.08) < 1e-9
    HT.note_exit(B, dict(tr, re_leg=True, t_out=T0 + 999))                    # a re-entry leg's own exit is not remembered
    assert B.ctl["rx_last"]["t"] == T0 + 300
    Hd._MODELS["reenter"] = _model("reenter", +1.0, 0.0)
    try:
        ctx, o = _ctx(T0 + 420)
        got, why = HT.want_reentry(ctx, B)
        assert got is o and why.startswith("RE-ENTRY") and B.ctl["rx_last"]["used"]
        assert HT.want_reentry(_ctx(T0 + 480)[0], B) == (None, None)            # once per exit window
        HT.note_exit(B, tr)
        assert HT.want_reentry(_ctx(T0 + 300 + Hd.REENTER_WINDOW_S + 5)[0], B) == (None, None)   # window over
        assert "rx_last" not in B.ctl
    finally:
        Hd._MODELS.pop("reenter", None)
    leg = dict(entry=100.0, t_in=T0)
    c, _ = _ctx(T0 + 60)
    assert HT.leg_exit(c, leg, dict(bid=120.0), False) is None and leg["re_peak"] == 120.0
    assert "8 %" in HT.leg_exit(c, leg, dict(bid=110.0), False)
    assert "15 minutes" in HT.leg_exit(_ctx(T0 + Hd.RE_HOLD_S)[0], dict(entry=100.0, t_in=T0), dict(bid=101.0), False)
    assert "flat" in HT.leg_exit(c, dict(entry=100.0, t_in=T0), dict(bid=101.0), True)


def test_the_twins_are_shadow_books_outside_the_pool():
    assert config.validate() == []
    assert "hx_c20_9y" not in config.VARIANTS                                    # its model never earned an action
    assert Hd.model("reenter").ok and Hd.model("reenter").line == 2.0             # the frozen, installed re-entry model
    for n, k in (("rx_c20_9y", "reenter"),):
        v = config.VARIANTS[n]
        assert v["council"] == "c20_9y" and v["twin"] and v[k] and not n.startswith("c20")
