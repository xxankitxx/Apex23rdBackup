"""
The Conductor's account, computed OFFLINE from a run's saved trades (docs/28 §7; apex/engine/conductor.py is the
live path). Because the Conductor only mirrors its pool books — their trigger, their fill, their exit — its day is a
function of the pool books' recorded trades: walk every pool book's trades by trigger time (same tick: the pool
priority), take the first whose rule passes while the account is flat, hold it to its own exit, compound the
Conductor's own capital. Triggers while occupied, lost on priority, blocked by a rule, or unaffordable are counted.

Known difference from the engine: an owner's entry that LAPSED (no print within ENTRY_FILL_MAX_S) occupies the
engine's account for those seconds and leaves no trade behind, so it is invisible here. Everything else agrees to the
trade (tests/test_conductor.py drives both paths on the same synthetic day).

    py -3.13 -m apex.conductor.account_sim OUT_DIR RUN_DIR [RUN_DIR ...] [--pool apex/rules/pool.json] [--asof all|day]
                                           [--vs c20_9x]
"""
import argparse
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from apex import config  # noqa: E402
from apex.conductor import diary  # noqa: E402
from apex.engine import conductor as cond, rules  # noqa: E402


def _trades(books, members, order):
    """Every pool book's trades on one day as (trigger_t, priority, entry, trade)."""
    out = []
    for m in members:
        b = books.get(m["book"])
        if not b:
            continue
        for t in b.get("trades") or []:
            if t.get("entry") is None or t.get("exit") is None or t.get("t_in") is None:
                continue
            trig = t.get("trigger_t") if t.get("trigger_t") is not None else t["t_in"]
            out.append((float(trig), cond.priority_key(m, order), m, t))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def simulate_day(day, books, members, order, reg=None):
    """One day of the Conductor from the pool books' saved trades. Returns the day's record."""
    reg = rules.register_rules() if reg is None else reg
    cap = float(config.START_CAPITAL)
    held = None                     # (trigger_t, t_out, book)
    taken, log = [], []
    counts = {"occupied": 0, "lost_priority": 0, "rule_block": 0, "unaffordable": 0, "pending": 0}
    occupied_s = 0.0
    for trig, _prio, m, t in _trades(books, members, order):
        if held is not None:
            h_trig, h_out, h_book = held
            if trig <= h_trig:                 # the same tick as the taken trigger: lost on priority
                what = "lost_priority"
            elif trig < h_out or (trig == h_out and m["book"] == h_book):
                what = "occupied"
            else:
                held = None
            if held is not None:
                if what == "occupied" and trig < (taken[-1]["t_in"] if taken else h_out):
                    what = "pending"
                counts[what] += 1
                log.append({"t": trig, "event": what, "book": m["book"], "rule": m.get("rule"), "key": t.get("key"),
                            "by": h_book})
                continue
        msg = None
        if m.get("rule"):
            ctx = {"now_dt": datetime.fromtimestamp(trig, config.IST), "episode": None}
            pattern = diary.entry_pattern(m["book"], t.get("ep_type"), t.get("why"))
            msg = rules.check_rule(m["rule"], t.get("weather_trig") or {}, ctx, pattern, reg)
        if msg:
            counts["rule_block"] += 1
            log.append({"t": trig, "event": "rule_block", "book": m["book"], "rule": m.get("rule"), "key": t.get("key"), "why": msg})
            continue
        px = float(t["entry"])
        lots = int(cap // (px * config.LOT_SIZE))
        if lots < 1:
            counts["unaffordable"] += 1
            log.append({"t": trig, "event": "unaffordable", "book": m["book"], "key": t.get("key"), "capital": cap})
            continue
        qty = lots * config.LOT_SIZE
        pnl = round((float(t["exit"]) - px) * qty, 2)
        cap = round(cap + pnl, 2)
        held = (trig, float(t["t_out"]), m["book"])
        occupied_s += float(t["t_out"]) - trig
        taken.append({"src": m["book"], "rule": m.get("rule"), "standing": m.get("standing"), "key": t.get("key"),
                      "strike": t.get("strike"), "rr": t.get("rr"), "trigger_t": trig, "t_in": t["t_in"], "t_out": t["t_out"],
                      "time_in": t.get("time_in"), "time_out": t.get("time_out"), "entry": px, "exit": float(t["exit"]),
                      "lots": lots, "qty": qty, "pnl_rs": pnl, "ret_pct": t.get("ret_pct"), "reason": t.get("reason"),
                      "why": t.get("why"), "capital_after": cap})
    wins = sum(1 for x in taken if x["pnl_rs"] > 0)
    return {"day": day, "trades": taken, "n": len(taken), "wins": wins, "losses": sum(1 for x in taken if x["pnl_rs"] < 0),
            "pnl_rs": round(sum(x["pnl_rs"] for x in taken), 2), "capital_end": cap,
            "ret_day_pct": round(100.0 * (cap / float(config.START_CAPITAL) - 1.0), 3),
            "occupied_min": round(occupied_s / 60.0, 1), "counts": counts, "log": log}


def simulate(days_books, pool, asof="", order=None):
    """{day: record} over several days; the pool as of each day (asof='all': every entry on every day)."""
    out = {}
    for day in sorted(days_books):
        books = days_books[day]
        order_ = order or {n: i for i, n in enumerate(books)}
        members = sorted(cond.active_entries(pool, day, asof), key=lambda e: cond.priority_key(e, order_))
        out[day] = simulate_day(day, books, members, order_)
        out[day]["pool_n"] = len(members)
    return out


def _book_day(books, name):
    b = books.get(name) or {}
    tr = b.get("trades") or []
    return {"n": len(tr), "wins": sum(1 for t in tr if (t.get("pnl_rs") or 0) > 0),
            "pnl_rs": round(sum(float(t.get("pnl_rs") or 0) for t in tr), 2)}


def report(res, days_books, vs="c20_9x", asof="", pool_entries=()):
    bases = sorted({str(e.get("ret_basis") or "unstated") for e in pool_entries}) if pool_entries else []
    lines = ["# The Conductor's account, offline from the run's saved trades", "",
             f"Priority basis of the pool's `ret_per_trade`: {', '.join(bases) or 'no entries'} — forward figures replace "
             "the discovery-day ones as test days are scored.", "",
             f"Pool as of each day{' — EVERY entry on every day (in-sample study)' if asof == 'all' else ''}; "
             f"compared with `{vs}` alone on the same run. Rupees are gross paper results, all-in, ₹{config.START_CAPITAL:,.0f} a day.", "",
             f"| day | pool | trades | wins | losses | P&L ₹ | day % | occupied min | occupied/pending/lost/blocked/unaffordable | {vs} trades | {vs} P&L ₹ |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    tot = {"n": 0, "w": 0, "l": 0, "pnl": 0.0, "vs_n": 0, "vs_pnl": 0.0, "ldays": 0, "vs_ldays": 0}
    for day, r in sorted(res.items()):
        v = _book_day(days_books[day], vs)
        c = r["counts"]
        lines.append(f"| {day} | {r['pool_n']} | {r['n']} | {r['wins']} | {r['losses']} | {r['pnl_rs']:+,.0f} | {r['ret_day_pct']:+.1f} | "
                     f"{r['occupied_min']} | {c['occupied']}/{c['pending']}/{c['lost_priority']}/{c['rule_block']}/{c['unaffordable']} | "
                     f"{v['n']} | {v['pnl_rs']:+,.0f} |")
        tot["n"] += r["n"]; tot["w"] += r["wins"]; tot["l"] += r["losses"]; tot["pnl"] += r["pnl_rs"]
        tot["vs_n"] += v["n"]; tot["vs_pnl"] += v["pnl_rs"]
        tot["ldays"] += 1 if r["pnl_rs"] < 0 else 0; tot["vs_ldays"] += 1 if v["pnl_rs"] < 0 else 0
    lines += ["", f"**Total** Conductor: {tot['n']} trades, {tot['w']} wins, {tot['l']} losses, ₹{tot['pnl']:+,.0f}, "
                  f"{tot['ldays']} losing day(s) of {len(res)}. `{vs}`: {tot['vs_n']} trades, ₹{tot['vs_pnl']:+,.0f}, "
                  f"{tot['vs_ldays']} losing day(s).", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--pool", default=cond.POOL)
    ap.add_argument("--asof", default="", help="'all' = every pool entry on every day (in-sample); default: as of each day")
    ap.add_argument("--vs", default="c20_9x")
    a = ap.parse_args(argv)
    days_books = {}
    for rd in a.run_dirs:
        b, _m = diary.load_days(rd)
        days_books.update(b)
    pool = cond.load_pool(a.pool)
    res = simulate(days_books, pool, a.asof)
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "conductor_sim.json"), "w", encoding="utf-8") as fh:
        json.dump({"pool": pool, "asof": a.asof, "days": res}, fh, indent=1, default=str)
    md = report(res, days_books, a.vs, a.asof, pool.get("entries") or [])
    with open(os.path.join(a.out_dir, "conductor_sim.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    try:                                           # 13 Nov: a cp1252 console cannot print the rupee sign
        print(md)
    except UnicodeEncodeError:
        print(md.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
