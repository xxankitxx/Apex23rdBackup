"""Ideas board (owner, 29 Oct 2026: "I want to test my ideas later. I still want them somewhere in the UI so that I can
get an idea as to what is happening. Keep your best champion to keep giving trades.")

The owner's ideas -- and the ones the 28-29 Oct research rejected -- computed live from the same ticks, shown on the
dashboard and taped to <PAPER_DIR>/ideas_<day>.jsonl so they can be judged later against the champion's trades.

OBSERVERS ONLY. No book, gate or exit reads anything from here: the board is fed AFTER the books have run, it gets
copies of what it needs, and its view goes only to the dashboard and the tape.

Each idea is one module `i<NN>_<slug>.py` in this package with:

    NAME = "slug"                # unique, lower case
    TITLE = "Short title"        # <= 32 chars, shown on the card
    IDEA = "what it watches"     # one line: the owner's idea in plain words
    VERDICT = "research verdict" # one line: what the 28-29 Oct research found (or "new, untested")
    EVERY_S = 5                  # how often update() runs (1..60 s)

    class Idea:
        def update(self, env):   # -> dict, see _clean() for the fields
            ...

`env` (Env, read-only) gives the current chain and 1-Hz histories; see Env / History below. An idea that raises
5 times, or takes > IDEAS_SLOW_MS on average, is switched off for the day and the card says so.
"""
import copy
import importlib
import json
import math
import os
import pkgutil
import time
from datetime import datetime

import numpy as np

from ... import config

# history fields per option, in column order (column 0 is the epoch second)
OPT_FIELDS = ("t", "ltp", "bid", "ask", "mid", "tbq", "tsq", "ttq", "oi", "iv", "delta", "gamma", "theta", "vega")
_COL = {f: i for i, f in enumerate(OPT_FIELDS)}
SCALAR_KEYS = ("SPOT", "FUT")


def _f(x):
    """float or nan"""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return math.nan
    return v if math.isfinite(v) else math.nan


class History:
    """1-Hz ring buffers, IDEAS_HIST_S long. Keys: "SPOT", "FUT" (fields "t", "v") and (strike, "CE"/"PE") for the
    nearest weekly (fields OPT_FIELDS). Missing values are nan. Arrays returned are oldest -> newest and must not be
    modified."""

    def __init__(self, length):
        self.L = int(length)
        self._buf = {}          # key -> [array (L, ncol), next write index, count]
        self._cache = {}
        self.now = None

    def _ring(self, key, ncol):
        r = self._buf.get(key)
        if r is None:      # every row is written twice (i and i + L) so the last L rows are always one slice: no copy
            r = self._buf[key] = [np.full((2 * self.L, ncol), np.nan), 0, 0]
        return r

    def add(self, key, row):
        r = self._ring(key, len(row))
        a, i = r[0], r[1]
        a[i] = row
        a[i + self.L] = row
        r[1] = (i + 1) % self.L
        r[2] = min(r[2] + 1, self.L)

    def tick(self, now):
        self.now = now
        self._cache.clear()

    def keys(self):
        return list(self._buf)

    def table(self, key):
        """(n, ncol) array oldest -> newest, or None."""
        c = self._cache.get(key)
        if c is not None:
            return c
        r = self._buf.get(key)
        if r is None or r[2] == 0:
            return None
        a, i, n = r
        out = a[:n] if n < self.L else a[i:i + self.L]
        out = out.view()
        out.flags.writeable = False
        self._cache[key] = out
        return out

    def series(self, key, field="ltp", secs=None, since=None):
        """(T, V) arrays for one field. secs: only the last `secs` seconds; since: only t > since."""
        tab = self.table(key)
        if tab is None:
            return np.empty(0), np.empty(0)
        col = 1 if key in SCALAR_KEYS else _COL[field]
        T, V = tab[:, 0], tab[:, col]
        lo = None
        if secs is not None and self.now is not None:
            lo = self.now - secs
        if since is not None:
            lo = since if lo is None else max(lo, since)
        if lo is not None:
            j = int(np.searchsorted(T, lo, side="right" if since is not None else "left"))
            T, V = T[j:], V[j:]
        return T, V

    def at(self, key, field="ltp", secs_ago=0.0):
        """The newest value at or before now - secs_ago (nan if none)."""
        tab = self.table(key)
        if tab is None or self.now is None:
            return math.nan
        T = tab[:, 0]
        j = int(np.searchsorted(T, self.now - secs_ago, side="right")) - 1
        if j < 0:
            return math.nan
        return float(tab[j, 1 if key in SCALAR_KEYS else _COL[field]])


class Env:
    """What an idea sees (read-only).

    t, dt, hm        epoch s, IST datetime, minutes since midnight (hm(9:15) = 555)
    spot, fut        Nifty index (None while untrusted) and futures mid
    atm, step        ATM strike (nearest to spot, else futures) and strike step (50)
    expiry, dte0     the nearest weekly expiry (ISO) and whether today is its expiry day
    chain            {(strike, "CE"/"PE"): row} for the nearest weekly, ATM +- IDEAS_STRIKES; row keys:
                     strike rr ltp bid ask mid tbq tsq ttq oi iv delta gamma theta vega age
                     (tbq/tsq = total qty waiting to buy/sell; ttq = cumulative volume; oi = open interest, updates
                     about once a minute; theta per MINUTE; iv decimal; age = s since the quote; None if unknown)
    hist             History (1 Hz, IDEAS_HIST_S long) for "SPOT", "FUT" and every (strike, rr) ever in the band
    champ            the champion's open position or None: {rr, strike, entry, t_in, ret_pct, ep_type}
    trades           the champion's closed trades today (dicts: time_in time_out rr strike ret_pct reason)
    episode          the champion's trigger state (copy) or None; day = day-state levels (copy); regime (copy)
    """
    __slots__ = ("t", "dt", "hm", "spot", "fut", "atm", "step", "expiry", "dte0", "chain", "hist", "champ", "trades",
                 "episode", "day", "regime")

    def row(self, strike, rr):
        return self.chain.get((strike, rr))

    def strikes(self):
        return sorted({k for k, _ in self.chain})


def _clean(d, prev):
    """Validate an idea's output. Fields: state (short label, required), side ("CE"/"PE"/None: the option it would
    favour), value (number or None) + unit, text (<= 160 chars), alert (bool: tape it even if the state did not
    change), plan (optional short string: what to prepare for, e.g. "CE 25900 if spot > 25920")."""
    if not isinstance(d, dict):
        raise TypeError("update() must return a dict")
    st = str(d.get("state") or "").strip()[:28] or "—"
    side = d.get("side")
    side = side if side in ("CE", "PE") else None
    v = d.get("value")
    try:
        v = None if v is None else float(v)
        if v is not None and not math.isfinite(v):
            v = None
    except (TypeError, ValueError):
        v = None
    return {"state": st, "side": side, "value": None if v is None else round(v, 4),
            "unit": str(d.get("unit") or "")[:12], "text": str(d.get("text") or "")[:160],
            "plan": str(d.get("plan") or "")[:80], "alert": bool(d.get("alert"))}


class _Slot:
    __slots__ = ("mod", "obj", "name", "every", "phase", "out", "since", "errors", "ms", "calls", "off", "flips",
                 "last_t")

    def __init__(self, mod, k):
        self.mod = mod
        self.obj = mod.Idea()
        self.name = str(mod.NAME)
        self.every = max(1, min(60, int(getattr(mod, "EVERY_S", 5) or 5)))
        self.phase = k % self.every
        self.out = None
        self.since = None
        self.errors = 0
        self.ms = 0.0
        self.calls = 0
        self.off = ""
        self.flips = []
        self.last_t = None


def discover():
    """All idea modules in this package (i<NN>_*.py), sorted by file name. A module that fails to import is skipped
    and reported."""
    mods, bad = [], []
    for m in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if not m.name.startswith("i") or not m.name[1:3].isdigit():
            continue
        try:
            mod = importlib.import_module(f"{__name__}.{m.name}")
            assert hasattr(mod, "Idea") and hasattr(mod, "NAME"), "needs NAME and class Idea"
            mods.append(mod)
        except Exception as e:      # an idea must never stop the engine
            bad.append((m.name, f"{type(e).__name__}: {e}"))
    return mods, bad


class Board:
    def __init__(self, day, out_dir=None, log=None, tape=True):
        self.day = day
        self.log = log or (lambda s: None)
        self.path = os.path.join(out_dir or config.PAPER_DIR, f"ideas_{day}.jsonl") if tape else None
        self.hist = History(getattr(config, "IDEAS_HIST_S", 3600))
        mods, bad = discover()
        self.slots, names = [], set()
        for k, mod in enumerate(mods):
            try:
                s = _Slot(mod, k)
                if s.name in names:
                    raise ValueError(f"duplicate NAME {s.name}")
                names.add(s.name)
                self.slots.append(s)
            except Exception as e:
                bad.append((mod.__name__, f"{type(e).__name__}: {e}"))
        self.bad = bad
        for n, e in bad:
            self.log(f"ideas: {n} not loaded ({e})")
        self.last_feed = -1e9
        self.last_snap = -1e9
        self.env = None
        self._fh = None
        self.stats = {"feed_ms": 0.0, "eval_ms": 0.0}

    # ── tape ─────────────────────────────────────────────────────────────
    def _tape(self, rec):
        if not self.path:
            return
        try:
            if self._fh is None:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                self._fh = open(self.path, "a", encoding="utf-8")
            self._fh.write(json.dumps(rec, separators=(",", ":"), default=str) + "\n")
            self._fh.flush()
        except OSError:
            pass

    def close(self):
        if self._fh is not None:
            try:
                self._fh.close()
            except OSError:
                pass
            self._fh = None

    # ── feed (1 Hz) ──────────────────────────────────────────────────────
    def feed_rows(self, now, dt, spot, fut, expiry, rows, champ=None, trades=None, episode=None, day=None,
                  regime=None):
        """rows: dicts with strike rr expiry ltp bid ask tbq tsq ttq oi iv delta gamma theta vega age (any may be
        None). Only the nearest weekly within IDEAS_STRIKES of ATM is kept."""
        t0 = time.perf_counter()
        step = getattr(config, "STRIKE_STEP", 50)
        ref = spot if spot else fut
        if not ref:
            return
        atm = int(round(ref / step) * step)
        band = getattr(config, "IDEAS_STRIKES", 10) * step
        chain = {}
        for o in rows:
            if o.get("expiry") != expiry or o.get("rr") not in ("CE", "PE"):
                continue
            k = o.get("strike")
            if k is None or abs(k - atm) > band + 1e-6:
                continue
            k = int(round(k))
            b, a, ltp = _f(o.get("bid")), _f(o.get("ask")), _f(o.get("ltp"))
            mid = (b + a) / 2 if (b > 0 and a > 0 and a >= b) else ltp
            r = {"strike": k, "rr": o["rr"], "ltp": ltp, "bid": b, "ask": a, "mid": mid,
                 "tbq": _f(o.get("tbq")), "tsq": _f(o.get("tsq")), "ttq": _f(o.get("ttq")), "oi": _f(o.get("oi")),
                 "iv": _f(o.get("iv")), "delta": _f(o.get("delta")), "gamma": _f(o.get("gamma")),
                 "theta": _f(o.get("theta")), "vega": _f(o.get("vega")), "age": _f(o.get("age"))}
            for kk, vv in r.items():
                if isinstance(vv, float) and math.isnan(vv):
                    r[kk] = None
            chain[(k, o["rr"])] = r
            self.hist.add((k, o["rr"]), [now, ltp, b, a, mid, _f(o.get("tbq")), _f(o.get("tsq")),
                                         _f(o.get("ttq")), _f(o.get("oi")), _f(o.get("iv")),
                                         _f(o.get("delta")), _f(o.get("gamma")), _f(o.get("theta")),
                                         _f(o.get("vega"))])
        if spot:
            self.hist.add("SPOT", [now, float(spot)])
        if fut:
            self.hist.add("FUT", [now, float(fut)])
        self.hist.tick(now)
        e = Env()
        e.t, e.dt = now, dt
        e.hm = dt.hour * 60 + dt.minute + dt.second / 60.0
        e.spot, e.fut, e.atm, e.step = spot, fut, atm, step
        e.expiry = expiry
        e.dte0 = dt.date().isoformat() == expiry
        e.chain, e.hist = chain, self.hist
        e.champ, e.trades = champ, list(trades or [])
        e.episode, e.day, e.regime = episode, day, regime
        self.env = e
        self.last_feed = now
        self.stats["feed_ms"] = 0.9 * self.stats["feed_ms"] + 0.1 * (time.perf_counter() - t0) * 1000

    # ── evaluate (staggered) ─────────────────────────────────────────────
    def evaluate(self):
        e = self.env
        if e is None:
            return
        now = e.t
        sec = int(now)
        t_all = time.perf_counter()
        slow_ms = getattr(config, "IDEAS_SLOW_MS", 40.0)
        for s in self.slots:
            if s.off or (sec % s.every) != s.phase or s.last_t == sec:
                continue
            s.last_t = sec
            t0 = time.perf_counter()
            try:
                out = _clean(s.obj.update(e), s.out)
            except Exception as ex:
                s.errors += 1
                if s.errors == 1 or s.errors >= 5:
                    self.log(f"ideas: {s.name} faulted ({type(ex).__name__}: {ex})")
                if s.errors >= 5:
                    s.off = f"switched off after 5 faults: {type(ex).__name__}"
                    self._tape({"kind": "off", "time": e.dt.strftime("%H:%M:%S"), "name": s.name, "why": s.off})
                continue
            ms = (time.perf_counter() - t0) * 1000
            s.calls += 1
            s.ms = ms if s.calls == 1 else 0.9 * s.ms + 0.1 * ms
            if (s.calls >= 20 and s.ms > slow_ms) or (s.calls > 3 and ms > 25 * slow_ms):   # one slow first call (lazy numpy imports) is forgiven
                s.off = f"switched off: too slow ({s.ms:.0f} ms)"
                self.log(f"ideas: {s.name} {s.off}")
                self._tape({"kind": "off", "time": e.dt.strftime("%H:%M:%S"), "name": s.name, "why": s.off})
            prev = s.out
            flip = prev is None or prev["state"] != out["state"] or prev["side"] != out["side"]
            if flip:
                s.since = e.dt.strftime("%H:%M:%S")
            if (flip and prev is not None) or out["alert"]:
                rec = {"kind": "alert" if (out["alert"] and not flip) else "flip", "time": e.dt.strftime("%H:%M:%S"),
                       "t": round(now, 1), "name": s.name, "state": out["state"], "side": out["side"],
                       "value": out["value"], "unit": out["unit"], "text": out["text"], "plan": out["plan"],
                       "from": prev["state"] if prev else None, "alert": out["alert"], "spot": e.spot, "fut": e.fut,
                       "champ": _champ_tag(e.champ)}
                self._tape(rec)
                s.flips.insert(0, [rec["time"], out["state"], out["side"]])
                del s.flips[6:]
            s.out = out
        if now - self.last_snap >= 60:
            self.last_snap = now
            self._tape({"kind": "snap", "time": e.dt.strftime("%H:%M:%S"), "t": round(now, 1), "spot": e.spot,
                        "fut": e.fut, "atm": e.atm, "champ": _champ_tag(e.champ),
                        "ideas": {s.name: ([s.out["state"], s.out["side"], s.out["value"]] if s.out else None)
                                  for s in self.slots if not s.off}})
        self.stats["eval_ms"] = 0.9 * self.stats["eval_ms"] + 0.1 * (time.perf_counter() - t_all) * 1000

    # ── engine adapter ───────────────────────────────────────────────────
    def step(self, eng, ctx, snap):
        """Called by the engine at the END of a step (after the books). Feeds at 1 Hz, evaluates the due ideas."""
        now = ctx.get("now_s")
        if now is None or now - self.last_feed < 1.0:
            return
        hm = eng.now_dt.hour * 60 + eng.now_dt.minute
        if hm < 9 * 60 + 15 or hm > 15 * 60 + 30:
            return
        tbq, tsq, ttq, oi = snap["tbq"], snap["tsq"], snap["ttq"], snap["oi"]
        greek = eng.greek
        rows = []
        w0 = ctx.get("w0")
        ref = ctx.get("spot") or ctx.get("fut")
        band = getattr(config, "IDEAS_STRIKES", 10) * getattr(config, "STRIKE_STEP", 50) + 1
        for o in ctx.get("options") or ():
            if o.get("expiry") != w0 or not ref or abs(o["strike"] - ref) > band + 50:
                continue
            i = o["id"]
            g = greek.get(i, {})
            rows.append(dict(o, tbq=float(tbq[i]), tsq=float(tsq[i]), ttq=float(ttq[i]), oi=float(oi[i]),
                             theta=o.get("theta_min"), vega=g.get("vega")))
        champ, trades = None, []
        b = (eng.books or {}).get(eng.champion)
        if b is not None:
            if b.pos:
                p = b.pos
                o = ctx["by_key"].get(p.get("key")) or {}
                last = o.get("ltp") or p.get("last") or p.get("entry")
                champ = {"rr": p.get("rr"), "strike": p.get("strike"), "entry": p.get("entry"), "t_in": p.get("t_in"),
                         "ret_pct": (100.0 * (last - p["entry"]) / p["entry"]) if p.get("entry") and last else None,
                         "ep_type": p.get("ep_type")}
            trades = [{k: t.get(k) for k in ("time_in", "time_out", "rr", "strike", "ret_pct", "reason")}
                      for t in b.trades[-20:]]
        self.feed_rows(now, eng.now_dt, ctx.get("spot"), ctx.get("fut"), w0, rows, champ=champ, trades=trades,
                       episode=copy.deepcopy(ctx.get("episode")), day=_plain(ctx.get("day")),
                       regime=copy.deepcopy(ctx.get("regime")))
        self.evaluate()

    # ── dashboard ────────────────────────────────────────────────────────
    def view(self):
        out = []
        for s in self.slots:
            o = s.out or {}
            out.append({"name": s.name, "title": str(getattr(s.mod, "TITLE", s.name))[:40],
                        "idea": str(getattr(s.mod, "IDEA", ""))[:200], "verdict": str(getattr(s.mod, "VERDICT", ""))[:200],
                        "state": o.get("state"), "side": o.get("side"), "value": o.get("value"), "unit": o.get("unit"),
                        "text": o.get("text"), "plan": o.get("plan"), "since": s.since, "off": s.off,
                        "ms": round(s.ms, 2), "flips": s.flips[:4], "every": s.every})
        return {"ideas": out, "bad": [list(b) for b in self.bad], "eval_ms": round(self.stats["eval_ms"], 2),
                "feed_ms": round(self.stats["feed_ms"], 2), "file": os.path.basename(self.path) if self.path else None}


def _champ_tag(c):
    if not c:
        return None
    r = c.get("ret_pct")
    return f"{c.get('rr')} {c.get('strike'):.0f} {r:+.1f}%" if (r is not None and c.get("strike")) else f"{c.get('rr')}"


def _plain(d):
    """A JSON-safe deep copy of the day-state view (drops objects)."""
    if not d:
        return None
    try:
        return json.loads(json.dumps({k: v for k, v in d.items() if k != "day_obj"}, default=lambda o: None))
    except (TypeError, ValueError):
        return None
