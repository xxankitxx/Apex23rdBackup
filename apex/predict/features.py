"""Causal 1-second features for the prediction service (docs/41 section 3). ONE implementation: the offline builder
feeds it recorded seconds, the engine feeds it live seconds, so a forecast is made from the same numbers it was
trained on. A feature that cannot be measured is NaN, never a guess. Nothing later than the update's own second is read.

Directional features are SIGNED by the trade's direction d (+1 call, -1 put): "with the trade" is positive for both
rights, so one model serves both. Units: futures points, index points, per cent of premium, seconds."""
import datetime as _dt
import hashlib

import numpy as np

RING = 901                      # seconds of history kept
Q_FRESH_S = 3.0                 # index-future quote and option quote
HW_FRESH_S = 5.0                # stock cash price and stock-futures quote
COVER = 0.70                    # share of heavyweight weight that must be fresh at both ends of a window
WARM_S = 300                    # seconds of clean history before any feature set is called ready
GAP_S = 5                       # a hole up to this long does not restart the warm-up (a quiet second has no row);
                                # a window whose far end falls in a hole is simply not measured (NaN)

MARKET = ("mom5", "mom15", "mom30", "mom60", "mom180", "mom300", "br30", "brsf30", "cash30", "sfut30", "z30",
          "rngpos", "flow30", "flow120", "dimb", "dimb30", "rv60", "rv300", "fspread", "tod", "dte", "expd", "strad60",
          "strad300")
SIGNED = frozenset(("mom5", "mom15", "mom30", "mom60", "mom180", "mom300", "br30", "brsf30", "cash30", "sfut30",
                    "z30", "rngpos", "flow30", "flow120", "dimb", "dimb30"))
CONTRACT = ("prem", "spread_pct", "mny", "om10", "om30", "om60", "lag30", "opp30", "prem_strad")
NAMES = MARKET + CONTRACT
SCHEMA = hashlib.sha256(("|".join(NAMES) + f"|{RING}|{Q_FRESH_S}|{HW_FRESH_S}|{COVER}|{WARM_S}|{GAP_S}").encode()).hexdigest()[:12]
S01_B_CASH, S01_B_MOM = 0.4554, 0.4359          # as gen3 VERSION 1 (signal side only, docs/39 section 5.1)
_H900 = np.arange(0, 900)


class Features:
    """update() once per second with what was RECEIVED before that second; market() and contract() read it back."""

    def __init__(self):
        self.sec = np.full(RING, -1, np.int64)          # which second each ring slot holds
        self.mid = np.full(RING, np.nan)
        self.flow = np.zeros(RING)                      # signed traded quantity of the second / smoothed depth
        self.dimb = np.full(RING, np.nan)               # (bid depth - ask depth) / (bid depth + ask depth), top 5
        self._pf = None                                 # previous second's (bid, ask, ltp, cumulative volume)
        self._dep = None
        self.cash = None
        self.sfm = None
        self.om = None
        self.K = None
        self.w = None
        self.t = None
        self.n_clean = 0
        self.gaps = 0
        self.cur = {}
        self._m = None

    def _slot(self, sec):
        i = sec % RING
        return i if self.sec[i] == sec else None

    def update(self, t, fbid, fask, f_age, cash, cash_age, sf_bid, sf_ask, sf_age, w, K, bid, ask, age, dte, expd,
               tod_s, f_ltp=None, f_vol=None, bq=None, aq=None, d_age=None):
        """t: the second (epoch). cash / sf arrays per heavyweight; K strikes (fixed order for the day);
        bid / ask / age shaped (len(K), 2), right 0 = call, 1 = put. dte calendar days, tod_s seconds since 09:15."""
        sec = int(t)
        cash = np.asarray(cash, float)
        w = np.asarray(w, float)
        K = np.asarray(K, float)
        bid = np.asarray(bid, float)
        ask = np.asarray(ask, float)
        age = np.asarray(age, float)
        if self.cash is None or self.cash.shape[1] != len(cash) or self.om.shape[1] != len(K):
            self.cash = np.full((RING, len(cash)), np.nan)
            self.sfm = np.full((RING, len(cash)), np.nan)
            self.om = np.full((RING, len(K), 2), np.nan)
            self.sec[:] = -1
            self.n_clean = 0
        step = 1 if self.t is None else sec - self.t
        if step != 1:
            self.gaps += 1
            if step > GAP_S or step <= 0:
                self.n_clean = 0                        # a long hole (or time going back): the warm-up starts again
        self.t, self.K, self.w = sec, K, w
        f_ok = bool(fbid > 0 and fask >= fbid and f_age <= Q_FRESH_S)
        i = sec % RING
        self.sec[i] = sec
        self.mid[i] = 0.5 * (fbid + fask) if f_ok else np.nan
        with np.errstate(invalid="ignore"):
            c_ok = np.isfinite(cash) & (cash > 0) & (np.asarray(cash_age, float) <= HW_FRESH_S)
            sb, sa = np.asarray(sf_bid, float), np.asarray(sf_ask, float)
            s_ok = (sb > 0) & (sa >= sb) & (np.asarray(sf_age, float) <= HW_FRESH_S)
            o_ok = (bid > 0) & (ask > bid) & (age <= Q_FRESH_S)
        self.cash[i] = np.where(c_ok, cash, np.nan)
        self.sfm[i] = np.where(s_ok, 0.5 * (sb + sa), np.nan)
        self.om[i] = np.where(o_ok, 0.5 * (bid + ask), np.nan)
        self.n_clean = self.n_clean + max(1, min(step, GAP_S)) if f_ok else 0
        # signed flow: the second's traded quantity, signed by where the last price sat against the PREVIOUS quote
        x = 0.0
        dq_ok = bq is not None and aq is not None and bq > 0 and aq > 0 and (d_age is None or d_age <= Q_FRESH_S)
        if dq_ok:
            dd = 0.5 * (bq + aq)
            self._dep = dd if self._dep is None else 0.98851 * self._dep + 0.01149 * dd      # 60-s half life
        pf = self._pf
        if pf is not None and step == 1 and f_ltp is not None and f_vol is not None and self._dep:
            dq = f_vol - pf[3]
            if 0 < dq < 1e9:
                sg = 1 if f_ltp >= pf[1] else (-1 if f_ltp <= pf[0] else (1 if f_ltp > pf[2] else (-1 if f_ltp < pf[2] else 0)))
                x = sg * dq / self._dep
        self._pf = (fbid, fask, f_ltp, f_vol) if f_ltp is not None and f_vol is not None and f_ok else None
        self.flow[i] = x
        self.dimb[i] = (bq - aq) / (bq + aq) if dq_ok else np.nan
        self.cur = dict(i=i, f_ok=f_ok, fspread=(fask - fbid) if f_ok else np.nan, bid=bid, ask=ask, o_ok=o_ok,
                        dte=float(dte), expd=1.0 if expd else 0.0, tod=float(tod_s) / 22500.0)
        self._m = None

    def ready(self):
        return self.n_clean >= WARM_S

    def _basket(self, arr, i, j):
        """Weighted move of a basket from slot j (earlier) to slot i in index points, and its weighted breadth."""
        a, b = arr[i], arr[j]
        ok = np.isfinite(a) & np.isfinite(b) & np.isfinite(self.w)
        tot = self.w[np.isfinite(self.w)].sum()
        ws = self.w[ok].sum()
        if tot <= 0 or ws / tot < COVER:
            return np.nan, np.nan
        r = a[ok] / b[ok] - 1.0
        return float((self.w[ok] * r).sum() / ws) * self.mid[i], float((self.w[ok] * np.sign(r)).sum() / ws)

    def atm(self):
        m = self.mid[self.cur["i"]] if self.cur else np.nan
        return int(np.argmin(np.abs(self.K - m))) if np.isfinite(m) else None

    def _strad(self, i, j):
        k = self.atm()
        if k is None or j is None:
            return np.nan
        a, b = self.om[i, k].sum(), self.om[j, k].sum()        # NaN if either leg is missing
        return 100.0 * (a / b - 1.0) if np.isfinite(a) and np.isfinite(b) and b > 0 else np.nan

    def market(self):
        """The unsigned market features of this second (dict), or None before the warm-up or on a stale future."""
        if self._m is not None:
            return self._m
        c = self.cur
        if not c or not c["f_ok"] or not self.ready():
            return None
        i = c["i"]
        m = self.mid[i]
        out = {}
        for h in (5, 15, 30, 60, 180, 300):
            j = self._slot(self.t - h)
            out[f"mom{h}"] = m - self.mid[j] if j is not None else np.nan
        j30 = self._slot(self.t - 30)
        if j30 is not None:
            out["cash30"], out["br30"] = self._basket(self.cash, i, j30)
            out["sfut30"], out["brsf30"] = self._basket(self.sfm, i, j30)
        else:
            out["cash30"] = out["br30"] = out["sfut30"] = out["brsf30"] = np.nan
        out["z30"] = out["sfut30"] - S01_B_CASH * out["cash30"] - S01_B_MOM * out["mom30"]
        secs = self.t - _H900
        idx = secs % RING
        win = np.where(self.sec[idx] == secs, self.mid[idx], np.nan)         # newest first
        lo, hi = np.nanmin(win), np.nanmax(win)
        out["rngpos"] = (m - lo) / (hi - lo) - 0.5 if hi > lo else 0.0
        ok900 = self.sec[idx] == secs
        out["flow30"] = float(self.flow[idx[:30]][ok900[:30]].sum())
        out["flow120"] = float(self.flow[idx[:120]][ok900[:120]].sum())
        out["dimb"] = float(self.dimb[i])
        d30 = self.dimb[idx[:30]][ok900[:30]]
        out["dimb30"] = float(np.nanmean(d30)) if np.isfinite(d30).sum() >= 15 else np.nan
        d1 = np.diff(win[:301])
        f60, f300 = np.isfinite(d1[:60]), np.isfinite(d1)
        out["rv60"] = float(d1[:60][f60].std()) if f60.sum() >= 40 else np.nan
        out["rv300"] = float(d1[f300].std()) if f300.sum() >= 200 else np.nan
        out["fspread"], out["tod"], out["dte"], out["expd"] = c["fspread"], c["tod"], c["dte"], c["expd"]
        out["strad60"] = self._strad(i, self._slot(self.t - 60))
        out["strad300"] = self._strad(i, self._slot(self.t - 300))
        self._m = out
        return out

    def contract(self, k, rr):
        """Feature vector (order = NAMES) for strike index k and right rr (0 call, 1 put), or None when the market
        set is not ready or this contract has no fresh two-sided quote now."""
        mk = self.market()
        c = self.cur
        if mk is None or not c["o_ok"][k, rr]:
            return None
        d = 1.0 if rr == 0 else -1.0
        i = c["i"]
        m = self.mid[i]
        om = self.om[i, k, rr]
        x = [(d * mk[n] if n in SIGNED else mk[n]) for n in MARKET]
        ask, bid = c["ask"][k, rr], c["bid"][k, rr]

        def chg(h, r=rr):
            j = self._slot(self.t - h)
            p = self.om[j, k, r] if j is not None else np.nan
            return (self.om[i, k, r] - p) if np.isfinite(p) else np.nan
        o30 = chg(30)
        om_opp = self.om[i, k, 1 - rr]
        st = om + om_opp
        x += [ask, 100.0 * (ask - bid) / om, 100.0 * d * (m - self.K[k]) / m,
              100.0 * chg(10) / om, 100.0 * o30 / om, 100.0 * chg(60) / om,
              o30 - 0.5 * d * mk["mom30"],
              100.0 * chg(30, 1 - rr) / om_opp if np.isfinite(om_opp) and om_opp > 0 else np.nan,
              om / st if np.isfinite(st) and st > 0 else np.nan]
        return np.array(x, float)


def tod_seconds(t_epoch, ist_offset=19800):
    """Seconds since 09:15 IST."""
    return (int(t_epoch) + ist_offset) % 86400 - (9 * 3600 + 15 * 60)


def dte_days(day, expiry):
    """Calendar days from the trading day to the expiry (both 'YYYY-MM-DD')."""
    return (_dt.date.fromisoformat(expiry) - _dt.date.fromisoformat(day)).days
