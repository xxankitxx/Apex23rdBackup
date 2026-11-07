"""Missed-signal recorder (7 Nov 2026; design: docs/29_MISSED_SIGNAL_RECORDER.md). Observer only.

While a book is busy (in a position or waiting for an entry fill), a FLAT TWIN of that book is stepped through the
same entry pipeline. Each episode it fires becomes one row in missed_<day>.jsonl, with the outcome of a clean
COUNTERFACTUAL book that takes the trade and runs the book's own exits to a natural end. Nothing here is read by any
decision, saved with the books, or shown on the dashboard. Switched on by APEX_RECORD_MISSED=1 (replays only).
At the end of the day a summary (rows, episodes per book, errors, faults, copy time) goes to missed_summary_<day>.json.
"""
import copy
import json
import os
import re
import time

from .. import config
from . import paper, learning

# Fires further apart than this start a new episode. It is also the WRITE DELAY: an episode is written only once its
# counterfactual has finished AND no fire has extended it for this long, so its fire_count is complete.
EPISODE_GAP_S = 30.0
_SETUP_KEYS = paper._SETUP_KEYS_ALL
_V = re.compile(r"v=([+-]?\d+(?:\.\d+)?)")


def enabled():
    return os.environ.get("APEX_RECORD_MISSED") == "1"


def _side_of(rr):
    return "CE" if rr == "CE" else "PE"


def _photo_safe(ctx, side):
    try:
        from .weather import photo
        return photo(ctx, 1 if side == "CE" else -1, None)
    except Exception:
        return None


def _real_side(b):
    """The side of the trade keeping the real book busy: its position, or the entry it is waiting to fill."""
    rr = (b.pos or {}).get("rr")
    if rr is None:
        key = (b.ctl.get("pending_entry") or {}).get("key") or ""
        rr = key.split("|")[-1] if key else None
    return rr if rr in ("CE", "PE") else None


class _Episode:
    __slots__ = ("book", "eid", "side", "relation", "first_t", "first_time", "last_t", "last_time", "count",
                 "last_sec", "setup", "signal", "strength", "real_key", "real_time_in", "cf", "cf_kind",
                 "cf_status", "cf_trade", "done", "weather")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


class MissedRecorder:
    def __init__(self, day, out_dir):
        self.day = day
        self.path = os.path.join(out_dir, f"missed_{day}.jsonl")
        self.summary_path = os.path.join(out_dir, f"missed_summary_{day}.json")
        self.twins = {}                 # book name -> twin (paper.Book copy, or council strategy copy)
        self.twin_i = {}                # council book -> last row stepped
        self.open = {}                  # (book, side) -> current _Episode (for dedupe)
        self.live = []                  # episodes not yet written
        self.n = {}                     # book -> episode counter
        self.rows = 0
        self.cf_errors = 0              # counterfactual books that raised (gate: must be zero)
        self.faults = 0                 # recorder steps that raised (gate: must be zero)
        self.copy_s = 0.0               # time spent deep-copying twins and counterfactuals
        self.copies = 0

    # ------------------------------------------------------------------ helpers
    def _copy(self, obj, memo):
        t0 = time.perf_counter()
        out = copy.deepcopy(obj, memo)
        self.copy_s += time.perf_counter() - t0
        self.copies += 1
        return out

    def _new_episode(self, name, side, relation, ctx, signal, strength, real, setup):
        k = self.n.get(name, 0) + 1
        self.n[name] = k
        t = ctx["now_s"]
        tm = ctx["now_dt"].strftime("%H:%M:%S")
        return _Episode(book=name, eid=f"{name}#{k}", side=side, relation=relation, first_t=t, first_time=tm,
                        last_t=t, last_time=tm, count=1, last_sec=int(t), setup=setup, signal=signal,
                        strength=strength, real_key=(real or {}).get("key"),
                        real_time_in=(real or {}).get("time_in"), cf=None, cf_kind=None, cf_status=None,
                        cf_trade=None, done=False,
                        weather=_photo_safe(ctx, side))   # 7 Nov (stage 2): at the episode's first fire

    def _fire(self, name, side, ctx, signal, strength, b, setup=None):
        """Dedupe. A fire extends the open episode in the same direction when it is within EPISODE_GAP_S of that
        episode's last fire AND (when both carry one) has the same setup identity; otherwise it starts a new episode.
        fire_count counts distinct SECONDS with a fire (paper twins are stepped every 100 ms, council once a second).
        Returns the NEW episode (to receive a counterfactual), or None when the fire only extended one."""
        key = (name, side)
        ep = self.open.get(key)
        now = ctx["now_s"]
        same_setup = setup is None or ep is None or ep.setup is None or ep.setup == setup
        if ep is not None and now - ep.last_t <= EPISODE_GAP_S and same_setup:
            ep.last_t, ep.last_time = now, ctx["now_dt"].strftime("%H:%M:%S")
            if int(now) != ep.last_sec:
                ep.count, ep.last_sec = ep.count + 1, int(now)
            return None                          # (a seeded real episode has eid None and is never written)
        rs = _real_side(b)
        relation = None if rs is None else ("same" if rs == side else "opposite")
        pe = b.ctl.get("pending_entry") or {}
        real = b.pos or ({"key": pe.get("key"), "time_in": pe.get("time")} if pe else None)
        ep = self._new_episode(name, side, relation, ctx, signal, strength, real, setup)
        self.open[key] = ep
        self.live.append(ep)
        return ep

    def _seed_real(self, name, b, ctx, setup=None):
        """At twin creation: the real book's own trade is the current episode in its direction, so the twin's
        repeats of that same signal are absorbed (never written) instead of being counted as a missed trade."""
        rr = _real_side(b)
        if rr is not None:
            t = ctx["now_s"]
            self.open[(name, rr)] = _Episode(book=name, eid=None, side=rr, first_t=t, last_t=t, count=1,
                                             last_sec=int(t), setup=setup, done=True)

    def _write(self, ep):
        if ep.eid is None:                       # a seeded real episode: never written
            return
        t = ep.cf_trade or {}
        row = {"date": self.day, "book": ep.book, "episode_id": ep.eid, "side": ep.side, "relation": ep.relation,
               "first_fire_time": ep.first_time, "last_fire_time": ep.last_time, "fire_count": ep.count,
               "fire_count_unit": "seconds", "signal": ep.signal, "strength": ep.strength,
               "real_key": ep.real_key, "real_time_in": ep.real_time_in,
               "cf_status": ep.cf_status, "cf_time_in": t.get("time_in"), "cf_time_out": t.get("time_out"),
               "cf_entry": t.get("entry"), "cf_exit": t.get("exit"), "cf_hold_s": t.get("hold_s"),
               "cf_pnl_rs": t.get("pnl_rs"), "cf_ret_pct": t.get("ret_pct"), "cf_peak_pts": t.get("peak_pts"),
               "cf_worst_pts": t.get("worst_pts"), "cf_stale_exit": bool(t.get("stale_exit")),
               "cf_fill_delay_s": t.get("fill_delay_s"), "cf_gap": bool(t.get("gap")),
               "cf_reason": t.get("reason"), "cf_strike": t.get("strike"), "cf_rr": t.get("rr"),
               "ep_type": t.get("ep_type"), "cf_why": t.get("why"),   # 7 Nov (stage 3): the diaries' family
               "is_counterfactual": True, "snapshot_id": ep.eid,
               # 7 Nov (stage 2): the photograph. The counterfactual's own (with its contract's theta) when it
               # reached a trigger, else the one taken at the first fire (no contract fields)
               "weather": t.get("weather_trig") or ep.weather}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=float, separators=(",", ":")) + "\n")
        self.rows += 1

    # ------------------------------------------------------------------ paper books
    def step_paper(self, eng, name, b, ctx):
        """Called every engine step, right after the real book's own exit and entry for this step."""
        try:
            self._step_paper(eng, name, b, ctx)
        except Exception:
            self.faults += 1
            raise

    def _step_paper(self, eng, name, b, ctx):
        assert not b.p.get("council"), f"{name}: a council book reached the paper twin path"   # 7 Nov (C16)
        busy = b.pos is not None or bool(b.ctl.get("pending_entry"))
        if not busy:
            self.twins.pop(name, None)
            return
        tw = self.twins.get(name)
        if tw is None:
            tw = self._copy(b, {id(b.trades): [], id(b.pos): None})   # never copy the trade list or position
            tw.pos = None
            tw.trades = []
            pe = tw.ctl.pop("pending_entry", None)
            if pe:                               # the real book is about to fill this setup: the twin has used it
                for k, v in (pe.get("ctl") or {}).items():
                    if v is not None:
                        tw.ctl[k] = v
            setup = self._setup_id(tw, ctx)
            self._consume(tw, ctx)
            self._seed_real(name, b, ctx, setup)
            self.twins[name] = tw
            return                               # the twin starts stepping from the next step
        gates = [] if name == "RAW" else (eng.gates + [name[len(learning.GATED_PREFIX):]]
                                          if name.startswith(learning.GATED_PREFIX) else eng.gates)
        fire, opt, why, _msg = eng._entry_choice(tw, ctx, gates)
        if not (fire and opt):
            return
        strength = tw.ctl.get("trig_str")
        setup = self._setup_id(tw, ctx)
        ep = self._fire(name, _side_of(opt["rr"]), ctx, why, strength, b, setup)
        if ep is not None:                       # a new episode: a clean counterfactual book takes the trade
            cf = self._copy(tw, {id(tw.trades): []})
            cf.capital = b.capital
            cf.trades = []
            cf.gt_id = ep.eid                    # its own gain-trail window: never the real book's (paper._GT_BUF)
            if config.FILL_NEXT_PRINT:
                paper.request_entry(cf, ctx, opt, why)
            elif paper.open_trade(cf, ctx, opt, why) is None:
                ep.cf_status = "rejected"
            ep.cf, ep.cf_kind = cf, "paper"
        # The twin uses the setup up AT THE FIRE; the real book uses it up at the FILL. So if a real entry lapses and
        # re-fires, the twin has one (lapsed) row and does not re-fire (docs/29, "known divergence").
        self._consume(tw, ctx)

    @staticmethod
    def _setup_id(tw, ctx):
        """A STABLE setup identity where the book has one: the straddle spike id or the domino episode id. Books
        driven by a fire_id (spot, pullback, ORB, controls) get None and fall back to the 30-s gap, because their
        fire_id embeds the current second and changes on every fire."""
        if tw.ctl.get("fire_id") is not None:
            return None
        if tw.p.get("spike"):
            sp = (ctx.get("straddle_watch") or {}).get("spike")
            return ("spike", sp["id"]) if sp else None
        ep = (ctx.get("episode") or {}).get("id")
        return ("episode", ep) if ep is not None else None

    @staticmethod
    def _consume(tw, ctx):
        """What paper.open_trade does to a book's entry state (fired episode or spike, trigger keys, re-entry chain),
        without opening a position."""
        sp = (ctx.get("straddle_watch") or {}).get("spike") if tw.p.get("spike") else None
        ep_id = -int(sp["id"]) if sp else (ctx.get("episode") or {}).get("id")
        if tw.ctl.get("fire_id") is not None:
            ep_id = tw.ctl["fire_id"]
        if ep_id is not None:
            tw.fired_episodes.add(ep_id)
        tw.ctl.pop("reentry", None)
        tw.ctl.pop("fill", None)
        for k in _SETUP_KEYS:
            tw.ctl.pop(k, None)

    # ------------------------------------------------------------------ council books
    def step_council(self, eng, name, adapter, b, ctx):
        try:
            self._step_council(eng, name, adapter, b, ctx)
        except Exception:
            self.faults += 1
            raise

    def _step_council(self, eng, name, adapter, b, ctx):
        busy = b.pos is not None or bool(b.ctl.get("pending_entry"))
        if not busy:
            self.twins.pop(name, None)
            self.twin_i.pop(name, None)
            return
        D = adapter.D
        i = int(ctx["now_s"] - D.t_open)
        if i < 0 or i >= len(D.T) or self.twin_i.get(name) == i or D.i != i:
            return
        self.twin_i[name] = i
        tw = self.twins.get(name)
        if tw is None:
            tw = self._copy(adapter.strat, {id(D): D})     # never copy the shared LiveDay
            self.twins[name] = tw
            self._seed_real(name, b, ctx)
            return                               # the real strategy already processed this second
        act = tw.on_second(i, D, None)
        if not act or act[0] != "BUY":
            return
        # the adapter's own entry checks (same as Adapter.step's BUY branch)
        if (ctx.get("blackout") or {}).get("on") or ctx.get("kill"):
            return
        w0 = ctx.get("w0")
        k, rr = int(act[1]), act[2]
        opt = ctx["by_key"].get(f"NIFTY|OPT|{w0}|{k}|{rr}")
        if not opt or not opt.get("ltp") or (opt.get("age") or 9e9) > config.EXIT_QUOTE_STALE_S:
            return
        if abs(opt.get("delta") or 0) < 0.5:
            return
        why = f"COUNCIL {act[3] if len(act) > 3 else ''}".strip()
        if b.p.get("rules"):                     # 7 Nov (stage 5): the same frozen-rule check as Adapter.step
            from . import rules as rules_mod
            if rules_mod.check(b, ctx, opt, why):
                return
        strength = getattr(tw, "_buy_v", None)   # 7 Nov (C20): the strategy's own trigger strength at the BUY
        if strength is None:
            m = _V.search(why)                   # fallback: the velocity in the signal text (e.g. "EXP brk v=+23")
            strength = float(m.group(1)) if m else None
        ep = self._fire(name, _side_of(rr), ctx, why, strength, b)
        if ep is None:
            return
        from . import council
        cfb = paper.Book(name + "#cf", b.p, self.day)
        cfb.gt_id = ep.eid
        cfb.capital = b.capital
        cfa = object.__new__(council.Adapter)    # Adapter.step needs only strat, D, last_i (+ getattr defaults)
        cfa.strat = self._copy(tw, {id(D): D})
        cfa.D, cfa.day, cfa.last_i = D, adapter.day, i
        cfa._warn = lambda msg: None             # a counterfactual never writes to the engine log
        if config.FILL_NEXT_PRINT:
            paper.request_entry(cfb, ctx, opt, why)
        else:
            pos = paper.open_trade(cfb, ctx, opt, why)
            if pos is None:
                ep.cf_status = "rejected"
            else:
                pos["ep_type"] = "COUNCIL"
        ep.cf, ep.cf_kind = (cfb, cfa), "council"

    # ------------------------------------------------------------------ counterfactuals, every step
    def advance(self, eng, ctx):
        """Runs once per engine step AFTER the whole book loop (engine_main.run_books), so the shared LiveDay row for
        this second has already been written by the real council books."""
        keep = []
        for ep in self.live:
            if ep.cf is None or ep.cf_status == "rejected":
                ep.done = True
            elif not ep.done and ep.cf_kind == "paper":
                cf = ep.cf
                try:
                    paper.check_exit(cf, ctx)
                    if cf.ctl.get("pending_entry"):
                        paper.try_fill_entry(cf, ctx)
                except Exception:
                    ep.cf_status, ep.done = "error", True
                    self.cf_errors += 1
                self._settle(ep, cf)
            elif not ep.done:
                cfb, cfa = ep.cf
                D = cfa.D
                if D.i == int(ctx["now_s"] - D.t_open):   # never let a counterfactual write the shared LiveDay
                    try:
                        cfa.step(eng, cfb, ctx)
                    except Exception:
                        ep.cf_status, ep.done = "error", True
                        self.cf_errors += 1
                    self._settle(ep, cfb)
            if ep.done and ctx["now_s"] - ep.last_t > EPISODE_GAP_S:
                self._write(ep)
                if self.open.get((ep.book, ep.side)) is ep:
                    del self.open[(ep.book, ep.side)]
            else:
                keep.append(ep)
        self.live = keep

    @staticmethod
    def _settle(ep, book):
        """trades[0]: a counterfactual book takes exactly one trade (it is never asked for a second entry)."""
        if ep.done:
            return
        if book.trades:
            ep.cf_trade, ep.cf_status, ep.done = book.trades[0], "closed", True
        elif book.pos is None and not book.ctl.get("pending_entry"):
            ep.cf_status, ep.done = "lapsed", True

    def close(self, ctx=None):
        """End of day: every episode is written (a counterfactual still open is marked open_at_end), then the
        day's summary."""
        for ep in self.live:
            if not ep.done:
                ep.cf_status = ep.cf_status or "open_at_end"
            self._write(ep)
        self.live = []
        self.open = {}
        self.twins = {}
        summary = {"date": self.day, "rows": self.rows, "episodes_by_book": dict(sorted(self.n.items())),
                   "cf_errors": self.cf_errors, "recorder_faults": self.faults,
                   "copies": self.copies, "copy_seconds": round(self.copy_s, 3)}
        try:
            with open(self.summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=1)
        except OSError:
            pass
        return summary
