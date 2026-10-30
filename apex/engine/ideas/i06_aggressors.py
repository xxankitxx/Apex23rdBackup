"""Aggressors (owner, 28 Oct: "buyers vs sellers queued on each strike and how fast that changes").

Who is HITTING: traded volume classified by the aggressor. For ATM +- 2 CE and PE, each second's volume (change in
ttq) is a BUY if the ltp traded at/above the previous second's ask (or above its mid), a SELL if at/below the previous
bid (or below the mid), and by the tick rule (last price change) otherwise. Summed over 1 and 5 minutes per side.

Uses only the near touch (ltp, bid, ask, ttq) -- never tbq/tsq, which are dominated by far resting orders (R2_01).
A 1-Hz snapshot can hold several trades per second, so the split is an approximation (Lee-Ready on snapshots).

States: CE BUYERS HITTING, PE BUYERS HITTING, CE SELLERS DUMPING, PE SELLERS DUMPING, MIXED, THIN, WARMING.
Value: net aggressive buy share (%) of the leading side over 5 min, (buy - sell) / (buy + sell); negative when the
leading side is being dumped."""
import math

import numpy as np

NAME = "aggressors"
TITLE = "Aggressors: who is hitting"
IDEA = "Buyers vs sellers on each strike: whose options are being bought (or dumped) at the touch, last 1 and 5 min."
VERDICT = ("Order-flow imbalance (OFI, L1/L5 book) showed no edge as an entry rule (r~0, sign flips by day; "
           "docs/18, R2_01/R2_06); shown for watching only.")
EVERY_S = 5

WIN = 300           # 5-min window
WIN1 = 60           # 1-min window
ENTER = 0.22        # leading side's |net share| to enter a directional state
STAY = 0.06         # ... to stay in it (checked after MIN_HOLD)
SWITCH = 0.06       # a rival must beat the held state by this much to take over
MIN_HOLD = 120      # min seconds in any state before it may change
DWELL = 240         # min seconds in a directional state before a stronger rival may take over
THIN_FRAC = 0.30    # 5-min volume below 30 % of the day's median 5-min volume -> THIN
ALERT_SHARE = 0.40  # alert: 5-min and 1-min share both >= 40 % ...
ALERT_VOL = 1.5     # ... on >= 1.5x the day's median 5-min volume
ALERT_GAP = 900     # at most one alert per 15 min

_LABEL = {("CE", 1): "CE BUYERS HITTING", ("PE", 1): "PE BUYERS HITTING",
          ("CE", -1): "CE SELLERS DUMPING", ("PE", -1): "PE SELLERS DUMPING"}


_NEED = WIN + 40     # rows read per contract (5 min + a little extra for the tick rule)


def _recent(hist, key):
    """The newest _NEED rows of one contract's 1-Hz history, oldest -> newest (a copy), or None.
    Reads the ring directly so the full hour is not concatenated for every contract (History.table copies
    IDEAS_HIST_S rows); falls back to History.table if the ring layout is not what we expect."""
    tab = hist.table(key)          # History.table is a zero-copy view (29 Oct); copy only the rows used
    return None if tab is None else np.array(tab[-_NEED:])


def _classify(X, now):
    """X: (k, m, ncol) right-aligned histories of k contracts (nan-padded). -> (buy, sell, in1) each (k, m-1):
    aggressive buy / sell qty per second, inside the last WIN s, and a mask for the last WIN1 s. One vectorised pass."""
    T, ltp, bid, ask, ttq = X[:, :, 0], X[:, :, 1], X[:, :, 2], X[:, :, 3], X[:, :, 7]
    with np.errstate(invalid="ignore"):
        dv = np.diff(ttq, axis=1)
        dv = np.where(np.isfinite(dv) & (dv > 0), dv, 0.0)
        p, pb, pa = ltp[:, 1:], bid[:, :-1], ask[:, :-1]
        okq = np.isfinite(pb) & np.isfinite(pa) & (pb > 0) & (pa >= pb)
        at_ask = okq & (p >= pa)
        at_bid = okq & (p <= pb)
        buy = at_ask & ~at_bid
        sell = at_bid & ~at_ask
        sprd = okq & (pb < pa) & ~(buy | sell)
        pm = (pb + pa) / 2.0
        buy |= sprd & (p > pm)
        sell |= sprd & (p < pm)
        rest = ~(buy | sell)
        # tick rule: sign of the last non-zero price change up to this second
        d = np.sign(np.diff(ltp, axis=1))
        d = np.where(np.isfinite(d), d, 0.0)
        idx = np.where(d != 0, np.arange(d.shape[1])[None, :], -1)
        idx = np.maximum.accumulate(idx, axis=1)
        tick = np.where(idx >= 0, np.take_along_axis(d, np.maximum(idx, 0), axis=1), 0.0)
        buy |= rest & (tick > 0)
        sell |= rest & (tick < 0)
        Tn = T[:, 1:]
        keep = Tn > now - WIN
        in1 = Tn > now - WIN1
    return dv * (buy & keep), dv * (sell & keep), in1


class Idea:
    def __init__(self):
        self.state = None           # (side, sign) or "MIXED"/"THIN"
        self.since = None
        self.vols = []              # 5-min totals sampled once a minute (day's own scale)
        self.last_sample = -1e9
        self.last_alert = -1e9

    def update(self, env):
        now = env.t
        if env.atm is None or env.hm < 9 * 60 + 15 + 6:
            return {"state": "WARMING", "text": "needs 5 minutes of trades"}
        keys, tabs = [], []
        for k in range(-2, 3):
            strike = int(env.atm + k * env.step)
            for rr in ("CE", "PE"):
                tab = _recent(env.hist, (strike, rr))
                if tab is not None and len(tab) >= 3:
                    keys.append(rr)
                    tabs.append(tab)
        n_ok = len(tabs)
        acc = {"CE": [0.0, 0.0, 0.0, 0.0], "PE": [0.0, 0.0, 0.0, 0.0]}   # buy5 sell5 buy1 sell1
        if n_ok >= 4:
            m = max(len(t) for t in tabs)
            X = np.full((n_ok, m, tabs[0].shape[1]), np.nan)
            for j, t in enumerate(tabs):
                X[j, m - len(t):] = t
            B, S, in1 = _classify(X, now)
            b5, s5 = B.sum(axis=1), S.sum(axis=1)
            b1, s1 = (B * in1).sum(axis=1), (S * in1).sum(axis=1)
            for j, rr in enumerate(keys):
                a = acc[rr]
                a[0] += float(b5[j])
                a[1] += float(s5[j])
                a[2] += float(b1[j])
                a[3] += float(s1[j])
        if n_ok < 4:
            return {"state": "WARMING", "text": "ATM +-2 strikes not in the history yet"}
        tot5 = sum(acc["CE"][:2]) + sum(acc["PE"][:2])
        if now - self.last_sample >= 60 and tot5 > 0:
            self.last_sample = now
            self.vols.append(tot5)
        med = float(np.median(self.vols)) if len(self.vols) >= 5 else None

        def share(a, i):
            v = a[i] + a[i + 1]
            return (a[i] - a[i + 1]) / v if v > 0 else 0.0

        sh5 = {rr: share(acc[rr], 0) for rr in acc}
        sh1 = {rr: share(acc[rr], 2) for rr in acc}
        # candidate strength: |5-min share|, only if the last minute does not point the other way
        cand = {}
        for rr in ("CE", "PE"):
            sg = 1 if sh5[rr] >= 0 else -1
            if sh1[rr] * sg >= -0.05:
                cand[(rr, sg)] = abs(sh5[rr])
        best = max(cand, key=cand.get) if cand else None
        best_v = cand.get(best, 0.0)

        thin = tot5 <= 0 or (med is not None and tot5 < THIN_FRAC * med)
        held = self.state
        age = 1e9 if self.since is None else now - self.since
        new = held
        if held is None:
            new = "THIN" if thin else (best if best_v >= ENTER else "MIXED")
        elif thin:
            if held != "THIN" and age >= MIN_HOLD:
                new = "THIN"
        elif isinstance(held, tuple):
            rr, sg = held
            hv = sg * sh5[rr]                       # held side's share in the held direction (may be < 0)
            if age >= MIN_HOLD and hv < STAY:
                new = best if best_v >= ENTER else "MIXED"
            elif age >= DWELL and best is not None and best != held and best_v >= ENTER and best_v >= hv + SWITCH:
                new = best
        elif age >= MIN_HOLD:                       # MIXED / THIN
            new = best if best_v >= ENTER else "MIXED"
        if new != held:
            self.state, self.since = new, now
        st = self.state

        ce_t, pe_t = acc["CE"][0] + acc["CE"][1], acc["PE"][0] + acc["PE"][1]
        txt = (f"5m CE buy {acc['CE'][0]:,.0f} / sell {acc['CE'][1]:,.0f} ({sh5['CE'] * 100:+.0f} %), "
               f"PE buy {acc['PE'][0]:,.0f} / sell {acc['PE'][1]:,.0f} ({sh5['PE'] * 100:+.0f} %); "
               f"1m CE {sh1['CE'] * 100:+.0f} %, PE {sh1['PE'] * 100:+.0f} %")
        if isinstance(st, tuple):
            rr, sg = st
            val = sh5[rr] * 100
            label = _LABEL[st]
            side = rr if sg > 0 else None
            alert = False
            if (sg > 0 and sh5[rr] >= ALERT_SHARE and sh1[rr] >= ALERT_SHARE and med is not None
                    and tot5 >= ALERT_VOL * med and now - self.last_alert >= ALERT_GAP):
                self.last_alert = now
                alert = True
            plan = (f"{rr} buyers lifting offers {val:+.0f} % (1m {sh1[rr] * 100:+.0f} %) -- watch only"
                    if sg > 0 else f"{rr} being sold into bids {val:+.0f} % -- no buy signal")
            return {"state": label, "side": side, "value": val, "unit": "% net buy", "text": txt, "plan": plan,
                    "alert": alert}
        lead = "CE" if abs(sh5["CE"]) * ce_t >= abs(sh5["PE"]) * pe_t else "PE"
        if st == "THIN":
            vs = f"{tot5 / med * 100:.0f} % of the day's median" if med else "no volume"
            return {"state": "THIN", "value": sh5[lead] * 100, "unit": "% net buy",
                    "text": f"5m ATM+-2 volume {tot5:,.0f} ({vs}); " + txt}
        return {"state": "MIXED", "value": sh5[lead] * 100, "unit": "% net buy", "text": txt}
