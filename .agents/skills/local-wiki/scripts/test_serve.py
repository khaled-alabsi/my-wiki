#!/usr/bin/env python3
"""Tests for `serve.py` — the wiki UI: its routes, its writes, and mostly its refusals.

    python3 test_serve.py

The routes are the easy half. The half worth testing is what the server must NOT do, because every
one of these failures is silent and none of them shows up in a browser:

  it must bind 127.0.0.1 only         — a vault is somebody's private notes, on whatever network
                                        the laptop happens to be joined to
  it must refuse a write it cannot    — any page you have open can POST to localhost. A write
    prove came from its own page        needs the token that only this server's page carries
  it must never open a path it is given — `?path=../../.ssh/id_rsa` has to die against the notes
                                        table, not against the filesystem's opinion
  it must never overwrite blind       — the previous bytes go to .wiki/.trash/ first, every time
  a broken query must not kill it     — a 500 on one route while the rest keeps serving

No network and no clock: assets are seeded on disk, `--no-fetch` forbids the download, and
`--no-reindex` keeps the post-write refresh from spawning scanners.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import http.cookiejar
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVE = HERE / "serve.py"
SCANNER = HERE / "scan_vault.py"
GRAPH = HERE / "graph.py"
PORT = 8914

_failures: list[str] = []
_passed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _passed
    if condition:
        _passed += 1
        print(f"  ok    {name}")
    else:
        _failures.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


VAULT_FILES = {
    "reg/psd2.md": (
        "# PSD2\n\nPSD2 (Payment Services Directive 2) governs payments.\n\n"
        "```mermaid\nflowchart TD\n  A --> B\n```\n\n"
        "## Related\n- regulates :: [sca](../pay/sca.md) — mandates SCA\n"
    ),
    "pay/sca.md": "# SCA\n\n## Related\n- part-of :: [checkout](checkout.md) — a step\n",
    "pay/checkout.md": "# Checkout\n",
    "orphan.md": "# Alone\n",
    "pay/code.md": ("# Code\n\nA fenced block:\n\n```python\ndef fee(amount):\n"
                    "    return amount * 0.015\n```\n\nAnd one with no language:\n\n"
                    "```\njust text\n```\n"),
    "pay/shots.md": ("# Shots\n\n![beside it](shot.png)\n\n![from the root](/pay/shot.png)\n\n"
                     "![missing](nope.png)\n"),
    # One word, several lines, under two headings: the fixture for "every match, not just the
    # first" and for the heading chain that tells them apart.
    "reg/limits.md": (
        "# Limits\n\n## Retail\n\nThe threshold is 15,000 EUR.\n"
        "A second threshold applies at renewal.\n\n"
        "## Corporate\n\nHere the threshold is 50,000 EUR.\n"
        "And a fourth threshold nobody should see, because three is the cap.\n"
    ),
    # The routing map, and the only authoritative source of glossary entries. Deliberately carries
    # a section AFTER the glossary, so a reader that slurps the whole file instead of slicing the
    # one section is caught by "91".
    "index.md": (
        "# Index\n\n## Business Glossary\n\n"
        "- **SCA** (aka 2FA) \u2014 Strong Customer Authentication. Extra proof before a payment "
        "completes. \u2192 `pay/sca.md`\n"
        "- **PSD2** \u2014 Payment Services Directive 2. The EU rules these payment notes follow. "
        "\u2192 `reg/psd2.md`\n"
        "- **TaMrA** \u2014 Target Market Assessment. (inferred from usage in 4 notes) "
        "\u2192 `reg/psd2.md`\n"
        "- **Themenblock** \u2014 Micro-frontend fragment mounted into a host page. "
        "\u2192 `reg/psd2.md`\n"
        "- **BPKN** \u2014 undefined in the vault; appears in `reg/psd2.md`.\n\n"
        "## Contents\n\n- `reg/` - Nothingburger, a word that is in no glossary.\n"
    ),
    # A superseded pair. Nothing else writes to these, so the temporal checks are stable even
    # though test_write rewrites reg/psd2.md 25 times.
    "reg/mifid1.md": (
        "---\nvalid_until: 2018-01-03\n---\n\n# MiFID I\n\n"
        "The old regime. PSD2 came later, and SCA with it. Not sca, which is a word.\n\n"
        "## Related\n- superseded-by :: [MiFID II](mifid2.md) - replaced from 2018-01-03\n"
    ),
    "reg/mifid2.md": "---\nvalid_from: 2018-01-03\n---\n\n# MiFID II\n\nThe regime in force.\n",
    "pay/flow.mmd": "flowchart LR\n  Client --> Gateway\n  Gateway --> Ledger\n",
    # The browser check reads this one and nothing writes to it. reg/psd2.md is not usable there:
    # test_write rewrites it 25 times, so its fence is long gone by the time the browser runs.
    "docs/drawn.md": ("---\nauthor: Ada\ntype: use-case\nstatus: sample\n---\n\n"
                      "# Drawn\n\n```mermaid\nflowchart TD\n  A[Order] --> B[Booked]\n```\n"),
    # Working folders. A leading dot or underscore is the long-standing way to say "not content",
    # and the sidebar should not be listing somebody's scratch drafts as notes.
    "_drafts/wip.md": "# Half a thought\n",
    "_drafts/sketch.mmd": "flowchart LR\n  A --> B\n",
}

# Stand-ins for the pinned bundles. The fetch is never exercised in a test: it is network I/O,
# and a suite that needs the internet is a suite that stops being run.
FAKE_ASSETS = {"mermaid.min.js": "/* fake mermaid */\n", "marked.min.js": "/* fake marked */\n",
               "highlight.min.js": "/* fake highlight */\n"}


# A real PNG, so the media route is exercised on bytes a browser would actually decode.
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def build_vault(files: dict | None = None) -> Path:
    root = Path(tempfile.mkdtemp(prefix="serve-test-"))
    (root / ".wiki").mkdir()
    assets = root / ".wiki" / "ui-assets"
    assets.mkdir()
    for name, text in FAKE_ASSETS.items():
        (assets / name).write_text(text, encoding="utf-8")
    for rel, text in (files or VAULT_FILES).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (root / "pay").mkdir(exist_ok=True)
    (root / "pay" / "fees.py").write_text(
        "def fee(amount):\n    \"\"\"Flat 1.5%.\"\"\"\n    return amount * 0.015\n",
        encoding="utf-8")
    for rel in ("pay/shot.png", "_drafts/hidden.png"):
        img = root / rel
        img.parent.mkdir(parents=True, exist_ok=True)
        img.write_bytes(TINY_PNG)
    manifest = root / ".wiki" / "manifest.json"
    subprocess.run([sys.executable, str(SCANNER), "--root", str(root), "--out", str(manifest)],
                   capture_output=True, text=True, check=True)
    subprocess.run([sys.executable, str(GRAPH), "--vault", str(root), "scan", "--full"],
                   capture_output=True, text=True, check=True)
    return root


def start(vault: Path, port: int, *extra: str) -> subprocess.Popen:
    server = subprocess.Popen(
        [sys.executable, str(SERVE), "--vault", str(vault), "--port", str(port),
         "--no-fetch", "--no-reindex", *extra],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    for _ in range(60):
        try:
            request("/api/stats", port=port)
            return server
        except OSError:
            if server.poll() is not None:
                out, err = server.communicate()
                raise RuntimeError(f"server died: {err or out}")
            time.sleep(0.2)
    server.kill()
    raise RuntimeError("server never came up")


def request(path: str, method: str = "GET", body: bytes | None = None,
            headers: dict | None = None, port: int = PORT):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method, data=body)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    # surrogateescape, not strict: this server also serves PNG icons, and a helper that throws on
    # the first non-text byte cannot be used to check them. Valid UTF-8 decodes identically, and
    # `body.encode("utf-8", "surrogateescape")` gives the original bytes back.
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.read().decode("utf-8", "surrogateescape")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "surrogateescape")


def get_json(path: str, port: int = PORT):
    status, body = request(path, port=port)
    return status, json.loads(body)


def put(path_value: str, markdown: str, token: str | None, port: int = PORT,
        ctype: str = "application/json", site: str = "same-origin", extra: dict | None = None,
        tags: list | None = None):
    headers = {"Content-Type": ctype, "Sec-Fetch-Site": site}
    if token is not None:
        headers["X-Wiki-Token"] = token
    headers.update(extra or {})
    fields = {"path": path_value, "markdown": markdown}
    if tags is not None:
        fields["tags"] = tags
    payload = json.dumps(fields).encode("utf-8")
    return request("/api/note", "PUT", payload, headers, port=port)


def resolve_host_of(value: str) -> str:
    """serve.py's own resolver, imported rather than reimplemented."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("sv_host", SERVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.resolve_host(value)


def serve_module():
    """serve.py loaded as a module, for the pure functions that need no server."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("sv_mod", SERVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_scan_prunes() -> None:
    """The source scan must PRUNE excluded directories, not walk them and filter afterwards.

    The old implementation ran one `rglob` per known extension - 26 of them - and each one
    descended the whole tree before the results were filtered by path. In a repository with a
    virtualenv that is 26 full walks of tens of thousands of files nobody wanted: measured at
    24 seconds for `find_sources` on a 2000-note vault, paid again inside `/api/stats`, so the
    page sat empty for over a minute and the sidebar looked broken.

    The assertion is about descent, not speed: a timing test would be flaky, and the thing that
    was actually wrong is that `.venv` got visited at all.
    """
    sv = serve_module()
    root = Path(tempfile.mkdtemp(prefix="wiki-prune-"))
    (root / "notes").mkdir()
    (root / "notes/real.py").write_text("x = 1\n", encoding="utf-8")
    for hidden in (".venv/lib/python3.12/site-packages/pkg", "node_modules/dep", ".git/objects"):
        d = root / hidden
        d.mkdir(parents=True)
        (d / "buried.py").write_text("x = 2\n", encoding="utf-8")

    visited: list[str] = []
    real_walk = sv.os.walk

    def spy(top, *a, **kw):
        for dirpath, dirnames, filenames in real_walk(top, *a, **kw):
            visited.append(str(dirpath))
            yield dirpath, dirnames, filenames

    sv.os.walk = spy
    try:
        found = sv.find_sources(root)
    finally:
        sv.os.walk = real_walk

    check("93 the source scan finds a real source file", "notes/real.py" in found,
          f"got {sorted(found)}")
    check("93 and none of the buried ones",
          not any(p.endswith("buried.py") for p in found), f"got {sorted(found)}")
    check("93 it walks the tree once, pruning as it goes — never per extension",
          visited and len(visited) < 10, f"visited {len(visited)} directories")
    for excluded in (".venv", "node_modules", ".git"):
        check(f"93 it never descends into {excluded}",
              not any(f"/{excluded}/" in v or v.endswith(f"/{excluded}") for v in visited),
              f"descended into {excluded}")
    shutil.rmtree(root, ignore_errors=True)


def test_csv_renders_as_a_table() -> None:
    """A `.csv` opens as a table, not as a wall of commas - and a huge one is capped, and says so.

    A results file is a table somebody produced; fenced as plain text the reader lines the columns
    up by eye. The row cap matters because a vault of experiment output carries files with tens of
    thousands of rows, and a page that tries to draw all of them stops being a page.
    """
    sv = serve_module()
    root = Path(tempfile.mkdtemp(prefix="wiki-csv-"))
    (root / "data").mkdir()
    (root / "data/small.csv").write_text(
        "method,arl0,note\nMVFC,200,fine\nPP|CUSUM,300,has a pipe\n", encoding="utf-8")
    (root / "data/big.csv").write_text(
        "name,n\n" + "\n".join(f"r{i},{i}" for i in range(1, 900)) + "\n", encoding="utf-8")

    md = sv.read_source(root, "data/small.csv").get("markdown", "")
    check("122 a csv opens as a markdown table", md.lstrip().startswith("| method"), repr(md[:80]))
    check("122 it has a header separator row", "| --- |" in md, "no separator row")
    check("122 a cell's own pipe is escaped, not left to split the column",
          "PP\\|CUSUM" in md, "unescaped pipe in a cell")

    big = sv.read_source(root, "data/big.csv").get("markdown", "")
    check("122 a huge csv is capped", big.count("\n|") <= 520, "every row was drawn")
    check("122 and says how many rows it did not draw", "899" in big and "showing" in big.lower(),
          "the cap is silent")
    shutil.rmtree(root, ignore_errors=True)


def test_tree_has_no_duplicate_rows() -> None:
    """One file, one row. A `.csv` is both a scanned note and an openable source - listing the
    merged set without deduplicating drew it twice in its folder."""
    status, html = request("/")
    check("122 the tree deduplicates by path", "seenPaths" in html, "no dedupe in the tree builder")


def test_search_autocompletes_filenames(vault: Path, token: str) -> None:
    """Typing in the search box offers the vault's filenames, and a hint never overlaps a row.

    Two reports. The box offered nothing while typing, so finding a file meant knowing enough of
    its name to get a hit. And the tree's secondary hint was styled `float:right`, which takes the
    text out of the row's height - a long note title drew straight over the folder row beneath it.
    """
    status, html = request("/")
    check("121 the search box is backed by a filename list",
          'list="names"' in html and 'id="names"' in html, "no filename datalist")
    check("121 the list is filled from the vault's own files",
          "fillNames(" in html, "nothing fills the name list")
    check("121 a tree hint is a block that truncates, never a float",
          ".hit .sub" in html and "text-overflow:ellipsis" in html,
          "hint still floats out of its row")


def test_search_status_is_one_line(vault: Path, token: str) -> None:
    """The status under a search is one short line; the diagnostics move to its tooltip.

    It had grown to three wrapped lines under every single search - backend, coverage, and the
    whole reason the semantic index was unavailable including the command to repair it. All of it
    true, none of it what someone who just typed a word is reading for, and repeated on every
    keystroke's worth of results.
    """
    status, html = request("/")
    check("120 the status line is built short", "statusLine(" in html, "no short status builder")
    check("120 the detail is carried as a tooltip, not a second line",
          "statusDetail(" in html and "title=" in html, "no tooltip detail")
    check("120 the old stacked second line is gone",
          '<div class="dim">${esc(extra.join(" \u00b7 "))}</div>' not in html,
          "the stacked detail line is still rendered")


def test_search_placement(vault: Path, token: str) -> None:
    """Search sits in the top bar, and there is a visible way to clear it.

    Two reports: the box was buried at the top of the sidebar under the vault name, and once a
    query was typed there was no control to get back to the tree - only selecting the text and
    deleting it. The as-of date, which is used far more rarely, had the prominent bar slot.
    """
    status, html = request("/")
    bar = html.split('<div id="bar">', 1)[1].split("</div>", 1)[0]
    check("99 the search box is in the top bar", 'id="q"' in bar, "search box not in the bar")
    check("99 and no longer above the sidebar tree",
          html.split('<aside>', 1)[1].split('id="tree"', 1)[0].count('id="q"') == 0,
          "search box still in the sidebar")
    check("99 the as-of date moved out of the bar", 'id="asof"' not in bar,
          "as-of still holds the bar slot")
    check("99 there is a button that clears the search", 'id="q-clear"' in html,
          "no clear control")
    check("99 and Escape clears it too", "Escape" in html and "clearSearch" in html,
          "no keyboard clear")


def test_tree_labels_are_filenames(vault: Path, token: str) -> None:
    """A tree row is labelled by its FILENAME, the way every file tree is.

    Labelling rows by the note's `#` heading made three different files at the repo root read as
    `Python 3.12.7`, `Python 3.12.7` and `Python version 3.12.7` — they were `requirements.txt`
    and its two platform variants, each starting with a `# Python 3.12.7` comment. A tree is how
    you find a file you already know the name of, so the name is the label; the heading is the
    extra, shown beside it only when it says something the filename does not.
    """
    status, html = request("/")
    check("98 a tree row is labelled by its filename", "leafName(" in html,
          "no filename label helper")
    check("98 the heading rides along as secondary text",
          'class="why"' in html and "leafHint(" in html, "no secondary title hint")


def test_tree_holds_every_file(vault: Path, token: str) -> None:
    """Code and diagrams live in the folder they are in, not in flat lists of their own.

    The sidebar used to end with separate `Code` and `Diagrams` sections listing every source
    file and `.mmd` in the vault by full path. So a folder in the tree showed only its markdown
    and looked empty of everything else, while the same files sat in a flat list somewhere below
    with no folder structure at all. One tree, holding whatever the folder holds.
    """
    status, html = request("/")
    check("97 the tree is built from notes, diagrams and sources together",
          "treeEntries(" in html, "tree still built from notes alone")
    check("97 there is no separate flat Code list", 'id="sources-h"' not in html,
          "flat sources section still present")
    check("97 and no separate flat Diagrams list", 'id="diagrams-h"' not in html,
          "flat diagrams section still present")
    check("97 a leaf carries its kind and a marker for code and diagrams",
          'data-kind="${esc(n.kind' in html and "KIND_MARK" in html,
          "leaves are not marked by kind")


def test_math(vault: Path, token: str) -> None:
    """Display and inline TeX render, offline, from a pinned bundle.

    Reported from a real note: a `$$ ... \\begin{cases} ... $$` block was shown as raw source.
    The renderer is MathJax's SVG build on purpose - it draws glyphs as SVG paths, so unlike KaTeX
    it needs no font files, which is what lets the page stay entirely offline under a CSP that
    allows no remote stylesheet and no remote font.
    """
    status, html = request("/")
    check("96 the math bundle is pinned like every other asset",
          "tex-svg.js" in html, "no math bundle on the page")
    check("96 display math is delimited by $$",
          '"\\\\[", "\\\\]"' in html or "'$$', '$$'" in html or '"$$", "$$"' in html,
          "no $$ display delimiter configured")
    check("96 inline math is delimited by $",
          "inlineMath" in html, "no inline delimiter configured")
    check("96 math is typeset after a note renders",
          "typesetNote" in html, "nothing typesets a rendered note")


def test_sidebar_tree(vault: Path, token: str) -> None:
    """The sidebar is a real directory tree, and it says something before the data arrives.

    Two failures the page had, both reported from a real vault:

    1. Every folder was rendered as one flat row labelled with its FULL path, so
       `Theory/Fundamental/Detection methods/Trees/FAQ` appeared as a top-level row and its
       ancestors were repeated on every line. A tree is nested: one row per path SEGMENT, each
       collapsible on its own.
    2. `boot()` awaited two slow calls before painting anything, so a refresh showed empty
       headings with no spinner and no message. A page that looks broken for a minute is
       indistinguishable from one that is broken.
    """
    status, html = request("/")
    check("95 the page serves", status == 200, str(status))
    check("95 the sidebar says something before the data arrives",
          'id="tree-loading"' in html and "reading the vault" in html, "no loading placeholder")
    check("95 the tree is built by nesting path segments",
          "function buildFolderTree" in html and "function renderFolder" in html,
          "no nested tree builder")
    check("95 and not by listing whole folder paths flat",
          "Object.keys(byFolder).sort().map" not in html, "flat folder render still present")
    check("95 a folder row is labelled with its own segment, not its full path",
          "node.name" in html, "folder row does not use the segment name")
    check("95 boot failure is reported rather than left blank",
          "could not read the vault" in html, "no failure path")


def test_hidden_folders() -> None:
    """A folder the owner listed in `hidden_folders` is not listed — but is still served.

    Hiding is a LISTING decision, exactly like `in_a_working_folder`: a note you can reach by a
    link but cannot browse to is surprising; a note that 404s the moment something links to it is
    broken. So the sidebar drops it and `/api/note` still answers for it.
    """
    sv = serve_module()
    root = Path(tempfile.mkdtemp(prefix="wiki-hide-"))
    (root / ".wiki").mkdir()

    check("94 no config means nothing is hidden", sv.hidden_folders(root) == (), "expected empty")

    (root / ".wiki/wiki-config.json").write_text(
        json.dumps({"hidden_folders": ["archive", "old/drafts"]}), encoding="utf-8")
    check("94 the configured folders are read back",
          sv.hidden_folders(root) == ("archive", "old/drafts"), str(sv.hidden_folders(root)))

    hidden = sv.hidden_folders(root)
    check("94 a note in a hidden folder is hidden", sv.is_hidden("archive/old.md", hidden), "")
    check("94 and so is one further down", sv.is_hidden("archive/2024/old.md", hidden), "")
    check("94 and one in a hidden subpath", sv.is_hidden("old/drafts/x.md", hidden), "")
    check("94 a note elsewhere is not", not sv.is_hidden("labs/real.md", hidden), "")
    check("94 a folder that merely starts with the same letters is not",
          not sv.is_hidden("archived-later/x.md", hidden), "prefix matched too eagerly")
    check("94 the hidden folder itself is not listed as a folder",
          not sv.is_hidden("labs/archive-notes.md", hidden), "substring matched")
    shutil.rmtree(root, ignore_errors=True)


def test_default_port() -> None:
    """Each vault gets its OWN default port, derived from its path.

    A shared constant meant every vault's UI opened on the same number. The second one to start
    could not bind - and the failure that actually costs you is quieter than that: a request aimed
    at vault B reaches vault A's server, and you read another vault's notes believing they are
    yours. Measured: a UI pointed at a research repo answered /api/stats with a banking vault's
    folders, because that vault's server already held the port.
    """
    sv = serve_module()
    a, b = Path("/tmp/vault-alpha"), Path("/tmp/vault-beta")
    pa, pb = sv.default_port(a), sv.default_port(b)

    check("92 two vaults get different default ports", pa != pb, f"both got {pa}")
    check("92 the same vault gets the same port every time", sv.default_port(a) == pa,
          "port is not stable across calls")
    lo, hi = sv.DEFAULT_PORT_RANGE
    check("92 the derived port is in the configured range", lo <= pa <= hi and lo <= pb <= hi,
          f"{pa}, {pb} outside {lo}-{hi}")

    # No config -> derived, not a constant shared with every other vault.
    empty = Path(tempfile.mkdtemp(prefix="wiki-port-"))
    check("92 a vault with no config falls back to its own derived port",
          sv.configured_port(empty, sv.default_port(empty)) == sv.default_port(empty),
          "fallback is not the derived port")

    # An explicit dashboard_port is an operator decision and still wins.
    (empty / ".wiki").mkdir(parents=True, exist_ok=True)
    (empty / ".wiki/wiki-config.json").write_text(json.dumps({"dashboard_port": 8123}),
                                                  encoding="utf-8")
    check("92 an explicit dashboard_port still wins over the derived one",
          sv.configured_port(empty, sv.default_port(empty)) == 8123, "config ignored")
    shutil.rmtree(empty, ignore_errors=True)


def token_from_page(html: str) -> str:
    match = re.search(r'const TOKEN\s*=\s*"([0-9a-f]{16,})"', html)
    return match.group(1) if match else ""


def test_routes(vault: Path, token: str) -> None:
    status, stats = get_json("/api/stats")
    check("40 /api/stats serves", status == 200, str(status))
    check("40 stats counts what you can browse, not what is hidden",
          stats["notes"] == 11 and stats["edges"] == 3, str(stats))
    check("40 and its folder list hides the working folders too",
          not any(f["folder"].startswith(("_", ".")) for f in stats["folders"]),
          str(stats["folders"]))
    check("40 stats lists relation types",
          any(t["rel_type"] == "regulates" for t in stats["relation_types"]),
          str(stats["relation_types"]))

    status, graph = get_json("/api/graph?limit=10")
    check("41 /api/graph serves nodes and edges",
          status == 200 and graph["nodes"] and graph["edges"], str(status))
    check("41 edges carry their relation type",
          all("rel_type" in e for e in graph["edges"]), str(graph["edges"][:2]))

    status, filtered = get_json("/api/graph?type=regulates")
    check("42 the type filter runs server-side",
          all(e["rel_type"] == "regulates" for e in filtered["edges"]), str(filtered["edges"]))

    status, node = get_json("/api/node?path=reg/psd2.md")
    check("43 /api/node serves a known note", status == 200 and node["path"] == "reg/psd2.md",
          str(node)[:200])
    check("43 the note carries its relations", node["relations"], str(node)[:200])

    status, concepts = get_json("/api/concepts")
    check("45 /api/concepts serves the vault's vocabulary",
          status == 200 and isinstance(concepts, list), str(status))

    status, query = get_json("/api/query?kind=components")
    check("46 /api/query answers like the CLI", query["query"] == "components", str(query)[:200])
    status, path_q = get_json("/api/query?kind=path-between&from=reg/psd2.md&to=pay/checkout.md")
    check("46 path-between works over HTTP too", path_q["count"] == 3, str(path_q)[:200])


def test_reader(vault: Path, token: str) -> None:
    """The half graph.py never had: the note's own bytes, the tree, and the assets."""
    status, tree = get_json("/api/tree")
    check("52 /api/tree lists every note", status == 200 and len(tree["notes"]) == 11,
          str(tree)[:200])
    check("52 the tree carries folders", {"reg", "pay"} <= set(tree["folders"]), str(tree)[:200])
    check("52e a folder starting with _ or . is not listed",
          not any(f.startswith(("_", ".")) for f in tree["folders"]), str(tree["folders"]))
    check("52e and neither are the notes inside it",
          all(not n["path"].startswith(("_", ".")) for n in tree["notes"]),
          str([n["path"] for n in tree["notes"]]))
    check("52e nor its diagrams",
          all(not d["path"].startswith(("_", ".")) for d in tree.get("diagrams", [])),
          str([d["path"] for d in tree.get("diagrams", [])]))
    check("52 a standalone .mmd diagram is listed too",
          any(d["path"] == "pay/flow.mmd" for d in tree.get("diagrams", [])), str(tree)[:250])
    check("52 diagrams are kept apart from notes",
          all(not n["path"].endswith(".mmd") for n in tree["notes"]), str(tree["notes"])[:200])

    status, mmd = get_json("/api/note?path=pay/flow.mmd")
    check("52b a .mmd file opens like a note", status == 200 and mmd.get("path") == "pay/flow.mmd",
          str(mmd)[:200])
    check("52b its body is wrapped in a mermaid fence so the page renders it",
          mmd.get("markdown", "").startswith("```mermaid") and "Gateway" in mmd["markdown"],
          str(mmd.get("markdown"))[:160])
    check("52b it is marked as a diagram, not prose", mmd.get("kind") == "diagram",
          str(mmd)[:160])
    check("52b the raw source comes with it, for the download button",
          mmd.get("source", "").startswith("flowchart LR") and "```" not in mmd["source"],
          str(mmd.get("source"))[:80])

    status, fm = get_json("/api/note?path=docs/drawn.md")
    check("52d frontmatter comes back as ordered pairs, not prose",
          fm.get("frontmatter") == [["author", "Ada"], ["type", "use-case"],
                                    ["status", "sample"]], str(fm.get("frontmatter")))
    check("52d the body starts after it, so it is never rendered as a paragraph",
          fm.get("body", "").lstrip().startswith("# Drawn"), str(fm.get("body"))[:80])
    check("52d markdown still holds the WHOLE file, so an edit round-trips it",
          fm.get("markdown", "").startswith("---\nauthor: Ada"), str(fm.get("markdown"))[:60])
    check("52d a note with no frontmatter has none, and body is the whole text",
          (lambda n: n.get("frontmatter") == [] and n.get("body") == n.get("markdown"))(
              get_json("/api/note?path=orphan.md")[1]), "empty frontmatter mishandled")

    status, body = get_json("/api/note?path=../../../etc/hosts.mmd")
    check("52c an unlisted .mmd path is refused like any other",
          body.get("error") == "unknown note", str(body)[:160])

    status, note = get_json("/api/note?path=reg/psd2.md")
    check("53 /api/note returns the raw markdown",
          note.get("markdown", "").startswith("# PSD2"), str(note)[:160])
    check("53 the mermaid fence survives intact", "```mermaid" in note.get("markdown", ""),
          "fence lost")
    check("53 backlinks come back with it", isinstance(note.get("backlinks"), list),
          str(note)[:160])

    status, body = request("/assets/mermaid.min.js")
    check("54 the mermaid bundle is served same-origin",
          status == 200 and "fake mermaid" in body, str(status))
    status, body = request("/assets/marked.min.js")
    check("54 the markdown renderer is served too", status == 200 and "fake marked" in body,
          str(status))
    status, _ = request("/assets/../../etc/passwd")
    check("54 the asset route refuses a path it was handed", status in (403, 404), str(status))

    status, found = get_json("/api/search?q=psd")
    check("55 /api/search answers", status == 200 and "hits" in found, str(found)[:200])
    check("55 it names the backend it used", found.get("backend") in ("rag", "text"),
          str(found)[:200])
    # Was `sqlite`, meaning titles only. A vault now reads note bodies too, so the honest name for
    # the no-rag answer is `text` - and each hit says whether it was a name or a line of prose.
    check("55 with no .rag workspace it says text, it does not claim to be semantic",
          found["backend"] == "text", str(found)[:120])
    check("55 and a title match is labelled as one, not as the backend",
          any(h.get("matched_by") in ("title", "concept") for h in found["hits"]),
          str([h.get("matched_by") for h in found["hits"]]))
    check("55 and it says WHY, not just which backend",
          "no .rag" in (found.get("reason") or ""), str(found.get("reason")))
    check("55 a concept row is marked as one, and is not a note to open",
          all(h.get("openable") is not None for h in found["hits"]), str(found["hits"][:1])[:200])
    check("55 the hit carries a path", found["hits"] and "path" in found["hits"][0],
          str(found)[:200])
    check("55 every backend returns the same hit shape, so nothing has to ask who answered",
          all({"path", "title", "score", "matched_by", "citation", "heading_path", "line", "text"}
              <= set(h) for h in found["hits"]), str(found["hits"][:1])[:200])

    status, filtered = get_json("/api/search?q=psd&path=pay/*")
    check("55 the path filter excludes reg/",
          all(not h["path"].startswith("reg/") for h in filtered["hits"]), str(filtered)[:200])


def test_refusals(vault: Path, token: str) -> None:
    for method in ("POST", "DELETE", "PATCH"):
        status, _ = request("/api/note", method)
        check(f"47 {method} is refused — PUT is the only write", status == 405, str(status))

    status, body = get_json("/api/node?path=../../../etc/passwd")
    check("48 a traversal path is rejected against the notes table",
          body.get("error") == "unknown note", str(body)[:200])
    check("48 nothing from outside the vault leaks", "root:" not in json.dumps(body),
          str(body)[:200])
    status, body = get_json("/api/node?path=/etc/passwd")
    check("48 an absolute path is rejected too", body.get("error") == "unknown note",
          str(body)[:200])

    status, _ = request("/../graph.sqlite")
    check("49 an unknown route is a 404, not a file", status == 404, str(status))

    status, body = get_json("/api/query?kind=nonsense")
    check("50 an unknown query kind is an error, not a crash", "error" in body, str(body))
    status, _ = get_json("/api/stats")
    check("50 the server is still alive afterwards", status == 200, str(status))


def test_write_gates(vault: Path, token: str) -> None:
    """A localhost port is not a boundary. Every one of these is a real way in."""
    status, _ = put("orphan.md", "# nope\n", None)
    check("56 a write with no token is refused", status == 403, str(status))
    status, _ = put("orphan.md", "# nope\n", "0" * 32)
    check("56 a write with the wrong token is refused", status == 403, str(status))
    status, _ = put("orphan.md", "# nope\n", token, site="cross-site")
    check("56 a cross-site write is refused even with a token", status == 403, str(status))
    status, _ = put("orphan.md", "# nope\n", token, ctype="text/plain")
    check("56 a form-shaped content type is refused", status == 415, str(status))
    check("56 none of the refused writes touched the note",
          (vault / "orphan.md").read_text(encoding="utf-8") == "# Alone\n", "note was modified")

    for bad in ("../escape.md", "/etc/passwd", ".wiki/manifest.json", ".rag/config.toml",
                ".git/config", ".agents/skills/local-wiki/SKILL.md", "notes.txt"):
        status, body = put(bad, "# nope\n", token)
        check(f"57 a write to {bad} is refused", status == 403, f"{status} {body[:80]}")
    check("57 nothing escaped the vault", not (vault.parent / "escape.md").exists(),
          "a file was written outside the vault")


def test_write(vault: Path, token: str) -> None:
    status, body = put("reg/psd2.md", "# PSD2\n\nrewritten once.\n", token)
    check("58 a legitimate write succeeds", status == 200, f"{status} {body[:120]}")
    check("58 the note holds the new text",
          "rewritten once." in (vault / "reg/psd2.md").read_text(encoding="utf-8"), "not written")

    backups = sorted((vault / ".wiki" / ".trash").glob("*/reg/psd2.md"))
    check("59 the previous bytes went to the trash first", len(backups) == 1, str(backups))
    check("59 the backup is the version that was replaced",
          backups and "Payment Services Directive 2" in backups[0].read_text(encoding="utf-8"),
          "backup is not the prior content")

    status, _ = put("reg/new-note.md", "# New\n\nmade in the browser.\n", token)
    check("60 a new note can be created", status == 200 and (vault / "reg/new-note.md").exists(),
          str(status))

    for n in range(24):
        put("reg/psd2.md", f"# PSD2\n\nedit {n}\n", token)
    kept = list((vault / ".wiki" / ".trash").glob("*/reg/psd2.md"))
    check("61 the trash keeps the last 20 versions of a note, not all 25",
          len(kept) == 20, f"{len(kept)} backups")
    other = list((vault / ".wiki" / ".trash").glob("*/reg/new-note.md"))
    check("61 pruning one note does not touch another's history", len(other) == 0, str(other))

    # Every edit already writes the previous version to .wiki/.trash/. Until now nothing showed it,
    # so the safety net existed and was invisible.
    status, history = get_json("/api/history?path=reg/psd2.md")
    check("90 a note's previous versions can be listed", status == 200 and len(history["versions"]) == 20,
          str(history)[:200])
    check("90 newest first, each with a stamp and a size",
          history["versions"][0]["at"] > history["versions"][-1]["at"]
          and all(v.get("bytes") for v in history["versions"]), str(history["versions"][:2]))

    newest = history["versions"][0]["at"]
    status, version = get_json(f"/api/version?path=reg/psd2.md&at={newest}")
    check("91 one version's text can be read back",
          status == 200 and "edit 2" in version.get("text", ""), str(version)[:160])

    status, bad = get_json("/api/version?path=reg/psd2.md&at=../../../etc/passwd")
    check("92 a stamp is a KEY, not a path", bad.get("error") is not None
          and "root:" not in json.dumps(bad), str(bad)[:160])
    status, none = get_json("/api/history?path=orphan.md")
    check("93 a note never edited has an empty history, not an error",
          none.get("versions") == [], str(none)[:160])


def test_glossary(vault: Path, token: str) -> None:
    """The vault's own vocabulary, served from the one place that is authoritative for it.

    `index.md` -> `## Business Glossary` is where a definition comes from. The `concepts` table is
    a second thing entirely: terms the scanner SAW. Serving the two as one list would present
    machine guesses as the vault's own definitions, so they stay apart - `terms` and `candidates`.
    """
    status, gloss = get_json("/api/glossary")
    terms = {t["term"]: t for t in gloss.get("terms", [])}
    check("94 the glossary is served from the index", status == 200 and len(terms) == 5,
          str(gloss)[:240])
    check("94 alphabetical, case-insensitively",
          [t["term"] for t in gloss.get("terms", [])]
          == sorted(terms, key=str.lower), str(list(terms)))

    check("94 an expansion is separated from the meaning",
          terms.get("PSD2", {}).get("expansion") == "Payment Services Directive 2"
          and terms.get("PSD2", {}).get("meaning", "").startswith("The EU rules"),
          str(terms.get("PSD2")))
    check("94 the source note travels with the term",
          terms.get("PSD2", {}).get("source") == "reg/psd2.md", str(terms.get("PSD2")))
    check("94 an alias is parsed and kept", terms.get("SCA", {}).get("aliases") == ["2FA"],
          str(terms.get("SCA")))

    # The three statuses of references/glossary.md, each recognised from its own marker.
    check("95 a plain entry is `defined`", terms.get("PSD2", {}).get("status") == "defined",
          str(terms.get("PSD2")))
    check("95 `(inferred ...)` is carried as a status, not left in the prose",
          terms.get("TaMrA", {}).get("status") == "inferred"
          and "inferred" not in terms.get("TaMrA", {}).get("meaning", "inferred"),
          str(terms.get("TaMrA")))
    check("95 a term the vault never defines is `undefined`",
          terms.get("BPKN", {}).get("status") == "undefined", str(terms.get("BPKN")))
    check("95 a non-acronym has no expansion, only a meaning",
          terms.get("Themenblock", {}).get("expansion") == ""
          and terms.get("Themenblock", {}).get("meaning", "").startswith("Micro-frontend"),
          str(terms.get("Themenblock")))

    check("96 a term carries how many notes mention it",
          isinstance(terms.get("PSD2", {}).get("mentions"), int)
          and terms.get("PSD2", {}).get("mentions", 0) >= 1,
          str(terms.get("PSD2")))

    # The scanner's own finds, kept separate from the vault's definitions and never mixed in.
    cand = {c["term"] for c in gloss.get("candidates", [])}
    check("96 terms the scanner saw but the glossary does not define are candidates, not terms",
          cand and not (cand & set(terms)), f"terms={sorted(terms)} candidates={sorted(cand)}")

    # Access: the glossary section is SLICED out of index.md. A reader that slurps the file gets
    # `## Contents` too, and this is the check that catches it.
    check("97 only the glossary section is read, not the whole index",
          "Nothingburger" not in json.dumps(gloss), "the whole index.md was parsed")


def test_as_of(vault: Path, token: str) -> None:
    """What the vault said on a date. The store already carries the windows; nothing showed them."""
    status, now = get_json("/api/tree")
    paths = {n["path"] for n in now["notes"]}
    check("98 with no date, every note is listed",
          {"reg/mifid1.md", "reg/mifid2.md"} <= paths, str(sorted(paths)))

    status, past = get_json("/api/tree?as_of=2017-01-01")
    past_paths = {n["path"] for n in past["notes"]}
    check("98 a note not yet valid is not in the tree of that day",
          "reg/mifid2.md" not in past_paths and "reg/mifid1.md" in past_paths,
          str(sorted(past_paths)))
    check("98 and the tree says how many it hid, rather than quietly shortening",
          past.get("hidden") == len(paths) - len(past_paths) and past["hidden"] > 0,
          f"hidden={past.get('hidden')}")

    status, later = get_json("/api/tree?as_of=2020-01-01")
    later_paths = {n["path"] for n in later["notes"]}
    check("98 a note whose window has closed drops out too",
          "reg/mifid1.md" not in later_paths and "reg/mifid2.md" in later_paths,
          str(sorted(later_paths)))

    status, stats = get_json("/api/stats?as_of=2017-01-01")
    check("99 the footer counts what was valid that day, not everything",
          stats.get("notes") == len(past_paths) == 10,
          f"stats={stats.get('notes')} tree={len(past_paths)}")

    # The banner. This one shows in EVERY mode, because "this was replaced" is always worth saying.
    status, note = get_json("/api/note?path=reg/mifid1.md")
    check("100 a superseded note says so, and names its successor",
          note.get("superseded_by", {}).get("path") == "reg/mifid2.md",
          str(note.get("superseded_by")))
    check("100 the successor is named as a reader would recognise it, not as a path",
          (note.get("superseded_by") or {}).get("title") == "MiFID II",
          str(note.get("superseded_by")))
    status, live = get_json("/api/note?path=reg/mifid2.md")
    check("100 a note nothing replaced carries no banner", live.get("superseded_by") is None,
          str(live.get("superseded_by")))

    status, note = get_json("/api/note?path=reg/mifid2.md&as_of=2017-01-01")
    check("101 a note read as of a date it was not valid says so",
          note.get("valid_now") is False, str({k: note.get(k) for k in
                                               ("valid_now", "valid_from", "valid_until")}))

    status, found = get_json("/api/search?q=MiFID&as_of=2017-01-01")
    check("102 search on a date drops what was not valid, and reports how many",
          all(h["path"] != "reg/mifid2.md" for h in found.get("hits", []))
          and isinstance(found.get("hidden"), int), str(found)[:240])


def test_installable(vault: Path, token: str) -> None:
    """The page can be installed on a phone as an app, and says so in the three ways a browser
    checks: a manifest, real icons, and a service worker with a fetch handler.

    The server still binds to 127.0.0.1 only. Reaching it from a phone is the user's tunnel to
    arrange; that is a deployment question and never a reason to widen the bind.
    """
    status, body = request("/manifest.webmanifest")
    manifest = json.loads(body) if status == 200 else {}
    check("108 a web app manifest is served", status == 200, str(status))
    check("108 it carries the four fields a browser needs to offer an install",
          all(manifest.get(k) for k in ("name", "short_name", "start_url", "display")),
          str(manifest)[:200])
    check("108 it is standalone, so it opens without browser chrome",
          manifest.get("display") == "standalone", str(manifest.get("display")))
    check("108 it names the vault, so two vaults do not install as one app",
          vault.name in manifest.get("name", ""), str(manifest.get("name")))
    sizes = {icon.get("sizes") for icon in manifest.get("icons", [])}
    check("108 both icon sizes an install needs are declared",
          {"192x192", "512x512"} <= sizes, str(sizes))

    for size in (192, 512):
        status, raw = request(f"/icon-{size}.png")
        head = raw.encode("utf-8", "surrogateescape")[:24]
        check(f"109 icon-{size}.png is a real PNG of the size it claims",
              status == 200 and head[:8] == b"\x89PNG\r\n\x1a\n"
              and int.from_bytes(head[16:20], "big") == size, f"{status} {head[:16]!r}")
    status, _ = request("/icon-999.png")
    check("109 an icon size nobody declared is not generated on demand", status == 404,
          str(status))

    status, worker = request("/sw.js")
    check("110 a service worker is served, which is what makes it installable",
          status == 200 and "addEventListener" in worker and "fetch" in worker, str(status))
    # The page and every API answer are no-store because this server restarts often, sometimes
    # against a DIFFERENT vault on the same port. A worker that cached them would put another
    # vault's notes on screen - the exact bug `no-store` exists to prevent, made persistent.
    check("110 the worker caches the pinned bundles and nothing else",
          "/assets/" in worker and "/api/" not in worker,
          "the service worker is willing to cache API answers")

    status, page = request("/")
    check("111 the page declares a viewport, or a phone renders it at desktop width",
          '<meta name="viewport"' in page and "width=device-width" in page, "no viewport meta")
    check("111 the page links its manifest and an icon for the home screen",
          'rel="manifest"' in page and "apple-touch-icon" in page, "not linkable as an app")
    check("111 a theme colour is declared for both schemes",
          page.count('name="theme-color"') >= 2, "no theme-color")


def test_csp_allows_only_what_the_app_needs(vault: Path) -> None:
    """A manifest and a worker are blocked outright by `default-src 'none'` unless named."""
    status, _ = request("/")
    import urllib.request as u
    with u.urlopen(f"http://127.0.0.1:{PORT}/") as response:
        csp = response.headers.get("Content-Security-Policy", "")
    check("112 the manifest is allowed to load", "manifest-src 'self'" in csp, csp)
    check("112 the service worker is allowed to run", "worker-src 'self'" in csp, csp)
    check("112 and nothing remote became allowed on the way",
          "default-src 'none'" in csp and "http://" not in csp and "https://" not in csp, csp)


def test_no_access_code_anywhere(vault: Path) -> None:
    """A network bind serves the vault straight away — there is no code and no code route.

    The gate was removed on the owner's instruction: on a network they control, being challenged
    by a six-digit code printed in a terminal they are not looking at made the phone unusable.
    What that costs is stated plainly in the banner instead — anyone who can reach the address
    can read and edit the vault — so the choice is visible rather than enforced.
    """
    port = PORT + 5
    server = subprocess.Popen(
        [sys.executable, str(SERVE), "--vault", str(vault), "--port", str(port),
         "--host", "lan", "--no-fetch", "--no-reindex"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(80):
            try:
                request("/", port=port)
                break
            except OSError:
                if server.poll() is not None:
                    out, err = server.communicate()
                    raise RuntimeError(f"server died: {err or out}")
                time.sleep(0.2)
        status, stats = get_json("/api/stats", port=port)
        check("113 a network bind serves the vault with no challenge",
              status == 200 and stats.get("notes") == 11, f"{status} {str(stats)[:120]}")
        status, page = request("/", port=port)
        check("113 and the real page is served, token and all",
              len(token_from_page(page)) >= 16, "no write token on the page")
        check("113 the page never asks for a code",
              "access code" not in page, "a code prompt is still reachable")
        status, _ = request("/pin?code=000000", port=port)
        check("113 there is no code route left", status == 404, str(status))
    finally:
        stop(server)


def test_lan_still_serves_the_laptop(vault: Path) -> None:
    """Asking for the phone must not take the vault away from the machine running it.

    `--host lan` binding only the LAN address stops serving 127.0.0.1 - the bookmark on the laptop
    dies the moment you enable phone access, which is a silent trade nobody agreed to.
    """
    check("118 `lan` binds every interface, not just the network one",
          resolve_host_of("lan") == "0.0.0.0", resolve_host_of("lan"))
    port = PORT + 7
    server = subprocess.Popen(
        [sys.executable, str(SERVE), "--vault", str(vault), "--port", str(port),
         "--host", "lan", "--no-fetch", "--no-reindex"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(80):
            try:
                status, _ = request("/", port=port)
                break
            except OSError:
                if server.poll() is not None:
                    out, err = server.communicate()
                    raise RuntimeError(f"server died: {err or out}")
                time.sleep(0.2)
        status, page = request("/", port=port)
        check("118 and 127.0.0.1 still answers after --host lan",
              status == 200 and "code" in page.lower(), str(status))
    finally:
        stop(server)


def test_a_vault_searches_note_bodies(vault: Path, token: str) -> None:
    """A word that appears inside a note, and in no title, must be findable.

    This was the hole: `Search.run` sent a plain FOLDER to `literal()`, which reads file contents,
    and sent a VAULT to `graph.serve_search()`, which matches `path LIKE`, `title LIKE` and a
    glossary term and NEVER opens a note. So the corpus with the database, the graph and the
    glossary had strictly worse text search than a directory somebody pointed at by accident - and
    every vault whose `.rag` was broken had been running on title-matching alone without saying so.
    """
    # "regime" is in reg/mifid1.md's prose and in no title, path or glossary entry anywhere.
    status, found = get_json("/api/search?q=regime&k=20")
    paths = [h["path"] for h in found.get("hits", [])]
    check("120 a word only in a note's body is found", status == 200 and "reg/mifid1.md" in paths,
          f"backend={found.get('backend')} hits={paths}")
    body_hit = next((h for h in found.get("hits", []) if h["path"] == "reg/mifid1.md"), {})
    check("120 and it carries the line it was found on, so it can be opened there",
          isinstance(body_hit.get("line"), int) and body_hit["line"] > 0, str(body_hit)[:200])
    check("120 and the matching line itself, so the card can show it",
          "regime" in (body_hit.get("text") or "").lower(), str(body_hit)[:200])

    # Title and glossary matching must SURVIVE the change, not be replaced by it.
    status, found = get_json("/api/search?q=Checkout&k=20")
    hits = found.get("hits", [])
    check("121 a title match still works, and still ranks above a body match",
          hits and hits[0]["path"] == "pay/checkout.md", str([h["path"] for h in hits])[:200])
    status, found = get_json("/api/search?q=TaMrA&k=20")
    check("121 a glossary term is still matched and still marked unopenable",
          any(h.get("kind") == "concept" and h.get("openable") is False
              for h in found.get("hits", [])), str(found.get("hits"))[:240])

    # Every hit says how IT matched, so a merged answer is still readable.
    status, found = get_json("/api/search?q=regime&k=20")
    ways = {h.get("matched_by") for h in found.get("hits", [])}
    check("122 each hit says how it matched", ways and None not in ways, str(ways))

    # 0d — what the search could actually see. Naming the backend was never enough: "sqlite" read
    # like an answer when it meant "I did not look inside a single note".
    status, found = get_json("/api/search?q=regime&k=20")
    cov = found.get("coverage") or {}
    # 8 notes + the one listed .mmd: `literal()` reads diagrams too, and a diagram is a thing
    # somebody drew and may well be looking for.
    check("123 the answer says how much of the vault it could see",
          cov.get("searchable") == 13 and cov.get("total") == 13, str(cov))
    check("123 and the page is told what to say about it",
          isinstance(found.get("backend"), str) and found.get("backend") != "", str(found)[:120])


def test_every_match_not_just_the_first(vault: Path, token: str) -> None:
    """A note that says the word four times used to produce one hit and hide the rest.

    One hit per FILE means the reader is shown an arbitrary occurrence - the first - and has no way
    to know there were others, or which one they wanted. The heading chain is what makes several
    hits in one note distinguishable rather than repetitive.
    """
    status, found = get_json("/api/search?q=threshold&k=30")
    mine = [h for h in found.get("hits", []) if h["path"] == "reg/limits.md"]
    check("124 several matches in one note are all returned, up to the cap",
          len(mine) == 3, f"{len(mine)} hits from reg/limits.md")
    check("124 each on its own line, and no two the same",
          len({h["line"] for h in mine}) == len(mine) and all(h["line"] for h in mine),
          str([h["line"] for h in mine]))
    check("124 the cap is stated, not silent",
          isinstance(found.get("total"), int) and found["total"] >= 4,
          f"total={found.get('total')}")
    check("125 each match carries the heading it sits under",
          {h["heading_path"] for h in mine} >= {"Limits > Retail", "Limits > Corporate"},
          str([h["heading_path"] for h in mine]))
    check("125 and the quoted line is the one that matched",
          all("threshold" in h["text"].lower() for h in mine), str([h["text"] for h in mine]))

    # Real counts: k is a page size, never a claim about how much exists.
    status, small = get_json("/api/search?q=threshold&k=2")
    check("126 a small k pages the answer and says how many there really are",
          len(small["hits"]) == 2 and small["total"] > 2 and small["truncated"] is True,
          f"hits={len(small['hits'])} total={small.get('total')}")


def test_images_in_notes(vault: Path, token: str) -> None:
    """A note can show a picture that lives in the vault.

    Nothing served images at all: `![](shot.png)` rendered an <img> pointing at `/shot.png`, which
    fell through every route to the 404 branch, so every screenshot in every vault was a broken
    icon. Vaults hold screenshots - that is most of what gets pasted into them.

    The path is a KEY in the media allowlist, exactly the discipline `find_diagrams()` gives .mmd
    files. Nothing here reaches open() with a string off a URL.
    """
    status, body = request("/media?path=pay/shot.png")
    raw = body.encode("utf-8", "surrogateescape")
    check("127 an image in the vault is served", status == 200 and raw[:8] == b"\x89PNG\r\n\x1a\n",
          f"{status} {raw[:12]!r}")

    for bad, why in (("../../etc/passwd", "a traversal"),
                     ("/etc/passwd", "an absolute path"),
                     (".wiki/manifest.json", "a machinery file"),
                     ("reg/psd2.md", "a note, which is not media"),
                     ("pay/nope.png", "a file that does not exist")):
        status, body = request(f"/media?path={bad}")
        check(f"128 {why} is refused", status == 404 and "root:" not in body,
              f"{bad} -> {status} {body[:60]}")

    # Hiding is a LISTING decision everywhere else in this server; for media it is an ACCESS one,
    # because an <img> is a fetch and a working-folder image would otherwise be a way to read a
    # file the sidebar deliberately does not show.
    status, _ = request("/media?path=_drafts/hidden.png")
    check("128 an image in a working folder is not served", status == 404, str(status))

    # The page has to rewrite <img> the same way it resolves links, or a relative src 404s.
    status, page = request("/")
    check("129 the page routes images through the media route",
          "/media?path=" in page and "querySelectorAll(\"img\")" in page.replace("'", '"'),
          "images are not rewritten in the rendered note")


def test_code_is_rendered(vault: Path, token: str) -> None:
    """Fenced code is highlighted, and a source file in the vault can be opened like a diagram.

    A vault about a banking system is full of snippets, and `marked` hands them over as plain
    `<pre><code class="language-python">` with nothing to colour them. A `.py` sitting beside the
    notes was invisible entirely - not in the tree, not openable - for the same reason `.mmd` used
    to be: it is not a note, so nothing listed it.
    """
    status, tree = get_json("/api/tree")
    sources = {s["path"] for s in tree.get("sources", [])}
    check("131 a source file in the vault is listed, apart from the notes",
          sources == {"pay/fees.py"}, str(sources))
    check("131 and it is not mistaken for a note",
          all(n["path"] != "pay/fees.py" for n in tree["notes"]), "a .py was listed as a note")

    status, note = get_json("/api/note?path=pay/fees.py")
    check("132 a source file opens, fenced in its own language",
          status == 200 and note.get("kind") == "source"
          and note.get("markdown", "").startswith("```python"), str(note)[:200])
    check("132 with its bytes intact and not reformatted",
          "return amount * 0.015" in note.get("source", ""), str(note.get("source"))[:120])

    status, bad = get_json("/api/note?path=pay/nothing.py")
    check("132 a source path nobody listed is refused",
          bad.get("error") is not None, str(bad)[:120])

    status, page = request("/")
    check("133 the page loads a pinned highlighter, same-origin",
          '/assets/highlight.min.js' in page, "no highlighter")
    check("133 and highlights a fence without touching a mermaid one",
          "hljs" in page and "language-mermaid" in page, "code is not highlighted")
    status, body = request("/assets/highlight.min.js")
    check("133 the highlighter is served from this server, never a CDN",
          status == 200 and "fake highlight" in body, str(status))


def test_read_only(vault: Path) -> None:
    """The old guarantee, still reachable in one flag."""
    server = start(vault, PORT + 1, "--read-only")
    try:
        status, page = request("/", port=PORT + 1)
        for method in ("PUT", "POST", "DELETE", "PATCH"):
            status, _ = request("/api/note", method, port=PORT + 1)
            check(f"62 --read-only refuses {method}", status == 405, str(status))
        status, _ = get_json("/api/stats", port=PORT + 1)
        check("62 --read-only still serves reads", status == 200, str(status))
    finally:
        stop(server)


# --- the one check a headless browser has to make ------------------------------------------
# Everything above proves the server hands over the right bytes. None of it proves a diagram
# actually DRAWS - that happens in a JavaScript engine, and the only honest way to assert it is
# to run one. Opt-in, because it needs the real 2.7 MB bundles and this suite is otherwise
# offline and fast:
#
#   WIKI_UI_ASSETS=<a vault>/.wiki/ui-assets python3 test_serve.py
#
# Skipped, loudly, when the variable is unset or no Chrome is installed. A skipped check says so;
# it never counts as a pass.

CHROMES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
]


def find_chrome() -> str | None:
    for path in CHROMES:
        if Path(path).exists():
            return path
    return shutil.which("google-chrome") or shutil.which("chromium")


def test_renders_in_a_browser(vault: Path) -> None:
    real = os.environ.get("WIKI_UI_ASSETS", "")
    chrome = find_chrome()
    if not real or not Path(real).is_dir():
        print("  skip  63 browser render — set WIKI_UI_ASSETS to a real ui-assets dir to run it")
        return
    if not chrome:
        print("  skip  63 browser render — no Chrome or Chromium found")
        return
    for name in FAKE_ASSETS:
        source = Path(real) / name
        if not source.exists():
            print(f"  skip  63 browser render — {name} missing from WIKI_UI_ASSETS")
            return
        shutil.copy2(source, vault / ".wiki" / "ui-assets" / name)
    shutil.copy2(Path(real) / "asset-pins.json", vault / ".wiki" / "ui-assets" / "asset-pins.json")

    port = PORT + 2
    server = start(vault, port)
    # No --user-data-dir on purpose: a virgin profile makes headless Chrome hang through its
    # first-run setup on macOS, and a test that hangs is worse than one that is skipped.
    full = {}

    def dump(path: str, budget: int = 30000) -> str:
        """The page's own script mentions the selectors, so only #note counts as evidence."""
        dom = subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
             "--no-default-browser-check", f"--virtual-time-budget={budget}", "--dump-dom",
             f"http://127.0.0.1:{port}/#{path}"],
            capture_output=True, text=True, timeout=120).stdout
        # The page signals with the NOTE's path; the hash may carry a :line or @n suffix.
        bare = re.sub(r"(@\d+|:\d+)$", "", re.sub(r"~\d{4}-\d{2}-\d{2}$", "", path))
        if f'data-rendered="{bare}"' not in dom:
            return ""            # the page had not finished drawing; caller retries with more
        full["dom"] = dom
        start_at = dom.find('<article id="note"')
        end_at = dom.find("</article>", start_at)
        return dom[start_at:end_at] if start_at >= 0 and end_at > start_at else ""

    try:
        for path, label in (("docs/drawn.md", "a fence inside a markdown note"),
                            ("pay/flow.mmd", "a standalone .mmd file")):
            note = ""
            for budget in (30000, 90000):          # the page says when it is done; wait for that
                note = dump(path, budget)
                if note:
                    break
            check(f"63 mermaid draws for {label}",
                  'data-processed="true"' in note and "aria-roledescription" in note,
                  "no rendered svg inside #note for " + path)
            check(f"63 the fence source is replaced by the drawing — {path}",
                  "language-mermaid" not in note, "raw fence still in #note")

        # The graph tab: nodes drew from the start, edges did not, because /api/graph returns
        # `nodes` as plain path STRINGS plus a separate `titles` map - spreading a string yields
        # {0:"R",1:"E",...} with no .path, so every edge lookup missed and every line was dropped.
        dom = subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
             "--no-default-browser-check", "--virtual-time-budget=30000", "--dump-dom",
             f"http://127.0.0.1:{port}/#graph"], capture_output=True, text=True,
            timeout=120).stdout
        svg = dom[dom.find('<svg id="g"'):dom.find("</svg>", dom.find('<svg id="g"'))]
        # `#<path>:<line>` opens a note at a line: the block that contains it is marked, so a
        # search hit can land the reader on the sentence rather than the top of the file.
        at_line = dump("reg/psd2.md:3")
        check("72 a note opens at a line",
              'data-line=' in at_line, "no line anchors stamped on the rendered blocks")
        check("72 and the block holding that line stays marked for the reader",
              "data-hit=" in at_line, "target block not marked after the flash faded")

        meta_dom = dump("docs/drawn.md")
        opts = full.get("dom", "")  # the datalists live outside #note
        # The sidebar only. Searching the whole DOM means the page's own SCRIPT text answers for
        # it - any template literal containing `>.<` reads as a folder row labelled ".".
        aside = opts[opts.find("<aside>"):opts.find("</aside>")] if "<aside>" in opts else ""
        check("69 the path filter is filled from the vault's own folders",
              'value="pay/*"' in opts and 'value="reg/*"' in opts, "no folder completions")
        check("70 notes at the vault root get a readable group name, not a dot",
              ">(root)<" in aside and ">.<" not in aside,
              "root group is labelled '.' or missing")
        check("70 the root group is still a real folder row",
              'data-f=""' in opts, "no root disclosure row")

        check("69 the type filter offers the extensions actually present",
              'value=".md"' in opts and 'value=".mmd"' in opts, "no extension completions")

        check("66 a rendered diagram offers to open full screen",
              'class="zoom"' in meta_dom, "no expand control beside the diagram")

        # `#<path>@<n>` opens the nth diagram full screen. The clone must carry a REAL size:
        # stripping width/style off it leaves an svg with no intrinsic dimensions, which lays out
        # to nothing and shows an empty overlay.
        blown = subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
             "--no-default-browser-check", "--virtual-time-budget=30000", "--dump-dom",
             f"http://127.0.0.1:{port}/#docs/drawn.md@1"],
            capture_output=True, text=True, timeout=120).stdout
        stage = blown[blown.find('<div id="stage"'):]
        stage = stage[:stage.find("</svg>") + 6] if "</svg>" in stage else stage[:400]
        check("67 the overlay opens from the address bar", 'id="overlay" class="on"' in blown
              or 'class="on" id="overlay"' in blown, "overlay not open")
        check("67 the blown-up copy is in the stage", "<svg" in stage, "no svg in #stage")
        check("68 the export bar is there when a diagram is open",
              blown.count('data-x="') >= 4, "export buttons missing from the open overlay")
        check("68 the source travelled with the figure, so .mmd can be downloaded",
              "data-src=" in blown, "no captured mermaid source on the figure")
        check("67 and it has a real size, not a zero-width clone",
              re.search(r'<svg[^>]*\swidth="(\d+(?:\.\d+)?)"', stage) is not None
              and float(re.search(r'<svg[^>]*\swidth="(\d+(?:\.\d+)?)"', stage).group(1)) > 0,
              "svg in the overlay has no positive width: " + stage[:200])
        check("65 frontmatter renders as a metadata strip",
              'class="fm"' in meta_dom, "no .fm element in #note")
        check("65 and not as a paragraph of key: value text",
              "<p>author: Ada" not in meta_dom, "frontmatter rendered as prose")

        check("64 the graph draws its nodes", svg.count("<circle") >= 4,
              f"{svg.count('<circle')} circles")
        check("64 the graph draws its edges", svg.count("<line") >= 2,
              f"{svg.count('<line')} lines — edges were dropped")
        check("64 node labels are the note titles, not character soup",
              "PSD2" in svg or "Checkout" in svg, "no readable label in the graph")

        # Interactive: every node knows which note it is, the whole scene sits in one transform
        # group so it can be panned and zoomed, and there is somewhere to show a selection.
        check("71 every node carries its note path, so it can be acted on",
              svg.count('data-p="') >= 4, f"{svg.count(chr(100)+'ata-p=')} nodes with a path")
        check("71 the scene is one transform group, so it can pan and zoom",
              '<g id="gview"' in svg, "no transform group around the graph")
        check("71 there is a panel for the selected node",
              'id="gdetail"' in blown, "no selection panel")

        # --- the three surfaces that only exist once JavaScript has run ---------------------
        # Every one of these passed its server-side check while the page showed nothing, which is
        # exactly the class of defect enhance.md requires this suite for.

        gloss = ""
        for budget in (30000, 90000):
            gloss = dump("reg/mifid1.md", budget)
            if gloss:
                break
        check("103 a known term is marked where it appears in prose",
              'class="term"' in gloss and ">PSD2</a>" in gloss,
              "no decorated term in the rendered note")
        check("103 an acronym is matched case-sensitively — `sca` is a word, `SCA` is the term",
              gloss.count('class="term"') == 2 and ">sca</a>" not in gloss,
              f"{gloss.count(chr(99)+'lass=\"term\"')} decorated; lowercase sca must not be one")
        check("103 the same term is marked once per block, not on every mention",
              gloss.count(">PSD2</a>") == 1, "the block was carpeted with one term")
        side = full.get("dom", "")
        check("103 the glossary has its own place in the sidebar",
              'id="glossary"' in side and 'data-t="SCA"' in side, "no glossary list")

        card = dump("!SCA")
        check("104 a glossary term opens as a card, and is not pretending to be a note",
              "termcard" in card and "Strong Customer Authentication" in card,
              "no term card for SCA")

        # The banner that shows in every mode: a reader must not act on a replaced note.
        sup = dump("reg/mifid1.md")
        check("105 a superseded note says so, naming its successor",
              "banner" in sup and "Superseded by" in sup and "MiFID II" in sup,
              "no supersede banner")
        live = dump("reg/mifid2.md")
        check("105 a note nothing replaced carries no banner", "Superseded by" not in live,
              "banner on a note that was never superseded")

        past = ""
        for budget in (30000, 90000):
            past = dump("reg/mifid2.md~2017-01-01", budget)
            if past:
                break
        check("106 reading at a past date says the note was not valid then",
              "not valid on 2017-01-01" in past, "no as-of banner")
        check("106 and the page says, in the frame, which day it is showing",
              'data-asof="2017-01-01"' in full.get("dom", ""), "the date is not on the page")

        # The editor's whole mechanism: a block that does not carry its own source cannot be
        # handed back as markdown, so it cannot be edited in place either.
        # --- the sidebar, and what a phone actually gets ------------------------------------
        def dump_at(width: int, height: int, path: str) -> str:
            return subprocess.run(
                [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
                 "--no-default-browser-check", f"--window-size={width},{height}",
                 "--virtual-time-budget=30000", "--dump-dom",
                 f"http://127.0.0.1:{port}/#{path}"],
                capture_output=True, text=True, timeout=120).stdout

        wide = dump_at(1280, 900, "reg/mifid1.md")
        check("108 on a wide screen the sidebar is open, as it always was",
              'data-nav="open"' in wide, "sidebar not open on a desktop-sized window")
        narrow = dump_at(390, 844, "reg/mifid1.md")
        check("108 on a phone it starts closed — a drawer over the note is not a useful open",
              'data-nav="closed"' in narrow, "sidebar covers the note on a phone")
        check("108 and the note is still what you land on",
              'data-rendered="reg/mifid1.md"' in narrow, "the note did not render at 390px")
        check("108 the toggle is on the toolbar at both sizes",
              'id="nav"' in wide and 'id="nav"' in narrow, "no sidebar toggle")

        shots = ""
        for budget in (30000, 90000):
            shots = dump("pay/shots.md", budget)
            if shots:
                break
        check("130 an image in a note actually renders in a browser",
              shots.count("/media?path=") == 2, f"{shots.count('/media?path=')} images rewritten")
        check("130 a relative src is resolved against the note, not the page root",
              "pay%2Fshot.png" in shots or "pay/shot.png" in shots,
              "relative image src was not resolved")
        check("130 and a missing image says which path did not resolve",
              "image not found" in shots, "a broken image is left as a mystery")

        code = ""
        for budget in (30000, 90000):
            code = dump("pay/code.md", budget)
            if code:
                break
        check("134 a fenced block is actually coloured in a browser",
              'class="hljs' in code and "hljs-keyword" in code,
              "no highlight spans inside #note")
        src = dump("pay/fees.py")
        check("134 and a source file opens and is coloured the same way",
              "hljs" in src and "0.015" in src, "the .py did not render")
        check("134 a mermaid fence is left to mermaid, not highlighted",
              "data-processed" in dump("docs/drawn.md"), "mermaid stopped drawing")

        check("107 every rendered block carries the source it was made from",
              "data-src=" in gloss and gloss.count("data-line=") >= 2,
              "blocks have no source stamped on them")
    finally:
        stop(server)

def stop(server: subprocess.Popen) -> None:
    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()


def main() -> int:
    vault = build_vault()
    print("serve.py")
    server = start(vault, PORT)
    try:
        status, html = request("/")
        check("51 / serves the page", status == 200 and "<!doctype html>" in html.lower(),
              str(status))
        # The SVG namespace URI is an identifier, never fetched, so it is excluded by name. What
        # this rules out is a CDN: the page must work with no network at all.
        stripped = (html.replace("http://www.w3.org/2000/svg", "")
                        .replace("http://127.0.0.1", ""))
        check("51 the page loads nothing remote",
              "http://" not in stripped and "https://" not in stripped,
              "external reference in the page")
        # The point is that nothing is fetched from ANOTHER ORIGIN. Banning `<link>` outright was
        # a proxy for that, and it fails the moment the page links its own manifest or icon.
        remote_link = re.search(r'<link\b[^>]*href="(?!/)[^"]*"', html)
        check("51 no remote script or stylesheet tag",
              "<script src=\"http" not in html and remote_link is None,
              f"remote asset tag: {remote_link.group(0) if remote_link else ''}")
        check("51 every link the page makes is same-origin and absolute-rooted",
              all(h.startswith("/") for h in re.findall(r'<link\b[^>]*href="([^"]*)"', html)),
              "a link with a relative or remote href")
        check("51 the vault name is in the page", vault.name in html, "vault name missing")

        token = token_from_page(html)
        check("51 the page carries a write token no other origin can read", len(token) >= 16,
              f"token={token!r}")

        # Editing is behind a lock the reader has to open on purpose. This is a guard against the
        # stray click, not a security control - the server's gates below are that, and they do not
        # care what the page thinks.
        check("51b the page has a lock button", 'id="lock"' in html, "no lock control")
        check("51b it starts locked, so a page left open cannot be typed into",
              "let UNLOCKED = false" in html, "edit mode is not locked by default")

        check("51c folders in the sidebar are collapsible",
              'class="folder"' in html and "function toggleFolder" in html, "no disclosure rows")
        check("51c and start collapsed — no folder body carries the open class",
              'class="folder-notes open"' not in html, "a folder is open in the served markup")

        check("51d the page ships a diagram overlay",
              'id="overlay"' in html and "function openOverlay" in html, "no overlay")
        check("51d the overlay can pan, zoom and reset",
              all(s in html for s in ("wheel", "pointerdown", "function fitOverlay")),
              "overlay has no pan/zoom wiring")

        check("51e the overlay can export the diagram",
              all(s in html for s in ('data-x="svg"', 'data-x="png"', 'data-x="mmd"',
                                      'data-x="pdf"')), "export controls missing")
        check("51e export is wired to real serialization, not a stub",
              all(s in html for s in ("XMLSerializer", "toBlob", "URL.createObjectURL",
                                      "print()")), "export functions missing")
        check("51e printing hides everything but the diagram",
              "@media print" in html, "no print stylesheet")

        check("51g graph nodes are draggable and selectable",
              all(s in html for s in ("function selectNode", "function dragNode",
                                      "gpointerdown", "dblclick")),
              "graph interaction wiring missing")
        check("51g hovering a node highlights its neighbourhood",
              "function highlightNode" in html and ".faded" in html, "no hover highlighting")

        check("51h search results highlight the query and show where the hit sits",
              all(s in html for s in ("function highlight", "<mark", "crumbs")),
              "no highlighting or breadcrumbs in the result card")
        check("51h a hit can jump to the line it matched",
              all(s in html for s in ("function jumpToLine", "data-line", "marked.lexer")),
              "no line anchoring")

        check("51j the page can show a note's history and diff a version",
              all(s in html for s in ('id="hist"', "function showHistory", "function diffLines",
                                      "function restoreVersion")), "no history UI")

        check("51i a slow answer to an old query cannot overwrite a newer one",
              "SEARCH_SEQ" in html and "function runSearch" in html, "no stale-response guard")

        # The three new surfaces exist only once JavaScript runs. These assert the page CARRIES
        # them; test_renders_in_a_browser is what proves they work.
        check("51g the glossary has a place in the page",
              all(s in html for s in ('id="glossary"', "function decorateTerms",
                                      "function openTerm")), "no glossary UI")
        check("51g a known term is decorated in the reading pane, not just listed",
              "a.term" in html and 'className = "term"' in html and "TERMS" in html,
              "no inline term decoration")
        check("51g decoration never touches code, a link or a drawn diagram",
              "pre, code, a, textarea, .fm, .figure, .mermaid" in html,
              "the term walker has no exclusion list")
        check("51h the page can be put into a past date",
              all(s in html for s in ('id="asof"', "function setAsOf", "AS_OF")),
              "no as-of control")
        check("51h a superseded note gets a banner",
              "superseded_by" in html and "supersede" in html.lower(), "no supersede banner")
        check("51j editing renders in place, and can fall back to source",
              all(s in html for s in ("function liveEdit", "function blockSource",
                                      'id="srcmode"', "function pushUndo")),
              "no live editor")
        check("51j the undo stack is bounded, not a leak",
              "UNDO_MAX" in html, "undo stack has no cap")

        check("51k the sidebar can be put away",
              all(s in html for s in ('id="nav"', "function setNav", 'data-nav')),
              "no sidebar toggle")
        check("51k and the layout collapses rather than scrolling sideways on a phone",
              "max-width: 760px" in html or "max-width:760px" in html,
              "no narrow-screen layout")

        check("51m history is a centred dialog, not a panel pinned to a corner",
              all(s in html for s in ('id="history"', 'class="hbox"', 'class="hlist"',
                                      'class="hpreview"')),
              "history has no two-pane dialog")
        check("51m with the versions on one side and the preview on the other",
              "grid-template-columns:260px 1fr" in html.replace(" 260px", "260px")
              or "grid-template-columns: 260px 1fr" in html, "history body is not two columns")
        check("51m and it closes the way a dialog closes",
              "function closeHistory" in html, "no way to dismiss the dialog")

        check("51n the page tells you how much of the vault the search read",
              "read only" in html and "read all" in html and "found.coverage" in html,
              "no coverage line")
        check("51n and says how each hit matched, in words",
              '"in the name"' in html and '"in the text"' in html, "no plain match labels")

        check("51p results are grouped into one card per note, with its matching lines",
              'class="ln"' in html and "byNote" in html, "hits are not grouped by note")
        check("51p and the list can be grown to the real total",
              'id="more"' in html and "SEARCH_K" in html, "no way to see past the first page")

        check("51f the search filters offer completions",
              'list="paths"' in html and 'list="exts"' in html
              and '<datalist id="paths">' in html and '<datalist id="exts">' in html,
              "filters have no datalist")

        test_routes(vault, token)
        test_reader(vault, token)
        test_refusals(vault, token)
        test_write_gates(vault, token)
        test_glossary(vault, token)
        test_as_of(vault, token)
        test_a_vault_searches_note_bodies(vault, token)
        test_every_match_not_just_the_first(vault, token)
        test_images_in_notes(vault, token)
        test_code_is_rendered(vault, token)
        test_installable(vault, token)
        test_sidebar_tree(vault, token)
        test_math(vault, token)
        test_tree_holds_every_file(vault, token)
        test_tree_labels_are_filenames(vault, token)
        test_search_placement(vault, token)
        test_search_status_is_one_line(vault, token)
        test_search_autocompletes_filenames(vault, token)
        test_csv_renders_as_a_table()
        test_tree_has_no_duplicate_rows()
        test_csp_allows_only_what_the_app_needs(vault)
        test_write(vault, token)
    finally:
        stop(server)

    test_read_only(vault)
    test_no_access_code_anywhere(vault)
    test_lan_still_serves_the_laptop(vault)
    test_renders_in_a_browser(vault)

    folder, cache = test_plain_folder()
    test_default_port()
    test_hidden_folders()
    test_source_scan_prunes()
    test_folder_writes(folder, cache)
    test_tags_vault()
    test_tags_in_a_plain_folder()
    test_tags_render_in_a_browser()

    print()
    if _failures:
        print(f"{len(_failures)} failed, {_passed} passed")
        for line in _failures:
            print(f"  - {line}")
        return 1
    print(f"all {_passed} checks passed")
    return 0



# --- opening a folder that is not a vault -----------------------------------------------------
# A docs tree, a cloned repo's docs/, a pile of notes: markdown and .mmd, no .wiki, no graph, no
# manifest, no .rag, no local skill. It must browse, render, search and draw - and above all it
# must not turn somebody's folder into a vault behind their back.

FOLDER_FILES = {
    "guide/install.md": (
        "# Installing\n\nRun the bootstrap script. See [config](config.md).\n\n"
        "```mermaid\nflowchart LR\n  Download --> Verify --> Install\n```\n"
    ),
    "guide/config.md": "# Configuration\n\nThe knob nobody documents is `retry_backoff`.\n",
    # The dangling link matters: documentation prose is full of [example](path.md) references to
    # files that do not exist. They must not be counted as edges, or the footer claims links the
    # graph cannot draw.
    "notes.md": "# Loose note\n\nA thought about idempotency, see [nowhere](missing.md).\n",
    "arch/overview.mmd": "flowchart TD\n  Client --> Server\n",
    "node_modules/junk/readme.md": "# should never be listed\n",
}


def build_folder() -> Path:
    root = Path(tempfile.mkdtemp(prefix="serve-folder-"))
    for rel, text in FOLDER_FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    # A symlink pointing out of the tree. os.walk and rglob both YIELD symlinked files, and
    # `root / rel` then follows the link — so a folder containing one link can hand out a file
    # from anywhere on disk. An arbitrary folder is exactly where this happens.
    outside = Path(tempfile.mkdtemp(prefix="serve-outside-"))
    (outside / "private.md").write_text("# Secret\n\nnot yours to read\n", encoding="utf-8")
    try:
        (root / "leak.md").symlink_to(outside / "private.md")
        (root / "leak.mmd").symlink_to(outside / "private.md")
    except (OSError, NotImplementedError):
        pass
    return root


def start_folder(root: Path, cache: Path, port: int, *extra: str) -> subprocess.Popen:
    server = subprocess.Popen(
        [sys.executable, str(SERVE), "--vault", str(root), "--port", str(port),
         "--cache-dir", str(cache), "--no-fetch", "--no-reindex", *extra],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    for _ in range(60):
        try:
            request("/api/stats", port=port)
            return server
        except OSError:
            if server.poll() is not None:
                out, err = server.communicate()
                raise RuntimeError(f"server died: {err or out}")
            time.sleep(0.2)
    server.kill()
    raise RuntimeError("folder server never came up")


def test_plain_folder() -> None:
    root = build_folder()
    cache = Path(tempfile.mkdtemp(prefix="serve-cache-"))
    (cache / "ui-assets").mkdir(parents=True, exist_ok=True)
    for name, text in FAKE_ASSETS.items():
        (cache / "ui-assets" / name).write_text(text, encoding="utf-8")
    port = PORT + 3
    server = start_folder(root, cache, port)
    try:
        status, stats = get_json("/api/stats", port=port)
        check("80 a folder with no vault still serves", status == 200, str(status))
        check("80 and it says so, rather than pretending to be a vault",
              stats.get("mode") == "folder", str(stats)[:200])
        check("80 it counts what it found by walking",
              stats["notes"] == 3 and stats["diagrams"] == 1, str(stats)[:200])

        # The whole point. graph.connect() does mkdir(parents=True) on <root>/.wiki, so the old
        # code turned any folder it was pointed at into half a vault and THEN exited.
        check("81 no .wiki was created in the folder", not (root / ".wiki").exists(),
              "serve.py wrote .wiki/ into a folder it was only asked to read")
        check("81 nothing at all was added to the folder",
              sorted(p.name for p in root.iterdir()) == ["arch", "guide", "leak.md", "leak.mmd",
                                                         "node_modules", "notes.md"],
              str(sorted(p.name for p in root.iterdir())))

        status, tree = get_json("/api/tree", port=port)
        check("82 the tree is built from the filesystem", status == 200 and len(tree["notes"]) == 3,
              str([n["path"] for n in tree["notes"]]))
        check("82 node_modules is not somebody's notes",
              all("node_modules" not in n["path"] for n in tree["notes"]),
              str([n["path"] for n in tree["notes"]]))
        check("89 a symlink out of the tree is not listed as a note",
              all("leak" not in n["path"] for n in tree["notes"]),
              str([n["path"] for n in tree["notes"]]))
        check("89 nor as a diagram",
              all("leak" not in d["path"] for d in tree["diagrams"]),
              str([d["path"] for d in tree["diagrams"]]))
        status, leaked = get_json("/api/note?path=leak.md", port=port)
        check("89 and it cannot be read through the note route",
              leaked.get("error") == "unknown note" and "not yours" not in json.dumps(leaked),
              str(leaked)[:160])

        check("82 a standalone .mmd is found here too",
              any(d["path"] == "arch/overview.mmd" for d in tree["diagrams"]), str(tree)[:200])

        status, note = get_json("/api/note?path=guide/install.md", port=port)
        check("83 a note opens", status == 200 and note["markdown"].startswith("# Installing"),
              str(note)[:120])
        check("83 its mermaid fence is intact", "```mermaid" in note["markdown"], "fence lost")
        check("83 links become relations without a graph database",
              any(r["path"] == "guide/config.md" for r in note.get("relations", [])),
              str(note.get("relations"))[:200])

        status, back = get_json("/api/note?path=guide/config.md", port=port)
        check("83 and the back-edge is derived too",
              any(r["path"] == "guide/install.md" for r in back.get("backlinks", [])),
              str(back.get("backlinks"))[:200])

        status, found = get_json("/api/search?q=retry_backoff", port=port)
        check("84 the literal scan reports how much it actually looked at",
              found.get("scanned", 0) >= 3, str(found.get("scanned")))
        check("84 a literal hit says which line it matched",
              found["hits"] and found["hits"][0].get("line") == 3,
              str(found["hits"][:1])[:200])
        check("84 search finds a word that is only in the body", status == 200
              and any(h["path"] == "guide/config.md" for h in found["hits"]),
              str(found)[:250])
        check("84 and it names the backend honestly", found["backend"] == "text",
              str(found)[:120])

        status, graph = get_json("/api/graph", port=port)
        check("85 a link to a file that does not exist is not an edge",
              all(e["target"] != "missing.md" for e in graph["edges"]), str(graph["edges"]))
        check("85 and the footer count agrees with what is drawn",
              stats["edges"] == len(graph["edges"]),
              f'stats says {stats["edges"]}, graph draws {len(graph["edges"])}')
        check("85 the graph is derived from the markdown links",
              graph["edges"] and any(e["source"] == "guide/install.md" for e in graph["edges"]),
              str(graph)[:220])

        status, body = request("/assets/mermaid.min.js", port=port)
        check("86 the renderer bundles come from the shared cache, not the folder",
              status == 200 and "fake mermaid" in body, str(status))
    finally:
        stop(server)
    return root, cache


def test_folder_writes(root: Path, cache: Path) -> None:
    """Editing is allowed here too — but the backup goes to the cache, not into their folder."""
    port = PORT + 4
    server = start_folder(root, cache, port)
    try:
        status, html = request("/", port=port)
        token = token_from_page(html)
        status, body = put("guide/config.md", "# Configuration\n\nrewritten.\n", token, port=port)
        check("87 a note in a plain folder can be edited", status == 200, f"{status} {body[:120]}")
        check("87 the file really changed",
              "rewritten." in (root / "guide/config.md").read_text(encoding="utf-8"), "not written")
        check("87 the previous version went to the cache, not the folder",
              not (root / ".wiki").exists()
              and list(cache.glob("trash/*/*/guide/config.md")), "backup in the wrong place")

        status, _ = put("../escape.md", "# no\n", token, port=port)
        check("88 a write outside the folder is refused here too", status == 403, str(status))
        status, _ = put("node_modules/junk/readme.md", "# no\n", token, port=port)
        check("88 and one into an ignored folder", status == 403, str(status))
    finally:
        stop(server)


# --- tags: a tree you can walk, filter by, draw and edit ---------------------------------------
# Its own dummy vault, so the counts the checks above rely on stay what they were. `bank/b.md`
# writes its tags as a block list on purpose: the page must read every form a vault already holds.

TAG_FILES = {
    ".wiki/tags.md": (
        "# Tags\n\n"
        "- `banking` — Running a bank.\n"
        "- `banking/mifid` — EU investor protection.\n"
        "- `banking/mifid/target-market`\n"
        "- `banking/payments` — Moving money.\n"
    ),
    "bank/a.md": "---\ntitle: TM\ntags: [banking/mifid/target-market]\n---\n\n# Target market\n\nSuitability assessment.\n",
    "bank/b.md": "---\ntags:\n  - banking/mifid\n---\n\n# MiFID\n\nInvestor protection.\n",
    "bank/c.md": "---\ntags: [banking/payments]\n---\n\n# Instant payments\n\nA suitability question too.\n",
    "bank/d.md": "---\ntags: [loose/unlisted]\n---\n\n# Loose\n",
    "bank/e.md": "# Untagged\n\nSuitability, with no tag at all.\n",
}


def inventory_of(vault: Path) -> list[str]:
    lines = (vault / ".wiki" / "tags.md").read_text(encoding="utf-8").splitlines()
    return [line.split("`")[1] for line in lines if line.startswith("- `")]


def test_tags_are_served(port: int) -> None:
    status, note = get_json("/api/note?path=bank/a.md", port=port)
    check("135 a note carries its tags", status == 200
          and note.get("tags") == ["banking/mifid/target-market"], str(note.get("tags")))
    status, block = get_json("/api/note?path=bank/b.md", port=port)
    check("135 a block-list note reads the same", block.get("tags") == ["banking/mifid"],
          str(block.get("tags")))
    status, tree = get_json("/api/tree", port=port)
    rows = {n["path"]: n for n in tree["notes"]}
    check("136 tree rows carry tags", rows["bank/c.md"].get("tags") == ["banking/payments"]
          and rows["bank/e.md"].get("tags") == [], str(rows["bank/c.md"]))

    status, tags = get_json("/api/tags", port=port)
    nodes = {n["tag"]: n for n in tags.get("nodes", [])}
    check("137 the tag tree is served with parents, counts and meanings",
          status == 200 and nodes.get("banking", {}).get("notes") == 3
          and nodes["banking/mifid"]["parent"] == "banking"
          and nodes["banking"]["meaning"] == "Running a bank.", str(tags)[:300])
    unlisted = [n["tag"] for n in tags.get("unlisted", [])]
    check("137 nodes only the notes carry are kept apart from the inventory's",
          unlisted == ["loose", "loose/unlisted"] and "loose" not in nodes, str(unlisted))


def test_search_filters_by_tag(port: int) -> None:
    status, wide = get_json("/api/search?q=suitability&tag=banking", port=port)
    paths = sorted({h["path"] for h in wide["hits"]})
    check("138 a tag filter keeps the notes under that node",
          paths == ["bank/a.md", "bank/c.md"], str(paths))
    check("138 and says how many hits it removed", wide.get("tag_hidden", 0) >= 1
          and wide.get("tag") == "banking", str({k: wide.get(k) for k in ("tag", "tag_hidden")}))
    status, narrow = get_json("/api/search?q=suitability&tag=banking/mifid", port=port)
    check("138 a deeper node is narrower",
          sorted({h["path"] for h in narrow["hits"]}) == ["bank/a.md"], str(narrow["hits"])[:200])
    status, listing = get_json("/api/search?q=&tag=banking", port=port)
    check("138 a tag with no words lists the notes under it",
          sorted(h["path"] for h in listing["hits"]) == ["bank/a.md", "bank/b.md", "bank/c.md"]
          and all(h.get("matched_by") == "tag" for h in listing["hits"]), str(listing)[:300])
    status, nothing = get_json("/api/search?q=suitability&tag=../../etc/passwd", port=port)
    check("138 a tag is a KEY: an unknown one finds nothing and breaks nothing",
          status == 200 and nothing["hits"] == [] and nothing.get("reason"), str(nothing)[:200])


def test_tag_queries_and_graph(port: int) -> None:
    status, under = get_json("/api/query?kind=tag&tag=banking", port=port)
    check("139 the tag query is reachable from the page", under.get("count") == 3, str(under)[:200])
    status, level = get_json("/api/query?kind=tag-tree&tag=banking", port=port)
    check("139 and so is one level of the tree",
          sorted(r["tag"] for r in level.get("results", [])) == ["banking/mifid", "banking/payments"],
          str(level)[:200])

    status, whole = get_json("/api/tag-graph", port=port)
    by_id = {n["id"]: n for n in whole.get("nodes", [])}
    check("140 the tag graph has a node per tag, sized by its notes",
          status == 200 and by_id.get("banking", {}).get("notes") == 3
          and by_id["banking/payments"]["kind"] == "tag", str(whole)[:300])
    check("140 and an edge from each parent to its child",
          {"source": "banking", "target": "banking/mifid", "rel_type": "parent-of"} in whole["edges"],
          str(whole["edges"])[:300])
    status, bounded = get_json("/api/tag-graph?limit=1", port=port)
    check("140 the limit bounds it and says so",
          len(bounded["nodes"]) == 1 and bounded["truncated"] is True, str(bounded)[:200])
    status, rooted = get_json("/api/tag-graph?root=banking/mifid&notes=1", port=port)
    kinds = {n["id"]: n["kind"] for n in rooted["nodes"]}
    check("140 a rooted graph can carry its notes as leaves",
          kinds.get("bank/a.md") == "note" and kinds.get("bank/b.md") == "note"
          and "banking/payments" not in kinds, str(kinds))


def test_tags_are_edited_through_the_one_write(vault: Path, token: str, port: int) -> None:
    before = (vault / "bank/a.md").read_text(encoding="utf-8")
    status, body = put("bank/a.md", before, token, port=port, tags=["banking/payments"])
    after = (vault / "bank/a.md").read_text(encoding="utf-8")
    check("141 a write carrying tags succeeds", status == 200, f"{status} {body[:160]}")
    check("141 only the tags line changed",
          after == before.replace("tags: [banking/mifid/target-market]", "tags: [banking/payments]"),
          repr(after))
    backups = sorted((vault / ".wiki" / ".trash").glob("*/bank/a.md"))
    check("141 the previous version went to the trash first",
          len(backups) == 1 and "target-market" in backups[0].read_text(encoding="utf-8"),
          str(backups))

    status, body = put("bank/a.md", after, token, port=port, tags=["banking/cards/debit"])
    added = json.loads(body).get("inventory_added")
    check("142 a tag new to the vault is listed by the same write, parent first",
          status == 200 and added == ["banking/cards", "banking/cards/debit"], body[:200])
    check("142 and lands sorted in the inventory",
          inventory_of(vault) == ["banking", "banking/cards", "banking/cards/debit", "banking/mifid",
                                  "banking/mifid/target-market", "banking/payments"],
          str(inventory_of(vault)))

    trash_before = len(list((vault / ".wiki" / ".trash").glob("*/bank/c.md")))
    c_before = (vault / "bank/c.md").read_text(encoding="utf-8")
    status, body = put("bank/c.md", c_before, token, port=port, tags=["bad:colon"])
    check("142 a malformed tag is refused with 400", status == 400, f"{status} {body[:160]}")
    check("142 and nothing was written or trashed",
          (vault / "bank/c.md").read_text(encoding="utf-8") == c_before
          and len(list((vault / ".wiki" / ".trash").glob("*/bank/c.md"))) == trash_before)

    source = "---\ntags: [regulation/psd2]\n---\n\n# Untagged\n\nNow tagged in source mode.\n"
    status, body = put("bank/e.md", source, token, port=port)
    check("143 a source-mode save enriches the inventory too",
          status == 200 and {"regulation", "regulation/psd2"} <= set(inventory_of(vault)),
          f"{body[:160]} {inventory_of(vault)}")


def test_tags_vault() -> None:
    vault = build_vault(TAG_FILES)
    port = PORT + 8
    server = start(vault, port)
    try:
        status, html = request("/", port=port)
        token = token_from_page(html)
        test_tags_are_served(port)
        test_search_filters_by_tag(port)
        test_tag_queries_and_graph(port)
        test_tags_are_edited_through_the_one_write(vault, token, port)

        check("144 the page has a tag filter, a tag tree and a tag graph tab",
              all(s in html for s in ('id="ftag"', '<datalist id="tagnames">', 'id="tagtree"',
                                      'id="tab-tags"')), "tag markup missing")
        check("144 and the code that fills, routes and draws them",
              all(s in html for s in ("function loadTags", "function openTagListing",
                                      "function drawTagGraph", "function editTags")),
              "tag functions missing")
        check("144 both graphs share one layout, not a copy of it",
              html.count("function drawScene(") == 1 and html.count("function layoutScene(") == 1
              and html.count("d2 < 40000") == 1, "the force layout exists more than once")
    finally:
        stop(server)

    port = PORT + 9
    server = start(vault, port, "--read-only")
    try:
        status, html = request("/", port=port)
        status, body = put("bank/b.md", "x", token_from_page(html), port=port, tags=["banking"])
        check("143 a read-only server refuses a tag edit like any other write", status == 405,
              f"{status} {body[:120]}")
    finally:
        stop(server)


def test_tags_render_in_a_browser() -> None:
    """The tag surfaces exist only once JavaScript has run: chips, the listing, the tree in the
    sidebar, the tag graph. Every one of them passes its server-side check on a page that draws
    nothing, so they are asserted where they are drawn - same opt-in as the other browser checks."""
    real = os.environ.get("WIKI_UI_ASSETS", "")
    chrome = find_chrome()
    if not real or not Path(real).is_dir() or not chrome:
        print("  skip  145-149 tags in a browser — needs WIKI_UI_ASSETS and Chrome, as check 63 does")
        return
    vault = build_vault(TAG_FILES)
    for name in list(FAKE_ASSETS) + ["asset-pins.json"]:
        if not (Path(real) / name).exists():
            print(f"  skip  145-149 tags in a browser — {name} missing from WIKI_UI_ASSETS")
            return
        shutil.copy2(Path(real) / name, vault / ".wiki" / "ui-assets" / name)
    port = PORT + 11
    server = start(vault, port)

    def dump(address: str, signal: str) -> str:
        """The whole DOM once the page has signalled `signal`, or "" if it never did."""
        for budget in (30000, 90000):
            dom = subprocess.run(
                [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--no-first-run",
                 "--no-default-browser-check", f"--virtual-time-budget={budget}", "--dump-dom",
                 f"http://127.0.0.1:{port}/#{address}"],
                capture_output=True, text=True, timeout=180).stdout
            if f'data-rendered="{signal}"' in dom:
                return dom
        return ""

    def region(dom: str, opener: str, closer: str) -> str:
        """One element of the dump. The page's own script names every selector, so a search of
        the whole document is answered by the source as readily as by what was drawn."""
        start_at = dom.find(opener)
        end_at = dom.find(closer, start_at)
        return dom[start_at:end_at] if start_at >= 0 and end_at > start_at else ""

    try:
        dom = dump("bank/a.md", "bank/a.md")
        note = region(dom, '<article id="note"', "</article>")
        check("145 a note's tags are chips linking into the tag tree",
              'class="tagchip"' in note and 'href="#+banking%2Fmifid%2Ftarget-market"' in note,
              "no tag chip in #note")
        check("145 and they left the metadata strip", "<b>tags</b>" not in note and "<b>title</b>" in note,
              "tags still shown as a frontmatter pair")
        check("145 a locked page offers no way to edit them",
              'id="tagadd"' not in note and "data-untag" not in note, "edit controls on a locked page")

        aside = region(dom, "<aside>", "</aside>")
        tree = region(aside, '<div id="tagtree"', "<h2>Vault</h2>")
        check("149 the sidebar holds the tag tree, nested",
              'data-tag="banking"' in tree and 'data-kids="banking"' in tree
              and 'data-tag="banking/mifid/target-market"' in tree, "tag tree not nested")
        check("149 each node shows the notes under it", '<span class="n">3</span>' in tree,
              "no subtree count on the top node")
        check("149 a node the inventory does not list is shown apart",
              'class="tagrow unlisted" data-tag="loose"' in tree, "unlisted node not marked")
        check("149 the tag filter completes from the vault's own tree",
              '<option value="banking/payments">' in region(aside, '<datalist id="tagnames"', "</datalist>"),
              "no tag completions")

        listing = region(dump("+banking", "+banking"), '<article id="note"', "</article>")
        check("146 a tag address lists the notes under it and below it",
              all(f'data-p="bank/{n}.md"' in listing for n in "abc")
              and 'data-p="bank/e.md"' not in listing, "listing is not the tag's subtree")
        check("146 with its meaning and its children", "Running a bank." in listing
              and 'href="#+banking%2Fmifid"' in listing, "no meaning or child chips")

        svg = region(dump("tags", "tags"), '<svg id="g"', "</svg>")
        radius = {m.group(2): float(m.group(1)) for m in
                  re.finditer(r'<circle[^>]*\sr="([\d.]+)"[^>]*data-p="([^"]+)"', svg)}
        check("147 the tag graph draws one node per tag",
              svg.count('data-kind="tag"') == 6 and svg.count('data-kind="note"') == 0, str(radius))
        check("147 a line from each parent to its child", svg.count("<line") == 4,
              f"{svg.count('<line')} lines")
        check("147 a tag with more notes under it is drawn bigger",
              radius.get("banking", 0) > radius.get("loose/unlisted", 99), str(radius))

        rooted = region(dump("tags+banking/mifid", "tags+banking/mifid"), '<svg id="g"', "</svg>")
        check("148 a rooted tag graph hangs that subtree's notes off their tags",
              rooted.count('data-kind="tag"') == 2 and rooted.count('data-kind="note"') == 2
              and 'data-p="bank/b.md"' in rooted, "leaves missing from the rooted graph")
    finally:
        stop(server)


def test_tags_in_a_plain_folder() -> None:
    root = Path(tempfile.mkdtemp(prefix="serve-tagfolder-"))
    for rel, text in TAG_FILES.items():
        if rel.startswith(".wiki"):
            continue
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    cache = Path(tempfile.mkdtemp(prefix="serve-cache-"))
    (cache / "ui-assets").mkdir(parents=True, exist_ok=True)
    for name, text in FAKE_ASSETS.items():
        (cache / "ui-assets" / name).write_text(text, encoding="utf-8")
    port = PORT + 10
    server = start_folder(root, cache, port)
    try:
        status, tags = get_json("/api/tags", port=port)
        unlisted = {n["tag"]: n for n in tags.get("unlisted", [])}
        check("143 a plain folder builds the tag tree from its notes",
              status == 200 and tags.get("nodes") == [] and unlisted.get("banking", {}).get("notes") == 3
              and tags.get("reason"), str(tags)[:300])
        status, html = request("/", port=port)
        status, body = put("bank/e.md", "# Untagged\n", token_from_page(html), port=port,
                           tags=["banking/new"])
        check("143 a tag edit works there", status == 200
              and "tags: [banking/new]" in (root / "bank/e.md").read_text(encoding="utf-8"),
              f"{status} {body[:160]}")
        check("143 and still creates no .wiki in somebody's folder", not (root / ".wiki").exists(),
              "a tag edit turned a plain folder into half a vault")
    finally:
        stop(server)


if __name__ == "__main__":
    sys.exit(main())
