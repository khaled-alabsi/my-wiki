-----

title: “Domain-Hierarchy-Anchored Decomposition of Monolithic Applications into Microservices”
subtitle: “A Skeleton-Constrained, Triple-Score, LLM-Augmented Method with Human-in-the-Loop Refinement”
authors:

- “[TODO: author 1, affiliation]”
- “[TODO: author 2, affiliation]”
  keywords:
- microservices
- software architecture
- monolith decomposition
- hierarchical clustering
- LLM-augmented program analysis
- domain-driven design
  status: “WORK IN PROGRESS — scaffolding draft v0.1 (refactored from internal idea-collection)”
  target_venues: “ICSE / FSE / ASE / EMSE / TSE / TOSEM (pick one — [TODO])”

-----

> **Editorial notes (remove before submission).**
> This document is a scaffolding draft. It is structurally complete but not yet a finished paper. Three conventions are used throughout:
> 
> - `[TODO: …]` — content that must be written or empirically produced.
> - `[DRAFT]` — text refactored from the internal idea-collection; tone and density still need a pass.
> - `[CITE: …]` — bibliographic key resolved in the reference pack at the end.
> 
> All references in `[CITE: …]` markers are present in the consolidated reference pack (Section 15) and are drawn from the prior novelty-and-related-work analysis.

-----

## Abstract

`[TODO: Write abstract last. ~200 words. Cover: (i) the problem — opaque, search-based, or embedding-driven monolith-to-microservice decomposition produces non-interpretable results that practitioners cannot defend to stakeholders; (ii) the contribution — a domain-hierarchy-anchored decomposition that replaces population search with a single skeleton-constrained clustering refined by three deterministic, interpretable scores (contamination, coherence, redundancy), with an LLM judge confined to whitelisted-reason overrides and a human-in-the-loop with three explicit intervention modes; (iii) the validation — benchmark evaluation on Daytrader, Plants, AcmeAir, JPetStore and one industrial monolith using BCP/ICP/SM/IFN/NED, MoJoFM, and human accept-rate; (iv) headline result placeholder.]`

**Keywords:** monolith-to-microservice decomposition, hierarchical clustering with skeletons, interpretable software architecture, LLM-as-extractor-auditor, domain-driven design.

-----

## 1. Introduction

### 1.1 Motivation

`[DRAFT — refactor for venue tone]`
Migrating monolithic enterprise applications into microservices remains a recurring industrial problem. A decade of research has produced decomposition methods spanning four broad families: dynamic-trace-based use-case partitioning [CITE: Kalia2021; Jin2019], static-graph-based dependency partitioning [CITE: Mazlami2017; Nitin2022], embedding- and GNN-based clustering [CITE: Mathai2022; Desai2021; Sellami2025; Trabelsi2024], and interface- or data-centric identification [CITE: Baresi2017; Romani2022]. Despite this diversity, three gaps persist in practice:

1. **Opacity.** Embedding- and search-based methods produce decompositions practitioners cannot defend to stakeholders. There is no per-move provenance.
1. **Single-trigger scope.** Existing pipelines anchor on one trigger family (HTTP endpoints, runtime traces, or static call graphs), excluding scheduler, batch, MQ, and CLI entry points that characterise enterprise monoliths.
1. **No first-class place for enterprise knowledge.** Domain catalogs (BIAN, ArchiMate-derived capability maps, internal taxonomies) exist in the organisation but are not consumed by decomposition algorithms as structural inputs.

`[TODO: tighten with one concrete industrial anecdote or statistic — e.g., percentage of enterprise Java monoliths with non-HTTP entry points; source from Spring Batch / Quartz usage surveys if available.]`

### 1.2 Problem Statement

`[TODO: one-paragraph crisp problem statement. Suggested form: "Given a monolithic application $M$ and (optionally) an enterprise domain catalog $H$ structured as a tree of capability nodes, produce a partition of $M$'s mid-tier components into microservices, each placed at a node of $H$, that minimises a depth-weighted contamination score, maximises a cross-hierarchy coherence score, and minimises an unjustified-redundancy score, while admitting human policy constraints as hard constraints throughout the process."]`

### 1.3 Contributions

This paper makes three primary contributions and three secondary engineering contributions.

**Primary contributions** (see Section 3 for the method overview and Sections 4–10 for details):

- **C1 — Domain hierarchy as a clustering skeleton with empty and multi-occupancy nodes.** We use the microservice-level domain hierarchy not as a soft prior, but as a structural skeleton: interior nodes are legal placements, multi-occupancy is permitted, and empty nodes are first-class. We refine placement deterministically through three interpretable scores. This replaces population search [CITE: Mitchell2006; Praditwong2011; Jin2019] and opaque embeddings [CITE: Sellami2025; Trabelsi2024; Desai2021] with a single skeleton-constrained partition.
- **C2 — Structured responsibility record + three-stage redundancy detection with whitelisted intentional duplication.** Each mid-tier service is summarised into a fixed-schema record `(action_verb, object, description, inputs, outputs, data_sources_touched, tags)`. The record drives a three-stage redundancy detector (literal → structured → semantic) with a four-path resolver including ACCEPT-as-justified under a closed whitelist of DDD-, operational-, ACL-, and latency-grounded reasons.
- **C3 — Six-step deterministic-Propose / LLM-Judge / Human-Supervise iteration cycle.** Deterministic math proposes moves over a domain-hierarchy trie; an LLM judge confirms or overrides only under a whitelisted reason or proposes vocabulary refinements; a human supervises through three explicit modes. Every move has auditable provenance.

**Secondary contributions** (engineering reuse, not novel in isolation, but engineered into a coherent pipeline):

- **C4 — Unified nine-trigger action-point primitive** (REST, SOAP, scheduler, batch, MQ, GraphQL, gRPC, CLI, webhook) extending entry-point-based decomposition [CITE: Baresi2017; Kalia2021].
- **C5 — Symmetric three-level hierarchical tagging on services AND data sources** from one controlled vocabulary inventory, extending Service Cutter’s flat catalog [CITE: Gysel2016].
- **C6 — LLM-as-extractor-auditor with a `fix_extractor` vs `hardcode_patch` dichotomy** that biases the system toward systemic upstream fixes over per-case patches.

### 1.4 Paper Structure

Section 2 surveys related work and locates the contribution against it. Section 3 gives a method overview. Sections 4–10 detail the method: Section 4 covers foundations (layers, action points, chains, graph hardening); Section 5 the semantic layer (responsibility records and tagging); Section 6 the skeleton (the microservice-level domain hierarchy); Section 7 initial assignment; Section 8 scoring; Section 9 iterative refinement; Section 10 the human-in-the-loop. Section 11 discusses boundaries and anticipated reviewer objections. Section 12 outlines the evaluation plan. Section 13 concludes.

-----

## 2. Background and Related Work

`[Editorial note: structured as four families + one positioning subsection. Each family ends with a one-sentence "where we differ" anchor that recurs in the method sections.]`

### 2.1 Microservice Decomposition

**Search-based and evolutionary modularization.** Bunch [CITE: Mancoridis1998; Mancoridis1999; Mitchell2006; Mitchell2008] established the Modularization Quality (MQ) trade-off of inter- vs intra-cluster edges, refined by multi-objective search [CITE: Praditwong2011; Harman2002]. FoSCI [CITE: Jin2019] applies this lineage to microservice decomposition using execution traces and a genetic algorithm.

**Static-graph and dependency-based identification.** Mazlami et al. [CITE: Mazlami2017] extract coupling graphs from monoliths. CARGO [CITE: Nitin2022] performs flow-sensitive system dependency-graph analysis with database tables. Levcovitz et al. [CITE: Levcovitz2016] and Chen et al. [CITE: Chen2017] use dataflow-driven approaches.

**Dynamic-trace and use-case-based partitioning.** Mono2Micro [CITE: Kalia2021] dynamically collects runtime traces under the execution of specific business use cases. Taibi & Systä [CITE: Taibi2019] apply process mining. `[DRAFT]` Both families anchor decomposition on user-defined business use cases executed at runtime; non-HTTP trigger families (scheduler, MQ, CLI, batch) are systematically out of scope.

**Embedding- and GNN-based clustering.** CO-GCN [CITE: Desai2021] uses a graph convolutional network to dilute outliers. CHGNN [CITE: Mathai2022] enriches monolith graphs with heterogeneous program + resource nodes. MonoEmbed [CITE: Sellami2025] employs contrastive learning on LLM code embeddings. MAGNET [CITE: Trabelsi2024] is a method-level GNN. MicroDec [CITE: Sellami2024] uses LLMs as feature providers.

**Interface- and data-centric identification.** Baresi et al. [CITE: Baresi2017] use OpenAPI interface analysis. Romani et al. [CITE: Romani2022] propose data-centric microservice identification. Service Cutter [CITE: Gysel2016] organises 16 coupling criteria into four flat categories. Context Mapper [CITE: Kapferer2020] performs DDD-driven context modelling. Agarwal et al. [CITE: Agarwal2021] use business functionality inference.

**Where we differ.** Existing methods either (a) optimise a population (GA Pareto fronts), (b) cluster opaque embeddings, or (c) anchor on a single trigger family. We produce a *single* clustering, refined deterministically, with a multi-trigger action-point primitive and a domain hierarchy as a structural skeleton.

### 2.2 Constrained, Seeded, and Hierarchical Clustering

Constrained clustering injects prior knowledge through pairwise must-link/cannot-link constraints [CITE: Wagstaff2001; Davidson2005], seed sets [CITE: Basu2002; Basu2004], or triplet constraints [CITE: Chatziafratis2018]. HierSeed [CITE: Shen2022] seeds expert-crafted taxonomies but forces every taxonomy node to be populated. Hierarchical clustering with prior knowledge [CITE: Ma2018] and joint spherical-tree + text embedding [CITE: Meng2020] use external taxonomies as soft penalties. Recent surveys [CITE: GonzalezAlmagro2024; Bae2020] catalogue the design space.

**Where we differ.** Our skeleton admits *empty* interior nodes and *multi-occupancy* leaves, matching how enterprise capability maps are authored (aspirationally complete, partially instantiated) but not how seeded HC typically operates.

### 2.3 Hierarchical Classification and Tag-Based Scoring

Depth-weighted hierarchical penalties are standard in classification [CITE: Bertinetto2020; Silla2011; Kosmopoulos2015; CesaBianchi2006]. Tree-edit-distance is due to Tai [CITE: Tai1979] and Zhang & Shasha [CITE: ZhangShasha1989]. IDF term weighting is from Salton & Buckley [CITE: SaltonBuckley1988]. Semantic-web service catalogs (OWL-S, WSMO) [CITE: Martin2004; Roman2005] use flat taxonomies (UNSPSC, NAICS).

**Where we differ.** We compute depth-weighted distance against a *placement path*, not a *label*, and we decompose contamination by source (service, data-source, action-point) for diagnostic refactoring.

### 2.4 LLM-as-Judge and Human-in-the-Loop SE

LLM-as-judge has become an active research area in software engineering [CITE: He2025; Wang2025; Hou2024]. Interactive software re-modularization is precedented by Bavota et al. [CITE: Bavota2012]. The broader interactive-clustering literature [CITE: Amershi2014; Bae2017; Vikram2016; Settles2009] supports pairwise constraints and developer feedback.

**Where we differ.** We confine the LLM to *whitelisted-reason overrides* and *vocabulary refinement*, not to primary scoring. Human signals form a three-mode typology (passive review, active rule injection, escalation) with *policy-as-constraint* domain rules.

### 2.5 Domain-Driven Design and Enterprise Catalogs

DDD [CITE: Evans2003; Vernon2013; Vernon2016] and the microservice canon [CITE: Newman2015] motivate bounded contexts and aggregate boundaries; EventStorming [CITE: Brandolini2018] is a related discovery practice. Enterprise capability maps exist in the wild: the BIAN Service Landscape v13.0 [CITE: BIAN2025] defines roughly 326 service domains in a three-level Business Area → Business Domain → Service Domain hierarchy with 250 Semantic APIs; ArchiMate 3.2 [CITE: ArchiMate2022] formalises a Motivation layer of Drivers, Goals, Outcomes, Principles, Requirements, Constraints, and Stakeholders.

**Where we differ.** We consume such catalogs as the *clustering skeleton*, not as informal background; when no catalog is available, we infer one with the LLM but feed it through the same algorithm.

### 2.6 Cross-Cutting Concerns and Clone Detection

Cross-cutting concerns and aspect mining [CITE: Marin2007; Kiczales1997; Robillard2007]; code clone detection [CITE: RoyCordy2009; Sajnani2016; White2016]; refactoring opportunity detection [CITE: Tsantalis2009].

**Where we differ.** Cross-cutting detection is used twice — once before clustering (filter) and once during it (the lift-to-shared operation in iterative refinement). Clone detection feeds the redundancy score but with a *whitelist for intentional duplication* drawn from DDD.

### 2.7 Positioning Summary

`[TODO: Table 1 — coverage matrix. Rows = competing methods (Mono2Micro, FoSCI, CARGO, MAGNET, CHGNN, MonoEmbed, MicroDec, Service Cutter, Context Mapper). Columns = (trigger families covered, resource graph coverage, hierarchical skeleton, interpretable scoring, redundancy whitelist, LLM role, human-in-the-loop modes, output: single vs Pareto). Use a tick / partial / cross notation. This is the single most important figure for related-work reviewers.]`

-----

## 3. Method Overview

### 3.1 Core Premise

`[DRAFT — sharpen for venue tone]`
The method decomposes a monolithic application into microservice candidates through a deterministic pipeline whose every step has interpretable inputs and outputs. There is **no population, no genetic algorithm, no Pareto front**. There is one clustering, refined iteratively, with auditable per-move provenance.

The pipeline has twelve stages:

1. **Three-layer component extraction** (Section 4.1).
1. **Action-point enumeration** across nine trigger families (Section 4.2).
1. **Per-action-point deterministic chain extraction** (Section 4.3).
1. **Graph hardening** via LLM revalidation, human quick-review, and noise filter (Section 4.4).
1. **Cross-cutting filtering** (Section 4.5).
1. **Service-level summarisation, responsibility records, and three-level tagging** (Section 5.1–5.3).
1. **Data-source hierarchical tagging** (Section 5.4).
1. **Domain-hierarchy skeleton** definition (user-supplied or LLM-inferred) (Section 6).
1. **Single initial whole-clustering** via cascading assignment (Section 7).
1. **Triple scoring** — contamination, coherence, redundancy — plus an LLM-judged rubric for ties (Section 8).
1. **Iterative refinement** through four operations: move, split, merge, lift-to-shared (Section 9).
1. **Human-in-the-loop** between iterations (Section 10).

### 3.2 Pipeline Figure

`[TODO: Figure 1 — pipeline diagram. Three swim lanes: deterministic (boxes 1, 3, 4-step1, 7, 8-deterministic-scores, 9-step1-to-4), LLM (boxes 4-step2, 5, 6, 8-rubric, 9-step5), human (boxes 4-step3, 10). Arrows show data flow + feedback edges from human to deterministic config (rule injection).]`

-----

## 4. Foundations: Components, Action Points, Chains, and Graph Hardening

### 4.1 Three-Layer Component Extraction

`[DRAFT — verbatim from idea collection, minor reformat]`
The monolith is parsed into three architectural layers using static analysis (tree-sitter, JavaParser, Spoon, Soot, WALA, CodeQL, or equivalent):

- **Layer 1 — Action layer.** Components that can trigger execution (Section 4.2).
- **Layer 2 — Business-logic tier** (a.k.a. application tier, processing layer). Services, processes, orchestration components, and any mid-tier processing component. Cross-cutting components (logging, authentication, authorization) are flagged separately (Section 4.5).
- **Layer 3 — Data-source layer.** Databases (relational, NoSQL), mainframe connections, SOAP/third-party service connections, message queues used as data sources, and any external persistence or data-exchange endpoint.

`[TODO: add a static-analysis configuration matrix as Table 2 — stack (Spring, Quartz, JMS, Kafka, JAX-RS, JAX-WS) → annotations & descriptors parsed. This pre-empts the reviewer question "how does this generalise across stacks?"]`

### 4.2 Action Points — A Unified Multi-Trigger Primitive (C4)

An **action point** is any component that can trigger execution from outside the system. Enumeration is unified across nine trigger families: REST controllers, SOAP endpoints, schedulers (cron, Spring `@Scheduled`, Quartz), batch jobs (Spring Batch), message-queue listeners (JMS, Kafka, RabbitMQ), GraphQL endpoints, gRPC endpoints, CLI entry points, and webhooks. Each action point becomes a first-class unit of analysis.

`[DRAFT — from novelty analysis E1 for-paper snippet]`
Existing pipelines anchor on a single trigger family — runtime traces of business use cases [CITE: Kalia2021], OpenAPI endpoints [CITE: Baresi2017], execution traces [CITE: Jin2019], or static call graphs [CITE: Trabelsi2024]. We treat REST, SOAP, scheduler, batch, MQ, GraphQL, gRPC, CLI, and webhook entries as instances of one *action-point* primitive, making batch and scheduled pipelines (typical of enterprise monoliths) first-class citizens of decomposition.

### 4.3 Deterministic Per-Action-Point Chain Extraction (C5 supporting)

For each action point, a deterministic script extracts the full downstream dependency chain: all called methods and classes, all touched mid-tier services, all touched data sources (DB tables, queues, external APIs), and all relevant configuration. The output is a per-action-point closure: a structured artifact describing the chain.

`[DRAFT — important clarification]`
Chains are **not** used as the unit of clustering. A single chain can legitimately be split across multiple microservices. For example, an action point `GET /customer/data` calling Service A (which reads Data Source 1) and Service B (which reads Data Source 2) may span two microservices if Data Source 1 belongs to microservice X and Data Source 2 to microservice Y; the action-point endpoint itself may then be split or routed via an aggregator. Chains are a *signal source for scoring* (Section 8), not a clustering primitive.

### 4.4 Graph Extraction Hardening (C6)

A four-step hardening pipeline.

**Step 1 — Deterministic extraction, configured maximally.** Static analyser configured for the specific stack: all annotation packages registered (Spring, JAX-RS, JAX-WS, Spring Batch, JMS, Kafka, Quartz, custom annotations); custom dispatcher patterns registered (factories, registries, programmatic handler registration); reflection sites flagged for manual review; configuration files parsed (Spring XML, `application.yaml`, properties) with edges added from config-declared bindings; edge types preserved (call / data-access / config / event / transaction).

**Step 2 — LLM revalidation pass.** For each chain, an LLM reviews and reports missing edges, suspicious gaps, suspicious branches, and likely false positives. The LLM does **not silently patch** the graph; it produces a report with two action types:

- `fix_extractor` — improve the static-analysis configuration. Applied once, benefits all chains.
- `hardcode_patch` — manual edge addition or removal with justification. Last-resort fix.

The `fix_extractor` : `hardcode_patch` ratio is tracked as a pipeline-quality KPI: a healthy pipeline biases toward systemic upstream fixes.

`[DRAFT — from novelty analysis E3 for-paper snippet]`
Recent LLM-augmented program analysis [CITE: Sellami2025; Trabelsi2024] treats the LLM as a *feature provider*. We instead use it as an *extractor auditor*, with a structured `fix_extractor` vs `hardcode_patch` dichotomy that pushes systemic gaps back into the deterministic extractor rather than papering over individual errors.

**Step 3 — Human quick review.** Human reviews only LLM-flagged chains: high-confidence-correct chains are auto-approved; flagged chains are routed to a reviewer who can accept, reject, or trigger an extractor reconfiguration.

**Step 4 — Noise filter on chains.** Strip migration-irrelevant components before downstream LLM agents see chains: cross-cutting components (Section 4.5), test scaffolding, dead code, framework boilerplate, generated code, build/deployment configuration.

`[TODO: pseudocode block for the four-step pipeline. Also a sequence diagram in Figure 2.]`

### 4.5 Cross-Cutting Component Detection

`[DRAFT — short, can stay near-verbatim]`
Components every microservice would need anyway. The LLM tags each mid-tier class as:

- `cross_cutting` — definitely cross-cutting; exclude from clustering signal.
- `candidate_cross_cutting` — possibly cross-cutting; needs human confirmation.
- `business` — full weight in clustering.

Human review focuses on `candidate_cross_cutting`. Cross-cutting detection is repeated implicitly during iteration through the lift-to-shared operation (Section 9.1) — a redundancy resolution path that promotes a duplicated component to the cross-cutting bucket [CITE: Marin2007; Kiczales1997].

-----

## 5. Semantic Layer: Responsibility Records and Hierarchical Tagging

### 5.1 Service-Level Summarisation

`[DRAFT]`
For each mid-tier service, the LLM produces a structured progressive summary: starting generic (what kind of component this is at a high level), drilling down progressively, describing the class’s responsibilities, then its role.

### 5.2 Responsibility Records (C2 supporting)

Each mid-tier service receives a structured **responsibility record** combining controlled-vocabulary fields and free-form description:

```
{
  action_verb:           <from controlled vocabulary>     e.g., "convert", "validate", "fetch", "compute", "transform", "orchestrate"
  object:                <from controlled vocabulary>     e.g., "currency", "customer-record", "payment-amount"
  description:           <1-2 sentence LLM-written>       e.g., "Converts a monetary amount between currencies using daily FX rates"
  inputs:                [<typed input descriptors>]
  outputs:               [<typed output descriptors>]
  data_sources_touched:  [<data source IDs>]
  tags:                  { L1, L2, L3 }                   (filled by Stage 3)
}
```

The `action_verb` and `object` controlled vocabularies are maintained as inventories (Section 5.5) to prevent vocabulary explosion.

`[DRAFT — from novelty analysis E5 for-paper snippet]`
The responsibility record extends OWL-S’s IOPE pattern [CITE: Martin2004] and Jacobson’s actor-verb-object form [CITE: Jacobson1992] with `data_sources_touched` and three-level tags. Unlike semantic-web service catalogs — which are static descriptors for discovery — our records are *operational inputs* to a deterministic decomposition algorithm, and the `(action_verb, object)` pair forms the second key of three-stage redundancy detection (Section 8.3).

The responsibility record is used for: (a) redundancy detection (Section 8.3); (b) tag enrichment (Section 5.3); (c) contamination detection independent of tags (a service whose `data_sources_touched` are all in microservice X but is placed in microservice Y is contaminated independent of its tags); (d) LLM-judge prompts, more efficient than showing raw code.

### 5.3 Service-Level Three-Level Hierarchical Tagging

Three levels of tags per service, drawn from the controlled service-level tag inventory (Section 5.5):

- **L1 — very high / generic.** Example: `customer`.
- **L2 — middle / narrow.** Example: `customer care`.
- **L3 — deep / very specific.** Example: `customer care data retrieval`.

The structured responsibility fields inform tag selection.

### 5.4 Data-Source Three-Level Hierarchical Tagging

`[DRAFT]`
Three-level tagging applied to data sources, *the second of three independent tag hierarchies*:

- **L1** — business-domain area. Examples: `customer`, `payment`, `inventory`.
- **L2** — sub-domain. Examples: `customer master`, `customer transaction`, `customer interaction`.
- **L3** — specific role. Examples: `customer profile store`, `customer event log`.

Independent of the service-level tag hierarchy. May use overlapping vocabulary but maintained separately because data sources and services are different concerns. Cross-hierarchy alignment is a scoring signal (Section 8.2).

`[DRAFT — from novelty analysis E4 for-paper snippet]`
Service Cutter [CITE: Gysel2016] organises 16 flat coupling criteria into four categories without a tag sub-hierarchy; semantic-web service catalogs [CITE: Martin2004; Roman2005] classify services against fixed flat taxonomies (UNSPSC, NAICS) but do not cover data sources. We tag services and data sources with the same three-level taxonomy drawn from one controlled inventory, enabling cross-hierarchy alignment scoring.

### 5.5 Controlled Vocabulary Inventories

`[DRAFT — slight refactor]`
To prevent vocabulary explosion, all tagging and structured-field generation is controlled by incrementally maintained inventories. Workflow: (1) the first item is tagged freely; values enter the inventory; (2) for each subsequent item, the LLM first inspects existing inventory entries; (3) if an existing entry fits → reuse it, otherwise → create new and add to inventory.

Applied to: service-level L1/L2/L3 tags; data-source-level L1/L2/L3 tags; microservice-level L1/L2/L3/L4 domain hierarchy (when LLM-inferred); responsibility `action_verb`; responsibility `object`.

`[TODO: design decision — whether the three tag hierarchies plus the two responsibility vocabularies are unified into one inventory or maintained as separate aligned inventories. Provisional answer: separate-but-aligned. Defer to evaluation.]`

-----

## 6. Clustering Skeleton: The Microservice-Level Domain Hierarchy (C1)

### 6.1 Structure

The skeleton is a tree of nested cluster nodes:

- **L1** — top-level domains (`customer`, `payment`, `inventory`).
- **L2** — sub-domains within each L1.
- **L3** — finer sub-domains.
- **L4** — finest level. `[TODO: empirical evaluation needed — is L4 useful or is L3 sufficient? Provisionally retain L4 and ablate.]`

### 6.2 Source of the Hierarchy

The hierarchy is either **user-supplied** from an enterprise domain catalog (preferred when available) or **LLM-inferred** from the monolith’s services, data sources, action points, and their tags. Enterprise capability maps in the wild include the BIAN Service Landscape v13.0 [CITE: BIAN2025] and ArchiMate 3.2 capability/motivation layers [CITE: ArchiMate2022].

`[TODO: address the reviewer concern "you've moved the hard problem to skeleton design" — argue that (a) large organisations have skeletons in hand, (b) the skeleton is a forcing function for stakeholder alignment, not a defect, (c) LLM-inferred fallback is supported and benchmarked separately. See Section 11.]`

### 6.3 Clusters and Microservices

- Each cluster node is a container.
- A cluster can hold **multiple microservices**. No constraint of one microservice per cluster.
- A cluster can stay **empty** — the hierarchy is a skeleton, not a requirement.
- A microservice lives at a specific node (its **domain path**, e.g., `customer/care/inbound`).

`[DRAFT — from novelty analysis E6 for-paper snippet]`
Constrained and seeded hierarchical clustering [CITE: Wagstaff2001; Basu2002; Chatziafratis2018; Shen2022] inject prior structure as pairwise constraints, seed points, or triplet relations. We treat the enterprise domain catalog as a complete clustering *skeleton* — an L1–L4 cluster tree where every interior node is a legal placement, multi-occupancy is allowed, and empty nodes are first-class — matching how enterprise capability maps are authored.

### 6.4 The Three Independent Hierarchies — Cross-Hierarchy Alignment

`[DRAFT — present as a table]`

|Hierarchy         |What it tags                             |Depth|Purpose                            |
|------------------|-----------------------------------------|-----|-----------------------------------|
|Service-level     |Each mid-tier service                    |L1–L3|Coherence + tag-based contamination|
|Data-source-level |Each data source                         |L1–L3|Data-ownership scoring             |
|Microservice-level|Each microservice (placement in the tree)|L1–L4|The clustering skeleton            |

A microservice placed at `customer/care` should contain services tagged `customer / customer-care / *` and use data sources tagged `customer / customer-master / *`. Alignment = high coherence; mismatch = contamination.

-----

## 7. Initial Whole-Clustering Assignment

### 7.1 Output of the First Iteration

`[DRAFT]`
Every mid-tier business component assigned to a microservice; every microservice placed at a node in the domain hierarchy; some predefined cluster nodes may stay empty; cross-cutting components are not assigned to microservices.

### 7.2 Cascading Assignment Mechanism

A three-step cascade.

**Step 1 — Coarse cut by action-point package depth.** Group action points by their package (the action point’s own package, not every component in the chain). Package depth is resolved as **tag-coherence-driven depth** — go deeper only if it improves L1+L2 tag coherence within the resulting groups.

**Step 2 — If a group is too big, split by service-level L1+L2 tags.**

**Step 3 — If still too big, split by data-source-level L1+L2 tags.**

### 7.3 Definition of “Too Big” — Tag-Diversity Threshold

A group is too big if it contains more than $N$ distinct L1 tags or $M$ distinct L2 tags, regardless of raw size. The **target microservice count range** (e.g., 5–10) is supplied by the human; the cascade continues while (tag-diversity high OR group count below human target).

`[DRAFT — from novelty analysis E7 for-paper snippet]`
Existing seeding strategies cut by class count [CITE: Mitchell2006], dendrogram threshold [CITE: Kalia2021], or trace-atom grouping [CITE: Jin2019]; we cut by *tag diversity* and choose package depth to maximise L1+L2 tag coherence, then place each group at the domain node minimising tag tree-edit-distance contamination.

### 7.4 Placement into the Domain Hierarchy

Each group (= microservice) is placed at the node in the microservice-level domain hierarchy whose path minimises contamination of the group’s contents (Section 8.1).

`[TODO: pseudocode for the cascading mechanism + worked example on a small synthetic monolith.]`

-----

## 8. Scoring (C2 + C5)

The clustering is scored by three deterministic scores plus an LLM-judged rubric.

### 8.1 Contamination (Minimise)

**Definition.** Contamination measures misplacement: components that don’t belong where they sit. Floor at 0.

**Per-component contamination.** Given the tag path $T$ of a component and the domain path $P$ of its microservice, contamination is the depth-weighted tree-edit-distance:

$$
d(T, P) = \sum_{i:, T_i \neq P_i} w^{,\text{max_depth} - i}, \quad w > 1
$$

with default $w = 3$. L1 mismatch is much more expensive than L3 mismatch — matching the intuition that crossing top-level domain boundaries is the real damage.

**Three contamination sources** (reported separately for diagnostic purposes):

- **Service contamination** — services tagged outside the microservice’s domain path.
- **Data-source contamination** — data sources tagged outside the microservice’s domain path. Usually weighted heaviest (data ownership is the core of microservice definition).
- **Action-point contamination** — action points whose own tags don’t match the microservice’s domain path.

**Per-microservice and total:**

$$
\text{contamination}(m) = \sum_{c \in m,, c \notin \text{cross_cutting}} d(T_c, P_m) \cdot \text{weight}(c.\text{type})
$$

$$
\text{total_contamination} = \sum_m \text{contamination}(m)
$$

Cross-cutting components are excluded.

`[DRAFT — from novelty analysis E8 for-paper snippet]`
Depth-weighted hierarchical penalties are standard in classification [CITE: Bertinetto2020; Silla2011; CesaBianchi2006]; the underlying tree-edit-distance is due to Tai [CITE: Tai1979]. We adapt these to clustering quality by computing, for each component in a microservice, the depth-weighted distance from its tag path to the microservice’s domain placement path, and we decompose contamination by source (service, data-source, action-point) to drive specific Section 9 refactorings.

`[TODO: sensitivity analysis of w on a benchmark. Default w = 3.]`

### 8.2 Coherence (Maximise)

**Definition.** Coherence rewards positive structure within and across microservices. Unbounded above. Distinguishes microservices with contamination = 0 by how much positive structure they exhibit.

**Coherence signals.** Same service-level L1/L2/L3 tag across services within a microservice (L3 matches IDF-weighted, rare tags weighted higher [CITE: SaltonBuckley1988]); data-source exclusivity (used by only one microservice); action-point tag alignment with its target microservice; cross-hierarchy alignment (L1/L2 match between action points + services + data sources of a microservice); same transactional boundary; same write-access pattern.

**Coupling penalties** (subtracted from coherence): cross-microservice data-source sharing; cross-microservice chain count (an action point’s chain crossing $N$ microservices contributes an $(N-1)$ penalty); read-write conflicts across services; distributed transaction count; synchronous-call density across boundaries.

`[DRAFT — from novelty analysis E9 for-paper snippet]`
Bunch’s MQ [CITE: Mitchell2006] rewards intra-cluster edges; Service Cutter [CITE: Gysel2016] enumerates 16 coupling criteria; CARGO [CITE: Nitin2022] adds transaction awareness. Our coherence score unifies these into a positive-direction signal that IDF-weights rare L3-tag matches [following CITE: SaltonBuckley1988] and rewards data-source exclusivity and write-access locality jointly.

### 8.3 Redundancy (Minimise Toward a Justified Floor) (C2)

Two services in different microservices are *functionally redundant* if they share the same `(action_verb, object)` or have high description similarity. Redundancy is **not always an error**; three legitimate reasons for duplication are recognised:

- **Cross-cutting that escaped Section 4.5** (validation, currency conversion, formatting, schema mapping). Second-chance filter.
- **Bounded-context duplication** — DDD-style [CITE: Evans2003; Vernon2013]. Two microservices both have a “Customer” concept with different attributes/responsibilities.
- **Operational duplication** — high-availability, latency, or independent-deployment concerns [CITE: Newman2015].

**Three-stage detection** (cheap → expensive):

- **Stage 1 — Literal duplication.** Same class/method ID in multiple microservices. Trivially detected.
- **Stage 2 — Structured-responsibility duplication.** Two services share `(action_verb, object)` across microservices. Deterministic.
- **Stage 3 — Semantic-responsibility duplication.** Description-embedding cosine similarity > threshold across microservices. Expensive; run sparingly.

**Per clustering:**

$$
\text{total_redundancy} = \sum_{c:,\text{redundancy}(c)>1} \bigl(\text{redundancy}(c) - 1\bigr)
$$

Minimise toward a **justified floor** — not zero.

**Resolution paths.**

1. **Eliminate** — consolidate into the microservice with lowest contamination.
1. **Promote to shared/cross-cutting** (the lift-to-shared operation in Section 9.1).
1. **Accept** — intentional duplication. Requires a whitelisted reason: bounded-context, operational-independence, anti-corruption-layer, latency-critical.
1. If no whitelisted reason fits → default to (1) or (2).

`[DRAFT — from novelty analysis E10 for-paper snippet — placeholder, replace with original]`
Code-clone detection literature [CITE: RoyCordy2009; Sajnani2016; White2016] treats all duplication as defect. DDD canon [CITE: Evans2003; Vernon2013; Newman2015] endorses intentional duplication but does not operationalise it. We close the gap with a three-stage detector and a four-path resolver where ACCEPT-as-justified is gated by a closed whitelist.

### 8.4 LLM-Judged Rubric (Secondary)

`[DRAFT]`
Used for ties and borderline decisions only. Five questions:

- “Does this microservice have a coherent business domain?” (Yes / Partial / No)
- “Could you name this microservice in 2–3 words?” (Yes / Struggles / No)
- “Is this microservice’s data ownership clear?” (Yes / Mixed / No)
- “Does this microservice respect DDD aggregate boundaries?” (Yes / Partial / No)
- “Are the action points exposed by this microservice consistent with its domain?” (Yes / Mostly / No)

The LLM rubric is *not* the primary scoring driver. It is invoked when deterministic scores tie, to validate borderline moves before they’re applied, and as a final pass on the converged clustering. `[TODO: pre-empt reviewer objection — ablation by replacing the judge with a coin flip; we expect graceful degradation, not collapse.]`

### 8.5 Use in Iterative Refinement

- **Contamination** drives **move** and **split** decisions (what to fix).
- **Coherence** drives **merge** and tie-breaking.
- **Redundancy** drives **lift-to-shared**.
- **LLM rubric** validates borderline moves and provides a stop condition.

-----

## 9. Iterative Refinement (C3)

The initial clustering is refined iteratively. **One clustering**, not a population.

### 9.1 Four Operations

- **Move** — relocate a portion of a service to a different microservice. Destination can be the same leaf cluster, a different sub-cluster of the same L1 (e.g., `customer/care` → `customer/billing`), or a different L1 cluster entirely.
- **Split** — break a domain-incoherent service into smaller services.
- **Merge** — combine two related small services in the same or adjacent cluster nodes.
- **Lift-to-shared** — promote a redundant component to the cross-cutting / shared bucket.

### 9.2 Six-Step Iteration Cycle

`[DRAFT]`

- **Step 1 — Detect.** Rank microservices by contamination (descending). Pick top-K most contaminated (small K, 1–3 per iteration). Also scan for redundancy candidates (Stages 1 + 2 of Section 8.3). Optionally rank by contamination *concentration* (per-component) to favour few-bad-components over uniformly-mediocre microservices.
- **Step 2 — Identify.** Within each detected microservice, rank components by individual contamination contribution $d(T_c, P_m)$. Top contributors are candidates to move out, split off, or lift-to-shared.
- **Step 3 — Search.** For each candidate component, find candidate destination microservices via **trie-lookup on the domain hierarchy**. Build a trie of microservices indexed by domain path; for a component with tag $T$, traverse the trie following $T$’s path; top-K closest microservices (by LCA depth) become candidate destinations. Lookup is $O(\text{depth})$ per component, not $O(N)$.
- **Step 4 — Propose.** Deterministic suggestion based on the search: move to lowest-distance destination; split if the contaminating components form an internally coherent subgroup; merge if two microservices in adjacent nodes share most of their action points / data sources / mid-tier components; lift-to-shared if redundancy is high and per-location contamination is uniformly low.
- **Step 5 — Judge.** LLM confirms or overrides the deterministic proposal. Override only with a **whitelisted reason**: usage-locality, transaction-integrity, tag-mistagging, adapter-pattern; for redundancy resolution, the four reasons in Section 8.3. The LLM may also propose **tag refinement** (e.g., split `customer/care/inbound` into `customer/care/inbound/b2b` and `customer/care/inbound/b2c`); the tag vocabulary is updated, components re-tagged, and the math now sees the divergence. **The LLM does not override the math — it updates the math’s inputs.** Every override produces an audit record (component, microservice, deterministic suggestion, LLM decision, whitelisted reason) used for reviewer-defensibility, calibration, and revert.
- **Step 6 — Apply.** Update only the affected microservices’ scores (lazy recomputation — cached per-microservice contamination, recompute only the two affected ones). Move to the next candidate.

`[DRAFT — from novelty analysis B1 Anchor 3]`
We separate concerns in iterative refactoring: deterministic math proposes moves (with LCA-depth-bounded trie lookup over the domain hierarchy), an LLM judge confirms or overrides them under a whitelisted-reason discipline, and a human supervises through three explicit interaction modes — yielding auditable per-move provenance unavailable to LLM-judge-centric [CITE: He2025; Wang2025] or pure search-based [CITE: Mitchell2006; Jin2019] methods.

### 9.3 Conflict Resolution Priority

1. **Hard human constraints** (forced-together / forced-apart / anchors / ignored) — never overridden by math or LLM.
1. **Deterministic math** — suggests the move.
1. **LLM judge** — confirms or overrides with whitelisted reason.
1. **Human-in-the-loop** (Section 10) — can revert any change post-hoc.

### 9.4 Per-Iteration Budget

`[DRAFT]`
At most K microservices detected per iteration (small, e.g., 1–3); at most M moves total; at most one split or one merge. Forces incremental progress; prevents whole-clustering thrashing.

### 9.5 Termination

Multiple stop conditions, any one triggers:

- **Contamination floor:** `total_contamination ≤ threshold`.
- **Coherence plateau:** no coherence improvement for K iterations.
- **No accepted moves** in a full iteration.
- **Max iterations.**
- **Human says we’re done** (Section 10).

### 9.6 Convergence Argument (Lyapunov-Style)

`[TODO: this is a critical novelty lever flagged in the novelty analysis (Lever 1). Sketch: define the total score $S = \alpha \cdot \text{contamination} - \beta \cdot \text{coherence} + \gamma \cdot \text{redundancy}$. Show that each deterministic proposal weakly decreases $S$; LLM overrides are admitted only when they do not increase $S$ (or when paired with vocabulary refinement that strictly decreases $S$ after re-scoring). Conclude monotone non-increase of $S$ → termination. This converts the loop into a "provably-improving local-search-with-judge" in the style of Mitchell & Mancoridis [CITE: Mitchell2006].]`

-----

## 10. Human-in-the-Loop

`[DRAFT]`
The human is in the iteration itself, not just before it. Three intervention modes.

### 10.1 Mode 1 — Per-Iteration Review (Passive)

After each iteration, the system shows the human: top N moves applied; top N moves rejected by the LLM judge with reasons; microservices with highest remaining contamination; new redundancy detections. The human may accept the iteration as-is, revert specific moves (which creates a forced-apart or forced-together constraint), or skip to “run K more iterations without review” (batch mode). **Default: silent batch mode**; the human is invoked only when the iteration produces low-confidence changes or when contamination/coherence diverge unexpectedly.

### 10.2 Mode 2 — Inter-Iteration Rule Injection (Active)

Between iterations, the human can add rules:

- New forced-together / forced-apart constraints.
- New anchor or ignored data sources.
- New microservice-level domain hierarchy nodes (e.g., “add L3 cluster `customer/care/vip`”).
- Tag overrides (e.g., “this service is mistagged, correct to `payment/refund`”).
- **Domain rules as policy-as-constraint** (e.g., “all services touching `customers_pii` must live in `customer/data-privacy`”).

The policy-as-constraint rule type is the most distinctive: a single rule propagates across many components in one iteration. Each rule applies from the next iteration onward; the system replays affected components, re-scores, and continues.

`[DRAFT — from novelty analysis E12 for-paper snippet]`
Interactive software clustering [CITE: Bavota2012] and human-in-the-loop clustering more broadly [CITE: Amershi2014; Wagstaff2001; Bae2020] support pairwise constraints and developer feedback. We extend this with (a) a three-mode interaction typology — passive per-iteration review, active inter-iteration rule injection, rare mid-iteration escalation — and (b) a rule taxonomy specific to microservice decomposition, including *policy-as-constraint* domain rules that propagate over many components in a single rule.

### 10.3 Mode 3 — Mid-Iteration Intervention (Escalation)

If the system detects high uncertainty — LLM-judge confidence low across many decisions, contamination oscillating between iterations, redundancy resolutions all hitting “accept” with no clear reason — it pauses and asks the human a specific question. **Not continuous interruption** — only when the system itself is stuck.

### 10.4 Review-Burden Management

`[DRAFT]`
Deltas only, not full clustering. Group changes by microservice. Auto-approve high-confidence; surface borderline. Time-box review (“review for 5 minutes; untouched = auto-approved”). Convergence helper: change volume drops over iterations; review burden decreases toward zero naturally.

-----

## 11. Discussion

### 11.1 Boundaries — What the Method Does NOT Do

`[TODO: a short and honest list. Examples to develop:]`

- Does not produce runtime artefacts (deployment manifests, network policies). Output is a partition + placement + per-component rationale.
- Does not perform automated code transplantation. Splits and moves are recommendations; refactoring is a separate downstream step.
- Does not infer domain hierarchies from scratch with high confidence — the LLM-inferred path is a fallback.
- Does not replace DDD modelling sessions [CITE: Brandolini2018]; it complements them.

### 11.2 Comparison with Closest Prior Work

`[TODO: Table 3 — comparison matrix expanded from Table 1. Columns include: (single-clustering vs population), (interpretable score vs black-box), (multi-trigger), (skeleton-anchored), (whitelisted intentional duplication), (LLM role: feature provider / judge / extractor auditor / off), (HITL modes). Rows: Mono2Micro [CITE: Kalia2021], FoSCI [CITE: Jin2019], CARGO [CITE: Nitin2022], MAGNET [CITE: Trabelsi2024], CHGNN [CITE: Mathai2022], MonoEmbed [CITE: Sellami2025], MicroDec [CITE: Sellami2024], Service Cutter [CITE: Gysel2016], Context Mapper [CITE: Kapferer2020], OURS.]`

### 11.3 Anticipated Reviewer Objections and Responses

`[DRAFT — direct re-use of novelty analysis B4. Sharpen tone for venue submission.]`

**Objection 1: “The LLM judge is unreliable; demoting it to tertiary use does not make it sound.”**
**Response.** The LLM is invoked only when deterministic math is tied or borderline; every override is logged with a whitelisted reason; we ablate by replacing the judge with a coin flip and report degradation. The judge is auditable, not load-bearing — replacing it with a coin flip should produce graceful degradation, not collapse. `[TODO: actually run this ablation.]`

**Objection 2: “The domain skeleton is the user’s; you’ve just moved the hard problem to skeleton design.”**
**Response.** We support LLM-inferred skeletons as fallback [CITE: Shen2022; Meng2020]. Empirically, large organisations have skeletons in hand: BIAN Service Landscape v13.0 [CITE: BIAN2025] defines ~326 service domains in a three-level hierarchy with 250 Semantic APIs; ArchiMate 3.2 [CITE: ArchiMate2022] formalises Motivation-layer elements reusable as a skeleton. The skeleton is a forcing function for stakeholder alignment, not a defect of the method.

**Objection 3: “You replaced a population (Pareto front) with a single solution — you lost diversity.”**
**Response.** The skeleton plus the budgeted iteration already explores a constrained Pareto-frontier surrogate via the three deterministic scores; the audit log and (optional) k-snapshot retention preserves trace diversity for post-hoc analysis. Single-clustering is the right trade for interpretability and human-in-the-loop review — Bavota et al. [CITE: Bavota2012] document the human cost of opaque GA solutions.

**Objection 4: “Triple scoring with three knobs ($w$, IDF, whitelist) is a hyperparameter zoo.”**
**Response.** $w$ defaults to 3 and sensitivity is reported (Section 8.1 TODO); IDF is parameter-free; the whitelist is a closed set of four named reasons each grounded in cited DDD/operational literature. These are interpretable design parameters, not numerical regularizers tuned per-dataset.

**Objection 5: “How do you validate against ground-truth decompositions?”**
**Response.** Standard benchmark set used by CARGO [CITE: Nitin2022] and Mono2Micro [CITE: Kalia2021]: Daytrader, Plants, AcmeAir, JPetStore (and one industrial monolith). We report BCP/ICP/SM/IFN/NED [CITE: Kalia2021], MoJoFM [CITE: TzerposHolt1999], and precision/recall versus ground-truth as MAGNET does; we also report human accept-rate of proposed moves over iterations.

### 11.4 Threats to Validity

`[TODO: standard internal / external / construct / conclusion validity discussion. Internal: LLM non-determinism, addressed via temperature 0 + audit log + replay. External: benchmark applications are small (~30–110 classes); industrial-monolith validation is required. Construct: tags as proxy for domain semantics — addressed via reviewer-burden study. Conclusion: small-N benchmarks limit statistical power.]`

-----

## 12. Evaluation Plan `[TODO entire section]`

### 12.1 Research Questions

`[TODO. Suggested:]`

- RQ1: Does skeleton-anchored decomposition produce architecturally interpretable clusterings (measured via human acceptance rate of moves) compared to embedding-based baselines?
- RQ2: How does triple-score performance compare to Mono2Micro / CARGO / MAGNET on BCP/ICP/SM/IFN/NED and MoJoFM?
- RQ3: What is the fix_extractor : hardcode_patch ratio across applications, and does it improve over LLM-extractor-auditor iterations?
- RQ4: What is the LLM-judge override rate, and what fraction of overrides cite each whitelisted reason?
- RQ5: How does the controlled vocabulary evolve (growth rate, reversion rate)? `[Novelty lever 2 from the novelty analysis.]`
- RQ6: How does human review burden evolve over iterations?
- RQ7: Ablation — replace the LLM judge with a coin flip; what is the degradation?
- RQ8: Sensitivity of $w$ in contamination.
- RQ9: Effect of L3 vs L4 skeleton depth.

### 12.2 Benchmarks

Daytrader, Plants, AcmeAir, JPetStore (109 / 33 / 66 / 82 classes per the CARGO benchmark set [CITE: Nitin2022]) plus one industrial monolith `[TODO: identify partner organisation]`.

### 12.3 Metrics

- BCP, ICP, SM, IFN, NED [CITE: Kalia2021]
- MoJoFM [CITE: TzerposHolt1999]
- Precision / Recall versus ground-truth decomposition (MAGNET-style)
- Human accept-rate of proposed moves over iterations
- fix_extractor : hardcode_patch ratio
- Vocabulary growth and reversion rates
- Review burden (review time per iteration; auto-approve rate)

### 12.4 Baselines

Mono2Micro [CITE: Kalia2021]; FoSCI [CITE: Jin2019]; CARGO [CITE: Nitin2022]; MAGNET [CITE: Trabelsi2024]; MonoEmbed [CITE: Sellami2025]; Service Cutter [CITE: Gysel2016].

### 12.5 Ablations

`[TODO: enumerate. At minimum: (a) LLM judge → coin flip; (b) skeleton → flat cluster space; (c) tag-diversity threshold → class count; (d) three-stage redundancy → Stage 1 only; (e) whitelist → empty whitelist (treat all redundancy as defect).]`

-----

## 13. Conclusion and Future Work

`[TODO: 2-3 paragraphs. Restate: skeleton + triple score + propose/judge/apply + HITL modes. Position as a methodological alternative to embedding-driven decomposition. Future work: (1) automated industrial-monolith partner evaluation; (2) integration with Context Mapper [CITE: Kapferer2020] for downstream contract generation; (3) extension to runtime-trace + static-graph hybrid signals; (4) formal convergence proof; (5) skeleton inference quality study.]`

-----

## 14. Acknowledgments

`[TODO]`

-----

## 15. References

`[Editorial note: ACM Reference Format used as a placeholder; switch to the venue's required style. All entries are drawn from the prior novelty-and-related-work analysis reference pack. Keys correspond to the [CITE: …] markers throughout the paper.]`

### 15.1 Microservice Decomposition

- **[Agarwal2021]** S. Agarwal, R. Sinha, G. Sridhara, P. Das, U. Desai, S. Tamilselvam, A. Singhee, and H. Nakamuro. 2021. Monolith to Microservice Candidates using Business Functionality Inference. *Proc. ICWS 2021*, 758–763. DOI: https://doi.org/10.1109/ICWS53863.2021.00104
- **[Baresi2017]** L. Baresi, M. Garriga, and A. De Renzis. 2017. Microservices Identification through Interface Analysis. *Proc. ESOCC 2017*, LNCS 10465, 19–33. DOI: https://doi.org/10.1007/978-3-319-67262-5_2
- **[Chen2017]** R. Chen, S. Li, and Z. Li. 2017. From Monolith to Microservices: A Dataflow-Driven Approach. *Proc. APSEC 2017*, 466–475. DOI: https://doi.org/10.1109/APSEC.2017.53
- **[Desai2021]** U. Desai, S. Bandyopadhyay, and S. G. Tamilselvam. 2021. Graph Neural Network to Dilute Outliers for Refactoring Monolith Application (CO-GCN). *Proc. AAAI* 35(1), 72–80. DOI: https://doi.org/10.1609/aaai.v35i1.16079
- **[Gysel2016]** M. Gysel, L. Kölbener, W. Giersche, and O. Zimmermann. 2016. Service Cutter: A Systematic Approach to Service Decomposition. *Proc. ESOCC 2016*, LNCS 9846, 185–200. DOI: https://doi.org/10.1007/978-3-319-44482-6_12
- **[Jin2019]** W. Jin, T. Liu, Y. Cai, R. Kazman, R. Mo, and Q. Zheng. 2019. Service Candidate Identification from Monolithic Systems Based on Execution Traces (FoSCI). *IEEE TSE*. DOI: https://doi.org/10.1109/TSE.2019.2910531
- **[Kalia2021]** A. K. Kalia, J. Xiao, R. Krishna, S. Sinha, M. Vukovic, and D. Banerjee. 2021. Mono2Micro: A Practical and Effective Tool for Decomposing Monolithic Java Applications to Microservices. *Proc. ESEC/FSE ’21*, 1214–1224. DOI: https://doi.org/10.1145/3468264.3473915
- **[Kapferer2020]** S. Kapferer and O. Zimmermann. 2020. Domain-driven Service Design — Context Modeling, Model Refactoring and Contract Generation (Context Mapper). *SummerSoC 2020*, CCIS 1310, 189–208. DOI: https://doi.org/10.1007/978-3-030-64846-6_11
- **[Levcovitz2016]** A. Levcovitz, R. Terra, and M. T. Valente. 2016. Towards a Technique for Extracting Microservices from Monolithic Enterprise Systems. arXiv:1605.03175
- **[Mathai2022]** A. Mathai, S. Bandyopadhyay, U. Desai, and S. G. Tamilselvam. 2022. Monolith to Microservices: Representing Application Software through Heterogeneous Graph Neural Network (CHGNN). *Proc. IJCAI-22*, 3905–3911. DOI: https://doi.org/10.24963/ijcai.2022/542
- **[Mazlami2017]** G. Mazlami, J. Cito, and P. Leitner. 2017. Extraction of Microservices from Monolithic Software Architectures. *Proc. ICWS 2017*, 524–531. DOI: https://doi.org/10.1109/ICWS.2017.61
- **[Nitin2022]** V. Nitin, S. Asthana, B. Ray, and R. Krishna. 2022. CARGO: AI-Guided Dependency Analysis for Migrating Monolithic Applications to Microservices Architecture. *Proc. ASE ’22*, Article 20, 12 pp. DOI: https://doi.org/10.1145/3551349.3556960
- **[Romani2022]** Y. Romani, O. Tibermacine, and C. Tibermacine. 2022. Towards Migrating Legacy Software Systems to Microservice-based Architectures: A Data-Centric Process for Microservice Identification. *Proc. ICSA-C 2022*, 15–19.
- **[Sellami2024]** K. Sellami et al. 2024. MicroDec: Leveraging Large Language Models for Microservice Decomposition. ResearchGate preprint. https://www.researchgate.net/publication/386345028
- **[Sellami2025]** K. Sellami and M. A. Saied. 2025. MonoEmbed: Enhancing LLM Representations for Monolith to Microservices Decomposition through Contrastive Learning. *Empirical Software Engineering* 31, Article 11. DOI: https://doi.org/10.1007/s10664-025-10732-z
- **[Taibi2019]** D. Taibi and K. Systä. 2019. From Monolithic Systems to Microservices: A Decomposition Framework based on Process Mining. *CLOSER 2019*. DOI: https://doi.org/10.5220/0007755901530164
- **[Trabelsi2024]** I. Trabelsi et al. 2024. MAGNET: Method-based Approach using Graph Neural Network for Microservices Identification. *Proc. ICSA 2024*, Research Papers Track.

### 15.2 Search-Based and Evolutionary Software Engineering

- **[Harman2002]** M. Harman, R. Hierons, and M. Proctor. 2002. A New Representation and Crossover Operator for Search-Based Optimization of Software Modularization. *Proc. GECCO 2002*, 1351–1358.
- **[Mahdavi2003]** K. Mahdavi, M. Harman, and R. M. Hierons. 2003. A Multiple Hill Climbing Approach to Software Module Clustering. *Proc. ICSM 2003*, 315–324. DOI: https://doi.org/10.1109/ICSM.2003.1235437
- **[Mancoridis1998]** S. Mancoridis, B. S. Mitchell, C. Rorres, Y.-F. Chen, and E. R. Gansner. 1998. Using Automatic Clustering to Produce High-Level System Organizations of Source Code. *Proc. IWPC 1998*, 45–52. DOI: https://doi.org/10.1109/WPC.1998.693283
- **[Mancoridis1999]** S. Mancoridis, B. S. Mitchell, Y.-F. Chen, and E. R. Gansner. 1999. Bunch: A Clustering Tool for the Recovery and Maintenance of Software System Structures. *Proc. ICSM 1999*, 50–59. DOI: https://doi.org/10.1109/ICSM.1999.792498
- **[Mitchell2006]** B. S. Mitchell and S. Mancoridis. 2006. On the Automatic Modularization of Software Systems Using the Bunch Tool. *IEEE TSE* 32(3), 193–208. DOI: https://doi.org/10.1109/TSE.2006.31
- **[Mitchell2008]** B. S. Mitchell and S. Mancoridis. 2008. On the Evaluation of the Bunch Search-Based Software Modularization Algorithm. *Soft Computing* 12(1), 77–93. DOI: https://doi.org/10.1007/s00500-007-0218-3
- **[Praditwong2011]** K. Praditwong, M. Harman, and X. Yao. 2011. Software Module Clustering as a Multi-Objective Search Problem. *IEEE TSE* 37(2), 264–282. DOI: https://doi.org/10.1109/TSE.2010.26

### 15.3 Constrained, Seeded, and Hierarchical Clustering

- **[Bae2017]** J. Bae et al. 2017. A Method to Accelerate Human-in-the-Loop Clustering. *Proc. SIAM SDM 2017*.
- **[Bae2020]** J. Bae et al. 2020. Interactive Clustering: A Comprehensive Review. *ACM CSUR* 53(1), Article 4. DOI: https://doi.org/10.1145/3340960
- **[Basu2002]** S. Basu, A. Banerjee, and R. J. Mooney. 2002. Semi-supervised Clustering by Seeding. *Proc. ICML 2002*, 19–26.
- **[Basu2004]** S. Basu, M. Bilenko, and R. J. Mooney. 2004. A Probabilistic Framework for Semi-Supervised Clustering. *Proc. KDD 2004*, 59–68. DOI: https://doi.org/10.1145/1014052.1014062
- **[Chatziafratis2018]** V. Chatziafratis, R. Niazadeh, and M. Charikar. 2018. Hierarchical Clustering with Structural Constraints. *Proc. ICML 2018*, PMLR 80, 774–783.
- **[Davidson2005]** I. Davidson and S. S. Ravi. 2005. Clustering With Constraints: Feasibility Issues and the K-Means Algorithm. *Proc. SDM 2005*. DOI: https://doi.org/10.1137/1.9781611972757.13
- **[GonzalezAlmagro2024]** G. González-Almagro et al. 2024. Semi-supervised Constrained Clustering: An In-depth Overview, Ranked Taxonomy and Future Research Directions. *AI Review* 57. DOI: https://doi.org/10.1007/s10462-024-11103-8
- **[Ma2018]** X. Ma, L. Dhulipala, and K. Konwar. 2018. Hierarchical Clustering with Prior Knowledge. arXiv:1806.03432
- **[Meng2020]** Y. Meng, Y. Zhang, J. Huang, Y. Zhang, C. Zhang, and J. Han. 2020. Hierarchical Topic Mining via Joint Spherical Tree and Text Embedding. *Proc. KDD 2020*, 1908–1917. DOI: https://doi.org/10.1145/3394486.3403242
- **[Settles2009]** B. Settles. 2009. Active Learning Literature Survey. CS Tech Report 1648, Univ. Wisconsin–Madison.
- **[Shen2022]** J. Shen, Z. Wu, D. Lei, J. Shang, X. Ren, and J. Han. 2022. Seeded Hierarchical Clustering for Expert-Crafted Taxonomies (HierSeed). arXiv:2205.11602
- **[Vikram2016]** S. Vikram and S. Dasgupta. 2016. Interactive Bayesian Hierarchical Clustering. *Proc. ICML 2016*, PMLR 48, 2081–2090.
- **[Wagstaff2001]** K. Wagstaff, C. Cardie, S. Rogers, and S. Schroedl. 2001. Constrained K-means Clustering with Background Knowledge. *Proc. ICML 2001*, 577–584.

### 15.4 Hierarchical Classification and Tree Distance

- **[Bertinetto2020]** L. Bertinetto, R. Mueller, K. Tertikas, S. Samangooei, and N. A. Lord. 2020. Making Better Mistakes: Leveraging Class Hierarchies with Deep Networks. *Proc. CVPR 2020*, 12506–12515. DOI: https://doi.org/10.1109/CVPR42600.2020.01252
- **[CesaBianchi2006]** N. Cesa-Bianchi, C. Gentile, and L. Zaniboni. 2006. Incremental Algorithms for Hierarchical Classification. *JMLR* 7, 31–54.
- **[Kosmopoulos2015]** A. Kosmopoulos, I. Partalas, E. Gaussier, G. Paliouras, and I. Androutsopoulos. 2015. Evaluation Measures for Hierarchical Classification: A Unified View and Novel Approaches. *DMKD* 29(3), 820–865. DOI: https://doi.org/10.1007/s10618-014-0382-x
- **[SaltonBuckley1988]** G. Salton and C. Buckley. 1988. Term-Weighting Approaches in Automatic Text Retrieval. *Information Processing & Management* 24(5), 513–523. DOI: https://doi.org/10.1016/0306-4573(88)90021-0
- **[Silla2011]** C. N. Silla Jr. and A. A. Freitas. 2011. A Survey of Hierarchical Classification across Different Application Domains. *DMKD* 22(1–2), 31–72. DOI: https://doi.org/10.1007/s10618-010-0175-9
- **[Tai1979]** K.-C. Tai. 1979. The Tree-to-Tree Correction Problem. *JACM* 26(3), 422–433. DOI: https://doi.org/10.1145/322139.322143
- **[ZhangShasha1989]** K. Zhang and D. Shasha. 1989. Simple Fast Algorithms for the Editing Distance between Trees and Related Problems. *SIAM J. Computing* 18(6), 1245–1262. DOI: https://doi.org/10.1137/0218082

### 15.5 LLM for Software Engineering

- **[He2025]** J. He, J. Shi, T. Y. Zhuo, C. Treude, J. Sun, Z. Xing, X. Du, and D. Lo. 2025. From Code to Courtroom: LLMs as the New Software Judges. arXiv:2503.02246
- **[Hou2024]** X. Hou et al. 2024. Large Language Models for Software Engineering: A Systematic Literature Review. *ACM TOSEM*. DOI: https://doi.org/10.1145/3695988
- **[Iyer2016]** S. Iyer, I. Konstas, A. Cheung, and L. Zettlemoyer. 2016. Summarizing Source Code Using a Neural Attention Model. *Proc. ACL 2016*, 2073–2083. DOI: https://doi.org/10.18653/v1/P16-1195
- **[Wang2025]** J. Wang, Y. Huang, C. Chen, Z. Liu, S. Wang, and Q. Wang. 2025. Can LLMs Replace Human Evaluators? An Empirical Study of LLM-as-a-Judge in Software Engineering. arXiv:2502.06193

### 15.6 Cross-Cutting Concerns and Clone Detection

- **[Kiczales1997]** G. Kiczales, J. Lamping, A. Mendhekar, C. Maeda, C. V. Lopes, J.-M. Loingtier, and J. Irwin. 1997. Aspect-Oriented Programming. *Proc. ECOOP 1997*, LNCS 1241, 220–242. DOI: https://doi.org/10.1007/BFb0053381
- **[Marin2007]** M. Marin, A. van Deursen, and L. Moonen. 2007. Identifying Crosscutting Concerns Using Fan-in Analysis. *ACM TOSEM* 17(1), Article 3, 37 pp. DOI: https://doi.org/10.1145/1314493.1314496
- **[Robillard2007]** M. P. Robillard and G. C. Murphy. 2007. Representing Concerns in Source Code. *ACM TOSEM* 16(1), Article 3. DOI: https://doi.org/10.1145/1189748.1189751
- **[RoyCordy2009]** C. K. Roy, J. R. Cordy, and R. Koschke. 2009. Comparison and Evaluation of Code Clone Detection Techniques and Tools: A Qualitative Approach. *Science of Computer Programming* 74(7), 470–495. DOI: https://doi.org/10.1016/j.scico.2009.02.007
- **[Sajnani2016]** H. Sajnani, V. Saini, J. Svajlenko, C. K. Roy, and C. V. Lopes. 2016. SourcererCC: Scaling Code Clone Detection to Big-Code. *Proc. ICSE 2016*, 1157–1168. DOI: https://doi.org/10.1145/2884781.2884877
- **[Tsantalis2009]** N. Tsantalis and A. Chatzigeorgiou. 2009. Identification of Move Method Refactoring Opportunities. *IEEE TSE* 35(3), 347–367. DOI: https://doi.org/10.1109/TSE.2009.1
- **[White2016]** M. White, M. Tufano, C. Vendome, and D. Poshyvanyk. 2016. Deep Learning Code Fragments for Code Clone Detection. *Proc. ASE 2016*, 87–98. DOI: https://doi.org/10.1145/2970276.2970326

### 15.7 Domain-Driven Design and Use Cases

- **[Brandolini2018]** A. Brandolini. 2018. *Introducing EventStorming.* Leanpub.
- **[Evans2003]** E. Evans. 2003. *Domain-Driven Design: Tackling Complexity in the Heart of Software.* Addison-Wesley. ISBN 0-321-12521-5.
- **[Jacobson1992]** I. Jacobson, M. Christerson, P. Jonsson, and G. Övergaard. 1992. *Object-Oriented Software Engineering: A Use Case Driven Approach.* ACM Press / Addison-Wesley. ISBN 0-201-54435-0.
- **[Mernik2005]** M. Mernik, J. Heering, and A. M. Sloane. 2005. When and How to Develop Domain-Specific Languages. *ACM CSUR* 37(4), 316–344. DOI: https://doi.org/10.1145/1118890.1118892
- **[Newman2015]** S. Newman. 2015 / 2021. *Building Microservices: Designing Fine-Grained Systems* (1st / 2nd ed.). O’Reilly.
- **[Vernon2013]** V. Vernon. 2013. *Implementing Domain-Driven Design.* Addison-Wesley. ISBN 0-321-83457-7.
- **[Vernon2016]** V. Vernon. 2016. *Domain-Driven Design Distilled.* Addison-Wesley. ISBN 0-13-443442-1.

### 15.8 Semantic Web Services

- **[Martin2004]** D. Martin et al. 2004. OWL-S: Semantic Markup for Web Services. W3C Member Submission. https://www.w3.org/submissions/2004/SUBM-OWL-S-20041122/
- **[Roman2005]** D. Roman, U. Keller, H. Lausen, J. de Bruijn, R. Lara, M. Stollberg, A. Polleres, C. Feier, C. Bussler, and D. Fensel. 2005. Web Service Modeling Ontology. *Applied Ontology* 1(1), 77–106.

### 15.9 Human-in-the-Loop / Interactive ML

- **[Amershi2014]** S. Amershi, M. Cakmak, W. B. Knox, and T. Kulesza. 2014. Power to the People: The Role of Humans in Interactive Machine Learning. *AI Magazine* 35(4), 105–120. DOI: https://doi.org/10.1609/aimag.v35i4.2513
- **[Bavota2012]** G. Bavota, F. Carnevale, A. De Lucia, M. Di Penta, and R. Oliveto. 2012. Putting the Developer in-the-Loop: An Interactive GA for Software Re-Modularization. *Proc. SSBSE 2012*, LNCS 7515, 75–89. DOI: https://doi.org/10.1007/978-3-642-33119-0_7
- **[TzerposHolt1999]** V. Tzerpos and R. C. Holt. 1999. MoJo: A Distance Metric for Software Clusterings. *Proc. WCRE 1999*, 187–193. DOI: https://doi.org/10.1109/WCRE.1999.806959

### 15.10 Enterprise Domain Catalogs

- **[ArchiMate2022]** The Open Group. 2022. *ArchiMate® 3.2 Specification.* Document C226. ISBN 1-957866-02-4.
- **[BIAN2025]** BIAN e.V. 2025. *BIAN Service Landscape v13.0.* Banking Industry Architecture Network.

-----

## Appendix A — Open Design Questions `[carry-over from idea collection]`

Reproduced for the design team; trim or move to a separate technical report before submission.

- **Microservice-level hierarchy depth.** L3 vs L4. Provisionally L4; ablate (RQ9).
- **Flat vs. hierarchical refinement loop.** Whether sub-iteration within each L1 subtree is needed before cross-L1 moves.
- **Termination criterion thresholds.** Contamination floor, coherence-plateau window K, max iterations.
- **Per-iteration budget values.** Specific K (microservices), M (moves), one-split-one-merge — confirm or tune.
- **Tag tree-edit-distance weighting $w$.** Default 3.
- **Candidate-destination top-K size** for trie lookup. Default 3–5.
- **Tag-diversity thresholds** N (L1) and M (L2).
- **Functional-duplication similarity threshold** for Stage 3 redundancy.
- **Redundancy threshold for lift-to-shared** — minimum copy count K.
- **Unified vs. separate inventories** across the five controlled vocabularies.
- **Default review mode.** Silent batch vs. interactive.
- **Action-point splitting mechanism** when a chain crosses microservice boundaries (aggregator vs sub-flow split).
- **Mid-tier naming.** “business logic tier” / “application tier” / “processing layer”.
- **LLM-inferred vs. user-supplied skeleton merging** when both partially available.
- **Whitelisted override-reason completeness.** When should new reasons be added vs forced into existing categories?

-----

## Appendix B — Mapping from Idea Collection Sections to Paper Sections `[for the authors only]`

|Idea collection §                  |Paper §                          |
|-----------------------------------|---------------------------------|
|1. Core Premise                    |1.1, 3.1                         |
|2. Three-Layer Component Extraction|4.1                              |
|3. Action Points                   |4.2                              |
|4. Chain Extraction                |4.3                              |
|5. Graph Hardening                 |4.4                              |
|6. Cross-Cutting Detection         |4.5                              |
|7. Service Summarization & Tagging |5.1, 5.2, 5.3                    |
|8. Data-Source Tagging             |5.4                              |
|9. Microservice-Level Hierarchy    |6                                |
|10. Controlled Vocabularies        |5.5                              |
|11. First Iteration                |7.1                              |
|12. Cascading Assignment           |7.2, 7.3, 7.4                    |
|13. Scoring                        |8.1, 8.2, 8.4, 8.5               |
|14. Redundancy                     |8.3                              |
|15. Top-Down / Bottom-Up Coherence |8.2 (folded in)                  |
|16. Human-Preference Signals       |10 (forced-together/anchors); 9.3|
|17. Position on Chains             |4.3 (folded in)                  |
|18. Iterative Refinement           |9                                |
|19. Human-in-the-Loop              |10                               |
|20. Open Questions                 |Appendix A                       |

-----

*End of scaffolding draft v0.1. Next iteration: tighten Section 1, write Section 11.4 (threats), draft Section 12 (evaluation plan) with concrete RQ-to-metric mapping, draft pseudocode/algorithms blocks in Sections 4.4 / 7.2 / 9.2, produce Figure 1 (pipeline) and Tables 1/2/3.*