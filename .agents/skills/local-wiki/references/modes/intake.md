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

**Flag every transcript in the inventory.** A `.vtt`, an `.srt`, or any export full of timestamps
and speaker tags is one file and many units, and it is the item most likely to be miscounted as one
small placement (`references/ingest-sources.md` → Recordings, presentations and discussions).

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

A transcript is the one file that always splits: one recording is many units, segmented by topic
rather than by the order things were said (`references/ingest-sources.md` → The passes).

### 5. Extract each unit

<!-- profile-hook: intake-decompose -->

Per `references/ingest-sources.md`, produce an intake summary per unit. Extraction only — no vault
writes yet, nothing added the source didn't contain.

**Nothing is dropped, and a batch is where dropping happens.** Grouping several scraps into one unit
merges their *placement*, never their content: every claim from every member file survives into the
unit. The four things that may be dropped are listed in `references/ingest-sources.md` → Lose
nothing, and that list is exhaustive. A unit is not extracted until every fact in its sources has a
line in its summary.

**Tag nodes are decided across the whole batch too.** Resolve the batch's subjects against this
vault's tag tree once, by the ladder in `references/tagging.md`, and list every new node in one
pass (`python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> add <node> --meaning "..."`, parents first) before anything is filed. Each unit then
sets its own tags as it is filed.

**Terms are resolved across the whole batch**, once per term, not per unit.

**Extract before deciding what the material is about.** A structure chosen first becomes the sieve
that drops everything not shaped like it, and a heading is a container, not content. For every
source file with extractable text, take the mechanical baseline now — it is what step 9's second
pass measures the notes against, and it is the only count in this mode that is not the agent's own
opinion of its work:

```bash
python3 .agents/skills/local-wiki/scripts/extract_units.py extract <source> \
  --out .wiki/.second-pass/<source>.units.txt
```

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

Write the plan down before the first vault write — to `.wiki/intake-log.md` in step 6, never only
in the conversation. It is the resume record.

**`intake` combined with `where`** stops here: report the plan and write nothing at all, not even the
intake log.

#### Register the plan in a file, not in the conversation

**Write it to `.wiki/intake-log.md`** before the first vault write. A plan that exists only in the
running conversation is lost the moment the run is interrupted, and the next run re-derives it from
the folder — which is how material gets filed twice, or filed thinner the second time.

```
## Intake 2026-08-02 from .input/   [open]
- screenshot_01..03.png -> processes/onboarding.md ## Compliance checks  [merge]    [ ]
- notes-scratch.md      -> regulatory/target-market.md                   [new note] [ ]
```

- One line per unit: sources → destination and section → the rule that fired → a `[ ]` ticked in
  step 9, once that unit is written **and its second pass has closed**.
- The header carries `[open]`, and becomes `[done]` when every line is ticked.
- **This is the resume record.** An interrupted run reads the last block and continues from the
  unticked lines; it never re-inventories `.input/`.
- Before appending, check `wc -l .wiki/intake-log.md` and move every `[done]` block to
  `.wiki/intake-archive-<year>.md`, leaving at most the previous batch and this one. The archive is
  written and never read; the live file is read whole only when resuming.

### 6b. Delta pass — what of this batch is actually new

Per unit, with its destination open, run `references/placement-rules.md` → Rule 0. This is what
makes a re-dropped inbox a no-op: the check is per claim and by substance, so it holds however
the material was renamed, reformatted or re-exported. Report the batch totals
(`47 claims — 31 present, 12 new, 3 sharper, 1 conflicting`), and skip a unit whose every claim
came back `present`.

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

### 9. File one unit at a time — and prove each one landed before starting the next

Plan the whole inbox in steps 3–8; **file it one unit at a time.** A unit is one piece of material,
so it is usually one source file and sometimes several (five screenshots of one whiteboard). Nothing
about the next unit is read until the current one is written **and verified**.

| | Why |
|---|---|
| **One unit at a time** | Each unit means reading the destination, deciding, writing, linking, indexing, and proving the source landed. Three of those interleaved is how the verification degrades into agreeing with the notes |
| **Verified before the next starts** | `references/second-pass.md` re-reads the *source*. A source filed three units ago is out of context, and re-reading it then costs more and finds less |
| **Each unit finishes completely** | Written, tagged (`tags.py set`), linked, index updated, second pass closed, intake log marked — a point the run can stop at with nothing half-done |
| **The next unit reads the plan, not the folder** | The step-6 plan is what is left. Re-inventorying `.input/` mid-run re-reads material already filed |
| **Say where you are between units** | "4 of 14 filed, next: the MiFID scraps." A silent ten-minute run looks identical to a hung one |

Per unit, in this order:

1. Run `references/modes/update.md` steps 5–9 — read candidates, conflict check, validation gate,
   place, write, link, index.
2. Run the **second pass** on every source file in the unit, per `references/second-pass.md`:
   extract the baseline, `cover` the notes against it, double check both directions, self-critique,
   collect the open questions. Write the gaps it finds **now**.
3. Mark the unit's line in the intake log `[x]` — **only once its second pass closed.** A unit whose
   second pass is still `open` keeps its `[ ]`, and the run says so.

The intake log is what makes the run resumable — a unit written but not logged gets filed twice, and
a unit logged before its second pass carries a mark that says "verified" about work nobody checked.

The open-question cap is **per unit** (5), and a question already answered for one unit is not
re-researched for the next.

One unit per write operation, under ~200 lines.

Order across units: merges into existing notes first, then new notes in existing folders, then new
folders. If the run is interrupted, the vault is left with the least structural churn — and the
early units are the cheap, low-risk ones.

**A unit that produced a correction slows the rest down, not speeds them up.** If the second pass on
one unit found a real loss, the next unit's first pass is the one that produced it — extract before
deciding the structure, and expect to find the same loss again.

The validation answer from step 8 applies to every unit — do not re-ask per unit.

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

Never per unit. One episode for the batch's shape, not one per file — and any
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

Then the second-pass line, which is never omitted — a batch with nothing to report there is a batch
whose verification did not run:

```
Second pass: 14/14 files closed, 41 units recovered, 3 invented claims removed, 2 files still open
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

session startup (READY token) · git safety · **domain context read** · units filed (count) ·
**second pass closed (files closed / files in batch)** · conflict check · validation gate ·
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
- **A unit's second pass will not close** — its uncovered units stay listed, its intake-log line
  stays `[ ]`, and the batch continues with the next unit. Never mark it filed to keep the report
  tidy.
- **`.input/` is empty** — say so and stop. That's the normal state of a drained inbox.
- **Run interrupted** — re-run it. The vault shows what already landed, and step 6's
  duplicate check skips those units; nothing needs a resume file.
