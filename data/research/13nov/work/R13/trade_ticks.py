import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, re
P = r"D:\ApexOptions\data\paper"; L = r"D:\ApexOptions\data\logs"
eng9 = {}
for i, ln in enumerate(open(L + r"\engine.log", encoding="utf-8", errors="replace"), 1):
    if 933 <= i < 1264 and "tick time last minute" in ln:
        g = re.search(r"mkt=(\d\d:\d\d).*?p50 (\d+) ms, p95 (\d+) ms, max (\d+) ms over (\d+) ticks", ln)
        eng9[g.group(1)] = dict(p50=int(g.group(2)), p95=int(g.group(3)), max=int(g.group(4)), n=int(g.group(5)))
def perf(day):
    if day == "2026-11-09": return eng9
    out = {}
    for l in open(fr"{L}\perf_{day}.jsonl"):
        r = json.loads(l); out[r["mkt"]] = dict(p50=r["p50"], p95=r["p95"], max=r["max"], n=r["n"])
    return out
for day in ("2026-11-09", "2026-11-11", "2026-11-12", "2026-11-13"):
    pf = perf(day); ent = None
    for l in open(fr"{P}\conductor_{day}.jsonl"):
        d = json.loads(l)
        if d["event"] in ("entry", "exit"):
            hm = d["time"][:5]
            # the per-minute line stamped hh:mm covers the minute before it
            m = pf.get(hm) or {}
            if d["event"] == "entry": ent = (d["time"], d.get("book"), m)
            else:
                print(day, "in", ent[0], "ticks/min", ent[2].get("n"), "p95", ent[2].get("p95"), "max", ent[2].get("max"),
                      "| out", d["time"], "ticks/min", m.get("n"), "p95", m.get("p95"), "max", m.get("max"), "|", round(d.get("ret_pct") or 0, 1), "%", d.get("reason"))
