import os as _os
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    _os.environ.setdefault(_k, "1")
"""arena: ONE scoring harness for every entry idea (14 Nov 2026, the 30-agent search; docs/60).

Every idea is judged the same way, the way the live account works:
  * buy only, a call or a put at the money or in the money (|delta| >= 0.52 enforced), all-in, one position at a time
    per idea, the idea's own cooldown;
  * a fresh account every day (config.START_CAPITAL), so a day's trades compound and nothing carries;
  * fills: the ask one second after the signal, exits at the bid one second after the decision (half the recorded
    median spread, 0.11 %, each way);
  * every rule may read rows <= i only (the harness only hands the generator what is known by then).

Data per session (14 Nov 2025 to 13 Nov 2026):
  ctx["D"]   the session: D["fwd"] / D["fs"] (the Nifty future minus the day's basis, per second, and its 5-s EMA),
             D["T"] (years to expiry per second), D["dte"] (sessions to expiry, 0 = expiry day), D["dte0"], D["iv"]
             (the day's model IV from the 20-session realised volatility), D["expiry"]
  ctx["X"]   per-second arrays from lab1s.feats_full: mom{60..3600}, hi/lo/rng{300..3600}, er{300,1200,3600}, em15
  ctx["M"]   per-minute CAPTURED-DATA inputs (DataFrame, one row per minute 5..344, column "i" = the decision second
             60*minute+59), or None when that session's broker history is not downloaded: f_* (future), c_* (context),
             hw_* (Nifty-weighted heavyweights, breadth, banks vs rest, lead), sis_* (BANKNIFTY, FINNIFTY futures and
             their lead), o_* (option chain: ATM IV and its changes, skew, OI changes of calls / puts near the money,
             call and put OI walls and distances, put-call OI ratio, option volume pace). No label columns.
  ctx["meta"] prior close / high / low (pc, ph, pl), em (one-sigma day move in points), rv20, gap
  ctx["day"]

A generator is a Python file with   def signals(ctx): return [(i, side, tag), ...]   or 4-tuples
(i, side, tag, exits) where exits overrides the exit ladder for that trade: sl (fraction, e.g. 0.15), trail
(forward points), hold (seconds), floor ("ramp" | "pex" | None), ptrail (bool), tp (fraction or None), dt (target
|delta|, >= 0.52), cool (seconds after the exit before this idea may buy again). Defaults: the champion's ladder
for the day type (fastlab.NORM on normal days, fastlab.EXP on expiry days).

Pricing: REAL-IV on every session with minute history (all of found / judged / window): the broker's real 1-minute
option closes give each contract's implied volatility each minute; the price each second is Black-76 on the
per-second forward with the IV of the last COMPLETED minute (ARENA_IV=zoh; the old "interp" leaned on the current
minute's close, up to 59 s ahead). A contract outside the downloaded strikes is priced on the model option
(price="model_fb") and the account moves on, instead of the signal vanishing. Normal sessions without minute history:
the model option. Expiry sessions without it are skipped.

Coordinates (r2_harness_fix): the forward of a broker-1s session is the future minus the basis known by 09:20
(ARENA_BASIS=first5; the old whole-day median read the rest of the day); meta pc / ph / pl / gap and M c_gap are in
the same spot coordinates (each session net of its own basis).

Pool (r2_harness_fix): pooled_gain is the champion-priority account (see evaluate), with a random null beside it.

    import arena
    R = arena.evaluate("path/to/my_idea.py", name="my idea")      # all splits, pooled with the champion
    arena.report(R)
"""
import os, sys, glob, json, pickle, importlib.util, datetime as dt
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from apex import fastlab as FL
import lab1s, hist1s

N = FL.N
HALF = 0.0011
WX = r"D:\ApexOptions\data\research\hist_wx"
FE = os.path.join(WX, "feat")
HS = hist1s.OUT
REC = set(FL.days())
SPLITS = {"found": ("2026-05-07", "2026-10-16"), "judged": ("2025-11-14", "2026-05-06"), "window": ("2026-10-19", "2026-11-13"),
          "holdout": ("2024-11-14", "2025-11-13")}      # holdout: an untouched year, used only for the final verdict
NORM, EXP = FL.NORM, FL.EXP
_CTX = {}


def _fut_path(day):
    e = _FUTEXP.get(day)
    return os.path.join(HS, f"fut_{e}_x_0_{day}.parquet") if e else ""


_FUTEXP = json.load(open(os.path.join(hist1s.OUT, "fut_expiry.json"))) if os.path.exists(os.path.join(hist1s.OUT, "fut_expiry.json")) else {}


def sessions(split=None):
    have = {os.path.basename(p).split("_")[-1][:10] for p in glob.glob(os.path.join(HS, "fut_*.parquet"))}
    days = sorted(have | REC)
    if split:
        a, b = SPLITS[split]
        days = [d for d in days if a <= d <= b]
    return days


def _minute_feats(day):
    p = os.path.join(FE, f"{day}.parquet")
    if not os.path.exists(p):
        if not os.path.exists(os.path.join(WX, f"{day}.parquet")):
            return None
        try:
            import s44_wxfeat
            s44_wxfeat.one(day)
        except Exception:
            return None
        if not os.path.exists(p):
            return None
    M = pd.read_parquet(p)
    return M[[c for c in M.columns if not c.startswith("y_")]].reset_index(drop=True)


CACHE_N = 4                      # sessions kept in memory (a year of per-second arrays would not fit 30 agents)


def is_expiry(day):
    m = lab1s.meta().get(day)
    return bool(m and m["dte0"])


BASIS = os.environ.get("ARENA_BASIS", "first5")    # FIX (d): "first5" = the basis known by 09:20; "day" = the old median
_BT = {}


def basis_first5():
    """per session: the median futures-spot difference of the first five 1-minute bars (09:15-09:19), known by 09:20."""
    if "T" not in _BT:
        import lab1
        f = lab1._tab("fut")[["day", "ts", "c"]].drop_duplicates(["day", "ts"])
        s = lab1._tab("spot")[["day", "ts", "c"]].drop_duplicates(["day", "ts"])
        x = f.merge(s, on=["day", "ts"], suffixes=("_f", "_s"))
        x = x[x.ts.str[11:16] < "09:20"]
        _BT["T"] = (x.c_f - x.c_s).groupby(x.day).median().to_dict()
    return _BT["T"]


def basis_of(day):
    m = lab1s.meta()[day]
    b = basis_first5().get(day) if BASIS == "first5" else None
    return float(b) if b is not None and np.isfinite(b) else float(m["basis"])


def meta_spot(day):
    """FIX (c): prior close / high / low and the gap in the forward's own (spot) coordinates: every session net of ITS
    basis (the raw values carried the prior session's basis: 47 points on average, up to 179 at the monthly roll)."""
    M = lab1s.meta(); ks = _META_KEYS()
    m = M[day]; j = ks.index(day)
    P = M[ks[j - 1]] if j else None
    out = dict(em=m.get("em"), rv20=m.get("rv20"), open=float(m["o"][0] - basis_of(day)), pc=None, ph=None, pl=None, gap=None)
    if P is not None:
        bp = basis_of(ks[j - 1])
        out.update(pc=float(P["c"][-1] - bp), ph=float(np.max(P["h"]) - bp), pl=float(np.min(P["l"]) - bp))
        out["gap"] = out["open"] - out["pc"]
    return out


_MK = []


def _META_KEYS():
    if not _MK:
        _MK.extend(sorted(lab1s.meta()))
    return _MK


def context(day):
    if day in _CTX:
        return _CTX[day]
    while len(_CTX) >= CACHE_N:
        _CTX.pop(next(iter(_CTX)))
    if day in REC:
        D = lab1s.session(day, fwd=FL.load_day(day)["fwd"].copy())        # the recorded parity forward (causal)
    else:
        D = lab1s.session(day)
        if D is not None and BASIS != "day":                               # FIX (d): future minus the 09:20 basis
            D["fwd"] = D["fwd"] + float(lab1s.meta()[day]["basis"]) - basis_of(day)
            D["fs"] = FL.ema(D["fwd"], 5.0)
    if D is None:
        _CTX[day] = None
        return None
    M = _minute_feats(day)
    if M is not None and "c_gap" in M:                                     # FIX (c): the spot-coordinate gap
        ms = meta_spot(day)
        M = M.assign(c_gap=(ms["gap"] / ms["em"]) if ms["gap"] is not None and ms["em"] else np.nan)
    ctx = dict(day=day, D=D, X=lab1s.feats_full(D), M=M, meta=meta_spot(day))
    _CTX[day] = ctx
    return ctx


# ── pricing ─────────────────────────────────────────────────────────────────────────────────────────────────────────
_WXC = {}
WX2 = "D:/ApexOptions/data/research/hist_wx_mythos"      # the holdout year's real 1-minute option bars (MYTHOS)


def has_wx(day):
    return os.path.exists(os.path.join(WX, f"{day}.parquet")) or os.path.exists(os.path.join(WX2, f"{day}.parquet"))


def _wx(day):
    if day not in _WXC:
        while len(_WXC) >= CACHE_N:
            _WXC.pop(next(iter(_WXC)))
        p = os.path.join(WX, f"{day}.parquet")
        if not os.path.exists(p):
            p = os.path.join(WX2, f"{day}.parquet")
        _WXC[day] = pd.read_parquet(p) if os.path.exists(p) else None
    return _WXC[day]


IV_MODE = os.environ.get("ARENA_IV", "zoh")        # FIX (e): "zoh" = the last COMPLETED minute's IV (causal);
                                                    # "interp" = the old interpolation toward minute m's close (59 s ahead)
IV_PC = os.environ.get("ARENA_IV_PC", "0") == "1"   # the strike's call/put-averaged IV (cancels the stale-close bias)
_GRID = {}


def _grids(day):
    """every option contract's 1-minute close grid in one pass (s44_wxfeat.minute_grid re-parses the day per call)."""
    if day not in _GRID:
        while len(_GRID) >= CACHE_N:
            _GRID.pop(next(iter(_GRID)))
        wx = _wx(day)
        G = None
        if wx is not None:
            w = wx[wx.what.str.startswith("opt:")]
            t = pd.to_datetime(w.datetime)
            m = ((t.dt.hour * 60 + t.dt.minute) - 555).to_numpy()
            ok = (m >= 0) & (m < 375)
            what = w.what.to_numpy(); cl = w.close.to_numpy(float); G = {}
            for key, idx in pd.Series(np.arange(len(w))).groupby(what).indices.items():
                idx = np.sort(idx); idx = idx[ok[idx]]
                out = np.full(375, np.nan); out[m[idx]] = cl[idx]
                G[key] = pd.Series(out).ffill().to_numpy()
        _GRID[day] = G
    return _GRID[day]


def _ivm(D, K, side):
    G = _grids(D["day"])
    key = f"opt:{int(K)}:{'call' if side == 'CE' else 'put'}"
    if G is None or key not in G or not np.isfinite(G[key]).any():
        return None
    fw = FL._ffill0(D["fwd"])
    ends = np.minimum(np.arange(375) * 60 + 59, N - 1)
    with np.errstate(all="ignore"):
        return FL.iv_of(fw[ends], float(K), D["T"][ends], G[key], side == "CE")


def realiv_series(D, K, side, iv_mode=None, pc=None):
    """per-second price of contract (K, side): Black-76 on the per-second future with the contract's REAL implied
    volatility, solved each minute from the broker's 1-minute close. iv_mode "zoh" (default) holds the last completed
    minute's IV (bar m closes at second 60m+59); "interp" is the old interpolation toward the CURRENT minute's close.
    pc: average the strike's call and put IV where both exist. None when the contract has no minute history."""
    iv_mode = iv_mode or IV_MODE; pc = IV_PC if pc is None else pc
    ivm = _ivm(D, K, side)
    if ivm is None:
        return None
    if pc:
        o = _ivm(D, K, "PE" if side == "CE" else "CE")
        if o is not None:
            ok = np.isfinite(ivm) & np.isfinite(o)
            ivm = np.where(ok, 0.5 * (ivm + o), ivm)
    ivm = pd.Series(ivm).ffill().bfill().to_numpy()
    if not np.isfinite(ivm).any():
        return None
    ends = np.minimum(np.arange(375) * 60 + 59, N - 1)
    s = np.arange(N)
    iv = ivm[np.clip((s - 59) // 60, 0, 374)] if iv_mode == "zoh" else np.interp(s, ends, ivm)
    fw = FL._ffill0(D["fwd"])
    with np.errstate(all="ignore"):
        return FL.b76(fw, float(K), D["T"], np.maximum(iv, 0.01), side == "CE")


def model_series(D, K, side):
    with np.errstate(all="ignore"):
        return FL.b76(FL._ffill0(D["fwd"]), float(K), D["T"], D["iv"], side == "CE")


_PM = {}                                           # (memo) one price per (session, forward, contract, pricing)


def _fp(D):
    f = D["fwd"]
    return (D["day"], float(np.nansum(f[::997])), int(np.isfinite(f).sum()))


def price_memo(D, K, side, mode):
    k = (_fp(D), float(K), side, mode, IV_MODE, IV_PC)
    if k not in _PM:
        days = list(dict.fromkeys(x[0][0] for x in _PM))
        if D["day"] not in days and len(days) >= 2:                          # keep two sessions (~180 KB a contract)
            for x in [x for x in _PM if x[0][0] == days[0]]:
                del _PM[x]
        _PM[k] = _price(D, K, side, mode)
    return _PM[k]


def pick_strike(D, i, side, dt):
    F = D["fwd"][i]
    if not np.isfinite(F):
        return None
    call = side == "CE"
    Ks = (np.floor(F / 50.0) * 50.0 + 50.0 * np.arange(-6, 7)).astype(float)
    dl, _, _ = FL.greeks(F, Ks, D["T"][i], D["iv"], call)
    ad = np.abs(dl)
    ok = ad >= 0.52
    if not ok.any():
        return None
    return float(Ks[int(np.argmin(np.where(ok, np.abs(ad - max(dt, 0.52)), 9.0)))])


def _price(D, K, side, mode):
    if mode == "realiv":
        s = realiv_series(D, K, side)
        if s is not None:
            return s, "realiv"
        return None, None
    return model_series(D, K, side), "model"


FALLBACK = os.environ.get("ARENA_FALLBACK", "model")   # FIX (b): a contract outside the downloaded strikes
DROPS = []                                               # every signal that passed 'free' but bought nothing


def _ext_of(ex):
    """the exit hooks of one trade: stall=(after, pk, band) and/or ext=callable(c) -> (name, mask) | list of them.
    c holds D, i, a, side, sg, e, b (bid path), f (signed forward path), g (peak gain), pk, best, L, j, c."""
    fs = []
    if ex.get("stall"):
        import fam
        fs.append(fam.stall(*ex["stall"]))
    h = ex.get("ext")
    if h is not None:
        fs += list(h) if isinstance(h, (list, tuple)) else [h]
    if len(fs) <= 1:
        return fs[0] if fs else None

    def comb(c):
        best = None
        for f in fs:
            r = f(c)
            w = np.flatnonzero(r[1]) if r is not None else []
            if len(w) and (best is None or w[0] < best[0]):
                best = (int(w[0]), r[0])
        if best is None:
            return None
        m = np.zeros(c["L"], bool); m[best[0]] = True
        return (best[1], m)
    return comb


def run_day(ctx, sigs, mode=None, busy=None):
    """one position at a time; returns the trades.
    busy: (ins, outs) of a HIGHER-priority book's trades this session (the champion): this book buys only while that
    book is flat, and a position still open when that book's next trade fills is sold at that second (why=PREEMPT,
    the 'preempt' behaviour; the champion's own trades are then exactly its standalone trades)."""
    D = ctx["D"]
    mode = mode or ("realiv" if has_wx(ctx["day"]) else ("model" if not D["dte0"] else None))
    if mode is None:
        return []
    base = EXP if D["dte0"] else NORM
    out = []; free = base["t0"]; last_exit = -1
    ins, outs = (np.asarray(busy[0], int), np.asarray(busy[1], int)) if busy is not None else (np.array([], int), np.array([], int))
    cache = {}
    for s in sorted(sigs, key=lambda x: x[0]):
        i, side, tag = int(s[0]), s[1], s[2]
        ex = dict(s[3]) if len(s) > 3 and s[3] else {}
        P = dict(base, **{k: v for k, v in ex.items() if k in ("sl", "trail", "hold", "floor", "ptrail", "tp", "dt", "cool")})
        P["dt"] = max(float(P.get("dt", base["dt"])), 0.52)
        if i < free or i < base["t0"] or i > base["t1"] or side not in ("CE", "PE"):
            continue
        if len(ins) and (i + 1 <= last_exit or ((ins <= i + 1) & (i + 1 <= outs)).any()):
            continue                                                      # the higher-priority book holds
        K = pick_strike(D, i, side, P["dt"])
        if K is None:
            DROPS.append(dict(day=ctx["day"], i=i, side=side, K=None, tag=tag, why="no_strike"))
            continue
        key = (K, side)
        if key not in cache:
            px, how = price_memo(D, K, side, mode)
            if px is None and FALLBACK == "model":
                px, how = model_series(D, K, side), "model_fb"
            if px is None:
                cache[key] = None
            else:
                o = np.full((N, 1, 2, 2), np.nan, np.float32)
                c = 0 if side == "CE" else 1
                o[:, 0, c, 0] = px * (1 - HALF); o[:, 0, c, 1] = px * (1 + HALF)
                Dm = FL.Day(dict(D)); Dm["opt"] = o; Dm["K"] = np.array([K])
                cache[key] = (Dm, how)
        if cache[key] is None:
            DROPS.append(dict(day=ctx["day"], i=i, side=side, K=K, tag=tag, why="no_minute_history"))
            continue
        Dm, how = cache[key]
        t = FL.exit_ladder(Dm, i, side, 0, P, _ext_of(ex))
        if t is None:
            DROPS.append(dict(day=ctx["day"], i=i, side=side, K=K, tag=tag, why="no_fill"))
            continue
        nxt = ins[ins > t["i_in"]]
        if len(nxt) and nxt[0] < t["i_out"]:
            so = int(nxt[0]); c = 0 if side == "CE" else 1
            bid = FL._ffill0(Dm["opt"][t["i_in"]:so + 1, 0, c, 0].astype(float))
            xb = float(bid[-1]) if np.isfinite(bid[-1]) else t["e"]
            t.update(i_out=so, x=xb, ret=100.0 * (xb / t["e"] - 1.0), why="PREEMPT", hold_s=so - t["i_in"])
        t.update(day=ctx["day"], tag=tag, dte=D["dte"], price=how, minute=i // 60)
        out.append(t)
        last_exit = t["i_out"]
        free = t["i_out"] + int(P.get("cool", 60))
    return out


def load_gen(path):
    spec = importlib.util.spec_from_file_location("gen_" + os.path.basename(path).replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.signals


def placebo(sig, tr, base, rng):
    """the null at the idea's own rate: one random entry per idea trade this session, a random second and side, the
    exits of the idea's own signal."""
    by_i = {int(s[0]): s for s in sig}
    out = []
    for t in tr:
        s = by_i.get(int(t["i_in"]) - 1)
        ex = dict(s[3]) if s is not None and len(s) > 3 and s[3] else {}
        out.append((int(rng.integers(base["t0"], base["t1"] + 1)), "CE" if rng.random() < 0.5 else "PE", "null", ex))
    return sorted(out, key=lambda x: x[0])


def trades(gen, days, mode=None, day_types=("normal", "expiry"), champ=None, nulls=0, seed=0):
    """the idea's standalone trades; with champ (the champion's trades): also its champion-priority trades and, with
    nulls=K, K random placebos at its trade count (standalone and priority). Returns T, or (T, TP, NT, NP)."""
    if isinstance(gen, str):
        gen = load_gen(gen)
    out = []; pr = []; nt = []; npr = []
    rng = np.random.default_rng(seed)
    for d in days:
        typ = "expiry" if is_expiry(d) else "normal"
        if typ not in day_types or (typ == "expiry" and not has_wx(d)):
            continue
        ctx = context(d)
        if ctx is None:
            continue
        try:
            sig = gen(ctx) or []
        except Exception as e:
            raise RuntimeError(f"generator failed on {d}: {type(e).__name__}: {e}")
        tr = run_day(ctx, sig, mode)
        out += tr
        if champ is not None:
            c = champ[champ.day == d].sort_values("i_in")
            busy = (c.i_in.to_numpy(), c.i_out.to_numpy())
            pr += run_day(ctx, sig, mode, busy=busy)
            base = EXP if ctx["D"]["dte0"] else NORM
            for k in range(nulls):
                ps = placebo(sig, tr, base, rng)
                nt += [dict(t, null=k) for t in run_day(ctx, ps, mode)]
                npr += [dict(t, null=k) for t in run_day(ctx, ps, mode, busy=busy)]
    if champ is None:
        return pd.DataFrame(out)
    return pd.DataFrame(out), pd.DataFrame(pr), pd.DataFrame(nt), pd.DataFrame(npr)


# ── the champion, for pooling: its own entries (gen_champion.py) priced EXACTLY as the idea is ────────────────────────
CHAMP = "D:/ApexOptions/data/research/14nov/agents/_champion_trades.parquet"


def champion_trades(rebuild=False):
    """the champion's trades priced through this harness, cached; rebuilt only on request (rebuild=True), so 30
    agents never rebuild it at once; the owner of the run rebuilds it when new history arrives."""
    days = [d for sp in ("found", "judged", "window") for d in sessions(sp)]          # never the holdout
    sig = dict(days=len(days), wx=len([d for d in days if has_wx(d)]), feat=len([d for d in days if os.path.exists(os.path.join(FE, f"{d}.parquet"))]),
               iv=IV_MODE, pc=IV_PC, basis=BASIS, fallback=FALLBACK)
    if os.path.exists(CHAMP) and not rebuild:
        try:
            old = json.load(open(CHAMP + ".sig"))
        except Exception:
            old = None
        if old != sig:
            print(f"arena: WARNING the champion cache was built on {old}, the data / pricing now is {sig}; "
                  f"ask the run owner to rebuild it (champion_trades(rebuild=True))", file=sys.stderr)
        return pd.read_parquet(CHAMP)
    T = trades(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_champion.py"), days)
    os.makedirs(os.path.dirname(CHAMP), exist_ok=True)
    T.to_parquet(CHAMP + ".tmp"); os.replace(CHAMP + ".tmp", CHAMP)
    open(CHAMP + ".sig", "w").write(json.dumps(sig))
    return T


def pool(a, b):
    """one account: a's trades first on a tie (the live pool order), no pause between trades (as the Conductor)."""
    x = pd.concat([a.assign(_p=0), b.assign(_p=1)], ignore_index=True).sort_values(["day", "i_in", "_p"])
    out = []
    for day, d in x.groupby("day"):
        free = -1
        for r in d.itertuples():
            if r.i_in > free:
                out.append(r._asdict()); free = r.i_out
    return pd.DataFrame(out)


def stats(T, days):
    if T is None or not len(T):
        return dict(sessions=len(days), trades=0)
    T = T[T.day.isin(days)]
    if not len(T):
        return dict(sessions=len(days), trades=0)
    dd = T.groupby("day").ret.apply(lambda r: 100 * (np.prod(1 + r.to_numpy() / 100) - 1)).reindex(days).fillna(0.0)
    sd = dd.std(ddof=1)
    return dict(sessions=len(days), trades=len(T), per_day=round(len(T) / len(days), 2), winners=round(100 * (T.ret > 0).mean(), 1),
                per_trade=round(T.ret.mean(), 2), day_sum=round(dd.sum(), 1), mean_day=round(dd.mean(), 2),
                t=round(dd.mean() / (sd / np.sqrt(len(dd))), 2) if sd > 0 else np.nan, days_up=int((dd > 0).sum()),
                days_down=int((dd < 0).sum()), worst_day=round(dd.min(), 1), best_day=round(dd.max(), 1))


def evaluate(gen, name="idea", splits=("found", "judged", "window"), day_types=("normal", "expiry"), pooled=True, save=None, nulls=8):
    """the idea alone and pooled with the champion, per split and day type. Returns a DataFrame.
    pooled_gain is now the CHAMPION-PRIORITY account (the idea trades only while the champion is flat and is sold when
    a champion trade fills), so it can no longer score by blocking champion losers; pooled_gain_first is the old
    first-come pool. null_gain / null_sd: the same account with `nulls` random placebos at the idea's trade count;
    gain_z = (pooled_gain - null_gain) / null_sd."""
    g = load_gen(gen) if isinstance(gen, str) else gen
    C = champion_trades() if pooled else None
    rows = []
    allT = []
    for sp in splits:
        days = sessions(sp)
        if pooled and C is not None:
            T, TP, NT, NP = trades(g, days, day_types=day_types, champ=C[C.day.isin(days)], nulls=nulls)
        else:
            T = trades(g, days, day_types=day_types); TP = NT = NP = pd.DataFrame()
        if len(T):
            T["split"] = sp
            allT.append(T)
        for typ in day_types:
            dd = [d for d in days if d in lab1s.meta() and is_expiry(d) == (typ == "expiry") and (typ == "normal" or has_wx(d))
                  and (d in REC or os.path.exists(_fut_path(d)))]
            Tt = T[T.day.isin(dd)] if len(T) else T
            r = dict(idea=name, split=sp, days=typ, **{f"{k}": v for k, v in stats(Tt, dd).items()})
            if pooled and C is not None:
                Ct = C[C.day.isin(dd)]
                sc = stats(Ct, dd)
                first = stats(pool(Ct, Tt) if len(Tt) else Ct, dd)
                TPt = TP[TP.day.isin(dd)] if len(TP) else TP
                sb = stats(pd.concat([Ct, TPt], ignore_index=True) if len(TPt) else Ct, dd)
                gains = []
                for k in range(nulls):
                    x = NP[(NP.null == k) & NP.day.isin(dd)] if len(NP) else NP
                    gains.append(stats(pd.concat([Ct, x], ignore_index=True) if len(x) else Ct, dd).get("day_sum", 0) - sc.get("day_sum", 0))
                gain = round(sb.get("day_sum", 0) - sc.get("day_sum", 0), 1)
                nm, ns = (float(np.mean(gains)), float(np.std(gains, ddof=1))) if len(gains) > 1 else (np.nan, np.nan)
                r.update(champ_trades=sc.get("trades", 0), champ_day_sum=sc.get("day_sum", 0), champ_winners=sc.get("winners"),
                         pooled_trades=sb.get("trades", 0), pooled_day_sum=sb.get("day_sum", 0), pooled_winners=sb.get("winners"),
                         pooled_gain=gain, preempted=int((TPt.why == "PREEMPT").sum()) if len(TPt) else 0,
                         pooled_gain_first=round(first.get("day_sum", 0) - sc.get("day_sum", 0), 1),
                         null_gain=round(nm, 1), null_sd=round(ns, 1), gain_z=round((gain - nm) / ns, 2) if ns and ns > 0 else np.nan)
            rows.append(r)
    R = pd.DataFrame(rows)
    if save:
        os.makedirs(os.path.dirname(save), exist_ok=True)
        if allT:
            pd.concat(allT, ignore_index=True).to_parquet(save)
    return R


AGENTS = "D:/ApexOptions/data/research/14nov/agents"


def record(theme, variant, R, note=""):
    """append every variant tried to agents/<theme>/trials.jsonl (the multiple-testing count of docs/60 test 6)."""
    d = os.path.join(AGENTS, theme)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "trials.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(theme=theme, variant=variant, note=note, rows=json.loads(R.to_json(orient="records")))) + "\n")


def report(R):
    cols = [c for c in ("idea", "split", "days", "sessions", "trades", "per_day", "winners", "per_trade", "day_sum", "mean_day", "t", "days_up",
                        "worst_day", "champ_day_sum", "pooled_day_sum", "pooled_gain", "null_gain", "null_sd", "gain_z", "pooled_gain_first",
                        "preempted", "pooled_trades", "pooled_winners", "champ_winners") if c in R]
    with pd.option_context("display.width", 260, "display.max_columns", 40):
        print(R[cols].to_string(index=False))


if __name__ == "__main__":
    R = evaluate(sys.argv[1], name=os.path.basename(sys.argv[1]))
    report(R)
