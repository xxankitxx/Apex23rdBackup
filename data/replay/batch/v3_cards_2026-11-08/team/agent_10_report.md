# Agent 10 — fade_switch and fade_switch_r002 (8 Nov 2026)

Data: 14 replayed days (v3 photographs), discovery = first 10 days (19 Oct – 2 Nov), holdout = last 4 (3 – 6 Nov).
Everything below was searched on discovery only; the holdout was evaluated once per frozen rule. Scripts, logs and
every result card are in this folder (`s1_search.py`, `log_*.txt`, `results_*.json`, `cards.md`, `rules.json`).

## Verdicts

| book | verdict | nearest candidate | discovery kept | holdout kept | p |
|---|---|---|---|---|---|
| fade_switch | **NONE** | `oi_own_chg5 < 1.259e5 AND new_lows >= 26` | 308 kept, 61 %, 119 losers | 0 kept (clause never true on holdout) | 0.020 |
| fade_switch_r002 | **PROPOSE (weak)** | `e_fut_imb5 < 0.25 AND range_now >= 191.1` (stationary set) | 181 kept, 63 %, 67 losers, +330,008 Rs | 63 kept, 48 %, 33 losers, +5,203 Rs | 0.047 pooled (0.050 n=200; 0.045 n=400) |

One rule, on fade_switch_r002, passes 2–4 by the letter of the standard and is proposed with a loud caveat (it makes the book
break-even on holdout, not profitable). Nothing passes on fade_switch. 35 rule cards are in `rules.json`; 33 REJECTED, 2 PROPOSE (the same rule from the two shuffle runs).

## The books' own record

**fade_switch** — 757 trades (563 discovery, 194 holdout). Discovery: 290 winners / 273 losers (51.5 %), mean +0.05 %,
+158,051 Rs. Holdout: 94 / 100 (48.5 %), mean −0.18 %, −48,363 Rs. All 14 days: 384 W / 373 L, +109,688 Rs.
Average winner +4.8 %, average loser −5.0 % (symmetric target/stop, win-loss ratio 0.96): a coin flip with a tiny
edge on the first ten days and a slightly negative one on the last four. By day: +108k (19 Oct) and −88k (27 Oct)
dominate; 7 of 14 days are negative.

**fade_switch_r002** — 469 trades (351 / 118). Discovery: 177 W / 174 L (50.4 %), mean +0.07 %, +144,372 Rs.
Holdout: 55 / 63 (46.6 %), mean −0.26 %, −32,081 Rs. All days: 232 W / 237 L, +112,291 Rs. Same symmetric
payoff (ratio 1.00). The R-002 filter keeps 62 % of the parent's trades and does not change its character.

Structural facts common to both (all 14 days, descriptive only): STOP exits are 39 % / 38 % of trades and carry the
entire loss; the direction edge FLIPS between windows (fade_switch PE 54 % on discovery, 41 % on holdout; CE 48 % to
57 %), so any direction rule learned on discovery would have lost on holdout; `regime=RANGE` trades lose in both
windows (42 % / 43 %; 39 % / 39 % for r002) and `regime=UNCERTAIN` wins in both (56 % / 61 %; 67 % / 72 %) — see
"observations" for why that is NOT proposed.

## What was searched (reproducible)

Feature set "all" = 268 numeric weather fields (fill >= 80 %, >= 4 distinct values; hmm_*/hk_* excluded) + 60 text
indicators (`field=VALUE`, 2–8 values) = 328 features for fade_switch (327 for r002). The numeric fields include 75
derived ones built in `s1_search.py`: ratios (mv60/rv15, mv30/rv5, premium/theta_be15, theta_be15/speed15,
speed15/sigma15, vega/premium, fmv60/mv60, rv5/rv15, spread/premium, imp_rng/sigma15, absorb60/kyle_lambda ...),
differences (er60−er30, mv60−mv300, fmv60−mv60, rv5−rv15, vix_chg5−vix_chg15, bn60−nifty60 ...), products
(gamma·mv30, mv60·mv300, mv30·wmove30, mv60·er60, kv·mv60, vanna·mv60, (breadth_dir−0.5)·mv60 ...), absolute
values (|kv|, |kvt|, |cusum|, |skew_atm|, |vwap_ext| ...), direction interaction (`is_ce`, signal r15 in the trade's
direction, OTM points in direction), within-day z-scores and ranks of mv60 / rv15 / premium / er60 / vix / speed15 /
theta_be15 / sigma15 / fut_vol60 / atm_iv_chg5 against the book's OWN EARLIER trades that day (>= 3 earlier trades),
the book's closed-before-trigger record today (prior wins / losses / P&L / win rate), hour, (mins_open−180)^2,
advisor veto count, and the trigger-time signal / edge fields (`sig_*`, `edge_*`).

Feature set "stationary" = the same minus 70 fields that can name the DAY rather than the market: session counters
(new_lows, new_highs, n_today, ret_today, streak, hi/lo_age_min, reversals60 ...), calendar (mins_open, hour, dte,
weekday, hrs_to_expiry ...), feed health, gap/PDH/PDL distances, raw levels (vix, premium, strike, pcr, walls, max
pain), all oi_* and adv_*, prior_* and phase_bucket. 258 / 257 features.

Searches, each on discovery only, each with its own 200-shuffle test of the SAME search (`rule_lab.shuffle_p`, seed 7):
1. best single clause (5 quantile lines per field, both directions), min_keep 20 and 150;
2. best 2-clause AND (`rule_lab.best_pair`, distinct fields, strongest 2,500 single masks), min_keep 20 and 150;
3. best 3-clause AND: the 100 best pairs each ANDed with every single mask on a third field, min_keep 20;
4. best OR of two single clauses (distinct fields), min_keep 60;
5. best single clause over the 60 text indicators only, min_keep 20 and 150.
1–4 were run on both feature sets for both books (28 searches); 5 on both books (4). Score = share of discovery
losers removed − share of discovery winners removed (`rule_lab.score_masks`).

## fade_switch — results

Nearest to passing (beats luck, but keeps nothing on holdout):

### fade_switch: `oi_own_chg5 < 1.259e+05 AND new_lows >= 26`
Search: pair AND, min_keep 20 (identical at 150), 328 features, all set. Shuffle p = 0.020 (real 0.216; shuffled best
median 0.179, max 0.224).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 563 | 52% | +0.05 | +158,051 | 273 |
| discovery | kept | 308 | 61% | +1.23 | +427,372 | 119 |
| discovery | removed | 255 | 40% | −1.06 | −269,321 | 154 |
| holdout | book | 194 | 48% | −0.18 | −48,363 | 100 |
| holdout | kept | 0 | | | 0 | 0 |
| holdout | removed | 194 | 48% | −0.18 | −48,363 | 100 |

Why it is rejected: `new_lows >= 26` ("at least 26 new session lows so far today") is true on the heavy down-days of
discovery and never once on the four holdout days. It names WHICH DAY, not a market condition, and the rule keeps
nothing on holdout. The triple (`... AND fut_imb_o >= -0.443`, p = 0.020, 64 % kept on discovery) has the same
clause and the same empty holdout. This is the clearest case in my books of a rule that beats the shuffle test and is
still a memory of the tape — exactly why the holdout exists.

Looked good on discovery, failed (one line each; full cards in `cards.md`):
* `oi_own_chg5 < 1.259e5` (single, all set): disc kept 392, 57 %; p = 0.165 (does not beat luck); holdout kept 139 at
  50 % vs book 48 % but −11,729 Rs (mean −0.01 %), removed −36,634. Passes 4 on win rate only; fails 3.
* `opt_opp_o=REFILLING < 1` (single, stationary set and text-only set): disc kept 395, 56 %; p = 0.27 on the full
  stationary set, p = 0.02–0.03 on the 60-indicator search; holdout kept 134 at **46 % < 48 %**, −61,539 Rs, while
  the removed 60 trades made +13,176. Fails 4 outright.
* `atm_iv_med < 30.6 AND opt_opp_o=REFILLING < 1` (pair, stationary): disc 349 kept, 59 %; p = 0.23; holdout kept 46 %,
  −61,539. Fails 3 and 4.
* `... AND e_fut_tot_imb >= -0.337` (triple, stationary): disc 313 kept, 62 %; p = 0.13; holdout kept 111 at 48 %,
  −48,230, removed −133. Fails 3; the kept side carries the whole holdout loss.
* `(oi_own_chg5 < -8.58e4) OR (max_pain_dist < -41.8)` (OR, all): disc 269 kept, 61 %; p = 0.395; holdout 50 %,
  −17,053. Fails 3.
* `(breadth_dir < 0.232) OR (sig_r15_dir < -10.55)` (OR, stationary): disc 291 kept, 60 %; p = 0.335; holdout 49 %,
  −31,099. Fails 3.

## fade_switch_r002 — results

Nearest to passing:

### fade_switch_r002: `e_fut_imb5 < 0.25 AND range_now >= 191.1`
Search: pair AND, stationary set (257 features), min_keep 150 (identical rule at min_keep 20). Shuffle p = **0.050**
at min_keep 150 (10 of 200 shufflings matched or beat the real score 0.259; shuffled median 0.219, max 0.300) and
0.055 at min_keep 20.

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 351 | 50% | +0.07 | +144,372 | 174 |
| discovery | kept | 181 | 63% | +1.73 | +330,008 | 67 |
| discovery | removed | 170 | 37% | −1.69 | −185,637 | 107 |
| holdout | book | 118 | 47% | −0.26 | −32,081 | 63 |
| holdout | kept | 63 | 48% | −0.03 | +5,203 | 33 |
| holdout | removed | 55 | 45% | −0.51 | −37,284 | 30 |

Reading: on holdout the kept side's win rate (47.6 %) is a hair above the book's (46.6 %) and the removed side holds
most of the loss — the right shape — but the kept side still has 33 losers in 63 trades and a mean of −0.03 %; it
became a break-even book, not a profitable one. Meaning: `e_fut_imb5 < 0.25` = the 5-s futures depth imbalance is not
strongly in our favour (the book fades; a crowd already leaning our way is a warning), `range_now >= 191` = the day has
already travelled at least 191 points. The shuffle test says a search this wide finds a score this good in random
labels about 5 % of the time — on the line. Re-test with 400 fresh shufflings (seed 11): p = 0.045 (18/400). Pooled over all 600 shufflings: p = 0.047 (28/600) — under 0.05 by a hair. It therefore passes 2, 3 and 4 as the standard is written, so the verdict is PROPOSE (weak): kept side on holdout 47.6 % vs book 46.6 %, +5,203 Rs, mean −0.03 %, 33 losers in 63 — break-even, not profitable.

Looked good on discovery, failed:
* `edge_imp_f >= 0.1244` (single, both sets): disc kept 245, 57 %; p = 0.08–0.135; holdout kept 75 at 48 % vs 47 %,
  −452 Rs; removed −31,629. Fails 3; holdout break-even at best.
* `imp_depth >= 0.1238 AND oi_net_help5 >= -8.87e5` (pair, all set): disc kept 175, 63 %, +400,858; p = 0.06–0.07;
  holdout kept 57 at **42 % < 47 %**, −38,009, and the removed 61 made +5,928. Inverted on holdout.
* `edge_imp_f >= 0.1244 AND oi_net_help5 >= -8.87e5 AND p_kv_mv60 >= 0` (triple, all): disc kept 156, 67 %, +415,743;
  p = 0.075; holdout kept 51 at 47 %, −4,426. Fails 3.
* `e_fut_imb5 < 0.25 AND range_now >= 191.1 AND d_bn60_nifty60 < 0.051` (triple, stationary): disc kept 164, 66 %;
  p = 0.055; holdout kept 58 at 52 %, +11,352, removed −43,433. The best holdout of anything found — still p >= 0.05,
  and 28 losers in 58 kept trades.
* `(e_fut_imb5 < 0.25) OR (d_vixchg5_vixchg15 < -0.04)` (OR, all): disc kept 272, 58 %; p = 0.535; holdout kept 92 at 50 %,
  +25,916, removed −57,996. A good-looking holdout, but the OR search finds this score in random labels more than half
  the time: luck.
* `(edge_imp_f >= 0.1244) OR (mv120 < -18.62)` (OR, stationary): disc 258 kept, 58 %; p = 0.425; holdout 48 %, +4,147.
* `opt_opp_o=REFILLING < 1` (text-only single): p = 0.06–0.085; holdout kept 88 at **41 %**, −62,563, removed +30,482.
  Inverted.

## Observations that are NOT rules (said plainly)

* `regime=RANGE` loses on both windows for both books (fade_switch: 110 discovery trades at 42 %, −64k; 49 holdout at
  43 %, −47k. r002: 66 at 39 %, −26k; 33 at 39 %, −39k) and `regime=UNCERTAIN` wins on both (fade_switch 89 at 56 %
  then 36 at 61 %, +57k; r002 60 at 67 % then 18 at 72 %, +44k). I saw this in a descriptive table that INCLUDED the
  holdout days, so these have no honest holdout and no valid shuffle test — the search over the 60 text indicators,
  run properly on discovery alone, picked `opt_opp_o=REFILLING` instead, which then failed. Reported as a hypothesis
  for the NEXT four days, not a finding. Cards in `rules.json`, marked HAND-PICKED / REJECTED.
* The direction edge flips sign between windows (PE 54 % to 41 % on fade_switch). No `is_ce` rule survived even the
  discovery search, consistent with no stable direction edge.
* Every rule that beat luck on discovery kept at best a break-even book on holdout. With a symmetric ±5 % payoff and
  a 48–52 % strike rate, removing losers "almost completely" would need a feature that separates winners from losers
  far better than anything in the 328-field photograph does at the trigger second; the shuffle distributions (best
  random pair score 0.18–0.22 on 563 trades) show how much apparent separation is noise.

## Honest conclusion

* **fade_switch: NONE.** The only rules that beat the shuffle test (p = 0.02) rely on `new_lows >= 26`, a day label
  with zero holdout trades. Every day-independent rule fails the shuffle test (p 0.13–0.40) and most also lose on
  holdout. No rule honestly removes this book's losers.
* **fade_switch_r002: PROPOSE (weak).** The stationary pair `e_fut_imb5 < 0.25 AND range_now >= 191.1` passes 2–4 as
  written: discovery kept 181 at 63 % (+330,008, removed 170 with 107 losers); pooled shuffle p = 0.047 over 600
  shufflings (on the line — one more lucky shuffle in 600 would have failed it); holdout kept 63 at 47.6 % vs the book's
  46.6 %, +5,203 Rs, removed 55 at 45 %, −37,284. What it does NOT do: make the book profitable. The kept side on
  holdout has 33 losers in 63 trades and a mean of −0.03 %; it turns a −32k holdout into +5k by removing the worse half,
  not by keeping winners. The owner's register should read it as "the least bad filter found", not as an edge.

Next step (no replay was run; owner's rule): freeze `e_fut_imb5 < 0.25 AND range_now >= 191.1` on r002 and
`regime != RANGE` on both books as written hypotheses now, and score them on the next four live/replayed days before
anyone looks at them again.
