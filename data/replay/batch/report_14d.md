# 14-day replay: which rule fits which book (for Sunday 8 Nov review)

Replay of all 87 books on 19 Oct – 6 Nov (14 trading days, 4 folders full_g1..g4, seeded from live data, missed-signal
recorder on). 9,249 trades, 5,434 missed-signal rows, 0 errors, 0 recorder faults, engine logs clean.

**Everything below is in-sample.** R-002..R-005 were written after these days, so nothing here counts as a pass under
the 7-test standard. Real scoring starts with live trades from Mon 9 Nov.

## 1. Rule books vs free books (past days, information only)

| Rule | Book | Rule book: trades, strike, mean/trade | Free book | Reading |
|---|---|---|---|---|
| R-002 (trend last hour) | spot_dc12_t12 | 60, 45 %, +1.69 % | 291, 36 %, +0.62 % | fits |
| R-002 | spot_dc12_t12_first | 131, 44 %, +1.17 % | 603, 38 %, +0.18 % | fits |
| R-002 | spot_pb45 | 12, 58 %, −5.76 % | 57, 54 %, +1.14 % | hurts |
| R-002 | spot_orb45 | 5, 80 %, +0.62 % | 17, 88 %, +9.40 % | hurts (keeps few ORB trades) |
| R-002 | c20_9x | 41, 56 %, +6.24 % | 81, 53 %, +8.60 % | hurts a little |
| R-002 | fade_switch | 469, 49 %, −0.01 % | 757, 51 %, −0.01 % | no effect |
| R-002 | m1.5_s0.4 | 6, 50 %, +2.06 % | 20, 50 %, +1.29 % | too few trades |
| R-002 | gap3_s0.4 | 2, 100 %, +7.90 % | 6, 67 %, +2.83 % | too few trades |
| R-003 (breadth ≥ 60 %) | spot_dc12_t12_first | 577, 37 %, +0.15 % | 603, 38 %, +0.18 % | almost no effect |
| R-003 | spot_orb45 | 16, 88 %, +8.75 % | 17, 88 %, +9.40 % | almost no effect |
| R-003 | m1.5_s0.4, gap3_s0.4 | identical to free | | no effect |
| R-003 | spot_pb45 | **0 trades** | 57, 54 %, +1.14 % | **cannot ever trade (see 3)** |
| R-004 (council normal days before 12:00) | c20_9x | 63, 52 %, +8.40 % | 81, 53 %, +8.60 % | no help |
| R-005 (ORB before 14:30) | spot_orb45 | identical to free | | no ORB entry after 14:30 in 14 days |

## 2. Weather cards (search of the past, a candidate is not a rule)

14 of 24 families had enough trades to search (30 or more). Two lines beat luck; about 0.7 would by chance alone, so
this is weak evidence.

* **FADE on normal days (fade_switch):** enter only if the ATM straddle rose less than 1.67 points in the last
  5 minutes. Kept 262 trades, 54 %, +0.63 % against 68 trades, 31 %, −1.12 %; keeps 32 of 40 big wins. 11 days.
* **SPOT-BREAKOUT on expiry days (spot_dc12_t12_first):** enter only if the last 30 minutes' efficiency ratio is
  ≥ 0.072 (i.e. not dead flat). Kept 81 trades, 50 %, +1.59 % against 19 trades, 11 %, −5.54 %. Only 2 expiry days:
  fragile.

The other searched families (council, follow, retest, pullback, forward pullback) show no line that beats luck.

## 3. Fault found: R-003 cannot work on pullbacks

R-003 asks that 60 % of the heavyweights moved our way in the last 5 minutes. A pullback entry comes after a few
minutes against the trend by design, so at spot_pb45's 57 entries breadth was between 0 % and 57 % (median 14 %);
never 60 %. spot_pb45_r003 will take no trades, never complete a window and never be scored. This was a mistake in
putting SPOT-PULLBACK into R-003, not a market finding.

## 4. Decisions for the owner

1. spot_pb45_r003: record it as "off" (status line, register untouched), or leave it running empty.
2. Whether to freeze either card line as a new rule (R-019, R-020) today so it tests from Monday. The FADE line has
   11 days behind it; the breakout-expiry line only 2.

## 5. Checks done 8 Nov

* **Gate item 5 passed:** 6 Nov 09:15–11:15 replayed with the shared council day data locked read-only during
  every recorder twin and counterfactual step (909,284 locked steps): 0 write attempts, 0 errors, 0 faults, and
  identical to the earlier unguarded run in every book, decision, strike, missed row and event (the only
  difference: spot_pb45_r003, switched off since). Guard lived in the scratchpad only; removed after.
* **Replay vs live, all 14 days:** 69 % of 5,417 live trades matched within 3 s. 19 Oct 3 % (live ran v1.2.1),
  21 Oct 41 % (v1.5.0), 22 Oct–6 Nov 64–88 % (v1.9.0 with 20 later commits), 6 Nov 80 %. Remaining misses are
  the known ones: premium_momentum delta-floor fix, `_fill` books' fill timing, spot_dc12 sampling phase.

Files: scratchpad full_out/diary.jsonl, cards.md, cards.json, restricted_insample.json.
