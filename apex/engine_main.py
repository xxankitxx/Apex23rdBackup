"""
ENGINE process — everything that thinks, isolated from the tick path.

Every 100 ms of system time (wall clock live; virtual clock in sim/replay):
  sample the shared table -> buyers/sellers flow -> Greeks (4 Hz) -> pressure
  zones (on new chain) -> domino/basket + episode -> force detector ->
  advisors -> every variant's paper book (exits, then entries)
Every 250 ms: publish the full state for the dashboard.
At the close (or a date change): save books, write the trades CSV, record the
day for learning, run the learning loop, start the new day with its decisions.
"""
import bisect
import json
import math
import os
import sys
import time
import traceback
from collections import deque
from datetime import datetime

import numpy as np

from . import audio, config, greeks
from .engine import learning, paper
from .engine.extras import BankLead, EpisodeLog, LagMeter, Straddle, event_today
from .engine.straddle_watch import StraddleWatch
from .engine.gex import GexMap
from .engine.guard import RESUME_S, DataGuard, in_session
from .engine.ledger import Ledger
from .engine.commentary import Commentary
from .engine.regime import Regime
from .engine import missed as missed_mod      # 7 Nov: missed-signal recorder (replays, APEX_RECORD_MISSED=1)
try:                                     # 5 Nov: display-only quant evidence (needs scipy)
    from .engine.quantview import QuantView
except Exception:                        # pragma: no cover - a missing scipy must never stop the engine
    QuantView = None
from .engine.impulse import ImpulseWindow
from .engine.weather import Weather   # 7 Nov: stage 2, the weather photograph (observer)
from .engine.daystate import DayState, load_prior, save_day
from .engine import strike_levels as sl_mod
from .engine import ideas as ideas_mod
from .engine import edge as edge_mod
from .engine.domino import Domino
from .engine.flow import CLS, REFILL, Flow
from .engine.levels import Force, Pressure
from .engine.market import Market
from .feed_core import Registry
from .table import StateBlob, Table, clean, FEED_STATES

try:                                       # C-34: the decision tape groups reasons like the report does
    from .engine.diagnostics import reason_class as _reason_class
except Exception:                          # pragma: no cover - fall back to the text before the first ":"
    _reason_class = None

LOG = None
MKT = {"dt": None}                         # C-77: the engine's market clock, for log lines


def log(msg):
    mdt = MKT.get("dt")
    mkt = f" mkt={mdt.strftime('%H:%M:%S')}" if mdt is not None else ""
    line = f"{datetime.now(config.IST).strftime('%H:%M:%S')}{mkt} ENGINE {msg}"
    print(line, flush=True)
    try:
        LOG.write(line + "\n"); LOG.flush()
    except Exception:
        pass


def reason_cls(why, fired=False):
    """Category of the champion's reason (diagnostics.reason_class, or the text up to its first ':')."""
    if _reason_class is not None:
        try:
            return _reason_class({"decision_at_cross": why or "", "fired": bool(fired)})
        except Exception:
            pass
    return "TAKEN" if fired else (why or "").split(":")[0].strip()


def _append_jsonl(path, rec):
    """Append one JSON line; never raises (a full disk must not stop the loop)."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(clean(rec), default=str) + "\n")
        return True
    except Exception:
        return False


def _pos_finite(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and x > 0 else None


def _interp_atm_iv(strikes, K, iv, F, ce_j=None, pe_j=None):
    """O-1 observer: IV at the forward F, linear in strike between the two strikes bracketing F,
    each strike's IV being the mean of its finite CE and PE IVs. None if F is not bracketed.
    (T02: with ce_j/pe_j — the row of each strike's CE and PE, -1 if absent — the per-strike means are
    one vector pass: one finite leg -> that value (v + 0.0), two -> (ce + pe) / 2.0, as np.mean does.)"""
    pts = []
    if ce_j is not None:
        c = np.where(ce_j >= 0, iv[ce_j], np.nan)
        q = np.where(pe_j >= 0, iv[pe_j], np.nan)
        fc, fp = np.isfinite(c), np.isfinite(q)
        cnt = fc.astype(float) + fp.astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = (np.where(fc, c, 0.0) + np.where(fp, q, 0.0)) / cnt
        for k, mv, n in zip(strikes, mean.tolist(), cnt.tolist()):
            if n > 0:
                pts.append((float(k), float(mv)))
    else:
        for k in strikes:
            v = iv[K == k]
            v = v[np.isfinite(v)]
            if v.size:
                pts.append((float(k), float(v.mean())))
    if not pts or F is None or not np.isfinite(F):
        return None
    lo = [p for p in pts if p[0] <= F]
    hi = [p for p in pts if p[0] >= F]
    if not lo or not hi:
        return None
    (k0, v0), (k1, v1) = lo[-1], hi[0]
    if k1 == k0:
        return v0
    return v0 + (v1 - v0) * (F - k0) / (k1 - k0)


def fnum(x, nd=2):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, nd) if math.isfinite(x) else None


class Engine:
    def __init__(self, table: Table, blob: StateBlob, mode: str):
        self.t, self.blob, self.mode = table, blob, mode
        self.m = Market()
        self.flow = Flow(config.MAX_ROWS)
        self.pressure = Pressure()
        self.gex = GexMap()
        self.force = Force()
        self.reg_version = -1
        self.items = []
        self.domino = None
        self.events = deque(maxlen=120)
        self.guard = DataGuard()             # D-063: no decisions on frozen or just-resumed data
        self._day_hi = self._day_lo = None   # today's futures high / low, shown in the header
        self._last_step_s = None
        self.tainted_spikes = set()
        self._gap_on = True
        self.greek = {}                      # row id -> dict(iv, delta, theta_min, vega)
        self.iv_hist = deque(maxlen=900)     # (t, atm_iv) at 1 Hz
        self.fut_hist = deque()               # D-114/D-115: (t, futures mid) at 1 Hz, 35 min
        self._spot_bad = ""                   # D-132: why the Nifty index print is not trusted right now ("" = trusted)
        self._basis_hist = deque()            # D-132: (t, future - spot) over the last 30 valid minutes
        self._sp_chg = None                   # D-132: (t, spot value, future at that time) of the last change in spot
        self.impulse = ImpulseWindow(config.PB_WINDOW_S)   # D-134: 45-min spot window for the pullback book
        self._pb_view = {"ok": False}
        self.day_state = None                 # D-141: session extremes, range mode, opening range, prior-day levels
        self.spot_hist = deque()              # D-116: (t, Nifty spot) at 1 Hz, in session, SPOT_DC_S long
        self.oi_hist = deque(maxlen=400)     # (t, {id: oi}) at 1 Hz (heroes + futures)
        self._ohist = {}                     # 28 Oct night: option id -> deque of (t, iv, tbq) at 1 Hz (paper.flow_veto)
        self._ohist_t = -1e9
        self._ohist_on = any(v.get("iv_fall_rel15") is not None or v.get("skip_bid_pile")
                             or v.get("entry_hi5_veto_pct") or v.get("req_move_veto") or v.get("cheap_strike")
                             for v in config.VARIANTS.values())
        # 29 Oct midday: books with spot_src="fwd" read a spot-unit put-call-parity forward instead of Nifty spot
        self._fwd_on = any(v.get("spot_src") == "fwd" for v in config.VARIANTS.values())
        self._reset_fwd()
        self._fwd_t = None
        self.last_greeks = self.last_publish = self.last_1hz = 0.0
        self.day = None
        self.books = {}
        self.lstate = learning.load_state()
        self.last_reason = ""
        self.loop_ms = 0.0
        self.advisors = {}
        self.ctx = {}
        self.straddle = Straddle()
        self.watch = StraddleWatch()          # fixed-strike straddle: spikes, gamma leg, ATM rolls
        self._watch_err = 0.0
        self.bank = BankLead()
        self.lag = LagMeter()
        self.eplog = None
        self._err_t = {}                     # C-07: name -> last time a fault was logged (throttle)
        self.engine_ok_s = None              # C-08: market time of the last step that completed
        self._exit_sig = None                # C-11: open-position exit state as last saved
        self._exit_sig_t = None
        self._dec_cls = None                 # C-34: last champion reason class written to the tape
        self._dec_n = 0
        self.atm_iv_interp = None            # O-1 observer: ATM IV interpolated at F (never a trigger input)
        self.ideas = None                    # 29 Oct: the Ideas board (observers only, never read by a book)

    # ── fault isolation (C-07) ─────────────────────────────────────────────
    _kill_t, _kill_v = -1e18, False
    missed = None                       # 7 Nov: the missed-signal recorder (replays only)

    def _kill_on(self):
        """The kill-switch file, checked at most every 0.5 s of wall time (one stat cost ~1.7 ms on Windows, every
        100-ms step). Entries stop within half a second of the file appearing."""
        now = time.monotonic()
        if now - self._kill_t >= 0.5:
            self._kill_t = now
            self._kill_v = bool(config.KILL_FILE and os.path.exists(config.KILL_FILE))
        return self._kill_v

    def _safe(self, name, fn, default=None):
        """Run fn(); on an exception log it (at most once a minute per name) and return default.
        Advisors and observers go through here so one fault can never skip the books' exits."""
        try:
            return fn()
        except Exception:
            self._fault(name)
            return default

    def _fault(self, name):
        """Log the exception being handled, at most once a minute per name."""
        now = time.monotonic()
        if now - self._err_t.get(name, -1e9) > 60:
            self._err_t[name] = now
            log(f"{name} faulted: " + traceback.format_exc().strip().splitlines()[-1])

    # ── registry ───────────────────────────────────────────────────────────
    def load_registry(self):
        v = int(self.t.c("reg_version"))
        if v == self.reg_version or v <= 0:
            return
        reg = Registry.load()
        self.reg_version = v
        old_key = getattr(self, "key", {})
        self.items = reg["items"]
        self.key = {it["key"]: it["id"] for it in self.items}
        moved = any(old_key.get(k) not in (None, i) for k, i in self.key.items())
        if moved:                                   # a feed restart re-numbered rows: history is void
            log("instrument ids changed — resetting price history")
            self.m = Market()
            self.flow = Flow(config.MAX_ROWS)
            self.greek = {}
            self.iv_hist.clear(); self.oi_hist.clear()
        self.opts = [it for it in self.items if it["kind"] == "opt"]
        self.fut_id = self.key.get("NIFTY|FUT")
        self.spot_id = self.key.get("NIFTY|SPOT")
        if self.spot_id is None:
            log("registry has no NIFTY|SPOT row — the spot-breakout books cannot trade")
            self.ev("DATA", "no Nifty index row in the registry: the spot books cannot trade")
        self.m.mid_rows = (self.fut_id,) if (config.FUT_PRICE_IS_MID and self.fut_id is not None) else ()
        self.bn_id = self.key.get("BANKNIFTY|FUT") or self.key.get("BANKNIFTY|SPOT")
        if self.domino is None:
            self.domino = Domino(self.items, config.MAX_ROWS)
        else:
            self.domino.reload(self.items, config.MAX_ROWS)
        exps = sorted({it["expiry"] for it in self.opts})
        self.w0 = exps[0] if exps else ""
        self.w1 = exps[1] if len(exps) > 1 else ""
        log(f"registry v{v}: {len(self.items)} instruments, weekly {self.w0}, next {self.w1}")

    # ── day lifecycle ──────────────────────────────────────────────────────
    def start_day(self, day):
        self.day = day
        self.armed_ep = None
        self.eplog = EpisodeLog(day)
        self.lag = LagMeter()
        self.straddle = Straddle()
        if getattr(self, "watch", None) is not None:
            self.watch.close()
        self.watch = StraddleWatch(day)
        if getattr(self, "ideas", None) is not None:
            self._safe("ideas close", self.ideas.close)
        self.ideas = (self._safe("ideas board", lambda: ideas_mod.Board(day, log=log), None)
                      if getattr(config, "IDEAS_ON", False) else None)
        self.lstate = learning.load_state()
        loaded = paper.load_books(day)
        champ = self.lstate["champion"]
        if champ not in config.VARIANTS or champ in config.CONTROLS:
            log(f"learning state names champion {champ!r}, not a registered variant — using {config.CHAMPION_DEFAULT}")
            champ = self.lstate["champion"] = config.CHAMPION_DEFAULT
        books = {}
        for name, params in config.VARIANTS.items():
            books[name] = (loaded or {}).get(name) or paper.Book(name, params, day)
        books["RAW"] = (loaded or {}).get("RAW") or paper.Book("RAW", config.VARIANTS[champ], day)
        # D-067: each CANDIDATE advisor trades as a hard gate on its own copy of the champion
        for a in self.lstate.get("candidates", {}):
            name = learning.GATED_PREFIX + a
            books[name] = (loaded or {}).get(name) or paper.Book(name, config.VARIANTS[champ], day)
        self.books = books
        self.champion = champ
        self.gates = list(self.lstate.get("gates", []))
        self.guard.new_day()
        self._day_hi = self._day_lo = None
        self.tainted_spikes = set()
        self.regime = Regime()                   # D-069: market state, session-aware, no look-ahead
        for k in ("_syn_state", "_ofi_state", "_frozen_prev", "_frozen_t"):     # 7 Nov (B18): edge.py's EWMA / OFI state is per day, as in a replay
            self.__dict__.pop(k, None)
        self.quant = self._safe("quant view", QuantView, None) if QuantView else None   # 5 Nov: display only
        self.impulse = ImpulseWindow(config.PB_WINDOW_S)   # D-134: a new day starts a new impulse window
        self._pb_view = {"ok": False}
        self._reset_fwd()
        self.day_state = DayState(day, load_prior(day))     # D-141
        self.weather = Weather(day)                          # 7 Nov (stage 2): the photograph's histories, per day
        self.strike_lv = self._safe("strike levels", lambda: sl_mod.StrikeLevels(day, sl_mod.load_prior(day)), None)
        self._sl_last = 0.0                                  # 27 Oct: each strike's own support / resistance
        self._restore_warm(day)                  # D-120: a same-day restart keeps the regime and the price histories
        if getattr(self, "ledger", None) is not None:
            self.ledger.close()
        self.ledger = Ledger(day)                # D-070: every candidate, taken or not
        if getattr(self, "missed", None) is not None:
            self._safe("missed close", self.missed.close)
        self.missed = (missed_mod.MissedRecorder(day, config.PAPER_DIR) if missed_mod.enabled() else None)
        self.commentary = Commentary(day, paper_dir=config.PAPER_DIR, log=log)   # council 5: the live-trade commentary
        self._exit_sig, self._exit_sig_t = self._exit_signature(), None
        self._dec_cls, self._dec_n = None, 0
        self.ev("SYSTEM", f"day {day} · champion {champ} · gates {', '.join(self.gates) or 'none'} · "
                          f"capital ₹{books[champ].capital:,.0f}")

    # ── D-120 (council 4, m06/m25): warm state across a same-day restart ──────────
    # Each restart on 19 Oct rebuilt the regime (10 min WARMING, empty VWAP/percentiles) and emptied the
    # 1-Hz price histories (the 30-min trend and the 12-min spot range): with the regime gate live that
    # is 10-27 min of blindness per restart. The state is pickled every WARM_SAVE_S and restored if the
    # file is from today and younger than WARM_MAX_AGE_S. The domino's scales are deliberately NOT
    # restored (instrument ids can change on a restart); they re-learn in a few minutes.
    def _warm_path(self, day):
        return os.path.join(config.PAPER_DIR, f"warm_{day}.pkl")

    def _save_warm(self):
        import pickle
        try:
            st = {"t": self.now_s, "regime": self.regime, "fut_hist": list(self.fut_hist),
                  "spot_hist": list(self.spot_hist), "day_hi": self._day_hi, "day_lo": self._day_lo,
                  "impulse": self.impulse.dump(),
                  "fspot_hist": list(self.fspot_hist), "impulse_f": self.impulse_f.dump(),
                  "basis_f": list(self._basis_f), "basis_med": self._basis_med,
                  "day_state": self.day_state.dump() if self.day_state is not None else None}
            tmp = self._warm_path(self.day) + ".tmp"
            with open(tmp, "wb") as f:
                pickle.dump(st, f)
            os.replace(tmp, self._warm_path(self.day))
        except Exception:
            if self.now_s - getattr(self, "_warm_err", 0) > 300:
                self._warm_err = self.now_s
                log("warm state save: " + traceback.format_exc().strip().splitlines()[-1])

    def _restore_warm(self, day):
        import pickle
        path = self._warm_path(day)
        if self.mode != "live" or not os.path.exists(path):
            return
        try:
            with open(path, "rb") as f:
                st = pickle.load(f)
            age = time.time() - float(st.get("t") or 0)
            if age > getattr(config, "WARM_MAX_AGE_S", 1800):
                log(f"warm state {age:.0f} s old — not restored")
                return
            self.regime = st["regime"]
            self.regime.after_gap()              # the restart itself is a gap: its 5-min windows re-check
            self.fut_hist = deque(st.get("fut_hist") or [])
            self.spot_hist = deque(st.get("spot_hist") or [])
            if st.get("impulse"):
                self.impulse = ImpulseWindow.load(st["impulse"], config.PB_WINDOW_S)
                self._pb_view = self.impulse.view()
            if st.get("day_state") and st["day_state"].get("day") == day:
                self.day_state = DayState.load(st["day_state"])
            if st.get("impulse_f"):
                self.fspot_hist = deque(st.get("fspot_hist") or [])
                self.impulse_f = ImpulseWindow.load(st["impulse_f"], config.PB_WINDOW_S)
                self._pb_view_f = self.impulse_f.view()
                self._basis_f = deque(st.get("basis_f") or [])
                self._basis_med = st.get("basis_med")
            self._day_hi, self._day_lo = st.get("day_hi"), st.get("day_lo")
            self._hist_cols = None
            self.ev("SYSTEM", f"restart: regime and price histories restored ({age:.0f} s old)")
        except Exception:
            log("warm state restore: " + traceback.format_exc().strip().splitlines()[-1])

    def end_day(self):
        if not self.books or getattr(self, "_learned", "") == self.day:
            return
        self._learned = self.day
        paper.save_books(self.books, self.day)
        paper.write_trades_csv(self.books[self.champion], self.day)
        save_day(self.day_state)                 # D-141: tomorrow's prior-day levels
        self._safe("strike levels save", lambda: sl_mod.save_day(getattr(self, "strike_lv", None)))
        self.ledger.close()                      # unresolved candidates are written before learning reads them
        if getattr(self, "missed", None) is not None:   # 7 Nov: every missed-signal episode is written
            self._safe("missed close", self.missed.close)
        learning.record_day(self.day, self.books)   # always: the day's record must never be lost
        if learning.already_learned(self.day):
            log(f"day {self.day} was already learned — recorded, decisions not repeated")
            return
        s = learning.learn(self.day)
        self.ev("LEARN", f"{self.day}: champion next session {s['champion']}, gates "
                         f"{', '.join(s['gates']) or 'none'}, status {s.get('status')}")
        if s.get("log") and s["log"][-1].get("day") == self.day:
            audio.play("learn")
        log(f"day {self.day} closed and learned")

    def ev(self, kind, text):
        e = {"t": self.now_dt.strftime("%H:%M:%S") if hasattr(self, "now_dt") else "", "k": kind, "x": text}
        self.events.appendleft(e)
        if self.day:                             # C-34: the event tape survives a restart
            _append_jsonl(os.path.join(config.PAPER_DIR, f"events_{self.day}.jsonl"),
                          dict(e, mkt_t=getattr(self, "now_s", None)))

    # ── main step ──────────────────────────────────────────────────────────
    def step(self):
        now_ns = self.t.now_ns()
        now_s = now_ns / 1e9
        self.now_s = now_s
        self.now_dt = datetime.fromtimestamp(now_s, config.IST)
        MKT["dt"] = self.now_dt
        day = self.now_dt.date().isoformat()
        if self.day is None:
            self.start_day(day)
        elif day != self.day:
            self.end_day()
            self.start_day(day)
        elif config.hm(self.now_dt) >= config.mins(config.MARKET_CLOSE) + 1:   # D-094: F&O close 15:40
            self.end_day()

        snap = self.t.snapshot()
        dt = now_s - self.m.now if self.m.now else 0.1
        self.m.push(snap, now_s)
        if dt > 0:
            self.flow.update(self.m, dt)
        spot = self.px(self.spot_id)
        fut = self.px(self.fut_id)
        if not np.isfinite(fut):
            fut = spot
        self._spot_guard(now_s, spot, fut, snap)          # D-132: every step, before anything reads the index
        if now_s - self.last_greeks >= 0.25:
            self.last_greeks = now_s
            self.compute_greeks(spot, fut)
        if now_s - self.last_1hz >= 1.0:
            self.last_1hz = now_s
            self.iv_hist.append((now_s, self.atm_iv))
            if getattr(self, "weather", None) is not None:        # 7 Nov (stage 2): heavyweights and VIX, 1 Hz
                self._safe("weather feed", lambda: self._weather_feed(now_s, snap), None)
            if np.isfinite(spot) and in_session(self.now_dt) and self._spot_age(snap) <= config.SPOT_STALE_S:
                if self.spot_hist and now_s - self.spot_hist[-1][0] > 60:
                    self.spot_hist.clear()                        # D-124: a > 60-s hole restarts the range (no stitching)
                self.spot_hist.append((now_s, float(spot)))       # D-116: in-session 1-Hz Nifty spot (D-124: fresh only)
                self.impulse.add(now_s, float(spot))              # D-134: the 45-min impulse window (trusted spot only)
                if self.day_state is not None:                    # D-141: the day state, from the same trusted spot
                    self.day_state.add(now_s, float(spot), config.hm(self.now_dt))
                if getattr(self, "weather", None) is not None:    # 7 Nov (stage 2): the same trusted spot
                    self.weather.feed_spot(now_s, float(spot))
                self._pb_view = self.impulse.view(now_s)
                while self.spot_hist and now_s - self.spot_hist[0][0] > config.SPOT_DC_S + 5:
                    self.spot_hist.popleft()
            if np.isfinite(fut) and in_session(self.now_dt):   # D-114/D-115: 35 min of 1-Hz in-session futures (mid)
                self.fut_hist.append((now_s, float(fut)))
                while self.fut_hist and now_s - self.fut_hist[0][0] > 2100:
                    self.fut_hist.popleft()
            if self._fwd_on:
                self._safe("forward history", lambda: self._feed_fwd(now_s, spot, snap))
            self._edge = self._safe("edge snapshot", lambda: edge_mod.snapshot(self, snap, spot, fut), {})   # D-136
            if getattr(self, "quant", None) is not None and in_session(self.now_dt):   # 5 Nov: display only
                self._safe("quant view", lambda: self.quant.step(self, snap))
            self._hist_cols = None                               # T02: the 1-Hz histories changed
            self.oi_hist.append((now_s, {it["id"]: float(snap["oi"][it["id"]])
                                         for it in self.items if it["kind"] in ("opt", "fut", "sfut")}))
        self.pressure.refresh(self.t, spot)
        self.update_gex(fut)
        fid = self.fut_id if self.fut_id is not None else self.spot_id
        rn = int(snap["recv_ns"][fid]) if fid is not None else 0
        fut_age = (now_ns - rn) / 1e9 if rn else None
        fpx0 = float(snap["ltp"][fid]) if fid is not None and snap["ltp"][fid] > 0 else None
        if fpx0 and in_session(self.now_dt):
            fh = float(snap["high"][fid]) if snap["high"][fid] > 0 else fpx0
            fl = float(snap["low"][fid]) if snap["low"][fid] > 0 else fpx0
            self._day_hi = max(self._day_hi or fh, fh, fpx0)
            self._day_lo = min(self._day_lo or fl, fl, fpx0)
        step_gap = (now_s - self._last_step_s) if self._last_step_s else 0.0
        self._last_step_s = now_s
        rmax = int(snap["recv_ns"].max()) if len(snap) else 0
        feed_age = (now_ns - rmax) / 1e9 if rmax else None          # D-097: newest quote on ANY row
        self.feed_age = feed_age
        self.guard.update(now_s, int(self.t.c("feed_state")), fut_age, in_session(self.now_dt), fpx0,
                          step_gap=step_gap, feed_age_s=feed_age)
        if self.guard.on != self._gap_on:
            self._gap_on = self.guard.on
            gv = self.guard.view(now_s)
            if self.guard.on:
                self.ev("GAP", f"data gap: {gv['why']} — entries paused until {RESUME_S:.0f} s of fresh data")
            elif self.guard.gaps:
                st, en, why = self.guard.gaps[-1]
                self.ev("GAP", f"data back after {en - st:.0f} s ({why}); entries resume")
                self.regime.after_gap()          # its 5-min windows must not span the jump
        self.domino.update(self.m, now_s, learn_scales=not self.guard.on)
        try:
            dm = self.domino
            fpx = float(fut) if np.isfinite(fut) else None     # D-110: the regime reads the futures MID too
            self.regime.update(now_s, fpx, float(snap["ttq"][fid]) if fid is not None else None,
                               snap["ltp"][dm.eq_ids].astype(float) if len(dm.eq_ids) else None,
                               dm.eq_w, live=not self.guard.on, in_session=in_session(self.now_dt))
        except Exception:                        # an observer: never stops the loop
            if now_s - getattr(self, "_reg_err", 0) > 60:
                self._reg_err = now_s
                log("regime: " + traceback.format_exc().strip().splitlines()[-1])
        ep_now = self.domino.episode
        if ep_now is not None and "gap" not in ep_now:
            # D-098: decided once, at birth. An episode BORN while the guard is on (inside a gap or its
            # 20-s resume window, when a 15-s change can still span the hole) is never tradeable. One
            # that began on clean data stays tradeable after a later gap has lifted: its onset was real.
            # The old rule tainted any episode a gap touched — 52.7 % of the 19 Oct window, and the
            # 09:55 and 10:30 triggers were lost to it.
            ep_now["gap"] = bool(self.guard.on)
        dom = self.domino.state
        ep = self.domino.episode
        if ep is not None and ep.get("iv0") is None and self.atm_iv:
            ep["iv0"] = self.atm_iv
        if ep is not None and ep.get("iv0_interp") is None and self.atm_iv_interp:
            ep["iv0_interp"] = self.atm_iv_interp     # O-1 observer only: the trigger reads iv0
        K_up, K_dn = self.coherence()
        d = dom.get("dir", 1)
        self._safe("straddle", lambda: self.straddle.update(self.m, snap, self.key, getattr(self, "atm", None),
                                                            self.w0, now_s))
        try:
            self.update_watch(snap, now_s, float(fut) if np.isfinite(fut) else None)
            if (self.guard.on or self.guard.settling(now_s) > 0) and self.watch.spike:
                self.tainted_spikes.add(int(self.watch.spike["id"]))
        except Exception:                        # the watch is an observer: never let it stop the loop
            if now_s - self._watch_err > 60:
                self._watch_err = now_s
                log("straddle watch: " + traceback.format_exc().strip().splitlines()[-1])
        self._safe("bank", lambda: self.bank.update(self.m, self.bn_id, now_s, self.domino.episode_view(now_s)))
        self._safe("lag", lambda: self.lag.update(ep))
        self._safe("force", lambda: self.force.update(self.m, self.flow, self.fut_id, spot, self.pressure,
                                                      K_up if d > 0 else K_dn, now_s))
        if not np.isfinite(fut):
            return
        spot_rng = self._spot_range()
        spot_age = self._spot_age(snap)
        if spot_age is not None and spot_age > 86400 and not self._spot_bad:
            spot_age = None                                   # never received: unknown, not "a day old"
        self.ctx = ctx = {
            "now_s": now_s, "now_dt": self.now_dt, "fut": float(fut), "spot": float(spot) if (np.isfinite(spot) and not self._spot_bad) else None,
            "fut_mid": self._fut_mid(snap, fut),
            "domino": dom, "episode": self.domino.episode_view(now_s), "w0": self.w0,
            "options": self.option_rows(snap), "advisors": {}, "K_up": K_up, "K_dn": K_dn,
            "iv_rise_since_onset": (self.atm_iv - ep["iv0"]) * 100 if (ep and ep.get("iv0") and self.atm_iv) else None,
            "iv_rise_interp": ((self.atm_iv_interp - ep["iv0_interp"]) * 100     # O-1 observer, never a decision
                               if (ep and ep.get("iv0_interp") and self.atm_iv_interp) else None),
            "blackout": self.guard.view(now_s), "fut_age": fut_age, "tainted_spikes": self.tainted_spikes,
            "regime": self.regime.view(),
            "fut_r60": (float(self.m.change(self.m.ltp, 60)[fid]) if fid is not None
                        and np.isfinite(self.m.change(self.m.ltp, 60)[fid]) else None),
            "spot_hi": spot_rng[0], "spot_lo": spot_rng[1],   # D-116: previous SPOT_DC_S range
            "spot_age": spot_age,                             # D-124: seconds since the Nifty index last arrived
            "pb": self._pb_view,                              # D-134: 45-min impulse window (pullback book)
            "day": (dict(self.day_state.view(), or_done=self.day_state.or_done(now_s), t0=self.day_state.t0)
                    if self.day_state is not None else {}),     # D-141: range mode, opening range, levels
            "day_obj": self.day_state,
            "edge": getattr(self, "_edge", {}) or {},         # D-136: data snapshot (evidence, never a decision)
            "trend30": self._fut_back(now_s, 1800, fut),      # D-114: futures move over the last 30 min
            "range5": self._fut_range(now_s, 300),            # D-115: 5-min high-low
            "range15": self._fut_range(now_s, 900, full=True),   # D-121: 15-min high-low (None until 15 min held)
            "fut_ltp": float(snap["ltp"][fid]) if fid is not None else None,   # the raw last print (D-110 keeps the mid in "fut")
            "kill": self._kill_on(),             # 5 Nov: stat at most twice a second (was every step)
        }
        if self._fwd_on:
            ctx["fwd_over"] = self._safe("forward view", lambda: self._fwd_view(now_s), None)
        ctx["by_id"] = {o["id"]: o for o in ctx["options"]}
        ctx["by_key"] = {o["key"]: o for o in ctx["options"]}
        ctx["weather"] = (self._safe("weather base", lambda: self.weather.base(now_s), {})   # 7 Nov (stage 2)
                          if getattr(self, "weather", None) is not None else {})
        if self._ohist_on:
            self._safe("option history", lambda: self._feed_ohist(snap, ctx), None)
        self._safe("frozen tape", lambda: self._frozen_tape(snap), None)
        # C-07: from here on ctx exists, so nothing may stop run_books (the exits) from running
        ctx["book_state"] = self._safe("book_state", self.book_state, {})
        ctx["straddle_watch"] = self._safe("straddle watch view", lambda: self.watch.view(series=False), {})
        if getattr(self, "strike_lv", None) is not None and now_s - self._sl_last >= 1.0:
            self._sl_last = now_s
            self._safe("strike levels", lambda: self._strike_levels(ctx))
        ctx["strike_lv"] = getattr(self, "strike_lv", None)
        self._safe("straddle watch events", self._drain_watch_events)
        if ctx["episode"]:
            ctx["advisors"] = self._safe("advise", lambda: self.advise(ctx, ctx["episode"]["dir"]), {})
        self.advisors = ctx["advisors"]
        self._safe("maybe_arm", lambda: self.maybe_arm(ctx))
        self.run_books(ctx)
        try:
            self.ledger.update(ctx, self.books[self.champion], getattr(self, "last_reason", ""), ctx["regime"])
        except Exception:
            if now_s - getattr(self, "_led_err", 0) > 60:
                self._led_err = now_s
                log("ledger: " + traceback.format_exc().strip().splitlines()[-1])
        if self.eplog:
            self._safe("episode log", lambda: self.eplog.update(ctx, self))
        if self.ideas is not None:                 # 29 Oct: after the books, observers only
            self._safe("ideas", lambda: self.ideas.step(self, ctx, snap))

    def _strike_levels(self, ctx):
        """27 Oct: feed every fresh option print to the per-strike levels; tape the breaks of near-ATM strikes and of
        any contract a book holds. Evidence only."""
        if not in_session(self.now_dt):
            return
        now_s, hm, sp = ctx["now_s"], config.hm(self.now_dt), ctx.get("spot")
        held = {}
        for name, b in (self.books or {}).items():
            if b.pos:
                held.setdefault(b.pos["key"], []).append(b)
        for o in ctx["options"]:
            if not o.get("ltp") or o.get("age", 9e9) > 5.0:
                continue
            for e in self.strike_lv.add(now_s, o["key"], float(o["ltp"]), hm):
                rec = dict(e, time=self.now_dt.strftime("%H:%M:%S"), strike=o.get("strike"), rr=o.get("rr"))
                if (sp and abs(float(o["strike"]) - sp) <= 150) or o["key"] in held:
                    _append_jsonl(os.path.join(config.PAPER_DIR, f"strikes_{self.day}.jsonl"), rec)
                for b in held.get(o["key"], []):
                    br = b.pos.setdefault("sr_breaks", [])
                    if len(br) < 12:
                        br.append([rec["time"], e["dir"], e["label"], e["level"]])

    def _drain_watch_events(self):
        for kind, text in self.watch.drain_events():
            self.ev(kind, text)                  # 2 Nov: tape only — a spike is not a trade, so no sound

    def book_state(self):
        """Opposing-side classes for every hero contract (used by the book exit and the book advisor).
        C-12: we only BUY, and a bought contract profits when its own price rises, so the opposing
        side is always the asks: Flow.side(i, +1) for CE and PE alike."""
        out = {}
        for i, rr, _ in self.heroes():
            cq, co, imb = self.flow.side(i, +1)
            out[i] = {"opp_q": cq, "opp_o": co, "imb": imb, "lead": float(self.flow.lead[i]), "side_fix": 1}
        return out

    def maybe_arm(self, ctx):
        """The 'look up' chime: every corner of the Triangle past 80 %, once per episode."""
        ep, dom = ctx.get("episode"), ctx.get("domino") or {}
        champ = self.books.get(self.champion)
        if not ep or not champ or champ.pos or ep["id"] == getattr(self, "armed_ep", None):
            return
        if champ.p.get("spot_dc") or champ.p.get("fade_switch"):
            return                                   # D-124: the Triangle is the domino books' setup, not this champion's
        hmn = config.hm(ctx["now_dt"])
        if hmn < config.mins(config.SUPPRESS_UNTIL) or hmn >= config.mins(config.LAST_ENTRY):
            return                                  # the trigger itself can't fire here either
        d = ep["dir"]
        push = (dom.get("z", 0.0) * d) / champ.p["m_star"]
        crowd = (dom.get("S_up", 0.0) if d > 0 else dom.get("S_dn", 0.0)) / champ.p["s_star"]
        late = self.lateness(ctx)
        if push >= 0.8 and crowd >= 0.8 and late is not None and late < 0.8:
            self.armed_ep = ep["id"]             # 2 Nov: tape only — arming is not a trade, so no sound
            self.ev("ARMED", f"Triangle closing: push {push:.0%}, together {crowd:.0%}, "
                             f"{(1 - late):.0%} room left — {'CE' if d > 0 else 'PE'} side")

    def px(self, i):
        if i is None:
            return np.nan
        return float(self.m.ltp[i, self.m.k])

    # ── Greeks ─────────────────────────────────────────────────────────────
    def _greek_plan(self):
        """Per-registry cache of the option rows by expiry (ids, strikes, rights) — the same lists
        compute_greeks built on every call. Rebuilt when the registry version changes."""
        key = (self.reg_version, self.w0, self.w1, id(self.opts))
        plan = getattr(self, "_gplan", None)
        if plan is not None and plan["key"] == key:
            return plan
        plan = {"key": key, "exps": []}
        for exp in (self.w0, self.w1):
            rows = [it for it in self.opts if it["expiry"] == exp]
            if not rows:
                continue
            ids = np.array([it["id"] for it in rows])
            K = np.array([it["strike"] for it in rows])
            is_call = np.array([it["right"] == "call" for it in rows])
            strikes = sorted(set(K))
            # one CE and one PE row per strike (the registry keys are unique): the per-strike nanmean of a
            # single value is that value, so the mean step reduces to a gather (fallback below if not unique)
            unique = len({(float(k), bool(c)) for k, c in zip(K, is_call)}) == len(K)
            pos = {(float(k), bool(c)): j for j, (k, c) in enumerate(zip(K, is_call))}
            ce_j = np.array([pos.get((float(k), True), -1) for k in strikes])
            pe_j = np.array([pos.get((float(k), False), -1) for k in strikes])
            plan["exps"].append({"exp": exp, "ids": ids, "K": K, "is_call": is_call, "strikes": strikes,
                                 "unique": unique, "ce_j": ce_j, "pe_j": pe_j, "ids_int": [int(i) for i in ids]})
        self._gplan = plan
        return plan

    def compute_greeks(self, spot, fut):
        self.atm_iv = getattr(self, "atm_iv", None)
        ref = spot if np.isfinite(spot) else fut
        if not np.isfinite(ref):
            return
        snap = self.m.snap
        now_ns = self.t.now_ns()
        parts = []
        for ex in self._greek_plan()["exps"]:
            exp, ids, K, is_call, strikes = ex["exp"], ex["ids"], ex["K"], ex["is_call"], ex["strikes"]
            bid, ask, ltp = snap["bid"][ids], snap["ask"][ids], snap["ltp"][ids]
            mid = np.where((bid > 0) & (ask > 0) & (ask >= bid), (bid + ask) / 2, ltp)
            # D-102: a leg whose quote has not updated for IV_LEG_MAX_AGE_S is left out of the forward
            # and IV. On 19 Oct the frozen call legs pushed the parity forward +29 pts (up to +112,
            # inside the 150-pt sanity bound) and ATM IV +6 vol pts (up to +18) for 95 minutes.
            rn = snap["recv_ns"][ids].astype(np.int64)
            fresh = (rn > 0) & ((now_ns - rn) / 1e9 <= config.IV_LEG_MAX_AGE_S)
            mid = np.where((mid > 0) & fresh, mid, np.nan)
            if ex["unique"]:
                ce = np.where(ex["ce_j"] >= 0, mid[ex["ce_j"]], np.nan)
                pe = np.where(ex["pe_j"] >= 0, mid[ex["pe_j"]], np.nan)
            else:
                ce = [np.nanmean(mid[(K == k) & is_call]) if ((K == k) & is_call).any() else np.nan for k in strikes]
                pe = [np.nanmean(mid[(K == k) & ~is_call]) if ((K == k) & ~is_call).any() else np.nan for k in strikes]
            F = greeks.synthetic_forward(strikes, ce, pe, ref)
            T = greeks.years_to_expiry(exp, self.now_dt)
            parts.append((ex, mid, F, T))
        if not parts:
            return
        # one IV solve and one Greeks pass for both expiries (per-row F and T; elementwise, so identical)
        mid_all = np.concatenate([p[1] for p in parts])
        K_all = np.concatenate([p[0]["K"] for p in parts]).astype(float)
        call_all = np.concatenate([p[0]["is_call"] for p in parts])
        F_all = np.concatenate([np.full(len(p[1]), float(p[2])) for p in parts])
        T_all = np.concatenate([np.full(len(p[1]), float(p[3])) for p in parts])
        iv_all = greeks.implied_vol(mid_all, F_all, K_all, T_all, call_all)
        g = greeks.greeks(F_all, K_all, T_all, iv_all, call_all)
        ivl, dl, tl, vl, gl = (iv_all * 100).tolist(), g["delta"].tolist(), g["theta_min"].tolist(), g["vega"].tolist(), g["gamma"].tolist()
        isf, rnd = math.isfinite, round
        greek = self.greek
        j0 = 0
        for ex, mid, F, T in parts:
            n = len(mid)
            for j, i in enumerate(ex["ids_int"], j0):
                g_new = {"iv": rnd(ivl[j], 2) if isf(ivl[j]) else None,
                         "delta": rnd(dl[j], 3) if isf(dl[j]) else None,
                         "theta_min": rnd(tl[j], 4) if isf(tl[j]) else None,
                         "vega": rnd(vl[j], 2) if isf(vl[j]) else None,
                         "gamma": rnd(gl[j], 5) if isf(gl[j]) else None}
                if greek.get(i) != g_new:           # T02: same values -> same dict object (option_rows cache key)
                    greek[i] = g_new
            if ex["exp"] == self.w0:
                K, strikes = ex["K"], ex["strikes"]
                iv = iv_all[j0:j0 + n]
                atm = min(strikes, key=lambda k: abs(k - F))
                sel = (K == atm)
                v = iv[sel]
                v = v[np.isfinite(v)]
                self.atm_iv = float(v.mean()) if v.size else self.atm_iv
                self.fwd = F
                self._fwd_t = self.now_s
                self.atm = atm
                # O-1 observer: IV at F, linear in strike between the bracketing strikes (CE/PE mean)
                cj, pj = (ex["ce_j"], ex["pe_j"]) if ex["unique"] else (None, None)
                self.atm_iv_interp = self._safe(
                    "atm iv interp", lambda: _interp_atm_iv(strikes, K, iv, F, cj, pj), None) or self.atm_iv_interp
            j0 += n

    def data_health(self, snap):
        """D-103 (council m28): what the eye cannot see on the board. The 19 Oct freeze showed call
        prices updating 0 % of the time while every age on the page read < 2 s. Exchange-stamp based:
          ce_live / pe_live : share of this week's options whose last trade is < 60 s old (in session)
          frozen            : hero contracts whose exchange stamp is > 300 s old (name + minutes)
          lag_s             : receive time minus exchange time on the Nifty index (feed delivery lag)."""
        now = self.now_s
        out = {"ce_live": None, "pe_live": None, "frozen": [], "lag_s": None,
               "feed_sync": int(self.t.c("feed_sync"))}       # 7 Nov (review 4.1): 1 / -1 / 0, see table.CTRL_DTYPE
        if self.spot_id is not None:
            lt, rn = float(snap["ltt"][self.spot_id]), int(snap["recv_ns"][self.spot_id])
            if lt > 1e9 and rn > 0:
                out["lag_s"] = round(rn / 1e9 - lt, 1)
        if not in_session(self.now_dt):
            return out
        live = {"CE": [0, 0], "PE": [0, 0]}
        for it in self.opts:
            if it["expiry"] != self.w0 or it.get("rr") not in live:
                continue
            lt = float(snap["ltt"][it["id"]])
            c = live[it["rr"]]
            c[1] += 1
            if lt > 1e9 and now - lt < 60:
                c[0] += 1
        out["ce_live"] = round(live["CE"][0] / live["CE"][1], 2) if live["CE"][1] else None
        out["pe_live"] = round(live["PE"][0] / live["PE"][1], 2) if live["PE"][1] else None
        for i, rr, k in self.heroes():
            lt = float(snap["ltt"][i])
            if lt > 1e9 and now - lt > config.HERO_FROZEN_S:
                out["frozen"].append(f"{int(k)} {rr} {int((now - lt) // 60)} min")
        return out

    def _weather_feed(self, now_s, snap):
        """Stage 2: the heavyweights' last prices and VIX (with its own arrival stamp) into the photograph's histories."""
        dm = self.domino
        if dm is not None and len(dm.eq_ids):
            self.weather.feed_hw(now_s, snap["ltp"][dm.eq_ids].astype(float), dm.eq_w)
        self.weather.feed_vix(float(self.t.c("vix")), int(self.t.c("vix_ns")))

    def _frozen_tape(self, snap):
        """D-103 on the event tape. 7 Nov (review 4.1): run once per MARKET second from step(), not from publish()
        (wall-clock 4 Hz live, market time in a replay), so the DATA lines are the same in live and in a replay."""
        now = self.now_s
        if now - getattr(self, "_frozen_t", -1e18) < 1.0:
            return
        self._frozen_t = now
        names = set()
        if in_session(self.now_dt):
            for i, rr, k in self.heroes():
                lt = float(snap["ltt"][i])
                if lt > 1e9 and now - lt > config.HERO_FROZEN_S:
                    names.add(f"{int(k)} {rr}")
        new = names - getattr(self, "_frozen_prev", set())
        if new:
            self.ev("DATA", "no trade for %d s on hero contract(s): %s" % (config.HERO_FROZEN_S, ", ".join(sorted(new))))
        self._frozen_prev = names

    def _spot_guard(self, now_s, spot, fut, snap):
        """D-132 (council 6 M10): the vendor index freezes ~15:15 and then prints garbage (+501 pts on 19 and 21 Oct) while its
        receive time stays fresh. Two plain sanity tests, in session only, on EVERY step (a wild print must not reach an
        exit or a range for even one second); the 30-min reference spread is refreshed once a second. Sets self._spot_bad
        to a reason ("" = trusted); _spot_age then reads 9e9, so every existing safety net applies: no spot entry, spot not
        added to the range history, and an open position falls back to the futures-mid stop at spot_trail points."""
        bad = ""
        try:
            if np.isfinite(spot) and np.isfinite(fut) and in_session(self.now_dt):
                sec = int(now_s)
                bh = self._basis_hist
                if sec != getattr(self, "_basis_sec", None):          # once a second: age the window, refresh the reference
                    self._basis_sec = sec
                    while bh and now_s - bh[0][0] > 1800:
                        bh.popleft()
                    self._basis_ref = (sorted(b for _, b in bh)[len(bh) // 2] if len(bh) >= 60 else config.SPOT_BASIS_REF)
                    self._basis_due = True
                ref = getattr(self, "_basis_ref", config.SPOT_BASIS_REF)
                basis = float(fut) - float(spot)
                c = self._sp_chg
                if c is None or float(spot) != c[1]:
                    self._sp_chg = c = (now_s, float(spot), float(fut))
                if abs(basis - ref) > config.SPOT_BASIS_MAX:
                    bad = f"spot {float(spot):.1f} is {basis - ref:+.0f} pts off its usual spread to the future"
                elif now_s - c[0] >= config.SPOT_FLAT_S and abs(float(fut) - c[2]) >= config.SPOT_FLAT_FUT_PTS:
                    bad = f"spot unchanged for {now_s - c[0]:.0f} s while the future moved {float(fut) - c[2]:+.0f}"
                elif getattr(self, "_basis_due", False):
                    self._basis_due = False
                    bh.append((now_s, basis))
        except Exception:
            bad = ""
        if bad and not self._spot_bad:
            self.ev("DATA", "NIFTY index not trusted: " + bad)
        elif self._spot_bad and not bad:
            self.ev("DATA", "NIFTY index trusted again")
        self._spot_bad = bad

    def _spot_age(self, snap):
        """D-124: seconds since the Nifty index row was last written by the feed (None without a spot row).
        D-132: 9e9 while the print itself is not trusted (see _spot_guard)."""
        if self.spot_id is None:
            return None
        if self._spot_bad:
            return 9e9
        rn = int(snap["recv_ns"][self.spot_id])
        return (self.now_s - rn / 1e9) if rn > 0 else 9e9

    _hist_cols = None

    def _hist(self):
        """T02: (spot_t, spot_px, fut_t, fut_px) as lists, rebuilt only when the 1-Hz histories change
        (once a second); the window scans below become bisections on the sorted time lists."""
        sh, fh = self.spot_hist, self.fut_hist
        key = (len(sh), sh[0][0] if sh else None, sh[-1][0] if sh else None,
               len(fh), fh[0][0] if fh else None, fh[-1][0] if fh else None)
        c = self._hist_cols
        if c is None or c[0] != key:
            c = self._hist_cols = (key, [t for t, _ in sh], [px for _, px in sh], [t for t, _ in fh], [px for _, px in fh])
        return c[1:]

    # ── 29 Oct midday: the put-call-parity forward as a second "spot" (shadow books with spot_src="fwd") ──
    def _reset_fwd(self):
        self.fspot_hist = deque()                 # (t, spot-unit forward) at 1 Hz, in session
        self.impulse_f = ImpulseWindow(config.PB_WINDOW_S)
        self._pb_view_f = {"ok": False}
        self._basis_f = deque()                   # (t, forward - spot) while spot is trusted, 30 min
        self._basis_med = None

    def _fwd_fresh(self, now_s):
        F = getattr(self, "fwd", None)
        return (F is not None and np.isfinite(F) and self._fwd_t is not None and now_s - self._fwd_t <= 2.0)

    def _feed_fwd(self, now_s, spot, snap):
        if not in_session(self.now_dt) or not self._fwd_fresh(now_s):
            return
        F = float(self.fwd)
        sa = self._spot_age(snap)
        if np.isfinite(spot) and not self._spot_bad and sa is not None and sa <= config.SPOT_STALE_S:
            self._basis_f.append((now_s, F - float(spot)))
            while self._basis_f and now_s - self._basis_f[0][0] > 1800:
                self._basis_f.popleft()
            if len(self._basis_f) >= 30:
                self._basis_med = float(np.median([b for _, b in self._basis_f]))
        if self._basis_med is None:
            return
        fa = F - self._basis_med
        h = self.fspot_hist
        if h and now_s - h[-1][0] > 60:
            h.clear()                                 # as D-124: a > 60-s hole restarts the range
        h.append((now_s, fa))
        while h and now_s - h[0][0] > config.SPOT_DC_S + 5:
            h.popleft()
        self.impulse_f.add(now_s, fa)
        self._pb_view_f = self.impulse_f.view(now_s)

    def _fwd_view(self, now_s):
        """The ctx keys a spot book reads, rebuilt on the forward. None until the forward and its gap are known."""
        if self._basis_med is None or not self._fwd_fresh(now_s):
            return {"spot": None, "spot_hi": None, "spot_lo": None, "spot_age": None, "pb": {"ok": False}}
        h = self.fspot_hist
        hi = lo = None
        if h and h[-1][0] - h[0][0] >= config.SPOT_DC_S - 5:
            xs = [px for t, px in h if now_s - config.SPOT_DC_S <= t < now_s - 0.5]
            if len(xs) >= 0.8 * config.SPOT_DC_S:
                hi, lo = max(xs), min(xs)
        return {"spot": float(self.fwd) - self._basis_med, "spot_hi": hi, "spot_lo": lo,
                "spot_age": now_s - self._fwd_t, "pb": self._pb_view_f}

    def _spot_range(self):
        """D-116: (high, low) of Nifty spot over the previous SPOT_DC_S seconds, excluding the current second,
        in session only; (None, None) until the window is ~full (first signal possible ~09:27)."""
        h = self.spot_hist
        if not h or h[-1][0] - h[0][0] < config.SPOT_DC_S - 5:
            return None, None
        now_s = self.now_s
        st, sp, _, _ = self._hist()
        xs = sp[bisect.bisect_left(st, now_s - config.SPOT_DC_S):bisect.bisect_left(st, now_s - 0.5)]
        # D-124 (review): the window must be COVERED, not just spanned — after an index stall or a restart hole a
        # handful of samples spread over 12 min is not a 12-minute range
        if len(xs) < 0.8 * config.SPOT_DC_S:
            return None, None
        return (max(xs), min(xs))

    def _fut_back(self, now_s, secs, fut):
        """Futures move over the last `secs` seconds from the 1-Hz history, or None while short."""
        if not self.fut_hist or not np.isfinite(fut):
            return None
        t0 = now_s - secs
        _, _, ft, fp = self._hist()
        j = bisect.bisect_left(ft, t0)                     # first sample with t >= t0
        old = fp[j] if j < len(fp) else None
        if old is None or now_s - self.fut_hist[0][0] < secs * 0.9:
            return None
        return float(fut) - old

    def _fut_range(self, now_s, secs, full=False):
        if full and (not self.fut_hist or now_s - self.fut_hist[0][0] < secs * 0.9):
            return None
        _, _, ft, fp = self._hist()
        xs = fp[bisect.bisect_left(ft, now_s - secs):]
        return (max(xs) - min(xs)) if len(xs) >= 10 else None

    def _fut_mid(self, snap, fut):
        """D-109 (owner, 19 Oct 13:14): the Nifty-future bid/ask midpoint, used by every exit instead of
        the last print (spread 4-10 pts against a 12-pt stop: 29 of 34 morning exits fired on a print
        the mid had not crossed). Falls back to the last price when the quote is one-sided or wide."""
        fid = self.fut_id
        if fid is None:
            return None
        b, a = float(snap["bid"][fid]), float(snap["ask"][fid])
        if b > 0 and a >= b and (a - b) <= config.FUT_MID_MAX_SPREAD:
            return (a + b) / 2.0
        return float(fut) if np.isfinite(fut) else None

    def _session_open_epoch(self):
        """Epoch seconds of today's pre-open start (09:00 IST): a last-trade stamp before it is from
        an earlier session."""
        d = self.now_dt
        return d.replace(hour=9, minute=0, second=0, microsecond=0).timestamp()

    def option_rows(self, snap):
        """One dict per option. "ltt" (exchange last-trade time, epoch s, or None) is the O-7 observer
        input that paper.py uses for trade age; nothing here decides on it.
        (T02: the per-row values are gathered once as Python floats; the session-open epoch and the
        clock are computed once per call instead of once per row. Same dicts, same values.)"""
        now_ns = self.t.now_ns()
        opts = self.opts
        if not opts:
            return []
        plan = getattr(self, "_oplan", None)
        if plan is None or plan[0] is not opts:
            plan = (opts, np.array([it["id"] for it in opts]))
            self._oplan = plan
        ids = plan[1]
        ltp_l = snap["ltp"][ids].tolist()
        rn_l = snap["recv_ns"][ids].tolist()
        ltt_l = snap["ltt"][ids].tolist()
        bid_l = snap["bid"][ids].tolist()
        ask_l = snap["ask"][ids].tolist()
        open_epoch = self._session_open_epoch()
        greek = self.greek
        isf, rnd = math.isfinite, round
        cache = getattr(self, "_ocache", None)
        if cache is None or cache[0] is not opts:
            cache = self._ocache = (opts, {})
        rows = cache[1]
        out = []
        for j, it in enumerate(opts):
            i = it["id"]
            g = greek.get(i, {})
            rn = rn_l[j]
            b, a = bid_l[j], ask_l[j]
            ltp = ltp_l[j]
            ltt = ltt_l[j]
            age = (now_ns - rn) / 1e9 if rn else 9e9
            ck = (rn, id(g), ltp, ltt, b, a)
            c = rows.get(i)
            if c is not None and c[0] == ck:
                d = c[1].copy()                      # the row is unchanged: only its age moves
                d["age"] = age if c[2] else 9e9
                out.append(d)
                continue
            ltt = ltt if (isf(ltt) and ltt > 0) else None
            today = not (ltt is not None and ltt < open_epoch)
            if not today:
                # D-102: no trade on this contract today — its last price is a previous session's.
                # It cannot be bought or sold at that price, so every freshness gate treats it as stale.
                age = 9e9
            d = {"id": i, "key": it["key"], "strike": it["strike"], "rr": it.get("rr"),
                 "week": it.get("week", 0), "expiry": it["expiry"],
                 "ltp": ltp if ltp > 0 else None,
                 "bid": rnd(b, 2) if isf(b) else None, "ask": rnd(a, 2) if isf(a) else None,
                 "delta": g.get("delta"), "iv": g.get("iv"),
                 "gamma": g.get("gamma"), "theta_min": g.get("theta_min"),   # 27 Oct: buyer-edge gate (paper.py)
                 "age": age, "ltt": ltt}
            rows[i] = (ck, d, today)
            out.append(d.copy())
        return out

    # ── coherence across the ten hero contracts ────────────────────────────
    def heroes(self):
        atm = getattr(self, "atm", None)
        if atm is None:
            return []
        hs = []
        for k in range(-config.HERO_BAND, config.HERO_BAND + 1):
            for rr in ("CE", "PE"):
                i = self.key.get(f"NIFTY|OPT|{self.w0}|{int(atm + k * config.STRIKE_STEP)}|{rr}")
                if i is not None:
                    hs.append((i, rr, atm + k * config.STRIKE_STEP))
        return hs

    def coherence(self):
        hs = self.heroes()
        if not hs:
            return 0.0, 0.0
        chg5 = self.m.change(self.m.ltp, 5)              # T02: once per step, not once per hero and side
        up = [self.flow.run_score(i, 1 if rr == "CE" else -1, self.m, chg5) for i, rr, _ in hs]
        dn = [self.flow.run_score(i, -1 if rr == "CE" else 1, self.m, chg5) for i, rr, _ in hs]
        return (float(np.mean([x >= 0.3 for x in up])), float(np.mean([x >= 0.3 for x in dn])))

    # ── advisors: would-have verdicts (D-033) ──────────────────────────────
    def advise(self, ctx, d):
        """Every advisor runs through _safe (C-07): a fault yields a non-veto marked "faulted"."""
        a = {}
        F = lambda name: {"veto": False, "why": "advisor faulted", "faulted": True}   # noqa: E731

        def iv_late():
            iv5 = self.iv_change(300)
            return {"veto": bool(iv5 is not None and self.atm_iv and iv5 >= 0.08 * self.atm_iv * 100),
                    "why": f"ATM IV {iv5:+.2f} pts in 5 min" if iv5 is not None else "IV history warming"}
        a["iv_late"] = self._safe("advisor iv_late", iv_late, F("iv_late"))
        opt, _ = self._safe("advisor contract", lambda: paper.choose_contract(ctx, d), (None, "faulted"))

        def room():
            dest = self.pressure.destination(ctx["spot"] or ctx["fut"], d)
            need = None
            if opt and opt.get("delta"):
                th = abs((self.greek.get(opt["id"], {}) or {}).get("theta_min") or 0.0)
                need = (12.0 + th * 5) / max(abs(opt["delta"]), 0.05)
            return {"veto": bool(dest and need and dest["room"] < 1.3 * need),
                    "why": (f"next wall {dest['level']:.0f} is {dest['room']:.0f} pts away, need ~{need:.0f}"
                            if dest and need else "no wall data")}
        a["room"] = self._safe("advisor room", room, F("room"))

        def coherence():
            K = ctx["K_up"] if d > 0 else ctx["K_dn"]
            return {"veto": K < 0.5, "why": f"{K:.0%} of hero contracts confirm"}
        a["coherence"] = self._safe("advisor coherence", coherence, F("coherence"))

        def force():
            fv = self.force.view()
            return {"veto": bool(fv.get("dir") == d and fv["verdict"] == "HOLD-STRONG"),
                    "why": f"futures level {fv.get('name', '—')}: {fv['verdict']}"}
        a["force"] = self._safe("advisor force", force, F("force"))

        def episode():
            et = ctx["episode"]["type"]
            return {"veto": et in ("FUTURES-LED", "SINGLE-NAME"), "why": f"episode {et}"}
        a["episode"] = self._safe("advisor episode", episode, F("episode"))

        # book: on the contract we would buy, are the opposing orders refilling or is the book against us?
        def book():
            if not opt:
                return {"veto": False, "why": "no contract in band"}
            bk = ctx["book_state"].get(opt["id"]) or {}
            refill = bk.get("opp_q") == REFILL or bk.get("opp_o") == REFILL
            against = bk.get("imb", 0.0) < -0.3
            return {"veto": bool(refill or against),
                    "why": (f"{opt['strike']:.0f} {opt['rr']}: sellers qty {CLS[bk.get('opp_q', 0)]}, "
                            f"orders {CLS[bk.get('opp_o', 0)]}, order imbalance {bk.get('imb', 0.0):+.2f}, "
                            f"book leads price {bk.get('lead', 0.0):+.2f}")}
        a["book"] = self._safe("advisor book", book, F("book"))

        def premium():
            sv = self.straddle.view()
            return {"veto": self.straddle.veto(),
                    "why": (f"ATM straddle {sv['px']:.1f} vs VWAP {sv['vwap']:.1f}: {sv['state']}"
                            if sv["vwap"] else "straddle VWAP warming")}
        a["premium"] = self._safe("advisor premium", premium, F("premium"))

        def quiet():
            sv = self.straddle.view()
            sig = (self.domino.state or {}).get("sigma15") or 0.0
            return {"veto": bool(sig and sig < 2.5 and self.straddle.veto()),
                    "why": f"σ15 {sig:.1f} pts, premium {sv['state'].lower()}"}
        a["quiet"] = self._safe("advisor quiet", quiet, F("quiet"))
        a["bank"] = self._safe("advisor bank", lambda: {"veto": self.bank.veto(d),
                                                         "why": f"Bank Nifty futures z {self.bank.z:+.1f}"}, F("bank"))

        def event():
            evt = event_today(self.day)
            return {"veto": bool(evt), "why": evt or "no event today"}
        a["event"] = self._safe("advisor event", event, F("event"))

        def gamma_leg():
            gv, gw = self.watch.advise(d)
            return {"veto": bool(gv), "why": gw}
        a["gamma_leg"] = self._safe("advisor gamma_leg", gamma_leg, F("gamma_leg"))

        def gex_room():
            # C-14: the gamma map is built at the w0 forward, so measure the walls from it, not the monthly future
            xv, xw = self.gex.advise(d, getattr(self, "fwd", None) or ctx["fut"])
            return {"veto": bool(xv), "why": xw}
        a["gex_room"] = self._safe("advisor gex_room", gex_room, F("gex_room"))

        def regime():
            rv, rw = self.regime.advise(d)
            return {"veto": bool(rv), "why": rw}
        a["regime"] = self._safe("advisor regime", regime, F("regime"))
        return a

    # ── dealer gamma map (D-062): an observer, never allowed to stop the loop ──
    def update_gex(self, fut):
        try:
            atm_iv = getattr(self, "atm_iv", None)
            if not self.pressure.oi or not self.pressure.expiry or not atm_iv or not getattr(self, "opts", None):
                return
            F = getattr(self, "fwd", None) or (float(fut) if np.isfinite(fut) else None)
            iv_k = {}
            if self.gex.needs(self.pressure.version, F):     # T02: the map is keyed on (chain, F/10); the
                for it in self.opts:                         # IV dict is only read when it is recomputed
                    if it["expiry"] != self.w0:
                        continue
                    v = (self.greek.get(it["id"]) or {}).get("iv")
                    if v:
                        iv_k.setdefault(float(it["strike"]), []).append(v / 100.0)
                iv_k = {k: float(np.mean(v)) for k, v in iv_k.items()}
            self.gex.update(self.pressure.version, self.pressure.oi, self.pressure.expiry,
                            self.now_dt, F, iv_k, atm_iv)
        except Exception:
            if time.time() - getattr(self, "_gex_err", 0) > 60:
                self._gex_err = time.time()
                log("gex map: " + traceback.format_exc().strip().splitlines()[-1])

    # ── the fixed-strike straddle watch ────────────────────────────────────
    def _leg_quotes(self, snap, k):
        """(quote, greeks, ids) for strike k's CE and PE, or (None, None, None) if either is missing."""
        quote, g, ids = {}, {}, []
        for rr in ("CE", "PE"):
            i = self.key.get(f"NIFTY|OPT|{self.w0}|{int(k)}|{rr}")
            if i is None:
                return None, None, None
            quote[rr] = (float(snap["ltp"][i]), float(snap["bid"][i]), float(snap["ask"][i]))
            g[rr] = self.greek.get(i, {})
            ids.append(i)
        return quote, g, ids

    def update_watch(self, snap, now_s, fut):
        atm = getattr(self, "atm", None)
        if atm is None or not self.w0:
            return
        w = self.watch
        roll = w.wants_roll()
        if roll is not None:
            quote, _, _ = self._leg_quotes(snap, roll)
            if quote:
                w.roll(now_s, self.now_dt, roll, quote)
            else:
                w._roll_to = None
        K = w.K if w.K is not None else atm
        quote, g, ids = self._leg_quotes(snap, K)
        if quote is None:
            return
        vol = 0.0
        if self.m.prev_snap is not None:
            for i in ids:
                dv = float(snap["ttq"][i]) - float(self.m.prev_snap["ttq"][i])
                if dv == dv and dv > 0:
                    vol += dv
        w.update(now_s, self.now_dt, atm, quote, g, fut, vol)

    def fut_book(self):
        i = self.fut_id
        if i is None:
            return None
        f = self.flow
        return {"imb_q": fnum(f.imb_q[i], 2), "imb_o": fnum(f.imb_o[i], 2), "imb_t": fnum(f.imb_t[i], 2),
                "imb_t_chg": fnum(f.imb_t_chg[i], 2), "lead": fnum(f.lead[i], 2),
                "bid_cls": CLS[int(f.cls_b[i])], "ask_cls": CLS[int(f.cls_s[i])],
                "bid_ord_cls": CLS[int(f.cls_bo[i])], "ask_ord_cls": CLS[int(f.cls_so[i])],
                "sbo": fnum(self.m.sbo[i, self.m.k], 0), "sso": fnum(self.m.sso[i, self.m.k], 0)}

    def lateness(self, ctx):
        """Fraction of the not-late allowance already used (0 fresh .. 1 late) for the champion."""
        ep = self.domino.episode if self.domino else None
        champ = self.books.get(getattr(self, "champion", ""), None)
        if not ep or not champ or not ctx.get("fut"):
            return None
        sig = (self.domino.state or {}).get("sigma15") or 1.0
        used = abs(ctx["fut"] - ep["fut0"]) / max(champ.p["L_star"] * sig, 1e-6)
        ivr = ctx.get("iv_rise_since_onset")
        if ivr is not None:
            used = max(used, ivr / config.IV_RISE_CAP)
        return round(float(min(max(used, 0.0), 2.0)), 3)

    def iv_change(self, secs):
        if not self.iv_hist or not self.atm_iv:
            return None
        target = self.now_s - secs
        for t, v in reversed(self.iv_hist):               # T02: the LAST entry at or before target with a value
            if t <= target and v:
                return (self.atm_iv - v) * 100
        return None

    # ── books ──────────────────────────────────────────────────────────────
    def run_books(self, ctx):
        changed = False
        fctx = None
        for name, b in self.books.items():
            bctx = ctx
            if b.p.get("spot_src") == "fwd":           # 29 Oct midday: this shadow reads the forward as its spot
                if fctx is None:
                    fo = ctx.get("fwd_over") or {"spot": None, "spot_hi": None, "spot_lo": None, "spot_age": None,
                                                 "pb": {"ok": False}}
                    fctx = dict(ctx, **fo)
                bctx = fctx
            if b.p.get("council"):                     # 30 Oct (D-145): council strategy books (apex/engine/council)
                try:
                    changed = self._council(name, b, bctx) or changed
                except Exception:
                    self._fault(f"council {name}")
                if self.missed is not None:          # 7 Nov: observer only (docs/29)
                    ad = (getattr(self, "_council_ad", None) or {}).get(name)
                    if ad is not None:
                        self._safe("missed council", lambda: self.missed.step_council(self, name, ad, b, bctx))
                continue
            try:                                       # C-07: one book's fault must not skip the others' exits
                t = paper.check_exit(b, bctx)
            except Exception:
                self._fault(f"exit {name}")
                continue                               # no entry decision on a book whose exit check faulted
            if t:
                changed = True
                if name == self.champion:
                    audio.play("win" if t["pnl_pts"] > 0 else "loss")
                if name in (self.champion, "RAW"):
                    tag = "EXIT" if name == self.champion else "RAW-EXIT"
                    self.ev(tag, f"{t['rr']} {t['strike']:.0f} {t['lots']} lots · {t['entry']:.2f} → {t['exit']:.2f} "
                                 f"= {t['pnl_pts']:+.2f} pts / ₹{t['pnl_rs']:+,.0f} · {t['reason']} · capital ₹{b.capital:,.0f}")
            try:
                changed = self._entry(name, b, bctx) or changed
            except Exception:
                self._fault(f"entry {name}")
            if self.missed is not None:              # 7 Nov: observer only (docs/29)
                self._safe("missed paper", lambda: self.missed.step_paper(self, name, b, bctx))
        if self.missed is not None:
            self._safe("missed advance", lambda: self.missed.advance(self, ctx))
        sig = self._exit_signature()
        if changed:
            paper.save_books(self.books, self.day)
            self._exit_sig, self._exit_sig_t = sig, ctx["now_s"]
        elif sig != self._exit_sig and (self._exit_sig_t is None or ctx["now_s"] - self._exit_sig_t >= 1.0) \
                and not config.REPLAY_FAST:
            # C-11: an armed trail, a new best or a committed exit must survive a restart (≤ 1 save/s).
            # T02: not in a --fast replay (never restarted; the books are saved on every trade and at the stop)
            if self._safe("save exit state", lambda: paper.save_books(self.books, self.day) or True, False):
                self._exit_sig, self._exit_sig_t = sig, ctx["now_s"]
        self._safe("decision tape", lambda: self._tape_decision(ctx))
        if getattr(self, "commentary", None) is not None:
            self._safe("commentary", lambda: self.commentary.update(ctx, self))   # observer: never a decision

    def _feed_ohist(self, snap, ctx):
        """1 Hz (t, iv, tbq) per option row for paper.flow_veto; 16 min kept."""
        now = ctx["now_s"]
        if now - self._ohist_t >= 1.0:
            self._ohist_t = now
            tbq = snap["tbq"]
            for o in ctx["options"]:
                i = o["id"]
                q = float(tbq[i]) if tbq is not None else float("nan")
                h = self._ohist.get(i)
                if h is None:
                    h = self._ohist[i] = deque(maxlen=1000)
                b_, a_ = o.get("bid"), o.get("ask")
                mid = (b_ + a_) / 2.0 if (b_ and a_ and a_ >= b_ > 0) else o.get("ltp")
                h.append((now, o.get("iv"), q if q == q and q > 0 else None, mid,
                          o.get("delta"), o.get("gamma"), o.get("theta_min")))
            if ctx.get("spot"):
                sh = self._ohist.get("spot")
                if sh is None:
                    sh = self._ohist["spot"] = deque(maxlen=1000)
                sh.append((now, float(ctx["spot"])))
            if ctx.get("fut"):
                fh = self._ohist.get("fwd")
                if fh is None:
                    fh = self._ohist["fwd"] = deque(maxlen=1000)
                fh.append((now, float(ctx["fut"])))
        ctx["ohist"] = self._ohist

    def _entry_choice(self, b, ctx, gates):
        """The entry decision of one paper book, without filling: (fire, opt, why, msg). Shared by the real entry
        path and the missed-signal recorder's flat twins (7 Nov), so both run exactly the same rules."""
        fire, why = paper.evaluate_entry(b, ctx, gates)
        if not fire:
            return False, None, why, why
        d = paper.entry_dir(b, ctx)
        opt, msg = paper.choose_contract(ctx, d, b)
        if opt and b.p.get("cheap_strike"):
            opt, cnote = paper.cheap_strike(b, ctx, opt)   # 29 Oct night (R4-01): expiry-day lag-cheapest strike
            if cnote:
                why = f"{why} · {cnote}"
        if opt and b.p.get("gt_min"):
            msg = paper.buyer_edge_gate(b, ctx, opt)   # 27 Oct: is gamma worth its theta rent right now?
            if msg:
                opt = None
                for k in ("fire_id", "ep_type", "dir", "leg", "pb_trade", "orb_trade", "trig_str", "trig_unit"):
                    b.ctl.pop(k, None)              # the setup is skipped, not queued
        if opt and b.p.get("reentry"):
            opt, rmsg = paper.reentry_check(b, ctx, d, opt)   # 27 Oct: after a trailing exit: cheaper / stronger
            if not opt:
                msg = rmsg
                for k in ("fire_id", "ep_type", "dir", "leg", "pb_trade", "orb_trade", "trig_str", "trig_unit"):
                    b.ctl.pop(k, None)
        if opt and (b.p.get("iv_fall_rel15") is not None or b.p.get("skip_bid_pile")
                    or b.p.get("entry_hi5_veto_pct") or b.p.get("req_move_veto")):
            vmsg = paper.flow_veto(b, ctx, opt)     # 28 Oct night (round 2): IV fall / late bid pile
            if vmsg:
                opt, msg = None, vmsg
                for k in ("fire_id", "ep_type", "dir", "leg", "pb_trade", "orb_trade", "trig_str", "trig_unit"):
                    b.ctl.pop(k, None)
        return True, opt, why, msg

    def _entry(self, name, b, ctx):
        """The entry decision for one book (unchanged logic). True if a position was opened."""
        if name == "RAW":
            gates = []
        elif name.startswith(learning.GATED_PREFIX):          # the champion + one candidate gate
            gates = self.gates + [name[len(learning.GATED_PREFIX):]]
        else:
            gates = self.gates
        if b.ctl.get("pending_entry"):                            # D-126: a trigger waiting for its first print
            pos, why = paper.try_fill_entry(b, ctx)
            if name == self.champion:
                self.last_reason = why
            if not pos:
                return False
        else:
            fire, opt, why, msg = self._entry_choice(b, ctx, gates)
            if name == self.champion:
                self.last_reason = why
            if not fire:
                return False
            if not opt:
                if name == self.champion:
                    self.last_reason = msg
                return False
            if config.FILL_NEXT_PRINT:
                paper.request_entry(b, ctx, opt, why)
                if name == self.champion:
                    self.last_reason = f"entry pending: waiting for a print on {opt['strike']:.0f} {opt['rr']}"
                return False
            pos = paper.open_trade(b, ctx, opt, why)
            if not pos:
                if name == self.champion:
                    self.last_reason = b.blocked or "entry rejected"      # D-124: never show "Entering" for a rejected entry
                return False
        if name == self.champion:
            audio.play("entry")
        if name in (self.champion, "RAW"):
            tag = "ENTRY" if name == self.champion else "RAW-ENTRY"
            self.ev(tag, f"BUY {pos['lots']} lots NIFTY {pos['strike']:.0f} {pos['rr']} "
                         f"({pos['expiry']}) @ {pos['entry']:.2f} · {why}")
        return True

    def _council(self, name, b, ctx):
        """One second of a council book: the strategy class decides, paper.open_trade / close_trade fill."""
        from .engine import council
        ad = getattr(self, "_council_ad", None)
        if ad is None:
            ad = self._council_ad = {}
        a = ad.get(name)
        if a is None or a.day != self.day:
            a = ad[name] = council.Adapter(b.p["council"], self.day, self.w0)
        n0, had = len(b.trades), b.pos
        traded = a.step(self, b, ctx)
        if not traded or name not in (self.champion, "RAW"):
            return traded
        champ = name == self.champion
        if len(b.trades) > n0:                         # closed a position
            t = b.trades[-1]
            if champ:
                audio.play("win" if t["pnl_pts"] > 0 else "loss")
            self.ev("EXIT" if champ else "RAW-EXIT",
                    f"{t['rr']} {t['strike']:.0f} {t['lots']} lots · {t['entry']:.2f} → {t['exit']:.2f} "
                    f"= {t['pnl_pts']:+.2f} pts / ₹{t['pnl_rs']:+,.0f} · {t['reason']} · capital ₹{b.capital:,.0f}")
        if b.pos and b.pos is not had:                 # opened a position
            pos = b.pos
            if champ:
                audio.play("entry")
                self.last_reason = pos.get("why") or "council entry"
            self.ev("ENTRY" if champ else "RAW-ENTRY",
                    f"BUY {pos['lots']} lots NIFTY {pos['strike']:.0f} {pos['rr']} "
                    f"({pos['expiry']}) @ {pos['entry']:.2f} · {pos.get('why', 'COUNCIL')}")
        return traded

    def _exit_signature(self):
        """What a restart must not forget about each open position (C-11)."""
        out = []
        for name, b in sorted((self.books or {}).items()):
            p = b.pos
            if p:
                out.append((name, p.get("key"), p.get("best"), bool(p.get("trail")), p.get("best_spot"),
                            (p.get("pending") or {}).get("reason"), bool(p.get("stale_exit"))))
        return tuple(out)

    DEC_MAX_LINES = 3000                         # hard cap per day: a flip-flopping reason cannot fill the disk

    _lp = None

    def _loop_stat(self, ms):
        """3 Nov: once a minute, log the tick time (p50 / p95 / max) when any tick in the minute took over 300 ms.
        Live ticks that run late (book saves, audio) shift fills by a print; the fast replay never has them."""
        lp = self._lp
        now = time.perf_counter()
        if lp is None or now - lp["t0"] >= 60.0:
            if lp and lp["xs"] and max(lp["xs"]) > 300.0:
                xs = sorted(lp["xs"])
                log(f"ENGINE tick time last minute: p50 {xs[len(xs) // 2]:.0f} ms, p95 {xs[int(len(xs) * 0.95)]:.0f} ms, "
                    f"max {xs[-1]:.0f} ms over {len(xs)} ticks (over 300 ms: {sum(1 for x in xs if x > 300.0)})")
            self._lp = lp = {"t0": now, "xs": []}
        lp["xs"].append(ms)

    def _tape_decision(self, ctx):
        """C-34: the champion's reason path, one line whenever its reason class changes."""
        champ = self.books.get(self.champion)
        why = self.last_reason
        fired = bool(champ and champ.pos and champ.pos.get("t_in") == ctx["now_s"])
        cls = reason_cls(why, fired)
        if cls == self._dec_cls or self._dec_n >= self.DEC_MAX_LINES:
            return
        self._dec_cls = cls
        self._dec_n += 1
        dom = ctx.get("domino") or {}
        ep = ctx.get("episode") or {}
        dr = ep.get("dir") or dom.get("dir") or 1
        rec = {"t": ctx["now_s"], "time": ctx["now_dt"].strftime("%H:%M:%S"), "cls": cls, "reason": why,
               "z": fnum((dom.get("z") or 0.0) * dr, 2),
               "S": fnum(dom.get("S_up") if dr > 0 else dom.get("S_dn"), 3),
               "moved": fnum(abs(ctx["fut"] - ep["fut0"]), 1) if ep.get("fut0") else None,
               "ep": ep.get("id"), "iv_rise": fnum(ctx.get("iv_rise_since_onset"), 2),
               "iv_rise_interp": fnum(ctx.get("iv_rise_interp"), 2),
               "edge": edge_mod.signed(ctx.get("edge"), dr)}       # D-136
        if self._dec_n == self.DEC_MAX_LINES:
            rec["capped"] = True
        _append_jsonl(os.path.join(config.PAPER_DIR, f"decisions_{self.day}.jsonl"), rec)

    # ── publish ────────────────────────────────────────────────────────────
    def publish(self):
        snap = self.m.snap
        if snap is None or not self.items:
            return
        ctx = self.ctx or {}
        heroes = []
        oi5 = self.oi_hist[0][1] if self.oi_hist else {}
        chg5 = self.m.change(self.m.ltp, 5)
        for i, rr, k in self.heroes():
            g = self.greek.get(i, {})
            heroes.append({
                "id": i, "rr": rr, "strike": k,
                "iv": g.get("iv"), "delta": g.get("delta"), "theta": g.get("theta_min"), "vega": g.get("vega"),
                "sb": fnum(self.m.sb[i, self.m.k], 0), "ss": fnum(self.m.ss[i, self.m.k], 0),
                "sbo": fnum(self.m.sbo[i, self.m.k], 0), "sso": fnum(self.m.sso[i, self.m.k], 0),
                "cls_b": CLS[int(self.flow.cls_b[i])], "cls_s": CLS[int(self.flow.cls_s[i])],
                "cls_bo": CLS[int(self.flow.cls_bo[i])], "cls_so": CLS[int(self.flow.cls_so[i])],
                "imb_q": fnum(self.flow.imb_q[i], 2), "imb_o": fnum(self.flow.imb_o[i], 2),
                "imb_t": fnum(self.flow.imb_t[i], 2), "lead": fnum(self.flow.lead[i], 2),
                "avg_b": fnum(self.flow.avg_b[i], 0), "avg_s": fnum(self.flow.avg_s[i], 0),
                "agg_b": fnum(self.flow.agg_b[i], 0), "agg_s": fnum(self.flow.agg_s[i], 0),
                "vol_s": fnum(self.flow.vol_s[i], 0),
                "oi_chg": fnum(float(snap["oi"][i]) - oi5.get(i, np.nan), 0),
                "run_up": fnum(self.flow.run_score(i, 1 if rr == "CE" else -1, self.m, chg5), 2),
            })
        dom = self.domino.state if self.domino else {}
        tiles = []
        for tile in dom.get("tiles", []):
            tiles.append(tile)
        eq = []
        for it in self.items:
            if it["kind"] != "eq":
                continue
            i = it["id"]
            ltp, prev = float(snap["ltp"][i]), float(snap["close"][i])
            fid = self.key.get(f"{it['sym']}|FUT")
            eq.append({"sym": it["sym"], "group": it.get("group"), "wn": it.get("wn"), "wb": it.get("wb"), "wf": it.get("wf"),
                       "id": i, "fid": fid,
                       "chg": fnum((ltp / prev - 1) * 100, 2) if prev > 0 and ltp > 0 else None,
                       "cls_b": CLS[int(self.flow.cls_b[i])], "cls_s": CLS[int(self.flow.cls_s[i])],
                       "agg": fnum(self.flow.agg_b[i] - self.flow.agg_s[i], 0),
                       "fut_oi_chg": fnum(float(snap["oi"][fid]) - oi5.get(fid, np.nan), 0) if fid is not None else None})
        champ = self.books.get(self.champion)
        pos = None
        if champ and champ.pos:
            p = champ.pos
            o = (ctx.get("by_key", {}).get(p["key"]) if ctx else None)
            if o and o["id"] != p["id"]:
                p["id"] = o["id"]                   # follow the contract if its row moved
            last = (o or {}).get("ltp") or p.get("last") or p["entry"]
            pos = dict(p, last=last, pnl_pts=round(last - p["entry"], 2),
                       pnl_rs=round((last - p["entry"]) * p["qty"], 0),
                       g=self.greek.get(p["id"], {}))
            pos.pop("advisors", None)
            # display-only extras for the dashboard (nothing below feeds a decision)
            fut_now, stop = ctx.get("fut"), p.get("stop_fut")
            zero_dte = p.get("expiry") == self.now_dt.date().isoformat()
            if (champ.p or {}).get("spot_trail"):           # D-124: the spot book's stop is on spot
                fut_now, stop = ctx.get("spot"), p.get("stop_spot")
            council = bool((champ.p or {}).get("council"))
            if council:                                     # 3 Nov: a council book never runs the spot trail or the
                fut_now, stop = ctx.get("fut"), None        # profit lock; its real rules are in pos["rules"]
            pos.update(d_star=None if council else ((champ.p or {}).get("spot_trail") or (champ.p or {}).get("d_star")),
                       fut_now=fnum(fut_now, 2),
                       on_spot=bool((champ.p or {}).get("spot_trail")) and not council,
                       lock_pct=None if council else (champ.p or {}).get("lock_pct"),
                       lock_trail_pct=None if council else (champ.p or {}).get("lock_trail_pct"),
                       spot_now=fnum(ctx.get("spot"), 2),
                       stop_pts=fnum((fut_now - stop) * p["dir"], 2) if fut_now is not None and stop is not None else None,
                       hold_s=fnum(self.now_s - p["t_in"], 0),
                       ret_pct=fnum(100.0 * (last - p["entry"]) / p["entry"], 2) if p["entry"] else None,
                       time_exit=(p.get("rules") or {}).get("flat_at") if council else
                                 "%02d:%02d" % (config.ZERO_DTE_FLATTEN if zero_dte else config.FLATTEN_AT))
        state = {
            "mode": self.mode, "now": self.now_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "phase": config.session_phase(self.now_dt), "cas_test": bool(getattr(config, "CAS_TEST", False)),
            "entry_window": "%02d:%02d-%02d:%02d" % (config.SUPPRESS_UNTIL + config.LAST_ENTRY),
            "feed": FEED_STATES.get(int(self.t.c("feed_state")), "?"),
            "health": self._safe("health", lambda: self.data_health(snap), None),
            "hot_p50": fnum(self.t.c("hot_p50_us"), 1), "hot_p99": fnum(self.t.c("hot_p99_us"), 1),
            "msgs_s": fnum(self.t.c("msgs_per_s"), 0), "rest_today": int(self.t.c("rest_today")),
            "reconnects": int(self.t.c("reconnects")), "loop_ms": fnum(self.loop_ms, 1),
            "vix": fnum(self.t.c("vix"), 2), "atm": getattr(self, "atm", None), "fwd": fnum(getattr(self, "fwd", None), 1),
            "atm_iv": fnum(self.atm_iv * 100 if getattr(self, "atm_iv", None) else None, 2),
            "iv5": fnum(self.iv_change(300), 2), "w0": self.w0, "w1": self.w1,
            "heroes": heroes, "K_up": fnum(ctx.get("K_up"), 2), "K_dn": fnum(ctx.get("K_dn"), 2),
            "domino": {k: v for k, v in dom.items() if k != "tiles"}, "tiles": tiles, "eq": eq,
            "episode": self.domino.episode_view(self.now_s) if self.domino else None,
            "iv_rise": fnum(ctx.get("iv_rise_since_onset"), 2),
            "atm_iv_interp": fnum(self.atm_iv_interp * 100 if self.atm_iv_interp else None, 2),   # O-1 observer
            "iv_rise_interp": fnum(ctx.get("iv_rise_interp"), 2),                                  # O-1 observer
            "engine_ok_s": self.engine_ok_s,     # C-08: market time of the last step that completed
            "reason": self.last_reason, "advisors": self.advisors,
            "pressure": self.pressure.view(ctx.get("spot") or ctx.get("fut")),
            "chain": self.pressure.chain_view(ctx.get("spot") or ctx.get("fut")),
            "fut": fnum(ctx.get("fut"), 2), "fut_ltp": fnum(ctx.get("fut_ltp"), 2), "spot": fnum(ctx.get("spot"), 2),
            "fut_prev": fnum(snap["close"][self.fut_id], 2) if self.fut_id is not None and snap["close"][self.fut_id] > 0 else None,
            # today's range of the futures (from the feed's session high/low fields; the engine also keeps
            # its own running extremes in case a feed omits them)
            "fut_hi": self._day_hi, "fut_lo": self._day_lo,
            "late": self.lateness(ctx),
            "straddle": self.straddle.view(), "bank": self.bank.view(), "lag": self.lag.view(),
            "straddle_watch": self.watch.view(series=True),
            "ideas": self._safe("ideas view", self.ideas.view, None) if getattr(self, "ideas", None) else None,
            "gex": self.gex.v,
            "event": event_today(self.day),
            "fut_book": self.fut_book(),
            "episodes_logged": self.eplog.count if self.eplog else 0,
            "force": self.force.view(),
            "params": self.books[self.champion].p if champ else None,
            "spot_range": {"hi": fnum(ctx.get("spot_hi"), 2), "lo": fnum(ctx.get("spot_lo"), 2),   # D-124: what the
                           "age": fnum(ctx.get("spot_age"), 1),                                      # spot books see
                           "swing_last": (champ.ctl.get("swing_last") if champ else None)},
            "champion": self.champion, "gates": self.gates,
            "learning": {k: self.lstate.get(k) for k in ("status", "scoreboard", "champion_since", "retired", "candidates")},
            "controls": list(config.CONTROLS),
            "blackout": self.guard.view(self.now_s),
            "regime": self.regime.view() if getattr(self, "regime", None) else None,
            "quant": self.quant.view() if getattr(self, "quant", None) else None,   # 5 Nov: display only
            "ledger": self.ledger.view() if getattr(self, "ledger", None) else None,
            "commentary": self.commentary.view() if getattr(self, "commentary", None) else None,   # council 5
            "spot_prev": fnum(snap["close"][self.spot_id], 2) if self.spot_id is not None and snap["close"][self.spot_id] > 0 else None,
            "vix_prev": None,
            "flatten_at": "%02d:%02d" % config.FLATTEN_AT, "lock_pct": config.LOCK_PCT, "lock_trail_pct": config.LOCK_TRAIL_PCT,
            "book": champ.stats() if champ else None, "pos": pos,
            "trades": [{k: t.get(k) for k in ("time_in", "time_out", "rr", "strike", "lots", "entry", "exit",
                                              "pnl_pts", "pnl_rs", "reason", "capital_after", "ep_type",
                                              "spot_in", "best_spot", "qty", "hold_s", "ret_pct", "entry_bid", "entry_ask",
                                              "lock_armed", "fill_delay_s", "fill_slip")}
                       for t in (champ.trades[-25:] if champ else [])][::-1],
            "variants": sorted([b.stats() for b in self.books.values()], key=lambda s: -s["pnl_pts"]),
            "events": list(self.events)[:60],
        }
        self.blob.write_state(state)              # 5 Nov: fast path, byte-identical to write(clean(state))

    def run(self):
        from .feed_core import source_hash
        log(f"starting in {self.mode} mode · code {source_hash()}")
        src = audio.init(log)
        log(f"audio: {src}" if src else "audio: off")
        while not int(self.t.c("stop")):
            self.load_registry()
            if self.items:
                break
            time.sleep(0.2)
        last_vt = 0
        while not int(self.t.c("stop")):
            lock = self.mode == "replay" and int(self.t.c("lockstep"))
            if lock:
                # D-105: one step per published boundary of virtual time — deterministic at any speed
                while not int(self.t.c("stop")) and int(self.t.c("feed_state")) != 7:
                    vt = int(self.t.c("now_ns"))
                    if vt > last_vt:
                        break
                    time.sleep(0.0002)
                last_vt = int(self.t.c("now_ns"))
            t0 = time.perf_counter()
            ok = self.tick()
            if lock:
                self.t.set("eng_vt_ns", last_vt)
            if not ok:
                if lock:
                    continue
                time.sleep(0.5)
            self.loop_ms = (time.perf_counter() - t0) * 1000
            self._loop_stat(self.loop_ms)
            if int(self.t.c("feed_state")) == 7 and self.mode != "live":   # replay finished
                break
            if lock:
                continue
            speed = max(float(self.t.c("speed")), 1.0)
            time.sleep(max(0.1 / speed - (time.perf_counter() - t0), 0.005))
        if self.books:
            self._safe("stop: save books", lambda: paper.save_books(self.books, self.day))
            if self.eplog:
                self._safe("stop: episode log", self.eplog.close)
            self._safe("stop: straddle watch", self.watch.close)
            if getattr(self, "ideas", None) is not None:
                self._safe("stop: ideas", self.ideas.close)
            if getattr(self, "ledger", None) is not None:
                self._safe("stop: ledger", self.ledger.close)
            if self.mode != "live" or config.hm(self.now_dt) >= config.mins(config.MARKET_CLOSE):
                try:                                 # the stop path must always reach "stopped"
                    self.end_day()
                except Exception:
                    log("end_day at stop: " + traceback.format_exc())
        self._safe("stop: publish", self.publish)
        log("stopped")

    def tick_nopublish(self):
        """T02: one step without the wall-clock publish (apex/replay_fast.py publishes on market time)."""
        try:
            self.load_registry()
            self.step()
        except Exception:
            log(traceback.format_exc())
            return False
        self.engine_ok_s = getattr(self, "now_s", None)
        self.t.set("engine_hb_ns", time.time_ns())
        return True

    def tick(self):
        """One loop iteration. C-08: the heartbeat (engine_hb_ns, and engine_ok_s in the state blob)
        advances only when step() completed, so a faulting engine looks stalled, not healthy."""
        if not self.tick_nopublish():
            return False
        try:
            if time.monotonic() - self.last_publish >= 0.25:
                self.last_publish = time.monotonic()
                self.publish()
            if self.mode == "live" and time.monotonic() - getattr(self, "_last_warm", 0.0) >= getattr(config, "WARM_SAVE_S", 30):
                self._last_warm = time.monotonic()
                self._save_warm()
        except Exception:
            log(traceback.format_exc())
            return False
        return True


def main():
    global LOG
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)   # Ctrl+C is the supervisor's: it sets ctrl.stop
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)   # NaN = "no quote yet"
    mode = sys.argv[1] if len(sys.argv) > 1 else "live"
    LOG = open(os.path.join(config.LOG_DIR, "engine.log"), "a", encoding="utf-8")
    t = Table()
    blob = StateBlob()
    Engine(t, blob, mode).run()


if __name__ == "__main__":
    main()
