"""
Clock norms (docs/27 items 7, 17, 25, 34: "vs the same clock time on earlier days", "vs its normal").
A standalone pass over the recorded tapes (data/ticks/<day>.jsonl.gz and its parts) that writes, per day and per
session minute (0 = 09:15-09:16, ..., 374 = 15:29-15:30):
  range     Nifty spot high - low so far at the END of the minute (points)
  rv5       realised vol of 1-s spot returns over the last 5 min, annualised %  (the weather.rv convention)
  fut_vol   Nifty futures volume traded during the minute (units)
  hw_vol    the heavyweights' cash volume traded during the minute (units, summed)
to data/learning/clock_norms.json. The engine (weather.Weather.norms_for(day)) reads only days BEFORE the day it is
running, so a photo never sees its own day's norm: no look-ahead. Raw packets are parsed here the same way
feed_core.apply_packet does (ltp raw[2]; ttq raw[14] on a 23-field F&O quote, raw[12] on a 21-field cash quote).
    py -3.13 -m apex.conductor.clock_norms [--ticks data/ticks] [--out data/learning/clock_norms.json]
"""
import argparse
import glob
import gzip
import json
import math
import os
import sys
from collections import deque
from datetime import datetime
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from apex import config  # noqa: E402

MINUTES = 375
_ANN = (252 * 22500) ** 0.5 * 100


def _parts(path):
    base = path[:-len(".jsonl.gz")]
    out = [path]
    k = 2
    while os.path.exists(f"{base}.p{k}.jsonl.gz"):
        out.append(f"{base}.p{k}.jsonl.gz")
        k += 1
    return out


def one_day(path):
    day = os.path.basename(path)[:10]
    y, m, d = (int(x) for x in day.split("-"))
    open_s = datetime(y, m, d, 9, 15, tzinfo=config.IST).timestamp()
    by_tok = {"eq": {}, "fo": {}}
    kinds = {}
    spot_id = fut_id = None
    eq_ids = set()
    rng = [None] * MINUTES
    rv5 = [None] * MINUTES
    fut_vol = [0.0] * MINUTES
    hw_vol = [0.0] * MINUTES
    seen_min = [False] * MINUTES
    hi = lo = None
    sp_hist = deque()                               # (sec, px) last 300 s
    last_sec = None
    ttq_prev = {}
    n_p = 0
    for p in _parts(path):
        try:
            with gzip.open(p, "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    k = r.get("k")
                    if k == "reg":
                        by_tok = {"eq": {}, "fo": {}}
                        kinds = {}
                        eq_ids = set()
                        for it in r["d"]:
                            tok = (it.get("token") or "").split("!", 1)[-1]
                            seg = it.get("seg") or ("eq" if it.get("kind") in ("spot", "vix", "eq") else "fo")
                            by_tok[seg][tok] = it["id"]
                            kinds[it["id"]] = it.get("kind")
                            if it.get("key") == "NIFTY|SPOT":
                                spot_id = it["id"]
                            elif it.get("key") == "NIFTY|FUT":
                                fut_id = it["id"]
                            elif it.get("kind") == "eq":
                                eq_ids.add(it["id"])
                        continue
                    if k != "p":
                        continue
                    raw = r["d"]
                    if not isinstance(raw, list) or not raw or not isinstance(raw[0], str) or "!" not in raw[0]:
                        continue
                    head, tok = raw[0].split("!", 1)
                    if not head.endswith(".1"):
                        continue                    # depth packets carry no ltp / ttq
                    n = len(raw)
                    if n not in (21, 23):
                        continue
                    i = by_tok["fo" if n == 23 else "eq"].get(tok)
                    if i is None:
                        continue
                    t = r["t"] / 1e9
                    mi = int((t - open_s) // 60)
                    if mi < 0 or mi >= MINUTES:
                        continue
                    n_p += 1
                    seen_min[mi] = True
                    if i == spot_id:
                        px = raw[2]
                        if isinstance(px, (int, float)) and px > 0:
                            px = float(px)
                            hi = px if hi is None else max(hi, px)
                            lo = px if lo is None else min(lo, px)
                            rng[mi] = round(hi - lo, 2)
                            sec = int(t)
                            if sec != last_sec:
                                last_sec = sec
                                sp_hist.append((sec, px))
                                while sp_hist and sec - sp_hist[0][0] > 300:
                                    sp_hist.popleft()
                                if len(sp_hist) >= 150:
                                    a = np.asarray([x[1] for x in sp_hist], float)
                                    rr = np.diff(np.log(a))
                                    rv5[mi] = round(float(np.std(rr)) * _ANN, 2)
                        continue
                    if i == fut_id or i in eq_ids:
                        q = raw[14] if n == 23 else raw[12]
                        if not isinstance(q, (int, float)) or not (q >= 0):
                            continue
                        q = float(q)
                        prev = ttq_prev.get(i)
                        ttq_prev[i] = q
                        if prev is None or q < prev:
                            continue                # first sight, or a reset / reordered packet
                        if i == fut_id:
                            fut_vol[mi] += q - prev
                        else:
                            hw_vol[mi] += q - prev
        except (EOFError, OSError):
            pass                                    # a crashed part ends where its data ends
    fut_vol = [round(v, 0) if seen_min[j] else None for j, v in enumerate(fut_vol)]
    hw_vol = [round(v, 0) if seen_min[j] else None for j, v in enumerate(hw_vol)]
    return day, {"range": rng, "rv5": rv5, "fut_vol": fut_vol, "hw_vol": hw_vol, "packets": n_p}


def build(ticks_dir, out_path, procs=14):
    tapes = sorted(p for p in glob.glob(os.path.join(ticks_dir, "????-??-??.jsonl.gz"))
                   if config.is_trading_day(datetime.fromisoformat(os.path.basename(p)[:10]).date()))
    with Pool(min(procs, max(1, len(tapes)))) as pool:
        res = dict(pool.map(one_day, tapes, chunksize=1))
    res = {d: v for d, v in res.items() if v["packets"] > 1000}        # an empty / test tape is not a day
    out = {"version": 1, "minutes": MINUTES, "built": datetime.now(config.IST).strftime("%Y-%m-%d %H:%M"),
           "days": res}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    os.replace(tmp, out_path)
    return out


def norms_before(data, day):
    """{name: [MINUTES] median over the recorded days strictly BEFORE `day`}, or None when fewer than 3 such days.
    This is the only reader: a day never sees its own values or a later day's."""
    days = sorted(d for d in (data or {}).get("days", {}) if d < day)
    if len(days) < 3:
        return None
    out = {"n_days": len(days), "days": days}
    for name in ("range", "rv5", "fut_vol", "hw_vol"):
        cols = []
        for j in range(MINUTES):
            vals = [data["days"][d][name][j] for d in days if data["days"][d][name][j] is not None]
            cols.append(float(np.median(vals)) if len(vals) >= 3 else None)
        out[name] = cols
    return out


def load(path=None):
    path = path or os.path.join(config.LEARN_DIR, "clock_norms.json")
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--ticks", default=os.path.join(ROOT, "data", "ticks"))
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "learning", "clock_norms.json"))
    ap.add_argument("--procs", type=int, default=14)
    a = ap.parse_args(argv)
    out = build(a.ticks, a.out, a.procs)
    for d, v in sorted(out["days"].items()):
        r = [x for x in v["range"] if x is not None]
        fv = [x for x in v["fut_vol"] if x]
        print(f"{d}: {v['packets']:>9,} packets, range at close {r[-1] if r else None}, "
              f"fut vol/min median {np.median(fv) if fv else None:.0f}" if fv else f"{d}: {v['packets']} packets")
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
