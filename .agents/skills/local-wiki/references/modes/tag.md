# Tag mode: tag the notes a vault already holds

`update` and `intake` tag a note as they file it. This mode is for everything in this vault that
was filed before tagging existed, or before anyone tagged it: it walks the vault, gives each note its tags,
and shapes the tag tree as it goes. The rules it applies are in `references/tagging.md`. Read that
first; this file is only the order of work.

**Inputs**: nothing, or a subtree (`tag regulation/`) to limit the run. `retag=<subtree>` (or
`retag=.` for the whole vault) revisits notes that already carry tags.
**Outputs**: a `tags:` line on each note that earns one, new nodes in `.wiki/tags.md`, and a report
per folder.

**It writes and reports. There is no approval gate**, because a tag line is additive: it changes
no prose, moves no note, and `tags.py set` with `--remove` undoes it. What it must never do is
reword a note, move one, or place one by its tags.

Never inferred from a prompt shape. The user asks for it by name: it writes a line into many notes
in one run, and that is not something to start because a prompt mentioned tags.

## Workflow

1. **Session startup** (`references/tracking.md` → Session startup), then **git safety**, once
   (`references/git-safety.md`). A run that rewrites a line in hundreds of notes starts from a
   checkout that is in step.

2. **Scan**, so the work list is current:

   ```bash
   python3 .agents/skills/local-wiki/scripts/scan_vault.py --root <vault> --out .wiki/manifest.json \
       --previous .wiki/manifest.json
   ```

3. **Read what decides a tag, once each**: `.wiki/tags.md` whole (this mode reasons about the
   whole tree), `.wiki/domain-context.md`, the knowledge profile when the vault has one, and the
   root index's `Place here:` lines and `## Business Glossary`. No inventory file yet means
   `python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> init`.

4. **Seed the trunk, only when the inventory is empty.** Propose up to twelve top-level
   **subjects**, each with a one-line meaning, and `tags.py add` them. Subjects, never folder names:
   a trunk that mirrors the folders says nothing the folders do not
   (`references/tagging.md` → What a tag is).

5. **Take in what the notes already carry.**

   ```bash
   python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> check --json
   ```

   Every `unlisted` failure is a tag some note already has. `add` each one, parents first, with a
   meaning line taken from how the notes use it. Those tags are the owner's decisions and stay as
   they are for now. A `malformed` one is fixed in step 6, when its note comes up.

6. **One folder at a time, in sorted order, in batches of 25:**

   ```bash
   python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> pending --scope <folder> --limit 25 --json
   ```

   Each record is a note's **outline**: title, H2 headings, first line, acronyms, current tags.
   - **Decide from the outline plus the note's line in `index.md`.** Open the note only when those
     two do not settle which subjects it is about. That is what keeps a vault of thousands of notes
     inside one run's context: 25 outlines at a time, and no note text kept between batches.
   - **Assign by the ladder** (`references/tagging.md` → Reuse before creating). `add` any new
     node first, then `tags.py set <note> --add <tag> ...` for each note.
   - **A note that earns no tag gets none.** A routing file, a stub, a note whose only subject is
     its folder. It stays on the pending list, and the report says why.
   - **Reshape only at the end of a batch.** A node that now directly carries more than
     `tag_branch_notes` notes is split into children; a pair of nodes that turned out to be one
     subject is merged. Both go through `tags.py move`, which rewrites the notes already tagged.
     Never mid-batch: the outlines in hand still name the old node.
   - Say where the run is: `folder done: <n> notes tagged, <m> nodes added, next: <folder>`.

7. **Resuming needs no state.** For a plain `tag` run the notes are the record: an untagged note is
   pending, a tagged one is done, and `pending` reads that live. An interrupted run is resumed by
   running the mode again.

   A **`retag`** is different: a note that was revisited and left as it was looks exactly like one
   not visited yet. So `pending --retag` keeps a receipt, `.wiki/.tag-run.json`, of the folders
   finished. Close each folder with `python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> batch-done <folder>`.
   The tool deletes the receipt when nothing is pending.

8. **Close out, once:**

   ```bash
   python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> drop <node>      # each trunk node that ended up empty
   python3 .agents/skills/local-wiki/scripts/scan_vault.py --root <vault> --out .wiki/manifest.json \
       --previous .wiki/manifest.json
   python3 .agents/skills/local-wiki/scripts/graph.py --vault <vault> scan --since-manifest
   .rag/bin/rag update --quiet
   python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> check
   ```

   **`check` must exit 0.** Anything it still fails is cleared now, by the command its line names,
   or listed in the report as outstanding with the reason.

9. **Record who changed what**, once, for every note whose tags line was written:
   `python3 .agents/skills/local-wiki/scripts/contributors.py record --user-id <user_id> --path <file> --type edited --vault <vault>`
   (`--path` repeats, so one call per batch).

10. **Record what could have gone another way**: a split, a re-parent, a merge. One episode each,
   `python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> record --mode tag --scope glossary ...`
   (`references/agent-memory.md`). A tag picked by the `Certain` rung is not a decision and is not
   recorded.

## Report

```
Tagged 212 notes in 9 folders. 38 nodes in the tree, 14 of them new.

  regulation/ ......... 61 tagged, 2 left untagged (routing stubs)
  payments/ ........... 40 tagged
  ...

Tree
  added ............... regulation/mifid/target-market, payments/sca, ... (14)
  moved ............... compliance/kyc -> banking/accounts/kyc (11 notes rewritten)
  split ............... regulation (31 direct) -> regulation/mifid, regulation/psd2, regulation/gdpr
  dropped ............. operations (seeded, nothing landed there)
  inventory ........... 38 of 300 nodes

Still to do
  3 nodes have no meaning line: payments/cards, ...
```

## Closeout checklist

```
Closeout
  [x] session startup .......... READY <token>
  [x] git safety ............... in step with origin/main
  [x] scanned .................. 218 notes
  [x] inventory read ........... 24 nodes at the start
  [x] notes tagged ............. 212 of 214 pending, 2 left with a reason
  [x] tree shaped .............. 14 added, 1 moved, 1 split, 1 dropped
  [x] graph rescanned .......... 38 tags
  [x] .rag refreshed ........... 212 files re-embedded
  [x] tags check ............... tags check OK: 38 nodes, 212 of 218 notes tagged
  [x] contributors recorded .... 212 files, edited
  [x] episodes recorded ........ EP-301 (split), EP-302 (move)
```

The `tags check` line carries the line the command printed. A mark with nothing behind it is
worth nothing.

## Edge cases

- **The inventory is at its cap** and `add` exits 3: merge the leaves it names, or the leaves that
  turned out to be one subject, before adding. Never raise `tag_nodes_max` to get past one node.
- **A vault that arrives with hundreds of its own tags**: step 5 lists them all. If that alone
  passes the cap, say so and stop. Raising the cap or merging the owner's tags is the owner's call.
- **A note with an unclosed frontmatter block**: `set` refuses it. Report the note; never guess
  where the block ends.
- **A subtree was given**: only its notes are tagged, and the tree may still gain nodes anywhere.
  `check` runs over the whole vault regardless.
- **The run is asked for in the middle of another task**: finish that task first. A `move` rewrites
  notes the other task may have open.
