import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R04 step 5: collate s1 (single items) over every group: survivors, and items with no information.
Field -> docs/27 item from apex/conductor/search.py ITEMS and apex/engine/weather5.py (parsed, not imported)."""
import ast, glob, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(r"D:\ApexOptions\apex\conductor\search.py", encoding="utf-8").read()
blk = src[src.index("ITEMS = {"):src.index("# 10 Nov (photo v5")]
ITEMS = ast.literal_eval(blk.split("=", 1)[1].strip())
w5 = open(r"D:\ApexOptions\apex\engine\weather5.py", encoding="utf-8").read()
E = {}
for m in re.finditer(r"^(E1\d\d) = (\([^)]*\))", w5, re.M | re.S):
    E[m.group(1)] = ast.literal_eval(m.group(2))
for m in re.finditer(r"^\s+(\d{3}): \(\"([^\"]+)\", (E1\d\d)\),", w5, re.M):
    ITEMS[int(m.group(1))] = (m.group(2), E.get(m.group(3), ()))
ITEM_OF = {k: n for n, (_l, ks) in ITEMS.items() for k in ks}
# weather4 fields map through search.py already; anything else is "unmapped"


def item(f):
    k = f.split("=")[0]
    n = ITEM_OF.get(k, 61 if k.startswith("adv_") else None)
    return n, (ITEMS[n][0] if n else "?")


runs = {}
for fn in sorted(glob.glob(os.path.join(HERE, "out_s1_*.json"))):
    r = json.load(open(fn))
    runs[r["group"]] = r
print("groups:", list(runs))
feat = {}
for g, r in runs.items():
    for row in r["rows"]:
        feat.setdefault(row["f"], {})[g] = row
summary = []
for f, by in feat.items():
    n, lab = item(f)
    zs = [x["z"] for x in by.values() if x.get("z") is not None]
    ps = [x["p"] for x in by.values()]
    rt = [x["rho_test"] for x in by.values() if x.get("rho_test") is not None]
    rd = [x["rho_disc"] for x in by.values() if x.get("rho_disc") is not None]
    cov = [x["cov"] for x in by.values()]
    nun = [x["nuniq"] for x in by.values()]
    agree = [1 if (a is not None and b is not None and a * b > 0) else 0 for a, b in
             [(x.get("rho_disc"), x.get("rho_test")) for x in by.values()]]
    summary.append({"f": f, "item": n, "label": lab, "groups": len(by), "max_z": max(zs) if zs else None,
                    "min_p": min(ps) if ps else None, "bh_any": any(x.get("bh10") for x in by.values()),
                    "max_abs_rho_test": max([abs(v) for v in rt]) if rt else None,
                    "max_abs_rho_disc": max([abs(v) for v in rd]) if rd else None,
                    "sign_agree": sum(agree), "max_cov": max(cov), "max_nuniq": max(nun)})


def cls(s):
    if s["max_cov"] < 0.05 or s["max_nuniq"] <= 1:
        return "no data (missing or constant)"
    if (s["max_z"] is None or s["max_z"] <= 0.5) and (s["max_abs_rho_test"] is None or s["max_abs_rho_test"] < 0.05):
        return "no information"
    if s["bh_any"]:
        return "survives FDR somewhere"
    return "weak / unproven"


for s in summary:
    s["class"] = cls(s)
json.dump(summary, open(os.path.join(HERE, "out_s5_summary.json"), "w"), default=float)
from collections import Counter, defaultdict
print(Counter(s["class"] for s in summary))
byitem = defaultdict(list)
for s in summary:
    byitem[(s["item"], s["label"])].append(s)
print("\nITEMS where EVERY field is 'no data' or 'no information':")
for (n, lab), ss in sorted(byitem.items(), key=lambda x: (x[0][0] or 999)):
    if all(s["class"] in ("no data (missing or constant)", "no information") for s in ss):
        print(f"  {n} {lab}: {', '.join(s['f'] for s in ss)}")
print("\nfields 'no data':", ", ".join(sorted(s["f"] for s in summary if s["class"].startswith("no data"))))
print("\nfields 'survives FDR somewhere':")
for s in sorted([s for s in summary if s["bh_any"]], key=lambda s: s["min_p"]):
    gs = [g for g in runs if feat[s["f"]].get(g, {}).get("bh10")]
    print(f"  {s['f']} (item {s['item']} {s['label']}) min_p {s['min_p']:.5f} groups {gs}")
