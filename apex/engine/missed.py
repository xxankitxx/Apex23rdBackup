"""Missed-signal recorder (7 Nov 2026; design: docs/29_MISSED_SIGNAL_RECORDER.md). Observer only.

While a book is busy (in a position or waiting for an entry fill), a FLAT TWIN of that book is stepped through the
same entry pipeline. Each episode it fires becomes one row in missed_<day>.jsonl, with the outcome of a clean
COUNTERFACTUAL book that takes the trade and runs the book's own exits to a natural end. Nothing here is read by any
decision, saved with the books, or shown on the dashboard. Switched on by APEX_RECORD_MISSED=1 (replays only).
"""
import copy
import json
import os

from .. import config
from . import paper, learning

EPISODE_GAP_S = 30.0                    # fires further apart than this start a new episode
_SETUP_KEYS = ("fire_id", "ep_type", "dir", "leg", "pb_trade", "orb_trade", "trig_str", "trig_unit")


def enabled():
    return os.environ.get("APEX_RECORD_MISSED") == "1"


def _side_of(rr):
    return "CE" if rr == "CE" else "PE"


class _Episode:
    __slots__ = ("book", "eid", "side", "relation", "first_t", "first_time", "last_t", "last_time", "count",
                 "signal", "strength", "real_key", "real_time_in", "cf", "cf_kind", "cf_status", "cf_trade", "done")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


class MissedRecorder:
    def __init__(self, day, out_dir):
        self.day = day
        self.path = os.path.join(out_dir, f"missed_{day}.jsonl")
        self.twins = {}                 # book name -> twin (paper.Book copy, or council strategy copy)
        self.twin_i = {}                # council book -> last row stepped
        self.open = {}                  # (book, side) -> current _Episode (for dedupe)
        self.live = []                  # episodes whose counterfactual is still running
        self.n = {}                     # book -> episode counter
        self.rows = 0

    # ------------------------------------------------------------------ helpers
    def _new_episode(self, name, side, relation, ctx, signal, strength, real):
        k = self.n.get(name, 0) + 1
        self.n[name] = k
        t = ctx["now_s"]
        tm = ctx["now_dt"].strftime("%H:%M:%S")
        return _Episode(book=name, eid=f"{name}#{k}", side=side, relation=relation, first_t=t, first_time=tm,
                        last_t=t, last_time=tm, count=1, signal=signal, strength=strength,
                        real_key=(real or {}).get("key"), real_time_in=(real or {}).get("time_in"),
                        cf=None, cf_kind=None, cf_status=None, cf_trade=None, done=False)

    def _fire(self, name, side, ctx, signal, strength, real_pos):
        """Dedupe: a fire within EPISODE_GAP_S of the last one in the same direction extends that episode.
        Returns the NEW episode (to receive a counterfactual), or None when the fire only extended one."""
        key = (name, side)
        ep = self.open.get(key)
        now = ctx["now_s"]
        if ep is not None and now - ep.last_t <= EPISODE_GAP_S:
            ep.last_t, ep.last_time, ep.count = now, ctx["now_dt"].strftime("%H:%M:%S"), ep.count + 1
            return None                          # (a seeded real episode has eid None and is never written)
        real_side = _side_of(real_pos["rr"]) if real_pos else None
        relation = None if real_side is None else ("same" if real_side == side else "opposite")
        ep = self._new_episode(name, side, relation, ctx, signal, strength, real_pos)
        self.open[key] = ep
        self.live.append(ep)
        return ep

    def _seed_real(self, name, b, ctx):
        """At twin creation: the real book's own trade is the current episode in its direction, so the twin's
        repeats of that same signal are absorbed (never written) instead of being counted as a missed trade."""
        rr = (b.pos or {}).get("rr")
        if rr is None:
            key = (b.ctl.get("pending_entry") or {}).get("key") or ""
            rr = key.split("|")[-1] if key else None
        if rr in ("CE", "PE"):
            t = ctx["now_s"]
            self.open[(name, rr)] = _Episode(book=name, eid=None, side=rr, first_t=t, last_t=t, count=1, done=True)

    def _write(self, ep):
        t = ep.cf_trade or {}
        row = {"date": self.day, "book": ep.book, "episode_id": ep.eid, "side": ep.side, "relation": ep.relation,
               "first_fire_time": ep.first_time, "last_fire_time": ep.last_time, "fire_count": ep.count,
               "signal": ep.signal, "strength": ep.strength, "real_key": ep.real_key, "real_time_in": ep.real_time_in,
               "cf_status": ep.cf_status, "cf_time_in": t.get("time_in"), "cf_time_out": t.get("time_out"),
               "cf_entry": t.get("entry"), "cf_exit": t.get("exit"), "cf_hold_s": t.get("hold_s"),
               "cf_pnl_rs": t.get("pnl_rs"), "cf_ret_pct": t.get("ret_pct"), "cf_peak_pts": t.get("peak_pts"),
               "cf_reason": t.get("reason"), "cf_strike": t.get("strike"), "cf_rr": t.get("rr"),
               "is_counterfactual": True, "snapshot_id": None}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=float, separators=(",", ":")) + "\n")
        self.rows += 1

    # ------------------------------------------------------------------ paper books
    def step_paper(self, eng, name, b, ctx):
        busy = b.pos is not None or bool(b.ctl.get("pending_entry"))
        if not busy:
            self.twins.pop(name, None)
            return
        tw = self.twins.get(name)
        if tw is None:
            tw = copy.deepcopy(b, {id(b.trades): [], id(b.pos): None})   # never copy the trade list or position
            tw.pos = None
            tw.trades = []
            pe = tw.ctl.pop("pending_entry", None)
            if pe:                               # the real book is about to fill this setup: the twin has used it
                for k, v in (pe.get("ctl") or {}).items():
                    if v is not None:
                        tw.ctl[k] = v
            self._consume(tw, ctx)
            self._seed_real(name, b, ctx)
            self.twins[name] = tw
            return                               # the twin starts stepping from the next second
        gates = [] if name == "RAW" else (eng.gates + [name[len(learning.GATED_PREFIX):]]
                                          if name.startswith(learning.GATED_PREFIX) else eng.gates)
        fire, opt, why, _msg = eng._entry_choice(tw, ctx, gates)
        if not (fire and opt):
            return
        strength = tw.ctl.get("trig_str")
        ep = self._fire(name, _side_of(opt["rr"]), ctx, why, strength, b.pos)
        if ep is not None:                       # a new episode: a clean counterfactual book takes the trade
            cf = copy.deepcopy(tw, {id(tw.trades): []})
            cf.capital = b.capital
            cf.trades = []
            cf.gt_id = ep.eid                    # its own gain-trail window: never the real book's (paper._GT_BUF)
            if config.FILL_NEXT_PRINT:
                paper.request_entry(cf, ctx, opt, why)
            elif paper.open_trade(cf, ctx, opt, why) is None:
                ep.cf_status = "rejected"
            ep.cf, ep.cf_kind = cf, "paper"
        self._consume(tw, ctx)                   # the twin uses the setup as a real entry would, and stays flat

    @staticmethod
    def _consume(tw, ctx):
        """What paper.open_trade does to a book's entry state (fired episode, trigger keys, re-entry chain),
        without opening a position."""
        ep_id = (ctx.get("episode") or {}).get("id")
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
            tw = copy.deepcopy(adapter.strat, {id(D): D})     # never copy the shared LiveDay
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
        ep = self._fire(name, _side_of(rr), ctx, why, None, b.pos)
        if ep is None:
            return
        from . import council
        cfb = paper.Book(name + "#cf", b.p, self.day)
        cfb.gt_id = ep.eid
        cfb.capital = b.capital
        cfa = object.__new__(council.Adapter)
        cfa.strat = copy.deepcopy(tw, {id(D): D})
        cfa.D, cfa.day, cfa.last_i = D, adapter.day, i
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
        keep = []
        for ep in self.live:
            if ep.cf is None or ep.cf_status == "rejected":
                ep.done = True
            elif ep.cf_kind == "paper":
                cf = ep.cf
                try:
                    paper.check_exit(cf, ctx)
                    if cf.ctl.get("pending_entry"):
                        paper.try_fill_entry(cf, ctx)
                except Exception:
                    ep.cf_status, ep.done = "error", True
                self._settle(ep, cf)
            else:
                cfb, cfa = ep.cf
                try:
                    cfa.step(eng, cfb, ctx)
                except Exception:
                    ep.cf_status, ep.done = "error", True
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
        if ep.done:
            return
        if book.trades:
            ep.cf_trade, ep.cf_status, ep.done = book.trades[0], "closed", True
        elif book.pos is None and not book.ctl.get("pending_entry"):
            ep.cf_status, ep.done = "lapsed", True

    def close(self, ctx=None):
        """End of day: every episode is written; a counterfactual still open is marked open_at_end."""
        for ep in self.live:
            if not ep.done:
                ep.cf_status = ep.cf_status or "open_at_end"
            self._write(ep)
        self.live = []
        self.open = {}
        self.twins = {}
