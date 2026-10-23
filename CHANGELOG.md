# Changelog

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
