# 64. The first step after the outside review (15 Nov 2026, late evening)

Owner, after reading `docs/63` (an outside review of commit `c489e61`): "Yes, start". The step agreed: three things,
none of which changes a live entry or the live pool.

Later the same evening the owner said "Yes, build it" to a shadow twin with a longer fill window on expiry days.
Section 6 records that work. **It also corrects this note:** the first version said entries were lost on 9 Nov because
the option did not update in time. The recorded ticks show the option always had; the engine was late.

Two more steps followed, both on the owner's word: a speed check with all 124 books ("Yes, run it", section 6.5) and
**one change to a live fill rule** ("Yes, change it", section 6.6): an entry is no longer dropped because the engine
itself looked late.

## 1. What `docs/63` says, and what held when checked

`docs/63` argues that the system measures far more than it acts on, that the live account takes the first eligible
trigger without comparing what each candidate is worth, and that the next work should be a count of why the account
sits idle, parity between the research harnesses, one new non-pullback entry, exits tied to the entry's reason, and
only then a selector between candidates.

| Its claim | Checked against the code |
|---|---|
| The Conductor takes `eligible[0]` in priority order | True (`apex/engine/conductor.py`, `step`) |
| The strike picker's expected-value score is overwritten by the delta target | True (`c20_08.py`, `_pick`) |
| With no futures and no index price every exit stops, time exits included | True. The fix of earlier today only said so. Section 4 below changes it |
| The research "pooled" account sells an add-on when the champion's next trade fills, which the live account cannot do | True (`arena_fixed.py`, `run_day`, reason `PREEMPT`). The pooled figures in `docs/60` are conditional. The holdout verdict stands: the finalists lost on their own |
| The scorer can fall back to model prices | True. Each trade's `price` column says how it was priced; the count was never reported |
| 200 trades cannot settle the scoreboard's test | True (expected log-likelihood ratio 0.69 against a line of 2.77) |

Its own new experiment (18 sessions, 8,481 events, bought at the ask and sold at the bid after 3, 5 and 10 minutes) was
not rerun here. Its negative result agrees with `docs/60`: following heavyweights and sister indices does not pay.

## 2. The 13 Nov trade it asked about, and what it shows

`docs/63` section 6.2 asks why the rent trail did not protect the put bought on 13 Nov at 12:36:27. Every pool book
bought the same put at the same second, at 184.10.

| Book | Sold | Rule | Result |
|---|---|---|---|
| The Conductor, copying c20_9y | 13:19:02 at 170.95 | forward trail | -7.14 % |
| c20_9v, c20_9x | 13:19:02 at 170.95 | forward trail | -7.14 % |
| c20_9t (the rent-trail book) | 12:51:38 at 193.30 | rent trail | +5.00 % |

The protection worked in the one book that has it. The live account copies whichever book wins the same-tick priority,
and c20_9t is last. **Of the Conductor's 22 live trades c20_9y owned 18** (c20_9s 2, c20_9v 1, c20_9t 1). The live
account's exits are in effect c20_9y's.

Four live days, each book's own account in rupees on Rs 1,00,000:

| Book | 9 Nov | 11 Nov | 12 Nov | 13 Nov | Sum |
|---|---|---|---|---|---|
| c20_9t (12 rent-trail exits) | +58.4 % | +10.6 % | +13.8 % | -18.3 % | +64.6 % |
| Conductor | +59.7 % | +7.4 % | +3.7 % | -27.1 % | +43.7 % |
| c20_9s | +30.5 % | +18.7 % | +7.3 % | -22.5 % | +34.1 % |
| c20_9x | +30.5 % | +18.7 % | +3.7 % | -27.1 % | +25.9 % |
| c20_9v | +30.5 % | +17.9 % | +3.7 % | -27.1 % | +25.0 % |
| c20_9y | +30.5 % | -5.2 % | +3.4 % | -27.1 % | +1.7 % |

The offline account simulator, which reproduces the live record exactly (+59.7, +7.4, +3.7, -27.1), gives for the same
four days with c20_9t first: **+68.3 %, +2.0 %, +25.7 %, -18.3 %, a sum of +77.8 % against +43.7 %**, on 25 trades
against 22.

Four days, chosen after seeing them, against an in-sample priority that ranked c20_9t last. A lead, so a shadow.

## 3. What was built

### 3.1 `conductor_rt`: a shadow account that copies the rent-trail book first

`apex/engine/conductor.py` (`FIRST_BOOK`, policy `rtfirst`) and `VARIANTS["conductor_rt"]` in `apex/config.py`. The
same pool as the live account; c20_9t wins a same-tick tie. Its own all-in capital. 123 variants with it (124 with the
twin of section 6). The nightly report lists it beside the live account from 16 Nov. The live pool file and the live
Conductor are untouched.

### 3.2 The opportunity funnel in the nightly report

`apex/conductor/funnel.py`, read from the account's own log. It answers `docs/63`'s first request: where the day went
and what became of each trigger. On the four live days:

| Day | Moments a pool book fired | Taken | Filled | Released unfilled | Holding | Flat, no trigger | Blackout |
|---|---|---|---|---|---|---|---|
| 9 Nov (expiry) | 54 | 48 | 12 | 36 | 13 % | 85 % | 1 % |
| 11 Nov | 5 | 4 | 4 | 0 | 21 % | 78 % | 1 % |
| 12 Nov | 5 | 3 | 3 | 0 | 28 % | 72 % | 0 % |
| 13 Nov | 3 | 3 | 3 | 0 | 15 % | 71 % | 15 % |

Two things stand out.

* **On normal days the pool fires three to five times a day.** The account is flat for over 70 % of the session with no
  trigger at all. More trades on normal days need a new entry, not a looser filter.
* **On the expiry day three of four chosen entries never filled, and the engine was the cause, not the market.** All
  36 were released with "entry lapsed: no print within 3 s". They fall into 13 runs of retries; 3 runs filled a little
  later, and **10 never filled**: for example the 24,950 put at 13:13 was tried 8 times in 200 seconds. The account
  took 12 trades that day, the last at 11:57, and none after. Section 6 has the tick check.

What the funnel cannot see: a market move that fired no pool book. That needs the decision ledger of `docs/63`
section 5.1, which is not built.

### 3.3 Exits that still run when the underlying prices are missing

`engine_main._risk_step`. With neither a futures nor an index price the normal step cannot run. A held option may
still be quoted. For champion-family books that hold a position, the rules that need no forward now still run: the
premium stop, the hold clock, the forced flat at 15:00 / 15:20, and the fill of an exit already requested. The Conductor
accounts follow their owner book. Fills follow the usual rule: a clock exit at once, a price exit after at most 10 s
and tagged `stale_exit`. Nothing can be bought: the step runs only in a blackout. Older books still wait for data.

## 4. Checks

| Check | Result |
|---|---|
| `tests/test_doc63_15nov.py` (12 tests with section 6) | pass |
| Hold clock with empty futures and index rows, option quoted | the book sells at the option's fresh price; the account follows; nothing is bought |
| Premium stop in the same state | sells, tagged `stale_exit`, as every blackout fill is |
| Offline simulator against the live record, live pool | identical on all four days |
| Full suite, 15 Nov 20:44, before section 6 | 765 passed, 8 skipped, 4 expected failures, 1 unexpected pass, no failure (7 min 5 s) |
| Full suite after section 6.4, 15 Nov 21:18 | 768 passed, 8 skipped, 3 expected failures, 2 unexpected passes, no failure (5 min 27 s) |
| Full suite after the rule change of section 6.6, 15 Nov 21:50 | 771 passed, 8 skipped, 3 expected failures, 2 unexpected passes, no failure (3 min 32 s) |

Not verified: none of it has run in a live session. The price-free exits are tested on a rig, not on a real feed
restart.

## 5. Open

* **The expiry-day fill window.** Built as a shadow twin after the owner's "Yes, build it": section 6.
* **The engine's step time on Monday.** Measured: section 6.5. The books are not the risk; other work on the machine
  during market hours is.
* `docs/63`'s next items: parity between the real classes, fastlab and the research replica on a small set of days
  (needs replays), one frozen non-pullback entry, exits tied to the entry's reason.
* The 13 Nov trade also shows the 15-minute stall twin would not have sold it (it was +6 % at 15 minutes), as `docs/63`
  says: a trade that gives back a profit is a different case from one that never moves.

## 6. The expiry-day fill window (owner: "Yes, build it")

### 6.1 The cause was the engine, not the market

The first version of this note read the log's own words: "no print within 3 s". Checked against the recorded ticks
(`data/ticks/2026-11-09.jsonl.gz`) for all 48 entries the account chose that day:

| | Filled (12) | Lapsed (36) |
|---|---|---|
| The option's row next updated, after the trigger | 0.09 to 1.07 s | 0.00 to 0.94 s |
| Updates of that row in the next 3 s | 3 to 5 | 4 to 6 |
| The engine's first look, after the trigger | 1.0 to 3.0 s | 3.0 to 7.4 s (median 5.8 s) |

**Every one of the 36 options had a fresh price inside one second.** The engine did not look until the 3-second window
had closed, and the code drops an entry older than the window before it checks for a print. The delay was the save
freeze of that day (every save re-wrote every closed trade; fixed that night, `paper._trade_text`). The fill delays
show it building: 1.0 s at 09:26, 2.2 s at 10:20, 2.9 s at 10:56. After the 11:57 trade no entry filled.

So the live record of 9 Nov ends at 11:57 for every pool book. The "four live days" of section 2 are three days and a
morning.

### 6.2 What the missed afternoon was worth

fastlab: the real strategy classes on the recorded day, buying at the ask and selling at the bid (stricter than the
live rule), with no engine delay.

| Book | To 11:57 | After 11:57 | The afternoon's trades |
|---|---|---|---|
| c20_9y (the account's owner on 46 of its 48 choices) | 14 trades, -13.2 % | 7 trades, **+47.2 %** | +18.3, +5.8, -2.2, +40.1, -0.6, +1.7, -15.1 |
| c20_9t (the rent-trail book) | 14 trades, +49.3 % | 11 trades, **-31.0 %** | six gains of +2 to +12, one loss of -9, four stops near -16 |

Three cautions.

* One afternoon. Without the single +40 % trade, c20_9y's afternoon is +5 %.
* The simulator is rough. It reads c20_9y's morning at -13.2 % where the live book made +30.5 % (stricter fills and
  two extra losing trades).
* **It cuts against section 2.** On the afternoon nobody traded, the rent-trail book did far worse than c20_9y. The lead
  for `conductor_rt` is weaker than section 2 reads. It stays a shadow, to be measured.

### 6.3 Is the engine fast enough now?

From `data/logs/perf_<day>.jsonl`, session minutes only (median and 95th percentile are the middle minute's):

| Day | Median step | 95th percentile | Worst step | Minutes with a step over 1 s | Entries lapsed |
|---|---|---|---|---|---|
| 11 Nov | 31 ms | 105 ms | 0.9 s | 0 | 0 of 4 |
| 12 Nov | 42 ms | 150 ms | 1.2 s | 3 | 0 of 3 |
| 13 Nov | 72 ms | 216 ms | 3.6 s | 12 | 0 of 3 |

No entry was lost on these days. The step has slowed each day all the same. On 13 Nov one step took 3.6 s (10:57), and
the step at the second every pool book bought (12:36:27) took 1.6 s: a step over 3 s at such a second drops the entry
exactly as on 9 Nov. The code that ran on 13 Nov had 106 books, 13 of them strategy-class books, and one account.
Monday's has 124 books, 25 strategy-class books and eight accounts. The step time with all 124 was then measured:
section 6.5.

### 6.4 What was built

* **`lw_c20_9y`**, a shadow twin of c20_9y (`apex/config.py`, `paper.entry_wait_s`). On the option's own expiry day its
  entry waits up to 10 s for a print, the limit an exit already waits; 3 s on every other day, as every book. A fill
  later than 3 s carries `late_entry`. With a fast engine and a busy option it makes c20_9y's trades. It differs when
  the engine's look comes late or the option is quiet, which is the case to measure. It is in no pool; the key is
  refused on any book that is not a shadow twin and above 30 s (`config.validate`). Next expiry day: 17 Nov.
* **The funnel sorts every lapse by its cause**: the engine was late, a data gap, or a quiet option. A lapse is the
  engine's when the reason carries the stall tag (written since 10 Nov) or the account let go more than half a second
  after the window closed. The nightly report then says so in bold. On 9 Nov it marks 34 of the 36; the ticks show the
  other two (released 3.03 and 3.17 s after the trigger) were late looks too.

The live rule itself was changed later the same evening: section 6.6. Since then every book keeps an entry the
engine looked at late, so the twin differs from c20_9y only when the option itself is quiet for 3 to 10 s.

### 6.5 The speed check (owner: "Yes, run it")

The real engine, stepped through the recorded 9 Nov tape (an expiry day) from 08:45 to 09:37, every step timed. Two
runs back to back on a quiet machine: the code that ran live on 13 Nov, and tonight's. Each run wrote only to its own
scratch folder. The window holds two seconds at which every pool book and every twin buys at once (09:26:55 and
09:35:29); the account made the same trades in both runs.

| 09:15 to 09:37, 13,200 steps | 13 Nov code | Tonight's code |
|---|---|---|
| Books / strategy-class books / accounts | 106 / 13 / 1 | 124 / 25 / 8 |
| Median step | 7.7 ms | 7.9 ms |
| 95th percentile | 20.8 ms | 25.2 ms |
| 99th percentile | 32 ms | 45 ms |
| Slowest step (the second every pool book buys) | 129 ms | 298 ms |
| Steps over 300 ms / over 1 s | 0 / 0 | 0 / 0 |

**The extra books cost almost nothing on an ordinary step** (+2 % on the median, +11 % on the mean). The entry second
is 2.3 times heavier, because five more twins of c20_9y and seven more accounts act on the same second. It is still a
tenth of the 3-second window.

**So the books did not slow the engine on 13 Nov. Something else did.** The live log of that day, same code all day:

| 13 Nov, live | Minutes | Median step |
|---|---|---|
| 09:40 to 10:20 and 11:40 to 12:20 | 80 | 7.9 ms (the same as this check) |
| 10:20 to 11:40 and 12:20 to 15:00 | 240 | 87 ms |
| The three seconds the account bought (10:53, 12:36, 14:29) | 3 | steps of 2.06, 1.56 and 1.87 s |

In the slow stretches the engine ran 11 times slower than its own cost, and 16 to 23 times slower in the three minutes
it traded. What took the processor is not in the logs. The size of it matches 10 Nov, when other jobs on this machine
made runs 12 to 17 times slower.

**What it means for Monday.** On a free machine the entry second takes 0.3 s. Under the load of 13 Nov (12 to 21 times
on that step) it would take 3.6 to 6.3 s, past the 3-second window, and every book's entry would be dropped as on
9 Nov. The 13 Nov code survived that load with 1.6 to 2.1 s; tonight's would not.

Two protections, in order of effect:

1. **No other heavy work on this machine from 09:15 to 15:30**: no test suite, replay, research run or agent batch.
   That alone restores a tenfold margin.
2. An entry is no longer dropped before the engine has looked: section 6.6, built on the owner's "Yes, change it".

One pair of runs, on the expiry-day tape only. A fast replay leaves out the dashboard's four-a-second publish and the
feed process, so its absolute numbers are a floor; the live calm stretches of 13 Nov show the floor is real.

### 6.6 The late-look rule (owner: "Yes, change it")

A change to the live fill path, and to rule D-126 of 30 Oct. `paper.try_fill_entry`; `config.ENTRY_LATE_LOOK_MAX_S`
is 10 s. The 3 seconds are the time the option has to print, not the time the engine has to look. The code used to
drop an entry older than 3 s before it checked for a print. It now keeps the entry when the engine itself was slow:
a gap of 1 s or more between two of its own steps while the entry waited (`paper.ENGINE_STALL_S`, the measure the
lapse tag has used since 10 Nov).

| Case | Before | Now |
|---|---|---|
| The option prints and the engine looks, both within 3 s | fills at that price | the same |
| No print within 3 s | lapses | the same |
| The option has printed; the engine's look comes after 3 s because its own step gap reached 1 s | **lapses unseen** | **fills at the price then on the screen**; the trade carries `late_entry` and `late_gap_s` |
| The look comes after 3 s with the engine keeping up (a book that looks once a second) | lapses | the same |
| The kill switch appears while an entry waits | could still fill inside its window | lapses at once |
| The engine looks more than 10 s after the trigger | lapses | lapses; the reason now says the engine was late |
| A blackout, or past the last entry time | lapses | the same |

Unchanged: fills are at the last traded price; nothing is bought in a blackout; 10 s is also the limit an exit waits
and the pause after which the data guard itself calls a blackout. The rule is in the shared fill path, so it holds
for every book, and each Conductor account follows its owner book into the late fill.

What to keep in mind.

* **A late fill is a later price than the one the signal saw.** On 9 Nov it would have been 3 to 7 s later. The trade
  says so (`late_entry`, `fill_delay_s`, `fill_slip`), and the nightly report counts such fills in bold so their
  results can be read apart from the rest.
* **On an engine that keeps up nothing changes.** The first version, written on the night of 15 Nov, filled on any
  print since the trigger. An independent review before the first live session (16 Nov, 07:30) showed what that
  meant: the champion-family books look once a second, so an option silent for 3 s and printing at 3.5 s would have
  been bought at the 4 s look. The late fill now needs the engine's own delay. A replay, where the engine is never
  late, is therefore identical to the rule as it was.
* **It does not make a slow engine safe.** Exits wait on the engine too. The first protection of section 6.5 stands:
  no other heavy work on the machine in market hours.

Tests (`tests/test_doc63_15nov.py`): a look at 5.7 s with a fresh row fills, tagged, for c20_9y, c20_9t and an older
book; no print lapses at 3 s as before, on a slow or a fast engine; with the engine keeping up, a print at 3.5 s seen
at a 4 s look lapses, and so does a step gap of 0.9 s, while 1.0 s fills; a look at 10.5 s lapses and says why; a
blackout, the kill switch and the last entry time still drop it; the account follows its owner into the late fill
and the report counts it.

## 7. Tested against the recorded sessions (owner: "Have you tested it against all the taped data?")

It had not been. Sections 2 to 6 rest on four live days, unit tests and one 52-minute engine run. The check below was
run after the question, in 70 seconds: the five pool books' real strategy classes on all 18 sessions of the fast
simulator's set (19 Oct to 13 Nov; the tapes of 17, 18 and 20 Oct are not in that set), buying at the ask and selling
at the bid, then the account rebuilt offline in both orders.

| 18 sessions | Account, live order | Account, c20_9t first (`conductor_rt`) |
|---|---|---|
| Sum of day results | +1,162.7 % | +334.6 % |
| Days up | 12 | 12 |
| Trades | 124 | 135 |
| The 4 expiry days | +693.9 % | +96.1 % |
| The 14 normal days | +468.8 % | +238.6 % |
| The 4 sessions from 9 Nov | -16.8 % | -3.0 % |

* **The lead of section 2 does not hold.** With c20_9t first the account is better on 8 days and worse on 10, by 46
  points a day on average (t -1.56). The rent trail sells the big trend days early: 27 Oct +176 % against +700 %,
  26 Oct +132 % against +235 %. Only on the four sessions from 9 Nov is it ahead, which is where the lead came from.
  The same was found on 1 Nov (D-147). `conductor_rt` stays a shadow that the tapes do not support.
* **The level is in-sample.** These books were built on these tapes. Over 984 sessions the same pattern breaks even
  (`docs/58`), so +1,162 % is not an expectation.
* **The 10-second twin changes nothing on the tapes.** On the four expiry sessions `lw_c20_9y`'s rule made the same
  14, 13, 9 and 21 trades as c20_9y: no option was quiet for 3 s at an entry.
* **The late-look rule cannot be tested on a tape.** A replay steps the engine on the recorded clock, so the engine is
  never late in one. Its tests are the unit tests of section 6.6.
* The simulator is rough (section 6.2), and the account in it differs from the live record by up to tens of points a
  day.

The full engine was then run on the tapes overnight, on the owner's "Tonight": section 8.

## 8. The full engine on the tapes (owner: "Tonight"; night of 15 to 16 Nov)

Tonight's code, all 124 books, the real engine and its own fill rules, through the project's batch driver, one run
folder a tape (`data/replay/batch/night15q_<day>`), the current pool applied to every tape. **12 of the 18 recorded
sessions finished, none failed, no fault or traceback in any log.** Not run: 22, 23, 28, 30 Oct and 2, 5 Nov.
(Three of the 21 tape files, 17, 18 and 20 Oct, are empty.)

Two things went wrong on the way, both mine. The first start died after 111 minutes when my supervisor script could
not rewrite a status file another check of mine was reading; it took its four replays with it and no tape had
finished. And a tape takes about 2 hours 10 minutes with four running, not the 50 minutes I had said, so 18 could not
fit before the 07:15 stop. The restart finished its twelfth tape at 06:15.

### 8.1 Today's account against the champions of the past

Sum of the day results, each day all-in on Rs 1,00,000. 16,397 trades in all books.

| Book (when it was champion) | 12 sessions | Without 27 Oct | The 8 sessions to 6 Nov | The 4 sessions from 9 Nov | Days up |
|---|---|---|---|---|---|
| **The live account today** | **+949.6 %** | +417.6 % | +924.9 % | **+24.7 %** | 8 of 12 |
| c20_9x (30 Oct to 8 Nov) | +910.5 % | +378.5 % | +887.8 % | +22.7 % | 8 |
| lvl_trail_re (28 Oct) | +361.7 % | +315.3 % | +263.3 % | +98.4 % | 9 |
| t28_gap (29 Oct) | +350.8 % | +304.3 % | +263.3 % | +87.4 % | 9 |
| c20_9t (31 Oct, never live) | +349.1 % | +177.8 % | +345.6 % | +3.5 % | 8 |
| t28_cheap (29 Oct) | +303.2 % | +233.2 % | +327.6 % | -24.4 % | 6 |
| spot_dual | +288.9 % | +285.2 % | +230.5 % | +58.4 % | 8 |
| spot_dc12_t12 (20 Oct) | +228.6 % | +225.0 % | +191.8 % | +36.8 % | 8 |
| spot_dual_lvl | +215.0 % | +205.2 % | +160.8 % | +54.3 % | 8 |
| spot_pb45 | +128.5 % | +218.7 % | +176.3 % | -47.9 % | 7 |
| edge_gate_trail (27 Oct) | +104.5 % | +97.9 % | +98.8 % | +5.7 % | 7 |
| The first build (17 Oct) | +58.2 % | +16.5 % | +32.6 % | +25.6 % | 4 |
| Control: random entries | +58.7 % | +54.1 % | +40.6 % | +18.1 % | 7 |

* **On these tapes today's account beats every past champion**, by about 2.6 times the best one before the c20 family,
  and it ranks 11 of 125 books.
* **More than half of it is one day.** 27 Oct, an expiry day, is +532 of the +950. Without that day the account is
  +418 against +315 for the best older champion: still ahead, by a third.
* **It was built on these tapes.** On the eight sessions the c20 books were made from it is +925. On the four sessions
  since the pool was fixed it is +24.7 %, rank 58 of 125, and six of the eleven past champions did better there.
  The random-entry control made +18.1 % on the same four days. Four days settle nothing either way.
* **The tapes were a kind stretch.** 106 of the 125 books ended above zero, and the middle book made +128 %. Over 984
  sessions the same pattern breaks even (`docs/58`).

### 8.2 The shadows

| Account or book | 12 sessions | Worst day | Note |
|---|---|---|---|
| The live account | +949.6 % | -36.2 % | |
| c20_9y alone | +1,014.4 % | -26.7 % | the account's usual owner beats the pooled account |
| `conductor_rt` (c20_9t first, section 3.1) | **+409.7 %** | -32.4 % | better on 3 days, worse on 9 |
| `lw_c20_9y` (10 s wait, section 6.4) | +1,014.4 % | -26.7 % | the same trades as c20_9y on every tape |
| `conductor_wp60` (13 Nov) | +1,013.0 % | -24.6 % | 85 trades against 102 |
| `conductor_sl` (13 Nov) | +881.1 % | -13.7 % | 9 days up; the smallest worst day |
| tp_c20_9y, st15_c20_9y (twins of 13 and 14 Nov) | +1,142.8 %, +1,055.1 % | -26.7 % | first and second of all 125 books |

* **`conductor_rt` is not supported.** It agrees with the 70-second check of section 7 and with D-147.
* **`lw_c20_9y` changed nothing.** No option was quiet for 3 s at an entry on any of the 12 tapes.
* The older shadows in the last three rows are in-sample too, and `conductor_sl` had no earlier days to read in a
  one-tape run. They are leads, no more.

### 8.3 The late-look rule in a replay

2 of 16,397 trades carry `late_entry`: one entry of spot_pb45 and its restricted twin on 19 Oct, filled 3.1 s after
the trigger. The overnight run used the first version of the rule; with the rule as corrected on 16 Nov (section 6.6)
those two fills would not happen, and nothing else in the run depends on the difference. No pool book and no account
was touched. On the replayed 9 Nov
the account chose 22 entries and all 22 filled: with an engine that keeps up, none of the 36 lapses happens.

The replayed 9 Nov also prices the afternoon the live engine missed, at the live fill rule:

| 9 Nov, replay | To 11:57 | After 11:57 | Day |
|---|---|---|---|
| The account | +28.4 % (13 trades) | +11.5 % (9 trades) | +43.2 % |
| c20_9y | +0.2 % | +56.7 % | +57.1 % |
| c20_9t | +64.6 % | -30.2 % | +14.9 % |

### 8.4 The replay is not the live day

| Day | The account, live record | The account, replay | c20_9t, live | c20_9t, replay |
|---|---|---|---|---|
| 9 Nov | +59.7 % (12 trades, engine frozen from noon) | +43.2 % (22) | +58.4 % | +14.9 % |
| 11 Nov | +7.4 % (4) | +9.0 % (4) | +10.6 % | +5.9 % |
| 12 Nov | +3.7 % (3) | -4.0 % (4) | +13.8 % | +6.2 % |
| 13 Nov | -27.1 % (3) | -23.5 % (4) | -18.3 % | -23.6 % |

The same code on the same tape gives a different day than the live session did: a trade more on two days, and several
points either way. The rent-trail book is worse in every replay than it was live. The cause is not found; the live
engine's slower steps and later fills are the first suspect. Until this is explained, a replay figure is good to
several points a day and no better, and it may be unfair to the rent trail. This is `docs/63`'s first item, parity,
and it is still open.

## 9. Before the first live session (owner, 16 Nov: "Is the code ready to run in production? Check thoroughly")

| Check | Result |
|---|---|
| Full suite on the final code, 16 Nov 07:53 | 771 passed, 8 skipped, 5 expected failures, no failure |
| Twelve full-day engine runs of this code (section 8) | no fault, no traceback |
| The configuration self-check `live` runs first | passes; 124 books, 25 strategy-class, 8 accounts |
| Every strategy-class book loads its class; every engine, feed, gateway and report module imports | yes |
| The live account's pool today | c20_9y, c20_9s, c20_9v, c20_9x, c20_9t, as before |
| The seven shadow accounts build their pools | yes; `conductor_rt` has c20_9t first |
| Holiday calendar, trading day, expiries | 16 Nov is a normal day; the next expiry is 17 Nov |
| Dashboard scripts parse; the card test | 7 payloads rendered, 0 failures |
| Port 8780 free; no kill file; no books file for today; 53 GB of disk free | yes |
| Credential-shaped strings outside `secrets/` | none |
| An independent review of the live-path changes | no crash, duplicate-trade or saved-state defect; one rule mismatch, fixed (section 6.6); three small points below |

The reviewer's other points: the kill switch was not checked at the fill (fixed, section 6.6); the nightly funnel
could fail on a torn log line (fixed; it only ever lost its own section); and, live only, an option row's age is read
a few milliseconds after the step's clock, which can only drop an entry, never mis-fill one (not changed).

Not checked by me, the owner's to do with today's token: the broker login and the live stream (`run_apex.py
preflight`). Not exercised by any test or replay: an engine step that really comes late in a live session.

Found on the way, not part of the engine: the Forecast Lab's nightly run of 13 Nov failed on its 12 Nov step
(`data/nightly_status.json`), so the Lab has not learned 12 and 13 Nov. Its lock file is stale and harmless (the lock
is the operating system's, freed when that process ended).
