"""15 Nov review of apex/fastlab.py (the research simulator): four faults that could make a wrong number.
1. theta in the engine's unit (per trading minute), 2. feed gaps (no entry in a blackout, a sale waits for a live bid,
short look-backs are not read across a gap), 3. the champion's delta-scaled trail on normal days, 4. the all-in day
total beside the plain sum of trade %. Synthetic days only: nothing here reads or writes the recorded set."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config, fastlab as FL, greeks as G  # noqa: E402
from apex.engine import guard  # noqa: E402

N = FL.N


def _day(fwd, vol=0.12, dte0=False, days_left=2.0, gap=None):
    """one strike (25,000), calls and puts priced by Black-76 on the given forward path; `gap` = (a, b): no data."""
    K = np.array([25000.0])
    T = np.maximum(days_left * 86400.0 - np.arange(N), 60.0) / FL.YEAR_S
    opt = np.full((N, 1, 2, 2), np.nan, np.float32)
    for c, call in ((0, True), (1, False)):
        mid = FL.b76(fwd, K[0], T, vol, call)
        opt[:, 0, c, 0], opt[:, 0, c, 1] = mid - 0.25, mid + 0.25
    lag = np.zeros(N, np.float32)
    f = fwd.copy()
    if gap:
        a, b = gap
        opt[a:b] = np.nan
        lag[a:b] = np.arange(1, b - a + 1)
        f[a:b] = np.nan
    D = FL.Day(day="2026-11-16", expiry="2026-11-16" if dte0 else "2026-11-18", dte0=dte0, t_open=0, K=K, fwd=f,
               fmid=f.copy(), opt=opt, lag=lag, T=T)
    D["fs"] = FL.ema(D["fwd"], 5.0)
    D["P"] = FL.EXP if dte0 else FL.NORM
    D["black"] = FL.blackout(lag)
    return D


def test_theta_is_the_engines_unit_and_the_gap_constants_are_the_engines():
    F, K, T, s = 25010.0, np.array([25000.0, 25100.0]), 2.0 / 365.0, 0.12
    for call in (True, False):
        mine = FL.greeks(F, K, T, s, call)[2]
        eng = G.greeks(F, K, T, np.full(2, s), np.full(2, call))["theta_min"]
        assert np.allclose(mine, eng, rtol=1e-9), (mine, eng)          # it was 3.84 times smaller (calendar minutes)
    assert abs(FL.TRADING_MIN_YEAR * 3.84 - FL.YEAR_S / 60.0) < 1e-6
    assert FL.GAP_S == guard.FUT_QUIET_S and FL.RESUME_S == guard.RESUME_S and FL.FILL_MAX_S == config.ENTRY_FILL_MAX_S
    assert FL.T_FLAT_EXP == 345 * 60 and FL.T_FLAT == 365 * 60          # 15:00 on expiry days, 15:20 otherwise


def test_blackout_covers_the_gap_and_the_resume_time_after_it():
    lag = np.zeros(400)
    lag[100:160] = np.arange(1, 61)                                     # 60 s with no data
    b = FL.blackout(lag)
    assert not b[:110].any()                                            # silent for 10 s or less: not a gap yet
    assert b[110:160].all() and b[160:180].all() and not b[180:].any()  # the gap, then 20 s to resume
    assert not FL.blackout(np.full(50, 5.0)).any()


def test_no_entry_in_a_blackout_and_a_sale_waits_for_a_live_bid():
    fwd = np.full(N, 25040.0)                                           # the 25,000 call has |delta| about 0.57
    D = _day(fwd, gap=(5000, 5600))                                     # ten minutes with no data
    assert FL.run(D, [(5300, "CE", "in the gap")]) == []                # as the live engine: no buy in a blackout
    assert FL.run(D, [(5610, "CE", "resuming")]) == [] and len(FL.run(D, [(5630, "CE", "clear")])) == 1
    P = dict(FL.NORM, hold=900)                                         # the clock runs out inside the gap
    t = FL.exit_ladder(D, 4500, "CE", 0, P)
    assert t["why"] == "TIME" and t["i_in"] == 4501
    assert t["i_out"] == 5600 and t["wait_s"] == 5600 - 5402 and not t["stale_exit"]   # the first live bid after the gap
    assert t["blind_s"] == 5401 - 5000 + 1                              # seconds held on a carried price
    clean = FL.exit_ladder(_day(fwd), 4500, "CE", 0, P)
    assert clean["i_out"] == 5402 and clean["wait_s"] == 0 and clean["blind_s"] == 0 and clean["hold_s"] == 901


def test_the_trail_tightens_with_delta_on_normal_days_only():
    fwd = np.full(N, 25010.0)
    fwd[1000:1700] = 25010.0 + 140.0 * np.arange(700) / 700.0            # up 140 points: the call goes deep in the money
    fwd[1700:] = 25150.0
    fwd[2000:2350] = 25150.0 - 36.0 * np.arange(350) / 350.0             # then back 36 points and no further
    fwd[2350:] = 25114.0
    base = dict(FL.NORM, floor="none")                                   # the trail alone
    D = _day(fwd)
    ad = FL.delta_of(D, 0, 0)
    assert 0.5 < ad[901] < 0.56 and ad[1900] > 0.7                       # delta at entry, delta at the top
    t = FL.exit_ladder(D, 900, "CE", 0, base)
    assert t["why"] == "TRAIL", t                                        # 40 x 0.8 = 32 points given back
    give = float(np.nanmax(D["fs"][901:t["i_out"]]) - D["fs"][t["i_out"] - 1])
    assert 32.0 <= give < 34.0, give
    assert FL.exit_ladder(D, 900, "CE", 0, dict(base, dtr=None))["why"] != "TRAIL"     # the plain 40-point trail holds
    X = _day(fwd, dte0=True, days_left=0.3)
    assert FL.exit_ladder(X, 900, "CE", 0, dict(base, hold=5400, trail=40.0))["why"] != "TRAIL"   # never on expiry days


def test_stats_gives_the_all_in_day_total_beside_the_sum_of_trades():
    tr = [dict(day="a", ret=50.0), dict(day="a", ret=-50.0), dict(day="b", ret=10.0), dict(day="b", ret=10.0)]
    s = FL.stats(tr)
    assert s["n"] == 4 and s["sum"] == 20.0 and s["days"] == 2
    assert abs(s["day_sum"] - (-25.0 + 21.0)) < 1e-9                    # +50 then -50 all-in is -25 %, not 0
    assert FL.day_pct(tr) == {"a": -25.0, "b": 21.000000000000004} or abs(FL.day_pct(tr)["b"] - 21.0) < 1e-9
    e = FL.stats([])
    assert (e["n"], e["sum"], e["day_sum"], e["days"]) == (0, 0.0, 0.0, 0) and np.isnan(e["mean"]) and np.isnan(e["sr"])


def test_a_short_look_back_is_not_read_across_a_gap():
    fwd = np.full(N, 25010.0)
    fwd[5120:] = 24940.0                                                # the market fell 70 points during the outage
    D = _day(fwd, gap=(5000, 5120))                                     # two minutes with no data
    D["fvol"] = np.arange(N, dtype=float)
    D["fbq"] = D["faq"] = np.full(N, 500.0)
    D["hw"] = np.full((N, 2), 100.0, np.float32)
    D["sf"] = np.full((N, 2), 100.0, np.float32)
    D["w"] = np.array([1.0, 1.0])
    D["g"] = np.array(["bank", "it"])
    D["sis"] = np.full((N, 4), 100.0, np.float32)
    X = FL.features(D)
    assert np.isnan(X["mom60"][5125]) and np.isnan(X["nf60"][5125])     # it read about -69 points "in 60 seconds"
    assert np.isfinite(X["mom60"][5200]) and abs(X["mom60"][5200]) < 1.0   # a minute after the data is back: a reading
    assert np.isfinite(X["mom1200"][5125]) and X["mom1200"][5125] < -40    # two minutes are small in a 20-minute window
    assert X["black"][5125] == 1.0 and X["black"][5141] == 0.0 and X["since_gap"][5130] == 11.0
    assert X["gap"][5050] == 1.0 and X["since_gap"][4000] > 4000
