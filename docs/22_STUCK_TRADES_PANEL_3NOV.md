# Stuck trades — ten-member panel C11, 3 Nov 2026 (night)

Owner: *"Why are sometimes the trades held on for around 15 mins and it still does not decently trail out nor does
it book profit. What is the problem in entries for those times."* and *"We cannot be sitting on a trade for 15 mins
or higher if it is not performing."*

Method: the offline kit (fills at the ask 2 s after the signal, bid out) running the exact c20_9x class on eleven
tapes (19 Oct – 3 Nov, three expiry days). Kit numbers compare variants with each other; they are not engine P&L.
c20_9x, kit: +11,49,850. A "stuck" trade = held >= 10 min with peak < +15 %: 15 trades, −77,847.

## Why the trades sit there

* **Normal days (11 of 15 stuck, where the money is lost).** Every one is a pullback entry into an impulse that had
  already ended: the arming breakout printed a median ~4 min (up to 10+ min) before the buy, ~29 pts behind its
  extreme. After entry the forward adds ~4 pts by 3 min and ~20 pts by 8 min. The 40-pt trail is wider than any
  move, the ramp floor never arms, and the trade leaves on FWD_TRAIL at −1..−12 % after 14–53 min. Theta is not
  the cause (~0.3 pts per 10 min). They come later in the day and in lower-IV tape.
* **Expiry days (4 stuck, incl. today's four TIME exits).** CE breakouts at the minimum velocity (+20..22), high
  delta (0.65–0.73), at or within 11 pts of the day's high; the move stalled. Three of the four closed in profit;
  3 Nov's loss was mostly the five stop-losses.

## Why "exit if not performing" fails

Before ~8 min stuck trades and runners are not separable by price path: several of the biggest winners (19 Oct
09:52 PE +1.12 L, 26 Oct 10:31 / 11:20, 27 Oct 12:31 CE) were flat or under water at 2–5 min.

| Rule (one panel member each) | Kit vs c20_9x | Verdict (red team reproduced every number) |
|---|---|---|
| Progress clock: 5 min / +3 %, 10 min / +8 % | +11,300 | cliff: nudges −58k / −68k (cuts 26 Oct runners) |
| Forward stalled 5 min, peak < +10 % | −14,771 | every setting loses |
| Theta paid > gain after 15 min | −47,993 | every setting loses |
| Option queue ratio fall after 8 min | +17,238 | cliff: −35k at Q 0.96 |
| Normal-day 20-min / −8 % stop | +11,368 | one day; nudges turn negative |
| Expiry entry: forward moved 5 pts in last 60 s | +54,948 | one 19 Oct trade; nudges cost 27 Oct −14k |
| **Stale-impulse pullback veto (660 s, normal days)** | **+76,342** | **passes** |

## The surviving rule — c20_9s (shadow book)

On a normal day, refuse a pullback buy when the breakout that armed it first printed more than 660 s (11 min)
earlier. Expiry days, every exit, the picker, cooldown and seq veto are c20_9x.

| | c20_9x | c20_9s |
|---|---|---|
| Kit total, 11 days | +11,49,850 | +12,26,193 |
| Stuck trades | 15, −77,847 | 10, −31,307 |
| Expiry days | — | identical |
| 29 Oct, 30 Oct, 2 Nov, 3 Nov (never fitted) | +3,832 | +67,207 |

Weaknesses: six skipped trades make the whole gain (29 Oct +35k); plateau ~650–790 s (528 s keeps 53 %, 480 s cuts
the 21 Oct runner, 600 s the 28 Oct runner); leave-one-day-out +33k; it avoids stuck entries rather than exiting
them; expiry-day stuck trades are untouched. Promotion only after it keeps its edge on new days and in an engine
replay. Panel material: scratchpad `team3/` (brief, autopsy CSV, each member's rule.py, red-team combos).
