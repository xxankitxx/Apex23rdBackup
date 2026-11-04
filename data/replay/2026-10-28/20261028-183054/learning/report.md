# ApexOptions — learning report (2026-10-28)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `lvl_trail_re`
0 trades since 2026-10-28, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

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

## Challengers (daily return vs champion since it took over; one-sided α 0.0010 each, 48 challengers; 2 passing evenings in a row to promote)

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
| spot_pb45 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dual | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dual_rg | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dual_lvl | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_ft_prem10 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_orb45 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_d20 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_tvfast | 0 | +0.00 | 0.00 | inf | no | 0 |
| fade_switch | 0 | +0.00 | 0.00 | inf | no | 0 |
| apex_edge | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_gate_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_bracket_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_breakout | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_gate_trail | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx_c10 | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx_be | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_be | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_d46 | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_gap | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_dur20 | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_ts | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_fill | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_core | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_core_fill | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_all | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_d46_fill | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | -37.54 | 0.00 | inf | too few days |
| random_entry | 1 | -28.02 | 0.00 | inf | too few days |
| premium_momentum | 1 | -9.91 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 6 | 0 | -5.56 | -5.56 | +0.00 | 0% | no | advisory |
| room | 6 | 0 | -5.56 | -5.56 | +0.00 | 0% | no | advisory |
| coherence | 6 | 5 | -5.56 | -9.16 | -3.60 | 100% | no | advisory |
| force | 6 | 2 | -5.56 | -5.81 | -0.24 | 0% | no | advisory |
| episode | 6 | 0 | -5.56 | -5.56 | +0.00 | 0% | no | advisory |
| book | 6 | 1 | -5.56 | -4.82 | +0.75 | 0% | no | advisory |
| premium | 6 | 0 | -5.56 | -5.56 | +0.00 | 0% | no | advisory |
| quiet | 6 | 0 | -5.56 | -5.56 | +0.00 | 0% | no | advisory |
| bank | 6 | 0 | -5.56 | -5.56 | +0.00 | 0% | no | advisory |
| event | 6 | 0 | -5.56 | -5.56 | +0.00 | 0% | no | advisory |
| gamma_leg | 6 | 0 | -5.56 | -5.56 | +0.00 | 0% | no | advisory |
| gex_room | 6 | 2 | -5.56 | -3.68 | +1.89 | 0% | no | advisory |
| regime | 6 | 2 | -5.56 | -3.68 | +1.89 | 0% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| lvl_trail_re | COMPRESSION | 2 | -9.27 | 0% |
| lvl_trail_re | DIRECTIONAL | 3 | -1.85 | 33% |
| lvl_trail_re | EXHAUSTION | 1 | -9.29 | 0% |
| RAW | COMPRESSION | 2 | -9.27 | 0% |
| RAW | DIRECTIONAL | 3 | -1.85 | 33% |
| RAW | EXHAUSTION | 1 | -9.29 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| spot_dc12_t12 | 3 | -0.05 | 33% | -0.3 / +0.3 | 0 | CAS-ENTRY 3 |
| spot_dc12_t12_1130 | 3 | -0.05 | 33% | -0.3 / +0.3 | 0 | CAS-ENTRY 3 |
| spot_dc12_t12_first | 4 | -0.52 | 25% | -1.1 / +0.2 | 0 | CAS-ENTRY 4 |
| spot_dc12_t12_nolock | 3 | -0.05 | 33% | -0.3 / +0.3 | 0 | CAS-ENTRY 3 |
| spot_ft_prem10 | 1 | +0.03 | 100% | +0.0 / +0.0 | 0 | CAS-ENTRY 1 |
| t28_all | 3 | +0.00 | 0% | +0.0 / +0.0 | 3 | CAS-ENTRY 3 |
| t28_core_fill | 3 | +0.00 | 0% | +0.0 / +0.0 | 3 | CAS-ENTRY 3 |
| t28_d46_fill | 3 | +0.00 | 0% | +0.0 / +0.0 | 3 | CAS-ENTRY 3 |
| t28_fill | 3 | +0.00 | 0% | +0.0 / +0.0 | 3 | CAS-ENTRY 3 |

Champion for the next session: **`lvl_trail_re`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

428 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 426 | -0.55 | -0.5 | -0.0873 |
| iv_atm | 428 | 16 | 15.8 | 0.00447 |
| iv_chg5 | 428 | -0.08 | -0.05 | -0.073 |
| rv15 | 428 | 11.8 | 11.2 | 0.146 |
| iv_rv | 428 | 1.33 | 1.46 | -0.191 |
| fut_imb5 | 428 | -0.059 | -0.077 | -0.0324 |
| fut_tot_imb | 428 | -0.072 | 0.076 | -0.336 |
| wall_up | 420 | 273 | 281 | -0.0196 |
| wall_dn | 388 | 75.7 | 56.3 | 0.0754 |
| pcr | 426 | 0.919 | 0.965 | -0.187 |
| imp_rng | 426 | 98.9 | 90.9 | -0.0362 |
| imp_d | 426 | -1 | -1 | 0.000442 |
| imp_f | 426 | 0.274 | 0.506 | -0.132 |
| fut_ofi60 | 428 | 0.43 | 2.06 | -0.0169 |
| syn_dev | 426 | -0.03 | 0.23 | -0.19 |
| fut_micro | 428 | -0.44 | 0 | -0.0316 |
| v_min30 | 428 | 82.9 | 77.9 | 0.00361 |
| imp_with | 426 | 1 | 1 | -0.111 |
| wall_room | 395 | 227 | 197 | -0.00718 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
