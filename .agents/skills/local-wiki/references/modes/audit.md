# Audit mode

<!-- sync: local-wiki-modes v5 -->

A health check on the vault, its index, and its link graph. Reports findings; the only files it
modifies are the index files themselves and `see-also.md` files — routing infrastructure this skill
generates, not user-authored note content.

**Inputs**: the vault root, `.wiki/manifest.json`, the index files, the graph.
**Outputs**: a findings report, plus index-only and `see-also.md`-only fixes.

Audit is the **proactive** sweep. `references/index-repair.md` is the reactive counterpart that fires
mid-task on whatever a run trips over. Same conflict taxonomy, same authority boundary — read that
file for the definitions rather than re-deriving them here.

## Workflow

1. `scripts/scan_vault.py` against the current tree.
2. `scripts/graph.py scan --full` so link findings are computed from current files, not a stale
   cache.
3. Compare the scan, the graph and the index; collect the findings below.
4. Fix the index-only and `see-also.md`-only issues directly.
5. Report everything else with a recommendation — don't move, merge, or delete notes.

## What to look for

<!-- profile-hook: audit-checks -->

**Index drift** — entries pointing at files that no longer exist, files absent from the index, files
that moved, folder sections with no `Place here:` line.

**Description quality** — file lines that merely restate the filename, notes over ~150 lines or with
4+ H2s and no heading sub-bullets, `Place here:` lines too vague to route with.

**Link health** — four queries, not a hand-rolled sweep:

```bash
python3 .agents/skills/local-wiki/scripts/graph.py query --broken   --vault <vault>
python3 .agents/skills/local-wiki/scripts/graph.py query --oneway   --vault <vault>
python3 .agents/skills/local-wiki/scripts/graph.py query --orphans  --vault <vault>
python3 .agents/skills/local-wiki/scripts/graph.py query --hubs     --vault <vault>
python3 .agents/skills/local-wiki/scripts/graph.py query --components --vault <vault>
python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> stats --json
```

- **Broken** — dead targets and dead anchors (a heading was renamed). Fixable directly: the link is
  routing infrastructure once the target is identifiable. A link whose target genuinely no longer
  exists is reported, not silently deleted.
- **One-way** — A links B with no back-edge. Report with the suggested `## Related` line; adding it
  edits note content, so it is a finding unless the user asks for it.
- **Orphans** — notes nothing links to. In a vault whose `README.md` links every folder,
  an orphan is usually a note filed without its relation step, and worth flagging.
- **Hubs** — a note with an unusually high degree. Often a note that should be split, and the
  strongest structural signal the graph gives.

**Duplicates and orphans** — notes covering the same topic under different names (report as merge
candidates, naming which is better established), notes nothing links to and no index line describes.

**Structure** — notes past ~400 lines or 8+ H2s (split candidates), folders past ~15 files with no
per-folder index, folders holding one file, notes whose content belongs in a different folder.

**Architecture fit** — when reporting structural findings, judge them against
`references/domain-architecture.md` → Structure Evolution and Existing Vault Behavior: has a stable
new category emerged, has a folder become a junk drawer, does the hierarchy still match the
material? Report the finding and the reasoning; restructuring is a `refactor` run, never an audit
action.

**Reorganization pressure** — per `references/tracking.md`, compare against
`.wiki/wiki-config.json`: `last_reorganized_at` past `reorg_stale_days`, or any folder's note count
past `reorg_folder_notes`. Report it as a finding here regardless of role; only the *prompt* to run
a reorganization is admin-gated.

**Glossary** — every `(inferred)` entry listed for review (this is the point of marking them),
`undefined` entries, terms in 2+ notes with no entry, variant terms still present in note text with
per-file counts.

**Tags** (`references/tagging.md`) — `python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> check`, every failure line as it prints (a tag the
inventory lacks, a node nothing carries, a node with no parent, a malformed tag, a node listed
twice), each naming the command that clears it. Its warnings, quantified: nodes over the split
threshold, nodes with no meaning line, one leaf name under two parents. The untagged count per
folder, from `python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> pending --limit 0`; a large one is the signal to run `tag`. Audit reports these;
listing a node or setting a tag edits the vault, which is `tag`'s or `update`'s job.

**Validation backlog** — count `.wiki/todos_validations.md`'s open boxes, and flag any note carrying blank
`validated from:` fields with no corresponding entry, or vice versa. The two drifting apart means a
validation was recorded in one place only.

**Knowledge gaps** — count `.wiki/wiki_gaps.md`'s open questions, and flag any the vault can now answer:
material has been added since they were logged, and a gap that is now covered should be closed.

**Contributors** — `contributors.py query --stats`. One line: how many contributors, how many
changes, how many files touched. Never the raw log.

**Semantic index** — `.rag/bin/rag status`. One line: files indexed versus files in the vault, plus
any warning. A stale index is a finding with `.rag/bin/rag update` as the recommendation — audit
writes nothing, so it does not run the update itself.

**Conventions** — notes deviating from standard markdown (a wikilink, missing frontmatter where
every other note has it), grouped with counts.

**`--components` is the one to lead with.** An orphan count says how many notes are unreachable; a
component count says whether this is one body of knowledge or several that never learned about each
other. Report each island by size and a few members, and name the note it should connect to.

**Learning health**, when `.wiki/agent-memory/` exists — from `memory.py stats`, which reads the
rollup and never the log: corrections per 100 writes (flag above ~15 or rising), rules loaded (flag
0 while corrections are high — run `learn`), rules deprecated recently (2+ means the rules being
written are too broad), open episodes never closed (over ~30 means nothing can be learned), and
proposals open past 30 or older than 90 days. Never promote a rule here; audit reports, `learn`
consolidates, `memory.py promote` decides.

**Queue hygiene.** `.wiki/todos_validations.md` and `.wiki/wiki_gaps.md` are queues, not ledgers:
report the **open** count and move ticked or answered lines older than 90 days to
`.wiki/archive/<file>-<year>.md`. `.wiki/conflicts_ignored.md` is append-only — archive by year past
~200 lines, never delete. If `episodes.jsonl` is past its rotation threshold, run `memory.py rotate`.

## Report shape

Group by category, most actionable first. Each finding: the path, the issue in one line, the
recommendation. Lead with a one-line summary of vault size and overall state.

Fixed automatically (index and `see-also.md` only): list briefly.
Needs a decision: list with the recommendation, and stop there.

## Rules

- **Audit never edits note text.** The in-place edits `update` may make — normalizing a term,
  closing a question, inserting a link — are findings here, not actions.
- **Never move, merge, rename, or delete a note.** Those are reported, never performed. An audit
  finding is raw material for a reorganization, not permission to act.
- **Don't report style preferences as problems.** A convention only counts as a deviation if the
  vault is otherwise consistent about it.
- **Quantify.** "14 notes missing frontmatter" is actionable; "some notes are inconsistent" isn't.
- **An empty audit is a good result** — say so plainly rather than manufacturing findings.

## Closeout

End with the checklist (`SKILL.md` → Closeout checklist). For `audit`:

session startup (READY token) · scan run · **search stated** · graph rescanned · findings reported (count) ·
index fixes applied (count) · nothing else modified
