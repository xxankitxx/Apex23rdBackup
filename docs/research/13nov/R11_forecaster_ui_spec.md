# R11. The forecaster UI: a clear stand, a first-person plan, honest numbers (13 Nov)

Owner, 12 Nov: "very user-unfriendly, unable to grasp through eye, the code does not tell me what to do, nothing grasps
my attention, dull". 13 Nov: "just mentioning a +- range does not help, the system has to take a clear stand, inform how
the market is behaving, I have not seen the system's personal commentary on what it would do at that point of time".

Mock: `data/research/13nov/work/R11/mock.html` (open it in a browser, no network needed). Six moments: 13:46 flat with
no setup (today's real numbers), setup armed, buy fires, holding in profit, close to the exit, forecaster stale.

## Findings first

1. **The panel said WAIT all day.** On 13 Nov from 09:20 to 13:46 the flat read was WAIT except for 35 seconds
   (TILT TO CALLS, 10:49:46 to 10:50:21). A word that never changes is the "dull" the owner sees.
2. **While holding, it flickered.** During the 12:36 to 13:19 25200 PE trade the read flipped HOLD and WATCH 8 times in
   25 minutes, each time on ₹1 to ₹3 of premium around the entry price. The 30 s hold in `_feed_step` does not stop
   this; the boundary itself (in profit or not) is the problem.
3. **It never says what the account will do.** The verdict is built only from the forecaster's 2-minute lean and the
   premium versus entry. The thing that actually decides trades (the c20 trigger: push, pullback, turn) is not exported
   to the page at all. So the panel cannot say "I would buy the 25200 CE at about 153 after a pullback to 25,207".
4. **A 5 or 15-minute stand has no forecasting skill, and the panel must not pretend it has.** Walk-forward on 16 days
   (tables below): every stand I tried is right about 50 % at 15 minutes and 51 % at 5 minutes, better than half on
   only 8 or 9 of 16 days. So the stand is shown as a *description* of the market (who is in control, how strongly)
   with its measured record next to it, never as "68 % chance up".
5. **The forecaster cannot feed the action card.** Today its loop p95 reached 12.3 s (11:30), it skipped 4,815 seconds
   and was stale about 52 minutes (stale counter 392 s at 11:30 to 3,519 s at 12:31, the outage). The engine stayed
   live. The first trade of the day (10:53 to 11:03) happened while the forecaster was skipping and the panel never
   acknowledged it. The plan card must come from the engine.
6. **A trend "stand" is not a trade filter.** Pool-book trades whose side agreed with the trend stand won 66 % early
   and 36 % late; against it, 55 % early and 67 % late. The sign flips (same as the 2-minute lean in docs/54). Display only.

## Teardown

### What the page shows now (apex/static)

| Where | What it does | Where it fails |
|---|---|---|
| `index.html:93` `#labglance` | Five chips: next 5 min range, decay, which way 2 min, forecaster's read, age | The range chip leads; the read chip is WAIT almost all day |
| `index.html:96-100` `#fcsec` | Section title says "display only, the Conductor does not read it"; `#labplain` holds the hero | The first words a viewer reads are a disclaimer, not a stand |
| `app.js:1779-1803` `labPlain` | Hero: verdict word, `confidence:` word, head sentence, Nifty with `±N pts in 5 min` (`app.js:1796`), ladder, feed, option board, four plain rows | Confidence is "untested today" until 20 independent direction checks (today `dir_checks` 0.2 at 13:27), so the hero always carries a non-answer |
| `app.js:1732-1746` `fxLadder` | Three range bars with `±N` on the right (`app.js:1742`) | This is the "+- range" the owner rejects; it is correct but says nothing about direction or action |
| `app.js:1751-1768` `fxOption`, `app.js:1800` | "Where each option may be": expected premium and 8-in-10 range | The middle premium forecast is no better than "no change" (docs/54); at 13:27 the 25100 CE ask 166.65 had an expected 167.11 in 5 min. It looks like information and is not |
| `app.js:1831-1856` `labGlance` | Chips rebuilt each poll | The read chip copies the same WAIT |
| `style.css:1627-1635` `.fx-hero` | Tone by left border and tint | Only `good`, `bad`, `warn`; there is no "armed" state, so nothing ever turns gold before a buy |
| `app.js:663-740` position band, `renderCouncilRail` | Already shows the council floor, peak bid, stop and trail while holding | The best in-trade guidance on the page sits in the band, not in the Forecast section, and is not written as "I sell if ..." |

### Where the words come from (apex/forecast_lab/core.py)

| Line | What | Problem |
|---|---|---|
| `core.py:75` `LEAN_SD = 0.15` | one lean threshold | At 13:27 the 2-min mean was +0.29 on an sd of 14.62 (z 0.02): "no lean" is the normal state |
| `core.py:2526-2584` `verdict()` | flat: CALLS FAVOURED, TILT TO, or WAIT from the 2-min lean only; held: HOLD if bid ≥ entry else WATCH / UNDER PRESSURE | Flat read ignores the c20 setup; held read flips on the sign of (bid − entry), so ₹1 of noise around entry flips it |
| `core.py:2516` `_conf()` | high / medium / low from today's hit rate after 20 checks | Most of the day: "untested today" |
| `core.py:1648-1690` `_feed_step(hold_s=30)` | a new read must hold 30 s before the feed shows it | 30 s is shorter than the premium noise cycle; 8 flips in 25 min got through |
| `core.py:1559-1560` regime | trending if vr > 1.25 and er > 0.3, choppy if vr < 0.8, else mixed | At 13:27 vr 1.62 (trend-like) with er 0.07 (choppy) gave "mixed"; the market word turned mixed / choppy / mixed three times in 33 min |
| `core.py:2587-2627` `ladder()`, `board()` | 5 / 15 / 30-min ranges and premium forecasts | Both are ranges; neither takes a side |

### The c20 trigger is invisible (apex/engine/council)

`c20_08.py:150-180` `_pullback` and `c20_8x.py:179-205` (the `pbg` geometry used by c20_9y) keep the arm in
`self.arm = [side, base, extreme, pullback extreme, armed index]`: arm on a breakout of the 20-minute range with at
least 40 points of 20-minute velocity (`c20_08.py:38`: W 1200, L 1200, vmin 40, pb 0.5, rs 5), buy after a 50 % to
75 % retrace (`PB_DMAX` 0.75) and a 5-point resumption, drop the arm after 900 s (`PB_AMAX`). Exits
(`c20_08.py:110-127` plus docs/20 §4): −15 % premium stop, 40-point forward trail scaled 0.8 to 1.0 by delta, 90-minute
clock, break-even floor after +15 %. None of the arm state reaches the dashboard payload, so the page cannot say
"armed, waiting for a pullback to X". The engine works on the parity forward, so the card should quote that number
(labelled "Nifty") and not the futures mid.

## Evidence

All scripts in `data/research/13nov/work/R11/`. Data: `data/forecast_lab/collect/*.joblib` (16 days, 19 Oct to 11 Nov),
one origin every 30 s from 09:30 to 15:15, forward move of the futures mid after 5 and 15 minutes. Origins 30 s apart
overlap: a full-day stand is about 23 independent checks a day at 15 minutes.

### Can the panel take an honest 5 or 15-minute stand? (`stand_study.py`, `strength_study.py`)

Discover 19 Oct to 4 Nov (12 days), test 5, 6, 9, 11 Nov. Hit = the stand's side was right; cov = share of the time a
stand was taken.

| Variant | Horizon | Test days, hit (coverage) | Mean hit | Days above 50 % |
|---|---|---|---|---|
| Logistic on 17 market features, call at p ≥ 0.55 | 5 min | 47 % (33), 48 % (23), 57 % (27), 45 % (29) | 49.4 % | 1 of 4 |
| same, p ≥ 0.60 | 5 min | 33 % (7), 43 % (1), 62 % (3), 67 % (4) | 51.3 % | 2 of 4 |
| same, p ≥ 0.55 | 15 min | 39 % (37), 59 % (28), 60 % (35), 43 % (43) | 50.2 % | 2 of 4 |
| same, p ≥ 0.60 | 15 min | 42 % (10), 69 % (5), 84 % (7), 43 % (10) | 59.4 % | 2 of 4 |
| same, p ≥ 0.65 | 15 min | 46 % (2), none, 100 % (2), 100 % (2) | (2 to 4 independent checks) | not testable |
| Rolling refit each day (from day 6), p ≥ 0.60 | 15 min | 11 days | 52.8 % | 7 of 11 |
| Rule: above VWAP, 30-min momentum up, Kalman slope up (and mirror) | 15 min | all 16 days, no fitting | 52.4 % | 9 of 16 |
| Rule: above VWAP and 10-min momentum up (and mirror) | 15 min | 16 days | 51.5 % | 9 of 16 |
| **The mock's strength stand** (20-min slope and VWAP side, enter ±40, leave ±20, hold 90 s) | 15 min | 16 days | **49.9 %** | **8 of 16** |
| same | 5 min | 16 days | 50.8 % | 9 of 16 |

In-sample the logistic looked good (60.7 % at 5 min, 63.6 % at 15 min, p ≥ 0.60). Out of sample it fell to a coin.
Variants tried: 17 (14 in `stand_study.py`, 1 in `strength_study.py`, 2 in `stand_vs_trades.py`). The one cell above
60 % has 5 to 10 % coverage and 2 to 7 independent checks a day: noise.

The strength stand is right on trend days and wrong on turn days. Points gained in its direction over 15 minutes:

| Day | Stand BULL / BEAR share | 15-min hit | Points in its direction |
|---|---|---|---|
| 21 Oct | 3 % / 71 % | 59 % | +10.8 |
| 22 Oct | 40 % / 24 % | 31 % | −15.3 |
| 27 Oct | 41 % / 32 % | 37 % | −13.7 |
| 29 Oct | 71 % / 4 % | 63 % | +10.3 |
| 6 Nov | 74 % / 0 % | 65 % | +17.3 |
| 9 Nov | 35 % / 31 % | 44 % | −6.4 |

This is the owner's point 3 in numbers: a rule that decides the same way every day is right on some days and wrong on
others. The stand is useful to *read* the market, not to *predict* it.

Stand stability with the hysteresis: median 14.5 changes a day (9 to 20), about 2.5 an hour. The stand is BULL or
BEAR 54 % to 75 % of the day, so it does take a side most of the time. Without hysteresis the logistic stand changed
state 4 to 8 times an hour.

### Does agreeing with the stand make a trade better? (`stand_vs_trades.py`)

Pool books c20_9y, 9s, 9v, 9x, 9t in `trades_all_books.parquet` (the same trade often appears in several books, so n
overstates independent trades). Stand at the trigger: VWAP z and the 20-bar slope both on the trade's side ("with"),
both against ("against"), mixed (0).

| Window | Stand | Trades | Won | Mean return | Median |
|---|---|---|---|---|---|
| 19 Oct to 4 Nov | with | 106 | 66.0 % | +11.8 % | +5.5 % |
| 19 Oct to 4 Nov | against | 97 | 54.6 % | +9.6 % | +0.9 % |
| 5 to 12 Nov | with | 45 | 35.6 % | 0.0 % | −8.7 % |
| 5 to 12 Nov | against | 54 | 66.7 % | +5.7 % | +8.0 % |

The sign reverses between windows. Not a rule (reject). It also confirms the card must not say "the stand agrees, so
this trade is better".

### What the panel did today (live, `data/forecast_lab/log_2026-11-13.txt`, payload feed)

| Item | Value |
|---|---|
| Flat read other than WAIT, 09:20 to 13:46 | 35 seconds (TILT TO CALLS) |
| Held read flips, 12:38 to 13:19 | 8 (HOLD / WATCH), on ₹1.1 to ₹3.4 of premium |
| Market word changes, 12:24 to 13:27 | 5 (mixed / choppy / mixed / choppy / mixed) |
| Forecaster loop p95, worst | 12.3 s at 11:30 |
| Skipped seconds by 13:41 | 4,815 |
| Stale seconds, 11:30 to 12:31 | about 3,130 |
| Failed writes of the dashboard file | 965 |
| Conductor today | 10:53 25200 CE −12.4 %, 12:36 25200 PE −7.1 %; capital 82,317 |

## The spec

Everything below is display only. The Conductor still decides every trade. Nothing new is read by the engine.

### Layout (top of `#fcsec`, above the ladder and the option board)

1. **Stand banner** (fixed 148 px). Three columns; one column under 640 px.
   * Left: "MY STAND" label, the word (BULLISH, BEARISH, SIDEWAYS; 44 px Chakra Petch 700 in the side colour), "since
     13:57 · held 8 min", the strength number (−100 to +100, signed, 24 px) with the words "strength out of 100 (how
     one-sided the market is, not a chance)", and a centre-zero meter (sellers left, buyers right).
   * Middle: "HOW THE MARKET IS BEHAVING": one or two plain sentences in 17 px (see "Behaviour sentence" below) and up
     to 7 fact chips: futures, VWAP and distance, push size, day high / low distance, heavyweights up by Nifty weight,
     BANKNIFTY against Nifty, straightness. Chip border green if the fact supports the stand, coral if against.
   * Right: "HOW SURE I AM": next 2 min (lean with its record, 60 % on the strongest fifth, docs/54), next 15 min
     ("coin toss, my record 50 %"), the normal 5-minute move (the ± range lives here now, in one line), decay paid or not.
2. **What I would do now** (min height 262 px), first person, from the engine:
   * verb pill: WAIT, GET READY · CALLS / PUTS, BUYING · 25200 CE, HOLD · 25200 CE, CLOSE TO EXIT, SELLING.
   * a 2 to 3 sentence paragraph in 18 px: what I would do, at what price, and why.
   * the three-step progress (Push, Pullback, Turn) with the live numbers: "needs 40 pts in 20 min · best now 29",
     "wait for 25,207 to 25,193 · now 25,232", "5 pts up from the pullback low".
   * a plan row of four boxes: buy price, premium stop (−15 %), Nifty trail level, floor or clock.
   * while holding: a horizontal rail stop · entry · now · floor · best bid with the bid as a dot.
3. **What would change my mind**: 3 to 5 lines, each a price level or time with what happens there
   ("Nifty above 25,215 within 20 minutes: a call setup arms"; "No pullback by 14:19:40: the setup expires").
4. **Strength through the day**: the strength as a green / coral area around zero, ±40 dashed, futures line on the
   right scale, gold shading while a setup is armed, the account's entries (▲ CE, ▼ PE) and exits with their return.
5. **My record strip**: four cards with sample sizes: 2-minute lean 60 %, 15-minute stand 50 %, Conductor trades won
   53 % (in sample before 9 Nov), live days in profit.
6. Below: the existing ladder and feed, then the option board, then the folded notes. The glance row's first chip
   becomes the stand ("BULLISH +64"); the range chip moves to the end.

### Strength (display formula)

Every second, from numbers the forecaster already has (`signals`, `breadth`, `regime`) or the engine has:
`raw = 100 × (0.65 × tanh(20-min move / 40) + 0.35 × tanh(VWAP distance in 10-min volatility units))`, smoothed
`S += 0.25 × (raw − S)`. Optional later (untested, Phase B): add `0.15 × tanh(weighted heavyweight move / 10)` and
`0.10 × tanh(BANKNIFTY lead)`, keeping the weights summing to 1. The stand word: BULLISH when S ≥ +40, BEARISH when
S ≤ −40, back to SIDEWAYS only when |S| < 20, and any change must hold 90 seconds. These are the numbers in
`strength_study.py`: 14.5 changes a day, and 50 % at 15 minutes, which the banner says out loud.

### Behaviour sentence (template, core.py side)

Pick the first that applies, fill with numbers:
* push in progress: "Buyers took over at 13:47: Nifty climbed 54 points in 17 minutes, crossed VWAP and broke the
  25,200 ceiling of the last hour."
* fading: "The push is fading: Nifty peaked at 25,284 at 14:41 and has given back 26 points. Banks turned down first."
* range: "Nifty has gone sideways for 48 minutes between 25,150 and 25,200. It is sitting on VWAP. Nobody is in control."
* add the heavyweight clause by Nifty weight: "HDFC Bank and ICICI Bank lead" (top two weighted contributors over 2
  minutes, from `breadth` and the engine's heavyweight tile), and BANKNIFTY ahead / behind.

### "What I would do now" (engine side, the honest part)

New display-only field in the engine's dashboard payload, `council_watch`, for the pool book that would own the next
trade (c20_9y first, then 9s, 9v, 9x, 9t, the Conductor's priority order), written once a second:

```
{book, side, state: "wait" | "armed" | "fired",
 base, extreme, pull_extreme, armed_t, expires_t,              # from self.arm
 push_now: best 20-min move, push_need: vmin,                   # for the "needs 40, best now 29" line
 band_hi, band_lo: extreme − pb × imp, extreme − PB_DMAX × imp,  # pullback band
 off_level: same as band_lo,                                     # beyond it the arm is dropped
 turn_need: rs, turn_now: resumption so far,
 cand: {strike, side, ask, delta} from _pick at that moment,
 stop_px: ask × (1 − sl), trail_pts: 40 × delta factor, clock_s: hold}
```

While holding, the card reads the existing `p.rules` (floor_px, peak_bid, sl_pct, be_arm_pct, pt_arm_pct; `app.js:663`)
plus the trail level in Nifty points (best forward − trail). The card's sentences are templates over these numbers
only. The vetoes of c20_9y (IV, spread, `c20_9y.py:22`) are named when they block: "I would have bought, but the spread
is too wide (veto)".

Cost: a dict of 20 numbers once a second per pool book. Measure with the perf log before it goes live (memory: live
step-time check).

### In-trade words without flicker

Replace HOLD / WATCH on the sign of (bid − entry) with distance to the nearest exit, in Nifty points:
HOLD while the nearest exit is more than one normal 5-minute move away; CLOSE TO EXIT inside one move (amber);
SELLING when an exit fires; PROTECTED once the break-even floor is armed. Change only on a 60-second hold. It cannot flip on ₹1 of premium around entry, which caused the 8 flips on 13 Nov 12:38 to 13:19; it would have
turned CLOSE TO EXIT only as Nifty came within one normal move of the trail that sold the trade at 13:19 (not replayed).

### Speed and errors

* The action card renders from the engine's file (1 Hz, under 1 s a step). The stand banner renders from the
  forecaster file with its age; past 20 s it greys (`filter: saturate(.25)`, dashed border) and says "last read 11:31,
  21 min old"; the action card keeps working.
* Fixed heights for the banner (148 px) and the card (262 px); words change in place (the existing `labPut` keeps
  unchanged nodes). No animation except the gold glow on BUYING and the existing 300 ms flash.
* Every new render function wrapped in `labTry` (`app.js` existing pattern), so one failing part never blanks the panel.

## Ideas

| # | Idea | Mechanism | Test result | How to build | Risk |
|---|---|---|---|---|---|
| 1 | Stand banner (word, strength, behaviour, how sure) | Describes who is in control with hysteresis; states its record | Tested as a forecast: 49.9 % at 15 min, 8 of 16 days; stable (14.5 changes a day). As a display it is honest because it says so | core.py `stand()` from existing signals, app.js `fxStand`, CSS per mock | Viewer reads BULLISH as "buy". Mitigated by the "how sure" column and the card |
| 2 | "What I would do now" from the c20 arm state | The card says what the Conductor will actually do and at what levels | Untested as profit (it is the Conductor itself). Phase B `phaseB_armed_card.py` measures how often it says GET READY, fire rate and 15-min move after a fire | engine `council_watch` field (display only), app.js card | Engine payload grows; measure step time first |
| 3 | Exit-distance in-trade words | HOLD / CLOSE TO EXIT / PROTECTED from the rule levels | Untested; removes the cause of today's 8 flips by construction (needs a replay of the held seconds) | core.py `verdict()` held branch or a JS function over `p.rules` | None for trading |
| 4 | "What would change my mind" lines | Price levels where the arm, the stand or an exit changes | Untested (display) | templates over `council_watch` and the stand thresholds | Levels shift every second; round to whole points and update only on a 1-point change |
| 5 | Strength-through-the-day chart | Shows when the market was one-sided and where trades sat | Untested (display) | SVG, 1 point a minute, kept in the forecaster's state | None |
| 6 | Record strip with samples | Every percentage is a measured record | n/a | from `walk_forward.json`, `strength_study.json`, account | Must be refreshed nightly |
| 7 | Demote the ± range and the premium "expected" | They are correct but say nothing; the middle premium is no better than no change | docs/54 | move `fxLadder` and the board under the card; label the board "ranges only" | None |
| 8 | Trend agreement as an entry filter | Reject | Early with 66 % won, late 36 %; sign flips | none | Overfitting if adopted |
| 9 | Heavyweight and BANKNIFTY clause in the behaviour line | Names who moves Nifty, by weight | Untested; weight into strength is a Phase B question | `breadth.hw120`, `bank120`, the engine's heavyweight tile | Stale stock ticks; show age |

## Phase B scripts (ready, not run)

| Script | What it answers | Inputs |
|---|---|---|
| `work/R11/phaseB_armed_card.py` | Rebuilds the c20 NORM arm on the futures mid for 16 days: share of the entry window the card would say GET READY, arms and fires per day, fire rate after arming, median arm-to-fire time, and the 15-minute move after each fire (early vs late days). These are the numbers the card would quote ("of 9 setups I armed today, 3 fired") | `data/forecast_lab/collect/*.joblib`, `data/replay/batch/p44_sim*/conductor_sim.json` |

Already run (scratch, small): `extract.py` (cache of 16 days at 30 s), `stand_study.py`, `strength_study.py`,
`stand_vs_trades.py`; results in `stand_study.json` and `strength_study.json`.
