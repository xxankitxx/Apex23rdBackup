# R05 shared helpers (exec'd by analysis2 / phaseB_eval; no imports of its own beyond numpy / pandas in the caller)
TELE = ("wx_eng_", "wx_save_", "wx_lin_", "wx_sync_", "wx_req_", "wx_sig_age", "wx_reconnects", "wx_feed_state",
        "wx_chain_age", "wx_depth_age", "wx_fut_age", "wx_spot_age", "wx_quote_age", "wx_n_hero")


def hold_frame(d, m):
    """The engine's continuation photograph at mark m (weather5.hold_photo), in per cent of the entry premium."""
    p = f"h{m}_"
    X = pd.DataFrame(index=d.index)
    e = d.entry.astype(float)
    X["gain_pct"] = d[p + "gain_pct"]
    X["peak_pct"] = 100 * d[p + "peak_pts"] / e
    X["gain_vs_peak"] = d[p + "gain_vs_peak"]
    X["giveback_share"] = d[p + "giveback_share"]
    X["gbr_pct_min"] = 100 * d[p + "giveback_rate_pts_min"] / e
    X["time_to_peak_s"] = d[p + "time_to_peak_s"]
    X["peak_age_s"] = d[p + "peak_age_s"]
    X["worst_pct"] = 100 * d[p + "worst_pts"] / e
    for c in ("fut_fav_pts", "fut_best_fav_pts", "fut_giveback_pts", "attr_iv_chg"):
        X[c] = d[p + c]
    X["ad_pct"] = 100 * d[p + "attr_delta_pts"] / e
    X["at_pct"] = 100 * d[p + "attr_theta_pts"] / e
    X["ares_pct"] = 100 * d[p + "attr_resid_pts"] / e
    for c in ("thesis_ep_against", "thesis_fires_with_n", "thesis_fires_against_n", "thesis_held_with_n",
              "thesis_held_against_n", "thesis_impact_with"):
        X[c] = pd.to_numeric(d[p + c], errors="coerce").astype(float)
    X["fires_net"] = X.thesis_fires_with_n - X.thesis_fires_against_n
    X["held_net"] = X.thesis_held_with_n - X.thesis_held_against_n
    X["held_with_share"] = X.thesis_held_with_n / (X.thesis_held_with_n + X.thesis_held_against_n).replace(0, np.nan)
    return X


def conds(X, disc_mask, names, qs, both=True):
    cols, labs, seen = [], [], set()
    for c in names:
        v = X[c].values.astype(float)
        vd = v[disc_mask & np.isfinite(v)]
        if len(vd) < 50 or np.nanstd(vd) == 0:
            continue
        for qq in qs:
            q = float(np.round(np.quantile(vd, qq), 6))
            with np.errstate(invalid="ignore"):
                lo, hi = v <= q, v >= q
            ops = (("<=", lo), (">=", hi)) if (both or qq == 0.5) else ((("<=", lo),) if qq < 0.5 else ((">=", hi),))
            for op, b in ops:
                if (c, op, q) in seen:
                    continue
                seen.add((c, op, q))
                fr = b[disc_mask].mean()
                if 0.02 <= fr <= 0.8:
                    cols.append(b & np.isfinite(v))
                    labs.append((c, op, float(q)))
    if not cols:
        return np.zeros((len(X), 0), bool), []
    return np.column_stack(cols), labs


def fire(d, X, rule):
    kind, feat, op, thr = rule
    v = (X[feat] if kind == "H" else d[feat]).values.astype(float)
    with np.errstate(invalid="ignore"):
        b = (v <= thr) if op == "<=" else (v >= thr)
    return b & np.isfinite(v)


def path_frame(P, m):
    """The same photograph rebuilt from ds_v2 for council trades (phaseB_c20_paths): mid stands in for the LTP the
    engine books on; alt_bid is the conservative exit at the bid."""
    if f"m{m}" not in P:
        return None
    e = P.entry.astype(float)
    X = pd.DataFrame(index=P.index)
    X["alt_mid"] = 100 * (P[f"m{m}"] - e) / e
    X["alt_bid"] = 100 * (P[f"b{m}"] - e) / e
    X["gain_pct"] = X.alt_mid
    pk = 100 * (P[f"pm{m}"] - e) / e
    X["peak_pct"] = pk.where(pk > 0, 0.0)
    X["gain_vs_peak"] = (X.gain_pct / X.peak_pct).where(X.peak_pct > 0)
    X["giveback_share"] = 1 - X.gain_vs_peak
    X["time_to_peak_s"] = P[f"tp{m}"].where(X.peak_pct > 0)
    X["peak_age_s"] = (m - P[f"tp{m}"]).where(X.peak_pct > 0)
    X["fut_fav_pts"] = P[f"f{m}"]
    X["fut_best_fav_pts"] = P[f"pf{m}"]
    X["fut_giveback_pts"] = P[f"pf{m}"] - P[f"f{m}"]
    return X
