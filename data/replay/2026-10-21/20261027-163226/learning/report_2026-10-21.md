# ApexOptions — learning report (2026-10-21)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `apex_edge`
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

## Challengers (daily return vs champion since it took over; one-sided α 0.0016 each, 32 challengers; 2 passing evenings in a row to promote)

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
| edge_gate_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_bracket_only | 0 | +0.00 | 0.00 | inf | no | 0 |
| edge_breakout | 0 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +19.35 | 0.00 | inf | too few days |
| random_entry | 1 | -1.61 | 0.00 | inf | too few days |
| premium_momentum | 1 | +21.67 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 6 | 0 | -1.01 | -1.01 | +0.00 | 0% | no | advisory |
| room | 6 | 1 | -1.01 | -0.52 | +0.49 | 0% | no | advisory |
| coherence | 6 | 5 | -1.01 | -10.04 | -9.03 | 100% | no | advisory |
| force | 6 | 0 | -1.01 | -1.01 | +0.00 | 0% | no | advisory |
| episode | 6 | 0 | -1.01 | -1.01 | +0.00 | 0% | no | advisory |
| book | 6 | 3 | -1.01 | -1.20 | -0.19 | 50% | no | advisory |
| premium | 6 | 1 | -1.01 | +0.80 | +1.81 | 0% | no | advisory |
| quiet | 6 | 0 | -1.01 | -1.01 | +0.00 | 0% | no | advisory |
| bank | 6 | 0 | -1.01 | -1.01 | +0.00 | 0% | no | advisory |
| event | 6 | 0 | -1.01 | -1.01 | +0.00 | 0% | no | advisory |
| gamma_leg | 6 | 0 | -1.01 | -1.01 | +0.00 | 0% | no | advisory |
| gex_room | 6 | 3 | -1.01 | -7.13 | -6.12 | 100% | no | advisory |
| regime | 6 | 2 | -1.01 | -1.41 | -0.40 | 50% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| apex_edge | COMPRESSION | 1 | -10.04 | 0% |
| apex_edge | DIRECTIONAL | 4 | -1.41 | 25% |
| apex_edge | WARMING | 1 | +9.61 | 100% |
| RAW | COMPRESSION | 1 | -10.04 | 0% |
| RAW | DIRECTIONAL | 4 | -1.41 | 25% |
| RAW | WARMING | 1 | +9.61 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

Entries allowed until 15:29, flatten 15:35. The heavyweights stop printing at 15:15 (auction), so synchrony is blind in this window.

| book | trades | mean ret % | win | worst / best % | TIME exits | entered in |
|---|---|---|---|---|---|---|
| fade_switch | 1 | +3.66 | 100% | +3.7 / +3.7 | 0 | CAS-ENTRY 1 |

Champion for the next session: **`apex_edge`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

336 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 335 | -1 | -0.8 | 0.0413 |
| iv_atm | 336 | 14.6 | 14.6 | 0.0271 |
| iv_chg5 | 336 | 0.015 | 0.06 | -0.255 |
| rv15 | 336 | 10.6 | 10.6 | -0.121 |
| iv_rv | 336 | 1.42 | 1.41 | 0.101 |
| fut_imb5 | 336 | -0.07 | -0.2 | 0.0718 |
| fut_tot_imb | 336 | 0.355 | 0.275 | 0.0594 |
| wall_up | 335 | 232 | 249 | -0.0706 |
| wall_dn | 335 | 195 | 226 | 0.00682 |
| pcr | 335 | 0.975 | 0.985 | -0.0181 |
| imp_rng | 335 | 120 | 131 | -0.214 |
| imp_d | 335 | -1 | -1 | -0.0886 |
| imp_f | 335 | 0.202 | 0.117 | 0.168 |
| fut_ofi60 | 336 | 2.45 | 4.13 | -0.0494 |
| syn_dev | 335 | 0.58 | -0.015 | -0.102 |
| fut_micro | 336 | -0.05 | -0.03 | 0.104 |
| v_min30 | 336 | 83.3 | 79.7 | -0.132 |
| imp_with | 335 | 1 | 1 | -0.0199 |
| wall_room | 335 | 221 | 242 | -0.081 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
