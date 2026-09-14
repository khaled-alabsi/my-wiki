# Domain-Skeleton-Constrained Monolith-to-Microservice Decomposition

> Paper scaffold generated from the current method draft.  
> Status: pre-implementation / pre-evaluation.  
> Purpose: turn the idea collection into a publishable paper structure with clear contribution framing, TODO placeholders, and reviewer-facing defense.

## Table of Contents

- [[#Abstract|Abstract]]
- [[#1 Introduction|1 Introduction]]
- [[#2 Problem Statement and Motivation|2 Problem Statement and Motivation]]
- [[#3 Background and Related Work|3 Background and Related Work]]
- [[#4 Method Overview|4 Method Overview]]
- [[#5 Program Model and Component Extraction|5 Program Model and Component Extraction]]
- [[#6 Action Points and Dependency-Chain Extraction|6 Action Points and Dependency-Chain Extraction]]
- [[#7 Graph Hardening and Extraction Validation|7 Graph Hardening and Extraction Validation]]
- [[#8 Responsibility Records and Controlled Vocabularies|8 Responsibility Records and Controlled Vocabularies]]
- [[#9 Domain Hierarchy as Clustering Skeleton|9 Domain Hierarchy as Clustering Skeleton]]
- [[#10 Initial Decomposition|10 Initial Decomposition]]
- [[#11 Quality Model|11 Quality Model]]
- [[#12 Iterative Refinement Algorithm|12 Iterative Refinement Algorithm]]
- [[#13 Human-in-the-Loop and LLM-Judge Design|13 Human-in-the-Loop and LLM-Judge Design]]
- [[#14 Implementation Plan|14 Implementation Plan]]
- [[#15 Evaluation Plan|15 Evaluation Plan]]
- [[#16 Threats to Validity|16 Threats to Validity]]
- [[#17 Discussion|17 Discussion]]
- [[#18 Conclusion|18 Conclusion]]
- [[#Appendix A Core Data Structures|Appendix A Core Data Structures]]
- [[#Appendix B TODO Checklist|Appendix B TODO Checklist]]

---

## Abstract

Monolith-to-microservice decomposition remains difficult in enterprise systems because existing techniques often optimize over code dependencies, traces, APIs, or embeddings without making enterprise domain structure, data ownership, and intentional duplication explicit. This paper proposes a domain-skeleton-constrained decomposition method for deriving microservice candidates from monolithic applications. The method extracts action points, dependency chains, business components, and data sources; enriches business components with structured responsibility records and hierarchical tags; places candidate services into a predefined or inferred enterprise domain hierarchy; and iteratively refines the decomposition using deterministic contamination, coherence, and redundancy scores. Unlike population-based or opaque embedding-based approaches, the method maintains a single auditable decomposition and refines it through move, split, merge, and lift-to-shared operations. The LLM is used as a bounded judge and extractor auditor rather than as the primary optimizer. Human input is represented as explicit constraints, tag corrections, domain rules, and review decisions.

TODO: Replace this abstract after implementation and evaluation. Add the concrete implementation stack, benchmark systems, number of monoliths evaluated, and quantitative results.

---

## 1 Introduction

### 1.1 Motivation

Migrating a monolithic application to microservices is not merely a clustering problem over classes, methods, or traces. In realistic enterprise systems, decomposition decisions depend on business capability boundaries, data ownership, transaction boundaries, runtime entry points, team constraints, shared infrastructure, and intentionally duplicated concepts across bounded contexts.

Existing decomposition approaches provide useful signals: static dependencies, execution traces, API interfaces, data-flow relations, graph embeddings, search-based modularization, and human-guided clustering. However, these signals are often insufficient on their own. A decomposition that is structurally clean at the code level may still violate data ownership. A trace-based decomposition may ignore scheduled jobs, batch flows, CLI operations, or message listeners. A clone-based recommendation may incorrectly remove duplication that is intentional under domain-driven design. A fully automated clustering may produce a result that is hard for architects to inspect, modify, or defend.

This paper addresses that gap by proposing a method that treats decomposition as an auditable, domain-constrained refinement process. Rather than producing a population of candidate decompositions, the method maintains one decomposition and iteratively improves it using explicit scores and controlled human/LLM intervention.

### 1.2 Research Gap

Prior approaches commonly answer the question:

> Which code artifacts are similar or coupled enough to be grouped together?

This paper focuses on a stricter enterprise decomposition question:

> Where should each responsibility, action point, and data source belong within a domain hierarchy, and which deviations are justified?

This shift matters because enterprise decomposition is not only about minimizing technical coupling. It is also about aligning code with a domain model, establishing data ownership, avoiding inappropriate distributed transactions, and preserving legitimate duplication where bounded contexts require it.

TODO: Add 1–2 motivating examples from a real or benchmark monolith showing why class-level or trace-only clustering is insufficient.

TODO: Add one running example used throughout the paper, ideally involving:
- a REST endpoint,
- a scheduled or batch job,
- shared data source access,
- one intentionally duplicated responsibility,
- one cross-cutting component.

### 1.3 Contributions

This paper makes the following contributions.

**Contribution 1 — Domain-skeleton-constrained decomposition.**  
We introduce a decomposition method that uses an enterprise domain hierarchy as a clustering skeleton. Candidate microservices are placed at nodes in this hierarchy, where nodes may remain empty, may contain multiple microservices, and may represent either leaf or interior domain capabilities. This differs from flat clustering and from seeded clustering that assumes every taxonomy node must be populated. The domain skeleton gives the decomposition a stable enterprise-facing structure and makes placement decisions explainable as domain-path assignments.

**Contribution 2 — Structured responsibility records as the semantic unit of decomposition.**  
We introduce a structured responsibility record for each business component, consisting of an `action_verb`, `object`, free-text responsibility description, typed inputs and outputs, touched data sources, and hierarchical tags. The record acts as an operational bridge between static extraction, domain tagging, redundancy detection, LLM judging, and human review. Instead of asking the algorithm or LLM to reason only over raw classes or free-form summaries, the method reasons over fixed-schema semantic records.

**Contribution 3 — Interpretable quality model for decomposition refinement.**  
We define three complementary decomposition scores: contamination, coherence, and redundancy. Contamination penalizes mismatch between component/data/action tags and the microservice domain path. Coherence rewards aligned responsibilities, local data ownership, transactional integrity, and write-access locality. Redundancy detects literal, structured, and semantic duplication across microservices while allowing an explicit justified floor for intentional duplication.

**Contribution 4 — Formal treatment of justified duplication.**  
We distinguish harmful redundancy from intentional duplication. Redundant responsibilities may be eliminated, lifted to a shared/cross-cutting component, or accepted when justified by a closed whitelist of reasons such as bounded-context duplication, operational independence, anti-corruption layers, or latency-critical locality. This avoids the simplistic assumption that all duplication in a microservice decomposition is a defect.

**Contribution 5 — Auditable deterministic-propose / LLM-judge / human-review refinement loop.**  
We propose an iterative refinement cycle in which deterministic scoring proposes move, split, merge, and lift-to-shared operations; an LLM judge validates or rejects borderline proposals under whitelisted reasons; and humans can inject constraints, domain rules, tag corrections, or review decisions. The LLM is not the primary optimizer. It is used as a bounded auditor and judge over structured inputs, producing an audit trail for every override.

### 1.4 Why This Is a Publishable Contribution

The novelty of this work is integrative rather than component-wise. The method does not claim that hierarchical tags, tree-distance penalties, clone detection, static dependency extraction, or human-in-the-loop clustering are individually new. Instead, the contribution is the operational contract between these pieces: a reproducible decomposition framework in which enterprise domain structure, responsibility semantics, data ownership, redundancy, LLM judgment, and human constraints are represented explicitly and used together.

This distinction is important. Many software engineering papers contribute not by inventing a primitive technique from nothing, but by adapting, combining, operationalizing, and evaluating existing techniques for a problem that prior work handles incompletely. The proposed method should therefore be defended as a framework contribution: it makes decomposition decisions inspectable, constraint-aware, and aligned with enterprise domain structure.

The paper should avoid claiming twelve separate novelties. The strongest defensible position is that the paper contributes one coherent method with three main technical pillars:

1. domain-skeleton-constrained placement,
2. responsibility-record-based semantic reasoning,
3. interpretable refinement using contamination, coherence, redundancy, and justified duplication.

TODO: In the final paper, shorten this defense and move some of it to the discussion section. Keep the introduction focused and confident.

---

## 2 Problem Statement and Motivation

### 2.1 Problem Definition

Given a monolithic application consisting of action points, business components, data sources, configuration artifacts, and dependency relations, the goal is to produce a set of microservice candidates such that:

- each business component is assigned to one candidate microservice or marked as cross-cutting/shared,
- each candidate microservice is placed at a node in a domain hierarchy,
- data ownership is as local as possible,
- action points are assigned or decomposed consistently with the candidate microservices they expose,
- harmful redundancy is minimized,
- intentional duplication is explicitly justified,
- human constraints are respected,
- every automated move is auditable.

Formally, let:

- $A$ be the set of action points,
- $B$ be the set of business components,
- $D$ be the set of data sources,
- $H$ be the microservice domain hierarchy,
- $M$ be the set of candidate microservices,
- $p(m) \in H$ be the domain-path placement of microservice $m$,
- $assign(b) \in M \cup \{\text{shared}, \text{cross-cutting}\}$ assign each business component to a location.

The task is to find an assignment and placement that minimizes contamination and harmful redundancy while maximizing coherence, subject to hard human constraints.

TODO: Add exact mathematical formulation after the scoring functions are finalized.

### 2.2 Scope

The method targets enterprise monoliths where domain structure and data ownership matter. It is especially suited for systems with multiple trigger families, nontrivial data-source usage, scheduled/batch processing, message listeners, and cross-cutting infrastructure.

The method does not attempt to automatically perform the full physical migration. It identifies microservice candidates and refactoring recommendations. Actual extraction, API redesign, database migration, deployment restructuring, and operational rollout remain outside the primary scope.

TODO: State supported languages and frameworks after implementation. For first version, likely Java/Spring/Spring Batch/JPA/JMS/Kafka/Quartz.

### 2.3 Running Example

TODO: Insert running example.

Suggested example structure:

- `CustomerController.getCustomerData`
- `CustomerBatchJob.reconcileCustomerStatus`
- `CustomerProfileService`
- `CustomerRiskService`
- `CurrencyConversionService`
- `customers` table
- `risk_scores` table
- `fx_rates` table
- `customer-events` Kafka topic

Use this example to show:
1. action-point enumeration,
2. chain extraction,
3. responsibility records,
4. tag assignment,
5. contamination scoring,
6. justified duplication or lift-to-shared.

---

## 3 Background and Related Work

This section should not be a generic literature dump. It should be organized around the precise claims of the paper.

### 3.1 Microservice Decomposition from Static, Dynamic, and Interface Signals

Discuss work such as:

- static dependency graph approaches,
- execution-trace approaches,
- API/interface-based approaches,
- data-centric approaches,
- GNN/embedding-based approaches,
- process-mining approaches.

Positioning:

> These approaches provide useful decomposition signals, but they usually do not make enterprise domain skeletons, responsibility records, intentional duplication, and auditable human/LLM intervention first-class elements of the decomposition process.

TODO: Add citations and concise contrast:
- Mazlami et al.
- Baresi et al.
- Jin et al. / FoSCI
- Kalia et al. / Mono2Micro
- CARGO
- CHGNN
- CO-GCN
- MAGNET
- MonoEmbed
- MicroDec

### 3.2 Search-Based Software Modularization

Discuss Bunch, hill climbing, multi-objective modularization, and modularization quality.

Positioning:

> Search-based modularization performs local or population-based search over module assignments. Our method also refines assignments iteratively, but its neighborhood is constrained by a domain hierarchy and its objective is interpretable through contamination, coherence, and redundancy rather than only structural coupling.

TODO: Cite Bunch, Mahdavi et al., Praditwong et al.

### 3.3 Constrained, Seeded, and Hierarchical Clustering

Discuss constrained clustering, seeded clustering, and hierarchical clustering with prior knowledge.

Positioning:

> Prior clustering work shows that background knowledge can guide clustering. Our method specializes this idea for enterprise decomposition by treating the domain hierarchy as a placement skeleton that can have empty nodes, multi-occupancy nodes, and valid interior-node placements.

TODO: Cite Wagstaff, Basu, Chatziafratis, HierSeed, and related taxonomy/seeding papers.

### 3.4 Semantic Service Descriptions and Responsibility Modeling

Discuss OWL-S, WSMO, use-case modeling, code summarization, and DSLs.

Positioning:

> Semantic service descriptions model service capabilities, inputs, outputs, preconditions, and effects. Our responsibility record borrows this spirit but uses the record as an operational unit inside decomposition scoring, redundancy detection, LLM judging, and tag refinement.

TODO: Cite OWL-S, WSMO, Jacobson use cases, code summarization, and DSL literature.

### 3.5 Clone Detection, Cross-Cutting Concerns, and Intentional Duplication

Discuss clone detection and cross-cutting concern identification.

Positioning:

> Clone detection identifies duplicated code or behavior, but decomposition needs to distinguish harmful duplication from intentional bounded-context duplication. Our redundancy model therefore includes a closed whitelist for accepted duplication.

TODO: Cite Roy & Cordy, SourcererCC, embedding-based clone detection, fan-in analysis, aspect-oriented programming, DDD, Vernon, Newman.

### 3.6 Human-in-the-Loop and LLM-Assisted Software Engineering

Discuss interactive clustering, interactive re-modularization, active learning, LLM-as-judge, and LLM-for-SE.

Positioning:

> The method uses the LLM in a bounded role: extractor auditor, structured proposal judge, and vocabulary refinement assistant. It does not let the LLM silently rewrite the graph or act as the sole decomposition engine.

TODO: Cite Bavota, Amershi, Bae, Settles, LLM-as-judge SE papers, and LLM-for-SE surveys.

---

## 4 Method Overview

### 4.1 Pipeline Summary

The method consists of the following stages:

1. Extract action points, business components, data sources, and configuration artifacts.
2. Extract deterministic dependency chains from each action point.
3. Harden the extracted graph through deterministic configuration, LLM revalidation, human review, and noise filtering.
4. Detect and separate cross-cutting components.
5. Generate responsibility records and hierarchical tags for business components.
6. Generate hierarchical tags for data sources.
7. Obtain or infer the microservice-level domain hierarchy.
8. Produce one initial decomposition using cascading assignment.
9. Score the decomposition using contamination, coherence, and redundancy.
10. Iteratively refine the decomposition using move, split, merge, and lift-to-shared operations.
11. Apply human constraints and LLM judgment only through explicit, auditable mechanisms.

TODO: Add architecture diagram.

Suggested figure:
- left: monolith artifacts,
- middle: extraction + enrichment,
- right: domain skeleton + scoring + iteration loop.

### 4.2 Design Principles

The method follows five principles:

1. **One auditable decomposition, not a population.**  
   The system maintains one current decomposition and improves it iteratively.

2. **Domain placement is explicit.**  
   Every microservice candidate is located at a node in a domain hierarchy.

3. **Data ownership is first-class.**  
   Data-source tags and write-access patterns influence contamination and coherence.

4. **Duplication is judged, not automatically removed.**  
   Redundancy can be harmful, shared, or intentionally accepted.

5. **LLM actions are bounded and logged.**  
   The LLM may flag extraction gaps, judge borderline proposals, or propose vocabulary refinements, but deterministic scoring remains the primary driver.

---

## 5 Program Model and Component Extraction

### 5.1 Three Architectural Layers

The monolith is represented through three layers:

- action layer,
- business logic tier,
- data-source layer.

Action-layer components trigger execution. Business-tier components implement application logic, orchestration, transformation, validation, and domain behavior. Data-source components represent databases, queues, external APIs, mainframe connections, and persistence/data-exchange endpoints.

TODO: Define exactly which code artifacts count as business components in implementation:
- class-level?
- method-level?
- package-level?
- Spring bean-level?
- transaction boundary-level?

### 5.2 Static Extraction

The extraction engine should parse:

- source code,
- annotations,
- framework configuration,
- XML/YAML/properties files,
- dependency injection bindings,
- scheduler configuration,
- batch metadata,
- messaging listener declarations,
- persistence mappings,
- external client declarations.

TODO: Select implementation tools:
- JavaParser/Spoon for AST,
- Soot/WALA for call graph,
- CodeQL for dependency search,
- tree-sitter for multi-language parsing,
- custom Spring/JPA/JMS/Kafka/Quartz extractors.

### 5.3 Edge Types

The extracted graph preserves edge types:

- call,
- data access,
- config binding,
- event/message,
- transaction,
- external service call,
- scheduler trigger,
- batch step transition.

TODO: Define graph schema and serialize as JSON/GraphML/Neo4j.

---

## 6 Action Points and Dependency-Chain Extraction

### 6.1 Action Point Definition

An action point is any component that can trigger execution from outside the analyzed business logic.

Supported trigger families include:

- REST controllers,
- SOAP endpoints,
- schedulers,
- batch jobs,
- message listeners,
- GraphQL endpoints,
- gRPC endpoints,
- CLI entry points,
- webhooks,
- custom trigger mechanisms.

TODO: Implement trigger detectors by framework.

### 6.2 Per-Action-Point Chain Extraction

For each action point, the method extracts the downstream closure:

- called methods/classes,
- invoked business components,
- touched data sources,
- external APIs,
- queues/topics,
- configuration bindings,
- transaction boundaries.

Important: chains are not clustering units. They are evidence. A single chain may legitimately span multiple microservices.

### 6.3 Chain Outputs

Each chain should produce a structured artifact:

```json
{
  "action_point_id": "...",
  "trigger_type": "REST | SOAP | SCHEDULER | BATCH | MQ | GRAPHQL | GRPC | CLI | WEBHOOK | OTHER",
  "entry_signature": "...",
  "business_components": ["..."],
  "data_sources": ["..."],
  "external_calls": ["..."],
  "queues_topics": ["..."],
  "config_edges": ["..."],
  "transaction_boundaries": ["..."],
  "confidence": "...",
  "flags": []
}
```

TODO: Define confidence rules for deterministic extraction.

---

## 7 Graph Hardening and Extraction Validation

### 7.1 Deterministic Configuration

The extractor is configured maximally for the stack:

- framework annotations,
- custom annotations,
- dispatcher patterns,
- reflection sites,
- dependency injection,
- XML/YAML/properties bindings,
- generated code markers.

TODO: Write per-framework extraction configuration.

### 7.2 LLM as Extractor Auditor

The LLM receives structured chain artifacts and relevant code/config snippets. It may report:

- missing edges,
- suspicious gaps,
- suspicious branches,
- likely false positives.

It must not silently patch the graph. Every recommendation is classified as:

- `fix_extractor`: improve the extractor so the same issue is fixed systematically,
- `hardcode_patch`: apply a one-off graph patch with justification.

TODO: Define LLM prompt and output schema.

### 7.3 Human Review

Human review is limited to LLM-flagged chains and low-confidence extraction regions.

TODO: Define review UI or review artifact format.

### 7.4 Noise Filtering

The method removes or downweights:

- test scaffolding,
- generated code,
- dead code,
- framework boilerplate,
- build/deployment code,
- cross-cutting components.

TODO: Define exclusion rules.

---

## 8 Responsibility Records and Controlled Vocabularies

### 8.1 Responsibility Record

Each business component receives a responsibility record:

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
  "confidence": "...",
  "evidence": []
}
```

The `action_verb` and `object` fields are controlled-vocabulary entries. The description remains free text. The record is used for redundancy detection, tag enrichment, contamination analysis, and LLM judging.

### 8.2 Service-Level Tags

Each business component receives hierarchical service-level tags:

- L1: broad business area,
- L2: narrower capability,
- L3: specific responsibility.

TODO: Define examples and constraints for L1/L2/L3.

### 8.3 Data-Source-Level Tags

Each data source receives hierarchical tags:

- L1: business data area,
- L2: sub-domain,
- L3: specific data role.

TODO: Decide whether tags are assigned by LLM, human, schema names, table access patterns, documentation, or a combination.

### 8.4 Controlled Inventories

The method maintains controlled inventories for:

- service tags,
- data-source tags,
- domain hierarchy labels,
- action verbs,
- responsibility objects.

The LLM must prefer existing inventory entries and create new entries only when no existing term fits.

TODO: Define vocabulary merge/split rules.

TODO: Measure vocabulary growth and correction rate during evaluation.

---

## 9 Domain Hierarchy as Clustering Skeleton

### 9.1 Definition

The microservice-level domain hierarchy is a tree of candidate placement nodes:

- L1: top-level domains,
- L2: sub-domains,
- L3: capabilities,
- L4: optional finer capabilities.

Every microservice candidate is placed at one node in this hierarchy.

### 9.2 Properties

The hierarchy is a skeleton, not a mandatory set of services:

- nodes may remain empty,
- nodes may contain multiple microservices,
- interior nodes may contain microservices,
- leaf nodes do not have to be populated,
- the hierarchy may be user-supplied or inferred.

### 9.3 Source of the Skeleton

Preferred sources:

- enterprise capability map,
- domain catalog,
- team/service ownership model,
- architecture documentation,
- LLM-inferred hierarchy from extracted components and tags.

TODO: Define fallback algorithm for LLM-inferred skeleton.

TODO: Define merge algorithm when partial user hierarchy and inferred hierarchy both exist.

---

## 10 Initial Decomposition

### 10.1 Single Whole-Clustering

The initial step produces one complete decomposition:

- every business component is assigned,
- every candidate microservice is placed in the domain hierarchy,
- cross-cutting components are excluded or lifted,
- empty hierarchy nodes remain empty.

### 10.2 Cascading Assignment

Initial grouping follows a cascade:

1. group by action-point package depth,
2. split large groups by service-level L1/L2 tags,
3. split remaining large groups by data-source-level L1/L2 tags,
4. place each group at the domain node that minimizes contamination.

### 10.3 Tag-Diversity Threshold

A group is too broad if it contains more than:

- $N$ distinct L1 tags, or
- $M$ distinct L2 tags.

This avoids using raw class count as the primary size criterion.

TODO: Choose default values for $N$ and $M$.

TODO: Evaluate sensitivity to $N$ and $M$.

### 10.4 Service Count Target

A human may supply a target range, such as 5–10 microservice candidates. The cascade uses this as a granularity signal, not as a hard requirement unless configured as one.

TODO: Define exact interaction between target count and tag-diversity threshold.

---

## 11 Quality Model

The method scores each decomposition using contamination, coherence, and redundancy.

### 11.1 Contamination

Contamination measures domain misplacement. For a component with tag path $T$ placed in a microservice at domain path $P$, the cost is:

$$
d(T, P) =
\sum_{i : T_i \ne P_i} w^{maxDepth - i}
$$

where $w > 1$.

L1 mismatches are penalized more heavily than deeper mismatches.

Contamination sources:

- service contamination,
- data-source contamination,
- action-point contamination.

Per-microservice contamination:

$$
contamination(m) =
\sum_{c \in m, c \notin crossCutting}
d(T_c, P_m) \cdot weight(type(c))
$$

Total contamination:

$$
totalContamination =
\sum_{m \in M} contamination(m)
$$

TODO: Define normalization so scores are comparable across systems of different size.

TODO: Decide weights for service, data source, and action-point contamination.

### 11.2 Coherence

Coherence rewards positive internal structure:

- shared service-level tags,
- rare L3 tag agreement using IDF-style weighting,
- data-source exclusivity,
- action-point alignment,
- cross-hierarchy alignment,
- transactional integrity,
- write-access locality.

TODO: Define exact coherence formula.

TODO: Demonstrate that coherence is not redundant with contamination.

### 11.3 Coupling Penalties

Coherence may be reduced by:

- cross-microservice data-source sharing,
- action-point chains crossing multiple microservices,
- distributed transactions,
- read/write conflicts,
- synchronous boundary call density.

TODO: Define penalty formula and whether it is part of coherence or a separate fourth score.

### 11.4 Redundancy

Redundancy is detected in three stages:

1. literal duplication by class/method ID,
2. structured-responsibility duplication by `(action_verb, object)`,
3. semantic-responsibility duplication by embedding similarity.

Redundancy is minimized toward a justified floor, not necessarily zero.

Resolution paths:

- eliminate,
- lift to shared/cross-cutting,
- accept as justified duplication.

Accepted duplication requires a whitelisted reason:

- bounded-context duplication,
- operational independence,
- anti-corruption layer,
- latency-critical locality.

TODO: Define embedding model and similarity threshold.

TODO: Define audit schema for accepted duplication.

### 11.5 Overall Objective

The overall objective is not a single opaque scalar by default. The method reports a score tuple:

$$
Q = (contamination \downarrow, coherence \uparrow, harmfulRedundancy \downarrow)
$$

For deterministic move proposals, a configurable scalarization may be used:

$$
score = \alpha \cdot contamination - \beta \cdot coherence + \gamma \cdot harmfulRedundancy
$$

subject to hard constraints.

TODO: Decide whether the algorithm uses tuple ordering, scalarization, or hybrid rules.

---

## 12 Iterative Refinement Algorithm

### 12.1 Operations

The method supports four operations:

- move,
- split,
- merge,
- lift-to-shared.

### 12.2 Six-Step Cycle

Each iteration follows:

1. Detect high-contamination microservices and redundancy candidates.
2. Identify high-contribution components.
3. Search candidate destinations using LCA/trie lookup in the domain hierarchy.
4. Propose deterministic operations.
5. Judge borderline proposals with the LLM.
6. Apply accepted changes and update affected scores.

### 12.3 Candidate Search

Candidate destinations are found by matching a component tag path against the trie of existing microservice domain paths.

TODO: Formalize LCA distance and candidate top-K.

### 12.4 Proposal Rules

Default proposal rules:

- move component to the destination with lowest hypothetical contamination,
- split if contaminating components form an internally coherent subgroup,
- merge adjacent weak microservices with shared action points/data sources/components,
- lift-to-shared if redundancy is high and contamination is uniformly low.

TODO: Define exact split and merge criteria.

### 12.5 Conflict Resolution

Priority order:

1. hard human constraints,
2. deterministic scoring,
3. LLM judge,
4. human post-hoc review.

### 12.6 Termination

Possible stop conditions:

- contamination below threshold,
- no accepted moves,
- coherence plateau,
- max iterations,
- human termination.

TODO: Define default thresholds and max iteration count.

### 12.7 Algorithm Pseudocode

TODO: Replace with final pseudocode.

```text
Input:
  Extracted graph G
  Responsibility records R
  Service tags ST
  Data-source tags DT
  Domain hierarchy H
  Human constraints C

Output:
  Microservice decomposition M

1. M <- initial_decomposition(G, R, ST, DT, H, C)
2. repeat
3.   scores <- compute_scores(M)
4.   candidates <- detect_problem_regions(M, scores)
5.   proposals <- []
6.   for each candidate in candidates:
7.       destinations <- search_domain_neighbors(candidate, H, M)
8.       proposal <- deterministic_propose(candidate, destinations, scores, C)
9.       if borderline(proposal):
10.          proposal <- llm_judge(proposal, R, scores, whitelist)
11.      proposals.add(proposal)
12.  accepted <- apply_budget_and_constraints(proposals, C)
13.  M <- apply_changes(M, accepted)
14. until stop_condition(M)
15. return M
```

---

## 13 Human-in-the-Loop and LLM-Judge Design

### 13.1 Human Interaction Modes

The method supports three human interaction modes:

1. passive per-iteration review,
2. active inter-iteration rule injection,
3. rare mid-iteration escalation.

### 13.2 Human Rules

Humans may provide:

- forced-together constraints,
- forced-apart constraints,
- anchor data sources,
- ignored data sources,
- new domain hierarchy nodes,
- tag overrides,
- policy-as-constraint rules,
- service count target,
- decomposition style.

TODO: Define rule language.

### 13.3 LLM Judge

The LLM judge receives structured records, scores, candidate moves, and evidence. It may:

- confirm the deterministic proposal,
- reject it using a whitelisted reason,
- request tag refinement,
- mark uncertainty for human review.

The LLM may not silently alter the graph, assign arbitrary new reasons, or override hard human constraints.

TODO: Define judge prompt and JSON schema.

### 13.4 Audit Log

Every LLM or human override produces an audit record:

```json
{
  "iteration": 0,
  "proposal_id": "...",
  "operation": "move | split | merge | lift_to_shared",
  "component_ids": [],
  "source_microservice": "...",
  "target_microservice": "...",
  "deterministic_decision": "...",
  "judge_decision": "...",
  "human_decision": "...",
  "reason": "...",
  "score_delta": {},
  "evidence": []
}
```

TODO: Use the audit log as an evaluation artifact.

---

## 14 Implementation Plan

### 14.1 Prototype Architecture

TODO: Implement a prototype with modules:

- extractor,
- chain builder,
- graph hardener,
- cross-cutting detector,
- responsibility-record generator,
- tag inventory manager,
- domain-skeleton manager,
- initial decomposer,
- scorer,
- refiner,
- LLM judge,
- human review/audit exporter.

### 14.2 Target Stack

Initial target:

- Java monoliths,
- Spring/Spring Boot,
- JPA/Hibernate,
- REST controllers,
- scheduled jobs,
- Spring Batch,
- JMS/Kafka/RabbitMQ,
- external REST/SOAP clients.

TODO: Narrow scope for first paper. Do not claim all languages/frameworks unless implemented.

### 14.3 Reproducibility Package

TODO: Prepare:

- source code,
- benchmark configuration,
- extracted graph artifacts,
- responsibility records,
- tag inventories,
- decompositions per iteration,
- audit logs,
- prompts,
- evaluation scripts.

---

## 15 Evaluation Plan

The paper will only be credible if the framework is evaluated. Since no implementation exists yet, this section is the highest-priority TODO.

### 15.1 Research Questions

Recommended research questions:

**RQ1 — Decomposition quality.**  
Does the proposed method produce microservice candidates closer to known or expert decompositions than baseline methods?

**RQ2 — Domain alignment.**  
Does domain-skeleton-constrained placement reduce contamination and improve domain coherence compared with unconstrained clustering?

**RQ3 — Data ownership and transaction quality.**  
Does the method reduce cross-service data sharing, distributed transaction risk, and write-access conflicts?

**RQ4 — Redundancy handling.**  
Does structured responsibility-based redundancy detection identify harmful duplication while preserving justified bounded-context duplication?

**RQ5 — Human/LLM value.**  
Do LLM judging and human rule injection improve results over deterministic-only refinement, and at what cost?

**RQ6 — Robustness.**  
How sensitive is the method to tag-depth weighting, tag-diversity thresholds, similarity thresholds, and domain-skeleton quality?

### 15.2 Subject Systems

Possible benchmark systems:

- DayTrader,
- JPetStore,
- AcmeAir,
- Plants,
- TrainTicket,
- additional enterprise or industrial monolith if available.

TODO: Select final benchmark set.

TODO: Record system sizes: classes, methods, action points, data sources, tables, chains.

### 15.3 Baselines

Compare against:

- package-based decomposition,
- static dependency clustering,
- Bunch-style modularization,
- Mono2Micro if runnable,
- CARGO if runnable,
- graph embedding or GNN baseline if feasible,
- ablated versions of this method.

TODO: Decide feasible baselines. Avoid overpromising if tools are unavailable.

### 15.4 Metrics

Use a combination of external and internal metrics.

External / ground-truth comparison:

- precision/recall against known decomposition,
- MoJoFM,
- BCP/ICP/SM/IFN/NED if compatible with benchmark ground truth.

Internal architectural metrics:

- contamination,
- coherence,
- harmful redundancy,
- cross-service data sharing,
- distributed transaction count,
- cross-microservice chain count,
- number of shared data sources,
- number of accepted justified duplications.

Human/LLM metrics:

- number of LLM overrides,
- override acceptance rate,
- human review effort,
- number of human rules injected,
- vocabulary growth rate,
- tag correction rate,
- audit-log size,
- inter-rater agreement if multiple judges/humans are used.

TODO: Define exact metrics and scripts.

### 15.5 Ablation Study

Recommended ablations:

1. without domain skeleton,
2. without responsibility records,
3. without data-source tags,
4. without redundancy whitelist,
5. without LLM judge,
6. without human constraints,
7. contamination-only,
8. contamination + coherence but no redundancy,
9. package-only initial assignment vs cascading assignment.

TODO: Choose ablations that are implementable.

### 15.6 Sensitivity Analysis

Test sensitivity to:

- contamination weight $w$,
- tag-diversity thresholds $N$ and $M$,
- redundancy similarity threshold,
- candidate destination top-K,
- service-count target range,
- imperfect or partial domain skeleton.

TODO: Include plots showing stability or failure modes.

### 15.7 Qualitative Evaluation

Include at least one detailed case study showing:

- initial decomposition,
- top contamination issues,
- proposed moves,
- LLM/human override examples,
- final decomposition,
- accepted duplication examples,
- audit trail.

TODO: Use the running example or an actual benchmark monolith.

---

## 16 Threats to Validity

### 16.1 Construct Validity

The proposed scores may not fully capture architectural quality. Contamination, coherence, and redundancy are proxies. They must be validated against expert judgment and existing metrics.

TODO: Compare score changes with human accept/reject decisions.

### 16.2 Internal Validity

LLM-generated tags and responsibility records may be unstable. Prompt changes, model changes, and vocabulary ordering may affect results.

TODO: Use fixed prompts, fixed model versions, temperature control, and repeated runs.

### 16.3 External Validity

Initial implementation may target Java/Spring systems. Results may not generalize to other languages, frameworks, or architectural styles.

TODO: State scope honestly.

### 16.4 Baseline Validity

Some prior tools may be hard to reproduce. If unavailable, baseline comparison may be incomplete.

TODO: Document which baselines are run directly and which are compared conceptually.

### 16.5 Human-in-the-Loop Validity

Human rules may improve results because the human knows the target architecture, not because the algorithm is strong.

TODO: Separate automated-only, LLM-assisted, and human-assisted modes in evaluation.

---

## 17 Discussion

### 17.1 Why Integration Is a Valid Contribution

This method combines known techniques, but the combination is not arbitrary. Each borrowed idea fills a specific gap:

- static analysis extracts the technical graph,
- action points expose runtime entry surfaces,
- responsibility records provide semantic units,
- controlled vocabularies prevent tag drift,
- the domain skeleton constrains placement,
- contamination and coherence make quality interpretable,
- redundancy handling prevents naive clone elimination,
- LLM judging handles borderline semantic cases,
- human rules encode enterprise constraints.

The contribution is the framework that connects these pieces into a reproducible decomposition process. The paper should explicitly state that novelty is not claimed for every component. The novelty is in making domain skeletons, responsibility records, justified duplication, and auditable refinement work together as one method.

### 17.2 Expected Reviewer Objections and Responses

**Objection 1: This is only a combination of existing ideas.**  
Response: The contribution is an integrated decomposition method with explicit operational contracts between the parts. The paper evaluates whether the integration solves decomposition problems not handled well by isolated static, trace, embedding, or search-based methods.

**Objection 2: The domain skeleton moves the hard problem to the user.**  
Response: Many enterprises already maintain capability maps, domain catalogs, or ownership models. The method treats these as useful prior knowledge. When no skeleton exists, the method can infer an initial skeleton from tags and responsibility records, but user-supplied skeletons remain preferred.

**Objection 3: The LLM judge is unreliable.**  
Response: The LLM is not the optimizer. It only audits extraction issues, judges borderline proposals, or suggests vocabulary refinements under closed schemas. Every override is logged and can be ablated.

**Objection 4: The scoring model has too many parameters.**  
Response: The parameters are interpretable architectural preferences, not opaque learned weights. Sensitivity analysis should show which parameters are stable and which require tuning.

**Objection 5: Without implementation, the method is speculative.**  
Response: Correct. The current document is a method design. For publication as a research paper, implementation and evaluation are required. Without implementation, the work may only be suitable as a vision paper, position paper, or workshop paper.

### 17.3 Publication Positioning

The strongest venue framing is:

- SE methodology paper,
- tool-supported decomposition framework,
- empirical evaluation of domain-skeleton-constrained decomposition,
- LLM-assisted but deterministic-first software architecture recovery.

Avoid framing as:

- pure LLM decomposition,
- pure clustering algorithm,
- pure static-analysis paper,
- claim that every component is novel.

### 17.4 What Must Be True for Publication

For a main-track paper, the following must be completed:

1. working prototype,
2. benchmark evaluation,
3. comparison to baselines,
4. ablation study,
5. clear contribution claims,
6. reproducibility package,
7. at least one detailed case study.

For a workshop or vision paper, a detailed method and strong motivation may be enough, but the claims must be modest.

---

## 18 Conclusion

This paper proposes a domain-skeleton-constrained method for decomposing monolithic applications into microservice candidates. The method integrates static extraction, action-point chain analysis, responsibility records, hierarchical tags, data-source ownership, interpretable scoring, justified redundancy handling, bounded LLM judging, and human-in-the-loop refinement. Its central claim is that enterprise decomposition should be auditable and domain-aligned, not merely optimized over code dependencies or embeddings.

TODO: Rewrite conclusion after evaluation. Include concrete empirical findings.

---

## Appendix A Core Data Structures

### A.1 Action Point

```json
{
  "id": "...",
  "trigger_type": "...",
  "signature": "...",
  "package": "...",
  "tags": {
    "L1": "...",
    "L2": "...",
    "L3": "..."
  },
  "chain_id": "..."
}
```

### A.2 Business Component

```json
{
  "id": "...",
  "kind": "service | process | orchestrator | validator | mapper | adapter | other",
  "package": "...",
  "responsibility_record": "...",
  "cross_cutting_label": "business | candidate_cross_cutting | cross_cutting"
}
```

### A.3 Data Source

```json
{
  "id": "...",
  "kind": "relational_table | nosql_collection | queue | topic | external_api | mainframe | file | other",
  "access_pattern": "read | write | read_write",
  "tags": {
    "L1": "...",
    "L2": "...",
    "L3": "..."
  }
}
```

### A.4 Microservice Candidate

```json
{
  "id": "...",
  "name": "...",
  "domain_path": ["...", "...", "..."],
  "business_components": [],
  "action_points": [],
  "data_sources_owned": [],
  "data_sources_accessed": [],
  "scores": {
    "contamination": 0,
    "coherence": 0,
    "harmful_redundancy": 0
  }
}
```

### A.5 Human Constraint

```json
{
  "id": "...",
  "type": "forced_together | forced_apart | anchor_data_source | ignored_data_source | tag_override | domain_rule | service_count_target",
  "scope": [],
  "rule": "...",
  "priority": "hard | soft",
  "created_by": "human | system",
  "iteration": 0
}
```

---

## Appendix B TODO Checklist

### Paper-Framing TODOs

- [ ] Choose final title.
- [ ] Decide whether paper is positioned as method paper, tool paper, empirical study, or vision paper.
- [ ] Reduce contribution claims to 3–5 strong claims.
- [ ] Add precise related-work contrasts.
- [ ] Add a running example.
- [ ] Add all citations in final style.

### Method TODOs

- [ ] Define exact graph schema.
- [ ] Define business component granularity.
- [ ] Define action-point detectors.
- [ ] Define responsibility-record prompt and schema.
- [ ] Define service/data/domain tag inventories.
- [ ] Define domain hierarchy inference algorithm.
- [ ] Define contamination normalization.
- [ ] Define coherence formula.
- [ ] Define redundancy thresholds.
- [ ] Define split/merge/move/lift proposal rules.
- [ ] Define LLM judge prompt.
- [ ] Define audit-log schema.
- [ ] Define human rule language.

### Implementation TODOs

- [ ] Implement static extractor.
- [ ] Implement chain builder.
- [ ] Implement graph hardening loop.
- [ ] Implement cross-cutting detector.
- [ ] Implement responsibility-record generator.
- [ ] Implement tag inventory manager.
- [ ] Implement initial decomposition.
- [ ] Implement scorer.
- [ ] Implement iterative refiner.
- [ ] Implement LLM judge.
- [ ] Implement audit exporter.
- [ ] Package reproducibility scripts.

### Evaluation TODOs

- [ ] Select benchmark systems.
- [ ] Define ground-truth decompositions.
- [ ] Select baselines.
- [ ] Implement evaluation metrics.
- [ ] Run automated-only mode.
- [ ] Run LLM-assisted mode.
- [ ] Run human-assisted mode.
- [ ] Run ablations.
- [ ] Run sensitivity analysis.
- [ ] Write qualitative case study.
- [ ] Report threats to validity.

### Publication TODOs

- [ ] Decide target venue.
- [ ] Match paper length to venue.
- [ ] Decide whether to submit first as workshop/vision or main research paper.
- [ ] Prepare artifact appendix.
- [ ] Prepare replication package.
