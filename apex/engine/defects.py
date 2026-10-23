"""
Evidence hygiene (D-101, after the D-095 frozen-quote incident of 19 Oct 2026).

Two independent, auditable reasons keep a recorded trade OUT of the evidence (SPRT, challenger and
control tests, advisor screens, candidate diagnostics) while it stays on file and in the report:

 1. QUOTE DEFECT (per trade, automatic). The option's exchange stamp at entry or exit
    (paper._trade_age: now - ltt, recorded as trade_age_in / trade_age_out) is older than
    config.QUOTE_DEFECT_AGE_S, or older than the trade's own day (a previous-session quote).
    Derived from fields already in every paper/<day>.json since C-18, so it applies retroactively.

 2. DEFECT WINDOW (per day, all books). A feed defect does not only misprice the trades that touch
    the frozen contract: it also blinds every decision that read it (IV, straddle legs, contract
    choice), so books that happened to trade other contracts were selected on polluted inputs, and
    dropping only the mispriced trades would bias every PAIRED test (19 Oct: futures_only keeps its
    10 PE trades, -22.6 %/day, while its 9 frozen CE trades — +36 %, +12 % ... at true prices — are
    dropped). So on a day with a defect, a window is quarantined for EVERY book:
      * automatic: from the first defective entry (or the open, if the stamp is from a previous
        session — the contract never updated that day) to the last defective exit;
      * declared: windows the owner lists in data/learning/defects.json, e.g.
        [{"day": "2026-10-19", "from": "09:15:00", "to": "11:05:00", "ref": "D-095",
          "reason": "CE quotes frozen at Friday's close (ttq ordering guard)"}]
        "to" = the engine restart on the fixed code. A window covering the whole session removes
        the day from the evidence entirely (it is not a 0 % day).
    The union of both is used. Nothing here changes a trading decision.
"""
import json
import os

from .. import config

DEFECTS_FILE = os.path.join(config.LEARN_DIR, "defects.json")
_DAY_S = 86400.0


def _secs(hms):
    try:
        h, m, s = (str(hms) + ":0:0").split(":")[:3]
        return int(h) * 3600 + int(m) * 60 + int(float(s))
    except (TypeError, ValueError):
        return None


def _hms(x):
    return "%02d:%02d:%02d" % (x // 3600, (x % 3600) // 60, x % 60)


def quote_defect(t):
    """The reason this trade's price is not a real quote, or None. Legacy rows without the stamps
    are not flagged (they cannot be checked; the report counts them as unverified)."""
    lim = float(getattr(config, "QUOTE_DEFECT_AGE_S", 600.0))
    why = []
    for side, k, tk in (("entry", "trade_age_in", "time_in"), ("exit", "trade_age_out", "time_out")):
        a = t.get(k)
        if a is None:
            continue
        try:
            a = float(a)
        except (TypeError, ValueError):
            continue
        if a > lim:
            sod = _secs(t.get(tk))
            prior = sod is not None and a > sod            # stamp older than this day's midnight
            why.append(f"{side} quote {a / 3600:.1f} h old" + (" (previous session)" if prior else "")
                       if a >= 3600 else f"{side} quote {a:.0f} s old")
    return "; ".join(why) or None


def is_prior_session(t):
    sod = _secs(t.get("time_in"))
    a = t.get("trade_age_in")
    try:
        return a is not None and sod is not None and float(a) > sod
    except (TypeError, ValueError):
        return False


def load_declared(path=None):
    """Owner-declared defect windows: {day: [(from_s, to_s, ref, reason)]}. A missing file is no windows;
    an unreadable one is reported by the caller (never silently treated as 'no defects')."""
    path = path or DEFECTS_FILE
    out, err = {}, None
    if not os.path.exists(path):
        return out, None
    try:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        for r in rows:
            a, b = _secs(r.get("from", "00:00:00")), _secs(r.get("to", "23:59:59"))
            if a is None or b is None or b < a:
                raise ValueError(f"bad window {r!r}")
            out.setdefault(str(r["day"]), []).append((a, b, r.get("ref", ""), r.get("reason", "")))
    except Exception as e:                                  # noqa: BLE001 — reported, not swallowed
        err = f"{type(e).__name__}: {e}"
    return out, err


def auto_windows(rows):
    """rows = days.jsonl rows (every book). {day: (from_s, to_s, n_defect_trades)} from quote defects."""
    out = {}
    for r in rows:
        for t in r.get("trades") or []:
            if not quote_defect(t):
                continue
            a = config.mins(config.MARKET_OPEN) * 60 if is_prior_session(t) else _secs(t.get("time_in"))
            b = _secs(t.get("time_out") or t.get("time_in"))
            if a is None or b is None:
                continue
            lo, hi, n = out.get(r["day"], (a, b, 0))
            out[r["day"]] = (min(lo, a), max(hi, b), n + 1)
    return out


class Quarantine:
    """Decides, per (day, trade), whether a recorded trade is evidence. Built once per learn()."""

    def __init__(self, rows, declared=None, declared_err=None):
        self.auto = auto_windows(rows)
        if declared is None:
            declared, declared_err = load_declared()
        self.declared = declared
        self.err = declared_err

    def windows(self, day):
        w = [(a, b, "auto", f"{n} quote-defect trade(s)") for a, b, n in [self.auto[day]]] if day in self.auto else []
        return w + [(a, b, ref or "declared", why) for a, b, ref, why in self.declared.get(day, [])]

    def whole_day(self, day):
        o, c = config.mins(config.MARKET_OPEN) * 60, config.mins(config.MARKET_CLOSE) * 60
        return any(a <= o and b >= c for a, b, _, _ in self.declared.get(day, []))

    def reason(self, day, t):
        q = quote_defect(t)
        if q:
            return "quote defect: " + q
        ti = _secs(t.get("time_in"))
        for a, b, ref, _ in self.windows(day):
            if ti is not None and a <= ti <= b:
                return f"defect window {_hms(a)}-{_hms(b)} ({ref})"
        return None

    def in_window(self, day, hms):
        if self.whole_day(day):
            return True
        x = _secs(hms)
        return x is not None and any(a <= x <= b for a, b, _, _ in self.windows(day))
