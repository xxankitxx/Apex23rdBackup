# Member 17 — Safety, secrets & paper-only guarantees

## Lens
Credential handling (`secrets/`, `run_apex.py session`), the preflight credential scanner, the no-order guard test, gateway exposure (host/port, Host/Origin, websockets), file writes, and anything that could leak a key or place an order. I checked against baseline 85b65ed and downloaded the real `breeze-connect==1.0.69` sdist (`/tmp/council/17/sdk`) to compare the guard with the SDK's actual method list. Probe scripts are in `/tmp/council/17/probe/`. All 60+ tests pass. The repo was not modified (`git status` is clean).

## Teardown

**F1 — The preflight credential scanner misses the file format the project itself writes. HIGH.**
`run_apex.py:162` `KEYLIKE` expects `api_key\s*[=:]\s*'…'`. In JSON the key is followed by a closing quote (`"api_key": "…"`), so the regex never matches. `cmd_session` writes exactly that format (`run_apex.py:155-156`, `json.dump(c, f)`).
- *Scenario:* the owner copies `secrets/breeze.json` to the root as a backup, or a notes file gets pasted JSON. Preflight still prints `[PASS] no credential-shaped strings`, and the next `git add .` commits the API secret.
- *Other misses (`probe/p.py`):* unquoted `.env` style (`BREEZE_API_KEY=…`), secrets containing `/ = .`, which fall outside the char class at `:162`, `apisession=` URLs, and real keys that happen to contain "sample"/"xxx". `PLACEHOLDER` (`:164`) is applied to the whole match, so the key's own text can whitelist it.
- *Extensions:* only `.py .md .json .js .html .txt .cfg .ini` are scanned. `.yml .toml .env .ps1 .bat .csv .ipynb` are not.
- *Verified:* probe script. 7 of 8 realistic leak shapes are MISSED, including the exact `cmd_session` output.

**F2 — Directory skips in the scanner are substring tests on the absolute path. MEDIUM.**
`run_apex.py:194` `any(x in dp for x in ("secrets", os.sep+"data", ".git", …))`:
- `.git` also skips `.github/`.
- Any folder whose name contains "secrets" (for example `notes_secrets_rotation/`) is skipped.
- Any folder starting "data" (`database/`) is skipped.
- If the checkout ever sits under a path with `\data…` (for example `C:\Users\ankit\data\ApexOptions`), **the whole scan is skipped and the check still PASSes**.
- *Verified:* probe script.
- The `.gitignore` check (`:206`) only greps for the word "secrets". It does not check that `data/` or `logs/` are ignored, and does not ask git (`git check-ignore`).

**F3 — The no-order guard names a method that doesn't exist and misses five that do. HIGH (for the paper-only promise).**
`tests/test_core.py:414` blocks `place_order|modify_order|cancel_order|square_off|place_gtt_order|limit_calculator`. In SDK 1.0.69 there is **no `place_gtt_order`**. The real order-capable methods it does not block are:
- `gtt_single_leg_place_order`, `gtt_three_leg_place_order`
- `gtt_*_modify_order`, `gtt_*_cancel_order`
- `aggressive_limit_order_placement`
- `set_funds`, `add_margin`

The leading `\.` means `.gtt_single_leg_place_order(` never matches. The test is also lexical only:
- `getattr(b, "place_order")(…)`, `fn = b.place_order` and `api_handler.make_request("POST", "order", …)` all pass (`probe/g.py`).
- It scans `apex/` only, not `run_apex.py`, which also builds a logged-in `BreezeConnect` (`run_apex.py:233-234`).
- Nothing enforces paper-only at **runtime**. `config.PAPER_ONLY` is read only by `validate()` (`config.py:302`).
- *Verified:* SDK source grep plus probe.

**F4 — The gateway accepts any Origin and any Host, including on websockets. MEDIUM.**
`apex/gateway.py` has no TrustedHost or Origin check. Probe `probe/ws.py` (FastAPI TestClient against the real `gateway.app`):
- `GET /api/state` with `Host: attacker.rebind.example` returns **200**.
- `/ws/state` from `Origin: https://evil.example` is **ACCEPTED**.

Browsers do not apply CORS to WebSockets. So any web page the owner has open while Apex runs can read the live position, the books, the trades and the learning state from `ws://127.0.0.1:8780`. DNS rebinding also reaches `/api/state` over HTTP.

`/ws/ticks` runs a 4 ms poll loop per connection (`gateway.py:74-102`) with no connection cap. A hostile tab that opens a few hundred sockets would steal CPU from the engine on the same box. That last part is *unverified* (read only).

No credentials are in the state blob, and the gateway has no write endpoints. So this is a privacy and availability problem, not an order risk.

**F5 — Credentials are stored in plaintext inside the project tree, with default permissions. MEDIUM.**
- `cmd_session` stores the **permanent** `api_secret` next to the daily token in `ROOT/secrets/breeze.json` (`run_apex.py:154-156`), with no restrictive mode or ACL.
- On a `D:\` root folder, the default Windows ACL usually gives *Authenticated Users* read/modify (*unverified on the owner's box*).
- Anything that zips, syncs (OneDrive), or hands the project folder to a reviewer or LLM carries `secrets/` with it. (This review copy's `secrets/` was empty, which is good.)
- The SDK also writes `logs/apiLogs.log` relative to CWD (= ROOT) at DEBUG level, including the customer-details response (name, user id; the SDK deletes `session_token` from it, per SDK `breeze_connect.py:1183-1185`). That file is gitignored but lives in the tree.

**F6 — Small items. LOW.**
- `cmd_session` prints the full login URL with the API key (`run_apex.py:145-146`). The app key is semi-public, but it lands in console scrollback.
- The session token is read with echoing `input()` (`:151`).
- A secret with stray whitespace from `getpass` is `.strip()`ed (fine).
- If an existing file has `api_key` but no `api_secret`, the secret is never asked for (`:142`). Preflight then FAILs with a confusing SDK error.
- `RestLedger`, the token cache and the trial counter use non-atomic `json.dump(…, open(p,"w"))` (`feed_breeze.py:206,223,251,257`). If the process dies mid-write, the ledger reads back corrupt and the REST budget resets. That is not money-unsafe, just rate-limit risk.
- `config.py:26-27` creates `secrets/` and `data/` dirs as an import side effect.

## Good things
- **No secret has ever been committed.** I checked `git ls-files` and grepped `git log --all -p`. `.gitignore` covers `secrets/ data/ logs/`.
- **Key and secret are typed through `getpass`** (`run_apex.py:143-144`), never passed as CLI args, so they don't show up in shell history or the process list.
- **The gateway is loopback-only** (`config.py:34`). `port_busy` binds 127.0.0.1 (`run_apex.py:122-130`).
- **The gateway is strictly read-only.** There is no POST route, so no browser path can steer the engine. Static serving is a fixed `FileResponse` plus `StaticFiles`. Path traversal `/static/../config.py` returns 404 (verified).
- **Error strings are bounded and contain no auth material.** `connect_stream` builds `auth` in-process and reports only `type(e)` plus 160 chars (`feed_breeze.py:161-178`). Preflight truncates every SDK error.
- **Global requests timeout patch** (`feed_breeze.py:298-303`). This is also the ideal hook for a runtime endpoint allowlist (see Top 3, item 1).
- **Defence in depth on paper-only, even if leaky:** `PAPER_ONLY` sits in `validate()`, CI runs `validate()` plus the guard on every push (`.github/workflows/tests.yml`), and sim/replay are isolated to `data/sim|replay` (`run_apex.py:37-48`).
- **The dashboard loads no third-party script.** Only Google Fonts CSS; `app.js` is local. There is no CDN JavaScript that could read state.

## Ideas from GitHub (all opened)

1. **gitleaks/gitleaks** — https://github.com/gitleaks/gitleaks — MIT.
   - *Borrow:* `gitleaks dir` plus a `.gitleaks.toml` with `[extend] useDefault = true` and one custom rule for Breeze (`(?i)"?(api_?secret|session_?token|api_?key)"?\s*[:=]\s*"?[^\s",]{8,}`).
   - *Map:* a **tool**. Add it as a pre-commit hook and a CI step, and have preflight shell out to it when it is installed (falling back to the fixed in-house regex). This closes F1 and F2 for every file type and for git history.

2. **Yelp/detect-secrets** — https://github.com/Yelp/detect-secrets — Apache-2.0.
   - *Borrow:* the `.secrets.baseline` concept (known, audited findings are recorded, and only *new* ones fail) plus the high-entropy detectors (Base64 above 4.5, Hex above 3.0).
   - *Map:* replace `PLACEHOLDER` whitelisting (F1's self-whitelisting bug) with an explicit baseline of the doc examples, and with `# pragma: allowlist secret` on deliberate stand-ins.

3. **encode/starlette** `starlette/middleware/trustedhost.py` — https://github.com/encode/starlette — BSD-3-Clause.
   - *Borrow:* `TrustedHostMiddleware(allowed_hosts=["127.0.0.1","localhost"])`, which checks **both http and websocket scopes** and returns 400 on a foreign Host.
   - *Map:* a one-line `app.add_middleware(...)` in `gateway.py`, plus a small Origin check in `ws_ticks`/`ws_state`: if `ws.headers.get("origin")` is not `http://127.0.0.1:8780` or `http://localhost:8780`, close with code 1008. Add a per-endpoint connection cap of about 4. This closes F4.

4. **jaraco/keyring** — https://github.com/jaraco/keyring — MIT (pyproject).
   - *Borrow:* `keyring.set_password("ApexOptions", "breeze_api_secret", s)` / `get_password(...)`, backed by Windows Credential Locker.
   - *Map:* `cmd_session` and `load_credentials`. The permanent `api_secret` goes to the OS vault, and only the daily `session_token` stays in a file (now harmless after 24 h). Keep the file fallback when keyring returns `None`. This closes most of F5.

## Top 3

1. **A runtime paper-only interlock plus a correct static guard. Size S, before Monday.**
   - In the existing `_req` patch (`feed_breeze.py:300`), refuse any URL whose last path segment is not in an allowlist `{customerdetails, quotes, optionchain}`. Raise `RuntimeError("PAPER_ONLY: blocked <endpoint>")` for `order`, `gttorder`, `squareoff`, `funds`, `margin` and the rest. Install the same patch in `cmd_preflight`.
   - After `BreezeConnect(...)`, rebind every attribute matching `order|square|gtt|funds|margin|limit_calc` on the instance and on `ApificationBreeze` to a raiser.
   - Fix the test: derive the forbidden set from `dir(BreezeConnect)` when the SDK is importable, otherwise use the full static list above. Drop the leading-dot requirement, catch `getattr(…, "<name>")`, and scan `run_apex.py` too.
   - Add a unit test that the interlock rejects a fake `.../order` request.

2. **Fix the credential scanner. Size S, before Monday.**
   - Allow an optional closing quote after the key name (`["']?\s*[:=]`), accept unquoted values, and widen the value char class to `[^\s"',]`.
   - Apply `PLACEHOLDER` to the *value* only.
   - Skip directories by `os.path.relpath(dp, ROOT).split(os.sep)[0]` in `{secrets, data, logs, .git, __pycache__}`.
   - Add `.yml .toml .env .ps1 .bat .csv`.
   - Replace the `.gitignore` grep with `git check-ignore -q secrets/breeze.json data/x logs/x`.
   - Add a regression test that feeds the exact `cmd_session` JSON and asserts it is CAUGHT. Later, add gitleaks in CI.

3. **Lock down the gateway and move the long-lived secret out of the tree. Size M, later** (the gateway part, about 10 lines, could go before Monday).
   - Gateway: TrustedHost middleware, a websocket Origin check, and a connection cap.
   - Secrets: the `api_secret` goes to keyring. Support an optional `APEX_SECRETS` directory outside the project (for example `%APPDATA%\ApexOptions`). Have the feed run with CWD in `data/logs` so the SDK's `logs/apiLogs.log` lands under the already-ignored data dir.
