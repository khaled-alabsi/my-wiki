# The index.md contract

`index.md` is a **routing map for an agent**, not a summary of the vault and not a reading list for
a human. Every line exists to answer one of two questions:

- *Where do I look for X?*
- *Where does this new material belong?*

If a line helps with neither, it doesn't go in the index.

## Never use a markdown table in an index

**Bullet lists only. No tables, anywhere, for any part of an index.**

Not for the contents list, not for a folder's files, not for the glossary, not "just for the empty
folders". This holds for the root `index.md` and every per-folder one.

Tables wrap badly in a terminal, are painful to edit one row at a time, and are the single hardest
markdown structure for a model to append one correct row to. An index is appended to on almost every
write, so the format has to survive being edited constantly by something that is not careful.

> **Note on this file**: the reference files themselves use tables freely, because they are read
> top to bottom by a human and never appended to. Do not copy their formatting into an index. What
> an index looks like is defined by `assets/templates/index-root.md`, not by the file you are
> reading now.

## The two description types

**Folder line — `Place here:`.** A routing rule, phrased as what belongs, not what exists. This is
the single most important line in the index; a folder without one is a dead end.

- Good: `Place here: regulatory rules, MiFID/WpHG obligations, anything about advisory duties.`
- Bad: `Place here: banking stuff.` (unroutable)
- Bad: `This folder contains 12 notes about banking.` (describes, doesn't route)

**File line — what it covers.** Derived from the file's actual content and headings, never from its
filename. The test: could an agent decide from this line alone whether the answer to a question, or
the home for a new paragraph, is in this file?

- Good: `` `rebasing.md` - interactive rebase, fixup/squash, recovering from a botched rebase ``
- Bad: `` `rebasing.md` - notes about rebasing `` (restates the filename, routes nothing)

## Cross-reference files (`see-also.md`)

A folder that received a cross-reference (`references/placement-rules.md` → Cross-referencing a
strong secondary fit) gets a `see-also.md` at its root — a flat list of links to notes that live
elsewhere but are strongly relevant to this folder's topic. It is not a content note: never give it
heading sub-bullets, and never derive its index description from its contents the way a normal file
line is.

Its index entry is always the same fixed line, once per folder that has one:

```
- `see-also.md` - cross-references to notes that live elsewhere but are relevant here
```

Order it alphabetically among that folder's loose files, same as any other file line. Its presence
is never a reason to reword that folder's `Place here:` line — a cross-reference doesn't change what
belongs in the folder, it just admits something relevant lives elsewhere too.

## The Business Glossary section

Every index carries one — the terms this vault uses that an outsider couldn't resolve, so an agent
knows what `PIP` or `GEE` means before opening a note. One line per term, alphabetical:

```
## Business Glossary

- **GEE** — Geeignetheitserklärung. Written statement of why a recommendation suits the client. → `Banking/mifid-wphg.md`
- **PIP** (aka PEP) — Product Information Paper. Pre-contractual product summary. → `Banking/COBA/pip.md`
- **TaMrA** — Target Market Assessment. (inferred from usage in 4 notes) → `Banking/mifid-wphg.md`
```

`references/glossary.md` owns the rest: which terms are admitted, the stoplist, the three statuses
(defined / inferred / undefined), the alias confidence ladder, and when a term may be normalized in
note text. Read it before writing or repairing this section.

**Scope per index.** The root glossary holds terms used across the vault — anything appearing in 2+
top-level folders — plus the terms of every folder the root indexes inline. A folder with its own
`index.md` carries its own local terms there, additional to the root's, never a copy of them.

**Budget: ~50 lines per glossary section.** On overflow, folder-local terms move down into the
per-folder indexes and the root keeps terms by breadth of use; report the count that moved. The
section is always written as its own operation, never mixed into a folder section's write.

## The `## Related` section

A note carries a `## Related` section listing the notes it relates to, one line each with a reason
(`references/linking.md`). It is always the **last** section of a note.

```markdown
## Related
- [onboarding](../processes/onboarding.md#compliance-checks) — where the target market check is performed
```

It is note content, not index content: it lives in the note, and the index never reproduces it. But
it is *routing* content, so the same honesty rule applies — a line whose target no longer exists is
a broken link, found by `scripts/graph.py query --broken` and fixed like any other dead entry.

`## Related` is **never** given heading sub-bullets in the index, and never counts toward the 4+-H2
threshold that earns a note its sub-bullets — it is machinery, not a topic the note covers.

## Heading anchors, and the slug rule

A note over ~150 lines, or with 4+ H2 sections, lists its H2 headings as sub-bullets. This is what
makes *section-level* placement possible — the difference between "this belongs in `onboarding.md`"
and "this belongs under `## Compliance checks` in `onboarding.md`".

```
- `banking/processes/onboarding.md` - client onboarding end to end, from lead to open account
  - `## Intake` - forms collected, required client data
  - `## Compliance checks` - KYC, sanctions screening, escalation thresholds
  - `## Account opening` - system steps and who approves what
```

Small notes get no sub-bullets. Don't pad.

**Anchors are GitHub-style slugs**: lowercase, drop everything that is not a word character, space
or hyphen, then spaces to hyphens. `## Target Market (MiFID)` → `#target-market-mifid`. This is what
every section-level link in the vault depends on, and what silently breaks when a heading is
renamed — `scripts/scan_vault.py` records each note's real slugs so `graph.py query --broken` can
find the casualties.

## Structure

Root `index.md`, in this order:

1. `# <Vault name> - Index`
2. A blockquote header: what this file is, and how to keep it current
3. `## How to use this index` — the two lookup/placement instructions
4. `## Conventions` — what this vault does, detected once and recorded so later runs match it:
   link style, frontmatter fields, naming style, date format, attachments location
5. `## Business Glossary` — the vault's own vocabulary, one line per term
6. `## Contents` — one line per top-level folder and root-level file
7. `## Recently changed` — only on a `refresh` run; dropped on a fresh build
8. `## <folder>/` — one section per top-level folder, with its `Place here:` line and its entries

Vocabulary comes before routing because the routing lines use the vocabulary.

Use nested bullet lists throughout — see "Never use a markdown table in an index" above.

The full shape is in `assets/templates/index-root.md`. Per-folder indexes use
`assets/templates/index-folder.md`.

## A folder with no notes yet

Every folder is empty the moment a vault is created, so this is the **normal** case at `init` time,
not an edge case. Write the `Place here:` line and nothing else:

```markdown
## regulatory/

Place here: the regulatory rules the bank is bound by — MiFID, WpHG, advisory duties.

_No notes yet._
```

Do **not** invent a placeholder structure for the emptiness — no empty table, no `| | (empty) |`
row, no `- (none)` bullet pretending to be a file entry. An empty folder's routing line is the whole
point of it; the file list arrives when files do.

## Splitting

The root index stays under ~350 lines. When a folder is large enough to threaten that:

- **Threshold**: a folder with more than ~15 files gets its own `index.md` inside it.
- The root `## <folder>/` section then holds only the `Place here:` line, the file count, and a
  pointer: `See banking/index.md for its 34 notes.`
- A per-folder index has the same shape minus `## Conventions` (inherited from root) and lists that
  folder's own subfolders and files.
- Splitting is decided **before** writing any section content, from the scan counts — never
  mid-write. Nothing gets renamed or moved after the fact.

Nested splits (a subfolder inside an already-split folder getting its own index) apply the same
threshold, but stop at two levels deep. Deeper than that, list the files inline.

## Ordering

Folders in the `## Contents` list and their `## <folder>/` sections appear in the **same order**,
and that order is: the most-used/most-central folders first, then the rest alphabetically. A folder
that is clearly an archive, inbox, or scratch area goes last regardless of name.

Within a folder section: subfolders first, then loose files, each alphabetically.

## Line budgets

| File | Budget | Split rule |
|---|---|---|
| Root `index.md` | ~350 lines | Move the largest folders to their own `index.md` per Splitting above |
| Per-folder `index.md` | ~350 lines | Split its largest subfolder out, to a max of two levels |
| `## Business Glossary` | ~50 lines | Push folder-local terms down to per-folder indexes |
| One write operation | ~200 lines | Write one `## <folder>/` section per operation |

## What never goes in the index

- File sizes, line counts, mtimes — that's the manifest's job, and it goes stale instantly
- Content quotes or excerpts — the index routes, the file answers
- Anything not present in the vault: no aspirational folders, no "TODO: add notes about X"
- Glossary entries for terms the vault never uses, or definitions taken from general knowledge —
  the glossary describes *this* vault's vocabulary, not a domain's
- `.obsidian/`, `.git/`, `node_modules/`, `.wiki/`, `.rag/`, attachments and binary folders
- Restating the vault's purpose at length — one blockquote line is the whole allowance

## Staleness

The header blockquote always tells the reader how to refresh the index. `.wiki/manifest.json`
holds the per-file state the next `refresh` diffs against; the index itself carries no timestamps,
so that a note-only edit doesn't produce a misleading "generated on" date at the top.

Staleness is also corrected opportunistically: any task that reads a file and finds its index entry
wrong fixes that entry on the spot, per `references/index-repair.md`. So the parts of the index that
get used most stay the most accurate, without anyone having to run a refresh.
