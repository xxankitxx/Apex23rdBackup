"""
Self-improvement loop — it gets better on evidence, never on one lucky day.

Every session, every PRE-REGISTERED variant in config.VARIANTS trades its own paper book on
identical data. One is the CHAMPION — its book is the paper account you watch. Alongside:
  * RAW — the champion without any promoted gates, so every advisor's would-have verdict
    can always be scored;
  * CONTROLS (config.CONTROLS: futures_only, random_entry, premium_momentum) — nulls that can
    never become champion; the report says whether the champion beats them (D-065);
  * GATED books "gate:<advisor>" — the champion with one CANDIDATE advisor switched on as a
    hard gate, so a gate is judged on the path it really produces (D-067).

UNIT (D-064): the return on premium per trade, ret% = (exit - entry) / entry x 100. Under the
owner's all-in sizing that is what the account earns; a day's result is the compounded
product of its trades, tested as daily log growth. (Days recorded before D-064 fall back to premium points.)

After the close (engine day-roll or `python run_apex.py learn`):
 1. Scoreboard: Wald SPRT on the champion's per-trade ret% since it became champion,
    H0 mean <= 0 vs H1 mean >= SPRT_DELTA_PCT, sigma SPRT_SIGMA_PCT, alpha 5 %, beta 20 %:
    GO when sum >= (s^2/d) ln((1-b)/a) + n d/2, KILL when sum <= (s^2/d) ln(b/(1-a)) + n d/2.
    Undecided after SPRT_MAX_TRADES trades = KILL. The report prints the observed sd.
 2. Champion replacement (D-066): a challenger (every variant that is not a control) replaces
    the champion only if, over >= CHALLENGER_MIN_DAYS sessions both traded since the champion
    took over, its daily compounded return beats the champion's with mean > 0, a one-sided
    t-test at CHALLENGER_ALPHA / (number of challengers) (Bonferroni), every leave-one-day-out
    mean > 0 — and it has passed on PROMOTE_STREAK consecutive evenings (repeated looks).
    If the champion hits KILL, the best surviving non-control record takes over.
 3. Advisors (D-067): screened on RAW's trades since registration — >= 30 trades and >= 8
    vetoed; removing the vetoed trades improves the mean by >= ADV_MIN_GAIN_PCT per trade; it
    would have vetoed <= 25 % of the top-quartile winners; the improvement survives LODO.
    Passing the screen makes it a CANDIDATE: from the next session a gated book trades it.
    A candidate becomes a GATE only when its gated book beats the champion under rule 2's test
    (Bonferroni over the candidates). A gate is demoted if its RAW screen turns negative.
Nothing here invents new parameters; it only chooses among registered ones.
Decisions are written to data/learning/state.json and report.md, and take effect at the
next session (never intraday — invariant I-11).

Record integrity (WP-3): every file is written tmp + fsync + replace; a torn days.jsonl line is
skipped and kept in days.jsonl.corrupt; an unreadable state.json is kept as state.json.corrupt-<ts>;
an idle weekend or holiday is neither recorded nor learned; a session stopped before the day-roll is
back-filled from paper/<day>.json on the next evening. The report also prints observers (observed-sd
Wald lines, a log-unit SPRT, a betting e-value, champion/look counts, the §9.2 day-level checklist)
that change no decision.
"""
import json
import math
import os
import re
import time
from collections import defaultdict
from datetime import date, datetime

from .. import config
from . import defects

STATE = os.path.join(config.LEARN_DIR, "state.json")
DAYS = os.path.join(config.LEARN_DIR, "days.jsonl")
REPORT = os.path.join(config.LEARN_DIR, "report.md")
ADVISORS = ["iv_late", "room", "coherence", "force", "episode", "book", "premium", "quiet", "bank", "event", "gamma_leg", "gex_room", "regime"]
REGISTERED = "2026-10-17"
GATED_PREFIX = "gate:"


# ── units ────────────────────────────────────────────────────────────────────
def _r(t):
    """Per-trade result in the learning unit: ret% (legacy rows: premium points)."""
    r = t.get("ret_pct")
    return float(r) if r is not None else float(t["pnl_pts"])


def _day_ret(trades):
    """A day's LOG growth, in % units: 100 x sum ln(1 + ret). All-in sizing compounds every exit into
    the next entry, so the account grows by exp(this / 100); the log keeps the ordering of the
    compounded result but stays additive and well-behaved for the t-tests (a 100-trade synthetic
    day would otherwise produce +68,000 % outliers). A -100 % trade is floored at ln(1e-4)."""
    return 100.0 * sum(math.log(max(1e-4, 1.0 + _r(t) / 100.0)) for t in trades)


def sprt_lines(n):
    k = config.SPRT_SIGMA_PCT ** 2 / config.SPRT_DELTA_PCT
    a, b = config.SPRT_ALPHA, config.SPRT_BETA
    slope = n * config.SPRT_DELTA_PCT / 2.0
    return k * math.log((1 - b) / a) + slope, k * math.log(b / (1 - a)) + slope


# ── Student t without scipy (the owner's PC runs numpy only) ─────────────────
def _betacf(a, b, x):
    """Continued fraction for the regularized incomplete beta (Numerical Recipes)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-12:
            break
    return h


def _betai(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_sf(t, df):
    """P(T >= t) for Student t with df degrees of freedom (exact, via the incomplete beta)."""
    if df < 1:
        return 0.5
    if t < 0:
        return 1.0 - t_sf(-t, df)
    return 0.5 * _betai(df / 2.0, 0.5, df / (df + t * t))


def t_crit(alpha, df):
    lo, hi = 0.0, 50.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if t_sf(mid, df) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


# ── durable files (C-09, C-43) ───────────────────────────────────────────────
def _atomic_write_lines(path, lines):
    """Write `lines` (one per line) to `path` so a kill or power cut leaves either the old file or
    the new one, never a torn mix: build the text first, write a .tmp, flush + fsync, then
    os.replace. Windows can refuse the replace while a reader (editor, dashboard, antivirus) holds
    the target, so PermissionError is retried up to 5 times, 0.2 s apart. Any other failure raises
    with the old file untouched."""
    data = "".join(str(x) + "\n" for x in lines)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    for attempt in range(6):                 # the first try + up to 5 retries
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.2)


def _is_trading(day):
    """config.is_trading_day on an ISO string; an unparseable string counts as trading (never drop data)."""
    try:
        return config.is_trading_day(date.fromisoformat(str(day)))
    except ValueError:
        return True


def _is_weekly_expiry(day):
    try:
        d = date.fromisoformat(day)
        w = config.weekly_expiries(datetime(d.year, d.month, d.day, 10, 0, tzinfo=config.IST), 1)
        return bool(w) and w[0] == d
    except Exception:
        return False


# ── state / records ──────────────────────────────────────────────────────────
_NOTES = []          # report lines about damaged files found by this process (state.json preserved, …)
_RECORD_BAD = [0]    # torn days.jsonl rows skipped by record_day since the last report
_LOAD_BAD = [0]      # torn days.jsonl rows skipped by the most recent _load_days


def _default_state():
    return {"registered": REGISTERED, "champion": config.CHAMPION_DEFAULT,
            "champion_since": REGISTERED, "gates": [], "retired": [], "log": [],
            "status": "COLLECTING"}


def _preserve(path, why):
    """Move a damaged file aside as <path>.corrupt-<ts> so the next save cannot overwrite the evidence."""
    dst = path + ".corrupt-" + time.strftime("%Y%m%d-%H%M%S")
    k = 1
    while os.path.exists(dst):
        k += 1
        dst = path + ".corrupt-" + time.strftime("%Y%m%d-%H%M%S") + f"-{k}"
    try:
        os.replace(path, dst)
        _NOTES.append(f"**{os.path.basename(path)} was unreadable ({why}); preserved as "
                      f"`{os.path.basename(dst)}` and defaults were used — check it before trusting this report.**")
    except OSError as e:
        _NOTES.append(f"**{os.path.basename(path)} was unreadable ({why}) and could not be moved aside ({e}); defaults were used.**")
    return dst


def load_state():
    s, err = None, None
    if os.path.exists(STATE):
        for attempt in range(6):
            try:
                with open(STATE, encoding="utf-8") as f:
                    s = json.load(f)
                if not isinstance(s, dict):
                    raise ValueError("not a JSON object")
                err = None
                break
            except PermissionError as e:     # a writer or scanner holds it: wait, do not reset
                s, err = None, e
                time.sleep(0.2)
            except (ValueError, UnicodeDecodeError, OSError) as e:
                s, err = None, e
                break
        if err is not None:
            _preserve(STATE, type(err).__name__)
            s = None
    if s is None:
        s = _default_state()
    else:
        for k, v in _default_state().items():
            s.setdefault(k, v)
    s.setdefault("candidates", {})       # advisor -> day it became a candidate
    s.setdefault("streak", {})           # challenger -> consecutive passing evenings
    s.setdefault("gate_streak", {})      # candidate advisor -> consecutive passing evenings
    _apply_owner_champion(s)
    return s


def _apply_owner_champion(s):
    """D-124: the owner names the champion in config.CHAMPION_OWNER = (book, date). Applied once per (book, date)
    to the stored state: the champion changes, its scoreboard restarts from that date, challenger streaks reset,
    and the log says the owner did it. The learning loop may replace it later on evidence as usual."""
    oc = getattr(config, "CHAMPION_OWNER", None)
    if not oc:
        return
    book, since = oc
    if s.get("owner_champion") == list(oc) or s.get("owner_champion") == tuple(oc):
        return
    if book not in config.VARIANTS or book in config.CONTROLS:
        return
    if s.get("champion") != book or (s.get("champion_since") or "") < since:
        s["log"].append({"day": since, "event": "champion", "from": s.get("champion"), "to": book, "by": "owner (D-124)"})
        s["champion"], s["champion_since"] = book, since
        s["streak"] = {}
        s["retired"] = [r for r in s.get("retired", []) if r != book]
    s["owner_champion"] = list(oc)
    try:
        save_state(s)
    except Exception:
        pass


def save_state(s):
    _atomic_write_lines(STATE, [json.dumps(s, indent=1)])


def already_learned(day):
    s = load_state()
    return s.get("learned_day") == day


def _read_days_rows():
    """Every parseable row of days.jsonl, plus how many were not. A torn or malformed line (a write
    killed mid-line, a bad edit) is skipped and appended once to days.jsonl.corrupt, so the evidence
    is kept but one bad line can never stop learning (C-09)."""
    rows, bad = [], []
    if not os.path.exists(DAYS):
        return rows, 0
    with open(DAYS, encoding="utf-8", errors="replace") as f:
        for line in f:
            x = line.rstrip("\r\n")
            if not x.strip():
                continue
            try:
                r = json.loads(x)
                if not (isinstance(r, dict) and isinstance(r.get("day"), str) and "book" in r
                        and isinstance(r.get("trades"), list)):
                    raise ValueError("not a day row")
                rows.append(r)
            except ValueError:
                bad.append(x)
    if bad:
        cpath = DAYS + ".corrupt"
        try:
            have = set()
            if os.path.exists(cpath):
                with open(cpath, encoding="utf-8", errors="replace") as f:
                    have = {y.rstrip("\r\n") for y in f}
            new = [x for x in bad if x not in have]
            if new:
                with open(cpath, "a", encoding="utf-8") as f:
                    for x in new:
                        f.write(x + "\n")
                    f.flush()
                    os.fsync(f.fileno())
        except OSError:
            pass
    return rows, len(bad)


def record_day(day, books):
    """Append the finished day's trades for every book to days.jsonl (idempotent per day).
    Books with no trades are recorded too (an empty day is a 0 % day, not a missing one) — but only
    on an NSE trading day: an idle weekend or holiday is not a session (C-10). A non-trading day
    that does carry trades (a special session, or sim/test data) is still recorded, because evidence
    is never discarded. A book still holding a position is tagged "unclosed". Returns True if written."""
    if not _is_trading(day) and not any(getattr(b, "trades", None) for b in books.values()):
        return False
    rows, nbad = _read_days_rows()
    _RECORD_BAD[0] += nbad
    rows = [r for r in rows if r["day"] != day]
    for name, b in books.items():
        row = {"day": day, "book": name,
               "trades": [{"pnl_pts": t["pnl_pts"], "pnl_rs": t["pnl_rs"], "ret_pct": t.get("ret_pct"),
                           "entry": t.get("entry"), "gap": bool(t.get("gap")),
                           "stale_exit": bool(t.get("stale_exit")),
                           "advisors": {k: bool(v.get("veto")) for k, v in (t.get("advisors") or {}).items()},
                           "regime": t.get("regime"),
                           "phase_in": t.get("phase_in"), "phase_out": t.get("phase_out"),
                           "signal": t.get("signal"),                       # D-115
                           # D-101: what the quote-defect rule reads, kept so the exclusion is auditable
                           "key": t.get("key"), "exit": t.get("exit"), "time_out": t.get("time_out"),
                           "trade_age_in": t.get("trade_age_in"), "trade_age_out": t.get("trade_age_out"),
                           "exit_quote_age": t.get("exit_quote_age"),
                           "quote_defect": defects.quote_defect(t),
                           "reason": t["reason"], "time_in": t["time_in"]} for t in b.trades]}
        if getattr(b, "pos", None):
            row["unclosed"] = True
        if getattr(b, "backfilled", False):
            row["backfilled"] = True
        rows.append(row)
    rows.sort(key=lambda r: (r["day"], r["book"]))
    _atomic_write_lines(DAYS, [json.dumps(r) for r in rows])
    return True


def is_cas_trade(t):
    """D-094: a trade ENTERED after the cash market went into its closing auction (15:15). Only the
    owner's CAS test lets books enter there; those trades are kept on file but never count as
    evidence for SPRT, the challenger test or the advisor screens — the frozen v1 rule stops at 15:15."""
    pi = t.get("phase_in")
    if pi:
        return pi not in ("CTS", "PRE")
    ti = t.get("time_in") or ""
    return ti[:5] >= "%02d:%02d" % config.CAS_START


def cas_lines(days_all):
    """D-094: the owner's Closing Auction Session test — trades entered at/after 15:15, per book.
    Shown for study only; they are excluded from every decision above."""
    rows = []
    for book in sorted(days_all):
        tr = [t for d in sorted(days_all[book]) for t in days_all[book][d] if is_cas_trade(t)]
        if not tr:
            continue
        r = [_r(t) for t in tr]
        ph = defaultdict(int)
        for t in tr:
            ph[t.get("phase_in") or "?"] += 1
        tim = sum(1 for t in tr if str(t.get("reason", "")).startswith("TIME"))
        rows.append(f"| {book} | {len(tr)} | {_mean(r):+.2f} | {sum(x > 0 for x in r) / len(r):.0%} | "
                    f"{min(r):+.1f} / {max(r):+.1f} | {tim} | "
                    f"{', '.join(f'{k} {v}' for k, v in sorted(ph.items()))} |")
    head = ["", "## Closing Auction Session test (D-094) — study only, not evidence", ""]
    if not getattr(config, "CAS_TEST", False) and not rows:
        return []
    if not rows:
        return head + ["No trade has been entered at or after %02d:%02d yet." % config.CAS_START]
    return head + [f"Entries allowed until {config.LAST_ENTRY[0]:02d}:{config.LAST_ENTRY[1]:02d}, flatten "
                   f"{config.FLATTEN_AT[0]:02d}:{config.FLATTEN_AT[1]:02d}. The heavyweights stop printing at 15:15 "
                   "(auction), so synchrony is blind in this window.", "",
                   "| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |",
                   "|---|---|---|---|---|---|---|"] + rows


_QUAR = []           # (day, book, trade, why) kept on file but excluded by the most recent _load_days
_QUAR_DAYS = {}      # day -> "whole session" / window text, from the most recent _load_days
_QUAR_ERR = [None]   # defects.json could not be read


def _load_days(include_cas=False, include_quarantined=False):
    """book -> day -> [evidence trades]. CAS trades (D-094) and quarantined trades (D-101: a quote
    defect, or inside a feed-defect window — the same window for every book, so paired tests stay
    paired) are left out unless asked for. A day whose declared window covers the whole session is
    not a session at all here (not a 0 % day). Every exclusion is listed in _QUAR for the report."""
    out = defaultdict(dict)
    rows, nbad = _read_days_rows()
    _LOAD_BAD[0] = nbad
    q = defects.Quarantine(rows)
    del _QUAR[:]
    _QUAR_DAYS.clear()
    _QUAR_ERR[0] = q.err
    for d in sorted({r["day"] for r in rows}):
        if q.whole_day(d):
            _QUAR_DAYS[d] = "whole session (declared)"
        elif q.windows(d):
            _QUAR_DAYS[d] = ", ".join(f"{defects._hms(a)}-{defects._hms(b)} ({ref}: {why})" for a, b, ref, why in q.windows(d))
    for r in rows:
        d = r["day"]
        whole = q.whole_day(d)
        keep = []
        for t in r["trades"]:
            if not include_cas and is_cas_trade(t):
                continue
            why = "whole session declared defective" if whole else q.reason(d, t)
            if why:
                _QUAR.append((d, r["book"], t, why))
                if not include_quarantined:
                    continue
            keep.append(t)
        if whole and not include_quarantined:
            continue
        out[r["book"]][d] = keep
    return out


def quarantine_lines():
    """D-101: every trade kept on file but not counted, with the reason — so nothing disappears silently."""
    lines = ["", "## Quarantined evidence (D-101) — kept on file, NOT counted anywhere above", ""]
    if _QUAR_ERR[0]:
        lines.append(f"**defects.json could not be read ({_QUAR_ERR[0]}) — declared windows were NOT applied.**")
    if not _QUAR and not _QUAR_DAYS:
        return lines + ["None."] if _QUAR_ERR[0] else []
    for d, w in sorted(_QUAR_DAYS.items()):
        lines.append(f"- {d}: defect window(s) {w} — trades entered inside are excluded for every book.")
    lines += ["", "| day | book | time in-out | contract | entry → exit | recorded ret % | why |", "|---|---|---|---|---|---|---|"]
    for d, b, t, why in sorted(_QUAR, key=lambda x: (x[0], x[1], x[2].get("time_in") or "")):
        lines.append(f"| {d} | {b} | {t.get('time_in')}-{t.get('time_out') or '?'} | {t.get('key') or '?'} | "
                     f"{t.get('entry')} → {t.get('exit')} | {_r(t):+.2f} | {why} |")
    per = defaultdict(int)
    for _, b, _, _ in _QUAR:
        per[b] += 1
    lines += ["", "Per book: " + ", ".join(f"{b} {n}" for b, n in sorted(per.items()))]
    return lines


class _BookRecord:
    """The two attributes record_day reads, built from a saved paper/<day>.json book."""
    backfilled = True

    def __init__(self, d):
        self.trades = list(d.get("trades") or [])
        self.pos = d.get("pos")


def backfill_unrecorded(before_day, registered=REGISTERED):
    """C-03: a live session stopped before 15:30 (Ctrl+C, sleep, crash) never reached record_day.
    Record every paper/YYYY-MM-DD.json with registered < day < before_day that is an NSE trading
    day and is missing from days.jsonl, read straight from the JSON. Returns (days recorded, problems)."""
    done, problems = [], []
    try:
        names = sorted(os.listdir(config.PAPER_DIR))
    except OSError:
        return done, problems
    have = None
    for fn in names:
        m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.json", fn)
        if not m:
            continue
        d = m.group(1)
        if not (registered < d < before_day) or not _is_trading(d):
            continue
        if have is None:
            have = {r["day"] for r in _read_days_rows()[0]}
        if d in have:
            continue
        try:
            with open(os.path.join(config.PAPER_DIR, fn), encoding="utf-8") as f:
                raw = json.load(f)
            books = {n: _BookRecord(v) for n, v in raw.items() if isinstance(v, dict)}
            if books and record_day(d, books):
                done.append(d)
                have.add(d)
        except Exception as e:               # one bad file must not stop learning
            problems.append(f"{fn}: {type(e).__name__}: {e}")
    return done, problems


def _mean(x):
    return sum(x) / len(x) if x else 0.0


def _sd(x):
    n = len(x)
    if n < 2:
        return 0.0
    m = _mean(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1))


def _t(x):
    n = len(x)
    if n < 2:
        return 0.0
    m, sd = _mean(x), _sd(x)
    return m / (sd / math.sqrt(n)) if sd > 0 else (math.inf if m > 0 else 0.0)


def _lodo_ok(day_vals):
    if len(day_vals) < 3:
        return False
    tot = sum(day_vals)
    n = len(day_vals)
    return all((tot - v) / (n - 1) > 0 for v in day_vals)


def paired_test(days, a, b, since, alpha):
    """Daily compounded return of book a minus book b on the days both traded since `since`.
    Returns (n_days, mean_diff, t, t_needed, lodo_ok, passed)."""
    da = {d: _day_ret(tr) for d, tr in days.get(a, {}).items() if d > since}
    db = {d: _day_ret(tr) for d, tr in days.get(b, {}).items() if d > since}
    common = sorted(set(da) & set(db))
    diff = [da[d] - db[d] for d in common]
    n = len(diff)
    t = _t(diff)
    need = t_crit(alpha, n - 1) if n >= 2 else math.inf
    lodo = _lodo_ok(diff)
    passed = n >= config.CHALLENGER_MIN_DAYS and _mean(diff) > 0 and t >= need and lodo
    return n, _mean(diff), t, need, lodo, passed


def challengers(s):
    return [v for v in config.VARIANTS
            if v not in config.CONTROLS and v != s["champion"] and v not in s["retired"]]


# ── the loop ─────────────────────────────────────────────────────────────────
def _write_report(today, lines):
    try:                                     # D-136: the edge-feature table (evidence only)
        from .edge import report_lines
        lines = list(lines) + report_lines(config.PAPER_DIR)
    except Exception:
        pass
    _atomic_write_lines(REPORT, lines)
    try:                                     # a dated copy, so a later evening never hides this one
        _atomic_write_lines(os.path.join(config.LEARN_DIR, f"report_{today}.md"), lines)
    except Exception:
        pass


def learn(today: str = None):
    today = today or date.today().isoformat()
    s = load_state()
    days = _load_days()
    if not _is_trading(today) and not any(today in bd for bd in days.values()):
        # C-10: a weekend or holiday is not a session. Nothing is decided, no streak moves, nothing is saved.
        _write_report(today, [f"# ApexOptions — learning report ({today})", "",
                              f"{today} is not an NSE trading day: nothing learned, no streak moved, state unchanged "
                              f"(champion `{s['champion']}`, last learned {s.get('learned_day') or 'never'})."])
        return s
    filled, fill_problems = backfill_unrecorded(today, s.get("registered", REGISTERED))   # C-03
    for d in filled:
        s["log"].append({"event": "backfilled", "day": d, "on": today})
    if filled:
        days = _load_days()
    first_look = s.get("looked_day") != today      # streaks move once per evening, however often learn() runs
    s["looked_day"] = today
    lines = [f"# ApexOptions — learning report ({today})", "",
             "Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).", ""]
    champ = s["champion"]

    # 1. scoreboard for the champion
    ctr = [_r(t) for d, tr in sorted(days.get(champ, {}).items()) if d > s["champion_since"] for t in tr]
    n, tot = len(ctr), sum(ctr)
    go, kill = sprt_lines(n)
    if n < config.SPRT_MIN_TRADES:              # O-8: no verdict either way before the minimum
        status = "COLLECTING"
    elif n and tot >= go:
        status = "GO — edge > 0 is now likely (size still uncertain)"
    elif n and (tot <= kill or n >= config.SPRT_MAX_TRADES):
        status = "KILL — champion retired"
    else:
        status = "COLLECTING"
    s["scoreboard"] = {"n": n, "sum": round(tot, 2), "go_line": round(go, 1), "kill_line": round(kill, 1),
                       "sd_obs": round(_sd(ctr), 2) if n >= 2 else None}
    sd_note = (f" Observed sd {_sd(ctr):.1f} % vs assumed {config.SPRT_SIGMA_PCT:.0f} %"
               + (" — re-register SPRT_SIGMA_PCT if this persists." if n >= 30 and abs(_sd(ctr) - config.SPRT_SIGMA_PCT) > 0.5 * config.SPRT_SIGMA_PCT else ".")
               if n >= 2 else "")
    lines += [f"## Scoreboard — champion `{champ}`",
              f"{n} trades since {s['champion_since']}, Σ {tot:+.1f} %. GO line {go:.1f}, KILL line {kill:.1f} → **{status}**.{sd_note}", ""]
    try:                                       # report-only: nothing below changes a decision
        lines += observer_lines(s, days, ctr)
    except Exception as e:
        lines += [f"(observers failed: {e})", ""]

    # 2. champion vs challengers — Bonferroni over the challengers, plus a persistence streak
    chal = challengers(s)
    alpha = config.CHALLENGER_ALPHA / max(1, len(chal))
    best, best_t = None, 0.0
    lines += [f"## Challengers (daily return vs champion since it took over; one-sided α {alpha:.4f} each, "
              f"{len(chal)} challengers; {config.PROMOTE_STREAK} passing evenings in a row to promote)", "",
              "| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |",
              "|---|---|---|---|---|---|---|"]
    for v in chal:
        nd, m, t, need, lodo, ok = paired_test(days, v, champ, s["champion_since"], alpha)
        if first_look:
            s["streak"][v] = s["streak"].get(v, 0) + 1 if ok else 0
        lines.append(f"| {v} | {nd} | {m:+.2f} | {t:.2f} | {need:.2f} | {'yes' if lodo else 'no'} | {s['streak'].get(v, 0)} |")
        if ok and s["streak"].get(v, 0) >= config.PROMOTE_STREAK and t > best_t:
            best, best_t = v, t
    lines.append("")
    change = None
    if status.startswith("KILL"):
        if champ not in s["retired"]:
            s["retired"].append(champ)
        alive = []
        for v in config.VARIANTS:
            if v in s["retired"] or v in config.CONTROLS:
                continue
            x = [_r(t) for tr in days.get(v, {}).values() for t in tr]
            g, k = sprt_lines(len(x))
            if not x or sum(x) > k:
                alive.append((sum(x), v))
        if alive:
            change = max(alive)[1]
            lines.append(f"Champion `{champ}` hit KILL → replaced by `{change}` (best surviving record). Scoreboard restarts.")
        else:
            lines.append("**Every registered variant is in KILL territory: the v1 hypothesis has no edge. "
                         "Paper trading continues for data, but a new hypothesis is needed (owner decision).**")
            s["status"] = "NO-EDGE"
    elif best:
        change = best
        lines.append(f"Challenger `{best}` beat the champion (t {best_t:.2f}, LODO ok, "
                     f"{s['streak'].get(best, 0)} evenings in a row) → promoted.")
    if change:
        s["log"].append({"day": today, "event": "champion", "from": champ, "to": change})
        s["champion"], s["champion_since"] = change, today
        g0, k0 = sprt_lines(0)
        s["scoreboard"] = {"n": 0, "sum": 0.0, "go_line": round(g0, 1), "kill_line": round(k0, 1), "sd_obs": None}
        s["streak"] = {}
        s["gate_streak"] = {}

    # 3. controls — does the champion beat the nulls? (reported, never promoted)
    ca = config.CHALLENGER_ALPHA / max(1, len(config.CONTROLS))
    lines += ["", "## Controls (current champion minus control, daily return % since registration; the champion must beat these)", "",
              "| control | days | champion ahead by %/day | t | t needed | verdict |", "|---|---|---|---|---|---|"]
    for c in config.CONTROLS:
        # every variant trades every session, so the current champion's variant is compared with the
        # controls over all registered days, not only since it took over
        nd, m, t, need, lodo, ok = paired_test(days, s["champion"], c, s["registered"], ca)   # registered day itself excluded
        verdict = ("champion beats it" if ok else
                   "too few days" if nd < config.CHALLENGER_MIN_DAYS else
                   "control is ahead" if m < 0 else "not distinguishable yet")
        lines.append(f"| {c} | {nd} | {m:+.2f} | {t:.2f} | {need:.2f} | {verdict} |")

    # 4. advisors — screen on RAW, then a gated book decides (D-067)
    raw = [(d, t) for d, tr in sorted(days.get("RAW", {}).items()) if d > s["registered"] for t in tr]
    lines += ["", "## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)", "",
              "| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |",
              "|---|---|---|---|---|---|---|---|---|"]
    rs = sorted([_r(t) for _, t in raw])
    q75 = rs[int(0.75 * (len(rs) - 1))] if rs else 0
    screens = {}
    for a in ADVISORS:
        vet = [(d, t) for d, t in raw if t["advisors"].get(a)]
        kept = [(d, t) for d, t in raw if not t["advisors"].get(a)]
        m_all = _mean([_r(t) for _, t in raw])
        m_kept = _mean([_r(t) for _, t in kept])
        gain = m_kept - m_all
        top = [t for _, t in raw if _r(t) >= q75 and _r(t) > 0]
        top_v = sum(1 for t in top if t["advisors"].get(a)) / len(top) if top else 0.0
        byday = defaultdict(float)
        for d, t in vet:
            byday[d] -= _r(t)              # removing a vetoed trade adds -ret
        lodo = _lodo_ok(list(byday.values())) if byday else False
        screens[a] = dict(n=len(raw), nv=len(vet), m_all=m_all, m_kept=m_kept, gain=gain, top_v=top_v, lodo=lodo,
                          ok=len(raw) >= 30 and len(vet) >= 8 and gain >= config.ADV_MIN_GAIN_PCT and top_v <= 0.25 and lodo)
    cands = s["candidates"]
    ga = config.CHALLENGER_ALPHA / max(1, len(cands))
    gate_rows = []
    for a in ADVISORS:
        sc = screens[a]
        was_gate = a in s["gates"]
        st = "GATE" if was_gate else "advisory"
        if was_gate and sc["n"] >= 30 and sc["gain"] < 0:
            s["gates"].remove(a)
            s["log"].append({"day": today, "event": "gate-", "advisor": a})
            st = "DEMOTED"
        elif a in cands:
            book = GATED_PREFIX + a
            since = max(cands[a], s["champion_since"])
            nd, m, t, need, lodo, ok = paired_test(days, book, s["champion"], since, ga)
            if first_look:
                s["gate_streak"][a] = s["gate_streak"].get(a, 0) + 1 if ok else 0
            gate_rows.append(f"| {book} | {nd} | {m:+.2f} | {t:.2f} | {need:.2f} | {'yes' if lodo else 'no'} | {s['gate_streak'].get(a, 0)} |")
            if ok and s["gate_streak"].get(a, 0) >= config.PROMOTE_STREAK:
                s["gates"].append(a)
                cands.pop(a)
                s["gate_streak"].pop(a, None)
                s["log"].append({"day": today, "event": "gate+", "advisor": a})
                st = "PROMOTED"
            elif sc["n"] >= 30 and sc["gain"] < 0:
                cands.pop(a)
                s["gate_streak"].pop(a, None)
                s["log"].append({"day": today, "event": "candidate-", "advisor": a})
                st = "candidate dropped"
            else:
                st = "CANDIDATE (gated book running)"
        elif not was_gate and sc["ok"]:
            cands[a] = today
            s["log"].append({"day": today, "event": "candidate+", "advisor": a})
            st = "→ CANDIDATE (gated book from next session)"
        lines.append(f"| {a} | {sc['n']} | {sc['nv']} | {sc['m_all']:+.2f} | {sc['m_kept']:+.2f} | {sc['gain']:+.2f} | "
                     f"{sc['top_v']:.0%} | {'yes' if sc['lodo'] else 'no'} | {st} |")
    if gate_rows:
        lines += ["", "### Gated books vs champion (Bonferroni over the candidates)", "",
                  "| book | days | mean diff/day % | t | t needed | LODO | passing evenings |", "|---|---|---|---|---|---|---|"] + gate_rows
    # 5. evidence sections (D-070/D-071): trades by regime, and every candidate taken or not
    from . import diagnostics
    try:
        lines += diagnostics.regime_trade_lines(days, [s["champion"], "RAW"], _r)
        lines += diagnostics.candidate_lines(s["registered"], quarantine=defects.Quarantine(_read_days_rows()[0]))
    except Exception as e:                    # the report must never stop the learning decision
        lines += ["", f"(diagnostics failed: {e})"]
    try:
        lines += cas_lines(_load_days(include_cas=True))
    except Exception as e:
        lines += ["", f"(CAS section failed: {e})"]
    try:
        _load_days()                            # refresh _QUAR for the evidence view used above
        lines += quarantine_lines()
    except Exception as e:
        lines += ["", f"(quarantine section failed: {e})"]
    s["status"] = s.get("status") if s.get("status") == "NO-EDGE" else status.split(" ")[0]
    s["learned_day"] = today
    lines += ["", f"Champion for the next session: **`{s['champion']}`** · gates: {', '.join(s['gates']) or 'none'} · "
                  f"candidates: {', '.join(cands) or 'none'}"]
    lines += _integrity_lines(days, filled, fill_problems, s.get("registered", REGISTERED))
    save_state(s)
    _write_report(today, lines)
    _RECORD_BAD[0] = 0
    del _NOTES[:]
    return s


def _integrity_lines(days, filled, problems, registered):
    out = []
    nbad = _RECORD_BAD[0] + _LOAD_BAD[0]
    if nbad:
        out.append(f"- **{nbad} corrupt row(s) skipped** in days.jsonl (kept in `days.jsonl.corrupt`).")
    out += [f"- {x}" for x in _NOTES]
    if filled:
        out.append(f"- Back-filled unrecorded session(s) from paper/: {', '.join(filled)} "
                   "(stopped before the day-roll; rows of books still holding a position are tagged `unclosed`).")
    out += [f"- Back-fill skipped {x}" for x in problems]
    odd = sorted({d for bd in days.values() for d in bd if d > registered and not _is_trading(d)})
    if odd:
        out.append(f"- {len(odd)} recorded non-trading day(s) carry trades (special session, or sim/test data?): "
                   f"{', '.join(odd[:5])}{' …' if len(odd) > 5 else ''}")
    return ["", "## Record integrity", ""] + out if out else []


# ── report-only observers (C-02, C-24, C-25, C-26) ───────────────────────────
# They are printed for the owner to judge. None of them moves state, a streak, a gate or the champion;
# making any of them a rule is owner decision O-8 / O-9.
EVALUE_LAMBDAS = (0.05, 0.1, 0.2, 0.4, 0.8)   # fixed bet sizes of the mixture; frozen with REGISTERED
EVALUE_CLIP = (-100.0, 300.0)                 # per-trade ret% clipped to this range before betting


def e_value_mean_le0(rets_pct):
    """Anytime-valid betting e-value against H0 "mean per-trade return <= 0".

    Each trade's ret% is clipped to [-100, +300] and scaled to x = r/100, so x >= -1. For a fixed bet
    size lam in [0, 1), the wealth W_n = prod(1 + lam * x_i) stays >= 0, and under H0 (each trade's
    conditional mean given the past <= 0) it is a non-negative supermartingale. The e-value is the
    equal-weight mixture of the five wealth paths for EVALUE_LAMBDAS — a mixture of supermartingales
    is one too — so by Ville's inequality P(the e-value ever reaches 1/alpha) <= alpha under H0, however
    many evenings it is looked at, and with no assumed sigma. Clipping the top only lowers x, which keeps
    the test valid (conservative). 20 = 1/0.05 is the 5 % line. A stream of 0 % trades stays exactly 1."""
    logw = [0.0] * len(EVALUE_LAMBDAS)
    for r in rets_pct:
        x = min(EVALUE_CLIP[1], max(EVALUE_CLIP[0], float(r))) / 100.0
        for j, lam in enumerate(EVALUE_LAMBDAS):
            logw[j] += math.log1p(lam * x)
    top = max(logw)
    lse = top + math.log(sum(math.exp(v - top) for v in logw) / len(logw))
    try:
        return math.exp(lse)
    except OverflowError:
        return math.inf


def _would_be(total, n, go, kill):
    if n < config.SPRT_MIN_TRADES:
        return "COLLECTING"
    if n and total >= go:
        return "GO"
    if n and (total <= kill or n >= config.SPRT_MAX_TRADES):
        return "KILL"
    return "COLLECTING"


def observer_lines(s, days, ctr):
    champ, since = s["champion"], s["champion_since"]
    reg = s.get("registered", REGISTERED)
    n, tot = len(ctr), sum(ctr)
    d = config.SPRT_DELTA_PCT
    a, b = config.SPRT_ALPHA, config.SPRT_BETA
    out = ["### Observers (report only — they change no decision; owner items O-8 / O-9)", ""]

    # (iv) how many champions and looks this GO line has had (C-02, C-25)
    k = 1 + sum(1 for e in s.get("log", []) if e.get("event") == "champion")
    looks_c = sum(1 for x in days.get(champ, {}) if x > since)
    looks_all = len({x for bd in days.values() for x in bd if x > reg})
    out.append(f"- Champion #{k} since registration ({reg}); evening looks: {looks_c} for this champion, "
               f"{looks_all} since registration. Every new champion and every look is another chance at a false GO.")

    # (i) the same Wald lines with the observed sd (C-02)
    sd = _sd(ctr)
    if n >= 10 and sd > 0:
        kk = sd * sd / d
        g_o, k_o = kk * math.log((1 - b) / a) + n * d / 2, kk * math.log(b / (1 - a)) + n * d / 2
        out.append(f"- Wald lines with the observed sd {sd:.1f} % (assumed {config.SPRT_SIGMA_PCT:.0f} %): "
                   f"GO {g_o:.1f}, KILL {k_o:.1f} → would be **{_would_be(tot, n, g_o, k_o)}**.")
    else:
        out.append(f"- Wald lines with the observed sd: need ≥ 10 trades (have {n}).")

    # (ii) the SPRT on per-trade log growth, the quantity all-in compounding earns (C-24)
    lg = [100.0 * math.log(max(1e-4, 1.0 + r / 100.0)) for r in ctr]
    g_l, k_l = sprt_lines(n)
    out.append(f"- SPRT on per-trade 100·ln(1+r): Σ {sum(lg):+.1f} (mean {_mean(lg):+.2f}/trade) vs GO {g_l:.1f} / "
               f"KILL {k_l:.1f} → would be **{_would_be(sum(lg), n, g_l, k_l)}**.")

    # (iii) a sigma-free, anytime-valid e-value (C-02, C-25)
    e = e_value_mean_le0(ctr)
    out.append(f"- Betting e-value against \"mean ≤ 0\" (returns clipped to [−100, +300] %, λ mixture "
               f"{', '.join(str(x) for x in EVALUE_LAMBDAS)}): **{e:.2f}** — ≥ 20 would reject at 5 % under any number of looks.")

    # (v) the design's own day-level bar for GO (§9.2 / §6.1, C-26), as a checklist
    dv = [sum(_r(t) for t in tr) for x, tr in sorted(days.get(champ, {}).items()) if x > since]
    dsum = sum(dv)
    n_exp = sum(1 for x in days.get(champ, {}) if x > since and _is_weekly_expiry(x))
    ca = config.CHALLENGER_ALPHA / max(1, len(config.CONTROLS))
    beats = [paired_test(days, champ, c, reg, ca)[5] for c in config.CONTROLS]
    checks = [
        (len(dv) >= 15, f"≥ 15 sessions ({len(dv)})"),
        (n_exp >= 2, f"≥ 2 expiry days ({n_exp})"),
        (_lodo_ok(dv), "every leave-one-day-out mean > 0"),
        (bool(dv) and dsum - max(dv) > 0, "total > 0 with the best day dropped"),
        (bool(dv) and dsum > 0 and max(dv) <= 0.4 * dsum, "no single day > 40 % of the total"),
        (bool(dv) and sum(1 for v in dv if v > 0) >= 0.5 * len(dv), "≥ 50 % of days net-green"),
        (bool(beats) and all(beats), f"beats every control ({sum(beats)}/{len(beats)})"),
    ]
    out += ["", "Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). "
                "Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:", ""]
    out += [f"- [{'x' if ok else ' '}] {txt}" for ok, txt in checks]
    return out + [""]
