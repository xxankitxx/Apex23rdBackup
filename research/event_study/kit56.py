"""c20_9x on the kit for 5 and 6 Nov -> kit_trades_56.json (same trade fields as C12_baseline.json)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, r"C:\Users\ANKITM~1\AppData\Local\Temp\claude\D--ApexOptions\4fc710fd-915d-4b6c-be6c-118168a8b13b\scratchpad\team")
sys.path.insert(0, r"D:\ApexOptions")
from c12lib import run  # noqa: E402
from apex.engine.council import c20_9x  # noqa: E402

out = {}
for d in ("2026-11-05", "2026-11-06"):
    r = run(d, c20_9x.KitStrategy(), 2)
    out[d] = r["trades"]
    print(d, len(r["trades"]), round(r["pnl"]), flush=True)
json.dump(out, open(os.path.join(HERE, "kit_trades_56.json"), "w"), indent=1, default=float)
