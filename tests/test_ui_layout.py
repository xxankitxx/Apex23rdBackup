"""Dashboard layout and the Forecast Lab panel's contract (12 Nov, trade-first page).

Static checks on apex/static: while a trade is open the commentary sits directly under the position band, then the
held card and the glance row, then the Forecast Lab, in every width's grid; the Lab no longer uses the trigger's amber;
the containers the Lab code draws into exist. Then the page's Lab code is run under node over payloads built from real
Lab output (tests/js/lab_payload_contract_test.js). Reads only apex/static and tests/fixtures; writes to tmp_path.
"""
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "apex", "static")


def _read(name):
    with open(os.path.join(STATIC, name), encoding="utf-8") as f:
        s = f.read()
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S) if name.endswith(".css") else s


def _templates(css, selector):
    """Every grid-template-areas value of rules whose selector list contains `selector`, as lists of area names."""
    out = []
    for m in re.finditer(r"([^{}]*)\{([^{}]*)\}", css):
        sels = [s.strip() for s in m.group(1).split(",")]
        if selector not in sels:
            continue
        a = re.search(r"grid-template-areas:\s*((?:\"[^\"]*\"\s*)+)", m.group(2))
        if a:
            out.append([w for row in re.findall(r"\"([^\"]*)\"", a.group(1)) for w in row.split()])
    return out


def _first(areas, name):
    return areas.index(name) if name in areas else None


def test_commentary_directly_under_the_band_while_holding():
    css = _read("style.css")
    tpls = _templates(css, "body.cmt-on main")
    assert len(tpls) == 3, f"expected the desktop, 1280 px and 820 px templates, found {len(tpls)}"
    for t in tpls:
        pos, cmt, held, glance, fc = (_first(t, k) for k in ("pos", "cmt", "held", "glance", "fc"))
        assert None not in (pos, cmt, held, glance, fc), t
        assert pos < cmt < held < glance < fc, t
        # nothing but the band sits above the commentary
        assert set(t[:cmt]) <= {"pos", "voice"}, t        # 13 Nov: the band and the voice card ("What I would do now", docs/56) only


def test_flat_page_has_the_glance_row_before_the_lab():
    css = _read("style.css")
    tpls = [t for t in _templates(css, "main") if "fc" in t]
    assert len(tpls) == 3
    for t in tpls:
        assert _first(t, "pos") < _first(t, "glance") < _first(t, "fc"), t
        assert "cmt" not in t and "held" not in t, t


def test_every_template_row_count_matches_its_rows():
    """The desktop templates give explicit row sizes: one per template row, the trace row as the flexible one."""
    css = _read("style.css")
    for sel in ("main", "body.cmt-on main"):
        for m in re.finditer(r"(^|\})\s*" + re.escape(sel) + r"\s*\{([^{}]*)\}", css):
            body = m.group(2)
            a = re.search(r"grid-template-areas:\s*((?:\"[^\"]*\"\s*)+)", body)
            r = re.search(r"grid-template-rows:\s*([^;]+);", body)
            if not (a and r) or r.group(1).strip() == "none":
                continue
            rows = re.findall(r"\"([^\"]*)\"", a.group(1))
            sizes = re.findall(r"minmax\([^)]*\)|\S+", r.group(1).strip())
            assert len(sizes) == len(rows), (sel, rows, sizes)
            assert "minmax(0, 1fr)" in sizes[rows.index(next(x for x in rows if "trace" in x))], (sel, sizes)


def test_glance_and_held_rows_have_fixed_heights():
    css = _read("style.css")
    assert re.search(r"\.lab-glance\s*\{[^}]*\bheight:\s*64px", css)
    assert re.search(r"body\.holding \.heldcard:not\(\[hidden\]\)\s*\{[^}]*height:\s*96px", css)
    assert re.search(r"\.lab-whatif\s*\{[^}]*min-height:", css)


def test_lab_does_not_use_the_trigger_amber():
    css = _read("style.css")
    for m in re.finditer(r"([^{}]*)\{([^{}]*)\}", css):
        sel, body = m.group(1), m.group(2)
        if (".lab-" in sel or ".forecast" in sel or "#lab" in sel or "#fcsec" in sel) and "beacon" in body:
            pytest.fail(f"the Lab still uses the beacon amber: {sel.strip()} {{{body.strip()}}}")


def test_stale_lab_reuses_the_frozen_treatment():
    css = _read("style.css")
    assert re.search(r"#fcsec\.lab-stale[^{]*\{[^}]*border-style:\s*dashed", css)
    assert re.search(r"#fcsec\.lab-stale \.lab-detail[^{]*\{[^}]*grayscale", css)


def test_index_has_the_lab_containers():
    html = _read("index.html")
    for i in ("heldcard", "labglance", "labdetail", "labfut", "labopt", "labnext", "labwhatif", "labdecay", "labscore",
              "labsay", "labstrip", "labhint", "fcsec", "cmt", "posband"):
        assert f'id="{i}"' in html, i
    det = html[html.index('id="labdetail"'):html.index("</details>", html.index('id="labdetail"'))]
    for i in ("labfut", "labopt", "labnext", "labwhatif", "labdecay", "labscore"):
        assert f'id="{i}"' in det, f"{i} should be inside the collapsible detail"
    assert 'id="labsay"' not in det
    assert 'src="/static/held.js"' in html and 'onerror="this.remove()"' in html
    assert 'href="/static/twins.css"' in html


def test_static_files_keep_crlf():
    for name in ("app.js", "index.html"):
        with open(os.path.join(STATIC, name), "rb") as f:
            b = f.read()
        assert b.count(b"\n") == b.count(b"\r\n"), name


def test_fmt_caches_its_formatter():
    js = _read("app.js")
    line = next(x for x in js.splitlines() if x.startswith("const fmt = "))
    assert "toLocaleString" not in line and "NF(d)" in line
    assert "setInterval(labPoll" not in js


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_lab_payload_contract(tmp_path):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "fixtures", "forecast_lab", "make_payloads.py"),
                        str(tmp_path)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=110)
    assert r.returncode == 0, r.stdout + r.stderr
    r = subprocess.run(["node", os.path.join(ROOT, "tests", "js", "lab_payload_contract_test.js"),
                        os.path.join(STATIC, "app.js"), str(tmp_path)], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", timeout=110)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "lab payload contract checks passed" in r.stdout
