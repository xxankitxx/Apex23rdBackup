# R05: weather items for hold and exit decisions

Analyst R05, 13 Nov 2026 (market hours, low priority, within the 3-part ds_v2 budget). Lens: owner point 2 for holds
and exits. "At mark m, if X, exit now" and "if Y, hold longer / widen the trail", scored walk-forward.

## Findings first

1. **The books the Conductor trades have no hold photograph at all.** All 1,058 c20 trades and all 119 Conductor
   trades have zero coverage at the 60, 300, 900 and 1800 second marks. The council path never calls the code that
   takes it. Every hold mark in the trade table belongs to books the Conductor does not trade. So no weather hold rule
   can be tested on the champion from the table; I rebuilt the c20 hold paths from the 1-second quotes instead.
2. **The c20 exits are not early.** After a c20 exit the held contract's bid keeps falling: on average -1.5 % of
   entry after 60 s, -3.1 % after 300 s, -3.3 % after 600 s (253 exits, 5, 6, 9 Nov). Every "hold N seconds longer"
   variant lost (8 of 8 below zero per trade, -0.5 to -1.7 % per trade). Do not widen the trail.
3. **Cutting trades that have not moved yet destroys the c20 edge.** "At 120 s, if the peak is below +5 %, sell"
   cut the Conductor from +43 % to -39 % on 9 Nov and from +100 % to +3.5 % on 6 Nov. All 6 time-stop variants lost.
   The c20 winners start slowly.
4. **One c20 gap is real and fixable: expiry days have no profit floor between +25 % and +60 %.** On normal days the
   ramp floor locks 45 to 70 % of the peak gain. On expiry days the only floors are the entry (armed at +15 %) and 70 %
   of the gain (armed at +60 %). So expiry trades that peak at +30 to +55 % give half of it back. A floor "once the
   peak bid is +30 % or more on an expiry day, sell when the bid falls to entry + 60 % of the peak gain" took the
   Conductor's 9 Nov from **+43.2 % to +100.5 %**, same 11 of 22 winners, every top trade kept. Neighbouring settings
   (0.5 and 0.7 keep) also helped (+66.6 %, +86.7 %). **This is one test day only. It is not proven.** The three
   in-sample expiry days (19 Oct, 27 Oct, 3 Nov) are scripted for after the close.
5. **On the non-council books, one thesis item survives walk-forward:** at the 300-second mark, if the gen2 impact
   now agrees with the trade (`thesis_impact_with`), sell. Strike rate 59.8 % to 69.3 % (discovery) and 56.3 % to
   63.2 % (test); +0.87 and +0.78 % per trade; the worst test day goes from -2.85 % to -0.47 % per trade; still
   positive without the best day and without the best trade. It passes 8 of 12 discovery days but only 3 of 5 test
   days. It applies to t28, spot, lvl, edge and similar books, not to the Conductor today.
6. **The wide weather scan of exit rules has little real skill.** 9,548 single rules (wx_ entry items and hold-state
   items, 4 marks) were scanned on the non-council books. 273 passed the discovery filter. 61 % of those were positive
   on the test days, against 53 % of all scanned rules. At 300 s there was no skill at all (45 % vs 44 %). None of the
   top 30 survivors helped the c20 trades when transferred.
7. **Two bugs in the hold photograph** make some fields useless for council trades (details in the teardown).

## Teardown

### What the code does

| Part | File and line | What it does |
|---|---|---|
| Hold marks | `apex/engine/weather5.py:408` | `HOLD_MARKS = (60, 300, 900, 1800)`. No 120 s mark. |
| Hold photograph | `apex/engine/weather5.py:419-493` | gain, peak, time to peak, giveback share and rate, future's favourable move and best, attribution to delta, theta, IV and residual, thesis items (episode against, fires with / against, books held with / against, gen2 impact with). |
| Who takes it | `apex/engine/paper.py:1461` | only `paper.check_exit` calls `hold_tick`. |
| Council books skip it | `apex/engine_main.py:1647-1655` | a council book goes to `_council` and `continue`s; `check_exit` never runs for it. |
| Council position upkeep | `apex/engine/council/__init__.py:156-163` | updates `last`, `peak_pts`, `worst_pts`, nothing else. No `hold_tick`. |
| Council peak time | `apex/engine/council/__init__.py:176-181` | writes `pos["peak_t"]` from the bid peak (the hold model input). `hold_tick` writes the same key from the LTP peak. |
| Exit-request photo | `apex/engine/paper.py:1564, 1601` | `hold_mark(..., "exit_req")`; this is the only photograph council trades get. |
| c20 core exits | `apex/engine/council/c20_08.py:26-28, 39-40, 119-126` | expiry: 25-pt forward trail, -15 % premium stop, 900 s clock. Normal: 40-pt trail, -15 % stop, 5,400 s clock. |
| Premium floors | `apex/engine/council/c20_8x.py:280-286` | pex: peak +60 % keeps 70 % of the gain (GIVEBACK); peak +15 % keeps the entry (BE_LOCK). |
| Ramp floor | `apex/engine/council/c20_9x.py:175-188` | normal days only (`not dte0`): +15 % arm entry, +25 to +50 % keep 45 to 70 %, above +50 % keep 70 %. Expiry days fall through to the pex step floors. |
| Expiry premium trail | `apex/engine/council/c20_9x.py:55, 69` | `ptre`: only after the bid EMA reaches +70 %, exit 8 % below its peak. |
| Rent trail | `apex/engine/council/c20_9x.py:56, 166-172` | "rt" switch, keeps 60 % of the gain when the move goes quiet or choppy. Only in c20_9t (its own parts). |

### Where it fails

1. **No continuation photograph for any council trade.** Coverage of h60 to h1800 for the c20 family, the twins
   and the Conductor is 0.000 (all other families 0.37 to 0.98 at h60). The owner's "every item captured live" rule is
   broken for exactly the books that trade money. Cause: `engine_main.py:1647-1655` plus
   `council/__init__.py:156-163`.
2. **`fut_best_fav_pts` is always 0 in the council exit-request photo** (1,058 of 1,058 c20 trades: mean 0, std 0).
   `hold_photo` reads `pos["best"]` (`weather5.py:443`), which is set at the open (`paper.py:1390`) and moved only by `check_exit` (`paper.py:1466`). So
   `fut_giveback_pts` at a council exit is just minus the favourable move. Any study of forward giveback on c20 from
   the table is wrong.
3. **The fires thesis is dead.** `thesis_fires_against_n` is 0 on almost every non-council trade. The rule
   "fires_net <= -1" fired 0 times in discovery at every mark. The item takes the previous step's fire counts
   (`weather5.py:474-476`), which are rarely non-zero at a mark second.
4. **The book vote is dominated by clones.** `thesis_held_with_n` counts every other book (`weather5.py:477-485`).
   For a c20 trade, the nine other c20 books and the twins hold the same side, so held_net is +7 or more on 90 % of
   c20 trades at 60 s. The item says nothing for the Conductor unless the family is left out.
5. **Expiry-day profit gap.** `c20_9x.py:175` applies the ramp only on normal days. On expiry, a trade peaking at
   +30 to +59 % is protected only at the entry price. The Conductor's in-sample expiry trades show it: 19 Oct
   10:34 peak +48.9 % booked +24.0 %; 11:34 peak +44.5 % booked +16.1 %; 27 Oct 13:57 peak +38.3 % booked +8.2 %;
   9 Nov 13:46 peak +39.6 % booked +3.0 %; 9 Nov 13:31 peak +26.1 % booked -0.8 %.
6. **Giveback from the peak is the biggest leak, not the entry.** Conductor trades (119) by exit reason:

| Exit | n | Won | Mean ret % | Mean peak % | Given back % |
|---|---|---|---|---|---|
| FWD_TRAIL | 57 | 46 % | +5.8 | +21.8 | 16.1 |
| SL | 19 | 0 % | -15.3 | +4.2 | 19.6 |
| TIME | 15 | 93 % | +16.8 | +26.9 | 10.1 |
| BE_LOCK | 8 | 38 % | -0.2 | +19.2 | 19.4 |
| RENT_TRAIL | 6 | 100 % | +6.9 | +11.5 | 4.6 |
| RAMP_LOCK | 6 | 100 % | +17.5 | +33.7 | 16.1 |
| GIVEBACK | 4 | 100 % | +42.2 | +63.1 | 20.9 |
| PREM_TRAIL | 3 | 100 % | +63.2 | +89.3 | 26.1 |

   Trades whose peak stayed under +5 % (29 of 119) all lost, mean -12.9 %. Trades peaking at +15 to +25 % won 82 %
   but kept only +5.3 %. At the exit request, winners' gain came from delta (+22.5 % of premium), theta cost -3.5 %,
   IV and residual +2.3 %. On expiry days theta cost -4.2 % per trade against -0.8 % on normal days.

## Evidence

Conventions. Discovery 19 Oct to 4 Nov, test 5 Nov to 12 Nov. Alternative return = the held option's gain at the
mark (the engine's LTP basis for the table; the bid for the rebuilt c20 paths, which is the conservative exit). Returns
in per cent of entry premium; the Conductor in per cent of the day's capital, all-in compounding. My Conductor
re-simulation from the five pool books' trades matches `conductor_sim.json` on all 17 days, trade for trade.

### E1. Non-council books, scan of single exit rules (multiple testing)

| Mark | Trades disc / test | Rules scanned | Passed discovery | Passed rules positive on test | All rules positive on test |
|---|---|---|---|---|---|
| 60 s | 8,295 / 3,541 | 2,422 | 42 | 60 % | 32 % |
| 300 s | 2,610 / 883 | 2,419 | 84 | 45 % | 44 % |
| 900 s | 695 / 335 | 2,386 | 98 | 64 % | 60 % |
| 1800 s | 311 / 181 | 2,321 | 49 | 84 % | 76 % |

Discovery filter: fires on 40 or more trades over 6 or more days, positive in total and on 70 % of its days. At 900
and 1800 s "exit everything at the mark" was itself +1.0 and +4.8 % per trade on test (but -2.3 and -2.7 % on
discovery): the test days punished long holds, so most "survivors" there ride that base rate. The best-looking one,
"at 1800 s, if `wx_chop60` >= 5.3, sell" (test +3.27 % per trade, strike 41 % to 65 %), lost its edge on 11 Nov and
does not reach the c20 trades (only 15 c20 trades on 5, 6, 9 Nov were still held at 1800 s).

### E2. Non-council books, natural rules (pre-set list, 13 rules x 4 marks = 52, plus 18 thesis variants)

Per trade, per cent of entry. "vs random" = gain minus a random rule firing as often.

| Mark | Rule | Disc gain | Disc vs random | Disc days + | Test gain | Test vs random | Test days + | Strike test | Worst test day | Top kept |
|---|---|---|---|---|---|---|---|---|---|---|
| 300 | impact_with | +0.867 | +1.165 | 8/12 | +0.784 | +1.039 | 3/5 | 56.3 to 63.2 % | -2.85 to -0.47 | 0.91 |
| 300 | impact_with and gain >= 0 | +0.829 | +1.062 | 8/12 | +0.754 | +0.951 | 3/5 | 56.3 to 65.0 % | -2.85 to -0.52 | 0.96 |
| 60 | impact_with and held_net <= 0 | +0.066 | +0.162 | 9/12 | +0.147 | +0.219 | 5/5 | 50.3 to 52.8 % | -1.02 to -0.97 | 0.97 |
| 60 | held_net <= 0 | +0.145 | +0.382 | 7/12 | +0.101 | +0.246 | 4/5 | 50.3 to 52.2 % | -1.02 to -1.15 | 0.92 |
| 300 | held_net <= 0 | +0.105 | +0.212 | 7/12 | +0.266 | +0.392 | 4/5 | 56.3 to 56.7 % | -2.85 to -2.98 | 0.98 |
| 300 | gain <= 0 | +0.118 | +0.337 | 7/12 | -1.123 | -0.868 | 2/5 | 56.3 to 40.7 % | -2.85 to -1.97 | 0.64 |
| 300 | giveback share >= 0.5 | -0.421 | -0.058 | 4/12 | -1.436 | -1.119 | 2/5 | 56.3 to 43.8 % | | 0.60 |
| 900 | episode against | -1.944 | -1.175 | 6/12 | +2.976 | +2.516 | 4/5 | | | 1.00 |

Test per day for the 300 s impact rule: 5 Nov -0.23, 6 Nov +1.58, 9 Nov +2.81, 11 Nov -0.76, 12 Nov +2.38.
Without the best test day +0.38, without the best trade +0.75. The "episode against" rule flips sign between windows:
unstable, rejected. Cutting losers at a mark ("gain <= 0", "fut_fav <= 0") fails on test at every mark.

Rest of the trade after the mark (final ret minus gain at the mark), both windows, same sign:

| Mark | Group | Disc n | Disc rest % | Test n | Test rest % |
|---|---|---|---|---|---|
| 60 | all trades | 8,295 | +0.86 | 3,541 | +0.44 |
| 60 | held_net < 0 | 2,008 | -0.54 | 1,056 | -0.27 |
| 300 | held_net < 0 | 377 | -0.47 | 171 | -1.56 |
| 900 | held_net < 0 | 76 | -1.18 | 33 | -1.49 |
| 300 | impact with the trade | 1,167 | -1.94 | 401 | -1.73 |
| 300 | impact against the trade | 879 | +3.70 | 389 | +3.57 |

Reading: when more books hold the other side, the rest of the trade is negative. When gen2's impact already agrees
with the trade five minutes in, the move is spent and the rest is negative; when it still disagrees, the trade has
further to run. This is the most stable thesis pattern in the data.

### E3. The non-council survivors on the c20 trades (5, 6, 9 Nov, bid basis)

Of the top 24 transferred rules, the ones that fired on c20 mostly hurt: "at 60 s, `wx_hk_ratio` >= 1.25" -3.9 % per
trade (strike 57 % to 44 %); "at 900 s, `wx_fut_spread` <= 2.25" -17.9 %; "at 300 s, peak <= +10 %" -7.0 %;
"at 300 s, peak age >= 120 s" -4.2 %. Only "at 300 s, `wx_oi_own_chg_open` >= 5.4 M" was positive (+1.9 %, 51 fires).
Conclusion: non-council exit rules do not carry over to the c20 entry; c20 needs its own rules.

### E4. Per-second exit overlays on the c20 trades and the Conductor (5, 6, 9 Nov; 260 c20 trades, 128 in the pool)

Every variant on a grid fixed before the run is shown. 54 variants. These three days are all test days; no discovery
was possible within the 3-part budget. Conductor base: 5 Nov -5.9 % (0/1 won), 6 Nov +100.2 % (4/4), 9 Nov +43.2 %
(11/22).

| Variant | Fired | Per trade, all c20 | Top trades kept | Conductor 5 / 6 / 9 Nov |
|---|---|---|---|---|
| Expiry floor: peak >= +30 %, keep 60 % of gain | 34 | **+1.12** | 1.00 | -5.9 / +100.2 / **+100.5** (11/22) |
| Expiry floor: peak >= +30 %, keep 70 % | 50 | +0.74 | 0.69 | -5.9 / +100.2 / +86.7 |
| Expiry floor: peak >= +30 %, keep 50 % | 33 | +0.61 | 1.00 | -5.9 / +100.2 / +66.6 |
| Expiry floor: peak >= +20 %, keep 50 to 70 % | 59-73 | -0.70 to +0.24 | 0.69-0.73 | 9 Nov -3.5 to +27.6 |
| Expiry floor: peak >= +40 %, keep 50 to 70 % | 8-23 | -0.34 to +0.16 | 0.73-1.00 | 9 Nov +33.0 to +47.4 |
| c20_9x ramp copied to expiry days | 63 | -0.01 | 0.73 | 9 Nov +49.0 (cuts the 11:33 runner +61 % to +13 %) |
| Lock floor any day, peak >= +30 %, keep 50 / 70 % | 33 / 50 | +0.61 / +0.74 | 1.00 / 0.69 | fires only on 9 Nov |
| Lock floor, peak >= +10 or +20 %, keep 30 to 70 % | 22-145 | -2.46 to +0.36 | 0.08-1.00 | 9 Nov -6.2 to +37.3 |
| Premium trail from peak, arm 10-50 %, 10-30 % below | 0-127 | -2.25 to +0.56 | 0.42-1.00 | 6 Nov as low as +34.3 |
| Time stop: at 120 / 300 / 600 s, peak < +5 or +10 % | 20-136 | -0.43 to -5.35 | 0.69-1.00 | 9 Nov as low as -39.3 |
| Hold 60 to 600 s past a FWD_TRAIL exit | 52-116 | -1.71 to +0.00 | 0.96-1.00 | 9 Nov as low as -28.3 |
| Book vote (clones left out): at 300 s, held_net <= 0 | 43 | +0.33 | | -1.3 / +81.7 / +44.7 |

The expiry floor at 0.3 / 0.6 fired on four Conductor trades on 9 Nov: 10:38 PE +12.4 to +18.6 %, 11:13 CE +14.2
to +22.0 %, 11:56 PE +19.7 to +24.1 %, 13:46 CE +3.0 to +21.9 %. It left the 11:33 +61 % runner and the 13:11 +41 %
GIVEBACK alone. Normal days were not touched (by design).

Approximation: the account re-simulation keeps every book's own later trades unchanged when one exit moves. A book
that exits earlier could re-enter differently (cooldowns, its own forward best). The live engine would show that; the
overlay cannot.

### E5. The rebuilt book vote for c20 (from the trade table, checked against the engine)

Rebuilding held_with / held_against from every book's t_in, t_out and side reproduces the engine's own h300 numbers
exactly on 400 sampled non-council trades (mean absolute difference 0.0). With all books counted, held_net is
almost never negative for c20 (the clones vote with it). With the c20 family and twins left out, "at 300 s,
held_net <= -1, sell" fired 34 times: rest of trade -2.2 % when fired vs +8.0 % when not, but the Conductor went
+43.2 to +56.9 % on 9 Nov and +100.2 to +81.7 % on 6 Nov. Mixed; not a rule yet.

## Ideas

| # | Idea | Kind | Mechanism | Test result | How to build | Risk |
|---|---|---|---|---|---|---|
| 1 | Give council books the hold photograph | data | `hold_tick` on every held council second | n/a (instrumentation) | in `council/__init__.py:156-163`, after the peak update: `_w5.hold_tick(book.pos, ctx, o)`; make `hold_tick` write its LTP peak time to `peak_t_ltp`, not `peak_t` (council owns `peak_t`, line 178). Also keep `pos["best"]` (the forward's best) for council positions so `fut_best_fav_pts` is real. | Step time: 4 photos per trade, one loop over ~107 books each: well under 1 ms. Measure first (live step-time rule). |
| 2 | Expiry profit floor (shadow `c20_9y_xf`) | exit | expiry ramp gap: once peak bid >= entry x 1.30 on an expiry day, sell when bid <= entry x (1 + 0.6 x peak gain) | 9 Nov only: Conductor +43.2 to +100.5 %, strike unchanged 11/22, top kept 1.00, neighbours +66.6 / +86.7 %. 54 variants tried. Untested on 19, 27 Oct and 3 Nov. | subclass of c20_9y: in `_floor0` (`c20_9x.py:175`), on `dte0` add the floor `e*(1+0.6*g)` when `g >= 0.30` and keep the higher floor. Shadow book first, not the pool. | If the phase B days show it cutting 27 Oct style runners, it fails. One test day so far. |
| 3 | Exit at 300 s when gen2 impact agrees (non-council shadow twins) | exit | the impact that agrees five minutes in marks the end of the push | walk-forward: disc +0.87 %, test +0.78 % per trade, strike +9.5 / +6.9 pts, worst test day better, 8/12 and 3/5 days | shadow twins of t28 / lvl / edge / spot with `exit_if = h300 thesis_impact_with` in paper.check_exit (the item is already computed at the mark) | 3 of 5 test days only; does not cover the Conductor until idea 1 exists |
| 4 | Book-vote exit with clones removed | exit | the rest of the trade is negative when other families hold the other side (both windows, all marks) | c20 test: mixed (9 Nov better, 6 Nov worse) | new photo item `thesis_held_net_xfam` (other families only); evaluate after idea 1 has a week of data | clone counting today makes the item blind for c20 |
| 5 | Do not widen the c20 trail or hold past it | hold | price keeps falling after c20 exits | 8 of 8 "hold longer" variants lost; bid -3.1 % 300 s after exit | none (a "no" result) | none |
| 6 | Do not add time stops to c20 | exit | c20 winners start slowly | 6 of 6 time stops lost; worst cut 9 Nov to -39 % | none (a "no" result) | none |
| 7 | Commentary line on the hold | ui | say the floor in plain words: "I am up 34 %, my floor is +20 %; I sell if the bid touches 147.2" | untested (display) | cmt_hold.py reads the active floor and its kind from the strategy state | none; only a display |

## Phase B scripts (after 15:30, same rules, one at a time)

All under `D:\ApexOptions\data\research\13nov\work\R05\`. Each stays under 3 minutes and 1.5 GB.

| Order | Command | What it does |
|---|---|---|
| 1 | `py -3.13 phaseB_c20_overlays.py` | builds `paths_all.pkl`: every c20 trade's per-second bid from entry to 1,800 s past the exit, all ds_v2 parts, one part at a time (~2 min) |
| 2 | `py -3.13 phaseB_c20_overlays.py --group=KE` | the expiry floors and the ramp-on-expiry, walk-forward: strike, days better, losing days, worst day, without best day, top kept, per day. **Decides idea 2.** |
| 3 | `... --group=K`, `--group=P`, `--group=T`, `--group=L` | the other overlay families on all days |
| 4 | `py -3.13 phaseB_c20_paths.py all` | the c20 hold marks (13 marks) rebuilt from ds_v2 for every day |
| 5 | `py -3.13 phaseB_c20_rules.py all` (add `--nopairs` if it nears 3 minutes) | exit-now rules on the rebuilt c20 marks with the wx_ photograph, walk-forward, and the best through the Conductor's account |

Already run today (results above): `analysis1.py` (scan, 9,548 rules), `analysis2.py` (scoring, account check),
`analysis3.py`, `analysis4.py` (overlays, natural and thesis rules), `analysis5.py` / `analysis5x.py` (book vote),
`phaseB_c20_paths.py pilot 2026-11-05 2026-11-06 2026-11-09` (the 3-part budget).

Variants tried in total: about 9,800 (9,548 scan, 70 natural and thesis, 54 overlays, 50 book-vote, about 90
transfers). With that many tries, a single test day can make almost anything look good; only ideas 2 and 3 are worth
the phase B run, and idea 1 is needed before any hold rule for the Conductor can be trusted.
