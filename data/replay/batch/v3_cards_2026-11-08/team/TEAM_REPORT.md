# The 10-agent rule team — combined report (8–9 Nov 2026)

**Owner's instruction (8 Nov):** "a 10-member team of smart agents which apply rules to different books and make them
only profitable and remove losses completely … all kinds of permutation and combination and every kind of mathematics
… before a book actually triggers … reduce the loss making trades to almost nil."

**Result in one line:** 10 agents, 59 books, 871 rules searched and shuffle-tested (trend, speed, Greeks, IV, order
flow, OI, breadth, time of day, ratios, differences, products, within-day z-scores, direction interactions, 2- and
3-clause ANDs, ORs, regime-conditional rules). **No rule removes any book's losses to near nil.** 12 rules passed the
written standard by the letter; after an independent re-check none is a loss-remover. One observation is honest and
worth a shadow: when a c20 council sibling that is free declines a trigger the rest of the family takes, the trade has
lost 12 of 12 times. Nothing goes into the register on this evidence.

## The standard every agent worked to (`BRIEF.md`)

Discovery = first 10 replayed days (19–30 Oct), holdout = last 4 (3–6 Nov), searched on discovery only. Kept side
≥ 20 trades and profitable on discovery. The same search re-run on ≥ 200 shufflings of the discovery outcomes must beat
the real score in < 5 % of shufflings (p). On holdout the kept side must win at least as often as the book and the
removed side must not be profitable. Fitted-model fields (`hmm_*`, `hk_*`) excluded (docs/34 F02). Toolkit
`rule_lab.py` (here), read-only on the repo; no replays, no engine, no pytest.

## Why the bar is where it is

Every agent found the same thing on every book: a search over ~190 fields × 5–9 lines × pairs finds "35 kept, 80 %
winners, 7 losers" out of 65 trades in RANDOM labels about half the time (shuffle medians 0.40–0.50 on the score).
Rules that look perfect on discovery (t28_ivfall triple: 22 kept, 100 % winners) have p ≈ 0.4. A book with 60–80
trades cannot support a two-clause rule chosen from thousands of candidates; the holdout then shows the kept side
winning less than the book, or losing rupees, in most of them.

## The 12 rules that passed by the letter, and what they are on inspection

| book | rule | discovery kept (n, win, losers) | holdout: book win → kept win, kept ₹, removed ₹ | agent p | my verdict |
|---|---|---|---|---|---|
| c20_9y | `agree_same >= 7` (every earlier council sibling fired) | 40, 78 %, 9 | 56 % → 59 %, +61,678, −2,379 (1 trade) | 0.000 (1-field search) / **0.347 under the full-width search** | honest observation; removes 1 holdout trade; shadow only |
| c20_9y | `agree_same >= 7 AND adv_vetoes_raw >= 2` | 32, 84 %, 5 | 56 % → 62 %, +62,234, −2,935 (2) | 0.03 | same signal plus a clause that removes winners (+1.1 L of discovery P&L lost) |
| c20_9s | `agree_same >= 6` | 45, 69 %, 14 | 50 % → 56 %, +51,454, −29,634 (2) | 0.005 (1-field) / **1.000 full-width** (not even the best single) | the same observation on a book sharing 8 of the 12 flagged triggers with 9y: not an independent confirmation |
| c20_9t | `hwvol_x_futvol_surge < 1.296 AND swing_ahead_over_behind < 0.7953` | 35, 94 %, 2 | 65 % → 70 %, **−7,312**, −3,679 | 0.01 | kept side loses rupees on holdout; derived pair out of ~70 derived features; reject |
| c20_9x_r004 | `opt_opp_q≠DRAIN-FAST AND hw_book_imb_t >= −0.2956 AND oi_other_chg5 >= −43,836` | 24, 96 %, 1 | 42 % → 45 %, **−24,856**, −36,143 | 0.01 | three clauses on 44 trades; kept side loses on holdout; reject |
| spot_dc12_t12_r002 | `opt_lead < 0.0668 AND abs(e_fut_ofi60) >= 4.066` | 27, 78 %, 6 | 38 % → 50 %, **−15,730**, −18,249 | 0.025 | 44 discovery trades, 9 searches tried; kept side loses on holdout; agent itself says "treat as NONE" |
| spot_dc12_t12_first | `oi_net_help5 >= 1.059e5` | 217, 47 %, 116 | 41 % → 42 %, +27,901, −22,662 | 0.02 / **0.063 on my re-run (300 shuffles, 9 lines)** | a tilt on a 38 %-win book, not a loss remover (49 of 84 kept trades lost on holdout) |
| spot_dc12_t12_first_r003 | `oi_net_help5 >= 1.283e5` | 208, 47 %, 111 | 38 % → 38 %, +13,419, −28,906 | 0.005 | same field on the same trades gated by R-003; holdout kept win rate equals the book's |
| edge_breakout | `gaps_today < 6 AND vomma >= 0.00696 AND vix_chg30 < 0.608` | 29, 79 %, 6 | 28 % → 43 %, **−2,298**, −62,384 | 0.045 | kept side 3 W / 4 L on holdout; `gaps_today` is a feed-health counter; reject |
| fade_switch_r002 | `e_fut_imb5 < 0.25 AND range_now >= 191.1` | 181, 63 %, 67 | 47 % → 48 %, +5,203, −37,284 | 0.047 | kept side break-even on holdout (33 of 63 lost); reject |

(Agent 7 listed `spot_dc12_t12_first_r003` twice at two seeds; agent 10 listed its pair twice. 12 entries, 10 distinct rules.)

## Lead A in full — the family vote

`agree_same` (item 67 of the photograph) is the number of books that fired on the same side at this step and the
previous one, counted at the moment the book triggers. The c20 books are evaluated in a fixed order (8x, 9x, 9t, 9v,
9e, 9h, 9s, 9y), so for c20_9y a value of 7 means all seven earlier siblings fired and 6 means exactly one stayed
silent. The siblings differ from c20_9x only in their council member: c20_9t adds the rent trail, c20_9s adds the
stale-impulse pullback veto (660 s).

What the tape shows (`abstain_out.txt`, `busy_out.txt`, all 14 days):

| agree_same at 9y's trigger | trades | winners | which sibling was silent |
|---|---|---|---|
| 7 (all fired) | 57 | 41 | — |
| 6 (one silent) | 12 | **0** | c20_9t on 6 (19 Oct ×4, 27 Oct ×2), c20_9s on 6 (21, 22, 29 ×2 Oct, 2 and 4 Nov) |
| 5 (two silent) | 2 | 2 | 9t + 9h on 27 Oct 13:08 (+99,099); 8x + 9t on 2 Nov |
| 1 | 1 | 1 | the family was busy in an earlier trade |

The silent sibling was **free, not busy**, in 31 of 40 cases checked (the other 9 were holding an earlier trade), so
this is a genuine veto by 9t or 9s, not an artefact of occupancy. The whole family lost on each of the 12 trades
(c20_9e and c20_9h sometimes escaped through their own exits).

Why it is not a register rule yet:

- **Luck under the honest search.** With agree_same as the only field, 12 of 12 losers has an exact probability of
  0.0003 on 9y and the 10-of-10 replication on 9s has 0.006. But the field was found by searching the whole photograph
  on 9y; under that search the shuffle p is 0.347 (random labels give a split this good one time in three). The 9s
  replication shares 8 of its 12 flagged triggers with 9y, so it is the same 14 days seen twice, not a second sample.
- **Holdout is thin.** On the 4 held-out days the rule removes 1 trade from 9y (−2,379) and 2 from 9s (−29,634, both
  on 3 Nov). It does not touch the other 7–8 holdout losers of either book.
- **It does not reach c20_9x.** 9x is second in the order; its agree_same is 0 or 1 on every trade. The signal exists
  only for the books evaluated after 9s and 9t.
- **It removes 12 of 28 losers at most**, on the book where it is strongest. Not "almost nil".

What it is good for: a **shadow rule** — log, from Monday, every c20_9y / c20_9s trigger with agree_same below the
full count and its outcome. If the 12-of-12 holds for another 15–20 cases live, it becomes a register rule (a yes/no
condition on item 67, already in the photograph) with a real out-of-sample record. Alternatively, the same information
is available directly: c20_9t's and c20_9s's silence IS their council member's veto, so the register could carry
"c20_9y takes a trigger only if c20_9s and c20_9t also fire" as R-019 in shadow.

A related observation (`abstain_out.txt`, bottom): across all 123 family triggers, when all 10 family books (the
8 council books plus 9x_r002 and 9x_r004) took the trade, most books won on 22 of 29; when 7 took it, 0 of 5. This is
the same R-002/R-004 data the 14-day rule verdicts already cover (R-002 removed winners on balance over the 14 days
and cost c20_9x three trading days), so it is noted, not acted on.

## Lead B in full — own-side OI help on spot_dc12_t12_first

`oi_net_help5 >= 1.059e5` keeps 301 of 603 trades over the 14 days (45 % win vs the book's 38 %), on holdout 84 trades
at 42 % (book 41 %), +27,901 against −22,662 removed. Frozen on the parent spot_dc12_t12 it also tilts the right way
(holdout 47 % vs 43 %). My re-run with 300 shuffles and 9 lines gives p = 0.063 against the agent's 0.020 with 200
shuffles and 5 lines: on the edge of luck. It is a tilt on a book that loses 55–62 % of its trades either way; it
removes 50 losers and 33 winners on holdout. Not a candidate for "no losing trade".

## The books with nothing (49 of 59)

Every other book's best rule failed the shuffle test, the holdout, or both. Agents 3, 4, 5, 6, 8 (t28 and lvl_trail
families, spot_dual family, spot_pb45, spot_ft_prem10) found p ≥ 0.05 on every search or holdout kept sides that lost
money; agent 1 on c20_9x / c20_9v / c20_8x, agent 2 on c20_9e / c20_9h / c20_9x_r002 / apex_edge / futures_only,
agent 9 on the edge and premium books, agent 10 on fade_switch likewise. Each agent's `agent_N_report.md` has every
book's card, every search tried and the one-line reason each rule failed; `agent_N_rules.json` carries all 871 rule
objects with their windows and p. `collated_table.md` is the one-table view (best rule per book).

## Near-misses pre-registered for re-test as live days accumulate (NOT for the register now)

| book | rule | why re-test |
|---|---|---|
| t28_mh15 | `vixchg15_over_vix >= -0.00115` | p 0.075; holdout kept 64 % vs 52 %, +29,929 vs −8,664 |
| t28_fill | CE entries after a losing trade today (`is_CE AND prev_win_today < 0.5`) | p 0.08; holdout kept 64 % vs 45 %, removed −24,739 |
| t28_req | `fut_spread >= 2.6 AND oi_own_chg5 < -11,090` | p 0.09, best of 96 t28 rules; removed side still profitable on holdout |
| spot_ft_prem10 | `ep_n_cross < 14 AND chop30 >= 2.31` | p 0.005 on 350 trades but removed side profitable on holdout; `er30 < 0.432 AND breadth_dir < 0.917`; `opt_lead >= 0.0215 OR opt_iv_chg1 >= 0.05` |
| spot_dual family | `abs(e_fut_ofi60) >= 7` | consistent direction across the three siblings, never clears p |
| c20_9y / c20_9s | family vote (above) | shadow from Monday |

## What this means for the owner's aim

The losers of the strong books are not separable from their winners by anything recorded at the trigger second, nor by
any arithmetic on it, at 14 days of tape. The two things that do separate some losers are (a) a sibling council
member's veto and (b) a weak OI tilt on a weak book. The honest route to "no losing trade" on this evidence is not a
filter at the trigger; it is more days of tape so that a rule with a 12-of-12 record can be told from luck, and the
Conductor's photograph is capturing exactly that from Monday.

The pool recommendation stands: the c20 family unrestricted (9y, 9s, 9v, 9x; 9t) with no factor lines; the family
vote as a shadow rule, logged not enforced.

## Files

`BRIEF.md` (the agents' instructions), `rule_lab.py` (shared toolkit), `agent_1..10_report.md` and
`agent_1..10_rules.json`, `collated_table.md` + `collate.py`, `verify_leads.md` + `verify_leads.py` (independent
re-check), `abstain.py` → `abstain_out.txt`, `busy.py` → `busy_out.txt`. Agent working folders (scripts, logs, raw
result JSON) stayed in the session scratchpad.
