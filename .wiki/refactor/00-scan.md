# 00 — Scan (scope: `Dev/`)

Run date: 2026-09-20. Scope: the `Dev/` subtree. Link graph built vault-wide.

## Inventory

| Layer | Folders | Markdown notes |
|---|---|---|
| Grouped layout (`architecture/ frontend/ infra/ languages/ practices/`) | 5 + 11 sub | 74 notes + 4 index.md |
| Pre-refactor flat layout (18 folders) | 18 | 80 notes |
| `Dev/LLM/` (protected sandbox, not notes) | 1 | — |
| Loose at `Dev/` root | — | `index.md` only |

- Old-layout files: 84 (md + assets). New-layout files: 86.
- Link graph: **no wikilink anywhere in the vault resolves to a `Dev/` note.** Link rewriting on any
  move inside `Dev/` is a no-op. (Verified by grepping the vault's `[[...]]` style and filtering
  Python list literals and intra-note anchors, per the profile's Known state.)
- `.rag`: present and healthy — 304 files, 6645 chunks, last incremental run 161 files.

## Findings

### F1 — `Dev/` holds two complete layouts at once  `structural`  folder: `Dev/`
The 2026-08-02 refactor regrouped 19 flat folders into 5 areas. The flat folders are **back on
disk**, unchanged, alongside the grouped ones. Every pair is a genuine duplicate:

| Pre-refactor folder | Grouped counterpart |
|---|---|
| `Dev/Architect/` | `Dev/architecture/` |
| `Dev/Spec/` | `Dev/architecture/Spec format.md` |
| `Dev/Monolithic decomposition/` | `Dev/architecture/Monolithic decomposition/` |
| `Dev/React JS/`, `Dev/React-Native/`, `Dev/Skia-React-Native/` | `Dev/frontend/…` |
| `Dev/redux/`, `Dev/Microfrontend/` | `Dev/frontend/Redux_Toolkit_Notes.md`, `Themenblock.md` |
| `Dev/TeamCity/`, `Dev/elastic stack/`, `Dev/openshift/` | `Dev/infra/…` |
| `Dev/wk/` | `Dev/infra/security/` |
| `Dev/Kotlin/`, `Dev/Python/`, `Dev/Java/`, `Dev/JS/` | `Dev/languages/…` |
| `Dev/Read/` | `Dev/practices/` |
| `Dev/Dev tools/` | **no counterpart** |

Evidence: content-hash comparison of all 84 old files against all 86 new files. **82 of 84 are
byte-identical to a file in the grouped layout.** The grouped copies additionally carry the
2026-08-02 filename normalizations (`Techincal`→`Technical`, `filbeats`→`filebeats`,
`docker_connetion`→`docker_connection`, `generte`→`generate`, `needen`→`needed`,
`exmaple.md`→`Spring Boot REST API example.md`, `0000001 …` prefixes dropped from the
non-curriculum Kotlin notes) and the four `index.md` files. `Dev/Skia-React-Native/013 …` is also
missing its `.md` extension in the old copy.

### F2 — Two old files have no counterpart  `structural`  folder: `Dev/Dev tools/`, `Dev/Read/`
- `Dev/Dev tools/Vs code configs.md` — VS Code on macOS failing local-network access from the
  integrated terminal, with the `defaults write com.apple.network.local-network` fix. Nothing in the
  grouped layout covers it. Material added after the last refactor, or missed by it.
- `Dev/Read/Untitled.md` (346 lines) — the raw capture that `Dev/practices/How to Read and
  Understand Code Quickly.md` (304 lines) was shaped from. **28 sentences of the capture are not in
  the shaped note**, including "Pattern recognition is the biggest speed boost", "Data flow is
  usually easier than call flow", "Many people spend 30 minutes reading helper functions they never
  needed", and the numbered "My favourite reading algorithm" questions. It is not a safe duplicate.

### F3 — The same note exists a third time at the vault root  `structural`  folder: `/` (out of scope)
`How to Read and Understand Code Quickly.md` at the vault root (302 lines) is the
`Dev/practices/` copy minus two lines. Outside the `Dev/` scope; surfaced, not planned.

### F4 — Index drift  `hygiene`  folder: `Dev/`, `/`
- Root `index.md:106` still carries an entry for `Dev/wk/` — "2 notes; folder name gives no routing
  rule". That folder is a pre-refactor duplicate of `Dev/infra/security/`.
- Root `index.md:90,104` claim 79 notes across 5 groups. The grouped layout holds 74 notes.
- `Dev/index.md` describes the grouped layout only. It has no entry for any of the 18 old folders —
  so 80 notes currently sit in `Dev/` unreachable from any index.

### F5 — `Dev/languages/` mixes folders and loose notes  `structural`  folder: `Dev/languages/`
`Kotlin/` and `Python/` are folders; `java-ee-monolith-knowledge-gaps-book.md`,
`java-functional-interfaces.md` and `javascript-loops.md` sit loose beside them. The folder has 5
entries, well under the profile's ~15 regrouping threshold, so this is an inconsistency rather than
a size problem.

### F6 — `.DS_Store` tracked inside `Dev/`  `hygiene`
`Dev/.DS_Store`, `Dev/architecture/Monolithic decomposition/.DS_Store`. Already reported in the
profile's Known state; not re-raised as new.

## Not findings

- `Dev/frontend/Skia-React-Native/` holds 18 entries, over the profile's ~15 regrouping threshold,
  but it is a deliberate `000`–`015` curriculum with its own `index.md`. The profile rules numbered
  sequences as owner decisions. Leave it.
- `Dev/languages/Python/key.txt` and the `.py`/`.ipynb` scratch files — protected by the profile,
  already reported once.
- `Dev/LLM/` — protected sandbox, keeps its misleading name.
