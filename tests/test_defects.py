"""Evidence hygiene after the D-095 frozen-quote incident (D-101): python tests/test_defects.py  (numpy only)."""
import json
import os
import sys
import tempfile

os.environ["APEX_DATA"] = tempfile.mkdtemp(prefix="apex_test_defects_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apex import config  # noqa: E402
from apex.engine import defects, diagnostics, learning  # noqa: E402

DAY = "2026-10-19"


def _t(ti, to, ret, age_in, age_out, key="NIFTY|OPT|2026-10-19|23050|CE"):
    return {"pnl_pts": ret, "pnl_rs": ret, "ret_pct": ret, "reason": "STOP", "time_in": ti, "time_out": to,
            "phase_in": "CTS", "key": key, "entry": 112.2, "exit": 112.2, "trade_age_in": age_in, "trade_age_out": age_out}


class _B:
    def __init__(self, trades):
        self.trades, self.pos = trades, None


def _reset():
    for p in (learning.DAYS, defects.DEFECTS_FILE):
        if os.path.exists(p):
            os.remove(p)


def test_quote_defect_rule():
    assert defects.quote_defect(_t("09:44:11", "09:44:34", 0.0, 237851.5, 237875.0)).startswith("entry quote 66.1 h old (previous session)")
    assert defects.quote_defect(_t("10:00:00", "10:01:00", 1.0, 1.1, 17.0)) is None      # 19 Oct max true age 17 s
    assert "exit quote 601 s old" in defects.quote_defect(_t("10:00:00", "10:11:00", 1.0, 1.0, 601.0))
    assert defects.quote_defect({"ret_pct": 1.0, "time_in": "10:00:00"}) is None          # legacy row: unverifiable


def test_19oct_shape_frozen_trades_excluded_and_paired_tests_stay_paired():
    _reset()
    books = {"m2.0_s0.5": _B([_t("09:44:11", "09:44:34", 0.0, 237851.5, 237875.0)]),
             "futures_only": _B([_t("09:28:15", "09:29:19", 4.766, 1.0, 1.2, "PE"),           # clean PE, before 1st defect
                                 _t("09:31:14", "09:32:40", 0.0, 237075.6, 237161.3),          # frozen CE
                                 _t("10:42:56", "10:44:07", -4.845, 2.4, 4.6, "PE"),           # clean PE, after
                                 _t("11:30:00", "11:31:00", 3.0, 1.0, 1.0, "PE")])}            # after the window
    assert learning.record_day(DAY, books)
    row = [json.loads(x) for x in open(learning.DAYS) if '"futures_only"' in x][0]
    assert row["trades"][1]["quote_defect"] and row["trades"][1]["trade_age_in"] == 237075.6    # auditable on file
    ev = learning._load_days()
    assert ev["m2.0_s0.5"][DAY] == []                                                         # champion: 0 evidence trades
    # auto window: prior-session stamp -> from the open (09:15) to the last defective exit (09:44:34)
    assert [t["time_in"] for t in ev["futures_only"][DAY]] == ["10:42:56", "11:30:00"]
    assert {b for _, b, _, _ in learning._QUAR} == {"m2.0_s0.5", "futures_only"}
    allr = learning._load_days(include_quarantined=True)
    assert len(allr["futures_only"][DAY]) == 4                                                 # nothing deleted
    txt = "\n".join(learning.quarantine_lines())
    assert "Quarantined evidence" in txt and "previous session" in txt and "09:15:00-09:44:34" in txt


def test_declared_window_and_whole_day():
    _reset()
    books = {"m2.0_s0.5": _B([_t("10:50:00", "10:51:00", 2.0, 1.0, 1.0, "PE"), _t("12:00:00", "12:05:00", 5.0, 1.0, 1.0, "PE")])}
    learning.record_day(DAY, books)
    with open(defects.DEFECTS_FILE, "w") as f:
        json.dump([{"day": DAY, "from": "09:15:00", "to": "11:05:00", "ref": "D-095", "reason": "CE frozen"}], f)
    assert [t["ret_pct"] for t in learning._load_days()["m2.0_s0.5"][DAY]] == [5.0]
    with open(defects.DEFECTS_FILE, "w") as f:
        json.dump([{"day": DAY, "from": "09:15:00", "to": "15:40:00", "ref": "D-095"}], f)
    assert DAY not in learning._load_days().get("m2.0_s0.5", {})                              # not a 0 % day
    with open(defects.DEFECTS_FILE, "w") as f:
        f.write("{torn")
    learning._load_days()
    assert "could not be read" in "\n".join(learning.quarantine_lines())


def test_candidates_in_window_are_quarantined():
    _reset()
    os.makedirs(config.PAPER_DIR, exist_ok=True)
    rows = [{"day": DAY, "time": "09:31:14", "label": "TARGET", "opt": {"rr": "CE"}, "opt_ret": {"300": 0.0}},
            {"day": DAY, "time": "11:30:00", "label": "STOP", "opt": {"rr": "PE"}, "opt_ret": {"300": -5.0}},
            {"day": DAY, "time": "12:00:00", "label": "STOP", "opt": {"rr": "CE"}, "opt_age0": 9999.0, "opt_ret": {"300": 0.0}}]
    with open(os.path.join(config.PAPER_DIR, f"candidates_{DAY}.jsonl"), "w") as f:
        f.write("\n".join(json.dumps(r) for r in rows) + "\n")
    q = defects.Quarantine([], declared={DAY: [(9 * 3600 + 900, 11 * 3600 + 300, "D-095", "")]}, declared_err=None)
    txt = "\n".join(diagnostics.candidate_lines(None, quarantine=q))
    assert "1 candidate(s) inside a feed-defect window" in txt
    assert "| all candidates | 2 | 0% |" in txt and "-5.0 |" in txt                          # stale opt_ret dropped


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
