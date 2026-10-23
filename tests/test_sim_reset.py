"""Every simulator run starts fresh (owner, 18 Oct 2026): python tests/test_sim_reset.py  (numpy only)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import run_apex  # noqa: E402


def test_each_sim_run_gets_a_fresh_folder_and_continue_resumes_the_latest():
    root = tempfile.mkdtemp(prefix="apex_simreset_")
    orig = run_apex.data_dir_for
    run_apex.data_dir_for = lambda mode: os.path.join(root, mode)
    try:
        a = run_apex.sim_run_dir(stamp="20261018-230000")
        b = run_apex.sim_run_dir(stamp="20261018-231500")
        assert a != b and a.endswith("20261018-230000")
        assert run_apex.latest_sim_dir() is None                    # nothing created yet
        os.makedirs(a); os.makedirs(b); os.makedirs(os.path.join(root, "sim", "paper"))  # legacy folder ignored
        assert run_apex.latest_sim_dir() == b
        assert run_apex.sim_run_dir(resume=True) == b               # --continue
        assert run_apex.sim_run_dir(resume=False, stamp="20261018-232000") != b   # default: fresh
        assert run_apex._mode_dir("sim", None) == b                 # learn/report follow the latest run
    finally:
        run_apex.data_dir_for = orig


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
