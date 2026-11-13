"""Writes the voice payloads the JS card test renders (tests/js/voice_card_test.js): the real Voice on the synthetic
trigger path of tests/test_voice.py, one payload per mode, plus a holding one.   py -3.13 tests/fixtures/voice/make_payloads.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))
import test_voice as T
from apex.engine.voice import Voice

D, s, eng = T._rig()
v, out = Voice(), {}
for i, f in enumerate(T._path()):
    D.fwd[i] = f; D.i = i
    s.on_second(i, D, None)
    if i >= 1250 and (i % 5 == 0 or i > 2130):
        p = v.view(eng, T._ctx(D, i))
        out.setdefault(p["mode"], json.loads(json.dumps(p, default=float)))
cb = eng.books["conductor"]
key = f"NIFTY|OPT|{T.EXP}|25000|CE"
cb.pos = {"key": key, "rr": "CE", "strike": 25000.0, "lots": 6, "entry": 200.0, "time_in": "11:02:03", "src": "c20_9y",
          "rules": {"mode": "normal", "sl_pct": 15.0, "sl_px": 170.0, "trail_px": 25010.0, "trail_pts": 40.0, "trail_give": 12.0,
                    "fwd_now": 25038.0, "peak_pct": 8.0, "held_s": 600, "clock_left_s": 4800, "flat_at": "15:20", "be_arm_pct": 15.0}}
out["HOLDING"] = json.loads(json.dumps(Voice().view(eng, {"now_s": D.t_open + 7000, "by_key": {key: {"bid": 210.0, "delta": 0.6}}, "w0": T.EXP}), default=float))
for k, p in out.items():
    json.dump(p, open(os.path.join(HERE, f"{k.lower()}.json"), "w"), indent=1)
print(sorted(out))
