# Apex Conductor — official specification

*One trading system built from Apex's strategies, each trading only in the market weather the future has confirmed
it wins in.*

**Status:** official specification, version 2, 7 November 2026. It combines the owner's write-up, the review
adjustments, and two rounds of stakeholder amendments, including the promotion standard (§2). **Nothing described
here trades yet.**

**Supporting documents:**

* docs/27 — the factor catalogue (the "weather");
* docs/29 — the missed-signal recorder;
* docs/26 — the event study;
* docs/20 — the current live system's specification (c20_9x).

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

**There is no champion.** In the end state the Conductor is the one system traded, and every book is simply a member
of its pool, there only because a dated, tested rule earned it a place. Until the Conductor proves itself, today's
live system (c20_9x) keeps trading, and it is the yardstick the Conductor must beat (§2).

One thing shapes everything below: **a pattern found by looking at the past is a guess until the future agrees with
it.** Patterns found in the taped days are written down with a date, new days judge them, and only patterns the
future confirmed get money behind them.

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
                                         (new days only; restricted book vs free book;
                                          the promotion standard; two windows)
                                                               │ passed
                                                               ▼
                                                       THE CONDUCTOR
                                       (one pot, all-in; first proven book to fire takes it)
                                                               │ beats the live system on
                                                               ▼ the same standard
                                                   THE SYSTEM YOU TRADE
```

---

## 2. The promotion standard — one test, applied at both levels

Nothing gets promoted on one number, one trade or one day. The same standard decides both:

* **a book's rule entering the pool** — its restricted book against its own free book; and
* **the Conductor replacing the current live system** — the Conductor against c20_9x.

Using one standard at both levels means the two can never pull in different directions. Every test is yes/no,
measured on **test days only** (days after the rule or the Conductor's rules were frozen), and **all** must pass:

| # | Test | Passes when |
|---|---|---|
| 1 | **Wins more often** | its strike rate (share of trades that close in profit) beats the comparator's by the luck margin (§6) |
| 2 | **Makes more money** | its rupees beat the comparator's by the luck margin |
| 3 | **Not one win** | it is still ahead on rupees after removing its single best trade, and also after removing its single best test day |
| 4 | **Keeps the big wins** | it still takes at least two-thirds of the comparator's biggest wins (its top 10 % of trades by rupees) |
| 5 | **No worse on bad days** | its worst test day is no worse than the comparator's worst test day |
| 6 | **Trades enough** (Conductor level only) | at least as many trades a day as the live system. A rule is a filter by design and is exempt, but it must still reach the minimum sample (§6) |
| 7 | **Holds over time** | it passes in the first window, and again in a second window of the same length |

Why each is there:

* **Tests 1 and 2** are the owner's: win more often, and make more.
* **Test 3** answers "one win alone does not decide": a result that depends on one runner or one lucky day fails.
* **Test 4** protects the few large trades that carry the current system's results: 8 trades made 79 % of its
  14-day total.
* **Test 5** guards against a higher strike rate bought with a bigger loss.
* **Test 6** is the owner's "trade often".
* **Test 7** stops a lucky window from promoting anything.

---

## 3. Where Apex stands today

| | Today |
|---|---|
| Instruments | Nifty weekly options, buy-only, ATM or in-the-money strikes (\|delta\| ≥ 0.52), paper trading |
| Capital rule | ₹1,00,000 fresh each day, all-in on every trade, no position sizing |
| Books running live | 72; 526 paper trades on 6 Nov |
| Current live system | c20_9x — on the 14 recorded days (19 Oct – 6 Nov): 81 trades, 54 % strike rate, ~6 trades a day, +₹12.1 L |
| Its weakness | 8 trades made 79 % of its total; live record 2 winning days, 4 losing; on normal days it caught 6 of 26 big option moves |
| Frequent books | spot breakout books trade 20–40 times a day at a 37–52 % strike rate; uneven from day to day |
| Recorded data | 14 full sessions; every new session adds about 70 move starts and 15 distinct option runs |
| Research so far | single indicators as yes/no filters on one book did not survive (docs/24, docs/26); no book has ever been analysed by market condition |
| Built for this plan | the missed-signal recorder (docs/29), identical on two tape slices; the full-tape proof is stage 2 (§13) |

### Families

Most of the 72 books are variants of a few strategies. Books are grouped into **families by entry logic**, because
the weather question is about *when a trigger fires*, and that is the entry's doing. Exits change what a trigger
earns, not when it fires.

| Family (by entry) | Examples |
|---|---|
| Council | c20_9x, c20_8x, c20_9y, c20_9s, c20_9v, c20_9t, c20_9e, c20_9h |
| t28 pullback | t28_gap, t28_core, t28_ivfall, … (20) |
| Spot breakout / retest / opening range | spot_dc12_t12 and variants, spot_orb45, spot_dual … |
| Impulse grid | the m-grid and gap books |
| Edge / straddle / fade | edge_*, straddle_spike, fade_switch, apex_edge |
| Controls (their own group) | RAW, random_entry, futures_only, premium_momentum |

"Level trail" is an exit style, so those books sit inside the family whose entry they use.

---

## 4. Step 1 — Each book's diary

One line per trigger, recording:

* when it fired and its direction (call or put);
* the weather photograph at that second (§11);
* the outcome: rupees, minutes held, best and worst points, exit reason.

**Labels on every line:**

* **Winner or loser** — closed in profit or not.
* **If a loser, what kind:**
  * **Never worked** — its best point never reached **+10 % of premium, or the book's own stop distance if that is
    larger**. *A weather problem.*
  * **Worked, then gave it back** — it reached that level and still closed at a loss. *An exit problem;* it goes to
    the exit work (§10), not the weather search.

**Missed signals** (from docs/29), while the book was busy:

* flagged `is_counterfactual`, never mistaken for real trades;
* both directions used — the real trade's own repeats are already folded in by the recorder, so a remaining
  same-direction row is a new setup;
* **weight:** a counterfactual that does not overlap the real trade in time counts as a **full observation**; one
  that overlaps counts as **half** (it shares the real trade's outcome);
* **search only** — never used to score a rule on test days.

---

## 5. Step 2 — The search: what did the winners have in common?

Per **family**, using a representative variant (below), and for each weather number: *if a line is drawn on this
number, do the winners fall mostly on one side and the losers on the other?*

> Example. A breakout book: 60 triggers over 14 days, 30 winners. With the line at 60 % breadth (the share of the 23
> big stocks moving with the trade):
>
> * above the line: 25 trades, 18 winners, 72 %;
> * below the line: 35 trades, 12 winners, 34 %.

| Check | Rule |
|---|---|
| **Enough trades on both sides** | at least **15 trades each side** for trade-level weather; for a pair of conditions at least **15 in the combined cell** |
| **Day-type weather counts days** | for whole-day facts (expiry or not, opening gap, VIX), at least **4–5 days on each side**; 30 wins on one trend day are one piece of evidence |
| **Holds when the line moves** | it must still work with the line slightly lower and higher (e.g. 55 % and 65 %) |
| **Keeps the big wins** | a condition that drops most of the book's largest wins is rejected |
| **Beats pure luck** | the same search on the same trades with win/loss labels shuffled shows what luck looks like; a real condition must be clearly better |

**Families in the search.** Variants of one entry share the same triggers with different outcomes, so the search
uses one **representative variant** per family: the one with the most triggers. A rule learned there is proposed for
the family. The luck arithmetic counts **distinct families**, not books, because variants pass or fail together.

The output is each family's **weather card**, every line marked **found by searching the past**.

---

## 6. Steps 3–4 — Dated rules and the forward test

### Writing a rule

* Plain language, dated: *"Breakout family — from 7 Nov: trade only when breadth ≥ 60 %."*
* One condition to start; two joined by "and" only if each passed alone; never three.
* One "strong triggers only" rule per family is allowed.
* Each rule records the days it was learned from and, ideally, a reason a trader would nod at.
* **Near-duplicates of a failed rule** (same factor, nearby threshold, same family) are blocked for 20 trading days,
  so the search cannot re-propose "breadth ≥ 58 %" the day after "breadth ≥ 60 %" failed.

### Frozen

From its date the rule does not change. A change makes a new rule with a new date and a fresh test.

### The restricted book

* The **representative variant** runs as a **registered restricted book** in the **evening replay** of each day's
  tape, beside its free version. It is never computed from the diary: blocking one trade changes the rest of the
  book's day.
* A passed rule is rolled out to the family's other variants, and each starts its own (shorter) confirmation window.
* **Live engine:** at most **5** rules that passed their first window may also run live; everything else stays in
  the evening replay, so the live engine is never slowed.
* **Compute:** restricted books start on the freeze date. The evening replay takes about 1 h 40 min per day for
  today's books plus a share per restricted book; the nightly budget is shown on the register.

### Windows

* **First window:** **30 restricted trades or 15 trading days, whichever comes later.** Day-type rules also need at
  least 5 test days on each side of the condition. **Never extended** until a rule passes; that would be searching
  again.
* **Second window:** the same length again.
* **Realistic timing:** a family firing once or twice a day needs **20+ test days**. Pooling variants does not
  shorten this, because they fire on the same triggers. Expiry-day rules (one expiry a week) need **two months or
  more**.
* **The early pass list will be short.** At 30 trades the luck margin is about 15 points of strike rate, so even a
  rule with a genuine 10-point edge will often fail its first window. That is the honest price of a strict test, not
  a sign that nothing works.

### The luck margin (tests 1 and 2 of §2)

Draw many random sets of the **free book's** test-day trades, each the same size as the restricted book's set. The
spread of their strike rates and rupees is what luck looks like. The restricted book must beat the **95th
percentile** of both.

*Caveat:* the restricted book is not an exact subset of its free book (it becomes free earlier and takes some
different later trades), so this is a close baseline, not an exact null. It is the right baseline for the question
asked.

### Pass, fail, switch off

| Result | What happens |
|---|---|
| Passes the promotion standard (§2) in the **first window** | enters the pool at **low priority** |
| Passes again in the **second window** | **full standing** |
| Fails at any stage | recorded as failed, with the near-duplicate block |
| A pooled rule falls behind its free version **on both strike rate and rupees, by the luck margin, over the last 40 trading days** | switched off until it recovers |

### The register reports its own luck

Every day: *"N rules under test across F families; P passed; about M of those passes are expected by luck."* M comes
from the same permutation, counted over families.

---

## 7. Step 5 — The Conductor

* **The pool starts empty.** Only rules that passed enter. No book has a place by name, the current live system
  included. Its strengths (expiry-afternoon breakouts, for example) earn their place the same way: a dated rule
  passing its windows. An empty pool trades nothing, which is fine, because the Conductor runs as a shadow until it
  meets the promotion standard against the live system.
* **One trade at a time, all-in, buy-only, ATM/ITM.**
* **First to fire takes it; the others wait.** "First" means the earlier tick. Within one tick, a fixed book order
  is recorded in every run manifest, so the result is the same on every replay.
* **Priority when two books are ready on the same tick:**
  1. full-standing beats low-priority, whatever the numbers;
  2. among equals, higher **test-day rupees per trade** wins.

  Strike rates on 20–40 test trades are too close to rank on.
* **Protected phases, the same rule for everyone.** If a full-standing book's passed rule covers a session phase
  (say, expiry afternoons), no lower-ranked book may enter a trade likely to still be open when that phase begins.
  "Likely" means within the entering book's **75th-percentile hold time**; on expiry days the 15:00 forced flat
  bounds it. Collisions are measured in replay first; if they turn out to be rare, the rule stays simple.
* **Switching is a candidate rule under trial, not a default.**
  * For every opposite-direction missed signal, its result is the new trade's P&L minus what the held trade went on
    to make from that second to its own exit.
  * It passes only if switching beats holding on test days on **choppy days** (day efficiency, net move ÷ path
    length, below a stated value) **and** on trending days.
  * Slippage and brokerage are left out of the whole study for now, at the owner's instruction. The switching trial
    therefore runs at zero cost, and that is flagged as an open question on the register. Switching will not be
    switched on without revisiting costs.
  * Until it passes, the Conductor runs "first to fire takes it; the others wait".
* **The Conductor's record is honest:** replayed on past days using the rules as they stood on each date.

---

## 8. Every evening

1. **Replay** today's tape: free books, restricted books, the Conductor.
2. **Score** every rule under test against the promotion standard.
3. **Learn:**
   * add today's triggers and photographs to the diaries;
   * rerun the search and the luck check;
   * propose new rules, dated today.
4. **Decide:** pass, fail, promote or switch off.
5. **Publish:**
   * the **rule register** (with the luck arithmetic and the nightly compute budget);
   * each family's **weather card**;
   * the **loss breakdown**: never-worked against gave-it-back.

No one adjusts rules by hand.

---

## 9. Safeguards on the machinery itself

| Check | When | What it proves |
|---|---|---|
| **Recorder is an observer** | stage 2 | recorder off vs on: every book trade-for-trade identical on two full tapes (one busy, one quiet) |
| **Determinism** | stage 3 | the same tape replayed twice gives identical trades and recorder output |
| **Leak test for every weather factor** | before any diary is built (stage 6) | each factor recomputed with **all data after the trigger second deleted** gives exactly the same value; any factor that changes is using the future and is dropped |
| **Whole-pipeline control run** | once stages 6–8 exist | the full loop (search, freeze, forward test, register) run on a deliberately useless input, e.g. a coin-flip book or a real book with outcomes shuffled before the search. Its pass rate must match the register's luck estimate; if not, the machinery leaks |
| **Point-in-time Conductor** | every evening | the Conductor replays with each day's rules as they stood |

**The leak test in detail.** For every factor in docs/27 and a sample of trigger seconds on several tapes:

1. compute the snapshot from the full day's data;
2. compute it again from a copy of the day truncated at the trigger second;
3. require the two to be bit-identical.

It runs automatically whenever a factor is added or changed.

---

## 10. The other half: exits

**Worked, then gave it back** losses are exit problems. Three candidate exit designs, each a dated, frozen candidate
with a forward test under the same promotion standard:

* a trail measured in premium, scaled by the option's live delta and gamma, active from the start;
* a theta budget: a trade that has paid more decay than its delta can earn back is cut;
* a give-back cap from the peak that tightens with gamma near expiry.

They are tested first on **all** diary triggers (thousands, not one book's 80 trades), so a design that kills the big
winners is caught early.

---

## 11. Which weather numbers are searched (docs/27)

**Searched:**

* time of day and the expiry calendar;
* the day's shape so far: trend or chop, position in the range, side of VWAP, the opening range;
* realised volatility;
* big-stock breadth and leadership;
* room to the nearest OI wall;
* whether the straddle is expanding;
* the option's breakeven against theta;
* VIX.

**Set aside:**

| Group | Why |
|---|---|
| The book's own trigger measurements | they are the entry rule (exception: one "strong triggers only" rule per family) |
| The book's own recent history | the Conductor replaces per-book habits; counterfactual rows have none |
| The engine's verdicts (regime label, advisors) | derived from the other numbers; kept as report labels |
| Five higher-order Greeks | largely one fact (time to expiry); one is kept |
| Model outputs (premium race, hidden regime, Hawkes, gamma map) | predictions with tuned parameters; each tested alone |
| Feed health, option spread | safety vetoes for every book |

---

## 12. A worked example *(illustrative numbers)*

1. **7 Nov — the search.** On the breakout family's representative variant, breadth ≥ 60 % gives 72 % against 34 %.
   On shuffled labels the best condition reaches 61 %. It survives at 55 % and 65 % and keeps 8 of the 10 biggest
   wins. The rule is frozen and the restricted book registered.
2. **First window (30 trades / 15 days).**
   * Restricted: 31 trades, 62 % strike rate, ₹41,000. Free: 61 % and ₹33,000 worse on both counts.
   * It clears the luck margins on both strike rate and rupees.
   * It is still ahead without its best trade and without its best day.
   * It keeps 5 of the free version's 6 biggest wins, and its worst day is no worse.

   **Low priority in the pool.**
3. **Second window.** It passes again. **Full standing**, rolled out to the family's variants.
4. **In the Conductor.** It takes the trade when it fires first. A tie with another full-standing book on the same
   tick goes to the higher test-day rupees per trade.
5. **Ongoing.** If it falls behind its free version on both strike rate and rupees, by the margin, over 40 days, it is
   switched off.

---

## 13. Build order

| # | Stage | Status |
|---|---|---|
| 1 | Missed-signal recorder | built and tested (docs/29); identical on two tape slices, **not yet proven on full tapes** |
| 2 | Freeze: recorder off vs on on two full tapes; the run manifest (commit, book registry, **fixed book order**) | next, ~2 h |
| 3 | Pre-flight: all books load; double replay identical; anchor check against the live days, each difference tagged by cause | ~2 h |
| 4 | One full tape, stop for sign-off with the anchor diff and validation report | ~2 h |
| 5 | Full replay of every book on all taped days (resumable, per-tape validation) | ~8 h |
| 6 | Weather snapshot engine + **leak test** | to build; the leak-test spec is §9 |
| 7 | Diaries, loss labels, family search with luck check, weather cards | to build |
| 8 | First dated rules; restricted books in the evening replay; the register | to build |
| 9 | Whole-pipeline control run | once 6–8 exist |
| 10 | Forward tests; first passes | weeks; low-frequency families 20+ days; expiry-day rules 2+ months |
| 11 | Conductor in the evening replay, then live as a shadow; switching trial | after the first passes |
| 12 | Exit candidates (§10) | in parallel from stage 7 |

---

## 14. How success is judged

The Conductor replaces the live system only by passing **the promotion standard (§2)** against it on test days.
Along the way, these are the goals, measured on test days against c20_9x on the same days. They are targets, not
promises.

| Measure | c20_9x today | Goal |
|---|---|---|
| Strike rate | 54 % | ≥ 60 % |
| Trades per day | ~6 | staged: ≥ the live system's once the pool holds several families; ≥ 8 as the pool grows |
| Big option moves caught on normal days (≥ +40 % available) | 23 % | ≥ 50 % |
| Profit concentration | 8 trades = 79 % of the total | still ahead with the best trade and the best day removed (test 3) |
| Worst day | −₹38,428 (offline, 3 Nov) | no worse (test 5) |

---

## 15. Risks

| Risk | Handling |
|---|---|
| Lucky patterns from too little history | luck checks in the search; margins, two windows and family-level luck counts in the test; the register prints expected lucky passes; the control run checks the machinery |
| Looking into the future | every factor computed up to the trigger second; the leak test proves it |
| Markets change | passed rules are watched and switched off when they fall behind |
| All-in sizing | only confirmed conditions get money; test 5 guards the worst day; exit work (§10) |
| Most factors are noise (docs/26) | only what beats luck is kept; the forward test is the final judge |
| A slow start | stated plainly: the first passes take weeks, and the pool starts empty |
| Compute | restricted books run in the evening replay; at most 5 live; the nightly budget is reported |
| Costs excluded | owner's instruction for now; switching stays off until costs are revisited |
| Missing data (GIFT Nifty, global markets, news) | out of scope for the first version |

---

## 16. Principles that do not change

* Buy-only Nifty weekly options; ATM or in-the-money strikes only.
* All-in on every trade; no position sizing.
* Yes/no rules only, no composite scores or weights.
* Paper trading; the live system is untouched until the evidence says otherwise.
* Rules are dated and frozen; only days a rule has never seen count as proof.
* No book is promoted by name; everything passes the same standard.
* Every result is reported honestly, including what did not work.

---

## 17. Glossary

| Term | Meaning |
|---|---|
| Book | one complete trading strategy with its own paper capital and trades |
| Family | books sharing one entry logic; the unit of search and luck counting |
| Representative variant | the family's book with the most triggers; the one tested first |
| Current live system | the book trading today (c20_9x); a transition role and the yardstick, not a privilege |
| Shadow | any book trading on paper in the background |
| Strike rate | the share of trades that close in profit |
| Weather / photograph | the ~150 market numbers at the second a trigger fires (docs/27) |
| Diary | a book's record of every trigger, its photograph and its outcome |
| Never worked / gave it back | a loss that never reached +10 % (or the stop distance), against one that did and still lost |
| Counterfactual | a trade a busy book would have taken; reconstructed, never real |
| Rule | a dated, frozen yes/no condition for a family |
| Free / restricted book | taking every trigger, against only the triggers the rule allows |
| Test day | a day after the rule was frozen; the only days that count as proof |
| Luck margin | the 95th percentile of random same-size subsets of the free book's test-day trades |
| Promotion standard | the seven yes/no tests of §2, used for rules and for the Conductor alike |
| Pool | the rules that passed; the only ones the Conductor trades |
| Conductor | the layer that combines the pool into one non-clashing, all-in trade stream |
