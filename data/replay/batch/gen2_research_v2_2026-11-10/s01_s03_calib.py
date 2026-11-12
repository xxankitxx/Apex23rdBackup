"""S01 / S03 calibration, 10 Nov 2026. Uses the SIGNAL side only (no later price is read anywhere in this file):
the regression of the stock-futures basket move on the cash basket move and the Nifty future's own move (S01's
orthogonal part), and the quantiles of each quantity, so thresholds can be set by occupancy and not by outcome."""
import glob, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s01_s02_check as c
L = 30
X, Y, B, BF, Q = [], [], [], [], []
for p in sorted(glob.glob(os.path.join(c.DS, '*.npz'))):
    z = np.load(p)
    if len(z['t']) < 1800:
        continue
    t0, n, g = c.grid(z)
    fut = g(z['fut']); fa = g(z['fa'], 1e9)
    fm = np.where((fut[:, 0] > 0) & (fut[:, 1] >= fut[:, 0]) & (fa[:, 0] <= c.FRESH), 0.5 * (fut[:, 0] + fut[:, 1]), np.nan)
    w = z['w'].astype(float); w = w / w.sum()
    hw, hwa, sf, sfa = g(z['hw']), g(z['hwa'], 1e9), g(z['sf']), g(z['sfa'], 1e9)
    c_ok = np.isfinite(hw) & (hw > 0) & (hwa <= c.FRESH)
    sfm = 0.5 * (sf[..., 0] + sf[..., 1])
    f_ok = (sf[..., 0] > 0) & (sf[..., 1] >= sf[..., 0]) & (sfa <= c.FRESH)
    ok = c_ok & f_ok & c.lag(c_ok.astype(float), L).astype(bool) & c.lag(f_ok.astype(float), L).astype(bool)
    with np.errstate(all='ignore'):
        rc = np.where(ok, np.log(hw / c.lag(hw, L)), 0.0); rf = np.where(ok, np.log(sfm / c.lag(sfm, L)), 0.0)
    cw = (ok * w).sum(1)
    good = (cw >= 0.7) & np.isfinite(fm) & np.isfinite(c.lag(fm, L))
    with np.errstate(all='ignore'):
        cc = (rc * w).sum(1) / cw * fm; cs = (rf * w).sum(1) / cw * fm
        b = ((np.sign(rc) * ok) * w).sum(1) / cw; bf = ((np.sign(rf) * ok) * w).sum(1) / cw
    cm = fm - c.lag(fm, L)
    X.append(np.column_stack([cc, cm])[good]); Y.append(cs[good])
    bb = np.where(good, b, np.nan); B.append(np.column_stack([bb, c.lag(bb, 10), c.lag(bb, 20), c.lag(bb, 30), np.where(good, bf, np.nan), cm]))
X, Y, B = np.concatenate(X), np.concatenate(Y), np.concatenate(B)
coef = np.linalg.lstsq(X, Y, rcond=None)[0]
zz = Y - X @ coef
q = lambda a: {k: round(float(np.nanpercentile(np.abs(a), k)), 3) for k in (50, 90, 95, 99, 99.5, 99.9)}
out = dict(window_s=L, rows=int(len(Y)), b_cash=round(float(coef[0]), 4), b_mom=round(float(coef[1]), 4),
           abs_z=q(zz), abs_cash=q(X[:, 0]), abs_sfut=q(Y), abs_mom=q(X[:, 1]), abs_breadth=q(B[:, 0]),
           abs_breadth_chg30=q(B[:, 0] - B[:, 3]), abs_sfut_breadth=q(B[:, 4]))
d = np.sign(B[:, 0])
for th, ch in ((0.6, 0.5), (0.6, 0.8), (0.7, 0.8), (0.7, 1.0)):
    m = (np.abs(B[:, 0]) >= th) & ((B[:, 0] - B[:, 3]) * d >= ch) & (B[:, 0] * d >= B[:, 1] * d) & (B[:, 1] * d >= B[:, 2] * d) \
        & (B[:, 4] * d >= 0.5) & (np.abs(B[:, 5]) <= 6.0)
    out[f's03_seconds_share_{th}_{ch}'] = round(float(np.nanmean(m)), 5)
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(c.OUT, 's01_s03_calib.json'), 'w'), indent=1)
