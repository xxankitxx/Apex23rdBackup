"""
ApexOptions — configuration and the NSE calendar.

Everything tunable lives here. The four v1 trigger parameters are in TRIGGER;
the self-learning loop may switch the champion between pre-registered
VARIANTS, but never invents new numbers (see apex/engine/learning.py).
"""
import os
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# APEX_DATA lets sim / replay runs keep their paper books and learning state
# apart from the live paper account (run_apex.py sets data/sim, data/replay).
DATA_DIR = os.environ.get("APEX_DATA") or os.path.join(ROOT, "data")
TICKS_DIR = os.path.join(ROOT, "data", "ticks")    # recorder output (always the main data dir)
PAPER_DIR = os.path.join(DATA_DIR, "paper")        # paper books, trades csv
LEARN_DIR = os.path.join(DATA_DIR, "learning")     # self-learning state + reports
LOG_DIR = os.path.join(DATA_DIR, "logs")
SECRETS_DIR = os.path.join(ROOT, "secrets")        # gitignored; never committed
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
INSTRUMENTS_JSON = os.path.join(DATA_DIR, "instruments.json")
TOKEN_CACHE_JSON = os.path.join(ROOT, "data", "token_cache.json")

for _d in (DATA_DIR, TICKS_DIR, PAPER_DIR, LEARN_DIR, LOG_DIR, SECRETS_DIR):
    os.makedirs(_d, exist_ok=True)

# ── mode ─────────────────────────────────────────────────────────────────────
PAPER_ONLY = True          # v1 never places a broker order. Owner decision 17 Oct 2026.
AUDIO = True               # speaker alerts from the engine (armed / entry / win / loss), as in MYTHOS

# ── web ──────────────────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 8780                # MYTHOS uses 8765 — both can run side by side

# ── shared memory names ──────────────────────────────────────────────────────
SHM_TABLE = "apex_table_v1"
SHM_STATE = "apex_state_v1"
MAX_ROWS = 512
STATE_BYTES = 2 * 1024 * 1024

# ── instrument ───────────────────────────────────────────────────────────────
NIFTY = "NIFTY"
STRIKE_STEP = 50
LOT_SIZE = 65              # verified NSE contract master Oct–Dec 2026; re-check on lot revisions
FREEZE_QTY = 3510          # NSE/FAOP/76693 from 5 Oct 2026 (paper: informational)
WEEKLY_BAND = 12           # subscribe weekly ATM ± 12 strikes (both rights)
NEXTWEEK_BAND = 4          # next-week ATM ± 4 strikes
HERO_BAND = 2              # ATM ± 2 = the ten hero contracts (depth)
RECENTER_STRIKES = 4       # extend the bands when spot drifts this far (keeps next-week ±4 usable)
# D-109 (owner, 19 Oct 13:14 — anti-churn, every book; trigger numbers and the 12-pt stop unchanged):
FUT_PRICE_IS_MID = True    # D-110: the engine's Nifty-futures price IS the bid/ask mid (impulse, sigma, episode, guard, exits, trace)
FUT_EXIT_ON_MID = True     # D-109: exits on the mid (redundant under D-110; kept for the replay of pre-D-110 days)
FUT_MID_MAX_SPREAD = 30.0  #   (a wider or one-sided futures quote falls back to the last print)
THESIS_VOID_HOLD_S = 5.0   # "heavyweights flipped against us" must hold this long before it exits
REENTRY_COOLDOWN_S = 60.0  # no new entry in a book for this long after its last exit
MIN_IMPULSE_PTS = 15.0     # the 15-s futures move must also be at least this many points (z alone can be 10 pts in a dead market)
# D-112: standing gates for every non-control book (the learning loop's gates add to these)
BASE_GATES = ("regime",)   # no entry while the regime is WARMING / UNCERTAIN / RANGE / COMPRESSION / EXHAUSTION or the other way
REGIME_BLOCK = ("WARMING", "UNCERTAIN", "RANGE", "COMPRESSION", "EXHAUSTION")   # D-112: states that block entries
# D-113: daily brake per book (control books exempt)
# D-123 (owner, 19 Oct 22:04): the daily brake below was NEVER an owner requirement — D-113 was my proposal in the
# plan, D-117 the council's. All of it is OFF by default (0 / None = no rule). The owner sets a number to turn one on.
DAILY_LOSS_STOP_PCT = 0.0  # OFF. e.g. 15.0 = no new entries once the book is down 15 % on the day
LOSS_STREAK_N = 0          # OFF. e.g. 3 = after 3 consecutive losses ...
LOSS_STREAK_PAUSE_S = 0    # ... pause this long (0 = the rest of the day). Does nothing while LOSS_STREAK_N is 0
MAX_ENTRIES_PER_DAY = 0    # OFF. e.g. 6 = at most 6 entries per book per day
EXPIRY_ENTRY_END = None    # OFF. e.g. (11, 30) = on expiry day no new entries after 11:30
WARM_SAVE_S = 30          # D-120: engine warm state saved this often (live) ...
WARM_MAX_AGE_S = 1800     # ... and restored on a same-day restart if younger than this
KILL_FILE = os.path.join(DATA_DIR, "KILL")   # D-117: create this file to stop new entries in every book
# D-114: the trend variant
TREND_MIN_PTS = 20.0       # the 30-min futures move must be at least this, in the impulse's direction
HERO_FROZEN_S = 120        # D-103: a hero contract with no trade for this long is shown FROZEN
FEED_SYNC_DISPATCH = True  # D-106: websocket messages handled in the read loop (no thread per message)
REPLAY_LOCKSTEP = True     # D-105: replays step the engine once per REPLAY_STEP_S of recorded time
REPLAY_STEP_S = 0.1        #        (live samples every 100 ms); results no longer depend on --speed or CPU load
# T02 (council 5): `run_apex.py replay --fast` — feed and engine in ONE process (apex/replay_fast.py), the same
# lock-step boundaries, no shared-memory hand-shake; the engine skips work that no decision reads: the ≤1/s
# restart-safety book saves (C-11; a replay is never restarted) and fsync. Books, trades, decisions identical.
REPLAY_FAST = os.environ.get("APEX_FAST", "") == "1"
RECENTER_HOLD_S = 30       # D-104: ... and has stayed there this long, in market hours only

# ── session clock (IST) ──────────────────────────────────────────────────────
MARKET_OPEN = (9, 15)
# D-094: NSE equity derivatives trade until 15:40 since 3 Aug 2026 (the Closing Auction Session
# launch). The cash market ends continuous trading at 15:15 for CAS stocks (every heavyweight).
MARKET_CLOSE = (15, 40)
SUPPRESS_UNTIL = (9, 25)   # overnight repricing: synchrony meaningless (G1)
# [TESTING — owner, 19 Oct 2026] entries allowed up to 15:29 so the books trade INTO the cash
# market's Closing Auction Session and the data shows how the trigger behaves there. The v1
# production value was (15, 15) and FLATTEN_AT (15, 25). Revert both lines to end the test.
LAST_ENTRY = (15, 29)
FLATTEN_AT = (15, 35)
CAS_TEST = True            # tags the test in the reports; flip to False when LAST_ENTRY is reverted
# Cash-market Closing Auction Session phases (NSE, CAS stocks — the whole heavyweight basket).
CAS_START = (15, 15)       # 15:15-15:20 reference price (VWAP 15:00-15:15) and transition
CAS_MATCH = (15, 30)       # order entry closes (randomly in the last 2 min); 15:30-15:35 matching
CAS_END = (15, 35)         # 15:35-15:50 transition to the post-close session
ZERO_DTE_FLATTEN = (15, 0) # 0DTE flat by 15:00 unless delta >= 0.9 (I-7)
ZERO_DTE_NO_ENTRY = (14, 45)
ZERO_DTE_NEXTWEEK_FROM = (13, 0)
# Owner, 19 Oct 13:06 (D-108): on expiry day trade the EXPIRING weekly, never next week's / the monthly.
# Entries stop at ZERO_DTE_NO_ENTRY (14:45) and positions are flat by ZERO_DTE_FLATTEN (15:00).
# (D-021 had "after 13:00 prefer next week"; set True to bring that back.)
ZERO_DTE_USE_NEXTWEEK = False

# ── paper capital ────────────────────────────────────────────────────────────
START_CAPITAL = 100_000.0  # fresh every trading day [OWNER]
# Owner 17 Oct: paper trading — slippage and charges ignored. Fills at LTP, gross P&L.
# Bid/ask at fill are still recorded so a net view can be computed later.
FILL_AT = "ltp"
# D-126 (council 5 T01, confirmed by the lead on the 19 Oct tape): a fill is priced on the FIRST print of the option that
# arrives AFTER the trigger, never on the print that was already on the screen when spot moved (that print predates the
# move: it made the paper buy too cheap and the paper sell too dear — 19 Oct read ₹4.69 L this way and ₹1.79 L honestly).
# Still LTP (owner), only the timing changes. An entry waits at most ENTRY_FILL_MAX_S for a print, then lapses.
FILL_NEXT_PRINT = True
ENTRY_FILL_MAX_S = 3.0

# ── v1 trigger (D-033): four tunables ────────────────────────────────────────
TRIGGER = {
    "m_star": 2.0,     # futures 15-s impulse z-score threshold
    "s_star": 0.50,    # weighted basket synchrony threshold
    "L_star": 3.0,     # not-late: futures move since onset <= L* x sigma15
    "d_star": 12.0,    # stop distance in Nifty-futures points (also the trail width; 1R)
}
IV_RISE_CAP = 1.5      # vol points since onset (frozen, not tuned — G2/G7)
ONSET_Z = 1.0          # |z| at which an episode starts
EPISODE_END_Z = 0.5    # episode ends after |z| < this for EPISODE_END_SEC
EPISODE_END_SEC = 30.0
RECRUIT_Z = 1.0        # a stock counts toward synchrony at |z_i| >= this
ACTIVITY_MIN = 1.2     # ...and volume >= this x its own baseline (once warm)
SIGMA_HALF_LIFE_S = 20 * 60
SIGMA15_SEED = 4.0     # Nifty pts; used until the 20-min scale warms up
SIGMA15_FLOOR = 5.0    # D-111: sigma15 never below this (was 0.5): in the lunch lull it shrank to 3-5 pts and a
                       # 10-pt wiggle read z = 2 (17 of 19 afternoon entries on 19 Oct were +1..+10 pt "impulses")
WARMUP_S = 10 * 60

# Pre-registered variants for the self-learning loop (registered 17 Oct 2026).
# Every variant trades its own virtual paper book in parallel on the same data;
# the champion's book is the one shown as "the" paper account.
VARIANTS = {
    f"m{m}_s{s}": {"m_star": m, "s_star": s, "L_star": 3.0, "d_star": 12.0}
    for m in (1.5, 2.0, 2.5) for s in (0.4, 0.5, 0.6)
}
# Owner's purest domino idea (17 Oct): enter when the heavyweight BASKET implies a move the
# futures have not yet made — gap = basket-implied pts − futures pts ≥ gap_star, with synchrony.
VARIANTS["gap3_s0.4"] = {"m_star": 1.0, "s_star": 0.4, "L_star": 3.0, "d_star": 12.0, "gap_star": 3.0}
VARIANTS["gap5_s0.4"] = {"m_star": 1.0, "s_star": 0.4, "L_star": 3.0, "d_star": 12.0, "gap_star": 5.0}
# Fifth exit as a variant: leave when the sellers on the HELD contract refill (orders and
# quantity) while futures stall — "force on the contract you hold".
VARIANTS["m2.0_s0.5_bookexit"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0, "exit_book": True}
# Owner's straddle observation (17 Oct, evening): when the fixed-strike ATM straddle spikes above
# its theta decay, buy the leg that carries the spike (its delta is rising). One trade per spike,
# entered within SPIKE_ENTRY_MAX_AGE_S of the spike's start; the usual four exits apply.
VARIANTS["straddle_spike"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0, "spike": True}
# CONTROL books (D-065, external review F3/F6): pre-registered NULLS. They trade every session
# with the usual four exits but can NEVER become champion; the report compares the champion
# against each. If the champion cannot beat them, the trigger has not shown an edge.
#   futures_only     : the champion's trigger with the basket removed (s* = 0) -> does the basket add anything?
#   random_entry     : random times in the entry window, side from the futures 1-min move -> do entries beat chance?
#   premium_momentum : buy a straddle leg on its RAW 5-min rise (no theta path) -> does the theta model add anything?
VARIANTS["futures_only"] = {"m_star": 2.0, "s_star": 0.0, "L_star": 3.0, "d_star": 12.0, "s_exit": 0.5}  # s_exit: same THESIS-VOID exit as the champion
VARIANTS["random_entry"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0, "random": True}
VARIANTS["premium_momentum"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0, "momentum": True}
CONTROLS = ("futures_only", "random_entry", "premium_momentum")
# Owner decision O-1 (18 Oct 2026): the trigger keeps its nearest-strike ATM IV; this variant is the
# champion's trigger with the frozen 1.5-pt IV cap applied to IV interpolated at the forward between the
# two bracketing strikes (no jump when the nearest strike changes, no artificial rise on down-moves).
VARIANTS["m2.0_s0.5_ivinterp"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0, "iv_interp": True}
# D-100 (council of 19 Oct, 6 members independently): the per-stock volume test (each heavyweight's
# 15-s volume >= ACTIVITY_MIN x its own mean) is what keeps synchrony low on real data — at the 86
# impulse decisions of 19 Oct mean S was 0.40 without it and 0.16 with it (15-s volume is heavy-
# tailed: the mean sits 1.4-2.3x the median). The champion keeps it; this pre-registered book runs
# the champion's four frozen numbers with S measured without the volume test, so the data decides.
VARIANTS["m2.0_s0.5_novol"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0, "novol": True}
# D-114 (plan after 19 Oct): the champion's four numbers plus "only with the 30-min futures direction".
# 19 Oct afternoon: 9 of 9 counter-trend call buys lost; the 2 winners were puts with the drift.
VARIANTS["m2.0_s0.5_trend"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0, "trend": True}
# D-116 (council 4, 19 Oct evening): Nifty SPOT breakout of its previous 12-min range, 12-pt SPOT trail,
# one trade per swing; no regime gate, no cool-down, no 3-loss pause (the -15 % daily stop still applies).
# m28 proposed it; m30 red-teamed it: profitable on the full day in every +-20 % cell (N 10-14 min, D 10-14),
# still profitable from a 09:35 start and with the best 3 trades removed, beats 96-99 % of random-entry and
# random-direction runs; its afternoon edge is NOT proven (4/9 neighbours lose the PM). m_star..d_star are
# placeholders the shared code reads; this book's entry and exit use only spot_dc / spot_trail.
SPOT_DC_S = 720            # D-116 look-back of the spot range (12 min)
# D-127 (owner, 20 Oct 19:22: "the trailing has to be improved once a considerable profit is observed"; council 5 T01,
# 213 rules / 645 runs): once the option is LOCK_PCT over entry the lock arms; from then on the trade exits if the premium
# falls LOCK_TRAIL_PCT from its best. The 12-pt spot trail keeps running. 19 Oct (honest fills): +18-21 % on the day, every
# +-20 % neighbour (15-22 / 8-12) at least as good, no winner cut short, 3 PM trades changed, all improved. Tighter than
# ~8 % collapses into noise. OWNER NUMBERS to confirm. 0 = off. `spot_dc12_t12_nolock` runs beside as the old rule.
LOCK_PCT = 18.0
LOCK_TRAIL_PCT = 10.0
# D-131 (owner, 21 Oct 15:41: "it would take trades when the price has already run ... it would come out so soon in a cheap
# manner"; council 6, 10 members, 21 Oct tape + 19 Oct tape): the first-touch entry bought the first second of a break. On 21 Oct
# (6 DTE, a chop-down drift) 48 % of those entries never moved 8 pts and every entry paid about 2.3 premium points for buying
# right after the burst; the 12-pt exit itself did its job (give-back 3-6 %). RETEST entry (council-6 M06): a break is only
# ARMED at the level it broke; the book buys when spot has run RETEST_EXT_PTS beyond the level AND then comes back to within
# RETEST_TOL_PTS of it (the level held), cancels if the level is lost by RETEST_FAIL_PTS or after RETEST_WINDOW_S. The exit,
# the lock and the swing rule are untouched. Simulated on both tapes (LTP, lock on): 19 Oct +88k -> +173k (15 trades),
# 21 Oct -29k -> +22k (19 trades); beats random thinning of the old entries on both days; BUT: two days, 34 trades, the gain is
# morning-only and it skips ~half the trades incl. most clean runners. The old rule keeps running beside it as
# `spot_dc12_t12_first`. OWNER NUMBERS (5 / 2 / 3 / 300) to confirm. 0 = off (first touch, as before).
RETEST_EXT_PTS = 5.0
RETEST_TOL_PTS = 2.0
RETEST_FAIL_PTS = 3.0
RETEST_WINDOW_S = 300
# D-132 (council 6 M10): the vendor index feed freezes ~15:15 and prints garbage from 15:20 on every day seen (19 and 21 Oct:
# +501 pts, basis -486 against a normal -13..+39). Receipt time kept looking fresh, so the D-124 staleness nets never fired.
SPOT_BASIS_MAX = 80.0       # spot is INVALID when |future - spot - its 30-min median basis| exceeds this
SPOT_BASIS_REF = 20.0       # basis used until 60 valid seconds are held
SPOT_FLAT_S = 20.0          # ... or when the spot value has not changed for this long while the future moved SPOT_FLAT_FUT_PTS
SPOT_FLAT_FUT_PTS = 6.0
_SPOT = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0, "lock_pct": LOCK_PCT, "lock_trail_pct": LOCK_TRAIL_PCT,
         "spot_dc": SPOT_DC_S, "spot_trail": 12.0, "swing": True, "cooldown_s": 0, "no_streak_pause": True,
         "no_trade_cap": True, "retest_ext": RETEST_EXT_PTS, "retest_tol": RETEST_TOL_PTS, "retest_fail": RETEST_FAIL_PTS,
         "retest_window_s": RETEST_WINDOW_S}
VARIANTS["spot_dc12_t12"] = dict(_SPOT, expiry_window_exempt=True)    # R2 + D-131 retest entry; its _1130 twin carries the cut
VARIANTS["spot_dc12_t12_first"] = dict(_SPOT, expiry_window_exempt=True, retest_ext=0.0, retest_tol=0.0, retest_fail=0.0,
                                       retest_window_s=0)             # D-131 twin: the old first-touch entry
VARIANTS["spot_dc12_t12_1130"] = dict(_SPOT, spot_expiry_end=(11, 30))   # m28 'R3': expiry day entries end 11:30
VARIANTS["spot_dc12_t12_nolock"] = dict(_SPOT, expiry_window_exempt=True, lock_pct=0.0, lock_trail_pct=0.0)   # D-127 twin: no lock
# D-134 (owner, 21 Oct 18:23: "way too many trades and not holding them ... the same mistake again and again ... it enters
# when the rally is already over"; council 7, 8 members, ideas from public code: smart-money-concepts structure/OTE
# retracement, Supertrend, chandelier/ATR exits, choppiness gates, option-chain lead): the PULLBACK book (member C06).
# An IMPULSE is a 45-min spot window whose high-low range is >= PB_MIN_RANGE; its direction is whichever extreme came last.
# Buy ONLY when spot has pulled back into 50-78 % of the impulse (and never went deeper than 80 %), once per impulse.
# Stop = the impulse origin; target = the impulse extreme + 1.0 x its size; the D-127 lock stays; entries end 14:45,
# flat 15:00. All-in lots, LTP, no brake, no cap: the trade count is small because impulses are few.
# Council simulator (both tapes, LTP / ask-bid): 19 Oct 5 trades +124k / +131k, 21 Oct 4 trades +59k / +56k; every
# number within +-20 % positive on both days; cliff only below a 30-min window. Honest: the entry is not better timed;
# the profit is the structural stop that holds through 30-75-pt bounces + one shot per impulse; 9 trades is anecdote.
PB_WINDOW_S = 2700
_PB = dict(_SPOT, expiry_window_exempt=True, swing=False, retest_ext=0.0, retest_tol=0.0, retest_fail=0.0, retest_window_s=0,
           entry_mode="pullback", pb_min_range=60.0, pb_zone_lo=0.50, pb_zone_hi=0.78, pb_zone_slack=0.02, pb_ext=1.0,
           pb_min_age_s=30, pb_entry_end=(14, 45), pb_flatten=(15, 0))
VARIANTS["spot_pb45"] = dict(_PB)
# D-137 (external reviews, 21 Oct: "dual mode by days-to-expiry"): shadow. Expiry day (0 DTE) trades the D-131 retest
# breakout with its 12-pt trail (19 Oct engine replay +131k vs the pullback's +79k); every other day trades the pullback.
# Chosen with ONE day of each kind (council 7 C08 warning). D-140: CHAMPION since 21 Oct (owner: "implement the best
# solution"). Engine replay: 19 Oct 17 trades +₹1,31,193; 21 Oct 4 trades +₹55,426 (pullback alone: +78,647 / +55,426).
VARIANTS["spot_dual"] = dict(_PB, dte0_retest=True, swing=True, retest_ext=RETEST_EXT_PTS, retest_tol=RETEST_TOL_PTS,
                             retest_fail=RETEST_FAIL_PTS, retest_window_s=RETEST_WINDOW_S)
# D-141 (owner, 22 Oct 16:02, after the champion lost -52,084 live on its first unseen day; council 9, 20 members, every
# rule judged leave-one-day-out on 19 / 21 / 22 Oct): the DAY STATE (apex/engine/daystate.py) — session extremes, RANGE
# MODE, opening range, prior-day levels.
RANGE_MIN_LEG_PTS = 100.0   # T04: range mode needs a day leg of at least this many spot points ...
RANGE_GIVEBACK = 0.618      # ... and spot having given back this fraction of it; off at the next new session extreme
OR_WINDOW_S = 2700          # T08: the opening range is 09:15 to 10:00
# Champion (D-141): spot_dual + range mode. The pullback half stops ENTERING while the day is in range mode (exits
# unchanged); the expiry-day retest half is exempt. Sim, all three days, LTP / ask-in-bid-out: 19 Oct +134.4k / +121.2k,
# 21 Oct +59.3k / +55.5k (the gate never fires on either trend day), 22 Oct +2.5k / +3.4k (was -29.2k / -40.9k; live
# -52.1k). The gate's own two numbers give the same result in 26 of 30 cells. Honest: on 22 Oct it makes the day FLAT,
# not profitable, and it cannot save an entry made before the trend's end is known (22 Oct 11:33 CE).
VARIANTS["spot_dual_rg"] = dict(VARIANTS["spot_dual"], range_gate=True)
# D-142: CHAMPION since 22 Oct. Engine replay (honest fills, all-in), the only book of the family positive on all three
# recorded days: 19 Oct +1,36,594 (18 trades), 21 Oct +36,312 (5), 22 Oct +1,199 (4) — live 22 Oct the old champion lost
# -52,084 (replay -53,046). Costs a trend day some profit (21 Oct: +36k vs +55k without booking). spot_dual_rg (range mode
# only: +1,31,193 / +55,426 / -14,878) and spot_dual (+1,31,193 / +55,426 / -53,046) keep running as shadows.
# Other shadows from council 9 (each positive on 3 of 3 held-out days at LTP in its team's test; NOT champions):
# T02/T10 — book at a level the trade cannot break: levels ahead are fixed at entry (prior-day H/L/C, day extremes, opening
# range, round 100s); when the best spot came within lvl_near of the next level without breaking it by more than lvl_brk and
# spot then gives back lvl_rej, BOOK. 22 Oct's live 7 trades: +19.6k instead of -52.1k; costs trend days (21 Oct -21k).
VARIANTS["spot_dual_lvl"] = dict(VARIANTS["spot_dual_rg"], lvl_book=True, lvl_near=5.0, lvl_rej=10.0, lvl_brk=5.0)
# T06 — the ChatGPT "premium-outcome lab": the 12-min first touch with a fixed +10 % / -10 % premium exit (no spot trail,
# no lock): 19 / 21 / 22 Oct +26k / +20k / +39k LTP, +29k / +18k / +24k ask-bid.
VARIANTS["spot_ft_prem10"] = dict(VARIANTS["spot_dc12_t12_first"], prem_tgt=10.0, prem_stop=10.0, lock_pct=0.0,
                                  lock_trail_pct=0.0)
# T08 — opening-range breakout (Crabel / OpenAlgo / Zarattini ORB, CPR-pivot booking; ideas only): range 09:15-10:00, first
# break -> buy; stop when spot crosses back through the opposite edge; book at the first classic level >= orb_gap beyond
# entry; lock on; one trade per direction; entries to 14:45, flat 15:00. +18.7k / +17.3k / +9.9k, one trade a day.
VARIANTS["spot_orb45"] = dict(_PB, entry_mode="orb", orb_gap=15.0)
# D-118 (council 4) shadow books beside the champion — evidence, not candidates yet:
VARIANTS["m2.0_s0.5_d20"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 20.0}          # m01/m25/m30: wider stop
VARIANTS["m2.0_s0.5_tvfast"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0,       # m02: thesis-void on S
                                "s_exit": 0.30, "tv_novol": True, "tv_hold_s": 1.0}               #   without the volume test
# D-121 (council 4, m14 'P1 vol switch'): shadow book. A 15-s move of >= imp_pts on the futures mid; if the
# futures moved >= range_follow pts high-to-low in the last 15 min, FOLLOW it, otherwise FADE it (buy the
# other side). Exit: bracket on the futures mid, +tp_pts / -sl_pts, or max_hold_s. 60-s cool-down.
# Harness on 19 Oct: FULL 55 trades ₹2.14L, AM ₹1.54L, PM ₹1.40L; profitable at thr 10 in 27/27 grid cells
# but LOSES at thr 8 and at 1-pt slippage -> FRAGILE. Runs as evidence only; no gates but the daily brake.
VARIANTS["fade_switch"] = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0,
                           "fade_switch": True, "imp_pts": 10.0, "range_follow": 60.0,
                           "tp_pts": 12.0, "sl_pts": 12.0, "max_hold_s": 180, "cooldown_s": 60,
                           "no_streak_pause": True, "no_trade_cap": True, "expiry_window_exempt": True}
RANDOM_ENTRIES_PER_DAY = 6.0     # Poisson mean; ~ the expected champion rate (re-check after 10 sessions)
CHAMPION_DEFAULT = "spot_dual_lvl"   # D-142 (owner, 22 Oct): range mode + booking at levels the trade cannot break
# D-124 (owner, 20 Oct 16:16: "Apply spot_dc12_t12 thoroughly on my code"): the champion is the owner's choice.
# learning.load_state applies it ONCE to an existing state (the champion lives in data/learning/state.json,
# which the learning loop may later change on evidence); trades from the day after this date count for its
# scoreboard. Bump the date to force the owner's champion again.
CHAMPION_OWNER = ("spot_dual_lvl", "2026-10-22")   # D-142; before: spot_dual (D-140), spot_pb45 (D-134), spot_dc12_t12 (D-124)
SPOT_STALE_S = 5.0         # D-124: the spot books neither enter nor extend their range on a Nifty quote older than this
SPOT_FROZEN_EXIT_S = 60.0  # D-124: in a position, if the index is older than this the stop is taken on the futures mid instead

# ── learning (D-064 / D-066 / D-067) ─────────────────────────────────────────
# Unit: RETURN ON PREMIUM per trade, %. Under all-in sizing a trade's rupee result is
# ret% x capital, and a day's result is the product of (1 + ret) - so % is what the account earns.
SPRT_DELTA_PCT = 2.5       # H1: mean trade return >= +2.5 %
SPRT_SIGMA_PCT = 30.0      # owner decision O-8 (18 Oct 2026; was 10): assumed sd of trade return (0DTE trades swing far more than Friday ones);
                           # the report prints the observed sd so this can be re-registered if wrong
SPRT_ALPHA, SPRT_BETA = 0.05, 0.20
SPRT_MAX_TRADES = 200      # undecided after this many = KILL
SPRT_MIN_TRADES = 30       # owner decision O-8: no GO and no KILL before this many trades
CHALLENGER_ALPHA = 0.05    # family-wise, one-sided; split across the challengers (Bonferroni)
CHALLENGER_MIN_DAYS = 10
PROMOTE_STREAK = 2         # a challenger / gated book must pass on this many consecutive evenings
ADV_MIN_GAIN_PCT = 1.0     # advisor screen: removing its vetoes must add >= 1 % per trade
# D-101 (evidence hygiene after D-095): a trade whose option quote, at entry or at exit, carries an
# exchange stamp (ltt) older than this was priced on a quote the feed never refreshed. It is kept on
# file and shown in the report, but it is NOT evidence (SPRT, challengers, controls, advisor screens,
# candidate diagnostics). Pre-registered from the 19 Oct 2026 tape: in-band NIFTY weekly contracts
# (22900-23250) had a true exchange-stamp age of p50 1 s, p99 13 s, max 17 s over 09:20-10:50, while
# every frozen CE trade carried 237,000-241,000 s (Friday's close). 600 s is a 35x margin on the max.
QUOTE_DEFECT_AGE_S = 600.0

# ── data blackout (D-063) ────────────────────────────────────────────────────
EXIT_FUT_STALE_S = 10      # D-097: a quiet Nifty future (Breeze ~1 packet/s, silences to 7.4 s) is not a dead feed; was 3
IV_LEG_MAX_AGE_S = 30      # D-102: an option quote older than this is left out of the forward and IV
EXIT_QUOTE_STALE_S = 5.0   # a triggered exit waits for an option quote fresher than this ...
EXIT_DEFER_MAX_S = 10.0    # ... for at most this long, then exits at the last price (tagged stale_exit)

# ── straddle watch (apex/engine/straddle_watch.py) ───────────────────────────
SPIKE_MIN_PTS = 4.0        # excess over theta in 5 min, premium points — the floor
SPIKE_MIN_FRAC = 0.06      # ...or 6 % of the straddle 5 min ago, whichever is larger
SPIKE_SIGMA = 2.5          # ...or 2.5 x the running scale of |excess| in quiet time (20-min half-life)
SPIKE_SIGMA_SEED = 1.5     # premium points, until the scale warms up
SPIKE_COOLDOWN_S = 90.0    # after a spike ends, the next one needs this much quiet first
SPIKE_ENTRY_MAX_AGE_S = 150.0   # the straddle_spike book only enters this soon after a spike starts
SPIKE_MIN_DDELTA = 0.03    # ...and only if the leg's |delta| rose at least this much over 5 min

# Owner-maintained event calendar: days when the index moves on news, not on the heavyweights.
# Logged as a would-veto advisor ("event"); becomes a rule only through the learning loop.
# Dates verified against the RBI press release of 23 Mar 2026 (MPC schedule 2026-27): the
# decision is announced on the last day of each three-day meeting.
EVENT_DAYS = {
    "2026-12-04": "RBI policy decision",
    "2027-02-05": "RBI policy decision",
}

# ── instrument choice (G4 delta bands, v1 rule: nearest-the-money in band) ──
DELTA_BANDS = {           # by days-to-expiry bucket
    "ge3": (0.52, 0.70),
    "1to2": (0.60, 0.80),
    "zero_am": (0.65, 0.85),
    "nextweek": (0.52, 0.65),
}
MIN_PREMIUM = 20.0
MAX_PREMIUM = 600.0

# ── REST budget (ICICI: 100/min and 5,000/day across all endpoints) ─────────
CHAIN_POLL_S = 90.0
VIX_POLL_S = 60.0
REST_DAY_BUDGET = 5000
REST_DAY_DATA_CAP = 3000

# ── NSE holiday calendar (weekday closures) — drives expiry shifts ───────────
NSE_HOLIDAYS = {
    "2026-01-15", "2026-01-26", "2026-03-03", "2026-03-26", "2026-03-31",
    "2026-04-03", "2026-04-14", "2026-05-01", "2026-05-28", "2026-06-26",
    "2026-09-14", "2026-10-02", "2026-10-20", "2026-11-10", "2026-11-24",
    "2026-12-25",
}
NSE_HOLIDAYS_EXTRA = set()  # add ad-hoc closures here as "YYYY-MM-DD"

_MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def is_trading_day(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    iso = d.isoformat()
    return iso not in NSE_HOLIDAYS and iso not in NSE_HOLIDAYS_EXTRA


def _roll_back(d: date) -> date:
    for _ in range(10):
        if is_trading_day(d):
            return d
        d -= timedelta(days=1)
    return d


def session_phase(now: datetime) -> str:
    """Which market phase a clock time falls in, as seen by the HEAVYWEIGHT basket:
    PRE (before 9:15) · CTS (continuous) · CAS-ENTRY (15:15-15:30: stocks in the closing auction,
    no continuous prints, only indicative prices) · CAS-MATCH (15:30-15:35: the auction uncrosses,
    one closing print per stock) · POST (15:35-15:40: cash is closed, F&O still trades) · CLOSED."""
    t = hm(now)
    if t < mins(MARKET_OPEN):
        return "PRE"
    if t < mins(CAS_START):
        return "CTS"
    if t < mins(CAS_MATCH):
        return "CAS-ENTRY"
    if t < mins(CAS_END):
        return "CAS-MATCH"
    if t < mins(MARKET_CLOSE):
        return "POST"
    return "CLOSED"


def _after_close(now: datetime) -> bool:
    return hm(now) >= mins(MARKET_CLOSE)          # D-094: expiring contracts trade to 15:40


def weekly_expiries(now: datetime, n: int = 2) -> list:
    """Next n live weekly Nifty expiries (Tuesday, holiday-shifted to the previous
    trading day; today's expiry rolls off at MARKET_CLOSE, 15:40)."""
    today = now.date()
    t = today + timedelta(days=(1 - today.weekday()) % 7)
    out = []
    for _ in range(20):
        e = _roll_back(t)
        if e > today or (e == today and not _after_close(now)):
            if not out or out[-1] != e:
                out.append(e)
        if len(out) >= n:
            break
        t += timedelta(days=7)
    return out


def _last_tuesday(y: int, m: int) -> date:
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    d = nxt - timedelta(days=1)
    while d.weekday() != 1:
        d -= timedelta(days=1)
    return d


def monthly_expiry(now: datetime) -> date:
    """Near-month futures expiry: last Tuesday of the month, holiday-shifted."""
    today = now.date()
    y, m = today.year, today.month
    for _ in range(3):
        e = _roll_back(_last_tuesday(y, m))
        if e > today or (e == today and not _after_close(now)):
            return e
        y, m = (y + (m == 12), m % 12 + 1)
    return e


def monthly_expiry_candidates(now: datetime) -> list:
    """Stock futures: last Tuesday (current NSE rule) with last Thursday as a
    fallback probe — the token lookup decides which one exists."""
    e = monthly_expiry(now)
    y, m = e.year, e.month
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    d = nxt - timedelta(days=1)
    while d.weekday() != 3:
        d -= timedelta(days=1)
    thu = _roll_back(d)
    return [e] if thu == e else [e, thu]


def ws_expiry(d: date) -> str:
    """Breeze websocket/token expiry format, locale-independent: 19-Oct-2026."""
    return f"{d.day:02d}-{_MONTHS[d.month]}-{d.year}"


def rest_expiry(d: date) -> str:
    return f"{d.isoformat()}T06:00:00.000Z"


def now_ist() -> datetime:
    return datetime.now(IST)


def hm(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def mins(t) -> int:
    return t[0] * 60 + t[1]


def holiday_coverage_gaps(now: datetime) -> list:
    """Years between today and the farthest expiry the feed uses (next-week weekly,
    near-month futures) that have NO entry in NSE_HOLIDAYS (C-60). An uncovered year
    means expiry dates there are computed as if no holiday existed."""
    today = now.date()
    ends = [today]
    try:
        ends += list(weekly_expiries(now, 2))
    except Exception:
        pass
    try:
        ends.append(monthly_expiry(now))
    except Exception:
        pass
    have = {h[:4] for h in NSE_HOLIDAYS}
    return [y for y in range(today.year, max(ends).year + 1) if str(y) not in have]


# ── self-check (D-073): a mis-typed number fails preflight, not the session ─────
VARIANT_KEYS = frozenset(("m_star", "s_star", "L_star", "d_star", "s_exit", "iv_interp",
                          "gap_star", "exit_book", "spike", "random", "momentum", "novol", "trend",
                          "spot_dc", "spot_trail", "swing", "cooldown_s", "no_streak_pause", "spot_expiry_end",
                          "no_trade_cap", "expiry_window_exempt", "tv_novol", "tv_hold_s",
                          "fade_switch", "imp_pts", "range_follow", "tp_pts", "sl_pts", "max_hold_s",
                          "lock_pct", "lock_trail_pct", "retest_ext", "retest_tol", "retest_fail", "retest_window_s",
                          "entry_mode", "pb_min_range", "pb_zone_lo", "pb_zone_hi", "pb_zone_slack", "pb_ext",
                          "pb_min_age_s", "pb_entry_end", "pb_flatten", "dte0_retest",
                          "range_gate", "lvl_book", "lvl_near", "lvl_rej", "lvl_brk", "prem_tgt", "prem_stop", "orb_gap"))
VARIANT_MODES = ("gap_star", "exit_book", "spike", "random", "momentum", "spot_dc", "fade_switch")   # at most one per variant


def validate() -> list:
    """Returns a list of problems; empty = the configuration is coherent."""
    bad = []
    need = ("m_star", "s_star", "L_star", "d_star")
    for name, p in VARIANTS.items():
        unknown = sorted(set(p) - VARIANT_KEYS)
        if unknown:          # a typo ('exit_bok') would silently clone another variant (C-45)
            bad.append(f"variant {name} has unknown key(s) {unknown}")
        modes = [k for k in VARIANT_MODES if p.get(k) not in (None, False)]
        if len(modes) > 1:
            bad.append(f"variant {name} combines {modes}; at most one of {list(VARIANT_MODES)}")
        miss = [k for k in need if k not in p]
        if miss:
            bad.append(f"variant {name} lacks {miss}")
            continue
        if not (p["m_star"] > 0 and 0 <= p["s_star"] <= 1 and p["L_star"] > 0 and p["d_star"] > 0):
            bad.append(f"variant {name} has an out-of-range parameter: {p}")
    if CHAMPION_DEFAULT not in VARIANTS or CHAMPION_DEFAULT in CONTROLS:
        bad.append("CHAMPION_DEFAULT must be a registered, non-control variant")
    if not set(CONTROLS) <= set(VARIANTS):
        bad.append("every CONTROL must be registered in VARIANTS")
    for k, (lo, hi) in DELTA_BANDS.items():
        if not (0 < lo < hi < 1):
            bad.append(f"delta band {k} must satisfy 0 < lo < hi < 1")
    if not (0 < MIN_PREMIUM < MAX_PREMIUM):
        bad.append("premium band must satisfy 0 < MIN < MAX")
    order = [MARKET_OPEN, SUPPRESS_UNTIL, ZERO_DTE_NEXTWEEK_FROM, ZERO_DTE_NO_ENTRY, ZERO_DTE_FLATTEN,
             LAST_ENTRY, FLATTEN_AT, MARKET_CLOSE]
    if [mins(t) for t in order] != sorted(mins(t) for t in order):
        bad.append("session clock out of order (open < suppress < 0DTE times < last entry < flatten < close)")
    if not (mins(MARKET_OPEN) < mins(CAS_START) < mins(CAS_MATCH) < mins(CAS_END) <= mins(MARKET_CLOSE)):
        bad.append("CAS phases out of order (open < CAS start < match < end <= close)")
    if not (0 <= DAILY_LOSS_STOP_PCT < 100 and LOSS_STREAK_N >= 0 and LOSS_STREAK_PAUSE_S >= 0 and TREND_MIN_PTS >= 0):
        bad.append("D-113/D-114 brake and trend parameters out of range")
    if SIGMA15_FLOOR <= 0 or MIN_IMPULSE_PTS < 0:
        bad.append("SIGMA15_FLOOR must be positive")
    if CAS_TEST != (mins(LAST_ENTRY) > mins(CAS_START)):
        bad.append("CAS_TEST must be True exactly when LAST_ENTRY is inside the closing auction")
    if not (SPRT_DELTA_PCT > 0 and SPRT_SIGMA_PCT > 0 and 0 < SPRT_ALPHA < 0.5 and 0 < SPRT_BETA < 0.5):
        bad.append("SPRT parameters out of range")
    if not (SPOT_STALE_S > 0 and SPOT_FROZEN_EXIT_S > SPOT_STALE_S and SPOT_DC_S >= 60 and WARM_SAVE_S > 0 and WARM_MAX_AGE_S > 0):
        bad.append("SPOT_STALE_S / SPOT_DC_S / WARM_SAVE_S / WARM_MAX_AGE_S out of range")
    for name, p in VARIANTS.items():
        if p.get("spot_dc") and p["spot_dc"] != SPOT_DC_S:
            bad.append(f"variant {name}: spot_dc {p['spot_dc']} != SPOT_DC_S {SPOT_DC_S} (the engine keeps one spot range)")
        if p.get("spot_dc") and not (p.get("spot_trail") or 0) > 0:
            bad.append(f"variant {name}: spot_trail must be > 0")
        if (p.get("lock_pct") or 0) > 0 and not (0 < (p.get("lock_trail_pct") or 0) < p["lock_pct"]):
            bad.append(f"variant {name}: lock_trail_pct must be between 0 and lock_pct (else the lock is dead or immediate)")
        if (p.get("retest_ext") or 0) > 0:
            if not (p["retest_ext"] > (p.get("retest_tol") or 0) >= 0 and (p.get("retest_fail") or 0) > 0
                    and (p.get("retest_window_s") or 0) >= 60):
                bad.append(f"variant {name}: retest needs ext > tol >= 0, fail > 0 and window >= 60 s")
        if p.get("entry_mode") not in (None, "pullback", "orb"):
            bad.append(f"variant {name}: unknown entry_mode {p['entry_mode']!r}")
        if p.get("entry_mode") == "pullback":
            if not (0 < p.get("pb_zone_lo", 0) < p.get("pb_zone_hi", 0) < 1 and p.get("pb_min_range", 0) > 0
                    and p.get("pb_ext", 0) > 0 and p.get("pb_zone_slack", -1) >= 0 and p.get("pb_min_age_s", -1) >= 0):
                bad.append(f"variant {name}: pullback needs 0 < zone_lo < zone_hi < 1, min_range > 0, ext > 0")
            if p.get("pb_entry_end") and p.get("pb_flatten") and mins(tuple(p["pb_entry_end"])) >= mins(tuple(p["pb_flatten"])):
                bad.append(f"variant {name}: pb_entry_end must be before pb_flatten")
        if p.get("lvl_book") and not (p.get("lvl_near", 0) >= 0 and p.get("lvl_rej", 0) > 0 and p.get("lvl_brk", -1) >= 0):
            bad.append(f"variant {name}: level booking needs lvl_near >= 0, lvl_rej > 0, lvl_brk >= 0")
        if (p.get("prem_tgt") or p.get("prem_stop")) and not ((p.get("prem_tgt") or 0) > 0 and (p.get("prem_stop") or 0) > 0):
            bad.append(f"variant {name}: premium booking needs prem_tgt > 0 and prem_stop > 0")
        if p.get("entry_mode") == "orb" and not (p.get("orb_gap", 0) > 0):
            bad.append(f"variant {name}: orb needs orb_gap > 0")
    if not (RANGE_MIN_LEG_PTS > 0 and 0 < RANGE_GIVEBACK < 1 and OR_WINDOW_S >= 900):
        bad.append("RANGE_MIN_LEG_PTS / RANGE_GIVEBACK / OR_WINDOW_S out of range")
    if PB_WINDOW_S < 1800:
        bad.append("PB_WINDOW_S below 1800 s: the council measured a cliff under a 30-min window")
    if not (SPOT_BASIS_MAX > 0 and 0 < SPOT_FLAT_S < SPOT_FROZEN_EXIT_S and SPOT_FLAT_FUT_PTS > 0):
        bad.append("SPOT_BASIS_MAX / SPOT_FLAT_S / SPOT_FLAT_FUT_PTS out of range")
    if not (ENTRY_FILL_MAX_S > 0):
        bad.append("ENTRY_FILL_MAX_S must be > 0")
    if CHAMPION_OWNER and (CHAMPION_OWNER[0] not in VARIANTS or CHAMPION_OWNER[0] in CONTROLS):
        bad.append(f"CHAMPION_OWNER {CHAMPION_OWNER[0]!r} is not a registered non-control variant")
    if CHAMPION_DEFAULT not in VARIANTS or CHAMPION_DEFAULT in CONTROLS:
        bad.append(f"CHAMPION_DEFAULT {CHAMPION_DEFAULT!r} is not a registered non-control variant")
    if not (0 < CHALLENGER_ALPHA < 0.5 and CHALLENGER_MIN_DAYS >= 3 and PROMOTE_STREAK >= 1):
        bad.append("challenger test parameters out of range")
    if not (EXIT_QUOTE_STALE_S < EXIT_DEFER_MAX_S):
        bad.append("EXIT_QUOTE_STALE_S must be below EXIT_DEFER_MAX_S")
    if LOT_SIZE <= 0 or STRIKE_STEP <= 0 or START_CAPITAL <= 0:
        bad.append("lot size, strike step and capital must be positive")
    if not PAPER_ONLY:
        bad.append("PAPER_ONLY is False — v1 is paper-only (owner, 17 Oct 2026)")
    return bad
