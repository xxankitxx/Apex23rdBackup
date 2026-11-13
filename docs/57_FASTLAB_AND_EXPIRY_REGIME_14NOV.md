# 57. 14 Nov: the fast lab, why the champion is silent, and the days-to-expiry lead

Owner, 14 Nov: "The system has been wholly reliant on one pullback pattern ... Why is it that it also sits silently
for quite a lot of time ... holds on to a non-mover trade at length ... why does the replay run for hours ... DO NOT
TIGHTEN THE CHICKEN'S NECK AND KILL IT. I WANT A MORE PROFITABLE AND MORE TRADE-TAKING SYSTEM."

Nothing here changes a live trading decision. The Conductor, its pool and the five pool books are untouched; every new
rule is a shadow book with its flag off, scored forward under docs/28.

## 1. The tools

| Tool | What it is | Check |
|---|---|---|
| `apex/fastlab.py` | The recorded sessions on a 1-second grid (real option quotes, parity forward, heavyweights, BANKNIFTY futures, FINNIFTY, VIX), the champion's exit ladder in vectorised maths, one position at a time. An entry idea is a list of (second, side). | On the champion books' 200 recorded trades its exits reproduce the recorded return with correlation 0.999 (normal days) and 0.986 (expiry days); its strike pick matches 93 to 98 %. 93 entry variants on 14 days: 34 seconds. |
| Engine-class replay (`data/research/14nov/work/s20_classes.py`) | The real council strategy classes stepped second by second on a `LiveDay` filled from fastlab. | c20_9y gives 26 Oct +222 %, 6 Nov +98 %, 5 Nov -5.3 % (the engine replay: +261, +100, -5.9). 7 sessions x 4 books: 81 seconds. One `on_second` call: about 0.3 ms. |
| 5-minute history | 71 sessions (3 Aug to 13 Nov) of Nifty, BANKNIFTY, FINNIFTY, VIX, the Nifty future and all 14 heavyweights; 215 sessions of 15-minute Nifty (the TradingView connector, data under `data/research/14nov/work/tv/`). | Too coarse to reproduce the pullback entry (same trades: correlation 0.44), so it is used only for how the INDEX moves after an event, in points. |

Why engine replays take hours: they step every one of the 115 books of the live system through every second in Python.
A study of one entry idea does not need that.

## 2. What the data says

**The silence is real.** A buy at every 10th second of every recorded session, both sides, champion exits (64,000
buys): an "opportunity" is a stretch of at least a minute where a buy ended +20 % or better.

| Day type | Opportunities | The Conductor entered |
|---|---|---|
| Normal days (12) | 50 | 9 |
| Expiry days (4) | 51 | 33 |

On normal days the account is in a trade 46 to 171 minutes of 375.

**A blind buy has no edge.** Normal days: 35 % winners, +0.8 % a trade. So the exits alone are worth nothing; the
champion's entries (52 % winners, +10 % a trade on normal days) carry it.

**What does NOT find the missed opportunities** (all tested, all rejected):

| Idea | Test | Result |
|---|---|---|
| A model on 80 per-second inputs | leave one day out, 12 normal days | rank skill negative (3 of 12 days positive); trading its top 5 %: 38 trades, 32 % winners |
| 93 entry variants (breakouts, pullbacks at 3 scales, day-high/low breaks, squeezes, heavyweight and sister thrusts, VWAP crosses, catch-up) | fastlab, 14 normal days | none beats the pullback pattern per trade; most profit is calls in a rising month |
| Heavyweight / sister / order-book lead as its own trade | buy at the ask, sell at the bid 5 to 300 s later, 375,000 seconds | the lead is real but worth about 0.1 % of premium; the spread is 0.22 %. Every signal nets -0.1 to -0.3 % |
| 30 kinds of event on 71 sessions (index points 15 / 30 / 60 minutes later) | day-clustered t | best t 2.3; hit rates 46 to 57 %: a coin flip |
| The pullback at 5 to 30-minute scales in one account | fastlab, account level | twice the trades, the same total, lower strike rate (38 % vs 45 %), worse worst day |
| "Lunch-hour buy" (12:15 to 13:15 looked good on the recorded days) | 42 independent sessions | -0.3 % a trade: gone |

**The one lead: days to expiry (recent months only).** Seven kinds of momentum event pooled, 71 sessions (3 Aug to
13 Nov), Nifty points in the event's direction 30 minutes later:

| Sessions to expiry | Sessions | Mean | Day-clustered t | Sessions positive |
|---|---|---|---|---|
| 1 (the session before expiry) | 15 | +7.3 | 4.6 | 15 of 15 |
| 0 (expiry day) | 15 | +3.2 | 0.6 | 8 of 15 |
| 2 or more (Wed, Thu, Fri) | 41 | about 0 | under 1 | about half |

Fading a stretched move on the session before expiry loses (-6.7 points, t -2.7).

It is NOT confirmed outside those months. 215 sessions of 15-minute bars, after a 30-minute move of 35+ points, the
next 30 minutes in the same direction, on the session before expiry:

| Period | Sessions | Mean | t | Sessions positive |
|---|---|---|---|---|
| Aug to Nov 2026 (the same months as above) | 12 | +10.7 | 3.3 | 10 of 12 |
| Jan to Jul 2026 (independent) | 29 | +2.1 | 0.1 | 15 of 29 |

And on 30-minute bars before Sep 2025, when the weekly expiry was a Thursday, the continuation day was the expiry day
itself (23 of 30 Thursdays, t 3.0), not the day before. So the link between expiry and continuation moves around. It
is a lead from the last three and a half months, to be tested forward, not a law. Option hedging near expiry is a
plausible cause; that is a reading, not a proof.

The champion's own record splits the same way (17-day engine replay plus 13 Nov live):

| Sessions to expiry | Conductor trades | Winners |
|---|---|---|
| 1 | 10 | 10 |
| 0 | 63 | 35 (56 %) |
| 2 or more | 37 | 12 (32 %) |

So on the recorded sessions "the rules do not work every day" has a shape: far from expiry the pattern was close to a
coin flip. All 18 recorded sessions sit inside the Aug to Nov months.

**On the session before expiry, thrust entries add trades that pay** (fastlab, real quotes, 3 recorded sessions; the
11 other normal days beside them):

| Account | Trades, session before expiry | Winners | Sum of the 3 days | Same on the 11 far days |
|---|---|---|---|---|
| Champion pattern alone | 14 | 64 % | +256 % | +86 % |
| + sister thrust (8 pts / 60 s) | 40 | 52 % | +437 % | -4 % |
| + heavyweight thrust (8 pts / 60 s, breadth 0.5) | 40 | 60 % | +588 % | +69 % |
| + both at 12 pts | 39 | 59 % | +670 % | -61 % |

Limits: three sessions, all in sample (26 Oct, 2 Nov, 6 Nov; 12 Nov is NOT one: 10 Nov was a holiday, so that week's
expiry was Monday 9 Nov). The regime rests on 15 sessions of the last months (and is absent Jan to Jul); the thrust trigger rests on three. With the real
engine class the heavyweight book made -3 %, +45 %, +309 % on the three sessions (the sister book +283, +74, +57): one
different exit changes the day.

**The hold question.** On the pool books' 231 real normal-day entries:

| Sell a trade that after N minutes never reached +8 % and sits within +-4 % | Fired on | Those trades later won | Later mean | Sold-there mean | All trades, sum |
|---|---|---|---|---|---|
| never (today) | 0 | | | | +2,186 |
| 10 minutes | 77 | 47 % | +4.6 % | -0.4 % | +1,800 |
| 15 minutes | 48 | 31 % | -1.7 % | -1.2 % | +2,213 |
| 20 minutes | 38 | 37 % | -0.8 % | -1.7 % | +2,150 |

At 15 minutes a non-mover has no edge left; selling there costs nothing and frees about half an hour. At account level
the freed time took new triggers: the pattern's 12 in-sample normal days +366 to +431, and both untouched days better
(12 Nov +2.5 to +6.8, 13 Nov -26.3 to -16.5). A sequential drift test (SPRT) as an exit loses. Cutting at 5 minutes
loses (R19, 13 Nov). The maths in the exits already there: delta-scaled trail, gamma rent (realised over implied
variance), calendar theta, IV vetoes (c20_9x docstring).

## 3. What was built (shadow, flags off, registered last)

| Book | Rule | File |
|---|---|---|
| `thr_sis` | The session before expiry only: BANKNIFTY futures and the FINNIFTY index both moved 8 Nifty-equivalent points in 60 s: buy that side. First second of the stretch, one per side per 10 minutes. Champion's strike pick and exits. | `apex/engine/council/thr_d1.py`, `thr_sis.py` |
| `thr_hw` | Same, for the Nifty-weighted heavyweight basket: 8 Nifty points in 60 s with weighted breadth 0.5. | `thr_d1.py`, `thr_hw.py` |
| `st15_c20_9y` | c20_9y plus: normal day, held 15 minutes, peak under +8 %, bid within +-4 % of entry: SELL "STALL". | `apex/engine/council/c20_9y_st15.py` |
| `conductor_d1` | A shadow Conductor (policy `prexp`): its own all-in account pools the live pool plus the two thrust books, last in priority. Refuses nothing. | `apex/engine/conductor.py` `EXTRA_POOL` |

`LiveDay` (the council books' shared day) now carries one row a second of the BANKNIFTY futures mid, the FINNIFTY index
(quotes at most 5 s old) and the heavyweights' log last prices (30 s), forward-filled, written once per second inside a
try. Tests: `tests/test_thrust_14nov.py` (11). The engine classes take the same entries as fastlab on the three
sessions (15 of 15, 13 of 13, 13 of 13 for the sister book).

The next session before expiry is Monday 16 Nov (expiry Tuesday 17 Nov): the first forward day for the thrust books.

## 4. Not done, and why

* Step time, measured 14 Nov (owner: "Yes, run it"): the real engine on the 6 Nov tape to 10:15 (a session before
  expiry, 59 market minutes, 45,000 steps), all 115 books against the 106 without the nine shadows of 13 and 14 Nov,
  the two runs side by side on a machine that was also running the test suite:

  | Per step (budget 100 ms) | With the nine shadows | Without |
  |---|---|---|
  | median | 17.6 ms | 17.3 ms |
  | 95th percentile | 60 ms | 57 ms |
  | books phase, mean | 6.3 ms | 5.7 ms |
  | Conductors, mean | 0.31 ms | 0.18 ms |
  | steps over 300 ms | 0 | 1 |
  | books save | 16 ms, no lag | |

  No fault. Inside the engine `thr_sis` took the entries fastlab predicted (09:16, 09:26, 09:37, 09:49 puts:
  -10, -10, -4, -12 %; fastlab -9, -10, -4, -12) and `conductor_d1` pooled both thrust books.
* No rule was promoted. Three sessions cannot pass the 7 tests.
* BANKNIFTY / FINNIFTY options are not recorded, so nothing can be said about trading them.
