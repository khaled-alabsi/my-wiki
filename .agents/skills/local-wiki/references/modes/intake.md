# Intake mode — draining a staging folder

<!-- sync: local-wiki-modes v5 -->

A folder of raw material — screenshots, half-written notes, pasted scraps, exports — gets extracted,
restructured, and filed into the vault as one batch.

**The default source is `.input/`** at the vault root. It exists for exactly this, so "process my
inbox" needs no path. Any other folder the user names works the same way.

This is `update` applied to many items at once, plus the thing item-by-item filing cannot do:
**seeing the batch as a whole** before placing anything. Six scraps that are all one new topic become
one coherent note, not six scattered placements.

## The source folder is read-only — with one approved exception

Never delete, move, rename or edit anything in the staging folder while draining it. Filing material
does not entitle this skill to tidy up the source.

**The one exception**: after the batch is filed, step 11 asks whether to move the processed files to
`.wiki/.trash/`. That move happens only on an explicit yes, only after the content is safely in the
vault, and it is a **move to a recoverable location — never a delete**.

**One addition beyond that rule**: once the batch is filed, **actively ask the user to remove the
processed files**. The content is safely in the vault, `.input/` is git-ignored, and leaving it full
means the next run re-reads material it has already filed. Ask; never delete.

## Workflow

### 1. Session startup and git safety

`references/tracking.md` → Session startup, then `references/git-safety.md` **once for the whole
batch** — not per unit.

### 2. Read the domain context — before you look at a single file

```bash
cat .wiki/domain-context.md
```

**This is the most consequential read in the whole mode, and it comes first.** It carries the vault
owner's standing knowledge about this domain: canonical terminology, which identifier is
authoritative, rules that are always true here, how material in this domain should be handled.

A batch is where getting it wrong compounds. Every decision downstream depends on it:

- **Grouping** (step 4) — whether two scraps are the same concept is a domain question. Without the
  context you group by wording; with it you group by meaning.
- **Terminology** — the batch resolves each term once, for the whole batch. Resolving them against
  the wrong canonical form mislabels every unit at once.
- **Structure** (step 6) — whether a cluster deserves a folder depends on what the domain considers
  a real category.
- **Contradictions** (step 7) — a domain rule is often exactly what makes incoming material wrong.

Getting this wrong on a single note is one misplaced note. Getting it wrong on a batch of forty is
forty, all consistently wrong in the same direction, and consistent wrongness is the hardest kind to
spot afterwards.

Empty or absent → carry on, that is the normal state of a young vault.

### 3. Inventory the batch — before extracting anything

List every file (recursively, skipping the usual ignores). For each: name, extension, size, mtime,
and for text files a one-line read of what it appears to be. Report the count and the apparent mix
before starting.

Nothing tracks what a previous run consumed, and nothing needs to: **the vault is the record.**
Step 6 checks each unit against what is already there, and material already filed verbatim is
reported as a duplicate and skipped. `.input/` is cleared at the end of a successful run (step 11),
so a re-run of a drained inbox finds nothing to do.

If you want to know who filed what and when, that is `contributors.py query` — it records every
written path with its author and timestamp, and it is queried rather than read.

### 4. Group related items

The step that makes a batch different from a loop. Signals: filename sequence and shared prefixes,
mtime clustering, content continuity, shared entities.

Output: a list of **intake units**, each with its member files. Everything downstream operates on
units, never raw files.

### 5. Extract each unit

<!-- profile-hook: intake-decompose -->

Per `references/ingest-sources.md`, produce an intake summary per unit. Extraction only — no vault
writes yet, nothing added the source didn't contain.

**Terms are resolved across the whole batch**, once per term, not per unit.

### 6. Decide the shape of the whole batch — before any write

**Run `references/knowledge-organization.md` over the batch as a whole.** A batch is where its
reasoning pays off most: several scraps are often one knowledge object, one long export is often
several, and a cluster of three or more related units is the strongest evidence a folder has
actually been earned rather than invented.

For the batch, that file decides: what the real knowledge units are (which is **not** the same as
the file boundaries the inbox happened to have), which of them a canonical note already owns, where
primary ownership sits, and whether the cluster justifies a folder under its "folders emerge from
clusters" rule.

Which units merge into existing notes, which become new notes, which cluster into a new topic, which
are too thin to stand alone, and which terms the batch adds to the glossary.

Three or more units on a topic the vault has no home for is a **new folder**, not three loose notes.
Two units on one topic is usually one note with two sections. A single unit is just `update`.

Write the plan down before the first vault write. It is also the resume record.

**`intake` combined with `where`** stops here: report the plan and write nothing at all, not even the
intake log.

### 7. Check the batch for contradictions

Per `references/conflict-detection.md`, per unit, against what the vault already says. A batch is
where contradictions cluster — an export that restates an old process, a scrap that supersedes a
note. Each real conflict is raised before that unit is written.

### 8. Ask the validation question — before a single unit is written

**A required step, not a formality.** Ask once for the whole batch:

> Are you 100% sure this material is correct, or should it go on the validation list for someone to
> confirm?

- **Sure** → file normally, nothing else happens.
- **Not sure** → every unit in the batch gets a checkbox in `.wiki/todos_validations.md` and blank
  `validated from:` / `validated at:` fields on the note or section it lands in.

Once per batch, never once per unit — twelve identical confirmations is a prompt people stop
reading. But **never skipped**: material filed without anyone confirming it looks exactly as
authoritative as material someone checked, and that is what the validation list exists to prevent.

Full rules in `references/tracking.md` → Validation gate.

### 9. File in waves of three — never the whole inbox in one pass

Plan the whole inbox in steps 3–8; **file it at most 3 units at a time** (`intake_wave` in
`.wiki/wiki-config.json`).

| | Why |
|---|---|
| **A wave is ≤3 units** | Each unit means reading the destination, deciding, writing, linking and indexing. Thirty of those in one pass is how a run runs out of room half-way and leaves the vault written but unindexed |
| **Each wave finishes completely** | Written, linked, index updated, intake log marked — a point the run can stop at with nothing half-done |
| **The next wave reads the plan, not the folder** | The step-6 plan is what is left. Re-inventorying `.input/` mid-run re-reads material already filed |
| **Say where you are between waves** | "3 of 14 filed, next: the three MiFID scraps." A silent ten-minute run looks identical to a hung one |

For each unit in the wave, run `references/modes/update.md` steps 5–9 (read candidates, conflict
check, validation gate, place, write, link, index), then mark those lines in the intake log as filed
**before starting the next wave**. The log is what makes the run resumable — a wave written but not
logged gets filed twice.

The open-question cap is **per unit** (5), and a question already answered for one unit is not
re-researched for the next.

One unit per write operation, under ~200 lines.

Order across waves: merges into existing notes first, then new notes in existing folders, then new
folders. If the run is interrupted, the vault is left with the least structural churn — and the
early waves are the cheap, low-risk ones.

**Three is a ceiling, not a target.** Drop to 1 when the units are large, when each lands in a
different folder, or when the previous wave produced a correction — a wrong placement repeated
three at a time is three notes to move instead of one.

The validation answer from step 7 applies to every unit — do not re-ask per unit.

### 10. Once, at the end, for the whole batch

```bash
python3 .agents/skills/local-wiki/scripts/contributors.py record \
  --user-id <user_id> --path <each file> --type added|edited --vault <vault>
python3 .agents/skills/local-wiki/scripts/graph.py scan --since-manifest --vault <vault>
python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> record --mode intake \
  --decision place --target <the batch's main destination> --rationale "<why>" --user-id <user_id>
python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> promote --json
.rag/bin/rag update --quiet
```

Never per unit, never per wave. One episode for the batch's shape, not one per file — and any
promotion `promote` reports goes in the report, by id (`references/agent-memory.md`).

### 11. Report

Grouped by destination, not by source file — the user wants to see what their vault gained:

```
Filed 14 items from .input/ into 6 notes:

processes/onboarding.md
  - merged 5 screenshots into ## Compliance checks, added a mermaid flowchart
regulatory/  (new folder)
  - target-market.md (new) - from 3 scraps
  - suitability.md (new) - from 2 scraps

Not filed (2):
  - invoice-scan.pdf - unrelated to anything in the vault
  - IMG_4471.png - no readable content
```

Then the standard blocks (`references/modes/update.md` → Report) for questions, normalizations,
links, glossary, index repairs, validation, and the `.rag`/graph line.

End by saying explicitly that **the staging folder was not modified**.

### 12. Offer to clear the inbox

**A required step.** Once the batch is filed and reported, ask — do not leave it implied, and do not
end the run without asking:

> I filed 14 files from `.input/`. Shall I move them to `.wiki/.trash/`, or do you want to keep them
> where they are?

- **Yes** → move them into `.wiki/.trash/`, preserving their filenames. Create the folder if needed.
  Report what moved.
- **No** → leave them exactly where they are and say so.

**Move, never delete.** `.wiki/.trash/` is recoverable; a deletion is not, and material the user
dropped in an inbox is the last thing to destroy on a guess. If a name already exists in the trash,
suffix it rather than overwriting.

Why this is asked rather than assumed: a full `.input/` means the next run re-reads material it has
already filed, so leaving it is a real cost — but the files are the user's, and some people keep the
originals deliberately.

## Deciding a new folder

Rule 4 of `references/placement-rules.md`, with the batch as evidence. Justified when 3+ units share
a topic, **and** no existing folder's `Place here:` line covers it without becoming untrue, **and**
the topic sits at the same conceptual level as the vault's existing folders.

The new folder gets its `Place here:` line in the index immediately, before its notes are written.

A new top-level folder in a vault whose structure was deliberately accepted at `init` deserves a loud
flag in the report — the accepted structure is recorded in `.wiki/structure-accepted.md`, and this is
a departure from it.

## Closeout

End with the checklist (`SKILL.md` → Closeout checklist). For `intake` the mandatory lines are:

session startup (READY token) · git safety · **domain context read** · units filed (count) · conflict check · validation gate ·
links · index updated · intake log updated · contributors recorded · graph rescanned ·
**search stated** · search index refreshed · **inbox cleared (asked)**

The last one is the one most often missed — if you did not ask, the line is `[ ]`, not absent.

## Edge cases

- **Batch is huge (50+ items)** — report the inventory and propose a scoping cut before filing
  everything blind. This is the one place asking is cheaper than guessing.
- **An item is already in the vault verbatim** — skip it, list it under "already filed".
- **Two units duplicate each other** — merge them into one unit at step 3.
- **A file can't be read** — list it as not filed, with the reason. Never guess contents from a
  filename.
- **A whole subfolder in the staging area is one topic** — treat it as a unit boundary; the user's
  own grouping is evidence.
- **`.input/` is empty** — say so and stop. That's the normal state of a drained inbox.
- **Run interrupted** — re-run it. The vault shows what already landed, and step 6's
  duplicate check skips those units; nothing needs a resume file.
