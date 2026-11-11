# 37 — The 9 Nov live day, and the second-generation shadow books

9 November 2026, after the close. Two parts. Part A is the analysis of the first live day with the Conductor as
champion, across every book. Part B answers `CLAUDE_SHADOW_BOOK_HANDOFF.md` and
`docs/36_DISTINCT_SHADOW_BOOK_RESEARCH_BRIEF.md`: the novelty audit, the tape capability matrix, the first batch of
new books that was built, and what the proof package still needs.

Gross accounting throughout (owner: slippage and brokerage ignored). Nothing in this document claims a book is
profitable or that losses can be avoided; one day is one day.

---

# Part A — the live day

Monday 9 Nov was the weekly expiry (zero days to expiry), a gap of about 130 points, then a two-way range.

## A1. The champion's twelve trades

The Conductor took 12 trades, 6 wins and 6 losses, and ended at ₹159,664 (+59.7 %). Wins added ₹116,467 and losses
took ₹56,804. Without the single best trade (11:33 CE, +₹54,756) the day would have been +₹4,908 at the quantities actually traded. Recomputed all-in from the capital it would then have had, it is −₹110.50 (added 10 Nov, docs/39).

| In | Leg | Via | Return | Best while held | Exit | Note |
|---|---|---|---|---|---|---|
| 09:26:56 | 24850 CE | c20_9y | −12.5 % | +1.2 % | forward trail | bought into a falling day; never worked |
| 09:35:29 | 25000 PE | c20_9y | +6.7 % | +23 % | forward trail | gave back 16 points of 33 |
| 09:45:30 | 24850 CE | c20_9y | −9.3 % | +11.5 % | forward trail | was up 11.5 %, ended a loss |
| 09:55:09 | 25000 PE | c20_9y | −5.9 % | +7.9 % | forward trail | was up 7.9 %, ended a loss |
| 10:20:18 | 24850 CE | c20_9y | −5.6 % | +11.1 % | forward trail | was up 11.1 %, ended a loss |
| 10:26:14 | 25000 PE | c20_9t | +5.9 % | +13 % | rent trail | the only trade not from c20_9y |
| 10:38:12 | 24950 PE | c20_9y | +14.4 % | +36 % | forward trail | |
| 10:56:23 | 24850 CE | c20_9y | −14.8 % | 0 % | stop | straight to the stop |
| 11:13:21 | 24800 CE | c20_9y | +16.0 % | +40 % | forward trail | |
| 11:33:18 | 24900 CE | c20_9y | +64.8 % | +89 % | premium trail | the day's trade |
| 11:51:28 | 25050 PE | c20_9y | −9.8 % | +5.0 % | forward trail | |
| 11:57:17 | 25050 PE | c20_9y | +23.4 % | +44 % | forward trail | last trade of the day |

What the six losses have in common:

1. **Three of the six had been 8 to 11.5 % in profit** (09:45, 09:55, 10:20) and were carried back to a loss. The
   break-even lock on these books arms at +15 %, so nothing protected an 8–11 % gain. The quick-exit siblings kept all
   three green on the same entries: c20_9e closed them at +8.3 %, +1.3 %, +3.6 %, and c20_9t closed two of them at
   +4.7 % and +3.6 %. The price of that exit is the big trade: c20_9e took +17 % from the 11:33 trade that paid the
   champion +65 %. This is the known trade-off, seen again on one day; it is not evidence for changing the pool.
2. **Before 11:00 every call lost (4 of 4) and three of four puts won.** The index was 95–175 points below its first
   print all morning; the calls were bought against the day's move at the top of each bounce. After 11:13 the market
   turned and calls paid. Twelve trades cannot make this a rule; it is recorded here as a lead for the cards.
3. **Two never worked at all** (09:26, 10:56): entered, went straight down, stopped out.

The family-vote shadow rules, first test day: **both failed.** On c20_9y's own 12 trades R-019 (`agree_same >= 7`)
would have kept 5 (2 wins, −2.9 % summed) and blocked 7 (3 wins, +54.2 % summed, including the +64.8 % trade). R-020
on c20_9s (`>= 6`) made the identical split. One day, logged, not enforced; they stay in shadow.

Nothing in the 104-item photograph separates today's winners from losers better than luck: across the day's 189
distinct entries (all books), the best single field reaches |AUC − 0.5| = 0.139, and shuffled labels reach 0.114
(median) to 0.156 (max) on the same 321 fields.

## A2. The finding that matters most: the engine stood still, and the champion stopped trading at 12:05

After 12:05 the champion fired **27 more entry signals and every one lapsed** (corrected 10 Nov from 26: 36 lapses in the day, 27 after 12:05:08) ("no print within 3 s"). The tape
shows those contracts quoting every 0.7 s the whole time (25000 PE at 12:16:38–58: twenty packets). The engine was
not seeing them because it was frozen.

**Cause.** Every time any book opened, closed, armed a trail or committed an exit, the engine rewrote the whole
books file, re-serialising every closed trade of all 87 books with its ~400-field photograph. The file reached
7.7 MB by 14:43 (608 stored trades). The engine's own log shows the pause per save growing through the day:

| Half-hour from | Typical longest pause in a minute | Minutes with a pause over 3 s |
|---|---|---|
| 09:30 | 0.9 s | 0 of 25 |
| 10:00 | 1.4 s | 0 of 25 |
| 10:30 | 2.9 s | 5 of 24 |
| 11:00 | 3.4 s | 21 of 27 |
| 11:30 | 4.2 s | 27 of 28 |
| 12:00 | 6.5 s | 25 of 29 |
| 13:00–14:30 | 5.4–6.5 s | 67 of 76 |
| 15:00 (no more trades) | 0.7 s | 0 of 29 |

**Effects, all measured.**

- *Exits filled late.* An exit waits for the first print after its trigger; the trigger itself changed the saved
  state, the save froze the engine, and the fill came after the pause. Mean exit delay by hour, all books:
  0.8 s (09h), 1.9 s (10h), 3.5 s (11h), 6.0 s (12h), 5.2 s (13h), 5.6 s (14h). On the champion this moved
  12 exits by −₹3,383 in total (some better, some worse; 11:16 −₹2,795 and 12:05 −₹2,652 were the costly ones).
  On c20_8x it was −₹16,237 and on premium_momentum −₹26,137.
- *Council entries lapsed.* A council book tries its fill once a second for 3 s. With a pause over 3 s the entry
  lapses before it is tried. The champion's fill delay crept from 1.0 s (09:26) to 2.1–3.0 s (10:20–11:57) and then
  past the limit for good. Every c20_9* pool book stopped with it.
- *What was missed cannot be known exactly.* c20_8x (same family, not in the pool, which happened to get fills)
  traded on through the afternoon: +8.9, +7.3, −15.6, +40.1, −15.2, −16.8, +53.9, −20.2 % (4 wins, 4 losses).
  That is a neighbour's record, not the champion's.

**The 36 photograph items I added this morning made the file about half as large again and the pauses longer.**
The whole-file rewrite is the defect; the photograph is what made it bite on day one.

**Fixed tonight** (`apex/engine/paper.py`), in two parts:

1. A closed trade's text is serialised once and reused (`_books_chunks`). Building the whole 7.7 MB file from
   today's real books now takes about 10 ms on the engine's step; the old way took 0.4–0.75 s on this machine when
   idle and 1–6.5 s inside the live engine.
2. The disk write, fsync and replace (about 100 ms for 7.7 MB) run on a background writer (`save_books_async`,
   latest wins). The file on disk is always a whole earlier state, at most one write behind; day end and stop still
   write synchronously, and a load waits for any pending write.

Same file content as before (`tests/test_save_fast.py`, 6 tests: equality with the old dump, a field added after the
close, the open trade never cached, a failed write does not kill the writer, the step side of a 640-trade save under
0.2 s). **Not yet seen live:** the proof is tomorrow's "tick time" lines in `data/logs/engine.log` and zero
"entry lapsed" releases in the Conductor diary while the contract is quoting.

## A3. Other operational facts

- The engine was stopped by a second Ctrl+C at 15:32:53, during its final save. `data/paper/2026-11-09.json` is the
  14:43 state (the last trade of any book); the `.tmp` beside it is a torn file. The champion had no trade after
  12:05, so its record is complete. The day was **not closed and learned** (that runs at 15:41); the engine's
  start-up back-fill should pick it up, to be checked at the next start.
- The tape `data/ticks/2026-11-09.jsonl.gz` has no gzip end marker (same stop). It reads to 15:32:52.
- Five feed silences of 3–10 s paused entries (10:45, 12:35, 12:36, 14:40, 14:44). The index was distrusted for
  seconds at a time between 15:17 and 15:32 (spot up to 115 points off its usual spread).

## A4. All 87 books

23 books ended up, 60 down, 4 did not trade. 189 distinct entries across all books, 77 winners (41 %).

| Book or group | Trades | W / L | Day P&L | Note |
|---|---|---|---|---|
| premium_momentum (control) | 33 | 18 / 15 | +₹238,615 | the control beat everything; a strong two-way expiry |
| c20_8x | 19 | 9 / 10 | +₹115,843 | traded all day; two trades of +86 % and +54 % |
| c20_9e | 15 | 11 / 4 | +₹107,188 | best strike rate of the family; quick exits |
| **conductor (champion)** | 12 | 6 / 6 | +₹59,664 | stopped at 12:05 |
| c20_9t | 14 | 9 / 5 | +₹58,448 | |
| c20_9h | 12 | 5 / 7 | +₹45,776 | |
| c20_9x, 9y, 9s, 9v, 9x_r002, 9x_r004, RAW | 12 | 5 / 7 | +₹30,544 | identical today: the entry vetoes and rules changed nothing |
| spot_pb45, spot_pb45_r002 | 2 | 2 / 0 | +₹24,434 | no losing trade |
| m2.0_s0.5_d20 | 2 | 1 / 1 | +₹20,738 | |
| t28_st20 / edge_bracket_only | 5 | 2 / 3 | +₹10,371 / +₹5,788 | |
| m*_s0.6, m2.0_s0.5_trend | 1 | 1 / 0 | +₹1,138 | one small win |
| spot_orb45 and its three rule books | 0 | – | 0 | no trade |
| t28 family (20 books), lvl_trail family, spot_dual*, spot_dc12_t12* | 5 | 1 / 4 | −₹393 to −₹2,152 | one shared set of entries |
| spot_dc12_t12_first (+r002, r003) | 12–13 | 5–6 / 7 | −₹1,580 to −₹3,354 | |
| domino books (m*_s0.4/0.5, gap*) | 1–3 | 0–1 / 1–2 | −₹2,759 to −₹6,728 | |
| edge_gate_*, apex_edge, edge_breakout | 1 | 0 / 1 | −₹5,902 to −₹9,750 | |
| spot_dc12_t12_1130, t28_fwd | 4–5 | 0 / 4–5 | −₹12,876, −₹19,916 | no winner |
| spot_ft_prem10 | 17 | 8 / 9 | −₹18,284 | |
| random_entry (control) | 2 | 0 / 2 | −₹20,761 | |
| futures_only (control) | 12 | 5 / 7 | −₹31,142 | |
| straddle_spike | 13 | 4 / 9 | −₹48,188 | |
| fade_switch (+r002) | 63 | 22 / 41 | −₹76,661 | fading a 280-point two-way day |

The Conductor beat c20_9y alone (+₹59,664 against +₹30,544) on the same entries: it took c20_9t's 10:26 put (a win)
where c20_9y took a later put that hit its stop.

---

# Part B — the second-generation shadow books (docs/36)

## B1. Novelty audit (current code, not old docs)

The 86 books before tonight are 10 entry mechanisms: domino impulse, basket gap, straddle spike, premium momentum,
fade/follow switch, spot breakout, 45-min pullback, opening range, the "dual" family with its gate/exit/strike twins
(33 books), and the council's c20. No entry anywhere reads signed flow, depth, a fitted response, a path, or a
cross-stock transition; those exist only as observers (`levels.Force`, `flow.Flow`, `edge`, `apex/quant`, the ideas
board, the photograph).

| Candidate | Nearest existing code | Verdict | Why |
|---|---|---|---|
| N01 absorption / release | `levels.Force` (needs a level, never trades); fade_switch (price only) | **Distinct** | no entry reads flow or depth; no response model exists |
| N02 impact relaxation | fade_switch; `quant/micro.KyleLambda` (display) | **Distinct**, but shares N01's inputs | fade_switch has no flow-decay state. Merge with N01 if the events coincide |
| N03 sequence order | ideas i15, i02 (endpoint checks) | **Distinct**, not built | needs a trained predictor: a tape job, see B5 |
| N04 cross-strike propagation | t28_cheapK, idea i09 (strike choosers) | **Distinct** as an entry, not built | data exists (B2); model is the work |
| N05 surface migration | straddle_spike; idea i08; SVI fit (display, 60 s) | **Extension** of straddle_spike | the level part duplicates the spike; only skew/curvature rotation is new |
| N06 leadership transfer | domino synchrony, gap books, photo items 83–85 | **Extension unless** it fires while futures z is below the domino threshold | built with exactly that condition (index must be still) |
| N07 event-time cycles | `quant/hawkes` (display), docs/33 A10 | **Merge** into A10 / N01 | the tape is ~0.7-s snapshots, not trades: no true event clock |
| N08 matched episodes | `quant/passage` (parametric) | **Diagnostic**, not a book | a modelling variant of N03, per the brief's own test |

## B2. Tape capability matrix (measured on 9 Nov; 30 Oct and 6 Nov match)

15 trading days of tape (19 Oct – 9 Nov; four of them in several parts with restart gaps). 121 instruments.

| Data | Coverage | Cadence (median / p95) | Carries |
|---|---|---|---|
| Nifty future, quote | 1 | 0.79 / 1.74 s | LTP, last qty, cumulative volume, best bid/ask and sizes, OI, total buy/sell qty |
| Nifty future, depth | 1 | 1.63 / 1.84 s | 5 levels each side with order counts |
| Weekly options | 50 (ATM ±12 strikes at feed start; strikes are added, never dropped) | 0.66 / 1.04 s | full quote with OI |
| Weekly option depth | 14 (ATM ±3) | 1.62 / 1.84 s | 5 levels with order counts |
| Next-week options | 18 (ATM ±4) | 0.73 / 1.63 s | full quote, best level only |
| Heavyweights, cash | 23 (14 carry a Nifty weight; top-10 weights exact, 4 estimated) | 0.69 / 2.94 s | full quote, best level |
| Stock futures | 23 (6 with depth) | ~1.0 / 1.25 s | full quote with OI |
| Nifty spot / VIX | – | 0.10 s / 0.5 s | price only |

Limits that shape every new book:

- **No trade prints.** Snapshots with cumulative volume; one snapshot bundles several trades. Signed flow is a
  proxy: the volume step signed by the last price against the previous bid/ask. On the Nifty future 39 % of volume
  steps print at or above the prior ask, 36 % at or below the prior bid, 25 % inside. The side of individual trades
  cannot be recovered.
- **Depth is standing quantity every ~1.6 s.** Cancellations and replenishment are not observable.
- **Exchange stamps are whole seconds**; receive time is strictly increasing. Receive minus exchange is 0.9–1.2 s
  at the median.
- **IV and Greeks are not on the tape**; the engine computes them.
- **No per-strike price path is kept in memory beyond 60 s** except in the council's shared day matrix.

## B3. What was built tonight

One shared signal engine, `apex/engine/gen2.py`, stepped once per market second from the snapshot, and eight shadow
books that read it through a new entry mode (`"gen"` in `apex/config.py`; `paper.evaluate_gen`, `paper._gen_exit`).
No book reads another book's trigger. None is in the Conductor pool; the Conductor's semantics are untouched.

| Book | Signal | Mechanism | Buys |
|---|---|---|---|
| `n01_absorb` | `n01_rev` | flow pressure ≥ 2 sd for 20 s+, price responds ≤ 35 % of what the fitted response predicts, the absorbing side's depth holds; then the push gives way | against the absorbed pressure |
| `n01_release` | `n01_rel` | the same absorption, but the absorbing depth falls below 60 % and price goes 2 points through the zone | with the pressure (a separately frozen hypothesis) |
| `n01_ctl_price` | `ctl_price` | control: an 8-point 60-s move then a 3-point turn, price only | the turn |
| `n01_ctl_flow` | `ctl_flow` | control: 60-s flow imbalance ≥ 2 sd, flow only | with the flow |
| `n02_relax` | `n02_relax` | two-timescale propagator (5-s and 30-s half-lives, fitted online); transient displacement ≥ 5 points, decayed to ≤ 80 % of its peak, flow stopped, price started back, 5-min move not dominant | against the displacement |
| `n02_ctl_mr` | `ctl_mr` | control: 8-point 30-s move, 1-point turn | the fade |
| `n06_lead` | `n06_lead` | a heavyweight group leads (≥ 0.10 % in 120 s), another is against it, the index is within 10 points; then the opposer joins (≥ 0.04 % in 30 s) | the leader's direction |
| `n06_ctl_breadth` | `ctl_breadth` | control: 70 % of heavyweight weight one way in 60 s, index still | that way |

**Response model (N01).** `dF_hat = beta × flow / depth`, beta from an exponentially weighted regression (600-s
half-life) of 10-s mid change on 10-s signed flow over smoothed depth. The beta used at second t was fitted on
seconds before t. A non-positive beta switches the flow books off (the proxy explains nothing).

**State machines.** N01: neutral → candidate → confirmed → reversal *or* release → spent → (pressure below 1 sd) →
neutral; a confirmed absorption with no outcome expires after 300 s. N02: displacement episode opens at 5 points,
fires at most once, ends when the transient part falls below 1.5 points. N06: split → joined (fire) or expired
(240 s) → spent until the disagreement ends. One entry per episode in every case.

**Exits.** Each signal carries its own target and stop in futures points, a thesis stop where one exists (N01: price
beyond the absorption zone by 2 points), a model void (N02: the transient impact rebuilds past 1.2× its peak; N06:
the leader's 60-s return turns 0.05 % against the trade), and a clock (180–600 s). The observed option price is the
fill, as for every book.

**Kept apart from the older books' photograph.** The new books do not count in "books firing this step"
(`agree_same`, the factor R-019 / R-020 were frozen on) or in "the books around" an older book (items 100–101), so
those fields mean tomorrow what they meant when the rules and cards were made.

**Data hygiene.** A blackout or a hole over 5 s clears every window and every open episode; the fits are kept and
the windows refill for 300 s before any signal. 600 s of clean data before the first signal of the day.

**Parameter manifest.** Every threshold is in `gen2.P` (about 60 numbers), frozen 9 Nov **before any evaluation**
and unchanged after the pilot below. They are a priori choices, not fitted values. Model version `gen2.VERSION = 1`.

**Not saved across a restart:** the signal engine's state. After a restart it warms up again; an open position
keeps its bracket (`pos["gx"]`, saved with the book) but loses the model void until the engine is warm.

**Speed.** One update is a few fixed-length sums and a 2×2 solve, once a second. The tape pilot ran 22,384 seconds
of 9 Nov, including reading and parsing the 219 MB tape, in 23 s. Live step-time percentiles with the eight books
added have not been measured; that needs a session or a replay.

**Tests.** `tests/test_gen2.py`, 16 tests: nothing before warm-up; absorbed buying then a turn fires the reversal
once; offers pulled fires the release; normal impact is not absorption; relaxation needs decay and stopped flow, and
its rebuild void; leadership transfer and its fragment void; a gap drops every episode; truncation invariance (state
at second N is the same whether or not later seconds exist); the book mode, the bracket, the thesis stop, the
restart fallback, registration.

## B4. First look: 9 Nov tape, futures points only

A tape-reading pilot, not an engine replay: the signals on today's recorded future, each scored on the **futures**
with its own bracket. No options, no fills, no account. One day, seen once, parameters not changed afterwards.

| Signal | Signals | Wins | Sum (futures points) |
|---|---|---|---|
| n01_rev | 3 | 1 | −11.8 |
| n01_rel | 0 | – | – |
| ctl_price | 369 | 173 | +51.8 |
| ctl_flow | 39 | 20 | +49.1 |
| n02_relax | 35 | 15 | −86.0 |
| ctl_mr | 263 | 129 | −91.9 |
| n06_lead | 5 | 3 | +27.4 |
| ctl_breadth | 538 | 264 | +297.7 |

What this does and does not say:

- The machinery works on real data: the fits converge (beta 0.33 points per unit), episodes form, expire and reset.
- **N02 did not beat its control** on this day (43 % wins, the same as plain mean reversion), and the fitted fast
  coefficient was negative. On snapshot data the propagator may not be identifiable. This is the brief's own
  rejection test; one day does not settle it, but it is the first evidence and it is against the book.
- N01 is rare by construction (3 signals). It needs weeks, not a day.
- N06 fired 5 times with 3 wins. Too few to mean anything.
- The price and breadth controls fire hundreds of times as signals; as books they hold one position at a time with
  a 60-s cool-down, so they will trade far less, but they will be the busiest new books.

## B4a. The same pilot over all 15 recorded days (run 9 Nov night, owner's OK)

Same method: tape reading only, every signal scored on the **futures** with its own bracket, no options, no fills,
no account, signals not limited to one position at a time. 22 tape files (multi-part days warm up again after each
restart). Parameters unchanged. These 15 days are now discovery material for this batch: they can no longer serve
as a test.

| Signal | Signals | Wins | Sum (futures points) | Per signal | Days up / down |
|---|---|---|---|---|---|
| n01_rev | 42 | 13 (31 %) | −135.8 | −3.23 | 3 / 12 |
| n01_rel | 12 | 7 (58 %) | +28.9 | +2.41 | 4 / 4 (7 with no signal) |
| ctl_price | 3,907 | 1,765 (45 %) | −1,236.8 | −0.32 | 7 / 8 |
| ctl_flow | 429 | 209 (49 %) | +186.2 | +0.43 | 9 / 6 |
| n02_relax | 317 | 161 (51 %) | −171.2 | −0.54 | 5 / 10 |
| ctl_mr | 2,898 | 1,346 (46 %) | −2,066.3 | −0.71 | 2 / 13 |
| n06_lead | 74 | 27 (36 %) | +23.8 | +0.32 | 4 / 11 |
| ctl_breadth | 7,817 | 3,954 (51 %) | +7,585.6 | +0.97 | 15 / 0 |

Reading it, in the brief's own terms:

- **n01_absorb (reversal): against.** 31 % wins, down on 12 of 15 days, and worse than both of its controls.
  Fading absorbed pressure lost; following flow (the flow control) was mildly positive. On this evidence the
  hypothesis is wrong-signed or the snapshot proxy cannot see absorption.
- **n01_release: too few to say.** 12 signals in 15 days, 7 wins. It points the same way as the flow control
  (with the pressure), which is at least consistent.
- **n02_relax: not supported.** Slightly less bad than plain mean reversion, still negative, down on 10 of 15 days.
  The fitted fast coefficient was negative on most days: the two-timescale model is not identified on snapshots.
- **n06_lead: not supported over its control.** 36 % wins with a 20-point target and 10-point stop is about what a
  driftless walk gives (33 %).
- **The breadth control is the only consistent result**: positive on all 15 days, 51 % wins where a driftless walk
  would give 45 % with that bracket. Cautions before anyone reads it as an edge: the 7,817 signals overlap heavily
  (about 520 a day; a book holding one position takes a small fraction), the gain is about one futures point per
  signal before any option spread, and it is the old idea, heavyweights leading the index, which the domino and gap
  books already trade. It says the leadership information is real on the futures; it does not say the transition
  model in n06_lead adds anything, and so far it does not.

Status after 15 days of futures-point evidence: all four hypothesis books stay **research-interesting at most**;
none is statistically supported. They run as shadows from the next session as built, with their controls, so the
option-level record starts. No threshold is to be moved on the strength of this table.

## B5. The three ideas that were not built as books: tested on the tapes, all three rejected

Run on the night of 9 Nov after the owner's "continue". A 1-second dataset was built from all 15 days of tape
(futures quote and depth, every nearest-weekly strike's bid and ask with its quote age, the heavyweights). Protocol
fixed before the first run: **walk-forward by date** (a date is predicted only from earlier dates; the first five
dates only train, ten are tested), ridge regression, and an **executable** label: buy the at-the-money call or put
at the ask one second after the signal, sell at the bid after the horizon. Act only when the prediction is above the
99th percentile of the training predictions and above zero. Scripts and outputs:
`data/replay/batch/gen2_research_2026-11-09/`.

Base rate first: buying an at-the-money option at a random second and selling 120 s later returns **−0.21 %** on
average and is up 46 % of the time. That is the spread and the decay any signal has to beat.

**N03, sequence order** (60-s path of futures move, call and put premium moves and signed flow; horizon 120 s):

| Features | Picks | Wins | Mean | Sum | Sum without the best 5 | Days up / down |
|---|---|---|---|---|---|---|
| Endpoints only (60-s totals) | 159 | 41 % | −2.38 % | −379 % | −684 % | 3 / 7 |
| Lagged increments (linear) | 168 | 50 % | −0.87 % | −146 % | −469 % | 5 / 5 |
| Degree-2 path signature | 186 | 46 % | +2.11 % | +392 % | −358 % | 6 / 4 |
| Signature with the order shuffled | 192 | 45 % | +1.06 % | +204 % | −558 % | 4 / 6 |

The signature's positive sum is **one trade**: +593 % on the 9 Nov expiry. Its median pick is −0.44 %, its win rate
equals the base rate, its rank correlation with the outcome is 0.004, and the version with the order destroyed
caught the same trade. **Rejected:** no evidence that order carries information here. No book.

**N04, cross-strike propagation** (neighbours' delta-adjusted 2-s move minus the target's own; 292,694 rows):

| Signal | Rank correlation with the target's next 3 s | Target's catch-up in 3 s | Picks | Executable 30-s mean | Days up / down |
|---|---|---|---|---|---|
| Neighbours minus own | +0.21 | +0.90 pts | 864 | −0.92 % | 2 / 8 |
| Own 2-s momentum (control) | −0.19 | −0.85 pts | 957 | −0.74 % | 3 / 7 |
| Raw cross-strike average (control) | +0.16 | +0.71 pts | 902 | −0.95 % | 1 / 9 |

The lead is real in the mids: when the neighbours have moved and the target has not, the target's mid follows by
about 0.9 points within 3 s. **It cannot be bought.** One second later the ask has already moved, and the executable
result is worse than the base rate. This is the brief's own rejection test ("an edge that vanishes before the
current system could execute it") and what quotes refreshed every 0.66 s would produce by themselves. **Rejected**
as an entry generator. No book.

**N05, volatility-surface migration** (level, skew and curvature of a quadratic fit to out-of-the-money implied
vols within ±300 points, every 10 s; 60-s changes; horizon 120 s):

| Features | Picks | Wins | Mean | Days up / down | Same, without expiry days |
|---|---|---|---|---|---|
| Forward move only | 104 | 38 % | −1.28 % | 4 / 6 | +1.48 % (26 picks) |
| IV level momentum (control) | 166 | 45 % | +0.68 % | 5 / 3 | +0.31 % (58) |
| Premium momentum (control) | 152 | 41 % | −2.05 % | 0 / 10 | −0.20 % (114) |
| Level + skew + curvature + forward | 149 | 50 % | +0.87 % | 6 / 2 | −0.41 % (287), 2 / 4 |

The surface model is positive only with the expiry days in; without them it is negative, and it does not beat plain
IV-level momentum, which is what straddle_spike already reads. Rank correlations are zero to three decimals.
**Not supported.** No book. The one observation worth keeping for the cards: premium momentum picked this way lost
on 10 of 10 test days.

**N07** merges into N01 (its phases are the N01 state machine) and docs/33 A10. **N08** is a diagnostic for N03 and
falls with it.

What this leaves: of the eight candidates in docs/36, four are running as shadow books with controls (N01 twice,
N02, N06), three were tested and rejected before becoming books (N03, N04, N05), and two were merged or set aside
(N07, N08). On 15 days nothing in the brief has shown an edge. The one consistent signal anywhere in this work is
the oldest idea in the system: heavyweight breadth leads the index future.

## B6. Proof package (docs/36): where each item stands

| # | Item | Status |
|---|---|---|
| 1 | Freeze hypotheses, thresholds, horizons before evaluation | **Done** for the batch (`gen2.P`, 9 Nov). 9 Nov has now been seen once on futures points |
| 2 | Mechanism baseline, model version, ablation per book | Controls built and running beside each book. Ablations (N02 one-exponential, N01 without the depth test) not built |
| 3 | Wins, losses, losing days, abstentions, overlap, performance while incumbents idle | Starts with the first live session; nothing to report yet |
| 4 | Candidate alone / pool / pool + candidate / pool − member, reconciled as docs/35 | **Needs replays.** Not run |
| 5 | Mirror-Conductor track unchanged | Unchanged. No new book is in the pool |
| 6 | Executable-event simulation, pending and lapsed fills, truncation, restart equivalence | Truncation tested at the signal level. The books use the engine's own fill rule (first print, 3-s lapse). Restart equivalence does not hold for the signal state (B3) |
| 7 | Every loss kept with a pre-outcome explanation and its matched rejected winners | Every entry carries the 104-item photograph and the signal's own reason text. No veto has been added from any loss |
| 8 | Keep implementation-correct, research-interesting, supported, account-beneficial apart | Tonight's status is **implementation-correct only** |

## B7. Open decisions for the owner

1. Replays for the proof package (item 4). The futures-points pilot and the N03 / N04 / N05 tape tests are done.
2. Whether the champion should keep the c20_9y exit or move toward the quick exits, given A1 point 1. The cards
   after a few more days should decide, not today.
3. R-019 / R-020 failed their first day. They cost nothing in shadow.
