"""
The Conductor's account (docs/28 §7; owner, 8 Nov 2026: live on paper from 9 Nov, every other book in shadow).

One account, one position, all-in, buy-only. The POOL (apex/rules/pool.json, add-only, every entry dated) holds
book-plus-rule pairs. The Conductor never decides an entry or an exit itself: it MIRRORS the pool books.

  * Trigger. When a pool book fires (paper.request_entry stores its pending entry, with the weather photograph
    taken at the trigger second), the pair's rule is checked on that photograph (apex/engine/rules.py). If it passes
    and the Conductor is flat with no owner, that book becomes the OWNER of the account for this trade.
  * Priority on the same tick: full standing before low; then the higher test-day return per trade; then the fixed
    book order of the run (the engine's own book order, recorded in every manifest), so a replay repeats itself.
  * Fill. The owner book's own fill (first print after the trigger, paper.try_fill_entry) is the Conductor's fill:
    same contract, same price, the Conductor's own capital (its lots differ, its return per trade is the same).
    If the owner's entry lapses or is rejected, ownership is released at once and the reason is logged.
  * Hold and exit. While the owner book holds, the Conductor holds; the owner's exit (price and reason) is the
    Conductor's exit. So every pool book's state machine runs exactly as it does alone; the Conductor only copies.
  * Every trigger it could not take is logged with why: occupied (by which book, since when), pending, lost
    priority (to which book), rule blocked (which rule, which value), unaffordable; and once a minute while flat the
    standing reason (pool empty, no eligible trigger, data blackout, kill).

The pool is read AS OF the day: a row is in force from its `from` date through its `to` date (none = open), and the
latest row of a (book, rule) pair is that pair's state — so a promotion, a new return figure or a retirement is a new
dated row, never an edit, and a replay of an earlier day trades the pool as it stood then (APEX_POOL_ASOF=all
overrides that for an in-sample study, which the output then says). A released owner (lapsed, rejected,
unaffordable) frees the account on the same step, and the triggers that fired on that step are still admissible. apex/conductor/account_sim.py computes the same account offline from a run's saved trades; the two agree
to the trade (tests/test_conductor.py), the sim being the oracle for the engine path.
"""
import copy
import json
import os

from .. import config
from . import paper, rules

POOL = os.environ.get("APEX_POOL_FILE") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                        "rules", "pool.json")   # APEX_POOL_FILE: a test / smoke pool
BOOK = "conductor"
STANDINGS = ("full", "low")


def load_pool(path=POOL):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"entries": []}


def pool_problems(pool, variants=None, reg=None):
    """Why the pool file is not usable (empty list = fine). Every entry names a registered non-control book, a rule
    that can be checked (coded or in the register) or none, a standing, a from-date."""
    variants = config.VARIANTS if variants is None else variants
    reg = rules.register_rules() if reg is None else reg
    bad = []
    for i, e in enumerate(pool.get("entries") or []):
        b = e.get("book")
        if b not in variants or b in config.CONTROLS or b == BOOK:
            bad.append(f"entry {i}: book {b!r} is not a registered non-control variant")
        rid = e.get("rule")
        if rid is not None and rid not in rules.CODED and rid not in reg:
            bad.append(f"entry {i}: rule {rid!r} cannot be checked (not coded, not in the register)")
        if e.get("standing") not in STANDINGS:
            bad.append(f"entry {i}: standing {e.get('standing')!r} not in {STANDINGS}")
        if not isinstance(e.get("from"), str) or len(e["from"]) != 10:
            bad.append(f"entry {i}: 'from' must be a YYYY-MM-DD date")
        to = e.get("to")
        if to is not None and (not isinstance(to, str) or len(to) != 10 or to < str(e.get("from"))):
            bad.append(f"entry {i}: 'to' must be a YYYY-MM-DD date on or after 'from'")
    return bad


def active_entries(pool, day, asof=None):
    """The pool as of `day` (docs/34 F03: one state per pair per day). An entry is in force from its `from` date
    through its `to` date (inclusive; no `to` = open-ended). When several rows of the same (book, rule) pair are in
    force on the day, the one with the latest `from` is the pair's state (so a promotion, a new return figure or a
    retirement is a NEW dated row, never an edit of an old one, and a replay of an earlier day sees the pool as it
    stood then). asof='all': every row, latest per pair, in-sample."""
    asof = asof if asof is not None else os.environ.get("APEX_POOL_ASOF", "")
    latest = {}
    for i, e in enumerate(pool.get("entries") or []):
        frm = e.get("from") or "9999"
        if asof != "all" and frm > day:
            continue
        k = (e.get("book"), e.get("rule"))
        if k not in latest or frm >= latest[k][0]:          # the latest row that has begun is the pair's state ...
            latest[k] = (frm, i, e)
    out = []
    for _f, i, e in sorted(latest.values(), key=lambda x: x[1]):
        to = e.get("to")                                     # ... and only THEN is its end date applied: an expired
        if asof == "all" or to is None or day <= to:         # latest row retires the pair; it never revives an older row
            out.append(e)
    return out


def priority_key(e, order):
    """Same-tick priority (docs/28 §7): full standing first, higher test-day return per trade, then book order."""
    return (0 if e.get("standing") == "full" else 1, -float(e.get("ret_per_trade") or 0.0),
            order.get(e.get("book"), 10 ** 6), str(e.get("rule") or ""))


class Conductor:
    def __init__(self, day, book_order, pool=None, pool_path=POOL, asof=None, log_dir=None):
        self.day = day
        self.pool = load_pool(pool_path) if pool is None else pool
        self.asof = asof if asof is not None else os.environ.get("APEX_POOL_ASOF", "")
        self.order = {n: i for i, n in enumerate(book_order)}
        ents = active_entries(self.pool, day, self.asof)
        self.members = sorted(ents, key=lambda e: priority_key(e, self.order))
        self.reason = "pool empty" if not self.members else "flat: no eligible trigger"
        self.log_dir = log_dir if log_dir is not None else config.PAPER_DIR
        self._reason_t = None
        self.events = 0

    # ── log ────────────────────────────────────────────────────────────────
    def _log(self, ctx, event, **kw):
        row = {"t": ctx.get("now_s"), "time": ctx["now_dt"].strftime("%H:%M:%S") if ctx.get("now_dt") else None,
               "event": event}
        row.update(kw)
        self.events += 1
        if self.log_dir:
            try:
                with open(os.path.join(self.log_dir, f"conductor_{self.day}.jsonl"), "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row, default=str) + "\n")
            except OSError:
                pass

    def _standing_reason(self, ctx, text):
        """The dashboard reason while flat; written to the log once a minute or when it changes."""
        changed = text != self.reason
        self.reason = text
        now = ctx.get("now_s") or 0.0
        if changed or self._reason_t is None or now - self._reason_t >= 60.0:
            self._reason_t = now
            self._log(ctx, "flat", why=text)

    # ── one engine step, after every pool book has run ─────────────────────
    def step(self, cb, books, ctx):
        """cb = the Conductor's own Book. Returns ("entry", pos) | ("exit", trade) | ("owner", info) | None."""
        now = ctx["now_s"]
        reg = rules.register_rules()
        fired = self._fired(books, now)
        # A. holding: follow the owner book's position; if it closed this step, fall through to C (a trigger on
        #    the very step of the exit is not lost)
        exited = None
        if cb.pos:
            held_by, since = cb.pos.get("src"), cb.pos.get("time_in")
            exited = self._follow(cb, books, ctx)
            if exited is None:
                for m, pe in fired:
                    self._log(ctx, "occupied", book=m["book"], rule=m.get("rule"), key=pe.get("key"), by=held_by, since=since)
                return None
            fired = [(m, pe) for m, pe in fired if m["book"] != held_by]   # the book that just closed cannot re-fire this step
        # B. an owner's entry is pending its first print
        own = cb.ctl.get("owner")
        if own:
            res = self._await_fill(cb, books, ctx, own)
            if res is not None or cb.ctl.get("owner"):
                # filled, or still waiting for the owner's print: other triggers of this step cannot be taken
                for m, pe in fired:
                    if not (m["book"] == own["book"] and pe.get("t") == own["t"]):
                        self._log(ctx, "pending" if res is None else "occupied", book=m["book"], rule=m.get("rule"),
                                  key=pe.get("key"), by=own["book"])
                return res
            # released (lapsed, rejected, unaffordable): the account is flat again on THIS step, so the triggers that
            # fired on it are still admissible (docs/34 F01) — only the released entry itself is spent
            fired = [(m, pe) for m, pe in fired if not (m["book"] == own["book"] and pe.get("t") == own["t"])]
        # C. flat: the first eligible trigger takes the account
        if not self.members:
            self._standing_reason(ctx, "pool empty")
            return exited
        if (ctx.get("blackout") or {}).get("on"):
            self._standing_reason(ctx, "flat: data blackout")
            return exited
        if not fired:
            self._standing_reason(ctx, "flat: no eligible trigger")
            return exited
        eligible = []
        for m, pe in fired:                            # self.members is already in priority order
            msg = None
            if m.get("rule"):
                w = pe.get("weather_trig") or {}
                pattern = rules.entry_pattern(books[m["book"]], ctx, pe.get("why"))
                msg = rules.check_rule(m["rule"], w, ctx, pattern, reg)
            if msg:
                self._log(ctx, "rule_block", book=m["book"], rule=m.get("rule"), key=pe.get("key"), why=msg)
            else:
                eligible.append((m, pe))
        if not eligible:
            self._standing_reason(ctx, "flat: trigger blocked by its rule")
            return exited
        m, pe = eligible[0]
        for m2, pe2 in eligible[1:]:
            self._log(ctx, "lost_priority", book=m2["book"], rule=m2.get("rule"), key=pe2.get("key"), to=m["book"])
        own = {"book": m["book"], "rule": m.get("rule"), "standing": m.get("standing"), "t": pe["t"],
               "time": pe.get("time"), "key": pe["key"], "why": pe.get("why")}
        cb.ctl["owner"] = own
        self._log(ctx, "owner", **own)
        self.reason = f"entry pending via {m['book']}: {pe.get('why')}"
        return exited or ("owner", own)

    def _fired(self, books, now):
        """Pool books whose trigger fired THIS step, in priority order: (entry, pending_entry)."""
        out = []
        for m in self.members:
            b = books.get(m["book"])
            if b is None:
                continue
            pe = b.ctl.get("pending_entry")
            if pe and pe.get("t") == now:
                out.append((m, pe))
            elif not pe and b.pos and b.pos.get("t_in") == now and b.pos.get("trigger_t") in (None, now):
                # a book filled on the trigger print itself (config.FILL_NEXT_PRINT off): treat the fill as the trigger
                p = b.pos
                out.append((m, {"t": now, "time": p.get("time_in"), "key": p["key"], "id": p.get("id"),
                                "why": p.get("why"), "weather_trig": p.get("weather_trig"), "filled": True}))
        return out

    def _await_fill(self, cb, books, ctx, own):
        src = books.get(own["book"])
        pe = src.ctl.get("pending_entry") if src is not None else None
        if pe and pe.get("t") == own["t"]:
            return None                                # still waiting for the first print
        spos = src.pos if src is not None else None
        if spos and (spos.get("trigger_t") == own["t"] or (spos.get("trigger_t") is None and spos.get("t_in") == own["t"])):
            cb.ctl.pop("owner", None)
            pos = self._open(cb, spos, ctx, own)
            if pos is None:
                self._log(ctx, "unaffordable", book=own["book"], rule=own.get("rule"), key=own["key"],
                          why=cb.blocked, capital=cb.capital)
                self.reason = f"flat: {cb.blocked}"
                return None
            self._log(ctx, "entry", book=own["book"], rule=own.get("rule"), key=pos["key"], entry=pos["entry"],
                      lots=pos["lots"], why=pos.get("why"), fill_delay_s=pos.get("fill_delay_s"))
            self.reason = f"holding via {own['book']}"
            return ("entry", pos)
        cb.ctl.pop("owner", None)                      # lapsed or rejected: release at once
        why = (src.blocked if src is not None else "") or "entry lapsed"
        self._log(ctx, "release", book=own["book"], rule=own.get("rule"), key=own["key"], why=why)
        self.reason = f"flat: {own['book']} {why}"
        return None

    def _open(self, cb, spos, ctx, own):
        px = float(spos["entry"])
        lots = int(cb.capital // (px * config.LOT_SIZE))   # all-in on every trade (owner), the Conductor's own capital
        if lots < 1:
            cb.blocked = f"premium ₹{px:.1f} unaffordable"
            return None
        pos = copy.deepcopy(spos)
        pos.pop("pending", None)
        qty = lots * config.LOT_SIZE
        pos.update({"lots": lots, "qty": qty, "slices": -(-qty // config.FREEZE_QTY),
                    "src": own["book"], "rule": own.get("rule"), "standing": own.get("standing")})
        cb.pos = pos
        if pos.get("episode") is not None:
            cb.fired_episodes.add(pos["episode"])
        return pos

    def _follow(self, cb, books, ctx):
        pos = cb.pos
        src = books.get(pos.get("src"))
        spos = src.pos if src is not None else None
        if spos and spos.get("t_in") == pos["t_in"] and spos.get("key") == pos["key"]:
            for k in ("last", "peak_pts", "worst_pts", "best", "trail", "best_spot", "peak_bid", "stale_exit", "rules"):
                if k in spos:
                    pos[k] = spos[k]
            pos["pending"] = copy.deepcopy(spos["pending"]) if spos.get("pending") else None
            if pos["pending"] is None:
                pos.pop("pending", None)
            return None
        # the owner closed (or vanished): the Conductor closes on the same print
        t = None
        if src is not None:
            for x in reversed(src.trades):
                if x.get("t_in") == pos["t_in"] and x.get("key") == pos["key"]:
                    t = x
                    break
        o = (ctx.get("by_key") or {}).get(pos["key"])
        if t is None:
            # docs/34 F04: the source position is gone and no closed trade explains it (a restart lost the book, the
            # book was removed, ...). That is an integrity fault, not an exit. The account stays open, marked
            # unresolved, until a FRESH quote on its own contract exists; it then leaves at that quote as a
            # RECOVERY — an accounting adjustment, flagged on the trade and excluded from scoring — never at a
            # remembered price.
            fresh = o is not None and o.get("ltp") is not None and (o.get("age") or 0.0) <= config.EXIT_QUOTE_STALE_S
            if not pos.get("unresolved"):
                pos["unresolved"] = ctx.get("now_s")
                self._log(ctx, "integrity", book=pos.get("src"), key=pos["key"], t_in=pos["t_in"],
                          why="source position vanished with no closed trade", fresh_quote=fresh)
                self.reason = f"holding via {pos.get('src')} — UNRESOLVED: source position vanished"
            if not fresh:
                return None
            px, reason = float(o["ltp"]), "RECOVERY source lost, fresh quote"
            pos["stale_exit"] = False
        else:
            px, reason = float(t["exit"]), t["reason"]
            for k in ("stale_exit", "exit_fill_delay_s", "exit_trigger_px"):
                if k in t:
                    pos[k] = t[k]
        pos.pop("pending", None)
        closed = paper.close_trade(cb, ctx, float(px), reason, o)
        if t is None:
            closed["adjustment"] = "recovery"          # not a trading fill: scoring leaves it out (conductor/score.py)
            self._log(ctx, "adjustment", book=pos.get("src"), key=pos["key"], exit=px, pnl_rs=closed["pnl_rs"],
                      capital=cb.capital, unresolved_s=round(ctx["now_s"] - (pos.get("unresolved") or ctx["now_s"]), 1))
        if t is not None:                              # the owner's own exit quote, not this step's
            closed["exit_bid"], closed["exit_ask"] = t.get("exit_bid"), t.get("exit_ask")
            closed["exit_quote_age"], closed["time_out"], closed["t_out"] = t.get("exit_quote_age"), t.get("time_out"), t.get("t_out")
            closed["hold_s"] = (t.get("t_out") or ctx["now_s"]) - pos["t_in"]
        self._log(ctx, "exit", book=pos.get("src"), rule=pos.get("rule"), key=pos["key"], exit=px, reason=reason,
                  pnl_rs=closed["pnl_rs"], ret_pct=closed["ret_pct"], capital=cb.capital)
        self.reason = f"flat after {pos.get('src')} {reason}"
        return ("exit", closed)
