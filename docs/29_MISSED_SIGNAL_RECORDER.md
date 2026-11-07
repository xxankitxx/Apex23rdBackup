# Missed-signal recorder — design note (7 Nov 2026)

Part of Apex Conductor Phase 1–2 (docs/28). It answers: **while a book was already in a trade, which trades would it
have taken, and how would they have gone?** It is an observer: it never changes what any book does.
`apex/engine/missed.py`; switched on only by `APEX_RECORD_MISSED=1` (replays), off in the live engine.

## Why a twin is needed

The engine never asks a busy book about entries:

* a paper book's `paper.evaluate_entry` returns "in position" before any entry rule runs (paper.py, line 824);
* a council book's strategy is stepped only for its exits while it holds.

Asking the real book's entry rule out of band is not safe either: the rules change book state as they run (armed
breakouts, retest states, fired episodes, re-entry chains).

## The flat twin

* **Created** at the first second a book is busy (in a position, or waiting for an entry fill). It is a deep copy
  of the book's state at that moment, with no position and no pending entry. For a council book it is a copy of the
  strategy object; the shared `LiveDay` is not copied.
* **Stepped** every second the real book stays busy, through the **same entry pipeline the engine uses**:
  * paper books: `Engine._entry_choice` (shared with the real path), i.e. `evaluate_entry`, the contract picker and
    the same vetoes;
  * council books: `strategy.on_second(i, D, None)` plus the adapter's own entry checks (data gap, kill switch,
    stale quote, |delta| ≥ 0.5).
* **Consumes** a setup when it fires: the episode (or straddle spike) is marked fired and the trigger keys
  are cleared, as `open_trade` does. **Known divergence:** the real book consumes at the *fill*; the twin at
  the *fire*. If a real entry lapses and re-fires, the twin has written one `lapsed` row and does not re-fire.
  It then stays flat, so it can fire again on a new setup.
* **Discarded** the moment the real book is free again; from then on the real book trades for itself.

**Definition (pinned).** A twin signal is *what this book would have done had it been free*. Its state evolves as if
it never traded, so it carries **no per-book cool-down after the real trade**. This is the right counterfactual
only because the Conductor (docs/28, Phase 5) replaces per-book cool-downs with Conductor-level direction-aware
rules. If Phase 5 ever keeps per-book cool-downs, this definition must be revisited.

## Counterfactual outcome

At an episode's first fire, a separate **clean counterfactual book** is spawned: a copy of the twin at that second,
with the real book's capital (all-in). It runs the book's own machinery to a natural end:

* the entry fills on the first print after the trigger, or lapses (as live);
* the book's own exits apply;
* the engine's forced flat applies (15:00 expiry, 15:20 otherwise);
* data-gap freezes apply.

The counterfactual book is not one of the engine's books. It is never saved, never shown and never affects
anything.

## Episodes and dedupe

* **One row per episode per book.** An episode is the run of a twin's fires in one direction with no gap longer than
  30 s.
* Each row keeps:
  * `first_fire_time` and `last_fire_time`;
  * `fire_count`, i.e. how hard the book wanted it;
  * the signal text and strength.
* **Relation to the real position:** `same` (same direction as the real trade) or `opposite`. Opposite-direction
  fires feed the Conductor's switching rule.

## Scope

**Recorded:** only signals a book could not take **because it was busy**.

**Not recorded here:** signals blocked by cool-down, the entry window, data gaps or the daily brake while the book
was flat. They already appear in the decision tape for the champion, and they are a different question.

## Row schema — `data/paper/missed_<day>.jsonl` (in a replay run folder)

| Field | Meaning |
|---|---|
| `date`, `book`, `episode_id` | identity (`episode_id` = `<book>#<n>`) |
| `side`, `relation` | CE / PE; `same` / `opposite` to the real position |
| `first_fire_time`, `last_fire_time`, `fire_count` | the episode; `fire_count` counts distinct **seconds** with a fire (`fire_count_unit`) |
| `signal`, `strength` | the entry reason text and the trigger strength if the book records one |
| `real_key`, `real_time_in` | the trade that kept the book busy |
| `cf_status` | `closed`, `lapsed` (no print within the fill window), `rejected` (unaffordable, etc.), `open_at_end` |
| `cf_time_in`, `cf_time_out`, `cf_entry`, `cf_exit`, `cf_hold_s` | the counterfactual trade |
| `cf_pnl_rs`, `cf_ret_pct`, `cf_peak_pts`, `cf_worst_pts`, `cf_reason` | its outcome, same definitions as real trades |
| `cf_stale_exit`, `cf_fill_delay_s`, `cf_gap` | a stale exit fill, the entry fill's wait, a trade held through a data gap |
| `is_counterfactual` | always `true`, so Phase 3 can never train on these as real trades |
| `snapshot_id`, `weather` | the episode id, and the weather photograph (stage 2, `apex/engine/weather.py`): the counterfactual's own at its trigger, else the one at the first fire (no contract fields) |

## Proof it is an observer

A replay with the recorder on must give **trade-for-trade identical** books to the same replay with it off. That
check is the gate of the freeze step, on two tapes (one quiet, one busy; both must exercise council books in and out
of positions). Two replays with the recorder on must give identical recorder output (determinism).

## Step-1 results (7 Nov)

Two tape slices, each replayed three times in isolation (own port and folder): recorder off, on, on again.

| Slice | Books identical, off vs on | Trades compared (all fields) | Recorder rows, run 1 / run 2 | Time per step, off → on |
|---|---:|---:|---|---|
| 6 Nov 09:15–11:15 (busy normal day) | 72 / 72 | 208 | 98 / 98, identical | 16.11 → 16.44–16.49 ms (+2 %) |
| 3 Nov 09:15–10:45 (expiry morning) | 72 / 72 | 193 | 129 / 129, identical | 13.33 → 13.81–13.84 ms (+4 %) |

**Leak found and fixed on the way.** The first run of the 3 Nov slice had 23 books differing in one field,
`gt_peak`, the gain trail's peak. No entry, exit, price or reason changed. The cause: `paper._GT_BUF` kept one
smoothing window per **book name**, and a counterfactual copy (same name) replaced the real book's window. Fix:
`paper._hard_stop_gain_trail` keys the window on `book.gt_id` when set (counterfactual books get their episode id),
else on the name, so real books are keyed exactly as before. Test:
`tests/test_missed.py::test_a_counterfactual_never_resets_the_real_books_gain_trail_window`.

**Council path covered.** On 6 Nov six council books logged a missed same-direction CE, each with a closed
counterfactual. On 3 Nov the council twins stepped but did not fire.

**Full test suite.** No new failures. The 22 pre-existing failures dropped to 21, and the one pre-existing
collection error (`test_c5_fills_lock`) remains.


## Round-3 corrections (7 Nov, stakeholder review)

| # | Change |
|---|---|
| C1 | Counterfactual errors and recorder faults are **counted**; `missed_summary_<day>.json` reports rows, episodes per book, `cf_errors`, `recorder_faults`, the number of copies and the seconds spent copying (C10). The gate requires zero errors and zero faults. |
| C2 | The straddle_spike twin marks its spike (`-spike id`) as used, as `open_trade` does; before, it re-fired for up to 150 s. |
| C3 | `fire_count` counts distinct seconds (paper twins are stepped every 100-ms engine step, council twins once a second). |
| C4 | Rows carry `cf_worst_pts`, `cf_stale_exit`, `cf_fill_delay_s`, `cf_gap`. `worst_pts` is now tracked on every real and counterfactual position (paper.check_exit, council adapter). |
| C5 | `relation` and the real trade's time come from the pending entry while the real book is only waiting for its fill. |
| C6 | Council `strength` is the strategy's own trigger strength at the BUY (`_buy_v`, round 4: C20); the velocity in the signal text (`v=+23`) is only the fallback. |
| C7 | The consume-at-fire divergence is documented (above). |
| C8 | Episodes split on a **stable** setup identity where one exists (domino episode id, straddle spike id). Books driven by a `fire_id` fall back to the 30-s gap, because their `fire_id` embeds the current second. |
| C9 | Comments: `trades[0]` (a counterfactual takes exactly one trade); `EPISODE_GAP_S` is also the write delay; `advance()` runs after the book loop, and a counterfactual adapter is stepped only when the shared `LiveDay` row for this second already exists (it can never write it). |
| C12 | A counterfactual adapter's warnings are silenced (never in the engine log). |
| C13 | `LiveDay` docstring: `fwd[i]` is carried forward, not nan, when the engine's forward is stale. |
| C14 | `LiveDay` logs once when its 96 option columns are full, instead of dropping contracts silently. |
| C15 | Checked: no strategy module writes to a `D.` attribute. |
| C16 | A council book can never reach the paper twin path (an assert in `_step_paper`). |
| 4.1 | The engine's DATA events (frozen hero contracts) are written on market time, so the events tape compares equal run to run (gate item 2). |

**Known, intended difference (round 5, 5.2).** The real council strategy's breakout window has small holes: while
its fill is pending the adapter does not step it, `catch` bridges the forward through the skipped rows without
pushing them into the window's max/min, and its staleness count covers only stepped seconds. The twin is stepped
every second and has neither hole. About 2–3 s per fill; it can make a twin fire a second earlier or later than the
real book would have.

## The gate (final form, run at the Conductor build)

Run with `apex/replay_batch.py` (one folder per run, manifest) and checked with `apex/replay_compare.py`: items 1–4
are what it reports (`--books-only` for item 1). First on the two step-1 slices (6 Nov 09:15–11:15, 3 Nov
09:15–10:45: expected 72/72 identical, 98 and 129 rows, 0 errors), then the full pass.

1. Recorder off vs on: every real book trade-for-trade identical on two full tapes (one busy, one quiet, both
   exercising council books in and out of positions).
2. The decision tape, events tape and `strikes_*.jsonl` identical, with `#cf` lines filtered.
3. Recorder on, replayed twice: identical `missed_*.jsonl`.
4. Zero counterfactual errors and zero recorder faults (`missed_summary_<day>.json`), and no "missed … faulted" log lines.
5. One run with a read-only wrapper on `LiveDay` during `tw.on_second` and `cfa.step`, raising on any write; then
   remove it.
6. The recorder summary printed: rows, episodes per book, errors, faults, copy time.
