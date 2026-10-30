# ApexOptions — proposed strategy "c20_8x": complete specification for independent review

*29 October 2026. Prepared for the owner to send to other AI models for a thorough, independent analysis.*

**Status.** Proposal only. The owner's live system still trades the champion `t28_gap` and is unchanged. `c20_8x`
exists only in an isolated development copy of the code. A full engine replay of all 7 taped days (`c20_8x`, its
parent `c20_08` and the champion side by side) is running. Nothing is promoted until the owner decides on the
engine-verified numbers.

**How to read this document.** Sections 1–3 give the background and the results. Sections 4–15 say exactly what the
code does, second by second, with every formula and every number. Section 16 is the full parameter table, section 17
is pseudocode, section 18 the evidence and section 19 the known weaknesses and open questions. Reviewers are asked
to look especially hard at sections 18 and 19.

---

## 1. The owner's fixed rules (not open to change)

| Rule | Meaning in the code |
|---|---|
| Instrument | NIFTY weekly index options only |
| Direction | Buy only. Never sell or write options |
| Capital | Rs 1,00,000 fresh every trading day; profits and losses compound within the day only |
| Sizing | **All-in on every trade**: buy as many lots as the capital allows. No position sizing, ever |
| Strikes | ATM or in-the-money only: absolute delta ≥ 0.52 at entry |
| Expiry | On expiry day trade the expiring weekly; other days trade the nearest weekly |
| Positions | One position at a time |
| Mode | Paper trading only |

Lot size is 65. In the taped period the nearest weekly expired on 19 Oct and on 27 Oct (the next expiry is 3 Nov).

---

## 2. How this strategy was chosen

1. **The champion today, `t28_gap`**, buys pullbacks on the Nifty spot index (a 60-pt impulse inside 45 minutes,
   then a 50–78 % pullback). Engine replay of 7 taped days, real fills: **+Rs 3,72,630**, 5 of 7 days green. Live on
   29 Oct it sat out a ~215-pt rally because no pullback came.
2. **A 20-member council** (29 Oct) each built a different strategy with full freedom, tested on the same 7 days with
   a shared test kit (section 18.1). Only **member 08** clearly beat the champion and survived out-of-sample testing:
   +Rs 4,42,595, 6 of 7 days green, worst day −1,212.
3. **A 10-member autopsy team** then took member 08's strategy apart trade by trade (all 56 trades: entry context,
   greeks, derivatives, best and worst price during the trade, exit reason), classified every losing and low-profit
   entry, traced every missed big move, and each tested one improvement inside member 08's framework. A final member
   tested every combination of the improvements (a factorial), trade by trade, with leave-one-day-out selection.
4. **Result: `c20_8x` = member 08 + four changes** (two for expiry days, two for normal days). Kit result
   **+Rs 8,46,648, 7 of 7 days green, worst day +20,933**; leave-one-day-out **+Rs 6,57,700**.

---

## 3. What is in the final code, and what was rejected

### 3.1 Included (decided by the autopsy team's factorial, pending the engine replay)

| # | Change | Applies | Source | Why it was kept |
|---|---|---|---|---|
| — | Member 08's two-mode engine on the put-call-parity forward | both | council member 08 | the only council idea that beat the champion out of sample |
| A | **Sequence rent gate** ("seq"): after a losing trade, an entry on the OTHER side within 15 minutes needs the market's realised movement to pay at least 0.25 × the option's time decay | both in code; bites only on expiry days | autopsy member 08 | removed ~5 losing expiry whipsaw flips; positive out of sample in both directions |
| B | **Premium exits** ("pex"): once the bid has been ≥ +15 % above entry, never close below the entry price; once it has been ≥ +60 %, keep at least 70 % of the peak gain | both in code; on the 7 days it changed only expiry trades | autopsy member 06 | fixed the biggest give-backs without cutting any big winner |
| C | **Pullback geometry** ("pbg"): on normal days, abandon a "pullback" that retraces more than 75 % of the impulse (a reversal) or an impulse armed more than 15 minutes ago | normal days | autopsy member 02 | removed 4 losers, lost no winner; chosen in every out-of-sample fold |
| D | **Shallowest eligible strike on normal days** ("d52"): target absolute delta 0.52 instead of 0.60 | normal days | autopsy member 07 | more premium per Nifty point at negligible extra theta on non-expiry days; chosen in every fold |

### 3.2 Tested and rejected (do not add these)

| Add-on | Result | Reason |
|---|---|---|
| Exhaustion exit (fade signal as exit) | −1.39 L | cut the +86 %, +78 % and +61 % winners |
| Profit cap (exit at half of peak gain after +30 %) | −73k | cut runners |
| Gamma-rent gate on every normal-day entry | −60k | removed winners |
| Level booking at prior-day H/L/C and round 100s (the champion's exit) | −31k | booked +61 % and +78 % runners at +14 % and +49 % |
| Opening-range direction lock (normal days) | −6k net | +58k on 21–23 Oct, −65k on 26 and 28 Oct |
| Opening-range lock on expiry days | −1.30 L on 27 Oct | |
| IV-rise guard (no buy if IV rose > 0.3 vol pt in 3 min) | mixed | +1.62 L on the two expiry days in one study, but rising IV did not separate winners from losers in two others; substitutes for the chosen guard |
| No expiry entries after 13:30 | | overlaps the chosen guard; a clock tuned on two days |
| Theta cap (no expiry entry if theta > 1 % of premium per minute) | | cliff one notch away |
| Expiry range-width guard (broken 10-min range must be ≥ 40 pts) | +1.54 L in-sample | knife edge: 2.1× vmin gives 55k, 2.2× gives −0.2k on 27 Oct. Kept as the documented **backup** to change A |
| Stacking several expiry entry guards together | +1.16 L total only | they all remove the same afternoon losers; pairwise interactions strongly negative |
| Waiting for a dip / for acceleration to cool before entering | | no rule made money on both expiry days |
| Catch-the-trend entries when no pullback comes | LODO halved the normal-day result | in an all-in one-position book an extra entry can push out the day's one big winner |

---

## 4. Data the strategy uses (every second)

All decisions are taken **once per second**. Row `i` = seconds since 09:15:00 IST on the trading day
(`i = 0` at 09:15:00, `i = 22,500` at 15:30:00). The strategy may read only rows `≤ i` (no look-ahead).

| Symbol | What it is | How it is produced |
|---|---|---|
| `F_i` | **Put-call-parity forward** of the nearest weekly expiry | the engine's live synthetic forward: from the CE and PE mid prices at the strikes nearest the reference where both legs quote, F = K + (C − P) (`apex/greeks.py synthetic_forward`). Legs whose quote is older than `IV_LEG_MAX_AGE_S` are excluded. Recomputed every 0.25 s; the strategy reads it once per second and treats it as missing if it is older than 2 s |
| `S_i` | Nifty spot index | used only as a fallback for the ATM strike if F is missing |
| `bid, ask, ltp` | each option's best bid, best ask, last traded price | live quotes; `mid = (bid + ask)/2` when both are valid |
| `age` | seconds since that option's quote was received | live |
| `IV` | implied volatility of each option | Black-76, 40-step bisection on the mid, forward `F`, time to expiry `T` |
| `delta, gamma` | Black-76 greeks of each option | on `F`, `T`, `IV` |
| `theta` | **time decay in premium points per minute**, negative | `theta_year / 365 / 375`, i.e. one day's decay spread over 375 trading minutes (see section 19.2) |
| `T` | time to expiry in years | calendar seconds to 15:30 on expiry day ÷ (365 × 86,400); floored at 600 s on expiry day and 60 s otherwise |

**Smoothed forward.** `fs_i` is a causal exponential moving average of `F` with a 5-second time constant:

```
fs_i = fs_{i-1} + (F_i − fs_{i-1}) / 5        (if fs_{i-1} exists)
fs_i = F_i                                     (otherwise: first value, or after a gap)
```

**Rolling range.** `HI_W(i)` and `LO_W(i)` = the highest and lowest `fs` over the previous `W` seconds, **excluding
the current second** (rows `i−W … i−1`), maintained with monotonic queues.

**Velocity over L seconds.** `v_L(i) = fs_i − fs_{i−L}` (forward points moved over the last `L` seconds).

**Realised rent ratio** (used by change A only):

```
RV(i)  = mean over k in the last 600 s of ( F_k − F_{k−60} )²      (raw forward, 60-second changes)
rent   = 0.5 × gamma × RV / |theta|                                (for the contract about to be bought)
```

`rent` compares what the option earns from the market's actual movement (gamma × squared move) with what it pays in
time decay per minute. Above 1 the movement pays the decay; below 1 it does not. The threshold 0.25 is in the
375-minute theta convention (≈ 0.96 in calendar-minute theta — section 19.2).

---

## 5. The trading day at a glance

| Time | What happens |
|---|---|
| 09:15:00 | Data starts. The smoothed forward and the rolling windows begin filling |
| 09:16 | Earliest time the strategy is allowed to consider entries (`t0`) |
| ≈ 09:25:02 | **Expiry day:** the first entry becomes possible once 600 s + 2 s of forward history exist |
| ≈ 09:35:02 | **Normal day:** the first impulse can arm once 1,200 s + 2 s of history exist |
| 14:40 | **Expiry day:** last new entry (`t1`) |
| 15:00 | **Normal day:** last new entry (`t1`). **Expiry day:** any open position is closed |
| 15:20 | **Normal day:** any open position is closed |

---

## 6. Mode selection

Each morning the strategy checks whether today is the expiry date of the nearest weekly contract.
- **Yes → EXPIRY mode** for the whole day (sections 7, 9, 10).
- **No → NORMAL mode** for the whole day (sections 8, 9, 10).

The two modes share the smoothed forward, the contract picker, the order handling and the exits; they differ in how
an entry is triggered and in their parameters (section 16).

---

## 7. Expiry-day entry — step by step

Evaluated every second while **no position is open**:

1. **Time window:** `09:16 ≤ time < 14:40`.
2. **Cooldown:** at least **60 s** since the last exit.
3. **History:** at least `W + 2 = 602` seconds of data, and `fs_{i−600}` exists.
4. **Breakout plus speed:**
   - **CE (bullish)** if `fs_i > HI_600(i)` **and** `v_150(i) = fs_i − fs_{i−150} ≥ +20` points;
   - **PE (bearish)** if `fs_i < LO_600(i)` **and** `v_150(i) ≤ −20` points.

   In words: the smoothed forward has just broken out of its last-10-minutes range, and has moved at least 20
   points in the breakout direction over the last 2.5 minutes.
5. **Contract:** pick the strike (section 9) with target |delta| **0.65** (about 1 strike in the money).
6. **Veto check:** the sequence rent gate (section 10). If it vetoes, no trade this second (the signal can fire again
   next second if the conditions still hold).
7. Otherwise → **BUY** the chosen contract, all-in (section 11).

---

## 8. Normal-day entry — step by step (impulse → pullback → resumption)

The normal mode does **not** buy the breakout itself. It waits for the breakout impulse to pull back and then turn
again in the impulse's direction.

**8.1 Arming.** Every second, with no position open, the breakout test of section 7 is computed with the normal-day
parameters: `W = 1,200 s` (20-minute range), `L = 1,200 s`, `vmin = 40` points.
- If a breakout fires on side X and nothing is armed (or the armed side is the other side), the strategy **arms**:
  it records the side X, the impulse **base** `fs_{i−1200}`, the **extreme** `= fs_i`, the **pullback extreme**
  `= fs_i`, and the **arm time** `= i`.
- If a breakout fires again on the **same** armed side, the extreme moves to the new `fs` (if further) and the
  pullback extreme resets to the extreme. **The arm time does not reset.**
- A breakout second never produces an entry by itself.

**8.2 While armed** (seconds with no new breakout):
1. **Disarm on age:** if more than **900 s** (15 min) have passed since the arm time → disarm, nothing bought.
2. Update the **extreme** (furthest `fs` in the impulse direction) and the **pullback extreme** (deepest `fs` against
   it since the extreme).
3. `impulse = |extreme − base|`; `retrace = distance from the extreme back to the pullback extreme`.
4. If `retrace < 0.50 × impulse` → keep waiting (the pullback is not deep enough yet).
5. **Disarm on depth:** if `retrace > 0.75 × impulse` → disarm. This is a reversal, not a pullback.
6. **Resumption trigger:** if `fs` has moved **≥ 5 points** back from the pullback extreme in the impulse direction
   → **signal side X** and disarm.

**8.3 Entry.** On a resumption signal, and only within `09:16 ≤ time < 15:00` and at least 60 s after the last exit:
pick the contract (section 9) with target |delta| **0.52**, run the veto check (section 10), and BUY all-in
(section 11).

*Example (illustration only, not a real trade).* At 10:40 the smoothed forward breaks above its 20-minute high and is
45 points above where it was 20 minutes ago: CE side armed, base 25,100, extreme 25,145. It rises to 25,160
(impulse 60). It then falls to 25,125: retrace 35 = 58 % of 60, inside the 50–75 % band. At 10:49 it rises to
25,130, 5 points off the low: BUY the CE with |delta| nearest 0.52. Had it fallen to 25,110 (retrace 50 = 83 %), or
had 10:55 passed without a trigger, the arm would have been dropped.

---

## 9. Contract selection (both modes)

1. **ATM strike** = the listed strike nearest the forward `F_i` (spot if F is missing).
2. **Candidates:** for the signalled side (CE or PE), the strikes ATM − 150, −100, −50, ATM, +50, +100, +150.
3. **Eligible** if: the contract exists in the nearest weekly; its ask is valid and positive; its quote is at most
   **5 s** old; its **|delta| ≥ 0.52** (owner's ATM/ITM rule).
4. **Choose** the eligible contract whose |delta| is **closest to the target**: 0.65 on expiry days, 0.52 on normal
   days.
5. If none is eligible → no trade this second.

Why these targets. On expiry days 1-ITM (|delta| ≈ 0.65) gave about 70 % of ATM's premium % per forward point at
about half the theta (0.67 % vs 1.26 % of premium per minute); no other rule beat it on both expiry days. On normal
days theta is ≈ 0.03 % of premium per minute, so the shallowest eligible strike's extra leverage is almost free.

---

## 10. Entry veto — the sequence rent gate (change A)

Applied to every BUY signal (both modes; on the 7 taped days it never blocked a normal-day entry):

```
if  the last closed trade LOST money (bid at the exit second < entry price)
and the new signal is on the OTHER side (CE after a PE loss, or PE after a CE loss)
and fewer than 900 s have passed since that exit
then compute rent (section 4) for the contract about to be bought
     if rent < 0.25  → VETO (no trade this second)
```

In words: right after a losing trade, flipping to the other side is allowed only if the market is actually moving
enough to pay the new option's time decay. This targets the afternoon whipsaws of expiry days (19 Oct after 12:15).
A same-side re-entry, a flip after a winning trade, or any entry more than 15 minutes after the loss is not gated.

---

## 11. Placing the order and sizing (owner's all-in rule)

- **Lots** = floor( capital ÷ (option price × 65) ). Quantity = lots × 65. If fewer than 1 lot is affordable, no
  trade.
- **Capital** starts each day at Rs 1,00,000 and changes by each closed trade's profit or loss (compounding within
  the day).
- **In the engine (paper):** the position opens at the option's **last traded price** at the signal second; the bid
  and ask at that moment are recorded with the trade.
- **In the test kit:** the position is bought at the **ask, 2 seconds after the signal**, and sold at the **bid,
  2 seconds after the exit signal** ("real fills"). All headline numbers in this document are real fills. The
  engine's trades are scored the same way (entry ask in, exit bid out).
- **Engine safety checks at entry:** no entry during a data blackout (feed gap) or when the kill switch is on; the
  option must have a valid last price and a quote at most `EXIT_QUOTE_STALE_S` seconds old; |delta| ≥ 0.5 as a
  final safety net (the strategy itself enforces 0.52).

---

## 12. While holding — what is tracked every second

- **Best forward since entry:** for a CE, the highest `fs` since entry; for a PE, the lowest. Initialised to `fs` on
  the first second of the trade.
- **Forward give-back:** `best − fs_i` (CE) or `fs_i − best` (PE), in forward points.
- **Peak bid:** the highest bid of the held contract since entry (initialised to the bid at entry).
- **Peak gain:** `peak bid ÷ entry price − 1`.
- **Time held:** seconds since entry.
- The strategy keeps updating its smoothed forward and range windows every second (needed for the next entry).

---

## 13. Exits — checked every second, in this order (first one that fires wins)

| Order | Exit | Rule | Expiry | Normal |
|---|---|---|---|---|
| 0 | **Forced flat** (engine adapter, checked before the strategy runs) | time ≥ 15:00 (expiry) / 15:20 (normal) | yes | yes |
| 1 | **Premium stop** (SL) | bid ≤ entry × (1 − 0.15) | −15 % | −15 % |
| 2 | **Forward trail** (FWD_TRAIL) | forward give-back ≥ trail | 25 pts | 40 pts |
| 3 | **Time clock** (TIME) | time held ≥ hold | 900 s (15 min) | 5,400 s (90 min) |
| 4 | **Give-back cap** (GIVEBACK, change B) | peak gain ≥ +60 % **and** bid ≤ entry × (1 + 0.70 × peak gain) | yes | yes |
| 5 | **Break-even lock** (BE_LOCK, change B) | peak gain ≥ +15 % **and** bid ≤ entry × (1 + 0) | yes | yes |

Notes:
- A take-profit target exists in the code but is switched off (set to +990 %).
- The forward trail measures give-back of the **underlying forward**, not of the premium. A 25-point give-back on
  expiry day costs more premium on a big winner because its delta has grown (from ≈ 0.60 at entry to ≈ 0.80 at the
  peak). The give-back cap (4) limits exactly that case.
- The break-even lock (5) sets the floor **at** the entry price. Setting it 3 % above entry collapsed the result
  (+3.27 L instead of +5.92 L in the autopsy study), so it must stay at or below entry.
- **Example (illustration only).** Entry ₹200. The bid reaches ₹236 (+18 %): the lock is armed, the floor is ₹200.
  The bid later reaches ₹330 (+65 %): the give-back cap is armed with floor 200 × (1 + 0.7 × 0.65) = ₹291. If the bid
  falls to ₹291 → exit (GIVEBACK), unless the forward trail, stop or clock fired first.

---

## 14. After an exit

- **Cooldown:** no new entry for 60 seconds.
- The best-forward tracker is reset.
- **Last-trade memory** (for change A): side, whether it lost money (bid at the exit signal vs entry price) and the
  exit second.
- A normal-day arm, if any, continues independently; a new entry is possible as soon as the next signal and the
  cooldown allow. A same-side re-entry into a new breakout is allowed.

---

## 15. End of day and data safety

- Positions are force-closed at **15:00 on expiry day** and **15:20 on other days**.
- No new entries after the mode's `t1` (14:40 expiry, 15:00 normal).
- If the forward is missing or older than 2 s, the strategy does nothing that second (the smoothed forward restarts
  from the next valid value).
- During an engine **data blackout** (feed gap) no new entry is placed. Exits are still evaluated by the strategy, and
  the engine sells at the last price.
- Options with quotes older than 5 s are not eligible to buy.

---

## 16. All parameters

| Parameter | Expiry mode | Normal mode | Meaning |
|---|---|---|---|
| `tau` | 5 s | 5 s | EMA time constant of the smoothed forward |
| `W` | 600 s | 1,200 s | breakout window (previous range length) |
| `L` | 150 s | 1,200 s | velocity lookback |
| `vmin` | 20 pts | 40 pts | minimum forward move over `L` |
| entry type | breakout | impulse → pullback → resumption | |
| `pb` | — | 0.50 | minimum retrace, fraction of the impulse |
| `PB_DMAX` (change C) | — | 0.75 | maximum retrace before disarming |
| `PB_AMAX` (change C) | — | 900 s | maximum age of an arm |
| `rs` | — | 5 pts | resumption distance from the pullback extreme |
| target \|delta\| (change D) | 0.65 | **0.52** | contract choice |
| minimum \|delta\| | 0.52 | 0.52 | owner's rule |
| max quote age to buy | 5 s | 5 s | |
| `sl` | 15 % | 15 % | premium stop |
| `trail` | 25 pts | 40 pts | forward trail |
| `hold` | 900 s | 5,400 s | time clock |
| `cool` | 60 s | 60 s | cooldown after an exit |
| `t0` / `t1` | 09:16 / 14:40 | 09:16 / 15:00 | entry window |
| forced flat | 15:00 | 15:20 | |
| `SEQ_S`, `SEQ_C` (change A) | 900 s, 0.25 | 900 s, 0.25 | sequence rent gate window and threshold |
| rent RV window | 600 s of 60-s changes | same | |
| `GB_ARM`, `GB_KEEP` (change B) | +60 %, 0.70 | same | give-back cap |
| `BE_ARM`, `BE_LOCK` (change B) | +15 %, 0 % | same | break-even lock |
| take-profit | off | off | |
| lot size | 65 | 65 | |

---

## 17. Pseudocode (one call per second)

```
on_second(i):
    if new day: reset all state; mode = EXPIRY if today == weekly expiry else NORMAL
    F = forward(i); if F missing or stale: return nothing
    fs_i = EMA(fs_{i-1}, F, tau=5)
    update rolling HI_W / LO_W with fs_{i-1}

    if holding a position:
        best = max/min(best, fs_i); give = |best - fs_i| in the adverse direction
        bid  = bid of held contract; peak_bid = max(peak_bid, bid)
        if bid <= entry*(1-0.15):                       SELL "SL"
        elif give >= trail[mode]:                       SELL "FWD_TRAIL"
        elif held >= hold[mode]:                        SELL "TIME"
        elif peak_gain >= 0.60 and bid <= entry*(1+0.70*peak_gain):   SELL "GIVEBACK"
        elif peak_gain >= 0.15 and bid <= entry:        SELL "BE_LOCK"
        on SELL: last_exit = i; last = (bid/entry - 1, side, i)
        return

    if time outside [t0, t1) or i - last_exit < 60 or not enough history: return nothing
    v = fs_i - fs_{i-L}
    side = CE if fs_i > HI_W and v >= vmin;  PE if fs_i < LO_W and -v >= vmin;  else none
    if mode == NORMAL: side = pullback_state_machine(side)        # section 8
    if side is none: return nothing
    contract = pick(side, target_delta[mode])                     # section 9
    if contract is none: return nothing
    if last lost and side != last.side and i - last.i < 900 and rent(contract) < 0.25:
        return nothing                                            # section 10
    BUY contract all-in                                           # section 11
```

The source files (development copy): `apex/engine/council/c20_08.py` (core), `c20_20.py` (a switchable layer class;
only its pass-through is used), `c20_8x.py` (the four changes, `FINAL = ("exp", "norm", "seq", "pex", "pbg", "d52")`)
and `apex/engine/council/__init__.py` (the adapter that feeds the engine's live data to the strategy and places
orders through the engine's paper broker).

---

## 18. Evidence

### 18.1 How it was tested

- **Data:** 7 fully taped sessions: 19 (expiry), 21, 22, 23, 26, 27 (expiry), 28 Oct 2026. The tape has every
  quote for Nifty spot, futures and every strike of the nearest weekly. 29 Oct (live) is excluded from all research.
- **Test kit:** a per-second simulator on that tape: fills at the ask 2 s after the signal and at the bid 2 s after
  the exit signal, all-in, Rs 1 L per day, one position at a time, quotes older than 10 s untradeable, forced flat
  15:20 (15:00 expiry). **Calibration:** re-pricing the champion's 62 engine trades through the kit reproduced the
  engine's per-trade real-fill returns with correlation 0.988–1.000 and a mean difference within ±0.7 percentage
  points on every day.
- **Leave-one-day-out (LODO):** every tuned choice is picked on 6 days and scored on the 7th; the held-out results
  are summed. With only two expiry days, expiry choices are picked on one expiry day and scored on the other.
- **Robustness:** every parameter moved one step either side.
- **Big moves:** 112 catalogued moves (ATM option +25 % within 15 minutes); a strategy "caught" a move if it held the
  right side during it.

### 18.2 Per-day results (kit, real fills, Rs)

| Day | c20_8x (proposed) | c20_08 (member 08) | t28_gap (champion, engine) |
|---|---|---|---|
| 19 Oct (expiry) | +1,28,500 | +71,191 | +1,24,144 |
| 21 Oct | +29,100 | +26,111 | +83,255 |
| 22 Oct | +20,900 | −1,212 | +16,000 |
| 23 Oct | +50,900 | +25,613 | +1,40,921 |
| 26 Oct | +1,57,700 | +1,47,628 | −2,753 |
| 27 Oct (expiry) | +4,06,700 | +1,42,015 | +35,264 |
| 28 Oct | +52,700 | +31,249 | −24,201 |
| **Total** | **+8,46,648** | **+4,42,595** | **+3,72,630** |
| Green days | 7/7 | 6/7 | 5/7 |
| Worst day | +20,933 | −1,212 | −24,201 |
| Trades / win rate | 49 / 59 % | 56 / 52 % | 62 / 53 % |
| Big moves caught | 34 / 112 | 38 / 112 | 25 / 112 |
| Leave-one-day-out | **+6,57,700** | +1,48,746 | — |

(c20_8x per-day values are rounded to the nearest Rs 100 from the factorial report.)

### 18.3 Robustness of the four changes

- **A, sequence rent gate:** threshold 0.15–0.35 → expiry 2-day total +4.22 L to +5.35 L, always above member 08
  (+2.13 L). Window 1,200–1,800 s similar; 300–600 s smaller gains; RV window 300 s turns it negative.
- **B, premium exits:** give-back arm +50/60/70/80 % → +5.47 / 5.92 / 5.92 / 5.86 L (on member 08); keep 0.6/0.7/0.8
  → +5.49 / 5.92 / 6.16 L; lock trigger +12 % → +5.83 L, +20 % → +5.24 L; **lock level +3 % → +3.27 L (cliff)**.
- **C, pullback geometry:** retrace limit 0.70–0.80 identical; age limit 720 / 900 / 1,200 s → normal days +2.95 /
  2.83 / 2.59 L; retrace limit 0.65 cuts a 0.67-retrace winner on 26 Oct.
- **D, strike:** target 0.55 same as 0.52; 0.60 / 0.65 / 0.70 progressively worse on normal days.
- **Member 08's own parameters stay fragile:** expiry `L` and `W`, and normal `L` (900 / 1,800 s → −19k / −44k).

### 18.4 What the autopsy found (all 56 member-08 trades)

- **31 of 56** trades lost or made under +5 % (17 on expiry days, 14 on normal days).
- **Delta decides the result.** A second-order Taylor split (delta, gamma, theta, vega, spread) reproduces each
  trade's premium change; the delta term alone explains R² = 0.988 of trade returns. The other greeks roughly wash
  out. Losers are direction failures, not IV crush.
- **Main entry mistakes:**
  1. Expiry entries where the market moved less than the option's time decay costs (low rent), mostly after
     12:15: 13–14 bad trades.
  2. Expiry breakouts of a narrow 10-minute range (< 40 pts): 13 of 16 were bad. Losers were bought in the middle
     of a 10–30 s spike (10-s acceleration +113 vs +49 pts/min² for winners) and peaked about 1 minute after entry,
     vs 7 minutes for winners.
  3. Whipsaw flips within 15 minutes of a loss on the other side.
  4. Normal-day "pullbacks" that retraced > 75 % (reversals) or came from impulses > 13–15 minutes old.
  5. Give-backs: 12 trades reached ≥ +10 % and still closed under +5 %.
- **Missed big moves (74 of 112):** 29 while holding the other side (mostly the reversal after our own winner's
  peak), 10–11 after the 14:40 expiry cutoff (moving it to 14:50 cost Rs 20k), 16 normal-day impulses that never
  pulled back, the rest triggers missed by small margins, warm-up or cooldown. Attempts to catch these lost money
  out of sample.
- **Strike:** re-pricing every trade at ATM–3 ITM showed the strike is a leverage dial (losers lose least deep ITM,
  winners win most shallow); hindsight "best strike" is not a usable rule.

### 18.5 The council's general findings (useful context)

- Breakouts of the forward's range alone are a coin flip; raw velocity/acceleration alone has no edge; order flow,
  OI as a trigger, a walk-forward statistical model and fading moves all failed out of sample.
- Triggering the champion's own pullback logic on spot (with its misprint guard) beat the parity forward and the
  futures on non-expiry days; the parity forward is a cleaner price level but does not lead the option premium. It
  works for member 08 because member 08's logic is different.
- On expiry days the options priced ≈ 3× the move that actually happened (realised/implied ≈ 0.31–0.33 median).

---

## 19. Known weaknesses and open questions for reviewers

### 19.1 Small sample, especially expiry days
Only **7 days**, of which **2 are expiry days**. The expiry half of the strategy (changes A and B, and member 08's
expiry parameters) is effectively fitted on 19 and 27 Oct. **27 Oct alone contributes +4.07 L** of the +8.47 L
through intraday compounding. The out-of-sample figure (+6.58 L) is optimistic for expiry days because each expiry
"fold" is chosen on the only other expiry day. A realistic expectation is closer to member 08's own out-of-sample
figure than to the headline.

### 19.2 Theta convention
The engine's `theta` per minute spreads a whole day's decay over 375 trading minutes, while time to expiry runs on
calendar seconds. Within a session, at constant IV, the model's premium decays at `theta_year / 525,600` per clock
minute, i.e. **3.84× less** than the engine's per-minute theta. Every "rent" ratio (change A's 0.25 threshold) is
therefore in the 375-minute convention; in calendar terms the threshold is ≈ 0.96. A Taylor check with calendar theta
fits the observed premium changes better (expiry residual +0.4 % vs +2.9 %). **Question:** which convention should
the rent gate use, and should the threshold be re-derived?

### 19.3 Path dependence (all-in, one position)
Because every trade is all-in and only one position is open at a time, any change that adds or removes one trade
shifts every later trade of that day. One study found member 08's big winners appear in only 7–40 % of nearby
parameter settings while its losers recur in 50–100 %. The result depends on the exact sequence of trades.
**Question:** how much of the edge is the rule, and how much is the path?

### 19.4 Member 08's fragile core parameters
The expiry window `W = 600 s`, lookback `L = 150 s`, `vmin = 20` and the normal lookback `L = 1,200 s` are peaks:
typical neighbouring settings make much less (expiry median +43k vs +2.13 L). An autopsy member re-expressed the
thresholds in market units (the move the options price in, and realised volatility) and tested several lookbacks
at once. That flattened the surface (93–94 % of settings profitable) at +5.03 L, 7/7 green, but it is not included:
it needs a rewrite to compute its scales online before the engine can run it.

### 19.5 Kit vs engine differences
- The kit's forward comes from the recorded per-second frame. The engine computes its own live parity forward;
  timing and strikes can differ slightly. In an early engine test on 19 Oct the first trade was the same move,
  28 s earlier and one strike apart (09:25:33 PE 23150 vs 09:26:01 PE 23100).
- The engine fills paper trades at the last traded price; the kit at the ask (2 s later) and the bid (2 s later).
  Both are scored at real fills (ask in, bid out).
- The engine evaluates once per second from a 10 Hz loop; the kit once per second on the tape.
- **The engine replay of all 7 days is the deciding test** and is running now.

### 19.6 Specific questions
1. Is the 15-minute expiry time clock (900 s) right, given that winners peak a median 7 minutes after entry?
2. Should change A apply on normal days too? On the taped days it never fired there (rent was always > 0.5).
3. Should change B apply on normal days? On the taped days it changed only expiry trades.
4. Is buying the breakout itself on expiry days (vs waiting for a pullback, as on normal days) the right structure,
   given that losers were bought mid-spike?
5. 10–11 big expiry moves happened after the 14:40 cutoff, several of +90–154 %, but moving the cutoff to 14:50 lost
   money. Is there a safe way to trade the last hour of expiry day?
6. Are there look-ahead or survivorship risks in the method (section 18.1) that we have not seen?

---

## 20. Glossary

| Term | Meaning |
|---|---|
| Put-call-parity forward (F) | the forward Nifty level implied by the option prices: F = K + C − P at a strike K |
| ATM / ITM | at the money / in the money; ITM CE has strike below F, ITM PE above |
| Delta | change in option premium per 1-point move in F |
| Gamma | change in delta per 1-point move in F |
| Theta | change in premium per minute from time passing (negative for a buyer) |
| Vega | change in premium per 1 volatility point |
| Rent ratio | 0.5 × gamma × realised squared move ÷ |theta|: does the market's movement pay the time decay? |
| Real fills | buy at the ask, sell at the bid |
| LODO | leave-one-day-out: choose on the other days, score on the held-out day |
| MFE / MAE | best / worst price reached during a trade |
| All-in | every trade uses all of the day's current capital |
