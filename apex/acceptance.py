"""
Acceptance check on a replayed day (D-119, council 4 m27 OP-1).

A code version may trade live only after it has replayed recorded days and passed these BEHAVIOUR checks.
They are not profit targets — one day cannot prove an edge (m21) — they catch the failure modes of 19 Oct:
  * churn                : champion entries per hour, entries in any 30 min, median hold;
  * flips                : an opposite-direction entry within the cool-down after an exit;
  * expiry rules         : only the expiring weekly on expiry day, no entry after the expiry entry end;
  * brakes               : only when the owner has set them (D-123): no entry after a daily stop / streak stop / entry cap;
  * frozen quotes        : no trade priced on a quote whose exchange stamp is older than QUOTE_DEFECT_AGE_S;
  * data health          : the run's event tape shows no long feed silence.

Usage: python run_apex.py acceptance data/ticks/2026-10-19.jsonl.gz   (replays lock-step, then checks)
       python -m apex.acceptance <run folder>                           (check an existing replay folder)
"""
import glob
import json
import os
import sys
from datetime import datetime
from statistics import median

from . import config
from .engine import defects

LIMITS = {                          # the domino champion (19 Oct: 19 entries 12:47-15:29, median hold 30 s)
    "entries_per_hour": 6,          # champion, any clock hour
    "entries_per_30min": 4,         # champion, any 30-minute window
    "median_hold_s": 60,            # champion, over the day (if >= 3 trades)
}
LIMITS_SPOT = {                     # D-124: the spot-breakout champion trades every 12-min range break by design
    "entries_per_hour": 12,         # (19 Oct replay: at most 8 in any hour, 6 in any 30 min, holds 16 s - 11 min)
    "entries_per_30min": 8,
    "median_hold_s": 0,             # a 16-s trail exit is its rule, not churn
}


def _secs(hms):
    h, m, s = (int(x) for x in str(hms).split(":")[:3])
    return h * 3600 + m * 60 + s


def check_books(books, day, champion="m2.0_s0.5", w0=None):
    """books = the paper/<day>.json dict. Returns (failures, notes)."""
    fails, notes = [], []
    w0 = w0 or day                                    # caller passes the weekly expiry when known
    expiry_day = (w0 == day)
    for name, b in books.items():
        trades = b.get("trades") or []
        ctl = name in config.CONTROLS
        p = b.get("p") or {}
        # frozen quotes — every book
        for t in trades:
            q = defects.quote_defect(t)
            if q:
                fails.append(f"{name} {t.get('time_in')}: priced on a stale quote ({q})")
        if ctl or name == "RAW":
            continue
        # expiry rules
        if expiry_day:
            end = config.EXPIRY_ENTRY_END
            for t in trades:
                if t.get("expiry") and t["expiry"] != w0 and not config.ZERO_DTE_USE_NEXTWEEK:
                    fails.append(f"{name} {t['time_in']}: bought {t['expiry']} on the {w0} expiry day")
                if end and not p.get("expiry_window_exempt") and _secs(t["time_in"]) >= end[0] * 3600 + end[1] * 60:
                    fails.append(f"{name} {t['time_in']}: entry after the expiry entry end {end[0]:02d}:{end[1]:02d}")
        # brakes
        cap = 0 if p.get("no_trade_cap") else config.MAX_ENTRIES_PER_DAY
        if cap and len(trades) > cap:
            fails.append(f"{name}: {len(trades)} entries > cap {cap}")
        stop_on = config.DAILY_LOSS_STOP_PCT > 0                  # D-123: the brakes are owner-set, off by default
        cap_rs = config.START_CAPITAL * (1 - config.DAILY_LOSS_STOP_PCT / 100.0)
        n = 0 if p.get("no_streak_pause") else config.LOSS_STREAK_N
        streak = 0
        for i, t in enumerate(trades[:-1]):
            after = trades[i + 1]
            if stop_on and t.get("capital_after") is not None and t["capital_after"] <= cap_rs:
                fails.append(f"{name} {after['time_in']}: entered after the daily stop (capital {t['capital_after']:.0f})")
                break
            streak = streak + 1 if t["ret_pct"] <= 0 else 0
            if n and streak >= n and config.LOSS_STREAK_PAUSE_S <= 0:
                fails.append(f"{name} {after['time_in']}: entered after {n} losses in a row")
                break
        # flips inside the cool-down
        cool = p.get("cooldown_s", config.REENTRY_COOLDOWN_S)
        for a, c in zip(trades, trades[1:]):
            if cool and a.get("time_out") and _secs(c["time_in"]) - _secs(a["time_out"]) < cool - 1:
                fails.append(f"{name} {c['time_in']}: re-entered {_secs(c['time_in']) - _secs(a['time_out'])} s after an exit")
    # churn — champion
    cb = books.get(champion) or {}
    ch = cb.get("trades") or []
    lim = LIMITS_SPOT if (cb.get("p") or {}).get("spot_dc") else LIMITS
    ts = sorted(_secs(t["time_in"]) for t in ch)
    for i, t0 in enumerate(ts):
        n60 = sum(1 for x in ts[i:] if x < t0 + 3600)
        n30 = sum(1 for x in ts[i:] if x < t0 + 1800)
        if n60 > lim["entries_per_hour"]:
            fails.append(f"{champion}: {n60} entries within an hour from {t0 // 3600:02d}:{t0 % 3600 // 60:02d}")
            break
        if n30 > lim["entries_per_30min"]:
            fails.append(f"{champion}: {n30} entries within 30 min from {t0 // 3600:02d}:{t0 % 3600 // 60:02d}")
            break
    if len(ch) >= 3 and lim["median_hold_s"]:
        mh = median(t.get("hold_s") or 0 for t in ch)
        if mh < lim["median_hold_s"]:
            fails.append(f"{champion}: median hold {mh:.0f} s < {lim['median_hold_s']} s")
    for name, b in sorted(books.items()):
        tr = b.get("trades") or []
        notes.append(f"{name:22s} trades {len(tr):3d}  wins {sum(1 for t in tr if t['ret_pct'] > 0):3d}  "
                     f"capital ₹{b.get('capital', 0):>11,.0f}")
    return fails, notes


def check_run(run_dir, champion=None):
    paper = os.path.join(run_dir, "paper")
    files = sorted(glob.glob(os.path.join(paper, "20??-??-??.json")))
    if not files:
        return [f"no paper books in {paper}"], []
    fails, notes = [], []
    for f in files:
        day = os.path.basename(f)[:-5]
        books = json.load(open(f, encoding="utf-8"))
        try:
            w0 = str(config.weekly_expiries(datetime.fromisoformat(day + "T10:00:00+05:30"), 1)[0])
        except Exception:
            w0 = None
        champ = champion or (next((n for n, b in books.items() if n == config.CHAMPION_DEFAULT), None)) or config.CHAMPION_DEFAULT
        ff, nn = check_books(books, day, champ, w0)
        fails += [f"{day}: {x}" for x in ff]
        notes += [f"{day}: {x}" for x in nn]
        ev = os.path.join(paper, f"events_{day}.jsonl")
        if os.path.exists(ev):
            gaps = [json.loads(l) for l in open(ev, encoding="utf-8") if '"GAP"' in l]
            starts = [g for g in gaps if "data gap" in g.get("x", "")]
            if len(starts) > 10:
                fails.append(f"{day}: {len(starts)} data-gap blackouts (feed or guard problem)")
    return fails, notes


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python -m apex.acceptance <replay run folder>")
    fails, notes = check_run(sys.argv[1])
    print("\n".join(notes))
    print()
    if fails:
        print("ACCEPTANCE: FAIL")
        for f in fails:
            print("  - " + f)
        sys.exit(1)
    print("ACCEPTANCE: PASS (behaviour only — not a profit claim)")


if __name__ == "__main__":
    main()
