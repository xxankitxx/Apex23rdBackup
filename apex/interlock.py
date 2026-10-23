"""
Paper-only interlock (C-33): a runtime guard, not just a lexical test.

v1 is paper trading only (config.PAPER_ONLY, owner 17 Oct 2026). Two layers:

  install(breeze)   every callable attribute of the Breeze object, of its class and
                    of the SDK's REST handler class whose NAME looks like an order,
                    square-off, GTT, funds, margin or limit-calculator call is
                    replaced by a stub that raises RuntimeError("PAPER_ONLY: ...").
                    Read-only data calls the feed uses (generate_session,
                    get_stock_token_value, get_names, get_quotes,
                    get_option_chain_quotes, subscribe_feeds) do not match and
                    are untouched.

  patch_requests()  wraps requests.Session.request (which requests.get/post/...
                    also go through) so a URL whose last path segment is not on
                    ALLOWED_SEGMENTS raises the same error before any byte is sent.
                    The allowlist is what SDK 1.0.69 needs for a data-only session:
                      customerdetails     generate_session() -> api_util()
                      SecurityMaster.zip  generate_session() -> get_stock_script_list()
                      quotes, optionchain REST quotes / option chain (feed poller)
                      historicalcharts    history (v1 and v2)
                      StockScriptNew.csv  the SDK's older script-list source
                      socket.io           an engine.io polling fallback, if ever used

Both are idempotent and never raise themselves.
"""
import re
from urllib.parse import urlsplit

BLOCK = re.compile(r"order|square|gtt|funds|margin|limit_calc", re.I)
ALLOWED_SEGMENTS = frozenset(s.lower() for s in (
    "customerdetails", "quotes", "optionchain", "historicalcharts",
    "SecurityMaster.zip", "StockScriptNew.csv", "socket.io",
))
_MARK = "_apex_paper_only"


class PaperOnlyError(RuntimeError):
    pass


def _stub(name):
    def blocked(*a, **k):
        raise PaperOnlyError(f"PAPER_ONLY: blocked {name}")
    blocked.__name__ = f"blocked_{name}"
    setattr(blocked, _MARK, True)
    return blocked


def _block_on(target, names, out):
    for name in names:
        if name.startswith("__") or not BLOCK.search(name):
            continue
        try:
            cur = getattr(target, name)
        except Exception:
            continue
        # only callables: data attributes such as sio_order_refresh_handler (None or a
        # socket object the SDK tests for truthiness) and orderconnect (an int) stay as they are
        if not callable(cur) or isinstance(cur, type) or getattr(cur, _MARK, False):
            continue
        try:
            setattr(target, name, _stub(name))
            out.append(name)
        except Exception:
            pass


def install(breeze):
    """Block every order-like method on this Breeze object. Returns the blocked names."""
    out = []
    if breeze is None:
        return out
    try:
        cls = type(breeze)
        for k in cls.__mro__:
            if k is object:
                continue
            _block_on(k, list(vars(k)), out)
        _block_on(breeze, list(getattr(breeze, "__dict__", {})), out)
        # the SDK's REST handler class (BreezeConnect.place_order delegates to it); the
        # instance is created later by generate_session(), so patch the class itself
        import sys
        mod = sys.modules.get(cls.__module__)
        handler = getattr(mod, "ApificationBreeze", None) if mod else None
        if isinstance(handler, type):
            _block_on(handler, list(vars(handler)), out)
        h = getattr(breeze, "api_handler", None)
        if h is not None and not isinstance(h, type):
            _block_on(type(h), list(vars(type(h))), out)
    except Exception:
        pass
    return sorted(set(out))


def allowed_url(url) -> bool:
    try:
        path = urlsplit(str(url)).path
    except Exception:
        return False
    segs = [s for s in path.split("/") if s]
    return bool(segs) and segs[-1].lower() in ALLOWED_SEGMENTS


def patch_requests():
    """Refuse any HTTP request whose last path segment is not a data endpoint."""
    try:
        import requests
    except Exception:
        return False
    cur = requests.Session.request
    if getattr(cur, _MARK, False):
        return True

    def request(self_, method, url, *a, **k):
        if not allowed_url(url):
            seg = [s for s in urlsplit(str(url)).path.split("/") if s]
            raise PaperOnlyError(f"PAPER_ONLY: blocked {seg[-1] if seg else url}")
        return cur(self_, method, url, *a, **k)
    setattr(request, _MARK, True)
    requests.Session.request = request
    return True
