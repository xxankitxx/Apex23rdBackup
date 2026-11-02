# Changelog

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
