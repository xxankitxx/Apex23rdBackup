# Apex Conductor

*One trading system built from Apex's best strategies, each trading only in the market weather it has proven it
wins in.*

**Prepared:** 6 November 2026. **Status:** proposal for stakeholder review; nothing described here trades yet.

---

## 1. Summary

Apex runs **72 paper-trading strategies ("books") side by side**, on the same live Nifty market, every second. Each
book has its own rules and its own results. Every second, Apex also records the full state of the market — about
**68 groups of factors, roughly 150 numbers**: the index, its futures and order book, the 23 heavyweight stocks and
their order books, the option chain and its open interest, implied volatility and Greeks, and Apex's own
conclusions.

Until now these two assets have never been connected. We pick one "champion" book and let the others run in the
background. We have never asked, for each book: **in which market conditions do its trades win, and in which do they
lose?**

**Apex Conductor** connects them, in four steps:

1. **Measure every book in every weather.** For every trade of every book, record the full factor snapshot at the
   second it was taken, and whether the trade won.
2. **Find each book's favourable conditions.** Narrow each book down to the combinations of conditions in which its
   strike rate is high, written as plain yes/no rules.
3. **Conditioned books.** Each book trades only when its favourable conditions are met. We check how each would have
   done day by day.
4. **One combined system.** The conditioned books play together under a single "conductor", which:
   * holds one position at a time;
   * resolves clashes between books by fixed rules;
   * hands each moment to the book that has proven itself in that weather.

The goal is a system that **trades often, misses fewer opportunities, and wins a higher share of its trades**,
proven on market days it was never tuned on.

---

## 2. Where Apex stands today

| | Today |
|---|---|
| Instruments traded | Nifty weekly options, buy-only, ATM or in-the-money strikes (\|delta\| ≥ 0.52), paper trading |
| Capital rule | ₹1,00,000 fresh each day, all-in on every trade, no position sizing |
| Books running live | 72 (one champion, 71 shadows); 526 paper trades on 6 Nov |
| Champion | c20_9x — on the 14 recorded days (19 Oct – 6 Nov): 81 trades, **54 % strike rate**, ~6 trades a day, +₹12.1 L |
| Champion weakness | 8 trades made 79 % of its total; live record 2 winning days / 4 losing; on normal days it caught 6 of 26 big option moves |
| Frequent books | e.g. spot breakout books trade 20–40 times a day at a 37–52 % strike rate; uneven from day to day |
| Recorded data | 14 full sessions of tick data; every new session adds about 70 move starts and 15 distinct option runs |
| Research so far | Single indicators tested as yes/no filters on one book did not survive (docs/24, docs/26). *No book has ever been analysed by market condition.* |

**The insight behind Conductor.** No single factor tells, at the start of a move, whether it will run (docs/26).
But different books make money in different conditions:

* a breakout book can shine on a trend day and bleed in chop;
* the champion's expiry rules make most of its money in a few hours of expiry afternoons.

The untried question is **conditional**: *which book, in which weather?* Apex Conductor is built to answer it.

---

## 3. The idea in one picture

```
                 THE MARKET, EVERY SECOND
   index · futures book · 23 heavyweights · option chain · IV · Greeks
                            │
                            ▼
              FACTOR SNAPSHOT ENGINE  (68 groups, ~150 numbers)
                            │
        ┌──────────┬────────┼────────┬──────────┐
        ▼          ▼        ▼        ▼          ▼
     Book A     Book B   Book C   Book D  ...  Book N        ← the players (existing strategies)
   + its own  + its own + its own + its own   + its own
   favourable favourable favourable favourable favourable    ← each player's "sheet music":
   conditions conditions conditions conditions conditions      yes/no rules on the factors
        │          │        │        │          │
        └──────────┴────────┼────────┴──────────┘
                            ▼
                     THE CONDUCTOR
     one position at a time · fixed rules for clashes · switching ·
     direction-aware cool-downs · the proven book for this weather
                            │
                            ▼
              ONE TRADE STREAM  ·  all-in  ·  paper first
```

---

## 4. The plan, phase by phase

### Phase 1 — A level playing field

Books started live on different days (some 5 days old, some 14), so their records cannot be compared fairly yet.

* Replay **every book on every recorded day** through the same engine, with the same fills (≈ 1 h 40 min of compute
  per tape; three in parallel; a full 14-day pass takes about 8 hours).
* Make this a standing job: each new session's tape is replayed for all books overnight.

**Output:** one table of every trade of every book on every day.

### Phase 2 — The factor snapshot at every signal

* At the second each book signals, freeze all ~150 factor values (docs/27).
* Record the outcome: won or lost, best and worst point, minutes held, rupees.
* Also record the signals a book **could not take because it was already in a trade**, with their outcomes. A book's
  opportunities are measured separately from being busy, which is exactly the "missed opportunity" question.

**Output:** the Apex trade-and-weather dataset, growing every day.

### Phase 3 — Each book's weather fingerprint

For each book, and for each factor and each combination of two or three factors:

* strike rate, average win, average loss and trades per day **when the factor is in favour against when it is
  not**;
* stable, readable conditions, found with shallow decision trees and written as plain **yes/no rules**.
  * Example: *"spot_orb45 wins when the opening range is under 60 pts and the heavyweights are moving with it"*.
  * No scores or weights: the owner's rule.

**Output:** a weather report card for every book, showing where it wins, where it loses, and how sure we are.

### Phase 4 — Conditioned books

* Each book keeps its own entries and exits, but now **trades only when its favourable conditions are met**.
* Replay each conditioned book day by day, against its unconditioned self.

**Output:** for each book, how much a better choice of moments improves its strike rate, and what it costs in
trades.

### Phase 5 — The Conductor

The conditioned books play together as one system, under fixed rules.

**Capital and positions**

* One position at a time, all-in, buy-only, ATM/ITM.
* The book that opened a trade owns its exit rules.

**When two books fire at the same second**

* Same direction: take one trade — the book with the higher proven strike rate *in the current weather*.
* Opposite directions: no trade, unless one book's record in this weather clearly dominates the other's.

**Switching**

* Holding a losing trade while a proven book fires the other way: exit and switch.

**Cool-downs, by direction instead of one blanket 60 s**

* The opposite side is allowed at once.
* The same side after a stop needs a fresh extreme.

**Output:** Apex Conductor as a shadow book next to the champion, live, every day.

### Phase 6 — Better exits, applied across the system (in parallel)

The owner's complaints about exits are addressed here: late trailing, giving back points, holding non-working
trades.

* A trail measured in premium and scaled by the option's live delta and gamma, active from the start.
* A theta budget: a trade that has paid more decay than its delta can earn back is cut.
* A give-back cap from the peak that tightens with gamma (close to expiry).
* Tested on **all** signals in the dataset — thousands, not one book's 80 trades — so a rule that kills the big
  winners is caught before it ships.

---

## 5. How we will know it works

Every claim is judged on market days the system was **never tuned on**.

| Safeguard | What it does |
|---|---|
| Walk-forward | conditions are learned on days 1…k and scored on day k+1, then the window rolls forward |
| Leave-one-day-out | every day takes a turn as the unseen test day |
| Minimum sample | a condition needs a minimum number of trades before it counts |
| Plateau, not peak | a rule must keep most of its result when each threshold moves ±20 % |
| Luck baseline | the same search on shuffled outcomes shows how good "pure luck" looks; a finding must beat it clearly |
| Live shadow | Conductor runs live beside the champion before any promotion |

**Champion rule (owner, 6 Nov).** Champions are chosen by **strike rate**, with a considerable number of trades a
day. The guards: a positive result on unseen days, and an average loss not far larger than the average win. The
biggest total alone no longer decides.

**Goals** (targets, not promises; measured on unseen days, compared with c20_9x on the same days):

| Measure | c20_9x today | Conductor goal |
|---|---|---|
| Strike rate | 54 % | ≥ 60 % |
| Trades per day | ~6 | ≥ 8 |
| Big option moves caught on normal days (≥ +40 % available) | 23 % | ≥ 50 % |
| Losing days | 4 of 14 | fewer, with a smaller worst day |
| Result on unseen days | — | positive |

---

## 6. What stakeholders will see

* **A weather report card** for every book: its best and worst conditions, its strike rate in each, and how many
  trades back it up.
* **A live weather panel** on the dashboard:
  * today's conditions;
  * which books are "in season" right now;
  * what the Conductor would do and why.
* **A daily scoreboard:**
  * Conductor against the champion and every book;
  * strike rate, trades, average win and loss, worst trade, missed big moves.
* **Promotion only by evidence:** Conductor becomes champion only when it beats c20_9x by the champion rule on days
  it was not built on.

---

## 7. Risks and how they are handled

| Risk | Handling |
|---|---|
| **Too little history.** 14 days sliced by 150 factors produces lucky patterns. | Minimum samples, the luck baseline, walk-forward; findings are re-scored automatically as each new day arrives. The system gets stronger with every session. |
| **Hindsight weather.** "It was a trend day" is only known at the close. | Every factor is computed from data up to the signal second; nothing from later in the day. |
| **Markets change.** A book's good weather can stop working. | Rolling re-scoring; a condition whose live record turns against it is switched off automatically. |
| **All-in sizing.** Every loss is felt in full. | The Conductor trades only proven conditions; exits are improved in Phase 6. |
| **Factors that are just noise.** | Most will be (docs/26). The study keeps only what beats the luck baseline. |
| **Missing data.** No GIFT Nifty, global markets or news on the feed. | Out of scope for the first version; can be added to the feed later. |
| **Compute.** | Overnight replay jobs, so nothing competes with the live engine during market hours. |

---

## 8. Principles that do not change

* Buy-only Nifty weekly options; ATM or in-the-money strikes only.
* All-in on every trade; no position sizing.
* Yes/no rules only — no composite scores or weights.
* Paper trading; the live champion is not touched until the evidence says so.
* Every result is reported honestly, including what did not work.

---

## 9. Glossary

| Term | Meaning |
|---|---|
| Book | one complete trading strategy with its own paper capital and trades |
| Champion | the book the system currently treats as "the" trader |
| Shadow | any other book, trading on paper in the background on the same data |
| Strike rate | the share of trades that close in profit |
| Weather / conditions | the state of the market at the second a trade is signalled (docs/27) |
| Favourable conditions | yes/no rules on the factors under which a book's trades have proven to win |
| Unseen day | a market day not used to find or tune a rule; the only days that count as proof |
| Conductor | the layer that combines the conditioned books into one non-clashing trade stream |

*Reference documents:* docs/20 (champion specification), docs/23–24 (panels and model tests), docs/25 (response to
external reviews), docs/26 (event study), docs/27 (factor catalogue).
