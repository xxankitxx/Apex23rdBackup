# Changelog

## 11 Nov 2026 (16:00 to 18:00, after the close) — Forecast Lab v2, the engine's hazard model, pending items (docs/50)
- **Forecast Lab v2** (`apex/forecast_lab/brain.py`, `core.py` VERSION 2): a trained layer under the online one.
  45 causal inputs; a multi-scale volatility model; fat-tailed quantiles and a stochastic-volatility mixture in the
  paths; two trained direction experts (ridge, boosted trees) beside the five online ones; implied-volatility drift
  by time of day and days to expiry and the skew slide by moneyness. New in the panel: a market-state strip, a what-if
  grid (futures move by time), "what moves my lean", options-priced against delivered against forecast movement.
- **Evidence, 11 unseen sessions:** volatility error 8 to 31 % below the 10-minute clock on 8 or 9 sessions; with
  online learning the 80 % ranges stay at 80 % and are 4 to 10 % narrower. The premium's middle forecast equals "no
  change"; profit chance scores as a coin. The 1-minute direction skill (IC +0.21) is the options and stocks leading
  the recorded futures quote, not foresight.
- **Engine:** label version 2 (a recording that ends inside the horizon is unobservable; 179 of 131,585 rows moved);
  one coherent hazard model (`apex/predict/hazard.py`, 12 chronological artefacts) replaces the eight-model
  forecaster; `registry.for_session` wired into engine start, `PREDICT_MODE=chronological` (never a model fitted on
  the session, no fallback); `ranges_v2.json`. Hazard on 11 unseen sessions: log loss 0.976 against 1.108 for base
  rates (10 of 11), side AUC 0.530; on today's live day side AUC 0.443.
- **Label parity on today's live session:** same fill 92.5 %; first event the same 99.5 % at 30 s, 96.2 % at 300 s;
  differences are knife-edge touches sampled at different instants inside a second.
- **Nightly:** `research/forecast_lab/nightly.py <day>` converts the tape, collects the day, refits the trained layer.
- **Tests:** full suite 564 passed, no failure.
- **Prepared, not yet run when this was written:** the overnight replay p43 (16 sessions, recorder on).

## 11 Nov 2026 (13:55 to 14:30) — tighter trailing and re-entry studied (docs/49); re-entry twin added
- **Giveback:** c20_9y booked 11.9 lakh of 31.5 lakh at its trades' peaks (38 %). Tighter trails (40 variants), floors
  after a gain, and buying back on a new high all lost money on the recorded trades.
- **Continuation and re-entry models** (`apex/predict/hold.py`, `research/predict/build_hold.py`): held out by day,
  selling early never helped; buying back helped only on a thin line (+12,477 on 9 decisions).
- **`rx_c20_9y`** (shadow re-entry twin, `apex/engine/holdtwin.py`, `reenter_v1.json`) added; the hold-or-sell twin
  was not, because its honest line never acts. 106 books. Effective at the next engine restart.
- **Tests:** `tests/test_hold_twins.py` (4); book-count tests updated to 106.

## 11 Nov 2026 (12:15 to 13:45, during the live session) — the Forecast Lab (docs/47, docs/48)
- **Why nothing traded today:** the account and all 13 champion-family books stayed flat ("no eligible trigger").
  Not a fault: those books buy only when movement pays for decay, and today it has not (gamma-rent ratio about 0.2
  against the 1.0 needed). 457 trades happened across the other books.
- **docs/47** (new, research): 11 topics, 88 references, a ranked plan: decay and movement clock first, a path
  engine with full repricing second, self-scoring with weighted experts third; skip big direction classifiers.
- **Forecast Lab** (`apex/forecast_lab/`, docs/48): a separate process that reads the feed's table read-only and
  writes `apex/static/live/forecast_lab.json` once a second. Futures distribution at 1 to 30 minutes from five
  experts weighted by their matured scores; option premiums by Monte Carlo repricing with time decay and the measured
  volatility trend and spot-vol beta; decay alone; break-even move; profit chance; +5 %/-5 % race; decay register on
  the trading and calendar clocks plus decay measured from the quotes; gamma rent; plain-English commentary with
  "what I would do" (advice only, needs its own record before it says buy); self-scoring of every forecast and online
  learning with a frozen morning copy. About 2 % of one core at below-normal priority; no measurable effect on the
  engine (median step 42 ms before, 39 ms after).
- **Dashboard:** the Forecast panel now sits directly under the position band (it had no grid slot and fell to the
  bottom); fan charts for the future and each option, the next-steps table, the decay register and the scoreboard.
  The old model's cards are kept in a fold for the four forecast books.
- **Engine publish change, prepared, not live:** the straddle series, ideas board and book table are encoded at most
  once a second instead of four times (`_slow_parts`, `write_state(raw=...)`). Takes effect at the next engine restart.
- **Tests:** `tests/test_forecast_lab.py` (9), one more in `tests/test_state_fastpath.py`.

## 11 Nov 2026 (08:25 to 08:35) — docs/46 review: three fixes before the open
- **Stale signal (finding 1):** the forecaster withdraws its signals in any second without a current forecast, and
  `paper.evaluate_gen` refuses a forecast-book signal whose exact contract has no current forecast.
- **Chain edge (finding 2):** a missing neighbouring strike no longer silences buyable and held contracts.
- **Publication (finding 5):** an artefact counts as published before a session only if its recorded time is before
  that session's 09:15 open.
- **Left for after the session:** finding 3 (a recording that ends inside the horizon is labelled "neither"; the fix
  is a new target version, a rebuild and a refit) and finding 4 (the registry is not wired into engine start).
- **Tests:** 3 more; full suite 543 passed, no failure, no error. Freeze re-recorded 08:3x. docs/45 section 10.

## 11 Nov 2026 (08:00 to 08:20) — forecast panel on the dashboard, display only
- **Forecast panel** (`Pred.panel`, state key `forecast`, `apex/static`): one card for the call and the put the
  engine would buy now and for each held contract: chance the premium gains 5 % first, loses 5 % first, or neither
  within 5 minutes; the likely premium range at 1 and 5 minutes in per cent and rupees; one sentence on the lean;
  the model, its cut-off and a plain warning that its percentages are rough. Built once a second, isolated by
  `_safe` in the engine and a try/catch in the page. Decides nothing.
- Checked on a stand-alone page with the real renderer, styles and forecaster output (no console errors); not seen
  inside a running engine: a simulated run was blocked by the permission system.
- **Tests:** one more in `tests/test_forecast_repairs.py`; full suite 538 passed, no failure, no error.
- **Not changed:** the 10 weather items of docs/38 still not built (111 to 119, 127). All can be recomputed from the
  recorded tape. The known slow step when many books enter at once (1.2 s once in the idle hour) is not fixed.
- **08:20, after a review of the panel, five wording faults fixed:** the headline now compares one stated event
  (the chance of gaining 5 % before losing 5 %) and no longer says "more likely to rise"; "raw entry level reached"
  replaces "strong enough for the books to act", and each forecast book's own state is shown; zero, one and two
  buyable sides are told apart; ranges are labelled as estimated 10th to 90th percentiles with their own model and
  cut-off, rupees as approximate; the hardcoded 0.54 is gone. The reviewer's two cases and three more are pinned
  (`tests/js/forecast_headline_test.js`). Full suite 540 passed.
- The panel's ranges are computed once a second inside the engine's publish, about half a millisecond a row:
  display only is not zero cost. Not measured in a running engine.
- Freeze re-recorded at 08:22; no decision code changed since 03:21.

## 11 Nov 2026 (02:00 to 03:30) — docs/44 roadmap: M0 and M1 evidence, first M2 comparison (docs/45)
- **docs/45** (new): the implementation matrix docs/44 asks for, then the evidence.
- **Life cycle:** full contract key and expiry on the signal, the pending order and the fill (`fc_sig`, a ledger
  `fill` record); held coverage by priority, cap 24, over-cap counted; the fill is the next second or none; a full
  queue evicts unfilled first with a censored record; a restart keeps signal numbers, closes a torn line and marks
  orphans once. `tests/test_forecast_lifecycle.py` (3, end to end) found and fixed one fault: a filled forecast was
  marked as an orphan after a restart. All contracts are scored in one pass a second.
- **Aligned data:** `research/predict/build_candidates.py` writes `origins_v3` (648,026 rows, 103,995 executable
  picks, no moment dropped). 52.4 % of executable picks are at the depths the old model was fitted on, 47.6 % are
  not; the gap is in moneyness. The reconstructed selector equals the engine's real choice on 98.3 % of 8,796 fills.
- **Champion episodes** (`build_episodes.py`, 92 executed trades): 49 of 89 dipped 5 % first and that group still
  made +2.3 lakh with 6 runners. "+5 % before -5 %" is the wrong target for the champion. Untraded triggers missing.
- **M2, ten unseen sessions:** no model beats an activity-only baseline on proper scores; a small direction signal
  (0.54 against 0.50, interval clear of zero); the deployed eight-model method is badly calibrated out of sample and
  is rejected as a probability model; the coherent hazard model becomes the baseline. Top-edge slice +0.22 % a
  300-s hold on 6 of 10 sessions: not a trading result.
- **Registry** validates what it hands out; **freeze log** (`research/predict/freeze.py`), frozen 03:21 on 11 Nov.
- **Ten-day replay stopped** on the owner's instruction. On its trades 111 of 111 forecast-book trades were on the
  scored contract.
- **Tests:** full suite on the idle machine, 537 passed, no failure, no error.
- **Not done:** recorder-on replay for untraded champion triggers; admission, timing and continuation models; the
  hazard model in the engine; label parity on a tape; Conductor with and without a candidate.

## 11 Nov 2026 (before the open) — forecast audit (docs/42) checked, first repairs (docs/43)
- **The audit holds.** The 15-day replay did not test the forecast: the forecast books bought another contract than
  the one scored (86 to 94 % of trades) on a line fitted to another score. docs/41 section 14.4 corrects the report:
  day counts in rupees, and "no forecast book adds to the account" is withdrawn.
- **Exact contract:** the engine names the contract it would buy on each side, the forecaster scores it, the signal
  carries it, and `paper.bound_contract` buys it or nothing. No substitution. `apex/engine/pred.py` VERSION 2.
- **One scoring function:** `Forecaster.score`. `model_v2.json` (hash `7db140939ea1`): the same weights as v1,
  lines from the deployed score. `config.PREDICT_MODEL` points to v2; v1 is kept.
- **Coverage:** held contracts are scored (up to 12); a missing forecast carries its reason.
- **Also:** in-sample flag; counters on the two twins; a quote age of zero is a fresh quote in `_gen_exit`.
- **Tests:** `tests/test_forecast_repairs.py` (9). Full suite 529 passed, no failure, no error.
- **Not done:** refit on the executable contract (the model is extrapolating to deeper strikes), champion-specific
  labels and admission model, hazards, continuation model, the six experiments, Conductor with and without a book,
  the other life-cycle items of finding G.

## 10 Nov 2026 (night) to 11 Nov (before the open) — 15-day replay, account contribution, ranges, afternoon slowdown
- **docs/41 sections 13 and 14.**
- **15-day replay** (`p41_g1` to `p41_g8`, 105 books, all 15 tapes finished 01:12 on 11 Nov). Account contribution
  (`contribution.py`): `c20_9y` is first of 106 books, 92 trades, 54 won, 38 lost, +890 %. The forecast runner twin
  never changed a trade. The forecast exit twin wins more often and earns less (139 trades, 93 won, +562 %). The
  forecast entry books beat their control (+296 % and +356 % against -130 %) but are in-sample and far below the
  champion family. S01 fails, S03 is flat. The Conductor trades only on 9 Nov in a replay (+71 %, 10 won, 12 lost).
  **No losing trade: unmet**, no book with trades has none.
- **Premium ranges in the forecast record:** `apex/predict/ranges.py`, artefact `ranges_v1.json` (hash
  `dc41cd42f5c8`), the 10, 50 and 90 % points at 60 s and 300 s on every ledger record. A record only. The volatility
  scenario in the translator was tested and overshoots; the direct model was chosen by the rule set before the run.
- **Afternoon slowdown, two causes fixed:** the per-second weather base no longer re-scans the day for the range,
  the median IV and the opening ranges (36 ms to 12 ms at the close, loaded machine); `Book.stats()` keeps its sums
  until a trade changes (7.9 ms a publish removed). Same numbers as before, pinned by
  `tests/test_weather_base_running.py`.
- **Tests:** full suite on the idle machine, 520 passed, no failure, no error.
- **Not done:** the many-books-in-one-step burst; the rest of the publish growth; missed and rejected winners for the
  forecast books; range calibration by day type; a 15-day comparison with the Conductor itself.

## 10 Nov 2026 (afternoon) — the prediction service, forecast shadow books, live priority guard, disk
- **docs/41** (new): the answer to docs/40. What was built, the evidence on 15 sessions, performance, disk, what is
  not done.
- **Prediction service** (`apex/predict/`): 33 causal features (one code path offline and live), fixed-contract
  targets with competing events and gaps, a small logistic model saved as a file, an append-only forecast ledger and
  a queue that releases an outcome only when it has finished. Frozen model `apex/predict/model_v1.json`, hash
  `88c09e8db35f`, fitted on all 15 sessions (discovery for it).
- **Evidence, each test day forecast from earlier days only:** how fast an option moves is forecast well (a 5 % move
  inside 30 s: AUC 0.85, Brier skill 17 to 20 %). Which side is forecast only slightly (0.53 against 0.50). Neither
  the weather photograph nor the forecast separates the champion's winners from its losers. The strict forecast line
  inside trading hours gave 131 trades on 10 unseen days, 75 won and 56 lost, +0.93 % a trade, positive on 10 of 10
  days; the wider line was flat. Learning during the day did not help offline.
- **Four forecast shadow books** (`apex/engine/pred.py`): `p02_clock`, `p02_top1`, `p02_ctl_mom` (control),
  `p05_adaptive`. Exit on the premium itself (+5 % / −5 % on the bid), 300 s, or the forecast leaving. **103 books.**
  The forecast is also recorded on every champion-family fill (`fc` on the position, and the ledger). It gates
  nothing.
- **Live guard:** in a live session the feed and engine run above normal priority, and the launcher lists replay,
  test and research processes at the start. On 10 Nov such jobs made the same code 12 to 17 times slower.
- **Disk:** git repacked, 142 MB to 48 MB, nothing removed. `research/archive_runs.py` (verified archiver) written,
  run in dry mode only: the old replay folders are tracked in git, so removing them is the owner's call.
- **Replay batch of 10 Nov:** stopped after the first tape of each group (19 Oct, 26 Oct, 30 Oct, 5 Nov) because at
  the measured pace it would have run through the 11 Nov live session. 11 of 15 days not replayed.
- **Not done:** no engine replay of the forecast books; step time of v5 with 103 books not measured on an idle
  machine; the many-books-in-one-step burst is not fixed; P03 and a champion twin for P04 not built.
- **Evening:** two twins of c20_9y that read the forecast for the held contract, `fx_c20_9y` (exit) and `fr_c20_9y`
  (runner); **105 books**. Four replayed days through option quotes: S01 fails (43 trades, 17 won, -68.7 %), S03 is
  flat (315 trades, 148 won, +20.2 %) but beats its control. Idle-machine profile: no single function dominates a
  step; a photograph costs about 10 ms early in the day. Premium ranges: repricing a forecast of the underlying gives
  the best tails but a range that is too narrow (74 to 75 % against 80 %). `research/run_registry.py`,
  `research/profile_replay.py`. Overnight replay of all 15 days started 17:09 in eight groups, stopped at 08:25 if
  unfinished.

## 10 Nov 2026 — operational fixes pinned by tests, photograph v5, research corrections, third shadow batch
- **docs/39** (new): the answer to docs/38. Every 9 Nov operational fault with its fix and its test, the research
  corrections, photograph v5, the S01 and S02 capability checks, the third shadow batch, and what is not done.
- **Operational fixes** (`tests/test_ops_10nov.py`, `tests/test_save_fast.py`): per-phase step accounting and a SLOW
  TICK line; the supervisor reports a pause under its 10 s limit; a second Ctrl+C is ignored while the engine saves and
  the third forces; a flat book stopped after 15:25 closes and learns the day; dated log lines; a torn `.tmp` is
  removed and logged at the next start; a failed background save is retried, each writer has its own temporary file,
  and an older state never overwrites a newer one.
- **gen2 VERSION 3** (frozen, not replayed): bracket fixed at the fill, per-input ages, model exits only when ready,
  N01 refit on the pressure window, independent price-only control `n01_ctl_price_ind`.
- **Research v2** (ask one second later, bid out, 15 dates): N03 has no edge inside the tradable window (148 picks,
  −29.2 %; every large win is an expiry day after 15:20). N04 predicts the mid but loses quote-aware. N05 never beats
  IV momentum.
- **Photograph v5:** 114 entry items (105 to 110, 120 to 122, 128 added) and a continuation photograph `weather_hold`
  on the trade (123 to 126). 13 telemetry fields are recorded but kept out of the rule search: the one exception.
  Items 111 to 119 and 127 are not built.
- **gen3 VERSION 1** (`apex/engine/gen3.py`, manifest `6fc9150866a1`): four shadow books, `s01_transmit` with controls
  `s01_ctl_cash` and `s01_ctl_sfut`, and `s03_recruit`. **99 books.** Futures-level first look only: S01 does not beat
  its cash control; S03 is positive on 15 of 15 days at the mid and still loses 1,031 of 2,186. No option-quote
  result yet. S02, S04, S05, S06 not built.
- **Corrections to 9 Nov:** 27 lapses after 12:05, not 26. Without the best trade the day is +₹4,908 at traded
  quantities and −₹110.50 recomputed all-in.
- **Not done:** no engine replay of gen2 VERSION 3 or gen3; step time with v5 and 99 books not measured in an engine
  run; nothing has run live with these changes.

## 9 Nov 2026 (after the close) — the live day analysed, the save freeze fixed, eight second-generation shadow books
- **docs/37** (new): Part A the 9 Nov live day across all 87 books; Part B the answer to docs/36 (novelty audit, tape
  capability matrix, the first batch, the proof-package status).
- **The day:** Conductor 12 trades, 6 wins / 6 losses, +59.7 %; without its best trade +4.9 %. Three of the six losses
  had been 8-11.5 % in profit. R-019 / R-020 (family vote, shadow) failed their first day: kept 5 trades (2 wins),
  blocked 7 (3 wins, including the +64.8 % one).
- **Defect found and fixed: the engine froze on every books save.** `paper.save_books` re-serialised every closed trade
  of every book with its ~400-field photograph on every entry, exit, armed trail and committed exit; the file was
  7.7 MB by 14:43 and the pause grew from 0.9 s (09:30) to 6.5 s (noon). Exits filled 3-6 s late from 11:00, and
  every council entry lapsed (3-s fill window) after 12:05: the champion fired 27 more signals and took none (corrected 10 Nov from 26).
  The 36 photograph items added that morning made the file about half as large again. **Fix:** a closed trade is
  serialised once and its text reused (`paper._books_chunks`: about 10 ms on the step for today's 7.7 MB, was
  0.4-0.75 s idle and up to 6.5 s live), and the disk write runs on a background writer (`paper.save_books_async`,
  latest wins; day end and stop stay synchronous; `load_books` waits for a pending write). Same file content.
  `tests/test_save_fast.py`. Not yet seen live: check the "tick time" log lines after the next session.
- **`apex/engine/gen2.py` (new), entry mode `"gen"`:** eight shadow books that read their own signals, never another
  book's trigger. `n01_absorb` / `n01_release` (flow pressure the price does not respond to, against a fitted response
  model; then the turn, or the absorbing depth giving way), `n02_relax` (two-timescale impact propagator; trade the
  decay once flow stops), `n06_lead` (a heavyweight group leads, another opposes, the index is still; the opposer
  joins), and one control each: `n01_ctl_price`, `n01_ctl_flow`, `n02_ctl_mr`, `n06_ctl_breadth`. Thresholds in
  `gen2.P`, frozen 9 Nov before any evaluation. Shadow only; not in the pool; the Conductor is unchanged. 94 books.
- **Kept apart from the older books' photograph:** the new books do not count in "books firing this step"
  (`agree_same`, on which R-019 / R-020 were frozen) or in "the books around" an older book (items 100-101).
- **First look (tape pilot, futures points, 9 Nov only, not a replay):** n01_rev 3 signals 1 win; n02_relax 35
  signals 15 wins, no better than its control; n06_lead 5 signals 3 wins. Implementation-correct only; nothing is
  shown about profit. Replays for the proof package have not been run (owner's rule: ask first).
- **Same pilot over all 15 recorded days (owner's OK, 9 Nov night; docs/37 B4a):** n01_rev 42 signals, 31 % wins,
  -136 pts (against); n01_rel 12 signals, +29; n02_relax 317, -171 (not supported); n06_lead 74, +24 (no better than
  a driftless walk). The breadth-only control was positive on 15 of 15 days (+0.97 pt per overlapping signal). No
  hypothesis book is supported; no threshold was moved.
- **N03 / N04 / N05 tested on the tapes and rejected before becoming books (docs/37 B5; walk-forward by date,
  executable labels; `data/replay/batch/gen2_research_2026-11-09/`):** the path-signature model's whole gain is one
  +593 % expiry trade and the order-shuffled version caught it too; the cross-strike lead is real in the mids
  (+0.9 pt in 3 s) but gone by the next ask (-0.92 % executable); the surface model is negative without expiry days
  and no better than IV momentum. N07 merges into N01; N08 falls with N03.
- **Tests:** `tests/test_gen2.py` (17), `tests/test_save_fast.py` (6); the two tests that pin the book count now say 94. Full suite: 445 passed, 8 skipped.

## 9 Nov 2026 (pre-open, 08:35 IST) — weather photograph version 4: 36 more items (69–104)
- **Owner:** "67-68 items that you are capturing are not enough to identify a bad trade from a good trade. So add some
  more from now on ... at least 30-40 more different kind of items."
- **`apex/engine/weather4.py` (new), photo `VERSION = 4`:** docs/27 items 69–104, about 140 more fields, in six new
  groups: L the tape's structure (yesterday's shape, pivots, strike grid, bars, runs, window positions, oscillators,
  moving averages, compression, the day's net move, persistence, the adverse path), M across markets (Bank Nifty
  divergence, the VIX path, breadth at 1 and 15 min, dispersion and concentration, the leaders), N the option and the
  chain (moneyness, gearing, implied move used, the opposite leg, the premium's own path, entry liquidity, the IV path,
  the wings, own-strike OI, futures OI build-up), O flow through time (volume acceleration, up-volume share, VWAP
  stretch, call/put tilt), P the books around this one (other books' positions with the family's busy / free count,
  other books' results today, trigger density), Q this book's day (re-entry context, the day's P&L shape).
- **Observer only, no look-ahead:** no book reads it; every history read is at or before the trigger second; the
  direction-free part is computed only when a photograph is taken (about 10 ms, once per market second). A failing
  block is named in `v4_error` and never stops an entry.
- **`search.ITEMS` has 104 items;** `weather.static_check` refuses to start the engine on anything else. The engine
  passes the histories and the books to the photograph (`ctx["_wx"]`, `ctx["_books"]`).
- **Not in the recorded days:** photographs before 9 Nov are version 3. The 14 replayed days carry the new items only
  after a re-replay (not run).
- **Tests:** `tests/test_weather_v4.py` (leak test, definitions, the books' block, a broken block, the real engine rig).

## 9 Nov 2026 (pre-open, 05:20 IST) — the pool is applied; the Conductor is the champion
- **Owner ("Yes, apply pool"):** `apex/rules/pool.json` holds the c20 family unrestricted from 9 Nov: c20_9y, c20_9s,
  c20_9v, c20_9x, c20_9t (standing low; same-tick priority by the 14-day card's mean return per trade, in-sample).
  No factor lines: the 10-agent rule team (59 books, 871 rules, `data/replay/batch/v3_cards_2026-11-08/team/`) found
  none that survives the shuffle test and the held-out days.
- **`config.CHAMPION_OWNER = ("conductor", "2026-11-09")`.** `CHAMPION_DEFAULT` stays c20_9x (RAW's base, and the
  fallback if the learning state names an unknown book).
- **Shadow rules R-019 / R-020 (register, frozen before the open, NOT in the pool):** the family vote,
  `agree_same >= 7` on c20_9y and `>= 6` on c20_9s. On the 14 replayed days every c20_9y trade taken while one earlier
  council sibling stayed silent lost (12 of 12). Pre-registered and judged on live days only.
- **Tests:** the suite runs on a plain champion (`conftest._plain_champion`); tests marked `owner_champion` check the
  shipped value. New: the engine starts with the Conductor as champion, loads this pool, and mirrors a pool book's
  fill and exit through its own step.

## 8 Nov 2026 (evening) — the Conductor's account
- **Owner's decision:** the Conductor runs live on paper from Mon 9 Nov on the pairs the 14-day all-item cards
  support; every other book in shadow; no proof period as a gate; the pool is improved every evening. "No losing
  trade" is the aim the rules serve. Every weather item must be captured live.
- **`apex/engine/conductor.py`:** one account, one position, all-in; the pool (`apex/rules/pool.json`, add-only,
  dated, read as of the day) holds book-plus-rule pairs; the first pool book whose trigger passes its rule owns the
  account; the owner's own fill and exit are the Conductor's; same-tick priority (standing, test-day return per
  trade, book order); every trigger it could not take is logged with why (`paper/conductor_<day>.jsonl`); a lapsed
  owner releases the account. `engine_main` runs it after every pool book; as champion it is "the" account (RAW
  stays c20_9x's ungated twin via `raw_of`); the dashboard describes it and its pool.
- **`apex/engine/rules.py`:** register-stated factor rules (`factor op line`, the cards' form) checked straight from
  the register; an unknown rule id never trades.
- **`apex/conductor/account_sim.py`:** the same account offline from a run's saved trades (the oracle for the engine
  path, `tests/test_conductor.py`); **`apex/conductor/pool_builder.py`:** each book's card to proposed rules and pool
  pairs for the owner to admit (`--apply` freezes them).
- **docs/34 audit, same evening:** F01 fixed (a released owner frees the account on the same step; competing
  triggers of that step are admitted; regression test); F03 (pool rows take an optional `to` date, latest row per
  pair is its state as of the day); F05 (SciPy in `requirements.txt`; a failed QuantView import now refuses to start
  the engine with the reason instead of silently emptying the model items); F02 noted (quant parameters fitted 5 Nov
  on sessions through 4 Nov are used on October replays — pairs proposed on HMM / Hawkes factors are flagged, dated
  artifacts are a docs/33 Wave 1 item); F08 deferred by the owner; F09 closed by the owner (deliberate). Second pass: an expired latest pool row retires
  the pair instead of reviving an older row; HMM / Hawkes lines are excluded before the best line is chosen
  (`--allow-fitted` to admit, flagged); a vanished source position is an integrity fault that keeps the account open
  until a fresh quote, then a flagged recovery adjustment that scoring ignores (F04); pool entries state the basis of
  their priority figure (`ret_basis`).
- **Capture guard (owner):** `weather.static_check` refuses to start the engine unless the photograph defines all
  68 items and 200+ fields; the first photograph of the day is counted and logged (`weather.check_photo`).

## 8 Nov 2026 — weather photograph v3: every docs/27 item, every book
- **Owner's correction:** the 7–8 Nov search had reduced "weather" to 22 of the 68 docs/27 items and one book per
  family. Withdrawn. Every item is weather; nothing is set aside without the owner (docs/28 §11 rewritten, docs/27
  build status rewritten).
- **`apex/engine/weather.py` v3:** the remaining 37 items in the photo (about 230 fields): range / rv / volume vs
  earlier days at the same clock, reversals, choppiness, VWAP side and its age, the forward's moves and
  acceleration, basis and its changes, the Nifty futures book (resting rupees, next round level, refill / withdrawal
  classes, aggressive flow, volume surge, absorption, Kyle's lambda, spread), the heavyweights' books and volume, who
  moved first, Fin Nifty, OI change by strike over 5 / 15 / 30 min and since the open, PCR change, max pain, the
  gamma map, call / put activity, skew and term changes, the smile residual, vega and the higher Greeks, the
  option's IV / premium / volume history, premium response, the option's book and own levels, race odds, the
  forward's Kalman / jump / CUSUM state, the hidden regime, Hawkes on the chosen contract, regime and episode labels,
  every advisor's verdict, level force, the trigger, agreement across books, feed health. Per-second feeds in
  `engine_main._weather_feed3`; `oi_hist` 30 min; the option history always on (+ ttq); `quantview` Hawkes per hero
  and Kyle's lambda; `domino.episode_view` first_t / fut_cross_t; `paper.request_entry` counts fires.
- **`apex/conductor/clock_norms.py`:** the earlier-days norms from the tapes (14 processes, ~5 min); seeded into
  replays; a day reads only days before it.
- **`apex/conductor/book_cards.py`:** each BOOK's card over every field; `search.ITEMS` maps every field to its
  docs/27 item (test enforced); the family search no longer filters fields.

## 7 Nov 2026 (night) — rule scoring
- **`apex/conductor/score.py`**: each frozen rule's restricted book against its free book on test days only.
  Windows per docs/28 §6 (30 trades or 15 trading days, whichever later; the second the same again; never extended);
  the seven tests per §2 (strike rate and return against the 95th percentile of random same-size sets of the free
  book's trades, a day-level draw for day-type rules; positive with and without the best trade / day; ahead without
  them; two-thirds of the free book's top-10 % wins taken within 60 s on the same side; worst day no worse; two
  windows); verdicts; after a pass the two e-values on the daily differences (switch-off at 20). Evidence hygiene
  as in the learning loop. `--record` writes status changes.
- **Register near-duplicates per docs/28 §6:** a line within 20 % of the factor's range of a failed rule, in either
  direction, is blocked for 20 trading days (was 10 % of the line, for ever).
- First run on a copy of the live records: no window complete yet; R-001 completes its first window after 10 Nov.
- Tests: test_score.py (6); test_conductor.py updated. Suite: 405 passed, 0 failed.

## 7 Nov 2026 (night, last) — Conductor stage 5 begins: the restricted books
- **`apex/engine/rules.py`**: the frozen rules R-002 to R-005 as code, numbers exactly as registered (efficiency 0.35
  in our direction, breadth 60 %, council normal days before 12:00, ORB before 14:30), read on the weather
  photograph at the entry, only for the entry patterns in the rule's family. A book with `rules=(...)` refuses an
  entry the rule fails; the setup is skipped like every other entry veto. Same check in the council adapter and in
  the missed-signal recorder's council twins. An unknown rule id refuses every entry (never trade unchecked).
- **spot_pb45_r003 switched off** (owner, 8 Nov): the 14-day replay showed R-003's breadth >= 60 % is never met at a
  pullback entry (0 of 57; max 57 %), so the book could never trade. Removed from `config.RESTRICTED`; status
  line `R-003/spot_pb45 off` in apex/rules/status.jsonl (register untouched; `record_status` accepts a
  rule/book id). 85 books + RAW; pinned counts 86 -> 85.
- **15 restricted shadow books** (owner's go-ahead): each representative + one rule, `config.RESTRICTED`, named
  `<rep>_r00N`; they trade beside their free books from Mon 9 Nov. 86 books in all (+ RAW). No existing book
  changes.
- Tests: test_restricted_books.py (the code matches the register, each rule's scope, the veto clears the setup on
  the real entry path); pinned book counts 71 -> 86. Suite: 399 passed, 0 failed. A real engine with all 87 books
  stepped with no fault, both restricted council books with their own adapters.

## 7 Nov 2026 (night, later) — Conductor stage 3: diaries, search, weather cards, register code
- **`apex/conductor/diary.py`**: one row per trigger from paper/<day>.json and missed_<day>.jsonl: family (entry
  pattern x day type, per row), the weather photograph, the outcome, win / loss labels. A loser "never worked" when
  its best point stayed under max(one-third of its family's median winning peak, the book's own stop distance =
  the median points of its stop-outs), else it "gave it back". Counterfactuals weigh 0.5 when they overlap the real
  trade, 1 when not. Exclusions kept with their reason: quote defects and defect windows, closing-auction entries,
  counterfactuals with no outcome. `python -m apex.conductor.diary DATA_DIR`.
- **`apex/conductor/search.py`**: per family, on its representative (the least-gated member), every weather number
  and line; a line goes on the card only with >= 15 trades each side (>= 5 days for whole-day facts), more wins AND
  more return on the kept side, the same with the line moved a step, two-thirds of the big wins kept, and a lift
  above the 95th percentile of the best line found on shuffled outcomes. cards.json + cards.md, every line marked
  "found by searching the past". About 24 s per family.
- **`apex/conductor/register.py`**: propose a rule from a card line (frozen today, tested from the next trading
  day), refuse duplicates and near-duplicates of failed rules (within 10 %), append-only register, statuses in
  `apex/rules/status.jsonl`, test days, the register's own luck line.
- Missed rows now carry `ep_type` / `cf_why`.
- Smoke check on the live paper records (read only; no weather photo on them yet): 5,557 rows, 32 families, 382
  excluded with reasons; of the labelled losers 2,563 never worked and 295 gave it back.
- Tests: test_conductor.py (7). Suite: 392 passed, 0 failed.

## 7 Nov 2026 (later still) — stage 2, version 2 of the weather photograph
- **About 40 more factors from docs/27**, all from data the engine already has, in the trade's direction where it
  matters: day before expiry, first session after a break, event day, hours to expiry, minutes to the flatten,
  phase bucket; the opening gap and whether it filled; position in the 15 / 30-min opening range; 30-min efficiency;
  new session highs and lows so far; distance from VWAP; distance to yesterday's high / low / close; age of today's
  extremes; spot moves over 5 s to 5 min and the 15-s acceleration; the 45-min impulse's size, side, age and
  pullback depth; room to the 30-min swing high / low; realised vol over 1 / 5 / 15 min; the heavyweights' weighted
  move in Nifty points (10 / 30 / 60 s; banks, IT, energy, others over 60 s); the basket gap; Bank Nifty against
  Nifty; ATM skew and this-week-vs-next-week IV; the contract's premium, spread %, quote age, delta, gamma, theta
  per minute and as % of premium, the 15-min theta breakeven; VIX over 5 and 30 min; the book's own day (time since
  its last exit, won or lost, same side, trades and return so far, streak); data quality (feed ages, gaps today).
- docs/27 has a build-status table: what is in the photograph, what is already on every trade elsewhere (the edge
  and signal photos, the advisors), and what needs data the engine does not keep yet.
- Cost: about 1 ms once a second. The leak test covers every new value (the whole per-second base is compared).
- Tests: test_weather.py (10). Two wall-clock performance tests in the commentary suites are marked
  timing-sensitive: they fail at random on this machine with or without any change. Suite: 386 passed, 0 failed.

## 7 Nov 2026 (late) — Conductor stage 2: the weather photograph (the eight factors)
- **`apex/engine/weather.py`** (an observer: no book reads it). At every entry trigger (`paper.request_entry`, used by
  paper books, council books and the missed-signal counterfactuals) the pending entry gets `weather_trig`, copied to
  the position and so into `paper/<day>.json`; missed rows carry it as `weather` (`snapshot_id` = the episode id).
  The eight: calendar (mins_open, phase, weekday, dte, expiry_day); efficiency (er60 / dir60 exactly as R-002
  defines them, er_day); range (pos_in_range, pos_dir, give, range_on, dist_hi / dist_lo, or_pos, or_late); breadth
  (breadth_dir exactly as R-003 defines it); OI wall (wall_room in the trade's direction); straddle (chg5, excess,
  expanding, state); theta breakeven (|theta_min| / |delta| in spot pts per minute, against speed15, the mean 1-min
  spot move over 15 min); VIX (level, change since the day's first reading, 15-min change). Missing data is None,
  never 0.
- **No look-ahead by construction:** every history is stamped with its arrival time (the engine's virtual clock; VIX
  by its own `vix_ns`) and every function reads only samples at or before the asked time. The leak test feeds the
  same day to two points in time and checks that the photo at the earlier one is identical, and that wild prints
  after it change nothing.
- **Live-only note:** the histories start empty at a restart, so er60 / breadth / speed15 are undefined until enough
  data has arrived again (an hour for er60). A replay starts at the open and has them.
- Tests: test_weather.py (leak test, definitions, hook, the real engine); test_missed.py row fields. Suite: 385
  passed, 0 failed.

## 7 Nov 2026 (night) — rules frozen, spec reconciled, test suite green
- **Rule register** (`apex/rules/register.json`, docs/31): the five hand-written rules frozen today with exact
  formulas (ER60, BREADTH_DIR), numbers, families, restricted and free books; test days from Mon 9 Nov. R-001
  (expiry retests end 11:30) keeps its original 21 Oct date. The existing restricted-vs-free pairs are seeded at their
  original dates (R-006 to R-018). R-005 (no entry after 14:30 for families whose median hold > 15 min) holds ORB
  only on the live record. `tests/test_rule_register.py` pins every frozen rule: an edit fails the suite.
- **docs/28 reconciled:** switch-off is the two-sided e-value (`e_value_mean_le0` on the daily differences and on their
  negation, off at 20), no 40-day window; returns, not rupees, in the luck margin and the worked example;
  representatives are the least-gated members everywhere (§3, §5, glossary); spot_ft_prem10 under first-touch;
  test numbers in §14 (tests 3–4, 5b); determinism is checked at the Conductor build; the glossary's "never worked"
  matches §4.
- **Test suite green:** 377 passed, 0 failed (8 gateway tests skipped: `httpx2` not installed; 3 expected failures
  with reasons). Root cause of most old failures: suites switched `config.FILL_NEXT_PRINT` / `REPLAY_LOCKSTEP` off at
  import, so the last file imported decided the value for all; conftest now gives each test file its own value.
  Stale counts updated (71 books); the defects test uses its own paper folder; no engine change.

## 7 Nov 2026 (evening) — stakeholder code review round 2: replay fidelity
- **`apex/replay_compare.py`**: two run folders, per day: books / trades / fields exact, tapes line by line (#cf
  lines out; DATA lines optional), recorder errors fail the day; one verdict per day, non-zero exit on a difference.
- **Batch driver:** every restarted-feed part of a tape is listed and hashed; the tape's own meta record; `--seed`
  also copies `day_levels.json`, `strike_levels.json` and `defects.json` (hashed in the manifest); per day what the
  engine actually ran with (default book, gates, gate: books); Python, numpy and platform; a hash of every config
  constant (`feed_core.config_hash_full`; the old `config_hash` stays for old tapes); each child's output in
  `tape_XX.out`; refuses to run without `config.LEARN_DECIDE`; a stopped run is marked "aborted"; git checked once.
- **Quarantine windows per cluster** of quote-defect trades (30 min gap), not one window per day; a session-long
  automatic window removes the day like a declared one. Evidence only; no trading decision changes.
- **Opening range after a late start:** a first trusted print more than 10 min after 09:15 (a cold restart) leaves
  the range unknown: no OR levels, no ORB trade that day. Normal days and replays unchanged.
- **Day state view:** `give` (share of the leg given back), `pos_in_range`, `or_late`, for the factor search.
- **Feed:** a WARNING when the in-order dispatch (D-106) cannot be installed, and a `feed_sync` flag shown on the
  dashboard's data-health line ("FEED SLOW MODE"); a reconnect no longer reports the installed hook as a failure;
  `python-engineio` added to requirements.
- **Comments:** the seqlock's single-writer and x86 assumptions and who writes each control field; snapshot cost;
  the older-packet rule in `apply_packet`; depth segment routing; the mid-day table zeroing; recenter under the GIL;
  the fired-id ranges per family; domino state kept by position.
- Tests: test_review2_7nov.py, test_replay_batch.py; test_c10_daystate.py feeds at 09:15. Suite: no new failures.

## 7 Nov 2026 (later) — stakeholder rounds 4–5: record-only learning, run manifest, review fixes
- **The learning loop is record-only** (`config.LEARN_DECIDE = False`, owner): its nightly report still says what it
  would have done, but it never changes the default book, retires a book, or adds/removes a gate or candidate book.
  The deciding code stays (its tests switch it on).
- **Photograph at the trigger:** `signal_trig` / `edge_trig` stored at the entry request and copied to the position.
- **Per-day reset** of the edge observers' EWMA / OFI state and the frozen-contract check at the start of each day.
- **DATA events on market time:** the frozen hero-contract line is written from the engine step once per market
  second, not from the wall-clock dashboard publish, so a replay's events tape is reproducible.
- **`apex/replay_batch.py`** (not run yet; replays wait for the Conductor build): one fresh folder per batch run, a
  `manifest.json` (tapes and hashes, commit, code hash, switches, starting learning state, book order, per-tape
  trades, recorder rows / errors / faults, wall time), private shared memory, no dashboard.
  `replay_fast --gateway` refuses to start while a live session holds the default names.
- **Recorder:** council strength from the strategy's own `_buy_v`; an assert that no council book reaches the paper
  twin path; `replay_fast.run()` sets the fast path itself.
- **Small fixes and comments:** the guard's bad-print test is a flag, not a text prefix; the c20_9x `gbw` undo also
  restores the last-exit mark (a no-op today; `gbw` is not in the live combination); comments on `_SER` (offline
  only), the 150-pt parity reset, the 252 × 22,500 annualisation and the two order-book imbalance inputs.
- **Docs:** docs/28 §16a (owner's decisions, per-row families, the seeded register, diaries, manifest, e-value
  monitor, reuse list); docs/29 C6, C16, 4.1 and the breakout-window note; docs/30 F9 (five books) and F10.
- Tests: test_replay_batch.py, test_review_7nov.py, test_missed.py additions. Suite: no new failures.

## 7 Nov 2026 — book guide; filler bug fixed
- **docs/30_BOOK_GUIDE.md**: how every one of the 72 books trades (entries, strikes, holds, exits in code order, live
  figures), read from the code with file:line references, and the issues found while writing it (Part F).
- **Fixed: the t28 retest filler traded past the pullback book's 14:45 entry end** (t28_fill, t28_all, t28_core_fill,
  t28_d46_fill). It fired on any "no" from the pullback rule, including "too late", range mode and the data-gap block,
  and entered after 14:45 and even after the 15:00 book flatten (closed a second later): 41 trades, −₹43,293 live
  29 Oct – 6 Nov. The filler now fires only when the pullback has no setup (`paper._pullback_closed`). Shadow books
  only; the live system was never affected. Tests: test_c13_team.py.
- **Owner's decisions (7 Nov):** entries until **15:15**, flatten **15:25** (the 19 Oct closing-auction test values
  15:29 / 15:35 retired; `CAS_TEST` off); the council's own clock exit ("COUNCIL TIME") fills at once like the forced
  flat; straddle_spike and premium_momentum respect |delta| ≥ 0.52 (`config.MIN_ABS_DELTA`); controls never enter
  the Conductor pool; families are entry pattern × day type.
- **Fixed:** a fill that `open_trade` rejects (unaffordable) no longer leaves the trigger's direction in the book.
- **`worst_pts`** is tracked on every position (paper and council), for the diaries' loss labels.
- **Missed-signal recorder, round 3** (docs/29): error and fault counts with a daily summary; straddle-spike consume;
  fire_count in seconds; relation while pending; council strength; stable setup identities; new row fields; a
  counterfactual can never write the shared LiveDay or the engine log. LiveDay warns when its columns are full.
- **docs/28 version 3:** the stakeholder's corrections: absolute-profit test, returns not rupees, Conductor-level
  sign-flip margin and window, day-level null, per-family "never worked" threshold, families by entry × day type,
  explicit phase coverage, priority before book order, leak test by arrival time, and all replays at the Conductor
  build (owner).

## 5 Nov 2026 — the reviews' quant layer (display only), speed, two bug fixes
- **apex/quant/** (reviews/ teardown, DeepSeek x2): Black-76 to third order and full repricing, a premium-outcome
  (two-barrier first-passage) model, Hawkes intensity with exact and binned MLE, a Gaussian HMM with a semi-Markov
  duration layer, bipower jump test / CUSUM / Kyle lambda / Kalman velocity, quasi-explicit SVI. 32 tests.
- **Tested as yes/no rules on c20_9y** (kit, 12 days, models fitted leave-one-day-out): none adds profit; the
  premium race's probabilities are uncalibrated (predicted 1 % -> 17 % actual, 98 % -> 23 %); as an entry engine it
  trades ~50 times a day and loses. No new book; c20_9x champion, c20_9y shadow. docs/24_REVIEWS_QUANT_LAYER_5NOV.md.
- **Dashboard**: a "Quant evidence" block (premium race for the ATM call and put, Hawkes flow, jump and drift-change
  alarms, regime posterior with minutes left, third-order Greeks, smile residuals), from apex/engine/quantview.py
  once per second inside the fault guard. Parameters in apex/quant/params.json.
- **Speed, no decision changed** (72 of 72 books trade-for-trade identical on the 4 Nov 09:15-10:30 replay; 20.6 vs
  23.7 ms per step): publish serialises without the recursive NaN scrub unless the output holds NaN/Infinity
  (StateBlob.write_state, byte-identical); the kill-switch file is stat'ed at most twice a second; all council books
  share one LiveDay.
- **Fixes**: c20_9y faulted on its first live second (LiveDay had no i_at); a numpy array holding NaN crashed the
  state write.

## 4 Nov 2026 (night) — twenty-member panel C12; c20_9y shadow
- Twenty members, one mathematical angle each (gamma-theta breakeven, Kalman, variance ratio, CUSUM, SPRT, σ-trail,
  Taylor premium model, vanna, charm, OFI, GEX walls, re-entry, ...), red team on the best six, synthesis
  (docs/23_TWENTY_MEMBER_PANEL_4NOV.md). Every exit idea failed (cuts the runners). Two entry vetoes survived:
  IV_RICH (ATM IV > 3.5 vol pts over its median since 09:20) and OI_WALL (normal days, max-OI resisting strike
  <= 25 pts ahead). Kit, 12 days: +12.32 L vs c20_9x +11.24 L; losers 36 -> 28; no winner lost. Registered as
  shadow c20_9y; c20_9x stays champion. tests/test_c20_9y.py.

## 3 Nov 2026 (night) — stuck-trade panel; c20_9s shadow
- Ten-member panel on trades held 10+ min that never perform (docs/22_STUCK_TRADES_PANEL_3NOV.md). Six exit/entry
  rules failed (cliffs or losses); the stale-impulse pullback veto passed: on normal days refuse a pullback whose
  breakout is > 660 s old. Kit, 11 days: +12.26 L vs c20_9x +11.50 L; stuck trades 15 / -77.8k -> 10 / -31.3k;
  expiry days unchanged. Registered as shadow c20_9s; c20_9x stays champion. tests/test_c20_9s.py.

## 3 Nov 2026 (evening) — expiry trail tested, not promoted
- Shadow council books c20_9e (expiry give-back trail: arm +5 pts, give 6 pts) and c20_9h (half-of-peak floor from
  +15 % on expiry days). Replayed on 19 Oct, 27 Oct, 3 Nov: c20_9x +5.17 L, c20_9e +1.10 L, c20_9h +0.21 L
  (docs/21 §8). c20_9x stays champion. Dashboard names EXP_TRAIL / HALF_LOCK exits; tests/test_c20_9e.py.

## Unreleased — 3 Nov 2026 (dashboard: a council position shows its real exit rules)

- **Why.** The ten-member live-vs-tape review (docs/21_LIVE_VS_TAPE_3NOV.md) found the band showing the t28 books'
  12-pt spot trail and +18 % profit lock for the c20_9x champion, which inherits those parameters but never runs
  them: "Stop not set yet" and "LOCK ARMS AT +18 %" all day, an exit chip that only said "COUNCIL", and 158
  commentary lines of "[giveback: TypeError]" (the give-back warning formatted a None stop distance).
- **The council adapter publishes the strategy's own rules** in `pos["rules"]` every second it holds: the −15 %
  premium stop level, the forward trail (best smoothed forward since entry, the trail size, the exit level, the
  give-back so far), the hold clock (15 min expiry / 90 min normal) and time left, the premium floor that is armed
  (break-even / give-back / ramp / rent) or the peak gain that arms the next one, and the +70 % premium trail once it
  is on. Display only; nothing feeds a decision (`apex/engine/council/__init__.py` `Adapter._rules`).
- **The publish** no longer sends `on_spot` / `d_star` / `lock_pct` / `lock_trail_pct` for a council book, and
  `time_exit` is the council's own flat time (15:00 expiry, 15:20 otherwise).
- **The band**: a council rail in forward points ("FWD PTS TO TRAIL", forward / best / trail size / % left, NEAR
  TRAIL at a quarter of the trail), the floor row ("FLOOR ARMS AT +15 %" with the peak bid, or "BE LOCK 100.00 ·
  at break-even"), the stop and the clock on one line; once the premium trail arms the rail switches to the bid.
  The exit chip and the trades table read the council code ("BE_LOCK" → "Break-even floor (peaked +15 %, sold at
  entry)", "SL" → "Premium stop −15 %", "TIME" → "Hold clock ran out", …), the trigger panel explains "COUNCIL EXP
  brk v=+21", and the lead-book sentence describes the council rules instead of the spot range.
- **Commentary**: the give-back warning takes its guard sentence from the rules when there is no spot stop
  (`commentary.guard_text`); the hold commentary's trail size is the council's forward trail.
- **Records**: the exit's wait is `exit_fill_delay_s` (a new CSV column); `fill_delay_s` stays the entry's. The
  engine logs its tick time (p50 / p95 / max) once a minute whenever a tick in that minute took over 300 ms.
- Not changed: any trading rule. Tests: `tests/test_council_view.py`.

## Unreleased — 2 Nov 2026 (fix: the Best tile could fall during a live trade)

- **Best never falls now.** The engine records its peak from one print a second, but the tile also took the
  current tick, so a tick high between engine samples showed as Best and then vanished on the next tick. The tile
  now keeps the highest value it has seen for the trade (engine peak, profit-lock best, or a fresh tick).
- **The premium chart's "best" label reads the same value.** It used to read only the browser's own buffer, which
  dropped its oldest points after about 12 minutes (so a long trade lost its peak) and starts empty on a reload.
  The buffer now thins its older half instead of dropping it, always keeping its highest point.
- View only: the engine, its peak and the trade records are unchanged. A page reload during a trade restarts the
  tile from the engine's own peak. Tests: `tests/test_best_tile.py`.

## Unreleased — 2 Nov 2026 (dashboard redesign: "night instrument panel")

- **Whole dashboard restyled by a ten-member design team** (director, eight section designers, integrator). Deep
  layered glass surfaces, 1 px hairlines, luminous tabular Chakra Petch numerals; glow only where it means
  something (green calls, coral puts, gold trigger). Design system recorded in `docs/UI_DESIGN.md`.
- `style.css` rebuilt section by section on one token set (surfaces, lines, radii, spacing, type scale, motion).
  Every state keeps a distinct look: stale (FROZEN, dashed, desaturated, canvases too), nodata, held, hot, flash,
  clock phases, VIX levels, band states, commentary states. Reduced motion switches all animation off.
- Canvases (trigger, futures trace, OI map, straddle, position path) redrawn sharp at any devicePixelRatio, with
  pixel-snapped gridlines, label chips and meaning-only glow. Drawing code only; no data or threshold changes.
- Small markup hooks: the verdict gets a `near` look when all three corners are at 80 % or more; the position band
  carries `data-rr` so its CALLS / PUTS pill takes the side colour; the trades table scrolls inside its panel; a held
  ATM tile drops the word "ATM" so the strike stays readable beside HELD.
- Phones: the header is no longer sticky below 820 px (it is six rows tall there). The futures chart grows with the
  trigger column above 1280 px, capped at 440 px.

## Unreleased — 2 Nov 2026 (ATM CE / PE in the header)

- **Two new header tiles, ATM CE (green) and ATM PE (coral), between Spot and VIX**, the same size and style as
  the Spot numeral. Each shows this week's at-the-money contract (the engine's `atm` strike and `w0` expiry),
  its last traded price painted on the tick like Spot is, and a sub-line with bid / ask plus delta and IV from
  the hero list. A tile the champion is holding gets an ink border and a HELD badge. Before the chain exists
  the tiles say so; after an ATM roll they switch to the new strike and wait for its first print. Fed entirely
  in the browser from the tick stream and the existing state frame: no engine or gateway change.
- **Header grid re-flowed for ten cells**: one row from 1760 px, two rows of five below that (futures, ATM CE,
  ATM PE and capital on the first; Spot, VIX, ATM IV, Clock and feed health on the second), two columns on
  phones. `tests/test_header_atm.py` checks every `grid-template-areas` in the stylesheet is rectangular and
  every header layout places every cell.

## Unreleased — 2 Nov 2026 (tests fenced off the live data)

- **`tests/conftest.py`: every test runs against a throw-away data tree (D-149).** A `pytest` run at 07:51 on
  2 Nov deleted `data/learning/days.jsonl` and `defects.json`, overwrote `state.json` with a synthetic scoreboard
  (shown on the dashboard all day as "10 trades, +4000 %"), rewrote the 21–23 Oct paper files and left 45 report
  files for dates up to Feb 2027: tests wrote through `config.PAPER_DIR` / `LEARN_DIR` and through the paths that
  `learning.py` and `defects.py` fix at import. The session-wide autouse fixture now redirects `DATA_DIR`,
  `TICKS_DIR`, `PAPER_DIR`, `LEARN_DIR`, `LOG_DIR`, `KILL_FILE`, `learning.STATE/DAYS/REPORT` and
  `defects.DEFECTS_FILE` to a temporary directory, and fails the session if anything under the live `data/`
  changed. Repair the same evening: tracked files restored from git (`days.jsonl` to 23 Oct, `defects.json`,
  `state.json` to 23 Oct with the owner champion re-applied, the 21–23 Oct paper files); 26 Oct – 2 Nov rebuilt
  from the paper records by the learning module itself; the evening look for 2 Nov run (the engine had been killed
  at 15:28 before recording the day); 2 Nov high / low / close written from trusted prints only (the index feed
  printed 23769 at 15:20 after a credential error). Not recoverable: the champion-change log between 23 and
  30 Oct, the 24–30 Oct strike levels, any defect windows declared after 23 Oct.

## Unreleased — 2 Nov 2026 (sounds)

- **Sound only for trades** (owner: "no unnecessary sound if there was no event like an entry"). The engine speaker
  plays a cue only when the champion buys, sells (win / loss) and once when the day is learned. Gone: the Triangle
  "armed" chime, the straddle-spike chime (every spike, 60-s throttle), the browser's oscillator beeps on ARMED and
  SPIKE, its commentary warning beep and the EXIT-SOON double beep. `apex/audio.py` no longer looks for mp3 files
  (the MYTHOS project's alerts were playing); the four cues are synthesised at start (numpy, 44.1 kHz, peak-normalised
  and soft-clipped, so loud without distortion) and opened on a mono mixer with `allowedchanges=0` (SDL otherwise
  opens stereo and a mono buffer plays at double speed). `static/app.js` plays the same four recipes through Web Audio
  (`sfx()`), remembers the Sound toggle across reloads, and treats the tape as first seen as history (no sound on load).
  Cues: entry = rising power-up arpeggio; win = fanfare into a sustained major chord; loss = four falling notes, the
  last sagging and wobbling; learn = two bells with a sparkle. Original chiptune-style synthesis, nothing copied from
  any game. Tests: `tests/test_audio.py`.

## Unreleased — 1 Nov 2026 (C9 council: c20_9v shadow)

- **`c20_9v` (shadow)** (owner, 1 Nov: "Yes, add as shadow"), from the 10-member C9 council on c20_9x variants
  (owner: "make each day more profitable and especially friday 30th october profitable"). c20_9x plus two exits on
  normal days only (expiry days are pure c20_9x; `apex/engine/council/c20_9v.py`):
  **LVL_BOOK** — the 50-pt round numbers of Nifty ahead of the trade are fixed at entry; sell when the bid is ≥ +6 %,
  the peak is still < +20 %, spot came within 13 pts of the next level (not broken by > 8) and gave back ≥ 10 pts;
  **PGB** — once the 20-s average of the bid has been +15 %, sell when it falls below entry + 60 % of its best gain.
  9-day engine replay (real fills, gross): c20_9v +₹9.74 L vs c20_9x +₹9.30 L; 30 Oct +₹11,622 vs −₹5,558; 21 Oct
  +₹23k, 28 Oct +₹27k; 23 Oct −₹22k (LVL_BOOK sold the 09:41 22800 PE at +9.8 % that c20_9x rode to +77 %); the other
  five days trade for trade identical. Kit: +₹12.48 L vs +₹11.49 L. Other council angles (switch permutations, earlier
  floor, swing-sized trail, box detector, entry vetoes, Greek/IV exits, stall/time exits) did not beat c20_9x robustly.
  67 variants.
- **c20_9v review fixes** (same day, from an eight-angle code review of the new book). (1) A frozen Nifty print
  (the D-132 guard withholds it and the adapter carries the last value forward) no longer disables LVL_BOOK: a print
  unchanged for 120 s counts as stale and the reference falls back to forward − basis, with the basis measured only
  against new prints. (2) The exits' state (smoothed bid and its peak, the level list and the best) now lives in
  `pos["st"]`, which the council adapter keeps on the book position and saves with it, so a mid-trade engine restart
  keeps the PGB arm and the levels fixed at entry, like c20_9x's own `peak_bid`. (3) When the reference changes source
  (print ↔ forward) the best-since-entry is re-based, so a basis jump is never a rejection. Five behavioural tests
  (LVL_BOOK fires on a 10-pt rejection at the next 50-pt level, is off on expiry days, works through a frozen print,
  ignores a source jump; PGB fires and survives a restart). Not changed: the LVL_BOOK label, shared with c20_8x's unused
  `lvl` layer; PGB's own smoothed bid beside c20_9x's `ptr` one; the exits sit in a mixin rather than `parts` switches.

## Unreleased — 31 Oct 2026 (rent trail)

- **Champion stays `c20_9x`; `c20_9t` is a shadow** (owner, 1 Nov: "Yes, revert to c20_9x"). The 8-day replay (19–29
  Oct, real fills, + 30 Oct) gave c20_9t +₹3.89 L vs c20_9x +₹9.30 L (t28_gap +₹3.76 L); it won only 30 Oct. The trail
  armed on nearly every trade, trend days included, booking ≈ +5 % where c20_9x ran +77 % (23 Oct), +81 % (21 Oct),
  +45 % (29 Oct), +18–23 % (26 Oct). Likely cause: trend efficiency < 0.35 is the normal state (30 Oct median 0.25),
  not a chop signal. Kept for live measurement; any new chop test is replayed on all taped days first.
- **`c20_9t` (shadow)**, built 31 Oct (owner: "I want a stronger trailing system on days which are not
  trending and the greeks also do not support holding for too long"). 30 Oct live: c20_9x's three trades peaked
  +15.1 %, +13.2 %, +17.6 % and exited +0.7 %, −4.6 %, 0.0 % — the normal-day floor only arms at +15 % and protects
  only the entry until +25 %. `c20_9t` = c20_9x + **rent trail** (`apex/engine/council/c20_9t.py`, switch `rt` in
  c20_9x.py): once the peak bid is ≥ +8 % and the market is choppy for the trade — the held contract's gamma rent
  (realised ÷ implied variance of the forward, last 10 min, calendar theta) has fallen to half its value at entry (the
  move went quiet) OR the forward's 10-min trend efficiency (|net move| ÷ sum of |1-min moves|) is below 0.35 (two-way
  chop) — the trail arms for the rest of the trade: exit when the bid falls below entry + 60 % of the peak gain
  (`RENT_TRAIL`). Neither condition (trending) leaves c20_9x's exits alone. Both day types: the market decides. A
  same-side re-entry within 15 min of a rent-trail exit needs a faster forward trigger than the booked trade's and
  trend efficiency ≥ 0.35 (owner: "a stronger reason than why the trade got trailed"). Calibration on the 30 Oct tape:
  the first version (absolute rent < 1) never fired — rent sat at 1.1–10 through all three trades, so c20_9t traded
  exactly like c20_9x in the replay; rent-halved catches trades 2 and 3 (~10 min in), efficiency < 0.35 catches trade 1
  (the whole day's median efficiency was 0.25). 8 % / 60 % / 0.5 / 0.35 / 15 min are the owner's picks of 31 Oct.
  66 variants.
- **Peak display fix.** The dashboard's "Best" tile is `entry + peak_pts`, which only `check_exit` maintained, so for
  council books it followed the price down and never showed the real peak. The adapter now updates `last` and
  `peak_pts` every second (not in a blackout), so the tile, the trade record and the CSV carry the true peak.

## Unreleased — 30 Oct 2026 (champion c20_9x)

- **Champion `c20_9x`** (owner, 30 Oct pre-open: "c20_9x as champion"; "I want them to run today"). The round-9
  strategy (docs/20_C20_9X_STRATEGY_SPEC.md) runs as a **council book**: `apex/engine/council/` holds the exact
  classes tested in the offline kit (`c20_08` → `c20_20` → `c20_8x` → `c20_9x`), and `council.Adapter` feeds them a
  live per-second `D` (forward, quotes, Greeks, OI of the nearest weekly) and trades through `paper.open_trade` /
  `close_trade` (all-in, |delta| ≥ 0.5 at the signal, forced flat 15:00 expiry / 15:20 otherwise). Champion and RAW
  council books raise ENTRY / EXIT events and the entry / win / loss sounds like any champion.
- **Shadows:** `c20_8x` (council) and yesterday's champion `t28_gap`; every other book unchanged (65 variants).
- Engine replay (test copy, real fills, cut at ~14:30 on most days): c20_9x +₹10.32 L over 7 days, 29 Oct +₹26.4k;
  c20_8x +₹8.06 L / +₹7.9k; t28_gap +₹3.47 L / +₹4.0k. Honest leave-one-day-out of the round-9 gains ≈ +₹1.6 L.
- New test file `tests/test_c15_council.py`; champion asserts moved to `c20_9x` / 30 Oct.
- **Code review of the port (30 Oct evening).** All nine round-9 parts match their members' code parameter for
  parameter (`l2`, `ffirst`, `seqcal`, `catch`, `dtr`, `ramp`, `ivz`, `ptre`, `tie`). Two adapter defects fixed:
  - council books filled at the print on the screen at the trigger second, bypassing D-126 (every other book waits
    for the first print AFTER the trigger: ≤ 3 s in, ≤ 10 s out). Now `paper.request_entry` / `try_fill_entry` on the
    way in and new `paper.request_exit` / `try_fill_exit` on the way out, with the same deferral, blackout and
    `stale_exit` rules. The strategy is not stepped while a fill is pending (the kit skipped its 2-s lag the same way;
    `catch` bridges the smoothed forward). **Every earlier engine figure for c20_8x / c20_9x is optimistic by the
    fill-timing bias D-126 removed for the other books.**
  - a held contract missing from the adapter's table fell back to column 0 (another contract's quote for the stop and
    floors); the strategy is now skipped for that second and a line is logged. The position's `peak_bid` is saved
    with the book so an armed floor survives a restart.

## Unreleased — 29 Oct 2026 (entry checks: "a little cheap, won't break down")

- **Three shadow books** (owner, 29 Oct midday; champion unchanged, 63 variants): `t28_fwd` (the champion's rules on
  the put-call-parity forward of the nearest weekly, shifted by its 30-min median gap to spot; 19 Oct study R² for
  option moves: future 0.45, spot 0.66, forward 0.94), `t28_mh15` (out after 15 min), `t28_tt8` (gain trail arms at
  +8 %, keeps 70 %). Short 23 Oct engine check: all three trade, no faults. The forward's histories survive a warm
  restart.
- **Champion back to `t28_gap`** (owner, 29 Oct 11:40: "Switch the champion back to t28_gap now and keep t28_cheap
  running as a shadow book"). Live, `t28_cheap` skipped both of the day's signals on the required-move check by ~3 pts
  (10:58 CE: needed 33 vs 30 moved; 11:14 PE: 32 vs 29), and a skipped signal marks its whole impulse as used.
  `t28_gap` took the 10:58 CE. Engine-only restart; the open trade carried over.
- **Champion `t28_cheap`** (owner, 29 Oct morning, replaced the same day: "Yes, promote t28_cheap to champion"): `t28_gap` entries and exits unchanged
  + two yes/no entry checks, no score:
  - **not at the high:** on pullback / retest entries, skip if the option's mid is within 2 % of its 5-min high
    (`entry_hi5_veto_pct=2.0`);
  - **move must be realistic:** skip if the spot move needed for +10 % (delta, gamma, theta over 15 min) is larger
    than the last 15-min spot range (`req_move_veto`, `req_move_k=1.0`).
  Engine replay, 7 days, real fills (ask in, bid out): **+₹4.59 L vs `t28_gap` +₹3.73 L**, no day worse
  (19 Oct +₹47 k, 27 Oct +₹21 k, 28 Oct +₹18 k), 55 trades vs 62. Caveat: the gain rests on 7 skipped trades; the
  second check is sensitive to ±30 s timing in research.
- **Ideas board** (owner, 29 Oct: "I want to test my ideas later ... somewhere in the UI"): `apex/engine/ideas/`, 16
  observer cards (move clock, OI writers, writer squeeze, OI walls, fresh-OI PCR, queue speed, aggressors, gamma vs
  theta, IV pulse, cheapest strike, regime, arm → fire, room to run, straddle pulse, peak watch, premium
  continuation), written by a 15-member council. Shown on the dashboard, every state change taped to
  `<paper dir>/ideas_<day>.jsonl` with the champion's position. **No book reads them**; a card that faults 5 times
  or runs slow is switched off for the day. `tests/test_c14_ideas.py`.
- **Champion `t28_gap`** (owner, 28 Oct evening): `lvl_trail_re` + no pullback measured across a data gap (120 s).
- **Shadow books:** `t28_nohigh`, `t28_req` (each check alone), `t28_cheapK` (expiry-day lag-cheapest strike, ATM–2
  ITM; +₹10 k on 19 + 27 Oct), `t28_ivfall`, `t28_bidpile`, `t28_st20`, `t28_gap_ts` (60 variants). Engine keeps a
  1-Hz per-option history (`ctx["ohist"]`) for these checks.
- **Rejected on the replay / research:** OI quadrants, walls, PCR, OI-acceleration + VWAP (−₹1.04 L as a trigger),
  buyers-vs-sellers queues, greek timing filters, regime gates, waiting for a dip, tighter trails, time stop.

## 1.10.1 — 28 Oct 2026 (trail, strike levels, re-entry; docs/18 §6b)

- **Champion `lvl_trail_re`:** `spot_dual_lvl` entries (no entry gate) + hard premium stop −10 % + gain trail on the
  30-s average premium (arm +20 %, keep 80 %) + expiry-day max hold 10 min + the owner's re-entry rules (after a
  trailing exit: cheaper or the next OTM strike for 30 min, stronger trigger within 10 min; after a stop: stronger
  trigger within 10 min). Six-day engine replay: +₹3.87 L, **6/6 days green** (old champion +₹3.48 L, 4/6).
- **Each strike's premium support / resistance** (`apex/engine/strike_levels.py`): taped and carried on trades,
  evidence only.
- **Shadow books:** `edge_gate_trail`, `lvl_trail`, `lvl_trail_rx`, `lvl_trail_rx_c10`, `lvl_trail_rx_be`,
  `lvl_trail_be` (43 variants). Breakeven guard and the opening-range wait were rejected on the replay.
- **Sizing:** all-in on every trade, no position sizing (owner's rule). `run_apex.py --port` runs replays in parallel.

## 1.10.0 — 27 Oct 2026 evening (buyer edge; docs/18_BUYER_EDGE.md)

- **Diagnosis, six live sessions (106 trades):** the entries carry no directional edge (option mid moves summed to +3
  pts over all trades); the 12-pt spot trail exits inside the option's ±13 % noise; options were bought when dear
  (27 Oct: IV 28–36 % vs realised 8–12 %); four champions in six sessions, each chosen on 1–3 days of replay.
- **Research files tested on the six days' ticks:** order-flow imbalance, book imbalance, micro-price, put-call-parity
  synthetic forward, Bank Nifty lead and momentum show no edge for an option buyer. The theta-vs-gamma test does.
- **Champion `edge_gate_only`:** `spot_dual_lvl` unchanged + **buyer-edge gate** (½·Γ·realised variance/min ≥ 0.5 ×
  |Θ/min|). Engine replay, six days: +₹2.50 L, 21 trades, 76 % winners, +10.5 %/trade (old champion +₹3.48 L, 55 trades,
  +5.5 %/trade; the difference is 19 Oct, in-sample for the old champion). The first pick, `apex_edge` (gate + premium
  bracket −10/+20/30 min + −20 % day stop; replayed at 50 % capital, now all-in like every book — owner's rule), made only +₹46 k on the replay — the bracket caps trend days —
  and is a shadow with `edge_bracket_only`, `edge_breakout` and `spot_dual_lvl`.
- **Freeze rule:** no champion swap or re-tune for 15 sessions or until the SPRT decides.
- New `edge.v_min30`; option rows carry gamma and theta; `max_hold_s`, `day_stop_pct`, `gt_min` variant
  keys. `tests/test_c11_buyer_edge.py`.

## 1.9.0 — 22 Oct 2026 evening (council 9: read the day, book at levels)

- **Day state** (D-141): session high/low, **range mode**, opening range, prior-day levels (`learning/day_levels.json`), round hundreds.
- **Champion `spot_dual_lvl`** (D-142): dual book + range mode + booking at a level the trade cannot break. Engine replay: 19 Oct +₹1,36,594, 21 Oct +₹36,312, 22 Oct +₹1,199 (old champion −₹53,046 replay / −₹52,084 live).
- Shadows: `spot_dual_rg`, `spot_orb45` (opening-range breakout), `spot_ft_prem10` (±10 % premium). `tests/test_c10_daystate.py`. docs/17.

## 1.8.1 — 21 Oct 2026 night

- **Champion is now `spot_dual`** (D-140): retest breakout on expiry day, pullback on other days. Engine replay: 19 Oct +₹1,31,193 (17 trades), 21 Oct +₹55,426 (4 trades). `spot_pb45` stays as a shadow.

## 1.8.0 — 21 Oct 2026 night (four external reviews)

- **Edge snapshot** (D-136): basis, IV/RV, futures book imbalance, OI-wall room, impulse state on every second, entry and decision; an "edge features" table in the evening report. Evidence only.
- **`spot_dual` shadow** (D-137): retest on expiry day, pullback otherwise.
- **Packet-shape canary + parser fuzz test** (D-138). `tests/test_c9_reviews.py`. docs/16_REVIEWS_21OCT.md.

## 1.7.0 — 21 Oct 2026 evening (council 7: few trades, held, profitable on both tapes)

- **Champion is now `spot_pb45`, the pullback book** (D-134): a ≥ 60-pt 45-min impulse, buy only its 50–78 % pullback, once per impulse, stop at the impulse origin, target one impulse beyond, lock on, entries to 14:45, flat 15:00. Engine replay: 19 Oct 5 trades +₹78,647; 21 Oct 4 trades +₹55,426. All-in, LTP, no brake.
- New module `apex/engine/impulse.py` (O(1) rolling window, warm-state persisted); `tests/test_c7_pullback.py`.
- The retest and first-touch spot books keep running as shadows. docs/14_COUNCIL7_21OCT.md.

## 1.6.0 — 21 Oct 2026 (council 6: why the champion bled on a 6-DTE day)

- **Retest entry** (D-131): a break only arms the level; buy after a 5-pt run and a pullback to within 2 pts (cancel: level lost by 3 pts / 300 s). Old entry kept as `spot_dc12_t12_first`. Engine replay: 19 Oct +90k → +131k, 21 Oct −24k → −1.9k. Two days only.
- **Index sanity guard** (D-132): a frozen or wild NIFTY print (15:15–15:30 on every day seen) can no longer set a range, a best spot, or a trade.
- Tests: `test_c6_retest.py`, `test_c6_feed.py`; `test_wp2` no longer depends on the wall clock; docs/12_COUNCIL6_21OCT.md.

## 1.5.0 — 20 Oct 2026 (council 5: "a piece of art")

- **Fills on the first print after the trigger** (D-126): 19 Oct's ₹4.69 L was priced on prints from before the move; honestly it is ₹1.79 L (same 32 trades). Still LTP.
- **Profit lock** on the spot champion (D-127, owner): +18 % arms, exit 10 % off the best; `spot_dc12_t12_nolock` runs beside. 19 Oct: ₹1,90,161 vs ₹1,81,156 without.
- **Fast replay** `--fast` (D-128): one process, bit-identical, 50 → ~18 min.
- **Live-trade commentary** (D-129): 209 templates / 685 phrasings in three modules, HOLD / WATCH / EXIT-SOON verdict, entry and review cards, tape `commentary_<day>.jsonl`, docs/11_COMMENTARY.md.
- **Dashboard** (D-130): header tiles (Spot / VIX / ATM IV / Clock), the live-trade band (lots, quantity, capital deployed, cash left, Greeks, premium path, exit clock, LOCK), the trades table, the commentary panel.

## 1.4.0 — 19 Oct 2026 evening (plan D-108 … D-115, council 4 D-116 … D-122)

- Exits and the impulse measured on the futures bid/ask mid; σ15 floor 5; 15-pt impulse floor; regime is a gate; 60-s cool-down; expiry day trades the expiring weekly. A daily brake exists in the code but is OFF (D-123: never an owner requirement); `data/KILL` stops entries only if the owner creates it.
- New books: `spot_dc12_t12` and `spot_dc12_t12_1130` (Nifty spot 12-min range break, 12-pt spot trail), shadows `m2.0_s0.5_d20`, `m2.0_s0.5_tvfast`, `fade_switch`.
- `python run_apex.py acceptance <tick file>`: lock-step replay + behaviour checks. Warm state across same-day restarts.
- Lock-step replay of 19 Oct: champion 0 trades (₹1,00,000; live it lost to ₹48,146); `spot_dc12_t12` 32 trades ₹4,68,657 — in-sample, see docs/10 §7.

## 1.3.0 — 19 Oct 2026 (first live session; 30-member council)

Call options were frozen at Friday's close all morning (feed ordering guard) and depth packets hid it; the data guard paused entries ~25 % of the time on a healthy feed and an episode-taint rule another ~30 %; per-stock scales learned from pre-open prints. Fixed: D-095 … D-107 (docs/02, docs/08). Lock-step replay of the 19 Oct tape on this code: champion 4 trades 09:25–10:51 at real prices (was 1 at a frozen price). New pre-registered book `m2.0_s0.5_novol`; evidence quarantine for data defects; data-health line in the header; deterministic replays.

## 1.2.1 — 19 Oct 2026

- Simulator stock model realistic (D-091); dashboard never cached (D-092); day high/low in the header, trades above the futures trace (D-093).
- **Closing Auction Session test (D-094)**: entries until 15:29, flatten 15:35, session to 15:40 (NSE F&O close since 3 Aug 2026); trades tagged by market phase; CAS-window trades shown in their own report section and kept out of the learning decisions; the sim models the auction; the header shows the phase after 15:15.

## 1.2.0 — 18 Oct 2026 (the council build)

Twenty independent reviewers, one assembly (106 findings: 6 critical, 28 high, 44 medium, 28 low; `docs/07_COUNCIL_REPORT.md`), seven work packages built in parallel and merged (D-080 … D-086), and four owner decisions (D-087 … D-090). Tests: 104 in eight suites plus 5 owner-decision tests. Highlights: crash-safe tick recording and replay; every advisor fault-isolated so exits always run; real heartbeats and a STALE banner; atomic, self-healing learning record with back-fill; runtime paper-only interlock; PE book side and `gex_room` forward fixed; stops fire once fresh data returns; SPRT re-registered at σ 30 % with a 30-trade minimum; IV-interpolated variant pre-registered.

Versions follow the decision log (`docs/02_DECISION_LOG.md`); every entry cites its D-numbers.

## 1.1.1 — 18 Oct 2026, 03:00 (audit)

Audit of the night's changes (`docs/06_AUDIT.md`): four defects found by re-reading, seven by an independent reviewer, all fixed with tests (28). Settling period after gaps (D-075); no exit decisions on frozen/implausible data, pricing by key only (D-076); engine sampling holes are gaps (D-077); learning idempotent per evening, day always recorded, promotion day excluded, `futures_only` keeps the champion's exit (D-078); simulator gap drill `--gap` (D-079).

## 1.1.0 — 17 Oct 2026, night (before the first live paper session)

Strengthening from the external reviews (`docs/04_EXTERNAL_REVIEWS.md`, `docs/05_STRENGTHENING.md`).

- **Market regime** classifier and advisor `regime`; every trade and candidate carries the label; the report shows results by regime (D-069).
- **Candidate ledger**: every impulse that reaches the champion's m*, taken or not, with features, decision, would-be contract and a 15-min outcome label (D-070); **diagnostics** in the learning report: hit rates with Wilson intervals by decision, rejection reason, regime, impulse size and advisor verdict (D-071).
- **Bad-print guard**: a futures move > 1 % within 2 s puts the engine in blackout (D-072).
- **Configuration self-check** in preflight and in the tests (D-073); **CI workflow** (D-074).
- Earlier the same night: data blackout guard (D-063), learning in % return / log growth (D-064), control books (D-065), Bonferroni challenger test (D-066), gated-book advisor promotion (D-067), no-order guard test (D-068), dealer gamma map (D-062), straddle watch (D-060/D-061).

## 1.0.0 — 17 Oct 2026

First complete build: feed / engine / gateway, v1 trigger (D-033), paper books, learning loop, dashboard.
