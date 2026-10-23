"""
Data blackout guard (D-063) — external review finding F1.

The failure it prevents: the feed freezes (socket drop, silent stall), every price in the
ring buffer stops changing, then the feed resumes and the futures AND every heavyweight jump
to their current prices in the same tick. The 15-s impulse sees the whole outage move as a
15-s move, every stock "moved together" (synchrony), and the episode is born at the jump (so
it looks fresh): the Triangle closes on an artefact. The jump would also inflate the 20-min
sigma scales.

Rule: the engine is in BLACKOUT whenever the feed is not delivering (feed state not LIVE /
SIM / REPLAY, or NO instrument has delivered a quote for STALE_S — the feed is silent), or the
Nifty-futures quote alone is older than FUT_QUIET_S. D-097 (live, 19 Oct 2026): Breeze sends the
Nifty future only ~1 packet/s and only when it changes; 3-s futures silences happened 79 times in
the morning while every other instrument kept flowing (88-174 packets/s), so the old "futures quote
older than 3 s" rule produced 47 false blackouts (~25 % of the window) and no real one. It stays in blackout until
RESUME_S of continuous fresh futures quotes — longer than the 15-s impulse window, so once the
blackout lifts no 15-s change can span the gap. During blackout:
  * no entries in any book;
  * the domino does not update its scales (sigma, volume baselines);
  * an episode or straddle spike that begins inside it is tainted and can never be traded;
  * exits wait for fresh quotes (only the clock-driven TIME exits still run).
The engine starts in blackout, so the first RESUME_S seconds after any (re)start are covered.
"""
from .. import config

LIVE_STATES = {2, 5, 6}        # LIVE, SIM, REPLAY (apex/table.py FEED_STATES)
STALE_S = 3.0                  # NO quote on ANY instrument for this long = the feed is not delivering
FUT_QUIET_S = 10.0             # D-097: the Nifty-future quote alone may be quiet this long (max seen 7.4 s)
RESUME_S = 20.0                # continuous fresh data needed before the blackout lifts
ENGINE_PAUSE_S = 10.0          # a hole this long in the ENGINE's own sampling is a gap (a 3-s hole cannot
                               # fake a 15-s impulse; a 10-s one is most of the window). Live steps are 100 ms.
JUMP_FRAC = 0.01               # D-072: a futures move > 1 % within JUMP_WINDOW_S is a bad print, not a move
JUMP_WINDOW_S = 2.0            #        (Nifty does not move 250 points in two seconds outside a circuit event)
SETTLE_S = 300.0               # after a gap lifts, 5-min windows (straddle watch, premium momentum) still
                               # contain the jump for this long: spikes born in it are tainted, momentum waits


class DataGuard:
    def __init__(self):
        self.on = True
        self.reason = "starting"
        self.since = None          # when the current blackout began
        self.fresh_since = None    # first fresh tick of the current clean run
        self.gaps = []             # this day's lifted blackouts: [(start_s, end_s, reason)]
        self.last_px = None        # last futures price seen, and when (bad-print check)
        self.last_px_t = None

    def update(self, now_s, feed_state, fut_age_s, in_session=True, fut_px=None, step_gap=0.0, feed_age_s=None):
        """step_gap = seconds since the engine's previous step. If the ENGINE paused (OS sleep, a
        long GC, a blocked disk write) the feed may have kept writing, so the futures quote is
        fresh and the price ring buffer holds a hole: the stall move would read as a 15-s impulse.
        A sampling hole is therefore a data gap too."""
        feed_ok = feed_age_s is None or feed_age_s <= STALE_S
        ok = (feed_state in LIVE_STATES and feed_ok and fut_age_s is not None and fut_age_s <= FUT_QUIET_S)
        if step_gap > ENGINE_PAUSE_S:
            ok = False
            self.reason = f"engine paused {step_gap:.0f} s"
            self.fresh_since = None
            if not self.on:
                self.on, self.since = True, now_s
            self.last_px, self.last_px_t = fut_px, now_s      # a jump across the pause is not a bad print
            return self.on
        bad_print = False
        if fut_px is not None and fut_px > 0:
            if (self.last_px and self.last_px_t is not None and now_s - self.last_px_t <= JUMP_WINDOW_S
                    and abs(fut_px / self.last_px - 1.0) > JUMP_FRAC):
                bad_print = True
            self.last_px, self.last_px_t = fut_px, now_s
        if bad_print:
            if not self.on:
                self.on = True
            self.since = self.since or now_s
            self.reason = f"implausible futures jump to {fut_px:.1f}"
            self.fresh_since = None
            return self.on
        if not ok:
            # outside market hours a quiet futures quote is normal, not a gap
            if feed_state in LIVE_STATES and not in_session:
                ok = True
        if not ok:
            if not self.on:
                self.on, self.since = True, now_s
            if self.since is None:
                self.since = now_s
            self.reason = ("feed " + ("not live" if feed_state not in LIVE_STATES
                                      else f"silent: no quote on any instrument for {feed_age_s:.0f} s" if not feed_ok
                                      else f"stale: futures quote {fut_age_s:.0f} s old" if fut_age_s is not None
                                      else "has no futures quote"))
            self.fresh_since = None
            return self.on
        if self.fresh_since is None:
            self.fresh_since = now_s
        if self.on and now_s - self.fresh_since >= RESUME_S:
            if self.since is not None and self.reason != "starting":
                self.gaps.append((self.since, now_s, self.reason))
            self.on, self.since, self.reason = False, None, ""
        return self.on

    def new_day(self):
        self.gaps = []

    def settling(self, now_s):
        """Seconds of settling left after the last lifted gap (0 when clear)."""
        if self.on or not self.gaps:
            return 0.0
        return max(0.0, SETTLE_S - (now_s - self.gaps[-1][1]))

    def exits_ok(self):
        """Owner decision O-4 (18 Oct 2026): stops and trails may fire during the resume phase — fresh
        futures quotes are arriving again — while ENTRIES keep the full RESUME_S rule. Not after a bad
        print: a wrong price can persist, and a stop must never fire on it."""
        return (not self.on) or (self.fresh_since is not None and not self.reason.startswith("implausible"))

    def view(self, now_s):
        return {"on": self.on, "why": self.reason if self.on else "", "settling_s": round(self.settling(now_s), 1),
                "exits_ok": self.exits_ok(),
                "for_s": round(now_s - self.since, 1) if (self.on and self.since) else 0.0,
                "resume_in": (round(max(0.0, RESUME_S - (now_s - self.fresh_since)), 1)
                              if (self.on and self.fresh_since is not None) else None),
                "gaps_today": len(self.gaps),
                "gap_s_today": round(sum(e - s for s, e, _ in self.gaps), 1)}


def in_session(now_dt):
    hmn = config.hm(now_dt)
    return config.mins(config.MARKET_OPEN) <= hmn < config.mins(config.MARKET_CLOSE)
