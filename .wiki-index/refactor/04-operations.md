# 04 — Operations

Materialized from `03-merged-plan.md` before the first operation ran. Baseline: `93c89c7`.
Undo: `git -C <vault> reset --hard 93c89c7`

Resume contract: skip `[done]`, continue from the first `[plan]`. If the record and the disk disagree,
**the disk wins** — verify, correct the record, then continue.

## Phase 1 — Create folders

- [done] MKDIR `Dev/architecture/`
- [done] MKDIR `Dev/frontend/`
- [done] MKDIR `Dev/infra/`
- [done] MKDIR `Dev/languages/`
- [done] MKDIR `Dev/practices/`
- [done] MKDIR `Mathematik/dot-product/`
- [done] MKDIR `Mathematik/ml-foundations/`

## Phase 2 — Split outputs

None.

## Phase 3 — Merges

- [done] MERGE `Dev/Read/Untitled.md` -> `Dev/How to Read and Understand Code Quickly.md` `## 12`
        DEVIATION FROM PLAN, reported to user. Planned as "append 93 unique lines under a
        `## Field notes (earlier draft)` section". Reading both files in full showed the target is a
        strict superset: all 12 sections, the reading algorithm and the closing mindset map 1:1, each
        better expressed. The "93 unique lines" were a set-difference artifact of formatting (stray
        `  ` spacers, unfenced code blocks, capitalization), not content. Exactly one sentence was
        genuinely absent — "This is probably the hardest mindset." — and it was added to `## 12.
        Accept Partial Understanding` as one line. Appending the full draft would have added ~340
        lines of inferior duplicate. Source goes to trash in phase 6 and is restorable.

## Phase 4 — Moves and renames

### Dev/architecture/
- [done] MOVE `Dev/Monolithic decomposition/` -> `Dev/architecture/Monolithic decomposition/`  (whole folder, Archive/ opaque)
- [done] MOVE `Dev/Architect/Mix Architecture patterns- Infra-Deployment strategies.md` -> `Dev/architecture/Mix Architecture patterns - Infra-Deployment strategies.md`
- [done] MOVE `Dev/Architect/resources/` -> `Dev/architecture/resources/`
- [done] MOVE `Dev/Spec/Spec format.md` -> `Dev/architecture/Spec format.md`

### Dev/languages/
- [done] MOVE `Dev/Kotlin/` -> `Dev/languages/Kotlin/`
- [done] MOVE `Dev/Python/` -> `Dev/languages/Python/`  (includes .py/.ipynb/key.txt, unopened)
- [done] MOVE `Dev/JS/loops and so.md` -> `Dev/languages/javascript-loops.md`
- [done] MOVE `Dev/Java/FunctionalInterface.md` -> `Dev/languages/java-functional-interfaces.md`
- [done] MOVE `Dev/architecture/Monolithic decomposition/java-ee-monolith-knowledge-gaps-book.md` -> `Dev/languages/java-ee-monolith-knowledge-gaps-book.md`
- [done] RENAME `Dev/languages/Kotlin/0000001  DTO.md` -> `DTO.md`
- [done] RENAME `Dev/languages/Kotlin/0000001  general.md` -> `Kotlin general.md`
- [done] RENAME `Dev/languages/Kotlin/0000001 Access Modifiers .md` -> `Access Modifiers.md`
- [done] RENAME `Dev/languages/Kotlin/0000001 Inheritance in Kotlin and Comparison with Java copy.md` -> `Inheritance in Kotlin and Comparison with Java.md`
- [done] RENAME `Dev/languages/Kotlin/0000001 Static in Java and Comparison with Kotlin.md` -> `Static in Java and Comparison with Kotlin.md`
- [done] RENAME `Dev/languages/Kotlin/Difference Between runBlocking-launch-async.md` -> `0000007 Difference Between runBlocking-launch-async.md`
- [done] RENAME `Dev/languages/Kotlin/exmaple.md` -> `Spring Boot REST API example.md`

### Dev/frontend/
- [done] MOVE `Dev/React JS/` -> `Dev/frontend/React JS/`
- [done] MOVE `Dev/React-Native/` -> `Dev/frontend/React-Native/`
- [done] MOVE `Dev/Skia-React-Native/` -> `Dev/frontend/Skia-React-Native/`
- [done] MOVE `Dev/Microfrontend/Themenblock.md` -> `Dev/frontend/Themenblock.md`
- [done] MOVE `Dev/redux/Redux_Toolkit_Notes.md` -> `Dev/frontend/Redux_Toolkit_Notes.md`
- [done] RENAME `Dev/frontend/Skia-React-Native/013 Skia with react-native-gesture-handler and react-native-reanimated` -> same name + `.md`
- [done] RENAME `Dev/frontend/Skia-React-Native/000 Techincal.md` -> `000 Technical.md`

### Dev/infra/
- [done] MOVE `Dev/TeamCity/` -> `Dev/infra/TeamCity/`
- [done] MOVE `Dev/elastic stack/` -> `Dev/infra/elastic stack/`
- [done] MOVE `Dev/openshift/` -> `Dev/infra/openshift/`
- [done] MOVE `Dev/wk/` -> `Dev/infra/security/`
- [done] RENAME `Dev/infra/elastic stack/filbeats.md` -> `filebeats.md`
- [done] RENAME `Dev/infra/elastic stack/needen cert.md` -> `needed cert.md`
- [done] RENAME `Dev/infra/elastic stack/generte cert steps.md` -> `generate cert steps.md`
- [done] RENAME `Dev/infra/TeamCity/docker_connetion.md` -> `docker_connection.md`

### Dev/practices/
- [done] MOVE `Dev/How to Read and Understand Code Quickly.md` -> `Dev/practices/How to Read and Understand Code Quickly.md`

### Mathematik/
- [done] MOVE `Dev/LLM/Dot product_2025-03-09/*.md` (5) -> `Mathematik/dot-product/`
- [done] MOVE `Dev/LLM/machine learning/*.md` (8) -> `Mathematik/ml-foundations/`

### AI/
- [done] MOVE `AI/tourch/nn-layer-exmple.md` -> `AI/Transformer/nn-layer-example.md`
- [done] RENAME `AI/Transformer/LLM-Fine-Tuning.md.md` -> `LLM-Fine-Tuning.md`
- [done] RENAME `AI/Transformer/PyTorsh-gpt.md` -> `PyTorch-gpt.md`

### Banking/
- [done] MOVE `Banking/AV/AV-ev.md` -> `Banking/COBA/AVD/AV-ev.md`

### Kanban/
- [done] RENAME `Kanban/Reorgenise plane.md` -> `Reorganise plan.md`

## Phase 5 — Link rewrite (vault-wide, after all names are final)

- [done] LINK `Kanban/PhD.md`: `[[Reorgenise plane]]` -> `[[Reorganise plan]]`

## Phase 6 — Trash superseded sources

- [done] TRASH `Banking/AV/AV-refiment.md`  (byte-identical to `Banking/COBA/AVD/knowledge.md`)
- [done] TRASH `Dev/Read/Untitled.md`  (only after re-reading the merge target and confirming content)
- [done] TRASH `Dev/LLM/Dot product_2025-03-09/Topics.md.pdf`
- [done] TRASH `Dev/LLM/machine learning/1- Variables and Functions.md.pdf`
- [done] TRASH `Dev/LLM/machine learning/2- Graphing and Plotting Points.md.pdf`
- [done] TRASH `Dev/LLM/machine learning/3- Functions and Relations.md.pdf`
- [done] TRASH `Dev/LLM/machine learning/4- Polynomials and Expressions.md.pdf`
- [done] TRASH `Dev/LLM/machine learning/5- Matrices and Determinants.md.pdf`
- [done] TRASH `Dev/LLM/machine learning/6- Statistics and Probability.md.pdf`
- [done] TRASH `Dev/LLM/machine learning/7- Data Analysis.md.pdf`
- [done] TRASH `Dev/LLM/machine learning/Topics.md.pdf`
- [done] TRASH `Dev/LLM/index.md`  (describes only folders that moved out)

## Phase 7 — Trash emptied folders

- [done] TRASH-DIR `Dev/Architect/`, `Dev/Spec/`, `Dev/JS/`, `Dev/Java/`, `Dev/Microfrontend/`,
        `Dev/redux/`, `Dev/Read/`, `Dev/wk/`, `AI/tourch/`, `Banking/AV/`, `_templates/`,
        `Dev/LLM/Dot product_2025-03-09/`, `Dev/LLM/machine learning/`

## Phase 8 — Link repair

- [done] TOC `Banking/mifid-wphg-banking-notes.md` lines 5–16 -> markdown anchors (8 entries)
- [done] LEAVE `Excalidraw/Drawing 2026-07-20 00.46.12.excalidraw.md` `[[Stuff]]` ×2 — ambiguous
- [done] LEAVE `Kanban/PhD.md` `[[Understand alternative distributions]]` — target never written

## Phase 9 — Index rebuild

- [done] INDEX root `index.md`
- [done] INDEX `Dev/index.md`  (5 group sections, each with a `Place here:` line)
- [done] INDEX `AI/index.md`
- [done] INDEX `Quick note/index.md`
- [done] KEEP `Dev/languages/Kotlin/index.md`, `Dev/frontend/Skia-React-Native/index.md`,
        `Dev/architecture/Monolithic decomposition/index.md` — accurate, pointed to not regenerated
- [done] MANIFEST regenerate `.wiki-index/manifest.json`

## Phase 10 — Report


---

## Completion record — 2026-08-02

All operations completed. No `[failed]` operations.

### Verification results

- **Content preservation**: 180 files on disk are byte-identical to a blob in `93c89c7`. Every move
  and rename preserved content exactly.
- **Files whose content differs from HEAD — 10, all accounted for**: `AGENTS.md` (new); `index.md`,
  `Dev/index.md`, `AI/index.md` (index rebuild); `Dev/languages/Kotlin/index.md`,
  `Dev/frontend/Skia-React-Native/index.md`, `Dev/architecture/Monolithic decomposition/index.md`
  (path rewrites); `Banking/mifid-wphg-banking-notes.md` (planned TOC repair); `Kanban/PhD.md`
  (planned link rewrite); `Dev/practices/How to Read and Understand Code Quickly.md` (the merge).
  Note prose changed in exactly two files, both planned.
- **Link graph**: 1 resolved note-to-note wikilink (`Kanban/PhD.md` -> `Reorganise plan`), the
  rewritten one. Broken links unchanged at the 2 known deliberate ones. No new breakage.
- **Index**: every entry resolves to a real file; every note is covered by an index line.
- **Protected paths intact**: `Dairy/`, `Excalidraw/`, `Paper/Archive/`, `_utils/`, `Dev/LLM/src/`.
- **Counts**: 149 -> 147 markdown files (3 trashed, `AGENTS.md` added). 137 content notes.

### Deviations from the plan

1. **The merge** — see the phase 3 entry above. Planned as "append 93 unique lines"; reading both
   files showed the target is a strict superset and the 93 lines were formatting artifacts. One
   genuinely missing sentence was carried over instead of ~340 lines of inferior duplicate.
2. **The three leaf indexes were rewritten, not merely "preserved and pointed to"** as the plan said.
   Their descriptions are preserved verbatim, but their file *paths* all changed when their parent
   folders moved, and several Kotlin/Skia filenames were normalized — so leaving them untouched would
   have left every entry in them dead. Paths and filenames updated; no description reworded.
3. **`Dev/frontend/Skia-React-Native/index.md` gained one entry** — note `013 Skia with
   react-native-gesture-handler and react-native-reanimated.md`. It had no `.md` extension before this
   run, so no previous index pass could see it.
4. **Root index count line** says 79 Dev notes, not the plan's 78. The plan's figure was off by one;
   79 is the counted value.

### Not done, by design

- 2 broken wikilinks left in place (`[[Stuff]]` x2, `[[Understand alternative distributions]]`).
- Tracked secrets (`Dev/languages/Python/key.txt`, `.tmp/.env.zip`) and tracked junk (`.DS_Store`,
  `*.pyc`, `*.log`) reported to the user, not actioned.
- Nothing committed. The working tree is left dirty for the user to review and commit.
