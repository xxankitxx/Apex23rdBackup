# R19. Statistics and overfitting audit (13 Nov 2026)

Lens: owner point 3. Why the rules work on some days and fail on others, how much of the +10.92 lakh is real, and a
reusable test harness for every other agent's ideas.

## Findings first

1. **95.6 % of the +10.92 lakh comes from in-sample days.** The seven days the c20 parameters were fitted on
   (19 to 28 Oct) gave 87.1 %. 26 and 27 Oct alone gave 72.6 %. The days after c20_9x was frozen (30 Oct onward,
   9 days) gave 10.6 %.
2. **Honest forward expectancy is about +6 % to +13 % a day, and the median day is a small loss.** On the 9 days
   after the c20_9x freeze the Conductor averaged +12.8 % a day (90 % interval −7.8 to +36.0), its geometric day
   was +6.5 % (−11.3 to +28.6), and its median day was −4.0 %. There is about a 1 in 5 chance that the true mean
   day is zero or worse. The in-sample figure (+64.3 % a day) overstates it about 5 to 10 times.
3. **After allowing for the number of books and rules tried, no pool book's edge is proven.** Deflated Sharpe
   ratio of the Conductor with 107 books tried: 0.007 on all 17 days, 0.073 on the 9 days after the freeze (a
   pass needs 0.95). Romano-Wolf adjusted p over all 99 active books: 0.36 to 0.54 for the pool books on 17 days,
   0.83 to 0.99 after the freeze. The best of all 99 books (t28_ts) has adjusted p 0.20.
4. **What is real: the c20 family is better than the other books, persistently.** Book ranks in 19 Oct to 4 Nov and
   5 to 12 Nov correlate (Spearman 0.65, p < 0.001). The ten best early books stayed in the top 15 % later. The
   probability of backtest overfitting (PBO) for "pick the best book" is low, 0.06. But **picking which c20 sibling
   is a coin flip** (PBO 0.53 on Sharpe within the family).
5. **The pool is one book five times.** Daily returns of the five pool books correlate 0.89 to 1.00. 108 of the
   Conductor's 119 trades are the same trade c20_9x took. That is why the account is flat two-thirds of the day:
   all five books wait for the same trigger.
6. **Why it fails on some days: the day decides, not the rule.** The Conductor's day tracks the median book's day
   (Spearman 0.64, p 0.006). None of day range, day efficiency, VIX, gap or previous-day range does (all p > 0.08).
   On a day when most books lose, the c20 entry loses too. The c20 entry is one fixed pattern. It does not "know"
   what day it is.
7. **The right tail shrank out of sample.** Conductor trades before 30 Oct: 53 % won, mean +6.7 %, 90th percentile
   +40.8 %. After: 60 trades, 48 % won, mean +2.3 %, median −0.6 %, 90th percentile +19.6 %. After the freeze
   the top 10 % of trades carry all of the growth; the other 90 % lose money together.
8. **Entry filters learned on these days kill the next big day.** A filter re-fitted every day on all earlier days
   (rolling walk-forward) found nothing better than "take everything" for ER60 or VIX. For day range it chose
   "range < 213": it saved 4 Nov (+26.7 points) and then cost 6 Nov its whole +100.2 %.
9. **Registered rule R-019 cannot change the Conductor as written.** It blocks c20_9y trades, but a sibling
   (c20_9s, 9v, 9x) takes the same trigger seconds later. Conductor trades 35 → 35 on the test days, P&L unchanged.
10. **Defect found: the pool books have no hold photographs.** `apex/engine/council/__init__.py:158-164` updates
    last / peak / worst for a held council position but never calls `weather5.hold_tick` (`apex/engine/paper.py:1461`
    does for every other book). All 1,058 c20 trades, the Conductor's and RAW's have empty `h60_*` to `h1800_*`.
    So no exit rule for the books that trade can be tested from the trade table today.
11. **How long until the live record can prove anything:** at the post-freeze mean and spread, about 43 trading days
    for a simple t of 2, and about 127 days on compounded (log) growth.

## Teardown (what the code does in my area, and where it fails)

| Where | What it does | Where it fails |
|---|---|---|
| `apex/conductor/account_sim.py:44-97` | walks the pool books' trades by trigger time; the first while flat is taken; all-in lots = floor(capital / (premium × 65)) (line 78) | Correct. My harness reproduces it to the rupee: 119 trades, 63 won, +10,92,458 (`work/R19/s02_verify.py`) |
| `apex/engine/conductor.py:95-98` `priority_key` | same-tick priority: standing, then `ret_per_trade`, then book order | `ret_per_trade` in `apex/rules/pool.json` is stated as "discovery days (in-sample)". So c20_9y (12.09) wins every tie: 95 of 119 Conductor trades come from c20_9y. Picking 9y over 9x was an in-sample choice (PBO within family 0.53) |
| `apex/rules/pool.json` | five c20 books, unrestricted, standing low | near copies (corr 0.89 to 1.00); no second entry pattern, so no cover on straight-line days (docs/54) |
| `apex/rules/register.json` R-019, R-020 | family vote shadow rules on single books | the vote is checked on one book; siblings re-take the same trigger, so the Conductor never sees it (finding 9). To mean anything it must block the trigger cluster |
| `apex/engine/council/__init__.py:158-164` | updates held council position fields every second | no `hold_tick`, so no `weather_hold`; exit research on the pool books is blind (finding 10) |
| docs/28 §6 windows | first window 30 restricted trades or 15 days | for the Conductor itself, 15 days gives t ≈ 1.2 at today's spread: the window can pass or fail on luck. A day-level sign flip on 9 days cannot reach p < 0.05 unless 8 of 9 days agree |
| The search history | 5 champions in 7 sessions (19-28 Oct), a 30-member kit team on 7 days, a 20-member panel, a 10-agent team with 871 rules on 59 books, 20 registered rules, 107 books | each round chose on the same in-sample days. Counting them, the effective number of trials is at least about 1,000 |

## Evidence

All returns are in % of the day's 1 lakh (all-in, compounding within the day). Data: `trades_all_books.parquet`
(p44, pool on every day), Conductor rebuilt by my harness, identical to docs/54. Scripts and outputs in
`D:\ApexOptions\data\research\13nov\work\R19\` (`s03_stats.py`, `s03_out.json`, `s03_out_daymatrix.csv`,
`s04_days.py`, `s04_out.json`, `s07_am_pm.py`).

### How much is in sample

| Group of days | Days | Sum of day % | Share of total | Mean day | Median day | Losing days |
|---|---|---|---|---|---|---|
| c20 kit fitted (19-28 Oct) | 7 | +952.0 | 87.1 % | +136.0 | +48.1 | 0 |
| 29 Oct (seen before the 9x freeze) | 1 | +24.8 | 2.3 % | +24.8 | +24.8 | 0 |
| 30 Oct - 6 Nov (after 9x freeze, inside pool choice) | 6 | +67.4 | 6.2 % | +11.2 | −5.7 | 4 |
| 9-12 Nov (live forward) | 3 | +48.2 | 4.4 % | +16.1 | +9.0 | 1 |

Best day 48.7 % of the total, best two 72.6 %, best three 81.8 %.

### Forward expectancy per day (block bootstrap over days, 20,000 draws)

| Sample | Days | Mean day (90 % interval) | Geometric day (90 %) | Median day | P(mean ≤ 0) |
|---|---|---|---|---|---|
| all 17 days, block 1 | 17 | +64.3 (+17.9, +123.1) | +36.2 (+11.7, +71.3) | +24.8 | 0.001 |
| all 17 days, block 3 | 17 | +64.3 (+12.2, +137.9) | +36.2 (+6.5, +82.9) | +24.8 | 0.004 |
| all but 26-27 Oct, block 2 | 15 | +20.0 (+4.6, +35.0) | +15.2 (+0.1, +30.8) | +21.8 | 0.017 |
| **after 9x freeze, block 1** | 9 | **+12.8 (−7.8, +36.0)** | **+6.5 (−11.3, +28.6)** | **−4.0** | **0.175** |
| after 9x freeze, block 2 | 9 | +12.8 (−9.2, +37.4) | +6.5 (−12.8, +30.3) | −4.0 | 0.187 |
| live 3 days | 3 | +16.1 (+0.4, +31.8) | +14.4 | +9.0 | 0.039 (3 days only) |

Plan on the post-freeze row: about +₹6,500 a day geometric, +₹12,800 a day on average, with a typical day slightly
negative and a few big days carrying the result.

### Deflated Sharpe ratio (Bailey and López de Prado 2014)

Daily Sharpe, skew and kurtosis of each series; the expected best Sharpe of N lucky books from the cross-book
spread of Sharpe (variance 0.094 over 99 active books, mean pair correlation 0.25, effective N = ρ + (1 − ρ) N).
Expected best lucky Sharpe: N 5 → 0.32, N 20 → 0.55, N 107 → 0.75, N 978 → 0.97. A pass needs DSR ≥ 0.95.

| Series | Window | Daily Sharpe | Skew | DSR N=5 | N=20 | N=107 | N=978 |
|---|---|---|---|---|---|---|---|
| Conductor | 17 days | 0.47 | 2.6 | 0.89 | 0.25 | 0.007 | 0.000 |
| Conductor | after freeze (9) | 0.30 | 0.9 | 0.48 | 0.22 | 0.073 | 0.016 |
| c20_9y | after freeze | 0.42 | 1.0 | 0.63 | 0.33 | 0.122 | 0.027 |
| c20_9s | after freeze | 0.33 | 0.6 | 0.51 | 0.25 | 0.095 | 0.023 |
| c20_9v | after freeze | 0.36 | 0.6 | 0.55 | 0.29 | 0.117 | 0.031 |
| c20_9x | after freeze | 0.28 | 0.8 | 0.44 | 0.20 | 0.069 | 0.015 |
| c20_9t | after freeze | 0.23 | −0.5 | 0.40 | 0.20 | 0.080 | 0.023 |

### Probability each pool book's edge is luck

| Book | 17-day sign flip p | After freeze p | 5 test days p | Beats median book after freeze (days of 9), p | RW adjusted p, 17 days | RW adjusted p, after freeze | 1 − DSR (N=107, after freeze) |
|---|---|---|---|---|---|---|---|
| c20_9y | 0.002 | 0.135 | 0.250 | 5, 0.113 | 0.363 | 0.834 | 0.88 |
| c20_9s | 0.003 | 0.184 | 0.125 | 6, 0.191 | 0.414 | 0.935 | 0.91 |
| c20_9v | 0.003 | 0.162 | 0.062 | 6, 0.168 | 0.432 | 0.897 | 0.88 |
| c20_9x | 0.005 | 0.236 | 0.125 | 5, 0.250 | 0.484 | 0.973 | 0.93 |
| c20_9t | 0.022 | 0.250 | 0.031 | 5, 0.391 | 0.537 | 0.989 | 0.92 |
| Conductor | 0.005 | 0.203 | 0.156 | 5, 0.227 | n/a | n/a | 0.93 |

Read across: on all 17 days each book looks clearly real (p ≤ 0.02), but those days are where the books were found.
Out of sample, and after counting the other books, the chance that each edge is luck is high (0.8 to 0.99).
Trade returns are hardly clustered by day (intraclass correlation 0.01 to 0.07), so 119 trades are worth about 113
independent ones; the weakness is the number of days, not the trades.

### Book persistence and overfitting probability

| Test | Result |
|---|---|
| Spearman of book mean day, 19 Oct-4 Nov vs 5-12 Nov (99 books) | 0.65, p < 0.001 |
| Same, split at the 9x freeze | 0.60, p < 0.001 |
| Ten best early books, mean day later | +26.2 % vs +10.0 % for all books |
| PBO (CSCV, 8 blocks, 70 splits), all books, mean day | 0.06 |
| PBO, all books, Sharpe | 0.40 |
| PBO, c20 family (9 books), mean day / Sharpe | 0.04 / 0.53 |
| Pool book rank early → later | 9y 2 → 13, 9s 4 → 12, 9v 5 → 6, 9x 7 → 15, 9t 25 → 45 |

### Why the rules fail on some days (Spearman over 17 days against the Conductor's day %)

| Day descriptor | ρ | p |
|---|---|---|
| median book's day % | **+0.64** | **0.006** |
| VIX at the first trigger | +0.43 | 0.086 |
| previous day range | +0.28 | 0.28 |
| day range (max of range so far) | +0.26 | 0.31 |
| day efficiency (last) | −0.18 | 0.48 |
| median ER60 | −0.06 | 0.82 |
| gap | 0.00 | 0.99 |

Loss days (30 Oct, 3 Nov, 4 Nov, 5 Nov, 12 Nov) are the days when the median book also lost or made nothing.
No single weather item separates them on 17 days.

### Harness tests (each counted in the ledger)

| Idea | Window | Conductor trades | Conductor strike | Sum of day % | Losing days | p (pre-declared) | Verdict |
|---|---|---|---|---|---|---|---|
| Mornings only (trigger before 12:00), all pool books | discovery 12 days | 84 → 43 | 54 → 58 % | +949.9 → +420.4 | 3 → 2 | cluster shuffle 0.23 | |
| | test 5 days | 35 → 19 | 51 → 53 % | +142.5 → +44.7 | 2 → 1 | 0.79 | REJECT |
| R-019 family vote (agree_same ≥ 7), c20_9y only | discovery (in sample) | 84 → 84 | 54 → 55 % | +949.9 → +963.3 | 3 → 3 | 0.28 | passes all tests by the letter |
| | test 5 days | 35 → 35 | 51 → 51 % | +142.5 → +142.5 | 2 → 2 | 1.00 | REJECT (book strike 48 → 50 %, n 20) |
| Exit at 5 min if below −5 % (t28_gap, a book with hold marks) | test 5 days | 34 → 35 | 50 → 46 % | +105.6 → +84.8 | 2 → 3 | 1.00 | REJECT (shows the exit path works) |
| Stand down after noon if the morning's all-book trades lost | 17 days | | | | | ρ −0.01, p 0.97 | REJECT (one pre-declared test) |
| Rolling re-fit, ER60 / VIX / day range lines (36 trials) | 9 days after freeze | | | +115.6 → +115.6 / +115.6 / +42.1 | 5 → 5 / 5 / 4 | 1.00 / 1.00 / 0.75 | none |

Variants tried by me in total: 3 harness ideas plus a pool exit rule that touched no trade (no hold marks), 36
rolling lines, 1 noon rule, plus the descriptive statistics. Nothing I tested is claimed to add profit.

## Ideas

| # | Idea | Mechanism | Test result | How to build | Risk |
|---|---|---|---|---|---|
| 1 | **Honest-number tile** on the dashboard and in the nightly report | show the post-freeze bootstrap: mean, geometric and median day with 90 % intervals, P(mean ≤ 0), days still needed; recomputed every evening from forward days only | measurement, not an edge | display only: run `s03_stats.py` logic nightly on forward days (no engine change) | none; it may disappoint, which is the point |
| 2 | **Every idea goes through the harness and the ledger** | one pre-declared p per idea, Bonferroni or Benjamini-Hochberg across the ledger count; in-sample windows labelled | process; demonstrated on 3 ideas | `work/R19/harness.py` now; move to `apex/conductor/` after review | slows promotion, by design |
| 3 | **Rules on the trigger cluster, not on one book** | a family vote or veto must block every sibling's copy of the same trigger, or the Conductor just takes the copy | R-019 as written: 0 change on test days | new register rule with family = c20 trigger cluster; restricted Conductor in replay | same in-sample evidence (12 of 12 losses was found on 14 in-sample days) |
| 4 | **Diversify the pool with a low-correlation family** | the five books are one book; a second entry pattern (day correlation with c20_9x < 0.5 and positive excess over the median book after its own freeze date) would fill the flat two-thirds of the day | untested | rank candidates from `s03_out_daymatrix.csv`; test each with the harness `--books X` on its own out-of-sample days; shadow pool | adding a weak family lowers the account; must pass on its own forward days |
| 5 | **No new entry filters from the 19 Oct-6 Nov days** | filters cut the rare big days that carry the account | rolling re-fit: nothing beats "take all"; day range filter cost 6 Nov +100 % | policy | missing a real filter; acceptable at this sample |
| 6 | **Fix the council hold photograph** | call `_w5.hold_tick(book.pos, ctx, o)` beside `council/__init__.py:162-164` | defect; until then `phaseB_holdmarks_council.py` rebuilds bid marks from ds_v2 | engine change (owner's call; observer only, wrapped in try like `paper.py:1460-1463`); measure step time first | tiny step cost; must not touch exits |
| 7 | **Sequential live scoring** of the Conductor against the median book | e-value / SPRT on daily differences, decide when evidence is enough, never peek-and-stop on a t-test | untested; needs about 43 days (mean) to 127 days (log growth) at today's spread | add to `apex/conductor/score.py` nightly | none |
| 8 | **Priority from forward figures only** | `ret_per_trade` in pool.json is in-sample; replace with each book's post-freeze return per trade as days accrue | untested; low impact (siblings are copies) | dated new pool rows, as docs/28 allows | none |

## Phase B scripts (ready to run after 15:30, same rules: py -3.13, lowprio, one at a time, under 3 minutes)

| Script | What it does |
|---|---|
| `D:\ApexOptions\data\research\13nov\work\R19\phaseB_holdmarks_council.py` | rebuilds bid-based hold marks (60 to 1800 s: return, peak, worst) for every pool-book trade from ds_v2, one part at a time; writes `pool_holdmarks.parquet`. Then exit rules on the pool run with `harness.py --exit "hb300_ret < -6" --mark 300 --holdfile ...pool_holdmarks.parquet`. 12 Nov is not in ds_v2. Check the CE/PE and bid/ask axis order against ds2.py before running |
| `D:\ApexOptions\data\research\13nov\work\R19\phaseB_rolling.py` | rolling re-fit walk-forward for a list of factors with Benjamini-Hochberg; small runs are quick (3 factors in 4 s); long factor lists after the close |
| `D:\ApexOptions\data\research\13nov\work\R19\harness.py` | the evaluation harness (below) |

### Harness usage for Phase B agents

```
py -3.13 D:\ApexOptions\data\research\13nov\work\R19\harness.py --filter "wx_er60 >= 0.35"
py -3.13 ...\harness.py --filter "wx_agree_same >= 7" --apply-to c20_9y
py -3.13 ...\harness.py --exit "h300_gain_pct < -5" --mark 300 --books t28_gap --no-conductor
```

It prints the per-day walk-forward table (discovery 19 Oct-4 Nov, test 5-12 Nov, `--split` to change), the
Conductor all-in account with and without the rule, the docs/28 §2 tests on each window (strike rate and return
against the membership luck line, positive without best trade and best day, ahead of the free version without
them, keeps two-thirds of the top 10 % trades, worst day no worse, sample), a trigger-cluster mask shuffle through
the Conductor (sibling copies of one trigger move together; shuffling single trades would always leave a copy and
make every filter look bad), a daily sign flip, and the ledger count with a Bonferroni-adjusted p. Caveats in its
header: an entry filter on saved trades cannot create the later trades a freed book would take; an exit at a mark
uses the LTP gain minus half the entry spread (or the bid when a holdfile is given).

## Sources

* Bailey and López de Prado, The Deflated Sharpe Ratio (2014): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
* Bailey, Borwein, López de Prado and Zhu, The Probability of Backtest Overfitting (2015): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
* Romano and Wolf, stepwise multiple testing (Econometrica 2005); White's Reality Check (Econometrica 2000); Hansen SPA (2005); implemented in the arch package: https://github.com/bashtage/arch
* pypbo (PBO, PSR, DSR in Python): https://github.com/esvhd/pypbo
* sharpebench (PSR, DSR, PBO): https://pypi.org/project/sharpebench/
* fynance overfit module (CSCV PBO): https://fynance.readthedocs.io/en/master/_modules/fynance/research/overfit.html
