# AGENTS.md — working in this vault

A personal Obsidian knowledge vault. 137 notes, git-tracked, synced through iCloud Drive.
This file is orientation and hazards. **`index.md` is the routing map — read it before looking for
anything or deciding where new material goes.**

## The areas

| Folder | Holds |
|---|---|
| `Dev/` | Software development, 79 notes in 5 groups: `architecture/`, `frontend/`, `infra/`, `languages/`, `practices/` |
| `AI/` | Transformer internals, LLM fine-tuning, PyTorch, Hugging Face |
| `PhD/` | MSPC research — multivariate statistical process control and fault diagnosis |
| `Banking/` | Generic MiFID II / WpHG regulation, plus `COBA/` for Commerzbank-specific knowledge |
| `Mathematik/` | Vector/matrix products, dot product, ML math foundations |
| `Work-life/` | Workplace diplomacy, feedback, boundaries, self-help |
| `Quick note/` | Obsidian/LaTeX setup, benchmarks, macOS configs |
| `Excalidraw/` | Drawings (plugin folder) |
| `Kanban/` | Board plans (plugin folder) |
| `Dairy/` | Obsidian daily notes (empty) |

## Three distinctions that get gotten wrong

1. **`PhD/` is MSPC only** — multivariate statistical process control, fault diagnosis, PCA/T2/SPE.
   Monolith-decomposition research is *not* PhD material here; it lives in
   `Dev/architecture/Monolithic decomposition/`.
2. **`Banking/` is generic, `Banking/COBA/` is Commerzbank-specific.** The test: does the material
   name an internal system or API — `Tamara`, `CPMS`, `Sau`/`WBF-E-SAU`, `DocFamily`, `Filiale`,
   `FRÜHSTART`, `AVD`? Then it is COBA. A generic regulatory concept stays in `Banking/`.
3. **`Dev/LLM/` is a code sandbox, not an AI notes folder.** AI and LLM notes live in `AI/`. The
   folder keeps its name only because the code inside it does.

## Hazards

- **Never write into `.obsidian/`.** It holds plugin and workspace state. Two folder names are
  referenced from config and will break a plugin if renamed:
  - `Dairy/` — the daily-notes folder (`.obsidian/daily-notes.json`). It is empty on purpose. Do not
    "clean it up", and do not fix the spelling.
  - `Excalidraw/` — the Excalidraw plugin's folder.
- **`Dev/architecture/Monolithic decomposition/Paper/Archive/` is out of scope.** Never read, open,
  grep or modify anything inside it. Treat it as if it is not there.
- **Not notes — never index, never reformat:** `_utils/` (MCP servers and their logs), `Dev/LLM/`
  (Python sandbox: `src/`, notebooks, `requirements.txt`), `Dev/languages/Python/*.py` and `*.ipynb`,
  `.tmp/`, `.wiki-index/`.
- **Tracked secrets.** `Dev/languages/Python/key.txt` and `.tmp/.env.zip` are committed to git. Do not
  print their contents, and do not add more secrets to the vault. Cleaning git history is the owner's
  call, not an agent's.
- **iCloud sync.** Files can be evicted to the cloud and materialise on access. A file that appears
  missing may simply not be downloaded yet — check before concluding it was deleted.
- **`.venv/` at the vault root is a symlink, not project code.** It points at the RAG environment
  outside iCloud. Do not read it, index it, or treat this vault as a Python project because of it.
- **Filenames contain spaces, German umlauts, em dashes and smart quotes.** Always quote paths.
  macOS stores them NFD-normalised, so a byte comparison against an NFC string can fail even though
  the path resolves fine.

## Conventions

- **Links:** `[[wikilinks]]`, resolved by note name, not path. The vault has almost no note-to-note
  links — that is normal here, not a defect to fix in bulk.
- **Tables of contents:** markdown anchors, `[Section](#Section%20Name)`. Older notes still use
  `[[#Section|Section]]`; both render. New TOCs use the markdown form.
- **Frontmatter:** used by 3 files only (Kanban and Excalidraw, both plugin-generated). Do not add it.
- **Filenames:** mixed Title Case, kebab-case, and numbered prefixes. `Dev/languages/Kotlin/` uses a
  deliberate `0000001`–`0000008` sequence that maps onto the curriculum in its `0 LIST.md` — keep them
  in sync if you add one.
- **Attachments:** per-folder `resources/` subfolders, embedded with `![[image.png]]`.
- **Dates:** ISO, `2026-08-02`.
- **Language:** notes are in English and German; keep whichever a note already uses.

## Editing rules

- **Additive by default.** Do not rewrite, reflow or delete existing note prose. Material that
  contradicts a note is appended as a dated correction, not a silent overwrite.
- **Update `index.md` in the same change** whenever you add, move, rename or remove a note. A stale
  index is worse than no index.
- **Never state what a source did not say.** Transcribing a screenshot means transcribing it, not
  filling in what was cut off.

## Semantic search (`.rag/`)

There is a local, offline retrieval index over the vault. It returns ranked passages with exact
citations (`file:line-range — heading trail`); it does **not** write answers. Use it to find where
something is discussed when `index.md` routing is not specific enough — especially for paraphrased
or cross-language questions, where grep fails.

```bash
.rag/bin/rag search "how do I set a boundary when scope creeps mid-task" -k 5
.rag/bin/rag search "Geeignetheitserklärung" --path "Banking/**"
.rag/bin/rag update              # after adding or editing notes
.rag/bin/rag status
```

- **It is multilingual.** An English question finds the German `Work-life/` notes and vice versa.
- **It covers 144 files / 3055 chunks** — the notes only. It deliberately excludes everything in the
  "not notes" hazard above, plus `Excalidraw/` and anything starting with `.` or `_`. If a search
  finds nothing, check `.rag/.ragignore` before concluding the vault is silent on a topic.
- **Scores are informative here:** a real hit lands 0.67–0.95; a topic the vault does not cover
  lands at 0.001. A whole result list in the thousandths means "not in these notes".
- **Run `update` after any bulk change**, in the same pass as updating `index.md`. The index is a
  snapshot and will otherwise answer from stale content.

**Hazard — `.rag/` is half-synced by design.** `config.toml`, `docs/`, `toolkit/`, `bootstrap.sh`
and `requirements.txt` live in iCloud. `.rag/cache`, `.rag/db`, `.rag/state` and `<vault>/.venv` are
**symlinks** to `~/.local/share/rag/my-wiki/` and hold 7.7 GB that must never enter iCloud. Never
`rm -rf .rag/db` or `.rag/state` — that deletes the link and orphans the store. On a new machine
the links arrive dangling; `bash .rag/bootstrap.sh` rebuilds them. To check whether any path is a
link and where it really lives: `python3 -c "import os;print(os.path.realpath('<path>'))"` — a
result under `~/.local/share/rag/` is outside iCloud, which is what you want. Full detail in
`.rag/docs/MAINTAINER_MANUAL.md`.

## Working here

| Task | Command |
|---|---|
| File new material into the right note | `/wiki` with the content |
| Ask a question answerable from the notes | `/wiki <question>` |
| Rebuild the routing map after direct edits | `/wiki refresh` |
| Health check: duplicates, orphans, drift | `/wiki audit` |
| Restructure folders (plans first, then asks) | `/wiki refactor` |
| Find passages semantically, with citations | `.rag/bin/rag search "..."` |
| Refresh the search index after edits | `.rag/bin/rag update` |
| Rebuild search after cloning to a new Mac | `bash .rag/bootstrap.sh` |

- Undo for any bulk change: `git -C <vault> reset --hard <sha>`.
- Deleted notes go to `.wiki-index/refactor/trash/` at their original relative path, never `rm`.
  Nothing empties that folder automatically — clearing it is the owner's decision.
