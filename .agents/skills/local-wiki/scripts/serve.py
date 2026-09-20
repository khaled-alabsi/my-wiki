#!/usr/bin/env python3
"""The wiki UI — read the vault, search it, draw its diagrams, edit a note.

    python3 serve.py --vault <vault> --open

One page, bound to 127.0.0.1, that renders a note's markdown and its ```mermaid fences, searches
through the vault's `.rag` index with filters, and shows the graph. It is for the person who owns
the vault; the agent uses `graph.py query --json` and `.rag/bin/rag`, and never opens this.

Four rules, and none of them is negotiable, because this opens a port on a machine that holds
somebody's private notes:

  1. 127.0.0.1 only. Never 0.0.0.0, not even behind "it's just my laptop".
  2. PUT /api/note is the only write. No POST, no DELETE, no rename, no move - restructuring
     stays behind `refactor`'s approval gate, where a human has to accept a plan first.
  3. No parameter is ever passed to open(). A `path` is looked up in the notes table and used as
     a KEY; a server that will read whatever path it is handed is a file-disclosure hole, and
     "it's bound to localhost" is not a defence against a browser tab.
  4. A write proves it came from this server's own page, or it does not happen: the token below,
     a same-origin fetch, and a JSON content type. Any site you have open can POST to localhost;
     none of them can read this page to learn the token.

And one promise on top of those: no edit destroys anything. The previous bytes go to
.wiki/.trash/<timestamp>/<path> before the new ones land, every single time.

Why the re-exec below: the vault's `.rag` workspace owns a venv with the embedding models in it.
Importing `rag_toolkit.api.Index` once keeps those models resident for the life of the process;
shelling out to `.rag/bin/rag` per keystroke would reload them on every query. So if that venv is
there, this process re-launches itself inside it. Nothing else about the server changes - it is
stdlib either way.
"""

from __future__ import annotations

import argparse
import csv
import errno
import hashlib
import io
import json
import os
import re
import socket
import secrets
from html import escape as html_escape
import struct
import zlib
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Each vault's UI gets its OWN port, derived from the vault's path (see `default_port`). A single
# shared constant put every vault on one number: the second server could not bind, and a request
# aimed at one vault silently reached whichever vault got there first.
DEFAULT_PORT_RANGE = (10000, 19999)   # above the well-known ports, below the ephemeral range
TRASH_VERSIONS_KEPT = 20          # per note; the enforcement point is backup_note() below
SEARCH_LIMIT = 50
# Matches shown per note. A note that says the word forty times should be one card with a few
# lines on it, not forty rows that push every other note off the list. The ones past the cap are
# still COUNTED, so the total never lies about how much is there.
MATCHES_PER_FILE = 3
REINDEX_DEBOUNCE = 2.0            # seconds of quiet before the scanners run
REEXEC_GUARD = "WIKI_SERVE_REEXEC"

# Pinned by version AND by hash. A CDN serving different bytes under the same version is exactly
# what a pin is for, and a mismatch aborts rather than caching whatever arrived.
ASSETS = {
    "mermaid.min.js": {
        "url": "https://cdn.jsdelivr.net/npm/mermaid@11.12.0/dist/mermaid.min.js",
        "sha256": "07e37dfa97b337ccc85365d57eddf99b9706f09db3b59b260d0333b23b343c4b",
    },
    "marked.min.js": {
        "url": "https://cdn.jsdelivr.net/npm/marked@15.0.6/marked.min.js",
        "sha256": "8b10a6173d524fc6c97bc9589ba8383e0212d5c0d617e1519e5f4e6a0c9f224f",
    },
    # 127 KB against mermaid's 2.7 MB. A hand-rolled highlighter would be worse at forty languages
    # than this is, and the theme is inlined below rather than fetched, because `style-src` is
    # `'unsafe-inline'` and does NOT include `'self'` - a linked stylesheet would be blocked.
    "highlight.min.js": {
        "url": "https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@11.11.1/highlight.min.js",
        "sha256": "c4a399dd6f488bc97a3546e3476747b3e714c99c57b9473154c6fb8d259b9381",
    },
    # MathJax's SVG build, not KaTeX: it draws glyphs as SVG paths, so it needs no font files at
    # all. KaTeX would need a stylesheet and a dozen woff2 faces, and the page's CSP allows
    # neither a remote stylesheet nor a remote font - the whole point being that a vault renders
    # with no network.
    "tex-svg.js": {
        "url": "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js",
        "sha256": "d4295dc33744836935c1399feece5159577b34c5c8ffb9f1c6324cd82e03a882",
    },
}
PINS_FILE = "asset-pins.json"     # .wiki/ui-assets/asset-pins.json - the hashes actually in use


# --- where things live ------------------------------------------------------------------------

def wiki_dir(vault: Path) -> Path:
    return vault / ".wiki"


def assets_dir(root: Path, cache: Path | None = None) -> Path:
    """A vault keeps its bundles inside itself, so it stays portable - clone it and the diagrams
    still draw offline. A plain folder gets the shared cache instead; it is not ours to write in.
    """
    if cache is None and is_vault(root):
        return wiki_dir(root) / "ui-assets"
    return (cache or shared_cache()) / "ui-assets"


def trash_dir(root: Path, cache: Path | None = None) -> Path:
    """Previous versions of an edited note. In a vault that is `.wiki/.trash/`, beside everything
    else the vault owns. In a plain folder it goes to the shared cache, keyed by the folder: the
    edit itself lands in their file, but the machinery around it never does.
    """
    if cache is None and is_vault(root):
        return wiki_dir(root) / ".trash"
    return (cache or shared_cache()) / "trash" / folder_key(root)


def is_vault(root: Path) -> bool:
    """A vault has machinery; a folder is just markdown someone wrote.

    Checked by what is ON DISK, never by creating anything. `graph.connect()` does a
    `mkdir(parents=True)`, so asking the graph whether a folder is a vault MAKES it one - that is
    exactly how pointing this server at somebody's docs tree used to leave a `.wiki/` behind.
    """
    wiki = root / ".wiki"
    return (wiki / "manifest.json").exists() or (wiki / "graph.sqlite").exists()


def shared_cache(override: str = "") -> Path:
    """Where machinery goes for a folder we must not write into.

    One shared location per machine rather than a sidecar per folder: the folder the user pointed
    at stays exactly as they left it, and the 2.7 MB of renderer bundles is fetched once ever
    instead of once per folder.
    """
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return base / "wiki-ui"


def folder_key(root: Path) -> str:
    """A stable, filesystem-legal name for one folder's cached state.

    The name carries the folder's own name so a person can tell the directories apart, and a hash
    of the absolute path so two folders called `docs` never collide.
    """
    digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:12]
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", root.name).strip("-") or "folder"
    return f"{safe}-{digest}"


def rag_python(vault: Path) -> Path | None:
    """The vault's own interpreter, if `rag` built one here."""
    candidate = vault / ".rag" / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else None


ICON_SIZES = (192, 512)
_ICONS: dict[int, bytes] = {}          # derived: two entries, generated once, never grows


def _png(width: int, height: int, rgba: bytes) -> bytes:
    """A PNG from raw RGBA rows, with zlib and struct and nothing else.

    An installable app needs real raster icons at 192 and 512, and pulling in an image library to
    draw two squares would be a dependency this server has spent its whole life not having.
    """
    raw = b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def app_icon(size: int) -> bytes:
    """The home-screen icon: a rounded square in the page's accent, with three page-lines on it.

    Drawn from arithmetic so it is readable in this file and cannot drift from the palette. Only
    the declared sizes are generated - `size` is a KEY in ICON_SIZES, never a number off a URL.
    """
    if size in _ICONS:
        return _ICONS[size]
    bg, fg = (0x4C, 0x6E, 0xF5), (0xFF, 0xFF, 0xFF)
    radius = size * 0.22
    rows = bytearray()
    bars = [(0.30, 0.62), (0.46, 0.72), (0.62, 0.50)]        # top, width — a note, not a letter
    for y in range(size):
        for x in range(size):
            # Rounded corners: only the corner quadrants are distance-tested.
            cx = radius if x < radius else (size - radius if x > size - radius else x)
            cy = radius if y < radius else (size - radius if y > size - radius else y)
            outside = ((x - cx) ** 2 + (y - cy) ** 2) > radius ** 2
            if outside:
                rows += bytes((0, 0, 0, 0))
                continue
            on_bar = any(top * size <= y < top * size + size * 0.075
                         and size * 0.19 <= x < size * (0.19 + width) for top, width in bars)
            rows += bytes(fg + (255,)) if on_bar else bytes(bg + (255,))
    _ICONS[size] = _png(size, size, bytes(rows))
    return _ICONS[size]


def web_manifest(vault_name: str) -> dict:
    """What a browser reads before it will offer to install the page.

    `id` and `name` both carry the vault, so two vaults on two ports install as two apps rather
    than fighting over one home-screen icon.
    """
    return {
        "id": f"/?vault={vault_name}",
        "name": f"{vault_name} — wiki",
        "short_name": vault_name[:12] or "wiki",
        "description": f"The {vault_name} notes vault: read, search, graph and edit.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "any",
        "background_color": "#fbfbfc",
        "theme_color": "#4c6ef5",
        "icons": [{"src": f"/icon-{n}.png", "sizes": f"{n}x{n}", "type": "image/png",
                   "purpose": "any maskable"} for n in ICON_SIZES],
    }


# Installability wants a worker with a fetch handler. This one caches the two pinned bundles and
# refuses to touch anything else: the page and every API answer are `no-store` because this server
# restarts often, sometimes against a DIFFERENT vault on the same port, and a worker that cached
# them would make that mix-up survive the restart instead of ending with it.
SERVICE_WORKER = """const CACHE = "wiki-bundles-v1";
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", event => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET") return;
  if (!url.pathname.startsWith("/assets/")) return;   // everything else goes to the network
  event.respondWith(caches.open(CACHE).then(cache =>
    cache.match(event.request).then(hit => hit || fetch(event.request).then(response => {
      if (response.ok) cache.put(event.request, response.clone());
      return response;
    }))));
});
"""


LOOPBACK = ("127.0.0.1", "::1", "localhost")


def lan_address() -> str:
    """This machine's address on the network it would use to reach the world.

    The UDP socket is never sent on; connecting it only asks the routing table which interface
    would be used, which is the address a phone on the same network has to type.
    """
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 9))       # TEST-NET-1: reserved, never routed anywhere
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


def resolve_host(value: str) -> str:
    """`lan` binds EVERY interface; anything else is taken as given.

    Not the LAN address alone: binding only that address stops serving 127.0.0.1, so asking to
    reach the vault from a phone would silently take it away from the laptop it is running on.
    The startup line still reports the LAN address, because that is the one to type on the phone.
    """
    return "0.0.0.0" if value == "lan" else value


def default_port(vault: Path) -> int:
    """A stable port derived from this vault's own absolute path.

    Two vaults must never default to the same port. The collision is not merely a failed bind: the
    server that loses the race is gone, and every later request to that number is answered by the
    OTHER vault, so you read someone else's notes believing they are yours. Deriving from the path
    gives each vault a number of its own, the same one on every run, with no registry to keep in
    step and nothing to configure.
    """
    lo, hi = DEFAULT_PORT_RANGE
    digest = hashlib.sha256(str(vault).encode("utf-8")).digest()
    return lo + int.from_bytes(digest[:4], "big") % (hi - lo + 1)


def configured_port(vault: Path, fallback: int) -> int:
    """`.wiki/wiki-config.json` -> `dashboard_port`.

    The vault's committed settings name the port every contributor's UI should open on; the
    constant is only what a folder with no config gets. This read is bounded and cheap - one small
    JSON file, once, at startup - and a malformed or absent config falls back rather than refusing
    to start, because a bad port key is not a reason to be unable to read your notes.
    """
    config = vault / ".wiki" / "wiki-config.json"
    try:
        value = json.loads(config.read_text(encoding="utf-8")).get("dashboard_port")
        return int(value) if isinstance(value, (int, str)) and str(value).isdigit() else fallback
    except (OSError, ValueError, AttributeError):
        return fallback


def maybe_reexec(vault: Path) -> None:
    """Re-launch inside the vault's rag venv, once, so `rag_toolkit` is importable."""
    if os.environ.get(REEXEC_GUARD):
        return
    interpreter = rag_python(vault)
    if interpreter is None or Path(sys.executable).resolve() == interpreter.resolve():
        return
    toolkit = vault / ".rag" / "toolkit"
    if not toolkit.is_dir():
        return
    env = dict(os.environ)
    env[REEXEC_GUARD] = "1"
    env["PYTHONPATH"] = os.pathsep.join([str(toolkit), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    os.execve(str(interpreter), [str(interpreter), os.path.abspath(__file__), *sys.argv[1:]], env)


# --- the two vendored bundles -----------------------------------------------------------------

def read_pins(vault: Path, cache: Path | None = None) -> dict:
    path = assets_dir(vault, cache) / PINS_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def fetch_assets(vault: Path, force: bool = False, cache: Path | None = None) -> list[str]:
    """Download the pinned bundles into .wiki/ui-assets/. The only network call this server makes.

    Derived state: git-ignored, re-fetchable, never read as prose. Deleting the folder costs one
    re-run of this function and nothing else.
    """
    target = assets_dir(vault, cache)
    target.mkdir(parents=True, exist_ok=True)
    pins = read_pins(vault, cache)
    written = []
    for name, spec in ASSETS.items():
        path = target / name
        if path.exists() and not force:
            continue
        print(f"  fetching {name} …", flush=True)
        with urllib.request.urlopen(spec["url"], timeout=120) as response:
            body = response.read()
        digest = hashlib.sha256(body).hexdigest()
        expected = spec["sha256"] or pins.get(name, "")
        if expected and digest != expected:
            raise SystemExit(
                f"{name}: hash mismatch — expected {expected}, got {digest}. Refusing to cache it."
            )
        path.write_bytes(body)
        pins[name] = digest
        written.append(f"{name} ({len(body) // 1024} KB, sha256 {digest[:12]}…)")
    (target / PINS_FILE).write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    return written


def verify_asset(vault: Path, name: str, cache: Path | None = None) -> bytes | None:
    """Read one cached bundle, refusing it if its bytes no longer match the recorded pin."""
    if name not in ASSETS:
        return None
    path = assets_dir(vault, cache) / name
    if not path.exists():
        return None
    body = path.read_bytes()
    pinned = read_pins(vault, cache).get(name, "")
    if pinned and hashlib.sha256(body).hexdigest() != pinned:
        return None
    return body


# --- the graph half, borrowed whole ------------------------------------------------------------
# graph.py owns every question about relations. Importing it keeps one implementation behind two
# front doors - the CLI the agent uses and the page a person opens.

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graph  # noqa: E402
import scan_vault  # noqa: E402
import tags as tag_tool  # noqa: E402  (`tags` is what every payload calls a note's own list)


# --- reading ------------------------------------------------------------------------------------

def note_paths(conn) -> set[str]:
    return {row["path"] for row in conn.execute("SELECT path FROM notes").fetchall()}


def inside(root: Path, rel: str) -> Path | None:
    """The real file `rel` names, or None if it is not actually inside `root`.

    `os.walk` and `rglob` both YIELD symlinked FILES, and `root / rel` then follows the link - so a
    folder containing one symlink can hand out a file from anywhere on disk. That is tolerable in
    a vault somebody built; it is not tolerable when the root is a directory the user merely
    pointed at. Resolving both ends and comparing is the whole guard.
    """
    try:
        target = (root / rel).resolve()
        if target.is_relative_to(root.resolve()) and target.is_file():
            return target
    except (OSError, ValueError, RuntimeError):
        return None
    return None


def in_a_working_folder(rel: str) -> bool:
    """True when any FOLDER on the way to this file starts with `.` or `_`.

    A leading dot or underscore on a directory is the long-standing way to say "not content" -
    drafts, scratch, archives, tooling. The sidebar lists what the vault is about, so those stay
    out of it. The filename itself is not judged: `_index.md` inside a real folder is a note.

    Hiding is a LISTING decision, not an access one. `/api/note` still serves such a file when a
    link or the address bar asks for it by name - a note you can reach but cannot browse to is
    surprising; a note that vanishes when something links to it is broken.
    """
    return any(part.startswith((".", "_")) for part in rel.split("/")[:-1])


_DIAGRAM_CACHE: dict[str, tuple[float, list[str]]] = {}
DIAGRAM_TTL = 5.0


def _walk_content(vault: Path):
    """Yield `(relative directory, filenames)` for the vault's content tree, pruning as it descends.

    One pass, and excluded directories are cut at the directory level so their contents are never
    visited. Filtering AFTER a walk looks equivalent and is not: the walker still has to enter
    every directory it later discards. Doing that once per file extension multiplied the cost by
    the size of the extension table - measured at 24 seconds on a repository whose virtualenv the
    scan had no business entering, paid twice on every `/api/stats`.

    The pruning rule is the same one `in_a_working_folder` states: a directory whose name starts
    with `.` or `_` is not content. Because it is applied here, neither caller needs to re-check it.
    """
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in FORBIDDEN_SEGMENTS
                             and not d.startswith(".")
                             and not d.startswith("_"))
        rel_dir = Path(dirpath).relative_to(vault).as_posix()
        yield ("" if rel_dir == "." else rel_dir), filenames


def find_diagrams(vault: Path) -> list[str]:
    """Standalone `.mmd` files, relative to the vault.

    They are not notes - `scan_vault.py` never sees them and they carry no links - but they are
    diagrams somebody drew, and a UI that renders fences while hiding whole diagram files is
    rendering half the vault. Cached briefly: a full walk per request scales with the vault.
    """
    key = str(vault)
    now = time.monotonic()
    cached = _DIAGRAM_CACHE.get(key)
    if cached and now - cached[0] < DIAGRAM_TTL:
        return cached[1]
    found = []
    for rel_dir, filenames in _walk_content(vault):
        for name in filenames:
            if not name.endswith(".mmd"):
                continue
            rel = f"{rel_dir}/{name}" if rel_dir else name
            if inside(vault, rel) is None:
                continue      # a symlink pointing out of the tree is not this folder's diagram
            found.append(rel)
    found.sort()
    _DIAGRAM_CACHE[key] = (now, found)
    return found


_GLOSSARY_CACHE: dict[str, tuple[float, list[dict]]] = {}
GLOSSARY_TTL = 5.0
GLOSSARY_HEADING = "## business glossary"

# `- **PIP** (aka PEP) — Product Information Paper. The one-line meaning. → `path/to/note.md``
# The em-dash and arrow are what references/glossary.md specifies; the ASCII forms are accepted
# because a person editing the index in a hurry types those and means the same thing.
GLOSSARY_ENTRY_RE = re.compile(
    r"^\s*[-*+]\s+\*\*(?P<term>[^*]+?)\*\*"
    r"(?:\s*\((?:aka|a\.k\.a\.)\s*(?P<aliases>[^)]*)\))?"
    r"\s*(?:\u2014|\u2013|--|-)\s*(?P<rest>.+?)\s*$")
GLOSSARY_SOURCE_RE = re.compile(r"\s*(?:\u2192|->)\s*`(?P<source>[^`]+)`\s*\.?\s*$")
GLOSSARY_INFERRED_RE = re.compile(r"\s*\((?:inferred[^)]*)\)\s*")


def parse_glossary_entry(line: str) -> dict | None:
    """One glossary line, in the grammar references/glossary.md fixes: term, aliases, expansion,
    one-line meaning, source. Anything that is not that shape is prose and is skipped.

    The expansion is only split off for an ACRONYM. `**Themenblock** — Micro-frontend fragment...`
    has no expansion, and calling its meaning one would put the same sentence in both fields.
    """
    match = GLOSSARY_ENTRY_RE.match(line)
    if not match:
        return None
    term = match.group("term").strip()
    aliases = [a.strip() for a in (match.group("aliases") or "").replace(";", ",").split(",")
               if a.strip()]
    rest = match.group("rest")

    source = ""
    found = GLOSSARY_SOURCE_RE.search(rest)
    if found:
        source = found.group("source").strip()
        rest = rest[:found.start()].rstrip()

    status = "defined"
    if GLOSSARY_INFERRED_RE.search(rest):
        status = "inferred"
        rest = GLOSSARY_INFERRED_RE.sub(" ", rest).strip()
    elif rest.lower().startswith("undefined in the vault"):
        status = "undefined"

    expansion, meaning = "", rest.strip()
    if sum(1 for c in term if c.isupper()) >= 2 and status != "undefined":
        head, dot, tail = meaning.partition(". ")
        if dot:
            expansion, meaning = head.strip(), tail.strip()
        else:
            expansion, meaning = meaning.rstrip("."), ""
    return {"term": term, "aliases": aliases, "expansion": expansion, "meaning": meaning,
            "status": status, "source": source}


def read_glossary(root: Path, index_name: str = "index.md") -> tuple[list[dict], str]:
    """The `## Business Glossary` section of the index, and nothing else in that file.

    Access class: SLICED. The index is a budgeted routing map whose other sections are a folder
    listing this has no use for, so the read stops at the next `##`. Reading the whole file to
    find fifty lines is the habit that turns a routing map into a context bill.

    Growth class: derived - in memory, TTL-bounded, rebuilt from the file it came from.
    """
    key = f"{root}|{index_name}"
    now = time.monotonic()
    cached = _GLOSSARY_CACHE.get(key)
    if cached and now - cached[0] < GLOSSARY_TTL:
        return cached[1], ""
    path = inside(root, index_name)
    if path is None:
        return [], f"no {index_name} in this folder"
    entries: list[dict] = []
    try:
        with path.open(encoding="utf-8") as handle:
            inside_section = False
            for line in handle:
                heading = line.strip().lower()
                if heading.startswith("## "):
                    if inside_section:
                        break                 # the next section begins; the slice is complete
                    inside_section = heading == GLOSSARY_HEADING
                    continue
                if inside_section:
                    entry = parse_glossary_entry(line)
                    if entry:
                        entries.append(entry)
    except (OSError, UnicodeDecodeError) as exc:
        return [], f"{index_name} is unreadable ({type(exc).__name__})"
    entries.sort(key=lambda e: e["term"].lower())
    _GLOSSARY_CACHE[key] = (now, entries)
    return entries, "" if entries else f"{index_name} has no ## Business Glossary entries yet"


def superseded_by(payload: dict, titles: dict) -> dict | None:
    """The note that replaced this one, if the author declared it.

    Shown in EVERY mode, not only while time-travelling: "this was replaced" is the one thing a
    reader most needs to know before acting on a note, and it is already in the graph as a typed
    relation. The successor is named by its TITLE - a reader recognises `MiFID II`, not a path.
    """
    for relation in payload.get("relations", []):
        if relation.get("direction") == "out" and relation.get("rel_type") == "superseded-by":
            target = relation.get("path", "")
            return {"path": target,
                    "title": titles.get(target) or relation.get("text") or target}
    return None


_MEDIA_CACHE: dict[str, tuple[float, dict]] = {}
MEDIA_TTL = 5.0
MEDIA_MAX_BYTES = 25 * 1024 * 1024
# Raster only, on purpose. An SVG is a document that can carry script, and it would be served from
# this origin; a screenshot pasted into a note is what vaults actually hold, and `.mmd` already
# covers drawings. Admitting SVG is a deliberate decision with a CSP consequence, not a default.
MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".gif": "image/gif", ".webp": "image/webp", ".avif": "image/avif",
               ".bmp": "image/bmp", ".ico": "image/x-icon"}


def find_media(root: Path) -> dict:
    """Every image in the vault, relative path -> content type.

    The same allowlist discipline `find_diagrams()` gives `.mmd` files, for the same reason: a
    requested path is a KEY in this map and never a string handed to open(). Cached briefly - an
    rglob per <img> would scale with the vault and a note can hold a dozen images.

    Growth class: derived. In memory, TTL-bounded, rebuilt from the filesystem.
    """
    key = str(root)
    now = time.monotonic()
    cached = _MEDIA_CACHE.get(key)
    if cached and now - cached[0] < MEDIA_TTL:
        return cached[1]
    found: dict = {}
    for suffix, ctype in MEDIA_TYPES.items():
        for path in root.rglob(f"*{suffix}"):
            rel = path.relative_to(root).as_posix()
            if any(part in FORBIDDEN_SEGMENTS or part.startswith(".")
                   for part in Path(rel).parts):
                continue
            # For a note, a leading dot or underscore on a folder hides it from the SIDEBAR and
            # `/api/note` still serves it. For media it has to hide it from ACCESS too: an <img>
            # is a fetch, so a working-folder image would otherwise be a way to read a file the
            # vault deliberately does not show.
            if in_a_working_folder(rel) or Path(rel).parent.name.startswith(("_", ".")):
                continue
            if inside(root, rel) is None:
                continue          # a symlink out of the tree is not this vault's image
            found[rel] = ctype
    _MEDIA_CACHE[key] = (now, found)
    return found


_SOURCE_CACHE: dict[str, tuple[float, dict]] = {}
SOURCE_TTL = 5.0
SOURCE_MAX_BYTES = 2 * 1024 * 1024
# Extension -> the language name highlight.js knows it by. A source file beside the notes is not a
# note - it has no links and no index entry - but it is something somebody put in the vault on
# purpose, and a UI that will not open it is hiding part of the vault, exactly as it did with .mmd.
SOURCE_LANGS = {
    ".py": "python", ".js": "javascript", ".mjs": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".jsx": "javascript", ".java": "java", ".kt": "kotlin",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php", ".cs": "csharp",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp", ".swift": "swift",
    ".sh": "bash", ".bash": "bash", ".zsh": "bash", ".sql": "sql", ".r": "r",
    ".yml": "yaml", ".yaml": "yaml", ".json": "json", ".toml": "ini", ".ini": "ini",
    ".xml": "xml", ".html": "xml", ".css": "css", ".scss": "scss", ".txt": "plaintext",
    # Rendered as a TABLE rather than fenced - see `csv_table`.
    ".csv": "csv", ".tsv": "csv",
}

CSV_MAX_ROWS = 500                # a results file can carry tens of thousands; the cap says so


def find_sources(vault: Path) -> dict:
    """Source files in the vault, relative path -> language. A requested path is a KEY here.

    Growth class: derived. In memory, TTL-bounded, rebuilt from the filesystem.
    """
    key = str(vault)
    now = time.monotonic()
    cached = _SOURCE_CACHE.get(key)
    if cached and now - cached[0] < SOURCE_TTL:
        return cached[1]
    found: dict = {}
    for rel_dir, filenames in _walk_content(vault):
        for name in filenames:
            lang = SOURCE_LANGS.get(Path(name).suffix.lower())
            if lang is None:
                continue
            rel = f"{rel_dir}/{name}" if rel_dir else name
            if inside(vault, rel) is None:
                continue
            found[rel] = lang
    _SOURCE_CACHE[key] = (now, found)
    return found


def csv_table(body: str, delimiter: str) -> str:
    """A CSV as a markdown table, capped, with the cap stated.

    A results file is a table somebody produced. Fenced as plain text the reader has to line the
    columns up by eye, while the page already carries a renderer that draws tables properly.
    """
    rows = list(csv.reader(io.StringIO(body), delimiter=delimiter))
    rows = [r for r in rows if any(cell.strip() for cell in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)

    def cell(value: str) -> str:
        # A pipe inside a value would end the column early, and a newline would end the row.
        return value.replace("|", "\\|").replace("\n", " ").strip() or " "

    def line(values) -> str:
        padded = list(values) + [""] * (width - len(values))
        return "| " + " | ".join(cell(v) for v in padded) + " |"

    head, rest = rows[0], rows[1:]
    shown = rest[:CSV_MAX_ROWS]
    out = [line(head), "| " + " | ".join(["---"] * width) + " |"]
    out += [line(r) for r in shown]
    if len(rest) > len(shown):
        out.append("")
        out.append(f"_showing the first {len(shown)} of {len(rest)} rows._")
    return "\n".join(out) + "\n"


def read_source(vault: Path, rel: str) -> dict:
    """One source file, fenced in its own language so the page renders it with the code path it
    already has. `rel` is a KEY in find_sources(), never a path handed to open()."""
    lang = find_sources(vault).get(rel)
    if lang is None:
        return {}
    real = inside(vault, rel)
    if real is None or real.stat().st_size > SOURCE_MAX_BYTES:
        return {}
    try:
        body = real.read_text(encoding="utf-8").rstrip("\n")
    except (OSError, UnicodeDecodeError):
        return {}
    if lang == "csv":
        rendered = csv_table(body, "\t" if rel.endswith(".tsv") else ",")
    else:
        rendered = f"```{lang}\n{body}\n```\n"
    return {"path": rel, "title": rel.rsplit("/", 1)[-1], "kind": "source", "lang": lang,
            "markdown": rendered, "body": rendered,
            "source": body, "frontmatter": [], "relations": [], "backlinks": [], "concepts": []}


def hidden_folders(vault: Path) -> tuple[str, ...]:
    """Folders the owner asked the UI not to list: `.wiki/wiki-config.json` -> `hidden_folders`.

    A vault often carries material that is kept but not worked in - a frozen catalog, a retired
    tree - and listing it in the sidebar buries the folders somebody actually opens. Naming them
    in the config keeps the decision with the vault, so it survives a regenerated skill and is not
    a name baked into this script.

    Hiding is a LISTING decision only, exactly as `in_a_working_folder` says: `/api/note` still
    serves a hidden note when a link or the address bar names it. A note that vanishes the moment
    something links to it is broken, not tidy.
    """
    config = vault / ".wiki" / "wiki-config.json"
    try:
        value = json.loads(config.read_text(encoding="utf-8")).get("hidden_folders")
    except (OSError, ValueError, AttributeError):
        return ()
    if not isinstance(value, list):
        return ()
    return tuple(str(v).strip("/") for v in value if isinstance(v, str) and str(v).strip("/"))


def is_hidden(rel: str, hidden: tuple[str, ...]) -> bool:
    """True when `rel` sits inside one of the hidden folders.

    Matched on whole path SEGMENTS, never as a string prefix: `archive` must not hide
    `archived-later/`, and a config entry may name a nested folder such as `old/drafts`.
    """
    return any(rel == h or rel.startswith(h + "/") for h in hidden)


def build_tree(conn, vault: Path, as_of: str | None = None) -> dict:
    rows = [dict(r) for r in conn.execute(
        "SELECT path, title, valid_from, valid_until FROM notes ORDER BY path").fetchall()]
    hidden_in = hidden_folders(vault)
    rows = [r for r in rows
            if not in_a_working_folder(r["path"]) and not is_hidden(r["path"], hidden_in)]
    # Hiding without a count is how a tree quietly lies about what the vault holds.
    before = len(rows)
    rows = [r for r in rows if graph.in_window(r, as_of)]
    hidden = before - len(rows)
    folders = sorted({r["path"].rsplit("/", 1)[0] for r in rows if "/" in r["path"]})
    tags_by_note: dict = {}
    for tagged in conn.execute("SELECT path, tag FROM note_tags ORDER BY tag").fetchall():
        tags_by_note.setdefault(tagged["path"], []).append(tagged["tag"])
    for row in rows:
        row["folder"] = row["path"].rsplit("/", 1)[0] if "/" in row["path"] else ""
        row["tags"] = tags_by_note.get(row["path"], [])
    diagrams = [{"path": d, "title": d.rsplit("/", 1)[-1][:-4],
                 "folder": d.rsplit("/", 1)[0] if "/" in d else ""}
                for d in find_diagrams(vault) if not is_hidden(d, hidden_in)]
    folders = sorted(set(folders) | {d["folder"] for d in diagrams if d["folder"]})
    sources = [{"path": s, "title": s.rsplit("/", 1)[-1], "lang": lang,
                "folder": s.rsplit("/", 1)[0] if "/" in s else ""}
               for s, lang in sorted(find_sources(vault).items()) if not is_hidden(s, hidden_in)]
    folders = sorted(set(folders) | {s["folder"] for s in sources if s["folder"]})
    return {"folders": folders, "notes": rows, "diagrams": diagrams, "sources": sources,
            "as_of": as_of or "", "hidden": hidden}


def split_front_matter(text: str) -> tuple[list[list[str]], str]:
    """Separate a note's YAML frontmatter from its prose.

    Returns ordered [key, value] pairs and the body. The pairs are for DISPLAY - the page shows
    them as a metadata strip instead of letting a markdown renderer turn `---` into a rule and the
    keys into a paragraph, which is what the reader was seeing.

    `scan_vault.parse_front_matter_full` deliberately keeps only temporal values, because the
    manifest is a routing artifact and not a copy of the vault. This one is the opposite job -
    everything, for one note, on its way to a browser - so it is its own small parser rather than
    a loosening of that rule.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text
    for i in range(1, min(len(lines), 200)):
        if lines[i].strip() in ("---", "..."):
            pairs = []
            for raw in lines[1:i]:
                stripped = raw.strip()
                if not stripped or stripped.startswith("#") or raw.startswith((" ", "\t")):
                    continue
                key, sep, value = stripped.partition(":")
                if sep:
                    pairs.append([key.strip(), value.strip().strip("'\"")])
            return pairs, "\n".join(lines[i + 1:]).lstrip("\n")
    return [], text          # an unterminated block is not frontmatter, it is content


# --- tags ---------------------------------------------------------------------------------------
# A tag is a full path in the vault's tag tree (references/tagging.md). graph.py builds the tree
# and its counts; tags.py is the only writer. What is here is the shaping both corpora share, so a
# vault and a plain folder answer the page in one form.

NO_INVENTORY = "this vault has no tag inventory yet - the tree is built from what the notes carry"
FOLDER_TAGS = "plain folder - no tag inventory; the tree is built from what the notes carry"


def read_live_tags(text: str) -> list[str]:
    """A note's tags from its own bytes, so a chip is right before the debounced reindex lands."""

    note_tags, _bad_tags = scan_vault.parse_tags(text.splitlines())

    return note_tags


def build_tag_tree_payload(index: dict, reason: str) -> dict:
    """What the inventory LISTS, and apart from it what the notes merely carry. Never merged: an
    unlisted node has no meaning line and nobody decided it belongs in the tree."""

    ordered = sorted(index.values(), key=lambda entry: tuple(entry["tag"].split(graph.TAG_SEPARATOR)))
    nodes = [entry for entry in ordered if entry["listed"]]
    unlisted = [entry for entry in ordered if not entry["listed"]]

    return {"nodes": nodes, "unlisted": unlisted, "source": ".wiki/tags.md",
            "reason": "" if nodes else reason}


def list_tagged_notes(corpus, allowed: set, tag: str, k: int) -> dict:
    """The notes under a tag, in the shape of a search answer, for a tag asked for with no words."""

    rows = [row for row in corpus.tree()["notes"] if row["path"] in allowed]
    hits = [{"path": row["path"], "title": row.get("title", ""), "kind": "note", "score": None,
             "matched_by": "tag", "heading_path": "", "citation": row["path"], "line": None,
             "openable": True, "text": ", ".join(row.get("tags") or [])} for row in rows]

    return {"backend": "tags", "hits": hits[:k], "scanned": len(rows), "total": len(hits),
            "truncated": len(hits) > k,
            "reason": "" if hits else f"no note carries `{tag}` or anything under it"}


def read_diagram(vault: Path, rel: str) -> dict:
    """One `.mmd` file, wrapped in a fence so the page renders it with the same code path as a
    fence inside a note. `rel` is a KEY in find_diagrams(), never a path handed to open()."""
    if rel not in find_diagrams(vault):
        return {}
    body = (vault / rel).read_text(encoding="utf-8").strip("\n")
    wrapped = f"```mermaid\n{body}\n```\n"
    return {"path": rel, "title": rel.rsplit("/", 1)[-1][:-4], "kind": "diagram",
            "markdown": wrapped, "body": wrapped, "frontmatter": [], "source": body,
            "relations": [], "backlinks": [], "concepts": []}


def read_note(vault: Path, conn, rel: str, as_of: str | None = None) -> dict:
    """The note's own bytes. `rel` is validated as a KEY first — it never reaches open() unchecked."""
    if rel.endswith(".mmd"):
        return read_diagram(vault, rel)
    if Path(rel).suffix.lower() in SOURCE_LANGS:
        return read_source(vault, rel)
    payload = graph.serve_node(conn, rel)
    if not payload:
        return {}
    path = inside(vault, rel)
    if path is None:
        return {}             # in the table, but the file resolves outside the root

    try:
        text = path.read_text(encoding="utf-8")
        # `markdown` stays the WHOLE file: it is what the editor loads and saves back, and an
        # editor that silently drops a note's frontmatter is a data-loss bug, not a display one.
        payload["markdown"] = text
        payload["frontmatter"], payload["body"] = split_front_matter(text)
        payload["tags"] = read_live_tags(text)
    except (OSError, UnicodeDecodeError) as exc:
        payload["markdown"] = payload["body"] = ""
        payload["frontmatter"] = []
        payload["tags"] = []
        payload["error"] = f"unreadable: {type(exc).__name__}"
    payload["backlinks"] = [r for r in payload.get("relations", []) if r.get("direction") == "in"]
    payload["kind"] = "note"
    titles = {row["path"]: row["title"] for row in
              conn.execute("SELECT path, title FROM notes").fetchall()}
    payload["superseded_by"] = superseded_by(payload, titles)
    payload["valid_now"] = graph.in_window(payload, as_of)
    return payload


class VaultCorpus:
    """A vault: the notes table, the typed relation graph, the glossary, the semantic index.

    Everything the UI knew how to do before, unchanged - it just now says its name.
    """

    mode = "vault"

    def __init__(self, root: Path) -> None:
        self.root = root

    def _conn(self):
        return graph.connect(self.root)

    def tree(self, as_of: str | None = None) -> dict:
        conn = self._conn()
        try:
            return build_tree(conn, self.root, as_of)
        finally:
            conn.close()

    def note(self, rel: str, as_of: str | None = None) -> dict:
        conn = self._conn()
        try:
            return read_note(self.root, conn, rel, as_of)
        finally:
            conn.close()

    def valid_paths(self, as_of: str | None) -> set | None:
        """Which notes existed on that date. None means "no date asked, filter nothing"."""
        if not as_of:
            return None
        conn = self._conn()
        try:
            return {r["path"] for r in conn.execute(
                "SELECT path, valid_from, valid_until FROM notes").fetchall()
                if graph.in_window(r, as_of)}
        finally:
            conn.close()

    def glossary(self, index_name: str = "index.md") -> dict:
        """The vault's own vocabulary: what the index DEFINES, and separately what the scanner SAW.

        They are never merged. `terms` are the owner's definitions; `candidates` are machine
        guesses with no glossary line yet. Presenting the second as the first would put words the
        vault never defined into its glossary, which is the one thing glossary.md forbids.
        """
        entries, reason = read_glossary(self.root, index_name)
        conn = self._conn()
        try:
            counts = {r["term"]: r["n"] for r in conn.execute(
                "SELECT term, COUNT(*) AS n FROM concept_edges GROUP BY term").fetchall()}
            seen = {r["term"] for r in conn.execute("SELECT term FROM concepts").fetchall()}
        finally:
            conn.close()
        known = {e["term"] for e in entries} | {a for e in entries for a in e["aliases"]}
        for entry in entries:
            entry["mentions"] = counts.get(entry["term"], 0) + sum(
                counts.get(a, 0) for a in entry["aliases"])
        candidates = sorted(
            ({"term": term, "mentions": counts.get(term, 0)} for term in seen if term not in known),
            key=lambda c: (-c["mentions"], c["term"].lower()))
        return {"terms": entries, "candidates": candidates, "source": index_name,
                "reason": reason}

    def stats(self, as_of: str | None = None) -> dict:
        conn = self._conn()
        try:
            payload = graph.serve_stats(conn)
            visible = build_tree(conn, self.root, as_of)
        finally:
            conn.close()
        payload["notes"] = len(visible["notes"])
        payload["diagrams"] = len(visible["diagrams"])
        payload["folders"] = [f for f in payload.get("folders", [])
                              if not f["folder"].startswith(("_", "."))]
        return payload

    def graph_payload(self, folder: str, rel_type: str, as_of, limit: int) -> dict:
        conn = self._conn()
        try:
            return graph.graph_payload(conn, folder, rel_type, as_of, limit)
        finally:
            conn.close()

    def node(self, rel: str, as_of: str | None = None) -> dict:
        conn = self._conn()
        try:
            payload = graph.serve_node(conn, rel)
            if payload:
                titles = {r["path"]: r["title"] for r in
                          conn.execute("SELECT path, title FROM notes").fetchall()}
                payload["superseded_by"] = superseded_by(payload, titles)
                payload["valid_now"] = graph.in_window(payload, as_of)
            return payload
        finally:
            conn.close()

    def concepts(self, limit: int) -> list:
        conn = self._conn()
        try:
            return [dict(r) for r in conn.execute(
                "SELECT c.term, c.definition, c.status, c.defined_in, "
                "(SELECT COUNT(*) FROM concept_edges e WHERE e.term = c.term) AS notes "
                "FROM concepts c ORDER BY notes DESC, c.term LIMIT ?", (limit,)).fetchall()]
        finally:
            conn.close()

    def query(self, params: dict, limit: int, as_of) -> dict:
        conn = self._conn()
        try:
            return graph.api_query(conn, self.root, params, limit, as_of)
        finally:
            conn.close()

    def sqlite_search(self, term: str, k: int) -> list:
        conn = self._conn()
        try:
            return graph.serve_search(conn, term, k)
        finally:
            conn.close()

    def _load_listed_note_tags(self, conn, as_of: str | None) -> list:
        """(tag, note) pairs for the notes the tree lists - a hidden or working folder's notes
        are not counted under a tag they cannot be reached from."""
        hidden_in = hidden_folders(self.root)
        return [(tag, path) for tag, path in graph.load_note_tags(conn, as_of)
                if not in_a_working_folder(path) and not is_hidden(path, hidden_in)]

    def build_tag_tree(self, as_of: str | None = None) -> dict:
        conn = self._conn()
        try:
            index = graph.build_tag_index(self._load_listed_note_tags(conn, as_of), graph.load_listed_tags(conn))
        finally:
            conn.close()
        return build_tag_tree_payload(index, NO_INVENTORY)

    def find_tagged_paths(self, node: str, as_of: str | None = None) -> set:
        """The notes under a tag node. `node` is a KEY matched against tags, never a path."""
        conn = self._conn()
        try:
            return {row["path"] for row in
                    graph.find_notes_under_tag(self._load_listed_note_tags(conn, as_of), node)}
        finally:
            conn.close()

    def build_tag_graph(self, root: str, notes: bool, as_of: str | None, limit: int) -> dict:
        conn = self._conn()
        try:
            note_tags = self._load_listed_note_tags(conn, as_of)
            index = graph.build_tag_index(note_tags, graph.load_listed_tags(conn))
            titles = {r["path"]: r["title"] for r in conn.execute("SELECT path, title FROM notes")}
        finally:
            conn.close()
        return graph.build_tag_graph(index, note_tags, titles,
                                     root.casefold().strip(graph.TAG_SEPARATOR), notes, limit)


class FolderCorpus:
    """Any folder of markdown: no `.wiki`, no database, no semantic index, nothing written.

    The whole index is `scan_vault.walk()` held in memory. That function already returns each
    file's title, headings, outbound links WITH their relation types, and its frontmatter keys, and
    already skips `node_modules`, `dist`, `build`, `target`, `venv` and `.git` - so a docs tree gets
    a real tree and a real link graph without this server writing a byte or duplicating a parser.

    Growth class: derived, in memory only, rebuilt from the filesystem. Bounded by a TTL so a long
    session does not walk a large tree on every keystroke, and invalidated outright after a write.
    """

    mode = "folder"
    TTL = 4.0

    def __init__(self, root: Path) -> None:
        self.root = root
        self._at = 0.0
        self._records: list = []
        self._graph: dict = {}
        self._backlinks: dict = {}
        self._lock = threading.Lock()

    def refresh(self) -> None:
        self._at = 0.0

    def records(self) -> list:
        with self._lock:
            now = time.monotonic()
            if self._records and now - self._at < self.TTL:
                return self._records
            records = [r for r in scan_vault.walk(str(self.root))
                       if r["ext"] in (".md", ".markdown", ".mdx")
                       and not in_a_working_folder(r["path"])
                       and inside(self.root, r["path"]) is not None]
            self._graph, self._backlinks = scan_vault.build_graph(records)
            self._records = records
            self._at = now
            return records

    def _title(self, record: dict) -> str:
        return record.get("h1") or record["path"].rsplit("/", 1)[-1]

    def tree(self, as_of: str | None = None) -> dict:
        rows = [{"path": r["path"], "title": self._title(r),
                 "valid_from": r.get("valid_from"), "valid_until": r.get("valid_until"),
                 "folder": r["path"].rsplit("/", 1)[0] if "/" in r["path"] else "",
                 "tags": r.get("tags") or []}
                for r in self.records()]
        before = len(rows)
        rows = [r for r in rows if graph.in_window(r, as_of)]
        hidden = before - len(rows)
        diagrams = [{"path": d, "title": d.rsplit("/", 1)[-1][:-4],
                     "folder": d.rsplit("/", 1)[0] if "/" in d else ""}
                    for d in find_diagrams(self.root)]
        folders = sorted({r["folder"] for r in rows if r["folder"]}
                         | {d["folder"] for d in diagrams if d["folder"]})
        sources = [{"path": s, "title": s.rsplit("/", 1)[-1], "lang": lang,
                    "folder": s.rsplit("/", 1)[0] if "/" in s else ""}
                   for s, lang in sorted(find_sources(self.root).items())]
        folders = sorted(set(folders) | {s["folder"] for s in sources if s["folder"]})
        return {"folders": folders, "notes": rows, "diagrams": diagrams, "sources": sources,
                "as_of": as_of or "", "hidden": hidden}

    def valid_paths(self, as_of: str | None) -> set | None:
        if not as_of:
            return None
        return {r["path"] for r in self.records() if graph.in_window(r, as_of)}

    def glossary(self, index_name: str = "index.md") -> dict:
        """A plain folder has no concepts table. If it happens to carry an index with a glossary
        section, that is still the owner's own vocabulary and is served; otherwise the answer says
        why it is empty rather than looking like a vault with nothing in it."""
        entries, reason = read_glossary(self.root, index_name)
        for entry in entries:
            entry["mentions"] = 0
        return {"terms": entries, "candidates": [], "source": index_name,
                "reason": reason or "plain folder — no concept index, so no candidates"}

    def note(self, rel: str, as_of: str | None = None) -> dict:
        if rel.endswith(".mmd"):
            return read_diagram(self.root, rel)
        if Path(rel).suffix.lower() in SOURCE_LANGS:
            return read_source(self.root, rel)
        record = next((r for r in self.records() if r["path"] == rel), None)
        if record is None or inside(self.root, rel) is None:
            return {}
        relations = [{"path": link["target"], "rel_type": link.get("rel_type") or "relates-to",
                      "text": link.get("text", ""), "direction": "out"}
                     for link in record.get("links", [])]
        relations += [{"path": source, "rel_type": "relates-to", "text": "", "direction": "in"}
                      for source in self._backlinks.get(rel, [])]
        payload = {"path": rel, "title": self._title(record), "kind": "note",
                   "valid_from": record.get("valid_from"),
                   "valid_until": record.get("valid_until"),
                   "relations": relations, "concepts": []}
        try:
            text = (self.root / rel).read_text(encoding="utf-8")
            payload["markdown"] = text
            payload["frontmatter"], payload["body"] = split_front_matter(text)
            payload["tags"] = read_live_tags(text)
        except (OSError, UnicodeDecodeError) as exc:
            payload["markdown"] = payload["body"] = ""
            payload["frontmatter"] = []
            payload["tags"] = []
            payload["error"] = f"unreadable: {type(exc).__name__}"
        payload["backlinks"] = [r for r in relations if r["direction"] == "in"]
        titles = {r["path"]: self._title(r) for r in self.records()}
        payload["superseded_by"] = superseded_by(payload, titles)
        payload["valid_now"] = graph.in_window(payload, as_of)
        return payload

    def node(self, rel: str, as_of: str | None = None) -> dict:
        note = self.note(rel, as_of)
        return {k: v for k, v in note.items() if k != "markdown" and k != "body"} if note else {}

    def stats(self, as_of: str | None = None) -> dict:
        tree = self.tree(as_of)
        counts: dict = {}
        for row in tree["notes"]:
            counts[row["folder"] or "."] = counts.get(row["folder"] or ".", 0) + 1
        # Only edges between files that exist. `build_graph` records every outbound link,
        # including the [example](path.md) references documentation prose is full of; counting
        # those makes the footer claim links the graph refuses to draw.
        known = {r["path"] for r in self.records()}
        edges = sum(1 for source, targets in self._graph.items() if source in known
                    for target in targets if target in known)
        return {"notes": len(tree["notes"]), "diagrams": len(tree["diagrams"]),
                "edges": edges, "concepts": 0, "scanned_at": "", "relation_types": [],
                "folders": [{"folder": f, "n": n} for f, n in sorted(counts.items())],
                "cluster_above": graph.CLUSTER_ABOVE}

    def graph_payload(self, folder: str, rel_type: str, as_of, limit: int) -> dict:
        rows = [r for r in self.records()
                if not folder or r["path"].startswith(folder.rstrip("/") + "/")]
        total = len(rows)
        rows = rows[:limit] if limit > 0 else rows
        known = {r["path"] for r in rows}
        edges = []
        for record in rows:
            for link in record.get("links", []):
                kind = link.get("rel_type") or "relates-to"
                if link["target"] in known and (not rel_type or kind == rel_type):
                    edges.append({"source": record["path"], "target": link["target"],
                                  "anchor": link.get("anchor", ""), "kind": link.get("kind", ""),
                                  "rel_type": kind, "text": link.get("text", "")})
        return {"nodes": [r["path"] for r in rows], "edges": edges,
                "titles": {r["path"]: self._title(r) for r in rows},
                "total": total, "truncated": total > len(rows)}

    def concepts(self, limit: int) -> list:
        return []

    def _load_note_tags(self, as_of: str | None) -> list:
        """(tag, note) pairs straight from the walk. A plain folder has no inventory and gets none
        written: every node it shows is one its notes carry."""
        return [(tag, r["path"]) for r in self.records() if graph.in_window(r, as_of)
                for tag in r.get("tags") or []]

    def build_tag_tree(self, as_of: str | None = None) -> dict:
        return build_tag_tree_payload(graph.build_tag_index(self._load_note_tags(as_of), {}), FOLDER_TAGS)

    def find_tagged_paths(self, node: str, as_of: str | None = None) -> set:
        return {row["path"] for row in graph.find_notes_under_tag(self._load_note_tags(as_of), node)}

    def build_tag_graph(self, root: str, notes: bool, as_of: str | None, limit: int) -> dict:
        note_tags = self._load_note_tags(as_of)
        titles = {r["path"]: self._title(r) for r in self.records()}
        return graph.build_tag_graph(graph.build_tag_index(note_tags, {}), note_tags, titles,
                                     root.casefold().strip(graph.TAG_SEPARATOR), notes, limit)

    def query(self, params: dict, limit: int, as_of) -> dict:
        return {"error": "graph queries need a vault; this is a plain folder"}

    def sqlite_search(self, term: str, k: int) -> list:
        return []


class Search:
    """Semantic search when the vault has a `.rag` workspace, SQLite when it does not.

    Which one answered is reported on every response. A grep-shaped answer that looks like a
    semantic one is the failure this exists to prevent.
    """

    def __init__(self, vault: Path) -> None:
        self.vault = vault
        self._index = None
        self._lock = threading.Lock()
        self._tried = False
        # Why the semantic index is not answering. It used to go to stderr, where no browser ever
        # sees it, so the page could only say "sqlite" and never why - and "no index here" and
        # "the index is broken" are very different things to be told.
        self.reason = ""

    def index(self):
        with self._lock:
            if self._tried:
                return self._index
            self._tried = True
            if not (self.vault / ".rag").is_dir():
                self.reason = "no .rag workspace in this folder"
                return None
            try:
                from rag_toolkit.api import Index      # noqa: PLC0415 - optional, by design
                self._index = Index(self.vault / ".rag")
            except Exception as exc:                    # a missing venv must not break the UI
                self.reason = (f".rag is here but its toolkit will not import "
                               f"({type(exc).__name__}) — try `.rag/bin/rag doctor`")
                print(f"  semantic search unavailable: {self.reason}", file=sys.stderr)
                self._index = None
            return self._index

    def literal(self, corpus, query: str, k: int, path_glob: str, ext: str) -> dict:
        """Plain substring search over the files themselves.

        The right fallback for a folder with no semantic index: it reads what is on disk right now,
        so it cannot be stale, and it can quote the matching line. It is not semantic and the
        response says `text` so nothing has to guess.
        """
        from fnmatch import fnmatch                     # noqa: PLC0415
        needle = query.casefold()
        hits, scanned, total = [], 0, 0
        tree = corpus.tree()
        for row in tree["notes"] + tree["diagrams"] + tree.get("sources", []):
            path = row["path"]
            if path_glob and not fnmatch(path, path_glob):
                continue
            if ext and not any(path.endswith(e if e.startswith(".") else "." + e)
                               for e in ext.split(",") if e):
                continue
            real = inside(corpus.root, path)
            if real is None:
                continue
            try:
                text = real.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            scanned += 1
            # Every occurrence, not the first. One hit per FILE shows the reader an arbitrary
            # line and gives them no way to know there were others - which is the same defect as
            # returning a file without a line number, one level down.
            found_here = 0
            trail: list[str] = []
            for line_no, raw in enumerate(text.splitlines(), start=1):
                stripped = raw.strip()
                if stripped.startswith("#"):
                    # The heading chain is what makes several hits in one note distinguishable
                    # rather than four copies of the same-looking row.
                    depth = len(stripped) - len(stripped.lstrip("#"))
                    title_text = stripped[depth:].strip()
                    if 0 < depth <= 6 and title_text:
                        del trail[depth - 1:]
                        trail.append(title_text)
                    continue
                if needle not in stripped.casefold():
                    continue
                total += 1
                if found_here >= MATCHES_PER_FILE:
                    continue          # counted, not shown - the cap is stated, never silent
                found_here += 1
                hits.append({"path": path, "title": row.get("title", ""), "kind": "note",
                             "score": None, "matched_by": "text",
                             "heading_path": " > ".join(trail),
                             "citation": f"{path}:{line_no}", "line": line_no,
                             "openable": True, "text": stripped[:220]})
        # Every candidate file is read even after k hits, so `scanned` is the whole corpus and a
        # zero here means the string is genuinely absent. Stopping early made an empty result
        # indistinguishable from an unfinished one.
        return {"backend": "text", "hits": hits[:k], "scanned": scanned, "total": total,
                "truncated": total > len(hits[:k]), "reason": self.reason}

    def run(self, corpus, query: str, k: int, path_glob: str, ext: str) -> dict:
        index = self.index()
        if index is not None:
            try:
                # search_report is what Index.search() calls internally; using it directly returns
                # identical hits AND keeps the report - whether reranking ran, how many the text
                # index contributed, and any note the store wants to make about the query.
                report = index.search_report(query, k=k, path=path_glob, ext=ext or None)
                from rag_toolkit.retrieve import to_dict     # noqa: PLC0415
                hits = [to_dict(h, max_chars=700) for h in report.hits]
                # The anchor carries line_start/line_end for markdown. Passing it through is
                # what lets a hit open the note ON the matching line instead of at the top.
                return {"backend": "rag", "hits": [
                    {"path": h.get("rel_path") or h.get("path", ""), "title": h.get("title", ""),
                     "score": h.get("score"), "matched_by": h.get("matched_by", ""),
                     "citation": h.get("citation", ""), "heading_path": h.get("heading_path", ""),
                     "line": (h.get("anchor") or {}).get("line_start"),
                     "openable": True,
                     "text": h.get("text", "")}
                    for h in hits],
                    "reranked": getattr(report, "reranked", None),
                    "notes": list(getattr(report, "notes", []) or [])}
            except Exception as exc:
                self.reason = f"the semantic search failed ({type(exc).__name__})"
                print(f"  rag search failed ({type(exc).__name__}); using sqlite", file=sys.stderr)
        if corpus.mode == "folder":
            return self.literal(corpus, query, k, path_glob, ext)
        return self.titles_and_bodies(corpus, query, k, path_glob, ext)

    def titles_and_bodies(self, corpus, query: str, k: int, path_glob: str, ext: str) -> dict:
        """A vault with no working semantic index: names AND prose, in that order.

        This used to be `sqlite_search` alone - `path LIKE`, `title LIKE`, glossary `term LIKE` -
        which never opens a note. A plain folder got `literal()` and could find a word inside a
        file; the vault, with the database and the graph and the glossary, could not. The richer
        corpus had the poorer search, and because the response said `sqlite` rather than "I did not
        read any note", nothing on screen ever admitted it.

        Names first because someone typing three letters is usually reaching for a note they know
        exists; prose after, because that is the half that was missing entirely.
        """
        rows = corpus.sqlite_search(query, k)
        # Same shape as every other backend, so nothing downstream has to ask which one answered
        # before it can read a hit. A title match has no line to point at, and says so with null.
        # `graph.serve_search` returns glossary terms with the TERM in the path field. They are
        # not notes and opening them 404s, so every hit says whether it can be opened.
        # Each hit says how IT matched, because the answer is now two searches merged and
        # "sqlite" would no longer distinguish a title from a word found inside a note.
        hits = [{"path": r["path"], "title": r.get("title") or "", "kind": r.get("kind", "note"),
                 "score": None,
                 "matched_by": "concept" if r.get("kind") == "concept" else "title",
                 "citation": r["path"], "heading_path": "", "line": None,
                 "openable": r.get("kind", "note") != "concept", "text": ""}
                for r in rows]
        if path_glob:
            from fnmatch import fnmatch                 # noqa: PLC0415
            hits = [h for h in hits if fnmatch(h["path"], path_glob)]
        if ext:
            wanted = {e if e.startswith(".") else f".{e}" for e in ext.split(",") if e}
            hits = [h for h in hits if any(h["path"].endswith(e) for e in wanted)]

        # The half that was missing. `literal()` is the same scanner a plain folder gets - it reads
        # what is on disk right now, so it cannot be stale, and it can quote the line it matched.
        body = self.literal(corpus, query, k, path_glob, ext)
        named = {h["path"] for h in hits}
        merged = hits + [h for h in body["hits"] if h["path"] not in named]
        # 0d - what the search could actually SEE. Naming the backend was never enough: a reader
        # cannot tell "found nothing" from "never looked", and for vaults with a broken .rag the
        # answer was the second one for a long time without ever saying so.
        total = len(hits) + body.get("total", len(body["hits"]))
        return {"backend": "text", "hits": merged[:k], "scanned": body.get("scanned", 0),
                "total": total, "truncated": total > len(merged[:k]), "reason": self.reason,
                "coverage": self.coverage(corpus, body.get("scanned", 0)),
                "notes": ["names and prose; no semantic index in this vault"]}

    def coverage(self, corpus, scanned: int) -> dict:
        """How many of the vault's notes this answer actually looked inside."""
        try:
            tree = corpus.tree()
            total = (len(tree.get("notes", [])) + len(tree.get("diagrams", []))
                     + len(tree.get("sources", [])))
        except Exception:
            total = 0
        return {"searchable": scanned, "total": total}


# --- writing --------------------------------------------------------------------------------

FORBIDDEN_SEGMENTS = {".git", ".rag", ".wiki", ".agents", ".input", ".obsidian", "node_modules"}


def validate_write_path(vault: Path, raw: str) -> tuple[Path | None, str]:
    """Decide where a browser edit may land. Returns (absolute path, reason-if-refused)."""
    rel = (raw or "").strip().replace("\\", "/")
    if not rel:
        return None, "no path given"
    if rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
        return None, "an absolute path is not a note in this vault"
    if ".." in Path(rel).parts:
        return None, "a path may not walk up out of the vault"
    if not rel.endswith(".md"):
        return None, "only markdown notes can be written from the browser"
    parts = Path(rel).parts
    if any(part in FORBIDDEN_SEGMENTS or part.startswith(".") for part in parts):
        return None, "that folder holds machinery, not notes"
    target = (vault / rel).resolve()
    if not target.is_relative_to(vault.resolve()):
        return None, "that path resolves outside the vault"
    return target, ""


def backup_note(vault: Path, target: Path, cache: Path | None = None) -> Path | None:
    """Move the current bytes into the trash before they are replaced, then prune that note's
    history to the last TRASH_VERSIONS_KEPT. This is the enforcement point for the trash's cap:
    a queue bounded by versions per note, not by how long the vault has existed."""
    if not target.exists():
        return None
    rel = target.relative_to(vault.resolve())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%f")
    bin_ = trash_dir(vault, cache)
    destination = bin_ / stamp / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, destination)

    existing = sorted(bin_.glob(f"*/{rel.as_posix()}"),
                      key=lambda p: p.relative_to(bin_).parts[0])
    for stale in existing[:-TRASH_VERSIONS_KEPT]:
        stale.unlink(missing_ok=True)
        folder = stale.parent
        while folder != bin_ and not any(folder.iterdir()):
            folder.rmdir()
            folder = folder.parent
    return destination


class Reindexer:
    """After an edit, bring the derived state back in step — debounced, off the request thread.

    The manifest, the graph and the semantic index are all rebuildable caches over the markdown.
    Letting them drift behind an editor is how a vault starts answering questions with yesterday's
    content.
    """

    def __init__(self, vault: Path, enabled: bool = True) -> None:
        self.vault = vault
        self.enabled = enabled
        self.status = "idle"
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def poke(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(REINDEX_DEBOUNCE, self._run)
            self._timer.daemon = True
            self._timer.start()

    def _run(self) -> None:
        here = Path(__file__).resolve().parent
        steps = [
            [sys.executable, str(here / "scan_vault.py"), "--root", str(self.vault),
             "--out", str(wiki_dir(self.vault) / "manifest.json")],
            [sys.executable, str(here / "graph.py"), "--vault", str(self.vault),
             "scan", "--since-manifest"],
        ]
        rag = self.vault / ".rag" / "bin" / "rag"
        if rag.exists():
            steps.append([str(rag), "update", "--quiet"])
        self.status = "running"
        for step in steps:
            try:
                subprocess.run(step, capture_output=True, text=True, timeout=900)
            except (OSError, subprocess.SubprocessError) as exc:
                print(f"  reindex step failed: {type(exc).__name__}", file=sys.stderr)
        self.status = "idle"


STAMP_RE = re.compile(r"^\d{8}T\d{6}\.\d{6}$")


def versions_of(root: Path, rel: str, cache: Path | None = None) -> list[dict]:
    """Every previous version of one note, newest first.

    The safety net has been there since the first edit - `backup_note` copies the old bytes to
    `.trash/<stamp>/<path>` before the new ones land - and nothing ever showed it. A backup nobody
    can see is a backup nobody trusts.
    """
    bin_ = trash_dir(root, cache)
    if not bin_.is_dir():
        return []
    found = []
    for copy in bin_.glob(f"*/{rel}"):
        stamp = copy.relative_to(bin_).parts[0]
        if not STAMP_RE.match(stamp) or not copy.is_file():
            continue
        try:
            found.append({"at": stamp, "bytes": copy.stat().st_size})
        except OSError:
            continue
    return sorted(found, key=lambda v: v["at"], reverse=True)


def version_text(root: Path, rel: str, stamp: str, cache: Path | None = None) -> str | None:
    """One version's bytes. `stamp` is matched against the stamps that exist, never joined blind -
    a timestamp from a URL is exactly as untrusted as a path from one."""
    if not STAMP_RE.match(stamp or ""):
        return None
    if stamp not in {v["at"] for v in versions_of(root, rel, cache)}:
        return None
    copy = trash_dir(root, cache) / stamp / rel
    try:
        return copy.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def make_handler(vault: Path, token: str, search: Search, reindexer: Reindexer,
                 read_only: bool, corpus=None, cache: Path | None = None,
                 index_name: str = "index.md"):
    from http.server import BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs

    class Handler(BaseHTTPRequestHandler):
        server_version = "wiki-ui"

        def log_message(self, fmt, *a):  # quiet: one line per page load is noise, not information
            pass

        def _send(self, code: int, body: bytes, ctype: str, cache: str = "no-store") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            # The page and every API answer are generated per request and must never be reused:
            # this server is restarted often, sometimes against a different vault on the same
            # port, and a cached page is how someone ends up looking at another vault's notes and
            # reporting a bug that is not there. The bundles are the exception - they are pinned
            # by hash, so they revalidate against their ETag instead of being re-sent.
            self.send_header("Cache-Control", cache)
            if getattr(self, "_etag", ""):
                self.send_header("ETag", self._etag)
            # Everything the page loads is served from here. 'self' covers the two cached bundles;
            # no 'unsafe-eval', which the pinned mermaid build does not need.
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'self' 'unsafe-inline'; "
                             "style-src 'unsafe-inline'; img-src 'self' data:; "
                             "font-src 'self'; connect-src 'self'; "
                             # `default-src 'none'` blocks both of these outright unless named,
                             # and a blocked manifest is an app the browser will not install.
                             "manifest-src 'self'; worker-src 'self'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, payload, code: int = 200) -> None:
            self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")

        # --- the refusals ---------------------------------------------------------------

        def do_POST(self) -> None:  # noqa: N802 - PUT /api/note is the only write
            self._json({"error": "PUT /api/note is the only write this server accepts"}, 405)

        do_DELETE = do_PATCH = do_POST

        def _write_gate(self) -> str:
            """Every reason to refuse a write, in order. Empty string means it may proceed."""
            if read_only:
                return "405 this server was started --read-only"
            if self.headers.get("X-Wiki-Token", "") != token:
                return "403 a write must carry this page's token"
            if self.headers.get("Sec-Fetch-Site", "same-origin") not in ("same-origin", "none"):
                return "403 a write must come from this server's own page"
            ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
            if ctype != "application/json":
                return "415 a write must be application/json"
            return ""

        def do_PUT(self) -> None:  # noqa: N802
            refusal = self._write_gate()
            if refusal:
                code, _, message = refusal.partition(" ")
                self._json({"error": message}, int(code))
                return
            if urlparse(self.path).path.rstrip("/") != "/api/note":
                self._json({"error": "not found"}, 404)
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
                payload = json.loads(self.rfile.read(length) or b"{}")
            except (ValueError, OSError) as exc:
                self._json({"error": f"unreadable body: {type(exc).__name__}"}, 400)
                return
            self._write_note(payload)

        def _write_note(self, payload: dict) -> None:
            target, refusal = validate_write_path(vault, payload.get("path", ""))
            if target is None:
                self._json({"error": refusal}, 403)
                return
            markdown = payload.get("markdown")
            if not isinstance(markdown, str):
                self._json({"error": "markdown must be a string"}, 400)
                return
            # A tag edit rides on this same write: the page sends the note's tags beside its
            # text and the ONE frontmatter writer puts them in. Refused before the backup, so a
            # malformed tag leaves neither a changed note nor a trash entry behind it.
            if "tags" in payload:
                try:
                    wanted = payload["tags"] if isinstance(payload["tags"], list) else None
                    markdown = tag_tool.with_tags(markdown, tag_tool.normalize(wanted))
                except (ValueError, TypeError, AttributeError) as exc:
                    self._json({"error": f"tags refused: {exc}"}, 400)
                    return
            backup = backup_note(vault, target, cache)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(markdown, encoding="utf-8")
            inventory_added = self._list_new_tags(markdown)
            if hasattr(corpus, "refresh"):
                corpus.refresh()   # the in-memory index is now a version behind the disk
            reindexer.poke()
            self._json({"path": str(target.relative_to(vault.resolve())),
                        "bytes": len(markdown.encode("utf-8")),
                        "backup": str(backup) if backup else None,
                        "created": backup is None,
                        "tags": read_live_tags(markdown),
                        "inventory_added": inventory_added})

        def _list_new_tags(self, markdown: str) -> list:
            """List every tag the saved note carries that the vault's inventory lacks, parents
            first. After EVERY write, not only a chip edit - a tag typed in Source mode is as new
            to the vault as one picked from a chip. A plain folder has no inventory and gets none:
            that would turn somebody's folder into half a vault. The inventory's path is a
            constant of the vault; nothing from the request reaches it."""
            if corpus.mode != "vault":
                return []
            added = []
            for tag in read_live_tags(markdown):
                for node in graph.list_tag_ancestors(tag) + [tag]:
                    try:
                        if tag_tool.add_node(vault, node):
                            added.append(node)
                    except ValueError:
                        return added       # a full tree: `tags.py check` reports the rest
            return added

        # --- the reads ------------------------------------------------------------------

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            route = parsed.path.rstrip("/") or "/"
            if route == "/":
                page = (PAGE_HTML.replace("__VAULT__", vault.name)
                                 .replace("__TOKEN__", token)
                                 .replace("__READONLY__", "true" if read_only else "false"))
                self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
                return
            # --- what makes it an app you can install -------------------------------------
            if route == "/manifest.webmanifest":
                self._send(200, json.dumps(web_manifest(vault.name), indent=2).encode("utf-8"),
                           "application/manifest+json")
                return
            if route == "/sw.js":
                # Scope is the root, so it is served from the root. No Service-Worker-Allowed
                # header is needed and none is given.
                self._send(200, SERVICE_WORKER.encode("utf-8"), "text/javascript; charset=utf-8")
                return
            if route.startswith("/icon-") and route.endswith(".png"):
                # The size is a KEY in ICON_SIZES. A number off a URL never reaches a generator
                # that would happily render a 20000px square and take the machine with it.
                try:
                    size = int(route[len("/icon-"):-len(".png")])
                except ValueError:
                    size = 0
                if size not in ICON_SIZES:
                    self._json({"error": "not found"}, 404)
                    return
                self._send(200, app_icon(size), "image/png")
                return

            # An image a note points at. Vaults are full of pasted screenshots and every one of
            # them used to render as a broken icon, because nothing served them at all.
            if route == "/media":
                media = find_media(vault)
                rel = params.get("path", "")
                ctype = media.get(rel)
                if ctype is None:
                    self._json({"error": "not found"}, 404)
                    return
                real = inside(vault, rel)
                if real is None or real.stat().st_size > MEDIA_MAX_BYTES:
                    self._json({"error": "not found"}, 404)
                    return
                self._send(200, real.read_bytes(), ctype)
                return

            if route.startswith("/assets/"):
                # The name is matched against the ASSETS keys, never joined to what was sent.
                name = route[len("/assets/"):]
                body = verify_asset(vault, name, cache)
                if body is None:
                    self._json({"error": "asset not cached — run serve.py --fetch-assets"}, 404)
                    return
                etag = '"' + read_pins(vault, cache).get(name, "")[:32] + '"'
                if self.headers.get("If-None-Match") == etag:
                    self.send_response(304)
                    self.send_header("ETag", etag)
                    self.end_headers()
                    return
                self._etag = etag
                self._send(200, body, "text/javascript; charset=utf-8", cache="no-cache")
                return
            if not route.startswith("/api/"):
                self._json({"error": "not found"}, 404)
                return
            try:
                self._api(route, params)
            except Exception as exc:  # a broken query must not take the page down
                self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)

        def _api(self, route: str, params: dict) -> None:
            limit = max(1, min(int(params.get("limit") or 400), 2000))
            as_of = params.get("as_of") or None
            if route == "/api/stats":
                payload = corpus.stats(as_of)
                payload["mode"] = corpus.mode
                payload["read_only"] = read_only
                payload["reindex"] = reindexer.status
                payload["as_of"] = as_of or ""
                self._json(payload)
            elif route == "/api/tree":
                self._json(corpus.tree(as_of))
            elif route == "/api/note":
                self._json(corpus.note(params.get("path", ""), as_of)
                           or {"error": "unknown note"})
            elif route == "/api/glossary":
                self._json(corpus.glossary(index_name))
            elif route == "/api/tags":
                self._json(corpus.build_tag_tree(as_of))
            elif route == "/api/tag-graph":
                self._json(corpus.build_tag_graph(params.get("root", ""),
                                            params.get("notes", "") in ("1", "true"), as_of, limit))
            elif route == "/api/search":
                k = min(int(params.get("k") or 10), SEARCH_LIMIT)
                # A tag is applied to the HITS, like the date below and for the same reason:
                # `.rag` cannot filter by tag. So the search over-fetches, the filter runs here
                # against a set this server built, and the answer says how many it removed.
                tag = (params.get("tag") or "").strip().casefold().strip(graph.TAG_SEPARATOR)
                allowed = corpus.find_tagged_paths(tag, as_of) if tag else None
                if tag and not params.get("q", "").strip():
                    found = list_tagged_notes(corpus, allowed, tag, k)
                else:
                    found = search.run(corpus, params.get("q", ""), SEARCH_LIMIT if tag else k,
                                       params.get("path", ""), params.get("ext", ""))
                tag_hidden = 0
                if tag and found.get("backend") != "tags":
                    kept = [h for h in found.get("hits", []) if h.get("path") in allowed]
                    tag_hidden = len(found.get("hits", [])) - len(kept)
                    found["truncated"] = bool(found.get("truncated")) or len(kept) > k
                    found["hits"] = kept[:k]
                    if not allowed:
                        found["reason"] = f"no note carries `{tag}` or anything under it"
                found["tag"] = tag
                found["tag_hidden"] = tag_hidden
                # Time is applied to the HITS, not inside a backend: `.rag` cannot filter by date,
                # and a result set that is silently shorter is the failure "search says why"
                # exists to prevent. A concept hit has a term where a path goes and is never dated.
                valid = corpus.valid_paths(as_of)
                hidden = 0
                if valid is not None:
                    kept = [h for h in found.get("hits", [])
                            if not h.get("openable", True) or h["path"] in valid]
                    hidden = len(found.get("hits", [])) - len(kept)
                    found["hits"] = kept
                found["hidden"] = hidden
                found["as_of"] = as_of or ""
                self._json({"query": params.get("q", ""), **found})
            elif route == "/api/graph":
                self._json(corpus.graph_payload(params.get("folder", ""),
                                                params.get("type", ""), as_of, limit))
            elif route == "/api/node":
                self._json(corpus.node(params.get("path", ""), as_of)
                           or {"error": "unknown note"})
            elif route == "/api/concepts":
                self._json(corpus.concepts(limit))
            elif route == "/api/history":
                rel = params.get("path", "")
                # The path is a key in the corpus first; history is not a way around that.
                if not corpus.note(rel):
                    self._json({"error": "unknown note"}, 404)
                else:
                    self._json({"path": rel, "versions": versions_of(vault, rel, cache)})
            elif route == "/api/version":
                rel = params.get("path", "")
                text = version_text(vault, rel, params.get("at", ""), cache) \
                    if corpus.note(rel) else None
                self._json({"path": rel, "at": params.get("at", ""), "text": text}
                           if text is not None else {"error": "no such version"})
            elif route == "/api/query":
                self._json(corpus.query(params, limit, as_of))
            else:
                self._json({"error": "not found"}, 404)

    return Handler


# --- the page ----------------------------------------------------------------------------------
# One inline constant, no build step, no CDN. The two bundles it does load are served from
# /assets/ by this same process, so the page works with no network at all.

PAGE_HTML = r"""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>__VAULT__ — wiki</title>
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="apple-touch-icon" href="/icon-192.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="__VAULT__">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#fbfbfc">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#14161a">
<style>
  :root { color-scheme: light dark; --bg:#fbfbfc; --fg:#16181d; --panel:#fff; --line:#dcdfe6;
          --dim:#6b7280; --accent:#4c6ef5; --warn:#c2410c; --ok:#15803d; --hover:#eef1f7; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#14161a; --fg:#e8eaed; --panel:#1b1e24; --line:#2c313a; --dim:#9aa1ad;
            --warn:#fb923c; --ok:#4ade80; --hover:#232833; }
  }
  * { box-sizing: border-box; }
  body { margin:0; font:13px/1.55 system-ui,sans-serif; background:var(--bg); color:var(--fg);
         display:grid; grid-template-columns: var(--nav) 1fr; height:100dvh;
         --nav:300px; }
  /* Putting the sidebar away is one custom property, so nothing has to be re-laid out by hand. */
  body[data-nav="closed"] { --nav:0px; }
  body[data-nav="closed"] aside { transform:translateX(-100%); border-right:none; }
  aside { background:var(--panel); border-right:1px solid var(--line); overflow-y:auto;
          padding:14px; transition:transform .18s ease; min-width:0; }

  /* --- a phone ------------------------------------------------------------------------
     One column, and the sidebar becomes a drawer OVER the note rather than a column beside
     it: 300px of a 390px screen leaves no room to read anything. */
  @media (max-width: 760px) {
    body { grid-template-columns: 1fr; --nav:0px; }
    aside { position:fixed; inset:0 auto 0 0; width:min(86vw, 320px); z-index:40;
            box-shadow:0 0 0 100vmax rgba(0,0,0,.38); }
    body[data-nav="closed"] aside { box-shadow:none; }
    #bar { position:sticky; top:0; z-index:20; background:var(--bg); flex-wrap:wrap; }
    /* A finger is not a mouse: 44px is the smallest target that can be hit reliably. */
    #bar button, #bar input { min-height:34px; }
    #note { padding:12px 14px 40vh; font-size:14.5px; }
    #overlay .bar { flex-wrap:wrap; }
    .hit, #tree .folder, #glossary .g { padding-top:7px; padding-bottom:7px; }
  }
  /* An installed app runs under the notch and the home indicator. */
  @supports (padding: max(0px)) {
    aside { padding-left:max(14px, env(safe-area-inset-left)); }
    #bar { padding-left:max(10px, env(safe-area-inset-left)); }
  }
  h1 { font-size:14px; margin:0 0 12px; }
  h2 { font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:var(--dim);
       margin:18px 0 6px; }
  input, select, button, textarea { font:inherit; width:100%; padding:5px 7px; margin-bottom:6px;
       background:var(--bg); color:var(--fg); border:1px solid var(--line); border-radius:5px; }
  button { cursor:pointer; width:auto; padding:5px 10px; }
  button:hover { border-color:var(--accent); }
  .row { display:flex; gap:6px; } .row > * { flex:1; margin-bottom:6px; }
  .chip { display:inline-block; padding:1px 6px; margin:0 3px 3px 0; border-radius:9px;
          border:1px solid var(--line); cursor:pointer; font-size:11px; }
  .chip.on { background:var(--accent); color:#fff; border-color:var(--accent); }
  .folder { padding:4px 2px; margin-top:4px; cursor:pointer; user-select:none; font-size:12px;
            display:flex; gap:6px; align-items:center; }
  .folder:hover { color:var(--accent); }
  .folder .caret { display:inline-block; width:9px; transition:transform .12s; color:var(--dim); }
  .folder.open .caret { transform:rotate(90deg); }
  .folder .n { margin-left:auto; color:var(--dim); font-size:11px; }
  .folder-notes { display:none; margin:0 0 4px 10px; border-left:1px solid var(--line);
                  padding-left:6px; }
  .folder-notes.open { display:block; }
  .hit { padding:5px 6px; border-radius:4px; cursor:pointer; border-bottom:1px solid var(--line); }
  .hit:hover { background:var(--bg); }
  .hit.noopen { cursor:default; opacity:.8; }
  .hit .p { font-family:ui-monospace,monospace; font-size:11px; color:var(--dim); }
  .hit .t { font-size:11px; color:var(--dim); max-height:3.6em; overflow:hidden; }
  .hit .crumbs { font-size:10px; color:var(--dim); }
  .hit .why { font-size:10px; color:var(--dim); float:right; }
  /* A tree hint is a SECOND LINE, never a float: a floated span is outside the row's height, so a
     long note title drew straight over the folder row below it. */
  .hit .sub { display:block; font-size:10px; color:var(--dim); line-height:1.35;
              white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  mark { background:rgba(250,204,21,.45); color:inherit; border-radius:2px; padding:0 1px; }
  [data-line].hit-line { animation:flash 1.6s ease-out; border-radius:4px; }
  [data-hit] { box-shadow:-10px 0 0 -8px var(--accent); }
  @keyframes flash { from { background:rgba(250,204,21,.5); } to { background:transparent; } }
  .dim { color:var(--dim); }
  main { display:flex; flex-direction:column; overflow:hidden; }
  #bar { display:flex; gap:8px; align-items:center; padding:8px 14px;
         border-bottom:1px solid var(--line); background:var(--panel); }
  #where { font-family:ui-monospace,monospace; font-size:12px; flex:1; overflow:hidden;
           text-overflow:ellipsis; white-space:nowrap; }
  #lock.open { border-color:var(--warn); color:var(--warn); }
  #save { display:none; } #save.on { display:inline-block; }
  #note { flex:1; overflow-y:auto; padding:18px 30px; }
  #edit { flex:1; display:none; width:100%; font-family:ui-monospace,monospace; font-size:12.5px;
          border:0; border-radius:0; resize:none; padding:18px 26px; }
  #edit.on { display:block; } #note.off { display:none; }

  /* Editing happens IN the rendered note: the block under the caret shows its markdown, every
     other block stays drawn. The textarea below is one block's source, not the whole file. */
  #note.live { outline:2px solid var(--accent); outline-offset:6px; border-radius:4px; }
  #note.live > [data-line]:hover { background:var(--hover); border-radius:3px; }
  textarea.blocksrc { width:100%; box-sizing:border-box; font-family:ui-monospace,monospace;
    font-size:12.5px; line-height:1.55; color:var(--fg); background:var(--hover);
    border:1px solid var(--accent); border-radius:3px; padding:6px 8px; resize:vertical; }

  #asof { background:var(--bg); color:var(--fg); border:1px solid var(--line); border-radius:3px;
    font:inherit; font-size:11px; padding:2px 4px; }
  #asof-bar { display:none; padding:6px 10px; font-size:11.5px; border-bottom:1px solid var(--line);
    background:var(--hover); color:var(--accent); }
  body[data-asof]:not([data-asof=""]) #asof-bar { display:block; }
  .banner { border-left:3px solid var(--accent); background:var(--hover); padding:7px 10px;
    margin:0 0 12px; font-size:12.5px; border-radius:0 3px 3px 0; }
  .banner.stale { border-left-color:#c1121f; }

  /* A glossary term found in the prose. Underlined, never coloured like a link: it is a
     definition you can look at, not a note you are about to leave the page for. */
  a.term { text-decoration:underline dotted; text-underline-offset:2px; cursor:help;
    color:inherit; }
  a.term:hover { color:var(--accent); }
  #glossary .g { padding:3px 4px; cursor:pointer; font-size:12px; }
  #glossary .g:hover { color:var(--accent); }
  #glossary .g b { font-weight:600; }
  #tagtree .tagrow { display:flex; gap:4px; align-items:center; padding:3px 4px; font-size:12px; }
  #tagtree .caret { width:10px; cursor:pointer; color:var(--dim); user-select:none; }
  #tagtree .tagrow a { flex:1; color:inherit; text-decoration:none; }
  #tagtree .tagrow a:hover { color:var(--accent); }
  #tagtree .n { color:var(--dim); font-size:10px; }
  #tagtree .unlisted a { font-style:italic; }
  .tagkids { display:none; margin-left:12px; } .tagkids.open { display:block; }
  #glossary .g .st { color:var(--dim); font-size:10px; margin-left:4px; }
  .termcard h2 { margin-top:0; }
  .termcard .chip { display:inline-block; font-size:10.5px; border:1px solid var(--line);
    border-radius:9px; padding:1px 7px; margin-right:5px; color:var(--dim); }
  #note h1 { font-size:22px; margin:.2em 0 .6em; }
  #note h2 { font-size:16px; text-transform:none; letter-spacing:0; color:var(--fg);
             margin:1.4em 0 .4em; border-bottom:1px solid var(--line); padding-bottom:.2em; }
  #note pre { background:var(--panel); border:1px solid var(--line); border-radius:6px;
              padding:10px; overflow-x:auto; }
  #note code { font-family:ui-monospace,monospace; font-size:12px; }
  #note table { border-collapse:collapse; display:block; overflow-x:auto; width:100%; }
  #note > p, #note > ul, #note > ol, #note > blockquote { max-width:none; }
  #note th, #note td { border:1px solid var(--line); padding:4px 8px; text-align:left; }
  #note blockquote { margin:0; padding-left:12px; border-left:3px solid var(--line);
                     color:var(--dim); }
  #note a { color:var(--accent); }
  .fm { display:flex; flex-wrap:wrap; gap:5px 8px; margin:0 0 16px; padding-bottom:10px;
        border-bottom:1px solid var(--line); font-size:11px; }
  .fm span { display:inline-flex; gap:4px; border:1px solid var(--line); border-radius:9px;
             padding:1px 8px; background:var(--panel); }
  .fm b { font-weight:600; color:var(--dim); }
  .tags { display:flex; flex-wrap:wrap; gap:5px 6px; margin:0 0 14px; font-size:11px;
          align-items:center; }
  .tagchip { display:inline-flex; gap:3px; align-items:center; border:1px solid var(--accent);
             border-radius:9px; padding:1px 8px; }
  .tagchip a { text-decoration:none; }
  .tagchip button { border:0; background:none; padding:0 0 0 2px; cursor:pointer;
                    color:var(--dim); font-size:12px; line-height:1; }
  #tagadd { width:140px; font-size:11px; padding:1px 6px; }
  .tagnote { padding:5px 0; border-top:1px solid var(--line); }
  .mermaid { background:var(--panel); border:1px solid var(--line); border-radius:6px;
             padding:10px; overflow-x:auto; margin:1em 0; }
  #graph { flex:1; display:none; position:relative; } #graph.on { display:block; }
  svg#g { width:100%; height:100%; display:block; }
  circle { fill:var(--accent); cursor:pointer; } circle.faded { opacity:.25; }
  line { stroke:var(--dim); stroke-opacity:.45; }
  text { font-size:10px; fill:currentColor; pointer-events:none; }
  #meta { position:absolute; left:12px; bottom:10px; color:var(--dim); font-size:11px; }
  #graph svg { cursor:grab; touch-action:none; } #graph svg.panning { cursor:grabbing; }
  circle.sel { fill:var(--warn); }
  circle.leaf { fill:var(--dim); }
  circle.near { fill:var(--accent); }
  line.hot { stroke:var(--accent); stroke-opacity:.9; stroke-width:1.6; }
  .faded { opacity:.12; }
  text.lbl { opacity:.75; } text.lbl.show { opacity:1; font-weight:600; }
  #gdetail { position:absolute; right:12px; top:12px; width:290px; max-height:78%;
             overflow-y:auto; background:var(--panel); border:1px solid var(--line);
             border-radius:8px; padding:11px; display:none; font-size:12px; }
  #gdetail.on { display:block; }
  #gdetail h3 { margin:0 0 2px; font-size:13px; }
  #gdetail .rel { padding:3px 0; border-top:1px solid var(--line); cursor:pointer; }
  #gdetail .rel:hover { color:var(--accent); }
  #gdetail .t { color:var(--dim); font-size:10px; text-transform:uppercase;
                letter-spacing:.05em; }
  .figure { position:relative; }
  .figure .zoom { position:absolute; top:6px; right:6px; opacity:0; transition:opacity .12s;
                  padding:2px 7px; font-size:11px; background:var(--bg); }
  .figure:hover .zoom, .figure .zoom:focus { opacity:1; }
  #overlay { position:fixed; inset:0; background:var(--bg); display:none; z-index:50; }
  #overlay.on { display:block; }
  #stage { position:absolute; inset:0; overflow:hidden; cursor:grab; touch-action:none; }
  #stage.drag { cursor:grabbing; }
  #stage > div { position:absolute; top:0; left:0; transform-origin:0 0; will-change:transform; }
  #stage svg { max-width:none !important; height:auto; }
  #overbar { position:absolute; top:10px; right:12px; display:flex; gap:6px; z-index:2; }
  #overbar button { background:var(--panel); }
  #overcap { position:absolute; top:14px; left:16px; color:var(--dim); font-size:11px;
             font-family:ui-monospace,monospace; z-index:2; }
  @media print {
    aside, #bar, #overbar, #toast, .figure .zoom { display:none !important; }
    body { display:block; height:auto; }
    #overlay.on { position:static; }
    #stage { position:static; overflow:visible; height:auto; }
    #stage > div { position:static; transform:none !important; }
    #stage svg { width:100% !important; height:auto !important; }
    #note.off { display:none !important; }
  }
  /* A dialog, centred, because comparing two versions is the task the screen is for while it is
     open - not something to squint at in a 330px column pinned to the corner. */
  #history { position:fixed; inset:0; z-index:60; display:none;
             background:rgba(0,0,0,.45); place-items:center; padding:18px; }
  #history.on { display:grid; }
  #history .hbox { width:min(1100px, 95vw); height:min(760px, 84vh); display:flex;
             flex-direction:column; background:var(--panel); border:1px solid var(--line);
             border-radius:12px; box-shadow:0 18px 60px rgba(0,0,0,.3); overflow:hidden; }
  #history .htop { display:flex; align-items:center; gap:10px; padding:11px 14px;
             border-bottom:1px solid var(--line); font-size:12.5px; }
  #history .htop b { font-size:13.5px; }
  #history .htop .grow { flex:1; color:var(--dim); overflow:hidden; text-overflow:ellipsis;
             white-space:nowrap; }
  #history .htop button { margin:0; }
  /* Versions on the left, what that version changed on the right. */
  #history .hbody { flex:1; display:grid; grid-template-columns:260px 1fr; min-height:0; }
  #history .hlist { overflow-y:auto; border-right:1px solid var(--line); padding:6px; }
  #history .hpreview { overflow-y:auto; padding:12px 14px; min-width:0; }
  #history .v { padding:8px 9px; border-radius:6px; cursor:pointer; display:flex; gap:8px;
                align-items:baseline; font-size:12px; }
  #history .v:hover { background:var(--hover); }
  #history .v.sel { background:var(--accent); color:#fff; }
  #history .v.sel .sz { color:#fff; opacity:.8; }
  #history .v .sz { margin-left:auto; color:var(--dim); font-size:10px; }
  /* The highlight.js theme, INLINE. `style-src` is `'unsafe-inline'` and does not include
     `'self'`, so a linked stylesheet would be blocked - and a theme built on the page's own
     tokens follows light and dark without a second palette to keep in step. */
  #note pre code.hljs { display:block; padding:10px 12px; border-radius:6px; overflow-x:auto;
                        background:var(--panel); border:1px solid var(--line); }
  .hljs-comment, .hljs-quote { color:var(--dim); font-style:italic; }
  .hljs-keyword, .hljs-selector-tag, .hljs-literal, .hljs-doctag { color:var(--accent); }
  .hljs-string, .hljs-regexp, .hljs-addition { color:var(--ok); }
  .hljs-number, .hljs-symbol, .hljs-bullet { color:var(--warn); }
  .hljs-title, .hljs-section, .hljs-name { color:var(--accent); font-weight:600; }
  .hljs-attr, .hljs-attribute, .hljs-variable, .hljs-template-variable { color:var(--fg); }
  .hljs-type, .hljs-class .hljs-title, .hljs-built_in { color:var(--warn); font-weight:600; }
  .hljs-meta { color:var(--dim); }
  .hljs-deletion { color:var(--warn); }
  .hljs-emphasis { font-style:italic; } .hljs-strong { font-weight:700; }
  #note img { max-width:100%; height:auto; border-radius:6px; border:1px solid var(--line);
              display:block; margin:10px 0; }
  #hits .ln { display:block; padding:3px 6px 3px 8px; margin-top:3px; border-left:2px solid
              var(--line); cursor:pointer; border-radius:0 3px 3px 0; }
  #hits .ln:hover { border-left-color:var(--accent); background:var(--hover); }
  #hits .ln .lno { color:var(--dim); font-size:10px; margin-right:6px; }
  #hits .ln .crumbs { display:block; }
  #bar #q { flex:1 1 200px; min-width:110px; }
  #results { border-bottom:1px solid var(--line); background:var(--card);
             max-height:55vh; overflow:auto; padding:8px 12px; }
  #results #backend { padding:2px 0 6px; }
  #results .spin { display:inline-block; width:9px; height:9px; margin-right:6px;
                   border:2px solid var(--line); border-top-color:var(--accent);
                   border-radius:50%; animation:spin .7s linear infinite; vertical-align:-1px; }
  @keyframes spin { to { transform:rotate(360deg); } }
  #bar #q-clear { margin-left:-2px; }
  .more { width:100%; margin-top:8px; }
  #history .hempty { padding:26px; color:var(--dim); text-align:center; }
  @media (max-width: 760px) {
    #history .hbody { grid-template-columns:1fr; grid-template-rows:34% 1fr; }
    #history .hlist { border-right:none; border-bottom:1px solid var(--line); }
  }
  #diff { font-family:ui-monospace,monospace; font-size:11px; white-space:pre-wrap;
          margin-top:8px; border-top:1px solid var(--line); padding-top:8px; }
  #diff .add { background:rgba(34,197,94,.16); }
  #diff .del { background:rgba(239,68,68,.16); }
  #toast { position:fixed; right:16px; bottom:14px; background:var(--panel); padding:7px 12px;
           border:1px solid var(--line); border-radius:6px; display:none; }
</style>
<aside>
  <h1>__VAULT__</h1>
  <div class="row">
    <input id="fpath" list="paths" placeholder="path filter, e.g. reg/*" autocomplete="off">
    <input id="fext" list="exts" placeholder=".md" autocomplete="off">
  </div>
  <div class="row">
    <input id="ftag" list="tagnames" placeholder="tag filter, e.g. banking/mifid" autocomplete="off"
           title="keep only notes under this tag - alone, it lists them">
  </div>
  <datalist id="tagnames"></datalist>
  <datalist id="paths"></datalist>
  <datalist id="exts"></datalist>
  <datalist id="names"></datalist>
  <h2>Notes</h2>
  <div id="tree"></div>

  <h2 id="glossary-h" style="display:none">Glossary</h2>
  <div id="glossary"></div>

  <h2 id="tags-h" style="display:none">Tags</h2>
  <div id="tagtree"></div>

  <h2>Vault</h2>
  <div id="stats" class="dim"></div>
  <div class="row">
    <input id="asof" type="date" title="show this vault as it stood on a date">
    <button id="asof-now" title="back to today" style="display:none">Now</button>
  </div>
</aside>
<main>
  <div id="bar">
    <button id="nav" title="show or hide the sidebar" aria-label="toggle sidebar">&#9776;</button>
    <span id="where" class="dim">nothing open</span>
    <button id="tab-note">Note</button>
    <button id="tab-graph">Graph</button>
    <button id="tab-tags" title="the tag tree, drawn">Tags</button>
    <button id="hist" title="previous versions of this note">History</button>
    <input id="q" list="names" placeholder="search this vault…" autocomplete="off">
    <button id="q-clear" title="clear the search (Esc)" style="display:none">&#10005;</button>
    <button id="lock" title="editing is locked">&#128274; Locked</button>
    <button id="srcmode" title="edit the raw markdown instead">Source</button>
    <button id="save">Save</button>
  </div>
  <div id="results" style="display:none">
    <div id="backend" class="dim"></div>
    <div id="hits"></div>
  </div>
  <div id="asof-bar"></div>
  <article id="note" class="dim">Pick a note on the left.</article>
  <div id="history">
    <div class="hbox">
      <div class="htop">
        <b>History</b><span class="grow" id="hpath"></span>
        <button id="hclose" title="close">Close</button>
      </div>
      <div class="hbody">
        <div class="hlist"></div>
        <div class="hpreview"><div id="diff"></div></div>
      </div>
    </div>
  </div>
  <textarea id="edit" spellcheck="false"></textarea>
  <div id="graph"><svg id="g"></svg><div id="gdetail"></div><div id="meta" class="dim"></div></div>
</main>
<div id="overlay">
  <div id="overcap"></div>
  <div id="overbar">
    <button data-z="in">+</button>
    <button data-z="out">&minus;</button>
    <button data-z="fit">Fit</button>
    <button data-x="svg" title="download the drawing as SVG">SVG</button>
    <button data-x="png" title="download the drawing as PNG">PNG</button>
    <button data-x="mmd" title="download the mermaid source">.mmd</button>
    <button data-x="pdf" title="print, or save as PDF">PDF</button>
    <button data-z="close">Close &#9003;</button>
  </div>
  <div id="stage"><div></div></div>
</div>
<div id="toast"></div>
<script>
// MathJax reads this before it loads. `processHtmlClass`/`ignoreHtmlClass` keep it out of code
// fences and drawn diagrams, where a `$` is a shell prompt or a label, not mathematics.
window.MathJax = {
  tex: { inlineMath: [["$", "$"], ["\\(", "\\)"]],
         displayMath: [["$$", "$$"], ["\\[", "\\]"]],
         processEscapes: true },
  options: { skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"],
             ignoreHtmlClass: "mermaid|no-math" },
  startup: { typeset: false }          // nothing is typeset until a note is actually rendered
};
</script>
<script src="/assets/marked.min.js"></script>
<script src="/assets/highlight.min.js"></script>
<script src="/assets/mermaid.min.js"></script>
<script src="/assets/tex-svg.js"></script>
"""

PAGE_HTML += r"""<script>
const TOKEN = "__TOKEN__";
const READ_ONLY = __READONLY__;
// Editing starts locked on purpose. A page left open in a tab should not be one keystroke away
// from changing a note - the lock is the deliberate act. It is a guard against the stray click,
// never a security control: the server re-checks the token, the origin and the path on every write.
let UNLOCKED = false;
let CURRENT = null, DIRTY = false, VIEW = "note";
// The date the whole page is being read at. "" is today. Every request carries it, so the tree,
// the counts, the graph and the search all agree about which day they are describing - a page
// where only some panes time-travelled would be worse than one that cannot.
let AS_OF = "";
// The vault's own vocabulary, loaded once. Used for the sidebar list and for decorating terms
// where they appear in prose.
let TERMS = [];
// The vault's tag tree: what its inventory lists, and apart from it what the notes merely carry.
let TAGS = { nodes: [], unlisted: [] };

const $ = s => document.querySelector(s);
const NS = "http://www.w3.org/2000/svg";
const api = (p, params) => fetch(p + "?" + new URLSearchParams(
  Object.assign(AS_OF ? { as_of: AS_OF } : {}, params || {}))).then(r => r.json());
const esc = s => (s || "").replace(/[&<>"]/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function toast(msg, ms = 2600) {
  const t = $("#toast"); t.textContent = msg; t.style.display = "block";
  clearTimeout(toast._t); toast._t = setTimeout(() => t.style.display = "none", ms);
}

const dark = matchMedia("(prefers-color-scheme: dark)").matches;
if (window.mermaid) mermaid.initialize({
  startOnLoad: false, securityLevel: "strict", theme: dark ? "dark" : "default"
});

// Registering makes the browser offer to install the page. It is only allowed in a secure
// context - localhost counts, and so does https - so over plain http to a LAN address it simply
// does not run, and nothing else on the page cares.
if ("serviceWorker" in navigator && window.isSecureContext) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

async function boot() {
  // Painted BEFORE the first await. Both calls behind this read the whole vault, and on a large
  // one that is seconds: a sidebar with headings and nothing under them looks broken, and the
  // reader has no way to tell waiting from failed.
  $("#tree").innerHTML = `<div class="dim" id="tree-loading">reading the vault\u2026</div>`;
  $("#stats").textContent = "reading the vault\u2026";
  try {
    await bootInner();
  } catch (err) {
    $("#tree-loading")?.remove();
    $("#stats").textContent = "could not read the vault: " + (err && err.message || err);
  }
}

async function bootInner() {
  const s = await api("/api/stats");
  $("#stats").textContent = s.mode === "folder"
    ? `${s.notes} notes · ${s.diagrams || 0} diagrams · ${s.edges} links · plain folder, no index`
    : `${s.notes} notes · ${s.diagrams || 0} diagrams · ${s.edges} links · ${s.concepts} concepts`
      + ` · scanned ${s.scanned_at || "—"}`;
  if (READ_ONLY) { $("#lock").disabled = true; $("#lock").textContent = "\u{1F512} Read-only"; }
  const tree = await api("/api/tree");
  // Folders start shut. A vault of any size turns an always-open tree into a wall of filenames,
  // and the sidebar is for finding a note, not for listing every one of them at once.
  $("#tree").innerHTML = renderFolder(buildFolderTree(treeEntries(tree)));
  document.querySelectorAll("#tree .folder").forEach(row =>
    row.onclick = () => toggleFolder(row.dataset.f));
  wireHits("#tree");
  fillFilters(tree);
  fillNames(tree);
  if (typeof tree.hidden === "number" && tree.hidden > 0)
    $("#stats").textContent += ` \u00b7 ${tree.hidden} hidden on ${AS_OF}`;
  await loadGlossary();
  await loadTags();
  route();
}

// --- the vault's own vocabulary ---------------------------------------------------------
// index.md's `## Business Glossary` is the only place a definition comes from. `candidates` are
// terms the scanner merely SAW; they are listed apart and never presented as definitions.

async function loadGlossary() {
  const g = await api("/api/glossary");
  TERMS = g.terms || [];
  const cands = g.candidates || [];
  $("#glossary-h").style.display = (TERMS.length || cands.length) ? "" : "none";
  $("#glossary").innerHTML = TERMS.map(term =>
    `<div class="g" data-t="${esc(term.term)}"><b>${esc(term.term)}</b>` +
    (term.status === "defined" ? "" : `<span class="st">${esc(term.status)}</span>`) +
    `</div>`).join("") + (cands.length
      ? `<div class="g dim" data-cands="1" title="seen in the notes, not in the glossary">` +
        `+ ${cands.length} undefined term${cands.length === 1 ? "" : "s"}</div>` : "");
  $("#glossary").querySelectorAll(".g[data-t]").forEach(row =>
    row.onclick = () => { location.hash = "!" + row.dataset.t; });
  const more = $("#glossary").querySelector(".g[data-cands]");
  if (more) more.onclick = () => toast(cands.map(c => c.term).join(", "), 6000);
}

function findTerm(name) {
  const wanted = (name || "").toLowerCase();
  return TERMS.find(t => t.term.toLowerCase() === wanted
    || (t.aliases || []).some(a => a.toLowerCase() === wanted));
}

// A term is not a note. It has no file, so it gets no edit control, no history and no lock -
// the same discipline `openable:false` already applies to a concept in the search results.
function openTerm(name) {
  const term = findTerm(name);
  if (!term) { toast(`no glossary entry for ${name}`); return; }
  CURRENT = null; DIRTY = false;
  setView("note");
  $("#where").textContent = term.term + "  (glossary)";
  $("#note").classList.remove("dim", "live");
  const mentions = term.mentions
    ? `<span class="chip">${term.mentions} mention${term.mentions === 1 ? "" : "s"}</span>` : "";
  $("#note").innerHTML =
    `<div class="termcard"><h2>${esc(term.term)}</h2>` +
    `<p><span class="chip">${esc(term.status)}</span>${mentions}` +
    ((term.aliases || []).length ? `<span class="chip">aka ${esc(term.aliases.join(", "))}</span>`
                                 : "") + `</p>` +
    (term.expansion ? `<p><b>${esc(term.expansion)}</b></p>` : "") +
    (term.meaning ? `<p>${esc(term.meaning)}</p>` : "") +
    (term.source ? `<p class="dim">Defined in <a href="#" data-p="${esc(term.source)}">` +
                   `${esc(term.source)}</a></p>`
                 : `<p class="dim">No note in this vault defines it yet.</p>`) +
    `</div>`;
  $("#note").querySelectorAll("a[data-p]").forEach(a =>
    a.onclick = ev => { ev.preventDefault(); openNote(a.dataset.p); });
  document.body.dataset.rendered = "!" + term.term;
}

// Wrap the FIRST mention of each known term in each block. Every mention would carpet a note that
// says `PIP` forty times; the first one in a block is where a reader actually needs the reminder.
function decorateTerms(root) {
  if (!TERMS.length || !root) return;
  const names = [];
  TERMS.forEach(t => { names.push(t.term); (t.aliases || []).forEach(a => names.push(a)); });
  names.sort((a, b) => b.length - a.length);          // longest match wins
  const pattern = new RegExp(
    "\\b(" + names.map(n => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")\\b", "i");
  const isAcronym = s => (s.match(/[A-Z]/g) || []).length >= 2;

  root.querySelectorAll(":scope > [data-line]").forEach(block => {
    const done = new Set();
    const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        // Never inside code, a link, a diagram, the metadata strip or an open editor: those are
        // not prose, and decorating them would change what the reader is looking at.
        return node.parentElement.closest("pre, code, a, textarea, .fm, .figure, .mermaid")
          ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      },
    });
    const texts = [];
    for (let n = walker.nextNode(); n; n = walker.nextNode()) texts.push(n);
    texts.forEach(start => {
      // Walk the whole node, not just its first match: one paragraph naming two terms must mark
      // both, and a term already marked in this block has to be stepped OVER rather than ending
      // the scan - otherwise the first skipped word hides every term after it.
      let node = start;
      while (node) {
        const match = pattern.exec(node.nodeValue);
        if (!match) break;
        const hit = match[1];
        const term = findTerm(hit);
        // An acronym is matched case-sensitively: `sca` in prose is a word, `SCA` is the term.
        const wrong = !term || done.has(term.term)
          || (isAcronym(term.term) && hit !== term.term
              && !(term.aliases || []).includes(hit));
        if (wrong) { node = node.splitText(match.index + hit.length); continue; }
        done.add(term.term);
        const found = node.splitText(match.index);
        const tail = found.splitText(hit.length);
        const link = document.createElement("a");
        link.className = "term";
        link.href = "#!" + encodeURIComponent(term.term);
        link.textContent = hit;
        link.title = [term.expansion, term.meaning].filter(Boolean).join(" \u2014 ")
          || `${term.term} (${term.status})`;
        found.replaceWith(link);
        node = tail;
      }
    });
  });
}

// --- tags: a tree to walk -----------------------------------------------------------------
// A tag is a full path (`banking/mifid/target-market`) and a note under a child is under every
// ancestor, so the sidebar shows the tree a level at a time and a node's count is everything
// below it. Nodes the inventory does not list are shown too, in italics - hiding them would hide
// exactly the drift `tags.py check` reports.

const allTagNodes = () => [...(TAGS.nodes || []), ...(TAGS.unlisted || [])];
const tagHash = tag => "#+" + encodeURIComponent(tag);

function renderTagLevel(parent) {
  return allTagNodes().filter(n => n.parent === parent)
    .sort((a, b) => a.tag.localeCompare(b.tag))
    .map(n =>
      `<div class="tagrow${n.listed ? "" : " unlisted"}" data-tag="${esc(n.tag)}"` +
      ` title="${esc(n.meaning || (n.listed ? "" : "carried by notes, not in the inventory"))}">` +
      `<span class="caret" data-caret="${esc(n.tag)}">${n.children ? "\u25b8" : ""}</span>` +
      `<a href="${tagHash(n.tag)}">${esc(n.name)}</a><span class="n">${n.notes}</span></div>` +
      (n.children ? `<div class="tagkids" data-kids="${esc(n.tag)}">${renderTagLevel(n.tag)}</div>`
                  : "")).join("");
}

async function loadTags() {
  TAGS = await api("/api/tags");
  const all = allTagNodes();
  $("#tags-h").style.display = all.length ? "" : "none";
  $("#tagnames").innerHTML = all.map(n => `<option value="${esc(n.tag)}">`).join("");
  $("#tagtree").innerHTML = renderTagLevel("");
  $("#tagtree").querySelectorAll("[data-caret]").forEach(caret => caret.onclick = () => {
    const kids = $("#tagtree").querySelector(`[data-kids="${CSS.escape(caret.dataset.caret)}"]`);
    if (!kids) return;
    const open = kids.classList.toggle("open");
    caret.textContent = open ? "\u25be" : "\u25b8";
  });
}

// A tag is not a note either: no file, so no edit control, no history and no lock.
async function openTagListing(name) {
  const tag = (name || "").toLowerCase().replace(/^\/+|\/+$/g, "");
  const node = allTagNodes().find(n => n.tag === tag);
  CURRENT = null; DIRTY = false;
  setView("note");
  $("#where").textContent = tag + "  (tag)";
  $("#note").classList.remove("dim", "live");
  const found = await api("/api/search", { q: "", tag, k: 50 });
  const parts = tag.split("/");
  const crumbs = parts.map((part, i) =>
    `<a href="${tagHash(parts.slice(0, i + 1).join("/"))}">${esc(part)}</a>`).join(" / ");
  const kids = allTagNodes().filter(n => n.parent === tag).map(n =>
    `<span class="tagchip"><a href="${tagHash(n.tag)}">${esc(n.name)}</a> ${n.notes}</span>`).join(" ");
  const notes = (found.hits || []).map(h =>
    `<div class="tagnote"><a href="#" data-p="${esc(h.path)}">${esc(h.title || h.path)}</a> ` +
    `<span class="dim">${esc(h.path)} \u00b7 ${esc(h.text || "")}</span></div>`).join("");
  $("#note").innerHTML =
    `<div class="termcard tagcard"><h2>${crumbs}</h2>` +
    (node && node.meaning ? `<p>${esc(node.meaning)}</p>` : "") +
    `<p><span class="chip">${node ? node.notes : 0} note${node && node.notes === 1 ? "" : "s"} under it</span>` +
    `<span class="chip">${node ? node.direct : 0} carrying it directly</span>` +
    (node && !node.listed ? `<span class="chip">not in the inventory</span>` : "") + `</p>` +
    (kids ? `<p class="tags">${kids}</p>` : "") +
    `<p><a href="#tags+${encodeURIComponent(tag)}">Show it in the tag graph</a></p>` +
    (notes || `<p class="dim">${esc(found.reason || "No note carries this tag.")}</p>`) +
    `</div>`;
  $("#note").querySelectorAll("a[data-p]").forEach(a =>
    a.onclick = ev => { ev.preventDefault(); openNote(a.dataset.p); });
  document.body.dataset.rendered = "+" + tag;
}

// `#graph` opens the graph, anything else is a note path. No note is called "graph" - every one
// of them ends in .md or .mmd - so the two cannot collide.
function route() {
  let raw = decodeURIComponent(location.hash.slice(1));
  // `~<date>` anywhere in the hash reads the vault as it stood that day: `#reg/psd2.md~2024-06-01`,
  // or `#~2024-06-01` for the tree alone. `~` is legal in a fragment and unused by the shapes
  // below, which already claim `:` for a line and `@` for a diagram.
  const tilde = raw.match(/^(.*?)~(\d{4}-\d{2}-\d{2})$/);
  if (tilde) { raw = tilde[1]; if (tilde[2] !== AS_OF) { setAsOf(tilde[2], raw); return; } }
  else if (AS_OF && !location.hash.includes("~")) { setAsOf("", raw); return; }
  // `#!<term>` is a glossary entry, which is not a note and has no file behind it.
  if (raw.startsWith("!")) { openTerm(raw.slice(1)); return; }
  // `#+<tag>` lists the notes under a tag. `+` cannot appear in a tag, and a note path ends in an
  // extension a tag cannot contain, so the two cannot collide.
  if (raw.startsWith("+") && !/\.(md|markdown|mdx|mmd)$/i.test(raw)) {
    openTagListing(raw.slice(1)); return;
  }
  if (raw === "graph") { setView("graph"); return; }
  // `#tags` draws the tag tree; `#tags+<tag>` draws one subtree with its notes as leaves.
  if (raw === "tags" || raw.startsWith("tags+")) { setView("tags", raw.slice(5)); return; }
  // `#<path>@<n>` opens the note and blows up its nth diagram, so a diagram can be linked to.
  const at = raw.lastIndexOf("@");
  let wanted = at > 0 ? raw.slice(0, at) : raw;
  const which = at > 0 ? parseInt(raw.slice(at + 1), 10) : 0;
  // `#<path>:<line>` opens a note at a line — the shape a search hit and a citation both use.
  let line = 0;
  const colon = wanted.match(/^(.*\.(?:md|markdown|mdx)):(\d+)$/i);
  if (colon) { wanted = colon[1]; line = Number(colon[2]); }
  if (!wanted) return;
  const after = () => {
    if (!which) return;
    const figures = $("#note").querySelectorAll(".figure");
    const figure = figures[which - 1];
    if (figure) openOverlay(figure.querySelector(".mermaid"), `${wanted}  \u00b7 diagram ${which}`);
  };
  if (!CURRENT || CURRENT.path !== wanted) openNote(wanted, line).then(after);
  else { if (line) jumpToLine(line); after(); }
}

addEventListener("hashchange", route);

// --- the sidebar, which is a drawer on a phone -------------------------------------------
// Wide screens remember what you chose; a phone always starts with the note, because a drawer
// covering the note is not a useful thing to open onto.

const NARROW = () => matchMedia("(max-width: 760px)").matches;

function setNav(open, remember = true) {
  document.body.dataset.nav = open ? "open" : "closed";
  if (remember && !NARROW()) {
    try { localStorage.setItem("wiki-nav", open ? "open" : "closed"); } catch (e) {}
  }
}

$("#nav").onclick = () => setNav(document.body.dataset.nav !== "open");

// On a phone, opening a note closes the drawer - you asked for the note, not the list.
function navAfterOpen() { if (NARROW()) setNav(false, false); }

// Tapping the dimmed area beside the drawer closes it, which is what every drawer does.
addEventListener("pointerdown", ev => {
  if (!NARROW() || document.body.dataset.nav !== "open") return;
  if (ev.target.closest("aside") || ev.target.closest("#nav")) return;
  setNav(false, false);
});

(() => {
  let saved = null;
  try { saved = localStorage.getItem("wiki-nav"); } catch (e) {}
  setNav(NARROW() ? false : saved !== "closed", false);
})();
matchMedia("(max-width: 760px)").addEventListener("change", ev => {
  let saved = null;
  try { saved = localStorage.getItem("wiki-nav"); } catch (e) {}
  setNav(ev.matches ? false : saved !== "closed", false);
});

// --- reading the vault as it stood on a date ---------------------------------------------
// The store has carried validity windows all along; nothing could ask it for them. Setting a date
// re-reads everything, because a page where only the tree time-travelled would mislead worse than
// one that cannot travel at all.

async function setAsOf(date, keepPath) {
  AS_OF = date || "";
  document.body.dataset.asof = AS_OF;
  $("#asof").value = AS_OF;
  $("#asof-now").style.display = AS_OF ? "" : "none";
  $("#asof-bar").textContent = AS_OF
    ? `Reading this vault as it stood on ${AS_OF} \u2014 notes outside that window are hidden.`
    : "";
  const path = keepPath !== undefined ? keepPath : (CURRENT ? CURRENT.path : "");
  CURRENT = null;
  await boot();
  if (path) {
    const wanted = AS_OF ? `${path}~${AS_OF}` : path;
    if (decodeURIComponent(location.hash.slice(1)) !== wanted) location.hash = wanted;
    else route();
  }
}

$("#asof").onchange = () => {
  const path = CURRENT ? CURRENT.path : "";
  location.hash = $("#asof").value ? `${path}~${$("#asof").value}` : path;
  if (!location.hash || location.hash === "#") setAsOf($("#asof").value, "");
};
$("#asof-now").onclick = () => {
  const path = CURRENT ? CURRENT.path : "";
  location.hash = path;
  if (!path) setAsOf("", "");
};

// The filters take a glob and an extension list. Nobody remembers a vault's folder names, and a
// typo just returns nothing with no hint why - so the vault fills its own completions.
// Every filename in the vault, offered as you type. Finding a file you know the name of should
// not require knowing enough of it to produce a hit.
function fillNames(tree) {
  const names = new Set();
  [...(tree.notes || []), ...(tree.diagrams || []), ...(tree.sources || [])]
    .forEach(e => names.add(e.path.split("/").pop()));
  $("#names").innerHTML = [...names].sort()
    .map(v => `<option value="${esc(v)}">`).join("");
}

function fillFilters(tree) {
  const everything = [...tree.notes, ...(tree.diagrams || []),
                     ...(tree.sources || [])].map(n => n.path);
  const folders = new Set();
  everything.forEach(path => {
    const parts = path.split("/");
    // Every ancestor, not just the immediate parent: `processes/*` has to be offered as well as
    // `processes/account-opening/*`.
    for (let i = 1; i < parts.length; i++) folders.add(parts.slice(0, i).join("/"));
  });
  const globs = [...folders].sort().map(f => `${f}/*`);
  $("#paths").innerHTML = globs.concat(everything.sort())
    .map(v => `<option value="${esc(v)}">`).join("");

  const exts = [...new Set(everything.map(p => p.slice(p.lastIndexOf("."))).filter(e => e))];
  $("#exts").innerHTML = exts.sort().map(v => `<option value="${esc(v)}">`).join("");
}

// Nest the note paths into a real directory tree. The sidebar used to render one flat row per
// folder, labelled with the folder's WHOLE path - so `a/b/c` sat beside `a` and `a/b`, and every
// ancestor was repeated on every line. A tree has one row per path segment, and each row opens on
// its own.
// Everything the vault holds, as one list. A `.py` beside a note is part of that folder, and a
// standalone `.mmd` is too - listing them in flat sections of their own meant a folder in the tree
// looked to hold only its markdown, while the rest sat below with no folder structure at all.
function treeEntries(tree) {
  const all = [
    ...(tree.notes || []).map(n => ({ ...n, kind: "note" })),
    ...(tree.diagrams || []).map(d => ({ ...d, kind: "diagram" })),
    ...(tree.sources || []).map(s => ({ ...s, kind: "source", why: s.lang })),
  ];
  // One file, one row. A `.csv` is both a scanned note and an openable source, so the merged list
  // holds it twice; first entry wins, which keeps the note's own title.
  const seenPaths = new Set();
  return all.filter(e => !seenPaths.has(e.path) && seenPaths.add(e.path));
}

const KIND_MARK = { diagram: "\u25C7 ", source: "</> " };

// A file tree is how you find a file whose NAME you know, so the name is the label - the same
// choice every editor and every notes app makes. Labelling rows by the note's `#` heading instead
// made three different files read as `Python 3.12.7`: they were `requirements.txt` and its two
// platform variants, each opening with a `# Python 3.12.7` comment.
function leafName(entry) {
  return entry.path.split("/").pop();
}

// The heading is not thrown away - it rides beside the name, and only when it adds something the
// filename does not already say.
function leafHint(entry) {
  const name = leafName(entry);
  const stem = name.replace(/\.[^.]+$/, "");
  const title = (entry.title || "").trim();
  const extra = entry.why || "";
  if (!title || title === name || title.toLowerCase() === stem.toLowerCase()) return extra;
  return extra ? `${title} \u00b7 ${extra}` : title;
}

function buildFolderTree(notes) {
  const root = { name: "", path: "", dirs: new Map(), notes: [], count: 0 };
  (notes || []).forEach(n => {
    const parts = n.folder ? n.folder.split("/") : [];
    let node = root;
    parts.forEach((part, i) => {
      if (!node.dirs.has(part))
        node.dirs.set(part, { name: part, path: parts.slice(0, i + 1).join("/"),
                              dirs: new Map(), notes: [], count: 0 });
      node = node.dirs.get(part);
      node.count++;                     // every ancestor counts what is beneath it
    });
    node.notes.push(n);
  });
  return root;
}

function renderFolder(node) {
  const kids = [...node.dirs.values()].sort((a, b) => a.name.localeCompare(b.name));
  const inner = kids.map(renderFolder).join("")
    + node.notes
        .slice()
        .sort((a, b) => leafName(a).localeCompare(leafName(b)))
        .map(n => {
          const hint = leafHint(n);
          return `<div class="hit" data-p="${esc(n.path)}" data-kind="${esc(n.kind || "note")}">` +
                 `${esc(KIND_MARK[n.kind] || "")}${esc(leafName(n))}` +
                 (hint ? `<span class="sub">${esc(hint)}</span>` : "") +
                 `</div>`;
        }).join("");
  // The root is the container, not a row: notes sitting at the vault root render at top level.
  if (!node.path) return inner;
  const total = node.count || node.notes.length;
  return `<div class="folder" data-f="${esc(node.path)}"><span class="caret">&#9656;</span>` +
         `<span>${esc(node.name)}</span><span class="n">${total}</span></div>` +
         `<div class="folder-notes" data-for="${esc(node.path)}">${inner}</div>`;
}

// Typeset one rendered subtree. Called after mermaid has run and after the highlighter, so a `$`
// inside a fence or a diagram is never touched. A vault that carries no mathematics pays nothing:
// MathJax finds no delimiters and returns.
async function typesetNote(scope) {
  if (!window.MathJax || !MathJax.typesetPromise) return;
  try { await MathJax.typesetPromise([scope]); }
  catch (e) { /* one bad formula never stops the note */ }
}

function toggleFolder(folder, force) {
  const row = document.querySelector(`#tree .folder[data-f="${CSS.escape(folder)}"]`);
  const body = document.querySelector(`#tree .folder-notes[data-for="${CSS.escape(folder)}"]`);
  if (!row || !body) return;
  const open = force === undefined ? !body.classList.contains("open") : force;
  body.classList.toggle("open", open);
  row.classList.toggle("open", open);
}

function wireHits(scope) {
  document.querySelectorAll(scope + " .hit").forEach(h => {
    if (h.classList.contains("noopen")) return;      // a glossary term has no file to open
    h.onclick = () => openNote(h.dataset.p, Number(h.dataset.line) || 0);
  });
}

// --- reading ---------------------------------------------------------------------------

async function openNote(path, line) {
  if (DIRTY && !confirm("You have unsaved changes. Leave them?")) return;
  const note = await api("/api/note", { path });
  if (note.error) { toast(note.error); return; }
  // The note in the address bar, so a reload keeps your place and a link can be shared.
  const current = decodeURIComponent(location.hash.slice(1));
  const bare = current.split("@")[0].replace(/~\d{4}-\d{2}-\d{2}$/, "").replace(/:\d+$/, "");
  const stamp = AS_OF ? `~${AS_OF}` : "";
  if (current !== path && bare !== path)
    location.hash = (line ? `${path}:${line}` : path) + stamp;
  CURRENT = note; DIRTY = false;
  closeHistory();
  // Reaching a note from search, a link or the address bar opens the folder holding it, so the
  // sidebar always shows where you are.
  toggleFolder(path.includes("/") ? path.slice(0, path.lastIndexOf("/")) : "", true);
  const kindLabel = { diagram: "  (diagram)", source: `  (${note.lang || "code"})` };
  $("#where").textContent = path + (kindLabel[note.kind] || "");
  navAfterOpen();
  $("#edit").value = note.markdown || "";
  setView("note");
  await render(note);
  if (line) jumpToLine(line);
}

// A note's tags: a chip each, linking into the tag tree. With the lock open a chip can be removed
// and one added - picked from the vault's own tree, or typed new. The edit is NOT a write of its
// own: it rides on Save, through the same PUT as the text, and the server is what rewrites the
// frontmatter line and lists a tag the vault has never seen.
function renderTagRow() {
  const row = $("#notetags");
  if (!row) return;
  const tags = (CURRENT && CURRENT.tags) || [];
  const editable = UNLOCKED && !READ_ONLY && CURRENT && CURRENT.kind === "note";
  row.style.display = (tags.length || editable) ? "" : "none";
  row.innerHTML = tags.map(tag =>
    `<span class="tagchip"><a href="${tagHash(tag)}">${esc(tag)}</a>` +
    (editable ? `<button data-untag="${esc(tag)}" title="remove this tag">\u00d7</button>` : "") +
    `</span>`).join("") +
    (editable ? `<input id="tagadd" list="tagnames" placeholder="add a tag\u2026" ` +
                `autocomplete="off">` : "");
  row.querySelectorAll("[data-untag]").forEach(button =>
    button.onclick = () => editTags(tags.filter(tag => tag !== button.dataset.untag)));
  const add = row.querySelector("#tagadd");
  if (add) add.onchange = () => { if (add.value.trim()) editTags([...tags, add.value]); };
}

function editTags(next) {
  const cleaned = next.map(tag => tag.trim().toLowerCase().replace(/^#/, "")).filter(Boolean);
  CURRENT.tags = [...new Set(cleaned)];
  CURRENT.tagsEdited = true;
  DIRTY = true;
  renderTagRow();
}

async function render(note) {
  // `body` is the note without its frontmatter. Handing the raw file to a markdown renderer turns
  // the opening `---` into a horizontal rule and the keys into a paragraph of "author: ... type:
  // ..." across the top of every note. The keys are metadata, so they get shown as metadata.
  // The ORIGINAL body, not a rewritten copy. The `[[wikilink]]` rewrite below is a display
  // convenience, and a block whose stored source had been rewritten would save back `[x](x.md)`
  // where the author wrote `[[x]]` - a silent edit, which is the one thing the editor may not do.
  const md = note.body !== undefined ? note.body : (note.markdown || "");
  $("#note").classList.remove("dim");
  // Tags leave the metadata strip: they are links into the tag tree, and editable, so they get
  // a row of their own.
  const pairs = (note.frontmatter || []).filter(([k]) => k !== "tags");
  const fm = pairs.length
    ? `<div class="fm">` + pairs.map(([k, v]) =>
        `<span><b>${esc(k)}</b>${esc(v)}</span>`).join("") + `</div>`
    : "";
  // Render token by token so every top-level block carries the source line it started on.
  // Without that a search hit can only open the file; with it, it can land on the sentence.
  // Two things a reader needs before acting on a note, both from relations already in the graph.
  // The supersede banner shows in EVERY mode: "this was replaced" is never not worth saying.
  let banners = "";
  if (note.superseded_by)
    banners += `<div class="banner stale">Superseded by ` +
      `<a href="#" data-p="${esc(note.superseded_by.path)}">` +
      `${esc(note.superseded_by.title || note.superseded_by.path)}</a>.</div>`;
  if (AS_OF && note.valid_now === false)
    banners += `<div class="banner">This note was not valid on ${esc(AS_OF)}` +
      (note.valid_from ? ` \u2014 it starts ${esc(note.valid_from)}` : "") +
      (note.valid_until ? `, it ends ${esc(note.valid_until)}` : "") + `.</div>`;
  $("#note").innerHTML = banners + fm + `<div class="tags" id="notetags"></div>` +
    (window.marked ? blocksWithLines(md) : "<pre>" + esc(md) + "</pre>");
  renderTagRow();

  // ```mermaid fences arrive as <pre><code class="language-mermaid">; mermaid wants its own node.
  $("#note").querySelectorAll("code.language-mermaid").forEach(code => {
    const box = document.createElement("pre");
    box.className = "mermaid";
    box.textContent = code.textContent;
    // Keep the source: mermaid.run replaces the node's text with an <svg>, and the .mmd download
    // needs what was written, not what was drawn.
    box.dataset.src = code.textContent;
    code.closest("pre").replaceWith(box);
  });
  const nodes = [...$("#note").querySelectorAll(".mermaid")];
  nodes.forEach((box, i) => {
    const figure = document.createElement("div");
    figure.className = "figure";
    box.replaceWith(figure);
    figure.append(box);
    if (!box.dataset.src && note.source) box.dataset.src = note.source;
    const button = document.createElement("button");
    button.className = "zoom";
    button.type = "button";
    button.textContent = "\u2921 Expand";
    button.title = "open full screen — drag to pan, scroll or pinch to zoom";
    button.onclick = () => {
      location.hash = `${note.path}@${i + 1}`;
      openOverlay(box, `${note.path}  \u00b7 diagram ${i + 1}`);
    };
    figure.append(button);
  });
  // `rendered` flips only once every diagram has finished drawing. It is what a test - or a
  // person waiting on a slow page - can watch, instead of guessing when async work is done.
  document.body.dataset.rendered = "";
  if (nodes.length && window.mermaid) {
    try { await mermaid.run({ nodes }); }
    catch (e) { nodes.forEach(n => n.classList.add("dim")); toast("a diagram failed to draw"); }
  }
  // Colour every fence except the ones mermaid owns - those have already been replaced by a
  // drawing, and a highlighter would be painting the source of a picture nobody is looking at.
  highlightCode($("#note"));
  await typesetNote($("#note"));
  // The vault's own vocabulary, marked where it actually appears. Done after mermaid has run, so
  // a term inside a drawn diagram is never touched.
  decorateTerms($("#note"));
  // The banner's successor link is an in-app jump, not a navigation.
  $("#note").querySelectorAll(".banner a[data-p]").forEach(a =>
    a.onclick = ev => { ev.preventDefault(); openNote(a.dataset.p); });
  if (UNLOCKED && !SRC_MODE) liveEdit(true);
  document.body.dataset.rendered = note.path;
  // An <img src> is a path relative to the NOTE, exactly like a link, and the browser would
  // otherwise resolve it against the page root and 404. Same resolve() the links already use.
  $("#note").querySelectorAll("img").forEach(img => {
    const src = img.getAttribute("src") || "";
    if (/^(?:[a-z]+:|data:|\/media\?)/i.test(src)) return;
    const rel = src.startsWith("/") ? src.slice(1) : resolve(note.path, src);
    img.setAttribute("src", "/media?path=" + encodeURIComponent(rel));
    img.loading = "lazy";
    // A missing image is a fact about the vault, not a mystery: say which path did not resolve.
    img.onerror = () => {
      const gone = document.createElement("span");
      gone.className = "dim";
      gone.textContent = `\u26a0 image not found: ${rel}`;
      img.replaceWith(gone);
    };
  });
  // A link to another note opens it here rather than navigating away from the app.
  $("#note").querySelectorAll("a[href]").forEach(a => {
    const href = a.getAttribute("href");
    if (!href || /^[a-z]+:/i.test(href) || href.startsWith("#")) return;
    a.onclick = ev => { ev.preventDefault(); openNote(resolve(CURRENT.path, href)); };
  });
  if (note.backlinks && note.backlinks.length) {
    const back = document.createElement("p");
    back.className = "dim";
    back.innerHTML = "Linked from: " + note.backlinks.map(b =>
      `<a href="#" data-p="${esc(b.path)}">${esc(b.path)}</a>`).join(", ");
    $("#note").append(back);
    back.querySelectorAll("a").forEach(a =>
      a.onclick = ev => { ev.preventDefault(); openNote(a.dataset.p); });
  }
}

// `[[target|label]]` -> `[label](target.md)`. Display only: the source a block stores is what the
// author typed, never this.
function wikilinks(md) {
  return md.replace(/\[\[([^\]|]+)(\|[^\]]+)?\]\]/g,
    (_, target, label) => `[${(label || "|" + target).slice(1)}](${target}.md)`);
}

// Every top-level block carries the source LINE it started on and the source TEXT it was made
// from. The line is what lets a search hit land on a sentence; the text is what lets the editor
// hand one block back as markdown without re-parsing the file - and what it saves back.
// A missing highlighter is not a broken page: the code still reads, just without colour. Same
// degradation the diagram bundle already has.
function highlightCode(root) {
  if (!root || !window.hljs) return;
  root.querySelectorAll("pre code").forEach(code => {
    if (code.classList.contains("language-mermaid") || code.dataset.hl) return;
    code.dataset.hl = "1";
    try { hljs.highlightElement(code); } catch (e) { /* one bad fence never stops the note */ }
  });
}

function blocksWithLines(md) {
  let tokens;
  try { tokens = marked.lexer(md); }
  catch (e) { return marked.parse(wikilinks(md)); }
  let line = 1, out = "";
  for (const token of tokens) {
    const at = line;
    line += (token.raw.match(/\n/g) || []).length;
    let html;
    try { html = marked.parser(marked.lexer(wikilinks(token.raw))); }
    catch (e) { html = "<pre>" + esc(token.raw) + "</pre>"; }
    out += `<div data-line="${at}" data-src="${encodeURIComponent(token.raw)}">${html}</div>`;
  }
  return out;
}

function jumpToLine(line) {
  const blocks = [...$("#note").querySelectorAll("[data-line]")];
  if (!blocks.length || !line) return;
  // The last block that starts at or before the target line is the one containing it.
  let target = blocks[0];
  for (const block of blocks) {
    if (Number(block.dataset.line) <= line) target = block; else break;
  }
  // The flash fades; the mark stays until you navigate away, so you can still see which block
  // the search actually landed you on after the animation is over.
  $("#note").querySelectorAll("[data-hit]").forEach(b => delete b.dataset.hit);
  target.dataset.hit = "1";
  target.classList.add("hit-line");
  target.scrollIntoView({ block: "center" });
  setTimeout(() => target.classList.remove("hit-line"), 2000);
}

function highlight(text, query) {
  const terms = (query || "").split(/\s+/).filter(w => w.length > 1)
    .map(w => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  let out = esc(text);
  if (!terms.length) return out;
  return out.replace(new RegExp("(" + terms.join("|") + ")", "gi"), "<mark>$1</mark>");
}

function resolve(from, href) {
  const base = from.includes("/") ? from.slice(0, from.lastIndexOf("/")).split("/") : [];
  href.split("/").forEach(part => {
    if (part === "..") base.pop(); else if (part !== ".") base.push(part);
  });
  return base.join("/").replace(/[?#].*$/, "");
}

// --- searching -------------------------------------------------------------------------

let searchTimer = null;
// Emptying the box already restores the tree - what was missing was any way to DO that other
// than selecting the text and deleting it. A visible x, and Escape while the box has focus.
// What is read at a glance: how many hits, and out of how much. Nothing else.
function statusLine(found, cov) {
  const n = found.total || found.hits.length;
  const seen = cov && cov.total && cov.searchable < cov.total
    ? ` \u00b7 ${cov.searchable}/${cov.total} notes` : "";
  return `${n} hit${n === 1 ? "" : "s"}${seen}`;
}

// Everything the line used to say, kept in full for whoever hovers it.
function statusDetail(found, extra) {
  const how = { rag: "semantic", text: "names and prose", sqlite: "titles only",
                tags: "every note under the tag" };
  return [how[found.backend] || found.backend].concat(extra).join(" \u00b7 ");
}

function showResults(on) {
  $("#results").style.display = on ? "" : "none";
}

function clearSearch() {
  $("#q").value = "";
  $("#hits").innerHTML = "";
  $("#backend").textContent = "";
  $("#q-clear").style.display = "none";
  showResults(false);
  $("#q").focus();
}

$("#q-clear").onclick = clearSearch;
$("#q").onkeydown = ev => { if (ev.key === "Escape") { ev.preventDefault(); clearSearch(); } };
$("#q").oninput = () => {
  const typed = $("#q").value.trim();
  $("#q-clear").style.display = $("#q").value ? "" : "none";
  clearTimeout(searchTimer);
  if (!typed) { clearSearch(); return; }
  // Said the moment you stop typing, not when the answer lands: a search over a large vault takes
  // long enough that a still panel reads as "no results" rather than "still looking".
  showResults(true);
  $("#backend").innerHTML = `<span class="spin"></span>searching\u2026`;
  $("#hits").innerHTML = "";
  searchTimer = setTimeout(runSearch, 220);
};
$("#fpath").onchange = $("#fext").onchange = $("#ftag").onchange = runSearch;

let SEARCH_SEQ = 0;
// How many hits this query has asked for so far. Grows only when the reader asks for more, and
// resets on every new question - otherwise one deep search makes every later one expensive.
let SEARCH_K = 12;

async function runSearch() {
  const q = $("#q").value.trim();
  const tag = $("#ftag").value.trim();
  if (q !== runSearch._last) { SEARCH_K = 12; runSearch._last = q; }   // a new question, page one
  // A tag alone is a question too: it lists the notes under that node.
  if (!q && !tag) { $("#hits").innerHTML = ""; $("#backend").textContent = ""; showResults(false); return; }
  showResults(true);
  // A slower earlier query used to land after a newer one and overwrite it, leaving results that
  // did not match the box. The answer is only written if it is still the latest question asked.
  const seq = ++SEARCH_SEQ;
  const found = await api("/api/search",
    { q, k: SEARCH_K, path: $("#fpath").value.trim(), ext: $("#fext").value.trim(), tag });
  if (seq !== SEARCH_SEQ) return;
  // Always name the backend. A literal match that reads like a semantic one is the failure this
  // line exists to prevent.
  const how = { rag: "semantic", text: "names and prose", sqlite: "titles only" };
  const extra = [];
  // What it could SEE, not just which backend answered. "sqlite · 0 hits" read like an answer
  // when it meant "I never opened a note" - the coverage line is what makes that impossible.
  const cov = found.coverage;
  if (cov && cov.total) {
    extra.push(cov.searchable >= cov.total
      ? `read all ${cov.total} notes`
      : `read only ${cov.searchable} of ${cov.total} notes`);
  }
  if (found.backend === "text" && found.scanned && !cov) extra.push(`scanned ${found.scanned} files`);
  if (found.backend === "rag" && found.reranked === false) extra.push("not reranked");
  if (found.backend !== "rag" && found.reason) extra.push(found.reason);
  // A filter that removes hits says so, or a short list reads as "that is all there is".
  if (found.tag) extra.push(found.tag_hidden
    ? `${found.tag_hidden} hit${found.tag_hidden === 1 ? "" : "s"} outside the tag ${found.tag}`
    : `under the tag ${found.tag}`);
  (found.notes || []).forEach(n => extra.push(n));
  // Someone who just typed a word is reading for the hit count, not for why the semantic index is
  // unavailable and which command repairs it. All of that stays - on the tooltip, where it is
  // there when wanted and silent when not.
  $("#backend").innerHTML = `<span title="${esc(statusDetail(found, extra))}">` +
                            `${esc(statusLine(found, cov))}</span>`;
  // One card per NOTE, with its matching lines on it. A note that says the word four times used
  // to push three other notes off the list; grouped, the list is a list of documents again and
  // the lines are what you choose between inside one.
  const byNote = [];
  const at = new Map();
  found.hits.forEach(h => {
    const key = h.path + "\u0000" + (h.kind || "note");
    if (!at.has(key)) { at.set(key, byNote.length); byNote.push({ head: h, lines: [] }); }
    if (h.line) byNote[at.get(key)].lines.push(h);
  });

  const said = { title: "in the name", text: "in the text", concept: "glossary", tag: "tagged",
                 rerank: "reranked", hybrid: "hybrid", vector: "semantic" };
  $("#hits").innerHTML = byNote.map(({ head, lines }) => {
    const why = head.matched_by
      ? `<span class="why">${esc(said[head.matched_by] || head.matched_by)}`
        + `${head.score != null ? " " + head.score.toFixed(2) : ""}</span>`
      : "";
    // A glossary term is not a note. Marking it stops the card offering a click that 404s.
    const cls = head.openable === false ? "hit noopen" : "hit";
    const label = head.kind === "concept"
      ? `${esc(head.path)} <span class="why">glossary</span>`
      : esc(head.title || head.path);
    const where = head.kind === "concept" ? "" : `<div class="crumbs">${esc(head.path)}</div>`;
    // Each line is its own click target: the card opens the note, a line opens that line.
    const rows = lines.map(l =>
      `<div class="ln" data-p="${esc(l.path)}" data-line="${l.line}">` +
      `<span class="lno">${l.line}</span>` +
      `<span class="t">${highlight(l.text.slice(0, 260), q)}</span>` +
      (l.heading_path ? `<span class="crumbs">${esc(l.heading_path)}</span>` : "") +
      `</div>`).join("");
    return `<div class="${cls}" data-p="${esc(head.path)}">` +
           why + `<div class="p">${label}</div>` + where + rows + `</div>`;
  }).join("")
  // k is a page size, never a claim about how much exists. Say the real number and offer the rest.
  + (found.truncated
      ? `<button id="more" class="more">Show more \u2014 ${found.total} matches in all</button>`
      : "");
  showResults(true);
  wireHits("#hits");
  // A line inside a card is its own target and must not also trigger the card behind it.
  $("#hits").querySelectorAll(".ln").forEach(row => row.onclick = ev => {
    ev.stopPropagation();
    openNote(row.dataset.p, Number(row.dataset.line) || 0);
  });
  const more = $("#more");
  if (more) more.onclick = () => { SEARCH_K += 12; runSearch(); };
}
</script>
"""

PAGE_HTML += r"""<script>
// --- the lock, and the write it guards -------------------------------------------------

// --- editing in the rendered note -------------------------------------------------------
// Obsidian's model, and for the same reason: a vault whose notes are half diagrams is edited
// blind in a raw textarea. The document stays drawn; the block you put the caret in shows its
// markdown, and closing it re-renders that block - so a mermaid fence redraws the moment you
// leave it. Nothing else on the page changes, and the file is still saved by one PUT.
//
// A textarea per open block, rather than contenteditable over the whole note: the browser's own
// undo, selection and IME keep working inside it, and no keystroke can ever produce HTML that
// then has to be turned back into markdown.

let SRC_MODE = false;        // the plain whole-file textarea, kept as the escape hatch
let OPEN_BLOCK = null;

// Growth class: budgeted. One entry per block commit, capped, oldest evicted at the push below -
// an editing session that runs all afternoon holds 100 strings, not one per keystroke forever.
const UNDO_MAX = 100;
let UNDO = [];

function pushUndo(text) {
  if (UNDO.length && UNDO[UNDO.length - 1] === text) return;
  UNDO.push(text);
  if (UNDO.length > UNDO_MAX) UNDO.shift();
}

function blockSource(block) {
  const area = block.querySelector("textarea.blocksrc");
  return area ? area.value : decodeURIComponent(block.dataset.src || "");
}

// The frontmatter the render dropped, kept verbatim so saving can put it back. An editor that
// silently loses a note's frontmatter is data loss, not a display bug.
function frontMatterRaw() {
  if (!CURRENT || !CURRENT.markdown) return "";
  const body = CURRENT.body !== undefined ? CURRENT.body : CURRENT.markdown;
  return CURRENT.markdown.endsWith(body)
    ? CURRENT.markdown.slice(0, CURRENT.markdown.length - body.length) : "";
}

function docSource() {
  const blocks = [...$("#note").querySelectorAll(":scope > [data-line]")];
  return frontMatterRaw() + blocks.map(blockSource).join("");
}

async function closeBlock() {
  const block = OPEN_BLOCK;
  OPEN_BLOCK = null;
  if (!block) return;
  const area = block.querySelector("textarea.blocksrc");
  if (!area) return;
  const text = area.value;
  block.dataset.src = encodeURIComponent(text);
  let html;
  try { html = marked.parser(marked.lexer(wikilinks(text))); }
  catch (e) { html = "<pre>" + esc(text) + "</pre>"; }
  block.innerHTML = html;
  // A fence that was edited has to be drawn again, or the diagram on screen is the old one.
  const fences = [...block.querySelectorAll("code.language-mermaid")];
  fences.forEach(code => {
    const box = document.createElement("pre");
    box.className = "mermaid";
    box.textContent = code.textContent;
    box.dataset.src = code.textContent;
    code.closest("pre").replaceWith(box);
  });
  const nodes = [...block.querySelectorAll(".mermaid")];
  if (nodes.length && window.mermaid) {
    try { await mermaid.run({ nodes }); }
    catch (e) { nodes.forEach(n => n.classList.add("dim")); toast("that diagram will not draw"); }
  }
  highlightCode(block);
  await typesetNote(block);
  decorateTerms($("#note"));
  pushUndo(docSource());
}

async function openBlock(block) {
  if (OPEN_BLOCK === block) return;
  await closeBlock();
  const text = decodeURIComponent(block.dataset.src || "");
  const area = document.createElement("textarea");
  area.className = "blocksrc";
  area.spellcheck = false;
  area.value = text;
  block.innerHTML = "";
  block.append(area);
  area.style.height = Math.max(area.scrollHeight, 28) + "px";
  area.oninput = () => {
    DIRTY = true;
    area.style.height = "auto";
    area.style.height = Math.max(area.scrollHeight, 28) + "px";
  };
  area.onblur = () => { closeBlock(); };
  area.focus();
  OPEN_BLOCK = block;
}

function liveEdit(on) {
  $("#note").classList.toggle("live", !!on);
  if (!on) { closeBlock(); return; }
  pushUndo(docSource());
}

$("#note").addEventListener("mousedown", ev => {
  if (!UNLOCKED || SRC_MODE || VIEW !== "note" || !CURRENT) return;
  if (ev.target.closest("a, button, .figure")) return;   // a link, a control, a drawn diagram
  const block = ev.target.closest("#note > [data-line]");
  if (block && block !== OPEN_BLOCK) { ev.preventDefault(); openBlock(block); }
});

addEventListener("keydown", ev => {
  if (ev.key === "Escape" && OPEN_BLOCK) { closeBlock(); return; }
  if ((ev.metaKey || ev.ctrlKey) && ev.key === "z" && !ev.shiftKey
      && UNLOCKED && !SRC_MODE && !OPEN_BLOCK && UNDO.length > 1) {
    ev.preventDefault();
    UNDO.pop();
    const text = UNDO[UNDO.length - 1];
    CURRENT.markdown = text;
    CURRENT.body = text.slice(frontMatterRaw().length);
    render(CURRENT);
    DIRTY = true;
  }
});

$("#srcmode").onclick = () => {
  SRC_MODE = !SRC_MODE;
  $("#srcmode").classList.toggle("on", SRC_MODE);
  $("#srcmode").textContent = SRC_MODE ? "Rendered" : "Source";
  if (SRC_MODE) { closeBlock(); $("#edit").value = CURRENT ? docSource() : ""; }
  else if (CURRENT) { CURRENT.markdown = $("#edit").value;
                      CURRENT.body = CURRENT.markdown.slice(frontMatterRaw().length); }
  if (VIEW === "note") setView("note");
  if (!SRC_MODE && CURRENT) render(CURRENT);
};

// --- the lock, and the write it guards -------------------------------------------------

$("#lock").onclick = () => {
  if (READ_ONLY) return;
  if (UNLOCKED && DIRTY && !confirm("Discard unsaved changes?")) return;
  UNLOCKED = !UNLOCKED;
  $("#lock").classList.toggle("open", UNLOCKED);
  $("#lock").innerHTML = UNLOCKED ? "&#128275; Editing" : "&#128274; Locked";
  $("#lock").title = UNLOCKED ? "click to lock editing again" : "editing is locked";
  $("#save").classList.toggle("on", UNLOCKED);
  $("#srcmode").classList.toggle("on", UNLOCKED && SRC_MODE);
  $("#srcmode").style.display = UNLOCKED ? "" : "none";
  if (UNLOCKED) { UNDO = []; if (SRC_MODE) $("#edit").value = CURRENT ? docSource() : ""; }
  liveEdit(UNLOCKED && !SRC_MODE && !!CURRENT);
  renderTagRow();
  if (VIEW === "note") setView("note");
};
$("#srcmode").style.display = "none";

$("#edit").oninput = () => { DIRTY = true; };

$("#save").onclick = async () => {
  if (!UNLOCKED || !CURRENT) return;
  await closeBlock();
  const markdown = SRC_MODE ? $("#edit").value : docSource();
  // Tags travel only when a chip was edited. Sent on every save they would overwrite a tag the
  // author just typed into the frontmatter in Source mode.
  const fields = { path: CURRENT.path, markdown };
  if (CURRENT.tagsEdited) fields.tags = CURRENT.tags;
  const response = await fetch("/api/note", {
    method: "PUT",
    headers: { "Content-Type": "application/json", "X-Wiki-Token": TOKEN },
    body: JSON.stringify(fields),
  });
  const result = await response.json();
  if (!response.ok) { toast(result.error || "save refused"); return; }
  DIRTY = false;
  UNDO = [];
  const listed = result.inventory_added || [];
  if (CURRENT.tagsEdited || listed.length) {
    // The server rewrote the frontmatter line, so what is on disk is not what was sent.
    const fresh = await api("/api/note", { path: CURRENT.path });
    if (!fresh.error) CURRENT = fresh;
    await loadTags();
  } else {
    CURRENT.markdown = markdown;
    CURRENT.body = markdown.slice(frontMatterRaw().length);
    CURRENT.tags = result.tags || CURRENT.tags;
  }
  toast((result.backup ? "saved · previous version in .wiki/.trash/" : "saved") +
        (listed.length ? ` · new in the tag tree: ${listed.join(", ")}` : ""));
  await render(CURRENT);
};

addEventListener("keydown", ev => {
  if ((ev.metaKey || ev.ctrlKey) && ev.key === "s") { ev.preventDefault(); $("#save").click(); }
});
addEventListener("beforeunload", ev => { if (DIRTY) ev.preventDefault(); });

// --- which pane is showing -------------------------------------------------------------

// --- what this note used to say -------------------------------------------------------
// Every save copies the previous version to the trash. This is the half that was missing: seeing
// them, seeing what changed, and putting one back.

function stampLabel(at) {
  // 20260906T214233.123456 -> 2026-09-06 21:42:33
  const m = at.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})/);
  return m ? `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}:${m[6]}` : at;
}

function diffLines(before, after) {
  // Longest common subsequence over lines. Small enough for a note, and it means no dependency.
  const a = before.split("\n"), b = after.split("\n");
  const n = a.length, m = b.length;
  const grid = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--)
      grid[i][j] = a[i] === b[j] ? grid[i + 1][j + 1] + 1
                                 : Math.max(grid[i + 1][j], grid[i][j + 1]);
  const out = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) { out.push(["same", a[i]]); i++; j++; }
    else if (grid[i + 1][j] >= grid[i][j + 1]) { out.push(["del", a[i]]); i++; }
    else { out.push(["add", b[j]]); j++; }
  }
  while (i < n) out.push(["del", a[i++]]);
  while (j < m) out.push(["add", b[j++]]);
  return out;
}

function renderDiff(before, after) {
  const rows = diffLines(before, after);
  const changed = rows.filter(r => r[0] !== "same").length;
  if (!changed) return `<div class="dim">identical to what is on disk now</div>`;
  // Only changed lines and one line of context either side: a whole note of unchanged text is
  // not what anybody opened this to read.
  const keep = new Set();
  rows.forEach(([kind], i) => {
    if (kind === "same") return;
    for (let k = i - 1; k <= i + 1; k++) keep.add(k);
  });
  let body = "", gap = false;
  rows.forEach(([kind, text], i) => {
    if (!keep.has(i)) { if (!gap) { body += `<div class="dim">  …</div>`; gap = true; } return; }
    gap = false;
    const sign = kind === "add" ? "+" : kind === "del" ? "-" : " ";
    body += `<div class="${kind}">${esc(sign + " " + text)}</div>`;
  });
  return `<div class="dim">${changed} changed lines</div>` + body;
}

function closeHistory() { $("#history").classList.remove("on"); }

$("#hclose").onclick = closeHistory;
// A dialog closes on Esc and on a click outside it. Clicks inside must not reach the backdrop.
$("#history").onclick = ev => { if (ev.target === $("#history")) closeHistory(); };
addEventListener("keydown", ev => {
  if (ev.key === "Escape" && $("#history").classList.contains("on")) closeHistory();
});

async function showHistory() {
  if (!CURRENT) { toast("open a note first"); return; }
  const panel = $("#history");
  if (panel.classList.contains("on")) { closeHistory(); return; }
  const data = await api("/api/history", { path: CURRENT.path });
  const versions = data.versions || [];
  const list = panel.querySelector(".hlist");
  $("#hpath").textContent = CURRENT.path;
  if (!versions.length) {
    list.innerHTML = "";
    $("#diff").innerHTML = `<div class="hempty">No earlier versions of this note.<br><br>`
      + `A version is kept each time you save an edit here — so this fills up once you start `
      + `changing it.</div>`;
    panel.classList.add("on");
    return;
  }
  list.innerHTML = `<div class="dim" style="padding:4px 9px 8px">${versions.length} earlier `
    + `version${versions.length > 1 ? "s" : ""}, newest first</div>`
    + versions.map(v => `<div class="v" data-at="${esc(v.at)}"><span>${stampLabel(v.at)}</span>`
        + `<span class="sz">${v.bytes} B</span></div>`).join("");
  panel.classList.add("on");
  list.querySelectorAll(".v").forEach(row =>
    row.onclick = () => openVersion(row.dataset.at));
  openVersion(versions[0].at);
}

async function openVersion(at) {
  const panel = $("#history");
  panel.querySelectorAll(".v").forEach(v => v.classList.toggle("sel", v.dataset.at === at));
  const old = await api("/api/version", { path: CURRENT.path, at });
  if (old.error) { $("#diff").innerHTML = `<div class="dim">${esc(old.error)}</div>`; return; }
  $("#diff").innerHTML = renderDiff(old.text, CURRENT.markdown || "")
    + (READ_ONLY ? "" : `<p><button data-restore="${esc(at)}">Restore this version</button></p>`);
  const button = $("#diff").querySelector("[data-restore]");
  if (button) button.onclick = () => restoreVersion(at);
}

async function restoreVersion(at) {
  if (!UNLOCKED) { toast("open the lock first — restoring is an edit"); return; }
  const old = await api("/api/version", { path: CURRENT.path, at });
  if (old.error) { toast(old.error); return; }
  if (!confirm(`Put ${CURRENT.path} back to ${stampLabel(at)}? The current text is kept too.`))
    return;
  // A restore is an ordinary write: it goes through every gate and keeps a backup of what it
  // replaces, so restoring the wrong version is itself undoable.
  const response = await fetch("/api/note", {
    method: "PUT",
    headers: { "Content-Type": "application/json", "X-Wiki-Token": TOKEN },
    body: JSON.stringify({ path: CURRENT.path, markdown: old.text }),
  });
  const result = await response.json();
  if (!response.ok) { toast(result.error || "restore refused"); return; }
  toast(`restored to ${stampLabel(at)}`);
  closeHistory();
  await openNote(CURRENT.path);
}

$("#hist").onclick = showHistory;

// --- the diagram overlay ---------------------------------------------------------------
// A diagram is often wider than the column it sits in. Rather than shrink it to fit and make it
// unreadable, every drawn diagram can be opened full screen and moved around: drag to pan, wheel
// or pinch to zoom about the pointer, Fit to get back.

let VIEWPORT = { x: 0, y: 0, k: 1 };

function applyViewport() {
  $("#stage").firstElementChild.style.transform =
    `translate(${VIEWPORT.x}px, ${VIEWPORT.y}px) scale(${VIEWPORT.k})`;
}

function fitOverlay() {
  const { w, h } = NATURAL;
  if (!w || !h) return;
  const stage = $("#stage").getBoundingClientRect();
  const width = stage.width || innerWidth, height = stage.height || innerHeight;
  const k = Math.min((width - 60) / w, (height - 60) / h, 4);
  VIEWPORT = { k, x: (width - w * k) / 2, y: (height - h * k) / 2 };
  applyViewport();
}

let NATURAL = { w: 0, h: 0 };

function openOverlay(box, caption) {
  const svg = box.querySelector("svg");
  if (!svg) { toast("nothing drawn to open"); return; }
  // The size has to come from the viewBox, not from the copy's layout. Mermaid sizes its svg with
  // width="100%" and a max-width style; strip those and the clone has NO intrinsic dimensions, so
  // it lays out to nothing and the overlay looks empty. Measuring it afterwards cannot recover
  // that - it is already zero.
  const view = (svg.getAttribute("viewBox") || "").split(/[\s,]+/).map(Number);
  const shown = svg.getBoundingClientRect();
  const w = view[2] > 0 ? view[2] : shown.width || 800;
  const h = view[3] > 0 ? view[3] : shown.height || 600;
  NATURAL = { w, h };

  const layer = $("#stage").firstElementChild;
  layer.replaceChildren(svg.cloneNode(true));
  const copy = layer.querySelector("svg");
  copy.setAttribute("width", w);
  copy.setAttribute("height", h);
  copy.style.width = w + "px";
  copy.style.height = h + "px";
  copy.style.maxWidth = "none";
  layer.style.width = w + "px";
  layer.style.height = h + "px";

  OPEN_DIAGRAM = {
    source: box.dataset.src || (CURRENT && CURRENT.source) || "",
    name: (caption || "diagram").split("/").pop().replace(/[^\w.-]+/g, "-")
            .replace(/\.mmd$|\.md$/, "").replace(/^-+|-+$/g, "") || "diagram",
  };
  $("#overcap").textContent = caption || "";
  $("#overlay").classList.add("on");
  VIEWPORT = { x: 0, y: 0, k: 1 };
  applyViewport();
  fitOverlay();
}

function closeOverlay() {
  const raw = decodeURIComponent(location.hash.slice(1));
  if (raw.lastIndexOf("@") > 0) location.hash = raw.slice(0, raw.lastIndexOf("@"));
  $("#overlay").classList.remove("on");
  $("#stage").firstElementChild.replaceChildren();
}

function zoomAbout(factor, cx, cy) {
  const next = Math.min(12, Math.max(0.05, VIEWPORT.k * factor));
  const ratio = next / VIEWPORT.k;
  VIEWPORT.x = cx - (cx - VIEWPORT.x) * ratio;
  VIEWPORT.y = cy - (cy - VIEWPORT.y) * ratio;
  VIEWPORT.k = next;
  applyViewport();
}

$("#overbar").onclick = ev => {
  const what = ev.target.dataset.z, stage = $("#stage").getBoundingClientRect();
  if (ev.target.dataset.x) { exportDiagram(ev.target.dataset.x); return; }
  if (what === "close") closeOverlay();
  else if (what === "fit") fitOverlay();
  else if (what) zoomAbout(what === "in" ? 1.25 : 0.8, stage.width / 2, stage.height / 2);
};

// --- taking a diagram away with you ------------------------------------------------------
// SVG is the drawing, .mmd is what it was drawn FROM - both are worth having, and they are not
// interchangeable: only the source can be edited or re-rendered later.

let OPEN_DIAGRAM = { source: "", name: "diagram" };

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

function overlaySvg() {
  const svg = $("#stage").querySelector("svg");
  if (!svg) { toast("nothing open to export"); return null; }
  const copy = svg.cloneNode(true);
  copy.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  copy.setAttribute("width", NATURAL.w);
  copy.setAttribute("height", NATURAL.h);
  return new XMLSerializer().serializeToString(copy);
}

function exportDiagram(kind) {
  const name = OPEN_DIAGRAM.name;
  if (kind === "mmd") {
    if (!OPEN_DIAGRAM.source) { toast("the source for this diagram was not captured"); return; }
    saveBlob(new Blob([OPEN_DIAGRAM.source + "\n"], { type: "text/plain" }), name + ".mmd");
    return;
  }
  if (kind === "pdf") { print(); return; }   // the browser's own dialog, incl. Save as PDF
  const markup = overlaySvg();
  if (!markup) return;
  if (kind === "svg") {
    saveBlob(new Blob([markup], { type: "image/svg+xml" }), name + ".svg");
    return;
  }
  // PNG: paint the svg into a canvas at 2x, so it stays sharp when it is pasted somewhere.
  const scale = 2;
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(NATURAL.w * scale));
  canvas.height = Math.max(1, Math.round(NATURAL.h * scale));
  const image = new Image();
  image.onload = () => {
    const context = canvas.getContext("2d");
    context.fillStyle = getComputedStyle(document.body).backgroundColor || "#fff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => blob ? saveBlob(blob, name + ".png") : toast("could not make a PNG"));
  };
  image.onerror = () => toast("could not rasterise this diagram — SVG still works");
  // A data: URL, never a blob: one — img-src allows 'self' and data:, and nothing else.
  image.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(markup);
}

addEventListener("keydown", ev => {
  if (!$("#overlay").classList.contains("on")) return;
  if (ev.key === "Escape") closeOverlay();
  if (ev.key === "0") fitOverlay();
});

// A trackpad pinch reaches the page as a wheel event with ctrlKey set; a mouse wheel does not.
// Both mean zoom here, because the overlay has nothing else to scroll.
$("#stage").addEventListener("wheel", ev => {
  ev.preventDefault();
  const stage = $("#stage").getBoundingClientRect();
  const factor = Math.exp(-ev.deltaY * (ev.ctrlKey ? 0.01 : 0.0025));
  zoomAbout(factor, ev.clientX - stage.left, ev.clientY - stage.top);
}, { passive: false });

// Pointer events cover mouse drag and touch alike; two fingers down is a pinch.
const POINTERS = new Map();
let PINCH = 0;

$("#stage").addEventListener("pointerdown", ev => {
  $("#stage").setPointerCapture(ev.pointerId);
  POINTERS.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
  $("#stage").classList.add("drag");
});

$("#stage").addEventListener("pointermove", ev => {
  const previous = POINTERS.get(ev.pointerId);
  if (!previous) return;
  POINTERS.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
  const points = [...POINTERS.values()];
  if (points.length >= 2) {
    const spread = Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
    const stage = $("#stage").getBoundingClientRect();
    if (PINCH) {
      zoomAbout(spread / PINCH, (points[0].x + points[1].x) / 2 - stage.left,
                (points[0].y + points[1].y) / 2 - stage.top);
    }
    PINCH = spread;
    return;
  }
  VIEWPORT.x += ev.clientX - previous.x;
  VIEWPORT.y += ev.clientY - previous.y;
  applyViewport();
});

function releasePointer(ev) {
  POINTERS.delete(ev.pointerId);
  if (POINTERS.size < 2) PINCH = 0;
  if (!POINTERS.size) $("#stage").classList.remove("drag");
}
$("#stage").addEventListener("pointerup", releasePointer);
$("#stage").addEventListener("pointercancel", releasePointer);

// What #g is showing right now. Both graphs - the notes and the tag tree - go through the same
// layout and the same listeners, which are bound ONCE and read this. A second copy of the force
// loop per kind of graph is how one of them quietly stops getting the other's fixes.
let SCENE = null, SCENE_KIND = "";
let CAMERA = { x: 0, y: 0, k: 1 }, SELECTED = null, DRAG = null, PANNING = null;

function setView(next, tagRoot) {
  VIEW = next;
  // The raw textarea is now the ESCAPE HATCH, not the editor. Unlocking leaves the rendered note
  // on screen and edits it in place; only Source mode swaps in the whole-file textarea.
  const editing = next === "note" && UNLOCKED && SRC_MODE;
  $("#note").classList.toggle("off", next !== "note" || editing);
  $("#edit").classList.toggle("on", editing);
  $("#graph").classList.toggle("on", next === "graph" || next === "tags");
  // Lay it out against the real container. Drawn while hidden, every measurement is zero and the
  // layout falls back to a guessed canvas size.
  if (next === "graph" && SCENE_KIND !== "notes") drawGraph();
  if (next === "tags" && SCENE_KIND !== "tags:" + (tagRoot || "")) drawTagGraph(tagRoot || "");
}
$("#tab-note").onclick = () => setView("note");
$("#tab-graph").onclick = () => { location.hash = "graph"; setView("graph"); };
$("#tab-tags").onclick = () => { location.hash = "tags"; setView("tags", ""); };

// --- the graph, for seeing the shape of the whole thing --------------------------------
// A hand-rolled force layout: a CDN is unavailable offline and this page must work with nothing
// installed beyond the two bundles this server hands out.

function layoutScene(nodes, links, at, W, H) {
  for (let step = 0; step < 180; step++) {
    for (const a of nodes) for (const b of nodes) {
      if (a === b) continue;
      const dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy || 1;
      if (d2 < 40000) { a.x += dx / d2 * 220; a.y += dy / d2 * 220; }
    }
    for (const e of links) {
      const a = at[e.source], b = at[e.target];
      const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1, f = (d - 90) / d * 0.06;
      a.x += dx * f; a.y += dy * f; b.x -= dx * f; b.y -= dy * f;
    }
    for (const n of nodes) {
      n.x = Math.max(20, Math.min(W - 20, n.x + (W / 2 - n.x) * 0.002));
      n.y = Math.max(20, Math.min(H - 20, n.y + (H / 2 - n.y) * 0.002));
    }
  }
}

// A scene is what one graph IS, apart from how any graph is drawn:
//   nodes    [{ id, label, r?, cls? }]      links  [{ source, target, rel_type }]
//   address  what the page signals when it is on screen
//   meta     (nodeCount, linkCount) -> the line under the drawing
//   detail   id -> the selection panel's html      open  id -> what a double-click does
function drawScene(scene) {
  const svg = $("#g"), box = $("#graph").getBoundingClientRect();
  const W = box.width || 900, H = box.height || 600;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const nodes = scene.nodes;
  nodes.forEach((n, i) => {
    n.x = W / 2 + Math.cos(i) * (60 + i % 90);
    n.y = H / 2 + Math.sin(i) * (60 + i % 90);
  });
  const at = Object.fromEntries(nodes.map(n => [n.id, n]));
  const links = scene.links.filter(e => at[e.source] && at[e.target]);
  layoutScene(nodes, links, at, W, H);

  const make = (tag, attrs) => {
    const el = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
    return el;
  };

  // One transform group holds the whole scene, so panning and zooming is a single attribute
  // rather than 250 coordinate rewrites.
  const view = make("g", { id: "gview" });
  const drawn = new Map();          // id -> {node, dot, label, lines:[{line, end}]}
  const neighbours = new Map();     // id -> Set(id)

  nodes.forEach(n => {
    drawn.set(n.id, { node: n, lines: [] });
    neighbours.set(n.id, new Set());
  });
  links.forEach(e => {
    const line = make("line", { x1: at[e.source].x, y1: at[e.source].y,
                                x2: at[e.target].x, y2: at[e.target].y });
    line.dataset.rel = e.rel_type || "relates-to";
    view.append(line);
    drawn.get(e.source).lines.push({ line, end: 1 });
    drawn.get(e.target).lines.push({ line, end: 2 });
    neighbours.get(e.source).add(e.target);
    neighbours.get(e.target).add(e.source);
  });

  nodes.forEach(n => {
    const entry = drawn.get(n.id);
    const degree = neighbours.get(n.id).size;
    const dot = make("circle", { cx: n.x, cy: n.y,
                                 r: n.r != null ? n.r : 4 + Math.min(6, degree) });
    dot.dataset.p = n.id;
    dot.dataset.kind = n.kind || "note";
    if (n.cls) dot.classList.add(n.cls);
    const label = make("text", { x: n.x + 9, y: n.y + 3, class: "lbl" });
    label.textContent = n.label || n.id;
    label.dataset.p = n.id;
    entry.dot = dot;
    entry.label = label;
    view.append(dot, label);
  });
  svg.replaceChildren(view);

  CAMERA = { x: 0, y: 0, k: 1 }; SELECTED = null; DRAG = null; PANNING = null;
  SCENE = Object.assign({}, scene, { svg, view, drawn, neighbours });
  $("#gdetail").classList.remove("on");
  $("#meta").textContent = scene.meta(nodes.length, links.length);
  bindSceneOnce();
  document.body.dataset.rendered = scene.address;
}

// --- interaction ---------------------------------------------------------------------
// A picture you can only look at answers "is it connected". Being able to grab a node, follow
// its edges and read its relations is what answers "connected to WHAT, and how".

const applyCamera = () =>
  SCENE.view.setAttribute("transform", `translate(${CAMERA.x} ${CAMERA.y}) scale(${CAMERA.k})`);

function scenePoint(ev) {
  const box = SCENE.svg.getBoundingClientRect();
  return { x: (ev.clientX - box.left - CAMERA.x) / CAMERA.k,
           y: (ev.clientY - box.top - CAMERA.y) / CAMERA.k };
}

function moveNode(id) {
  const { node, dot, label, lines } = SCENE.drawn.get(id);
  dot.setAttribute("cx", node.x); dot.setAttribute("cy", node.y);
  label.setAttribute("x", node.x + 9); label.setAttribute("y", node.y + 3);
  lines.forEach(({ line, end }) => {
    line.setAttribute("x" + end, node.x);
    line.setAttribute("y" + end, node.y);
  });
}

function highlightNode(id) {
  const near = id ? SCENE.neighbours.get(id) : null;
  SCENE.drawn.forEach((entry, key) => {
    const on = !id || key === id || near.has(key);
    entry.dot.classList.toggle("faded", !on);
    entry.dot.classList.toggle("near", Boolean(id) && on && key !== id);
    entry.label.classList.toggle("faded", !on);
    entry.label.classList.toggle("show", Boolean(id) && on);
  });
  SCENE.view.querySelectorAll("line").forEach(line => {
    line.classList.toggle("faded", Boolean(id));
    line.classList.remove("hot");
  });
  if (id) SCENE.drawn.get(id).lines.forEach(({ line }) => {
    line.classList.remove("faded"); line.classList.add("hot");
  });
}

async function selectNode(id) {
  if (!SCENE.drawn.has(id)) return;
  SELECTED = id;
  SCENE.drawn.forEach((entry, key) => entry.dot.classList.toggle("sel", key === id));
  highlightNode(id);
  const panel = $("#gdetail");
  panel.innerHTML = await SCENE.detail(id);
  panel.classList.add("on");
  panel.querySelectorAll("[data-open]").forEach(button =>
    button.onclick = () => { openNote(button.dataset.open); setView("note"); });
  panel.querySelectorAll("[data-sel]").forEach(row =>
    row.onclick = () => selectNode(row.dataset.sel));
}

function clearSelection() {
  SELECTED = null;
  SCENE.drawn.forEach(entry => entry.dot.classList.remove("sel"));
  highlightNode(null);
  $("#gdetail").classList.remove("on");
}

function dragNode(id, at_) {
  const entry = SCENE.drawn.get(id);
  entry.node.x = at_.x; entry.node.y = at_.y;
  moveNode(id);
}

// Bound once, for whichever scene is showing. Bound per draw, a second graph would stack a second
// set of listeners on the same svg and every drag would move twice.
function bindSceneOnce() {
  if (bindSceneOnce.done) return;
  bindSceneOnce.done = true;
  const svg = $("#g");
  const idOf = ev => ev.target.dataset && ev.target.dataset.p;

  svg.addEventListener("pointerover", ev => {
    if (idOf(ev) && !SELECTED && !DRAG) highlightNode(idOf(ev));
  });
  svg.addEventListener("pointerout", ev => {
    if (idOf(ev) && !SELECTED && !DRAG) highlightNode(null);
  });
  svg.addEventListener("pointerdown", function gpointerdown(ev) {
    svg.setPointerCapture(ev.pointerId);
    if (idOf(ev)) { DRAG = { id: idOf(ev), moved: false }; }
    else { PANNING = { x: ev.clientX - CAMERA.x, y: ev.clientY - CAMERA.y }; svg.classList.add("panning"); }
  });
  svg.addEventListener("pointermove", ev => {
    if (DRAG) { DRAG.moved = true; dragNode(DRAG.id, scenePoint(ev)); return; }
    if (PANNING) { CAMERA.x = ev.clientX - PANNING.x; CAMERA.y = ev.clientY - PANNING.y; applyCamera(); }
  });
  svg.addEventListener("pointerup", ev => {
    if (DRAG && !DRAG.moved) selectNode(DRAG.id);
    else if (PANNING && ev.target === svg) clearSelection();
    DRAG = null; PANNING = null; svg.classList.remove("panning");
  });
  svg.addEventListener("dblclick", ev => { if (idOf(ev)) SCENE.open(idOf(ev)); });
  svg.addEventListener("wheel", ev => {
    ev.preventDefault();
    const box = svg.getBoundingClientRect();
    const cx = ev.clientX - box.left, cy = ev.clientY - box.top;
    const next = Math.min(8, Math.max(0.15, CAMERA.k * Math.exp(-ev.deltaY * 0.0022)));
    const ratio = next / CAMERA.k;
    CAMERA.x = cx - (cx - CAMERA.x) * ratio;
    CAMERA.y = cy - (cy - CAMERA.y) * ratio;
    CAMERA.k = next;
    applyCamera();
  }, { passive: false });
}

// --- the two scenes ------------------------------------------------------------------

async function drawGraph() {
  SCENE_KIND = "notes";
  const data = await api("/api/graph", { limit: 400 });
  // /api/graph sends `nodes` as plain path STRINGS and the titles in a map beside them. Spreading
  // a string gives {0:"R",1:"E",...} with no .path, which silently drops every edge - the lookup
  // misses on both ends and the lines never get built.
  const titles = data.titles || {};
  drawScene({
    address: "graph",
    nodes: data.nodes.map(path => ({ id: path, label: titles[path] || path, kind: "note" })),
    links: data.edges,
    meta: (shown, linked) => `${shown} of ${data.total} notes · ${linked} links · ` +
                             `drag a node, click it for detail, double-click to open`,
    detail: async path => {
      const note = await api("/api/node", { path });
      const rows = (note.relations || []).map(r =>
        `<div class="rel" data-sel="${esc(r.path)}">` +
        `<span class="t">${esc(r.rel_type || "relates-to")} ${r.direction === "in" ? "&larr;" : "&rarr;"}</span> ` +
        `${esc(r.path)}</div>`).join("") || `<div class="dim">no relations</div>`;
      return `<h3>${esc(note.title || path)}</h3>` +
        `<div class="dim" style="font-size:11px">${esc(path)}</div>` +
        `<p><button data-open="${esc(path)}">Open note</button></p>` + rows;
    },
    open: path => { openNote(path); setView("note"); },
  });
}

// The tag tree, drawn: a node per tag, sized by how many notes sit under it, a line from each
// parent to its child. Rooted at one node (`#tags+<tag>`) it also hangs that subtree's notes off
// the tags they carry. The whole tree never carries notes - that is the notes graph again, and a
// vault's worth of leaves is what the layout cannot afford.
async function drawTagGraph(root) {
  SCENE_KIND = "tags:" + root;
  const data = await api("/api/tag-graph", root ? { root, notes: 1, limit: 400 } : { limit: 400 });
  const byId = Object.fromEntries(data.nodes.map(n => [n.id, n]));
  const tagCount = data.nodes.filter(n => n.kind === "tag").length;
  drawScene({
    address: root ? "tags+" + root : "tags",
    nodes: data.nodes.map(n => n.kind === "tag"
      ? { id: n.id, label: `${n.label} (${n.notes})`, kind: "tag",
          r: 4 + Math.min(14, Math.sqrt(n.notes)) }
      : { id: n.id, label: n.label, kind: "note", r: 3, cls: "leaf" }),
    links: data.edges,
    meta: shown => `${tagCount} of ${data.total} tags` +
                   (root ? ` under ${root} · ${shown - tagCount} notes` : "") +
                   (data.truncated ? " · cut at the limit" : "") +
                   ` · click a tag for detail, double-click to open its subtree`,
    detail: async id => {
      const n = byId[id];
      if (n.kind === "note")
        return `<h3>${esc(n.label)}</h3><div class="dim" style="font-size:11px">${esc(id)}</div>` +
               `<p><button data-open="${esc(id)}">Open note</button></p>`;
      return `<h3>${esc(id)}</h3>` + (n.meaning ? `<p>${esc(n.meaning)}</p>` : "") +
        `<p class="dim">${n.notes} note${n.notes === 1 ? "" : "s"} under it · ` +
        `${n.direct} carrying it directly</p>` +
        `<p><a href="${tagHash(id)}">List its notes</a> · ` +
        `<a href="#tags+${encodeURIComponent(id)}">Expand its notes here</a></p>` +
        (n.parent ? `<div class="rel" data-sel="${esc(n.parent)}"><span class="t">parent &larr;</span> ` +
                    `${esc(n.parent)}</div>` : "");
    },
    open: id => {
      if (byId[id].kind === "note") { openNote(id); setView("note"); }
      else location.hash = "tags+" + id;
    },
  });
}

boot();
</script>
"""


# --- cli ---------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="the wiki UI — read, search and edit the vault")
    parser.add_argument("--vault", default=".", help="vault root (default: current directory)")
    parser.add_argument("--port", type=int, default=None,
                        help="port on 127.0.0.1 (default: the vault's dashboard_port, else a "
                             "port derived from the vault's path so two vaults never collide; "
                             "0 picks a free one)")
    parser.add_argument("--index", default="index.md",
                        help="the routing map to read the Business Glossary from "
                             "(default: index.md)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="address to bind (default: 127.0.0.1, this machine only). "
                             "`lan` binds this machine's network address so a phone can reach "
                             "it; anything but loopback requires a code, printed at startup")
    parser.add_argument("--open", action="store_true", help="open a browser at it")
    parser.add_argument("--read-only", action="store_true",
                        help="refuse every write, whatever the page sends")
    parser.add_argument("--no-fetch", action="store_true",
                        help="never download the renderer bundles; serve without them if absent")
    parser.add_argument("--no-reindex", action="store_true",
                        help="do not rescan the vault after an edit")
    parser.add_argument("--fetch-assets", action="store_true",
                        help="download and pin the renderer bundles, then exit")
    parser.add_argument("--force", action="store_true", help="with --fetch-assets, re-download")
    parser.add_argument("--cache-dir", default="",
                        help="where machinery for a non-vault folder is kept "
                             "(default: the OS cache directory)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    vault = Path(args.vault).resolve()

    # Which kind of root is this? Asked of the disk, never by opening the graph: `graph.connect()`
    # does a `mkdir(parents=True)`, so the old code turned every folder it was pointed at into half
    # a vault - creating `.wiki/graph.sqlite` inside somebody's docs tree - and only then exited
    # with "graph is empty".
    vault_mode = is_vault(vault)
    cache = None if (vault_mode and not args.cache_dir) else shared_cache(args.cache_dir)

    if args.fetch_assets:
        for line in fetch_assets(vault, force=args.force, cache=cache) or ["already cached"]:
            print(f"  {line}")
        print(f"  -> {assets_dir(vault, cache)}")
        return 0

    maybe_reexec(vault)   # from here on, `rag_toolkit` may be importable

    if vault_mode:
        conn = graph.connect(vault)
        empty = not graph.require_scan(conn)
        conn.close()
        if empty:
            print("graph is empty — run `graph.py scan --full` first", file=sys.stderr)
            return 2
        corpus = VaultCorpus(vault)
    else:
        corpus = FolderCorpus(vault)
        found = corpus.tree()
        if not found["notes"] and not found["diagrams"]:
            print(f"no markdown or .mmd files under {vault}", file=sys.stderr)
            return 2

    missing = [name for name in ASSETS if not (assets_dir(vault, cache) / name).exists()]
    if missing and not args.no_fetch:
        print(f"{vault.name}: caching the renderer bundles, once")
        try:
            for line in fetch_assets(vault, cache=cache):
                print(f"  {line}")
        except Exception as exc:
            print(f"  could not fetch ({type(exc).__name__}) — notes will render without "
                  f"diagrams until `serve.py --fetch-assets` succeeds", file=sys.stderr)
    elif missing:
        print(f"  {', '.join(missing)} not cached — run `serve.py --fetch-assets`",
              file=sys.stderr)

    from http.server import ThreadingHTTPServer
    token = secrets.token_hex(24)
    search = Search(vault)
    # Only a vault has scanners to re-run. A folder's index is in memory and is dropped on write.
    reindexer = Reindexer(vault, enabled=vault_mode and not args.no_reindex)
    host = resolve_host(args.host)
    handler = make_handler(vault, token, search, reindexer, args.read_only, corpus, cache,
                           args.index)

    # An explicit --port always wins; otherwise the vault's own committed setting does, which is
    # what references/ui.md has always said happens.
    port = args.port if args.port is not None else configured_port(vault, default_port(vault))
    try:
        server = ThreadingHTTPServer((host, port), handler)
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            raise
        # Never fall through to a different port: the URL has to be the one this vault always uses,
        # and a server that quietly moves is how you end up reading the wrong vault.
        print(f"port {port} is already in use — something else is serving it. "
              f"Free it, or pass --port, or set dashboard_port in .wiki/wiki-config.json.",
              file=sys.stderr)
        return 1
    shown = lan_address() if host in ("0.0.0.0", "::") else host
    url = f"http://{shown}:{server.server_address[1]}"
    counts = corpus.stats()
    print(f"{vault.name} {'wiki' if vault_mode else 'folder'}: {url}")
    print(f"  {counts['notes']} notes, {counts.get('diagrams', 0)} diagrams"
          + ("" if vault_mode else f" · no vault here, so no semantic index"
                                   f" · machinery in {assets_dir(vault, cache).parent}"))
    if host not in LOOPBACK:
        # No gate stands in front of a network bind: anyone who can reach the address is in.
        print(f"  on your phone: open {url}")
        print(f"reachable from your network on {host}. Anyone who can reach {url} can read and "
              f"edit this vault. Ctrl-C to stop.")
    else:
        print("bound to localhost. " + ("read-only. " if args.read_only
                                        else "editing is locked until you open the lock. ")
              + "Ctrl-C to stop.")
    sys.stdout.flush()
    if args.open:
        import webbrowser
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
