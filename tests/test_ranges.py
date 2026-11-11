"""10 Nov, evening (docs/41 section 12.3): premium-return ranges in the forecast record (apex/predict/ranges.py).
These tests pin behaviour: silence without a usable artefact, ordered quantiles, the scale floor, the arithmetic,
and that the installed artefact loads against the engine's feature schema. Not that the ranges are right."""
import os
import time

import numpy as np

from apex.predict import features as F, ranges as R, targets as T

N = len(F.NAMES)


def artefact(w_mu=0.01, w_sc=0.02, floor=0.005):
    def hz(scale):
        mu = [0.0] * (N + 1)
        sc = [0.0] * (N + 1)
        mu[1 + F.NAMES.index("mom30")] = w_mu
        sc[0] = 0.03 * scale
        sc[1 + F.NAMES.index("mom30")] = w_sc
        return dict(n=1, med=[0.0] * N, sd=[1.0] * N, w_mu=mu, w_sc=sc, floor=floor, zq=[-1.6, 0.0, 1.7])
    return dict(version=1, feature_schema=F.SCHEMA, target_spec=T.SPEC, training_cutoff="2026-11-09", l2=10.0, clip=4.0,
                quantiles=[0.1, 0.5, 0.9], horizons={"60": hz(1.0), "300": hz(2.0)}, hash="test")


def vec(mom=0.0):
    x = np.zeros(N)
    x[F.NAMES.index("mom30")] = mom
    return x


def test_silent_without_an_artefact_or_with_another_schema():
    assert R.Ranger().ranges(vec()) is None and R.Ranger().why == "no range artefact"
    a = artefact()
    a["feature_schema"] = "somethingelse"
    r = R.Ranger(a)
    assert not r.ok and "feature schema" in r.why and r.ranges(vec()) is None
    b = artefact()
    b["target_spec"] = "other"
    assert R.Ranger(b).ranges(vec()) is None
    assert R.Ranger(artefact()).ranges(None) is None


def test_the_arithmetic_and_the_order():
    r = R.Ranger(artefact())
    out = r.ranges(vec(1.0))
    assert set(out) == {60, 300}
    # mean 0.01, scale 0.03 + 0.02 = 0.05 at 60 s
    assert np.allclose(out[60], [0.01 - 1.6 * 0.05, 0.01, 0.01 + 1.7 * 0.05], atol=1e-5)
    assert np.allclose(out[300], [0.01 - 1.6 * 0.08, 0.01, 0.01 + 1.7 * 0.08], atol=1e-5)
    for mom in (-9.0, -1.0, 0.0, 0.5, 9.0):
        for q in r.ranges(vec(mom)).values():
            assert q[0] <= q[1] <= q[2]


def test_the_scale_never_falls_below_its_floor():
    r = R.Ranger(artefact(floor=0.005))
    q = r.ranges(vec(-4.0))[60]                  # scale model says 0.03 - 0.08 < 0: the floor holds
    assert np.isclose(q[2] - q[0], 3.3 * 0.005, atol=1e-5)


def test_a_missing_feature_counts_as_typical_and_extremes_are_clipped():
    r = R.Ranger(artefact())
    x = vec(0.0)
    x[3] = np.nan
    assert r.ranges(x) == r.ranges(vec(0.0))
    assert r.ranges(vec(1e9)) == r.ranges(vec(4.0))


def test_the_installed_artefact_loads_and_is_cheap():
    path = os.path.join(os.path.dirname(os.path.abspath(R.__file__)), "ranges_v1.json")
    r = R.Ranger(path=path)
    assert r.ok, r.why
    assert r.horizons == (60, 300)
    out = r.ranges(vec(0.0))
    assert all(q[0] < q[1] < q[2] for q in out.values())
    assert out[300][2] - out[300][0] > out[60][2] - out[60][0]      # the longer horizon is the wider range
    t0 = time.perf_counter()
    for _ in range(2000):
        r.ranges(vec(0.3))
    assert (time.perf_counter() - t0) / 2000 < 0.002                 # generous: asked only when a record is written


def test_the_ledger_record_carries_the_range(tmp_path):
    import json
    from tests.test_pred import Tape, artefact as model
    from apex.engine import pred
    tp = Tape(model(), str(tmp_path))
    tp.p.rg = R.Ranger(artefact())
    tp.step(400)
    tp.p.led.flush()
    rows = [json.loads(l) for l in open(tp.p.led.fpath, encoding="utf-8")]
    assert rows and all(set(r["forecast"]["range"]) == {"60", "300"} and r["forecast"]["range_model"] == "test" for r in rows)
    bare = Tape(model(), None)                       # no range artefact: the record is as before, and nothing breaks
    assert bare.p.rec(vec(), dict(pT={300: 0.2}, pA={300: 0.1}, edge=0.1)).keys() == {"pT", "pA", "edge"}
