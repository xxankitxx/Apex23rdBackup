# R16: Internet and GitHub research, tested on our own trades

Analyst R16, 13 Nov 2026. Lens: owner point 1 (ideas from the internet and free public GitHub code), tested walk-forward on
`trades_all_books.parquet` and the Conductor's 119 replayed trades. Scratch scripts and result files:
`D:\ApexOptions\data\research\13nov\work\R16\` (`wf_lit.py`, `wf_short.py`, `wf_extra.py`, CSVs).

## Findings first

1. **The best idea from the literature is the VWAP side.** Zarattini, Aziz and Barbon trade intraday momentum only when
   price is on the right side of the session VWAP, and use VWAP as the trailing stop. On our data, trades taken with the
   futures on our side of VWAP beat trades against it **in both windows, in the c20 pool, in the Conductor, and across all
   107 books (20,817 trades)**. It is the only idea of the 13 families I tested that held up everywhere.
   On the Conductor test days (5 to 12 Nov): strike rate 63.2% against 51.4%, no losing day (base: 2), worst day 0.0%
   (base -6.0%). It is **not ready to promote**: on the early days it skips some big winners, so the compounded
   return falls (see Evidence). Build it as a shadow book first.
2. **Our dealer-gamma map reads Nifty the wrong way round.** The code assumes dealers are long calls and short puts
   (`apex/engine/gex.py:6-9`) and vetoes buying when the regime is DAMPEN (`gex.py:150-158`). In our trades the
   opposite holds: AMPLIFY was the worst regime (36.3% winners, mean -2.35% on 1,078 trades) and DAMPEN the best
   (51.5% and 48.8% winners in the two windows). The gex_room advisor's veto flips sign between windows, so it carries
   no reliable information. On Nifty, retail buys options and proprietary desks and foreign funds sell both sides, so the
   US sign convention does not fit.
3. **Max pain pinning does not help a buyer.** On the 4 expiry days, trades pointed TOWARD max pain did worse than trades
   pointed away from it (morning: 45.6% against 53.0% winners; afternoon: 43.5% against 45.6%). Do not buy toward max
   pain on expiry day.
4. **Options are always rich.** Implied vol over 15-minute realised vol (`wx_e_iv_rv`) never fell below 0.45 and its
   median is 1.70. The buyer always pays a variance premium. No IV/RV band gives a stable edge. This supports what we
   already know: buy only for short, sharp moves.
5. **A "trend vote" (60-min MA, 5-min RSI, VWAP side: 2 of 3 with us)**, the free-code cousin of Supertrend, was the
   strongest rule on the test days (Conductor 76.5% winners, pool 76.3%) but weak on the early days (more losing days,
   much lower compounded return). It fails "passes in two windows". Shadow only.
6. **Opening range breakout, order flow imbalance, the day's move (a Gao-style proxy), PCR, OI change, IV regime and
   mean reversion all failed** walk-forward or flipped between windows. Details below.
7. **Multiple testing.** Pass 1 tried 734 threshold variants (67 final rules); pass 2 tried 10 fixed rules on 3 trade sets
   in 2 windows; pass 3 tried 8 splits. With this many tries, about a third of rules look better on the test days by
   chance. Treat only results that hold in both windows and on all 107 books as signals. Only the VWAP side meets that.

## Teardown: what the code already has, and where it falls short

I grepped `apex/engine/` for every idea on my list. Most ideas already exist as **weather items** (recorded at each
trigger), but almost none is used as a **yes/no gate** by the pool books: every pool entry runs with `rule = null`
(`data/replay/batch/p44_sim/conductor_sim.json` pool block; pool selection `apex/engine/conductor.py:72`).

| Idea (source) | In the code? | Where | Used to decide? |
|---|---|---|---|
| Session VWAP, distance, z-score | Yes | VWAP built `apex/engine/regime.py:109-111`; `vwap_ext` `weather.py:714`; `vwap_side_with` `weather.py:1036`; `vwap_z` `weather4.py:249` | No. Shown and logged only. Regime uses VWAP stretch for EXHAUSTION (`regime.py:24,149`) |
| VWAP trailing stop (Zarattini et al.) | No | none | No |
| Opening range 15/30/45 min | Yes | `weather.py:711-712` (unsigned: 0 low, 1 high) | No |
| First half-hour predicts last half-hour (Gao et al.) | No | `day_move` from the first print `weather4.py:361-364` is the nearest; no "previous close to 09:45" return | No |
| Noise area (move vs normal move at this time of day) | Partly | `range_vs_norm`, `rv5_vs_norm` `weather.py:573`; `day_move_vs_strad` `weather4.py:454` | No |
| Order flow imbalance (Cont et al.) | Yes | `e_fut_ofi60`, imbalance items (`weather.py:55` list), forecaster tape | Forecaster only |
| Dealer gamma, flip, walls (GEX repos) | Yes | `apex/engine/gex.py` whole file | Advisor `gex_room` `apex/engine_main.py:1519-1523`; vote only through learning |
| Max pain | Yes | `gex.py:93-95`; `max_pain_dist` `weather.py:952` | No |
| PCR and its change | Yes | `weather.py:548` | No |
| OI change own/other strike | Yes | `oi_*_chg*` items (`weather.py:63`) | No |
| Supertrend / ATR bands | No | only `atr1_15` and `ma_stack` `weather4.py:352` | No |
| HAR realised-vol forecast (Corsi) | No | `rv1`, `rv5`, `rv15` raw only (`weather.py:488,738`) | No |
| IV crush / IV rank | Partly | `iv_vs_med`, `atm_iv_day_pos`, `e_iv_rv` | No |
| Expiry-day gamma | Yes | `dte`, `gamma_theta`, `theta_ratio` | No |

Where it fails, in my area:

* **`gex.py` sign assumption** (`gex.py:6-9`, `_net_at` at `gex.py:43-47` uses `ce_oi - pe_oi`). The file's own honesty note
  (`gex.py:12-14`) says the dealer sign may be wrong on Nifty. Our trades confirm it (Evidence, table 4). The `advise`
  method vetoes DAMPEN (`gex.py:150-158`), the regime in which our trades actually did best.
* **`gex.py` has OI only for the nearest weekly** (`gex.py:21`), so on Monday and on expiry Tuesday the map ignores the next
  week, where much of the open interest has moved.
* **VWAP is computed but never acted on.** `regime.py:109` builds a true volume-weighted price; nothing in the pool books or
  the hold logic reads its side.
* **No first-half-hour field.** The Gao effect needs the return from the previous close to 09:45. The photograph has
  `to_pdc` and `day_move`, but `to_pdc` cannot rebuild the previous close cleanly (my rebuild scattered by 50 to 500 points
  within a day), so the effect cannot be tested from the trade table.

## Evidence

Method. Discovery days 19 Oct to 4 Nov (12 days); test days 5, 6, 9, 11, 12 Nov (5 days). Returns are per trade in
percent of premium; day returns compound all-in. The Conductor test is "skip only": a skipped trade is removed and the
account stays flat. A real replay would let another book use the free time, so this is a lower bound on activity.

### Table 1. Pass 1: thresholds learned on early days only, then applied to test days (Conductor, best and worst rows)

Test-day base: 35 trades, 51.4% winners, mean +4.81%, compounded +200.7%, 2 losing days.

| Family | Rule (learned early) | Test n | Test win % | Test mean % | Test compounded % | Losing days |
|---|---|---|---|---|---|---|
| Mean reversion (inverse) | `pos60 >= 0.625` | 13 | 69.2 | 13.83 | 308.1 | 0 |
| Trend | `ma60_dist >= 11` | 14 | 78.6 | 12.81 | 314.8 | 1 |
| VWAP | `vwap_ext >= -1.4` | 20 | 65.0 | 10.47 | 400.6 | 0 |
| ORB | `or15_pos >= 0.26` | 22 | 54.5 | 8.46 | 282.7 | 1 |
| GEX | `gex_flip_ahead >= -37` | 22 | 63.6 | 8.05 | 295.6 | 1 |
| Max pain | `max_pain_dist <= 7.5` | 20 | 60.0 | 8.11 | 232.2 | 1 |
| OFI | `e_fut_ofi60 <= 9` | 22 | 50.0 | 6.33 | 157.9 | 2 |
| PCR | `pcr <= 1.09` | 34 | 50.0 | 4.79 | 184.9 | 2 |
| Noise area | `range_vs_norm <= 0.956` | 9 | 33.3 | -2.51 | -25.8 | 3 |

Full table for both the pool and the Conductor: `work\R16\wf_lit_results.csv` (734 variants tried).
Note the last row: it had 71.8% winners on the early days and 33.3% on the test days. That is what overfitting looks like.
The trend rows (MA60, RSI, position in 60-min range) all say the same thing: **be with the last hour's trend**.

### Table 2. Pass 2: fixed literature thresholds (no fitting), both windows, Conductor (skip only)

| Rule | Window | n | Win % | Mean % | Compounded % | Losing days | Worst day % | Without best trade % | Without best day % | Top 10 kept |
|---|---|---|---|---|---|---|---|---|---|---|
| Base | early | 84 | 53.6 | 7.55 | 7,489 | 3 | -37.1 | 3,874 | 1,082 | 10 |
| VWAP side with us | early | 54 | 59.3 | 9.39 | 3,811 | 3 | -11.7 | 1,948 | 1,367 | 8 |
| Trend vote 2 of 3 | early | 41 | 53.7 | 7.01 | 638 | 6 | -24.1 | 308 | 271 | 5 |
| Above 60m MA | early | 66 | 54.5 | 8.76 | 4,974 | 4 | -43.1 | 2,557 | 1,430 | 10 |
| Day move our way (Gao proxy) | early | 45 | 55.6 | 8.13 | 1,267 | 3 | -19.0 | 656 | 661 | 6 |
| Gamma not DAMPEN | early | 68 | 54.4 | 8.34 | 4,994 | 2 | -37.1 | 2,567 | 1,249 | 9 |
| Base | test | 35 | 51.4 | 4.81 | 201 | 2 | -6.0 | 75 | 44 | 10 |
| VWAP side with us | test | 19 | 63.2 | 10.87 | 386 | 0 | 0.0 | 183 | 131 | 8 |
| Trend vote 2 of 3 | test | 17 | 76.5 | 14.14 | 594 | 0 | 0.0 | 305 | 159 | 8 |
| Above 60m MA | test | 23 | 60.9 | 7.53 | 271 | 1 | -4.8 | 116 | 77 | 7 |
| Day move our way (Gao proxy) | test | 18 | 50.0 | 6.94 | 139 | 1 | -14.0 | 39 | 27 | 7 |
| Gamma not DAMPEN | test | 18 | 61.1 | 5.81 | 110 | 1 | -9.5 | 22 | 0.1 | 7 |

Conductor per test day, VWAP side with us: 5 Nov skipped (base -6.0%), 6 Nov +88.0% (base +109.2%), 9 Nov +110.3%
(base +43.4%), 11 Nov +21.6% (base +12.0%), 12 Nov +1.1% (base -4.8%).

Owner's standard (docs/28 section 2) for "VWAP side with us" on the Conductor:

| Test | Early window | Test window |
|---|---|---|
| Strike rate higher | yes (59.3 vs 53.6) | yes (63.2 vs 51.4) |
| Return higher | **no** (3,811% vs 7,489%) | yes (386% vs 201%) |
| Positive without best trade and best day | yes | yes |
| Keeps most top trades | yes, 8 of 10 | yes, 8 of 10 |
| Worst day no worse | yes (-11.7 vs -37.1) | yes (0.0 vs -6.0) |
| Passes in two windows | **no** (return) | |

### Table 3. VWAP side across all 107 books (trade level, every trade counted)

| Window | Side | Trades | Win % | Mean % |
|---|---|---|---|---|
| early | against us | 5,845 | 44.8 | 0.35 |
| early | with us | 8,328 | 49.7 | 1.93 |
| test | against us | 2,901 | 44.9 | -0.59 |
| test | with us | 3,729 | 48.4 | 1.83 |

Pool books only: early 52.7% / +5.91% against, 63.2% / +8.80% with; test 40.5% / -2.04% against, 64.4% / +10.03% with.
The gap is about 5 points of strike rate in both windows. Trades of different books overlap in time, so the effective
sample is much smaller than the trade count; still, it is the steadiest split I found.

### Table 4. Dealer gamma regime (all 107 books)

| Window | Regime | Trades | Win % | Mean % |
|---|---|---|---|---|
| early | AMPLIFY | 1,078 | 36.3 | -2.35 |
| early | DAMPEN | 2,509 | 51.5 | 1.95 |
| early | MIXED | 10,596 | 47.9 | 1.49 |
| test | DAMPEN | 3,580 | 48.8 | 1.32 |
| test | MIXED | 3,054 | 44.6 | 0.13 |

The `gex_room` veto: early, vetoed trades 46.6% against 48.1% unvetoed (veto helps a little); test, vetoed 48.3% against
44.7% (veto hurts). It flips, so it fails.

### Table 5. Expiry days (19 Oct, 27 Oct, 3 Nov, 9 Nov): direction relative to max pain, all books

| Session part | Pointing | Trades | Win % | Mean % |
|---|---|---|---|---|
| before 13:15 | away from max pain | 3,501 | 53.0 | 3.18 |
| before 13:15 | toward max pain | 1,644 | 45.6 | 0.27 |
| after 13:15 | away | 1,181 | 45.6 | 0.13 |
| after 13:15 | toward | 704 | 43.5 | -1.09 |

Only 4 expiry days, 3 of them in the discovery window. Untested out of sample in the strict sense.

### Table 6. IV over realised vol (all books): no stable band

| IV/RV | early win % / mean % | test win % / mean % |
|---|---|---|
| up to 1.3 | 49.3 / 1.53 | 43.9 / -0.19 |
| 1.3 to 1.7 | 47.3 / 1.16 | 44.8 / 0.22 |
| 1.7 to 2.2 | 47.1 / 1.04 | 45.3 / 0.02 |
| above 2.2 | 47.1 / 1.35 | 50.0 / 1.89 |

## Ideas, ranked by expected value for this system

Each idea fits buy-only, all-in, one position, yes/no rules.

### 1. VWAP side gate (entry) and VWAP trailing stop (exit). Expected value: highest.
* Source: Zarattini, Aziz, Barbon, "Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)",
  SFI 24-97, https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy ;
  free Pine version https://kr.tradingview.com/script/gJeM3LZ5-Out-of-the-Noise-Intraday-Strategy-with-VWAP-YuL ;
  replication thread https://www.quantconnect.com/forum/discussion/18444 .
* Mechanism: VWAP is the average price paid today. Above it, the day's buyers are in profit and defend; below it, they
  are trapped sellers. An impulse with VWAP behind it has support; one fighting VWAP runs into it.
* Fields: `wx_vwap_side_with`, `wx_vwap_ext`, `wx_vwap_z`; live `regime.py:109`.
* Result: entry gate tested (Tables 2 and 3): passes everything on the test days, fails return on the early days.
  The VWAP trailing stop is **untested** (no VWAP at the hold marks); Phase B script below tests it.
* Build: shadow book `c20_vw` = each c20 pool book plus the yes/no rule `vwap_side_with == True` (silent when missing).
  As a display change, show "Futures are X points above/below VWAP, on/against our side" in the Forecaster's stand line.
* Risk: on strong trend-reversal days (the early window), the best trades start against VWAP. Skipping them costs a lot
  of compounded return. A softer form: require VWAP side only after 11:00, when VWAP has enough volume to mean something.
  That variant is untested.

### 2. Fix the gamma map's sign for Nifty, or retire the veto. Expected value: high (removes a wrong-way signal).
* Sources: Baltussen, Da, Lammers, Martens, "Hedging Demand and Market Intraday Momentum", JFE 2021,
  https://www3.nd.edu/~zda/intramom.pdf (momentum is strong only when dealers are short gamma);
  GEX code: https://github.com/FlashAlpha-lab/gex-explained , https://github.com/Matteo-Ferrara/gex-tracker ,
  https://github.com/aakash-code/GammaGEX .
* Mechanism: GEX only predicts if we know who is short the options. On Nifty, the public mostly buys calls AND puts;
  prop desks and foreign funds sell both. So sellers are short gamma on both sides and the "calls positive, puts
  negative" rule measures call-versus-put OI tilt, not dealer hedging.
* Fields: `wx_gex_regime`, `wx_gex_balance`, `wx_adv_gex_room`, `wx_gex_flip_ahead`.
* Result: tested (Table 4). The current reading is backwards in the early window and flips in the test window.
* Build: (a) stop showing "gamma DAMPENS moves: spikes tend to fade" as a reason not to buy (`gex.py:158`);
  (b) shadow item `gex_short_both` = minus gamma times (call OI + put OI) summed within 3 strikes of the forward,
  as a "how much hedging fuel sits near here" number. Untested.
* Risk: low. It is an advisor today; removing a wrong advisor cannot hurt trades.

### 3. Trend vote (Supertrend-like): 2 of 3 of {above 60-min MA, 5-min RSI above 50, VWAP side} with us. Expected value: medium.
* Sources: Supertrend plus ADX on Nifty options, https://fr.github.com/srikar-kodakandla/fully-automated-nifty-options-trading ;
  Gao, Han, Li, Zhou "Market Intraday Momentum", JFE 2018, https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414 .
* Mechanism: the c20 trigger is a 20-minute impulse plus pullback. If the last hour already leans our way, the pullback
  is a pause inside a trend, not a reversal.
* Fields: `wx_ma60_dist`, `wx_rsi14_5m`, `wx_vwap_ext`.
* Result: tested (Table 2). Test days: 76.5% winners, no losing day. Early days: 6 losing days against 3, compounded
  return falls from 7,489% to 638%, keeps only 5 of the top 10. Fails two windows.
* Build: shadow book `c20_tv`. Display: "trend vote 3/3 with us" in the commentary.
* Risk: high overfitting risk; it looks good on exactly the days that trended.

### 4. Expiry day: never buy toward max pain. Expected value: medium on Mondays/Tuesdays, nil otherwise.
* Sources: no peer-reviewed Nifty study found; broker claims conflict (e.g. https://aliceblueonline.com/blog/max-pain-options-trading-decisions-guide ,
  https://equitiesindia.com/glossary/max-pain-theory ).
* Mechanism: pinning, if it exists, is a slow drift. A buyer needs a fast move; a slow drift toward max pain is
  eaten by theta. Moves away from max pain on expiry are the ones that run.
* Fields: `wx_max_pain_dist`, `wx_dte`, `wx_mins_open`.
* Result: tested in sample (Table 5, 4 days). Not tested out of sample.
* Build: shadow rule "on dte < 1, skip trades whose direction points toward max pain". Re-check after 17 Nov expiry.
* Risk: 4 days; max pain uses only nearest-week OI (`gex.py:21`).

### 5. First half-hour predicts last half-hour (Gao et al.). Expected value: unknown; cheap to test.
* Sources: JFE 2018 above; summary https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/ ;
  gamma explanation in Baltussen et al. above.
* Mechanism: late-informed and rebalancing flows trade the morning's information in the last half hour.
  For us: after 14:45, only take c20 entries that agree with the sign of (09:45 price minus previous close).
* Fields: none clean. `wx_day_move` is from the first print, not the previous close; `wx_to_pdc` cannot rebuild the
  close. The proxy "day move our way" failed on the test days (50.0% winners).
* Result: untested properly. Rough proxy: 7 of 10 days with usable prints had the same sign; too few to mean anything.
* Build: add weather item `r_first30 = F(09:45) - previous close` (signed our way) and a display line
  "the morning said up/down; late-day flows usually follow". Phase B script below measures it on 17 days.
* Risk: 17 days cannot confirm a 1.6% R-squared effect. Use only as a tie-breaker.

### 6. HAR realised-vol forecast for "can this move pay the theta?". Expected value: medium for the Forecaster (owner point 4).
* Sources: Corsi 2009 HAR-RV; Python: https://pypi.org/project/mfe-toolbox/ , https://matmou.github.io/OpenModules/session-06-har-models ;
  0DTE variance premium: https://carey.jhu.edu/articles/risk-reward-insights-0dte-option-trading .
* Mechanism: RV next 15 min = a + b1 RV(1 min) + b5 RV(5 min) + b30 RV(30 min). If forecast RV times delta is below the
  theta break-even (`wx_theta_be15`), the option cannot pay for itself; say so and stand aside.
* Fields: `wx_rv1`, `wx_rv5`, `wx_rv15_spot`, `wx_theta_be15`, `wx_e_iv_rv`.
* Result: untested. Table 6 shows IV is always rich (median 1.7 times RV), so this is about timing, not about cheap options.
* Build: forecaster display "expected range next 15 min: X points; break-even needs Y" as one plain sentence, plus a
  shadow rule "forecast range >= break-even". Fit the 3 betas on discovery days per the Phase B plan.
* Risk: three numbers fitted on 12 days; keep it linear.

### 7. Ideas tested and rejected (do not build)

| Idea | Source | Result |
|---|---|---|
| Opening range breakout (15/30/45 min, signed) | Zarattini, Barbon, Aziz ORB, https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/ | Learned thresholds raised mean on test days but not strike rate (or15: 50.0% vs 53.7% pool) |
| Order flow imbalance as an entry filter | Cont, Kukanov, Stoikov, https://arxiv.org/abs/1011.6402 | No strike-rate gain (54.1% vs 53.7%). OFI belongs in the 1 to 3 minute forecaster, where it already is |
| Noise area via range vs normal | Zarattini et al. | Learned rule went 71.8% early to 33.3% test: overfit |
| PCR level and change | broker practice | No gain (52.2% vs 53.7% pool test) |
| OI net help (own vs other strike) | broker practice | Hurt on test days (46.5% vs 53.7%) |
| Mean reversion after extension (z20, VWAP stretch low) | many blogs | Wrong way: our winners are with the stretch, not against it |
| IV regime (IV vs median, VIX change) | IV crush literature | No stable band (Table 6) |
| GEX wall room | GEX repos | Flips between windows |

## Phase B scripts (ready, not run)

* `D:\ApexOptions\data\research\13nov\work\R16\phaseB_vwap_exit_gao.py`. Run after 15:30, one day per run:
  `py -3.13 phaseB_vwap_exit_gao.py 2026-11-06`. For each Conductor trade it finds the first second (after 30 s) that the
  futures sit on the wrong side of VWAP and books the option bid then, if earlier than the real exit; it also records
  first-30-minute and last-30-minute futures moves for the Gao test. Writes `phaseB_vwap_exit_<day>.csv` and
  `phaseB_gao_<day>.json`. It reads one ds_v2 part at a time. It uses `fut[:,3]` as the exchange VWAP if that field sits
  within 0.5% of the last price, otherwise a time-weighted average (flagged in the output), because I could not confirm
  the field's meaning from `ds2.py:128`. 12 Nov is not in ds_v2.

## How many things I tried

* Pass 1: 13 families, 67 fields, 734 threshold-and-side variants, chosen on early days only.
* Pass 2: 10 fixed rules on 3 trade sets, 2 windows.
* Pass 3: 8 splits (gamma regime, gex veto, IV/RV, VWAP side, each on all books and pool; max pain by session part).
* Web: 9 searches; no repository code was downloaded or run.
