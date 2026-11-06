# The Apex books — how every book trades (7 Nov 2026)

A reference for the owner and stakeholders: for **every one of the 72 paper books** running today, exactly when it
enters, which option it buys, how long it holds, and when and why it exits. It was read from the source code at
commit `78be22f` (every key rule cites `file:line`) and checked against the live paper records of 19 Oct – 6 Nov.
**Changed since that commit (7 Nov, owner's decisions):** entries until **15:15** and flatten at **15:25** (the 19 Oct
test values 15:29 / 15:35 are retired); the council's own clock exit fills at once; straddle_spike and
premium_momentum respect |delta| ≥ 0.52; the filler books respect the 14:45 cut-off; a rejected fill no longer leaves
a stale direction. Where this guide quotes the old values, Part F says what changed.

**How to read the numbers.**

* "Live" figures are paper trades the engine actually made, from `data/paper/`.
* Books started on different days, so a book's history runs from **2 to 14 live days**. Totals are **not
  comparable** across books; strike rate and trades a day are more comparable, but still small samples.
* Times are IST. All books are buy-only Nifty weekly options, all-in, one position at a time per book, ₹1,00,000
  fresh each day.

## Contents

* Part 0 — The families at a glance
* Part A — What every book shares (the engine step, fills, time rules, capital, data gaps, kill switch, constants)
* Part B — The council books, and the current live system c20_9x
* Part C — The domino-impulse grid (m-grid, gap books) and the edge books
* Part D — The spot breakout, t28 and level-trail books
* Part E — The controls and the special books
* Part F — Things found while writing this guide (bugs, quirks, code vs intent)

---

## Part 0 — The families at a glance

| Family | Books | Trades a day | Strike rate | Median hold | Best book (live total ₹) | Worst book (live total ₹) |
|---|---:|---|---|---|---|---|
| Council (incl. the current live system c20_9x) | 8 | 2.0–5.2 | 42–75 % | 7.2–40.6 min | c20_9y +88,335 | c20_9t -19,419 |
| t28 pullback / retest | 20 | 3.4–19.4 | 42–58 % | 3.3–10.0 min | t28_ivfall +61,558 | t28_fwd -15,346 |
| Level trail | 6 | 4.5–4.8 | 47–56 % | 8.8–8.8 min | lvl_trail_rx_be +49,611 | lvl_trail +2,743 |
| Spot breakout / pullback / opening range | 10 | 1.3–42.8 | 37–86 % | 2.1–25.2 min | spot_ft_prem10 +223,889 | spot_pb45 -86,066 |
| Edge (spot entry + gates/brackets) | 5 | 2.4–5.6 | 33–58 % | 11.6–19.8 min | apex_edge +43,345 | edge_breakout -85,387 |
| Domino impulse grid (m-grid, gap) | 17 | 0.9–4.8 | 29–69 % | 0.4–2.3 min | m2.0_s0.5_trend +45,269 | m1.5_s0.5 -24,677 |
| Specials | 2 | 3.0–54.0 | 36–50 % | 1.3–1.7 min | fade_switch -7,816 | straddle_spike -25,044 |
| Controls (yardsticks) | 4 | 5.7–22.7 | 31–39 % | 1.3–2.7 min | RAW +51,886 | random_entry -160,885 |

*(Live paper results 19 Oct – 6 Nov; each family's books have 2–14 live days. The best council total, c20_9y, comes
from only 2 live days.)*

**In one line each:**

* **Council (8):** the current live system c20_9x and its research shadows. Two modes:
  * expiry day: buy the break of the forward's 10-min range with ≥ 20 pts of velocity over 150 s;
  * normal day: a 40-pt impulse, a 50–75 % pullback, then a 5-pt resumption.

  Exits: −15 % premium stop, a forward trail, premium floors, clocks.
* **t28 (20) and level trail (6):**
  * entry: spot pullbacks of a 45-min impulse on normal days, a retest breakout on expiry day;
  * exits: level booking, a −10 % premium hard stop, a smoothed gain trail and a lock;
  * each variant adds one veto or exit.
* **Spot (10):** spot breaks its 12-min range (bought at once or on the retest), pullback, or opening-range break.
  Mostly a 12-pt spot trail; some use premium brackets.
* **Edge (5):** spot entries with a "buyer edge" gate (is gamma worth its theta) and/or a premium bracket.
* **Domino grid (17):** buy when the futures impulse z-score and the heavyweight basket's synchrony both clear a
  threshold. 12-pt futures stop and trail, "thesis void" exit. Very short trades.
* **Specials (2):** straddle_spike (the gamma-leg idea) and fade_switch (a follow/fade switch with a ±12-pt bracket).
* **Controls (4):** yardsticks, not strategies:
  * RAW, the champion's entries without gates;
  * random_entry, random times with the same exits;
  * futures_only, futures-only triggers;
  * premium_momentum, raw premium momentum.

---

## Part A — What every book shares



This part was read from the code as it stands on 7 Nov 2026 (commit 78be22f). The files are `apex/engine_main.py`, `apex/engine/paper.py`, `apex/engine/guard.py`, `apex/engine/straddle_watch.py` and `apex/config.py`. "Line" means the line number in that file.

**Scope.** These are the common rules for every *non-council* paper book: the rules inside `paper.evaluate_entry` / `paper.check_exit`. Council books (`council=` in their parameters, e.g. `c20_9x`) skip this pipeline. They go to `apex/engine/council` instead (`engine_main.py:1220`). They share only the fill functions (`request_entry`/`try_fill_entry`, `request_exit`/`try_fill_exit`), `open_trade`/`close_trade` (all-in lots, capital), the kill switch and the blackout. **Today RAW is also a council book** (see Part 2).

### 1.1 How the books are created each day (`engine_main.start_day`, lines 264–322)

1. **The champion.** It is read from `data/learning/state.json` (`learning.load_state`). If that name is not a registered variant, or is a control book, the engine falls back to `config.CHAMPION_DEFAULT = "c20_9x"` (line 280–282).
   - `CHAMPION_OWNER = ("c20_9x", "2026-10-30")` forces the owner's pick into the state once.
   - Today state.json says `champion: c20_9x`, `gates: []`, `candidates: {}`.
2. **One book per entry in `config.VARIANTS`** (line 284). There are 71 today.
   - If today's `data/paper/<day>.json` already holds that book (a same-day restart), it is reloaded with its saved trades, position, capital, cool-down clock and **its saved parameters**. The book file's `p` wins over the current `config.py` until the next day (`Book.from_json`, paper.py:60–75).
   - Otherwise the book is new, with capital `START_CAPITAL = ₹1,00,000` (paper.py:43).
3. **RAW** (line 286): a new book named `RAW` that gets a copy of the champion's parameters. On the domino path `_entry` passes it no learning gates (line 1328–1329), and `base_gate` exempts it (paper.py:742).
4. **Gated candidate books** (line 288–290): for each *candidate* advisor in the learning state, a book `gate:<advisor>` (`learning.GATED_PREFIX = "gate:"`, learning.py:61). It is a copy of the champion that trades with the promoted gates plus that one candidate as a hard veto (line 1330–1331). **Today there are none** (`candidates: {}`).
5. **72 books in total today**: 71 variants plus RAW.
6. **What "gates" are.** A gate is one of the 13 advisors (`learning.ADVISORS`: iv_late, room, coherence, force, episode, book, premium, quiet, bank, event, gamma_leg, gex_room, regime).
   - Only the end-of-day learning loop can promote an advisor to a gate. It needs a screen on RAW's trades, then a gated book that beats the champion on PROMOTE_STREAK = 2 consecutive evenings.
   - A promoted gate vetoes the entry when that advisor says "veto" (paper.py:893–895).
   - Advisors are computed only while a domino episode exists (engine_main.py:572–573).
   - **Today the gate list is empty**, so learning gates block nothing.
   - The *standing* gate is separate: `base_gate`, the regime gate (see 1.3, step 10).
7. **When the day rolls.** Books are saved and learning runs (`end_day`, line 378) once the clock passes `MARKET_CLOSE + 1 min` = 15:41 (line 420), or when the date changes.

### 1.2 The engine step (100 ms) and the book order

- **Step length.** In live mode the loop runs one `tick()` and then sleeps `max(0.1/speed − work time, 0.005)` s (engine_main.py:1622). That gives one step about every **100 ms**, or longer when a step takes more than about 95 ms of work.
- **Replays** run one step per `REPLAY_STEP_S = 0.1` s of recorded time (lock-step, config.py:79–80).
- **Each step** builds one market snapshot `ctx`: prices, greeks, the guard state, the kill flag and so on (lines 535–559). It then calls `run_books(ctx)` (line 578).
- **If neither a futures price nor a spot price exists**, the step returns *before* `run_books` (line 529). In that case no exit and no entry is checked at all.
- **`run_books` (lines 1209–1263)** walks the books in dictionary order: config.VARIANTS order, then RAW, then the `gate:` books. For each book:
  1. A council book goes to the council adapter, and the walk moves on (line 1220–1228).
  2. **The exit check comes first**: `paper.check_exit(book, ctx)` (line 1231).
  3. **The entry comes second**: `self._entry(name, book, ctx)` (line 1244).
- **Faults are isolated.** An error in one book's exit check is logged at most once a minute, and *that book's entry is skipped for that step* (line 1232–1234). An error in its entry is logged, and the other books carry on (C-07).
- **Saving.** After every trade the books are saved to `data/paper/<day>.json`. A changed open-position state (a new best, an armed trail, a committed exit) is saved at most once a second.

### 1.3 One step for one book, in order (exit first, then entry)

#### A. Exit check — `paper.check_exit` (paper.py:1133–1273), only when the book holds a position

1. **Find the held contract's quote.** The lookup is by contract key, not row id (row ids can be renumbered on a feed restart) (lines 1140–1145).

2. **Data-gap freeze.**
   - `in_gap` = the guard is ON. The trade is then tagged `gap=True`.
   - `blackout` = the guard is ON **and** `exits_ok` is false (line 1152).
   - `exits_ok` is true once fresh futures quotes are arriving again during the 20-s resume phase. It is never true after an "implausible jump" bad print (guard.py:109–113, owner decision O-4).
   - During `blackout` the last option price, the peak, and the best futures price used for the trail are **not** updated (lines 1154–1159).

3. **The book's own price exit** (the book-family branch, lines 1163–1214).
   - For the domino books, the controls and straddle_spike, this is the **12-pt futures stop / trail**:
     - The trail arms once the best favourable futures move reaches `d_star = 12` pts.
     - The stop level is `entry futures − 12` before the trail arms, and `best − 12` after.
     - The exit fires when the futures *mid* touches that level: `STOP` or `TRAIL` (lines 1199–1204).
   - Every "futures" price in these exits is the Nifty-future bid/ask **mid** when the spread is ≤ `FUT_MID_MAX_SPREAD = 30` pts, else the last print (`_fx`, paper.py:799–803; D-109/D-110).
   - **THESIS-VOID** (lines 1206–1214): the opposite-side basket synchrony is ≥ `s_exit` (default = the book's `s_star`) **and** the futures z is ≤ −1 against the trade. Both must hold continuously for `THESIS_VOID_HOLD_S = 5` s.
   - fade_switch uses a bracket instead (Part 2).

4. **Clock exits**, checked only if nothing above fired (lines 1220–1235), in this order:
   - a book's own `dte0_max_hold_s` (expiry day)
   - a book's own `max_hold_s` (not fade_switch: its 180 s is inside the bracket)
   - a book's own `pb_flatten`
   - **`FLATTEN_AT = 15:35`** → `TIME (15:35 flatten)` for every book
   - **0DTE**: if the held contract expires today and the time is ≥ **`ZERO_DTE_FLATTEN = 15:00`**, exit with `TIME (0DTE 15:00)`. **Exception:** the held option's *current* |delta| is ≥ 0.9. If its delta is unknown, it is flattened.

5. **Frozen-data rule** (lines 1239–1249).
   - A *price* exit found during `blackout` is discarded for this step: "not a decision".
   - An exit already *committed* earlier (`pos["pending"]`) stays committed even if the price bounces back (line 1242–1244).
   - A price exit (not TIME) also waits while the futures quote is older than **`EXIT_FUT_STALE_S = 10` s**. There is no upper limit on this wait.

6. **Exit fill** (lines 1250–1264), `FILL_NEXT_PRINT = True`:
   - The exit is committed at the trigger time.
   - It fills on the **first update of the held option that arrives after the trigger** (quote age < time since the trigger).
   - If none arrives within **`EXIT_DEFER_MAX_S = 10` s**, it fills at the current LTP and is tagged `stale_exit`.
   - **TIME exits never wait.** They fill at once at the current LTP, and are tagged `stale_exit` if the quote is older than `EXIT_QUOTE_STALE_S = 5` s (line 1268–1269).
   - If there is no LTP at all, the price used is the last recorded price, else the entry price (tagged stale).
   - `EXIT_QUOTE_STALE_S` is **not** the freshness test for price exits while FILL_NEXT_PRINT is on. It is used for that tagging and by some premium exits.

7. **`close_trade`** (paper.py:1324–1356).
   - P&L pts = exit − entry. P&L ₹ = pts × quantity. ret % = (exit − entry)/entry × 100.
   - **`capital += P&L ₹`** (gross, compounding within the day).
   - The trade is appended to the book. `last_exit_s = now` **starts the cool-down**.
   - Bid/ask, quote age, futures at exit and the session phase are recorded.

#### B. Entry — `engine_main._entry` → `_entry_choice` → `paper.evaluate_entry` (engine_main.py:1293–1366; paper.py:813–898)

0. **A pending entry is completed first.** If the book has a pending entry, `try_fill_entry` handles it (step 14), and nothing new is evaluated that step (engine_main.py:1335–1340).

Then `evaluate_entry` runs its checks in this exact order. The first one that fails is the reason shown.

1. Bookkeeping side-effects only: premium_momentum re-arms its legs (`_momentum_rearm`), and data-gap tracking runs for books with `pb_gap_block_s`.
2. **In position** → no entry ("one position at a time", line 824).
3. **Entry pending** → no entry (line 826).
4. **Entry window.** No entry before **`SUPPRESS_UNTIL = 09:25`** or at/after **`LAST_ENTRY = 15:29`** (line 828).
   - 15:29 is marked "[TESTING — owner, 19 Oct]". The production value was 15:15 (config.py:93–98).
5. **Blackout.** No entry while the data guard is ON: `DATA GAP: …` (line 830–832).
6. **Cool-down.** No entry for `cooldown_s` seconds after this book's last exit (line 833–837). The default is **`REENTRY_COOLDOWN_S = 60` s**. A book can override it (fade_switch: 60; the spot books: 0).
7. **Daily brake** `_daily_brake` (paper.py:756–796):
   - **Kill switch** (all books, controls included): if the file `KILL_FILE = <DATA_DIR>/KILL` exists (live: `data/KILL`), the reason is "KILL switch: no new entries".
   - Control books stop here: they are exempt from everything below.
   - **Every other brake is OFF** (D-123, owner, 19 Oct): `DAILY_LOSS_STOP_PCT = 0.0`, `LOSS_STREAK_N = 0`, `LOSS_STREAK_PAUSE_S = 0`, `MAX_ENTRIES_PER_DAY = 0`, `EXPIRY_ENTRY_END = None`.
   - The only live part is a per-book `day_stop_pct` (20 % on apex_edge / edge_breakout). None of the books in Part 2 has one.
8. **Family entry rule.** The function hands off by flag, in this order: `spot_dc` → spot books, `fade_switch`, `spike`, `random`, `momentum`. Anything else uses the domino trigger (lines 841–898; Part 2).
9. (Domino path) the trigger itself: episode, z, 15-pt floor, synchrony, not late, IV cap (Part 2, futures_only).
10. **`base_gate`, the standing regime gate** (paper.py:738–753; D-112). It applies to **every book except the 3 controls and RAW**, and only where a family calls it: the domino path and straddle_spike. It returns no entry when:
    - there is no regime reading yet, or
    - the regime is one of `REGIME_BLOCK = WARMING, UNCERTAIN, RANGE, COMPRESSION, EXHAUSTION`, or
    - the regime is DIRECTIONAL/BREAKOUT the other way.
    - fade_switch, random_entry and premium_momentum never call it.
11. **Learning gates** (domino path, straddle_spike, premium_momentum): any promoted advisor that says veto blocks the entry. Today there are none.

Then `_entry_choice` (engine_main.py:1293–1324):

12. **Direction**: `entry_dir`. The spike leg for straddle_spike; the direction a control book set when it fired; otherwise the domino direction (paper.py:89–97).
13. **Contract**: `choose_contract` (paper.py:126–173):
    - **straddle_spike and premium_momentum** buy a leg of the anchored straddle (`spike_leg`, Part 2).
    - **Every other book here**:
      - CE if the direction is up, PE if down.
      - Only the **nearest weekly** (`week == 0`).
      - Only contracts with a known delta, an LTP between **`MIN_PREMIUM = 20` and `MAX_PREMIUM = 600`**, and a quote younger than **15 s**.
      - The |delta| band depends on calendar days to the weekly expiry:

        | Days to expiry | |delta| band |
        |---|---|
        | ≥ 3 days | **0.52–0.70** |
        | 1–2 days | **0.60–0.80** |
        | expiry day | **0.65–0.85** |

      - On expiry day the expiring weekly is still the one traded (`ZERO_DTE_USE_NEXTWEEK = False`, D-108). There are **no entries at/after `ZERO_DTE_NO_ENTRY = 14:45`**.
      - **Pick:** the in-band contract with the *smallest* |delta*. That is the strike nearest the money inside the band: ATM or one step ITM, since the lower edge is ≥ 0.52.
      - **Fallback:** if nothing is in the band, the smallest |delta| *above* the band (tagged `band_fallback`).
      - If no contract has |delta| ≥ the lower edge, the reason is "no CE/PE in delta band", and there is no trade.
      - `HERO_BAND = 2` (ATM ± 2) is **not** used to pick strikes. It only chooses the ten "hero" contracts for depth and the display.
      - `delta_target` (t28 books only) is not relevant here.
14. **Fill** (D-126, `FILL_NEXT_PRINT = True`):
    - `request_entry` records a pending entry: the time, the contract, the reason and the LTP on screen at the trigger (paper.py:1026–1034).
    - On later steps `try_fill_entry` (paper.py:1037–1068) **fills on the first update of that contract that arrives after the trigger**, at that update's LTP.
    - **The entry lapses (cancelled)** if, before a fill arrives, any of these happens:
      - the guard goes ON (data gap), or
      - more than **`ENTRY_FILL_MAX_S = 3.0` s** pass, or
      - the clock reaches LAST_ENTRY.
    - Nothing else is re-checked at fill time (not the kill switch, not the cool-down, not the price).
    - The trigger-to-fill delay (`fill_delay_s`) and the slippage against the trigger LTP (`fill_slip`) are recorded.
15. **`open_trade`** (paper.py:1071–1130) — **all-in**:
    - lots = floor(capital / (LTP × `LOT_SIZE` 65)) (line 1073). Quantity = lots × 65.
    - If lots < 1, there is no trade: "premium unaffordable".
    - Leftover cash simply stays in capital. There is no position sizing ever (owner's rule).
    - **Recorded:** contract, lots/qty, freeze slices (`FREEZE_QTY = 3510`, informational), entry LTP plus bid/ask, time, direction, futures mid at fill (this is the reference for the 12-pt stop), spot, delta, IV, reason, all advisors' verdicts, episode/fire id, regime, session phase, a signal snapshot (z, synchrony, 30-min trend, …) and the edge snapshot.
    - The episode / spike / fire id is added to `fired_episodes`, so the same setup is never traded twice.

### 1.4 Fill rules (summary)

- **Price.** Paper fills are at **LTP, gross**. Slippage and charges are ignored (owner, 17 Oct; `FILL_AT = "ltp"`). Bid/ask at entry and exit are stored for a later net view.
- **Entry.** It fills on the *first update arriving after the trigger*, never on the print already on screen (D-126). The entry waits ≤ 3 s, then lapses.
- **Price exit.** It fills on the first update after the trigger, waiting ≤ 10 s, then at the last price with a `stale_exit` tag. It waits indefinitely while the futures quote is > 10 s old or the engine is in a frozen blackout.
- **Clock (TIME) exit.** It fills immediately.

### 1.5 Time rules (IST)

| Time | Rule |
|---|---|
| 09:15 | market open (`MARKET_OPEN`) |
| before 09:25 | no entries (`SUPPRESS_UNTIL`: overnight repricing) |
| 14:45 | expiry day: no new entries (`ZERO_DTE_NO_ENTRY`) |
| 15:00 | expiry day: flat unless the held option's \|delta\| ≥ 0.9 (`ZERO_DTE_FLATTEN`) |
| 15:29 | last entry (`LAST_ENTRY`, CAS test; production 15:15). A pending fill also lapses here |
| 15:35 | every book flat (`FLATTEN_AT`, CAS test; production 15:25) |
| 15:40 | F&O close (`MARKET_CLOSE`); the day is closed and learned at 15:41 |

### 1.6 Capital and all-in

- **Every trading day starts each book at ₹1,00,000** (`START_CAPITAL`). This is a new `Book` object; only a same-day restart reloads the saved book.
- **Every entry spends the whole current capital** on as many 65-unit lots as it buys.
- **After every exit, capital = capital + gross P&L.** The next trade is sized on the new capital (compounding within the day).
- **Nothing carries over to the next day.**

### 1.7 Data-gap rules (`apex/engine/guard.py`, D-063 / D-097)

**The guard is ON (blackout) when any of these holds:**
- the feed state is not LIVE/SIM/REPLAY;
- **no instrument at all** has delivered a quote for `STALE_S = 3` s;
- the Nifty-future quote is older than `FUT_QUIET_S = 10` s (only during market hours);
- the engine's own step hole is > `ENGINE_PAUSE_S = 10` s;
- a futures move of > `JUMP_FRAC = 1 %` happens within `JUMP_WINDOW_S = 2` s (a bad print).

**Lifting.** The guard turns OFF only after `RESUME_S = 20` s of continuously fresh data. It starts ON at every engine start, so the first 20 s after any start are covered.

**While the guard is ON:**
- no new entries in any book;
- pending entries lapse;
- domino scales are not learned;
- an episode or straddle spike *born* in it is never tradeable;
- price exits wait (TIME exits still run). During the 20-s resume phase stops and trails *may* fire again (O-4), except after a bad print.

**After it lifts:** for `SETTLE_S = 300` s
- spikes born in that time are tainted;
- premium_momentum waits the whole 300 s;
- random_entry waits the first 60 s (it blocks while more than 240 s of settling remain).

### 1.8 Kill switch

- **Creating the file `KILL` in the data folder** (live: `D:\ApexOptions\data\KILL`; `APEX_DATA` moves it for sim/replay) **stops all new entries in every book**, controls and council books included. The reason shown is "KILL switch: no new entries (delete data/KILL to resume)".
- The file is checked at most every 0.5 s of wall time (engine_main.py:204–211), so entries stop within about half a second.
- **Exits keep running normally.**
- Deleting the file resumes entries.
- *Note:* an entry already pending at that moment can still fill within its 3-s window, because `try_fill_entry` does not re-check the kill flag.

### 2. Shared constants

| Name | Value | Meaning |
|---|---|---|
| START_CAPITAL | 100,000.0 | ₹ per book, fresh every trading day |
| LOT_SIZE | 65 | Nifty lot; lots = floor(capital/(LTP×65)) |
| FREEZE_QTY | 3510 | order slices (informational on paper) |
| STRIKE_STEP | 50 | strike gap |
| HERO_BAND | 2 | ATM±2 "hero" contracts (display/depth only, not strike choice) |
| WEEKLY_BAND / NEXTWEEK_BAND | 12 / 4 | strikes subscribed around ATM (weekly / next week) |
| FILL_AT | "ltp" | fills at last traded price, gross |
| FILL_NEXT_PRINT | True | fill on the first update after the trigger (D-126) |
| ENTRY_FILL_MAX_S | 3.0 s | an entry with no new print within this lapses |
| EXIT_QUOTE_STALE_S | 5.0 s | stale tag for TIME exits; freshness for some premium exits |
| EXIT_DEFER_MAX_S | 10.0 s | a price exit waits at most this for a new option print |
| EXIT_FUT_STALE_S | 10 s | price exits wait while the futures quote is older |
| SUPPRESS_UNTIL | 09:25 | first entry time |
| LAST_ENTRY | 15:29 | last entry time (CAS test; production 15:15) |
| FLATTEN_AT | 15:35 | all books flat (CAS test; production 15:25) |
| ZERO_DTE_NO_ENTRY | 14:45 | expiry-day entry cut-off |
| ZERO_DTE_FLATTEN | 15:00 | expiry-day flat, unless \|delta\| ≥ 0.9 |
| ZERO_DTE_USE_NEXTWEEK | False | expiry day trades the expiring weekly |
| MARKET_OPEN / MARKET_CLOSE | 09:15 / 15:40 | session |
| REENTRY_COOLDOWN_S | 60.0 s | default wait after an exit before the next entry |
| THESIS_VOID_HOLD_S | 5.0 s | synchrony flip must persist this long |
| MIN_IMPULSE_PTS | 15.0 pts | domino: the 15-s futures move must also be ≥ this |
| FUT_MID_MAX_SPREAD | 30.0 pts | futures price = mid unless the spread is wider |
| BASE_GATES / REGIME_BLOCK | ("regime",) / WARMING, UNCERTAIN, RANGE, COMPRESSION, EXHAUSTION | standing regime gate |
| DAILY_LOSS_STOP_PCT | 0.0 (OFF) | daily loss stop |
| LOSS_STREAK_N / LOSS_STREAK_PAUSE_S | 0 / 0 (OFF) | losing-streak stop |
| MAX_ENTRIES_PER_DAY | 0 (OFF) | entry cap |
| EXPIRY_ENTRY_END | None (OFF) | expiry-day entry end |
| KILL_FILE | data/KILL | kill switch file |
| DELTA_BANDS | ge3 0.52–0.70 · 1to2 0.60–0.80 · zero_am 0.65–0.85 · nextweek 0.52–0.65 (unused while USE_NEXTWEEK False) | \|delta\| bands |
| MIN_PREMIUM / MAX_PREMIUM | 20 / 600 | tradeable premium range |
| (choose_contract) quote age | < 15 s | contract quote must be younger |
| CHAMPION_DEFAULT | c20_9x | fallback champion |
| guard STALE_S / FUT_QUIET_S / RESUME_S / ENGINE_PAUSE_S | 3 / 10 / 20 / 10 s | blackout on / lift rules |
| guard JUMP_FRAC / JUMP_WINDOW_S / SETTLE_S | 1 % / 2 s / 300 s | bad print; post-gap settling |
| REPLAY_STEP_S | 0.1 s | engine step (live ≈ 100 ms) |
| TRIGGER m*/s*/L*/d* | 2.0 / 0.50 / 3.0 / 12.0 | domino defaults (z, synchrony, lateness ×σ15, stop pts) |
| IV_RISE_CAP | 1.5 vol pts | domino "not late" IV cap |
| ONSET_Z / EPISODE_END_Z / EPISODE_END_SEC | 1.0 / 0.5 / 30 s | episode start/end |
| RECRUIT_Z / ACTIVITY_MIN | 1.0 / 1.2 | a stock counts toward synchrony |
| SIGMA15_FLOOR | 5.0 pts | 15-s futures σ never below |
| RANDOM_ENTRIES_PER_DAY | 6.0 | random_entry Poisson mean |
| SPIKE_MIN_PTS / SPIKE_MIN_FRAC / SPIKE_SIGMA / SPIKE_SIGMA_SEED | 4.0 pts / 6 % / 2.5× / 1.5 pts | straddle spike threshold |
| SPIKE_COOLDOWN_S / SPIKE_ENTRY_MAX_AGE_S / SPIKE_MIN_DDELTA | 90 s / 150 s / 0.03 | spike spacing, entry age, delta rise |


---

## Part B — The council books, and the current live system c20_9x



Source of truth: `apex/engine/council/*.py`, `apex/engine/paper.py`, `apex/config.py`. Where the spec
(`docs/20_C20_9X_STRATEGY_SPEC.md`) and the code differ, the code is described and the difference is flagged.
All times IST. "Row i" = seconds since 09:15:00 that day; the clock used by the strategies is
`hm = 555 + i/60` minutes after midnight (`council/__init__.py:42`).

The eight council books (`config.py:381-388`): `c20_8x`, `c20_9x` (champion, `CHAMPION_DEFAULT`, `config.py:390`),
and shadows `c20_9t`, `c20_9v`, `c20_9e`, `c20_9h`, `c20_9s`, `c20_9y`. Each is registered as
`dict(_G, council="<name>")`: it inherits the full parameter set of the old `t28_gap` book (`lvl_book`,
`prem_hard_stop` 10, `spot_trail` 12, `reentry` …). **None of those t28 parameters is used by a council book** — the
engine sends council books to `_council()` and skips `check_exit` / `_entry_choice` entirely
(`engine_main.py:1220-1229`). The parameter JSON is identical for all eight books except the `council` name.

---

### 1. How a council book is run (the adapter)

`apex/engine/council/__init__.py` — class `Adapter`, called once per engine step; it acts at most once per second
(`step`, L135-141: row `i = int(now − 09:15:00)`, skipped if the same second was already handled).

#### 1.1 What the strategy sees (LiveDay, L32-110)
One shared table per day for all council books (`shared_day`, L116-125), written once per second by the first
council book to run (L142-143). Each row holds, for every contract of the **nearest weekly** expiry (`w0`, CE and PE,
up to 96 contracts, L28; contracts beyond 96 are ignored, L88-89):
bid, ask, ltp, mid, quote age, IV, delta, gamma, theta (per minute), vega, OI, traded qty, total buy/sell qty.
Plus Nifty spot, Nifty future and **the parity forward** (`eng.fwd`, put-call-parity forward of the nearest weekly).
- The forward is written only if the engine computed it ≤ 2.0 s ago (L75-76); otherwise the previous row's value is
  carried forward unchanged. Every field is forward-filled over seconds that were skipped (L66-72).
- Zero or negative bid/ask/ltp/mid are not written (the old value stays) (L103). Missing quote age → 9e9 ("stale").
- `D.dte0` = today is the weekly's expiry day (L38). This one flag selects **expiry mode** vs **normal mode**.
- `D.atm(i)` = listed strike nearest the forward (or spot if no forward) (L57-62).

#### 1.2 Order of work each second (L144-214)
1. **Track last / peak** for the dashboard (L148-153), not during a data blackout.
2. **Exit pending?** → only try to fill it (`paper.try_fill_exit`), strategy not stepped (L154-155).
3. **Entry pending?** → only try to fill it (`paper.try_fill_entry`), strategy not stepped (L156-160).
4. **Holding:** update the **peak bid** = max bid seen since entry (L166-172). It starts at the first bid seen after
   the fill (or the saved value after a restart; or the entry price if no bid) — it can therefore start *below*
   entry. It is saved on the position, so premium floors survive a restart.
5. **Forced flat** (L173-175): at **15:00 on expiry day, 15:20 on normal days** → exit reason
   `TIME (council forced flat)`. This is checked *before* the strategy runs, so it beats every other exit.
6. If the held contract has no column this second, the strategy is **not stepped** (no exits other than forced flat)
   and a warning is logged (L176-179).
7. **Step the strategy** (`on_second(i, D, pos)`, L185). It answers nothing, `("SELL", why)` or
   `("BUY", strike, CE/PE, why)`.
8. **SELL** → `paper.request_exit(book, ctx, "COUNCIL <why>")` (L193-196). So in the trade log every strategy exit is
   `COUNCIL <CODE>` (e.g. `COUNCIL FWD_TRAIL`); the only exit without the prefix is the forced flat.
9. **BUY** (only if flat) — the adapter adds its own checks (L197-205); the buy is dropped silently if:
   - data **blackout** is on, or the **kill file** (`data/KILL`, `config.py:74`) exists;
   - the contract has no quote, no LTP, or its quote is older than **5.0 s** (`EXIT_QUOTE_STALE_S`, `config.py:431`);
   - **|delta| < 0.5** (L204). The comment says the owner's rule is 0.52; the adapter tests 0.5, but every council
     strike picker already refuses |delta| < 0.52 (`c20_08.py:71`, `c20_9x.py:319`), so **0.52 is the effective rule**.
   Then, because `FILL_NEXT_PRINT = True` (`config.py:120`), `paper.request_entry` records a pending entry (L207-209).

#### 1.3 Fills (paper.py)
- **Entry** (`try_fill_entry`, `paper.py:1037-1068`): fills on the **first print of that contract that arrives after
  the signal** (quote age < time waited). It **lapses** (no trade, `entry lapsed: …`) if no such print within
  **3.0 s** (`ENTRY_FILL_MAX_S`, `config.py:121`), if a blackout starts, or if the clock is ≥ **15:29**
  (`LAST_ENTRY`, `config.py:96`). Price = that print's **LTP** (`FILL_AT = "ltp"`, gross, no costs; bid/ask at the
  fill are recorded alongside).
- **Size** (`open_trade`, `paper.py:1072-1076`): `lots = floor(capital ÷ (LTP × 65))`, qty = lots × 65 — all-in. If
  under one lot the entry is refused ("premium unaffordable"). Capital starts at ₹1,00,000 each day and compounds
  within the day (`close_trade` adds P&L, `paper.py:1330`).
- **Exit** (`request_exit` / `try_fill_exit`, `paper.py:1276-1321`): the exit is committed at the signal second and
  filled on the **first print after the signal** (and not during a blackout, unless the guard says "exits ok" — fresh
  futures quotes resuming, not a bad print, `guard.py:109-113`). If no fresh print within **10 s**
  (`EXIT_DEFER_MAX_S`, `config.py:432`) it fills at the last price, tagged `stale_exit`. Reasons starting with
  `TIME` fill **at once** — note this is only the forced flat (`TIME (council forced flat)`); the strategy's own
  clock exit is logged `COUNCIL TIME`, which does **not** start with "TIME", so it waits for a fresh print like any
  other exit (see Ambiguities).
- The strategy is not stepped while a fill is pending, but the shared table keeps being written, and c20_9x's
  "catch" fix rolls its smoothed forward through those skipped seconds (§2.2).
- While an exit is pending nothing else can happen; the strategy's cooldown clock starts at the **signal** second.

---

### 2. c20_9x — the current live system

Class chain (Python MRO): `c20_9x.LiveStrategy` → `_R9Mixin` (round-9) → `c20_8x.Strategy` (round-8) →
`c20_20.Strategy` (layers) → `c20_08.Strategy` (core). The adapter builds `c20_9x.Strategy()` = `LiveStrategy` with
`parts = FINAL_R9` (`c20_9x.py:69, 459-460, 515`).

#### 2.1 Which parts are switched on
`FINAL_R9 = ("exp","norm","seq","pex","pbg","d52") + ("l2","ffirst","seqcal","catch") + ("dtr","ramp","ivz","ptre","tie")`
(`c20_9x.py:57, 69`; `c20_8x.py:295`).

| Layer | Active in c20_9x | Present in the code but OFF |
|---|---|---|
| c20_08 core | breakout/velocity entry, pullback entry, picker, SL, TP (set to 9.9 = off), FWD_TRAIL, TIME, cooldown, entry windows | — |
| c20_20 (`c20_20.py`) | `exp`, `norm` (mode switches) | `oi`, `iv`, `gr`, `orb`, `cap`, `pm`. (c20_20's own default `("exp","norm","iv","orb")` at L30 is **replaced** by c20_8x's FINAL, so the IV guard and opening-range lock are not active.) |
| c20_8x (`c20_8x.py`) | `seq` (flip-after-loss gate), `pex` (premium floors), `pbg` (pullback geometry), `d52` (normal delta 0.52) | `exh`, `lvl`, `rw`, `th1`, `orbx` |
| c20_9x (`c20_9x.py`) | `l2`, `ffirst`, `seqcal`, `catch`, `dtr`, `ramp`, `ivz`, `ptre`, `tie` | `gbw`, `fy`, `uw`, `ptr` (both-mode premium trail), `rt` (rent trail — used by c20_9t) |

#### 2.2 Common machinery
- **Smoothed forward `fs`**: causal EMA of the parity forward, `fs = fs_prev + (1/5)·(F − fs_prev)`, tau = **5 s**
  (`c20_08.py:22, 92-94`). If the previous row has no `fs`, it restarts at the raw forward.
- **Catch-up bridge** (`catch`, `c20_9x.py:132-139`): if the strategy was not stepped for some seconds (fill pending),
  the EMA is rolled through those rows from the stored forward, so it does not restart at the raw forward.
- **Rolling range**: max and min of `fs` over the previous **W** seconds, *excluding* the current row
  (`c20_08.py:96-108`). Only rows on which the strategy was stepped enter this window.
- **Stale forward** (`l2`, `c20_9x.py:142-149`): if the forward is missing or exactly unchanged for **≥ 5**
  consecutive steps (`FS = 5`), it is "stale". (In live the table carries the last value when the engine's forward is
  > 2 s old, so a frozen forward shows as "unchanged".)
- **Cooldown**: **60 s** after a strategy exit signal before any new entry (`cool=60`, `c20_08.py:29, 40, 129`).

#### 2.3 Entry — expiry day (EXP mode, `c20_08.py:21-36`)
| Rule | Value | Code |
|---|---|---|
| Entry window | from **09:16** (`t0=556.0`) to before **14:40** (`t1=880`) | `c20_08.py:30-31, 129` |
| Warm-up | needs `i ≥ W+2` and `fs` 600 s ago → no entry before **09:25:02** (later if the forward started late) | L132 |
| Breakout window W | **600 s** (10 min) | L23 |
| Velocity | fs moved **≥ 20 pts** over the last **L = 150 s** | L24-25 |
| CE signal | `fs` > highest `fs` of the previous 600 s **and** `fs − fs(150 s ago) ≥ +20` | L137-138 |
| PE signal | `fs` < lowest `fs` of the previous 600 s **and** `fs − fs(150 s ago) ≤ −20` | L139-140 |
| Pullback | none (`pb = 0`): buys the breakout second itself | L34, L141 |
| Signal text | `EXP brk v=+23` (v = the 150-s move) | L149 |

The signal re-evaluates every second, so a vetoed breakout can still be bought a second later if it still qualifies.

#### 2.4 Entry — normal day (NORM mode, `c20_08.py:37-41`; geometry `c20_8x.py:179-209`)
| Rule | Value | Code |
|---|---|---|
| Entry window | **09:16** to before **15:00** (`t1 = 900`) | `c20_08.py:40` |
| Warm-up | `i ≥ 1202` → nothing before **09:35:02** | `c20_08.py:132` |
| Impulse ("arm") | `fs` breaks the high (CE) / low (PE) of the previous **1200 s** AND moved **≥ 40 pts** over **1200 s** (`W = L = 1200`, `vmin = 40`). This **arms**; it never buys on the breakout itself. | `c20_08.py:38`, `c20_8x.py:183-189` |
| Arm record | side, **base** = `fs` 1200 s before the first arming second, **extreme**, **pullback extreme**, **arm time** (first arming second). Further breakouts on the same side push the extreme and reset the pullback extreme to it, but do **not** reset the arm time. A breakout on the other side re-arms fresh. | `c20_8x.py:184-188` |
| Arm expiry | disarm if the arm is older than **min(1200, 900) = 900 s** (`PB_AMAX`) | `c20_8x.py:192-194` |
| Pullback zone | impulse = |extreme − base|; retrace = extreme − deepest pullback (CE). Needs retrace **≥ 50 %** of impulse (`pb = 0.5`); disarm if retrace ever **> 75 %** (`PB_DMAX = 0.75`) | `c20_8x.py:199-205` |
| Resumption | buy when `fs` has come back **≥ 5 pts** off the pullback extreme (`rs = 5`) (CE: up from the pullback low; PE: down from the pullback high). The arm is cleared at that moment. | `c20_8x.py:206-208` |
| Signal text | `NORM pb v=+45` (v = the 1200-s move at the buy second) | `c20_08.py:149` |

The pullback state machine runs only while flat, inside the entry window and outside the cooldown.

#### 2.5 Strike picker (which contract)
Only the nearest weekly; only contracts with a finite ask > 0, quote ≤ **5 s** old and **|delta| ≥ 0.52**.
- **Normal day** (`c20_08._pick`, `c20_08.py:62-83`, with `d52`: `dt = 0.52`, `c20_8x.py:50-51`): candidates
  ATM−150 … ATM+150 (7 strikes, 50-pt steps). Score = −| |delta| − 0.52 | → the eligible strike whose |delta| is
  **closest to 0.52** (in practice the cheapest strike that is still ≥ 0.52, i.e. ATM or 1 ITM). Exact ties: the first
  in the order ATM−150 → ATM+150.
- **Expiry day** (`tie`, `c20_9x.py:307-329`): candidates ATM ± 3 strikes. For each:
  `capture = 100 × ( |Δ|·m + ½·Γ·m² − |θ|·0.26·7.5 ) / ask` and
  `score = capture − 5 × 100 × | |Δ| − 0.65 |`, where m = |forward move over the last 150 s|, θ = engine theta per
  minute, 0.26 = `TIE_THM` (≈ calendar conversion 375/1440), 7.5 min = half of the 15-min clock, λ = `TIE_LAM` = 5.
  Highest score wins; ties broken by |delta| nearer 0.65. The 0.65 delta target dominates; the capture term tilts
  near-ties to the cheaper contract.

#### 2.6 Entry vetoes (in the order the code applies them)
1. **Mode switch** (`c20_20.py:154-157`): both `exp` and `norm` are on, so no effect.
2. **Flip-after-loss gate** (`seq` + `seqcal`, `c20_9x.py:272-304`, rent in `c20_8x.py:211-216`):
   applies only if **all** of: the last exit was a loss (bid return at the exit-signal second < 0), the new buy is the
   **other side** (CE after a PE loss or vice versa), and it is **< 900 s** (`SEQ_S`) after that exit signal.
   Then the candidate contract's gamma rent must be high enough:
   `rent = 0.5 × Γ × RV / |θ|`, RV = mean of squared 60-s changes of the forward over the last 600 s, θ = engine theta
   per minute. Threshold **0.3125** in these units = **1.2 in calendar theta** (`SEQ_CAL = 1.2 × 375/1440`).
   Below → veto (`seq`). If rent can't be computed (NaN) the buy is allowed. Same-side re-entries and buys after a
   winning/flat exit are not gated (the `fy` "flip after a non-loss" rule is off).
   Calibration (docstring L12-13, spec §3): the old c20_8x threshold 0.25 kit-theta = 0.96 calendar; 1.2 sits in the
   middle of a flat range 0.88–1.5.
3. **Stale forward** (`l2`, `c20_9x.py:381-382`): no buy while the forward is stale (§2.2).
4. **IV-shock veto, expiry days only** (`ivz`, live version `c20_9x.py:481-504`, test L383-389):
   - a(t) = mean of CE IV and PE IV (vol points) at the strike nearest the forward, averaged over the last **30 s**;
   - d(t) = a(t) − a(t − **300 s**), computed only from row 600 (**09:25:00**) on;
   - s = RMS of all d values so far today; needs **≥ 600** values (so from ≈ 09:35);
   - **veto if d / s > 1.5** (`IZ_Z`). Blocks both sides alike.
5. **Adapter checks** (§1.2 step 9): blackout, kill file, quote > 5 s old, |delta| < 0.5.
6. **Fill checks** (§1.3): no print within 3 s, blackout, ≥ 15:29, unaffordable.

Not used by c20_9x: IV-rise guard (`iv`), opening-range lock (`orb`/`orbx`), OI flow (`oi`), gamma-rent gate (`gr`),
expiry 13:30 cut (`pm`), range-width guard (`rw`), theta/ask cap (`th1`), exhaustion block (`exh`).

#### 2.7 Exits — in the exact order checked each held second
Let entry = fill LTP, bid = current bid of the held contract, g = peak bid ÷ entry − 1, held = seconds since the fill.

**0. Adapter, before the strategy:** forced flat **15:00 (expiry) / 15:20 (normal)** → `TIME (council forced flat)`,
filled at once (`__init__.py:173-175`).

**Preparation** (`c20_9x.py:347-370`):
- Normal days (`dtr`): forward trail = **40 × clip( |Δ at entry| ÷ |Δ now| , 0.8 , 1.0 )** → between **32 and 40 pts**;
  it tightens as the option goes deeper ITM, never widens (`_dfac`, L152-161; Δ at entry = the table's delta on the
  fill second).
- Expiry days (`ptre`): sb = bid (EMA with tau 1 s = the raw bid), spk = highest sb since entry. Once
  **spk ≥ entry × 1.70** (`PT_PA = 0.7`) the premium trail is **armed** and the forward trail is switched off
  (trail set to 1e9).

**1. Core exits** (`c20_08.py:110-127`) — run only when the forward has a value this second:
| Order | Code | Rule |
|---|---|---|
| 1a | `SL` | bid ≤ entry × **0.85** (−15 %, `sl = 0.15`, both modes) |
| 1b | `TP` | bid ≥ entry × 10.9 (`tp = 9.9` — **effectively off**) |
| 1c | `FWD_TRAIL` | forward give-back from the best smoothed forward since entry ≥ trail. CE: best `fs` − `fs` now; PE: `fs` now − lowest `fs`. Trail = **25 pts expiry**; **40 × factor (32–40) normal**; off on expiry once the premium trail is armed. The "best" starts at the first stepped second after the fill. |
| 1d | `TIME` | held ≥ **900 s** (15 min) expiry / **5400 s** (90 min) normal |

**2. Premium floors** (`c20_9x.py:222-253`, levels `_floor0` L172-187) — checked whenever the bid is known; exit when
**bid ≤ floor**:
| Day | Peak gain g | Floor | Code |
|---|---|---|---|
| Expiry (`pex` step) | < +15 % | none | — |
| Expiry | +15 % ≤ g < +60 % | entry (break-even, `BE_LOCK = 0.0`) | `BE_LOCK` |
| Expiry | g ≥ +60 % | entry × (1 + **0.70** × g) | `GIVEBACK` |
| Normal (`ramp`) | < +15 % (`R_ARM`) | none | — |
| Normal | +15 % ≤ g < +25 % (`R0`) | entry | `BE_LOCK` |
| Normal | +25 % ≤ g < +50 % (`R1`) | entry × (1 + g × k), k = 0.45 + 0.25 × (g − 0.25)/0.25 (0.45 → 0.70), never below entry | `RAMP_LOCK` |
| Normal | g ≥ +50 % | entry × (1 + **0.70** × g) | `GIVEBACK` |

Examples (normal): peak +30 % → floor +15 %; +40 % → +24 %; +50 % → +35 %. Expiry: peak +60 % → floor +42 %.
Precedence (`ffirst`, L239-244): if the floor is hit and the core said nothing → floor exit. If in the same second the
core said `FWD_TRAIL` or `TIME`, the exit is **relabelled** with the floor's name (same second, same fill). If the core
said `SL`, it stays `SL`.

**3. Two-layer loop** (`l2`, `c20_9x.py:405-427`) — only if nothing above fired:
- `SL` (bid ≤ entry × 0.85) and `TIME` (clock) again — these matter when the forward is missing and the core skipped;
- `STALE_PTRAIL`: while the forward is stale, remember the best bid since it went stale and the forward give-back at
  that moment (give0); exit when the bid has fallen from that best by ≥ |Δ now| × max(trail − give0, 0) (|Δ| = 0.6 if
  unknown or ≤ 0.05). Trail here = the **base** 25 / 40 pts (see Ambiguities).

**4. Premium trail, expiry only** (`ptre`, L428-430): once armed (peak bid ≥ +70 %), exit when
bid ≤ peak bid × **0.92** (`PT_PQ = 0.08`) → `PREM_TRAIL`. (At a +70 % peak this is +56.4 %, above the +49 % GIVEBACK
floor; the floors are checked first in the same second.)

(`RENT` underwater stop `uw` and `RENT_TRAIL` `rt` exist in the class but are off in c20_9x.)

#### 2.8 Exit codes you will see in the trade log
| Log reason | Meaning |
|---|---|
| `COUNCIL SL` | −15 % premium stop (bid ≤ 85 % of entry) |
| `COUNCIL FWD_TRAIL` | the smoothed forward gave back the trail (25 pts expiry; 32–40 pts normal) from its best since entry |
| `COUNCIL TIME` | the strategy clock: 15 min expiry / 90 min normal |
| `COUNCIL BE_LOCK` | peak was ≥ +15 % and the bid fell back to the entry price |
| `COUNCIL RAMP_LOCK` | normal day, peak +25…+50 %, bid fell to the ramp floor |
| `COUNCIL GIVEBACK` | peak ≥ +60 % (expiry) / ≥ +50 % (normal) and the bid fell to entry + 70 % of the peak gain |
| `COUNCIL PREM_TRAIL` | expiry, peak ≥ +70 %, bid 8 % below the peak bid |
| `COUNCIL STALE_PTRAIL` | forward frozen ≥ 5 s; premium version of the forward trail |
| `COUNCIL TP` | take-profit at +990 % — never expected |
| `TIME (council forced flat)` | 15:00 expiry / 15:20 normal |
| Shadows only | `RENT_TRAIL` (9t), `PGB`, `LVL_BOOK` (9v), `EXP_TRAIL` (9e), `HALF_LOCK` (9h) |
| Defined, unused anywhere live | `PCAP`, `EXH`, `RENT` |

(`live_stats.json` lists the codes without the `COUNCIL ` prefix.)

#### 2.9 What changed from the spec (code wins)
- Spec §5 lists forced flat last; the code checks it **first** (adapter).
- Spec §11.5 says the EMA catch-up "is a no-op in the engine"; since the D-126 fill rule the adapter does not step the
  strategy while a fill is pending, so `catch` **is active** live.
- Spec §4.4 says the premium trail uses "the raw bid": the code uses an EMA with tau = 1 s, which is the raw bid. ✔
- Everything else in spec §2–§6 (numbers, windows, floors, picker, ivz) matches the code.

---

### 3. The shadows

All shadows are c20_9x plus one small mixin (or, for c20_8x, c20_9x minus the round-9 parts). Unchanged unless stated.

#### 3.1 c20_8x — the parent (round-8 autopsy, before round 9)
`c20_8x.Strategy()` with `FINAL = ("exp","norm","seq","pex","pbg","d52")` (`c20_8x.py:47-48, 295`). Why: the
round-8 autopsy's minimal combination on member 08's core (docs/19); champion candidate before c20_9x.
Differences from c20_9x:
| Area | c20_8x | c20_9x |
|---|---|---|
| Expiry picker | |delta| closest to **0.65**, ATM±150 (`c20_08.py:79-80`) | tie-breaker score (§2.5) |
| Flip gate threshold | rent ≥ **0.25** kit units (`SEQ_C`, `c20_8x.py:29, 226-229`) | ≥ 0.3125 (= 1.2 calendar) — slightly stricter |
| IV-shock veto | none | expiry `ivz` |
| Stale forward | no veto, no SL/TIME without a forward, no STALE_PTRAIL | `l2` |
| EMA after skipped seconds | restarts at the raw forward (no `catch`) | bridged |
| Normal-day trail | fixed **40 pts** | 40 × (0.8–1.0) |
| Normal-day floors | the step: +15 % → entry (`BE_LOCK`), +60 % → keep 70 % (`GIVEBACK`) | the ramp |
| Expiry premium trail | none (forward trail always on) | `PREM_TRAIL` after +70 % |
| Floor precedence | floors checked only if the core gave no exit; `GIVEBACK` tested before `BE_LOCK` (`c20_8x.py:280-286`); no relabelling | `ffirst` |
Entry windows, impulse/pullback geometry, SL −15 %, clocks, cooldown and the normal picker (0.52) are the same.

#### 3.2 c20_9t — rent trail (`c20_9t.py`, switch `rt` in `c20_9x.py:189-221, 256-270`)
Why: owner, 31 Oct, after three 30 Oct trades peaked +13…+18 % and exited ≈ 0 — "a stronger trailing system on days
which are not trending". Shadow since 1 Nov (lost the 8-day replay: +3.89 L vs +9.30 L, CHANGELOG 1 Nov).
- **Arming** (both day types, checked every held second, L201-220): peak gain ≥ **+8 %** (`RT_ARM`) AND either
  - *quiet*: the held contract's calendar rent (realised ÷ implied variance of the forward, last 600 s) ≤ **0.5 ×**
    its value at entry (first computable value after the fill), or
  - *chop*: trend efficiency of the raw forward over the last **600 s** (sampled every 60 s: |net move| ÷ sum of
    |1-min moves|) < **0.35**.
  Once armed it stays armed for the rest of the trade.
- **Exit**: an extra floor `entry × (1 + 0.60 × peak gain)` (`RT_KEEP`), used when higher than c20_9x's floor →
  `RENT_TRAIL` (L164-170).
- **Re-entry veto** (L256-270): a **same-side** buy within **900 s** (`RT_W`) of a `RENT_TRAIL` exit is refused
  (`rt_reentry`) unless the forward's move over L (150 s expiry / 1200 s normal) is larger than the booked trade's
  trigger move **and** trend efficiency ≥ 0.35.

#### 3.3 c20_9v — level booking + smoothed give-back, normal days (`c20_9v.py`)
Why: C9 council, 1 Nov (owner: make each day, especially 30 Oct, profitable); 9-day replay +9.74 L vs +9.30 L, but
23 Oct −22k. Expiry days are pure c20_9x. On normal days, after all c20_9x exits found nothing (L73-74):
- **`PGB`** (L66-80): sb = EMA (**20 s**) of the held bid (`sb += (bid − sb)/20`), spk = max sb. Once
  spk ≥ entry × **1.15**, sell when sb ≤ entry × (1 + **0.6** × (spk/entry − 1)).
- **`LVL_BOOK`** (L82-100): reference = Nifty spot while fresh (changed within the last **120 s**), else forward −
  last basis. At the first held normal second the 50-pt round numbers ahead of the trade by > **3 pts** are fixed
  (base−300 … base+350). Track the best reference since entry; levels it has passed by > **8 pts** are dropped. Sell
  when the best came within **13 pts** of the next level (or passed it by ≤ 8), the reference has given back
  ≥ **10 pts** from the best, the bid is ≥ entry × **1.06**, and the peak bid is still < entry × **1.20**.
- State is kept on the position (`pos["st"]`), so it survives a restart. If the reference switches source the best is
  re-based (no false rejection).

#### 3.4 c20_9e — expiry give-back trail in points (`c20_9e.py`)
Why: owner, 3 Nov ("the code is still not trailing") after a −44,688 expiry day where 7 trades peaked +11…+19 pts
(docs/21 §2, §4). Expiry days only: once peak bid − entry ≥ **5 pts** (`ARM`), an extra floor = peak bid − **6 pts**
(`GIVE`) → `EXP_TRAIL`, used when higher than c20_9x's floor (L20-28). Note: with a peak between +5 and +6 pts this
floor is *below* entry (a small loss can be booked). Replay on 19 Oct, 27 Oct, 3 Nov: c20_9x +5.17 L, c20_9e +1.10 L
(CHANGELOG). Normal days identical to c20_9x.

#### 3.5 c20_9h — half-of-peak floor on expiry (`c20_9h.py`)
Why: the alternative to c20_9e from docs/21 §4 (3 Nov). Expiry days only: once g ≥ **+15 %**, an extra floor =
entry × (1 + **0.5** × g) → `HALF_LOCK`, used when higher (L13-20). So between +15 % and +60 % it keeps half the gain
(c20_9x keeps only the entry); from +60 % c20_9x's GIVEBACK (70 %) is higher and wins. Same replay: +0.21 L.
Normal days identical to c20_9x.

#### 3.6 c20_9s — stale-impulse pullback veto, normal days (`c20_9s.py`)
Why: panel C11, 3 Nov night (owner: "we cannot be sitting on a trade for 15 mins … if it is not performing"); every
stuck normal-day trade was a pullback into an impulse that had already finished (docs/22). Rule (L38-45): refuse the
normal-day pullback BUY if the impulse **first armed more than 660 s** (11 min, `PB_AGE_MAX`) before the buy
second. The arm is consumed as if bought. Applied after all c20_9x vetoes. Expiry days, exits, picker identical.
Kit 11 days: +12.26 L vs +11.50 L.

#### 3.7 c20_9y — IV-rich and OI-wall vetoes (`c20_9y.py`)
Why: twenty-member panel C12, 4 Nov night (owner: "taking stupid loss making trades"; docs/23). Two entry vetoes,
applied after all c20_9x vetoes (L83-97):
- **`iv_rich`** (both day types): ATM IV (30-s mean of (CE IV + PE IV)/2 at the strike nearest the forward, percent)
  more than **3.5 vol pts** above its median since 09:20; needs ≥ **300 s** since 09:20 (i.e. from 09:25).
- **`oi_wall`** (normal days): among strikes within **250 pts** of the forward, the strike with the most OI of the
  *same* type as the buy (call OI for a CE buy, put OI for a PE buy) lies **ahead** of the trade and **≤ 25 pts** away.
Kit 12 days: +12.32 L vs +11.24 L; thin evidence (8 vetoed buys on 5 days).

---

### 4. Summary table (live statistics from `live_stats.json`)

| Book | Entry (one line) | Exits (one line) | Live days (from) | Trades/day | Strike rate | Median hold (p90) | Main exit reasons (count) | Live total ₹ |
|---|---|---|---|---|---|---|---|---|
| **c20_9x** (champion) | Expiry: 10-min breakout + 20 pts/150 s, tie-break strike near Δ0.65; Normal: 40-pt/20-min impulse → 50–75 % pullback → 5-pt resumption, Δ≈0.52; vetoes seq(1.2 cal), stale fwd, ivz (expiry) | SL −15 %; fwd trail 25 / 32–40 pts; clock 15 / 90 min; floors BE +15 %, GIVEBACK +60 % (exp) / ramp (normal); PREM_TRAIL 8 % after +70 % (exp); flat 15:00 / 15:20 | 6 (30 Oct) | 4.7 | 50 % | 13.0 min (43.6) | FWD_TRAIL 9, SL 6, TIME 6, BE_LOCK 5, GIVEBACK 1 | +57,879 |
| c20_8x | Same entries; expiry Δ closest 0.65; seq 0.25 kit; no ivz / stale veto | SL; fwd trail 25 / 40 fixed; clocks; step floors both days; no premium trail | 6 (30 Oct) | 5.2 | 42 % | 11.7 (24.9) | FWD_TRAIL 12, SL 7, TIME 6, BE_LOCK 5, GIVEBACK 1 | +9,659 |
| c20_9t | c20_9x + same-side re-entry veto 15 min after RENT_TRAIL | c20_9x + RENT_TRAIL (keep 60 % once +8 % and quiet/choppy) | 5 (2 Nov) | 5.2 | 62 % | 7.2 (18.5) | RENT_TRAIL 16, SL 6, FWD_TRAIL 3, BE_LOCK 1 | −19,419 |
| c20_9v | = c20_9x | c20_9x + normal days PGB (20-s bid EMA, keep 60 % after +15 %) and LVL_BOOK (50-pt levels, +6 %…<+20 %) | 5 (2 Nov) | 5.0 | 56 % | 12.1 (34.9) | SL 6, TIME 6, FWD_TRAIL 4, BE_LOCK 3, LVL_BOOK 2 | +80,356 |
| c20_9e | = c20_9x | c20_9x + expiry EXP_TRAIL (arm +5 pts, give 6 pts) | 3 (4 Nov) | 3.0 | 44 % | 11.7 (70.5) | FWD_TRAIL 8, TIME 1 | +62,923 |
| c20_9h | = c20_9x | c20_9x + expiry HALF_LOCK (keep 50 % from +15 %) | 3 (4 Nov) | 3.0 | 44 % | 11.7 (70.5) | FWD_TRAIL 8, TIME 1 | +62,923 |
| c20_9s | c20_9x + refuse normal pullback if impulse armed > 660 s ago | = c20_9x | 3 (4 Nov) | 2.7 | 50 % | 12.5 (70.5) | FWD_TRAIL 7, TIME 1 | +65,302 |
| c20_9y | c20_9x + iv_rich (> 3.5 vol pts over median) + normal oi_wall (≤ 25 pts ahead) | = c20_9x | 2 (5 Nov) | 2.0 | 75 % | 40.6 (70.5) | FWD_TRAIL 3, TIME 1 | +88,335 |

Notes on the table: c20_9e and c20_9h differ from c20_9x only on expiry days and have had no expiry day live yet, so
their identical figures are expected. The books started on different days, so totals are not comparable across rows.
c20_9x's exit counts sum to 27 of 28 trades and c20_9v's to 21 of 25 — the file appears to list the top five reasons
only.

---


---

## Part C — The domino-impulse grid and the edge books



Source read on 7 Nov 2026 (commit 78be22f). File:line references are to `apex/engine/paper.py` unless named.
Every book here starts the day with ₹1,00,000, buys all-in (`lots = floor(capital / (premium × 65))`, paper.py:1073),
holds at most one position, and only buys options.

**Which path each book really takes.** `evaluate_entry` (paper.py:812) checks, in order, `spot_dc`, `fade_switch`,
`spike`, `random`, `momentum` (paper.py:841-850); only a book with none of these reaches the domino-episode branch.

| Path | Books |
|---|---|
| Domino episode / impulse (paper.py:851-898) | the nine m-grid books `m1.5_s0.4` … `m2.5_s0.6`, `gap3_s0.4`, `gap5_s0.4`, `m2.0_s0.5_bookexit`, `m2.0_s0.5_ivinterp`, `m2.0_s0.5_novol`, `m2.0_s0.5_trend`, `m2.0_s0.5_d20`, `m2.0_s0.5_tvfast` |
| **NOT this path: SPOT books** (`spot_dc = 720` → `evaluate_spot_breakout`, paper.py:841-842) | `apex_edge`, `edge_gate_only`, `edge_bracket_only`, `edge_gate_trail` (pullback entry; retest breakout on expiry day) and `edge_breakout` (retest breakout every day). Their m*/s*/L*/d* values are placeholders that their entry never reads (config.py:187-188 comment). They are covered separately in section 4. |

---

### 1. Entry — the domino-impulse books

#### 1a. What the engine measures (apex/engine/domino.py)
All futures prices here are the Nifty-futures **bid/ask mid** (config.py:55 `FUT_PRICE_IS_MID`).
- **r15** = futures move over the last 15 s, in points.
- **sigma15** = a 20-minute half-life average of |r15| (sampled 1 per second, in-session only), **never below 5.0 pts**
  (`SIGMA15_FLOOR`, config.py:138; domino.py:139). Seed 4.0 until it warms.
- **Impulse z** = r15 / sigma15 (domino.py:140). Direction d = UP if z ≥ 0, else DOWN (domino.py:142).
- **Synchrony S** (domino.py:157-163) = the share of tracked Nifty-heavyweight index weight whose own 15-s move is in
  direction d, with its own z ≥ 1.0 (`RECRUIT_Z`) **and** 15-s volume ≥ 1.2 × its own baseline (`ACTIVITY_MIN`; the
  volume test is only on after 10 min of session, `WARMUP_S`). `novol` variants use the same S without the volume test.
- **Basket gap** = Mb − r15 (domino.py:172, 182): Mb is the basket's weighted move converted into Nifty points and scaled
  up to 100 % of index weight; r15 is what the futures actually did. Positive in direction d = the stocks imply more move
  than the futures have made.
- **Episode** (domino.py:194-221): starts when |z| ≥ 1.0 (`ONSET_Z`); remembers the futures price at onset (fut0) and
  its direction. It ends after |z| < 0.5 for 30 s, or at once if the opposite direction reaches |z| ≥ 2.0. It carries a
  type (BASKET-LED / FUTURES-LED / SINGLE-NAME / CO-FIRST / FORMING) and the first stock to cross z 2 — **the type is
  only reported, it never gates the entry**. An episode born while the data guard is on is tagged `gap`
  (engine_main.py:500-506).

#### 1b. The checks, in the exact order the code makes them (every 100 ms)
Common pre-checks (all books):
1. Already in a position → no (paper.py:822). An entry waiting for its fill → no (paper.py:824).
2. Time window: **09:25 ≤ now < 15:29** (`SUPPRESS_UNTIL`, `LAST_ENTRY` — 15:29 is the owner's CAS test value;
   production was 15:15; config.py:92-96; paper.py:828).
3. Data blackout (feed frozen or just resumed) → no (paper.py:831).
4. **Cool-down: 60 s after any exit** (`REENTRY_COOLDOWN_S`, config.py:59; none of these books overrides it;
   paper.py:834-837).
5. Daily brake (paper.py:756): only the KILL file (data/KILL) is active. Daily loss stop, losing-streak stop, max
   entries/day and expiry-day entry end are all OFF (`DAILY_LOSS_STOP_PCT = 0`, `LOSS_STREAK_N = 0`,
   `MAX_ENTRIES_PER_DAY = 0`, `EXPIRY_ENTRY_END = None`, config.py:67-71).

Domino branch (paper.py:851-898):
6. There must be a live episode; not born in a data gap; **not already traded by this book** (one trade per episode).
7. The current impulse direction must equal the episode's direction ("impulse against the episode").
8. **Impulse z ≥ m\*** in that direction. Gap books first need **basket gap ≥ gap\*** (3.0 or 5.0 pts), then z ≥ m\*
   (their m\* is 1.0) (paper.py:863-870).
9. **Points floor: |r15| ≥ 15 pts** (`MIN_IMPULSE_PTS`, config.py:60; paper.py:871). Applies to every book incl. the gap
   books. Because sigma15 is floored at 5, z ≥ 2 already needs ≥ 10 pts; whenever sigma15 ≤ 7.5 pts the 15-pt floor is
   the stricter rule, so m\* = 1.5 and m\* = 2.0 often fire on the same impulses (the live stats show m1.5 and m2.0 at
   each s\* with identical trade counts and exit mixes).
10. **Synchrony S ≥ s\*** (0.4 / 0.5 / 0.6) (paper.py:874).
11. Trend variant only: futures move over the last 30 min must be **≥ 20 pts in the impulse's direction**
    (`TREND_MIN_PTS`, config.py:76; paper.py:876-882).
12. **Not late (points):** |futures now − futures at episode onset| ≤ L\* × sigma15 = **3.0 × sigma15** (so at least
    15 pts) (paper.py:883).
13. **Not late (IV):** ATM IV has risen ≤ **1.5 vol points** since onset (`IV_RISE_CAP`, config.py:130). `ivinterp` measures
    the same rise on IV interpolated at the forward instead of the nearest strike (paper.py:887-889).
14. **Regime gate** (`base_gate`, paper.py:738; config.py:62-63): entries only when the market regime
    (apex/engine/regime.py:143-159) is **DIRECTIONAL** (5-min efficiency ER5 ≥ 0.35 and heavyweight breadth ≥ 60 %) or
    **BREAKOUT** (beyond the 30-min range that ended 5 min ago, ER5 ≥ 0.35, activity ≥ 60th pct), and **not pointing
    the other way**. WARMING (first 10 min, or after a gap), EXHAUSTION, COMPRESSION, RANGE, UNCERTAIN all block.
15. Learning-loop gates (paper.py:893): advisors promoted by the learning loop veto. **Currently none**
    (data/learning/state.json: `gates: []`). The advisors (iv_late, room, coherence, force, episode, regime …;
    engine_main.py:1025) are computed and stored with each trade but do not block.

#### 1c. Which option is bought (choose_contract, paper.py:126-178)
- CE for UP, PE for DOWN. Candidates: this week's expiry, premium **₹20-600**, quote younger than 15 s, delta known.
- Delta band by calendar days to this week's expiry (config.py:453-458):
  - ≥ 3 days: |delta| **0.52-0.70**; 1-2 days: **0.60-0.80**;
  - expiry day (0 DTE): **0.65-0.85**, this week's expiring contract only (`ZERO_DTE_USE_NEXTWEEK = False`), and **no
    entries at or after 14:45** (`ZERO_DTE_NO_ENTRY`).
- Pick: the **lowest |delta| inside the band** = the strike nearest the money on the in-the-money side (ATM or 1-2 ITM).
  If none is in the band: the lowest |delta| above the band's floor (flagged `band_fallback`). None at all → no trade
  (the episode is NOT marked traded, so it can still fire later).
- None of these books sets `cheap_strike`, `gt_min`, `reentry`, or the flow vetoes, so `_entry_choice`
  (engine_main.py:1293-1324) adds nothing after the strike pick.

#### 1d. The fill (paper.py:1026-1066; config.py:120-121)
The trigger does not fill on the print on screen. It waits for the **first new print of that contract after the
trigger, at most 3.0 s** (`ENTRY_FILL_MAX_S`); no print, a data gap, or 15:29 reached → the entry lapses. Fill price =
that LTP; lots = floor(₹ capital / (LTP × 65)); under 1 lot → rejected. The episode is marked traded at the fill.

---

### 2. Exits — the domino-impulse books (check_exit, paper.py:1133; default branch 1198-1205)

Measured on the futures **mid** (`_fx`, paper.py:806). There is **no premium LOCK, no hard premium stop and no max-hold
for these books**: `_premium_lock_exit` and the gain trail are only called in the spot-book branch (paper.py:1172-1194).

Priority (first that fires wins):
1. **STOP / TRAIL (futures points)** (paper.py:1199-1204). Stop starts at entry futures − d\* (12 pts; **20 pts** for
   `d20`). Once the best futures price since entry has gone **d\* in favour** (+12 / +20), the trail arms and the stop
   becomes best − d\* (it never moves back). Hit before arming → **STOP**; after arming → **TRAIL** (a TRAIL exit is at
   or above the entry futures price, but the option itself may still be slightly down).
2. **THESIS-VOID (synchrony flipped)** (paper.py:1205-1213): the opposite direction's synchrony ≥ s_exit (default = the
   book's own s\*) **and** futures z ≥ 1.0 against the trade, holding continuously for **5 s** (`THESIS_VOID_HOLD_S`,
   config.py:58). `tvfast`: opposite S measured without the volume test, ≥ **0.30**, held **1.0 s**.
3. **BOOK** (`bookexit` only, paper.py:1215-1219): the asks on the held contract are REFILLING in both quantity and
   number of orders (ask qty up > 15 % over 10 s; apex/engine/flow.py:190), futures have made less than 0.5 × d\*
   (6 pts) in favour, and the trade is over 20 s old. Only for the ten "hero" contracts (this week, ATM ± 2 strikes).
4. **TIME** — `TIME (15:35 flatten)` (`FLATTEN_AT`, the CAS-test value; production 15:25) and on expiry day
   `TIME (0DTE 15:00)` unless the held option's |delta| ≥ 0.9 (`ZERO_DTE_FLATTEN`) (paper.py:1231-1235).

Exit fills (paper.py:1236-1265): a price exit is not decided on frozen data (blackout or futures quote older than 10 s,
`EXIT_FUT_STALE_S`). Once triggered it is committed even if price bounces, and it fills on the first new option print
after the trigger, waiting up to 10 s (`EXIT_DEFER_MAX_S`); after that it fills at the last price and is tagged
`stale_exit`. TIME exits fill at once.

**Exit codes in the trade log (these books):** `STOP` = 12-pt (20-pt) futures stop before trail armed; `TRAIL` =
trailing stop after +d\*; `THESIS-VOID (synchrony flipped)`; `BOOK (sellers refilled on the held contract)`;
`TIME (15:35 flatten)` / `TIME (0DTE 15:00)`.

**How long trades last (live):** very short. Median hold **0.9-1.4 min** for the 12-pt books, p90 **2.7-5.5 min**;
`d20` median 2.3 / p90 7.6 min; `bookexit` 0.4 / 1.0; `tvfast` 0.5 / 1.3. Median first entry of the day is around
13:00-13:20 (regime gate + quiet-market floor); no TIME exits appear in the live record for any of them.

---

### 3. Per-book table (live: data/paper, from live_stats.json; strike = % of trades won; total in ₹)

All domino books: L\* 3.0, IV cap 1.5, 60-s cool-down, regime gate, 15-pt floor, exits as in section 2.

| Book | Distinguishing settings | In words | Live days / trades/day | Strike | Hold med / p90 (min) | Exits (live) | Total ₹ |
|---|---|---|---|---|---|---|---|
| m1.5_s0.4 | m\* 1.5, s\* 0.4, d\* 12 | loosest impulse, loosest crowd | 14 / 3.4 | 40 % | 1.0 / 3.2 | STOP 17, TV 17, TRAIL 14 | +6,685 |
| m1.5_s0.5 | m\* 1.5, s\* 0.5 | | 14 / 2.7 | 34 % | 0.9 / 3.2 | STOP 14, TV 13, TRAIL 11 | −24,677 |
| m1.5_s0.6 | m\* 1.5, s\* 0.6 | | 14 / 1.9 | 42 % | 1.1 / 5.5 | TRAIL 12, STOP 9, TV 5 | +3,370 |
| m2.0_s0.4 | m\* 2.0, s\* 0.4 | | 14 / 3.4 | 42 % | 1.0 / 5.5 | STOP 17, TV 17, TRAIL 14 | +9,100 |
| m2.0_s0.5 | m\* 2.0, s\* 0.5 (= config.TRIGGER, the v1 trigger D-033) | the original trigger | 14 / 2.6 | 35 % | 0.9 / 3.2 | STOP 14, TV 12, TRAIL 11 | −17,950 |
| m2.0_s0.6 | m\* 2.0, s\* 0.6 | | 14 / 1.7 | 46 % | 1.4 / 5.5 | TRAIL 12, STOP 9, TV 3 | +11,027 |
| m2.5_s0.4 | m\* 2.5, s\* 0.4 | | 14 / 2.9 | 42 % | 0.9 / 5.5 | STOP 17, TRAIL 13, TV 10 | +16,946 |
| m2.5_s0.5 | m\* 2.5, s\* 0.5 | | 14 / 2.0 | 43 % | 0.9 / 5.5 | STOP 12, TRAIL 11, TV 5 | −4,683 |
| m2.5_s0.6 | m\* 2.5, s\* 0.6 | strictest impulse + crowd | 14 / 1.5 | 52 % | 1.3 / 5.5 | TRAIL 12, STOP 8, TV 1 | +32,922 |
| gap3_s0.4 | gap\* 3.0, m\* 1.0, s\* 0.4 | basket implies ≥ 3 pts more than futures moved (still needs a ≥ 15-pt futures move) | 14 / 1.2 | 29 % | 0.9 / 2.7 | TRAIL 9, TV 5, STOP 3 | −7,306 |
| gap5_s0.4 | gap\* 5.0, m\* 1.0, s\* 0.4 | same, basket lead ≥ 5 pts | 14 / 0.9 | 50 % | 0.9 / 1.7 | TRAIL 7, TV 3, STOP 2 | +9,588 |
| m2.0_s0.5_bookexit | `exit_book` | m2.0_s0.5 + leave when sellers refill on the held contract | 14 / 2.7 | 39 % | 0.4 / 1.0 | BOOK 23, TV 5, TRAIL 5, STOP 5 | −22,964 |
| m2.0_s0.5_ivinterp | `iv_interp` | IV-late cap read on forward-interpolated IV | 14 / 2.6 | 35 % | 0.9 / 3.2 | STOP 14, TV 12, TRAIL 11 | −17,950 (identical to m2.0_s0.5 live) |
| m2.0_s0.5_novol | `novol` | synchrony without the per-stock volume test (entry and thesis-void) | 14 / 4.8 | 40 % | 0.9 / 2.9 | TV 29, TRAIL 20, STOP 18 | −17,563 |
| m2.0_s0.5_trend | `trend` | only with a ≥ 20-pt 30-min futures move in the same direction | 13 / 1.0 | 69 % | 1.3 / 5.5 | TRAIL 10, STOP 3 | +45,269 |
| m2.0_s0.5_d20 | d\* 20 | 20-pt stop, trail arms at +20, trails 20 behind | 13 / 1.3 | 47 % | 2.3 / 7.6 | TRAIL 10, STOP 7 | −11,437 |
| m2.0_s0.5_tvfast | s_exit 0.30, tv_novol, tv_hold_s 1.0 | thesis-void much sooner: opposite S (no vol test) ≥ 0.30 for 1 s | 13 / 1.4 | 44 % | 0.5 / 1.3 | TV 14, TRAIL 3, STOP 1 | +10,335 |

(TV = THESIS-VOID.) Why each exists (config.py comments): m-grid = the 3×3 pre-registered grid around the v1 trigger
for the learning loop (config.py:142-148); gap books = owner's "basket leads, futures lag" idea, 17 Oct (config.py:151-154);
bookexit = a fifth exit "force on the contract you hold" (config.py:155-157); ivinterp = owner decision O-1, 18 Oct
(config.py:169-173); novol = D-100, the volume test kept S low (config.py:174-179); trend = D-114, 19 Oct counter-trend
calls all lost (config.py:180-182); d20 and tvfast = D-118 council-4 shadows, wider stop / faster thesis-void (config.py:276-279).

---

### 4. The edge books and apex_edge (SPOT path — separate rules)

All five carry `spot_dc 720`, so they never read episodes, z, synchrony, the 15-pt floor, the L\*/IV lateness, or the
regime gate, and the learning-loop gates are not consulted. Shared settings (config.py:217-220 `_SPOT`, 236-238 `_PB`,
245-266): **cool-down 0 s**, no streak stop, no entry cap; common pre-checks 1-3 and 5 of §1b still apply (09:25-15:29,
blackout, KILL), and the same `choose_contract` delta bands and the 3-s next-print fill.

#### Entry A — PULLBACK (apex_edge, edge_gate_only, edge_bracket_only, edge_gate_trail; non-expiry days)
`evaluate_pullback`, paper.py:285-337, on the 45-min Nifty **spot** window (apex/engine/impulse.py):
spot quote ≤ 5 s old; **no new entries from 14:45** (`pb_entry_end`); **range gate**: no entries while the day is in range
mode (a day leg ≥ 100 pts has given back ≥ 61.8 %, until a new session high/low; config.py:251-252); the window's
high-low range must be **≥ 60 pts** (`pb_min_range`); direction = whichever extreme came last; that extreme must be ≥ 30 s
old; one trade per impulse; the deepest pullback so far must not exceed **80 %** (78 % + 2 % slack) of the range; buy when
spot is **50-78 %** back from the extreme. The position remembers stop = impulse origin, target = extreme + 1.0 × range.

#### Entry B — RETEST BREAKOUT (edge_breakout every day; the other four on expiry day, `dte0_retest`)
`evaluate_spot_breakout`, paper.py:190-268: spot breaks the high/low of the previous **12 minutes** (720 s; window must be
≥ 80 % covered, engine_main.py:891-904) → the break is ARMED at that level; spot must run **5 pts** beyond it, then come
back to within **2 pts** of it → buy. Cancelled if the level is lost by **3 pts** or after **300 s**. "One trade per
swing": after a trade, another in the same direction needs spot beyond that trade's best spot (paper.py:252-256). On
expiry day choose_contract still stops entries at 14:45.

#### Extra entry gate — BUYER EDGE (`gt_min 0.5`: apex_edge, edge_gate_only, edge_gate_trail, edge_breakout)
After the strike is chosen (engine_main.py:1305-1310; paper.py:511-532): skip unless
**0.5 × gamma × v_min30 / |theta per minute| ≥ 0.5**, where v_min30 = spot's realised variance per minute over the last
30 min from 1-minute changes (apex/engine/edge.py:102-121; needs ≥ 6 one-minute bars). "Theta is the rent for gamma".
A skipped setup is dropped, not queued.

#### Exits (check_exit spot branch, paper.py:1172-1194), priority as coded
1. Structural spot exit `_spot_trail_exit` (paper.py:697-735): pullback trade → `STOP (impulse origin …)` / `TARGET (…)`;
   retest trade → 12-pt spot trail from the best spot (initial stop spot_in − 12) → `TRAIL` if best ever beat entry spot,
   else `STOP`.
2. **Premium bracket** books (`prem_tgt` set) **replace** step 1's verdict with the premium bracket only
   (paper.py:1174-1175, 535-545): `TARGET (premium +20 %)` / `STOP (premium −10 %)`, fresh prints (≤ 5 s) only.
3. Level book (`lvl_book`, paper.py:376-391), only if 1/2 gave nothing: levels ahead fixed at entry (prior-day H/L/C,
   day high/low, opening range, round 100s); best spot came within 5 pts of the next level without passing it by > 5
   and spot then gave back 10 → `BOOK at <level>`.
4. Hard stop / gain trail (paper.py:589-647; edge_gate_trail only): `STOP (premium …, hard stop −10 %)`; once the 30-s
   average premium has gained ≥ 20 %, out when that average falls to ≤ 0.8 × its peak gain → `TRAIL (kept …)`.
5. LOCK (paper.py:669-694; lock_pct 18 / trail 10, edge_gate_only and edge_gate_trail): armed at premium +18 %, then out if
   premium falls 10 % from its best → `LOCK (…)`. If another exit fires while armed, it is suffixed "(locked +18 % at …)".
6. Safety: spot quote > 60 s old → stop/trail on the futures mid at 12 pts → `STOP (futures: spot quote … s old)`.
7. TIME: `TIME (max hold 30 min)` (bracket books, `max_hold_s 1800`); `TIME (15:00 book flatten)` (`pb_flatten`, all but
   edge_breakout); `TIME (15:35 flatten)`; `TIME (0DTE 15:00)` unless |delta| ≥ 0.9. THESIS-VOID never applies (S_opp = −1).

#### The five books

| Book | Entry | Gate | Exits | Daily stop | Live (8 days from 28 Oct) |
|---|---|---|---|---|---|
| **apex_edge** | pullback (retest on expiry day) | buyer edge 0.5 | premium −10 % / +20 %, 30 min max; no lock, no level book | −20 % on the day (no entries below ₹80,000) | 2.5/day, 55 %, med 13.1 / p90 30.0 min, STOP 8 · TARGET 6 · TIME 6, **+43,345** |
| **edge_gate_only** | pullback (retest on expiry day) | buyer edge 0.5 | spot_dual_lvl's: impulse-origin stop / 1× target (12-pt trail on retest trades), level book, LOCK 18/10 | none | 2.4/day, 58 %, med 19.4 / p90 120.3 min, STOP 7 · BOOK 7 · LOCK 4 · TIME 1, **−19,006** |
| **edge_bracket_only** | pullback (retest on expiry day) | none | premium −10 % / +20 %, 30 min max | none | 4.9/day, 41 %, med 12.4 / p90 30.0, STOP 21 · TARGET 9 · TIME 9, **+5,782** |
| **edge_breakout** | 12-min retest breakout every day | buyer edge 0.5 | premium −10 % / +20 %, 30 min max; flat 15:35 (no 15:00 book flatten) | −20 % | 5.6/day, 33 %, med 19.8 / p90 30.0, STOP 28 · TIME 9 · TARGET 8, **−85,387** |
| **edge_gate_trail** | pullback (retest on expiry day) | buyer edge 0.5 | edge_gate_only's exits + −10 % hard premium stop + 20 % / 0.8 / 30-s gain trail | none | 2.5/day, 55 %, med 11.6 / p90 70.4, STOP 9 · BOOK 7 · TRAIL 4, **+28,275** |

Why (config.py:290-320, CHANGELOG 27 Oct): six sessions showed no directional edge and options bought when dear; the
gate (theta vs gamma), the bracket and the day stop were tested on 104 recorded entries. apex_edge = all three; the
others separate the effects; edge_gate_trail = the owner's "giving away too much from the peak" fix (27 Oct evening).
edge_gate_only was champion on 27 Oct; none is champion now (c20_9x).


---

## Part D — The spot breakout, t28 and level-trail books



Scope: 36 paper books: 10 `spot_*`, 6 `lvl_trail*`, 20 `t28_*`. All of it was read from `apex/engine/paper.py`,
`apex/engine_main.py`, `apex/engine/impulse.py`, `apex/engine/daystate.py` and `apex/config.py` as of commit 78be22f.
"Spot" means the Nifty 50 index print. The engine only uses a print it trusts: one that has arrived in the last 5 s
and passes the D-132 basis check against the future.

Every book has the same frame. ₹1,00,000 at the start of each day. All-in on every trade:
`lots = floor(capital / (premium × 65))` (paper.py:1073). One position at a time. Buy only. Fill at LTP, gross.

---

### 0. Rules shared by all 36 books

#### 0.1 The gates before any entry rule runs (`evaluate_entry`, paper.py:813-842)
They are checked in this order, and the first one that fails blocks the entry:
1. The book is already in a position, or an entry is waiting for its fill: no entry.
2. The clock is before **09:25** (`SUPPRESS_UNTIL`) or at/after **15:29** (`LAST_ENTRY`, the "CAS test" value): no entry.
3. The data guard is in blackout (a feed gap, or the resume period after one): no entry.
4. Cool-down: `cooldown_s = 0` in every one of these books, so there is **no cool-down** after an exit.
5. Daily brake (`_daily_brake`, paper.py:756). The only part that can fire is the KILL file (`data/KILL`):
   * the daily loss stop is `DAILY_LOSS_STOP_PCT = 0`, which is off;
   * none of these books has `day_stop_pct`;
   * `no_streak_pause` is set, so there is no losing-streak stop;
   * `no_trade_cap` is set, so there is no cap on entries;
   * `EXPIRY_ENTRY_END = None`.
6. `spot_dc` is set (720 s in all 36 books), so the book goes to `evaluate_spot_breakout` (paper.py:841).

What these books never use:
* the regime gate (`base_gate`);
* the learning loop's gates;
* the futures z-score, synchrony and episode trigger (`m_star`, `s_star`, `L_star`, `d_star` are placeholders);
* THESIS-VOID (in check_exit `S_opp = -1`, so it can never fire).

#### 0.2 After a book signals: picking the contract, vetoes, fill (`engine_main._entry_choice`, engine_main.py:1293-1324)
The steps run in this order:
1. **`choose_contract`** (paper.py:126-173). It picks a CE for an up signal and a PE for a down signal, on the nearest
   weekly (`w0`).
   * A candidate needs a delta, an LTP from **₹20 to ₹600**, and a quote younger than **15 s**.
   * The delta band depends on the days to expiry (calendar days):
     * **≥ 3 days: |Δ| 0.52-0.70**
     * **1-2 days: 0.60-0.80**
     * **expiry day: 0.65-0.85**, on the expiring weekly only (D-108)
   * Inside the band it takes the **lowest |Δ|**, which is the strike nearest the money. If nothing is in the band, it
     takes the lowest |Δ| at or above the band's floor (tagged `band_fallback`).
   * So these books buy ATM-to-ITM: one step ITM on normal days, deeper ITM on expiry day.
   * **On expiry day, no contract is returned at or after 14:45** (`ZERO_DTE_NO_ENTRY`), so no expiry-day entry after
     14:45 in any book.
   * `delta_target = 0.46` (t28_d46, t28_core, t28_core_fill, t28_all, t28_d46_fill): on **non-expiry days only**, it
     takes the strike whose |Δ| is nearest 0.46 among those from 0.42 to 0.52. If none qualifies, the band rule above
     applies (paper.py:159-165). This is ATM or slightly OTM.
2. `cheap_strike`, only in t28_cheapK (see 2.3).
3. `buyer_edge_gate`: needs `gt_min`, which none of these books has. Not used.
4. `reentry_check`, only in books with `reentry` (see 0.5).
5. `flow_veto`, only in t28_ivfall, t28_bidpile, t28_nohigh, t28_req, t28_cheap (see 2.3).
6. **The fill** (`request_entry` / `try_fill_entry`, paper.py:1026-1068).
   * The trade is filled on the **first option print that arrives after the trigger**, at that LTP.
   * If no print comes within **3 s** (`ENTRY_FILL_MAX_S`), or a data gap starts, or 15:29 is reached, the entry
     **lapses**.
   * Lots = floor(capital / (LTP × 65)). If that is under 1 lot, the trade is rejected.

> **A setup is used up when it fires, not when it fills.** The pullback's "once per impulse" mark (`pb_done`), the
> ORB's "once per direction" mark and the retest's armed break are set or cleared inside the entry rule, before the
> contract is picked. So if a veto, the re-entry rule, a missing contract or a lapsed fill stops the trade, the setup
> is **skipped, not queued** (engine_main.py:1309-1323; paper.py:243, 332, 370).

#### 0.3 The exits, in priority order (`check_exit`, paper.py:1133-1273)
Every one of these books has `spot_trail`. Check_exit takes one of two branches.

**Branch F: retest-filler trades (`pos["fill"]`, only the t28 `*_fill` and `t28_all` books)**, paper.py:1163-1171.
* The only price exit is the filler's own premium bracket, on a fresh quote (≤ 5 s): **TARGET at +fill_tgt %
  (10)** and **STOP at −fill_stop % (7)**.
* There is **no** spot trail, lock, gain trail, hard stop, level booking or frozen-spot fallback.
* The clock exits below still apply.

**Branch S: every other trade**, paper.py:1172-1194. The steps are evaluated in this order:
1. **Spot structure exit** (`_spot_trail_exit`, paper.py:697-735). Which one applies depends on how the trade was entered:
   * **Breakout or retest trade:** a **trail of `spot_trail` points (12; 20 in t28_st20)** behind the best spot since
     entry. The first stop is entry spot − 12.
     * It is labelled **`TRAIL` if the best spot was ever above the entry spot (even by 0.1 pt), else `STOP`.**
     * So `TRAIL` **does not mean a profit**. On live data, 173 of spot_dc12_t12's 283 TRAIL exits lost money.
   * **Pullback trade** (`pos["pb"]`): the 12-pt trail is **not** used. Two fixed levels are set at entry and never move:
     * **`STOP (impulse origin X)`** when spot reaches or crosses the impulse origin;
     * **`TARGET (X)`** when spot reaches the impulse extreme + `pb_ext` (1.0) × impulse size.
   * **ORB trade** (`pos["orb"]`): two exits:
     * **`STOP (back through the opening range X)`** when spot crosses the **opposite** edge of the opening range
       (for a CE, the OR low);
     * **`BOOK at <level>`** at the first level fixed at entry that is ≥ `orb_gap` (15) pts beyond the entry spot.
2. **Premium bracket**, only in spot_ft_prem10 (`prem_tgt`):
   * Its result **replaces** step 1's (paper.py:1174-1175), so the spot trail never decides this book's exits.
   * **`TARGET (premium +x %)` at +10 %** and **`STOP (premium −x %)` at −10 %**, on fresh quotes only.
3. **Level booking** (`lvl_book`, `_level_book_exit`, paper.py:376-392). It runs only if nothing above fired.
   * At entry the book fixes the "levels ahead": prior-day high, low and close; the day high and low; the opening-range
     high and low; the round 100s within ±200 of spot. A level counts only if it is ≥ 5 pts ahead (daystate.py:63-81).
   * The levels are walked nearest first:
     * If the best spot so far is from **5 pts short of a level to 5 pts beyond it** (`lvl_near`, `lvl_brk`), and spot
       has since **given back 10 pts** from that best (`lvl_rej`): **`BOOK at <label> <level>`**.
     * If the best is in that zone but has not given back 10 pts: no exit.
     * If the best broke the level by more than 5 pts: the next level is checked.
     * If the best is more than 5 pts short of a level: nothing beyond it is checked.
4. **Hard stop / time stop / breakeven / gain trail** (`_hard_stop_gain_trail`, paper.py:589-634). Checked only on a
   fresh option quote (≤ 5 s). Its result is used only if steps 1-3 gave nothing. Within it, the order is:
   * **`STOP (premium −x %, hard stop −10 %)`**: raw LTP ≤ entry × 0.90 (`prem_hard_stop` 10).
   * **`TIME (no progress …)`**: only with `ts_min_s`. At ≥ 240 s since entry, out if the best raw return so far is
     under +2 %.
   * **`BREAKEVEN`**: only with `be_arm_pct`. The book watches the **30-s average** premium. Once that average has
     been +10 % or more, it exits when the average falls to +1 % or below.
   * **`TRAIL (kept +g % of a +pk % peak gain …)`**: the gain trail. Once the **30-s average** gain has reached
     `gt_arm_pct` (20 %; 8 % in t28_tt8), it exits when the average gain ≤ `gt_keep` (0.8; 0.7 in t28_tt8) × its peak
     gain. Example: a peak of +30 % exits at +24 %.
5. **Profit lock** (`_premium_lock_exit`, paper.py:669-694). Used only if steps 1-4 gave nothing.
   * It arms once the raw LTP is **≥ entry × 1.18** (`lock_pct` 18). From then on it exits when the LTP is **≤ the best
     LTP × 0.90** (`lock_trail_pct` 10): **`LOCK (…)`**.
   * If an exit from steps 1-4 fires while the lock is armed, that exit's reason gets the suffix `(locked +18 % at hh:mm:ss)`.
   * The lock is off in spot_dc12_t12_nolock and spot_ft_prem10 (0 / 0).
6. **Frozen-spot fallback** (paper.py:1186-1193). If the spot quote is **more than 60 s old**, the stop moves to the
   futures mid at `spot_trail` points (from entry, or from the best futures price once that is +12):
   **`STOP (futures: spot quote N s old)`**.
7. **Clock exits** (paper.py:1222-1235), checked only if nothing else fired, in this order:
   * `dte0_max_hold_s` (600): on expiry day, out **10 min** after entry: `TIME (expiry day, max hold 10 min)`.
   * `max_hold_s` (only t28_mh15, 900): `TIME (max hold 15 min)`.
   * `pb_flatten` (15:00, all `_PB`-derived books): `TIME (15:00 book flatten)`.
   * `FLATTEN_AT` 15:35: `TIME (15:35 flatten)`.
   * Expiry day at 15:00: out unless the held option's |Δ| ≥ 0.9: `TIME (0DTE 15:00)`.

**How an exit is filled** (paper.py:1239-1269):
* A price exit is not taken while the data guard is in blackout, or while the **spot** quote is more than 10 s old.
  This holds even for premium exits, because the engine substitutes `spot_age` for the futures age in spot books.
* Once triggered, a price exit is **committed** and filled on the next fresh option print. After 10 s at most, it fills
  at the last price and is tagged `stale_exit`.
* Clock exits fill at once.

#### 0.4 What happens when a trade closes (`close_trade`, paper.py:1324-1356)
* Capital += P&L (₹).
* **One trade per swing:** the trade's best spot and its direction are stored (`swing_last`). A later breakout or
  retest in the **same** direction must see spot go beyond that best first (paper.py:255-259).
  * Only the last trade counts.
  * Pullback and ORB entries do not check this rule.
  * A filler trade never tracks a best spot, so it **does not update** `swing_last`.

#### 0.5 The re-entry chain (`reentry`, `reentry_check`, paper.py:548-583, chain set at 1344-1355)
**When the chain is set.** In books with `reentry`, after these exits:
* `TRAIL…` or `LOCK…` (this kind is called "trailed");
* `STOP…` when `reentry_stop` is set;
* any exit when `reentry_any` is set.

Filler trades never set the chain. Any new trade, in either direction, clears it.

**What it changes**, for a later signal in the **same direction**:
* After `reentry_cheap_s` (1800 s; 600 s in `_c10`) the chain is dropped. A non-trailed chain is also dropped after
  `reentry_fast_s` (600 s).
* Within `reentry_fast_s` (600 s), the new trigger must be **strictly stronger** than the old one, or the signal is
  skipped. Strength means:
  * a pullback: impulse size in points;
  * a retest: how far spot ran beyond the level, in points.
  * If the old trade had a strength and the new signal has none (a filler, or a first-touch break), it is skipped.
* After a trailed exit, for up to 30 min, there is also a price rule. The chosen option's LTP must be **below the old
  exit price**. If it is not, the book tries **one strike further OTM**: quote < 15 s old, LTP ≥ ₹20 and below the old
  exit price. If neither qualifies, the signal is skipped.
* After a stop or any other exit there is no price rule.

---

### 1. The spot-breakout family (`spot_dc12_t12*`, `spot_ft_prem10`; plus the pullback, ORB and dual spot books)

#### 1.1 The base breakout entry (`evaluate_spot_breakout`, paper.py:190-267), in code order
The base parameters are `_SPOT` (config.py:217-220): 12-min look-back, 12-pt trail, swing rule on, retest numbers
5 / 2 / 3 / 300 s, lock 18 / 10.

1. If no 12-min range is available, or spot is missing: wait ("spot range warming"), and drop any armed break.
   * The range is the high and low of trusted 1-Hz spot over the previous **720 s**, leaving out the current second
     (engine_main.py:891-903).
   * It needs at least 80 % of those seconds present. A hole of more than 60 s restarts it.
2. Spot quote older than **5 s**: no entry, and drop the armed break.
3. `spot_expiry_end` (only `_1130`): on expiry day, at or after **11:30**, no entry, and drop the armed break.
4. **If a break is armed (retest books):** let `rel` = how far spot is beyond the broken level, in the break's direction.
   * `rel` < −**3** (`retest_fail`): the level is lost; the break is cancelled.
   * More than **300 s** since arming (`retest_window_s`): the break is cancelled.
   * Not yet extended: once `rel` ≥ **5** (`retest_ext`), it is marked extended. Then keep waiting.
   * Extended and `rel` ≤ **2** (`retest_tol`): **BUY** (`SPOT-RETEST`). In effect the entry is when spot comes back to
     between level − 3 and level + 2 after running 5 pts beyond it. Strength = the furthest it ran beyond the level.
   * While a break is armed nothing else is checked, including a break in the other direction.
5. Break test: spot > 12-min high is up; spot < 12-min low is down. Otherwise, no break.
6. Swing rule (`swing`): a same-direction break needs spot beyond the last trade's best spot.
7. Retest books: **arm** the break at the level it broke (the old 12-min high or low), and do not buy yet.
   **First-touch books** (`retest_ext = 0`): **BUY at once** (`SPOT-BREAKOUT`).

Contract, fill and exits follow sections 0.2 and 0.3. For these books the exits are:
* 12-pt spot trail (`TRAIL` / `STOP`);
* lock 18 / 10 (`LOCK`);
* frozen-spot fallback;
* `TIME (15:35 flatten)`;
* `TIME (0DTE 15:00)` on expiry day.

There is no 15:00 book flatten, so on non-expiry days they can **enter until 15:29** and hold until 15:35. In
practice the vendor index stops updating around 15:15 (D-132), which stops entries.

#### 1.2 Pullback entry (`entry_mode = "pullback"`, `evaluate_pullback`, paper.py:285-337)
The "impulse" is the 45-min (`PB_WINDOW_S` 2700) trusted-spot window kept by `impulse.py`:
* **size** = the window's high − low;
* **direction** = up if the high came after the low, down if the low came last;
* **extreme time** = the earliest time the extreme was printed;
* **deepest pullback** = the furthest spot has retraced since the extreme.

The window starts at the day's first trusted sample. It is valid only with at least 80 % of its seconds present.

The checks run in code order:
1. Spot older than 5 s: no entry.
2. At or after **14:45** (`pb_entry_end`): no entry.
3. `range_gate` and the day is in **range mode**: no entry.
   * Range mode turns on when the day's low-to-high leg is ≥ **100 pts** and spot has given back ≥ **61.8 %** of it.
   * It turns off at a new session high or low (daystate.py:35-58).
4. 45-min window not valid: wait.
5. Impulse size < **60 pts** (`pb_min_range`): no entry.
6. No direction yet: no entry.
7. Less than **30 s** (`pb_min_age_s`) since the extreme: "still extending".
8. `pb_gap_block_s` (120): no entry if the last 45 min (2700 s) contained a data gap of ≥ 120 s. A gap is a blackout
   or a spot quote older than 5 s (`_track_gap`, paper.py:270-282).
9. `pb_min_impulse_s` (1200): no entry if the impulse took **less than 20 min**, measured from the opposite extreme to
   the extreme.
10. This impulse (same direction and extreme time) was already used: no entry.
11. If the deepest pullback went beyond **80 %** of the impulse (0.78 + 0.02 slack): the impulse is "spent".
12. Fire only when spot is now **50 %-78 %** back from the extreme toward the origin (`pb_zone_lo`/`hi`).

**BUY** (`SPOT-PULLBACK`). The impulse is frozen on the position (paper.py:1104-1105):
* **stop** = impulse origin, which is the window low for an up impulse;
* **target** = extreme + 1.0 × size;
* strength = the impulse size in points.

Exits:
* `STOP (impulse origin)` / `TARGET`;
* the lock 18 / 10;
* in the lvl/t28 books also the level BOOK, the −10 % hard stop and the gain trail;
* `TIME (15:00 book flatten)`.

#### 1.3 Opening-range breakout (`entry_mode = "orb"`, `evaluate_orb`, paper.py:348-373)
* The opening range is the spot high and low from the first trusted print (about 09:15) for 2700 s, so to about
  10:00 (`OR_WINDOW_S`).
* Entry rules:
  * No entry after 14:45.
  * Once the range is complete, spot above the OR high buys a CE; spot below the OR low buys a PE.
  * The rule only asks whether spot is outside the range; it does not wait for a fresh cross.
  * **One trade per direction per day.** The direction is used up when the rule fires.
* Exits:
  * `STOP` when spot crosses the **opposite** OR edge;
  * `BOOK` at the first fixed level ≥ 15 pts beyond the entry;
  * the lock 18 / 10;
  * `TIME (15:00 book flatten)`.

#### 1.4 What each spot_* book changes

| book | entry | exits | changes vs `_SPOT` (config line) | why (one line) |
|---|---|---|---|---|
| **spot_dc12_t12** | 12-min break, **retest** 5/2/3/300 s, swing rule | 12-pt spot trail, lock 18/10, 15:35 / 0DTE 15:00 | `expiry_window_exempt` (no effect: `EXPIRY_ENTRY_END` is None) (221) | D-116 + D-131: the first-touch entry bought the first second of a burst |
| **spot_dc12_t12_first** | 12-min break, **first touch** (buy at once), swing rule | same | retest 0/0/0/0 (222) | D-131 twin: the old first-touch entry |
| **spot_dc12_t12_1130** | as spot_dc12_t12, but **no entries on expiry day from 11:30** | same | `spot_expiry_end=(11,30)` (224) | m28 "R3": the expiry-day edge was morning-only |
| **spot_dc12_t12_nolock** | as spot_dc12_t12 | **no lock**: spot trail + clock only | lock 0/0 (225) | D-127 twin: shows what the lock adds |
| **spot_pb45** | **pullback** on every day (sec 1.2), no range gate, no swing | impulse-origin STOP / TARGET, lock, 15:00 flatten | `_PB` (237-240) | D-134: too many trades, entered after the rally was over |
| **spot_dual** | **expiry day: retest** (12-min, 5/2/3/300, swing); **other days: pullback** | pullback trades as spot_pb45; retest trades 12-pt trail + lock; 15:00 flatten | `dte0_retest`, swing on, retest numbers (245) | D-137/D-140: "dual mode by days-to-expiry" |
| **spot_dual_rg** | as spot_dual + **range gate** on the pullback half (expiry retest exempt) | same | `range_gate` (258) | D-141: live −52k on 22 Oct, a range day |
| **spot_dual_lvl** | as spot_dual_rg | + **level BOOK** (5/10/5) | `lvl_book` (267) | D-142: book at a level the trade cannot break |
| **spot_ft_prem10** | 12-min **first touch**, swing rule | **only ±10 % premium** (TARGET/STOP), frozen-spot fallback, 15:35 / 0DTE 15:00; no trail, no lock | from `_first` + `prem_tgt=prem_stop=10`, lock 0 (270) | council 9 T06 "premium-outcome lab" |
| **spot_orb45** | **opening-range breakout** (sec 1.3) | OR-edge STOP, BOOK ≥ 15 pts, lock, 15:00 flatten | `_PB` + `entry_mode="orb"`, `orb_gap=15` (275) | council 9 T08 ORB |

---

### 2. The t28 family (20 books)

#### 2.1 The common base (= `lvl_trail_re`, config.py:340; that is spot_dual_lvl + lvl_trail exits + re-entry)
**Entry**
* **Non-expiry days: pullback** (sec 1.2): ≥ 60-pt 45-min impulse, 50-78 % pullback (never deeper than 80 %), ≥ 30 s
  after the extreme, once per impulse, none in range mode, until 14:45.
* **Expiry day: retest breakout** of the 12-min range (sec 1.1): run 5, back within +2, cancel at −3 or after 300 s,
  swing rule. Range mode does not block it. Entries end 14:45, because no contract is offered after that time on expiry
  day.

**Contract:** the delta band by days to expiry (0.52-0.70 at ≥ 3 days, 0.60-0.80 at 1-2, 0.65-0.85 on expiry day),
nearest the money.

**Re-entry** (sec 0.5): `reentry`, `reentry_stop`, fast 600 s, cheap 1800 s.

**Exits**, in priority order:
1. Spot structure:
   * pullback trades: `STOP (impulse origin)` / `TARGET (extreme + 1 × impulse)`;
   * expiry-day retest trades: 12-pt spot `TRAIL` / `STOP`.
2. Level `BOOK` (5 / 10 / 5).
3. **Hard stop −10 %** on the premium.
4. **Gain trail**: arms when the 30-s average reaches +20 %, exits at 80 % of the peak gain.
5. **Lock** 18 / 10.
6. Frozen-spot fallback.
7. **`TIME (expiry day, max hold 10 min)`**, then `TIME (15:00 book flatten)` / 0DTE 15:00.

#### 2.2 What each t28 book changes, and what it means

The `_G` base (config.py:352) is t28_gap, that is the base + data-gap block.

| book | change (config line) | what it means for trading |
|---|---|---|
| **t28_gap** | `pb_gap_block_s=120` (342) | no pullback entry if a ≥ 120-s data gap occurred in the last 45 min (the impulse may be measured on prices that never traded). Champion 28-29 Oct. |
| **t28_core** | base + `delta_target 0.46`, gap block, `pb_min_impulse_s 1200` (346) | t28_gap + t28_dur20 + t28_d46 combined |
| **t28_ivfall** | `_G` + `iv_fall_rel15 −2` (353) | skip if the chosen contract's IV fell ≥ 2 % (relative) over the last 15 min (paper.py:473-479) |
| **t28_tt8** | `_G` + `gt_arm_pct 8`, `gt_keep 0.7` (372) | a tighter gain trail: arms at +8 % (30-s average), exits at 70 % of the peak gain |
| **t28_mh15** | `_G` + `max_hold_s 900` (371) | out after **15 min** on every day: `TIME (max hold 15 min)` |
| **t28_fill** | base (no gap block) + `rt_fill`, `fill_tgt 10`, `fill_stop 7` (345) | on non-expiry days, if the pullback does not fire, a **retest of the 12-min break** may trade as a "filler" (`SPOT-RETEST-FILL`). Exits: **+10 % / −7 %** premium only, plus the clock. **See ambiguity A1: the filler ignores 14:45, range mode and the gap block.** |
| **t28_d46** | base + `delta_target 0.46` (341) | on non-expiry days, buy the strike with |Δ| nearest 0.46 (from 0.42 to 0.52); otherwise the band rule |
| **t28_d46_fill** | base + d46 + filler (349) | d46 + filler (no gap block, no 20-min rule) |
| **t28_dur20** | base + `pb_min_impulse_s 1200` (343) | the impulse must have taken ≥ 20 min from the opposite extreme to the extreme (no fast spikes) |
| **t28_ts** | base + `ts_min_s 240`, `ts_prog_pct 2` (344) | `TIME (no progress …)` at 4 min if the trade never reached +2 % (raw LTP) |
| **t28_gap_ts** | base + gap block + time stop (350) | t28_gap + t28_ts |
| **t28_bidpile** | `_G` + `skip_bid_pile`, 30 s, 0.007 (354) | skip if the contract's total bid quantity rose ≥ 0.7 % in the last 30 s (a late chase) |
| **t28_st20** | `_G` + `spot_trail 20` (355) | the retest trades (expiry day) trail 20 pts instead of 12; pullback trades unaffected (they use origin/target) |
| **t28_nohigh** | `_G` + `entry_hi5_veto_pct 2` (358) | for pullback/retest entries: skip if the option's mid is within 2 % of its 5-min high mid (needs ≥ 4 min of history) (paper.py:480-487) |
| **t28_req** | `_G` + `req_move_veto`, k 1.0 (359) | find the spot move needed for **+10 % of the ask in 15 min after theta**: 0.5·γ·x² + |Δ|·x = 0.10·ask − θ/min·15. Skip if that move is bigger than the last 15 min's spot range (paper.py:488-500) |
| **t28_cheap** | `_G` + nohigh + req (360) | both checks. **No cheap-strike chooser**, despite the name. Champion 29 Oct morning. |
| **t28_cheapK** | `_G` + `cheap_strike "lag"`, anchor 60 s, expiry day only (363) | on expiry day the book looks at the strikes from ATM to 2 ITM with |Δ| ≥ 0.52. It switches to the one whose ask is furthest below its "fair" value. Fair value = the mid 60 s ago + Δ·dF + ½γ·dF² + θ·dt (paper.py:406-455). |
| **t28_fwd** | `_G` + `spot_src "fwd"` (370) | the whole rule set runs on a **put-call-parity forward**, shifted onto spot by its 30-min median gap to spot, instead of the Nifty index. That covers the 12-min range, the 45-min impulse, spot age and the levels comparison (engine_main.py:855-889, 1213-1218). |
| **t28_core_fill** | t28_core + filler (347) | core + filler |
| **t28_all** | t28_core_fill + time stop (348) | everything in round 1 together |

Why: round 1 came from the 28 Oct 15-member review (scratchpad team/NN), one book per idea plus combinations. Round 2
(ivfall, bidpile, st20) came from the owner's burst, order-flow and greeks ideas. Round 3 (nohigh, req, cheap) came from
"buy only a little cheap". R4-01 is cheapK. The 29 Oct shadows are fwd, mh15 and tt8 (config.py:337-379; CHANGELOG
lines 210-236).

#### 2.3 Detail of the entry vetoes (paper.py:458-508)
* **History.** The option history is 1 Hz, kept 16 min (engine_main.py:1265-1291).
  * If a contract has no history and only the nohigh or req check is on, a one-row history is used. So the nohigh check
    cannot fire, but the req check can.
* **Burned setups.** All the vetoes run after the pullback has marked the impulse "used". A vetoed pullback is
  therefore gone for good.

---

### 3. The level-trail family (6 books)

**Common base: `lvl_trail`** = spot_dual_lvl + hard stop −10 % + gain trail 20 / 0.8 / 30 s (config.py:322).

* Entry: as the t28 base (expiry-day retest, pullback on other days, range gate), **without** re-entry rules.
* Exits: spot structure → level BOOK → hard stop −10 % → gain trail → lock 18/10 → fallback → 15:00 / 0DTE.
* There is **no** 10-min expiry-day max hold in lvl_trail or lvl_trail_be.

| book | change (config line) | meaning |
|---|---|---|
| **lvl_trail** | base (322) | 27 Oct, "giving away too much from the peak" |
| **lvl_trail_re** | + `reentry`, fast 600, cheap 1800, `dte0_max_hold_s 600`, `reentry_stop` (326) | re-entry chain after TRAIL / LOCK (stronger trigger within 10 min + cheaper within 30 min) and after STOP (stronger trigger within 10 min); **out after 10 min on expiry day**. Champion 28 Oct; it is the t28 base. |
| **lvl_trail_rx** | + `reentry_any` (333) | the stronger-trigger rule for 10 min after **any** exit (BOOK, TARGET, TIME, BREAKEVEN too) |
| **lvl_trail_rx_c10** | rx + `reentry_cheap_s 600` (334) | the "cheaper than the exit" rule lasts 10 min instead of 30 |
| **lvl_trail_rx_be** | rx + `be_arm_pct 10`, `be_floor_pct 1` (335) | **BREAKEVEN**: once the 30-s average gain has been ≥ +10 %, out when it falls to ≤ +1 % |
| **lvl_trail_be** | lvl_trail + breakeven (336) | breakeven without re-entry rules and without the 10-min expiry hold |

---

### 4. Exit codes in the trade log (`reason` column; the first word is the code)

| code | exact source and meaning |
|---|---|
| `TRAIL` (plain) | the 12-pt (20-pt) spot trail hit, and the best spot had been above entry at some point. **Can be a loss.** |
| `TRAIL (kept +g % of a +pk % peak gain, 30-s average)` | the premium gain trail (lvl/t28) |
| `STOP` (plain) | the spot trail hit and spot was never better than at entry |
| `STOP (impulse origin X)` | pullback trade: spot back at the impulse origin |
| `STOP (premium −x %, hard stop −10 %)` | lvl/t28 premium hard stop |
| `STOP (premium −x %)` | spot_ft_prem10 −10 % bracket |
| `STOP (filler premium −x %)` | retest filler −7 % |
| `STOP (back through the opening range X)` | ORB opposite edge |
| `STOP (futures: spot quote N s old)` | spot frozen > 60 s; stop on the futures mid |
| `TARGET (X)` | pullback target: spot at extreme + 1 × impulse |
| `TARGET (premium +x %)` / `TARGET (filler premium +x %)` | +10 % bracket (prem10 / filler) |
| `LOCK (px fell y % from best b; armed +18 % at t)` | the profit lock: was ≥ +18 %, then 10 % off the best LTP |
| `BOOK at <label> <level>` | level booking (stalled within 5 pts of a level, gave back 10), or the ORB booking level |
| `BREAKEVEN (was +pk %, now +g %)` | breakeven guard (`_be` books) |
| `TIME (expiry day, max hold 10 min)` | `dte0_max_hold_s` |
| `TIME (max hold 15 min)` | t28_mh15 |
| `TIME (no progress: best +x % in 4 min)` | t28_ts, t28_gap_ts, t28_all |
| `TIME (15:00 book flatten)` | `pb_flatten`, all pullback-type books |
| `TIME (15:35 flatten)` | the global flatten (breakout books) |
| `TIME (0DTE 15:00)` | expiry-day flatten unless |Δ| ≥ 0.9 |
| suffix `(locked +18 % at …)` | the lock was armed when another exit fired |
| `THESIS-VOID` | never in these books |

---

### 5. Per-book summary (live paper trades from `live_stats.json`)

"Total" is the ₹ sum over the live days. Strike = win rate %. Hold is in minutes.

| book | entry (short) | exits (short) | live days | trades/day | strike % | hold med / p90 | top exits | total ₹ |
|---|---|---|---|---|---|---|---|---|
| spot_dc12_t12 | 12-min retest | 12-pt trail, lock | 13 | 23.2 | 37 | 2.1 / 6.4 | TRAIL 283, STOP 16, LOCK 2 | +15,353 |
| spot_dc12_t12_first | 12-min first touch | 12-pt trail, lock | 12 | 42.8 | 37 | 2.1 / 6.5 | TRAIL 488, LOCK 15, STOP 11 | +4,121 |
| spot_dc12_t12_1130 | retest; expiry ≤ 11:30 | trail, lock | 13 | 21.9 | 38 | 2.1 / 6.4 | TRAIL 269, STOP 16 | +85,579 |
| spot_dc12_t12_nolock | 12-min retest | trail only | 13 | 23.2 | 37 | 2.1 / 6.4 | TRAIL 285, STOP 16 | +10,091 |
| spot_pb45 | pullback, every day | origin/target, lock, 15:00 | 12 | 3.8 | 48 | 25.2 / 109.4 | STOP 22, LOCK 18, TIME 4 | −86,066 |
| spot_dual | retest (expiry) / pullback | + 12-pt trail on retests | 12 | 5.7 | 46 | 12.2 / 62.0 | TRAIL 28, LOCK 17, STOP 17 | −55,062 |
| spot_dual_rg | dual + range gate | as dual | 11 | 5.3 | 47 | 9.4 / 95.7 | TRAIL 28, LOCK 14, STOP 11 | −33,309 |
| spot_dual_lvl | dual + range gate | + level BOOK | 11 | 5.5 | 48 | 8.8 / 36.0 | TRAIL 24, BOOK 18, STOP 10 | +35,126 |
| spot_ft_prem10 | 12-min first touch | ±10 % premium | 11 | 32.0 | 52 | 4.7 / 21.9 | TARGET 178, STOP 171, TIME 3 | +2,23,889 |
| spot_orb45 | opening-range break | OR-edge stop, BOOK ≥ 15, lock | 11 | 1.3 | 86 | 24.9 / 106.8 | BOOK 9, LOCK 3, STOP 1 | +82,111 |
| lvl_trail | dual + range gate | lvl BOOK, −10 %, gain trail, lock | 8 | 4.8 | 47 | 8.8 / 61.4 | STOP 14, TRAIL 14, BOOK 8 | +2,743 |
| lvl_trail_re | lvl_trail + re-entry | + 10-min expiry hold | 8 | 4.5 | 50 | 8.8 / 61.4 | TRAIL 13, STOP 12, BOOK 8 | +24,040 |
| lvl_trail_rx | re + stronger-after-any | same | 8 | 4.5 | 50 | 8.8 / 61.4 | TRAIL 13, STOP 12, BOOK 8 | +24,040 |
| lvl_trail_rx_c10 | rx, cheaper 10 min | same | 8 | 4.5 | 50 | 8.8 / 61.4 | TRAIL 13, STOP 12, BOOK 8 | +24,040 |
| lvl_trail_rx_be | rx | + breakeven 10/1 | 8 | 4.5 | 56 | 8.8 / 35.0 | TRAIL 13, STOP 10, BOOK 8, BE 2 | +49,611 |
| lvl_trail_be | lvl_trail | + breakeven 10/1 | 8 | 4.8 | 53 | 8.8 / 35.0 | TRAIL 14, STOP 12, BOOK 8, BE 2 | +28,314 |
| t28_gap | base + gap block | base | 7 | 4.4 | 52 | 8.8 / 35.0 | TRAIL 12, STOP 9, BOOK 7 | +32,510 |
| t28_core | gap + dur20 + Δ0.46 | base | 7 | 3.6 | 44 | 8.7 / 35.0 | TRAIL 12, STOP 9, BOOK 2 | +15,496 |
| t28_ivfall | gap + IV-fall veto | base | 7 | 4.0 | 57 | 8.8 / 35.0 | TRAIL 11, BOOK 7, STOP 7 | +61,558 |
| t28_tt8 | gap | trail 8 % / 0.7 | 7 | 4.4 | 58 | 7.4 / 19.3 | TRAIL 18, STOP 7, BOOK 5 | +41,502 |
| t28_mh15 | gap | + 15-min max hold | 7 | 4.4 | 55 | 8.8 / 15.0 | TIME 10, TRAIL 8, BOOK 6 | +48,503 |
| t28_fill | base + filler | filler ±10/−7 | 7 | 17.4 | 45 | 6.1 / 17.8 | STOP 55, TARGET 40, TIME 10 | +27,245 |
| t28_d46 | base + Δ0.46 | base | 7 | 4.7 | 48 | 8.7 / 35.0 | TRAIL 13, STOP 12, BOOK 6 | +20,352 |
| t28_d46_fill | Δ0.46 + filler | + filler | 7 | 18.9 | 45 | 5.3 / 16.6 | STOP 61, TARGET 43, TRAIL 11 | +17,053 |
| t28_dur20 | base + ≥ 20-min impulse | base | 7 | 3.4 | 42 | 8.8 / 35.0 | TRAIL 12, STOP 8, BOOK 2 | +7,985 |
| t28_ts | base | + 4-min/+2 % time stop | 7 | 4.4 | 52 | 8.7 / 35.0 | TRAIL 12, STOP 8, BOOK 7 | +40,635 |
| t28_gap_ts | gap | + time stop | 7 | 4.4 | 52 | 8.7 / 35.0 | TRAIL 12, STOP 8, BOOK 7 | +40,635 |
| t28_bidpile | gap + bid-pile veto | base | 7 | 4.4 | 52 | 8.8 / 35.0 | TRAIL 12, STOP 9, BOOK 7 | +32,510 |
| t28_st20 | gap | 20-pt spot trail | 7 | 4.4 | 52 | 10.0 / 35.0 | STOP 12, BOOK 7, TRAIL 7 | +16,601 |
| t28_nohigh | gap + not-at-5-min-high | base | 7 | 4.4 | 48 | 8.8 / 35.0 | TRAIL 12, STOP 9, BOOK 7 | +23,611 |
| t28_req | gap + required-move | base | 7 | 3.9 | 52 | 8.8 / 26.5 | TRAIL 12, STOP 7, BOOK 5 | +45,016 |
| t28_cheap | gap + nohigh + req | base | 7 | 3.9 | 48 | 8.8 / 26.5 | TRAIL 12, STOP 7, BOOK 5 | +36,117 |
| t28_cheapK | gap; expiry lag-cheapest strike | base | 7 | 4.4 | 52 | 8.5 / 35.0 | TRAIL 10, STOP 9, BOOK 7 | +36,930 |
| t28_fwd | gap, on parity forward | base | 7 | 5.0 | 46 | 3.3 / 25.7 | BOOK 11, STOP 10, TRAIL 10 | −15,346 |
| t28_core_fill | core + filler | + filler | 7 | 19.1 | 43 | 5.3 / 17.4 | STOP 65, TARGET 46, TIME 10 | +25,649 |
| t28_all | core + filler + time stop | all | 7 | 19.4 | 43 | 5.2 / 16.6 | STOP 63, TARGET 48, TIME 12 | +52,302 |

Live twins that came out **identical**:
* lvl_trail_re = rx = rx_c10 (the extra re-entry rules never bit);
* t28_ts = t28_gap_ts;
* t28_bidpile = t28_gap (the bid-pile veto never fired live).

---


---

## Part E — The controls and the special books




The live figures below come from `live_stats.json`, covering 19 Oct – 6 Nov (14 live days; fade_switch has 13 days, from 21 Oct). "Strike" = % of trades that won. Totals are summed ₹ P&L over all those days.

**Common exits for random_entry, futures_only, premium_momentum and straddle_spike.** All four use the default branch of `check_exit`:
- **STOP**: the futures mid falls 12 pts against the entry futures mid.
- **TRAIL**: arms after +12 pts of best favourable move, then exits 12 pts behind the best.
- **THESIS-VOID**: opposite-side synchrony ≥ 0.5 and z ≤ −1 against the trade, held for 5 s.
- **TIME**: 15:35, or 15:00 on expiry day.

None of them has a max-hold. The cool-down is 60 s for all four.

#### random_entry (control, D-065)

**What it is for.** It tests whether the entries beat chance. It can never be champion.

**Entry** (`evaluate_random_entry`, paper.py:956–979):
- **Schedule.** A fixed schedule per day and book (seeded by "day:name"): a Poisson count with mean **6**, at times spread uniformly between 09:25 and 15:29 (`random_schedule`, line 940).
- **When a slot fires.** At each due slot it fires when all the common checks pass: flat, not pending, in window, no blackout, cool-down over, no kill. Controls skip `base_gate`, the brakes and the learning gates.
- **Missed slots.** A slot missed while blocked is deferred to the next allowed moment. If several are overdue, only the latest fires and the others are skipped.
- **Waits** while more than 240 s of post-gap settling remain.
- **Side.** It takes the sign of the futures' **60-s move** (`fut_r60`). If that move is exactly 0 or missing, it waits.

**Strike**: the standard delta band (§1.3 step 13).

**Exits**: the common 12-pt futures stop/trail, THESIS-VOID at s = 0.5, and TIME.

**Live**:

| Trades/day | Strike rate | Median hold | p90 hold | Total |
|---|---|---|---|---|
| **5.7** (80 trades) | **31 %** | **2.7 min** | **11.5 min** | **−₹1,60,885** |

Exits: STOP 46, TRAIL 30, THESIS-VOID 3, TIME 1.

#### futures_only (control)

**What it is for.** It tests whether the heavyweight basket adds anything. It is the domino trigger with the basket removed (`s_star = 0.0`).

**Entry** (the domino path of `evaluate_entry`, paper.py:851–898). All of these must hold:
- an episode exists (it starts when |15-s futures z| ≥ 1.0 and ends after |z| < 0.5 for 30 s);
- the episode was not born in a data gap;
- this episode has not already been traded;
- the impulse is in the episode's direction;
- **z ≥ 2.0**, where z = 15-s futures-mid change ÷ σ15, and σ15 is never below 5 pts;
- **|15-s move| ≥ 15 pts**;
- synchrony ≥ 0 (always true);
- **not late**: |futures − futures at onset| ≤ **3 × σ15**;
- **ATM IV rise since onset ≤ 1.5 vol pts**;
- no learning gate vetoes (none today).

As a control it skips `base_gate` (regime) and the brakes.

**Strike**: the standard delta band.

**Exits**: the common set, with **THESIS-VOID at `s_exit = 0.5`**: the same synchrony-flip exit as the champion of its time.

**Live**:

| Trades/day | Strike rate | Median hold | p90 hold | Total |
|---|---|---|---|---|
| **17.2** (241 trades) | **36 %** | **1.3 min** | **5.3 min** | **−₹31,473** |

Exits: STOP 129, TRAIL 96, THESIS-VOID 16.

#### premium_momentum (control)

**What it is for.** It tests whether straddle_spike's theta model adds anything. It buys a straddle leg on its *raw* 5-min rise.

**Entry** (`evaluate_momentum_entry`, paper.py:998–1023):
- **Settling.** No entry while any post-gap settling remains (300 s after a gap lifts).
- **Threshold** = max(**4.0 pts**, **6 % × the current straddle price**).
- **Candidates.** A leg (CE or PE of the anchored straddle strike, see straddle_spike) qualifies when:
  - it is *armed*;
  - its 5-min change is ≥ the threshold;
  - its |delta| rose by **≥ 0.03** over 5 min.
- **Choice.** The leg with the larger 5-min rise is bought.
- **Disarming.** Firing disarms that leg (even if the fill later lapses). It re-arms when its 5-min change drops below half the threshold.
- **Gates.** Learning gates are checked (none today). There is no regime gate and no brake (control).

**Strike**: that leg at the straddle's anchor strike K (`spike_leg`):
- the nearest weekly;
- LTP 20–600;
- quote < 15 s old;
- not on expiry day at/after 14:45.

There is no delta-band check.

**Exits**: the common set.

**Live**:

| Trades/day | Strike rate | Median hold | p90 hold | Total |
|---|---|---|---|---|
| **22.7** (318 trades) | **39 %** | **2.3 min** | **8.7 min** | **+₹2,346** |

Exits: TRAIL 163, STOP 146, THESIS-VOID 8, TIME 1.

#### RAW

**What it is for** (learning.py:6–7). It is the champion *without promoted gates*, so every advisor's would-have verdict can be scored on an ungated path.

**Today.** `RAW` = a copy of **c20_9x's** parameters, including `council: "c20_9x"`. So it runs through the **council adapter, exactly like the champion**:
- No `evaluate_entry`, base gate or learning gate is involved.
- The fill and all-in rules are as in §1.4.
- Its own rules are documented in the council section.

Checked on 3, 4, 5 and 6 Nov in `data/paper`: RAW's trades match c20_9x's one-for-one (12 / 5 / 1 / 3 trades).

**Live**:

| Trades/day | Strike rate | Median hold | p90 hold | Total |
|---|---|---|---|---|
| **10.0** (140 trades) | **39 %** | **2.7 min** | **24.2 min** | **+₹51,886** |

Exits: TRAIL 69, STOP 17, THESIS-VOID 12, BOOK 9, FWD_TRAIL 9.

**These live figures mix every champion RAW has copied since 19 Oct** (the domino books, then the spot books, then the t28 books, then c20_9x from 30 Oct), so they do not describe one rule set.

#### straddle_spike (owner's idea, 17 Oct evening)

**What it is for.** When the fixed-strike ATM straddle rises *above its theta decay*, buy the leg carrying the rise (its delta is rising).

**The watch** (`straddle_watch.py`):

- **Anchor.**
  - K is the ATM strike: the strike nearest the put-call-parity forward of the nearest weekly (engine_main.py:732–740).
  - K is kept fixed. It re-anchors only after the ATM has differed by ≥ 2 strikes for 120 s, or by any amount for 600 s (lines 152–160).
  - A re-anchor ends any live spike.
- **Measured once a second** on that pair:
  - straddle S = CE + PE. Each leg uses its mid when the spread is ≤ max(8 % of ask, ₹1), else its LTP.
  - chg5 = S − S five minutes ago.
  - expected5 = (θ/min CE + θ/min PE) × 5.
  - **excess = chg5 − expected5**.
- **Threshold.** thr = max(**4.0 pts**, **6 % of S five minutes ago**, **2.5 × σ**).
  - σ is a running average of |excess| learned only in quiet time.
  - σ starts at 1.5 and has a 20-min half-life.
  - σ is never below 0.5 inside the formula (lines 196–202).
- **A directional spike starts** (lines 216–224) when all of these hold:
  - excess ≥ thr;
  - the rising leg's 5-min change is ≥ 60 % of chg5;
  - the other leg's change is ≤ 35 % of the rising leg's;
  - at least **90 s** have passed since the last spike ended.
- **A spike ends** when any of these happens:
  - it is 20 min old;
  - after 60 s the leg is back at or below its start;
  - the leg gave back half its gain (once the gain is ≥ 2 pts);
  - excess stays < 40 % of thr for 60 s;
  - the ATM rolls.
- **Vol spike.** If both legs rise, it is a "VOL-SPIKE": no trade.
- A 5-min history on the anchor is needed first ("WARMING").

**Entry** (`evaluate_spike_entry`, paper.py:901–926), after the common checks. All must hold:
- a live spike;
- not already traded (**one trade per spike**);
- the spike was not born in or within 300 s after a data gap;
- **spike age ≤ 150 s**;
- the carrying leg's |delta| rose **≥ 0.03** over 5 min;
- **`base_gate` (regime) passes**, judged in the leg's direction;
- learning gates pass.

It is not a control, so the brakes would apply, but all of them are off.

**Strike**: the spiking leg at strike K (`spike_leg`, paper.py:100–123):
- the nearest weekly;
- LTP 20–600;
- quote < 15 s;
- not on expiry day at/after 14:45.

There is no delta-band check.

**Exits**: the common set.

**Live**:

| Trades/day | Strike rate | Median hold | p90 hold | Total |
|---|---|---|---|---|
| **3.0** (42 trades) | **36 %** | **1.7 min** | **10.4 min** | **−₹25,044** |

Exits: TRAIL 23, STOP 18, THESIS-VOID 1. Average win was ₹18,857 and average loss −₹11,404.

#### fade_switch (D-121, council 4 member m14 "P1 vol switch"; shadow "as evidence only")

**What it is for.** A fast follow-or-fade rule on 15-s futures bursts. The council harness called it FRAGILE.

**Parameters**:
- `imp_pts 10`
- `range_follow 60`
- `tp_pts 12`
- `sl_pts 12`
- `max_hold_s 180`
- `cooldown_s 60`
- `no_streak_pause`, `no_trade_cap` and `expiry_window_exempt` are all set (all moot: those brakes are OFF anyway).

**Entry** (`evaluate_fade_switch`, paper.py:637–653), after the common checks:
1. It needs the 15-min futures high-low range. That is None until about 13.5 min (0.9 × 15 min) of in-session 1-Hz history exists (engine_main.py:918–923).
2. It needs **|15-s futures-mid move| ≥ 10 pts**.
3. **If the futures' 15-min high-low range is ≥ 60 pts, it FOLLOWS** the move (buys in its direction). **Otherwise it FADES** it (buys the opposite side).

It uses no episode, no synchrony, no regime gate and no learning gates. Each fire has its own id, so it can fire again as soon as the 60-s cool-down ends.

**Strike**: the standard delta band.

**Exits** (`_bracket_exit`, paper.py:656–666), on the futures mid, measured from the futures mid at the fill:
- **TARGET**: +12 pts in favour.
- **STOP**: −12 pts against.
- **HOLD-LIMIT**: 180 s after entry.
- Then the clock exits: 15:35, and 15:00 on expiry day.
- There is no trail and no THESIS-VOID (lines 1195–1197, 1206).
- The fills follow §1.4.

**Live**:

| Trades/day | Strike rate | Median hold | p90 hold | Total |
|---|---|---|---|---|
| **54.0** (702 trades) | **50 %** | **1.3 min** | **3.0 min** | **−₹7,816** |

Exits: STOP 281, TARGET 276, HOLD-LIMIT 145.


---

## Part F — Things found while writing this guide

None of these were changed. They are listed so they can be decided on. **Verified** means checked against the code
and/or the live records while assembling this guide; **from the code reading** means found by the reader of that
family and not yet independently re-checked.

### Behaviour that looks unintended

| # | Finding | Books | Status |
|---|---|---|---|
| F1 | **Filler books trade after the entry cut-off.** The retest filler trades whenever the pullback rule says "no", for any reason, including "too late". It enters after 14:45, and even after 15:00, where the 15:00 book flatten closes it a second later (paper.py:204–207). Live: 29 Oct 14:54 (flattened 15:00), 30 Oct 15:00–15:14 (several, each closed within 1–2 s), 2 Nov 14:45 and 15:12, and more. | t28_fill, t28_all, t28_core_fill, t28_d46_fill | **verified** (live records); **fixed 7 Nov**: the filler now respects the 14:45 end, range mode, a stale spot and the data-gap block (`paper._pullback_closed`; tests in test_c13_team.py). Cost before the fix: 41 late trades, −₹43,293 across the four books |
| F2 | **A council clock exit waited for a print.** The strategy's own 15-min (expiry) or 90-min (normal) clock exit is logged "COUNCIL TIME …"; the exit-fill code filled at once only reasons starting with "TIME", so it waited up to 10 s like a price exit. | all council books | **verified**; **fixed 7 Nov** (owner): "COUNCIL TIME" fills at once, like the forced flat |
| F3 | **The council adapter checks \|delta\| ≥ 0.5, while its comment says 0.52** (council/__init__.py:204). The council strike pickers already enforce 0.52, so 0.52 is the rule in practice. | council books | **verified** (code) |
| F4 | **Two books could buy out of the money.** They bought the straddle's anchored strike with no delta check. | straddle_spike, premium_momentum | **verified**; **fixed 7 Nov** (owner): `spike_leg` requires \|delta\| ≥ 0.52 (`config.MIN_ABS_DELTA`) |
| F5 | **A stale direction after an "unaffordable" entry.** When lots < 1 the restored direction was not cleared, and could override the next episode's direction. | domino books | **verified**; **fixed 7 Nov**: `try_fill_entry` clears the trigger keys when `open_trade` rejects the fill |
| F6 | `t28_cheapK` measures the "lag" move on the futures mid, not the parity forward its description names. | t28_cheapK | from the code reading |
| F7 | `t28_fwd` reads range mode and the levels from the index, but compares them with its forward-based spot. | t28_fwd | from the code reading |
| F8 | The council premium trail used when the forward is frozen (STALE_PTRAIL) uses the base 25/40-pt trail, not the delta-scaled one; and the premium trail's peak is not saved across a same-day restart. | council books | from the code reading |
| F9 | **Two books buy below the 0.52 delta floor by design.** t28_d46 and t28_d46_fill target \|delta\| ≈ 0.46 (0.42–0.52) on non-expiry days (`delta_target`, paper.py choose_contract). This contradicts the ATM/ITM rule; raised with the owner 7 Nov. | t28_d46, t28_d46_fill | **verified** (code) |

### Things to know when reading trade logs

| # | Point |
|---|---|
| K1 | **Times.** Until 7 Nov entries ran to 15:29 and the general flatten was 15:35 (the 19 Oct closing-session test). **From 7 Nov (owner): 15:15 / 15:25.** The council books flatten at 15:00 (expiry) / 15:20 regardless. |
| K2 | **"TRAIL" is not always a win.** On spot books it means the 12-pt spot trail fired: 173 of spot_dc12_t12's 283 TRAIL exits lost money. On domino books it means the trail had armed. |
| K3 | **A lapsed entry can re-trigger.** An episode or setup is marked used only when the fill happens. A lapsed fill, or "no contract in band", leaves it free to fire again (premium_momentum is the exception). On spot books, a veto, a re-entry block or a lapsed fill uses the setup up for good. |
| K4 | **The kill switch (data/KILL) does not stop an entry already waiting for its fill**; it can still fill within its 3 s. |
| K5 | **Price exits can wait** while the futures quote is more than 10 s old or the data guard is frozen. The 10-s cap only limits the wait for a fresh option print. On spot books even premium exits wait while the spot quote is stale. |
| K6 | **Some books trade identically.** Live, these pairs have had the same trades so far: lvl_trail_re = lvl_trail_rx = lvl_trail_rx_c10; t28_ts = t28_gap_ts; t28_bidpile = t28_gap; m2.0_s0.5_ivinterp = m2.0_s0.5; c20_9e = c20_9h (no expiry day yet since they started); RAW = c20_9x (RAW is a council copy of the champion). The m1.5 and m2.0 books often take the same entries, because the 15-pt impulse floor binds before the z threshold. |
| K7 | **Council take-profit is set to +990 %**, i.e. effectively off; profits are taken by the trails and floors. |
| K8 | **A same-day restart reloads each book's saved parameters**, so a mid-day config change only reaches the books the next day. |

### The readers' raw notes

The full notes from each family's code reading follow, for anyone checking the details.

#### Ambiguities / things to know

1. **What counts as a "print".** A "print after the trigger" is any feed update of that contract. Its age is measured from the moment the feed last *received* the contract, not from an exchange trade time. A bid/ask-only update can therefore complete a fill at an LTP that has not changed.
2. **Spike legs can be out of the money.** straddle_spike and premium_momentum buy the leg at the *anchored* strike K with no |delta| check. Because K lags the ATM (by up to 1 strike for 10 min, or ≥ 2 strikes for 2 min), the leg bought can be OTM, against the ATM/ITM intent.
3. **A lapsed entry can fire again at once.** If an entry lapses (no print within 3 s), nothing marks the setup as used. The domino episode is only marked traded at the fill, the random slot stays due, and fade_switch fires again if the burst persists. The next step can re-trigger. premium_momentum is the exception: its leg stays disarmed.
4. **Pending entries ignore the kill switch.** An entry already pending can still fill within its 3 s after the KILL file appears.
5. **Price exits can wait without limit.** A price exit (STOP/TRAIL/TARGET/THESIS-VOID) waits indefinitely while the futures quote is > 10 s old or the guard is frozen. The 10-s cap only limits the wait for a fresh *option* print. TIME exits always go through.
6. **No prices means no exits.** If both the futures and spot prices are missing, the step returns before any book is checked, so no exits run that step.
7. **Possible stale direction after an "unaffordable" entry.** If `open_trade` refuses an entry because lots < 1, the control keys restored from the pending entry (including `dir`) are not cleared. For a domino-path book a stale `dir` would then override the domino direction on the next fire. This is rare (it needs capital < LTP × 65) and looks like an oversight, not a rule.
8. **Restarted books keep their old parameters.** A same-day restart reloads each book's *saved* parameters, so a `config.py` change mid-day reaches the books only the next day.
9. **RAW's live stats mix rule sets.** RAW has copied five champion families since 19 Oct. Today it is simply a twin of c20_9x.
10. **The 15:29 / 15:35 times are a test.** They are marked "[TESTING — owner, 19 Oct 2026]" in config.py; the production values were 15:15 / 15:25.


#### 5. Ambiguities and quirks found in the code

1. **Strategy clock exits are not filled "at once".** `try_fill_exit` treats a reason as a clock exit only if it
   starts with `TIME` (`paper.py:1296`); the strategy's clock is logged `COUNCIL TIME`, so it waits for a fresh print
   (≤ 10 s) like any other exit. Only the forced flat fills immediately. Possibly unintended.
2. **Delta check 0.5 vs 0.52.** The adapter tests |delta| ≥ 0.5 (`__init__.py:204`) though its comment says 0.52; the
   strike pickers enforce 0.52, so the effective rule is 0.52.
3. **STALE_PTRAIL uses the base trail** (25 / 40 pts), not the delta-scaled trail, and it is not switched off when the
   expiry premium trail is armed — the trail value is restored before the `l2` block runs (`c20_9x.py:371-376, 420`).
4. **Premium-trail memory is not restart-safe.** `peak_bid` (floors) is saved on the position, but the PREM_TRAIL
   smoothed bid and its peak (`sb`, `spk`) live only in the strategy object; after a mid-trade restart they start
   again from the current bid. Likewise the strategy's history (`fs`, range window, pullback arm, last-loss record)
   starts empty in a new process, so after a restart there is a fresh warm-up (10 / 20 min) before any entry —
   inferred from the code, not observed.
5. **The flip gate judges "loss" on the bid at the exit-signal second**, not on the actual fill price.
6. **Normal-day arm age is not refreshed** by later same-side breakouts: the 900-s expiry (and c20_9s's 660-s rule)
   count from the first arming second.
7. **TP exists but is off** (`tp = 9.9` → +990 %).
8. The t28_gap parameters attached to every council book (e.g. `prem_hard_stop` 10, `dte0_max_hold_s` 600,
   `lvl_book`) are inert; the dashboard may still show some of them elsewhere.


#### 6. Ambiguities and code-vs-intent gaps

* **A1. The retest filler is not stopped by 14:45, range mode or the gap block.**
  * In `rt_fill` books the filler runs whenever `evaluate_pullback` returns "no", for **any** reason (paper.py:204-207).
    That includes "after 14:45", "range mode" and "data gap".
  * Nothing else stops entries until 15:29. So the filler buys after 14:45, and also **after 15:00**, where the next
    step closes it at once with `TIME (15:00 book flatten)`.
  * Seen live: t28_fill 30 Oct 15:03:51→15:03:52 and 15:14:34→15:14:35; 2 Nov 15:12; 4 Nov 15:12 and 15:14; 6 Nov
    15:03. The same happened in t28_all, t28_core_fill and t28_d46_fill.
  * This is probably unintended: the retest is meant to be a "filler" inside the pullback's hours.
* **A2. Fillers and the re-entry rule.**
  * A filler clears its strength (`trig_str`), so it cannot pass the "stronger" rule within 10 min of a trailed or
    stopped trade that had a strength. It is skipped.
  * Fillers also never set a chain, and never update the swing mark.
* **A3. The cheap-strike chooser measures dF on the futures, not the forward.** `lag_cheapness` reads
  `ohist["fwd"]`, which the engine fills with `ctx["fut"]`, the Nifty-futures mid (engine_main.py:1286-1291). The
  docstring says "forward".
* **A4. "TRAIL" can be a loss.** The spot trail is labelled TRAIL as soon as the best spot was ever above the entry
  spot by any amount.
* **A5. A veto, re-entry block or lapsed fill uses the setup up** (sec 0.2 note). A pullback impulse or an ORB
  direction is not retried.
* **A6. A stale spot quote delays premium exits too.** In spot books a premium exit (hard stop, lock, gain trail)
  waits while the spot quote is more than 10 s old (paper.py:1246-1249). Before that, the hard stop and lock need a
  fresh option quote (≤ 5 s).
* **A7. Strength comparisons can mix units.** The re-entry "stronger" test compares the raw strength numbers. A
  pullback's impulse size and a retest's run beyond the level are both in points, but they measure different things.
  The comparison is same-day and same-direction only.
* **A8. t28_fwd only partly switches to the forward.** It reads range mode and the levels list from the **index**
  (`ctx["day"]` is not overridden) but compares them with forward-based spot. The forward is shifted by its median gap,
  so the mismatch is small but non-zero.
* **A9. "total" is taken from live_stats.json as given.** The JSON is assumed to be summed P&L over live days, not
  recomputed here.
