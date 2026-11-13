import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
# R16 PHASE B (run after the 15:30 close only; one day part at a time; under 3 min and 1.5 GB per run).
# Usage: py -3.13 phaseB_vwap_exit_gao.py 2026-11-06        (one day per run; loops over that day's parts)
# Tests two literature ideas that the trade table cannot test:
#  A) Zarattini/Aziz/Barbon "Beat the Market" VWAP trailing stop: exit a Conductor trade the first second
#     (after a 30 s grace) the futures close on the WRONG side of the session VWAP. Exit at the option BID then,
#     if earlier than the real exit. Compares per trade with the real exit.
#  B) Gao/Han/Li/Zhou intraday momentum on Nifty: first 30 min (09:15-09:45 futures) vs last 30 min (14:55-15:25).
# VWAP: fut[:,3] is field 14 of the futures packet; if it sits within 0.5 % of the LTP it is taken as the
# exchange's average traded price (session VWAP); otherwise a session TWAP of the LTP is used and flagged.
import json, glob, os, numpy as np, pandas as pd
day = sys.argv[1]
DS = r"D:\ApexOptions\data\research\ds_v2"
OUT = r"D:\ApexOptions\data\research\13nov\work\R16"
src = r"D:\ApexOptions\data\replay\batch\p44_simr\conductor_sim.json" if day in ("2026-10-28", "2026-10-30", "2026-11-02", "2026-11-03") \
    else r"D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json"
trades = json.load(open(src))["days"].get(day, {}).get("trades", [])
res, gao = [], {}
parts = sorted(p for p in glob.glob(os.path.join(DS, day + "*.npz")))
for p in parts:
    man = json.load(open(p.replace(".npz", ".manifest.json")))
    if not man.get("rows"): continue
    z = np.load(p)
    t, fut, opt, strikes = z["t"], z["fut"], z["opt"], z["strikes"]
    ltp = fut[:, 2].astype(float); f3 = fut[:, 3].astype(float)
    use_atp = np.nanmedian(np.abs(f3 / ltp - 1)) < 0.005
    vw = f3 if use_atp else pd.Series(ltp).expanding().mean().values
    hm = pd.to_datetime(t, unit="s").tz_localize("UTC").tz_convert("Asia/Kolkata").strftime("%H:%M").values
    for a, b, k in (("09:15", "09:45", "first30"), ("14:55", "15:25", "last30")):
        ia, ib = np.where(hm >= a)[0], np.where(hm <= b)[0]
        if len(ia) and len(ib) and ia[0] < ib[-1]:
            gao[k] = float(ltp[ib[-1]] - ltp[ia[0]])
    for tr in trades:
        if not (t[0] <= tr["t_in"] <= t[-1]): continue
        d = 1 if tr["rr"] == "CE" else -1
        si = np.where(np.isclose(strikes, tr["strike"]))[0]
        if not len(si): continue
        side = 0 if tr["rr"] == "CE" else 1
        i0 = np.searchsorted(t, tr["t_in"] + 30); i1 = np.searchsorted(t, tr["t_out"])
        wrong = np.where((ltp[i0:i1] - vw[i0:i1]) * d < 0)[0]
        if len(wrong):
            j = i0 + wrong[0]; bid = float(opt[j, si[0], side, 0])
            r_new = (bid / tr["entry"] - 1) * 100 if np.isfinite(bid) and bid > 0 else np.nan
        else:
            j, r_new = None, tr["ret_pct"]
        res.append(dict(day=day, time_in=tr["time_in"], rr=tr["rr"], ret_real=tr["ret_pct"], ret_vwap_exit=r_new,
                        vwap_exit_s=(float(t[j] - tr["t_in"]) if j is not None else None),
                        in_wrong_side_at_entry=bool((ltp[max(i0 - 30, 0)] - vw[max(i0 - 30, 0)]) * d < 0), vwap_src="ATP" if use_atp else "TWAP"))
pd.DataFrame(res).to_csv(os.path.join(OUT, f"phaseB_vwap_exit_{day}.csv"), index=False)
json.dump(gao, open(os.path.join(OUT, f"phaseB_gao_{day}.json"), "w"))
print(day, len(res), "trades", gao)
