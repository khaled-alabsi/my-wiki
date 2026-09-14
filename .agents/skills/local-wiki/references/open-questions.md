# Answering the open questions in incoming material

Material rarely arrives complete. It carries a `?`, a `TBD`, a "not sure which team owns this", or
one of the uncertainty markers this skill itself writes when a screenshot is cut off. The vault very
often already answers those — nobody ever goes and looks.

This file is that lookup: **detect what the material left open, answer it from the vault, and close
it.** It runs inside `update` and `intake`, between reading the candidate notes and writing.

## 1. Detect

Scan the intake summary and the raw material for:

- A line ending in `?`, or containing `??`
- `TODO`, `TBD`, `FIXME`, `open:`, `unclear`, `verify`, `check`, `which one`, `not sure`
- The skill's own uncertainty markers, per `references/ingest-sources.md`:
  `- Threshold: 15,000 EUR (screenshot cut off — verify)`
- A placeholder standing in for a value: `X`, `???`, `<name>`, an empty table cell in an otherwise
  filled row

Rhetorical questions and section headings phrased as questions ("## Why does this matter?") are
**not** open questions. The test: would a factual answer change what the note says? If not, skip it.

Record each as: the question, what kind of answer would close it (a value, a name, a step, a
yes/no), and the terms to search on — expanded through the glossary first, so a question about `PEP`
searches for `PIP` too (`references/glossary.md`).

## 2. Budget

**At most 5 questions per intake unit.** More than that means the material is a draft, not a note —
resolve the 5 most answerable, leave the rest open, and say so in the report.

Answering is retrieval, and retrieval is the expensive part of filing. A question that needs three
searches and two file reads to resolve is worth it; ten of them are not.

## 3. Resolve, in cost order

Stop at the first step that answers it.

1. **Glossary** — a "what does X mean" question is answered by the index itself.
2. **The index** — `Place here:` and `covers` lines, then H2 sub-bullets, then read that section.
   The candidate notes from the update workflow's step 4 are already open; check them first.
3. **`.rag` search**, when the vault has one (`references/rag.md`). This is the case it is best at:
   a question phrased in the user's words against notes phrased in someone else's. Batch the run's
   questions into few searches. Then **open the cited file** — a passage is a pointer, never the
   answer itself.
4. **Direct grep** for the expanded terms.

## 4. Close it

An answered question is **written in and closed** — the marker goes, the answer stays, and the
source travels with it:

```
before:  - Escalation threshold: ? (screenshot cut off — verify)
after:   - Escalation threshold: 15,000 EUR — [[escalation-matrix]] ## Limits (answered 2026-08-03)
```

```
before:  - TBD: who signs off the target market check?
after:   - Sign-off on the target market check: the advisor's team lead — [[advisory-roles]] (answered 2026-08-03)
```

Rules for the rewrite:

- **The subject survives.** The question's topic becomes the lead-in, so the note never loses what
  was being asked — only the fact that it was unanswered.
- Link and date in the **vault's own style**, from `## Conventions`. A markdown-link vault gets
  `[advisory-roles](../advisory-roles.md)`, not a wikilink.
- Cite the **section** when the source note has one.
- The answer is stated in the source's own terms. Don't expand a one-word answer into a paragraph.

## 5. What must never happen

- **Only a vault-sourced answer closes a question.** Not general knowledge, not an inference from
  the material itself, not a plausible default. Unanswered stays open, verbatim, and is listed in
  the report.
- **A partial answer does not close it.** Write what the vault gave, keep the question open for the
  rest:
  `- Escalation threshold: 15,000 EUR for retail — [[escalation-matrix]] (answered 2026-08-03); professional-client threshold still open`
- **Two notes disagreeing does not close it.** The question stays open, both notes are cited in the
  report as a conflict, and nothing is picked as the winner.
- **Never invent the question either.** If the material is merely terse, that is not an open
  question — don't manufacture one to answer.

## Questions already sitting in existing notes

A note the task **opened** may have its own open question closed the same way, when the vault answers
it. This is deliberate — the answer was found anyway, and leaving a known-answered `TBD` in place is
worse than the edit.

Limits, same as term normalization (`references/glossary.md` → Normalization):

- Only notes this task actually read. Never a file seen in a scan and not opened.
- Never inside a code fence.
- A sweep of every open question in the vault is a `refactor` job, not a side effect of filing.
- Every closure is reported, with its path.

## Reporting

Its own block, after the placement result:

```
Questions answered (2):
- "escalation threshold?" -> 15,000 EUR — Banking/escalation-matrix.md ## Limits
- "who signs off?" -> the advisor's team lead — Banking/advisory-roles.md

Left open (1):
- "does this apply to professional clients?" — nothing in the vault covers it
```

Left-open questions are the useful half of this report: they are exactly what the user should either
answer themselves or go find out. Never omit them because they look like a failure.
