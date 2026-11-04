# PREMIUM CONTINUATION ENGINE (PCE) — Build Specification for Claude Code

> **Owner:** Ankit
> **Instrument traded:** NIFTY weekly options — **BUY ONLY** (CE or PE). Never sell options.
> **Data / broker:** ICICI Direct **Breeze API** (same API key, secret and daily session key as MYTHOS / VAJRA / ApexOptions; session key is entered by hand into `secrets/breeze.json`).
> **Mode for v1:** Paper trading — the system must announce and log every paper trade it takes.
> **Version:** 1.0 — 29 Oct 2026

---

## 0. READ THIS FIRST — Instructions to Claude Code

You are building (or plugging into an existing project) an **entry engine whose single job is to buy a CE or PE only at the moment the premium is about to keep moving in our favour — no immediate breakdown, no fading motion.**

The core idea, in one line:

> **Do not predict whether Nifty goes up or down. Detect the moment when forced flows (writers covering, dealers hedging, heavyweights dragging the index, aggressive orders sweeping the book) are pushing the premium in our direction — and enter exactly then, not after.**

### 0.1 Owner rules you must NEVER change without asking Ankit first
1. **Buy-only.** No option selling, no spreads, no hedges.
2. **All-in sizing.** Full capital (₹1,00,000 fresh every day) plus running P&L goes into every trade. Do **not** add risk-based position sizing.
3. **No trade-restricting rules** — no daily loss stop, no "stop after N losses", no cooldowns, no daily trade cap, no time curfews — unless Ankit explicitly approves.
4. **Trade objective:** minimum **+10 % on premium within 10–15 minutes**. If the engine cannot judge that +10 % is likely in that window, **skip** the trade.
5. **Strikes:** ATM or ITM only (1 ITM preferred when delta < 0.52 at ATM). No deep OTM lottery tickets.
6. **Expiry day:** trade the **expiring weekly contract**, never next week / monthly. Read the expiry date from the Breeze contract master each morning — **do not hard-code the weekday** (NSE moved Nifty weekly expiry to Tuesday in Sept 2025; it can change again).
7. **Lot size:** read from contract master / config (currently 65). Never hard-code.
8. **Slippage and taxes:** kept out of the code for now.
9. **Tick-by-tick display** of the open position with no delay. Sounds only for real events (armed, fill, win, loss, alarm) — no constant pinging.
10. **The system must actually trade.** A paper system that sits idle all day is a failed system. See §9.4 (anti-starvation).
11. **No fabricated results.** Never fake backtest numbers or claim a win rate the logs don't show.

### 0.2 How to work
- Build module by module in the order of §11. After each module: unit tests + replay test on saved Breeze tick data (e.g. the 19 Oct 2026 session that was kept for testing).
- Keep a `docs/STATE.md` updated with what is done, what is pending, and any decision you need from Ankit.
- Every number in this document marked **[CONFIG]** goes into `config/pce.yaml`, not into code.

---

## 1. The problem we are solving — defined precisely

"The option should not break down or fade after I buy" must become a measurable event.

For an entry at time `t` at executable premium `V₀` (use the **ask** for paper buys), define:

```
G  = favourable target   = +10 % of V₀            [CONFIG: target_pct = 10]
L  = adverse limit        = owner's stop rule        [CONFIG: adverse_pts, e.g. 10 premium pts as in MYTHOS]
H  = horizon              = 10–15 minutes            [CONFIG: horizon_min = 15]

τ_G = first time premium (bid side) ≥ V₀ + G
τ_L = first time premium (bid side) ≤ V₀ − L

SUCCESS  ⇔  τ_G < τ_L  and  τ_G ≤ H        ("target-first" / competing-barrier event)
```

Also record for **every** entry (taken or shadow):

```
MFE = max over [0,H] of (V_t − V₀)     — Maximum Favourable Excursion
MAE = max over [0,H] of (V₀ − V_t)     — Maximum Adverse Excursion
TIME_TO_G, TIME_TO_MAE
CLEAN_START = premium never trades below V₀ − ε in first 60 s   [CONFIG: clean_eps_pts]
```

**The engine's quality target:** P(SUCCESS | entry) of **80–85 %**, with **low MAE before MFE** (the premium should run, not dip first). Every module below exists to raise this number.

---

## 2. The five ways the market traps an option buyer (what the engine must detect)

| # | Trap | What it looks like | Module that catches it |
|---|------|-------------------|------------------------|
| T1 | **False breakout / liquidity sweep** | Nifty pokes above resistance, CE buyers jump in, price falls back into range | M2 Structure, M3 Order flow |
| T2 | **Late entry** | Direction right, but most of the burst is over; pullback eats premium | M2 (extension), M7 Domino lag, M10 |
| T3 | **Premium doesn't respond** | Nifty moves, premium barely rises (IV crush, theta, charm, wide spread) | M8 Greeks, M9 IV |
| T4 | **Absorption** | Aggressive buying continues but price stops progressing — passive sellers soaking it up | M3 Absorption detector |
| T5 | **Misread option chain** | Static OI / PCR read as support/resistance, but positioning is shifting | M4 Dynamic chain, M5 Gamma |

---

## 3. Data layer (foundation — build first)

### 3.1 Streams to subscribe via Breeze WebSocket
| Stream | Instruments | Fields needed |
|---|---|---|
| Index spot | NIFTY 50, BANKNIFTY, FINNIFTY | LTP, timestamp |
| Index futures | NIFTY current-month (and next on rollover week) | LTP, LTQ, volume, best bid/ask + qty, **market depth (all levels Breeze gives)**, OI |
| Nifty options | Current weekly: **ATM, 2 ITM, 2 OTM — both CE and PE** (re-centre as ATM shifts) | LTP, LTQ, volume, bid/ask + qty, depth, OI, timestamp |
| Heavyweights | Top Nifty constituents by weight (list from config, refreshed monthly from niftyindices.com) — cash **and** futures | LTP, LTQ, volume, bid/ask + qty, depth |
| India VIX | INDIA VIX | LTP (watch the known Breeze decimal-shift bug — sanity-check range) |

### 3.2 Freshness rules (non-negotiable)
- Every value carries `received_ts` and `exchange_ts`. Compute `age_ms`.
- **OI updates slowly / in bursts.** Never treat repeated identical OI readings as new confirmations. Track `oi_last_change_ts`.
- Any input older than `[CONFIG: max_age_ms]` is marked **STALE** and its feature is set to "unknown" (not zero).
- Log feed gaps; display a red STALE badge on the console.

### 3.3 Derived bars
Build in parallel: tick bars, 5-s, 10-s, 30-s, 1-min, 3-min, 5-min bars for every instrument. Keep a rolling **same-time-of-day baseline** (last 20 sessions) for volume and volatility so everything can be z-scored against "normal for this minute".

### 3.4 Storage
Persist every tick and every computed feature (Parquet per day, or the project's existing DB). This is the training set for M10.

---

## 4. MODULE M1 — Market Regime Classifier

Classify each minute into: **TREND_UP, TREND_DOWN, RANGE, COMPRESSION (pre-expansion), EXHAUSTION, VOLATILE_CHOP.**

Inputs: efficiency ratio (§5.2), VWAP slope, ATR/range z-score vs time-of-day baseline, count of VWAP crossings in last 30 min, GEX regime (M5), VIX level and change.

Use:
- **RANGE / VOLATILE_CHOP + positive gamma** → breakout entries need much stronger evidence (raise threshold).
- **COMPRESSION** → highest-value state; prepare for expansion entries.
- **EXHAUSTION** (extended move, MFE of recent bursts shrinking, delta divergence) → do not chase.

---

## 5. MODULE M2 — Market Structure & Breakout Acceptance

### 5.1 Levels to maintain (live)
Previous day H/L/C, opening range (first 15 min) H/L, intraday swing highs/lows, session VWAP, anchored VWAPs (from day open, from last swing), Call Wall / Put Wall and gamma-flip level (from M5), owner's pressure-zone levels (from PV-RSI / PVBF / force-detector logic if available in the host project).

### 5.2 Directional efficiency (Kaufman efficiency ratio)
```
ER_n = |P_t − P_{t−n}|  /  Σ_{i=0}^{n−1} |P_{t−i} − P_{t−i−1}|
```
ER → 1: clean directional move. ER → 0: back-and-forth. Compute for n = 10 s, 30 s, 1 min, 3 min on Nifty futures.

### 5.3 Volatility-normalised distance from a level
```
Z_R = (P_t − R) / σ_ΔP          (σ_ΔP = std of price change over a comparable short window)
```
Small positive Z_R with acceptance = early. Very large Z_R = extended → late-entry risk (T2).

### 5.4 Acceptance rules (CE side; mirror for PE at support)
A breakout above level R is **ACCEPTED** only when:
1. A bar on the chosen timeframe **closes** above R (not just a wick);
2. Retest (if it happens) holds above R − buffer `[CONFIG]`;
3. Next push makes a higher high (progress);
4. Order flow (M3) stays positive during the push;
5. Room to next resistance ≥ the Nifty move needed for +10 % premium (from M8).

**Failed-breakout invalidation:** if price returns inside the prior range by more than `[CONFIG: reentry_pts]` within `[CONFIG: reentry_sec]`, cancel the breakout thesis immediately. Do not keep the old signal alive.

**Trap-reversal opportunity:** a completed failed breakout (sweep above highs then acceptance back below) is itself a high-quality **PE** setup (mirror for CE). Model it as its own setup type.

---

## 6. MODULE M3 — Order Flow, Imbalance & Absorption

### 6.1 Trade-side classification (aggressor)
Breeze gives LTP/LTQ and top-of-book, not a tagged tape. Classify each trade:
- **Quote rule:** trade at/above ask → buyer-initiated; at/below bid → seller-initiated.
- **Tick rule** fallback for trades inside the spread (uptick = buy, downtick = sell).
- (Lee–Ready algorithm — see references.)

Compute for Nifty futures, each tracked option strike, and each heavyweight.

### 6.2 Order-Flow Imbalance (trade-based)
```
OFI_t = (B_t − S_t) / (B_t + S_t + ε)        range ≈ [−1, +1]
```
B = buyer-initiated volume, S = seller-initiated volume over windows 10 s / 30 s / 60 s. Z-score vs time-of-day baseline.

### 6.3 Cumulative Volume Delta (CVD)
```
CVD_t = Σ (B − S)  since session open (and since last swing)
```
Use the **slope** of CVD and divergence vs price.

### 6.4 Book-based OFI (Cont–Kukanov–Stoikov)
For each best-quote update n:
```
e_n =  q^b_n · 1{P^b_n ≥ P^b_{n−1}}  −  q^b_{n−1} · 1{P^b_n ≤ P^b_{n−1}}
     −  q^a_n · 1{P^a_n ≤ P^a_{n−1}}  +  q^a_{n−1} · 1{P^a_n ≥ P^a_{n−1}}

OFI_book(window) = Σ e_n
```
This captures pressure from quote changes, not just trades — it leads price at very short horizons.

### 6.5 Depth imbalance & stacked imbalance
```
DepthImb = (ΣBidQty_top_k − ΣAskQty_top_k) / (ΣBidQty_top_k + ΣAskQty_top_k)

Diagonal imbalance at price p:  I_p = AskVolTraded(p) / BidVolTraded(p − tick)
STACKED (bullish) = I_p ≥ 3.0 on ≥ 3 consecutive levels      [CONFIG]
```

### 6.6 Absorption detector (T4 killer)
```
PriceResponse = ΔP_window / (signed aggressive volume in window)     (Kyle-lambda style)

ABSORPTION_UP = aggressive buy volume z-score ≥ 2  AND  ΔP ≈ 0 (|ΔP| < k·tick)  AND  ask qty refilling
```
- Absorption against our direction → **veto**.
- **Sweep trigger:** the resting opposing wall (ask qty at the level) **drops to ~0 / is pulled** while aggressive orders keep lifting → this is the entry moment ("wall broke"). This is the owner's "force detector": the opposing force was holding; now it is not enough.

### 6.7 Buyers vs sellers standing in the option
For each tracked strike: track total bid qty vs ask qty across visible depth and its **rate of change**, plus fresh volume per unit time. Rising bid stack + shrinking ask stack + accelerating volume on our option = demand building in the premium itself.

---

## 7. MODULE M4 — Dynamic Option-Chain Positioning

Track ATM, 2 ITM, 2 OTM for CE and PE, timestamped snapshots.

### 7.1 Changes, velocity, acceleration
```
ΔOI_t      = OI_t − OI_{t−k}
%ΔOI_t     = 100 · ΔOI_t / OI_{t−k}
OI_vel     = d(OI)/dt         (only across real OI updates)
OI_acc     = d²(OI)/dt²
ΔPrem_t    = Prem_t − Prem_{t−k}
```

### 7.2 Price–OI quadrant (per strike, joint with underlying move)
| Nifty | Premium | OI | Read |
|---|---|---|---|
| ↑ | CE ↑ | CE OI ↓ | **Call writers covering** → strong fuel for CE |
| ↑ | CE ↑ | CE OI ↑ | Fresh positioning — check aggressor side (M3) |
| ↓ | PE ↑ | PE OI ↓ | **Put writers covering** → strong fuel for PE |
| ↓ | PE ↑ | PE OI ↑ | Fresh positioning — check aggressor side |
| flat | — | OI swings hard | Repositioning / absorption → wait |

### 7.3 Writer-trap signature (best CE fuel; mirror for PE)
- Nifty crosses above ATM strike,
- ΔOI(ATM CE) turns **negative** (call writers covering),
- ΔOI(ATM PE) spikes **positive** (put writers defending new floor),
- Fakeout check: if CE OI at the broken strike **rises 10–15 % within a few bars**, fresh writers are fading the move → likely fakeout → veto. `[CONFIG]`

### 7.4 Option-VWAP crossover gate
Compute intraday VWAP for each tracked option.
**CE trigger:** ATM CE crosses **above** its VWAP **and** ATM PE breaks **below** its VWAP/intraday low **at the same time** (within `[CONFIG: sync_sec]`). Mirror for PE.

### 7.5 PCR
Compute total and ATM±2 PCR and its change. **Context feature only** — never a standalone trigger.

---

## 8. MODULE M5 — Dealer Gamma Exposure (GEX) & Gamma Flip

### 8.1 Per-strike GEX (ATM ± 10 strikes)
```
GEX_k = Γ_k × OI_k × LotSize × S² × 0.01
Net GEX = Σ_calls GEX_k  −  Σ_puts GEX_k        (default convention; sign convention [CONFIG])
```
Γ from Black-Scholes with each strike's own IV (M8).

### 8.2 Gamma-flip level
Recompute Net GEX across a grid of hypothetical spot prices (S ± 2 %). The spot where Net GEX crosses zero = **gamma flip**.
- **Call Wall** = strike with largest call GEX; **Put Wall** = largest put GEX.

### 8.3 How to use
- **Positive gamma zone** (dealers long gamma): they sell rallies / buy dips → breakouts get faded → raise threshold or require a wall break.
- **Negative gamma zone / crossing the flip / breaching a wall where writers are trapped**: dealer hedging **chases** the move → highest-quality continuation entries.
- The sign convention for India is not certain; let M10 learn which convention actually predicts continuation from our own data, and keep both versions as features.

---

## 9. MODULE M6 — Synthetic Future Parity Lead

```
S_syn(K) = K + C(K) − P(K)            (at ATM K; optionally adjust for carry)
LEAD = ΔS_syn − ΔS_spot   over 5 s / 15 s / 30 s
```
- Spot ticks up 10 but S_syn rises only 3 → option market is not buying the move → **fake** → veto CE.
- **ΔS_syn > ΔS_spot** → real option demand is leading the index → strong confirmation.
- Also track the **futures basis** (Fut − Spot) change as a parallel lead signal.

---

## 10. MODULE M7 — Heavyweight Domino / Lag Engine

Owner concept: one heavyweight moves, others follow, Nifty follows after a short lag — **enter inside that lag**.

1. Maintain live index weights (config, refreshed monthly).
2. **Weighted heavyweight impulse:**
   ```
   HWI_t = Σ_i w_i · r_i,t          (r = short-window return of stock i, cash and futures)
   ```
3. **Breadth-of-heavyweights:** count of top-N `[CONFIG: N=6..10]` ticking in our direction with positive OFI (M3).
4. **Lead–lag estimate:** rolling cross-correlation of each heavyweight's returns with Nifty futures at lags 0–60 s; store the current best lag per stock.
5. **Domino trigger:** HWI and heavyweight OFI move hard while Nifty has not yet moved its implied share → entry window open for `estimated_lag` seconds.
6. **Veto:** Nifty breaks a high but the top 2 heavyweights sit on aggressive ask walls / negative OFI → breakout likely fails.
7. BankNifty and FinNifty act as **co-equal live drivers** (their futures/options OFI and moves feed the same logic).

---

## 11. MODULE M8 — Greeks & Premium Feasibility (T3 killer)

### 11.1 Live Greeks
Compute per tracked strike every tick (or every 1 s): IV (solve from mid price), Δ, Γ, Θ, Vega, plus second-order **Vanna** (∂Δ/∂σ) and **Charm** (∂Δ/∂t). Use `py_vollib` or an own Black-Scholes implementation; consistent units (Θ per minute for scalps).

### 11.2 Premium change decomposition
```
ΔV ≈ Δ·ΔS + ½·Γ·ΔS² + Vega·Δσ + Θ·Δt
```

### 11.3 Required move check (core gate)
Solve for the Nifty move `ΔS_req` that gives ΔV = +10 % of V₀ within H, after expected Θ·H and expected Δσ.
Compare against **achievable move**: current spot velocity × H, recent burst sizes in this regime, distance to next opposing level.
**If ΔS_req > achievable move → skip.** (Owner rule: skip if +10 % in 10–15 min can't be judged.)

### 11.4 Strike selection
- Default ATM; switch to 1 ITM when ATM |Δ| < 0.52 `[CONFIG]`.
- Charm rule: never use a strike where `spot velocity < charm/theta bleed threshold`.
- Spread rule: reject if (ask − bid) / mid > `[CONFIG: max_spread_pct]`.

### 11.5 Vanna edge
- PE on support break: IV usually spikes → Delta (via Gamma) + Delta (via Vanna) + Vega all add → **double tailwind**, favour these.
- CE on bounce from lows: IV often drops → Vanna shrinks delta → require larger spot velocity.

---

## 12. MODULE M9 — IV & Volatility Regime

- ATM IV, IV change over 1/5/15 min, IV vs neighbouring strikes (skew), IV percentile vs last 20 sessions, India VIX level and change.
- Before scheduled events (RBI, budget, US data) IV inflates; after, it collapses → model expected Δσ in M8 accordingly.
- Feature only — no blanket "never buy high IV" rule. M8 decides whether the move beats the IV drift.

---

## 13. MODULE M10 — Probability Engine (the brain)

### 13.1 Candidate generation
Every time any trigger fires (breakout acceptance, sweep, domino window, VWAP crossover, gamma-flip cross, trap reversal), create a **candidate** with full feature snapshot `X_t` — using only data available at `t`.

### 13.2 Labels
For every candidate (taken or not), compute outcome with the competing-barrier definition of §1 on **bid-side** premiums: `SUCCESS / FAIL / TIMEOUT`, plus MFE, MAE, CLEAN_START.

### 13.3 Features (from all modules)
Structure (Z_R, ER, distance to next level, acceptance flags) · Order flow (OFI multi-window, book OFI, CVD slope, depth imbalance, stacked imbalance, absorption, sweep) · Chain (ΔOI, OI velocity/acc, quadrant, writer-trap, VWAP crossover) · GEX (net GEX, distance to flip/walls, regime) · Parity lead · Domino (HWI, breadth, lag position) · Greeks (Δ, Γ, Θ, Vega, Vanna, Charm, ΔS_req vs achievable) · IV regime · time of day, minutes to expiry, expiry-day flag · data-freshness flags.

### 13.4 Models
- **Baseline:** logistic regression (auditable).
- **Main:** gradient-boosted trees (LightGBM).
- **Calibrate** probabilities (isotonic / Platt) so "0.85" really means ~85 % on unseen days.
- **Separate models (or a regime feature)** for expiry day vs non-expiry, and CE vs PE.

### 13.5 Walk-forward training (owner's standing preference)
- Rolling: train on past N sessions, validate next M, test next block, roll forward.
- Purge overlapping holding windows between train/test (no leakage).
- Report per block: calibration curve, hit-rate at each probability bucket, trade count, MAE/MFE distribution, **Wilson 95 % interval** on hit-rate.
- Retrain nightly (persistent learning layer), keep model versions, auto-promote only if the new model beats the champion on the latest unseen block.

### 13.6 Bootstrap before enough labels exist
Until the model has `[CONFIG: min_labels]` labelled candidates, use the rule-score of §14 as the decision, and keep labelling everything.

---

## 14. MODULE M11 — Decision Layer & Explanations

### 14.1 Vetoes (hard, few, evidence-based)
1. Failed breakout / re-entry into prior range (M2).
2. Absorption against our direction (M3).
3. Parity lag — S_syn not confirming spot (M6).
4. Writer fade signature at the broken strike (M4 §7.3).
5. Required move > achievable move (M8 §11.3).
6. Critical data stale (§3.2).

### 14.2 Conviction score (pre-model / alongside model)
| Group | Starting weight [CONFIG] |
|---|---|
| Structure & location | 20 % |
| Order flow & sweep | 25 % |
| Option-chain dynamics + VWAP crossover | 15 % |
| Gamma regime + parity lead | 15 % |
| Heavyweight domino | 10 % |
| Premium feasibility & IV | 15 % |

Weights are starting points — M10 learns the real ones.

### 14.3 Entry rule
```
ENTER if  no veto  AND  P_model(SUCCESS) ≥ p_threshold   [CONFIG: start 0.80]
(during bootstrap: conviction_score ≥ score_threshold)
```

### 14.4 The 4-gate "sweet spot" alignment (highest-quality tier)
Tag an entry **A+** when all four align at the same timestamp:
1. **Regime gate:** breaking a gamma wall or inside negative-gamma pocket.
2. **Parity gate:** S_syn leading spot.
3. **Crossover gate:** our option above its VWAP while the opposite leg breaks below its VWAP/low.
4. **Microstructure gate:** Nifty futures stacked imbalance sweeping resting orders + ≥ 4 of top 6 heavyweights ticking our way.

### 14.5 Explanation string (always)
Every decision prints why. Examples:
```
CE ENTER A+ @ 142.5 | P=0.86 | wall 25800 swept, ask stack pulled | S_syn lead +4.2 | ATM CE>VWAP, ATM PE<VWAP |
HDFCBANK/RELIANCE/ICICIBANK/INFY up w/ +OFI | ΔS_req 18 pts vs achievable 31 | neg-gamma pocket
PE SKIP | breakdown not accepted (re-entered range 8s) | absorption at bid | parity not confirming
```

---

## 15. MODULE M12 — Live Trade Monitor

- Tick-by-tick display: premium, P&L ₹ and %, MFE, MAE, seconds elapsed, live thesis health.
- **Thesis-health signals** (emit, colour, sound on change): reclaimed level lost, order flow flipped, absorption appeared, S_syn turned against, heavyweights reversed, premium deteriorating while spot holds (IV/charm bleed).
- **What to do with those signals (exit or hold) follows the host project's existing owner rules** (e.g. MYTHOS 2.0 stop-or-rally, −10 premium stop, 15:25 EOD flatten). Do **not** invent new exit or risk rules — ask Ankit.

---

## 16. Expiry-Day Specifics

- Trade the expiring weekly contract only.
- Gamma and charm are extreme after ~13:30: re-weight M5/M8 features; separate model or regime flag.
- Pin dynamics near max-OI strikes (reuse VAJRA pin-risk logic if available) — breakouts away from the pin after a wall break can run hard; inside the pin they fade.
- Closing Auction Session from 15:15 — handle quotes carefully; follow existing project time rules.

---

## 17. Making sure the system TRADES (anti-starvation)

1. Log **every candidate** with its probability and outcome (shadow trades) — this is how the engine learns and how Ankit sees what it saw.
2. If no trade has fired by `[CONFIG: starvation_check_time]`, show the best candidates so far and their probabilities on the console.
3. Report daily: candidates generated, entries taken, hit-rate by probability bucket. If thresholds are blocking good candidates (shadow hit-rate high), surface that to Ankit for a decision — **do not silently lower thresholds**.

---

## 18. Config file skeleton — `config/pce.yaml`

```yaml
underlying: NIFTY
mode: paper
capital_start_inr: 100000
sizing: all_in
lot_size: from_contract_master
expiry: from_contract_master          # trade expiring weekly on expiry day

objective:
  target_pct: 10
  horizon_min: 15
  adverse_pts: 10                      # align with host project stop rule
  clean_eps_pts: 1.0

strikes:
  track_itm: 2
  track_otm: 2
  min_abs_delta: 0.52
  max_spread_pct: 1.5

data:
  max_age_ms: 1500
  baseline_sessions: 20

structure:
  reentry_pts: 8
  reentry_sec: 30
  retest_buffer_pts: 5
  er_windows_sec: [10, 30, 60, 180]

orderflow:
  ofi_windows_sec: [10, 30, 60]
  stacked_ratio: 3.0
  stacked_levels: 3
  absorption_vol_z: 2.0

chain:
  writer_fade_oi_pct: 12
  sync_sec: 10

gamma:
  strikes_each_side: 10
  sign_convention: dealer_long_calls_short_puts   # learn both

heavyweights:
  top_n: 6
  weights_source: niftyindices_monthly
  max_lag_sec: 60

model:
  p_threshold: 0.80
  min_labels: 500
  retrain: nightly_walk_forward

starvation_check_time: "11:30"
```

---

## 19. Suggested folder layout

```
pce/
  data/        breeze_stream.py, bars.py, freshness.py, store.py
  features/    regime.py, structure.py, orderflow.py, chain.py, gamma.py,
               parity.py, domino.py, greeks.py, iv.py
  model/       labels.py, train_walkforward.py, calibrate.py, predict.py
  decision/    vetoes.py, conviction.py, decide.py, explain.py
  monitor/     live_monitor.py, sounds.py, console_ui.py
  replay/      replay_engine.py   (feed saved ticks through the full pipeline)
  config/      pce.yaml
  docs/        STATE.md, DECISIONS.md, this spec
  tests/
```

---

## 20. Build phases for Claude Code

| Phase | Deliverable | Done when |
|---|---|---|
| 1 | Data layer + freshness + storage + replay engine | 19 Oct session replays tick-for-tick |
| 2 | M2 Structure + M3 Order flow + absorption/sweep | Unit tests + visual check on replay |
| 3 | M4 Chain dynamics + M6 Parity + M7 Domino | Features logged per candidate |
| 4 | M8 Greeks/feasibility + M9 IV + M5 GEX/flip | Greeks match a reference calculator within tolerance |
| 5 | Candidate generator + labels (§1) + rule conviction (§14) | Paper trades fire and are announced |
| 6 | M10 model, calibration, walk-forward, nightly retrain | Calibration report per block |
| 7 | M12 monitor, sounds, console, daily report, anti-starvation | Full live paper day runs end-to-end |

---

## 21. Acceptance checklist

- [ ] Only BUY orders exist anywhere in the code path.
- [ ] All-in sizing; no new limits/caps/cooldowns added.
- [ ] Expiry and lot size read from contract master.
- [ ] Every candidate logged with features, probability, decision, explanation, outcome, MFE/MAE.
- [ ] Stale data never counted as fresh confirmation.
- [ ] Greeks verified against reference.
- [ ] Walk-forward report with calibration and Wilson intervals produced.
- [ ] Paper trades fire on a normal live day.
- [ ] Tick-by-tick position display; sounds only on real events.

---

## 22. References & Links
*(Claude Code: verify each link on first use; if one has moved, search for the title.)*

**Market data & broker**
- ICICI Breeze API documentation — https://api.icicidirect.com/breezeapi/documents/index.html
- Breeze Python SDK (GitHub) — https://github.com/Idirect-Tech/Breeze-Python-SDK
- NSE Option Chain — https://www.nseindia.com/option-chain
- India VIX (historical) — https://www.nseindia.com/reports-indices-historical-vix
- Nifty 50 index page / factsheet (constituent weights) — https://www.niftyindices.com/indices/equity/broad-based-indices/nifty--50

**Order flow & microstructure**
- Cont, Kukanov & Stoikov — *The Price Impact of Order Book Events* (book-based OFI) — https://arxiv.org/abs/1011.6402
- Lee & Ready (1991) — *Inferring Trade Direction from Intraday Data* — https://doi.org/10.1111/j.1540-6261.1991.tb02683.x
- Easley, López de Prado & O'Hara — *Flow Toxicity and Liquidity in a High-Frequency World* (VPIN) — https://doi.org/10.1093/rfs/hhs053

**Gamma / dealer positioning**
- SqueezeMetrics — *The Implied Order Book* (GEX white paper) — https://squeezemetrics.com/download/The_Implied_Order_Book.pdf

**Options maths**
- Greeks incl. Vanna & Charm — https://en.wikipedia.org/wiki/Greeks_(finance)
- Put–call parity (synthetic future) — https://en.wikipedia.org/wiki/Put%E2%80%93call_parity
- py_vollib (Black-Scholes IV & Greeks in Python) — https://github.com/vollib/py_vollib

**Labelling, modelling & validation**
- López de Prado — *Advances in Financial Machine Learning* (triple-barrier labelling, purged CV) — https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086
- LightGBM docs — https://lightgbm.readthedocs.io/
- scikit-learn probability calibration — https://scikit-learn.org/stable/modules/calibration.html
- Wilson score interval — https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval

**Nifty-specific reading (from the source notes)**
- Quantsapp backtest — EMA20/50 volume-spike breakout momentum — https://www.quantsapp.com/backtesting/strategies/ema20-50-volume-spike-breakout-momentum
- NiftyDesk — Nifty options flow analysis guide — https://niftydesk.app/blog/nifty-options-flow-analysis-guide
- TickerPulse — Expiry-day trap, 1,600 moves tested — https://tickerpulse.in/article/expiry-day-trap-tested-1600-moves
- SSRN paper on ML / Greeks-aware labelling — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6625120

---

*End of specification. Claude Code: start with Phase 1, keep `docs/STATE.md` current, and ask Ankit before changing any owner rule in §0.1.*
