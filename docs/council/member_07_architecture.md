# Member 07: Software architecture & maintainability

## Lens
Module boundaries, `apex/engine_main.py` as orchestrator, coupling through the `ctx` dict, duplicated logic, error handling, `config.py` design, and how safely an advisor or variant can be added. Baseline 85b65ed; all 31 tests pass. Probes ran on a private copy (scratchpad `m07/repo`), with private shared-memory names `m07_tbl`/`m07_st`, the sim feed running in-process, and no gateway or port. The ApexOptions tree was not touched.

## Teardown

### T1. One failing advisor stops every exit while an episode is live, and the heartbeat says all is well. Severity: HIGH (verified, probe)
- `engine_main.py:283-287`: `advise()` runs before `run_books()` inside `step()`, with no guard of its own. Eleven of the thirteen advisor computations (`advise()`, lines 405-453) call sub-objects such as `self.watch.advise`, `self.gex.advise`, `self.regime.advise`, `self.straddle.view()` and `self.force.view()`. Any exception from them propagates up to the catch-all at `run()` lines 701-703, which logs, sleeps 0.5 s and loops.
- That makes the error policy inconsistent. regime (238), watch (255), gex (472) and ledger (290) are wrapped as "observers: never stop the loop", but the **advisors are observers too** (D-033: logged only, never voting unless promoted), and they sit unguarded in front of the code that manages positions. The same holds for `straddle.update`, `bank.update`, `lag.update` and `force.update` (250-262).
- Probe (scratchpad `m07/probe.py`): sim at 60x, seed 7. After the first paper entry, `advise()` was forced to raise. Result: 685 steps, `run_books` ran only 373 times, and **312 steps skipped all exits**. The `premium_momentum` position stayed open about 62 s of wall time (roughly an hour of sim time) while futures moved **99 points against it**, with `d_star = 12`. Exits only came back when no episode was live, because `advise()` is called only when `ctx["episode"]` exists. That is the worst case: exits are blocked exactly while price is moving.
- Compounding it, `engine_hb_ns` is written every loop, even right after the exception (705), and nothing reads it (`grep`: only `table.py:44` and `engine_main.py:705`). `run_apex.py:85` restarts the engine only on process exit. An engine stuck in this failure loop looks healthy to both the supervisor and the dashboard.
- In paper mode this corrupts the books and the learning record: the stop and trail never fire, and the learning loop then scores those trades.

### T2. Advisor names live in three hand-kept lists, and nothing cross-checks them. Severity: MEDIUM (verified, read + probe)
- They are produced as dict keys in `engine_main.py:405-453`, consumed in `learning.py:49` (`ADVISORS = [...]`), and labelled in `static/app.js:147`. If you add `a["new"]` in `advise()` and forget `learning.ADVISORS`, the advisor is logged on every trade but **silently never screened**. `config.validate()` cannot catch this; the probe confirmed `'my_new' in learning.ADVISORS` is False and no check fails.
- Related statistical flaw caused by the structure: there is one global `REGISTERED = "2026-10-17"` (`learning.py:50`), and the screen reads every RAW trade since then (330). Trades from before an advisor existed have no key for it, so `t["advisors"].get(a)` is falsy (338) and they count as "kept, not vetoed". A late-added advisor therefore reaches `n >= 30` on trades it never saw, and its `gain` and `top_v` are diluted by them. The repo has no per-advisor registration date. The D-033 "pre-registered" discipline is enforced for variants, but not for when an advisor started.

### T3. Variant behaviour is a set of loose flags read with `p.get(...)` in five functions, and the config check accepts typos. Severity: MEDIUM (verified, probe)
- The flags `spike`, `random`, `momentum`, `gap_star`, `exit_book` and `s_exit` are tested in `paper.py:69,102-105,142-156,169,313,370,372`. Adding a new kind of variant means editing `entry_dir`, `choose_contract`, `evaluate_entry`, `open_trade` and maybe `check_exit`. Precedence between flags is set only by the order of the `if` statements.
- `config.validate()` (270-304) checks that the four required keys exist and are in range, but never rejects unknown keys or conflicting flags. Probe: registering `{'exit_bok': True}` (a typo) and `{'spike': True, 'random': True}` both returned `validate() -> []`. The first silently becomes a clone of `m2.0_s0.5`, which spends a challenger slot and also inflates the Bonferroni divisor (`learning.py:271`) for every real challenger. That is a statistical cost, not only a code-style one.

### T4. `ctx` is an untyped bag of about 20 keys, and its contract is held only by convention. Severity: MEDIUM (read)
- It is built in `engine_main.py:265-278` and read through `ctx["..."]` and `ctx.get(...)` in paper, ledger (`ledger.py:79`), extras (`extras.py:177`) and the variant evaluators. Some keys are read with `[]` (`ctx["advisors"]`, `ctx["domino"]["dir"]`, `ctx["by_key"]`) and others with `.get` and a default, so a renamed key gives either a `KeyError` (which leads straight into T1) or a silent `None`. Nothing documents which module owns which key.
- `advise()` also reaches past `ctx` into engine state: `self.greek`, `self.pressure`, `self.domino.state`, `self.day`. So an advisor cannot be tested from a `ctx` snapshot or replayed from the ledger.

### T5. The orchestrator has no tests, and its state is created lazily. Severity: MEDIUM (verified, grep)
- `tests/test_core.py` never imports `engine_main`. All 31 tests exercise leaf modules, so the step ordering in T1 (the most safety-relevant sequence in the system) has no coverage.
- `Engine` creates many attributes on demand (`getattr(self, "atm"/"atm_iv"/"fwd"/"ledger"/"regime"/"_learned"/"_reg_err"…)`, and `self.key` and `self.opts` are never set in `__init__`). Each `getattr` default hides an ordering assumption. `compute_greeks` sets `self.atm_iv = getattr(...)` on every call (332), which is a sign the initialisation belongs in `__init__`.

### T6. Small duplications that will drift. Severity: LOW (read)
- The "for g in gates: veto → return" loop is copied three times (`paper.py:184,210,294`).
- The instrument key format `f"NIFTY|OPT|{w0}|{K}|{rr}"` is built in three places (`engine_main.py:391,482`, `paper.py:88`).
- The "log once a minute" error throttle is copied four times with four ad-hoc attributes (`_reg_err`, `_watch_err`, `_gex_err` using `time.time()` where the others use `now_s`, and `_led_err`).

## Good things
- **A clean process split.** feed → shared memory → engine → blob → gateway (`table.py`, `run_apex.py:57-61`). The engine can be restarted alone because the books are on disk (`run_apex.py:87`, `paper.save_books`, saved atomically via `os.replace` at 433-438).
- **`learning.py` is pure, file-in and file-out**, has no engine dependency, and writes its state atomically (146-150). It is idempotent per evening (`looked_day`/`learned_day`, with a test). This is the best-bounded module.
- **`config.validate()` plus preflight** (`run_apex.py:176`). The design is right; it just needs to check more (T3).
- **Exit logic matches contracts by key, not row id** (`paper.py:343-348`), which survives a feed restart that renumbers rows. Registry re-numbering resets history on purpose (`engine_main.py:102-108`).
- **Controls and gated books reuse the ordinary `Book`.** Champion, RAW, controls and `gate:<a>` books all go through one `run_books` path (548-586), so every null hypothesis is tested on identical code.
- The deterministic random-control schedule (`paper.py:226-239`) keeps replays reproducible.

## Ideas from GitHub (all opened or cloned into /tmp/council/07/)

1. **pytest-dev/pluggy** (https://github.com/pytest-dev/pluggy, MIT). Borrow the "hookspec plus registration-time verification" idea from `src/pluggy/_manager.py:_verify_hook` (lines 429+, which rejects implementations whose arguments are not in the spec) and `check_pending()` (479).
   - Map onto Apex as a small **advisor registry** (`apex/engine/advisors.py`). Each advisor is declared once with `name`, `registered` date, `label` and `fn(view) -> (veto, why)`. `learning.ADVISORS`, the `app.js` labels (served via the state blob) and the per-advisor screen start date are all derived from it.
   - That fixes T2 at the root. You don't need pluggy itself, only its "declare once, verify at load" pattern, which can be copied freely under MIT.

2. **nautechsystems/nautilus_trader** (https://github.com/nautechsystems/nautilus_trader, LGPL-3.0, so borrow the concept only and copy no code). From `docs/concepts/actors.md:83-102`, take the component state machine RUNNING → DEGRADED → FAULTED with `on_degrade`/`on_fault`.
   - Map onto Apex: each observer and advisor runs in its own guard. On an exception it becomes DEGRADED, and its output is replaced by `{"veto": False, "why": "advisor faulted", "faulted": True}`. That flag is stored with the trade, so learning can exclude faulted rows.
   - The engine itself goes FAULTED only when the core path fails (market, domino, books). This is the systematic fix for T1. Keep the "faulted" flag out of the trigger: it is a recorded state, not a vote (I-11 safe).

3. **pydantic/pydantic** (https://github.com/pydantic/pydantic, MIT). Use `ConfigDict(extra='forbid')` (`docs/concepts/models.md:267-272`) and discriminated unions (`docs/concepts/unions.md:174,217`).
   - Map onto Apex as a **tooling/preflight change only**. Describe each variant with a `kind` tag (`trigger | gap | bookexit | spike | random | momentum`) and a typed model per kind, validated in `config.validate()`.
   - Typos and conflicting flags then fail preflight (T3), and `paper.py` can dispatch on `kind` instead of a chain of `p.get`.
   - pydantic is already present wherever the gateway runs, because fastapi depends on it. If the owner wants the engine to stay numpy-only, a twenty-line hand-written allowed-keys table gives 80 % of the benefit.

## Top 3 (ranked)

1. **Guard advisors and observers individually, and give the heartbeat meaning.** Size **S**, **before Monday**.
   - Wrap each advisor in `advise()` and each update in 250-262 in a shared `safe(name, fn, default)` helper, so a fault yields `veto False, faulted True` and `run_books` always runs.
   - Move `run_books` exits before advisors, or into their own try block.
   - Set `engine_hb_ns` only after a step succeeds, and have `run_apex.py` (or the dashboard) flag a heartbeat older than 5 s.
   - Add one test that injects a raising advisor and asserts that a stop still fires. This is the T1 probe made into a test.

2. **One advisor registry with per-advisor registration dates.** Size **M**, **later** (the change touches learning and must not change the decisions already recorded).
   - Derive `learning.ADVISORS` and the dashboard labels from the registry.
   - Screen each advisor only on RAW trades dated after its own `registered` date and carrying its key.
   - Add a `validate()` check that every advisor key `advise()` produces is registered.

3. **Strict variant schema in `config.validate()`.** Size **S**, **before Monday**.
   - Keep an allowed-keys set per variant kind, reject unknown keys, and reject more than one behaviour flag.
   - Then refactor `paper.py` to dispatch on a `kind` field and drop the three copied gate loops (later, size M).
