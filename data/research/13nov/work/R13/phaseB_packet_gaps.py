import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""PHASE B (run after the 15:30 close, one day per run, at most 3 minutes):
    py -3.13 phaseB_packet_gaps.py 2026-11-13
For one day's tick tape(s), find every silence of the websocket (no packet of any kind) of 2 s or more inside
09:15-15:30 IST, and the exchange-stamp lag (receive time minus the packet's exchange second) around it. Then match
each engine GAP event of that day (data/paper/events_<day>.jsonl, "feed silent ... 3 s") with the tape:
  * a real silence in the tape at that time  -> broker or network side (nothing to fix in the code)
  * no silence in the tape                   -> the feed or engine process was starved (machine load)
Writes work/R13/packet_gaps_<day>.json and prints a table. Reads only; stops itself after 170 s."""
import glob, gzip, json, os, time
from datetime import datetime, timedelta, timezone
IST = timezone(timedelta(hours=5, minutes=30))
day = sys.argv[1]
T0 = time.time()
lo = datetime.fromisoformat(day + "T09:15:00").replace(tzinfo=IST).timestamp()
hi = datetime.fromisoformat(day + "T15:30:00").replace(tzinfo=IST).timestamp()
gaps, prev, n, lag_samples = [], None, 0, []
for path in sorted(glob.glob(fr"D:\ApexOptions\data\ticks\{day}*.jsonl.gz")):
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for ln in f:
            if not ln.startswith('{"k":"p"'):
                continue
            i = ln.find('"t":') + 4
            t = int(ln[i:ln.find(",", i)]) / 1e9
            n += 1
            if lo <= t <= hi:
                if prev is not None and t - prev >= 2.0:
                    gaps.append((prev, t))
                if n % 2000 == 0:                       # exchange-stamp lag sample: field 19 of the packet list
                    try:
                        d = json.loads(ln)["d"]
                        ex = float(d[19]) if len(d) > 19 and d[19] not in ("", None) else None
                        if ex:
                            lag_samples.append((t, t - ex))
                    except Exception:
                        pass
            prev = t
            if time.time() - T0 > 170:
                print("time budget reached; partial result"); break
ev = []
try:
    for l in open(fr"D:\ApexOptions\data\paper\events_{day}.jsonl", encoding="utf-8"):
        d = json.loads(l)
        if d.get("k") == "GAP" and "data gap" in d.get("x", ""):
            ev.append((d["mkt_t"], d["x"][:90]))
except OSError:
    pass
rows = []
for et, x in ev:
    hit = [g for g in gaps if g[0] - 2 <= et <= g[1] + 5]
    rows.append(dict(t=datetime.fromtimestamp(et, IST).strftime("%H:%M:%S"), event=x,
                     tape_silence_s=round(max((g[1] - g[0]) for g in hit), 1) if hit else 0.0,
                     verdict="broker/network" if hit else "local starvation"))
out = dict(day=day, packets=n, silences_ge2s=len(gaps), silence_s_total=round(sum(b - a for a, b in gaps), 1),
           longest=[(datetime.fromtimestamp(a, IST).strftime("%H:%M:%S"), round(b - a, 1)) for a, b in sorted(gaps, key=lambda g: g[0] - g[1])[:10]],
           lag_p50=None, events=rows)
if lag_samples:
    ls = sorted(x[1] for x in lag_samples); out["lag_p50"] = round(ls[len(ls) // 2], 2); out["lag_p95"] = round(ls[int(len(ls) * .95)], 2)
json.dump(out, open(fr"D:\ApexOptions\data\research\13nov\work\R13\packet_gaps_{day}.json", "w"), indent=1)
print(json.dumps(out, indent=1)[:4000])
