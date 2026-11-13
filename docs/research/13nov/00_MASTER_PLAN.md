# 00. Master plan from the 20-analyst study (13 Nov 2026)

Synthesis lead. I read all 20 reports in full (R01 to R20 in this folder) and ran two small cross-checks of my own on the
Conductor's 119 replayed trades (scripts in `data/research/13nov/work/SYN/`). Nothing in `apex\`, `tests\` or the live
session was touched.

## The main points first

1. **No idea is ready to change the live Conductor.** 20 analysts tried about 16,000 rule and policy variants, plus more
   than 500,000 weather line tests. Not one idea passes all seven tests of the promotion standard (docs/28 section 2) in
   two windows. The closest are four expiry-day and loss-memory shadows (table P below).
2. **The honest forward edge is small.** 95.6 % of the +10.92 lakh came from days the c20 books were fitted on. After the
   c20_9x freeze the Conductor averages +12.8 % a day (mean), +6.5 % (geometric), and the median day is -4.0 %. There is
   about a 1 in 5 chance the true mean day is zero or worse (R19). Every plan below is sized against that.
3. **Why it "does something stupid" on some days.** The pool is one signal five times (140 distinct trigger seconds for
   543 pool trades; daily correlation 0.89 to 1.00). The day decides, not the rule: the Conductor's day tracks the median
   book's day (rho 0.64) and no single market measure predicts it. Which book wins does not carry over from one day to
   the next (rank correlation 0.16). So switching to recent winners, bandits, regime-gated pools and weather filters all
   fail (R03, R04, R15, R19, R20). What does carry inside a day is loss memory by side (R17, R20) and the clean-trend
   morning (R03). Those are the shadows to run.
4. **The real money leaks are on expiry days.** 18 expiry premium stops cost 301 log points, more than half of the
   account's whole log gain (R02). Expiry trades that peak at +30 % to +60 % give back half, because expiry days have no
   floor between the entry and +60 % (R05). Expiry afternoon after 13:30 wins 29 % of pool trades (R18). Three of the four
   best shadows are expiry-day fixes.
5. **Tighter exits, time stops, chop guards, day stops and cooldowns all lose.** About 250 exit variants (R02), 54 overlays
   and 8 hold-longer variants (R05), 211 guard settings (R17): the giveback is the price of the runners.
6. **The forecaster's short-term skill is real but is not foresight.** It reads the options' forward and the heavyweights
   moving before the futures quote. Measured from 30 seconds after the call, its 1-minute skill falls from IC +0.18 to
   +0.016 (R10), and on the forward that premiums follow it is about zero (R07). A 15-minute stand is right 50 % of the
   time (R11). So the screen must take a stand as a *description* of the market and of the Conductor's own plan, with its
   measured record beside every number, not as a prediction.
7. **The system already knows what it would do; it just never says it.** The c20 arm state (impulse, pullback, the price
   that fires) lives in engine memory. A replica reproduced 10 of 10 Conductor triggers within 3 s (R12). Publishing it as
   a first-person "What I would do now" card is the single biggest answer to owner point 4, and it changes no decision.
8. **Heavyweights and sisters carry information only at 5 to 60 seconds.** Weighted cash basket and BANKNIFTY/FINNIFTY
   moves lead the Nifty future by 1 to 10 s (R08, R09). Use them in the forecaster's short-term stand and commentary. As
   entry gates they failed walk-forward. Two sister readings are broken (FINNIFTY reads an illiquid future: 74 % of photos
   show fn60 = 0).
9. **Live reliability: the machine, then a few small code fixes.** Today the CPU ran at 100 % and about 25 % of its rated
   clock, so every engine phase slowed about 15 times (R13). The Forecast Lab runs below normal and lost 29 % of its
   seconds. The 965 refused dashboard writes come from the gateway holding the file open. Speed beyond 10 steps a second
   is worth only 0.1 to 0.4 % of premium per trade; uptime is worth whole trades.
10. **Four defects block the research itself.** The council books (the only books that trade money) record no hold
    photograph, so no hold or exit rule can be tested on the champion from the trade table. R-019/R-020 have zero effect
    because a sister book takes the vetoed trigger. FINNIFTY and BANKNIFTY read stale last prices. 9 Nov is missing from
    day_levels.json, so 11 Nov ran on 6 Nov's prior-day levels.

## 1. One set of baseline numbers

The reports quote the Conductor's late window in four ways. They are all right; they measure different things.

| Number | What it is | Used by |
|---|---|---|
| +142.5 % | Sum of the 5 test days' returns, integer lots (the account as it runs) | R03, R15, R17, R19 |
| +153.8 % | Same sum, compounding `ret_pct` without lot rounding | R08, R18, R20, my checks |
| x2.82 | Product of the 5 test days' growth, integer lots | R04 |
| +200.7 % | Product of the 5 test days' growth, no lot rounding | R06, R07, R09, R16 |
| +1,092.5 % / +1,140.7 % | Sum over all 17 days, with / without lot rounding | docs/54 / R18, R20 |

Test window per day (no lot rounding): 5 Nov -6.0 %, 6 Nov +109.2 %, 9 Nov +43.4 %, 11 Nov +12.0 %, 12 Nov -4.8 %.
Strike rate 51.4 % (35 trades). Early window: 84 trades, 53.6 %, sum +986.9 %, 3 losing days, worst -37.1 % (3 Nov).

Caution on the "test window": the c20 books were found on days up to 6 Nov (R15, R19). Only 9, 11 and 12 Nov (and 13 Nov
live) are truly out of sample for the pool itself.

## 2. The owner's six points, mapped to work

| Owner point | What the team found | Work that meets it | Where |
|---|---|---|---|
| 1. Teardown and innovative ideas (maths, greeks, internet, GitHub) | Full code teardowns of entry (c20_08/8x/9x chain), exits, greeks, flow, heavyweights, sisters, Lab, commentary, engine loop. Ideas from Zarattini-Aziz-Barbon (VWAP), Cont-Kukanov-Stoikov (OFI), Stoikov micro-price, Gao et al., Baltussen et al. (gamma), Corsi HAR, Lopez de Prado (triple barrier, DSR, PBO), Adams-MacKay BOCPD, Hayashi-Yoshida lead-lag, Jaeckel "Let's Be Rational". Calculus of the honest break-even (R06). | Build list (c) shadows, (d) Phase B. Honest theta clock. GEX sign fix. | R01, R02, R05, R06, R07, R14, R16, R19, R20 |
| 2. Every permutation of every weather item for entries, holds, exits | Entries: all 457 photo fields (524 after splitting text), 19 quantile lines, both sides, singles, pairs, triples, at the account, the pool, 16 families and all books. Exits: 9,548 single rules at 4 marks, 80 mark rules, about 250 exit variants, 54 per-second overlays. Coverage on the c20 books' holds is **0 %** until the council hold photograph is fixed. | Stop-looking list (14 empty fields, 6 misleading items). Walk-forward column for the nightly search. Council hold photograph. Phase B per-second hold rebuilds (R05, R17, R19). | R02, R04, R05, R07, R08, R09, R18 |
| 3. Not the same way every day, then something stupid | The day decides; book success does not persist; pool is one signal. In-day loss memory by side and the clean-trend morning are the only adaptive signals that held. 0 of 115 switching designs and 0 of 336 meta-selectors passed. | Shadows: side-loss lock, whipsaw pause, trend lock, expiry-afternoon cut. Account memory shown on screen. "Do not build" list. | R03, R15, R17, R19, R20 |
| 4. Forecaster takes a clear stand, describes behaviour, first-person "what I would do now" | Old verdict says WAIT all day (lean diluted by kappa and Hedge weights); held read flips on Rs 1 to 3 of premium; commentary never says "I", is silent when flat, and judges the Conductor by a 12-point spot trail it does not use (obeying it turned +182 % into -1 %). | Voice observer and "What I would do now" card, stand banner, exit ladder, record strip, demote the +- range. | R10, R11, R12 (plus lines from R03, R06, R07, R08, R09, R17, R18, R20) |
| 5. Heavyweights by Nifty weight; sweet spot for BANKNIFTY and FINNIFTY | Weighted pressure P (10 s cash and stock-futures gap) right 60 to 65 % at 10 to 60 s, no edge at 5 min. Sister futures mids lead by 1 to 2 s; best look-back 5 to 15 s, horizon 5 to 60 s, equal weight on the two sisters. Bank relative strength has the wrong sign; spread mean reversion is not stable. | P chip replaces the unweighted "Heavyweights rising" chip. Sister lead features in a shadow Lab brain. Data fixes (mids, units, sector map, 5 s staleness). Shadows: futures-led veto, bank-against veto. | R08, R09 |
| 6. No errors live, blazing fast | No engine fault 9 to 13 Nov; nothing stopped a trade. Slowness is the machine (throttled CPU). Real risks: Lab starvation, dashboard swap refusals, feed reconnect that ignores stop, registry save that can kill the feed, login restart loop. | Build list (b): Lab priority, research CPU cap, in-memory dashboard hand-off, feed fixes, R14 identity-checked speed batch behind the replay gate. | R13, R14 |

Nothing in the owner's request is left without an owner and a next step. The one gap that cannot be closed today is hold
and exit permutations on the champion: it needs the council hold photograph (build (b) item 6) or the Phase B rebuilds.

## 3. Profit ideas ranked

Grades: **A** = tested walk-forward, better in both windows, survives a multiple-testing check, exact measurement.
**B** = better in both windows on strike rate or return, but fails one promotion test, thin sample, or approximate.
**C** = one window, one day or in sample only. **U** = untested. Effect = change in the Conductor's sum of day returns
(no lot rounding), early 12 days / late 5 days, unless stated.

### P. Promising: run as shadows (none is promotable yet)

| Rank | Idea | Grade | Evidence (strike first) | Effect early / late | Fails | Risk | Analyst |
|---|---|---|---|---|---|---|---|
| 1 | Expiry-day take-profit at +60 % (`tp=0.60`, EXP mode only) | A- | Strike unchanged (6 trades change). Better in both windows on 3 trade sets; plateau 55 to 70 %; exact from each hold's best bid. My rebuild matches (19 Oct +22.8 to +32.1, 27 Oct +541.9 to +612.1, 9 Nov +43.4 to +61.1). | +79 / +18 | Trims one top trade (+79.7 to +60) | Only 6 trades; re-entries after the earlier exit not modelled | R02 |
| 2 | Expiry profit floor: once peak bid >= +30 %, sell at entry + 60 % of the peak gain (`c20_9y_xf`) | B- | Per-second on 9 Nov: +43.2 to +100.5 %, strike unchanged, all top trades kept. My bounds from the table (all 4 expiry days): 9 Nov +75.7 to +105.4; 19 Oct +6.7 to +52.6 (could be worse); 27 Oct +554 to +651. | -4 to +139 / +32 to +62 | Untested on 3 of 4 expiry days; 54 variants | Pessimistic bound loses on 19 Oct | R05 |
| 3 | c20 side-loss lock (`conductor_sl`): refuse a side when today's last 12 closed c20-family trades on it (at least 3) have more losses than wins | B | Strike 59.3 vs 52.9 % (17 days), late 54.2 vs 51.4 %; worst day -13.6 vs -37.1 %; 12 of 18 side-specific variants raise strike in both windows; locked-side pool trades win 49.6 % / 40.7 % vs open side 64.2 % / 61.0 %. | -94 over 17 days (all on 27 Oct) / +8 | Return over 17 days; luck margin not yet run | Gives up counter-move days like 27 Oct | R20 |
| 4 | Whipsaw pause: after two account losses in a row on opposite sides, no entry for 60 min (`conductor_wp60`) | B- | Strike 58.0 vs 53.6 % early, 53.3 vs 51.4 % late; no day worse; 36 book-days better, 6 worse across 10 c20 books. | +57 / +29 | Strike gain inside luck; holes at 45 and 50 min; late gain is one day (9 Nov) | Path chaos: 9 Nov ranged -0.4 to +72.5 % across nearby settings | R17 |
| 5 | Expiry afternoon cut at 13:30 (restore c20_20 "pm") | B- | Pool trades after 13:30 on expiry won 29 % (58) vs 63 %, lower on 4 of 4 days. Account: strike 56.0 vs 53.6 % early, 56.7 vs 51.4 % late; worst day -28.5 vs -37.1 %; without best day 727 vs 599. | -228 / +92 | Early return (loses 27 Oct 14:36 +79.7 %) | Only 4 expiry days | R18 |
| 6 | Expiry day one strike deeper ITM (`c20_9y_x1`) | C+ | Repriced at the same seconds: 3 Nov -40.0 to -26.2 %, 9 Nov +31.0 to +45.2 %; strike 61.5 vs 53.8 % on 6 and 9 Nov. Normal day worse. | n/a (2 expiry days) | Rests on 2 days, 37 policies | Premium-path exits fire at different times on a deeper strike | R06 |
| 7 | c20_9v PGB (20-s smoothed premium giveback) on every pool book, normal days | C+ | The c20_9v twin is the only exit twin better in both windows (3/1 and 3/0 days, +56 and +14 day-%, 3 losing days vs 5). PGB on the other books untested. | +56 / +14 (twin) | Untested on the other books | Overlaps the ramp floor | R02 |
| 8 | Confirmation (`conductor_conf`): take a c20 trigger only if an independent family fired the same side within 300 s | C | Never worse than the pool on any test in either window; strike 59.6 vs 58.6 % and 52.9 vs 51.4 %. | +23 / +8 | Inside luck (sign-flip p 0.5) | Small effect | R15 |
| 9 | VWAP side gate (`c20_vw`): buy only on the futures' side of session VWAP | C | Strike higher in both windows (59.3 vs 53.6 %, 63.2 vs 51.4 %), worst day -11.7 vs -37.1 %, 0 losing test days; holds across all 107 books (about 5 points of strike). | -467 / +67 | Early return halves (27 Oct +532 to +107) | Kills counter-move winners | R16, R03 |
| 10 | Futures-led veto: skip a c20 trigger when the domino basket gap with the trade is above 1.6 pts | C | Strike up in both windows (0.536 to 0.574, 0.514 to 0.583). | -440 / +56 | Early return; chosen from 594 variants | Vetoes basket-led big winners | R08 |
| 11 | c20 trend lock after 10:15 or 11:00 on clean-trend mornings (ER since open >= 0.30, move >= 60 % of range) | C | In sample: strike 55.7 vs 52.9 %, worst day -17.7 vs -36.3 %, 12 of 12 top trades kept; c20 vetoed trades won 22 to 34 %. No test day has triggered it. | +49 to +81 (in sample) / 0 | Two windows (no test day) | A trend morning that turns into a V (2 Nov) | R03 |
| 12 | Side lock plus hand-off to lvl_trail on its own losing side (`conductor_slh`) | C | Strike 57.1 %, sum +1,373 vs +1,141, late +205.5 vs +153.8. | +232 over 17 days | Worst day by 1.3 pts; gain is path dependence (lvl trades win 50 %) | Sequence luck | R20 |
| 13 | Filler that steps aside (retest family with pre-emption) | C | Test +83 % (log +0.60) vs pool; 24 books: 71 % positive on test. | +84 % / +83 % (log) | Account strike lower (50.0 vs 51.4 %), worst day worse (5 Nov -19 %) | Approximate pre-emption price | R01 |
| 14 | With-gap-unfilled veto; restore the ORB lock in a twin | C | Trade level consistent (ORB against: worse on 10 of 11 days). Account: mixed. | gap: +21 / +25; ORB: -123 / -12 | Worst early day (gap); late return (ORB) | Substitution erases trade-level gains | R18, R03 |
| 15 | Bank-against veto (existing advisor, z < -0.5) | C | Strike up in both windows (54.9 vs 53.6 %, 53.1 vs 51.4 %). | -10 / +24 | Worst early day worse (-43.1 vs -37.1 %) | Re-test after the mid-price data fix | R09 |
| 16 | R04-A: `sign_none_share300 >= 0.0197` as an account gate | C- | My skip-only check: strike 56.3 vs 53.6 %, 60.0 vs 51.4 %; sum +92 / +106. | +92 / +106 | Picked after seeing the test days; its 60-s twin fails | Probably luck | R04 |

How to read the effects: the forward expectancy is about +6.5 % a day. Ranks 1 and 2 work only on expiry days (one day in
five) and add roughly +15 to +60 points on such a day. The guard shadows (3, 4, 5) mostly lift the strike rate and the
worst day, and pay for it on rare counter-move days like 27 Oct.

### U. Promising but untested (Phase B decides)

| Idea | Mechanism | Script or build | Analyst |
|---|---|---|---|
| Shallower pullback / longer arm life; age-out trend entry | 18 of 26 replayed arms aged out with a median 36 % pullback, so trends go untraded | `R01/phaseB_pb_sweep.py` | R01 |
| Morning warm-up W=600 until 09:45 | Pool trades before 09:45 won 74 %; NORM cannot fire before about 09:36 | engine replay twin (owner's OK) | R18 |
| Expiry stop on forward points or a smoothed bid | Most of the 18 expiry stops never went right; SL 20 %/off pilot +80 log pts on 9 Nov only | `R02/phaseB_paths.py` variants | R02 |
| Late no-progress clock (30 min, peak < 10 %) on normal days | Positive in both windows on 92 marked books (+432 / +265) | `R02/phaseB_paths.py` | R02 |
| Early exit when IV falls in the first minutes | IV change after entry is the second-biggest driver (IV up > 1 pt: 93 % won) | `R17/phaseB_iv_after_entry.py` | R17, R06 |
| 300-s "gen2 impact already agrees" exit, non-council books | Walk-forward both windows on non-council books (+0.87 / +0.78 % per trade, strike +9.5 / +6.9 pts) | shadow twins of t28/lvl/edge/spot | R05 |
| VWAP trailing exit | Zarattini-Aziz-Barbon stop | `R16/phaseB_vwap_exit_gao.py` | R16 |
| Forward-resumption speed veto | 45 pool trades: faster forward move before the trigger, better return (rank corr +0.35, +0.61) | `R07/phaseB_ms_gate.py` | R07 |
| Second low-correlation entry family | Pool is one book; t28/lvl correlate 0.2 with council | `R19/harness.py --books X`; shadow pool | R19, R15 |
| Day-type switch council vs t28/lvl (hindsight ceiling +2,114 % vs +1,092 %) | The day decides which family wins | `R15/phaseB_dropped_trades_weather.py`, R03 classifier | R15 |

### X. Rejected (do not build), and why

| Rejected idea | Why (numbers) | Analyst |
|---|---|---|
| Any weather entry filter, pair or triple from the nightly search | Top 10 discovery lines helped on test 1 time in 10; rank correlation discovery vs test -0.06 over 372 fields; FDR survivors replicate less often than non-survivors (24 % vs 33 %); pairs and triples worse than singles in all 8 groups | R04 |
| R-019/R-020 family vote as coded | Zero effect at the account (35 to 35 trades); as an account gate it hurts (x2.82 to x2.06) | R04, R19 |
| Greek and IV entry filters (theta_ratio, theta_be, delta, IV level, IV vs median) | 538 variants per sample; none changed more than one test trade | R06 |
| Order-flow and book items as entry filters | 13 of 66 sign-stable vs 12.4 by chance; 9 of 55 early picks beat the late base | R07, R16 |
| Tighter stops, trails, ATR trails, sigma TPs, theta-aware exits, shorter clocks, earlier floors | All 16 stop settings lose in both windows; trail x0.5 to x1.5 -66 to -287 log pts; ATR trails -35 to -265 | R02 |
| Time stops and "hold longer" on c20 | 6 of 6 and 8 of 8 lost; "at 120 s peak < 5 %" took 9 Nov from +43 % to -39 % | R05 |
| Chop guards, day stops, loss caps, 14:15 cutoff, spread and quote-age guards, cooldowns of 18 min or more | Every one lost in at least one window; chop guards remove c20's best trades (er60 < 0.10 won 66 %) | R17 |
| Family switching, regime-gated pools, bandit routers, best-of-recent, rotation, static additions, fillers without pre-emption | 0 of 115 (R20) and 0 of 336 (R15) passed; rolling chooser halves profit (+500 vs +1,035); 35 discovery-picked fillers: 4 positive on test (11 %) vs 22 % of all | R15, R20, R01 |
| Adaptive selection by detected day type | 108 variants: 17 better, 53 worse; the best fails worst day | R03 |
| The forecaster stand or trend agreement as an entry filter | "Skip when the stand agrees" lowers return in both windows; trend agreement flips sign (66 % / 36 %) | R10, R11, docs/54 |
| Obeying the old HOLD/WATCH/EXIT-SOON verdict | +182 % became -1.1 % on 5, 6 and 9 Nov; it fired on 119 of 119 trades | R12 |
| Opening-drive, last-half-hour, noise-boundary, ORB, PCR, OI, mean-reversion, IV-regime books | Every variant flipped sign between windows or failed (noise boundary 3 of 10 right) | R01, R16, R18 |
| Next weekly as a mode; bank relative strength; bank spread mean reversion; VIX as a lead | Lower strike and return; AUC 0.42 to 0.45 (wrong sign); reverts one day, trends the next; IC -0.09 to +0.03 | R06, R09 |
| Slow 10 to 15 minute stand; today's follow-or-fade | IC below 0 on 7 of 11 days; late 44.7 % | R10 |
| Adding more c20 variants to the pool | They add exits, not entries (140 trigger seconds for 543 trades) | R01, R15 |
| Engine speed beyond 10 Hz as a profit lever | 1 to 3 s of delay costs 0.1 to 0.4 % of premium per trade | R13 |

### Proven facts (not profit claims, but certain)

| Fact | Evidence | Analyst |
|---|---|---|
| Council books record no hold photograph; `fut_best_fav_pts` is always 0 for them | 0 of 1,058 c20 trades have h-marks; 1,058 of 1,058 zeros | R02, R05, R17, R19 |
| A per-book pool rule is undone by sister books (`conductor.py:177-191`) | R-019 replay identical to no rule on 5 to 12 Nov | R04, R19, R12 |
| FINNIFTY reads an illiquid future's LTP; BANKNIFTY reads LTP | 74 % of photos have fn60 = 0; LTP changes 1 % (FIN) and 28 % (BANK) of seconds | R09 |
| Futures aggressor split compares the mid, not the last print | `market.py:46-52` with `flow.py:94-103` | R07 |
| Theta clock: kit clock is right on DTE >= 1, about 4 to 5 x too big on expiry day | Implied clock 3.45 to 4.89 x calendar on DTE >= 1, 0.73 to 0.99 on expiry (13,306 trades) | R06 |
| 9 Nov missing from day_levels.json; 11 Nov used 6 Nov's levels | `daystate.py:121-133`, `c20_8x.py:34-40` | R18 |
| Event calendar is empty for the 17 days | `wx_event` False on 20,817 of 20,817 trades | R18 |
| GEX sign reads backwards on Nifty | AMPLIFY worst (36.3 % won, n 1,078); DAMPEN best in both windows | R16 |
| The Lab resets its own calibration at every start | load bounds `core.py:40-42` narrower than online clips `core.py:876, 878` | R13, R10 |
| The c20 family is persistently better than other books; which sibling is a coin flip | PBO 0.06 across books, 0.53 within the family | R19 |

## 4. Conflicts between analysts, resolved

| # | Conflict | Who is right, and why |
|---|---|---|
| C1 | R10 says the fused 2-minute needle is calibrated and right 60 % when it says 60 to 65 %. R07 says the Lab's skill is the futures mid catching up with the options, about zero on the forward. R11 says a 15-minute stand is a coin toss. | **All three, about different targets.** R10's own delay test proves R07's point: from 30 s after the call, IC falls from +0.181 to +0.016. So the needle is a true nowcast of the futures quote and worthless for premiums. Show it, label it "next 1 to 2 minutes, already in option prices", score it on the forward too (R07 I1), never use it as a filter. The banner word comes from R11's strength (a description with its 50 % record), not from R10's needle, whose word changes 16 to 23 times an hour. |
| C2 | R08's heavyweight pressure P and R09's sister lead as "the stand" vs R07 (heavyweights predict the future, not the forward). | Same resolution as C1. P is right 60 to 65 % at 10 to 60 s on the futures; show it as a seconds-scale push, never as a 5-minute view. R09 also warns part of the sister lead may be packet delivery order. |
| C3 | R04 and R19: make pool rules account-level. R12: the trades that leak through c20_9y's vetoes made money out of sample (late 2 of 4 won, +4.9 %). | **Both.** Build the mechanism (`pool_gate`), so a rule means what it says. Do not switch c20_9y's IV and OI-wall vetoes to account level: the only out-of-sample evidence is against it. |
| C4 | R14: ship the speed batch; "engine and feed above normal priority is the largest lever, owner's decision". R13: do not chase speed, fix uptime. | **R13 on priority, R14 on safety.** `run_apex.py:97-106` already runs the feed and engine ABOVE_NORMAL in live mode, so R14 idea 12 is already done. The slowdown is a throttled, saturated CPU. Do R13's uptime fixes first. R14's identity-checked batch is still worth it (it removes 100 to 276 ms spikes that land on trade ticks) but only behind its A/A2/B replay gate. |
| C5 | R06: warm-started Newton or "Let's Be Rational" IV for speed. R14: no, it changes the last bits of IV and delta, and delta picks the strike. | **R14 for the live engine.** Use R14's bit-identical stacked erf. A new IV solver is fine in the Forecast Lab or research, or in the engine only if a replay shows identical strikes. |
| C6 | R02's expiry take-profit at +60 % vs R05's expiry floor at 0.6 of the peak gain. | **Complementary, not rivals.** The floor protects peaks of +30 to +60 %; the TP caps at +60 %. R02's evidence is stronger (exact, both windows, 3 sets). My bounds for the pair on all 4 expiry days: early +76 to +232, late +54 to +87 day-% (table V2). Run both as separate shadows and one combined shadow; Phase B R05 `--group=KE` gives the exact floor result. |
| C7 | R17: chop guards fail (low efficiency trades win 66 %). R03: a trend lock on high-efficiency mornings works. | **No conflict.** R17 measures 60-minute ER at the trigger; R03 measures efficiency since the open at a checkpoint. A c20 pullback is low-ER tape by design; a clean one-way morning is a day-level fact. |
| C8 | R10 stance word (2-min odds, Schmitt 0.56/0.53) vs R11 stance word (20-min slope and VWAP strength, +-40/20, 90 s hold). | **R11 for the word, R10 for the needle.** R11's word changes 14.5 times a day and says honestly that it is right 50 % at 15 minutes. R10's needle underneath carries the short-term odds. |
| C9 | R11 `council_watch` field vs R12 `state["voice"]` observer. | **One observer, R12's contract, R11's layout.** R12 is right not to call the live `_pick` (c20_8x "rw" writes `self.blk`); use a display copy. |
| C10 | R19 and R15: diversify with a second low-correlation family. R15 and R20: every non-council Conductor and rotation lost. R01: plain fillers fail; pre-emption fillers pass return only. | **Diversification survives only in constrained forms**: a filler that steps aside (R01) or a hand-off on the side where c20 is locked (R20). Both are shadows. Rotation and replacement are dead. |
| C11 | R15's confirmation drops only 1 to 4 trades a window; my curated (t28, lvl, spot, edge only) 300 s version drops 29 early and 15 late. | R15's CONF_W300_K1 counts any non-pool family (including m-grid and c20 twins), so it confirms almost everything. The curated version is a much stronger filter and costs the 19 and 21 Oct winners. The shadow should be R15's any-family version, as R15 recommends. |
| C12 | R16 and R03 both found the VWAP side; R03 says -436 points over 17 days, R16 says compounded early falls from +7,489 % to +3,811 %. | Same rule, same verdict, two ways of counting (sum vs product). My skip-only check: early sum 520 vs 987, late 221 vs 154, strike 59.3 % and 63.2 %. |

## 5. My own cross-checks

### V1. Do the guard shadows remove the same trades? (skip-only on the Conductor's 119 trades)

Skip-only means a flagged trade is dropped and nothing replaces it (the analysts' own re-simulations let a sister book
take the slot, so their totals differ a little). Signs checked: `wx_bank_z` and `wx_basket_gap` are already signed with
the trade (my counts then match R08 and R09).

| Rule | Early kept / strike / sum / worst | Late kept / strike / sum / losing days | Cut early W/L | Cut late W/L |
|---|---|---|---|---|
| None | 84 / 53.6 % / +986.9 / -37.1 | 35 / 51.4 % / +153.8 / 2 | | |
| Expiry cut 13:30 | 75 / 56.0 % / +758.5 / -28.5 | 30 / 56.7 % / +245.9 / 2 | 3 / 6 | 1 / 4 |
| VWAP against | 54 / 59.3 % / +520.0 / -11.7 | 19 / 63.2 % / +221.0 / 0 | 13 / 17 | 6 / 10 |
| Futures-led gap > 1.6 | 59 / 57.6 % / +547.3 / -28.5 | 24 / 58.3 % / +210.1 / 1 | 11 / 14 | 4 / 7 |
| Bank z < -0.5 | 71 / 54.9 % / +977.2 / -43.1 | 32 / 53.1 % / +178.0 / 2 | 6 / 7 | 1 / 2 |
| R04-A | 71 / 56.3 % / +1,079.3 / -30.3 | 30 / 60.0 % / +260.2 / 1 | 5 / 8 | 0 / 5 |
| With gap unfilled | 73 / 52.1 % / +1,008.2 / -41.8 | 31 / 58.1 % / +178.9 / 1 | 7 / 4 | 0 / 4 |
| OR30 broken against | 63 / 58.7 % / +864.0 / -28.5 | 32 / 50.0 % / +142.2 / 2 | 8 / 13 | 2 / 1 |
| Whipsaw 60 | 69 / 58.0 % / +1,045.5 / -25.5 | 30 / 53.3 % / +186.9 / 2 | 5 / 10 | 2 / 3 |
| Side lock 12 | 57 / 61.4 % / +885.2 / -13.6 | 23 / 56.5 % / +175.4 / 1 | 10 / 17 | 5 / 7 |

What this shows:
* **The late-window gains of almost every guard come from the two bad expiry days, 3 Nov and 9 Nov.** 9 Nov alone loses
  -45 (pm cut), -29 (VWAP), -27 (futures-led) and -43 (R04-A) points of trade return to the flagged trades.
* **The guards are mostly different rules.** Overlap of the 40 losers of -5 % or worse (Jaccard): 0.0 to 0.3 for most
  pairs. The exceptions: whipsaw and side lock 0.61 (they are one idea, loss memory, so score them as one hypothesis),
  VWAP and OR30-against 0.53.
* **Danger of stacking them.** 39 of the 40 big losers are flagged by at least one of the ten rules, and the 27 Oct
  +79.7 % and 19 Oct +50.5 % winners are each flagged by three. A union of rules would look perfect in sample and would be
  pure overfitting. Promote at most one guard at a time, each on its own forward record.

### V2. Expiry exits, bounded from the trade table (all 4 expiry days)

The floor needs the bid path, so I bound it: the upper bound assumes the exit at 60 % of the final peak gain; the lower
bound assumes the floor fires at its earliest possible level (+18 %).

| Shadow | Early strike / sum | Late strike / sum | 19 Oct | 27 Oct | 3 Nov | 9 Nov |
|---|---|---|---|---|---|---|
| Base | 53.6 % / +986.9 | 51.4 % / +153.8 | +22.8 | +541.9 | -37.1 | +43.4 |
| TP +60 % (exact) | 53.6 % / +1,066.4 | 51.4 % / +171.6 | +32.1 | +612.1 | -37.1 | +61.1 |
| Floor 0.6 / 30, upper | 53.6 % / +1,125.5 | 51.4 % / +215.8 | +52.6 | +650.7 | -37.1 | +105.4 |
| Floor 0.6 / 30, lower | 53.6 % / +983.2 | 51.4 % / +186.1 | +6.7 | +554.3 | -37.1 | +75.7 |
| TP + floor, upper | 53.6 % / +1,219.1 | 51.4 % / +241.2 | +64.1 | +732.8 | -37.1 | +130.8 |
| TP + floor, lower | 53.6 % / +1,062.8 | 51.4 % / +207.8 | +14.7 | +626.0 | -37.1 | +97.4 |

R05's per-second +100.5 % on 9 Nov sits inside my band (+75.7 to +105.4). The floor's risk is 19 Oct (its six PE trades
peaked at +44 to +71 %). Neither exit touches 3 Nov: that day's losses are entries (18 stops), so the entry-side shadows
(13:30 cut, side lock) are the ones aimed at it.

## 6. Build list, in order

Everything here is for after the 15:30 close, with flags off, and with the live step time measured before any engine
change goes live (standing rule). Nothing below changes a live trading decision.

### (a) Display only: build first (owner point 4)

| # | Item | What it shows | Engine or Lab change | Source |
|---|---|---|---|---|
| a1 | The Conductor's voice: `apex/engine/voice.py`, `state["voice"]`, 1 Hz, inside `_safe` | Modes WAITING / IMPULSE / ARMED / ZONE / HOLDING / EXITING / CLOSED with real numbers: "Armed for a CALL since 11:02 (impulse 46). Pullback 12 of the 23 points I need. Expires 11:17." Veto margins per pool book. The contract and price it would buy. | New observer reading `strat.arm`, `fs`, `qmax/qmin`, vetoes, `pos["rules"]`; display copy of `_pick`; a 5-row `recent` deque in the Conductor log | R12 I1, R11, R01 idea 1 |
| a2 | "What I would do now" card and "What would change my mind" lines | Verb pill (WAIT, GET READY, BUYING, HOLD, CLOSE TO EXIT, SELLING), the plan row (buy price, stop, trail, floor/clock), price levels and times that change the plan | UI over a1; mock: `data/research/13nov/work/R11/mock.html` | R11 |
| a3 | Replace HOLD/WATCH/EXIT-SOON with the real exit ladder | Distance to stop, forward trail, floor, clock, flat time; words by distance (HOLD / CLOSE TO EXIT / PROTECTED / SELLING), 60 s hold | Reads `pos["rules"]` only; retire `verdict_of` from the panel | R12 I2, R11, R02 idea 7, R05 idea 7 |
| a4 | Stand banner | Word BULLISH / BEARISH / SIDEWAYS from R11's strength (-100..+100, hysteresis), a behaviour sentence with facts in points (held 60 s), "how sure I am" with the measured record | Lab `stand()` key per R10's data contract | R11, R10 |
| a5 | Short-term needle | Calibrated "% up, next 1 to 2 min" (R10), with the label "nowcast, already in option prices" and its forward-target score; the heavyweight push P chip (R08) replacing the unweighted chip; a "futures are behind the options by X pts" line (R07); sister lead line once a6-b data is fixed (R09) | Lab only; `phaseB_stand_fit.py` builds `stand_model.json` | R10, R08, R07, R09 |
| a6 | Context lines in first person | Day type so far (R03), time-of-day record (R18), account memory and whipsaw (R17), BOCPD segment and side-lock state (R20), honest break-even with the market's theta clock (R06), family agreement count (R15) | Small Lab or engine observers | R03, R18, R17, R20, R06, R15 |
| a7 | Record strip and honest-number tile | Every percentage with its sample: 2-min lean, 15-min stand 50 %, Conductor strike, post-freeze +6.5 % geometric, P(mean <= 0) 0.18 | Nightly job | R11, R19 |
| a8 | Demote the +- range ladder and the "expected premium" board below the card | | UI | R11 |
| a9 | Clean the legacy commentary | Drop 1,580 broken remarks, 19 Oct base rates, rate limit; trail width from `pos["rules"]`; fix "velocity -0" entry wording (`app.js:378-383`). Changing the tests that ban first-person words (`tests/test_c5_cmt_hold.py:107`, `tests/test_c5_commentary.py:21`) is the owner's call. | commentary.py, cmt_hold.py, app.js | R12 I4, I6 |
| a10 | Lab lean scale and monotone ranges | Lean from calibrated odds or a robust sd; sd non-decreasing in horizon (display copy) | Lab | R10 ideas 3 and 5 |

### (b) Reliability and speed: decisions stay identical

| # | Item | Why | Source |
|---|---|---|---|
| b1 | Owner actions: check laptop cooling and set Windows power mode to "Best performance" while trading; confirm the clock in Task Manager; keep heavy research after 15:30 | CPU at 100 % and 25 to 29 % of max frequency | R13 |
| b2 | Research jobs under a hard CPU cap (job object) in `data/research/13nov/lowprio.py` | Priority does not stop heat; the cap does (tested) | R13 idea 2 |
| b3 | Forecast Lab at normal priority (engine and feed stay above normal) | Lab lost 29 % of seconds | R13 idea 1 |
| b4 | Dashboard payload to the gateway in memory (or two fixed slots); gateway errors to `data/logs/gateway.log` | 965 refused swaps are caused by the reader handle; today's console error left no record | R13 ideas 3, 4, 9 |
| b5 | One set of Lab calibration bounds (load = online clip) | z80 and kappa reset every morning | R13 idea 5, R10 idea 4 |
| b6 | Feed: stop-aware reconnect and a "reconnecting" supervisor line; registry save that cannot kill the feed; login refusal without a restart loop; atomic REST ledger; log chain-write failures; quick VIX retry; label the 09:15 wait as OPEN | The one path that can drop the feed in session; misleading STALE alarms | R13 ideas 6, 7, 8, 10, 13 |
| b7 | Council hold photograph: call `weather5.hold_tick` for council positions, but write the LTP peak time to `peak_t_ltp` (council owns `peak_t`, a hold-model input) and keep `pos["best"]` for council positions | Unblocks every hold and exit study on the champion. Must be proven decision-identical (replay gate), because `peak_t` is read | R05 idea 1, R02, R17, R19 |
| b8 | Data fixes that only change photographs: FINNIFTY spot (or futures mid) for fn60/fn300, BANKNIFTY futures mid for BankLead and bn60/bn300; raw last print for the futures aggressor test (log both for a week); time-based flow and Force windows; basket units with a `_ix` field and one sector map; `theta_min_mkt` as a new field; a real event calendar | Broken or mislabelled inputs. Before shipping, check that no live pool rule reads the changed fields (today none of the five pool books does) | R09, R07, R08, R06, R18 |
| b9 | Prior-day levels with a staleness check | **Not decision-identical**: c20_9v's level booking reads the prior-day levels, so this changes a pool book on days after a missing save. Treat it as a correctness fix that needs the owner's yes | R18 idea 5 |
| b10 | R14 speed batch behind the A/A2/B replay gate on 27 Oct, 3 Nov and 12 Nov: rule check on the five-field rule photo (keep the fire_log append), forward view by bisection, regime sorted percentiles, VWAP-side run index, basis sorted median, stacked erf, pre-allocated council day table, leaner publish, cached photograph text in the books save, strikes tape kept open, GC measurement, per-book timing | Removes most 100 to 276 ms book spikes; 12 to 25 % of engine time. The gate runs replays: owner's OK | R14 |

### (c) New shadow books and rules for the next session (flags off, scored by the 7-test standard from 16 Nov)

Pre-register all of them today, in this order, in the R19 ledger (`work/R19/harness.py`), and adjust for the number of
shadows (11 here): with 11 shadows scored forward, one will look good by luck within two weeks.

| Tier | Shadow | Exact rule | Build | Judge on |
|---|---|---|---|---|
| 1 | `tp60` twins of each pool book (start with c20_9y) | EXP mode `tp=0.60`; normal days unchanged | c20_9x subclass; the core switch exists (`c20_08.py:33, 121`) | Expiry days only; strike and return per expiry day |
| 1 | `c20_9y_xf` | Expiry: once peak bid >= entry x 1.30, sell when bid <= entry x (1 + 0.6 x peak gain) | `_floor0` in `c20_9x.py:175` on `dte0` | Same |
| 1 | `c20_9y_txf` | Both of the above | | Same |
| 2 | `conductor_sl` | Side-loss lock N=12 (R20 E6) | `AdaptiveConductor` with a `SideTape`; a list of shadow Conductors in `engine_main.py:336-341`; same `admit` hook in `account_sim` | Strike first, worst day, losing days |
| 2 | `conductor_wp60` | Whipsaw pause 60 min (R17) | One check before `eligible[0]` | Same; scored with `conductor_sl` as one hypothesis |
| 2 | `c20_9y_pm` | No expiry entry from 13:30 (c20_20 "pm") | Twin with FINAL_R9 + ("pm",) | Expiry days |
| 3 | `c20_9y_x1` | Expiry day: one strike deeper ITM (abs delta 0.65 to 0.75) | `tie` picker subclass | Expiry days |
| 3 | `conductor_conf` | Any-family confirmation within 300 s (R15 CONF_W300_K1) | Shadow Conductor reading other books' triggers | All days |
| 3 | `c20_vw` / `c20_tl` / futures-led | VWAP side; trend lock 10:15; domino gap > 1.6 | Account-level `pool_gate` (needs the R04 fall-through fix) | Watch only: each failed early return |
| 3 | `c20_9y_orb` | Restore the ORB lock in a twin | FINAL_R9 + ("orb",) | All days |
| 3 | R04-A | `sign_none_share300 >= 0.0197` at account level | `phaseB_fresh_days.py` on new days | Never live before 10 fresh days |

Two mechanisms are needed first and change nothing by themselves: the account-level `pool_gate` list in pool.json read
before the per-member loop (`conductor.py:177`), and the list of shadow Conductors. Measure step time before going live:
R20 estimates under 0.1 ms a step for the side tape.

### (d) Phase B studies after the 15:30 close

Standing rules apply: one script at a time, `py -3.13`, `lowprio`, under 3 minutes and 1.5 GB per run, and nothing starts
without the owner's go-ahead (standing rule on long runs). Paths are under `D:\ApexOptions\data\research\13nov\work\`.

**Order 1. Decides the tier-1 and tier-2 shadows**

| Script | Decides | Notes |
|---|---|---|
| `R05\phaseB_c20_overlays.py`, then `--group=KE`, then `--group=K`, `P`, `T`, `L` | Expiry floor on all 4 expiry days | First call builds `paths_all.pkl` (about 2 min) |
| `R02\phaseB_list.txt` (37 commands of `phaseB_paths.py <part> <chunk>`), then `R02\phaseB_merge.py` | Expiry TP 55/60/70 %, forward-point and smoothed stops, PGB on every pool book, no-progress clock | 37 short runs |
| `R18\phaseB_tod_baseline.py` | Is the expiry-afternoon weakness the market (decay) or c20? | About 35 s per day part, about 10 min in all: split by part or ask |
| `R20\phaseB_luck_margin.py` | Luck margin for the side lock | 10 to 20 min: over the 3-minute limit, needs the owner's OK or a split by seed |
| `R17\phaseB_iv_after_entry.py <day> --marks-only` per day, then no arguments; `R17\phaseB_guards_all_books.py` | IV-after-entry exit; whipsaw and cooldown on all 107 books | |
| `R06\phaseB_reprice_all.py` (repeat; skips done days), then `R06\phaseB_strike_policy.py` | Expiry deeper-ITM shadow | 1 to 2 min per day |
| `R19\phaseB_holdmarks_council.py`, then `R19\harness.py --exit ... --holdfile` | Bid-based hold marks for every pool trade until b7 exists | Check CE/PE and bid/ask axis order against ds2.py first |

**Order 2. Entries, heavyweights, sisters, microstructure**

| Script | Decides |
|---|---|
| `R01\phaseB_pb_sweep.py`; `R01\phaseB_c20_complements.py ALL` | Pullback depth x arm age; age-out entry; FLAG, GRIND, REV families |
| `R08\phaseB_hw_all17.py` (four batches, then `--summary`) | P on all 17 days; P at every trigger |
| `R09\phaseB_sister_extract_all.py` (one part per run; 1 to 4 min each, some parts may need a split), then `R09\phaseB_sister_wf.py` | Sister lead walk-forward on the late days |
| `R07\phaseB_ms_alldays.py todo`, `feat <part>` per part, `eval`; then `R07\phaseB_ms_gate.py`; `R07\phaseB_l1_ofi_ticks.py <part>` | Forward-speed veto; true OFI. `eval` on 23 parts may pass 3 min: ask first |
| `R16\phaseB_vwap_exit_gao.py <day>` per day | VWAP trailing exit; Gao first/last half hour |
| `R03\phaseB_daytypes_dsv2.py` | Day labels with weighted heavyweight features |

**Order 3. Display calibration (the numbers the screen will quote)**

| Script | Gives |
|---|---|
| `R10\phaseB_stand_fit.py`, `R10\phaseB_lag_decay.py`, `R10\phaseB_behaviour_hyst.py` | `stand_model.json`; how fast the needle goes stale; held behaviour labels |
| `R12\phaseB_arm_phases.py`, `R12\phaseB_verdict_obey.py`, `R12\phaseB_retrigger_hold.py` | "Chance I fire within 5/10/15 min" calibration; the old verdict on 16 days; re-triggers while holding |
| `R11\phaseB_armed_card.py` | GET READY share, fire rate after arming, move after a fire |
| `R20\phaseB_bocpd_ds2.py` | BOCPD segment from per-second futures |

**Order 4. Statistics and process**

| Script | Gives |
|---|---|
| `R04\phaseB_conductor_null.py` (seeds 1 to 10), `R04\phaseB_beam_null.py GROUP`, `R04\phaseB_fresh_days.py` | More permutations; frozen candidates on 13 Nov onwards |
| `R19\phaseB_rolling.py` | Rolling re-fit with Benjamini-Hochberg |
| `R15\phaseB_meta_of_meta.py`, `R15\phaseB_dropped_trades_weather.py` | Choosing the chooser; what the confirmation drops |
| `R13\phaseB_packet_gaps.py <day>` | Broker silences vs a starved feed |
| `R14\phaseB_bench.py` | Speed timings on a quiet machine |

**Needs the owner's explicit OK (replays or long runs):** `R14\phaseB_equivalence.py --run` (A/A2/B replays),
`R13\phaseB_machine_monitor.py` (runs all session), engine replay twins (`c20_9y_pm`, `c20_9y_orb`, morning warm-up
W=600, trend lock, futures-led, the shadow Conductors), `R20\phaseB_luck_margin.py`, the full `R18\phaseB_tod_baseline.py`
and `R07` eval on all parts.

## 7. Claims to re-check adversarially before anything changes the Conductor

| # | Claim | What could make it wrong | Check |
|---|---|---|---|
| 1 | Expiry TP +60 % helps in both windows | Re-entries after an earlier exit are not modelled; the bid may gap past +60 %; it rests on 6 trades | R02 per-second Phase B; forward expiry days (17 Nov is next) |
| 2 | Expiry floor 0.6 / 30 took 9 Nov to +100.5 % | One day; my lower bound loses 16 points on 19 Oct | R05 `--group=KE` on all 4 expiry days |
| 3 | Side lock raises strike in both windows | No luck margin yet; the c20 family list includes twins built in sample; it costs 27 Oct | `R20\phaseB_luck_margin.py`; at least 10 forward days |
| 4 | Whipsaw pause is ahead in both windows | Holes at 45 and 50 minutes; 9 Nov swings -0.4 to +72.5 % with tiny setting changes; overlaps the side lock (Jaccard 0.61) | Score with the side lock as one hypothesis |
| 5 | Expiry afternoon is weak | 4 expiry days; may be decay for every buyer, not c20 | `R18\phaseB_tod_baseline.py` |
| 6 | Every account guard result | All are re-walks of recorded trades: a freed book cannot create the new trades it would take live (skip or substitute only); the account path is chaotic (R17) | Engine replay of each shadow before promotion |
| 7 | The 5-day "test window" is out of sample | 5 and 6 Nov were inside the pool choice; only 9, 11, 12 Nov are truly out of sample | Judge promotions on 13 Nov onwards |
| 8 | Forecaster short-term skill | It is lead-lag between feeds; part may be Breeze packet order (R09: even the spot index arrives first) | Score on the forward (R07 I1); `R10\phaseB_lag_decay.py` |
| 9 | Theta clock on expiry day is calendar | An intraday IV seasonal could imitate it (R06's own caveat) | Straddle-decay test on more expiry days |
| 10 | VWAP side result | R16 could not confirm the meaning of `fut[:,3]` in ds2 for the per-second test; the photo field `wx_vwap_side_with` is the engine's own | Read `ds2.py:128` before the Phase B exit study |
| 11 | CPU is throttled to 25 % | The counter can read low on this hybrid chip (R13) | Task Manager "Speed" figure |
| 12 | Council hold photograph is a harmless observer | `hold_tick` writes `pos["peak_t"]`, which the council hold model reads | Replay gate, decisions identical |
| 13 | R04-A (`sign_none_share300`) | Chosen after seeing the test days, from about 90 lines that pass a 1-in-7 luck bar | Fresh days only |
| 14 | "Every big loser is caught by some rule" (my V1) | That is the overfitting trap, not evidence: 39 of 40 losers flagged by at least one of 10 rules | Promote at most one guard at a time |
| 15 | The baseline itself (+10.92 lakh) | 95.6 % in sample; DSR 0.073 after the freeze with 107 books tried | The honest-number tile; 43 to 127 forward days to prove an edge |

## Files

* This plan: `D:\ApexOptions\docs\research\13nov\00_MASTER_PLAN.md`.
* The 20 reports: `D:\ApexOptions\docs\research\13nov\R01_*.md` to `R20_*.md`.
* My cross-check scripts and outputs: `D:\ApexOptions\data\research\13nov\work\SYN\` (`c1.py` join, `c2.py` guard overlap,
  `c4.py` expiry exit bounds, `cond.pkl`).
* UI mock: `D:\ApexOptions\data\research\13nov\work\R11\mock.html`.
* Evaluation harness for every Phase B idea: `D:\ApexOptions\data\research\13nov\work\R19\harness.py`.


## Phase B outcome (13 Nov night)

All Phase B studies ran; results and verdicts are in `docs/56_BUILD_13NOV_EVENING.md` ("Phase B results"). None meets the 7-test standard. Leads for the next round: R20 BOCPD with-drift filter (needs the Conductor, worst-day and null tests), R09 rsb15 < 0, R17 against100_er0.1.
