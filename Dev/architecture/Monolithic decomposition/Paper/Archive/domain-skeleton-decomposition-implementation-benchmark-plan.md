# Implementation and Benchmark Plan for the Domain-Skeleton Microservice Decomposition Paper

> Purpose: give this file to a coding agent together with:
>
> 1. the paper scaffold Markdown,
> 2. the novelty/report document,
> 3. the original method draft.
>
> The coding agent should implement a minimal but credible prototype and run benchmarks without first building a full static graph extractor.
>
> Main strategy:
>
> Use existing Mono2Micro replication data as the first input layer, then implement this paper's contribution on top:
>
> - responsibility records,
> - controlled vocabularies,
> - domain skeleton,
> - contamination/coherence/redundancy scoring,
> - iterative refinement,
> - audit logging,
> - benchmark report.

---

## 0. Main Decision

Do **not** start by building a full Java static analyzer.

The paper's main contribution is the decomposition framework, not graph extraction. To save time, the first prototype should consume existing extracted/runtime benchmark data from the Mono2Micro replication package.

Use graph extraction only as future work or optional extension.

### Required paper wording

Insert this paragraph into the paper, probably in the implementation/evaluation section:

> In this prototype, we evaluate the decomposition method using existing extracted runtime and decomposition data from the Mono2Micro replication package. This isolates the contribution of the present work: domain-skeleton-constrained placement, responsibility-record enrichment, interpretable scoring, redundancy handling, and iterative refinement. Full end-to-end extraction from source code is outside the scope of this prototype and is treated as future work.

Slightly stronger version if source-code inspection is also used:

> In this prototype, we use the Mono2Micro replication package as the primary source of extracted runtime and decomposition artifacts, and we supplement it with lightweight source-code inspection where needed to recover names, packages, data-source references, and responsibility descriptions. This allows the evaluation to focus on the decomposition method rather than on reimplementing a full extractor.

Use the first version if the agent uses only the dataset. Use the second version if the agent also parses or inspects Java source.

---

## 1. Repository Links

### 1.1 Primary benchmark data repository

Mono2Micro FSE 2021 replication package:

https://github.com/kaliaanup/Mono2Micro-FSE-2021

Important folders:

https://github.com/kaliaanup/Mono2Micro-FSE-2021/tree/master/datasets_runtime

Expected applications:

- `acmeair`
- `daytrader`
- `jpetstore`
- `plants`

The coding agent must inspect the repository structure first and document exactly which files are used as input and which are used as baseline output.

### 1.2 Source repositories for optional source-code enrichment

Use these only if the dataset does not contain enough names/metadata for responsibility records or tag generation.

DayTrader 8:

https://github.com/OpenLiberty/sample.daytrader8

DayTrader 7:

https://github.com/WASdev/sample.daytrader7

PlantsByWebSphere:

https://github.com/WASdev/sample.plantsbywebsphere

AcmeAir monolithic Java:

https://github.com/blueperf/acmeair-monolithic-java

Optional advanced benchmark, only if time remains:

https://github.com/cloudhubs/train-ticket-monolith

Original TrainTicket microservice benchmark, useful only as reference context:

https://github.com/cloudhubs/train-ticket

### 1.3 Recommended benchmark priority

Use this order:

1. `jpetstore` — first smoke test.
2. `daytrader` — main paper case study.
3. `plants` — second small benchmark.
4. `acmeair` — second serious benchmark if time allows.
5. `train-ticket-monolith` — optional later extension, not required for the first paper.

---

## 2. What the Prototype Must Prove

The prototype does not need to prove every idea in the paper.

It must prove this narrower claim:

> Given existing monolith dependency/runtime decomposition data, the proposed method can enrich components with responsibility records, place candidate services into a domain skeleton, compute interpretable contamination/coherence/redundancy scores, refine the decomposition through auditable operations, and compare the resulting decomposition against baseline outputs.

The prototype must produce:

1. normalized input artifacts,
2. responsibility records,
3. tag inventories,
4. domain skeletons,
5. initial decompositions,
6. score reports,
7. refinement iterations,
8. audit logs,
9. benchmark comparison reports,
10. paper-ready tables and figures.

---

## 3. Expected Final Repository Structure

The coding agent should create a new repository or project directory with this structure:

```text
domain-skeleton-decomposition/
  README.md
  pyproject.toml or requirements.txt

  data/
    raw/
      mono2micro/
        Mono2Micro-FSE-2021/
      sources/
        sample.daytrader8/
        acmeair-monolithic-java/
        sample.plantsbywebsphere/
    processed/
      jpetstore/
      daytrader/
      plants/
      acmeair/
    outputs/
      jpetstore/
      daytrader/
      plants/
      acmeair/

  configs/
    datasets.yaml
    scoring.yaml
    llm.yaml
    benchmark.yaml

  src/
    dsdecomp/
      __init__.py

      ingest/
        mono2micro_loader.py
        source_metadata_loader.py
        normalizer.py

      model/
        schema.py
        graph.py
        decomposition.py
        responsibility.py
        tags.py
        skeleton.py
        audit.py

      enrichment/
        responsibility_generator.py
        tagger.py
        inventory_manager.py
        skeleton_builder.py

      scoring/
        contamination.py
        coherence.py
        redundancy.py
        objective.py

      refinement/
        detect.py
        identify.py
        search.py
        propose.py
        judge.py
        apply.py
        loop.py

      evaluation/
        metrics.py
        baseline_compare.py
        ablation.py
        sensitivity.py
        report_builder.py

      cli.py

  prompts/
    responsibility_record.md
    tag_assignment.md
    skeleton_inference.md
    llm_judge.md

  scripts/
    00_download_data.sh
    01_inspect_mono2micro_data.py
    02_normalize_dataset.py
    03_generate_responsibilities.py
    04_build_domain_skeleton.py
    05_initial_decomposition.py
    06_score_decomposition.py
    07_run_refinement.py
    08_run_benchmarks.py
    09_generate_paper_tables.py

  notebooks/
    exploratory_data_inspection.ipynb

  paper_artifacts/
    tables/
    figures/
    snippets/
    logs/

  tests/
    test_schema.py
    test_contamination.py
    test_redundancy.py
    test_refinement.py
```

If the agent prefers a simpler structure, it may simplify, but it must preserve the outputs listed in Section 13.

---

## 4. Phase 1 — Download and Inspect Existing Data

### Goal

Understand the Mono2Micro replication data format before implementing anything.

### Tasks

1. Clone the repository:

```bash
git clone https://github.com/kaliaanup/Mono2Micro-FSE-2021.git data/raw/mono2micro/Mono2Micro-FSE-2021
```

2. Inspect:

```bash
find data/raw/mono2micro/Mono2Micro-FSE-2021/datasets_runtime -maxdepth 4 -type f | sort
```

3. For each benchmark app, inspect filenames and formats:

```bash
find data/raw/mono2micro/Mono2Micro-FSE-2021/datasets_runtime/jpetstore -maxdepth 5 -type f | sort
find data/raw/mono2micro/Mono2Micro-FSE-2021/datasets_runtime/daytrader -maxdepth 5 -type f | sort
find data/raw/mono2micro/Mono2Micro-FSE-2021/datasets_runtime/plants -maxdepth 5 -type f | sort
find data/raw/mono2micro/Mono2Micro-FSE-2021/datasets_runtime/acmeair -maxdepth 5 -type f | sort
```

4. Create an inspection report:

```text
paper_artifacts/logs/dataset_inspection.md
```

The report must document:

- available files per app,
- file format,
- what each file appears to represent,
- which files contain input data,
- which files contain output decompositions,
- whether class names/method names are available,
- whether runtime traces are available,
- whether baseline cluster assignments are available,
- whether ground-truth or expert assignments are available.

### Deliverable

`paper_artifacts/logs/dataset_inspection.md`

### Acceptance criteria

The agent must not proceed to Phase 2 until it can answer:

- What is the smallest input artifact needed to build the normalized graph?
- Which file contains Mono2Micro output?
- Which file can serve as baseline decomposition?
- Are components class-level, method-level, or transaction-level?
- Are package names available?

---

## 5. Phase 2 — Define Normalized Internal Schema

### Goal

Create a stable internal representation independent of the Mono2Micro file format.

### Required entities

#### Application

```json
{
  "app_id": "daytrader",
  "name": "DayTrader",
  "source": "mono2micro_replication",
  "notes": []
}
```

#### Component

```json
{
  "component_id": "...",
  "app_id": "...",
  "name": "...",
  "qualified_name": "...",
  "kind": "class | method | transaction | unknown",
  "package": "...",
  "source_file": "...",
  "metadata": {}
}
```

#### ActionPoint

If action points are not explicitly available in the Mono2Micro data, infer or leave as unknown.

```json
{
  "action_point_id": "...",
  "app_id": "...",
  "trigger_type": "REST | SERVLET | JSP | SOAP | SCHEDULER | BATCH | MQ | GRAPHQL | GRPC | CLI | WEBHOOK | UNKNOWN",
  "name": "...",
  "entry_component_id": "...",
  "package": "...",
  "chain_component_ids": [],
  "metadata": {}
}
```

#### DataSource

If exact data sources are not available, create placeholder data sources from table names, DAO names, repository classes, or leave empty.

```json
{
  "data_source_id": "...",
  "app_id": "...",
  "name": "...",
  "kind": "table | database | queue | topic | external_api | unknown",
  "accessed_by_component_ids": [],
  "metadata": {}
}
```

#### BaselineDecomposition

```json
{
  "app_id": "...",
  "baseline_name": "mono2micro",
  "clusters": [
    {
      "cluster_id": "...",
      "component_ids": []
    }
  ]
}
```

#### OurDecomposition

```json
{
  "app_id": "...",
  "run_id": "...",
  "microservices": [
    {
      "microservice_id": "...",
      "name": "...",
      "domain_path": ["...", "...", "..."],
      "component_ids": [],
      "action_point_ids": [],
      "data_source_ids": []
    }
  ]
}
```

### Tasks

1. Implement dataclasses or Pydantic models.
2. Implement JSON serialization.
3. Implement validation checks:
   - no duplicate component IDs,
   - all assigned IDs exist,
   - every component is assigned or explicitly excluded,
   - every microservice has a domain path,
   - no invalid tag depth.

### Deliverables

- `src/dsdecomp/model/schema.py`
- `tests/test_schema.py`
- JSON schema examples in `data/processed/example_schema/`

---

## 6. Phase 3 — Build Mono2Micro Loader

### Goal

Convert Mono2Micro replication files into the normalized schema.

### Tasks

1. Implement:

```text
src/dsdecomp/ingest/mono2micro_loader.py
```

2. The loader should support all four apps:

- `jpetstore`
- `daytrader`
- `plants`
- `acmeair`

3. The loader should produce:

```text
data/processed/<app>/components.json
data/processed/<app>/action_points.json
data/processed/<app>/data_sources.json
data/processed/<app>/baseline_mono2micro.json
data/processed/<app>/raw_manifest.json
```

4. If the dataset lacks action points or data sources, do not fake high-confidence data. Use:

```json
"trigger_type": "UNKNOWN"
```

or:

```json
"data_source_id": "unknown"
```

and record the limitation in:

```text
data/processed/<app>/limitations.md
```

### Important instruction

Do not over-engineer this phase. The goal is to get usable benchmark inputs quickly.

If exact action points are unavailable, the first paper can still evaluate the core placement and scoring using components/clusters.

### Deliverables

- Loader code.
- Processed JSON for at least `jpetstore` and `daytrader`.
- Limitations file for each app.

### Acceptance criteria

The following command should work:

```bash
python scripts/02_normalize_dataset.py --app jpetstore
python scripts/02_normalize_dataset.py --app daytrader
```

and produce processed JSON files.

---

## 7. Phase 4 — Optional Source-Code Metadata Enrichment

### Goal

Improve names, packages, and possible responsibility descriptions using source repositories, but do not build a full extractor.

### Use only if needed

This phase is optional. Do it only if the Mono2Micro data does not contain enough names for useful responsibility records.

### Tasks

1. Clone source repos as needed.

For DayTrader:

```bash
git clone https://github.com/OpenLiberty/sample.daytrader8.git data/raw/sources/sample.daytrader8
```

For AcmeAir:

```bash
git clone https://github.com/blueperf/acmeair-monolithic-java.git data/raw/sources/acmeair-monolithic-java
```

For Plants:

```bash
git clone https://github.com/WASdev/sample.plantsbywebsphere.git data/raw/sources/sample.plantsbywebsphere
```

2. Implement lightweight source lookup:

```text
src/dsdecomp/ingest/source_metadata_loader.py
```

3. The source lookup should map qualified class names to:

- source file path,
- package name,
- class name,
- method names,
- imports,
- annotations,
- short code snippet.

4. Do not implement complete call graph extraction.

### Deliverable

```text
data/processed/<app>/source_metadata.json
```

### Paper wording if this phase is used

Insert into implementation section:

> Source repositories were used only for lightweight metadata enrichment, such as package names, class names, annotations, and code snippets for responsibility-record generation. The prototype does not implement a full static call-graph extractor; dependency and runtime artifacts are taken from the Mono2Micro replication package.

---

## 8. Phase 5 — Responsibility Record Generation

### Goal

Generate structured responsibility records for each business component.

### Input

```text
data/processed/<app>/components.json
data/processed/<app>/source_metadata.json  # optional
```

### Output

```text
data/processed/<app>/responsibility_records.json
data/processed/<app>/responsibility_inventory.json
```

### Responsibility record schema

```json
{
  "component_id": "...",
  "action_verb": "...",
  "object": "...",
  "description": "...",
  "inputs": [],
  "outputs": [],
  "data_sources_touched": [],
  "tags": {
    "L1": "...",
    "L2": "...",
    "L3": "..."
  },
  "confidence": "high | medium | low",
  "evidence": [
    {
      "type": "component_name | package | source_snippet | dataset",
      "value": "..."
    }
  ]
}
```

### Implementation modes

Support two modes:

#### Mode A — Heuristic mode

Use component names and package names to derive approximate records.

Example rules:

- `AccountProfileDataBean`:
  - action_verb: `manage`
  - object: `account-profile`
  - L1: `account`
  - L2: `profile`
  - L3: `account-profile-management`

- `TradeOrder`:
  - action_verb: `execute`
  - object: `trade-order`
  - L1: `trading`
  - L2: `order`
  - L3: `trade-order-execution`

#### Mode B — LLM mode

Use an LLM prompt to generate the record from:

- component name,
- package,
- optional source snippet,
- neighboring components,
- existing vocabulary.

The LLM must return strict JSON.

### Prompt file

Create:

```text
prompts/responsibility_record.md
```

The prompt must instruct:

- reuse existing `action_verb` if possible,
- reuse existing `object` if possible,
- reuse existing tags if possible,
- create new vocabulary only if necessary,
- include confidence,
- include evidence.

### Required fallback

If no LLM API is configured, heuristic mode must still run.

### Acceptance criteria

For `jpetstore` and `daytrader`, the agent must generate responsibility records for all components.

---

## 9. Phase 6 — Controlled Vocabulary and Tag Inventory

### Goal

Prevent uncontrolled tag explosion.

### Files

For each app:

```text
data/processed/<app>/inventories/
  action_verbs.json
  objects.json
  service_tags.json
  data_source_tags.json
  domain_nodes.json
```

### Tasks

1. Implement inventory manager:

```text
src/dsdecomp/enrichment/inventory_manager.py
```

2. Features:

- lookup existing term,
- add new term,
- alias term,
- merge terms,
- split term,
- export inventory statistics.

3. Track:

- number of terms created,
- number of terms reused,
- number of low-confidence terms,
- number of manual or automatic merges.

### Output report

```text
paper_artifacts/tables/vocabulary_growth_<app>.csv
```

### Paper text

Insert into method section:

> Controlled vocabularies are maintained as explicit artifacts rather than implicit prompt context. The prototype records vocabulary creation, reuse, and correction events so that tag stability can be measured during evaluation.

---

## 10. Phase 7 — Domain Skeleton Construction

### Goal

Create or infer a domain hierarchy for each benchmark.

### Output

```text
data/processed/<app>/domain_skeleton.json
```

### Skeleton schema

```json
{
  "app_id": "...",
  "source": "manual | inferred | hybrid",
  "nodes": [
    {
      "node_id": "trading/order",
      "path": ["trading", "order"],
      "label": "Order",
      "parent": "trading",
      "description": "..."
    }
  ]
}
```

### Minimal manual skeletons

The first prototype may use simple manually written skeletons based on benchmark domain names.

#### JPetStore example

```text
catalog
  product
  category
  inventory
account
  customer
  profile
order
  cart
  checkout
  payment
```

#### DayTrader example

```text
account
  profile
  authentication
portfolio
  holdings
  account-summary
trading
  quote
  order
  buy-sell
market
  pricing
  symbols
infrastructure
  messaging
  notifications
```

#### Plants example

```text
catalog
  plants
  product-details
customer
  profile
order
  shopping-cart
  checkout
admin
  inventory
```

#### AcmeAir example

```text
customer
  profile
  authentication
flight
  search
  schedule
booking
  reservation
  cancellation
loyalty
  miles
```

### Important

Manual skeletons are acceptable for the first paper if documented.

The paper should say:

> For benchmark systems, we used compact manually defined domain skeletons derived from the application domain descriptions and component names. This reflects the intended enterprise use case, where a domain catalog or capability map is available before decomposition. We also evaluate sensitivity to imperfect skeletons by removing or perturbing selected nodes.

### Optional inferred skeleton

Implement only if time allows:

```text
src/dsdecomp/enrichment/skeleton_builder.py
```

Input:

- all responsibility records,
- service tags,
- object vocabulary,
- component packages.

Output:

- proposed L1/L2/L3 domain tree.

---

## 11. Phase 8 — Initial Decomposition

### Goal

Produce this method's initial decomposition.

### Inputs

- components,
- optional action points,
- optional data sources,
- responsibility records,
- domain skeleton,
- Mono2Micro baseline decomposition.

### Important design choice

There are two possible initial modes.

#### Mode A — Baseline-seeded mode

Start from Mono2Micro clusters and place each cluster into the domain skeleton.

This is fastest and fair for evaluating the scoring/refinement layer.

Paper wording:

> To isolate the effect of the proposed scoring and refinement model, we initialize the prototype from the clusters available in the Mono2Micro replication package and place each cluster into the closest domain-skeleton node. Refinement is then performed by our contamination, coherence, and redundancy model.

#### Mode B — Our cascade mode

Implement the paper's cascading initial assignment:

1. group by package prefix,
2. split by service L1/L2 tags,
3. split by data-source L1/L2 tags if available,
4. place group at minimum-contamination domain node.

Paper wording:

> We also evaluate a fully method-native initialization that groups components by package proximity and recursively splits groups using service and data-source tag diversity.

### Recommendation

Implement both if possible.

If time is limited:

1. Implement Mode A first.
2. Implement Mode B second.
3. In the paper, report Mode A as `DSD-seeded` and Mode B as `DSD-native`.

### Outputs

```text
data/outputs/<app>/initial_decomposition_baseline_seeded.json
data/outputs/<app>/initial_decomposition_native.json
```

### Acceptance criteria

Every component must be either:

- assigned to a microservice,
- assigned to shared/cross-cutting,
- explicitly marked unassigned with a reason.

---

## 12. Phase 9 — Contamination Scoring

### Goal

Implement the first core score.

### Formula

For component tag path `T` and microservice domain path `P`:

```text
d(T, P) = sum over mismatch depth i of w^(max_depth - i)
```

Default:

```text
w = 3
max_depth = 3
```

Example:

- L1 mismatch = 9
- L2 mismatch = 3
- L3 mismatch = 1

### Required implementation

```text
src/dsdecomp/scoring/contamination.py
```

### Required outputs

For each decomposition:

```text
data/outputs/<app>/scores/contamination.json
paper_artifacts/tables/contamination_<app>.csv
```

Each row:

```text
app, run_id, microservice_id, component_id, component_tag, microservice_path, contamination, source
```

### Required aggregate values

- total contamination,
- average contamination per component,
- max microservice contamination,
- contamination concentration,
- top 10 contaminating components.

### Acceptance criteria

The agent must produce a readable table like:

```text
Top contaminating components in DayTrader:
1. Component X, tag trading/order, placed in account/profile, cost 12
2. Component Y, tag market/quote, placed in portfolio/holdings, cost 6
...
```

---

## 13. Phase 10 — Redundancy Scoring

### Goal

Implement the second strongest contribution: redundancy with justified duplication.

### Required stages

#### Stage 1 — literal duplication

Same component ID appears in multiple microservices.

#### Stage 2 — structured responsibility duplication

Two different components in different microservices share:

```text
(action_verb, object)
```

#### Stage 3 — semantic description similarity

Optional for first prototype. Use embedding similarity if available. If not, use lexical similarity as placeholder and mark it as prototype limitation.

### Resolution labels

Each redundancy candidate must receive one of:

```text
eliminate
lift_to_shared
accept_justified
needs_human_review
```

### Whitelisted accepted reasons

```text
bounded_context_duplication
operational_independence
anti_corruption_layer
latency_critical_locality
```

### Required implementation

```text
src/dsdecomp/scoring/redundancy.py
```

### Required output

```text
data/outputs/<app>/scores/redundancy.json
paper_artifacts/tables/redundancy_<app>.csv
```

### Paper text

Insert into paper:

> Redundancy is not treated as an unconditional defect. The prototype detects literal, structured, and semantic redundancy, but resolutions distinguish harmful duplication from intentional duplication. A redundancy instance may be eliminated, lifted to a shared component, or accepted only under a closed set of explicit architectural reasons.

---

## 14. Phase 11 — Coherence Scoring

### Goal

Implement a simple but useful coherence score.

### Minimal coherence formula

For each microservice:

```text
coherence =
  service_tag_agreement
  + domain_path_agreement
  + data_source_locality
  - cross_microservice_chain_penalty
  - shared_data_source_penalty
```

If action chains/data sources are not available, use only:

```text
coherence =
  service_tag_agreement
  + domain_path_agreement
```

and document limitation.

### Service tag agreement

For each microservice:

```text
L1_agreement = proportion of components sharing the majority L1 tag
L2_agreement = proportion of components sharing the majority L2 tag
L3_agreement = proportion of components sharing the majority L3 tag
```

Weighted formula:

```text
service_tag_agreement = 1.0 * L1_agreement + 1.5 * L2_agreement + 2.0 * L3_agreement
```

### Required implementation

```text
src/dsdecomp/scoring/coherence.py
```

### Required output

```text
data/outputs/<app>/scores/coherence.json
paper_artifacts/tables/coherence_<app>.csv
```

### Paper wording for prototype limitation

Use this if data sources/action chains are incomplete:

> In the current prototype, coherence is computed from service-tag agreement and domain-path agreement for all benchmarks. Data-source locality, transaction boundaries, and chain-crossing penalties are included in the framework definition but are only evaluated when the benchmark data exposes the required information.

---

## 15. Phase 12 — Iterative Refinement

### Goal

Implement the minimal refinement loop.

### Required operation for first version

Implement **move**.

Optional:

- lift-to-shared,
- split,
- merge.

Do not spend too much time implementing split/merge before move works.

### Move operation

1. Detect top contaminated microservice.
2. Identify top contaminated component.
3. Search domain skeleton for closest existing or new microservice path matching the component tag.
4. Compute hypothetical score delta if moved.
5. Accept if:
   - contamination decreases,
   - hard constraints are not violated,
   - coherence does not collapse beyond threshold.

### Required implementation files

```text
src/dsdecomp/refinement/detect.py
src/dsdecomp/refinement/identify.py
src/dsdecomp/refinement/search.py
src/dsdecomp/refinement/propose.py
src/dsdecomp/refinement/apply.py
src/dsdecomp/refinement/loop.py
```

### Minimal loop

```text
for iteration in range(max_iterations):
    compute scores
    select top contaminated component
    find best target microservice/domain path
    propose move
    apply if score improves
    write audit log
    stop if no accepted move
```

### Required output

```text
data/outputs/<app>/iterations/iteration_000.json
data/outputs/<app>/iterations/iteration_001.json
...
data/outputs/<app>/audit_log.jsonl
paper_artifacts/tables/refinement_summary_<app>.csv
```

### Acceptance criteria

For at least `jpetstore` and `daytrader`, the agent must show:

- initial score,
- score after each iteration,
- final score,
- list of accepted moves,
- list of rejected moves,
- reason for each decision.

---

## 16. Phase 13 — LLM Judge

### Goal

Implement a bounded LLM judge, but do not make the prototype depend on it.

### Design

The deterministic algorithm should work without the LLM.

The LLM judge is used only when:

- score delta is small,
- move improves contamination but hurts coherence,
- redundancy candidate may be intentional,
- tag looks suspicious.

### Judge output schema

```json
{
  "decision": "confirm | reject | request_human_review | suggest_tag_refinement",
  "reason_code": "...",
  "reason_text": "...",
  "confidence": "high | medium | low",
  "suggested_updates": []
}
```

### Allowed reason codes

For move rejection:

```text
usage_locality
transaction_integrity
tag_mistagging
adapter_or_facade
insufficient_evidence
```

For redundancy acceptance:

```text
bounded_context_duplication
operational_independence
anti_corruption_layer
latency_critical_locality
```

### Required implementation

```text
src/dsdecomp/refinement/judge.py
prompts/llm_judge.md
```

### Required fallback

If no LLM key is available:

- return deterministic confirmation,
- mark judge mode as `disabled`,
- still write audit logs.

### Paper wording

Use this if LLM judge is implemented but not central:

> The LLM judge is deliberately non-load-bearing: the deterministic refinement loop can run without it. In the prototype, the judge is used only for borderline moves and redundancy cases, and every override is logged with a closed reason code.

---

## 17. Phase 14 — Human Rule Simulation

### Goal

Implement human constraints without needing an actual UI.

### Human rules file

Create:

```text
configs/human_rules_<app>.yaml
```

Example:

```yaml
forced_together:
  - id: rule_001
    components: ["AccountProfileDataBean", "AccountDataBean"]
    reason: "Account profile and account data share lifecycle."

forced_apart:
  - id: rule_002
    components: ["QuoteDataBean", "AccountProfileDataBean"]
    reason: "Market quote and account profile are separate domains."

anchor_data_sources: []

ignored_data_sources: []

tag_overrides:
  - component: "QuoteDataBean"
    tags:
      L1: "market"
      L2: "quote"
      L3: "quote-data"

domain_rules:
  - id: rule_003
    match:
      tag_L1: "account"
    must_live_under: "account"
```

### Required implementation

- Rules are hard constraints.
- Move proposals violating rules are rejected.
- Rule effects are logged.

### Required output

```text
data/outputs/<app>/human_rule_effects.json
```

### Paper wording

> Human input is represented as explicit machine-readable constraints rather than informal intervention. This allows the prototype to replay, audit, and ablate human guidance.

---

## 18. Phase 15 — Benchmark Runs

### Goal

Run the method on selected benchmarks.

### Required benchmark set

Minimum credible set:

```text
jpetstore
daytrader
plants
```

Recommended if time allows:

```text
acmeair
```

Optional only:

```text
train-ticket-monolith
```

### Required commands

Create one command that runs all:

```bash
python scripts/08_run_benchmarks.py --apps jpetstore daytrader plants
```

Optional:

```bash
python scripts/08_run_benchmarks.py --apps jpetstore daytrader plants acmeair
```

### Required modes

Run at least:

1. `baseline_seeded_no_refinement`
2. `baseline_seeded_refined`
3. `native_initial_no_refinement` if native initialization exists
4. `native_initial_refined` if native initialization exists

### Required output directory

```text
data/outputs/<app>/runs/<run_id>/
  decomposition_initial.json
  decomposition_final.json
  scores_initial.json
  scores_final.json
  audit_log.jsonl
  refinement_summary.csv
  limitations.md
```

### Required summary table

```text
paper_artifacts/tables/main_results.csv
```

Columns:

```text
app,
mode,
num_components,
num_initial_microservices,
num_final_microservices,
initial_contamination,
final_contamination,
contamination_delta,
initial_coherence,
final_coherence,
coherence_delta,
initial_redundancy,
final_redundancy,
num_moves,
num_rejected_moves,
num_accepted_duplications,
runtime_seconds
```

---

## 19. Phase 16 — Baseline Comparison

### Goal

Compare this method with Mono2Micro output, not necessarily beat it on every metric.

### Comparison types

#### Type 1 — Score comparison

Score Mono2Micro's own clusters using this method's scores.

Then score this method's refined clusters.

Report:

- contamination difference,
- coherence difference,
- redundancy difference.

This is easy and directly supports the paper.

#### Type 2 — Cluster similarity

If ground truth or baseline cluster assignments exist:

- compute overlap,
- pairwise precision/recall,
- adjusted Rand index if feasible,
- MoJoFM if feasible.

#### Type 3 — Qualitative comparison

For DayTrader, show:

- Mono2Micro cluster,
- our domain placement,
- contamination problems found,
- refinement moves,
- final decomposition.

### Important paper positioning

Do not claim:

> We outperform Mono2Micro.

unless the metrics clearly support it.

Safer claim:

> The proposed method produces a complementary, domain-aligned interpretation and refinement of decomposition candidates generated from existing runtime data.

Stronger claim if results support it:

> The proposed method reduces domain contamination and harmful redundancy while preserving comparable cluster similarity to existing decompositions.

---

## 20. Phase 17 — Ablation Study

### Goal

Show which parts of the framework matter.

### Required ablations

Minimum:

1. without domain skeleton:
   - group by tags but do not place in hierarchy.
2. without responsibility records:
   - use component names only.
3. without redundancy whitelist:
   - treat all duplicates as harmful.
4. without refinement:
   - initial decomposition only.

Optional:

5. without LLM judge.
6. without human rules.
7. contamination-only objective.
8. random skeleton perturbation.

### Required output

```text
paper_artifacts/tables/ablation_results.csv
```

Columns:

```text
app,
ablation,
contamination,
coherence,
redundancy,
num_microservices,
num_moves,
notes
```

### Paper text

> The ablation study is designed to test whether the framework's integration is necessary. In particular, we compare the full method against variants without the domain skeleton, without responsibility records, without justified duplication, and without iterative refinement.

---

## 21. Phase 18 — Sensitivity Analysis

### Goal

Answer reviewer objection: "too many parameters."

### Parameters

Test:

```text
w in {2, 3, 4}
tag_diversity_L1_threshold in {1, 2, 3}
tag_diversity_L2_threshold in {2, 3, 4}
redundancy_similarity_threshold in {0.75, 0.85, 0.90}
top_k_destinations in {1, 3, 5}
max_iterations in {5, 10, 20}
```

Only test parameters that are actually implemented.

### Required output

```text
paper_artifacts/tables/sensitivity_results.csv
paper_artifacts/figures/sensitivity_contamination.png
paper_artifacts/figures/sensitivity_coherence.png
```

### Paper text

> We report sensitivity analysis for the main interpretable parameters. The goal is not to tune a hidden model but to show how architectural preferences affect decomposition results.

---

## 22. Phase 19 — Paper Artifacts

### Required tables

Generate these:

```text
paper_artifacts/tables/dataset_summary.csv
paper_artifacts/tables/main_results.csv
paper_artifacts/tables/refinement_summary.csv
paper_artifacts/tables/ablation_results.csv
paper_artifacts/tables/sensitivity_results.csv
paper_artifacts/tables/redundancy_cases.csv
paper_artifacts/tables/vocabulary_growth.csv
```

### Required figures

Generate these:

```text
paper_artifacts/figures/pipeline_overview.png
paper_artifacts/figures/domain_skeleton_daytrader.png
paper_artifacts/figures/score_over_iterations_daytrader.png
paper_artifacts/figures/contamination_before_after_daytrader.png
paper_artifacts/figures/refinement_loop.png
```

Simple generated diagrams are enough for first draft.

### Required snippets

Create Markdown snippets the paper can include:

```text
paper_artifacts/snippets/evaluation_setup.md
paper_artifacts/snippets/implementation_scope.md
paper_artifacts/snippets/results_summary.md
paper_artifacts/snippets/threats_to_validity.md
paper_artifacts/snippets/prototype_limitations.md
```

---

## 23. Text Blocks to Insert into the Paper

### 23.1 Implementation scope

Use this if only Mono2Micro data is used:

> The prototype does not implement a full static dependency extractor. Instead, it consumes existing extracted runtime and decomposition artifacts from the Mono2Micro replication package. This design choice isolates the paper's main contribution: responsibility-record enrichment, domain-skeleton placement, interpretable scoring, redundancy handling, and iterative refinement. Full source-level extraction is orthogonal to the proposed decomposition model and is left as future work.

Use this if source-code metadata is also used:

> The prototype consumes existing runtime and decomposition artifacts from the Mono2Micro replication package and supplements them with lightweight source-code metadata such as class names, packages, annotations, and code snippets. We intentionally avoid reimplementing a full static call-graph extractor, because the contribution of this paper is the decomposition and refinement model rather than extraction infrastructure.

### 23.2 Benchmark selection

> We evaluate the prototype on benchmark systems from the Mono2Micro replication package, focusing on JPetStore, DayTrader, PlantsByWebSphere, and AcmeAir. These systems are suitable because they have been used in prior monolith-to-microservice decomposition studies and include existing runtime/decomposition artifacts. DayTrader is used as the main case study because it is more enterprise-like than the smaller examples and contains richer business and persistence behavior.

### 23.3 Contribution defense

> The novelty of the method is integrative rather than component-wise. We do not claim that static dependency analysis, hierarchical tags, clone detection, or constrained clustering are individually new. The contribution is the operational composition of these ideas into an auditable decomposition framework where domain skeletons, responsibility records, data ownership, redundancy handling, LLM judgment, and human constraints interact through explicit artifacts and scores.

### 23.4 LLM role

> The LLM is used in bounded roles: generating responsibility records, suggesting tag reuse or refinement, and judging borderline proposals under a closed set of reason codes. It is not the primary optimizer and does not silently mutate the decomposition. Every LLM decision is represented in the audit log.

### 23.5 Limitation if action points are incomplete

> Some benchmark artifacts do not expose all trigger families required by the full method definition. For these systems, the prototype evaluates the subset of the method supported by the available artifacts and records missing trigger or data-source information explicitly. This limitation affects the evaluation of chain-crossing and action-point contamination but not the responsibility-record, domain-placement, redundancy, or core refinement mechanisms.

### 23.6 Limitation if data sources are incomplete

> When table-level or data-source-level access information is unavailable, the prototype computes coherence and contamination from service tags and domain paths only. Data-source ownership remains part of the full method, but its quantitative evaluation requires benchmark artifacts that expose data-access relations.

### 23.7 Baseline comparison caution

> The goal is not to replace Mono2Micro's runtime-trace clustering, but to show that domain-skeleton scoring and refinement can enrich, diagnose, and improve decomposition candidates derived from existing runtime data. Accordingly, we compare both the initial baseline-seeded decomposition and the refined decomposition under the proposed quality model.

### 23.8 Future work

> Future work will integrate a full source-level extractor for Java/Spring and Java EE systems, expand trigger coverage to schedulers, batch jobs, message queues, GraphQL, gRPC, CLI entry points, and webhooks, and evaluate the method on larger industrial monoliths with enterprise-provided domain catalogs.

---

## 24. Minimal Main-Track Version

If time is limited, implement this minimum:

1. Load Mono2Micro data for `jpetstore`, `daytrader`, and `plants`.
2. Normalize components and baseline clusters.
3. Generate heuristic responsibility records.
4. Create manual domain skeletons.
5. Place clusters into skeleton.
6. Compute contamination.
7. Compute simple coherence.
8. Compute Stage 1 and Stage 2 redundancy.
9. Run move-only refinement.
10. Generate audit log.
11. Compare before/after scores.
12. Run one ablation: without domain skeleton.
13. Write DayTrader case study.

This is enough for a credible workshop or early conference submission if written honestly.

---

## 25. Stronger Version

For a stronger paper, add:

1. AcmeAir benchmark.
2. LLM-generated responsibility records.
3. Source-code metadata enrichment.
4. Data-source inference.
5. Native cascade initialization.
6. LLM judge for borderline moves.
7. Redundancy whitelist examples.
8. Sensitivity analysis.
9. Multiple ablations.
10. Paper-ready diagrams.

---

## 26. What Not to Do

Do not spend the first month building a perfect extractor.

Do not try to support all trigger families in the first prototype.

Do not claim the prototype fully implements the whole framework if it only uses available benchmark artifacts.

Do not claim superiority over Mono2Micro unless the comparison is fair and the results support it.

Do not hide missing action-point or data-source information. Record it explicitly.

Do not let the LLM silently change clusters. Every LLM action must be logged.

Do not make the method impossible to run without an LLM API key. Heuristic fallback is required.

---

## 27. Suggested First Week Plan

### Day 1

- Clone Mono2Micro replication repo.
- Inspect `datasets_runtime`.
- Write `dataset_inspection.md`.

### Day 2

- Implement schema models.
- Implement loader for `jpetstore`.

### Day 3

- Implement loader for `daytrader`.
- Export normalized JSON.

### Day 4

- Implement heuristic responsibility records.
- Implement controlled inventories.

### Day 5

- Create manual domain skeletons for `jpetstore` and `daytrader`.
- Implement contamination scoring.

### Day 6

- Implement baseline-seeded initial decomposition.
- Score Mono2Micro clusters.

### Day 7

- Implement move-only refinement.
- Produce first before/after result table.

After Day 7, decide whether results are promising before expanding to Plants/AcmeAir.

---

## 28. Suggested Milestones

### Milestone 1 — Data works

The agent can run:

```bash
python scripts/02_normalize_dataset.py --app jpetstore
python scripts/02_normalize_dataset.py --app daytrader
```

and produce normalized JSON.

### Milestone 2 — Scores work

The agent can run:

```bash
python scripts/06_score_decomposition.py --app daytrader --mode baseline_seeded
```

and produce contamination/coherence/redundancy tables.

### Milestone 3 — Refinement works

The agent can run:

```bash
python scripts/07_run_refinement.py --app daytrader --max-iterations 10
```

and produce before/after scores plus audit logs.

### Milestone 4 — Benchmark works

The agent can run:

```bash
python scripts/08_run_benchmarks.py --apps jpetstore daytrader plants
```

and produce `main_results.csv`.

### Milestone 5 — Paper artifacts work

The agent can run:

```bash
python scripts/09_generate_paper_tables.py
```

and produce all tables and figures under `paper_artifacts/`.

---

## 29. Final Deliverables for the Paper

The coding agent must deliver:

1. runnable prototype,
2. README with setup and benchmark commands,
3. normalized benchmark data,
4. generated responsibility records,
5. domain skeletons,
6. final decompositions,
7. score tables,
8. ablation tables,
9. sensitivity tables if implemented,
10. audit logs,
11. paper-ready text snippets,
12. limitations file.

The most important files for paper writing are:

```text
paper_artifacts/tables/main_results.csv
paper_artifacts/tables/ablation_results.csv
paper_artifacts/tables/redundancy_cases.csv
paper_artifacts/figures/score_over_iterations_daytrader.png
paper_artifacts/snippets/results_summary.md
paper_artifacts/snippets/prototype_limitations.md
```

---

## 30. Final Advice for the Coding Agent

The project is successful if it shows:

- the method can consume existing benchmark decomposition data,
- it can impose domain-skeleton structure,
- it can explain bad placements via contamination,
- it can detect responsibility-level redundancy,
- it can improve scores through auditable moves,
- it can generate tables that make the paper credible.

Do not try to implement the entire ideal framework before producing first results.

The correct sequence is:

```text
load data -> normalize -> enrich -> score -> refine -> report
```

not:

```text
build extractor -> build perfect graph -> then start method
```
