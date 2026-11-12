"""Checks on the pre-registration ledger research/preregistry.jsonl (PKG-01).

The ledger is append-only: every rule, line, evidence start and verdict rule is written
before any evidence for it is read. These tests read the committed file only.
"""
import datetime
import json
import os
import re
import zoneinfo

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "research", "preregistry.jsonl")
IST = zoneinfo.ZoneInfo("Asia/Kolkata")

REQUIRED = ("id", "written_at", "kind", "subject", "rule", "line", "standard", "evidence_from",
            "min_events", "strata", "counting", "verdict_rule", "hypotheses_tested_to_date")
KINDS = {"retire", "twin", "rule", "promotion", "acceptance", "test"}
STANDARDS = {"docs/28 s2 Conductor-level, all 7 tests", "rule-level, test 6 exempt", "metric"}
# Every PR id the build plan cites, in any package.
PLAN_IDS = ["PR-%03d" % i for i in range(1, 13)]
P43_DEADLINE = datetime.datetime(2026, 11, 12, 8, 10, tzinfo=IST)
STRATA = {"dte0-1", "dte2+"}
EVIDENCE_KINDS = {"forward", "unscored_retrospective"}
# The ideas PKG-01 must pre-register (council plan, PKG-01 ideas list).
PKG01_IDEAS = {"L5-I2", "L3-I1", "L6-I1", "L6-I3", "L1-I5", "L3-I3", "L4-I1", "L4-I2", "L6-I5"}
DOC = os.path.join(ROOT, "docs", "51_build_plan.md")


def _when(s):
    """ISO date or datetime -> aware IST datetime. A bare date means 00:00 IST that day."""
    if len(s) == 10:
        d = datetime.date.fromisoformat(s)
        return datetime.datetime(d.year, d.month, d.day, tzinfo=IST)
    t = datetime.datetime.fromisoformat(s)
    if t.tzinfo is None:
        raise ValueError("timestamp without a zone: " + s)
    return t


def load(path=PATH):
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            if not raw.strip():
                continue
            try:
                rows.append(json.loads(raw))
            except ValueError as e:
                raise AssertionError("line %d does not parse: %s" % (n, e))
    return rows


def check(rows):
    """Return a list of problems (empty when the ledger is valid)."""
    bad = []
    seen = set()
    last = None
    last_id = None
    for r in rows:
        rid = r.get("id", "?")
        miss = [k for k in REQUIRED if k not in r]
        if miss:
            bad.append("%s missing %s" % (rid, miss))
            continue
        if rid in seen:
            bad.append("%s duplicated" % rid)
        seen.add(rid)
        if r["kind"] not in KINDS:
            bad.append("%s kind %r" % (rid, r["kind"]))
        if r["standard"] not in STANDARDS:
            bad.append("%s standard %r" % (rid, r["standard"]))
        if not isinstance(r["strata"], list):
            bad.append("%s strata not a list" % rid)
        elif any(s not in STRATA for s in r["strata"]):
            bad.append("%s strata %r" % (rid, r["strata"]))
        if not (isinstance(rid, str) and re.fullmatch(r"PR-\d{3}", rid)):
            bad.append("%s id format" % rid)
        elif last_id is not None and rid <= last_id:
            bad.append("%s out of order after %s" % (rid, last_id))
        else:
            last_id = rid
        me = r["min_events"]
        if me is not None and (isinstance(me, bool) or not isinstance(me, int) or me < 0):
            bad.append("%s min_events %r" % (rid, me))
        if "evidence_kind" in r and r["evidence_kind"] not in EVIDENCE_KINDS:
            bad.append("%s evidence_kind %r" % (rid, r["evidence_kind"]))
        for k in ("subject", "rule", "line", "counting", "verdict_rule"):
            if not (isinstance(r[k], str) and r[k].strip()):
                bad.append("%s empty %s" % (rid, k))
        try:
            w = _when(r["written_at"])
            ev = _when(r["evidence_from"])
            if len(r["written_at"]) == 10:
                bad.append("%s written_at needs a time" % rid)
            elif w >= ev:
                bad.append("%s written_at %s not before evidence_from %s" % (rid, r["written_at"], r["evidence_from"]))
        except (TypeError, ValueError) as e:
            bad.append("%s bad time: %s" % (rid, e))
        c = r["hypotheses_tested_to_date"]
        if isinstance(c, bool) or not isinstance(c, int) or c < 0:
            bad.append("%s hypothesis count %r" % (rid, c))
        elif last is not None and c < last:
            bad.append("%s hypothesis count fell %d -> %d" % (rid, last, c))
        else:
            last = c
    return bad


@pytest.fixture(scope="module")
def rows():
    assert os.path.exists(PATH), "research/preregistry.jsonl is missing"
    return load()


def test_schema(rows):
    assert rows, "empty ledger"
    assert check(rows) == []
    ids = [r["id"] for r in rows]
    for pid in PLAN_IDS:
        assert pid in ids, pid + " is cited by the plan but not registered"


def test_written_before_evidence(rows):
    for r in rows:
        assert _when(r["written_at"]) < _when(r["evidence_from"]), r["id"]
    pr1 = next(r for r in rows if r["id"] == "PR-001")
    assert _when(pr1["written_at"]) < P43_DEADLINE


def test_hypothesis_count_monotone(rows):
    counts = [r["hypotheses_tested_to_date"] for r in rows]
    assert counts == sorted(counts)
    assert counts[0] >= 65  # the round table examined 65 ideas before the first entry


def test_owner_decides_promotions(rows):
    # Nothing in the ledger promotes itself: every entry leaves promotion to the owner.
    assert all(r.get("promotion_needs_owner") is True for r in rows)


def test_family_veto_waits_for_20_out_of_sample(rows):
    pr2 = next(r for r in rows if r["id"] == "PR-002")
    assert pr2["min_events"] == 20 and pr2["evidence_from"] >= "2026-11-12"
    assert pr2.get("also_reported") == "rule-level, test 6 exempt"


def test_row_lists_capped(rows):
    for r in rows:
        if "rows" in r:
            assert 1 <= len(r["rows"]) <= 5, r["id"]


def test_ascii_only():
    with open(PATH, "rb") as f:
        data = f.read()
    data.decode("ascii")
    assert b"\r\n" not in data


# The checker itself must catch the faults it exists for.

def _good(**kw):
    r = {"id": "PR-900", "written_at": "2026-11-11T23:00:00+05:30", "kind": "rule", "subject": "s",
         "rule": "r", "line": "l", "standard": "metric", "evidence_from": "2026-11-12", "min_events": 1,
         "strata": [], "counting": "c", "verdict_rule": "v", "hypotheses_tested_to_date": 70}
    r.update(kw)
    return r


def test_checker_flags_late_registration():
    assert check([_good(written_at="2026-11-12T09:00:00+05:30")])


def test_checker_flags_missing_key_and_bad_kind():
    r = _good()
    del r["line"]
    assert check([r])
    assert check([_good(kind="promote")])
    assert check([_good(standard="all 7")])


def test_checker_flags_falling_count_and_duplicates():
    assert check([_good(), _good(id="PR-901", hypotheses_tested_to_date=60)])
    assert check([_good(), _good()])
    assert check([_good(), _good(id="PR-901", hypotheses_tested_to_date=71)]) == []


def test_checker_flags_zoneless_time():
    assert check([_good(written_at="2026-11-11T23:00:00")])


def test_checker_flags_bad_values_and_order():
    assert check([_good(min_events=True)])
    assert check([_good(hypotheses_tested_to_date=True)])
    assert check([_good(strata=["expiry"])])
    assert check([_good(evidence_kind="hindsight")])
    assert check([_good(id="PR-9")])
    assert check([_good(id="PR-901"), _good(id="PR-900")])
    assert check([_good(written_at=None)])


def test_package_ideas_all_registered(rows):
    # No idea in PKG-01's list may be silently dropped.
    have = set()
    for r in rows:
        have.update(r.get("ideas", []))
    assert PKG01_IDEAS <= have, sorted(PKG01_IDEAS - have)


def test_seen_numbers_marked_not_evidence(rows):
    # Results the round table already saw must be named, so nobody quotes them as evidence later.
    by = {r["id"]: r for r in rows}
    assert "greyed" in by["PR-002"]["sessions"] and "never quoted as evidence" in by["PR-002"]["sessions"]
    assert "not evidence" in by["PR-006"]["sessions"]
    assert "58-72 %" in by["PR-005"]["sessions"]


def test_build_plan_doc():
    assert os.path.exists(DOC), "docs/51_build_plan.md is missing"
    with open(DOC, "rb") as f:
        text = f.read().decode("ascii")  # no em-dashes or other non-ASCII marks
    assert "->" not in text and "=>" not in text
    for n in range(1, 17):
        assert "PKG-%02d" % n in text, "PKG-%02d missing from docs/51" % n
    for pid in PLAN_IDS:
        assert pid in text, pid + " missing from docs/51"
    for flag in ("FILL_LATE_OBSERVED", "COUNCIL_FILL_EVERY_STEP", "PHOTO_CACHE", "RESTORE_ARM_ON_LAPSE",
                 "TRADE_SAVE_ASYNC", "DECISION_TAPE", "VETO_LOG", "LAPSE_DIAG"):
        assert flag in text, flag + " missing from docs/51"
    assert "## 5. Long runs" in text and "## 6. Decisions only you can make" in text
