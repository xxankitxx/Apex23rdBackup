import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import re, collections, json
LOG = r"D:\ApexOptions\data\logs"
def sessions(path, first9):
    """yield (day, line) from first9 (1-based line of 9 Nov start) on; undated lines before first dated -> 2026-11-09"""
    day = "2026-11-09"
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, ln in enumerate(f, 1):
            if i < first9: continue
            m = re.match(r"^(2026-11-\d\d) ", ln)
            if m: day = m.group(1)
            yield day, i, ln.rstrip("\n")
KEYS = re.compile(r"error|warn|fail|refused|exception|traceback|slow tick|stale|reconnect|denied|timeout|timed out|expired|unresolved|exited|paused|lost|drop|skipp|not |cannot|could not", re.I)
def norm(s):
    s = re.sub(r"^(2026-\d\d-\d\d )?\d\d:\d\d:\d\d (mkt=\d\d:\d\d:\d\d )?", "", s)
    s = re.sub(r"0x[0-9a-f]+", "0x", s)
    s = re.sub(r"\d+(\.\d+)?", "N", s)
    return s[:150]
out = {}
for name, first9 in (("engine.log", 933), ("feed.log", 800), ("supervisor.log", 1)):
    c = collections.Counter(); ex = {}; days = collections.defaultdict(collections.Counter)
    for day, i, ln in sessions(f"{LOG}\{name}", first9):
        if ln.startswith(" ") or not ln.strip(): continue
        if "tick time last minute" in ln: k = "TICKMIN"
        elif not KEYS.search(ln): continue
        else: k = norm(ln)
        c[k] += 1; days[k][day] += 1; ex.setdefault(k, f"{i}: {ln[:300]}")
    print("=====", name)
    for k, n in c.most_common(80):
        print(n, dict(days[k]), "|", ex[k][:260])
