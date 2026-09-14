Adopted: 2026-09-14

# Structure, as adopted — engineering

The routing rules in force for this vault. Nothing here was created by `adopt`; every folder listed
already existed. Each line is tagged with where it came from:

- **`(from index.md)`** — your own routing line, taken verbatim from `index.md`, `Dev/index.md`,
  `AI/index.md` or `Quick note/index.md`. Not rewritten.
- **`(derived)`** — a folder your indexes had no `Place here:` line for. Derived from its contents.

Knowledge profile: **none**. Conventions detected: Obsidian, `[[wikilinks]]`, frontmatter in 3 files
only, mixed filename casing — all left as they are.

## Dev/

**Place here:** *(from index.md)* software development — programming languages, frontend frameworks,
infrastructure and CI, architecture and decomposition research, and general engineering practice.

- `Dev/index.md`, `How to Read and Understand Code Quickly.md`

## Dev/architecture/

**Place here:** *(from index.md)* system and software architecture — architectural patterns,
deployment topologies, specification formats, and monolith-to-microservice decomposition methods and
paper work.

- `Mix Architecture patterns - Infra-Deployment strategies.md`, `Monolithic decomposition/`

## Dev/frontend/

**Place here:** *(from index.md)* anything rendered in a browser or a mobile view — React, React
Native, Skia canvas graphics, Redux state, micro-frontend integration.

- `Themenblock.md`, `Redux_Toolkit_Notes.md`, `Skia-React-Native/`

## Dev/frontend/React JS/

**Place here:** *(from index.md)* React on the web — components, hooks, DOM, build tooling.

## Dev/frontend/React-Native/

**Place here:** *(from index.md)* React Native app development, including platform-specific iOS and
Android setup.

## Dev/infra/

**Place here:** *(from index.md)* everything around running and shipping software — CI servers,
container platforms, log and metric pipelines, TLS certificates, and application security
configuration.

## Dev/infra/TeamCity/

**Place here:** *(from index.md)* TeamCity build server configuration.

## Dev/infra/elastic stack/

**Place here:** *(from index.md)* Elasticsearch, the Beats agents, and the certificates they need.

## Dev/infra/openshift/

**Place here:** *(from index.md)* OpenShift platform notes.

## Dev/infra/security/

**Place here:** *(from index.md)* application and transport security — Spring Security internals,
certificates, mutual TLS.

## Dev/languages/

**Place here:** *(from index.md)* programming language reference notes — syntax, type systems,
idioms, and language-specific runtime behaviour.

- `java-functional-interfaces.md`, `javascript-loops.md`, `Kotlin/`

## Dev/languages/Python/

**Place here:** *(from index.md)* Python language notes. Scratch scripts and notebooks live here too,
but are not notes and are not indexed.

## Dev/practices/

**Place here:** *(from index.md)* engineering practice not tied to a language or framework — reading
code, reviewing, debugging, working with legacy systems.

## Dev/LLM/

**Place here:** *(derived)* a code sandbox, not a notes folder — scratch source, prompts and
experiment directories. AI *knowledge* goes in `AI/`; the maths behind it goes in `Mathematik/`.

## Dev/wk/

**Place here:** *(derived)* _unclear — no routing rule derived._ Two notes; the folder name says
nothing about what belongs in it.

## AI/

**Place here:** *(from index.md)* AI and deep learning — transformer internals, LLM fine-tuning
(LoRA/QLoRA), PyTorch, Hugging Face, tokenizers. Note that `Dev/LLM/` is a code sandbox, not an AI
notes folder.

## AI/Transformer/

**Place here:** *(from index.md)* transformer architecture internals, PyTorch (framework mechanics
and LLM training), Hugging Face Transformers, parameter-efficient fine-tuning (LoRA/QLoRA),
tokenizers, seq2seq, and tensor-shape walkthroughs.

- `How Transformers Process Seq.md`, `LoRa.md`, `transformer_qkv_notes.md`

## AI/tourch/

**Place here:** *(derived)* PyTorch material, spelled `tourch`. One note; `AI/Transformer/` already
covers PyTorch.

## PhD/

**Place here:** *(from index.md)* **MSPC only** — multivariate statistical process control, fault
diagnosis and attribution, PCA/T2/SPE methods, correlated-feature residual monitoring, noise
handling, and framing this work for publication. Monolith-decomposition research does **not** belong
here; it lives in `Dev/architecture/`.

- `pca-t2-spe-attribution-methods.md`, `hawkins-decomposition-t2-fault-diagnosis.md`

## Banking/

**Place here:** *(from index.md)* **generic** banking and securities regulation — MiFID II, WpHG,
BaFin, target market (TaMrA), suitability statements (GEE), advisory duties. Anything naming an
internal system (`Tamara`, `CPMS`, `Sau`/`WBF-E-SAU`, `DocFamily`, `Filiale`, `FRÜHSTART`, `AVD`) or
a bank-specific API goes in `Banking/COBA/` instead.

## Banking/COBA/

**Place here:** *(from index.md)* Commerzbank-specific banking knowledge — internal systems, APIs,
product configurations and processes that only apply to this bank.

- `commerzbank-identity-model-updated.md`, `customer-ids-relations.md`

## Banking/COBA/AVD/

**Place here:** *(derived)* the AVD subsystem — PIP configuration, subsidy calculation, and
recommendation-compliance orchestration.

## Banking/COBA/op/, extante/, cancellation/, chain-traces/

**Place here:** *(derived)* generated chain traces — one file per trigger, written by the
`coba-chain-tracer` skill. Machine-written; never hand-file a note here.

## Banking/AV/

**Place here:** *(derived)* the AV product area — refinement notes and evaluations.

## Mathematik/

**Place here:** *(from index.md)* mathematics — vector and matrix operations, dot/cross/outer
products, and the math foundations underlying machine learning (functions, graphing, polynomials,
matrices, statistics, data analysis).

## Mathematik/dot-product/

**Place here:** *(from index.md)* dot product mathematics — definition, notation, algebraic and
geometric properties, applications.

## Mathematik/ml-foundations/

**Place here:** *(from index.md)* the school-level mathematics needed to follow machine learning —
variables, functions, graphing, polynomials, matrices and determinants, statistics and probability,
data analysis.

## Work-life/

**Place here:** *(from index.md)* workplace dynamics — diplomacy, handling feedback and criticism,
assumptions, trigger situations, boundary communication, exit strategies, and self-help reflections
on invalidation and exploitation at work.

## Quick note/

**Place here:** *(from index.md)* miscellaneous short notes — Obsidian and LaTeX setup, model
benchmarks, file sync, macOS configuration.

## Quick note/Benchmarks/

**Place here:** *(from index.md)* benchmark results for AI models (tokens per second, hardware
specs).

## Quick note/OS/

**Place here:** *(from index.md)* macOS configuration notes — personal vs code environments, Pi agent
setup with LM Studio.

## _utils/

**Place here:** *(derived)* the vault's own tooling — system prompts, scripts, the MCP server log.
Machinery, not knowledge; never route a note here.

## _templates/

**Place here:** *(derived)* Obsidian note templates. Plugin folder — never route a note here.

## Excalidraw/

**Place here:** *(from index.md)* Excalidraw drawings only. This is the Excalidraw plugin's
configured folder — do not rename it.

## Kanban/

**Place here:** *(from index.md)* Kanban board plans, in the obsidian-kanban plugin's format.

## Dairy/

**Place here:** *(from index.md)* nothing manually. This is the Obsidian daily-notes folder
(`.obsidian/daily-notes.json`); Obsidian creates dated notes here. Currently empty. Never rename or
remove it.
