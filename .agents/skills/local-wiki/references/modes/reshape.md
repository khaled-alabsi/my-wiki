# Reshape mode — moving this vault to a different domain or structure

<!-- sync: local-wiki-modes v5 -->

The vault was set up for one domain and should be about another: "this is a banking wiki, make it an
AI research wiki", "the structure is wrong, start it over as X". Reshape changes what the vault
**is** — its domain, its folder structure, its vocabulary, its routing — rather than what is in it.

**Two axes, independently or together:**

| Axis | Changes | Example |
|---|---|---|
| **Domain** | what the vault is *about* | banking → AI research |
| **Knowledge profile** | what *shape* its knowledge takes, and the instructions this skill runs by | none → `process-knowledge` |

Adopting a profile is the second axis and it is not cosmetic: it re-derives the folder structure
from that profile's knowledge types **and re-applies its overlay to this skill's own instructions**,
so `update`, `intake`, `refactor`, `audit` and `ask` all start following the new doctrine. That is
why it sits behind the same gate as a domain change rather than being a setting.

**The expected case is a vault initialized a day ago with the wrong domain.** That is cheap and
safe: there is nothing to lose. A vault with a year of notes is a different proposition entirely,
and this mode is deliberately reluctant about it.

**Inputs**: the new domain, and optionally a structure to use.
**Outputs**: a new folder structure, a rewritten `index.md`, an updated `vault-profile.md`,
`.wiki/wiki-config.json` and `.wiki/structure-accepted.md`, a rebuilt graph and search index, a
report — **after** you accept a plan.
**Reads**: `references/domain-architecture.md` (this is the mode it was written for),
`references/knowledge-organization.md`, `references/index-format.md`, `references/tracking.md`,
`references/git-safety.md`, `references/agent-memory.md`.

Never inferred. The user asks for it by name — reshaping a vault because a prompt mentioned another
subject would be a catastrophe.

## What it may and may not do

| May | May not |
|---|---|
| Create, rename and remove folders | **Delete a single note.** Anything displaced goes to `.wiki/.trash/` at its original path |
| Move notes into the new structure | Rewrite the prose of any note |
| Rewrite `index.md` and its glossary wholesale | Touch `.wiki/contributors.json` — who wrote what does not change because the subject did |
| Rewrite `vault-profile.md` — the one mode that may, since the domain *is* its content | Silently discard `.wiki/domain-context.md` — see step 5 |
| Reset learned rules | Delete `.wiki/agent-memory/episodes.jsonl` — history is history |
| Swap the knowledge profile and re-apply its overlay | Hand-edit the spliced instructions — that is `apply_profile.py`'s job, and a hand-splice drifts on the next regeneration |

## Step 1 — session startup, git safety, and measure the vault

`references/tracking.md` → Session startup, then `references/git-safety.md`. A reshape is the single
largest change this skill can make; doing it on a diverged checkout is indefensible.

Then **measure before proposing anything**:

```bash
python3 .agents/skills/local-wiki/scripts/scan_vault.py \
  --root <vault> --out .wiki/manifest.json --previous .wiki/manifest.json
```

From the manifest: the note count, the total line count, how many notes have real body content
(more than ~15 lines), how many folders, and how many notes carry `validated at:`.

## Step 2 — the weight check, and what it changes

**Say what is in the vault before saying what you would do to it.** The user asking for this
probably believes the vault is nearly empty; the check is there for when they are wrong.

| Weight | Signal | What happens |
|---|---|---|
| **Fresh** | ≤10 notes, none over ~15 lines, no `validated at:` | Proceed to a normal plan. Seeded scaffolding is not content, and re-scaffolding costs nothing |
| **Started** | ≤40 notes, or some notes with real content | **Warn, with numbers**, then plan. Every note is carried into the new structure — none is dropped for not fitting |
| **Heavy** | over 40 notes, or any validated content, or more than ~2,000 lines | **Warn hard and do not offer re-scaffolding at all.** Only the migrating shape below is on the table, and say plainly that `refactor` may be the better tool |

The warning is concrete, never vague:

```
This vault is not empty.

  63 notes across 9 folders, 4,180 lines
  22 notes have real content (more than 15 lines)
  3 notes are marked validated — somebody checked those personally
  oldest note: 2025-11-04, newest: 2026-08-14

Reshaping to `ai` will restructure all of it. Nothing is deleted — displaced notes go to
.wiki/.trash/ — but the folder structure, the index and the glossary are replaced, and every
note that does not fit the new domain has to go somewhere.

If what you actually want is to reorganize the banking material, that is `refactor` and it
keeps the domain. Reshape is for changing what this vault is about.
```

Then stop and let them answer. **A heavy vault never proceeds on an implied yes.**

## Step 2b — settle the profile, if that is what is changing

If the request names a knowledge profile — or changes the domain in a way that makes the current one
wrong — ask which profile the reshaped vault should use, exactly as `init` does: the available ones
one line each, plus `none`. Never pick silently.

**Changing the profile alone is a valid reshape.** The domain stays, the folders are re-derived from
the new doctrine, and this skill's instructions are re-spliced. Say plainly that this changes how
every future note is classified and placed, not just where the existing ones sit.

**Keeping the profile is also valid** — a domain change with the same doctrine re-derives the
structure from the profile's types applied to the new domain.

## Step 3 — propose the new structure

Run `references/domain-architecture.md` for the new domain, exactly as `init` did for the old one:
classify the domain, work out its knowledge dimensions, apply the growth test. Do not translate the
old folders into new names — a banking structure with AI labels is a banking structure.

**With a profile in force, its `## Structure implications` is an input to that reasoning** — the
knowledge types that earn their own home. It is not a folder list to copy: a folder the profile
implies but this vault will never fill is still speculative, and the growth test still applies. State
each proposed folder's provenance — profile, domain, or both.

Present:

- the new folders, each with its `Place here:` line;
- **where every existing note goes**, one line each, grouped by destination — including the ones
  that fit nowhere, listed under `.wiki/.trash/` with a reason;
- what happens to the glossary: which terms carry over (usually none), which are dropped;
- what happens to `.wiki/domain-context.md`;
- what happens to learned rules.

For a fresh vault this is short and mostly "the four seeded notes are trashed". For a heavy vault it
is long, and its length is the honest cost of what was asked.

## Step 4 — the gate

**Wait for an explicit accept.** Not an assumption, not "proceeding unless you object". The same
gate `refactor` and `init` use, and for the same reason: everything after this point is expensive to
undo, and the user is the only one who knows whether the old material still matters.

An edited proposal comes back as the plan — use theirs, do not re-derive it.

## Step 5 — the four things that are not notes

Decided explicitly, never by default:

- **`.wiki/domain-context.md`** — owner-authored standing knowledge about the *old* domain. It is
  almost never right for the new one, and it is also the only file nobody can regenerate. **Move it
  to `.wiki/.trash/domain-context-<old-domain>.md` and write a fresh empty one from the template.**
  Say that you did, and where the old one is.
- **The knowledge profile** — if it is changing, the overlay is swapped in step 6, not here. If it
  is *not* changing, nothing happens to it: the doctrine survives a domain change untouched, because
  how knowledge decomposes is independent of what it is about.
- **Learned rules** — every `validated` rule in `.wiki/agent-memory/rules/` was earned on the old
  domain's placements, and under the old doctrine if the profile is changing too. **Demote them all
  to `supported`** so they stop influencing decisions, and
  keep them: if a rule was really about knowledge organization rather than banking, it will earn its
  slot back in a handful of episodes. Never delete them, and never leave them loaded.
- **Episodes** — untouched. What happened, happened; the log is a record, not an opinion.
- **`.wiki/todos_validations.md` and `.wiki/wiki_gaps.md`** — open items about the old domain.
  Archive them to `.wiki/archive/<name>-<old-domain>.md` and start clean.

## Step 6 — execute, in this order

1. Create the new folders.
2. **Move** notes into them — never copy, never delete. Anything with no destination goes to
   `.wiki/.trash/` at its original path.
3. Rewrite links that the moves broke (`references/linking.md`).
4. Remove folders that are now empty.
5. Rewrite `.wiki/structure-accepted.md` with the accepted structure and today's date, keeping the
   old one as a `## Superseded` section — the reasoning behind the previous shape is worth keeping.
6. Update `.wiki/wiki-config.json`: `domain`, `last_reorganized_at`, and — when the profile
   changed — `knowledge_profile` and `relation_types` from the new profile's `## Relation types`.

6b. **Swap the overlay**, when the profile changed. Remove the old one first, then apply the new;
   never splice one over another:

   ```bash
   python3 .agents/skills/local-wiki/scripts/apply_profile.py \
     --artifact .agents/skills/local-wiki --remove
   python3 .agents/skills/local-wiki/scripts/apply_profile.py \
     --profile <path to the new profile> \
     --artifact .agents/skills/local-wiki --vault <vault>
   ```

   Adopting a profile where there was none skips the removal. Dropping to `none` is the removal
   alone, plus deleting `.wiki/knowledge-profile.md`. Either way, update the `Knowledge profile` row
   in `vault-profile.md` — regeneration reads it to know what to re-apply, so a stale row silently
   rebuilds the wrong skill.

   **The profile file must be reachable.** It ships with the `wiki` skill
   (`~/.agents/skills/wiki/references/knowledge-profiles/<name>.md`); if `wiki` is not installed on
   this machine, say so and stop before removing the old overlay — leaving the artifact with neither
   doctrine is worse than leaving it with the old one.
7. Update `vault-profile.md`: the domain row, the accepted-structure table, and **clear
   `## Vault-specific decisions`** — those answers were about the old domain. List what you cleared
   in the report so nothing disappears silently.
8. Rebuild `index.md` from scratch, glossary included, per `references/index-format.md`. This is one
   of the two times a from-scratch rebuild is right: the old descriptions describe a vault that no
   longer exists.
9. Rewrite `README.md`'s domain, purpose and "What's in here" list.

Follow `references/index-format.md`'s write budget: scaffold, then one folder per operation.

## Step 7 — rebuild everything derived

```bash
python3 .agents/skills/local-wiki/scripts/scan_vault.py --root <vault> --out .wiki/manifest.json
python3 .agents/skills/local-wiki/scripts/graph.py --vault <vault> scan --full
python3 .agents/skills/local-wiki/scripts/contributors.py record \
  --user-id <user_id> --path <each moved file> --type edited --vault <vault>
python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> record --mode reshape \
  --decision new-folder --target <the new structure's root> \
  --rationale "reshaped <old domain> -> <new domain>" --user-id <user_id>
.rag/bin/rag update --quiet
```

`graph.py scan --full`, not `--since-manifest`: every path changed, so an incremental scan would
leave edges pointing at notes that have moved.

## Report

```
Reshaped: banking -> ai, profile none -> process-knowledge

Structure
  6 new folders: foundations/, models/, training/, evaluation/, tooling/, research-log/
  9 old folders removed (empty after the moves)

Notes (11)
  moved   8  -> foundations/ (3), tooling/ (3), research-log/ (2)
  trashed 3  -> .wiki/.trash/  (seeded banking scaffolding, no content)

Not notes
  domain-context.md  -> .wiki/.trash/domain-context-banking.md, fresh one written
  4 learned rules    -> demoted to `supported`; they were earned on banking placements
  2 open validations -> .wiki/archive/todos_validations-banking.md
  3 vault-specific decisions cleared:
      - regulatory/ is authoritative for anything legally binding
      - client names never written into notes
      - meeting notes go under processes/, not general/

Rebuilt: index.md (6 sections, glossary emptied), README.md, structure-accepted.md,
         graph (14 edges), search index (11 files)
```

Then the closeout checklist:

```
Closeout
  [x] session startup .......... READY, token 2026-08-28-b894af19
  [x] git safety ............... in step with origin/main
  [x] weight check ............. 11 notes, 3 with content — fresh, shown to you
  [x] plan accepted ............ you accepted the 6-folder AI structure
  [x] notes moved .............. 8 moved, 3 trashed, 0 deleted
  [x] links repaired ........... 4 rewritten
  [x] profile updated .......... domain, structure, decisions cleared
  [x] index rebuilt ............ from scratch, glossary emptied
  [x] profile applied .......... process-knowledge, 11 hook(s) into 9 instruction file(s)
  [x] doctrine written ......... .wiki/knowledge-profile.md
  [x] rules demoted ............ 4 -> supported
  [x] contributors recorded .... 11 files
  [x] graph rebuilt ............ scan --full, 14 edges
  [x] search ................... .rag, 3 queries, 9 hits
  [x] search index refreshed ... 11 files re-embedded
```

## Edge cases

- **The vault is empty** — no notes at all. Then this is just `init`'s structure step: propose,
  accept, create, index. Say that it was empty rather than implying work was done.
- **The new domain is a superset of the old** ("banking wiki → fintech wiki") — usually not a
  reshape. The existing notes still belong; what is wanted is new folders alongside. Say so and
  offer `refactor` instead; reshape only if they still want the structure rebuilt.
- **Some notes belong to neither domain** — they were always misfiled. Trash them with a reason,
  and list them individually; a user will often want to move them to a different vault.
- **The user wants the old material kept somewhere** — copy the vault directory yourself first,
  outside this vault, before step 6. Say where you put it. Never rely on `.wiki/.trash/` as a
  backup: it holds displaced files, not a snapshot.
- **The reshape is interrupted mid-execution** — the vault is in a half-moved state and this is the
  worst case. Report exactly which numbered step completed, and resume from the next one; never
  restart from step 1, which would move already-moved notes again.
- **`.wiki/agent-memory/` does not exist** — nothing to demote. Normal for an older vault.
