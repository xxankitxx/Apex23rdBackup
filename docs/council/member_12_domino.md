# Member 12 — The core domino / basket-leads-futures thesis

## Lens
`apex/engine/domino.py` (impulse z, synchrony, basket gap, episodes), `apex/engine/extras.py` (LagMeter, BankLead, EpisodeLog), `apex/universe.py` weights, plus `market.py`, `guard.py`, `paper.py:150-190`, `config.py:66-96`. Question: does the system actually measure "the basket leads the futures"?

**Method.** Besides reading the code, I wrote a null-model probe. It drives the real `Market` and `Domino` classes and `LagMeter`, using the 14 real Nifty weights, a one-factor model with idiosyncratic noise and vol bursts, 10 Hz, 180 simulated minutes. In the probe the futures price is the true index, so **no stock ever leads**. Run A: stocks are simultaneous with futures. Run B: stock LTPs lag futures by 1 s, so the *futures* lead. Script: `/tmp/claude-0/-home-claude/a63e9fa2-7e12-5819-bed7-d06bfece2a8a/scratchpad/probe_domino.py`, with `probe_preopen.py` next to it. Tests pass (`python tests/test_core.py`).

| Null run (no basket lead) | Episodes | BASKET-LED | CO-FIRST | FUTURES-LED | LagMeter median | P(gap·d ≥ 3) / ≥ 5 while z ≥ 1 |
|---|---|---|---|---|---|---|
| A: simultaneous | 130 | **14.6 %** | 85.4 % | 0 % | 0.0 s | 0.6 % / 0.0 % |
| B: futures lead by 1 s | 130 | **13.8 %** | 86.2 % | **0 %** | **0.0 s** | **23.1 % / 13.5 %** |

## Teardown

**F1 — CRITICAL. The episode classifier has a built-in BASKET-LED bias and cannot see futures leadership.** `domino.py:183-198`.
- A stock crossing is only recorded while an episode is open, and an episode opens on the *futures* reaching |z| ≥ 1.
- Fourteen stock clocks race one futures clock. The earliest of 14 noisy crossings is systematically early.
- Line 191 labels the episode BASKET-LED whenever `ft is None`, i.e. whenever futures z peaks between 1 and 2 and any one stock touches 2.
- Line 192 labels it BASKET-LED even when only one stock crossed, if concentration is below 0.6.
- Result: with no lead at all, 14.6 % of episodes come out BASKET-LED. That is right at the D-015 kill line ("Study F1: basket-led < 15 % → re-scope"), so the study can be passed or failed by noise. When futures truly lead by 1 s, FUTURES-LED is still 0 %, because the ±2 s CO-FIRST band and the onset censoring swallow it.
- Failure scenario: the owner reads "basket-led 18 %" after two weeks and treats the thesis as confirmed, when that rate is the null.
- Verified by probe.

**F2 — HIGH. LagMeter measures the futures' rise time, not a domino lag.** `extras.py:117-125` together with `domino.py:184`.
- A stock that crossed before onset gets timestamped at onset, so the lag is bounded by `fut_cross_t − t0`.
- Episodes where futures never reach z = 2 are dropped, which is a selection effect.
- With futures leading by 1 s, the day median still reads **0.0 s** (n = 127): the first-of-N bias cancels the real lead exactly.
- The published "domino lag" (D-057) therefore cannot reject anything.
- Verified by probe.

**F3 — HIGH. The basket gap is dominated by timestamp skew, and coverage extrapolation turns sector moves into fake "gap" signals.** `domino.py:127`, plus the variants at `config.py:95-96` and `paper.py:169-173`.
- *Timestamp skew.* `Mb` uses cash LTPs from the movers/rest sockets. `Mf` uses the hero-socket futures, Breeze `ltt` is truncated to 1 s, and illiquid stock LTPs sit stale between trades. With a 1 s skew in the futures' favour, gap·d ≥ 3 pts happens 23 % of the time while z ≥ 1, and ≥ 5 pts 13.5 % of the time (0.6 % / 0 % when synchronous). In other words, `gap3_s0.4` and `gap5_s0.4` fire mostly when the futures have **just paused or ticked back** while stale stock prints still show the move. They buy into the lull and label it "basket leads". Verified by probe.
- *Coverage extrapolation.* `Mb = Σmi · 100/wtot` scales the tracked ~61.6 % of weight up to the whole index. In a bank-only move with the untracked 38 % flat, Mb = 1.62 × Mf exactly, so gap = 0.62 × Mf. An 8-pt bank-news move gives a 5-pt "gap" although futures priced it fully. Verified by arithmetic from the code; not probed on live data.

**F4 — HIGH. Stock sigmas learn pre-open zeros; futures sigma does not.**
- `domino.py:89` gates `fut_sigma` on `in_session`, but the stock-scale block at `domino.py:91-105` has no such gate. `guard.py:73-74` keeps `learn_scales=True` outside session hours.
- If the engine starts at 09:00, the 15 pre-open minutes of zero moves drag `self.sig` down. Fast-start alpha (1/n) makes this worse, and then the 20-min half-life recovers it only slowly.
- Probe, same seed: median stock sigma at 09:25 is 0.19 when started at 09:00, against 0.47 when started at 09:15 (steady state ≈ 0.38). P(S ≥ 0.5) over 09:25-09:35 is **45.5 % vs 21.2 %**. Synchrony is doubled exactly when `SUPPRESS_UNTIL` (09:25) lifts.
- The same zeros push `vol15_base` towards 0, so `act = dv/base` becomes inf and passes the 1.2× activity filter.
- Verified by probe.

**F5 — MEDIUM. BankLead ignores the blackout and the session.** `extras.py:91-96`.
- Its sigma updates on every finite reading: it is never frozen in a data gap (D-063 freezes only the domino), and pre-open zeros shrink it to the 2-pt floor.
- A reconnect jump inflates `sig` for about 20 min, so the `bank_z` written to the episode log is biased low after every gap.
- Verified by read.

**F6 — MEDIUM. Cash, not stock futures, defines "the basket"; nothing measures index-arbitrage coupling.**
- `domino.py:56` uses `kind=="eq"` only. `sfut` rows are subscribed (`feed_breeze.py:373`) but never used here.
- Nifty futures and the cash basket are tied together by arbitrage desks within milliseconds. At a 15-s horizon, a genuine retail-visible "basket leads futures" signal has to survive that coupling. Most published Indian work finds futures lead cash (background knowledge, not verified here).
- The system never compares stock *futures* against Nifty futures, which is the like-for-like, same-segment comparison with no cash-session microstructure.
- Status: design gap, verified by read.

**F7 — LOW. Weights and z units.**
- Weights date from 30 Sep 2026 (`universe.py`). Four of them (TCS, ITC, BAJFINANCE, HINDUNILVR) are May-2026 estimates. Within a month, drift (wᵢ·Pᵢ/Pᵢ,ref ÷ N/N_ref) is a few percent: immaterial compared with F1-F3.
- "z" divides by an EWMA of |x| (the mean absolute move), not the sd. z = 2 is ≈ 1.6σ under normality, so thresholds read stricter than they are. This needs documenting, not fixing.

## Good things
- **Scales are time-based on a single 10 Hz ring** (`market.py:61-72`), so "15 s ago" means the same in live, sim and replay. That consistency is what made my probe trustworthy.
- **Blackout handling** (D-063): `learn_scales=False` freezes the futures and stock sigmas and the volume baselines (`domino.py:87`). Gap-born episodes are tainted (`engine_main.py:242`, `paper.py:159`), and a test reproduces the reconnect artefact (`tests/test_core.py:218-268`).
- **Synchrony is weight-normalised over *fresh* names only** (`domino.py:119-124`). It also requires both the move z and a volume confirmation, so it is not a vote count.
- **The weight tags are honest** (`universe.py:7-12`): exact vs estimate, with the source documented.
- **The counterfactual EpisodeLog** (`extras.py:136-201`) records the grid at +0/15/30/60/120/300 s for every episode, traded or not. That is exactly the dataset needed to fix F1-F3 offline without touching the frozen trigger.
- **The gap ideas enter as pre-registered variant books** (D-056), not as trigger edits. The process is right even though the measurement is flawed.

## Ideas from GitHub
1. **philipperemy/lead-lag** (https://github.com/philipperemy/lead-lag, MIT). Repo opened.
   - What it is: `lead_lag.lag(ts1, ts2, max_lag)` implements the Hoffmann-Rosenbaum-Yoshida contrast built on a modified Hayashi-Yoshida covariation. It is designed for non-synchronous ticks and resolves lags down to 100 µs.
   - Where it goes: an **EOD tool** (`tools/leadlag_eod.py`, not in the engine). Run it on the recorder's raw sequenced logs (D-026) for each heavyweight against Nifty futures, per episode window and per day.
   - Value: this is the statistically valid answer to "measure the lag" (D-057). It replaces LagMeter's crossing-clock race as the number that judges study F1. MIT, so it can be a dependency.
2. **bashtage/arch** (https://github.com/bashtage/arch; LICENSE.md is in the repo, and I believe it is NCSA, which is permissive, but the fetched page did not show the licence name). Repo opened.
   - What it is: `arch.bootstrap` provides Stationary and Circular Block bootstraps plus **SPA / StepM / MCS** multiple-comparison tests.
   - Where it goes: the **learning loop** (`engine/learning.py`), as an EOD report. With 12 variants plus RAW, the "winner" is selected from many candidates. SPA or StepM against the RAW/random-control books answers "is any variant better than chance after snooping". A block-bootstrapped null of the BASKET-LED rate also gives F1 a proper p-value.
3. **nkaz001/hftbacktest** (https://github.com/nkaz001/hftbacktest, MIT). Repo opened.
   - Idea: model **feed latency explicitly**, keeping an exchange timestamp and a local-receipt timestamp per feed.
   - Where it goes: a **replay variant** in `feed_replay.py` that injects per-socket delay (hero 0 ms, movers/rest +250/500/1000 ms). Run the same day through it and check whether the BASKET-LED rate and the gap-variant P&L survive.
   - Value: anything that flips sign under a 500 ms skew is an artefact (F3).

## Top 3
1. **Pre-register a null for every domino label and lag.** In the EOD report, compute the BASKET-LED rate and the lag median on a time-shuffled or phase-randomised copy of the day (or with stocks shifted ±1 s), and report observed minus null. Restate the D-015 bar as "basket-led rate significantly above the null rate", not "≥ 15 %". This is observer-only, so I-11 is untouched. **S — before Monday.**
2. **Gate stock-scale learning on `in_session`, like futures** (`domino.py:91`, and the same for `BankLead.update`, which should also respect `learn_scales`). This is a bug fix to scale estimation, not a trigger change. It stops the 09:25 synchrony inflation in every book from day one. **S — before Monday.**
3. **Make the gap variants measurable before trusting them.**
   - Log `gap_cov` (Σmi with no 1/coverage extrapolation) and the per-name quote age next to `gap`.
   - Run the EOD Hayashi-Yoshida lead-lag tool (idea 1) on the raw logs.
   - Add the latency-injection replay (idea 3).
   - Keep `gap3/gap5` as they are (pre-registered), but tag each of their trades with the futures' last-1 s move, so the learning loop can see whether they are buying pauses.
   - **M — later** (logging fields before Monday if cheap).
