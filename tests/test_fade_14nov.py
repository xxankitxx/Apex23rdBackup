"""14 Nov night (docs/58): the fade shadow books (buy against a stretched move), their day sigma from the prior closes,
and the shadow Conductor that pools them. All shadow: the live Conductor and its pool are untouched."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import config  # noqa: E402
from apex.engine import conductor as cond  # noqa: E402
from apex.engine.council import LiveDay, fade, fade20, fade60, fade60x, orbfade  # noqa: E402

NEW = ["fade20", "fade60", "conductor_fd"]


def _levels(tmp_path, n=21):
    L = {}
    for k in range(n):
        L[f"2026-10-{k + 1:02d}"] = {"close": 25000.0 if k % 2 == 0 else 25250.0, "hi": 25300.0, "lo": 24950.0}
    p = tmp_path / "day_levels.json"
    p.write_text(json.dumps(L), encoding="utf-8")
    return str(p)


def test_day_sigma_needs_ten_returns_and_reads_only_earlier_days(tmp_path):
    p = _levels(tmp_path)
    s = fade.day_sigma("2026-11-16", p)
    assert s is not None and abs(s - np.std(np.diff(np.log([25000.0, 25250.0] * 10 + [25000.0])), ddof=1)) < 1e-12
    assert fade.day_sigma("2026-10-05", p) is None                 # only four closes before that day
    assert fade.day_sigma("2026-10-12", p) is not None and fade.day_sigma("2026-10-11", p) is None
    assert fade.day_sigma("2026-11-16", str(tmp_path / "missing.json")) is None


def test_registered_last_and_only_the_shadow_account_pools_them():
    names = list(config.VARIANTS)
    i = names.index(NEW[0])
    assert names[i:i + 3] == NEW and names[names.index("orbfade"):names.index("orbfade") + 3] == ["orbfade", "conductor_fo", "fade60x"] and config.validate() == []
    assert all(config.VARIANTS[n].get("twin") for n in NEW)
    live = cond.Conductor("2026-11-16", names)
    assert not {m["book"] for m in live.members} & set(NEW)
    fd = cond.AdaptiveConductor("2026-11-16", names, "fade", "conductor_fd")
    assert [m["book"] for m in fd.members][-3:] == ["fade20", "fade60", "orbfade"]
    assert [m["book"] for m in fd.members][:-3] == [m["book"] for m in live.members]
    assert fd.admit(fd.members[0], {"key": "NIFTY|OPT|2026-11-17|25000|CE"}, None, {}, {"now_s": 0.0}) is None
    d1 = cond.AdaptiveConductor("2026-11-16", names, "prexp", "conductor_d1")
    assert not {m["book"] for m in d1.members} & {"fade20", "fade60"}
    assert fade20.Strategy.W_MIN == 20 and fade20.Strategy.Z == 0.6 and fade60.Strategy.W_MIN == 60 and fade60.Strategy.Z == 0.7


def _day(day, exp, move, n=3600):
    D = LiveDay(day, exp)
    D.K = np.array([25000.0, 25000.0, 24950.0, 25050.0, 25200.0, 24800.0])
    D.rr = np.array(["CE", "PE", "CE", "PE", "PE", "CE"])
    D.col = {(25000, "CE"): 0, (25000, "PE"): 1, (24950, "CE"): 2, (25050, "PE"): 3, (25200, "PE"): 4, (24800, "CE"): 5}
    f = np.full(n, 25010.0)
    f[1500:2100] = 25010.0 + move * np.arange(600) / 600.0
    f[2100:] = 25010.0 + move
    D.fwd[:n] = f
    for j, (b, dl) in enumerate(((120.0, 0.53), (125.0, -0.53), (150.0, 0.62), (155.0, -0.60), (160.0, -0.56), (160.0, 0.56))):
        D.bid[:n, j], D.ask[:n, j], D.age[:n, j] = b, b + 0.5, 0.5
        D.delta[:n, j], D.gamma[:n, j], D.theta[:n, j], D.iv[:n, j] = dl, 0.001, -0.05, 12.0
    return D


def _buys(D, cls, upto):
    s = cls()
    out = []
    for i in range(upto):
        D.i = i
        a = s.on_second(i, D, None)
        if a and a[0] == "BUY":
            out.append((i, a))
    return s, out


def test_fade_buys_against_the_stretch_at_a_minute_close_on_normal_days_only(tmp_path):
    p = _levels(tmp_path)

    class F(fade.Fade20):
        LEVELS = p

    s, out = _buys(_day("2026-11-16", "2026-11-17", +200.0), F, 2400)       # up 200 pts in 10 minutes: buy a PUT
    line = 0.6 * 25010.0 * fade.day_sigma("2026-11-16", p)
    assert 140 < line < 170 and abs(s.fd_em - 25010.0 * fade.day_sigma("2026-11-16", p)) < 1e-6
    assert len(out) == 1 and out[0][1][2] == "PE" and out[0][0] % 60 == 59 and "FADE +" in out[0][1][3], out
    i = out[0][0]
    assert 25010.0 + 200.0 * (i - 60 - 1500) / 600.0 < 25010.0 + line + 25                # the first minute close past the line
    s, out = _buys(_day("2026-11-16", "2026-11-17", -200.0), F, 2400)       # down: buy a CALL
    assert len(out) == 1 and out[0][1][2] == "CE"
    s, out = _buys(_day("2026-11-16", "2026-11-17", +100.0), F, 2400)       # under the line: nothing
    assert out == []
    s, out = _buys(_day("2026-11-17", "2026-11-17", +200.0), F, 2400)       # expiry day: the book is off
    assert out == [] and s.fd_dte == 0


def test_without_a_history_of_closes_the_line_comes_from_the_options(tmp_path):
    class F(fade.Fade20):
        LEVELS = str(tmp_path / "none.json")

    D = _day("2026-11-16", "2026-11-17", +200.0)
    s, out = _buys(D, F, 2400)
    want = 25010.0 * 12.0 / 100.0 / fade.IV_OVER_RV / np.sqrt(252.0)
    assert s.fd_rs is None and abs(s.fd_em - want) < 1e-6 and len(out) == 1 and out[0][1][2] == "PE"


def test_one_signal_per_side_per_window(tmp_path):
    p = _levels(tmp_path)

    class F(fade.Fade20):
        LEVELS = p

    D = _day("2026-11-16", "2026-11-17", +400.0, n=5000)           # the stretch stays over the line for many minutes
    s, out = _buys(D, F, 3000)
    rows = [i for i, _ in out]
    assert len(rows) >= 1 and all(b - a >= 1200 for a, b in zip(rows, rows[1:])), rows
    assert [r[0] for r in s.fd_log] == rows


def test_fade_only_account_pools_the_two_fades_and_nothing_else():
    names = list(config.VARIANTS)
    fo = cond.AdaptiveConductor("2026-11-16", names, "fadeonly", "conductor_fo")
    assert [m["book"] for m in fo.members] == ["fade20", "fade60"] and fo.reason == "flat: no eligible trigger"
    assert fo.admit(fo.members[0], {"key": "NIFTY|OPT|2026-11-17|25000|PE"}, None, {}, {"now_s": 0.0}) is None
    assert cond.offline_admit("fadeonly")(0.0, None, {}, [], {}) is None
    live = cond.Conductor("2026-11-16", names)
    assert "orbfade" not in [m["book"] for m in live.members] + [m["book"] for m in fo.members]      # only conductor_fd pools it
    assert config.VARIANTS["orbfade"].get("twin") and config.VARIANTS["conductor_fo"].get("twin")


def _orb_day(day, exp, after, n=4000):
    D = _day(day, exp, 0.0, n=n)
    f = np.full(n, 25010.0)
    f[300:600] = 25030.0                                   # the opening range: 25,010 to 25,030
    f[1500:] = after
    D.fwd[:n] = f
    return D


def test_opening_range_fade_buys_against_the_first_break_once_on_normal_days():
    s, out = _buys(_orb_day("2026-11-16", "2026-11-17", 25080.0), orbfade.Strategy, 3000)       # breaks UP: buy a PUT
    assert len(out) == 1 and out[0][1][2] == "PE" and out[0][0] % 60 == 59 and out[0][0] >= 1500 and "ORB FADE" in out[0][1][3], out
    assert 25028.0 < s.of_hi <= 25030.0 and abs(s.of_lo - 25010.0) < 1e-6 and s.of_done
    s, out = _buys(_orb_day("2026-11-16", "2026-11-17", 24960.0), orbfade.Strategy, 3000)       # breaks DOWN: buy a CALL
    assert len(out) == 1 and out[0][1][2] == "CE"
    s, out = _buys(_orb_day("2026-11-16", "2026-11-17", 25020.0), orbfade.Strategy, 3000)       # stays inside: nothing
    assert out == []
    s, out = _buys(_orb_day("2026-11-17", "2026-11-17", 25080.0), orbfade.Strategy, 3000)       # expiry day: off
    assert out == [] and s.of_dte == 0


def test_sidelock_tape_takes_the_latest_trades_across_books_in_time_order():
    """14 Nov review: the engine tape must agree with offline_admit (latest SIDE_N closed trades by exit time)."""
    class B:
        def __init__(self, trades):
            self.trades = trades
    old_wins = [{"rr": "CE", "pnl_rs": 100.0, "t_out": 1000.0 + k} for k in range(12)]
    new_losses = [{"rr": "CE", "pnl_rs": -100.0, "t_out": 5000.0 + k} for k in range(12)]
    books = {"c20_8x": B(new_losses), "rx_c20_9y": B(old_wins)}
    sl = cond.AdaptiveConductor("2026-11-16", list(config.VARIANTS), "sidelock", "conductor_sl")
    why = sl.admit(sl.members[0], {"key": "NIFTY|OPT|2026-11-17|25000|CE"}, None, books, {"now_s": 9000.0})
    off = cond.offline_admit("sidelock")(9000.0, None, {"rr": "CE"}, [], {k: {"trades": v.trades} for k, v in books.items()})
    assert why is not None and "0 won, 12 lost" in why and off is not None and "0 won, 12 lost" in off


def test_a_bad_expiry_faults_once_not_all_day():
    from apex.engine.council import thr_sis
    for cls in (thr_sis.Strategy, fade20.Strategy, orbfade.Strategy):
        D = _day("2026-11-16", "", 0.0, n=2500)
        s = cls()
        errs = []
        for i in range(3):
            D.i = i
            try:
                s.on_second(i, D, None)
            except Exception as e:
                errs.append(type(e).__name__)
        assert errs and set(errs) == {"ValueError"}, (cls, errs)        # the same clear error each time, never AttributeError


def test_expiry_fade_trades_expiry_days_only(tmp_path):
    p = _levels(tmp_path)

    class X(fade60x.Strategy):
        LEVELS = p

    class N(fade.Fade60):
        LEVELS = p
    up = 400.0
    s, out = _buys(_day("2026-11-17", "2026-11-17", up, n=5000), X, 4900)        # expiry day: fades the rise
    assert len(out) == 1 and out[0][1][2] == "PE" and s.fd_dte == 0 and "in 60 min" in out[0][1][3], out
    s, out = _buys(_day("2026-11-16", "2026-11-17", up, n=5000), X, 4900)        # a normal day: off
    assert out == []
    s, out = _buys(_day("2026-11-17", "2026-11-17", up, n=5000), N, 4900)        # and fade60 stays off on expiry
    assert out == []
    assert config.VARIANTS["fade60x"].get("twin") and "fade60x" not in [m["book"] for m in cond.Conductor("2026-11-17", list(config.VARIANTS)).members]


def test_the_heavy_old_book_is_off_and_nothing_names_it():
    assert "spot_dc12_t12_first_r002" not in config.VARIANTS and "spot_dc12_t12_first_r003" in config.VARIANTS
