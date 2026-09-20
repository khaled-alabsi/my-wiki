# The wiki UI — `scripts/serve.py`

**The UI is for the person; the MCP server is for a remote agent.** They are two surfaces on one vault and neither substitutes for the other: a page is opened and read, a tool is called and its result parsed. Never answer a question by scraping this page, and never expose a UI route as an agent's door — `references/mcp.md` is that door.

The page a person opens to read their own vault: notes rendered, diagrams drawn, search that
finds the note they phrased differently, the graph, and — behind a lock — editing.

```bash
python3 scripts/serve.py --vault <vault> --open
```

**For the user, never for the agent.** The agent's doors are `graph.py query --json` and
`.rag/bin/rag`. Never open this page, never parse it, never scrape it for an answer. Mention it
when someone asks to see, browse or edit their vault; then leave it alone.

## What the UI can do — the list to answer from

**Read this section to answer "what can the wiki UI do".** It is the inventory, kept current with
the code; nobody should have to read `serve.py` to tell somebody what the page offers.

| Feature | What it does | Flag / how to reach it |
|---|---|---|
| Read notes | Renders markdown, mermaid fences and standalone `.mmd` files | click a note |
| Syntax highlighting | Fenced code in a note is coloured; mermaid fences are left to mermaid | automatic |
| Mathematics | `$…$` and `$$…$$` TeX render, offline, via MathJax's SVG build (no font files) | automatic |
| Directory tree | The sidebar nests one row per path segment, each folder collapsible on its own. It holds **every** file the folder has — notes, code and standalone diagrams — never a flat list per file type | sidebar |
| Loading state | The sidebar says it is reading the vault before the data lands, and names a failure | automatic |
| Search placement | The box sits in the top bar; results open in a panel directly beneath it, with a spinner while it runs. `x` or Escape clears | top bar |
| Tree labels | A row is labelled by its **filename**; the note's heading rides beside it only when it adds something | sidebar |
| Hidden folders | Folders listed in `wiki-config.json` → `hidden_folders` are not listed; `/api/note` still serves them | edit the config |
| Source files | A `.py`, `.sql`, `.yaml` … in the vault opens, fenced in its language | in the tree, marked `</>` |
| CSV as a table | A `.csv`/`.tsv` renders as a real table, capped at 500 rows and saying how many it did not draw | click the file |
| Filename autocomplete | The search box offers every filename in the vault as you type | the search box |
| Short search status | One line: hits and coverage. Backend and any repair hint move to its tooltip | hover the line |
| Images in notes | `![](shot.png)` displays; src resolved against the note, missing ones named | automatic |
| Frontmatter strip | Shows YAML keys as chips instead of prose | automatic |
| Tag chips | A note's tags as chips on their own row, each opening that tag's listing | automatic, under the strip |
| Tag editing | Remove a chip, or add a tag picked from the vault's tree or typed new; saved with the note, previous version to the trash first | open the lock, then **Save** |
| Diagram full screen | Expand, drag to pan, wheel/pinch to zoom, `Fit`, `Esc` | **Expand** on any diagram |
| Diagram export | SVG, PNG (2x), `.mmd` source, PDF via print | in the full-screen bar |
| Search | `.rag` semantic, else **names and prose together** — always says which answered and why | the search box |
| Body-text search in a vault | Finds a word inside a note, not only in its title | automatic |
| Coverage line | "read all 54 notes" / "read only 3 of 37" — what the answer could actually see | under the search box |
| Match provenance | Each hit says *in the name*, *in the text* or *glossary* | on every hit |
| Every match per note | Up to 3 matching lines per note, each with its heading chain and line | on every card |
| Honest totals | `k` is a page size; the real total is shown with **Show more** | under the results |
| Search filters | Path glob and extension, both self-completing from the vault | the two boxes under search |
| Tag filter | Keeps only hits under a tag node and everything below it, and says how many it removed; with no words it lists the tag's notes | the tag box in the sidebar |
| Hit → sentence | Opens the note at the matching line, marks the block | click a hit; `#<path>:<line>` |
| Graph | Force layout; hover to highlight, drag, click for typed relations, double-click to open | **Graph** tab |
| Tags panel | The vault's tag tree, collapsible, each node with the notes under it; nodes the inventory does not list shown in italics | sidebar → Tags |
| Tag listing | A tag's meaning, its children, and every note under it | click a tag, or `#+<tag>` |
| Tag graph | The tag tree drawn: a node per tag sized by its notes, a line from parent to child; one subtree can be opened with its notes as leaves | **Tags** tab, `#tags`, `#tags+<tag>` |
| Glossary panel | Every term the index defines, plus terms the notes use but never define | sidebar → Glossary |
| Term decoration | First mention per block underlined, definition on hover | automatic in prose |
| Term card | Definition, aliases, status, source note, mentions | click a term, or `#!<term>` |
| Time travel | Whole page as of a date: tree, counts, graph, search; hidden counts reported | date box in the toolbar |
| Supersede banner | Names the note that replaced this one | automatic, in every mode |
| Edit in place | The block under the caret shows markdown, the rest stays rendered; diagrams redraw | open the lock, click a block |
| Source mode | The whole raw file in one textarea | **Source** |
| Undo | Steps back through block commits, capped at 100 | `Cmd-Z` |
| Version history | Earlier saved versions of the open note, with a diff and Restore | **History** |
| Collapsible sidebar | Hides the sidebar; a drawer on narrow screens | **☰** |
| Mobile layout | One column under 760px, sticky toolbar, larger targets, safe-area insets | automatic |
| Installable | Manifest, service worker, generated icons — adds to the home screen | browser's Install / Add to Home Screen |
| Phone access | Binds every interface and prints the LAN address plus a 6-digit code | `--host lan` |
| No code | Serves a network bind with no challenge at all | `--no-code` |
| Read-only | Refuses every write | `--read-only` |
| Trash | Every save keeps the previous bytes, last 20 per note | automatic |

## What it serves

| Route | Answers |
|---|---|
| `GET /` | the page: one inline HTML constant, no build step, no CDN |
| `GET /assets/<name>.js` | the two cached renderer bundles, same-origin |
| `GET /api/tree` | every note and folder, plus the vault's standalone `.mmd` files |
| `GET /api/note?path=` | one note's raw markdown, relations, backlinks, concepts — or a `.mmd` file |
| `GET /api/search?q=&k=&path=&ext=&tag=` | semantic hits through `.rag`, or SQLite when there is none |
| `GET /manifest.webmanifest` `/sw.js` `/icon-192.png` `/icon-512.png` | what makes it installable |
| `GET /pin?code=` | only when bound off loopback: the code that admits a client |
| `GET /media?path=` | one image from the vault, by a path that is a KEY in the media allowlist |
| `GET /api/glossary` | the vault's own vocabulary: what the index defines, and what the scanner merely saw |
| `GET /api/tags` | the tag tree with counts: `nodes` the inventory lists, and apart from them `unlisted` ones only the notes carry |
| `GET /api/tag-graph?root=&notes=&limit=` | the tag tree as nodes and edges, optionally one subtree, optionally with its notes as leaves |
| `GET /api/history?path=` | the versions of one note sitting in the trash, newest first |
| `GET /api/version?path=&at=` | one of those versions, by its stamp |
| `GET /api/stats` `/api/graph` `/api/node` `/api/concepts` `/api/query` | `graph.py`'s payloads, unchanged |
| `PUT /api/note` | the only write |

`as_of=<date>` is accepted by `/api/tree`, `/api/stats`, `/api/note`, `/api/node`, `/api/search`
and `/api/graph` — every route that describes what the vault holds. Half a page time-travelling
is worse than none of it.

`/api/query` and the graph payloads are `graph.py`'s own functions, imported. One implementation,
two front doors — the CLI the agent uses and the page a person opens.

## A vault, or any folder at all

The server serves two kinds of root, decided by `is_vault()` — **on disk, never by asking the
graph**. `graph.connect()` does a `mkdir(parents=True)`, so probing a folder with it *makes* it one:
that is how pointing this server at somebody's docs tree used to leave a `.wiki/graph.sqlite`
behind and only then exit with "graph is empty".

| | vault | plain folder |
|---|---|---|
| detected by | `.wiki/manifest.json` or `.wiki/graph.sqlite` exists | neither does |
| index | the notes table and the relation graph | `scan_vault.walk()` held in memory, TTL 4s, dropped on write |
| search | `.rag`, falling back to SQLite titles | literal substring over the files, quoting the matching line |
| backend reported | `rag` / `sqlite` | `text` |
| bundles | `<vault>/.wiki/ui-assets/` — portable, travels with the vault | the shared OS cache |
| trash | `<vault>/.wiki/.trash/` | the shared cache, keyed by the folder |
| tags | `graph.py`'s tag tables plus the inventory `.wiki/tags.md`; a save lists a new tag there | the tree built from what the notes carry, every node `unlisted`; nothing listed anywhere |
| written into the root | the vault's own machinery | **nothing, ever** — only the notes you edit |

`FolderCorpus` reuses `scan_vault.walk()`, which already returns each file's title, outbound links
**with their relation types**, and frontmatter keys, and already skips `node_modules`, `dist`,
`build`, `target`, `venv` and `.git`. So a docs tree gets a real tree and a real link graph without
this server writing a byte or growing a second parser.

**The shared cache** is `~/Library/Caches/wiki-ui/` on macOS, `$XDG_CACHE_HOME/wiki-ui/` elsewhere,
overridable with `--cache-dir`. One location per machine: the 2.7 MB of bundles is fetched once
ever rather than once per folder, and the folder the user pointed at stays exactly as they left it.
Trash goes under `trash/<folder-name>-<hash of the absolute path>/` so two folders called `docs`
never collide.

**Only edges between files that exist are counted.** `build_graph` records every outbound link,
and documentation prose is full of `[example](path.md)` references to files that do not exist —
counting those makes the footer claim links the graph refuses to draw.

What a folder does not get: semantic search, a glossary, typed-relation queries, `as-of` history.
The footer says `plain folder, no index` and the search line says `literal text match`, so nothing
has to be guessed.

## Code — coloured in a note, and openable on its own

**The theme is inlined in the page, not linked.** `style-src` is `'unsafe-inline'` and does **not**
include `'self'`, so a `<link>` to a stylesheet in `/assets/` would be blocked outright. The theme
is written against the page's own tokens, so it follows light and dark with no second palette to
keep in step.

`highlightCode()` runs after `mermaid.run` and **skips `language-mermaid`** — those fences have
already been replaced by a drawing, and highlighting them would be colouring the source of a
picture nobody is looking at. A block is marked once (`data-hl`) so a re-render after an edit does
not highlight it twice. **No highlighter is not a broken page**: the code still reads, in the same
degradation the diagram bundle already has.

**A source file is not a note.** `find_sources()` is the allowlist — the same discipline as
`find_diagrams()` and `find_media()` — mapping extension to the language highlight.js knows it by.
`read_source()` fences the file in that language, so the page renders it through the code path it
already had, and `kind` is `source`. They get their own sidebar section, are excluded from the
notes list, and **are scanned by search**, so a word inside a `.py` in the vault is findable.
Capped at 2 MB; working folders are excluded.

## Images a note points at

Nothing served images at all: `![](shot.png)` rendered an `<img>` pointing at `/shot.png`, which
fell through every route to the 404 branch. Every screenshot in every vault was a broken icon —
and a screenshot pasted into a note is most of what a vault actually accumulates.

`find_media()` is the allowlist, built exactly like `find_diagrams()`: a requested path is a **key**
in it and never a string handed to `open()`. Cached 5 s, because an `rglob` per `<img>` scales with
the vault and one note can hold a dozen.

- **The page resolves an `<img src>` against the NOTE**, with the same `resolve()` the links use,
  then rewrites it to `/media?path=…`. A browser would otherwise resolve it against the page root.
- **A working-folder image is not served.** For a note, a leading `_` or `.` on a folder hides it
  from the sidebar and `/api/note` still serves it. For media that has to hide it from **access**
  too: an `<img>` is a fetch, so otherwise it is a way to read a file the vault does not show.
- **Raster only.** An SVG is a document that can carry script and it would come from this origin;
  `.mmd` already covers drawings. Admitting SVG is a deliberate decision with a CSP consequence.
- **25 MB cap**, and a missing image is replaced by the path that did not resolve — a broken image
  icon tells the reader nothing about which link is wrong.
- `img-src 'self' data:` already allowed this; only the route was missing.

## Two kinds of diagram, one rendering path

A ```mermaid fence inside a note and a standalone `.mmd` file are both diagrams somebody drew, and
a UI that renders one while hiding the other is showing half the vault.

`.mmd` files are **not notes**: `scan_vault.py` never sees them, they carry no links and they have
no index entry. So they are listed separately (`tree.diagrams`, its own sidebar section) and
`/api/note` wraps the file's body in a fence before returning it — the page then renders it with
exactly the same code that handles a fence inside a note. `kind` says which one you got.

`find_diagrams()` is the allowlist: a requested `.mmd` path must be a **key** in it, the same
discipline the notes table provides for prose. It is cached for 5 seconds, because an `rglob` per
request scales with the vault.

## The four rules

They are not negotiable, because this opens a port on a machine holding somebody's private notes.

1. **127.0.0.1 by default, and anything else is opt-in, explicit, and gated by a code.**
   `--host lan` (or an address) is how the vault reaches a phone; it is never the default, it is
   never inferred, and the moment the bind is not loopback a 6-digit code stands in front of every
   request. **This rule used to read "127.0.0.1 only, never `0.0.0.0`"** — it was changed on
   request, deliberately, because reading your own notes on your own phone is a real thing to want
   and the old rule made it impossible. What has not changed is that widening the bind is a
   decision the operator makes in the command line, with the consequence printed back at them.
2. **`PUT /api/note` is the only write.** No POST, no DELETE, no rename, no move. Restructuring
   stays behind `refactor`'s approval gate, where a human accepts a plan first.
3. **No parameter is ever passed to `open()`.** A `path` is looked up in the notes table and used
   as a **key**. A server that reads whatever path it is handed is a file-disclosure hole, and
   "it's bound to localhost" is not a defence against a browser tab.
4. **A write proves it came from this server's own page, or it does not happen.**

## Reaching it from a phone, and the code that guards it

`--host lan` resolves this machine's network address and binds it; `--host <address>` takes one as
given; `--host 0.0.0.0` binds everything. Anything but loopback flips `PinGate.required`.

**Why a code, and not just the bind.** On loopback, the write token in the page is safe because
only processes on this machine can fetch the page that carries it. On a network that stops being
true: anyone who can reach the port can load the page, read the token out of it, and write to the
vault. The code replaces the trust the loopback bind was providing.

- **It gates everything, and the vault page is never the thing an unauthenticated client is
  handed** — that page carries the token. They get the code form instead; the API gets `403`.
- **No exemption for a loopback peer.** One rule applied to every request is a rule the suite can
  exercise. An exemption nothing tests is an exemption nobody should rely on.
- **The code is printed once, at startup, in the terminal that started it** — six digits,
  `secrets.randbelow`, new every run. Compared with `compare_digest`.
- **Guessing is rate-limited**: 8 wrong codes from one address and it waits 60 seconds.
- Success sets `wiki_pin`, `SameSite=Strict`, for a week. `GET /pin?code=` rather than a POST, so
  rule 2 below is still literally true.
- **The startup line says what it has done**: the address, and that anyone who reaches it with the
  code can read and edit the vault. A widened bind the operator is not told about is the failure
  this reporting prevents.

**What this is not.** It is not authentication for an untrusted network, there is no TLS, and the
code travels in the clear. It is the difference between "anyone on this wifi" and "whoever I read
the code to". For anything stronger, put it behind a tunnel — the bind stays where you point it.

## Installable, so it behaves like an app

`/manifest.webmanifest`, `/sw.js`, and `/icon-192.png` `/icon-512.png` are what a browser reads
before it will offer "Add to Home Screen". The icons are **generated**, not shipped: `app_icon()`
draws a rounded square from arithmetic and `_png()` encodes it with `zlib` and `struct`, because
two squares are not worth an imaging dependency in a server that has never had one. A size that is
not in `ICON_SIZES` is a `404` — the number in the URL is a **key**, never an argument to a
generator that would happily render a 20000px square.

`id` and `name` both carry the vault name, so two vaults on two ports install as two apps rather
than fighting over one home-screen icon.

**The service worker caches the two pinned bundles and refuses to touch anything else.** The page
and every API answer stay `no-store` for the reason they always were — this server restarts often,
sometimes against a different vault on the same port — and a worker that cached them would make
that mix-up survive the restart instead of ending with it.

**The CSP had to name them.** `default-src 'none'` blocks a manifest and a worker outright, so
`manifest-src 'self'` and `worker-src 'self'` are now in it. Nothing remote became allowed.

Registration only runs in a secure context, which is `localhost` and `https`. Over plain http to a
LAN address the browser will not install it and the page works exactly as before — so the install
prompt appears on the machine running it, and on a phone only through a tunnel that terminates in
one of those two.

## Why a write needs proving

Any page you have open can `fetch` `http://127.0.0.1:8899`. None of them can *read* this page, so
the token it carries is what separates the two. Three gates, in order, in `_write_gate()`:

| Gate | Refusal |
|---|---|
| `--read-only` was passed | `405` |
| `X-Wiki-Token` missing or wrong | `403` |
| `Sec-Fetch-Site` is not `same-origin` / `none` | `403` |
| `Content-Type` is not `application/json` | `415` — this is what blocks a plain form post |

Then the path itself, in `validate_write_path()`: relative, no `..`, ends `.md`, no segment that
is `.git` `.rag` `.wiki` `.agents` `.input` `.obsidian` `node_modules` or begins with a dot, and
the resolved path must still be inside the vault. Anything else is `403`.

**The lock is a different thing and is not security.** The page starts with editing locked, so a
tab left open is not one keystroke from changing a note. The server re-checks all four gates on
every write regardless of what the page believes.

## No edit destroys anything

Before new bytes land, the current ones are copied to
`.wiki/.trash/<UTC timestamp>/<path>` — the same trash `reset_vault.py` uses.

**Growth class: queue.** Bounded by versions per note, not by how long the vault has existed:
the last **20** versions of each note are kept and older ones are deleted. The enforcement point
is `backup_note()`, at the moment it writes a backup — pruning one note never touches another's
history.

After a write, a debounced background thread (2 s of quiet) re-runs `scan_vault.py`,
`graph.py scan --since-manifest` and `.rag/bin/rag update --quiet`. Derived state drifting behind
an editor is how a vault starts answering with yesterday's content. `--no-reindex` turns it off.

## A vault searches names AND prose

`Search.run()` used to send a plain **folder** to `literal()`, which reads file contents, and a
**vault** to `graph.serve_search()`, which matches `path LIKE`, `title LIKE` and a glossary term
and never opens a note. So the corpus with the database, the graph and the glossary had strictly
worse text search than a directory somebody pointed at by accident, and every vault whose `.rag`
was broken had been answering from titles alone without saying so.

`titles_and_bodies()` merges the two: **names first**, because someone typing three letters is
usually reaching for a note they know exists, then **prose**, which is the half that was missing.
`backend` is `text`, and each hit carries `matched_by` — `title`, `text` or `concept` — because
one label can no longer describe a merged answer.

**Coverage is reported, not just the backend.** `coverage: {searchable, total}` says how many notes
the answer actually looked inside. "sqlite · 0 hits" read like an answer when it meant "I never
opened a note"; a reader cannot tell *found nothing* from *never looked* unless the response says.

**Every occurrence, not the first.** `literal()` returns up to `MATCHES_PER_FILE` (3) hits per note,
each with its line and the **heading chain** it sits under, tracked while scanning. Matches past the
cap are still **counted** — `total` is the true number, so `k` is a page size and never a claim
about how much exists. The page groups the hits into one card per note and offers **Show more**.

## Search: which backend answered is always reported

If `<vault>/.rag` exists, the server imports `rag_toolkit.api.Index` and holds it open for the
life of the process. That is the reason for the re-exec below: shelling out to `.rag/bin/rag` per
keystroke would reload the embedding model **and** the reranker on every query.

No `.rag`, or an import that fails → SQLite title/path/concept matching, and the response says
`"backend": "sqlite"`. The page prints it too. A grep-shaped answer that looks like a semantic one
is exactly the failure this reporting exists to prevent.

Filters `path` (glob) and `ext` are pushed into the RAG query, and applied with `fnmatch` on the
SQLite path.

## The re-exec

If `<vault>/.rag/.venv/bin/python` exists, `serve.py` re-launches itself under it with
`PYTHONPATH=<vault>/.rag/toolkit`, once, guarded by `WIKI_SERVE_REEXEC`. Nothing else changes —
the server is stdlib either way, and a vault with no RAG workspace simply runs under whatever
`python3` started it.

## The two bundles

Markdown and mermaid render **in the browser**. Mermaid is a JavaScript library with no Python
equivalent, and the browser is already a JavaScript engine — so nothing here needs Node, at
install time or run time. Node would only be required to pre-render diagrams to SVG headlessly,
which is a heavier way to get the same picture.

| File | Pin |
|---|---|
| `mermaid.min.js` | `mermaid@11.12.0` — sets `globalThis.mermaid`; needs no CSP `unsafe-eval` |
| `marked.min.js` | `marked@15.0.6` |
| `highlight.min.js` | `@highlightjs/cdn-assets@11.11.1` — 127 KB against mermaid's 2.7 MB |

**Growth class: derived.** They live in `.wiki/ui-assets/`, are git-ignored, and are re-fetchable
by deleting the folder. `asset-pins.json` beside them records the SHA-256 actually in use; a
cached file whose bytes no longer match its pin is refused rather than served.

`serve.py --fetch-assets` downloads and pins them and exits — the only network call this server
makes, and `init` makes it at scaffold time. On a normal start, missing bundles are fetched once
unless `--no-fetch`; if the fetch fails the server still runs and notes render without diagrams.

The page's CSP is `default-src 'none'; script-src 'self' 'unsafe-inline'; style-src
'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'`. `'self'` is those two
files. Nothing remote, ever — a page that reaches a CDN is a page that stops working on a plane.

## The glossary is served from one place, and guesses are kept apart from it

`index.md` → `## Business Glossary` is the only source of a definition. The `concepts` table is a
different thing: terms the scanner **saw**. `/api/glossary` returns both and never merges them —
`terms` are the owner's definitions, `candidates` are machine finds with no glossary line yet.
Merging them would put words the vault never defined into the vault's own glossary, which is the
one thing `references/glossary.md` forbids.

**Access class: sliced.** `read_glossary()` seeks the heading and stops at the next `##`. The index
is a budgeted routing map whose other sections are a folder listing this has no use for, and
reading a whole index to find fifty lines is how a routing map becomes a context bill.
**Growth class: derived** — in memory, TTL 5 s, rebuilt from the file.

A term is not a note. `#!<term>` opens a **card**, not a file: no edit control, no history, no
lock — the same discipline `openable: false` already applies to a concept in the search results.

**A known term is marked where it appears in prose.** After the diagrams have drawn, a tree walker
wraps the **first mention per term per block** in a dotted underline carrying the definition.
Every mention would carpet a note that says `PIP` forty times; the first one per block is where a
reader actually needs the reminder. It never enters `pre`, `code`, `a`, `textarea`, the frontmatter
strip or a drawn diagram — those are not prose. An **acronym matches case-sensitively**: `sca` in a
sentence is a word, `SCA` is the term.

## Tags: one writer, and the inventory is enriched by the same save

A tag is a full path in the vault's tag tree, and `references/tagging.md` owns the rules. What the
page adds is a way to walk the tree and a way for the owner to change a note's tags.

- **`/api/tags` keeps what the inventory lists apart from what the notes merely carry**, the way
  the glossary keeps definitions apart from candidates. An unlisted node has no meaning line and
  nobody decided it belongs in the tree; hiding it would hide exactly the drift `tags.py check`
  reports.
- **A tag filter is applied to the hits, never inside a backend.** `.rag` cannot filter by tag, so
  the search over-fetches to `SEARCH_LIMIT`, the filter runs against a set this server built, and
  the answer carries `tag_hidden`, separate from the date's `hidden`. **The tag is a key**: it is
  matched against tag paths and never reaches `open()` (rule 3).
- **A tag edit is not a second write route.** `PUT /api/note` takes `{path, markdown, tags?}`. When
  `tags` is present the server validates every tag first, 400 on a malformed one **before the
  backup**, and then the one frontmatter writer, `tags.with_tags`, puts the line in. The page never
  rewrites frontmatter itself: a second writer in JavaScript would be testable only in the opt-in
  browser run. Rule 2 stands.
- **Every save lists new tags in the inventory**, chip edit or Source mode alike: after the write
  the server reads the saved note's tags and calls `tags.add_node` for each one the inventory
  lacks, parents first, with no meaning line. The response names them in `inventory_added`. The
  inventory's path is a constant of the vault; nothing from the request reaches it. **A plain
  folder gets no inventory**, because that would turn somebody's folder into half a vault.
- **The page sends `tags` only when a chip was edited.** Sent on every save, it would overwrite a
  tag the author just typed into the frontmatter in Source mode.
- **The server never drops a node.** Removing a tag's last carrier leaves a node nothing carries,
  which `tags.py check` fails as `unused` until `audit` reports it and a `tag` run or the owner
  drops it. A node listed from the page has no meaning line until one of those fills it in.
- **Both graphs are one drawing.** `drawScene(scene)` lays out and draws whatever it is handed, and
  the svg's listeners are bound once and read the current scene. `drawGraph` and `drawTagGraph`
  only build scenes. A second copy of the force loop is how one graph stops getting the other's
  fixes. The whole tag tree never carries notes; one subtree does, because a vault's worth of
  leaves is what the O(n²) layout cannot afford. `limit` bounds tag nodes and leaves alike.
- **Addresses:** `#+<tag>` is a tag's listing (`+` cannot appear in a tag, and a note path ends in
  an extension a tag cannot contain), `#tags` the tag graph, `#tags+<tag>` one subtree with its
  notes. Each sets `data-rendered`, which is what the browser checks wait on.

## Time — reading the vault as it stood on a date

The store has carried `valid_from` / `valid_until` on notes and edges since the graph existed, and
`graph.in_window()` has always been able to answer with them. Nothing could ask.

A date in the toolbar puts the **whole page** in that day: the tree, the counts, the graph and the
search all filter through the same helper, and `AS_OF` rides on every request the page makes. A
page where only some panes time-travelled would mislead worse than one that cannot.

- **Hiding is always counted.** `/api/tree` returns `hidden`, and the footer says how many notes it
  is not showing. A tree that quietly shortens is a tree that lies about what the vault holds.
- **Search filters the hits, not the backend.** `.rag` cannot filter by date, so the route drops
  the hits that were not valid and reports `hidden` — the same "say why" rule the backends follow.
  A concept hit carries a term where a path goes and is never dated.
- **`superseded-by` gets a banner in EVERY mode**, not only while time-travelling. "This was
  replaced" is the thing a reader most needs before acting on a note, and the successor is named by
  its **title** — a reader recognises `MiFID II`, not a path.
- `~<date>` in the hash is the address for it: `#reg/psd2.md~2024-06-01`, or `#~2024-06-01` for the
  tree alone. `~` is legal in a fragment and was unused; `:` already means a line and `@` a diagram.

## Editing happens in the rendered note

A vault whose notes are half mermaid is edited blind in a raw textarea. So the document stays
drawn, and the block you put the caret in shows its markdown — Obsidian's model, for Obsidian's
reason. Leaving a block re-renders it, so an edited fence redraws the moment you click away.

**A textarea per open block, never `contenteditable` over the note.** The browser's own undo,
selection and IME keep working inside a textarea, and no keystroke can produce HTML that then has
to be turned back into markdown. That conversion is where a live editor loses somebody's content.

- **Every block carries the source it was made from.** `blocksWithLines()` stamps `data-src` beside
  the `data-line` it already stamped, so a block is handed back as markdown without re-parsing the
  file. `docSource()` reassembles the document from those, in order.
- **The stored source is what the author typed.** The `[[wikilink]]` rewrite is display only and is
  applied per block on the way to HTML — a block whose stored source had been rewritten would save
  back `[x](x.md)` where the author wrote `[[x]]`, which is a silent edit.
- **The frontmatter is put back on save.** It is stripped for rendering and kept verbatim; an
  editor that drops a note's frontmatter is data loss, not a display bug.
- **Undo is explicit.** One entry per block commit. **Growth class: budgeted** — `UNDO_MAX` 100
  states, in memory, oldest evicted in `pushUndo()`, which is the enforcement point. An afternoon
  of editing holds 100 strings, not one per keystroke.
- **`Source` is the escape hatch**, and it is the old whole-file textarea unchanged. If the live
  editor mishandles something, the raw file is one click away.
- Unchanged by all of it: the lock, all four write gates, `validate_write_path()`, `backup_note()`,
  the 20-version trash cap, history and diff. Still exactly one `PUT /api/note`.

## Version history, and putting one back

Every save copies the previous bytes to the trash; `/api/history` lists them newest-first with
sizes and `/api/version` reads one back. A restore is an ordinary `PUT`, so **the restore is itself
undoable** and lands in the trash like any other edit. A stamp is looked up as a **key** among the
stamps that exist — never joined onto a path, the same rule as every other parameter here.

## The page's own conventions

- **The sidebar can be put away, and on a phone it is a drawer.** `body[data-nav]` drives one
  custom property, so closing it is a layout change rather than a pile of hidden elements. A wide
  screen remembers the choice in `localStorage`; a narrow one always starts closed, opens over the
  note, closes when you open a note and when you tap beside it. 300px of a 390px screen leaves no
  room to read, which is why the drawer is not simply a narrower column.
- **The page declares a viewport.** Without it a phone renders at desktop width and zooms out,
  which is the difference between "works on mobile" and "is legible on mobile". Below 760px the
  grid drops to one column, the toolbar sticks and wraps, controls grow to 34px, and the note gets
  bottom padding so the last line is not under the keyboard. `100dvh`, not `100vh`, because mobile
  browser chrome moves. Safe-area insets are honoured for an installed app under a notch.
- **Folders in the sidebar start collapsed**, and open on click. Opening a note from search, a
  link or the address bar expands the folder holding it. A vault of any size turns an always-open
  tree into a wall of filenames.
- **Frontmatter is metadata, not prose.** `/api/note` returns `frontmatter` as ordered
  `[key, value]` pairs and `body` as the note without it; the page renders the pairs as a strip of
  chips. Handing the raw file to a markdown renderer turns the opening `---` into a horizontal
  rule and the keys into a paragraph across the top of every note. **`markdown` stays the whole
  file** — it is what the editor loads and saves back, and an editor that drops a note's
  frontmatter is data loss, not a display bug.
- **Any drawn diagram opens full screen.** A diagram is often wider than the column it sits in;
  shrinking it to fit makes it unreadable. Every rendered diagram carries an **Expand** control:
  drag to pan, wheel or pinch to zoom about the pointer, `Fit` or `0` to reframe, `Esc` to close.
  A trackpad pinch arrives as a wheel event with `ctrlKey` set, and pointer events cover mouse and
  touch alike, so two fingers down is a pinch. The overlay clones the SVG — the note underneath is
  never touched.
- **A diagram can be taken away.** The overlay exports **SVG** (the drawing, serialized from the
  live node), **PNG** (painted into a canvas at 2x so it stays sharp when pasted, on an opaque
  background), **.mmd** (the mermaid *source* — captured off the fence before `mermaid.run`
  replaces the text with a drawing, or the file's own bytes for a standalone diagram) and **PDF**,
  which is the browser's print dialog plus a print stylesheet that hides everything except the
  diagram. SVG and .mmd are not interchangeable: only the source can be edited or re-rendered.
  The PNG rasteriser uses a `data:` URL rather than a `blob:` one, because `img-src` allows
  `'self'` and `data:` and nothing else.
- **A search hit lands you on the sentence, not the file.** Every hit carries the line it matched
  (`anchor.line_start` from the retrieval layer, or the matched line from the literal backend), its
  heading chain, and why it matched — `rerank`, `hybrid`, `vector`, `text` — with the score. The
  card shows all of it and highlights the query terms in the snippet. Clicking opens the note and
  scrolls to the block containing that line, flashes it, and leaves it marked until you navigate
  away. `#<path>:<line>` is the address for that, so a citation is a link.

  The mechanism: the page renders **token by token** (`marked.lexer` then `marked.parser` per
  token), wrapping each top-level block in `<div data-line="N">` where N is the source line it
  started on. Without that a hit can only open the file. Every backend returns the same hit shape
  — a title match has no line and says so with `null` — so nothing downstream has to ask who
  answered before it can read a hit.
- **Search says why, not just which.** `sqlite` and `text` are causes, not answers: the response
  carries a `reason` — `no .rag workspace in this folder`, or `.rag is here but its toolkit will
  not import (ModuleNotFoundError)` — which used to go to a stderr no browser ever reads. A rag
  answer relays the retrieval report too (whether reranking ran, and any note the store makes
  about the query), and the literal backend reports how many files it `scanned`, so a zero there
  is trustworthy. It reads every candidate before trimming to `k`; stopping early made an empty
  result indistinguishable from an unfinished one.
- **A glossary term is not a note.** `graph.serve_search` returns concepts with the *term* in the
  path field, so clicking one used to 404. Every hit carries `openable`, and a concept renders as
  a term card that cannot be clicked into a file that does not exist.
- **A slow answer never overwrites a newer question.** `runSearch` stamps a sequence number and
  drops any response that is no longer the latest — otherwise a slow first query lands after a
  fast second one and leaves results that do not match the box.
- **A symlink out of the tree is not in the tree.** `os.walk` and `rglob` both yield symlinked
  files, and `root / rel` follows them — so one link could hand out a file from anywhere on disk.
  `inside()` resolves both ends and compares; it guards the walk, the diagram list, the note read
  and the literal scan. Tolerable in a vault somebody built; not when the root is a directory the
  user merely pointed at.
- **The filters complete themselves.** The path and type boxes are backed by `<datalist>`s the
  page fills from the vault: every ancestor folder as a `folder/*` glob, then every note and
  diagram path, and the extensions actually present. Nobody remembers a vault's folder names, and
  a typo'd glob just returns nothing with no hint why. Native completion, so there is no dropdown
  to build, and typing a value the list does not contain still works.
- **A folder starting with `.` or `_` is not listed.** Drafts, scratch, archives, tooling — a
  leading dot or underscore on a directory is the long-standing way to say "not content", so those
  notes and diagrams stay out of the sidebar, out of the filter completions, and out of the counts
  in the footer. The **filename** is not judged: `_index.md` inside a real folder is a note.

  Hiding is a **listing** decision, not an access one — `/api/note` still serves such a file when
  a link or the address bar asks for it by name. A note you can reach but cannot browse to is
  merely quiet; a note that vanishes the moment something links to it is broken. `graph.py` is
  untouched and still counts the whole store, which is what the CLI and the agent want.
- **The graph is handled, not just looked at.** A picture you can only stare at answers "is it
  connected"; grabbing a node and following its edges answers "connected to **what**, and how".
  Hover highlights a node's neighbourhood and dims the rest; **drag** moves a node and it stays
  put; **click** selects it and opens a panel listing its typed relations, each one clickable to
  walk the graph; **double-click** opens the note; drag the background to pan, wheel to zoom about
  the pointer, click empty space to deselect. Node radius scales with degree, so hubs are visible
  before anything is clicked. The whole scene lives in one `<g id="gview">` transform, so panning
  is one attribute write rather than repositioning every element.
- **The open note is in the address bar** as `#<path>`, so a reload keeps your place and a link
  can be handed to someone else.
- **`document.body.dataset.rendered`** is set to the note's path once every diagram has finished
  drawing, and cleared while a render is in flight. It is what a test — or a person on a slow
  page — watches instead of guessing when async work is done.
- **Nothing is cached except the bundles.** The page and every API answer are `no-store`: this
  server is restarted often, sometimes against a different vault on the same port, and a cached
  page is how someone ends up looking at another vault's notes and reporting a bug that is not
  there. The bundles revalidate against an ETag taken from their pin, so 2.7 MB is not re-sent
  on every load.

## Ports

`.wiki/wiki-config.json` → `dashboard_port`, read by `configured_port()` at startup. When that is
`null`, absent or unusable the port is **derived from the vault's own absolute path** by
`default_port()` (range `DEFAULT_PORT_RANGE`, 10000-19999), so two vaults never default to the same
number — a shared constant meant the second server could not bind, and every request to that port
was answered by whichever vault won the race. An explicit `--port` always wins, and a port already
in use is reported and refused rather than silently swapped for another.

`.wiki/wiki-config.json` → `hidden_folders` is a list of folders the sidebar must not list, read by
`hidden_folders()` and applied by `is_hidden()` on whole path segments — so `archive` hides
`archive/` and `archive/2024/` but never `archived-later/`. Hiding is a **listing** decision only:
`/api/note` still serves a hidden note, because a note that vanishes the moment something links to
it is broken rather than tidy. Absent or empty means nothing is hidden, which is the default. This file claimed
the config was the source long before `serve.py` read it — the constant merely happened to match.

`rag`'s own web UI defaults to `8765`; they do not collide, and this server never starts that one.

## Tests

`scripts/test_serve.py`. The routes are the easy half; the half worth reading is the refusals —
every write gate, every rejected path, the trash cap at exactly 20, and `--read-only`. It seeds
fake bundles and passes `--no-fetch --no-reindex`, so it needs no network and no clock.

**The glossary, the date, the in-place editor and every tag surface exist only once JavaScript has
run**, so the server-side half cannot see them at all. They are asserted in
`test_renders_in_a_browser` and `test_tags_render_in_a_browser`, which are opt-in and must be run
for any change to the page:

```bash
WIKI_UI_ASSETS=<a vault>/.wiki/ui-assets python3 scripts/test_serve.py
```

It skips loudly when Chrome or the real bundles are missing, and a skipped check is never a pass.

## No access code on a network bind

`--host lan` serves the vault to the whole network with **no challenge of any kind**: anyone who
can reach the address can read every note and edit it. The banner says so on every start.

The six-digit gate that used to stand there was removed at the owner's instruction. It printed the
code only in the terminal that started the server, which made the page unusable from a phone
whenever that terminal was not in front of them. The trade is deliberate and it is theirs: bind to
loopback when the network is not one they control.
