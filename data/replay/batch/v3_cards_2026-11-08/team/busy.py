"""Was the 'abstaining' sibling judging the trigger, or simply still holding its previous trade?"""
import sys
sys.path.insert(0, r"C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/team")
import rule_lab as rl
sys.path.insert(0, "D:/ApexOptions")
from apex import config

fam = [b for b in config.VARIANTS if b.startswith("c20_")]
D = rl.days()
def key(t):
    return (round(float(t.get("trigger_t") or t["t_in"]), 1), t["key"])
took = {}
alltr = {}
for d in D:
    for b in fam:
        ts = [t for t in (D[d].get(b) or {}).get("trades") or [] if t.get("pnl_rs") is not None]
        alltr[(d, b)] = ts
        for t in ts:
            took.setdefault((d, key(t)), {})[b] = t
busy_n = judged_n = 0
for book, full in (("c20_9y", 7), ("c20_9s", 6)):
    print(f"\n== {book}: agree_same < {full}")
    for x in rl.load_book(book):
        a = x["w"].get("agree_same")
        if a is None or a >= full:
            continue
        d = x["day"]; trig = float(x["t"].get("trigger_t") or x["t"]["t_in"])
        who = took.get((d, key(x["t"])), {})
        notes = []
        for b in fam:
            if b in who or b.endswith(("_r002", "_r004")):
                continue
            # open position at the trigger second?
            inpos = [t for t in alltr[(d, b)] if float(t["t_in"]) <= trig <= float(t["t_out"])]
            if inpos:
                t = inpos[0]
                notes.append(f"{b}: BUSY (in {t['rr']} since {t.get('time_in')}, out {t.get('time_out')}, {t['pnl_rs']:+,.0f})")
                busy_n += 1
            else:
                notes.append(f"{b}: free, did not fire")
                judged_n += 1
        print(f"{d} {x['t'].get('time_in')} {x['t']['rr']} a={a} {x['pnl_rs']:+,.0f} | " + "; ".join(notes))
print(f"\nabsent siblings (rule books excluded): busy in an earlier trade {busy_n}, free and silent {judged_n}")
