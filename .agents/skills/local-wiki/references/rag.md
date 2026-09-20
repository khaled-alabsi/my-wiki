# Using a `.rag` semantic index, when the vault has one

Some vaults carry a `.rag/` workspace: a local hybrid search index (dense embeddings + BM25, with a
reranker) over the vault's own files. When it's there, it answers the one question grep cannot —
*"is there already a note about this, phrased differently?"* — and it does it with citations.

**This is not optional infrastructure, and a run that does not use it owes an explanation.** Grep
finds the words you thought of; the index finds the note someone else phrased differently, which is
the failure mode a knowledge base exists to prevent. A vault answered from grep alone looks like it
is working right up until the day it silently misses the note that already said the answer.

Nothing here requires another skill to be installed: a `.rag` workspace is self-contained, carrying
its own virtualenv path in `.rag/config.toml`.

## Detection

```
<vault>/.rag/bin/rag   exists and is executable   ->  available
```

That's the whole check. Do it once, at the start of a run, and remember the answer for the rest of
it.

**Absent or broken is a defect to repair, not a state to work around.** See "The index is not
optional" below: the run says so, fixes it, and only then continues.

## Commands

Run from the vault root, or with the absolute path to `.rag/bin/rag`.

```bash
.rag/bin/rag search "why does the advisor need a target market check" -k 5 --lines 4
.rag/bin/rag search "target market" --path "Banking/**" -k 8
.rag/bin/rag --json search "GEE"          # machine-readable
.rag/bin/rag status                       # is the index current, or built with another model
.rag/bin/rag update --quiet               # re-embed only the files that changed
```

**`--json` is a top-level flag and must come BEFORE the subcommand.** `rag search "x" --json` is an
argparse error, whatever the workspace's own `QUICKSTART.md` shows.

Search flags worth knowing: `-k` (hits, default from config), `--path` (glob, relative to the
source), `--ext`, `--source`, `--since ISO-DATE`, `--max-chars` (per-hit text, default 700),
`--lines` (printed lines per hit, default 8), `--no-rerank`, `--no-hybrid`.

Result shape — file, line range, heading trail, score, then the passage:

```
[1] Banking/mifid-wphg-banking-notes.md:107-136 — Geeignetheitserklärung (GEE)
    score 0.952476  (rerank)
    # Geeignetheitserklärung (GEE)
    **The GEE explains why the bank's recommendation is suitable for the customer.**
```

## Two front doors, and only one of them is yours

| Door | Who uses it | Why |
|---|---|---|
| `.rag/bin/rag` (CLI) | **the agent — this is your door** | one question, one answer, process exits |
| `rag_toolkit.api.Index` (in-process) | `scripts/serve.py` only | the UI holds it open so the models stay resident |

**Always shell out to the CLI.** A run asks a handful of questions and stops; the import costs
nothing there and buys nothing.

The UI is the exception, and the reason is measured, not stylistic: every CLI invocation reloads
the embedding model *and* the reranker, so a person typing in a search box would pay that on each
keystroke. `serve.py` therefore re-execs itself under `<vault>/.rag/.venv/bin/python` with
`PYTHONPATH=<vault>/.rag/toolkit`, constructs one `Index`, and keeps it for the life of the
process (`references/ui.md`).

Neither door ever writes inside `.rag/` — see the last section.

## The index is not optional

Three states, three responses. None of them is "carry on quietly with grep".

| State | Do, in this run |
|---|---|
| **Working** | Use it. Say so in the report |
| **Broken** — venv missing, model mismatch, non-zero exit | Repair it: `bash .rag/bootstrap.sh`, then `.rag/bin/rag update`. Say what was wrong and that it is fixed |
| **Absent** — no `.rag/` at all | Set it up. Announce it first (it downloads an embedding model and takes minutes), then build it and index the vault |

- **Announce before a first-time setup or a bootstrap, then do it** — do not ask permission and wait.
  The user has already decided the vault has a semantic index; a prompt per session is the same
  question re-asked forever.
- **Repair once per session.** If it fails twice, stop retrying, report the exact error and the
  command, and fall back to grep **loudly** — that is the one case where a run legitimately proceeds
  without the index, and it still gets the justification line below.
- **Never let the repair eat the user's task.** Fix the index, then do what they asked, in the same
  run. A session that returns only a repair report has failed at the actual request.

> **This overrides `rag`'s Constitution rule 1** — *"Never launch indexing, embedding, model
> downloads, or dependency installs yourself. Print the exact command and stop."*
>
> Scope of the override: **an absent or broken `.rag` workspace belonging to the vault this skill
> serves**, repaired or built once per session, announced before it starts. It is the same reasoning
> as the `first_run` override in the session startup routine — a contributor who asks a question
> should get an answer, not a setup checklist — widened from "a fresh clone" to "any state where the
> index cannot answer". Every other install still follows `rag`'s rule.

## Every answer says whether the index was used

**One line, in every report, in every mode — including the modes that write nothing.** It is the
only way a silently dead index ever gets noticed, because a grep-only answer looks exactly like a
good one.

```
search ...... .rag, 2 queries, 7 hits           <- used
search ...... .rag rebuilt (venv was dangling), then 1 query, 4 hits
search ...... grep only — .rag bootstrap failed twice: <error>. Run: bash .rag/bootstrap.sh
search ...... grep only — exact-token lookup (a filename), retrieval adds nothing
```

**Not using it requires a reason that names which exemption applied**, from "When not to" below.
"Didn't need it" is not a reason. If no exemption fits, the index should have been used, and saying
so plainly is better than a silent grep answer — that line is the signal the vault's owner acts on.

## When to use it

- **Before creating a new note** (`references/placement-rules.md` → rule 3). The near-duplicate
  search is the highest-value use: a note under a name you'd never have guessed is exactly what
  dense retrieval finds and grep misses.
- **Finding where a term is defined**, when building or repairing a glossary entry.
- **Resolving an open question** from the incoming material
  (`references/open-questions.md` → step 3).
- **`ask` mode retrieval**, after the index shortlist and alongside direct search.
- **`audit` duplicate detection** across the whole vault.

## When not to

- The index already routes you to an obvious single destination — don't spend a model load to
  confirm what a `Place here:` line already said.
- A small vault, where reading the candidates outright is cheaper than a search.
- Anything **path-shaped**: folder structure, split decisions, `refactor` planning. RAG knows
  content, not layout; the manifest knows layout.
- An **exact-token** lookup — a filename, a code symbol, a specific number. Grep is faster and
  exact; retrieval is fuzzy by design.
- **"Every note about this subject"** — `.rag` has no tag filter (`--path`, `--ext`, `--source` and
  `--since` are all it filters by). The tag tree answers that: `graph.py query --tag <node>`
  (`references/tagging.md`).

## The rule that keeps it honest

**RAG returns passages, not truth.** A hit is a pointer, exactly like an index line: **open and read
the cited file** before writing anything based on it, or quoting it, or concluding a duplicate
exists. Cite the note and its section — never the snippet, and never a line range as if it were a
quote you verified when you didn't.

A retrieval miss is not proof of absence either. "Not in the vault" still needs the index and a
direct search to agree.

## Cost discipline

The first search of a session loads the embedding model and the reranker — allow a generous timeout
(60s+) and don't treat a slow first call as a failure. After that, calls are fast.

- Batch a task's questions into **few searches**, not one per entity.
- Keep probes cheap: `-k 5 --lines 4`.
- Ask in **full sentences**. These indexes are built for prose; `"why does MYT divide instead of
  subtract"` beats `"MYT divide subtract"`.
- Scope with `--path` when the index already narrowed you to a folder.

## Keeping the index current after writes

Any run that **wrote to the vault** ends with:

```bash
.rag/bin/rag update --quiet
```

- **Once, at the very end** — after every note write and every index update, never per note.
- **Never** `rag index --full`. That is a from-scratch rebuild of the entire vault (minutes, not
  seconds) and is only ever justified by an embedding-model change, which is the vault owner's call.
- **Never** in `where` mode, or in any run that wrote nothing. A no-write mode stays a no-write mode.
- On failure: repair it once — `bash .rag/bootstrap.sh && .rag/bin/rag update` — and if that fails
  too, report the exact error and the command, and say in the search line that the index is now
  stale. Never leave a failed update unmentioned: the next session inherits it and cannot tell.

```
.rag index updated (3 files re-embedded).
```

or

```
.rag update failed (dangling venv symlink). Run: bash .rag/bootstrap.sh && .rag/bin/rag update
```

## Failure modes

| Symptom | Meaning | Do |
|---|---|---|
| `bin/rag` missing | No workspace here | **Set one up** — announce, then build and index. Never grep silently |
| Command exits non-zero, venv path missing | Store/venv lives outside the vault and didn't sync | **Run `bash .rag/bootstrap.sh`, then retry once.** Grep only if that fails, and say so in the search line |
| `status` warns about model mismatch | Index built with a different embedding model | Results are unreliable — **re-index** with the configured model; grep meanwhile, and report both |
| `status` shows many files unindexed | Index is stale | **Run `update` first**, then search. A stale index is a fixable state, not a caveat |
| Search returns nothing for an obvious term | The path is excluded by `.ragignore` | Check `.rag/.ragignore`; use grep for that area |

## Never write inside `.rag/`

It joins `.obsidian/`, `.git/`, `node_modules/` and `.wiki/` on the never-write list, and it
is excluded from the vault scan (`scripts/scan_vault.py` → `SKIP_DIRS`). Its `docs/*.md` are toolkit
manuals, not notes — indexing them as vault content is a bug, not a feature. The only files this
skill ever touches under `.rag/` are none; the only thing it does is run `bin/rag`.
