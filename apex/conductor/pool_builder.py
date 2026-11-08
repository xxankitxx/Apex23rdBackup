"""
From each book's weather card to a PROPOSED pool (docs/28 §7; owner, 8 Nov: the Conductor runs live on paper from
9 Nov on the pairs the 14-day all-item cards support). Nothing here is applied without `--apply`: the owner reads
the proposal first.

For every searched book whose card has a line that beats luck, the strongest line (largest win-rate gap, kept side
profitable in mean) becomes a register rule — `weather_trig.<factor> <op> <line>`, frozen today, first test day the
next trading day (register.propose: near-duplicates of failed rules are blocked) — and the pair (book, rule) a pool
entry with standing "low" (no pair has a forward pass yet) and ret_per_trade = the kept side's mean return per trade
ON THE DISCOVERY DAYS (in-sample; the forward scoring replaces it). Books with no such line are listed, with their
plain record, for the owner to admit unrestricted (rule null) or leave out; `--include-free BOOK,...` admits them.

    py -3.13 -m apex.conductor.pool_builder OUT_DIR CARDS_JSON [--today 2026-11-08] [--min-kept 20] [--all-lines]
                                            [--include-free c20_9x,...] [--apply]
"""
import argparse
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from apex import config  # noqa: E402
from apex.conductor import register  # noqa: E402
from apex.engine import conductor as cond  # noqa: E402

# docs/34 F02: these photograph fields come from parameters fitted on 5 Nov over sessions through 4 Nov
# (apex/quant/params.json) and are used unchanged on every replayed day, so a line on them is not chronological
# evidence until dated artifacts exist (docs/33 Wave 1). The proposal says so beside every such pair.
FITTED_PREFIXES = ("hmm_", "hk_")
F02 = "model provenance not chronological (docs/34 F02)"


def fitted_factor(factor):
    return str(factor or "").startswith(FITTED_PREFIXES)


def best_line(card, all_lines=False, min_kept=20, allow_fitted=False):
    """The strongest ELIGIBLE line on a card: beats luck (unless all_lines), kept side profitable, enough kept trades,
    and not on a fitted-model factor (docs/34 F02) unless allow_fitted — excluded BEFORE choosing, so a valid
    alternative line on the same card is the one proposed."""
    best = None
    for x in card.get("lines") or []:
        if not all_lines and not x.get("beats_luck"):
            continue
        if not allow_fitted and fitted_factor(x.get("factor")):
            continue
        if x.get("kept_ret") is None or x["kept_ret"] <= 0 or (x.get("kept_n") or 0) < min_kept:
            continue
        if best is None or (x["score"], x["kept_ret"]) > (best["score"], best["kept_ret"]):
            best = x
    return best


def propose(cards, today, all_lines=False, min_kept=20, include_free=(), reg=None, st=None, allow_fitted=False):
    """(rules, entries, free_candidates, skipped): the proposal, nothing written."""
    reg = register.load() if reg is None else reg
    st = register.statuses() if st is None else st
    reg_work = {"rules": list(reg["rules"])}
    rules_out, entries, free, skipped = [], [], [], []
    for book, c in sorted(cards["cards"].items(), key=lambda kv: -(kv[1].get("n_real") or 0)):
        if c.get("skipped") or book in config.CONTROLS or book == cond.BOOK or book not in config.VARIANTS:
            skipped.append((book, "too few rows" if c.get("skipped") else "not a pool candidate"))
            continue
        x = best_line(c, all_lines, min_kept, allow_fitted)
        if x is None:
            free.append({"book": book, "n_real": c["n_real"], "n_days": c["n_days"], "real_win": c["real_win"],
                         "real_mean": c["real_mean"], "never_worked": c["never_worked"], "gave_back": c["gave_back"]})
            if book in include_free:
                entries.append({"book": book, "rule": None, "standing": "low", "ret_per_trade": c["real_mean"],
                                "ret_basis": "discovery days (in-sample)",
                                "from": register.next_trading_day(today).isoformat(),
                                "note": f"unrestricted (owner); {c['n_real']} trades, {c['real_win']:.0%} winners, mean {c['real_mean']:+.1f} % on the discovery days"})
            continue
        reason = (f"book card 8 Nov (all 68 items, {cards.get('perms')} shuffles): kept {x['kept_n']:g} trades, "
                  f"{x['kept_sr']:.0%} winners, mean {x['kept_ret']:+.1f} %; other side {x['other_n']:g}, {x['other_sr']:.0%}, "
                  f"{x['other_ret']:+.1f} %; never-worked losses on the hurt side {x.get('nw_other')} of {x.get('nw_all')}; "
                  f"{'beats' if x.get('beats_luck') else 'does not beat'} luck; item {x.get('item')} {x.get('item_label', '')}")
        try:
            r = register.propose(reg_work, f"BOOK:{book}", x["factor"], x["op"], x["line"], f"{book} via the Conductor pool",
                                 book, reason, today=today, st=st)
        except ValueError as e:
            skipped.append((book, f"rule blocked: {e}"))
            continue
        if fitted_factor(x["factor"]):
            r["provenance"] = F02
        r["item"], r["item_label"], r["card"] = x.get("item"), x.get("item_label"), {k: x[k] for k in
                                                                                     ("kept_n", "kept_sr", "kept_ret", "other_n", "other_sr", "other_ret", "score", "beats_luck")}
        reg_work["rules"].append(r)
        rules_out.append(r)
        entries.append({"book": book, "rule": r["id"], "standing": "low", "ret_per_trade": x["kept_ret"],
                        "ret_basis": "discovery days (in-sample)",     # replaced by "forward" when test days score it
                        "from": r["first_test_day"],
                        "note": f"{x['factor']} {x['op']} {x['line']:g} (item {x.get('item')} {x.get('item_label', '')}); in-sample"
                                + (f"; {F02}" if fitted_factor(x["factor"]) else "")})
    return rules_out, entries, free, skipped


def markdown(rules, entries, free, skipped, today):
    L = [f"# Proposed Conductor pool — {today.isoformat()}", "",
         "Every pair below is a lead found by searching the past (the 14 replayed days). Standing is **low** for all: no "
         "pair has a forward pass yet; `ret_per_trade` is the kept side's mean return per trade on the discovery days and "
         "is replaced by the forward figure as test days arrive. The owner admits, strikes or adds pairs; `--apply` then "
         "freezes the rules in the register and writes the pool.", "",
         f"## {len(entries)} proposed pairs", "",
         "| Book | Rule | Condition at the trigger | Item | Kept: trades, win %, mean | Other side | Beats luck |", "|---|---|---|---|---|---|---|"]
    by = {r["id"]: r for r in rules}
    for e in entries:
        r = by.get(e["rule"])
        if r is None:
            L.append(f"| {e['book']} | — | unrestricted | | | | |")
            continue
        c = r["card"]
        flag = f" **({F02})**" if r.get("provenance") else ""
        L.append(f"| {e['book']} | {r['id']} | `{r['factor']} {r['op']} {r['line']:g}`{flag} | {r.get('item')} {r.get('item_label', '')} | "
                 f"{c['kept_n']:g}, {c['kept_sr']:.0%}, {c['kept_ret']:+.1f} % | {c['other_n']:g}, {c['other_sr']:.0%}, {c['other_ret']:+.1f} % | "
                 f"{'yes' if c['beats_luck'] else 'no'} |")
    L += ["", f"## {len(free)} books with no line beating luck (admit unrestricted, or leave out)", "",
          "| Book | Trades | Days | Win % | Mean % | Never worked | Gave back |", "|---|---|---|---|---|---|---|"]
    for f in free:
        L.append(f"| {f['book']} | {f['n_real']} | {f['n_days']} | {f['real_win']:.0%} | {f['real_mean']:+.1f} | {f['never_worked']} | {f['gave_back']} |")
    if skipped:
        L += ["", "## Not proposed", ""] + [f"- {b}: {why}" for b, why in skipped]
    return "\n".join(L) + "\n"


def apply(rules, entries, pool_path=cond.POOL, reg_path=None):
    for r in rules:
        r = {k: v for k, v in r.items() if k != "card"}
        register.add(r, reg_path or register.REGISTER)
    pool = cond.load_pool(pool_path)
    pool.setdefault("entries", []).extend(entries)
    with open(pool_path, "w", encoding="utf-8") as fh:
        json.dump(pool, fh, indent=1, ensure_ascii=False)
    return pool


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("cards_json")
    ap.add_argument("--today", default=date.today().isoformat())
    ap.add_argument("--min-kept", type=int, default=20)
    ap.add_argument("--all-lines", action="store_true", help="also lines that do not beat luck")
    ap.add_argument("--include-free", default="", help="books to admit unrestricted, comma-separated")
    ap.add_argument("--allow-fitted", action="store_true", help="also lines on HMM / Hawkes factors (docs/34 F02: not chronological)")
    ap.add_argument("--apply", action="store_true", help="freeze the rules in the register and write the pool")
    a = ap.parse_args(argv)
    today = date.fromisoformat(a.today)
    cards = json.load(open(a.cards_json, encoding="utf-8"))
    free_in = tuple(x for x in a.include_free.split(",") if x)
    rules, entries, free, skipped = propose(cards, today, a.all_lines, a.min_kept, free_in, allow_fitted=a.allow_fitted)
    os.makedirs(a.out_dir, exist_ok=True)
    md = markdown(rules, entries, free, skipped, today)
    open(os.path.join(a.out_dir, "pool_proposal.md"), "w", encoding="utf-8").write(md)
    json.dump({"today": a.today, "rules": rules, "entries": entries, "free": free, "skipped": skipped},
              open(os.path.join(a.out_dir, "pool_proposal.json"), "w", encoding="utf-8"), indent=1, default=str)
    print(md)
    if a.apply:
        pool = apply(rules, entries)
        probs = cond.pool_problems(pool)
        print(f"applied: {len(rules)} rules added to the register, pool now {len(pool['entries'])} entries; problems: {probs or 'none'}")
        return 1 if probs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
