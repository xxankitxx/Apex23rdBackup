# ApexOptions — learning report (2026-10-21)

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
| futures_only | 1 | +89.51 | 0.00 | inf | too few days |
| random_entry | 1 | +68.55 | 0.00 | inf | too few days |
| premium_momentum | 1 | +91.82 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 4 | 0 | +20.08 | +20.08 | +0.00 | 0% | no | advisory |
| room | 4 | 1 | +20.08 | +3.73 | -16.35 | 50% | no | advisory |
| coherence | 4 | 4 | +20.08 | +0.00 | -20.08 | 100% | no | advisory |
| force | 4 | 0 | +20.08 | +20.08 | +0.00 | 0% | no | advisory |
| episode | 4 | 0 | +20.08 | +20.08 | +0.00 | 0% | no | advisory |
| book | 4 | 1 | +20.08 | +24.23 | +4.15 | 0% | no | advisory |
| premium | 4 | 0 | +20.08 | +20.08 | +0.00 | 0% | no | advisory |
| quiet | 4 | 0 | +20.08 | +20.08 | +0.00 | 0% | no | advisory |
| bank | 4 | 1 | +20.08 | +24.23 | +4.15 | 0% | no | advisory |
| event | 4 | 0 | +20.08 | +20.08 | +0.00 | 0% | no | advisory |
| gamma_leg | 4 | 0 | +20.08 | +20.08 | +0.00 | 0% | no | advisory |
| gex_room | 4 | 2 | +20.08 | -1.06 | -21.14 | 100% | no | advisory |
| regime | 4 | 1 | +20.08 | +22.33 | +2.25 | 50% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| lvl_trail_re | DIRECTIONAL | 3 | +22.33 | 67% |
| lvl_trail_re | WARMING | 1 | +13.33 | 100% |
| RAW | DIRECTIONAL | 3 | +22.33 | 67% |
| RAW | WARMING | 1 | +13.33 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| fade_switch | 1 | +3.66 | 100% | +3.7 / +3.7 | 0 | CAS-ENTRY 1 |

Champion for the next session: **`lvl_trail_re`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

437 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 436 | -0.9 | -0.425 | 0.0309 |
| iv_atm | 437 | 14.7 | 14.5 | 0.105 |
| iv_chg5 | 437 | -0.06 | 0.08 | -0.371 |
| rv15 | 437 | 10.7 | 10.6 | -0.0748 |
| iv_rv | 437 | 1.42 | 1.38 | 0.081 |
| fut_imb5 | 437 | -0.07 | -0.222 | 0.114 |
| fut_tot_imb | 437 | 0.389 | 0.237 | 0.132 |
| wall_up | 436 | 232 | 263 | -0.231 |
| wall_dn | 436 | 185 | 191 | 0.0824 |
| pcr | 436 | 0.961 | 0.982 | -0.0781 |
| imp_rng | 436 | 121 | 132 | -0.185 |
| imp_d | 436 | -1 | -1 | -0.0544 |
| imp_f | 436 | 0.325 | 0.13 | 0.149 |
| fut_ofi60 | 437 | -3.32 | 4.07 | -0.112 |
| syn_dev | 436 | 0.2 | -0.59 | -0.0878 |
| fut_micro | 437 | -0.05 | -0.13 | 0.134 |
| v_min30 | 437 | 83.9 | 82.2 | -0.0826 |
| imp_with | 436 | 1 | 1 | 0.00235 |
| wall_room | 436 | 221 | 247 | -0.117 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
