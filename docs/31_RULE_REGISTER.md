# Rule register (frozen rules)

The machine-readable register is `apex/rules/register.json`; this page is the same content in words. It
implements docs/28 §6 ("Writing a rule", "Frozen") and §16a (the seeded register).

## How a rule is frozen

* **Written in full before any test day:** the family it applies to, the exact condition with its formula and
  number, the restricted book and the free book it is compared against, the freeze date, the reason.
* **Evidence of the date:** the git commit that added the rule to `register.json`.
* **Never edited.** A change (a different number, a different family, a different formula) is a **new rule** with
  a new id and a new date, and its test-day count starts from zero.
* **Test days** are the trading days from `first_test_day` on. Days before it are where the idea came from, not
  evidence.
* **When the condition is read:** at the trigger second (the last completed virtual second before the trigger),
  on data that had *arrived* by then (receive time, `recv_ns`), never on exchange time.
* **Scored** at the Conductor build and every evening after: the restricted book against the free book, with the
  seven tests of docs/28 §2. A restricted book is a full replay of the free book with the condition switched on, not
  a filter of its trades (blocking one trade can free the book for a later one).

## Factor rules (8 Nov)

A rule the register states as `factor`, `op` (`>=` or `<`) and `line`, the form the weather cards produce
(`register.propose`), is checked by `apex/engine/rules.py` straight from `register.json`: `weather_trig.<factor>
<op> <line>` on the photograph taken at the trigger second; a missing value blocks the entry (as R-002's unknown trend
does); an indicator factor `field=value` is 1 when the field equals the value. The Conductor's pool
(`apex/rules/pool.json`) pairs a book with such a rule; a restricted book can carry one in `rules=(...)` too.

## Shared definitions

| Term | Definition |
|---|---|
| expiry day / normal day | the nearest weekly Nifty expiry is today (the engine's `dte0`) / it is not |
| trade direction `d` | +1 for a call, −1 for a put |
| trusted 1-Hz spot | the engine's in-session Nifty spot samples (fresh, the D-132 guard applied), as fed to `spot_hist` |
| **ER60**, **DIR60** | `m_k` = the last spot sample at or before `t − 60·k` s, `k = 0…60`. ER60 = \|m₀ − m₆₀\| / Σₖ₌₁…₆₀ \|mₖ₋₁ − mₖ\|; DIR60 = sign(m₀ − m₆₀). Undefined (the rule blocks the entry) if a mark has no sample within 5 s before it, if the sum is 0, or before 10:15:00 |
| **BREADTH_DIR** | for each heavyweight stock `i` (weight `wn` > 0, a price now and 300 s ago): cᵢ = ltpᵢ(t) / ltpᵢ(t − 300 s) − 1. BREADTH_DIR = (weight of stocks with sign(cᵢ) = d) / (weight of stocks with a finite cᵢ); unchanged stocks count in the denominator only. Undefined (blocks) with fewer than 2 stocks |
| family | per trade, from what it carries: `ep_type`, council trades split into COUNCIL-EXP / COUNCIL-NORM by their signal, × day type |

## The five hand-written rules (frozen 7 Nov 2026, test days from Mon 9 Nov)

| Id | Rule | Family | Exact condition | Restricted vs free |
|---|---|---|---|---|
| **R-001** | Spot retest on expiry days: entries end 11:30 | SPOT-RETEST × expiry day | on an expiry day, no entry with a trigger at or after 11:30:00 | spot_dc12_t12_1130 vs spot_dc12_t12. **Already running since 21 Oct**: kept at its original date (21 Oct), not re-dated |
| **R-002** | Normal days: trend followers only after a trending last hour | SPOT-BREAKOUT, SPOT-RETEST, SPOT-RETEST-FILL, SPOT-PULLBACK, ORB, the domino types (CO-FIRST, FORMING, BASKET-LED, FUTURES-LED), FOLLOW, COUNCIL-NORM; normal days | enter only if **ER60 ≥ 0.35 and DIR60 = d**; otherwise (also before 10:15, or ER60 undefined) no entry | each family's representative with the condition vs without |
| **R-003** | Breakout and impulse families only with breadth ≥ 60 % | SPOT-BREAKOUT, ORB, SPOT-PULLBACK, the domino types; both day types | enter only if **BREADTH_DIR ≥ 0.60** | each family's representative with the condition vs without |
| **R-004** | Council books on normal days: mornings only | COUNCIL-NORM × normal day | no council entry with a trigger at or after **12:00:00** | c20_9x with the condition vs c20_9x (reported for every council book) |
| **R-005** | Long-hold families: no entry in the last 45 minutes | families whose **median** hold on the live record 19 Oct – 6 Nov exceeds 15 min: **ORB only** (24.9 min, 14 trades) | no entry with a trigger at or after **14:30:00** (LAST_ENTRY 15:15 − 45 min) | spot_orb45 with the condition vs spot_orb45 |

Notes:

* The two thresholds in R-002 and R-003 (efficiency 0.35, breadth 60 %) are the regime's own DIRECTIONAL thresholds
  (`apex/engine/regime.py`), used unchanged rather than picked now. R-003 measures breadth in the **trade's**
  direction; the regime measures it in the futures' 5-minute direction.
* **R-005 membership was measured from hold times only** (no win or loss was looked at), and fixed today. On those
  numbers the 45-min pullback (median 14.0 min) and the council normal-day books (11.7 min) do *not* qualify, so
  they are not in it. R-005 is close to empty so far: the ORB book made no entry after 14:30 between 19 Oct and 6
  Nov. A wider version would be a new rule.
* Representatives (docs/28 §16a, the least-gated member of each family): spot_pb45, spot_dc12_t12,
  spot_dc12_t12_first, spot_orb45, m1.5_s0.4, gap3_s0.4, straddle_spike, fade_switch, c20_9x; t28_fwd is its own
  family.

## The restricted books (registered 7 Nov, trading as shadows from Mon 9 Nov)

**Owner, 7 Nov: they run live, at the same time as every other book.** Measured cost about +6 % per engine
step on the test rig.

Each is the family's representative with **one** rule switched on (`config.RESTRICTED`, parameter `rules`), traded
beside its free book; name = representative + `_r00N`. The rule is checked at the entry, after the contract is
chosen, on the weather photograph (`apex/engine/rules.py`); a refusal skips the setup like every other entry veto.
The same check runs for council books (`council.Adapter`) and for the missed-signal recorder's twins.

| Rule | Restricted books (14) |
|---|---|
| R-002 | spot_dc12_t12_r002, spot_dc12_t12_first_r002, spot_pb45_r002, spot_orb45_r002, m1.5_s0.4_r002, gap3_s0.4_r002, fade_switch_r002, c20_9x_r002 |
| R-003 | spot_dc12_t12_first_r003, spot_orb45_r003, m1.5_s0.4_r003, gap3_s0.4_r003 (spot_pb45_r003 off 8 Nov: a pullback entry never has 60 % breadth our way; 14-day replay 0 of 57 entries) |
| R-004 | c20_9x_r004 |
| R-005 | spot_orb45_r005 |

The rule applies only to the entry patterns in its family: fade_switch_r002 is restricted on its FOLLOW entries
only (FADE is not a trend follower); spot_dc12_t12_r002 on both its retest and breakout entries. R-001 and the
seeded rules already have their restricted books (the variants named in the table below).

## Seeded rules (existing restricted-vs-free pairs, at their original dates)

| Id | Rule (as coded in the variant) | Restricted vs free | Frozen | First test day |
|---|---|---|---|---|
| R-006 | spot dual: no trend entry in range mode (`range_gate`) | spot_dual_rg vs spot_dual | 22 Oct | 23 Oct |
| R-007 | pullback: no impulse measured across a data gap (`pb_gap_block_s=120`) | t28_gap vs lvl_trail_re | 28 Oct | 29 Oct |
| R-008 | pullback: the impulse must take ≥ 20 min (`pb_min_impulse_s=1200`) | t28_dur20 vs lvl_trail_re | 28 Oct | 29 Oct |
| R-009 | domino: trend filter (`trend`) | m2.0_s0.5_trend vs m2.0_s0.5 | 19 Oct | 21 Oct |
| R-010 | domino: no volume term (`novol`) | m2.0_s0.5_novol vs m2.0_s0.5 | 19 Oct | 19 Oct |
| R-011 | spot dual levels: edge gate (`gt_min`) | edge_gate_only vs spot_dual_lvl | 27 Oct | 28 Oct |
| R-012 | pullback (gap book): skip if the contract's IV fell ≥ 2 % in 15 min | t28_ivfall vs t28_gap | 28 Oct | 29 Oct |
| R-013 | pullback (gap book): skip a late chase into a bid pile | t28_bidpile vs t28_gap | 28 Oct | 29 Oct |
| R-014 | pullback (gap book): veto when the pullback did not cheapen the option | t28_nohigh vs t28_gap | 29 Oct | 30 Oct |
| R-015 | pullback (gap book): +10 % needs more than the 15-min range | t28_req vs t28_gap | 29 Oct | 30 Oct |
| R-016 | pullback (gap book): R-014 and R-015 together | t28_cheap vs t28_gap | 29 Oct | 30 Oct |
| R-017 | council: c20_9x + stale-impulse pullback veto (normal days, 660 s) | c20_9s vs c20_9x | 3 Nov | 4 Nov |
| R-018 | council: c20_9x + IV-rich and OI-wall entry vetoes | c20_9y vs c20_9x | 4 Nov | 5 Nov |

Exit-only pairs (nolock, tt8, mh15, st20, the be/rx chain, c20_9t / 9v / 9e / 9h) are not entry rules; they go to
the exit test (docs/28 §10).

## Scoring (`python -m apex.conductor.score DATA_DIR`)

`apex/conductor/score.py` scores every rule on its own test days (R-002 to R-005 once per restricted book): the
first window (30 restricted trades or 15 trading days, whichever comes later), then a second of the same length;
the seven tests of docs/28 §2 on each; verdict under_test / passed_first_window / full_standing / failed; after a
pass, the e-value watch (switch-off at 20). `--record` writes the changes to `apex/rules/status.jsonl`. Quote
defects, defect windows and closing-auction entries are not evidence.

**7 Nov, on the live record:** no window is complete yet (the oldest pairs have 13 test days). R-001 has 284
restricted trades in 13 days, so its first window completes after Tue 10 Nov.
