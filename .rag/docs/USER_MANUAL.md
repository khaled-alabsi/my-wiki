# RAG user manual

How to get good answers out of the index over **144 notes from the `my-wiki` Obsidian vault**.

- Quick reference: `QUICKSTART.md`
- Keeping it current and tuning it: `UPDATING.md`
- Internals and repair: `MAINTAINER_MANUAL.md`

---

## 1. What this does, and what it does not

It finds the passages in your own notes that are most relevant to a question, and tells you exactly
where each one came from.

It does **not** write answers. There is no language model in this toolkit and no API key. You read
the passages, or you hand them to an agent that does. The benefit is that every statement traces to
a citation the index actually returned.

## 2. How a search actually runs

1. Your query is embedded by `BAAI/bge-m3`.
2. **Dense retrieval** finds chunks whose meaning is close to the query — this is what catches
   "how do I push back on extra work" in a note that says "Scope Creep mitten in der laufenden
   Aufgabe".
3. **Keyword retrieval** finds chunks containing the literal terms — this is what catches
   `Geeignetheitserklärung`, `TaMrA`, `NSGA-II`, or `WpHG` exactly.
4. The two ranked lists are fused by Reciprocal Rank Fusion.
5. A cross-encoder (`BAAI/bge-reranker-v2-m3`) re-scores the top 40 candidates by reading each
   passage together with the query.
6. The top 10 come back with citations.

You need both halves. Dense retrieval alone misses exact identifiers; keyword retrieval alone
misses paraphrase. `matched_by` on each hit tells you which found it: `vector`, `text`, `hybrid`,
or `rerank`.

## 3. Writing queries that work

**Ask the way the note is written, not the way a search engine expects.**
`why does MYT divide instead of subtract` beats `MYT divide subtract`. The embedding model was
trained on sentences; give it one.

**Use a distinctive noun when you have one.** Names, codes and jargon go straight through the
keyword half: `Geeignetheitserklärung`, `Tamara`, `FRÜHSTART`, `NSGA-II`, `SEMA-GA`.

**Ask one thing at a time.** A query with two subjects retrieves the average of both and the best
of neither. Run two searches.

**Language does not matter.** The index is multilingual. An English question finds the German
`Work-life/` notes and vice versa — this was verified during setup, not assumed.

**Raise `-k` when exploring, lower it when you know what you want.** `-k 30` to survey a topic;
`-k 3` when you expect one authoritative passage.

## 4. Filters

| Flag | Effect | Example |
|---|---|---|
| `--path GLOB` | restrict to paths inside the vault | `--path "PhD/**"` |
| `--ext LIST` | restrict by file type | `--ext .md` |
| `--source NAME` | one configured source only | `--source my-wiki` |
| `--since DATE` | only files modified since | `--since 2026-07-01` |
| `--no-rerank` | skip reranking (faster, less precise) | |
| `--no-hybrid` | dense only, no keyword half | |
| `-k N` | how many results | `-k 20` |
| `--json` | machine-readable output | |

There is one configured source: `my-wiki`, pointing at the vault root — so `--source` is only
useful if you add another later. `--path` is the one you will actually use, and it maps onto your
top-level folders: `AI/`, `Banking/`, `Dev/`, `Mathematik/`, `PhD/`, `Quick note/`, `Work-life/`.

`--since` is unusually useful in a vault, because "what did I write about this recently" is a
common question and notes accumulate.

Filters narrow *before* ranking, so a filtered search is not the same as searching everything and
ignoring the misses — it gives weaker matches a chance to surface.

## 5. Reading a result

```
[1] Banking/mifid-wphg-banking-notes.md:107-136 — Geeignetheitserklärung (GEE)
    score 0.952476  (rerank)
    # Geeignetheitserklärung (GEE)

    **The GEE explains why the bank's recommendation is suitable for the
    customer.**
```

| Citation form | Means |
|---|---|
| `PhD/myt-decomposition.md:65-86 — MYT Decomposition > Worked TEP Example` | Markdown, lines 65–86, under that heading trail |
| `AI/opencode.json:1-40` | JSON file, line range |
| `... (part 2)` | One section long enough to need splitting |

Only Markdown and JSON appear in this index — there are no PDFs, Office documents or notebooks in
the indexed set, so you will never see page, slide or cell citations here.

**Scores are ordinal, not absolute.** A 0.42 does not mean "42% right". Compare scores within one
result list, never across two queries. After reranking the scale changes again — ordering is what
carries meaning.

That said, the *spread* is informative on this index. Verified during setup: a question the vault
genuinely answers scores 0.67–0.95, while a topic the vault does not cover at all scores
0.0007–0.0013. If your whole result list is down in the thousandths, the honest reading is "not in
these notes".

## 6. Interfaces

### Command line

```bash
.rag/bin/rag search "question"
.rag/bin/rag status
.rag/bin/rag update
```

Each invocation loads the embedding model and the reranker from disk, which costs a few seconds
before results appear. That is per-process startup, not a slow index — the web UI and the MCP
server load once and stay warm, so use those if you are running many queries.

### Python

```python
from rag_toolkit import Index

with Index.find() as index:
    hits = index.search("hawkins T2 decomposition", k=5)
    for hit in hits:
        print(hit["citation"], hit["score"])

    # Pre-formatted for pasting into a prompt, citations attached:
    print(index.context_block("hawkins T2 decomposition", k=6))
```

Each hit is a plain dict: `citation`, `score`, `matched_by`, `text`, `path`, `rel_path`, `source`,
`title`, `heading_path`, `anchor`, `chunk_id`.

### Notebook

`.rag/notebooks/rag_quickstart.ipynb` uses plain printed output and `IPython.display.Markdown` —
no `ipywidgets`, which avoids the stale-widget double-render problem in VS Code notebooks.

**Select the kernel named `my-wiki RAG (.venv)`.** It is registered against the vault's own venv,
which is the only interpreter that has `torch`/`sentence-transformers`. Any other kernel will get
as far as importing `rag_toolkit` — it is pure Python and the notebook puts it on `sys.path` — and
then fail on `ModuleNotFoundError: No module named 'sentence_transformers'`. The first cell checks
for this and tells you what to do rather than letting it surface mid-search.

If the kernel is not in the picker, register it once:

```bash
~/.local/share/rag/my-wiki/venv/bin/python -m ipykernel install --user \
    --name my-wiki-rag --display-name "my-wiki RAG (.venv)"
```

There is no `.venv` in the vault — the environment lives outside iCloud. `bash .rag/bootstrap.sh`
registers this kernel for you.

```python
from rag_toolkit import Index, to_markdown
from IPython.display import Markdown

with Index.find() as index:
    display(Markdown(to_markdown(index.search("dot product properties", k=5))))
```

### Local web page

```bash
.rag/bin/rag serve --web
```

Then open `http://127.0.0.1:8765`. Bound to localhost only, no authentication — do not expose it
to a network.

### Agents (MCP)

```bash
.rag/bin/rag serve --mcp
```

Register with the snippet in `QUICKSTART.md`. Exposes `rag_search`, `rag_context`, `rag_status`,
`rag_sources`. All read-only: an agent can search the index but cannot start an index run as a
side effect.

## 7. When a search comes back empty

An empty result has three quite different causes. Tell them apart before concluding the vault
lacks the answer.

1. **The note is excluded by design.** Check `.rag/.ragignore` first. Anything starting with `.`
   or `_` is never indexed, and neither are `Dev/LLM/`, `Dev/languages/Python/*.py|.ipynb`, or
   `Excalidraw/`. If your answer lived in one of those, the index will never find it.
2. **The index is stale.** `status` shows when it last ran. If you wrote the note after that, run
   `.rag/bin/rag update`.
3. **The content genuinely is not there.** Scores in the thousandths across the whole list is the
   signature. Say so rather than reaching for a plausible answer.

`doctor --extract` covers the fourth case — a file present but yielding no text. That has not
occurred on this vault: the build reported 0 empty and 0 failed across all 144 files.

## 8. Limits worth knowing

- **Chunks are passages, not documents.** A hit shows the passage that matched. If the answer
  spans a whole note, open the cited file.
- **Retrieval does not aggregate.** "How many notes mention MiFID?" is a counting question;
  retrieval returns passages that mention it, not a total.
- **Very recent edits need `update` first.** The index is a snapshot.
- **Changing the embedding model invalidates every stored vector.** `status` warns when the config
  and the index disagree; the fix is `rag index --full`.
- **Wikilinks are not a retrieval path.** `[[note name]]` is collected as metadata, but the index
  ranks text. Your `index.md` notes the vault has almost no note-to-note links anyway.
