# Placement rules


**This ladder is how a placement is carried out, not how it is decided.** The reasoning
that picks the destination — knowledge identity, primary ownership, split/merge/extend, whether a
folder is earned, the future-growth test — is in `references/knowledge-organization.md`, and it
runs first. Where the two appear to disagree, that file decides.

How to decide where incoming material goes. Apply in order and stop at the first rule that fits —
the order encodes a bias toward **enriching what exists** over **adding more files**, because a
vault degrades by fragmentation long before it degrades by long notes.

The user has said explicitly they don't want to be asked when it isn't necessary. Rule 5 is the last
resort, not the safe default.

<!-- profile-hook: placement-classify -->

## Rule 0 — the delta pass: decide what is actually new

**Runs before rules 1–5, per claim, never per file.** Filenames, file format and wording are
irrelevant: the same material dropped again in a different shape must produce no second copy.

With the destination note open (and its one-hop neighbourhood from the graph), give every claim in
the unit one of four verdicts:

| Verdict | Test | What happens |
|---|---|---|
| **present** | the note already states this, in any wording | dropped, and counted in the report |
| **sharper** | same subject, more specific value — "15,000 EUR" where the note says "a threshold" | the existing line is refined, per the in-place edit rules |
| **conflicting** | same subject, incompatible value | `references/conflict-detection.md`, never a silent add |
| **new** | nothing in the vault states it | written |

- **Substance, not string.** A reworded, reordered or re-formatted claim is `present`. A claim with
  a different value is never `present`, however similar it reads.
- **Bounded cost.** The comparison uses notes this run already opened; a unit whose claims found no
  destination gets **one** `.rag` query, not one per claim.
- **The counts are reported**: `47 claims — 31 present, 12 new, 3 sharper, 1 conflicting`. A re-drop
  of an already-filed inbox reports `0 new` and writes nothing, which is the outcome this rule
  exists to produce.
- **`present` is the only verdict that drops anything**, and it is the one verdict that requires
  having read the line that makes it true. Assuming coverage from a heading, an index entry or a
  filename is not a delta pass (`references/ingest-sources.md` → Lose nothing).

## Rule 1 — Merge into an existing section

**When**: a note already covers this topic *and* has a section the material belongs under.

Append into that section. Keep its existing structure — if it's a bullet list, add bullets; if it's
prose, add a paragraph. Never reflow or rewrite what's already there.

If the material overlaps what the section already says, add only the genuinely new parts, and say in
the report what was already covered. **"Already covered" is decided per claim, by reading the line
in the note** — never from the heading, the index entry or a general sense that the topic is there.
A claim more specific than what the note says is new, and the overlap check is never a shortcut for
condensing the material (`references/ingest-sources.md` → Lose nothing).

## Rule 2 — Add a new section to an existing note

**When**: a note clearly owns the topic, but nothing in it covers this specific aspect.

Add an H2 (or the note's own heading level for peers). Place it where its topic belongs relative to
the existing sections — a step in a process goes in sequence, a new category goes next to related
categories. Appending at the end is a choice to justify, not a default.

If the note would exceed ~400 lines, still add it, and flag the note as a split candidate in the
report. Don't pre-emptively split someone's note as a side effect of filing a paragraph.

<!-- profile-hook: placement-folder -->

## Rule 3 — Create a new note in a clear folder

**When**: no existing note covers the topic, but a folder's `Place here:` line fits it.

Before creating, **check for near-duplicates**: search the vault for the material's key entities and
terms — canonical and variant forms both, per the glossary — not just the topic phrase. A note under
a name you didn't predict is the most common cause of an unnecessary new file. If one turns up, go
back to rule 1 or 2. When the vault has a `.rag` index, this is the search worth spending it on
(`references/rag.md` → When to use it): a duplicate phrased in different words is exactly what grep
cannot find.

The new note follows the vault's detected conventions: naming style, frontmatter fields, link style,
and the structure its shape deserves (`references/note-shaping.md`).
Link it from the most closely related existing note — an unlinked new note is an orphan the moment
it's written.

## Rule 4 — Create a new folder

**When**: the material's topic has no home at all, and forcing it into the nearest folder would
make that folder's `Place here:` line untrue.

This is a real outcome, not a failure. Create the folder at the **shallowest sensible level** — a
new top-level folder for a genuinely new domain, a subfolder when it's a subdivision of an existing
one. Give it an index entry with a `Place here:` line immediately, then apply rule 3 inside it.

Flag it prominently in the report: the user should know their vault structure changed.

**In a batch, the evidence is the cluster, not the item.** A single scrap almost never justifies a
folder; three or more units sharing a topic the vault has no home for usually does — and it may
warrant several notes inside it rather than one. That judgment is made once for the whole batch
before any write, per `references/modes/intake.md` → Deciding a new folder. A lone unit with no
home still goes to the best-fit folder and gets flagged, exactly as it would outside a batch.

## Rule 5 — Ask

**When**, and only when, both of these hold:

- Two or more destinations are **equally** plausible, and
- The choice is **materially different** — different folders in different domains, or merging into
  an existing note versus creating a new one, such that a wrong guess is annoying to undo

Not a reason to ask: a close call between two files in the same folder; uncertainty about the exact
filename; not knowing which section of a note is best. Decide those, and say what you decided.

When you do ask, ask once, with the two options named and the reason each is plausible. Don't ask
open-endedly ("where should this go?").

## Cross-referencing a strong secondary fit

After the primary placement is decided — by rule 1, 2, 3, 4, an answer to rule 5's question, or a
destination the user named outright — look at the other candidates from the update workflow's
step-3 shortlist (`references/modes/update.md`). Any candidate that was itself a *plausible primary
destination* (its folder's `Place here:` line genuinely fits the material — the rule 3/4 bar, not a
loose tag or keyword match) gets a pointer back to where the material actually landed, filed in a
`see-also.md` at that folder's root.

This is what keeps "the user already said where it goes" from losing the other genuinely relevant
location: the material is written once, and every other strong-fit folder gets a one-line reference
to it instead of a copy.

**What counts** — a folder qualifies only if:
- It surfaced in the step-3 shortlist (never go hunting beyond it for this), and
- It's a different top-level domain from where the material landed — not a sibling section of the
  *same* note or folder, which rules 1/2 already handle, and
- Its match is substantive, not a coincidental tag overlap — the same bar rule 3 uses to decide a
  folder deserves a new note in the first place.

Cap at 2 secondary folders. If more than 2 qualify, keep the 2 strongest and drop the rest rather
than scattering references thin.

**What goes in `see-also.md`** — one bullet per cross-reference: a link to the note in the vault's
link style (`references/vaults/*.md` → Links), plus a short reason, nothing else:

```
- [[micro-frontend-loading]] — how coba's Themenblock micro-frontend is loaded and mounted, filed under banking/coba
```

Never the material itself, never a summary long enough to make reading the actual note optional —
that's a duplicate wearing a different name, exactly what "dedupe before creating" already forbids.

**Idempotency**: before adding a line, check whether an equivalent one (same target note) already
exists in that `see-also.md`. If it does, leave it — don't add a second line or rewrite the reason.

**First time a folder gets a `see-also.md`**: create it with just that bullet, and add its one line
to the folder's index entry (`references/index-format.md` → Cross-reference files). Every later
addition to an existing `see-also.md` is an append, same as any other note edit — existing bullets
are never reordered or reworded as a side effect.

## Writing in the vault's own words

Whatever rule fired, the text that lands uses the vault's **canonical terms** — the glossary's, not
the material's, with variants normalized under the rules and limits in `references/glossary.md`.
A note filed with the wrong spelling of a term is a note the next search won't find.

The form that text takes — heading level, list style, table or diagram, how a new note is
structured — is `references/note-shaping.md`, decided before the write, not during it.

## Section-level placement

Rules 1 and 2 depend on knowing a note's sections. The index's H2 sub-bullets give you candidates,
but confirm against the file — sub-bullets go stale between refreshes.

Choosing between two sections in the same note: prefer the one whose existing content the material
would sit alongside naturally, not the one whose *title* matches most literally.

## Handling contradictions

Material that contradicts what a note says is **never** a silent overwrite.

Keep the existing text. Beneath it, append a correction in the vault's date format:

```
> Correction 2026-08-01: the threshold is 15,000 EUR, not 10,000 (per the escalation matrix screenshot).
```

Then flag it in the report so the user can reconcile it themselves. The exception is when the user
explicitly says the new material supersedes the old — then replace, and say what was replaced.

## Splitting incoming material

<!-- profile-hook: split-decompose -->

Material covering two unrelated topics gets **split** and placed separately. This is normal for
screenshots and pasted chunks. Place each part by these same rules, and report both destinations.

Don't split material that's genuinely one topic just because it's long.

## What never happens

- Creating a note that duplicates an existing one because the search wasn't thorough enough
- Rewriting, reflowing, or reordering existing content as a side effect of adding to it
- Deleting anything
- Moving an existing note (that's an `audit` finding, reported and left to the user)
- Adding content the source material didn't contain, to "round out" a note
