"""12 Nov (PKG-08): the Forecast Lab's one business clock (apex/forecast_lab/clock.py). k = calendar seconds left /
trading seconds left, from config's holiday calendar: exactly 1 on expiry day, about 2.5 the Monday before a Tuesday
expiry, about 5 to 6 midweek. Pure functions, fast."""
import json
import math
from datetime import datetime

import numpy as np

from apex import config, greeks
from apex.forecast_lab import clock as CK
from apex.forecast_lab import core as C


def at(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=config.IST)


def k_of(now, exp):
    k, tau, why = CK.k_ts(now, exp)
    assert why is None, why
    return k


def test_expiry_day_is_exactly_one():
    for hh, mm in ((9, 30), (12, 0), (15, 0), (15, 25)):            # 15:25: both clocks floor at 10 minutes
        assert abs(k_of(at(2026, 11, 17, hh, mm), "2026-11-17") - 1.0) < 1e-9


def test_days_before_expiry():
    assert abs(k_of(at(2026, 11, 16, 10), "2026-11-17") - 2.51) <= 0.02     # Monday before a Tuesday expiry
    assert abs(k_of(at(2026, 11, 16, 12), "2026-11-17") - 2.82) <= 0.02
    assert abs(k_of(at(2026, 11, 11, 12), "2026-11-17") - 5.18) <= 0.02     # Wednesday to the next Tuesday
    assert abs(k_of(at(2026, 11, 13, 10), "2026-11-17") - 5.64) <= 0.02     # Friday to Tuesday


def test_a_weekday_holiday_inside_the_window_is_skipped():
    # Friday 6 Nov 12:00 to Tuesday 17 Nov: 10 Nov 2026 is a holiday, so 6 sessions after today, not 7
    tau, why = CK.tau_left_s(at(2026, 11, 6, 12), "2026-11-17")
    assert why is None and tau == 12600 + 6 * CK.SESSION_S
    # that week's expiry moved to Monday 9 Nov; 24 Nov's to Monday 23 Nov
    tau, why = CK.tau_left_s(at(2026, 11, 6, 12), "2026-11-09")
    assert tau == 12600 + 1 * CK.SESSION_S
    tau, why = CK.tau_left_s(at(2026, 11, 20, 12), "2026-11-23")
    assert tau == 12600 + 1 * CK.SESSION_S
    k, _, why = CK.k_ts(at(2026, 11, 9, 16), "2026-11-10")           # a holiday is never an expiry
    assert k is None and "not a trading day" in why


def test_uncovered_year_and_bad_inputs_give_no_clock():
    k, tau, why = CK.k_ts(at(2026, 12, 30, 12), "2027-01-05")
    assert k is None and tau is None and "2027" in why
    assert CK.k_ts(at(2026, 11, 18, 12), "2026-11-17")[0] is None        # expiry passed
    assert CK.k_ts(at(2026, 11, 17, 15, 45), "2026-11-17")[0] is None    # the expiry session has closed
    assert CK.k_ts(at(2026, 11, 16, 12), "not a date")[0] is None
    assert CK.k_ts(None, "2026-11-17")[0] is None


def test_outside_the_session():
    tau, _ = CK.tau_left_s(at(2026, 11, 16, 8), "2026-11-17")           # before the open: the whole session
    assert tau == 2 * CK.SESSION_S
    tau, _ = CK.tau_left_s(at(2026, 11, 14, 12), "2026-11-17")          # Saturday: no session today
    assert tau == 2 * CK.SESSION_S
    tau, _ = CK.tau_left_s(at(2026, 11, 16, 16), "2026-11-17")          # after the close
    assert tau == CK.SESSION_S


def test_atm_identity():
    """For Black-76 the break-even move from the business-clock theta and Gamma equals the implied move a minute."""
    now, exp = at(2026, 11, 11, 15, 14), "2026-11-17"
    F, iv = 25175.61, 0.1778
    T = greeks.years_to_expiry(exp, now)
    k, tau, _ = CK.k_ts(now, exp, T)
    for K in (F, 25200.0, 25050.0):
        g = C.b76_greeks(F, np.array([K]), T, iv, np.array([True]))
        be = CK.be_per_min(CK.theta_wall(float(g["theta"][0]), k), float(g["gamma"][0]))
        imp = CK.implied_move_per_min(F, iv, T, tau)
        assert abs(be / imp - 1.0) < 0.02
    # the two old numbers for the same thing differed by sqrt(365/252) every day
    g = C.b76_greeks(F, np.array([F]), T, iv, np.array([True]))
    old_be = math.sqrt(2 * abs(float(g["theta"][0]) * C.TRADE_CLOCK) / float(g["gamma"][0]))
    old_imp = math.sqrt((iv * F) ** 2 / C.TRADE_S_YEAR * 60.0)
    assert abs(old_imp / old_be - math.sqrt(365 / 252)) < 1e-3


def test_helpers_handle_missing_values():
    assert CK.be_per_min(None, 1e-3) is None and CK.be_per_min(-0.05, 0.0) is None and CK.be_per_min(0.01, 1e-3) is None
    assert CK.theta_wall(-0.01, None) is None
    assert CK.implied_var_per_trade_s(25000.0, float("nan"), 0.01, 1000.0) is None
    assert CK.implied_move_per_min(25000.0, 0.15, 0.01, None) is None
    assert CK.rent_ratio(None, 1.0) is None and CK.rent_ratio(2.0, 0.0) is None
    assert CK.rent_ratio(2.0, 1.0) == 2.0
    assert CK.label(None) == "unknown" and CK.label(2.514) == "business (k=2.51)"


def test_iv_noise_table_and_increments():
    for b in ("exp", "1-2", "3+"):
        sd = CK.iv_sd_at([300, 900, 1800], b)
        assert np.allclose(sd * 100.0, CK.IV_SD[b])
    assert CK.dte_bucket(0.3) == "exp" and CK.dte_bucket(1.2) == "1-2" and CK.dte_bucket(6.0) == "3+"
    grid = np.array([10.0 * i for i in range(1, 31)] + [600.0, 900.0, 1800.0])
    inc = CK.iv_increments(grid, "3+")
    assert np.all(inc >= 0)
    cum = np.sqrt(np.cumsum(inc ** 2))
    assert np.allclose(cum, CK.iv_sd_at(grid, "3+"))                    # the variance adds up to the table at each h
    assert float(CK.iv_sd_at(3600.0, "3+")) > float(CK.iv_sd_at(1800.0, "3+"))   # extended past 30 minutes


def test_iv_noise_table_file(tmp_path):
    t, f, note = CK.load_iv_sd(str(tmp_path / "missing.json"))
    assert t == {k: tuple(v) for k, v in CK.IV_SD.items()} and note is None and f["1-2"] is False
    p = tmp_path / "reprice.json"
    p.write_text("{not json", encoding="utf-8")
    t, f, note = CK.load_iv_sd(str(p))
    assert t["3+"] == CK.IV_SD["3+"] and "not read" in note
    p.write_text(json.dumps(dict(iv_sd={"1-2": [0.4, 0.6, 0.8], "3+": [0.5, 0.2, 0.1]})), encoding="utf-8")
    t, f, note = CK.load_iv_sd(str(p))
    assert t["1-2"] == (0.4, 0.6, 0.8) and f["1-2"] is True
    assert t["3+"] == CK.IV_SD["3+"] and "3+" in note                    # not increasing: refused, said why


def test_bridge_race_matches_continuous_monitoring():
    """A premium of 220 with noise 0.58 a second and barriers of +-11: the race checked only every 10 s misses touches
    (about 6 points too much 'neither'); the Brownian bridge per 10-s step recovers 1-second monitoring."""
    rng = np.random.default_rng(11)
    n, s0, sig, b = 6000, 220.0, 0.58, 11.0
    X = s0 + np.cumsum(sig * rng.standard_normal((n, 300)), axis=1)
    def first(up, dn):
        fu = np.where(up.any(1), up.argmax(1), 10 ** 6)
        fd = np.where(dn.any(1), dn.argmax(1), 10 ** 6)
        return float((fu == fd).mean())
    ref = first(X >= s0 + b, X <= s0 - b)                                 # 1-second monitoring
    G = X[:, 9::10]
    grid_only = first(G >= s0 + b, G <= s0 - b)
    r = CK.race(G, s0, s0 + b, s0 - b, np.random.default_rng(5))
    assert abs(r["up"] + r["down"] + r["neither"] - 1.0) < 1e-9
    assert grid_only > ref + 0.03
    assert abs(r["neither"] - ref) < 0.03
    assert abs(r["up"] - r["down"]) < 0.04                                # no drift: symmetric
    assert CK.race(np.zeros((5, 0)), 1.0, 2.0, 0.0, rng) == dict(up=0.0, down=0.0, neither=1.0)


def test_held_attribution_closes_and_survives_a_restart():
    """A held call on a Black-76 path with constant IV: direction + convexity + decay + IV + residual = the mid's
    change, the residual is small, and the parts plus the entry and exit spreads add up to bid now minus the entry."""
    exp, K = "2026-11-17", 25200.0
    rng = np.random.default_rng(3)
    t0 = at(2026, 11, 12, 10).timestamp()
    F, iv = 25180.0, 0.15
    now0 = datetime.fromtimestamp(t0, config.IST)
    T0 = greeks.years_to_expiry(exp, now0)
    k, _, _ = CK.k_ts(now0, exp, T0)
    def state(t, F):                                    # the market decays on the business clock
        T = T0 - (t - t0) * k / CK.SPY
        mid = float(C.b76(F, K, T, iv, True))
        g = {n: float(v[0]) for n, v in C.b76_greeks(F, np.array([K]), T, iv, np.array([True])).items()}
        g["theta_wall"] = g["theta"] * k
        return mid, g
    mid, g = state(t0, F)
    a = CK.HeldAttribution("pos1|25200|0", mid + 1.0, t0, F, mid, iv, g)
    for i in range(1, 361):
        t = t0 + 5 * i
        F += 2.0 * rng.standard_normal()
        mid, g = state(t, F)
        a.step(t, F, mid, mid - 0.5, iv, g)
        if i == 180:
            a = CK.HeldAttribution.from_json(json.loads(json.dumps(a.to_json())))   # a restart keeps the sums
    v = a.view(sd_iv=0.003)
    parts = v["parts"]
    move = mid - a.mid0
    inner = sum(parts[k] for k in ("direction", "convexity", "decay", "iv", "residual"))
    assert abs(inner - move) < 0.05
    assert abs(parts["residual"]) < 0.1 * max(abs(move), 1.0) + 0.5
    assert parts["decay"] < 0 and parts["iv"] == 0.0 and parts["before"] == -1.0 and parts["exit_spread"] == -0.5
    assert abs(parts["before"] + inner + parts["exit_spread"] - v["total"]) < 0.06
    assert v["iv_change"] == 0.0 and v["iv_z"] == 0.0 and v["steps"] == 360
    # a gap longer than 30 s books the whole change to the residual
    r0 = a.sums["residual"]
    a.step(a.t + 120, F + 30.0, mid + 15.0, mid + 14.5, iv, g)
    assert abs(a.sums["residual"] - r0 - 15.0) < 1e-9
