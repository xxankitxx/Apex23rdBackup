# ApexOptions — learning report (2026-11-09)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `conductor`
0 trades since 2026-11-09, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

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

## Challengers (daily return vs champion since it took over; one-sided α 0.0006 each, 90 challengers; 2 passing evenings in a row to promote)

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
| n01_absorb | 0 | +0.00 | 0.00 | inf | no | 0 |
| n01_release | 0 | +0.00 | 0.00 | inf | no | 0 |
| n01_ctl_price | 0 | +0.00 | 0.00 | inf | no | 0 |
| n01_ctl_flow | 0 | +0.00 | 0.00 | inf | no | 0 |
| n02_relax | 0 | +0.00 | 0.00 | inf | no | 0 |
| n02_ctl_mr | 0 | +0.00 | 0.00 | inf | no | 0 |
| n06_lead | 0 | +0.00 | 0.00 | inf | no | 0 |
| n06_ctl_breadth | 0 | +0.00 | 0.00 | inf | no | 0 |
| apex_edge | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_gate_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_bracket_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_breakout | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_gate_trail | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail | 0 | +0.00 | 0.00 | inf | no | 0 |
| lvl_trail_re | 0 | +0.00 | 0.00 | inf | no | 0 |
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
| t28_gap_ts | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_ivfall | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_bidpile | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_st20 | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_nohigh | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_req | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_cheap | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_cheapK | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_fwd | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_mh15 | 0 | +0.00 | 0.00 | inf | no | 0 |
| t28_tt8 | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_8x | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9x | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9t | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9v | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9e | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9h | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9s | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9y | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_pb45_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_orb45_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.4_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| gap3_s0.4_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| fade_switch_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9x_r002 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first_r003 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_orb45_r003 | 0 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.4_r003 | 0 | +0.00 | 0.00 | inf | no | 0 |
| gap3_s0.4_r003 | 0 | +0.00 | 0.00 | inf | no | 0 |
| c20_9x_r004 | 0 | +0.00 | 0.00 | inf | no | 0 |
| spot_orb45_r005 | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +27.04 | 0.00 | inf | too few days |
| random_entry | 1 | +49.47 | 0.00 | inf | too few days |
| premium_momentum | 1 | -35.15 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 21 | 0 | +3.11 | +3.11 | +0.00 | 0% | no | advisory |
| room | 21 | 1 | +3.11 | +1.19 | -1.92 | 17% | no | advisory |
| coherence | 21 | 11 | +3.11 | +5.94 | +2.83 | 33% | no | advisory |
| force | 21 | 1 | +3.11 | +3.98 | +0.87 | 0% | no | advisory |
| episode | 21 | 0 | +3.11 | +3.11 | +0.00 | 0% | no | advisory |
| book | 21 | 7 | +3.11 | +2.32 | -0.79 | 50% | no | advisory |
| premium | 21 | 2 | +3.11 | +3.79 | +0.68 | 0% | no | advisory |
| quiet | 21 | 0 | +3.11 | +3.11 | +0.00 | 0% | no | advisory |
| bank | 21 | 1 | +3.11 | +3.53 | +0.42 | 0% | no | advisory |
| event | 21 | 0 | +3.11 | +3.11 | +0.00 | 0% | no | advisory |
| gamma_leg | 21 | 0 | +3.11 | +3.11 | +0.00 | 0% | no | advisory |
| gex_room | 21 | 8 | +3.11 | -2.88 | -5.99 | 50% | no | advisory |
| regime | 21 | 13 | +3.11 | +13.20 | +10.09 | 33% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| conductor | BREAKOUT | 1 | +61.09 | 100% |
| conductor | COMPRESSION | 5 | +0.44 | 40% |
| conductor | DIRECTIONAL | 5 | +11.22 | 80% |
| conductor | RANGE | 4 | -1.63 | 50% |
| conductor | UNCERTAIN | 6 | -8.22 | 17% |
| conductor | WARMING | 1 | +7.65 | 100% |
| RAW | BREAKOUT | 1 | +61.09 | 100% |
| RAW | COMPRESSION | 5 | +0.44 | 40% |
| RAW | DIRECTIONAL | 6 | +6.92 | 67% |
| RAW | RANGE | 3 | +3.34 | 67% |
| RAW | UNCERTAIN | 5 | -11.44 | 0% |
| RAW | WARMING | 1 | +7.65 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Record-only (config.LEARN_DECIDE = False)
The learning loop does not change books during the Conductor's forward tests. It would not have changed anything tonight.

Champion for the next session: **`conductor`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

1878 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 1878 | 2.2 | 1.3 | 0.141 |
| iv_atm | 1878 | 35.2 | 35.4 | -0.117 |
| iv_chg5 | 1878 | -0.05 | 0.17 | 0.0217 |
| rv15 | 1878 | 11.4 | 12.4 | -0.228 |
| iv_rv | 1878 | 3.03 | 2.8 | 0.157 |
| fut_imb5 | 1878 | -0.2 | -0.08 | -0.0781 |
| fut_tot_imb | 1878 | 0.131 | -0.094 | 0.226 |
| wall_up | 1749 | 80.2 | 82.2 | -0.0422 |
| wall_dn | 1653 | 142 | 400 | -0.307 |
| pcr | 1878 | 0.804 | 0.842 | -0.243 |
| imp_rng | 1878 | 110 | 124 | -0.253 |
| imp_d | 1878 | 1 | -1 | 0.0425 |
| imp_f | 1878 | 0.342 | 0.278 | -0.0692 |
| fut_ofi60 | 1878 | 6.3 | 3.91 | -0.0193 |
| syn_dev | 1878 | 0.65 | 0.42 | -0.029 |
| fut_micro | 1878 | 0 | 0 | 0.0492 |
| v_min30 | 1878 | 97.7 | 129 | -0.273 |
| imp_with | 1878 | -1 | 1 | 0.124 |
| wall_room | 1657 | 88.3 | 108 | -0.144 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
