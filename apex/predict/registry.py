"""11 Nov 2026 (docs/42 finding F): which frozen artefact may forecast a given session.

registry.json lists artefacts with `trained_through` and `effective_from`. pick(day) returns the newest artefact whose
effective_from is on or before `day` AND whose trained_through is before `day`: a model never forecasts a session it
was fitted on. A session before the first artefact gets none (the forecaster is then silent, with the reason).
Nothing is fitted here."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "registry.json")
SESSION_OPEN = "09:15:00"


def load(path=None):
    path = path or PATH
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(json.load(f).get("artefacts") or [])


def pick(day, path=None, rows=None):
    """(artefact path or None, reason). `day` is 'YYYY-MM-DD'."""
    rows = load(path) if rows is None else rows
    if not rows:
        return None, "no artefact registry"
    day = str(day)
    ok = [r for r in rows if str(r["trained_through"]) < day and (r.get("effective_from") is None or str(r["effective_from"]) <= day)]
    if not ok:
        first = min(str(r["trained_through"]) for r in rows)
        return None, f"no artefact fitted before {day} (the first is trained through {first})"
    best = max(ok, key=lambda r: str(r["trained_through"]))
    return os.path.join(os.path.dirname(path or PATH), best["file"]), \
        f"artefact {best['hash']} trained through {best['trained_through']}"


def for_session(day, mode, discovery_path, path=None):
    """11 Nov (docs/46 finding 4): the artefact the ENGINE loads for a session, and why.
    mode "chronological": only an artefact fitted on earlier sessions (validated). None when there is none: the
                          forecaster is then silent for that session; it NEVER falls back to a file that has seen it.
    mode "discovery":     the fixed file `discovery_path`, whatever it was fitted on. For experiments only; the
                          forecaster reports in_sample when the file has seen the session.
    Returns (artefact dict or None, reason)."""
    if mode == "discovery":
        if not discovery_path or not os.path.exists(discovery_path):
            return None, "discovery mode: no artefact file"
        with open(discovery_path, encoding="utf-8") as f:
            return json.load(f), "discovery mode: " + os.path.basename(discovery_path)
    art, why, _ = validated(day, path)
    return art, "chronological: " + why


def validated(day, path=None, rows=None):
    """(artefact dict or None, reason, row). docs/44 section 2: selection is not validation. The artefact picked for
    `day` is loaded only if the file exists, its content hash equals both its own `hash` field and the registry's,
    its embedded training cut-off equals the registry's, and the cut-off is before `day`. Feature schema and target
    are checked by ledger.Forecaster. Anything else is an explicit unavailable state with its reason.
    `published` on a row (a timestamp written when the artefact was really in place before a live session) tells a
    live-published artefact from one whose availability on a past day is only simulated."""
    from . import models as Mo
    rows = load(path) if rows is None else rows
    p, why = pick(day, path, rows)
    if p is None:
        return None, why, None
    row = max((r for r in rows if os.path.join(os.path.dirname(path or PATH), r["file"]) == p), key=lambda r: str(r["trained_through"]))
    if not os.path.exists(p):
        return None, f"artefact file missing: {row['file']}", row
    try:
        with open(p, encoding="utf-8") as f:
            art = json.load(f)
    except (OSError, ValueError) as e:
        return None, f"artefact unreadable: {row['file']} ({type(e).__name__})", row
    h = Mo.model_hash(art)
    if h != art.get("hash") or h != row.get("hash"):
        return None, f"artefact {row['file']} does not match its hash (content {h}, file says {art.get('hash')}, registry {row.get('hash')})", row
    if str(art.get("training_cutoff")) != str(row["trained_through"]):
        return None, f"artefact cut-off {art.get('training_cutoff')} is not the registry's {row['trained_through']}", row
    if str(art["training_cutoff"]) >= str(day):
        return None, f"artefact was fitted on {art['training_cutoff']}, not before {day}", row
    # docs/46 finding 5: "published" is a recorded wall-clock time 'YYYY-MM-DD HH:MM:SS' (IST). It proves prior
    # availability only when it is before that session's open; anything else is simulated availability.
    pub = str(row.get("published") or "")
    live = len(pub) == 19 and pub[4] == "-" and pub[10] == " " and pub < f"{day} {SESSION_OPEN}"
    note = (f" · recorded as published {pub} IST, before the open of {day}" if live else
            f" · publication time {pub} is not before the open of {day}: availability simulated" if pub else " · availability simulated")
    return art, why + note, row
