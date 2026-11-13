# R04: weather items as entry filters, every item, pairs and triples

Analyst R04, 13 Nov 2026. Lens: owner point 2 (try every weather item and every combination for entries).
Data: `data/research/13nov/trades_all_books.parquet` (20,817 trades, 107 books, 17 days, 524 usable weather fields
after splitting text fields into yes/no values). Discovery days 19 Oct to 4 Nov (12 days), test days 5, 6, 9, 11 and
12 Nov (5 days). Scratch work and every output file: `data/research/13nov/work/R04/`.

## Findings first

1. **No weather entry filter survives honestly.** I searched every weather field at 19 quantile lines, both
   directions, for the Conductor account, the pool books, all 16 book families and all books together. The best
   lines on the discovery days get worse, not better, on the test days. At the exact Conductor account, the 10
   best discovery lines helped on the test days only 1 time in 10. Across all 372 fields, the discovery rank and
   the test result are unrelated (rank correlation -0.06).
2. **More items make it worse.** Pairs and triples (beam search) look far better on discovery and do worse on
   test than single lines, in every group I ran (8 groups). The best Conductor triple keeps a 78% strike rate on
   discovery and gives 50% on test, below the unfiltered 51%.
3. **The statistical "survivors" are a mirage.** False discovery rate control at 10% passed 1,419 field-and-group
   lines. On the test days these survivors improved results LESS often than the lines that failed it (for
   example pool trades: 24% of survivors helped, 33% of non-survivors). The reason: 107 books fire on the same
   market moves at almost the same seconds, so trades are not independent and a shuffle-within-the-day null is
   far too easy to beat. The production nightly search (`apex/conductor/search.py`) has the same weakness, worse.
4. **The R-019/R-020 family vote (agree_same) is the best discovery line and fails on test.** At the account,
   `agree_same >= 7` turns the 5 test days from x2.82 to x2.06 (product of day growth), strike rate 51% to 50%,
   and makes 12 Nov worse (-4.0% to -12.5%). As coded per book it has NO effect at all (see Teardown T1).
5. **The nightly search used as a procedure does not help.** Re-searching every night on all days before and
   trading the next day with the best line: on the 5 test days it was worse on 4 and equal on 1.
6. **One frozen hypothesis for a shadow book, not a rule:** `sign_none_share300 >= 0.0197` (photo item 109, the
   share of futures volume whose buy/sell side could not be told). It passed every bar I set at trade level and
   at the account (test: 60% strike rate vs 51%, 1 losing day vs 2, x5.24 vs x2.82). But I picked it after
   seeing the test days, from about 90 lines that passed a bar that about 1 line in 7 passes by luck. Treat it
   as untested until 13 Nov onwards say otherwise.
7. **Stop looking at:** 14 fields that are empty or constant, and 6 items whose lines hurt far more often than
   they help out of sample (item 31 "Who moved first" is the clearest: 20 helped, 157 hurt).

## Teardown

**T1. A weather rule on one pool book is silently undone by its sister books.** `apex/engine/conductor.py:177-191`:
when flat, the Conductor walks the fired triggers in priority order and drops any whose own rule blocks it; the
next book that fired takes the account. All five c20 books trigger on the same impulse within seconds. So R-019
(only on c20_9y) blocks 9y and c20_9s takes the same trade. Replayed on 5-12 Nov, R-019, R-020 and both together
give exactly the unfiltered account (-5.9, +100.2, +43.2, +9.0, -4.0 %). Any weather gate meant to change the
account must apply to every pool member's trigger, not one book.

**T2. The nightly search's luck test shuffles across days.** `apex/conductor/search.py:283-284` (the shuffle is line 284) permutes outcomes
over all rows of all days (`rng.permutation(len(rows))`). A line that only separates good days from bad days
(range so far, IV level, VIX) then beats luck easily, although with 12 days there is no way to tell it from
chance. The day-fact protection (`DAY_FACTORS`, line 34, at least 5 days each side, line 167) covers only 13 named
fields; `range_now`, `range_vs_pd`, `e_iv_atm`, `atm_iv_day_pos` and many others behave like day facts and are
not in it. I tried the stricter null (shuffle within book and day): it is still far too easy (z-scores up to 36),
because trades overlap.

**T3. The search scores strike-rate difference, not compounded growth** (`search.py:230`, `score = srk - sro`).
All-in compounding makes the account's result depend on which trades are kept in sequence; a line can raise the
strike rate and still lose money at the account (example: `with_vol_share300 < 0.636`, discovery strike rate 61%,
but 9 Nov goes from +43% to -13%). My account-level search (`s2_conductor.py`) re-simulates the exact account.

**T4. Only 7 lines per field** (`search.py:166`, quantiles 0.2 to 0.8) and the nearest-neighbour robustness check
(`search.py:246-251`) are sensible, but the search never holds anything out. A card line becomes a candidate on
in-sample numbers alone; the register then waits for test days. That is the right order, but the card should
also carry a walk-forward score so weak lines never reach the register.

**T5. Missing value = blocked** (`apex/engine/rules.py:128-130`). Correct and conservative. My search uses the
same convention, so every result below includes the cost of missing photos.

## Evidence

Multiple testing, in numbers: single lines: about 6,700 lines x 2 sides per group, 19 groups (about 255,000
tests). Conductor account: 13,428 single lines, 12 beams x 13,428 pairs, 6 x 13,428 triples. Trade-level beams:
8 groups, K = 6 to 10. Permutations: 10 to 1,000 per group (the all-books run only 10; see Phase B).

### E1. The exact Conductor account (five pool books, all-in, one position), 5 test days

Unfiltered rebuild matches docs/54 (base below). Product = the 5 test days' growth multiplied together.

| Gate (chosen on 19 Oct - 4 Nov) | 5 Nov | 6 Nov | 9 Nov | 11 Nov | 12 Nov | trades | strike | losing days | product |
|---|---|---|---|---|---|---|---|---|---|
| none (the live Conductor) | -5.9 | +100.2 | +43.2 | +9.0 | -4.0 | 35 | 51% | 2 | x2.82 |
| best single: agree_same >= 7 | -5.9 | +94.2 | +19.6 | +7.4 | -12.5 | 20 | 50% | 2 | x2.06 |
| 2nd: range_vs_pd < 1.014 | -5.9 | +20.4 | +43.2 | +28.7 | -4.0 | 32 | 53% | 2 | x2.00 |
| 3rd: atm_iv_day_pos < 0.874 | -5.9 | +100.2 | +71.3 | +9.0 | -4.0 | 34 | 53% | 2 | x3.38 |
| with_vol_share300 < 0.636 | -5.9 | +100.2 | -12.6 | +9.0 | -1.9 | 28 | 50% | 3 | x1.76 |
| best pair: agree_same >= 7 and opt_run < 0.495 | -5.9 | +94.2 | +19.1 | +7.4 | -12.5 | 19 | 47% | 2 | x2.05 |
| best triple: vwap_z >= -1.87, with_vol_share300 < 0.637, held_other < 6.6 | 0 | +8.9 | -12.6 | +28.7 | -1.9 | 22 | 50% | 2 | x1.20 |
| R-019, R-020, both (as coded, per book) | -5.9 | +100.2 | +43.2 | +9.0 | -4.0 | 35 | 51% | 2 | x2.82 |

On discovery the same gates looked strong (agree_same: 72% strike rate on 53 trades vs 54% on 84). Permutation
p of the best discovery single at the account: 0.125 (7 permutations; Phase B adds more).

How the discovery ranking carries over (all 372 fields with a valid line at the account):

| Discovery rank | share that helped on test | mean change in test log growth |
|---|---|---|
| top 10 | 10% | -0.33 |
| top 25 | 16% | -0.23 |
| top 100 | 20% | -0.23 |
| all 372 | 29% helped, 55% hurt, 16% no change | |

### E2. Rolling walk-forward of the search itself (Conductor account)

Each day from 28 Oct: search all days before it, freeze the best line, trade that day.

| Day | line chosen | unfiltered % | gated % |
|---|---|---|---|
| 28 Oct | with_vol_share300 < 0.636 | +56.2 | +62.9 |
| 29 Oct | same | +24.8 | +24.8 |
| 30 Oct | agree_same >= 7 | -5.6 | -2.2 |
| 2 Nov | agree_same >= 7 | +41.6 | +40.8 |
| 3 Nov | agree_same >= 7 | -36.3 | -2.4 |
| 4 Nov | agree_same >= 7 | -26.7 | -24.3 |
| 5 Nov | agree_same >= 7 | -5.9 | -5.9 |
| 6 Nov | agree_same >= 7 | +100.2 | +94.2 |
| 9 Nov | agree_same >= 7 | +43.2 | +19.6 |
| 11 Nov | agree_same >= 7 | +9.0 | +7.4 |
| 12 Nov | agree_same >= 7 | -4.0 | -12.5 |

Better on 4 days, worse on 5, equal on 2. All the gain is 3 Nov, one day. On the 5 test days: worse on 4, equal
on 1. Trade-level rolling for the pool trades: 2 days better, 2 worse, 7 untouched (net log growth -0.68); c20
family -1.32; t28 family -9.41 (6 better, 5 worse).

### E3. Trade level: does a "significant" line replicate? (every field's best discovery line, scored on test)

| Group | test trades | FDR survivors | survivors that helped on test | non-survivors that helped |
|---|---|---|---|---|
| pool events (one row per trigger) | 45 | 3 | 0% | 34% |
| pool trades (five books) | 164 | 105 | 24% | 33% |
| c20 family | 319 | 174 | 30% | 29% |
| t28 family | 802 | 222 | 30% | 39% |
| spot_dc12 family | 826 | 135 | 24% | 29% |
| lvl_trail family | 226 | 209 | 19% | 25% |
| m_grid family | 88 | 137 | 32% | 36% |
| spot_dual family | 118 | 90 | 19% | 30% |
| spot_other family | 180 | 40 | 28% | 47% |
| edge family | 78 | 25 | 52% | 37% |
| all books | 6,418 | 210 | 27% | 33% |
| fade, n01 (losing books) | 541, 963 | 49, 18 | 94%, 100% | 91%, 77% |
| n02, n06, p02, p05, s01, s03 | | 0 to 1 each | | |

Fade and n01 "help" with almost any line because they lose money on the test days; dropping any of their trades
helps. That says "switch the book off", not "the weather knows". A line that also helped in both halves of
discovery (19-28 Oct and 29 Oct-4 Nov) did no better on test (pool trades: 24% vs 31%; c20: 23% vs 30%).

Strict out-of-sample bar (test growth up, strike rate up, more test days helped than hurt and at least 2, two
thirds of test big winners kept, at least 30% of trades kept): FDR survivors passed it at 7% (pool trades),
12% (c20), 16% (all); non-survivors at 12%, 10%, 21%. About 90 survivor lines pass it in total, which is the
number luck alone predicts.

### E4. Beam search, pairs and triples (trade level, test days)

| Group | base test strike | single: test strike, growth change | pair | triple |
|---|---|---|---|---|
| pool events | 51% | 50%, -0.26 | 50%, -0.62 | 56%, -0.89 |
| pool trades | 54% | 50%, -3.04 | 49%, -3.28 | 46%, -4.62 |
| c20 family | 53% | 55%, +1.31 | 50%, -5.52 | 45%, -8.35 |
| t28 family | 49% | 48%, -5.58 | 50%, -4.43 | 52%, -2.75 |
| spot_dc12 | 37% | 37%, -2.24 | 37%, -0.39 | 35%, -2.25 |
| lvl_trail | 52% | 41%, -5.79 | 40%, -5.47 | 40%, -5.46 |
| m_grid | 57% | 83%, -1.92 (18 kept) | 51%, -0.33 | 62%, +0.53 |
| all books | 47% | 45%, -29.4 | 47%, -0.92 | 46%, -16.8 |

Growth change = sum of log(1 + return) of kept trades minus all trades. On discovery the pairs and triples raised
the strike rate to 70-87%. Beam permutation p values were 0.02 to 0.5 with few permutations; none matters given
the test results.

### E5. The one frozen hypothesis, R04-A: sign_none_share300 >= 0.0197 at the account

| | trades | strike | sum log growth | losing days | worst day |
|---|---|---|---|---|---|
| Discovery, none | 84 | 54% | 4.21 | 3 | -36.2 |
| Discovery, R04-A | 71 | 56% | 4.60 | 3 | -29.5 |
| Test, none | 35 | 51% | 1.04 (x2.82) | 2 | -5.9 |
| Test, R04-A | 30 | 60% | 1.66 (x5.24) | 1 | -5.9 |

Test days: 5 Nov -5.9 (same), 6 Nov +100.2 (same, all 4 winners kept), 9 Nov +126.2 vs +43.2, 11 Nov +18.6 vs
+9.0, 12 Nov +3.6 vs -4.0. Without its best day (9 Nov) it is still ahead (0.84 vs 0.68). It meets the docs/28
standard on paper. Its 60-second twin (`sign_none_share60`) fails on test, it ranked 110th of 372 at the account
on discovery, and I chose it after seeing the test days. Verdict: untested hypothesis.

### E6. Items that carry no information (stop looking)

Empty or constant on these trades (14 fields): adv_event, adv_quiet, breadth_n, eng_step_gap_s, event, feed_state,
n_hero_stale, or_late, phase=CTS, reconnects, req_cluster_s, req_first, req_retry_n, sync_n.

Out-of-sample record of each item's lines across the 19 groups (a line "acts" when it drops at least one test
trade; overall 38% of acting lines helped):

| Item | lines acting on test | helped | hurt | verdict |
|---|---|---|---|---|
| 31 Who moved first (ep_first=...) | 186 | 20 | 157 | stop: consistently misleads |
| 26 Absorption | 19 | 4 | 12 | stop |
| 85 The leaders | 50 | 11 | 34 | stop |
| 23 Resting value | 39 | 9 | 22 | stop |
| 100 Other books' positions | 70 | 17 | 41 | stop |
| 80 The adverse path | 26 | 6 | 14 | stop |
| 120 Opportunity survival | 0 | 0 | 0 | never changes an entry |
| 128 Research lineage, 65 Direction history, 64 Last trade | 5, 1, 6 | | | too few to judge |
| 32 Basket gap | 17 | 12 | 3 | worth a shadow look |
| 38 Put/call ratio, max pain | 57 | 36 | 16 | worth a shadow look |
| 73 Bar runs | 33 | 21 | 10 | worth a shadow look |

Groups overlap (all books contains every family), so these counts are not independent; treat the last three
rows as leads, not findings. Everything else sits between 25% and 55%, which is what chance gives.

## Ideas

**I1. Make pool rules account-level (fix T1).** Mechanism: a gate on the Conductor's trigger, applied to every
pool member, so a blocked impulse cannot slip through via a sister book. Test: shown above that per-book R-019
has zero effect; account-level gates do change the account. Build: a `pool_gate` list in pool.json read at
`conductor.py:177`, checked before the per-member loop; shadow first. Risk: none by itself; it only makes a rule
mean what it says.

**I2. Do not promote weather entry lines from the nightly search.** Mechanism: with 12 to 17 days, 500 fields and
overlapping trades, the search finds luck. Evidence: E1 to E4. Build: add a walk-forward column to every card
line (rolling, as `s4_rolling.py`), and require the line to help on held-out days at the account, not at the
book. Replace the cross-day shuffle (search.py:284) with a day-block check: a line must help on at least N of the
held-out days, judged in days. Risk: fewer rules, which is the point.

**I3. Shadow book R04-A (sign_none_share300 >= 0.0197, account-level).** Mechanism, guessed: when almost all
futures volume is clearly buyer- or seller-initiated (low "no side" share), the impulse may be one-sided sweeping
that reverses; a normal share of mid-price trades means a two-sided market where the c20 resumption holds.
Untested on fresh days. Build: a shadow Conductor copy with this gate, logged beside the live account; judge on
13 Nov onwards with `phaseB_fresh_days.py` and the docs/28 standard. Risk: selected after seeing the test days;
it may be luck. Never live before 10 fresh days.

**I4. Spend the search effort on holds and exits instead.** Entry filters only choose which c20 impulses to skip;
the account already sits flat two-thirds of the window and 26-27 Oct carry most of the profit. Skipping trades
mostly removes winners. Mechanism and evidence for exits are in R02 and R05. Untested by me.

**I5. Switch-off rules for losing books, not weather filters.** fade and n01 lose on test regardless of the
line. Build: a book-level "off when its own rolling 5-day log growth < 0" shadow rule. Untested.

**I6. Display change (owner point 4).** The weather panel should not present any of these 500 fields as "for" or
"against" an entry; none has shown out-of-sample entry value. If a field is shown, show its walk-forward hit
rate next to it (for example "item 31: 11% helped out of sample"). Untested as a display.

## Phase B scripts (ready, not run; after 15:30 only, lowprio, one at a time)

| Script | What it does | Runtime |
|---|---|---|
| `data/research/13nov/work/R04/phaseB_conductor_null.py` | adds permutations to the account-level null of the best single line (today: 7). Run 10 times with `R04_SEED=1..10 R04_ACCUM=1` | about 3 min each |
| `data/research/13nov/work/R04/phaseB_beam_null.py GROUP` | more beam-null permutations for fam:t28, fam:spot_dc12, fam:c20, pool_trades | about 3 min each |
| `data/research/13nov/work/R04/phaseB_fresh_days.py TABLE.parquet` | judges the frozen candidates (`frozen_candidates.json`: R04-A, R04-B, control) at the account on days after 12 Nov | under 1 min |

All scripts used today, in order: `build_cache.py`, `s1_single.py`, `s2_conductor.py`, `s3_beam.py`,
`s4_rolling.py`, `s5_summary.py`, `s6_replicate.py`, `s7_twowin.py`, `s8_cand.py`, `s9.py`, `s10_items.py`.
Outputs: `out_s*.json` in the same folder.
