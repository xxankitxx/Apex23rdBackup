# ApexOptions — proposed strategy "c20_9x": complete specification after the four AI reviews

*29 October 2026, night. Supersedes `19_C20_8X_STRATEGY_SPEC.md` as the proposal. Prepared for independent review.*

**Status.** Proposal only. The owner's live system still trades the champion `t28_gap`, unchanged. `c20_9x` exists only
in the research kit (`scratchpad/team/R9_30/strategy.py`, parts `FINAL_R9`). It has not yet been run in the engine.
**Engine replay of the previous proposal (`c20_8x`) — finished 29 Oct, 20:00, real fills (ask in, bid out), Rs 1 L
all-in per day:**

| Book | 19 | 21 | 22 | 23 | 26 | 27 | 28 | 7-day total | **29 Oct (untouched test day)** |
|---|---|---|---|---|---|---|---|---|---|
| `c20_8x` | +91,067 | +41,274 | +4,194 | +24,458 | +1,60,302 | +4,03,413 | +54,666 | **+7,79,375** (7/7 green) | **+31,646** (4 trades) |
| `c20_08` (member 08) | +34,444 | +36,246 | −15,705 | +22,150 | +1,60,022 | +1,86,689 | +35,324 | +4,59,171 | +26,382 |
| `t28_gap` (champion) | +1,24,144 | +83,255 | +16,000 | +1,40,921 | −2,753 | +35,264 | −24,201 | +3,72,630 | +4,033 |

The engine came in about 8 % below the kit for `c20_8x` (+7.79 L vs +8.47 L, consistent with its fill-timing
sensitivity, section 8) and it **won the untouched day**: on 29 Oct it bought the morning CE rally at 09:43 and held it
to 10:57 for +40.8 % — the rally the champion sat out. `c20_9x` must now pass the same 8-day engine replay before the
owner decides.

**What changed since document 19.** Four AI reviews (Gemini, ChatGPT, DeepSeek, Grok) were read in full. Their cost,
brokerage and fee suggestions were set aside on the owner's instruction (the bid–ask spread is not a fee and stays in
every result). A 30-member team tested every other review item against `c20_8x` on the same 7 taped days, each with a
per-day table, leave-one-day-out (LODO), one-notch robustness and a trade-by-trade diff. An evaluator stress-tested
the survivors against fill-path perturbations, and an integrator built and tested the final combination.

**Result in one line.** `c20_9x` = `c20_8x` + 4 correctness fixes + 5 improvements. Kit: **+Rs 11,46,018 over 7 days
vs +Rs 8,46,648** for `c20_8x`, every day green, better or equal on every single day, and better under all 17 path
perturbations. Honest out-of-sample estimate: about **+1.6 L** better, not +3.0 L (section 9).

---

## 1. Owner's fixed rules (unchanged)

Buy-only NIFTY weekly options; Rs 1,00,000 fresh each day, profits compound within the day only; **all-in on every
trade** (lots = floor(capital ÷ (premium × 65))); |delta| ≥ 0.52 at entry (ATM/ITM only); expiring weekly on expiry
day; one position at a time; paper only. Nothing in `c20_9x` changes any of these.

---

## 2. The base it builds on

Everything in document 19 (sections 4–17) still applies unless changed below:
- the put-call-parity forward F, smoothed by a 5-s EMA (`fs`);
- **expiry mode**: breakout of the 10-min range of `fs` with ≥ 20 pts in 150 s, buy |delta| ≈ 0.65;
- **normal mode**: 40-pt impulse in 20 min → 50–75 % pullback within 15 min of arming → 5-pt resumption, buy
  |delta| ≈ 0.52;
- exits: −15 % premium stop, forward trail 25 pts (expiry) / 40 pts (normal), clock 15 min (expiry) / 90 min (normal),
  break-even lock after +15 %, give-back cap (keep 70 %) after +60 %, forced flat 15:00 / 15:20;
- the flip-after-loss gate ("seq"), 60-s cooldown, entry windows 09:16–14:40 (expiry) / 09:16–15:00 (normal).

---

## 3. The four correctness fixes (no P&L change on the 7 days; kept because they are right)

| Fix | Review source | What it does | Effect on 7 days |
|---|---|---|---|
| **Two-layer loop** ("l2") | ChatGPT P0 | Exits never wait for the forward. Every held second the premium stop and the time clock are checked even if the forward is missing. If the forward has been unchanged or missing for ≥ 5 s ("stale"), the forward trail is replaced by a premium trail: from the moment it went stale, exit if the bid falls by |delta| × (remaining trail points) from its best since then. No new entry while the forward is stale. | identical trades |
| **Floors first** ("ffirst") | ChatGPT P0 | When an armed premium floor (break-even, ramp or give-back) and another exit fire in the same second, the floor is the reason recorded (the −15 % stop keeps priority). | identical trades, labels only |
| **Calendar-time rent** ("seqcal") | all four reviews | The flip-after-loss gate's "rent" uses calendar-minute theta (θ_cal = engine θ × 375/1440). In that form rent = realised variance ÷ implied variance exactly. Threshold 1.2 (the old 0.25 in engine-theta units = 0.96 calendar; 1.2 sits in the middle of a flat range 0.88–1.5 instead of next to a cliff at 0.85). | identical trades |
| **EMA catch-up** ("catch") | Gemini Hole 7 | The test kit skipped the smoothed forward's update during the 2-s order delay and restarted it at the raw forward (98 small steps). The fix rolls the EMA through those seconds, as the engine already does. | +Rs 1,027 |

Also confirmed but not changed: the expiry trigger is never a stale "state" in practice (0 of 28 entries; Gemini/
ChatGPT P1), and running the pullback state machine while holding only adds losing same-side re-entries (Gemini
Hole 6).

---

## 4. The five improvements

### 4.1 Normal days — delta-scaled forward trail ("dtr"; Gemini add-on 5b, team member 20)

Every second while holding on a normal day:
```
trail_now = 40 pts × clip( |delta at entry| / |delta now| , 0.8 , 1.0 )
```
The trail tightens from 40 pts towards 32 pts as the option goes in the money (a forward point is worth more premium
there); it never widens. Entries are unchanged. Result: positive on all 5 normal days (+4.4k, +6.1k, +7.1k, +7.5k,
+1.9k); the +50 % runners improve (23 Oct +82 % → +91 %, 26 Oct +86 % → +90 %); LODO 5/5 held-out days positive;
floor 0.5–0.9 is a plateau; positive at fill lags 1, 2 and 3 s. The most rule-like part of the proposal.

### 4.2 Normal days — continuous profit floor ("ramp"; Gemini add-on 5a, team member 19)

Replaces the step (+15 % → break-even, +60 % → keep 70 %) on **normal days only** with a ramp. With g = peak gain
(peak bid ÷ entry − 1):

| Peak gain g | Floor (exit if bid ≤ floor) |
|---|---|
| below +15 % | none |
| +15 % to +25 % | entry price (break-even) |
| +25 % to +50 % | entry × (1 + g × k), k rising linearly from 0.45 at +25 % to 0.70 at +50 % (never below entry) |
| +50 % and above | entry × (1 + 0.70 × g) |

Examples: peak +30 % → floor +15.0 % (k = 0.50); peak +40 % → floor +24.0 % (k = 0.60); peak +50 % → floor +35 %. Expiry days keep the
original step (Gemini's ramp on expiry days cut the runners: −2.34 L). Result: +45.1k on 26 Oct and +1.8k on 22 Oct,
0 elsewhere (it converts three 26 Oct trades that peaked at +29 % to +40 % and were trailed out at +10 % to +16 % into
+18 % to +22 % exits). LODO +42–47k. All one-notch neighbours positive. Main weakness: one day.

### 4.3 Expiry days — IV-shock veto ("ivz"; Gemini add-on 3 / DeepSeek / Grok D, members 13, 16, 27)

Before buying on an expiry day:
```
a(i)   = mean of CE and PE implied volatility (vol points) at the strike nearest the forward, averaged over the last 30 s
d(i)   = a(i) − a(i − 300 s)                       (the 5-minute IV change)
s(i)   = RMS of d over the day so far (from 09:25 onward), needs ≥ 600 seconds of history
VETO the entry if  d(i) / s(i) > 1.5
```
i.e. do not buy a breakout that comes with an unusually fast IV rise for that day — a volatility shock, which tends
to be crushed back. Three team members found this signal independently; this z-score form is the flattest (no
negative neighbour in 84 settings), unlike the fixed-threshold form (+1.24 L but cliffs of −36k / −99k). Result:
removes one losing trade (27 Oct 13:30 PE, −13.9 %), and the saved capital compounds into that day's 14:36 runner:
+93.5k inside the final combination. It never fires on 19 Oct, so it has no true out-of-sample test; at a 360-s window
it stops firing (still better than `c20_8x` overall).

### 4.4 Expiry days — premium give-back trail after +70 % ("ptre"; ChatGPT add-on 10, member 23)

Once the held option's bid has peaked at least **+70 % above entry**, the forward trail is switched off and replaced by:
```
exit when bid ≤ peak bid × (1 − 0.08)
```
(the raw bid; the −15 % stop, the clock and the premium floors are unchanged and checked first). Expiry days only — on
normal days it costs −9k inside the stack. Result: +47.5k on 19 Oct (09:26 PE +50 % → +60 %, 09:52 PE +44 % → +64 %)
and +37.9k on 27 Oct (12:31 CE +58 % → +69 %); no runner is cut. **The only expiry part confirmed out of sample in both
directions.** Neighbours: arm +60 % / +80 % → +1.74 L / +1.81 L for the whole combination; give-back 6 % / 10 % →
+3.35 L / +2.26 L. Weakness: one bad bid tick after +70 % can exit early.

### 4.5 Expiry days — strike tie-breaker ("tie"; Grok E / DeepSeek, member 24)

Among the eligible strikes (ATM ± 3 strikes, ask > 0, quote ≤ 5 s old, |delta| ≥ 0.52) on an expiry day, choose the
highest
```
score = 100 × ( |Δ|·m + ½·Γ·m² − |θ_cal|·h ) / ask  −  5 × 100 × | |Δ| − 0.65 |
```
with m = |forward move over the last 150 s|, h = 7.5 min, θ_cal = engine θ × 0.26. The 0.65 delta target still
dominates; the score only breaks near-ties toward the cheaper contract. Result: one strike change (27 Oct 13:08 PE
22800 → 22750: +31.7 % → +42.4 %) → +51.7k through compounding. LAM 3–8 and θ scale 0.2–0.35 identical. Weakness: one
trade, no out-of-sample day.

---

## 5. Order of checks every second (c20_9x)

1. Roll the smoothed forward; mark the forward stale if unchanged/missing ≥ 5 s.
2. **If holding:**
   1. −15 % premium stop (always, even without a forward).
   2. Forward trail (expiry 25 pts; normal 40 pts × delta factor 0.8–1.0) — unless the expiry premium trail is armed
      (peak ≥ +70 %), or the forward is stale (then the premium form of the trail).
   3. Time clock (expiry 15 min, normal 90 min) — always.
   4. Premium floors: expiry — break-even after +15 %, keep 70 % after +60 %; normal — the ramp of 4.2.
   5. Expiry premium trail: bid ≤ peak bid × 0.92 once peak ≥ +70 %.
   6. Forced flat 15:00 (expiry) / 15:20 (normal).
3. **If flat:** cooldown 60 s; entry window; forward fresh; mode trigger (expiry breakout / normal
   impulse→pullback→resumption); contract (expiry: tie-breaker score; normal: |delta| nearest 0.52); expiry IV-shock
   veto; flip-after-loss gate (calendar rent ≥ 1.2 after a losing trade, other side, within 15 min); BUY all-in.

---

## 6. Parameters (new or changed vs document 19)

| Parameter | Value | Mode |
|---|---|---|
| Stale-forward threshold | 5 s | both |
| Flip-gate rent (calendar) | ≥ 1.2 | both (fires on expiry only in practice) |
| Delta-trail factor clip | 0.8 – 1.0 | normal |
| Ramp: arm / R0 / R1 / k0 / k1 | +15 % / +25 % / +50 % / 0.45 / 0.70 | normal |
| IV-shock: averaging / window / z / min history | 30 s / 300 s / 1.5 / 600 s | expiry |
| Premium trail: arm / give-back | +70 % / 8 % of peak bid | expiry |
| Tie-breaker: λ / θ scale / move window / horizon | 5 / 0.26 / 150 s / 7.5 min | expiry |

All other parameters are as in document 19, section 16.

---

## 7. Results (kit, real fills: buy at ask 2 s after the signal, sell at bid 2 s after)

| Day | c20_8x | **c20_9x** | Change |
|---|---|---|---|
| 19 Oct (expiry) | +1,28,495 | +1,77,041 | +48,546 |
| 21 Oct | +29,149 | +33,556 | +4,407 |
| 22 Oct | +20,933 | +30,794 | +9,861 |
| 23 Oct | +50,934 | +58,061 | +7,127 |
| 26 Oct | +1,57,697 | +2,15,426 | +57,729 |
| 27 Oct (expiry) | +4,06,741 | +5,76,583 | +1,69,842 |
| 28 Oct | +52,699 | +54,558 | +1,859 |
| **Total** | **+8,46,648** | **+11,46,018** | **+2,99,371 (+35 %)** |

48 trades (49 before). Big moves held: 34 / 112 (unchanged — the parts improve exits and remove one loser; they do not
catch new moves). Fill lag 1 / 3 / 5 s: +11.38 L / +11.25 L / +11.84 L vs `c20_8x` +7.63 L / +8.22 L / +7.97 L.

**Where the gain comes from (inside the final):** normal days (delta trail + ramp) +80,984; expiry days (IV-shock veto
+ premium trail + tie-breaker) +2,17,360, of which 27 Oct +1.70 L.

---

## 8. Robustness

- **Path perturbations** (12 random fill-timing seeds, start capital 0.8 L / 1.2 L, 5-s lag, ±30-s clock shift): beats
  `c20_8x` in 17 / 17; median gain +2.99 L, minimum +2.34 L; median total under random fill timing +10.84 L vs +7.92 L.
  Only 19 Oct was ever below `c20_8x`, once, by −3.2k.
- **One notch on every chosen part, inside the combination:** no notch goes below `c20_8x` (section 4 lists them).
- **Note:** `c20_8x` itself is path-sensitive: +8.47 L at the kit's 2-s fill lag, +7.63 L at 1 s (19 Oct alone falls
  from +1.28 L to +38k).

---

## 9. Out-of-sample (LODO) — the honest number

- **Normal days:** choosing {delta trail, ramp} on 4 normal days and scoring the 5th picks both every time: **+80,984**.
- **Expiry days** (only two: choose on one, score on the other): choosing on 27 Oct and scoring 19 Oct +48.5k;
  choosing on 19 Oct and scoring 27 Oct +32.6k. 19 Oct cannot see the IV-shock veto or the tie-breaker (neither does
  anything on 19 Oct), so **only the premium trail is confirmed out of sample in both directions.**
- **Honest LODO total ≈ +1.62 L**, against the in-sample +2.99 L. Plan on the lower figure.

---

## 10. Review items tested and rejected (with the team's numbers)

| Review item | Source | Result on 7 days |
|---|---|---|
| Spike/kinematics guard (acceleration, κ, SPIKE_VERIFY) | Gemini add-on 1, Grok B | −9.7k as written; acceleration does not separate 0-DTE winners from losers; every variant helped 19 Oct and hurt 27 Oct |
| v_hurdle (drift vs spread + theta hurdle) | Gemini add-on 2 | never fires as written (breakouts are 8–112× the hurdle); tightened version nearly vetoes the +2 L winner |
| Expected-premium-move / EV veto | ChatGPT 1–3, DeepSeek 3.1 | normal days −2.1 to −3.1 L (pullback entries have adverse short-term drift by design); expiry inert |
| Skew velocity veto | Gemini add-on 3a | never fires as written; no edge in any form |
| Multi-strike forward dispersion | Gemini add-on 3b | −71k as written; it is skew/quote noise, not order flow |
| Option order flow (NODI, OFI, microprice) as confirmation | Gemini add-on 4, ChatGPT 5–7 | −2.65 L (flow mirrors the past price move, corr 0.83); the contrarian form is fragile |
| Realised-vol / regime scaling of thresholds and trails | Grok F, DeepSeek | fails LODO; the two expiry days want opposite trails |
| Volatility-aware pullback (z-resumption, ATR impulse) | ChatGPT 9, DeepSeek 3.9, Grok G | every family negative in LODO (down to −1.53 L) |
| Structural impulse base | Gemini Hole 2 | loses the two biggest normal-day winners; LODO −2.2 L |
| Longer arm clocks / second pullback attempt | Gemini Hole 1, Grok G | −9k / −57k to −1.76 L |
| Loss definition excluding scratch exits | Gemini Hole 4 | −67.7k (one 27 Oct chain) |
| Rent gate on every expiry entry | DeepSeek 3.2, Gemini Hole 5 | big 27 Oct winners were entered at low rent; −1.09 to −4.25 L |
| Stagnation exit / rent-collapse stop | Gemini 19.6(1), DeepSeek 3.5 | cut 19 Oct runners (−59k to −1.05 L) |
| Hazard-model hold clocks; expiry clock 850 s | ChatGPT 11, DeepSeek 3.8 | hazard model worse out of sample; 850 s is a timestamp fluke (−42k at 880 s) |
| Expiry 14:40–15:05 late mode | Gemini 19.6(5) | 7 of 13 late moves start after the 14:50 last entry; 0 of 216 settings helped 27 Oct |
| Kalman / adaptive EMA forward, CUSUM | DeepSeek 3.8 | the forward has momentum, not noise (Kalman gain ≈ 1); the 5-s EMA is a useful debounce; all variants lose |
| Contract scoring beyond the tie-break; deeper ITM on big mornings | Grok E, DeepSeek 3.3 | strike is a leverage dial; −20k to −345k |
| Quote-quality / spread filters | Grok B, DeepSeek | no effect: all 49 entries had clean, fresh quotes (kept as a live safety check) |
| Market-unit (realised-vol) normal-day core | Grok/ChatGPT via member A8_09 | flatter surface, +56.7k, but loses on 26 and 28 Oct inside the combination; LODO below the chosen stack |
| Fees, brokerage, STT, cost models | DeepSeek, Gemini | excluded by the owner |

---

## 11. Known weaknesses and open questions

1. **Concentration.** 73 % of the gain is on the two expiry days; 27 Oct alone is +1.70 L. Two of the five improvements
   (IV-shock veto, tie-breaker) each rest on one trade with no out-of-sample day.
2. **Inherited cliffs in `c20_8x`, untouched:** the flip-gate window (900 s; 600 s → 7.17 L, 1200 s → 6.49 L in the old
   form), the expiry 15-min clock (750 s → −94k, 950 s → −220k), and the normal-day lookback (member 08's L = 1200 s is
   a peak; a market-unit version is flatter but was not chosen).
3. **Seven days.** Every number here is fitted on 19, 21, 22, 23, 26, 27 and 28 Oct. 29 Oct is the untouched test
   day; more expiry days are needed before the expiry parts can be trusted.
4. **Forward freezes.** On 23 Oct the parity forward froze for 45 minutes while option quotes were live and then
   jumped 90 pts. The stale-forward fix blocks entries and protects exits during a freeze; a futures-based fallback
   after ~30 s of freeze was suggested but not proven profitable.
5. **Engine port notes.** The IV-shock veto must be computed incrementally in the engine (the kit precomputes the
   day's IV series; every value uses only earlier data, so the kit result is valid). The EMA catch-up fix is a no-op in
   the engine, which already updates every second. The engine's own theta convention (θ per minute = day decay / 375)
   is unchanged; the strategy converts it where needed.
6. **Questions for reviewers:** Is the expiry premium trail (8 % off peak after +70 %) at risk from single bad bid
   ticks in live data? Should the IV-shock veto use a longer or shorter window given that it stops firing at 360 s? Is
   the normal-day ramp over-fitted to 26 Oct?

---

## 12. Files (research copy)

- `scratchpad/team/R9_30/strategy.py` — the final class (`FINAL_R9`), every part a switch; all off = `c20_8x`.
- `scratchpad/team/R9_30/results.json` — per-day results, factorial, notches, perturbations, trades.
- `scratchpad/team/R9_01 … R9_29/` — each member's code, results and grids.
- `docs/19_C20_8X_STRATEGY_SPEC.md` — the base specification this document extends.
