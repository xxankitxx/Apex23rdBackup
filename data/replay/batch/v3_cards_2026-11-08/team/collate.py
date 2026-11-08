"""One table from the ten agents' rules.json: per book, the best rule they found (lowest p; PROPOSE first)."""
import glob, json, os
S = r"C:/Users/ANKITM~1/AppData/Local/Temp/claude/7432839338ffa931/4fc710fd-915d-4b6c-be6c-118168a8b13b/scratchpad/team"
rows, nrules, nprop = [], 0, 0
for f in sorted(glob.glob(S + "/agent_*/rules.json"), key=lambda p: int(p.split("agent_")[1].split(os.sep)[0].split("/")[0])):
    ag = f.replace("\\", "/").split("/")[-2].replace("agent_", "A")
    r = json.load(open(f, encoding="utf-8")); r = r if isinstance(r, list) else r.get("rules", r)
    nrules += len(r)
    by = {}
    for x in r:
        by.setdefault(x.get("book"), []).append(x)
    for book, xs in by.items():
        def pv(x):
            try:
                return float(x.get("p"))
            except Exception:
                return 9.0
        prop = [x for x in xs if str(x.get("verdict", "")).upper().startswith("PROPOSE")]
        nprop += len(prop)
        best = min(prop or xs, key=pv)
        d, h = best.get("discovery") or {}, best.get("holdout") or {}
        def side(w, s):
            v = (w.get(s) or {})
            if not v or v.get("n") in (None, 0):
                return "-"
            win = v.get("win"); win = f"{100*win:.0f}%" if isinstance(win, (int, float)) else "-"
            pnl = v.get("pnl"); pnl = f"{pnl:+,.0f}" if isinstance(pnl, (int, float)) else "-"
            return f"{v.get('n')}, {win}, {pnl}, {v.get('losers', '-')}L"
        rule = best.get("rule")
        if isinstance(rule, list):
            rule = " AND ".join(f"{c[0]} {c[1]} {c[2]:.4g}" if isinstance(c, (list, tuple)) and len(c) == 3 and isinstance(c[2], (int, float)) else str(c) for c in rule)
        verdict = str(best.get("verdict", "")).upper()
        rows.append((ag, book, len(xs), str(rule)[:90], side(d, "book"), side(d, "kept"), side(h, "book"), side(h, "kept"), side(h, "removed"), pv(best), verdict))
L = ["| agent | book | rules tried | best rule (lowest p) | discovery book: n, win, Rs, losers | discovery kept | holdout book | holdout kept | holdout removed | p | agent's verdict |",
     "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    L.append("| " + " | ".join(str(c) if not isinstance(c, float) else (f"{c:.3f}" if c < 9 else "-") for c in r) + " |")
open(S + "/collated_table.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print(f"{len(rows)} books, {nrules} rule objects, {nprop} marked PROPOSE")
print("\n".join(L))
