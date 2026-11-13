import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R07 PHASE B (run only after the 15:30 close, one part per invocation, nothing else running from R07).

Why: ds_v2 keeps only the future's best PRICES and the 5-level TOTAL sizes (ds2.py lines 128-131), so the true
Cont-Kukanov-Stoikov order-flow imbalance (best-level sizes, event by event) and the multi-level OFI of Xu, Gould and
Howison cannot be built from it. The raw tape has every quote packet: best bid / ask and their sizes (d[6..9]), the
whole-book totals (d[15], d[16]), and every depth packet (5 levels: price, qty, orders per side).

Reads D:\\ApexOptions\\data\\ticks\\<part>.jsonl.gz (read-only), keeps only the Nifty future's quote and depth packets
(the token is matched on the raw line before json parsing, as ds2.py does), and writes per second B (packets received
before B, the ds2 convention, so causal):
  ofi1     sum of event-level L1 OFI in (B-1, B]          mlofi[5]  per-level OFI of each depth level (sum per second)
  tfi      signed traded volume (Lee-Ready against the quote held before the print, tick rule at the mid)
  nq, nd   quote and depth packets in the second           bb, ba, bbq, baq, tbq, tsq  state at the end of the second
-> D:\\ApexOptions\\data\\research\\13nov\\work\\R07\\l1_<part>.npz

Usage: py -3.13 phaseB_l1_ofi_ticks.py <part>            e.g. 2026-11-04   (about 1-2 min per part on an idle machine)
       py -3.13 phaseB_l1_ofi_ticks.py eval <part> ...   IC of L1 OFI / MLOFI vs the ds_v2 5-level OFI (needs feat_<part>.npz)
NOTE (13 Nov README): during market hours only the sister-index agent reads the tick tapes. This script is Phase B."""
import gzip, json, os, time
import numpy as np

TICKS = r"D:\ApexOptions\data\ticks"
W = r"D:\ApexOptions\data\research\13nov\work\R07"
IST_S = 19800


def fl(v):
    try:
        return float(v)
    except Exception:
        return np.nan


def extract(part):
    t0 = time.time()
    src = os.path.join(TICKS, part + ".jsonl.gz")
    fut_tok = dep_tok = None
    rows = {}
    prev = None          # (bid, bq, ask, aq) of the last quote packet
    prevL = None         # (bpx[5], bq[5], apx[5], aq[5]) of the last depth packet
    last_ttq = None
    state = dict(bb=np.nan, ba=np.nan, bbq=np.nan, baq=np.nan, tbq=np.nan, tsq=np.nan, ltp=np.nan)
    cur_B = None
    acc = None

    def new_acc():
        return dict(ofi1=0.0, mlofi=np.zeros(5), tfi=0.0, vol=0.0, nq=0, nd=0)

    def flush(B):
        if acc is None:
            return
        r = dict(acc)
        r.update(state)
        rows[B] = r
    with gzip.open(src, "rt", encoding="utf-8") as f:
        try:
            for l in f:
                if l.startswith('{"k":"reg"'):
                    for r in json.loads(l)["d"]:
                        if r.get("key") == "NIFTY|FUT":
                            fut_tok, dep_tok = r["token"], r.get("depth_token")
                    continue
                if not l.startswith('{"k":"p"') or fut_tok is None:
                    continue
                q = l.find('"d":["') + 6
                tok = l[q:l.find('"', q)]
                if tok != fut_tok and tok != dep_tok:
                    continue
                e = json.loads(l)
                t = e["t"] / 1e9
                d = e["d"]
                B = int(t) + 1                       # this packet is "received before B"
                hm = ((B + IST_S) % 86400) // 60
                if not (555 <= hm < 931):
                    continue
                if B != cur_B:
                    if cur_B is not None:
                        flush(cur_B)
                    cur_B = B
                    acc = new_acc()
                if tok == fut_tok and len(d) == 23:
                    bid, bq, ask, aq = fl(d[6]), fl(d[7]), fl(d[8]), fl(d[9])
                    ltp, ttq = fl(d[2]), fl(d[14])
                    if prev is not None and bid > 0 and ask >= bid:
                        pb, pbq, pa, paq = prev
                        if pb > 0 and pa >= pb:
                            ev = (bq if bid >= pb else 0.0) - (pbq if bid <= pb else 0.0) - (aq if ask <= pa else 0.0) + (paq if ask >= pa else 0.0)
                            if np.isfinite(ev):
                                acc["ofi1"] += ev
                    if last_ttq is not None and np.isfinite(ttq) and ttq > last_ttq and prev is not None:
                        dv = ttq - last_ttq
                        pb, _, pa, _ = prev
                        s = 1.0 if ltp >= pa else (-1.0 if ltp <= pb else float(np.sign(ltp - 0.5 * (pa + pb))))
                        acc["tfi"] += s * dv
                        acc["vol"] += dv
                    if np.isfinite(ttq) and (last_ttq is None or ttq >= last_ttq):
                        last_ttq = ttq
                    if bid > 0 and ask >= bid:
                        prev = (bid, bq, ask, aq)
                    state.update(bb=bid, ba=ask, bbq=bq, baq=aq, tbq=fl(d[15]), tsq=fl(d[16]), ltp=ltp)
                    acc["nq"] += 1
                elif tok == dep_tok:
                    try:
                        lv = d[2]
                        bp = np.array([fl(x[0]) for x in lv[:5]]); bqv = np.array([fl(x[1]) for x in lv[:5]])
                        ap = np.array([fl(x[4]) for x in lv[:5]]); aqv = np.array([fl(x[5]) for x in lv[:5]])
                    except Exception:
                        continue
                    if len(bp) == 5 and prevL is not None:
                        pbp, pbq5, pap, paq5 = prevL
                        ev = (np.where(bp >= pbp, bqv, 0.0) - np.where(bp <= pbp, pbq5, 0.0)
                              - np.where(ap <= pap, aqv, 0.0) + np.where(ap >= pap, paq5, 0.0))
                        acc["mlofi"] += np.nan_to_num(ev)
                    if len(bp) == 5:
                        prevL = (bp, bqv, ap, aqv)
                    acc["nd"] += 1
        except EOFError:
            pass
    if cur_B is not None:
        flush(cur_B)
    Bs = np.array(sorted(rows), float)
    get = lambda k: np.array([rows[int(b)][k] for b in Bs], float)
    np.savez_compressed(os.path.join(W, f"l1_{part}.npz"), t=Bs, ofi1=get("ofi1"), tfi=get("tfi"), vol=get("vol"),
                        nq=get("nq"), nd=get("nd"), bb=get("bb"), ba=get("ba"), bbq=get("bbq"), baq=get("baq"),
                        tbq=get("tbq"), tsq=get("tsq"), mlofi=np.array([rows[int(b)]["mlofi"] for b in Bs], float))
    print(part, "seconds", len(Bs), "s", round(time.time() - t0, 1), flush=True)


def wsum(t, x, Wd):
    c = np.concatenate([[0.0], np.cumsum(np.nan_to_num(x))])
    j = np.searchsorted(t, t - Wd, side="right")
    return c[1:] - c[j]


def evaluate(parts):
    def rank(a):
        o = np.argsort(a, kind="stable"); r = np.empty(len(a)); r[o] = np.arange(len(a)); return r

    def sp(x, y):
        m = np.isfinite(x) & np.isfinite(y)
        return float(np.corrcoef(rank(x[m]), rank(y[m]))[0, 1]) if m.sum() > 50 else np.nan
    print("Spearman IC with the future's mid move (every 5 s). cols: horizon 30/60/120/300")
    for p in parts:
        L = np.load(os.path.join(W, f"l1_{p}.npz")); F = np.load(os.path.join(W, f"feat_{p}.npz"))
        t = F["t"]; Y = F["Y"]; names = list(F["names"]); X = F["X"]
        lt = L["t"]
        j = np.searchsorted(lt, t, side="right") - 1
        ok = j >= 0
        dep = np.nan_to_num(L["bbq"] + L["baq"])
        depbar = np.maximum(wsum(lt, dep / 2, 300) / np.maximum(wsum(lt, np.ones(len(lt)), 300), 1), 1)
        feats = {}
        for Wd in (10, 30, 60, 120):
            feats[f"L1ofi{Wd}"] = (wsum(lt, L["ofi1"], Wd) / depbar)[np.clip(j, 0, None)]
            ml = L["mlofi"]
            feats[f"MLofi{Wd}"] = (wsum(lt, ml.sum(1), Wd) / depbar)[np.clip(j, 0, None)]
            feats[f"MLw{Wd}"] = (wsum(lt, ml @ np.array([1, .5, .33, .25, .2]), Wd) / depbar)[np.clip(j, 0, None)]
            feats[f"L1tfi{Wd}"] = (wsum(lt, L["tfi"], Wd) / np.maximum(wsum(lt, L["vol"], Wd), 1))[np.clip(j, 0, None)]
        I1 = (L["bbq"] - L["baq"]) / (L["bbq"] + L["baq"])
        feats["I1"] = I1[np.clip(j, 0, None)]
        feats["Itot"] = ((L["tbq"] - L["tsq"]) / (L["tbq"] + L["tsq"]))[np.clip(j, 0, None)]
        for k in ("ofi30", "ofi60", "tfi30", "I5"):
            feats["ds_" + k] = X[:, names.index(k)]
        sel = np.arange(0, len(t), 5)
        print(p)
        for k, v in feats.items():
            v = np.where(ok, v, np.nan)
            print("  " + k.ljust(10) + "".join(f"{sp(v[sel], Y[sel, h]):8.3f}" for h in range(Y.shape[1])))


if __name__ == "__main__":
    if sys.argv[1] == "eval":
        evaluate(sys.argv[2:])
    else:
        for p in sys.argv[1:]:
            extract(p)
