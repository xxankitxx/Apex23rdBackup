# 53. The nightly runner: what runs after the close, in what order, and how it judges the forecaster

Written 12 Nov 2026 (PKG-10). Rule: PR-003 in `research/preregistry.jsonl`. Code: `research/nightly_all.py`,
`research/forecast_lab/nightly.py`, `research/forecast_lab/nightly_today.py`, `research/forecast_lab/backfill_ledger.py`.
Tests: `tests/test_forecast_nightly.py`.

## 1. In short

- One runner, `research/nightly_all.py`. The Windows task still calls `research/forecast_lab/nightly_today.py`, which
  now only starts `nightly_all.py` and writes the log `data/forecast_lab/nightly_<today>.log`.
- It runs once at a time (an OS lock on `data/nightly.lock`). It refuses 09:00 to 15:40 on a trading day unless you
  add `--force`. It waits while a replay is running or the live Forecast Lab is on, checking every 5 minutes, for up
  to 4 hours. Then it gives up and says "skipped: replay running".
- It catches up every taped day after the last day in the ledger, oldest first, at most 10 a run. Today counts
  only from 15:45. If 09:00 on a trading day comes during a catch-up, it stops before the next day and leaves the
  rest for the next run. A second run on the same day does nothing.
- `nightly.py` run by hand takes its own lock (`data/forecast_lab/nightly_day.lock`), so it can never work on the
  ledger at the same time as the scheduled run.
- Its result is in `data/nightly_status.json`. The Forecast Lab header shows it.
- "Improved nightly" now has one meaning: the trained layer must beat the plain clock on days it had not seen. When
  it loses on 4 of the last 5 such days, the Lab switches it off by itself. Switching it back on is your decision.

## 2. Run order and expected durations

Durations are estimates for an idle machine. The first full run must be timed (section 7). On a loaded machine
runs were 12 to 17 times slower on 10 Nov, so never time it alongside a replay.

| Step | Script | Runs when | Expected |
|---|---|---|---|
| 1 lab | `research/forecast_lab/nightly.py <day>` | always | 3 to 6 min offline; add 5 to 15 min with online walks |
| 2 hazard | `research/predict/nightly_hazard.py <day>` | when the script exists (PKG-15) | not yet measured |
| 3 label_parity | `research/predict/label_parity.py <day>` | when the day's forecasts and outcomes files exist | 1 to 5 min |
| 3 lab_parity | `research/forecast_lab/decision_card.py --parity <day>` | when the script exists (PKG-09) | not yet measured |
| 4 standard | `research/conductor/standard_nightly.py <day>` | when the script exists (PKG-12) | not yet measured |
| 5 reprice | `research/forecast_lab/reprice_study.py <day>` | when the script exists (PKG-08) | not yet measured |
| 5 straddle_clock | `research/forecast_lab/straddle_clock.py <day>` | when the script exists (PKG-08) | not yet measured |
| 6 replay_parity | `research/conductor/parity.py <day>` | only with your standing OK (section 6) | a one-day replay: up to an hour or more |

Each step has a time limit (3 hours for the lab step and replay parity, 1 hour or 30 minutes for the rest). A step
whose script is missing is marked "skip" with the reason. A failed lab step stops the catch-up, because the days
must be learned in order; the next run starts again from that day. The runner logs a planned end time, worked out
from the last run's step times.

Inside the lab step, for one day D:

1. Convert D's tape to the research format and collect D's forecast inputs (as before).
2. Score each contestant on D. Every one was fitted only on sessions before D.
3. Write one ledger row per contestant to `data/forecast_lab/ledger.jsonl`.
4. Held-out check of the model fitted through D-1 (see section 4).
5. Fit the model through D and install it, if the procedure says so.
6. Apply PR-003 and write one decision row. Write `data/forecast_lab/record_summary.json`.

## 3. The contestants and the scores

| Name | What it is |
|---|---|
| P-incumbent | the brain file that was live during D |
| P-candidate | the brain fitted on every session up to D-1 (the refit-every-night procedure) |
| P-plain-cal | the 10-minute clock x exp(intercept + a 25-bucket time-of-day table, shrunk to the mean), fitted on earlier sessions |
| P-clock | the plain 10-minute clock, for reference |
| P-plain | the live Lab with no trained layer (online walks only) |
| P-harp | the PKG-11 model, forward only, once it exists |

Scores are kept as sums per horizon, so any set of days can be pooled later:

- Primary: the 80 % range score of the futures move at 5 minutes (the interval or Winkler score: the width, plus a
  penalty of 10 times any miss). Lower is better. It is the same as 10 x the 10 % and 90 % pinball the Lab keeps.
- Coverage, width, pinball over the five quantiles, n.
- QLIKE raw, and QLIKE with the mean correction c_h. c_h is the average of realised variance over forecast on the
  contestant's own training sessions. The trained model predicts a geometric mean, so on its own training days the
  realised variance averages 10 to 39 % above its raw forecast. The correction is measured on training days only.
- 30-minute block sums at 5 minutes, and the days-to-expiry stratum (0 to 1 days, or 2 or more).
- With online walks: the option side (band coverage, pinball, middle error against "no change", and the
  profit-chance Brier against its base rate).

Offline scores come straight from the collected arrays and take seconds. Online walks run the whole Lab over D with
the online layers on, one session each, about 2 to 5 minutes each on an idle machine. They are on only with your
standing OK, because they lengthen the run.

Check on 11 Nov with the models fitted through 9 Nov: QLIKE 0.1495 against 0.1442 for the clock, better on 3 of 7
horizons, 76.7 % caught. These are the docs/50 section 11 figures, reproduced exactly by the new scorer.

## 4. The rule, PR-003, as the runner applies it

- Fast-off (automatic). The live brain is compared with the plain clock each day: online walk against online walk
  when both ran, otherwise offline against P-plain-cal. If it lost on 4 or more of the last 5 days with a score,
  the runner writes `data/forecast_lab/use_brain.json` as `{"use": false, ...}`. The Lab reads it within a
  minute and runs without the trained layer. The back-filled walk days count here, as PR-003 says.
- Slow-on and switch (proposed only). The day-block bootstrap (2,000 draws) 90 % interval of the mean daily
  log-ratio must exclude 0 over at least 10 common forward days, and at least 4 of 7 horizons must be better. Walk
  days never count. When this holds, the decision row and `record_summary.json` say so. Nothing switches until you
  do it (section 5).
- Held-out check, in place of the old in-sample check. The model fitted through D-1 needs finite weights, and its
  80 % range must catch 65 to 95 % on D. If it fails, tonight's refit is not installed. If the failed model is the
  live one, brain_prev is put back. brain_prev itself is kept.
- The procedure that runs the brain file: "refit" (the default, as before: install the model fitted through D) or
  "hold" (keep the live file). The one-day "2 % worse than the older models" check is gone. On 11 Nov it compared
  two neighbouring refits that differed by 10 % on one day, which is noise.

One deviation from PR-003 to note. PR-003 names P-plain-cal as the fallback. The live Lab cannot run the
time-of-day clock yet, so when the brain is switched off the Lab runs the plain online clock (P-plain). P-plain-cal
is scored every night offline, and that is what the offline comparison uses.

What the walk record says, if PR-003 had run from 27 Oct (`backfill_ledger.py`, using only earlier days):

- The trained layer lost on the first four walk days (27 to 30 Oct, 5 to 8 sessions of training).
- Fast-off would have switched it off after 30 Oct. It would have stayed off, because walk days cannot switch it
  back on.
- After that the trained layer won on 6 of the next 7 days. So the chosen procedure was worse than always-trained
  on 6 days, and never better than always-plain.
- The rule trails the plain clock on 4 of 5 consecutive sessions once, 27 Oct to 2 Nov. That is the time the rule
  needs to act.
- Over all 11 days: trained better than plain on 6 of 11. The 90 % day-block interval of the log-ratio is -0.060 to
  -0.002 (below 0 favours trained).
- On 2+ days to expiry, one day (6 Nov) carries 98 % of the gain.

This is a record, not an edge. Going into 12 Nov the trained layer was behind on 1 of the last 5 walk days (11 Nov),
so it stays on.

The back-filled walk days also get a `days/<day>.json` in the Lab's daily-record format. They are marked
`"forward": false`, so the record by day shows them but they never count toward what the Lab may claim.

## 5. Your switches

```
py -3.13 research/forecast_lab/nightly.py --set-procedure plain    --why "reason"   (trained layer off)
py -3.13 research/forecast_lab/nightly.py --set-procedure brain-on --why "reason"   (trained layer on)
py -3.13 research/forecast_lab/nightly.py --set-procedure hold     --why "reason"   (stop installing refits)
py -3.13 research/forecast_lab/nightly.py --set-procedure refit    --why "reason"   (install the nightly refit again)
```

Each one is written to the ledger with your reason.

Other commands:

```
py -3.13 research/nightly_all.py                          what the task runs (add --force inside market hours)
py -3.13 research/forecast_lab/nightly.py <day> --check-only   score one day and print; nothing written
py -3.13 research/forecast_lab/nightly.py <day> --force        redo a day already done
py -3.13 research/forecast_lab/backfill_ledger.py --check      the docs/50 table check and the walk retrospective only
```

## 6. Your standing OKs

Create `data/nightly_owner_ok.json`, for example:

```
{"online_walks": true, "replay_parity": true}
```

- `online_walks`: run the brains and the plain Lab through a one-session walk with the online layers on. This is
  needed for the online comparison PR-003 prefers. It adds 5 to 15 minutes.
- `replay_parity`: run step 6, the one-day Conductor replay parity. This is a long job, so give this OK only once
  it has been timed on an idle machine.

Without the file, both are off and the steps say "needs the owner's standing OK".

## 7. Scheduled task settings (not applied: for you to apply)

The task "ApexForecastNightly" today will not start on battery, stops if the laptop is unplugged, never runs a
missed start, and opens a console window that can be closed mid-write. Apply these in an elevated PowerShell. The
command stays `nightly_today.py`, now run hidden through pythonw:

```
$t = Get-ScheduledTask -TaskName "ApexForecastNightly"
$t.Settings.StartWhenAvailable = $true
$t.Settings.DisallowStartIfOnBatteries = $false
$t.Settings.StopIfGoingOnBatteries = $false
$t.Settings.ExecutionTimeLimit = "PT6H"
$t.Settings.MultipleInstances = "IgnoreNew"
$t.Actions[0].Execute = "C:\WINDOWS\pyw.exe"
$t.Actions[0].Arguments = "-3.13 D:\ApexOptions\research\forecast_lab\nightly_today.py"
$t.Actions[0].WorkingDirectory = "D:\ApexOptions"
Set-ScheduledTask -InputObject $t
Get-ScheduledTask -TaskName "ApexForecastNightly" | Select-Object -ExpandProperty Settings |
    Format-List StartWhenAvailable, DisallowStartIfOnBatteries, StopIfGoingOnBatteries, ExecutionTimeLimit
```

If `pyw.exe` is not in C:\WINDOWS, use `(Get-Command pyw).Source`. The trigger stays 16:30 Monday to Friday. With
StartWhenAvailable, a start missed while the machine slept runs at the next wake. The runner then catches up every
day it missed, so a missed night is never lost.

## 8. Files

| File | Written by | What |
|---|---|---|
| `data/nightly_status.json` | nightly_all | day, steps {status, secs, why}, processed and missed days, planned and actual end |
| `data/nightly.lock` | nightly_all | the run lock (pid and start time) |
| `data/forecast_lab/nightly_day.lock` | nightly | the lock for one day's lab step, also taken by a hand run |
| `data/forecast_lab/ledger.jsonl` | nightly, backfill | score rows per (day, procedure, basis), decision rows, owner rows, parity rows |
| `data/forecast_lab/record_summary.json` | nightly, backfill | trained against plain by day, both strata, best-day share, last decision |
| `data/forecast_lab/use_brain.json` | fast-off, owner | `{"use": false, "why": ...}` makes the Lab run without the trained layer |
| `data/forecast_lab/procedure.json` | owner | refit or hold |
| `data/forecast_lab/brains/archive/brain_<through>_<hash>.joblib` | nightly | every brain, written once, never overwritten |
| `data/forecast_lab/brain.joblib`, `brain_prev.joblib`, `brain.meta.json` | nightly | live, previous, meta (sklearn version, feature hash, c_h, git commit) |
| `data/forecast_lab/nightly_walk/<procedure>_<day>.json` | nightly | each procedure's chained online state after day D |
| `data/forecast_lab/days/<day>.json` | backfill (walk days), live Lab | one summary per day; a live record is never replaced |

Every file a reader may open is written to a temp file and renamed into place.

## 9. Still open (needs another package or your OK)

- `research/forecast_lab/train.py final` still writes brain.joblib directly, with no temp file and no check. Use
  the nightly instead. The fix belongs to the owner of train.py.
- The live Lab could save its loaded morning state as `data/forecast_lab/state_morning_<day>.json`. The parity
  re-run would then start from exactly what the Lab started from. Until then it uses the procedure's chained state
  and says so.
- Brain.vol does not apply c_h yet (PKG-11). The nightly records c_h in the meta and in every row.
- The back-fill writes to the live data tree, so it has not been run there. Run it once with
  `py -3.13 research/forecast_lab/backfill_ledger.py` (about 2 minutes; it loads the 11 dated brains for their hashes).
