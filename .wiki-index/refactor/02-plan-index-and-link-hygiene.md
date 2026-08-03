# 02 — Sub-plan: index-and-link-hygiene

Notes read in full for this pass: `Kanban/PhD.md`, root `index.md`, `Dev/index.md`.

```
LINK   Kanban/PhD.md :: remove `[[Reorganise plan]]` (line 7)
       why: scan finding #1 — target never existed with real content (0-byte placeholder deleted
       in 76feaae); no valid target to repoint to, so the dead reference is removed rather than
       invented.

EDIT   index.md :: `## Kanban/` section
       why: scan finding #1 — drop the `Kanban/Reorganise plan.md` line; file does not exist.

EDIT   Dev/index.md :: line 29
       why: scan finding #3 — "16 notes" -> "17 notes" for Skia-React-Native (find-verified: 17
       content notes, excluding its own index.md).

REGEN  .wiki-index/manifest.json
       why: scan finding #4 — snapshot predates the 76feaae refactor.

LEAVE  Kanban/PhD.md :: `[[Understand alternative distributions]]` (line 8)
       why: scan finding #2 — pre-existing, ambiguous, already reported by the first pass; no new
       target exists. Re-report only.

LEAVE  Excalidraw/Drawing 2026-07-20 00.46.12.excalidraw.md :: `[[Stuff]]` x2
       why: scan finding #2 — pre-existing, ambiguous, target lives in `.trash/`; already reported
       by the first pass. Re-report only.
```

No TRASH, MOVE, MERGE, SPLIT, or NEW-folder operations proposed — nothing changes location or is
superseded. Every operation above stays inside this unit's scope (no territorial decision made).
