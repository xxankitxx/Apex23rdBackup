# R09: sister indices (BANKNIFTY, FINNIFTY) and INDIAVIX

Owner point 5. Analyst R09, 13 Nov 2026. Read-only study; nothing in apex/ was changed.

## Findings first

1. **The engine's FINNIFTY reading is broken.** It uses the last traded price of the FINNIFTY future. That contract
   barely trades: its price changed in only 27 to 31 % of 60-second windows on the two days I extracted. So `wx_fn60` is
   exactly 0 on 74 % of all 20,817 trades, and `wx_fn300` on 38 %. Every FINNIFTY item in the weather and in the
   search cards is mostly noise. The FINNIFTY spot index and the FINNIFTY future's bid/ask both update every second.
2. **The Bank Nifty reading also uses last traded price.** BANKNIFTY futures LTP changes only 17 to 28 % of seconds. The
   15-second `bank_z` is exactly 0 on 11 % of trades. Bid/ask mid changes about twice as often.
3. **On the live feed the sisters arrive first, by about 1 to 2 seconds.** On 23 and 27 Oct, the BANKNIFTY and FINNIFTY
   futures mids (and even the Nifty spot index) move one second before the Nifty future mid. Nifty's own past return
   tells almost nothing about its next 5 to 60 seconds (IC 0.00 to 0.03). The sisters' past 5 to 15 seconds do
   (IC 0.07 to 0.16, sign right 53 to 57 % of the time), fitted on one day and scored on the other.
4. **The sweet spot is short.** Look back 5 to 15 seconds, forecast 5 to 60 seconds ahead, about equal weight on
   BANKNIFTY and FINNIFTY. Past 3 minutes the information is gone and the sign flips between days. Nothing at 5 minutes
   is stable. This fits the Forecast Lab's 1 to 3 minute skill, and the Lab uses no sister index at all today.
5. **As a yes/no trade filter, the sisters are weak.** I tried 146 sister and VIX filters walk-forward on the
   Conductor's trades. Only 8 % beat the unfiltered Conductor on the test days. The best candidate is the engine's own,
   never-promoted Bank advisor: skip a trade when Bank Nifty futures move against it (15-second z below -0.5). It improved
   the strike rate in both windows and the test return (+266 % against +201 %). But it made the worst discovery day
   worse (-43.1 % against -37.1 %), so it **fails the owner's standard**. Shadow book only.
6. **Relative strength points the other way from the obvious idea.** When Bank Nifty is beating Nifty in the trade's
   direction at entry, the trade does slightly *worse* (AUC 0.42 to 0.45 on all books, below 0.5 on all three days).
   On a 30 to 60 minute scale the bank-minus-Nifty spread drifts back on 23 Oct (half-life 58 min) but not on 27 Oct.
   Mean reversion of the spread is not a dependable intraday edge.
7. **VIX change does not predict the next Nifty move** (IC -0.09 to +0.03). It moves with Nifty at the same time
   (correlation -0.55 to -0.68), so it is a mirror, not a lead.

## Teardown: what the code does with the sisters today

| Where | What it does | Problem |
|---|---|---|
| `apex/feed_breeze.py:407-414` | Subscribes INDIAVIX, BANKNIFTY and FINNIFTY spot and futures. Depth only for BANKNIFTY. | Fine. The data is there. |
| `apex/engine_main.py:289` | `bn_id` = BANKNIFTY future (spot only as fallback). | Uses the future's LTP downstream. |
| `apex/engine/extras.py:91-126` | `BankLead`: 15-s change of BANKNIFTY futures **LTP** on its own running scale; `veto(d)` when `z*d < -0.5` (line 122). | LTP is stale 72 to 83 % of seconds. A stale print gives z = 0 and a lagged jump later. |
| `apex/engine_main.py:1506-1507` | The `bank` advisor reports that veto. | Only a gate if the learning loop promotes it (`apex/engine/paper.py:1130`, `gates` starts empty, `apex/engine/learning.py:183`). The c20 councils (`apex/engine/council/c20_*.py`) never read it. **The Conductor uses no sister information at all.** |
| `apex/engine_main.py:904` and `apex/engine/weather.py:388-392, 477-479` | `bn60`, `bn300`: Bank Nifty futures LTP history, 60 and 300 s. | LTP, not mid. |
| `apex/engine_main.py:1137-1141` and `apex/engine/weather.py:554-557` | `fn60`, `fn300` from the FINNIFTY **futures LTP**. | The broken item: 74 % zeros. Should use the FINNIFTY spot index or the future's mid. |
| `apex/engine/weather4.py:156-168, 374-381` | `bn_minus_nifty60/300`, `bn_corr30`, `vix_day_pos`. | Built on the same LTP history. `bn_corr30` is missing on 17.5 % of trades. |
| `apex/conductor/search.py:75, 124` | Cards 35 and 81 list these items for the rule search. | Searches over a broken FINNIFTY item. |
| `apex/forecast_lab/brain.py:41, 173-183` | `bank120` = bank *stocks* minus the rest of the heavyweights. | No index-level sister feature. The Lab ignores BANKNIFTY, FINNIFTY and VIX ticks completely. |
| `apex/feed_sim.py:126-130, 293-302` | The simulator builds BANKNIFTY and FINNIFTY from stock weights. | No lead or lag, so a sim run will never show the effect in point 3. |
| `data/research/ds_v2` (`ds2.py`) | Per-second research set. | Has no sister or VIX column. My extractor fills the gap. |

## Evidence

### Data built now

Streaming extractor `work/R09/sister_extract.py`: gzip in 8 MB blocks, a byte search finds only the target packets, below
normal priority. Same rule as `ds2.py`: a row stamped second B holds only packets that arrived before B. Columns: Nifty
spot, Nifty future LTP/bid/ask/volume, the same for BANKNIFTY and FINNIFTY, VIX, plus the age of each source.

| Part | Gzip MB | Rows (s) | Run time |
|---|---|---|---|
| 2026-10-23 | 62 | 7,111 | 59 s |
| 2026-10-23.p2 | 119 | 15,323 | 116 s |
| 2026-10-27.p2 | 133 | 15,343 | 122 s |
| 2026-10-27.p3 | 63 | 6,636 | 91 s |
| 2026-10-19.p2 (test part) | 14 | 1,451 | 20 s |

So 23 Oct and 27 Oct are complete, 09:15 to 15:30. The other days are left for phase B.

How fresh each source is (23 Oct):

| Source | Median age | Changes per second | Changed within 60 s |
|---|---|---|---|
| Nifty future mid | 0.13 s | 40 % | 94 % |
| BANKNIFTY spot | 0.13 s | 93 % | 96 % |
| BANKNIFTY future LTP | 0.52 s | **28 %** | 94 % |
| BANKNIFTY future bid/ask | 0.52 s | 38 to 44 % | 94 % |
| FINNIFTY spot | 0.13 s | 92 % | 96 % |
| FINNIFTY future LTP | 0.85 s | **1 %** | **27 %** |
| FINNIFTY future bid/ask | 0.85 s | 41 to 45 % | 94 % |
| INDIAVIX | 0.40 s | 45 % | 87 % |

### Lead-lag on 1-second returns

Correlation of X's return at second t with the Nifty future's return at t+k. Positive k means X moves first.

| Pair | Day | k = -1 | k = 0 | k = +1 | k = +2 |
|---|---|---|---|---|---|
| BANKNIFTY fut, Nifty fut | 23 Oct | 0.03 | 0.13 | 0.06 | 0.10 |
| BANKNIFTY fut, Nifty fut | 27 Oct | 0.10 | 0.13 | 0.11 | 0.07 |
| FINNIFTY fut, Nifty fut | 23 Oct | 0.06 | 0.15 | **0.15** | 0.05 |
| FINNIFTY fut, Nifty fut | 27 Oct | 0.08 | 0.16 | **0.14** | 0.05 |
| Nifty spot, Nifty fut | 23 Oct | 0.03 | 0.07 | 0.06 | 0.05 |
| Nifty spot, Nifty fut | 27 Oct | 0.01 | 0.17 | 0.14 | 0.02 |

By k = +5 everything is below 0.02. A real market usually has the future lead the spot index. Here even the spot index
arrives first, so part of this is the order in which Breeze delivers packets. That does not matter for trading: the tape
is the live arrival order, and the engine sees the same order live and in replay.

### Which inputs predict the Nifty future's next move (two-fold: fit one day, score the other)

IC = correlation of the forecast with the actual move. Hit = sign right.

| Look ahead | Look back | Nifty own | BANKNIFTY | FINNIFTY | Nifty + both sisters |
|---|---|---|---|---|---|
| 5 s | 5 s | 0.03 / 50.9 % | 0.13 / 54.5 % | 0.16 / 54.7 % | **0.22 / 56.9 %** |
| 15 s | 5 s | 0.01 / 49.5 % | 0.09 / 54.3 % | 0.13 / 54.4 % | 0.15 / 55.4 % |
| 15 s | 15 s | 0.02 / 51.5 % | 0.07 / 54.2 % | 0.12 / 55.4 % | 0.11 / 55.2 % |
| 30 s | 15 s | 0.03 / 51.5 % | 0.06 / 53.2 % | 0.09 / 54.5 % | 0.09 / 54.4 % |
| 60 s | 15 s | 0.01 / 50.7 % | 0.04 / 52.8 % | 0.07 / 54.1 % | 0.08 / 54.1 % |
| 180 s | 60 s | -0.05 / 48.7 % | 0.04 / 51.2 % | 0.07 / 52.7 % | 0.06 / 52.3 % |
| 300 s | 300 s | -0.09 / 50.4 % | -0.10 / 49.2 % | -0.09 / 51.0 % | 0.04 / 50.3 % |

Variants tried: 6 look-aheads x 5 look-backs x 7 feature sets = 210 cells. Only two days, both in the discovery window.
Treat these as strong hints, not proof.

By regime (15 s ahead, 15 s back), FINNIFTY-minus-Nifty kept a positive IC in every split on both days: low volatility,
high volatility, trend and chop (0.03 to 0.17). At 5 minutes the sign flipped between days in every split.

### The bank spread (BANKNIFTY future against Nifty future, 1-minute samples)

| Day | Beta | Spread std | Half-life | Spread z predicts its own move back (30 min) |
|---|---|---|---|---|
| 23 Oct | 0.77 | 17 bp | 58 min | IC 0.24, but toward Nifty only for 5 to 15 min |
| 27 Oct | 0.65 | 30 bp | none (no reversion) | IC -0.29 |

The spread is not a stable mean-reverting pair inside one day. No idea built on it.

### Sister confirmation at the trigger, walk-forward on the Conductor's trades

119 Conductor trades (p44_sim plus p44_simr), joined 119 of 119 to the photograph. Discovery 19 Oct to 4 Nov (84 trades,
12 days), test 5 to 12 Nov (35 trades, 5 days). A filtered trade is simply dropped; I did not replay what the Conductor
would take instead. 146 variants (23 items, keep above or below, cut at the discovery 20/33/50 % points and at 0).

| Filter | Window | Trades | Strike | Compounded | Losing days | Worst day | Without best day |
|---|---|---|---|---|---|---|---|
| None (the Conductor) | discovery | 84 | 53.6 % | +7,489 % | 3 | -37.1 % | +1,082 % |
| None (the Conductor) | test | 35 | 51.4 % | +201 % | 2 | -6.0 % | +44 % |
| Bank veto z < -0.5 (engine's own advisor) | discovery | 71 | 54.9 % | +7,914 % | 3 | **-43.1 %** | +1,149 % |
| Bank veto z < -0.5 | test | 32 | 53.1 % | +266 % | 2 | -6.0 % | +84 % |
| Bank veto z < -1.0 | discovery | 76 | 55.3 % | +8,313 % | 3 | -37.1 % | +1,211 % |
| Bank veto z < -1.0 | test | 35 | 51.4 % | +201 % | 2 | -6.0 % | +44 % (vetoed nothing) |
| Bank veto z < 0 | discovery | 63 | 55.6 % | +4,792 % | 4 | -47.0 % | +551 % |
| Bank veto z < 0 | test | 29 | 51.7 % | +213 % | 1 | -6.0 % | +58 % |
| VIX 15-s change above -0.06 | discovery | 55 | 60.0 % | +10,229 % | 4 | -22.7 % | |
| VIX 15-s change above -0.06 | test | 26 | 57.7 % | +192 % | 2 | -6.0 % | +16 % |
| Both sisters with the trade over 5 min | test | 20 | 55.0 % | +83 % | 0 | 0.0 % | +17 % |

Test per day for the -0.5 Bank veto: 5 Nov -6.0, 6 Nov +98.4 (base +109.2), 9 Nov +39.9 (base +43.4), 11 Nov +23.2
(base +12.0), 12 Nov -4.8 (base -4.8), in %.

The same -0.5 veto on each c20 pool book: test return better for all five (9y 252 against 175, 9s 255 against 205,
9v 296 against 239, 9x 247 against 197, 9t 72 against 65). Discovery return worse for all five. So the pattern is not
stable across windows. Across all 146 variants the median test result was +64 %, below the unfiltered +201 %.

The one thing in its favour: the -0.5 threshold is the engine's pre-registered advisor, not a number I fitted. That
lowers the multiple-testing worry for this single line, but it still fails the "worst day no worse" test.

### Winner separation, all items (AUC, 0.5 = no information)

| Item | Conductor early / late | Pool books early / late | All books early / late |
|---|---|---|---|
| bn60 | 0.50 / 0.47 | 0.47 / 0.48 | 0.49 / 0.50 |
| fn60 (broken) | 0.60 / 0.54 | 0.59 / 0.50 | 0.53 / 0.48 |
| bank_z | 0.52 / 0.57 | 0.49 / 0.60 | 0.50 / 0.52 |
| bn_minus_nifty300 | 0.51 / 0.55 | 0.52 / 0.58 | 0.48 / 0.50 |
| vix_chg30 | 0.53 / 0.68 | 0.54 / 0.69 | 0.52 / 0.53 |
| vix level | 0.64 / 0.44 | 0.63 / 0.44 | 0.51 / 0.52 |

Nothing holds in both windows above 0.55 except VIX 15-s change on the Conductor (0.58 / 0.61). That is 35 test trades.

Clean sister measures from my panel at the entry second (23 Oct and 27 Oct, 2,972 all-book trades): Nifty's own 60-s
move separates winners best (AUC 0.60). The sisters' 60-s moves add nothing on top (0.55 to 0.57), because at entry
they mostly repeat Nifty's move. Bank relative strength scores 0.42 to 0.45, consistent across days.

## Ideas

### 1. Fix the sister readings (data fix, not a rule)

* Mechanism: read the FINNIFTY **spot index** for `fn60/fn300` in `engine_main.py:1137-1141`, falling back to the
  future's mid. Feed `BankLead` and `bn60/bn300` with the BANKNIFTY future's **mid** (or the spot index), not LTP.
* Test: not needed for correctness. The measured staleness above is the evidence.
* Build: a few lines in the two feeders. The weather card numbers for items 35 and 81 change, so mark the old
  `wx_fn*` as "v1, broken" in the cards, so no rule gets found on them.
* Risk: low. Any pool rule that uses `fn60` would change behaviour (none of the five c20 books uses it today).
* Speed: no cost. It is one array read per second.

### 2. Sister lead features in the Forecast Lab (the sweet spot)

* Mechanism: add three features to `apex/forecast_lab/brain.py` FEATS: `sis5` and `sis15` (mean of BANKNIFTY and
  FINNIFTY futures mid return over 5 and 15 s, minus the Nifty future's, on the Lab's own volatility scale), and
  `nlead5` (Nifty spot index minus Nifty future, 5 s). Equal weight on the two sisters. The Lab's live process
  already reads the shared table, so the mids are there.
* Test: two-fold on two days, IC 0.13 to 0.22 at 5 to 15 s, 0.07 to 0.08 at 60 s. Not tested inside the Lab's model.
  Phase B runs the walk-forward on all 17 days.
* Build: shadow first. Train a second brain with the three extra features, show both forecasts side by side, score
  both at 1, 3 and 5 minutes in `walk_forward.json`.
* Risk: the lead may be partly packet-delivery order. If Breeze changes its delivery, the edge goes. Watch the per-day
  IC; drop the features if it falls below 0.03 for three days.
* Display (owner point 4): the commentary can say, in first person, "Bank and Fin futures moved up 4 and 6 points in the
  last 10 seconds and Nifty has not followed yet. I expect Nifty to tick up in the next half minute." That is a clear
  stand at the horizon where the skill is real.

### 3. Bank-against shadow book

* Mechanism: c20_9y (and the Conductor as a whole) skips a trigger when the BANKNIFTY future's 15-s z is below -0.5 in
  the trade's direction. This is the existing `bank` advisor used as a gate.
* Test: walk-forward above. Better strike in both windows, better test return, worse worst discovery day. **Fails** the
  promotion standard. 146 variants in the family.
* Build: register it as a shadow pair (book c20_9y, rule "bank advisor veto") and let the official standard score it
  live. Re-test after idea 1, since the z built on mid will be different.
* Risk: it removes about 15 % of trades, and one of the removed trades on 26 or 27 Oct could be a big winner.

### 4. Ideas tested and dropped

* Bank relative strength as a confirmation: wrong sign (AUC 0.42 to 0.45). Dropped.
* Bank-minus-Nifty spread mean reversion: reverts on one day, trends on the other. Dropped.
* Both sisters agreeing over 5 min: test 0 losing days, but return +83 % against +201 %. It trades too little. Dropped.
* VIX change as a lead for direction: IC near zero. VIX 15-s change as a filter looked good in both windows by strike
  (60.0 % and 57.7 %), but the return fell on the test window. Untested further.

## Phase B scripts (ready, not run)

| Script | What it does | Run after |
|---|---|---|
| `data/research/13nov/work/R09/phaseB_sister_extract_all.py` | Builds the per-second sister panel for every tape part, one at a time, skipping today and empty stubs. About 1 to 4 minutes per part on a quiet machine. | 15:30 close, machine quiet |
| `data/research/13nov/work/R09/phaseB_sister_wf.py` | All-day walk-forward: lead model fitted on 19 Oct to 4 Nov, scored per day on 5 to 12 Nov (80 cells); clean sister measures at the Conductor's entries with discovery-chosen cuts, scored per test day. | the script above |

Other scratch files: `sister_extract.py`, `sister_io.py`, `sister_leadlag.py` (two-day lead-lag, results in
`leadlag_results.json`), `sister_trades.py` (trade-table walk-forward, `trades_results.json`, `trades_out.txt`),
`sister_at_trigger.py` (`at_trigger.parquet`, `at_trigger_results.json`), `bankz_check.py`.

## What I did not do

* No per-second walk-forward on the late days yet: only 23 and 27 Oct are extracted (both discovery days).
* Dropped trades are not replaced in the Conductor test. A real replay with the gate could differ.
* No web sources were needed. The lead-lag and spread methods are standard (cross-correlation, least-squares,
  AR(1) half-life).
