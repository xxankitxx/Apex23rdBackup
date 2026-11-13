# R08 Heavyweights by Nifty weight (owner point 5)

Analyst R08, 13 Nov 2026. Scope: how the 14 heavyweight stocks are used today, a weight-adjusted constituent index
with sector sub-indices, lead-lag against the Nifty future at 5 s to 5 min, weighted breadth thrusts, divergences,
and whether any of it separates c20 winners at the trigger. All runs were short and low-priority. Three ds_v2
parts were read (26 Oct, 5 Nov, 9 Nov). The trade table covers all 17 days.

## Findings first

1. **The heavyweights are photographed but never act.** About 70 heavyweight fields go into every trade's photo.
   No rule in the Conductor pool reads any of them. The forecaster screen shows one chip, "Heavyweights rising",
   and that chip is an unweighted count: HINDUNILVR (1.85 %) counts as much as HDFCBANK (10.38 %).
2. **At the trigger, the existing fields do not separate winners.** Across 20,817 trades (107 books) every
   heavyweight field has an AUC between 0.45 and 0.55. On the c20 pool books the AUCs flip between windows. For
   example, 15-min breadth is 0.33 in the early window and 0.64 in the late one. The sector split (bank, IT,
   energy, other) also carries nothing.
3. **There is real lead-lag, but only at 5 to 60 seconds.** The weighted cash basket and the stock-futures basket
   lead the Nifty future by one step at 5 to 10 s. The future closes about 27 % of the cash basket's 10-s lead
   over the next 5 to 10 s. The coefficient was stable in all three leave-one-day-out fits (0.21 to 0.30).
   Out-of-sample R2 is 4 to 8 % at 5 s, 1 to 2 % at 30 s, near 0 at 60 s, and negative at 5 min.
4. **A fixed, unfitted pressure formula P takes a clear short-term stand.** On all three days it fires on 12 to
   17 % of seconds. It is right 65 % of the time at 10 s, 60 to 64 % at 30 s, 59 to 64 % at 60 s, and has no
   edge by 5 min. This is the "short-term probable stand" the owner asked for, and it is honest about its horizon.
5. **For c20 entries the sign is reversed.** When the cash basket is already ahead of the future in the trade's
   direction (domino gap above +1.6 pts), the c20 trade does worse. The future catches up within 10 s (before or
   at the fill), and then the move is spent. A veto on this raises the Conductor's strike rate in both windows
   (0.536 to 0.574 early, 0.514 to 0.583 late) and lifts late return (+154 % to +210 %). It **cuts** early return
   (+987 % to +531 %) because it vetoes the 27 Oct 79.7 % trade. **It does not pass the promotion standard.** It is
   worth running as a shadow book.
6. **Weighted breadth thrusts are real but redundant.** A thrust means 60-s weighted breadth crosses 0.8 from
   below 0.3. It is followed by +1.8 to +2.4 pts over 30 s, right 57 to 61 % of the time. Adding breadth as a
   filter on P adds nothing.
7. **Divergences are too rare to use.** "Future makes a top-decile 60-s move while the cash basket moves the
   other way by 3 pts" happened 0, 3 and 0 times on the three days.

## Teardown (what the code does, and where it fails)

| # | Where | What it does | Problem |
|---|---|---|---|
| T1 | apex/universe.py:15-31, 59 | 14 Nifty heavyweights with factsheet weights. Tracked total is 61.42 %. | TCS and ITC (2.52 each) are capped estimates (line 26-29). The other 38.6 % of the index has no proxy. |
| T2 | apex/engine/weather.py:273-288 `wmove` | spot x sum(w_i/100 x r_i) | This is not normalised by the tracked weight, so it reads about 61 % of an index-equivalent move. gen3.py:142 and forecast_lab/core.py:703 do normalise. The same "basket move" therefore has three different units in three modules, and the photo's wmove cannot be compared with mv (spot move) without dividing by 0.6142. |
| T3 | weather.py:471-476 | Sector masks bank / it / energy / other | "bank" excludes nbfc, so BAJFINANCE lands in "other". forecast_lab/live.py:385 puts nbfc into bank. The two modules disagree on what "banks" means. |
| T4 | weather.py:291-309, 450, 633 | Weighted breadth over 300 s (breadth_dir) | This is a sound weighted measure, but it is too slow. My evidence puts the information at 5-60 s. At c20 triggers the 5-min breadth AUC is 0.47 to 0.55 and flips. |
| T5 | weather4.py:154-211, 385-399 | 1- and 15-min breadth, dispersion, top-3 share, leaders | Photo only. None separates winners in both windows (table E1). |
| T6 | domino.py:150, 161 | Mb = basket 15-s move per 100 % weight, gap = Mb - futures 15-s LTP move | This is **the one heavyweight number that matters at c20 triggers** (finding 5). It is computed every step and photographed as wx_basket_gap, but no rule reads it. |
| T7 | forecast_lab/live.py:428-431 | Feeds heavyweight cash LTP to the forecaster if its age is 30 s or less | 30 s is too stale for a signal that lives at 5-30 s. gen3.py:28 uses 5 s. A 30-s-old HDFCBANK print makes a fake basket lead in hwlead30. Median cash age in ds_v2 is 0.3 to 1.4 s, so 5 s costs almost nothing. |
| T8 | forecast_lab/core.py:677-705 | Cumulative weighted log returns: index, bank, rest | Correctly weighted. |
| T9 | forecast_lab/core.py:719-728 `hw_tail` | `up` = share of stocks higher than 60 s ago | **This is an unweighted count** (`(p1 > p0).mean()`, line 727). |
| T10 | forecast_lab/brain.py:171-184 | Features hw30, hw120, hwlead30, bank120, up60 | The evidence puts the edge in the 10-s cash gap (g10). The brain has only 30-s and 120-s versions. 120-s and bank-minus-rest carried no out-of-sample skill here (table E3, rows "bank_rest"). |
| T11 | forecast_lab/core.py:1575-1576 and static/app.js:1871 | The UI chip "Heavyweights rising" shows `up` as a percentage | It is unweighted (T9), takes no stand, gives no points, and has no horizon. This is the owner's point 4 complaint, for heavyweights. |
| T12 | engine/gen3.py:141-145 (S01, S03), gen2.py n06 | Shadow books that use the baskets | These are thresholds on 30-s windows. S01 uses the stock-futures gap at its 99th percentile, which is rare. None is in the pool. |
| T13 | config.py:436-438; rules.py:60-64 | R-003 "breadth >= 60 %" on restricted books | This is the only heavyweight rule, and it is off for the pullback family because a pullback can never have 5-min breadth with it. That is the same reason the heavyweight photo fields do not help c20. |
| T14 | conductor/search.py:68-75, 126-127 | Heavyweight factor groups 28-35, 83, 84 in the nightly search | They are searchable, but at 5-min horizons, which do not separate (E1). |

## Evidence

### E1. Heavyweight photo fields at the trigger (AUC of win, signed with the trade)

Discovery is 19 Oct to 4 Nov. Test is 5 to 12 Nov. All 107 books: 14,183 / 6,634 trades. Pool books: 379 / 164.
0.5 means no separation.

| Field | All early | All late | Pool early | Pool late |
|---|---|---|---|---|
| wmove10 | 0.485 | 0.517 | 0.462 | 0.601 |
| wmove60 | 0.504 | 0.495 | 0.505 | 0.452 |
| wmove60_bank | 0.494 | 0.486 | 0.476 | 0.451 |
| breadth_dir (5 min) | 0.466 | 0.486 | 0.551 | 0.455 |
| breadth900_dir | 0.477 | 0.485 | **0.334** | **0.640** |
| sync_dir | 0.477 | 0.520 | 0.455 | 0.633 |
| hw_at_ext30 | 0.469 | 0.539 | 0.525 | 0.738 |
| **basket_gap (domino)** | 0.478 | 0.510 | **0.414** | **0.305** |
| div30 (wmove30/0.614 - mv30) | 0.488 | 0.486 | 0.493 | 0.380 |
| bank_z | 0.500 | 0.524 | 0.488 | 0.603 |

Only basket_gap points the same way in both pool windows, and it is below 0.5 in both: a bigger gap with the trade
means more losers. The full table of 43 fields x 2 sets is in work/R08/s03_auc.csv.

### E2. Cross-correlation, future vs weighted baskets (k = +1: the basket's previous step vs the future's current step)

| Step | Day | cash k=-1 | cash k=0 | cash k=+1 | sfut k=+1 |
|---|---|---|---|---|---|
| 5 s | 26 Oct | 0.154 | 0.595 | 0.182 | 0.204 |
| 5 s | 5 Nov | 0.064 | 0.407 | 0.174 | 0.192 |
| 5 s | 9 Nov | 0.097 | 0.444 | 0.148 | 0.216 |
| 10 s | 26 Oct / 5 Nov / 9 Nov | 0.099 / 0.095 / 0.059 | 0.76 / 0.60 / 0.73 | 0.167 / 0.150 / 0.158 | 0.19 / 0.16 / 0.18 |
| 60 s | same | 0.05 / 0.09 / 0.07 | 0.91 / 0.69 / 0.79 | 0.08 / 0.17 / 0.08 | 0.06 / 0.13 / 0.09 |

On all three days the basket leads slightly more than it lags at 5-10 s. The future is a mid price and the cash
price is a last trade, so the cash lead is not a stale-price artefact. If it were, the effect would run the other way.

### E3. Granger-style forecasts of the future's forward move, leave-one-day-out (fit on 2 days, test on the third)

Hit and pts are on the top 10 % of predictions, in the predicted direction.

| Horizon | Model | Test 26 Oct R2 / hit / pts | Test 5 Nov | Test 9 Nov |
|---|---|---|---|---|
| 5 s | own move only | 0.001 / 0.54 / 0.4 | -0.003 / 0.47 / -0.2 | 0.001 / 0.51 / 0.1 |
| 5 s | own + cash gap | 0.053 / 0.71 / 1.8 | 0.036 / 0.62 / 0.8 | 0.057 / 0.67 / 1.7 |
| 5 s | own + sfut gap | 0.076 / 0.72 / 2.0 | 0.045 / 0.66 / 0.8 | 0.066 / 0.69 / 1.8 |
| 10 s | own + all | 0.062 / 0.70 / 2.3 | 0.040 / 0.61 / 1.1 | 0.061 / 0.68 / 2.3 |
| 30 s | own + all | 0.019 / 0.54 / 2.7 | 0.023 / 0.75 / 2.1 | 0.021 / 0.66 / 1.8 |
| 60 s | own + cash | 0.005 / 0.60 / 3.7 | 0.028 / 0.69 / 3.8 | 0.007 / 0.63 / 4.2 |
| 5 min | any | negative on all days | negative | negative |
| any | bank minus rest alone | about 0 / 0.48-0.55 | same | same |

The cash-gap coefficient at 10 s was 0.27, 0.30 and 0.26 in the three fits. The own-move coefficient was 0.09 to 0.11.

### E4. The fixed pressure rule P (no fitting), |P| >= 1.0 pt

| Day | Cover | 10 s hit / pts | 30 s | 60 s | 120 s | 300 s |
|---|---|---|---|---|---|---|
| 26 Oct | 14 % | 0.65 / 1.7 | 0.61 / 2.3 | 0.59 / 2.1 | 0.54 / 2.5 | 0.54 / 3.1 |
| 5 Nov | 12 % | 0.66 / 1.2 | 0.64 / 1.7 | 0.62 / 1.9 | 0.60 / 2.7 | 0.59 / 2.9 |
| 9 Nov | 17 % | 0.65 / 2.1 | 0.63 / 2.6 | 0.64 / 3.3 | 0.56 / 1.7 | 0.54 / 0.6 |

Requiring 60-s weighted breadth of 0.3 or more in the same direction cut coverage by a quarter and did not raise
the hit rate.

### E5. P at c20 pool triggers (3 days, 134 trades), signed with the trade

| P with the trade | n | Strike rate | Mean ret % | Future next 10 s | next 60 s | next 300 s |
|---|---|---|---|---|---|---|
| below -1 | 5 | 1.00 | 61.1 | -7.2 | +27.3 | +91.3 |
| -1 to -0.3 | 23 | 0.78 | 12.0 | -1.7 | +0.5 | +9.9 |
| -0.3 to 0.3 | 27 | 0.52 | 0.2 | +1.6 | -1.3 | +2.3 |
| 0.3 to 1 | 42 | 0.57 | 11.9 | +2.9 | -2.6 | +19.0 |
| above 1 | 37 | 0.46 | -1.1 | +1.8 | -2.5 | -9.5 |

The 10-s catch-up happens as the formula says, and then the c20 move fades. A c20 resumption that the future leads
while cash lags is the better trade. Across all 107 books (4,438 trades) the pattern is flat. This is a c20 effect.
On 17 days the photo's basket_gap (correlation 0.70 with this g10) tells the same story (E6).

### E6. Conductor veto "skip a c20 trigger if domino gap with the trade > +1.6 pts" (all 17 days)

The threshold was chosen on the early window as one of 594 variants (33 fields x 2 sides x 9 quantiles; table in
work/R08/s05_veto.csv). The account was re-run as a one-position greedy sim over the five pool books' own trades.
With no veto that sim reproduces the Conductor exactly (84 + 35 trades, the same daily returns), so a vetoed
trigger correctly lets the next pool trigger in.

| | Early n | Early SR | Early sum of daily % | Early losing days | Late n | Late SR | Late sum % | Late losing days | Late without best day |
|---|---|---|---|---|---|---|---|---|---|
| Conductor (base) | 84 | 0.536 | 987 | 3 | 35 | 0.514 | 154 | 2 | 45 |
| veto gap > 1.0 | 56 | 0.571 | 558 | 2 | 21 | 0.571 | 170 | 1 | 82 |
| **veto gap > 1.6** | 61 | 0.574 | 531 | 3 | 24 | **0.583** | **210** | **1** | **112** |
| veto gap > 3.0 | 70 | 0.557 | 613 | 3 | 29 | 0.517 | 145 | 1 | 46 |

Per test day (base -> veto, day return %): 5 Nov -6.0 -> -6.0; 6 Nov +109.2 -> +98.2; 9 Nov +43.4 -> +95.1;
11 Nov +12.0 -> +12.0; 12 Nov -4.8 -> +10.7. On 9 Nov it vetoed 7 trades (-12.5, -5.2, +7.9, -14.4, -13.5, +7.6,
+3.0). On 12 Nov it vetoed 3 losers.

Across all 17 days the veto was better on 10, worse on 5 (26, 27, 28 Oct, 2 Nov, 6 Nov) and equal on 2. The worst
early day improved (-37.1 % to -28.5 %). The biggest loss is 27 Oct (+542 % to +114 %), because the 79.7 % trade
had a gap of +6.9.

Promotion standard (docs/28 section 2):

| Test | Result |
|---|---|
| Strike rate | Pass in both windows |
| Return | Fail in the early window, pass in the late window |
| Positive without its best trade and best day | Pass |
| Keeps most of the top trades | Kept 10 of the top 12 |
| Worst day no worse | Pass |
| Passes in two windows | Fail |

**Verdict: not promotable. Shadow book only.**

Book-level check: 66 % of books with enough trades did worse after a high gap in the early window, but only 39 % in
the late window. The effect is not universal and belongs to the c20 family.

Multiple testing: 594 variants on 84 discovery trades. The late window has only 35 trades over 5 days, and one
day (9 Nov) carries most of the gain. Treat this as a hypothesis with some support, not as proof.

## Ideas

### I1. A weighted heavyweight pressure P for the forecaster's stand (tested on 3 days; phase B for all)

Formula, computed every second in Nifty points:

```
C10 = F * sum_i w_i [ln p_i(t) - ln p_i(t-10)] / sum_i w_i     cash prints, age <= 5 s at both ends, covered weight >= 70 %
S10 = the same with each stock future's mid (bid+ask)/2
dF10 = F(t) - F(t-10)                                            F = Nifty future mid
P = 0.10*dF10 + 0.27*(C10 - dF10) + 0.10*(S10 - dF10)
Stand: P >= +1.0 -> UP, P <= -1.0 -> DOWN, else no heavyweight stand. Horizon 10-60 s. Never beyond 2 min.
```

- **Mechanism.** The stocks reprice first, and the future closes about a quarter of the gap within seconds. Index
  arbitrage flow and the 14 names' own order flow carry the push.
- **Display.** Replace the "Heavyweights rising" chip (app.js:1871) with a chip that takes a stand. For example:
  "Heavyweights push UP +1.6 pts (next 30 s, right about 62 % of the time)".
- **First-person commentary.** "HDFCBANK and ICICIBANK are 4 points ahead of the future. I expect the future to
  add about 1.5 points in the next half-minute. This is a seconds-scale push. It tells me nothing about the next
  five minutes."
- **Weighted breadth.** Replace `up` in core.py:727 with a weighted share. In the same function, add `pressure`
  and `top_contributors` (w_i x r_i, the top 3) so the commentary can name the stocks.
- **Speed.** Two 14-element dot products per second, which is negligible. Tighten live.py:429 to an age of 5 s or
  less.
- **Risk.** The skill is small in points (1-3 pts of future, which is half that on an ATM option). It must never be
  sold as a 5-minute view. The coefficients come from 3 days.

### I2. Shadow book "c20 pool, futures-led only" (tested, failed promotion, worth a shadow)

- **Rule.** At a c20 trigger, skip if `d * domino.gap > 1.6` (domino.py:161; already computed, no new cost).
- **Build.** A Conductor shadow account with the same pool and one extra yes/no line in the council veto list,
  next to the c20_9y IV and wall vetoes. It needs a replay to confirm. That replay needs the owner's OK, so I have
  not run it.
- **Risk.** It vetoes some big basket-led winners (27 Oct). Before going further, the shadow should show the
  strike-rate gain holding on new days.

### I3. Unify the basket units (display and correctness, no profit claim)

- One helper `basket_move(lag, mask)` returning index-equivalent points, normalised by the covered weight. Use it in
  weather.py:273, gen3, the forecast lab and the domino.
- One sector map with nbfc inside "fin".
- Keep the old photo fields under their names for history, and add `wmove*_ix` alongside.

### I4. Drop the sector split from entry search (tested negative)

- Bank minus rest had zero out-of-sample skill at every horizon (E3).
- wmove60_bank, _it and _energy have AUC about 0.5 at triggers (E1).
- Keep them on the display as colour ("banks are carrying the move"). Remove factor group 30 from the nightly search,
  which saves search budget and multiple testing.

### I5. A Hayashi-Yoshida lead-lag estimator on raw ticks (untested)

- The 1-Hz grid hides sub-second leadership. The Hayashi-Yoshida covariation works on asynchronous ticks
  (Hoffmann, Rosenbaum and Yoshida 2013).
- A Python implementation is https://github.com/philipperemy/lead-lag (research grade; its author warns of a
  possible missing term). It can be cross-checked with R yuima `llag` (https://rdrr.io/cran/yuima/man/llag.html).
- Background: multi-scale lead-lag, https://arxiv.org/pdf/1708.03992.
- Use it nightly to re-estimate, per stock, its lead and its weight-adjusted share of leadership, then weight P by
  that leadership instead of raw index weight. This is a nightly offline job, never live.

### I6. Divergence and thrust alarms (tested, too rare or redundant)

- The thrust alarm adds little beyond P.
- Divergence happened 3 times in 3 days. Do not build it.

## Phase B scripts (ready, not run)

1. `D:\ApexOptions\data\research\13nov\work\R08\phaseB_hw_all17.py`. Run after 15:30, one invocation at a time, in
   four batches of about 6 parts, then `--summary`. The commands are in the file header. It covers all 26 ds_v2
   parts:
   - cross-correlation
   - per-day OLS stability of the 0.10 / 0.27 / 0.10 coefficients
   - the fixed rule P at 10 s to 5 min
   - thrusts
   - P at every trade trigger, split into early and late windows, for the pool books and for all books

   This is the 17-day test of E4 and E5.
2. A Conductor replay with the I2 veto as a shadow account. **Needs the owner's OK** (it is a replay). No script was
   written, because replays must go through the owner.

Scratch scripts and outputs are in `D:\ApexOptions\data\research\13nov\work\R08\`: s03 (AUC), s04 (lead-lag),
s05 (veto search), s06 (veto detail), s07 (fitted stand), s08 (fixed P), s09 (P at triggers), s10 (greedy sim).
