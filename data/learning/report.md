# ApexOptions — learning report (2026-10-23)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `spot_dual_lvl`
5 trades since 2026-10-22, Σ +129.2 %. GO line 1004.4, KILL line -554.7 → **COLLECTING**. Observed sd 23.8 % vs assumed 30 %.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #4 since registration (2026-10-17); evening looks: 1 for this champion, 4 since registration. Every new champion and every look is another chance at a false GO.
- Wald lines with the observed sd: need ≥ 10 trades (have 5).
- SPRT on per-trade 100·ln(1+r): Σ +107.8 (mean +21.56/trade) vs GO 1004.4 / KILL -554.7 → would be **COLLECTING**.
- Betting e-value against "mean ≤ 0" (returns clipped to [−100, +300] %, λ mixture 0.05, 0.1, 0.2, 0.4, 0.8): **1.51** — ≥ 20 would reject at 5 % under any number of looks.

Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:

- [ ] ≥ 15 sessions (1)
- [ ] ≥ 2 expiry days (0)
- [ ] every leave-one-day-out mean > 0
- [ ] total > 0 with the best day dropped
- [ ] no single day > 40 % of the total
- [x] ≥ 50 % of days net-green
- [ ] beats every control (0/3)

## Challengers (daily return vs champion since it took over; one-sided α 0.0018 each, 28 challengers; 2 passing evenings in a row to promote)

| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |
|---|---|---|---|---|---|---|
| m1.5_s0.4 | 1 | -103.95 | 0.00 | inf | no | 0 |
| m1.5_s0.5 | 1 | -112.54 | 0.00 | inf | no | 0 |
| m1.5_s0.6 | 1 | -105.51 | 0.00 | inf | no | 0 |
| m2.0_s0.4 | 1 | -103.95 | 0.00 | inf | no | 0 |
| m2.0_s0.5 | 1 | -112.54 | 0.00 | inf | no | 0 |
| m2.0_s0.6 | 1 | -105.51 | 0.00 | inf | no | 0 |
| m2.5_s0.4 | 1 | -103.95 | 0.00 | inf | no | 0 |
| m2.5_s0.5 | 1 | -112.54 | 0.00 | inf | no | 0 |
| m2.5_s0.6 | 1 | -105.51 | 0.00 | inf | no | 0 |
| gap3_s0.4 | 1 | -107.81 | 0.00 | inf | no | 0 |
| gap5_s0.4 | 1 | -107.81 | 0.00 | inf | no | 0 |
| m2.0_s0.5_bookexit | 1 | -115.43 | 0.00 | inf | no | 0 |
| straddle_spike | 1 | -99.51 | 0.00 | inf | no | 0 |
| m2.0_s0.5_ivinterp | 1 | -112.54 | 0.00 | inf | no | 0 |
| m2.0_s0.5_novol | 1 | -98.66 | 0.00 | inf | no | 0 |
| m2.0_s0.5_trend | 1 | -105.51 | 0.00 | inf | no | 0 |
| spot_dc12_t12 | 1 | -126.16 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first | 1 | -110.41 | 0.00 | inf | no | 0 |
| spot_dc12_t12_1130 | 1 | -126.16 | 0.00 | inf | no | 0 |
| spot_dc12_t12_nolock | 1 | -126.16 | 0.00 | inf | no | 0 |
| spot_pb45 | 1 | -57.83 | 0.00 | inf | no | 0 |
| spot_dual | 1 | -57.83 | 0.00 | inf | no | 0 |
| spot_dual_rg | 1 | -57.83 | 0.00 | inf | no | 0 |
| spot_ft_prem10 | 1 | -112.86 | 0.00 | inf | no | 0 |
| spot_orb45 | 1 | -93.21 | 0.00 | inf | no | 0 |
| m2.0_s0.5_d20 | 1 | -114.94 | 0.00 | inf | no | 0 |
| m2.0_s0.5_tvfast | 1 | -111.48 | 0.00 | inf | no | 0 |
| fade_switch | 1 | -91.07 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +145.76 | 0.00 | inf | too few days |
| random_entry | 1 | +109.49 | 0.00 | inf | too few days |
| premium_momentum | 1 | +117.60 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 65 | 0 | +0.60 | +0.60 | +0.00 | 0% | no | advisory |
| room | 65 | 10 | +0.60 | +1.10 | +0.50 | 6% | no | advisory |
| coherence | 65 | 41 | +0.60 | +2.55 | +1.95 | 59% | no | advisory |
| force | 65 | 2 | +0.60 | +0.69 | +0.09 | 0% | no | advisory |
| episode | 65 | 2 | +0.60 | +0.33 | -0.26 | 6% | no | advisory |
| book | 65 | 21 | +0.60 | +0.99 | +0.40 | 29% | no | advisory |
| premium | 65 | 17 | +0.60 | +1.23 | +0.63 | 18% | no | advisory |
| quiet | 65 | 0 | +0.60 | +0.60 | +0.00 | 0% | no | advisory |
| bank | 65 | 9 | +0.60 | -0.52 | -1.11 | 24% | no | advisory |
| event | 65 | 0 | +0.60 | +0.60 | +0.00 | 0% | no | advisory |
| gamma_leg | 65 | 0 | +0.60 | +0.60 | +0.00 | 0% | no | advisory |
| gex_room | 65 | 20 | +0.60 | +1.01 | +0.41 | 24% | no | advisory |
| regime | 65 | 48 | +0.60 | +3.54 | +2.94 | 53% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| spot_dual_lvl | DIRECTIONAL | 2 | +32.40 | 100% |
| spot_dual_lvl | RANGE | 2 | +32.20 | 100% |
| spot_dual_lvl | WARMING | 1 | -0.03 | 0% |
| RAW | BREAKOUT | 3 | -1.41 | 33% |
| RAW | COMPRESSION | 14 | -4.12 | 7% |
| RAW | DIRECTIONAL | 19 | +3.05 | 53% |
| RAW | EXHAUSTION | 2 | -3.92 | 0% |
| RAW | RANGE | 17 | +3.77 | 59% |
| RAW | UNCERTAIN | 8 | -2.21 | 38% |
| RAW | WARMING | 2 | +2.20 | 50% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

283 candidate(s) inside a feed-defect window are quarantined (D-101) and not counted below.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| fade_switch | 1 | +3.66 | 100% | +3.7 / +3.7 | 0 | CAS-ENTRY 1 |

## Quarantined evidence (D-101) — kept on file, NOT counted anywhere above

- 2026-10-19: defect window(s) whole session (declared) — trades entered inside are excluded for every book.

| day | book | time in-out | contract | entry → exit | recorded ret % | why |
|---|---|---|---|---|---|---|
| 2026-10-19 | RAW | 09:44:11-09:44:34 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | RAW | 12:53:10-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 105.3 → 101.95 | -3.18 | whole session declared defective |
| 2026-10-19 | RAW | 12:53:41-12:54:10 | NIFTY|OPT|2026-10-19|22850|CE | 92.25 → 86.85 | -5.85 | whole session declared defective |
| 2026-10-19 | RAW | 12:54:22-12:54:42 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 110.35 | -1.78 | whole session declared defective |
| 2026-10-19 | RAW | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | RAW | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.6 | -2.58 | whole session declared defective |
| 2026-10-19 | RAW | 13:12:54-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 81.55 → 80.0 | -1.90 | whole session declared defective |
| 2026-10-19 | RAW | 13:17:10-13:17:43 | NIFTY|OPT|2026-10-19|22950|PE | 75.15 → 73.0 | -2.86 | whole session declared defective |
| 2026-10-19 | RAW | 13:17:44-13:17:52 | NIFTY|OPT|2026-10-19|22850|CE | 78.3 → 72.55 | -7.34 | whole session declared defective |
| 2026-10-19 | RAW | 13:17:57-13:20:47 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 88.3 | +8.88 | whole session declared defective |
| 2026-10-19 | RAW | 13:20:47-13:22:56 | NIFTY|OPT|2026-10-19|22800|CE | 98.7 → 91.5 | -7.29 | whole session declared defective |
| 2026-10-19 | RAW | 13:25:02-13:25:57 | NIFTY|OPT|2026-10-19|22900|PE | 75.25 → 64.5 | -14.29 | whole session declared defective |
| 2026-10-19 | RAW | 13:25:57-13:27:18 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 79.0 | -7.28 | whole session declared defective |
| 2026-10-19 | RAW | 13:27:19-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 64.65 | -10.95 | whole session declared defective |
| 2026-10-19 | RAW | 13:42:11-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 98.8 → 93.15 | -5.72 | whole session declared defective |
| 2026-10-19 | RAW | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | RAW | 13:42:44-13:42:49 | NIFTY|OPT|2026-10-19|22800|CE | 93.25 → 90.15 | -3.32 | whole session declared defective |
| 2026-10-19 | RAW | 13:42:49-13:45:10 | NIFTY|OPT|2026-10-19|22950|PE | 93.1 → 108.25 | +16.27 | whole session declared defective |
| 2026-10-19 | RAW | 13:49:43-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 75.65 | -9.35 | whole session declared defective |
| 2026-10-19 | RAW | 14:22:13-14:24:43 | NIFTY|OPT|2026-10-19|22800|CE | 73.3 → 62.7 | -14.46 | whole session declared defective |
| 2026-10-19 | futures_only | 09:28:15-09:29:19 | NIFTY|OPT|2026-10-19|23200|PE | 238.15 → 249.5 | +4.77 | whole session declared defective |
| 2026-10-19 | futures_only | 09:31:14-09:32:40 | NIFTY|OPT|2026-10-19|22950|CE | 182.0 → 182.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 09:34:03-09:34:03 | NIFTY|OPT|2026-10-19|23200|PE | 156.75 → 151.6 | -3.29 | whole session declared defective |
| 2026-10-19 | futures_only | 09:37:03-09:37:16 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 09:39:03-09:39:31 | NIFTY|OPT|2026-10-19|23200|PE | 113.65 → 114.35 | +0.62 | whole session declared defective |
| 2026-10-19 | futures_only | 09:41:12-09:41:55 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 09:44:44-09:44:52 | NIFTY|OPT|2026-10-19|23200|PE | 106.65 → 104.3 | -2.20 | whole session declared defective |
| 2026-10-19 | futures_only | 09:52:38-09:53:20 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 09:53:21-09:53:39 | NIFTY|OPT|2026-10-19|23200|PE | 121.65 → 120.35 | -1.07 | whole session declared defective |
| 2026-10-19 | futures_only | 09:57:42-09:57:45 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 09:58:57-09:59:20 | NIFTY|OPT|2026-10-19|23200|PE | 181.25 → 189.15 | +4.36 | whole session declared defective |
| 2026-10-19 | futures_only | 10:00:43-10:01:03 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 10:01:45-10:02:10 | NIFTY|OPT|2026-10-19|23200|PE | 165.25 → 151.25 | -8.47 | whole session declared defective |
| 2026-10-19 | futures_only | 10:08:10-10:10:14 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 10:10:23-10:11:40 | NIFTY|OPT|2026-10-19|23200|PE | 163.75 → 156.0 | -4.73 | whole session declared defective |
| 2026-10-19 | futures_only | 10:16:57-10:17:53 | NIFTY|OPT|2026-10-19|23200|PE | 163.0 → 152.2 | -6.63 | whole session declared defective |
| 2026-10-19 | futures_only | 10:17:53-10:17:55 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 10:42:16-10:42:56 | NIFTY|OPT|2026-10-19|22950|CE | 182.0 → 182.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 10:42:56-10:44:07 | NIFTY|OPT|2026-10-19|23250|PE | 227.05 → 216.05 | -4.84 | whole session declared defective |
| 2026-10-19 | futures_only | 10:50:59-10:52:09 | NIFTY|OPT|2026-10-19|23250|PE | 232.55 → 216.3 | -6.99 | whole session declared defective |
| 2026-10-19 | futures_only | 10:56:10-11:00:23 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 11:00:23-11:00:40 | NIFTY|OPT|2026-10-19|23250|PE | 208.1 → 200.9 | -3.46 | whole session declared defective |
| 2026-10-19 | futures_only | 11:01:23-11:04:06 | NIFTY|OPT|2026-10-19|23250|PE | 208.85 → 203.15 | -2.73 | whole session declared defective |
| 2026-10-19 | futures_only | 11:06:22-11:06:48 | NIFTY|OPT|2026-10-19|23250|PE | 206.1 → 197.1 | -4.37 | whole session declared defective |
| 2026-10-19 | futures_only | 11:06:49-11:10:23 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 11:11:28-11:11:39 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 11:11:43-11:11:56 | NIFTY|OPT|2026-10-19|23250|PE | 183.2 → 183.75 | +0.30 | whole session declared defective |
| 2026-10-19 | futures_only | 11:11:57-11:12:27 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 11:13:42-11:14:09 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 11:16:22-11:17:48 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | futures_only | 11:28:15-11:30:13 | NIFTY|OPT|2026-10-19|23250|PE | 208.65 → 206.95 | -0.81 | whole session declared defective |
| 2026-10-19 | futures_only | 12:28:30-12:42:44 | NIFTY|OPT|2026-10-19|23350|PE | 421.85 → 429.1 | +1.72 | whole session declared defective |
| 2026-10-19 | futures_only | 12:42:44-12:45:01 | NIFTY|OPT|2026-10-19|22500|CE | 425.75 → 414.65 | -2.61 | whole session declared defective |
| 2026-10-19 | futures_only | 12:46:10-12:48:00 | NIFTY|OPT|2026-10-19|23000|PE | 100.55 → 107.5 | +6.91 | whole session declared defective |
| 2026-10-19 | futures_only | 12:52:32-12:52:42 | NIFTY|OPT|2026-10-19|23000|PE | 99.8 → 99.5 | -0.30 | whole session declared defective |
| 2026-10-19 | futures_only | 12:52:47-12:53:06 | NIFTY|OPT|2026-10-19|22850|CE | 93.6 → 89.8 | -4.06 | whole session declared defective |
| 2026-10-19 | futures_only | 12:53:10-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 105.3 → 101.95 | -3.18 | whole session declared defective |
| 2026-10-19 | futures_only | 12:53:41-12:54:10 | NIFTY|OPT|2026-10-19|22850|CE | 92.25 → 86.85 | -5.85 | whole session declared defective |
| 2026-10-19 | futures_only | 12:54:22-12:54:42 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 110.35 | -1.78 | whole session declared defective |
| 2026-10-19 | futures_only | 12:57:44-13:04:38 | NIFTY|OPT|2026-10-19|22850|CE | 77.75 → 103.2 | +32.73 | whole session declared defective |
| 2026-10-19 | futures_only | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | futures_only | 13:05:03-13:05:29 | NIFTY|OPT|2026-10-27|22900|CE | 203.95 → 201.0 | -1.45 | whole session declared defective |
| 2026-10-19 | futures_only | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.6 | -2.58 | whole session declared defective |
| 2026-10-19 | futures_only | 13:07:16-13:07:57 | NIFTY|OPT|2026-10-27|22900|CE | 206.45 → 203.8 | -1.28 | whole session declared defective |
| 2026-10-19 | futures_only | 13:08:00-13:12:54 | NIFTY|OPT|2026-10-27|23000|PE | 201.55 → 209.25 | +3.82 | whole session declared defective |
| 2026-10-19 | futures_only | 13:12:54-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 81.55 → 80.0 | -1.90 | whole session declared defective |
| 2026-10-19 | futures_only | 13:14:58-13:17:43 | NIFTY|OPT|2026-10-19|23000|PE | 106.2 → 110.1 | +3.67 | whole session declared defective |
| 2026-10-19 | futures_only | 13:17:44-13:17:52 | NIFTY|OPT|2026-10-19|22850|CE | 78.3 → 72.55 | -7.34 | whole session declared defective |
| 2026-10-19 | futures_only | 13:17:57-13:20:47 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 88.3 | +8.88 | whole session declared defective |
| 2026-10-19 | futures_only | 13:20:47-13:22:56 | NIFTY|OPT|2026-10-19|22800|CE | 98.7 → 91.5 | -7.29 | whole session declared defective |
| 2026-10-19 | futures_only | 13:23:21-13:25:01 | NIFTY|OPT|2026-10-19|22800|CE | 86.7 → 75.6 | -12.80 | whole session declared defective |
| 2026-10-19 | futures_only | 13:25:01-13:25:57 | NIFTY|OPT|2026-10-19|22900|PE | 75.25 → 64.5 | -14.29 | whole session declared defective |
| 2026-10-19 | futures_only | 13:25:57-13:27:18 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 79.0 | -7.28 | whole session declared defective |
| 2026-10-19 | futures_only | 13:27:19-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 64.65 | -10.95 | whole session declared defective |
| 2026-10-19 | futures_only | 13:35:18-13:36:13 | NIFTY|OPT|2026-10-19|22800|CE | 87.25 → 81.85 | -6.19 | whole session declared defective |
| 2026-10-19 | futures_only | 13:36:27-13:42:22 | NIFTY|OPT|2026-10-19|22800|CE | 91.15 → 94.9 | +4.11 | whole session declared defective |
| 2026-10-19 | futures_only | 13:42:22-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.15 → 90.0 | +0.95 | whole session declared defective |
| 2026-10-19 | futures_only | 13:42:33-13:42:49 | NIFTY|OPT|2026-10-19|22800|CE | 95.0 → 90.15 | -5.11 | whole session declared defective |
| 2026-10-19 | futures_only | 13:42:49-13:45:10 | NIFTY|OPT|2026-10-19|22950|PE | 93.1 → 108.25 | +16.27 | whole session declared defective |
| 2026-10-19 | futures_only | 13:49:42-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.05 → 75.65 | -8.91 | whole session declared defective |
| 2026-10-19 | futures_only | 14:10:32-14:12:54 | NIFTY|OPT|2026-10-19|22800|CE | 90.4 → 81.1 | -10.29 | whole session declared defective |
| 2026-10-19 | futures_only | 14:16:17-14:17:55 | NIFTY|OPT|2026-10-19|22800|CE | 77.8 → 71.85 | -7.65 | whole session declared defective |
| 2026-10-19 | futures_only | 14:22:07-14:24:03 | NIFTY|OPT|2026-10-19|22800|CE | 71.55 → 62.8 | -12.23 | whole session declared defective |
| 2026-10-19 | futures_only | 14:32:04-14:38:20 | NIFTY|OPT|2026-10-19|22800|CE | 75.7 → 62.0 | -18.10 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 09:37:09-09:37:16 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 09:44:07-09:44:34 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 12:28:30-12:31:14 | NIFTY|OPT|2026-10-19|23350|PE | 421.85 → 414.9 | -1.65 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 12:54:27-12:54:42 | NIFTY|OPT|2026-10-19|22950|PE | 77.75 → 73.25 | -5.79 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 13:04:20-13:04:33 | NIFTY|OPT|2026-10-27|22950|CE | 185.0 → 178.75 | -3.38 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 13:05:32-13:07:15 | NIFTY|OPT|2026-10-27|23000|PE | 205.2 → 198.9 | -3.07 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 13:18:00-13:20:43 | NIFTY|OPT|2026-10-19|22950|PE | 82.75 → 87.8 | +6.10 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 13:25:57-13:27:18 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 79.0 | -7.28 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 13:27:19-13:28:13 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 67.55 | -6.96 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 13:30:20-13:32:02 | NIFTY|OPT|2026-10-19|22800|CE | 78.6 → 77.3 | -1.65 | whole session declared defective |
| 2026-10-19 | gap3_s0.4 | 13:41:31-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 97.5 → 94.45 | -3.13 | whole session declared defective |
| 2026-10-19 | gap5_s0.4 | 09:37:10-09:38:15 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | gap5_s0.4 | 09:44:07-09:44:34 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | gap5_s0.4 | 13:04:20-13:04:33 | NIFTY|OPT|2026-10-27|22950|CE | 185.0 → 178.75 | -3.38 | whole session declared defective |
| 2026-10-19 | gap5_s0.4 | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | gap5_s0.4 | 13:05:32-13:07:15 | NIFTY|OPT|2026-10-27|23000|PE | 205.2 → 198.9 | -3.07 | whole session declared defective |
| 2026-10-19 | gap5_s0.4 | 13:18:00-13:20:43 | NIFTY|OPT|2026-10-19|22950|PE | 82.75 → 87.8 | +6.10 | whole session declared defective |
| 2026-10-19 | gap5_s0.4 | 13:26:01-13:27:18 | NIFTY|OPT|2026-10-19|22800|CE | 86.85 → 79.0 | -9.04 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 09:37:09-09:37:16 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 09:44:07-09:47:13 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 11:00:26-11:00:40 | NIFTY|OPT|2026-10-19|23250|PE | 206.85 → 200.9 | -2.88 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 11:16:27-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 12:28:30-12:31:14 | NIFTY|OPT|2026-10-19|23350|PE | 421.85 → 414.9 | -1.65 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 12:52:54-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 100.9 → 101.95 | +1.04 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 12:53:40-12:53:57 | NIFTY|OPT|2026-10-19|22850|CE | 93.15 → 90.8 | -2.52 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 12:54:22-12:54:42 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 110.35 | -1.78 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 12:57:45-13:04:33 | NIFTY|OPT|2026-10-19|22850|CE | 77.05 → 104.95 | +36.21 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:04:37-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.1 → 199.5 | +2.25 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 202.7 → 198.6 | -2.02 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:12:54-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 82.2 → 80.0 | -2.68 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:15:04-13:17:32 | NIFTY|OPT|2026-10-19|23000|PE | 108.55 → 111.8 | +2.99 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:17:44-13:17:52 | NIFTY|OPT|2026-10-19|22850|CE | 78.3 → 72.55 | -7.34 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:17:57-13:20:43 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 87.8 | +8.26 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:20:43-13:22:56 | NIFTY|OPT|2026-10-19|22800|CE | 98.65 → 91.5 | -7.25 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:24:22-13:24:59 | NIFTY|OPT|2026-10-19|22800|CE | 85.35 → 76.65 | -10.19 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:25:02-13:25:51 | NIFTY|OPT|2026-10-19|22900|PE | 75.25 → 67.8 | -9.90 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:25:57-13:27:18 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 79.0 | -7.28 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:27:19-13:28:13 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 67.55 | -6.96 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:28:14-13:28:52 | NIFTY|OPT|2026-10-19|22800|CE | 82.9 → 77.8 | -6.15 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:41:27-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 94.6 → 94.45 | -0.16 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:42:43-13:42:49 | NIFTY|OPT|2026-10-19|22800|CE | 97.65 → 90.15 | -7.68 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:42:49-13:45:07 | NIFTY|OPT|2026-10-19|22950|PE | 93.1 → 106.4 | +14.29 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 13:49:43-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 75.65 | -9.35 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 14:10:33-14:12:54 | NIFTY|OPT|2026-10-19|22800|CE | 90.4 → 81.1 | -10.29 | whole session declared defective |
| 2026-10-19 | m1.5_s0.4 | 14:22:13-14:24:41 | NIFTY|OPT|2026-10-19|22800|CE | 73.3 → 63.0 | -14.05 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 09:44:11-09:44:34 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 12:53:06-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 104.9 → 101.95 | -2.81 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 12:53:40-12:54:10 | NIFTY|OPT|2026-10-19|22850|CE | 93.15 → 86.85 | -6.76 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 12:54:22-12:54:42 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 110.35 | -1.78 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.6 | -2.58 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:12:54-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 81.55 → 80.0 | -1.90 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:17:10-13:17:43 | NIFTY|OPT|2026-10-19|22950|PE | 76.5 → 73.0 | -4.58 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:17:44-13:17:52 | NIFTY|OPT|2026-10-19|22850|CE | 78.3 → 72.55 | -7.34 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:17:57-13:20:47 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 88.3 | +8.88 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:20:47-13:22:56 | NIFTY|OPT|2026-10-19|22800|CE | 98.7 → 91.5 | -7.29 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:24:27-13:24:59 | NIFTY|OPT|2026-10-19|22800|CE | 87.15 → 76.65 | -12.05 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:25:02-13:25:57 | NIFTY|OPT|2026-10-19|22900|PE | 75.25 → 64.5 | -14.29 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:25:57-13:27:18 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 79.0 | -7.28 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:27:19-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 64.65 | -10.95 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:42:11-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 98.8 → 93.15 | -5.72 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:42:44-13:42:49 | NIFTY|OPT|2026-10-19|22800|CE | 93.25 → 90.15 | -3.32 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:42:49-13:45:10 | NIFTY|OPT|2026-10-19|22950|PE | 93.1 → 108.25 | +16.27 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 13:49:43-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 75.65 | -9.35 | whole session declared defective |
| 2026-10-19 | m1.5_s0.5 | 14:22:13-14:24:43 | NIFTY|OPT|2026-10-19|22800|CE | 73.3 → 62.7 | -14.46 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 12:53:06-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 104.9 → 101.85 | -2.91 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 12:53:40-12:54:10 | NIFTY|OPT|2026-10-19|22850|CE | 93.15 → 86.85 | -6.76 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 12:54:22-12:56:02 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 112.3 | -0.04 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 13:05:30-13:07:15 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.9 | -2.43 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 13:12:55-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 81.55 → 80.0 | -1.90 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 13:17:10-13:17:43 | NIFTY|OPT|2026-10-19|22950|PE | 76.5 → 73.0 | -4.58 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 13:17:57-13:20:56 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 84.1 | +3.70 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 13:25:03-13:25:57 | NIFTY|OPT|2026-10-19|22900|PE | 75.05 → 64.5 | -14.06 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 13:27:19-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 64.65 | -10.95 | whole session declared defective |
| 2026-10-19 | m1.5_s0.6 | 13:42:11-13:43:56 | NIFTY|OPT|2026-10-19|22800|CE | 98.8 → 84.05 | -14.93 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 09:37:09-09:37:16 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 09:44:07-09:47:13 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 11:00:26-11:00:40 | NIFTY|OPT|2026-10-19|23250|PE | 206.85 → 200.9 | -2.88 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 11:16:27-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 12:28:32-12:42:44 | NIFTY|OPT|2026-10-19|23350|PE | 421.85 → 429.1 | +1.72 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 12:52:54-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 100.9 → 101.95 | +1.04 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 12:53:41-12:53:57 | NIFTY|OPT|2026-10-19|22850|CE | 92.25 → 90.8 | -1.57 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 12:54:22-12:54:42 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 110.35 | -1.78 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 12:57:45-13:04:33 | NIFTY|OPT|2026-10-19|22850|CE | 77.05 → 104.95 | +36.21 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:04:37-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.1 → 199.5 | +2.25 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 202.7 → 198.6 | -2.02 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:12:54-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 82.2 → 80.0 | -2.68 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:15:04-13:17:32 | NIFTY|OPT|2026-10-19|23000|PE | 108.55 → 111.8 | +2.99 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:17:44-13:17:52 | NIFTY|OPT|2026-10-19|22850|CE | 78.3 → 72.55 | -7.34 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:17:57-13:20:43 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 87.8 | +8.26 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:20:43-13:22:56 | NIFTY|OPT|2026-10-19|22800|CE | 98.65 → 91.5 | -7.25 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:24:22-13:24:59 | NIFTY|OPT|2026-10-19|22800|CE | 85.35 → 76.65 | -10.19 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:25:02-13:25:51 | NIFTY|OPT|2026-10-19|22900|PE | 75.25 → 67.8 | -9.90 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:25:57-13:27:18 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 79.0 | -7.28 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:27:19-13:28:13 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 67.55 | -6.96 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:28:14-13:28:52 | NIFTY|OPT|2026-10-19|22800|CE | 82.9 → 77.8 | -6.15 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:41:27-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 94.6 → 94.45 | -0.16 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:42:43-13:42:49 | NIFTY|OPT|2026-10-19|22800|CE | 97.65 → 90.15 | -7.68 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:42:49-13:45:07 | NIFTY|OPT|2026-10-19|22950|PE | 93.1 → 106.4 | +14.29 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 13:49:43-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 75.65 | -9.35 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 14:10:33-14:12:54 | NIFTY|OPT|2026-10-19|22800|CE | 90.4 → 81.1 | -10.29 | whole session declared defective |
| 2026-10-19 | m2.0_s0.4 | 14:22:13-14:24:41 | NIFTY|OPT|2026-10-19|22800|CE | 73.3 → 63.0 | -14.05 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 09:44:11-09:44:34 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 12:53:10-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 105.3 → 101.95 | -3.18 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 12:53:41-12:54:10 | NIFTY|OPT|2026-10-19|22850|CE | 92.25 → 86.85 | -5.85 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 12:54:22-12:54:42 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 110.35 | -1.78 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.6 | -2.58 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:12:54-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 81.55 → 80.0 | -1.90 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:17:10-13:17:43 | NIFTY|OPT|2026-10-19|22950|PE | 75.15 → 73.0 | -2.86 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:17:44-13:17:52 | NIFTY|OPT|2026-10-19|22850|CE | 78.3 → 72.55 | -7.34 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:17:57-13:20:47 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 88.3 | +8.88 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:20:47-13:22:56 | NIFTY|OPT|2026-10-19|22800|CE | 98.7 → 91.5 | -7.29 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:25:02-13:25:57 | NIFTY|OPT|2026-10-19|22900|PE | 75.25 → 64.5 | -14.29 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:25:57-13:27:18 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 79.0 | -7.28 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:27:19-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 64.65 | -10.95 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:42:11-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 98.8 → 93.15 | -5.72 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:42:44-13:42:49 | NIFTY|OPT|2026-10-19|22800|CE | 93.25 → 90.15 | -3.32 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:42:49-13:45:10 | NIFTY|OPT|2026-10-19|22950|PE | 93.1 → 108.25 | +16.27 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 13:49:43-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 75.65 | -9.35 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5 | 14:22:13-14:24:43 | NIFTY|OPT|2026-10-19|22800|CE | 73.3 → 62.7 | -14.46 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 09:44:11-09:44:31 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 12:53:10-12:53:30 | NIFTY|OPT|2026-10-19|23000|PE | 105.3 → 104.25 | -1.00 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 12:53:41-12:54:03 | NIFTY|OPT|2026-10-19|22850|CE | 92.25 → 89.05 | -3.47 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 12:54:22-12:54:42 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 110.35 | -1.78 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.6 | -2.58 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:12:54-13:13:17 | NIFTY|OPT|2026-10-19|22850|CE | 81.55 → 85.3 | +4.60 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:17:10-13:17:34 | NIFTY|OPT|2026-10-19|22950|PE | 75.15 → 74.55 | -0.80 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:17:44-13:17:52 | NIFTY|OPT|2026-10-19|22850|CE | 78.3 → 72.55 | -7.34 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:17:57-13:20:47 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 88.3 | +8.88 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:20:47-13:21:17 | NIFTY|OPT|2026-10-19|22800|CE | 98.7 → 101.7 | +3.04 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:25:02-13:25:22 | NIFTY|OPT|2026-10-19|22900|PE | 75.25 → 70.2 | -6.71 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:25:57-13:26:40 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 87.45 | +2.64 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:27:19-13:27:42 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 71.5 | -1.51 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:42:11-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 98.8 → 93.15 | -5.72 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:42:44-13:42:49 | NIFTY|OPT|2026-10-19|22800|CE | 93.25 → 90.15 | -3.32 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:42:49-13:43:10 | NIFTY|OPT|2026-10-19|22950|PE | 93.1 → 97.05 | +4.24 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 13:49:43-13:50:22 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 77.15 | -7.55 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_bookexit | 14:22:13-14:22:33 | NIFTY|OPT|2026-10-19|22800|CE | 73.3 → 69.45 | -5.25 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 09:44:11-09:44:34 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 12:53:10-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 105.3 → 101.95 | -3.18 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 12:53:41-12:54:10 | NIFTY|OPT|2026-10-19|22850|CE | 92.25 → 86.85 | -5.85 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 12:54:22-12:54:42 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 110.35 | -1.78 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.6 | -2.58 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:12:54-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 81.55 → 80.0 | -1.90 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:17:10-13:17:43 | NIFTY|OPT|2026-10-19|22950|PE | 75.15 → 73.0 | -2.86 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:17:44-13:17:52 | NIFTY|OPT|2026-10-19|22850|CE | 78.3 → 72.55 | -7.34 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:17:57-13:20:47 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 88.3 | +8.88 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:20:47-13:22:56 | NIFTY|OPT|2026-10-19|22800|CE | 98.7 → 91.5 | -7.29 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:25:02-13:25:57 | NIFTY|OPT|2026-10-19|22900|PE | 75.25 → 64.5 | -14.29 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:25:57-13:27:18 | NIFTY|OPT|2026-10-19|22800|CE | 85.2 → 79.0 | -7.28 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:27:19-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 64.65 | -10.95 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:42:11-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 98.8 → 93.15 | -5.72 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:42:44-13:42:49 | NIFTY|OPT|2026-10-19|22800|CE | 93.25 → 90.15 | -3.32 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:42:49-13:45:10 | NIFTY|OPT|2026-10-19|22950|PE | 93.1 → 108.25 | +16.27 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 13:49:43-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 75.65 | -9.35 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_ivinterp | 14:22:13-14:24:43 | NIFTY|OPT|2026-10-19|22800|CE | 73.3 → 62.7 | -14.46 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 12:53:10-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 105.3 → 101.95 | -3.18 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 12:53:41-12:54:10 | NIFTY|OPT|2026-10-19|22850|CE | 92.25 → 86.85 | -5.85 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 12:54:22-12:54:42 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 110.35 | -1.78 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 12:57:49-12:58:50 | NIFTY|OPT|2026-10-19|22850|CE | 77.8 → 80.3 | +3.21 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:02:37-13:04:33 | NIFTY|OPT|2026-10-27|22900|CE | 195.7 → 206.25 | +5.39 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:04:37-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.1 → 199.5 | +2.25 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:05:29-13:06:19 | NIFTY|OPT|2026-10-27|23000|PE | 202.7 → 208.4 | +2.81 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:06:44-13:07:36 | NIFTY|OPT|2026-10-27|22900|CE | 200.0 → 204.3 | +2.15 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:07:41-13:08:05 | NIFTY|OPT|2026-10-27|23000|PE | 203.2 → 200.9 | -1.13 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:12:54-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 81.55 → 80.0 | -1.90 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:17:10-13:17:43 | NIFTY|OPT|2026-10-19|22950|PE | 75.15 → 73.0 | -2.86 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:17:44-13:17:52 | NIFTY|OPT|2026-10-19|22850|CE | 78.3 → 72.55 | -7.34 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:17:57-13:20:47 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 88.3 | +8.88 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:20:47-13:22:20 | NIFTY|OPT|2026-10-19|22800|CE | 98.7 → 98.4 | -0.30 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:22:29-13:24:17 | NIFTY|OPT|2026-10-19|22950|PE | 89.45 → 99.1 | +10.79 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:24:18-13:24:56 | NIFTY|OPT|2026-10-19|22800|CE | 87.05 → 78.65 | -9.65 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:25:00-13:25:15 | NIFTY|OPT|2026-10-19|22900|PE | 74.5 → 68.85 | -7.58 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:25:16-13:27:09 | NIFTY|OPT|2026-10-19|22800|CE | 81.55 → 83.85 | +2.82 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:27:19-13:28:13 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 67.55 | -6.96 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:28:14-13:28:45 | NIFTY|OPT|2026-10-19|22800|CE | 82.9 → 78.55 | -5.25 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:32:02-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 73.25 → 64.65 | -11.74 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:35:18-13:35:55 | NIFTY|OPT|2026-10-19|22800|CE | 87.25 → 80.75 | -7.45 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:36:27-13:37:13 | NIFTY|OPT|2026-10-19|22800|CE | 91.15 → 87.6 | -3.90 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:37:13-13:37:46 | NIFTY|OPT|2026-10-19|22950|PE | 98.85 → 96.6 | -2.28 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:37:47-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 90.1 → 93.15 | +3.38 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:42:38-13:42:49 | NIFTY|OPT|2026-10-19|22800|CE | 96.05 → 90.15 | -6.14 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:42:49-13:45:06 | NIFTY|OPT|2026-10-19|22950|PE | 93.1 → 106.9 | +14.82 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 13:49:43-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 75.65 | -9.35 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 14:10:32-14:12:54 | NIFTY|OPT|2026-10-19|22800|CE | 90.4 → 81.1 | -10.29 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 14:16:17-14:17:55 | NIFTY|OPT|2026-10-19|22800|CE | 77.8 → 71.85 | -7.65 | whole session declared defective |
| 2026-10-19 | m2.0_s0.5_novol | 14:22:07-14:24:03 | NIFTY|OPT|2026-10-19|22800|CE | 71.55 → 62.8 | -12.23 | whole session declared defective |
| 2026-10-19 | m2.0_s0.6 | 12:54:22-12:56:02 | NIFTY|OPT|2026-10-19|23000|PE | 112.35 → 112.3 | -0.04 | whole session declared defective |
| 2026-10-19 | m2.0_s0.6 | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | m2.0_s0.6 | 13:05:30-13:07:15 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.9 | -2.43 | whole session declared defective |
| 2026-10-19 | m2.0_s0.6 | 13:12:55-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 81.55 → 80.0 | -1.90 | whole session declared defective |
| 2026-10-19 | m2.0_s0.6 | 13:17:10-13:17:43 | NIFTY|OPT|2026-10-19|22950|PE | 75.15 → 73.0 | -2.86 | whole session declared defective |
| 2026-10-19 | m2.0_s0.6 | 13:17:57-13:20:56 | NIFTY|OPT|2026-10-19|22950|PE | 81.1 → 84.1 | +3.70 | whole session declared defective |
| 2026-10-19 | m2.0_s0.6 | 13:25:03-13:25:57 | NIFTY|OPT|2026-10-19|22900|PE | 75.05 → 64.5 | -14.06 | whole session declared defective |
| 2026-10-19 | m2.0_s0.6 | 13:27:19-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 64.65 | -10.95 | whole session declared defective |
| 2026-10-19 | m2.0_s0.6 | 13:42:11-13:43:56 | NIFTY|OPT|2026-10-19|22800|CE | 98.8 → 84.05 | -14.93 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 09:37:09-09:37:16 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 09:44:10-09:44:34 | NIFTY|OPT|2026-10-19|23050|CE | 112.2 → 112.2 | +0.00 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 11:16:27-11:17:35 | NIFTY|OPT|2026-10-19|23000|CE | 144.0 → 144.0 | +0.00 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 12:52:55-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 100.0 → 101.95 | +1.95 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 12:57:45-13:04:33 | NIFTY|OPT|2026-10-19|22850|CE | 77.05 → 104.95 | +36.21 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 202.7 → 198.6 | -2.02 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:13:02-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 82.25 → 80.0 | -2.74 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:17:58-13:20:43 | NIFTY|OPT|2026-10-19|22950|PE | 80.2 → 87.8 | +9.48 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:21:25-13:21:25 | NIFTY|OPT|2026-10-19|22800|CE | 103.55 → 103.25 | -0.29 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:21:45-13:22:30 | NIFTY|OPT|2026-10-19|22800|CE | 104.6 → 96.0 | -8.22 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:24:22-13:24:59 | NIFTY|OPT|2026-10-19|22800|CE | 85.35 → 76.65 | -10.19 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:25:04-13:25:51 | NIFTY|OPT|2026-10-19|22900|PE | 74.15 → 67.8 | -8.56 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:27:19-13:28:13 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 67.55 | -6.96 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:28:14-13:28:52 | NIFTY|OPT|2026-10-19|22800|CE | 82.9 → 77.8 | -6.15 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:41:27-13:42:23 | NIFTY|OPT|2026-10-19|22800|CE | 94.6 → 94.45 | -0.16 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 13:49:43-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 75.65 | -9.35 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 14:10:33-14:12:54 | NIFTY|OPT|2026-10-19|22800|CE | 90.4 → 81.1 | -10.29 | whole session declared defective |
| 2026-10-19 | m2.5_s0.4 | 14:22:13-14:24:41 | NIFTY|OPT|2026-10-19|22800|CE | 73.3 → 63.0 | -14.05 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 12:53:10-12:53:40 | NIFTY|OPT|2026-10-19|23000|PE | 105.3 → 101.95 | -3.18 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 13:05:29-13:07:16 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.6 | -2.58 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 13:13:04-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 82.6 → 80.0 | -3.15 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 13:17:58-13:20:47 | NIFTY|OPT|2026-10-19|22950|PE | 80.2 → 88.3 | +10.10 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 13:25:04-13:25:57 | NIFTY|OPT|2026-10-19|22900|PE | 74.15 → 64.5 | -13.01 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 13:27:19-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 64.65 | -10.95 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 13:42:12-13:42:22 | NIFTY|OPT|2026-10-19|22800|CE | 98.0 → 94.9 | -3.16 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 13:42:23-13:42:31 | NIFTY|OPT|2026-10-19|22950|PE | 89.25 → 90.0 | +0.84 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 13:49:43-13:50:29 | NIFTY|OPT|2026-10-19|22800|CE | 83.45 → 75.65 | -9.35 | whole session declared defective |
| 2026-10-19 | m2.5_s0.5 | 14:22:13-14:24:43 | NIFTY|OPT|2026-10-19|22800|CE | 73.3 → 62.7 | -14.46 | whole session declared defective |
| 2026-10-19 | m2.5_s0.6 | 13:04:38-13:04:55 | NIFTY|OPT|2026-10-27|23000|PE | 195.6 → 199.5 | +1.99 | whole session declared defective |
| 2026-10-19 | m2.5_s0.6 | 13:05:30-13:07:15 | NIFTY|OPT|2026-10-27|23000|PE | 203.85 → 198.9 | -2.43 | whole session declared defective |
| 2026-10-19 | m2.5_s0.6 | 13:13:04-13:13:34 | NIFTY|OPT|2026-10-19|22850|CE | 82.6 → 80.0 | -3.15 | whole session declared defective |
| 2026-10-19 | m2.5_s0.6 | 13:17:58-13:20:56 | NIFTY|OPT|2026-10-19|22950|PE | 80.2 → 84.1 | +4.86 | whole session declared defective |
| 2026-10-19 | m2.5_s0.6 | 13:27:19-13:35:15 | NIFTY|OPT|2026-10-19|22900|PE | 72.6 → 64.65 | -10.95 | whole session declared defective |
| 2026-10-19 | m2.5_s0.6 | 13:42:12-13:42:22 | NIFTY|OPT|2026-10-19|22800|CE | 98.0 → 94.9 | -3.16 | whole session declared defective |
| 2026-10-19 | premium_momentum | 09:25:00-09:25:57 | NIFTY|OPT|2026-10-19|23150|PE | 96.1 → 122.45 | +27.42 | whole session declared defective |
| 2026-10-19 | premium_momentum | 09:42:09-09:44:04 | NIFTY|OPT|2026-10-19|23150|PE | 86.1 → 74.7 | -13.24 | whole session declared defective |
| 2026-10-19 | premium_momentum | 09:49:17-09:49:38 | NIFTY|OPT|2026-10-19|23150|PE | 77.2 → 79.3 | +2.72 | whole session declared defective |
| 2026-10-19 | premium_momentum | 09:59:10-09:59:20 | NIFTY|OPT|2026-10-19|23150|PE | 145.25 → 151.5 | +4.30 | whole session declared defective |
| 2026-10-19 | premium_momentum | 12:54:26-12:54:42 | NIFTY|OPT|2026-10-19|22900|PE | 49.4 → 46.25 | -6.38 | whole session declared defective |
| 2026-10-19 | premium_momentum | 12:56:52-12:58:01 | NIFTY|OPT|2026-10-19|22900|PE | 50.25 → 44.2 | -12.04 | whole session declared defective |
| 2026-10-19 | premium_momentum | 12:58:42-13:02:27 | NIFTY|OPT|2026-10-19|22900|PE | 48.25 → 41.1 | -14.82 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:02:27-13:04:38 | NIFTY|OPT|2026-10-19|22900|CE | 54.65 → 67.2 | +22.96 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:06:48-13:07:57 | NIFTY|OPT|2026-10-19|22900|CE | 59.3 → 60.6 | +2.19 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:08:29-13:12:54 | NIFTY|OPT|2026-10-19|22900|PE | 37.65 → 42.3 | +12.35 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:17:55-13:20:47 | NIFTY|OPT|2026-10-19|22900|PE | 48.6 → 54.5 | +12.14 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:29:15-13:31:13 | NIFTY|OPT|2026-10-19|22900|PE | 73.2 → 68.0 | -7.10 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:31:44-13:39:45 | NIFTY|OPT|2026-10-19|22900|PE | 70.15 → 59.3 | -15.47 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:40:51-13:42:22 | NIFTY|OPT|2026-10-19|22850|CE | 55.75 → 58.9 | +5.65 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:42:22-13:42:23 | NIFTY|OPT|2026-10-19|22850|CE | 58.9 → 59.15 | +0.42 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:44:20-13:45:10 | NIFTY|OPT|2026-10-19|22850|PE | 37.15 → 41.3 | +11.17 | whole session declared defective |
| 2026-10-19 | premium_momentum | 13:51:43-14:07:24 | NIFTY|OPT|2026-10-19|22850|CE | 47.65 → 55.6 | +16.68 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:09:59-14:10:32 | NIFTY|OPT|2026-10-19|22850|PE | 30.35 → 26.0 | -14.33 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:12:10-14:16:41 | NIFTY|OPT|2026-10-19|22850|PE | 30.85 → 27.95 | -9.40 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:18:00-14:19:30 | NIFTY|OPT|2026-10-19|22850|PE | 33.3 → 29.0 | -12.91 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:21:11-14:23:19 | NIFTY|OPT|2026-10-19|22850|PE | 33.45 → 31.7 | -5.23 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:24:30-14:29:54 | NIFTY|OPT|2026-10-19|22850|PE | 34.7 → 33.9 | -2.31 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:31:13-14:36:28 | NIFTY|OPT|2026-10-19|22850|CE | 34.75 → 32.2 | -7.34 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:37:54-14:43:17 | NIFTY|OPT|2026-10-19|22850|PE | 33.4 → 23.35 | -30.09 | whole session declared defective |
| 2026-10-19 | premium_momentum | 14:44:17-14:49:46 | NIFTY|OPT|2026-10-19|22850|CE | 45.15 → 33.75 | -25.25 | whole session declared defective |
| 2026-10-19 | random_entry | 09:59:10-09:59:20 | NIFTY|OPT|2026-10-19|23200|PE | 184.95 → 189.15 | +2.27 | whole session declared defective |
| 2026-10-19 | random_entry | 12:31:46-12:41:02 | NIFTY|OPT|2026-10-19|22800|CE | 310.0 → 310.0 | +0.00 | whole session declared defective |
| 2026-10-19 | random_entry | 12:49:01-12:50:03 | NIFTY|OPT|2026-10-19|22850|CE | 92.85 → 86.7 | -6.62 | whole session declared defective |
| 2026-10-19 | random_entry | 13:00:00-13:04:38 | NIFTY|OPT|2026-10-27|22900|CE | 192.85 → 205.0 | +6.30 | whole session declared defective |
| 2026-10-19 | random_entry | 14:02:48-14:07:24 | NIFTY|OPT|2026-10-19|22800|CE | 90.5 → 92.55 | +2.27 | whole session declared defective |
| 2026-10-19 | random_entry | 14:26:03-14:32:04 | NIFTY|OPT|2026-10-19|22900|PE | 71.9 → 56.45 | -21.49 | whole session declared defective |
| 2026-10-19 | straddle_spike | 09:25:00-09:25:57 | NIFTY|OPT|2026-10-19|23150|PE | 96.1 → 122.45 | +27.42 | whole session declared defective |
| 2026-10-19 | straddle_spike | 09:42:10-09:44:04 | NIFTY|OPT|2026-10-19|23150|PE | 88.05 → 74.7 | -15.16 | whole session declared defective |
| 2026-10-19 | straddle_spike | 09:49:23-09:49:38 | NIFTY|OPT|2026-10-19|23150|PE | 81.05 → 79.3 | -2.16 | whole session declared defective |
| 2026-10-19 | straddle_spike | 09:59:21-10:00:43 | NIFTY|OPT|2026-10-19|23150|PE | 147.9 → 132.35 | -10.51 | whole session declared defective |
| 2026-10-19 | straddle_spike | 13:03:29-13:04:38 | NIFTY|OPT|2026-10-19|22900|CE | 69.4 → 67.2 | -3.17 | whole session declared defective |
| 2026-10-19 | straddle_spike | 14:44:35-14:47:56 | NIFTY|OPT|2026-10-19|22850|CE | 55.25 → 36.85 | -33.30 | whole session declared defective |

Per book: RAW 20, futures_only 64, gap3_s0.4 12, gap5_s0.4 7, m1.5_s0.4 28, m1.5_s0.5 21, m1.5_s0.6 11, m2.0_s0.4 28, m2.0_s0.5 20, m2.0_s0.5_bookexit 20, m2.0_s0.5_ivinterp 20, m2.0_s0.5_novol 32, m2.0_s0.6 9, m2.5_s0.4 20, m2.5_s0.5 11, m2.5_s0.6 6, premium_momentum 25, random_entry 6, straddle_spike 6

Champion for the next session: **`spot_dual_lvl`** · gates: none · candidates: none

## Record integrity

- 1 recorded non-trading day(s) carry trades (special session, or sim/test data?): 2026-10-18

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

635 trades over 2 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 635 | 0.2 | -0.75 | 0.0539 |
| iv_atm | 635 | 15.3 | 15.2 | 0.116 |
| iv_chg5 | 634 | 0.03 | -0.03 | 0.128 |
| rv15 | 635 | 12.4 | 12.2 | 0.127 |
| iv_rv | 635 | 1.25 | 1.25 | -0.105 |
| fut_imb5 | 635 | 0.034 | 0 | -0.00816 |
| fut_tot_imb | 635 | 0.085 | -0.065 | 0.0806 |
| wall_up | 622 | 267 | 252 | 0.00321 |
| wall_dn | 622 | 122 | 135 | 0.0147 |
| pcr | 635 | 1.23 | 1.22 | 0.0696 |
| imp_rng | 599 | 123 | 110 | 0.0807 |
| imp_d | 599 | -1 | -1 | -0.0893 |
| imp_f | 599 | 0.157 | 0.335 | -0.155 |
| fut_ofi60 | 634 | 4.14 | 7.5 | -0.0689 |
| syn_dev | 635 | 0.15 | 0.265 | -0.0208 |
| fut_micro | 634 | 0 | 0 | -0.0287 |
| imp_with | 599 | 1 | 1 | 0.128 |
| wall_room | 622 | 168 | 190 | -0.028 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
