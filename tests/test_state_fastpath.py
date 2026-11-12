"""5 Nov speed work: the fast publish path writes exactly the bytes the old write(clean(state)) did; the council
books share one LiveDay; the kill-switch stat is cached."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex import table  # noqa: E402

CASES = [
    {"a": 1.5, "b": [1, 2, (3, 4)], "c": {"d": None, "e": "text"}},
    {"nan": float("nan"), "inf": [float("inf"), -float("inf")], "ok": 2.0},
    {"np": np.float64(1.25), "npnan": np.float32("nan"), "i": np.int64(7), "arr": np.array([1.0, np.nan])},
    {"msg": "iv NaN on 23800 CE", "deep": [{"x": [float("nan")]}]},
    {"msg": "Infinity and beyond", "v": 3},
]


class _Blob:
    """StateBlob without shared memory: capture the bytes each path would write."""
    HDR = table.StateBlob.HDR

    def __init__(self):
        import struct  # noqa: F401
        self.buf = bytearray(4 * 1024 * 1024)
        self.shm = type("S", (), {"buf": memoryview(self.buf)})()

    def last(self):
        _, n = self.HDR.unpack_from(self.buf, 0)
        return bytes(self.buf[self.HDR.size:self.HDR.size + n])


def test_fast_path_is_byte_identical():
    for obj in CASES:
        a, b = _Blob(), _Blob()
        table.StateBlob.write(a, table.clean(obj))
        table.StateBlob.write_state(b, obj)
        assert a.last() == b.last(), obj
        json.loads(b.last())                       # valid JSON the dashboard can parse (no NaN tokens)


def test_council_books_share_one_live_day():
    from apex.engine import council
    a = council.shared_day("2026-11-05", "2026-11-10")
    assert council.shared_day("2026-11-05", "2026-11-10") is a
    b = council.shared_day("2026-11-06", "2026-11-10")
    assert b is not a and ("2026-11-05", "2026-11-10") not in council._DAYS    # an old day is dropped


def test_slow_parts_spliced_as_text_give_the_same_state():
    """11 Nov: write_state(obj, raw=...) splices pre-encoded parts; the dashboard must parse the same object."""
    for obj in CASES:
        full = dict(obj, straddle_watch={"px": 1.0, "series": [[1.0, float("nan"), 2.0]]}, ideas=None, variants=[{"n": 1}])
        a, b = _Blob(), _Blob()
        table.StateBlob.write_state(a, full)
        rest = {k: v for k, v in full.items() if k not in ("straddle_watch", "ideas", "variants")}
        sw = table.dumps_part({"px": 1.0})
        sw = sw[:-1] + ',"series":' + table.dumps_part(full["straddle_watch"]["series"]) + "}"
        table.StateBlob.write_state(b, rest, raw={"straddle_watch": sw, "ideas": table.dumps_part(None),
                                                  "variants": table.dumps_part(full["variants"])})
        assert json.loads(a.last()) == json.loads(b.last()), obj
    c = _Blob()
    table.StateBlob.write_state(c, {}, raw={"k": "1"})
    assert json.loads(c.last()) == {"k": 1}
