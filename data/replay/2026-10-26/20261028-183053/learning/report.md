# ApexOptions — learning report (2026-10-26)

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
| futures_only | 1 | +11.84 | 0.00 | inf | too few days |
| random_entry | 1 | +25.15 | 0.00 | inf | too few days |
| premium_momentum | 1 | +51.58 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| room | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| coherence | 7 | 4 | +1.23 | -4.18 | -5.41 | 67% | no | advisory |
| force | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| episode | 7 | 2 | +1.23 | +5.49 | +4.27 | 0% | no | advisory |
| book | 7 | 4 | +1.23 | +7.87 | +6.64 | 33% | no | advisory |
| premium | 7 | 2 | +1.23 | +0.95 | -0.28 | 33% | no | advisory |
| quiet | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| bank | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| event | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| gamma_leg | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| gex_room | 7 | 0 | +1.23 | +1.23 | +0.00 | 0% | no | advisory |
| regime | 7 | 4 | +1.23 | -4.01 | -5.24 | 67% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| lvl_trail_re | COMPRESSION | 3 | +10.02 | 67% |
| lvl_trail_re | DIRECTIONAL | 3 | -4.01 | 33% |
| lvl_trail_re | WARMING | 1 | -9.42 | 0% |
| RAW | COMPRESSION | 3 | +10.02 | 67% |
| RAW | DIRECTIONAL | 3 | -4.01 | 33% |
| RAW | WARMING | 1 | -9.42 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| spot_dc12_t12_first | 1 | -0.85 | 0% | -0.9 / -0.9 | 1 | CAS-ENTRY 1 |

Champion for the next session: **`lvl_trail_re`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

559 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 559 | 2.97 | 1.55 | 0.197 |
| iv_atm | 559 | 23.3 | 23.6 | -0.195 |
| iv_chg5 | 559 | -0.07 | -0.08 | 0.0379 |
| rv15 | 559 | 12.5 | 13.2 | -0.179 |
| iv_rv | 559 | 1.83 | 1.77 | 0.162 |
| fut_imb5 | 559 | -0.2 | -0.059 | -0.104 |
| fut_tot_imb | 559 | -0.198 | 0.167 | -0.181 |
| wall_up | 559 | 119 | 118 | -0.0152 |
| wall_dn | 379 | 107 | 101 | 0.0278 |
| pcr | 559 | 1.3 | 1.31 | -0.116 |
| imp_rng | 559 | 88.8 | 98.7 | -0.129 |
| imp_d | 559 | 1 | -1 | 0.0891 |
| imp_f | 559 | 0.421 | 0.406 | -0.0261 |
| fut_ofi60 | 559 | 5.78 | 3.86 | 0.114 |
| syn_dev | 559 | 0.775 | -0.32 | 0.0577 |
| fut_micro | 559 | 0 | 0 | -0.0282 |
| v_min30 | 559 | 95.3 | 117 | -0.105 |
| imp_with | 559 | 1 | 1 | 0.00152 |
| wall_room | 486 | 107 | 99.5 | -0.0259 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
