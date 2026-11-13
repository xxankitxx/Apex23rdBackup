import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
W = r"D:\ApexOptions\data\research\13nov\work\R02"
q = W + r"\pathlib_r02.py"
s = open(q, encoding="utf-8").read()
s = s.replace('''    if sl is not None:
        hits["SL"] = first(bid <= e * (1 - sl))''', '''    if sl is not None:
        sbid = ema(bid, 1.0 / V["sl_tau"]) if V.get("sl_tau") else bid     # stop on a smoothed bid (no 1-s flicker)
        hits["SL"] = first(sbid <= e * (1 - sl))
    if V.get("fsl") is not None and (expd or not V.get("fsl_exp_only", True)):   # thesis stop in forward points
        adv = (fs[0] - fs) if ce else (fs - fs[0])
        hits["FSL"] = first(adv >= V["fsl"])
    if V.get("tp_fix") is not None and (expd or not V.get("tp_exp_only", True)):
        hits["TPX"] = first(bid >= e * (1 + V["tp_fix"]))''')
s = s.replace('''    if book == "c20_9v" and not expd and V.get("pgb", True):''', '''    if (book == "c20_9v" or V.get("pgb_all")) and not expd and V.get("pgb", True):''')
open(q, "w", encoding="utf-8").write(s)
p = W + r"\a4_paths.py"
s = open(p, encoding="utf-8").read()
s = s.replace('''VARIANTS["hold to flat, SL only"]''', '''for x in (0.55, 0.60, 0.70):
    VARIANTS[f"expiry TP {x}"] = {"tp_fix": x}
for tau in (3, 5, 10):
    VARIANTS[f"SL on {tau}s-smoothed bid"] = {"sl_tau": tau}
for f_, c in ((12, 0.25), (15, 0.25), (20, 0.25), (15, 0.20)):
    VARIANTS[f"expiry fwd stop {f_} pts + SL {int(c*100)}%"] = {"fsl": f_, "sl_exp": c}
VARIANTS["PGB on every pool book"] = {"pgb_all": True}
VARIANTS["hold to flat, SL only"]''')
open(p, "w", encoding="utf-8").write(s)
