# ApexOptions — learning report (2026-10-22)

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

## Challengers (daily return vs champion since it took over; one-sided α 0.0015 each, 34 challengers; 2 passing evenings in a row to promote)

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


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +50.14 | 0.00 | inf | too few days |
| random_entry | 1 | +14.67 | 0.00 | inf | too few days |
| premium_momentum | 1 | +28.35 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 4 | 0 | +4.84 | +4.84 | +0.00 | 0% | no | advisory |
| room | 4 | 0 | +4.84 | +4.84 | +0.00 | 0% | no | advisory |
| coherence | 4 | 2 | +4.84 | +19.70 | +14.87 | 0% | no | advisory |
| force | 4 | 0 | +4.84 | +4.84 | +0.00 | 0% | no | advisory |
| episode | 4 | 0 | +4.84 | +4.84 | +0.00 | 0% | no | advisory |
| book | 4 | 2 | +4.84 | +3.07 | -1.77 | 50% | no | advisory |
| premium | 4 | 0 | +4.84 | +4.84 | +0.00 | 0% | no | advisory |
| quiet | 4 | 0 | +4.84 | +4.84 | +0.00 | 0% | no | advisory |
| bank | 4 | 1 | +4.84 | +9.82 | +4.98 | 0% | no | advisory |
| event | 4 | 0 | +4.84 | +4.84 | +0.00 | 0% | no | advisory |
| gamma_leg | 4 | 0 | +4.84 | +4.84 | +0.00 | 0% | no | advisory |
| gex_room | 4 | 0 | +4.84 | +4.84 | +0.00 | 0% | no | advisory |
| regime | 4 | 1 | +4.84 | +9.82 | +4.98 | 0% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| edge_gate_trail | DIRECTIONAL | 3 | +9.82 | 67% |
| edge_gate_trail | UNCERTAIN | 1 | -10.11 | 0% |
| RAW | DIRECTIONAL | 3 | +9.82 | 67% |
| RAW | UNCERTAIN | 1 | -10.11 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`edge_gate_trail`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

407 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 407 | 0.2 | -0.4 | 0.0535 |
| iv_atm | 407 | 14.7 | 14.6 | 0.0147 |
| iv_chg5 | 407 | 0.015 | -0.05 | 0.139 |
| rv15 | 407 | 11.3 | 11.6 | 0.0297 |
| iv_rv | 407 | 1.31 | 1.25 | -0.0321 |
| fut_imb5 | 407 | 0 | 0.056 | -0.0331 |
| fut_tot_imb | 407 | 0.081 | -0.057 | -0.0672 |
| wall_up | 407 | 320 | 284 | 0.113 |
| wall_dn | 407 | 122 | 115 | 0.0746 |
| pcr | 407 | 1.22 | 1.16 | 0.0972 |
| imp_rng | 407 | 124 | 123 | 0.0826 |
| imp_d | 407 | 1 | 1 | -0.0405 |
| imp_f | 407 | 0.28 | 0.45 | -0.179 |
| fut_ofi60 | 407 | 3.75 | 6.21 | -0.0336 |
| syn_dev | 407 | 1.02 | 0.24 | 0.0655 |
| fut_micro | 407 | 0 | 0 | -0.027 |
| v_min30 | 407 | 144 | 135 | 0.0414 |
| imp_with | 407 | 1 | 1 | 0.0196 |
| wall_room | 407 | 173 | 165 | 0.124 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
