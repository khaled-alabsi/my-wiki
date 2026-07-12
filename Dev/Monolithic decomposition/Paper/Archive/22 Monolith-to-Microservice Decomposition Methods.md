# Research Report: 22 Monolith-to-Microservice Decomposition Methods for SEMA-GA Paper

This report provides the source-cited factual basis for assembling the user’s deliverable (summary matrix + 22 pipeline cards + capability heatmap + family clustering view + novelty summary). Findings are organized by family.

## 0. Critical corrections to the user’s task brief

Five items require correction before assembling the final artifact:

1. **MicroDec authors**: Actual authors are **Ahmed Saeed Alsayed, Hoa Khanh Dam, Chau Nguyen**  (University of Wollongong, preprint Dec 2024) — *not* “Alsayed & Benomar”. No “Benomar”-authored MicroDec paper exists.
2. **CO-GCN expansion**: The published expansion in Desai et al. 2021 (AAAI) is **“Clustering and Outlier-aware Graph Convolutional Network”** — *not* “Constraint-Oriented GCN”. The “constraints” framing appears only in a related IBM patent.
3. **SEMA-GA**: A thorough web/arXiv/Google Scholar search returns **zero hits** for “SEMA-GA”, “Semantically Mediated Adaptive Genetic Algorithm”, “LLM-inside-GA microservice”, or “semantic crossover NSGA microservice”. SEMA-GA is genuinely new — the user is authoring it. Pipeline reconstruction below is grounded in the task description and verified against parent methods.
4. **SRME**: The exact acronym “SRME = Sub-Requirement-based Microservice Extraction” was **not verifiable** in DBLP/IEEE/ACM/arXiv. Closest primary source is **Bu, Xiao, Li & Xie (REW 2024)** — “A Microservice Decomposition Approach Driven by Sub-Requirement References in Problem Diagrams”,   extending their earlier **PF4Microservices** (arXiv:2207.04586, 2022). Treat as SRME but flag the acronym for user confirmation.
5. **CHM**: Canonical expansion in Jin et al. (FoSCI/TSE) is **“Cohesion at Message level”**  (operations’ messages), not “Method level” — downstream papers paraphrase. Pick one and footnote.

-----

## 1. Verified acronyms (with primary citations)

|Acronym      |Verified expansion                                                                  |Primary citation                                                 |
|-------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------|
|**NSGA-II**  |Non-dominated Sorting Genetic Algorithm II                                          |Deb, Pratap, Agarwal, Meyarivan,  *IEEE TEVC* 6(2), 2002         |
|**NSGA-III** |(Reference-Point-Based Many-Objective) Non-dominated Sorting Genetic Algorithm III  |Deb & Jain, *IEEE TEVC* 18(4), 2014                              |
|**IBEA**     |Indicator-Based Evolutionary Algorithm                                              |Zitzler & Künzli, PPSN VIII, LNCS 3242, 2004                     |
|**LoRA**     |Low-Rank Adaptation                                                                 |Hu et al., arXiv:2106.09685  / ICLR 2022                         |
|**CARGO**    |Context-sensitive lAbel pRopaGatiOn                                                 |Nitin et al., ASE 2022,  arXiv:2207.11784                        |
|**MAGNET**   |Method-based Approach using Graph Neural Network (for microservices identification) |Trabelsi, Moha, Guéhéneuc, Geffard, ICSA 2024                    |
|**CO-GCN**   |**Clustering and Outlier-aware Graph Convolutional Network** (correction)           |Desai, Bandyopadhyay, Tamilselvam, AAAI 2021,   arXiv:2102.03827 |
|**SEMGROMI** |SEmantic GROuping for MIcroservice identification (algorithm)                       |Vera-Rivera et al., *PeerJ CS* 9:e1380, 2023                     |
|**DDD**      |Domain-Driven Design                                                                |Evans, Addison-Wesley, 2003                                      |
|**CML**      |Context Mapper Language (DSL)                                                       |Kapferer & Zimmermann, MODELSWARD 2020                           |
|**SRME**     |*Unverified*; closest: “Sub-Requirement References in Problem Diagrams”             |Bu et al., REW 2024 (10.1109/REW61692.2024.00031)                |
|**DQN**      |Deep Q-Network                                                                      |Mnih et al., *Nature* 518, 2015                                  |
|**CodeBERT** |Bimodal pre-trained model for programming and natural languages                     |Feng et al., EMNLP 2020 Findings,  arXiv:2002.08155              |
|**LLM2Vec**  |LLM-to-Vector (decoder LLMs as text encoders)                                       |BehnamGhader et al., COLM 2024,  arXiv:2404.05961                |
|**CHM**      |Cohesion at Message level                                                           |Jin et al., FoSCI / *IEEE TSE* 2021                              |
|**CHD**      |Cohesion at Domain level                                                            |Jin et al., FoSCI / *IEEE TSE* 2021                              |
|**CBM**      |Coupling Between Microservices                                                      |Taibi & Systä, CLOSER 2019                                       |
|**SMQ / CMQ**|Structural / Conceptual Modularity Quality                                          |Jin et al., FoSCI (derived from Mancoridis Bunch MQ)             |
|**IFN / OPN**|Interface Number / OPeration Number                                                 |Jin et al., FoSCI                                                |
|**NED**      |Non-Extreme Distribution                                                            |Wu et al.; popularized via a-BMSC and surveys                    |
|**BCP / ICP**|Business Context Purity / Inter-Call Percentage                                     |Kalia et al., Mono2Micro, ESEC/FSE 2021                          |

-----

## 2. Summary matrix data (one row per method)

|# |Method                                                                                               |Family                              |Input signal                                 |Core technique (1 line)                                                                                                                                             |LLM role                        |Search type                             |Objectives                                                       |Output type          |Typed comps                                   |Feedback                      |DDD                                   |
|--|-----------------------------------------------------------------------------------------------------|------------------------------------|---------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|----------------------------------------|-----------------------------------------------------------------|---------------------|----------------------------------------------|------------------------------|--------------------------------------|
|1 |MonoEmbed (Sellami & Saied, EMSE 2026)                                                               |LLM-only                            |Static + Semantic                            |Triplet-contrastive LoRA fine-tune of LLM2Vec/Llama-3, then Affinity Propagation clustering                                                                         |Encoder                         |None (single-shot)                      |Single (aggregate SCORE)                                         |One                  |No                                            |No (offline training only)    |Partial                               |
|2 |MicroDec (Alsayed, Dam, Nguyen, 2024)                                                                |Hybrid (graph+LLM)                  |Static                                       |Class-dep graph + biased random-walk structural embeddings + CodeBERT/GPT semantic embeddings → K-Means                                                             |Encoder                         |None                                    |Single (best K by multi-metric)                                  |One                  |Partial (handler/API)                         |No                            |No                                    |
|3 |Systematic LLM use (Trabelsi, Moha, Guéhéneuc, ICSOC-W 2024/2025)                                    |LLM-only                            |Semantic / Static                            |Systematic prompt catalog driving an LLM through migration steps (decomposition + pattern integration)                                                              |Proposer + Operator             |Iterative (prompt refinement)           |Single (qualitative)                                             |One                  |Yes (pattern roles)                           |Yes (explicit human)          |Partial                               |
|4 |Pattern-Driven + LLM for ML monoliths (Ghlissi et al., ICSOC 2025)                                   |Hybrid                              |Static + Semantic                            |LLM labels ML-pipeline layers; CodeBERT + HDBSCAN clusters pattern-aware microservice candidates                                                                    |Labeler (+CodeBERT encoder)     |None                                    |Single (cluster quality)                                         |One                  |Yes (ML-layer types)                          |No                            |Partial                               |
|5 |Domain Aligned Microservices (Gandhi et al., ISEC 2025)                                              |Hybrid (DDD+graph+LLM)              |Static + Domain                              |Weighted heterogeneous graph + architect-supplied Domain Description Map (DDM); GPT-4o synthesizes domain descriptions                                              |Labeler                         |None                                    |Multi-objective aggregated (cohesion, coupling, domain alignment)|One                  |Yes (business services)                       |No (proposed future)          |Yes                                   |
|6 |Stojanović & Lazarević (E-business Tech Conf 2023)                                                   |LLM-only                            |Semantic                                     |Direct zero-shot ChatGPT prompting on natural-language requirements                                                                                                 |Proposer                        |None                                    |Single (informal)                                                |One                  |No                                            |No / implicit                 |Partial                               |
|7 |MSExtractor v1 (Saidani et al., ICSOC 2019) / v2 (Sellami et al., IST 2022)                          |GA-only                             |Static (v1) → Static+Semantic (v2)           |Multi-objective NSGA-II (v1) / IBEA (v2) on class-to-service label-vector chromosomes                                                                               |None                            |Population-based                        |Multi-objective Pareto (2 → 3)                                   |Pareto front + knee  |No                                            |No                            |No (Partial in v2)                    |
|8 |FoSCI (Jin et al., *IEEE TSE* 2021)                                                                  |Hybrid (clustering+GA)              |Dynamic (traces) + Semantic                  |Hierarchical-clustering warm-start of Functional Atoms; NSGA-II with 4 struct/conc intra/inter objectives                                                           |None                            |Population-based                        |Pareto (4 objectives)                                            |Pareto front + knee  |No                                            |No                            |No (Partial)                          |
|9 |So4MoD (Liu et al., *JSEP* 2024)                                                                     |GA-only                             |Static (+ data-security signals)             |NSGA-II adding ≥5 data-security metrics to modularity objectives                                                                                                    |None                            |Population-based                        |Pareto (security + modularity)                                   |Pareto front / one   |No                                            |No                            |No                                    |
|10|Microservices Backlog (MB-GA, Vera-Rivera et al., *IEEE Access* 2021) / SEMGROMI (PeerJ CS 2023)     |GA-only (MB) / Clustering (SEMGROMI)|Semantic (user stories)                      |Single-objective GA on binary user-story × microservice assignment matrix;  SEMGROMI replaces GA with semantic-similarity clustering                                |None                            |Population-based (MB); None (SEMGROMI)  |Single (weighted-sum GM of 5 sub-metrics)                        |One best             |No                                            |No (semi-automatic)           |Partial                               |
|11|Service Cutter (Gysel et al., ESOCC 2016)                                                            |DDD + Clustering                    |Hybrid (Semantic + Domain + light Static)    |Weighted graph clustering (Girvan-Newman / Leung / MCL) over nanoentity graph scored by 16 coupling criteria                                                        |None                            |None                                    |Multi-criteria aggregated to weighted score                      |One                  |Yes (nanoentities/services typed)             |No                            |Partial                               |
|12|Mono2Micro (Kalia et al., ESEC/FSE 2021)                                                             |Clustering (dynamic)                |Dynamic + Semantic                           |Hierarchical agglomerative clustering   on spatio-temporal similarity from labeled runtime traces (DCR, DCP, ICR, ICP)                                              |None                            |None / mild iterative (hill-climb for k)|Single combined similarity                                       |One (two flavors)    |No                                            |No                            |Partial                               |
|13|Context Mapper / CML (Kapferer & Zimmermann, MODELSWARD 2020/21)                                     |DDD                                 |Domain + Semantic (+ Static via reverse-eng.)|Typed DDD meta-model + DSL + library of typed Architectural Refactorings (AR-1..AR-11) + optional Service Cutter                                                    |None (LLM-free)                 |Iterative (human-driven AR sequencing)  |Implicit / qualitative                                           |One per run          |Yes (richest type system)                     |Yes (human-in-the-loop)       |Yes                                   |
|14|Domain Aligned (Gandhi et al., ISEC 2025)                                                            |Hybrid (DDD+graph+LLM)              |Static + Domain                              |(same as #5; listed under DDD too)                                                                                                                                  |Labeler                         |None                                    |Multi (aggregated)                                               |One                  |Yes                                           |No                            |Yes                                   |
|15|DDD + static/dynamic (Krause, Zirkelbach, Hasselbring, Lenga, Kröger  — adesso in|FOCUS, ICSA-C 2020)|Hybrid (DDD+code)                   |Domain + Static + Dynamic                    |DDD bounded-context identification refined by Structure101 static maps + ExplorViz dynamic-trace visualization                                                      |None                            |Iterative (multi-pass human)            |Single (qualitative multi-criteria)                              |One                  |Partial (BCs typed)                           |Yes                           |Yes                                   |
|16|SRME — Bu, Xiao, Li, Xie (REW 2024) / PF4Microservices (arXiv:2207.04586, 2022)                      |Other (problem-frame-driven)        |Semantic / Domain (requirements)             |Jackson problem diagrams per requirement, merged by correlation of sub-requirement references and hardware similarity                                               |None                            |None (single-shot deterministic)        |Single (cohesion via shared sub-reqs)                            |One                  |Yes (typed problem-frame domains)             |No                            |Partial                               |
|17|Feature Table (Wei, Yu, Pan, Zhang, Internetware 2020)                                               |Other (artifact-driven)             |Semantic / Domain (features)                 |12 typed Feature Cards + Feature Table + Decomposition Rules + Mapping Rules; semi-automatic tool                                                                   |None                            |None                                    |Multi-criteria aggregated (coupling+cohesion)                    |One                  |Yes (12 Feature Card types)                   |No / weak human-in-loop       |Partial                               |
|18|CARGO (Nitin et al., ASE 2022)                                                                       |Hybrid (LPA + program analysis)     |Static (+ DB transactional edges)            |Context- and flow-sensitive System Dependency Graph; context-sensitive label propagation; reduces distributed transactions                                          |None                            |Iterative (propagation)                 |Single (cohesion/coupling + distributed-txn)                     |One                  |Yes (methods + DB tables)                     |No (implicit)                 |No                                    |
|19|MAGNET (Trabelsi, Moha, Guéhéneuc, Geffard, ICSA 2024)                                               |GNN                                 |Hybrid (Static + Semantic)                   |GCN over method-level KDM dependency graph with Word2Vec semantic node features for unsupervised clustering                                                         |Encoder (Word2Vec — borderline) |Iterative (training + K-sweep)          |Single (composite cohesion/coupling)                             |One                  |No                                            |No                            |No                                    |
|20|CO-GCN (Desai et al., AAAI 2021)                                                                     |GNN                                 |Static (classes + entrypoints + inheritance) |2-layer GCN autoencoder + outlier-aware multi-task loss (L_str + L_att + L_clus) + integrated k-means clustering                                                    |None                            |Iterative (alternating minimization)    |Multi-objective scalarized                                       |One + outlier ranking|No                                            |No                            |No                                    |
|21|RLDec (Sellami & Saied, EMSE 2025)                                                                   |RL                                  |Hybrid (Static + Semantic)                   |DQN agent assigns classes to one of K microservices to maximize structural+semantic quality reward (MDP)                                                            |None                            |Iterative (RL policy improvement)       |Multi-objective scalarized into reward                           |One                  |No                                            |**Yes (RL reward = feedback)**|No                                    |
|22|**SEMA-GA** (target method)                                                                          |**Hybrid (LLM+GA)**                 |Hybrid (Static + Semantic; optional Domain)  |LLM as first-class genetic operator (semantic crossover, reflective mutation, Pareto critic, adaptive op scheduler, semantic niching) inside constrained NSGA-II/III|**Operator + Critic + Proposer**|Population-based                        |Multi-objective Pareto (5–8)                                     |**Pareto front**     |**Yes** (LLM tags Frontend/Backend/API/Worker)|**Yes (explicit reflection)** |Partial (optional CML/DDD constraints)|

-----

## 3. Per-method pipeline cards (8 steps each, with sources)

### 3.1 LLM-based methods

#### Method 1 — MonoEmbed

**Source:** Sellami & Saied, “Contrastive Learning-Enhanced Large Language Models for Monolith-to-Microservice Decomposition,” arXiv:2502.04604 (Feb 2025);  journal version “MonoEmbed,” *Empirical Software Engineering* 31, 11 (2026), DOI 10.1007/s10664-025-10732-z.   Laval University, Québec. 

1. **Input** — Java source code at class-level granularity  (raw class source text). No traces, no DB, no user stories.
2. **Representation** — Dense embedding vector per class via pre-trained or fine-tuned LLM  (best variant: ME-LLM2Vec-340K  based on LLM2Vec/Llama-3-8B). Feature matrix N×M,  z-score normalized.
3. **Seeding** — None (clustering algorithms use their own initialization, e.g., k-means++).
4. **Variation** — None (single-shot; only hyperparameter sweep over clustering algorithms for reporting).
5. **Fitness** — Two-level: (a) internal embedding quality (balanced BCE on pairwise cosine vs. ground-truth co-membership, F_β with β=0.25);  (b) decomposition metrics CHM, CHD, BCP, ICP, NED, COV  and aggregate SCORE = 2·CHM + 2·CHD − 2·BCP − 2·ICP − NED + COV. 
6. **Selection** — None. Affinity Propagation is best (median F_β); K-Means/Hierarchical when K known. 
7. **Output** — One decomposition D = [M₁,…,M_K], disjoint class subsets. 
8. **Feedback** — None at inference. Implicit training-time feedback via triplet-contrastive (FaceNet-style) loss with LoRA fine-tuning  on 340K GitHub-mined triplets — offline only.

**Lineage:** Repr ⊃ MicroMiner (extends CodeBERT → LLM2Vec/Llama-3) — NEW use of 7-8B decoder LLMs as encoders for decomposition.  Seeding ≈ MSExtractor (none). Variation ≈ MicroDec / Mono2Micro (single-shot). Fitness ⊃ CHGNN (aggregate SCORE), ≈ Mono2Micro (BCP, ICP). Output ≈ Mono2Micro / Code2VecDec / MicroDec (one decomposition); ≠ MSExtractor (Pareto). Feedback NEW (offline contrastive loop on synthetic triplets).

#### Method 2 — MicroDec

**Source:** Alsayed, Dam, Nguyen, “MicroDec: Leveraging Large Language Models for Microservice Decomposition,” preprint Dec 2024 (ResearchGate 386345028; University of Wollongong). **Author correction**: not “Alsayed & Benomar”.

1. **Input** — Java/Spring monolithic source code (static analysis via JavaSymbolSolver). Extracts classes, method signatures, handler classes with `@RequestMapping` / `@Controller`. 
2. **Representation** — Graph G(V,E): V = classes, E = method-invocation/dependency edges  (weighted). Two parallel feature streams: (a) biased random walks  (node2vec-style) → structural embeddings; (b) CodeBERT (`microsoft/codebert-base`)  or GPT  → semantic embeddings (MicroDec-BERT vs MicroDec-GPT variants).  Combined per-class vector.
3. **Seeding** — None. Handler classes identified for interface extraction only, not as cluster seeds.
4. **Variation** — None (single-shot). Hyperparameter sweep only over LLM choice and K.
5. **Fitness** — CHM, CHD, IFN (Interface Number), SMQ (Structural Modularity Quality), CMQ (Conceptual Modularity Quality).  Reported, not optimized.
6. **Selection** — None / single-best K-Means; best K chosen by metric performance. 
7. **Output** — One decomposition (K service candidates SC₁..SC_K).
8. **Feedback** — None.

**Lineage:** Repr ⊃ MAGNET (adds LLM semantics to graph approach); NEW: biased-random-walk structural embeddings combined with LLM textual embeddings. Fitness ≈ FoSCI / MAGNET (CHM, CHD, SMQ, CMQ). Output ≈ MonoEmbed / Mono2Micro (one). All single-shot.

Baselines compared: Topic Modeling, MAGNET.  MicroDec-BERT beats baselines by ~29-41% on CHM-related metrics (75 wins at P<0.001). 

#### Method 3 — Systematic LLM use

**Source:** Trabelsi, Moha, Guéhéneuc, “Exploring the Systematic Use of LLMs for Microservices Generation,” ICSOC 2024 Workshops, LNCS 15833, pp. 121–128 (online Jul 2025), DOI 10.1007/978-981-96-7238-7_10. 

1. **Input** — Monolithic source code (key classes/methods + dependencies) + NL requirements. Validated on Spring PetClinic. 
2. **Representation** — Prompt (text); code fed as snippets.
3. **Seeding** — Heuristic — architect identifies key classes/methods to seed prompts (phased approach). 
4. **Variation** — Iterative prompt refinement; operator re-edits prompts after observing output. 
5. **Fitness** — Qualitative human assessment (pattern adherence, API coverage, dependency preservation). No metric.
6. **Selection** — None.
7. **Output** — One decomposition with generated microservices + APIs + integrated patterns (API Gateway, Circuit Breaker, Service Registry). 
8. **Feedback** — Explicit (developer-in-the-loop reflection, continuous prompt refinement). 

**Lineage:** Repr NEW (prompt text). Variation NEW (prompt re-engineering, no formal population). Output ≈ Mono2Micro (single). Feedback ⊃ Context Mapper (interactive). LLM role: Proposer + Operator.

#### Method 4 — Pattern-Driven + LLM for ML monoliths

**Source:** Ghlissi, Boukhatem, Abdellatif, Moha  (ÉTS), “A Pattern-Driven and LLM-Assisted Approach for Decomposing Monolithic ML-Based Systems into Microservices,” ICSOC 2025, LNCS  16320, pp. 221–229 (online Jan 2026), DOI 10.1007/978-981-95-5012-8_16.  Code: github.com/HakimGhlissi/AIDecompose-ML-Monolith-Decomposition-Approach.

1. **Input** — Source code of ML-based monolithic systems (TextAnalyzer, Asparagus, etc.).
2. **Representation** — (a) LLM prompt (via Groq console) tags classes/methods into ML layers; (b) CodeBERT transformer embeddings of code units.
3. **Seeding** — Heuristic — ML architectural patterns (Yokoyama 2019, Washizaki 2022) act as a-priori category seeds; LLM tags into these layers.
4. **Variation** — None (single-shot LLM labeling + single HDBSCAN pass).
5. **Fitness** — Implicit cluster cohesion/coupling via HDBSCAN density; external precision/recall vs ground truth (84% / 65% on 3 ML monoliths). 
6. **Selection** — None.
7. **Output** — One decomposition (clusters tagged by ML-layer type).
8. **Feedback** — None.

**Lineage:** Repr ⊃ MonoEmbed (uses CodeBERT); adds LLM labeling NEW. Seeding NEW (ML architectural patterns as seed types). Typed components NEW vs MonoEmbed.

#### Method 5 — Domain Aligned Microservices Decomposition

**Source:** Gandhi, Medicherla, Patwardhan, Sharma, Naik (TCS Research), ISEC 2025 (Article 16), DOI 10.1145/3717383.3717396. Follow-up: ASEW 2025 “Microservices Identification Using LLM,”  DOI 10.1109/ASEW67777.2025.00013.

1. **Input** — (a) Monolith source code (Java); (b) Domain Description of business services (text); (c) Domain Description Map (DDM) linking domain elements ↔ classes/methods.   In experiments, GPT-4o synthesizes the domain descriptions where unavailable; class-to-service mapping done manually.  
2. **Representation** — Weighted heterogeneous graph: nodes = class attributes/methods; edges = inheritance, aggregation, composition, business-function-sharing, DDM-link. Edge weights configurable. 
3. **Seeding** — DDM = the seed (architect/LLM-assisted anchor mapping).
4. **Variation** — None (graph built once; clustering once). Label propagation refines class assignments along edges.
5. **Fitness** — Internal cohesion + coupling; external domain alignment. 
6. **Selection** — Off-the-shelf unsupervised partitioning. 
7. **Output** — One decomposition: clusters aligned to business/domain services.  
8. **Feedback** — None (future: LLM-summarization to refine DDM iteratively).  

**Lineage:** Input ⊃ Service Cutter + Context Mapper (uses DDD artifacts). Repr ≈ Mono2Micro + GNN methods (heterogeneous graph); ⊃ MonoEmbed by adding DDM edges. Seeding NEW (DDM construct). Fitness ⊃ Service Cutter + NEW domain alignment. Typed by business domain — NEW vs MonoEmbed/Mono2Micro.

#### Method 6 — Stojanović & Lazarević (ChatGPT for microservices)

**Source:** Stojanović & Lazarević, “The Application of ChatGPT for Identification of Microservices,” *E-business Technologies Conf. Proc.* 3(1):99–105 (2023), University of Belgrade.  ebt.rs/journals/index.php/conf-proc/article/view/181. 

1. **Input** — Natural-language software requirements / user stories (3 example domains). 
2. **Representation** — Prompt (text); requirements pasted directly into ChatGPT.
3. **Seeding** — None (zero-shot).
4. **Variation** — None (single-shot; some manual re-prompting in examples, not formalized).
5. **Fitness** — None formal; qualitative human assessment.
6. **Selection** — None.
7. **Output** — One decomposition per example (suggested microservices + boundaries). 
8. **Feedback** — Implicit only (authors discuss drawbacks; no automated loop).  

**Lineage:** Input ≈ Service Cutter (user-story-like). Repr NEW (prompt). Earliest (2023) ChatGPT-for-microservice-identification paper, widely cited as exploratory.

### 3.2 Genetic / Evolutionary methods (deep, since SEMA-GA inherits most heavily)

#### Method 7 — MSExtractor (v1 + v2)

**Sources:** (v1) Saidani, Ouni, Mkaouer, Saied, “Towards Automated Microservices Extraction Using Multi-objective Evolutionary Search,” ICSOC 2019, LNCS 11895, DOI 10.1007/978-3-030-33702-5_5. (v2) Sellami, Ouni, Saied, Bouktif, Mkaouer, “Improving microservices extraction using evolutionary search,” *Information and Software Technology* 151, 106996 (2022),   DOI 10.1016/j.infsof.2022.106996.

1. **Input** — Java source code. v1: static class-level dependencies (calls, inheritance, field access). v2: + semantic/lexical info from class identifiers (tokenization, stop-word removal, stemming).
2. **Representation** — Chromosome = integer label vector (length = #classes), each gene assigns a class to a microservice ID. Equivalent to Bunch-style MDG partition encoding.
3. **Seeding** — Random partitioning. Population ~100.
4. **Variation** — Single-point crossover on labels; mutation = random reassignment of a class to another microservice ID. Pₓ ~0.9, Pₘ ~1/N.
5. **Fitness** — **v1 (NSGA-II, 2 objectives):** maximize CHM (Cohesion at Message level, Athanasopoulos), minimize CBM (Coupling Between Microservices). **v2 (IBEA, 3 objectives):**  (1) structural+semantic cohesion, (2) structural+conceptual coupling, (3) granularity (penalizes extreme distributions).
6. **Selection** — v1: NSGA-II non-dominated sorting + crowding distance + binary tournament + elitism.   v2: IBEA hypervolume/ε-indicator.  v2 reports IBEA > NSGA-II > SPEA2 statistically. 
7. **Output** — Pareto front; final = knee point.
8. **Feedback** — None (single GA run).

**Benchmarks:** v1: JPetStore-6, SpringBlog. v2: 7 systems  incl. JPetStore, SpringBlog, SpringBoot ground-truth projects (e.g., PiggyMetrics).
**Baselines:** FoME/MEM (Mazlami), LIMBO,  WCA  (v1);  NSGA-II and SPEA2 internal (v2).

**Lineage:** Repr ≈ Bunch/Praditwong (partition encoding). Variation ≈ standard NSGA-II ops (Mkaouer NSGA-III). v1 Fitness ⊃ Athanasopoulos CHM + standard CBM. v2 Fitness NEW = granularity objective + semantic-cohesion fusion. Selection v1 ≈ NSGA-II (Deb 2002);  v2 ⊃ IBEA (Zitzler/Künzli). 

#### Method 8 — FoSCI

**Source:** Jin, Liu, Cai, Kazman, Mo, Zheng, “Service Candidate Identification from Monolithic Systems based on Execution Traces,” *IEEE TSE* 47(5):987–1007 (2021),   DOI 10.1109/TSE.2019.2956525. Code: github.com/wj86/FoSCI. 

1. **Input** — Dynamic execution traces collected via Kieker 1.13 under a functional test suite;  representative trace set R_tr (after trace-reduction algorithm).  Also commit history (evolvability).
2. **Representation** — Chromosome = partition P = {q₁,…,q_k} of the Functional Atoms set FA = {fa₁,…,faₘ}; each qᵢ ≠ ∅, ∪qᵢ = FA, qᵢ ∩ qⱼ = ∅. N-partition → N service candidates. 
3. **Seeding** — Hierarchical agglomerative clustering (Jaccard over trace co-occurrence) produces Functional Atoms.  Random N-partitions of FA seed the initial population (size 20). Clustering threshold diff=3.  **Clustering-warm-started GA**.
4. **Variation** — **Single-parent crossover** (unusual): offspring = neighbor partition (NP) of parent P, generated by moving one FA from one element of P to a different element  (implements “move” and “pull-up”). Mutation = random NP replacement. Pₓ=0.8, Pₘ=0.04·log₂(n),  200 generations, pop=20, 30 repeats.
5. **Fitness** — **4 objectives** (maximize): (1) structural intra-connectivity (Mancoridis MQ-derived; edge = call in trace); (2) –structural inter-connectivity; (3) conceptual intra-connectivity (edge if shared identifier terms); (4) –conceptual inter-connectivity.  Post-hoc evaluation suite (8 metrics): IFN, CHM, CHD, SMQ, CMQ, ICF, ECF, REI. 
6. **Selection** — NSGA-II non-dominated sorting + crowding distance + binary tournament + elitism.
7. **Output** — Pareto front; final = knee point Pₖₙₑₑ (smallest Euclidean distance from ideal point). 
8. **Feedback** — None (30 independent runs averaged for stochastic robustness; no algorithmic loop).

**Benchmarks (6):** SpringBlog, Solo, JForum, Apache Roller, Agilefant, XWiki-platform. 
**Baselines:** WCA (UENM), LIMBO, MEM. 

**Lineage:** Input NEW (execution-trace-driven FAs vs static-only predecessors). Seeding ⊃ hierarchical clustering warm-start (Jaccard on traces) — NEW for monolith-decomposition GA. Variation NEW (single-parent neighbor-partition move+pull-up). Fitness ⊃ Mancoridis MQ + NEW conceptual intra/inter combination. Selection ≈ NSGA-II.

#### Method 9 — So4MoD

**Source:** Liu et al., “Towards a security-optimized approach for the microservice-oriented decomposition,” *Journal of Software: Evolution and Process* (Wiley, 2024), DOI 10.1002/smr.2670. Code: github.com/fengyingzi/So4MoD  (NSGA-II in Java under methodImplementation/nsga/NSGAService.java). 

1. **Input** — Monolith source code; static analysis extracts class-level structural + data dependencies (which classes access which DB entities).
2. **Representation** — Integer label-vector chromosome (≈ MSExtractor).
3. **Seeding** — Random.
4. **Variation** — Standard NSGA-II single/uniform crossover + per-gene mutation (relabel class to another service). Tournament selection. NSGA-II defaults (pop~100, gens~200).
5. **Fitness** — **5 data-security metrics**   (cross-service exposure of sensitive data tables/entities) + modularity metrics (SMQ-style + CHM/IFN-comparable for evaluation). Combined under NSGA-II as multi-objective.  
6. **Selection** — NSGA-II crowding distance + binary tournament + elitism.
7. **Output** — Pareto front of (security, modularity) trade-offs; one selected (knee/best-indicator).
8. **Feedback** — None.

**Benchmarks:** 8 OSS projects   incl. JPetStore.
**Baselines:** FoSCI, CO-GCN, MSExtractor. Claim: ≥11.5% security improvement + outperforms in 4 modularity metrics.

**Lineage:** Input ⊃ MSExtractor (adds data-security/data-dependency layer). Repr ≈ MSExtractor label vector. Fitness NEW (5 data-security metrics as objectives for monolith decomposition).

#### Method 10 — Microservices Backlog (MB-GA) / SEMGROMI

**Sources:** (MB-GA) Vera-Rivera, Puerto, Astudillo, Gaona, “Microservices Backlog – A Genetic Programming Technique…”, *IEEE Access*  9:117178 (2021), DOI 10.1109/ACCESS.2021.3106342. (SEMGROMI) Vera-Rivera, Puerto Cuadros, Perez, Astudillo, Gaona, “SEMGROMI — a semantic grouping algorithm to identifying microservices using semantic similarity of user stories,” *PeerJ Computer Science* 9:e1380 (2023).  **Note:** SEMGROMI itself is a clustering algorithm; MB-GA is the GA component.

**MB-GA pipeline:**

1. **Input** — User stories from product backlog  (NOT code/traces). Each: id, description, priority, points, dependencies, acceptance criteria. Data/entity/operation dependencies + semantic similarity of descriptions derived.
2. **Representation** — Binary assignment matrix (n user stories × m microservices)  flattened to bit string. b_ij = 1 ⇒ story i assigned to service j; each story to exactly one service.
3. **Seeding** — Random.
4. **Variation** — Standard binary GA crossover + bit-flip mutation  (forcing reassignment of a user story across microservices). 
5. **Fitness** — **Single aggregated Granularity Metric (GM)** = weighted sum of Coupling (low), Cohesion (high), Granularity, Semantic similarity, Complexity (low).   Eight  weight variants F1–F8 tested. 
6. **Selection** — Classical ranked/elitist (population ordered ascending by GM).   NOT NSGA-II.
7. **Output** — One best decomposition (minimum-GM individual).
8. **Feedback** — None algorithmic (semi-automatic via architect; SEMGROMI 2023 replaces GA with Word2Vec semantic-similarity clustering for speed). 

**Benchmarks (4):** Cargo Tracking, JPetStore, Foristom Conferences,   Sinplafut (industrial, 92 stories).
**Baselines:** DDD, Service Cutter, MITIA, FoSCI execution-traces, architect’s manual. 

**Lineage:** Input NEW (user stories — distinct from all other 3 GA methods which use code/traces). Repr NEW (binary user-story × microservice matrix). Fitness ⊃ weighted-sum scalar of 5 sub-metrics — ≠ Pareto from FoSCI/MSExtractor. Selection ≠ NSGA-II.

### 3.3 DDD-based methods

#### Method 11 — Service Cutter

**Source:** Gysel, Kölbener, Giersche, Zimmermann, “Service Cutter: A Systematic Approach to Service Decomposition,” ESOCC 2016,  LNCS 9846, pp. 185–200, DOI 10.1007/978-3-319-44482-6_12.  

1. **Input** — System Specification Artifacts (SSAs / “user representations”): ER model, use cases, aggregates, entities, predefined services, shared owner groups, security zones, security access groups, compatibilities. JSON-encoded.
2. **Representation** — Undirected weighted graph: nodes = nanoentities (data fields, operations, artifacts); edges = weighted couplings  scored by 16 coupling criteria. 
3. **Seeding** — None (deterministic construction; Girvan-Newman takes desired #clusters; Leung/MCL pick automatically).
4. **Variation** — None (one-shot clustering; randomized algorithms may produce different cuts on rerun).
5. **Fitness** — Edge-weighted modularity-like objective. Per-edge score = weighted sum of 16 CC scores (each [-10..+10])  using priorities XS/S/M/L/XL/XXL/IGNORE.
6. **Selection** — Graph clustering: **Girvan-Newman** (deterministic, edge-betweenness, user-given k), **Epidemic Label Propagation (Leung)** (auto-k), **MCL / Chinese Whispers** (later additions).
7. **Output** — One service cut (partition of nanoentities into candidate services). 
8. **Feedback** — None in algorithm; architect manually re-tunes priorities and reruns.

**The 16 Coupling Criteria (4 categories):**

- *Cohesiveness (3):* CC-1 Identity & Lifecycle Commonality, CC-2 Semantic Proximity, CC-3 Shared Owner.
- *Compatibility (6):* CC-4 Structural Volatility, CC-5 Content Volatility, CC-6 Availability Criticality, CC-7 Consistency Criticality, CC-8 Storage Similarity, CC-9 Security Criticality.
- *Constraint (4):* CC-10 Predefined Service Constraint, CC-11 Latency Constraint, CC-12 Consistency Constraint, CC-14 Security Constraint.
- *Communication (3):* CC-13 Network Traffic Suitability, CC-15 Security Contextuality, CC-16 communication/mutability-related.

#### Method 12 — Mono2Micro

**Source:** Kalia, Xiao, Krishna, Sinha, Vukovic, Banerjee (IBM), “Mono2Micro: A Practical and Effective Tool for Decomposing Monolithic Java Applications to Microservices,”  ESEC/FSE 2021   Industry, pp. 1214–1224, DOI 10.1145/3468264.3473915  (arXiv:2107.09698). Demo precursor: ESEC/FSE 2020.

1. **Input** — Monolithic Java/JEE bytecode + labeled business use cases executed via UI/functional tests. Runtime call traces   with timestamps + thread IDs.
2. **Representation** — Reduced class-level Calling-Context Trees (CCTs) per use case → four similarity matrices → final class–class similarity matrix S.
3. **Seeding** — None (bottom-up agglomerative).
4. **Variation** — None.
5. **Fitness** — Combined similarity across 4 spatio-temporal features (below). Evaluation: BCP, ICP, SM, IFN, NED.
6. **Selection** — Hierarchical agglomerative clustering on S; cluster count chosen via hill-climbing across dendrogram cuts.
7. **Output** — One (or small set of) partition recommendations;  two flavors: business-logic-seam-based and natural-seam-based.
8. **Feedback** — No closed loop (practitioner may re-label use cases).

**Spatio-temporal features:**

- *Space (use-case dimension):* **DCR** Direct Call Relation; **DCP** Direct Call Pattern.
- *Time (control-flow dimension):* **ICR** Indirect Call Relation; **ICP** Indirect Call Pattern.

**Code is not open-sourced** (reproducibility caveat).

#### Method 13 — Context Mapper / CML

**Sources:** Kapferer & Zimmermann, “DSL and Tools for Strategic Domain-Driven Design…,” MODELSWARD 2020; “Domain-Driven Architecture Modeling and Rapid Prototyping with Context Mapper,” MODELSWARD selected papers, CCIS 1361 (Springer 2021); “Domain-Driven Service Design…,” SummerSOC 2020, CCIS 1310. Tool: contextmapper.org. Follow-up: Levezinho, Kapferer, Zimmermann, Rito Silva, “DDD Representation of Monolith Candidate Decompositions Based on Entity Accesses,” EDOC 2024 (arXiv:2407.02512).

1. **Input** — CML (`*.cml`) text models,  authored manually or reverse-engineered (Discovery Library from Spring Boot annotations);  optional SCL files for Service Cutter config.
2. **Representation** — Typed DDD meta-model: BoundedContext (typed FEATURE/APPLICATION/SYSTEM/TEAM), Subdomain (CORE/SUPPORTING/GENERIC),  Aggregate (with owner, security zone, characteristics), Entity/ValueObject/DomainEvent/Service/Repository (tactical DDD), ContextMap with typed relationships (Partnership, Shared Kernel, Customer/Supplier, Conformist, **Anti-Corruption Layer**, Open Host Service, Published Language).
3. **Seeding** — Initial CML model authored (Event Storming, user stories via Rapid OOAD/Story Splitting, or reverse-engineered from code).
4. **Variation** — Library of typed **Architectural Refactorings (ARs)**: AR-1 Split Aggregate by Entities; AR-2 Split BC by Features; AR-3 Split BC by Owner; AR-4 Extract Aggregates by Volatility; AR-5 Extract by Cohesion; AR-6 Merge Aggregates; AR-7 Merge BCs; AR-8 Extract Shared Kernel; AR-9 Suspend Partnership; AR-10/11 toggle Shared Kernel ↔ Partnership.
5. **Fitness** — No formal objective function; modeler judgement. When delegated to embedded Service Cutter, 16-CC score applies.
6. **Selection** — Manual (architect picks AR sequence) or automated via Service Cutter (MCL/Leung/Chinese Whispers).
7. **Output** — Refactored CML model + generators:  PlantUML, Context Map graphics, MDSL service contracts, JHipster microservice projects, BPMN Sketch Miner, Service Cutter JSON.
8. **Feedback** — Iterative human-in-the-loop;  bidirectional roundtrip model ↔ code; no automated metric-driven feedback.

**Lineage:** Context Mapper ⊃ Service Cutter (CM embeds SC as a generator).  Richest type system among DDD methods (BC types, Subdomain types, typed AR catalog). NEW: typed DDD model + AR catalog as transformation library.

#### Method 14 — Domain Aligned (ISEC 2025) — DDD view

*(Same paper as Method 5; reclassified for DDD listing)*
**Source:** Gandhi et al., ISEC 2025, DOI 10.1145/3717383.3717396. 

Pipeline as in Method 5. From the DDD angle, the contribution is the **explicit Domain Description Map (DDM)** — an architect-curated mapping from domain elements to code elements  that anchors the static-analysis graph clustering. This is the DDD-flavored axis missing from Service Cutter (which consumes domain artifacts only at nanoentity level, not via top-down domain projection).

**Lineage:** ≈ Context Mapper in spirit (domain-model → code) but ≠ in mechanism (code-first matching vs model-first DSL). NEW: explicit architect-curated domain-to-code map (DDM) as first-class algorithmic input.

#### Method 15 — DDD + static/dynamic (adesso in|FOCUS)

**Source:** Krause, Zirkelbach, Hasselbring, Lenga, Kröger, “Microservice Decomposition via Static and Dynamic Analysis of the Monolith,”  ICSA-C 2020, DOI 10.1109/ICSA-C50368.2020.00009 (arXiv:2003.02603).

1. **Input** — Layered monolithic Enterprise Java legacy system (adesso’s in|FOCUS lottery  SaaS)   + domain knowledge + source code + runtime traces.
2. **Representation** — Context Map of Bounded Contexts  with grouped use cases; **Structure101** levelized structure maps (Source Code Packages → use cases); **ExplorViz** live trace visualization  (dynamic call graph).
3. **Seeding** — Domain analysis (event-storming-like collaboration with developers) → ubiquitous language,  use cases, initial BC set as candidate boundaries. 
4. **Variation** — Manual refactoring iterations: re-mapping SCPs to BCs when static analysis reveals package overlap; further splitting/merging when dynamic traces show unexpected runtime coupling. 
5. **Fitness** — Qualitative: BC cohesion, business-function overlap (ambiguity), runtime coupling intensity, alignment with DDD ubiquitous language, maintainability. No scalar metric.
6. **Selection** — Human-in-the-loop collaborative review with developers.
7. **Output** — One decomposition: refined Context Map → set of microservice candidates.
8. **Feedback** — Yes: iterative loop. Static findings refine BCs from domain analysis; dynamic visualization refines further;  developers iterate.

**Lineage:** ⊃ Service Cutter (uses coupling/cohesion-style criteria; adds dynamic). ≈ Context Mapper (DDD-based, BC-driven) but as industrial case rather than DSL/tool. ≈ Mono2Micro on use of runtime traces but uses live ExplorViz visualization + DDD instead of unsupervised clustering. NEW: first published industrial DDD experience report combining ExplorViz dynamic visualization + Structure101 static maps for BC refinement.

#### Method 16 — SRME (Sub-Requirement-based Microservice Extraction)

**Source (best match):** Bu, Xiao, Li, Xie, “A Microservice Decomposition Approach Driven by Sub-Requirement References in Problem Diagrams,” REW 2024, pp. 192–199, DOI 10.1109/REW61692.2024.00031.  Precursors: PF4Microservices (arXiv:2207.04586, 2022); PF4MD tool demo (RE 2023).  **Acronym SRME not literally verified — flagged for user confirmation.**

1. **Input** — Natural-language requirements (functional requirements, use cases, system topology / hardware facilities). No source code.
2. **Representation** — Jackson Problem Frames / Problem Diagrams: rectangles for machine, biddable, causal, lexical problem domains; shared phenomena; requirement references / **sub-requirement references**.
3. **Seeding** — One problem diagram per individual requirement; hardware facilities mapped to problem domains. 
4. **Variation** — Merging of problem diagrams sharing problem domains and sub-requirement references; resolving multi-microservice domain assignment by counting diagram involvement. 
5. **Fitness** — Correlation between diagrams (shared domains / shared sub-requirement references) + hardware-facility similarity; aim is high intra-microservice cohesion of requirements/domains and low inter-microservice coupling.
6. **Selection** — Deterministic tie-breaking: problem domains in multiple candidates assigned to microservice with largest # involving diagrams.
7. **Output** — One decomposition (set of merged “microservice decomposition problem diagrams”).  Case study: smart parking → 3 microservices.
8. **Feedback** — None (single-pass deterministic).

**Lineage:** ≠ Service Cutter / Mono2Micro / MSExtractor (no code, no traces, no clustering — purely requirements-side). ≠ Context Mapper (uses Jackson Problem Frames instead of DDD BCs — Michael Jackson lineage, not Eric Evans). ≈ SEMGROMI and Dataflow-driven (Li 2019) as requirements/artifact-driven decomposers. NEW: first method to exploit Jackson sub-requirement references as the merging signal.

#### Method 17 — Feature Table

**Source:** Wei, Yu, Pan, Zhang, “A Feature Table approach to decomposing monolithic applications into microservices,” Internetware 2020 (ACM, proceedings 2021), DOI 10.1145/3457913.3457939 (arXiv:2105.07157).

1. **Input** — Monolith’s functional requirements / feature catalogue (use cases, business logic). Validated on Cargo Tracking System (Evans/DDD canonical).
2. **Representation** — **12 typed Feature Cards** + **Feature Table** correlating functional features × candidate microservices + **Mapping Rules** linking features → code components. 
3. **Seeding** — Enumerate functional features; instantiate one Feature Card per feature; populate Feature Table cells.
4. **Variation** — Apply fixed **Decomposition Rules** to combine/split features into microservice candidates within the Feature Table.
5. **Fitness** — Coupling + cohesion metrics (quantitative; used in comparative evaluation vs Dataflow-driven, Service Cutter, API Analysis).
6. **Selection** — Rule-based, semi-automatic via Feature Table Analysis Tool; analyst confirms.
7. **Output** — One decomposition: set of microservice candidates with Mapping Rules to implementation artifacts.
8. **Feedback** — None explicit (interactive tool, but no fitness-driven loop).

**Lineage:** ⊃ Dataflow-Driven (Li et al. 2019). ≠ Service Cutter (compared against; FT claims better coupling/cohesion). ≠ Mono2Micro (no traces/ML). ≈ API Analysis (Baresi). NEW: 12 typed Feature Cards + Decomposition Rules + semi-automatic Feature Table Analysis Tool with Mapping Rules.

### 3.4 Hybrid / GNN / RL methods

#### Method 18 — CARGO

**Source:** Nitin, Asthana, Ray, Krishna, “CARGO: AI-Guided Dependency Analysis for Migrating Monolithic Applications to Microservices Architecture,” ASE 2022,  DOI 10.1145/3551349.3556960 (arXiv:2207.11784).

1. **Input** — Java EE source code → context- and flow-sensitive **System Dependency Graph (SDG)**; nodes = methods + DB tables; edges = call-return, data-flow, heap-dependency, **transactional edges**.   Static (no dynamic traces).
2. **Representation** — SDG decomposed into “contextual snapshots” (sub-graphs per calling context across transactional scopes).   Context-sensitivity per Milanova et al. 
3. **Seeding** — Semi-supervised: initial labels from a baseline partitioner (Mono2Micro, FoSCI, CO-GCN, IBM MS Extractor). Unsupervised: small seed set chosen by structural heuristics — nodes with high transactional/heap connectivity as anchors.
4. **Variation** — **Label Propagation Algorithm (LPA)** (Xiaojin & Zoubin 2002)  per contextual snapshot;  labels propagate along weighted SDG edges where transactional/heap edges receive higher weight to keep DB-coupled methods together. Per-context labels aggregated/merged into global partitioning.
5. **Fitness** — Structural Modularity (SM), modularity, ICP (Inter-Partition Calls), BCP (Business Context Purity) + # distributed transactions + runtime latency/throughput.
6. **Selection** — Iterative: LPA iterates to label convergence per snapshot; outer loop refines baseline partitions.
7. **Output** — One decomposition.
8. **Feedback** — Implicit (LPA update is the only loop); no external reward.

**Benchmarks:** DayTrader, Plants, AcmeAir, JPetStore  + 1 proprietary IBM app.

**Lineage:** ≈ Service Cutter, FoSCI (graph partitioning). ⊃ Mono2Micro / FoSCI / CO-GCN (used as refinement on top of these baselines). ≠ MonoEmbed (no embeddings); ≠ MSExtractor (not genetic). NEW: first to use context- and flow-sensitive SDG with **DB-transaction edges**; novel context-sensitive label propagation reduces distributed transactions,  eliminates “distributed monolith” partitions. 

#### Method 19 — MAGNET

**Source:** Trabelsi, Moha, Guéhéneuc, Geffard, “MAGNET: Method-based Approach using Graph Neural Network for Microservices Identification,” ICSA 2024   (Hyderabad), pp. 1–11,  DOI 10.1109/ICSA59870.2024.00009. Replication: github.com/magnetmicro/MAGNET; Zenodo 10.5281/zenodo.10794892.

1. **Input** — Monolithic Java source code → KDM (Knowledge Discovery Metamodel,  via MoDisco)  at **method-level** granularity.
2. **Representation** — Feature-Rich Dependency Graph:   **nodes = methods**;  edges = method-call dependencies. Node features = pre-trained  **Word2Vec**  (GoogleNews 300d) encoding of method names, class names, comments, aggregated per method. Feature matrix X.
3. **Seeding** — None (fully automated;  no expert input,  no a-priori labels).
4. **Variation** — Message passing via **GCN** layers.  Model learns node embeddings via graph convolution; then clusters; K swept and K maximizing internal quality auto-selected.
5. **Fitness** — SMQ, CMQ, CHM, CHD. Training objective promotes  high intra-cluster cohesion / low inter-cluster coupling.  
6. **Selection** — Iterative: GNN trained over epochs; K-sweep retains best-quality partition. 
7. **Output** — One decomposition.
8. **Feedback** — Implicit (training loss only); no RL.

**Performance:** 56% precision, 68% recall, 61% F-measure on 4 OSS systems incl. JavaFX POS.

**Lineage:** ≈ CO-GCN (GNN-based deep graph clustering). ≈ MonoEmbed (uses pre-trained semantic encoder — Word2Vec vs LLM). ⊃ MicroMiner (extends method-level static+semantic graph with deep clustering). ≠ FoSCI / Mono2Micro (no dynamic traces); ≠ MSExtractor (not GA). NEW: method-level granularity (not class-level); fully automated K selection; combines KDM structure with Word2Vec semantic enrichment in a single GCN clustering pipeline.

#### Method 20 — CO-GCN

**Source:** Desai, Bandyopadhyay, Tamilselvam, “Graph Neural Network to Dilute Outliers for Refactoring Monolith Application,” AAAI 2021,   arXiv:2102.03827. Code: github.com/utkd/cogcn.  **Note:** AAAI 2021, not ICSE; full name is **Clustering and Outlier-aware GCN**, not Constraint-Oriented.

1. **Input** — Monolithic Java source code (static analysis via SOOT). Extracts classes, inheritance, entrypoint methods/APIs.
2. **Representation** — Attributed directed graph G=(V,E,X): nodes = classes; edge A→B if method in A calls one in B (unweighted).  Attribute matrix X = concatenation of three matrices: **EP** (entrypoint membership, |V|×|P|), **C** (entrypoint co-occurrence, |V|×|V|), **In** (inheritance indicator, |V|×|V|), each row-normalized. 
3. **Seeding** — k-means++ initializes cluster assignment matrix M and cluster centers C  *after* GCN encoder/decoder pretraining. K supplied by SME. 
4. **Variation** — 2-layer GCN encoder (sizes 64 and 32): Z = ReLU(Â·ReLU(Â·X·W⁰)·W¹); 2-layer GCN decoder reconstructs X̂.  Alternating minimization updates GCN params, outlier scores, cluster assignments. 
5. **Fitness** — Joint loss: L_total = α₁L_str + α₂L_att + α₃L_clus, with α = {0.1, 0.1, 0.8}. 
- L_str (structural reconstruction) with structural-outlier discount log(1/Osi) 
- L_att (attribute reconstruction) with attribute-outlier discount log(1/Oai) 
- L_clus = k-means quadratic loss in embedding space
   
   Constraints: ΣOsi = ΣOai = 1; M ∈ {0,1}^{|V|×K}. 
1. **Selection** — Iterative alternating optimization (ADAM for W; closed-form for outliers; k-means updates for M, C). 250 pretraining + 500 main iterations. 
2. **Output** — One decomposition + ranked **outliers** (top refactor candidates) via Osi and Oai scores.
3. **Feedback** — Implicit (training loss only).

**Benchmarks:** DayTrader (111 classes), Plants-by-WebSphere/PBW (36), AcmeAir (38), DietApp/C# (32).  Metrics: SM, Modularity, 1-NED, IFN.

**Lineage:** ≈ Mazlami graph-clustering (first GNN approach for this problem). ⊃ vanilla GCN-AE (Kipf & Welling) + outlier-aware ONE framework (Bandyopadhyay). ≠ FoSCI / Mono2Micro (static vs dynamic); ≠ MSExtractor (deep vs evolutionary). NEW: first GNN-based monolith decomposition; novel joint loss unifying embedding + outlier-aware learning + integrated clustering;  outliers identified as refactor candidates. Predates and inspired DEEPLY, CHGNN, MAGNET.

#### Method 21 — RLDec

**Source:** Sellami & Saied (Laval), “Extracting microservices from monolithic systems using deep reinforcement learning,”  *Empirical Software Engineering* 30, Article 1 (Feb 2025;   online Oct 2024), DOI 10.1007/s10664-024-10547-4. Code: github.com/khaledsellami/decomp-rldec; artifacts: figshare 24939159.

1. **Input** — Source code of monolithic Java application  → static analysis pipeline (decomp-java-analysis-service + decomp-parsing-service) producing structural call relations + semantic (lexical) features per class.
2. **Representation** — State space = structural + semantic features of all classes + current (partial) assignment of classes to candidate microservices; class-level granularity.
3. **Seeding** — None / empty assignment at episode start (or initial uniform/random partition); no expert labels required.
4. **Variation** — RL action policy: at each step, agent assigns a class to one of K microservices.  Policy learned via **Deep Q-Network (DQN)**; variants incl. Double DQN evaluated.
5. **Fitness** — Reward = structural and semantic quality of generated microservices   (cohesion ↑, coupling ↓, with semantic-similarity terms). MDP set up so reward signals decomposition-quality change  after each action. 
6. **Selection** — RL policy update via Q-learning Bellman target, experience replay, target network (standard DQN). Iterative training over many episodes.
7. **Output** — One decomposition (class-to-microservice mapping by learned greedy policy).
8. **Feedback** — **Yes — explicit reward feedback** (the reward signal *is* the closed feedback loop).

**Benchmarks (per follow-on work):** AcmeAir, DayTrader, JPetStore, Plants. Compared vs Mono2Micro, FoSCI, MEM, hierarchical DBSCAN.

**Lineage:** ≈ Chaieb et al. 2022 (MDE+RL reverse-engineering). ⊃ MSExtractor (moves from genetic to RL); ⊃ Mono2Micro/FoSCI quality metrics (re-used as reward). ≠ CO-GCN/MAGNET (no GNN); ≠ CARGO (no program graph). NEW: first DQN/MDP formulation of monolith → microservices with structural+semantic quality as reward;   learnt class-assignment policy generalizes across applications; no a-priori partition required.

### 3.5 Target method: SEMA-GA

#### Method 22 — SEMA-GA (Semantically Mediated Adaptive Genetic Algorithm)

**Status:** Not published; the user is authoring this paper. Search returned zero hits for “SEMA-GA”. The closest adjacent works are **LMEA** (Liu et al., arXiv:2310.19046, 2023 — LLM as zero-shot evolutionary operator on TSP) and **MOEA/D-LO / LLM4MOEA** (Liu et al., arXiv:2310.12541, 2023 — LLM as black-box operator in decomposition-based MOEA). Both are for general MOO benchmarks, *not* microservice decomposition.

**Central thesis (for the paper’s framing):** Pure LLM decomposition methods (MonoEmbed, MicroDec, prompt-only baselines) have strong *semantic perception* but perform myopic local search (one forward pass or greedy clustering). Evolutionary methods (MSExtractor, FoSCI, So4MoD, MB-GA) have strong *global search* via NSGA-II/III over the Pareto front of cohesion/coupling/modularity, but their operators are *semantically blind*. **SEMA-GA composes the two**: the LLM becomes a first-class genetic operator inside a constrained multi-objective NSGA-II/III loop.

1. **Input** — Source code (AST + class/method bodies); static call graph (class-class and method-method edges, ⊃ MSExtractor/CARGO); LLM-readable per-class summaries (name + javadoc + method signatures + identifiers). Optional: dynamic traces (FoSCI-style) and DB-table edges (CARGO-style).
2. **Representation** — Dual: (a) chromosome = integer vector x ∈ {1..K}^N (class-to-service label vector — ≈ MSExtractor/FoSCI/So4MoD); (b) phenotype augmentation: per cluster c, a concatenated text view of class summaries + 1-sentence LLM-generated cluster description. The dual representation bridges GA and LLM layers.
3. **Seeding** — Hybrid warm-start from four sources:
- Random label vectors (≈ MSExtractor; preserves NSGA-II diversity baseline)
- Heuristic clustering (Louvain/Leiden/spectral on call graph)
- **LLM-proposed seeds** (NEW): prompt LLM with class summaries to propose candidate partitions → parsed → label vectors
- Embedding warm-start (MonoEmbed-style: CodeBERT/LLM2Vec → k-means)
1. **Variation** — **Adaptive operator scheduler** arbitrates among:
- Classical crossover (uniform / one-point on label vectors) — ≈ MSExtractor
- Classical mutation (random relabel) — ≈ MSExtractor
- **Semantic crossover (NEW)**: LLM shown two parent partitions’ text views, prompted to “merge the best subsets of each parent into a coherent child” preserving conceptual boundaries; output parsed and repaired
- **Reflective mutation (NEW)**: LLM shown a candidate’s text view + fitness vector + diagnostic of weakest objective; proposes targeted reassignments to improve weak axis (the “reflection” is explicit observation of prior-iteration outcome in prompt context)
- **Repair operator**: enforces feasibility (size bounds, no empty service, balance)
   
   Scheduler uses progress signals (hypervolume Δ, Pareto-front spread Δ) to bias toward operator that recently produced most non-dominated offspring — UCB-style adaptive operator selection (Fialho/Sebag tradition) extended with **LLM-call cost-awareness**.
1. **Fitness** — Constrained multi-objective (all standardized to minimization for NSGA-II):
- Cohesion: CHM, CHD (Cohesion at Message/Domain level — Jin et al. FoSCI)
- Coupling: CBM (Coupling Between Microservices — Taibi & Systä), ICP
- Modularity: SMQ (FoSCI)
- Interface complexity: IFN, OPN
- Balance: NED
- **Semantic coherence (NEW)**: intra-cluster cosine similarity of CodeBERT/LLM2Vec embeddings + LLM-scored cluster-coherence rating
- Constraints (NSGA-II constrained-dominance, Deb 2002): size bounds; optional DDD constraints (aggregate-roots stay together; entities in same Bounded Context per CML); architectural-layer constraints (Frontend/Backend/API typed components respect layer boundaries)
1. **Selection** —
- NSGA-II non-dominated sorting + crowding distance for ≤3 objectives (Deb et al. 2002)
- NSGA-III with reference points for ≥4 objectives (Deb & Jain 2014)
- **Semantic niching (NEW)**: niches in semantic-embedding space of cluster-summary embeddings — two solutions that are “semantically the same decomposition” penalized for crowding even if their fitness vectors differ; prevents front collapsing onto rephrasings
- **Pareto critic (NEW, auxiliary)**: LLM shown current front (top-k by hypervolume contribution), critiques each candidate, flags overloaded services, missing bounded contexts, anti-patterns (god-service, chatty-service); critic score is auxiliary tiebreaker and feeds reflective-mutation prompt
1. **Output** — **Pareto front** of decompositions, each with: label vector; objective vector (CHM, CHD, CBM, SMQ, IFN, NED, OPN, semantic-coherence); LLM-generated rationale per cluster; LLM critic notes; LLM-inferred typed components (Frontend/Backend/API/Worker).
2. **Feedback** — **Yes — explicit reflection**: every T generations, LLM is fed (current front, previous front, Δ per objective, which operator produced which improvement). Returns natural-language critique and “operator hints” (e.g., “Order/Inventory boundary fragmenting — try semantic-crossover fixing Order classes as a unit”). Hints injected into subsequent prompts. Loop closed, not just generative — distinguishes SEMA-GA from one-shot LLM-as-operator (LMEA, MOEA/D-LO).

**Lineage tags per step:**

- **Input** ⊃ MSExtractor v2 / FoSCI (static code + semantic); NEW if fuses LLM-extracted typed components
- **Representation** ≈ MSExtractor / FoSCI / So4MoD (label-vector partition encoding); NEW: dual numeric+textual phenotype
- **Seeding** ⊃ FoSCI (clustering warm-start); NEW: LLM-proposed seeds and embedding warm-start as parallel seeding streams
- **Variation** ≈ MSExtractor for classical ops; **NEW: semantic crossover, reflective mutation, adaptive scheduler arbitrating between LLM and classical operators**
- **Fitness** ⊃ FoSCI (struct+conc cohesion/coupling); NEW: semantic coherence objective + LLM-judged cluster-coherence + DDD constraints
- **Selection** ≈ NSGA-II / NSGA-III backbone; **NEW: semantic niching + Pareto critic auxiliary**
- **Output** ≈ FoSCI / MSExtractor (Pareto front); NEW: per-candidate LLM rationale + typed components + critic notes
- **Feedback** **NEW**: all four GA predecessors (MSExtractor, FoSCI, So4MoD, MB-GA) have no feedback loop — closed-loop explicit LLM reflection is a clear novelty axis
- **Domain-driven** NEW if SEMA-GA encodes DDD constraints (only MB-GA is partial; Context Mapper is fully DDD but not a search algorithm)
- **Typed components** NEW: distinguishes Frontend/Backend/API/Worker via LLM labels — none of the GA predecessors do this

-----

## 4. Capability heatmap data

|Capability                     |1 MonoEmbed|2 MicroDec|3 SysLLM  |4 PatLLM-ML|5 DomAln |6 Stoj.   |7 MSExt|8 FoSCI|9 So4MoD|10 MB-GA|11 ServCut|12 Mono2Mi|13 CtxMap|14 DomAln-DDD|15 adesso|16 SRME|17 FeatTab|18 CARGO     |19 MAGNET |20 CO-GCN |21 RLDec|22 SEMA-GA  |
|-------------------------------|-----------|----------|----------|-----------|---------|----------|-------|-------|--------|--------|----------|----------|---------|-------------|---------|-------|----------|-------------|----------|----------|--------|------------|
|Uses LLM                       |✓ Encoder  |✓ Encoder |✓ Proposer|✓ Labeler  |✓ Labeler|✓ Proposer|–      |–      |–       |–       |–         |–         |–        |✓ Labeler    |–        |–      |–         |–            |◐ Word2Vec|–         |–       |✓ Op+Critic |
|Population-based search        |–          |–         |–         |–          |–        |–         |✓      |✓      |✓       |✓       |–         |–         |–        |–            |–        |–      |–         |–            |–         |–         |–       |✓           |
|Multi-objective Pareto         |–          |–         |–         |–          |–        |–         |✓      |✓      |✓       |–       |–         |–         |–        |–            |–        |–      |–         |–            |–         |–         |–       |✓           |
|Produces Pareto front          |–          |–         |–         |–          |–        |–         |✓      |✓      |✓       |–       |–         |–         |–        |–            |–        |–      |–         |–            |–         |–         |–       |✓           |
|Feedback / iteration           |–          |–         |✓ human   |–          |–        |–         |–      |–      |–       |–       |–         |–         |✓ human  |–            |✓ human  |–      |–         |◐ propagation|◐ training|◐ training|✓ reward|✓ reflection|
|DDD-aware                      |◐          |–         |◐         |◐          |✓        |◐         |–      |–      |–       |◐       |◐         |◐         |✓        |✓            |✓        |◐      |◐         |–            |–         |–         |–       |◐           |
|Typed components produced      |–          |◐         |✓         |✓          |✓        |–         |–      |–      |–       |–       |✓         |–         |✓        |✓            |◐        |✓      |✓         |✓            |–         |–         |–       |✓           |
|Static code input              |✓          |✓         |✓         |✓          |✓        |–         |✓      |–      |✓       |–       |◐         |–         |◐        |✓            |✓        |–      |–         |✓            |✓         |✓         |✓       |✓           |
|Dynamic trace input            |–          |–         |–         |–          |–        |–         |–      |✓      |–       |–       |–         |✓         |–        |–            |✓        |–      |–         |–            |–         |–         |–       |◐ optional  |
|Requirements / user-story input|–          |–         |◐         |–          |–        |✓         |–      |–      |–       |✓       |◐         |–         |◐        |◐            |◐        |✓      |✓         |–            |–         |–         |–       |–           |
|Domain model input             |–          |–         |–         |–          |✓        |–         |–      |–      |–       |–       |✓         |–         |✓        |✓            |✓        |◐      |◐         |–            |–         |–         |–       |◐ optional  |
|Semantic similarity used       |✓          |✓         |✓         |✓          |✓        |–         |◐ v2   |✓      |–       |✓       |◐         |◐         |–        |✓            |–        |–      |–         |–            |✓         |–         |✓       |✓           |
|Outputs single decomposition   |✓          |✓         |✓         |✓          |✓        |✓         |– knee |– knee |– knee  |✓       |✓         |✓         |✓        |✓            |✓        |✓      |✓         |✓            |✓         |✓         |✓       |–           |
|Acknowledges constraints       |–          |–         |–         |–          |◐        |–         |–      |–      |–       |◐       |✓         |–         |✓        |✓            |–        |–      |–         |✓ txn        |–         |–         |–       |✓           |

Legend: ✓ = yes / present; ◐ = partial / weak; – = no / absent.

-----

## 5. Family clustering view (groupings for the visual)

- **Cluster A — LLM-only / LLM-centric:** MonoEmbed (1), Systematic LLM (3), Stojanović (6). LLM is the engine; either as encoder (MonoEmbed) or as proposer (Systematic, Stojanović). No combinatorial search.
- **Cluster B — Hybrid LLM+structural (single-shot):** MicroDec (2), Pattern-Driven-ML (4), Domain Aligned (5/14). LLM provides semantic signal; classical clustering/graph algorithm consumes it. Single-shot.
- **Cluster C — Genetic / Evolutionary (no LLM):** MSExtractor (7), FoSCI (8), So4MoD (9), MB-GA / SEMGROMI (10). Multi-objective NSGA-II/IBEA over partition chromosomes. Pareto fronts (except MB-GA which is single-objective weighted).
- **Cluster D — DDD-tooling / model-driven:** Service Cutter (11), Context Mapper (13), adesso in|FOCUS (15). Domain-model-first; ARs or coupling criteria. Human-in-the-loop iteration.
- **Cluster E — Clustering on traces:** Mono2Micro (12). Closest to Cluster D in producing a single recommended cut, but signal is dynamic and the engine is purely algorithmic.
- **Cluster F — Requirements/Artifact-driven (non-DDD):** SRME (16), Feature Table (17). Pre-code, requirement-side; problem frames and feature cards.
- **Cluster G — Graph-analytical hybrids:** CARGO (18). Label propagation on heterogeneous SDG; can refine other methods’ outputs.
- **Cluster H — GNN deep-learning:** MAGNET (19), CO-GCN (20). Neural graph encoders + clustering loss.
- **Cluster I — Reinforcement learning:** RLDec (21). DQN-based; only prior method with explicit reward-feedback loop.
- **Cluster J — Composed Hybrid (LLM-inside-GA):** **SEMA-GA (22)**. The target method occupies an empty quadrant: combines population-based Pareto search (Cluster C) with LLM-as-operator (extends Cluster A/B beyond encoder/proposer to first-class genetic operator), with explicit reflection feedback (extends Cluster I beyond reward to language-mediated critique).

-----

## 6. Novelty count summary (how many methods have each capability)

Of 21 prior methods (1–21), counts of capability presence (✓ + ◐ partial):

- **LLM used at all:** 7 of 21 (MonoEmbed, MicroDec, Systematic, Pattern-ML, Domain-Aligned, Stojanović, MAGNET-borderline Word2Vec). Of these, all are encoder/labeler/proposer — **zero use LLM as operator or critic**.
- **Population-based evolutionary search:** 4 of 21 (MSExtractor, FoSCI, So4MoD, MB-GA).
- **Produces a Pareto front (not a single solution):** 3 of 21 (MSExtractor, FoSCI, So4MoD).
- **Multi-objective optimization (true Pareto, not weighted sum):** 3 of 21 (same).
- **Closed feedback loop (explicit, algorithmic — not human-in-loop):** 1 of 21 (RLDec via reward); all four GA methods have **no** feedback loop.
- **Explicit reflection / language-mediated feedback:** **0 of 21** — SEMA-GA is the first.
- **DDD-aware (Yes, not Partial):** 3 of 21 (Context Mapper, Domain Aligned, adesso in|FOCUS).
- **Produces typed components (Frontend/Backend/API/Worker or domain-typed):** 9 of 21 (Systematic, Pattern-ML, Domain-Aligned, ServiceCutter, ContextMapper, adesso, SRME, FeatureTable, CARGO).
- **Combines LLM + multi-objective Pareto search:** **0 of 21** — SEMA-GA is first.
- **Combines LLM + DDD constraints in search:** **0 of 21** — SEMA-GA optional but unique among search methods.
- **Adaptive operator selection on LLM-vs-classical operators:** **0 of 21** — SEMA-GA NEW.
- **Semantic niching in microservice decomposition:** **0 of 21** — SEMA-GA NEW.
- **LLM as Pareto critic in any search algorithm for software architecture:** **0 of 21** — SEMA-GA NEW.

**SEMA-GA novelty count (axes where it is the first or only method):** at least 6 — (1) LLM-as-crossover operator, (2) LLM-as-reflective-mutation operator, (3) LLM-as-Pareto-critic, (4) adaptive operator scheduler arbitrating LLM-vs-classical operators with cost-awareness, (5) semantic niching by NLP-embedding distance, (6) explicit language-mediated reflection feedback loop driving operator hints. Additionally (7) DDD-constraint encoding within NSGA-II constrained-dominance is new among search methods, and (8) typed-component-aware constraints are new among GA-family methods.

-----

## 7. Lineage map for SEMA-GA (consolidated, per step)

|Step            |Tag → Parent                                                                    |Justification                                                                             |
|----------------|--------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
|1 Input         |⊃ MSExtractor v2 / FoSCI                                                        |Static code + semantic, with optional dynamic traces (FoSCI) and DB edges (CARGO)         |
|1 Input         |NEW                                                                             |Fusion of LLM-readable summaries as first-class input substrate                           |
|2 Representation|≈ MSExtractor / FoSCI / So4MoD                                                  |Integer label-vector chromosome (partition encoding)                                      |
|2 Representation|NEW                                                                             |Dual numeric + LLM-readable textual cluster view (phenotype augmentation)                 |
|3 Seeding       |⊃ FoSCI                                                                         |Clustering warm-start tradition                                                           |
|3 Seeding       |⊃ MonoEmbed                                                                     |Embedding-based clustering warm-start                                                     |
|3 Seeding       |NEW                                                                             |LLM-proposed partition seeds as parallel seeding stream                                   |
|4 Variation     |≈ MSExtractor                                                                   |Classical crossover/mutation on label vectors                                             |
|4 Variation     |NEW                                                                             |Semantic crossover via LLM (concept-level parent merging)                                 |
|4 Variation     |NEW                                                                             |Reflective mutation via LLM (mutation conditioned on weakest objective + diagnostics)     |
|4 Variation     |NEW                                                                             |Adaptive operator scheduler arbitrating LLM-vs-classical with cost-aware UCB              |
|5 Fitness       |⊃ FoSCI / MSExtractor v2                                                        |CHM, CHD, CBM, SMQ, IFN, OPN, NED                                                         |
|5 Fitness       |⊃ MonoEmbed                                                                     |Semantic coherence via embedding similarity                                               |
|5 Fitness       |NEW                                                                             |LLM-judged cluster coherence as objective; DDD-aware constraint encoding                  |
|6 Selection     |≈ NSGA-II (Deb 2002)                                                            |Non-dominated sorting + crowding distance                                                 |
|6 Selection     |⊃ NSGA-III (Deb & Jain 2014)                                                    |Reference-point selection for ≥4 objectives                                               |
|6 Selection     |NEW                                                                             |Semantic niching in cluster-summary embedding space                                       |
|6 Selection     |NEW                                                                             |LLM Pareto critic as auxiliary tiebreaker                                                 |
|7 Output        |≈ FoSCI / MSExtractor                                                           |Pareto front + knee point                                                                 |
|7 Output        |NEW                                                                             |Per-candidate LLM rationale, typed components, critic notes                               |
|8 Feedback      |NEW vs all 4 GA parents (MSExtractor, FoSCI, So4MoD, MB-GA — none have feedback)|Explicit language-mediated reflection loop with operator-hint injection across generations|

-----

## 8. Key URLs / DOIs (primary citations)

|# |Method              |DOI / URL                                                                          |
|--|--------------------|-----------------------------------------------------------------------------------|
|1 |MonoEmbed           |arXiv:2502.04604 ; DOI 10.1007/s10664-025-10732-z                                  |
|2 |MicroDec            |ResearchGate 386345028                                                             |
|3 |Systematic LLM      |DOI 10.1007/978-981-96-7238-7_10                                                   |
|4 |Pattern-Driven-ML   |DOI 10.1007/978-981-95-5012-8_16                                                   |
|5 |Domain Aligned      |DOI 10.1145/3717383.3717396                                                        |
|6 |Stojanović 2023     |https://ebt.rs/journals/index.php/conf-proc/article/view/181                       |
|7 |MSExtractor v1      |DOI 10.1007/978-3-030-33702-5_5                                                    |
|7 |MSExtractor v2      |DOI 10.1016/j.infsof.2022.106996                                                   |
|8 |FoSCI               |DOI 10.1109/TSE.2019.2956525 ; github.com/wj86/FoSCI                               |
|9 |So4MoD              |DOI 10.1002/smr.2670 ; github.com/fengyingzi/So4MoD                                |
|10|MB-GA               |DOI 10.1109/ACCESS.2021.3106342                                                    |
|10|SEMGROMI            |DOI 10.7717/peerj-cs.1380                                                          |
|11|Service Cutter      |DOI 10.1007/978-3-319-44482-6_12                                                   |
|12|Mono2Micro          |DOI 10.1145/3468264.3473915 ; arXiv:2107.09698                                     |
|13|Context Mapper      |DOI 10.5220/0008910502990306 ; DOI 10.1007/978-3-030-67445-8_11 ; contextmapper.org|
|14|Domain Aligned (DDD)|DOI 10.1145/3717383.3717396                                                        |
|15|adesso in|FOCUS     |DOI 10.1109/ICSA-C50368.2020.00009 ; arXiv:2003.02603                              |
|16|SRME (best match)   |DOI 10.1109/REW61692.2024.00031 ; arXiv:2207.04586 (PF4Microservices)              |
|17|Feature Table       |DOI 10.1145/3457913.3457939 ; arXiv:2105.07157                                     |
|18|CARGO               |DOI 10.1145/3551349.3556960 ; arXiv:2207.11784                                     |
|19|MAGNET              |DOI 10.1109/ICSA59870.2024.00009 ; github.com/magnetmicro/MAGNET                   |
|20|CO-GCN              |arXiv:2102.03827 ; github.com/utkd/cogcn                                           |
|21|RLDec               |DOI 10.1007/s10664-024-10547-4 ; github.com/khaledsellami/decomp-rldec             |
|22|SEMA-GA             |(unpublished; user is author)                                                      |

-----

## 9. Items to confirm with the user before finalizing the artifact

1. **SRME acronym:** confirm the originating paper. If it is Bu et al. REW 2024, the title is “Sub-Requirement References in Problem Diagrams” — SRME as “Sub-Requirement-based Microservice Extraction” is plausible shorthand but not literally in the paper.
2. **MicroDec author:** correct from “Alsayed & Benomar” → “Alsayed, Dam & Nguyen (University of Wollongong)”.
3. **CO-GCN expansion:** correct from “Constraint-Oriented” → “Clustering and Outlier-aware”. The Desai et al. AAAI 2021 paper uses Clustering-and-Outlier-aware.
4. **CHM expansion:** Jin et al. canonical form is “Cohesion at Message level”; many surveys paraphrase as “Method level”. Pick one and footnote.
5. **SEMA-GA itself:** confirmed not yet in the literature — the lineage analysis above positions it as the first to compose LLM-as-operator with NSGA-II/III Pareto search + explicit reflection feedback for monolith decomposition.