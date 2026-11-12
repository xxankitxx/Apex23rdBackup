"""Forecast Lab panel payloads for the dashboard's contract test (tests/js/lab_payload_contract_test.js).

Built from the real 11 Nov 15:14 payloads in this folder. Each variant gets its earned() block and its commentary from
apex.forecast_lab.core, exactly as panel() adds them, so the page is tested against what the Lab really writes.
Writes <out>/<name>.json and <out>/manifest.json: for each case the payload file, the page clock to use (seconds),
the body classes the engine would set, and the payload to feed first (for a 'stopped after running' sequence).

    py -3.13 tests/fixtures/forecast_lab/make_payloads.py [out_dir]     (default: tests/fixtures/forecast_lab/gen)

Reads only this folder; imports apex.forecast_lab.core (no engine module). Display data only.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from apex.forecast_lab import core  # noqa: E402

FLAT = "payload_2026-11-11_1514_flat.json"
HELD = "payload_2026-11-11_1514_held.json"
DAY_S = 86400.0


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def finish(p, cross=None):
    """What panel() adds after the numbers: earned(), the median flags, the commentary. JSON round trip as written."""
    p = json.loads(json.dumps(p))
    if p.get("ok"):
        p.setdefault("day", "2026-11-11")
        p["earned"] = core.earned(p, cross=cross, memo={})
        dh = p["earned"].get("dir_h") or {}
        for x in p.get("path") or []:
            x["draw_median"] = bool((dh.get(str(x["h"])) or {}).get("earned"))
    p["say"] = core.commentary(p) if p.get("ok") else dict(now=[str(p.get("why"))])
    return json.loads(json.dumps(p))


def runner(p):
    r = dict(p.get("runner") or {})
    r.update(learning=dict(ok=True, source="state.json", why="loaded", restarts=0, updates=411279),
             brain="on", nightly=dict(day="2026-11-11", steps=dict(lab=dict(status="ok", secs=812, why=None),
                                                                     hazard=dict(status="fail", secs=1200, why="time limit 1200 s reached")),
                                      missed_days=[]), errors=0, write_fails=0)
    return r


def cases():
    flat, held = load(FLAT), load(HELD)
    t = float(flat["t"])
    out = {}

    p = copy.deepcopy(flat)
    p["runner"] = runner(p)
    p["record_days"] = [dict(day="2026-11-10", forward=True, restarts=0, cov5=0.79, cov15=0.71, dir5=0.52, dir5_n=310,
                             brier5=0.2493, clim5=0.2488, opt5_n=640),
                        dict(day="2026-11-09", forward=False, restarts=1, cov5=0.83, cov15=0.9, dir5=0.55, dir5_n=280,
                             brier5=0.248, clim5=0.25, opt5_n=600)]
    out["flat"] = dict(p=finish(p), now=t + 2, body=[])

    p = copy.deepcopy(held)
    p["runner"] = runner(p)
    p["held"] = dict(strike=25150.0, side="CE", expiry="2026-11-17", entry=230.5, qty=650, t_in=t - 900,
                     book="c20_9y", rules=None)
    out["held"] = dict(p=finish(p), now=t + 2, body=["holding", "cmt-on"])

    out["stale"] = dict(p=out["flat"]["p"], now=t + 40, body=[])

    err = dict(ok=False, why="shared table: not found", t=t + 60, now="15:15:13", date="2026-11-11", last_ok_t=t,
               errors=1, hist=[], runner=runner(flat))
    out["ok_false"] = dict(p=finish(err), now=t + 61, body=[], first="flat")

    p = copy.deepcopy(flat)
    for k in ("chain", "decay", "rent", "options"):
        p.pop(k, None)
    p["volx"] = dict(p.get("volx") or {}, implied=None)
    out["chain_missing"] = dict(p=finish(p), now=t + 2, body=[])

    # 12 Nov 09:10 IST, before the Lab is started: yesterday's file
    out["previous_day"] = dict(p=out["flat"]["p"], now=t + DAY_S - 6 * 3600 - 4 * 60, body=[])

    p = copy.deepcopy(flat)
    for f in p["score"]["fut"]:
        if f["h"] == 300:
            f.update(n=1125, cov=0.80)           # on target: 1125 x 5 / 300 = 18.75 independent checks
        elif f["h"] == 600:
            f.update(n=789, cov=0.573)           # 6.6 checks: unchecked
        elif f["h"] == 900:
            f.update(n=4000, cov=0.66)           # 22 checks, caught 66 %: narrow (30 min is past the close here)
        elif f["h"] == 60:
            f.update(n=1125, cov=0.95)           # wide
    out["unearned_horizons"] = dict(p=finish(p), now=t + 2, body=[])

    p = copy.deepcopy(flat)
    p["stale"] = "the futures quote is 9 s old"
    for k in ("path", "path_F", "regime", "volx", "breadth", "experts", "signals"):
        p.pop(k, None)
    p.pop("options", None)
    out["quote_stale"] = dict(p=finish(p), now=t + 2, body=[])
    return out


def main(out_dir=None):
    out_dir = out_dir or os.path.join(HERE, "gen")
    os.makedirs(out_dir, exist_ok=True)
    man = []
    for name, c in cases().items():
        fn = f"{name}.json"
        tmp = os.path.join(out_dir, fn + ".tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(c["p"], f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, os.path.join(out_dir, fn))
        man.append(dict(name=name, file=fn, now=c["now"], body=c["body"], first=c.get("first")))
    tmp = os.path.join(out_dir, "manifest.json.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(man, f, indent=1)
    os.replace(tmp, os.path.join(out_dir, "manifest.json"))
    return out_dir, man


if __name__ == "__main__":
    d, m = main(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"{len(m)} payloads written to {d}")
