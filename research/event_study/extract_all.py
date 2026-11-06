"""Per-second snapshot of a recorded day with EVERY instrument the engine sees: indices, index futures, VIX, the
heavyweight stocks and their futures, and the nearest-weekly Nifty options.

    py -3.13 extract_all.py 2026-11-04        ->  raw_2026-11-04.npz in this folder

The tape is replayed through the engine's own parser into a PRIVATE shared-memory table (its own name, so the live
engine and other runs are never touched). Each second, the latest state of every kept instrument is sampled.
X (N, M, 12) float32: ltp bid ask bqty aqty tbq tsq ttq oi ltt bq5 aq5; names (M,); kind (M,); wn (M,) Nifty weight.
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"D:\ApexOptions")
from apex import feed_replay  # noqa: E402
from apex.feed_core import apply_packet  # noqa: E402
from apex.table import Table  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ("ltp", "bid", "ask", "bqty", "aqty", "tbq", "tsq", "ttq", "oi", "ltt")
KEEP_KINDS = ("spot", "fut", "vix", "eq", "sfut")


def main(day):
    path = rf"D:\ApexOptions\data\ticks\{day}.jsonl.gz"
    t = Table(create=True, name=f"apex_ev_{day.replace('-', '')}")
    by_token = items = None
    version, part, new_part = 0, 1, False
    names, kind, wn, ids = [], [], [], []
    expiry = None
    rows, secs = [], []
    nxt = None

    def sample(sec):
        c = t.col
        idx = np.asarray(ids, dtype=np.int64)
        miss = idx < 0
        idx = np.where(miss, 0, idx)
        a = np.stack([c[f][idx] for f in FIELDS] + [c["bq"][idx].sum(1), c["aq"][idx].sum(1)], 1).astype(np.float32)
        a[miss] = np.nan                                  # a column this registry does not carry
        rows.append(a)
        secs.append(sec)

    for pn, r in feed_replay.iter_records(path):
        if pn != part:
            part, new_part = pn, True
        k = r.get("k")
        if k == "meta":
            continue
        try:
            vns, d = int(r.get("t", 0)), r.get("d")
        except Exception:
            continue
        sec = vns // 1_000_000_000
        if k == "p" and nxt is not None and items is not None:
            while sec > nxt:
                sample(nxt)
                nxt += 1
        if k == "reg":
            version += 1
            by_token = feed_replay.install_registry(t, d, version, prev_items=items, zero=new_part)
            items, new_part = d, False
            exps = sorted({x["expiry"] for x in d if x["kind"] == "opt"})
            if expiry is None:
                expiry = exps[0]
            keep = [x for x in d if x["kind"] in KEEP_KINDS
                    or (x["kind"] == "opt" and x["sym"] == "NIFTY" and x["expiry"] == expiry)]
            key_now = {x["key"]: x for x in keep}
            if not names:                                   # first registry fixes the column order
                for x in keep:
                    nm = f'{int(x["strike"])}{x["rr"] if "rr" in x else x["right"]}' if x["kind"] == "opt" else x["key"]
                    names.append(nm)
                    kind.append(x["kind"])
                    wn.append(float(x.get("wn") or 0.0))
            # map every column to this registry's row id (a later registry may renumber rows)
            ids = []
            for nm, kd in zip(names, kind):
                if kd == "opt":
                    k2 = None
                    for x in keep:
                        if x["kind"] == "opt" and f'{int(x["strike"])}{x.get("rr", x.get("right"))}' == nm:
                            k2 = x
                            break
                else:
                    k2 = key_now.get(nm)
                ids.append(k2["id"] if k2 is not None else -1)
        elif k == "p" and by_token is not None:
            apply_packet(t, by_token, d, vns)
            if nxt is None:
                nxt = sec + 1
    X = np.stack(rows) if rows else np.zeros((0, len(names), 12), np.float32)
    np.savez_compressed(os.path.join(HERE, f"raw_{day}.npz"), T=np.array(secs, float), X=X,
                        names=np.array(names, dtype=object), kind=np.array(kind, dtype=object),
                        wn=np.array(wn), expiry=expiry)
    try:
        t.close()
        t.unlink()
    except Exception:
        pass
    print(day, X.shape, expiry, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
