# ApexOptions — learning report (2026-11-02)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `c20_9x`
4 trades since 2026-10-30, Σ +44.1 %. GO line 1003.1, KILL line -555.9 → **COLLECTING**. Observed sd 23.5 % vs assumed 30 %.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #2 since registration (2026-10-17); evening looks: 1 for this champion, 1 since registration. Every new champion and every look is another chance at a false GO.
- Wald lines with the observed sd: need ≥ 10 trades (have 4).
- SPRT on per-trade 100·ln(1+r): Σ +35.2 (mean +8.80/trade) vs GO 1003.1 / KILL -555.9 → would be **COLLECTING**.
- Betting e-value against "mean ≤ 0" (returns clipped to [−100, +300] %, λ mixture 0.05, 0.1, 0.2, 0.4, 0.8): **1.13** — ≥ 20 would reject at 5 % under any number of looks.

Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:

- [ ] ≥ 15 sessions (1)
- [ ] ≥ 2 expiry days (0)
- [ ] every leave-one-day-out mean > 0
- [ ] total > 0 with the best day dropped
- [ ] no single day > 40 % of the total
- [x] ≥ 50 % of days net-green
- [ ] beats every control (0/3)

## Challengers (daily return vs champion since it took over; one-sided α 0.0008 each, 63 challengers; 2 passing evenings in a row to promote)

| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |
|---|---|---|---|---|---|---|
| m1.5_s0.4 | 1 | -41.50 | 0.00 | inf | no | 0 |
| m1.5_s0.5 | 1 | -36.09 | 0.00 | inf | no | 0 |
| m1.5_s0.6 | 1 | -37.32 | 0.00 | inf | no | 0 |
| m2.0_s0.4 | 1 | -41.50 | 0.00 | inf | no | 0 |
| m2.0_s0.5 | 1 | -36.09 | 0.00 | inf | no | 0 |
| m2.0_s0.6 | 1 | -37.32 | 0.00 | inf | no | 0 |
| m2.5_s0.4 | 1 | -41.50 | 0.00 | inf | no | 0 |
| m2.5_s0.5 | 1 | -36.09 | 0.00 | inf | no | 0 |
| m2.5_s0.6 | 1 | -37.32 | 0.00 | inf | no | 0 |
| gap3_s0.4 | 1 | -37.32 | 0.00 | inf | no | 0 |
| gap5_s0.4 | 1 | -37.32 | 0.00 | inf | no | 0 |
| m2.0_s0.5_bookexit | 1 | -35.74 | 0.00 | inf | no | 0 |
| straddle_spike | 1 | -38.88 | 0.00 | inf | no | 0 |
| m2.0_s0.5_ivinterp | 1 | -36.09 | 0.00 | inf | no | 0 |
| m2.0_s0.5_novol | 1 | -41.50 | 0.00 | inf | no | 0 |
| m2.0_s0.5_trend | 1 | -36.09 | 0.00 | inf | no | 0 |
| spot_dc12_t12 | 1 | -59.29 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first | 1 | -39.86 | 0.00 | inf | no | 0 |
| spot_dc12_t12_1130 | 1 | -59.29 | 0.00 | inf | no | 0 |
| spot_dc12_t12_nolock | 1 | -59.29 | 0.00 | inf | no | 0 |
| spot_pb45 | 1 | -45.23 | 0.00 | inf | no | 0 |
| spot_dual | 1 | -45.23 | 0.00 | inf | no | 0 |
| spot_dual_rg | 1 | -45.23 | 0.00 | inf | no | 0 |
| spot_dual_lvl | 1 | -52.70 | 0.00 | inf | no | 0 |
| spot_ft_prem10 | 1 | -65.79 | 0.00 | inf | no | 0 |
| spot_orb45 | 1 | -114.10 | 0.00 | inf | no | 0 |
| m2.0_s0.5_d20 | 1 | -37.56 | 0.00 | inf | no | 0 |
| m2.0_s0.5_tvfast | 1 | -36.09 | 0.00 | inf | no | 0 |
| fade_switch | 1 | -16.62 | 0.00 | inf | no | 0 |
| apex_edge | 1 | +1.13 | 0.00 | inf | no | 0 |
| edge_gate_only | 1 | -5.43 | 0.00 | inf | no | 0 |
| edge_bracket_only | 1 | -1.59 | 0.00 | inf | no | 0 |
| edge_breakout | 1 | -56.56 | 0.00 | inf | no | 0 |
| edge_gate_trail | 1 | -9.49 | 0.00 | inf | no | 0 |
| lvl_trail | 1 | -22.89 | 0.00 | inf | no | 0 |
| lvl_trail_re | 1 | -12.59 | 0.00 | inf | no | 0 |
| lvl_trail_rx | 1 | -12.59 | 0.00 | inf | no | 0 |
| lvl_trail_rx_c10 | 1 | -12.59 | 0.00 | inf | no | 0 |
| lvl_trail_rx_be | 1 | -12.59 | 0.00 | inf | no | 0 |
| lvl_trail_be | 1 | -22.89 | 0.00 | inf | no | 0 |
| t28_d46 | 1 | -19.26 | 0.00 | inf | no | 0 |
| t28_gap | 1 | -12.59 | 0.00 | inf | no | 0 |
| t28_dur20 | 1 | -27.62 | 0.00 | inf | no | 0 |
| t28_ts | 1 | -12.59 | 0.00 | inf | no | 0 |
| t28_fill | 1 | -48.83 | 0.00 | inf | no | 0 |
| t28_core | 1 | -41.19 | 0.00 | inf | no | 0 |
| t28_core_fill | 1 | -61.60 | 0.00 | inf | no | 0 |
| t28_all | 1 | -61.60 | 0.00 | inf | no | 0 |
| t28_d46_fill | 1 | -26.57 | 0.00 | inf | no | 0 |
| t28_gap_ts | 1 | -12.59 | 0.00 | inf | no | 0 |
| t28_ivfall | 1 | -9.49 | 0.00 | inf | no | 0 |
| t28_bidpile | 1 | -12.59 | 0.00 | inf | no | 0 |
| t28_st20 | 1 | -12.59 | 0.00 | inf | no | 0 |
| t28_nohigh | 1 | -12.59 | 0.00 | inf | no | 0 |
| t28_req | 1 | -12.59 | 0.00 | inf | no | 0 |
| t28_cheap | 1 | -12.59 | 0.00 | inf | no | 0 |
| t28_cheapK | 1 | -12.59 | 0.00 | inf | no | 0 |
| t28_fwd | 1 | -35.59 | 0.00 | inf | no | 0 |
| t28_mh15 | 1 | -7.51 | 0.00 | inf | no | 0 |
| t28_tt8 | 1 | -12.41 | 0.00 | inf | no | 0 |
| c20_8x | 1 | -12.12 | 0.00 | inf | no | 0 |
| c20_9t | 1 | -40.58 | 0.00 | inf | no | 0 |
| c20_9v | 1 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +32.28 | 0.00 | inf | too few days |
| random_entry | 1 | +52.75 | 0.00 | inf | too few days |
| premium_momentum | 1 | +66.08 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 4 | 0 | +11.03 | +11.03 | +0.00 | 0% | no | advisory |
| room | 4 | 2 | +11.03 | +8.85 | -2.18 | 50% | no | advisory |
| coherence | 4 | 3 | +11.03 | +0.80 | -10.23 | 100% | no | advisory |
| force | 4 | 0 | +11.03 | +11.03 | +0.00 | 0% | no | advisory |
| episode | 4 | 0 | +11.03 | +11.03 | +0.00 | 0% | no | advisory |
| book | 4 | 2 | +11.03 | -6.71 | -17.74 | 100% | no | advisory |
| premium | 4 | 1 | +11.03 | +19.45 | +8.42 | 0% | no | advisory |
| quiet | 4 | 0 | +11.03 | +11.03 | +0.00 | 0% | no | advisory |
| bank | 4 | 1 | +11.03 | +9.08 | -1.95 | 50% | no | advisory |
| event | 4 | 0 | +11.03 | +11.03 | +0.00 | 0% | no | advisory |
| gamma_leg | 4 | 0 | +11.03 | +11.03 | +0.00 | 0% | no | advisory |
| gex_room | 4 | 2 | +11.03 | +13.22 | +2.18 | 50% | no | advisory |
| regime | 4 | 3 | +11.03 | +0.80 | -10.23 | 100% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| c20_9x | BREAKOUT | 1 | +0.80 | 100% |
| c20_9x | RANGE | 1 | +40.66 | 100% |
| c20_9x | UNCERTAIN | 1 | -14.22 | 0% |
| c20_9x | WARMING | 1 | +16.90 | 100% |
| RAW | BREAKOUT | 1 | +0.80 | 100% |
| RAW | RANGE | 1 | +40.66 | 100% |
| RAW | UNCERTAIN | 1 | -14.22 | 0% |
| RAW | WARMING | 1 | +16.90 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`c20_9x`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

459 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 459 | 4.8 | 2.9 | 0.193 |
| iv_atm | 459 | 17.4 | 17.1 | 0.206 |
| iv_chg5 | 459 | -0.1 | 0 | -0.232 |
| rv15 | 459 | 10.4 | 10.3 | 0.299 |
| iv_rv | 459 | 1.67 | 1.67 | -0.275 |
| fut_imb5 | 459 | -0.128 | -0.2 | -0.0289 |
| fut_tot_imb | 459 | -0.02 | 0.054 | -0.278 |
| wall_up | 450 | 55.2 | 458 | -0.326 |
| wall_dn | 459 | 98.5 | 42.2 | 0.33 |
| pcr | 459 | 0.716 | 0.877 | -0.242 |
| imp_rng | 459 | 77.3 | 71.5 | 0.184 |
| imp_d | 459 | -1 | 1 | -0.225 |
| imp_f | 459 | 0.499 | 0.21 | 0.124 |
| fut_ofi60 | 459 | 2.97 | 2.08 | -0.00458 |
| syn_dev | 459 | -0.51 | 0.85 | -0.223 |
| fut_micro | 459 | 0 | -0.24 | 0.283 |
| v_min30 | 459 | 43.3 | 35.8 | 0.245 |
| imp_with | 459 | 1 | 1 | 0.0926 |
| wall_room | 451 | 63.2 | 238 | -0.262 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
