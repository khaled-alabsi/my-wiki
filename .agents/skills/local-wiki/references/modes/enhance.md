# Enhance mode — improving this skill, not the vault it serves

<!-- sync: local-wiki-modes v5 -->

The subject is `.agents/skills/local-wiki/` itself: its instructions, its scripts, its profile. Use
it when something this skill does is wrong — it files things in the wrong place by default, a mode
misbehaves, a tool errors, a rule in a reference file does not fit how this vault actually works.

**Inputs**: what is wrong, in the user's words.
**Outputs**: a change inside this skill folder, and a report. **No note is touched** — if the fix is
"and re-file those three notes", that is an `update` or `refactor` run afterwards, said out loud.
**Reads**: `vault-profile.md`, then whichever file owns the behaviour.

Never inferred. The user asks for it by name.

## The first question, always: which zone does this belong in?

This skill has two zones, and putting a fix in the wrong one is the mistake this mode exists to
avoid.

| Zone | Files | What happens to it |
|---|---|---|
| **Vault** | `vault-profile.md`, `remote_instructions.md` | **Yours. Survives forever.** Nothing regenerates them |
| **Generated** | everything else — `SKILL.md`, `references/`, `scripts/`, `assets/` | Came from the `wiki` package's template, and **is overwritten wholesale the next time anyone runs `wiki enhance`** against this vault |

So:

- **"Meeting notes should go under `processes/`, not `general/`"** — a standing decision about *this*
  vault. It goes in `vault-profile.md` → Vault-specific decisions. Editing a reference file to say
  it would work until the next regeneration, and then silently stop working.
- **"The placement ladder has a real bug"** — a defect in a carried rule. Fix it here so this vault
  works today, **and tell the user it must go upstream**, because the fix lives in the `wiki`
  package's template and this copy is downstream of it.

**When in doubt, it is a vault decision.** A vault decision in the profile is always correct; a
vault decision in a reference file is a fix with an expiry date.

## Step 1 — reproduce it

A report is a hypothesis. Before changing anything, find the actual line that produced the
behaviour: the mode file's step, the reference rule it followed, or the tool's output. Quote it back
in one line.

"I could not reproduce it, here is what I checked" is a legitimate outcome and a far better one than
a speculative edit to a rule that was already right.

## Step 2 — classify by owner

| What is wrong | Where it lives |
|---|---|
| Where material gets filed, the ladder, cross-references | `references/placement-rules.md` |
| How a placement is reasoned out, split/merge/extend, primary ownership | `references/knowledge-organization.md` |
| How this vault's structure is designed, whether a folder is earned | `references/domain-architecture.md` |
| `index.md` shape, sections, budgets, the split threshold | `references/index-format.md` |
| What earns a glossary entry, term normalization, the stoplist | `references/glossary.md` |
| When a mention becomes a link, relation types, back-edges | `references/linking.md` |
| Relation types, temporal queries, which graph query answers what | `references/graph.md` |
| Episodes, learned rules, the promotion gate, memory budgets | `references/agent-memory.md` |
| Registration, first run, contributors, provenance, the validation gate | `references/tracking.md` |
| Contradiction handling, override / ignore / supersede | `references/conflict-detection.md` |
| What structure material takes on the way in | `references/note-shaping.md` |
| Reading screenshots, pasted text, diagrams | `references/ingest-sources.md` |
| The `.rag` workspace — when it is used, how it is refreshed | `references/rag.md` |
| **The UI** — a route, the reader, search filters, the sidebar, the editor and its lock, the diagram overlay and its exports, the renderer bundles, ports | `references/ui.md` and `scripts/serve.py` |
| One mode's workflow | the matching `references/modes/*.md` |
| Triggers, mode resolution, the constitution, the closeout | `SKILL.md` |
| A tool's behaviour | the matching `scripts/*.py` — **and its test** |
| **A standing decision about this vault** | **`vault-profile.md`** |

## Step 3 — the two standing checks

Asked of every change, whatever it is about, because both failures are invisible on the day and
expensive a year later.

**Growth.** Every file this skill writes has one of four classes, and a new file with no class is a
defect:

| Class | Examples | Policy |
|---|---|---|
| Derived | `manifest.json`, `graph.sqlite`, `.rag/` | Unbounded is fine — rebuildable, git-ignored |
| Ledger | `contributors.json`, `agent-memory/episodes.jsonl` | Unbounded on disk, never read whole, tool-queried, rotated |
| Budgeted | `index.md` (~350), glossary (~50), `domain-context.md` (~150), rules index (8/scope) | A hard cap **and a named eviction rule** |
| Queue | `todos_validations.md`, `wiki_gaps.md`, `conflicts_ignored.md`, `proposals.md` | Bounded by *open* items; closed ones move to `.wiki/archive/` |

A cap with no eviction rule is decoration, and a cap needs an enforcement point — `wc -l` at the
moment of writing, not judgement by eye.

**Access.** Per file, decided deliberately: **blind append** through a tool (ledgers and queues,
where correctness does not depend on what is already there), **bounded slice** (`grep -F`, `tail`, a
`query` subcommand), or **full read** (only when rewriting or loading into a decision). Read only if
the content changes what you write; never read a file to learn its size; read a management file at
most once per session.

## Step 4 — fix, and run what you changed

- **A script change runs its test**, and if the test passed while the bug was live, **write the
  failing test first**:

  ```bash
  cd .agents/skills/local-wiki/scripts
  python3 test_scan_vault.py && python3 test_graph.py && python3 test_tags.py && python3 test_memory.py \
    && python3 test_contributors.py && python3 test_mermaid_validator.py \
    && python3 test_serve.py
  ```

- **A UI change runs the browser checks too, or it is not tested.** `test_serve.py` proves the
  server hands over the right bytes; it cannot prove a diagram DRAWS, a graph gets its edges, or an
  overlay is not empty — that happens in a JavaScript engine. Those checks are opt-in so the
  default run stays offline, and they **skip loudly** rather than passing silently:

  ```bash
  WIKI_UI_ASSETS=<vault>/.wiki/ui-assets python3 test_serve.py
  ```

  It needs Chrome or Chromium installed and the vault's cached bundles. Every UI bug found so far
  was invisible to the server-side checks and obvious to these: an svg cloned without a width laid
  out to nothing, and graph nodes spread as objects when the API sends strings. **If a UI fix has
  no browser check, it has not been verified** — say so in the report rather than implying it was.

- **A `SKILL.md` frontmatter change is checked mechanically** — the loader enforces both:

  ```bash
  python3 -c "
  import re,sys
  t=open(sys.argv[1]).read(); d=re.search(r'^description:\s*(.*)\$',t,re.M).group(1)
  print(len(d),'chars','OK' if len(d)<=1024 else 'OVER')
  print('colon+space:','none' if not re.search(r':\s', d) else 'INVALID YAML')
  " .agents/skills/local-wiki/SKILL.md
  ```

  A `": "` inside an unquoted `description:` is a nested mapping to YAML and the skill will not
  load at all. Use an em dash.

## Step 5 — record a generated-zone change where it will survive

A fix in the generated zone is invisible to whoever regenerates this artifact, and it will be
overwritten without anyone noticing. So whenever the generated zone is changed, **append a line to
`vault-profile.md` → `## Local modifications`**, creating the section if absent:

```markdown
## Local modifications

Changes made to this skill's generated zone by `enhance`. They are **overwritten** the next time
this artifact is regenerated from the `wiki` package — this list is what makes that visible.

- 2026-08-15 — `references/placement-rules.md`: the see-also rule fired on every near-miss, not
  only strong secondary fits. Belongs upstream in `wiki`.
```

And **say it in the report**: *"this fix lives in the generated zone; report it upstream or it is
lost on the next regeneration."*

Vault-zone changes need no such line — they are permanent by construction.

## Report

```
Enhanced: references/placement-rules.md (generated zone)

Cause      the cross-reference rule fired on any shortlist entry, not only strong secondary fits,
           so every filed note added two or three see-also pointers nobody wanted
Fixed      tightened the rule to require the same explicit test the placement ladder uses
Zone       GENERATED — recorded in vault-profile.md → Local modifications.
           This will be overwritten when the artifact is regenerated. Report it upstream.
Tests      no script changed; nothing to run
Not done   the 14 notes that already carry spurious see-also lines — that is a `refactor` run,
           say the word
```

Then the closeout:

```
Closeout
  [x] reproduced ............... found the rule at placement-rules.md, step 4
  [x] zone decided ............. generated — a real defect, not a vault preference
  [x] growth check ............. no file added, no budgeted file touched
  [x] access check ............. no new read path
  [x] fixed .................... references/placement-rules.md
  [-] tests .................... n/a, no script changed
  [x] recorded ................. vault-profile.md → Local modifications
  [-] search ................... n/a, enhance reads this skill, never the notes
  [-] notes touched ............ n/a, enhance never edits notes
```

## Edge cases

- **The fix is really a vault decision** — the commonest case. Put it in `vault-profile.md` and say
  why that is the better home: it survives regeneration and it is where the next run looks first.
- **The user wants a new mode** — that is upstream work in the `wiki` package, not a local edit. A
  mode invented here has no template behind it and disappears on the next regeneration. Say so.
- **The behaviour is correct and the user disagrees with it** — not a defect. It is a vault-specific
  decision, and the profile is exactly the mechanism for overriding a default.
- **A tool is broken outright** (it errors, it cannot be run) — fix it, run every test, and treat a
  green suite over a live bug as a second defect: add the failing test.
- **`wiki` is not installed here** — normal and expected. This artifact is self-contained; nothing
  in this mode needs the upstream package, and "report it upstream" means telling the human, not
  reaching for a folder that may not exist.
- **The same fix has been made here twice** — it was overwritten by a regeneration in between. That
  is the clearest possible signal it belongs upstream; say so explicitly.
