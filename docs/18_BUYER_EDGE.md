# 18 — Buyer edge (Tue 27 Oct 2026): why the system loses, what the research files add, what changed

Scope: the six live paper sessions since 19 Oct (19, 21, 22, 23, 26, 27 Oct; 106 trades), the raw tick files of the
same six days, and the three research files the owner supplied (`advanced.docx`, `advanced_chatgpt.txt`,
`advanced_deepseek.txt`). Every claim below was measured on that data; scripts are described in §6.

## 1. What happened live (FACT)

| Day | Champion | Trades | Win % | P&L (₹1 L start) |
|---|---|---|---|---|
| 19 Oct (expiry) | m2.0_s0.5 (domino) | 20 | 20 % | −51,854 |
| 21 Oct | spot_dc12_t12 (breakout) | 53 | 38 % | −22,562 |
| 22 Oct | spot_dual (pullback) | 7 | 29 % | −52,084 |
| 23 Oct | spot_dual_lvl | 5 | 80 % | **+1,78,682** |
| 26 Oct | spot_dual_lvl | 3 | 33 % | −21,398 |
| 27 Oct (expiry) | spot_dual_lvl (retest) | 18 | 39 % | −19,234 |
| **Total** | | **106** | 35 % | **+11,551** — five of six days red; one day carries everything |

## 2. Root causes, in order of size

1. **The entries have no directional edge.** Summed over all 106 trades, the option's mid price moved **+3 points**
   from entry to exit. The trades were coin flips; the account lost the friction and the asymmetry below.
2. **The exits sit inside the option's own noise.** The median ±30-minute excursion of the bought option was +12.9 % /
   −13.2 % of premium. A 12-point *spot* trail is ~4–6 % of premium: it cut winners at +5–7 % and let losers run to the
   trail. Same 104 entries, held under a plain −10 % / +20 % / 30-min premium bracket: **+1.5 %/trade instead of −0.6 %**.
3. **The options were bought when they were dear.** On 27 Oct every entry paid ATM IV 28–36 % while Nifty was
   realising 8–12 %; the profitable 23 Oct had IV ≈ realised. In options-pricing terms (advanced.docx §2,
   Θ ≈ −½σ²S²Γ): *theta is the rent paid for gamma*. When Nifty's actual movement does not cover the rent, a bought
   option bleeds even when the direction is right.
4. **Champion hopping (overfitting).** Four champions in six sessions, each picked on 1–3 days of in-sample replay
   (19 Oct replay +₹1.36 L, +₹1.31 L, +₹78 k …), each lost on its first unseen day. Every rule tuned to yesterday.
5. **No daily stop.** All-in on every trade is the owner's rule and stays; without a proven edge, noise can make −50 % days (19 and 22 Oct).
6. The current spot books return **before** the regime gate (`base_gate`), so 21 COMPRESSION-regime entries
   (10 % win) and 13 WARMING entries were taken. Not changed here (see §5): the new gate covers the same ground on
   evidence rather than labels.

## 3. Each research idea, tested on the six days

Per-second data (futures book, spot, every option strike) was rebuilt from the ticks: ~130,000 seconds. Directional
signals were scored by their correlation with the *next* 1–15 minutes, day by day (non-overlapping samples).

| Idea (source) | Result on 6 days | Verdict |
|---|---|---|
| Order-flow imbalance, Cont OFI (ChatGPT #1) | r ≈ +0.01…+0.10, sign flips by day (4/6) | **No edge — not used** |
| Book imbalance L1 / L5, micro-price (ChatGPT #1) | r ≈ 0, flips by day | **No edge — not used** |
| Put-call-parity synthetic forward (docx §1) | Predicts the **futures** (6/6 days, t = 8.6 at 1 min) but **not** the option premiums, the synthetic itself or spot (r ≈ 0). It is futures noise catching up with options already priced. | **No edge for a buyer — not used** |
| Bank Nifty / cross-market lead-lag (ChatGPT #7) | r ≈ 0, flips by day | **No edge — not used** |
| Momentum vs mean reversion (1–15 min) | r ≈ 0 | **No edge — not used** |
| Total book buy/sell quantity | contrarian, 5/6 days, t ≈ −2.8 at 15 min | Weak hint; **watch item only** |
| Theta-vs-gamma / IV-vs-RV (docx §2 & §4, DeepSeek vol-arb, ChatGPT #3) | Straddle P&L over next 10 min: +0.7 % when gamma pays ≥ 1× the theta rent, −0.1 % below. Real entries: ratio ≥ 0.5 → +3.5 %/trade under the bracket (69 trades, 5/6 days green, worst leave-one-day-out +3.0 %); ratio < 0.5 → losing | **ADOPTED: `gt_min` gate** |
| Premium-response / target-before-stop (ChatGPT #10, §5) | Premium bracket beats every spot-based exit on the same entries | Adopted first; **dropped after the engine replay (§6)**: it caps trend days. Shadow only |
| Risk-first allocation (DeepSeek portfolio construction) | Would reduce the stake per trade | **IGNORED: owner's rule is all-in on every trade, no position sizing** |
| No-trade filter (ChatGPT build order #4) | The gate *is* the no-trade filter: it skips decay-dominated conditions (most 0DTE afternoons) | **ADOPTED (via the gate)** |
| Online evaluation by regime (ChatGPT #9) | Already in the learning loop | **Kept; plus a freeze rule** |
| GEX / dealer gamma (docx §5), OI positioning (ChatGPT #2), dynamic levels (ChatGPT #4) | Already computed (gex.py, pressure, daystate); dealer sign unverifiable on Nifty | **Kept as evidence, not gates** |

### Ideas deliberately IGNORED, and why

| Idea | Why not |
|---|---|
| Risk reversals, iron condors, premium selling, short straddles, conversions/reversals, box spreads, calendars/diagonals, dispersion, 0DTE condors, "9:20 straddle" | All require **selling** options. The owner's hard rule is buy-only. |
| Gamma scalping (long straddle + futures hedging) | Needs continuous futures trading; and the straddle study shows long gamma is roughly break-even here. |
| Heston / SABR / jump-diffusion, Monte Carlo, trees | Pricing precision for exotic or American options; irrelevant to 5–30 min holds of liquid European ATM options (Black-76 is already used). |
| Third-order Greeks (speed, zomma, color), vomma | Negligible for ATM options held under 30 minutes. |
| Vanna / charm dealer flows (VEX, CHEX) | Need the dealer's sign; on Nifty retail buys and props write, so the sign is unknown and cannot be checked from our data. |
| Reinforcement learning, multi-agent ML ("85 % success" claims) | ~100 trades in 6 days; any ML would memorise them. Claims are not about Nifty and not out-of-sample. Revisit after 60+ sessions. |
| Bayesian signal fusion | Needs several *independent, calibrated* signals; none of the directional signals showed an edge, so there is nothing to fuse yet. |
| Event-conditioned pattern discovery | Six days of history; the pattern count would exceed the events. |
| Expiry pinning | A seller's edge; for a buyer the gate already avoids theta-dominated expiry afternoons. |
| Speed / execution latency | Breeze allows 100 REST calls/min and no market orders; there is no latency edge to win at retail. |

## 4. What changed in the code

* `apex/engine/edge.py`: `v_min30`, spot's realised variance per minute over 30 min (`var_per_min`).
* `apex/engine_main.py`: option rows carry `gamma` and `theta_min`; a book with `gt_min` checks the gate after the
  contract is chosen; a skipped setup is dropped, not queued.
* `apex/engine/paper.py`: `buyer_edge_gate` (ratio = ½·Γ·v_min30 / |Θ_min| ≥ `gt_min`); `max_hold_s` exit for every
  book except `fade_switch`, which keeps its own clock; per-book `day_stop_pct`. Every book sizes all-in (owner's rule; the brief 50 % sizing was removed).
* `apex/config.py`: champion **`edge_gate_only`** = `spot_dual_lvl` (its entries, exits, level booking and all-in
  sizing) + the buyer-edge gate at 0.5. Chosen on the full engine replay in §6, which overturned the first pick.
  Shadows: `apex_edge` (gate + bracket −10/+20/30 min + −20 % day stop), `edge_bracket_only`,
  `edge_breakout` (the 12-min breakout/retest entries + gate + bracket). `spot_dual_lvl` keeps running as a shadow,
  so the learning report compares the gate against no gate every evening.
* Tests: `tests/test_c11_buyer_edge.py` (9). Tests that pinned the old champion's name or the variant count were
  updated.

To restore the old champion: `CHAMPION_DEFAULT` and `CHAMPION_OWNER` = `spot_dual_lvl` (bump the date).

## 5. Honest limits, and the rule from here

* Everything above is **in-sample on six days**. The gate and bracket were chosen from options theory first and
  checked leave-one-day-out, which is far stronger than the previous one-day replays — but it is still a hypothesis.
* Even the "perfect direction" leg gains only +13 % in 10 minutes on average. Without a directional edge, the best a
  buyer can do is stop paying for expensive gamma and stop cutting trades inside the noise. That is what this change
  does; it does not create a directional edge, and none of the tested ideas showed one.
* **Freeze rule:** do not swap or re-tune `edge_gate_only` for 15 sessions or until the SPRT decides. Changing the
  champion after every losing day is the single most expensive habit in this project's history.

## 6. Engine replay of all six days (lock-step, honest fills)

Full engine, every book, the recorded ticks of each day, fills on the first print after the trigger. P&L in ₹ on
₹1 L fresh each day (trades in brackets).

| Book | 19 Oct | 21 Oct | 22 Oct | 23 Oct | 26 Oct | 27 Oct | Total | Trades | Win % | Mean / trade | Green days |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **edge_gate_only (champion)** | +36,065 (3) | +69,774 (5) | −8,236 (4) | +1,66,254 (5) | −20,449 (3) | +6,581 (1) | **+2,49,990** | 21 | 76 % | **+10.5 %** | 4/6 |
| spot_dual_lvl (old champion) | +1,36,594 (18) | +69,774 (5) | −8,236 (4) | +1,66,254 (5) | −20,449 (3) | +3,630 (20) | +3,47,568 | 55 | 56 % | +5.5 % | 4/6 |
| apex_edge (gate + bracket; replayed at ½ capital) | +13,458 (3) | −1,580 (6) | +8,297 (4) | +23,231 (7) | −6,692 (4) | +9,555 (1) | +46,270 | 25 | 52 % | +4.1 % | 4/6 |
| edge_bracket_only | −10,839 (17) | −7,439 (6) | +16,858 (4) | +50,359 (7) | −445 (8) | +7,816 (19) | +56,310 | 61 | 41 % | +1.8 % | 3/6 |
| spot_dc12_t12 | +1,31,193 (17) | −1,882 (22) | −24,518 (27) | +41,548 (20) | +21,892 (22) | +3,630 (20) | +1,71,863 | 128 | 38 % | +1.3 % | 4/6 |
| edge_breakout | +13,458 (3) | +4,284 (9) | −23,056 (6) | −14,557 (13) | +10,562 (10) | +9,555 (1) | +247 | 42 | 36 % | +0.2 % | 4/6 |
| random_entry (control) | −23,364 (6) | −5,684 (6) | −289 (6) | −2,369 (5) | −18,792 (6) | −43,137 (7) | −93,636 | 36 | 28 % | −2.7 % | 0/6 |

What this says, plainly:

* **The bracket was wrong.** On the real engine, `spot_dual_lvl`'s level booking lets a 23 Oct-type trend pay
  (+₹1.66 L); a +20 % premium target caps it (`edge_bracket_only` +₹50 k that day). The earlier study (§3) re-ran
  *other* champions' live entries, whose spot-trail exits were worse than both; against level booking the bracket
  loses. Not adopted; kept as a shadow.
* **The gate keeps its promise where it matters.** On dear 27 Oct (IV ≈ 3× realised) it took 1 trade instead of 20
  (live, the old champion lost ₹19 k that day). On 21, 22, 23 and 26 Oct it changed nothing. Per trade it doubles the
  mean return (+10.5 % vs +5.5 %) with 76 % winners.
* **What it cost:** on 19 Oct it skipped 15 trades worth ~₹1 L. 19, 21 and 22 Oct are the days `spot_dual_lvl` was
  chosen on (in-sample for it); on the three days after its choice (23, 26, 27 Oct, unseen for it) the gate is
  +₹1,52,386 vs +₹1,49,435 without. The gate is therefore **not proven** to add money; it is proven to cut trades
  that the theory says are rent-dominated, at similar profit. That is the trade-off chosen.
* Replay vs live for `spot_dual_lvl` on its unseen days: 23 Oct +₹1.66 L vs +₹1.79 L live, 26 Oct −₹20 k vs −₹21 k,
  27 Oct +₹4 k vs −₹19 k. The replay is close to live, not identical.
* Every book with a premise beats `random_entry` (−₹94 k, 0 green days): the entries carry *some* information;
  the 19–22 Oct live losses came from books that are no longer the champion.

## 6b. Trail, strike levels, re-entry — champion `lvl_trail_re` (27 Oct night – 28 Oct)

The owner, after §6: the days were profitable but the books "hold too long" and "give away too much from the peak";
the entry gate is not worth keeping ("entries should have an edge over everybody"); do not hold long on expiry day;
after a hard trail out, re-enter only cheaper (or the next OTM strike, about to become ATM, when it is cheaper), and
within 10 minutes only on a stronger trigger ("if you re-enter in the same direction and it was not a stronger
trigger than before, you may end up losing more often").

**What was built (all in `paper.py` unless named):**

* **Hard premium stop −10 %** (`prem_hard_stop`). The impulse-origin stop had let losers run to −27 %.
* **Gain trail on the 30-s average premium** (`gt_arm_pct` 20, `gt_keep` 0.8, `gt_smooth_s` 30): once the average
  is +20 %, out when it falls to 80 % of its best gain. On raw prints the same trail fired on one-second noise and
  cut the +70 % runners; on the average it does not.
* **Expiry day: hold at most 10 min** (`dte0_max_hold_s` 600). Recorded prices: expiry trades hold a median 2.3 min;
  10 min added ₹5 k over the two expiries, 5 min lost ₹24 k.
* **Re-entry rules** (`reentry_check`). After a TRAIL / LOCK exit, a same-direction setup within 30 min must be
  cheaper than the exit (else the next OTM strike if that is cheaper, else skipped); within 10 min it must also have
  a stronger trigger (a bigger impulse for a pullback, a longer run beyond the level for a retest). After a STOP the
  stronger-trigger rule applies for 10 min (`reentry_stop`), with no price rule. The other direction is never limited.
* **Each strike's own support / resistance** (`strike_levels.py`): day high/low, 09:15–09:30 range, 1-min swing
  pivots, yesterday's high/low/close per contract; a break is 1 % beyond a level ≥ 5 min old. Taped to
  `paper/strikes_<day>.jsonl`; trades carry `sr_in` and `sr_breaks`. **Evidence only**: a premium breaking its day
  low fell a further −4.5 % in 10 min on 6/6 days, but used as a stop it lost to the plain −10 % stop.

**Engine replay, six days (batch 20261027-221837), ₹ on ₹1 L all-in each day:**

| Book | 19 Oct | 21 Oct | 22 Oct | 23 Oct | 26 Oct | 27 Oct | Total | Green days |
|---|---|---|---|---|---|---|---|---|
| **lvl_trail_re (champion)** | +1,31,670 | +82,332 | +15,568 | +1,13,366 | +2,194 | +41,473 | **+3,86,604** | **6/6** |
| lvl_trail_rx_c10 (rule after any exit, cheaper 10 min) | +1,37,787 | +75,926 | +15,568 | +1,13,366 | +2,194 | +41,473 | +3,86,314 | 6/6 |
| lvl_trail (trail, no re-entry rules) | +1,36,594 | +89,261 | +15,568 | +1,13,366 | −8,060 | +23,770 | +3,70,500 | 5/6 |
| lvl_trail_rx (stronger rule after any exit) | +1,20,549 | +75,926 | +15,568 | +1,13,366 | +2,194 | +41,473 | +3,69,076 | 6/6 |
| spot_dual_lvl (no trail) | +1,36,594 | +69,774 | −8,236 | +1,66,254 | −20,449 | +3,630 | +3,47,568 | 4/6 |
| lvl_trail_rx_be (+ breakeven guard) | +1,20,549 | −18,353 | +15,568 | +1,13,366 | +43,157 | +41,473 | +3,15,760 | 5/6 |
| lvl_trail_be | +1,36,594 | −15,688 | +15,568 | +1,13,366 | +29,708 | +23,770 | +3,03,319 | 5/6 |
| edge_gate_trail (gate + trail) | +36,065 | +89,261 | +15,568 | +1,13,366 | −19,484 | +6,581 | +2,41,358 | 5/6 |
| random_entry (control) | −23,364 | −5,684 | −289 | −2,369 | −18,792 | −43,137 | −93,636 | 0/6 |

* **The entry gate goes.** It changed only the two expiry days and cost ₹1 L of winners on 19 Oct.
* **The trail pays** on 21, 22 and 27 Oct; it gives back ₹53 k on 23 Oct, where the −10 % stop (not the trail)
  closed the 11:11 trade that later recovered.
* **The re-entry rules blocked 4 trades: 3 losers** (26 Oct 12:41 −9.7 %, 27 Oct 13:30 −10.5 %, 27 Oct 11:12
  −0.4 %) and one small winner (21 Oct 13:57 +3.9 %). They turned 26 Oct green and nearly doubled 27 Oct.
* **Stronger rule after any exit:** after profit bookings it blocked two winners (19 Oct 09:29 +6.6 %, 21 Oct
  13:19 +7.6 %): −₹17 k. Kept for stops only, where on these days it blocked nothing (the one re-entry after a stop
  had the stronger trigger and made +28 %).
* **Breakeven guard rejected:** +₹41 k on 26 Oct, but it closed 21 Oct's +69 % runner at breakeven (−₹1 L that day).
* **Opening-range wait rejected without a replay:** of six entries before 09:30, only 26 Oct's lost (−₹9 k); the
  other five made ~₹42 k.

**Limits.** All six days are in-sample: every rule here was written after seeing them. The re-entry evidence is four
blocked trades. The champion is frozen from 28 Oct; new paper days are the test.

## 7. How the numbers were produced

Scratch scripts (not part of the system): rebuild a per-second frame from `data/ticks/*.jsonl.gz` with the
system's own parser (`feed_replay.iter_records`, `apply_packet`); compute the features with the same definitions
as `edge.py`; score correlations day by day; replay every live entry over the recorded option mids under alternative
exits; then the full engine replay (`python run_apex.py replay <day> --fast --no-browser`) for §6.
