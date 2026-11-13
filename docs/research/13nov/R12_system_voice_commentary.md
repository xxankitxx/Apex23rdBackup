# R12: The system's own voice (owner point 4)

Lens: the commentary the system gives about what it would do. Files read: `apex/engine/commentary.py`,
`cmt_entry.py`, `cmt_hold.py`, `cmt_basket.py`, `apex/engine/ideas/`, `apex/engine/conductor.py`,
`apex/engine/council/` (c20_08, c20_20, c20_8x, c20_9x, c20_9s, c20_9y, c20_9v, c20_9t), `apex/engine/missed.py`,
`apex/engine_main.py`, `apex/static/app.js`, `apex/static/commentary.js`, `docs/11_COMMENTARY.md`, the live tapes
of 11, 12 and 13 Nov and the 17 replayed days (run p44). Scratch work: `data/research/13nov/work/R12/`.

## Findings first

1. **The system never speaks in the first person.** 0 of 38,074 remarks (17 replayed days plus 11 to 13 Nov live)
   use "I", "my" or "me". 38 % of the replay and 11 to 12 Nov remarks say "you" or "your". The panel was built on 20 Oct for an owner who trades by hand
   ("instil more and more confidence in me to hold"). Since 9 Nov the Conductor trades by itself, and the voice was
   never pointed at it. The tests even forbid it: `tests/test_c5_cmt_hold.py:107` bans the words hold, sell and buy,
   and `tests/test_c5_commentary.py:21` bans them as instructions. A system that may not say "I will sell" cannot say
   what it would do.
2. **When flat, it says nothing.** The commentary only runs while the account holds (`commentary.py:468-496`); the
   panel is removed when flat (`commentary.js:205`, "flat: the panel does not exist"). The account is flat 45 to 89 %
   of the entry window (median 68 %, 17 days). While flat, the top line shows `conductor.reason` raw: on 11 Nov it
   logged "flat: no eligible trigger" 356 times and nothing else (`conductor.py:175`, `app.js:392-422` has no
   translation for it).
3. **The voice describes a different system from the one trading.** The verdict uses the old spot-trail width of
   12 points (`commentary.py:538` reads `spot_trail` of the conductor book, which is 12.0 because the conductor
   inherits t28_gap parameters), and `cmt_hold.py:129` only uses the council trail when the book itself has
   `council` set, which the Conductor does not. The real exits are a 40-point forward trail, a -15 % stop, a ramp
   floor from +15 % and a 90-minute clock. So EXIT-SOON fires on a 3 to 4 % premium wobble. **Every one of the 119
   replayed Conductor trades got an EXIT-SOON verdict, winners and losers alike** (63 of 63 winners, 56 of 56 losers).
4. **The verdict has no edge, and obeying it would have destroyed the profit.** Tested on the late days (5, 6 and
   9 Nov, 27 trades, per-second bids): selling at the first EXIT-SOON raises the strike rate from 15/27 to 19/27 but
   cuts the compounded return from +182 % to -1 %. It sells the runners: +71.6 % became +3.1 %, +61.1 % became
   +14.5 %, +41.4 % became -0.4 %. After an EXIT-SOON the held bid still rose a median +0.35 % over the next 5
   minutes (after HOLD: +1.63 %). The owner saw "EXIT-SOON" 22 times during the 12 Nov 11:12 trade that the system
   held for 70 minutes and closed at +10.7 %.
5. **It is noise by volume.** 18.6 remarks a minute while holding; 23 % are warnings; the verdict changes 28 times per
   10 minutes (median); 76 % of warnings arrive within 10 s of a confident remark (6,023 of 7,880). 10 % of remarks
   quote 19 Oct base rates from a spot book that no longer trades. 1,580 remarks (3.9 %) print a missing number,
   almost all "the stop is — away", because the Conductor has no spot stop (`warn.stall_long`, `cau.giveback`,
   `cau.lull`).
6. **Everything needed for a real voice already exists in engine memory, unpublished.** The c20 strategy objects hold
   the full trigger state every second: the arm (side, impulse base, extreme, pullback extreme, armed second), the
   smoothed forward, the 20-minute high and low, the velocity, each veto's margin, and the exit levels. My
   never-holding replica of that trigger reproduced **10 of 10 Conductor triggers within 3 s** on 4 to 6 Nov.
7. **The trigger has a readable "distance".** On 4 to 6 Nov the account was IDLE 52 to 67 % of the window, ARMED
   (impulse done, waiting for the pullback) 29 to 42 %, and in the firing ZONE only 1 to 2 %. From the ZONE it fired
   within 5 minutes 80 to 100 % of the time; from IDLE about 1 to 3 %. That is the honest "how close am I" the owner
   asked for (pilot, 3 days, calibration test is Phase B).
8. **The pool is one signal with five names, and the vetoes leak.** All five pool books fire on the same second (the
   Conductor log shows 4 "lost_priority" rows at almost every trigger). c20_9y owns 95 of 119 trades. When c20_9y
   refuses a trigger (IV rich or OI wall), the c20_9x clones still fire and the next one takes it: 13 such
   trades, 2 won (early 0 of 9, late 2 of 4). The owner is never told "c20_9y refused, c20_9s took it anyway".

## Teardown

### What the code does in my area

| Piece | Where | What it does | Where it fails the owner |
|---|---|---|---|
| Commentary engine | `apex/engine/commentary.py:439-648` | While the champion holds: builds about 115 facts each second, picks at most 1 remark a second and 3 per 10 s from 209 templates, keeps a HOLD / WATCH / EXIT-SOON verdict | Silent when flat (`:468`). Addresses "you". Verdict thresholds in spot-trail units (`:538`) |
| Verdict | `commentary.py:334-378` | Highest level among about 15 rules wins | Giveback rule `:346` fires at best >= 6 premium points and 60 % given back; the Conductor's real trail is 40 forward points. Stop rules `:341`, `:350` never fire for council books (no `stop_spot`) |
| Hold content | `apex/engine/cmt_hold.py` | 115 hold facts, give-back ladders, stall warnings | `:129` trail falls back to 12 for the Conductor; `warn.stall_long` (`:831`) says "no trade survived a stall" from 19 Oct while the Conductor's normal-day clock is 90 minutes |
| Entry content | `apex/engine/cmt_entry.py` | Entry grade A to E, 59 templates | Grades the fill against 19 Oct spot-book stats ("On 19 Oct, D-entries: 2/4 won") |
| Basket content | `apex/engine/cmt_basket.py` | Heavyweight attribution since entry | Produces half of all remarks (1,143 of 2,164 on 12 Nov), often both "a wave your way" and "more weight against you" inside 10 s |
| Ideas board | `apex/engine/ideas/` (16 cards) | Independent observers of the owner's older ideas, "each one on its own, no combined score" | None of them describes the Conductor's own trigger. i11 arm-fire is a spot compression idea the research rejected |
| Conductor | `apex/engine/conductor.py:139-200` | Mirrors the first pool book whose trigger passes its rule | Its only flat words: "flat: no eligible trigger" / "flat: data blackout" (`:175`, `:172`). Rule blocks, lost priority and releases go to the file only |
| Conductor view | `engine_main.py:1732-1740` | `members`, `reason`, `owner`, `src` | No trigger state, no veto state, no exit levels |
| Council exit rules | `council/__init__.py:225`, `:273-319` | `pos["rules"]`: stop price, forward trail level, floor, clock, premium trail. Copied to the Conductor in `conductor.py:282` | Computed every second, labelled "dashboard only", but the verdict ignores them |
| Flat twins | `missed.py:239-256` | Deep copy of each council strategy run as if flat while the real book holds | Already the "what would trigger now" engine; only used for the missed-signal tape |
| Dashboard flat line | `app.js:431-438`, `humanReason` `:392-422` | Shows `s.reason` | Falls through to the raw text. `councilEntry` (`:378-383`) says "resumed with velocity v pts" but for a pullback entry `v` is the 20-minute net move at the resumption second (11 Nov 13:20: "v=-0") |
| Dashboard Conductor text | `app.js:450-454` | One fixed paragraph about the pool | Never changes with the market |
| Commentary panel | `commentary.js:157-206` | Feed, verdict card, entry and review cards | Hidden when flat; the verdict card shows the misleading level |

### Why the owner has not seen first-person commentary

1. The design target was a human trader (docs/11 opening quote, 20 Oct). "You entered costly", "That is what you just
   bought".
2. The honesty rules turned into tests that ban action words. They stop the system from saying what it will do.
3. The commentary only exists while holding. Two-thirds of the session has no voice at all.
4. The engine's trigger state lives inside private strategy objects (`eng._council_ad[name].strat`) that nothing
   publishes. The UI cannot say "impulse 32 of 40" because it never receives 32 or 40.
5. When the champion changed to the Conductor (9 Nov) the commentary kept treating it as a spot-trail book.

## Evidence

All scripts are in `data/research/13nov/work/R12/`. Strike rate first, returns in percent, all-in compounding.

### E1. Tape audit (`s1_tape_audit.py`, `s5_missing_vals.py`)

| | Replay, 17 days | Live, 11 and 12 Nov |
|---|---|---|
| Conductor trades | 119 | 7 |
| Minutes held | 1,819 | 184 |
| Remarks | 33,822 | 3,251 |
| Remarks per minute | 18.6 | 17.7 |
| Warnings | 7,880 (23 %) | 777 (24 %) |
| Verdict changes, median per 10 min | 28.2 | 15.4 |
| Trades with at least one EXIT-SOON | 119 of 119 | 7 of 7 |
| Warnings within 10 s of a confident remark | 6,023 | 599 |
| Remarks quoting "19 Oct" | 3,486 | 307 |
| Remarks in the first person | 0 | 0 |
| Remarks with "you / your" | 12,856 | 1,267 |

13 Nov live so far (to 13:19): 2 trades (-12.4 %, -7.1 %), 1,001 remarks, 0 in the first person; the Conductor log
shows 166 "no eligible trigger" and 56 "data blackout" minutes.

Missing values (all 40,896 remarks of all tapes): 1,580 (3.9 %). Top: `warn.stall_long` 454 ("The stop is — away"),
`cau.giveback` 354, `cau.lull` 151, `warn.giveback_half` 133.

EXIT-SOON does not separate winners from losers (replay): winners 63/63 had one (median 12 % of the hold spent in
EXIT-SOON, first one at a median 152 s), losers 56/56 (3 %, 170 s).

### E2. Obeying the verdict (`s2_verdict_obey.py`, test days 5, 6 and 9 Nov, per-second bids from ds_v2)

Two variants tried: sell at the bid one second after the first EXIT-SOON; the same but only after 120 s of holding.

| Policy | Trades | Won | Mean per trade | Compounded |
|---|---|---|---|---|
| Actual (the system's own exits) | 27 | 15 | +5.83 % | +182.0 % |
| Sell at the first EXIT-SOON | 27 | 19 | +0.36 % | -1.1 % |
| Same, only after 120 s | 27 | 18 | +0.66 % | -1.9 % |

Information test: held bid change over the next 300 s (capped at the trade's exit) after each verdict change.

| After | n | Mean | Median | Share up |
|---|---|---|---|---|
| HOLD | 253 | +2.62 % | +1.63 % | 0.58 |
| WATCH | 323 | +2.43 % | +1.24 % | 0.57 |
| EXIT-SOON | 106 | +2.64 % | +0.35 % | 0.53 |

Verdict: the verdict is a worse exit rule than the one trading, and as a signal it is close to useless. It should not
be shown as advice. This is 3 days and one window; the full 16-day run is Phase B (`phaseB_verdict_obey.py`).

### E3. The trigger as a readable state (`s4_arm_phases.py`, pilot 4 to 6 Nov)

Replica check: observer fires against the Conductor's own triggers.

| Day | Observer fires | Conductor triggers | Matched within 30 s (all were within 3 s) |
|---|---|---|---|
| 4 Nov | 6 | 5 | 5 |
| 5 Nov | 2 | 1 | 1 |
| 6 Nov | 5 | 4 | 4 |

The extra observer fires happened while the account was already holding.

Share of the window by phase: IDLE 0.52 to 0.67, ARMED 0.29 to 0.42, ZONE 0.01 to 0.02, IMPULSE printing 0.03 to 0.05.

Chance the trigger fires within N minutes, by phase and progress (pooled, 3 days, every second counted, so the
seconds are strongly dependent):

| Phase | Progress | Seconds | 5 min | 10 min | 15 min |
|---|---|---|---|---|---|
| IDLE (20-min move / 40) | 0 to 0.5 | 19,819 | 0.01 | 0.06 | 0.12 |
| IDLE | 0.5 to 0.8 | 7,577 | 0.03 | 0.09 | 0.18 |
| IDLE | 0.8 to 1 | 6,576 | 0.03 | 0.11 | 0.22 |
| ARMED (pullback / 50 %) | 0 to 0.5 | 11,311 | 0.08 | 0.16 | 0.19 |
| ARMED | 0.5 to 0.8 | 6,759 | 0.12 | 0.21 | 0.27 |
| ARMED | 0.8 to 1 | 3,381 | 0.23 | 0.23 | 0.23 |
| ZONE (resumption / 5 pts) | 0 to 0.5 | 629 | 0.80 | 0.80 | 0.80 |
| ZONE | 0.5 to 0.8 | 126 | 1.00 | 1.00 | 1.00 |

Not a profit claim: this is what the voice may honestly say about closeness. The walk-forward calibration (learn on
19 Oct to 4 Nov, check on 5 to 11 Nov, Brier score against a constant) is `phaseB_arm_phases.py`.

### E4. Is the account ever blind? (`s3_blind_time.py`, 17 days) Refuted.

Hypothesis: a pool book holding its own shadow copy cannot arm, so the Conductor might be flat while all five books
hold. Result: while the Conductor was flat (3,442 minutes), all five books were flat and able to fire 99.3 % of the
time. Books enter and exit together. No idea here; it confirms the pool is one signal.

### E5. Vetoes leak through the pool (`s6_owner_handoff.py`, 17 days)

Trades the Conductor took from a book other than c20_9y, when c20_9y was flat (so it refused):

| Group | Window | Trades | Won | Compounded |
|---|---|---|---|---|
| c20_9y refused, the c20_9x clones fired, the next one took it | early (19 Oct to 4 Nov) | 9 | 0 | -65 % |
| same | late (5 to 12 Nov) | 4 | 2 | +4.9 % |
| only c20_9t or c20_9v fired (their own timing) | early | 7 | 5 | +16.8 % |
| same | late | 3 | 2 | -5.0 % |

The early window is in sample (c20_9y's vetoes were found on those days, docs/23). The late window is 4 trades on 3
days (9 Nov -16.6 %, 11 Nov +23.4 % and -7.9 %, 12 Nov +10.7 %): out of sample the leak made money. One variant tried. Not promotable; a shadow candidate (I3).

## Ideas

### I1. The Conductor's voice (display only). Highest priority.

Mechanism: a new observer `apex/engine/voice.py`, class `Voice`, stepped once a second right after
`_conductor_step` inside `_safe("voice", ...)`, never read by any decision. It reads the strategy objects of the pool
books, the Conductor, `pos["rules"]` and the flat twins, and writes one small block `state["voice"]`. The dashboard
puts its headline where the flat line is today (`app.js:431-438`) and its exit ladder where the verdict card is
(`commentary.js:145`).

It takes a stand in the system's own terms (the trigger it actually trades), not a forecast. Example lines, every
number from engine state:

| Mode | Example |
|---|---|
| WAITING | "I am flat. The forward has moved +18 of the 40 points I need in 20 minutes and sits 9 points under its 20-minute high. The market is ranging: 20-minute range 28 points. On past days I fired within 10 minutes from here about 1 time in 10." |
| IMPULSE | "The impulse is printing: forward +46 in 20 minutes, a new 20-minute high. I do not buy the breakout. I wait for a pullback of 23 points, then a 5-point turn back up." |
| ARMED | "Armed for a CALL since 11:02 (impulse 46 points). The pullback is 12 of the 23 points I need. If it falls past 34 points I drop the idea. The arm expires at 11:17." |
| ZONE | "Ready. Pullback 26 points (57 %). I buy the 25300 CE, about 211, 6 lots, the moment the forward turns up to 25,241. From here I fired within 5 minutes 4 times in 5." |
| VETO | "c20_9y refuses this one: ATM IV is 4.1 points above its median, rich line 3.5. c20_9s will take it anyway; the pool has no common veto." |
| HOLDING | "I hold 6 lots of the 25350 PE, +4.2 %, peak +8 %. I sell at the first of: forward back up to 25,276 (31 points away, about 17 premium points), bid 189.97 (the -15 % stop), 15:20. My floor arms at +15 %. Nearest exit: the forward trail." |
| EXITING | "My forward trail fired at 12:22:24. I am selling at the next print." |
| CLOSED | "Sold at 247.45, +10.7 %, on the forward trail after 70 minutes. Next I need a fresh 40-point impulse." |

Test result: untested as a display. Its input was tested: the replica reproduces 10/10 triggers (E3).
Risk: low. It is an observer; a fault is caught by `_safe` and only empties the block. Cost: a few scalar reads plus
one `wall_ahead` scan (about 80 strikes) and one median, under 0.3 ms at 1 Hz if the median is cached every 10 s
(today `commentary` costs 1.07 ms a step and `ideas` 1.22 ms, `perf_2026-11-12.jsonl`).

### I2. Replace the verdict with the real exit ladder (display only)

Mechanism: the HOLD / NEAR / EXITING level comes only from `pos["rules"]`: distance to the stop price, to the
forward trail level, to the floor, to the clock and the flat time. NEAR = the nearest exit is within 25 % of its
distance at entry. EXITING = `pos["pending"]`. Retire `verdict_of` from the panel (keep it in the tape for study).
Evidence: E2 shows the old verdict is a worse exit rule than the real one. Risk: none to trading.

### I3. Shadow book: a binding pool veto (profit idea, shadow only)

Mechanism: when the highest-priority pool book refuses a trigger with a named veto (c20_9y iv_rich or oi_wall,
c20_9s stale_impulse), the Conductor does not hand the same trigger to the next book on the same second.
Build: a Conductor twin (`conductor_v` book) with `step()` reading `books[m].strat.blocked` deltas this second, or
simpler, a flag in `conductor.py:178-195` that drops lower-priority members whose trigger second equals a vetoed
higher member's signal second. Evidence: E5, early 0/9 (in sample), late 2/4 and +4.9 % (out of sample, against the idea).
Risk: it would have removed the 11 Nov +23 % and 12 Nov +10.7 % winners; fails the promotion standard (no second window). Phase B can widen it.

### I4. Clean the old commentary (display only)

* Drop every template whose numbers come from the spot stop when `stop_spot` is None (1,580 broken remarks).
* Remove the 19 Oct reference rates or recompute them on the Conductor's own 119 trades.
* One remark per 20 s at most, and never a warning and a confident remark about the same thing within 30 s.
* Point the trail width at `pos["rules"]["trail_pts"]` when the position has `rules` (fixes `cmt_hold.py:129` and
  `commentary.py:538`).
* Change the tests so first-person statements of the system's own rule are allowed ("I sell if ...") while advice to
  the owner stays banned.

### I5. Same-side and opposite-side re-triggers while holding (untested)

Mechanism: the flat twins (`missed.py`) already run the trigger while the account holds. A same-side fire is a reason
the voice can give for holding; an opposite-side fire is a warning it can give with evidence. Test:
`phaseB_retrigger_hold.py` (2 variants). Until it runs this is display wording only, not an exit.

### I6. Fix the entry wording (display only)

`councilEntry` (`app.js:378-383`) should say "impulse X points, pullback Y, resumed 5" for pullback entries.
The `v=` in the `why` string (`c20_08.py`, the BUY return) is the 20-minute net move at the resumption second, so 11
Nov 13:20 read "velocity -0 pts". Display only; the `why` string itself is used by rules (`rules.entry_pattern`), so
add new fields, do not change it.

## Data contract: engine state to the UI

`state["voice"]`, written at 1 Hz by `Voice.view()`, about 1.5 KB. **NEW** = a new display-only field.
Everything else is read from existing engine objects.

```
voice = {
  v: 1, t, time,                                   NEW (block)
  mode: WAITING | IMPULSE | ARMED | ZONE | PENDING | HOLDING | EXITING | CLOSED | STOOD_DOWN | OFF   NEW
  headline: str, lines: [str] (<= 4)               NEW (first-person text built from the fields below)
  stand: {dir: UP|DOWN|NONE, word, range_pts, move_pts, why}         NEW, from strat.fs / qmax / qmin
  trigger: {
    mode: normal | expiry                          exists: D.dte0 (council/__init__.py LiveDay)
    side                                           exists: strat.arm[0], or the side whose v is larger
    move_pts, need_pts, window_s                   exists: strat.fs[i] - strat.fs[i - p["L"]], p["vmin"], p["L"]
    hi, lo, edge_gap_pts                           exists: strat.qmax[0][1], strat.qmin[0][1]
    impulse_pts                                    exists: |arm[2] - arm[1]|
    pullback_pts, pullback_pct, need_pct, max_pct  exists: arm[2], arm[3]; p["pb"] (0.5); strat.x["PB_DMAX"] (0.75)
    resume_pts, resume_need, fire_level            exists: fs - arm[3]; p["rs"] (5); NEW fire_level = arm[3] +/- rs
    arm_since, arm_expires                         exists: arm[4]; min(p["W"], x["PB_AMAX"]) (900 s)
    stale_after                                    exists: c20_9s SI["PB_AGE_MAX"] (660 s)
    cool_left_s                                    exists: p["cool"] - (i - strat.last_exit)
    window_left_s                                  exists: p["t1"] (15:00 normal, 14:40 expiry)
    progress, p_fire_10m, base_n, base_dates       NEW (constant table from phaseB_arm_phases.json)
  }
  books: [ {book, ready, veto, margin, text} ] in Conductor priority order
    c20_9y iv_rich: strat._y_avg[i] - median(_y_avg[_y_st:i]) vs Y["IVR"]      exists (median: NEW 10-s cache)
    c20_9y oi_wall: c20_9y.wall_ahead(D, i, side, 250) vs 25                   exists (function)
    c20_9s stale_impulse: i - arm[4] vs 660                                    exists
    seq veto (all): strat.last (ret, side, i) and SEQ_S 900                    exists
    stale forward (l2): strat.fage >= r["FS"]                                  exists
    busy: books[name].pos / ctl["pending_entry"]                               exists
  would_buy: {book, rr, strike, ask, delta, lots, cost_rs}
    strike: c20_08 _pick logic (|delta| target 0.52 normal, tie score expiry)  NEW display copy (do not call the
            live strat._pick: c20_8x "rw" writes self.blk)
    ask, delta: ctx["by_key"], eng.greek                                       exists
    lots: conductor capital // (ask * LOT_SIZE)                                exists (conductor.py _open)
  hold: {book, key, bid, ret_pct, peak_pct, nearest, level: HOLD|NEAR|EXITING,
         exits: [ {kind: SL, px, away_px}, {kind: FWD_TRAIL, fwd_level, fwd_now, away_fwd, away_px_est},
                  {kind: FLOOR, armed, arms_at_pct, px}, {kind: PREM_TRAIL, armed, px}, {kind: CLOCK, left_s},
                  {kind: TIME, at} ],
         twin: {same_side_fired, opposite_armed} }
    all exits: pos["rules"] (council/__init__.py:273-319, copied by conductor.py _follow)   exists
    away_px_est = away_fwd x |delta|                                           NEW
    twin: eng.missed.twins[name] (missed.py:239-256)                           exists
  last_event: {event, book, why, time}            NEW: Conductor keeps its last 5 log rows in memory
}
```

Two engine additions, both display only: `Voice` itself, and a `recent` deque of 5 rows in `Conductor._log`
(`conductor.py` keeps writing the file as now). No decision code changes.

UI changes (display only): the flat line (`renderVerdict`, `app.js:431`) shows `voice.headline` and a trigger gauge
(move vs 40, pullback vs 50 to 75 %, resumption vs 5, with the fire level); a five-chip row for the books (ready or the
veto with its margin); while holding, the commentary verdict card is replaced by the exit ladder; the old remark feed
moves under a "Notes" fold.

## Phase B scripts (ready, not run; after 15:30, same rules)

| Script | What it answers | Inputs |
|---|---|---|
| `work/R12/phaseB_verdict_obey.py` | E2 on every ds_v2 part (16 days), per day and per window, strike rate first | ds_v2, p44 commentary tapes |
| `work/R12/phaseB_arm_phases.py` | Walk-forward calibration of the voice's "chance I fire within 5/10/15 min" (learn 19 Oct to 4 Nov, test 5 to 11 Nov, Brier score vs a constant), phase shares per day, replica match on all days, expiry breakout mode included | ds_v2, conductor_sim |
| `work/R12/phaseB_retrigger_hold.py` | I5: same-side and opposite-side triggers while holding, early and late windows | ds_v2, conductor_sim |

All use `work/R12/r12_observer.py` (the replica of the c20 trigger).

## Multiple testing

Profit-related variants tried: 4 (two "obey EXIT-SOON" policies, the blind-time hypothesis, the binding veto). None is
recommended for trading. The voice (I1, I2, I4, I6) changes no decision and needs no promotion test.
