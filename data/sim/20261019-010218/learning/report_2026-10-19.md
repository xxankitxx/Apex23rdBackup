# ApexOptions — learning report (2026-10-19)

Unit: return on premium per trade, % (all-in sizing). Day = log growth of the compounded trades, 100·Σln(1+r).

## Scoreboard — champion `m2.0_s0.5`
17 trades since 2026-10-17, Σ +468.9 %. GO line 1019.4, KILL line -539.7 → **COLLECTING**. Observed sd 25.8 % vs assumed 30 %.

### Observers (report only — they change no decision; owner items O-8 / O-9)

- Champion #1 since registration (2026-10-17); evening looks: 1 for this champion, 1 since registration. Every new champion and every look is another chance at a false GO.
- Wald lines with the observed sd 25.8 % (assumed 30 %): GO 760.0, KILL -393.9 → would be **COLLECTING**.
- SPRT on per-trade 100·ln(1+r): Σ +384.5 (mean +22.62/trade) vs GO 1019.4 / KILL -539.7 → would be **COLLECTING**.
- Betting e-value against "mean ≤ 0" (returns clipped to [−100, +300] %, λ mixture 0.05, 0.1, 0.2, 0.4, 0.8): **6.98** — ≥ 20 would reject at 5 % under any number of looks.

Day-level conditions for GO (§9.2; not wired into GO — owner item O-8e). Day = Σ ret% of the champion's trades since it took over; ≥ 1 trend day is not measured here:

- [ ] ≥ 15 sessions (1)
- [ ] ≥ 2 expiry days (1)
- [ ] every leave-one-day-out mean > 0
- [ ] total > 0 with the best day dropped
- [ ] no single day > 40 % of the total
- [x] ≥ 50 % of days net-green
- [ ] beats every control (0/3)

## Challengers (daily return vs champion since it took over; one-sided α 0.0038 each, 13 challengers; 2 passing evenings in a row to promote)

| variant | days | mean diff/day % | t | t needed | LODO | passing evenings |
|---|---|---|---|---|---|---|
| m1.5_s0.4 | 1 | +65.82 | 0.00 | inf | no | 0 |
| m1.5_s0.5 | 1 | +11.38 | 0.00 | inf | no | 0 |
| m1.5_s0.6 | 1 | -79.32 | 0.00 | inf | no | 0 |
| m2.0_s0.4 | 1 | +38.34 | 0.00 | inf | no | 0 |
| m2.0_s0.6 | 1 | -86.82 | 0.00 | inf | no | 0 |
| m2.5_s0.4 | 1 | +30.69 | 0.00 | inf | no | 0 |
| m2.5_s0.5 | 1 | -7.65 | 0.00 | inf | no | 0 |
| m2.5_s0.6 | 1 | -92.13 | 0.00 | inf | no | 0 |
| gap3_s0.4 | 1 | -53.98 | 0.00 | inf | no | 0 |
| gap5_s0.4 | 1 | -126.07 | 0.00 | inf | no | 0 |
| m2.0_s0.5_bookexit | 1 | +1.41 | 0.00 | inf | no | 0 |
| straddle_spike | 1 | +101.36 | 0.00 | inf | no | 0 |
| m2.0_s0.5_ivinterp | 1 | +0.00 | 0.00 | inf | no | 0 |


## Controls (current champion minus control, daily return % since registration; the champion must beat these)

| control | days | champion ahead by %/day | t | t needed | verdict |
|---|---|---|---|---|---|
| futures_only | 1 | -109.08 | 0.00 | inf | too few days |
| random_entry | 1 | +340.25 | 0.00 | inf | too few days |
| premium_momentum | 1 | -340.28 | 0.00 | inf | too few days |

## Advisors (screen: would-have vetoes on the ungated champion; decision: the gated book)

| advisor | trades | vetoed | mean all % | mean kept % | gain/trade % | top-winners vetoed | LODO | status |
|---|---|---|---|---|---|---|---|---|
| iv_late | 17 | 2 | +27.58 | +27.71 | +0.13 | 20% | no | advisory |
| room | 17 | 1 | +27.58 | +28.67 | +1.09 | 0% | no | advisory |
| coherence | 17 | 1 | +27.58 | +29.23 | +1.64 | 0% | no | advisory |
| force | 17 | 0 | +27.58 | +27.58 | +0.00 | 0% | no | advisory |
| episode | 17 | 1 | +27.58 | +28.67 | +1.09 | 0% | no | advisory |
| book | 17 | 0 | +27.58 | +27.58 | +0.00 | 0% | no | advisory |
| premium | 17 | 5 | +27.58 | +35.11 | +7.53 | 0% | no | advisory |
| quiet | 17 | 0 | +27.58 | +27.58 | +0.00 | 0% | no | advisory |
| bank | 17 | 0 | +27.58 | +27.58 | +0.00 | 0% | no | advisory |
| event | 17 | 0 | +27.58 | +27.58 | +0.00 | 0% | no | advisory |
| gamma_leg | 17 | 0 | +27.58 | +27.58 | +0.00 | 0% | no | advisory |
| gex_room | 17 | 3 | +27.58 | +27.51 | -0.07 | 20% | no | advisory |
| regime | 17 | 14 | +27.58 | +35.35 | +7.77 | 80% | no | advisory |

## Trades by regime at entry

| book | regime | trades | mean return % | win rate |
|---|---|---|---|---|
| m2.0_s0.5 | BREAKOUT | 3 | +35.35 | 100% |
| m2.0_s0.5 | COMPRESSION | 5 | +10.71 | 100% |
| m2.0_s0.5 | DIRECTIONAL | 2 | +17.78 | 100% |
| m2.0_s0.5 | RANGE | 3 | +43.85 | 100% |
| m2.0_s0.5 | UNCERTAIN | 4 | +35.55 | 100% |
| RAW | BREAKOUT | 3 | +35.35 | 100% |
| RAW | COMPRESSION | 5 | +10.71 | 100% |
| RAW | DIRECTIONAL | 2 | +17.78 | 100% |
| RAW | RANGE | 3 | +43.85 | 100% |
| RAW | UNCERTAIN | 4 | +35.55 | 100% |


## Candidates (every impulse that reached the champion's m*, taken or not)

Hit = futures reached +1R (the champion's d*) before −1R within 15 min. Option +5m = the would-be contract's return on premium 5 min later, mean.

### Overall and by decision

| group | resolved | hit rate | 95 % interval | option +5m % |
|---|---|---|---|---|
| all candidates | 112 | 60% | 51%–68% | +14.8 |
| taken | 17 | 94% | 73%–99% | +27.6 |
| rejected: already in a trade | 13 | 69% | 42%–87% | -4.5 |
| rejected: basket too thin | 68 | 54% | 43%–66% | +16.5 |
| rejected: other | 1 | 100% | 21%–100% | — |
| rejected: outside window | 13 | 31% | 13%–58% | +4.3 |

### By regime at the candidate moment

| group | resolved | hit rate | 95 % interval | option +5m % |
|---|---|---|---|---|
| BREAKOUT | 10 | 80% | 49%–94% | +6.9 |
| COMPRESSION | 16 | 69% | 44%–86% | +24.3 |
| DIRECTIONAL | 23 | 70% | 49%–84% | +11.4 |
| EXHAUSTION | 4 | 50% | 15%–85% | +15.0 |
| RANGE | 23 | 43% | 26%–63% | +15.4 |
| UNCERTAIN | 29 | 59% | 41%–74% | +15.3 |
| WARMING | 7 | 43% | 16%–75% | +11.6 |

### By impulse size (z at the crossing)

| group | resolved | hit rate | 95 % interval | option +5m % |
|---|---|---|---|---|
| z 0–2.5 | 89 | 58% | 48%–68% | +12.3 |
| z 2.5–3.5 | 22 | 64% | 43%–80% | +21.6 |
| z 3.5–∞ | 1 | 100% | 21%–100% | +76.6 |

### Does each advisor's veto separate good candidates from bad?

| advisor | vetoed: resolved | vetoed hit rate | passed: resolved | passed hit rate |
|---|---|---|---|---|
| bank | 0 | — | 112 | 60% |
| book | 19 | 68% | 93 | 58% |
| coherence | 82 | 54% | 30 | 77% |
| episode | 4 | 100% | 108 | 58% |
| event | 0 | — | 112 | 60% |
| force | 0 | — | 112 | 60% |
| gamma_leg | 11 | 55% | 101 | 60% |
| gex_room | 18 | 72% | 94 | 57% |
| iv_late | 13 | 85% | 99 | 57% |
| premium | 39 | 54% | 73 | 63% |
| quiet | 0 | — | 112 | 60% |
| regime | 98 | 59% | 14 | 64% |
| room | 2 | 50% | 110 | 60% |


Champion for the next session: **`m2.0_s0.5`** · gates: none · candidates: none
