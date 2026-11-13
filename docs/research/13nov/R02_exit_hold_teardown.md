# R02. Exit and hold teardown (owner point 2: holds and exits)

13 November 2026. Analyst R02. All numbers are from the 17-day replay trade table (run p44) and the Conductor's own
119 replayed trades, plus a per-second pilot on three test days. Returns are in percent of premium (all-in, so they
compound). Nothing here was run against the live session.

## Findings first

1. **The Conductor keeps 30 % of the move its trades make.** Over 119 trades the sum of returns is 802 % against
   2,652 % at each trade's best bid. In compounding terms it keeps 27 % on the early days and 19 % on the later days.
   16 trades that were up 10 % or more ended at zero or below.
2. **The leak is not where it looks.** The giveback is mostly the price of keeping the runners. Every tighter trail,
   tighter stop, earlier floor or earlier clock I tested loses money in at least one window, as docs/49 found.
   I tried about 250 variants across four test beds (table at the end). None of the trail changes survives.
3. **The single biggest drag is the expiry-day premium stop.** 18 of the Conductor's 66 expiry trades hit the 15 %
   stop. Together they cost 301 log points, more than half of the account's whole log gain (543). 12 of the 18 were
   stopped within 2 minutes. The median trade never had the forward move its way at all (best favourable move 0
   points). 5 of the 18 were stopped while the forward had moved less than 3.5 points against them. Those were
   cheap afternoon options losing to the spread, IV and decay, not to direction.
4. **Theta is the expiry hold's real enemy.** At the exit request, the delta move had earned +497 premium points over
   the expiry trades. Decay took back 228 of them (46 %). On normal days decay took only 74 of 879 (8 %).
5. **The best robust change: an expiry-day take-profit at +60 %.** It can be scored exactly from the table, because
   it only needs the best bid of each hold. It is better in both windows on every set: the Conductor (+18 and +12
   log points), the five pool books (+78 and +46) and all c20 books (+200 and +110). Every level from 55 % to 70 %
   is positive in both windows. It touches only 6 Conductor trades, so the evidence is thin. It should run as a
   shadow book first.
6. **The only exit twin already in the replay that wins in both windows is c20_9v** (smoothed premium giveback PGB
   plus round-number booking LVL_BOOK). Against c20_9x it is better on 3 early days and worse on 1 (+56 day-%), and
   better on 3 late days and worse on none (+14 day-%). It has 3 losing days against 5. Every tighter twin raises
   the strike rate and loses money: c20_9t, c20_9e, c20_9h and fx_c20_9y all lose more than 400 day-% on
   27 Oct alone.
7. **Exit signals change sign from one window to the next.** On the 92 books that record hold marks, I measured how
   each 5-minute and 15-minute feature relates to the return still to come. Most of those relationships flip sign
   between the early and late days. At 5 minutes, gain had rho +0.08 early and -0.15 late. Forward follow-through
   had +0.16 early and -0.12 late. So any rule of the form "exit when the mark looks weak" is fitted to its window.
   The best rule on the early days (exit at 5 minutes if the forward is not yet in favour) added +1,594 log points
   early and lost 573 late.
8. **A data gap hides the champion's hold.** The c20 books never record the hold marks (h60 to h1800): 0 of 543
   pool trades have them. The council adapter never calls the hold photograph (`weather5.hold_tick`), which only
   runs inside `paper.check_exit`. So the champion's hold cannot be studied from the trade table. Every hold study
   of the champion needs the per-second tapes.

## Teardown: what the exit code does, and where it fails

### Where the exits live

| Layer | File:line | What it does |
|---|---|---|
| Core c20_08 | apex/engine/council/c20_08.py:21-41 | Expiry: SL 15 %, forward trail 25 pts, 15-min clock. Normal: SL 15 %, forward trail 40 pts, 90-min clock. |
| Core exit order | c20_08.py:110-127 | SL, then TP (off: 9.9), then forward trail (from the best smoothed forward), then clock. |
| Premium floors (pex) | c20_8x.py:29, 280-286 | Expiry: from +15 % peak the floor is the entry (BE_LOCK); from +60 % it keeps 70 % of the gain (GIVEBACK). |
| Ramp floor (normal days) | c20_9x.py:174-184, R9P line 46-56 | Below +15 % peak: no floor. +15 to +25 %: entry. +25 to +50 %: 45 % to 70 % of gain. Above +50 %: 70 %. |
| Delta trail factor (dtr) | c20_9x.py:154-163, 366-368 | The normal-day trail shrinks to 0.8x as the option goes in the money. |
| Expiry premium trail (ptre) | c20_9x.py:352-361, 432-434 | From +70 % peak the forward trail is off; exit 8 % below the best bid (tau 1 s, so raw bid). |
| Stale-forward trail (l2) | c20_9x.py:409-431 | If the forward freezes for 5 s the trail becomes a premium trail. |
| Rent trail (c20_9t) | c20_9x.py:203-222, c20_9t.py | Once +8 % and the market is choppy or quiet, keep 60 % of the gain. |
| PGB and LVL_BOOK (c20_9v) | c20_9v.py:66-101 | Normal days: a 20-s smoothed bid keeps 60 % of its gain once +15 %; sell near a round number after a 10-pt rejection. |
| Adapter forced flat | council/__init__.py:193, 201-202 | 15:00 expiry, 15:20 normal. |
| Peak tracking | council/__init__.py:184-192 | The peak bid is the raw 1-second bid maximum. |
| Fill of an exit | paper.py:1590-1640 | Fills on the first print after the trigger (D-126); clocks fill at once. |
| Conductor | apex/engine/conductor.py:15-16, 258-312 | Copies the owner book's exit price and reason. It never exits on its own. |

### Where it fails

1. **The expiry SL is a premium stop on a raw 1-second bid** (c20_08.py:119, c20_9x.py:411). It is measured from the
   ask paid. On a 47-point afternoon option a 1.5-point spread is already 3 % of the 15 %. One flicker of the bid
   fires it. Example: 3 Nov 14:24 PE at 47.35 was stopped at -16 % while the forward had moved 0.35 points against
   it. The stop does not ask whether the thesis (the forward) is wrong.
2. **Nothing protects a normal-day trade between +8 % and +15 %.** The ramp only arms at +15 % (R_ARM, c20_9x.py:49).
   The median normal-day FWD_TRAIL exit had peaked +11 % and left at -2.7 %. A 40-point forward trail is wider than
   most of these moves. This is the "stuck trade" of docs/22, but docs/49 shows that floors armed at 8 to 15 % lose.
3. **The expiry floor jumps from the entry to 70 % of the gain only at +60 %** (c20_8x.py:283-286). Between +15 % and
   +60 % the only floor is the entry. 7 expiry BE_LOCK trades peaked at a median +18 % and exited at -0.4 %.
4. **The raw-bid peak** (council/__init__.py:189-191) lets a one-second spike arm a floor or the +70 % premium trail.
5. **Exit priority hides reasons.** With "ffirst", a floor relabels a same-second trail exit (c20_9x.py:244-245).
   Reason counts therefore mix "trail" and "floor".
6. **No hold photograph for council books** (paper.py:1460-1463 only; council/__init__.py:178-248 has no call).
   The `hexit_req_*` snapshot exists, but the 60/300/900/1800-second marks do not.

## Evidence

### Exit reasons of the Conductor's 119 replayed trades

Peak = best bid during the hold over entry. Capture = sum of returns / sum of positive peaks. MAE = worst LTP.
Hold and time-to-peak are medians in minutes.

| Day type | Reason | Trades | Win % | Mean ret % | Median ret % | Median peak % | Capture % | Median giveback % | Median MAE % | Hold min | To peak min | Up >= 10 % then <= 0 | Sum log % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Normal | FWD_TRAIL | 37 | 37.8 | 6.70 | -2.72 | 11.3 | 34 | 13.1 | -7.4 | 18.6 | 10.2 | 7 | +154 |
| Normal | RAMP_LOCK | 6 | 100 | 17.54 | 17.57 | 33.8 | 53 | 16.0 | -6.9 | 18.6 | 17.0 | 0 | +97 |
| Normal | RENT_TRAIL / TIME / others | 10 | 70 | 11.9 | | | | | | | | 1 | +96 |
| Expiry | FWD_TRAIL | 20 | 60.0 | 4.03 | 4.11 | 24.1 | 16 | 20.7 | -7.7 | 5.2 | 3.4 | 2 | +60 |
| Expiry | SL | 18 | 0 | -15.39 | -15.03 | 2.9 | n/a | 18.3 | -15.7 | 1.5 | 0.3 | 2 | **-301** |
| Expiry | TIME (15-min clock) | 12 | 100 | 15.33 | 9.30 | 18.8 | 58 | 8.5 | -8.5 | 15.0 | 11.2 | 0 | +164 |
| Expiry | BE_LOCK | 7 | 42.9 | -0.13 | -0.36 | 18.2 | -1 | 18.7 | -2.5 | 3.5 | 1.8 | 4 | -1 |
| Expiry | GIVEBACK | 3 | 100 | 42.70 | 42.65 | 62.8 | 67 | 20.8 | -8.1 | 13.9 | 11.4 | 0 | +107 |
| Expiry | PREM_TRAIL | 3 | 100 | 63.20 | 61.09 | 85.4 | 71 | 24.3 | -4.6 | 4.4 | 4.2 | 0 | +146 |
| Expiry | RENT_TRAIL | 3 | 100 | 7.47 | 7.91 | 12.6 | 57 | 5.0 | -2.5 | 1.4 | 1.0 | 0 | +22 |
| All | | 119 | 52.9 | 6.74 | 0.80 | 14.6 | 30 | 15.6 | -8.0 | 8.9 | 4.9 | 16 | +543 |

The five pool books (543 trades) look the same: capture 31 %, normal days 44 %, expiry days 22 %.

### What the hold looked like at the exit request (Conductor trades, medians)

| Day type | Reason | Gain pts | Peak pts | Gain / peak | Giveback rate pts/min | Peak age s | Forward in favour pts | Delta pts | Theta pts | IV change |
|---|---|---|---|---|---|---|---|---|---|---|
| Normal | FWD_TRAIL (37) | -5.3 | 22.1 | -0.22 | 4.2 | 370 | -1.7 | -1.0 | -0.9 | -0.11 |
| Expiry | FWD_TRAIL (20) | +4.6 | 28.0 | 0.16 | 17.9 | 90 | +13.9 | +8.7 | -2.1 | +0.17 |
| Expiry | SL (18) | -12.0 | 2.0 | n/a | 10.0 | 77 | -11.5 | -7.1 | -1.0 | -0.60 |
| Expiry | TIME (12) | +9.3 | 17.6 | 0.51 | 3.6 | 231 | +17.5 | +11.8 | -7.1 | +0.50 |

Sum over all trades at the exit request. Normal days: gain 792 pts = delta +879, theta -74, rest -12. Expiry days:
gain 298 pts = delta +497, theta -228, rest +29.

### Capture per day (Conductor)

| Day | Trades | Won | Day return % | Capture % |
|---|---|---|---|---|
| 19 Oct | 18 | 8 | +22.8 | 15 |
| 21 Oct | 5 | 1 | +47.5 | 47 |
| 22 Oct | 3 | 2 | +8.4 | 19 |
| 23 Oct | 5 | 1 | +27.4 | 38 |
| 26 Oct | 6 | 6 | +277.8 | 68 |
| 27 Oct | 13 | 10 | +541.9 | 49 |
| 28 Oct | 5 | 4 | +62.5 | 56 |
| 29 Oct | 4 | 2 | +28.1 | 38 |
| 30 Oct | 3 | 0 | -6.0 | -13 |
| 2 Nov | 4 | 3 | +42.2 | 43 |
| 3 Nov | 13 | 7 | -37.1 | -24 |
| 4 Nov | 5 | 1 | -28.5 | -113 |
| 5 Nov | 1 | 0 | -6.0 | -72 |
| 6 Nov | 4 | 4 | +109.2 | 74 |
| 9 Nov | 22 | 11 | +43.4 | 15 |
| 11 Nov | 4 | 2 | +12.0 | 29 |
| 12 Nov | 4 | 1 | -4.8 | -10 |

The worst capture days (19 Oct, 3 Nov, 9 Nov) are expiry days with many trades. On them, stops and BE_LOCK exits
churn.

### Test 1. Tighter premium stops (exact from the table: the worst bid of the hold)

| Set | Rule | Change, early (log pts) | Change, late | Trades changed | Winners cut | Strike rate |
|---|---|---|---|---|---|---|
| Conductor | Expiry SL 10 % | -93 | -86 | 8 | 7 | 52.9 to 47.1 |
| Conductor | Expiry SL 12 % | -50 | -95 | 6 | 6 | 52.9 to 47.9 |
| Conductor | Normal SL 10 % | -51 | 0 | 4 | 3 | 52.9 to 50.4 |
| Pool 5 | Expiry SL 10 % | -450 | -415 | 40 | 36 | 57.8 to 51.2 |
| Pool 5 | Normal SL 8 % | -703 | -102 | 51 | 38 | 57.8 to 50.8 |

All 16 settings lose in both windows. On expiry days, 36 eventual winners dip below -10 % first. The stop is
already as tight as it can be. If anything it should be wider or smarter (Test 5).

### Test 2. Take-profit levels (exact from the table: the best bid of the hold)

45 rules: fixed levels of 10 % to 100 %, and levels in units of the 30-minute 1-sigma premium move
(|delta| x forward x IV x sqrt(30 min)). Each was tried on all days, expiry only and normal only. Change in the sum of
log returns:

| Expiry TP level | Conductor early / late | Pool 5 early / late | All c20 books early / late |
|---|---|---|---|
| 45 % | +24 / -8 | +104 / -21 | +297 / -66 |
| 50 % | +6 / -1 | +50 / -12 | +111 / -19 |
| 55 % | +26 / +5 | +120 / +17 | +296 / +47 |
| **60 %** | **+18 / +12** | **+78 / +46** | **+200 / +110** |
| 65 % | +15 / +2 | +63 / +12 | +169 / +17 |
| 70 % | +8 / +5 | +39 / +27 | +112 / +47 |
| 80 % | 0 / +11 | +1 / +55 | +29 / +104 |

Normal-day TPs and every sigma-scaled TP do nothing or lose. The 60 % rule changes 6 Conductor trades. 4 gain:
48.8 to 60, 42.6 to 60, 44.0 to 60, 41.4 to 60. 2 lose: 79.7 to 60, 61.1 to 60. The strike rate is unchanged.
Days changed: 19 Oct +22.8 % to +32.1 %, 27 Oct +541.9 % to +612.1 %, 9 Nov +43.4 % to +61.1 %. Without its best
trade it is still +16.9 log points. The worst day is unchanged. It cuts one top trade (27 Oct 14:36, +79.7 % to
+60 %). Why it works: on expiry days the +60 % GIVEBACK floor keeps only 70 % of the gain (a floor near +42 %). The
+70 % premium trail gives back 8 % from a raw-bid peak. Most expiry runners that reach +60 % then fall back to the
+42 % floor.

### Test 3. Mark-based exits on the 92 books that record hold marks (trade table)

80 rules. Each one exits at the 60/300/900/1800-second mark when a yes/no condition holds. The conditions use gain,
peak, giveback share, theta against delta paid, forward follow-through, IV change and peak age. Exits are priced at
LTP minus half the spread. 13,056 early trades and 6,121 late trades.

| Rule | Early | Late | Losing book-days, late |
|---|---|---|---|
| Best early: 5 min, forward not in favour | +1,594 | -573 | -8 |
| 5 min, theta paid > delta earned | +1,101 | -585 | -6 |
| 5 min, theta > delta and gain < 0 | +959 | -854 | +16 |
| 30 min, peak still < 10 % (no-progress clock) | +432 | +265 | -19 |
| 30 min, peak still < 8 % | +414 | +306 | -12 |
| 15 min, gave back > 50 % of a peak > 10 % | +590 | +475 | -4 |

35 of 80 rules helped early and 47 helped late, but only 19 helped in both. The "theta dominates" exits fail late.
Late, slow exits (a 30-minute no-progress clock, or a giveback-share exit at 15 minutes) hold up in both windows.
These books are not the champion, so this is a lead for c20, not proof.

### Test 4. Exit twins already in the replay (book level, sum of daily all-in returns)

| Twin vs parent | Strike rate | Early: days better/worse, sum | Late: days better/worse, sum | Losing days | Worst day |
|---|---|---|---|---|---|
| c20_9v vs c20_9x (PGB + LVL_BOOK) | 58.2 vs 51.4 | 3/1, +56 | 3/0, +14 | 3 vs 5 | -43.2 vs -43.2 |
| c20_9t vs c20_9x (rent trail) | 67.2 vs 51.4 | 3/9, -576 | 2/3, -93 | 5 vs 5 | -22.1 vs -43.2 |
| c20_9e vs c20_9x (expiry 6-pt trail) | 60.6 vs 51.4 | 1/2, -425 | 0/1, -12 | 5 vs 5 | -28.5 vs -43.2 |
| c20_9h vs c20_9x (expiry half lock) | 52.1 vs 51.4 | 1/2, -514 | 0/1, -41 | 6 vs 5 | |
| fx_c20_9y vs c20_9y (forecast exit) | 65.8 vs 56.6 | 1/5, -437 | 2/3, -118 | 7 vs 6 | |
| c20_8x vs c20_9x (no ramp, no dtr) | 48.6 vs 51.4 | 2/9, -177 | 2/2, +16 | 5 vs 5 | -56.8 vs -43.2 |

The pattern is the owner's point 3 in exit form. A tighter exit wins more often and earns less, because 26 and 27 Oct
pay for everything. c20_9v passes because its PGB only arms at +15 % and smooths the bid over 20 seconds, so it does
not cut the runners.

### Test 5. Per-second pilot (3 test days: 6 Nov all 16 pool trades, 9 Nov the 22 Conductor trades, 11 Nov 16 trades)

I rebuilt the c20_9x stack second by second from the recorded bids (`work/R02/pathlib_r02.py`) and changed one part
at a time. The rebuild matches the real exit within 2 percentage points on 47 of 54 trades (median gap 0.28). On
these 54 trades the actual exits keep **44 % of the peaks inside the hold and 15 % of the peaks up to the flat
time**. 51 variants. Change in the sum of log returns against the rebuilt base:

| Variant | Strike rate | Change | 6 Nov | 9 Nov | 11 Nov |
|---|---|---|---|---|---|
| base | 61.1 | 0 | | | |
| SL 20 % or SL off | 63.0 | +80 | 0 | +80 | 0 |
| No-progress: at 15 min peak still < 6 % | 66.7 | +22 | +12 | 0 | +10 |
| No-progress: at 30 min peak < 10 % | 63.0 | +6 | +6 | 0 | 0 |
| Expiry clock 25 min or no clock | 61.1 | -4 | | -4 | |
| Theta-aware (decay since peak > k x gain), k = 0.5, 1, 2 | 57 to 61 | -20 to -31 | | | |
| Forward trail x0.5 / x0.75 / x1.25 / x1.5 / x2 | 46 to 63 | -287 / -273 / -66 / -159 / -21 | | | |
| Volatility trail 4 to 14 x the 1-min ATR | 50 to 61 | -35 to -265 | | | |
| TP at 1 to 3 x the 30-min sigma move | 61.1 | -3 to -114 | | | |
| Normal clock 45 min, or both clocks halved | 61.1 | -124 / -102 | | | |
| SL 10 % | 53.7 | -64 | | -64 | |
| Hold to flat with the SL only | 33.3 | -348 | | | |

All three days are test days, so this is a check, not a discovery. The SL result comes from one day. The full
17-day run is Phase B.

## Ideas

| # | Idea | Mechanism | Test result | How to build | Risk |
|---|---|---|---|---|---|
| 1 | **Expiry take-profit at +60 %** | Expiry runners that reach +60 % mostly fall back to the 70 %-of-gain floor near +42 %. Selling at the first bid of +60 % locks the run before theta and IV take it. | Better in both windows on 3 sets. Plateau 55 to 70 %. Conductor +18 / +12 log pts, 6 trades, strike rate unchanged. | Shadow twin `tp60_c20_9y` (and the same for each pool book): c20_9x with EXP `tp=0.60` (the core already has the switch, c20_08.py:33, 121). Normal days untouched. A display line: "Expiry: selling at +60 % (now +47 %)". | Thin: 6 trades. Cuts a +80 % runner. Re-entries after an earlier exit are not modelled. |
| 2 | **c20_9v's PGB on every pool book (normal days)** | A 20-s smoothed bid keeps 60 % of its gain once +15 %. It catches fades the 40-pt forward trail misses, without the 1-s noise. | The c20_9v twin is better in both windows (3/1 and 3/0 days), with 3 losing days against 5. Per-second "PGB on every pool book" is untested (Phase B). | Add "pgb" from c20_9v (c20_9v.py:66-80) to c20_9y, c20_9s, c20_9x and c20_9t as twins. | It overlaps the ramp floor, so the gain may be small. |
| 3 | **Expiry stop on the thesis, not the premium** | The 15 % premium stop fires on the spread, IV and decay of cheap afternoon options. A forward-points stop (12 to 20 pts against) with a 20 to 25 % catastrophe stop, or a stop on a 3 to 10-s smoothed bid, asks whether the direction failed. | Untested on all days. Pilot: SL 20 % +80 on 9 Nov only. Tighter stops lose in both windows (Test 1). | Phase B variants "expiry fwd stop 12/15/20 pts + SL 25 %" and "SL on 3/5/10-s smoothed bid". If one passes: a twin with the EXP `sl` replaced. | A bigger loss per failed entry. The real fix for these 18 trades is the entry (most never went right). |
| 4 | **Late no-progress clock (normal days): at 30 min, peak still < 10 %, sell** | A stuck trade pays decay and blocks the account. Two-thirds of the window is already flat. | Marked books: +432 early / +265 late, 19 fewer losing book-days. Pilot +6 (one trade). On c20, docs/22 found no clean cut on 11 days. | Phase B variant "noprog 1800s pk<0.1" is in the run. If it passes: twin with "np" (30 min, 10 %). | Cuts a slow winner. The per-second runs will show how many. |
| 5 | **Record hold marks for council books** | Without h60/h300/h900/h1800 the champion's hold is invisible in the trade table. | Not a trading rule. | Call `weather5.hold_tick(pos, ctx, o)` where the adapter updates the peak (council/__init__.py:188-192), in a try block like paper.py:1460-1463. Measure step time first (owner's live step-time rule). | About 1 comparison per step. Measure before going live. |
| 6 | **Peak from a smoothed bid** | A 1-second bid spike can arm BE_LOCK or the +70 % trail (council/__init__.py:189). A 3-s smoothed peak avoids false arming. | Untested. | Variant for Phase B, or a display field "peak (smoothed)". | Small. |
| 7 | **Display: what the exit will do now** | Owner point 4. The adapter already writes `pos["rules"]` (council/__init__.py:225). Show the distances to each trigger in plain words. Example: "I hold. Stop is 6.1 pts away. Floor is armed at entry. I sell at +60 % if expiry. The trail fires if Nifty gives back 18 more pts." | Display only. | UI change only. Read the existing rules field. | None to P&L. |

Ideas from outside, not tested here:
- Triple-barrier labels (take-profit, stop, time limit) from Marcos Lopez de Prado, "Advances in Financial Machine
  Learning" (2018). Code: https://github.com/hudson-and-thames/mlfinlab. Ideas 1, 3 and 4 are the three barriers
  set per day type. The labels could train the hold model of docs/49 section 7.
- Chandelier and ATR trails: vectorbt has stop, trailing-stop and take-profit exits that can be swept
  (https://github.com/polakowo/vectorbt). My ATR-trail test (Test 5) lost on all three days, so I would not pursue it.
- Kaufman's efficiency ratio is already the rent trail's chop test (c20_9x.py:191-201). The c20_9t twin loses
  (Test 4).

## Best robust change

**The expiry-day take-profit at +60 %**, run first as a shadow twin of each pool book. It is the only exit change I
found that is exactly measurable, better in both windows on all three sets, flat-topped from 55 % to 70 %, still
positive without its best trade and best day, and no worse on the worst day. It does not lower the strike rate. It
fails one part of the promotion standard ("keeps most of the top trades"): it trims one top trade. It needs live
evidence before it touches the Conductor.

Everything else that tightens exits loses. The money is in the entries (18 expiry stops that never went right) and in
the runners, not in a sharper trail.

## Phase B scripts (after the 15:30 close; not run now)

All are in `D:\ApexOptions\data\research\13nov\work\R02\`. Each run takes one ds_v2 part and at most 20 trades,
one at a time, under 3 minutes on an idle machine.

| Script | What it does |
|---|---|
| `phaseB_list.txt` | 37 commands, one per (part, 20-trade chunk), covering every pool trade that starts inside a built part. |
| `phaseB_paths.py <part> <chunk>` | Runs `a4_paths.py` (63 variants: the 51 above plus expiry TP 55/60/70 %, smoothed-bid stops, expiry forward stops, PGB on every book). Writes `a4_B_<part>_<chunk>.json`. |
| `phaseB_merge.py` | Merges every run and scores each variant walk-forward (19 Oct to 4 Nov against 5 to 11 Nov). Reports strike rate, change in log return, without the best trade, losing book-days, worst book-day, the Conductor subset per day, the per-test-day change, and a promotion-screen PASS flag. 12 Nov is not built. |

## Variants tried (multiple testing)

| Test bed | Variants | Passing both windows |
|---|---|---|
| Tighter stops (table) | 16 | 0 |
| Take-profits (table) | 45 x 2 sets | 3 per set (expiry 40 / 60 / 80 %; only 55 to 70 % form a plateau) |
| Mark rules (92 marked books) | 80 x 2 sets | 19 and 17 |
| Exit twins (replay) | 9 | 1 (c20_9v) |
| Per-second pilot | 51 | test-only check |

About 250 variants in all. With that many tries, a lone pass is a lead. Only plateaus that repeat across sets
(expiry TP 55 to 70 %) count as evidence.

Scratch: `work/R02/a2_out.txt` (reason table), `a3_out.txt` (marks), `a7_tp.py`, `a9_tp60.py` (TP), `a10_sl.py`
(stops), `a5_twins.py` (twins), `a6_merge.py` and `a4_d1106.json`, `a4_d1109c.json`, `a4_d1111.json` (pilot).
