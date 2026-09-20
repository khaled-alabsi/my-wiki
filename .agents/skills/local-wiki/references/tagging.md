# Tagging: a tree of subjects, carried by the notes

<!-- sync: local-wiki-tagging v1 -->

A tag says what a note is **about**. Tags form a **tree**: a general subject such as `banking` is a
node, a more specific subject sits inside it as `banking/accounts`, and any node may branch again.
The tree is there to be walked. A reader starts at a general node and steps down until the notes
under the node are the ones they came for.

**The agent decides the tags. A script only carries the decision out.** Which subjects a note is
about is a judgement made from the note and from the tree the vault already has. `scripts/tags.py`
writes that judgement into the note and into the tree, and refuses whatever would let the two
drift apart. It never chooses a tag.

**Read this when** a run tags a note, walks the tree to search, or reshapes the tree.

## What a tag is, against the three things it is not

| Thing | Says | How many per note |
|---|---|---|
| **Folder** | where the note lives | one |
| **Link** | that this note relates to that note, and why | as many as are real |
| **Glossary term** | what a word means in this vault | none, a term belongs to the vault |
| **Tag** | which subjects the note is about | one to five |

- **A tag that restates the folder earns nothing.** A note in `regulation/` tagged `regulation`
  says the same thing twice. Tag what the folder does not already say: the second subject of the
  note, or the narrower one inside the folder's subject.
- **A glossary term is not automatically a tag.** `SCA` is a word the vault defines. It becomes a
  tag only when notes are *about* it, not when they merely use the word.
- **A tag is not a relation.** Two notes that share a tag are about the same subject. That they
  relate to each other is a link, with a stated reason (`references/linking.md`).

## Tags never decide where a note goes

Placement is decided by what the note is and what owns it
(`references/knowledge-organization.md`, Rule 1 and the keyword-routing anti-pattern). A tag
describes a note once it is understood. It is never the reason a note lands in a folder.

In a search, a tag **boosts a shortlist**: the notes under a node join the candidates. Every one of
them is still opened before anything is written from it or cited.

## The tree

- **A tag is a full path.** Segments joined by `/`: `regulation/mifid/target-market`. That is the
  form in the note, in the inventory and in every query.
- **A child implies every ancestor.** A note tagged `regulation/mifid` is under `regulation`. The
  ancestor is never written beside it. `tags.py` drops it, and `check` warns when it finds one.
- **One parent per node.** It is a tree, never a graph. A subject that seems to fit two parents is
  created **once**, under the parent whose meaning it narrows. A note that really is about both
  subjects carries **two tags**. Several memberships live on the note, never in the tree.
- **Never the same leaf name under two parents.** `payments/sca` and `security/sca` are one
  subject listed twice. `check` warns.
- **Depth of four at most.** A deeper path is a folder tree wearing a tag's name.
- **A node is split when it directly carries more than `tag_branch_notes` notes** (default 25, in
  `.wiki/wiki-config.json`). Past that the node has stopped narrowing anything. Create the children
  that the notes under it actually fall into, then move the notes down one at a time with
  `tags.py set`.
- **A node is renamed, re-parented or merged only through `tags.py move`.** It rewrites the
  inventory and every note that carries the node or a descendant, in one step.

## What earns a node

A subject earns a node when **one** of these holds:

- two or more notes are about it,
- the vault defines it (it has a note or a glossary entry of its own),
- it narrows a node that is over the split threshold.

One note about a subject nothing else mentions does not earn a node. It takes the nearest existing
node instead.

## Reuse before creating: the ladder

Asked of every subject, against the inventory, **in this order**. It is the glossary's alias
ladder (`references/glossary.md`) applied to subjects.

| Rung | Test | Action |
|---|---|---|
| **Certain** | A node's name or one of its `aka` names is this subject | Use that node |
| **Likely** | The subject narrows an existing node, and does not yet meet "What earns a node" | Use the **parent**. Add the child later, when a second note needs it |
| **New** | No node covers it, and it earns a node | `tags.py add <path> --meaning "..."`, parents first, then use it |
| **Never** | It fits no node and does not earn one | No tag for this subject. Never a synonym of an existing node, never a node for one note |

Look the inventory up by slice, never by reading it whole:

```bash
grep -iF "<word>" <vault>/.wiki/tags.md
python3 scripts/graph.py --vault <vault> query --tag-tree [<node>] --json --limit 25
```

## Per note

- **One to five tags**, the most specific node each time.
- **Evidence comes from the note.** What it states, its headings, its first lines. Never from what
  the model knows about the subject in general.
- **Agent-made nodes are lowercase kebab-case**: `target-market`, never `TargetMarket`.
- **Tags a note already carries are kept.** A vault that arrives with tags has decisions in it.
  They are listed in the inventory as they are, and reshaped only by a `tag` run, through `move`.

## The mechanics

**In the note**, one frontmatter line, one written form:

```yaml
tags: [regulation/mifid/target-market, payments/sca]
```

`scan_vault.py` *reads* every form a vault may already hold: a block list, a comma scalar, a
leading `#`, quotes, any letter case. Identity is the casefolded path, so `Banking/MiFID` matches
the node `banking/mifid` without the note changing. **Only `tags.py` writes**, and it writes the
form above. A `#hashtag` in the body of a note is prose and is never read as a tag, because lifting
it into the frontmatter would rewrite the note.

**A segment** is letters, digits, `_` and `-`, and is not all digits. No space, `:`, `,`, `[`, `]`,
`#` or quote. A malformed tag is reported by the scan and failed by `check`. It never stops a scan.

**The inventory** is `.wiki/tags.md`, the single source of the tree. One node per line, flat full
paths, sorted by segment:

```markdown
- `regulation/mifid/target-market` — Who a product is designed for. (aka zielmarkt, tm)
```

- The backticks make both slices exact: `` grep -F '`regulation/mifid' `` returns the node and its
  whole subtree, `` grep -F '`regulation/mifid`' `` returns the one node.
- **No counts in the file.** A count changes with every tagged note and is derived. `query
  --tag-tree` serves it.
- **Growth: budgeted.** At most `tag_nodes_max` nodes (default 300). **Eviction:** the leaf that
  the fewest notes carry is merged into its parent, `tags.py move <leaf> <parent>`. **Enforcement
  point:** `tags.py add` counts the nodes before it writes, exits 3 at the cap and prints the five
  cheapest merges.
- **One writer at a time.** Every command is a read-modify-write of that one file, and an agent
  that fires several `add` calls in one block runs them at once - so each holds an exclusive lock
  (`.wiki/.tags.lock`, empty, derived, git-ignored) for its read-check-write cycle. That file is
  created once and **never deleted**: deleting it on release is what makes a lock stop locking,
  because a process still waiting on the old inode and one arriving afterwards open two different
  files and both proceed. Measured without the lock: 12 parallel `add` calls, 12 reported success,
  10 landed.
- **Access:** written only through `tags.py` (`add`, `move`, `drop`), never opened to edit.
  `update`, `intake`, `ask` and `where` slice it as above. `tag` and `audit` read it whole, once
  per session, because they reason about the shape of the entire tree.

**The commands:**

| Command | Does | Refuses |
|---|---|---|
| `tags.py add <path> [--meaning] [--aka a,b]` | lists one node | exit 2 when the parent is not listed, naming the parent's `add`. Exit 3 at the cap |
| `tags.py set <note> [--add T] [--remove T]` | rewrites the note's one `tags` line and nothing else | exit 2 when a tag is not in the inventory, naming the `add` to run first |
| `tags.py move <old> <new>` | renames, re-parents or merges a node and rewrites every note under it | exit 2 when `<new>` is under `<old>` or its parent is missing |
| `tags.py drop <path>` | removes an empty leaf | exit 2 when a note carries it or it has children |
| `tags.py check [--json]` | compares the notes and the tree, live | see below |
| `tags.py pending [--scope] [--limit] [--json] [--retag]` | the notes still to tag, as outlines | exit 2 with no manifest, naming the scan |
| `tags.py init` | creates the empty inventory when the vault has none | never |

The refusal on `set` is what keeps the inventory complete. A tag cannot reach a note before it is
in the tree, so "a tag that never occurred before is added to the inventory in the same run" is
something the tool enforces, never something a run has to remember.

## The consistency command

```bash
python3 scripts/tags.py --vault <vault> check
```

**A run that wrote a tag ends with it, and a non-zero exit is cleared in that same run.** Every
failure line names the command that clears it. It reads the notes and the inventory as they are on
disk, so it has no scan to be behind.

| Exit 1 when | Cleared by |
|---|---|
| `unlisted`: a note carries a tag the inventory lacks | `tags.py add` |
| `unused`: a node that no note carries, itself or through a descendant | `tags.py drop`, or tag the notes it was made for |
| `orphan`: a node whose parent is not listed | `tags.py add <parent>` |
| `malformed`: a tag that breaks the grammar | `tags.py set` on the note, which drops it |
| `duplicate`: a node listed twice | delete the second line |

Warnings, which never fail: an ancestor beside its descendant, more than five tags on a note, a
path deeper than four, a node over the split threshold, one leaf name under two parents, a node
with no meaning line, the inventory past 90% of its cap.

## Who maintains it

| Mode | Does |
|---|---|
| `init` | Creates the empty inventory (`tags.py init`) |
| `adopt` | Creates the inventory and lists the tags the notes already carry, parents first. Changes no note |
| `update`, `intake` | Tags every note they create or extend, by the ladder. `add` for new nodes, then `set`. End with `check` |
| `where` | Says which tags it would set. Writes nothing |
| `ask` | Expands the question through the tree and adds the notes under the matching node to the shortlist. Writes nothing |
| `tag` | Tags the notes of a vault that already exists, shapes the tree, fills missing meaning lines (`references/modes/tag.md`) |
| `audit` | Runs `check`, reports the untagged count, the nodes over the threshold and the nodes with no meaning |
| `refresh`, `indexing` | Run `check` and report. Tag nothing |
| `refactor` | A merged note carries the union of its sources' tags. A split note has its tags decided again per part |
| The UI | The owner adds and removes chips. The server lists a new tag in the inventory as part of the same save (`references/ui.md`) |

A node the UI listed has no meaning line yet. The next `audit` reports it and the next `tag` or
`update` that touches the node fills it in.
