"""
Frozen entry rules as code (Conductor stage 5, the restricted books; docs/31, apex/rules/register.json).

A book whose parameters carry `rules=("R-00x", ...)` is a RESTRICTED book: the same book with those conditions
switched on. At an entry (after the contract is chosen, at the trigger second) each listed rule that applies to the
entry's pattern is checked on the weather photograph (apex/engine/weather.py, which reads only data that had
arrived by then). A failed check skips the setup, like every other entry veto; nothing else about the book changes.

The code below is the register's text, nothing more: R-002 and R-003 read the same er60 / dir60 / breadth_dir values
the photograph records, with the register's numbers. tests/test_restricted_books.py checks every coded rule
against the register (id present, frozen, condition numbers) so the two cannot drift apart.
"""
TREND_PATTERNS = ("SPOT-BREAKOUT", "SPOT-RETEST", "SPOT-RETEST-FILL", "SPOT-PULLBACK", "ORB", "CO-FIRST", "FORMING",
                  "BASKET-LED", "FUTURES-LED", "FOLLOW", "COUNCIL-NORM")
IMPULSE_PATTERNS = ("SPOT-BREAKOUT", "ORB", "SPOT-PULLBACK", "CO-FIRST", "FORMING", "BASKET-LED", "FUTURES-LED")
LONG_HOLD_PATTERNS = ("ORB",)                    # R-005: median hold > 15 min on the live record 19 Oct - 6 Nov

ER60_MIN = 0.35                                  # R-002
BREADTH_MIN = 0.60                               # R-003
COUNCIL_NORM_END = (12, 0)                       # R-004
LONG_HOLD_END = (14, 30)                         # R-005


def entry_pattern(book, ctx, why=None):
    """The entry's pattern, as the diaries classify it (apex/conductor/diary.py)."""
    w = str(why or "")
    if w.startswith("COUNCIL EXP"):
        return "COUNCIL-EXP"
    if w.startswith("COUNCIL NORM"):
        return "COUNCIL-NORM"
    if getattr(book, "name", "") == "t28_fwd":
        return "FWD-PULLBACK"
    return book.ctl.get("ep_type") or (ctx.get("episode") or {}).get("type") or "UNKNOWN"


def _hm(ctx):
    t = ctx.get("now_dt")
    return (t.hour, t.minute) if t is not None else None


def r002(w, ctx, pattern):
    if pattern not in TREND_PATTERNS or w.get("expiry_day") is not False:
        return None                                  # normal days only (an unknown day type is not a normal day)
    er, d = w.get("er60"), w.get("dir60")
    if w.get("mins_open") is not None and w["mins_open"] < 60:
        return "R-002: before 10:15 (no full last hour yet)"
    if er is None or d is None:
        return "R-002: last hour's trend unknown (before 10:15 or a data hole)"
    if er < ER60_MIN or d != 1:
        return f"R-002: last hour not trending our way (efficiency {er:.2f}, direction {'with' if d == 1 else 'against'})"
    return None


def r003(w, ctx, pattern):
    if pattern not in IMPULSE_PATTERNS:
        return None
    b = w.get("breadth_dir")
    if b is None:
        return "R-003: breadth unknown"
    if b < BREADTH_MIN:
        return f"R-003: breadth {b:.0%} < {BREADTH_MIN:.0%}"
    return None


def r004(w, ctx, pattern):
    if pattern != "COUNCIL-NORM" or w.get("expiry_day") is not False:
        return None
    hm = _hm(ctx)
    if hm is not None and hm >= COUNCIL_NORM_END:
        return "R-004: council normal-day entries end 12:00"
    return None


def r005(w, ctx, pattern):
    if pattern not in LONG_HOLD_PATTERNS:
        return None
    hm = _hm(ctx)
    if hm is not None and hm >= LONG_HOLD_END:
        return "R-005: long-hold family, no entry from 14:30"
    return None


CODED = {"R-002": r002, "R-003": r003, "R-004": r004, "R-005": r005}


def check(book, ctx, opt, why=None):
    """None if every rule on the book allows this entry; else the first refusal's text."""
    ids = (getattr(book, "p", None) or {}).get("rules") or ()
    if not ids:
        return None
    from .weather import photo
    d = 1 if (opt or {}).get("rr") == "CE" else -1
    w = photo(ctx, d, opt, book)
    pattern = entry_pattern(book, ctx, why)
    for rid in ids:
        fn = CODED.get(rid)
        if fn is None:
            return f"{rid}: not a coded rule"        # never trade a restricted book whose rule cannot be checked
        msg = fn(w, ctx, pattern)
        if msg:
            return msg
    return None
