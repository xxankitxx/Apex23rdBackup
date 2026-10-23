# 10 — Council 4: why 19 Oct lost ₹51,854, and what would have made it money without fooling ourselves

The team leader's consolidated report of 30 member reports (`/tmp/claude-0/c4/m01.md` … `m30.md`; m30 includes an addendum
red-teaming m14 `fade_switch` and m28 `R2`). Code state: HEAD `3f11460` (D-109 … D-116 committed; D-110 … D-115 coded, not yet replayed).
Data: the 1-Hz pack of the whole 19-Oct session (161 instruments, built from the full tick tape with the fixed parser), the live books
and tapes. Every number below was scored under the harness rules unless a member says otherwise: ask in / bid out, fill at i+1,
all-in compounding, ₹1,00,000 fresh in each window, entries 09:25–14:45, flat 15:00. FULL = 09:25–14:45, AM = 09:25–12:30,
PM = 12:30–14:45. Member ids are in brackets.

---

## 1. The answer in six lines

1. **It lost because its entries were worse than random.** Against a random-entry null with matched holds, the champion's day sits at the **1st percentile** (p ≈ 0.01; [m21]). In the PM it bought 1–10-pt wiggles of the **27-Oct future**. Those wiggles were mostly basis noise against the **spot** price the 19-Oct weekly settles on: spot never moved ≥ 15 pts in 15 s after 12:30, while the future did so 16 times [m20]. It bought 9 of 9 calls into a 100-pt fall and flipped side on every wiggle (13 flips ≈ −₹38k of the −₹52k) [m12, m16]. Spread, theta and fills explain only about 10 % of the loss [m09, m10, m13].
2. **Nothing stopped it.** The regime classifier said no to 18 of 20 entries but was only advisory. There was no daily brake. Four code versions were hot-swapped into the same book during the session; the worst segment (D-108, 13:11–13:45) made 167 trades across the books at −2.76 % each [m27].
3. **What would have prevented it:** an acceptance replay on recorded tape plus a random-entry null before go-live, hard gates (regime plus the point floor), a brake that stops the book for the day, and no code changes during market hours. HEAD (D-109 … D-115) already turns today's −52 % into **one trade at −11 %** [m29]. That avoids the loss. It does not make money.
4. **Making today profitable:** almost every "₹1.6–3.7 lakh" headline is two trades between 09:25 and 09:35 [m30]. Only one rule survives removing that crash, dropping its best 3 trades, ±20 % on every number, 5 s of latency and 1 pt of slippage per side: **Nifty SPOT breaks its previous 12-min range → buy that way; exit on a 12-pt spot trail** (R2) [m28, m30]. It makes ₹2.32 L FULL, still ₹1.79 L if trading starts at 09:35, and beats 96–99 % of random nulls in the AM. Its PM (₹1.13 L) is **not** proven: 4 of 9 neighbouring settings lose.
5. **It is not proven, and today cannot prove it.** The council tried about 12,000 variants. After that much searching, no single-day result is statistically significant [m21]. R2 now runs as two **pre-registered books** (D-116). It is not the champion.
6. **The honest answer to "make it profitable on today's data":** that is easy, and that is the trap. 76 of m21's 430 variants are profitable on the day. The correct result for today's afternoon was **zero trades**.

---

## 2. What should have been done

### Design

| What should have been done | Said by |
|---|---|
| **Measure the signal on what the option is priced on.** On expiry day the weekly settles on spot. The 27-Oct future ran +8 → +37 pts above it and its 15-s basis noise (sd 3.3–5.8 pts) was the same size as the "impulses" traded. Fidelity R² for explaining option moves: future 0.45, spot 0.66, parity synthetic 0.94. | m09, m10, m13, m19, m20, m26, m28 |
| **Size the trigger in points sized to the trade's cost, not only in z.** σ15 fell from 8 to 2.5 pts, so z = 2 meant a 5-pt wiggle by lunch. Impulses under ~10–12 pts had no follow-through anywhere today; ≥ 15 pts continued in the AM (+13.8 pts at 120 s). | m03, m08, m14, m23 |
| **Gates must be gates.** The regime classifier was right more often than the trigger, but it was advisory. On every trigger tested, gating improved FULL, AM and PM. | m06, m29 |
| **Allow one trade per swing, with the swing.** Never flip on a 15-s wiggle inside a range. Re-entry is a question of swings, not of the clock. | m12, m28 |
| **Run a daily risk budget from day 1:** stop the book for the day after 3 straight losses or −15 %, and cap trades. A pause-and-resume puts the book straight back into the same chop. | m11, m27, m15 |
| **Do not let a lateness filter pose as confirmation.** The per-stock volume test inside synchrony was only met at the end of a move, so champion entries came 10–45 s after the plain trigger. | m04, m02 |
| **Treat the contract as a sizing dial, not as alpha.** ITM depth only sets the rupees per point. | m09, m10 |
| **Judge exits by MFE/MAE and a race test against random entries,** not by ₹ P&L. On 19 Oct, MFE ≈ |MAE| for the live entries, so no stop or target could have helped. | m01, m23, m24, m25 |
| **Know when the edge exists.** Today's 15-min ranges were 190–205 pts at the open and 28–45 pts after 11:45. Realised volatility fell below the level the options implied at about 10:45 and never came back. | m07, m08, m16 |

### Process

| What should have been done | Said by |
|---|---|
| **Score every rule ask-in / bid-out, split into halves, with a ±20 % neighbourhood and a random-entry null, before it trades.** Count the variants tried. | m21, m28, m30, m23 |
| **Freeze code during market hours. Put changes into shadow books. Pass an acceptance replay before go-live.** The ₹48,146 is four different systems added together. | m27 |
| **Use paper fills at the touch, and include charges.** The LTP was outside the bid/ask in 30–60 % of seconds. Charges are ≈ 0.2–0.25 % per round trip, about the size of the spread. | m13, m22 |
| **Persist state across restarts.** Each restart gave the regime 10 min of WARMING; 7 of the champion's 20 entries were labelled WARMING. Three positions were left unmanaged for 20–60 s. | m06, m27 |
| **Pre-register the expected trade rate and a churn breaker.** The live books ran 3.7–5 trades per minute with a 30-s median hold. | m27, m12 |

---

## 3. Ranked findings

Verdict key: **ROBUST** = holds in both halves, out of sample and across ±20 % on this day (still one day). **FRAGILE** = depends on one
half, one setting, or 1–3 trades. **REJECTED** = loses, or fails out of sample. "Loss-avoider" means the rule's PM "win" is that it takes 0 trades.

| # | Finding | Members | Evidence (numbers) | Verdict | Code status |
|---|---|---|---|---|---|
| 1 | **The champion's entries were worse than random** | m21, m23, m14, m01 | Hold-matched null: champion at the 1.2nd percentile (p 0.012); PM with matched sides p 0.001. PM MFE ≈ |MAE| at every horizon (5 min: +9.3 / −9.4 pts). The mirror of the champion's PM entries (same seconds, opposite option) made 13 trades, 10 wins, ₹1,55,624 | ROBUST (a negative finding) | Proposed: `NULL_PCTL` in the evening report (m21) |
| 2 | **Wrong underlying: the 27-Oct future instead of the spot the 19-Oct weekly settles on** | m09, m10, m19, m20, m26, m28 (also m13, m17) | Basis +8 → +37 pts during the day. In the PM spot never moved ≥ 15 pts in 15 s; the future did 16 times. R² for option moves: future 0.45, spot 0.66, synthetic 0.94. Same rule on spot vs future: PM loses in 6 of 25 vs 25 of 25 cells [m28]. Untuned SPOT/SPOT ₹1,54,281 vs FUT/FUT ₹1,06,376, PM 0 trades vs 3 losers [m26]. The future quote changes in only 27–30 % of seconds and lags spot by 1–3 s | ROBUST as an engineering correction; FRAGILE as a profit source | **D-116** books are on spot. Champion still on the future mid (D-110). `UNDERLYING="spot"` is proposed (m26) |
| 3 | **Spot breakout R2** (12-min spot range break, 12-pt spot trail, one trade per swing) | m28, m30 (addendum) | 33/18 ₹2,31,823 FULL; AM ₹2,04,387; PM 12/6 ₹1,13,091. From 09:35: ₹1,79k; drop best 3 trades: ₹1,04k. ±20 % (9 cells): FULL ₹157–232k, all profitable; PM ₹91–113k, 4 of 9 lose. Latency 5 s: ₹155k; slippage 1 pt per side: ₹142k. Beats random entry / random direction at the 99th / 98th percentile FULL from 09:35, but only the 76th percentile against random entry in the PM. Flipping its direction: ₹33k | ROBUST AM/FULL; FRAGILE PM; not significant after the search | **Implemented D-116** (`spot_dc12_t12`) |
| 4 | **Expiry-day entry window 09:25–11:30** | m07, m29, m30 (m08, m10 related) | Impulse proxy ₹98,905 → ₹1,66,079 (PM 0 trades); every cut-off from 11:05 to 11:55 profitable; activity gate (15-min range ≥ 60) ₹1.36–1.79 L. From 09:35 it is only ₹94–110k [m30]. On HEAD the champion gets 0 trades, ₹1,00,000 [m29]. It cuts the same trades as SPOTCONF, G-RV and the VWAP cap | ROBUST as a loss-limiter; FRAGILE as profit | **D-116** `spot_dc12_t12_1130` has it. For the champion it is proposed (`ENTRY_WINDOWS_0DTE` / `ZERO_DTE_LAST_ENTRY`) |
| 5 | **Brakes: stop for the day, not pause** | m11, m27 | Champion's real 20 trades: none ₹48,146 → D-113 as built ₹81,164 → m11 "P" (−15 %, 3 losses → stop for the day, max 6 trades/day) ₹91,336. Random books: P(loss > 25 %) 60 % → 0 %. A 3-loss pause alone is the weakest brake (worse than none on 7 of 11 combos). Shadow-on-change would have ended the official champion flat at ₹1,00,000 [m27] | ROBUST as capital protection; no edge | D-113 implemented (pause). Stop-for-day, `MAX_TRADES_PER_DAY=6` and a system kill switch are proposed |
| 6 | **Regime gate as a hard gate** | m06, m29 | Improves all 4 triggers in every window (+₹16k … +₹1.15 L); live-like trigger ₹42,277 → ₹1,57,548. On HEAD the funnel lets 1 of 106 episodes through. Profit appears only with the futures-only trigger and only from 09:25–09:36. Restart WARMING made many of the live "vetoes" | ROBUST as a loss-avoider; FRAGILE as profit | D-112 implemented. Persisting regime state across restarts is proposed |
| 7 | **One trade per swing / churn** | m12, m28 | 13 of the champion's re-entries were flips; re-entries within 5 min ≈ −₹38,400. SWING-ONE Z = 60: live base ₹1,64,353, never worse than −2.3 % in the PM across Z 48–72; most of the gain is two trades at 09:25–09:34. Time cool-downs of 600–1080 s jump ±40 % between neighbouring settings. The swing rule adds ₹12–19k to R2 | ROBUST as a damage limiter; FRAGILE as profit | 60-s cool-down D-109 implemented. Swing rule is in **D-116**. SWING-ONE for the champion is proposed |
| 8 | **Volume test inside synchrony is a lateness filter** | m04, m02 | Gated entries 10–45 s late. Every S_vol threshold loses FULL (₹45–94k) while the ungated trigger makes ₹1.29 L. S_vol ≥ 0.5 at only 5 of 64 impulses. S without volume almost never says no (62/64). Spearman(S, next move) is ~0, negative at the 15-pt floor | ROBUST as harm-removal; no edge | The `m2.0_s0.5_novol` book exists (D-100). Changing the champion is proposed only through the challenger test |
| 9 | **Thesis-void exit** | m02, m04 | Live TV (volume S, 0.5, 5-s hold) almost never fires (≤ ±1 %); holds of 15/30 s never fire. TV-fast (S without volume ≥ 0.30, z ≤ −1, 1-s hold) beats stop/trail in 18 of 18 neighbourhood cells, for every entry family and both halves, and by +23.8 % (mean log) over 60 random-entry seeds. PM still loses (best ~₹94k) | ROBUST as an exit improvement; not a profit source | Proposed variant `m2.0_s0.5_tvfast` |
| 10 | **VWAP stretch gate** (no entries when |future − VWAP| > 60) | m16 (m05) | Improves FULL in 18 of 18 settings; all 54 ±20 % combinations end FULL > ₹1 L. Would have blocked 19 of 20 live champion trades. PM result is "flat", not profit. Absolute-point threshold. VWAP-side alone hurts the AM | ROBUST as a loss-avoider; FRAGILE as profit | Proposed (later, expressed as a relative stretch) |
| 11 | **Realised-vs-implied volatility gate (G-RV)** (enter only if σ15 raw ≥ VIX-implied) | m08 | ₹91,414 → ₹1,63,245; flat over k 0.7–1.2 and half-life 16–24 min; PM 0 trades. Today it is identical to "no entries after ~10:45". From 09:40 the gated system ends at ₹91,804 | ROBUST as a loss-avoider; FRAGILE as profit | Proposed: log `rv_iv` for ~10 days first, gate later |
| 12 | **`fade_switch`** (impulse ≥ 10; follow if the 15-min range ≥ 60, else fade; bracket 12/12/180 s) | m14, m30 | 55/33 ₹2,13,886; AM ₹1,53,898; PM ₹1,39,702. From 09:35 ₹2,21k; nulls at the 99th percentile. Breaks at impulse floor 8 (₹93k FULL, ₹57k AM) and at 1 pt slippage per side (₹90k). Thin edge per trade on 55 trades. Needs a new bracket exit, and the regime gate must be off for it | FRAGILE | Proposed as a shadow book. Not implemented |
| 13 | **Impulse floor / size** | m03, m14, m20, m29, m30 | Impulses < 10–12 pts: 0 % of 405 follow configurations profitable in the PM. Floor 20: ₹1,22,669, but that is 1 trade (+₹47,645); the 90th percentile of random entries is ₹1,23,241. Lowering the floor to 10–12 brings PM losers back under every gate | ROBUST as damage control (keep ≥ 15); raising it is not needed | D-109 (15 pts) implemented. Do not lower it |
| 14 | **Exits, holds, targets** | m01, m10, m23, m24, m25, m30 | Race test: the hit ratio barely moves for X = 6…30 pts. 74 exits × 3 entry sets: none profitable in both halves on the champion's entries. d25 + 20-min time stop ₹3,03,002 [m10] collapses to ₹1,30k from 09:35, and the 24-min neighbour loses [m30]. Bank exit (20 → 0 over 120 s) beats live in 8 of 8 cells but also rescues 26 of 30 random-entry books, so it measures the day. fix20 beats fix12 in 5 of 6 pairings, a weak tilt | REJECTED as a profit source; time stop REJECTED; fix20 and bank are weak tilts | No change to the champion's d* = 12. Shadow `d_star = 20` with no time stop proposed (m01, m30). Bank as an observer, proposed (m24) |
| 15 | **Trend filters (D-114, 30-min trend ≥ 20)** | m05, m14, m21, m07, m26 | D-114-like: 9 trades, 1 win, ₹57,025, the worst filter on both impulse versions. It cuts the morning reversal winners. Day-open side / VWAP side on old noisy entries: PM −41 % → −2 % | REJECTED as profit; ROBUST negative | D-114 registered. Keep it as a book but expect nothing from it. A day-open-side gate is proposed (low priority) |
| 16 | **Contract choice** | m09 (m10, m22) | Spread ≈ ₹240 of a ₹2,467 mean PM loss. Champion entries: OTM50 ₹35,767 … ITM200 ₹69,824. No depth wins, and the best depth reverses between halves. Harness PE picks are 50–100 pts deeper than the engine's [m22] | ROBUST: keep ITM ≈ 100 / delta 0.65–0.85 | No change. De-risk depth after the first loss is optional and overlaps the brake |
| 17 | **Fills, latency, harness fidelity** | m13, m22 | Repricing fills moves results ±1–3 %. Charges are ≈ −5 % on a 20-trade day. Fill at i+3 instead of i+1: ₹105k → ₹72.6k. The harness forbids a same-second flip, which flatters churny rules by up to +13 pp. The pack is exact (98/98 quotes). **Any result within ±15 % of ₹1 L on ≤ 15 trades is noise** | ROBUST (as measurement) | Proposed: `FILL_AT="touch"`, charges, entry safety gate, harness fixes |
| 18 | **Statistics: one day cannot prove an edge** | m21 (m30, m14) | About 12,000 variants across the council. The median of the best of 430 random books is ₹2,83,157. Bonferroni leaves every rule at p = 1. Detecting +2.5 %/trade at sd 11 % takes about 120 trades. AM-vs-PM rank agreement is 0.21 | ROBUST | Proposed: `tools/evaluate_rule.py`, registration dates ≥ 2026-10-20, fix `SPRT_SIGMA_PCT` |
| 19 | **Process failures** | m27 | 4 code versions in one book; 3 in-session restarts. D-108 segment: 167 trades, −2.76 %/trade. D-109 segment: 2 wins in 42. 31 minutes from the owner flagging the churn to the fix going live: −₹3.92 L across the books | ROBUST | OP-1 proposed (section 6) |
| 20 | **SPOTCONF gate on futures impulses** (spot r15 ≥ 0.8 × future r15) | m20, m29, m30 | ₹1,08,044 → ₹1,72,901 (PM 0 trades). Non-monotone in c (0.70–0.75 lets a PM loser in); fails at floor 10/12; 5 s latency: ₹110k; no effect on the HEAD champion [m29]; same trades as the clock window | FRAGILE (a loss-limiter only) | Proposed, but moving the signal onto spot (#2) supersedes it |
| 21 | **Options flow, domino lag, straddle spike, opening range, day structure** | m17, m19, m18, m15 | The 1-s cash → future lead is real, but the option premium already contains it (synthetic +3.6 before entry). Flow signs flip between AM and PM. Spike: PM loses in 12 of 12 cells. ORB5: n = 1 | REJECTED as entries. ORB5 FRAGILE (an observation book only) | Logging only (`syn15`, `basis15`, `fwd_in/out`). 0DTE theta clock fix proposed (m18) |
| 22 | **Bank Nifty / Fin Nifty lead** | m20 | Bank Nifty future LTP changes in 14 % of seconds, Fin Nifty in 1 %: stale. The bank/fin filters are non-monotone | REJECTED | Proposed: retire or re-base `BankLead` (extras.py) |

---

## 4. Disagreements, and how the evidence settles them

**m21 "nothing is significant" vs m30 "R2 beats 96–99 % of random nulls".** Both are right about different questions. m30 shows R2 is not the
09:25 crash in disguise: it survives a 09:35 start, the loss of its best 3 trades and both nulls. That rules out the specific way most
other rules fooled us. m21's point is about selection. R2 was the best of about 340 cells in m28's own grid and of about 12,000 variants across the
council. A 1-in-100 result is what that much searching produces as a matter of course. Bonferroni-corrected, it is not significant. **Settled:** R2 is the
best candidate to watch, and it is unproven. It earned a pre-registered book (D-116), not the champion's seat. 19 Oct can never count as its evidence.

**Spot confirmation: robust (m20) or fragile (m30), and inert (m29)?** These are two separate claims. (a) *The signal should be measured on spot* is
ROBUST. It has a mechanism (settlement, lead, quote quality, basis drift) and it shows up across members: m26's fidelity R² and m28's PM 25/25 vs 6/25.
(b) *A SPOTCONF ratio gate bolted onto a futures impulse* is FRAGILE: non-monotone in c, latency-sensitive, inert on the HEAD champion, and it removes
the same 3 PM trades as the clock. **Settled:** move the signal onto spot instead of adding a confirmation ratio. Do not count SPOTCONF and the 11:30
window as two independent confirmations.

**Wider stop and longer hold (m10: d25 + 20-min time stop "ROBUST in the AM") vs m25 / m30 / m28 (FRAGILE / REJECTED).** m10's ₹3.03 L is
₹1.30 L from 09:35. The 24-min time-stop neighbour loses. On spot, trails ≥ 20 pts lose the PM almost everywhere [m28]. m25 shows the sign
flips between halves: a wide stop helps in the volatile AM and hurts in the PM. **Settled:** no time stop. d* stays 12 for the champion; d* 20 with no time stop
runs as a shadow only (m01 and m30 agree on this).

**Fade (m14) vs "never fade" (m03, m21, m05).** m03 and m21 tested fading ≥ 15-pt impulses: it loses, because the big AM moves trended. m14 fades
only in a narrow range (15-min range < 60) and follows otherwise. Without the switch both halves fail (follow-only AM ₹87k, fade-only AM ₹56k).
**Settled:** fading as a standalone rule is REJECTED. `fade_switch` is FRAGILE (floor 8 and 1 pt of slippage break it) and gets a shadow book at most, never the
champion.

**Volume test: remove it (m04) vs keep the champion unchanged (m29).** m04 shows S_vol loses at every threshold and enters 10–45 s late. m29 shows
the `novol` book on HEAD (₹93.6k) rests on one +36 % trade. **Settled:** the mechanism argument is strong, but the P&L evidence is one trade.
The existing `novol` book is the challenger. Let the learning loop decide.

**Bank exit (m24) "ROBUST relative improvement" vs m01 "no exit creates edge".** Both are right. Banking quickly beats the live trail in 8 of 8
cells, but it also rescues 26 of 30 random-entry books, which shows it is measuring today's short-horizon mean reversion. It would cut winners
on a trend day. **Settled:** observer book at most.

**Regime gate (m06 "keep it") vs trend gates harmful in the open (m05, m07, m14).** No conflict. D-112's regime gate improves every trigger.
D-114's 30-min trend filter makes every trigger worse. They are different gates. Keep D-112 and expect nothing from D-114.

**"All the loss-avoiders work" (m07, m08, m16, m20, m12).** The time window, G-RV, the VWAP cap, SPOTCONF and SWING-ONE all take the same 0 PM
trades and remove the same late-AM losers (11:16, 11:35, 11:41, 12:04). They are **one** finding seen five ways: *after about 11:00 on 19 Oct there was
nothing worth buying*. Implement one or two, not five. Each extra gate adds parameters and multiple-testing load.

---

## 5. Recommended rule set for Wednesday 21 Oct

First, two facts about Wednesday:
- **21 Oct is not an expiry day.** Every expiry-only rule (the 11:30 cut, `spot_dc12_t12_1130`, 0DTE delta bands) is dormant. `spot_dc12_t12` and
  `spot_dc12_t12_1130` will trade **identically** on Wednesday. Their difference shows only on expiry days.
- If the contract traded is the 27-Oct series, the 27-Oct future is the **same-expiry** forward, so the basis argument against the future is much
  weaker on Wednesday. The quality argument is not: the future's quote changes in only 27–30 % of seconds, lags spot by 1–3 s, and its spread is above 6 pts 37 % of the time [m13, m26].

### (a) Champion and risk changes the council endorses

These are risk controls. None of them is claimed to make money.

1. **Keep HEAD's gates**: D-109 (15-pt floor on the mid, 60-s cool-down), D-111 (σ floor 5), D-112 (regime as a hard gate). On today's tape they turn −52 %
   into −11 % [m29]. **Do not lower the 15-pt floor** [m03, m20, m30].
2. **Brake: stop for the day, not pause** [m11]: −15 % on the day (kept), **3 straight losses → no more entries today**, **at most 6 entries per day**.
   Control books exempt. Add a **system kill switch** (KILL file / dashboard button; auto-trip at > 4 champion entries in 30 min or −25 % on the day) [m27].
3. **Expiry-day entries end 11:30** for the champion family, as a risk rule [m07, m29, m30]. Dormant on Wednesday; it matters next expiry.
4. **Paper fills at the touch plus charges** (`FILL_AT="touch"`, entry = ask, exit = bid, STT/txn/stamp/GST/brokerage deducted) and the entry safety gate
   (spread ≤ 1 pt and ≤ 1 %, quote ≤ 5 s, last trade ≤ 60 s) [m13, m22]. This makes the reported numbers worse and honest.
5. **Persist regime state across restarts** (or rebuild it from the day's tape) [m06]. Refuse `stop` while a position is open [m27].
6. **No change** to d* (12), contract choice (ITM ≈ 100 / delta 0.65–0.85), or the champion's synchrony settings [m01, m09, m25].
7. **Not before an acceptance replay** (D-105 lock-step, at least 19 Oct plus 2 other recorded days): D-110 … D-115, and the champion changes 2–5 above.
   If the replay is not done by Wednesday's open, the champion runs on its committed code and the changes run in shadow.

### (b) Books to run beside it (pre-registered on 20 Oct; 19 Oct excluded from their evidence)

Each extra book raises the bar for every book (m21). Keep the list short and in this order of priority:

| Priority | Book | Rule | Status |
|---|---|---|---|
| 1 | `spot_dc12_t12` | R2: spot breaks its previous 12-min range → buy that way; 12-pt spot trail; one trade per swing; −15 % daily stop only | **Implemented D-116** |
| 1 | `spot_dc12_t12_1130` | Same, expiry-day entries end 11:30 (R3) | **Implemented D-116** |
| 2 | `m2.0_s0.5_spot` (champion twin) | The champion's own numbers with signal and stop on spot (`UNDERLYING="spot"`) | Proposed (m26) |
| 3 | `fade_switch` | m14 P1, bracket 12/12/180 s, regime gate off, exempt from the 15-pt floor | Proposed (needs the bracket exit) |
| 4 | `m2.0_s0.5_d20` | The champion with d* = 20, no time stop | Proposed (m01, m30) |
| 5 | `m2.0_s0.5_tvfast` | Thesis-void on S without volume ≥ 0.30, 1-s hold | Proposed (m02) |
| — | Keep running as they are | `m2.0_s0.5_novol`, `m2.0_s0.5_trend` (D-114), `random_entry`, `futures_only` controls | Existing |
| — | Observers only, if cheap | `orb5` (m15), `m2.0_s0.5_bank` (m24) | Proposed, lowest priority |

**What evidence would prove an edge** [m21]:
- At least **~120 post-registration trades** per book. That is enough to detect +2.5 %/trade at a per-trade sd of ~11 %. R2 trades about 15–34 times a day, so this means
  roughly 4–8 sessions. The champion trades 0–6 times a day, so it needs 20+ sessions.
- At least **10 sessions including ≥ 2 expiry days, ≥ 3 trend days and ≥ 3 chop days**. One day is one regime observation.
- Each book must beat both random nulls (random entry, random direction) at p < 0.05 / N, with N = the number of books under test. It must pass `learning.py`'s SPRT
  (with `SPRT_SIGMA_PCT` re-set from 30 % to the measured 11–21 %) and the Bonferroni challenger test on 2 evenings in a row, and pass the start-shift and
  drop-best-trade checks [m30].
- Until then, **no book is promoted, and no ₹ figure from 19 Oct is quoted as expected performance.**

### (c) Things NOT to do

- Do not crown R2, `fade_switch`, or anything else on 19 Oct's numbers. Do not quote any 09:25-start ₹ figure [m21, m30].
- Do not tune d*, the floor, N or D to today's best cell. AM-best → PM: R2 grid ₹2.82 L → ₹30k [m28]; m01 s20_tp40 +262 % → PM −24 %.
- Do not add a time stop, a break-even stop, big targets, σ-scaled stops, or stops under ~8 pts [m01, m23, m25, m30].
- Do not lower the 15-pt impulse floor. Do not fade small impulses as a standalone rule. Do not follow impulses < 12 pts [m03, m14].
- Do not use D-114's 30-min trend as a fix; it is the worst filter [m05, m14, m21].
- Do not trade the basket gap, options flow, OI, Bank/Fin futures leads, or the straddle spike on the old theta clock [m17, m18, m19, m20].
- Do not go ATM/OTM on expiry day for leverage [m09, m10].
- Do not stack SPOTCONF + clock window + G-RV + VWAP cap and count them as separate confirmations (section 4).
- **Do not change code during market hours. Do not promote anything intraday** [m27].

---

## 6. Process (m27 OP-1)

- **Change freeze 09:00–15:40.** If the code hash differs from the day's recorded hash, every book becomes a shadow book `<name>@<hash>` starting at ₹1,00,000. The official
  champion takes no new entries. The only exception is a written safety fix that *removes* entries.
- **Acceptance gate before any hash is champion-eligible:** a lock-step replay on ≥ 3 recorded days including the latest expiry. Invariants: ≤ 6 entries/hour and
  ≤ 4 in any 30 min, median hold ≥ 60 s, no reversal inside the cool-down, expiry policy respected, no entry while a gate or brake blocks, data health ≥ 90 %.
  The gate also produces a trade-by-trade diff against the previous hash.
- **Pre-open self-test:** replay the last recorded day 09:15–10:15 and compare it with the hash's golden summary. Any mismatch is NO-GO.
- **Kill switch and churn breaker:** a KILL file or button stops all new entries at once (exits keep running). It auto-trips at > 4 champion entries in 30 min or at −25 % on the day.
- **Restart safety:** `stop` refuses while a position is open. A restart reloads the same registry and bands, and the regime and trend state.
- **Promotion ladder:** new code → acceptance → ≥ 1 full session in shadow → champion only via the challenger test (≥ 10 days, Bonferroni, 2 evenings in a row). **Never intraday.**
- **Owner requests during the session go to a queue:** coded after 15:40, replayed on that day's tape, live the next day.
- **Every rule is judged with the council's checklist:** ask in / bid out with charges, AM/PM halves, ±20 % neighbourhood, random-entry and random-direction nulls,
  a start-shift (09:25 → 09:35) and drop-best-trade check, latency L = 1–3 s, and the council-wide variant count.

---

## 7. Lead's lock-step replay of 19 Oct (code 9d63dd2: D-116 … D-122)

`python run_apex.py acceptance 2026-10-19.jsonl.gz` — the whole recorded day (all five tape parts, the three feed
restarts included) through the real engine, lock-step, 100-ms steps. Paper fills at LTP (owner rule); the second
set of columns re-prices every trade at the recorded ask in / bid out, and the last one adds 0.15 % a side for charges.

| Book | LTP (owner rule): n / wins / ₹ | Ask in, bid out: FULL | AM (to 12:30) | PM | + 0.15 %/side |
|---|---|---|---|---|---|
| `spot_dc12_t12` | 32 / 19 / **₹4,68,657** | ₹5,22,064 | 20 / 13 / ₹3,90,459 | 12 / 7 / ₹1,33,173 | ₹4,79,569 |
| `spot_dc12_t12_1130` | 14 / 9 / **₹2,67,992** | ₹2,98,305 | same | 0 trades | ₹2,88,711 |
| `fade_switch` (D-121) | 55 / 29 / ₹1,50,788 | ₹1,20,332 | ₹1,07,862 | ₹1,11,508 | ₹1,01,260 |
| `straddle_spike` | 6 / 3 / ₹1,67,532 | ₹1,66,560 | | 0 trades | ₹1,63,975 |
| champion `m2.0_s0.5` (all of D-109 … D-117) | 0 / 0 / ₹1,00,000 | | | | |
| `m2.0_s0.5_novol` | 2 / 1 / ₹1,18,671 | | | | |
| controls: `random_entry` / `futures_only` / `premium_momentum` | ₹85,079 / ₹1,03,133 / ₹28,672 | | | | |

Live on 19 Oct the champion went to ₹48,146. The same tape through today's code: the champion does not trade
(every afternoon "impulse" is now below the 15-pt floor on the mid or vetoed by the regime gate), and the spot
breakout book makes 4.7x.

**Why the engine beats the council's harness (₹2.32 L):** the engine picks the strike by delta band (near the money,
cheaper premium, more lots, more gamma on an expiry day) where the harness bought 100 pts in the money, and it reads
spot sub-second instead of at 1 Hz. Spreads on the traded options were 0.2–0.4 pts; the quotes were fresh (median
quote age 0.4 s at the exit).

**The first replay (code 3f11460) found a bug (D-122):** "one trade per swing" kept the day's best spot per direction,
so after the 09:29 put every put was blocked until 12:04. That run ended at ₹1,19,997 at 14:26; the fix restores the
council's rule (compare with the last trade only).

**Acceptance (D-119): FAIL on one check only — 21 data-gap blackouts.** They are in the recording itself (the live
feed went silent for 3–39 s again and again between 11:36 and 12:07 and around the three engine restarts); the engine
correctly paused entries. No stale-quote fill, no wrong expiry, no brake breach, no flip inside a cool-down, no churn.

**What this does NOT prove.** The rule was found on this same day (in-sample), by a council that tried ≈ 12,000 variants
(m21). One expiry day with a 250-pt fall and a trending morning is the best case for a breakout rule. The afternoon
(PM ₹1.33 L) is the part closest to a fair test, and m28/m30 found 4 of 9 neighbouring settings lose there. Wednesday
21 Oct is not an expiry day (options have 6 days to run, less gamma). Expect much less than 4.7x; judge it after
≥ 10 sessions / ≈ 120 trades.

## 8. Lock-step replay with `spot_dc12_t12` as champion (D-124 / D-125, code ef53160+)

Same tape, same command (`run_apex.py acceptance`), the owner's champion in place, brakes off (D-123), the review fixes in (D-125).

| Book | n / wins / ₹ at the close | Note |
|---|---|---|
| **champion `spot_dc12_t12`** | **32 / 19 / ₹4,68,657** | identical trade list to §7, to the second and the paisa |
| RAW (champion without gates) | 32 / 19 / ₹4,68,657 | the spot rule has no gates, so RAW = champion |
| `spot_dc12_t12_1130` | 14 / 9 / ₹2,67,992 | |
| `fade_switch` | 55 / 29 / ₹1,50,788 | |
| `straddle_spike` | 13 / 4 / ₹84,741 | 6 trades / ₹1,67,532 in §7 was the 6-entry cap (D-117), now off |
| old champion `m2.0_s0.5` | 0 / 0 / ₹1,00,000 | |

Checked on this run: the event tape and the decision tape follow the spot book (classes "spot inside range", "same
swing", "already in a trade"); the dashboard rendered in a headless browser at 07:57 (range warming), 09:27 (inside the
range, same swing as the last trade) and 09:36 (in a 23050 CE, "12.0 spot pts to TRAIL, stop at 23,144.1") with no
script errors; the evening learning run produces the scoreboard for `spot_dc12_t12` ("COLLECTING", 32 trades, observed
sd 11 %); `state.json` names the champion with `champion_since` 2026-10-20 and an owner log entry. Acceptance: the only
FAIL line is the recording's own 21 feed gaps.

## 9. Council 5 (20 Oct evening): honest fills, the profit lock, the fast replay — the numbers

**The fill correction (D-126) comes first.** Every figure in §7 and §8 was priced on the option's last print at the
moment spot triggered — a print from before the move. Re-priced on the first print after the trigger (entries ≤ 3 s,
exits on the next print), the same 32 champion trades of 19 Oct give **₹1,79,378** instead of ₹4,68,657. The engine now
fills that way; the 19 Oct numbers below are from the corrected engine (lock-step replay, code of council 5).

| Book | n / wins / ₹ at the close | Note |
|---|---|---|
| **champion `spot_dc12_t12`** (lock 18 / 10) | **32 / — / ₹1,90,161** | 11 trades armed the lock; 4 exited on it, 7 on the spot trail after arming |
| `spot_dc12_t12_nolock` (the old rule) | 32 / — / ₹1,81,156 | the lock is worth ≈ +5 % on this day — small, as T01 said |
| `spot_dc12_t12_1130` | 14 / — / ₹1,66,745 | |
| `fade_switch` (shadow) | 55 / — / ₹2,08,433 | the delayed fills HELP a fade rule (it sells into the print that follows) |
| `straddle_spike` | 13 / — / ₹80,623 | |
| old champion `m2.0_s0.5` | 0 / 0 / ₹1,00,000 | |

**Determinism of the fast replay (D-128):** the standard three-process lock-step replay and `--fast` on the same
code: **26 books, 251 trades, identical in every field** (T10's `diff_trades.py --all-fields`), tapes identical. Wall
time 1,246 s (21 min) for the fast run while sharing the machine with the standard one; alone ≈ 18 min (T02).

**The commentary on 19 Oct:** the first full-day tape (before the warning throttle) hit its 5,000-line cap with 3,600
warnings — fixed (a warning key ≥ 15 s apart, any two warnings ≥ 5 s apart). Verdicts, entry cards (grades A–E) and
review cards were produced for all 32 trades. The dashboard was rendered headless against the live replay: header
tiles, the band in profit / locked / near-stop states, the entry card ("Grade C — fair · 106 pts ITM vs spot, 16 %
extrinsic …"), the feed with stock chips, the verdict card.

**Still true:** one day, found on the same day. Judge after ten sessions.
