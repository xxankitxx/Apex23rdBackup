"""lab1: the 1-minute lab on the broker history (D:/ClaudeCodeImproved/mythos/data/history/history.db, read-only).
988 sessions of Nifty futures, 139+ sessions of real weekly option bars (ATM +- 4 strikes). The champion's exit ladder
walked on 1-minute bars; where option bars are missing, a Black-76 model option (IV = VIX x a factor fitted on the
real-option days). A Day here can also be built from a fastlab session, to check what 1-minute bars lose."""
import os, sys, sqlite3, datetime as dt
sys.path.insert(0, r"D:\ApexOptions")
import numpy as np, pandas as pd
from apex import fastlab as FL

DB = "file:D:/ClaudeCodeImproved/mythos/data/history/history.db?mode=ro"
W = r"D:\ApexOptions\data\research\14nov\work\h1"
NB = 375                                   # 09:15 .. 15:29
HALF = 0.0011                              # half the recorded median spread (0.22 % of premium)
B_FLAT = 365                               # 15:20
IVK = {0: 1.9, 1: 1.08}
IVK_FAR = 0.93


def _grid(day):
    t0 = pd.Timestamp(day + " 09:15:00")
    return pd.date_range(t0, periods=NB, freq="1min")


def build_cache():
    os.makedirs(W, exist_ok=True)
    con = sqlite3.connect(DB, uri=True)
    f = pd.read_sql_query("select expiry, ts, o, h, l, c, v from bars where kind='fut' and interval='1minute'", con)
    f["day"] = f.ts.str[:10]
    near = f.groupby("day").expiry.min().rename("near")           # the nearest contract of the day
    f = f.join(near, on="day")
    f = f[f.expiry == f.near].drop(columns=["near"])
    f.to_parquet(os.path.join(W, "fut.parquet"))
    o = pd.read_sql_query("select expiry, strike, right, ts, o, h, l, c, v, oi from bars where kind='opt' and interval='1minute'", con)
    o["day"] = o.ts.str[:10]
    o.to_parquet(os.path.join(W, "opt.parquet"))
    s = pd.read_sql_query("select ts, c from bars where kind='spot' and interval='1minute'", con)
    s["day"] = s.ts.str[:10]
    s.to_parquet(os.path.join(W, "spot.parquet"))
    con.close()
    return len(f), len(o)


_C = {}


def _tab(name):
    if name not in _C:
        _C[name] = pd.read_parquet(os.path.join(W, name + ".parquet"))
    return _C[name]


def sessions():
    f = _tab("fut")
    n = f.groupby("day").size()
    return sorted(n[n >= 300].index)


def expiry_map(days):
    """weekly expiry per session: from the option bars where we have them; else Thursday (to Aug 2025) or Tuesday
    (from Sep 2025), moved back to the last session on or before it."""
    o = _tab("opt")
    known = o.groupby("day").expiry.min().to_dict()
    dset = [dt.date.fromisoformat(d) for d in days]
    sset = set(dset)
    out = {}
    for d in dset:
        k = d.isoformat()
        if k in known:
            out[k] = known[k]
            continue
        wd = 3 if d < dt.date(2025, 9, 1) else 1
        e = d + dt.timedelta(days=(wd - d.weekday()) % 7)
        if e <= dset[-1]:
            while e not in sset and e > d:
                e -= dt.timedelta(days=1)
            if e not in sset:
                e = d
        out[k] = e.isoformat()
    return out


def dte_map(days, exp):
    idx = {d: i for i, d in enumerate(days)}
    out = {}
    for d in days:
        e = exp[d]
        out[d] = (idx[e] - idx[d]) if e in idx else int(np.busday_count(d, e))
    return out


class Day(dict):
    __getattr__ = dict.__getitem__


def load_day(day, exp=None, dte=None, vix=None, with_opt=True):
    f = _tab("fut")
    g = f[f.day == day].drop_duplicates("ts").set_index("ts")
    grid = _grid(day).strftime("%Y-%m-%d %H:%M:%S")
    g = g.reindex(grid)
    c = g.c.ffill().bfill().to_numpy(float)
    o_ = g.o.fillna(pd.Series(c, index=grid)).to_numpy(float)
    h = g.h.fillna(pd.Series(c, index=grid)).to_numpy(float)
    l = g.l.fillna(pd.Series(c, index=grid)).to_numpy(float)
    D = Day(day=day, o=o_, h=h, l=l, c=c, v=g.v.fillna(0).to_numpy(float), expiry=exp, dte=dte, dte0=(dte == 0), vix=vix, opt=None, basis=0.0)
    D["T"] = np.maximum((pd.Timestamp((exp or day) + " 15:30:00") - _grid(day)).total_seconds().to_numpy() - 60.0, 60.0) / FL.YEAR_S
    if with_opt:
        ot = _tab("opt")
        q = ot[ot.day == day]
        if len(q):
            ex = q.expiry.min()
            q = q[q.expiry == ex]
            opt = {}
            for (k, r), x in q.groupby(["strike", "right"]):
                x = x.drop_duplicates("ts").set_index("ts").reindex(grid)
                opt[(float(k), "CE" if r == "call" else "PE")] = np.stack([x.o.to_numpy(float), x.h.to_numpy(float), x.l.to_numpy(float), x.c.ffill().to_numpy(float)], 1)
            D["opt"] = opt
            # futures minus the parity forward (the near future carries a basis the weekly options do not)
            sp = _tab("spot"); s = sp[sp.day == day].drop_duplicates("ts").set_index("ts").c.reindex(grid).ffill().bfill().to_numpy(float)
            D["basis"] = float(np.nanmedian(c - s)) if np.isfinite(s).any() else 0.0
    return D


def from_fastlab(day):
    """the same Day built from a recorded per-second session (1-minute bars of the mids): what do the bars lose?"""
    F = FL.load_day(day)
    fw = FL._ffill0(F["fwd"])
    def bars(x):
        x = x[:NB * 60].reshape(NB, 60)
        with np.errstate(all="ignore"):
            return x[:, 0], np.nanmax(x, 1), np.nanmin(x, 1), x[:, -1]
    o_, h, l, c = bars(fw)
    c = FL._ffill0(c); o_ = np.where(np.isfinite(o_), o_, c); h = np.where(np.isfinite(h), h, c); l = np.where(np.isfinite(l), l, c)
    opt = {}
    for j, k in enumerate(F["K"]):
        for ci, rr in ((0, "CE"), (1, "PE")):
            mid = 0.5 * (F["opt"][:, j, ci, 0] + F["opt"][:, j, ci, 1]).astype(float)
            bo, bh, bl, bc = bars(FL._ffill0(mid))
            if np.isfinite(bc).sum() > 100:
                opt[(float(k), rr)] = np.stack([bo, bh, bl, FL._ffill0(bc)], 1)
    from apex.engine.council.thr_d1 import days_to_expiry
    dte = days_to_expiry(day, F["expiry"])
    D = Day(day=day, o=o_, h=h, l=l, c=c, v=np.zeros(NB), expiry=F["expiry"], dte=dte, dte0=(dte == 0), vix=None, opt=opt, basis=0.0)
    D["T"] = np.maximum((pd.Timestamp(F["expiry"] + " 15:30:00") - _grid(day)).total_seconds().to_numpy() - 60.0, 60.0) / FL.YEAR_S
    return D


# ── the ladder on 1-minute bars ─────────────────────────────────────────────────────────────────────────────────────
def _pick_real(D, b, side):
    """strike just in the money of the forward (|delta| >= 0.52 on a normal day), one deeper on expiry day if too thin."""
    F = D["c"][b] - D["basis"]
    ks = sorted({k for (k, r) in D["opt"] if r == side})
    if not ks:
        return None
    if side == "CE":
        cand = [k for k in ks if k <= F - 3.0]
        cand = cand[::-1]
    else:
        cand = [k for k in ks if k >= F + 3.0]
    if not cand:
        return None
    k = cand[0]
    if D["dte0"] and len(cand) > 1 and abs(F - k) < 25.0:          # expiry: the champion wants |delta| about 0.65
        k = cand[1]
    return k


def ladder(D, b, side, sl=0.15, trail=None, hold=None, floor=None, stall=None, tp=None, model=None):
    """decision at the close of bar b, fill at the open of bar b+1 (+ half spread). model=None: real option bars when
    the session has them, else the model option; True forces the model."""
    e0 = b + 1
    if e0 >= B_FLAT - 1:
        return None
    x0 = D["dte0"]
    trail = (25.0 if x0 else 40.0) if trail is None else trail
    hold = (15 if x0 else 90) if hold is None else hold
    floor = ("pex" if x0 else "ramp") if floor is None else floor
    call = side == "CE"
    sg = 1.0 if call else -1.0
    use_model = (D["opt"] is None) if model is None else model
    c, h, l, o_ = D["c"], D["h"], D["l"], D["o"]
    if use_model:
        if D["vix"] is None:
            return None
        iv = max(0.05, D["vix"] / 100.0 * IVK.get(D["dte"], IVK_FAR))
        F0 = o_[e0] - D["basis"]
        Ks = (np.floor(F0 / 50.0) * 50.0 + 50.0 * np.arange(-4, 5)).astype(float)
        dl, _, _ = FL.greeks(F0, Ks, D["T"][e0], iv, call)
        ad = np.abs(dl); ok = ad >= 0.52
        if not ok.any():
            return None
        K = float(Ks[int(np.argmin(np.where(ok, np.abs(ad - (0.65 if x0 else 0.52)), 9.0)))])
        P = lambda F, i: float(FL.b76(F - D["basis"], K, D["T"][i], iv, call))
        po = lambda i: P(o_[i], i); pc = lambda i: P(c[i], i)
        plo = lambda i: P(l[i] if call else h[i], i); phi = lambda i: P(h[i] if call else l[i], i)
    else:
        K = _pick_real(D, b, side)
        if K is None:
            return None
        A = D["opt"][(K, side)]
        if not np.isfinite(A[e0, 0]) and not np.isfinite(A[e0, 3]):
            return None
        po = lambda i: A[i, 0] if np.isfinite(A[i, 0]) else A[i, 3]
        pc = lambda i: A[i, 3]
        plo = lambda i: A[i, 2] if np.isfinite(A[i, 2]) else A[i, 3]
        phi = lambda i: A[i, 1] if np.isfinite(A[i, 1]) else A[i, 3]
    e = po(e0) * (1 + HALF)
    if not (e > 1.0):
        return None
    best = sg * c[b]; pk = e
    last = min(B_FLAT, e0 + hold)
    why = "FLAT" if last >= B_FLAT else "TIME"
    xp = None; kx = last
    for i in range(e0, last + 1):
        lo_, hi_, cl = plo(i), phi(i), pc(i)
        opn = po(i)
        g = pk / e - 1.0
        fl = float(FL._floor(e, np.array(g), floor))
        if lo_ <= e * (1 - sl):
            xp, why, kx = min(e * (1 - sl), opn) if i > e0 else e * (1 - sl), "SL", i; break
        if fl == fl and lo_ <= fl:
            xp, why, kx = min(fl, opn) if i > e0 else fl, "FLOOR", i; break
        pk = max(pk, hi_)
        if tp is not None and hi_ >= e * (1 + tp):
            xp, why, kx = e * (1 + tp), "TP", i; break
        best = max(best, sg * c[i])
        if best - sg * c[i] >= trail:
            xp, why, kx = cl, "TRAIL", i; break
        g = pk / e - 1.0
        if stall is not None and i - e0 + 1 >= stall[0] and g < stall[1] and abs(cl / e - 1) < stall[2]:
            xp, why, kx = cl, "STALL", i; break
        if i == last:
            xp = cl
    if xp is None or not (xp == xp):
        return None
    xp *= (1 - HALF)
    return dict(day=D["day"], b_in=e0, b_out=kx, side=side, K=K, e=e, ret=100.0 * (xp / e - 1.0), why=why, peak=100.0 * (pk / e - 1.0), dte=D["dte"], model=use_model)


def run(D, sigs, cool=1, **kw):
    out = []; free = 1
    t1 = 325 if D["dte0"] else 345
    for b, side, tag in sorted(sigs):
        if b < free or b < 1 or b >= t1:
            continue
        t = ladder(D, b, side, **kw)
        if t is None:
            continue
        t["tag"] = tag
        out.append(t)
        free = t["b_out"] + cool
    return out


# ── entries on 1-minute bars ────────────────────────────────────────────────────────────────────────────────────────
def sig_pb(D, W=20, vmin=40.0, pb=0.5, dmax=0.75, amax=15, rs=5.0, scale=None):
    """the champion's normal-day entry on 1-minute closes. scale: multiply the point thresholds by price / scale."""
    c = D["c"]
    k = (c[0] / scale) if scale else 1.0
    vmin_, rs_ = vmin * k, rs * k
    out = []; arm = None
    for b in range(W + 1, NB):
        f = c[b]
        hi = c[b - W:b].max(); lo = c[b - W:b].min()
        v = f - c[b - W]
        side = "CE" if (f > hi and v >= vmin_) else ("PE" if (f < lo and -v >= vmin_) else None)
        if side:
            if arm is None or arm[0] != side:
                arm = [side, c[b - W], f, f, b]
            else:
                arm[2] = max(arm[2], f) if side == "CE" else min(arm[2], f)
                arm[3] = arm[2]
        elif arm is not None:
            if b - arm[4] > amax:
                arm = None
                continue
            up = arm[0] == "CE"
            arm[2] = max(arm[2], f) if up else min(arm[2], f)
            arm[3] = min(arm[3], f) if up else max(arm[3], f)
            imp = abs(arm[2] - arm[1]); ret = (arm[2] - arm[3]) if up else (arm[3] - arm[2])
            if imp > 0 and ret >= pb * imp:
                if ret > dmax * imp:
                    arm = None
                elif ((f - arm[3]) if up else (arm[3] - f)) >= rs_:
                    out.append((b, arm[0], "pb")); arm = None
    return out


def sig_brk(D, W=10, L=3, vmin=20.0, gap=5, scale=None):
    """the champion's expiry-day entry on 1-minute closes: a new W-bar extreme with vmin points in L bars."""
    c = D["c"]
    k = (c[0] / scale) if scale else 1.0
    out = []; last = {"CE": -99, "PE": -99}
    for b in range(W + 1, NB):
        f = c[b]; v = f - c[b - L]
        side = "CE" if (f > c[b - W:b].max() and v >= vmin * k) else ("PE" if (f < c[b - W:b].min() and -v >= vmin * k) else None)
        if side and b - last[side] >= gap:
            out.append((b, side, "brk")); last[side] = b
    return out


def sig_pb_hl(D, W=20, vmin=40.0, pb=0.5, dmax=0.75, amax=15, rs=5.0, scale=None):
    """the same idea read from each bar's HIGH and LOW (closer to the per-second pattern): a bar whose high takes out
    the prior W-bar high with vmin points over W bars arms; lows mark the pullback; a close rs points off the pullback
    low fires. Everything is known at the close of the firing bar."""
    c, h, l = D["c"], D["h"], D["l"]
    k = (c[0] / scale) if scale else 1.0
    vmin_, rs_ = vmin * k, rs * k
    out = []; arm = None
    for b in range(W + 1, NB):
        hiW = h[b - W:b].max(); loW = l[b - W:b].min()
        up = h[b] > hiW and h[b] - c[b - W] >= vmin_
        dn = l[b] < loW and c[b - W] - l[b] >= vmin_
        side = "CE" if (up and not dn) else ("PE" if (dn and not up) else None)
        if side:
            x = h[b] if side == "CE" else l[b]
            if arm is None or arm[0] != side:
                arm = [side, c[b - W], x, x, b]
            else:
                arm[2] = max(arm[2], x) if side == "CE" else min(arm[2], x)
                arm[3] = arm[2]
            # the rest of the same bar may already be the pullback: the close is after the extreme
            arm[3] = min(arm[3], c[b]) if side == "CE" else max(arm[3], c[b])
            continue
        if arm is None:
            continue
        if b - arm[4] > amax:
            arm = None
            continue
        u = arm[0] == "CE"
        arm[3] = min(arm[3], l[b]) if u else max(arm[3], h[b])
        imp = abs(arm[2] - arm[1]); ret = (arm[2] - arm[3]) if u else (arm[3] - arm[2])
        if imp > 0 and ret >= pb * imp:
            if ret > dmax * imp:
                arm = None
            elif ((c[b] - arm[3]) if u else (arm[3] - c[b])) >= rs_:
                out.append((b, arm[0], "pbhl")); arm = None
    return out
