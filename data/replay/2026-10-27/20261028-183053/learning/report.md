# ApexOptions — learning report (2026-10-27)

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
| futures_only | 1 | -46.42 | 0.00 | inf | too few days |
| random_entry | 1 | +93.71 | 0.00 | inf | too few days |
| premium_momentum | 1 | -114.76 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 18 | 0 | +2.74 | +2.74 | +0.00 | 0% | no | advisory |
| room | 18 | 2 | +2.74 | +3.14 | +0.40 | 0% | no | advisory |
| coherence | 18 | 13 | +2.74 | -6.32 | -9.06 | 100% | no | advisory |
| force | 18 | 0 | +2.74 | +2.74 | +0.00 | 0% | no | advisory |
| episode | 18 | 0 | +2.74 | +2.74 | +0.00 | 0% | no | advisory |
| book | 18 | 9 | +2.74 | +1.35 | -1.39 | 50% | no | advisory |
| premium | 18 | 4 | +2.74 | +2.50 | -0.24 | 33% | no | advisory |
| quiet | 18 | 0 | +2.74 | +2.74 | +0.00 | 0% | no | advisory |
| bank | 18 | 2 | +2.74 | +2.65 | -0.09 | 17% | no | advisory |
| event | 18 | 0 | +2.74 | +2.74 | +0.00 | 0% | no | advisory |
| gamma_leg | 18 | 1 | +2.74 | +3.38 | +0.65 | 0% | no | advisory |
| gex_room | 18 | 1 | +2.74 | +3.12 | +0.38 | 0% | no | advisory |
| regime | 18 | 11 | +2.74 | -1.30 | -4.04 | 83% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| lvl_trail_re | BREAKOUT | 1 | -10.08 | 0% |
| lvl_trail_re | COMPRESSION | 7 | +1.92 | 57% |
| lvl_trail_re | DIRECTIONAL | 3 | +4.12 | 33% |
| lvl_trail_re | EXHAUSTION | 1 | -8.23 | 0% |
| lvl_trail_re | RANGE | 2 | +10.54 | 100% |
| lvl_trail_re | UNCERTAIN | 3 | +9.33 | 67% |
| lvl_trail_re | WARMING | 1 | -7.29 | 0% |
| RAW | BREAKOUT | 1 | -10.08 | 0% |
| RAW | COMPRESSION | 7 | +1.92 | 57% |
| RAW | DIRECTIONAL | 3 | +4.12 | 33% |
| RAW | EXHAUSTION | 1 | -8.23 | 0% |
| RAW | RANGE | 2 | +10.54 | 100% |
| RAW | UNCERTAIN | 3 | +9.33 | 67% |
| RAW | WARMING | 1 | -7.29 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`lvl_trail_re`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

714 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 714 | 1.5 | 1.3 | -0.022 |
| iv_atm | 714 | 31.9 | 32.1 | -0.025 |
| iv_chg5 | 714 | 0.28 | 0.17 | -0.0102 |
| rv15 | 714 | 11.1 | 9.32 | 0.123 |
| iv_rv | 714 | 2.91 | 3.13 | -0.189 |
| fut_imb5 | 714 | -0.034 | 0.04 | -0.0748 |
| fut_tot_imb | 714 | 0.031 | 0.286 | -0.0687 |
| wall_up | 688 | 66.3 | 52.5 | 0.0535 |
| wall_dn | 512 | 47.2 | 51.7 | 0.122 |
| pcr | 714 | 0.996 | 0.988 | -0.0423 |
| imp_rng | 714 | 76.7 | 88.1 | -0.109 |
| imp_d | 714 | 1 | -1 | 0.154 |
| imp_f | 714 | 0.393 | 0.256 | 0.0605 |
| fut_ofi60 | 714 | 7.68 | 2.15 | 0.188 |
| syn_dev | 714 | 0.4 | -0.71 | 0.204 |
| fut_micro | 714 | 0 | 0 | -0.0465 |
| v_min30 | 714 | 62.4 | 39.5 | 0.111 |
| imp_with | 714 | -1 | 1 | -0.165 |
| wall_room | 532 | 89.3 | 49.2 | 0.215 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
