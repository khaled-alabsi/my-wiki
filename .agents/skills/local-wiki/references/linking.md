# Relation linking — wiring a note to the notes near it

Every write connects what it wrote to what it relates to, in both directions. Not as a separate
step the user asks for: it is part of what writing to the vault means. A vault that grows note by
note without this grows *disconnected* — navigating by topic means searching again every time, and
there is no graph to render because nothing ever recorded the edges.

This is **note- and section-level**. It sits alongside, and does not replace, the folder-level
`see-also.md` pointers in `references/placement-rules.md` → Cross-referencing a strong secondary
fit. Both feed one graph.

## The bar: a link needs a stated reason

Without a bar, every note links every note and the graph is noise — which is worse than no graph,
because it looks like information.

**A relation is a link when you can say, in one line, why a reader following it would be better
off.** A shared keyword is not a relation. A term that appears in both notes is not a relation. If
the reason won't write, there is no link.

Cap: **~5 new inline links per note per run**. Hitting the cap usually means the material belonged
somewhere else, or belongs split.

## Rendering: a link is never wrapped in backticks

`` `[text](path.md)` `` is not a link — the backticks make it an inline code span, and every
markdown renderer prints it as literal text. Clicking it does nothing. This holds everywhere a link
is written in this skill: an inline mention, a `## Related` back-edge, a `## See also` entry
(`references/note-shaping.md`), a `see-also.md` bullet, an index line, a README line — all plain
`[text](path.md)`, with nothing around the brackets.

Backticks stay reserved for what they actually mean: a bare filename or path mentioned in prose with
no link attached (`` `config.json` ``), or a code span. The moment brackets and parentheses turn that
mention into a link, the backticks come off.

Before finishing a write that added a link, look at the raw line: if it starts with a backtick, it
is broken, not stylistic.

## 1. Inline links

When a write mentions a topic the vault already covers, the mention becomes a link — anchored to a
section when the target has a heading that matches:

```markdown
The advisor completes a [target market check](../regulatory/mifid.md#target-market) before
recommending the product.
```

**This is a bounded in-place edit to existing note text** — the third one this skill permits, and it
inherits exactly the limits of the other two (`SKILL.md` → Constitution):

- Only in notes **the running task actually opened**. Never a file seen in a scan.
- Never inside a code fence, an inline `` `code span` ``, a URL, a file path, a frontmatter value,
  or a filename.
- **First occurrence per note only.** Not every mention of the word — a note that says "onboarding"
  nine times gets one link, on the first.
- Never inside an existing link.
- Every one is listed in the report.

The link text is the words already in the sentence. Never reword a sentence to accommodate a link;
if the sentence doesn't contain a natural anchor, use `## Related` instead.

## 2. The `## Related` back-edge

When a run links A → B, **B gets a line back to A**, with the reason:

```markdown
## Related
- [onboarding](../processes/onboarding.md#compliance-checks) — where the target market check is performed
```

The back-edge is what makes the graph traversable both ways with no build step, and it is what turns
"what links here?" into a question the notes themselves answer.

- **Position**: `## Related` is the last section of a note. Create it if absent.
- **Idempotent**: a line already pointing at that target is left alone — never duplicated, never
  reworded. Check before appending.
- **One line per target**, newest last.
- Adding a `## Related` line is an append, so it is ordinary additive editing — not one of the
  bounded exceptions.

### A `## Related` line may declare what kind of relation it is

```markdown
## Related
- requires :: [sca](../payments/sca.md) — PSD2 art. 97 mandates strong customer authentication
- superseded-by :: [psd3](psd3.md) — from 2026-01, ZAG transposition pending
- [onboarding](../processes/onboarding.md#compliance-checks) — untyped, and that is fine
```

`type ::` before the link, from a closed vocabulary: `relates-to` (the default), `part-of`,
`requires`, `regulates`, `implements`, `supersedes`, `superseded-by`, `contradicts`, `example-of`,
`defined-in`. Full rules in `references/graph.md`.

- **The type is optional and the reason is not.** A type says which verb; only the reason says why,
  and the bar above is unchanged. `requires :: [x](x.md)` with no reason does not get written.
- **Type it when the verb is genuinely known** — a regulation that mandates a control, a version
  that replaces another, a step that is part of a process. When the honest answer is "these are
  related", leave it untyped rather than picking a verb that overstates it.
- **Only here and in `see-also.md`.** An inline mention in prose is never typed.
- A type outside the vocabulary is recorded as `relates-to` and reported by the scan, so a typo
  costs a report line, not an edge.

<!-- profile-hook: relation-types -->

## 3. Anchors are GitHub-style slugs

Lowercase, drop everything that is not a word character, space or hyphen, then spaces to hyphens.

| Heading | Anchor |
|---|---|
| `## Target Market (MiFID)` | `#target-market-mifid` |
| `## Who's responsible?` | `#whos-responsible` |
| `## Step 1 — intake` | `#step-1-intake` |

**Only anchor to a heading you have actually seen** in the file you opened. An invented anchor is a
broken link that renders fine and fails silently — the single most common way this goes wrong.

`scripts/scan_vault.py` records every note's real slugs, and `graph.py query --broken` finds the
ones that have died since. When a heading is renamed, its inbound anchors break; that is a
`refresh`/`audit` finding, and fixing it is an ordinary edit.

## 4. Finding what to link to

Three sources, cheapest first:

1. **The step-3 shortlist you already built.** Candidates that lost the placement decision are the
   best link targets — they were relevant enough to consider.
2. **`graph.py query --neighbors <destination> --depth 2 --json --limit 10`** — what is already
   connected to where the material landed. Relations cluster; the note you want is usually one hop
   from the note you wrote. Add `--types requires,regulates,part-of` to follow only strong
   relations when the neighbourhood is crowded.
3. **`graph.py suggest --path <the note> -k 5`** — candidates nobody has linked yet, ranked from the
   vault's own `.rag` embeddings, or shared-term overlap when there is no index.

```bash
python3 scripts/graph.py suggest --path processes/onboarding.md -k 5 --vault <vault>
```

**A suggestion is never an answer.** It is ranked text similarity, and text similarity is not a
relation — two notes can discuss the same term for unrelated reasons. Open the candidate, decide
whether the relation is real, and write the reason yourself. The tool cannot produce the reason, and
the reason is the bar.

## 5. Recording the edges

After the writes, once per run:

```bash
python3 scripts/graph.py scan --since-manifest --vault <vault>
```

The graph is a **cache**. The markdown is the source of truth, and `scan --full` rebuilds everything
from the files at any time. Never hand-write an edge into `.wiki/graph.sqlite`, and never read that
file directly — `query` answers questions, and it is bounded where the raw store is not.

## What not to link

- **A note that merely uses the same word.** The standing test: could you write the reason line?
- **Two notes in the same section of the same file** — they are already adjacent.
- **The index, `README.md`** — navigation files link outward, not inward.
  `README.md` linking every folder is deliberate and set at `init`; nothing links back to
  it.
- **`.wiki/todos_validations.md`, `.wiki/wiki_gaps.md`, `.wiki/` files** — tracking artifacts, not content.
- **A note you did not open.** You cannot know its headings, so you cannot anchor honestly, and you
  cannot write a truthful reason.

## Reporting

Its own block, after the result, omitted entirely when empty:

```
Links added (3):
- processes/onboarding.md -> regulatory/mifid.md#target-market — the check this step performs
- regulatory/mifid.md ## Related -> processes/onboarding.md — back-edge
- processes/onboarding.md ## Related -> regulatory/escalation.md — where breaches escalate
```

Back-edges are listed too. A user should be able to see every note this run touched, and a
`## Related` line added to a note they didn't ask about is exactly the kind of edit that must not be
silent.

## Edge cases

- **The target has no matching heading** — link the file without an anchor. Better an honest file
  link than a guessed anchor.
- **The relation is genuinely one-way** — a glossary-style definition note that fifty notes
  reference should not carry fifty back-edges. Skip the back-edge and say so in the report;
  `graph.py query --oneway` will list it, and that is the correct answer for a hub.
- **The note already has 20 `## Related` lines** — it is a hub, and probably wants splitting. Add
  the link, flag it for `audit`.
- **Both notes are new in the same run** — link them to each other normally; the back-edge is
  written in the same pass.
- **A link would point at a note the user has not validated** — link it anyway, and say so. An
  unverified note is still the vault's best answer on that topic.
- **The vault has no `.rag` index yet** — `suggest` falls back to shared-term overlap and says so.
  Weight its output a little lower; the reason-line bar is unchanged.
