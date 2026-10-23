# ApexOptions — learning report (2026-10-21)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `spot_pb45`
0 trades since 2026-10-21, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #2 since registration (2026-10-17); evening looks: 0 for this champion, 1 since registration. Every new champion and every look is another chance at a false GO.
- Wald lines with the observed sd: need ≥ 10 trades (have 0).
- SPRT on per-trade 100·ln(1+r): Σ +0.0 (mean +0.00/trade) vs GO 998.1 / KILL -560.9 → would be **COLLECTING**.
- Betting e-value against "mean ≤ 0" (returns clipped to [−100, +300] %, λ mixture 0.05, 0.1, 0.2, 0.4, 0.8): **1.00** — ≥ 20 would reject at 5 % under any number of looks.

Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:

- [ ] ≥ 15 sessions (0)
- [ ] ≥ 2 expiry days (0)
- [ ] every leave-one-day-out mean > 0
- [ ] total > 0 with the best day dropped
- [ ] no single day > 40 % of the total
- [ ] ≥ 50 % of days net-green
- [ ] beats every control (0/3)

## Challengers (daily return vs champion since it took over; one-sided α 0.0021 each, 24 challengers; 2 passing evenings in a row to promote)

| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |
|---|---|---|---|---|---|---|
| m1.5_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.5 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.6 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.6 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.5_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.5_s0.5 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.5_s0.6 | 0 | +0.00 | 0.00 | inf | no | 0 |
| gap3_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| gap5_s0.4 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_bookexit | 0 | +0.00 | 0.00 | inf | no | 0 |
| straddle_spike | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_ivinterp | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_novol | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_trend | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_1130 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_nolock | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dual | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_d20 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_tvfast | 0 | +0.00 | 0.00 | inf | no | 0 |
| fade_switch | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +76.39 | 0.00 | inf | too few days |
| random_entry | 1 | +55.43 | 0.00 | inf | too few days |
| premium_momentum | 1 | +78.70 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 4 | 0 | +16.93 | +16.93 | +0.00 | 0% | no | advisory |
| room | 4 | 1 | +16.93 | -0.47 | -17.40 | 50% | no | advisory |
| coherence | 4 | 4 | +16.93 | +0.00 | -16.93 | 100% | no | advisory |
| force | 4 | 0 | +16.93 | +16.93 | +0.00 | 0% | no | advisory |
| episode | 4 | 0 | +16.93 | +16.93 | +0.00 | 0% | no | advisory |
| book | 4 | 1 | +16.93 | +21.27 | +4.35 | 0% | no | advisory |
| premium | 4 | 0 | +16.93 | +16.93 | +0.00 | 0% | no | advisory |
| quiet | 4 | 0 | +16.93 | +16.93 | +0.00 | 0% | no | advisory |
| bank | 4 | 0 | +16.93 | +16.93 | +0.00 | 0% | no | advisory |
| event | 4 | 0 | +16.93 | +16.93 | +0.00 | 0% | no | advisory |
| gamma_leg | 4 | 0 | +16.93 | +16.93 | +0.00 | 0% | no | advisory |
| gex_room | 4 | 3 | +16.93 | -16.27 | -33.20 | 100% | no | advisory |
| regime | 4 | 1 | +16.93 | +18.92 | +1.99 | 50% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| spot_pb45 | DIRECTIONAL | 3 | +18.92 | 67% |
| spot_pb45 | WARMING | 1 | +10.97 | 100% |
| RAW | DIRECTIONAL | 3 | +18.92 | 67% |
| RAW | WARMING | 1 | +10.97 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| fade_switch | 1 | +3.66 | 100% | +3.7 / +3.7 | 0 | CAS-ENTRY 1 |

Champion for the next session: **`spot_pb45`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

272 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 271 | -1 | -1.07 | 0.0629 |
| iv_atm | 272 | 14.5 | 14.6 | -0.0731 |
| iv_chg5 | 272 | 0.03 | 0.08 | -0.362 |
| rv15 | 272 | 10.6 | 10.5 | -0.127 |
| iv_rv | 272 | 1.42 | 1.42 | 0.0723 |
| fut_imb5 | 272 | 0.0265 | -0.222 | 0.166 |
| fut_tot_imb | 272 | 0.318 | 0.335 | -0.0658 |
| wall_up | 271 | 232 | 249 | -0.0549 |
| wall_dn | 271 | 212 | 228 | -0.000569 |
| pcr | 271 | 0.975 | 0.988 | -0.105 |
| imp_rng | 271 | 115 | 131 | -0.308 |
| imp_d | 271 | -1 | -1 | 0.119 |
| imp_f | 271 | 0.173 | 0.086 | 0.236 |
| fut_ofi60 | 272 | 2.04 | 5.2 | -0.134 |
| syn_dev | 271 | 0.85 | 0.06 | -0.11 |
| fut_micro | 272 | -0.08 | -0.03 | 0.0674 |
| imp_with | 271 | 1 | 1 | 0.00614 |
| wall_room | 271 | 229 | 237 | -0.0442 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
