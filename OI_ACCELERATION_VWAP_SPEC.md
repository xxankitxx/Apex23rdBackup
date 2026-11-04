# OI ACCELERATION + VWAP BREAK — "Writer Squeeze / Writer Flood" Detector

> **Owner:** Ankit · **Instrument:** NIFTY weekly options, **BUY ONLY** · **Data:** ICICI Breeze API
> **Companions:** `PREMIUM_CONTINUATION_ENGINE_SPEC.md` (plugs in as module **M4b**, next to M4 Dynamic Option-Chain) and `CHEAPNESS_AND_REGIME_SPEC.md`
> **Version:** 1.0 — 29 Oct 2026

---

## 0. Instructions to Claude Code

This document describes **one specific idea of Ankit's**, explained here in plain words, then made precise enough to code. Build it as its own detector (`features/oi_accel.py`) with its own state machine, logging and on-screen panel. Its output feeds the entry decision (M11) and the probability model (M10).

Owner rules from the companion spec §0.1 apply in full (buy-only, all-in sizing, no new trade-restricting rules without Ankit's permission, +10 % in 10–15 min or skip, ATM/ITM only, expiring weekly on expiry day, the system must actually trade).

All numbers marked **[CONFIG]** go in `config/pce.yaml`.

---

## 1. The idea in plain words

Watch a single option strike — say the **22500 CE** — and track two things together: its **open interest (OI)** and its **traded price (CMP) relative to the day's VWAP** of that option.

### 1.1 Bullish case — "Writer Squeeze" → sharp rally in the CE
1. The 22500 CE's OI starts **falling** at some steady pace. Call writers (sellers) are buying back their short calls and leaving.
2. Then the **pace of the fall suddenly increases**. Measured every 3 minutes, each interval's OI drop is noticeably bigger than the previous one. The exit is turning into a rush.
3. **Right after that**, the option's traded price keeps rising and **crosses above its VWAP**.
4. → The 22500 CE is likely to see a **sharp rally**.

**Why:** a writer closing a short call has to **buy** the call back. When many writers do this at once, and faster and faster, it becomes forced buying that doesn't care about price. That's a short squeeze inside the option. The VWAP cross confirms it. The average trader of the day is now in profit on longs, and writers who sold below VWAP are underwater. Their stop-losses become more buying, which feeds the rally.

### 1.2 Bearish case — "Writer Flood" → sharp fall in the CE
1. The 22500 CE's OI starts **rising** at some pace. Fresh call writers are entering.
2. Then the **pace of the rise suddenly increases**. Each 3-minute interval adds more OI than the last, so writing is becoming aggressive.
3. **Right after that**, the traded price keeps falling and **breaches the day's VWAP** from above.
4. → The 22500 CE is likely to see a **sharp fall**.

**Why:** confident sellers are flooding the strike with supply, faster and faster. Below VWAP, the day's CE buyers are trapped in losses. Their exits add to the selling, and the premium collapses.

### 1.3 The key insight
It is not the **level** of OI, and not even the **change** in OI. It is the **acceleration** of the change: speed that suddenly increases. That's the moment writers switch from orderly to panicked (squeeze) or from cautious to aggressive (flood). The VWAP break, coming **after** the acceleration, confirms that the price agrees. **Order matters: OI acceleration first, VWAP break next.**

---

## 2. The same idea for every strike and both sides

The pattern is symmetric. Run the detector on every tracked strike (ATM, 2 ITM, 2 OTM, CE and PE, plus any strike Ankit pins, such as 22500):

| Strike type | OI behaviour | Price vs its VWAP | Read | Use in a buy-only system |
|---|---|---|---|---|
| CE | falling, **accelerating** | crosses **above** | Call-writer squeeze | **Buy CE** candidate |
| CE | rising, **accelerating** | breaks **below** | Call-writer flood | **Do not buy CE**; exit alarm if holding a CE; supports a **PE** buy |
| PE | falling, **accelerating** | crosses **above** | Put-writer squeeze (market falling) | **Buy PE** candidate |
| PE | rising, **accelerating** | breaks **below** | Put-writer flood (market rising/holding) | Do not buy PE; supports a **CE** buy |

The strongest setup is a **dual-side signal at the same strike** within the same window:
- **Bullish:** CE squeeze (CE OI falling fast, CE above VWAP) **and** PE flood (PE OI rising fast, PE below VWAP). Call writers are running while put writers build a new floor.
- **Bearish:** PE squeeze **and** CE flood.

---

## 3. Making it precise

### 3.1 OI sampling — do this carefully
- Breeze OI updates are **not continuous**; they come in steps. Measure the real update cadence on our data and store each **actual OI change** with its exchange timestamp.
- **Never treat a repeated identical OI reading as new information.**
- Build OI series on a fixed **interval Δt = 3 min** (Ankit's default) **[CONFIG: oi_interval_min = 3]**, using the last real OI value at each interval end. Also compute 1, 2 and 5-min versions in parallel as research features. Let walk-forward results show which works best.
- Intervals slide forward continuously (rolling windows re-evaluated every few seconds, ending at "now"), not on fixed clock boundaries. This avoids the bar-boundary mistakes described in the regime spec §B3.

### 3.2 Velocity and acceleration
For interval k:
```
v_k   = (OI_k − OI_{k−1}) / Δt                 OI velocity (contracts per minute)
v%_k  = 100 × (OI_k − OI_{k−1}) / OI_{k−1}     normalised velocity (% of OI per interval)
a_k   = v_k − v_{k−1}                          OI acceleration
AR_k  = v_k / v_{k−1}   (only when same sign)  acceleration ratio
```
Normalise against history: z-score `v%` and `a` against **the same strike moneyness, same time-to-expiry bucket and same time of day** over the last `[CONFIG: 20]` sessions. A 2 % OI drop at 10:00 on a Monday is not the same as a 2 % drop at 14:30 on expiry day.

### 3.3 Conditions — bullish squeeze (CE shown; PE identical in mirror)
**Stage 1 — OI_TREND (falling at a speed):**
`v%_{k−1} < −θ_trend` for at least `[CONFIG: 1]` interval, with `θ_trend` `[CONFIG: e.g. z ≤ −1]`.

**Stage 2 — OI_ACCEL (speed of fall suddenly increases):**
- `v%_k < v%_{k−1} < 0` (still falling, now faster),
- `AR_k ≥ m` with `m = [CONFIG: 1.5]`, **and** `z(a_k) ≤ −[CONFIG: 1.5]`,
- Preferably **consecutive**: two accelerating intervals in a row (`AR_k ≥ m` and `AR_{k−1} ≥ 1`) → stronger tier.

**Stage 3 — PRICE_CONFIRM (traded price keeps rising and crosses VWAP), within window W after Stage 2:**
- Option VWAP = session VWAP of that option from traded price × traded qty since 09:15.
- Premium slope over last `[CONFIG: 60–180 s]` > 0 (rising, not one spike).
- **Cross:** trade/ask moves from below VWAP to above VWAP.
- **Acceptance:** price stays above VWAP for `[CONFIG: 10–30 s]`, or the retest holds above `VWAP − buffer`.
- Must happen within `W = [CONFIG: 2 intervals ≈ 6 min]` of OI_ACCEL, otherwise the setup expires.

**→ TRIGGER: SQUEEZE_UP on 22500 CE.**

### 3.4 Conditions — bearish flood (mirror)
Stage 1: `v% > +θ_trend`. Stage 2: `v%_k > v%_{k−1} > 0`, `AR_k ≥ m`, `z(a_k) ≥ +1.5`. Stage 3: premium slope < 0 and price breaks **below** VWAP with acceptance. **→ TRIGGER: FLOOD_DOWN.**

### 3.5 What if price crosses VWAP first, then OI accelerates?
Still valid, but a lower tier (`ORDER = REVERSED`). Ankit's idea ranks highest when acceleration comes first and price follows. Log the order; let the model learn whether reversed order also works.

---

## 4. The trap to avoid: OI falling does NOT always mean writers covering

OI can fall for two different reasons:

| OI | Option price | Who is leaving | Effect on premium |
|---|---|---|---|
| ↓ | ↑ | **Writers covering** (short covering) — they buy | **Bullish for the option** ✅ our signal |
| ↓ | ↓ | **Buyers exiting** (long unwinding) — they sell | **Bearish for the option** ❌ |
| ↑ | ↓ | **Fresh writing** (short build-up) — they sell | **Bearish for the option** ✅ our flood signal |
| ↑ | ↑ | **Fresh buying** (long build-up) | Bullish, but a different signal |

That's why **price confirmation is mandatory**. OI acceleration alone tells us *someone* is rushing. The price direction and VWAP tell us *who*.

Add these extra discriminators so we know who is rushing:
1. **Aggressor side of trades on that strike** (quote/tick rule, companion spec M3 §6.1). In a squeeze, the rising volume should be **buyer-initiated** (lifting the ask).
2. **Order book:** ask-side quantity thinning and bid-side building on that option.
3. **Volume per minute accelerating** on the strike along with OI acceleration. OI change with little volume is suspicious (data step or expiry roll artefacts).
4. **Churn ratio** = traded volume / |ΔOI|. A very high churn means positions are being swapped, not closed, so the OI signal is weaker.

---

## 5. My additions to strengthen the idea

### 5.1 Underlying and moneyness context
- **Distance of Nifty futures to the strike** (22500). Writer panic peaks as the strike moves from OTM toward ATM/ITM, because the writers' losses and delta jump fastest there (gamma is highest near the strike).
- Require the underlying to be moving toward/through the strike in the signal's direction (Nifty futures slope + OFI agree).
- **Synthetic future (22500 + CE − PE) leading spot** confirms real option demand (companion spec M6).

### 5.2 Neighbour strikes
A real squeeze rarely hits one strike alone. Check 22450 and 22550 CE: are their OIs also falling, and accelerating? **Cluster squeeze score** = count of adjacent strikes in the same state. A lone strike may be one large player's adjustment.

### 5.3 Opposite leg of the same strike
For SQUEEZE_UP on 22500 CE, check 22500 PE: OI rising (put writers defending) and PE price below its VWAP. This turns it into the dual-side signal of §2, the highest tier.

### 5.4 Expiry and time
- On expiry day, OI moves are huge and fast after ~13:30. Use the expiry-day baseline for z-scores, never the normal-day one.
- First 15 minutes: OI often includes overnight adjustments, so mark low confidence.

### 5.5 Gamma context
If the squeeze happens while Nifty is crossing the gamma-flip level or breaking the **Call Wall** at 22500, dealers must chase. That's the strongest continuation environment (companion spec M5).

### 5.6 Cheapness check
At trigger time, compute **lag cheapness** (cheapness spec A7). If the option has already run far above VWAP and the lag is gone, the entry is late. Prefer triggers caught right at the VWAP cross, when the premium hasn't caught up yet.

### 5.7 Exhaustion: the end of the squeeze
A squeeze ends when the writers are gone. Signs:
- OI fall **decelerates** (`AR < 1` for consecutive intervals) or OI stops falling,
- Premium makes a new high but buyer-initiated volume drops,
- Price falls back below VWAP.

Emit `SQUEEZE_EXHAUSTING` as a **thesis-health signal** for the live monitor (companion spec M12). What the monitor does with it follows the host project's existing exit rules. Do not invent new exit rules.

### 5.8 Signal strike vs traded strike
The signal may appear on a strike we are not allowed to buy (for example 22500 CE when it is 2 strikes OTM). Default behaviour: **use the signal, but buy the eligible ATM/1-ITM CE** (Δ ≥ 0.52) per owner rules. Flag this in `docs/STATE.md` as a question for Ankit: *"May the signal strike itself be bought when it is OTM?"* Do not change this without his answer.

---

## 6. State machine (per strike, per side)

```
IDLE
  └─(v% beyond θ_trend)──────────────► OI_TREND
OI_TREND
  ├─(AR ≥ m and z(a) beyond limit)──► OI_ACCEL        (start window W)
  └─(trend fades)───────────────────► IDLE
OI_ACCEL
  ├─(price slope ok + VWAP cross + acceptance within W)──► TRIGGERED  → send candidate to M11
  ├─(OI reverses direction)─────────► IDLE    (log INVALIDATED)
  └─(W expires)─────────────────────► IDLE    (log EXPIRED)
TRIGGERED
  └──────────────────────────────────► MONITOR
MONITOR
  ├─(exhaustion signs §5.7)─────────► EXHAUSTING  (thesis-health signal)
  └─(price back across VWAP by buffer)► INVALIDATED (thesis-health signal)
```
Log every transition with timestamp, OI, v%, a, AR, price, VWAP and the reasons.

---

## 7. Signal strength — `SQUEEZE_SCORE` (0–100)

| Component | Starting weight [CONFIG] |
|---|---|
| OI acceleration strength (z of a, AR, consecutive intervals) | 25 % |
| VWAP cross quality (acceptance, slope, distance) | 20 % |
| Aggressor flow + order-book confirmation on the strike | 15 % |
| Dual-side confirmation (opposite leg same strike) | 15 % |
| Neighbour-strike cluster | 10 % |
| Underlying / moneyness / gamma context | 10 % |
| Lag cheapness (not late) | 5 % |

Tiers: **A+** (dual-side + consecutive acceleration + acceleration-before-VWAP order), **A**, **B** (reversed order or single interval). Weights are starting points; the model (M10) learns real ones. Every component is also logged as a separate feature.

**Explanation string example:**
```
SQUEEZE_UP A+ 22500 CE | OI −0.6L → −1.2L → −1.8L per 3m (AR 1.5, z(a) −2.3) |
CE 62→68 crossed VWAP 66, held 20s | buyer-initiated 71% | 22500 PE OI +2.1L, PE < VWAP |
22450/22550 CE also covering | Nifty fut 22468 rising toward strike | → buy ATM CE
```

---

## 8. Worked example (illustrative numbers)

22500 CE, 3-minute intervals:

| Time | OI (lakh) | ΔOI | v% | AR | CE price | CE VWAP | State |
|---|---|---|---|---|---|---|---|
| 10:00 | 80.0 | — | — | — | 60.0 | 65.0 | IDLE |
| 10:03 | 79.4 | −0.6 | −0.75 % | — | 61.0 | 64.9 | OI_TREND |
| 10:06 | 78.8 | −0.6 | −0.76 % | 1.0 | 62.5 | 64.8 | OI_TREND (steady) |
| 10:09 | 77.6 | −1.2 | −1.52 % | 2.0 | 64.0 | 64.8 | **OI_ACCEL** (window opens) |
| 10:12 | 75.8 | −1.8 | −2.32 % | 1.5 | 66.5 ↑ crosses | 64.9 | consecutive accel + **VWAP cross** |
| 10:12:20 | — | — | — | — | 67.2 (held) | 64.9 | **TRIGGERED SQUEEZE_UP** |

Mirror example for a flood: OI +0.5L, +0.5L, +1.1L, +1.7L per interval while the CE premium slides from above VWAP to below it → `FLOOD_DOWN`.

---

## 9. Validation

1. Run the detector over all stored Breeze sessions (including the saved 19 Oct 2026 session) with **no look-ahead**: OI and VWAP use only data up to the decision time.
2. For every TRIGGERED / EXPIRED / INVALIDATED event, record the forward 10–15-min premium **MFE, MAE, time-to-+10 %** on bid-side prices.
3. Tune by walk-forward: the interval (1/2/3/5 min), m, z-limits, window W and acceptance time.
4. Report hit-rate by tier (A+/A/B), by order (accel-first vs reversed), by expiry vs non-expiry, CE vs PE, with Wilson 95 % intervals.
5. Check how often "OI falling + price falling" (long unwinding) would have fooled a version without price confirmation. This proves why §4 matters.

---

## 10. Display

A panel per watched strike (with a pin for any strike Ankit types, such as 22500):
- OI sparkline with velocity bars coloured by acceleration, AR value and the current state.
- Premium vs VWAP line with the cross marked.
- Opposite-leg and neighbour status lights.
- Sound only on TRIGGERED and EXHAUSTING (no pings for intermediate states).

---

## 11. Config — add to `config/pce.yaml`

```yaml
oi_accel:
  interval_min: 3
  research_intervals_min: [1, 2, 5]
  eval_every_sec: 5
  trend_z: 1.0
  accel_ratio_m: 1.5
  accel_z: 1.5
  require_consecutive: false     # true → only A+ tier triggers
  confirm_window_intervals: 2    # W
  price_slope_window_sec: 120
  vwap_accept_sec: 20
  vwap_buffer_pct: 0.5
  churn_max: 50                  # volume / |ΔOI|
  baseline_sessions: 20
  pinned_strikes: [22500]
  allow_buy_signal_strike_if_otm: false   # ASK ANKIT before changing
  weights: {accel: 25, vwap: 20, flow: 15, dual: 15, cluster: 10, context: 10, lag: 5}
```

## 12. Code layout and tests
```
features/oi_accel.py          series builder, velocity/acceleration, z-scores, state machine, score, explain
monitor/oi_accel_panel.py     display panel
tests/test_oi_accel.py        synthetic squeeze, flood, long-unwinding (must NOT trigger), stale-OI repeats (must NOT count),
                              reversed order (tier B), window expiry, no-look-ahead
```

## 13. Acceptance checklist
- [ ] OI series built only from real OI changes; repeats never counted.
- [ ] Velocity, acceleration, AR and z-scores computed per strike with time-of-day / expiry baselines.
- [ ] Price confirmation (slope + VWAP cross + acceptance) mandatory; long-unwinding case does not trigger.
- [ ] Works for CE and PE, squeeze and flood; dual-side and cluster tiers.
- [ ] Signal-strike vs traded-strike rule respects ATM/ITM owner rule.
- [ ] Every event logged with outcome (MFE/MAE) for walk-forward tuning.
- [ ] No new hard bans or exit rules added.

---

## 14. References & Links
*(Verify on first use; if moved, search the title.)*
- Open interest basics — https://www.investopedia.com/terms/o/openinterest.asp
- Short squeeze (mechanics of forced covering) — https://www.investopedia.com/terms/s/shortsqueeze.asp
- VWAP — https://www.investopedia.com/terms/v/vwap.asp
- NSE option chain (strike-wise OI and change in OI) — https://www.nseindia.com/option-chain
- ICICI Breeze API documentation — https://api.icicidirect.com/breezeapi/documents/index.html
- Lee & Ready (1991), trade-direction classification — https://doi.org/10.1111/j.1540-6261.1991.tb02683.x
- Greeks / gamma near the strike — https://en.wikipedia.org/wiki/Greeks_(finance)

*End of document. Claude Code: build `features/oi_accel.py` with tests first, replay it on stored sessions, then wire it into M10/M11. Record the open question in §5.8 in `docs/STATE.md`.*
