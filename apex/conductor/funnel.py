"""The opportunity funnel of one Conductor account for one day (15 Nov 2026, owner: "Yes, start"; docs/63 section 1, docs/64).

Where did the day go, and what happened to every moment a pool book fired? Built from the account's own log
(data/paper/<account>_<day>.jsonl, written by apex/engine/conductor.py). Report only: it reads a file and changes nothing.

    time      holding a trade / waiting for a fill / flat (by the reason the account gave) / not running
    triggers  moments a pool book fired -> taken by the account -> filled -> closed in profit
              and, for those not taken or not filled, why (occupied, lost on priority, refused by a rule, unaffordable,
              released because the order never filled)

What it cannot see: a market move that fired NO pool book is not in this log. That needs the decision ledger of docs/63
section 5.1 and is not built.

15 Nov, later (docs/64 section 6): an entry released without a fill is sorted by WHY it lapsed. On 9 Nov all 36 lapses
read "no print within 3 s", and the recorded ticks show every one of those options had a fresh row within a second of
its trigger: the engine's own step took 3 to 7 s that afternoon, so its first look came after the window had closed. A
lapse is "the engine was late" when the reason carries paper.py's stall tag (10 Nov on) or the release came more than
LATE_S after the window closed (a healthy engine releases within a tick of it).

    py -3.13 -m apex.conductor.funnel 2026-11-09 [account]
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from apex import config  # noqa: E402

OPEN_S, CLOSE_S = 9 * 3600 + 15 * 60, 15 * 3600 + 30 * 60        # the session the books trade in, seconds of the day
TRIGGERS = ("owner", "occupied", "pending", "lost_priority", "rule_block", "unaffordable")
NOT_RUNNING = "engine not running"
LATE_S = 0.5                                   # a release this long after the fill window closed: the engine was late
LAPSE_LATE = "entry lapsed: the engine itself was late"
LAPSE_GAP = "entry lapsed: data gap"
LAPSE_QUIET = "entry lapsed: no print in time"


def lapse_kind(why, wait):
    """which of the three lapses a release was: a data gap, the engine's own delay, or a quiet option. Any other
    reason (a rejection, ...) is returned as written."""
    why = str(why or "released")
    if not why.startswith("entry lapsed"):
        return why
    if "data gap" in why:
        return LAPSE_GAP
    if "[engine stalled" in why or "the engine looked" in why or (
            wait is not None and wait > config.ENTRY_FILL_MAX_S + LATE_S):
        return LAPSE_LATE
    return LAPSE_QUIET


def read_log(day, account="conductor", paper_dir=None):
    """the account's log rows for the day, in time order ([] when there is no log)."""
    p = os.path.join(paper_dir or config.PAPER_DIR, f"{account}_{day}.jsonl")
    rows = []
    try:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                    r["t"] = float(r["t"])
                except (ValueError, TypeError, KeyError):
                    continue                          # a torn line is skipped, never guessed
                rows.append(r)
    except OSError:
        return []
    rows.sort(key=lambda r: r["t"])
    return rows


def _day_start(day):
    y, m, d = (int(x) for x in day.split("-"))
    return datetime(y, m, d, tzinfo=config.IST).timestamp()


def funnel(rows, day):
    """{"seconds": {state: s}, "events": Counter, "moments": n, ...} for one day's rows (see the module text)."""
    t0 = _day_start(day)
    a, b = t0 + OPEN_S, t0 + CLOSE_S
    sec = Counter()
    state, last = NOT_RUNNING, a

    def spend(until):
        nonlocal last
        u = min(max(until, a), b)
        if u > last:
            sec[state] += u - last
            last = u

    ev = Counter()
    fired, owned, took = Counter(), Counter(), Counter()
    lapse_why, lapse_keys = Counter(), set()
    moments = set()
    closed = winners = 0
    own_t, waits = None, []                           # the trigger the account is waiting on; seconds to each release
    late_fills = []                                   # fills that came from a look after the window (15 Nov rule)
    for r in rows:
        e, t = r.get("event"), r["t"]
        spend(t)
        ev[e] += 1
        if e in TRIGGERS:
            moments.add(round(t, 3))                  # sibling books firing on one step are one moment
            fired[r.get("book")] += 1
        if e == "flat":
            if state not in ("holding a trade", "waiting for a fill"):
                state = str(r.get("why") or "flat")
        elif e == "owner":
            owned[r.get("book")] += 1
            own_t = t
            state = "waiting for a fill"
        elif e == "entry":
            took[r.get("book")] += 1
            try:
                if float(r.get("fill_delay_s") or 0.0) > config.ENTRY_FILL_MAX_S:
                    late_fills.append(float(r["fill_delay_s"]))
            except (TypeError, ValueError):
                pass
            own_t = None
            state = "holding a trade"
        elif e in ("release", "unaffordable"):
            if e == "release":
                wait = (t - own_t) if own_t is not None else None
                kind = lapse_kind(r.get("why"), wait)
                lapse_why[kind] += 1
                if wait is not None and kind in (LAPSE_LATE, LAPSE_QUIET):
                    waits.append(wait)
                lapse_keys.add(r.get("key"))
            own_t = None
            state = "flat: no eligible trigger"
        elif e in ("exit", "adjustment"):
            if e == "exit":
                closed += 1
                try:
                    winners += float(r.get("ret_pct") or 0.0) > 0
                except (TypeError, ValueError):
                    pass
            state = "flat: no eligible trigger"
    if rows and rows[-1]["t"] < b - 120.0:            # the log stops well before the close: the engine stopped
        spend(rows[-1]["t"] + 60.0)
        state = NOT_RUNNING
    spend(b)
    return {"day": day, "seconds": dict(sec), "events": dict(ev), "moments": len(moments), "fired": dict(fired),
            "owned": dict(owned), "took": dict(took), "closed": closed, "winners": int(winners),
            "lapse_why": dict(lapse_why), "lapse_contracts": len(lapse_keys - {None}),
            "engine_late": lapse_why.get(LAPSE_LATE, 0), "lapse_waits": sorted(waits), "late_fills": sorted(late_fills)}


def lines(day, account="conductor", paper_dir=None):
    """the funnel as report lines (markdown). One short line when the account has no log for the day."""
    rows = read_log(day, account, paper_dir)
    out = ["", f"## Where `{account}`'s day went on {day} (report only)", ""]
    if not rows:
        return out + ["No log for this account on this day."]
    f = funnel(rows, day)
    total = float(CLOSE_S - OPEN_S)
    order = ["holding a trade", "waiting for a fill"] + sorted(
        k for k in f["seconds"] if k not in ("holding a trade", "waiting for a fill", NOT_RUNNING)) + [NOT_RUNNING]
    out += ["| State, 09:15 to 15:30 | Minutes | Share |", "|---|---|---|"]
    for k in order:
        s = f["seconds"].get(k, 0.0)
        if s > 0 or k == "holding a trade":
            out.append(f"| {k[0].upper() + k[1:]} | {s / 60.0:.0f} | {100.0 * s / total:.0f} % |")
    e = f["events"]
    own, fill, rel = e.get("owner", 0), e.get("entry", 0), e.get("release", 0)
    out += ["", "| What happened to the pool's triggers | Count |", "|---|---|",
            f"| Moments a pool book fired (sibling books on one second count once) | {f['moments']} |",
            f"| Taken by the account | {own} |",
            f"| ... filled | {fill} |",
            f"| ... released without a fill | {rel} |",
            f"| Not taken: the account was occupied | {e.get('occupied', 0) + e.get('pending', 0)} |",
            f"| Not taken: refused by a rule or policy | {e.get('rule_block', 0)} |",
            f"| Not taken: one lot was unaffordable | {e.get('unaffordable', 0)} |",
            f"| Trades closed | {f['closed']}, {f['winners']} in profit |"]
    if rel:
        why = "; ".join(f"{n} x {w}" for w, n in sorted(f["lapse_why"].items(), key=lambda x: -x[1]))
        out += ["", f"Released without a fill: {why}, on {f['lapse_contracts']} contract(s). "
                    f"Of {own} triggers the account took, {fill} filled ({100.0 * fill / max(own, 1):.0f} %)."]
        w = f["lapse_waits"]
        if f["engine_late"] and w:                    # w is empty when a torn log lost the "owner" rows
            out += ["", f"**{f['engine_late']} of these were lost to the engine's own delay, not to the market.** "
                        f"The fill window is {config.ENTRY_FILL_MAX_S:.0f} s; the account let go {w[0]:.1f} to {w[-1]:.1f} s "
                        f"after the trigger (median {w[len(w) // 2]:.1f} s). Read the tick-time lines of the engine log "
                        f"for these minutes before anything else."]
    books = sorted(set(f["fired"]) | set(f["took"]), key=lambda k: -f["took"].get(k, 0))
    if f["late_fills"]:
        lf = f["late_fills"]
        out += ["", f"**{len(lf)} of the {fill} fills came from a late look**: the engine first saw the entry "
                    f"{lf[0]:.1f} to {lf[-1]:.1f} s after its trigger, past the {config.ENTRY_FILL_MAX_S:.0f} s window. "
                    f"Under the rule of 15 Nov the entry was kept and filled at the price then on the screen "
                    f"(`late_entry` on the trade). Before it these were lost. The engine was slow at those seconds: "
                    f"read the tick-time lines."]
    if books:
        out += ["", "| Pool book | Times it fired | Times the account chose it | Trades it gave the account |", "|---|---|---|---|"]
        out += [f"| {k} | {f['fired'].get(k, 0)} | {f['owned'].get(k, 0)} | {f['took'].get(k, 0)} |" for k in books]
    out += ["", "A market move that fired no pool book is not counted here."]
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print("\n".join(lines(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "conductor")))
