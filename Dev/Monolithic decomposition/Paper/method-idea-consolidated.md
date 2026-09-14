# Monolith-to-Microservice Decomposition Method — Idea Collection

> Working document. Consolidates the idea as discussed across sessions. No critique, no novelty assessment, no opinion. Purely a description of the proposed method.

## Table of Contents

- [[#1. Core Premise|1. Core Premise]]
- [[#2. Three-Layer Component Extraction|2. Three-Layer Component Extraction]]
- [[#3. Action Points (Trigger Enumeration)|3. Action Points (Trigger Enumeration)]]
- [[#4. Deterministic Chain Extraction per Action Point|4. Deterministic Chain Extraction per Action Point]]
- [[#5. Graph Extraction Hardening (LLM Revalidation + Human Review + Noise Filter)|5. Graph Extraction Hardening (LLM Revalidation + Human Review + Noise Filter)]]
- [[#6. Cross-Cutting Component Detection|6. Cross-Cutting Component Detection]]
- [[#7. Service-Level Summarization, Responsibility, and Hierarchical Tagging|7. Service-Level Summarization, Responsibility, and Hierarchical Tagging]]
- [[#8. Data-Source-Level Hierarchical Tagging|8. Data-Source-Level Hierarchical Tagging]]
- [[#9. Microservice-Level Domain Hierarchy (Clustering Skeleton)|9. Microservice-Level Domain Hierarchy (Clustering Skeleton)]]
- [[#10. Controlled Tag and Vocabulary Inventories|10. Controlled Tag and Vocabulary Inventories]]
- [[#11. First Iteration — Initial Whole-Clustering Assignment|11. First Iteration — Initial Whole-Clustering Assignment]]
- [[#12. Cascading Initial Assignment Mechanism|12. Cascading Initial Assignment Mechanism]]
- [[#13. Scoring — Contamination, Coherence, and LLM-Judged Rubric|13. Scoring — Contamination, Coherence, and LLM-Judged Rubric]]
- [[#14. Redundancy Score|14. Redundancy Score]]
- [[#15. Top-Down and Bottom-Up Coherence|15. Top-Down and Bottom-Up Coherence]]
- [[#16. Human-Preference / Configurable Signals|16. Human-Preference / Configurable Signals]]
- [[#17. Position on Chains|17. Position on Chains]]
- [[#18. Iterative Refinement — Detect, Identify, Search, Propose, Judge, Apply|18. Iterative Refinement — Detect, Identify, Search, Propose, Judge, Apply]]
- [[#19. Human-in-the-Loop in the Iteration|19. Human-in-the-Loop in the Iteration]]
- [[#20. Open Questions|20. Open Questions]]

-----

## 1. Core Premise

The method decomposes a monolithic application into microservice candidates by:

1. Extracting components in three architectural layers.
1. Enumerating all action points (anything that triggers execution).
1. Extracting deterministic dependency chains from each action point through the mid-tier down to data sources.
1. Hardening the graph through an LLM revalidation pass, human quick-review, and a noise filter.
1. Filtering out cross-cutting components.
1. Summarizing each service and producing a **responsibility record** (structured + descriptive) plus three-level service-level tags using a controlled vocabulary.
1. Tagging data sources hierarchically.
1. Defining (user-supplied or LLM-inferred) a **microservice-level domain hierarchy** — the predefined cluster skeleton into which microservices are placed.
1. Producing a **single initial whole-clustering** (not a population) via a cascading assignment mechanism.
1. Scoring the clustering with three deterministic scores — **contamination (minimize)**, **coherence (maximize)**, **redundancy (minimize toward a justified floor)** — plus an LLM-judged rubric for borderline decisions.
1. Iteratively improving the clustering through four operations — **move**, **split**, **merge**, **lift-to-shared** — driven by per-microservice and per-component score contributions.
1. Allowing the human to intervene between iterations: reviewing, correcting, and injecting rules to accelerate convergence.

There is **no population, no genetic algorithm, no Pareto front**. There is one clustering, refined iteratively.

-----

## 2. Three-Layer Component Extraction

The monolith is parsed into three architectural layers.

**Layer 1 — Action layer.** Components that can trigger execution (see [[#3. Action Points (Trigger Enumeration)|Section 3]]).

**Layer 2 — Business logic tier (a.k.a. application tier / processing layer).** Everything between the action layer and the data source layer:

- Services
- Processes
- Orchestration components
- Any mid-tier processing component
- Cross-cutting components (logging, authentication, authorization, etc.) — flagged separately, see [[#6. Cross-Cutting Component Detection|Section 6]]

**Layer 3 — Data source layer.** External resources accessed by the monolith:

- Databases (relational, NoSQL)
- Connections to mainframe systems
- SOAP service connections
- Other third-party service connections
- Message queues / streaming systems (when used as data sources)
- Any external persistence or data-exchange endpoint

All three layers are captured deterministically via static analysis (tree-sitter, JavaParser, Spoon, Soot, WALA, CodeQL, or equivalent).

-----

## 3. Action Points (Trigger Enumeration)

An **action point** is any component that can trigger execution from outside the system. Enumeration is unified across all trigger protocols:

- REST controllers
- SOAP endpoints
- Schedulers (cron jobs, Spring `@Scheduled`, Quartz)
- Batch jobs (Spring Batch)
- Message queue listeners (JMS, Kafka, RabbitMQ)
- GraphQL endpoints
- gRPC endpoints
- CLI entry points
- Webhooks
- Any other trigger mechanism present in the codebase

Each action point becomes a first-class unit of analysis.

-----

## 4. Deterministic Chain Extraction per Action Point

For each action point, a deterministic script extracts the full downstream dependency chain:

- All called methods and classes
- All touched mid-tier services
- All touched data sources (DB tables, queues, external APIs)
- All relevant configuration

The extraction is done for every action point. The output is a per-action-point closure: a structured artifact describing the chain.

**Important clarification on chains:**
Chains are **not** used as the unit of clustering. They are not turned into services directly. A single chain can legitimately be split across multiple microservices.

Example: an action point `GET /customer/data` calls Service A and Service B. Service A reads from Data Source 1; Service B reads from Data Source 2. If Data Source 1 belongs to Microservice X and Data Source 2 belongs to Microservice Y, then this action point’s chain spans two microservices, and the action point endpoint itself may need to be split (or routed via an aggregator).

Chains are used as a **signal source for scoring** (see [[#13. Scoring — Contamination, Coherence, and LLM-Judged Rubric|Section 13]]), not as a clustering primitive.

-----

## 5. Graph Extraction Hardening (LLM Revalidation + Human Review + Noise Filter)

Four-step hardening pipeline.

### Step 1 — Deterministic extraction, configured maximally

Static analyzer configured for the specific stack:

- All annotation packages registered (Spring, JAX-RS, JAX-WS, Spring Batch, JMS, Kafka, Quartz, custom annotations)
- Custom dispatcher patterns registered (factories, registries, programmatic handler registration)
- Reflection sites flagged for manual review
- Configuration files parsed (Spring XML, `application.yaml`, properties) and edges added from config-declared bindings
- Edge types preserved (call / data-access / config / event / transaction)

### Step 2 — LLM revalidation pass

For each chain, an LLM reviews and reports:

- Missing edges
- Suspicious gaps
- Suspicious branches
- Likely false positives

LLM does **not silently patch** the graph. It produces a report with two action types:

- `fix_extractor` — improve the static-analysis configuration. Applied once, benefits all chains.
- `hardcode_patch` — manual edge addition or removal with justification. Last-resort fix.

### Step 3 — Human quick review

Human reviews only LLM-flagged chains:

- High-confidence-correct chains → auto-approved
- LLM-flagged chains → human review
- Reviewer can accept, reject, or trigger an extractor reconfiguration

### Step 4 — Noise filter on chains

Strip migration-irrelevant components before downstream LLM agents see chains:

- Cross-cutting components (see [[#6. Cross-Cutting Component Detection|Section 6]])
- Test scaffolding
- Dead code
- Framework boilerplate
- Generated code
- Build/deployment configuration

-----

## 6. Cross-Cutting Component Detection

Components every microservice would need anyway. LLM tags each mid-tier class with one of:

- `cross_cutting` — definitely cross-cutting, exclude from clustering signal
- `candidate_cross_cutting` — possibly cross-cutting, needs human confirmation
- `business` — not cross-cutting, full weight in clustering

Human review focuses on `candidate_cross_cutting`.

-----

## 7. Service-Level Summarization, Responsibility, and Hierarchical Tagging

Mid-tier business services are summarized, given a **responsibility record**, and tagged. Produces the **first of three independent tag hierarchies** plus the responsibility record used for redundancy detection.

### Stage 1 — Summarization

For each mid-tier service, the LLM produces a summary:

1. Start generic (what kind of component this is at a high level).
1. Drill down progressively.
1. Describe the class’s responsibilities.
1. Describe the class’s role.

### Stage 2 — Responsibility Record

In addition to the prose summary, each service receives a structured **responsibility record** with both controlled-vocabulary fields and free-form description:

```
{
  action_verb: <from controlled vocabulary>     e.g., "convert", "validate", "fetch", "compute", "transform", "orchestrate"
  object: <from controlled vocabulary>          e.g., "currency", "customer-record", "payment-amount"
  description: <1-2 sentence LLM-written>       e.g., "Converts a monetary amount between currencies using daily FX rates"
  inputs: [<typed input descriptors>]
  outputs: [<typed output descriptors>]
  data_sources_touched: [<data source IDs>]
  tags: { L1, L2, L3 }                          (filled by Stage 3)
}
```

The `action_verb` and `object` controlled vocabularies are maintained as inventories (see [[#10. Controlled Tag and Vocabulary Inventories|Section 10]]) to prevent vocabulary explosion across services.

The responsibility record is used for:

- **Redundancy detection** ([[#14. Redundancy Score|Section 14]]): two services are functionally redundant if they share `(action_verb, object)` or have high description similarity.
- **Tag enrichment**: the structured `(action_verb, object)` informs L3 tag generation.
- **Contamination detection**: a service whose `data_sources_touched` are all in microservice X but is placed in microservice Y is contaminated independent of tags.
- **LLM judge prompts**: more efficient than showing raw code.

### Stage 3 — Service-Level Hierarchical Tagging

Three levels of tags per service:

- **L1 — Very high / generic.** Example: `customer`.
- **L2 — Middle / narrow.** Example: `customer care`.
- **L3 — Deep / very specific.** Example: `customer care data retrieval`.

Tags are drawn from the controlled service-level tag inventory ([[#10. Controlled Tag and Vocabulary Inventories|Section 10]]). The structured responsibility fields inform tag selection.

-----

## 8. Data-Source-Level Hierarchical Tagging

Three-level tagging applied to data sources. **Second of three independent tag hierarchies.**

- **L1** — business-domain area. Examples: `customer`, `payment`, `inventory`.
- **L2** — sub-domain. Examples: `customer master`, `customer transaction`, `customer interaction`.
- **L3** — specific role. Examples: `customer profile store`, `customer event log`.

Independent of the service-level tag hierarchy. May use overlapping vocabulary, but maintained separately because data sources and services are different concerns.

Cross-hierarchy alignment is a scoring signal (see [[#13. Scoring — Contamination, Coherence, and LLM-Judged Rubric|Section 13]]).

-----

## 9. Microservice-Level Domain Hierarchy (Clustering Skeleton)

**Third independent tag hierarchy**, and the one that defines the **clustering skeleton**.

### Structure

A tree of nested cluster nodes:

- **L1** — top-level domains (e.g., `customer`, `payment`, `inventory`).
- **L2** — sub-domains within each L1.
- **L3** — finer sub-domains.
- **L4** — finest level. (Open question: needed or L3 sufficient — see [[#20. Open Questions|Section 20]].)

### Source of the hierarchy

- **User-supplied** from an enterprise domain catalog (preferred when available).
- **LLM-inferred** from the monolith’s services, data sources, action points, and their tags.

### Clusters and microservices

- Each cluster node is a container.
- A cluster can hold **multiple microservices**. No constraint of one microservice per cluster.
- A cluster can stay **empty** — the hierarchy is a skeleton, not a requirement.
- A microservice lives at a specific node (its **domain path**, e.g., `customer/care/inbound`).

### Three independent hierarchies summary

|Hierarchy                                                                                 |What it tags                                        |Depth                |Purpose                |
|------------------------------------------------------------------------------------------|----------------------------------------------------|---------------------|-----------------------|
|Service-level ([[#7. Service-Level Summarization, Responsibility, and Hierarchical Tagging|Section 7]])                                        |Each mid-tier service|L1–L3                  |
|Data-source-level ([[#8. Data-Source-Level Hierarchical Tagging                           |Section 8]])                                        |Each data source     |L1–L3                  |
|Microservice-level (this section)                                                         |Each microservice (its location in the cluster tree)|L1–L4 (open)         |The clustering skeleton|

May share vocabulary but are independent.

### Cross-hierarchy alignment

A microservice placed at `customer/care` should contain services tagged `customer / customer-care / *` and use data sources tagged `customer / customer-master / *`. Alignment = high coherence; mismatch = contamination.

-----

## 10. Controlled Tag and Vocabulary Inventories

To prevent vocabulary explosion, all tagging and structured-field generation is controlled by incrementally maintained inventories.

Workflow:

1. First item is tagged / labeled freely. Values enter the inventory.
1. For each subsequent item, the LLM first looks at existing inventory entries.
1. If an existing entry fits → reuse it. Otherwise → create new and add to inventory.

Applies to:

- Service-level L1, L2, L3 tags
- Data-source-level L1, L2, L3 tags
- Microservice-level L1, L2, L3, L4 domain hierarchy (when LLM-inferred)
- Responsibility `action_verb` (from [[#7. Service-Level Summarization, Responsibility, and Hierarchical Tagging|Section 7]])
- Responsibility `object` (from [[#7. Service-Level Summarization, Responsibility, and Hierarchical Tagging|Section 7]])

**Open question:** whether the three tag hierarchies plus the two responsibility vocabularies are unified into one inventory or maintained as separate aligned inventories (see [[#20. Open Questions|Section 20]]).

-----

## 11. First Iteration — Initial Whole-Clustering Assignment

The first iteration produces **one complete clustering of the entire monolith**, not a population.

### What is produced

- Every mid-tier business component assigned to a microservice.
- Every microservice placed at a node in the microservice-level domain hierarchy.
- Some predefined cluster nodes may stay empty.
- Cross-cutting components are not assigned to microservices.

### How it is produced

Cascading mechanism using signals from earlier sections (action-point packages, service-level tags, data-source tags) — see [[#12. Cascading Initial Assignment Mechanism|Section 12]].

Output: a single concrete clustering — every component placed, every microservice at a domain path.

-----

## 12. Cascading Initial Assignment Mechanism

Three-step cascade.

### Step 1 — Coarse cut by action-point package depth

Group action points by their package (the action point’s own package, not the package of every component in the chain).

Package depth resolved as **tag-coherence-driven depth** — go deeper only if it improves L1+L2 tag coherence within the resulting groups.

### Step 2 — If a group is too big, split by service-level L1+L2 tags

Split each group from Step 1 by the L1+L2 service-level tags of its mid-tier components.

### Step 3 — If still too big, split by data-source-level L1+L2 tags

Split groups still too large by the L1+L2 data-source-level tags of the data sources they touch.

### Definition of “too big”

**Tag-diversity threshold**: a group is too big if it contains more than N distinct L1 tags or M distinct L2 tags, regardless of raw size.

### Tunable input

The **target microservice count range** is provided by the human (e.g., 5–10 microservices). The cascade splits while (tag-diversity high OR group count below human target).

### Placement into the microservice-level domain hierarchy

Each group (= microservice) is **placed** at the node in the microservice-level domain hierarchy whose path minimizes contamination of the group’s contents (see [[#13. Scoring — Contamination, Coherence, and LLM-Judged Rubric|Section 13]] for contamination definition).

-----

## 13. Scoring — Contamination, Coherence, and LLM-Judged Rubric

The clustering is scored by three deterministic scores plus an LLM-judged rubric.

### 13.1 Contamination (minimize)

**Definition.** Contamination measures misplacement: components that don’t belong where they sit. Floor at 0 (no contamination = nothing misplaced).

**Per-component contamination** uses **tag tree-edit-distance** between the component’s tag path `T` and the microservice’s domain path `P`.

Given the tree structure of the domain hierarchy:

```
d(T, P) =
  0                          if T == P (full match)
  Σ over depths i where T_i ≠ P_i:  w^(max_depth - i)
```

with `w > 1` (suggested default `w = 3`):

- L1 mismatch (different top-level domain) → cost `w^(max_depth - 1)`
- L2 mismatch → cost `w^(max_depth - 2)`
- L3 mismatch → cost `w^(max_depth - 3)`

L1 mismatch is much more expensive than L3 mismatch — matches the intuition that crossing top-level domain boundaries is the real damage.

**Three contamination sources:**

- **Service contamination**: services tagged outside the microservice’s domain path.
- **Data-source contamination**: data sources tagged outside the microservice’s domain path. Usually weighted heaviest (data ownership is the core of microservice definition).
- **Action-point contamination**: action points whose own tags don’t match the microservice’s domain path.

**Per-microservice contamination:**

```
contamination(m) = Σ d(T_c, P_m) · weight(c.type) for all c ∈ m, c ∉ cross_cutting
```

**Total contamination:**

```
total_contamination = Σ contamination(m) for all m
```

Cross-cutting components are excluded from contamination (they’re expected everywhere).

### 13.2 Coherence (maximize)

**Definition.** Coherence rewards positive structure within and across microservices. Unbounded above. Distinguishes microservices with contamination = 0 by how much positive structure they exhibit.

**Coherence signals:**

- Same service-level L1 tag across all services within a microservice
- Same service-level L2 tag across services within a microservice
- Same service-level L3 tag (stronger — rare specific tags weighted higher, IDF-style)
- Data source exclusivity — data source used by only one microservice
- Action-point tag alignment with its target microservice
- Cross-hierarchy alignment — L1/L2 match between action points + services + data sources of a microservice
- Same transactional boundary (no cross-service distributed transactions)
- Same write-access pattern (services writing to the same tables stay together)

### 13.3 Coupling penalties (feed into coherence subtraction)

- Cross-microservice data source sharing
- Cross-microservice chain count — an action point’s chain crossing N microservices = (N–1) penalty
- Read-write conflicts across services
- Distributed transaction count
- Synchronous call density across boundaries

### 13.4 LLM-judged rubric (secondary, used for ties and borderline decisions)

- “Does this microservice have a coherent business domain?” (Yes / Partial / No)
- “Could you name this microservice in 2–3 words?” (Yes / Struggles / No)
- “Is this microservice’s data ownership clear?” (Yes / Mixed / No)
- “Does this microservice respect DDD aggregate boundaries?” (Yes / Partial / No)
- “Are the action points exposed by this microservice consistent with its domain?” (Yes / Mostly / No)

The LLM rubric is **not** the primary scoring driver. It is used:

- When deterministic scores tie between alternatives.
- To validate borderline moves before they’re applied.
- As a final pass on the converged clustering.

### 13.5 Use in iterative refinement

- **Contamination** drives **move/split** decisions (what to fix).
- **Coherence** drives **merge** decisions and **tie-breaking** between alternatives.
- **Redundancy** (see [[#14. Redundancy Score|Section 14]]) drives **lift-to-shared** decisions.
- **LLM rubric** validates borderline moves and provides a stop condition.

Per-component contamination contributions are computed for every component in every microservice. These are used to compute distances (current vs. hypothetical contamination at other cluster nodes) — the math for move/split/merge in [[#18. Iterative Refinement — Detect, Identify, Search, Propose, Judge, Apply|Section 18]].

-----

## 14. Redundancy Score

The same mid-tier component (or near-identical functionality) appearing in multiple microservices.

### 14.1 Why redundancy is not always bad

Three legitimate reasons for duplication:

- **Cross-cutting that escaped the Section 6 filter** (validation, currency conversion, formatting, schema mapping). Detected here as a second-chance filter.
- **Bounded-context duplication** — DDD-style. Two microservices both have a “Customer” concept with different attributes/responsibilities.
- **Operational duplication** — high-availability, latency, or independent-deployment concerns force the same logic in multiple services.

Redundancy is a **signal**, not always an error. The score *measures* it; resolution depends on context.

### 14.2 Detection pipeline (cheap to expensive)

**Stage 1 — Literal duplication.** Same class/method ID in multiple microservices. Trivially detected by scanning the clustering for `{component_id → list_of_microservices}` with length > 1.

**Stage 2 — Structured-responsibility duplication.** Two services share their `(action_verb, object)` responsibility-record fields across microservices. Deterministic, cheap, uses the controlled vocabulary from [[#7. Service-Level Summarization, Responsibility, and Hierarchical Tagging|Section 7]].

**Stage 3 — Semantic-responsibility duplication.** Description-embedding cosine similarity > threshold across microservices. Expensive — run sparingly (e.g., end-of-iteration-block, not every iteration).

Stages 2 and 3 trigger only on non-cross-cutting services.

### 14.3 Scoring

Per component:

```
redundancy(c) = count of microservices containing c (or its functional equivalent)
```

Per clustering:

```
total_redundancy = Σ (redundancy(c) - 1) for all c where redundancy(c) > 1
```

Minimize toward a **justified floor** (not zero — some duplications are legitimate).

### 14.4 Resolution paths

For each redundant component (or set of functionally-equivalent components):

1. **Eliminate** — consolidate into the microservice with lowest contamination. Default when only one location is low-contamination.
1. **Promote to shared/cross-cutting** ([[#6. Cross-Cutting Component Detection|Section 6]] bucket). Default when redundancy ≥ K (high copy count) and contamination is low everywhere.
1. **Accept** — intentional duplication. Requires LLM (or human) justification with a whitelisted reason:
- “Bounded-context duplication — same concept, different responsibilities” (DDD)
- “Operational independence — must be deployable per microservice” (architectural)
- “Anti-corruption layer — duplicated wrapper, intentional” (DDD)
- “Latency-critical — must live with the caller” (performance)

If no whitelisted reason fits → default to (1) or (2) based on which yields lower contamination.

### 14.5 Interaction with other scores

- **Contamination**: each redundant location’s contamination is computed normally. If contamination is low in all locations → likely legitimate cross-cutting (resolution path 2). If high in some, low in one → that’s the “right home” (resolution path 1).
- **Coherence**: redundancy slightly hurts per-microservice coherence (extra component the microservice doesn’t fundamentally need). Small effect.
- **Iteration**: redundancy above threshold triggers the **lift-to-shared** operation (see [[#18. Iterative Refinement — Detect, Identify, Search, Propose, Judge, Apply|Section 18]]).

-----

## 15. Top-Down and Bottom-Up Coherence

Coherence is evaluated in two directions.

**Top-down: action point → mid-tier.**
If two action points are placed in the same microservice and share mid-tier components → coherence boost.

**Bottom-up: data source → mid-tier.**
If two services use the same data source → signal they should be in the same microservice (or that the data source should be split). Two microservices sharing a data source → coupling penalty.

Both directions feed the scoring in [[#13. Scoring — Contamination, Coherence, and LLM-Judged Rubric|Section 13]].

-----

## 16. Human-Preference / Configurable Signals

The decomposition is driven by automated signals plus configurable human preferences:

- **Anchor data sources** — human marks specific data sources (mainframe, host, legacy DB) as anchors. Score boost when a microservice is built around an anchor.
- **Ignored data sources** — human marks data sources that should not drive decomposition. Example: external REST endpoints should not spawn new microservices — keep as direct calls. Goal is decomposing the legacy system, not multiplying external boundaries.
- **Forced-together** — components or data sources that must be in the same microservice.
- **Forced-apart** — components that must be in different microservices.
- **Decomposition target style** — optimization profile that reweights the scoring:
  - “Extract around mainframe”
  - “Extract around databases”
  - “Extract around domains”
  - “Extract around teams”
- **Service count target** — target range (e.g., 5–10 microservices). Used by the cascading initial assignment and as a granularity signal in scoring.
- **Microservice-level domain hierarchy** — when supplied by the user, defines the clustering skeleton (see [[#9. Microservice-Level Domain Hierarchy (Clustering Skeleton)|Section 9]]).

Human preferences are hard constraints — they override deterministic math and LLM judgment in the conflict resolution priority order (see [[#18. Iterative Refinement — Detect, Identify, Search, Propose, Judge, Apply|Section 18]]).

-----

## 17. Position on Chains

Chains are **not** clustering units. They are signal sources for scoring and graph navigation.

Reasons:

- A single chain can legitimately span multiple microservices (example in [[#4. Deterministic Chain Extraction per Action Point|Section 4]]).
- An action point may need to be **broken into sub-flows** when its chain crosses microservice boundaries.

Chain information is used to:

- Establish which mid-tier components are shared across which action points (top-down coherence signal).
- Establish which data sources are touched by which chains (bottom-up coherence signal).
- Feed the question-based scoring.
- Drive Step 1 of the cascading initial assignment (action-point package proximity within the chain).

-----

## 18. Iterative Refinement — Detect, Identify, Search, Propose, Judge, Apply

The initial clustering is refined iteratively. **One clustering**, not a population. Each iteration applies a small number of changes via a six-step cycle.

### 18.1 Four operations available

- **Move** — relocate a portion of a service to a different microservice. Destination can be:
  - The same leaf cluster (rebalancing inside one L3/L4 node)
  - A different sub-cluster of the same L1 (e.g., `customer/care` → `customer/billing`)
  - A different L1 cluster entirely
- **Split** — break a domain-incoherent service into smaller services. Resulting services may stay in the same cluster or be placed at different nodes.
- **Merge** — combine two related small services in the same or adjacent cluster nodes.
- **Lift-to-shared** — promote a redundant component to the cross-cutting / shared bucket (resolution path 2 in [[#14. Redundancy Score|Section 14]]).

### 18.2 Six-step iteration cycle

**Step 1 — Detect.**
Rank microservices by contamination (descending). Pick top-K most contaminated. Also scan for redundancy candidates (Stage 1 + Stage 2 of Section 14). Small K (1–3 per iteration) — fix few problems per iteration, not the whole clustering.

Optionally rank by contamination *concentration* (contamination per component) to favor microservices with a few badly-misplaced components over uniformly-mediocre ones.

**Step 2 — Identify.**
Within each detected microservice, rank components by individual contamination contribution `d(T_c, P_m)`. Top contributors are candidates to move out, split off, or lift-to-shared.

**Step 3 — Search.**
For each candidate component, find candidate destination microservices via **trie-lookup** on the microservice-level domain hierarchy:

- Build a trie of microservices indexed by domain path.
- For component with tag `T`, traverse the trie following `T`’s path.
- Top-K closest microservices (by LCA depth) become candidate destinations.
- Lookup is O(depth) per component, not O(N).

**Step 4 — Propose.**
Deterministic suggestion based on the search:

- **Move** — to lowest-distance destination (lowest hypothetical contamination there).
- **Split** — if the contaminating components form an internally coherent subgroup (cluster the contaminating components by their tags; if they form a coherent group, that’s a split candidate).
- **Merge** — if two microservices in adjacent nodes share most of their action points / data sources / mid-tier components and individually score below a fragmentation penalty.
- **Lift-to-shared** — if redundancy is high and per-location contamination is uniformly low.

**Step 5 — Judge.**
LLM confirms or overrides the deterministic proposal. Override only with a **whitelisted reason**:

- “Component is only used by chains rooted in this microservice’s action points” (usage-locality)
- “Moving creates a distributed transaction” (transaction-integrity)
- “Component is tagged correctly but its actual responsibility is narrower than the tag suggests” (tag-mistagging)
- “Component is a façade/adapter to the destination domain, not part of it” (adapter pattern)
- For redundancy resolution: the four reasons in [[#14. Redundancy Score|Section 14]] resolution path 3.

If no whitelisted reason fits → default to deterministic proposal.

**LLM-proposed tag refinement.** If the LLM sees that the current tag granularity hides a real distinction (Pattern B from the contamination-LLM design), it can propose a finer tag (e.g., split `customer/care/inbound` into `customer/care/inbound/b2b` and `customer/care/inbound/b2c`). The tag vocabulary is updated, components are re-tagged, and the math now sees the divergence. The LLM doesn’t override the math — it updates the math’s inputs.

**Audit logging.** Every override produces an audit record: component, microservice, deterministic suggestion, LLM decision, whitelisted reason. Used for reviewer-defensibility, calibration (frequent override reasons should be promoted to deterministic signals), and revert.

**Step 6 — Apply.**

- If change is accepted, update only the affected microservices’ scores (lazy recomputation — cached per-microservice contamination, recompute only the two affected ones).
- Move on to the next candidate.

### 18.3 Conflict resolution priority order

1. **Hard human constraints** (forced-together / forced-apart / anchors / ignored) — never overridden by math or LLM.
1. **Deterministic math** — suggests the move.
1. **LLM judge** — confirms or overrides with whitelisted reason.
1. **Human in-the-loop** (see [[#19. Human-in-the-Loop in the Iteration|Section 19]]) — can revert any change post-hoc.

### 18.4 Per-iteration budget

To keep the loop tractable:

- At most K microservices detected per iteration (small, e.g., 1–3).
- At most M moves total per iteration.
- At most one split or one merge per iteration.
- Forces incremental progress; prevents whole-clustering thrashing.

### 18.5 Flat vs. hierarchical sub-iteration (open question)

- **Flat**: one global refinement loop. Any move can go anywhere in the tree.
- **Hierarchical with sub-iterations**: inner loop refines placements within each L1 cluster’s subtree first (moves/splits/merges inside the subtree); then outer loop allows moves across L1 clusters. May converge faster.

See [[#20. Open Questions|Section 20]].

### 18.6 Termination

Multiple stop conditions, any one triggers:

- **Contamination floor**: `total_contamination ≤ threshold`.
- **Coherence plateau**: no coherence improvement for K iterations (when contamination has bottomed but coherence is still being optimized).
- **No accepted moves**: a full iteration produced no accepted moves.
- **Max iterations**.
- **Human says we’re done** (see [[#19. Human-in-the-Loop in the Iteration|Section 19]]).

-----

## 19. Human-in-the-Loop in the Iteration

The human is in the iteration itself, not just before it. Three intervention modes.

### 19.1 Mode 1 — Per-iteration review (passive, optional)

After each iteration, the system shows the human:

- Top N moves applied this iteration.
- Top N moves rejected by the LLM judge, with reasons.
- Microservices with highest remaining contamination.
- New redundancy detections.

Human can:

- Accept the iteration as-is (no input).
- Revert specific moves (creates a forced-apart or forced-together constraint).
- Skip to “run K more iterations without review” (batch mode).

Default: silent batch mode. Human invoked only when iteration produces low-confidence changes or when contamination/coherence diverge unexpectedly.

### 19.2 Mode 2 — Inter-iteration rule injection (active, optional)

Between iterations, the human can add rules:

- New forced-together / forced-apart constraints.
- New anchor or ignored data sources.
- New microservice-level domain hierarchy nodes (e.g., “add L3 cluster `customer/care/vip`”).
- Tag overrides (e.g., “this service is mistagged, correct to `payment/refund`”).
- Domain knowledge as a rule (e.g., “all services touching `customers_pii` table must live in `customer/data-privacy`”).

Each new rule applies from the next iteration onward. The system replays affected components under the new rule, re-scores, and continues.

### 19.3 Mode 3 — Mid-iteration intervention (rare, escalation)

If the system detects high uncertainty — LLM judge confidence low across many decisions, contamination oscillating between iterations, redundancy resolutions all hitting “accept” with no clear reason — it pauses and asks the human a specific question. Not continuous interruption — only when the system itself is stuck.

### 19.4 Review-burden management

- Show only deltas, not full clustering.
- Group changes by microservice.
- Auto-approve high-confidence; surface borderline.
- Time-box review (“review for 5 minutes; untouched = auto-approved”).
- Convergence helper: change volume drops over iterations; review burden decreases toward zero naturally.

### 19.5 Side effects

- **Convergence accelerates** when the human knows what they want. A few well-placed rules can save many iterations.
- **Termination criterion** now includes “human says we’re done” (in addition to the deterministic conditions in [[#18. Iterative Refinement — Detect, Identify, Search, Propose, Judge, Apply|Section 18]]).

-----

## 20. Open Questions

Undecided, to be designed in the next step:

- **Microservice-level hierarchy depth.** Whether L4 is needed or L3 sufficient ([[#9. Microservice-Level Domain Hierarchy (Clustering Skeleton)|Section 9]]). Provisionally L4.
- **Flat vs. hierarchical refinement loop.** Whether sub-iteration within each L1 cluster’s subtree is needed before allowing cross-L1 moves ([[#18. Iterative Refinement — Detect, Identify, Search, Propose, Judge, Apply|Section 18]]).
- **Termination criterion thresholds.** Specific values for contamination floor, coherence plateau window K, max iterations.
- **Per-iteration budget values.** Specific K (microservices detected), M (moves), one-split-one-merge — confirm or tune.
- **Tag tree-edit-distance weighting `w`.** Default `w = 3` (L1 mismatch much worse than L3). May need per-project tuning.
- **Candidate-destination top-K size.** How many trie-lookup candidates to consider per component. Default 3–5.
- **Tag-diversity thresholds.** Specific N (distinct L1 tags) and M (distinct L2 tags) for the “too big” criterion.
- **Functional-duplication similarity threshold.** Cosine threshold for Stage 3 redundancy detection ([[#14. Redundancy Score|Section 14]]).
- **Redundancy threshold for lift-to-shared.** Minimum copy count K to trigger promotion to cross-cutting.
- **Unified vs. separate inventories.** Whether service-level + data-source-level + microservice-level tag vocabularies + `action_verb` + `object` share one inventory or are aligned-but-separate ([[#10. Controlled Tag and Vocabulary Inventories|Section 10]]).
- **Default review mode.** Silent batch vs. interactive ([[#19. Human-in-the-Loop in the Iteration|Section 19]]).
- **How action points are split when their chain crosses microservice boundaries.** Mechanism for breaking an endpoint into sub-flows or routing through an aggregator.
- **Naming of the mid-tier layer.** Working name: “business logic tier” / “application tier” / “processing layer”.
- **LLM-inferred vs. user-supplied microservice-level hierarchy merging.** When both are partially available, how to merge consistently.
- **Whitelisted override reasons completeness.** Are the listed reasons in [[#18. Iterative Refinement — Detect, Identify, Search, Propose, Judge, Apply|Section 18]] step 5 exhaustive? When should new reasons be added vs. forced into existing categories?