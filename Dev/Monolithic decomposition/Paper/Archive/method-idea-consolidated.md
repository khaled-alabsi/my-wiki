# Monolith-to-Microservice Decomposition Method — Idea Collection

> Working document. Consolidates the idea as discussed. No critique, no novelty assessment, no opinion. Purely a description of the proposed method.

## Table of Contents

- [[#1. Core Premise|1. Core Premise]]
- [[#2. Three-Layer Component Extraction|2. Three-Layer Component Extraction]]
- [[#3. Action Points (Trigger Enumeration)|3. Action Points (Trigger Enumeration)]]
- [[#4. Deterministic Chain Extraction per Action Point|4. Deterministic Chain Extraction per Action Point]]
- [[#5. Cross-Cutting Component Detection|5. Cross-Cutting Component Detection]]
- [[#6. Summarization and Hierarchical Tagging|6. Summarization and Hierarchical Tagging]]
- [[#7. Controlled Tag Vocabulary (Tag Inventory)|7. Controlled Tag Vocabulary (Tag Inventory)]]
- [[#8. LLM-Generated Initial Population of Clusterings|8. LLM-Generated Initial Population of Clusterings]]
- [[#9. Scoring Mechanism — Question-Based Coherence Scoring|9. Scoring Mechanism — Question-Based Coherence Scoring]]
- [[#10. Top-Down and Bottom-Up Coherence|10. Top-Down and Bottom-Up Coherence]]
- [[#11. Position on Chains|11. Position on Chains]]
- [[#12. Iterative Refinement Loop|12. Iterative Refinement Loop]]
- [[#13. Open Questions|13. Open Questions]]

-----

## 1. Core Premise

The method decomposes a monolithic application into microservice candidates by:

1. Extracting components in three architectural layers.
1. Enumerating all action points (anything that triggers execution).
1. Extracting deterministic dependency chains from each action point through the mid-tier down to data sources.
1. Filtering out cross-cutting components that should not influence clustering decisions.
1. Summarizing and hierarchically tagging the remaining components using an LLM with a controlled tag vocabulary.
1. Generating an initial population of candidate clusterings using an LLM.
1. Scoring clusterings using a question-based scoring system combined with both top-down (action point → mid-tier) and bottom-up (data source → mid-tier) coherence signals.
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
- Cross-cutting components (logging, authentication, authorization, etc.) — these are flagged separately, see [[#5. Cross-Cutting Component Detection|Section 5]]

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

Chains are used as a **signal source for scoring** (see [[#9. Scoring Mechanism — Question-Based Coherence Scoring|Section 9]]), not as a clustering primitive.

-----

## 5. Cross-Cutting Component Detection

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

## 6. Summarization and Hierarchical Tagging

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

## 7. Controlled Tag Vocabulary (Tag Inventory)

To prevent tag explosion, tagging is controlled by an incrementally maintained inventory.

Workflow:

1. The first class is tagged freely. Tags enter the inventory.
1. For each subsequent class, the LLM **first looks at the existing tags** in the inventory.
1. The LLM decides whether existing tags fit the new class:
- If an existing tag fits → reuse it.
- If no existing tag fits → create a new tag and add it to the inventory.
1. New tags are only created when necessary.

This applies at all three tag levels (generic, narrow, specific).

The result is a compact, controlled vocabulary that grows only as needed, with maximum tag reuse across components.

-----

## 8. LLM-Generated Initial Population of Clusterings

After all components are summarized, tagged, and cross-cutting components are flagged, the LLM is used to **generate an initial population of candidate clusterings** — multiple alternative decompositions, not a single one.

Inputs to the clustering LLM:

- Action-point chains
- Three-level tags per component
- Cross-cutting flags (cross-cutting components excluded or down-weighted)
- Shared dependencies across chains (shared mid-tier services, shared data sources)

Output: a population of N candidate clusterings.

-----

## 9. Scoring Mechanism — Question-Based Coherence Scoring

The LLM does the clustering **and** also computes a coherence score for each candidate clustering using a question list.

For each question, the LLM answers, and the answer maps to score points.

Example question:

> Does the service have a coherent business domain? If yes → +X points; if no → 0 points.

The question list is the scoring rubric. Each candidate clustering is evaluated against every question, accumulating a total score.

-----

## 10. Top-Down and Bottom-Up Coherence

Coherence is evaluated in two directions, both feeding the scoring system.

**Top-down: action point → mid-tier.**
If two action points are clustered into the same microservice and they share mid-tier components, this increases the coherence score for that microservice.

**Bottom-up: data source → mid-tier.**
If two microservices end up using the same data source, this is a signal that they should be combined (or that the data source should be split). This is captured by the scoring as well.

The score combines both directions.

-----

## 11. Position on Chains

Chains are **not** clustering units. They are signal sources for scoring.

Reasons:

- A single chain can legitimately span multiple microservices (see example in [[#4. Deterministic Chain Extraction per Action Point|Section 4]]).
- An action point endpoint may need to be **broken into multiple sub-flows** when its chain crosses microservice boundaries.

Chain information is used to:

- Establish which mid-tier components are shared across which action points (top-down coherence signal).
- Establish which data sources are touched by which chains (bottom-up coherence signal).
- Feed the question-based scoring.

-----

## 12. Iterative Refinement Loop

After the initial population is generated and scored, the method iterates to improve the clusterings.

- Some number of candidates is selected from the population (selection mechanism not yet decided).
- The LLM refines these candidates.
- Re-score using the question list and top-down/bottom-up coherence.
- Iterate.

-----

## 13. Open Questions

These are still undecided and to be designed in the next step:

- **Selection mechanism for the iterative loop.** How candidates are picked from the population for refinement — systematic (e.g., Pareto / tournament / elitism on the score) or LLM-judge-based or random. Not yet decided.
- **How the iteration terminates.** Convergence criterion, max iterations, score plateau threshold — not yet decided.
- **Exact question list for scoring.** The specific questions and their point weights — not yet defined.
- **Naming of the mid-tier layer.** Working name: “business logic tier” / “application tier” / “processing layer”.
- **Naming of cross-cutting components.** Working term: “cross-cutting components” (was “noise” in earlier discussion).
- **How action points are split when their chain crosses microservice boundaries.** Mechanism for breaking an endpoint into sub-flows — not yet defined.