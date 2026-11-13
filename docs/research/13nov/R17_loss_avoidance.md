# R17. Loss avoidance: can yes/no guards stop the Conductor "doing something stupid"? (13 Nov 2026)

Lens: owner point 3. Every losing trade and losing day of the Conductor (c20 pool, 17 replayed days), studied for
re-entries after a loss, loss runs, chop, trading against the day, time of day, IV after entry, spreads and stale quotes.
Guards may only say yes or no. All-in on every trade is untouched.

## Findings first

1. **Losses do cluster.** After a losing trade the next Conductor trade wins 45 % of the time; after a winner, 58 %.
   This holds in both windows (discovery 44 % vs 58 %, test 46 % vs 59 %).
2. **But blocking the trade after a loss costs more than it saves.** The trade after a loss still averages +3.4 %.
   Two of the five biggest wins of the 17 days came about 17 minutes after a loss (21 Oct +80.9 %, 27 Oct +79.7 %).
   Every cooldown of 18 minutes or more, every daily loss cap and every day stop lost money in at least one window.
3. **The Conductor has no memory of its own account.** `apex/engine/conductor.py` hands the account to the first
   eligible trigger without looking at what the account just did. The only loss memory lives inside each book
   (its own last trade). 16 of the 29 "other side right after a loss" entries came from a different book than the
   one that lost, so no gate saw them.
4. **Chop guards fail here, and the reason is structural.** The c20 entry buys a resumption after a deep pullback, so
   it fires in low-efficiency tape by design. Trades with hour efficiency `er60` below 0.10 won 66 %; between 0.10 and
   0.25 they won 43 %. "No entry when efficiency is low" removes the best trades (discovery window: from +950 % to
   between -15 % and +603 %).
5. **One guard family is worth a shadow book: the whipsaw pause.** When the last two account trades both lost **and were
   on opposite sides**, take no new entry for 30 to 60 minutes. It improved both windows. It never touched 26 Oct,
   27 Oct or 6 Nov. It made no day worse at 60 minutes. Across the 10 c20 books run as their own accounts, 36 book-days
   were better and 6 worse.
6. **It is not ready for money.** The result has holes: 45 and 50 minutes were bad in the test window. Picking the
   minutes by rolling walk-forward lost slightly to doing nothing (+1,004 % vs +1,015 %). In the test window only one
   day (9 Nov) changed. The day result swings with which book gets the account after a block (see 7).
7. **The account path is chaotic.** Blocking one trigger changes which book owns the account for the rest of the day.
   9 Nov alone ranged from -0.4 % to +72.5 % across guard variants that differ by a few minutes. Any guard tested on
   17 days is mostly measuring this reshuffle. Strike-rate gains are the more trustworthy signal.
8. **"IV falling after entry" could not be tested on the trade table.** The c20 books record no hold marks: every
   `h60_*`, `h300_*`, `hexit_*` column is empty for all 10 c20 books (80 other books have them). At the exit, IV had
   risen more than 0.3 vol points in 76 to 93 % of winners and fallen in most losers, but that is known only at the
   exit. A Phase B script rebuilds the first five minutes of every trade from the per-second tape to test an early exit.
9. **Time of day:** entries from 14:15 won 31 % (13 trades). But a 14:15 cutoff deletes the 27 Oct 14:36 +79.7 % trade
   and costs -278 % on that day. Rejected.

Variants tried in total: about 211 guard settings (91 in the first grid, 10 candidates, 63 cooldown settings, 15 whipsaw
and side-ban settings, 32 early-exit settings that found no data), plus about 20 descriptive cuts. With that many
tries, one or two settings will look good in both windows by luck. Nothing here clears that bar strongly.

## Teardown (what the code does in my area, and where it fails)

| Where | What it does | The gap |
|---|---|---|
| `apex/engine/conductor.py:137-199` (`step`) | When flat, takes the first eligible pool trigger (`eligible[0]`, line 191) | No account history at all: losses in a row, last side, minutes since the last loss, the day's P&L are never read |
| `apex/engine/conductor.py:152` | The book that just closed cannot re-fire on the same step | That is the only re-entry rule at the account level |
| `apex/engine/conductor.py:180-183` | A pool member's rule is checked on the **trigger photograph** | Today every pool rule is `null` (`apex/rules/pool.json`), so nothing is checked |
| `apex/conductor/account_sim.py:52-92` | The offline oracle; same walk | Same blind spot. Reproduced to the trade by my simulator (17 of 17 days, 119 trades, +1,092.5 %) |
| `apex/engine/council/c20_9x.py:276-305` (`_r8_veto_seq`) | Per book: after **its own** loss below -3 % (`FY_LOSS`), an other-side entry within 900 s (`SEQ_S`, `c20_8x.py:29`) needs gamma rent >= 1.2, and on normal days RV/IV >= 1.0 | Memory is the book's own `self.last`. A loss by c20_9y does not affect c20_9s. 16 of 29 post-loss flips at the account came from a different book |
| `apex/engine/council/c20_08.py:29,129` | 60 s cooldown after the book's own exit | Book-level only |
| `apex/engine/weather4.py:631-660` (`_p_own`) | `n_losses_today`, `since_last_loss_s`, `last_ret_pct`, `win_share_today` | Computed from `book.trades`: for a Conductor entry they describe the **source book**, not the account. Easy to misread as account memory |
| `apex/engine/paper.py:1461` | `weather5.hold_tick` takes the hold marks at 60/300/900/1800 s | Called only inside the generic `check_exit` path. Council exits go through `request_exit` (`paper.py:1591`), so the live c20 books record no continuation photograph. That blocks every "what happened in the first minutes" study on the traded books |
| `apex/engine/council/c20_9x.py:60-66, 204-222` | Rent trail: chop (`er < 0.35` over 600 s) or quiet gamma rent arms a tighter trail **while holding** | Chop is used for exits, never for entries. That is right: my tests show chop is a poor entry filter for c20 |

## Evidence

Method: `work/R17/sim.py` re-walks the pool books' recorded trades exactly as `account_sim.py` does (same-tick
priority c20_9y, 9s, 9v, 9x, 9t). A guard is checked on each trigger while the account is flat. A blocked trigger
leaves the account free, so a later trigger from another book can take it. Day % is the all-in compounding return on
1 lakh. "Sum of day %" adds days (each day restarts at 1 lakh). Discovery (E) = 19 Oct to 4 Nov (12 days, 84 trades).
Test (L) = 5 to 12 Nov (5 days, 35 trades). Caveat: a blocked book would, in reality, stay flat and might fire another
trigger that its recorded trades do not show. That favours guards slightly.

### Baseline (the Conductor as replayed)

| Window | Trades | Strike rate | Sum of day % | Losing days | Worst day | Without best day | Without best trade |
|---|---|---|---|---|---|---|---|
| Discovery | 84 | 53.6 % | +949.9 | 3 | -36.3 | +417.9 | +778.0 |
| Test | 35 | 51.4 % | +142.5 | 2 | -5.9 | +42.3 | +59.0 |

### Loss anatomy (119 trades, 56 losers)

| Item | Number |
|---|---|
| Losers' summed return | -545 % (winners +1,348 %) |
| Exit reason of losers | forward trail 31, -15 % stop 19, break-even lock 5, time 1 |
| Losers of -10 % or worse | 30 (stop-outs held 3.7 minutes on average) |
| Trades right after a loss | 47: 29 on the other side (16 of them from a different book), 18 on the same side |
| Strike rate after a loss | other side 41 %, same side 50 % |

Losing days: 3 Nov -36.3 % (morning fine, then c20_9s bought PE three times between 13:54 and 14:24 against a day
up 107 to 139 points: -13.9, -20.2, -15.1). 4 Nov -26.7 % (c20_9y alternating PE, CE, PE, CE every 10 to 20 minutes, four
losses: a whipsaw). 30 Oct -5.6 %, 5 Nov -5.9 % (one trade), 12 Nov -4.0 %.

### Strike rate by situation (both windows shown: discovery / test)

| Situation | n | Strike rate | Mean return | Discovery SR | Test SR |
|---|---|---|---|---|---|
| Previous account trade won | 55 | 58 % | +7.4 % | 58 % | 59 % |
| Previous account trade lost | 47 | 45 % | +3.4 % | 44 % | 46 % |
| First trade of the day | 17 | 59 % | +13.9 % | 67 % | 40 % |
| Entry 5 to 10 min after a loss | 10 | 20 % | -6.3 % | 0 % (6) | 50 % (4) |
| `er60` < 0.10 | 35 | 66 % | +11.4 % | 67 % | 65 % |
| `er60` 0.10 to 0.25 | 42 | 43 % | +0.2 % | 42 % | 45 % |
| ATM IV 5-min change -0.1 to 0 | 21 | 29 % | +3.5 % | 29 % | 25 % |
| ATM IV 5-min change below -0.3 | 30 | 70 % | +15.5 % | 78 % | 58 % |
| Entry from 14:15 | 13 | 31 % | +1.2 % | 36 % | 0 % (2) |
| Day moved 150+ pts against the trade | 12 | 42 % | -2.7 % | 38 % | 50 % |
| Option quote older than 1 s | 4 | 25 % | +12.7 % | | |
| IV at exit minus IV at entry > +0.3 (known only at exit) | 36 | 83 % | +26 % | | |
| IV at exit minus IV at entry < -1 (known only at exit) | 14 | 36 % | -7.3 % | | |

Spread at entry did not separate winners from losers (the tightest spreads won least, 36 %).

### Guard grid on the Conductor (selected rows of 91; full table `work/R17/grid1.csv`)

| Guard (block when) | E trades | E SR | E sum % | E worst | L trades | L SR | L sum % | L losing days | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| none | 84 | 53.6 | +949.9 | -36.3 | 35 | 51.4 | +142.5 | 2 | |
| any entry within 10 min of a loss | 74 | 59.5 | +995.0 | -24.8 | 29 | 51.7 | +172.9 | 2 | spike, neighbours fail |
| any entry within 20 min of a loss | 67 | 56.7 | +649.5 | -26.9 | 25 | 48.0 | +127.9 | 2 | fail |
| after 1 loss, rest of day | 27 | 59.3 | +376.2 | -14.1 | 10 | 60.0 | +93.1 | 3 | fail |
| 3 losses today, stop | 61 | 57.4 | +740.2 | -21.1 | 17 | 47.1 | +81.5 | 3 | fail |
| day down 15 %, stop | 79 | 54.4 | +976.2 | -21.1 | 17 | 47.1 | +81.5 | 3 | fail |
| owner's example: after 2 losses, `er_day` < 0.08 and straddle not expanding, wait 30 min | 81 | 55.6 | +891.3 | -36.3 | 35 | 48.6 | +108.4 | 2 | fail |
| `er_day` < 0.05 and straddle not expanding | 73 | 52.1 | +516.6 | -36.3 | 30 | 53.3 | +151.6 | 2 | fail (E) |
| `er_day` < 0.08 (any straddle) | 43 | 41.9 | -14.7 | -36.3 | 16 | 56.2 | +86.9 | 2 | fail |
| trade 100+ pts against the day | 70 | 58.6 | +1,036.3 | -24.3 | 21 | 47.6 | +93.5 | 2 | fail (L) |
| same, only when `er_day` >= 0.1 | 76 | 57.9 | +996.3 | -24.3 | 29 | 51.7 | +146.5 | 2 | small, mixed by day |
| no entry from 14:15 | 73 | 56.2 | +699.4 | -26.7 | 33 | 54.5 | +179.4 | 2 | fail (27 Oct -278) |
| ATM IV falling (5-min chg < -0.15) | 54 | 50.0 | +384.4 | -37.3 | 24 | 45.8 | +14.6 | 2 | fail |
| option quote older than 0.8 s | 70 | 57.1 | +936.0 | -29.5 | 30 | 53.3 | +154.2 | 1 | mixed by day (5 better, 5 worse of 17) |
| spread above 0.25 % | 58 | 46.6 | +425.4 | -33.8 | 25 | 48.0 | +91.4 | 3 | fail |

### The post-loss cooldown in detail (minutes 2 to 30, loss thresholds 0, -3, -5, -10 %; `work/R17/s8_out.txt`)

| Block any entry this long after a loss | E sum % | E SR | L sum % | L SR |
|---|---|---|---|---|
| 6 min | +954.3 | 53.8 | +112.8 | 46.9 |
| 8 min | +930.5 | 54.5 | +178.6 | 53.3 |
| 10 min | +995.0 | 59.5 | +172.9 | 51.7 |
| 12 min | +1,008.8 | 58.9 | +116.0 | 46.4 |
| 14 min | +991.8 | 57.1 | +119.1 | 48.1 |
| 20 min | +649.5 | 56.7 | +127.9 | 48.0 |

Rolling walk-forward (each day from 23 Oct uses the setting that was best on all earlier days): +973.9 % against
+1,014.6 % for no guard; 2 days better, 3 worse. Verdict: no stable setting.

### The whipsaw pause (two losses in a row on opposite sides, then no entry for M minutes)

| M | E trades | E SR | E sum % | E worst | L trades | L SR | L sum % | L worst | L without best day | Top trades kept (L) |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 84 | 53.6 | +949.9 | -36.3 | 35 | 51.4 | +142.5 | -5.9 | +42.3 | 100 % |
| 20 | 78 | 57.7 | +1,022.8 | -40.1 | 33 | 48.5 | +114.6 | -5.9 | +14.4 | 100 % |
| 30 | 76 | 57.9 | +978.2 | -40.1 | 32 | 53.1 | +169.5 | -5.9 | +69.3 | 100 % |
| 40 | 76 | 56.6 | +958.0 | -40.1 | 32 | 53.1 | +169.0 | -5.9 | +68.8 | 100 % |
| 45 | 70 | 57.1 | +986.8 | -24.6 | 26 | 46.2 | +67.1 | -32.3 | -33.1 | 75 % |
| 50 | 69 | 58.0 | +1,006.6 | -24.6 | 25 | 44.0 | +63.6 | -35.8 | -36.6 | 75 % |
| 60 | 69 | 58.0 | +1,006.6 | -24.6 | 30 | 53.3 | +171.9 | -5.9 | +71.7 | 100 % |
| 90 | 68 | 57.4 | +997.8 | -29.7 | 29 | 51.7 | +155.3 | -5.9 | +55.1 | 100 % |
| 120 | 66 | 59.1 | +1,038.9 | -12.7 | 26 | 50.0 | +99.0 | -5.9 | -1.2 | 75 % |

The 45 and 50 minute holes come from 9 Nov: a few minutes' difference hands the account to a different book later
that day. Rolling choice of M: +1,004.3 % vs +1,014.6 %, 3 days better, 2 worse.

Whipsaw 60 min, per test day (day %, guarded vs none): 5 Nov -5.9 / -5.9; 6 Nov +100.2 / +100.2; 9 Nov +72.5 /
+43.2; 11 Nov +9.0 / +9.0; 12 Nov -4.0 / -4.0. Discovery days changed: 19 Oct +29.4 / +21.8; 23 Oct +47.3 / +25.2;
30 Oct -5.0 / -5.6; 3 Nov -24.6 / -36.3; 4 Nov -11.9 / -26.7. No day worse. Trades it removed over 17 days: 20, of which
13 losers and 7 winners (largest winner lost: 19 Oct +50.5 %).

Family check (each of the 10 c20 books as its own all-in account, its own history), change in sum of day %:

| Guard | Discovery change | Test change | Book-days better | worse |
|---|---|---|---|---|
| whipsaw 30 min | +64 | +306 | 30 | 12 |
| whipsaw 60 min | +297 | +340 | 36 | 6 |
| whipsaw, rest of day | +417 | -378 | 30 | 12 |
| any entry within 10 min of a loss | -132 | +312 | 36 | 17 |
| other side within 10 min of a loss | -167 | +105 | 29 | 16 |
| same side barred after 2 same-side losses | +62 | -291 | 11 | 19 |

Promotion standard (docs/28 section 2) for whipsaw 60 against the Conductor, test window: 1 strike rate 53.3 vs 51.4
(+1.9 points on 30 trades: far inside the luck margin, **fail**); 2 return +171.9 vs +142.5 (ahead); 3 positive without
best trade (+88.3) and best day (+71.7) (pass); 4 still ahead without best trade (+88.3 vs +59.0) and best day (+71.7
vs +42.3) (pass); 5 keeps 100 % of the top trades (pass); 6 worst day -5.9, the same (pass); 7 discovery window also
ahead (pass). But the improvement rests on one test day, and the idea was shaped after seeing 4 Nov (discovery).
**Not promotable; shadow it.**

## Ideas

### 1. Whipsaw pause as a Conductor shadow (recommended, confidence low to medium)
* Mechanism: two losses in a row on opposite sides means the market has just run both stops. That is two-way chop
  at the scale of the c20 pullback. The c20 resumption trigger keeps firing in it, from whichever book is free.
* Test: both windows ahead at 30 and 60 minutes. No day worse at 60. Family 36 better book-days, 6 worse. Holes at
  45 to 50 minutes. Rolling choice of minutes slightly behind.
* Build: a shadow Conductor (`conductor_wp60`) next to the live one. Same pool, same priority. One extra yes/no in
  `Conductor.step` section C before `eligible[0]` (around `conductor.py:188`): read the account's last two closed
  trades from `cb.trades`. If both have `pnl_rs < 0` and different `rr`, and the trigger is within 3,600 s of the last
  `t_out`, log `whipsaw_pause` and stay flat. No book changes. All-in unchanged. Cost: one list read a step.
* Risk: it skips a reversal winner after a two-sided flush (19 Oct lost a +50.5 % trade). The day result is
  path-sensitive, so judge it by strike rate and losing days over at least 10 forward days.

### 2. Account memory in the Conductor's photograph and its commentary (display, confidence high that it helps understanding)
* Mechanism: owner point 3 and 4. The owner cannot see that the system just lost twice on opposite sides and is
  firing again. Today `wx_n_losses_today` is the source book's count (`weather4.py:638`), not the account's.
* Build: add `acct_losses_run`, `acct_last_side`, `acct_since_loss_s`, `acct_day_pct`, `acct_whipsaw` to the
  Conductor's own log row (`conductor.py:_log` on `owner`) and to the dashboard line. First-person line, for example:
  "I lost on a put at 11:11 and a call at 11:27. The market is whipping both ways. I am sitting out until 12:27."
  Untested as a profit idea; it is a display change.
* Risk: none for trading.

### 3. Short cooldown after any loss (10 minutes) (not recommended for money, confidence low)
* Both windows ahead at exactly 10 minutes, with failure at 6, 12 and 14. Family: discovery worse, test better.
  Rolling choice loses. Keep only as one more shadow if shadows are cheap.

### 4. Chop entry guards (er_day, er60, flat straddle) (rejected)
* They remove c20's best trades, which are pullback entries in low-efficiency tape. Every setting lost in at least
  one window, most in both. Keep chop where it already is: in the rent trail (`c20_9x.py` "rt").

### 5. Day stops, daily loss caps, late cutoffs, quote-age and spread guards (rejected)
* They cost the big afternoon winners (27 Oct 14:36 +79.7 %, 6 Nov 14:09 +71.6 %, 21 Oct 11:15 +80.9 % after two losses).
  Quote age above 0.8 s improved 7 days and worsened 5: noise.

### 6. Early exit when IV falls after entry (untested; Phase B)
* Mechanism: a bought option whose IV sinks in the first minutes is losing vega and usually its thesis. At the exit,
  IV change separates winners (83 % won when IV rose > 0.3) from losers (36 % won when IV fell > 1). Only the
  first minutes are usable for a rule.
* Build: Phase B script below. If it passes, it is a hold/exit rule for a shadow c20 book, not a Conductor change.
* Risk: IV on a 1-3 day option is noisy second to second. The script uses the mid and a 60 s or longer mark.

### 7. Record hold marks for the council books (engineering, needed by 6 and by every hold study)
* `paper.py:1461` runs `weather5.hold_tick` only in the generic exit path. The live c20 books never call it. One guarded
  call in the council position update would fill `weather_hold` for the books that actually trade. Measure step
  time first (memory: live step-time check).

### 8. Against an efficient day (watch only)
* Trades 100+ points against the day when `er_day` >= 0.1: +46 % discovery, +4 % test, mixed by day. The 3 Nov afternoon
  (three PE stop-outs on an up day) is the case it catches. Not strong enough alone.

## Phase B scripts (written, not run; run after 15:30, one at a time)

| Script | What it does | How to run |
|---|---|---|
| `D:\ApexOptions\data\research\13nov\work\R17\phaseB_iv_after_entry.py` | Rebuilds the first 60/120/180/300 s of every c20 pool trade from `ds_v2` (bid, Black-76 IV from the mid). Tests "exit at mark M if IV change < X and bid gain < Y" (64 settings), re-simulates the account, discovery vs test by day | Step 1, one day per call (stays under 3 min): `py -3.13 ...\phaseB_iv_after_entry.py 2026-10-19 --marks-only`, repeat for each day to 11 Nov. Step 2: run with no arguments |
| `D:\ApexOptions\data\research\13nov\work\R17\phaseB_guards_all_books.py` | Runs the whipsaw, 10-minute cooldown, flip and against-trend guards on all 107 books as their own accounts, by window, with book-days better and worse | `py -3.13 ...\phaseB_guards_all_books.py` (or pass book prefixes to split) |

Scratch scripts and outputs: `D:\ApexOptions\data\research\13nov\work\R17\` (`sim.py` simulator, `guards.py`,
`s4_grid.py` and `grid1.csv`, `s5_desc.py`, `s6_out.txt`, `s8_out.txt`, `s9_out.txt`, `s10_out.txt`).
