"""
The rule register, in code (docs/28 §6, docs/31). `apex/rules/register.json` is ADD-ONLY: a rule is never edited
(tests/test_rule_register.py pins every frozen one). What happens to a rule later (passed, failed, switched off)
goes to `apex/rules/status.jsonl`, one dated line per change; the latest line is the rule's status.

* propose(): a new rule from a weather-card line (family, factor, op, line), frozen today, first test day = the
  next trading day. Refused when it duplicates a rule already registered, or is a NEAR-DUPLICATE of a rule that
  failed or was switched off within the last NEAR_DAYS trading days (same family and factor, a line within NEAR_REL
  of that factor's range; docs/28 §6), so the search cannot re-propose "breadth >= 58 %" the day after
  "breadth >= 60 %" failed.
* test_days(): the days a rule is scored on (from its first test day on, never earlier).
* luck_line(): "N rules under test across F families; P passed; about M of those passes are expected by luck".
"""
import json
import os
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTER = os.path.join(ROOT, "apex", "rules", "register.json")
STATUS = os.path.join(ROOT, "apex", "rules", "status.jsonl")
NEAR_REL = 0.20                  # docs/28 §6: a line within +-20 % of the factor's range of a failed one ...
NEAR_DAYS = 20                   # ... is blocked for 20 trading days after the failure
STATUSES = ("under_test", "passed_first_window", "full_standing", "failed", "off")


def load(path=REGISTER):
    return json.load(open(path, encoding="utf-8"))


def save(reg, path=REGISTER):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(reg, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def next_trading_day(d):
    from .. import config
    x = d + timedelta(days=1)
    while not config.is_trading_day(x):
        x += timedelta(days=1)
    return x


def statuses(path=STATUS):
    """{rule id: latest status line}."""
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            out[r["id"]] = r
    return out


def record_status(rid, status, day, note="", path=STATUS, reg=None):
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}")
    reg = reg or load()
    if rid not in {r["id"] for r in reg["rules"]}:
        raise KeyError(rid)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"id": rid, "status": status, "day": str(day), "note": note}) + "\n")


def _same_idea(a, b, factor_range=None):
    """Same family and factor, and a line within NEAR_REL of the factor's range (when the range is unknown: of
    max(|line|, 1))."""
    if a.get("family") != b.get("family") or a.get("factor") != b.get("factor"):
        return False
    la, lb = a.get("line"), b.get("line")
    if la is None or lb is None:
        return la == lb
    span = float(factor_range) if factor_range else max(abs(float(lb)), 1.0)
    return abs(float(la) - float(lb)) <= NEAR_REL * span


def trading_days_between(a, b):
    """Trading days after date a up to and including date b."""
    from .. import config
    n, x = 0, a
    while x < b:
        x += timedelta(days=1)
        n += config.is_trading_day(x)
    return n


def propose(reg, family, factor, op, line, restricted_book, free_book, reason, today=None, st=None,
            factor_range=None):
    """A new frozen rule dict, or raises ValueError with the blocking rule's id. factor_range = the factor's
    max - min on the rows it was found on (the weather card gives it)."""
    if op not in (">=", "<"):
        raise ValueError("op must be '>=' or '<'")
    today = today or date.today()
    st = statuses() if st is None else st
    new = {"family": family, "factor": factor, "op": op, "line": float(line)}
    for r in reg["rules"]:
        if r.get("factor") is None:
            continue
        if r.get("family") == family and r.get("factor") == factor and r.get("op") == op                 and float(r["line"]) == float(line):
            raise ValueError(f"already registered as {r['id']}")
        if _same_idea(new, r, factor_range):
            srow = st.get(r["id"]) or {}
            s = srow.get("status", "under_test")
            if s in ("failed", "off"):
                since = trading_days_between(date.fromisoformat(srow["day"]), today) if srow.get("day") else 0
                if since < NEAR_DAYS:
                    raise ValueError(f"near-duplicate of {r['id']} ({s} {srow.get('day')}, blocked for "
                                     f"{NEAR_DAYS - since} more trading days): {r['factor']} {r['op']} {r['line']}")
    n = max(int(r["id"].split("-")[1]) for r in reg["rules"]) + 1
    return {"id": f"R-{n:03d}", "name": f"{family}: {factor} {op} {line:g}", "kind": "entry", "family": family,
            "factor": factor, "op": op, "line": float(line),
            "condition": f"enter only if weather_trig.{factor} {op} {line:g} at the trigger second (docs/27, "
                         "apex/engine/weather.py); a missing value blocks the entry",
            "restricted_book": restricted_book, "free_book": free_book, "frozen": today.isoformat(),
            "first_test_day": next_trading_day(today).isoformat(),
            "source": "weather card: found by searching the past (apex/conductor/search.py)", "reason": reason}


def add(rule, path=REGISTER):
    """Append a proposed rule to the register (never touches an existing one)."""
    reg = load(path)
    if rule["id"] in {r["id"] for r in reg["rules"]}:
        raise ValueError(f"{rule['id']} exists")
    reg["rules"].append(rule)
    save(reg, path)
    return rule


def test_days(rule, days):
    """The days a rule is scored on: from its first test day on."""
    f = rule["first_test_day"]
    return [d for d in sorted(days) if d >= f]


def luck_line(reg, st=None):
    st = statuses() if st is None else st
    rules = [r for r in reg["rules"] if r.get("kind") == "entry"]
    under = [r for r in rules if (st.get(r["id"]) or {}).get("status", "under_test") not in ("failed", "off")]
    fams = {r["family"] for r in under}
    passed = [r for r in under if (st.get(r["id"]) or {}).get("status") in ("passed_first_window", "full_standing")]
    return (f"{len(under)} rules under test across {len(fams)} families; {len(passed)} passed; about "
            f"{0.05 * len(fams):.1f} of those passes are expected by luck")
