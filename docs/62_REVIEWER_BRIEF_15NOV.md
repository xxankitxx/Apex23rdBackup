# ApexOptions Reviewer Brief

15 Nov 2026. Markdown copy of the shared doc; the doc is the master copy.

No part of this system has a proven edge yet. This brief shows outside reviewers every part of it, what changed between 5 and 15 Nov 2026, and where criticism would help most.

## 1. What we ask of you

Attack this system; do not approve it. We want to learn why it has no proven edge, where it can be wrong, and what to remove.

Three kinds of criticism help most:

- **Evidence.** Where a conclusion rests on too little data, on a choice made after seeing the result, or on a test that could not have failed.
- **Correctness.** Where the code can produce a wrong number, a wrong trade, or a statement on screen that is not true.
- **Design.** Where the structure makes errors likely or progress slow, and what you would delete.

A useful finding names the file and line (or the document and section), gives one concrete scenario, says what goes wrong, and proposes the smallest change. Say also what evidence would change your mind.

### The owner's fixed rules

These are choices, not findings. You may argue against them, but treat them as the frame the code was built in.

| Rule | Value |
| --- | --- |
| Instrument | Nifty 50 weekly index options on NSE India |
| Direction | Buy only: a call or a put. Nothing is ever sold short or written |
| Strike | At or in the money. The champion's strike picker needs \|delta\| of at least 0.52; its order gate refuses under 0.50. Exception: five older shadow books (t28\_d46, t28\_core, t28\_core\_fill, t28\_all, t28\_d46\_fill) target \|delta\| 0.46 on normal days |
| Size | All capital on every trade, in whole lots of 65. No position sizing |
| Capital | Rs 1,00,000 fresh at the start of every trading day |
| Money | Paper only. No order reaches a broker |
| Holding | Intraday only. The champion family is forced flat at 15:20, and at 15:00 on expiry days; older books at 15:25 |

### How to read this brief

| Sections | What they hold |
| --- | --- |
| 2 and 3 | The whole system on one page, then one diagram |
| 4 to 16 | Every part in turn: data, engine, paper fills, strategies, the live account, observers, forecasting, learning, dashboard, research tools, tests, operations |
| 17 | The evidence on profit, test by test, with each test's caveat |
| 18 | What changed from 5 to 15 Nov 2026 |
| 19 and 20 | Known weaknesses, then the questions we most want answered |
| 21 | File map and glossary |

The brief describes the code at commit c489e61 of 15 Nov 2026, including fixes made that day. Four additions, one correction and one change to a live fill rule made later that evening are noted at the top of section 18. File paths are relative to the repository root. The `secrets/` folder is outside the review: do not open it.

## 2. The system in one page

ApexOptions watches the Nifty options market every second and lets 122 rule sets trade it on paper, side by side, to find one worth trusting. None has earned that trust yet.

**What it is.** A Python system for one Windows PC: about 38,000 lines in 127 source files, 4,400 lines of dashboard code, and 17,000 lines of tests in 86 files. It lists nine packages, chiefly numpy, scipy, FastAPI, uvicorn and the broker's SDK (breeze-connect). Research and Lab code also import pandas and joblib, which are not listed.

**What runs.** A supervisor starts three processes that share memory: the feed (the broker's websocket), the engine (all trading logic), and the gateway (the dashboard, on localhost). A fourth process, the Forecast Lab, runs apart and only reads.

**A book.** One rule set with its own paper account is called a book. There are 122. Each starts every day with Rs 1,00,000 and puts all of it on every trade.

**The live account.** The account the owner follows is called the Conductor. It owns no rule of its own. It takes the first trigger among five pool books (c20\_9y, c20\_9s, c20\_9v, c20\_9x, c20\_9t), copies that trade with its own capital, and leaves when that book leaves. The owner declared it champion on 9 Nov 2026; it did not earn the place through the system's own test.

**The pattern it trades.** On normal days: the forward moves 40 points within 20 minutes, pulls back about half, turns 5 points, and the book buys in the direction of the move. On expiry days: the forward breaks its 10-minute range with 20 points of speed in 150 seconds. Exits are a 15 % premium stop, a trail on the forward, profit floors and a clock.

**Everything else.** The other 116 books are shadows, controls or older families. They trade on paper beside the live account and change nothing. The forecasts, the commentary and the voice card are display only.

### Honest status on 15 Nov 2026

| Question | Answer |
| --- | --- |
| Live record of the Conductor | 4 sessions (9, 11, 12, 13 Nov): 22 trades, 9 winners. Days, in rupees on Rs 1,00,000: +59.7 %, +7.4 %, +3.7 %, -27.1 % |
| The same pattern on four years | 2,214 trades before the recorded window: 33 % winners, -0.01 % a trade. The recorded window is its best quarter of 17 |
| Search for a better entry | 4,217 variants tried on 14 and 15 Nov. None passed the bar set in advance. Every finalist lost on the untouched year |
| Promotion standard | Nothing has passed the seven-test standard |
| Code health | 759 tests pass. Three reads on 15 Nov found no defect in the code changed since 13 Nov that alters a live trade, and 18 defects were fixed. The surveys for this brief then confirmed 54 further points in older code; 8 on the live path were fixed the same evening (section 19) |

The system is therefore a well-instrumented test bench around an unproven idea. Sections 17 and 19 say this in detail.

## 3. At a glance

```
 Broker (ICICI Breeze)                                          Dashboard in a browser
 websocket quotes, REST                                         one local page, 127.0.0.1
          |                                                                ^
          v                                                                |
+--------------- started and watched by the supervisor (run_apex.py) ----------------+
|  Feed                          Engine                         Gateway              |
|  parses each broker packet     reads the table every 0.1 s    serves the engine    |
|  writes the table of quotes -> steps 122 books, then the   -> state to one local   |
|  records every packet          live account; paper only       page; no login       |
+------------------------------------------------------------------------------------+
          |                               |                                ^
          v                               v                                |
 Tick tape (data/ticks)          Books and day record            Forecast Lab
 every packet, 21 days so far    trades, events, speed log       separate process, by hand
 a replay feeds it back in       scored every evening            reads quotes, posts a panel
```

Quotes flow from left to right through shared memory. The feed and the engine also write to disk, and a replay sends the recorded tape back through the same parser. The Forecast Lab sits outside: it reads quotes and posts a panel, and nothing in the engine reads it back.

## 4. Market data: the feed, shared memory, recording and replay

One parser turns every broker packet into a row of a shared table, and the same parser serves live, simulated and replayed data. That single path is the system's best protection against a replay that differs from live.

### From packet to quote

| Stage | What happens |
| --- | --- |
| Login | The feed logs in to the broker (ICICI Breeze) with the day's session token |
| Universe | About 121 instruments: 7 index rows, this week's options 12 strikes either side of the money, next week's 4 strikes, and 23 heavyweight stocks with cash and futures |
| Re-centre | When the money sits 4 strikes off the band's centre for 30 s, the option band is extended; existing rows keep their place |
| Receive | Each websocket message is stamped with the receive time and applied in arrival order |
| Parse | `apply_packet` in `apex/feed_core.py`. A packet from an earlier day is dropped. A packet 2 s older than the held quote keeps the held price |
| Slow data | The volatility index by REST every 60 s; chain open interest every 90 s; at most 3,000 data calls a day by REST |

### Shared memory

| Segment | Holds | Writer | Readers |
| --- | --- | --- | --- |
| Table | 512 rows of 392 bytes: 25 fields per instrument, with five levels of depth. Each row has a sequence counter, so a reader can detect and re-read a half-written row. Rows still torn after 2 ms are returned and counted | Feed | Engine, gateway, Forecast Lab |
| Control block | 24 fields: heartbeats, feed state, the stop flag, the replay clock | Each process its own fields | Supervisor and all processes |
| State blob | Up to 2 MiB of JSON: everything the dashboard shows | Engine, every 0.5 s | Gateway |

### What is recorded

Every raw packet goes to `data/ticks/<date>.jsonl.gz` through a queue, with a new part after each feed restart. The set today is 21 days in 40 files, 3.8 GB. The engine adds a per-minute speed log under data/logs, and its books, trades, events and decisions under `data/paper/`.

### Three ways to run

| Mode | Feed | Clock |
| --- | --- | --- |
| Live | The broker's websocket | Wall time; the engine samples every 0.1 s |
| Sim | Synthetic packets every 0.25 virtual seconds | The feed's virtual clock; not locked to the engine |
| Replay | A recorded tape | Lock-step: the feed waits for the engine at every 0.1 s of tape. A `--fast` variant runs parser and engine in one process |

### The paper-only interlock

`apex/interlock.py` replaces every order-like method of the broker's SDK with a stub that raises. `config.PAPER_ONLY = True` is checked only by the optional preflight command; the live start does not check it.

### Points the survey flagged (confirmed by a second read unless noted; fixed ones say so)

- **The interlock is thinner in live than in preflight.** The live feed installs only the method-name block. The URL allowlist runs only in the preflight command, and the installer swallows every exception.
- **A feed restart zeroes the table.** The engine then resets its price history. A live re-centre keeps row ids.
- **An oversized state is dropped silently.** If the dashboard's JSON passes 2 MiB, nothing is published and nothing is logged.
- **The tape does not record when the live engine sampled,** so a replay need not step at the instants live did.
- **No test covers the lock-step handshake between processes,** the refused-login wait, or the re-centre routine itself.
- **The 15 files of this layer hold 83 broad `except` clauses,** 25 in the feed and 22 in the supervisor.

## 5. The engine: one step from start to finish

The engine steps up to ten times a second. Each step reads the shared table, rebuilds prices and greeks, judges whether the data can be trusted, runs every book, then the live account. All of it is single-threaded Python in `apex/engine_main.py` (2,419 lines; `step()` alone is 241).

### The phases of one step, in order

| # | Phase | What happens |
| --- | --- | --- |
| 1 | Day | Reads the clock. Starts the day. Closes it on a date change or from 15:41 |
| 2 | Market | Snapshots the table into a 60-second ring. The future is its bid-ask mid when the spread is at most 30 points |
| 3 | Greeks | Implied volatility and greeks for the chain, every 0.25 s. One-second price histories |
| 4 | Guards | Order-book pressure, dealer gamma, the data guard, heavyweight stocks, regime |
| 5 | Observers | Display and record modules. The step ends here if neither the future nor the index has a price |
| 6 | Context | One dictionary of prices, option rows, quote ages and the blackout flag, shared by all books |
| 7 | Pre-books | Advisors and the feeds for the weather photograph |
| 8 | Books | Every book in registration order: exit check, then entry. Then the Conductor, the six shadow accounts, the voice card |
| 9 | After | Candidate ledger, episode log, saves. State is published to the dashboard every 0.5 s |

In a replay the engine takes exactly one step per 0.1 s of recorded time, so results do not depend on machine speed.

### Prices and greeks

- **Forward.** The mean of strike + call - put over the two strikes nearest the reference price. A leg older than 30 s is left out. A result more than 150 points from the reference is replaced by the reference. No interest rate.
- **Model.** Black-76 on that forward. Implied volatility by 40 bisections between 0.5 % and 500 %.
- **Time.** Calendar seconds to 15:30 on expiry day over a 365-day year, floored at 600 s on expiry day.
- **Units.** Volatility in percent. Theta in premium points per trading minute (a year is 365 days of 375 minutes).

### When the data is not trusted (blackout)

The guard (`apex/engine/guard.py`, 129 lines) starts every session in blackout and returns to it when any of these holds: the feed is not live; no quote on any instrument for 3 s; the futures quote is over 10 s old; the engine itself stood still over 10 s; the future moved over 1 % inside 2 s. It lifts after 20 s of clean data.

During a blackout no book may enter. Older books hold their price exits while data is frozen. Champion-family books still decide exits on carried prices; the fill waits at most 10 s, then takes the last price and is tagged stale. A separate check distrusts the index when it sits over 80 points off its usual gap to the future.

### The engine's account of its own time

Each step is timed by phase and by book. A step over 1 s is logged at once with its largest parts. Measured live medians: 31 ms on 11 Nov, 42 ms on 12 Nov, 72 ms on 13 Nov, when 5,038 steps took over 300 ms and 21 over 1 s. In a replay with 120 books the median was 16.6 ms.

### End of day

From 15:41 the engine saves the books, writes the champion's trades, updates the day's levels, records every book's trades, and runs the nightly learning step in the same process (section 12).

### Points a survey on 15 Nov flagged here (confirmed by a second read unless noted; fixed ones say so)

- Fixed on 15 Nov: greeks were computed from the raw index price, so an index print the guard had rejected could become the forward's reference. The reference is now the trusted index, else the future.
- `start_day` marked the day as started before a check that can refuse to run, so the next step could carry on without the ledger. Fixed on 15 Nov: a failed start is dropped and retried every 30 s, and nothing trades meanwhile.
- `end_day` marked the day as done before its work. Fixed on 15 Nov: done only after the day's record is on disk, with up to 5 retries.
- With no futures and no index price, the step returns before any exit is checked, time exits included. Since 15 Nov this is said once a minute, and champion-family positions still run their premium stop, hold clock and forced flat on the option's own quote (docs/64). Older books still wait for data.
- The option's expiry is taken as 15:30 for greeks; `config.py` says derivatives close at 15:40.
- Engine and fill code hold 50 `except` handlers, 41 of them broad. A spot-guard error counts as "trusted".

## 6. Paper trading: fills, sizing and what survives a restart

Every result in this system is gross: a paper fill is priced at the option's last traded price, with no spread, slippage or charges. That is the owner's choice of 17 Oct 2026, and it flatters every live and replay result. The bid and ask at each fill are recorded so a net view can be computed later.

The mechanics live in `apex/engine/paper.py` (2,060 lines).

| Step | Rule |
| --- | --- |
| Entry | A trigger stores a pending entry. It fills at the last traded price on the first update of that option's row after the trigger |
| Entry lapses | After 3.0 s with no update, on a blackout, or at 15:15. Changed on the night of 15 Nov: when the engine itself looks late, an option that has printed since the trigger still fills, at the price then on the screen, up to 10 s after the trigger, and the trade is tagged late\_entry (docs/64 section 6.6) |
| Price exit (stop, trail, floor) | The decision is committed, then fills on the first row update after it |
| Exit with no update | After 10 s it fills at the last price and the trade is tagged `stale_exit` |
| Time exit | Fills at once; tagged stale when the quote is over 5 s old |
| Size | lots = whole part of capital / (price x 65). Under one lot the entry is refused |
| Capital | Each book starts the day at Rs 1,00,000 and compounds its gross profit and loss within the day |
| Freeze quantity | 3,510 units an order at NSE. On paper it only yields a count of slices |

### What survives a restart inside the session

| Survives | Does not survive |
| --- | --- |
| Open positions with their trail, best price and pending exit | Pending entries |
| Closed trades and capital | The 60-second price ring, flow and heavyweight scales |
| Episodes already traded, last exit time | Greeks, volatility and open-interest histories |
| Regime and one-second histories, if under 30 minutes old | Each strategy's own state (range, impulse, pullback arm) |

Books are written to `data/paper/<day>.json` by a background thread: at once on a trade, and at most every 10 s when only a trail moved. An unreadable file is moved aside and fresh books start. The engine restarts in blackout, so at least 20 s pass without entries.

### Points the survey flagged here (confirmed by a second read unless noted; fixed ones say so)

- **"First print" means first row update.** A quote-only packet also updates the row. The fill price is the last traded price held then, which can be an older trade: 10 of 22 entries on the four live days. Buying at the ask and selling at the bid instead would have cost 0.40 % a trade, and the days become +54.2 %, +6.7 %, +3.2 %, -28.4 %. The rule is the owner's and stands; from 16 Nov the nightly record carries both prices.
- **The research simulator fills differently.** `apex/fastlab.py` buys at the ask and sells at the bid. The engine uses the last traded price for both. Numbers from the two are not on the same basis.
- **A reloaded book keeps the parameters saved in its file,** not those in `config.py`. A parameter changed at midday does not reach a book restored from disk.
- **The deferred-exit rule exists twice** in `paper.py`, and one tuple of setup keys is retyped in seven places.
- No test file names `try_fill_exit`, `synthetic_forward`, `compute_greeks` or the warm-restart routine (searched by name only).

## 7. The 122 books

Six books are live (the five pool books and the Conductor), 53 are shadows, 3 are controls, and 60 belong to older families that still trade on paper every session. All are registered in `apex/config.py` as `VARIANTS`; each is a dictionary of parameters laid over a base.

| Family | Books | What it trades on | Standing |
| --- | --- | --- | --- |
| c20 pool: c20\_9y, 9s, 9v, 9x, 9t | 5 | Breakout of the forward on expiry days, pullback after an impulse on normal days | Live pool |
| Conductor | 1 | Copies the first eligible pool trigger | Live account |
| c20 others: c20\_8x, 9e, 9h | 3 | The same core: the parent and two expiry floors | Shadow |
| Twins of c20\_9y: fx, fr, rx, tp, pgb, pm, st15 | 7 | c20\_9y's entries with one exit or veto changed | Shadow |
| Fades: fade20, fade60, fade60x, fade3x, orbfade | 5 | Buy against a stretched move or an opening-range break | Shadow |
| Thrust: thr\_sis, thr\_hw | 2 | A 60-second thrust of sister indices or heavyweights, on the session before expiry | Shadow |
| Shadow Conductors: sl, wp60, d1, fd, fo, xs | 6 | The same copying with another pool or a refusal rule | Shadow |
| Restricted books (`_r002` to `_r005`) | 13 | A representative book plus one frozen hand-written rule | Shadow |
| Second generation (gen2) | 9 | Flow absorption, impact relaxation, leadership transfer; 4 signals and 5 controls | Shadow |
| Third generation (gen3) | 4 | Cash-to-futures transmission, breadth recruitment; 2 signals and 2 controls | Shadow |
| Forecast books (pred) | 4 | The edge forecast by a frozen model; one momentum control | Shadow |
| Controls | 3 | futures\_only, random\_entry, premium\_momentum | Control |
| Domino grid | 18 | A 15-second futures impulse with heavyweight stocks moving together | Older family |
| t28 | 20 | An older champion plus one veto or exit each | Older family |
| spot | 10 | Index range break, 45-minute pullback, opening range | Older family |
| lvl\_trail | 6 | Level-aware entries with a hard stop, gain trail and re-entry | Older family |
| edge | 5 | Index entries with a gamma-against-theta gate | Older family |
| fade\_switch | 1 | A 10-point burst, followed or faded by the 15-minute range | Older family |

One more book, `RAW`, runs outside the registry as an ungated twin of c20\_9x.

### Points worth a reviewer's attention

- **Sixty older books still run.** They cost engine time every step and add 60 more comparisons to any search for a winner. Whether they still earn their place is an open question.
- **The book guide is out of date.** `docs/30_BOOK_GUIDE.md` covers 72 books as of 7 Nov; 51 of today's 122 came later.
- **Inherited parameters that never run.** Every council book is built as a copy of an older book's parameters plus a `council` key, so it carries stop and trail settings the engine never reads for it.
- **Vetoes do not carry over.** Fade, thrust and opening-range buys are built after the champion's own logic has run, so none of the champion's entry vetoes applies to them.
- **Five older books break the delta rule** (section 1): on normal days they may buy at |delta| 0.42 to 0.52.

## 8. The champion family (c20), rule by rule

The champion is one entry idea wrapped in five layers of exits and vetoes: 15 switchable parts, built up through eight classes. Its fourth layer, c20\_9x, was fitted on 7 days in October (19 to 28 Oct: 48 trades, 2 expiry days), by the project's own account in `docs/20`.

**The signal.** The put-call-parity forward (section 5), smoothed by a 5-second average. All books read one shared table of the day: one row a second from 09:15:00, up to 96 contracts of the nearest weekly expiry. Code: `apex/engine/council/`.

### Entry

|  | Expiry day | Normal day |
| --- | --- | --- |
| Trigger | The forward is beyond its high or low of the last 600 s and has moved at least 20 points in 150 s. Buy at once | A break of the 1,200-second range with at least 40 points in 1,200 s only arms the book. A 50 % retrace, then a 5-point turn back, buys |
| Arm dies | Not applicable | After 900 s, or if the retrace passes 75 % |
| Window | 09:16 to 14:40. Nothing can fire before 09:25 | 09:16 to 15:00. Nothing can arm before 09:35 |
| Strike | Within 3 strikes of the money, \|delta\| at least 0.52, scored toward \|delta\| 0.65 | Within 150 points of the money, \|delta\| at least 0.52, nearest to 0.52 |

### Exit, first rule to fire

| Rule | Expiry day | Normal day |
| --- | --- | --- |
| Premium stop | Bid at or under 85 % of entry | The same |
| Forward trail | The forward gives back 25 points from its best | 40 points, tightened to as little as 32 as the option's delta rises |
| Profit floor | Peak gain of 15 % locks the entry price. Peak of 60 % locks 70 % of the gain | Peak of 15 to 25 % locks the entry price. 25 to 50 % locks 45 to 70 % of the gain. Above 50 % keeps 70 % |
| Premium trail | Once the bid reaches 170 % of entry, the forward trail is off and the exit is 8 % under the peak bid | Not used |
| Clock | 900 s | 5,400 s |
| Forced flat | 15:00 | 15:20 |
| No forward for 5 s | Stop and clock still run. The trail becomes a trail on the premium | The same |

After an exit the book waits 60 s.

### Vetoes on a buy

| Veto | When | Rule |
| --- | --- | --- |
| Stale forward | Always | The forward unchanged or missing for 5 s |
| Sequence | After a losing exit, for an opposite-side buy within 900 s | Needs realised movement to cover time decay: 0.5 x gamma x realised variance / \|theta\| of at least 0.3125 |
| Volatility shock | Expiry days | The 300-second rise of at-the-money volatility exceeds 1.5 times its typical 300-second change since 09:20 |
| Rich volatility (c20\_9y only) | Always | At-the-money volatility more than 3.5 points above its median since 09:20 |
| Open-interest wall (c20\_9y only) | Normal days | The largest open-interest strike of the bought type, within 250 points, sits ahead and at most 25 points away |

### How the five pool books differ

All five share the entry, the strike picker and the exits above. Each adds one idea.

| Book | Adds | Same-tick priority |
| --- | --- | --- |
| c20\_9y | The rich-volatility and open-interest-wall vetoes | 1 |
| c20\_9s | Normal days: no pullback buy when the arming impulse is over 660 s old | 2 |
| c20\_9v | Normal days: two extra exits, one near round 50-point levels and one that keeps 60 % of a 15 % gain | 3 |
| c20\_9x | Nothing: the base | 4 |
| c20\_9t | A trail that arms at +8 % when realised movement no longer covers time decay; keeps 60 % of the peak gain | 5 |

The priority is each book's return per trade on the days it was discovered on, as `apex/rules/pool.json` says itself ("in-sample"). On expiry days c20\_9x, c20\_9s and c20\_9v run identical rules.

### From signal to order

The adapter (`apex/engine/council/__init__.py`) steps each strategy once a second. A buy is dropped in a blackout, with the kill switch on, with no last price, with a quote over 5 s old, or with |delta| under 0.50. Otherwise it becomes a pending entry (section 6). While a fill is pending the strategy is not stepped.

### Points the survey flagged (confirmed by a second read unless noted; fixed ones say so)

- **Deep inheritance.** A pool book resolves through 6 to 8 classes; a fade book through 11. The instance edits its own parameter set during a call and restores it afterwards.
- **A veto may only pass the trade along.** The five pool books share one signal. When c20\_9y or c20\_9s refuses a buy, the next pool book may take it, so the Conductor still trades. One live case is on record: on 12 Nov at 11:12 the trade came from the third book.
- **Strategy state is not restored after a restart.** Only the peak bid and one small per-position record are saved.
- **A hard-coded path.** `c20_8x.py` reads `D:\ApexOptions\data\learning\day_levels.json` by absolute path; the fades' volatility line depends on it.
- **Dead and duplicated code.** An expected-value strike score is always overwritten. The pullback logic exists twice, the give-back exit twice, and one entry block in four files.
- **Research class against engine class.** The research ("kit") class precomputes the day's volatility series in decimals; the engine class builds it each second in percent. The kit and its sweep scripts are not in the repository.
- **Constants without stated evidence:** the thrust thresholds; c20\_9y's own docstring calls its evidence thin (eight vetoed buys).

## 9. The Conductor, its pool and its six shadow accounts

The Conductor is a copier. It owns no signal: it takes the first eligible trigger among its pool books and mirrors that book's contract, entry price and exit, with its own capital. Code: `apex/engine/conductor.py` (509 lines).

### One step of the live account

| State | What it does |
| --- | --- |
| Holding | Copies the owner book's marks. When the owner closes, it closes at the owner's exit price and reason |
| Owner pending | Waits for the owner's fill, then opens the same contract at the same price. A lapse, a rejection or an unaffordable premium frees the account at once |
| Flat | Takes the triggers fired on this step in priority order. The first eligible one becomes the owner. The rest are logged as lost on priority |

**The pool** is `apex/rules/pool.json`: five rows, all dated 9 Nov 2026, none with a rule attached. **Priority on the same tick** is standing, then each book's return per trade on its discovery days, then registration order. Every refusal is logged to `data/paper/conductor_<day>.jsonl`.

**If the owner's position vanishes** with no closed trade (a restart lost it), the account stays open, marked unresolved, and leaves only at a quote at most 5 s old. That exit is flagged as a recovery and left out of scoring.

**An offline twin** (`apex/conductor/account_sim.py`) rebuilds the account from saved trades. A test holds the two to the same trades.

### The six shadow accounts

Each is the same copier with its own capital and one changed rule. From 16 Nov the nightly report lists all seven side by side.

| Account | What differs |
| --- | --- |
| `conductor_sl` | Refuses a side when today's last 12 closed champion-family trades on that side number at least 3 and losses exceed wins |
| `conductor_wp60` | After its own last two trades both lost on opposite sides, refuses everything for 60 minutes |
| `conductor_d1` | The live pool plus the two thrust books |
| `conductor_fd` | The live pool plus fade20, fade60 and orbfade |
| `conductor_fo` | fade20 and fade60 only |
| `conductor_xs` | Normal days: the live pool. Expiry days: the pool if its last 6 expiry days summed at least as much as fade3x, otherwise fade3x alone |

### Points the survey flagged (confirmed by a second read unless noted; fixed ones say so)

- **The pool was not earned.** `docs/28` says only rules that pass the standard enter the pool. The five rows carry no rule and no pass is recorded. Their priority uses in-sample returns.
- **Engine and offline twin can drift.** A lapsed owner entry is invisible offline. "Unaffordable" is decided at the fill in the engine and at the trigger offline. Blackout and recovery exist only in the engine. Two different pattern classifiers exist.
- **A trigger is visible for one step only.** If that step faults, the fault is logged and the trigger is not retried.
- **An unreadable pool file used to read as an empty pool**. Fixed on 15 Nov: the configuration check reports it and the engine says so at the day's start.
- **Three policies are written twice** (side lock, whipsaw and the expiry switch, each in the engine and offline), and tests touch the whipsaw account only by name.
- **The account-level standard has no code.** `apex/conductor/score.py` implements the promotion standard for rules only.

## 10. Market observers, the weather photograph and the rule register

About 12,000 lines of the engine describe the market without trading it. The five pool books read none of it: they see only prices, the forward and option quotes. A few older and restricted books do.

### The observers

| Module | What it computes | Who reads it | Lines |
| --- | --- | --- | --- |
| `weather.py`, `weather4.py`, `weather5.py` | The weather photograph (below) and its per-second base | Recorded on every trade. Restricted books can veto on it | 2,243 |
| `domino.py` | Heavyweight stocks' 15-second moves in Nifty points, and how many move together | A decision input for the 18 domino books | 235 |
| `gex.py` | Dealer gamma map: flip level, walls, max pain | An advisor, the dashboard, the photograph | 164 |
| `flow.py` | Resting buyers and sellers per contract, every 100 ms | One older book's exit; an advisor; the dashboard | 225 |
| `regime.py` | A seven-state market label once a second | A standing gate for older books; an advisor | 191 |
| `apex/quant/` and `quantview.py` | Hidden-Markov regime, Hawkes flow, jump statistics, volatility smile, first-passage odds | Display and the photograph only. Tested as rules on 12 days and rejected | 1,019 |
| `straddle_watch.py` | A fixed-strike straddle and its change beyond time decay | One older book and one control | 390 |
| `ideas/` (i00 to i15) | Sixteen trade ideas, refreshed every 1 to 5 s | Display and a tape. Each is switched off after 5 faults or a 40 ms mean | 3,463 |
| `commentary.py` and three `cmt_` modules | Remarks, a verdict, an entry grade and an exit review on the open trade; 209 templates | Display and a tape | 3,898 |
| `voice.py` | A first-person card: what the lead pool book waits for and where it would sell | Display only | 531 |

### The weather photograph

At every entry trigger of every book the engine records 114 items (459 fields) about that instant: calendar, the day's shape, speed, the futures book, heavyweights, the option chain, volatility, regime, other books, feed health. It is saved with the trade. Up to four timed snapshots follow while the position is held, and one more at the exit.

Its purpose is to let later research ask which conditions separate winners from losers without re-running the day. A leak test checks that the base at time T is identical whether history stops at T or runs on 300 s. The test does not cover fields copied in from other engine state.

### The rule register and restricted books

A rule is a frozen entry condition with an id (R-001 to R-020), a freeze date and a first test day. The register (`apex/rules/register.json`) is add-only: a change is a new id. A restricted book is a normal book cloned with one rule attached and named `<book>_r00N`; 13 exist. It trades beside its free twin so the rule can be scored on test days only.

Scoring (`apex/conductor/score.py`) compares restricted against free in two windows, each closing only when both 30 restricted trades and 15 trading days are reached, against a luck margin from 2,000 random draws. **No rule has a recorded pass or fail yet**, and nothing runs the scorer automatically.

### Points the survey flagged (confirmed by a second read unless noted; fixed ones say so)

- **"Record only" is not quite true.** Two module docstrings say no book reads the photograph. Restricted books veto on it, and any field can become a gate through a new register row with no code change.
- **One field depends on book order.** `agree_same` (the factor of rules R-019 and R-020) counts books that fired earlier in the same step.
- **Two rules are never scored.** The scorer skips R-019 and R-020, and their hash is not pinned.
- **Display work sits inside the trading step.** The voice card reads live strategy objects; commentary appends to a file; the ideas board is handed the whole engine object.
- **Silent failures.** A failed photograph becomes an empty one. Lost log lines are not reported.

## 11. Forecasting: the prediction service and the Forecast Lab

Two forecasters exist and neither touches the live account. By the project's own measurements they predict how fast a premium will move far better than which way, and the direction skill is close to none by five minutes.

|  | Prediction service | Forecast Lab |
| --- | --- | --- |
| Where | Inside the engine: `apex/predict/`, `apex/engine/pred.py` | Its own process, started by hand: `apex/forecast_lab/` (`core.py` is 2,832 lines) |
| Predicts | For one option contract: which comes first on the bid within 30, 60, 180 and 300 s, +5 %, -5 % or neither | The Nifty future's change over 1 to 30 minutes as a range; an option's premium by simulation of 600 paths |
| Inputs | 33 one-second features: 24 of the market, 9 of the contract | 45 trained inputs, five online experts and two trained ones mixed by recent accuracy |
| Model | A competing-risk model fitted offline. A registry gives each session only a model trained before it | Recursive least squares, ridge, boosted trees; ranges by adaptive conformal calibration |
| Training data | 16 sessions, through 11 Nov. Nothing refits it nightly | 16 sessions, through 11 Nov, plus online learning kept in a state file |
| Scores itself | Every 15 s to a ledger; outcomes matched later | At each horizon's end: range coverage, error against "no move", direction |
| Isolation | Runs in the engine step | Copies the shared table each second and posts a panel to the gateway. No engine module imports it |

### Which decisions read a forecast

Six shadow books and one control. None is in the pool; the Conductor reads no forecast; no book reads the Lab.

| Book | How it uses the forecast |
| --- | --- |
| `p02_clock`, `p02_top1`, `p05_adaptive` | Enter when the 300-second edge reaches a high percentile of the model's own training rows |
| `p02_ctl_mom` | Control: enters on 30-second momentum |
| `fx_c20_9y` | After a 5 % gain, sells when the edge falls below a line |
| `fr_c20_9y` | Holds through the strategy's sell while the edge stays high |
| `rx_c20_9y` | Buys a contract back after an exit when a re-entry model expects over +2 % |

### Measured accuracy, from the project's own documents

| Measure | Result | Source |
| --- | --- | --- |
| Speed: "+5 % within 30 s" | AUC 0.851 on 10 unseen days | `docs/41` |
| Speed at 300 s | AUC 0.607 | `docs/41` |
| Side, given a move | AUC 0.533; on the live day 11 Nov, 0.443 | `docs/41`, `docs/50` |
| Against an activity-only baseline | Not better on log loss (0.9704 against 0.9694) | `docs/45` |
| On the champion's own entries | AUC 0.39 on 64 entries: winners are not told from losers | `docs/41` |
| Lab's 80 % range, 9 Nov | Caught 80.5 % at 1 minute, 95.4 % at 30 minutes | `docs/48` |
| Lab's central forecast | 0.4 to 2.3 % worse than "no move" | `docs/48` |
| The stand (BULLISH, BEARISH, SIDEWAYS) | Right 49.9 % at 15 minutes; the banner says so | `core.py` |

No document scores the forecast books forward after 11 Nov.

### Points the survey flagged (confirmed by a second read unless noted; fixed ones say so)

- **Lines fitted on the data they judge.** Entry and exit lines are percentiles of each model's own training rows. One range model is loaded by fixed path with no date check.
- **A display claim stronger than the record.** The Lab shows a past lean as "right about 60 % of the time" from hard-coded constants that nothing recomputes (the figure shown is 55 to 67 % by horizon); `docs/50` attributes that skill to a feed timing effect.
- **Constants with no stated source:** the stand's 0.65 and 0.35 weights and its 40, 20 and 90 thresholds.
- **The nightly retrain is broken.** `research/nightly_all.py` last ran on 13 Nov and failed; four of its step scripts are missing.
- **The Lab's read is read-only by code,** not by the operating system: it opens the shared table without a read-only flag.

## 12. Nightly learning and the promotion standard

Every evening the system scores every book, but it decides nothing: since `LEARN_DECIDE = False`, each promotion it would make is undone and listed as "would have". The champion is whatever the owner declared in `config.CHAMPION_OWNER`.

**What is recorded.** At the close the engine writes one row per book per day to `data/learning/days.jsonl`, with every trade's return, prices, contract, times, exit reason and flags. The file holds 1,131 rows: 107 book names over 20 days. `state.json` keeps the champion, the scoreboard, streaks and a log. `report.md` is the evening report. Code: `apex/engine/learning.py` (968 lines).

### The champion's scoreboard

A sequential test on the sum of the champion's trade returns since it took over.

| Parameter | Value |
| --- | --- |
| Hypothesis to prove | Mean trade return of at least +2.5 % |
| Assumed spread of a trade return | 30 % (an assumption, not measured) |
| Error rates | 5 % false GO, 20 % false KILL |
| GO line | Sum of returns at least 998.1 + 1.25 x trades |
| KILL line | Sum at most -560.9 + 1.25 x trades |
| No verdict before | 30 trades |
| Forced verdict | Undecided at 200 trades counts as KILL |

### How a challenger would be promoted

A challenger's daily growth is compared with the champion's on common days. It needs 10 days, a positive mean, every leave-one-day-out mean positive, and a one-sided t at 5 % shared across all challengers. With 118 challengers that is a t of about 4.9 at 10 days. Two passing evenings in a row would promote it.

### The promotion standard for rules and for the Conductor (`docs/28`)

All of these must pass, on test days only, against a comparator.

| # | Test | Passes when |
| --- | --- | --- |
| 1 | Wins more often | Its share of winning trades beats the comparator's by the luck margin |
| 2 | Makes more | Its return beats the comparator's by the luck margin |
| 3 | Makes money at all | Its own return is positive, also without its best trade and without its best day |
| 4 | Not one win | Still ahead without its best trade and without its best day |
| 5 | Keeps the big wins | Takes at least two-thirds of the comparator's top 10 % of trades |
| 5b | No worse on bad days | Its worst test day is no worse than the comparator's |
| 6 | Trades enough | At least as many trades a day as the live system (account level only) |
| 7 | Holds over time | Passes in a first window and again in a second of the same length |

Nothing has passed it, and only the rule-level version has code.

### Points the survey flagged (confirmed by a second read unless noted; fixed ones say so)

- **One flag holds three automatic paths off.** Challenger promotion, replacement after a KILL, and gate promotion all exist. The engine takes its champion from `state.json` each morning. Only `LEARN_DECIDE` keeps them from acting.
- **The replacement after a KILL has no test.** It is the book with the largest total over all recorded days.
- **The forced KILL may come too early.** By the surveyor's arithmetic the test needs about 550 trades on average to prove a true +2.5 % edge; the cut-off is 200.
- **A two-evening streak cannot show in record-only mode,** because streaks are restored every night.
- **Two definitions of a day's result.** The learning step compounds trade returns (9 Nov: +65.0 %). The account in rupees earned +59.7 %, because whole lots leave cash idle. Comparisons between books use the first.
- **A read error is treated as an empty file.** For the switch's history and the day-levels file, a failed read leads to a rewrite from nothing.

## 13. The dashboard

The dashboard is a single local web page that shows what the engine publishes; it sends nothing back and can place no trade. The gateway (`apex/gateway.py`, 343 lines, FastAPI) serves it on `127.0.0.1:8780` only, with no login.

| What the owner sees | Source |
| --- | --- |
| Position, capital, the day's trades and an event tape | Engine state |
| "What I would do now": a first-person card on what the lead pool book waits for, what it would buy, where it would sell | `apex/engine/voice.py` |
| The held trade with running commentary, an entry grade and an exit review | `apex/engine/commentary.py` |
| Forecast glance and the Forecast Lab panel with its stand (BULLISH, BEARISH, SIDEWAYS) | The two forecasters (section 11) |
| Trigger triangle, futures trace, hero contracts, open-interest map, heavyweights | Engine state and the tick stream |
| Ideas board and straddle watch | Observers (section 10) |
| Parallel books: all 122 side by side | Engine state |

The page (`apex/static/`: 2,062 lines of `app.js`, 1,763 of CSS) gets its data from two websockets, one for changed quote rows and one for the state every 0.5 s, plus a one-second poll of the Lab's panel.

### Points the survey flagged (confirmed by a second read unless noted; fixed ones say so)

- **One write path into the gateway.** `POST /api/lab/{name}` accepts up to 4 MB from any local process, with no origin check. The page then writes Lab-derived HTML with `innerHTML`; the escaping was not audited.
- **The page loads fonts from the internet** (Google Fonts), the only outside call a display makes.
- **FastAPI's default `/docs` page is not switched off.**
- **Display text has been wrong before.** On 15 Nov the voice card could call a two-minute-old price "now", and the stand could stay BULLISH on a stale quote. Both are fixed; the lesson is that display code needs the same staleness rules as trading code.

## 14. Research tools and data

Research runs on four harnesses that price a trade in four different ways. Reconciling them is unfinished work, and most of the research code has no tests.

| Tool | What it does | How it prices a trade | Speed |
| --- | --- | --- | --- |
| Engine replay (`apex/feed_replay.py`, `apex/replay_batch.py`) | Plays a recorded tick tape through the live parser and the real engine, one step per 0.1 s of tape | As live: last traded price on the first update after the trigger | Hours for a set of days |
| `apex/fastlab.py` | Loads a recorded session onto a 1-second grid. Scores a list of entries with a vectorised copy of the champion's exits, or steps a real strategy class | Buys at the ask and sells at the bid, one second later | 18 sessions in about 84 s |
| Four-year lab (`lab1.py`, `h4.py`) | Walks the exit ladder on 1-minute bars over 984 sessions | Real option bars where they exist; elsewhere a model option | Minutes |
| Search harness (`arena.py`, then `arena_fixed.py`) | Scores an entry generator on 1-second futures with option volatility from real 1-minute bars, over four dated splits | Model price from the last completed minute's volatility | Minutes per idea |

The last two and their scripts (`s20` to `s54`) live under `data/research/14nov/work/`, with the code tracked in git and the data not.

### Data

| Dataset | Holds | Period |
| --- | --- | --- |
| `data/ticks` | Raw feed tapes as recorded live | 21 dates, 17 Oct to 13 Nov 2026 |
| `data/research/ds_v2` | The tapes on a 1-second grid: futures, option chain, heavyweights | 18 sessions, 4 of them expiry days |
| One-minute history | Nifty futures and index for 984 sessions; option bars for 145 sessions | 15 Nov 2022 to 13 Nov 2026; options 14 Nov 2024 to 18 Jun 2025 |
| `data/research/hist1s` | One-second futures history from the broker | 474 sessions, 14 Nov 2024 to 6 Nov 2026 (245 of them the holdout year) |
| `data/research/hist_wx` | Heavyweights, sister futures and an option chain with open interest, by the minute | 246 sessions |
| `data/learning/days.jsonl` | Every book's trades, live and replayed | 20 days |

The one-minute history belongs to the owner's other project and is read from there, read-only.

### Points a reviewer should press on

- **Four price bases.** Live paper uses the last traded price, fastlab the bid and ask, the labs model prices. A result from one is not comparable with a result from another, and nobody has measured the gap between them.
- **A correlation was taken as validation.** `docs/57` reported 0.999 between fastlab's exits and the engine's. The same ladder matched the real class on only 37 of 50 normal-day trades until 15 Nov.
- **The recorded set is 18 sessions.** Anything fitted on it, including the champion's fourth layer, was fitted on days that later tests show to be the pattern's best quarter.
- **Research scripts are untested and partly absent.** The original research class ("kit") and its sweep scripts, cited in docstrings, are not in the repository.

## 15. Tests and quality controls

The suite has 761 test functions in 86 test files and passes in full: 759 passed, 8 skipped, 4 expected failures, 0 failed on 15 Nov. There is no continuous integration, no linter configuration and no type checking; tests run by hand.

| Control | What it does | Limit |
| --- | --- | --- |
| Unit and rig tests (`tests/`) | Each new book, account, exit rule and fix has a test, usually on a synthetic day driven through the real strategy class | Synthetic paths prove the rule fires as written, not that the rule is right |
| Data fence (`tests/conftest.py`) | Points every data path at a throw-away folder and fails the run if a test touches live data | Written after a test run on 2 Nov deleted the learning record. Scripts run outside pytest have no fence |
| Page tests (`tests/js/`) | Three node scripts render the dashboard cards from saved payloads | No browser test of the whole dashboard |
| Engine against offline simulator | `tests/test_conductor.py` checks the live account in the engine against `apex/conductor/account_sim.py`, trade for trade | Covers the live policy. The six shadow policies were first tied together on 15 Nov |
| Simulator against real class | The fast exit ladder reproduces 107 of 107 trades of the real strategy class on 18 recorded days | Checked on 15 Nov after four simulator faults were fixed |
| Config self-check (`config.validate()`) | Reports a mistyped parameter, a bad pool entry or paper-only switched off | Until 15 Nov it ran only in the optional preflight command. It now runs at every live start and stops it on a problem, and it reports an unreadable pool file |
| Step-time accounting | The engine times each phase of each step and logs any step over 1 second with its largest parts | Tells what was slow, after the fact |

Gaps a reviewer may want to press on:

- One timing test (`test_ops_10nov.py`, the slow-tick test) fails when the machine is busy. It failed the same way on the commit before the 15 Nov fixes.
- No test replays a full recorded session through the engine. That is done by hand with the replay tool, which takes hours.
- Line endings are mixed across files (LF and CRLF), with git set to convert them.
- The research scripts under `data/research/` have no tests. The wrong time-decay unit found on 15 Nov had reached three of them unnoticed.

## 16. Operations: a trading day

The whole system runs on one Windows PC, started by hand each morning through one script, `run_apex.py`. It depends on a broker session token that the owner pastes in daily.

1. **Token.** `run_apex.py session` opens the broker's login page; the owner pastes the day's token, which is stored in a local credentials file.
2. **Preflight.** `run_apex.py preflight` validates the configuration and the pool entries and tests the paper-only checks. It is optional. Since 15 Nov the configuration check itself also runs at every live start.
3. **Start.** `run_apex.py live` warns about other heavy jobs, creates the shared memory and starts the feed, the engine and the gateway. The Forecast Lab is started separately by hand.
4. **Session.** The engine starts in blackout and trades on paper from the first clean 20 s of data. The supervisor checks the processes every second.
5. **Kill switch.** A file named `data/KILL` stops all new entries within half a second. Open positions keep their exits.
6. **Stop.** Ctrl+C asks the feed to stop (12 s), then gives the engine up to 180 s to save the books and close the day.
7. **Close.** From 15:41 the engine records every book's trades and writes the evening report (section 12).

### What the supervisor does when something breaks

| Event | Response |
| --- | --- |
| Engine process dies | Restarted at once. Books are on disk; strategy state is not (section 6) |
| Feed process dies | Restarted after a growing wait, up to 60 s |
| Broker refuses the token | The feed exits; the supervisor waits for the credentials file to change, then restarts it |
| Websocket silent for 30 s in market hours | The feed reconnects; the dashboard shows RECONNECTING; the engine is in blackout |
| A heartbeat older than 10 s | A warning once a minute. Since 15 Nov, after 120 s the engine is stopped and restarted |
| Gateway dies | Restarted at once |

### Hazards met in the last two weeks

| Date | What happened | What was done |
| --- | --- | --- |
| 2 Nov | A test run deleted the learning record | Tests now run inside a fenced copy of the data |
| 9 Nov | The engine froze for seconds while saving | Saves moved to a background thread; step time logged by phase |
| 10 Nov | Other jobs on the PC made the engine 3 to 4 times slower | The supervisor warns at start; no hard guard |
| 12 Nov | The books file was rewritten about 4,700 times in a day and file swaps failed under antivirus locks | Saves throttled to one per 10 s; one retrying file-swap helper |
| 13 Nov | Median step time 72 ms, 20 % of steps dropped, 21 steps over a second. Research jobs ran on the same PC in market hours | Rule adopted: keep the machine quiet in market hours. One slow old book removed. The afternoon slowdown of 12 Nov is still unexplained |

### Points the survey flagged (confirmed by a second read unless noted; fixed ones say so)

- **A frozen engine was never restarted.** Fixed on 15 Nov. The supervisor only warned on a stale heartbeat; an engine with no heartbeat for 120 s in market hours is now stopped and restarted from the books on disk.
- **The engine restart had no delay.** Fixed on 15 Nov: restarts inside ten minutes now wait 0, 5, 10 and up to 60 s.
- **The warning about other heavy jobs could never show.** Fixed on 15 Nov: it now asks PowerShell and says when it cannot look. It used to shell out to a Windows tool that was not on the path, and treated any failure as "nothing running".
- **Logs are appended with no rotation.**
- **Token handling is casual.** The token is typed with visible input and the credentials file is written in place rather than through the safe file-swap helper.
- **One machine, one person.** There is no second machine, no alert to a phone, and no check that the nightly jobs ran: the Lab's nightly last failed on 13 Nov.

## 17. Evidence: does it make money?

No test shows a durable edge. The champion's pattern broke even over four years, and the weeks the system was recorded in are that pattern's best quarter of 17.

Sums below add daily results, each in % of one day's capital.

| Test | Data and period | Result | The documents' own caveat |
| --- | --- | --- | --- |
| Live paper record | The Conductor, 4 sessions, 9 to 13 Nov 2026 | +59.7 %, +7.4 %, +3.7 %, -27.1 %. 22 trades, 9 winners | "Four sessions cannot judge anything." Gross of all costs |
| 17-day engine replay (`docs/54`) | Recorded tapes, 19 Oct to 12 Nov 2026 | 119 trades, 53 % winners, +Rs 10.9 lakh | In sample before 9 Nov. Two days, 26 and 27 Oct, gave 73 % of the profit |
| Four-year test (`docs/58`) | 1-minute Nifty futures, 984 sessions, 15 Nov 2022 to 13 Nov 2026. Real option bars for 145 sessions, a model option elsewhere. Normal days only | Recorded window: 75 trades, 49 % winners, +5.7 % a trade. The four years before: 2,214 trades, 33 %, -0.01 %. On real option bars: 385 trades, 28 %, -0.6 %. None of 216 exit sets changes this | A 1-minute relative of the champion, not the champion itself |
| Year of seconds (`docs/58`, `docs/59`) | 1-second futures, 229 sessions, 14 Nov 2025 to 6 Nov 2026. Real strategy classes on a model option chain; 48 expiry sessions repriced on real option seconds | Normal days before the window: 393 trades, 38 % winners, +0.65 % a trade, negative without its five best trades. Expiry days: 639 trades, 31 %, -0.62 % | No open interest and flat volatility, so two vetoes cannot fire. Expiry figures used the wrong time-decay unit and are on hold |
| Search by 84 agents (`docs/60`) | Found on 7 May to 16 Oct 2026. Judged on 14 Nov 2025 to 6 May 2026. Holdout 14 Nov 2024 to 13 Nov 2025, opened once | 4,217 variants. Two finalists; both lost on the holdout (-178 and -164). No candidate passed | With 4,217 tries, noise alone is expected to reach t near 3.6 |
| Expiry-style switch (`docs/60` section 7) | 83 expiry days with real option volatility | +1,186 against -634 for the champion. t 4.23 on the daily difference | Chosen after the search, not before. Loses on the judged period. Now a shadow |
| Session before expiry (`docs/57`) | 71 sessions of 5-minute bars, 3 Aug to 13 Nov 2026 | Momentum continued on 15 of 15 such sessions, t 4.6 | Absent from Jan to Jul 2026 (t 0.1) and over four years (t 0.7) |

### The bar set before the search

A candidate had to pass six tests: positive on the found and the judged periods; positive on the holdout year; raises the account when pooled with the champion; sign holds on real option volatility; the engine class reproduces at least 80 % of its entries; t of at least 2 on judged plus holdout.

### A look-ahead that was found and fixed

The first pricing harness (`arena.py`) moved each option's volatility toward the current minute's close, up to 59 s ahead. That flattered every idea by 0.22 % a trade on normal days and 1.35 % on expiry days. `arena_fixed.py` holds the last completed minute's value and is the scorer to trust.

### What the project now believes

| Standing | Claim |
| --- | --- |
| Established | The recorded window is the pattern's best quarter of 17; outside it the pattern breaks even or loses |
| Established | A blind buy with the champion's exits has no edge |
| Established | Expiry days decide the year |
| Established | With all capital on every trade, an edge under about +2 % a trade shrinks a compounding account |
| Lead | The expiry-style switch; fading a stretched move; continuation on the session before expiry |
| Refuted | Filters on the pullback (473 weather items), tighter exits, an 80-input model, heavyweight or sister-index lead as a trade |
| Refuted | Hawkes, hidden-Markov, first-passage, jump and Kalman rules; "confirm with the forecaster" |

### Figures on hold until rerun

Before 15 Nov the simulator fed the strategy classes time decay per calendar minute; the engine's unit is 3.84 times larger. Do not quote: the expiry rows of `docs/57`; the real-class expiry columns of the year-long runs in `docs/58`; the sums -579 and -331 in `docs/59`; the expiry column of the baseline in `docs/60` section 4; the +372 % of the fade3x check. The holdout verdict and the switch's history do not use that value.

### Where the evidence itself is weak (from a read of the documents on 15 Nov, unresolved)

- **The switch's gain is one column.** +1,259 of its +1,186 comes from the holdout year, where it simply matches the champion (+1,247).
- **The pre-registration has no earlier dated copy.** The bar entered git on 15 Nov together with the results, and is not in `research/preregistry.jsonl`.
- **The splits run backward.** "Found" is the latest period; "judged" and "holdout" are earlier.
- **The holdout is thin on expiry days.** The verdict scores 31 holdout expiry sessions, because minute option bars end in June 2025.
- **Harness and engine disagree and nobody reconciled them.** On the four expiry days of the recorded window the causal scorer gives the champion -82; the engine replay gives +21.8 %, +532.0 %, -36.3 %, +43.2 %.
- **One day carries much of the story.** 27 Oct 2026 alone is +532 %.
- **Documents disagree.** `docs/59` calls fades "what helps"; `docs/60`, written later, says no price-only family holds from year to year.

## 18. What changed from 5 to 15 Nov 2026

The source grew 85 % in eleven days, from 20,600 to 38,100 lines over 32 commits, and the tests more than doubled. The pool file last changed on 9 Nov, and the pool books' strategy files between 30 Oct and 7 Nov. Later commits were meant to add only shadows, measurement, display and fixes. After this brief was written, the same evening added four things, none of which changes a live entry: a seventh shadow account (conductor\_rt, which copies the rent-trail book first; 123 books at that point), a shadow twin of c20\_9y whose entry waits up to 10 s for a print on an expiry day (lw\_c20\_9y; 124 books), a nightly count of where the account's day went and what became of each trigger, and exits that still run when the futures and index prices are missing. They are recorded in docs/64. The same check found that the 9 Nov freeze cost the live account every entry after 11:57: 36 of its 48 chosen entries lapsed while the option had a fresh price, because the engine looked 3 to 7 s late. The four live days are three days and a morning. Later still the owner changed one live fill rule: an entry is no longer dropped because the engine itself looked late (docs/64 section 6.6). A speed check on a recorded tape found that the 124 books cost almost nothing on an ordinary step (median 7.9 ms against 7.7 ms for the 13 Nov code); the slow steps of 13 Nov came from other load on the machine (docs/64 section 6.5).

| Date | Change | Touches a live trade? |
| --- | --- | --- |
| 15 Nov (not yet committed) | Review by three readers; 18 defects fixed, then 8 more on the live path after the surveys for this brief (\`docs/61\` section 6). The research simulator used time decay in the wrong unit and bridged feed gaps. The voice card could call an old price "now". The Lab's stand survived a stale quote. Details in `docs/61_CODE_REVIEW_15NOV.md` | Only when the index print is rejected: the forward then uses the future |
| 15 Nov | Expiry-style switch as a shadow: book `fade3x` and account `conductor_xs`. On expiry days the account trades the pool or the fades, whichever did better over the last 6 expiry days | No |
| 14 to 15 Nov | Search by 84 agents over 4,217 entry variants. A look-ahead in the first pricing harness was found and fixed (`arena_fixed`). Nothing passed on the untouched year | No |
| 14 Nov | System report with evidence (`docs/59`). Scoreboard now counts the champion's first day. Shadow `fade60x`. One slow old book switched off (3.1 ms a step) | No |
| 14 Nov | Four-year test on 984 sessions and a year of per-second history (`docs/58`). Shadow books `fade20`, `fade60`, `orbfade`; shadow accounts `conductor_fd`, `conductor_fo` | No |
| 14 Nov | `apex/fastlab.py`, a simulator that replays a session in seconds. Shadows `thr_sis`, `thr_hw` (thrust on the session before expiry), `st15_c20_9y` (sell a non-mover at 15 minutes), `conductor_d1` | No |
| 13 Nov | Voice card ("What I would do now"). Forecast Lab stand banner. Exit twins `tp_`, `pgb_`, `pm_c20_9y`. Shadow accounts `conductor_sl`, `conductor_wp60`. Feed reconnect and refused-login handling | No |
| 13 Nov | Runtime fixes and speed-ups after slow steps on 12 Nov; books file saved at most every 10 s between trades | No (timing only) |
| 11 to 12 Nov | In-engine forecast service, second and third generation shadow books, Forecast Lab as its own process, audit repairs | Not meant to. The shared fill code grew by 521 lines |
| 9 Nov | **The pool applied: the five c20 books, unrestricted, and the Conductor declared champion.** Weather photograph grown to 104 items. Shadow rules R-019 and R-020 | **Yes** |
| 8 Nov | Weather photograph v3 (68 items). The Conductor's account. A 14-day replay with per-book cards. 871 candidate rules shuffle-tested | No |
| 7 Nov | Conductor design (`docs/28`): missed-signal recorder, weather photograph, rule register frozen at R-001 to R-018, restricted books, the seven-test promotion standard | No |
| 5 to 6 Nov | A quant display layer and engine speed-ups. Outside reviews of the quant layer and the reply to them. Event study of runners and duds. Catalogue of 68 pre-trade factor groups | No |

Four things a reviewer should weigh:

- **Pace.** Most of the code is under two weeks old and has run in few live sessions. Every book, account and card added since 13 Nov has its first live session on 16 Nov.
- **Uncommitted work.** The 15 Nov fixes sit in the working tree (25 files changed, plus 6 new). Make sure the code you review includes them.
- **Corrected figures.** Some research numbers written before 15 Nov used the wrong time-decay unit and were not rerun. Section 17 lists them.

* **Shared code moved under the live books.** Since 9 Nov the pool books' own files, the pool file, the data guard and the greeks are unchanged. But `apex/engine/paper.py` (fills, 521 lines longer) and the strategy adapter did change, to add twins and observers behind flags. So did the Conductor's own file, the engine's main loop, the feed and the config. Nobody has proved line by line that a pool book's path through them is the same as on 9 Nov.

## 19. Known weaknesses and open risks

The largest weakness is not in the code: the system trades a pattern that four years of data do not support. The rest are ranked by how much they could mislead a decision.

| # | Weakness | Why it matters | See |
| --- | --- | --- | --- |
| 1 | No proven edge | The live pattern made -0.01 % a trade over the four years before the recorded window | 17 |
| 2 | Every live and replay result is gross | Fills at the last traded price, no spread, no charges. On the four live days, buying at the ask and selling at the bid would have cost 0.40 % a trade | 6 |
| 3 | The live choices were declared, not earned | The champion was named by the owner. The pool's five rows have no recorded pass. Their priority uses in-sample returns | 9, 12 |
| 4 | Many tries on little data | 18 recorded sessions; 122 books; 871 candidate rules; 4,217 entry variants. Noise alone produces winners at this scale | 14, 17 |
| 5 | All capital on every trade, no loss limit | The worst live day was -27.1 %. Under this rule an edge below about +2 % a trade shrinks a compounding day | 1, 17 |
| 6 | The pool may be one book | Five books share one entry. A veto in one may only pass the trade to the next | 8 |
| 7 | Four price bases | Live, fastlab and the two labs price a trade differently and have not been reconciled. On four expiry days the scorer and the engine disagree in sign | 14, 17 |
| 8 | The code is younger than its record | The source grew 85 % in eleven days. Everything added since 13 Nov has no live session yet | 18 |
| 9 | Shared code moved under the live books | The fill code grew by 521 lines after 9 Nov, and the Conductor, the engine loop and the feed changed too, with no line-by-line proof that the pool books' path is unchanged | 18 |
| 10 | About 65 flagged points, 8 fixed | A second read tested 59 of them and confirmed 54 in full and 5 in part. Eight on the live path were fixed on 15 Nov: the forward's reference, the day's start and close, the pool file, the start check, the hung engine, the restart loop, the heavy-jobs check. The rest are open | 4 to 16 |
| 11 | Display and observers run inside the trading step | A slow or faulty card costs trading time. Display text has twice stated stale data as current | 10, 13 |
| 12 | One thread, one file, one machine | A 2,419-line engine steps 122 books in a single Python thread on a shared PC. Step time more than doubled when other jobs ran | 5, 16 |
| 13 | Restart and hang handling | A restart loses each strategy's state. A hung engine is restarted after 120 s since 15 Nov, and that restart loses the same state | 6, 16 |
| 14 | Dormant automation | Three automatic promotion paths wait behind one flag. One of them picks a new champion with no test | 12 |
| 15 | Documents drift | Some figures are on hold, two documents disagree about fades, the book guide predates 51 books, comments state old timings | 7, 17 |
| 16 | One operator, manual start, daily token | No second machine, no remote alert, no check that nightly jobs ran | 16 |

### What is in good shape

- One parser serves live, simulated and replayed data, and the replay is locked step for step to the engine.
- Negative results are written down. The four-year test, the failed search and the look-ahead that was found are all in the documents.
- The rule register is add-only and dated, and restricted books trade beside free twins so a rule can be scored forward.
- Tests run inside a fenced copy of the data; the suite passes in full.
- The engine measures its own time by phase and by book.
- The paper-only block exists in code, not only in intent.

## 20. Questions for reviewers

These are the questions whose answers would change what is built next. Answer any; ignore the rest.

### On the evidence

1. Is there any reason to keep trading the pullback pattern, given four years at -0.01 % a trade? What result would justify stopping it?
2. The expiry-style switch shows t 4.23 on 83 days but was chosen after the search. What forward record, in days and trades, should it show before it replaces the live expiry rule?
3. With 4,217 variants tried on one data set, what is the right bar for the next idea? Is t near 3.6 enough, or should the search stop until new data exists?
4. The splits run backward in time (found on the latest months, judged on earlier ones). Does that weaken the holdout verdict, and how would you redo it?
5. Paper fills use the last traded price with no costs. What simple, defensible cost model should every result be restated on?

### On the design

6. All capital goes on every trade, by the owner's rule. Given that rule, what is the smallest edge and win rate that does not ruin a compounding day? Is the rule itself the main obstacle?
7. The Conductor copies the first trigger of five nearly identical books. Is the pool doing anything a single book would not? How would you test that?
8. 60 older books and about 12,000 lines of observers still run every step. Which would you delete first, and what would be lost?
9. The engine is one 2,419-line file stepping 122 books in one Python thread. Where would you cut it, and is its speed (a 72 ms median on 13 Nov) a real risk for a strategy that reads once a second?
10. Three automatic promotion paths are held off by one flag. Should they be removed, or finished and trusted?

### On correctness

11. Sections 4 to 16 list points flagged on 15 Nov; a second read confirmed nearly all, and eight were fixed. Of the rest, which matter most?
12. Where can the live engine and the research harnesses still disagree about the same trade? Sections 6 and 14 name four price bases.
13. What should be tested that is not? The exit fill, the forward, the greeks and the warm restart have no test by name.
14. The system has run 4 live sessions as the Conductor. What should be watched on the next 10, and what result should stop it?

### On process

15. The code grew 85 % in eleven days, most of it written by AI assistants at the owner's direction. What review routine would catch errors like the wrong time-decay unit sooner?
16. What would you want to see in this brief that is missing?

## 21. File map and glossary

The source is 127 Python files (38,111 lines): 126 under `apex/` and the supervisor at the root. All but one open with a docstring that says what the file is for and which decision created it.

| Where | Files | Lines | What it holds |
| --- | --- | --- | --- |
| `run_apex.py` | 1 | 868 | The supervisor and every command: live, sim, replay, session, preflight, learn |
| `apex/` (top level) | 19 | 7,830 | `engine_main.py` (the engine), `config.py` (all constants and the 122 books), feeds (`feed_breeze`, `feed_sim`, `feed_replay`, `feed_core`), `table.py` (shared memory), `gateway.py`, `greeks.py`, `fastlab.py`, replay drivers, `interlock.py`, `fsutil.py` |
| `apex/engine/` | 35 | 15,371 | `paper.py` (fills), `conductor.py`, `learning.py`, `guard.py`, the weather photograph, commentary, voice, second and third generation books, the in-engine forecast glue, levels, flow, regime, heavyweights |
| `apex/engine/council/` | 24 | 2,473 | The champion family, its twins, the fades, the thrust books, and the adapter that turns a strategy signal into a paper order |
| `apex/engine/ideas/` | 17 | 3,463 | Sixteen display-only trade ideas |
| `apex/forecast_lab/` | 6 | 4,559 | The separate forecasting process |
| `apex/predict/` | 9 | 1,078 | The in-engine prediction service and its model files |
| `apex/conductor/` | 9 | 1,666 | Offline tools for the live account: simulator, scorer, diary, rule search, pool builder |
| `apex/quant/` | 7 | 803 | Statistical models used for display only |
| `apex/rules/` | 3 |  | `pool.json`, `register.json`, `status.jsonl` |
| `apex/static/` | 5 | 4,385 | The dashboard page |
| `tests/` | 89 | 17,282 | Tests, fixtures and three page tests |
| `docs/` | 62 numbered |  | Design, decisions, reviews and results. Start with 28, 58, 59, 60, 61 |
| `data/research/14nov/work/` |  |  | Research harnesses and scripts (code tracked, data not) |

### Where to start reading

| To understand | Read |
| --- | --- |
| The live trade, end to end | `apex/engine/council/c20_08.py`, then `c20_9x.py`, `c20_9y.py`, the adapter in `council/__init__.py`, `apex/engine/conductor.py`, and the fill rules in `apex/engine/paper.py` |
| What can stop a trade | `apex/engine/guard.py` and the buy checks in the adapter |
| The evidence | `docs/58`, `docs/60`, then `data/research/14nov/work/arena_fixed.py` |
| The most recent review | `docs/61_CODE_REVIEW_15NOV.md` |
| The standard a change must meet | `docs/28_APEX_CONDUCTOR_PLAN.md`, section 2 |

### Glossary

| Term | Meaning here |
| --- | --- |
| Book | One rule set with its own paper account; also called a variant |
| Pool | The five books whose triggers the live account may copy |
| Conductor | The live account. It copies the first eligible pool trigger |
| Champion | The account the owner follows and the scoreboard tracks. Now the Conductor |
| Shadow | A book or account that trades on paper beside the live one and changes nothing |
| Twin | A shadow that differs from its parent in one rule |
| Control | A deliberately naive book kept as a baseline |
| Restricted book | A book with one frozen rule attached, named `_r00N` |
| Forward | The futures-equivalent price implied by option prices: strike + call - put |
| Normal day, expiry day | A day with at least one session left before the weekly expiry; the expiry day itself |
| Weather photograph | The 114 items recorded at every entry trigger |
| Blackout | The state in which the data is not trusted and no book may enter |
| All-in | All of a book's capital on every trade |
| Kit | The original research version of a strategy class; not in the repository |
| Found, judged, holdout | The three dated periods of the 14 Nov search; the holdout was opened once |
| Day sigma | One day's typical move: the last 20 daily returns' spread times the day's first forward |
