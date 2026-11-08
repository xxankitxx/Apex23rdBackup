"""Independent re-verification of the team's two surviving leads with the shared toolkit (rule_lab), nothing copied
from the agents' scripts. Frozen rules evaluated, the search that would find them re-run on shuffled labels,
and the same rule tried on the sibling books it was NOT found on."""
import sys, json
sys.path.insert(0, r"C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/team")
import numpy as np
import rule_lab as rl

OUT = r"C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/team/verify_leads"
L = ["# Independent re-verification of the two leads (rule_lab, 300 shufflings, seed 3)", ""]


def search_single9(X, f, y, min_keep=20):
    return rl.best_single(X, f, y, min_keep=min_keep, n_lines=9)


def check(book, rule, min_keep=20, note=""):
    T = rl.load_book(book)
    disc, hold = rl.split_days(T)
    ev = rl.evaluate(T, rule, disc, hold)
    Td = [T[i] for i in disc]
    X, f, y = rl.matrix(Td)
    real = search_single9(X, f, y, min_keep)
    # the frozen rule's own score on discovery, under the same scoring
    m = rl.keep_mask(Td, rule)
    sc_rule, *_ = rl.score_masks(m[None, :], y, min_keep)
    p, med, mx = rl.shuffle_p(search_single9, X, f, y, float(sc_rule[0]), n=300, seed=3, min_keep=min_keep)
    L.append(rl.card_markdown(book, ev, p, note + f" Search re-run: best single clause over {len(f)} numeric fields x 9 quantile "
                              f"lines (both directions, min {min_keep} kept); the rule's discovery score {float(sc_rule[0]):.3f}; "
                              f"best found by the search {real[0]:.3f} = `{rl.rule_text(real[1])}`; shuffled best median {med:.3f}, max {mx:.3f}."))
    # per-day holdout losers removed
    hl = [(T[i]["day"], T[i]["pnl_rs"]) for i in hold if not m_all(T, rule)[i]]
    L.append("Holdout trades the rule removes: " + (", ".join(f"{d} {p:+,.0f}" for d, p in hl) if hl else "none") + "\n")
    return ev, p


def m_all(T, rule):
    return rl.keep_mask(T, rule)


# ── Lead A: council unanimity on the c20 family ──────────────────────────────────────────────────────────
L.append("## Lead A — `agree_same` (sibling books agreeing at the trigger)\n")
for book, line in (("c20_9y", 7.0), ("c20_9s", 6.0)):
    check(book, [("agree_same", ">=", line)])
L.append("### The same clause on the siblings it was NOT found on (frozen, all 14 days)\n")
L += ["| book | line | window | book win % / P&L | kept n, win %, P&L | removed n, win %, P&L |", "|---|---|---|---|---|---|"]
for book in ("c20_9x", "c20_9v", "c20_9t", "c20_8x", "c20_9e", "c20_9h"):
    T = rl.load_book(book)
    if len(T) < 20:
        continue
    for line in (6.0, 7.0):
        ev = rl.evaluate(T, [("agree_same", ">=", line)])
        for w in ("discovery", "holdout"):
            b, k, r = ev[w]["book"], ev[w]["kept"], ev[w]["removed"]
            L.append(f"| {book} | >= {line:.0f} | {w} | {b['win']:.0%} / {b['pnl']:+,.0f} | {k['n']}, {('%.0f%%' % (100*k['win'])) if k['win'] is not None else '-'}, {k['pnl']:+,.0f} | "
                     f"{r['n']}, {('%.0f%%' % (100*r['win'])) if r['win'] is not None else '-'}, {r['pnl']:+,.0f} |")
L.append("")
# distribution of agree_same for the family
L.append("### What `agree_same` looks like (c20_9y, all days): value -> trades (winners)\n")
T = rl.load_book("c20_9y")
cnt = {}
for x in T:
    v = x["w"].get("agree_same")
    cnt.setdefault(v, [0, 0]); cnt[v][0] += 1; cnt[v][1] += x["y"]
L.append(", ".join(f"{k}: {n} ({w})" for k, (n, w) in sorted(cnt.items(), key=lambda kv: (kv[0] is None, kv[0]))) + "\n")

# ── Lead B: own-OI help on spot_dc12_t12_first ────────────────────────────────────────────────────────────
L.append("## Lead B — `oi_net_help5` on spot_dc12_t12_first\n")
check("spot_dc12_t12_first", [("oi_net_help5", ">=", 105917.5)], min_keep=30)
L.append("### The same clause frozen on the parent and the cousins (all 14 days)\n")
L += ["| book | window | book win % / P&L | kept n, win %, P&L | removed n, win %, P&L |", "|---|---|---|---|---|"]
for book in ("spot_dc12_t12", "spot_dc12_t12_first_r003", "spot_dc12_t12_1130", "spot_dc12_t12_nolock", "spot_dc12_t12_r002"):
    T = rl.load_book(book)
    if len(T) < 20:
        continue
    ev = rl.evaluate(T, [("oi_net_help5", ">=", 105917.5)])
    for w in ("discovery", "holdout"):
        b, k, r = ev[w]["book"], ev[w]["kept"], ev[w]["removed"]
        L.append(f"| {book} | {w} | {b['win']:.0%} / {b['pnl']:+,.0f} | {k['n']}, {('%.0f%%' % (100*k['win'])) if k['win'] is not None else '-'}, {k['pnl']:+,.0f} | "
                 f"{r['n']}, {('%.0f%%' % (100*r['win'])) if r['win'] is not None else '-'}, {r['pnl']:+,.0f} |")
L.append("")
rl.save(OUT + ".md", "\n".join(L))
print("\n".join(L))
