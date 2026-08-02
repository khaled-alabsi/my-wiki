# Keeping the index current

Which command to run after which kind of change, and what each one costs.

---

## The decision table

| What changed | Command | Cost |
|---|---|---|
| Notes added, edited, or deleted | `.rag/bin/rag update` | Only the changed files |
| A whole new folder to cover | edit `sources` in `config.toml`, then `update` | The new folder |
| `.ragignore` loosened | `.rag/bin/rag update` | The newly-included files |
| `.ragignore` tightened | `.rag/bin/rag index --full` | Everything (see §3) |
| `retrieval.*` | nothing — next search uses it | Free |
| `chunking.*` | `.rag/bin/rag index --full` | Everything |
| `embedding.*` | `.rag/bin/rag index --full` | Everything |
| Toolkit upgraded | `.rag/bin/rag doctor`, then rebuild only if it says to | Usually free |
| Store looks inconsistent | empty `db/` + `state/`, then `index --full` | Everything (~285s) |
| **New machine**, or dangling symlinks | `bash .rag/bootstrap.sh`, then `doctor --models` + `index` | Full rebuild + 6.4 GB download |

**The rule behind the table:** anything that changes how text is turned into vectors invalidates
every stored vector. Anything that only changes how stored vectors are searched is free.

## 1. Routine: notes changed

```bash
.rag/bin/rag update
.rag/bin/rag status
```

Unchanged files are skipped by size and mtime, so this stays fast. Deleted notes drop out in the
same pass.

Automate it if you prefer:

```bash
.rag/bin/rag watch          # re-indexes a few seconds after the vault goes quiet
```

`watch` batches a burst of editor saves into one run and refuses to start a second run while one
is going. It is a good fit here — the vault is small, re-indexing is cheap, and edits are frequent
and manual. `watchdog` is already installed.

Note `watch` ignores the same private names as the indexer, so saving into `_utils/` or
`.wiki-index/` will not trigger a run.

## 2. Adding a source

```toml
[[sources]]
name = "papers"
path = "/absolute/path/to/papers"
include = []
exclude = []
```

Then `.rag/bin/rag update`. Existing sources are untouched. Afterwards restrict searches with
`--source papers`.

Check what a source will actually pull in *before* committing:

```bash
.rag/bin/rag plan
```

That prints the file count, the estimated chunk count, and every skip reason. It is free and needs
no dependencies.

**If the new source contains PDFs or Office files**, install the extractors first — they were
deliberately left out because this vault has none:

```bash
python3 .rag/toolkit/rag_toolkit/install.py --extras documents
```

Without them those files are reported as unsupported with a reason, not silently indexed as empty.

## 3. Changing what is excluded

`.ragignore` uses gitignore syntax and lives at `.rag/.ragignore`.

```bash
# after editing it
.rag/bin/rag plan      # see the effect first
.rag/bin/rag update    # if you loosened it
```

**Tightening it needs a full rebuild.** `update` adds and refreshes; it does not walk the store
looking for chunks that are now excluded, because newly-ignored files are no longer discovered at
all. Use `index --full` after tightening.

One thing you cannot loosen: names beginning with `.` or `_` are excluded by the toolkit itself,
not by `.ragignore`. If you genuinely need such a folder indexed, rename it.

## 4. Changing chunking

```bash
.rag/bin/rag config set chunking.target_chars 1200
.rag/bin/rag index --full
```

Current: target 1800 chars, overlap 220.

Change one value, rebuild, and re-run the same probe queries so you compare like with like. The
probes used to validate this index, with their expected top hit:

| Probe | Should return |
|---|---|
| `how do I push back when a colleague keeps adding work in the middle of a task` | `Work-life/Trigger-Situationen…md` — TEIL 1, Scope Creep |
| `Geeignetheitserklärung` | `Banking/mifid-wphg-banking-notes.md:107` |
| `worked example of MYT decomposition on Tennessee Eastman data` | `PhD/myt-decomposition.md:65-86` |
| `sourdough bread starter hydration and fermentation schedule` | nothing above ~0.002 |

Guidance:

- Results **too vague**, whole sections when you wanted a sentence → lower `target_chars`.
- Results are **fragments** cut off before the answer → raise it, or raise `overlap_chars`.
- The answer keeps landing **split across two chunks** → raise `overlap_chars`.

Do not raise `target_chars` merely because `bge-m3` accepts 8192 tokens — see
`MAINTAINER_MANUAL.md` §4.

## 5. Changing the embedding model

This is the one change that silently corrupts results if done halfway.

```bash
.rag/bin/rag config set embedding.model NEW_MODEL_ID
.rag/bin/rag doctor --models      # confirm it loads and see the real dimension
.rag/bin/rag index --full         # not optional
```

Between step 1 and step 3 the index holds vectors from the old model while queries are embedded by
the new one. Those are not comparable. Guards:

- `rag update` **raises** rather than mixing two models into one store.
- `rag status` prints a warning until the rebuild is done.
- `rag doctor` reports `model drift` as a failure.

Model IDs live only in `toolkit/rag_toolkit/models.py` — see `MAINTAINER_MANUAL.md` §5.

## 6. Upgrading the toolkit

```bash
# 1. re-copy the skill's scripts/rag_toolkit/ over .rag/toolkit/rag_toolkit/
python3 .rag/toolkit/rag_toolkit/install.py    # any new dependencies
.rag/bin/rag doctor                            # reports version drift
```

Then update `.rag/VERSION` and `config.toml`'s `toolkit_version` by hand — `doctor` compares them
and will warn until they match. Current: 1.1.2.

Rebuild only if `doctor` says chunking or embedding defaults changed. A change confined to the
CLI, the web UI, or retrieval does not need one.

## 7. Verifying an update actually worked

Do not trust the run summary alone:

```bash
.rag/bin/rag status                          # counts and last-run time moved
.rag/bin/rag search "something you just wrote" -k 3
```

If a note you added does not come back:

1. `.rag/bin/rag plan` — is it discovered at all, or being skipped?
2. Check `.ragignore`, and check the name does not start with `.` or `_`.
3. `.rag/bin/rag doctor --extract` — does it yield text?

A file that is discovered, extracts text, and still does not retrieve is a ranking problem, not an
indexing one — raise `retrieval.candidates` or confirm reranking is on.

## 8. Costs, in the shape they actually take

Indexing time is dominated by embedding, which scales with **chunk count**, not file count.

Measured on this vault, not estimated:

- Full build: 144 files → 3055 chunks in **284.8s** on `BAAI/bge-m3`, device `mps`, batch size 16.
- That is roughly **11 chunks/second**. Use it to project a rebuild after you add notes.
- `update` after editing a handful of notes: seconds.
- A cold single query costs about 1.2s of model loading before results appear.

`rag plan` prints the chunk estimate before you commit to a run — though note it under-predicted
here (1279 estimated vs 3055 actual), because heading-dense notes split well below the character
target. Treat it as a lower bound.

Run one index job at a time. Embedding is memory-bound, and running it alongside other heavy work
is the usual cause of an OOM kill part-way through.
