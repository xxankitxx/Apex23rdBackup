"""Dashboard header: the ATM CE / PE tiles (3 Nov 2026) and the header grid itself.

Static checks only (no browser): the two tiles exist, every header layout places them, every grid-template-areas
in the stylesheet is rectangular (a missing or extra cell silently breaks a CSS grid), and app.js feeds the tiles
from the tick stream for the engine's ATM strike and this week's expiry.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "apex", "static")


def _read(name):
    return open(os.path.join(STATIC, name), encoding="utf-8").read()


def _areas(css):
    """Every grid-template-areas value in the stylesheet as a list of rows (each a list of cell names)."""
    out = []
    for m in re.finditer(r"grid-template-areas:\s*((?:\"[^\"]*\"\s*)+)", css):
        rows = [r.split() for r in re.findall(r"\"([^\"]*)\"", m.group(1))]
        out.append(rows)
    return out


def test_tiles_exist_in_the_html():
    html = _read("index.html")
    for i in ("t-ce", "t-pe", "atmce", "atmpe", "cek", "pek", "cesub", "pesub", "ceheld", "peheld"):
        assert f'id="{i}"' in html, i
    assert html.index('id="t-spot"') < html.index('id="t-ce"') < html.index('id="t-pe"') < html.index('id="t-vix"')


def test_every_grid_is_rectangular_and_every_header_layout_places_the_tiles():
    css = _read("style.css")
    grids = _areas(css)
    assert grids, "no grid-template-areas found"
    for rows in grids:
        widths = {len(r) for r in rows}
        assert len(widths) == 1, f"ragged grid-template-areas: {rows}"
    header = [rows for rows in grids if any("spot" in r for r in rows)]
    assert len(header) >= 3, "expected the wide, medium and phone header layouts"
    for rows in header:
        cells = {c for r in rows for c in r}
        assert {"ce", "pe", "spot", "fut", "vix", "iv", "clock", "money", "health", "mark", "stale"} <= cells, rows
    assert ".ht-ce   { grid-area: ce;" in css and ".ht-pe   { grid-area: pe;" in css
    assert "--c-ce:" in css and "--c-pe:" in css


def test_app_js_feeds_the_tiles_from_the_tick_stream():
    js = _read("app.js")
    assert "const ATM = { ce: -1, pe: -1, ba: {} }" in js
    assert "idOf(`NIFTY|OPT|${s.w0}|${Math.round(K)}|${rr}`)" in js       # the engine's strike and this week's expiry
    assert 'hdrNum(id === ATM.ce ? "atmce" : "atmpe", ltp)' in js         # painted on the tick, like Spot
    assert "tile.classList.toggle(\"held\", held)" in js
    for msg in ("chain after the open", "no chain yet", "contract not in the feed", "waiting for a print"):
        assert msg in js, msg
