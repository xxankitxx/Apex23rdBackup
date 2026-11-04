# OPTION CHEAPNESS & MARKET REGIME — Specification for Claude Code

> **Owner:** Ankit · **Instrument:** NIFTY weekly options, **BUY ONLY** (CE/PE) · **Data:** ICICI Breeze API
> **Companion to:** `PREMIUM_CONTINUATION_ENGINE_SPEC.md` (this document replaces/expands its M1 Regime and M9 IV modules and feeds M8 strike selection and M10 features)
> **Version:** 1.0 — 29 Oct 2026

---

## 0. Instructions to Claude Code

This document teaches the system two concepts:

1. **Part A — What "cheap" means for an option.** Cheap is NOT a low rupee premium. A ₹50 CE can be expensive and a ₹200 CE can be cheap.
2. **Part B — How to calculate the market regime** (bullish, bearish, trending, ranging, choppy, volatile, compressing, exhausted…), and **why the current once-a-minute calculation causes mistakes**, plus how to fix it.

Owner rules from the companion spec §0.1 still apply in full (buy-only, all-in sizing, no new trade-restricting rules without Ankit's permission, +10 % in 10–15 min or skip, ATM/ITM only, expiring weekly on expiry day, system must actually trade). **Cheapness and regime are inputs to the entry decision — they must not become new hard bans that starve the system.** Any new veto needs Ankit's approval.

Every threshold marked **[CONFIG]** goes into `config/pce.yaml`.

---

# PART A — OPTION CHEAPNESS

## A1. Definition

> **An option is cheap when its market price is below what the move we expect in the next 10–15 minutes is worth — after time decay, IV drift and the spread.**

Three kinds of cheapness. The system must measure all three, but **only the third one makes money for us**:

| Type | Meaning | Role |
|---|---|---|
| **Statistically cheap** | IV is low versus its own history | Context |
| **Theoretically cheap** | Market premium is below a fair value computed from an *independent* volatility estimate | Cross-check |
| **Situationally cheap** | Premium is low relative to a move that is developing right now and that the option has **not yet priced in** | **The target** |

**Rule:** cheapness alone is never a reason to buy. **Cheapness + catalyst** (a continuation setup from the companion spec) is the reason to buy. Cheapness decides *how good* the entry is and *which strike* to buy.

---

## A2. Metric 1 — IV Rank and IV Percentile (statistical cheapness)

```
IVR = 100 × (IV_now − IV_min) / (IV_max − IV_min)
IVP = 100 × count(IV_hist < IV_now) / N
```

Example: IV_now 12 %, min 10 %, max 25 % → IVR = 13.3 (near the bottom of the range).

**How to compute it correctly for weekly Nifty options (important):**
- Compare **like with like**: same moneyness bucket (ATM, 1 ITM…), same **days/hours-to-expiry bucket**, and same **time-of-day bucket**. A 4-hours-to-expiry IV must never be ranked against 6-days-to-expiry IVs.
- Build the history from **our own stored Breeze data** (snapshot ATM IV each minute, keep per-bucket history). Until we have enough, use **India VIX** rank/percentile as a market-wide proxy.
- Lookback `[CONFIG: 252 sessions]`, plus a short one `[CONFIG: 20 sessions]`.
- Prefer IVP over IVR when one spike has distorted the high.
- Low IVR/IVP (< ~25–30) = favourable context for buyers; high (> ~70–80) = premiums inflated, IV-crush risk.

---

## A3. Metric 2 — Implied vs Realised Volatility (VRP)

```
VRP = σ_implied − σ_realised            (negative = market has been moving more than options charge → cheap)
VR  = σ_forecast / σ_implied            (> 1 = we expect more movement than is priced → cheap)
```

**Realised volatility (from our tick / 1-min data):**
```
Close-to-close:  σ_RV = sqrt( Σ r_i² × (375 × 252) / n )        r = 1-min log return, 375 Nifty minutes/day
Parkinson:       σ²_P = (1 / (4·ln2)) × mean( ln(H/L)² )          (uses bar ranges — less noisy)
```
Compute for 5, 15, 30, 60 min and 1, 5, 10, 20 days.

**Forecast volatility (independent of option prices):** EWMA and a HAR-RV model (daily + weekly + monthly RV components), blended with same-regime historical RV. Validate which forecast is most accurate on our data.

**Horizon rule:** compare IV with a forecast for the **same remaining horizon**. Never compare the last 5 minutes' RV directly to the full-life IV of the option.

---

## A4. Metric 3 — Market Premium vs Fair Value (theoretical cheapness)

Nifty options are European and cash-settled → use **Black-76 on the forward** (Nifty futures, or the put-call-parity synthetic forward), not raw spot.

```
D  = V_market − V_fair
D% = 100 × D / V_fair            (negative = cheaper than fair)
```
- V_market = **mid** for valuation; **ask** for what we actually pay.
- **CRITICAL — avoid circularity:** if V_fair uses the option's own IV, it just reproduces the market price. V_fair must use an **independent** volatility: the surface benchmark (A6) or the forecast (A3).

---

## A5. Metric 4 — Expected move priced in vs the move we expect

```
EM ≈ S × σ_IV × sqrt(T)                      (1-σ move priced in)
ATM straddle ≈ 0.8 × S × σ × sqrt(T)         (quick cross-check from live CE+PE)
```
Example: S = 25,000, IV = 12 %, 1 trading day left → EM ≈ 25,000 × 0.12 × √(1/252) ≈ 189 points.

**For our 10–15-minute horizon:** measure time in **trading minutes** (T = minutes / (375 × 252)), and compare:
- the move the option prices over our horizon, vs
- the empirical distribution of Nifty moves over 10–15 min **in the current regime** (Part B), vs
- the **required move** for +10 % premium (companion spec M8 §11.3).

Cheap ⇔ achievable move in current regime comfortably exceeds both the priced move and the required move.

---

## A6. Metric 5 — Volatility surface residual, skew and term structure (relative cheapness)

1. **Smile fit:** every snapshot, fit IV across strikes of the current weekly vs log-moneyness `k = ln(K/F)` (quadratic in k to start; SVI later). Exclude stale/illiquid/wide-spread quotes.
```
R_IV = σ_market(K) − σ_surface(K)        (negative = this strike is cheap relative to its neighbours)
```
2. **Skew:** Nifty puts normally carry higher IV than calls. Track skew = IV(OTM put) − IV(ATM) and IV(OTM call) − IV(ATM) vs their own history. Unusually steep put skew → puts rich; depressed call skew → calls relatively cheap.
3. **Term structure:** weekly IV vs next weekly vs monthly.
   - Contango (far > near): normal.
   - **Backwardation (near > far): event premium in the weekly** → it will collapse after the event. The weekly is *not* cheap even if IVR looks fine.

---

## A7. Metric 6 — LAG CHEAPNESS (the most important one for our system)

This is situational cheapness at tick level: **the underlying has moved, but the option premium has not caught up yet.** It links directly to the domino/lag idea.

```
V_expected(t) = V_mid(t₀) + Δ·(S_t − S_t₀) + ½·Γ·(S_t − S_t₀)² + Vega·(σ_t − σ_t₀) + Θ·(t − t₀)
LAG(t)        = V_expected(t) − V_ask(t)
LAG%          = 100 × LAG / V_ask
```
- **LAG > 0** → we can buy the option for less than the underlying's move already justifies → **cheap right now**.
- Use the **forward (futures/synthetic)** for S, re-anchor t₀ every `[CONFIG: lag_anchor_sec]`.
- Track how quickly lag normally closes (half-life) per strike — that tells us how long the window stays open.

### Parity cheapness (CE vs PE)
```
C_parity = P + (F − K)·e^(−rT)        P_parity = C − (F − K)·e^(−rT)
CE cheap vs PE   ⇔  C_ask < C_parity(using PE bid)  − threshold
```
If the CE is cheap relative to the PE at the same strike, real demand has not reached the CE yet. Also feeds the parity-lead gate in the companion spec (M6).

---

## A8. Metric 7 — Net expected premium gain (final situational test)

```
NetGain = Δ·E[ΔS] + ½·Γ·E[ΔS²] + Vega·E[Δσ] + Θ·H − half_spread
```
Over our horizon H, with E[ΔS] and E[ΔS²] from the current regime's empirical distribution. Compare with the **adverse excursion** typical for similar setups (MAE history from M10).

> Example: statistically cheap option, NetGain = ₹3, typical adverse move = ₹7 → **not cheap for our purpose**.
> Elevated-IV option, NetGain = ₹18, typical adverse move = ₹4 → **situationally cheap, buy-worthy**.

---

## A9. Execution cheapness
- Spread % = (ask − bid) / mid. A wide spread can wipe out all cheapness.
- Visible depth on the ask vs our quantity (all-in size can be several lots).
- Quote age (stale quotes make options look falsely cheap or rich).

---

## A10. Composite Cheapness Score — `CHEAP_SCORE` (0–100)

| Component | Starting weight [CONFIG] |
|---|---|
| Lag cheapness (A7) | 25 % |
| Net expected premium gain vs adverse move (A8) | 25 % |
| Forecast vol / implied vol (A3) | 15 % |
| Surface residual + skew + term structure (A6) | 15 % |
| Expected-move advantage (A5) | 10 % |
| IVR / IVP context (A2) | 10 % |
| Spread / depth / quote freshness (A9) | applied as multiplier, not added |

Weights are starting points; M10 learns real ones. Output per strike, per tick (or every 1 s).

**How the system uses it:**
1. As **features** in the probability model (every component, not just the total).
2. For **strike selection**: among eligible strikes (ATM, 1 ITM, delta ≥ 0.52), buy the one with the best situational cheapness.
3. In the **explanation string**: `CHEAP 78 | lag +2.4% | NetGain 14 vs MAE 5 | IVP 22 | weekly not backwardated`.

### Pitfalls to code against
- Circular fair value (A4).
- Using LTP instead of bid/ask/mid.
- Comparing IVs across different time-to-expiry.
- **Near-expiry IV instability:** as T → 0, IV solvers blow up. Floor T at `[CONFIG: min_T_minutes]`; on expiry afternoon judge cheapness mainly via A7/A8 (premium terms), not IV levels.
- IV solver failure on deep ITM / zero time value → mark "unknown", never 0.
- Stale quotes and wide spreads masquerading as cheapness.

---

# PART B — MARKET REGIME

## B1. Regime is several axes, not one label

Calculate each axis separately, then combine. Never squeeze everything into one indicator.

| Axis | Question | Main measures |
|---|---|---|
| **Direction** | Bullish / bearish / neutral? | Price vs VWAP, VWAP slope, regression slope t-stat, HH/HL vs LH/LL structure |
| **Trend quality** | Clean move or back-and-forth? | Efficiency ratio, variance ratio, return autocorrelation, VWAP-cross count, Choppiness Index |
| **Volatility level** | Quiet or wild? | Realised vol (close-to-close, Parkinson), range — z-scored vs **same time of day** |
| **Volatility change** | Expanding or contracting? | RV short / RV long, range contraction, Bollinger-width percentile |
| **Participation** | Is the move backed by volume/flow? | Relative volume vs time-of-day baseline, OFI, heavyweight breadth |
| **Dealer gamma** | Will hedging dampen or amplify? | Net GEX, distance to gamma flip / walls (companion spec M5) |
| **Option-market stress** | Is fear / event premium present? | India VIX level & change, ATM IV change, term-structure backwardation |

### Key formulas
```
Efficiency ratio:  ER_n = |P_t − P_{t−n}| / Σ|ΔP|                       (→1 trending, →0 choppy)
Variance ratio:    VR(q) = Var(q-period returns) / (q × Var(1-period returns))
                   VR > 1 trending / momentum,  VR < 1 mean-reverting / choppy
Choppiness Index:  CHOP = 100 × log10( Σ TR_n / (maxHigh_n − minLow_n) ) / log10(n)
                   high (> ~61.8) choppy,  low (< ~38.2) trending
Regression slope t-stat over window: slope / SE(slope)                  (direction with significance)
Vol z-score:       z = (RV_now − mean RV_same_time_of_day) / sd
```

## B2. Regime labels (combine the axes)

| Label | Direction | Trend quality | Vol level | Vol change | Notes |
|---|---|---|---|---|---|
| **TREND_UP_CLEAN** | up | high | normal | stable/expanding | best CE continuation state |
| **TREND_DOWN_CLEAN** | down | high | normal | stable/expanding | best PE continuation state |
| **TREND_VOLATILE** (up/down) | up/down | medium | high | expanding | moves big but with deep pullbacks — MAE risk |
| **RANGE_QUIET** | neutral | low | low | stable | breakouts often fake |
| **CHOP** (range volatile) | neutral | low | high | any | whipsaw; VWAP crossed repeatedly |
| **COMPRESSION** | neutral | low | low | **contracting** | precedes expansion — prepare |
| **EXPANSION / BREAKOUT** | up/down | rising fast | rising | **expanding** from compression | the money transition |
| **EXHAUSTION** | up/down | falling | high | expanding then failing | late-move trap |
| **EVENT_SHOCK** | any | any | extreme | jump | news / gap; Greeks unstable |

Output: **probabilities per label** (soft), not only the top label, plus a **confidence** value.

---

## B3. THE PROBLEM: calculating regime once every minute

The current code recomputes regime once per minute on 1-minute bars. This causes these mistakes:

1. **Late detection (the "almost late" problem).** A breakout that starts at 10:14:05 is only recognised at the 10:15:00 bar close — and often only after 2–3 bars confirm. By then the burst is mostly over, we buy the top, and the pullback hits the stop. This is exactly the late-entry complaint about MYTHOS.
2. **Regime flip-flopping (whipsaw).** Near a threshold, the label alternates TREND → RANGE → TREND every minute. Each flip can trigger or cancel entries → entries on noise, exits on noise.
3. **Bar-boundary artefacts.** The same price action gives a different label depending on where the minute boundary falls. A move split across two bars looks weaker than it is; a spike-and-reverse inside one bar looks like nothing.
4. **Too short a window = noise; too long = lag.** One fixed window on one timeframe is always wrong in one of the two directions.
5. **Single-timeframe blindness.** 1-min can say CHOP while 15-min is a clean uptrend (we skip good pullback entries), or 1-min says TREND_UP inside a 15-min range top (we buy into resistance).
6. **Time-of-day mis-labelling.** 9:15–9:30 is always volatile; 12:30–13:30 is always quiet. Without same-time-of-day normalisation, the open is labelled VOLATILE every day and lunch is labelled COMPRESSION every day.
7. **Missing the transition.** The most profitable moment is the **change** (COMPRESSION → EXPANSION, positive → negative gamma). A label snapshot every minute sees "before" and "after" but misses the change while it is happening.
8. **Stale inputs counted as fresh.** OI and some quotes don't update every minute. Re-reading the same value each minute looks like "confirmation" when nothing new happened.
9. **Look-ahead leak in backtests.** If the 10:15 regime uses the 10:15 bar's close but is applied to a decision made during 10:14, the backtest looks far better than live.
10. **Cold start.** At the open there isn't enough intraday history; the regime is garbage for the first minutes unless previous-day context is carried over.
11. **Over-gating → no trades.** If the label is used as a hard on/off switch, a wrong or flickering label blocks the whole day (the system that didn't trade).

---

## B4. THE FIX: how regime must be calculated

1. **Event-driven rolling windows, not minute buckets.** Update regime features on **every tick** (or every `[CONFIG: 1–5 s]`) using **rolling time windows** (last 30 s, 2 min, 5 min, 15 min, 60 min) that slide continuously. No dependence on bar close.
2. **Three timescales, always together:**
   | Scale | Windows | Used for |
   |---|---|---|
   | Micro | 10 s – 2 min | entry timing, sweeps, transitions |
   | Short | 5 – 15 min | the trade's own horizon (10–15 min) — **primary** |
   | Session | 30 – 60 min + day + previous day | context and bias |
   Record agreement: e.g. `micro EXPANSION_UP, short TREND_UP, session RANGE→top` → strong CE but near session resistance.
3. **Hysteresis.** Separate enter/exit thresholds (e.g. enter TREND when trend score > 0.65, leave when < 0.45 `[CONFIG]`). Stops flip-flopping.
4. **Minimum dwell time** `[CONFIG: e.g. 20–60 s]` before a label can change — **except** a **shock override** when volatility jumps beyond `[CONFIG: k σ]`, which switches immediately.
5. **Soft probabilities.** Output P(label) for each label (via a scoring model or an HMM on returns/volatility); downstream uses probabilities as features, not a single hard label.
6. **Detect transitions explicitly.** Separate signals: `COMPRESSION_BREAKING`, `GAMMA_FLIP_CROSSED`, `VOL_EXPANDING`, `TREND_DECAYING`. These fire within seconds and are the most valuable inputs for entries.
7. **Time-of-day normalisation** of every volatility and volume measure against the last `[CONFIG: 20]` sessions at the same minute.
8. **Freshness-aware.** Each feature carries its input age; stale inputs → feature = unknown.
9. **Warm start.** Seed the session with previous-day regime, overnight gap size, pre-open / opening auction info and GIFT-Nifty cue if available; mark first `[CONFIG: 5]` min as WARMING with lower confidence.
10. **Strict no-look-ahead.** Regime at time t uses data up to and including t only. Replay tests must assert this.
11. **Regime adjusts, it does not ban.** Regime changes thresholds, feature weights and which setup types are preferred (e.g. CHOP prefers trap-reversal setups over breakouts). It must not become a new hard ban without Ankit's approval.

---

## B5. How regime and cheapness work together

| Regime | What "cheap" means here |
|---|---|
| COMPRESSION → EXPANSION | IV usually low and not yet repriced → **best cheapness window**; lag cheapness opens wide |
| TREND_CLEAN | Lag cheapness on pullback-continuations; IV stable |
| TREND_VOLATILE / EVENT_SHOCK | IV rising — a PE can still be cheap (vanna + vega tailwind); a CE is often not |
| CHOP | Options look cheap but moves don't follow through — NetGain small, MAE large |
| EXHAUSTION | Premium looks cheap after a pullback but continuation probability low |
| Post-event | IV crush underway — apparent "cheapness" can keep falling |

The forward-move distribution used in A5 and A8 must come from the **current regime**, not all history.

---

## B6. Validation (prove each regime label is useful)
- For each label, plot the forward 10–15-min premium MFE/MAE distribution of candidates. A label is useful only if these distributions differ meaningfully between labels.
- Measure label stability (flips per hour) before and after the B4 fix.
- Measure detection delay: seconds from a true breakout start (marked offline) to EXPANSION detection — must drop sharply vs the per-minute version.
- Walk-forward, no look-ahead, as in the companion spec §13.5.

---

## C. Config additions — `config/pce.yaml`

```yaml
cheapness:
  ivr_lookback_sessions: 252
  ivr_short_lookback_sessions: 20
  bucket_by: [moneyness, time_to_expiry, time_of_day]
  vol_forecast: [ewma, har_rv]
  pricing_model: black76_forward
  fair_value_vol_source: surface      # never the option's own IV
  lag_anchor_sec: 5
  min_T_minutes: 15
  max_spread_pct: 1.5
  weights: {lag: 25, netgain: 25, vr: 15, surface: 15, em: 10, ivr: 10}

regime:
  update_every_sec: 1
  windows_sec: {micro: [10, 30, 120], short: [300, 600, 900], session: [1800, 3600]}
  hysteresis: {trend_enter: 0.65, trend_exit: 0.45}
  min_dwell_sec: 30
  shock_override_sigma: 3.0
  tod_baseline_sessions: 20
  warmup_min: 5
  er_trend: 0.5
  chop_index_choppy: 61.8
  chop_index_trending: 38.2
  output: probabilities
```

## D. Code layout
```
features/cheapness.py   ivr_ivp, rv_estimators, vol_forecast, black76, surface_fit, lag_cheapness, parity_cheapness, netgain, cheap_score
features/regime.py      axes (direction, trend_quality, vol_level, vol_change, participation, gamma, stress),
                        rolling multi-scale windows, hysteresis, dwell, transitions, probabilities
tests/test_no_lookahead.py, tests/test_regime_stability.py, tests/test_black76.py
```

## E. Acceptance checklist
- [ ] Cheapness never uses the option's own IV for fair value.
- [ ] IV rank/percentile bucketed by moneyness, time-to-expiry and time of day.
- [ ] Lag cheapness and parity cheapness computed live per tracked strike.
- [ ] CHEAP_SCORE and its components logged for every candidate and shown in the explanation.
- [ ] Regime updates on rolling windows every ≤ 5 s, three timescales, with hysteresis + dwell + shock override.
- [ ] Transition signals fire within seconds.
- [ ] Time-of-day normalisation in place; warm-start at open.
- [ ] No-look-ahead test passes; flip rate and detection delay reported vs the old per-minute version.
- [ ] No new hard bans introduced; system still trades.

---

## F. References & Links
*(Verify each on first use; if moved, search the title.)*
- Black-76 model (options on futures/forwards) — https://en.wikipedia.org/wiki/Black_model
- Put–call parity — https://en.wikipedia.org/wiki/Put%E2%80%93call_parity
- Greeks (incl. vanna, charm) — https://en.wikipedia.org/wiki/Greeks_(finance)
- India VIX historical data (NSE) — https://www.nseindia.com/reports-indices-historical-vix
- NSE option chain — https://www.nseindia.com/option-chain
- Volatility smile / skew — https://en.wikipedia.org/wiki/Volatility_smile
- Gatheral & Jacquier — *Arbitrage-free SVI volatility surfaces* — https://arxiv.org/abs/1204.0646
- Corsi (2009) — *A Simple Approximate Long-Memory Model of Realized Volatility* (HAR-RV) — https://doi.org/10.1093/jjfinec/nbp001
- Volatility estimators (Parkinson, Garman–Klass) — https://en.wikipedia.org/wiki/Volatility_(finance)
- Variance ratio test (Lo & MacKinlay) — https://doi.org/10.1093/rfs/1.1.41
- Hidden Markov models in Python (hmmlearn) — https://hmmlearn.readthedocs.io/
- py_vollib (Black / Black-Scholes IV & Greeks) — https://github.com/vollib/py_vollib
- Hysteresis (concept) — https://en.wikipedia.org/wiki/Hysteresis

*End of document. Claude Code: implement Part B's fix first (it affects every other module), then Part A. Update `docs/STATE.md` and ask Ankit before adding any new hard veto.*
