# 08 — Council report: live paper session, Monday 19 Oct 2026 (weekly expiry)

Team leader's consolidated report of 30 independent member reports (`/tmp/claude-0/council3/m01.md` … `m30.md`).
Code state at the time of writing: HEAD `f84b94a` (D-095 … D-106 committed). Data: tick tape 07:45–10:51:30 IST (truncated),
paper books, decision tape, candidate ledger, episodes, events and logs of 19 Oct.
Where members disagreed, the evidence decided. Where nobody had measured the committed code, the team leader replayed
today's tape through it (section 4, "Lead replay").

---

## 1. The answer in five lines

1. **For about 25 % of the entry window the data guard was switched on although the feed was healthy, and an "episode was alive during a gap" rule blocked another ~30 %.** Together they put the champion in "data gap" for 55.6 % of 09:25–10:51. The Nifty future sends only about one quote per second, and it was silent for more than 3 s 79 times, while the feed as a whole never went quiet for more than 2.5 s. Each silence cost at least 20 s of blackout, and every episode alive at that moment stayed untradeable for the rest of its life. (FIXED: D-097, D-098.)
2. **When the futures push did arrive, the rule itself said no: the heavyweight basket was "too thin" 17 times out of 23 pushes.** The main cause is the per-stock volume test inside synchrony: each stock's 15-s volume must be at least 1.2× its own *mean*, and volume is heavy-tailed. That test removes about 60 % of the stock weight that is already moving the right way. S ≥ 0.5 together with z ≥ 2 happened in only 5–9 % of impulse seconds. (RULE, owner decision; observed through the D-100 variant.)
3. **The one trade was fake.** Every call option was frozen at Friday's close: the ttq-only ordering guard dropped 86 % of call packets. Depth packets kept the frozen rows looking 0.1 s old, so no staleness check fired. The real trade was 132.15 → 126.25, a loss of 5.9 points (−4.5 %), booked as 112.2 → 112.2 = 0. (FIXED: 17ef498 → 8b52c99, D-095/D-096, D-102.)
4. **The per-stock scales and volume baselines were trained on the 09:00–09:15 pre-open auction prints.** Three heavyweights were 1.5–2.2× too wide until about 10:00, which cost about a third of the qualifying moments. (FIXED: D-099.)
5. **After 10:10 the feed ran 3–14 s behind the exchange in a 32-s saw-tooth, which made the futures silences longer and smeared the 15-s impulse.** Correlation of z with the exchange-clock z fell from 0.82 to 0.60. No guard measures this lag. (D-106 is a fix based on a hypothesis about the cause, still to be verified live. A lag guard is OPEN.)

The frozen CE prices did **not** change how many times the champion fired today: z and S read futures and stocks, which were 99.7 % intact. They did corrupt prices, P&L, IV, the strikes chosen, the straddle books and all learning evidence.

---

## 2. Root causes, ranked

Severity is the effect on trading today. "Found by" lists the members who reported the issue independently in their own area.

| # | Issue | Severity | Found by (n) | Evidence (today's data) | Status |
|---|---|---|---|---|---|
| 1 | **Data guard `STALE_S = 3 s` measured on the Nifty-future quote alone** (`guard.py:24` old, `engine_main.py:304-305`) | CRITICAL | m03, m04, m12, m13, m17, m20, m21, m22, m23, m24, m25, m27, m28, m30 (14) | Future quote gaps: p50 0.87 s, p99 3.35 s, max 7.4 s; 79 silences > 3 s; the whole feed was never silent > 2.49 s (27–174 other packets/s arrived inside every futures silence). 47 blackouts, 1,225 s = 24–25 % of 09:25–10:51, and 0 real outages. 10:15–10:51 was 0 % clean. | **FIXED** D-097 (`8a1838d`): blackout only if no instrument has delivered for 3 s, or the future is quiet > 10 s; `EXIT_FUT_STALE_S` 3 → 10. Replayed on today's tape: 0 blackouts. |
| 2 | **Any gap during an episode's life tainted the episode for good** (`engine_main.py:336-337` old) | CRITICAL | m03, m04, m08, m20, m21, m28, m30 (7) | Tainted episodes were live 52.7 % of the window; 1,660 s labelled "data gap" were really "clean feed, tainted episode". Lost triggers: 09:55:13 DOWN (z 2.07, S 0.51, moved 8.9 against a budget of 24.6; futures then +45 to +71 in its favour) and the 10:30 DOWN episode (+12 hit after 72 s). 12 episodes tainted from 09:49 on. | **FIXED** D-098: tainted only if born while the guard is on. |
| 3 | **Per-stock volume test inside S (`act ≥ 1.2 × EWMA mean`)** (`domino.py` act_ok, `config.ACTIVITY_MIN`) | CRITICAL (by trade count) — this is the rule, not a bug | m05, m06, m07, m16, m19, m30 (6); S binding also in m08, m09, m15, m21, m22, m28 | At z ≥ 2: median S 0.12–0.17 with the test, 0.39–0.45 without it. Decisions with S ≥ 0.5: 2/86 with it, 25/86 without; episodes 1/21 against 10/21 (m07). The 15-s volume mean is 1.4–2.3× its median. Moving heavyweights have a median act of 1.01–1.07, so a "1.2× mean" bar fails them. In every one of 53 near-miss moments the single failing gate was S (m21). | **OPEN, owner.** The champion is unchanged (D-033). A pre-registered `m2.0_s0.5_novol` book was added (D-100). |
| 4 | **ttq-only ordering guard froze every call option at Friday's close** (`17ef498^:feed_core.py`) | CRITICAL for prices, P&L, IV and evidence; zero effect on the champion's trade count today | m01, m02, m10, m11, m12, m13, m14, m15, m18, m21, m22, m24, m26, m27, m28, m29, m30 (17) | Dropped: 86.2 % of call packets (weekly CE 204,453 of 220,594) and 25 % of put packets. 23050 CE applied 1 packet and dropped 7,952. It read 112.2 all morning while the real price ranged 43.75–148.95. All 18 CE trades in every book carry `trade_age_in` ≈ 237,000 s (66 h). | **FIXED** 17ef498, then 8b52c99. Verified by m01, m27 and m30: HEAD drops 0 whole packets, and the table differs from the last packet on 24 of 637,330 option packets. |
| 5 | **Depth packets refreshed `recv_ns`, so frozen quotes looked fresh** (`feed_core.py` depth branch, `engine_main.py:489`, `paper.py:132`, `paper.py:413`, ledger `age < 15`) | CRITICAL (it hid #4 from every check) | m02, m11, m13, m17, m18, m28, m29 (7) | The engine saw 23050 CE as 0.1 s old at entry while the real quote was 2,626 s old. `exit_quote_age` was 0.06–1.9 s on every frozen exit, and `stale_exit` = None on all 43 records. The 09:29 re-centre gave 22950 CE depth, which made its frozen 182.0 (real 99.45) eligible for contract choice. | **FIXED** D-096 (8b52c99): depth writes only `depth_ns`. D-102 adds: a contract with no trade today counts as stale everywhere. |
| 6 | **The 17ef498 hotfix itself dropped packets that were newer** (ltt jitters by ±1 s) | HIGH (now superseded) | m01, m02, m03, m07, m10, m15, m16, m20, m23 (9) | 56,451 packets dropped, 38,235 of them carrying a higher ttq. FINNIFTY FUT frozen for 733 s; 23750 PE for 480 s. m15 and m23 warned that this would double the futures gaps (79 → 151–153). | **FIXED** 8b52c99 (field-by-field rule). Verified: 0 whole packets dropped; futures silences back to the raw 79, which D-097 then tolerates. |
| 7 | **Per-stock σ and volume baselines learned from pre-open prints; warm-up counted from engine start (07:45)** (`domino.py:87-105` old) | HIGH | m05, m06, m07, m16, m17, m18, m19, m25, m30 (9) | At 09:25, scales were too wide: SBIN 1.48–1.90 vs 0.85; BHARTIARTL 1.55 vs 0.83; KOTAK 1.50–1.57 vs 0.70 (1.4–2.2× until 10:30). The HDFCBANK volume baseline was 114,209 at 09:08 against 12,395 learned in session. Qualifying steps (z ≥ 2 and S ≥ 0.5): 205 vs 304 (m19). | **FIXED** D-099 + fast start (`8a1838d`, `9a9dde9`). Verified on the committed code by the lead's replay (section 6). |
| 8 | **Feed delivery lag after 10:10: 32-s saw-tooth, 3–14 s behind the exchange, index seconds lost** (`feed_breeze.py on_message`; engineio starts a thread per message) | HIGH | m04, m17, m20, m28 (4) | NIFTY index recv − ltt: median 0.4–0.8 s before 10:05, then 2.1–7.6 s (max 14.5 s). 25–45 % of exchange seconds never arrived. Throughput fell from 230/s to 140–180/s. Correlation of r15 with the exchange-clock r15 fell from 0.82 to 0.60. The cause is a HYPOTHESIS: client thread churn or CPU, or Breeze conflation. | **PARTLY ADDRESSED.** D-106 (`f84b94a`) dispatches messages in the read loop, but this is unverified live. D-103 shows the lag on the dashboard. **A lag guard is OPEN.** |
| 9 | **IV, forward and ATM-IV rise computed from frozen CE legs; no staleness check; the IV cap fails open** (`engine_main.py:435-472`, `greeks.py:111` 150-pt bound, `paper.py:204-206`) | HIGH (learning and evidence; 0 champion entries blocked today) | m09, m10, m11, m14, m21, m24, m26, m30 (8) | Forward off by +27.7 pts on average (max +112). ATM IV off by +6.1 vol on average (max +18.4). iv_rise was +3.62 median on down-moves and −1.56 on up-moves: direction-dependent garbage. On correct data the cap blocked 0 triggers in every configuration (m30). With the polluted IV it would have blocked the 09:59 trigger once the other fixes were in. | **FIXED, partially**, by D-102: legs ≤ 30 s (by receive time) only. The fail-open behaviour and the 150-pt bound are unchanged (section 6). |
| 10 | **PE strikes chosen from the polluted forward** | MEDIUM | m11, m15, m24 (3) | The old PE pick differed from the correct one at 128 of 174 samples, on average 144 pts deeper ITM (up to 343). | FIXED by #4 and D-102. |
| 11 | **Learning evidence contaminated** (`learning.record_day`, `_load_days`, ledger, advisor screens) | CRITICAL for tonight's learn | m10, m11, m13, m14, m15, m22, m24, m29 (8) | 24 frozen-CE trades in 12 books would be recorded as genuine 0 % trades. The futures_only control would be recorded at −22.6 %/day although it was really about +13.4 %. The sign of "champion vs control" flips. 12 of 27 ledger option returns are frozen zeros. Advisor veto rates (coherence 87 %, gex_room 61 %, regime 97 %) are polluted. | **FIXED** D-101 (`b4bdd92`, m29's patch applied verbatim). The **owner must still declare the window** (section 7). |
| 12 | **Stops and trails measured on the futures LTP, which bounces across a 5.6-pt spread** (`engine_main.py:290`, `paper.py:372-382`) | MEDIUM (honesty of the evidence, not trade count) | m12, m13, m15, m22 (4) | Futures spread: p50 5.6, p90 10.7. 29 of 34 exits fired on a print the mid had not crossed. At the champion's stop the mid was −4.7, not −12. Re-scored on the mid, P&L was the same or worse (m12, m13, m15), so this is not an edge leak. | **OPEN** (observer). |
| 13 | **Straddle watch built on a frozen CE leg; theta clock /375 on 0DTE** | HIGH for the two straddle books, none for the champion | m14, m15, m24, m26, m28 (frozen leg); m11, m14, m26 (theta) | All 17 spikes said "PE leg carries it". On real prices, 13 of 17 spikes did not happen, and CE spikes existed but could not be seen. Measured decay matches /1440 (residual −1.15 pts/5 min against −1.07 predicted). 8 of 13 spikes existed only because of /375. | Frozen leg FIXED by #4. **/375 OPEN** (owner decision O-3). |
| 14 | **300-s "settling" and regime reset after every gap** (`guard.py:35`, `regime.py:69-74`, `engine_main.py:327`) | MEDIUM (spike, momentum and random books; regime labels). The champion is not affected (m04). | m03, m04, m15, m20, m23, m24 (6) | Blackout + settling covered 54.7 of 86.5 min. straddle_spike had 11 of 15 spikes tainted. premium_momentum never fired after 09:59. Regime read WARMING 62–65 % of the session and 100 % after 10:15. | **Mostly removed** by D-097 (no false gaps). Scaling settle and regime reset to the length of the gap is **OPEN**. |
| 15 | **Band re-centred on the pre-open indicative index** (`feed_breeze.maybe_recenter`) | LOW | m17, m18 (2) | 09:00:04 to 23350, then back at 09:07. 16 dead strikes stayed subscribed all day: 102,316 packets, 9.9 % of L1 load. | **FIXED** D-104 (in session only, 30-s hold). Unsubscribing is **OPEN**. |
| 16 | **No exchange-time data health on the dashboard; verdict text unmapped; "data gap" class mixed blackout with taint** | HIGH (the owner could not see it) | m21, m28 (2); m02, m17 asked for the same observer | A 0.1–2.1 s "age" and a green dot all morning on a 66-h-old price. A check on ltt freshness would have fired at 09:16:00 and has 0 false alarms on HEAD (m28). | **FIXED, partially**, by D-103 and the diagnostics class split (section 6). |
| 17 | **Replay depended on `--speed` and CPU load** | MEDIUM (trust in replays) | m25 (1) | 0.1/0.3/0.5 s steps: 09:59:18 PE; 1.0 s: no trade; 2.0 s: a different trade (10:30:14 CE). | **FIXED** D-105 (`38231c2`). |
| 18 | **random_entry loses slots during blocks** | LOW (control sample size) | m15 (1) | The 10:44:32 slot was lost inside blackout plus settle. The book was blocked 47 % of the window. | **FIXED** in `f84b94a` (deferral; older pending slots are recorded as skipped). |
| 19 | **Spike and momentum books ignored the 0DTE cut-off** | LOW (afternoon) | m26 (1) | From code: a 0DTE leg opened after 15:00 is flattened on the next step. | **FIXED** `9a9dde9` (`paper.py:95-100`). |

**Disagreements, and how the evidence settles them**

- **"The guard is the biggest blocker" (m04, m20, m30) against "synchrony is" (m05, m07, m21, m28).** Both are right, on different measures. By *time*, the guard and taint blocked 55.6 % of the window. By *opportunity*, every moment when the push arrived on clean data failed on S (m21: 53 of 53 near-misses). Fixing the guard opens time; it does not raise S.
- **"The 09:44 trade exists only because of pre-open seeding" (m17) against "session-only scales add trades" (m06, m16, m19, m30).** m17 ran a domino started at 09:15 *without* a volume fast start: the opening burst then seeds the baseline high and S stays low. m19 and m30 ran a version whose baseline is seeded at 0, which is lenient. Neither version is what was committed (session-only, plus a 1/n fast start seeded from positive volume). The lead replayed the **committed** domino on today's tape. The 09:44 trade is still there (09:44:18, S 0.54) and 09:59:19 is added. m17's risk did not materialise. m18's observation (scales *smaller* at 09:20) is a different time point: 75 min of flat pre-market zeros dominate at 09:20, while the inflation shows from 09:25 to 10:30. Everyone agrees the effect fades by about 10:30.
- **Did the hotfix double the futures gaps (m15, m23) or not (m27, m30)?** The 17ef498 hotfix dropped whole packets, so `recv_ns` was not refreshed: 151–153 gaps. HEAD 8b52c99 drops no whole packets: back to the raw 79 (m30: 25.3 % blackout with HEAD against 24.5 % live). Moot after D-097.
- **What did the champion's trade really cost?** See section 3. The −9.6-pt estimates from delta (m12, m21) were labelled HYPOTHESIS. The tape prices replace them.
- **Is synchrony blocking winners?** No member found evidence that it does. Synchrony-rejected candidates went 7 TARGET / 10 STOP, with a median option return at +15 min of −4.7 % (m22). Relaxing S entirely gives about 20 more entries, with a 40 % hit rate and −80 futures pts (m21). Re-priced, futures_only is 9/19 winners, all of the profit coming from one trade (m15). m05 found +5.2 pts of 60-s follow-through when S without volume ≥ 0.5, against −0.3 otherwise. That is one morning and about 42 bursts: suggestive, not proof.

---

## 3. Why the one trade showed 112.2 → 112.2

**What happened**

- At 09:00:25 Breeze replayed Friday's last quote for 23050 CE: ltp 112.2, bid/ask 111.3/112.3, cumulative volume (ttq) 305,082,635, last-trade time (ltt) Friday 15:40.
- The old guard dropped any packet whose ttq was lower than the held one. Today's ttq starts near zero, so it rejected 7,952 of the next 7,953 packets. The row stayed at Friday's quote all morning.
- Depth packets for that contract kept arriving (2,956 of them). Each one rewrote the row's receive time, so the engine saw a quote 0.1 s old.

**The trade**

- 09:44:11 entry: the trigger was real (z 2.19, S 0.577, 10 pts since onset; reproduced offline by m04, m06 and m19). The champion bought 13 lots at **112.2**.
- The real market at that second was last print **132.15**, bid/ask 132.15/132.45. The print 0.1 s earlier was 130.5, with bid/ask 131.7/132.0.
- 09:44:34.911 exit: the futures stop was 23145.0 − 12 = 23133.0. A single print at 23131.8 hit it while bid/ask was 23131.3/23144.3, so the mid was 23137.8, only −4.7. The next print was 23142.0. The real CE was **126.25** (bid/ask 125.9/126.25). The engine booked 112.2 again, so P&L = 0.

**The real result**

| | Entry | Exit | Points | % |
|---|---|---|---|---|
| Recorded | 112.2 | 112.2 | 0.00 | 0.0 % |
| Real, last print at the trigger second (m02, m13, m15, m22, m27) | 132.15 | 126.25 | **−5.90** | **−4.5 %** |
| Real, executable (ask in, bid out) (m13) | 132.45 | 125.9 | −6.55 | −4.9 % |
| Real, print just before the second (m11, m17, m29) | 130.5 | 125.7 | −4.80 | −3.7 % |

- **In rupees:** about −₹4,200 at the 11 lots the true price would have bought from ₹1 lakh (m15: −₹4,219). The 13 lots sized on 112.2 overstated exposure by about 18 %.
- **The stop was right to fire:** the futures then fell −42.5 pts within 10 minutes (m12).
- **The setup:** futures_only had entered the same episode at 09:41:12 with S 0.04. S reached 0.58 three minutes later, near the local top.
- **Not a one-off:** all 13 trades on 23050 CE across the books were 112.2 → 112.2. In every book, all 18 CE trades were at frozen prices (22950 CE at 182.0, 23000 CE at 144.0).

---

## 4. Why so few trades

### (a) Data bugs

| Bug | Effect on the champion today | Effect elsewhere |
|---|---|---|
| Frozen CE quotes (#4) and the depth age mask (#5) | **0 trades lost or added.** z and S read futures and stocks, which the old guard accepted at 99.6–99.9 % (m30, m21). | All CE prices and P&L wrong. IV garbage. PE strikes wrong. Straddle books one-sided. Learning evidence corrupt. With the other fixes in, the garbage IV would have blocked the 09:59 trigger (m30). |
| Hotfix 1-s jitter drops (#6) | Not live today: the hotfix was committed at 10:57, after the tape ends. | Would have doubled futures gaps tomorrow. Superseded. |
| Delivery lag after 10:10 (#8) | It lengthens futures silences, so it feeds #1. It also makes z late and distorted (correlation 0.60). Any trigger after 10:10 was on a move 5–10 s old. | Paper fills priced 4–12 s late. |

### (b) Computation bugs

| Bug | What it blocked |
|---|---|
| 3-s futures-only guard (#1) | 1,225–1,312 s of 5,190 s (24–25 %). |
| Taint through any gap (#2) | A further 1,479–1,660 s (28.5–32 %). Together with #1: 55.6 % of the window in "data gap". |
| Pre-open-trained scales (#7) | About 33 % of qualifying moments until about 10:00. |

### (c) The frozen rule itself

| What happened, 09:25–10:51 (86.5 min) | Value |
|---|---|
| Time with futures \|z\| ≥ 2 in the episode's direction | ≈ 174 s (3.4 %) |
| Median S at those moments | 0.15–0.17 |
| Share of impulse seconds with S ≥ 0.5 | 5–9 % |
| Episodes reaching z ≥ 2 | 31 of 33 |
| … of which ever reach S ≥ 0.5 at a z ≥ 2 second | 5 |
| … of which are not LATE | 3 |
| Candidates where the basket gap (Mb − Mf) was negative, i.e. futures led the basket | 31 of 31 |
| L* | Bound once, correctly: the 09:26–09:27 crash was 102–127 pts in against a ~30-pt budget. |
| IV cap | 0 blocks on correct prices. |

The binding piece is the volume test inside S. It is not one of the four frozen numbers, but it is part of how S is defined.

### Counterfactual trigger counts, same tape, 09:25–10:51

| Configuration | Champion triggers | Source |
|---|---|---|
| Live, as run (old feed, old guard, old taint, old scales) | **1** (09:44:11, fake price) | live books |
| Correct prices only (8b52c99), everything else as coded | 1 | m30 |
| + guard on whole feed (D-097-like, futures 8, 10 or 15 s: identical) | 2 (adds 10:30:38 DN) | m30 |
| + session-only baselines (D-099-like) | 2 (adds 09:59:19 DN) | m30 |
| + taint only at birth (D-098) alone | 1 | m30 |
| All three (m30's implementation) | **3**: 09:44:11 UP, 09:59:19 DN, 10:30:38 DN | m30 |
| Old domino, STALE_S = 10, taint fixed (10 Hz) | 3: 09:44:11, 09:55:13, 10:30:36, plus a knife-edge 09:29:00 | m04 |
| **Lead replay of the COMMITTED code (D-097 + D-098 + D-099 with fast start), correct prices, IV cap applied** | **3**: 09:44:18 UP (S 0.54), 09:59:19 DN (S 0.55), 10:30:38 DN (S 0.56). IV rise −0.6 / +0.7 / 0.0, so no cap blocks. | team leader, `scratchpad/lead/run_head.py` (m30's harness on HEAD `apex/`) |
| Committed code but the old 3-s guard | 2 (09:44:18, 09:59:19) | team leader |
| One gate relaxed at a time on the decision tape: m\* 0 → +0; s\* 0.5 → 0.4 +1; L\* +0; IV cap +0; L\* and IV together +1 (09:26, 102 pts in); **S removed: +20** | — | m21 |
| **`m2.0_s0.5_novol` (D-100), committed code** | **17** in 86.5 min (lead replay); 17 (m30) | team leader, m30 |
| futures_only control (S not used) | 19 trades live | live books |

**Outcomes, futures path, crude 12-pt trailing proxy (1-s sampling).** These count wins, not money:

- Committed champion: 09:44 −18.2, 09:59 −12.2, 10:30 +20.0. Two losers out of 3.
- On m04's first-touch measure, 09:55 and 10:30 both reached +12 first.
- novol: 3 winners out of 16 closed, −72.5 futures pts (lead replay). m30: 4 winners, 12 losers.
- S removed (futures_only): 8 TARGET / 12 STOP, −80.3 futures pts (m21).

**What the frozen rule allows on a day like today:** about one qualifying, not-late moment per 30 minutes of clean data, i.e. **2–3 per morning, at most**. Today, with the data and computation bugs fixed, it allowed 3 in 86.5 minutes. The trigger sampling is knife-edge: S and z flip within a second. So ±1 trigger depends on the exact sampling instant (m25: 0.1 s and 1.0 s steps give different trades).

---

## 5. What works on real data

- **Packet parsing is right field by field.** Every index cross-checks against an exact identity on 1.28 M packets: ttv = ttq·avg, chg against close, and OI against the REST chain 97 % exact. Routing by packet length (21 or 23 fields) has 0 collisions and 0 unknown tokens (m01, m02, m07, m16).
- **HEAD feed (8b52c99) is correct.** 0 whole packets dropped. The table equals the latest packet on all but 24 of 637,330 option packets. No ttq backward steps after 09:16. Option quote age p50 0.5 s, p99 3.2 s. The exchange-age health check gives 0 false alarms (m01, m27, m28, m30).
- **The trigger arithmetic is right.** z, S, σ15, `ago(15)` (exactly 15.000 s), episodes and the lateness check reproduce the live decision tape to a median |ΔS| of 0.000 and |Δz| of 0.01–0.02 (m05, m06, m08, m09, m16, m19, m21).
- **The basket is right.** All 14 heavyweights tick and their prices match NSE; the weights reproduce the spot index (slope 0.959, correlation 0.946). S is normalised by the tracked weight with a live price, 61.36, so 0.5 is reachable (m05, m16).
- **Futures σ** learns only in session and never collapses (m06, m09, m30).
- **Exits fire exactly on the futures path.** STOP/TRAIL times reproduce within 0.0–0.2 s on all 34 unique trades (m12, m13, m15). PE prices were right to the paisa all day.
- **Contract choice on correct data:** an in-band contract 100 % of the time, delta 0.65–0.75, spread 0.2–0.45. A 0DTE contract is a sensible instrument for a 12-pt futures stop (m11, m26).
- **Expiry calendar:** holidays, the 20 Oct shift, the 15:40 roll and the 0DTE flags are all correct (m26).
- **On clean data, IV and greeks are consistent:** CE and PE IV agree to 0.24 vol. The O-1 interpolated IV tracks the nearest-strike IV (m10, m11).
- **Registry re-centres** never move ids or reset state. Positions follow keys (m18, m19).
- **The engine loop is fast:** 4.7 ms median, 34 ms p99, against a 100 ms budget. No engine pauses and no bad prints (m20).
- **The bad-print check, the engine-pause check and O-4** (exits allowed during resume) behaved correctly (m03, m04, m13).
- **The exchange-stamp observers (`trade_age_in/out`, C-18)** are the reason the contamination could be identified exactly after the fact (m29).
- **The live variant books form a working counterfactual system.** Their fires match the tape-derived counterfactuals one for one (m21).

---

## 6. Do the committed fixes do what the members asked?

| Fix | What the members asked | What the diff does | Verdict |
|---|---|---|---|
| **D-095/096** `8b52c99` `feed_core.py:186-212, 246` | m02: field-by-field ordering, never drop the bid/ask, no ttq ordering. m01, m07, m16, m20, m23: ttq or two-clock rule. m02, m11, m13, m17, m18, m28: depth must not refresh quote age. | Drops a packet only if it is stamped on an earlier trading day. Price fields advance unless ≥ 2 s older (`:186`). Book fields are always the newest. ttq never steps back except on a reset (< 20 %). Depth calls `table.end(i, r["recv_ns"][i])` (`:246`). | **Correct.** Verified on the tape by m01, m27 and m30. Residual (m28 F6, LOW): when `px_ok` is false, `table.end(i, recv_ns)` (`:212`) still marks the row fresh while its price is held. It is rare (1,220 packets, 95 % with the same LTP) and the exchange-age checks cover it. The regression tests m01 and m02 asked for (22700 PE tick/snapshot pair, 23200 CE 09:15:00 Friday-ttq packet, Friday ltt with ttq 0) are worth confirming in `tests/test_core.py`. |
| **D-097** `8a1838d` `guard.py:28-29, 54-55`; `engine_main.py:314-316`; `config.py:162` | m03, m04, m20, m27, m30: feed-alive test on any packet (3 s) plus a futures allowance of 8–15 s. m03: exits on the same test. | `feed_age` = newest `recv_ns` on any row. Blackout if > 3 s, or if the future > 10 s. `EXIT_FUT_STALE_S` = 10. | **Correct.** On today's tape it gives 0 blackouts (the largest futures silence was 7.4 s). **Side effect nobody should miss:** the 3-s rule was the only thing that incidentally caught the 10:10+ lag. The guard is now fully blind to delivery lag (m04 F3, m17 F2, m20 F2). D-103 *shows* the lag but does not gate on it. On a lagging day the engine will now trade on 5–12-s-old prices. → OPEN item E1. |
| **D-098** `8a1838d` `engine_main.py:340-346` | m04, m08, m21, m30: taint only if the onset (or its impulse window) is inside a gap; m08 alternatively re-anchor. | The taint is decided once, on the first step that sees the episode: `gap = guard.on`. The guard is still on through the 20-s resume, so "born in resume" is covered. `domino.update` runs after `guard.update` (`:317`, `:328`), so the order is right. | **Correct.** It changes nothing today once D-097 is in (no gaps), and it protects real-outage days. Not done: m08's re-anchoring of `fut0` after a long real gap (LOW). |
| **D-099** `8a1838d` + `9a9dde9` `domino.py:89-120`, `market.py:48-50` | m05, m06, m07, m16, m17, m18, m19, m25, m30: gate the stock σ and volume on `in_session`; warm-up from 09:15. m19 F2: skip the first 15 s. m19 F3: do not seed the baseline with 0; use a fast start. m19 F4: ttq ≤ 0 → NaN. **m17's warning:** a clean 09:15 seeding can make the opening burst set the baseline high and remove trades. | All of the above are implemented: `session_start_s` (`:90`), 15-s skip (`:96`, `:99`), a 1/n fast start seeded from dv > 0 (`:116-120`), and ttq ≤ 0 → NaN (`market.py:49`). | **Correct, and verified on the committed code by the lead replay:** 3 champion triggers with D-097/098, including the 09:44 trade. m17's warning did not materialise with the fast start. Two residuals. (1) After a **mid-session restart** `warm` is False for 10 min, and `act_ok` is then all-True: the champion runs *without* the volume test for 10 minutes after any restart. The behaviour still depends on start time, as m25 F5 and m17 F4.3 warned. → E7. (2) `vol_n` also counts dv = 0 samples before the first positive one. Negligible. Also, the futures σ fast start still weights 09:15:15–09:20 heavily (m06 F3: it needs r15 ≥ 19.4 pts at 09:25 rather than 15.7). This is not addressed. LOW, because SUPPRESS_UNTIL hides most of it. |
| **D-100** `8a1838d` `config.py`, `domino.py` `sync_novol`, `paper.py _sync` | m05, m06, m07, m16, m30: pre-register an S-without-volume book; m05/m06 also a median-baseline or act-1.0 book; m07 per-stock `act` in decision records. | `m2.0_s0.5_novol` uses the same four numbers. THESIS-VOID uses the same S definition (consistent). | **Correct, as far as it goes.** The median-baseline and `act ≥ 1.0` variants were not added, and `act` per tile is not written to the decision or episode records (m07 F5, m21 F5). Adding a variant changes the rule-set hash, as expected. |
| **D-101** `b4bdd92` `engine/defects.py`, `learning.py`, `ledger.py`, `diagnostics.py` | m29: a 600-s exchange-age quote-defect flag; a common quarantine window for every book; a declared-window file; ledger `opt_age0`/`opt_defect`. | m29's patch applied verbatim (only the D-number in its comments changed: D-097 → D-101). | **Correct.** It needs the **owner action** in section 7 (O-1). Not done: m29 F6 (code version on trades) and F7 (automatic window from a feed-health observer when no trade hit the defect). |
| **D-102** `9a9dde9` `engine_main.py:459-464, 535-541`; `config IV_LEG_MAX_AGE_S = 30` | m10: legs fresher than about 5 s by ltt/L1 time; an `iv_valid` flag; a forward sanity bound of about 20–25 pts against futures; log "IV UNKNOWN" when the cap is skipped. m11: tighten the 150-pt parity bound. m21: drop legs ≥ 15 s. m24: liveness by ltt. m02/m11/m13/m17: refuse contracts with a previous-session ltt. | Legs whose **receive** time is older than 30 s are excluded from the forward and IV. Any contract whose ltt is before 09:00 today gets `age = 9e9`, so every entry and exit gate treats it as stale. | **Incomplete.** (1) The cap still **fails open**: `paper.py:204-205` skips it silently when `iv_rise` is None. With legs now filtered, None becomes more likely, and nothing logs it. (2) `greeks.py:111` still accepts a forward 150 pts off. (3) 30 s is loose against today's p99 of 3.2 s, and receive time is what was fooled this morning. After D-096 this is acceptable, but it is not what m10 asked for. (4) No same-day freeze check by ltt ("ltt > 60 s old while the book is live", m02 F5, m13 F1). → E3. |
| **D-103** `9a9dde9` `engine_main.py:488-517`, `app.js renderHealth` | m28: `fresh60` per side **limited to ATM ±250**; a frozen list (LTP unchanged ≥ 60 s while spot moved ≥ 15); quote-vs-depth mismatch; drop counters; lag p50/p90 per packet; HEALTH events on the event tape; RED/AMBER levels; leg badges; optionally pause entries. | Shows `ce_live`/`pe_live` over **all** this-week options; hero contracts with no trade for **> 300 s**; lag from the **last** spot packet only. Display only. | **Partial.** It would have flagged this morning (CE live about 0 %). Gaps: (1) the full ±12-strike band includes deep-ITM strikes that may not trade every minute, so the "calls x %" can read low on a healthy day. That is a HYPOTHESIS, unmeasured; m28's tested design used ATM ±250. (2) Frozen at 300 s is 5× slower than m28's 60-s rule. (3) No HEALTH events in `events_*.jsonl`, so tomorrow's tape cannot prove or refute the lag hypothesis after the fact. (4) A single-sample lag is noisy. (5) No entry effect. That is fine as designed, but see E1. |
| **D-104** `9a9dde9` `feed_breeze.py:612-634` | m17, m18: no re-centre before 09:15 (or 09:08), plus hysteresis; unsubscribe strikes that leave the band; depth for heroes around the engine's ATM (m18 F3). | Session-only plus a 30-s hold. | **Correct for the trigger cause.** Unsubscribe and hero depth are **OPEN** (E9). |
| **Spike/momentum 0DTE cut-off** `9a9dde9` `paper.py:95-100` | m26 F2 | `spike_leg` (used by both books, `:116`, `:118`) refuses w0 legs after 14:45 on expiry day. | **Correct.** The entry evaluator still returns "fire" and the contract step then refuses it. Cosmetic. |
| **Diagnostics class split + verdict text** `9a9dde9` `diagnostics.py:56`, `app.js humanReason` | m21 F1/F5, m28 F4/F5 | "episode born in gap" is a separate class; both DATA GAP texts are mapped. | **Correct.** Still missing: run-summary lines with max S, σ15 and the L threshold on the tape (m21 F5); z printed with 2 decimals (m21 F5.4, m03 F5). |
| **D-105** `38231c2` `engine_main.py:971-994`, `feed_replay.py:121-192` | m25 F1, F2, F6: lock-step on a 0.1-s virtual grid. | The feed publishes boundaries and waits for the engine's ack. The engine steps once per boundary. Falls back to free-running after 30 s with no ack, and logs it. | **Correct.** It also fixes the clock standing still between records (F6) and the virtual-time ENGINE_PAUSE false alarms (F2). Still OPEN: the code hash in tape meta (F4; `_git_short()` returns None on the owner's PC), `replace_retry` in `install_registry` (F7), and learning from a partial replay day (F8). |
| **D-106** `f84b94a` `feed_breeze.py:184-207, 468-469` | m17 F1, m20 F2: no thread per message; a lag meter; move recording off the hot path; unsubscribe. | engineio MESSAGE packets are dispatched synchronously in the read loop. | **Plausible, unverified.** The cause of the lag is a HYPOTHESIS. m20 measured total feed CPU at < 2 % of a core, and Breeze-side conflation is not ruled out. A handler that ever blocks (lock, recorder queue, antivirus) now stalls the socket read and the ping/pong. Proof needs a per-second lag meter **recorded on the tape** (E1, E2). The decision log marks it "FIXED (verify live)", which is the honest status. |
| **random_entry deferral** `f84b94a` `paper.py:269-277` | m15 F3 | A missed slot fires at the next allowed moment. When several are pending, only the latest fires and the rest are recorded as skipped. | **Correct.** Note: after a mid-day restart, every past unfired slot is "due" at once, so the latest fires immediately and the others are skipped. That is acceptable, but it puts a control entry right after every restart. |

**No fix contradicts a member's warning.** m19's warnings on D-099 (the first 15 s, the zero-seeded baseline, ttq 0) were all applied. m17's warning about clean seeding was checked on the committed code and did not materialise. m23's warning about the hotfix doubling gaps is void under 8b52c99 plus D-097.

---

## 7. Still open

### Engineering (no owner decision needed; none of these touch m\*, s\*, L\*, d\* or the IV cap)

| # | Item | Members | Where | Why it matters |
|---|---|---|---|---|
| E1 | **Lag meter on the tape, and a lag guard.** Per-second p50/p90 of recv − ltt on the NIFTY index (subtract the ~0.15-s clock offset) in the ctrl block and the recorder meta. Log it as `HEALTH` events. Entry blackout when p50 > 2–3 s, pre-registered as a guard constant. | m04, m17, m20, m28 | `feed_core.HotStats`, `guard.py`, `engine_main.data_health` | D-097 removed the only incidental protection. Without the meter on the tape, D-106 cannot be proven. |
| E2 | **Verify D-106 live.** Compare tomorrow's lag profile with today's (median 0.4–0.8 s before 10:05, 2–7.6 s after). If the lag persists, move recording out of process, unsubscribe dead strikes, and record CPU %. | m17, m20 | `feed_breeze.py` | The cause is still a hypothesis. |
| E3 | **IV cap must not fail silently.** Log "IV UNKNOWN" when `iv_rise` is None, and record it on the decision tape. Tighten the parity bound to ~25 pts against futures − basis. Optionally use an ltt-based leg freshness. | m10, m11, m21, m24 | `paper.py:204-205`, `greeks.py:111`, `engine_main.py:459-464` | Today the cap ran on garbage without anyone knowing. Next time it may not run at all without anyone knowing. |
| E4 | **Stop and fill observers:** a would-have exit on the futures mid and on the exit-side quote; `fut_spread_in/out`; `ret_pct_exec` (ask in, bid out); `ltp_minus_mid`. | m01, m12, m13, m15, m22 | `paper.py` exit observers | 29 of 34 stops fired on bounce prints. The evidence needs this context. Do **not** change d\*. |
| E5 | **Theta clock /375 on 0DTE** (O-3, measured): wall-clock decay matches /1440; /375 created 8 of 13 spikes. | m11, m14, m26 | `greeks.py:91`, `straddle_watch.py:190` | Owner decision O-3 (below). |
| E6 | **Regime reset and 300-s settle after any gap:** reset only after gaps > 15 s (or real feed silence); scale settling to the length of the gap. | m03, m04, m15, m20, m23, m24 | `engine_main.py:327`, `regime.py:69-74`, `guard.py:35` | Much rarer now that the false gaps are gone. Still disproportionate on a real short outage. |
| E7 | **Restart dependence:** persist the stock scales and volume baselines with the books, or seed them deterministically. Today a mid-session restart runs the champion **without the volume test for 10 minutes** (`warm` False → `act_ok` all True). | m06, m17, m25 | `domino.py` act_ok / warm | Same rule, different behaviour depending on restart time. |
| E8 | **Straddle evidence reads the wrong strike after a roll:** store (K, leg) in the pending record. | m14 | `straddle_watch.py:311-321` | 5 of 13 evidence records today were wrong. |
| E9 | **Unsubscribe strikes that leave the band; depth for the heroes around the engine's ATM; depth for next-week ATM ±1 on expiry afternoons** (the BOOK exit never fires on week-1 positions). | m17, m18, m26 | `feed_breeze.py:408-414` | 9.9 % wasted load. A blind BOOK-exit variant after 13:00 on expiry day. |
| E10 | **0DTE IV cap on expiry days:** add an `iv_rise_w1` observer. After 13:00 the cap measures the expiry the book no longer buys. | m10, m26 | `engine_main.py:463`, `paper.py:204` | 0DTE IV moves 0.49 vol per 10 pts (next week: 0.02), so on expiry days the cap acts as a ~30-pt "late" rule. Variant decision → O-5. |
| E11 | **Code hash on the tape and on every trade:** a sha1 of the `apex/*.py` sources, plus why `_git_short()` returns None on the owner's PC. | m25, m29 | `feed_core.py:254-316`, `paper.py` | The boundary between the frozen morning and the fixed afternoon had to be declared by hand. |
| E12 | **Decision tape fields:** σ15, the L threshold, `gap_on`, per-tile `act`/`z_i`, and run summaries (max S, max z, S at max z). Print z to 2 decimals. | m07, m21, m03 | `engine_main.py:770-791` (now around 831) | Five "impulse z 2.0 < 2.0" lines (z = 1.96–1.99) misled the owner. |
| E13 | **maybe_arm chimes during blackout / for tainted episodes.** | m04 | `engine_main.py:419` | The ARMED chime at 10:30:42 promised a trade that could not happen. |
| E14 | **Episode mechanics** (observers only): the quiet-end rule is almost never reached (once all session), so 30 of 34 episodes ended on reversal; type is FORMING at 29 of 31 candidates; first-mover ties; a z ≥ 2 reversal tick opens no episode. | m08, m24 | `domino.py:163-198` | The episode advisor's screen is near-vacuous; this is not a trade blocker. |
| E15 | **Ledger and learning hygiene:** end-of-day re-labeller from the tape; `fired_fut`/`fired_px` on TAKEN rows; no candidates before 09:15; skip `learn()` on a partial replay day; `replace_retry` in replay. | m22, m25 | `ledger.py`, `engine_main.py:930`, `feed_replay.py:57` | 19 of 31 rows were followed through gaps. |
| E16 | **Small items:** `ago()` tolerance (m19 F5); log `last_torn` (m19 F6); key the stock scales by symbol, not position (m06 F6); VIX poll retry (m20 F5); `save_books` fsync off the loop (m20 F6); the 2027 holiday list (m26 F9); w0/w1 refresh if the feed outlives the day (m26 F8); DTE counted in trading days (m26 F5); `<` vs `<=` session edges (m17 F8, m27 F5); weights estimates (m16 F4). | various | | LOW |

### Owner decisions (each with a neutral recommendation)

| # | Decision | Options | Recommendation |
|---|---|---|---|
| **O-1** | **Declare 19 Oct's defect window tonight**, in `data/learning/defects.json`, before `end_day` runs. Leave the engine running until 15:41 so `end_day` runs (m27 F4). | `"from": "09:15:00", "to": <time the engine was restarted on ≥ 8b52c99>`; if it was never restarted, `"15:40:00"`. | Do it. D-101's automatic window (09:15–10:42:56) catches the frozen trades, but not the polluted IV, advisors and contract choice outside it. Neither the tape nor the logs record the restart time. |
| **O-2** | **The volume test inside S** (`ACTIVITY_MIN` 1.2 × an EW mean of 15-s volume) | (a) keep it; (b) watch `novol` (D-100); (c) also register `act ≥ 1.0` and/or a median-baseline book. | Keep the champion frozen. Run (b), and preferably (c) too, for ≥ 10–15 sessions. Today the volume test turned about 17 triggers into 3. The 17 were mostly losers on the futures path (3 of 16 winners). No member found evidence that the test blocks winners. |
| **O-3** | **Theta clock on 0DTE** (/375 or /1440) | (a) adopt /1440 as a bug fix, since T is calendar time; (b) a pre-registered `straddle_spike_0dte1440` book. | The measurement favours /1440: the model straddle matched to 0.3 pts at 09:20 and 10:45. Either option is defensible. It does not affect the champion. |
| **O-4** | **D-021 vs code after 14:45 on expiry day**: code buys next-week contracts 14:45–15:29; the decision log and docstring say "no entries". | (a) enforce no entry; (b) correct the docs. | Decide before Tue 27 Oct, the next expiry. |
| **O-5** | **The IV cap on expiry days measures 0DTE IV** | (a) keep it; (b) add an `iv_rise_w1` observer and an `m2.0_s0.5_ivw1` variant. | (b), as an observer first. On clean data the cap blocked 0 triggers today, but it binds at about 30 pts moved on expiry days. |
| **O-6** | **Expiry anchor for T** (15:30 now; the CAS settlement is about 15:35; the F&O close is 15:40) | Pick one constant and document it. | 15:35 (CAS end) with a 60-s floor, as m26 suggests. This affects only afternoon 0DTE IV and theta. |
| **O-7** | **Exchange-lag entry guard** (E1) | A new pre-registered guard constant. | Adopt after one session of lag-meter data. |
| **O-8** | **Data-health RED pausing entries** (m28) | Display only, or a guard. | Display only until D-103 has been checked for false alarms over several healthy sessions. |
| **O-9** | **Stops on the futures LTP** | Keep d\* on the LTP; observe on the mid. | Keep, and observe (E4). Today the mid-based stops did no better. |
| **O-10** | **Sequential trigger** (z crosses, then S reaches s\* within N s in the same episode) | An observer, as m21 F2 proposes. | Worth registering as an observer only. Futures led the basket at all 31 candidates. |

---

## 8. Will it give trades?

**Yes, but few. On the evidence, few is the correct output of the frozen rule, not a bug.**

| Book | Today, live | Same tape, committed code (lead replay) | Per full day, estimate |
|---|---|---|---|
| **Champion m2.0_s0.5** | 1 (fake price) | **3** (09:44 UP, 09:59 DN, 10:30 DN) | **About 3–9 on a day like today** (m30: 5–12; most members 1–6). **0–2 on a quiet day.** |
| `m2.0_s0.5_novol` (D-100) | did not exist | 17 | roughly 20–50 (same scaling; very uncertain) |
| m1.5_s0.4 / m2.0_s0.4 | 2 each | 4 each | about 6–12 |
| m2.5 books | 0 | 1 | about 1–4 |
| futures_only control | 19 | 19 (S not used) | about 15–55 (m15: 15–25) |

**The uncertainty is large.**

- **Small sample.** Three events in 86.5 minutes give a Poisson 95 % interval of 0.6–8.8 for the morning.
- **Extrapolating to a full day.** The rest of today's tape was quieter; the futures volume fell from 72–230k to 11–20k per 5 min. A damped factor of about 2.9× gives the range above.
- **Knife-edge triggers.** S and z flip within a second, so a given trigger appears or disappears with the sampling instant (m25). D-105 makes replays deterministic. Live, the same knife edge remains.
- **Not a typical day.** This morning was an expiry day with a 200-pt range, very large for 15-s statistics.

**Will the trades make money?** Nothing today says so.

- The champion's 3 triggers on the committed code: 2 losers and 1 winner on the futures path.
- Every candidate group is a coin flip (n = 23, median option return at +15 min negative).
- The novol book trades 6× more, mostly at a loss today.
- The SPRT needs 30 trades. At about 3–9 a day that is about 4–10 sessions before the champion can be judged.

**What has to hold for this estimate:**

- the feed delivers without the 10:10 lag (D-106, E1);
- the owner files the defect window tonight (O-1);
- the engine runs the committed code from before 09:15, so the warm-up, baselines and quarantine behave as replayed (E7).

If the lag returns, z goes stale again, and with D-097 nothing blocks entries on stale data. That is the first thing to watch on tomorrow's health line.

---

*Lead replay reproducibility:* `/tmp/claude-0/-home-claude/a63e9fa2-7e12-5819-bed7-d06bfece2a8a/scratchpad/lead/run_head.py` and `detail.py`.
They use m30's 1-s harness and pre-applied tape (`work_m30/pass1.npz`, HEAD feed) with the repo's committed `apex/` (Domino and guard
constants as of `f84b94a`). The guard is simulated at 10 Hz from packet arrival times. Taint is decided at birth. The IV cap uses correct-feed ATM IV. Exits use a crude
12-pt trailing proxy on futures LTP, for win/loss counts only. Its limits: 1-s sampling, which can miss sub-second S peaks, and no option P&L.
