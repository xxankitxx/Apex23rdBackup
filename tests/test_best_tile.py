"""Dashboard "Best" tile and the premium chart's best label (2 Nov 2026): the best premium since entry never falls.

The engine records its peak from one print a second (peak_pts, best_prem); the tick stream shows every print. The
tile used to take max(engine peak, current tick), so a tick high between engine samples showed and then vanished
on the next tick. The chart label read only the browser's own buffer, which dropped its oldest points after ~12
minutes and starts empty on a reload. Now both read one never-falling value (st.bestPx), and the buffer thins its
older half instead of dropping it, always keeping its highest point.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = open(os.path.join(ROOT, "apex", "static", "app.js"), encoding="utf-8").read()


def test_tile_keeps_a_never_falling_best():
    assert "Math.max(p.entry + (p.peak_pts || 0), p.best_prem || 0, ltp)" not in JS          # the old, falling formula
    assert "const bestNow = Math.max(st.bestPx, p.entry + (p.peak_pts || 0)" in JS
    assert "put(E.pospeak, fmt(st.bestPx));" in JS
    assert "st.bestPx = -1e9; st.rail = null;" in JS                                             # reset per new trade


def test_chart_label_reads_the_same_best():
    assert "st.bestPx - p.entry" in JS
    assert "pnlBuf.splice(0, pnlBuf.length - 3000)" not in JS                                    # no more dropping the start


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_buffer_thinning_keeps_the_peak_and_the_whole_trade():
    m = re.search(r"function pushPnl\(t, v\) \{.*?\n\}", JS, re.S)
    assert m, "pushPnl not found"
    prog = ("const pnlBuf = [];\n" + m.group(0) +
            "\nfor (let i = 0; i < 20000; i++) pushPnl(i, i === 137 ? 99 : Math.sin(i / 50));"
            "\nconsole.log(JSON.stringify({len: pnlBuf.length, peak: pnlBuf.some(x => x[1] === 99),"
            " first: pnlBuf[0][0], last: pnlBuf[pnlBuf.length - 1][0],"
            " sorted: pnlBuf.every((x, i) => !i || x[0] > pnlBuf[i - 1][0])}));")
    out = json.loads(subprocess.run(["node", "-e", prog], capture_output=True, text=True, check=True).stdout)
    assert out == {"len": out["len"], "peak": True, "first": 0, "last": 19999, "sorted": True}
    assert out["len"] <= 3000
