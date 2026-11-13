# 54. Why the system stays quiet, and why the forecaster did not help (12 Nov 2026)

Owner, 12 Nov evening: "hardly profitable, took losses, silent for so long; why is the forecaster not helping, and how
would I even understand what it is trying to say?" This note records what was measured. The 17-day replay of the
current code (run ids `p44_g1` to `p44_g9`, `APEX_POOL_ASOF=all`) is added when it finishes.

## 12 Nov, live

| Time | Trade | Result |
|---|---|---|
| 11:12 to 12:22 | 25350 PE (c20_9v) | +₹9,340 (+10.7 %) |
| 12:53 to 13:16 | 25200 CE (c20_9y) | −₹2,821 (−2.9 %) |
| 13:45 to 13:58 | 25200 CE (c20_9y) | −₹2,844 (−2.9 %) |
| Day | | +₹3,676 (+3.7 %) |

The Conductor was in the top 12 of about 110 books. Most books that chased the 09:15 to 10:02 rally (about 250
points) bought near the 10:02 top and lost ₹8,700 to ₹33,000 each.

## Why it is quiet

Every pool book is a c20 council book. On normal days its only entry is: a 40-point impulse in 20 minutes, a 50 to
75 % pullback within 15 minutes of arming, then a 5-point resumption (docs/20). A straight-line rally has no deep
pullback, so nothing fires. The Conductor logged "no eligible trigger" 322 times on 12 Nov.

On the 15 replayed days of the 10 Nov batch (p41, pool applied to every day, in sample) the account held a trade
about 109 minutes a day: flat about two-thirds of the 09:16 to 15:00 entry window.

## Why the profit feels thin

p41 offline account (apex/conductor/account_sim.py, `--asof all`): 111 trades, 60 won, ₹+10.87 lakh on 15 days, 4
losing days. Three days (26 Oct, 27 Oct, 6 Nov) gave 82 % of it; the median day was about +₹25,000. Those are the
days the c20 books were found on. Forward (live): 9 Nov +₹59,664, 11 Nov +₹7,439, 12 Nov +₹3,676.

## The current Conductor on every recorded day (p44, 13 Nov night)

Code as committed in 7a3deb5, pool applied to every day (`APEX_POOL_ASOF=all`, in sample before 9 Nov), seeded from
the 12 Nov learning files, account from `apex/conductor/account_sim.py --asof all` (`data/replay/batch/p44_sim`).
Four days (28 Oct, 30 Oct, 2 Nov, 3 Nov) stopped part-way, each on a refused `chain_latest.json` swap
(Windows access denied); their rows in `p44_sim` are partial. They were rerun alone as `p44_r1` to `p44_r4` (account in
`data/replay/batch/p44_simr`); the table uses the reruns.

| Day | Trades | Won | P&L ₹ | Day % | Minutes in a trade |
|---|---|---|---|---|---|
| 19 Oct | 18 | 8 | +21,775 | +21.8 | 103 |
| 21 Oct | 5 | 1 | +48,074 | +48.1 | 164 |
| 22 Oct | 3 | 2 | +7,771 | +7.8 | 72 |
| 23 Oct | 5 | 1 | +25,226 | +25.2 | 118 |
| 26 Oct | 6 | 6 | +2,60,920 | +260.9 | 103 |
| 27 Oct | 13 | 10 | +5,32,038 | +532.0 | 119 |
| 28 Oct | 5 | 4 | +56,235 | +56.2 | 203 |
| 29 Oct | 4 | 2 | +24,788 | +24.8 | 171 |
| 30 Oct | 3 | 0 | −5,558 | −5.6 | 56 |
| 2 Nov | 4 | 3 | +41,584 | +41.6 | 85 |
| 3 Nov | 13 | 7 | −36,254 | −36.3 | 102 |
| 4 Nov | 5 | 1 | −26,679 | −26.7 | 49 |
| 5 Nov | 1 | 0 | −5,902 | −5.9 | 65 |
| 6 Nov | 4 | 4 | +1,00,233 | +100.2 | 114 |
| 9 Nov | 22 | 11 | +43,166 | +43.2 | 111 |
| 11 Nov | 4 | 2 | +9,019 | +9.0 | 78 |
| 12 Nov | 4 | 1 | −3,978 | −4.0 | 109 |
| 17 days | 119 | 63 (53 %) | +10,92,458 | | |

Five losing days of 17; median day +₹24,788. 26 and 27 Oct gave 73 % of the profit, with 6 Nov 82 %. Every
day before 9 Nov is in sample (the c20 books were found on them).

Replay against live on the forward days: 9 Nov +₹43,166 replayed, +₹59,664 live; 11 Nov +₹9,019 and +₹7,439;
12 Nov −₹3,978 and +₹3,676. On 12 Nov the replay took the same three trades as live at the same prices, plus a
10:08 25350 CE from c20_9y (−₹7,585) that live never armed; the live engine's tick time had a p95 of 1.2 s around
the 10:02 top, the likely reason it read that impulse differently.

## Why the forecaster did not help

1. It is display only; the Conductor never reads it (by design, docs/48).
2. Its own gate needs 5 forward days before any direction or buy claim; its record started 11 Nov, so "no call" and
   "no buy case" were certain on 12 Nov.
3. Its direction skill is real but short. Walk-forward, models fitted only on earlier days, 11 sessions 27 Oct to
   11 Nov (`data/forecast_lab/walk_forward.json`), strongest fifth of leans:

   | Horizon | Right | Days with positive skill |
   |---|---|---|
   | 1 min | 67 % | 11 of 11 |
   | 2 min | 60 % | 11 of 11 |
   | 3 min | 59 % | 11 of 11 |
   | 5 min | 54 to 56 % | 9 to 10 of 11 |
   | 10 min and longer | about 50 % | about half |

   Its buy case is judged at 5 minutes, where the skill is nearly gone; its option-premium middle forecast is no
   better than "no change". (docs/48 already notes that 1 to 3 minute skill is largely feed lead-lag.)
4. Its agreement did not improve entries. The 2-minute lean rebuilt out of sample at each of 78 Conductor entries
   (27 Oct to 11 Nov): with the trade 51 trades, 51 % won, +3.5 % mean; neutral 12, +10.4 %; against 15, 80 % won,
   +10.5 %. Day by day the sign is unstable (against better on 3 of 7 days at 2 min, 5 of 7 at 3 min), so it is not a
   rule; it does rule out "confirm with the forecaster".
5. Under machine load it fell behind on 12 Nov: loop p95 up to 3.6 s, 2,468 skipped seconds, 1,726 failed writes of
   the dashboard file (the reader holding the file during the swap). The engine stayed under 1 s a step all day.

## Changes made the same evening (display only, no engine file)

* `core.plain()`: four plain rows (how far, which way for 2 minutes with its measured hit rate, the held trade or what
  a fresh buy needs, decay against movement) and a one-line headline; the dashboard shows them first and folds the
  old commentary under "Full notes". Tests: `tests/test_forecast_lab_plain.py`, the JS payload contract.
* Learning state: the 15:40 `state.json` (z80 0.75 after a wide-range day) was rejected whole by the loader's bounds
  (0.9 to 2.0) although the learner allows 0.6 to 3.5, so the next start would have dropped the day's learning for
  the older warm file. An out-of-bounds kappa or z80 is now reset on load and the rest is kept
  (`tests/test_forecast_lab_state.py`).
