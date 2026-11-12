"""11 Nov 2026 (docs/49, owner: "book higher and re-enter the same direction if the conviction to run is still strong"):
the two shadow twins of c20_9y that act on the hold and re-entry models of apex/predict/hold.py.

  hx_c20_9y (hold_exit)  same strategy, same entries as c20_9y. Every 15 s while holding: if the hold model says
                         holding to the parent's own exit is worth less than its line, SELL NOW. It can only exit
                         earlier than the parent would.
  rx_c20_9y (reenter)    same strategy, same entries and exits as c20_9y. After each of its own exits, for 15 minutes,
                         every 15 s: if the re-entry model says buying the same contract back is worth more than its
                         line, BUY once. That leg has a fixed exit: 8 % off its peak bid, 15 minutes, or the council's
                         flat time. While that leg is held the strategy keeps running as if flat (its BUY signals are
                         skipped and counted), so its state is not disturbed.
Both are shadow books (twin=True): never in the pool, never champion. Without a model file they do exactly what the
parent does. Every decision is counted on the position or the book, so a twin that never acted is visible."""
from datetime import date

from ..predict import hold as Hd


def _hist(ctx, oid):
    oh = (ctx.get("ohist") or {})
    dq = oh.get(oid)
    mids = [(h[0], h[3]) for h in list(dq)[-240:]] if dq else []
    fwd = list(oh.get("fwd") or [])[-700:]
    return mids, fwd


def _ctx_common(ctx, p, o):
    now = float(ctx["now_s"])
    dte = (date.fromisoformat(p["expiry"]) - ctx["now_dt"].date()).days if p.get("expiry") else 0
    tod = (ctx["now_dt"].hour * 3600 + ctx["now_dt"].minute * 60 + ctx["now_dt"].second) - (9 * 3600 + 15 * 60)
    iv = (o.get("iv") or 0) / 100.0 if o.get("iv") else None
    return now, dte, tod, iv


def sell_now(ctx, book, p, o, peak_bid):
    """hx twin: a reason to sell now, or None. Called each second; decides every Hd.CHECK_S seconds."""
    m = Hd.model("hold")
    if not m.ok or not o or not o.get("bid") or not o.get("ask"):
        return None
    now = float(ctx["now_s"])
    if now - float(p.get("hx_t") or 0) < Hd.CHECK_S or now - p["t_in"] < Hd.CHECK_S:
        return None
    p["hx_t"] = now
    now, dte, tod, iv = _ctx_common(ctx, p, o)
    mids, fwd = _hist(ctx, o.get("id"))
    d = 1 if p.get("rr") == "CE" else -1
    x = Hd.hold_features(now, p["entry"], o["bid"], o["ask"], mids, peak_bid, p["t_in"], p.get("peak_t") or p["t_in"],
                         fwd, d, iv, dte, tod)
    p["hx_checks"] = int(p.get("hx_checks") or 0) + 1
    if x is None:
        p["hx_missing"] = int(p.get("hx_missing") or 0) + 1
        return None
    v = m.predict(x)
    p["hx_last"] = round(v, 2)
    if v < m.line:
        return f"HOLD MODEL SELL (hold worth {v:+.1f} % < {m.line:+.1f} %)"
    return None


def note_exit(book, tr):
    """rx twin: remember an exit of a strategy-managed trade, to consider buying it back."""
    if not tr or tr.get("re_leg") or not book.p.get("reenter"):
        return
    try:
        book.ctl["rx_last"] = dict(t=float(tr["t_out"]), exit=float(tr["exit"]), gain=float(tr["exit"]) / float(tr["entry"]) - 1.0,
                                   peak=float(tr.get("peak_bid") or tr["exit"]), key=tr["key"], rr=tr["rr"],
                                   expiry=tr.get("expiry"), used=False, checked=0)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        book.ctl.pop("rx_last", None)


def want_reentry(ctx, book):
    """rx twin, flat: (option row, reason) to buy back now, or (None, None)."""
    last = book.ctl.get("rx_last")
    m = Hd.model("reenter")
    if not last or last.get("used") or not m.ok:
        return None, None
    now = float(ctx["now_s"])
    if now - last["t"] > Hd.REENTER_WINDOW_S:
        book.ctl.pop("rx_last", None)
        return None, None
    if now - float(last.get("t_chk") or 0) < Hd.CHECK_S:
        return None, None
    last["t_chk"] = now
    o = (ctx.get("by_key") or {}).get(last["key"])
    if not o or not o.get("bid") or not o.get("ask") or (o.get("age") or 99) > 15:
        return None, None
    p = dict(expiry=last.get("expiry"), rr=last["rr"])
    now, dte, tod, iv = _ctx_common(ctx, p, o)
    mids, fwd = _hist(ctx, o.get("id"))
    d = 1 if last["rr"] == "CE" else -1
    x = Hd.re_features(now, last["t"], last["exit"], last["gain"], last["peak"], o["bid"], o["ask"], mids, fwd, d, iv, dte, tod)
    last["checked"] += 1
    if x is None:
        return None, None
    v = m.predict(x)
    last["pred"] = round(v, 2)
    if v > m.line:
        last["used"] = True
        return o, f"RE-ENTRY (model {v:+.1f} % > {m.line:+.1f} %, {int((now - last['t']) // 60)} min after the exit)"
    return None, None


def leg_exit(ctx, p, o, flat):
    """rx twin: the re-entry leg's fixed exit, a reason or None."""
    bid = (o or {}).get("bid")
    if not bid:
        return None
    p["re_peak"] = max(float(p.get("re_peak") or p["entry"]), bid)
    if bid <= p["re_peak"] * (1 - Hd.RE_TRAIL):
        return f"RE-ENTRY EXIT (8 % off its peak {p['re_peak']:.1f})"
    if float(ctx["now_s"]) - p["t_in"] >= Hd.RE_HOLD_S:
        return "RE-ENTRY EXIT (15 minutes)"
    if flat:
        return "RE-ENTRY EXIT (council flat time)"
    return None
