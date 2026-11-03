# Why c20_9x loses live but profits on tape — ten-member review, 3 Nov 2026

Owner's question (3 Nov, after a −₹44,688 expiry day): *why is the code loss-making live when the champion is
profitable on taped data, and why is it still not trailing properly?*

Team: nine analysts (fills, exits, feed, expiry, divergence, clocks, robustness, carried state, display) and one
reviewer who re-opened every cited line and recomputed at least one number per analyst. Every finding below was
confirmed by the reviewer and the load-bearing ones were re-checked by hand against the code afterwards.
Records: `data/paper/*2026-11-03*`, `data/paper/*2026-11-02*`, `data/replay/2026-11-02/20261102-225710/`,
`data/logs/`, the tapes. Nothing was modified.

## 1. The short answer

**Live execution is not the problem.** On the only two days with both a live run and a replay of the same tape with
the same code, live *beat* the replay for the champion (30 Oct +₹2,019, 2 Nov +₹1,599). Today every one of the 24
fills used a quote 0.09–0.81 s old, the recorder dropped 0 of 4.77 M packets, and the data gaps are reproduced on
the tape to 0.1 s. There is no stale-print exit, no restart, no exception, no missed contract.

**The tape profit was never a forecast.** The "+₹9.30 L over 9 days" is 98 % in-sample: seven of the nine days are
the days every c20_9x parameter was fitted on (spec §11.3), two expiry tapes supply 60 % of it, and one 261-second
trade on 27 Oct (22700 CE 40.60 → 72.95) supplies 29 %. On the four days the strategy had never seen — 29 Oct
(tape), 30 Oct, 2 Nov and 3 Nov (live) — it made +24,788, −3,539, +43,183, −44,688: about ₹5k a day, not ₹1.3 L.

**Today's loss is the expiry mode meeting a day it was never tested on.** A gap-up grind with no 60-point leg:
five −15 % stops cost ₹71,058, the PE side alone ₹40,739, and the seven trades that did run (peaks +11 to +19 pts)
realised ₹26,371 of ₹1,05,752 available at their peak bids — **₹79,381 given back**.

**It is not trailing because, on an expiry day, c20_9x has almost nothing that trails** — and the dashboard was
showing a trail that belongs to a different book.

## 2. The exits c20_9x actually has on an expiry day

`apex/engine/council/c20_9x.py:172-187, :362`, `c20_8x.py:29`, `c20_08.py:26-28`:

| Exit | Rule | Today |
|---|---|---|
| SL | bid ≤ entry × 0.85 | fired 5× (−₹71,058) |
| Forward trail | smoothed parity forward 25 pts off its best since entry | never fired (≈16 premium pts at Δ 0.65 — the size of every peak) |
| TIME | 900 s after entry | fired 4× |
| BE_LOCK | arms at +15 % peak; floor = **entry** (BE_LOCK = 0.0) | fired 3× |
| GIVEBACK | arms at +60 % peak; keep 70 % of the gain | unreachable (peaks +1 to +19 %) |
| Premium trail (ptre) | arms at +70 % peak; 8 % off the peak bid | unreachable |
| Ramp floor, delta trail (ramp, dtr) | **normal days only** (`not dte0`) | off |

So between +15 % and +60 % the only floor is the entry price. Today's premiums were 47–112 and the peaks were
+14 to +19 %: exactly the dead zone. The exit reasons on all 12 trades are what the rules say; the replay will
reproduce them. The spec itself lists this as a cliff (§11.2) and notes that a ramp on expiry days "cut the
runners: −2.34 L" on the October tapes — which is why it was left out.

What the owner saw instead (`config.py` council entries inherit `_G`'s `spot_trail 12` / `lock_pct 18`;
`engine_main.py:1193-1200` skips `paper.check_exit` for council books so `stop_spot` / `lock_armed` are never set;
`engine_main.py:1450-1457` still publishes `on_spot` / `d_star` / `lock_pct` from those parameters): the band read
"Stop not set yet" and "LOCK ARMS AT +18 %" all day, the exit chip said only "COUNCIL" (`app.js` takes the first
word), and the commentary wrote 158 lines of `[giveback: TypeError]`. None of the real rules (BE floor, 25-pt
forward trail, 15-min clock) was ever on screen.

## 3. Why live and tape can never match trade for trade (and why that is not the loss)

1. **Sample phase.** The council book is stepped once per market second (`council/__init__.py:119-122`). The fast
   replay steps at exactly x.000; live lands at x.00–x.09 (11 of 12 entries today within 80 ms of the second).
   Entries fire at v = 20–22 against a threshold of 20, so a 0.1-s shift moves a trigger by one second and the fill
   by one print: ±₹700–1,900 per trade, random sign. Today's replay already took trade 1 one second earlier
   (+₹572 vs live −₹1,404). On 2 Nov only 14 of 68 books had identical trades; live was worse than the replay in
   53 of them (median −₹2,122) but better for the champion. Compare live and tape by day totals, never per trade.
2. **Fill timing.** With `FILL_NEXT_PRINT` the fill is the newest print at the council's next whole-second step
   (`paper.py:1053-1066`, `o["age"] >= waited`), not the first print after the trigger. On an expiry burst that is
   the top of the burst: 12:10:34 PE triggered at 76.25, first print after was 76.15, fill 80.95 (₹5,928);
   13:54:06 PE 59.80 → 62.25 → fill 63.30 (₹1,570). Trigger-to-fill slip today: ₹9,600 (entries +5.25 pts, exits
   −0.95 pts). The tape pays the same rule, so this is a cost of the strategy, not of live.
3. **Live-only: disk inside the tick.** `save_books` (2.1 MB JSON + fsync, `paper.py:1414-1425`) runs inside the
   engine tick on every trade and up to once a second while any book's best moves (`engine_main.py:1218-1228`);
   the fast replay skips it. Four of the 24 champion ticks that touched trades were 0.3–1.8 s late. Net effect today
   ≈ ±₹200 — noise — but it is the one clock effect that exists live and not on tape, and `loop_ms` is never logged.

## 4. What would have changed today (recorded bids, next-print fills, per-second walk)

| Change | Day P&L | Trades changed |
|---|---|---|
| As run | −44,688 | — |
| Expiry give-back trail: once bid ≥ entry + 5 pts, exit when bid falls 6 pts below its best | −9,370 (+35.3k) | 9 of 12 |
| Half-of-peak floor after +15 % (the normal-day ramp shape) | −18,590 (+26.1k) | 5 of 12 |
| Fill on the first print after the trigger | ≈ +7.5k | 12:10 and 13:54 entries |
| Lapse an entry whose first print is > 3 % above the trigger | +14,609 | skips 12:10 and 13:54 |
| No expiry-day entries at all | 0 (+44.7k) | all 12 |

Every money rule above is fitted to one day. The spec records that a floor of this shape cut the October expiry
runners (−2.34 L) and D-147 records c20_9t's trail turning the 9-day +9.30 L into +3.89 L. None of them should trade
before it is replayed on the three expiry tapes (19 Oct, 27 Oct, 3 Nov) and beats c20_9x on all three.

## 5. Recommended order

1. **Display and records (no P&L risk).** Council positions: publish the real floor (kind + level), the 25-pt forward
   trail level, SL = entry × 0.85 and the 15-min clock; stop publishing `on_spot` / `d_star` / `lock_pct` for council
   books; `code()` in `app.js` to use the second word of "COUNCIL X"; guard the give-back commentary template; store
   the exit wait as `exit_fill_delay_s` (today `fill_delay_s` is overwritten at exit, `paper.py:1262, 1312`); write
   each council veto (ivz / stale / tie) to `decisions_<day>.jsonl`; log `loop_ms` p50/p95 once a minute.
2. **Decide the expiry mode.** Either keep c20_9x out of expiry days until its dte0 branch has beaten the three
   expiry tapes, or test the 5-pt-arm / 6-pt-give trail on them first. Both need replays (≈2 h per tape).
3. **Fill on the first print after the trigger** (run the fill check on every engine tick, not once a second).
   Changes every replay number by a few points, so the 9-day figure must be rerun before comparing.
4. **Take disk out of the tick** (background writer; restart save only on open / close / floor armed / exit).
5. **Promotion rule for future champions:** tape P&L counts only on days the candidate was not fitted on, must keep
   its sign with the best day removed, and with the replay clock offset by +0.05 / +0.3 / +0.6 s.

## 6. Minor findings (₹0 today)

- 2 Nov live session ended without `end_day` (no `trades_2026-11-02.csv`, tape truncated, no "closed and learned").
- A same-day restart would lose the strategy's in-memory trail state and any pending entry (only `pos['st']` and
  `peak_bid` persist).
- Whether the ivz / stale vetoes fired today cannot be checked: they log only in memory.

## 7. Today's tape, replayed (finished 18:08; `data/replay/2026-11-03/20261103-154519/`)

Same code, same tape: c20_9x took the **same 12 trades** (same strikes, sides and exit codes; entries within 0–5 s
of live) and lost **₹40,986 against ₹44,688 live**. Ten of the twelve exits are within a print of each other; the
two that differ are the sample-phase shifts of §3: trade 1 entered one second earlier (94.45 vs 93.75) and left on
the floor nine minutes earlier (+572 vs −1,404), and trade 2 left on the forward trail at 95.65 instead of the −15 %
stop at 94.90 (−12,591 vs −14,112). The other council books agree (c20_9t −20,673 vs −29,390; c20_8x −55,149 vs
−60,340); across all 68 books the replay lost ₹11.84 L against ₹13.16 L live, with identical trades in 20. The tape
does not make today profitable: the loss is the strategy's, not the live path's.

## 8. The expiry trail on the three expiry tapes (replayed 3 Nov evening, runs `20261103-205612`)

Owner: "Yes, run the tapes." Two shadow books were added beside c20_9x and the three expiry tapes replayed with the
same engine: **c20_9e** (expiry days: once the peak bid is +5 pts the floor is peak − 6 pts, exit EXP_TRAIL) and
**c20_9h** (expiry days: half-of-peak floor from +15 %, exit HALF_LOCK). Normal days are c20_9x in both.

| Book | 19 Oct | 27 Oct | 3 Nov | Three days |
|---|---|---|---|---|
| c20_9x (champion) | +39,904 | +5,18,352 | −40,986 | **+5,17,270** |
| c20_9e (5-pt arm / 6-pt give) | +29,412 | +92,268 | −12,152 | +1,09,528 |
| c20_9h (half of peak from +15 %) | +9,444 | +51,750 | −39,744 | +21,450 |
| c20_9t (rent trail, shadow) | +9,539 | +1,71,239 | −20,673 | +1,60,105 |

**Both fail the test set in §4.** The trail does what it did on 3 Nov (−12,152 against −40,986, 10 of 14 exits
EXP_TRAIL) but on the two profitable expiry tapes it sells every runner 6 pts off its first peak: the 27 Oct 22700 CE
40.60 → 72.95 (+2.73 L) leaves at 55.55 (+2.1 k), the 10:17 PE 123.60 → 187 (+64 pts) leaves at 122.50, and 21 of 26
exits on 19 Oct are the trail at +2..+12 pts. The half-of-peak floor loses on all three. The rent trail (c20_9t)
is the best of the three alternatives and still gives up 69 % of the champion's three-day total.

So the 3 Nov loss is the price of the expiry mode that paid +5.58 L on the other two expiry days; a tight premium
trail removes both. The books stay registered as shadows (no champion change). What is left for the owner to decide
is §5 item 2: trade expiry days with c20_9x as it is, or keep it out of them.
