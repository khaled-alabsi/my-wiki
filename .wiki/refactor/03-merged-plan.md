# 03 — Merged plan (scope: `Dev/`)

Reconciled from the three sub-plans. This is the only file execution reads.

## Conflicts found
**None.** Unit 2 proposes no operation, so no path collision with unit 1 is possible. Unit 3 records
only. No unit renames a file another unit moves.

## Recomputed global effects
- `Dev/` ends with `architecture/ frontend/ infra/ languages/ practices/ LLM/ index.md`.
- No surviving folder gains or loses a note, so no folder crosses the ~15 regrouping threshold or
  falls empty.
- Link rewrite: **no-op.** No wikilink in the vault resolves to a `Dev/` note.
- Note count under `Dev/` goes from 154 to 74 (+1 if D2 keeps the capture as its own note).

## Ordered operations

| # | Op | Target | Gate |
|---|---|---|---|
| 1 | verify hashes | 16 folders of OP-1 | every file must match a grouped counterpart |
| 2 | trash | those 16 folders | to `.wiki/.trash/<original path>` |
| 3 | D2 | `Dev/Read/Untitled.md` | per the accepted option; append-then-verify before trash |
| 4 | D1 | `Dev/Dev tools/Vs code configs.md` | move, then trash the empty folder |
| 5 | index | root `index.md` — drop `Dev/wk/`, fix counts | — |
| 6 | index | `Dev/index.md`, and `Quick note/` if D1 lands there | — |
| 7 | rag | `.rag/bin/rag update --quiet` | once |

## Open decisions
- **D1** — where `Vs code configs.md` goes. Recommended `Quick note/VS Code macOS local network
  access.md`.
- **D2** — what happens to `Dev/Read/Untitled.md`. Recommended: fold its 28 uncarried lines into the
  shaped note, verify, then trash.
- **D3** (out of scope, reported only) — the third copy of the code-reading note at the vault root.

## Not changing
The grouped layout's folders and files; `Dev/LLM/`; `Dev/languages/Python/` scratch code and
`key.txt`; the `Skia-React-Native/` and `Kotlin/` numbered curricula; the four local `index.md`
files' structure; anything outside `Dev/` except the root index entries and D1's destination.

## Undo
`git -C "<vault>" reset --hard <sha-before-execution>` — the owner takes that sha and runs it; this
skill runs no git command in this vault.
