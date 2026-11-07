"""7 Nov: the frozen rule register (docs/31, apex/rules/register.json). A frozen rule is never edited: a change is a
new rule with a new id and date. This test pins each rule's content, so an edit fails loudly here."""
import hashlib
import json
import os
from datetime import date

from apex import config

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apex", "rules", "register.json")

FROZEN = {                       # id -> sha256[:16] of the rule as frozen. Add new ids; never change a line here.
    "R-001": "f0d8955e216bb4d8", "R-002": "856b9bb40f3d8dab", "R-003": "b8251ea5378a4e13",
    "R-004": "6376a76e249f3bac", "R-005": "85b4e16923dd7a66", "R-006": "0c0402430c5e39fd",
    "R-007": "991eef238477410e", "R-008": "3a6d4cb9920bd9b7", "R-009": "9813cbf59776671e",
    "R-010": "7600be07a0518465", "R-011": "6e24389163f2b522", "R-012": "501d4b0a4b7a2b21",
    "R-013": "9d361860b4bd1506", "R-014": "07ad1a162a92c934", "R-015": "a3a1bf94ed2fc426",
    "R-016": "1d5b846ce26684d3", "R-017": "d863d7b0ddd9b8c2", "R-018": "6b211412f8d0bafe",
}


def _rules():
    return json.load(open(PATH, encoding="utf-8"))["rules"]


def _h(r):
    return hashlib.sha256(json.dumps(r, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def test_frozen_rules_are_unchanged():
    got = {r["id"]: _h(r) for r in _rules()}
    for rid, h in FROZEN.items():
        assert rid in got, f"{rid} was removed: a frozen rule stays in the register (mark it failed / off instead)"
        assert got[rid] == h, f"{rid} was edited after its freeze: write a NEW rule with a new id and date instead"


def test_register_is_well_formed():
    rules = _rules()
    ids = [r["id"] for r in rules]
    assert len(ids) == len(set(ids))
    for r in rules:
        for k in ("id", "name", "kind", "family", "condition", "restricted_book", "free_book", "frozen",
                  "first_test_day", "source", "reason"):
            assert r.get(k), (r["id"], k)
        f, t = date.fromisoformat(r["frozen"]), date.fromisoformat(r["first_test_day"])
        assert t >= f, r["id"]
        assert config.is_trading_day(t) or t.weekday() < 5, r["id"]


def test_named_books_exist():
    books = set(config.VARIANTS) | {"RAW"}
    for r in _rules():
        if r["free_book"] in books or " " not in r["free_book"]:
            assert r["free_book"] in books, (r["id"], r["free_book"])
        rb = r["restricted_book"]
        if " " not in rb:                                  # an existing variant (seeded pairs, R-001)
            assert rb in books, (r["id"], rb)
