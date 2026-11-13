import sys; sys.path.insert(0, r"D:\ApexOptions\data\research\13nov"); import lowprio
"""R01 Phase B (also runnable now on at most 3 day parts): a per-second replica of the c20 NORMAL-day entry on the
futures mid (proxy for the parity forward, same 5-s EMA), with a log of every arm and why it ended, and three
complementary entry families for the day shapes c20 cannot trade, all scored with the SAME exits (c20_9x normal day:
-15 % premium stop, 40-pt forward trail, ramp floors, 90-min clock, forced flat 15:20), one position per family,
fills at the ask 1 s after the signal and exits at the bid 1 s after.

    py -3.13 phaseB_c20_complements.py 2026-11-05 2026-10-30 2026-11-02      (now: at most 3 single-part days)
    py -3.13 phaseB_c20_complements.py ALL                                  (after 15:30: every normal day in ds_v2)

Families (every rule reads rows <= i only):
  C20   the replica: 20-min new extreme with >= 40 pts in 20 min arms; 50-75 % retrace within 900 s of the first arm;
        buy a 5-pt resumption.
  FLAG  strong-trend continuation: an arm whose impulse is efficient (|net| / path of the 1-min samples over the
        last 20 min >= FLAG_ER) and whose retrace stays between FLAG_LO and 50 % (shallow) -> buy when fs makes a
        NEW extreme beyond the impulse extreme (the pause ended). Arm age <= 900 s.
  GRIND slow trend: 60-min net move >= GR_NET pts with 60-min efficiency >= GR_ER while the 20-min move is < 40 (c20
        cannot arm) -> buy a new 20-min extreme in the 60-min direction. At most one entry per GR_GAP s.
  REV   failed impulse: when a c20 arm is dropped for retracing > 75 % and fs then crosses the impulse BASE within
        REV_WIN s -> buy the opposite side (a V turn that c20 throws away).
Outputs work/R01/phaseB_c20_complements_<tag>.json and prints per-day tables.
"""
import glob, json, os, time
import numpy as np

DS = r"D:\ApexOptions\data\research\ds_v2"
OUT = r"D:\ApexOptions\data\research\13nov\work\R01"
IST = 19800
P = dict(tau=5.0, W=1200, L=1200, vmin=40.0, pb=0.5, dmax=0.75, amax=900, rs=5.0, cool=60,
         sl=0.15, trail=40.0, hold=5400, R_ARM=0.15, R0=0.25, R1=0.50, K0=0.45, K1=0.70,
         FLAG_ER=0.55, FLAG_LO=0.15, GR_NET=50.0, GR_ER=0.5, GR_GAP=1800, REV_WIN=900)


def load_day(day):
    parts = sorted(glob.glob(os.path.join(DS, day + "*.npz")))
    T, F, K, Q = [], [], None, []
    allk = set()
    zs = []
    for p in parts:
        z = np.load(p, allow_pickle=False)
        if len(z["t"]) == 0:
            continue
        zs.append(z)
        allk |= set(int(k) for k in z["strikes"])
    if not zs:
        return None
    K = np.array(sorted(allk))
    kix = {k: i for i, k in enumerate(K)}
    for z in zs:
        t = z["t"]
        f = z["fut"]
        mid = np.where((f[:, 0] > 0) & (f[:, 1] >= f[:, 0]) & (f[:, 1] - f[:, 0] < 30), (f[:, 0] + f[:, 1]) / 2, f[:, 2])
        o = z["opt"]
        q = np.full((len(t), len(K), 2, 2), np.nan, np.float32)
        for j, k in enumerate(z["strikes"]):
            q[:, kix[int(k)]] = o[:, j]
        T.append(t); F.append(mid); Q.append(q)
    t = np.concatenate(T); f = np.concatenate(F); q = np.concatenate(Q)
    exp = str(zs[0]["expiry"])
    # one row per second 09:15:00 .. 15:30:00, forward-filled
    d0 = int(np.floor((t[0] + IST) / 86400) * 86400 - IST)
    t_open = d0 + 9 * 3600 + 15 * 60
    N = 6 * 3600 + 15 * 60 + 1
    idx = np.searchsorted(t, t_open + np.arange(N), side="right") - 1
    ok = idx >= 0
    fut = np.full(N, np.nan); fut[ok] = f[idx[ok]]
    opt = np.full((N, len(K), 2, 2), np.nan, np.float32); opt[ok] = q[idx[ok]]
    return dict(day=day, expiry=exp, t_open=t_open, fut=fut, opt=opt, K=K)


def ema(x, tau):
    out = np.full(len(x), np.nan)
    a = 1.0 / tau
    prev = np.nan
    for i, v in enumerate(x):
        if not np.isfinite(v):
            out[i] = prev
            continue
        prev = v if not np.isfinite(prev) else prev + a * (v - prev)
        out[i] = prev
    return out


def roll_max_min(fs, W):
    """max / min of fs over rows i-W .. i-1 (the current row excluded)."""
    from collections import deque
    N = len(fs)
    hi = np.full(N, np.nan); lo = np.full(N, np.nan)
    qa, qi = deque(), deque()
    for i in range(N):
        if i > 0 and np.isfinite(fs[i - 1]):
            x = fs[i - 1]
            while qa and qa[-1][1] <= x:
                qa.pop()
            qa.append((i - 1, x))
            while qi and qi[-1][1] >= x:
                qi.pop()
            qi.append((i - 1, x))
        while qa and qa[0][0] < i - W:
            qa.popleft()
        while qi and qi[0][0] < i - W:
            qi.popleft()
        if qa:
            hi[i], lo[i] = qa[0][1], qi[0][1]
    return hi, lo


def eff(fs, i, W, step=60):
    if i < W:
        return np.nan
    seg = fs[i - W:i + 1:step]
    seg = seg[np.isfinite(seg)]
    if len(seg) < 4:
        return np.nan
    p = np.sum(np.abs(np.diff(seg)))
    return abs(seg[-1] - seg[0]) / p if p > 0 else np.nan


class Kit:
    """one position, c20_9x normal-day exits on the option bid and the smoothed futures."""

    def __init__(self, D, fs):
        self.D, self.fs = D, fs
        self.pos = None
        self.trades = []
        self.last_exit = -10 ** 9

    def strike(self, i, side):
        f = self.D["fut"][i]
        k = np.floor(f / 50) * 50 if side == "CE" else np.ceil(f / 50) * 50
        K = self.D["K"]
        j = int(np.argmin(np.abs(K - k)))
        return j if abs(K[j] - k) < 1 else None

    def buy(self, i, side, why):
        if self.pos is not None or i - self.last_exit < P["cool"]:
            return False
        j = self.strike(i, side)
        if j is None or i + 1 >= len(self.fs):
            return False
        c = 0 if side == "CE" else 1
        ask = self.D["opt"][i + 1, j, c, 1]
        if not (np.isfinite(ask) and ask > 0):
            return False
        self.pos = dict(i=i, side=side, j=j, c=c, entry=float(ask), best=self.fs[i], pk=float(ask), why=why)
        return True

    def floor(self, e, g):
        if g < P["R_ARM"]:
            return None
        if g < P["R0"]:
            return e
        if g < P["R1"]:
            u = (g - P["R0"]) / (P["R1"] - P["R0"])
            return e * (1 + max(0.0, g * (P["K0"] + (P["K1"] - P["K0"]) * u)))
        return e * (1 + P["K1"] * g)

    def step(self, i, flat_i):
        p = self.pos
        if p is None:
            return
        fs = self.fs[i]
        ce = p["side"] == "CE"
        p["best"] = max(p["best"], fs) if ce else min(p["best"], fs)
        bid = self.D["opt"][i, p["j"], p["c"], 0]
        if np.isfinite(bid):
            p["pk"] = max(p["pk"], float(bid))
        e = p["entry"]
        why = None
        if i >= flat_i:
            why = "FLAT"
        elif np.isfinite(bid) and bid <= e * (1 - P["sl"]):
            why = "SL"
        else:
            fl = self.floor(e, p["pk"] / e - 1)
            if fl is not None and np.isfinite(bid) and bid <= fl:
                why = "FLOOR"
            elif ((p["best"] - fs) if ce else (fs - p["best"])) >= P["trail"]:
                why = "TRAIL"
            elif i - p["i"] >= P["hold"]:
                why = "TIME"
        if why:
            k = min(i + 1, len(self.fs) - 1)
            xb = self.D["opt"][k, p["j"], p["c"], 0]
            if not np.isfinite(xb):
                xb = bid
            r = float(xb) / e - 1
            hm = lambda x: f"{(555 + x // 60) // 60:02d}:{(555 + x // 60) % 60:02d}"      # noqa: E731
            self.trades.append(dict(t_in=hm(p["i"]), t_out=hm(i), side=p["side"], K=int(self.D["K"][p["j"]]),
                                    ret=round(100 * r, 2), why=p["why"], exit=why, peak=round(100 * (p["pk"] / e - 1), 1)))
            self.pos = None
            self.last_exit = i


def run_day(D):
    fut = D["fut"]
    fs = ema(fut, P["tau"])
    hi, lo = roll_max_min(fs, P["W"])
    N = len(fs)
    t0, t1, flat = 60, 345 * 60, 365 * 60          # 09:16, 15:00, 15:20 in rows since 09:15
    kits = {k: Kit(D, fs) for k in ("C20", "FLAG", "GRIND", "REV")}
    arm = None          # [side, base, ext, pbx, armed_at, max_retrace_frac]
    arms = []
    flag = None         # [side, base, ext, pbx, armed_at]
    rev = None          # (side_to_buy, base_level, until_i)
    last_grind = -10 ** 9
    for i in range(N):
        for k in kits.values():
            k.step(i, flat)
        f = fs[i]
        if not np.isfinite(f) or i < P["W"] + 2 or not np.isfinite(fs[i - P["L"]]):
            continue
        v = f - fs[i - P["L"]]
        side = None
        if np.isfinite(hi[i]) and f > hi[i] and v >= P["vmin"]:
            side = "CE"
        elif np.isfinite(lo[i]) and f < lo[i] and -v >= P["vmin"]:
            side = "PE"
        inwin = t0 <= i < t1
        # ---- the c20 replica arm: as in c20_08.on_second, the state machine only runs while flat, inside the
        #      entry window and past the 60-s cooldown (c20_08.py:129-130) ----
        fire = None
        c20_on = inwin and kits["C20"].pos is None and i - kits["C20"].last_exit >= P["cool"]
        if not c20_on:
            pass
        elif side is not None:
            if arm is None or arm[0] != side:
                if arm is not None:
                    arms.append(dict(arm_i=arm[4], end_i=i, side=arm[0], imp=round(abs(arm[2] - arm[1]), 1),
                                     maxret=round(arm[5], 2), end="other side armed"))
                arm = [side, fs[i - P["L"]], f, f, i, 0.0]
            else:
                arm[2] = max(arm[2], f) if side == "CE" else min(arm[2], f)
                arm[3] = arm[2]
        elif arm is not None:
            if i - arm[4] > P["amax"]:
                arms.append(dict(arm_i=arm[4], end_i=i, side=arm[0], imp=round(abs(arm[2] - arm[1]), 1),
                                 maxret=round(arm[5], 2), end="aged out (no 50 % pullback in 15 min)"))
                arm = None
            else:
                up = arm[0] == "CE"
                arm[2] = max(arm[2], f) if up else min(arm[2], f)
                arm[3] = min(arm[3], f) if up else max(arm[3], f)
                imp = abs(arm[2] - arm[1])
                ret = (arm[2] - arm[3]) if up else (arm[3] - arm[2])
                arm[5] = max(arm[5], ret / imp if imp > 0 else 0.0)
                if imp > 0 and ret >= P["pb"] * imp:
                    if ret > P["dmax"] * imp:
                        arms.append(dict(arm_i=arm[4], end_i=i, side=arm[0], imp=round(imp, 1), maxret=round(arm[5], 2),
                                         end="retrace > 75 % (reversal)"))
                        rev = ("PE" if up else "CE", arm[1], i + P["REV_WIN"])
                        arm = None
                    elif ((f - arm[3]) if up else (arm[3] - f)) >= P["rs"]:
                        arms.append(dict(arm_i=arm[4], end_i=i, side=arm[0], imp=round(imp, 1), maxret=round(arm[5], 2),
                                         end="FIRED (5-pt resumption)"))
                        fire = arm[0]
                        arm = None
        if fire and inwin:
            kits["C20"].buy(i, fire, "c20 pb")
        # ---- FLAG: efficient impulse, shallow pause, new extreme ----
        if side is not None:
            if flag is None or flag[0] != side:
                flag = [side, fs[i - P["L"]], f, f, i]
            else:
                # a new extreme after a shallow pause = the FLAG trigger (before the extreme is pushed)
                up = side == "CE"
                imp = abs(flag[2] - flag[1]); ret = (flag[2] - flag[3]) if up else (flag[3] - flag[2])
                if inwin and imp > 0 and P["FLAG_LO"] * imp <= ret < P["pb"] * imp and i - flag[4] <= P["amax"] \
                        and ((f > flag[2]) if up else (f < flag[2])):
                    e_ = eff(fs, i, P["W"])
                    if np.isfinite(e_) and e_ >= P["FLAG_ER"]:
                        kits["FLAG"].buy(i, side, f"flag ret {ret / imp:.2f} er {e_:.2f}")
                flag[2] = max(flag[2], f) if up else min(flag[2], f)
                flag[3] = flag[2]
        elif flag is not None:
            if i - flag[4] > P["amax"]:
                flag = None
            else:
                up = flag[0] == "CE"
                flag[3] = min(flag[3], f) if up else max(flag[3], f)
                imp = abs(flag[2] - flag[1]); ret = (flag[2] - flag[3]) if up else (flag[3] - flag[2])
                if imp > 0 and ret >= P["pb"] * imp:
                    flag = None                       # deep pullback: c20's territory
        # ---- GRIND: 60-min trend that never makes 40 pts in 20 min ----
        if inwin and i >= 3600 and np.isfinite(fs[i - 3600]) and abs(v) < P["vmin"] and i - last_grind >= P["GR_GAP"]:
            net60 = f - fs[i - 3600]
            e60 = eff(fs, i, 3600)
            if abs(net60) >= P["GR_NET"] and np.isfinite(e60) and e60 >= P["GR_ER"]:
                sd = "CE" if net60 > 0 else "PE"
                if (sd == "CE" and np.isfinite(hi[i]) and f > hi[i]) or (sd == "PE" and np.isfinite(lo[i]) and f < lo[i]):
                    if kits["GRIND"].buy(i, sd, f"grind net60 {net60:+.0f} er {e60:.2f}"):
                        last_grind = i
        # ---- REV: the impulse c20 dropped as a reversal breaks its own base ----
        if rev is not None:
            sd, base, until = rev
            if i > until:
                rev = None
            elif inwin and ((sd == "PE" and f < base) or (sd == "CE" and f > base)):
                kits["REV"].buy(i, sd, "rev through impulse base")
                rev = None
    hm = lambda x: f"{(555 + x // 60) // 60:02d}:{(555 + x // 60) % 60:02d}"      # noqa: E731
    for a in arms:
        a["arm"], a["end_t"] = hm(a.pop("arm_i")), hm(a.pop("end_i"))
    # the day's shape, for the record
    ok = np.isfinite(fs)
    f0 = fs[ok][0]; f1 = fs[ok][-1]
    shape = dict(open=round(float(f0), 1), close=round(float(f1), 1), hi=round(float(np.nanmax(fs)), 1),
                 lo=round(float(np.nanmin(fs)), 1), er_day=round(float(eff(fs, N - 1, N - 61)), 2))
    return dict(day=D["day"], expiry=D["expiry"], shape=shape, arms=arms,
                trades={k: v.trades for k, v in kits.items()})


def main(argv):
    days = argv[1:] or []
    if days == ["ALL"]:
        names = sorted({os.path.basename(p)[:10] for p in glob.glob(os.path.join(DS, "*.npz"))})
        days = names
    if len(days) > 3 and argv[1:] != ["ALL"]:
        print("at most 3 day parts while the market is open"); return
    out = []
    t0 = time.time()
    for day in days:
        D = load_day(day)
        if D is None:
            print(day, "no rows"); continue
        if D["expiry"] == day:
            print(day, "expiry day: c20 uses the breakout mode there; skipped"); continue
        r = run_day(D)
        out.append(r)
        print(f"\n=== {day}  shape {r['shape']}  ({time.time() - t0:.0f} s)", flush=True)
        n = {}
        for a in r["arms"]:
            n[a["end"]] = n.get(a["end"], 0) + 1
        print("c20 arms:", len(r["arms"]), n)
        for a in r["arms"]:
            print("   ", a)
        for k, tr in r["trades"].items():
            rets = [x["ret"] for x in tr]
            cmp = np.prod([1 + x / 100 for x in rets]) - 1 if rets else 0.0
            print(f"  {k:6s} trades {len(tr):2d} won {sum(1 for x in rets if x > 0):2d} compounded {100 * cmp:+.1f} %")
            for x in tr:
                print("      ", x)
    tag = "ALL" if argv[1:] == ["ALL"] else "_".join(d[5:] for d in days)
    with open(os.path.join(OUT, f"phaseB_c20_complements_{tag}.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    print("done", round(time.time() - t0, 1))


if __name__ == "__main__":
    main(sys.argv)
