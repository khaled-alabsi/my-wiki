# This vault

<!-- NOT generated. `wiki enhance` never touches this file. -->
<!-- Everything specific to this one vault lives here, so the rest of the package can be
     regenerated wholesale without losing it. Edit it by hand when something below changes. -->

| | |
|---|---|
| **Path** | `/Users/Khaled.Alabsi/Library/Mobile Documents/iCloud~md~obsidian/Documents/my-wiki` |
| **Name** | my-wiki |
| **Domain** | engineering |
| **Knowledge profile** | none |
| **Created** | 2026-09-14 |

<!-- `Knowledge profile` is the doctrine this vault decomposes knowledge by, or `none`.
     It is not decoration: regeneration re-applies that profile's overlay to this skill's
     instructions, so a wrong value here silently produces the wrong skill. The doctrine itself is
     at `.wiki/knowledge-profile.md`; change which profile is in force with `reshape`, never by
     editing this row. -->

## Conventions

Standard markdown throughout. These were set when the vault was created, not detected — follow them,
never re-derive them, and never impose a different style.

| | |
|---|---|
| Links | **`[[wikilinks]]`**, resolved by note name — this is an Obsidian vault and 45 notes already use them. Never write `[text](path.md)` between notes. A link to a folder whose name contains a space must be percent-encoded if written as markdown (`[x](Quick%20note/note.md)`) |
| Anchors | Markdown anchors — `[Section](#Section%20Name)`. Older notes use `[[#Section\|Section]]`; both work, new TOCs use the markdown form |
| Frontmatter | **Present in 3 files only** (Kanban, Excalidraw plugin files). Do not assume it exists and **do not add it** to a note that has none |
| Filenames | **Mixed, deliberately** — Title Case, numbered prefixes (`0000001`), kebab-case, and German. Match the folder you are writing into; never normalise an existing name |
| Headings | One H1 per note, `##` for sections |
| Dates | ISO (`2026-08-01`) where present |
| Attachments | `resources/` or `images/` beside the note that uses them, per folder |

**These were detected from the vault at adopt time, not imposed.** They differ from a vault created
by `init`, which always uses standard markdown and kebab-case. Do not "correct" them.

## Accepted structure

The folders this vault already had when it was adopted on 2026-09-14. The authoritative record —
including each line's provenance — is `.wiki/structure-accepted.md`; this is the routing summary.

| Folder | Place here |
|---|---|
| `Dev/` | *(from index.md)* software development — programming languages, frontend frameworks, infrastructure and CI, architecture and decomposition research, and general engineering practice. |
| `Dev/architecture/` | *(from index.md)* system and software architecture — architectural patterns, deployment topologies, specification formats, and monolith-to-microservice decomposition methods and paper work. |
| `Dev/frontend/` | *(from index.md)* anything rendered in a browser or a mobile view — React, React Native, Skia canvas graphics, Redux state, micro-frontend integration. |
| `Dev/frontend/React JS/` | *(from index.md)* React on the web — components, hooks, DOM, build tooling. |
| `Dev/frontend/React-Native/` | *(from index.md)* React Native app development, including platform-specific iOS and Android setup. |
| `Dev/infra/` | *(from index.md)* everything around running and shipping software — CI servers, container platforms, log and metric pipelines, TLS certificates, and application security configuration. |
| `Dev/infra/TeamCity/` | *(from index.md)* TeamCity build server configuration. |
| `Dev/infra/elastic stack/` | *(from index.md)* Elasticsearch, the Beats agents, and the certificates they need. |
| `Dev/infra/openshift/` | *(from index.md)* OpenShift platform notes. |
| `Dev/infra/security/` | *(from index.md)* application and transport security — Spring Security internals, certificates, mutual TLS. |
| `Dev/languages/` | *(from index.md)* programming language reference notes — syntax, type systems, idioms, and language-specific runtime behaviour. |
| `Dev/languages/Python/` | *(from index.md)* Python language notes. Scratch scripts and notebooks live here too, but are not notes and are not indexed. |
| `Dev/practices/` | *(from index.md)* engineering practice not tied to a language or framework — reading code, reviewing, debugging, working with legacy systems. |
| `Dev/LLM/` | *(derived)* a code sandbox, not a notes folder — scratch source, prompts and experiment directories. AI *knowledge* goes in `AI/`; the maths behind it goes in `Mathematik/`. |
| `Dev/wk/` | *(derived)* _unclear — no routing rule derived._ Two notes; the folder name says nothing about what belongs in it. |
| `AI/` | *(from index.md)* AI and deep learning — transformer internals, LLM fine-tuning (LoRA/QLoRA), PyTorch, Hugging Face, tokenizers. Note that `Dev/LLM/` is a code sandbox, not an AI notes folder. |
| `AI/Transformer/` | *(from index.md)* transformer architecture internals, PyTorch (framework mechanics and LLM training), Hugging Face Transformers, parameter-efficient fine-tuning (LoRA/QLoRA), tokenizers, seq2seq, and tensor-shape walkthroughs. |
| `AI/tourch/` | *(derived)* PyTorch material, spelled `tourch`. One note; `AI/Transformer/` already covers PyTorch. |
| `PhD/` | *(from index.md)* **MSPC only** — multivariate statistical process control, fault diagnosis and attribution, PCA/T2/SPE methods, correlated-feature residual monitoring, noise handling, and framing this work for publication. Monolith-decomposition research does **not** belong here; it lives in `Dev/architecture/`. |
| `Banking/` | *(from index.md)* **generic** banking and securities regulation — MiFID II, WpHG, BaFin, target market (TaMrA), suitability statements (GEE), advisory duties. Anything naming an internal system (`Tamara`, `CPMS`, `Sau`/`WBF-E-SAU`, `DocFamily`, `Filiale`, `FRÜHSTART`, `AVD`) or a bank-specific API goes in `Banking/COBA/` instead. |
| `Banking/COBA/` | *(from index.md)* Commerzbank-specific banking knowledge — internal systems, APIs, product configurations and processes that only apply to this bank. |
| `Banking/COBA/AVD/` | *(derived)* the AVD subsystem — PIP configuration, subsidy calculation, and recommendation-compliance orchestration. |
| `Banking/COBA/op/, extante/, cancellation/, chain-traces/` | *(derived)* generated chain traces — one file per trigger, written by the `coba-chain-tracer` skill. Machine-written; never hand-file a note here. |
| `Banking/AV/` | *(derived)* the AV product area — refinement notes and evaluations. |
| `Mathematik/` | *(from index.md)* mathematics — vector and matrix operations, dot/cross/outer products, and the math foundations underlying machine learning (functions, graphing, polynomials, matrices, statistics, data analysis). |
| `Mathematik/dot-product/` | *(from index.md)* dot product mathematics — definition, notation, algebraic and geometric properties, applications. |
| `Mathematik/ml-foundations/` | *(from index.md)* the school-level mathematics needed to follow machine learning — variables, functions, graphing, polynomials, matrices and determinants, statistics and probability, data analysis. |
| `Work-life/` | *(from index.md)* workplace dynamics — diplomacy, handling feedback and criticism, assumptions, trigger situations, boundary communication, exit strategies, and self-help reflections on invalidation and exploitation at work. |
| `Quick note/` | *(from index.md)* miscellaneous short notes — Obsidian and LaTeX setup, model benchmarks, file sync, macOS configuration. |
| `Quick note/Benchmarks/` | *(from index.md)* benchmark results for AI models (tokens per second, hardware specs). |
| `Quick note/OS/` | *(from index.md)* macOS configuration notes — personal vs code environments, Pi agent setup with LM Studio. |
| `_utils/` | *(derived)* the vault's own tooling — system prompts, scripts, the MCP server log. Machinery, not knowledge; never route a note here. |
| `_templates/` | *(derived)* Obsidian note templates. Plugin folder — never route a note here. |
| `Excalidraw/` | *(from index.md)* Excalidraw drawings only. This is the Excalidraw plugin's configured folder — do not rename it. |
| `Kanban/` | *(from index.md)* Kanban board plans, in the obsidian-kanban plugin's format. |
| `Dairy/` | *(from index.md)* nothing manually. This is the Obsidian daily-notes folder (`.obsidian/daily-notes.json`); Obsidian creates dated notes here. Currently empty. Never rename or remove it. |

<!-- one row per accepted folder -->

A note that fits none of these is a signal the structure needs a new folder — flag it loudly rather
than forcing a bad placement. The structure was chosen deliberately, so departing from it is worth
saying out loud.

## Vault-specific decisions

Standing answers for this vault, added over time. A decision recorded here is **already made** —
never re-ask a question this section answers, and never propose a change it rules out. If the user
overrides one, apply the override *and* update this file in the same run.

<!-- e.g.
- `regulatory/` is authoritative for anything the bank is legally bound by. Internal process notes
  that merely reference a rule go in `processes/`, with a link.
- Client names are never written into notes. Use the account reference instead.
-->

_None recorded yet._

## Local modifications

Changes `enhance` mode made to this skill's **generated zone** — `SKILL.md`, `references/`,
`scripts/`, `assets/`. Everything listed here is **overwritten** the next time this artifact is
regenerated from the `wiki` package, and this list is the only thing that makes that visible.

A fix that keeps reappearing here belongs upstream in `wiki`'s template, not in this copy.

<!-- e.g.
- 2026-08-15 — `references/placement-rules.md`: the see-also rule fired on every near-miss rather
  than only strong secondary fits. Belongs upstream.
-->

_None._

## Paths

| | |
|---|---|
| Index | `index.md` |
| Manifest (derived, git-ignored) | `.wiki/manifest.json` |
| Search index | `.rag/bin/rag` |
| Domain context (shared) | `.wiki/domain-context.md` |
| Config (shared) | `.wiki/wiki-config.json` |
| Memory (personal, git-ignored) | `.wiki/memory_local.md` |
| Contributors (shared) | `.wiki/contributors.json` |
| Graph (derived, git-ignored) | `.wiki/graph.sqlite` |
| Ignored conflicts | `.wiki/conflicts_ignored.md` |
| Validation queue | `.wiki/todos_validations.md` |
| Remote instructions | `remote_instructions.md` (in this skill) |
| Knowledge gaps | `.wiki/wiki_gaps.md` |
| Staging | `.input/` |
