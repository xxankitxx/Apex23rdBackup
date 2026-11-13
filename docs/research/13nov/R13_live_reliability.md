# R13: Live reliability and speed (owner point 6), 13 Nov

Lens: every log from 9 to 13 Nov (engine.log, feed.log, supervisor.log, perf_11/12/13, the Forecast Lab logs of
12 and 13 Nov, today's events and Conductor files), the live console error, and the code behind each line.
No decision logic is judged here. Nothing was changed in apex\, run_apex.py or tests\. Diffs below are proposals.

## Findings first

1. **Today's slowness is the machine, not one piece of code.** In the calm minutes (10:00 to 10:20) the engine
   step took 13.5 ms on average. From 10:50 to 11:29 it took 208 ms. Every part of the step slowed by the same
   10 to 38 times (books x14, greeks x23, publish x28, weather base x38). One slow part would not do that. The
   engine fell from 598 steps a minute to 243 (4 a second instead of 10). Slowest single step: 3.6 s at 10:57.
2. **The CPU is busy 100% and running at about a quarter of its rated speed.** Windows' own counters at 13:3x and
   13:43: total CPU 98 to 100%, "% of maximum frequency" 25 to 29%, "% Processor Performance" 15% on the P-cores
   and 26% on the E-cores, on AC power, Balanced plan. This laptop chip (i5-1240P) is being held back, most likely by
   heat. At the same time three trading systems (ApexOptions, and two others), the Forecast Lab and many research
   scripts share it. Priority cannot fix heat: a hot chip slows every process, the above-normal engine included.
   The counter can read low on this hybrid chip, so please confirm with Task Manager's "Speed" figure.
3. **The Forecast Lab lost 29% of the market-hours seconds today** (4,300 skipped by 13:21). Its loop went from
   7 to 27 ms in calm minutes to a p50 of 330 ms and a p95 of 12.3 s. It runs at below-normal priority
   (apex/forecast_lab/live.py:81-98), the same class as the research scripts, so it starves first. Its own work is
   tiny (2 to 3% of one core when calm).
4. **The Lab's refused dashboard writes are caused by the reader, not mainly by Defender.** Test on this machine:
   a writer swapping a 35 KB file every 10 ms had 0 of 150 swaps refused with no reader, and 127 to 138 of 150
   refused while another thread kept opening the file to read it. Opening the file with "share delete" did not help.
   The gateway (and the browser's once-a-second poll through it) holds the file open while it serves it. So every
   read that overlaps a swap refuses it. Under load the reads take longer, so refusals cluster in the slow
   minutes: 193, 174 and 130 in 09:19 to 09:49, then 182 at 12:40 to 12:50. Total 965 by 13:01 (code as running).
5. **Today's console error is the same collision seen from the other side.** The static file server sent the file
   size, then the file. A swap in between made the body shorter: "Response content shorter than Content-Length".
   The patch in apex/gateway.py:275-290 (read the whole file, then send) removes it. My drill of the patched pair
   (the new DashWriter and a gateway-style reader) had 0 refused swaps with the 2 s budget, but 6 to 7% of reads
   still failed while a swap was in flight. The patched gateway answers those with 404, and the panel says "cannot
   be read" for a second.
6. **The 53-minute internet outage (11:30:14 to 12:23:16) was handled safely.** The engine blacked out entries at
   11:30:17 and lifted at 12:23:37. The account was flat (the 10:53 trade had closed at 11:03). But three things
   went wrong around it: the supervisor printed 53 "FEED STALE" warnings that mean "reconnecting", a Ctrl+C in that
   hour would not have stopped the feed cleanly, and the Lab showed a stale forecast as live for some minutes
   (stale 3,519 s).
7. **The Lab throws away its own calibration at every start.** It learns z80 inside 0.6 to 3.5 and kappa inside 0.2
   to 6.0 (apex/forecast_lab/core.py:876, 878), but rejects a saved z80 outside 0.9 to 2.0 and kappa outside 0.5
   to 2.0 on load (core.py:40-42, 383-404). Today it reset z80 = 0.75 to 1.28 and said so in every status line.
8. **Speed beyond today's is worth little in rupees; uptime is worth a lot.** Measured on 3 later days (4, 5, 6 Nov)
   with the per-second quotes: entering or exiting a c20 pool trade 1 to 3 s late costs 0.1 to 0.4% of the premium
   (70 trades). The account's trades average several percent each. A 53-minute outage, a feed restart loop or a
   frozen engine costs whole trades.
9. **Nothing in the logs stopped a trade between 9 and 13 Nov.** No engine fault line, no books-save failure on 12
   or 13 Nov (2 retried refusals on 11 Nov), no feed crash in session. Both of today's Conductor trades were taken
   in the slowest minutes (10:53 entry at 263 steps a minute with a 2.06 s step; 12:36 entry at 325 a minute).

## Teardown

### Error and warning classes, 9 to 13 Nov

Counts are lines in the logs. "9 Nov" lines carry no date in the logs; I placed them by session order.

| # | Where | Message (short) | 9 | 11 | 12 | 13 | Root cause in code | Effect | Fix |
|---|---|---|---|---|---|---|---|---|---|
| 1 | engine.log | per-minute tick time: minutes with p95 over 300 ms | many (worst p95 7.1 s) | 0 | 6 | 39 | none: whole-machine slowdown (finding 1, 2) | 4 steps/s instead of 10; late trails | machine (Ideas 1, 2) |
| 2 | engine.log | SLOW TICK over 1 s | n/a (not logged yet) | 1 | 6 | 15 | same; plus 'day' close 12.7 s at 15:41 on 11 Nov | entry tick 10:53:36 took 2.06 s | as 1 |
| 3 | engine.log | books swap refused, PermissionError WinError 5 | 0 | 2 | 0 | 0 | Windows lock on 2026-11-11.json; saver retried (paper.py:1813-1900) | none, saved later | done (13 Nov) |
| 4 | feed.log | poller: get_quotes "Expecting value" (empty broker reply) | 3 | 11 | 9 | 4 | broker returns an empty body; SDK json-decodes it; feed_breeze.py:556-578 | VIX one minute older | Idea 10 |
| 5 | feed.log | REST "Connection aborted / reset 10054" | 3 | 0 | 0 | 0 | broker or network | same as 4 | none |
| 6 | feed.log | REST "Max retries / connect timeout" | 0 | 1 | 0 | 53 | outage | none (entries blacked out) | none |
| 7 | feed.log | chain call failed | 1 | 0 | 0 | 35 | outage | strike levels 90 s older | none |
| 8 | feed.log | "no packets for 30 s, reconnecting" | 0 | 1 | 0 | 26 | outage; feed_breeze.py:627-631 | blackout (correct) | Idea 6 |
| 9 | feed.log | "ws connect failed (n)" | 0 | 5 | 0 | 181 | outage; 7 tries 2-30 s apart, feed_breeze.py:529-546 | main loop blocked 2.5 min per round | Idea 6 |
| 10 | feed.log | Session key expired (traceback) | 0 | 0 | 4 | 0 | owner had not saved the day's token; login raises, supervisor restarts (run_apex.py:342-349) | 4 restarts in 50 s | Idea 8 |
| 11 | feed.log | NIFTY futures unresolved / security master URLError | 0 | 3 | 0 | 0 | SDK downloads the security master at import (60 s socket timeout, feed_breeze.py:342-347) | 3 restarts, 4 min late start | Idea 8 |
| 12 | supervisor | FEED STALE n s | about 3 | 2 | 0 | 53 | hb written only in the main loop (feed_breeze.py:624); the loop sits in reconnect() | misleading alarm | Idea 6 |
| 13 | supervisor | FEED exited (code 1), restarting | 0 | 3 | 4 | 0 | rows 10 and 11 | late start | Idea 8 |
| 14 | supervisor | ENGINE heartbeat paused 3.0 s | 0 | 0 | 1 | 0 | slow tick | none | as 1 |
| 15 | supervisor | second Ctrl+C, terminating | 1 | 0 | 0 | 0 | 9 Nov stop killed the engine mid-save | torn tmp file | fixed 10 Nov (3 presses) |
| 16 | events | GAP "feed silent 3 s", entries paused about 20 s | 5 | 4 | 2 | 2 | guard.py:27-31, 50-100: no packet on any row for 3 s | entries paused 20-38 s each | Phase B test |
| 17 | events | GAP at 09:15:00 "futures quote 327-380 s old" | 1 | 1 | 1 | 1 | futures quiet before the open; guard waits 20 s of live futures | entries from 09:15:20; logged as a gap | Idea 13 (label only) |
| 18 | Lab log | dashboard write fails | n/a | n/a | 1,726 | 965 by 13:01 | reader handle blocks os.replace (finding 4); live.py:101-121 | loop held up to 0.25 s per refusal | Ideas 3, 4 |
| 19 | Lab log | skipped seconds | n/a | n/a | 2,468 | 4,300 by 13:21 | below-normal priority under a saturated, throttled CPU; live.py:81-98, 748 | forecasts and learning lose 29% of seconds | Idea 1 |
| 20 | Lab log | "kappa/z80 reset: z80 0.75 to 0.94 is outside 0.9 to 2.0" | n/a | n/a | yes | every status line | load bounds narrower than the online clip, core.py:40-42 vs 876-878 | calibration starts cold every day | Idea 5 |
| 21 | console | RuntimeError: Response content shorter than Content-Length | n/a | n/a | n/a | 09:09 | Starlette FileResponse sends stat size then streams; Lab swapped the file in between | one request dropped | patched (gateway.py:275-290), not live |
| 22 | gateway.log | (file never created) | | | | | uvicorn errors go only to the console (gateway.py:304, log_level warning) | today's error left no record | Idea 9 |

### Where the code fails, in detail

**Forecast Lab loop (apex/forecast_lab/live.py, committed version).**
* The loop sleeps to 0.15 s past each wall second (line 669 committed, 748 working tree), then reads the table,
  steps, builds the panel, dumps JSON and writes the file, all in series. Any second whose work runs past about
  0.85 s skips the next second. There is no catch-up: the table holds only current values.
* `below_normal()` (lines 81-98) puts the whole process in BELOW_NORMAL_PRIORITY_CLASS. The research scripts use
  the same class (data/research/13nov/lowprio.py). The engine and feed are ABOVE_NORMAL (run_apex.py:97-106). So
  the Lab competes as an equal with every research job.
* `Writer.write` (lines 101-121) retries a refused swap for 0.25 s on the loop. 965 refusals is up to 4 minutes of
  loop time lost, mostly in the minutes when the loop was already late.
* The working-tree DashWriter (uncommitted, lines 127-202) moves the write to a thread. Drill result: the loop never
  waits on a lock, 0 refused swaps with the 2 s budget. It does not remove the cause (the reader), and `put()` took
  up to 67 ms on this loaded machine because the writer thread competes for the interpreter lock.

**Lab calibration bounds (apex/forecast_lab/core.py).** `KAPPA_OK = (0.5, 2.0)`, `Z80_OK = (0.9, 2.0)` at lines
40-42. The online updates clip kappa to (0.2, 6.0) at line 876 and z80 to (0.6, 3.5) at line 878. A value the Lab
learned on its own is "out of bounds" at the next start (lines 383-404) and both are reset. On 12 Nov a wide-range
day pushed z80 to 0.75; since then every start resets it.

**Gateway (apex/gateway.py).** The static mount (line 293) served forecast_lab.json with FileResponse: size from a
stat, body streamed after. The patch adds a route before the mount that reads the whole file first (lines
275-290). Remaining gaps: an OSError during a swap returns 404 at once (no short retry); uvicorn runs with
`log_level="warning"` and no file handler (line 304), so its tracebacks never reach data/logs.

**Feed reconnect (apex/feed_breeze.py).**
* `run()` (lines 613-637) writes the heartbeat at line 624 and calls `reconnect()` on the same thread (line 631).
  `connect()` (lines 529-546) tries 7 times with sleeps of 2, 4, 8, 16, 30, 30, 30 s plus up to 15 s connect wait
  each: about 2.5 to 4 minutes with no heartbeat. Hence the supervisor's 10/70/130 s pattern today.
* `connect()` never looks at the stop flag. A Ctrl+C during an outage: the feed misses its 12 s (run_apex.py:191),
  the engine stops, and only then is the feed terminated (run_apex.py:236-243). A terminated feed does not close
  its tape, so that tape part has no gzip trailer.
* `last_msg` is set before `reconnect()` (line 630). After a failed round the loop starts the next round at once.
  That is good for recovery, but nothing records how long the network has been down.
* `maybe_recenter()` calls `self.reg.save(self.t)` (line 670), which uses `replace_retry(..., must=True)` with a 3 s
  budget (feed_core.py:89-96). If a reader holds instruments.json for 3 s, the exception leaves `run()`, the feed
  exits with code 1, and the supervisor restarts it with a fresh login (30 to 90 s without data) in the middle of a
  trending move. It has not happened yet; it is the one path I found that can drop the feed in session.
* `write_chain()` (lines 686-698) counts refused swaps in `WRITE_CHAIN_FAILS` but nothing ever logs it.
* `RestLedger.take()` (line 255) writes rest_ledger.json with a bare `open(path, "w")` on every call: not atomic,
  and a torn file is read as 0 calls at the next start (line 238), which could overspend the 3,000-call cap.

**Login (feed_breeze.py:334-368, run_apex.py:340-349).** A refused session token now logs a clear sentence, but the
exception still ends the process and the supervisor restarts it up to 20 times, 5 to 60 s apart. Each restart
fails the same way until the owner saves a new token.

**Engine (apex/engine_main.py).** No faults logged since 9 Nov. Two costs remain on the step: building the books
text on a trade tick, "save books (trade)", 121 to 385 ms on today's slow ticks (lines 1689-1692,
paper.py:1765-1790), and the end-of-day close, 12.7 s on 11 Nov and 5.5 s on 12 Nov at 15:41 (after the market,
harmless). Exit-state saves are now 1,225 by 13:31 (12 Nov: 4,741 for the day): the 13 Nov change works.

**Data guard (apex/engine/guard.py).** Correct and safe in the outage. It also fires 2 to 5 times a day on a 3 s
silence of all packets (STALE_S, line 28) and pauses entries for 20 s or more each time. On 9 Nov three of them
match broker connection resets in the poller log; on 12 Nov one matches a slow-tick minute. The logs cannot tell
which are broker silences and which are a starved feed process: Phase B script 1 answers that from the tapes.

## Evidence

### Engine step, per day (09:15 to 15:30 minute lines)

| Day | Minutes | Median p50 ms | Median p95 ms | Worst minute p95 ms | Max step ms | Steps over 300 ms | Steps over 1 s | Fewest steps in a minute |
|---|---|---|---|---|---|---|---|---|
| 9 Nov | 324 | 61 | 218 | 7,067 | 8,502 | 6,278 | n/a | 66 |
| 11 Nov | 376 | 31 | 106 | 277 | 949 | 458 | 0 | 440 |
| 12 Nov | 376 | 42 | 150 | 785 | 1,197 | 1,728 | 8 | 169 |
| 13 Nov (to 13:31) | 256 | 57 | 170 | 866 | 3,617 | 3,971 | 19 | 167 |

### 13 Nov, Lab and engine side by side (10-minute windows)

| Window | Lab loop p50 ms | Lab loop p95 ms | Lab seconds skipped | Lab write fails | Engine steps/min | Engine mean ms |
|---|---|---|---|---|---|---|
| 09:00-09:09 | 18.5 | 83 | 2 | 0 | 548 | 25 |
| 09:19-09:29 | 176 | 831 | 61 | 193 | 566 | 57 |
| 09:29-09:39 | 239 | 1,572 | 208 | 174 | 431 | 111 |
| 09:49-10:09 | 16-21 | 108-184 | 0 | 0 | 598 | 12 |
| 10:29-10:40 | 246 | 1,791 | 148 | 139 | 415 | 120 |
| 10:50-11:01 | 312 | 6,131 | 544 | 0 | 246 | 233 |
| 11:17-11:30 | 323 | 12,339 | 814 | 0 | 251 | 229 |
| 11:40-12:20 (outage: no quotes) | 6.4-6.8 | 28-29 | 0 | 0 | 598 | 8.7 |
| 12:40-12:50 | 331 | 2,419 | 182 | 182 | 462 | 102 |
| 13:11-13:21 | 138 | 1,444 | 87 | 0 | 492 | 83 |

The Lab and the engine slow down in the same minutes, by the same order. In the heaviest minutes the Lab wrote so
rarely that its write fails fell to 0.

### Engine phases, calm against loaded (13 Nov, mean ms per step)

| Part | 10:00-10:20 | 10:50-11:29 | Times slower |
|---|---|---|---|
| books | 2.91 | 42.08 | 14 |
| market | 2.62 | 27.37 | 10 |
| greeks | 1.92 | 43.48 | 23 |
| pre-books | 1.71 | 38.51 | 23 |
| publish | 0.85 | 23.81 | 28 |
| weather base | 0.39 | 14.81 | 38 |
| save books (trade) | 0.12 | 2.44 | 21 |
| all step parts | 13.5 | 207.8 | 15 |

### Live Conductor trades and engine speed at that minute

| Day | Entry | Steps/min, max step | Exit | Steps/min, max step | Result |
|---|---|---|---|---|---|
| 9 Nov | 11:33:18 | 452, 2.7 s | 11:38:29 | 159, 4.8 s | +64.8% |
| 9 Nov | 10:56:23 | 171, 2.9 s | 10:58:05 | 444, 2.9 s | -14.8% (SL) |
| 11 Nov | 13:20:12 | 556, 0.3 s | 13:58:20 | 576, 0.3 s | +21.3% |
| 12 Nov | 11:12:40 | 523, 0.7 s | 12:22:25 | 515, 0.4 s | +10.7% |
| 13 Nov | 10:53:36 | 263, 2.1 s | 11:03:27 | 212, 1.3 s | -12.4% |
| 13 Nov | 12:36:27 | 325, 1.6 s | 13:19:02 | 528, 0.3 s | -7.1% |

(9 Nov had 12 trades; two shown. All 21 live trades: work\R13\trade_ticks.py.)

### What a late fill costs (per-second quotes, 4 to 6 Nov, ask at entry and bid at exit)

| Delay | All books (3,135 trades): entry + exit cost | c20 pool books (70 trades): entry + exit cost |
|---|---|---|
| 1 s | +0.02% of premium | +0.16% |
| 2 s | +0.08% | +0.11% |
| 3 s | +0.08% | +0.37% |
| 5 s | +0.07% | +0.24% |

The data has one quote per second, so delays under 1 s read as 0. This is a cost estimate, not a profit claim.
One variant family, no selection. It says: making the engine faster than 10 steps a second will not show in the
rupees. Keeping it from stalling, and keeping the feed up, will.

### Dashboard file tests (this machine, today, scratch folder only)

| Test | Result |
|---|---|
| swap every 10 ms, no reader | 0 of 150 refused |
| swap every 10 ms, reader opens and reads the file in a loop | 128 of 150 refused |
| same, reader holds it 2 ms | 138 of 150 refused |
| same, reader opens with share-delete (Win32 CreateFile) | 127 and 136 of 150 refused |
| two fixed slots rewritten in place (no rename), reader keeps the newest complete one | 0 write errors; 432 torn reads detected and skipped |
| working-tree DashWriter (2 s budget) with a gateway-style reader, 60 payloads | 0 refused, 33-36 written, rest superseded; 6-7% of reads failed |
| job-object hard CPU cap of 2% on my own test script | spin loop fell from 42% to 18% of one core: the cap works |

### Machine at 13:3x and 13:43

| Counter | Value |
|---|---|
| total CPU | 98-100% |
| % of maximum frequency | 25-29% |
| % processor performance, P-cores / E-cores | 15% / 26% |
| power | AC, 100% charged, Balanced plan |
| free memory | 4.5 of 15.7 GB, paging 1-2 pages/s (not a memory problem) |
| python processes | ApexOptions (feed, engine, gateway, Lab), two other trading systems with 6 processes, 5+ research jobs |

## Ideas

Each idea is a reliability or speed change. None of them changes a trading decision. None needs the 7-test
standard. I tried 1 variant per idea; no profit is claimed.

### 1. Run the Forecast Lab at normal priority (high confidence, untested live)
* Mechanism: the engine and feed stay above normal, so a normal Lab cannot delay them. It would win against the
  below-normal research jobs that starve it now. Its own load is 2 to 3% of one core.
* Evidence: finding 3 and the side-by-side table. Not run live.
* Build: one change in live.py. Show "priority normal" in the runner block.

```diff
--- a/apex/forecast_lab/live.py
+++ b/apex/forecast_lab/live.py
@@ def below_normal():
-            k32.SetPriorityClass(k32.GetCurrentProcess(), 0x00004000)   # BELOW_NORMAL_PRIORITY_CLASS
+            # 13 Nov (R13): below normal starved the Lab behind research jobs of the same class (29% of seconds lost).
+            # The engine and feed run ABOVE_NORMAL, so NORMAL cannot delay them. APEX_LAB_PRIORITY=below for drills.
+            cls = 0x00004000 if os.environ.get("APEX_LAB_PRIORITY", "normal") == "below" else 0x00000020
+            k32.SetPriorityClass(k32.GetCurrentProcess(), cls)
```
* Risk: on a machine where the engine is not above normal (a manual start without run_apex.py), the Lab would
  compete with it equally. Check the engine's class at Lab start and fall back to below normal if it is not above.

### 2. Cap research jobs with a hard CPU limit, not only a low priority (high confidence, tested on my script)
* Mechanism: priority decides who runs first. It does not stop the chip from heating up and slowing everyone. A
  Windows job object with a hard CPU-rate cap limits the total work of research scripts, so the chip runs cooler
  and faster for the engine. My test: a 2% cap took a spin loop from 42% to 18% of one core.
* Build: add to data/research/13nov/lowprio.py (research code, not apex). Suggested cap: 25% of the machine in
  market hours for all research together (one job object per script, so about 4% each with 6 scripts).

```python
import ctypes
from ctypes import wintypes
class _RATE(ctypes.Structure):
    _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]
def cap_cpu(percent_of_machine):
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.restype = wintypes.HANDLE
    k.GetCurrentProcess.restype = wintypes.HANDLE
    k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    job = k.CreateJobObjectW(None, None)
    info = _RATE(0x1 | 0x4, int(percent_of_machine * 100))      # ENABLE | HARD_CAP, units of 0.01% of the machine
    k.SetInformationJobObject(job, 15, ctypes.byref(info), ctypes.sizeof(info))   # JobObjectCpuRateControlInformation
    k.AssignProcessToJobObject(job, k.GetCurrentProcess())
    return job                                                   # keep a reference for the life of the process
```
* Owner actions (not code, I did not touch them): check the laptop's cooling (vents, a stand), set the Windows
  power mode to "Best performance" while trading, and keep heavy research for after 15:30. Excluding
  D:\ApexOptions\data from Defender (docs/55) is still the owner's call.
* Risk: research runs slower in the day. That is the point.

### 3. Hand the dashboard file to the gateway in memory (high confidence, tested in part)
* Mechanism: the refusals come from the gateway holding the file open while the Lab swaps it. If the Lab posts
  each payload to the gateway (127.0.0.1 only, the same server it already reads /api/state from), nothing is
  swapped on disk while a reader holds it. The file is still written every 15 s and at stop, for a restart.
* Evidence: 0 refusals with no reader, 85 to 92% with a busy reader (tests above). The POST path itself is untested.
* Build:

```diff
--- a/apex/gateway.py
+++ b/apex/gateway.py
+from fastapi import Request
+LAB_MEM = {}                                   # name -> (bytes, wall time); the Lab posts here once a second
+
+@app.post("/api/lab/{name}")
+async def lab_put(name: str, request: Request):
+    if not _LIVE_RE.match(name):
+        return Response(status_code=404)
+    body = await request.body()
+    if not body or len(body) > 4_000_000:
+        return Response(status_code=413)
+    LAB_MEM[name] = (body, time.time())
+    return Response(status_code=204)
+
 @app.get("/static/live/{name}")
 def live_file(name: str):
     if not _LIVE_RE.match(name):
         return Response(status_code=404)
+    hit = LAB_MEM.get(name)
+    if hit is not None and time.time() - hit[1] < 30.0:          # fresh copy in memory: no disk, no lock
+        return Response(hit[0], media_type="application/json", headers={"Cache-Control": "no-store"})
-    try:
-        with open(os.path.join(config.STATIC_DIR, "live", name), "rb") as f:
-            data = f.read()
-    except OSError:
-        return Response(status_code=404)
+    data = None
+    for _ in range(4):                                            # a swap in flight: try again 5 ms later
+        try:
+            with open(os.path.join(config.STATIC_DIR, "live", name), "rb") as f:
+                data = f.read()
+            break
+        except OSError:
+            time.sleep(0.005)
+    if data is None:
+        return Response(status_code=503)
     return Response(data, media_type="application/json", headers={"Cache-Control": "no-store"})
```

```diff
--- a/apex/forecast_lab/live.py   (inside DashWriter._run, before the file write)
+                if self._post(path, text):                      # in memory at the gateway: done
+                    with self.cv:
+                        self.writes += 1; self.landed_wall = time.time()
+                        if t is not None: self.landed_t = t
+                    if time.time() - self._disk_t < DISK_EVERY_S:  # the disk copy only every 15 s
+                        continue
+                    self._disk_t = time.time()
 ...
+    def _post(self, path, text):
+        url = f"http://127.0.0.1:{config.PORT}/api/lab/{os.path.basename(path)}"
+        try:
+            req = urllib.request.Request(url, data=text.encode("utf-8"), method="POST",
+                                         headers={"Content-Type": "application/json"})
+            with urllib.request.urlopen(req, timeout=0.5) as r:
+                return r.status == 204
+        except Exception:
+            return False                                         # gateway down or old: the file path still works
```
* Risk: a gateway restart loses the memory copy for one second (it falls back to the file). The host check
  (TrustedHostMiddleware) already limits the endpoint to this machine.

### 4. If a file must stay: two fixed slots, no rename (medium confidence, tested)
* Mechanism: the Lab rewrites slot 0 and slot 1 in turn, each starting with a sequence number and the body length.
  The gateway reads both and serves the newest complete one. No rename, so nothing to refuse.
* Evidence: 0 write errors in 150 writes with a busy reader; torn reads were all detected.
* Build: Lab writes `forecast_lab.s0.json` / `.s1.json` with a first line `seq len`; gateway `live_file` picks the
  slot whose length matches and whose seq is larger.
* Risk: two files instead of one; any other reader of forecast_lab.json must change too (only the gateway reads it).

### 5. One set of bounds for the Lab's calibration (high confidence, code-evident)
* Mechanism: load accepts what the Lab itself learns, so it stops resetting z80 and kappa every morning.

```diff
--- a/apex/forecast_lab/core.py
+++ b/apex/forecast_lab/core.py
-KAPPA_OK = (0.5, 2.0)
-Z80_OK = (0.9, 2.0)
+KAPPA_OK = (0.2, 6.0)                       # 13 Nov (R13): the same range the online update clips to (line 876)
+Z80_OK = (0.6, 3.5)                         # ... and line 878; a value learned live is never "out of bounds" next day
@@ (lines 876, 878)
-                self.kappa[j] = float(np.clip(..., 0.2, 6.0))
+                self.kappa[j] = float(np.clip(..., *KAPPA_OK))
-                self.z80[j] = float(np.clip(..., 0.6, 3.5))
+                self.z80[j] = float(np.clip(..., *Z80_OK))
```
* Risk: a truly broken state (from a stall) inside the wider bounds now loads. The walk-forward files
  (data/forecast_lab/walk_*.json) can check 80% band coverage with the kept values before this goes live.

### 6. A feed reconnect that heeds stop and tells the truth (high confidence, code-evident)
* Mechanism: sleep in small steps, check the stop flag, and let the supervisor say "reconnecting" from feed_state
  (3 = reconnecting, 4 = failed) instead of "heartbeat not advancing". The heartbeat itself must not be written
  during reconnect: the dashboard reads it as "feed fresh".

```diff
--- a/apex/feed_breeze.py
+++ b/apex/feed_breeze.py
+    def _nap(self, s):
+        """Sleep s seconds in 0.25 s steps; False as soon as the supervisor asks the feed to stop."""
+        end = time.monotonic() + s
+        while time.monotonic() < end:
+            if int(self.t.c("stop")):
+                return False
+            time.sleep(0.25)
+        return True
+
     def connect(self):
         self.t.set("feed_state", 1)
         for attempt, wait in enumerate((2, 4, 8, 16, 30, 30, 30), 1):
+            if int(self.t.c("stop")):
+                return False
             try:
 ...
-            time.sleep(wait)
+            if not self._nap(wait):
+                return False
```

```diff
--- a/run_apex.py   (stale warning, around line 360)
-                                say(f"{name} STALE {age:.0f} s ... heartbeat not advancing ...")   # run_apex.py:363 today
+                                fs = int(t.c("feed_state"))
+                                if name == "FEED" and fs in (3, 4):
+                                    say(f"FEED reconnecting: no market data for {age:.0f} s (network or broker). "
+                                        f"Entries are paused; open trades wait for fresh quotes.")
+                                else:
+                                    say(f"{name} STALE {age:.0f} s, heartbeat not advancing (see data/logs/{name.lower()}.log)")
```
* Also log the outage length when the socket comes back ("websocket LIVE after 53 min 2 s down").
* Risk: none on decisions; the engine's guard already treats feed_state 3 and 4 as not live.

### 7. A registry save that cannot kill the feed (high confidence, code-evident)
* Mechanism: in `maybe_recenter()` a refused instruments.json swap keeps the old version number and tries again on
  the next loop, instead of raising out of `run()`.

```diff
--- a/apex/feed_breeze.py   (maybe_recenter, line 670)
-            self.reg.save(self.t)
+            try:
+                self.reg.save(self.t)
+            except OSError as e:                      # 13 Nov (R13): a locked file must not end the feed in session
+                self.reg.version -= 1                 # the table keeps the old version; readers keep the old list
+                self._reg_retry = True
+                log(f"registry save refused ({type(e).__name__}); trying again in 1 s")
+                return
```
  plus, at the top of `maybe_recenter()`: `if getattr(self, "_reg_retry", False): retry the save and the
  subscription first`.
* Risk: for a second or two the engine does not see the new strikes. It already handles a registry that lags.

### 8. Login and security master: no restart loop (medium confidence, code-evident)
* Mechanism: a refused token exits with its own code (say 3). The supervisor then waits, checking every 10 s
  whether the credentials file's modified time has changed (it never opens or prints the file), and restarts only
  then. A failed security master download is retried inside the process (3 tries, 20 s apart) before exiting.
* Build: feed_breeze.py `main()` maps the "LOGIN REFUSED" case to `sys.exit(3)`; run_apex.py:340-349 treats code 3
  as "waiting for a new token" and does not count it as a crash.
* Risk: none in session; it only changes what happens before the first tick.

### 9. Gateway errors to a file (high confidence)
* Mechanism: pass uvicorn a log config with a file handler on data/logs/gateway.log at level warning, so a
  traceback like today's leaves a record with a time.
* Build: `uvicorn.run(app, ..., log_config=LOGCFG)` with a `logging.FileHandler` for the "uvicorn.error" logger.
* Risk: none.

### 10. Small feed fixes (high confidence)
* Write rest_ledger.json with `fsutil.write_text(path, text, budget_s=0.25, must=False)` and a `with` block
  (feed_breeze.py:255), so a crash cannot tear it and reset the call count.
* Log `WRITE_CHAIN_FAILS` and `fsutil.STATS` once a minute in the feed log (feed_breeze.py:686-698).
* On an empty VIX reply (row 4 of the table), try once more after 2 s instead of waiting 60 s.

### 11. A cheaper books text on trade ticks (medium confidence, untested)
* Mechanism: "save books (trade)" builds the text for all 107 books on the step: 121 to 385 ms on today's slow
  ticks, exactly at entry and exit. Cache each book's head JSON with a change counter, rebuild only books that
  changed. Expected cost on a trade tick: a few ms.
* Build: in paper.py `_books_chunks`, keep `{name: (rev, head_text)}`; books bump `rev` when their state changes.
* Risk: a missed `rev` bump writes a stale book. Needs a replay proof that the saved files are byte-identical.

### 12. Do not chase more speed in the engine (high confidence, measured)
* Finding 8: 1 to 3 s of extra delay costs 0.1 to 0.4% of premium per trade. The heaviest books
  (`spot_dc12_t12_first*`) are not worth the risk of touching decision code for speed. Spend the effort on
  uptime: Ideas 1, 2, 6, 7, 8.

### 13. Label the 09:15 wait as the open, not a data gap (display, high confidence)
* Every day the guard logs "data gap: futures quote 327-380 s old" at 09:15:00 and lifts it at 09:15:20. That is
  the futures waking up at the open, and the 20 s wait is right. Logging it as a gap inflates the day's gap count.
  Build: in engine_main where GAP events are written, if the gap starts within 2 s of 09:15:00 and the reason is
  "futures quote ... old", write k="OPEN" with "waiting for 20 s of live futures after the open".

## Phase B scripts (ready, not run)

| Script | What it answers | Rules |
|---|---|---|
| D:\ApexOptions\data\research\13nov\work\R13\phaseB_packet_gaps.py `<day>` | For each "feed silent 3 s" gap, was the tape silent too (broker or network) or not (our process starved)? Also the exchange-stamp lag. One day per run, stops at 170 s. | after 15:30 |
| D:\ApexOptions\data\research\13nov\work\R13\phaseB_machine_monitor.py | A session-long, read-only log of CPU %, clock %, free memory and the engine's minute line, every 10 s. Shows whether slow ticks follow heat. | needs the owner's OK (runs all session) |

Scratch scripts already run (all short, below-normal, my folder only): classify_logs.py, tick_stats.py,
lab_vs_engine.py, trade_ticks.py, latency_cost.py (output latency_cost.parquet), replace_vs_reader.py,
dashwriter_drill.py, jobcap_test.py.

## What I did not do

* I did not apply any diff, restart anything, or change any system or security setting. The CPU readings are
  Windows counters, read only.
* The latency cost uses 3 days and one quote a second. It is a cost estimate, not a walk-forward profit test.
* I could not tell from the logs which 3-second feed silences were the broker's. Phase B script 1 does that.
