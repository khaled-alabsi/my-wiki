# Inline index repair

<!-- sync: local-wiki-index-repair v1 -->

The index is used mid-task to route. When it turns out to disagree with the vault, the disagreement
gets **fixed on the spot**, before the routing decision that depends on it — not worked around, not
left for a later `refresh`, not silently tolerated.

This is the reactive counterpart to `references/modes/audit.md`. Audit sweeps the whole vault on
purpose; this repairs only what a task actually tripped over.

## The two rules that matter

**Fix before you decide.** A conflict discovered while routing is repaired first, then the routing
decision is made against the corrected index. Deciding on data you already know is wrong is the
failure this exists to prevent.

**Repair only what you touched.** The scope is the folders and files this task actually walked
through. Never wander into unrelated parts of the vault fixing things — that's `audit`, it's the
user's call to run it, and an update task that silently rewrites half the index is worse than a
stale line.

## Authority boundary

Repairable without asking: `index.md`, any per-folder `index.md`, their `## Business Glossary`
sections, `see-also.md`, and `.wiki/manifest.json`. These are routing infrastructure this
skill generates and owns.

Never touched by repair: **note content**. If a conflict's real cause is in a note (wrong heading,
duplicated content, a note in the wrong folder), the index gets corrected to describe reality and
the note issue is *reported*, not fixed. The two in-place note edits `update` may make — term
normalization and closing an answered question — are its own steps under their own rules
(`references/glossary.md`, `references/open-questions.md`), never something repair reaches for.

## Conflict taxonomy

Each entry: how it shows up, and what the fix is.

**Dead entry** — the index lists a file that isn't there.
Check for a rename before deleting: if the scan shows a file with the same H1 or clearly the same
topic at a new path, rewrite the entry's path and keep its description. Otherwise remove the line.

**Missing entry** — a file exists in a folder you're working in but has no index line.
Add its line, described from its actual content per `references/index-format.md`.

**Wrong description** — the `covers` line doesn't match what the file actually says.
This is the conflict that causes bad routing, and it only surfaces when a candidate gets read.
Rewrite the line from what you just read.

**Stale heading anchors** — a file's H2 sub-bullets don't match its real headings.
Rewrite that file's sub-bullets. If the file has grown past the threshold and has none, add them.

**Missing or unusable `Place here:`** — you routed through a folder whose line is absent, or so
vague it routes nothing ("misc", "stuff", "notes").
Write one from the folder's actual contents. If the folder genuinely has no common topic, say that
explicitly rather than inventing a theme.

**Unindexed folder** — a folder exists in the working area with no `## <folder>/` section at all.
Add the section with its `Place here:` line and entries, or a pointer if it's over the split
threshold.

**Split drift** — a folder is now over ~15 files with no per-folder `index.md`, or the root points
at a per-folder index that doesn't exist.
Create the missing per-folder index, or fix the pointer to match reality.

**Contents/section mismatch** — a `## Contents` entry with no matching section, or a section not
listed in `## Contents`.
Add whichever side is missing.

**Dead cross-reference** — a `see-also.md` bullet pointing at a note that no longer exists or moved.
Fix the target if it moved, drop the bullet if it's gone.

**Convention drift** — `## Conventions` describes something the vault demonstrably no longer does
(says wikilinks, vault uses markdown links).
Re-detect from the files you've read and update it. This one matters more than it looks: every new
note this skill writes is formatted from that section.

### Glossary conflicts

Same authority, same "fix before you decide" rule. All four surface only when a note gets read.

**Missing term** — the material or a note you read uses a domain term the glossary doesn't carry.
Add it, with the right status (`references/glossary.md` → The three statuses).

**Definition contradicted** — a note you just read defines a term differently from the glossary.
If the entry was `(inferred)` or `undefined`, the note wins: rewrite it as `defined` and point at
that note. If the entry was already `defined` from another note, the two notes disagree — that's a
**finding**, reported with both paths, and the glossary keeps the older entry until the owner
settles it. Never pick a winner silently.

**Alias that must be split** — an entry carries `(aka X)` and you've just found X with its own
independent expansion. Split into two entries immediately, note the confusable pair on both lines,
and report it. This is the only glossary conflict that can have caused a *wrong edit* — check
whether this run normalized that term and say so.

**Dead source** — a glossary entry's `→` target no longer exists or no longer defines the term.
Repoint it if the note moved; otherwise drop to `(inferred)` with the notes that still use it.

## Not a conflict

Don't churn on these:

- A terse description that's still accurate
- A file whose content changed but whose coverage line is still true
- An `(inferred)` glossary entry that nothing has contradicted — it stays inferred until a note
  defines it; `audit` is where the owner reviews the whole list
- A term you'd have worded differently in the glossary
- Files legitimately excluded from the index (ignored folders, attachments, templates)
- Ordering that doesn't match the ideal from `references/index-format.md` → Ordering
- A `Place here:` line you'd have worded differently

Repair fixes what is *wrong*, not what is *suboptimal*.

## Escalation

Count the conflicts as you go. When the index is systemically stale rather than locally wrong, stop
patching:

- **5+ conflicts in one task**, or the working folder has more wrong entries than right ones → run
  `refresh` scoped to that subtree (`references/modes/refresh.md`), then continue the task.
- **Root structure is wrong** — top-level folders missing or renamed, or the index doesn't match the
  format at all → run a full `refresh` before continuing, and say so first.
- **The conflict count crosses the threshold mid-write** → finish the current write, then refresh,
  then continue. Never abandon a half-written note.

Say which one happened. A user whose task quietly turned into a re-index should know why.

## After repairing

- Update `.wiki/manifest.json` so the next run's diff starts from the corrected state.
- Repairs are idempotent: check the line isn't already correct before rewriting it.
- Never re-run a full index build to record a handful of line fixes.

## Reporting

Repairs go in their own short block, **after** the task result — never mixed into it. The user asked
to file a note; the index fix is a side effect they should see but not have to read past.

```
Index repairs (3):
- banking/mifid-basics.md — description didn't match content, rewrote it
- banking/old-note.md — file gone, entry removed
- banking/ — no "Place here:" line, added one
```

Nothing to repair → say nothing. An empty repair block is noise.

## Mode differences

- `update`, `ask`, `audit`, `indexing`/`refresh` — repair as described here.
- `intake` — repair as described here, but count conflicts across the **whole batch**, not per unit.
  A staging run touches many folders, so the escalation threshold is reached faster and a scoped
  refresh before filing is often cheaper than repairing entry by entry.
- `where` — **report conflicts, fix nothing.** It's an explicit no-write mode; a dry run that
  modifies files isn't a dry run. List what would be repaired alongside the placement decision.
- A **restructuring run** (`wiki refactor`, which this skill does not perform) rebuilds the index
  wholesale at the end, so patching entries during one is wasted work against a structure that's
  about to change. If a reorganization is under way, record conflicts as findings and let the
  rebuild resolve them.
