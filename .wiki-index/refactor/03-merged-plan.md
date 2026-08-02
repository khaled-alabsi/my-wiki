# 03 — Merged plan

Accepted by the user on 2026-08-02. This file is what execution reads.

## Note on the artifact trail

`01-meta-plan.md` and the `02-plan-<unit>.md` sub-plans were **not** written, and are deliberately not
registered anywhere. The decomposition-then-reconcile pipeline exists to make planning feasible when a
vault is too large to hold in one pass; here the plan was derived, presented, challenged and reconciled
interactively with the user across four rounds before acceptance, so that stage was performed in
conversation rather than on disk. A resumed run should read this file and `04-operations.md` only.

## Decisions the user settled during planning

1. Regroup `Dev/`'s 19 flat subfolders into 5 areas, and fix everything broken.
2. **`PhD/` is MSPC-only.** Monolith-decomposition research nests into `Dev/architecture/` instead.
   `PhD/` is not touched by any operation; only its index `Place here:` line is rewritten.
3. Trash the 8 generated `.md.pdf` exports. Leave all code, notebooks and `_utils/` alone.
4. Normalize all filenames, including cosmetic typos.
5. `Banking/AV/` folds into `Banking/COBA/AVD/` — both notes name the same proprietary systems
   (`Tamara`, `CPMS`, `Sau`/`WBF-E-SAU`, `DocFamily`, `Filiale`, `FRÜHSTART`), so this is
   bank-specific, not generic banking.
6. `Paper/Archive/` moves as an **opaque container** — relocated, never opened.
7. The MiFID TOC is rewritten with markdown anchors (user's explicit choice over the vault's
   dominant `[[#H|T]]` form).
8. `Dev/Read/Untitled.md` merges into `How to Read and Understand Code Quickly.md` under a labelled
   section, then goes to trash.

## Global effects (threshold cascade, computed after all moves)

- `Dev/` drops from 92 to 78 content notes; still needs `Dev/index.md`.
- `Mathematik/` rises from 1 to 14 notes — under the ~15 threshold, so it stays inline in the root index.
- `PhD/` stays at 6 — inline in the root index.
- `AI/` stays at 14 — keeps `AI/index.md`.
- Leaf indexes preserved and pointed to rather than regenerated: `Kotlin/`, `Skia-React-Native/`,
  `Monolithic decomposition/`. All three are already accurate; regenerating them would burn effort and
  risk regressions. This means the index nests three levels under `Dev/`, a deliberate deviation from
  the two-level rule in `references/index-format.md`, taken because the existing files are correct.
- Emptied by moves and trashed: `Dev/Architect/`, `Dev/Spec/`, `Dev/JS/`, `Dev/Java/`,
  `Dev/Microfrontend/`, `Dev/redux/`, `Dev/Read/`, `Dev/wk/`, `AI/tourch/`, `Banking/AV/`,
  `Dev/LLM/Dot product_2025-03-09/`, `Dev/LLM/machine learning/`, `_templates/`.
- `Dev/LLM/` survives holding only code (`src/`, 5 notebooks, `requirements.txt`, `prompt/`) and is
  excluded from the index rather than deleted.
- No note ends up orphaned that wasn't already: the vault has no link graph to break.

## Protected — no operation may touch these

- `Dairy/` — `.obsidian/daily-notes.json` points at it. Empty, and stays.
- `Excalidraw/` — the Excalidraw plugin's configured folder.
- `.obsidian/`, `.trash/` — never written.
- `Paper/Archive/` contents — relocated with its parent, never read.
- All `.py`, `.ipynb`, `.json`, `requirements.txt`, `_utils/`, `.tmp/` — moved only when their parent
  folder moves; never opened, never edited.

## Left alone deliberately

- 2 broken wikilinks (`[[Stuff]]` ×2, `[[Understand alternative distributions]]`) — ambiguous targets;
  guessing would create a wrong link where there is an obviously broken one.
- `Dev/Python/key.txt`, `.tmp/.env.zip` — tracked secrets. Reported to the user; removing them from
  git history is destructive and outside this mode's scope.
- Tracked `.DS_Store`, `*.pyc`, `*.log` — reported, not actioned.

## Body-text edits

Exactly one: `Banking/mifid-wphg-banking-notes.md` lines 5–16 (the TOC). Any other body diff at the end
of the run is a defect and a stop condition.
