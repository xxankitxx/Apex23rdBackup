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
* **Consumes** a setup when it fires, exactly as a real entry would: the episode is marked fired and the trigger
  keys are cleared. It then stays flat, so it can fire again on a new setup.
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
| `first_fire_time`, `last_fire_time`, `fire_count` | the episode |
| `signal`, `strength` | the entry reason text and the trigger strength if the book records one |
| `real_key`, `real_time_in` | the trade that kept the book busy |
| `cf_status` | `closed`, `lapsed` (no print within the fill window), `rejected` (unaffordable, etc.), `open_at_end` |
| `cf_time_in`, `cf_time_out`, `cf_entry`, `cf_exit`, `cf_hold_s` | the counterfactual trade |
| `cf_pnl_rs`, `cf_ret_pct`, `cf_peak_pts`, `cf_reason` | its outcome, same definitions as real trades |
| `is_counterfactual` | always `true`, so Phase 3 can never train on these as real trades |
| `snapshot_id` | null; filled by Phase 2's factor snapshot |

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
