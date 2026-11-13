import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R09 streaming extractor: raw tick tape -> per-second sister-index panel (read-only on the tape).
Streams the gzip in 8 MB decompressed blocks and picks the target packets with one compiled regex (C speed), so the
Python loop only touches the ~10 % of packets that matter.
Output work/R09/sister/<part>.npz:
  t  epoch s, grid seconds 09:15:00..15:29:59 IST inside the tape
  X[t, 16]: 0 NIFTY spot, 1 NF ltp, 2 NF bid, 3 NF ask, 4 BN spot, 5 BF ltp, 6 BF bid, 7 BF ask,
            8 FN spot, 9 FF ltp, 10 FF bid, 11 FF ask, 12 VIX, 13 NF ttq, 14 BF ttq, 15 FF ttq
  A[t, 8] age in s (1e9 = never): 0 NIFTY spot, 1 NF, 2 BN spot, 3 BF, 4 FN spot, 5 FF, 6 VIX
A row stamped B holds only packets with tape stamp strictly before B (ds2.py convention).
Usage: py -3.13 sister_extract.py <part> [time budget s, default 165]  (stops early and saves what it has; says so)"""
import gzip, json, os, re, time
import numpy as np
T0 = time.time()
part = sys.argv[1]; budget = float(sys.argv[2]) if len(sys.argv) > 2 else 165.0
SRC = os.path.join(r"D:\ApexOptions\data\ticks", part + ".jsonl.gz")
OUT = os.path.join(r"D:\ApexOptions\data\research\13nov\work\R09\sister", part + ".npz")
IST = 19800
SPOT = {"4.1!NIFTY 50": (0, 0), "4.1!NIFTY BANK": (4, 2), "4.1!NIFTY FIN SERVICE": (8, 4), "4.1!INDIA VIX": (12, 6)}
FKEY = {"NIFTY|FUT": (1, 1, 13), "BANKNIFTY|FUT": (5, 3, 14), "FINNIFTY|FUT": (9, 5, 15)}
FUT = {}
ev_t, ev_c, ev_v = [], [], []
age_t = [[] for _ in range(8)]
nbytes = nhit = 0; cut = torn = False
RXREG = re.compile(rb'\{"k":"reg"[^\n]*')


def fl(x):
    try:
        return float(x.strip(b'"'))
    except Exception:
        return np.nan


def build_rx():
    alt = b"|".join(re.escape(x.encode()) for x in list(SPOT) + list(FUT))
    return re.compile(rb'\{"k":"p","t":(\d+),"d":\["(' + alt + rb')",([^\n]*)\]\}')


rx = None; buf = b""; NL = bytes([10])
with gzip.open(SRC, "rb") as f:
    try:
        while True:
            blk = f.read(1 << 23)
            if not blk:
                data, buf = buf, b""
            else:
                data = buf + blk; j = data.rfind(b"\n"); buf = data[j + 1:]; data = data[:j + 1]
            nbytes += len(data)
            for m in RXREG.finditer(data):
                for r in json.loads(m.group(0))["d"]:
                    if r.get("kind") == "fut" and r["key"] in FKEY and r["token"] not in FUT:
                        FUT[r["token"]] = FKEY[r["key"]]; rx = None
            if rx is None:
                rx = build_rx()
            hits = []
            for tok in list(SPOT) + list(FUT):
                pat = b'"d":["' + tok.encode() + b'",'; p = data.find(pat)
                while p >= 0:
                    a = data.rfind(NL, 0, p) + 1; z = data.find(NL, p)
                    hits.append((tok, data[a:z])); p = data.find(pat, z)
            for tok, line in hits:
                m = rx.match(line)
                if m is None:
                    continue
                t = int(m.group(1)) / 1e9; rest = m.group(3).split(b",")
                nhit += 1
                s = SPOT.get(tok)
                if s is not None:
                    if len(rest) == 20:
                        v = fl(rest[1])
                        if v > 0:
                            ev_t.append(t); ev_c.append(s[0]); ev_v.append(v); age_t[s[1]].append(t)
                elif len(rest) == 22:
                    fu = FUT[tok]; b = fu[0]
                    for c, idx in ((b, 1), (b + 1, 5), (b + 2, 7), (fu[2], 13)):
                        v = fl(rest[idx])
                        if v > 0:
                            ev_t.append(t); ev_c.append(c); ev_v.append(v)
                    age_t[fu[1]].append(t)
            if not blk:
                break
            if time.time() - T0 > budget:
                cut = True; break
    except EOFError:
        torn = True
ev_t = np.array(ev_t); ev_c = np.array(ev_c, np.int16); ev_v = np.array(ev_v)
o = np.argsort(ev_t, kind="stable"); ev_t, ev_c, ev_v = ev_t[o], ev_c[o], ev_v[o]
if len(ev_t):
    day0 = int((ev_t[0] + IST) // 86400) * 86400 - IST
    lo = max(day0 + 555 * 60, int(ev_t[0]) + 1); hi = min(day0 + 930 * 60, int(ev_t[-1]) + 1)
    grid = np.arange(lo, hi, dtype=np.int64)
else:
    grid = np.zeros(0, np.int64)
X = np.full((len(grid), 16), np.nan); A = np.full((len(grid), 8), 1e9, np.float32)
for c in range(16):
    m = ev_c == c
    if not m.any():
        continue
    tt, vv = ev_t[m], ev_v[m]
    k = np.searchsorted(tt, grid, side="left") - 1; ok = k >= 0
    X[ok, c] = vv[k[ok]]
for a in range(8):
    if not age_t[a]:
        continue
    tt = np.sort(np.array(age_t[a]))
    k = np.searchsorted(tt, grid, side="left") - 1; ok = k >= 0
    A[ok, a] = (grid[ok] - tt[k[ok]]).astype(np.float32)
np.savez_compressed(OUT, t=grid, X=X, A=A)
print(json.dumps(dict(part=part, mb=round(nbytes / 1e6), hits=nhit, rows=len(grid), cut_by_budget=cut, torn=torn,
                      first=float(grid[0]) if len(grid) else None, last=float(grid[-1]) if len(grid) else None,
                      fut_tokens=FUT, secs=round(time.time() - T0, 1))))
