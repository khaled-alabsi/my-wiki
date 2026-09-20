# Refactor mode — restructuring the vault on your instruction

<!-- sync: local-wiki-modes v5 -->

The user says what should change — "merge these two notes", "split `payments.md`", "move everything
about settlement under `custody/`", "this folder has become a junk drawer, break it up" — and this
mode carries it out **and repairs everything the change breaks**.

That second half is the point. Moving one note is `mv`. Moving one note without leaving broken
links, a stale index, a wrong graph and a search index pointing at a path that no longer exists is
what this mode is for.

**Inputs**: the user's instruction, the vault root from `vault-profile.md`.
**Outputs**: moved/renamed/merged/split notes, rewritten links, an updated index, refreshed graph
and search index, a report.
**Reads**: `references/knowledge-organization.md` for whether the change is sound,
`references/domain-architecture.md` when the change is structural,
`references/index-format.md`, `references/linking.md`, `references/tracking.md`,
`references/git-safety.md`.

## What this mode may do

Move · rename · merge · split · create a folder · delete a folder that is now empty · rewrite links.

**Tags follow the content.** A merged note carries the union of its sources' tags, and a split
note's tags are decided again for each part, both through `scripts/tags.py set`. Reshaping the tag
tree itself is `tags.py move`, and the run ends with `tags.py check` (`references/tagging.md`).

**It never destroys.** A note that is merged away or superseded is **moved to `.wiki/.trash/`**,
preserving its relative path inside, after the destination has been written and verified to hold its
content. There is no `rm` in this mode.

## Workflow

### 1. Session startup and git safety

`references/tracking.md` → Session startup, then `references/git-safety.md`. A restructure touches
many files at once; doing it on a diverged checkout is the worst possible time to find out.

### 2. Understand what was asked, and check it is sound

<!-- profile-hook: refactor-soundness -->

**Load `.wiki/domain-context.md` first.** It carries the vault owner's standing knowledge about
this domain — canonical terminology, which identifier is authoritative, rules that are always true
here, how material in this domain should be handled. It is short by design and read in full.

It changes decisions this step is about to make: which term the note is written in, whether two
things are the same concept, which source wins when notes disagree. Reading it after placing the
material is too late.

Empty or absent → carry on, that is the normal state of a young vault.

Restate the instruction as concrete operations. Then sanity-check it against
`references/knowledge-organization.md` — not to overrule the user, but to catch the two things they
cannot see from outside:

- **a move that breaks primary ownership** — the note ends up somewhere its concept does not live;
- **a merge that destroys a useful distinction** — two notes share vocabulary but serve different
  purposes.

If the instruction is structural ("reorganize this folder"), also run
`references/domain-architecture.md` → Structure Evolution.

Say so in one line if you see a problem, then do what was asked. **The user's instruction wins** —
this is their vault, and they asked for a specific change, not for advice.

### 3. Find everything the change will break — before touching anything

```bash
python3 .agents/skills/local-wiki/scripts/graph.py query --backlinks <each affected note> --vault <vault>
```

Every inbound link is a file that must be rewritten when the target moves. This is the step that
separates a clean restructure from one that leaves a trail of dead links, and the graph already
knows the answer — do not grep for it.

Also collect: the affected `index.md` entries, any `see-also.md` bullets pointing at the notes, and
whether a folder will be left empty.

### 4. Write the plan, and get it accepted

For anything touching **more than one file**, show the plan and wait:

```
Refactor plan
  move    payments/sepa.md            -> payments/sepa/overview.md
  move    payments/sepa-instant.md    -> payments/sepa/instant-payments.md
  create  payments/sepa/              (3 notes, earns its own folder)
  rewrite 4 inbound links across 3 notes
  update  index.md: 1 folder section, 3 file lines
  trash   nothing
```

A **single unambiguous operation** the user spelled out — one rename, one move — does not need a
ceremony. Do it and report it.

**Nothing is written before the plan is accepted.** If the plan turns out to be wrong once accepted,
stop and re-plan rather than improvising mid-way.

### 5. Execute, in this order

Order matters — each step depends on the one before it:

1. **Create** any new folders, with their `Place here:` lines ready for the index.
2. **Write** the destination content first — for a merge, the merged note; for a split, all the new
   notes.
3. **Verify** the destination actually holds the content. Read it back.
4. **Then** move superseded sources to `.wiki/.trash/`, preserving their relative path. Never
   before step 3.
5. **Rewrite every inbound link** found in step 3 — path and anchor. A link whose anchor pointed at
   a heading that moved to a different note now points at the new note.
6. **Update `see-also.md`** bullets that referenced moved notes.

Stay under ~200 lines per write operation.

### 6. Update the index

Per `references/index-format.md`: folder sections added or removed, `Place here:` lines for new
folders, file lines moved between sections, heading sub-bullets for notes that changed shape. A
folder left empty loses its section.

The glossary is carried forward — a restructure moves notes, it does not change what terms mean.

### 7. Rebuild the derived state

Once, at the end, in this order:

```bash
python3 .agents/skills/local-wiki/scripts/scan_vault.py \
  --root <vault> --out .wiki/manifest.json --previous .wiki/manifest.json
python3 .agents/skills/local-wiki/scripts/graph.py scan --full --vault <vault>
python3 .agents/skills/local-wiki/scripts/contributors.py record \
  --user-id <user_id> --path <each moved or written note> --type edited --vault <vault>
.rag/bin/rag update --quiet
```

**`graph.py scan --full`, not `--since-manifest`** — paths moved, so incremental scanning would
leave edges pointing at the old locations. This is one of the few times a full rebuild is correct.

**`rag update` is not optional here.** The search index holds the old paths; without this, every
search returns hits for files that no longer exist. If many files moved, say so and recommend
`.rag/bin/rag index --full`, which is the case `README.md` describes for a `.ragignore` or path
change.

### 8. Verify, then report

```bash
python3 .agents/skills/local-wiki/scripts/graph.py query --broken --vault <vault>
```

**Zero broken links, or the refactor is not finished.** If any remain, fix them now — a restructure
that leaves dead links has failed at the one job that distinguishes it from `mv`.

Report what moved, what was trashed, how many links were rewritten, and what the index gained or
lost.

## 9. Closeout

End with the checklist (`SKILL.md` → Closeout checklist). For `refactor` the mandatory lines are:

session startup (READY token) · git safety · plan accepted · notes moved/merged/split (counts) · sources trashed ·
inbound links rewritten · see-also updated · index updated · **broken links checked (must be zero)** ·
graph rebuilt (full) · contributors recorded · **search stated** · search index refreshed

## Edge cases

- **The user asks for something that would lose content** — a merge that drops sections, a delete.
  Say exactly what would be lost and confirm. Nothing in this skill deletes; the answer is always
  `.wiki/.trash/`.
- **A moved note is the target of a link from outside the vault** — you cannot fix what you cannot
  see. Report the move so the user can update anything external.
- **The instruction conflicts with the accepted structure** in `.wiki/structure-accepted.md` — that
  file records what was agreed at `init`, not a law. Do what was asked, and mention the drift so
  the user can update the record if the new shape is the real one.
- **Halfway through, a destination already exists** — stop. Do not merge into it on a guess; ask
  whether to merge, rename, or pick another path.
- **The refactor is large** (dozens of files) — do it in batches with the plan approved once, and
  report progress between batches. Never leave the vault with half its links rewritten.
- **Nothing actually needs to change** — say so. "That folder is already organized the way you
  described" is a complete answer.
