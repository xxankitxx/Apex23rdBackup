# Member 05: Live data feed and Breeze integration

## Lens
`apex/feed_breeze.py`, `apex/feed_core.py`, `apex/universe.py`, plus how `run_apex.py` (supervisor, preflight) and `feed_replay.py` handle what the feed writes. I checked every SDK assumption against the `breeze-connect` 1.0.69 sdist and the installed engineio 4.14 / socketio 5.17. Probe scripts are in `/tmp/council/05/probe/`. Monday 19 Oct is the **first live session**. It is also a **0DTE expiry**: Tuesday 20 Oct is a holiday, so the weekly expiry moves to Monday. `weekly_expiries` handles that correctly (19-Oct, 27-Oct). There is no `token_cache.json` yet, so the first build resolves everything from scratch. Tests: 28/28 pass.

## Teardown

**T1. A feed crash followed by a same-day restart corrupts the day's recording, and replay then crashes. HIGH. Verified by probe.**
`feed_core.py:209-236` opens `data/ticks/<day>.jsonl.gz` in append mode inside a *daemon* thread. When the feed dies:
- `main()` re-raises at `feed_breeze.py:575-577`. The `SystemExit` at `:359` is one example.
- The supervisor's `terminate()` fires after 12 s (`run_apex.py:105-113`). The feed can easily overrun 12 s while it sits in `connect()` backoff (`:433-446`, up to 30 s sleep plus a 15 s wait).

In both cases the gzip member is never closed. The supervisor then respawns the feed (`run_apex.py:92-98`), which appends a new member behind the broken one. Probe `w.py`: a crashed run followed by a clean run gives `zlib.error: invalid block type`. Every line from the restarted run is unreadable (771 of 1,771 read). `feed_replay.py:61` catches only `(EOFError, OSError)`, and `zlib.error` subclasses neither, so replay dies with a traceback. Effect: one mid-day feed restart loses the rest of the day's recording, and that recording is the input to the learning loop's replay. Fix (S): open a new file per feed process (`<day>.<pid or n>.jsonl.gz`) and have replay read them in order. Also catch `zlib.error`.

**T2. An empty security master gives "websocket LIVE" with zero instruments. HIGH. Verified by probe.**
The SDK's `get_stock_script_list` swallows every download error and leaves empty dicts (sdist `breeze_connect.py:892-967`). After that, every `get_stock_token_value` returns `'4.1!False'`. In that case `build()` (`feed_breeze.py:337-380`) still succeeds as long as the REST spot works. Probe `p1.py` case A: `0 instruments`, `subscribe_all()` returns `True` (`:419-429`, because `bad == 0`), so `connect()` sets `feed_state=2` and logs "websocket LIVE". The 30 s watchdog then reconnects forever while the dashboard says LIVE. Fix (S): `build()` should `SystemExit` when `NIFTY|FUT` or fewer than about 40 options resolved. The supervisor then retries, which re-downloads the master.

**T3. Hero contracts lose depth as soon as Nifty drifts, and re-centering never adds it back. MEDIUM. Verified by probe.**
Depth is requested only for strikes within ±3 of the *build-time* centre (`feed_breeze.py:387`). The engine's heroes are ATM ±2 of the *current* ATM (`engine_main.py:384-394`). After a 100-point move, the far-side heroes have no depth. Re-centering waits for 4 strikes (`config.RECENTER_STRIKES`), and even then `Registry.add` on an existing key only flips `depth=True`. It never stores the new `depth_token` (`feed_core.py:65-69`), so `subscribe_all` never joins it. Probe case B: after re-centering 25000→25200, strikes 25200 and 25250 show `depth=True, depth_token=None, subscribed=False`. `market.py:48-56` then falls back to best-level quantity with `sbo/sso = NaN`. The order-count classes (PULLED/REFILLING by orders) vanish on exactly the contracts the book exit and coherence read. On a 0DTE Monday, 100 to 200 point moves are normal. Fix (S): in `Registry.add`, set `it["depth_token"]` when an existing item gains depth. Re-centre depth on every 1-strike ATM change, or widen depth to ±5.

**T4. Packets are applied in arbitrary order; only quotes with a rising `ttq` are guarded. MEDIUM. Verified by reading.**
engineio runs every message in its own thread (`engineio/client.py:436`, `run_async=True`). `apply_packet` drops a quote only when `ttq` goes backwards (`feed_core.py:152`), which leaves three gaps:
- Depth packets (`:182-195`) have no ordering guard at all. An older 5-level snapshot can overwrite a newer one, which makes up a "drain" or "refill" in `flow.py`.
- Index quotes (NIFTY, VIX, and the BANKNIFTY and FINNIFTY indices) have `ttq` 0, so they are never guarded either.
- `rec.put` runs outside the lock (`feed_breeze.py:407`), so the recording order is not the order the packets were applied, and replay is not bit-identical to live.

Fix (S): guard depth on `raw[1]` (exchange epoch) and quotes on `ltt` as a tiebreak. Move `rec.put` inside the lock.

**T5. Login can hang with no timeout and no log line. MEDIUM. Verified by reading.**
The `requests` timeout patch (`feed_breeze.py:298-303`) does not cover the SDK's `urlopen(SECURITY_MASTER_URL)`. That call runs once at import (sdist line 32) and again in `generate_session` (line 898), with no timeout, and the same function then runs a third full `requests.get` of the zip. A slow `directlink.icicidirect.com` leaves the feed stuck in state 1 (connecting), with nothing written to `feed.log` between "starting" and "session established". Fix (S): set `socket.setdefaulttimeout(60)` before importing `breeze_connect`, and log before and after `generate_session` with elapsed seconds.

**T6. A feed restart re-numbers the instrument rows, and the engine throws away its warm state. MEDIUM. Verified by reading.**
`BreezeFeed.__init__` zeroes the whole table (`:235`). `build()` assigns ids in build order, and option ids depend on the *new* band centre. Any mid-day restart therefore makes `moved` true in `engine_main.py:104-109`. That resets `Market`, `Flow`, the greeks and the IV/OI history, which means another 10-minute warm-up (`WARMUP_S`) right after an outage. Fix (M): seed the registry from `instruments.json` when it is from today, keeping ids and appending only new keys.

**T7. Likely spurious reconnect at 09:15:00. LOW. Unverified: depends on whether Breeze streams pre-open data.**
`run()` checks silence only inside 09:15 to 15:30 (`:520-525`). If nothing arrived between about 09:08 and 09:14:30, the first loop pass at 09:15:00 sees more than 30 s of silence and tears the socket down just as the open prints. That costs `sleep(1)`, the handshake and three join batches, roughly 3 to 5 s. Fix (S): start the watchdog at 09:15:30, or reset `last_msg` when the session opens.

**T8. Small items. LOW. Verified by reading.**
- `HotStats.add` runs on many threads outside the lock (`:408`). Two threads can run the 1 s roll-up together, and `np.fromiter` over a deque being appended to raises "deque mutated". The stats glitch, but the packet is not lost.
- The poller spends REST calls outside market hours. The ledger never rolls its day (`:202`), so a feed left running overnight carries yesterday's count.
- On first run, `isec()` calls `get_names` (a pandas CSV parse of the master) for all 23 symbols, including the 14 that have hints. That is slow, but it only happens once.

## Good things
- `connect_stream` (`feed_breeze.py:148-181`) registers `connect_error` *before* connecting, waits 15 s and keeps the server's reason. `stream_probe` and `stream_hint` turn "Failed to connect to live stream" into an actionable cause. This is the right fix for the 16 Oct failure.
- `drop_stream` really tears the socket down, where the SDK's `ws_disconnect` only emits an event. The client is never reused (`:184-193`, `:435`).
- The hook replaces `SocketEventBreeze.on_message` *before* `watch()` binds `self.on_message` (SDK line 144). So the raw-array hot path works, and the SDK's `rewatch` on auto-reconnect still re-joins the tokens.
- One parser (`apply_packet`) feeds live, sim and replay. Segment disambiguation by length (21 vs 23) is correct against the SDK's `get_data_from_stock_token_value`. The `'4.1!False'` sentinel is handled (`:269`). The `breeze.interval = ""` workaround for the SDK's missing attribute is correct.
- `RestLedger` is persisted per day and gives a per-minute window. `rest_expiry` and `ws_expiry` are locale-independent.
- Preflight (`run_apex.py:233-300`) resolves NIFTY futures and today's ATM CE token from the actual master before the open. It would catch a strike or expiry format mismatch, a risk I could not check offline because the master download is blocked here.

## Ideas from GitHub
1. **zerodha/pykiteconnect**: https://github.com/zerodha/pykiteconnect, MIT. Cloned and read `kiteconnect/ticker.py`.
   - What it does: `_loop_pong_check` (lines 118-135) drops a "ghost" connection when the last pong is older than 2×`PING_INTERVAL`. Reconnects use exponential backoff capped by `reconnect_max_delay`, with an `on_noreconnect` callback, and `_on_connect` calls `resubscribe()`.
   - How it maps onto Apex: a **feed-side tool** in `feed_breeze.py`. Replace the single 30 s market-wide silence check with two signals: (a) transport liveness from `h.sio.eio` ping/pong age, which catches a dead socket within about 5 s even in quiet pre-open; (b) per-segment silence across futures, options and equities, which catches the server silently dropping one batch of joins. Publish both as observer fields in the control block. No trigger change.
2. **marketcalls/openalgo**: https://github.com/marketcalls/openalgo, **AGPL-3.0, concept only, no code copied**. Read `websocket_proxy/connection_manager.py`.
   - What it does: it pools several websockets per broker under a per-socket symbol cap (`MAX_SYMBOLS_PER_WEBSOCKET`). It classifies connect and subscribe failures by auth keywords (401/403/token-expiry) and forces a re-init that reads fresh credentials, separate from plain network retries.
   - How it maps onto Apex: (a) extend `stream_hint` into a typed outcome (AUTH / NETWORK / SERVER). On AUTH, `connect()` should stop the 7-attempt loop at once, set `feed_state=4`, and show "regenerate session token" on the dashboard rather than retrying for 2½ minutes. (b) Keep the option of splitting joins across two sockets if the Breeze per-socket cap turns out to be lower than the ~145 tokens (rising with each re-centre) Apex needs. That cap is unverified: ICICI's README does not state one.

## Top 3
1. **Make the recorder crash-safe:** a new file per feed process, and replay catches `zlib.error` (T1). Size S. **Before Monday.** Today, one mid-day feed restart silently destroys the rest of the first live recording.
2. **Fail loudly on an empty or partial registry and on a login hang** (T2 + T5): `SystemExit` if `NIFTY|FUT` or fewer than 40 options resolved, a socket default timeout, and timed log lines around `generate_session`. Size S. **Before Monday.**
3. **Fix hero depth** (T3): store `depth_token` on existing keys and re-centre depth with the ATM. Then add ordering guards on depth and index packets (T4). Size S to M. **Before Monday** for T3; later for T4.
