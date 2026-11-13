# R14. Engine speed (owner point 6: "no errors live, blazing fast")

Analyst R14, 13 Nov 2026. Static reading of the engine's hot paths, the perf logs of 11, 12 and 13 Nov (read only),
the SLOW TICK lines, and small synthetic checks. No replay, no engine, no shared memory was touched.

## Findings first

1. **No runtime errors on 12 and 13 Nov.** engine.log has no "faulted", traceback or error line on either day, and
   the saver reports 0 errors. Point 6 is now a speed problem, not an error problem.
2. **The engine is close to saturation.** It aims at 10 steps a second. It managed about 9. The mean step was
   45 ms (11 Nov), 60 ms (12 Nov) and 68 ms (13 Nov to 13:27). On 12 Nov between 12:00 and 13:00 the mean step was
   91 ms, so the loop could not keep 10 Hz. Steps over 300 ms: 458, 1,728 and 4,090 on the three days.
3. **Most of the slowdown is the machine, not the code.** "step:market" does the same fixed work every step. It
   still went from 5.3 ms (09:00) to 14.5 ms (13:00). Every part slows together in the same minutes. The engine
   competes with the other trading systems at about 87 % CPU, at normal priority.
4. **Some parts grow with the day (O(history)).** On 11 Nov "weather base" went 0.44 to 2.54 ms per step (5.8 times)
   while "step:market" rose only 1.2 times. I found the loops that grow: a backward walk over the VWAP side
   (weather.py:543), two whole-day percentile scans in the regime (regime.py:47-52), a 720-sample list scan at
   10 Hz for the forward books (engine_main.py:1299) and a 1,800-sample median every second (engine_main.py:1279).
5. **The restricted books take a full 457-field photograph at 10 Hz just to be refused.** spot_dc12_t12_first_r002
   re-fires every step while spot is outside its 12-minute range. Each time, rules.check builds the whole
   photograph (rules.py:153) to read four fields, R-002 says no, and the setup is dropped. Cost: 151 to 227 s a day
   for that one book, steps of 100 to 276 ms each. All restricted books together: 179 to 298 s a day.
6. **Display and observers cost 18 to 23 % of the engine's time**, publish alone 701 to 1,292 s a day. No book
   reads any of it.
7. **The c20_8x "423 ms first tick" is the council day table**, not c20_8x. The first council book allocates
   14 float32 arrays of 22,501 x 96 (121 MB) at 09:00, and every second it writes the shared row for all council
   books in a Python loop (council/__init__.py:49 and 66-115). That is the 86 to 94 s a day charged to c20_8x.
8. Ten changes below keep every decision bit-identical by construction. Five of them I checked for identity on
   synthetic data (all identical). None is tested in a replay yet: the replay gate is Phase B and needs your OK.

## Teardown

### The loop (engine_main.py)

| Part | Lines | What it does each step | Weak point |
|---|---|---|---|
| run loop | 2193-2230 | step, then sleep `max(0.1 - elapsed, 0.005)` | at 90 ms steps the engine has no slack; it runs at whatever rate the CPU allows |
| step:day | 475-491 | clock, day change | 918 ms on the first tick (start_day), pre-open, harmless |
| step:market | 492-502 | `t.snapshot()` (200 KB copy, table.py:142), `Market.push` (8 ring columns, market.py:40-76), `Flow.update` (~80 numpy calls on 512 rows, flow.py:88-163), spot guard | only 137 of 512 rows are used; every array op runs over all 512 |
| step:greeks | 503-506, 793-859 | 4 Hz: Black-76 IV by 40 bisection rounds on 84 contracts (greeks.py:68-107), Greeks, a dict per contract | about 60 numpy calls per round, 2,400 per solve |
| step:one-hz | 507-540 | 1 Hz: weather feeds, gen2, gen3, histories, forward history, edge snapshot, quant view, OI history | all 1-Hz work lands on the same step, so one step a second is 3 to 5 times the others |
| step:guard-domino-regime | 559-597 | data guard, domino (10 Hz), regime (1 Hz) | regime `_pct` copies the whole day's list twice a second (regime.py:47-52, 110-111) |
| step:observers | 598-612 | straddle, straddle watch, bank, lag, force | small |
| step:ctx | 613-649 | option rows, day view, ranges, `_fwd_view` | `_fwd_view` scans 720 samples in a list comprehension at 10 Hz (1299) |
| step:pre-books | 650-689 | weather v3 feed, weather base (1 Hz), option history, book_state, strike levels (1 Hz), advisors | weather base grows during the day (below) |
| step:books | 690, 1625-1704 | 107 books: exit then entry; the Conductor; saves | per-book time is logged only above 2 ms (1633), so most of the 12 ms is invisible |
| step:post-books | 692-702 | ledger, episode log, ideas board (1 Hz) | ideas is display only |
| publish | 2036-2173 | 2 Hz: the whole dashboard state as JSON into shared memory | 23 ms per publish on 13 Nov |

### Where it fails, item by item

**F1. Restricted-book photographs (rules.py:146-160, engine_main.py:1819-1825, paper.py:385-387).** A first-touch
spot book returns "fire" on every step while spot is beyond its 12-minute range. `_entry_choice` then calls
`rules_mod.check`, which calls `photo(ctx, d, opt, book)`: all of v1 to v5, 457 fields, the 107-book scan in
`_p_books` (weather4.py:568-627), the OI-history linear scans (weather.py:918-936), the two-barrier passage model
(weather.py:972), and more. R-002 reads `expiry_day`, `mins_open`, `er60`, `dir60`. R-003 reads `breadth_dir`.
R-004 and R-005 read `expiry_day` and the clock. All five fields are set in the first 30 lines of `photo()`
(weather.py:604-633) and nothing later overwrites them (I checked every `out[...]` writer in weather.py,
weather4.py and weather5.py). When the rule passes, `request_entry` builds the same photograph a second time
(paper.py:1281).

**F2. VWAP-side walk (weather.py:539-546).** `vwap_side_min` walks back one sample at a time while the futures stay
on one side of VWAP. After three hours on one side that is about 11,000 Python iterations, every second.

**F3. Regime percentiles (regime.py:47-52).** `_pct` turns the whole day's `rv_hist` and `ext_hist` (22,000 values
by the close) into new numpy arrays twice a second. The regime is a decision input (VETO_ANY), so the fix must be
exact.

**F4. Forward view (engine_main.py:1292-1303).** The `spot_src="fwd"` books get their range from a list
comprehension over the whole 12-minute deque, 10 times a second. The spot version of the same range was already
moved to bisection on 11 Nov (T02, 1305-1318); the forward version was not. Logged as "forward view": 140 to 240 s
a day.

**F5. Basis median (engine_main.py:1279).** `np.median` of up to 1,800 values every second ("forward history",
35 to 54 s a day).

**F6. Council day table (council/__init__.py:41-49, 66-115, 150-153).** 121 MB allocated at the first council step.
Each second `put` loops over every option, builds a dict of 10 values and does up to 14 numpy scalar writes per
option (about 800 a second). Charged to whichever council book runs first (c20_8x).

**F7. Publish (engine_main.py:2036-2173, table.py:196-244).** The champion's open position is published as
`dict(p, ...)` (2086), so its 457-field `weather_trig` (about 10.6 KB of JSON) plus `signal` and `edge_trig` go to
the dashboard twice a second. The dashboard never reads them (checked apex/static/app.js: no `weather_trig`,
`signal` or `edge_trig`). `dumps_part` encodes everything a second time, through `clean()`, whenever the text
contains "NaN" (table.py:242), and nothing counts how often that happens.

**F8. Books-save text on the step (paper.py:1765-1791).** Each save re-encodes every book's head with
`json.dumps`; heads of open positions and pending entries carry their photographs. "save books (trade)" plus "save
exit state" cost 166 to 413 s a day, with single saves up to 402 ms. The write itself is on a thread, but its text
encoding still holds the GIL; the median write took 719 ms on 13 Nov (Defender is still scanning each 8 to 17 MB
copy).

**F9. Strike-levels tape (engine_main.py:704-724).** Every break event opens, appends to and closes
`strikes_<day>.jsonl` (720). Each close is a fresh Defender scan.

**F10. Garbage collection is never tuned or measured.** No `gc` call anywhere in apex/ or run_apex.py. The engine
keeps hundreds of thousands of live containers by the afternoon (photographs in every trade and pending entry,
the 107 books, deques of dicts). A full CPython collection walks all of them. Nothing in the perf line would show
such a pause as its own phase; it would land inside whatever phase was running.

**F11. Per-book timing hides most of the books loop (engine_main.py:1633).** Only a book over 2 ms in a step is
charged. On 12 Nov the logged "book:*" total was 388 s of the 2,486 s in "step:books".

### The SLOW TICK lines

22 lines in engine.log for 11 to 13 Nov. Three kinds:

| Kind | Example | Cause |
|---|---|---|
| day start or end | 11 Nov 15:41 12.7 s "day 12500"; 13 Nov 09:00 1.5 s "day 918, c20_8x 423" | end_day learning; the council table allocation. Outside the entry window |
| one heavy book | 12 Nov 12:45 1.1 s "spot_dc12_t12_first 256, _r003 246, _r002 118" | F1: photographs (the free twin on its real trigger, the restricted twins on refusals) |
| everything slow at once | 13 Nov 10:57 3.6 s: books 3,303 ms, spot_pb45 177, lvl_trail 150, lvl_trail_be 141 ... | ordinary books at 120 to 180 ms each: the process was starved (machine load, a books write running, save lag 0 to 2) |

## Evidence

### Where the time goes (perf logs, 09:15 to 15:30, read only)

| | 11 Nov | 12 Nov | 13 Nov (to 13:27) |
|---|---|---|---|
| steps | 213,370 | 202,192 | 129,042 |
| engine step time | 9,691 s | 12,091 s | 8,804 s |
| mean step | 45.4 ms | 59.8 ms | 68.2 ms |
| steps over 300 ms | 458 | 1,728 | 4,090 |
| steps over 1 s | 0 | 8 | 19 |
| display / observers (publish, quant view, ideas, pred, commentary, forecast panel, gen2, gen3, logs, health) | 2,214 s (22.8 %) | 2,215 s (18.3 %) | 1,566 s (17.8 %) |
| photograph inputs (weather base, feeds, option history, edge, strike levels, forward history) | 706 s (7.3 %) | 1,103 s (9.1 %) | 828 s (9.4 %) |
| persistence (saves) | 379 s (3.9 %) | 413 s (3.4 %) | 166 s (1.9 %) |
| restricted books (book:*_r00N, logged steps only) | 298 s (3.1 %) | 253 s (2.1 %) | 179 s (2.0 %) |
| median books-file write | 113 ms | 225 ms | 719 ms |

12 Nov by part, mean ms per step: books 12.3, market 9.8, greeks 8.3, pre-books 7.5, publish 6.4,
guard-domino-regime 4.6, ctx 4.3, one-hz 2.5, post-books 1.4, observers 1.3, pressure-gex 0.9.

### Load versus growth (mean ms per step by hour)

| Hour | market (fixed work) 11 Nov | weather base 11 Nov | market 12 Nov | weather base 12 Nov | forward view 12 Nov |
|---|---|---|---|---|---|
| 09 | 5.31 | 0.44 | 6.02 | 0.71 | 0.64 |
| 11 | 5.96 | 0.71 | 8.16 | 1.09 | 1.06 |
| 13 | 8.81 | 2.25 | 12.28 | 4.30 | 1.47 |
| 15 | 6.21 | 2.54 | 9.99 | 3.98 | 1.26 |

"market" tracks the machine load (it does the same work every step). "weather base" outgrows it by 3 to 5 times:
that extra is the O(history) part (F2).

### Identity checks run today (synthetic data, work\R14\identity_checks.py and bench_core.py)

| Rewrite | Test | Result |
|---|---|---|
| regime `_pct`: sorted mirror + `bisect_right` | 6,000 appends with ties, a random x each time | identical |
| `vwap_side_min`: run-start index kept at append | 20,000 samples, side flips, zeros, 130-s holes | identical |
| forward view: bisect slice instead of list scan | 5,000 steps, irregular stamps | identical |
| basis median: sorted 30-min window | 4,000 seconds, rounded values with ties | identical |
| Flow 10-s ring sums: running sum | 3,000 steps of integer lot volumes | identical |
| implied vol: both erf calls as one stacked call | one chain plus 200 random chains, 84 contracts | identical |

Timings on this machine today are not trustworthy: my scripts run at below-normal priority on an 87 % loaded CPU.
The stacked implied vol measured 116 to 61 ms in one run and 32 to 31 ms in the next. Phase B repeats the timings
after the close.

## Ideas

Each idea keeps every decision bit-identical. Savings are estimates from the perf logs unless marked measured.
"Gate" means the Phase B replay equivalence test (below) must pass before the change goes live.

| # | Change | Where | Expected saving | Status |
|---|---|---|---|---|
| 1 | Rule check on a "rule photo" (the 5 fields) | rules.py:146-160 | 160-270 s a day; most 100-276 ms book spikes | untested, gate |
| 2 | Run-start index for vwap_side_min | weather.py:539-546 | up to half of weather base: 150-300 s a day (estimate) | identity checked, gate |
| 3 | Bisect slice in `_fwd_view` | engine_main.py:1299 | 125-215 s a day (most of "forward view") | identity checked, gate |
| 4 | Sorted mirrors for regime `_pct` | regime.py:47-52 | tens of seconds a day, grows to the close | identity checked, gate |
| 5 | Sorted window for the basis median | engine_main.py:1279 | 25-40 s a day | identity checked, gate |
| 6 | Vectorised, pre-allocated council day table | council/__init__.py:41-115 | 60-70 s a day; the 423 ms first tick | untested, gate |
| 7 | Stacked erf in implied vol | greeks.py:90-105 | 0 to 45 % of IV time (greeks is 1,348-1,682 s a day) | identity checked, timing open |
| 8 | Leaner publish | engine_main.py:2036-2173 | 30-50 % of 701-1,292 s a day (estimate) | display only, untested |
| 9 | Cached photograph text in the books save | paper.py:1765-1791 | about half of 166-413 s a day | untested, byte test |
| 10 | Keep the strikes tape open | engine_main.py:720 | a few Defender scans per break | untested, byte test |
| 11 | Measure GC pauses, then freeze | engine_main.py start_day | unknown until measured | observability first |
| 12 | Engine and feed above normal priority | run_apex.py | the largest single lever (finding 3) | owner's decision |
| 13 | Charge every book's time, not only over 2 ms | engine_main.py:1633 | none (visibility) | observability |
| 14 | Exact running sums in Flow | flow.py:113-114 | small | identity checked |

Together 1 to 10 should cut roughly 1,200 to 2,600 s from a 9,000 to 12,000 s engine day (about 12 to 25 %), and
most of the remaining tail would then be machine load (idea 12).

### 1. Rule check without the full photograph

* Mechanism: split the first block of `photo()` (weather.py:601-633: calendar, efficiency, range, breadth) into
  `_photo_head(out, ctx, d, b)`. `photo()` calls it exactly as now. `rules.check()` calls a new `rule_photo(ctx, d)`
  that runs only `_photo_head` when every rule id of the book is in `CODED`, and the full `photo()` otherwise (a
  register factor rule may read any field). Same code lines, so the same values.
* One side effect must be kept: `_p_books` appends `(second, d)` to `W.fire_log` (weather4.py:626-627), and later
  photographs count it ("fires5_same", "fires30_same", "flip_n15"). Move those two lines into `note_fire(ctx, d)`,
  called from `_p_books` where they are now and from `rule_photo`. Then every later photograph is unchanged too.
* Edge to check in the gate: if `_p_books` ever raised before its append, the old code skipped the append. Count
  photos whose `v4_error` names `_p_books` in the A run; if zero, there is nothing to differ.
* Build: about 30 lines in weather.py, weather4.py and rules.py. Test: tests/test_restricted_books.py plus a new
  test that `rule_photo(ctx, d)` equals the same five keys of `photo(ctx, d, opt, book)` on a recorded ctx.
* Risk: low. A future coded rule that reads a field outside `_photo_head` would silently read None and block.
  Guard it: a `RULE_FIELDS` tuple next to `CODED`, and the test fails if a coded rule reads anything else.

### 2. vwap_side_min from a run-start index

* Mechanism: in `Weather.feed_misc` keep a parallel list `rs` for the "ext" series: `rs[k] = rs[k-1]` when sample k
  and k-1 are both non-zero, on the same side, and at most 120 s apart; else `rs[k] = k`. Then
  `vwap_side_min = (t - et[rs[i]]) / 60`. Along the walk every element shares the side of `ev[i]`, so testing the
  side of `ev[j-1]` against `ev[j]` is the same test as against `ev[i]`. O(1) instead of O(run).
* Test: identical on 20,000 synthetic samples. Gate: replay.
* Also worth a look in Phase B: `er_day` (weather.py:213-230) does one bisection per minute of the day every second;
  a numpy mirror of the stamps with `searchsorted` gives the same indices, and the path sum must stay a Python
  left-to-right `sum` to keep the same rounding.

### 3. `_fwd_view` by bisection

* Mechanism: the same `_hist()` cache the spot range uses (engine_main.py:1246-1255), extended with the forward
  deque's stamps and values, rebuilt once a second. Slice with `bisect_left` at `now - SPOT_DC_S` and `now - 0.5`.
  The deque is appended in time order and cleared on a 60-s hole, so the slice holds the same elements in the same
  order, and `max` / `min` are the same.
* Test: identical on 5,000 synthetic steps. Gate: replay (the forward books trade on it).

### 4. Regime percentiles from sorted mirrors

* Mechanism: keep `rv_srt` and `ext_srt` (insort on append). `_pct = 100 * (bisect_right(srt, x) / n)`.
  `np.mean(a <= x)` is an exact integer count over n, so the result is bit-identical. O(log n) instead of two
  22,000-element copies a second. Also `old` (regime.py:119) can be a bisect slice of a stamp list.
* Test: identical on 6,000 appends with ties. Gate: replay (the regime vetoes entries).

### 5. Basis median from a sorted window

* Mechanism: a sorted list beside `_basis_f`; insort on append, remove by `bisect_left` on pop. For an even count
  numpy's median is the mean of the two middle values, which is `(a + b) / 2.0` exactly.
* Test: identical on 4,000 seconds. Gate: replay.

### 6. Council day table

* Mechanism: (a) create the `LiveDay` in `start_day` (`council.shared_day(day, w0)`), so the 121 MB allocation
  happens before 09:15 and not inside a book's step. (b) In `put`, gather the option values once into numpy arrays
  (one list comprehension per field, or straight from `snap` by row id), then one masked assignment per field:
  `a[i, cols[ok]] = vals[ok]`. Float64 to float32 rounding is the same for a scalar and an array assignment. Keep
  the exact masks: value not None, not NaN, and price fields above 0; then the age rule (NaN or None age becomes
  9e9). Column discovery for a new contract stays a small Python loop.
* Test: a unit test feeding the same 3,000 seconds of recorded ctx to the old and new `put` and comparing all 14
  arrays with `array_equal(..., equal_nan=True)`. Gate: replay (all c20 books read D).
* Risk: low if the masks are copied literally. Memory stays 121 MB; float16 or fewer fields would change values,
  so no.

### 7. Stacked implied vol

* Mechanism: inside the 40 bisection rounds, compute `erf` for d1 and d2 as one (2n) array instead of two n arrays,
  and form `ncdf(d)` and `ncdf(-d)` once for both. Same elementwise operations, about 15 fewer numpy calls per round.
  The same trick (stacked EWMAs) was accepted on 11 Nov (flow.py:105-107) after a replay.
* Test: identical on 201 chains. Timing open (see Evidence). Gate: replay, and the existing greeks tests.
* Not proposed: a Newton or Jaeckel solver, caching IV across ticks, or numba. Each would change the last bits of
  IV, delta and theta, and delta picks the strike.

### 8. Leaner publish (display only)

* Mechanism: (a) publish the position without `weather_trig`, `signal`, `signal_trig`, `edge_trig` and `fc`
  (`pos.pop(...)` next to the existing `pos.pop("advisors")`, 2089); about 11 KB less per publish in a trade.
  (b) Move `learning`, `params`, `pressure`, `chain`, `regime`, `quant`, `ledger` and `commentary` into
  `_slow_parts` (1 Hz). (c) Count the second encode in `dumps_part` (table.py:242) and log the count in the perf
  minute; if it fires often, find the NaN at its source.
* Test: no decision can change (nothing reads the published state). Check the dashboard by eye, and diff a few
  published states before and after with those keys removed.
* Risk: a future dashboard panel that wants the photograph must read it from the slow parts.

### 9. Books-save text with cached photographs

* Mechanism: a photograph never changes after its trigger. In `_books_chunks`, replace each `weather_trig` (in
  `pos` and in `ctl.pending_entry`) by a unique placeholder string before `json.dumps(j)`, then splice in the cached
  `json.dumps(weather_trig)` text. JSON nests the same text whether a dict is encoded alone or inside another with
  the same settings, so the file is byte-identical.
* Test: build the text both ways from yesterday's books file (2026-11-12.json, read only) and compare the bytes.
* A bigger later step (not bit-level work): an append-only journal for closed trades, so a trade save writes a few
  KB, not 14 MB. Needs a restart test.

### 10. Strikes tape kept open

* Mechanism: one append handle per day, `write` plus `flush` per event, closed in `end_day` and `stop_path`. Same
  bytes, no open and close per event.
* Test: compare the strikes file of the gate's A and B runs (replay_compare already compares it line by line).

### 11. Garbage collection: measure, then freeze

* Mechanism: register `gc.callbacks` that time generation-2 collections and add them to the perf minute as a phase
  "gc2" (count and ms). If they show up, call `gc.freeze()` at the end of `start_day` (moves the morning's objects
  out of the collector's walk) and consider raising the generation-2 threshold. GC timing cannot change any value.
* Status: untested. A synthetic heap is not the engine's heap; only the live measurement counts.

### 12. Priority for the engine and the feed

* Mechanism: run the feed and the engine at above-normal process priority, the Forecast Lab and any research at
  below normal (the research scripts already use lowprio). Optionally pin the engine to cores the other trading
  systems do not use.
* Evidence: finding 3; docs/55 saw the same; memory notes 12 to 17 times slower runs under parallel load.
* This is a setting on your machine. You decide it; I have not changed anything.

### 13. Every book's time

* Mechanism: add each book's time to a per-minute counter on every step (no 2 ms floor) and log the top 10 in the
  perf minute. Shows where the 12 ms of "step:books" really goes before anyone optimises it.

### 14. Exact running sums in Flow

* Mechanism: `agg10 += new - old` instead of `ring.sum(axis=1)` (flow.py:113-114). Exact only for whole-number
  volumes, so check `np.all(v == np.floor(v))` each step and fall back to the full sum otherwise. Small saving.

### What I would not do

* Restrict the 512-row arrays to the 137 used rows. The saving is small (numpy's per-call cost dominates at this
  size) and rows that nobody reads would change, which makes the equivalence harder to argue.
* Spread the 1-Hz jobs across the ten steps of a second. It would smooth the tail, but the photograph reads most of
  those views, so photograph fields would change.

## The equivalence test (for every change above)

1. A = the committed code. B = A plus the change (a git worktree). A2 = A run a second time.
2. Replay the same tapes in all three: 27 Oct (the heaviest day), 3 Nov (an expiry Tuesday), 12 Nov (the newest).
   Use `apex.replay_batch` with its own APEX_PORT and run id, one run after another, seeded from data\.
3. `apex.replay_compare A A2` gives the noise floor: the photograph's wall-clock fields (eng_*, save_*) differ
   between any two runs.
4. Pass: `replay_compare A B` differs only where A and A2 differ. Every trade of the 107 books and the Conductor,
   every field, exact; every decisions and strikes line identical.
5. Byte tests for ideas 8 to 10 as described.

## Phase B scripts (written, not run)

| Script | What | Needs |
|---|---|---|
| D:\ApexOptions\data\research\13nov\work\R14\phaseB_bench.py | timings, now versus proposed, for ideas 2 to 5, 7 and 14, on a quiet machine (min of repeats) | after 15:30, lowprio, under 3 minutes |
| D:\ApexOptions\data\research\13nov\work\R14\phaseB_equivalence.py | prints (and with --run, executes) the A / A2 / B replays and the two compares | **your OK**: it runs replays |

Already run today (small, synthetic, no engine): `perf_agg.py`, `perf_agg2.py`, `perf_hour.py` (perf log tables),
`identity_checks.py` (identity table), `bench_core.py`, `bench_ab.py` and `iv_fast.py` (the stacked implied vol;
timings unreliable under today's load).
