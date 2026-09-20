# 04 — Operations (resume record)

Accepted 2026-09-20. D1 = new `Dev/tools/`. D2 = fold in, then trash.
Git preflight: repo is dirty **outside the scope** (`.agents/skills/local-wiki/`, `.obsidian/`,
`.gitignore`, `_utils/*.log`). No `Dev/` path is uncommitted. This skill runs no git command in this
vault, so no undo sha was recorded; recovery is `.wiki/.trash/` plus this record.

| # | Phase | Op | Source → Target | State |
|---|---|---|---|---|
| 1 | gate | hash-verify 16 folders against the grouped layout | — | [done] |
| 2 | 1 | mkdir | `Dev/tools/` | [done] |
| 3 | 3 | merge | 28 uncarried lines of `Dev/Read/Untitled.md` → `Dev/practices/How to Read and Understand Code Quickly.md` | [done] |
| 4 | 3 | verify merge | target contains all 28 lines | [done] |
| 5 | 4 | move+case-fix | `Dev/Dev tools/Vs code configs.md` → `Dev/tools/VS Code configs.md` | [done] |
| 6 | 5 | link rewrite | vault-wide — expected no-op | [done] |
| 7 | 6 | trash | `Dev/Read/Untitled.md` (after op 4 passes) | [done] |
| 8 | 7 | trash | `Dev/Architect/` | [done] |
| 9 | 7 | trash | `Dev/JS/` | [done] |
| 10 | 7 | trash | `Dev/Java/` | [done] |
| 11 | 7 | trash | `Dev/Kotlin/` | [done] |
| 12 | 7 | trash | `Dev/Microfrontend/` | [done] |
| 13 | 7 | trash | `Dev/Monolithic decomposition/` | [done] |
| 14 | 7 | trash | `Dev/Python/` | [done] |
| 15 | 7 | trash | `Dev/React JS/` | [done] |
| 16 | 7 | trash | `Dev/React-Native/` | [done] |
| 17 | 7 | trash | `Dev/Skia-React-Native/` | [done] |
| 18 | 7 | trash | `Dev/Spec/` | [done] |
| 19 | 7 | trash | `Dev/TeamCity/` | [done] |
| 20 | 7 | trash | `Dev/elastic stack/` | [done] |
| 21 | 7 | trash | `Dev/openshift/` | [done] |
| 22 | 7 | trash | `Dev/redux/` | [done] |
| 23 | 7 | trash | `Dev/wk/` | [done] |
| 24 | 7 | trash | `Dev/Dev tools/` (emptied), `Dev/Read/` (emptied) | [done] |
| 25 | 8 | broken links | the 2 known deliberate ones — left, per profile | [done] |
| 26 | 9 | index | root `index.md`: drop `Dev/wk/`, fix note counts | [done] |
| 27 | 9 | index | `Dev/index.md`: add `Dev/tools/`, note the appended section | [done] |
| 28 | 10 | rag | `.rag/bin/rag update --quiet` | [done] |
