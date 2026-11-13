"""13 Nov: one patient atomic file swap for every writer.

On Windows os.replace is refused (PermissionError, WinError 5 or 32) while another process has the source or the
target open: Defender scanning the fresh .tmp, the search indexer, the dashboard's static server reading the target.
The lock usually clears within tens of milliseconds but under load it can take over a second. 12 Nov: the engine's
day file was refused hundreds of times (saved later by its retry thread), the Forecast Lab's dashboard file 1,726
times, and four replays died on a refused chain_latest.json swap because the old helper gave up after 1.8 s and
raised.

replace() retries with a growing wait inside a time budget. With must=False it never raises: it returns False,
removes nothing, and the caller's next write tries again (snapshots that are rewritten every second or minute).
"""
import os
import time

DEFAULT_BUDGET_S = 3.0          # a durable file (books, learning): worth waiting for
SNAPSHOT_BUDGET_S = 0.25        # a file rewritten every second (dashboard, chain snapshot): the next write will do

STATS = {"ok": 0, "retried": 0, "refused": 0, "last": ""}


def replace(src, dst, budget_s=DEFAULT_BUDGET_S, must=True):
    """os.replace(src, dst), retried on PermissionError for up to budget_s seconds (waits 5, 10, 20 ... 200 ms).
    True when done. When the budget runs out: raises the last PermissionError if must, else returns False and leaves
    src in place. Any other OSError raises at once when must, else returns False."""
    t_end = time.monotonic() + max(0.0, budget_s)
    wait, tries = 0.005, 0
    while True:
        try:
            os.replace(src, dst)
            STATS["ok"] += 1
            if tries:
                STATS["retried"] += 1
            return True
        except PermissionError as e:
            tries += 1
            if time.monotonic() + wait > t_end:
                STATS["refused"] += 1
                STATS["last"] = f"{os.path.basename(dst)}: {e.__class__.__name__} after {tries} tries"
                if must:
                    raise
                return False
            time.sleep(wait)
            wait = min(wait * 2.0, 0.2)
        except OSError as e:
            STATS["refused"] += 1
            STATS["last"] = f"{os.path.basename(dst)}: {e.__class__.__name__}"
            if must:
                raise
            return False


def write_text(path, text, budget_s=DEFAULT_BUDGET_S, must=True, fsync=False, tmp=None, newline=None):
    """Write text to a temporary file beside path, then swap it in with replace(). Returns replace()'s answer."""
    tmp = tmp or path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)
        if fsync:
            f.flush()
            os.fsync(f.fileno())
    return replace(tmp, path, budget_s=budget_s, must=must)
