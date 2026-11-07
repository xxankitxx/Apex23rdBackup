"""
Step 1 of the Conductor plan, the DIARIES (docs/28 §4). One row per trigger, from a run folder's (or the live data
folder's) paper/<day>.json (every book's trades, B16: never the reduced days.jsonl) and missed_<day>.jsonl (the
missed-signal recorder's counterfactuals).

  python -m apex.conductor.diary DATA_DIR [--out FILE]        (DATA_DIR holds paper/; default out: DATA_DIR/conductor/diary.jsonl)

Each row: day, book, family, side, the weather photograph at the trigger (weather_trig, docs/27), the outcome
(ret_pct and points for the search, rupees reported, minutes held, best / worst points, exit reason, stale fill or
exit, data gap), and the labels:
  * win: closed in profit (ret_pct > 0);
  * loss_kind for a loser: "never_worked" when its best point never reached max(one-third of its FAMILY's median
    winning peak, the BOOK's own stop distance), a weather problem; "gave_back" when it did and still lost, an exit
    problem (§10). The book's stop distance is the median |points| of its losing trades that exited on a stop.
Counterfactual rows (is_counterfactual) carry weight 1.0 when they do not overlap the real trade in time and 0.5 when
they do (they share its outcome); they are for the search only, never for scoring a rule (§4).
Excluded rows stay in the diary with the reason (`excluded`): a quote defect or defect window (defects.Quarantine,
D-101), a trade entered in the closing auction (learning.is_cas_trade), a counterfactual with no outcome.
Families are per row (docs/28 §16a): ep_type, council trades split by their signal into COUNCIL-EXP / COUNCIL-NORM,
t28_fwd as its own family, x day type (EXP / NORM).
"""
import argparse
import glob
import json
import os
import statistics

STOP_WORDS = ("STOP", "SL", "HARD")


def _sec(hms):
    try:
        h, m, s = (str(hms) + ":0:0").split(":")[:3]
        return int(h) * 3600 + int(m) * 60 + int(float(s))
    except (TypeError, ValueError):
        return None


def entry_pattern(book, ep_type, why):
    """The row's entry pattern (docs/28 §16a)."""
    w = str(why or "")
    if w.startswith("COUNCIL EXP"):
        return "COUNCIL-EXP"
    if w.startswith("COUNCIL NORM"):
        return "COUNCIL-NORM"
    if book == "t28_fwd":
        return "FWD-PULLBACK"
    return str(ep_type or "UNKNOWN")


def day_type(t, weather):
    w = weather or {}
    if w.get("expiry_day") is not None:
        return "EXP" if w["expiry_day"] else "NORM"
    if t.get("dte_in") is not None:
        return "EXP" if t["dte_in"] == 0 else "NORM"
    return "UNK"


def load_days(data_dir):
    """{day: {book: book_json}} from paper/<day>.json, and {day: [missed rows]}."""
    pdir = os.path.join(data_dir, "paper") if os.path.isdir(os.path.join(data_dir, "paper")) else data_dir
    books, missed = {}, {}
    for f in sorted(glob.glob(os.path.join(pdir, "????-??-??.json"))):
        day = os.path.basename(f)[:-5]
        try:
            books[day] = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        mp = os.path.join(pdir, f"missed_{day}.jsonl")
        if os.path.exists(mp):
            rows = []
            for line in open(mp, encoding="utf-8"):
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
            missed[day] = rows
    return books, missed


def build(books, missed, controls=None, declared=None):
    """The diary rows (a list of dicts), labelled. `declared` = owner-declared defect windows (defects.load_declared
    of the folder's own learning/defects.json); None = none."""
    from .. import config
    from ..engine import defects
    from ..engine.learning import is_cas_trade
    controls = set(controls if controls is not None else tuple(config.CONTROLS) + ("RAW",))
    qrows = [{"day": d, "book": n, "trades": (b or {}).get("trades") or []} for d, bb in books.items()
             for n, b in bb.items()]
    q = defects.Quarantine(qrows, declared=declared or {})
    rows = []
    real_out = {}
    for day, bb in books.items():
        for name, b in bb.items():
            for i, t in enumerate((b or {}).get("trades") or []):
                wt = t.get("weather_trig")
                fam = entry_pattern(name, t.get("ep_type"), t.get("why"))
                r = {"day": day, "book": name, "n": i, "is_counterfactual": False, "weight": 1.0,
                     "control": name in controls, "pattern": fam, "day_type": day_type(t, wt),
                     "side": t.get("rr"), "time_in": t.get("time_in"), "time_out": t.get("time_out"),
                     "trigger_time": t.get("trigger_time"), "ret_pct": t.get("ret_pct"), "pnl_pts": t.get("pnl_pts"),
                     "pnl_rs": t.get("pnl_rs"), "hold_min": (t["hold_s"] / 60.0) if t.get("hold_s") is not None else None,
                     "peak_pts": t.get("peak_pts"), "worst_pts": t.get("worst_pts"), "reason": t.get("reason"),
                     "stale_exit": bool(t.get("stale_exit")), "fill_delay_s": t.get("fill_delay_s"),
                     "gap": bool(t.get("gap")), "weather": wt}
                why = q.reason(day, t) or ("closing auction" if is_cas_trade(t) else None)
                r["excluded"] = why
                rows.append(r)
                real_out[(day, name, t.get("time_in"))] = _sec(t.get("time_out"))
    for day, ms in missed.items():
        for m in ms:
            fam = entry_pattern(m.get("book"), m.get("ep_type"), m.get("cf_why") or m.get("signal"))
            wt = m.get("weather")
            ro = real_out.get((day, m.get("book"), m.get("real_time_in")))
            ci = _sec(m.get("cf_time_in"))
            overlap = ro is None or ci is None or ci < ro
            ret = m.get("cf_ret_pct")
            r = {"day": day, "book": m.get("book"), "n": m.get("episode_id"), "is_counterfactual": True,
                 "weight": 0.5 if overlap else 1.0, "control": m.get("book") in controls, "pattern": fam,
                 "day_type": day_type({}, wt), "side": m.get("side"), "relation": m.get("relation"),
                 "time_in": m.get("cf_time_in"), "time_out": m.get("cf_time_out"), "trigger_time": m.get("first_fire_time"),
                 "ret_pct": ret, "pnl_pts": None, "pnl_rs": m.get("cf_pnl_rs"),
                 "hold_min": (m["cf_hold_s"] / 60.0) if m.get("cf_hold_s") is not None else None,
                 "peak_pts": m.get("cf_peak_pts"), "worst_pts": m.get("cf_worst_pts"), "reason": m.get("cf_reason"),
                 "stale_exit": bool(m.get("cf_stale_exit")), "fill_delay_s": m.get("cf_fill_delay_s"),
                 "gap": bool(m.get("cf_gap")), "weather": wt,
                 "excluded": None if m.get("cf_status") == "closed" and ret is not None else
                 f"counterfactual {m.get('cf_status') or 'without outcome'}"}
            if r["excluded"] is None and m.get("cf_time_in"):
                tq = {"time_in": m.get("cf_time_in"), "time_out": m.get("cf_time_out")}
                r["excluded"] = q.reason(day, tq) or ("closing auction" if is_cas_trade(tq) else None)
            rows.append(r)
    label(rows)
    return rows


def family(r):
    return f"{r['pattern']}|{r['day_type']}"


def label(rows):
    """win and loss_kind, in place. Thresholds from REAL, kept rows only."""
    peaks, stops = {}, {}
    for r in rows:
        if r["is_counterfactual"] or r["excluded"] or r.get("ret_pct") is None:
            continue
        if r["ret_pct"] > 0 and r.get("peak_pts") is not None:
            peaks.setdefault(family(r), []).append(float(r["peak_pts"]))
        if r["ret_pct"] <= 0 and r.get("pnl_pts") is not None and any(w in str(r.get("reason") or "").upper()
                                                                      for w in STOP_WORDS):
            stops.setdefault(r["book"], []).append(abs(float(r["pnl_pts"])))
    med_peak = {k: statistics.median(v) for k, v in peaks.items() if v}
    med_stop = {k: statistics.median(v) for k, v in stops.items() if v}
    for r in rows:
        ret = r.get("ret_pct")
        r["win"] = None if ret is None else ret > 0
        r["loss_kind"] = None
        r["never_line"] = None
        if r["win"] is False:
            mp = med_peak.get(family(r))
            if mp is None:
                continue
            line = max(mp / 3.0, med_stop.get(r["book"], 0.0))
            r["never_line"] = round(line, 3)
            pk = r.get("peak_pts")
            if pk is not None:
                r["loss_kind"] = "never_worked" if float(pk) < line else "gave_back"
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the Conductor diaries from a data / run folder.")
    ap.add_argument("data_dir")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    from ..engine import defects
    books, missed = load_days(a.data_dir)
    declared, err = defects.load_declared(os.path.join(a.data_dir, "learning", "defects.json"))
    if err:
        print(f"WARNING: declared defects unreadable ({err}); none applied")
    rows = build(books, missed, declared=declared)
    out = a.out or os.path.join(a.data_dir, "conductor", "diary.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    n_ex = sum(1 for r in rows if r["excluded"])
    print(f"diary: {len(rows)} rows ({sum(1 for r in rows if r['is_counterfactual'])} counterfactual, "
          f"{n_ex} excluded) over {len(books)} days -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
