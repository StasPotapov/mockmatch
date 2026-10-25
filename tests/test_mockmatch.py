"""Tests for mockmatch. Run with the mockmatch venv: ~/.local/share/mockmatch/venv/bin/python -m pytest tests -q

Unit tests need nothing; the browser tests need Playwright with Chromium and are skipped without it.
"""
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(ROOT, "skill", "bin", "mockmatch")
FIX = os.path.join(ROOT, "tests", "fixtures")

os.environ["MOCKMATCH_NO_VENV"] = "1"
_loader = importlib.machinery.SourceFileLoader("mockmatch", CLI)
_spec = importlib.util.spec_from_loader("mockmatch", _loader)
mockmatch = importlib.util.module_from_spec(_spec)
_loader.exec_module(mockmatch)

try:
    import playwright  # noqa: F401
    HAVE_PW = True
except ImportError:
    HAVE_PW = False


# --- pure helpers ----------------------------------------------------------------------------

def test_colors():
    assert mockmatch.hexcolor("rgb(42, 98, 214)") == "#2a62d6"
    assert mockmatch.hexcolor("rgba(0, 0, 0, 0.5)") == "#000000/0.5"
    assert mockmatch.color_dist("rgb(0, 0, 0)", "rgb(0, 0, 10)") == 10
    assert mockmatch.color_dist("rgba(1, 2, 3, 0)", "rgba(200, 0, 0, 0)") == 0


def test_redact_hides_token():
    url = "https://abc.claudeusercontent.com/v1/design/projects/abc/serve/Page%20one.dc.html?t=secret123&direct=1"
    r = mockmatch.redact(url)
    assert "secret123" not in r
    assert r.endswith("Page one.dc.html")


def test_compact_styles():
    st = {"font-size": "16px", "letter-spacing": "normal", "padding-top": "8px", "padding-right": "8px",
          "padding-bottom": "8px", "padding-left": "8px", "border-top-width": "0px",
          "border-top-left-radius": "4px", "border-top-right-radius": "4px",
          "border-bottom-right-radius": "4px", "border-bottom-left-radius": "4px"}
    c = mockmatch.compact_styles(st)
    assert c == {"font-size": "16px", "border-radius": "4px", "padding": "8px"}


def test_parse_size():
    assert mockmatch.parse_size("390x844") == (390, 844)
    assert mockmatch.parse_size("1440") == (1440, 900)


def _item(i, text, x, y, w=100, h=20, kind="text", tag="div", par=-1, **st):
    base = {p: "" for p in mockmatch.STYLE_PROPS}
    base.update({"font-family": "Inter", "font-size": "16px", "font-weight": "400", "font-style": "normal",
                 "line-height": "20px", "letter-spacing": "normal", "color": "rgb(0, 0, 0)",
                 "text-transform": "none", "text-decoration-line": "none", "background-color": "rgba(0, 0, 0, 0)",
                 "background-image": "none", "box-shadow": "none", "opacity": "1", "display": "block",
                 "border-top-style": "none"})
    for side in ("top", "right", "bottom", "left"):
        base[f"border-{side}-width"] = "0px"
        base[f"border-{side}-color"] = "rgb(0, 0, 0)"
        base[f"padding-{side}"] = "0px"
    for c in ("top-left", "top-right", "bottom-right", "bottom-left"):
        base[f"border-{c}-radius"] = "0px"
    base.update({k.replace("_", "-"): v for k, v in st.items()})
    return dict(i=i, tag=tag, depth=1, par=par, key="", text=text if kind == "text" else "", full=text,
                alt="", kind=kind, x=x, y=y, w=w, h=h, st=base)


def test_compare_finds_style_missing_and_extra():
    frame = {"w": 800, "h": 600}
    D = [_item(0, "Title", 0, 0, font_size="48px"), _item(1, "Buy now", 0, 100), _item(2, "Docs", 0, 200)]
    S = [_item(0, "Title", 0, 0, font_size="40px"), _item(1, "Buy now", 0, 100), _item(2, "Extra", 0, 400)]
    issues, pairs, score = mockmatch.compare_items(D, S, frame, frame, dict(px=1, geo=2, font=0.5, color=6))
    lines = [mockmatch.issue_line(i) for i in issues]
    assert any("font-size 48→40" in x for x in lines)
    assert any(x.startswith("! missing") and "Docs" in x for x in lines)
    assert any(x.startswith("~ extra") and "Extra" in x for x in lines)
    assert pairs[0] == 0 and pairs[1] == 1


def test_compare_fuzzy_text_and_gap():
    frame = {"w": 800, "h": 600}
    D = [_item(0, "Header", 0, 0), _item(1, "Text lines, not images.", 0, 40)]
    S = [_item(0, "Header", 0, 0), _item(1, "Text lines instead of images.", 0, 52)]
    issues, pairs, _ = mockmatch.compare_items(D, S, frame, frame, dict(px=1, geo=2, font=0.5, color=6))
    line = mockmatch.issue_line(issues[0])
    assert 'text "Text lines, not images."→"Text lines instead of images."' in line
    assert "gap-above 20→32" in line


def test_children_of_a_changed_box_fold():
    frame = {"w": 800, "h": 600}
    D = [_item(0, "Card", 0, 0, w=300, h=100, kind="box", padding_top="20px"),
         _item(1, "Inside", 20, 20, par=0)]
    S = [_item(0, "Card", 0, 0, w=300, h=92, kind="box", padding_top="16px"),
         _item(1, "Inside", 16, 16, par=0)]
    issues, _, _ = mockmatch.compare_items(D, S, frame, frame, dict(px=1, geo=2, font=0.5, color=6))
    assert len(issues) == 1
    assert "(+1 inside moved)" in mockmatch.issue_line(issues[0])


def test_guard_hook():
    hook = os.path.join(ROOT, "skill", "hooks", "mockmatch-guard.py")

    def run(path):
        r = subprocess.run([sys.executable, hook], input=json.dumps({"tool_input": {"file_path": path}}),
                           capture_output=True, text=True)
        return r.stdout

    assert "deny" in run("/p/build/mockmatch/20261025-101010-x/1280/site.png")
    assert "deny" in run("/p/build/mockmatch/shots/home.png")
    assert run("/p/build/mockmatch/20261025-101010-x/1280/diff/r1.png") == ""
    assert run("/p/build/mockmatch/look/101010.png") == ""


# --- browser ---------------------------------------------------------------------------------

def cli(*args, cwd):
    env = dict(os.environ, MOCKMATCH_PROJECT=str(cwd))
    env.pop("MOCKMATCH_NO_VENV", None)
    return subprocess.run([sys.executable, CLI, *args], capture_output=True, text=True, env=env, timeout=180)


@pytest.mark.skipif(not HAVE_PW, reason="needs Playwright")
def test_compare_fixtures(tmp_path):
    r = cli("compare", "--design", os.path.join(FIX, "design.html"), "--site", os.path.join(FIX, "site.html"),
            "--width", "1280", cwd=tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    o = r.stdout
    assert 'missing  a "Docs"' in o
    assert "font-size 48→40" in o
    assert "border-radius 10→6" in o
    assert "background #2a62d6→#1f4fb8" in o
    assert 'extra    button "Subscribe"' in o
    run = o.strip().splitlines()[-1].split()[1]
    assert os.path.exists(os.path.join(tmp_path, run, "board.html"))
    rep = json.load(open(os.path.join(tmp_path, run, "report.json")))
    assert rep["cells"][0]["missing"] == 1


@pytest.mark.skipif(not HAVE_PW, reason="needs Playwright")
def test_compare_same_page_is_clean(tmp_path):
    d = os.path.join(FIX, "design.html")
    r = cli("compare", "--design", d, "--site", d, "--width", "1280", cwd=tmp_path)
    assert r.returncode == 0, r.stdout
    assert "0 missing, 0 extra, 0 differ" in r.stdout
    assert "pixels 0.0%" in r.stdout


@pytest.mark.skipif(not HAVE_PW, reason="needs Playwright")
def test_session_control(tmp_path):
    try:
        r = cli("open", os.path.join(FIX, "site.html"), "--size", "1280x800", cwd=tmp_path)
        assert r.returncode == 0, r.stdout + r.stderr
        assert 'button "Subscribe"' in r.stdout
        r = cli("click", "Subscribe", "--expect", "Thanks", cwd=tmp_path)
        assert r.returncode == 0 and "+ Thanks!" in r.stdout
        r = cli("assert", "Nope", cwd=tmp_path)
        assert r.returncode == 1
        r = cli("style", "h1", "--props", "font-size", cwd=tmp_path)
        assert "font-size: 40px" in r.stdout
        r = cli("batch", "scroll top", "assert Acme", "click Pricing", cwd=tmp_path)
        assert r.returncode == 0, r.stdout
    finally:
        cli("close", cwd=tmp_path)


@pytest.mark.skipif(not HAVE_PW, reason="needs Playwright")
def test_frames_and_canvas_compare(tmp_path):
    canvas = os.path.join(FIX, "canvas.html")
    r = cli("frames", canvas, cwd=tmp_path)
    assert "Claude Design canvas: 2 frames" in r.stdout
    assert "--frame '[id=\"1b\"] .dv-card'  960x511" in r.stdout
    r = cli("compare", "--design", canvas, "--frame", '[id="1b"] .dv-card', "--site", os.path.join(FIX, "site.html"),
            "--site-frame", ".wrap", cwd=tmp_path)
    assert "== 960:" in r.stdout
    assert 'missing  a "Docs"' in r.stdout
    assert "(+2 inside moved)" in r.stdout


def test_claude_design_status_parsing():
    ok = "claude_design:\n  Scope: User config\n  Status: ✔ Connected\n  Type: http\n"
    assert mockmatch.parse_mcp_status(0, ok)[0] == "connected"
    auth = "claude_design:\n  Status: ⚠ Needs authentication\n"
    state, msg = mockmatch.parse_mcp_status(0, auth)
    assert state == "auth" and "/mcp" in msg
    gone = 'No MCP server named "claude_design". Configured servers: context7'
    state, msg = mockmatch.parse_mcp_status(1, gone)
    assert state == "missing" and "claude mcp add" in msg
    assert mockmatch.parse_mcp_status(0, "  Status: ✗ Failed to connect\n")[0] == "failed"


def test_design_project_id():
    pid = "ebae3b89-1338-4e9b-83f8-23f4460aa23b"
    assert mockmatch.design_project_id(pid) == pid
    assert mockmatch.design_project_id(f"https://claude.ai/design/p/{pid}?file=x") == pid
    assert mockmatch.design_project_id("") is None


def test_pull_keeps_claude_design_source(tmp_path):
    class A:
        project, file = None, None
    out = tmp_path / "design"
    out.mkdir()
    (out / "design.json").write_text(json.dumps({"files": ["home.html"], "claude_design": {"project": "p1", "file": "Home.dc.html", "url": "u"}}))
    assert mockmatch.claude_design_source(A, str(out), "home.html")["project"] == "p1"
    assert mockmatch.claude_design_source(A, str(out), "other.html") is None
    A.project, A.file = "https://claude.ai/design/p/abcdef12-0000", "Other.dc.html"
    cd = mockmatch.claude_design_source(A, str(out), "other.html")
    assert cd == {"project": "abcdef12-0000", "file": "Other.dc.html",
                  "url": "https://claude.ai/design/p/abcdef12-0000?file=Other.dc.html"}
    A.project, A.file = "https://claude.ai/design/p/abcdef12-0000?file=%D0%9E+x.dc.html", None
    assert mockmatch.claude_design_source(A, str(out), "o.html")["file"] == "О x.dc.html"


def test_import_artifact_files(tmp_path):
    src = tmp_path / "read" / "project"
    src.mkdir(parents=True)
    blob = "f2c35a1cae9977131fcdf99eef6d321b"
    other = "0" * 32
    (src / "Login.dc.html").write_text(
        f'<html><head><script src="./support.js"></script></head><body><x-dc><img src="/_blob/{blob}">'
        f'<img src="/_blob/{other}"></x-dc><script type="text/x-dc">class C {{}}</script></body></html>')
    (src / "canvas.json").write_text(json.dumps({"boards": {"Login.dc.html": {"title": "Вход", "w": 1440, "h": 1000}}}))
    (tmp_path / "read" / "blobs").mkdir()
    (tmp_path / "read" / "blobs" / f"{blob}.svg").write_text("<svg/>")
    out = tmp_path / "design"
    r = subprocess.run([sys.executable, CLI, "import", str(tmp_path / "read"), "--artifact", "https://claude.ai/artifact/X",
                        "--out", str(out)], capture_output=True, text=True, env={**os.environ, "MOCKMATCH_PROJECT": str(tmp_path)})
    assert r.returncode == 1 and f"path={other}" in r.stdout
    doc = (out / "Login.dc.html").read_text()
    assert "<script" not in doc and f'src="assets/{blob}.svg"' in doc and (out / "assets" / f"{blob}.svg").exists()
    meta = json.loads((out / "design.json").read_text())
    assert meta["artifact"]["boards"]["Login.dc.html"] == {"title": "Вход", "w": 1440, "h": 1000}
    assert meta["files"] == ["Login.dc.html"] and "claude_design" not in meta
