# 61. Code review of everything since Friday's close, and the fixes (15 Nov 2026)

Owner, 15 Nov: "Check for code correctness thoroughly", then "Yes, fix all".

## 1. What was reviewed

Every code change after the commit of 13 Nov 08:52 (7 commits, 52 code files, +3,880 lines). Three independent reads:

| Area | Reader | Result |
|---|---|---|
| Engine live path: Conductor, shadow accounts, 11 new books, day rows, nightly learning, config | main session | no defect that changes a live trade or can stop the engine; 4 low items |
| Service and dashboard: voice card, Forecast Lab stand, gateway, feed reconnect, supervisor | independent reviewer | no crash on a hot path; 13 display or message defects |
| Research simulator `apex/fastlab.py` | independent reviewer | 4 confirmed ways to a wrong number, 3 smaller |

The live pool and the live Conductor's decisions are unchanged by the review and by the fixes.

## 2. Findings and what was done

14 items were reported to the owner; all 14 are fixed. Four further small items found by the reviewers are fixed too
(marked +). One is left as it is, with the reason.

### Research simulator (could produce a wrong number)

| # | Defect | Fix |
|---|---|---|
| 1 | `fastlab.greeks()` gave time decay per calendar minute. The engine and the strategy classes use per trading minute, 3.84 times larger. The champion's "seq" veto and expiry "tie" strike picker read it, so every expiry day of `play()` was wrong. 9 Nov c20_9y: -12.2 % in the simulator, +30.9 % in the live record; +27.8 % after the fix. | `greeks()` returns the engine's unit. This also corrects `s20_classes.py`, `s32_real_classes.py`, `s50_live_chain.py`, which call it. |
| 2 | A feed gap was bridged with the last price and nothing else: positions held blind, sales priced at a carried bid, and the whole outage read as a 60-second move just after it. | No entry in a blackout (feed silent over 10 s, or back under 20 s: the engine's own rule). A sale fills at the first live bid. Every trade carries `blind_s`, `wait_s`, `stale_exit`. A look-back feature is empty when a gap fills over a quarter of its window. New features `black`, `since_gap`. |
| 3 | The fast exit ladder left out the champion's delta-scaled trail on normal days. | Added (`NORM["dtr"]`), built from the same delta the classes see. |
| 4 | `stats()["sum"]` is a plain sum of trade %. On 9 Nov it read +24.0 % where the all-in day was -12.2 %. | `stats()` also returns `day_sum` and `days` (each day compounds, capital fresh every day). `sum` is kept and documented. |
| + | The cache was keyed by the day alone: a day built before all its parts existed was served for ever. | Each cached day remembers what it was built from and is rebuilt when that changes. The 18 existing caches were checked against a fresh build and stamped. |
| + | Expiry days were forced flat at 15:20 in the ladder; the engine uses 15:00. Reachable only with non-default settings. | 15:00 on expiry days. |

Left as it is: the levels of the `rv*`, `rent` and `iv` features (realised move from a smoothed series, straddle IV
interpolated between two strikes). Changing them would silently move every threshold tuned on them, and no research
script reads `rent`. They are documented here instead.

### Dashboard (could show a wrong or stale statement)

| # | Defect | Fix |
|---|---|---|
| 5 | While holding, the voice card ignored a feed gap and an old quote: "+5.0 % now, I hold" on a two-minute-old price. | The card says the price is old, drops "now", dims the exit distances, and shows "HOLD · OLD PRICE". |
| 6 | The card ignored the kill switch and still said "Ready to buy". | PAUSED: "The kill switch is on. I take no entries." |
| 7 | After a restart inside the session the card said the trigger was ready for 20 minutes when the book could not fire. | It says it is learning the range and gives the right ready time. |
| 8 | The Lab's stand stayed "BULLISH" when the futures quote was stale. | The stand is taken down with the reason. |
| 9 | The Lab's "+X pts in 20 min" counted samples, not seconds (85.6 shown for a true 60 after skipped seconds). BANKNIFTY could switch from futures to index inside the 10-second look-back and read the basis as a move. | Look-backs are by the clock. BANKNIFTY comes from one source all session. The sister lead reads both markets at the same two times. |
| 10 | Wording: "warming up" after 15:30; "2 min" for 150 s; "20-min range" on expiry days; the clock announced under another exit's name; "SELLING" shown for 10 s on a same-step handover. The supervisor's "FEED reconnecting" line never printed. | All corrected. A reconnect round now stays RECONNECTING, so the line prints and the dashboard says so. |
| + | A fault in the voice left the last second's card on screen with its old time. | A fault leaves no card for that second. |
| + | A token saved in the few seconds between the feed's failed login and the supervisor's first check became the baseline, so the supervisor waited for ever. The token wait also silenced the engine's heartbeat warnings. | The baseline is taken before each feed start. Engine warnings keep printing during the wait. |

### Shadow and report code

| # | Defect | Fix |
|---|---|---|
| 11 | The fade books read once a minute at second 59. If the engine missed that second (13 Nov: 21 steps over 1 s) the reading was lost. | The reading is taken at the first row stepped at or after it: once a minute, never twice. With no missed second it is exactly the research rows. |
| 12 | The nightly shadow table's total compounded across days, though capital is fresh every day. | The total is the sum of the days. |
| 13 | The gate test and two observer figures still left out 9 Nov. | They count as the scoreboard does. |
| 14 | The offline account simulator did not pool the shadow accounts' own books. | One pool builder (`conductor.shadow_members`) serves the engine and the offline simulator. |

## 3. Checks

The fixed simulator, real class `c20_9y`, all 18 recorded sessions (`play()`, 107 trades):

| Day | Type | Simulator after the fix | Live record of c20_9y |
|---|---|---|---|
| 19 Oct | expiry | +106.2 % | not live yet |
| 27 Oct | expiry | +710.3 % | not live yet |
| 3 Nov | expiry | -7.8 % | not live yet |
| 5 Nov | normal | -5.3 % | -5.6 % |
| 6 Nov | normal | +97.9 % | +97.6 % |
| 9 Nov | expiry | +27.8 % (was -12.2 %) | +30.9 % |
| 11 Nov | normal | +3.7 % | -5.1 % |
| 12 Nov | normal | +3.7 % | +4.0 % |
| 13 Nov | normal | -19.5 % | -28.7 % |

The four expiry days equal the reviewer's independent run with the engine's unit. 11 and 13 Nov had feed gaps (13 Nov:
53 minutes), and the simulator has no open interest, so the wall veto never fires there.

The fast exit ladder against the real class on the same entries: **107 of 107 trades reproduced** (exit second and
return). Before the fix it was 37 of 50 on normal days.

Cache: a fresh build of 13 Nov (the day with the longest gap) equals the cached day, array for array.

Tests added (all pass): `tests/test_fastlab_15nov.py` (6), `tests/test_voice.py` (+4), `tests/test_forecast_lab_stand.py`
(+4), `tests/test_fade_14nov.py` (+2), `tests/test_xswitch_15nov.py` (+1 and one extended), `tests/test_learning_scoreboard_14nov.py`
(+2), `tests/test_ops_10nov.py` (+1), and two stale-price payloads in `tests/js/voice_card_test.js`. The voice card
was also rendered in the real stylesheet with a fresh price, a 120-second-old quote and a feed gap.

## 4. What the corrected time-decay unit means

Research figures produced before 15 Nov with the real strategy classes on expiry days understate the champion's
family. They were not rerun. Until they are, do not quote:

* the expiry-day rows of docs/57 (fastlab on the recorded window);
* the real-class expiry columns of the year-long per-second runs in docs/58;
* the expiry column of the live system's baseline in docs/60 section 4;
* the expiry sum of -579 and the all-days sum of -331 carried in docs/59 sections 1 and 4.3 (from `s40_expiry_class.py`,
  which reads the same value through `s32_real_classes.py`);
* the +372 % day sum of the fade3x fidelity check in docs/60 section 9 (its 97 of 98 entry times stand).

Not affected: the 30-agent holdout verdict, the causal scorer `arena_fixed`, and the expiry switch's seeded history.
They use a vectorised replica of the champion that never read this value.

## 5. Open

* Monday 16 Nov is the first live session for every book, account and card added since Friday.
* fade3x and conductor_xs have run only in the simulator, never inside the real engine.
* With 15 books of the c20_9y family, the first step after a restart inside the session takes about 1 to 2 seconds
  (each book rebuilds its IV series from 09:15). A normal 09:00 start is not affected. On a loaded machine this trips
  the 1-second line of `tests/test_ops_10nov.py::test_slow_tick...`; it fails the same way on the commit before these
  fixes.

## 6. Live-path defects found while writing the reviewer brief, and what was done (15 Nov, evening)

The review above read only the code changed since 13 Nov. The surveys for the reviewer brief (`docs/62`) read the older
code too, and a second independent read confirmed 54 of the 59 points it tested. Owner: "Yes, fix them".

Eight were fixed, two were kept as the owner's rules and measured. The live pool is unchanged.

| # | Defect | What was done |
|---|---|---|
| 1 | The parity forward's reference was the raw index price. A print the spot guard had rejected stayed the reference, and the forward's 150-point sanity bound then replaced a sound forward by that print (the vendor index has printed +501 points). | Fixed. `engine_main.forward_ref`: the trusted index, else the future, else nothing. |
| 2 | With neither a futures nor an index price the step ends before any book is stepped or any exit is checked. It was silent. | Not changed: nothing can be priced in that state. It is now said once a minute in the log and the event tape, with the open positions that wait. |
| 3 | A day that failed to start (the photograph check) still counted as started, so the next step carried on with books but no ledger. | Fixed. The day and its books are dropped, the step raises `DayNotStarted`, the heartbeat stops, and the start is retried every 30 s. |
| 4 | The close was marked done before its work. One failed save or record was never retried. | Fixed. Marked done only after the day's record is on disk; up to 5 attempts 30 s apart, and one more at the stop. |
| 5 | An unreadable pool file read as an empty pool that no check could see. | Fixed. `load_pool` carries the error, `pool_problems` and so `config.validate()` report it, and the engine says at the day's start that the live account has no pool. |
| 6 | The configuration check ran only in the optional `preflight` command. | Fixed. `run_apex.py live` runs it first and does not start on a problem (`APEX_ALLOW_BAD_CONFIG=1` starts anyway). |
| 7 | A hung engine was warned about and never restarted. A crashing engine was restarted every second with no pause. | Fixed. No heartbeat for 120 s in market hours, after at least one beat since its start: stopped and restarted from the books on disk. Restarts inside 10 minutes wait 0, 5, 10 ... 60 s. |
| 8 | The warning about other heavy jobs asked `wmic`, which this Windows no longer has, and read its absence as "nothing running". | Fixed. PowerShell is asked first; "could not look" is printed, not hidden. |

### Two rules kept, with their numbers

**The fill price.** A paper fill takes the last traded price on the first update of the option's row after the
trigger (owner, 17 Oct). That update can be a quote, so the price can be an older trade. On the four live days:

| | Result |
|---|---|
| Entries priced on a trade older than the trigger | 10 of 22 |
| Exits priced on a trade older than the exit decision | 11 of 22 |
| Ask above the fill price at entry | mean 0.23 %, worst 1.41 % |
| Fill price above the bid at exit | mean 0.17 %, worst 2.07 % |
| Cost of crossing the spread instead | 0.40 % a trade |
| Days at the last price | +59.7 %, +7.4 %, +3.7 %, -27.1 % |
| The same trades at the ask and the bid | +54.2 %, +6.7 %, +3.2 %, -28.4 % |

The rule is not changed: it is the owner's, and changing it would move every result and cut the number of trades. Owner, 15 Nov, shown these figures: "Keep it".
From 16 Nov each trade's return at the ask and the bid is kept in the day record (`net_pct`), and the nightly report
shows the live account both ways.

**Exits in a data gap.** A champion-family book still decides an exit on carried prices; the fill waits at most 10 s
for a fresh quote, then takes the last price and is tagged `stale_exit`, and such trades are left out of the scoring.
None of the 22 live trades has that tag. Not changed.

Tests: `tests/test_live_path_15nov.py` (10). Still open from the surveys: the points listed in `docs/62` sections 4 to
16 that are not in the table above.
