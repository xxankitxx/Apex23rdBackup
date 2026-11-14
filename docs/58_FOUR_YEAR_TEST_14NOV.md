# 58. 14 Nov (night): the four-year test

Owner, 14 Nov: "So why ... have you stopped if you have not achieved what I asked." The wall was data: 18 recorded
sessions cannot prove an entry. The owner's other project (MYTHOS, `D:\ClaudeCodeImproved`) downloaded broker history
on 14 Nov: 1-minute Nifty futures and spot for 984 sessions (15 Nov 2022 to 13 Nov 2026) and 1-minute weekly option
bars (ATM +- 4 strikes, both sides) for 145 sessions (14 Nov 2024 to 10 Jun 2025). It was read here read-only; nothing
was written to that project. Scripts and caches: `data/research/14nov/work/` (`lab1.py`, `h4.py`, `s21` to `s26`).

Nothing here changes a live trading decision.

## The lab and what it can and cannot say

* The champion's exit ladder walked on 1-minute bars. Where real option bars exist they are used; elsewhere a Black-76
  model option whose IV is the 20-session realised volatility x 1.22 to 1.32 (fitted on the real sessions).
  Model against real, same sessions: day-result correlation 0.82 to 0.94; the model is about 1 point a trade kind.
* The pullback pattern read from each bar's high and low (`lab1.sig_pb_hl`) takes about as many trades as the
  per-second pattern and its day results correlate 0.71 to 0.75 with it and 0.80 to 0.90 with the real Conductor on the
  14 recorded normal days. It is a relative of the champion, not the champion: about a third of its trades differ.
* Expiry-day breakouts cannot be judged on 1-minute bars (15-minute clock, 25-point trail); normal days only.

## Results (normal days, % per trade, day-clustered t)

**The champion's pattern.** Best-matching 1-minute version (pullback 40 % of the impulse):

| Period | Trades | Winners | Per trade |
|---|---|---|---|
| The recorded window, 19 Oct to 13 Nov 2026 | 75 | 49 % | +5.7 % |
| The four years before it | 2,214 | 33 % | -0.01 % |

The window's quarter ranks first of 17 quarters. The other versions say the same (+2.0 and +3.9 % in the window, -0.1
and 0.0 % before). On the 105 sessions with REAL option bars (Nov 2024 to Jun 2025): 385 trades, 28 % winners, -0.6 %.
No exit setting changes this: 216 exit sets (stop 6 / 10 / 15 %, target none / 8 / 15 / 30 %, trail 25 / 40 / 70,
clock 20 / 45 / 90 minutes, floors on / off): best on 2022-2024 gives -0.1 % on 2025-2026.

**65 entry ideas, found on sessions before 2025, judged on 2025-2026.** Momentum and breakout ideas are flat or
negative on 2025-2026. A blind buy makes 0.0 to -0.6 % (the cost). Fades are the only family positive in both halves:

| Idea | 2022-2024 | 2025-2026 |
|---|---|---|
| Fade a 20-minute move of 0.6 day-sigmas | +3.5 % (245 trades, t 2.0) | +2.2 % (199 trades, t 1.5) |
| Fade the 15-minute opening-range break | +1.5 % (t 1.7) | +1.5 % (t 1.4) |
| Fade a 60-minute move of 0.7 sigmas | +1.9 % (t 1.7) | +1.8 % (t 1.4) |
| Buy the 15-minute opening-range break | -1.2 % | -0.3 % |

Sized honestly: across 36 window x stretch settings the fade is positive in 34 on 2025-2026, but the typical setting
earns about +1 % a trade with 35 % winners, and with other exits the 20-minute / 0.5-sigma fade is negative on
2025-2026. Real option bars, six settings: +1.2, -0.5, +2.7, +1.9, -1.5, -0.4 %. A lean, not an edge.

**Days to expiry over four years.** The pattern on the session before expiry: +0.6 % a trade (145 sessions, t 0.7);
further away: -0.3 %. Not significant. The 15 of 15 result of docs/57 belongs to Aug-Nov 2026.

**The price of options.** On 114 real-option sessions the at-the-money implied volatility at 09:30 was 1.26 x the
20-session realised volatility (median). Buying was not clearly better on the cheap third of days (+0.7 % against
-1.7 % and -0.4 %, rank correlation -0.01).

**Entry timing.** On 37 matched entries of the recorded days the per-second entry is 16 s earlier but only 0.6 index
points better (better on 49 %). The per-second pattern's better results there come from WHICH trades it takes.

## What this means

1. The champion's record (+10 % a trade, 52 % winners on normal days) was made in the kindest quarter of the last 17
   for this pattern. On the four years before, its 1-minute relative breaks even. Expect far less than the record.
2. Nothing tested on four years, entry or exit, has an edge big enough to build on. The fade is the only lean.
3. The thrust books and the days-to-expiry lead of docs/57 rest on the same kind window. They stay shadows.

## What could still change the answer

* The option download in MYTHOS is at 145 of about 490 sessions; each run adds real option prices to this lab.
* Whether the broker serves 1-second history is not known (the probe asked for 1-minute only). With it the real
  per-second champion could be run on a year instead of 18 sessions.
* Each live day adds one per-second session with depth and order flow, which no history has.

## Built from it (owner: "Build the fade shadow")

Shadow only, registered last, never in the live pool.

| Book | Rule | File |
|---|---|---|
| `fade20` | Normal days, read once a minute: the smoothed forward moved 0.6 day-sigmas or more in 20 minutes: buy the other side (a put after a rise, a call after a fall). One signal per side per 20 minutes. Champion's strike pick and exits. | `apex/engine/council/fade.py`, `fade20.py` |
| `fade60` | The same for a 60-minute move of 0.7 day-sigmas. | `fade.py`, `fade60.py` |
| `conductor_fd` | A shadow Conductor (policy `fade`): its own all-in account pools the live pool plus the two fade books, last in priority. | `apex/engine/conductor.py` `EXTRA_POOL` |

Day sigma = the day's first forward x the standard deviation of the last 20 daily log returns from
`data/learning/day_levels.json` (at least 10 returns; otherwise the forward x ATM IV / 1.26 / sqrt(252)). On 16 Nov
that is about 254 points, so the lines are about 152 points in 20 minutes and 178 points in 60 minutes: rare events
(about one trade every two days for `fade20` over the four years).

What to expect: in the recorded window (a momentum quarter) the real classes lose: `fade20` 12 trades, 3 winners;
`fade60` 14 trades, 2 winners (`py -3.13 -m apex.fastlab play fade20 fade60`, 18 sessions in 84 s). The case for them
is the four years, not the last four weeks. Tests: `tests/test_fade_14nov.py` (5). Step time: not re-measured; the two
classes are the same kind as the thrust books (about 0.3 ms a call, once a second).

## The broker serves 1-second history (owner: "Yes, probe it")

Probe on 14 Nov, 10 read-only calls (`data/research/14nov/work/probe_1s.py`; it logs in the way the feed does, with
the paper-only interlock): `get_historical_data_v2(interval="1second")` returns the Nifty future and expired weekly
option contracts second by second (open, high, low, close, volume, open interest) for 13 Nov 2026, 15 Oct 2026,
14 Aug 2026, 14 Nov 2025 and 23 May 2025: about 280 to 600 bars per 10 minutes asked. A whole session of one contract
is 25 calls of 15 minutes (`hist1s.py`, resumable, paced at 75 calls a minute, its own call count).

Checked on 6 Nov, which is also on tape (25 calls): the broker's future has a trade in 14,831 of 22,500 seconds; against
the tape's futures mid the mean absolute difference is 2.9 points. The champion's pattern fired from the broker series
at 10:27, 10:33, 10:47, 11:04, 13:03 and 14:06; from the tape at 10:27, 10:33, 10:46, 11:05 and 14:09: every tape entry
is matched within three minutes, with one extra. Priced on the tape's real quotes the trades are +11, +7, -6, -10,
+62 % against +10, +5, -5, +71 %. The 1-minute version missed the 14:09 winner; the 1-second one does not.

So the real per-second pattern can be tested on a year or more: 25 calls a session for the future (a year is about
6,200 calls, two to three days of the broker's allowance, never in market hours), then the model option or the real
option bars for the trades it takes.

## First per-second result from the broker history (owner: "Yes, start now")

Downloaded 14 Nov, 1,200 calls: the Nifty future second by second for the 48 sessions from 10 Aug to 16 Oct 2026
(`data/research/hist1s/`). The per-second model option (`lab1s.py`) was first checked on the recorded sessions' own
forward against real quotes: normal days 56 against 55 trades, 43 against 42 % winners, +6.2 against +5.8 % a trade,
day-result correlation 0.98. Expiry days: correlation 0.29, so they are left out until real option seconds are used.

The champion's pattern, per second, normal days (`s29_champion_1s.py`):

| Period | Sessions with a trade | Trades | Winners | Per trade | Days up |
|---|---|---|---|---|---|
| 10 Aug to 16 Oct 2026 (broker 1-second history) | 23 | 48 | 38 % | -0.3 % | 6 of 23 |
| Recorded window, 19 Oct to 13 Nov 2026 | 14 | 55 | 42 % | +5.8 % | 10 of 14 |

August: 4 trades, none won. September: 11 trades, 27 % won. The pattern also fired far less often (1 to 2 trades a day
against 4). Forty-eight trades is a small sample, but it points the same way as the four years of 1-minute bars: the
profit sits in the recorded window. The rest of the year needs about 5,000 more calls (`hist1s.py`, queue in
`data/research/hist1s/queue.txt`).

## The fades as an account of their own (owner: "do it now. And don't stop")

One account, one position at a time, four years of 1-minute bars, model option, normal days (`s34_composite.py`):

| Account | 2022-24: trades a day, per trade, t | 2025-26: trades a day, per trade, t | Quarters up | Worst quarter |
|---|---|---|---|---|
| The pullback pattern alone | 3.3, +0.44 %, 0.9 | 3.6, +0.23 %, 0.5 | 10 of 17 | -214 |
| fade20 + fade60 | 1.1, +2.59 %, 2.4 | 1.0, +2.07 %, 1.9 | 13 of 17 | -86 |
| fade20 + fade60 + opening-range fade | 2.0, +1.99 %, 2.8 | 1.9, +1.81 %, 2.4 | 14 of 17 | -90 |
| The pattern + fade20 + fade60 in one pool | 3.9, +0.89 %, 1.9 | 4.1, +0.38 %, 0.9 | 11 of 17 | -332 |

The pattern's quarters and the fades' quarters are negatively correlated (-0.33 to -0.40): the fades did well in the
pattern's bad quarters (2023 Q2 to Q4, 2026 Q3) and lost in its best one (2026 Q4, the recorded window). Pooled in one
account the pattern's many trades crowd the fades out, so the fades are tested as an account of their own.

Checks that keep this honest:

* Real option bars, 114 sessions (Nov 2024 to Jun 2025, `s35_fades_real.py`): the three fades +0.90 % a trade (234
  trades, 35 % winners, t 0.8; the model on the same sessions says +1.61 %, so the model is about 0.7 points kind);
  fade20 +2.74 %, fade60 +0.58 %, opening-range fade -0.46 %; the pattern alone -0.96 % (545 trades).
* The settings were chosen knowing both halves. The family is what holds: 34 of 36 fade settings are positive on
  2025-26 against a blind buy at 0.
* The real classes per second on the 89 broker sessions before the recorded window (model chain, `s32_real_classes.py`,
  checked 0.98 against tape quotes): c20_9x 85 trades, 41 % winners, +1.1 % a trade; fade20 41 trades, -0.3 %; fade60
  49 trades, +2.3 %; opening-range fade 69 trades, +0.8 %. None is significant on that sample yet.
* Trading a strategy only when its own trailing record is positive, or switching between the pattern and the fade on
  it: not better than running both (`s33_regime.py`). Waiting for the turn before a fade: worse (`s36`).
* Expiry days with real option seconds from the broker (`s31_expiry_real.py`, one call a trade; checked 0.92 against
  tape quotes): the expiry breakout on the 12 expiry sessions from 28 Jul to 13 Oct 2026 made -0.6 % a trade (101
  trades, 32 % winners, 3 of 12 days up, one day +289 %).

Built for it (shadow, registered last):

| Book | Rule |
|---|---|
| `orbfade` | Normal days: the first time the smoothed forward closes a minute outside the 09:15 to 09:30 range (until 11:45), buy the other side. One signal a day. In no pool. `apex/engine/council/orbfade.py` |
| `conductor_fo` | A shadow Conductor (policy `fadeonly`) whose pool is fade20 + fade60 and nothing else: the fade account. `conductor.ONLY_POOL` |

Tests: `tests/test_fade_14nov.py` (7).

Step time with all 120 books, measured 14 Nov night (the real engine on the 6 Nov tape to 10:15, against the 115
without `fade20`, `fade60`, `orbfade`, `conductor_fd`, `conductor_fo`, side by side): median 16.6 ms against 16.0 ms,
95th percentile 49 against 49 ms, books phase 5.72 against 5.68 ms, no step over 300 ms, no fault, books save 8 ms.
Inside the engine `orbfade` took its one trade of the day at 09:37 (a put, about 0 %); the 20- and 60-minute fades did
not fire on 6 Nov (no stretch reached the line by 10:15).

## The year at per-second resolution, with the real strategy classes

Downloaded 14 Nov (5,700 calls): the Nifty future second by second for the 229 sessions from 14 Nov 2025 to 6 Nov 2026.
The real classes (`c20_9x`, the stall twin, `fade20`, `fade60`, `orbfade`) stepped through every normal day on a model
option chain (`s32_real_classes.py`; on the recorded sessions the same classes on tape quotes: 50 against 49 trades,
+8.6 against +7.8 % a trade, day-result correlation 0.98). `s38_year_summary.py`:

| Book | Year before the recorded window (14 Nov 2025 to 16 Oct 2026) | Recorded window |
|---|---|---|
| `c20_9x` (the champion class) | 393 trades, 38 % winners, +0.65 % a trade (t 0.9), 56 of 135 days up, 6 of 12 months up, total +257 | 49 trades, 47 %, +7.75 %, total +380 |
| `st15_c20_9y` | 419 trades, 38 %, +0.14 %, total +59 | 56 trades, +6.24 % |
| `fade20` | 98 trades, 37 %, +0.06 % | 6 trades, 0 won |
| `fade60` | 124 trades, 35 %, +1.92 % (t 1.0), 9 of 12 months up | 10 trades, +4.96 % |
| `orbfade` | 179 trades, 44 %, +2.07 % (t 1.9), 7 of 12 months up | 14 trades, -4.99 % |

The champion class made more in the four recorded weeks (+380 points) than in the eleven months before them (+257),
and without its five best trades the eleven months are negative. The stall twin did not help over the year.

One account, one position at a time (`one_account` in `s38`), all 13 months:

| Account | Trades (a day) | Winners | Per trade | t | Months up | Worst month | Total |
|---|---|---|---|---|---|---|---|
| The champion class alone | 442 (3.0) | 39 % | +1.44 % | 1.8 | 7 of 13 | -74 | +636 |
| The three fades | 370 (1.9) | 39 % | +1.31 % | 1.4 | 8 of 13 | -155 | +486 |
| The champion + the three fades | 708 (3.6) | 39 % | +1.37 % | 2.4 | 9 of 13 | -98 | +973 |
| The champion + `fade60` + `orbfade` | 676 (3.5) | 39 % | +1.60 % | 2.7 | 9 of 13 | -92 | +1,082 |

In the year before the window the pooled account made +749 points against +257 for the champion alone; in the window
+225 against +380. Per second the fades do not crowd the champion out (they fire at other moments), so pooling adds:
more trades, a higher total, more months up. `conductor_fd` now pools the live pool with all three fades and is the
shadow account to watch. Limits: a model option (normal days only, no open interest, no moving IV, so c20_9y's two
vetoes are off); 13 months; the fade settings came from the four-year 1-minute set, not from this year.

Per-second search over the same year (`s30_search_1s.py`, 26 entry settings, replica entries, model option): every
pullback setting is negative in the newer half of the year and positive in the recorded window (the champion's own:
+0.80 % then -0.45 % a trade in the two halves, +5.84 % in the window); breakouts and day-high/low breaks are flat; the
60-minute fade is the only setting positive in both halves (+1.9 %, +1.9 %). The fade family per second on a grid
(`s39_fade_grid_1s.py`): stretch fades are positive in both halves in 13 of 36 window x stretch cells, opening-range
fades in 4 of 10 (the 60-minute range: +5.7 %, +1.9 %, and +5.9 % in the window). Thirty to ninety trades a cell: the
fade remains a lean of about +1 % a trade, clearest when pooled with the champion.

## Expiry days over the year, on real option prices

`s40_expiry_class.py`: the real class `c20_9x` stepped per second on a model chain (for its strike picker and vetoes;
the IV-jump veto cannot fire on a flat model IV), every contract it buys repriced on that contract's own 1-second
broker history for its 15-minute life. Checked on the four recorded expiry days against the same class on tape quotes:
71 against 80 trades, 42 against 41 % winners, day-result correlation 0.96.

| 48 expiry sessions, 18 Nov 2025 to 13 Oct 2026 | |
|---|---|
| Trades | 639 (13 a day) |
| Winners | 31 % |
| Per trade | -0.62 % |
| Days up | 11 of 48 |
| Median day (all-in, compounded) | -33 % |
| Days below -50 % | 14 |
| Days above +50 % / +100 % | 6 / 2 (best +430 %) |
| Older half / newer half | -1.12 % / +0.25 % a trade; 4 of 24 / 7 of 24 days up |

The plain breakout without the class (`s31_expiry_real.py`) says the same: 659 trades, 33 % winners, -0.79 %, 14 of 48
days up. The four recorded expiry days (+22, +532, -16, +43 % for the live Conductor) contain one of the year's two
best days. On this evidence the expiry-day breakout is a lottery with a losing median day, not the system's engine.
The live Conductor did better than this harness on the recorded days (56 % winners against 42 %), so the true figure
is somewhat better than the table; it would have to be very much better to change the conclusion.

Fades on expiry days, real option seconds (`s41_expiry_fades.py`, 48 sessions): the 60-minute fade 28 trades, 57 %
winners, +7.6 % a trade (t 1.9, 10 of 18 days up; older half +15.5 %, newer -0.4 %); the others flat or negative
(20-minute 0.6: 26 trades, +2.9 %; 20-minute 0.4: -0.8 %; opening-range 15-minute: -0.7 %; 60-minute range: +0.9 %).
A lead on 28 trades, nothing more.

## What all-in compounding does with these edges

`s42_capital.py`: an account of 100 on 14 Nov 2025, all-in on every trade, compounded trade by trade to 16 Oct 2026
(real classes per second; model option on normal days, real option seconds on expiry days):

| Normal days | Expiry days | Trades | 100 becomes | Deepest fall on the way |
|---|---|---|---|---|
| Champion | Breakout, as live | 1,032 | 0 | -100 % |
| Champion | No trading | 393 | 25 | -95 % |
| Champion + three fades | No trading | 647 | 125 | -97 % |
| Champion + three fades | 60-minute fade only | 675 | 565 | -98 % |
| Three fades | 60-minute fade only | 373 | 2,338 | -86 % |

The arithmetic says why. Growth under all-in is the average of log(1 + result), about (mean) - (variance) / 2. A trade
here swings about 15 to 20 % (a 15 % stop, winners of 20 % and more), so the variance term is 1 to 2 % a trade: an edge
under about +2 % a trade SHRINKS an all-in account even though it is positive. The champion's normal-day edge over the
year is +0.65 % a trade (its average log is about -0.35 %), and the expiry breakout's is negative. In the recorded
window the edge was +7.75 %, which is why all-in looked right there. Every row above, including the best, fell 86 % or
more at some point. The last rows rest on a model option and on settings chosen with hindsight; they show direction,
not a forecast.

**Owner's decision, 14 Nov:** asked whether the live champion should stand down on expiry days from Tuesday 17 Nov,
the owner answered "Keep it live". The live Conductor and its expiry-day mode are unchanged.

## Correction (14 Nov, after an independent review)

Two faults in the sections above, found by `docs/57_SYSTEM_PROFITABILITY_REVIEW.md` (another tool working in this
repository) and confirmed: (1) "What all-in compounding does" carried capital across the whole year, but the live
account starts at ₹1,00,000 every day, so its "100 becomes 0" rows describe a different account; (2) the one-account
merges (`s38_year_summary.one_account`) added a 60-second pause after every exit, which the live Conductor does not
have. Recomputed in `s48_parity.py` (daily reset, no pause, ties in pool order), year before the recorded window:
champion normal days +249 % summed over 135 days; champion expiry days -579 % over 48; the champion on every day as
live -331 % (-1.45 % a day); champion + three fades on normal days +550 %; fade60 + orbfade alone +620 %. The
conclusions stand in direction (expiry days decide the year; the fades add), not in the sizes printed above.
See docs/59 section 4.3.
