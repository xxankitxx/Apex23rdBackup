# Why the system cannot "be bullish, then bearish, then bullish" — diagnosis and solution design

Written 21 Oct 2026 evening for the owner and for the implementing session. Everything below is measured on the two
recorded tapes (Mon 19 Oct, expiry day; Wed 21 Oct, 6 DTE). Numbers are honest-fill engine replays unless marked "spot
points" (a spot-only check, no option pricing). Scripts: /tmp/claude-0/c6/fable_sim.py, fable_struct.py; council reports
M01–M10 summarised in docs/12.

## 1. The day, in the shape the owner describes

| Leg | Time | Spot | Move |
|---|---|---|---|
| Bullish | 09:15 → 09:38 | 23,004 → 23,119 | +115 |
| Bearish | 09:40 → 14:47 | 23,119 → 22,650 | **−470**, a staircase |
| Bullish | 14:47 → 15:12 | 22,650 → 22,743 | +93 |

The three-trade day at the engine's own strikes and lots: CE 23000 ₹+3,959; PE 23150 09:45→14:47, premium 191 → 520, 8
lots, **₹+1,70,820**; CE 22650 ₹+21,814. About ₹1.97 L was on the table. The system ended −₹22,561 live.

## 2. What the system actually did on the bearish leg (the leg that mattered)

Old entry (`spot_dc12_t12_first`, the code that ran live), 09:40–14:47:

* **34 PE trades.** Direction was right 34 times. Summed best-since-entry excursion: **565 spot points** — more than the
  whole leg. Net: **−₹231.** Median hold 117 s.
* **14 CE trades** into the falling market: 3 won, **−₹19,334.** Every one was a counter-rally that broke the 12-minute high.
* So the system "saw" the bear leg 34 times and threw it away 34 times. It was not blind to the direction. It could not
  *hold*, and it *reversed on every bounce*.

Retest entry (shipped today, D-131): 17 PE / 3 CE on the leg, +₹1,963 / −₹6,760. Fewer bad CEs, still no holding.

## 3. The three reasons it cannot hold — each measured

### 3a. The exit tolerance is smaller than the pullbacks of a trend day
Inside the 470-pt leg there were **22 counter-rallies ≥ 12 pts** (15 ≥ 20, 7 ≥ 30, 4 ≥ 40, 2 ≥ 60: 74 pts at 10:20 and
76 pts at 12:23). A 12-pt trail is stopped 22 times by construction. One PE from 09:45 with a wider trail:

| Trail (pts) | Stopped at | Captured of 443 |
|---|---|---|
| 12 | 09:51 | 54 |
| 20 | 09:55 | 52 |
| 30 | 10:01 | 56 |
| 40 | 10:16 | 127 |
| 60 | 10:34 | 109 |
| 80 | never (14:59) | **415** |

**Nothing under ~80 points holds this leg.** The profitable humans either sat through a 76-pt bounce (on the engine's 8 lots
that is a ₹31,564 premium drawdown inside a winning trade, ₹20,332 at the 10:20 bounce) or re-entered after each bounce
in the same direction. They did not run a 12-pt trail.

### 3b. The entry has no memory of the trend
The signal is "spot above/below its previous **12 minutes**". In a staircase every 30–75-pt bounce breaks the 12-min high,
so the code buys a CE at the top of each bounce (14 times). The code has no object that says "the hour-scale structure is
lower highs and lower lows; a bounce inside it is a selling opportunity, not a buy". M05 tested slope filters at 30/48/60/72
min: every one that cut the 21 Oct CEs also cut 19 Oct's winners (19 Oct's +122k came from counter-slope entries). A
simple slope is not the right object; a *structure* (pivot highs/lows) might be — see §5.

### 3c. Trade count × cost
Each round trip costs ~2.3 premium points (spread + buying just after the burst) ≈ ₹900 at 6–8 lots (M06, M08, M10). 54
trades × ₹900 ≈ **₹48k of pure friction** on a day the strategy's gross spot edge was +91 points. 19 Oct survived the
same friction because expiry-day gamma made each caught move worth 3–4× more premium per spot point.

### 3d. Why 19 Oct worked and 21 Oct did not — the same rule, two different instruments
| | 19 Oct (0 DTE) | 21 Oct (6 DTE) |
|---|---|---|
| Delta of the bought option | 0.70 | 0.54 |
| 12 spot pts in premium | 8.4 pts = **7.6 %** | 6.5 pts = **3.3 %** |
| Theta / min | 0.14 pts | 0.03 pts |
| Big winners | 3 trades carry the day (M09) | none: no trade allowed to run |

The 12/12 scalper is an **expiry-day machine**: on 0 DTE a 40-pt move is a 25 % premium move, so a tight trail that keeps
re-entering compounds. On 6 DTE the same 40 pts is 11 %, the trail costs the same ₹3k per stop, and a 470-pt trend is the
only thing that pays — and the rule is built to never hold one.

## 4. What does NOT work (so the implementer does not re-try it)

Measured by council 6 and re-checked today; each fails on 19 Oct, flips sign between days, or is parameter-fragile:
wider fixed trail 14–24 (worse on 21 Oct: −41k…−40k, M02); range-scaled trail (fits 2 days, M09 rejects); 24-pt initial
stop (fragile, 1.7× losses, M03); 30–72-min slope filters (M05); basket/VIX/BankNifty gates (M07); cool-downs, swing margins,
entry caps (M08, and the owner forbade count brakes); strike/expiry changes (M04); hold-N-seconds / bar-close confirmation
(−70k…−140k on 19 Oct, M06). Today's spot-point check of a naive "structure trend-follow" (enter with the bias when a
counter-move ends, exit on a break of the last pivot) is **unstable in the pivot size**: S=15 → +68/+53 pts, S=20 →
−22/+138, S=25 → −48/−93 (19 Oct / 21 Oct, net of cost). One trade in it (PE 11:07 → 12:33, +209 pts) is exactly the
hold the owner wants; the rest is noise. Two days cannot tune that.

## 5. Solution design — what to build so the system *can* behave like the humans

The honest statement: on the two tapes we hold, no single parameter change makes the scalper hold a trend without
hurting the expiry-day result. The capability has to be **added**, as a second mode, and judged on its own days.

### 5.1 Two modes, chosen by days-to-expiry (owner decision)
* **0 DTE (expiry day):** keep the current champion exactly (first-touch or retest — owner's call after more days).
* **≥ 1 DTE:** a **trend-holding mode**. The two days say the instrument is different (§3d); the mode switch is the
  one structural fact both days support. Risk: it is still fitted to one day of each kind — run both modes as books on
  every day and let the ledger decide.

### 5.2 The trend-holding mode — components (each testable on its own)
1. **Bias object** (new, engine-level, published in the state blob): pivot highs/lows of spot with a confirmation size
   S (candidates 15–30 pts; also try S = k × 12-min range, k≈0.5), bias = DOWN after a lower high + lower low, UP after
   higher high + higher low, NONE otherwise. Persisted in warm state. Dashboard: show the bias and the last two pivots.
2. **Entry = with the bias, at the end of a counter-move** — the retest logic already shipped is the right shape; point
   it at the bias instead of the 12-min level: when bias is DOWN, arm on a counter-rally, buy the PE when the rally stalls
   (falls `retest_ext` from its top) and the top holds. No CE while bias is DOWN. This is "sell the rally", what the
   profitable humans did.
3. **Exit = structure, not a fixed number**: stop at the last pivot against the position (for a PE: the last lower
   high), ratcheting down as new lower highs form; plus the D-127 premium lock for the parabolic end of a leg. The
   structure break *is* the bias flip: exit, then bias NONE until a new sequence forms. Time stop at flatten.
4. **Sizing (owner decision — the piece that makes 3 affordable):** all-in 8 lots with a 40–80-pt structural stop risks
   20–30 % of capital per trade. Risk-based lots = floor(risk_rs / (stop_pts × delta × 65)). On 21 Oct, PE held
   09:45→14:47: 3 % risk / 40-pt stop → 2 lots → **₹42,705**; 5 % / 40 pts → 3 lots → ₹64,058; 1 lot → ₹21,352. Smaller
   than the ₹1.7 L fantasy, honest, and it survives the two 75-pt bounces. All-in sizing and a trend hold are
   incompatible; the owner must pick one for non-expiry days.
5. **Trade budget by construction, not by brake**: the bias object makes at most a handful of entries per leg (one per
   counter-move). On 21 Oct that is ~6–10 PE entries instead of 34, so friction falls from ~₹48k to ~₹8k without any
   "stop for the day" rule.

### 5.3 Evaluation protocol (non-negotiable before it trades, even on paper)
* Engine replay, honest fills, both days, FULL/AM/PM; the current champion and `_first` twin stay as controls.
* Pivot size S swept 12–40 and reported as a table; the rule is accepted only if the sign holds across ≥ 3 adjacent S
  on **both** days. Today's quick check says it does not yet (§4) — the implementer should expect to need the sizing and
  the retest-at-bias pieces together, not the structure exit alone.
* Record, per trade: bias at entry, pivot used as stop, pullback size survived, premium drawdown inside the trade.
* Run it as a shadow book first (`trend_hold_*`), champion unchanged, for at least 5 trading days including an up day;
  there is no up-day tape yet, so symmetry is untested.

## 6. Plain-words summary for the owner
The system is a 12-minute scalper with a 12-point leash. On expiry day that leash is 7 % of the option and the scalper
wins. On a 6-DTE trend day the leash is 3 % of the option, the trend bounces 20–75 points twenty-two times, and the leash
yanks it out of a correct trade 34 times and into a wrong one 14 times, paying ₹900 each time. It could not be
"bullish, then bearish, then bullish" because it has no idea what the day's trend is and no permission to sit through a
bounce. Giving it both means: a trend object, entries only with it at the end of bounces, a stop at the structure, and
**fewer lots** so a 40–80-point stop is survivable. That last part is your decision; without it the hold is not possible.
