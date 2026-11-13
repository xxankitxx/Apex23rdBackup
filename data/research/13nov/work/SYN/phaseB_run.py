"""Phase B runner (owner's go-ahead 13 Nov, after the close): every short Phase B script, one at a time, below-normal
priority, one math thread. Items the master plan lists as needing a separate OK (replays, R20 luck margin, R07 eval on
all parts, R13 machine monitor, R14 equivalence) are NOT in this queue.

    py -3.13 phaseB_run.py            (waits for 15:31 IST, then runs the queue; resumes: skips steps already ok)
Writes phaseB_runlog.jsonl (one line per step) and phaseB_out/<nn>_<label>.txt (stdout+stderr of each step)."""
import json, os, subprocess, sys, time, datetime

W = r"D:\ApexOptions\data\research\13nov\work"
OUT = os.path.join(W, "SYN", "phaseB_out")
LOG = os.path.join(W, "SYN", "phaseB_runlog.jsonl")
PY = ["py", "-3.13", "-W", "ignore"]
BELOW_NORMAL = 0x00004000

PARTS = ["2026-10-19", "2026-10-19.p2", "2026-10-19.p3", "2026-10-19.p5", "2026-10-21", "2026-10-22", "2026-10-23",
         "2026-10-23.p2", "2026-10-26", "2026-10-27.p2", "2026-10-27.p3", "2026-10-28", "2026-10-29.p3", "2026-10-29.p4",
         "2026-10-29.p5", "2026-10-30", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06",
         "2026-11-09", "2026-11-11.p4"]      # 11-11, .p2, .p3 have 0 rows
DAYS = sorted({p.split(".")[0] for p in PARTS})


def q():
    s = []   # (label, folder, args, timeout_s, env)
    # Order 1: tier-1 and tier-2 shadows
    s.append(("R05_overlays_build", "R05", ["phaseB_c20_overlays.py"], 900, {}))
    for g in ("KE", "K", "P", "T", "L"):
        s.append((f"R05_overlays_{g}", "R05", ["phaseB_c20_overlays.py", f"--group={g}"], 900, {}))
    for i, line in enumerate(open(os.path.join(W, "R02", "phaseB_list.txt"))):
        a = line.split()
        if a:
            s.append((f"R02_paths_{a[-2]}_{a[-1]}", "R02", a[4:], 600, {}))
    s.append(("R02_merge", "R02", ["phaseB_merge.py"], 600, {}))
    for p in PARTS:
        s.append((f"R18_tod_{p}", "R18", ["phaseB_tod_baseline.py", p], 600, {}))
    for d in DAYS:
        s.append((f"R17_iv_{d}", "R17", ["phaseB_iv_after_entry.py", d, "--marks-only"], 600, {}))
    s.append(("R17_iv_all", "R17", ["phaseB_iv_after_entry.py"], 900, {}))
    s.append(("R17_guards", "R17", ["phaseB_guards_all_books.py"], 900, {}))
    s.append(("R06_reprice", "R06", ["phaseB_reprice_all.py"], 2400, {}))
    s.append(("R06_strike", "R06", ["phaseB_strike_policy.py"], 900, {}))
    s.append(("R19_holdmarks", "R19", ["phaseB_holdmarks_council.py"], 1800, {}))
    s.append(("R19_harness_exit", "R19", ["harness.py", "--exit", "hb300_ret < -6", "--mark", "300", "--holdfile",
                                         os.path.join(W, "R19", "pool_holdmarks.parquet")], 900, {}))
    # Order 2: entries, heavyweights, sisters, microstructure
    s.append(("R01_pb_sweep", "R01", ["phaseB_pb_sweep.py"], 1800, {}))
    s.append(("R01_complements", "R01", ["phaseB_c20_complements.py", "ALL"], 1800, {}))
    for i, b in enumerate((PARTS[0:6], PARTS[6:12], PARTS[12:18], PARTS[18:])):
        s.append((f"R08_hw_{i}", "R08", ["phaseB_hw_all17.py"] + b, 1200, {}))
    s.append(("R08_hw_summary", "R08", ["phaseB_hw_all17.py", "--summary"], 600, {}))
    s.append(("R08_hw_summary2", "R08", ["phaseB_hw_all17.py", "--summary"], 600, {}))   # after the batch-3 rerun
    s.append(("R09_sister_extract", "R09", ["phaseB_sister_extract_all.py"], 4 * 3600, {}))
    s.append(("R09_sister_wf", "R09", ["phaseB_sister_wf.py"], 900, {}))
    for p in PARTS:
        s.append((f"R07_feat_{p}", "R07", ["phaseB_ms_alldays.py", "feat", p], 1500, {}))
    for d in DAYS:
        s.append((f"R16_vwap_{d}", "R16", ["phaseB_vwap_exit_gao.py", d], 600, {}))
    s.append(("R03_daytypes", "R03", ["phaseB_daytypes_dsv2.py"], 900, {}))
    # Order 3: display calibration
    for n in ("phaseB_stand_fit.py", "phaseB_lag_decay.py", "phaseB_behaviour_hyst.py"):
        s.append((f"R10_{n[7:-3]}", "R10", [n], 900, {}))
    for n in ("phaseB_arm_phases.py", "phaseB_verdict_obey.py", "phaseB_retrigger_hold.py"):
        s.append((f"R12_{n[7:-3]}", "R12", [n], 1200, {}))
    s.append(("R11_armed_card", "R11", ["phaseB_armed_card.py"], 900, {}))
    s.append(("R20_bocpd", "R20", ["phaseB_bocpd_ds2.py"], 1200, {}))
    # Order 4: statistics and process
    for seed in range(1, 11):
        s.append((f"R04_null_{seed}", "R04", ["phaseB_conductor_null.py"], 600, {"R04_SEED": str(seed), "R04_ACCUM": "1"}))
    for g in ("fam:t28", "fam:spot_dc12", "fam:c20", "pool_trades"):
        s.append((f"R04_beam_{g.replace(':', '_')}", "R04", ["phaseB_beam_null.py", g], 600, {}))
    s.append(("R19_rolling", "R19", ["phaseB_rolling.py"], 900, {}))
    s.append(("R15_meta", "R15", ["phaseB_meta_of_meta.py"], 900, {}))
    s.append(("R15_dropped", "R15", ["phaseB_dropped_trades_weather.py"], 900, {}))
    s.append(("R13_packets_13nov", "R13", ["phaseB_packet_gaps.py", "2026-11-13"], 900, {}))
    return s


def done_ok():
    ok = set()
    if os.path.exists(LOG):
        for line in open(LOG, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("rc") == 0:
                ok.add(r["label"])
    return ok


def main():
    os.makedirs(OUT, exist_ok=True)
    while datetime.datetime.now().time() < datetime.time(15, 31):
        time.sleep(20)
    ok = done_ok()
    steps = q()
    for n, (label, folder, args, tmo, extra) in enumerate(steps):
        if label in ok:
            continue
        env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                   PYTHONIOENCODING="utf-8", **extra)
        out = os.path.join(OUT, f"{n:03d}_{label}.txt")
        t0 = time.time()
        with open(out, "w", encoding="utf-8") as f:
            try:
                p = subprocess.run(PY + args, cwd=os.path.join(W, folder), stdout=f, stderr=subprocess.STDOUT,
                                   env=env, timeout=tmo, creationflags=BELOW_NORMAL)
                rc = p.returncode
            except subprocess.TimeoutExpired:
                rc = "timeout"
        rec = {"n": n, "of": len(steps), "label": label, "rc": rc, "s": round(time.time() - t0, 1),
               "end": time.strftime("%H:%M:%S")}
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main()
