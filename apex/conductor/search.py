"""
Step 2 of the Conductor plan, THE SEARCH (docs/28 §5): per family, on its representative book, for each weather
number: if a line is drawn here, do the winners fall mostly on one side? The output is each family's WEATHER CARD,
every line marked "found by searching the past". A card line is a candidate; it becomes a rule only when it is
written into the register (register.py), frozen and passed on test days.

  python -m apex.conductor.search DIARY.jsonl [--out DIR] [--perms 200]

A line passes only if ALL of these hold (§5):
  * enough trades both sides: weighted count >= 15 each side (a counterfactual that overlaps the real trade counts
    0.5); for whole-day facts (DAY_FACTORS) at least 5 distinct DAYS each side;
  * the kept side wins more often AND makes more on average (mean ret_pct) than the other side;
  * it holds when the line moves: the neighbouring lines (one quantile step lower and higher) keep the same side ahead;
  * it keeps the big wins: at least two-thirds of the family's top 10 % of trades by return are on the kept side;
  * it beats pure luck: the same whole search run on the same rows with the outcomes shuffled (win and return move
    together) gives the distribution of the BEST line found by luck; a real line must beat its 95th percentile.
The luck arithmetic counts distinct families, not books (variants pass or fail together).
Rows used: real and counterfactual rows of the family's representative, not excluded, never control books.
"""
import argparse
import json
import os
import zlib
from collections import defaultdict

import numpy as np

from .diary import family

# docs/28 §3 / §16a: the least-gated member of each family, in order of preference. A family whose preferred books
# have no rows falls back to its member with the most rows (flagged on the card).
REPRESENTATIVES = ("spot_pb45", "spot_dc12_t12", "spot_dc12_t12_first", "spot_orb45", "m1.5_s0.4", "gap3_s0.4",
                   "straddle_spike", "fade_switch", "c20_9x", "t28_fwd")
DAY_FACTORS = {"expiry_day", "day_before_expiry", "after_break", "event", "weekday", "dte", "gap_pts", "gap_filled",
               "vix", "vix_chg_open", "hrs_to_expiry", "norm_days", "pd_range"}   # day-type weather: counted in DAYS, not trades
SKIP = {"v", "v2_error", "v3_error", "v4_error", "v5_error", "v5_missing"}         # housekeeping on the photo, not weather
# 8 Nov (owner): EVERY docs/27 item is weather and every photo field is searched; nothing is set aside. This table
# only names the docs/27 item each field belongs to, for the cards (tests/test_weather.py checks every photo field
# has an item). An "adv_" prefix covers the advisors (item 61).
ITEMS = {
    1: ("Day type", ("expiry_day", "day_before_expiry", "after_break", "event", "weekday", "dte")),
    2: ("Time to expiry", ("hrs_to_expiry",)),
    3: ("Clock", ("mins_open", "mins_to_flat")),
    4: ("Session phase", ("phase", "phase_bucket")),
    5: ("Opening gap", ("gap_pts", "gap_filled")),
    6: ("Opening range", ("or_pos", "or15_pos", "or30_pos", "or45_pos", "or_late")),
    7: ("Range so far vs earlier days", ("range_now", "range_vs_norm", "norm_days")),
    8: ("Position in the range", ("pos_in_range", "pos_dir", "give", "range_on", "dist_hi", "dist_lo")),
    9: ("Trend or range day so far", ("er30", "er60", "dir60", "er_day", "new_highs", "new_lows", "reversals60")),
    10: ("VWAP", ("vwap_ext", "vwap_side_with", "vwap_side_min")),
    11: ("Previous day's levels", ("to_pdh", "to_pdl", "to_pdc")),
    12: ("Extremes' age", ("hi_age_min", "lo_age_min")),
    13: ("Speed", ("mv5", "mv10", "mv30", "mv60", "mv120", "mv300", "nifty60", "fmv60", "fmv300")),
    14: ("Acceleration", ("accel15", "accel30")),
    15: ("Current impulse", ("imp_rng", "imp_with", "imp_age_min", "imp_depth")),
    16: ("Swing distance", ("swing_ahead", "swing_behind")),
    17: ("Realised volatility", ("rv1", "rv5", "rv15_spot", "rv5_vs_norm")),
    18: ("Jump and drift change", ("jump_z", "cusum", "kv", "kvt", "bp_sig")),
    19: ("Choppiness", ("chop30", "chop60")),
    20: ("Spot / futures / forward agreement", ("basis", "basis_chg60", "basis_chg300", "e_basis_dev", "e_syn_dev")),
    21: ("Order-flow imbalance", ("e_fut_ofi60", "e_fut_micro")),
    22: ("Depth imbalance", ("e_fut_imb5", "e_fut_tot_imb", "fut_imb_q", "fut_imb_o", "fut_imb_t_chg30", "fut_lead")),
    23: ("Resting value", ("rest_with_rs", "rest_opp_rs", "rest_round_rs", "round_dist")),
    24: ("Refill vs withdrawal", ("fut_opp_q", "fut_opp_o", "fut_pulled", "force_rho", "force_pi")),
    25: ("Traded volume", ("fut_vol_surge", "fut_vol60", "fut_ttq60", "fut_vol_vs_norm", "agg_with_rs", "agg_net")),
    26: ("Absorption", ("absorb60",)),
    27: ("Price impact and spread", ("kyle_lambda", "fut_spread")),
    28: ("Weighted move", ("wmove10", "wmove30", "wmove60")),
    29: ("Breadth", ("breadth_dir", "breadth_n")),
    30: ("Sector split", ("wmove60_bank", "wmove60_it", "wmove60_energy", "wmove60_other")),
    31: ("Who moved first", ("ep_first", "lead_s", "ep_n_cross")),
    32: ("Basket gap", ("basket_gap",)),
    33: ("Heavyweight books", ("hw_book_imb", "hw_book_imb_t", "hw_book_chg30")),
    34: ("Heavyweight volume", ("hw_vol_surge", "hw_vol60", "hw_vol_vs_norm")),
    35: ("Sister indices", ("bn60", "bn300", "bank_z", "fn60", "fn300")),
    36: ("OI walls", ("wall_up", "wall_dn", "wall_room")),
    37: ("OI change", ("oi_own_chg5", "oi_own_chg15", "oi_own_chg30", "oi_other_chg5", "oi_other_chg15", "oi_other_chg30",
                       "oi_net_help5", "oi_net_help15", "oi_net_help30", "oi_own_chg_open")),
    38: ("Put/call ratio, max pain", ("pcr", "pcr_chg30", "e_pcr", "max_pain_dist")),
    39: ("Gamma map", ("gex_regime", "gex_balance", "gex_flip_ahead", "gex_wall_ahead", "gex_wall_behind")),
    40: ("Call vs put activity", ("vol_ratio_with", "prem_ratio_with")),
    41: ("Straddle", ("strad_chg5", "strad_excess", "strad_expanding", "strad_state")),
    42: ("IV skew", ("skew_atm", "skew_chg5")),
    43: ("IV term structure", ("term_atm", "term_chg5")),
    44: ("Smile position", ("svi_res",)),
    45: ("Premium and quote", ("premium", "spread_pct", "quote_age")),
    46: ("First-order Greeks", ("delta", "gamma", "theta_min", "theta_pct", "vega")),
    47: ("Higher-order Greeks", ("vanna", "charm_min", "speed_g", "color_min", "vomma", "zomma")),
    48: ("Breakeven", ("theta_be", "theta_be15", "theta_ratio", "speed15")),
    49: ("IV", ("iv_vs_med", "opt_iv_chg1", "opt_iv_chg5", "atm_iv_chg1", "atm_iv_chg5", "atm_iv_med", "e_iv_atm", "e_iv_chg5")),
    50: ("Premium momentum", ("prem_chg1_pct", "opt_vol1", "opt_vol_chg1")),
    51: ("Premium response", ("prem_resp1",)),
    52: ("Option book", ("opt_book_imb", "opt_imb_chg30", "opt_opp_q", "opt_opp_o", "opt_lead", "opt_run")),
    53: ("Option's own levels", ("sl_room_up_pct", "sl_room_dn_pct", "sl_n_res", "sl_n_sup", "sl_next_res")),
    54: ("Premium race odds", ("po_up1", "po_up5", "po_up15", "po_dn15", "po_ever", "po_a", "po_b")),
    55: ("VIX", ("vix", "vix_chg_open", "vix_chg5", "vix_chg15", "vix_chg30")),
    56: ("IV vs realised", ("e_iv_rv", "e_rv15", "e_v_min30")),
    57: ("Hidden regime", ("hmm_state", "hmm_p", "hmm_run_min", "hmm_left_min", "hmm_drift")),
    58: ("Order-flow chain reaction", ("hk_buy", "hk_sell", "hk_ratio")),
    59: ("Regime label", ("regime", "regime_with", "regime_ext_pct", "regime_broke")),
    60: ("Domino episode", ("ep_type", "ep_with", "ep_age_s", "ep_max_s", "sync_dir", "dom_z", "sigma15")),
    61: ("Advisors", ("adv_vetoes",)),
    62: ("Level force", ("force_verdict", "force_with", "force_level_dist")),
    63: ("Trigger", ("trigger", "trig_str", "trig_unit")),
    64: ("Last trade", ("last_exit_s", "last_won", "last_reason")),
    65: ("Direction history", ("last_same_side",)),
    66: ("Today so far", ("n_today", "ret_today", "streak")),
    67: ("Agreement", ("agree_same", "agree_other")),
    68: ("Feed health", ("fut_age", "spot_age", "gaps_today", "gap_s_today", "reconnects", "feed_state", "chain_age",
                         "depth_age_fut", "n_hero_stale", "n_hero_wide")),
    # 9 Nov (photo v4, owner: "add at least 30-40 more different kind of items"): apex/engine/weather4.py
    69: ("Yesterday's shape", ("pd_range", "pd_close_pos", "inside_pd", "range_vs_pd")),
    70: ("Pivot levels", ("pivot_dist", "piv_next_ahead")),
    71: ("Strike grid", ("strike50_ahead", "strike_pin")),
    72: ("The last bars", ("bar5_body", "bar5_body_share", "bar5_wick_ahead", "bar1_body", "bar1_range_vs15")),
    73: ("Bar runs", ("run1_with", "with_share30", "hh_hl5")),
    74: ("Position in recent windows", ("pos5", "pos15", "pos60")),
    75: ("Oscillators", ("rsi14_1m", "rsi14_5m", "z20")),
    76: ("Moving averages", ("ma5_dist", "ma20_dist", "ma60_dist", "ma_stack", "ma20_slope")),
    77: ("Compression", ("range5", "range15", "range60", "squeeze", "atr1_15", "rv_ratio")),
    78: ("The day's net move", ("day_move", "day_move_share", "open_side_min")),
    79: ("Persistence", ("ac1_30", "vr5_60")),
    80: ("The adverse path", ("max_adv1_15", "adv_bars15")),
    81: ("Sister divergence", ("bn_minus_nifty60", "bn_minus_nifty300", "bn_corr30")),
    82: ("The VIX path", ("vix_day_pos", "vix_spot_same5")),
    83: ("Breadth at other horizons", ("breadth60_dir", "breadth900_dir", "breadth_net", "breadth_chg5")),
    84: ("Dispersion and concentration", ("hw_disp300", "hw_top3_share", "hw_n_with", "hw_at_ext30")),
    85: ("The leaders", ("lead1_move60", "lead1_move300", "lead3_agree")),
    86: ("Moneyness", ("moneyness_pts", "moneyness_pct", "intrinsic", "extrinsic", "extrinsic_pct")),
    87: ("Gearing", ("gearing", "gamma_theta", "gamma_1pct", "spread_be_pts")),
    88: ("Implied move used", ("strad_now", "strad_vs_open_pct", "range_vs_strad", "day_move_vs_strad")),
    89: ("The opposite leg", ("opp_prem_chg1_pct", "opp_prem_chg5_pct", "opp_iv_chg1", "pair_chg1")),
    90: ("The premium's own path", ("prem_chg5_pct", "prem_chg15_pct", "prem_pos15", "prem_off_hi15_pct", "prem_rv5")),
    91: ("Entry liquidity", ("opt_ask_rs", "opt_ask5_rs", "opt_bid5_rs", "opt_depth_ratio")),
    92: ("The IV path", ("atm_iv_day_pos", "iv_spot_corr15", "opt_iv_vs_atm")),
    93: ("The wings", ("rr100", "fly100")),
    94: ("Own-strike OI", ("own_oi", "own_vol_oi", "own_oi_share", "own_vs_opp_oi")),
    95: ("Futures OI build-up", ("fut_oi_chg5", "fut_oi_chg30", "fut_buildup", "fut_buildup_with")),
    96: ("Volume acceleration", ("fut_vol_accel", "hw_vol_accel", "band_vol_accel", "fut_vol300")),
    97: ("Up-volume share", ("with_vol_share60", "with_vol_share300")),
    98: ("VWAP stretch", ("vwap_z", "vwap_cross_n", "vwap_stretch_share")),
    99: ("Call/put flow tilt", ("cp_vol_tilt60", "cp_vol_tilt_chg")),
    100: ("Other books' positions", ("held_same", "held_other", "held_same_winning", "fam_n", "fam_busy", "fam_free")),
    101: ("Other books' results today", ("all_n_today", "all_win_today", "all_last_same_s", "all_last_same_won",
                                         "all_last5_same_win")),
    102: ("Trigger density", ("fires5_same", "fires5_other", "fires30_same", "fires30_other", "flip_n15",
                              "last_fire_other_s")),
    103: ("Re-entry context", ("n_same_side_today", "n_losses_today", "since_last_loss_s", "last_ret_pct", "last_peak_pts",
                               "last_hold_s", "same_key_as_last", "prem_vs_last_exit_pct", "prem_vs_last_entry_pct")),
    104: ("The day's P&L shape", ("best_today", "worst_today", "ret_last3", "win_share_today", "dd_today")),
}
# 10 Nov (photo v5, docs/38 section 6): items 105-110, 120-122, 128 are defined beside the code that builds them.
# TELEMETRY = the machine's own wall-clock timing and the provenance text: recorded on every photo, mapped to an item,
# but NOT searched (they differ between a live session and a replay of the same tape, so a rule on them cannot be
# re-tested). The one exception to "every photo field is searched".
from ..engine.weather5 import ITEMS5, TELEMETRY                         # noqa: E402
ITEMS.update(ITEMS5)
ITEM_OF = {k: n for n, (_lab, ks) in ITEMS.items() for k in ks}


def item_of(factor):
    """(item number, label) for a photo field (a category field arrives as 'name=value'); (None, '?') if unmapped."""
    k = factor.split("=")[0]
    n = ITEM_OF.get(k, 61 if k.startswith("adv_") else None)
    return (n, ITEMS[n][0]) if n else (None, "?")
QUANTILES = tuple(q / 10 for q in range(2, 9))
MIN_N, MIN_DAYS, BIG_SHARE = 15.0, 5, 2.0 / 3.0


def representative(fam_rows):
    """(book, fallback?) for one family's rows."""
    books = defaultdict(int)
    for r in fam_rows:
        books[r["book"]] += 1
    for b in REPRESENTATIVES:
        if books.get(b):
            return b, False
    return (max(books, key=books.get), True) if books else (None, True)


def features(rows):
    """{name: (values float array with nan, kind)}; kind = 'num' or 'ind' (a 0/1 indicator from a bool / category)."""
    keys = set()
    for r in rows:
        keys |= set((r.get("weather") or {}).keys())
    out = {}
    for k in sorted(keys - SKIP - TELEMETRY):          # 8 Nov: every photo field is searched; 10 Nov: bar telemetry
        vals = [(r.get("weather") or {}).get(k) for r in rows]
        if all(v is None for v in vals):
            continue
        if all(isinstance(v, (bool, type(None))) for v in vals):
            out[k] = (np.array([np.nan if v is None else float(v) for v in vals]), "ind")
        elif all(isinstance(v, (int, float, type(None))) and not isinstance(v, bool) for v in vals):
            out[k] = (np.array([np.nan if v is None else float(v) for v in vals]), "num")
        else:                                            # a category: one indicator per value
            for c in sorted({str(v) for v in vals if v is not None}):
                out[f"{k}={c}"] = (np.array([np.nan if v is None else float(str(v) == c) for v in vals]), "ind")
    return out


def _lines(x, kind):
    ok = x[np.isfinite(x)]
    if kind == "ind":
        return [0.5] if ok.size and 0 < ok.mean() < 1 else []
    if np.unique(ok).size < 10:
        return sorted(set(float(v) for v in np.unique(ok)))[1:]          # few values: every split between them
    return sorted(set(float(np.quantile(ok, q)) for q in QUANTILES))


def _side_stats(mask, w, win, ret):
    n = w[mask].sum()
    if n <= 0:
        return n, np.nan, np.nan
    return n, float((w[mask] * win[mask]).sum() / n), float((w[mask] * ret[mask]).sum() / n)


def evaluate(fx, kind, name, w, win, ret, days, big):
    """Every line of one factor: list of dicts (both sides, every line), with the checks applied except luck."""
    fin = np.isfinite(fx)
    lines = _lines(fx, kind)
    res = []
    for li, line in enumerate(lines):
        hi = fin & (fx >= line)
        lo = fin & (fx < line)
        for op, keep, other in ((">=", hi, lo), ("<", lo, hi)):
            nk, srk, rk = _side_stats(keep, w, win, ret)
            no, sro, ro = _side_stats(other, w, win, ret)
            if not (np.isfinite(srk) and np.isfinite(sro)):
                continue
            score = srk - sro
            dayf = name.split("=")[0] in DAY_FACTORS
            nd = int(days.max()) + 1 if days.size else 0
            dk = int(np.count_nonzero(np.bincount(days[keep], minlength=nd))) if dayf else None
            do = int(np.count_nonzero(np.bincount(days[other], minlength=nd))) if dayf else None
            enough = (dk >= MIN_DAYS and do >= MIN_DAYS) if dayf else (nk >= MIN_N and no >= MIN_N)
            nb = int(big.sum())
            bigk = int((big & keep).sum())
            res.append({"factor": name, "op": op, "line": round(line, 6), "li": li, "n_lines": len(lines),
                        "kept_n": round(float(nk), 1), "kept_sr": round(srk, 4), "kept_ret": round(rk, 4),
                        "other_n": round(float(no), 1), "other_sr": round(sro, 4), "other_ret": round(ro, 4),
                        "score": round(score, 4), "kept_days": dk, "other_days": do,
                        "big_wins_kept": f"{bigk}/{nb}",
                        "ok_count": bool(enough), "ok_better": bool(score > 0 and rk > ro),
                        "ok_big": bool(nb == 0 or bigk >= BIG_SHARE * nb)})
    # robustness: the neighbouring lines (same op) keep the same side ahead
    by = {(r["op"], r["li"]): r for r in res}
    for r in res:
        nbrs = [by.get((r["op"], r["li"] + k)) for k in (-1, 1)]
        nbrs = [x for x in nbrs if x is not None]
        r["ok_robust"] = bool(kind == "ind" or (nbrs and all(x["score"] > 0 and x["kept_ret"] > x["other_ret"]
                                                             for x in nbrs)))
    return res


def _passes(r):
    return r["ok_count"] and r["ok_better"] and r["ok_big"] and r["ok_robust"]


def search_family(rows, perms=200):
    """One family's card (rows = the representative's usable rows)."""
    feats = features(rows)
    w = np.array([float(r["weight"]) for r in rows])
    win = np.array([1.0 if r["win"] else 0.0 for r in rows])
    ret = np.array([float(r["ret_pct"]) for r in rows])
    dlist = sorted({r["day"] for r in rows})
    days = np.array([dlist.index(r["day"]) for r in rows], dtype=int)     # day index, for the day counts

    def run(win_, ret_):
        k = max(1, int(round(0.1 * len(ret_))))
        big = np.zeros(len(ret_), bool)
        big[np.argsort(-ret_, kind="stable")[:k]] = True
        big &= ret_ > 0
        out = []
        for name, (fx, kind) in feats.items():
            out += evaluate(fx, kind, name, w, win_, ret_, days, big)
        return out

    found = run(win, ret)
    cands = [r for r in found if _passes(r)]
    seed = zlib.crc32(("|".join(sorted({r["day"] for r in rows})) + str(len(rows))).encode())
    rng = np.random.default_rng(seed)
    best_luck = []
    for _ in range(perms):
        p = rng.permutation(len(rows))
        lk = [r["score"] for r in run(win[p], ret[p]) if _passes(r)]
        best_luck.append(max(lk) if lk else 0.0)
    luck95 = float(np.quantile(best_luck, 0.95)) if best_luck else None
    lines = sorted([dict(r, beats_luck=luck95 is not None and r["score"] > luck95, found_by="searching the past")
                    for r in cands], key=lambda r: -r["score"])
    return {"n_rows": len(rows), "weighted_n": round(float(w.sum()), 1), "n_days": len(dlist),
            "strike_rate": round(float((w * win).sum() / w.sum()), 4) if w.sum() else None,
            "mean_ret": round(float((w * ret).sum() / w.sum()), 4) if w.sum() else None,
            "n_factors": len(feats), "n_lines_tested": len(found), "perms": perms,
            "luck_best_95": None if luck95 is None else round(luck95, 4),
            "card": [r for r in lines if r["beats_luck"]], "near_misses": [r for r in lines if not r["beats_luck"]][:10]}


def search(diary_rows, perms=200, min_rows=30):
    fams = defaultdict(list)
    for r in diary_rows:
        if r.get("control") or r.get("excluded") or r.get("ret_pct") is None or r.get("win") is None:
            continue
        fams[family(r)].append(r)
    cards = {}
    for fam, rows in sorted(fams.items()):
        rep, fb = representative(rows)
        rr = [r for r in rows if r["book"] == rep]
        c = {"family": fam, "representative": rep, "representative_fallback": fb, "family_books": len({r["book"] for r in rows})}
        if len(rr) < min_rows:
            c.update(n_rows=len(rr), skipped=f"fewer than {min_rows} usable rows on the representative")
        else:
            c.update(search_family(rr, perms))
        cards[fam] = c
    searched = [c for c in cards.values() if "card" in c]
    return {"families": len(cards), "families_searched": len(searched),
            "lines_on_cards": sum(len(c["card"]) for c in searched),
            "expected_lucky_cards": round(0.05 * len(searched), 2),   # each family's 95 % line: 1 in 20 by luck
            "cards": cards}


def card_markdown(res):
    out = ["# Weather cards", "",
           f"{res['families_searched']} of {res['families']} families searched; {res['lines_on_cards']} line(s) beat "
           f"luck. About {res['expected_lucky_cards']} family card(s) would show a line by luck alone. Every line here "
           "was **found by searching the past**: a candidate, not a rule.", ""]
    for fam, c in res["cards"].items():
        out.append(f"## {fam} (representative {c['representative']}{' — fallback' if c.get('representative_fallback') else ''})")
        if c.get("skipped"):
            out += [f"Skipped: {c['skipped']} ({c['n_rows']}).", ""]
            continue
        out.append(f"{c['n_rows']} rows over {c['n_days']} days; strike rate {c['strike_rate']:.0%}, mean return "
                   f"{c['mean_ret']:+.2f} %; {c['n_lines_tested']} lines tested; luck's best (95th pct) "
                   f"{c['luck_best_95']:+.3f}.")
        if not c["card"]:
            out += ["No line beats luck.", ""]
            continue
        out += ["", "| Condition | Kept: trades, strike, mean | Other side | Lift | Big wins kept |", "|---|---|---|---|---|"]
        for r in c["card"]:
            out.append(f"| {r['factor']} {r['op']} {r['line']:g} | {r['kept_n']:g}, {r['kept_sr']:.0%}, "
                       f"{r['kept_ret']:+.2f} % | {r['other_n']:g}, {r['other_sr']:.0%}, {r['other_ret']:+.2f} % | "
                       f"{r['score']:+.3f} | {r['big_wins_kept']} |")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Search each family for weather lines; write the weather cards.")
    ap.add_argument("diary")
    ap.add_argument("--out", default=None)
    ap.add_argument("--perms", type=int, default=200)
    a = ap.parse_args(argv)
    rows = [json.loads(x) for x in open(a.diary, encoding="utf-8") if x.strip()]
    res = search(rows, a.perms)
    out = a.out or os.path.dirname(os.path.abspath(a.diary))
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(os.path.join(out, "cards.json"), "w", encoding="utf-8"), indent=1, default=str)
    open(os.path.join(out, "cards.md"), "w", encoding="utf-8").write(card_markdown(res))
    print(f"search: {res['families_searched']} / {res['families']} families, {res['lines_on_cards']} line(s) on the "
          f"cards -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
