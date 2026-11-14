"""The captured-data inputs over a year, one row per minute per session, every input known at that minute; and the
label: what a CALL and a PUT bought at that minute would have made with the champion's exits (per second, model
option on the session's own 1-second future; checked 0.98 against real quotes on the recorded sessions).

Inputs (all read from bars that have CLOSED by the decision second, 60 m + 59):
  future     moves over 1/5/15/30/60 min, position in the 20/60-min range and in the day, distance to VWAP and to
             the day's open, realised volatility 5/15/60 min (points), trend efficiency, the champion's own state
             (impulse armed, pullback depth) as numbers
  heavyweights  Nifty-weighted move 1/5/15 min (Nifty points), weighted breadth, banks against the rest, the
             basket's lead over the future
  sisters    BANKNIFTY and FINNIFTY futures moves 1/5/15 min in Nifty points, their lead over the future
  options    ATM implied volatility, its change 5/15 min, its level against the day's median; put-call skew at
             +-100 points; OI change 5/15 min of calls and puts within +-150 points of ATM (writers' flow); the
             biggest call OI above and put OI below (walls) and their distance; put-call OI ratio; option volume
             against the day's pace
  context    minute of the day, sessions to expiry, the gap, the 20-session realised volatility
    py -3.13 s44_wxfeat.py            builds data/research/hist_wx/feat/<day>.parquet for every downloaded session
"""
import os, sys, glob, json, pickle
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, r"D:\ApexOptions"); sys.path.insert(0, r"D:\ApexOptions\data\research\14nov\work")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from apex import fastlab as FL
import lab1s, hist1s, h4

WX = r"D:\ApexOptions\data\research\hist_wx"
FE = os.path.join(WX, "feat")
N = FL.N
NM = 375
WT = {"HDFCBANK": 10.38, "ICICIBANK": 9.05, "RELIANCE": 7.58, "BHARTIARTL": 5.1, "LT": 4.2, "SBIN": 3.79, "AXISBANK": 3.37, "INFY": 3.35,
      "KOTAKBANK": 2.93, "M&M": 2.52, "TCS": 2.52, "ITC": 2.52, "BAJFINANCE": 2.2, "HINDUNILVR": 1.85}
BANK = {"HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "BAJFINANCE"}
HALF = 0.0011


def minute_grid(df, what, col="close"):
    g = df[df.what == what]
    out = np.full(NM, np.nan)
    if not len(g):
        return out
    t = pd.to_datetime(g.datetime)
    m = ((t.dt.hour * 60 + t.dt.minute) - 555).to_numpy()
    ok = (m >= 0) & (m < NM)
    out[m[ok]] = g[col].to_numpy(float)[ok]
    return pd.Series(out).ffill().to_numpy()


def lag(x, k):
    o = np.full(len(x), np.nan); o[k:] = x[k:] - x[:-k]; return o


def labels(D, rows):
    """per decision second: CE and PE results with the champion's exits on the model option (normal-day ladder)."""
    fw = FL._ffill0(D["fwd"])
    out = {"CE": np.full(len(rows), np.nan), "PE": np.full(len(rows), np.nan), "CE_hold": np.full(len(rows), np.nan), "PE_hold": np.full(len(rows), np.nan)}
    cache = {}
    for n, i in enumerate(rows):
        F = fw[i]
        if not np.isfinite(F):
            continue
        for side in ("CE", "PE"):
            call = side == "CE"
            Ks = (np.floor(F / 50.0) * 50.0 + 50.0 * np.arange(-4, 5)).astype(float)
            dl, _, _ = FL.greeks(F, Ks, D["T"][i], D["iv"], call)
            ad = np.abs(dl); ok = ad >= 0.52
            if not ok.any():
                continue
            K = float(Ks[int(np.argmin(np.where(ok, np.abs(ad - 0.52), 9.0)))])
            key = (K, side)
            if key not in cache:
                with np.errstate(all="ignore"):
                    px = FL.b76(fw, K, D["T"], D["iv"], call)
                o = np.full((N, 1, 2, 2), np.nan, np.float32)
                c = 0 if call else 1
                o[:, 0, c, 0] = px * (1 - HALF); o[:, 0, c, 1] = px * (1 + HALF)
                Dm = FL.Day(dict(D)); Dm["opt"] = o; Dm["K"] = np.array([K])
                cache[key] = Dm
            t = FL.exit_ladder(cache[key], int(i), side, 0)
            if t:
                out[side][n] = t["ret"]; out[side + "_hold"][n] = t["hold_s"]
    return out


def one(day):
    try:
        p = os.path.join(FE, f"{day}.parquet")
        if os.path.exists(p):
            return day, "have"
        D = lab1s.session(day)
        if D is None or D["dte0"]:
            return day, "skip"
        wx = pd.read_parquet(os.path.join(WX, f"{day}.parquet"))
        meta = lab1s.meta()[day]
        fs = D["fs"]; fw = FL._ffill0(D["fwd"])
        mins = np.arange(5, 345)                       # 09:20 .. 14:59
        rows = mins * 60 + 59                          # the decision second: the minute's last second
        X = pd.DataFrame({"day": day, "minute": mins, "i": rows})
        # the future, per second, read at the decision second
        f = fs[rows]
        for L in (60, 300, 900, 1800, 3600):
            X[f"f_mom{L // 60}"] = f - fs[np.maximum(rows - L, 0)]
        for W in (1200, 3600):
            hi, lo = FL.roll_ext(fs, W)
            X[f"f_pos{W // 60}"] = (f - lo[rows]) / np.where(hi[rows] - lo[rows] > 0, hi[rows] - lo[rows], np.nan) - 0.5
            X[f"f_rng{W // 60}"] = hi[rows] - lo[rows]
        dhi = pd.Series(fs).cummax().to_numpy(); dlo = pd.Series(fs).cummin().to_numpy()
        X["f_daypos"] = (f - dlo[rows]) / np.where(dhi[rows] - dlo[rows] > 0, dhi[rows] - dlo[rows], np.nan) - 0.5
        X["f_dayrng"] = dhi[rows] - dlo[rows]
        first = fs[np.isfinite(fs)][0]
        X["f_from_open"] = f - first
        r1 = np.diff(fs, prepend=np.nan)
        for W in (300, 900, 3600):
            X[f"f_rv{W // 60}"] = np.sqrt(FL.roll_sum(r1 * r1, W))[rows]
        d15 = np.abs(FL.lagdiff(fs, 15))
        path = FL.roll_sum(d15, 1200) / 15.0
        X["f_er20"] = (np.abs(FL.lagdiff(fs, 1200)) / np.where(path > 0, path, np.nan))[rows]
        # the champion's own state: the 20-min breakout with 40 points, and the pullback from the extreme since
        hi20, lo20 = FL.roll_ext(fs, 1200)
        X["c_brk_up"] = (fs[rows] - hi20[rows]); X["c_brk_dn"] = (lo20[rows] - fs[rows])
        # heavyweights and sisters, per minute (bars that closed by the decision minute)
        F0 = np.where(np.isfinite(f), f, np.nan)
        lc = np.stack([np.log(minute_grid(wx, "eq:" + s)) for s in WT], 1)
        w = np.array(list(WT.values())); bank = np.array([s in BANK for s in WT], float)
        for k in (1, 5, 15):
            d = np.full(lc.shape, np.nan); d[k:] = lc[k:] - lc[:-k]
            ok = np.isfinite(d)
            den = np.where(ok, w, 0).sum(1)
            mv = np.where(ok, d * w, 0).sum(1) / np.where(den > 0, den, np.nan)
            br = (np.sign(np.where(ok, d, 0)) * w).sum(1) / np.where(den > 0, den, np.nan)
            mb = np.where(ok, d * w * bank, 0).sum(1) / np.where(np.where(ok, w * bank, 0).sum(1) > 0, np.where(ok, w * bank, 0).sum(1), np.nan)
            mr = np.where(ok, d * w * (1 - bank), 0).sum(1) / np.where(np.where(ok, w * (1 - bank), 0).sum(1) > 0, np.where(ok, w * (1 - bank), 0).sum(1), np.nan)
            X[f"hw_mv{k}"] = F0 * mv[mins]; X[f"hw_brd{k}"] = br[mins]; X[f"hw_bank_x{k}"] = F0 * (mb - mr)[mins]
            X[f"hw_lead{k}"] = X[f"hw_mv{k}"] - X[f"f_mom{k}"] if k in (1, 5, 15) and f"f_mom{k}" in X else X[f"hw_mv{k}"] - (f - fs[np.maximum(rows - 60 * k, 0)])
        for s in ("BANKNIFTY", "FINNIFTY"):
            ls = np.log(minute_grid(wx, "fut:" + s))
            for k in (1, 5, 15):
                X[f"sis_{s[:3].lower()}{k}"] = F0 * lag(ls, k)[mins]
        for k in (1, 5, 15):
            X[f"sis_lead{k}"] = 0.5 * (X[f"sis_ban{k}"] + X[f"sis_fin{k}"]) - (f - fs[np.maximum(rows - 60 * k, 0)])
        # the option chain
        ks = sorted({int(x.split(":")[1]) for x in wx.what.unique() if x.startswith("opt:")})
        C = {k: minute_grid(wx, f"opt:{k}:call") for k in ks}; P = {k: minute_grid(wx, f"opt:{k}:put") for k in ks}
        CO = {k: minute_grid(wx, f"opt:{k}:call", "open_interest") for k in ks}; PO = {k: minute_grid(wx, f"opt:{k}:put", "open_interest") for k in ks}
        CV = {k: minute_grid(wx, f"opt:{k}:call", "volume") for k in ks}; PV = {k: minute_grid(wx, f"opt:{k}:put", "volume") for k in ks}
        T = D["T"][rows]
        fm = fw[rows]
        ivs, skew, oic5, oip5, oic15, oip15, wall_c, wall_cd, wall_p, wall_pd, pcr, vol = ([] for _ in range(12))
        for n, m in enumerate(mins):
            F = fm[n]
            atm = min(ks, key=lambda k: abs(k - F)) if ks and np.isfinite(F) else None
            if atm is None:
                for L_ in (ivs, skew, oic5, oip5, oic15, oip15, wall_c, wall_cd, wall_p, wall_pd, pcr, vol):
                    L_.append(np.nan)
                continue
            st = C[atm][m] + P[atm][m]
            ivs.append(100 * st / (0.7979 * F * np.sqrt(T[n])) if np.isfinite(st) else np.nan)
            kc, kp = atm + 100, atm - 100
            if kc in C and kp in P and np.isfinite(C[kc][m]) and np.isfinite(P[kp][m]):
                ivc = FL.iv_of(F, float(kc), T[n], C[kc][m], True); ivp = FL.iv_of(F, float(kp), T[n], P[kp][m], False)
                skew.append(100 * float(ivp - ivc))
            else:
                skew.append(np.nan)
            near = [k for k in ks if abs(k - atm) <= 150]
            def chg(D_, k_, L_):
                a = [D_[k][m] - D_[k][m - L_] for k in near if m - L_ >= 0 and np.isfinite(D_[k][m]) and np.isfinite(D_[k][m - L_])]
                return float(np.sum(a)) / 1e5 if a else np.nan
            oic5.append(chg(CO, None, 5)); oip5.append(chg(PO, None, 5)); oic15.append(chg(CO, None, 15)); oip15.append(chg(PO, None, 15))
            above = [(CO[k][m], k) for k in ks if k > F and np.isfinite(CO[k][m])]
            below = [(PO[k][m], k) for k in ks if k < F and np.isfinite(PO[k][m])]
            if above:
                o_, k_ = max(above); wall_c.append(o_ / 1e5); wall_cd.append(k_ - F)
            else:
                wall_c.append(np.nan); wall_cd.append(np.nan)
            if below:
                o_, k_ = max(below); wall_p.append(o_ / 1e5); wall_pd.append(F - k_)
            else:
                wall_p.append(np.nan); wall_pd.append(np.nan)
            sc = sum(CO[k][m] for k in ks if np.isfinite(CO[k][m])); sp = sum(PO[k][m] for k in ks if np.isfinite(PO[k][m]))
            pcr.append(sp / sc if sc > 0 else np.nan)
            vol.append(sum(np.nansum(CV[k][max(0, m - 4):m + 1]) + np.nansum(PV[k][max(0, m - 4):m + 1]) for k in near))
        X["o_iv"] = ivs; X["o_skew"] = skew; X["o_oi_call5"] = oic5; X["o_oi_put5"] = oip5; X["o_oi_call15"] = oic15; X["o_oi_put15"] = oip15
        X["o_wall_call"] = wall_c; X["o_wall_call_dist"] = wall_cd; X["o_wall_put"] = wall_p; X["o_wall_put_dist"] = wall_pd; X["o_pcr"] = pcr
        X["o_iv5"] = X.o_iv - X.o_iv.shift(5); X["o_iv15"] = X.o_iv - X.o_iv.shift(15); X["o_iv_rich"] = X.o_iv - X.o_iv.expanding(10).median()
        vv = pd.Series(vol); X["o_vol_pace"] = vv / vv.expanding(10).mean()
        # VWAP of the future from its own 1-second volume
        df1 = pd.read_parquet(os.path.join(hist1s.OUT, f"fut_{json.load(open(os.path.join(hist1s.OUT, 'fut_expiry.json')))[day]}_x_0_{day}.parquet"))
        px = hist1s.grid(df1, day) - meta["basis"]
        vv1 = np.zeros(N)
        if "volume" in df1:
            t = pd.to_datetime(df1.datetime); ii = ((t - pd.Timestamp(day + " 09:15:00")).dt.total_seconds()).to_numpy().astype(int)
            ok = (ii >= 0) & (ii < N); vv1[ii[ok]] = df1.volume.to_numpy(float)[ok]
        cv = np.cumsum(vv1); vw = np.cumsum(np.where(np.isfinite(px), px, 0) * vv1) / np.where(cv > 0, cv, np.nan)
        X["f_vwap_d"] = f - vw[rows]
        # context
        X["c_dte"] = D["dte"]; X["c_rv20"] = meta["rv20"]; X["c_em"] = meta["em"]
        X["c_gap"] = (meta["o"][0] - meta["pc"]) / meta["em"] if meta["pc"] and meta["em"] else np.nan
        # labels
        L = labels(D, rows)
        for k, v in L.items():
            X["y_" + k] = v
        os.makedirs(FE, exist_ok=True)
        X.to_parquet(p + ".tmp"); os.replace(p + ".tmp", p)
        return day, len(X)
    except Exception as e:
        return day, f"error {type(e).__name__}: {e}"


if __name__ == "__main__":
    have = sorted(os.path.basename(p)[:10] for p in glob.glob(os.path.join(WX, "2*.parquet")))
    with ProcessPoolExecutor(max_workers=6) as ex:
        for d, r in ex.map(one, have):
            if r not in ("have", "skip"):
                print(d, r, flush=True)
    print("feature files:", len(glob.glob(os.path.join(FE, "*.parquet"))))
