# ApexOptions — learning report (2026-10-19)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `m2.0_s0.5`
0 trades since 2026-10-17, Σ +0.0 %. GO line 998.1, KILL line -560.9 → **COLLECTING**.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #1 since registration (2026-10-17); evening looks: 1 for this champion, 1 since registration. Every new champion and every look is another chance at a false GO.
- Wald lines with the observed sd: need ≥ 10 trades (have 0).
- SPRT on per-trade 100·ln(1+r): Σ +0.0 (mean +0.00/trade) vs GO 998.1 / KILL -560.9 → would be **COLLECTING**.
- Betting e-value against "mean ≤ 0" (returns clipped to [−100, +300] %, λ mixture 0.05, 0.1, 0.2, 0.4, 0.8): **1.00** — ≥ 20 would reject at 5 % under any number of looks.

Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:

- [ ] ≥ 15 sessions (1)
- [ ] ≥ 2 expiry days (1)
- [ ] every leave-one-day-out mean > 0
- [ ] total > 0 with the best day dropped
- [ ] no single day > 40 % of the total
- [ ] ≥ 50 % of days net-green
- [ ] beats every control (0/3)

## Challengers (daily return vs champion since it took over; one-sided α 0.0025 each, 20 challengers; 2 passing evenings in a row to promote)

| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |
|---|---|---|---|---|---|---|
| m1.5_s0.4 | 1 | -5.21 | 0.00 | inf | no | 0 |
| m1.5_s0.5 | 1 | +0.00 | 0.00 | inf | no | 0 |
| m1.5_s0.6 | 1 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.4 | 1 | -5.21 | 0.00 | inf | no | 0 |
| m2.0_s0.6 | 1 | +0.00 | 0.00 | inf | no | 0 |
| m2.5_s0.4 | 1 | -5.21 | 0.00 | inf | no | 0 |
| m2.5_s0.5 | 1 | +0.00 | 0.00 | inf | no | 0 |
| m2.5_s0.6 | 1 | +0.00 | 0.00 | inf | no | 0 |
| gap3_s0.4 | 1 | +0.00 | 0.00 | inf | no | 0 |
| gap5_s0.4 | 1 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_bookexit | 1 | +0.00 | 0.00 | inf | no | 0 |
| straddle_spike | 1 | +48.75 | 0.00 | inf | no | 0 |
| m2.0_s0.5_ivinterp | 1 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_novol | 1 | +18.30 | 0.00 | inf | no | 0 |
| m2.0_s0.5_trend | 1 | +0.00 | 0.00 | inf | no | 0 |
| spot_dc12_t12 | 1 | +1.55 | 0.00 | inf | no | 0 |
| spot_dc12_t12_1130 | 1 | +1.55 | 0.00 | inf | no | 0 |
| m2.0_s0.5_d20 | 1 | +0.00 | 0.00 | inf | no | 0 |
| m2.0_s0.5_tvfast | 1 | +0.00 | 0.00 | inf | no | 0 |
| fade_switch | 1 | -14.77 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | -30.59 | 0.00 | inf | too few days |
| random_entry | 1 | +0.00 | 0.00 | inf | too few days |
| premium_momentum | 1 | +4.00 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| room | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| coherence | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| force | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| episode | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| book | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| premium | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| quiet | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| bank | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| event | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| gamma_leg | 1 | 0 | -7.64 | -7.64 | +0.00 | 0% | no | advisory |
| gex_room | 1 | 1 | -7.64 | +0.00 | +7.64 | 0% | no | advisory |
| regime | 1 | 1 | -7.64 | +0.00 | +7.64 | 0% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| RAW | COMPRESSION | 1 | -7.64 | 0% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

### Overall and by decision

| group | resolved | hit rate | 95 % interval | option +5m % |
|---|---|---|---|---|
| all candidates | 12 | 58% | 32%–81% | +5.2 |
| rejected: basket too thin | 8 | 38% | 14%–69% | +12.0 |
| rejected: outside window | 4 | 100% | 51%–100% | -10.8 |

### By regime at the candidate moment

| group | resolved | hit rate | 95 % interval | option +5m % |
|---|---|---|---|---|
| COMPRESSION | 3 | 0% | 0%–56% | -9.4 |
| DIRECTIONAL | 4 | 50% | 15%–85% | +4.6 |
| UNCERTAIN | 1 | 100% | 21%–100% | +84.4 |
| WARMING | 4 | 100% | 51%–100% | -10.8 |

### By impulse size (z at the crossing)

| group | resolved | hit rate | 95 % interval | option +5m % |
|---|---|---|---|---|
| z 0–2.5 | 8 | 38% | 14%–69% | -0.7 |
| z 2.5–3.5 | 4 | 100% | 51%–100% | +18.9 |
| z 3.5–∞ | 0 | — | — | — |

### Does each advisor's veto separate good candidates from bad?

| advisor | vetoed: resolved | vetoed hit rate | passed: resolved | passed hit rate |
|---|---|---|---|---|
| bank | 1 | 0% | 11 | 64% |
| book | 5 | 40% | 7 | 71% |
| coherence | 3 | 100% | 9 | 44% |
| episode | 2 | 100% | 10 | 50% |
| event | 0 | — | 12 | 58% |
| force | 0 | — | 12 | 58% |
| gamma_leg | 0 | — | 12 | 58% |
| gex_room | 6 | 67% | 6 | 50% |
| iv_late | 4 | 50% | 8 | 62% |
| premium | 0 | — | 12 | 58% |
| quiet | 0 | — | 12 | 58% |
| regime | 9 | 56% | 3 | 67% |
| room | 0 | — | 12 | 58% |


## Closing Auction Session test (D-094) — study only, not evidence

No trade has been entered at or after 15:15 yet.

Champion for the next session: **`m2.0_s0.5`** · gates: none · candidates: none
