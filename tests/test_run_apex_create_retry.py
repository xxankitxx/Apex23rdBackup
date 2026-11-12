"""12 Nov (PKG-02): run_apex re-creates the shared memory even while the Forecast Lab polls it. On Windows a name that
another process has open cannot be created again, and the Lab maps it for about a millisecond a second, so the
supervisor tries 3 times over 3 s; after that it exits with a message naming the Forecast Lab, its pid and its STOP
file. It never creates the STOP file itself."""
import json
import os

import pytest

import run_apex


class Fake:
    fails = 0
    made = []
    closed = []

    def __init__(self, create=True):
        if Fake.fails > 0:
            Fake.fails -= 1
            raise FileExistsError(183, "Cannot create a file when that file already exists")
        Fake.made.append(self)

    def close(self):
        Fake.closed.append(self)


class Blob:
    def __init__(self, create=True):
        pass


def test_two_collisions_then_the_create_succeeds(tmp_path):
    Fake.fails, Fake.made = 2, []
    waits = []
    t, b = run_apex.create_shared(Fake, Blob, str(tmp_path), sleep=waits.append)
    assert isinstance(t, Fake) and isinstance(b, Blob) and waits == [1.5, 1.5]


def test_three_collisions_exit_naming_the_lab_and_its_stop_file(tmp_path):
    lab = tmp_path / "forecast_lab"
    lab.mkdir()
    (lab / "live.lock").write_text(json.dumps(dict(pid=4321, started=1.0)), encoding="utf-8")
    Fake.fails = 3
    waits = []
    with pytest.raises(SystemExit) as e:
        run_apex.create_shared(Fake, Blob, str(tmp_path), sleep=waits.append)
    msg = str(e.value)
    assert "Forecast Lab (pid 4321)" in msg and os.path.join(str(lab), "STOP") in msg
    assert "—" not in msg and len(waits) == 2
    assert not (lab / "STOP").exists()                                # never made by the supervisor


def test_a_blob_collision_closes_the_table_it_just_made(tmp_path):
    Fake.fails, Fake.made, Fake.closed = 0, [], []
    n = {"blob": 0}

    class BadBlob:
        def __init__(self, create=True):
            n["blob"] += 1
            if n["blob"] == 1:
                raise FileExistsError(183, "exists")
    t, b = run_apex.create_shared(Fake, BadBlob, str(tmp_path), sleep=lambda s: None)
    assert len(Fake.made) == 2 and Fake.closed == [Fake.made[0]] and t is Fake.made[1]


def test_no_lock_file_still_names_the_lab(tmp_path):
    Fake.fails = 3
    with pytest.raises(SystemExit) as e:
        run_apex.create_shared(Fake, Blob, str(tmp_path), sleep=lambda s: None)
    assert "Forecast Lab" in str(e.value) and "STOP" in str(e.value)
