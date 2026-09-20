# Refresh mode

<!-- sync: local-wiki-modes v5 -->

Re-describes only what changed since the last scan, and brings the search index and the graph back
in step. For after someone edited notes directly, pulled a colleague's changes, or added files
outside this skill.

**This is the incremental half only.** Building an `index.md` from scratch is not something this
skill does: the vault was indexed at `init`, and a from-scratch rebuild of a vault that already has a
curated index throws away descriptions people have refined. If the index is genuinely beyond repair,
that is a `wiki refresh` or `wiki indexing` run against the vault — say so rather than improvising.

**Inputs**: the vault root.
**Outputs**: updated index entries for changed files, updated glossary, refreshed `.rag` index and
graph, a report.

## Workflow

### 1. Session startup

`references/tracking.md` → Session startup. No git check — `refresh` describes what is already on
disk rather than adding anything.

### 2. Diff against the last manifest

```bash
python3 .agents/skills/local-wiki/scripts/scan_vault.py \
  --root <vault> --out .wiki/manifest.json --previous .wiki/manifest.json
```

Every record comes back tagged `NEW`, `CHANGED`, `UNCHANGED` or `REMOVED`. Only the first three
matter, and `UNCHANGED` files are never re-read — that is the entire point of this mode.

Report the counts before starting. A refresh that turns out to touch 200 files is a different
conversation from one touching 3.

### 3. Re-describe what moved

- **NEW** — write its index line, described from actual content per `references/index-format.md`.
  Add H2 sub-bullets if it is over ~150 lines or has 4+ H2s. Place it in the right folder section.
- **CHANGED** — re-read it and rewrite its `covers` line **only if the content moved away from what
  the line says**. A file whose line is still true is left alone; churning descriptions produces a
  diff nobody can review.
- **REMOVED** — check for a rename first (same H1 or clearly the same topic at a new path). A rename
  keeps its description at the new path. A genuine deletion loses its line.

### 4. Carry the glossary forward, then extend it

Existing entries are carried forward **verbatim** — statuses, aliases, sources and all. A refresh
never re-derives the glossary from scratch; an owner who corrected an entry would lose that
correction every time.

Then add terms from `NEW`/`CHANGED` files only, using the manifest's `glossary_candidates` and
`references/glossary.md`. Upgrade an `(inferred)` or `undefined` entry when a changed file now
defines the term.

### 5. Add a `## Recently changed` section

Per `references/index-format.md`, list what this refresh touched. It is dropped on a full rebuild and
regenerated each refresh — a short "what moved lately" for whoever reads the index next.

### 6. Refresh the graph and the search index

```bash
python3 .agents/skills/local-wiki/scripts/graph.py scan --since-manifest --vault <vault>
.rag/bin/rag update --quiet
```

`--since-manifest` re-parses only the files the scan marked NEW or CHANGED. Use `scan --full` only
when the graph is suspected wrong — after a bulk rename, or a restore from backup.

Then check the graph is still healthy after the outside edits, since that is exactly when links
break:

```bash
python3 .agents/skills/local-wiki/scripts/graph.py query --broken --vault <vault>
```

Someone renaming a heading by hand is the single most common source of a dead anchor, and a refresh
is when it surfaces. Report broken links; fixing them in note text is `update`'s job or the user's.

The same goes for tags. A note edited by hand, in Obsidian or in the UI, can carry a tag this vault
has never seen:

```bash
python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> check
```

Report what it prints. `refresh` tags nothing and lists nothing; each failure line names the
command that clears it, and a vault with many untagged notes wants a `tag` run
(`references/tagging.md`).

### 7. Report

```
Refreshed: 3 new, 5 changed, 1 removed (of 218 files).

New:
- regulatory/target-market.md — MiFID target market assessment, who performs it and when
Changed:
- processes/onboarding.md — coverage widened to include the escalation path
Removed:
- processes/old-flow.md — renamed to processes/onboarding-legacy.md, entry moved

Glossary (2 added, 1 upgraded):
- TaMrA — now defined by regulatory/target-market.md (was inferred)

Broken links (1):
- processes/onboarding.md -> regulatory/mifid.md#target-market — that heading no longer exists

Tags: tags check DRIFT — 1 failure
- unlisted  payments/instant  (payments/sepa-instant.md)

.rag index updated (8 files re-embedded). Graph updated (12 edges).
```

Omit any block that is empty. "Nothing changed since the last scan" is a complete and useful report.

## Closeout

End with the checklist (`SKILL.md` → Closeout checklist). For `refresh` the mandatory lines are:

session startup (READY token) · files re-described (new/changed/removed counts) · glossary carried forward ·
broken links checked · tags checked · graph rescanned · **search stated** · search index refreshed

## Edge cases

- **No manifest yet** — there is nothing to diff against. Scan without `--previous`, treat every file
  as NEW, and say that this first pass is a full description rather than a refresh.
- **The manifest is newer than every file** — nothing changed. Say so and stop; don't re-read the
  vault to prove it.
- **Many files changed at once** (a colleague's merge) — normal. Report the count first, then
  proceed; the work is proportional to what moved.
- **A changed file's index line is still accurate** — leave it. Not every change alters coverage.
- **`.rag` update fails** — report the command once and continue. A stale semantic index degrades
  search; it breaks nothing.
- **A file changed *and* its heading was renamed** — both a description update and a probable broken
  anchor. Handle the description here, report the anchor.
