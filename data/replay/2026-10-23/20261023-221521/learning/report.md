# ApexOptions — learning report (2026-10-23)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `spot_dual_lvl`
5 trades since 2026-10-22, Σ +123.7 %. GO line 1004.4, KILL line -554.7 → **COLLECTING**. Observed sd 28.4 % vs assumed 30 %.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #2 since registration (2026-10-17); evening looks: 1 for this champion, 1 since registration. Every new champion and every look is another chance at a false GO.
- Wald lines with the observed sd: need ≥ 10 trades (have 5).
- SPRT on per-trade 100·ln(1+r): Σ +101.2 (mean +20.24/trade) vs GO 1004.4 / KILL -554.7 → would be **COLLECTING**.
- Betting e-value against "mean ≤ 0" (returns clipped to [−100, +300] %, λ mixture 0.05, 0.1, 0.2, 0.4, 0.8): **1.47** — ≥ 20 would reject at 5 % under any number of looks.

Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:

- [ ] ≥ 15 sessions (1)
- [ ] ≥ 2 expiry days (0)
- [ ] every leave-one-day-out mean > 0
- [ ] total > 0 with the best day dropped
- [ ] no single day > 40 % of the total
- [x] ≥ 50 % of days net-green
- [ ] beats every control (0/3)

## Challengers (daily return vs champion since it took over; one-sided α 0.0018 each, 28 challengers; 2 passing evenings in a row to promote)

| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |
|---|---|---|---|---|---|---|
| m1.5_s0.4 | 1 | -97.02 | 0.00 | inf | no | 0 |
| m1.5_s0.5 | 1 | -106.16 | 0.00 | inf | no | 0 |
| m1.5_s0.6 | 1 | -102.65 | 0.00 | inf | no | 0 |
| m2.0_s0.4 | 1 | -97.02 | 0.00 | inf | no | 0 |
| m2.0_s0.5 | 1 | -106.16 | 0.00 | inf | no | 0 |
| m2.0_s0.6 | 1 | -102.65 | 0.00 | inf | no | 0 |
| m2.5_s0.4 | 1 | -97.02 | 0.00 | inf | no | 0 |
| m2.5_s0.5 | 1 | -106.16 | 0.00 | inf | no | 0 |
| m2.5_s0.6 | 1 | -102.65 | 0.00 | inf | no | 0 |
| gap3_s0.4 | 1 | -99.13 | 0.00 | inf | no | 0 |
| gap5_s0.4 | 1 | -102.11 | 0.00 | inf | no | 0 |
| m2.0_s0.5_bookexit | 1 | -109.07 | 0.00 | inf | no | 0 |
| straddle_spike | 1 | -98.10 | 0.00 | inf | no | 0 |
| m2.0_s0.5_ivinterp | 1 | -106.16 | 0.00 | inf | no | 0 |
| m2.0_s0.5_novol | 1 | -93.75 | 0.00 | inf | no | 0 |
| m2.0_s0.5_trend | 1 | -99.13 | 0.00 | inf | no | 0 |
| spot_dc12_t12 | 1 | -65.52 | 0.00 | inf | no | 0 |
| spot_dc12_t12_first | 1 | -92.92 | 0.00 | inf | no | 0 |
| spot_dc12_t12_1130 | 1 | -65.52 | 0.00 | inf | no | 0 |
| spot_dc12_t12_nolock | 1 | -65.52 | 0.00 | inf | no | 0 |
| spot_pb45 | 1 | -45.99 | 0.00 | inf | no | 0 |
| spot_dual | 1 | -45.99 | 0.00 | inf | no | 0 |
| spot_dual_rg | 1 | -45.99 | 0.00 | inf | no | 0 |
| spot_ft_prem10 | 1 | -64.05 | 0.00 | inf | no | 0 |
| spot_orb45 | 1 | -71.16 | 0.00 | inf | no | 0 |
| m2.0_s0.5_d20 | 1 | -106.26 | 0.00 | inf | no | 0 |
| m2.0_s0.5_tvfast | 1 | -110.59 | 0.00 | inf | no | 0 |
| fade_switch | 1 | -59.38 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | +139.17 | 0.00 | inf | too few days |
| random_entry | 1 | +103.77 | 0.00 | inf | too few days |
| premium_momentum | 1 | +116.88 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 5 | 0 | +24.75 | +24.75 | +0.00 | 0% | no | advisory |
| room | 5 | 0 | +24.75 | +24.75 | +0.00 | 0% | no | advisory |
| coherence | 5 | 4 | +24.75 | +71.86 | +47.11 | 50% | no | advisory |
| force | 5 | 0 | +24.75 | +24.75 | +0.00 | 0% | no | advisory |
| episode | 5 | 1 | +24.75 | +27.28 | +2.54 | 0% | no | advisory |
| book | 5 | 3 | +24.75 | +35.98 | +11.23 | 50% | no | advisory |
| premium | 5 | 0 | +24.75 | +24.75 | +0.00 | 0% | no | advisory |
| quiet | 5 | 0 | +24.75 | +24.75 | +0.00 | 0% | no | advisory |
| bank | 5 | 1 | +24.75 | +27.28 | +2.54 | 0% | no | advisory |
| event | 5 | 0 | +24.75 | +24.75 | +0.00 | 0% | no | advisory |
| gamma_leg | 5 | 0 | +24.75 | +24.75 | +0.00 | 0% | no | advisory |
| gex_room | 5 | 0 | +24.75 | +24.75 | +0.00 | 0% | no | advisory |
| regime | 5 | 4 | +24.75 | +71.86 | +47.11 | 50% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| spot_dual_lvl | DIRECTIONAL | 2 | +39.96 | 100% |
| spot_dual_lvl | RANGE | 1 | +14.60 | 100% |
| spot_dual_lvl | UNCERTAIN | 1 | +29.11 | 100% |
| spot_dual_lvl | WARMING | 1 | +0.10 | 100% |
| RAW | DIRECTIONAL | 2 | +39.96 | 100% |
| RAW | RANGE | 1 | +14.60 | 100% |
| RAW | UNCERTAIN | 1 | +29.11 | 100% |
| RAW | WARMING | 1 | +0.10 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

No candidates recorded yet.


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`spot_dual_lvl`** · gates: none · candidates: none

## Edge features at entry (D-136: evidence only, nothing here gates a trade)

314 trades over 1 day(s), all books. Signed features: positive = with the trade.

| feature | n | winners median | losers median | Spearman vs return |
|---|---|---|---|---|
| basis_dev | 314 | -0.7 | -1.3 | 0.243 |
| iv_atm | 314 | 15.7 | 15.7 | 0.0578 |
| iv_chg5 | 313 | 0.025 | -0.01 | 0.0902 |
| rv15 | 314 | 13 | 13.3 | 0.0665 |
| iv_rv | 314 | 1.19 | 1.17 | -0.0658 |
| fut_imb5 | 314 | 0.048 | 0 | -0.0098 |
| fut_tot_imb | 314 | 0.275 | -0.227 | -0.0926 |
| wall_up | 301 | 90.7 | 103 | -0.0655 |
| wall_dn | 301 | 164 | 197 | 0.0577 |
| pcr | 314 | 1.22 | 1.23 | -0.0819 |
| imp_rng | 294 | 114 | 104 | 0.0472 |
| imp_d | 294 | -1 | -1 | 0.165 |
| imp_f | 294 | 0.083 | 0.132 | -0.057 |
| fut_ofi60 | 314 | 4.03 | 7.74 | -0.11 |
| syn_dev | 314 | 0.27 | -0.31 | 0.0575 |
| fut_micro | 314 | 0 | 0 | -0.0644 |
| imp_with | 294 | 1 | 1 | 0.239 |
| wall_room | 301 | 152 | 271 | -0.173 |

A feature earns a pre-registered gate only when its sign holds on every recorded day and on new days, including an up day (council 8 bar).
