# 49. Tighter trailing and re-entry: what the champion's own trades say

11 November 2026. Owner: "We are giving away a lot of points from the peak where we could easily have booked at
higher prices and then re-entered the same direction (maybe another strike) if the conviction and forecast to run
was still strong."

Script: `research/predict/trail_study.py` (and `... more`). Output: `data/research/predict/trail_study.json`.
Data: the 15-day replay p41 (10 Nov code), the five pool books c20_9y, c20_9s, c20_9v, c20_9x, c20_9t (507 trades),
with each held contract's bid and ask second by second from the recorded quotes. Variants were ranked on the first 10
sessions (19 Oct to 2 Nov) and checked on the last 5 (3 to 9 Nov). Sell at the bid, buy at the ask, no costs, each
trade's own quantity. In-sample for the books themselves.

## 1. The giveback is real

| Book | Trades | Value at the peaks | Booked | Given back | Booked as share of peak |
|---|---|---|---|---|---|
| c20_9y | 92 | 31.5 lakh | 11.9 lakh | 19.6 lakh | 38 % |
| c20_9s | 96 | 31.4 lakh | 11.1 lakh | 20.3 lakh | 35 % |
| c20_9v | 103 | 31.0 lakh | 10.9 lakh | 20.0 lakh | 35 % |
| c20_9x | 102 | 31.5 lakh | 10.4 lakh | 21.1 lakh | 33 % |

- c20_9y: the median trade peaked at +17.7 % of its premium and exited at +2.8 %.
- 17 of its 38 losers had been up 5 % or more; 12 had been up 10 % or more.
- Giveback by exit: forward trail 7.8 lakh (44 trades), stop loss 3.4 lakh (12 trades that rose first), break-even
  lock 2.6 lakh, time 1.6 lakh, ramp lock 1.5 lakh, premium trail 1.4 lakh, giveback floor 1.1 lakh.

## 2. Tighter trails lose money

Applied on top of the book's own exits (they can only exit earlier):

| Variant on c20_9y | Change, first 10 days | Change, last 5 days |
|---|---|---|
| Best found: trail 5 % from the peak once up 25 %, with re-entry on a new high | -3,790 | -30,186 |
| Trail 8 % once up 25 %, no re-entry | -88,179 | -31,203 |
| Lock 60 % of the gain once up 15 %, with re-entry | -1,45,246 | +25,766 |
| Trail 5 % once up 5 %, no re-entry | -9,48,444 | -92,319 |

No variant of 40 (trails and gain locks, four arming levels, with and without re-entry) beat the book on the first
10 days. A few were better on the last 5 days, but they had been worse on the first 10. Reason: the book earns
through a few long runners; anything that exits earlier cuts them, and the re-entry pays the spread and misses part
of the move. This is the same lesson as the forecast-exit twin (more winners, half the rupees).

## 3. Floors after a gain lose money

"Once the peak gain reached a, exit if the bid falls back to entry x (1 + f)": every setting armed at 8 to 15 % lost
0.2 to 7.7 lakh on the first 10 days. Armed at 20 % it never hurt but fired on only 1 or 2 trades. Trades that dip
back to entry often recover.

## 4. After the book's own exit, the run often continues, but buying back on a new high loses

- The same contract's bid went 5 % or more above the exit price within 5 minutes on 50 of 89 trades, and within 15
  minutes on 62. So the "it kept going" feeling is correct.
- But a re-entry when the bid makes a new high above the trade's peak (buy at the ask, exit 8 % off the new peak or
  after 15 minutes) fired 31 times, won 11, and lost 1.13 lakh: -55,110 on the first 10 days and -57,463 on the last
  5. The breakouts it chased mostly reversed.

## 5. What this means

- Mechanical tightening and mechanical re-entry both lose on these 15 days. The giveback is largely the price of
  keeping the runners that make the book's money.
- The only route that could capture more is a decision that depends on the state of the trade and the market at
  that moment: hold when the run is likely to continue, sell when it is likely to fade. That is the held-position
  continuation model of docs/44 (sell now against keep, valued from now, never from the best future price).
- The Forecast Lab's direction experts showed no skill on 9 Nov (docs/48 section 8), so "the forecast says it will
  keep running" cannot be trusted yet as that conviction signal.

## 6. Proposed next step

1. Build held-state snapshots for these 507 trades every 15 s: gain, peak, drawdown from peak, time since peak, the
   future's momentum and range, the IV change, the gamma-rent ratio, the Forecast Lab's state. Label: the rupee
   difference between selling now and holding to the book's own exit.
2. Fit a small model on the first 10 days; check on the last 5 and on forward days.
3. Only if it beats the book on held-out days: a shadow twin of c20_9y that exits when the model says the run is
   fading, and a second twin that re-enters (any eligible strike) when it says the run resumed. Each with its own
   counters, compared to the parent in rupees.
4. Nothing changes the champion until a twin passes the owner's promotion standard.

## 7. Built and tested (11 Nov afternoon): the continuation and re-entry models

Code: `apex/predict/hold.py` (one feature function for offline and live), `research/predict/build_hold.py`,
`apex/engine/holdtwin.py`, the council hooks in `apex/engine/council/__init__.py`. Results:
`data/research/predict/hold_study.json`. Tests: `tests/test_hold_twins.py`.

Data: every 15 s while each of the 507 pool trades was held (25,533 snapshots), and every 15 s for 15 minutes after
each exit (28,182). Ridge regression, each trade weighted as one. The decision line was chosen on the first 10 days by
leave-one-day-out (each day scored by a model fitted without it), then frozen; the last 5 days were scored once.

| Model | What the line does on the first 10 days (leave-one-day-out) | Last 5 days |
|---|---|---|
| Hold or sell now | Every line that ever sells early loses: -8.8 lakh (5 sales) to -31.3 lakh (134 sales). Best: never act | not applicable |
| Buy back after an exit | Line +2 %: +12,477 on 9 buy-backs, 5 won; lower lines lose (-33,059 at 0, -1.63 lakh at +1) | no decision at line +2 |

What the hold model learned is sensible but not strong enough to act on: a strong move in the last 5 minutes lowers
the value of holding on (exhaustion), movement that pays for decay raises it, nearer expiry lowers it.

Decisions:
- **Hold-or-sell twin: not added.** Its honest line never acts, and it would cost the engine a council book's time.
  The code stays for a better model.
- **Re-entry twin `rx_c20_9y`: added**, model `apex/predict/reenter_v1.json` (hash `d67158b40ecf`, line +2 %), frozen.
  Same strategy and exits as c20_9y; after each of its exits it may buy the same contract back once within 15
  minutes, with a fixed exit (8 % off the peak bid, 15 minutes, or the flat time). Shadow only, outside the pool. The
  evidence for it is thin (9 decisions in discovery); it is there to collect forward evidence. Takes effect at the next
  engine restart. 106 books.
