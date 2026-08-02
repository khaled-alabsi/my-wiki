# RAG quick start

Local search over **144 notes from the `my-wiki` Obsidian vault**. Everything lives in
`<vault>/.rag`. Nothing leaves this machine — no API key, no network calls at query time.

Run these from the vault root, or use the absolute path to `.rag/bin/rag`.

## The five commands

```bash
.rag/bin/rag search "your question"    # find passages, with citations
.rag/bin/rag update                    # after you add or edit notes
.rag/bin/rag status                    # is the index current?
.rag/bin/rag doctor                    # something is wrong
.rag/bin/rag serve --web               # browse results at http://127.0.0.1:8765
```

## What it is holding right now

| | |
|---|---|
| Source | `my-wiki` → the vault root |
| Files indexed | 144 (142 `.md`, 2 `.json`) |
| Chunks | 3055 |
| Embedding model | `BAAI/bge-m3` (sentence-transformers, 1024 dimensions) |
| Reranker | `BAAI/bge-reranker-v2-m3` |
| Store | lancedb, with full-text index |
| Last indexed | 2026-08-02 — 144 files, 0 failed, 284.8s |

## Searching

```bash
.rag/bin/rag search "how do I set a boundary when scope creeps mid-task"
.rag/bin/rag search "T2 fault attribution" -k 20
.rag/bin/rag search "target market" --path "Banking/**"
.rag/bin/rag search "transformer attention" --path "AI/**"
.rag/bin/rag search "decomposition" --since 2026-07-01
.rag/bin/rag search "GEE" --json                      # for scripts
```

Every result carries a citation you can open directly:

```
[1] Banking/mifid-wphg-banking-notes.md:107-136 — Geeignetheitserklärung (GEE)
    score 0.952476  (rerank)
    # Geeignetheitserklärung (GEE)

    **The GEE explains why the bank's recommendation is suitable for the
    customer.**
```

Read it as `file` + `line range` + `heading trail`. Those line numbers are accurate — they were
spot-checked against the real files during setup, and they land on the cited heading.

**Ask in full sentences.** These are prose notes and the model was trained on prose, so
"why does MYT divide instead of subtract" beats "MYT divide subtract".

**Cross-language works.** The index is multilingual: an English question returns the relevant
section of the German notes in `Work-life/`, and vice versa. This was verified, not assumed.

## When you change your notes

```bash
.rag/bin/rag update
```

Only changed files are re-read and re-embedded — unchanged files are skipped by hash, so this is
fast. Deleted notes drop out automatically. Run it after adding, editing, moving, or deleting
notes.

To have it happen by itself, `.rag/bin/rag watch` re-indexes a few seconds after the vault goes
quiet. `watchdog` is already installed for this.

## From Python, a notebook, or an agent

```python
from rag_toolkit import Index

with Index.find() as index:
    for hit in index.search("hawkins T2 decomposition", k=5):
        print(hit["citation"], hit["score"])
```

Ready-made notebook: `.rag/notebooks/rag_quickstart.ipynb`. For agents, copy the `mcpServers`
block from `.rag/mcp.json` into your host's config — it exposes `rag_search`, `rag_context`,
`rag_status`, `rag_sources`, all read-only. Details in `USER_MANUAL.md` §6.

## What is deliberately not indexed

Anything starting with `.` or `_` (so `.obsidian/`, `.trash/`, `_utils/`), plus `Dev/LLM/`,
`Dev/languages/Python/*.py|.ipynb`, and `Excalidraw/`. Full list with reasons in `.rag/.ragignore`;
the rationale is in `USER_MANUAL.md` §7.

## On a new machine

iCloud syncs the vault and the small half of `.rag/`, but not the venv, the 6.4 GB of model
weights, the vector store, or the manifest — those live outside iCloud at
`~/.local/share/rag/my-wiki/` and are reached by symlinks, which will arrive dangling.

```bash
bash .rag/bootstrap.sh          # rebuilds the environment and the symlinks; idempotent
.rag/bin/rag doctor --models    # downloads the weights, once
.rag/bin/rag index              # ~285s
```

Details in `MAINTAINER_MANUAL.md` §12.

## If results look wrong

1. `.rag/bin/rag status` — is the index stale, or built with a different model?
2. `.rag/bin/rag doctor` — environment, dependencies, store, extraction.
3. `.rag/bin/rag doctor --extract` — are your files actually yielding text?

Troubleshooting is in `MAINTAINER_MANUAL.md`. Tuning retrieval is in `UPDATING.md`.

## Two things worth knowing

- **This retrieves, it does not answer.** You get passages and citations; you or your agent write
  the conclusion. That is deliberate — nothing can hallucinate a citation the index did not return.
- **Changing the embedding model invalidates the whole index.** Vectors from two models are not
  comparable. `rag index --full` is required after any model change, and `status` warns until then.
