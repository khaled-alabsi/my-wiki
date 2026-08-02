# RAG maintainer manual

Internals, tuning, and repair for the index at `<vault>/.rag`.

Read §9 first if anything is broken. This install sits inside an iCloud container, which is the
source of every non-obvious failure this workspace has hit: hidden `.pth` files, unsyncable
symlinks, and the empty `* 2` folders they leave behind.

---

## 1. Layout

```
.rag/
├── config.toml        the only file you normally edit
├── .ragignore         exclusions, gitignore syntax
├── .gitignore         commits config/docs/toolkit, ignores db/state/cache/.venv
├── requirements.txt   pinned dependency set, with rebuild instructions
├── bootstrap.sh       rebuilds everything below the line, on a new machine
├── mcp.json           MCP registration snippet to copy into an agent host
├── VERSION            vendored toolkit version (1.2.0), for drift detection
├── docs/              these four documents
├── toolkit/           the vendored Python package — the code that runs
├── notebooks/         rag_quickstart.ipynb
├── bin/rag, bin/rag.cmd   launchers
└── .vscode/settings.json   (at the vault root) points VS Code at the interpreter

~/.local/share/rag/my-wiki/     ── OUTSIDE iCloud, no link points here ──
├── venv     the Python environment, 1.5 GB
├── cache    model weights, 6.4 GB
├── db       the lancedb vector store, 19 MB
└── state    manifest.sqlite, progress.json, index.lock
```

**There are no symlinks anywhere in the vault, deliberately.** iCloud Drive cannot sync a symlink —
it replaces each one with an empty folder called `cache 2`, `db 2`, `.venv 2`, and they reappear
after every deletion. The store location lives in `config.toml` (`project.store`, `project.venv`)
and the toolkit reads it directly; `.rag/bin/rag` has the interpreter path baked in.

**The virtualenv is not inside the vault at all.** It lives in the external store; VS Code finds it
through `.vscode/settings.json` (`python.defaultInterpreterPath`), and the launchers have its
absolute path written into them by `install.write_launchers()`.

An earlier version symlinked it to `<vault>/.venv` (that path no longer exists). The symlink
produced iCloud conflict folders and was removed. If you ever see `.venv 2`, `cache 2` or `db 2` appear, something recreated a symlink —
`bash .rag/bootstrap.sh` removes both the links and the empty conflict folders.

**Commit** `config.toml`, `.ragignore`, `requirements.txt`, `bootstrap.sh`, `mcp.json`, `docs/`,
`toolkit/`, `VERSION`. **Never commit** `db/`, `state/`, `cache/`, `.venv/` — derived, large, and
machine-specific.

That committed/ignored split is exactly the same split as in-iCloud/out-of-iCloud. The rule is one
rule: **if `.rag/.gitignore` ignores it, it does not belong in the iCloud container either.**

`state/` moves with `db/` and is not optional. `manifest.sqlite` records which files are already
indexed; if it synced while `db/` stayed machine-local, a second machine would inherit a manifest
claiming all 144 files are done against an empty store, and `update` would skip every one of them —
producing an empty index that reports success.

## 2. The pipeline

```
discover → extract → chunk → embed → store
```

**discover** (`discover.py`) walks the source. Ignore precedence, first match wins: built-in skip
list → **private-name rule** (any name starting with `.` or `_`, not configurable) → `.ragignore`
→ the vault's `.gitignore` → `sources[].include` allowlist → size cap → binary sniff → "is there
an extractor".

**extract** (`extract/`) turns a file into a `Document` with a `kind` naming a chunking strategy.
For this vault that is Markdown plus two JSON files. A missing optional dependency makes a file
*unsupported with a reason* — never a silently empty document.

**chunk** (`chunk.py`) splits by structure first: headings for Markdown, paragraphs as fallback.
Every chunk gets a context prefix (`path > heading trail`) embedded with it but shown separately.
Anchors point at the chunk's own span, never at overlap borrowed from a neighbour — verified on
this index against three files, and they land exactly on the cited heading.

**embed** (`embed.py`) batches through sentence-transformers. The **real** dimension is read from
the loaded model (1024, confirmed), never trusted from the registry.

**store** (`store.py`) upserts by `chunk_id`. LanceDB gives vector search, metadata filters, and
full-text search in one embedded directory.

## 3. Incremental updates

A file is re-processed only when its size or mtime changed. Then: re-extract, re-chunk, re-embed
that file only; compute new chunk ids; delete the file's previous chunks that no longer exist;
upsert the new ones.

Files that vanished are removed from manifest and store on the next pass. Because every file is
committed to sqlite immediately, **a killed run resumes by re-running the same command** — no
checkpoint to repair.

## 4. Configuration

| Key | Now | Effect |
|---|---|---|
| `chunking.target_chars` | 1800 | Bigger = more context per hit, blurrier matching. Smaller = sharper, more fragments. |
| `chunking.overlap_chars` | 220 | Guards an answer split across a boundary. ~12% of target. |
| `chunking.prefix_context` | true | Embeds `path > heading trail`. Largest recall gain on a notes vault — leave it on. |
| `retrieval.top_k` | 10 | Results returned. |
| `retrieval.candidates` | 60 | Pulled from each retriever before fusion. Raise if a known answer ranks low. |
| `retrieval.hybrid` | true | Dense + keyword. Turn off only to diagnose. |
| `retrieval.rerank` | true | Cross-encoder pass. The biggest quality lever available. |
| `corpus.language` | multi | Set deliberately — the vault holds substantial German notes. |
| `corpus.max_file_mb` | 25.0 | Cap. Raise deliberately; one huge file can dominate. |
| `corpus.ocr` | false | Correct — there are no PDFs in this vault. |

```bash
.rag/bin/rag config set retrieval.top_k 15
.rag/bin/rag config show
```

**Anything under `embedding.` or `chunking.` requires `rag index --full`.** Retrieval keys take
effect on the next search.

### Why `target_chars` is 1800 and not higher

`bge-m3` accepts 8192 tokens, which invites raising the target. Resist it. A chunk that spans
several topics matches everything weakly; the long context is useful here because it means an
oversized section is never *truncated*, not because bigger chunks retrieve better. The observed
result of leaving it at 1800: 144 files produced 3055 chunks, well above the ~1279 the byte-based
estimate predicted, because these notes are heading-dense and split naturally.

## 5. Swapping the embedding model

Every model name lives in exactly one place: `toolkit/rag_toolkit/models.py`.

1. Edit or add the entry in `EMBEDDINGS`.
2. `.rag/bin/rag config set embedding.model NEW_ID` and
   `.rag/bin/rag config set embedding.backend fastembed|sentence-transformers`.
3. `.rag/bin/rag doctor --models` — verify it loads and see its real dimension.
4. `.rag/bin/rag index --full` — **not optional**.

Skipping step 4 leaves vectors from two models in one store. They are not comparable, and results
become quietly wrong rather than obviously broken. `status` and `doctor` both refuse to call that
healthy, and `update` raises rather than proceeding.

The `dimension` in `models.py` is advisory; the loaded model is authoritative.

The registry now states the measured on-disk figures (`approx_disk_mb`), not download sizes:
`bge-m3` is **4.3 GB** and `bge-reranker-v2-m3` **2.1 GB** — **6.4 GB** together. Earlier versions
advertised 4600 MB for the pair, which was 40% low.

## 6. Diagnosing bad results

| Symptom | Check | Likely fix |
|---|---|---|
| Nothing matches anything | `doctor` | Index empty or never built → `index` |
| Right note exists, never returned | `.ragignore` | It is probably excluded by design — see §8 |
| Exact terms miss, paraphrase works | `doctor` store line | FTS index missing → §9 |
| Paraphrase misses, exact works | `status` | Model drift, or `hybrid` masking a bad model |
| Topically right but too vague | — | `target_chars` too high, or reranking off |
| Results are fragments | — | `target_chars` too low |
| One note floods every result | — | Near-duplicates; exclude in `.ragignore` |
| Was fine, now wrong | `status` | Model drift → `index --full` |
| `ModuleNotFoundError: rag_toolkit` | §9 | Hidden `.pth` — the known iCloud failure |
| `ModuleNotFoundError: sentence_transformers` **in a notebook** | `sys.executable` in the notebook | Wrong kernel — select `my-wiki RAG (.venv)`. `rag_toolkit` imports on any kernel, so this is the first symptom. |

`rag doctor` runs a store round-trip (create, upsert, search, delete) against a scratch directory,
to catch a vector-store version mismatch in two seconds rather than two hours into an index run.

## 7. Concurrency

`state/index.lock` holds the pid and start time of the running index. A second run refuses to
start. If a run was killed hard, the lock is stale once its pid is gone or after six hours;
otherwise delete it by hand.

Never run two index jobs against one workspace, and never in parallel with other memory-heavy
work — embedding is memory-bound, and an OOM kill mid-run is the main cause of a
corrupted-looking store.

## 8. What is excluded, and why

| Excluded | Reason |
|---|---|
| any name starting with `.` or `_` | Built-in, not configurable. Covers `.obsidian/`, `.trash/`, `.tmp/`, `.wiki-index/`, `_utils/`. |
| `Dev/LLM/` | `index.md` lines 27–28: "not notes, never indexed" — it is a code sandbox. |
| `Dev/languages/Python/*.py`, `*.ipynb` | Same declaration in `index.md`. |
| `Dev/languages/Python/key.txt` | Credential-shaped name. Excluded on the name alone; the file was never opened. |
| `Excalidraw/`, `*.excalidraw.md`, `*.excalidrawlib` | Obsidian plugin wrappers around compressed drawing JSON. The only prose is a few disconnected canvas labels. |
| images, media | No text extractor. |

`.wiki-index/refactor/trash/` deserves a note: it holds copies of moved notes and would have been
a near-duplicate source flooding results. It is excluded by the private-name rule, but if you ever
rename that folder without a leading dot, exclude it explicitly.

To change any of this, edit `.ragignore`, then `rag plan` (free, instant) before `rag index`.

## 9. Environment hazards specific to this install

The vault lives at `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-wiki`, i.e. inside
an iCloud container. Two real problems came from that, both already fixed in toolkit 1.1.2.

### Hidden `.pth` — `ModuleNotFoundError: No module named 'rag_toolkit'`

macOS sets `UF_HIDDEN` on files beneath a dot-directory in an iCloud container. CPython **3.13 and
later skip `.pth` files carrying `UF_HIDDEN`**, so `.venv/lib/python3.13/site-packages/rag_toolkit.pth`
was written correctly, was byte-for-byte valid, and was simply never read. Every launcher call
failed while a direct `sys.path.insert` worked — which is what makes it confusing.

Diagnose:

```bash
ls -lO .venv/lib/python3.13/site-packages/rag_toolkit.pth   # look for "hidden" in column 5
```

Fix, if it ever returns:

```bash
chflags nohidden .venv/lib/python3.13/site-packages/rag_toolkit.pth
```

Both launchers now also `export PYTHONPATH="$here/toolkit"`, so they no longer depend on `.pth`
processing at all. Keep that line if you regenerate them.

### iCloud syncing rebuildable data — resolved by relocation

`.venv/`, `cache/`, `db/` and `state/` were originally inside the synced container: 7.7 GB of
large, machine-specific, fully rebuildable data. Beyond the quota cost, iCloud's "optimize
storage" can evict a file, and an evicted weights file or venv library breaks the install in a way
that looks like corruption.

They now live at `~/.local/share/rag/my-wiki/` and are reached through symlinks. Nothing in the
config changed — the symlinks are transparent to the toolkit, which is why `cache_dir` did not
need setting. Verified after the move: `doctor` reports 0 failed / 0 warnings and a probe query
returns a byte-identical score.

To relocate again, or to a different path, use `STORE=/new/path bash .rag/bootstrap.sh` after
moving the directories yourself.

### lancedb full-text index

`store.py` used to call `create_fts_index(["text", "prefix"])`. lancedb ≥ 0.25 rejects multi-column
FTS and has deprecated that method, so the call failed, the exception was swallowed, and hybrid
retrieval silently degraded to dense-only. Fixed in 1.1.1: one index per column via
`create_index(col, config=FTS())`, with fallbacks. If `doctor` ever reports "the full-text index
could not be built", exact-term search is compromised — do not ignore it.

## 10. Upgrading the vendored toolkit

`VERSION` records the vendored copy; `doctor` compares it to the code's own version and warns on
drift.

1. Re-copy the skill's `scripts/rag_toolkit/` over `.rag/toolkit/rag_toolkit/`.
2. `python3 .rag/toolkit/rag_toolkit/install.py` for any new dependencies.
3. Update `.rag/VERSION` and `config.toml`'s `toolkit_version` to match.
4. `.rag/bin/rag doctor`
5. `.rag/bin/rag index --full` **only if** chunking or embedding defaults changed.

## 11. Rebuilding from nothing

```bash
rm -rf ~/.local/share/rag/my-wiki/db/* ~/.local/share/rag/my-wiki/state/*
.rag/bin/rag index --full
```

Delete the contents of the **store**, not anything in `.rag/`. There is nothing to delete in
`.rag/db` — that path does not exist any more.

`config.toml`, `.ragignore`, `docs/`, and `toolkit/` survive. Only derived data is discarded. On
this vault a full pass costs about 285 seconds. This is the safe reset when the store looks
inconsistent.

## 12. Setting up on a new machine

iCloud brings the vault and the committed half of `.rag/` — config, ignores, docs, the vendored
toolkit, `requirements.txt`, `bootstrap.sh`. It does **not** bring the venv, the model weights, the
vector store, or the manifest; `config.toml` will point at a store path that does not exist yet.

```bash
cd "<vault>"
bash .rag/bootstrap.sh
```

That is idempotent and does the whole environment half:

1. creates `~/.local/share/rag/my-wiki/{venv,cache,db,state}` (override with `STORE=...`)
2. creates the store directories, and removes any symlink or empty `* 2` folder left inside the vault
3. builds the venv with the first CPython ≥ 3.11 it finds (override with `PYTHON=...`)
4. installs the pinned set from `requirements.txt`
5. writes `rag_toolkit.pth` **and clears `UF_HIDDEN` on it** — see above; `mv` preserves that flag,
   so it can even survive a relocation
6. regenerates both launchers, pointed at `~/.local/share/rag/my-wiki/venv/bin/python`
7. runs `doctor`

Then, one at a time — these are the slow, network-bound steps it deliberately does not run:

```bash
.rag/bin/rag doctor --models    # ~6.4 GB of weights, once per machine
.rag/bin/rag index              # ~285s for 144 notes on Apple Silicon
.rag/bin/rag status             # confirm files > 0 and chunks > 0
```

A machine without an accelerator should not use this config as-is. `tier = "large"` assumes MPS or
CUDA; on a CPU-only box switch to the `light` tier (`fastembed`, ONNX, ~560 MB, no torch) before
indexing — see §5. `rag doctor` reports the detected device.

To rebuild only the Python environment, see the header of `.rag/requirements.txt`.
