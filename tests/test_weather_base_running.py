"""10 Nov, night (docs/41 section 13): the per-second weather base no longer re-scans the whole day for the day's
range, the median ATM IV and the opening ranges. These tests pin that the running versions give EXACTLY the numbers
the whole-day scans gave, at every second, also when a query goes back in time, and that the cost stays flat."""
import time

import numpy as np

from apex import config
from apex.engine import weather as W


def _open_s(day_t):
    from datetime import datetime
    o = config.mins(config.MARKET_OPEN) * 60
    d0 = datetime.fromtimestamp(day_t, config.IST)
    return d0.replace(hour=o // 3600, minute=(o % 3600) // 60, second=0, microsecond=0).timestamp()


def _feed(n, seed=3, gaps=True):
    from datetime import datetime
    rng = np.random.default_rng(seed)
    t0 = datetime(2026, 11, 9, 9, 15, 3, tzinfo=config.IST).timestamp()
    w = W.Weather(day=None, norms=False)
    px, out = 25000.0, []
    for s in range(n):
        if gaps and 700 <= s < 760:                  # a hole in every series
            continue
        t = t0 + s
        px += rng.normal(0, 0.8)
        w.feed_spot(t, px)
        if not (gaps and s % 37 == 0):               # the IV series has its own holes
            w.feed_misc(t, dict(atm_iv=11 + rng.normal() * 0.3))
        out.append(t)
    return w, out


def _old(w, t):
    """The three whole-day scans exactly as base() had them before this change."""
    from bisect import bisect_right
    ts, ps = w.spot_t, w.spot_p
    open_s = _open_s(ts[0]) if ts else None
    n_sp = bisect_right(ts, t)
    rng_now = (max(ps[:n_sp]) - min(ps[:n_sp])) if n_sp else None
    it, iv = w._s("atm_iv")
    k = bisect_right(it, t)
    med = W._r(float(np.median(iv[:k])), 2) if k >= 60 else None
    return dict(range_now=W._r(rng_now, 2), atm_iv_med=med,
                or15=W.opening_range(ts, ps, t, 15, open_s) if open_s else None,
                or30=W.opening_range(ts, ps, t, 30, open_s) if open_s else None,
                or45=W.opening_range(ts, ps, t, 45, open_s) if open_s else None)


def test_running_values_equal_the_whole_day_scans_every_second():
    """Fed and read second by second, as the engine does."""
    from datetime import datetime
    rng = np.random.default_rng(5)
    t0 = datetime(2026, 11, 9, 9, 15, 3, tzinfo=config.IST).timestamp()
    w = W.Weather(day=None, norms=False)
    px, seen = 25000.0, 0
    for s in range(3300):                            # 55 minutes: past the 45-minute opening range
        if 700 <= s < 760:
            continue
        t = t0 + s
        px += rng.normal(0, 0.8)
        w.feed_spot(t, px)
        if s % 37:
            w.feed_misc(t, dict(atm_iv=11 + rng.normal() * 0.3))
        b = w.base(t + 0.4)
        want = _old(w, t + 0.4)
        for k, v in want.items():
            assert b[k] == v, (s, k, b[k], v)
        seen += b["or45"] is not None
    assert seen > 500 and b["atm_iv_med"] is not None and b["range_now"] > 0


def test_a_query_that_goes_back_in_time_is_still_exact():
    w, ts = _feed(3300)
    for t in (ts[-1], ts[2000], ts[-1], ts[100], ts[950], ts[40], ts[-1] + 5, ts[1800] + 0.5):
        w._base_s = None
        b = w.base(t)
        for k, v in _old(w, t).items():
            assert b[k] == v, (t - ts[0], k, b[k], v)


def test_prefix_median_matches_numpy_on_odd_and_even_counts_and_ties():
    rng = np.random.default_rng(9)
    vals = [float(v) for v in np.round(rng.normal(0, 1, 500), 1)]       # rounded: many ties
    p = W._Prefix(median=True)
    for k in list(range(1, 200)) + [450, 451, 300, 500]:                 # a big jump, then back
        assert p.to(vals, k).median() == float(np.median(vals[:k])), k
    q = W._Prefix()
    for k in (1, 2, 50, 49, 500):
        q.to(vals, k)
        assert (q.hi, q.lo) == (max(vals[:k]), min(vals[:k]))
    other = list(vals)                                                   # another list object: starts again
    assert p.to(other, 3).median() == float(np.median(other[:3]))


def test_the_cost_no_longer_grows_with_the_day():
    w, ts = _feed(20000, gaps=False)

    def cost(parts):
        best = 1e9
        for _ in range(3):
            t0 = time.perf_counter()
            for p in parts:
                p()
            best = min(best, time.perf_counter() - t0)
        return best
    it, iv = w._s("atm_iv")
    n = len(w.spot_p)
    w._px_rng.to(w.spot_p, n); w._iv_med.to(iv, len(iv))
    new = cost([lambda: w._px_rng.to(w.spot_p, n).hi, lambda: w._iv_med.to(iv, len(iv)).median()])
    old = cost([lambda: max(w.spot_p[:n]) - min(w.spot_p[:n]), lambda: float(np.median(iv[:len(iv)]))])
    assert new * 20 < old, (new, old)


def test_book_statistics_are_kept_and_stay_exact():
    """The dashboard's per-book numbers: kept between publishes, recomputed when a trade is added or changed."""
    from apex.engine import paper

    def direct(b):
        pts = [t["pnl_pts"] for t in b.trades]
        wins = [x for x in pts if x > 0]
        return {"name": b.name, "trades": len(pts), "wins": len(wins), "pnl_pts": round(sum(pts), 2),
                "pnl_rs": round(sum(t["pnl_rs"] for t in b.trades), 0), "capital": round(b.capital, 0),
                "win_rate": round(100.0 * len(wins) / len(pts), 1) if pts else None, "open": bool(b.pos)}
    rng = np.random.default_rng(2)
    b = paper.Book("x", {}, "2026-11-10")
    assert b.stats() == direct(b)
    for i in range(60):
        b.trades.append(paper.ClosedTrade(pnl_pts=float(rng.normal()), pnl_rs=float(rng.normal() * 75)))
        b.capital += 10.0
        assert b.stats() == direct(b) and b.stats() == direct(b)
    kept = b._stats
    assert b.stats() and b._stats is kept                       # nothing changed: nothing recomputed
    b.trades[7]["pnl_pts"] = 123.45                              # the Conductor rewrites a closed trade
    assert b.stats() == direct(b) and b._stats is not kept
    b.trades[3].update(pnl_rs=-999.0)
    assert b.stats() == direct(b)
    b.pos = {"entry": 1.0}
    assert b.stats()["open"] is True
    plain = paper.Book("y", {}, "2026-11-10")                    # plain dict trades: computed every time
    plain.trades.append({"pnl_pts": 1.0, "pnl_rs": 75.0})
    assert plain.stats() == direct(plain)
    plain.trades[0]["pnl_pts"] = -2.0
    assert plain.stats() == direct(plain)
