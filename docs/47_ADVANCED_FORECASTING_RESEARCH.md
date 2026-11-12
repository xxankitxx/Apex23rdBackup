# 47. Advanced short-horizon forecasting for Nifty weekly options: research and a build plan

11 November 2026. Research document written at the owner's request. The owner's complaint: the present forecaster is
naive. It outputs one number, P(premium gains 5 % before it loses 5 % within 300 s), from a logistic model on 33
features. It ignores time decay across strikes. It says nothing about what happens next, then next, then next.

**What this document is.** A literature and method review, checked against published sources, with a ranked plan and
a design sketch. **What it is not.** Nothing here was run. No code, model, threshold, book or setting was changed. The
live engine was running while this was written, so no Python, replay or test was started. Every cost figure below is
an estimate from operation counts, not a measurement. Every number that comes from this system is cited to its doc.

---

## 0. The short version

1. **Volatility and decay are predictable at 1 to 30 minutes. Direction is barely predictable.** The literature and
   this system's own results (docs/45 section 7) agree. Build on what is predictable first.
2. **The champion already trades on a volatility forecast, not a direction forecast.** Its "rent" is
   `0.5 * Gamma * RV / |Theta|`, which under Black-76 equals realised variance divided by implied variance
   (section 2.1). A better forecast of future realised variance, in the right clock, serves it directly.
3. **The decay clock matters more than any model choice.** The move an option needs per minute to pay its decay is
   about 3.8 index points on a calendar clock, 7.5 on the code's "trading minute" theta, 9.0 on a pure trading clock
   (illustration: future 23,000, IV 12 %). Which one is true intraday on NSE weekly options is an empirical question
   this system can answer from its own tapes (section 2.2).
4. **A path forecast is a construction, not a new model.** Forecast the future's variance and (weak) drift for each
   horizon, forecast how each strike's IV moves with the future, then reprice every candidate in full. One-factor
   quantile mapping gives the fan chart exactly and cheaply (section 2.7).
5. **The +5 %/-5 % barrier has a closed-form structural baseline.** With zero drift, the chance the bid hits +5 %
   before -5 % is `(5 % - spread %) / 10 %`. A 1 % spread gives 40 %, not 50 %. Decay and rent add a drift term with
   a closed form (section 2.7). With spreads near 0.4 to 0.5 % of premium it reproduces the recorded tilt toward
   "down first" (46 % up first, given an event) with no fitted weights. The spread figure must be checked on the tapes.
6. **Self-improvement must update only on matured outcomes and must beat a frozen copy of itself.** Fixed-share
   expert weighting, adaptive conformal intervals and online Platt scaling are the right tools. They cannot create a
   signal that is not there (section 2.8).
7. **Deep order-book models do not fit this data.** DeepLOB used 10 levels and 134 million samples; benchmarks show
   such models lose much of their accuracy on new data; their horizon is a few price changes, not minutes. This
   system has 15 sessions at 1 Hz with top-5 depth totals (section 2.9).
8. **Gamma exposure, max pain and OI walls rest on an unknown inventory sign.** Pinning near expiry has evidence in
   other markets. "Dealers are long calls and short puts" is an assumption, and on Nifty it may be wrong (section 2.10).
9. **Ranked plan:** first a decay clock, realised-decay tables and a variance (rent) forecast; second a structural
   path engine with barrier probabilities; third live maturity-only scoring with online weighting and a frozen
   control (section 4).
10. **No forecaster can deliver "no losing trade".** Even a 90 % win rate gives only a 12 % chance of 20 wins in a row
    (section 6).

---

## 1. Where the system stands

### 1.1 Data the forecaster can use today

From `apex/predict/features.py`, `apex/greeks.py`, `apex/engine/gex.py`, `apex/feed_breeze.py` and docs/41 to 46.

| Item | What is recorded | Limits |
|---|---|---|
| Index future | bid, ask, last price, cumulative volume, 1 s | no order-level events |
| Future depth | top-5 bid and ask quantity totals (`bq`, `aq` in `features.update`) | totals, not per level, in the forecaster |
| Heavyweights | cash price and stock-future quote, with index weights | freshness rules 5 s |
| Option chain | near-week bid, ask, age per strike and right, 1 s | depth only inside the hero band |
| Open interest | REST chain polls, nearest weekly only (`gex.py` header) | polled, not streamed |
| Greeks | Black-76 on the put-call-parity forward, IV by bisection | see 1.2 |
| History | 15 recorded sessions in `data/research/ds_v2`; 54,018 moments; 103,995 executable picks (docs/45 6.1) | 15 independent days |

### 1.2 Conventions in the code

- `greeks.years_to_expiry`: **calendar** time to 15:30 IST on expiry, floor 600 s on expiry day.
- `greeks.greeks`: `theta_min = theta_year / 365 / 375`. This puts each calendar day's decay into the 375 trading
  minutes. Call it the **kit** clock below. Vega is per vol point.
- `c20_9x.py` "seqcal": `rent_cal = 0.5 * G * RV_min / |Theta_cal|` with **calendar** theta, threshold 1.2. Its own
  comment says this equals realised over implied variance. Section 2.1 shows why.
- `c20_9x.py` uses `ANN = 252 * 375 * 60` for annualising realised variance.

Three clocks are already in use in one codebase. That is not a bug. It is the central modelling choice of section 2.2.

### 1.3 Evidence so far

| Finding | Source |
|---|---|
| Activity (will a 5 % move come) is forecast well, mostly from premium, spread, expiry, time and realised volatility | docs/41 3.1, docs/45 7 |
| No model beats an activity-only baseline on three-way log loss over 10 unseen sessions | docs/45 7 |
| Direction given an event: AUC 0.54 (hazard 0.5385, logistic 0.5426), interval clear of 0.50, 8 or 9 of 10 sessions | docs/45 7 |
| Top 5 % by edge: mean 300-s return +0.22 %, positive on 6 of 10 sessions | docs/45 7 |
| Order-flow and depth features did not raise direction skill; gradient boosting did not help | docs/41 3.2 |
| Greek repricing of a forecast of the future gives the best range tails; holding IV constant makes ranges too narrow; adding an IV scenario overshoots at 60 s | docs/41 12.3, 13.1 |
| Full repricing against delta-gamma-theta: 0.003 to 0.04 % of premium at the median; delta alone 0.17 to 0.74 % | docs/41 12.3 |
| Champion `c20_9y`: 92 fills, 54 profitable, 20 runners; "+5 % first" is the wrong target for its exits | docs/45 6.3 |
| Executable picks: delta 0.52 to 0.74, premium 85 to 213, median 169 | docs/45 6.1 |

### 1.4 The owner's request as forecast targets

| Target | Unit | Horizons |
|---|---|---|
| Index future path | quantiles of points, and drift | 1, 2, 3, 5, 10, 15, 30 min |
| Each candidate option's bid path, including decay | quantiles of premium | same |
| Decay-only path (future unchanged) | premium | same |
| Move needed to pay decay | index points | same |
| Barrier events (+x % before -x % on the bid) | probabilities, with timing | 30 s to 30 min |
| Future realised variance against implied | ratio ("rent") | same |

---

## 2. Methods

Each method has the same parts: what it predicts, the mathematics, inputs, cost per second at 1 Hz on a laptop,
published evidence at 1 to 30 minutes, how it applies here, and a verdict: **adopt now**, **test**, or **skip**.

Notation. `F` the parity forward of the weekly (index points), `K` strike, `sigma` implied volatility (decimal, per
year in the clock named), `T` time to expiry (years), `P` premium, `phi` and `N` the standard normal density and
distribution, `h` horizon. Black-76 with zero rate, which is fine for minutes.

### 2.1 Greeks-based premium dynamics

**Predicts.** Nothing by itself. It translates a forecast of (change in future, change in IV, time passed) into a
change in each option's premium. It is the bridge from a market forecast to a premium forecast.

**Mathematics.**

```
Black-76, zero rate:
  d1 = [ln(F/K) + 0.5 sigma^2 T] / (sigma sqrt T),   d2 = d1 - sigma sqrt T
  delta = N(d1) (call), N(d1) - 1 (put)
  Gamma = phi(d1) / (F sigma sqrt T)
  vega  = F phi(d1) sqrt T            (per 1.00 of sigma; the code divides by 100)
  Theta = -F phi(d1) sigma / (2 sqrt T)   (per year)
  vanna = d(delta)/d(sigma) = -phi(d1) d2 / sigma
  volga = d(vega)/d(sigma)  = vega d1 d2 / sigma

Second-order expansion over a step:
  dP ~ delta dF + 0.5 Gamma dF^2 + Theta dt + vega dsigma
       + vanna dF dsigma + 0.5 volga dsigma^2

The gamma-theta identity (Black-76, zero rate):
  Theta = -0.5 Gamma F^2 sigma^2

So the move that pays one step of decay, from 0.5 Gamma dF^2 = |Theta| dt:
  |dF_BE| = sqrt(2 |Theta| dt / Gamma) = F sigma sqrt(dt)
```

The break-even move depends only on the strike's own IV and the clock used for `dt`. It does not depend on expiry or
moneyness except through the smile. That is useful: one number per strike.

**Realised against implied variance.** Write `s^2` for realised variance of the future per unit time (points
squared). Then the gamma-plus-theta part of the premium change over `h` is

```
0.5 Gamma s^2 h - |Theta| h = |Theta| h (rent - 1),    rent = 0.5 Gamma s^2 / |Theta| = s^2 / (F^2 sigma^2)
```

This is why the champion's rent is a realised-to-implied variance ratio, and why its threshold means "movement is
paying the rent". Carr and Madan describe the delta-hedged version, where the P&L is driven by the gap between
realised and implied variance weighted by dollar gamma ([Carr and Madan 1998](https://www.next-finance.net/IMG/pdf/Towardsvoltrading.pdf)).
Bakshi and Kapadia show that delta-hedged index option gains are negative on average, consistent with a negative
volatility risk premium ([Bakshi and Kapadia 2003](https://ideas.repec.org/a/oup/rfinst/v16y2003i2p527-566.html)).
Ahmad and Wilmott study how the choice of hedging volatility changes the P&L path ([Ahmad and Wilmott 2005](https://wilmott.com/?p=1358)).

**The champion does not hedge.** For an unhedged long option the expected change over `h` is

```
E[dP] ~ delta * m(h) + |Theta| h (rent_f - 1) + vega * E[dsigma] + 0.5 Gamma m(h)^2
```

with `m(h)` the expected future move (drift) and `rent_f` the forecast rent. The direction term dominates the
variance of the outcome: for a 15-point move at delta 0.56 it is 8.4 premium points, while `0.5 Gamma dF^2` is
about 0.2 to 0.5 points (3 days to expiry, and expiry day, in the illustration below). So the rent filter does not pay
the champion through gamma directly. It selects moments when movement is large, so a directional entry with a trailing
exit can run before decay matters. That is a forecasting statement: rent is a forecast of variance.

**Taylor or full repricing.** Full Black-76 repricing of 40 contracts costs well under a millisecond in numpy. Use
full repricing in every path. Use the Taylor terms only to attribute P&L. The system's own measurement says the
second-order terms are accurate at the median (docs/41 12.3). They are not accurate for large moves near expiry,
where gamma changes fast. The "vanna-volga method" of Castagna and Mercurio is a different thing: an FX smile
interpolation from three quotes ([Castagna and Mercurio 2007](https://www.risk.net/derivatives/equity-derivatives/1500224/vanna-volga-method-implied-volatilities)).
Here vanna and volga are only second-order terms.

**Inputs.** F, K, T, sigma per strike; already in the engine.

**Cost at 1 Hz.** Greeks for 40 contracts: about 0.1 ms. P&L attribution per held contract: microseconds.

**Evidence at 1 to 30 minutes.** The expansion is an identity, not a forecast, so the question is only accuracy. The
system's test (docs/41 12.3) is the relevant evidence: repricing a forecast of the future gives the best tails at
60 s and 300 s; it does not help the median, because the median needs direction.

**Here.** (1) Every live trade gets a P&L attribution: delta, gamma, theta, vega, residual. This tells the owner
whether a loss came from direction, decay or an IV drop. (2) The translator becomes the core of the path engine.

**Verdict. Adopt now** (attribution and translator).

### 2.2 Time decay inside the session

**Predicts.** How each candidate's premium decays over the next minutes if the future does not move, by strike, by
days to expiry and by minute of the day. This is the part the owner says is missing.

**Three clocks.**

| Clock | Minutes per year | Assumes | In the code |
|---|---|---|---|
| Calendar | 365 x 1440 = 525,600 | IV constant; time passes at night and on weekends at the same rate | `years_to_expiry`, `rent_cal` |
| Kit | 365 x 375 = 136,875 | a full calendar day of decay inside 375 trading minutes | `greeks.theta_min` |
| Trading | 252 x 375 = 94,500 | all variance in trading minutes | `ANN` in `c20_9x.py` |

Illustration, ATM, future 23,000, IV 12 %. The break-even move `F sigma sqrt(dt)` per clock:

| Horizon | Calendar | Kit | Trading |
|---|---|---|---|
| 1 min | 3.8 points | 7.5 | 9.0 |
| 5 min | 8.5 | 16.7 | 20.1 |
| 15 min | 14.7 | 28.9 | 34.8 |
| 30 min | 20.9 | 40.9 | 49.2 |

These are numbers computed here from the formula, not market data. The spread between the columns is a factor of 2.4.
It decides whether a given session's movement "pays the rent".

Three days to expiry, same inputs: ATM premium about 100 points, calendar theta 0.0116 points a minute. A 375-minute
session decays 4.3 points on the calendar clock and 16.7 on the kit clock. On the calendar clock the other 12.3
points fall overnight, as a gap at the open if IV is unchanged.

**What the evidence says about which clock is right.**

- French and Roll: variance is far lower when the market is closed. A weekend's variance was only about 11 % above
  a normal weekday's, over 66 closed hours ([French and Roll 1986](https://www-2.rotman.utoronto.ca/~kan/3032/pdf/AssetPricingAnomalies/French_Roll_JFE_1986.pdf)).
- Muravyev and Ni: delta-hedged S&P 500 option returns average -0.7 % a day, all of it overnight (about -1 %);
  open-to-close returns are about +0.3 %. Their explanation: prices ignore that volatility is much higher in trading
  hours ([Muravyev and Ni 2020](https://ideas.repec.org/a/eee/jfinec/v136y2020i1p219-238.html)).
- Jones and Shemesh: option returns are lower over non-trading periods, mostly weekends, which they attribute to
  mispricing of variance over closures ([Jones and Shemesh 2018](https://ideas.repec.org/a/bla/jfinan/v73y2018i2p861-900.html)).
- **Nifty specifically:** Bhat, Pandey and Nageswara Rao find the same day-night pattern in Nifty options, 2017 to 2020. Short
  option strategies earn overnight and lose intraday. The asymmetry is weaker on jump days and declines with
  moneyness and maturity. They argue the day-night volatility bias does not explain it; the option seller's premium
  is mainly a reward for overnight risk ([Bhat, Pandey and Nageswara Rao 2024](https://ideas.repec.org/a/wly/jfutmk/v44y2024i8p1320-1337.html)).
  They also report that selling at the close and covering at the open is not profitable after transaction costs.

So, for an intraday option buyer on Nifty, the published evidence says the net cost of holding through the session
has been **low**: sellers lost intraday and earned overnight. The kit clock books a full day's decay inside the
session, so it overstates the intraday cost. The champion holds intraday, so this is the most relevant published
fact for its economics. It is from 2017 to 2020, before the 2024 and 2025 rule changes, and it mixes decay with
movement gains, so it must be re-measured on this system's tapes.

**Variance clock.** A model that nests the three clocks:

```
tau_var(t) = sum over remaining intervals i of w_i
  w_i = u(m) for a trading minute m (intraday U-shape, measured)
      = g_on for an overnight, g_we for a weekend or holiday (measured from gaps)
  normalised so that one year sums to 1

Same ATM premium in both clocks:  sigma_cal^2 T_cal = sigma_var^2 tau_var
Theta in minute m of the session:  Theta_m = (dP / d tau_var) * u(m)
```

If the market prices flat IV in the variance clock, then calendar IV must drift: `sigma_cal(t) = sigma_var *
sqrt(tau_var(t) / T_cal(t))`. Intraday minutes are heavy, so `tau_var` falls faster than `T_cal` during the day and
calendar IV drifts down; overnight `T_cal` falls by 1,065 minutes while `tau_var` falls only by `g_on`, so calendar
IV rises at the open. This is a testable prediction. A one-parameter family spans the cases:

```
sigma_cal(t) = sigma_bar * (tau_var(t) / T_cal(t))^(kappa/2)
  kappa = 0: calendar clock is right (IV flat in calendar time)
  kappa = 1: variance clock is right
```

Estimate `kappa` by days-to-expiry bucket from the tapes. The published facts pull in two directions. Muravyev and
Ni's result (options lose overnight, gain intraday) is what `kappa` near 0 predicts: prices follow calendar time
while variance arrives in trading hours. The US VIX drifts down about 0.8 % from open to close, mostly in the first
30 minutes and the last minutes, and rises over the weekend
([Fernandez-Perez, Frijns, Tourani-Rad and Webb, summary](https://www.cxoadvisory.com/volatility-effects/intraday-and-intraweek-vix-behaviors/)).
That is the shape `kappa > 0` predicts. Both are US results. For Nifty weeklies the answer must be measured, and it
may differ by days to expiry.

**Intraday seasonality on Nifty.** One-minute Nifty futures data 2011 to 2018 show the U-shape, lowest volatility
11:00 to 12:00 ([Singh and Gangwar 2018](https://mpra.ub.uni-muenchen.de/89689/)). The general method of removing
intraday periodicity before modelling persistence is Andersen and Bollerslev
([1997](https://ideas.repec.org:443/a/eee/empfin/v4y1997i2-3p115-158.html)). The "activity time" idea of
integrating a seasonal activity curve into a new time scale is from Dacorogna and co-authors
([1993](https://econpapers.repec.org/RePEc:eee:jimfin:v:12:y:1993:i:4:p:413-438)).

**Expiry day (0DTE).** With IV flat, the ATM premium is `P ~ 0.4 F sigma sqrt(tau)`
([Brenner and Subrahmanyam 1988](https://scilit.com/publications/606a61fa3b0b8ee01f6b8eaa8d248d65)), so decay is
`dP/dtau = P / (2 tau)`: a share `1/(2 tau)` of the premium per minute. Illustration, future 23,000, IV 14 %:

| Time left to 15:30 | ATM premium | Decay per minute | Share of premium per minute |
|---|---|---|---|
| 375 min (09:15) | 34.4 | 0.046 | 0.13 % |
| 240 min | 27.5 | 0.057 | 0.21 % |
| 120 min | 19.5 | 0.081 | 0.42 % |
| 60 min | 13.8 | 0.115 | 0.83 % |
| 30 min | 9.7 | 0.162 | 1.67 % |
| 10 min (the code's floor) | 5.6 | 0.281 | 5.0 % |

With a 5 % barrier, the last half-hour of expiry day is a different instrument. Out-of-the-money options lose a larger
share of their premium per minute than ATM ones, because `|Theta_K| / P_K = 0.5 Gamma_K F^2 sigma_K^2 / P_K` rises
away from the money. Bandi, Fusari and Reno model 0DTE smiles and report large pricing improvements over standard
models ([0DTE option pricing](https://faculty.essec.edu/en/research/15649-0dte-option-pricing)); a 2026 follow-up
models tenors under one week, where the ATM IV term structure oscillates sharply
([Bandi, Fusari, Gazzani and Reno 2026](https://arxiv.org/abs/2603.29430)). In US data, retail 0DTE traders lost
money in aggregate, most of it to transaction costs ([Beckmeyer, Branger and Gayda 2023](https://papers.ssrn.com/abstract=4404704)).
All three are US data.

**Indian rules that change the expiry day.** SEBI's 1 October 2024 circular allowed weekly index expiries on one
benchmark per exchange (Nifty for NSE) from 20 November 2024, raised contract size, added 2 % extreme loss margin on
short options on expiry day, required upfront premium, and removed the calendar-spread benefit on expiry day
([summary, Zerodha](https://zerodha.com/z-connect/business-updates/sebis-new-rules-for-index-derivatives-heres-whats-changing)).
NSE moved Nifty weekly expiry from Thursday to Tuesday, first Tuesday expiry 2 September 2025; a holiday moves it to
the adjusted date ([Angel One](https://www.angelone.in/news/nse-moves-derivatives-expiry-to-tuesday-starting-august-28-2025)).
SEBI's July 2025 interim order alleges that one firm moved Bank Nifty and Nifty on expiry days through component
stocks while holding options; the firm disputes it ([Oxford Business Law Blog](https://blogs.law.ox.ac.uk/oblb/blog-post/2025/07/jane-street-and-expiry-day-trap-unpacking-sebis-crackdown-algorithmic)).
I found no peer-reviewed study of the intraday decay curve of NSE weekly options. Practitioner write-ups describe late
expiry-day IV swings ([Upstox](https://upstox.com/news/market-news/trading/what-is-driving-option-volatility-on-expiry/article-68819/))
and weaker-than-calendar weekend decay ([Sensibull](https://blog.sensibull.com/2017/12/26/the-weekend-effect/)).
Those are anecdotes.

**Measuring realised decay from quotes.** Because the engine solves IV with calendar time, the identity
`P_mid(t) = B76(F(t), K, T_cal(t), sigma_cal(t))` holds each second. So over an interval:

```
carry_k = P_mid,k(t1) - B76(F(t1), K, T_cal(t0), sigma_k(t0))      (what is left after the future's move)
        ~ Theta_cal,k * dt  +  vega_k * dsigma_k

realised decay rate = Theta_cal + vega * E[dsigma | minute of day, DTE, moneyness, spot move = 0]
ratio_k = carry_k / (Theta_cal,k * dt)        1 = calendar, about 3.84 = kit, below 1 = slower than calendar
```

Steps: (1) bucket contracts by standardised moneyness `ln(K/F) / (sigma sqrt T)`, days to expiry, expiry or not,
minute of day; (2) on 1-minute and 5-minute steps of mid quotes, regress the IV change on the future's log change to
remove spot-vol co-movement (section 2.3); (3) the intercept by minute is the seasonal IV drift; (4) the realised
decay table is `Theta_cal + vega * drift`. Check it by attributing the ATM straddle's change. Use mids and 1 to
5-minute steps so bid-ask bounce does not dominate. Report open-to-close and close-to-open separately.

**Inputs.** Recorded 1 s option mids, IVs, F; the overnight gap of the future.

**Cost at 1 Hz.** Online: a table lookup, microseconds. Offline: minutes over 15 sessions. It is a research job and
needs the owner's go-ahead before it runs.

**Evidence at 1 to 30 minutes.** The decay formula is exact given IV. The open question is IV's own intraday drift.
Published evidence on that is US and decades old in parts; the Nifty day-night result is the closest. Weak for
intraday detail, strong for the direction of the effect.

**Here.** Replace "theta per trading minute" in forecasts with a measured decay rate per (moneyness, DTE, minute,
day type). Report every forecast's decay-only line. Keep the champion's rent exactly as it is; compute a variance-clock
rent beside it in shadow.

**Verdict. Adopt now.**

### 2.3 Implied volatility dynamics

**Predicts.** How each strike's IV moves when the future moves, and how it drifts over the session.

**Mathematics.**

```
Skew slope:          S_K = d sigma / d ln K at fixed F
Sticky strike:       sigma_K unchanged when F moves; ATM IV moves along the skew
Sticky moneyness:    sigma depends on K/F; ATM IV unchanged; each fixed-strike IV moves by -S_K d ln F
Skew stickiness ratio (Bergomi):  R = (d sigma_ATM / d ln F) / S_ATM
  R = 0 sticky moneyness (delta), R = 1 sticky strike, R = 2 local volatility at short maturity
Fixed strike:        d sigma_K = (R - 1) S_K d ln F + seasonal drift + mean reversion + noise

Intraday IV model for strike K over horizon h:
  d sigma_K = (R - 1) S_K d ln F + d_K(m, h) - k (sigma_K - sigma_bar_K) h + eta_K sqrt(h) eps

Minimum variance delta (Hull and White):
  delta_MV = delta_BS + vega_BS / (F sqrt T) * (a + b delta_BS + c delta_BS^2)
```

Derman named the regimes and found S&P 500 skew behaviour changing between them over time
([Derman 1999](https://emanuelderman.com/regimes-of-volatility/)). Daglish, Hull and Suo tested these rules of
thumb on S&P 500 data and gave no-arbitrage conditions for surface moves
([2007](https://ideas.repec.org/a/taf/quantf/v7y2007i5p507-524.html)). Bergomi's empirical SSR for index options is
about 1.5 for maturities from a month to a few years, as summarised in recent papers
([arXiv 2603.10857](https://arxiv.org/pdf/2603.10857); [Fukasawa, arXiv 2602.05241](https://arxiv.org/abs/2602.05241));
under local volatility it tends to 2 at short maturity
([Fukasawa 2026](https://arxiv.org/abs/2609.11586)). Hull and White estimate the minimum variance delta empirically
and find it beats daily-recalibrated stochastic volatility models for S&P 500 options
([2017](https://ideas.repec.org/a/eee/jbfina/v82y2017icp180-190.html)). Hagan and co-authors show local volatility
predicts smile moves opposite to the market's, which motivated SABR ([Managing Smile Risk](https://www.maths.univ-evry.fr/pages_perso/crepey/Finance/SABR.pdf)).

**India VIX.** NSE computes it from the best bid and ask of out-of-the-money Nifty options in the near and next
monthly expiries, with the CBOE method adapted to the Nifty order book, interpolated to 30 calendar days; it rolls to
the next pair with three trading days left ([NSE India VIX page](https://nseindia.com/products/content/equities/indices/india_vix.htm);
[ICICI Direct description](https://www.icicidirect.com/ilearn/futures-and-options/articles/what-is-volatility-index-how-it-impacts-options-pricing)).
It does not use the weekly expiry. The weekly ATM IV the system trades can diverge from it. Use the system's own
weekly IV. India VIX is at most a slow regime input.

**Inputs.** Per-strike IV each second (have), the future (have).

**Cost at 1 Hz.** A skew slope by finite difference and a few multiplications per strike: under 0.1 ms. Fitting R,
drifts, reversion speed and noise: offline, minutes.

**Evidence at 1 to 30 minutes.** The regimes and SSR are documented on S&P 500 and mostly at daily or longer
horizons. The short-maturity result (R near 2 under local volatility) is theory; the ultra-short-tenor oscillation of
ATM IV is from US data. Both are recent. For Nifty weekly options at minutes there is no published estimate that I found. This system's
own result is the best evidence: holding IV flat gave too-narrow ranges; a drawn IV scenario overshot at 60 s
(docs/41 13.1). The IV move matters and its size must be fitted, not assumed.

**Here.** Estimate `R` (or the spot-vol beta directly), the seasonal drift `d_K`, the reversion speed and residual
noise, by DTE bucket and moneyness, on the 15 sessions. Expiry days separately. The existing `ivz` veto (IV spike on
expiry days) suggests the residual has jumps; measure their size and frequency.

**Verdict. Adopt now** the empirical beta, drift and noise model. **Test** SABR per expiry as a smile parametrisation
with dynamics. **Skip** a full arbitrage-free surface model for now.

### 2.4 Realised volatility forecasting at intraday horizons

**Predicts.** The future's variance over the next `h` minutes. This is the numerator of the rent and the width of
every fan chart. It is the most predictable quantity in this problem.

**Mathematics.**

```
Seasonal adjustment:        r*_t = r_t / sqrt(u(m_t))       (u from the U-shape, by day type)

EWMA (RiskMetrics):         s2_t = lambda s2_(t-1) + (1 - lambda) r*_t^2
  RiskMetrics used lambda = 0.94 for daily data; at 1 s pick half-lives (30 s, 2 min, 10 min) instead

HAR (Corsi), intraday form for the next h minutes:
  log RV(t, t+h) = b0 + b1 log RV(last h) + b2 log RV(last 30 min) + b3 log RV(today so far)
                 + b4 log RV(yesterday) + log u(t, t+h) + e

Realized GARCH (Hansen, Huang, Shek), log-linear:
  r_t = sqrt(h_t) z_t
  log h_t = w + b log h_(t-1) + g log x_(t-1)
  log x_t = xi + f log h_t + tau(z_t) + u_t

Multiplicative component (Engle and Sokalska):
  r_(t,i) = sqrt(h_t s_i q_(t,i)) e_(t,i)     daily x diurnal x intraday GARCH

Forecast rent over h:   rent_f(h) = E[RV(t, t+h)] / (F^2 sigma^2 * dt(h, clock))
```

Sources: [RiskMetrics Technical Document 1996](https://www.msci.com/research-and-insights/paper/1996-riskmetrics-technical-document);
[Corsi 2009](https://econpapers.repec.org/RePEc:oup:jfinec:v:7:y:2009:i:2:p:174-196);
[Hansen, Huang and Shek 2012](https://repec.econ.au.dk/repec/creates/rp/10/rp10_13.pdf);
[Engle and Sokalska 2012](https://ideas.repec.org/a/oup/jfinec/v10yi1p54-83.html).

**Microstructure noise.** At 1 s, bid-ask bounce and price discreteness inflate realised variance. The two-scales
estimator ([Zhang, Mykland and Ait-Sahalia 2005](https://www.nber.org/papers/w10111.pdf)) and realised kernels
([Barndorff-Nielsen, Hansen, Lunde and Shephard 2008](https://econpapers.repec.org/RePEc:ecm:emetrp:v:76:y:2008:i:6:p:1481-1536))
correct it. A cheaper check: a signature plot of realised variance against sampling interval (1, 5, 15, 30 s); if
it is flat from 5 s, sample there. The forecaster already uses mid quotes, which removes most bounce.

**Rough volatility.** Log-volatility behaves like a rough process with Hurst exponent near 0.1, and this gives a
simple forecasting formula ([Gatheral, Jaisson and Rosenbaum 2018](https://arxiv.org/abs/1410.3394)). A challenger
for the variance forecast only.

**Inputs.** 1 s mids of the future (have); yesterday's realised variance (have in tapes); jump flags (section 2.6).

**Cost at 1 Hz.** EWMA at three half-lives and HAR terms: under 0.05 ms. Realized GARCH filter: same. Fitting:
offline, seconds to minutes.

**Evidence at 1 to 30 minutes.** Strong that volatility is persistent and seasonal. HAR is the standard daily
benchmark. Intraday components improve forecasts: Engle and Sokalska on 10-minute returns of 2,500 US stocks; a
periodicity-adjusted HAR improves forecasts across horizons
([Dumitru, Hizmeri and Izzeldin 2025](https://papers.ssrn.com/abstract=3393464)); pooled intraday realised
volatilities with time-of-day effects help one-day forecasts ([Zhang, Zhang, Cucuringu and Qian](https://arxiv.org/abs/2202.08962)).
Direct published tests at exactly 1 to 30 minutes ahead are fewer. This system's own evidence agrees: the
activity-only baseline, which includes realised volatility, is the model nothing beats (docs/45 7).

**Here.** A variance forecast for each horizon, seasonally adjusted by day type (expiry or not), with jumps split
out. Then a rent forecast in a consistent clock, per candidate. This is a forecast of the exact quantity the champion
trades on.

**Verdict. Adopt now** a seasonal multi-scale EWMA and log-HAR. **Test** Realized GARCH and the rough-volatility
forecast as challengers.

### 2.5 Short-horizon direction from microstructure

**Predicts.** The sign and size of the next mid-price changes.

**Mathematics.**

```
Order flow imbalance (Cont, Kukanov, Stoikov), event n at the best quotes:
  e_n = 1{Pb_n >= Pb_(n-1)} qb_n - 1{Pb_n <= Pb_(n-1)} qb_(n-1)
      - 1{Pa_n <= Pa_(n-1)} qa_n + 1{Pa_n >= Pa_(n-1)} qa_(n-1)
  OFI(t, t+dt) = sum of e_n;   dMid ~ beta * OFI, beta roughly inverse to depth

Queue imbalance:        I = qb / (qb + qa)
Weighted mid:           Pw = Pa * I + Pb * (1 - I)
Micro-price (Stoikov):  Pmicro = Mid + g(I, spread), g estimated from a Markov model of (I, spread) so that
                        Pmicro is the limit of expected future mids

Hawkes intensity:       lambda(t) = mu + sum over past events of alpha exp(-beta (t - t_i))

Options-implied forward against the future:   basis_t = F_fut,t - (K + C_K,t - P_K,t)
```

Sources: [Cont, Kukanov and Stoikov 2014](https://arxiv.org/abs/1011.6402);
[Stoikov 2018](https://ideas.repec.org/a/taf/quantf/v18y2018i12p1959-1966.html);
[Gould and Bonart 2016](https://arxiv.org/abs/1512.03492);
[Bacry, Mastromatteo and Muzy 2015](https://arxiv.org/abs/1502.04592);
[Easley, Lopez de Prado and O'Hara, VPIN, with the critique](https://papers.ssrn.com/abstract=2062450).

**Evidence at 1 to 30 minutes.**

- OFI explains price changes over the same interval well; it is mainly a contemporaneous relation.
- Queue imbalance predicts the **next** mid move, strongly for large-tick stocks, moderately for small-tick ones.
- The micro-price predicts short-term prices better than the mid or the weighted mid.
- Deep models on stationary order-flow inputs reach the best accuracy, but the effective horizon is about two average
  price changes ([Kolm, Turiel and Westray 2023](https://econpapers.repec.org/RePEc:bla:mathfi:v:33:y:2023:i:4:p:1044-1081)).
- VPIN: Andersen and Bondarenko argue it predicts volatility only because classification errors rise with
  volatility ([Review of Finance 2015 version](https://econpapers.repec.org/RePEc:oup:revfin:v:19:y:2015:i:1:p:1-54.)).
- Lead-lag: Nifty futures lead the spot index in price discovery
  ([IJOEM 2023](https://ideas.repec.org/a/eme/ijoemp/ijoem-07-2022-1097.html)). For options, Chakravarty, Gulen and
  Mayhew estimate about 17 to 18 % of price discovery in US equity options
  ([2004](https://www.bauer.uh.edu/rsusmel/Academic/SSRN-id1404988.pdf)), while Muravyev, Pearson and Broussard find
  no economically significant price discovery: when put-call parity disagrees with the stock, option quotes adjust
  ([2013](https://econpapers.repec.org/RePEc:eee:jfinec:v:107:y:2013:i:2:p:259-283)). Expect the parity forward
  to lag the future.
- At 30 minutes there is one documented pattern: the market's first half-hour return predicts its last half-hour
  return, predictive R-squared about 1.6 % on S&P 500 ETF data ([Gao, Han, Li and Zhou 2018](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)),
  linked to gamma hedging ([Baltussen, Da, Lammers and Martens 2021](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403)).

**Here.** The system records 1 s snapshots, not events, and the forecaster sees top-5 depth totals. True event-level
OFI cannot be computed. A 1 s best-level OFI and a micro-price can be approximated if the tape keeps best-level sizes.
docs/41 3.2 already found that flow and depth features did not raise direction skill. The literature says this is
expected: microstructure signals live at seconds, and the system's horizons are minutes.

**Inputs.** Best bid and ask sizes per second (check the tape), trades from last price and volume (have).

**Cost at 1 Hz.** Under 0.05 ms each.

**Verdict.** **Test** a 1 s micro-price offset and best-level OFI as features in the hazard model and the 30 to 60 s
drift, with a block ablation. **Test** a Hawkes-style intensity only as an activity input. **Skip** VPIN. **Skip**
options-led direction; keep the parity-forward basis as a data-quality check.

### 2.6 State-space and regime models

**Predicts.** A drift with honest uncertainty; the current regime (quiet, active, jumpy; trending or reverting);
whether the last second contained a jump.

**Mathematics.**

```
Local linear trend (Kalman), on seasonally adjusted ln F:
  y_t = mu_t + e_t,                e_t ~ N(0, H)
  mu_(t+1) = mu_t + nu_t + x_t,    x_t ~ N(0, Q_mu)
  nu_(t+1) = nu_t + z_t,           z_t ~ N(0, Q_nu)
  forecast mean over h: mu_t + nu_t h;  variance grows with h and, through the slope, with h^3

Markov switching (Hamilton): K states with (drift, variance, AR coefficient)_k, transition matrix A.
  Filter: p_t(k) proportional to f_k(y_t) * sum_j A(j,k) p_(t-1)(j)

Variance ratio over q seconds (Lo and MacKinlay):  VR(q) = Var(r over q) / (q Var(r over 1))
  VR above 1: trending; below 1: reverting

Jump test (Lee and Mykland), return r_i with bipower volatility over the previous K returns:
  sigma_i^2 = (1/(K-2)) sum |r_j| |r_(j-1)|,    L_i = r_i / sigma_i
  flag a jump when (|L_i| - C_n) / S_n exceeds beta* = -log(-log(1 - alpha))
  C_n and S_n are extreme-value constants in n given in the paper
```

Sources: [Durbin and Koopman, state space methods](https://econpapers.repec.org/RePEc:oxp:obooks:9780199641178);
[Hamilton 1989](https://ideas.repec.org/a/ecm/emetrp/v57y1989i2p357-84.html);
[Lo and MacKinlay 1988](https://web.mit.edu/~alo/www/Papers/lo-mackinlay-88.html);
[Lee and Mykland 2008](https://galton.uchicago.edu/%7Emykland/paperlinks/LeeMykland-2535.pdf). Later work flags an
error in the original critical region (use the maximum of the absolute statistic) and compares jump tests
([Dumitru and Urga](https://openaccess.city.ac.uk/id/eprint/6962/1/DumitruUrga%20%28manuscript%20accepted%29.pdf);
[arXiv 1708.09520](https://arxiv.org/pdf/1708.09520)). Check the constants against the paper before coding.

**Inputs.** 1 s future mids; the seasonal curve.

**Cost at 1 Hz.** Two-state Kalman step: about 0.02 ms. Three-state HMM filter step: about 0.02 ms. Jump test with
a rolling bipower sum: microseconds. Fitting: offline.

**Evidence at 1 to 30 minutes.** The Kalman filter is a principled smoother; it does not create predictability, and
the momentum features it would replace were weak (docs/41 3.3). Hamilton's model was built for business cycles.
Volatility regimes are real at intraday horizons (volatility clusters); trend regimes at minutes have weak published
support and would overfit on 15 sessions. Jump detection is well established. The champion's own `rt` rule already
uses a trend-efficiency ratio, which is a cousin of the variance ratio.

**Here.** Use the Kalman slope only as the drift input of the path engine, shrunk hard to zero. Use jump flags to
split variance into diffusive and jump parts and to clean the realised-variance inputs. A three-state volatility
regime as a feature.

**Verdict.** **Adopt now** jump detection. **Test** the Kalman drift and a three-state volatility HMM. **Skip** trend
or mean-reversion HMMs until there are many more sessions.

### 2.7 Path forecasting and barrier probabilities

**Predicts.** The full distribution of the future and of every candidate's bid at 1, 2, 3, 5, 10, 15 and 30 minutes;
the chance of each barrier event before each horizon.

**Mathematics.**

```
Future (log), horizon h, variance clock:
  X_h = X_0 + m(h) + sqrt(v(h)) Z (+ jumps)
  v(h) = forecast integrated variance from 2.4, seasonal;  m(h) = shrunk drift from 2.6 (+ any direction expert)

IV per strike:
  sigma_K(h) = sigma_K(0) + (R - 1) S_K (X_h - X_0) + d_K(h) + eta_K sqrt(h) eps,   corr(eps, Z) = rho_res

Premium (full repricing):  P_K(h) = B76(F_h, K, T_K - h, sigma_K(h)), bid = mid - half spread (spread model)

One-factor shortcut: if eta_K = 0, a call's premium is increasing in F_h and a put's decreasing
  (true while delta outweighs vega * d sigma / dF from the spot-vol link; check per strike), so
  q-quantile of P_K(h) = P_K evaluated at the q-quantile of F_h          (exact, no simulation)
With IV noise: 2-D Gauss-Hermite quadrature (for example 16 x 8 nodes) or 512 to 2,048 antithetic paths.

Decay-only line:  P_K(F_0, sigma_K(0) + d_K(h), T_K - h)
Break-even move at h:  the dF that solves P_K(F_0 + dF, ...) = P_K(0)
```

**First passage, closed form.** For Brownian motion with drift `nu` and volatility `s` starting at 0, with an upper
barrier `U` and a lower barrier `-L`:

```
P(hit U before -L) = (1 - exp(theta L)) / (exp(-theta U) - exp(theta L)),   theta = 2 nu / s^2
  nu = 0:  L / (U + L)
Single barrier b by horizon h:
  P(max over [0,h] >= b) = N((-b + nu h) / (s sqrt h)) + exp(2 nu b / s^2) N((-b - nu h) / (s sqrt h))
Discrete monitoring (Broadie, Glasserman, Kou): a barrier checked every dt behaves like a continuous barrier moved
  away from the start by beta s sqrt(dt),  beta = -zeta(1/2) / sqrt(2 pi) ~ 0.5826
```

Sources: [Broadie, Glasserman and Kou 1997](https://ideas.repec.org/a/bla/mathfi/v7y1997i4p325-349.html); the
two-barrier formula follows from the scale function of Brownian motion with drift (standard; for example Shreve,
*Stochastic Calculus for Finance II*). Two barriers with a finite horizon need a series or simulation.

**The Greek-barrier model: a structural baseline for the existing target.** Treat the bid as Brownian motion in
premium space, using Ito on the Greeks:

```
premium drift  nu_P = delta * nu_F + |Theta| (rent_f - 1)       (decay and gamma rent; vega drift optional)
premium vol    s_P  = |delta| * s_F
Entry at the ask A, bid starts at A - c (c = spread in points)
  U = 0.05 A + c        (bid must climb the spread too)
  L = 0.05 A - c
Zero drift:  P(+5 % first | one is hit) = L / (U + L) = (5 % - spread %) / 10 %
```

| Spread, % of ask | P(+5 % first), zero drift |
|---|---|
| 0.25 % | 47.5 % |
| 0.5 % | 45 % |
| 1 % | 40 % |
| 2 % | 30 % |

The observed rates at 300 s were 36.6 % up first and 42.9 % down first, a conditional 46 % (docs/41 3.1). That is
what a spread near 0.4 % to 0.5 % of premium and no skill would give; check it against the recorded `spread_pct`
distribution before relying on it. The model also says when decay matters. At three
days to expiry with rent 0.5, the chance moves only from 45 % to about 44 %. On expiry afternoon, decay of 1 to 5 % of
premium per minute makes the drift term large. The discrete-monitoring shift at 1 s is about 0.4 premium points for
a delta 0.56 option in the trading clock (illustration), about 4 to 5 % of a 5 % barrier on a 169-point premium:
small but not negligible. The barriers in premium space also move with time, because decay changes the future
level each barrier corresponds to; simulation handles that exactly.

**Stochastic volatility models.** Heston gives a closed form under a mean-reverting variance
([Heston 1993](https://ideas.repec.org/a/oup/rfinst/v6y1993i2p327-43.html)); SABR gives a smile with dynamics
([Hagan and co-authors 2002](https://www.maths.univ-evry.fr/pages_perso/crepey/Finance/SABR.pdf)). Over 30 minutes the
variance barely mean-reverts, so their main value is a consistent smile and its motion. Calibrating Heston every
second to a weekly chain is slow and unstable. SABR per expiry is cheap. For tenors under one week, the 2026
Edgeworth++ model is the specialised option ([arXiv 2603.29430](https://arxiv.org/abs/2603.29430)).

**Inputs.** Outputs of 2.2, 2.3, 2.4, 2.6; a spread model per contract (current spread and its recent average).

**Cost at 1 Hz.** One-factor quantile mapping, 12 contracts x 7 horizons x 5 quantiles: 420 Black-76 calls, under
0.3 ms. 2-D quadrature 16 x 8: about 11,000 calls, 1 to 2 ms. Simulation, 1,024 paths x 7 x 12: about 86,000 calls,
3 to 8 ms in numpy. Closed-form barriers: microseconds. Heston calibration: seconds, not per second.

**Evidence at 1 to 30 minutes.** A path forecast is only as good as its inputs. The system's own translator test is
the evidence: best tails at 60 s and 300 s, too narrow with flat IV (74 to 75 % coverage for an 80 % range), too wide
at 60 s with a drawn IV scenario (84.4 %) (docs/41 12.3, 13.1). So the structure works and the IV part needs fitting
plus an online coverage repair (section 2.8).

**Here.** This is the "next, then next, then next" the owner asked for. Every candidate gets a fan chart, a
decay-only line and barrier probabilities at seven horizons.

**Verdict. Adopt now** the one-factor fan chart, the decay-only line and the Greek-barrier model. **Test** quadrature
or simulation with IV noise and jumps. **Test** SABR. **Skip** Heston.

### 2.8 Self-improvement in retrospect

**Predicts.** Nothing new. It decides how much to trust each forecaster, repairs calibration and interval coverage,
and proves or disproves that learning helps.

**Rule zero.** A forecast made at `t` for horizon `h` is scored and used for any update only at `t + h`, when its
outcome has matured. The ledger and maturity queue already enforce this (docs/41 2.3). A feed gap is censoring, not an
outcome.

**Mathematics.**

```
Exponentially weighted average forecaster (prediction with expert advice):
  w_(i,t+1) proportional to w_(i,t) exp(-eta * loss_(i,t)),   forecast = sum_i w_i * p_i
  with log loss and eta = 1 this is a Bayesian mixture; regret against the best expert <= ln N

Hedge (Freund and Schapire): same update; regret O(sqrt(T ln N)) for bounded losses

Fixed share (Herbster and Warmuth), after each update:
  w_(i,t+1) <- (1 - a) w_(i,t+1) + a / N          tracks a best expert that switches; a ~ 1 / expected run length

Recursive least squares with forgetting factor lambda (memory about 1 / (1 - lambda) steps):
  k_t = P_(t-1) x_t / (lambda + x_t' P_(t-1) x_t)
  b_t = b_(t-1) + k_t (y_t - x_t' b_(t-1))
  P_t = (P_(t-1) - k_t x_t' P_(t-1)) / lambda

Dynamic model averaging (Raftery, Karny, Ettler), forgetting a:
  pi_(t|t-1,k) = pi_(t-1|t-1,k)^a / sum_j pi_(t-1|t-1,j)^a
  pi_(t|t,k) proportional to pi_(t|t-1,k) * p_k(y_t | past)

Online Platt scaling (Gupta and Ramdas):  p' = sigmoid(a logit(p) + b), (a, b) updated online on log loss

Adaptive conformal inference (Gibbs and Candes):
  alpha_(t+1) = alpha_t + gamma (alpha - err_t),   err_t = 1 if y_t fell outside the interval at level alpha_t
  for any data: | (1/T) sum err_t - alpha | <= (max(alpha_1, 1 - alpha_1) + gamma) / (gamma T)
```

Variants: DtACI tunes `gamma` online with experts ([Gibbs and Candes 2024](https://www.jmlr.org/papers/v25/22-1218.html));
AgACI aggregates several ACI runs and treats the upper and lower bounds separately
([Zaffran and co-authors 2022](https://arxiv.org/abs/2202.07282)); conformal PID control adds an integrator and a
"scorecaster" ([Angelopoulos, Candes and Tibshirani 2023](https://arxiv.org/abs/2307.16895)); SAOCP gives strongly
adaptive regret over every interval ([Bhatnagar and co-authors 2023](https://arxiv.org/abs/2302.07869)).

Other sources: [Cesa-Bianchi and Lugosi, *Prediction, Learning, and Games*](https://ece.iisc.ac.in/~aditya/Prediction_Learning_and_Games.pdf);
[Freund and Schapire 1997](https://khoury.northeastern.edu/home/vip/teach/IRcourse/6_ML/other_notes/freund_schapire_adaboost_journal.pdf);
[Herbster and Warmuth 1998](https://mlanthology.org/mlj/1998/herbster1998mlj-tracking);
[Raftery, Karny and Ettler 2010](https://sites.stat.washington.edu/raftery/Research/PDF/Karny2010.pdf);
[Gupta and Ramdas 2023](https://proceedings.mlr.press/v202/gupta23c.html);
[Gibbs and Candes 2021](https://arxiv.org/abs/2106.00170);
[Venn-Abers predictors, Vovk and Petej](https://arxiv.org/abs/1211.0025) (isotonic calibration with a validity
guarantee under exchangeability).

**Delayed feedback.** Outcomes arrive `h` later. Delay multiplies regret in adversarial settings and adds to it in
stochastic ones ([Joulani, Gyorgy and Szepesvari 2013](https://proceedings.mlr.press/v28/joulani13.html)). Practical
rule: keep one learner state per horizon, update when outcomes mature, and give each **independent window** one unit
of weight. Origins every 5 s with a 300 s horizon overlap 60-fold; updating on each would count one move 60 times.

**Proper scores.**

```
Log score (categorical up / down / neither):  -ln p(observed)
Brier:                                        sum_j (p_j - y_j)^2
Pinball loss at quantile q:                   max(q (y - yhat), (q - 1)(y - yhat))
CRPS of N(mu, s^2) at y, z = (y - mu)/s:      s [ z (2 N(z) - 1) + 2 phi(z) - 1/sqrt(pi) ]
CRPS from quantiles:                          about (2/Q) * sum over Q evenly spaced quantiles of pinball loss
```

The Gaussian CRPS formula is from [Gneiting, Raftery, Westveld and Goldman 2005](https://sites.stat.washington.edu/raftery/Research/PDF/gneiting2005.pdf);
the theory of proper scores is reviewed by Gneiting and Raftery (JASA 2007), and implementations are documented in
[scoringRules](https://arxiv.org/abs/1709.04743).

**The frozen control.** Every adaptive forecaster runs beside its own frozen copy, fixed at the session open, on the
same inputs, written to the same ledger. Learning is shown to help only if the adaptive copy beats the frozen copy on
the pre-declared proper score, on sessions after the freeze, with a paired day-block interval that excludes zero
(section 2.11). docs/41 3.5 already found the binned calibrator slightly worse than frozen. That is the right kind of
result to keep.

**Inputs.** The forecast ledger and matured outcomes (have).

**Cost at 1 Hz.** Microseconds per update.

**Evidence.** The guarantees are distribution-free: regret bounds and long-run coverage hold for any data. They say
nothing about absolute accuracy. If no expert has skill, the weights find the best of no skill. Gibbs and Candes
test ACI on stock volatility forecasting and show it holds coverage through 2008 where a fixed method undershoots.
Coverage is an average over time, not per trade, and not on the subset the engine selects; conformal selection with
error control on a selected subset is a separate method ([Jin and Candes 2023](https://jmlr.org/papers/v24/22-1176.html)).

**Verdict. Adopt now:** maturity-only scoring, fixed-share weights over a small roster with a frozen control, DtACI
on every path quantile, online Platt on probabilities (shadow). **Test** RLS with forgetting for the variance
coefficients. **Skip** contextual bandits and reinforcement learning, as docs/44 already says.

### 2.9 Machine learning candidates

| Model | What it needs | Published evidence | Fit here |
|---|---|---|---|
| Gradient boosting (XGBoost, LightGBM) | tabular rows; thousands of independent samples | tree models beat deep nets on medium tabular data, about 10,000 samples ([Grinsztajn, Oyallon and Varoquaux 2022](https://arxiv.org/abs/2207.08815)) | tried: AUC 0.598 against 0.609, side AUC 0.52 to 0.53, trading check lost (docs/41 3.2) |
| Temporal convolutional network | many long sequences | beat LSTMs on generic sequence tasks ([Bai, Kolter and Koltun 2018](https://arxiv.org/abs/1803.01271)) | 15 sessions; no |
| Transformers (for example TFT) | large multi-series data | strong on multi-horizon benchmarks ([Lim and co-authors](https://arxiv.org/abs/1912.09363)) | no |
| DeepLOB | 10-level book, 40 features, 100 most recent states; one year of LSE data, more than 134 million samples; horizons 20 to 100 events ([Zhang, Zohren and Roberts 2019](https://arxiv.org/abs/1808.03668)) | a benchmark of 15 such models found a significant drop on new data ([Prata and co-authors 2024](https://arxiv.org/abs/2308.01915)); the effective horizon is about two price changes (Kolm and co-authors) | top-5 totals at 1 Hz; minutes, not events; no |
| Universal deep models | billions of US quotes and trades ([Sirignano and Cont](https://arxiv.org/abs/1803.06917)) | universal features exist at high frequency | far beyond this data |

**Realistic data size.** 15 sessions of 375 minutes. Non-overlapping windows: 5,625 of 1 minute, 1,125 of 5 minutes,
375 of 15 minutes, about 187 of 30 minutes. 92 champion fills. Each new session adds one independent day. Rows are
many; independent evidence is small.

**Cost at 1 Hz.** Boosting with 200 depth-3 trees on 12 rows: about 0.1 to 1 ms (estimate). A small TCN on CPU: 1 to
5 ms. DeepLOB-size models on CPU: tens of milliseconds.

**Verdict.** **Test** gradient boosting later, at 40 or more sessions, with monotone constraints, only as one expert
inside the weighting of 2.8. **Skip** TCN, transformers and DeepLOB-style models now.

### 2.10 Option-positioning signals

**Predicts.** Claimed: where hedging flows dampen or amplify moves; where the index will be pinned at expiry.

**Mathematics.**

```
Gamma exposure per strike (dealer sign ASSUMED):
  GEX_K = Gamma_K * OI_K * lot * F^2 * 0.01        calls +, puts -     (rupees per 1 % move)
Net GEX = sum over K;  "flip" = the F at which net GEX changes sign
Max pain = the strike that minimises the total intrinsic value paid to option holders at expiry
```

The sign convention comes from a practitioner white paper (SqueezeMetrics, "Gamma Exposure"), which assumes dealers
are long calls and short puts. Vendors differ; it is a heuristic
([description](https://slopeofhope.com/wp-content/uploads/2020/11/GEX-white_paper.pdf)). `apex/engine/gex.py` already
says the sign may be wrong on Nifty and keeps GEX as an advisor only.

**Evidence.**

| Claim | Evidence | Status |
|---|---|---|
| Net market-maker gamma changes underlying volatility | Ni, Pearson, Poteshman and White: hedge rebalancing affects stock volatility and large moves, with the sign set by net gamma ([2021](https://econpapers.repec.org/RePEc:oup:rfinst:v:34:y:2021:i:4:p:1952-1986.)) | evidence, US single stocks |
| Gamma hedging drives end-of-day momentum | Baltussen and co-authors, 60 futures 1974 to 2020 ([2021](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403)) | evidence, sign inferred |
| 0DTE gamma raises index volatility | Dim, Eraker and Vilkov find no evidence; aggregate 0DTE gamma is inversely related to intraday volatility ([summary](https://harbourfrontquant.substack.com/p/impact-of-zero-dte-options-on-the)); Cboe reports customer 0DTE flow is balanced ([Cboe](https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options)) | contested, US |
| Pinning at strikes on expiry | stocks cluster at strikes on expiry ([Ni, Pearson and Poteshman 2005](https://ideas.repec.org/a/eee/jfinec/v78y2005i1p49-87.html)); S&P 500 futures pinned to the ATM strike on serial option expiries ([Golez and Jackwerth 2012](https://ideas.repec.org/a/eee/jfinec/v106y2012i3p566-585.html)) | evidence, US |
| Index drifts to max pain | one academic paper reports an effect in small, illiquid stocks (secondary summaries of Filippou, Garcia-Ares and Zapatero 2022); nothing for indices found | folklore for Nifty |
| An OI "wall" is a floor or ceiling | dealers short puts sell more as the index falls; a put wall is not automatically support (docs/42 5.4) | folklore |

**Inventory sign in India.** Open interest counts contracts; every one has a long and a short. Who is short decides
the sign. NSE publishes participant-wise open interest (client, DII, FII, proprietary) once a day after the close,
not by strike and not intraday ([description](https://algotest.in/blog/participant-wise-open-interest/)). SEBI's
studies show individual traders are a large group and mostly lose (93 % over FY22 to FY24, about 91 % in FY25)
([Business Standard](https://www.business-standard.com/amp/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html)).
That suggests writers are often professionals, but it does not tell whether they hedge, or the strike-level sign.

**Inputs.** REST chain OI (have, nearest weekly, polled), IV per strike (have).

**Cost at 1 Hz.** Under 1 ms per chain poll.

**Here.** Two narrow tests, each pre-registered with an ablation: (1) unsigned gamma concentration near the forward
as a feature for the next 15 to 30 minutes' realised variance on expiry days; (2) distance to the highest-OI strike
in the last 90 minutes of expiry day as a drift feature in the path engine.

**Verdict.** **Skip** GEX-sign rules, max pain and OI walls as rules. **Test** the two features above, expiry days only.

### 2.11 Evaluation

**Walk-forward by session.** Fit, choose and calibrate on sessions before `d`; score `d`. docs/45 7 already does this.

**Purging and embargo.** Remove any training label whose window overlaps the test window, and leave a gap after the
test fold ([Lopez de Prado, purged cross-validation](https://en.wikipedia.org/wiki/Purged_cross-validation)). With
whole-session folds and horizons of 30 minutes or less, purging happens by construction, except for features that
reach into the previous day.

**Overlapping labels.** Effective sample size is about `N * spacing / h`. Prefer per-session statistics. If a
pooled test is needed, use HAC (Newey-West) standard errors with a lag of at least `h / spacing`.

**Day-block bootstrap.** Resample sessions with replacement and recompute the paired score difference; or the
stationary bootstrap for runs of days ([Politis and Romano 1994](https://gnosis.library.ucy.ac.cy/handle/7/57533)).

**Comparing forecasts.** Diebold-Mariano on loss differences, with the Harvey, Leybourne and Newbold small-sample
correction ([statsmodels](https://www.statsmodels.org/dev/generated/statsmodels.tsa.stattools.diebold_mariano_test.html)).

**Multiple trials.** Keep the trial registry (docs/44 8). The probability of backtest overfitting can be estimated by
combinatorially symmetric cross-validation ([Bailey and co-authors 2017](https://www.risk.net/journal-of-computational-finance/2471206/the-probability-of-backtest-overfitting)).

**How many forward sessions.** From docs/45 7, the hazard model's direction gain was +0.038 with a 90 % day-block
interval of +0.008 to +0.071 on 10 sessions. That implies a per-session spread of about 0.06. To show a gain of
size `D` with a 90 % interval clear of zero needs about `(1.645 * 0.06 / D)^2` sessions:

| Gain in direction AUC | Sessions needed |
|---|---|
| 0.04 | about 6 |
| 0.02 | about 25 |
| 0.01 | about 100 |

Rough, but it sets expectations: small improvements take months of live sessions to prove.

**Verdict. Adopt now** (most of it exists): session walk-forward, per-session scoring, day-block intervals, frozen
control, trial registry, Diebold-Mariano as a second check.

---

## 3. Verdicts and costs at a glance

Costs are estimates per second at 1 Hz in numpy on a laptop, not measurements. Measure on an idle machine before
anything goes live.

| Method | Predicts | Cost per second | Evidence at 1-30 min | Verdict |
|---|---|---|---|---|
| Greek translator and P&L attribution | premium change from scenario | about 0.1 ms | identity; local test good (docs/41) | adopt now |
| Variance clock, realised-decay tables | decay per minute by strike | microseconds | direction of effect strong (Nifty day-night); detail must be measured | adopt now |
| IV beta, drift, noise model | strike IV moves | under 0.1 ms | US regimes; own range tests | adopt now |
| SABR per expiry | smile and its motion | 1-5 ms per refit, every 30-60 s | daily and longer | test |
| Seasonal EWMA and log-HAR variance | realised variance, rent | under 0.05 ms | strong (persistence, seasonality) | adopt now |
| Realized GARCH, rough volatility | realised variance | under 0.05 ms | daily strong, intraday fewer tests | test |
| Micro-price, 1 s OFI | next seconds' direction | under 0.05 ms | strong at seconds, fades by minutes | test |
| VPIN | toxicity | small | contested | skip |
| Hawkes intensity | activity | small | good for clustering | test (activity only) |
| Kalman drift | drift with uncertainty | 0.02 ms | no direction gain expected | test (as path drift) |
| Volatility HMM, 3 states | regime | 0.02 ms | volatility regimes real | test |
| Trend HMM | trend regime | 0.02 ms | weak, overfits | skip |
| Lee-Mykland jumps | jump flags | microseconds | well established | adopt now |
| One-factor fan chart, decay line | paths | under 0.3 ms | structure validated in own tests | adopt now |
| Greek-barrier closed form | +x % before -x % | microseconds | consistent with recorded base rates (spread check pending) | adopt now |
| Quadrature or simulation with IV noise | paths | 1-8 ms | needed for coverage | test |
| Heston | smile, paths | seconds to calibrate | little at minutes | skip |
| Fixed share, DtACI, online Platt, frozen control | weights, coverage, calibration | microseconds | distribution-free guarantees | adopt now |
| Gradient boosting expert | any target | 0.1-1 ms | tried, no gain on 15 sessions | test at 40+ sessions |
| TCN, transformers, DeepLOB | sequences | 1-50 ms | data-hungry, poor transfer | skip |
| GEX sign, max pain, OI walls | levels | under 1 ms | folklore or contested | skip as rules |
| Gamma concentration, OI distance on expiry days | variance, drift | under 1 ms | pinning evidence in US | test |

---

## 4. Ranked recommendation (a)

Order by three questions: is the target predictable, does it serve the champion's actual decisions, and is it cheap
and testable on this data.

**First: the decay and movement clock.**
1. Realised-decay tables from the tapes: decay per minute as calendar theta plus vega times measured IV drift, by
   standardised moneyness, days to expiry, minute of day, expiry or not, open-to-close and close-to-open (2.2).
2. The `kappa` test: which clock does the market use intraday on Nifty weeklies (2.2).
3. A seasonal multi-scale variance forecast for 1 to 30 minutes, jumps split out (2.4, 2.6).
4. A rent forecast per candidate per horizon in one consistent clock, beside the champion's own rent, shadow only.
5. P&L attribution of every champion trade into delta, gamma, theta, vega and residual (2.1).

Why first: volatility and decay are the predictable part; the champion trades on rent; the owner's complaint about
decay is answered directly; no new data is needed.

**Second: the structural path engine.**
1. Future distribution at 1, 2, 3, 5, 10, 15, 30 minutes from the variance forecast and a drift shrunk to zero (2.7).
2. IV per strike from the fitted beta, drift and noise (2.3).
3. Full repricing: fan chart of each candidate's bid, the decay-only line, the break-even move (2.7).
4. The Greek-barrier model as a structural expert beside the hazard model, scored on the same origins (2.7).

Why second: it is the "next, then next" output and depends on the first step's inputs.

**Third: live self-scoring and online weighting.**
1. Maturity-only scoring of every quantile and probability: pinball, CRPS, log score, coverage, by horizon (2.8).
2. Fixed-share weights over a roster of at most five experts, one unit of weight per independent window (2.8).
3. DtACI on every path interval, by horizon; online Platt on probabilities (2.8).
4. A frozen control for each adaptive part; daily report with day-block intervals (2.8, 2.11).

Why third: it is how the system improves and proves it. It is cheap, but it needs the first two to have something
worth weighting.

**Later, only if the above is in place:** micro-price and 1 s OFI features (2.5); volatility HMM (2.6); expiry-day
positioning features (2.10); a gradient-boosting expert at 40 or more sessions (2.9).

**Not to build:** a bigger direction classifier; DeepLOB, TCN or transformer models; VPIN; GEX-sign, max-pain or
OI-wall rules; per-second Heston calibration.

---

## 5. Design sketch: a path forecaster with its own scoring (b)

Proposed names; module boundaries follow docs/44 section 10 (live code in `apex/predict/`, builders and trainers in
`research/predict/`). Shadow only. It records; it does not gate the champion, the pool or the Conductor.

### 5.1 Outputs, every second (or every 5 s for non-held candidates)

| Object | Fields | Horizons |
|---|---|---|
| Future | q10, q25, q50, q75, q90 of F; drift and its standard error; forecast variance; jump-mixture weight | 60, 120, 180, 300, 600, 900, 1,800 s |
| Each candidate contract | q10 to q90 of the bid; expected bid; decay-only bid; break-even move; P(+x % before -x %) for x = 5 % and the champion's own floors; rent forecast | same |
| Clock | `tau_var` to expiry; minute weight `u(m)`; implied variance per minute in calendar and variance clocks | |
| Trust | support distance, inputs missing, quote age, model disagreement (direct against structural), current interval coverage | |

Candidates are the union of the engine's executable picks, pending orders, held contracts and contracts with open
outcomes (docs/42 4.C), plus up to two strikes either side of each pick.

### 5.2 Per-second order

1. **Shared state, once.** Seasonally adjusted 1 s return of the future; jump test; three EWMA variances; HAR terms;
   Kalman level and slope; parity forward and basis check; minute weight `u(m)`.
2. **Per expiry.** `tau_var`; ATM IV in both clocks; skew slope by finite difference; every 30 to 60 s, a SABR or
   quadratic smile refit (test only).
3. **Future forecast.** For each horizon: `v(h) = sum of u(m) * s2_forecast` over the next `h` minutes, plus jump
   variance; `m(h) = shrink * slope * h` with shrink fitted chronologically (expect near zero); quantiles.
4. **IV forecast per candidate.** `E[d sigma_K(h)] = (R - 1) S_K E[d ln F] + d_K(m, h) - k (sigma_K - sigma_bar_K) h`;
   residual `eta_K sqrt(h)`.
5. **Premium paths.** One-factor quantile mapping with IV a function of F; 2-D quadrature for IV noise as the
   challenger; decay-only line; break-even move; bid = mid minus a half-spread forecast.
6. **Barriers.** Greek-barrier closed form with spread, decay drift and the 1 s discrete-monitoring shift; simulation
   check offline.
7. **Combine.** Fixed-share weighted mixture of experts per target and horizon: for probabilities a weighted
   average; for quantiles a weighted average of quantiles (quantile averaging), then sorted; then the ACI adjustment
   of the interval levels.
8. **Write.** One record per sampled origin to the forecast ledger, with artefact hashes, as now.
9. **Mature.** Outcomes due this second: score each expert and the mixture; update weights, ACI levels and Platt
   parameters, one unit per independent window.

### 5.3 The first roster

| # | Member | Frozen or adaptive |
|---|---|---|
| 1 | Expert: activity-only climatology, empirical quantiles and rates by DTE, minute, premium and spread bucket | frozen |
| 2 | Expert: hazard model (docs/45 7), for barrier probabilities | frozen |
| 3 | Expert: structural path model (this section), parameters fitted on past sessions | frozen at the open |
| 4 | Expert: structural path model with RLS-with-forgetting variance coefficients and online IV drift | adaptive |
| 5 | Not an expert: the fixed-share mixture of 1 to 4, with ACI and Platt on top | adaptive; its frozen twin is the same mixture with weights, ACI levels and Platt parameters fixed at the open |

### 5.4 Scoring, each matured outcome

| Target | Score | Report |
|---|---|---|
| Future and premium quantiles | pinball at each quantile, CRPS from quantiles | by horizon, DTE bucket, expiry or not |
| Interval | coverage hit and width | rolling, and on the subset the champion traded |
| Barrier events | three-way log score and Brier, with censoring kept apart | by horizon |
| Rent | log score of the realised ratio against the forecast distribution | by horizon |
| Decay-only line | error of the decay forecast on intervals where the future ended within a small band of its start | by moneyness and minute |

### 5.5 Online weighting rules (fixed before the first live session)

- Learning rate `eta = 1` for log-score targets; for pinball targets, a fixed `eta` chosen on past sessions only.
- Fixed share `a = 1 / (number of independent windows in one session)` per horizon: allow about one switch a day.
- One state per horizon. Updates only from matured outcomes. One unit of weight per independent window.
- ACI `gamma` from DtACI's grid; target 80 % for q10 to q90 and 50 % for q25 to q75.
- Weights, ACI levels and Platt parameters persist across restarts, with version and time.
- A frozen twin of every adaptive part runs beside it and is scored the same way.

### 5.6 Compute budget (estimates)

| Stage | Per second |
|---|---|
| Shared state | under 0.3 ms |
| Clock and smile per expiry | under 0.2 ms (a smile refit every 30 to 60 s: 1 to 5 ms when it runs) |
| One-factor paths, 12 candidates x 7 horizons x 5 quantiles | under 0.3 ms |
| 2-D quadrature challenger | 1 to 2 ms |
| Barriers, mixing, maturity updates | under 0.2 ms |
| **Total** | **about 1 to 3 ms** |

The engine's idle step was 28 ms median and 97 ms at the 95th percentile (docs/45 5); the current forecast service
was 3.7 ms per second under the profiler (docs/41 12.2). Following the owner's step-time rule, measure on an idle
machine before any per-trade field goes live, and run the challenger in a side process if the step grows.

### 5.7 Tests before anything is live

1. Greek attribution sums to full repricing within tolerance on synthetic and recorded seconds.
2. Clock invariance: `sigma_cal^2 T_cal = sigma_var^2 tau_var` reproduces the same premium.
3. Barrier closed form against simulation, with and without drift, at 1 s monitoring.
4. Quantiles are ordered and monotone in F for each right.
5. No update before maturity; no update from a censored outcome; one unit per window.
6. Parity: offline builder and live service give the same numbers on the same tape.
7. Restart: weights, ACI levels and Platt parameters survive and resume.
8. Missing inputs give an explicit unavailable state, never a guess.

### 5.8 Rollout and acceptance

1. Offline on the 15 sessions, walk-forward: every expert and the mixture scored against the activity climatology.
   Report, including failures. A research run needs the owner's go-ahead and a stated size first.
2. Freeze; then shadow in the live engine, record only.
3. Acceptance, declared before the first forward session: the mixture beats the climatology and its own frozen twin
   on CRPS and on barrier log score, with day-block 90 % intervals clear of zero; interval coverage within 78 to 82 %
   overall and on expiry days separately; latency within budget.
4. Only then do docs/44 M3 experiments (admission, timing, continuation) use these outputs, each against its own
   matched control.

---

## 6. What the owner should and should not expect (c)

**Should expect.**
- Honest fan charts for the future and each candidate at seven horizons, with a decay-only line, so "what happens
  next, then next" is visible every second.
- Better estimates of movement and decay. These are the predictable parts and the champion's rent depends on them.
- A clear split of every trade's result into direction, movement, decay and IV change.
- Forecasts that say when they are unsure, and intervals whose coverage is repaired online.
- A measured answer to "does the market charge an intraday buyer calendar decay or less?", from the 15 recorded
  sessions once the owner approves that research run, then confirmed on forward sessions.

**Should not expect.**
- Strong direction calls. Given a 5 % move, the best models rank the side at 0.54 against 0.50 (docs/45 7). The
  literature's strong direction signals live at seconds and need event-level order books.
- "No losing trade." A forecaster makes probabilities, not certainties. If each trade wins with probability `p`, the
  chance of `n` wins in a row is `p^n`:

| Win probability per trade | 10 trades without a loss | 20 trades without a loss |
|---|---|---|
| 0.59 (champion's 54 of 92, docs/42 3) | 0.5 % | 0.003 % |
| 0.70 | 2.8 % | 0.08 % |
| 0.90 | 34.9 % | 12.2 % |

- Even with zero skill and zero decay, the spread alone makes "+5 % before -5 %" less likely than even (section 2.7).
- Quick proof. A real improvement of 0.02 in direction AUC needs about 25 forward sessions to show (section 2.11).
  Fifteen recorded sessions are 15 independent days, whatever the row count.
- A forecaster cannot guarantee profit. Under the owner's all-in rule there is no position sizing, so a forecast can
  only act through which trades, when, which contract and when to exit. Each trade's outcome variance stays fully in
  the account.
- Larger models to fix this. The data supports small, structural models with honest scoring now; it does not support
  deep sequence models.

The realistic aim: fewer entries into conditions where movement will not pay decay, better contract choice across
strikes given decay, and exits informed by a path forecast, each proven against a frozen control on sessions the
models have not seen.

---

## 7. References

Papers and books (links checked during this research; some full texts are paywalled, and abstracts were used there).

1. Ahmad, R., Wilmott, P. (2005). Which free lunch would you like today, Sir? Wilmott. https://wilmott.com/?p=1358
2. Andersen, T., Bollerslev, T. (1997). Intraday periodicity and volatility persistence in financial markets. Journal of Empirical Finance 4. https://ideas.repec.org:443/a/eee/empfin/v4y1997i2-3p115-158.html
3. Andersen, T., Bondarenko, O. (2015). Assessing measures of order flow toxicity. Review of Finance 19. https://econpapers.repec.org/RePEc:oup:revfin:v:19:y:2015:i:1:p:1-54.
4. Angelopoulos, A., Candes, E., Tibshirani, R. (2023). Conformal PID control for time series prediction. https://arxiv.org/abs/2307.16895
5. Bacry, E., Mastromatteo, I., Muzy, J.-F. (2015). Hawkes processes in finance. https://arxiv.org/abs/1502.04592
6. Bai, S., Kolter, J. Z., Koltun, V. (2018). An empirical evaluation of generic convolutional and recurrent networks for sequence modeling. https://arxiv.org/abs/1803.01271
7. Bailey, D., Borwein, J., Lopez de Prado, M., Zhu, Q. (2017). The probability of backtest overfitting. Journal of Computational Finance 20(4). https://www.risk.net/journal-of-computational-finance/2471206/the-probability-of-backtest-overfitting
8. Bakshi, G., Kapadia, N. (2003). Delta-hedged gains and the negative market volatility risk premium. Review of Financial Studies 16. https://ideas.repec.org/a/oup/rfinst/v16y2003i2p527-566.html
9. Baltussen, G., Da, Z., Lammers, S., Martens, M. (2021). Hedging demand and market intraday momentum. Journal of Financial Economics 142. https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403
10. Bandi, F., Fusari, N., Reno, R. (2023). 0DTE option pricing. https://faculty.essec.edu/en/research/15649-0dte-option-pricing
11. Bandi, F., Fusari, N., Gazzani, G., Reno, R. (2026). Ultra-short-term volatility surfaces. https://arxiv.org/abs/2603.29430
12. Barndorff-Nielsen, O., Hansen, P., Lunde, A., Shephard, N. (2008). Designing realized kernels. Econometrica 76. https://econpapers.repec.org/RePEc:ecm:emetrp:v:76:y:2008:i:6:p:1481-1536
13. Beckmeyer, H., Branger, N., Gayda, L. (2023). Retail traders love 0DTE options... but should they? https://papers.ssrn.com/abstract=4404704
14. Bhat, Pandey and Nageswara Rao (2024). The asymmetry in day and night option returns: evidence from an emerging market. Journal of Futures Markets 44(8). https://ideas.repec.org/a/wly/jfutmk/v44y2024i8p1320-1337.html
15. Bhatnagar, A., Wang, H., Xiong, C., Bai, Y. (2023). Improved online conformal prediction via strongly adaptive online learning. https://arxiv.org/abs/2302.07869
16. Brenner, M., Subrahmanyam, M. (1988). A simple formula to compute the implied standard deviation. Financial Analysts Journal 44(5). https://scilit.com/publications/606a61fa3b0b8ee01f6b8eaa8d248d65
17. Broadie, M., Glasserman, P., Kou, S. (1997). A continuity correction for discrete barrier options. Mathematical Finance 7. https://ideas.repec.org/a/bla/mathfi/v7y1997i4p325-349.html
18. Carr, P., Madan, D. (1998). Towards a theory of volatility trading. https://www.next-finance.net/IMG/pdf/Towardsvoltrading.pdf
19. Castagna, A., Mercurio, F. (2007). The vanna-volga method for implied volatilities. Risk. https://www.risk.net/derivatives/equity-derivatives/1500224/vanna-volga-method-implied-volatilities
20. Cesa-Bianchi, N., Lugosi, G. (2006). Prediction, Learning, and Games. Cambridge University Press. https://ece.iisc.ac.in/~aditya/Prediction_Learning_and_Games.pdf
21. Chakravarty, S., Gulen, H., Mayhew, S. (2004). Informed trading in stock and option markets. Journal of Finance 59. https://www.bauer.uh.edu/rsusmel/Academic/SSRN-id1404988.pdf
22. Cont, R., Kukanov, A., Stoikov, S. (2014). The price impact of order book events. Journal of Financial Econometrics 12. https://arxiv.org/abs/1011.6402
23. Corsi, F. (2009). A simple approximate long-memory model of realized volatility. Journal of Financial Econometrics 7. https://econpapers.repec.org/RePEc:oup:jfinec:v:7:y:2009:i:2:p:174-196
24. Dacorogna, M., Muller, U., Nagler, R., Olsen, R., Pictet, O. (1993). A geographical model for the daily and weekly seasonal volatility in the foreign exchange market. Journal of International Money and Finance 12. https://econpapers.repec.org/RePEc:eee:jimfin:v:12:y:1993:i:4:p:413-438
25. Daglish, T., Hull, J., Suo, W. (2007). Volatility surfaces: theory, rules of thumb, and empirical evidence. Quantitative Finance 7. https://ideas.repec.org/a/taf/quantf/v7y2007i5p507-524.html
26. Derman, E. (1999). Regimes of volatility. Risk. https://emanuelderman.com/regimes-of-volatility/
27. Diebold, F., Mariano, R. (1995). Comparing predictive accuracy; with the Harvey, Leybourne, Newbold (1997) correction. https://www.statsmodels.org/dev/generated/statsmodels.tsa.stattools.diebold_mariano_test.html
28. Dumitru, A.-M., Hizmeri, R., Izzeldin, M. (2025). Forecasting the realized variance in the presence of intraday periodicity. Journal of Banking and Finance. https://papers.ssrn.com/abstract=3393464
29. Dumitru, A.-M., Urga, G. Identifying jumps in financial assets: a comparison between nonparametric jump tests. https://openaccess.city.ac.uk/id/eprint/6962/1/DumitruUrga%20%28manuscript%20accepted%29.pdf
30. Durbin, J., Koopman, S. J. (2012). Time Series Analysis by State Space Methods, second edition. Oxford University Press. https://econpapers.repec.org/RePEc:oxp:obooks:9780199641178
31. Engle, R., Sokalska, M. (2012). Forecasting intraday volatility in the US equity market. Multiplicative component GARCH. Journal of Financial Econometrics 10. https://ideas.repec.org/a/oup/jfinec/v10yi1p54-83.html
32. Fernandez-Perez, A., Frijns, B., Tourani-Rad, A., Webb, R. (2016). The intraday properties of the VIX and the VXO (summary). https://www.cxoadvisory.com/volatility-effects/intraday-and-intraweek-vix-behaviors/
33. French, K., Roll, R. (1986). Stock return variances: the arrival of information and the reaction of traders. Journal of Financial Economics 17. https://www-2.rotman.utoronto.ca/~kan/3032/pdf/AssetPricingAnomalies/French_Roll_JFE_1986.pdf
34. Freund, Y., Schapire, R. (1997). A decision-theoretic generalization of on-line learning and an application to boosting. Journal of Computer and System Sciences 55. https://khoury.northeastern.edu/home/vip/teach/IRcourse/6_ML/other_notes/freund_schapire_adaboost_journal.pdf
35. Fukasawa, M. (2026). Short-maturity skew stickiness ratio under local volatility. https://arxiv.org/abs/2609.11586
36. Gao, L., Han, Y., Li, S. Z., Zhou, G. (2018). Market intraday momentum. Journal of Financial Economics 129. https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414
37. Gatheral, J., Jaisson, T., Rosenbaum, M. (2018). Volatility is rough. Quantitative Finance 18. https://arxiv.org/abs/1410.3394
38. Gibbs, I., Candes, E. (2021). Adaptive conformal inference under distribution shift. NeurIPS. https://arxiv.org/abs/2106.00170
39. Gibbs, I., Candes, E. (2024). Conformal inference for online prediction with arbitrary distribution shifts. JMLR 25. https://www.jmlr.org/papers/v25/22-1218.html
40. Gneiting, T., Raftery, A., Westveld, A., Goldman, T. (2005). Calibrated probabilistic forecasting using ensemble model output statistics and minimum CRPS estimation. Monthly Weather Review 133. https://sites.stat.washington.edu/raftery/Research/PDF/gneiting2005.pdf
41. Golez, B., Jackwerth, J. (2012). Pinning in the S&P 500 futures. Journal of Financial Economics 106. https://ideas.repec.org/a/eee/jfinec/v106y2012i3p566-585.html
42. Gould, M., Bonart, J. (2016). Queue imbalance as a one-tick-ahead price predictor in a limit order book. https://arxiv.org/abs/1512.03492
43. Grinsztajn, L., Oyallon, E., Varoquaux, G. (2022). Why do tree-based models still outperform deep learning on tabular data? https://arxiv.org/abs/2207.08815
44. Gupta, C., Ramdas, A. (2023). Online Platt scaling with calibeating. ICML. https://proceedings.mlr.press/v202/gupta23c.html
45. Hagan, P., Kumar, D., Lesniewski, A., Woodward, D. (2002). Managing smile risk. Wilmott. https://www.maths.univ-evry.fr/pages_perso/crepey/Finance/SABR.pdf
46. Hamilton, J. (1989). A new approach to the economic analysis of nonstationary time series and the business cycle. Econometrica 57. https://ideas.repec.org/a/ecm/emetrp/v57y1989i2p357-84.html
47. Hansen, P., Huang, Z., Shek, H. (2012). Realized GARCH. Journal of Applied Econometrics 27. https://repec.econ.au.dk/repec/creates/rp/10/rp10_13.pdf
48. Hasbrouck, J. (1995). One security, many markets: determining the contributions to price discovery. Journal of Finance 50. https://ideas.repec.org/a/bla/jfinan/v50y1995i4p1175-99.html
49. Herbster, M., Warmuth, M. (1998). Tracking the best expert. Machine Learning 32. https://mlanthology.org/mlj/1998/herbster1998mlj-tracking
50. Heston, S. (1993). A closed-form solution for options with stochastic volatility. Review of Financial Studies 6. https://ideas.repec.org/a/oup/rfinst/v6y1993i2p327-43.html
51. Hull, J., White, A. (2017). Optimal delta hedging for options. Journal of Banking and Finance 82. https://ideas.repec.org/a/eee/jbfina/v82y2017icp180-190.html
52. Jin, Y., Candes, E. (2023). Selection by prediction with conformal p-values. JMLR 24. https://jmlr.org/papers/v24/22-1176.html
53. Jones, C., Shemesh, J. (2018). Option mispricing around nontrading periods. Journal of Finance 73. https://ideas.repec.org/a/bla/jfinan/v73y2018i2p861-900.html
54. Joulani, P., Gyorgy, A., Szepesvari, C. (2013). Online learning under delayed feedback. ICML. https://proceedings.mlr.press/v28/joulani13.html
55. Kolm, P., Turiel, J., Westray, N. (2023). Deep order flow imbalance: extracting alpha at multiple horizons from the limit order book. Mathematical Finance 33. https://econpapers.repec.org/RePEc:bla:mathfi:v:33:y:2023:i:4:p:1044-1081
56. Lee, S., Mykland, P. (2008). Jumps in financial markets: a new nonparametric test and jump dynamics. Review of Financial Studies 21. https://galton.uchicago.edu/%7Emykland/paperlinks/LeeMykland-2535.pdf
57. Lim, B., Arik, S., Loeff, N., Pfister, T. Temporal fusion transformers for interpretable multi-horizon time series forecasting. https://arxiv.org/abs/1912.09363
58. Lo, A., MacKinlay, C. (1988). Stock market prices do not follow random walks. Review of Financial Studies 1. https://web.mit.edu/~alo/www/Papers/lo-mackinlay-88.html
59. Muravyev, D., Ni, X. (2020). Why do option returns change sign from day to night? Journal of Financial Economics 136. https://ideas.repec.org/a/eee/jfinec/v136y2020i1p219-238.html
60. Muravyev, D., Pearson, N., Broussard, J. P. (2013). Is there price discovery in equity options? Journal of Financial Economics 107. https://econpapers.repec.org/RePEc:eee:jfinec:v:107:y:2013:i:2:p:259-283
61. Ni, S. X., Pearson, N., Poteshman, A. (2005). Stock price clustering on option expiration dates. Journal of Financial Economics 78. https://ideas.repec.org/a/eee/jfinec/v78y2005i1p49-87.html
62. Ni, S. X., Pearson, N., Poteshman, A., White, J. (2021). Does option trading have a pervasive impact on underlying stock prices? Review of Financial Studies 34. https://econpapers.repec.org/RePEc:oup:rfinst:v:34:y:2021:i:4:p:1952-1986.
63. Politis, D., Romano, J. (1994). The stationary bootstrap. JASA 89. https://gnosis.library.ucy.ac.cy/handle/7/57533
64. Prata, M., and co-authors (2024). LOB-based deep learning models for stock price trend prediction: a benchmark study. Artificial Intelligence Review. https://arxiv.org/abs/2308.01915
65. Raftery, A., Karny, M., Ettler, P. (2010). Online prediction under model uncertainty via dynamic model averaging. Technometrics 52. https://sites.stat.washington.edu/raftery/Research/PDF/Karny2010.pdf
66. RiskMetrics Technical Document, 4th edition (1996). J.P. Morgan and Reuters. https://www.msci.com/research-and-insights/paper/1996-riskmetrics-technical-document
67. Singh, G., Gangwar, R. (2018). A temporal analysis of intraday volatility of Nifty futures on the National Stock Exchange. MPRA 89689. https://mpra.ub.uni-muenchen.de/89689/
68. Sirignano, J., Cont, R. (2019). Universal features of price formation in financial markets: perspectives from deep learning. https://arxiv.org/abs/1803.06917
69. Stoikov, S. (2018). The micro-price: a high-frequency estimator of future prices. Quantitative Finance 18. https://ideas.repec.org/a/taf/quantf/v18y2018i12p1959-1966.html
70. Vovk, V., Petej, I. (2014). Venn-Abers predictors. UAI. https://arxiv.org/abs/1211.0025
71. Zaffran, M., Feron, O., Goude, Y., Josse, J., Dieuleveut, A. (2022). Adaptive conformal predictions for time series. ICML. https://arxiv.org/abs/2202.07282
72. Zhang, C., Zhang, Y., Cucuringu, M., Qian, Z. Volatility forecasting with machine learning and intraday commonality. https://arxiv.org/abs/2202.08962
73. Zhang, L., Mykland, P., Ait-Sahalia, Y. (2005). A tale of two time scales. JASA 100. https://www.nber.org/papers/w10111.pdf
74. Zhang, Z., Zohren, S., Roberts, S. (2019). DeepLOB: deep convolutional neural networks for limit order books. IEEE Transactions on Signal Processing 67. https://arxiv.org/abs/1808.03668

Indian market rules, data and practitioner sources (not peer reviewed unless stated).

75. SEBI, 1 October 2024 measures on equity index derivatives (summary). https://zerodha.com/z-connect/business-updates/sebis-new-rules-for-index-derivatives-heres-whats-changing
76. NSE weekly expiry moved to Tuesday from September 2025 (report). https://www.angelone.in/news/nse-moves-derivatives-expiry-to-tuesday-starting-august-28-2025
77. SEBI interim order on expiry-day index trading, July 2025 (analysis). https://blogs.law.ox.ac.uk/oblb/blog-post/2025/07/jane-street-and-expiry-day-trap-unpacking-sebis-crackdown-algorithmic
78. SEBI study, FY25 losses of individual F&O traders (report). https://www.business-standard.com/amp/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html
79. India VIX method: NSE page https://nseindia.com/products/content/equities/indices/india_vix.htm and a description https://www.icicidirect.com/ilearn/futures-and-options/articles/what-is-volatility-index-how-it-impacts-options-pricing
80. NSE participant-wise open interest (description). https://algotest.in/blog/participant-wise-open-interest/
81. Nifty futures lead spot in price discovery (International Journal of Emerging Markets 2023). https://ideas.repec.org/a/eme/ijoemp/ijoem-07-2022-1097.html
82. Expiry-day IV behaviour (practitioner). https://upstox.com/news/market-news/trading/what-is-driving-option-volatility-on-expiry/article-68819/
83. Weekend decay on Nifty options (practitioner). https://blog.sensibull.com/2017/12/26/the-weekend-effect/
84. Gamma exposure white paper (practitioner). https://slopeofhope.com/wp-content/uploads/2020/11/GEX-white_paper.pdf
85. Dim, Eraker, Vilkov on 0DTE gamma (summary). https://harbourfrontquant.substack.com/p/impact-of-zero-dte-options-on-the
86. Cboe on 0DTE market impact. https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options
87. Purged cross-validation and embargo (overview of Lopez de Prado 2018). https://en.wikipedia.org/wiki/Purged_cross-validation
88. Skew stickiness ratio values, as summarised in arXiv 2603.10857. https://arxiv.org/pdf/2603.10857

Repository sources read: docs/41, 42, 44, 45, 46; `apex/predict/features.py`, `models.py`, `targets.py`,
`ranges.py`; `apex/greeks.py`; `apex/engine/council/c20_9x.py` header; `apex/engine/gex.py` header.
