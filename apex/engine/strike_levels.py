"""27 Oct (owner: "are you keeping a track of the supports and resistances of each strike price, which can help in
decision making when such resistances/supports are breached?").

Support and resistance of every option's OWN premium (not Nifty's): per contract key, from fresh prints at 1 Hz:
  day high / day low        the premium's extremes so far today
  OR high / OR low          the premium's range 09:15-09:30
  swing highs / lows        1-minute pivots: a bar whose high (low) beats the two bars on each side
  prior high / low / close  yesterday's values for the same contract (data/learning/strike_levels.json)

A BREAK is the premium going 1 % beyond a level that has stood for at least 5 minutes (the day high/low count only
when they were set 5+ minutes earlier). Each level breaks once. Breaks of near-ATM strikes go to the tape
paper/strikes_<day>.jsonl, and the trade records carry the levels at entry (sr_in) and the breaks of the held
contract during the trade (sr_breaks).

EVIDENCE ONLY: nothing here gates or exits a trade. Measured on the six days 19-27 Oct (recorded premiums, near-ATM):
a premium that broke its day low fell a further -4.5 % over 10 min (6/6 days; a random near-ATM premium: -0.2 %);
breaks of the day high were mixed (+0.6 %, and -16 % on expiry day). Used directly as a stop on the replay's entries,
a support stop LOST against a plain -10 % premium stop (pullback entries dip under a recent low before they work).
It earns a role in a decision only when it holds on new days.
"""
import json
import os

from .. import config

BRK_PCT = 1.0          # a break is 1 % beyond the level
LEVEL_AGE_S = 300      # ... of a level that has stood this long
PIV_N = 2              # a swing pivot beats this many 1-min bars on each side
KEEP_PIVOTS = 6
OR_END_HM = 9 * 60 + 30


def path():
    return os.path.join(config.LEARN_DIR, "strike_levels.json")


def load_prior(day):
    """Yesterday's (hi, lo, close) per contract key, or {} — only a file from an EARLIER day counts."""
    try:
        d = json.load(open(path(), encoding="utf-8"))
        if d.get("day") and d["day"] < day:
            return d.get("levels") or {}
    except Exception:
        pass
    return {}


class StrikeLevels:
    def __init__(self, day, prior=None):
        self.day = day
        self.prior = prior or {}
        self.s = {}          # key -> state

    # ── updates ──────────────────────────────────────────────────────────
    def add(self, t, key, px, hm):
        """One fresh print (t epoch s, px premium, hm minutes since midnight IST). Returns a list of break events."""
        if not px or px <= 0:
            return []
        st = self.s.get(key)
        if st is None:
            st = self.s[key] = {"hi": px, "hi_t": t, "lo": px, "lo_t": t, "or_hi": None, "or_lo": None,
                                "bar": None, "bars": [], "piv_hi": [], "piv_lo": [], "done": set(), "last": px}
        ev = self._breaks(st, key, t, px)
        if px > st["hi"]:
            st["hi"], st["hi_t"] = px, t
        if px < st["lo"]:
            st["lo"], st["lo_t"] = px, t
        if hm < OR_END_HM:
            st["or_hi"] = px if st["or_hi"] is None else max(st["or_hi"], px)
            st["or_lo"] = px if st["or_lo"] is None else min(st["or_lo"], px)
        m = int(t // 60)
        b = st["bar"]
        if b is None or b[0] != m:
            if b is not None:
                st["bars"].append(b)
                del st["bars"][:-(2 * PIV_N + 1)]
                self._pivots(st, t)
            st["bar"] = [m, px, px]
        else:
            b[1], b[2] = max(b[1], px), min(b[2], px)
        st["last"] = px
        return ev

    def _pivots(self, st, t):
        bs = st["bars"]
        if len(bs) < 2 * PIV_N + 1:
            return
        c = bs[PIV_N]
        side = bs[:PIV_N] + bs[PIV_N + 1:]
        if all(c[1] > x[1] for x in side):
            st["piv_hi"] = (st["piv_hi"] + [(round(c[1], 2), c[0] * 60 + 60)])[-KEEP_PIVOTS:]
        if all(c[2] < x[2] for x in side):
            st["piv_lo"] = (st["piv_lo"] + [(round(c[2], 2), c[0] * 60 + 60)])[-KEEP_PIVOTS:]

    def _levels(self, st, key, t):
        """[(level, label, kind)] with kind 'R' (resistance) or 'S' (support); only levels old enough to break."""
        out = []
        if t - st["hi_t"] >= LEVEL_AGE_S:
            out.append((st["hi"], "day high", "R"))
        if t - st["lo_t"] >= LEVEL_AGE_S:
            out.append((st["lo"], "day low", "S"))
        for lv, lt in st["piv_hi"]:
            if t - lt >= LEVEL_AGE_S:
                out.append((lv, "swing high", "R"))
        for lv, lt in st["piv_lo"]:
            if t - lt >= LEVEL_AGE_S:
                out.append((lv, "swing low", "S"))
        if st["or_hi"] is not None:
            out += [(st["or_hi"], "OR high", "R"), (st["or_lo"], "OR low", "S")]
        pr = self.prior.get(key) or {}
        for k, lab in (("hi", "prior high"), ("lo", "prior low"), ("close", "prior close")):
            if pr.get(k):
                out.append((float(pr[k]), lab, "?"))           # resistance above the premium, support below
        return out

    def _breaks(self, st, key, t, px):
        ev = []
        last = st["last"]
        for lv, lab, kind in self._levels(st, key, t):
            tag = (lab, round(lv, 2))
            if tag in st["done"]:
                continue
            up = last <= lv * (1 + BRK_PCT / 100) < px and kind in ("R", "?")
            dn = last >= lv * (1 - BRK_PCT / 100) > px and kind in ("S", "?")
            if up or dn:
                st["done"].add(tag)
                ev.append({"t": t, "key": key, "dir": "UP" if up else "DOWN", "level": round(lv, 2), "label": lab,
                           "px": round(px, 2), "kind": "resistance" if up else "support"})
        return ev

    # ── views ────────────────────────────────────────────────────────────
    def view(self, key, px=None, t=None):
        """Resistances above and supports below the premium, nearest first, with the room in %."""
        st = self.s.get(key)
        if st is None:
            return {}
        px = px or st["last"]
        t = t if t is not None else (st["bar"][0] * 60 + 60 if st["bar"] else 0)
        lv = [(st["hi"], "day high"), (st["lo"], "day low")]
        lv += [(a, "swing high") for a, _ in st["piv_hi"]] + [(a, "swing low") for a, _ in st["piv_lo"]]
        if st["or_hi"] is not None:
            lv += [(st["or_hi"], "OR high"), (st["or_lo"], "OR low")]
        pr = self.prior.get(key) or {}
        lv += [(float(pr[k]), lab) for k, lab in (("hi", "prior high"), ("lo", "prior low"), ("close", "prior close"))
               if pr.get(k)]
        res = sorted({(round(a, 2), b) for a, b in lv if a > px * 1.001})
        sup = sorted({(round(a, 2), b) for a, b in lv if a < px * 0.999}, reverse=True)
        return {"px": round(px, 2), "res": [list(x) for x in res[:4]], "sup": [list(x) for x in sup[:4]],
                "room_up_pct": round(100 * (res[0][0] / px - 1), 2) if res else None,
                "room_dn_pct": round(100 * (1 - sup[0][0] / px), 2) if sup else None}

    def dump_day(self):
        """End of day: hi / lo / close per contract, tomorrow's prior levels."""
        return {"day": self.day, "levels": {k: {"hi": round(s["hi"], 2), "lo": round(s["lo"], 2),
                                                "close": round(s["last"], 2)} for k, s in self.s.items()}}


def save_day(sl):
    if sl is None or not sl.s:
        return
    p = path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(sl.dump_day(), f)
    os.replace(tmp, p)
