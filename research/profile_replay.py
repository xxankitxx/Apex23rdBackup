"""10 Nov 2026 (docs/40 M1, docs/41 section 7): a function-level profile of the engine on a recorded tape.

Runs the single-process fast replay of a tape under cProfile for a fixed number of wall seconds, then writes the
profile and exits. Its own run folder (data/replay/<day>/<stamp>, like every replay), its own port. Run it on an idle
machine: a profile taken beside other heavy jobs measures the other jobs.

Usage: py -3.13 research/profile_replay.py data/ticks/2026-11-09.jsonl.gz [wall seconds, default 600] [port, default 8796]
Output: <run folder>/profile.out and profile_top.txt (the 60 largest by cumulative and by own time)."""
import cProfile, io, os, pstats, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)


def main():
    tape = sys.argv[1]
    wall = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
    port = sys.argv[3] if len(sys.argv) > 3 else "8796"
    # the run folder is set BEFORE any apex module is imported: apex.config reads APEX_DATA at import, and an engine
    # built without it would write into the live data folder
    stem = os.path.basename(tape).split(".")[0]
    run_dir = os.path.join(ROOT, "data", "replay", stem, time.strftime("%Y%m%d-%H%M%S") + "-profile")
    os.makedirs(run_dir, exist_ok=True)
    os.environ.update(APEX_DATA=run_dir, APEX_PORT=port, APEX_FAST="1", APEX_PROFILE="1", PYTHONIOENCODING="utf-8")
    print("profile run folder:", run_dir, flush=True)
    pr = cProfile.Profile()

    def stop():
        pr.disable()
        pr.dump_stats(os.path.join(run_dir, "profile.out"))
        out = io.StringIO()
        st = pstats.Stats(os.path.join(run_dir, "profile.out"), stream=out)
        st.sort_stats("cumulative").print_stats(60)
        st.sort_stats("tottime").print_stats(60)
        with open(os.path.join(run_dir, "profile_top.txt"), "w", encoding="utf-8") as f:
            f.write(out.getvalue())
        print("profile written after", round(time.time() - t0), "s wall", flush=True)
        os._exit(0)
    t0 = time.time()
    sys.argv = ["apex.replay_fast", os.path.abspath(tape)]
    from apex import config, replay_fast
    assert os.path.abspath(config.DATA_DIR) == os.path.abspath(run_dir), "the engine would not write into the run folder"
    threading.Timer(wall, stop).start()
    pr.enable()
    replay_fast.main()
    stop()


if __name__ == "__main__":
    main()
