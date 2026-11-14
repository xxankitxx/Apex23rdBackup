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

Pricing: normal days on the per-second model option (lab1s; 0.98 day-result correlation with real quotes on the
recorded sessions). Expiry days on REAL-IV pricing: the broker's real 1-minute option closes give the implied
volatility of each contract each minute; the price each second is Black-76 on the per-second future with that IV
interpolated through the minute (validated in arena_check.py). Expiry sessions without the minute history are skipped.

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


def context(day):
    if day in _CTX:
        return _CTX[day]
    while len(_CTX) >= CACHE_N:
        _CTX.pop(next(iter(_CTX)))
    D = lab1s.session(day, fwd=FL.load_day(day)["fwd"].copy()) if day in REC else lab1s.session(day)
    if D is None:
        _CTX[day] = None
        return None
    m = lab1s.meta()[day]
    ctx = dict(day=day, D=D, X=lab1s.feats_full(D), M=_minute_feats(day),
               meta=dict(pc=m.get("pc"), ph=m.get("ph"), pl=m.get("pl"), em=m.get("em"), rv20=m.get("rv20"),
                         gap=(m["o"][0] - m["pc"]) if m.get("pc") else None, open=float(m["o"][0] - m["basis"])))
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


def realiv_series(D, K, side):
    """per-second price of contract (K, side): Black-76 on the per-second future with the contract's REAL implied
    volatility, solved each minute from the broker's 1-minute close and interpolated through the minute. None when
    the contract has no minute history that day."""
    wx = _wx(D["day"])
    if wx is None:
        return None
    from s44_wxfeat import minute_grid
    key = f"opt:{int(K)}:{'call' if side == 'CE' else 'put'}"
    if key not in set(wx.what.unique()):
        return None
    c = minute_grid(wx, key)
    if not np.isfinite(c).any():
        return None
    fw = FL._ffill0(D["fwd"])
    call = side == "CE"
    ends = np.minimum(np.arange(375) * 60 + 59, N - 1)
    with np.errstate(all="ignore"):
        ivm = FL.iv_of(fw[ends], float(K), D["T"][ends], c, call)
    ivm = pd.Series(ivm).ffill().bfill().to_numpy()
    if not np.isfinite(ivm).any():
        return None
    iv = np.interp(np.arange(N), ends, ivm)
    with np.errstate(all="ignore"):
        return FL.b76(fw, float(K), D["T"], np.maximum(iv, 0.01), call)


def model_series(D, K, side):
    with np.errstate(all="ignore"):
        return FL.b76(FL._ffill0(D["fwd"]), float(K), D["T"], D["iv"], side == "CE")


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


def run_day(ctx, sigs, mode=None):
    """one position at a time; returns the trades."""
    D = ctx["D"]
    mode = mode or ("realiv" if has_wx(ctx["day"]) else ("model" if not D["dte0"] else None))
    if mode is None:
        return []
    base = EXP if D["dte0"] else NORM
    out = []; free = base["t0"]
    cache = {}
    for s in sorted(sigs, key=lambda x: x[0]):
        i, side, tag = int(s[0]), s[1], s[2]
        ex = dict(s[3]) if len(s) > 3 and s[3] else {}
        P = dict(base, **{k: v for k, v in ex.items() if k in ("sl", "trail", "hold", "floor", "ptrail", "tp", "dt", "cool")})
        P["dt"] = max(float(P.get("dt", base["dt"])), 0.52)
        if i < free or i < base["t0"] or i > base["t1"] or side not in ("CE", "PE"):
            continue
        K = pick_strike(D, i, side, P["dt"])
        if K is None:
            continue
        key = (K, side)
        if key not in cache:
            px, how = _price(D, K, side, mode)
            if px is None:
                cache[key] = None
            else:
                o = np.full((N, 1, 2, 2), np.nan, np.float32)
                c = 0 if side == "CE" else 1
                o[:, 0, c, 0] = px * (1 - HALF); o[:, 0, c, 1] = px * (1 + HALF)
                Dm = FL.Day(dict(D)); Dm["opt"] = o; Dm["K"] = np.array([K])
                cache[key] = (Dm, how)
        if cache[key] is None:
            continue
        Dm, how = cache[key]
        ext = None
        if ex.get("stall"):
            import fam
            ext = fam.stall(*ex["stall"])
        t = FL.exit_ladder(Dm, i, side, 0, P, ext)
        if t is None:
            continue
        t.update(day=ctx["day"], tag=tag, dte=D["dte"], price=how, minute=i // 60)
        out.append(t)
        free = t["i_out"] + int(P.get("cool", 60))
    return out


def load_gen(path):
    spec = importlib.util.spec_from_file_location("gen_" + os.path.basename(path).replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.signals


def trades(gen, days, mode=None, day_types=("normal", "expiry")):
    if isinstance(gen, str):
        gen = load_gen(gen)
    out = []
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
        out += run_day(ctx, sig, mode)
    return pd.DataFrame(out)


# ── the champion, for pooling: its own entries (gen_champion.py) priced EXACTLY as the idea is ────────────────────────
CHAMP = "D:/ApexOptions/data/research/14nov/agents/_champion_trades.parquet"


def champion_trades(rebuild=False):
    """the champion's trades priced through this harness, cached; rebuilt only on request (rebuild=True), so 30
    agents never rebuild it at once; the owner of the run rebuilds it when new history arrives."""
    if os.path.exists(CHAMP) and not rebuild:
        return pd.read_parquet(CHAMP)
    days = sessions()
    sig = (len(days), len([d for d in days if has_wx(d)]))
    T = trades(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_champion.py"), days)
    os.makedirs(os.path.dirname(CHAMP), exist_ok=True)
    T.to_parquet(CHAMP)
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


def evaluate(gen, name="idea", splits=("found", "judged", "window"), day_types=("normal", "expiry"), pooled=True, save=None):
    """the idea alone and pooled with the champion, per split and day type. Returns a DataFrame."""
    g = load_gen(gen) if isinstance(gen, str) else gen
    C = champion_trades() if pooled else None
    rows = []
    allT = []
    for sp in splits:
        days = sessions(sp)
        T = trades(g, days, day_types=day_types)
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
                both = pool(Ct, Tt) if len(Tt) else Ct
                sc, sb = stats(Ct, dd), stats(both, dd)
                r.update(champ_trades=sc.get("trades", 0), champ_day_sum=sc.get("day_sum", 0), champ_winners=sc.get("winners"),
                         pooled_trades=sb.get("trades", 0), pooled_day_sum=sb.get("day_sum", 0), pooled_winners=sb.get("winners"),
                         pooled_gain=round(sb.get("day_sum", 0) - sc.get("day_sum", 0), 1))
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
                        "worst_day", "champ_day_sum", "pooled_day_sum", "pooled_gain", "pooled_trades", "pooled_winners", "champ_winners") if c in R]
    with pd.option_context("display.width", 260, "display.max_columns", 40):
        print(R[cols].to_string(index=False))


if __name__ == "__main__":
    R = evaluate(sys.argv[1], name=os.path.basename(sys.argv[1]))
    report(R)
