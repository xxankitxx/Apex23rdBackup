# Changelog

## 7 Nov 2026 (late) — Conductor stage 2: the weather photograph (the eight factors)
- **`apex/engine/weather.py`** (an observer: no book reads it). At every entry trigger (`paper.request_entry`, used by
  paper books, council books and the missed-signal counterfactuals) the pending entry gets `weather_trig`, copied to
  the position and so into `paper/<day>.json`; missed rows carry it as `weather` (`snapshot_id` = the episode id).
  The eight: calendar (mins_open, phase, weekday, dte, expiry_day); efficiency (er60 / dir60 exactly as R-002
  defines them, er_day); range (pos_in_range, pos_dir, give, range_on, dist_hi / dist_lo, or_pos, or_late); breadth
  (breadth_dir exactly as R-003 defines it); OI wall (wall_room in the trade's direction); straddle (chg5, excess,
  expanding, state); theta breakeven (|theta_min| / |delta| in spot pts per minute, against speed15, the mean 1-min
  spot move over 15 min); VIX (level, change since the day's first reading, 15-min change). Missing data is None,
  never 0.
- **No look-ahead by construction:** every history is stamped with its arrival time (the engine's virtual clock; VIX
  by its own `vix_ns`) and every function reads only samples at or before the asked time. The leak test feeds the
  same day to two points in time and checks that the photo at the earlier one is identical, and that wild prints
  after it change nothing.
- **Live-only note:** the histories start empty at a restart, so er60 / breadth / speed15 are undefined until enough
  data has arrived again (an hour for er60). A replay starts at the open and has them.
- Tests: test_weather.py (leak test, definitions, hook, the real engine); test_missed.py row fields. Suite: 385
  passed, 0 failed.

## 7 Nov 2026 (night) — rules frozen, spec reconciled, test suite green
- **Rule register** (`apex/rules/register.json`, docs/31): the five hand-written rules frozen today with exact
  formulas (ER60, BREADTH_DIR), numbers, families, restricted and free books; test days from Mon 9 Nov. R-001
  (expiry retests end 11:30) keeps its original 21 Oct date. The existing restricted-vs-free pairs are seeded at their
  original dates (R-006 to R-018). R-005 (no entry after 14:30 for families whose median hold > 15 min) holds ORB
  only on the live record. `tests/test_rule_register.py` pins every frozen rule: an edit fails the suite.
- **docs/28 reconciled:** switch-off is the two-sided e-value (`e_value_mean_le0` on the daily differences and on their
  negation, off at 20), no 40-day window; returns, not rupees, in the luck margin and the worked example;
  representatives are the least-gated members everywhere (§3, §5, glossary); spot_ft_prem10 under first-touch;
  test numbers in §14 (tests 3–4, 5b); determinism is checked at the Conductor build; the glossary's "never worked"
  matches §4.
- **Test suite green:** 377 passed, 0 failed (8 gateway tests skipped: `httpx2` not installed; 3 expected failures
  with reasons). Root cause of most old failures: suites switched `config.FILL_NEXT_PRINT` / `REPLAY_LOCKSTEP` off at
  import, so the last file imported decided the value for all; conftest now gives each test file its own value.
  Stale counts updated (71 books); the defects test uses its own paper folder; no engine change.

## 7 Nov 2026 (evening) — stakeholder code review round 2: replay fidelity
- **`apex/replay_compare.py`**: two run folders, per day: books / trades / fields exact, tapes line by line (#cf
  lines out; DATA lines optional), recorder errors fail the day; one verdict per day, non-zero exit on a difference.
- **Batch driver:** every restarted-feed part of a tape is listed and hashed; the tape's own meta record; `--seed`
  also copies `day_levels.json`, `strike_levels.json` and `defects.json` (hashed in the manifest); per day what the
  engine actually ran with (default book, gates, gate: books); Python, numpy and platform; a hash of every config
  constant (`feed_core.config_hash_full`; the old `config_hash` stays for old tapes); each child's output in
  `tape_XX.out`; refuses to run without `config.LEARN_DECIDE`; a stopped run is marked "aborted"; git checked once.
- **Quarantine windows per cluster** of quote-defect trades (30 min gap), not one window per day; a session-long
  automatic window removes the day like a declared one. Evidence only; no trading decision changes.
- **Opening range after a late start:** a first trusted print more than 10 min after 09:15 (a cold restart) leaves
  the range unknown: no OR levels, no ORB trade that day. Normal days and replays unchanged.
- **Day state view:** `give` (share of the leg given back), `pos_in_range`, `or_late`, for the factor search.
- **Feed:** a WARNING when the in-order dispatch (D-106) cannot be installed, and a `feed_sync` flag shown on the
  dashboard's data-health line ("FEED SLOW MODE"); a reconnect no longer reports the installed hook as a failure;
  `python-engineio` added to requirements.
- **Comments:** the seqlock's single-writer and x86 assumptions and who writes each control field; snapshot cost;
  the older-packet rule in `apply_packet`; depth segment routing; the mid-day table zeroing; recenter under the GIL;
  the fired-id ranges per family; domino state kept by position.
- Tests: test_review2_7nov.py, test_replay_batch.py; test_c10_daystate.py feeds at 09:15. Suite: no new failures.

## 7 Nov 2026 (later) — stakeholder rounds 4–5: record-only learning, run manifest, review fixes
- **The learning loop is record-only** (`config.LEARN_DECIDE = False`, owner): its nightly report still says what it
  would have done, but it never changes the default book, retires a book, or adds/removes a gate or candidate book.
  The deciding code stays (its tests switch it on).
- **Photograph at the trigger:** `signal_trig` / `edge_trig` stored at the entry request and copied to the position.
- **Per-day reset** of the edge observers' EWMA / OFI state and the frozen-contract check at the start of each day.
- **DATA events on market time:** the frozen hero-contract line is written from the engine step once per market
  second, not from the wall-clock dashboard publish, so a replay's events tape is reproducible.
- **`apex/replay_batch.py`** (not run yet; replays wait for the Conductor build): one fresh folder per batch run, a
  `manifest.json` (tapes and hashes, commit, code hash, switches, starting learning state, book order, per-tape
  trades, recorder rows / errors / faults, wall time), private shared memory, no dashboard.
  `replay_fast --gateway` refuses to start while a live session holds the default names.
- **Recorder:** council strength from the strategy's own `_buy_v`; an assert that no council book reaches the paper
  twin path; `replay_fast.run()` sets the fast path itself.
- **Small fixes and comments:** the guard's bad-print test is a flag, not a text prefix; the c20_9x `gbw` undo also
  restores the last-exit mark (a no-op today; `gbw` is not in the live combination); comments on `_SER` (offline
  only), the 150-pt parity reset, the 252 × 22,500 annualisation and the two order-book imbalance inputs.
- **Docs:** docs/28 §16a (owner's decisions, per-row families, the seeded register, diaries, manifest, e-value
  monitor, reuse list); docs/29 C6, C16, 4.1 and the breakout-window note; docs/30 F9 (five books) and F10.
- Tests: test_replay_batch.py, test_review_7nov.py, test_missed.py additions. Suite: no new failures.

## 7 Nov 2026 — book guide; filler bug fixed
- **docs/30_BOOK_GUIDE.md**: how every one of the 72 books trades (entries, strikes, holds, exits in code order, live
  figures), read from the code with file:line references, and the issues found while writing it (Part F).
- **Fixed: the t28 retest filler traded past the pullback book's 14:45 entry end** (t28_fill, t28_all, t28_core_fill,
  t28_d46_fill). It fired on any "no" from the pullback rule, including "too late", range mode and the data-gap block,
  and entered after 14:45 and even after the 15:00 book flatten (closed a second later): 41 trades, −₹43,293 live
  29 Oct – 6 Nov. The filler now fires only when the pullback has no setup (`paper._pullback_closed`). Shadow books
  only; the live system was never affected. Tests: test_c13_team.py.
- **Owner's decisions (7 Nov):** entries until **15:15**, flatten **15:25** (the 19 Oct closing-auction test values
  15:29 / 15:35 retired; `CAS_TEST` off); the council's own clock exit ("COUNCIL TIME") fills at once like the forced
  flat; straddle_spike and premium_momentum respect |delta| ≥ 0.52 (`config.MIN_ABS_DELTA`); controls never enter
  the Conductor pool; families are entry pattern × day type.
- **Fixed:** a fill that `open_trade` rejects (unaffordable) no longer leaves the trigger's direction in the book.
- **`worst_pts`** is tracked on every position (paper and council), for the diaries' loss labels.
- **Missed-signal recorder, round 3** (docs/29): error and fault counts with a daily summary; straddle-spike consume;
  fire_count in seconds; relation while pending; council strength; stable setup identities; new row fields; a
  counterfactual can never write the shared LiveDay or the engine log. LiveDay warns when its columns are full.
- **docs/28 version 3:** the stakeholder's corrections: absolute-profit test, returns not rupees, Conductor-level
  sign-flip margin and window, day-level null, per-family "never worked" threshold, families by entry × day type,
  explicit phase coverage, priority before book order, leak test by arrival time, and all replays at the Conductor
  build (owner).

## 5 Nov 2026 — the reviews' quant layer (display only), speed, two bug fixes
- **apex/quant/** (reviews/ teardown, DeepSeek x2): Black-76 to third order and full repricing, a premium-outcome
  (two-barrier first-passage) model, Hawkes intensity with exact and binned MLE, a Gaussian HMM with a semi-Markov
  duration layer, bipower jump test / CUSUM / Kyle lambda / Kalman velocity, quasi-explicit SVI. 32 tests.
- **Tested as yes/no rules on c20_9y** (kit, 12 days, models fitted leave-one-day-out): none adds profit; the
  premium race's probabilities are uncalibrated (predicted 1 % -> 17 % actual, 98 % -> 23 %); as an entry engine it
  trades ~50 times a day and loses. No new book; c20_9x champion, c20_9y shadow. docs/24_REVIEWS_QUANT_LAYER_5NOV.md.
- **Dashboard**: a "Quant evidence" block (premium race for the ATM call and put, Hawkes flow, jump and drift-change
  alarms, regime posterior with minutes left, third-order Greeks, smile residuals), from apex/engine/quantview.py
  once per second inside the fault guard. Parameters in apex/quant/params.json.
- **Speed, no decision changed** (72 of 72 books trade-for-trade identical on the 4 Nov 09:15-10:30 replay; 20.6 vs
  23.7 ms per step): publish serialises without the recursive NaN scrub unless the output holds NaN/Infinity
  (StateBlob.write_state, byte-identical); the kill-switch file is stat'ed at most twice a second; all council books
  share one LiveDay.
- **Fixes**: c20_9y faulted on its first live second (LiveDay had no i_at); a numpy array holding NaN crashed the
  state write.

## 4 Nov 2026 (night) — twenty-member panel C12; c20_9y shadow
- Twenty members, one mathematical angle each (gamma-theta breakeven, Kalman, variance ratio, CUSUM, SPRT, σ-trail,
  Taylor premium model, vanna, charm, OFI, GEX walls, re-entry, ...), red team on the best six, synthesis
  (docs/23_TWENTY_MEMBER_PANEL_4NOV.md). Every exit idea failed (cuts the runners). Two entry vetoes survived:
  IV_RICH (ATM IV > 3.5 vol pts over its median since 09:20) and OI_WALL (normal days, max-OI resisting strike
  <= 25 pts ahead). Kit, 12 days: +12.32 L vs c20_9x +11.24 L; losers 36 -> 28; no winner lost. Registered as
  shadow c20_9y; c20_9x stays champion. tests/test_c20_9y.py.

## 3 Nov 2026 (night) — stuck-trade panel; c20_9s shadow
- Ten-member panel on trades held 10+ min that never perform (docs/22_STUCK_TRADES_PANEL_3NOV.md). Six exit/entry
  rules failed (cliffs or losses); the stale-impulse pullback veto passed: on normal days refuse a pullback whose
  breakout is > 660 s old. Kit, 11 days: +12.26 L vs c20_9x +11.50 L; stuck trades 15 / -77.8k -> 10 / -31.3k;
  expiry days unchanged. Registered as shadow c20_9s; c20_9x stays champion. tests/test_c20_9s.py.

## 3 Nov 2026 (evening) — expiry trail tested, not promoted
- Shadow council books c20_9e (expiry give-back trail: arm +5 pts, give 6 pts) and c20_9h (half-of-peak floor from
  +15 % on expiry days). Replayed on 19 Oct, 27 Oct, 3 Nov: c20_9x +5.17 L, c20_9e +1.10 L, c20_9h +0.21 L
  (docs/21 §8). c20_9x stays champion. Dashboard names EXP_TRAIL / HALF_LOCK exits; tests/test_c20_9e.py.

## Unreleased — 3 Nov 2026 (dashboard: a council position shows its real exit rules)

- **Why.** The ten-member live-vs-tape review (docs/21_LIVE_VS_TAPE_3NOV.md) found the band showing the t28 books'
  12-pt spot trail and +18 % profit lock for the c20_9x champion, which inherits those parameters but never runs
  them: "Stop not set yet" and "LOCK ARMS AT +18 %" all day, an exit chip that only said "COUNCIL", and 158
  commentary lines of "[giveback: TypeError]" (the give-back warning formatted a None stop distance).
- **The council adapter publishes the strategy's own rules** in `pos["rules"]` every second it holds: the −15 %
  premium stop level, the forward trail (best smoothed forward since entry, the trail size, the exit level, the
  give-back so far), the hold clock (15 min expiry / 90 min normal) and time left, the premium floor that is armed
  (break-even / give-back / ramp / rent) or the peak gain that arms the next one, and the +70 % premium trail once it
  is on. Display only; nothing feeds a decision (`apex/engine/council/__init__.py` `Adapter._rules`).
- **The publish** no longer sends `on_spot` / `d_star` / `lock_pct` / `lock_trail_pct` for a council book, and
  `time_exit` is the council's own flat time (15:00 expiry, 15:20 otherwise).
- **The band**: a council rail in forward points ("FWD PTS TO TRAIL", forward / best / trail size / % left, NEAR
  TRAIL at a quarter of the trail), the floor row ("FLOOR ARMS AT +15 %" with the peak bid, or "BE LOCK 100.00 ·
  at break-even"), the stop and the clock on one line; once the premium trail arms the rail switches to the bid.
  The exit chip and the trades table read the council code ("BE_LOCK" → "Break-even floor (peaked +15 %, sold at
  entry)", "SL" → "Premium stop −15 %", "TIME" → "Hold clock ran out", …), the trigger panel explains "COUNCIL EXP
  brk v=+21", and the lead-book sentence describes the council rules instead of the spot range.
- **Commentary**: the give-back warning takes its guard sentence from the rules when there is no spot stop
  (`commentary.guard_text`); the hold commentary's trail size is the council's forward trail.
- **Records**: the exit's wait is `exit_fill_delay_s` (a new CSV column); `fill_delay_s` stays the entry's. The
  engine logs its tick time (p50 / p95 / max) once a minute whenever a tick in that minute took over 300 ms.
- Not changed: any trading rule. Tests: `tests/test_council_view.py`.

## Unreleased — 2 Nov 2026 (fix: the Best tile could fall during a live trade)

- **Best never falls now.** The engine records its peak from one print a second, but the tile also took the
  current tick, so a tick high between engine samples showed as Best and then vanished on the next tick. The tile
  now keeps the highest value it has seen for the trade (engine peak, profit-lock best, or a fresh tick).
- **The premium chart's "best" label reads the same value.** It used to read only the browser's own buffer, which
  dropped its oldest points after about 12 minutes (so a long trade lost its peak) and starts empty on a reload.
  The buffer now thins its older half instead of dropping it, always keeping its highest point.
- View only: the engine, its peak and the trade records are unchanged. A page reload during a trade restarts the
  tile from the engine's own peak. Tests: `tests/test_best_tile.py`.

## Unreleased — 2 Nov 2026 (dashboard redesign: "night instrument panel")

- **Whole dashboard restyled by a ten-member design team** (director, eight section designers, integrator). Deep
  layered glass surfaces, 1 px hairlines, luminous tabular Chakra Petch numerals; glow only where it means
  something (green calls, coral puts, gold trigger). Design system recorded in `docs/UI_DESIGN.md`.
- `style.css` rebuilt section by section on one token set (surfaces, lines, radii, spacing, type scale, motion).
  Every state keeps a distinct look: stale (FROZEN, dashed, desaturated, canvases too), nodata, held, hot, flash,
  clock phases, VIX levels, band states, commentary states. Reduced motion switches all animation off.
- Canvases (trigger, futures trace, OI map, straddle, position path) redrawn sharp at any devicePixelRatio, with
  pixel-snapped gridlines, label chips and meaning-only glow. Drawing code only; no data or threshold changes.
- Small markup hooks: the verdict gets a `near` look when all three corners are at 80 % or more; the position band
  carries `data-rr` so its CALLS / PUTS pill takes the side colour; the trades table scrolls inside its panel; a held
  ATM tile drops the word "ATM" so the strike stays readable beside HELD.
- Phones: the header is no longer sticky below 820 px (it is six rows tall there). The futures chart grows with the
  trigger column above 1280 px, capped at 440 px.

## Unreleased — 2 Nov 2026 (ATM CE / PE in the header)

- **Two new header tiles, ATM CE (green) and ATM PE (coral), between Spot and VIX**, the same size and style as
  the Spot numeral. Each shows this week's at-the-money contract (the engine's `atm` strike and `w0` expiry),
  its last traded price painted on the tick like Spot is, and a sub-line with bid / ask plus delta and IV from
  the hero list. A tile the champion is holding gets an ink border and a HELD badge. Before the chain exists
  the tiles say so; after an ATM roll they switch to the new strike and wait for its first print. Fed entirely
  in the browser from the tick stream and the existing state frame: no engine or gateway change.
- **Header grid re-flowed for ten cells**: one row from 1760 px, two rows of five below that (futures, ATM CE,
  ATM PE and capital on the first; Spot, VIX, ATM IV, Clock and feed health on the second), two columns on
  phones. `tests/test_header_atm.py` checks every `grid-template-areas` in the stylesheet is rectangular and
  every header layout places every cell.

## Unreleased — 2 Nov 2026 (tests fenced off the live data)

- **`tests/conftest.py`: every test runs against a throw-away data tree (D-149).** A `pytest` run at 07:51 on
  2 Nov deleted `data/learning/days.jsonl` and `defects.json`, overwrote `state.json` with a synthetic scoreboard
  (shown on the dashboard all day as "10 trades, +4000 %"), rewrote the 21–23 Oct paper files and left 45 report
  files for dates up to Feb 2027: tests wrote through `config.PAPER_DIR` / `LEARN_DIR` and through the paths that
  `learning.py` and `defects.py` fix at import. The session-wide autouse fixture now redirects `DATA_DIR`,
  `TICKS_DIR`, `PAPER_DIR`, `LEARN_DIR`, `LOG_DIR`, `KILL_FILE`, `learning.STATE/DAYS/REPORT` and
  `defects.DEFECTS_FILE` to a temporary directory, and fails the session if anything under the live `data/`
  changed. Repair the same evening: tracked files restored from git (`days.jsonl` to 23 Oct, `defects.json`,
  `state.json` to 23 Oct with the owner champion re-applied, the 21–23 Oct paper files); 26 Oct – 2 Nov rebuilt
  from the paper records by the learning module itself; the evening look for 2 Nov run (the engine had been killed
  at 15:28 before recording the day); 2 Nov high / low / close written from trusted prints only (the index feed
  printed 23769 at 15:20 after a credential error). Not recoverable: the champion-change log between 23 and
  30 Oct, the 24–30 Oct strike levels, any defect windows declared after 23 Oct.

## Unreleased — 2 Nov 2026 (sounds)

- **Sound only for trades** (owner: "no unnecessary sound if there was no event like an entry"). The engine speaker
  plays a cue only when the champion buys, sells (win / loss) and once when the day is learned. Gone: the Triangle
  "armed" chime, the straddle-spike chime (every spike, 60-s throttle), the browser's oscillator beeps on ARMED and
  SPIKE, its commentary warning beep and the EXIT-SOON double beep. `apex/audio.py` no longer looks for mp3 files
  (the MYTHOS project's alerts were playing); the four cues are synthesised at start (numpy, 44.1 kHz, peak-normalised
  and soft-clipped, so loud without distortion) and opened on a mono mixer with `allowedchanges=0` (SDL otherwise
  opens stereo and a mono buffer plays at double speed). `static/app.js` plays the same four recipes through Web Audio
  (`sfx()`), remembers the Sound toggle across reloads, and treats the tape as first seen as history (no sound on load).
  Cues: entry = rising power-up arpeggio; win = fanfare into a sustained major chord; loss = four falling notes, the
  last sagging and wobbling; learn = two bells with a sparkle. Original chiptune-style synthesis, nothing copied from
  any game. Tests: `tests/test_audio.py`.

## Unreleased — 1 Nov 2026 (C9 council: c20_9v shadow)

- **`c20_9v` (shadow)** (owner, 1 Nov: "Yes, add as shadow"), from the 10-member C9 council on c20_9x variants
  (owner: "make each day more profitable and especially friday 30th october profitable"). c20_9x plus two exits on
  normal days only (expiry days are pure c20_9x; `apex/engine/council/c20_9v.py`):
  **LVL_BOOK** — the 50-pt round numbers of Nifty ahead of the trade are fixed at entry; sell when the bid is ≥ +6 %,
  the peak is still < +20 %, spot came within 13 pts of the next level (not broken by > 8) and gave back ≥ 10 pts;
  **PGB** — once the 20-s average of the bid has been +15 %, sell when it falls below entry + 60 % of its best gain.
  9-day engine replay (real fills, gross): c20_9v +₹9.74 L vs c20_9x +₹9.30 L; 30 Oct +₹11,622 vs −₹5,558; 21 Oct
  +₹23k, 28 Oct +₹27k; 23 Oct −₹22k (LVL_BOOK sold the 09:41 22800 PE at +9.8 % that c20_9x rode to +77 %); the other
  five days trade for trade identical. Kit: +₹12.48 L vs +₹11.49 L. Other council angles (switch permutations, earlier
  floor, swing-sized trail, box detector, entry vetoes, Greek/IV exits, stall/time exits) did not beat c20_9x robustly.
  67 variants.
- **c20_9v review fixes** (same day, from an eight-angle code review of the new book). (1) A frozen Nifty print
  (the D-132 guard withholds it and the adapter carries the last value forward) no longer disables LVL_BOOK: a print
  unchanged for 120 s counts as stale and the reference falls back to forward − basis, with the basis measured only
  against new prints. (2) The exits' state (smoothed bid and its peak, the level list and the best) now lives in
  `pos["st"]`, which the council adapter keeps on the book position and saves with it, so a mid-trade engine restart
  keeps the PGB arm and the levels fixed at entry, like c20_9x's own `peak_bid`. (3) When the reference changes source
  (print ↔ forward) the best-since-entry is re-based, so a basis jump is never a rejection. Five behavioural tests
  (LVL_BOOK fires on a 10-pt rejection at the next 50-pt level, is off on expiry days, works through a frozen print,
  ignores a source jump; PGB fires and survives a restart). Not changed: the LVL_BOOK label, shared with c20_8x's unused
  `lvl` layer; PGB's own smoothed bid beside c20_9x's `ptr` one; the exits sit in a mixin rather than `parts` switches.

## Unreleased — 31 Oct 2026 (rent trail)

- **Champion stays `c20_9x`; `c20_9t` is a shadow** (owner, 1 Nov: "Yes, revert to c20_9x"). The 8-day replay (19–29
  Oct, real fills, + 30 Oct) gave c20_9t +₹3.89 L vs c20_9x +₹9.30 L (t28_gap +₹3.76 L); it won only 30 Oct. The trail
  armed on nearly every trade, trend days included, booking ≈ +5 % where c20_9x ran +77 % (23 Oct), +81 % (21 Oct),
  +45 % (29 Oct), +18–23 % (26 Oct). Likely cause: trend efficiency < 0.35 is the normal state (30 Oct median 0.25),
  not a chop signal. Kept for live measurement; any new chop test is replayed on all taped days first.
- **`c20_9t` (shadow)**, built 31 Oct (owner: "I want a stronger trailing system on days which are not
  trending and the greeks also do not support holding for too long"). 30 Oct live: c20_9x's three trades peaked
  +15.1 %, +13.2 %, +17.6 % and exited +0.7 %, −4.6 %, 0.0 % — the normal-day floor only arms at +15 % and protects
  only the entry until +25 %. `c20_9t` = c20_9x + **rent trail** (`apex/engine/council/c20_9t.py`, switch `rt` in
  c20_9x.py): once the peak bid is ≥ +8 % and the market is choppy for the trade — the held contract's gamma rent
  (realised ÷ implied variance of the forward, last 10 min, calendar theta) has fallen to half its value at entry (the
  move went quiet) OR the forward's 10-min trend efficiency (|net move| ÷ sum of |1-min moves|) is below 0.35 (two-way
  chop) — the trail arms for the rest of the trade: exit when the bid falls below entry + 60 % of the peak gain
  (`RENT_TRAIL`). Neither condition (trending) leaves c20_9x's exits alone. Both day types: the market decides. A
  same-side re-entry within 15 min of a rent-trail exit needs a faster forward trigger than the booked trade's and
  trend efficiency ≥ 0.35 (owner: "a stronger reason than why the trade got trailed"). Calibration on the 30 Oct tape:
  the first version (absolute rent < 1) never fired — rent sat at 1.1–10 through all three trades, so c20_9t traded
  exactly like c20_9x in the replay; rent-halved catches trades 2 and 3 (~10 min in), efficiency < 0.35 catches trade 1
  (the whole day's median efficiency was 0.25). 8 % / 60 % / 0.5 / 0.35 / 15 min are the owner's picks of 31 Oct.
  66 variants.
- **Peak display fix.** The dashboard's "Best" tile is `entry + peak_pts`, which only `check_exit` maintained, so for
  council books it followed the price down and never showed the real peak. The adapter now updates `last` and
  `peak_pts` every second (not in a blackout), so the tile, the trade record and the CSV carry the true peak.

## Unreleased — 30 Oct 2026 (champion c20_9x)

- **Champion `c20_9x`** (owner, 30 Oct pre-open: "c20_9x as champion"; "I want them to run today"). The round-9
  strategy (docs/20_C20_9X_STRATEGY_SPEC.md) runs as a **council book**: `apex/engine/council/` holds the exact
  classes tested in the offline kit (`c20_08` → `c20_20` → `c20_8x` → `c20_9x`), and `council.Adapter` feeds them a
  live per-second `D` (forward, quotes, Greeks, OI of the nearest weekly) and trades through `paper.open_trade` /
  `close_trade` (all-in, |delta| ≥ 0.5 at the signal, forced flat 15:00 expiry / 15:20 otherwise). Champion and RAW
  council books raise ENTRY / EXIT events and the entry / win / loss sounds like any champion.
- **Shadows:** `c20_8x` (council) and yesterday's champion `t28_gap`; every other book unchanged (65 variants).
- Engine replay (test copy, real fills, cut at ~14:30 on most days): c20_9x +₹10.32 L over 7 days, 29 Oct +₹26.4k;
  c20_8x +₹8.06 L / +₹7.9k; t28_gap +₹3.47 L / +₹4.0k. Honest leave-one-day-out of the round-9 gains ≈ +₹1.6 L.
- New test file `tests/test_c15_council.py`; champion asserts moved to `c20_9x` / 30 Oct.
- **Code review of the port (30 Oct evening).** All nine round-9 parts match their members' code parameter for
  parameter (`l2`, `ffirst`, `seqcal`, `catch`, `dtr`, `ramp`, `ivz`, `ptre`, `tie`). Two adapter defects fixed:
  - council books filled at the print on the screen at the trigger second, bypassing D-126 (every other book waits
    for the first print AFTER the trigger: ≤ 3 s in, ≤ 10 s out). Now `paper.request_entry` / `try_fill_entry` on the
    way in and new `paper.request_exit` / `try_fill_exit` on the way out, with the same deferral, blackout and
    `stale_exit` rules. The strategy is not stepped while a fill is pending (the kit skipped its 2-s lag the same way;
    `catch` bridges the smoothed forward). **Every earlier engine figure for c20_8x / c20_9x is optimistic by the
    fill-timing bias D-126 removed for the other books.**
  - a held contract missing from the adapter's table fell back to column 0 (another contract's quote for the stop and
    floors); the strategy is now skipped for that second and a line is logged. The position's `peak_bid` is saved
    with the book so an armed floor survives a restart.

## Unreleased — 29 Oct 2026 (entry checks: "a little cheap, won't break down")

- **Three shadow books** (owner, 29 Oct midday; champion unchanged, 63 variants): `t28_fwd` (the champion's rules on
  the put-call-parity forward of the nearest weekly, shifted by its 30-min median gap to spot; 19 Oct study R² for
  option moves: future 0.45, spot 0.66, forward 0.94), `t28_mh15` (out after 15 min), `t28_tt8` (gain trail arms at
  +8 %, keeps 70 %). Short 23 Oct engine check: all three trade, no faults. The forward's histories survive a warm
  restart.
- **Champion back to `t28_gap`** (owner, 29 Oct 11:40: "Switch the champion back to t28_gap now and keep t28_cheap
  running as a shadow book"). Live, `t28_cheap` skipped both of the day's signals on the required-move check by ~3 pts
  (10:58 CE: needed 33 vs 30 moved; 11:14 PE: 32 vs 29), and a skipped signal marks its whole impulse as used.
  `t28_gap` took the 10:58 CE. Engine-only restart; the open trade carried over.
- **Champion `t28_cheap`** (owner, 29 Oct morning, replaced the same day: "Yes, promote t28_cheap to champion"): `t28_gap` entries and exits unchanged
  + two yes/no entry checks, no score:
  - **not at the high:** on pullback / retest entries, skip if the option's mid is within 2 % of its 5-min high
    (`entry_hi5_veto_pct=2.0`);
  - **move must be realistic:** skip if the spot move needed for +10 % (delta, gamma, theta over 15 min) is larger
    than the last 15-min spot range (`req_move_veto`, `req_move_k=1.0`).
  Engine replay, 7 days, real fills (ask in, bid out): **+₹4.59 L vs `t28_gap` +₹3.73 L**, no day worse
  (19 Oct +₹47 k, 27 Oct +₹21 k, 28 Oct +₹18 k), 55 trades vs 62. Caveat: the gain rests on 7 skipped trades; the
  second check is sensitive to ±30 s timing in research.
- **Ideas board** (owner, 29 Oct: "I want to test my ideas later ... somewhere in the UI"): `apex/engine/ideas/`, 16
  observer cards (move clock, OI writers, writer squeeze, OI walls, fresh-OI PCR, queue speed, aggressors, gamma vs
  theta, IV pulse, cheapest strike, regime, arm → fire, room to run, straddle pulse, peak watch, premium
  continuation), written by a 15-member council. Shown on the dashboard, every state change taped to
  `<paper dir>/ideas_<day>.jsonl` with the champion's position. **No book reads them**; a card that faults 5 times
  or runs slow is switched off for the day. `tests/test_c14_ideas.py`.
- **Champion `t28_gap`** (owner, 28 Oct evening): `lvl_trail_re` + no pullback measured across a data gap (120 s).
- **Shadow books:** `t28_nohigh`, `t28_req` (each check alone), `t28_cheapK` (expiry-day lag-cheapest strike, ATM–2
  ITM; +₹10 k on 19 + 27 Oct), `t28_ivfall`, `t28_bidpile`, `t28_st20`, `t28_gap_ts` (60 variants). Engine keeps a
  1-Hz per-option history (`ctx["ohist"]`) for these checks.
- **Rejected on the replay / research:** OI quadrants, walls, PCR, OI-acceleration + VWAP (−₹1.04 L as a trigger),
  buyers-vs-sellers queues, greek timing filters, regime gates, waiting for a dip, tighter trails, time stop.

## 1.10.1 — 28 Oct 2026 (trail, strike levels, re-entry; docs/18 §6b)

- **Champion `lvl_trail_re`:** `spot_dual_lvl` entries (no entry gate) + hard premium stop −10 % + gain trail on the
  30-s average premium (arm +20 %, keep 80 %) + expiry-day max hold 10 min + the owner's re-entry rules (after a
  trailing exit: cheaper or the next OTM strike for 30 min, stronger trigger within 10 min; after a stop: stronger
  trigger within 10 min). Six-day engine replay: +₹3.87 L, **6/6 days green** (old champion +₹3.48 L, 4/6).
- **Each strike's premium support / resistance** (`apex/engine/strike_levels.py`): taped and carried on trades,
  evidence only.
- **Shadow books:** `edge_gate_trail`, `lvl_trail`, `lvl_trail_rx`, `lvl_trail_rx_c10`, `lvl_trail_rx_be`,
  `lvl_trail_be` (43 variants). Breakeven guard and the opening-range wait were rejected on the replay.
- **Sizing:** all-in on every trade, no position sizing (owner's rule). `run_apex.py --port` runs replays in parallel.

## 1.10.0 — 27 Oct 2026 evening (buyer edge; docs/18_BUYER_EDGE.md)

- **Diagnosis, six live sessions (106 trades):** the entries carry no directional edge (option mid moves summed to +3
  pts over all trades); the 12-pt spot trail exits inside the option's ±13 % noise; options were bought when dear
  (27 Oct: IV 28–36 % vs realised 8–12 %); four champions in six sessions, each chosen on 1–3 days of replay.
- **Research files tested on the six days' ticks:** order-flow imbalance, book imbalance, micro-price, put-call-parity
  synthetic forward, Bank Nifty lead and momentum show no edge for an option buyer. The theta-vs-gamma test does.
- **Champion `edge_gate_only`:** `spot_dual_lvl` unchanged + **buyer-edge gate** (½·Γ·realised variance/min ≥ 0.5 ×
  |Θ/min|). Engine replay, six days: +₹2.50 L, 21 trades, 76 % winners, +10.5 %/trade (old champion +₹3.48 L, 55 trades,
  +5.5 %/trade; the difference is 19 Oct, in-sample for the old champion). The first pick, `apex_edge` (gate + premium
  bracket −10/+20/30 min + −20 % day stop; replayed at 50 % capital, now all-in like every book — owner's rule), made only +₹46 k on the replay — the bracket caps trend days —
  and is a shadow with `edge_bracket_only`, `edge_breakout` and `spot_dual_lvl`.
- **Freeze rule:** no champion swap or re-tune for 15 sessions or until the SPRT decides.
- New `edge.v_min30`; option rows carry gamma and theta; `max_hold_s`, `day_stop_pct`, `gt_min` variant
  keys. `tests/test_c11_buyer_edge.py`.

## 1.9.0 — 22 Oct 2026 evening (council 9: read the day, book at levels)

- **Day state** (D-141): session high/low, **range mode**, opening range, prior-day levels (`learning/day_levels.json`), round hundreds.
- **Champion `spot_dual_lvl`** (D-142): dual book + range mode + booking at a level the trade cannot break. Engine replay: 19 Oct +₹1,36,594, 21 Oct +₹36,312, 22 Oct +₹1,199 (old champion −₹53,046 replay / −₹52,084 live).
- Shadows: `spot_dual_rg`, `spot_orb45` (opening-range breakout), `spot_ft_prem10` (±10 % premium). `tests/test_c10_daystate.py`. docs/17.

## 1.8.1 — 21 Oct 2026 night

- **Champion is now `spot_dual`** (D-140): retest breakout on expiry day, pullback on other days. Engine replay: 19 Oct +₹1,31,193 (17 trades), 21 Oct +₹55,426 (4 trades). `spot_pb45` stays as a shadow.

## 1.8.0 — 21 Oct 2026 night (four external reviews)

- **Edge snapshot** (D-136): basis, IV/RV, futures book imbalance, OI-wall room, impulse state on every second, entry and decision; an "edge features" table in the evening report. Evidence only.
- **`spot_dual` shadow** (D-137): retest on expiry day, pullback otherwise.
- **Packet-shape canary + parser fuzz test** (D-138). `tests/test_c9_reviews.py`. docs/16_REVIEWS_21OCT.md.

## 1.7.0 — 21 Oct 2026 evening (council 7: few trades, held, profitable on both tapes)

- **Champion is now `spot_pb45`, the pullback book** (D-134): a ≥ 60-pt 45-min impulse, buy only its 50–78 % pullback, once per impulse, stop at the impulse origin, target one impulse beyond, lock on, entries to 14:45, flat 15:00. Engine replay: 19 Oct 5 trades +₹78,647; 21 Oct 4 trades +₹55,426. All-in, LTP, no brake.
- New module `apex/engine/impulse.py` (O(1) rolling window, warm-state persisted); `tests/test_c7_pullback.py`.
- The retest and first-touch spot books keep running as shadows. docs/14_COUNCIL7_21OCT.md.

## 1.6.0 — 21 Oct 2026 (council 6: why the champion bled on a 6-DTE day)

- **Retest entry** (D-131): a break only arms the level; buy after a 5-pt run and a pullback to within 2 pts (cancel: level lost by 3 pts / 300 s). Old entry kept as `spot_dc12_t12_first`. Engine replay: 19 Oct +90k → +131k, 21 Oct −24k → −1.9k. Two days only.
- **Index sanity guard** (D-132): a frozen or wild NIFTY print (15:15–15:30 on every day seen) can no longer set a range, a best spot, or a trade.
- Tests: `test_c6_retest.py`, `test_c6_feed.py`; `test_wp2` no longer depends on the wall clock; docs/12_COUNCIL6_21OCT.md.

## 1.5.0 — 20 Oct 2026 (council 5: "a piece of art")

- **Fills on the first print after the trigger** (D-126): 19 Oct's ₹4.69 L was priced on prints from before the move; honestly it is ₹1.79 L (same 32 trades). Still LTP.
- **Profit lock** on the spot champion (D-127, owner): +18 % arms, exit 10 % off the best; `spot_dc12_t12_nolock` runs beside. 19 Oct: ₹1,90,161 vs ₹1,81,156 without.
- **Fast replay** `--fast` (D-128): one process, bit-identical, 50 → ~18 min.
- **Live-trade commentary** (D-129): 209 templates / 685 phrasings in three modules, HOLD / WATCH / EXIT-SOON verdict, entry and review cards, tape `commentary_<day>.jsonl`, docs/11_COMMENTARY.md.
- **Dashboard** (D-130): header tiles (Spot / VIX / ATM IV / Clock), the live-trade band (lots, quantity, capital deployed, cash left, Greeks, premium path, exit clock, LOCK), the trades table, the commentary panel.

## 1.4.0 — 19 Oct 2026 evening (plan D-108 … D-115, council 4 D-116 … D-122)

- Exits and the impulse measured on the futures bid/ask mid; σ15 floor 5; 15-pt impulse floor; regime is a gate; 60-s cool-down; expiry day trades the expiring weekly. A daily brake exists in the code but is OFF (D-123: never an owner requirement); `data/KILL` stops entries only if the owner creates it.
- New books: `spot_dc12_t12` and `spot_dc12_t12_1130` (Nifty spot 12-min range break, 12-pt spot trail), shadows `m2.0_s0.5_d20`, `m2.0_s0.5_tvfast`, `fade_switch`.
- `python run_apex.py acceptance <tick file>`: lock-step replay + behaviour checks. Warm state across same-day restarts.
- Lock-step replay of 19 Oct: champion 0 trades (₹1,00,000; live it lost to ₹48,146); `spot_dc12_t12` 32 trades ₹4,68,657 — in-sample, see docs/10 §7.

## 1.3.0 — 19 Oct 2026 (first live session; 30-member council)

Call options were frozen at Friday's close all morning (feed ordering guard) and depth packets hid it; the data guard paused entries ~25 % of the time on a healthy feed and an episode-taint rule another ~30 %; per-stock scales learned from pre-open prints. Fixed: D-095 … D-107 (docs/02, docs/08). Lock-step replay of the 19 Oct tape on this code: champion 4 trades 09:25–10:51 at real prices (was 1 at a frozen price). New pre-registered book `m2.0_s0.5_novol`; evidence quarantine for data defects; data-health line in the header; deterministic replays.

## 1.2.1 — 19 Oct 2026

- Simulator stock model realistic (D-091); dashboard never cached (D-092); day high/low in the header, trades above the futures trace (D-093).
- **Closing Auction Session test (D-094)**: entries until 15:29, flatten 15:35, session to 15:40 (NSE F&O close since 3 Aug 2026); trades tagged by market phase; CAS-window trades shown in their own report section and kept out of the learning decisions; the sim models the auction; the header shows the phase after 15:15.

## 1.2.0 — 18 Oct 2026 (the council build)

Twenty independent reviewers, one assembly (106 findings: 6 critical, 28 high, 44 medium, 28 low; `docs/07_COUNCIL_REPORT.md`), seven work packages built in parallel and merged (D-080 … D-086), and four owner decisions (D-087 … D-090). Tests: 104 in eight suites plus 5 owner-decision tests. Highlights: crash-safe tick recording and replay; every advisor fault-isolated so exits always run; real heartbeats and a STALE banner; atomic, self-healing learning record with back-fill; runtime paper-only interlock; PE book side and `gex_room` forward fixed; stops fire once fresh data returns; SPRT re-registered at σ 30 % with a 30-trade minimum; IV-interpolated variant pre-registered.

Versions follow the decision log (`docs/02_DECISION_LOG.md`); every entry cites its D-numbers.

## 1.1.1 — 18 Oct 2026, 03:00 (audit)

Audit of the night's changes (`docs/06_AUDIT.md`): four defects found by re-reading, seven by an independent reviewer, all fixed with tests (28). Settling period after gaps (D-075); no exit decisions on frozen/implausible data, pricing by key only (D-076); engine sampling holes are gaps (D-077); learning idempotent per evening, day always recorded, promotion day excluded, `futures_only` keeps the champion's exit (D-078); simulator gap drill `--gap` (D-079).

## 1.1.0 — 17 Oct 2026, night (before the first live paper session)

Strengthening from the external reviews (`docs/04_EXTERNAL_REVIEWS.md`, `docs/05_STRENGTHENING.md`).

- **Market regime** classifier and advisor `regime`; every trade and candidate carries the label; the report shows results by regime (D-069).
- **Candidate ledger**: every impulse that reaches the champion's m*, taken or not, with features, decision, would-be contract and a 15-min outcome label (D-070); **diagnostics** in the learning report: hit rates with Wilson intervals by decision, rejection reason, regime, impulse size and advisor verdict (D-071).
- **Bad-print guard**: a futures move > 1 % within 2 s puts the engine in blackout (D-072).
- **Configuration self-check** in preflight and in the tests (D-073); **CI workflow** (D-074).
- Earlier the same night: data blackout guard (D-063), learning in % return / log growth (D-064), control books (D-065), Bonferroni challenger test (D-066), gated-book advisor promotion (D-067), no-order guard test (D-068), dealer gamma map (D-062), straddle watch (D-060/D-061).

## 1.0.0 — 17 Oct 2026

First complete build: feed / engine / gateway, v1 trigger (D-033), paper books, learning loop, dashboard.
