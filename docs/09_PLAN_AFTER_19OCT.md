# 09 — Plan after the first live day (19 Oct 2026)

Owner, 15:43: "This destroyed the capital. How are you planning to improve it. Prepare a plan, then code it.
Don't test it now." Day after tomorrow (Wed 21 Oct) starts fresh at ₹1,00,000; every day does. Today's
data stays on disk (ticks p1–p5, books, decision tape, candidate ledger) for replay later.

## 1. What actually lost the money (champion `m2.0_s0.5`, 20 trades, ₹1,00,000 → ₹48,146)

| Where the rupees went | ₹ | Evidence |
|---|---|---|
| **Wrong-way entries** (option moved with the futures, the futures went against us) | **−59,900** | For every afternoon trade, delta × futures move explains the option loss within ±3 pts. Spreads at entry/exit were 0.1–0.3 pts: execution was not the problem. |
| Decay, IV, basis, spread | +8,000 (net favourable) | The unexplained part of each trade is small and sums positive. |

So the system did not lose on fills or prices. It lost because **the entries were on nothing**:

1. **The impulses were noise.** At 17 of 19 afternoon entries the 15-s futures move on the bid/ask mid
   was +1 to +10 pts. The trigger (z ≥ 2) fired because the 20-min scale σ15 had shrunk to 3–5 pts in
   the lunch lull; the 0.5-pt floor on σ15 is no floor. The LTP bounce across a 4–10-pt spread
   manufactured the rest (13:49: 15-s move +17 on LTP, +11 on the mid).
2. **Counter-trend.** 9 of 9 call buys were into a −100-pt 30-min drift. All 9 lost. The 2 winners of
   the afternoon (+8.9 %, +16.3 %) were puts with the drift.
3. **The regime classifier said no 18 times out of 20** (WARMING / RANGE / UNCERTAIN / EXHAUSTION)
   and nothing listened: `regime` was an advisor, not a gate.
4. **No brake.** The book was −24 % by 13:25 and kept entering; −52 % by the close.

The genuine impulses today (≥ 15 pts on the mid, one per minute) behaved as the thesis says in the
morning — 15 reached +12 before −12, 7 the reverse — and failed after 12:00 (0 vs 3). The edge, if
there is one, is in real moves; the afternoon trades were not real moves.

## 2. The plan (what is coded below, all pre-registered, trigger numbers m*/s*/L*/d* unchanged)

| # | Change | Why | Where |
|---|---|---|---|
| D-110 | **The futures price the engine uses is the bid/ask mid** — for the 15-s impulse, σ15, the episode anchor, lateness, the guard's bad-print check, every exit and the trace. The last print is kept beside it for the record. | Removes spread bounce from the signal itself, not only from the exits. | `market.py`, `engine_main.py` |
| D-111 | **σ15 floor = 5 pts** (was 0.5): z ≥ 2 needs a ≥ 10-pt move on the mid even in a dead lunch; the owner's 15-pt floor (D-109) stays and is now measured on the mid. | Noise cannot read as z = 2. | `config.py`, `domino.py` |
| D-112 | **`regime` becomes a standing gate for every non-control book**: no entry while the regime is WARMING, UNCERTAIN, RANGE, COMPRESSION or EXHAUSTION, or DIRECTIONAL/BREAKOUT the other way. The learning loop's own gates add to it. | It vetoed 18 of today's 20 champion entries (16 losers). Honest "don't know" = no trade. | `config.BASE_GATES`, `engine_main._entry` |
| D-113 | **Daily brake, per book**: no new entries once the book is down 15 % on the day, and a 15-minute pause after 3 consecutive losses. | Today: −24 % at 13:25 and still entering. | `config.py`, `paper.evaluate_entry`, `Book` |
| D-114 | **Trend variant** `m2.0_s0.5_trend`: the champion's four numbers plus "only with the 30-min futures direction (≥ 20 pts)". Pre-registered book, not the champion. | 9/9 counter-trend calls lost; one day is not proof, so it runs beside. | `config.VARIANTS`, `paper.py` |
| D-115 | **Every trade records what the signal looked like**: r15 on the mid, σ15, z, S, 30-min trend, 5-min range, regime, σ-floor hit. | So the next review is a query, not an archaeology. | `paper.open_trade`, `engine_main` ctx |
| — | Fresh ₹1,00,000 every day: already so (`Book.capital = START_CAPITAL` at `start_day`). Today's data: untouched; `defects.json` keeps 19 Oct out of the learning decisions only. | | |

## 2b. How it is implemented (19 Oct, 16:00)

| # | Code | Notes |
|---|---|---|
| D-110 | `market.Market.push` replaces the Nifty-future row's price with the bid/ask mid (`mid_rows`, set at registry load); one-sided or > 30-pt quotes fall back to the print. Everything downstream (z, σ15, episode anchor, lateness, regime, exits, trace) reads the mid; `fut_ltp` keeps the print (header tooltip, trade `signal`). The guard's bad-print check still watches the raw print. | `FUT_PRICE_IS_MID` |
| D-111 | `domino.update`: `sigma = max(EW, SIGMA15_FLOOR)`, floor 5 pts. | `SIGMA15_FLOOR` |
| D-112 | `paper.base_gate(book, ctx, d)`: judged in the direction the book would trade (the straddle-spike leg has its own), so it works with or without a futures episode. Blocks `REGIME_BLOCK` states and DIRECTIONAL/BREAKOUT the other way. RAW and the control books are exempt (RAW is the ungated reference, controls measure chance). | `BASE_GATES`, `REGIME_BLOCK` |
| D-113 | `paper._daily_brake`: −15 % on the day stops the book for the day; 3 straight losses pause it 15 min. Controls exempt. Fresh ₹1,00,000 every trading day resets it. | `DAILY_LOSS_STOP_PCT`, `LOSS_STREAK_N`, `LOSS_STREAK_PAUSE_S` |
| D-114 | `m2.0_s0.5_trend`; `trend30` from a 1-Hz in-session futures-mid history (ready ~27 min after the open or a restart). | `TREND_MIN_PTS` |
| D-115 | `trade["signal"]` at entry; also written to `learning/days.jsonl`. New decision-tape classes: daily stop, loss pause, cool-down, regime says no, impulse too small, against trend. Dashboard verdict explains each in plain words. | — |

Checks done: unit tests `tests/test_plan19.py` (8) and all 12 existing suites pass; a simulator smoke run 09:15–13:12 had no faults and exercised every new rule. **Not done (owner): no replay of 19 Oct.**

## 3. Not done now (owner decisions / later)
- The volume test inside synchrony (`m2.0_s0.5_novol` runs beside the champion).
- The 12-pt stop vs a σ-scaled stop (observer rows exist in docs/08 §7).
- Replay of 19 Oct through this plan — **not run, by owner instruction**; `python run_apex.py replay
  data/ticks/2026-10-19.jsonl.gz` does it when wanted (parts p2–p5 follow automatically).
- Theta /375 vs /1440 (O-3), expiry-day IV cap, entries after 14:45 (D-108 says none).

## 4. Risk of this plan
Fewer trades. On a day like today's afternoon, probably zero. That is the intent: the evidence says the
afternoon entries had no edge, and the learning loop needs trades taken on real moves to say anything.
