# 56. What was built on 13 Nov evening from the 20-analyst study

Owner, 13 Nov: "involve 20 agents ... teardown ... improve the entries/hold/exits ... the forecaster has to take a clear
stand ... the system's personal commentary on what it would do ... heavy weight stocks and other indices ... no errors
... blazing fast". Then: "Yes, both" (start the Phase B studies after 15:30 and build the display).

The study: `docs/research/13nov/00_MASTER_PLAN.md` and the 20 reports beside it. Nothing below changes a live trading
decision: the Conductor, its pool (`apex/rules/pool.json`) and the five pool books are untouched. New decision logic
is in shadow books and shadow Conductors with their own accounts, scored forward under the 7-test standard (docs/28).

## Owner point 4: a clear stand and the system's own voice

| Item | Where | What it shows |
|---|---|---|
| "What I would do now" card | `apex/engine/voice.py` (`state["voice"]`, 1 Hz, inside `_safe`), `apex/static/voice.js`, card under the position band | First person, from the lead pool book's real c20 trigger state: WAIT / WATCHING THE IMPULSE / GET READY / READY TO BUY / BUYING / HOLD / CLOSE TO EXIT / SELLING. The 40-pt impulse, the pullback against the 50 % it needs and the 75 % that drops the idea, the fire level, when the arm expires, the contract and lots it would buy, each pool book's veto with its margin, today's record, the last Conductor events. |
| Exit ladder | same card while holding | The real exits from `pos["rules"]`: premium stop, forward trail level and distance, floor, premium trail, clock, forced flat; the nearest one highlighted; HOLD / CLOSE TO EXIT / PROTECTED / SELLING held 10 s. |
| Old verdict retired from view | `apex/static/commentary.js` | HOLD / WATCH / EXIT-SOON is hidden when the voice is present (R12: obeying it turned +182 % into -1 %; it fired on 119 of 119 trades). Still computed and taped. |
| Stand banner | `apex/forecast_lab/core.py` `Lab.stand()`, `voice.js` `labStand`, top of the Forecast section | BULLISH / BEARISH / SIDEWAYS from the 20-minute move and the VWAP distance (R11: enter at +-40, leave at +-20, 90 s hold), the strength, how the market is behaving in points, fact chips marked for or against, and "how sure I am" with the rule's record: right 50 % at 15 minutes (8 of 16 days). It says it is a description, not a reason to buy. |

The voice's "how often I fired from here" figures (`voice.P_FIRE`) are R12's Phase B table: normal days 19 Oct to 11 Nov,
fitted on 19 Oct to 4 Nov and checked on 5 to 11 Nov (Brier better than a constant on all 4 test days), pooled by
sample count. In the test week ARMED fired about half as often as in the fit window, and the card says so.

## Owner point 5: heavyweights by weight, BANKNIFTY and FINNIFTY

* The stand's facts and sentence carry the heavyweight basket weighted by Nifty weight, in Nifty points over 2 minutes,
  and whether it moves ahead of, with or against the future (R08: right 60 to 65 % at 10 to 60 s, nothing at 5 min).
* The sister lead (R09 sweet spot): BANKNIFTY futures mid (its last price is stale 72 % of seconds) and the FINNIFTY index
  (its future is illiquid), equal weight, 10-second look-back, quotes older than 5 s dropped, against the Nifty future
  over the same seconds. Shown as a seconds-scale push. As entry gates both failed walk-forward, so neither is a rule.

## Owner points 2 and 3: shadows (flags off, never the champion)

| Book | Rule | Evidence | Judge on |
|---|---|---|---|
| `tp_c20_9y` | c20_9y with an expiry-day take-profit at +60 % | Phase B per-second (R02): passes R02's own screen (discovery +72.6 log pts, test +76.0, plateau 55 to 70 %) but strike rate is unchanged and the whole test gain is 9 Nov, so it does not meet docs/28; a shadow only | forward expiry days |
| `pgb_c20_9y` | c20_9y + PGB alone on normal days | Phase B (R02): "PGB on every pool book" passes R02's screen (+49.5 / +11.5); strike 52.2 to 53.3 % in discovery, unchanged in test, test gain on 2 days; a shadow only | all days |
| `pm_c20_9y` | c20_9y, no expiry entry from 13:30 | R18: pool trades after 13:30 on expiry won 29 % vs 63 %, lower on 4 of 4 expiry days | expiry days |
| `conductor_sl` | shadow Conductor: refuse a side when today's last 12 closed c20-family trades on it (at least 3) lost more than they won | R20 E6: strike 59.3 vs 52.9 %, worst day -13.6 vs -37.1 %; costs 27 Oct | strike first, worst day |
| `conductor_wp60` | shadow Conductor: after two account losses in a row on opposite sides, no entry for 60 min | R17: strike up in both windows, no day worse | scored with conductor_sl as one hypothesis |

Rejected by Phase B on 13 Nov: the expiry profit floor (R05 `c20_9y_xf`, 0.6 of the peak after +30 %). Per-second on all
four expiry days it lifts 9 Nov from +43 % to +100 % but cuts 27 Oct from +532 % to +338 %. Not built.

Offline check of the built code (`account_sim.simulate(policy=)`, 17 days, early = 19 Oct to 6 Nov, late = 9 to 12 Nov
plus the held-out tail):

| Account | Trades early / late | Strike early / late | Sum early / late | Worst day | Losing days |
|---|---|---|---|---|---|
| conductor | 84 / 35 | 53.6 / 51.4 % | +949.9 / +142.5 | -36.3 | 5 |
| conductor_sl | 57 / 24 | 61.4 / 54.2 % | +833.5 / +150.3 | -12.7 | 5 |
| conductor_wp60 | 69 / 30 | 58.0 / 53.3 % | +1006.6 / +171.9 | -24.6 | 5 |

The built code reproduces R20 and R17: sidelock lifts strike in both windows and cuts the worst day from -36 % to -13 %,
paying for it on 27 Oct (+532 to +342). Whipsaw lifts strike in both windows with no day worse than the Conductor.

The shadow Conductors use one hook, `Conductor.admit()`, which returns None in the live Conductor (no change), and the
same policies run offline through `apex.conductor.account_sim.simulate(..., policy=)` (`conductor.offline_admit`).

## Phase B results (all studies ran 13 Nov evening; outputs in `data/research/13nov/work/SYN/phaseB_out/`)

No study meets the full 7-test standard. Discovery = 19 Oct to 4 Nov, test = from 5 Nov.

| Study | Verdict | Key numbers |
|---|---|---|
| R19 rolling re-fit, all 473 weather items as entry filters | none survives | 4,689 line x side trials; best wx_mv10 p 0.031 vs Benjamini-Hochberg line 0.0002; on most items the rolling chooser never beats "take all" |
| R19 exit `hb300_ret < -6` | REJECT | strike 54 to 52 % (discovery), 51 to 49 % (test) |
| R02 exit variants (62, per second) | expiry TP 0.55 / 0.6 / 0.7 and PGB pass R02's screen only | no strike gain; TP gains all on 9 Nov. SL off, clock x2, theta exit, tighter trail, hold to flat all lose in test |
| R05 overlays | REJECT | profit lock K 0.1/0.7 lifts strike (70 / 60 %) but cuts 27 Oct +532 to +80 and adds a losing day; expiry floor rejected |
| R04 filter search with permutation null | REJECT | best (agree_same >= 7) p 0.032 in discovery, worse in test |
| R12 obey EXIT-SOON | REJECT | strike up, test return +216 % to -1.9 %, worst day -6 to -14 % |
| R12 exit on same-side re-trigger | REJECT | strike up, return down by five sixths in discovery |
| R16 VWAP trail, R17 IV-drop exit (64), R15 meta selector, R06 strike policy | REJECT | each lowers strike or worst day in test |
| R20 BOCPD "with the drift" (pool trades) | strongest lead | strike 59.6 to 71.0 % (discovery), 53.7 to 66.7 % (test), holds at 3 hazards; not yet run through the Conductor, worst day or a null |
| R09 sister filter rsb15 < 0 | lead | strike 62 % / 55.6 %, worst day -26.5 / -6.0, but halves the return |
| R17 guard against100_er0.1 (all 107 books) | lead | strike and losing book-days better in both windows; test return lower |
| R08 heavyweight pressure | INFO | right at 30 s on 22 of 23 parts; no consistent gate at the trigger |
| R18 time of day, opening range, gap (pooled, 16 days) | INFO | the 15-minute opening-range break followed through at 30 min on 5 of 16 days; 11 of 15 gaps filled, the 4 unfilled were all over 125 pts |
| R11 armed card (fixed) | INFO | 8 to 16 arms a day, about half fire (fire rate 0.22 to 0.75), the 15-minute move after a fire went the right way about half the time |
| R10 forecaster | INFO | skill decays from IC 0.20 at once to 0.02 after 30 s of delay; the 2-minute odds are well calibrated up to 0.65 |

Fixed and rerun on 13 Nov night: R08 last part (11 Nov), R19 rolling (booleans broke the percentile grid), R19 exit harness,
R11 (read 0 Conductor trades), R18 (each part overwrote the last; now one pooled run). Known weak runs: R16 used a
session TWAP (no exchange VWAP in ds_v2), R06's 19 Oct reprice reads IV 150 to 500 %, R07 built features only.

## Owner point 6: no errors live

| Fix | File | Why |
|---|---|---|
| Forecast Lab at normal priority (`APEX_LAB_PRIORITY=below` keeps the old) | `forecast_lab/live.py` | below normal lost 29 % of its seconds behind research jobs |
| One set of Lab calibration bounds | `forecast_lab/core.py` `KAPPA_OK`, `Z80_OK` | z80 and kappa reset every morning |
| Lab payload handed to the gateway in memory; file every 15 s | `forecast_lab/live.py` `DashWriter(post=True)`, `gateway.py` `POST /api/lab/{name}` | 965 refused swaps on 13 Nov came from the gateway holding the file |
| Gateway errors to `data/logs/gateway.log` | `gateway.py` | the 09:09 traceback left no record |
| Reconnect heeds stop; "websocket LIVE after N min down" | `feed_breeze.py` `_nap`, `connect` | a reconnect round slept 2.5 min blind |
| Supervisor says "FEED reconnecting" during an outage | `run_apex.py` | it said "heartbeat not advancing" for 33 minutes |
| A refused registry save no longer ends the feed | `feed_breeze.py` `_save_registry` | a Windows lock raised out of run() |
| Refused login: exit code 3, the supervisor waits for the credentials file to change (stat only) | `feed_breeze.py`, `run_apex.py` | 4 restarts in 50 s on 13 Nov morning |
| REST call ledger written atomically | `feed_breeze.py` `RestLedger.take` | a crash could tear it |

Not done here, needing the owner's OK: R14's identity-checked engine speed batch (needs the A/A2/B replays),
the council hold photograph (b7, reads `peak_t`, needs the replay gate), prior-day level staleness (b9, changes c20_9v),
the photograph data fixes (b8). Owner actions: Windows power mode "Best performance" while trading, laptop cooling, a
Defender exclusion for `D:\ApexOptions\data`.

## Before the next session

Measure the engine's step time with the three new twins and two shadow Conductors before 09:15 (standing rule: the
live step-time check). Restart all processes so the gateway, Lab and engine pick up the changes.
