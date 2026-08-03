# 00 — Scan (second pass)

Run date: 2026-08-02. Scope: whole vault. Vault type: Obsidian, profile `my-wiki` active.
Baseline commit: `97e36c5` (clean tree). Prior refactor completed same day at `76feaae` — this pass
checks for drift since then; supersedes the first-pass scan below for resume purposes.

## Inventory

- ~150 markdown notes across 10 top-level folders (`Dev/ AI/ Banking/ Dairy/ Excalidraw/ Kanban/
  Mathematik/ PhD/ Quick note/ Work-life/`); `.rag/` and `_utils/` are tooling, not notes, excluded.
- Folder structure unchanged since `76feaae` (5 `Dev/` groups, merged/renamed files from that pass
  all present and correct).

## Link graph

Re-grepped all `[[...]]` across the vault (~260 matches, same order of magnitude as the first pass).
Still effectively no real note-to-note link graph. Only 2 live wikilinks in the whole vault, both in
`Kanban/PhD.md`:

- `[[Reorganise plan]]` (line 7) — broken, **new** since `76feaae` (see Finding 1)
- `[[Understand alternative distributions]]` (line 8) — broken, pre-existing, already surfaced and
  left ambiguous by the first pass (`04-operations.md:123`); still no target
- Plus 2 pre-existing broken `[[Stuff]]` refs in `Excalidraw/Drawing 2026-07-20 00.46.12.excalidraw.md`
  (target in `.trash/`), also already left ambiguous by the first pass

All other matches are intra-note TOC anchors, Python/JS list literals in code fences, or convention
docs (`index.md`, `AGENTS.md`, `.rag/docs/*`) — not real links.

## Findings — hygiene (no structural findings this pass)

1. **Dead index entry + broken link, Kanban/** — root `index.md`'s `## Kanban/` section lists
   `Kanban/Reorganise plan.md`; file does not exist on disk. `Kanban/PhD.md:7` links
   `[[Reorganise plan]]` to the same nonexistent file.
   Root cause, verified via git history: source was `Kanban/Reorgenise plane.md`, a 0-byte
   placeholder since commit `0e8c818`. The `76feaae` refactor commit deleted it
   (`D Kanban/Reorgenise plane.md`, 0 insertions/deletions); the rename to `Reorganise plan.md`
   recorded `[done]` in that run's `04-operations.md:96` never actually landed. No content loss —
   source was empty.

2. **Pre-existing broken links, unchanged** — `[[Understand alternative distributions]]` and
   `[[Stuff]]` ×2 remain ambiguous, no valid target. Already reported by the first pass. No action;
   re-reported only, per `operations.md` phase 8 ("ambiguous → leave and report").

3. **Stale count, `Dev/index.md:29`** — states `Dev/frontend/Skia-React-Native/` has "16 notes";
   actual is 17 (`find`-verified).

4. **Stale manifest** — `.wiki-index/manifest.json` (`scanned_at: 2026-08-02T13:25:00Z`,
   `file_count: 152`) predates `76feaae` and does not reflect the current tree.

No territorial findings. Protected paths (`Dairy/`, `Excalidraw/`, `Kanban/`,
`Dev/architecture/.../Archive/`, `_utils/`, `Dev/LLM/`, `.tmp/`, `.obsidian/`, `.trash/`,
`.wiki-index/`) are untouched by every finding above.

---

## First-pass scan (2026-08-02, baseline `93c89c7`) — kept for history

Run date: 2026-08-02. Scope: whole vault. Vault type: Obsidian (`.obsidian/` present, wikilink syntax).
Baseline commit: `93c89c7`.

### Inventory

- 146 markdown notes (excluding `.trash/`, `.wiki-index/`)
- Top-level areas: `AI/` 15, `Banking/` 4, `Dev/` 97, `Excalidraw/` 2, `Kanban/` 2, `Mathematik/` 1,
  `PhD/` 6, `Quick note/` 7, `Work-life/` 11, `_utils/` 2 (tooling)
- Empty folders: `Dairy/`, `_templates/`
- `Dev/` is 66% of the vault across 19 flat subfolders
- Largest notes: `Dev/Kotlin/0000008 Kotlin Multiplatform KMP.md` 2035, `…/Archive/domain-skeleton-…-benchmark-plan.md` 1881,
  `Mathematik/vector-products-notes.md` 1850, `…/java-ee-monolith-knowledge-gaps-book.md` 1827

### Link graph

**The vault has effectively no link graph.** Of ~256 `[[...]]` matches:

- **1** real note-to-note wikilink: `Kanban/PhD.md` → `[[Reorgenise plane]]`
- 2 broken: `Excalidraw/Drawing 2026-07-20 00.46.12.excalidraw.md` → `[[Stuff]]` ×2 (target is in `.trash/`)
- 1 broken: `Kanban/PhD.md` → `[[Understand alternative distributions]]` (never written)
- The rest are Python list literals inside code fences (`[[0, 1, 2, 3]]`, `[[5.0]]`) and intra-note
  `[[#Section|Text]]` TOC anchors

Consequence: moving and renaming carries near-zero link risk in this vault, which is what makes the
scale of this refactor safe. Verified by resolving every extracted target against the note-name index.

Name collisions (Obsidian resolves by name): `001 Topics` ×2, `Topics` ×2, `method-idea-consolidated` ×2.
None are link targets, so none are live problems.

Frontmatter: 3 of 146 files. Not a convention — do not add it.

### Findings — structural

- **S1** `Banking/COBA/AVD/knowledge.md` is byte-identical to `Banking/AV/AV-refiment.md` (md5 `28912ec51d5d31cb1ca23aec9bf3b0e0`).
- **S2** `Dev/Read/Untitled.md` (346 lines, no H1) is an earlier take on `Dev/How to Read and Understand Code Quickly.md` (302 lines). 42 lines shared, 93 unique to Untitled.
- **S3** `Dev/LLM/` contains no LLM notes — dot-product math (5), ML-math foundations (8), plus a Python/notebook sandbox. The actual LLM notes are in `AI/`. The folder name misroutes.
- **S4** Math split across three places: `Mathematik/` (1 note), `Dev/LLM/Dot product_2025-03-09/`, `Dev/LLM/machine learning/5- Matrices and Determinants.md`.
- **S5** `AI/tourch/` — misspelled, one file, content is nn.Linear/attention projections = `AI/Transformer/` territory.
- **S6** `Dev/Monolithic decomposition/` (17 notes) is research/paper work sitting loose at `Dev/` root.
- **S7** Empty folders: `Dairy/`, `_templates/`.
- **S8** Single-file folders: `Dev/JS/`, `Dev/Java/`, `Dev/Microfrontend/`, `Dev/Read/`, `Dev/Spec/`, `Dev/redux/`, `AI/tourch/`, `Mathematik/`, `Dev/Architect/`.
- **S9** `Dev/wk/` — unroutable name; holds Spring Security + client/server certificates.
- **S10** `Dev/` has 19 flat subfolders and no grouping layer.
- **S11** Code and binaries stored as vault content: `Dev/Python/` (3 `.py`, 2 `.ipynb`, `key.txt`), `Dev/LLM/src/` + 5 notebooks + `requirements.txt` + 8 `.md.pdf`, `AI/opencode.json`, `Quick note/OS/models.json`, `_utils/`, `.tmp/`.
- **S12** `Dev/Monolithic decomposition/java-ee-monolith-knowledge-gaps-book.md` is a Java EE learning book, not decomposition research — misfiled inside a research folder.

### Findings — hygiene

- **H1** `Dev/Skia-React-Native/013 Skia with react-native-gesture-handler and react-native-reanimated` has **no `.md` extension** — invisible to Obsidian.
- **H2** `AI/Transformer/LLM-Fine-Tuning.md.md` — double extension.
- **H3** `Kanban/Reorgenise plane.md` — 0 bytes, misspelled, and the only wikilink target in the vault.
- **H4** Filename typos: `AI/tourch/`, `PyTorsh-gpt.md`, `Kotlin/exmaple.md`, `…Java copy.md`, `elastic stack/filbeats.md`, `needen cert.md`, `generte cert steps.md`, `TeamCity/docker_connetion.md`, `Skia…/000 Techincal.md`, `Banking/AV/AV-refiment.md`.
- **H5** `Dev/Kotlin/`: six files prefixed `0000001`, no `0000007`. `0 LIST.md` is the curriculum MOC whose 8 items map onto the numbered files; item 7 ("Asynchronous Programming with Coroutines") corresponds to the unnumbered `Difference Between runBlocking-launch-async.md`.
- **H6** `Banking/mifid-wphg-banking-notes.md` — 8 backslash-escaped wikilinks in the TOC from a pandoc conversion, 3 hard-wrapped across two lines. TOC renders as literal text.
- **H7** Tracked junk: 4 `.DS_Store`, 2 `_utils/*.pyc`, 2 `*.log`.
- **H8** **`Dev/Python/key.txt` (24 bytes) and `.tmp/.env.zip` are committed to git.** Reported, not actioned — out of scope for a notes refactor.

### Findings — index conflicts

- **I1** `Banking/stuff.md` listed in root index; does not exist (a `Stuff.md` sits in `.trash/`).
- **I2** `Mathematik/Vector and Matrix Multiplication Notes.md` listed; actual file is `vector-products-notes.md`.
- **I3** Wrong counts: `Dev/` "103 notes" (actual 92 content notes), `AI/` "15 notes" (actual 14), `Quick note/` "7 notes" (actual 6).
- **I4** Root `## Contents` omits `Dairy/`, `_templates/`, `_utils/`.
- **I5** `PhD/` `Place here:` line names monolith decomposition — wrong. **PhD/ is MSPC-only** (user-confirmed).
- **I6** `Dev/index.md` has no `Place here:` line for any of its 19 subfolders — routing dead-ends.
- **I7** `Banking/` section describes `Banking/AV/` but lists neither of its two files.

### Config constraints discovered

These override any structural instinct and are recorded because they are not visible from the note tree:

- `.obsidian/daily-notes.json` → `{"folder": "Dairy"}`. **`Dairy/` is the daily-notes folder** — never rename, never trash despite being empty.
- `.obsidian/plugins/obsidian-excalidraw-plugin/data.json` → `"folder": "Excalidraw"`. Never rename.
- `.obsidian/app.json` → `alwaysUpdateLinks: true` (only applies to renames done inside Obsidian; ours are external, so links are rewritten by hand).
- `_templates/` is referenced only by `workspace-mobile.json` (UI state) and the tasks plugin's bundled docs. QuickAdd's `templateFolderPath` is empty. Safe to remove.
- Standing rule: `Paper/Archive/` is never read or opened. Not opened during this scan; its file names are known only from a directory listing.
