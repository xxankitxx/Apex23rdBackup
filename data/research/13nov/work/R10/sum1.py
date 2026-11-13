import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
import json, numpy as np
r = json.load(open(r"D:\ApexOptions\data\research\13nov\work\R10\study2.json"))
H = (60,120,180,300,600,900)
print("variant      | " + " | ".join(f"{h//60}m IC  top  pos" for h in H))
for k, per in r["abl"].items():
    s = []
    for h in H:
        ic = [v[f"ic{h}"] for v in per.values()]; top = [v[f"top{h}"] for v in per.values()]
        s.append(f"{np.mean(ic):+.3f} {np.mean(top):.3f} {sum(x>0 for x in ic):2d}")
    print(f"{k:18s}| " + " | ".join(s))
# per day for all|lag0 and all|lag30 top60/top180
for k in ("all|lag0", "all|lag30"):
    print(k)
    for d, v in r["abl"][k].items():
        print(" ", d, " ".join(f"ic{h//60}={v[f'ic{h}']:+.3f}/top={v[f'top{h}']:.3f}" for h in (60,180,300)))
print(r["fus_w"]["lag0_H180"]["2026-11-11"], r["fus_w"]["lag30_H180"]["2026-11-11"])
