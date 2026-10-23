"""WP-6 checks (preflight, paper-only interlock, supervisor, calendar, config):
python tests/test_wp6.py

Credential-shaped test strings are assembled at run time (K_* below), so the preflight
scanner never finds a literal in this file."""
import ast
import json
import os
import sys
import tempfile
import types

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime  # noqa: E402

from apex import config, interlock  # noqa: E402
import run_apex  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K_KEY, K_SECRET, K_TOKEN = "api" + "_key", "api" + "_secret", "session" + "_token"


# ── (a) scanner catches what the project itself writes ──────────────────────────
def test_scanner_catches_real_shapes():
    session_json = json.dumps({K_KEY: "8a1F3x9Q2w7E5r6T", K_SECRET: "a9B/8c+7D6e5F4=", K_TOKEN: "48211937"})
    assert run_apex.credential_hits(session_json), session_json          # cmd_session's own output
    assert run_apex.credential_hits(K_KEY.upper() + "=k3J9sL2mQ8vX\n")    # a .env line
    assert run_apex.credential_hits('"' + K_SECRET + '": "abc/def=ghi.jkl"')
    assert run_apex.credential_hits(K_TOKEN + ": 'Zq81Lp02Xc93'")        # yaml
    assert not run_apex.credential_hits(K_KEY + '="sk-no-key-required"')   # a doc stand-in
    assert not run_apex.credential_hits(K_KEY + '=c["' + K_KEY + '"]')     # code that reads a key
    # the OLD pattern missed the JSON shape (C-32): keep the regression visible
    import re
    old = re.compile(r"(api_?key|api_?secret|session_?token)\s*[=:]\s*['\"][A-Za-z0-9~!@#$%^&*()_+\-]{8,}['\"]", re.I)
    assert not old.search(session_json)


def test_scanner_tree_skips_top_level_only():
    with tempfile.TemporaryDirectory() as d:
        def put(rel, text):
            p = os.path.join(d, *rel.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
        leak = json.dumps({K_KEY: "8a1F3x9Q2w7E5r6T"})
        put("secrets/breeze.json", leak)               # skipped: that is where it belongs
        put("data/x.json", leak)                       # skipped
        put(".git/config", leak)                       # skipped
        put(".github/workflows/ci.yml", K_SECRET + ": Xy7Pq2Lm9Rt4\n")   # scanned (was skipped as '.git')
        put(".env", K_KEY.upper() + "=k3J9sL2mQ8vX\n")                   # scanned (new extension)
        put("tools/run.ps1", "$" + K_TOKEN + " = 'Zq81Lp02Xc93'\n")
        put("docs/notes.md", K_KEY + '="sk-no-key-required"\n')         # stand-in: not a leak
        put("apex/sub/data/ok.json", leak)             # nested 'data' is NOT top-level -> scanned
        got = sorted(run_apex.scan_credentials(d))
        assert got == sorted([".github/workflows/ci.yml", ".env", "tools/run.ps1", "apex/sub/data/ok.json"]), got


# ── (b) a checkout under ...\data\... is still scanned (C-75) ───────────────────
def test_scanner_root_under_data_path():
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "data", "checkout")
        os.makedirs(root)
        with open(os.path.join(root, "leak.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps({K_SECRET: "a9B/8c+7D6e5F4="}))
        assert run_apex.scan_credentials(root) == ["leak.json"]


def test_repo_tree_is_clean():
    assert run_apex.scan_credentials(ROOT) == [], run_apex.scan_credentials(ROOT)


def test_gitignore_check():
    assert run_apex.gitignore_ok(ROOT)
    with tempfile.TemporaryDirectory() as d:          # not a git repo: falls back to .gitignore
        with open(os.path.join(d, ".gitignore"), "w") as f:
            f.write("secrets/\n")
        assert not run_apex.gitignore_ok(d)            # data/ and logs/ missing
        with open(os.path.join(d, ".gitignore"), "w") as f:
            f.write("secrets/\ndata/\nlogs/\n")
        assert run_apex.gitignore_ok(d)


# ── (c) runtime paper-only interlock (C-33) ─────────────────────────────────────
class ApificationBreeze:                     # stands in for the SDK's REST handler class
    def place_order(self, **k):
        return "SENT"

    def get_quotes(self, **k):
        return {"Success": [{"ltp": 1.0}]}


class FakeBreeze:
    """The SDK surface the live feed uses, plus the order-like methods it must never reach."""
    def __init__(self):
        self.sio_order_refresh_handler = None    # data attributes whose names match: untouched
        self.orderconnect = 0
        self.sio_rate_refresh_handler = None
        self.user_id = "u"
        self.session_key = "s"
        self.api_handler = ApificationBreeze()

    def generate_session(self, api_secret, session_token): return "ok"
    def get_stock_token_value(self, **k): return ("4.1!1", "4.2!1")
    def get_names(self, **k): return {"isec_stock_code": "X"}
    def get_quotes(self, **k): return {"Success": []}
    def get_option_chain_quotes(self, **k): return {"Success": []}
    def subscribe_feeds(self, **k): return {"message": "ok"}
    def place_order(self, **k): return "SENT"
    def gtt_single_leg_place_order(self, **k): return "SENT"
    def set_funds(self, **k): return "SENT"
    def square_off(self, **k): return "SENT"
    def add_margin(self, **k): return "SENT"
    def limit_calculator(self, **k): return "SENT"
    def aggressive_limit_order_placement(self, **k): return "SENT"


def _raises(fn):
    try:
        fn()
    except RuntimeError as e:
        return str(e).startswith("PAPER_ONLY: blocked")
    return False


def test_interlock_install_blocks_orders_keeps_data():
    b = FakeBreeze()
    names = interlock.install(b)
    for m in ("place_order", "gtt_single_leg_place_order", "set_funds", "square_off", "add_margin",
              "limit_calculator", "aggressive_limit_order_placement"):
        assert m in names and _raises(getattr(b, m)), m
    assert _raises(b.api_handler.place_order)          # the handler class is blocked too
    assert b.api_handler.get_quotes() == {"Success": [{"ltp": 1.0}]}
    # everything the feed uses still works, and data attributes are untouched
    assert b.generate_session("x", "y") == "ok"
    assert b.get_stock_token_value() == ("4.1!1", "4.2!1")
    assert b.get_names() and b.get_quotes() == {"Success": []} and b.get_option_chain_quotes() == {"Success": []}
    assert b.subscribe_feeds(stock_token=["4.1!1"]) == {"message": "ok"}
    assert b.sio_order_refresh_handler is None and b.orderconnect == 0
    assert interlock.install(b) == names or set(interlock.install(b)) <= set(names)   # idempotent
    assert interlock.install(None) == []


def test_interlock_spares_every_breeze_call_the_live_code_makes():
    """Every attribute the live feed and preflight touch on the Breeze object must survive
    install() — otherwise Monday's live session would be blocked by its own interlock."""
    used = set()
    for rel in ("apex/feed_breeze.py", "run_apex.py"):
        tree = ast.parse(open(os.path.join(ROOT, rel), encoding="utf-8").read())
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute):
                v = n.value
                if isinstance(v, ast.Attribute) and v.attr == "breeze":       # self.breeze.X
                    used.add(n.attr)
                elif isinstance(v, ast.Name) and v.id in ("br", "breeze"):    # br.X / breeze.X
                    used.add(n.attr)
    assert {"generate_session", "get_quotes", "get_option_chain_quotes", "subscribe_feeds",
            "get_stock_token_value", "get_names"} <= used, used
    hit = sorted(u for u in used if interlock.BLOCK.search(u))
    assert not hit, f"the interlock would block live calls: {hit}"


def test_interlock_patch_requests_allowlist():
    real = sys.modules.get("requests")
    sent = []

    class Session:
        def request(self, method, url, *a, **k):
            sent.append(url)
            return "sent"
    fake = types.ModuleType("requests")
    fake.Session = Session
    sys.modules["requests"] = fake
    try:
        assert interlock.patch_requests()
        assert interlock.patch_requests()              # second call does not double-wrap
        s = Session()
        api = "https://api.icicidirect.com/breezeapi/api/v1/"
        for ok in (api + "customerdetails", api + "quotes", api + "optionchain",
                   "https://breezeapi.icicidirect.com/api/v2/historicalcharts",
                   "https://directlink.icicidirect.com/MotherAppMaster/SecurityMaster.zip"):
            assert s.request("GET", ok) == "sent", ok
            assert s.request(method="GET", url=ok) == "sent", ok      # requests.get passes keywords
        for bad in ("order", "squareoff", "gttorder", "funds", "margin", "fnolmtpriceandqtycal",
                    "margincalculator"):
            assert _raises(lambda: s.request("POST", api + bad)), bad
        assert _raises(lambda: s.request("POST", api + "order?x=quotes"))   # query string cannot smuggle
        assert not any(u.endswith(("order", "squareoff", "funds")) for u in sent)
    finally:
        if real is not None:
            sys.modules["requests"] = real
        else:
            sys.modules.pop("requests", None)


# ── (d) AST no-order guard over apex/ and run_apex.py ───────────────────────────
ORDER_NAMES = {
    "place_order", "modify_order", "cancel_order", "square_off", "limit_calculator",
    "gtt_single_leg_place_order", "gtt_single_leg_modify_order", "gtt_single_leg_cancel_order",
    "gtt_three_leg_place_order", "gtt_three_leg_modify_order", "gtt_three_leg_cancel_order",
    "aggressive_limit_order_placement", "set_funds", "add_margin", "preview_order",
}


def order_refs(src, fname="<src>"):
    hits = []
    for n in ast.walk(ast.parse(src, fname)):
        name = None
        if isinstance(n, ast.Attribute):
            name = n.attr                                   # x.place_order / x.place_order(
        elif isinstance(n, ast.Name):
            name = n.id
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = n.name
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            name = n.value.strip()                          # getattr(x, "place_order"), dispatch dicts
        elif isinstance(n, ast.keyword):
            name = n.arg
        if name in ORDER_NAMES:
            hits.append(f"{fname}:{getattr(n, 'lineno', '?')}:{name}")
    return hits


def test_no_order_calls_ast_guard():
    assert order_refs("b.place_order(x=1)") and order_refs('getattr(b, "place_order")(1)')
    assert order_refs("b.gtt_three_leg_cancel_order()") and order_refs("f = br.set_funds")
    assert not order_refs("b.get_quotes(); s = 'place an order'")
    files = [os.path.join(ROOT, "run_apex.py")]
    for d, _, fs in os.walk(os.path.join(ROOT, "apex")):
        files += [os.path.join(d, f) for f in fs if f.endswith(".py")]
    hits = []
    for p in files:
        hits += order_refs(open(p, encoding="utf-8").read(), os.path.relpath(p, ROOT))
    assert not hits, hits
    assert config.PAPER_ONLY is True


# ── (e) strict variant keys (C-45) ──────────────────────────────────────────────
def test_validate_rejects_unknown_and_conflicting_keys():
    assert config.validate() == []
    base = {"m_star": 2.0, "s_star": 0.5, "L_star": 3.0, "d_star": 12.0}
    for extra, frag in (({"exit_bok": True}, "unknown key"), ({"spike": True, "random": True}, "combines")):
        config.VARIANTS["_wp6_probe"] = dict(base, **extra)
        try:
            probs = config.validate()
            assert any("_wp6_probe" in p and frag in p for p in probs), probs
        finally:
            del config.VARIANTS["_wp6_probe"]
    assert config.validate() == []


def test_registry_values_unchanged():
    """WP-6 must not move a number (D-033): the registry is exactly the baseline one."""
    assert config.TRIGGER == {"m_star": 2.0, "s_star": 0.50, "L_star": 3.0, "d_star": 12.0}
    assert len(config.VARIANTS) == 32 and config.IV_RISE_CAP == 1.5      # +ivinterp +novol +trend +2 spot (D-116) +d20 +tvfast (D-118) +fade_switch (D-121) +spot nolock (D-127) +spot first-touch twin (D-131) +pullback book (D-134) +dual shadow (D-137) +4 council-9 books (D-141)
    assert config.VARIANTS["m2.0_s0.5_bookexit"]["exit_book"] is True
    assert config.CONTROLS == ("futures_only", "random_entry", "premium_momentum")


# ── (f) holiday coverage to the farthest expiry (C-60) ──────────────────────────
def test_holiday_coverage_gap():
    xmas_eve = datetime(2026, 12, 24, 10, 0, tzinfo=config.IST)         # w1 = Tue 5 Jan 2027
    assert config.weekly_expiries(xmas_eve, 2)[1].year == 2027
    saved = set(config.NSE_HOLIDAYS)
    try:
        config.NSE_HOLIDAYS.clear(); config.NSE_HOLIDAYS.update(h for h in saved if h.startswith("2026"))
        assert config.holiday_coverage_gaps(xmas_eve) == [2027]
        config.NSE_HOLIDAYS.add("2027-01-26")
        assert config.holiday_coverage_gaps(xmas_eve) == []
    finally:
        config.NSE_HOLIDAYS.clear(); config.NSE_HOLIDAYS.update(saved)
    monday = datetime(2026, 10, 19, 9, 0, tzinfo=config.IST)
    assert config.holiday_coverage_gaps(monday) == []                   # Monday's preflight passes
    assert config.is_trading_day(monday.date())


def test_event_days_verified():
    assert config.EVENT_DAYS == {"2026-12-04": "RBI policy decision", "2027-02-05": "RBI policy decision"}
    for d in config.EVENT_DAYS:
        assert date.fromisoformat(d).weekday() == 4, d      # both are Fridays, not the old Saturday


# ── supervisor ──────────────────────────────────────────────────────────────────
def test_stale_report():
    s = 1_000 * 10**9
    now = s + 120 * 10**9
    assert run_apex.stale_report(now, now - 2 * 10**9, now - 1 * 10**9, s) == []
    r = dict(run_apex.stale_report(now, now - 15 * 10**9, now - 1 * 10**9, s))
    assert set(r) == {"ENGINE"} and 14 < r["ENGINE"] < 16
    assert run_apex.stale_report(s + 30 * 10**9, 0, 0, s) == []          # grace: not beaten yet
    assert {n for n, _ in run_apex.stale_report(now, 0, now, s)} == {"ENGINE"}
    noon = datetime(2026, 10, 19, 12, 0, tzinfo=config.IST)
    assert run_apex.in_market_hours(config, noon)
    assert not run_apex.in_market_hours(config, datetime(2026, 10, 20, 12, 0, tzinfo=config.IST))   # holiday
    assert not run_apex.in_market_hours(config, datetime(2026, 10, 19, 8, 0, tzinfo=config.IST))


class FakeProc:
    """poll() returns 0 once `stops_after` seconds have passed (None = never on its own)."""
    def __init__(self, stops_after):
        import time
        self.t0, self.after = time.time(), stops_after
        self.terminated = False
        self.returncode = None

    def poll(self):
        import time
        if self.terminated or (self.after is not None and time.time() - self.t0 >= self.after):
            self.returncode = 0
            return 0
        return None

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminated = True


def test_engine_gets_its_own_deadline_after_the_feed():
    """Old code: one 12-s deadline shared by feed and engine. A feed that hangs for the whole
    feed deadline used to leave the engine no time; now the engine gets its own."""
    msgs = []
    procs = {"feed": FakeProc(None), "engine": FakeProc(0.9), "gateway": FakeProc(None)}
    run_apex.stop_children(procs, msgs.append, feed_s=0.6, engine_s=1.0)
    assert not procs["engine"].terminated, "engine was terminated before its own deadline"
    assert procs["feed"].terminated and procs["gateway"].terminated
    assert msgs == []
    procs = {"feed": FakeProc(0.0), "engine": FakeProc(None), "gateway": FakeProc(None)}
    run_apex.stop_children(procs, msgs.append, feed_s=0.2, engine_s=0.3)
    assert procs["engine"].terminated and any("ENGINE did not stop" in m for m in msgs)


# ── replay isolation (C-20) ─────────────────────────────────────────────────────
def test_replay_run_folders_are_unique():
    a = run_apex.replay_run_dir("data/ticks/2026-10-19.jsonl.gz", "20261019-160000")
    b = run_apex.replay_run_dir("/x/2026-10-19.jsonl.gz", "20261019-160105")
    assert a != b
    base = os.path.join(run_apex.ROOT, "data", "replay", "2026-10-19")
    assert a == os.path.join(base, "20261019-160000") and b == os.path.join(base, "20261019-160105")
    assert run_apex.child_env("replay", a)["APEX_DATA"] == a
    assert run_apex.child_env("live")["APEX_DATA"] == os.path.join(run_apex.ROOT, "data")   # live unchanged
    assert run_apex.child_env("sim")["APEX_DATA"] == os.path.join(run_apex.ROOT, "data", "sim")


def test_ci_runs_every_package_suite():
    y = open(os.path.join(ROOT, ".github", "workflows", "tests.yml"), encoding="utf-8").read()
    assert "tests/test_core.py" in y and "tests/test_wp$n.py" in y and "1 2 3 4 5 6 7" in y


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
