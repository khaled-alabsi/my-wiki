# Conflict detection — before adding, not after

Before new material is written, check whether it **contradicts** something the vault already says.
Not whether it duplicates it — that is dedupe, a separate and older rule — but whether both
statements cannot be true at once.

Applies to `update` and `intake`, in both `wiki` and the generated local skill.

## Contradiction is not near-duplication

| | What it is | What happens |
|---|---|---|
| **Duplicate** | The same fact, said again | Merge into the existing note. Never add a second copy. (`references/placement-rules.md`) |
| **Elaboration** | New detail that the existing note doesn't cover | Ordinary additive placement |
| **Update over time** | The old statement was true then; this is true now | A contradiction — and usually a **supersession**, not an override. Say which is newer, and offer to date both |
| **Contradiction** | Both cannot be true | **Stop and ask.** This file |

Examples of the real thing:

- The vault says the escalation threshold is 10,000 EUR; the material says 15,000 EUR.
- The vault says the check runs before the recommendation; the material says after.
- The vault's glossary defines `TaMrA` as Target Market Assessment; the material defines it as
  something else.

Not the real thing:

- The vault says a process has four steps; the material describes three of them. That is partial
  coverage, not disagreement.
- Different wording for the same claim.
- A number the vault doesn't state at all.

**When in doubt, it is not a conflict.** Asking about every superficially different phrasing trains
the user to say "override" without reading, which is worse than not asking.

## Where the check happens

After the candidate notes have been **read** — you cannot detect a contradiction against a file you
only saw in the index — and **before** anything is written.

In `update` that is step 5. In `intake` it is per unit, after the batch plan is settled.

The check is scoped to what the task actually opened, plus what the glossary says. Do not sweep the
vault hunting for contradictions; that is `audit`'s job.

## When one is found

**Stop before the write.** Say plainly:

- what is being added,
- what it contradicts, with the file and section,
- and which is newer, if the notes carry dates.

Then ask which way to go. Three answers:

### Supersede — the old statement was right, and then the world changed

**Offer this first when the disagreement is about time**, not about correctness: a regulation
replaced, an API version bumped, a threshold that genuinely changed on a date. Overriding here
destroys history that was true; ignoring leaves two live statements with no relationship between
them. Neither is what happened.

Nothing is deleted. The old note keeps what it says and gains a closing date; the new one opens
where the old one ends; a typed relation records the succession:

```yaml
# in the old note's frontmatter
valid_until: 2026-01-01
```

```markdown
## Related
- superseded-by :: [psd3](psd3.md) — replaced from 2026-01
```

…and the back-edge, `supersedes ::`, on the new note, whose own `valid_from` is that date.

After this, `graph.py query --neighbors <note> --as-of 2024-06-01` still answers what the vault said
in 2024, and today's answer is the current one. This is the resolution most banking and
system-documentation conflicts actually want (`references/graph.md` → Time).

Report it as a supersession, naming both notes and the date. It edits an existing note's frontmatter
and appends a relation — it never changes what the old note *asserts*.

### Override — the new material is right

The agent **fixes the conflicting existing content in the same run**. Not an appended correction
line: the existing statement is wrong and is corrected, because leaving both in place is how a vault
becomes untrustworthy.

- Edit the existing text minimally — the claim, not the paragraph around it.
- Record the change in the note's provenance (`last_changed`, `last_changed_by`).
- Report it as a content edit, prominently. This is the one path in this skill that changes what an
  existing note *asserts*, and it must never be quiet.

### Ignore — leave the existing content alone

Nothing existing changes. The new material is still filed, and the incident is logged to
`.wiki/conflicts_ignored.md`:

```markdown
## 2026-08-13 — escalation threshold
- **Adding**: "the escalation threshold is 15,000 EUR" (into processes/escalation.md)
- **Conflicts with**: regulatory/limits.md ## Thresholds — "10,000 EUR"
- **Decision**: ignore — user said the regulatory note is authoritative and the newer figure is a
  draft
- **By**: alice@example.com
```

Append-only, no checkboxes. Nobody "resolves" a past incident — it is a record of a decision, not a
task. It lives in `.wiki/` alongside the config and contributors files, and it is **committed**:
every contributor should be able to see that a disagreement was noticed and deliberately left.

## The hard rule

**No content is written while a real conflict is unresolved.** Not "written and flagged", not
"written with a note". The user is asked first, every time.

This is the one place this skill blocks on a question rather than deciding — justified because both
alternatives silently corrupt something: writing the new claim makes the vault self-contradictory,
and dropping it loses information the user just supplied.

## How this relates to the correction rule

The Constitution already says contradicting material becomes a dated correction line rather than a
silent overwrite. That rule still holds — it is what happens **after** the user chooses, and it is
no longer the automatic default:

- Before: contradiction → append a correction line, always.
- Now: contradiction → ask → override (fix it) or ignore (log it).

The correction-line shape remains the right form for an "override" that is genuinely an update over
time rather than a correction of an error, when both the old and new values are worth keeping.

## Reporting

Its own block, omitted when empty:

```
Conflict found (1):
- Adding "escalation threshold 15,000 EUR" contradicts regulatory/limits.md ## Thresholds
  ("10,000 EUR", written 2026-03-02).
- You chose: override. regulatory/limits.md ## Thresholds updated to 15,000 EUR.
```

or

```
Conflict found (1) — logged to .wiki/conflicts_ignored.md, nothing existing changed.
```

## Edge cases

- **The contradiction is with an unvalidated note** (blank `validated from:`) — say so. That is
  usually the answer: the unverified statement is the one to doubt.
- **The material contradicts itself** — don't file it as fact. Ask which is right, or file both with
  the disagreement recorded in the note.
- **Several conflicts in one batch** — present them as one list, then ask once per conflict. Not one
  interruption per unit.
- **The user chooses override but the existing content is in many places** — fix the ones this task
  opened, and report the rest as an `audit` finding. A vault-wide rewrite is a restructuring
  operation, not part of filing a note.
- **The conflict is with the glossary rather than a note** — same procedure; the fix is the glossary
  entry (`references/glossary.md` → the three statuses), and an `(inferred)` definition losing to a
  note that actually defines the term is not a conflict at all, it is an ordinary repair.
