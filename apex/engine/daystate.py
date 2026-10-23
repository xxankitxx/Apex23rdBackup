"""D-141 (owner, 22 Oct 16:02: "the system is not making judgements about what the market regime is and not playing
according to the day ... why is it not booking when the data suggests a resistance it cannot break?"; council 9, 20
members). The DAY STATE: what a manual trader keeps on a notepad all day.

* session high / low of Nifty SPOT (trusted prints from 09:15) and when each was made;
* RANGE MODE (council 9 T04): once the day's leg (session low -> high, in the order they printed) is at least
  RANGE_MIN_LEG_PTS and spot has given back RANGE_GIVEBACK of it, the trend is over and the day is a range until spot prints
  a new session extreme. A trend book does not enter in range mode. 22 Oct: on at 11:46 (the 22784 top was 11:14), never
  on during 19 Oct's or 21 Oct's legs;
* LEVELS (council 9 T02 / T08 / T10): prior-day high / low / close (saved at each day's end in learning/day_levels.json),
  the opening range (09:15 to 09:15 + OR_WINDOW_S), the session extremes and the round hundreds — the numbers spot stalls at.

Fed once a second from engine_main with the same trusted spot as the 12-min and 45-min windows (D-132 guard applied).
"""
import json
import os

from .. import config


class DayState:
    def __init__(self, day, prior=None):
        self.day = day
        self.hi = self.lo = None
        self.t_hi = self.t_lo = None
        self.range_on = False
        self.range_since = None
        self.or_hi = self.or_lo = None
        self.t0 = None
        self.last = None
        self.close = None                    # last trusted print before the 15:15 index freeze (D-132)
        self.prior = prior or {}             # {"day", "hi", "lo", "close"} of the previous recorded session

    # ── per second ───────────────────────────────────────────────────────────
    def add(self, t, sp, hm=None):
        sp = float(sp)
        if self.t0 is None:
            self.t0 = t
        self.last = sp
        if hm is None or hm < config.mins((15, 15)):
            self.close = sp
        if t - self.t0 <= config.OR_WINDOW_S:
            self.or_hi = sp if self.or_hi is None else max(self.or_hi, sp)
            self.or_lo = sp if self.or_lo is None else min(self.or_lo, sp)
        new_ext = False
        if self.hi is None or sp > self.hi:
            new_ext = self.hi is not None
            self.hi, self.t_hi = sp, t
        if self.lo is None or sp < self.lo:
            new_ext = new_ext or self.lo is not None
            self.lo, self.t_lo = sp, t
        if new_ext and self.range_on:            # a new session extreme: a trend has (re)started
            self.range_on, self.range_since = False, None
        leg = self.hi - self.lo
        if not self.range_on and leg >= config.RANGE_MIN_LEG_PTS:
            give = (self.hi - sp) / leg if self.t_hi > self.t_lo else (sp - self.lo) / leg
            if give >= config.RANGE_GIVEBACK:
                self.range_on, self.range_since = True, t

    def or_done(self, t):
        return self.t0 is not None and t - self.t0 > config.OR_WINDOW_S

    def levels(self, sp):
        """The levels a manual trader watches, as (price, label), unsorted."""
        out = []
        for k, lab in (("hi", "PDH"), ("lo", "PDL"), ("close", "PDC")):
            v = self.prior.get(k)
            if v:
                out.append((float(v), lab))
        if self.hi is not None:
            out += [(self.hi, "DAY HIGH"), (self.lo, "DAY LOW")]
        if self.or_hi is not None:
            out += [(self.or_hi, "OR HIGH"), (self.or_lo, "OR LOW")]
        if sp:
            c = round(sp / 100.0) * 100.0
            out += [(c + k * 100.0, f"{c + k * 100.0:.0f}") for k in (-2, -1, 0, 1, 2)]
        return out

    def ahead(self, sp, d, min_gap=5.0):
        """Levels ahead of spot in direction d, at least min_gap away, nearest first: [(price, label)]."""
        return sorted([(p, lab) for p, lab in self.levels(sp) if (p - sp) * d >= min_gap], key=lambda x: (x[0] - sp) * d)

    def view(self):
        return {"hi": self.hi, "lo": self.lo, "t_hi": self.t_hi, "t_lo": self.t_lo, "range_on": self.range_on,
                "range_since": self.range_since, "or_hi": self.or_hi, "or_lo": self.or_lo,
                "pdh": self.prior.get("hi"), "pdl": self.prior.get("lo"), "pdc": self.prior.get("close")}

    # ── persistence ──────────────────────────────────────────────────────────
    def dump(self):
        return {k: getattr(self, k) for k in ("day", "hi", "lo", "t_hi", "t_lo", "range_on", "range_since", "or_hi",
                                               "or_lo", "t0", "last", "close", "prior")}

    @classmethod
    def load(cls, st):
        s = cls(st.get("day"), st.get("prior"))
        for k, v in st.items():
            setattr(s, k, v)
        return s


def levels_path():
    return os.path.join(config.LEARN_DIR, "day_levels.json")


def load_prior(day):
    """The most recent recorded session before `day`: {"day", "hi", "lo", "close"} or {}. A replay runs in its own folder,
    so it also reads APEX_PRIOR_LEVELS (a day_levels.json path) when that is set."""
    d = {}
    for path in (levels_path(), os.environ.get("APEX_PRIOR_LEVELS") or ""):
        try:
            if path and os.path.exists(path):
                for k, v in json.load(open(path, encoding="utf-8")).items():
                    d.setdefault(k, v)
        except Exception:
            pass
    prev = sorted(k for k in d if k < day)
    return dict(d[prev[-1]], day=prev[-1]) if prev else {}


def save_day(ds):
    """Record today's high / low / close for tomorrow's levels (never raises)."""
    if ds is None or ds.hi is None or ds.close is None:
        return
    try:
        p = levels_path()
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            d = {}
        d[ds.day] = {"hi": round(ds.hi, 2), "lo": round(ds.lo, 2), "close": round(ds.close, 2)}
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1, sort_keys=True)
        os.replace(tmp, p)
    except Exception:
        pass
