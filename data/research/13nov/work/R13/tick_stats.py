import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import re, collections
day = "2026-11-09"; rows = collections.defaultdict(list); slow = collections.defaultdict(list); errs = collections.defaultdict(list)
with open(r"D:\ApexOptions\data\logs\engine.log", encoding="utf-8", errors="replace") as f:
    for i, ln in enumerate(f, 1):
        if i < 933: continue
        m = re.match(r"^(2026-11-\d\d) ", ln)
        if m: day = m.group(1)
        if "tick time last minute" in ln:
            g = re.search(r"p50 (\d+) ms, p95 (\d+) ms, max (\d+) ms over (\d+) ticks \(over 300 ms: (\d+)(?:, over 1 s: (\d+))?", ln)
            t = re.search(r"mkt=(\d\d:\d\d)", ln)
            hm = t.group(1) if t else ln[:5]
            p50, p95, mx, n, o3, o1 = [int(x) if x else 0 for x in g.groups()]
            e = re.search(r"errors (\d+)", ln)
            rows[day].append((hm, p50, p95, mx, n, o3, o1, int(e.group(1)) if e else 0))
        if "SLOW TICK" in ln:
            g = re.search(r"SLOW TICK (\d+) ms", ln); slow[day].append(int(g.group(1)))
for d in sorted(rows):
    r = [x for x in rows[d] if "09:15" <= x[0] <= "15:30"]
    if not r: continue
    p95s = sorted(x[2] for x in r); n = sum(x[4] for x in r)
    print(d, "minutes", len(r), "ticks", n, "median p50", sorted(x[1] for x in r)[len(r)//2], "median p95", p95s[len(r)//2],
          "worst p95", p95s[-1], "max", max(x[3] for x in r), "over300", sum(x[5] for x in r), "over1s", sum(x[6] for x in r),
          "min ticks/min", min(x[4] for x in r), "save errors max cum", max(x[7] for x in r), "slow", len(slow[d]), sorted(slow[d])[-5:])
    # worst minutes
    w = sorted(r, key=lambda x: -x[2])[:6]
    print("   worst p95 minutes:", [(x[0], x[2], x[3], x[4]) for x in w])
    lo = sorted(r, key=lambda x: x[4])[:6]
    print("   fewest ticks:", [(x[0], x[4]) for x in lo])
