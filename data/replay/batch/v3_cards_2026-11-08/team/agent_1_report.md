# Agent 1 — the council family (c20_9y, c20_9s, c20_9v, c20_9x, c20_9t, c20_8x)

8 Nov 2026. Data: 14 replayed days 19 Oct – 6 Nov; discovery = first 10 days, holdout = last 4 (2026-11-03 .. 11-06). Every rule below was searched on discovery only, shuffle-tested with the identical search on 200 shufflings of the discovery outcomes, then evaluated frozen on the holdout. Verdict PROPOSE needs all three; anything else is REJECTED.

Search families run on every book (score = share of losers removed minus share of winners removed, kept side >= 20 discovery trades, lines at the 10..90 % quantiles of the discovery values):

* F1 best single clause over the raw weather fields (numeric, >= 80 % filled, >= 4 distinct values)
* F2 best AND-pair over the raw weather fields (two different fields)
* F3 / F4 the same over the FULL set: raw + derived mathematics + text indicators + the trigger's own numbers (signal_trig)
* F5 greedy triple over the full set (best pair, then the clause on a third field that most improves it)
* F6 / F7 single and pair over the full set with 9 quantile lines instead of 5 (finer thresholds, wider search)

Derived features (how computed):

* `mv60_over_rv15`: mv60 / rv15_spot (60-s move in trade direction per unit realised vol)
* `mv300_over_sigma15`: mv300 / sigma15
* `mv30_minus_mv60`: mv30 - mv60 (is the last 30 s faster than the minute?)
* `mv60_minus_mv300`: mv60 - mv300 (deceleration of the move)
* `accel15_over_sigma15`: accel15 / sigma15
* `premium_over_theta_be15`: premium / theta_be15
* `gamma_x_mv30`: gamma * mv30
* `delta_x_mv60`: delta * mv60
* `vega_x_atm_iv_chg5`: vega * atm_iv_chg5
* `er60_minus_er30`: er60 - er30
* `breadth_edge`: breadth_dir - 0.5 (breadth in the trade's direction minus even)
* `imp_rng_signed`: imp_rng * (+1 if imp_with else -1)
* `iv_vs_med_x_opt_iv_chg5`: iv_vs_med * opt_iv_chg5
* `ivrv_x_theta_pct`: e_iv_rv * theta_pct
* `premium_over_spot_bp`: premium / spot_in * 1e4 (premium in basis points of spot)
* `optrun_x_optimb`: opt_run * opt_book_imb
* `log_rest_with_over_opp`: sign-log(rest_with_rs / rest_opp_rs)
* `log_agg_with_over_rest_opp`: sign-log(agg_with_rs / rest_opp_rs)
* `oi_help5_over_own5`: oi_net_help5 / |oi_own_chg5|
* `po_up5_minus_po_dn15`: po_up5 - po_dn15
* `wmove60_minus_mv60`: wmove60 - mv60 (heavyweights lead/lag the index)
* `bn60_minus_nifty60`: bn60 - nifty60 (Bank Nifty confirming or diverging)
* `hwvol_x_futvol_surge`: hw_vol_surge * fut_vol_surge
* `theta_be15_over_speed15`: theta_be15 / speed15
* `kv_x_kvt`: kv * kvt (Kalman velocity weighted by its t-stat)
* `jumpz_x_cusum`: jump_z * cusum
* `strad_excess_over_premium`: strad_excess / premium
* `swing_ahead_over_behind`: swing_ahead / swing_behind
* `wall_room_over_sigma15`: wall_room / sigma15
* `spread_pct_x_quote_age`: spread_pct * quote_age
* `mins_open_bucket`: floor(mins_open / 60) (hour of session: 0=first hour ... 5)
* `mins_open_sq`: (mins_open - 187)^2 (distance from mid-session, squared)
* `is_ce`: 1 if the trade is a CE (direction up) else 0 (t['rr'])
* `ce_x_mv60`: (+1 CE / -1 PE) * mv60 (raw spot move, not direction-adjusted)
* `ce_x_breadth_edge`: (+1 CE / -1 PE) * (breadth_dir - 0.5)
* `ret_today_per_trade`: ret_today / max(n_today, 1)
* `streak_x_last_won`: streak * (1 if last_won else -1)
* `prem_z_day`: z-score of premium against this book's EARLIER trades today (None before 3 earlier trades)
* `mv60_z_day`: z-score of mv60 against this book's EARLIER trades today
* `rv5_z_day`: z-score of rv5 against this book's EARLIER trades today
* `sig_r15`: signal_trig r15 (trigger strength: 15-s futures move)
* `sig_z`: signal_trig z
* `sig_S`: signal_trig S (council score)
* `sig_S_novol`: signal_trig S_novol
* `sig_trend30`: signal_trig trend30 * (+1 CE / -1 PE) (30-min trend in the trade's direction)
* `sig_range5`: signal_trig range5
* `sig_iv_rise`: signal_trig iv_rise
* `sig_r15_over_sigma15`: signal_trig r15 / sigma15
* `adv_vetoes_raw`: adv_vetoes (number of advisors vetoing our direction)

Excluded: hmm_*, hk_* (fitted on these days); anything from the exit (hold_s, reason, peak) is a label, never an input.

## c20_9y

Record: 72 trades, 61% win, mean +11.2%, Rs +1,137,308, 28 losers over 14 days. Discovery: 54 trades, 63% win, mean +14.0%, Rs +1,078,009, 20 losers. Holdout: 18 trades, 56% win, mean +2.8%, Rs +59,300, 8 losers.
Features searched: 189 raw weather, 43 derived, 50 text indicators.

### Best rule found (F10 single, agree_same only (family unanimity))

### c20_9y: `agree_same >= 7`

Shuffle test p = 0.000 (beats luck). Search: best_single over the ONE feature agree_same (4 single masks), n_lines=5 (quantiles 10..90 % of discovery values), min_keep=20, score = share of losers removed - share of winners removed, discovery days only; shuffle = same search on 200 shufflings (seed 7).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 54 | 63% | +14.0 | +1,078,009 | 20 |
| discovery | kept | 40 | 78% | +20.4 | +1,145,687 | 9 |
| discovery | removed | 14 | 21% | -4.0 | -67,678 | 11 |
| holdout | book | 18 | 56% | +2.8 | +59,300 | 8 |
| holdout | kept | 17 | 59% | +3.1 | +61,678 | 7 |
| holdout | removed | 1 | 0% | -2.7 | -2,379 | 1 |
| all | book | 72 | 61% | +11.2 | +1,137,308 | 28 |
| all | kept | 57 | 72% | +15.2 | +1,207,365 | 16 |
| all | removed | 15 | 20% | -4.0 | -70,057 | 12 |

Verdict for this rule: **PROPOSE** — passes discovery, shuffle and holdout.

### Every search family, one line each

| family | rule | disc kept n / win / losers | disc removed n / win / losers | p | hold kept n / win / losers | hold removed n / win / Rs | verdict |
|---|---|---|---|---|---|---|---|
| F1 single, raw weather | `agree_same >= 7` | 40 / 78% / 9 | 14 / 21% / 11 | 0.245 | 17 / 59% / 7 | 1 / 0% / -2,379 | REJECTED |
| F2 pair, raw weather | `agree_same >= 7 AND sl_room_dn_pct >= 0.873` | 28 / 93% / 2 | 26 / 31% / 18 | 0.040 | 16 / 56% / 7 | 2 / 50% / +2,899 | REJECTED |
| F3 single, raw+derived+text+trigger | `agree_same >= 7` | 40 / 78% / 9 | 14 / 21% / 11 | 0.295 | 17 / 59% / 7 | 1 / 0% / -2,379 | REJECTED |
| F4 pair, raw+derived+text+trigger | `agree_same >= 7 AND opt_opp_o=DRAIN-FAST < 1` | 32 / 91% / 3 | 22 / 23% / 17 | 0.010 | 11 / 45% / 6 | 7 / 71% / +92,261 | REJECTED |
| F5 greedy triple, raw+derived+text+trigger | `agree_same >= 7 AND opt_opp_o=DRAIN-FAST < 1 AND theta_be >= 0.0693` | 29 / 97% / 1 | 25 / 24% / 19 | 0.020 | 11 / 45% / 6 | 7 / 71% / +92,261 | REJECTED |
| F6 single, raw+derived+text+trigger, 9 lines | `agree_same >= 7` | 40 / 78% / 9 | 14 / 21% / 11 | 0.410 | 17 / 59% / 7 | 1 / 0% / -2,379 | REJECTED |
| F7 pair, raw+derived+text+trigger, 9 lines | `agree_same >= 7 AND opt_opp_o=DRAIN-FAST < 0.4` | 32 / 91% / 3 | 22 / 23% / 17 | 0.015 | 11 / 45% / 6 | 7 / 71% / +92,261 | REJECTED |
| F8 pair, derived mathematics only | `mv60_minus_mv300 < 18.16 AND optrun_x_optimb < 0.4321` | 42 / 79% / 9 | 12 / 8% / 11 | 0.215 | 15 / 53% / 7 | 3 / 67% / +78,016 | REJECTED |
| F9 pair, book's own situation + calendar | `agree_same >= 7 AND adv_vetoes_raw >= 2` | 32 / 84% / 5 | 22 / 32% / 15 | 0.030 | 16 / 62% / 6 | 2 / 0% / -2,935 | PROPOSE |
| F10 single, agree_same only (family unanimity) | `agree_same >= 7` | 40 / 78% / 9 | 14 / 21% / 11 | 0.000 | 17 / 59% / 7 | 1 / 0% / -2,379 | PROPOSE |

### Reading

The wide searches (F1-F7) all converge on `agree_same >= 7` plus a second clause that is a memory of the tape: `opt_opp_o=DRAIN-FAST` and `theta_be` pass the shuffle (p 0.01-0.02) but on holdout the kept side wins 45 % against the book's 56 % and the removed side makes Rs +92k, so they are rejected. What survives is the first clause alone. `agree_same` is item J-67: the number of other books firing in this engine step and the last. On c20_9y it is 7 when every sibling fires. On the 14 days there are 12 trades with agree_same = 6 (one sibling abstained) and ALL 12 lost (11 on discovery: 4 on 19 Oct, 2 on 27 Oct, one each on 21, 22, 29 Oct and 2 Nov; 1 on holdout, 4 Nov). Matching the trades across the family shows which sibling abstained: c20_9s on 7 of them (7 losers, 0 winners) and c20_9t on the other 5 (5 losers; c20_9t also abstained on 2 winners, which carried agree_same = 5 because a second book was also out). So the rule reads: take c20_9y's trade only when c20_9s and c20_9t take it too. The pre-registered F9 search (24 situation/calendar features, pair) found `agree_same >= 7 AND adv_vetoes >= 2` at p = 0.030 and it passes the holdout (kept 62 % vs 56 %, removed 2/2 losers); the `adv_vetoes >= 2` clause is a passenger (it removes 4 winners and 4 losers more on discovery, and reads backwards: more advisor vetoes = keep). The bare clause's fair p is the one from the search that led to it: 0.055 in the 24-feature single search; the one-feature F10 search gives p = 0.000 but that search was chosen after looking, so its p is flattering. Holdout is thin: the rule removes 1 trade of 18 (a loser) and the kept side wins 59 % against 56 %. What makes me believe it more than the number says is the echo on the siblings, which were not used to form the idea: on c20_9s the same unanimity clause (`agree_same >= 6`) removes 10 discovery trades of which 8 lost, and on holdout 2 of 2 losers (p = 0.005 in its own one-feature search); on c20_9v (`agree_same >= 3`) 7 of 11 removed on discovery lost, 2 of 2 on holdout, p = 0.050. Does it remove the losers? No: c20_9y keeps 16 losers of 57 kept trades over 14 days (72 % win, up from 61 %); it removes a sliver, but the sliver is 12 losers of 12. Live caveat: agree_same is a count over the engine step and the one before; live timing of sibling triggers may differ from the replay's, and the rule says nothing about c20_9x, which fires first (its agree_same is 1 on nearly every trade).

**Verdict for c20_9y: PROPOSE**

## c20_9s

Record: 75 trades, 57% win, mean +10.0%, Rs +1,076,644, 32 losers over 14 days. Discovery: 55 trades, 60% win, mean +13.5%, Rs +1,054,823, 22 losers. Holdout: 20 trades, 50% win, mean +0.2%, Rs +21,820, 10 losers.
Features searched: 188 raw weather, 43 derived, 50 text indicators.

### Best rule found (F10 single, agree_same only (family unanimity))

### c20_9s: `agree_same >= 6`

Shuffle test p = 0.005 (beats luck). Search: best_single over the ONE feature agree_same (4 single masks), n_lines=5 (quantiles 10..90 % of discovery values), min_keep=20, score = share of losers removed - share of winners removed, discovery days only; shuffle = same search on 200 shufflings (seed 7).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 55 | 60% | +13.5 | +1,054,823 | 22 |
| discovery | kept | 45 | 69% | +17.4 | +1,087,590 | 14 |
| discovery | removed | 10 | 20% | -4.1 | -32,766 | 8 |
| holdout | book | 20 | 50% | +0.2 | +21,820 | 10 |
| holdout | kept | 18 | 56% | +2.1 | +51,454 | 8 |
| holdout | removed | 2 | 0% | -17.1 | -29,634 | 2 |
| all | book | 75 | 57% | +10.0 | +1,076,644 | 32 |
| all | kept | 63 | 65% | +13.1 | +1,139,044 | 22 |
| all | removed | 12 | 17% | -6.3 | -62,400 | 10 |

Verdict for this rule: **PROPOSE** — passes discovery, shuffle and holdout.

### Every search family, one line each

| family | rule | disc kept n / win / losers | disc removed n / win / losers | p | hold kept n / win / losers | hold removed n / win / Rs | verdict |
|---|---|---|---|---|---|---|---|
| F1 single, raw weather | `dist_hi < 153.4` | 38 / 76% / 9 | 17 / 24% / 13 | 0.145 | 19 / 47% / 10 | 1 / 100% / +618 | REJECTED |
| F2 pair, raw weather | `dist_hi < 153.4 AND opt_run < 0.5164` | 35 / 83% / 6 | 20 / 20% / 16 | 0.195 | 18 / 44% / 10 | 2 / 100% / +1,190 | REJECTED |
| F3 single, raw+derived+text+trigger | `dist_hi < 153.4` | 38 / 76% / 9 | 17 / 24% / 13 | 0.180 | 19 / 47% / 10 | 1 / 100% / +618 | REJECTED |
| F4 pair, raw+derived+text+trigger | `dist_hi < 153.4 AND optrun_x_optimb < 0.4537` | 34 / 85% / 5 | 21 / 19% / 17 | 0.085 | 18 / 44% / 10 | 2 / 100% / +1,190 | REJECTED |
| F5 greedy triple, raw+derived+text+trigger | `dist_hi < 153.4 AND optrun_x_optimb < 0.4537 AND e_iv_atm >= 14.13` | 29 / 93% / 2 | 26 / 23% / 20 | 0.075 | 18 / 44% / 10 | 2 / 100% / +1,190 | REJECTED |
| F6 single, raw+derived+text+trigger, 9 lines | `dist_hi < 153.4` | 38 / 76% / 9 | 17 / 24% / 13 | 0.210 | 19 / 47% / 10 | 1 / 100% / +618 | REJECTED |
| F7 pair, raw+derived+text+trigger, 9 lines | `dist_hi < 153.4 AND optrun_x_optimb < 0.4537` | 34 / 85% / 5 | 21 / 19% / 17 | 0.165 | 18 / 44% / 10 | 2 / 100% / +1,190 | REJECTED |
| F8 pair, derived mathematics only | `gamma_x_mv30 >= 0.003918 AND optrun_x_optimb < 0.4537` | 32 / 78% / 7 | 23 / 35% / 15 | 0.785 | 10 / 50% / 5 | 10 / 50% / +48,474 | REJECTED |
| F9 pair, book's own situation + calendar | `weekday < 4 AND n_today < 11` | 40 / 75% / 10 | 15 / 20% / 12 | 0.190 | 16 / 44% / 9 | 4 / 75% / +84,012 | REJECTED |
| F10 single, agree_same only (family unanimity) | `agree_same >= 6` | 45 / 69% / 14 | 10 / 20% / 8 | 0.005 | 18 / 56% / 8 | 2 / 0% / -29,634 | PROPOSE |

### Reading

Same picture as c20_9y. The wide searches find `dist_hi < 153.4` (points to today's high) with `opt_run` / `optrun_x_optimb` as the second clause: best p 0.075-0.085, never under 0.05, and on holdout the kept side wins 44-47 % against the book's 50 % while the removed side is the profitable one. Rejected. The unanimity clause `agree_same >= 6` (one-feature F10 search, formed on c20_9y, tested here) removes 10 discovery trades (2 winners, 8 losers, Rs -33k) and 2 holdout trades (both losers, Rs -30k); kept side 69 % vs 60 % on discovery, 56 % vs 50 % on holdout; p = 0.005 in that search. It passes every gate. It does not remove the losers: 22 remain in 63 kept trades across 14 days. The abstaining sibling on c20_9s's agree_same = 5 trades is c20_9t or c20_9y.

**Verdict for c20_9s: PROPOSE**

## c20_9v

Record: 82 trades, 62% win, mean +8.8%, Rs +1,062,207, 31 losers over 14 days. Discovery: 61 trades, 66% win, mean +11.7%, Rs +1,029,902, 21 losers. Holdout: 21 trades, 52% win, mean +0.6%, Rs +32,305, 10 losers.
Features searched: 189 raw weather, 43 derived, 44 text indicators.

### Best rule found (F10 single, agree_same only (family unanimity))

### c20_9v: `agree_same >= 3`

Shuffle test p = 0.050 (does NOT beat luck). Search: best_single over the ONE feature agree_same (4 single masks), n_lines=5 (quantiles 10..90 % of discovery values), min_keep=20, score = share of losers removed - share of winners removed, discovery days only; shuffle = same search on 200 shufflings (seed 7).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 61 | 66% | +11.7 | +1,029,902 | 21 |
| discovery | kept | 50 | 72% | +14.6 | +1,037,049 | 14 |
| discovery | removed | 11 | 36% | -1.6 | -7,147 | 7 |
| holdout | book | 21 | 52% | +0.6 | +32,305 | 10 |
| holdout | kept | 19 | 58% | +2.5 | +61,938 | 8 |
| holdout | removed | 2 | 0% | -17.1 | -29,634 | 2 |
| all | book | 82 | 62% | +8.8 | +1,062,207 | 31 |
| all | kept | 69 | 68% | +11.3 | +1,098,988 | 22 |
| all | removed | 13 | 31% | -4.0 | -36,780 | 9 |

Verdict for this rule: **REJECTED** — shuffle p=0.050 >= 0.05.

### Every search family, one line each

| family | rule | disc kept n / win / losers | disc removed n / win / losers | p | hold kept n / win / losers | hold removed n / win / Rs | verdict |
|---|---|---|---|---|---|---|---|
| F1 single, raw weather | `er_day < 0.09161` | 40 / 78% / 9 | 21 / 43% / 12 | 0.845 | 3 / 33% / 2 | 18 / 56% / +46,322 | REJECTED |
| F2 pair, raw weather | `oi_own_chg15 >= -4.57e+05 AND opt_run < 0.502` | 34 / 88% / 4 | 27 / 37% / 17 | 0.345 | 11 / 45% / 6 | 10 / 60% / +65,358 | REJECTED |
| F3 single, raw+derived+text+trigger | `opt_opp_q=DRAIN-FAST < 1` | 44 / 77% / 10 | 17 / 35% / 11 | 0.715 | 15 / 40% / 9 | 6 / 83% / +92,027 | REJECTED |
| F4 pair, raw+derived+text+trigger | `oi_own_chg15 >= -4.57e+05 AND opt_run < 0.502` | 34 / 88% / 4 | 27 / 37% / 17 | 0.460 | 11 / 45% / 6 | 10 / 60% / +65,358 | REJECTED |
| F5 greedy triple, raw+derived+text+trigger | `oi_own_chg15 >= -4.57e+05 AND opt_run < 0.502 AND skew_atm < 0.17` | 31 / 94% / 2 | 30 / 37% / 19 | 0.550 | 10 / 50% / 5 | 11 / 55% / +52,767 | REJECTED |
| F6 single, raw+derived+text+trigger, 9 lines | `opt_opp_q=DRAIN-FAST < 1` | 44 / 77% / 10 | 17 / 35% / 11 | 0.865 | 15 / 40% / 9 | 6 / 83% / +92,027 | REJECTED |
| F7 pair, raw+derived+text+trigger, 9 lines | `pos_in_range >= 0.1085 AND spread_pct >= 0.172` | 37 / 86% / 5 | 24 / 33% / 16 | 0.655 | 18 / 50% / 9 | 3 / 67% / +9,191 | REJECTED |
| F8 pair, derived mathematics only | `kv_x_kvt >= 0.0221 AND optrun_x_optimb < 0.4397` | 48 / 79% / 10 | 13 / 15% / 11 | 0.455 | 17 / 47% / 9 | 4 / 75% / +87,822 | REJECTED |
| F9 pair, book's own situation + calendar | `agree_same >= 3 AND adv_vetoes_raw >= 2` | 40 / 78% / 9 | 21 / 43% / 12 | 0.705 | 18 / 61% / 7 | 3 / 0% / -30,189 | REJECTED |
| F10 single, agree_same only (family unanimity) | `agree_same >= 3` | 50 / 72% / 14 | 11 / 36% / 7 | 0.050 | 19 / 58% / 8 | 2 / 0% / -29,634 | REJECTED |

### Reading

Nothing passes. The best wide-search rule (`oi_own_chg15 >= -4.57e5 AND opt_run < 0.502`) has p = 0.35-0.46 and loses on holdout. The unanimity clause `agree_same >= 3` (one-feature search) is on the line: p = 0.050, removes 11 discovery trades (4 winners, 7 losers) and 2 holdout trades (both losers), kept 72 % vs 66 % and 58 % vs 52 %. Rejected by the letter (p is not under 0.05), reported because it is the same mechanism that passes on c20_9y and c20_9s.

**Verdict for c20_9v: NONE**

## c20_9x

Record: 81 trades, 53% win, mean +8.6%, Rs +1,004,809, 38 losers over 14 days. Discovery: 60 trades, 55% win, mean +11.6%, Rs +985,368, 27 losers. Holdout: 21 trades, 48% win, mean +0.0%, Rs +19,442, 11 losers.
Features searched: 188 raw weather, 43 derived, 50 text indicators.

### Best rule found (F5 greedy triple, raw+derived+text+trigger)

### c20_9x: `hw_book_imb_t >= -0.2908 AND opt_opp_q=DRAIN-FAST < 1 AND regime_ext_pct < 95.1`

Shuffle test p = 0.050 (does NOT beat luck). Search: best_pair then best third clause over 281 features (2458 single masks), n_lines=5 (quantiles 10..90 % of discovery values), min_keep=20, score = share of losers removed - share of winners removed, discovery days only; shuffle = same search on 200 shufflings of discovery outcomes (seed 7).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 60 | 55% | +11.6 | +985,368 | 27 |
| discovery | kept | 34 | 85% | +23.8 | +995,147 | 5 |
| discovery | removed | 26 | 15% | -4.4 | -9,779 | 22 |
| holdout | book | 21 | 48% | +0.0 | +19,442 | 11 |
| holdout | kept | 14 | 36% | -5.5 | -65,670 | 9 |
| holdout | removed | 7 | 71% | +11.1 | +85,111 | 2 |
| all | book | 81 | 53% | +8.6 | +1,004,809 | 38 |
| all | kept | 48 | 71% | +15.3 | +929,477 | 14 |
| all | removed | 33 | 27% | -1.1 | +75,332 | 24 |

Verdict for this rule: **REJECTED** — shuffle p=0.050 >= 0.05; holdout: kept win rate below book's or removed side profitable.

### Every search family, one line each

| family | rule | disc kept n / win / losers | disc removed n / win / losers | p | hold kept n / win / losers | hold removed n / win / Rs | verdict |
|---|---|---|---|---|---|---|---|
| F1 single, raw weather | `dist_hi < 153` | 42 / 69% / 13 | 18 / 22% / 14 | 0.370 | 20 / 45% / 11 | 1 / 100% / +618 | REJECTED |
| F2 pair, raw weather | `dist_hi < 153 AND spread_pct >= 0.1419` | 36 / 78% / 8 | 24 / 21% / 19 | 0.265 | 18 / 44% / 10 | 3 / 67% / +3,802 | REJECTED |
| F3 single, raw+derived+text+trigger | `opt_opp_q=DRAIN-FAST < 1` | 43 / 70% / 13 | 17 / 18% / 14 | 0.245 | 15 / 40% / 9 | 6 / 67% / +80,119 | REJECTED |
| F4 pair, raw+derived+text+trigger | `hw_book_imb_t >= -0.2908 AND opt_opp_q=DRAIN-FAST < 1` | 38 / 79% / 8 | 22 / 14% / 19 | 0.050 | 15 / 40% / 9 | 6 / 67% / +80,119 | REJECTED |
| F5 greedy triple, raw+derived+text+trigger | `hw_book_imb_t >= -0.2908 AND opt_opp_q=DRAIN-FAST < 1 AND regime_ext_pct < 95.1` | 34 / 85% / 5 | 26 / 15% / 22 | 0.050 | 14 / 36% / 9 | 7 / 71% / +85,111 | REJECTED |
| F6 single, raw+derived+text+trigger, 9 lines | `opt_opp_q=DRAIN-FAST < 1` | 43 / 70% / 13 | 17 / 18% / 14 | 0.315 | 15 / 40% / 9 | 6 / 67% / +80,119 | REJECTED |
| F7 pair, raw+derived+text+trigger, 9 lines | `opt_opp_q=DRAIN-FAST < 1 AND hw_book_imb_t >= -0.2908` | 38 / 79% / 8 | 22 / 14% / 19 | 0.145 | 15 / 40% / 9 | 6 / 67% / +80,119 | REJECTED |
| F8 pair, derived mathematics only | `oi_help5_over_own5 < 6.38 AND optrun_x_optimb < 0.4421` | 26 / 77% / 6 | 34 / 38% / 21 | 0.930 | 12 / 50% / 6 | 9 / 44% / -28,886 | REJECTED |
| F9 pair, book's own situation + calendar | `weekday < 4 AND ret_today < 38.47` | 26 / 77% / 6 | 34 / 38% / 21 | 0.390 | 18 / 39% / 11 | 3 / 100% / +94,237 | REJECTED |
| F10 single, agree_same only (family unanimity) | `agree_same >= 1` | 58 / 55% / 26 | 2 / 50% / 1 | 0.645 | 19 / 53% / 9 | 2 / 0% / -29,634 | REJECTED |

### Reading

The live champion. Every one of the ten searches fails. The strongest discovery rules (`hw_book_imb_t >= -0.29 AND opt_opp_q != DRAIN-FAST`, with or without `regime_ext_pct < 95`) reach p = 0.050 exactly on discovery, keep 79-85 % winners there, and then INVERT on holdout: kept side 36-40 % win and Rs -61k to -66k, removed side 67-71 % win and Rs +80k to +85k. Day by day, their discovery edge is two days (19 Oct: 8 of 9 losers removed; 23 Oct: all 4), and on 3 Nov (the 6/6 holdout day) they remove nothing. The unanimity idea cannot be applied to c20_9x: it fires first, so agree_same is 1 on 58 of its 60 discovery trades. Calendar signatures were checked by hand: expiry days (41 trades) 23W/18L, non-expiry 20W/20L; no day type separates winners from losers. Verdict NONE. The book's record stands as it is: 53 % win, Rs +1.0m, 38 losers of 81, and its 4-day holdout is Rs +19k at 48 %.

**Verdict for c20_9x: NONE**

## c20_9t

Record: 90 trades, 70% win, mean +3.9%, Rs +372,333, 27 losers over 14 days. Discovery: 67 trades, 72% win, mean +5.3%, Rs +383,324, 19 losers. Holdout: 23 trades, 65% win, mean -0.4%, Rs -10,992, 8 losers.
Features searched: 191 raw weather, 43 derived, 51 text indicators.

### Best rule found (F8 pair, derived mathematics only)

### c20_9t: `hwvol_x_futvol_surge < 1.296 AND swing_ahead_over_behind < 0.7953`

Shuffle test p = 0.010 (beats luck). Search: best_pair over 43 features (418 single masks), n_lines=5 (quantiles 10..90 % of discovery values), min_keep=20, score = share of losers removed - share of winners removed, discovery days only; shuffle = same search on 200 shufflings of discovery outcomes (seed 7).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 67 | 72% | +5.3 | +383,324 | 19 |
| discovery | kept | 35 | 94% | +9.1 | +385,817 | 2 |
| discovery | removed | 32 | 47% | +1.1 | -2,493 | 17 |
| holdout | book | 23 | 65% | -0.4 | -10,992 | 8 |
| holdout | kept | 10 | 70% | -1.0 | -7,312 | 3 |
| holdout | removed | 13 | 62% | +0.1 | -3,679 | 5 |
| all | book | 90 | 70% | +3.9 | +372,333 | 27 |
| all | kept | 45 | 89% | +6.9 | +378,505 | 5 |
| all | removed | 45 | 51% | +0.8 | -6,172 | 22 |

Verdict for this rule: **PROPOSE** — passes discovery, shuffle and holdout.

### Every search family, one line each

| family | rule | disc kept n / win / losers | disc removed n / win / losers | p | hold kept n / win / losers | hold removed n / win / Rs | verdict |
|---|---|---|---|---|---|---|---|
| F1 single, raw weather | `vix_chg5 >= 0` | 34 / 91% / 3 | 33 / 52% / 16 | 0.050 | 10 / 80% / 2 | 13 / 54% / -29,617 | REJECTED |
| F2 pair, raw weather | `fut_vol_surge < 1.307 AND swing_behind >= 23.64` | 41 / 93% / 3 | 26 / 38% / 16 | 0.060 | 12 / 58% / 5 | 11 / 73% / +25,812 | REJECTED |
| F3 single, raw+derived+text+trigger | `vix_chg5 >= 0` | 34 / 91% / 3 | 33 / 52% / 16 | 0.065 | 10 / 80% / 2 | 13 / 54% / -29,617 | REJECTED |
| F4 pair, raw+derived+text+trigger | `fut_vol_surge < 1.307 AND swing_behind >= 23.64` | 41 / 93% / 3 | 26 / 38% / 16 | 0.085 | 12 / 58% / 5 | 11 / 73% / +25,812 | REJECTED |
| F5 greedy triple, raw+derived+text+trigger | `fut_vol_surge < 1.307 AND swing_behind >= 23.64 AND max_pain_dist < 65.66` | 37 / 97% / 1 | 30 / 40% / 18 | 0.130 | 9 / 44% / 5 | 14 / 79% / +41,220 | REJECTED |
| F6 single, raw+derived+text+trigger, 9 lines | `vix_chg5 >= 0` | 34 / 91% / 3 | 33 / 52% / 16 | 0.100 | 10 / 80% / 2 | 13 / 54% / -29,617 | REJECTED |
| F7 pair, raw+derived+text+trigger, 9 lines | `fut_vol_surge < 1.307 AND swing_behind >= 23.64` | 41 / 93% / 3 | 26 / 38% / 16 | 0.180 | 12 / 58% / 5 | 11 / 73% / +25,812 | REJECTED |
| F8 pair, derived mathematics only | `hwvol_x_futvol_surge < 1.296 AND swing_ahead_over_behind < 0.7953` | 35 / 94% / 2 | 32 / 47% / 17 | 0.010 | 10 / 70% / 3 | 13 / 62% / -3,679 | PROPOSE |
| F9 pair, book's own situation + calendar | `ret_today < 45.16 AND ret_today_per_trade < 6.068` | 39 / 85% / 6 | 28 / 54% / 13 | 0.550 | 22 / 64% / 8 | 1 / 100% / +4,628 | REJECTED |
| F10 single, agree_same only (family unanimity) | `agree_same >= 2` | 51 / 78% / 11 | 16 / 50% / 8 | 0.030 | 19 / 68% / 6 | 4 / 50% / -17,180 | REJECTED |

### Reading

The family's tightest book (72 % win on discovery, 70 % overall) and the one whose holdout is already slightly negative (Rs -11k). The wide searches fail (`vix_chg5 >= 0` p = 0.05-0.10 and the removed side has as many winners as losers; `fut_vol_surge < 1.3 AND swing_behind >= 23.6` p = 0.06-0.18, inverts on holdout). The derived-only pair search F8 (43 features) found `hwvol_x_futvol_surge < 1.296 AND swing_ahead_over_behind < 0.7953` at p = 0.010: enter when neither the heavyweights' nor the futures' volume is surging, and the nearest 30-minute swing ahead is closer than the one behind. Discovery: kept 35, 94 % win, 2 losers, Rs +386k; removed 32, 47 %, 17 losers, Rs -2k. Holdout: kept 10, 70 % (book 65 %), 3 losers, Rs -7k; removed 13, 62 %, Rs -4k. It passes the letter of every gate and it is threshold-stable (moving either line by +-30 % changes the holdout card not at all or by one trade). But: the kept side LOST rupees on holdout; the rule sends away 13 of 23 holdout trades; and frozen on the five siblings its kept win rate is above the book on all of them in both windows while the holdout rupees say the opposite on four of five (removed side profitable, kept side negative). I read it as a weak PROPOSE: a real-looking quiet-tape filter whose holdout is 10 trades and whose rupee verdict is negative. The one-feature unanimity search (`agree_same >= 2`) removes 16 discovery trades split 8W/8L, so it fails the discovery gate here.

**Verdict for c20_9t: PROPOSE**

## c20_8x

Record: 82 trades, 50% win, mean +7.7%, Rs +828,230, 41 losers over 14 days. Discovery: 59 trades, 53% win, mean +11.1%, Rs +821,909, 28 losers. Holdout: 23 trades, 43% win, mean -1.1%, Rs +6,321, 13 losers.
Features searched: 188 raw weather, 43 derived, 49 text indicators.

### Best rule found (F5 greedy triple, raw+derived+text+trigger)

### c20_8x: `hw_book_imb_t >= -0.2916 AND opt_opp_q=DRAIN-FAST < 1 AND e_fut_tot_imb < 0.4256`

Shuffle test p = 0.205 (does NOT beat luck). Search: best_pair then best third clause over 280 features (2454 single masks), n_lines=5 (quantiles 10..90 % of discovery values), min_keep=20, score = share of losers removed - share of winners removed, discovery days only; shuffle = same search on 200 shufflings of discovery outcomes (seed 7).

| window | side | trades | win % | mean % | P&L Rs | losers |
|---|---|---|---|---|---|---|
| discovery | book | 59 | 53% | +11.1 | +821,909 | 28 |
| discovery | kept | 35 | 80% | +21.4 | +946,800 | 7 |
| discovery | removed | 24 | 12% | -3.9 | -124,891 | 21 |
| holdout | book | 23 | 43% | -1.1 | +6,321 | 13 |
| holdout | kept | 17 | 35% | -5.7 | -73,915 | 11 |
| holdout | removed | 6 | 67% | +12.0 | +80,236 | 2 |
| all | book | 82 | 50% | +7.7 | +828,230 | 41 |
| all | kept | 52 | 65% | +12.5 | +872,885 | 18 |
| all | removed | 30 | 23% | -0.7 | -44,655 | 23 |

Verdict for this rule: **REJECTED** — shuffle p=0.205 >= 0.05; holdout: kept win rate below book's or removed side profitable.

### Every search family, one line each

| family | rule | disc kept n / win / losers | disc removed n / win / losers | p | hold kept n / win / losers | hold removed n / win / Rs | verdict |
|---|---|---|---|---|---|---|---|
| F1 single, raw weather | `dist_hi < 152.1` | 41 / 63% / 15 | 18 / 28% / 13 | 0.955 | 22 / 41% / 13 | 1 / 100% / +699 | REJECTED |
| F2 pair, raw weather | `pos_in_range >= 0.1994 AND vix >= 15.98` | 22 / 86% / 3 | 37 / 32% / 25 | 0.625 | 9 / 67% / 3 | 14 / 29% / -61,942 | REJECTED |
| F3 single, raw+derived+text+trigger | `opt_opp_q=DRAIN-FAST < 1` | 43 / 65% / 15 | 16 / 19% / 13 | 0.625 | 17 / 35% / 11 | 6 / 67% / +80,236 | REJECTED |
| F4 pair, raw+derived+text+trigger | `hw_book_imb_t >= -0.2916 AND opt_opp_q=DRAIN-FAST < 1` | 38 / 74% / 10 | 21 / 14% / 18 | 0.400 | 17 / 35% / 11 | 6 / 67% / +80,236 | REJECTED |
| F5 greedy triple, raw+derived+text+trigger | `hw_book_imb_t >= -0.2916 AND opt_opp_q=DRAIN-FAST < 1 AND e_fut_tot_imb < 0.4256` | 35 / 80% / 7 | 24 / 12% / 21 | 0.205 | 17 / 35% / 11 | 6 / 67% / +80,236 | REJECTED |
| F6 single, raw+derived+text+trigger, 9 lines | `opt_opp_q=DRAIN-FAST < 1` | 43 / 65% / 15 | 16 / 19% / 13 | 0.780 | 17 / 35% / 11 | 6 / 67% / +80,236 | REJECTED |
| F7 pair, raw+derived+text+trigger, 9 lines | `pos_in_range >= 0.1176 AND e_iv_atm >= 14.79` | 36 / 75% / 9 | 23 / 17% / 19 | 0.605 | 22 / 45% / 12 | 1 / 0% / -5,902 | REJECTED |
| F8 pair, derived mathematics only | `gamma_x_mv30 >= 0.003882 AND optrun_x_optimb < 0.4195` | 35 / 71% / 10 | 24 / 25% / 18 | 0.475 | 12 / 42% / 7 | 11 / 45% / +48,834 | REJECTED |
| F9 pair, book's own situation + calendar | `hrs_to_expiry >= 2.259 AND dte < 4` | 30 / 70% / 9 | 29 / 34% / 19 | 0.545 | 12 / 67% / 4 | 11 / 18% / -67,275 | REJECTED |
| F10 single, agree_same only (family unanimity) | `agree_same >= 0` | 59 / 53% / 28 | 0 / - / 0 | 1.000 | 23 / 43% / 13 | 0 / - / +0 | REJECTED |

### Reading

Nothing passes and nothing comes close: best p across ten searches is 0.20 (the greedy triple), the wide-search rules invert on holdout (kept 40 % vs book 43 %, removed profitable), and agree_same is undefined for this book (it is counted as -1 / None on every trade, so the unanimity rule cannot even be evaluated). Verdict NONE. The book's holdout is 43 % win, Rs +6k.

**Verdict for c20_8x: NONE**

## Across the family

Sixty pre-registered searches (6 books x 10 families, each shuffle-tested with its own search) and one post-hoc idea. What the wide searches find on this family is a memory of the tape: the same two or three fields (`dist_hi`, `opt_opp_q = DRAIN-FAST`, `hw_book_imb_t`, `agree_same`) keep 80-97 % winners on discovery, reach p = 0.01-0.05 when the shuffle bar is at its lowest, and then invert on the 4 held-out days on every book. That is the expected outcome for 55-67 trades: a search over 280 fields x pairs finds a 29-kept / 4-loser rule in random labels about a quarter of the time, and the owner's rule 4 (holdout) is what catches it. Two things survive. (1) Family unanimity: a council variant's trade loses when a sibling abstains. On c20_9y all 12 such trades over 14 days lost (7 when c20_9s abstained, 5 when c20_9t did); on c20_9s 10 of 12; on c20_9v 9 of 13. Pre-registered p for c20_9y is 0.030 (pair) / 0.055 (single); the sibling echo is the real evidence. It removes 12-14 % of trades and about a third of the losers, never all of them. It cannot help c20_9x, which fires first. (2) c20_9t's quiet-tape pair (p = 0.010, threshold-stable) passes by the letter with a negative-rupee holdout on 10 kept trades; weak. Honest answer to the owner's question 'remove the losses completely': no rule found on these 14 days does that on any of the six books, and the ones that appear to on discovery are the ones that lose on holdout. Multiplicity: with 54 pre-registered wide/narrow searches, about 2.7 would pass the shuffle gate by luck alone; two did and also passed holdout. Treat the proposals as candidates for the register's live shadow count, not as proven.

