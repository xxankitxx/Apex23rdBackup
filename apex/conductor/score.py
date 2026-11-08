"""
Scoring a frozen rule: its RESTRICTED book against its FREE book on test days only, with the promotion standard of
docs/28 §2 (rule level). Reads a data folder's paper/<day>.json (a replay run folder or the live data folder).

  python -m apex.conductor.score DATA_DIR [--rule R-002] [--record]

Windows (§6): the first window is 30 restricted trades or 15 trading days, whichever comes LATER, from the rule's
first test day; the second window is the same length again, right after it. A window is never extended: when it is
complete the rule passes or fails on it. A pass in the first window = "passed_first_window" (low priority in the
pool); a pass in the second too = "full_standing". Any fail = "failed".

The tests, all on the window's test days, all must pass:
  1 wins more often: the restricted strike rate beats the 95th percentile of the strike rates of random sets of the
    free book's trades of the same size (membership permutation; a day-level permutation for day-type rules);
  2 makes more: the same for the mean return per trade (ret_pct; rupees are reported, never tested);
  3 makes money: the restricted book's own return (learning._day_ret, the all-in log growth) is positive, also with
    its best trade removed and with its best day removed;
  4 not one win: it stays ahead of the free book (total return) with its best trade removed, and with its best day;
  5 keeps the big wins: it took at least two-thirds of the free book's top 10 % of trades by return (same day, same
    side, entered within 60 s);
  5b no worse on bad days: its worst day is no worse than the free book's worst day;
  6 trades enough: exempt at rule level (a rule is a filter); the window's minimum sample applies instead;
  7 holds over time: the two windows.
Evidence hygiene as everywhere else: quote-defect / defect-window trades (defects.Quarantine) and closing-auction
entries (learning.is_cas_trade) are not evidence; a quarantined whole day is not a test day.
After a pass, the WATCH (§6): two betting e-values on the daily differences d = restricted - free from the pass day:
e(d) "still earning its place", e(-d) "switch-off" (off at 20).
"""
import argparse
import json
import os
import zlib

import numpy as np

FIRST_TRADES, FIRST_DAYS = 30, 15
PERMS = 2000
BIG_SHARE, BIG_TOP, TAKE_S = 2.0 / 3.0, 0.10, 60.0
SWITCH_OFF_E = 20.0


def _ok_trades(trades, day, q, is_cas):
    return [t for t in trades or [] if t.get("ret_pct") is not None and not q.reason(day, t) and not is_cas(t)
            and not t.get("adjustment")]      # docs/34 F04: a recovery exit is an accounting adjustment, not a fill


def evidence(books, rb, fb, days, declared=None):
    """{day: (restricted trades, free trades)} on the given days, evidence-clean; whole quarantined days dropped."""
    from ..engine import defects
    from ..engine.learning import is_cas_trade
    rows = [{"day": d, "book": n, "trades": (b or {}).get("trades") or []}
            for d in days for n, b in (books.get(d) or {}).items()]
    q = defects.Quarantine(rows, declared=declared or {})
    out = {}
    for d in days:
        if q.whole_day(d):
            continue
        bb = books.get(d) or {}
        out[d] = (_ok_trades((bb.get(rb) or {}).get("trades"), d, q, is_cas_trade),
                  _ok_trades((bb.get(fb) or {}).get("trades"), d, q, is_cas_trade))
    return out


def windows(ev_days, ev, first_test_day):
    """[(start, end, complete?) for window 1 and 2] over the evidence days from first_test_day on."""
    days = [d for d in sorted(ev_days) if d >= first_test_day]
    out, i = [], 0
    for _ in range(2):
        n_tr, j = 0, i
        while j < len(days):
            n_tr += len(ev[days[j]][0])
            j += 1
            if j - i >= FIRST_DAYS and n_tr >= FIRST_TRADES:
                break
        complete = j - i >= FIRST_DAYS and n_tr >= FIRST_TRADES
        out.append((days[i:j], complete))
        if not complete:
            break
        i = j
    return out


def _dr(trades):
    from ..engine.learning import _day_ret
    return _day_ret(trades)


def _rng(key):
    return np.random.default_rng(zlib.crc32(key.encode()))


def tests(ev, days, key, day_level=False, perms=PERMS):
    """The promotion standard on one window. Returns {test: (passed, detail)} and a summary."""
    R = [(d, t) for d in days for t in ev[d][0]]
    F = [(d, t) for d in days for t in ev[d][1]]
    res = {}
    nR, nF = len(R), len(F)
    if nR == 0 or nF == 0:
        return {"sample": (False, f"{nR} restricted / {nF} free trades")}, {"n_r": nR, "n_f": nF}
    rr = np.array([t["ret_pct"] for _, t in R], float)
    fr = np.array([t["ret_pct"] for _, t in F], float)
    sr_r, sr_f = float((rr > 0).mean()), float((fr > 0).mean())
    rng = _rng(key)
    if day_level:                                    # draw whole free-book days, as many as the restricted book had
        fdays = [d for d in days if ev[d][1]]
        k = max(1, len({d for d, _ in R}))
        sims = []
        for _ in range(perms):
            pick = rng.choice(len(fdays), size=min(k, len(fdays)), replace=False)
            x = np.array([t["ret_pct"] for i in pick for t in ev[fdays[i]][1]], float)
            sims.append(((x > 0).mean(), x.mean()) if x.size else (0.0, 0.0))
    else:
        sims = []
        for _ in range(perms):
            pick = rng.choice(nF, size=nR, replace=nR > nF)
            x = fr[pick]
            sims.append(((x > 0).mean(), x.mean()))
    sims = np.array(sims)
    p_sr, p_ret = float(np.quantile(sims[:, 0], 0.95)), float(np.quantile(sims[:, 1], 0.95))
    res["1_strike_rate"] = (sr_r > p_sr, f"{sr_r:.1%} vs luck 95th pct {p_sr:.1%} (free book {sr_f:.1%})")
    res["2_return"] = (float(rr.mean()) > p_ret, f"{rr.mean():+.3f} % per trade vs luck {p_ret:+.3f} % "
                                                 f"(free {fr.mean():+.3f} %)")
    dr_r = {d: _dr(ev[d][0]) for d in days}
    dr_f = {d: _dr(ev[d][1]) for d in days}
    tot_r, tot_f = sum(dr_r.values()), sum(dr_f.values())
    bi = int(np.argmax(rr))
    bd, bt = R[bi]
    no_best_trade = tot_r - dr_r[bd] + _dr([t for t in ev[bd][0] if t is not bt])
    best_day = max(dr_r, key=dr_r.get)
    no_best_day = tot_r - dr_r[best_day]
    res["3_positive"] = (tot_r > 0 and no_best_trade > 0 and no_best_day > 0,
                         f"{tot_r:+.2f}; without its best trade {no_best_trade:+.2f}; without its best day "
                         f"{no_best_day:+.2f}")
    res["4_not_one_win"] = (no_best_trade > tot_f and no_best_day > tot_f,
                            f"free {tot_f:+.2f}; restricted without best trade {no_best_trade:+.2f}, without best day "
                            f"{no_best_day:+.2f}")
    k = max(1, int(round(BIG_TOP * nF)))
    big = [F[i] for i in np.argsort(-fr, kind="stable")[:k] if fr[i] > 0]

    def took(d, t):
        return any(x.get("rr") == t.get("rr") and x.get("t_in") is not None and t.get("t_in") is not None
                   and abs(float(x["t_in"]) - float(t["t_in"])) <= TAKE_S for x in ev[d][0])
    kept = sum(1 for d, t in big if took(d, t))
    res["5_big_wins"] = (not big or kept >= BIG_SHARE * len(big), f"{kept} of the free book's {len(big)} biggest wins")
    wr, wf = min(dr_r.values()), min(dr_f.values())
    res["5b_worst_day"] = (wr >= wf, f"worst day {wr:+.2f} vs free {wf:+.2f}")
    summ = {"n_r": nR, "n_f": nF, "days": len(days), "sr_r": round(sr_r, 4), "sr_f": round(sr_f, 4),
            "ret_r": round(float(rr.mean()), 4), "ret_f": round(float(fr.mean()), 4),
            "tot_r": round(tot_r, 3), "tot_f": round(tot_f, 3),
            "rs_r": round(sum(t.get("pnl_rs") or 0 for _, t in R), 0),
            "rs_f": round(sum(t.get("pnl_rs") or 0 for _, t in F), 0)}
    return res, summ


def watch(ev, since):
    """The two e-values on the daily differences from `since` (the pass day) on."""
    from ..engine.learning import e_value_mean_le0
    d = [_dr(ev[x][0]) - _dr(ev[x][1]) for x in sorted(ev) if x >= since]
    up, down = e_value_mean_le0(d), e_value_mean_le0([-x for x in d])
    return {"days": len(d), "e_earning": round(up, 3), "e_switch_off": round(down, 3), "switch_off": down >= SWITCH_OFF_E}


def score_rule(rule, books, declared=None, day_level=False, perms=PERMS, status=None):
    from .. import config
    days = sorted(d for d in books if d >= rule["first_test_day"] and config.is_trading_day(
        __import__("datetime").date.fromisoformat(d)))
    ev = evidence(books, rule["restricted_book"], rule["free_book"], days, declared)
    ws = windows(list(ev), ev, rule["first_test_day"])
    out = {"id": rule["id"], "name": rule["name"], "restricted": rule["restricted_book"], "free": rule["free_book"],
           "test_days": len(ev), "windows": []}
    verdict = "under_test"
    for k, (wd, complete) in enumerate(ws, 1):
        res, summ = tests(ev, wd, f"{rule['id']}#{k}", day_level, perms) if wd else ({}, {})
        passed = complete and bool(res) and all(v[0] for v in res.values())
        out["windows"].append({"window": k, "from": wd[0] if wd else None, "to": wd[-1] if wd else None,
                               "complete": complete, "passed": passed if complete else None, "summary": summ,
                               "tests": {n: {"pass": bool(v[0]), "detail": v[1]} for n, v in res.items()}})
        if not complete:
            break
        if not passed:
            verdict = "failed"
            break
        verdict = "passed_first_window" if k == 1 else "full_standing"
    out["verdict"] = verdict
    if verdict in ("passed_first_window", "full_standing"):
        since = out["windows"][0]["to"]
        w = watch(ev, since)
        out["watch"] = w
        if w["switch_off"]:
            out["verdict"] = "off"
    return out


def score_all(reg, books, declared=None, only=None, perms=PERMS):
    out = []
    for r in reg["rules"]:
        if only and r["id"] not in only:
            continue
        if r.get("kind") != "entry" or " " in r["restricted_book"] or " " in r["free_book"]:
            out.append({"id": r["id"], "name": r["name"], "verdict": "not scored",
                        "why": "restricted / free book named per family (scored on each representative pair)"})
            continue
        out.append(score_rule(r, books, declared, perms=perms))
    return out


def expand_family_rules(reg):
    """R-002..R-005 name their books per family: one scorable pair per registered restricted book."""
    from .. import config
    rules = []
    for r in reg["rules"]:
        reps = getattr(config, "RESTRICTED", {}).get(r["id"])
        if reps and " " in r["restricted_book"]:
            for rep in reps:
                rules.append(dict(r, id=f"{r['id']}/{rep}", restricted_book=f"{rep}_r{r['id'][2:]}", free_book=rep))
        else:
            rules.append(r)
    return dict(reg, rules=rules)


def main(argv=None):
    from ..engine import defects
    from . import register
    from .diary import load_days
    ap = argparse.ArgumentParser(description="Score every frozen rule on its test days (docs/28 §2, §6).")
    ap.add_argument("data_dir")
    ap.add_argument("--rule", action="append", default=None)
    ap.add_argument("--record", action="store_true", help="write status changes to apex/rules/status.jsonl")
    a = ap.parse_args(argv)
    books, _ = load_days(a.data_dir)
    declared, _err = defects.load_declared(os.path.join(a.data_dir, "learning", "defects.json"))
    reg = expand_family_rules(register.load())
    res = score_all(reg, books, declared, only=a.rule)
    for r in res:
        w = r.get("windows") or []
        last = w[-1] if w else {}
        print(f"{r['id']:<28} {r['verdict']:<20} test days {r.get('test_days', '-'):>3}  "
              + (f"window {last.get('window')}: {last.get('summary', {}).get('n_r', 0)} trades"
                 + (" (complete)" if last.get("complete") else " (still filling)") if w else r.get("why", "")))
    if a.record:
        st = register.statuses()
        base = register.load()
        ids = {x["id"] for x in base["rules"]}
        for r in res:
            rid = r["id"].split("/")[0]
            if rid in ids and "/" not in r["id"] and r["verdict"] not in ("under_test", "not scored") \
                    and (st.get(rid) or {}).get("status") != r["verdict"]:
                last = (r.get("windows") or [{}])[-1]
                register.record_status(rid, r["verdict"], last.get("to") or "", "scored", reg=base)
    out = os.path.join(a.data_dir, "conductor")
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, "scores.json"), "w", encoding="utf-8"), indent=1, default=str)
    print(f"-> {os.path.join(out, 'scores.json')}")
    print(register.luck_line(base if a.record else register.load()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
