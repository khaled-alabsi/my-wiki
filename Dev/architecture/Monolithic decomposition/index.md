# Dev/architecture/Monolithic Decomposition - Index

> Navigation map for agents: match what you are looking for, or what you want to add, against the
> one-line descriptions below, then open that file.
> Keep this current: run the `wiki` skill in `refresh` mode after adding, moving, or removing notes.
> A refresh only re-describes what changed.

## Business Glossary

> Method and metric names local to this research folder, additional to the root and `Dev/`
> glossaries. Every definition comes from a note here; `Paper/Archive/` was not read.

**Methods**

- **CARGO** — Nitin et al., ASE '22. AI-guided dependency analysis: a flow-sensitive system dependency graph that includes DB tables. Source of the standard benchmark set. → `Paper/Novelty Analysis of a Domain-Hierarchy-Anchored Monolith-to-Microservice Decomposition Method.md`
- **CHGNN** — Mathai et al., IJCAI-22. Heterogeneous graph neural network over program plus resource nodes. → `Paper/Novelty Analysis of a Domain-Hierarchy-Anchored Monolith-to-Microservice Decomposition Method.md`
- **FoSCI** — Jin et al., IEEE TSE 2019: *Service Candidate Identification from Monolithic Systems Based on Execution Traces*. Three-step "atom → cluster" pipeline over execution traces; the source of the SM/IFN/IPC/NED objective family. → `SEMA-GA vs. MonoEmbed.md`
- **IBEA** — indicator-based evolutionary algorithm, used by MSExtractor for cohesive, loosely coupled, coarse-grained services. → `Genetic Algorithms for Automated Monolith Decomposition.md`
- **MAGNET** — Trabelsi et al. 2024. Static-call-graph-based decomposition; reports precision/recall against ground truth. → `Paper/Novelty Analysis of a Domain-Hierarchy-Anchored Monolith-to-Microservice Decomposition Method.md`
- **MicroDec** — embedding-based decomposition method, compared step by step against MonoEmbed. → `Known methods/MonoEmbed vs MicroDec — Step-by-Step Comparison.md`
- **Mono2Micro** — Kalia et al., ESEC/FSE '21 (IBM). Hierarchical decomposition driven by runtime traces collected under specific business use cases. Source of the BCP/ICP/SM/IFN/NED metric set. → `Paper/Novelty Analysis of a Domain-Hierarchy-Anchored Monolith-to-Microservice Decomposition Method.md`
- **MonoEmbed** — Sellami & Saied, EMSE 2025. Clusters monolithic components using LLM-derived code embeddings with contrastive learning; no explicit architecture constraints, no extractor validation loop. → `SEMA-GA vs. MonoEmbed.md`
- **MSExtractor** — evolutionary service-extraction method (Sellami et al., 2022), run with IBEA. → `Known methods/NSGA-II vs MSExtractor.md`
- **NSGA-II** — the multi-objective genetic algorithm machinery this research builds on: fast non-dominated sorting into Pareto fronts, plus crowding distance to keep spread along each front. → `Known methods/NSGA-II.md`
- **SEMA-GA** — the vault owner's own 2025 method. A typed attributed multi-graph (role type, semantic embedding, trace-weighted edges) evolved under a *five*-objective vector: SM, IFN, IPC, NED, plus an LLM-as-Pareto-critic. Keeps NSGA-II's non-dominated sort but adds semantic niching in embedding space to counter LLM mode collapse. → `SEMA-GA vs. MonoEmbed.md`
- **So4MoD** — Security-Optimized approach for Microservice-Oriented Decomposition. → `Known methods/So4MoD.md`

**Metrics**

- **BCP, ICP** — two of the Mono2Micro metrics this work reports; **undefined in the vault**, named only in the metric list at `Paper/Novelty Analysis of a Domain-Hierarchy-Anchored Monolith-to-Microservice Decomposition Method.md`.
- **IFN** — interface number. Objective 2 of the numerical four. → `SEMA-GA vs. MonoEmbed.md`
- **IPC** — inter-partition calls / inter-partition communication. Objective 3. → `SEMA-GA vs. MonoEmbed.md`
- **MoJoFM** — Tzerpos & Holt 1999. Similarity of a produced decomposition to a reference/ground-truth one. → `Genetic Algorithms for Automated Monolith Decomposition.md`
- **NED** — non-extreme distribution. Objective 4; penalises partitions that are extremely large or extremely small. → `SEMA-GA vs. MonoEmbed.md`
- **SM** — structural modularity. Objective 1 of the numerical four. → `SEMA-GA vs. MonoEmbed.md`

**Benchmarks**

- **Daytrader, Plants, AcmeAir, JPetStore** — the standard Java EE benchmark applications used by CARGO and Mono2Micro for ground-truth validation. → `Paper/Novelty Analysis of a Domain-Hierarchy-Anchored Monolith-to-Microservice Decomposition Method.md`

## Contents

- `Dev/architecture/Monolithic decomposition/Known methods/` - known monolith-to-microservice decomposition methods compared and documented
- `Dev/architecture/Monolithic decomposition/Paper/` - paper scaffolding, novelty analysis, idea collection, planning for domain-hierarchy-anchored decomposition research
- `Dev/architecture/Monolithic decomposition/Genetic Algorithms for Automated Monolith Decomposition.md` - genetic algorithms for automated monolith decomposition into frontend, backend, and API services
- `Dev/architecture/Monolithic decomposition/SEMA-GA vs. MonoEmbed.md` - SEMA-GA (2025) vs. MonoEmbed (2021) stepwise comparison

## Dev/architecture/Monolithic decomposition/Known methods/

- Place here: known monolith-to-microservice decomposition methods — NSGA-II, So4MoD, MonoEmbed, MicroDec, MSExtractor — with step-by-step comparisons.
- `Dev/architecture/Monolithic decomposition/Known methods/MonoEmbed vs MicroDec — Step-by-Step Comparison.md` - MonoEmbed vs MicroDec compared step by step
- `Dev/architecture/Monolithic decomposition/Known methods/NSGA-II vs MSExtractor.md` - NSGA-II vs MSExtractor step-by-step comparison
- `Dev/architecture/Monolithic decomposition/Known methods/NSGA-II.md` - full NSGA-II algorithm documented with every step in detail
- `Dev/architecture/Monolithic decomposition/Known methods/So4MoD.md` - So4MoD: Security-Optimized approach for Microservice-Oriented Decomposition

## Dev/architecture/Monolithic decomposition/Paper/

- Place here: paper scaffolding, novelty analysis, idea collection, and planning for domain-hierarchy-anchored monolith-to-microservice decomposition research.
- `Dev/architecture/Monolithic decomposition/Paper/HOW TO PLAN.md` - planning guide for the decomposition paper
- `Dev/architecture/Monolithic decomposition/Paper/Novelty Analysis of a Domain-Hierarchy-Anchored Monolith-to-Microservice Decomposition Method.md` - novelty and related-work analysis for the consolidated decomposition method
- `Dev/architecture/Monolithic decomposition/Paper/method-idea-consolidated.md` - monolith-to-microservice decomposition method idea collection
- `Dev/architecture/Monolithic decomposition/Paper/plan phases.md` - paper planning: phases mapped to paper sections
- `Dev/architecture/Monolithic decomposition/Paper/Archive/22 Monolith-to-Microservice Decomposition Methods.md` - research report covering 22 monolith-to-microservice decomposition methods for SEMA-GA paper
- `Dev/architecture/Monolithic decomposition/Paper/Archive/Novelty Analysis of Seven New Elements in Monolith-to-Microservice Decomposition Method.md` - novelty and related-work analysis: 7 new elements of the decomposition method
- `Dev/architecture/Monolithic decomposition/Paper/Archive/domain-skeleton-decomposition-implementation-benchmark-plan.md` - implementation and benchmark plan for domain-skeleton microservice decomposition paper
- `Dev/architecture/Monolithic decomposition/Paper/Archive/domain-skeleton-microservice-decomposition-paper-scaffold.md` - domain-skeleton-constrained monolith-to-microservice decomposition paper scaffold
- `Dev/architecture/Monolithic decomposition/Paper/Archive/method-idea-consolidated.md` - monolith-to-microservice decomposition method idea collection (archive copy)
- `Dev/architecture/Monolithic decomposition/Paper/Archive/method-idea-consolidated2.md` - monolith-to-microservice decomposition method idea collection (second archive copy)
- `Dev/architecture/Monolithic decomposition/Paper/Archive/scaffolding paper v0_1.md` - scaffolding paper: domain-hierarchy-anchored decomposition of monolithic applications into microservices
