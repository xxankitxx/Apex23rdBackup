"""R02 per-second exit study. Pilot now: three day parts (6, 9, 11 Nov = test days). Phase B: every built part.
Usage: py -3.13 a4_paths.py [part ...]   (default: the three pilot parts). Output: a4_<tag>.json in the R02 folder."""
import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.path.insert(0, r"D:\ApexOptions\data\research\13nov\work\R02")
import json, time, os
import numpy as np
import pathlib_r02 as L

W = r"D:\ApexOptions\data\research\13nov\work\R02"
PARTS = sys.argv[1:] or ["2026-11-06", "2026-11-09", "2026-11-11.p4"]
TAG = os.environ.get("R02_TAG", "pilot")
T0 = time.time()

VARIANTS = {"base": {}}
for m in (0.5, 0.75, 1.25, 1.5, 2.0):
    VARIANTS[f"trail x{m}"] = {"trail_mult": m}
for k in (4, 6, 8, 10, 14):
    VARIANTS[f"trail {k}xATR1m"] = {"trail_atr": k}
for T_, x in ((600, 0.03), (900, 0.03), (900, 0.06), (1200, 0.06), (1800, 0.10)):
    VARIANTS[f"noprog {T_}s pk<{x}"] = {"np_T": T_, "np_x": x}
for k in (1.0, 1.5, 2.0, 3.0):
    VARIANTS[f"TP {k} sigma30"] = {"tp_sig": k}
for S, x in ((600, 0.0), (900, 0.0), (900, 0.05), (1500, 0.05)):
    VARIANTS[f"stall {S}s g<{x}"] = {"stall_S": S, "stall_x": x}
for k in (6, 9, 12):
    VARIANTS[f"prem chandelier {k}xATR"] = {"pchand": k, "pchand_arm": 0.05}
for k in (0.5, 1.0, 2.0):
    VARIANTS[f"theta since peak > {k}x gain"] = {"theta_k": k}
VARIANTS["no clock"] = {"hold": None}
VARIANTS["clock x2"] = {"hold": "x2"}
VARIANTS["clock x0.5"] = {"hold": "x0.5"}
VARIANTS["no floors"] = {"floors": False}
VARIANTS["floor arm 0.10"] = {"r_arm": 0.10}
VARIANTS["floor lock +3% at arm"] = {"be_lock": 0.03}
VARIANTS["floor k1 0.80"] = {"k1": 0.80}
VARIANTS["SL 10%"] = {"sl": 0.10}
VARIANTS["SL 20%"] = {"sl": 0.20}
VARIANTS["SL off"] = {"sl": None}
VARIANTS["exp prem trail arm 0.4"] = {"pt_pa": 0.4}
VARIANTS["exp prem trail give 0.15"] = {"pt_pq": 0.15}
VARIANTS["SL 10% expiry only"] = {"sl_exp": 0.10}
VARIANTS["SL 20% expiry only"] = {"sl_exp": 0.20}
for T_, x, pkx in ((120, -0.05, 0.03), (180, -0.05, 0.03), (300, -0.03, 0.05), (300, -0.07, 0.05)):
    VARIANTS[f"early cut {T_}s g<{x} pk<{pkx}"] = {"ec_T": T_, "ec_x": x, "ec_pk": pkx}
VARIANTS["exp clock 600"] = {"hold_exp": 600}
VARIANTS["exp clock 1500"] = {"hold_exp": 1500}
VARIANTS["norm clock 2700"] = {"hold_norm": 2700}
for x in (0.55, 0.60, 0.70):
    VARIANTS[f"expiry TP {x}"] = {"tp_fix": x}
for tau in (3, 5, 10):
    VARIANTS[f"SL on {tau}s-smoothed bid"] = {"sl_tau": tau}
for f_, c in ((12, 0.25), (15, 0.25), (20, 0.25), (15, 0.20)):
    VARIANTS[f"expiry fwd stop {f_} pts + SL {int(c*100)}%"] = {"fsl": f_, "sl_exp": c}
VARIANTS["PGB on every pool book"] = {"pgb_all": True}
VARIANTS["hold to flat, SL only"] = {"fwd_trail": False, "hold": None, "floors": False, "ptre": False, "pgb": False}


def resolve(V, p):
    V = dict(V)
    if "sl_exp" in V:
        if p["exp"]:
            V["sl"] = V["sl_exp"]
    if "hold_exp" in V and p["exp"]:
        V["hold"] = V["hold_exp"]
    if "hold_norm" in V and not p["exp"]:
        V["hold"] = V["hold_norm"]
    if V.get("hold") == "x2":
        V["hold"] = (900 if p["exp"] else 5400) * 2
    elif V.get("hold") == "x0.5":
        V["hold"] = (900 if p["exp"] else 5400) // 2
    return V


trades = json.load(open(os.path.join(W, "pool_trades.json"), encoding="utf-8"))
out = {"parts": PARTS, "variants": list(VARIANTS), "trades": []}
for part in PARTS:
    day = part[:10]
    T = [x for x in trades if x["day"] == day]
    _man = json.load(open(os.path.join(L.DS, part + ".manifest.json"), encoding="utf-8"))
    T = [x for x in T if _man["first"] <= x["t_in"] <= _man["last"]]      # only trades that start inside this part
    if os.environ.get("R02_BOOKS"):
        T = [x for x in T if x["book"] in os.environ["R02_BOOKS"].split(",")]
    if os.environ.get("R02_COND"):
        T = [x for x in T if x.get("cond")]
    if os.environ.get("R02_CHUNK"):                       # "k:size" -> the k-th block of `size` trades of this day
        k_, n_ = (int(v) for v in os.environ["R02_CHUNK"].split(":"))
        T = sorted(T, key=lambda x: (x["t_in"], x["book"]))[k_ * n_:(k_ + 1) * n_]
    if not T:
        continue
    P = L.load_part(part)
    nb = 0
    for tr in T:
        p = L.trade_path(P, tr)
        if p is None:
            continue
        L.add_theta(p, tr)
        nb += 1
        ia = p["ia"]
        rec = dict(day=day, book=tr["book"], cond=bool(tr.get("cond")), rr=tr["rr"], exp=bool(p["exp"]), t_in=tr["t_in"],
                   actual=tr["ret_pct"] / 100.0, reason=tr["reason0"], quote_ok=round(p["ok"], 3),
                   peak_hold=float(p["bid"][:ia + 1].max() / p["e"] - 1), peak_flat=float(p["bid"].max() / p["e"] - 1),
                   held_actual=float(p["t"][ia] - p["t"][0]), atr=p["atr"], iv0=float(p["iv"][0]), d0=float(p["delta"][0]))
        # theta share: decay paid over the actual hold vs the premium change
        th = p["theta_min"]
        rec["theta_paid_pts"] = float(np.sum(np.abs(th[:ia + 1])) / 60.0)
        res = {}
        for name, V in VARIANTS.items():
            row, why = L.sim(p, resolve(V, p), tr["book"])
            res[name] = (round(float(L.exit_ret(p, row)), 5), why, int(p["t"][row] - p["t"][0]))
        rec["v"] = res
        out["trades"].append(rec)
    print(part, "trades", nb, "elapsed", round(time.time() - T0, 1), flush=True)
    del P

json.dump(out, open(os.path.join(W, f"a4_{TAG}.json"), "w"))
# ---- summary
R = out["trades"]
if R:
    act = np.array([r["actual"] for r in R]); base = np.array([r["v"]["base"][0] for r in R])
    print("\nfidelity (rebuilt c20 stack vs the book's actual exit):",
          "median |diff| %.2f pct pts" % (100 * np.median(np.abs(base - act))),
          "| within 2 pct pts: %d of %d" % (int((np.abs(base - act) <= 0.02).sum()), len(R)),
          "| same reason: %d" % sum(1 for r in R if r["v"]["base"][1].split("_")[0] in r["reason"] or
                                   (r["v"]["base"][1] == "FLOOR" and ("LOCK" in r["reason"] or "GIVEBACK" in r["reason"]))))
    pf = np.array([max(r["peak_flat"], 0) for r in R]); ph = np.array([max(r["peak_hold"], 0) for r in R])
    print("available move: sum actual %.1f %% | sum peak inside hold %.1f %% | sum peak to flat %.1f %% | capture %.0f %% / %.0f %%"
          % (100 * act.sum(), 100 * ph.sum(), 100 * pf.sum(), 100 * act.sum() / ph.sum(), 100 * act.sum() / pf.sum()))
    days = sorted({r["day"] for r in R})
    print("\nvariant | n | win % | mean % | sum log % (minus base) | per day sum log minus base | conductor subset minus base")
    for name in VARIANTS:
        v = np.array([r["v"][name][0] for r in R])
        lg = np.log1p(np.clip(v, -0.99, None)); lb = np.log1p(np.clip(base, -0.99, None))
        pdx = " ".join("%+.1f" % (100 * (lg - lb)[[r["day"] == d for r in R]].sum()) for d in days)
        c = np.array([r["cond"] for r in R])
        print("%-30s %3d %5.1f %6.2f %+7.1f | %s | cond %+.1f (n %d)" % (name, len(v), 100 * (v > 0).mean(), 100 * v.mean(),
              100 * (lg - lb).sum(), pdx, 100 * (lg - lb)[c].sum(), int(c.sum())))
print("done", round(time.time() - T0, 1), "s")
