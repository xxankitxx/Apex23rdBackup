"""pool_builder (8 Nov): each book's card becomes a proposed register rule and a pool pair; books without a line that
beats luck are listed for the owner; nothing is written without --apply; the proposal validates as a pool."""
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apex.conductor import pool_builder as pb, register  # noqa: E402
from apex.engine import conductor as cond, rules  # noqa: E402


def _line(factor, op, line, score, kept_ret, beats=True, kept_n=30):
    return {"factor": factor, "op": op, "line": line, "score": score, "kept_ret": kept_ret, "kept_n": kept_n,
            "kept_sr": 0.7, "other_n": 25, "other_sr": 0.4, "other_ret": -2.0, "beats_luck": beats, "item": 12,
            "item_label": "Trend efficiency", "nw_other": 5, "nw_all": 6}


def _cards():
    return {"perms": 200, "cards": {
        "spot_dc12_t12": {"n_real": 80, "n_days": 14, "real_win": 0.5, "real_mean": 1.0, "never_worked": 10, "gave_back": 8,
                          "lines": [_line("er60", ">=", 0.35, 0.30, 4.0), _line("vix", "<", 12.0, 0.35, -1.0),
                                    _line("regime=TREND", ">=", 0.5, 0.28, 3.0, beats=False)]},
        "c20_9x": {"n_real": 40, "n_days": 14, "real_win": 0.6, "real_mean": 5.0, "never_worked": 4, "gave_back": 6,
                   "lines": [_line("breadth_dir", ">=", 0.6, 0.1, 2.0, beats=False)]},
        "random_entry": {"n_real": 50, "n_days": 14, "real_win": 0.4, "real_mean": -1.0, "never_worked": 20, "gave_back": 5,
                         "lines": [_line("er60", ">=", 0.5, 0.5, 9.0)]},
        "spot_pb45": {"n_real": 12, "skipped": True, "n_days": 5, "real_win": 0.5, "real_mean": 0.0, "never_worked": 1, "gave_back": 1}}}


def test_proposal_from_cards():
    today = date(2026, 11, 8)
    reg = register.load()
    rules_out, entries, free, skipped = pb.propose(_cards(), today, include_free=("c20_9x",), reg=reg, st={})
    assert [r["factor"] for r in rules_out] == ["er60"]            # the strongest PROFITABLE line that beats luck (not vix: kept side loses)
    r = rules_out[0]
    assert r["frozen"] == "2026-11-08" and r["first_test_day"] == "2026-11-09" and r["op"] == ">=" and r["line"] == 0.35
    assert r["id"] not in {x["id"] for x in reg["rules"]} and r["family"] == "BOOK:spot_dc12_t12"
    assert rules.generic(r, {"er60": 0.4}) is None and rules.generic(r, {"er60": 0.3})
    assert [(e["book"], e["rule"], e["standing"]) for e in entries] == [("spot_dc12_t12", r["id"], "low"), ("c20_9x", None, "low")]
    assert entries[0]["ret_per_trade"] == 4.0 and entries[0]["from"] == "2026-11-09" and entries[1]["ret_per_trade"] == 5.0
    assert [f["book"] for f in free] == ["c20_9x"] and dict(skipped)["random_entry"] == "not a pool candidate"
    assert "too few rows" in dict(skipped)["spot_pb45"]
    pool = {"entries": entries}
    assert cond.pool_problems(pool, reg={x["id"]: x for x in reg["rules"] + rules_out}) == []
    md = pb.markdown(rules_out, entries, free, skipped, today)
    assert "`er60 >= 0.35`" in md and "| c20_9x | — | unrestricted" in md


def test_apply_writes_register_and_pool(tmp_path, monkeypatch):
    regp, poolp, stp = tmp_path / "register.json", tmp_path / "pool.json", tmp_path / "status.jsonl"
    regp.write_text(json.dumps({"rules": [{"id": "R-001", "family": "x", "frozen": "2026-10-21"}]}), encoding="utf-8")
    poolp.write_text(json.dumps({"entries": []}), encoding="utf-8")
    monkeypatch.setattr(register, "REGISTER", str(regp))
    monkeypatch.setattr(register, "STATUS", str(stp))
    rules_out, entries, _f, _s = pb.propose(_cards(), date(2026, 11, 8), reg=register.load(str(regp)), st={})
    pool = pb.apply(rules_out, entries, pool_path=str(poolp), reg_path=str(regp))
    reg2 = json.load(open(regp, encoding="utf-8"))
    assert [r["id"] for r in reg2["rules"]] == ["R-001", "R-002"] and "card" not in reg2["rules"][1]
    assert pool["entries"][0]["rule"] == "R-002" and json.load(open(poolp, encoding="utf-8"))["entries"] == pool["entries"]


def test_fitted_model_factors_are_excluded_before_the_best_line_is_chosen():
    """docs/34 F02 (ChatGPT, 8 Nov): an HMM / Hawkes line is not eligible; the next valid line on the same card is
    proposed instead of nothing — unless --allow-fitted, which then flags the pair."""
    cards = _cards()
    cards["cards"]["spot_dc12_t12"]["lines"].insert(0, _line("hmm_p", ">=", 0.8, 0.9, 12.0))
    cards["cards"]["c20_9x"]["lines"] = [_line("hk_ratio", ">=", 1.5, 0.6, 7.0)]
    reg = register.load()
    rules_out, entries, free, _s = pb.propose(cards, date(2026, 11, 8), reg=reg, st={})
    assert [r["factor"] for r in rules_out] == ["er60"] and [e["book"] for e in entries] == ["spot_dc12_t12"]
    assert [f["book"] for f in free] == ["c20_9x"] and not any(r.get("provenance") for r in rules_out)
    rules_out, entries, _f, _s = pb.propose(cards, date(2026, 11, 8), reg=reg, st={}, allow_fitted=True)
    assert [r["factor"] for r in rules_out] == ["hmm_p", "hk_ratio"] and all(r["provenance"] == pb.F02 for r in rules_out)
    assert all(pb.F02 in e["note"] for e in entries)
    assert pb.F02 in pb.markdown(rules_out, entries, [], [], date(2026, 11, 8))
