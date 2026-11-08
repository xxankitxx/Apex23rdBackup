"""Which sibling abstained? For every c20_9y trade with agree_same < 7 and every c20_9s trade with agree_same < 6,
list the c20-family books that did / did not take the same trigger, and whether the trades are the same ones."""
import sys
sys.path.insert(0, r"C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/team")
import rule_lab as rl
sys.path.insert(0, "D:/ApexOptions")
from apex import config

fam = [b for b in config.VARIANTS if b.startswith("c20_")]
print("c20 family in config order:", fam)
D = rl.days()
def key(t):
    return (round(float(t.get("trigger_t") or t["t_in"]), 1), t["key"])
# per day: trigger key -> set of family books that took it
took = {}
for d in D:
    for b in fam:
        for t in (D[d].get(b) or {}).get("trades") or []:
            if t.get("pnl_rs") is None:
                continue
            took.setdefault((d, key(t)), {})[b] = t["pnl_rs"]
rows = []
for book, full in (("c20_9y", 7), ("c20_9s", 6)):
    T = rl.load_book(book)
    print(f"\n== {book}: trades with agree_same < {full}")
    for x in T:
        a = x["w"].get("agree_same")
        if a is None or a >= full:
            continue
        k = (x["day"], key(x["t"]))
        who = took.get(k, {})
        absent = [b for b in fam if b not in who]
        print(f"{x['day']} {x['t'].get('time_in')} {x['t']['rr']} agree_same={a} pnl={x['pnl_rs']:+,.0f} | took: "
              f"{', '.join(f'{b} {p:+,.0f}' for b, p in who.items())} | absent: {', '.join(absent)}")
        rows.append((book, k))
same = {k for b, k in rows if b == "c20_9y"} & {k for b, k in rows if b == "c20_9s"}
print(f"\nTriggers flagged by both 9y and 9s: {len(same)}")
# what does the abstaining book's record look like at the moments the full family fired?
print("\n== every family trigger: how many family books took it vs the family's P&L on it")
agg = {}
for (d, k), who in took.items():
    n = len(who)
    pos = sum(1 for p in who.values() if p > 0)
    agg.setdefault(n, [0, 0, 0.0]); agg[n][0] += 1; agg[n][1] += 1 if pos * 2 > n else 0; agg[n][2] += sum(who.values()) / n
for n in sorted(agg):
    c, w, p = agg[n]
    print(f"{n} books took it: {c} triggers, {w} where most books won, mean P&L per book-trade {p / c:+,.0f}")
