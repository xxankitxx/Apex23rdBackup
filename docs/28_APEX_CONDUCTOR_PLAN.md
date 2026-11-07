# Apex Conductor — official specification

*One trading system built from Apex's strategies, each trading only in the market weather the future has confirmed
it wins in.*

**Status:** official specification, version 3, 7 November 2026. It combines the owner's write-up, the review
adjustments, three rounds of stakeholder amendments and the owner's decisions of 7 Nov, including the promotion
standard (§2). **Nothing described here trades yet.** By the owner's instruction, **all engine replays run together
at the Conductor build** (§13); until then the work is code and unit tests.

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
| 1 | **Wins more often** | its strike rate (share of trades that close in profit) beats the comparator's by the luck margin |
| 2 | **Makes more** | its return beats the comparator's by the luck margin. Returns (% and points) are compared, not rupees: within a day capital compounds, so an afternoon trade's rupees depend on the morning. Rupees are reported alongside |
| 3 | **Makes money at all** | its own return on test days is **positive**, and stays positive with its single best trade removed and with its single best day removed. Losing less than a losing comparator is not enough |
| 4 | **Not one win** | it is still ahead of the comparator with its single best trade removed, and also with its single best test day removed |
| 5 | **Keeps the big wins** | it still takes at least two-thirds of the comparator's biggest wins (its top 10 % of trades by return). At the Conductor level, "takes" means the Conductor held a position in the same direction when the live system's big-win trade was entered, or entered within 60 s of it |
| 5b | **No worse on bad days** | its worst test day is no worse than the comparator's worst test day |
| 6 | **Trades enough** (Conductor level only) | at least as many trades a day as the live system. A rule is a filter by design and is exempt, but it must still reach the minimum sample (§6) |
| 7 | **Holds over time** | it passes in the first window, and again in a second window of the same length |

**Luck margins at the two levels.**

* **A rule against its free book:** membership permutation (§6); a day-level permutation for day-type rules.
* **The Conductor against the live system:** they take different trades, so a subset permutation does not apply.
  Pair each test day's Conductor result with the live system's on the same day, take the daily differences, and flip
  their signs at random many times. The Conductor must beat the 95th percentile, for both daily return and daily
  strike rate.

**The Conductor's window** is its most recent 30 trading days, **restarted whenever the pool's composition or the
priority rules change materially**; a window during which the pool grew from one family to four does not test the
Conductor you would trade. By design, the Conductor cannot pass test 5 against the live system until the
council-expiry family's own rule has passed, so its promotion waits on that rule.

Why each is there:

* **Tests 1 and 2** are the owner's: win more often, and make more.
* **Test 3** keeps losing books out of the pool, even when they lose less than their free version.
* **Test 4** answers "one win alone does not decide": a result that depends on one runner or one lucky day fails.
* **Test 5** protects the few large trades that carry the current system's results: 8 trades made 79 % of its
  14-day total.
* **Test 5b** guards against a higher strike rate bought with a bigger loss.
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

Families are defined by **entry pattern × day type**, because the weather question is about *when a trigger
fires*, and that is the entry's doing. Exits change what a trigger earns, not when it fires. A book whose entry
differs by day type (e.g. "retest on expiry day, pullback otherwise") belongs to two families.

| Family | Fires when | Books (examples) | Representative |
|---|---|---|---|
| Council-expiry | expiry day: the forward breaks its 10-min range with velocity | c20_9x and its council shadows, on expiry days | c20_9x |
| Council-normal | normal day: 40-pt impulse → 50–75 % pullback → resumption | the same council books, on normal days | c20_9x |
| Spot first-touch | spot breaks its 12-min range, bought at once | spot_dc12_t12_first, spot_ft_prem10 | spot_dc12_t12_first |
| Spot retest | the 12-min break, bought on the retest | spot_dc12_t12, _1130, _nolock, edge_breakout; the retest leg of every "retest on expiry" book | spot_dc12_t12 |
| 45-min pullback | 50–78 % pullback of a ≥ 60-pt 45-min spot impulse | t28_* (20), lvl_trail* (6), spot_dual*, spot_pb45, the edge pullback books (about 36 in all) | spot_pb45 |
| Opening range | break of the opening range | spot_orb45 | spot_orb45 |
| Impulse + basket | futures impulse z and heavyweight synchrony | the m-grid (15) | m1.5_s0.4 |
| Basket gap | the basket leads, futures lag | gap3_s0.4, gap5_s0.4 | gap3_s0.4 |
| Straddle spike | the straddle's gamma leg spikes | straddle_spike | straddle_spike |
| Burst follow / fade | short bursts, followed or faded | fade_switch | fade_switch |
| Controls | yardsticks | RAW, random_entry, futures_only, premium_momentum | — |

* The **representative** is the family's **least-gated member** (the one with the fewest extra conditions, so it
  sees the family's triggers most plainly), named explicitly in the table; t28_fwd is its own family. It is the one
  the family's rule is learned on and tested first. (Until 7 Nov this said "the most triggers"; identical twins such
  as t28_bidpile = t28_gap made that a tie.)
* **Controls never enter the pool.** They go through the search so their results show what luck looks like, but no
  rule on a control is ever pooled. RAW is a copy of c20_9x, so it is no longer a control in effect; random_entry is
  the control-run input (§9).

---

## 4. Step 1 — Each book's diary

One line per trigger, recording:

* when it fired and its direction (call or put);
* the weather photograph at that second (§11);
* the outcome: % return and points (what the search uses), rupees (reported), minutes held, best and worst points,
  exit reason, and whether the fill or exit was stale or in a data gap.

**Labels on every line:**

* **Winner or loser** — closed in profit or not.
* **If a loser, what kind:**
  * **Never worked** — its best point never reached **one-third of its family's median winning peak, and at least
    the book's own stop distance**. *A weather problem.* (A flat +10 % would mislabel almost every one-minute domino
    loss as a weather problem, so the threshold is set per family.)
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
uses one **representative variant** per family: its least-gated member (§3). A rule learned there is proposed for
the family. The luck arithmetic counts **distinct families**, not books, because variants pass or fail together.

The output is each family's **weather card**, every line marked **found by searching the past**.

---

## 6. Steps 3–4 — Dated rules and the forward test

### Writing a rule

* Plain language, dated: *"Breakout family — from 7 Nov: trade only when breadth ≥ 60 %."*
* One condition to start; two joined by "and" only if each passed alone; never three.
* One "strong triggers only" rule per family is allowed.
* Each rule records the days it was learned from and, ideally, a reason a trader would nod at.
* **Near-duplicates of a failed rule** (same factor, a threshold within ±20 % of that factor's range, same family)
  are blocked for 20 trading days,
  so the search cannot re-propose "breadth ≥ 58 %" the day after "breadth ≥ 60 %" failed.

### Frozen

From its date the rule does not change. A change makes a new rule with a new date and a fresh test.

### The restricted book

* The **representative variant** runs as a **registered restricted book** in the **evening replay** of each day's
  tape, beside its free version. It is never computed from the diary: blocking one trade changes the rest of the
  book's day.
* A passed rule is rolled out to the family's other variants, and each starts its own confirmation window of 15
  trading days. Each confirmed variant becomes its own pool entry (book under rule).
* **Live engine:** at most **5** rules that passed their first window may also run live; everything else stays in
  the evening replay, so the live engine is never slowed.
* **Compute:** restricted books start on the freeze date. The evening replay takes about 1 h 40 min per day for
  today's books plus a share per restricted book; the nightly budget is shown on the register.

### Windows

* **First window:** **30 restricted trades or 15 trading days, whichever comes later.** Day-type rules also need at
  least 5 test days on each side of the condition, counted on the **free book's** days (the restricted book does not
  trade on the off side). **Never extended** until a rule passes; that would be searching
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
spread of their strike rates and returns (% per trade, test 2) is what luck looks like. The restricted book must
beat the **95th percentile** of both. Rupees are reported, never tested (§2).

*Caveat:* the restricted book is not an exact subset of its free book (it becomes free earlier and takes some
different later trades), so this is a close baseline, not an exact null. It is the right baseline for the question
asked.

**Day-type rules** select whole days, and trades within a day move together. For any rule whose condition is a
whole-day fact, the permutation draws random **days** (as many as the rule allows) from the free book's test days,
not random trades.

### When test days are scored

A rule frozen on date D is tested on days after D. By the owner's instruction, engine replays run together at the
Conductor build, so restricted books are **scored then**, on every recorded session after each rule's date. Nothing
is lost: every session's tape is recorded. Rules can be written, dated and frozen now, and their test days
accumulate from the next session.

### Pass, fail, switch off

| Result | What happens |
|---|---|
| Passes the promotion standard (§2) in the **first window** | enters the pool at **low priority** |
| Passes again in the **second window** | **full standing** |
| Fails at any stage | recorded as failed, with the near-duplicate block |
| A pooled rule's **switch-off e-value** reaches 20 (below) | switched off; it can come back only as a new rule |

**Watching a passed rule (the only switch-off rule).** From the day a rule passes, take each test day's difference
d = (restricted book's daily return − free book's daily return), in %. Two betting e-values from learning.py, both
valid however often they are looked at:

* `e_value_mean_le0(d)`, **still earning its place**: reported nightly; it grows while the rule keeps adding return;
* `e_value_mean_le0([-x for x in d])`, **switch-off**: when it reaches **20** (the 5 % line), there is evidence the
  rule now costs return, and it is switched off.

There is no fixed 40-day look-back: a fixed window looked at every night has a multiple-looks problem; the e-value
does not. (This replaces the earlier "falls behind over the last 40 trading days" wording everywhere.)

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
* **The pool holds book-plus-rule pairs.** The representative trades its family's rule until the variants confirm;
  each confirmed variant is a separate pool entry.
* **First to fire takes it; the others wait.** "First" means the earlier tick.
* **Priority when two entries are ready on the same tick:**
  1. full-standing beats low-priority, whatever the numbers;
  2. among equals, the higher **test-day return per trade** wins;
  3. the last tiebreak only: the fixed book order recorded in every run manifest, so the result is the same on every
     replay.

  Strike rates on 20–40 test trades are too close to rank on.
* **Protected phases, the same rule for everyone.** A rule *covers* a phase only if its condition explicitly names
  one (a calendar or clock factor, e.g. "expiry day after 13:00"); a breadth rule covers no phase. If a
  full-standing entry's rule covers a phase, no lower-ranked entry may open a trade likely to still be open when that
  phase begins.
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
* **Occupancy.** Holds run from about a minute (impulse grid) to 90 minutes (council normal-day). With one pot and one
  position, long holders own their stretch of the day and fast families fill the gaps. The Conductor replay measures
  collisions and occupancy before any trades-a-day goal is expected.

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
| **Determinism** | stage 6 (the Conductor build) | the same tape replayed twice gives identical trades and recorder output (`apex/replay_compare.py`) |
| **Leak test for every weather factor** | before any diary is built (stage 6) | each factor recomputed with **all data after the trigger second deleted** gives exactly the same value; any factor that changes is using the future and is dropped |
| **Whole-pipeline control run** | at the Conductor build, before the first real search is read | the full loop (search, freeze, forward test, register) run on random_entry's real diary, and on one real book with its outcomes shuffled before the search. The pass rate must match the register's luck estimate; if not, the machinery leaks |
| **Point-in-time Conductor** | every evening | the Conductor replays with each day's rules as they stood |

**The leak test in detail.** For every factor in docs/27 and a sample of trigger seconds on several tapes:

1. compute the snapshot from the full day's data;
2. compute it again from a copy of the day truncated at the trigger second **by arrival time**: the second the data
   reached the engine (`recv_ns`), not the exchange timestamp (OI snapshots, quotes and depth can carry exchange
   times earlier than their arrival);
3. require the two to be bit-identical.

Expect at least one real catch: docs/27 G49 "IV against today's median" must be the median *so far*.

It runs automatically whenever a factor is added or changed.

---

## 10. The other half: exits

**Worked, then gave it back** losses are exit problems. Three candidate exit designs, each a dated, frozen candidate
with a forward test under the same promotion standard:

* a trail measured in premium, scaled by the option's live delta and gamma, active from the start;
* a theta budget: a trade that has paid more decay than its delta can earn back is cut;
* a give-back cap from the peak that tightens with gamma near expiry.

They are tested first on **all** diary triggers (thousands, not one book's 80 trades), so a design that kills the big
winners is caught early. **Start with the variants that already exist:** t28, lvl_trail and the c20_9x shadows differ
from their bases only by exits, on identical triggers, so they are a ready-made exit experiment.

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
   * Restricted: 31 trades, 62 % strike rate, +6.1 % average return. Free: 61 trades, 47 %, +2.4 %.
   * It clears the luck margins on both strike rate and return.
   * It is still ahead without its best trade and without its best day.
   * It keeps 5 of the free version's 6 biggest wins, and its worst day is no worse.

   **Low priority in the pool.**
3. **Second window.** It passes again. **Full standing**, rolled out to the family's variants.
4. **In the Conductor.** It takes the trade when it fires first. A tie with another full-standing book on the same
   tick goes to the higher test-day return per trade.
5. **Ongoing.** Its switch-off e-value (§6) is watched every night; if it reaches 20, the rule is switched off.

---

## 13. Build order

**All engine replays run together at the Conductor build (owner, 7 Nov).** Until then: code and unit tests only.

| # | Stage | Status |
|---|---|---|
| 1 | Missed-signal recorder | built and unit-tested (docs/29); proven on two tape slices; full-tape proof at the Conductor build |
| 2 | Weather snapshot engine on the existing entry hook (`open_trade` already records `signal`, `edge_in`, `advisors`, `regime`, `phase_in`, `sr_in`; counterfactuals carry the same), **leak test** by arrival time. The eight shortlisted factors first: calendar/phase, day efficiency, position in range, breadth, room to OI wall, straddle expanding, theta breakeven, VIX | **the eight built 7 Nov** (`apex/engine/weather.py`; `weather_trig` on every position and missed row; leak test by arrival time in tests/test_weather.py). The rest of docs/27 next, family by family; the full-tape leak test (a replay truncated at each trigger) runs at the Conductor build |
| 3 | Diaries, loss labels (per-family threshold), family search with luck check, weather cards, rule register | to build |
| 4 | Hand-written rules, dated and frozen now (they need no search). Candidates: spot retest on expiry days before 11:30; normal days only after a trending last 60 min; breakout and impulse families only with breadth ≥ 60 %; council-normal mornings only; no entries in the last 45 min for families holding > 15 min | **frozen 7 Nov** with exact formulas: docs/31, `apex/rules/register.json` (R-001 to R-005, plus the seeded pairs R-006 to R-018) |
| 5 | Restricted-book machinery; Conductor code (pool, priority, protected phases) | to build |
| 6 | **Conductor build — all replays together:** the recorder gate on two full tapes (docs/29); pre-flight (books load, double replay identical, anchor check against live days); one tape for sign-off; full replay of every book on all recorded days with the run manifest (commit, book registry, fixed book order); diaries; the whole-pipeline control run; scoring every frozen rule on its test days; the Conductor's own replay | at the Conductor build |
| 7 | Forward tests continue on each new day; first passes | weeks; low-frequency families 20+ days; expiry-day rules 2+ months |
| 8 | Conductor live as a shadow; switching trial | after the first passes |
| 9 | Exit candidates (§10), starting with the existing variants | in parallel from stage 3 |

---

## 14. How success is judged

The Conductor replaces the live system only by passing **the promotion standard (§2)** against it on test days.
Along the way, these are the goals, measured on test days against c20_9x on the same days. They are targets, not
promises.

| Measure | c20_9x today | Goal |
|---|---|---|
| Strike rate | 54 % | ≥ 60 % |
| Trades per day | ~6 | staged: ≥ the live system's once the pool holds several families; ≥ 8 as the pool grows (bounded by occupancy, §7) |
| Big option moves caught on normal days (≥ +40 % available) | 23 % | ≥ 50 % |
| Profit concentration | 8 trades = 79 % of the total | still ahead with the best trade and the best day removed (tests 3 and 4) |
| Worst day | −₹38,428 (offline, 3 Nov) | no worse (test 5b) |

---

## 15. Risks

| Risk | Handling |
|---|---|
| Lucky patterns from too little history | luck checks in the search; margins, two windows and family-level luck counts in the test; the register prints expected lucky passes; the control run checks the machinery |
| Looking into the future | every factor computed up to the trigger second; the leak test proves it |
| Markets change | passed rules are watched and switched off when they fall behind |
| All-in sizing | only confirmed conditions get money; test 5b guards the worst day; exit work (§10) |
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

## 16a. Decisions and facts added 7 Nov (stakeholder rounds 4–5)

**Owner's decisions**

* **The learning loop is record-only** (`config.LEARN_DECIDE = False`), live and in replay. It still writes its
  nightly report and says what it *would* have done ("Record-only" section; a `record-only` entry in its log), but it
  never changes the default book, retires a book, adds or removes a gate, or adds or drops a candidate book. During
  the forward tests nothing may change a book except a dated, frozen rule; in a run of several replayed days, day
  N+1's book set no longer depends on day N's learning.
* **The five 0.46-delta books stay as they are for now:** t28_d46, t28_core, t28_core_fill, t28_all, t28_d46_fill
  (`delta_target` 0.46 on non-expiry days, below the 0.52 floor). Not changed today; revisit before they enter the
  pool.
* **Families are assigned per diary row**, from what the row carries, not by book: entry pattern (`ep_type`:
  SPOT-PULLBACK, SPOT-RETEST, SPOT-RETEST-FILL, SPOT-BREAKOUT, ORB, FOLLOW/FADE, the domino types with or without a
  gap, STRADDLE-SPIKE, RANDOM, PREMIUM-MOMENTUM; council EXP / NORM) × day type (expiry or not). A filler book can
  so put rows in two families, and the ~40 books that fire the same expiry retest count as one family. Each family's
  representative is its least-gated member (spot_pb45, spot_dc12_t12, spot_dc12_t12_first, spot_orb45, m1.5_s0.4,
  gap3_s0.4, straddle_spike, fade_switch, c20_9x; t28_fwd is its own family).
* **The rule register is seeded from the restricted-vs-free pairs already running**, each frozen on the date its
  config comment gives: spot_dual_rg vs spot_dual (22 Oct); spot_dc12_t12_1130 vs spot_dc12_t12 (~21 Oct); t28_gap,
  t28_dur20 vs lvl_trail_re (28 Oct); m2.0_s0.5_trend, m2.0_s0.5_novol vs m2.0_s0.5 (19 Oct); edge_gate_only vs
  spot_dual_lvl (27 Oct); t28_ivfall / bidpile / nohigh / req / cheap vs t28_gap (28–29 Oct); c20_9s, c20_9y vs
  c20_9x (3–4 Nov). Exit-only pairs (nolock, tt8, mh15, st20, the be/rx chain, c20_9t/v/e/h) go to the exit test
  (§10) instead.

**How the machinery works (built 7 Nov)**

* **Diaries read `paper/<day>.json`**, not the learning loop's `days.jsonl`, which keeps only a reduced trade (no
  peak, hold time, edge, delta or trigger time).
* **The photograph is taken at the trigger.** `request_entry` stores `signal_trig` and `edge_trig` with the pending
  entry and the fill copies them to the position. They describe the last completed virtual second before the
  trigger. `signal` / `edge_in` are still the values at the fill, up to 3 s later.
* **One folder per run, with a manifest** (`apex/replay_batch.py`): every batch run gets a fresh
  `data/replay/batch/<run_id>/` (an existing folder is refused), and `manifest.json` records the tapes and their
  hashes, git commit and code hash, step size, every switch that changes what a replay trades (recorder, fast path,
  entry end, flatten, CAS test, learning mode, a hash of the book list), the starting learning state, the book order
  (the same-tick tie-break order), and at the end trades per book, recorder rows, errors, faults and wall time.
  A batch never serves the dashboard and uses its own shared-memory names, so it cannot collide with a live
  session; `replay_fast --gateway` refuses to start while a session holds the default names.
* **The compare tool** (`apex/replay_compare.py RUN_A RUN_B`) is the other half of the gate: per day it compares
  every book, trade and field exactly, then the decision, strike, missed and event tapes line by line, and fails on
  any recorder error. `--books-only` for recorder off vs on.
* **Faithful starting files.** `--seed` copies yesterday's levels (`day_levels.json`), the strike-levels prior and the
  declared defects along with the learning state; the manifest hashes them. For the full pass: seed from the live
  data folder, tapes in date order, no gaps. Every restarted-feed part of a tape is listed and hashed, and the
  manifest carries a hash of every config constant, the Python / numpy versions and what each day actually ran with.
  Live wrote yesterday's levels only from 22 Oct, so level-exit differences on earlier days are tagged
  "no prior levels live" in the anchor check.
* **Quarantine windows are per cluster.** A day's quote-defect trades are grouped (a new window after 30 min clear);
  one stale quote at 14:50 no longer throws out the morning. An automatic window covering the whole session removes
  the day, like a declared one.
* **The opening range after a late start is unknown, not wrong.** If the engine's first trusted print is more than
  10 min after 09:15 (a cold restart), there are no OR levels and the ORB book does not trade that day.
* **DATA events are on market time.** The "no trade for 300 s on hero contract(s)" line is now written once per
  market second from the engine step, not from the 4-Hz wall-clock dashboard publish, so the events tape of a replay
  is the same run to run (needed by the gate in docs/29).
* **Reuse, not rebuild:** `defects.Quarantine` / `quote_defect` for diary exclusions; `is_cas_trade` for the
  anchor check; `_day_ret` and `_lodo_ok` as the day unit and the leave-one-day-out check; `paired_test` as the
  skeleton of the Conductor-level day test, with the sign-flip permutation added for the margin.
* **Watching a rule after it passes:** the betting e-value already in learning.py (`e_value_mean_le0`) on the daily
  (restricted − free) differences from the pass date. It is valid however often it is looked at, so the nightly look
  does not inflate the false-alarm rate as a fixed 40-day window would. Two-sided, as §6 sets out: the switch-off
  e-value on the negated differences reaching 20 switches the rule off.
* **Pooled counts overstate evidence.** The learning report's pooled rows count the ~40 books that fire on the same
  trigger as separate evidence. Evidence-only today; per family in step 2.

## 17. Glossary

| Term | Meaning |
|---|---|
| Book | one complete trading strategy with its own paper capital and trades |
| Family | books sharing one entry logic; the unit of search and luck counting |
| Representative variant | the family's least-gated member (§3); the one tested first |
| Current live system | the book trading today (c20_9x); a transition role and the yardstick, not a privilege |
| Shadow | any book trading on paper in the background |
| Strike rate | the share of trades that close in profit |
| Weather / photograph | the ~150 market numbers at the second a trigger fires (docs/27) |
| Diary | a book's record of every trigger, its photograph and its outcome |
| Never worked / gave it back | a loss whose best point never reached one-third of its family's median winning peak (and at least the book's stop distance), against one that did and still lost (§4) |
| Counterfactual | a trade a busy book would have taken; reconstructed, never real |
| Rule | a dated, frozen yes/no condition for a family |
| Free / restricted book | taking every trigger, against only the triggers the rule allows |
| Test day | a day after the rule was frozen; the only days that count as proof |
| Luck margin | the 95th percentile of random same-size subsets of the free book's test-day trades |
| Promotion standard | the yes/no tests of §2 (1–7 plus 5b), used for rules and for the Conductor alike |
| Pool | the book-plus-rule pairs that passed; the only entries the Conductor trades (controls never) |
| Conductor | the layer that combines the pool into one non-clashing, all-in trade stream |
