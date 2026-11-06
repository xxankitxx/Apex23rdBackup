# Apex Conductor — official specification

*One trading system built from Apex's best strategies, each trading only in the market weather the future has
confirmed it wins in.*

**Status:** official specification, adopted 7 November 2026. It combines the owner's write-up, the review
adjustments and the stakeholder amendments of 7 Nov. **Nothing described here trades yet.**

**Supporting documents:**

* docs/27 — the factor catalogue (the "weather");
* docs/29 — the missed-signal recorder;
* docs/26 — the event study;
* docs/20 — the champion's specification.

---

## 1. The idea in plain words

Apex runs **72 paper-trading strategies ("books")** side by side on the same live Nifty market. Each fires its own
triggers during the day. Some triggers become winning trades, some losing ones. At the second each trigger fires,
Apex can record about **150 numbers describing the market**: the time of day, how far the index has moved, whether
the big stocks are moving with it, what the option chain looks like, how expensive the option is, and so on. Think
of them as a **photograph of the weather** at the moment the book pulled the trigger.

The question is simple: **for each book, what did the weather look like when it won, and when it lost?** If a book
keeps winning in one kind of weather and losing in another, it should trade only in its good weather. Once each
book's good weather is known, the books share **one pot of money**: whichever book sees its good weather first takes
the trade, and the others wait. That is the **Conductor**.

There is one thing to be careful about, and it shapes everything below: **a pattern found by looking at the past is
a guess until the future agrees with it.** So the system finds patterns in the taped days and writes them down with
a date. Then it lets new days judge them, and only patterns the future confirmed get money behind them.

```
  every trigger of every book
            │  + the weather photograph (≈150 numbers)  + what happened
            ▼
       THE DIARY  ──────────►  THE SEARCH  ──────────►  A DATED RULE
   (one line per trigger)   (what winners had in      ("trade only when …",
                             common; luck check)        frozen from today)
                                                               │
                                                               ▼
                                                     THE FORWARD TEST
                                              (new days only; restricted book vs
                                               free book; margin; two windows)
                                                               │ passed
                                                               ▼
                                                       THE CONDUCTOR
                                       (one pot, all-in; first proven book to fire takes it)
```

---

## 2. Where Apex stands today

| | Today |
|---|---|
| Instruments | Nifty weekly options, buy-only, ATM or in-the-money strikes (\|delta\| ≥ 0.52), paper trading |
| Capital rule | ₹1,00,000 fresh each day, all-in on every trade, no position sizing |
| Books running live | 72 (one champion, 71 shadows); 526 paper trades on 6 Nov |
| Champion | c20_9x — on the 14 recorded days (19 Oct – 6 Nov): 81 trades, **54 % strike rate**, ~6 trades a day, +₹12.1 L |
| Champion weakness | 8 trades made 79 % of its total; live record 2 winning days, 4 losing; on normal days it caught 6 of 26 big option moves |
| Frequent books | spot breakout books trade 20–40 times a day at a 37–52 % strike rate; uneven from day to day |
| Recorded data | 14 full sessions of tick data; every new session adds about 70 move starts and 15 distinct option runs |
| Research so far | single indicators tested as yes/no filters on one book did not survive (docs/24, docs/26); **no book has ever been analysed by market condition** |
| Built for this plan | the missed-signal recorder (docs/29), proven to leave all 72 books trade-for-trade identical |

**Champion rule (owner, 6 Nov).** A champion is chosen by **strike rate**, with a considerable number of trades a
day. The guards: a positive result on test days, and an average loss not far larger than the average win. The
biggest total alone no longer decides.

---

## 3. Step 1 — Each book's diary

For every book the system keeps a diary, one line per trigger. Each line records:

* when the trigger fired, and the direction (call or put);
* the weather photograph at that second (§9);
* what happened: rupees made or lost, minutes held, the best point in the book's favour, the worst point against
  it, and the exit reason.

Two labels are added to every line:

* **Winner or loser** — did it close in profit?
* **If a loser, what kind?**
  * **Never worked.** It went against the book almost from the start and never showed a profit. *The weather was
    wrong*; the book should not have fired here.
  * **Worked, then gave it back.** It was up a decent amount, then came back to a loss. *The entry was fine; the
    exit failed.* These go to the exit work (§8), not the weather search.

  If only "losers" were studied, the weather would be blamed for losses it had nothing to do with.

**Missed signals.** The diary also includes the triggers a book wanted to take but couldn't because it was already
in a trade, from the missed-signal recorder (docs/29), with what would have happened.

* They are flagged `is_counterfactual` and are never mistaken for real trades.
* **Both directions are used.** The recorder already folds the real trade's own repeated signal into the real trade
  (fires within 30 s), so a remaining same-direction row is a genuinely new setup. For example, c20_9x fired a fresh
  CE six minutes after its real entry on 6 Nov.
* A counterfactual trade that **overlaps the real trade in time shares its outcome**, so it counts as **at most half
  an observation**.
* **Counterfactual rows feed the search only.** They are never used to score a rule on test days (§6).

---

## 4. Step 2 — The search: what did the winners have in common?

For one book at a time, and for each weather number, the system asks a plain question: *if I draw a line somewhere
on this number, do the winners fall mostly on one side and the losers on the other?*

> Example. A breakout book fired 60 times over 14 days, winning 30. The line is breadth (the share of the 23 big
> stocks moving with the trade) at 60 %:
>
> * above the line: 25 trades, 18 winners, 72 %;
> * below the line: 35 trades, 12 winners, 34 %.
>
> If most of its *never-worked* losers had breadth below 60 %, low breadth also goes on its "hurt" list.

Every candidate condition must pass these checks:

| Check | What it means |
|---|---|
| **Enough trades on both sides** | a side with only a handful of trades is ignored |
| **Holds when the line moves** | it must still work with the line slightly lower and higher (e.g. 55 % and 65 %); a single sweet spot is luck |
| **Keeps the big wins** | a condition that raises the hit rate by excluding most of the book's largest wins is rejected; a higher hit rate with less money is not an improvement |
| **Counts days for day-type weather** | for whole-day facts (expiry or not, the opening gap, VIX), 30 wins on one trend day are one piece of evidence; at least 4–5 days are needed on each side |
| **Beats pure luck** | the same search is run on the same trades with the win/loss labels shuffled; whatever the best shuffled condition looks like is what luck looks like, and a real condition must be clearly better |

The output is each book's **weather card**: a short readable list such as "breadth above 60 % helped; low breadth
hurt; expiry afternoons helped". Every line is marked **found by searching the past**, so nobody mistakes it for
proof.

---

## 5. Step 3 — Write the rule down and date it

From the card the system proposes a rule in plain language:

> *Breakout book — from 7 November: trade only when breadth is 60 % or more.*

* **One condition to start.** Two joined by "and" only if each passed on its own. No three-condition rules: with
  this much data they are too easy to get by chance.
* **One "strong triggers only" rule per book is allowed.** The book's own trigger measurements are otherwise left
  out (§9), because searching them re-tunes the entry. But one plain strength rule, tested forward like any other,
  is a legitimate idea.
* Each rule carries:
  * the **date it was written** and the days it was learned from;
  * ideally, **a reason a trader would nod at** ("a breakout without the big stocks behind it tends to fail"). A
    rule with no sensible reason is allowed but trusted less.

---

## 6. Step 4 — Freeze the rule and let new days judge it

**From the day it is written, the rule does not change.** Not after a losing day, not after it blocks a winner.
Changing it makes a new rule with a new date and a fresh test. The point of the test is to see the rule on days it
has never seen; adjusting it after each day means it has seen every day.

### The restricted book

During the test the book runs twice on paper:

* the **free** version: the book as it is, taking every trigger;
* the **restricted** version: the book taking only the triggers that pass the rule.

The restricted version must be **registered as its own book** and run through the engine. It cannot be computed from
the diary, because blocking one trade changes the rest of the book's day: it is free earlier, takes different later
signals, and its internal state differs. The restricted book logs every trigger it blocked.

* **Restricted books run in the evening replay of each day's tape, not in the live engine.**
  * The test stays fully forward: every rule is frozen before the day it is scored on.
  * The live engine stays fast. 72 books × a few candidate rules could mean 200+ extra books, and the book loop is
    already about a quarter of each live tick.
  * Only rules that have passed their first window may also run live, and then only a capped number.
* **Start date and compute.** Restricted books start on the freeze date, not before. The evening replay of one day
  takes about 1 h 40 min for today's books, plus a share for every restricted book added. The nightly budget is
  reported with the register.

### Minimum test length

* **At least 10 new trading days and at least 20 restricted trades.**
* **Day-type rules:** at least **5 test days on each side** of the condition.
* **Realistic timing:**
  * a book at 1–2 trades a day needs 2–3 weeks for 20 trades;
  * an expiry-day rule (one expiry a week) needs at least 5 weeks.

  **The first rules pass in weeks; expiry-day rules take a month or two.**

### Pass criteria — with a margin

A rule that does nothing would beat its free version on "higher hit rate" about half the time on 20 trades. It would
beat it on "at least as many rupees" about half the time too, and the two move together. So without a margin roughly
**1 in 3 or 4** useless rules would pass. Across 72 books that is 20-odd lucky passes. The margin is what makes luck
rare.

On the test days only, the rule passes when **all** of these hold:

1. **The restricted hit rate beats the free hit rate by a margin.** The margin is calibrated for each rule by
   shuffling the win/loss labels of its own test-day trades: it must beat what shuffling produces in (say) 95 % of
   shuffles. On 20 trades a hit rate's own noise is about ±11 points, and the bar differs by book, so it is not one
   fixed number.
2. **Rupees beat the free version by a clear amount,** not merely equal.
3. **Most big wins are kept:** it blocks no more than a third of the free version's largest wins.

### Two windows

| Result | What happens |
|---|---|
| Passes the **first window** | enters the Conductor's pool at **low priority** |
| Stays ahead through a **second window** of the same length | **full standing** |
| Fails the second window | out of the pool, recorded as failed |
| Fails at any stage | recorded as failed; still useful ("breadth does not help the breakout book"), and the system will not propose it again |

### Watching rules that passed

A passed rule keeps being watched. If over the most recent 20 trading days the restricted version falls behind the
free version, the rule is switched off until it recovers. Markets change.

### The register reports its own luck

Every day the rule register prints the arithmetic: *"N rules under test; P passed; about M of those passes are
expected by luck."* M comes from the same label-shuffling. This keeps everyone honest about what the pool contains.

---

## 7. Step 5 — Placing the bets: the Conductor

**Only books with a rule that passed its test enter the pool.** A book without one keeps running as a shadow, keeps
being studied, and may join later.

* **One trade at a time, all-in, buy-only, ATM/ITM**, as today.
* **First to fire takes it; the others wait** until that trade closes.
* **Two pooled books firing in the same second:** the one whose rule has the better **test-day** hit rate takes the
  trade, never the hit rate from the days the rule was learned on. Low-priority (first-window) books yield to
  full-standing books.
* **The champion stays as it is** until a book's passed rule beats it on test days in the same part of the session.
  The champion is not replaced on a promise.
* **The Conductor's own record is honest.** It is replayed on past days using the rules *as they stood on each
  date*, never with today's knowledge.
* **Switching is a candidate rule under trial, not a default.** "Holding a losing trade while a pooled book fires the
  other way → exit and switch" is the rule most likely to whipsaw in a sideways market, so it gets a dated, frozen
  trial like everything else. It can be tested from data already being collected:
  * for every opposite-direction missed signal, the counterfactual row gives what the new trade would have made;
  * the free replay gives what the held trade went on to do from that same second;
  * **the switch's result = the new trade's P&L − the held trade's P&L from the switch second to its own exit.** The
    only costs are those of the paper fill rule itself (first traded price after each signal); slippage and
    brokerage are excluded by the owner's instruction.

  It passes only if switching beats holding on test days, **on choppy days as well as trending ones**. Until then
  the Conductor runs "first to fire takes it; the others wait".

---

## 8. The other half: exits

Losses labelled **worked, then gave it back** are an exit problem, not a weather problem. They feed the exit work,
which addresses the owner's complaints: trailing starts late, too much is given back from the peak, non-working
trades are held too long. Three candidate exit designs:

* a trail measured in premium, scaled by the option's live delta and gamma, and active from the start;
* a theta budget: a trade that has paid more decay than its delta can realistically earn back is cut;
* a give-back cap from the peak that tightens with gamma, near expiry.

They are tested on **all** triggers in the diaries (thousands, not one book's 80 trades), so a rule that kills the
big winners is caught first. Each is a dated, frozen candidate with its own forward test.

---

## 9. Which weather numbers are searched (docs/27)

**Searched**, because they have a clear reason to matter and can be measured before the trade:

* time of day and the expiry calendar;
* the shape of the day so far: trend or chop, position in the day's range, side of VWAP, the opening range;
* realised volatility;
* big-stock breadth and leadership;
* room to the nearest OI wall;
* whether the straddle is expanding;
* how expensive the option is relative to the move the index must make (breakeven against theta);
* VIX.

Start with these. If none of them survive for a book, searching combinations of the rest won't help; it would only
hide the fact that nothing is there.

**Set aside, with reasons:**

| Group | Why |
|---|---|
| The book's own trigger measurements (speed, impulse size) | this is the book's entry rule; searching it re-tunes the entry. Exception: one "strong triggers only" rule per book (§5) |
| The book's own recent history (last result, streak, agreement with other books) | the Conductor replaces these per-book habits with its own rules; missed-signal rows have no such history |
| The engine's verdicts (regime label, advisors) | computed from the other numbers; kept as labels on the reports, not searched |
| Five higher-order Greeks | on a weekly ATM option these are largely one fact (time to expiry) written five ways; one is kept |
| Model outputs (premium-race odds, hidden regime, Hawkes, gamma map) | predictions, not raw weather, each with tuned parameters; each tested alone as one yes/no idea |
| Feed health and option spread | plain safety vetoes for every book, not searched |

---

## 10. Every evening

1. **Replay** today's tape: every free book, every restricted book under test, and the Conductor.
2. **Score**: add today's result to every rule under test.
3. **Learn**: add today's triggers and photographs to every diary; rerun the search and the luck check; propose new
   rules, dated today.
4. **Decide**: pass, fail, promote (second window) or switch off rules whose windows completed.
5. **Publish**:
   * **the rule register** — every rule, its date, how it is doing on test days, its status, and the day's luck
     arithmetic;
   * **each book's weather card** — helped and hurt conditions, the numbers behind them, and whether each is still a
     guess or has passed;
   * **the loss breakdown per book** — never-worked (weather) against gave-it-back (exits).

No one adjusts rules by hand. Every session adds one more day of evidence to every rule at once.

---

## 11. Build order

| # | Stage | Status / effort |
|---|---|---|
| 1 | Missed-signal recorder | **done** (docs/29): 72/72 books identical on two tape slices; +2–4 % compute |
| 2 | Freeze: the recorder-off-vs-on check on two full tapes; run manifest | ~2 h of replays |
| 3 | Pre-flight: all books load, double replay identical, anchor check against live days | ~2 h |
| 4 | One full tape, stop for sign-off with the anchor diff and validation report | ~2 h |
| 5 | Full replay of every book on all taped days (resumable, per-tape validation) | ~8 h for 14 days |
| 6 | Weather snapshot engine: the photograph at every trigger, computed in replay and checked | to build |
| 7 | Diaries, loss labels, search with luck check, weather cards | to build |
| 8 | First dated rules; restricted books registered; evening replay loop | to build |
| 9 | Forward tests; rule register; first passes | weeks; expiry-day rules 1–2 months |
| 10 | Conductor in the evening replay, then live as a shadow; switching trial | after the first passes |
| 11 | Exit candidates (§8), forward-tested | in parallel from stage 7 |

---

## 12. A worked example

1. **7 Nov — the search.** The breakout book won 72 % with breadth above 60 % and 34 % below. On shuffled labels the
   best condition reaches 61 %. The condition survives moving the line to 55 % and 65 %, and it keeps 8 of the book's
   10 biggest wins. Rule written and frozen: *breakout book trades only when breadth ≥ 60 %.* A restricted book is
   registered.
2. **8–21 Nov — first window.** The free and restricted versions run in each evening's replay. After 10 days:
   * restricted: 24 trades, 15 winners (62 %), ₹41,000;
   * free: 58 trades, 27 winners (47 %), ₹33,000.

   The calibrated margin for this rule is 9 points; restricted beats free by 15. It blocked 2 of the free version's 6
   biggest wins. **First window passed**; the book enters the pool at low priority.
3. **22 Nov – early Dec — second window.** The restricted version stays ahead by more than the margin. **Full
   standing.**
4. **In the Conductor.** When the breakout book sees breadth above 60 % and nothing is held, it takes the trade. If
   the champion fires in the same second, the Conductor compares their test-day records in that session phase.
5. **Ongoing.** If over the last 20 days the restricted version falls behind the free one, the rule is switched off
   and the book returns to shadow.

*(Illustrative numbers.)*

---

## 13. How success is judged

Every number below is measured **on test days only**, against c20_9x on the same days. These are goals, not promises.

| Measure | c20_9x today | Conductor goal |
|---|---|---|
| Strike rate | 54 % | ≥ 60 % |
| Trades per day | ~6 | ≥ 8 |
| Big option moves caught on normal days (≥ +40 % available) | 23 % | ≥ 50 % |
| Losing days | 4 of 14 | fewer, with a smaller worst day |
| Result on test days | — | positive |

---

## 14. Risks

| Risk | Handling |
|---|---|
| Too little history: 14 days sliced many ways produces lucky patterns | luck check in the search; margins and two windows in the test; the register prints expected lucky passes |
| Hindsight weather ("it was a trend day") | every number is computed from data up to the trigger second |
| Markets change | passed rules are watched and switched off when they fall behind |
| All-in sizing makes every loss felt | only confirmed conditions get money; exit work (§8) |
| Most factors are noise (docs/26) | the search keeps only what beats the luck baseline; the forward test is the final judge |
| Compute | restricted books in the evening replay; a nightly budget on the register; the live engine is unaffected |
| Missing data (no GIFT Nifty, global markets, news) | out of scope for the first version; can be added to the feed later |

---

## 15. Principles that do not change

* Buy-only Nifty weekly options; ATM or in-the-money strikes only.
* All-in on every trade; no position sizing.
* Yes/no rules only, no composite scores or weights.
* Paper trading; the live champion is untouched until the evidence says otherwise.
* Rules are dated and frozen; only days a rule has never seen count as proof.
* Every result is reported honestly, including what did not work.

---

## 16. Glossary

| Term | Meaning |
|---|---|
| Book | one complete trading strategy with its own paper capital and trades |
| Champion | the book the system currently treats as "the" trader |
| Shadow | any other book, trading on paper in the background on the same data |
| Strike rate / hit rate | the share of trades that close in profit |
| Weather / photograph | the ~150 market numbers at the second a trigger fires (docs/27) |
| Diary | a book's record of every trigger, its photograph and its outcome |
| Never worked / gave it back | the two kinds of losing trade: wrong weather vs a failed exit |
| Counterfactual | a trade a book would have taken while busy, reconstructed by the recorder; never a real trade |
| Weather card | a book's helped and hurt conditions, marked as found by searching the past |
| Rule | a dated, frozen yes/no condition for one book |
| Free / restricted book | the book taking every trigger vs only the triggers its rule allows |
| Test day | a day after the rule was frozen; the only days that count as proof |
| Margin | how far a rule must beat its free version, calibrated against shuffled labels |
| Pool | the books whose rules passed; the only books the Conductor trades |
| Conductor | the layer that combines pooled books into one non-clashing, all-in trade stream |
