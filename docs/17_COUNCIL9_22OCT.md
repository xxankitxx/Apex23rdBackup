# Council 9 — Thu 22 Oct: why the system lost live, and the day state (20 members, 10 teams of 2)

## What happened live
Champion `spot_dual` (pullback book on non-expiry days), 5 DTE, ₹1,00,000: 7 trades, **−₹52,084**. Two wins booked by the
18/10 lock (+6.6k, +13.9k); five losses stopped at the "impulse origin" (−7.6k … −20.9k). Nifty: 22,588 → 22,784 (11:14)
→ a 230-pt box 22,555–22,784 for the rest of the day. The rule had been chosen on 19 + 21 Oct (two down-drift days);
22 Oct was its first unseen day — the overfitting risk every external review and the earlier red teams warned about.

## Root causes (agreed across T01, T02, T03, T04, T07, T10)
* **No idea what kind of day it was.** The engine had no day-level state; its 5-min regime label called four of the
  losers DIRECTIONAL. After 11:14 the market never made a new extreme; the book kept trading the box.
* **Targets outside the day.** All 7 targets were 52–177 pts outside the day's whole range: none could be reached; every
  exit was a stop or the lock (T03, T07).
* **Levels ignored.** 5 of the 7 entries were 5–23 pts short of levels the system already had (prior-day close 22,738,
  round 22,700 / 22,600 — also OI walls — and the 22,611 shelf). All 5 losers were in profit first (+5 … +44 spot pts),
  stalled at the level, and ran back 60–90 pts to the stop (T02).
* **All-in + a structural stop** makes each wrong trade cost 13–21 % of the day.

## Every team's verdict (leave-one-day-out over 19 / 21 / 22 Oct was mandatory)
| Team | Topic | Result | Status |
|---|---|---|---|
| T01 | Day regime | No feature labels the day correctly by 10:00/11:00; a "balance" gate fixes 22 Oct in-sample but kills 19 Oct's best trade | VWAP-side idea logged |
| T02 | Levels & booking | Booking at an unbroken level: 22 Oct's live 7 trades +19.6k instead of −52.1k; costs trend days | **shadow `spot_dual_lvl`** |
| T03 | Range-day playbook | Hindsight edge-fading makes +1.34 L on 22 Oct but no causal range rule passes held-out days (one range day in three) | rejected / logged |
| T04 | Trend vs range switch | **Range mode** (100-pt leg, 61.8 % given back, off at a new extreme): 22 Oct −29k → +2.5k, 19/21 unchanged | **champion `spot_dual_rg`** |
| T05 | DeepSeek review | composite score, dispersion, ledger mining, GEX: rejected; two-tier trigger and GEX>0 only as evidence | rejected / logged |
| T06 | ChatGPT review | premium-outcome lab over 2,266 candidates; fixed +10 %/−10 % premium exit positive on every day | **shadow `spot_ft_prem10`** |
| T07 | Grok + Gemini reviews | bias object, OFI, micro-price, synthetic-forward, regime matrix: none passes; structure exit fixes 22 but breaks 21 | rejected |
| T08 | Public GitHub / ORB / CPR | ORB 45 min with booking at classic levels: +18.7k / +17.3k / +9.9k, positive on 3/3 held-out | **shadow `spot_orb45`** |
| T09 | Live vs simulation | (see its report) | — |
| T10 | Red team | no rule positive on all held-out days under both fill models; promote nothing beyond a structural gate | — |

## Engine replay of 1.9.0 (honest fills, all-in) — the numbers that count
| Book | 19 Oct | 21 Oct | 22 Oct | 3 days |
|---|---|---|---|---|
| `spot_dual` (live champion on 22 Oct) | +1,31,193 | +55,426 | −53,046 | +1,33,572 |
| `spot_dual_rg` (+ range mode) | +1,31,193 | +55,426 | −14,878 | +1,71,740 |
| **`spot_dual_lvl` (+ range mode + level booking) — champion** | **+1,36,594** | **+36,312** | **+1,199** | **+1,74,106** |
| `spot_orb45` | +18,662 | +9,828 | +16,949 | +45,438 |
| `spot_ft_prem10` | −37,690 | +1,927 | +37,086 | +1,323 |
22 Oct, champion: PE 09:30 booked at the day low (+15,288); PE 09:39 stopped (−23,868); CE 10:49 booked at the prior close
22,738.5 (+11,079); CE 11:33 booked at the prior close (−1,300 instead of −14,638); range mode then blocked the three
afternoon trades that lost −₹37.5k live. fade_switch replays at +2.04 L over three days but lost −8.2k live on 22 Oct
(T09: a 94-trade scalper's replay is not a reliable number) — not promoted.

## What was built (1.9.0)
* `apex/engine/daystate.py`: session extremes, **range mode**, opening range, prior-day high/low/close (saved each evening
  in `learning/day_levels.json`), round hundreds; warm-state persisted; `ctx["day"]`.
* Champion **`spot_dual_lvl`** = expiry day: retest breakout; other days: pullback book, which does not ENTER in range mode;
  every trade BOOKS at a level ahead it cannot break.
* Shadows: `spot_dual_rg` (range mode only), `spot_ft_prem10` (premium ±10 %), `spot_orb45` (opening-range breakout).

## Honest limits
Three days, one range day. Range mode makes a range day roughly flat, not profitable; it cannot save an entry made before
the end of the trend is known (22 Oct 11:33 CE). The shadow books are where a range-day profit could come from; they have
to prove it on days they were not built on.
