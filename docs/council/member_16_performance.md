# Member 16 — Performance & latency

## Lens
The engine's 100 ms step, its numpy hot paths, how much it allocates, what `publish()` costs, and what the paper books cost.

**Method.** I copied the repo to `/tmp/council/16/ApexOptions` (the original was not touched). I wrote an in-process harness (`/tmp/council/16/harness.py`) that runs `feed_sim.Sim.step` and `Engine.step()`/`publish()` in lockstep: sim at 4 Hz virtual, engine at 10 Hz, publish at 4 Hz. Setup: seed 7, 121 instruments, 68 options, 17 books. All numbers below are **per-thread CPU time** (`time.thread_time`). The box had 2 cores and a load average of 18 (the other council members), so wall-clock was about 6x worse and is not reported. I also ran cProfile and a wrapper that times each component. Tests pass on the copy.

**Headline numbers (45 virtual minutes, 27,000 steps):**

| | mean | p50 | p99 | max |
|---|---|---|---|---|
| `Engine.step()` | 5.11 ms | 2.86 | 14.59 | 26.7 |
| `publish()` | 1.92 ms | 1.91 | 3.43 | 5.9 |
| sim step (feed) | 2.29 ms | 2.21 | 3.87 | 6.0 |

At 10 Hz live, the engine uses about 6 % of one core, so live has plenty of headroom. The state JSON is 19–31 kB, against a 2 MB limit. Step time is bimodal: steps that also compute Greeks take about 10–15 ms, the others about 3 ms.

**Per-component CPU (unprofiled wrapper, 2,400 steps):**

| component | per call | per step (amortised) |
|---|---|---|
| `compute_greeks` (4 Hz) | **7.04 ms** | **2.35 ms (~47 % of the step)** |
| `Flow.update` | 0.75 | 0.75 |
| `Pressure.refresh` | 0.34 | 0.34 |
| `coherence` | 0.27 | 0.27 |
| `Market.push` | 0.23 | 0.23 |
| `option_rows` / `Domino.update` / `update_gex` | ~0.18 each | |
| `run_books` (all 17 books) | **0.020** | 0.020 |
| `Regime.update` / `Ledger.update` / `EpisodeLog.update` | 0.013 / 0.009 / 0.005 | |

## Teardown

**F1 — Implied vol takes half the engine's CPU, and most of that is wasted. Severity: medium (headroom; it makes F2 worse).**
- **Where:** `apex/greeks.py:61-74` and `apex/engine_main.py:337-353`.
- **What is wrong:** each Greeks pass calls `implied_vol` twice, once per expiry (50 rows, then 18). Each call runs 40 bisection iterations. Each iteration prices both the call and the put through four `ncdf` calls, then keeps one with `np.where` (`b76_price`, lines 56-58). Forty iterations on [0.005, 5] give about 1e-12 precision; 20 already give 0.0002 vol points.
- **The cost is per call, not per row:** a 68-row call costs the same as an 18-row call (about 2.6 ms).
- **Prototype:** one merged call (array `T`), one priced leg via the sign trick, 20 iterations. Result: 5.49 ms down to 0.78 ms (**7.0x**), maximum difference 0.0002 vol points, no change in which rows come out NaN (probe script in this session).
- **Smaller extra cost:** the per-strike `nanmean` list comprehensions at lines 348-349 scan every row once per strike.
- **Verified by:** cProfile (`_erf` is the top function by self time, 403k calls in 6 minutes) and a microbenchmark.

**F2 — Replay and sim at `--speed` 10 or more cannot sample at 10 Hz, so they are not "identical at any speed". Severity: medium.**
- **Where:** `engine_main.py:709`, `time.sleep(max(0.1/speed - elapsed, 0.005))`. The sleep never goes below 5 ms, so each real cycle takes at least elapsed + 5 ms.
- **What follows:**
  - At `--speed 20` (the README's replay example) the engine can never step faster than 5 Hz virtual: a 0.2 s minimum, and about 0.38 s on Greeks steps.
  - At `--speed 10`, Greeks steps (10–15 ms) overrun the 10 ms budget, which is roughly 40 % of steps (derived from the measured distribution).
  - `market.py:5-6` claims "time-based, so replay at any speed is identical". That is not quite true. `Flow._rb`/`_rs` (`flow.py:66-67,103-106`) is a ring of 100 **samples** called "10 s", so at 5 Hz it covers 20 s. That `agg10` feeds the PULLED/DRAIN classification and the order-unit conversion. The EWMAs and the aggressor classification are also per-step.
- **Measured:** same sim, seed and minutes, engine cadence 0.1 s vs 0.2 s virtual.
  - Futures z correlation 0.99999.
  - Hero ask-class agreement 98.95 %.
  - 14 of 17 books had identical trades.
  - In `futures_only`, `premium_momentum` and `straddle_spike`, entry times moved by ±1 s and P&L by up to 0.5 pts.
  - One `premium_momentum` exit moved 55 s (09:27:50 vs 09:28:45).
  - Episode ids differ throughout, because `id = int(now_s*10)` depends on step phase.
- **Impact:** small in this sample, but replay-day learning records are not a faithful stand-in for live behaviour, and nothing on the dashboard reports the cadence actually achieved. The guard only reacts above a 10 s step gap (`guard.py:26`).
- **Verified by:** two harness runs, `run_0.1.pkl` vs `run_0.2.pkl`.

**F3 — `Pressure.refresh` rebuilds the OI arrays on every step, even when the chain has not changed. Severity: low.**
- **Where:** `apex/engine/levels.py:67-77`.
- **What is wrong:** it sorts the dict keys, builds two arrays through Python comprehensions and recomputes the walls and PCR at 10 Hz. Those only change when `chain_version` changes (every `CHAIN_POLL_S`) or when spot crosses a strike.
- **Cost:** 0.34 ms per step, measured, which is the third-largest item.

**F4 — `publish()` serialises the state twice in Python. Severity: low.**
- **Where:** `table.py:208` and `table.py:164`.
- **What is wrong:** `clean()` walks every value recursively (about 1,360 calls per publish under the profiler), and then `json.dumps` walks it all again. The 68 hero dicts are built with about 900 `fnum`/`round` calls per publish (1.22M `fnum` calls in 6 minutes).
- **Cost:** 1.9 ms mean. That is fine now, but it is the second-largest cost.

**F5 — All numpy work runs over 512 rows while 121 are used. Severity: low; the size of the saving is unverified.**
- **Where:** `config.MAX_ROWS = 512`, `market.py:20-28`.
- **What is wrong:** `Market.push`, `Flow.update` (eleven `ago()`-indexed 512-wide slices plus four `_classify` calls) and the 200 kB `snapshot()` copy all work on full-width rows.
- **Memory:** eight 512×600 float64 rings hold 19.7 MB, and each column write is strided by 4.8 kB.
- **Speed:** most of the per-call time here is numpy dispatch overhead, so I expect a modest gain (under 1.5x) from slicing to the used rows. I did not measure it.

**F6 — `Market.ago()` repeats an `arange` + `argmin` over 600 slots on every call. Severity: low.**
- **Where:** `market.py:61-69`.
- **What is wrong:** it runs 143k times in 6 minutes, about 40 times per step, because `run_score` → `m.change(m.ltp, 5)` computes a full 512-row difference to read a single element. That happens 44 times per step in `coherence` and again in `publish`.
- **Smaller repeat:** `ctx["fut_r60"]` computes `m.change(m.ltp, 60)` twice (`engine_main.py:272-273`).
- **Cost:** about 0.3 ms per step in total. A cache of slot per age per step would remove it.

**Not a problem (checked):**
- The 17 paper books cost 0.02 ms per step together.
- `Regime` (1 Hz, its percentile scan grows to about 22k samples by the close) costs 0.013 ms per step.
- The state blob is 1.5 % of `STATE_BYTES`.
- The `save_books` disk write happens only when a book changes.

## Good things
- **Shared memory between processes:** the seqlock with targeted re-reads of torn rows (`table.py:125-138`) costs only 0.065 ms per step for a full table copy. The feed hot path never waits on the engine.
- **Observers can't stop the loop:** each one (regime, watch, ledger, gex) is wrapped in its own try/except with a 60 s rate-limited log (`engine_main.py:232-241, 251-258, 288-293, 472-475`).
- **Loop timing is visible:** `loop_ms`, `hot_p50`/`hot_p99` and an engine heartbeat are all published, and an engine stall is treated as a data gap (`guard.py:44-56`, covered by a test). That is the right instinct.
- **Time-indexed rings:** `Market.ago()` looks up history by timestamp rather than by slot count, so most features already tolerate jitter in the step cadence.
- **Rate-limited heavy work:** Greeks run at 4 Hz, publish at 4 Hz and Regime/OI history at 1 Hz, all rate-limited on the virtual clock.
- **Cheap, isolated books:** each variant is pure Python dicts and costs about 1 µs, so adding pre-registered variants or controls is effectively free.

## Ideas from GitHub
1. **ijl/orjson** (https://github.com/ijl/orjson). Licence: MIT / Apache-2.0 (multi-licensed). It writes NaN/Inf as `null` and serialises numpy arrays natively with `OPT_SERIALIZE_NUMPY`, and it has Windows wheels.
   - **Maps to:** `StateBlob.write` (`table.py:163`). It could replace both the `clean()` walk and `json.dumps`. It is a tool-level change with no effect on trading logic.
   - **Caveat:** it adds one dependency, so it should be optional, falling back to the current path when it is not installed.
2. **benfred/py-spy** (https://github.com/benfred/py-spy). Licence: MIT. A sampling profiler that attaches to a running PID without a restart. It supports Windows, `top`, and flamegraph/speedscope output.
   - **Maps to:** a `run_apex.py profile` helper, or a documented runbook step, that records the live engine for 60 s during the first live week. It confirms on the owner's own machine (feed, gateway and browser all competing) the numbers I measured here. It is an observer tool with zero code in the hot path.
3. **marcdemers/py_vollib_vectorized** (https://github.com/marcdemers/py_vollib_vectorized, cloned). Licence: MIT. It has `vectorized_implied_volatility_black` (`implied_volatility.py:95`), based on Jäckel's "Let's Be Rational".
   - **Do not adopt it at runtime:** it needs numba, scipy and pandas.
   - **Use it offline:** a test that checks Apex's own Black-76 IV (after the F1 speed-up) against it on a grid of 0DTE and weekly strikes, so that cutting the iteration count is proven harmless.

## Top 3
1. **Make implied vol about 7x cheaper (F1).** One merged `implied_vol` call with an array `T`, price only the needed leg, 20 iterations, and vectorise the per-strike `nanmean`. The engine step should drop from about 5.1 to about 3 ms mean, and the p99 from about 14.6 to about 7 ms (estimated from the component split). Add the regression test from GitHub idea 3. The IV changes by at most 0.0002 vol points and the trigger numbers are untouched, so it can ship between sessions. **Size S, before Monday** (out of session only, per I-11).
2. **Make replay cadence honest (F2).**
   - Publish the achieved virtual step interval (p50/p99 of `step_gap`) next to `loop_ms`.
   - Warn when it goes above 0.12 s.
   - Change the floor sleep so the engine only sleeps when it has time to spare, instead of always sleeping 5 ms.
   - Fix the `market.py` docstring, which says replay at any speed is identical.
   - Later, make `Flow`'s "10 s" ring time-based.
   **Size S, before Monday** for the metric and the sleep; the ring is **later**.
3. **Cache `Pressure.refresh` on `chain_version`/ATM, memoise `Market.ago()` per step, and slice to the used rows (F3, F5, F6).** Together these save about 1 ms per step. **Size S–M, later.**
