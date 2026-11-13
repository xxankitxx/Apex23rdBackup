# 13 Nov research data (read-only inputs for the 20-agent study)

Every Python script run during market hours (until 15:30 IST) must start with:

    import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio

(below-normal CPU priority, one math thread). Load only the columns you need: `pd.read_parquet(path, columns=[...])`.

## trades_all_books.parquet
Every trade of all 107 books on the 17 replayed days (run p44: the code as committed 7a3deb5, pool applied to
every day, `APEX_POOL_ASOF=all`). 20,817 rows, 706 columns.

* `day`, `book`, and the book's own trade fields: `time_in`, `time_out`, `t_in`, `t_out` (epoch s), `rr` (CE/PE),
  `strike`, `entry` (ask paid), `exit` (bid received), `ret_pct`, `pnl_rs`, `hold_s`, `reason` (exit reason),
  `ep_type`, `regime`, `why` (entry reason), `peak_pts`, `worst_pts`, `delta_in`, `iv_in`, `iv_out`, `dte_in`,
  `phase_in`, `fut_in`, `fut_out`, `spot_in`, `signal`, `trigger_time` ...
* `wx_*`: the weather photograph at the trigger (about 450 items: momentum, efficiency ratios, opening range,
  breadth of the heavyweights, walls, straddle, theta break-even, VIX, gap, VWAP, distance to day high/low,
  previous day levels, time of day, expiry, ...). Names follow apex/engine/weather*.py.
* `h<mark>_*`: hold marks at fixed seconds after entry (gain, peak, giveback, attribution to delta/theta/IV, ...).

The Conductor's account trades (the live system as replayed): `D:\ApexOptions\data\replay\batch\p44_sim\conductor_sim.json`
(use its days except 28 Oct, 30 Oct, 2 Nov, 3 Nov) and `p44_simr\conductor_sim.json` (those four days). The pool
books are c20_9y, c20_9s, c20_9v, c20_9x, c20_9t (apex/rules/pool.json). Totals in docs/54.

Book-level saved files per day (heavier; read one day at a time): `D:\ApexOptions\data\replay\batch\<run>\paper\`
(`<day>.json` books, `conductor_<day>.jsonl`, `decisions_`, `events_`, `ideas_`, `forecasts_`, `commentary_`).
Day to run: 19/21 Oct g1, 22/23 g2, 26/27 g3, 28 r1, 29 g4, 30 r2, 2 Nov r3, 3 r4, 4 g6, 5/6 g7, 9/11 g8, 12 g9.

## Per-second market data
`D:\ApexOptions\data\research\ds_v2\<part>.npz` (builder and column meaning:
`data\replay\batch\gen2_research_v2_2026-11-10\ds2.py`). 17 days 19 Oct to 11 Nov; 12 Nov is not built. Parts with
rows > 0 are listed in each `.manifest.json`. Arrays: `t` epoch seconds; `fut[:,6]` Nifty futures (see ds2.py);
`opt[t, strike, CE/PE, bid/ask]` weekly options and `opt2` next weekly; `strikes`, `strikes2`; `hw[t, 14]` the 14
heavyweight stocks, `w` their Nifty weights in %, `sym` names, `g` sector; `sf` stock futures; `*a` = ages.
Load one part at a time.

Raw tick tapes (heavy, 3.7 GB, include BANKNIFTY and FINNIFTY spot and futures, INDIAVIX, 23 stocks):
`D:\ApexOptions\data\ticks\<day>[.pN].jsonl.gz`. Only the sister-index agent reads these, one day at a time.

## Live (today is running: read only, never write)
`D:\ApexOptions\data\paper\trades_<day>.csv` (Conductor live: 9, 11, 12 Nov), `conductor_<day>.jsonl`,
`commentary_<day>.jsonl`, `data\logs\*.log`, `data\logs\perf_<day>.jsonl`, `data\forecast_lab\log_<day>.txt`.

## Forecast Lab
`apex\forecast_lab\{core,brain,live,tape,clock}.py`; `data\forecast_lab\walk_forward.json`;
`data\forecast_lab\collect\<day>.joblib` (per-second features, X columns t, F, vref then 46 features).
