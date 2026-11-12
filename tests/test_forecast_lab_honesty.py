"""12 Nov (PKG-03): every sentence the Forecast Lab shows is backed by that horizon's own record against the right
no-skill baseline, and never contradicts the account. Pure functions on the real 11 Nov 15:14 payload
(tests/fixtures/forecast_lab) plus small synthetic Labs. Fast: no option simulation."""
import copy
import json
import os
import time
from datetime import datetime

import numpy as np

from apex import config
from apex.forecast_lab import core as C

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "forecast_lab")
T0 = datetime(2026, 11, 12, 9, 15, 0, tzinfo=config.IST).timestamp()


def _fixture(name="flat"):
    with open(os.path.join(FIX, f"payload_2026-11-11_1514_{name}.json"), encoding="utf-8") as f:
        p = json.load(f)
    p["day"] = "2026-11-11"
    return p


def _text(say):
    return " ".join(x for k in say for x in say[k])


def _good_days(n, skill=True, start=1):
    """n earlier forward days in the days/<day>.json format; skilled days beat every baseline clearly."""
    out = []
    rng = np.random.default_rng(4)
    for i in range(n):
        nn = np.full(len(C.H), 1000.0)
        hit = (0.66 if skill else 0.5) + 0.02 * rng.standard_normal(len(C.H))
        crps = np.full(len(C.H), 0.9 if skill else 1.0)
        on = np.full(len(C.H), 600.0)
        sc = dict(n=nn.tolist(), cov=(0.8 * nn).tolist(), dir_n=nn.tolist(), dir_hit=(hit * nn).tolist(),
                  crps=(crps * nn).tolist(), crps_still=nn.tolist(), on=on.tolist(), on_buy=on.tolist(),
                  obrier_buy=((0.20 if skill else 0.25) * on).tolist(), obrier_clim=(0.245 * on).tolist(),
                  oerr=((4.0 if skill else 4.5) * on).tolist(), oerr_naive=(4.5 * on).tolist())
        out.append(dict(day=f"2026-11-{start + i:02d}", H=list(C.H), forward=True, score=sc))
    return out


def _skilled_buy_row(h=300):
    """Today's option record at h that passes every buy condition."""
    return dict(h=h, n=4000, cov=0.8, err=4.0, err_naive=4.5, err_decay=4.6, slots=2000, n_buy=4000,
                slots_buy=2000, win=0.45, brier_buy=0.20, brier_clim=0.247, n_hi=3000, slots_hi=1500, win_hi=0.68)


def _with_buy_record(p, h=300):
    q = copy.deepcopy(p)
    q["score"]["opt"] = [(_skilled_buy_row(h) if o["h"] == h else o) for o in q["score"]["opt"]]
    return q


def _set_ev(p, ev=2.5, pp=0.61):
    for o in p.get("options") or []:
        for x in o["path"]:
            x["ev"], x["pp"] = ev, pp


# -- the account first --------------------------------------------------------------------------------------------
def test_holding_never_flat_or_buy():
    """The account holds the 25150 CE (11 Nov 15:14) and the option record is made to look perfect: still no 'Flat',
    no buy case, no 'what a buy case needs', and the held line is there."""
    p = _with_buy_record(_fixture("held"))
    _set_ev(p)
    cross = C.cross_day(_good_days(6), p["day"])
    e = C.earned(p, cross=cross)
    assert e["holding"] and not e["buy"] and e["buy_h"] == []
    assert e["buy_detail"]["300"]["record"]                          # the record alone would have passed
    p["earned"] = e
    say = C.commentary(p)
    assert say["do"] and not any(d.startswith("Flat") or d.startswith("Buy case") for d in say["do"])
    assert say["change"] == []
    assert say["do"][0].startswith("Holding the 25150 CE: the account's trade, held by a book (c20_9y).")
    assert "no new buy case is assessed" in say["do"][0]
    assert say["label"] == ["Forecaster's view (display only)"]
    assert not any(s.startswith("Repricing") for s in say["next"])  # no 'bought now' framing while holding
    # an earned dict injected from elsewhere cannot bring a buy case back while holding
    p["earned"] = dict(e, buy=True, buy_h=[300, 900])
    assert not any(d.startswith("Buy case") for d in C.commentary(p)["do"])
    # the account's position alone (no held row yet) also counts as holding
    q = _fixture("flat")
    q["account"] = dict(reason="holding via c20_9y", owner="c20_9y", pos="NIFTY|OPT|2026-11-17|25100|CE")
    q["held"] = dict(strike=25100.0, side="CE", book="c20_9y")
    say = C.commentary(q)
    assert say["do"][0].startswith("Holding the 25100 CE") and say["change"] == []


def _chain_lab():
    lab = C.Lab(n_paths=20, options=False)
    lab.day = "2026-11-12"
    lab.last_t = T0 + 6000
    K = np.array([25100.0, 25150.0, 25200.0])
    lab.chain = dict(exp="2026-11-17", now=datetime(2026, 11, 12, 11, 0, tzinfo=config.IST), K=K,
                     g=dict(delta=np.array([[0.6, -0.4], [0.5, -0.5], [0.4, -0.6]])),
                     mid=np.full((3, 2), 150.0), og=np.zeros((3, 2)), iv=np.full((3, 2), 0.15), k_atm=1)
    return lab


def test_stale_engine_gives_unknown_account_and_no_held_tag():
    lab = _chain_lab()
    pos = dict(key="NIFTY|OPT|2026-11-17|25100|CE", strike=25100.0, rr="CE", expiry="2026-11-17", entry=180.0,
               qty=75, t_in=T0 + 5000, book="c20_9y", rules=dict(sl_px=150.0))
    acc = dict(reason="holding via c20_9y", owner="c20_9y", pos=pos["key"])
    lab.engine = dict(t=time.time(), account=acc, pos=pos, old_rows=[])
    assert any(tag == "held" for _, _, tag in lab._candidates())
    out = {}
    lab._account(out)
    assert out["account"] == acc and out["held"]["strike"] == 25100.0 and out["held"]["entry"] == 180.0
    assert out["held"]["book"] == "c20_9y" and out["held"]["rules"] == dict(sl_px=150.0)
    lab.engine = dict(lab.engine, t=time.time() - 60.0)               # 60 s old by engine time
    assert not any(tag == "held" for _, _, tag in lab._candidates())
    out = {}
    lab._account(out)
    assert "held" not in out and out["account"]["reason"].startswith("account state unknown (engine not read for 6")
    assert not out["account"].get("pos")
    p = _fixture("flat")
    p["account"] = out["account"]
    say = C.commentary(p)
    assert any("account state unknown" in s for s in say["account"]) and not C.is_holding(p)
    # an unknown account may be holding: no buy case on it, even with a record that passes every condition
    assert out["account_known"] is False
    q = _with_buy_record(_fixture("flat"))
    _set_ev(q)
    q.update(account=out["account"], account_known=False)
    e = C.earned(q, cross=C.cross_day(_good_days(6), q["day"]))
    assert e["buy_detail"]["300"]["record"] and not e["buy"] and e["account_unknown"]
    q["earned"] = e
    say = C.commentary(q)
    assert say["do"] == ["The account's state is unknown (the engine report is old), so no buy case is assessed."]
    assert say["change"] == []
    lab.engine = None                                                # offline: no account at all
    out = {}
    lab._account(out)
    assert out["account"] is None and "held" not in out


# -- ranges, per horizon --------------------------------------------------------------------------------------------
def test_range_label_only_where_earned():
    p = _fixture("flat")
    for f in p["score"]["fut"]:
        if f["h"] == 900:
            f["n"], f["cov"] = int(12 * 900 / 5), 0.57                 # 12 independent checks, caught 57 %
    e = C.earned(p)
    r = e["range_h"]["fut"]["900"]
    assert r["status"] == "narrow" and r["checks"] == 12.0 and r["cov"] == 0.57
    assert e["range_h"]["fut"]["300"]["status"] == "ok"                 # 5 min: 76 % on 17 checks
    assert e["range_h"]["fut"]["1800"]["status"] == "unchecked"         # 521 checks over 30 min: 1.4 independent
    p["earned"] = e
    nxt = C.commentary(p)["next"]
    l15 = [s for s in nxt if s.startswith("In 15 min")]
    assert l15 and "(80 %)" not in l15[0] and "unreliable today (caught 57 % on 12 checks" in l15[0]
    l5 = [s for s in nxt if s.startswith("In 5 min")]
    assert l5 and "(80 %)" in l5[0]
    l10 = [s for s in nxt if s.startswith("In 10 min")]
    assert not l10                                                     # 10 min is not one of the stated horizons
    assert not any(s.startswith("In 30 min") for s in nxt)             # 15:14: 30 minutes would pass the close
    q = copy.deepcopy(p)
    for f in q["score"]["fut"]:
        if f["h"] == 300:
            f["n"] = 100                                               # 1.7 independent checks
    q["earned"] = C.earned(q)
    l5 = [s for s in C.commentary(q)["next"] if s.startswith("In 5 min")]
    assert l5 and "(80 %)" not in l5[0] and "not checked enough yet today (2 of 10 checks" in l5[0]
    assert C.earned(dict(score=dict(fut=[dict(h=300, n=1028, cov=0.9)])))["range_h"]["fut"]["300"]["status"] == "wide"
    # option premium ranges are judged on their own record
    q = copy.deepcopy(p)
    for o in q["score"]["opt"]:
        if o["h"] == 300:
            o["cov"] = 0.6
    q["earned"] = C.earned(q)
    assert q["earned"]["range_h"]["opt"]["300"]["status"] == "narrow"
    opt_lines = [s for s in C.commentary(q)["next"] if "CE (bid" in s or "PE (bid" in s]
    assert opt_lines and all("(80 %)" not in s and "unreliable today" in s for s in opt_lines)


# -- direction ------------------------------------------------------------------------------------------------------
def _dir_record(p, h=300):
    for f in p["score"]["fut"]:
        if f["h"] == h:
            f.update(n=3000, dir_n=1500, dir_hit=0.66, skill=0.02)
    return p


def test_flat_lean_never_earned():
    p = _dir_record(_fixture("flat"))
    cross = C.cross_day(_good_days(6), p["day"])
    assert cross["dir"]["300"]["ok"]
    for x in p["path"]:
        x["mu"] = 0.05 * x["sd"]                                         # under LEAN_SD
    e = C.earned(p, cross=cross)
    d = e["dir_h"]["300"]
    assert d["record"] and not d["earned"] and d["lean"] == "flat" and d["why"] == "no clear lean"
    assert not e["direction"]
    p["earned"] = e
    say = C.commentary(p)
    assert "Direction: no clear lean." in say["now"] and "This call is earned" not in _text(say)
    assert "most likely" not in _text(say)
    # the same record with a clear lean is stated
    for x in p["path"]:
        x["mu"] = 0.5 * x["sd"]
    e = C.earned(p, cross=cross)
    assert e["dir_h"]["300"]["earned"] and e["direction"]
    p["earned"] = e
    assert any(s.startswith("Direction over 5 minutes: up") for s in C.commentary(p)["now"])
    # without five forward days it is not earned, and the reason names the count
    e = C.earned(p, cross=C.cross_day(_good_days(3), p["day"]))
    assert not e["direction"] and e["dir_h"]["300"]["why"] == "needs 5 forward days, have 3"
    # nor on five days that show no skill
    assert not C.earned(p, cross=C.cross_day(_good_days(6, skill=False), p["day"]))["direction"]
    assert C.LEAN_SD == 0.15 and e["lean_sd"] == C.LEAN_SD


# -- the buy case ---------------------------------------------------------------------------------------------------
def test_constant_forecaster_never_earns_buy():
    """pp sits at the base rate 0.45 over 400 tickets (one per 15-s slot): calibrated, no resolution, no buy."""
    lab = C.Lab(n_paths=20, options=False)
    sc = lab.score
    rng = np.random.default_rng(11)
    j = C.H.index(300)
    for i in range(400):
        win = 1.0 if rng.random() < 0.45 else 0.0
        lab._win_sums(sc, j, dict(t=T0 + 15 * i, pp=[0.45], tag="buy"), 0, win)
    row = lab._score_view()["opt"][j]
    assert row["slots_buy"] == 400 and row["n_buy"] == 400 and row["n_hi"] == 0
    assert abs(row["brier_buy"] - row["brier_clim"]) < 0.02             # level with its own base rate
    row.update(n=400, cov=0.8, err=4.0, err_naive=4.5, err_decay=4.6)   # even with a good middle error
    p = dict(day="2026-11-12", score=dict(fut=[], opt=[row]))
    e = C.earned(p, cross=C.cross_day(_good_days(6), "2026-11-12"))
    conds = {c["name"]: c["ok"] for c in e["buy_detail"]["300"]["conds"]}
    assert conds["checks"] and conds["days"] and not conds["brier"] and not conds["bucket"]
    assert not e["buy"]
    # the coin baseline alone used to pass a constant forecaster on a skewed base rate (0.30): no longer
    lab2 = C.Lab(n_paths=20, options=False)
    for i in range(400):
        lab2._win_sums(lab2.score, j, dict(t=T0 + 15 * i, pp=[0.30], tag="buy"), 0, 1.0 if rng.random() < 0.30 else 0.0)
    r2 = lab2._score_view()["opt"][j]
    assert r2["brier_buy"] < 0.24 and r2["brier_buy"] > r2["brier_clim"] - C.BUY_MARGIN


def test_buy_tickets_count_per_slot_and_held_tickets_do_not_count():
    lab = C.Lab(n_paths=20, options=False)
    j = C.H.index(300)
    for i in range(10):
        for tag in ("buy", "buy", "held"):                               # call, put and a held contract in one slot
            lab._win_sums(lab.score, j, dict(t=T0 + 15 * i, pp=[0.6], tag=tag), 0, 1.0)
    row = lab._score_view()["opt"][j]
    assert row["slots"] == 10 and row["slots_buy"] == 10 and row["n_buy"] == 20 and row["slots_hi"] == 10
    assert row["win"] == 1.0 and row["win_hi"] == 1.0
    # the first ticket is scored against a coin, later ones against the running base rate (causal)
    assert abs(lab.score["obrier_clim"][j] - 0.25) < 1e-12


def test_buy_requires_five_forward_days():
    p = _with_buy_record(_fixture("flat"))
    _set_ev(p)
    e = C.earned(p, cross=C.cross_day(_good_days(4), p["day"]))
    assert not e["buy"] and e["buy_detail"]["300"]["conds"][-1] == dict(
        name="days", ok=False, have=4, need=5, lb=None, err_share=None)
    p["earned"] = e
    say = C.commentary(p)
    assert say["do"][0] == "Flat. There is no buy case."
    assert any("5 forward days on record (have 4)" in s for s in say["change"])
    assert any("Forward days on record: 4" in s for s in say["doing"])
    e = C.earned(p, cross=C.cross_day(_good_days(5), p["day"]))
    assert e["buy"] and e["buy_h"] == [300]
    p["earned"] = e
    do = C.commentary(p)["do"]
    assert do[0].startswith("Buy case: the ") and "across 5 earlier forward days taken together" in do[0]
    assert "beats its base rate" in do[0]
    # five days without skill do not earn it either
    assert not C.earned(p, cross=C.cross_day(_good_days(6, skill=False), p["day"]))["buy"]
    # a day of today's date or a day marked as fitted on itself never counts
    days = _good_days(4) + [dict(_good_days(1, start=11)[0]), dict(_good_days(1, start=9)[0], forward=False)]
    assert C.cross_day(days, "2026-11-11")["days"] == 4


def test_a_withdrawn_claim_stays_withdrawn_until_the_next_day():
    p = _with_buy_record(_fixture("flat"))
    cross = C.cross_day(_good_days(6), p["day"])
    memo = {}
    assert C.earned(p, cross=cross, memo=memo)["buy"]
    bad = copy.deepcopy(p)
    for o in bad["score"]["opt"]:
        if o["h"] == 300:
            o["brier_buy"] = 0.26
    assert not C.earned(bad, cross=cross, memo=memo)["buy"]
    e = C.earned(p, cross=cross, memo=memo)
    assert not e["buy"] and e["buy_detail"]["300"]["withdrawn"]
    p2 = dict(p, day="2026-11-12")
    assert C.earned(p2, cross=cross, memo=memo)["buy"]                  # a new day starts clean


# -- the display anchor -------------------------------------------------------------------------------------------
def _fut_lab(n=720, drift=0.0):
    lab = C.Lab(n_paths=20, options=False)
    rng = np.random.default_rng(2)
    F = 25000.0
    for i in range(n):
        F += drift + 1.2 * rng.standard_normal()
        lab.step(dict(t=T0 + i, fb=F - 0.5, fa=F + 0.5, fl=F, fv=1000.0 * i, fbq=500.0, faq=500.0))
    return lab


def test_reanchor_up_probability():
    lab = _fut_lab()
    assert lab.fpath is not None
    F_now = float(lab.fm[(lab.n - 1) % C.RING])
    lab.fpath = dict(lab.fpath, F=F_now - 3.0, t=lab.last_t - 3, mu=np.zeros(len(C.H)))
    p = lab.panel()
    assert p["path_F"] == round(F_now - 3.0, 2) and p["day"] == "2026-11-12"
    for x in p["path"]:
        assert abs(x["mean"] - F_now) < 0.02 and abs(x["q50"] - F_now) < 0.02
        assert abs(x["up"] - 0.5) <= 0.05, x
        assert x["q10"] < F_now < x["q90"] and x["draw_median"] is False
    # an expected move up puts 'higher than now' above a half, from the same quantiles that are drawn
    lab.fpath = dict(lab.fpath, mu=np.full(len(C.H), 2.0))
    x1 = lab.panel()["path"][0]
    assert x1["up"] > 0.5 and abs(x1["mean"] - (F_now + 2.0)) < 0.02
    up, txt = C._up_from_quantiles([1, 2, 3, 4, 5], 0.5)
    assert (up, txt) == (0.9, ">90 %") and C._up_from_quantiles([1, 2, 3, 4, 5], 6)[1] == "<10 %"
    assert C._up_from_quantiles([1, 2, 3, 4, 5], 3)[0] == 0.5
    assert json.loads(json.dumps(p, allow_nan=False)) == p


def test_payload_has_no_drivers_and_no_b_old():
    lab = _fut_lab()
    lab.fpath = dict(lab.fpath, drivers=[("r120", 1.0)])
    p = lab.panel()
    assert "drivers" not in p
    assert set(p["score"]["barrier"]) == {"n", "brier"}
    fut = {x["h"]: x for x in p["score"]["fut"]}
    assert fut[60]["lead_lag"] and fut[180]["lead_lag"] and not fut[300]["lead_lag"]
    assert "vol_skill" in fut[300]
    assert p["record_days"] == [] and p["held_view"] is None and p["account"] is None
    # a stale futures quote drops every forecast-derived block with the path
    lab.f_age = 9.0
    q = lab.panel()
    for k in ("path", "path_F", "regime", "volx", "breadth", "experts", "signals"):
        assert k not in q, k


# -- the red team's payload variants (L10 rt2.py) -------------------------------------------------------------------
def test_red_team_variants():
    base = _fixture("flat")
    # V4: earned direction record with a flat lean (above)
    # V6: an earned buy record while a 25450 PE is held
    p = _with_buy_record(base)
    h = copy.deepcopy(p["options"][1])
    h.update(tag="held", strike=25450.0)
    p["options"].append(h)
    _set_ev(p, 1.6, 0.58)
    p["earned"] = C.earned(p, cross=C.cross_day(_good_days(6), p["day"]))
    say = C.commentary(p)
    assert say["do"][0].startswith("Holding the 25450 PE") and not any("Buy case" in d for d in say["do"])
    # V7: None fields everywhere print a dash, never 'None', and never crash
    p = copy.deepcopy(base)
    for o in p["options"]:
        for x in o["path"]:
            for k in ("q10", "q90", "ev", "pp", "be", "decay"):
                x[k] = None
        o["bid"] = o["ask"] = None
    for x in p["path"]:
        x["q10"] = x["q90"] = None
    p["rent"] = dict(be=None, d10=9.1, d30=8.6, ratio=None, ratio30=None)
    for r in p["decay"]:
        r["measured"] = r["lot_hour"] = None
    for o in p["score"]["opt"]:
        o["err"] = o["err_decay"] = None
    say = C.commentary(p)
    text = _text(say)
    assert "None" not in text and "₹0 per lot" not in text and "premiums held up" not in text
    # chain missing: no 'what options price' comparison
    p = copy.deepcopy(base)
    p.pop("chain", None)
    p["volx"] = dict(implied=None, realised10=9.1, realised2=9.0, forecast5=10.4, forecast30=9.5)
    assert not any("Options are priced" in s for s in C.commentary(p)["now"])
    p["volx"]["implied"] = 14.6
    assert any("Options are priced" in s for s in C.commentary(p)["now"])
    # measured decay is labelled for what it is
    p = copy.deepcopy(base)
    dec = " ".join(C.commentary(p)["decay"])
    assert "not explained by the futures (decay + gamma + IV)" in dec and "after taking out" not in dec
    # V8: late in the day there is no 5-minute horizon
    p = copy.deepcopy(base)
    p["path"] = [x for x in p["path"] if x["h"] < 300]
    C.commentary(p)
    # V9: nothing checked yet
    p = copy.deepcopy(base)
    for f in p["score"]["fut"]:
        f.update(n=0, cov=None, dir_n=0, dir_hit=None, skill=None, skill_frozen=None)
    for o in p["score"]["opt"]:
        o["n"] = 0
    e = C.earned(p)
    assert e["ranges"] == "unchecked" and all(r["status"] == "unchecked" for r in e["range_h"]["fut"].values())
    p["earned"] = e
    assert all("(80 %)" not in s for s in C.commentary(p)["next"])
    # V1: stale: nothing but the reason
    p = copy.deepcopy(base)
    p["stale"] = "the futures quote is 7 s old"
    say = C.commentary(p)
    assert say["now"][0].startswith("No forecast") and not say["do"] and not say["next"]
    # the real 15:14 payload: the 10, 15 and 30 minute ranges are not stated as 80 %
    e = C.earned(base)
    assert {k: v["status"] for k, v in e["range_h"]["fut"].items() if k in ("600", "900", "1800")} == \
        {"600": "unchecked", "900": "unchecked", "1800": "unchecked"}
    for s in C.commentary(dict(base, earned=e))["next"]:
        if s.startswith("In 15 min") or s.startswith("In 30 min"):
            assert "(80 %)" not in s
    assert "—" not in _text(C.commentary(base))                          # no em-dashes in the wording


def test_days_files_are_read_and_bad_ones_noted(tmp_path):
    good = _good_days(2)
    for d in good:
        (tmp_path / f"{d['day']}.json").write_text(json.dumps(d), encoding="utf-8")
    (tmp_path / "2026-11-05.json").write_text("{not json", encoding="utf-8")
    notes = []
    rows = C.read_days(str(tmp_path), note=notes.append)
    assert [r["day"] for r in rows] == ["2026-11-01", "2026-11-02"] and notes and "2026-11-05.json" in notes[0]
    s = C.day_summary(rows[0])
    assert s["day"] == "2026-11-01" and s["cov5"] == 0.8 and s["forward"]
    assert C.read_days(str(tmp_path / "missing")) == []
    lab = C.Lab(n_paths=20, options=False)
    lab.days_dir, lab.day = str(tmp_path), "2026-11-12"
    d = lab._days()
    assert len(d["summary"]) == 2 and d["cross"]["days"] == 2 and lab._days() is d       # cached
