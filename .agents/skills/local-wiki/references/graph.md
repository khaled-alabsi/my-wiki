# The knowledge graph — typed relations, time, and how to ask it things

<!-- sync: graph v1 -->

`.wiki/graph.sqlite` is a **derived cache** of what the notes say. It is rebuildable at any moment
and never holds an edge that is not in a file. Never open it directly; `scripts/graph.py query`
answers a question and returns just that.

Two audiences, deliberately separated:

| Audience | Surface | Why |
|---|---|---|
| **the agent** | `graph.py query … --json --limit` | bounded, machine-readable, one question per call |
| **the user** | `serve.py` | the wiki UI's Graph tab, beside the reader. The agent never opens it |

## Relations carry a type

A link says two notes are connected. A **typed** relation says how — and that is what makes the
graph answerable rather than merely drawable.

```markdown
## Related
- requires :: [sca.md](../payments/sca.md) — PSD2 art. 97 mandates strong customer authentication
- superseded-by :: [psd3.md](psd3.md) — from 2026-01, ZAG transposition pending
- [onboarding](../processes/onboarding.md#compliance-checks) — untyped, means `relates-to`
```

- `type ::` before the link, Dataview syntax — Obsidian renders it natively and plain markdown
  ignores it, so a typed vault stays readable everywhere.
- **Only in `## Related` and `see-also.md`.** An inline mention in prose is a mention; typing it
  would assert a relation nobody wrote.
- **The reason line is still required.** A type is not a reason — `requires ::` with no explanation
  says which verb, not why, and `references/linking.md`'s bar is unchanged.

### The vocabulary is closed

`relates-to` (the default), `part-of`, `requires`, `regulates`, `implements`, `supersedes`,
`superseded-by`, `contradicts`, `example-of`, `defined-in`.

Closed on purpose: fifty one-off verbs mean no query can ask "what does this regulate" and get an
answer. A vault that genuinely needs more adds them to `relation_types` in `.wiki/wiki-config.json`
— a deliberate act by its owner, not something an agent does mid-run.

An unrecognised type **degrades to `relates-to` and is reported** by the scan. Never fail a scan
over a typo in one note; never let it pass silently either.

## Time — knowledge that stopped being current

A note may declare a window in its frontmatter:

```yaml
---
valid_from: 2018-01-13
valid_until: 2026-01-01
---
```

Edges inherit their source note's window. `--as-of DATE` then answers *what this vault said then*,
and both the edge **and the note it reaches** must have been valid — otherwise a 2020 query follows
a "superseded-by" line forward into a note written in 2026.

This is what makes **supersede** a real option when new material contradicts old:

| Situation | Resolution |
|---|---|
| The old note was wrong | override — fix it, per `references/conflict-detection.md` |
| Both are current and disagree | ask; log to `.wiki/conflicts_ignored.md` if ignored |
| **The old note was right, and then the world changed** | **supersede** — set `valid_until` on the old, `valid_from` on the new, and write `supersedes` / `superseded-by` between them |

For regulation, API versions and process changes, supersede is the correct answer far more often
than either of the other two. Nothing is deleted; the history stays queryable.

## Asking the graph

```bash
G="python3 scripts/graph.py --vault <vault>"

$G query --neighbors <path> --depth 2 --types requires,regulates --json --limit 10
$G query --backlinks <path> --json
$G query --path-between <a> <b> --max-hops 4 --json     # how are these two connected
$G query --type regulates [--from <path>] --json        # everything of one relation type
$G query --concept PSD2 --json                          # notes defining or mentioning a term
$G query --components --json                            # disconnected islands
$G query --orphans | --hubs | --broken | --oneway
$G query --neighbors <path> --as-of 2024-06-01          # the vault as it stood then
```

**Every query is capped** (`--limit`, default 25) and says whether the cap bit (`"truncated": true`).
That is the access rule made mechanical: an agent cannot pull an unbounded result set into context
however it asks.

### Where each one earns its keep

- **`ask` mode** — after the `.rag` search, expand each hit one hop and merge into the shortlist.
  "What does PSD3 change for our SCA implementation" is a traversal, not a similarity match, and
  retrieval alone cannot answer it.
- **`update` mode** — the neighbourhood of a candidate destination tells you whether the material
  belongs there; a note one hop from three near-identical notes is a merge candidate that retrieval
  will not flag.
- **`audit`** — `--components` is the real navigability measure. An orphan count says how many notes
  are unreachable; a component count says whether this is one body of knowledge or five that never
  learned about each other.
- **`refactor`** — hubs are split candidates, components are the seams a restructure should heal.

## Concepts are nodes too

The vault's own glossary terms are graph nodes, **derived** from what the scan already collects —
which note defines a term, which notes use it. Nothing is authored into the store.

`query --concept <term>` returns the defining note and every note that mentions it, with `defined-in`
distinguished from `mentions`. A term with no defining note is `inferred`, which is the same status
`references/glossary.md` uses and means the same thing: nobody has confirmed it.

## Seeing it — `serve.py`

The graph has a view in the wiki UI, beside the note reader:

```bash
python3 scripts/serve.py --vault <vault> --open        # Graph tab
```

`graph.py` no longer serves anything. It builds the payloads (`serve_stats`, `serve_node`,
`graph_payload`, `api_query`) and `serve.py` imports them, so the CLI and the page answer from one
implementation. Filtering happens in SQL, not in the browser: the client layout is O(n squared), so
above ~400 notes the server narrows by folder rather than handing over the whole vault.

`graph.py render --html <out>` still writes a standalone offline page with no server at all.

Mention the UI when the user asks about the shape of their vault, its structure, or what is
connected to what. **Never open it yourself** — `query --json` is the agent's door. The rules that
page runs under are in `references/ui.md`.

## Keeping the store in step

```bash
python3 scripts/scan_vault.py --root <vault> --out <vault>/.wiki/manifest.json
python3 scripts/graph.py --vault <vault> scan --full          # or --since-manifest
```

`scan --full` after any run that wrote; `--since-manifest` when only a few files changed. A schema
change needs no migration: the store is a cache, so it is dropped and rebuilt from the notes.

## Edge cases

- **The graph is empty** — `scan --full` has not run. Every query says so and exits 2; run the scan
  rather than answering from the index alone.
- **A typed relation points at a file that does not exist** — that is a `--broken` finding, not a
  node. The graph never invents an endpoint.
- **A note is in two components and you expected one** — usually a missing back-edge. `--oneway`
  finds those, and `references/linking.md` requires them.
- **`--as-of` returns nothing at all** — no note in the vault carries a validity window, which is
  the normal state. Temporal queries only mean something once someone starts dating knowledge.
