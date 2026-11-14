"""The LIVE system replayed over the year: the five pool books' real strategy classes stepped second by second on a
REAL-IV option chain (each contract's price from its real 1-minute IV, its IV, greeks, and real open interest filled
per second), then merged the way the Conductor merges them: first trigger while flat, pool priority on a tie, no
pause, fresh capital every day. Shadow and new books can be stepped the same way.

    py -3.13 s50_live_chain.py check            the recorded sessions: real-IV chain against the tape's quotes
    py -3.13 s50_live_chain.py run [books ...]   every session with minute history; writes hist1s/live_chain_<book>.parquet
"""
import os, sys, glob, importlib
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import arena, lab1s, hist1s
from s44_wxfeat import minute_grid
from s32_real_classes import levels_file
N = FL.N
HALF = 0.0011
POOL = ("c20_9y", "c20_9s", "c20_9v", "c20_9x", "c20_9t")
COUNCIL = {"c20_9y": "c20_9y", "c20_9s": "c20_9s", "c20_9v": "c20_9v", "c20_9x": "c20_9x", "c20_9t": "c20_9t",
           "fade20": "fade20", "fade60": "fade60", "orbfade": "orbfade", "fade60x": "fade60x", "thr_sis": "thr_sis", "thr_hw": "thr_hw"}


def realiv_live(D):
    """a council LiveDay whose chain is real-IV priced where the minute history has the contract, model elsewhere."""
    from apex.engine.council import LiveDay
    L = LiveDay(D["day"], D["expiry"])
    fw = FL._ffill0(D["fwd"])
    lo, hi = np.nanmin(fw), np.nanmax(fw)
    Ks = np.arange(np.floor(lo / 50.0) * 50.0 - 300.0, np.ceil(hi / 50.0) * 50.0 + 350.0, 50.0)
    cols = [(k, c) for k in Ks for c in (0, 1)][:96]
    L.K = np.array([k for k, _ in cols]); L.rr = np.array(["CE" if c == 0 else "PE" for _, c in cols])
    L.fwd[:] = D["fwd"]; L.spot[:] = D["fwd"]; L.fut[:] = D["fwd"]
    wx = arena._wx(D["day"])
    ends = np.minimum(np.arange(375) * 60 + 59, N - 1)
    for q, (k, c) in enumerate(cols):
        call = c == 0
        L.col[(int(k), "CE" if call else "PE")] = q
        px = arena.realiv_series(D, k, "CE" if call else "PE")
        if px is None:
            px = arena.model_series(D, k, "CE" if call else "PE")
            iv = np.full(N, D["iv"])
        else:
            with np.errstate(all="ignore"):
                iv = FL._ffill0(FL.iv_of(fw, float(k), D["T"], px, call))
            iv = np.where(np.isfinite(iv), iv, D["iv"])
        with np.errstate(all="ignore"):
            dl, gm, th = FL.greeks(fw, float(k), D["T"], np.maximum(iv, 0.01), call)
        L.bid[:, q] = px * (1 - HALF); L.ask[:, q] = px * (1 + HALF); L.mid[:, q] = px; L.ltp[:, q] = px
        L.age[:, q] = 0.5; L.iv[:, q] = 100.0 * iv; L.delta[:, q] = dl; L.gamma[:, q] = gm; L.theta[:, q] = th
        if wx is not None:
            oi = minute_grid(wx, f"opt:{int(k)}:{'call' if call else 'put'}", "open_interest")
            if np.isfinite(oi).any():
                L.oi[:, q] = np.interp(np.arange(N), ends, pd.Series(oi).ffill().bfill().to_numpy())
    return L


def play_books(day, books, tape=False):
    from apex.engine.council import c20_8x, fade
    lv = levels_file()
    c20_8x.LEVELS_PATH = lv
    fade._FadeMixin.LEVELS = lv
    if tape:
        F = FL.load_day(day)
        L = FL.live_day(F); D = F
    else:
        D = lab1s.session(day, fwd=FL.load_day(day)["fwd"].copy()) if day in arena.REC else lab1s.session(day)
        if D is None or not arena.has_wx(day):
            return []
        L = realiv_live(D)
    out = []
    for b in books:
        for t in FL.play(D, L, COUNCIL[b]):
            t.update(book=b, dte0=bool(D["dte0"])); out.append(t)
    return out


def conductor(T, order=POOL):
    """the Conductor's merge: first trigger while flat, pool order on a tie, no pause."""
    pri = {b: k for k, b in enumerate(order)}
    T = T[T.book.isin(order)].assign(_p=lambda x: x.book.map(pri)).sort_values(["day", "i_in", "_p"])
    out = []
    for day, d in T.groupby("day"):
        free = -1
        for r in d.itertuples():
            if r.i_in > free:
                out.append(r._asdict()); free = r.i_out
    return pd.DataFrame(out)


def _one(a):
    day, books, tape = a
    try:
        return play_books(day, books, tape)
    except Exception as e:
        return [dict(day=day, error=f"{type(e).__name__}: {e}")]


if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    books = sys.argv[2:] or list(POOL)
    comp = lambda r: 100 * (np.prod(1 + np.asarray(r, float) / 100) - 1)
    if mode == "check":
        days = [d for d in FL.days() if arena.has_wx(d)]
        rows = []
        with ProcessPoolExecutor(max_workers=3) as ex:
            for r in ex.map(_one, [(d, books, True) for d in days]):
                rows += [dict(x, src="tape") for x in r]
            for r in ex.map(_one, [(d, books, False) for d in days]):
                rows += [dict(x, src="realiv chain") for x in r]
        T = pd.DataFrame(rows)
        if "error" in T and T.error.notna().any():
            print(T[T.error.notna()].head())
        for src, g in T.groupby("src"):
            C = conductor(g)
            for d0, gg in C.groupby("dte0"):
                dd = gg.groupby("day").ret.apply(comp)
                print(f"{src:13} {'expiry' if d0 else 'normal'}: Conductor trades {len(gg)}, winners {100 * (gg.ret > 0).mean():.0f} %, per trade {gg.ret.mean():+.2f} %, day sum {dd.sum():+.0f} %")
        a = conductor(T[T.src == "tape"]).groupby("day").ret.apply(comp); b = conductor(T[T.src == "realiv chain"]).groupby("day").ret.apply(comp)
        idx = sorted(set(a.index) | set(b.index))
        print("day-result correlation, Conductor on tape vs on the real-IV chain:", round(np.corrcoef(a.reindex(idx).fillna(0), b.reindex(idx).fillna(0))[0, 1], 3))
        live = {"2026-11-09": 59.7, "2026-11-11": 7.4, "2026-11-12": 3.7, "2026-11-13": -27.1}
        print("live days, actual / tape replay / real-IV chain:", {d: (v, round(a.get(d, 0), 1), round(b.get(d, 0), 1)) for d, v in live.items()})
    else:
        days = [d for d in arena.sessions() if arena.has_wx(d)]
        rows = []
        with ProcessPoolExecutor(max_workers=3) as ex:
            for r in ex.map(_one, [(d, books, False) for d in days]):
                rows += r
        T = pd.DataFrame(rows)
        tag = "pool" if tuple(books) == POOL else ("all" if len(books) > 6 else "_".join(books))
        T.to_parquet(os.path.join(hist1s.OUT, f"live_chain_{tag}.parquet"))
        print("sessions", T.day.nunique(), "trades", len(T), "errors", int(T.get("error", pd.Series(dtype=object)).notna().sum()) if "error" in T else 0)
