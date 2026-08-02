# Monolith-to-Microservice Decomposition Method — Idea Collection

> Working document. Consolidates the idea as discussed across sessions. No critique, no novelty assessment, no opinion. Purely a description of the proposed method.

## Table of Contents

- [[#1. Core Premise|1. Core Premise]]
- [[#2. Three-Layer Component Extraction|2. Three-Layer Component Extraction]]
- [[#3. Action Points (Trigger Enumeration)|3. Action Points (Trigger Enumeration)]]
- [[#4. Deterministic Chain Extraction per Action Point|4. Deterministic Chain Extraction per Action Point]]
- [[#5. Graph Extraction Hardening (LLM Revalidation + Human Review + Noise Filter)|5. Graph Extraction Hardening (LLM Revalidation + Human Review + Noise Filter)]]
- [[#6. Cross-Cutting Component Detection|6. Cross-Cutting Component Detection]]
- [[#7. Summarization and Hierarchical Tagging|7. Summarization and Hierarchical Tagging]]
- [[#8. Data Source Tagging|8. Data Source Tagging]]
- [[#9. Controlled Tag Vocabulary (Tag Inventory)|9. Controlled Tag Vocabulary (Tag Inventory)]]
- [[#10. LLM-Generated Initial Population of Clusterings|10. LLM-Generated Initial Population of Clusterings]]
- [[#11. First Population — Seeding Strategies|11. First Population — Seeding Strategies]]
- [[#12. Cascading Anchor Candidate (Candidate 1)|12. Cascading Anchor Candidate (Candidate 1)]]
- [[#13. Scoring Mechanism — Question-Based Coherence Scoring|13. Scoring Mechanism — Question-Based Coherence Scoring]]
- [[#14. Top-Down and Bottom-Up Coherence|14. Top-Down and Bottom-Up Coherence]]
- [[#15. Human-Preference / Configurable Signals|15. Human-Preference / Configurable Signals]]
- [[#16. Position on Chains|16. Position on Chains]]
- [[#17. Iterative Refinement Loop|17. Iterative Refinement Loop]]
- [[#18. Open Questions|18. Open Questions]]

-----

## 1. Core Premise

The method decomposes a monolithic application into microservice candidates by:

1. Extracting components in three architectural layers.
1. Enumerating all action points (anything that triggers execution).
1. Extracting deterministic dependency chains from each action point through the mid-tier down to data sources.
1. Hardening the graph through an LLM revalidation pass, human quick-review, and a noise filter.
1. Filtering out cross-cutting components that should not influence clustering decisions.
1. Summarizing and hierarchically tagging the remaining components using an LLM with a controlled tag vocabulary.
1. Tagging data sources hierarchically with the same vocabulary system.
1. Generating an initial population of candidate clusterings using multiple non-random seeding strategies.
1. Scoring clusterings using a question-based scoring system combined with top-down (action point → mid-tier) and bottom-up (data source → mid-tier) coherence signals, plus human-preference signals.
1. Iteratively refining the clusterings.

-----

## 2. Three-Layer Component Extraction

The monolith is parsed into three layers of components.

**Layer 1 — Action layer.** Components that can trigger execution (see [[#3. Action Points (Trigger Enumeration)|Section 3]]).

**Layer 2 — Business logic tier (a.k.a. application tier / processing layer).** Everything between the action layer and the data source layer. This includes:

- Services
- Processes
- Orchestration components (some monoliths have an explicit orchestration layer for services)
- Any mid-tier processing component
- Cross-cutting components (logging, authentication, authorization, etc.) — these are flagged separately, see [[#6. Cross-Cutting Component Detection|Section 6]]

**Layer 3 — Data source layer.** External resources accessed by the monolith:

- Databases (relational, NoSQL, etc.)
- Connections to mainframe systems
- SOAP service connections
- Other third-party service connections
- Message queues / streaming systems (when used as data sources)
- Any external persistence or data-exchange endpoint

All three layers are captured deterministically via static analysis (e.g., Python scripts using tree-sitter, JavaParser, Spoon, Soot, WALA, CodeQL, or equivalent).

-----

## 3. Action Points (Trigger Enumeration)

An **action point** is any component that can trigger execution from outside the system. The enumeration is unified across all trigger protocols:

- REST controllers
- SOAP endpoints
- Schedulers (cron jobs, Spring `@Scheduled`, Quartz)
- Batch jobs (Spring Batch, etc.)
- Message queue listeners (JMS, Kafka, RabbitMQ, etc.)
- GraphQL endpoints
- gRPC endpoints
- CLI entry points
- Webhooks
- Any other trigger mechanism present in the codebase

Each action point becomes a first-class unit of analysis in the pipeline.

-----

## 4. Deterministic Chain Extraction per Action Point

For each action point, a deterministic script extracts the full downstream dependency chain:

- All called methods and classes
- All touched mid-tier services
- All touched data sources (DB tables, queues, external APIs)
- All relevant configuration

The extraction is done for **every** action point in the monolith. The output is a per-action-point closure: a structured artifact describing the chain.

**Important clarification on chains:**
Chains are **not** used as the unit of clustering. They are not turned into services directly. A single chain can legitimately be split across multiple microservices.

Example: an action point `GET /customer/data` calls Service A and Service B. Service A reads from Data Source 1; Service B reads from Data Source 2. If Data Source 1 belongs to Microservice X and Data Source 2 belongs to Microservice Y, then this action point’s chain spans two microservices, and the action point endpoint itself may need to be split (or routed via an aggregator).

Chains are used as a **signal source for scoring** (see [[#13. Scoring Mechanism — Question-Based Coherence Scoring|Section 13]]), not as a clustering primitive.

-----

## 5. Graph Extraction Hardening (LLM Revalidation + Human Review + Noise Filter)

To minimize the risk of bad graph extraction (missed annotations, bad configuration, reflection, dynamic dispatch, programmatic registration), the extraction is hardened in four steps.

### Step 1 — Deterministic extraction, configured maximally

Static analyzer (tree-sitter / JavaParser / Spoon / WALA / Soot / CodeQL) configured for the specific stack:

- All annotation packages registered (Spring, JAX-RS, JAX-WS, Spring Batch, JMS, Kafka, Quartz, custom annotations)
- Custom dispatcher patterns registered (factories, registries, programmatic handler registration)
- Reflection sites flagged for manual review
- Configuration files parsed (Spring XML, `application.yaml`, properties) and edges added from config-declared bindings
- Edge types preserved (call / data-access / config / event / transaction)

### Step 2 — LLM revalidation pass

For each extracted chain, an LLM reviews and reports:

- Missing edges (e.g., “this controller likely calls AuditService but no edge present”)
- Suspicious gaps (chain ends abruptly mid-flow, no data source reached)
- Suspicious branches (chain crosses unexpected layers)
- Likely false positives (edge exists but probably dead code or test-only)

The LLM does **not silently patch** the graph. It produces a report with two action types:

- `fix_extractor` — suggests improvements to the static-analysis configuration (e.g., “add annotation X to the registry”). Applied once, benefits all chains.
- `hardcode_patch` — proposes a manual edge addition or removal with justification. Applied only after review. Last-resort fix.

### Step 3 — Human quick review

Human reviews only the LLM-flagged chains, not all chains. Triage by LLM confidence:

- High-confidence-correct chains → auto-approved
- LLM-flagged chains → human review (focused, fast)
- Reviewer can accept, reject, or trigger an extractor reconfiguration

### Step 4 — Noise filter on chains

Before LLM agents see chains, strip migration-irrelevant components:

- Cross-cutting components (logging, auth) — already flagged in [[#6. Cross-Cutting Component Detection|Section 6]]
- Test scaffolding
- Dead code (if detectable)
- Framework boilerplate
- Generated code
- Build/deployment configuration not relevant to runtime

Result: leaner chains, lower LLM token cost, less noise for downstream agents.

-----

## 6. Cross-Cutting Component Detection

Some mid-tier components do not carry weight in the clustering decision because every extracted microservice would need them anyway. Examples:

- Logging services
- Authentication
- Authorization
- Other cross-cutting utilities

These are detected by the LLM with human-in-the-loop confirmation. The LLM:

1. Reviews the list of mid-tier classes.
1. Summarizes each class.
1. Tags each class.
1. Adds an additional field indicating cross-cutting status, with **graded values**:
- `cross_cutting` — definitely cross-cutting, exclude from clustering signal
- `candidate_cross_cutting` — possibly cross-cutting, needs human confirmation
- `business` — not cross-cutting, full weight in clustering

Human review focuses on the `candidate_cross_cutting` bucket.

-----

## 7. Summarization and Hierarchical Tagging

Mid-tier components (and other relevant components) are summarized and tagged in two LLM stages.

### Stage 1 — Summarization

For each mid-tier class, the LLM produces a summary following a guideline:

1. Start generic (what kind of component this is at a high level).
1. Drill down progressively.
1. Describe the class’s responsibilities.
1. Describe the class’s role.

### Stage 2 — Hierarchical Tagging

A second LLM (or agent) assigns three levels of tags to each summarized class:

- **Level 1 — Very high / generic.** Example: `customer`.
- **Level 2 — Middle / narrow.** Example: `customer care`.
- **Level 3 — Deep / very specific.** Example: `customer care data retrieval`.

(The examples above are illustrative only — actual tags are produced by the LLM.)

-----

## 8. Data Source Tagging

The same 3-level hierarchical tagging is applied to data sources, not just to mid-tier components. The tag inventory is shared (or at least aligned) across layers so cross-layer matching is meaningful.

- **L1** — business-domain area of the data source. Examples: `customer`, `payment`, `inventory`.
- **L2** — sub-domain. Examples: `customer master`, `customer transaction`, `customer interaction`.
- **L3** — specific role. Examples: `customer profile store`, `customer event log`.

Cross-layer alignment is then a scoring signal: a microservice whose business-tier services tag as `customer / customer care / customer care data retrieval` and whose data sources tag as `customer / customer master / customer profile store` gets a strong cohesion boost. Mismatched tag levels → penalty or no boost.

-----

## 9. Controlled Tag Vocabulary (Tag Inventory)

To prevent tag explosion, tagging is controlled by an incrementally maintained inventory.

Workflow:

1. The first class is tagged freely. Tags enter the inventory.
1. For each subsequent class, the LLM **first looks at the existing tags** in the inventory.
1. The LLM decides whether existing tags fit the new class:
- If an existing tag fits → reuse it.
- If no existing tag fits → create a new tag and add it to the inventory.
1. New tags are only created when necessary.

This applies at all three tag levels (generic, narrow, specific) and across both mid-tier components and data sources.

The result is a compact, controlled vocabulary that grows only as needed, with maximum tag reuse across components.

-----

## 10. LLM-Generated Initial Population of Clusterings

After all components are summarized, tagged, and cross-cutting components are flagged, the LLM is used to **generate an initial population of candidate clusterings** — multiple alternative decompositions, not a single one.

Inputs to the clustering LLM:

- Action-point chains (after graph hardening)
- Three-level tags per component
- Three-level tags per data source
- Cross-cutting flags (cross-cutting components excluded or down-weighted)
- Shared dependencies across chains (shared mid-tier services, shared data sources)
- Human-preference inputs (see [[#15. Human-Preference / Configurable Signals|Section 15]])

Output: a population of N candidate clusterings, each from a different seeding perspective.

-----

## 11. First Population — Seeding Strategies

The initial population is **not random**. Each candidate starts from a different principled angle, so the population spans the legitimate decomposition perspectives and the iterative loop has meaningful variation to select between.

**Practical population composition (10–15 candidates):**

- 1 cascading anchor candidate — see [[#12. Cascading Anchor Candidate (Candidate 1)|Section 12]]
- 2 tag-driven (L1 alone, L1+L2)
- 2 data-source-driven (one-per-data-source, anchor-data-source)
- 2 graph-algorithm (e.g., Louvain, spectral)
- 4–5 LLM-perspective seeds (each from a different framing prompt)
- 1–2 hybrid (existing-package only, git-history if available)

### Seeding-strategy catalog

**Tag-driven seeds**

- L1-tag seeding — group all components by their L1 tag. One microservice per L1 tag.
- L2-tag seeding — same but at L2. Finer-grained.
- L1+L2 combined — microservice = unique (L1, L2) pair.
- Tag-frequency seeding — rare L3 tags become standalone microservices; common L1 tags become merged services.

**Data-source-driven seeds (bottom-up)**

- One-microservice-per-data-source — every data source becomes a microservice; mid-tier components assigned to the microservice owning the data source they touch most.
- Data-source-cluster seeding — pre-cluster data sources by L1/L2 tag, then group services around each data-source cluster.
- Anchor-data-source seeding — use human-marked anchor data sources (mainframe, legacy DB) as cluster centers; assign services that touch them.

**Action-point-driven seeds (top-down)**

- One-microservice-per-action-point — fine-grained extreme.
- Action-point-tag seeding — group action points by their L1 or L2 tag.
- Action-point-cluster seeding — group action points by chain overlap.

**Graph-algorithm seeds**

- Louvain community detection on the component dependency graph.
- Leiden algorithm.
- Label propagation on the dependency graph.
- Spectral clustering on the call-graph adjacency matrix.
- Hierarchical agglomerative clustering on component embeddings (CodeBERT / LLM2Vec), cut dendrogram at different heights for multiple candidates.

**LLM-perspective seeds (each candidate from a different framing prompt)**

- “Optimize for low coupling” — minimize cross-service calls.
- “Optimize for data ownership” — group around data sources.
- “Optimize for business domain alignment” — group around L1/L2 tags.
- “Optimize for team ownership” — group by inferred functional teams.
- “Optimize for legacy isolation” — isolate mainframe/legacy access into separate services.
- “Optimize for transactional boundary” — keep transactions inside a service.

**Hybrid / human-grounded seeds**

- Architect-sketch seed — human-provided partial grouping as a candidate, diversified around it.
- Existing-package seed — monolith’s existing Java packages as a candidate.
- Git-history seed — components frequently co-changed in commits go together.

-----

## 12. Cascading Anchor Candidate (Candidate 1)

This is the strong default starting point: a multi-step cascading split using the chain’s action-point package depth, then business-tier tags, then data-source tags.

### The cascade

**Step 1 — Coarse cut by action-point package.**
Group action points by package. The package referenced is the **action point’s package** in the chain — not the package of every component in the chain. Endpoints close in the package tree are likely close in domain.

Open question: what depth in the package tree? Resolved as a **tag-coherence-driven depth** — go deeper only if it improves L1+L2 tag coherence within the resulting groups. If splitting one level deeper doesn’t make tags more uniform, stop at the current level. Depth is determined by what helps the decomposition, not by an arbitrary fixed number.

**Step 2 — If a group is too big, split by business-tier L1+L2 tags.**
Take each group from Step 1 and look at the L1+L2 tags of its mid-tier business components. Split further so each resulting group is internally tag-uniform.

**Step 3 — If still too big, split by data-source L1+L2 tags.**
Same idea, applied to data sources. Groups still too large after Step 2 are split by the L1+L2 tags of the data sources they touch.

### Definition of “too big”

Resolved as a **tag-diversity threshold**: a group is too big if it contains more than N distinct L1 tags or M distinct L2 tags, regardless of raw size. This ties “too big” to “domain-incoherent” rather than to an arbitrary LOC or component count — which is what the decomposition actually cares about. A group of 100 components all tagged `customer / customer-care / *` is fine; one with 30 components spanning `customer`, `payment`, `inventory` is not.

### Tunable input

The **target microservice count range** is a tunable input provided by the human (e.g., 5–10 microservices for this monolith). The cascade splits while (tag-diversity high OR group count below human target). This combines a principled signal (tag diversity) with a practical constraint (target count).

-----

## 13. Scoring Mechanism — Question-Based Coherence Scoring

The LLM does the clustering **and** also computes a coherence score for each candidate clustering using a question list. Each question’s answer maps to score points.

Example question:

> Does the service have a coherent business domain? If yes → +X points; if no → 0 points.

The score is composed of several signal categories.

### Cohesion signals (positive points)

- Same L1 tag across all services within a candidate microservice
- Same L2 tag across services within a candidate microservice
- Same L3 tag across services (stronger — rare specific tags weighted higher, IDF-style)
- Same L1/L2 tag between services and their data sources (cross-layer alignment)
- Data source exclusivity — data source used by only one microservice
- Action-point tag alignment with its target microservice
- Same transactional boundary (no cross-service distributed transactions)
- Same write-access pattern (services writing to the same tables stay together)

### Coupling penalties (negative points)

- Cross-microservice data source sharing
- Cross-microservice chain count — an action point’s chain crossing N microservices = (N–1) penalty
- Read-write conflicts across services
- Distributed transaction count
- Synchronous call density across boundaries

### Granularity signals

- Service count balance (penalty for extreme distributions)
- Component count per microservice (too large or too small penalized)
- Action-point density per microservice (services with zero action points flagged)

### LLM-judged questions (rubric)

- “Does this microservice have a coherent business domain?” (Yes / Partial / No)
- “Could you name this microservice in 2–3 words?” (Yes / Struggles / No)
- “Is this microservice’s data ownership clear?” (Yes / Mixed / No)
- “Does this microservice respect DDD aggregate boundaries?” (Yes / Partial / No)
- “Are the action points exposed by this service consistent with its domain?” (Yes / Mostly / No)

### Composite

- Final score = weighted sum of all signals. Weights configurable per decomposition profile.
- Alternative: keep multi-objective (cohesion / coupling / granularity / human-alignment) and use Pareto selection in the iterative loop.

-----

## 14. Top-Down and Bottom-Up Coherence

Coherence is evaluated in two directions, both feeding the scoring system.

**Top-down: action point → mid-tier.**
If two action points are clustered into the same microservice and they share mid-tier components, this increases the coherence score for that microservice.

**Bottom-up: data source → mid-tier.**
If two services use the same data source, this is a signal that they should be in the same microservice (or that the data source should be split). Conversely, if two microservices end up sharing a data source, this is a coupling penalty.

The score combines both directions.

-----

## 15. Human-Preference / Configurable Signals

The decomposition is driven not only by automated signals but also by configurable human preferences. Examples:

- **Anchor data sources** — human marks specific data sources (mainframe, host, legacy DB) as anchors. Score boosts when a microservice is built around an anchor.
- **Ignored data sources** — human marks data sources that should not drive decomposition. Example: a REST endpoint to an external system should be kept as a direct call, not turned into its own new microservice, because the goal is to decompose a legacy system, not to multiply external boundaries.
- **Forced-together** — human marks components or data sources that must be in the same microservice.
- **Forced-apart** — human marks components that must be in different microservices.
- **Decomposition target style** — human chooses the optimization profile. Each profile reweights the question scores:
  - “Extract around mainframe”
  - “Extract around databases”
  - “Extract around domains”
  - “Extract around teams”
- **Service count target** — human gives target range (e.g., 5–10 microservices). Used by the cascading anchor candidate ([[#12. Cascading Anchor Candidate (Candidate 1)|Section 12]]) and as a granularity signal in scoring.

-----

## 16. Position on Chains

Chains are **not** clustering units. They are signal sources for scoring and for graph navigation.

Reasons:

- A single chain can legitimately span multiple microservices (see example in [[#4. Deterministic Chain Extraction per Action Point|Section 4]]).
- An action point endpoint may need to be **broken into multiple sub-flows** when its chain crosses microservice boundaries.

Chain information is used to:

- Establish which mid-tier components are shared across which action points (top-down coherence signal).
- Establish which data sources are touched by which chains (bottom-up coherence signal).
- Feed the question-based scoring.
- Drive the cascading anchor candidate (Step 1 uses action-point package proximity within the chain).

-----

## 17. Iterative Refinement Loop

After the initial population is generated and scored, the method iterates to improve the clusterings.

- Some number of candidates is selected from the population (selection mechanism not yet decided).
- The LLM refines these candidates.
- Re-score using the question list and top-down/bottom-up coherence.
- Iterate until convergence (criterion not yet decided).

-----

## 18. Open Questions

These are still undecided and to be designed in the next step:

- **Selection mechanism for the iterative loop.** How candidates are picked from the population for refinement — systematic (e.g., Pareto / tournament / elitism on the score), LLM-judge-based, or hybrid. Not yet decided.
- **Enhancement mechanism inside the loop.** How a selected candidate is improved at each iteration — re-prompting with feedback, mutation operators, crossover, LLM-as-critic. Not yet decided.
- **Termination criterion.** Convergence threshold, max iterations, score plateau detection — not yet decided.
- **Exact question list for scoring.** Specific questions, their point weights, and how scores combine across categories — not yet finalized.
- **How action points are split when their chain crosses microservice boundaries.** Mechanism for breaking an endpoint into sub-flows or routing through an aggregator — not yet defined.
- **Naming of the mid-tier layer.** Working name: “business logic tier” / “application tier” / “processing layer”.
- **Concrete tag-diversity threshold values.** Specific N (distinct L1 tags) and M (distinct L2 tags) numbers for the “too big” criterion in the cascading anchor candidate.
- **How the controlled tag inventory is shared between mid-tier and data-source tagging.** One unified inventory or two aligned inventories.