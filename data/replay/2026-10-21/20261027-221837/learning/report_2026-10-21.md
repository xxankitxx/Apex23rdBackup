# ApexOptions — learning report (2026-10-21)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `edge_gate_trail`
0 trades since 2026-10-27, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

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

## Challengers (daily return vs champion since it took over; one-sided α 0.0013 each, 39 challengers; 2 passing evenings in a row to promote)

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
| lvl_trail | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_re | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx_c10 | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_rx_be | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_be | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +93.32 | 0.00 | inf | too few days |
| random_entry | 1 | +72.36 | 0.00 | inf | too few days |
| premium_momentum | 1 | +95.64 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 5 | 0 | +16.84 | +16.84 | +0.00 | 0% | no | advisory |
| room | 5 | 1 | +16.84 | +3.77 | -13.07 | 50% | no | advisory |
| coherence | 5 | 5 | +16.84 | +0.00 | -16.84 | 100% | no | advisory |
| force | 5 | 0 | +16.84 | +16.84 | +0.00 | 0% | no | advisory |
| episode | 5 | 0 | +16.84 | +16.84 | +0.00 | 0% | no | advisory |
| book | 5 | 2 | +16.84 | +24.23 | +7.39 | 0% | no | advisory |
| premium | 5 | 0 | +16.84 | +16.84 | +0.00 | 0% | no | advisory |
| quiet | 5 | 0 | +16.84 | +16.84 | +0.00 | 0% | no | advisory |
| bank | 5 | 1 | +16.84 | +19.14 | +2.30 | 0% | no | advisory |
| event | 5 | 0 | +16.84 | +16.84 | +0.00 | 0% | no | advisory |
| gamma_leg | 5 | 0 | +16.84 | +16.84 | +0.00 | 0% | no | advisory |
| gex_room | 5 | 3 | +16.84 | -1.06 | -17.91 | 100% | no | advisory |
| regime | 5 | 1 | +16.84 | +17.72 | +0.88 | 50% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| edge_gate_trail | DIRECTIONAL | 4 | +17.72 | 75% |
| edge_gate_trail | WARMING | 1 | +13.33 | 100% |
| RAW | DIRECTIONAL | 4 | +17.72 | 75% |
| RAW | WARMING | 1 | +13.33 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| fade_switch | 1 | +3.66 | 100% | +3.7 / +3.7 | 0 | CAS-ENTRY 1 |

Champion for the next session: **`edge_gate_trail`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

367 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 366 | -0.9 | -0.6 | 0.0311 |
| iv_atm | 367 | 14.7 | 14.5 | 0.0641 |
| iv_chg5 | 367 | -0.02 | 0.07 | -0.327 |
| rv15 | 367 | 10.6 | 10.6 | -0.0897 |
| iv_rv | 367 | 1.42 | 1.4 | 0.0873 |
| fut_imb5 | 367 | -0.07 | -0.211 | 0.0762 |
| fut_tot_imb | 367 | 0.382 | 0.255 | 0.121 |
| wall_up | 366 | 232 | 255 | -0.148 |
| wall_dn | 366 | 190 | 220 | 0.0338 |
| pcr | 366 | 0.961 | 0.985 | -0.0395 |
| imp_rng | 366 | 120 | 131 | -0.208 |
| imp_d | 366 | -1 | -1 | -0.124 |
| imp_f | 366 | 0.27 | 0.146 | 0.155 |
| fut_ofi60 | 367 | -0.53 | 4.07 | -0.0677 |
| syn_dev | 366 | 0.2 | -0.29 | -0.102 |
| fut_micro | 367 | -0.05 | -0.03 | 0.117 |
| v_min30 | 367 | 83.3 | 82.2 | -0.119 |
| imp_with | 366 | 1 | 1 | 0.034 |
| wall_room | 366 | 212 | 245 | -0.132 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
