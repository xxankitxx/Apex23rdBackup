"""Read-only probe: does the broker serve 1-SECOND history (futures, weekly options, how far back)? A handful of calls.
Logs in the way the feed does (apex.feed_breeze.load_credentials; nothing from the secrets folder is printed), with the
paper-only interlock installed. It asks for market history only."""
import sys, time, json
sys.path.insert(0, r"D:\ApexOptions")
from apex import feed_breeze as fb
try:
    from apex import interlock
except ImportError:
    interlock = None
fb.install_trust()
from breeze_connect import BreezeConnect
c = fb.load_credentials("")
bz = BreezeConnect(api_key=c["api_key"])
if interlock:
    interlock.install(bz); interlock.patch_requests()
try:
    bz.generate_session(api_secret=c["api_secret"], session_token=c["session_token"])
except Exception as e:
    print("LOGIN FAILED:", type(e).__name__, str(e)[:160]); sys.exit(3)
del c
print("session established")
FUT = json.loads(sys.argv[1])
calls = 0


def ask(label, interval, day, t0, t1, product, expiry="", right="", strike=""):
    global calls
    time.sleep(1.2); calls += 1
    try:
        r = bz.get_historical_data_v2(interval=interval, from_date=f"{day}T{t0}.000Z", to_date=f"{day}T{t1}.000Z", stock_code="NIFTY", exchange_code="NFO",
                                      product_type=product, expiry_date=(expiry + "T07:00:00.000Z") if expiry else "", right=right, strike_price=str(strike))
    except Exception as e:
        r = {"Success": None, "Error": f"{type(e).__name__}: {e}"}
    rows = (r or {}).get("Success") or []
    out = dict(probe=label, interval=interval, day=day, rows=len(rows), status=(r or {}).get("Status"), error=str((r or {}).get("Error") or "")[:150])
    if rows:
        ts = sorted(str(x.get("datetime")) for x in rows)
        out.update(first=ts[0], last=ts[-1], distinct_seconds=len(set(ts)), keys=sorted(rows[0].keys())[:12])
    print(json.dumps(out), flush=True)
    return rows


ask("control: future, 1 minute, yesterday", "1minute", "2026-11-13", "10:00:00", "10:10:00", "futures", FUT["2026-11"])
for day, mon in (("2026-11-13", "2026-11"), ("2026-10-15", "2026-10"), ("2026-08-14", "2026-08"), ("2025-11-14", "2025-11"), ("2025-05-23", "2025-05")):
    ask(f"future, 1 second, {day}", "1second", day, "10:00:00", "10:10:00", "futures", FUT[mon])
for day, exp, k in (("2026-11-06", "2026-11-09", 24650), ("2026-08-14", "2026-08-18", 24350), ("2025-11-14", "2025-11-18", 25850), ("2025-05-23", "2025-05-29", 24850)):
    ask(f"option {k} call, 1 second, {day}", "1second", day, "10:00:00", "10:10:00", "options", exp, "call", k)
print("calls made:", calls)
