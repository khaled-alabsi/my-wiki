# Shaping material to fit where it's going

Deciding *where* material goes is half the job. The other half is deciding *what it should look
like* once it's there — and it is the half that decides whether the vault reads as one person's
notes or as a scrapbook of pastes.

This step runs after the destination is settled and before anything is written. It answers two
questions in order:

1. **What shape is this material, and what structure does that shape deserve?**
2. **What does the destination already look like, and what must bend to fit it?**

The second outranks the first, always.

## 1. Shape → structure

The intake summary's `Shape` field (`references/ingest-sources.md`) picks the starting structure:

| Shape | Becomes |
|---|---|
| **Process / workflow** | Numbered steps, one action per step, plus an inline mermaid `flowchart TD` |
| **Decision tree** | Steps plus a mermaid `flowchart TD` with the conditions as diamonds |
| **Lifecycle / states** | A state list plus `stateDiagram-v2` |
| **Exchange between actors** | `sequenceDiagram` alongside the prose |
| **Reference / list** | Bullets, or a table when every item shares the same 2–4 fields |
| **Definition** | Term, expansion, one-paragraph meaning, an example if the source gave one — **and a glossary entry** (`references/glossary.md`) |
| **Decision (a choice made)** | Context → Decision → Consequence, dated |
| **Observation / finding** | A dated bullet under the note's running list |
| **Comparison** | A table, one row per option, one column per criterion |
| **Q&A** | Resolved statements, not a transcript (`references/open-questions.md`) |
| **Mixed** | Split it and shape each part separately (`references/placement-rules.md` → Splitting) |

Diagram rules — which diagram, how big, and the hard "only what the material stated" limit — live in
`references/ingest-sources.md` → Diagrams. Don't restate them; don't contradict them.

## 2. Destination fit outranks the ideal shape

Material joining an existing note **adopts that note's form**:

- **Heading depth** — a note whose sections are H2 gets an H2, even if the material arrived with an
  H1 and three H3s. Re-level the whole block, keeping its internal hierarchy intact.
- **List style** — a note written in bullets does not get three paragraphs of prose appended. A note
  written in prose does not get a bullet dump. Convert; don't paste and hope.
- **Density** — match the surrounding notes' level of detail. A vault of one-line facts doesn't want
  a 40-line transcription of the same fact.
- **Tense and person** — imperative step lists stay imperative; "we decided" notes stay first
  person.
- **Terminology** — use the vault's canonical glossary term, normalizing the material's variants
  (`references/glossary.md` → Normalization). This is where `PEP` becomes `PIP`.
- **Language** — a German note stays German; don't translate a section into English because the
  source was English. Say in the report that the material was kept in its source language if you
  couldn't match.

**The host note is never reflowed to accommodate the newcomer.** If the material genuinely doesn't
fit the note's form, that's evidence the placement is wrong — go back to
`references/placement-rules.md`, don't rewrite someone's note around a paragraph.

<!-- profile-hook: note-shape -->

## 3. New notes

A new note gets the structure its shape implies, built to the vault's detected conventions
(naming, frontmatter, link style, date format from the index's `## Conventions`):

```
# <Title matching the filename>

<One-line statement of what this note is. Not a preamble — the fact itself.>

## <Section per the shape table>
...

## See also
- [target market check](../regulatory/mifid.md#target-market) — why it matters here
```

- The H1 matches the filename, when the vault does that.
- **Sections only where the material fills them.** An empty `## Open questions` heading is worse
  than no heading. Three facts do not need four sections.
- A new note always gets linked from its closest existing relative — an unlinked note is an orphan
  the moment it's written (`references/placement-rules.md` → rule 3).
- **`## See also` links are plain markdown, never wrapped in backticks.** `` `[text](path.md)` ``
  renders as literal text, not a clickable link — see `references/linking.md` → Rendering. Write
  the link itself, not a code span that looks like one.

## 4. Reasoning to do before writing, in one pass

- Does the destination note already have a section whose **form** this material should copy? Copy it.
- Does the material repeat something the destination already says? Keep only what's genuinely new
  (`references/placement-rules.md` → rule 1).
- Does it contain values, names or steps that belong in a **table** the note already has? Add rows;
  don't start a second table.
- Does it introduce a term? Glossary entry, same run.
- Does it leave something open? `references/open-questions.md`, same run.
- Is it a process the note already diagrams? Update that diagram in the same edit — a step list and
  its diagram disagreeing is worse than no diagram.

## What never happens

- **Pasting the source's structure unchanged** when it fights the destination. A web page's H1/H2/H3
  ladder is the page's structure, not the note's.
- **Inventing sections the material doesn't fill**, to make the note look complete.
- **Adding content the source didn't contain** to round out a shape — a five-step process with four
  steps stated stays four steps, with the gap marked.
- **Splitting a coherent note** because it got long. That's an `audit` finding, reported, not done as
  a side effect of filing.
- **Adding a diagram to something that isn't a process.** Definitions, reference lists and
  observations get none.
- **Rewriting, reordering or reflowing existing content** to make room. Additive only, except the two
  bounded exceptions in `SKILL.md` → Constitution.
