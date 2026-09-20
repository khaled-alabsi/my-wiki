# Update mode (and where)

<!-- sync: local-wiki-modes v5 -->

The default path. Takes material the user hands over and puts it in the right place in this vault,
without asking where it goes.

`where` runs steps 1–6 and then stops, reporting the decision and writing nothing at all.

**Inputs**: the incoming material, the vault root from `vault-profile.md`.
**Outputs**: edited or created notes, updated index entries, relation links, a report.
**Reads**: `references/ingest-sources.md` for step 3, `references/glossary.md` for steps 3 and 6a,
`references/placement-rules.md` for step 6, `references/note-shaping.md` for step 11,
`references/open-questions.md` for step 12, `references/linking.md` for step 11,
`references/conflict-detection.md` for step 5, `references/git-safety.md` for step 2,
`references/tracking.md` throughout, `references/rag.md` wherever search is needed,
`references/index-repair.md` throughout.

The vault's conventions are **already known** — `vault-profile.md` records them, and they are
standard markdown. Never re-detect them, and never impose a different style.

## Workflow

### 1. Session startup

Per `references/tracking.md` → Session startup: registration check, first-run check, reorg-staleness
check, in that order. Runs once per session, not once per write.

### 2. Git safety — once per session, before the first add

Per `references/git-safety.md`. A diverged checkout blocks every add until the user resolves it. Not
a git repo, or no tracked upstream → skipped silently. Already checked this session → skipped.

`where` skips this entirely: it writes nothing, so there is nothing to protect.

### 3. Normalize the incoming material

**Load `.wiki/domain-context.md` first.** It carries the vault owner's standing knowledge about
this domain — canonical terminology, which identifier is authoritative, rules that are always true
here, how material in this domain should be handled. It is short by design and read in full.

It changes decisions this step is about to make: which term the note is written in, whether two
things are the same concept, which source wins when notes disagree. Reading it after placing the
material is too late.

Empty or absent → carry on, that is the normal state of a young vault.

Per `references/ingest-sources.md`, reduce whatever was supplied to an intake summary: topic, key
facts, entities, terms (resolved against the index's `## Business Glossary`), tags (the subjects
the material is about, each resolved against this vault's tag tree by the ladder in
`references/tagging.md`), open questions, and shape.

Run `references/placement-rules.md` → Rule 0 (the delta pass) once the destination is open: every
claim gets a verdict — present, sharper, conflicting or new — and only `new` and `sharper` are
written. The counts go in the report.

Do not write anything to the vault yet, and do not add anything the source didn't contain.

**A transcript is not one intake summary.** A recording of a presentation or a discussion segments
into several units first — each with its own topic, shape and destination — and each is routed from
step 3 on its own. Never carry a whole recording through this workflow as a single item
(`references/ingest-sources.md` → Recordings, presentations and discussions).

### 4. Route via the index

Match the topic and entities against the index's `Place here:` lines, then file `covers` lines, then
H2 sub-bullets. Produce a shortlist of up to 3 candidates.

Search directly for the entity names too, and — since this vault has a `.rag` workspace — run one
semantic search here (`references/rag.md`). It is the cheapest way to catch a near-duplicate phrased
differently, which is exactly what grep misses.

The tag tree adds candidates too: for a subject that resolved to a node,
`python3 .agents/skills/local-wiki/scripts/graph.py query --tag <node> --json --limit 10 --vault <vault>` lists the notes under it, and they join
the shortlist to be opened like any other. A shared tag never decides where material goes
(`references/tagging.md`).

`graph.py query --neighbors` on a strong candidate is the other cheap probe: it says what is already
connected to that note, which often surfaces the better destination.

Conflicts surface here as routing failures. Repair them now, per `references/index-repair.md`, and
rebuild the shortlist from the corrected index.

### 5. Read the candidates, then check for contradiction

Open the top candidates. The index says what a file is *about*, not what it already *says*.

Then apply `references/conflict-detection.md`: does the incoming material **contradict** something
already in the vault — not merely duplicate it? If it does, the user is asked before the write
completes. Override means the agent fixes the existing content; ignore means the incident is logged
to `.wiki/conflicts_ignored.md` and nothing existing changes.

**No content is written while a real conflict is unresolved.**

### 6. Decide the placement

<!-- profile-hook: update-classify -->

**Load what this vault has already learned**, before reasoning from scratch:

```bash
python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> rules --scope placement
python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> rules --scope linking
```

About a dozen lines, only rules that reached `validated` (`references/agent-memory.md`). These are
corrections this vault's owner already made. **A rule that changes the decision is named in the
report, by id** — so they can correct the rule, not just the note. No rules yet is normal.

Ask the graph what surrounds each candidate destination, too:

```bash
python3 .agents/skills/local-wiki/scripts/graph.py --vault <vault> \
    query --neighbors <candidate> --depth 1 --json --limit 10
```

A destination one hop from three near-identical notes is a **merge candidate** — retrieval finds
the notes, only the graph shows they already cluster.

**Then run `references/knowledge-organization.md` — it is the reasoning, and this step is the
result of it.** Do not start from "which folder name resembles this?". Start from "what knowledge
object is this, what already owns that concept, and what will this look like after another 10-30
notes on the subject arrive?"

In particular it decides, before any ladder is applied:

- whether the material is one knowledge unit or several that should be **split**;
- whether a **canonical note already exists** that should be extended instead of duplicated;
- which folder holds **primary ownership**, as opposed to the domains that merely get links;
- whether a **new folder is justified**, or whether it would be a folder-per-note;
- whether existing notes are misfiled — **reported for `refactor`, never moved while filing.**

Then apply `references/placement-rules.md` in its stated order: merge into an existing section, add a new
section, create a new note, or — only on a genuine tie — ask. Then apply its
Cross-referencing rule to the rest of the shortlist.

### 7. Settle the vocabulary

Per `references/glossary.md`: new terms get entries in step 12; known variants follow the confidence
ladder; a contradicted definition is a step-5 conflict, not a silent glossary rewrite.

Settle the tags in the same pass, per `references/tagging.md` → Reuse before creating: which
existing nodes the note will carry and which new nodes it needs. One to five, the most specific
node each time.

### 8. Decide the form

Per `references/note-shaping.md`. The destination's existing form wins.

### 9. Answer what the material left open

Per `references/open-questions.md`, resolved against this vault only. Cap at 5. Only a vault-sourced
answer closes a question.

**`where` stops here.** It reports the placement decision, the runner-up, cross-reference
candidates, and what 10–12 *would* do, the tags it would set included — and writes nothing: no note text, no index, no glossary, no
links, no `rag update`, no `graph.py scan`, no contributors entry. It lists index conflicts
**without fixing them**.

### 10. Ask the validation question, then write

Per `references/tracking.md` → Validation gate: ask whether the user is 100% sure this content is
correct. Unsure → a checkbox in `.wiki/todos_validations.md` plus blank `validated from:` /
`validated at:` fields on the note.

Then write, following standard markdown and the form decided in 6b:

- **Merging into a section**: append, keeping the section's structure. Never reflow what's there.
- **New section**: insert where its topic implies, not reflexively at the end.
- **New note**: frontmatter per `references/tracking.md` → Provenance, an H1, then the content.
- **Multi-step process or decision tree** → also an inline ` ```mermaid ` block.
- Term normalizations and question closures land in this same edit.
- **Tags**, on every note this run created or extended, only through the tool and never typed into
  the frontmatter by hand. New nodes first, parents first, then the note:

  ```bash
  python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> add <node> --meaning "<what it covers>"
  python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> set <note> --add <tag> [--add <tag>]
  ```

  `set` refuses a tag `.wiki/tags.md` lacks and names the `add` to run, which is what keeps the
  inventory complete. A note that is already tagged gains a tag only when the new material brought
  a subject it did not have.

Stay under ~200 lines per write operation.

**Before writing to an existing note**, run the recently-touched heads-up:

```bash
python3 .agents/skills/local-wiki/scripts/contributors.py query \
  --path <note> --since-hours 24 --vault <vault>
```

Exit 0 means someone else touched it recently — mention it. Exit 1 is the normal case.

### 11. Link it to what it relates to

Per `references/linking.md`: inline links on first occurrence, a `## Related` back-edge in each
target, GitHub-style anchors, a stated reason per link, capped per note.

`graph.py suggest --path <the note>` proposes candidates; **you** decide which are real and write
the reason. A suggestion is never an answer.

### 12. Validate any diagram you wrote

If the note you just wrote or edited contains a ` ```mermaid ` block, validate it before going any
further:

```bash
python3 .agents/skills/local-wiki/scripts/mermaid_validator.py <the note>
```

Exit 1 → fix what it names and re-run. A diagram that does not render is a defect in the note, and
this run put it there (`references/ingest-sources.md` → Validate every diagram you write).

### 13. Update the index

Only what changed: the file's `covers` line, a new file line, new H2 sub-bullets, the glossary
entries settled in 6a, and any repairs from steps 4–5. Then `.wiki/manifest.json`.

### 14. Record, refresh, and report

In this order, once, at the very end:

```bash
python3 .agents/skills/local-wiki/scripts/contributors.py record \
  --user-id <user_id> --path <each changed file> --type added|edited --vault <vault>
python3 .agents/skills/local-wiki/scripts/graph.py scan --since-manifest --vault <vault>
python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> record --mode update \
  --decision place --target <where it went> --alternatives <runner-up> \
  --rationale "<why this one>" [--applied-rule RULE-017] --user-id <user_id>
python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> promote --json
.rag/bin/rag update --quiet
python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> check            # only when this run set a tag
```

`tags.py check` exiting non-zero is cleared now, by the command each failure line names
(`references/tagging.md` → The consistency command).

Never per file. Never `rag index --full`. Never in `where` mode. On `rag` failure, report the
command once and move on — a stale semantic index degrades search, it breaks nothing.

**Record the decision that could have gone another way** — the placement, a split, a merge, a new
folder, a dedupe-skip. Not reads, not searches: a log of inevitabilities buries the corrections that
matter. **`promote` announces itself** — any promotion or demotion it prints goes in this run's
report, by id and text, because promotion is automatic and silent behaviour change is what that
would otherwise cost.

**When the user corrects an earlier placement**, close that episode in the same run:

```bash
python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> close \
  --id EP-238 --outcome corrected --correction <where it should have gone>
```

The correction is the valuable half of the record (`references/agent-memory.md`).

## Report

Where it went (full path, and the section if it merged), which rule fired, the runner-up if it was
close, cross-references added, and anything flagged.

Then these blocks, each omitted entirely when empty, in this order:

```
Questions answered (2):
- "escalation threshold?" -> 15,000 EUR — regulatory/escalation-matrix.md ## Limits
Left open (1):
- "does this apply to professional clients?" — nothing in the vault covers it

Terms normalized (1):
- processes/onboarding.md — PEP -> PIP (1 occurrence)

Links added (3):
- processes/onboarding.md -> regulatory/mifid.md#target-market — the check this step performs
- regulatory/mifid.md ## Related -> processes/onboarding.md — back-edge

Glossary (1 added):
- BPKN — inferred from usage in 3 notes; worth checking

Tags (2 set, 1 node added):
- processes/onboarding.md — banking/accounts/onboarding, regulation/mifid
- new node: banking/accounts/onboarding — taking on a new client

Index repairs (1):
- regulatory/mifid.md — description didn't match content, rewrote it

Validation: logged to .wiki/todos_validations.md (user wasn't certain).
Heads-up: processes/onboarding.md was edited by bob@example.com 3h ago.

.rag index updated (2 files re-embedded). Graph updated (3 edges).
```

- **Nothing dropped** — the completeness check from `references/ingest-sources.md` → Lose nothing:
  every claim in the material has a destination, or is listed here with which of the four drop
  reasons applied

Don't narrate the search. The user wants to know where their note went.

## Closeout

End with the checklist (`SKILL.md` → Closeout checklist). For `update` the mandatory lines are:

session startup (READY token) · git safety · conflict check · validation gate · note written · links ·
index updated · contributors recorded · graph rescanned · **search stated** · search index refreshed

`where` writes nothing, so its closeout is a single line saying so.

## Edge cases

- **Material covers two unrelated topics** — split it, place each part, report both.
- **Material is already in the vault verbatim** — write nothing, report the duplicate with its path.
- **Near-duplicate note exists** — merge into the better-established one and flag the other for
  `audit`. Don't create a third.
- **No folder fits** — create one at the shallowest sensible level, give it a `Place here:` line
  immediately, and flag it prominently. A brand-new top-level folder in a vault whose structure was
  deliberately accepted at `init` is worth saying loudly.
- **The material is a correction to an existing note** — that's the step-5 conflict path.
- **The user supplied a destination** — it wins outright for the primary placement. Step 4 still
  runs, but only to find secondary fits and link targets.
- **The git check fails** — nothing is written. Report the resolution commands and stop.
- **`contributors.py` fails** — report it and continue. Losing one provenance entry must never cost
  the user their note; a broken tool is reported, not worked around silently.
