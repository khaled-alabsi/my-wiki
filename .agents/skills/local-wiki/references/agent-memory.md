# Agent memory — what the agent learns, kept out of what the vault knows

<!-- sync: agent-memory v1 -->

The vault holds **world knowledge**: how settlement works, what MiFID requires, which system owns
the customer number. This holds **agent knowledge**: that three notes about reusable mechanisms were
filed under the project folder and the owner moved all three.

Keeping them apart is the whole design. Operational experience written into a note turns a knowledge
base into a diary, and a vault whose notes are half agent introspection is worth less than one with
no memory at all. `.wiki/` already holds machinery *about* the vault and never knowledge *belonging
to* it; agent memory lives there for exactly that reason.

## Where it lives

```
.wiki/agent-memory/
├── episodes.jsonl          every reversible decision. Append-only. NEVER read whole
├── episodes-rollup.json    fixed-size counters — what `stats` reads instead of the log
├── observations.md         patterns noticed but not yet evidenced
├── rules/
│   ├── index.md            generated. Loaded BY SCOPE before a decision, never whole
│   ├── RULE-017.md         one rule per file
│   └── deprecated/         rules that lost — kept, never deleted
├── reflections/2026-08.md  what `learn` concluded, one file per month
├── proposals.md            changes to existing notes the agent wants but may not make
└── archive/                rotated quarters of the log
```

Committed, like `contributors.json`. The vault learns once for everyone: a correction one person
makes improves the agent for every contributor, which is the entire return on keeping this at all.

## The tool, and the rule that makes it necessary

**Never open `episodes.jsonl`.** It grows with every decision ever made — this is the same rule the
constitution already applies to `contributors.json`, and it is enforceable only because every
question has a bounded command:

```bash
python3 scripts/memory.py --vault <vault> record --mode update --decision place \
    --target banking/processes/onboarding.md --alternatives regulation/mifid.md \
    --rationale "describes the process, not the rule" --applied-rule RULE-017 --user-id <id>
python3 scripts/memory.py --vault <vault> close --id EP-238 --outcome corrected \
    --correction regulation/mifid.md
python3 scripts/memory.py --vault <vault> stats --json          # counters; never opens the log
python3 scripts/memory.py --vault <vault> rules --scope placement
python3 scripts/memory.py --vault <vault> query --outcome corrected --since 90d --limit 20
python3 scripts/memory.py --vault <vault> promote --json        # end of every writing run
```

## What gets recorded — and what does not

**Record a decision that could have gone another way.** One `record` call per decision, at the point
the decision is made:

| Decision | Recorded when |
|---|---|
| `place` | material went to one destination and another was genuinely plausible |
| `split` / `merge` | material was divided, or folded into an existing note |
| `new-folder` | nothing fitted and a folder was created |
| `dedupe-skip` | a near-duplicate was found and the material was merged instead of added |
| `link` | a relation was written that a reasonable run might not have written |

**Do not record**: reads, searches, index repairs, anything with one possible outcome. A log of
inevitabilities is noise that makes the real corrections harder to find.

**`--rationale` is one line and it is about the *choice*.** "describes the process, not the rule" is
a rationale. "filed the note" is not, and a rationale that would fit any decision teaches nothing.

## Closing the loop — the corrections are the valuable half

An episode is `unknown` until something closes it:

- **`corrected`** — the user moved it, renamed it, or said it should have gone elsewhere. Close it
  the moment that happens, in the run where it happens, with `--correction <where it should have
  gone>`. This is worth more than ten silent successes and it is the only signal that ever demotes
  a rule.
- **`confirmed`** — the placement survived and was built on: material was later added to the same
  note, or the user referred to it approvingly. Never mark `confirmed` just because time passed and
  nobody complained; silence is not agreement.

## The gate

```
OBSERVATION → CANDIDATE → SUPPORTED → VALIDATED → CANONICAL
                                          ↘ DEPRECATED (kept in rules/deprecated/, never deleted)
```

| Transition | Trigger |
|---|---|
| observation → candidate | 2 supporting episodes, **or** 1 explicit user correction |
| candidate → supported | 3 supporting episodes, zero contradicting |
| supported → validated | **automatic** at 5 supporting episodes with no contradiction in 30 days |
| validated → canonical | the rule is generic, not vault-specific → it belongs in the skill package, via `enhance` |
| validated → supported | **automatic and immediate** on a contradicting correction |
| any → deprecated | contradictions equal or outnumber support |

**Only `validated` and `canonical` rules are ever loaded into a decision.** Candidates exist, and
they are visible in `learn`'s report, but they never influence a placement.

Thresholds are arithmetic in `scripts/memory.py`, not judgement — a model asked "is this enough
evidence?" answers yes. Confidence is `support / (support + contradictions)`, computed by the tool.

### Promotion is automatic, so it must be announced

Two obligations follow from the gate being automatic, and neither is optional:

- **Run `memory.py promote` at the end of every run that wrote**, and **put every promotion and
  demotion in the report**, by id, with the rule's text. Silent behaviour change is what
  auto-promotion costs; the announcement is what pays for it.
- **When a rule changed a decision, name it in that run's report** — `RULE-017 → filed under
  banking/ rather than projects/`. The user must always be able to see why a note went where it
  went, and to correct the rule rather than just the note.

`.wiki/agent-memory/` is committed, so `git` is the rollback: a promotion that turns out wrong is
reverted like any other change.

## Loading rules — by scope, never whole

Before deciding, load only the scopes the current mode uses:

| Mode | Scopes |
|---|---|
| `update`, `intake` | `placement`, `linking` |
| `refactor` | `placement`, `splitting` |
| `indexing`, `refresh` | `glossary` |
| `ask` | `answering` |

```bash
python3 scripts/memory.py --vault <vault> rules --scope placement
```

Eight slots per scope, so this is about a dozen lines whichever vault it runs in. **Memory cost
scales with corrections, not with notes**: a vault of 5,000 notes loads the same dozen lines as one
of 16. When a ninth rule is promoted into a full scope, the lowest-confidence rule loses its slot and
drops to `supported` — still true, still evidenced, no longer worth the tokens.

## Growth and access

| File | Class | Cap | Eviction |
|---|---|---|---|
| `episodes.jsonl` | ledger | none on disk | `memory.py rotate` moves closed quarters to `archive/` |
| `episodes-rollup.json` | derived | fixed | rewritten in place |
| `rules/index.md` | budgeted | 8 per scope | weakest rule in the scope drops to `supported` |
| `RULE-*.md` | budgeted | ~20 lines | deprecated → `rules/deprecated/` |
| `observations.md` | queue | 100 open | promoted, or dropped after 90 days and counted |
| `proposals.md` | queue | 30 open | oldest reported stale by `audit` |
| `reflections/` | queue | one file per month | older than 6 months → `archive/` |

Access, per file: **`episodes.jsonl` is append-only through the tool and never opened**;
`rules/index.md` is read once per session, by scope; `observations.md` and `proposals.md` are
appended after a `grep -F` key check, not a read.

## Proposals — what the agent wants to change but may not

A-MEM's insight is that a new fact can change how an old one should be understood. That is true and
it does **not** license rewriting notes: the constitution is additive-only outside an accepted
`refactor` plan.

So after a write, when the graph shows the new material contradicts, duplicates or supersedes a
neighbour, append the proposal:

```
- [ ] 2026-08-15 — payments/sepa-instant.md overlaps payments/sepa.md §Timing — merge candidate (EP-238)
```

Proposals are input to `refactor`, which has its own approval gate. Nothing here is ever applied
automatically.

## Edge cases

- **No `.wiki/agent-memory/` yet** — normal for a vault created before this existed. Create it on
  the first `record`; do not backfill episodes from git history, which would invent evidence.
- **A rule contradicts `.wiki/domain-context.md`** — the domain context wins, always. It is what the
  owner stated; a rule is what the agent inferred. Deprecate the rule and say so.
- **The same correction repeats after the rule was deprecated** — that is an observation about the
  *previous* rule being wrong in a specific way, not a reason to resurrect it. Write a new, narrower
  rule.
- **A run wrote but recorded nothing** — say so in the report. A run that changes the vault and
  leaves no episode is indistinguishable from a run that never happened.
