import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
sys.dont_write_bytecode = True                     # never write __pycache__ under apex\
sys.path.insert(0, r"D:\ApexOptions")
"""Drill of the uncommitted DashWriter (apex/forecast_lab/live.py working tree) against a gateway-like reader.
Writes only to this scratch folder. 60 payloads, 50 ms apart (20x the live rate), reader reads the file the way the
patched gateway does (whole file, then close), holding it 0 or 5 ms."""
import os, threading, time, json
from apex.forecast_lab.live import DashWriter
D = r"D:\ApexOptions\data\research\13nov\work\R13\scratch_dash"; os.makedirs(D, exist_ok=True)
P = os.path.join(D, "forecast_lab.json")
for hold in (0.0, 0.005):
    dw = DashWriter(budget_s=2.0)
    stop = threading.Event(); reads = [0, 0]
    def rd():
        while not stop.is_set():
            try:
                with open(P, "rb") as f:
                    b = f.read(); time.sleep(hold)
                json.loads(b); reads[0] += 1
            except (OSError, ValueError): reads[1] += 1
            time.sleep(0.01)
    open(P, "w").write("{}")
    th = threading.Thread(target=rd, daemon=True); th.start()
    put_ms = []
    for i in range(60):
        t0 = time.perf_counter(); dw.put(P, json.dumps({"t": i, "x": "y" * 35000}), i); put_ms.append((time.perf_counter() - t0) * 1e3)
        time.sleep(0.05)
    dw.flush(5.0); stop.set(); th.join(1)
    print(f"reader hold {hold*1000:.0f} ms: put() max {max(put_ms):.2f} ms; writes {dw.writes}, refused {dw.refused}, "
          f"superseded {dw.superseded}, last landed t {dw.landed_t}; reader ok {reads[0]}, failed {reads[1]}")
