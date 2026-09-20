# 02 — `dev-grouped-layout`

Owns F5.

## Read for this plan
The four `index.md` files, the folder listings, and the three loose `Dev/languages/` notes.

## Operations
**None proposed.** The grouped layout is the product of the 2026-08-02 refactor and is coherent:

- `architecture/` 2 loose notes + `Monolithic decomposition/` (11 notes, own index) + `resources/`
- `frontend/` 2 loose notes + `React JS/` (3) + `React-Native/` (5) + `Skia-React-Native/` (18, own index)
- `infra/` `TeamCity/` (4) + `elastic stack/` (5) + `openshift/` (2) + `security/` (2)
- `languages/` 3 loose notes + `Kotlin/` (16, own index) + `Python/` (1 note + scratch code)
- `practices/` 1 note

**F5 — deliberately not changed.** Splitting `java-functional-interfaces.md` and
`java-ee-monolith-knowledge-gaps-book.md` into `languages/Java/`, and `javascript-loops.md` into
`languages/JavaScript/`, would make the folder symmetrical with `Kotlin/` and `Python/`. It is not
proposed: `languages/` holds 5 entries against the profile's ~15 regrouping threshold, a one-note
`JavaScript/` is not an earned folder, and `Python/` exists mainly to hold scratch code rather than
as a per-language rule. The mode's constitution says refactor fixes what is broken, not what is
merely asymmetrical. Available on request.

**`Skia-React-Native/` at 18 entries** is over the ~15 threshold but is a deliberate `000`–`015`
curriculum with its own index. The profile rules numbered sequences owner decisions. Unchanged.

## Destinations for unit 1's orphans
- A VS Code macOS configuration note has no fitting home in the grouped layout — `practices/` is
  language- and framework-independent engineering practice, not machine setup. Hence D1's
  recommendation of `Quick note/`.
- The code-reading capture's home is `practices/`, where its shaped version already lives.
