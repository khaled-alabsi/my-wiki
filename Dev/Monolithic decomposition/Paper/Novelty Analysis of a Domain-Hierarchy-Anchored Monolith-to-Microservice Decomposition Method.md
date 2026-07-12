# Novelty and Related-Work Analysis — Consolidated Monolith-to-Microservice Decomposition Method

This analysis extends the prior 22-method survey and the prior novelty reviews. It is structured as paper-writing infrastructure: every closest-prior-art entry includes citation-ready bibliographic detail, every novelty verdict comes with sharpening suggestions, and every element provides a ready-to-paste contrast snippet for the related-work section.

-----

## PART A — NOVELTY ANALYSIS PER ELEMENT

### E1 — Unified multi-trigger action-point primitive

**What it is.** REST, SOAP, scheduler, batch, MQ, GraphQL, gRPC, CLI, and webhook entry points are treated as siblings of one “action-point” abstraction.

**Closest prior art.**

- Mazlami, G., Cito, J., & Leitner, P. (2017). *Extraction of Microservices from Monolithic Software Architectures.* ICWS 2017, pp. 524–531. DOI: https://doi.org/10.1109/ICWS.2017.61. Coupling-graph extraction from a monolith; no explicit trigger abstraction.
- Baresi, L., Garriga, M., & De Renzis, A. (2017). *Microservices Identification through Interface Analysis.* ESOCC 2017, LNCS 10465, pp. 19–33. DOI: https://doi.org/10.1007/978-3-319-67262-5_2. REST/OpenAPI only.
- Kalia, A. K., Xiao, J., Krishna, R., Sinha, S., Vukovic, M., & Banerjee, D. (2021). *Mono2Micro.* ESEC/FSE ’21, pp. 1214–1224. DOI: https://doi.org/10.1145/3468264.3473915. Mono2Micro verbatim: it “dynamically collects runtime traces under the execution of specific business use cases of the application”  — the trigger primitive is user-defined business use cases executed at runtime; non-HTTP trigger families (scheduler, MQ, CLI, batch) are out of scope.

**Verdict: PARTIALLY NOVEL.** OWL-S already models heterogeneous service invocations uniformly at the description level, but no decomposition pipeline we found commits to nine trigger types simultaneously as one primitive.

**Sharpening.** (1) Tabulate trigger-family coverage for FoSCI/Mono2Micro/CARGO/MAGNET/MicroDec; show none cover all nine. (2) Argue scheduler/batch/MQ/CLI triggers are systematically excluded by use-case-based (FoSCI, Mono2Micro), graph-based (MAGNET, CARGO), and embedding-based (MonoEmbed, MicroDec) prior work. (3) Include a coverage matrix as a paper figure.

**For-paper snippet.** “Existing pipelines anchor on a single trigger family — runtime traces of business use cases [Kalia et al. 2021], OpenAPI endpoints [Baresi et al. 2017], execution traces [Jin et al. 2019] or static call graphs [Trabelsi et al. 2024 — MAGNET]. We treat REST, SOAP, scheduler, batch, MQ, GraphQL, gRPC, CLI, and webhook entries as instances of one *action-point* primitive, making batch and scheduled pipelines (typical of enterprise monoliths) first-class citizens of decomposition.”

-----

### E2 — Deterministic per-trigger full-chain extraction (config, data sources, queues, external calls)

**Closest prior art.**

- Nitin, V., Asthana, S., Ray, B., & Krishna, R. (2022). *CARGO: AI-Guided Dependency Analysis.* ASE ’22, Article 20, 12 pp. DOI: https://doi.org/10.1145/3551349.3556960. Flow-sensitive system dependency graph with DB tables.
- Mathai, A., Bandyopadhyay, S., Desai, U., & Tamilselvam, S. G. (2022). *Monolith to Microservices: Heterogeneous GNN* (CHGNN). IJCAI-22, pp. 3905–3911. DOI: https://doi.org/10.24963/ijcai.2022/542. Heterogeneous graph with program + resource nodes.
- Romani, Y., Tibermacine, O., & Tibermacine, C. (2022). *Data-Centric Microservice Identification.* ICSA-C 2022, pp. 15–19.

**Verdict: PARTIALLY NOVEL.** Per-trigger chain including config, queues, and external calls is fuller than CARGO/CHGNN’s DB-only resource graph.

**Sharpening.** (1) Be precise about parsed artifact types (annotations, XML, YAML, properties, scheduler descriptors, Spring/Quartz/JMS config). (2) Position as “resource-aware program slicing per entry point” rather than “static analysis.” (3) Quantify added resource coverage vs. CARGO on a benchmark.

**For-paper snippet.** “CARGO [Nitin et al. 2022] and CHGNN [Mathai et al. 2022] enrich monolith graphs with database tables; we extend this resource graph to scheduler triggers, MQ topics, REST/SOAP clients, and CLI invocations, yielding a per-action-point chain that captures the full I/O surface of each entry point.”

-----

### E3 — Graph extraction hardening pipeline (fix_extractor vs hardcode_patch + confidence-triaged human review)

**Closest prior art.**

- Sellami, K., & Saied, M. A. (2025). *MonoEmbed.* Empirical Software Engineering 31, Art. 11. DOI: https://doi.org/10.1007/s10664-025-10732-z. LLM-based code embeddings; no extractor validation loop.
- Marin, M., van Deursen, A., & Moonen, L. (2007). *Identifying Crosscutting Concerns Using Fan-in Analysis.* ACM TOSEM 17(1), Art. 3, 37 pp. DOI: https://doi.org/10.1145/1314493.1314496. Semi-automated aspect mining with human validation.

**Verdict: NOVEL.** The fix_extractor vs hardcode_patch dichotomy — forcing the LLM to choose between *patching the extractor* and *patching this one case* — is, to our knowledge, absent from published microservice-decomposition literature and from LLM-as-extractor-auditor SE work.

**Sharpening.** (1) Frame as “LLM-as-extractor-auditor with bias toward upstream fixes.” (2) Track fix_extractor : hardcode_patch ratio as a quality KPI over iterations. (3) Compare against pure deterministic extraction error rates on a labeled benchmark.

**For-paper snippet.** “Recent LLM-augmented program analysis [Sellami & Saied 2025; Trabelsi et al. 2024 — MicroDec] treats the LLM as a *feature provider*. We instead use it as an *extractor auditor*, with a structured fix_extractor vs hardcode_patch dichotomy that pushes systemic gaps back into the deterministic extractor rather than papering over individual errors.”

-----

### E4 — Three-level hierarchical tagging on services AND data sources with controlled vocabulary

**Closest prior art.**

- Gysel, M., Kölbener, L., Giersche, W., & Zimmermann, O. (2016). *Service Cutter.* ESOCC 2016, LNCS 9846, pp. 185–200. DOI: https://doi.org/10.1007/978-3-319-44482-6_12. Verbatim from §3: “Figure 2 lists the 16 Coupling Criteria (CC) in the final catalog version”  organized “in four categories”;  Cohesiveness is “category 1: criteria describing certain common properties of mutually related nanoentities that justify why these nanoentities should belong to the same service.”  The 16 criteria are grouped but each criterion is itself flat — no L1/L2/L3 sub-hierarchy.
- Martin, D., et al. (2004). *OWL-S: Semantic Markup for Web Services.* W3C Member Submission, 22 November 2004. URL: https://www.w3.org/submissions/2004/SUBM-OWL-S-20041122/.  Service Profile vocabularies (UNSPSC, NAICS) classify services only.
- Roman, D., et al. (2005). *Web Service Modeling Ontology.* Applied Ontology 1(1), 77–106.

**Verdict: PARTIALLY NOVEL.** Novelty is (1) *symmetric* L1/L2/L3 hierarchies over services AND data sources, (2) tags as first-class controlled vocabularies the algorithm reads directly, (3) the same schema reused across both.

**Sharpening.** (1) Quote Service Cutter’s 16 criteria explicitly to show they are flat. (2) Note OWL-S Profile vocabularies do not address data sources. (3) Ship the vocabularies as a reusable enterprise artifact.

**For-paper snippet.** “Service Cutter [Gysel et al. 2016] organises 16 flat coupling criteria into four categories without a tag sub-hierarchy; semantic-web service catalogs [Martin et al. 2004; Roman et al. 2005] classify services against fixed flat taxonomies (UNSPSC, NAICS) but do not cover data sources. We tag services and data sources with the same three-level taxonomy drawn from one controlled inventory, enabling cross-hierarchy alignment scoring.”

-----

### E5 — Structured RESPONSIBILITY RECORD (action_verb + object + description + I/O + data_sources_touched + tags)

**Closest prior art.**

- Martin, D., et al. (2004). *OWL-S* (cited above). The Process Model (§5) defines atomic processes via inputs, outputs, preconditions, effects (“IOPEs”). Verbatim §5.1: *“it’s necessary to explain how inputs, outputs, preconditions, and effects (colloquially known as IOPEs) work.”* 
- Roman, D., et al. (2005). *WSMO* — capability descriptions with assumptions, preconditions, postconditions, effects.
- Jacobson, I., Christerson, M., Jonsson, P., & Övergaard, G. (1992). *Object-Oriented Software Engineering: A Use Case Driven Approach.* ACM Press / Addison-Wesley. ISBN 0-201-54435-0. Actor-verb-object use-case form.
- Iyer, S., Konstas, I., Cheung, A., & Zettlemoyer, L. (2016). *Summarizing Source Code Using a Neural Attention Model.* ACL 2016, pp. 2073–2083. DOI: https://doi.org/10.18653/v1/P16-1195. Neural code summarization — *free-text only*.
- Mernik, M., Heering, J., & Sloane, A. M. (2005). *When and How to Develop Domain-Specific Languages.* ACM CSUR 37(4), 316–344. DOI: https://doi.org/10.1145/1118890.1118892.

**Verdict: PARTIALLY NOVEL.** The schema is parallel to OWL-S atomic processes and Jacobson use cases. What is new: (a) using such records *inside* a decomposition algorithm as the unit of redundancy detection, tag enrichment, contamination scoring, and judge prompting; (b) maintaining `action_verb` and `object` as *evolving controlled vocabularies* the LLM judge refines during iteration; (c) prior microservice-decomposition work uses no such records — it clusters classes or methods.

**Sharpening.** (1) Be explicit that the record is an IOPE-style descriptor extended with `data_sources_touched` and three-level tags. (2) Justify the verb+object split by referencing Jacobson use-cases and linguistic-frame semantics. (3) Show how the record makes the three-stage redundancy detection (E10) tractable.

**For-paper snippet.** “The responsibility record extends OWL-S’s IOPE pattern [Martin et al. 2004] and Jacobson’s actor-verb-object form [Jacobson et al. 1992] with `data_sources_touched` and three-level tags. Unlike semantic-web service catalogs — which are static descriptors for discovery — our records are *operational inputs* to a deterministic decomposition algorithm, and the (action_verb, object) pair forms the second key of three-stage redundancy detection.”

-----

### E6 — Microservice-level domain hierarchy as PREDEFINED CLUSTERING SKELETON

**Closest prior art.**

- Wagstaff, K., Cardie, C., Rogers, S., & Schroedl, S. (2001). *Constrained K-means Clustering with Background Knowledge.* ICML 2001, pp. 577–584.   Morgan Kaufmann. ACM DL: https://dl.acm.org/doi/10.5555/645530.655669. Pairwise must-link/cannot-link.  
- Basu, S., Banerjee, A., & Mooney, R. J. (2002). *Semi-supervised Clustering by Seeding.* ICML 2002, pp. 19–26.  PDF: https://www.cs.utexas.edu/~ml/papers/semi-icml-02.pdf. Seed sets as cluster anchors.
- Chatziafratis, V., Niazadeh, R., & Charikar, M. (2018). *Hierarchical Clustering with Structural Constraints.* ICML 2018, PMLR 80, pp. 774–783. arXiv: https://arxiv.org/abs/1805.09476. Provable HC with triplet constraints. 
- Shen, J., Wu, Z., Lei, D., Shang, J., Ren, X., & Han, J. (2022). *Seeded Hierarchical Clustering for Expert-Crafted Taxonomies* (HierSeed). arXiv: https://arxiv.org/abs/2205.11602. User-defined topic hierarchy with seeds   — but forces every taxonomy node to be populated.
- Ma, X., Dhulipala, L., & Konwar, K. (2018). *Hierarchical Clustering with Prior Knowledge.* arXiv: https://arxiv.org/abs/1806.03432. Penalty terms encoding external taxonomies in linkage HC. 
- Meng, Y., Zhang, Y., Huang, J., Zhang, Y., Zhang, C., & Han, J. (2020). *Hierarchical Topic Mining via Joint Spherical Tree and Text Embedding.* KDD 2020, pp. 1908–1917. DOI: https://doi.org/10.1145/3394486.3403242.

**Verdict: PARTIALLY NOVEL.** The novelty lies in the structural specification: cluster nodes may hold zero/one/many microservices, and interior nodes may stay empty. Most seeded HC literature (including HierSeed) assumes one cluster per leaf and forces every node populated.

**Sharpening.** (1) Position explicitly as “seeded hierarchical clustering with a structural skeleton that admits empty and multi-occupancy nodes.” (2) Cite HierSeed as the closest analogue and note its leaf-per-cluster assumption. (3) Argue empty-node-allowed matches enterprise reality — domain catalogs are aspirationally complete, partially instantiated.

**For-paper snippet.** “Constrained and seeded hierarchical clustering [Wagstaff et al. 2001; Basu et al. 2002; Chatziafratis et al. 2018; Shen et al. 2022] inject prior structure as pairwise constraints, seed points, or triplet relations. We treat the enterprise domain catalog as a complete clustering *skeleton* — an L1–L4 cluster tree where every interior node is a legal placement, multi-occupancy is allowed, and empty nodes are first-class — matching how enterprise capability maps are authored.”

-----

### E7 — Cascading initial assignment (package depth → service L1+L2 tags → data-source L1+L2 tags), tag-coherence-driven depth, tag-diversity size threshold, placement at minimum-contamination domain node

**Closest prior art.**

- Mitchell, B. S., & Mancoridis, S. (2006). *On the Automatic Modularization of Software Systems Using the Bunch Tool.* IEEE TSE 32(3), 193–208.  DOI: https://doi.org/10.1109/TSE.2006.31. Package-cohesion clustering precursor.
- Jin, W., Liu, T., Cai, Y., Kazman, R., Mo, R., & Zheng, Q. (2019). *FoSCI.* IEEE TSE. DOI: https://doi.org/10.1109/TSE.2019.2910531. Three-step “atom → cluster” pipeline using execution traces. 
- Mazlami, G., Cito, J., & Leitner, P. (2017). *Extraction of Microservices* (cited above).
- Kalia, A. K., et al. (2021). *Mono2Micro* (cited above). Hierarchical agglomerative spatio-temporal clustering. 

**Verdict: NOVEL** for the *specific* combination: (a) initial cut by action-point package depth chosen to *maximize tag coherence* (not LOC or class count); (b) tag-diversity threshold (> N distinct L1 OR > M distinct L2 tags) as the size criterion; (c) placement at the domain-hierarchy node *minimizing tag tree-edit-distance contamination*. No microservice-decomposition paper we found uses tag-diversity as a splitting predicate.

**Sharpening.** (1) Give the precise tag-diversity formula with default thresholds. (2) Empirical comparison against Mono2Micro’s dendrogram-cut threshold on a benchmark — show tag-diversity cuts produce more semantically coherent seeds. (3) Ablation: replacing tag-diversity with class count still works but produces worse coherence/contamination trade-offs.

**For-paper snippet.** “Existing seeding strategies cut by class count [Mitchell & Mancoridis 2006], dendrogram threshold [Kalia et al. 2021], or trace-atom grouping [Jin et al. 2019]; we cut by *tag diversity* and choose package depth to maximise L1+L2 tag coherence, then place each group at the domain node minimising tag tree-edit-distance contamination.”

-----

### E8 — CONTAMINATION score: tag tree-edit-distance to microservice domain path, depth-weighted with w > 1

**Closest prior art.**

- Bertinetto, L., Mueller, R., Tertikas, K., Samangooei, S., & Lord, N. A. (2020). *Making Better Mistakes: Leveraging Class Hierarchies with Deep Networks.* CVPR 2020, pp. 12506–12515 (CVF Open Access).  DOI: https://doi.org/10.1109/CVPR42600.2020.01252. arXiv: https://arxiv.org/abs/1912.09393. Verbatim: *“The hierarchical distance of a mistake is the height of the lowest common ancestor (LCA) between the ground truth and the predicted class when the input is misclassified.”* 
- Silla Jr., C. N., & Freitas, A. A. (2011). *A Survey of Hierarchical Classification across Different Application Domains.* Data Mining and Knowledge Discovery 22(1–2), 31–72. DOI: https://doi.org/10.1007/s10618-010-0175-9. 
- Kosmopoulos, A., Partalas, I., Gaussier, E., Paliouras, G., & Androutsopoulos, I. (2015). *Evaluation Measures for Hierarchical Classification.* DMKD 29(3), 820–865. DOI: https://doi.org/10.1007/s10618-014-0382-x.
- Cesa-Bianchi, N., Gentile, C., & Zaniboni, L. (2006). *Incremental Algorithms for Hierarchical Classification.* JMLR 7, 31–54.
- Tai, K.-C. (1979). *The Tree-to-Tree Correction Problem.* JACM 26(3), 422–433. DOI: https://doi.org/10.1145/322139.322143.

**Verdict: PARTIALLY NOVEL.** Geometric depth-weighting (w^(max_depth−i)) is well within the hierarchical-classification literature. The novelty is applying it as a *clustering-quality score against a predefined skeleton placement path* (rather than against a ground-truth label), with three contamination sources (services, data sources, action points) summed and reported separately for diagnostic purposes.

**Sharpening.** (1) Acknowledge Bertinetto et al.’s LCA-height loss explicitly; differentiate by emphasising contamination is computed against a *placement* path, not a label. (2) Sensitivity analysis on w (default 3). (3) Show three-source decomposition is diagnostic, not merely aggregative — for example, high data-source contamination but low service contamination flags a data-ownership refactor, not a service refactor.

**For-paper snippet.** “Depth-weighted hierarchical penalties are standard in classification [Bertinetto et al. 2020; Silla & Freitas 2011; Cesa-Bianchi et al. 2006]; the underlying tree-edit-distance is due to Tai (1979). We adapt these to clustering quality by computing, for each component in a microservice, the depth-weighted distance from its tag path to the microservice’s domain placement path, and we decompose contamination by source (service, data-source, action-point) to drive specific E11 refactorings.”

-----

### E9 — COHERENCE score (cross-hierarchy alignment, IDF-weighted L3 matches, data exclusivity, transactional integrity, write-access patterns)

**Closest prior art.**

- Gysel, M., et al. (2016). *Service Cutter* (cited above) — Same Owner, Latency, Consistency Critical, Identity & Lifecycle and 12 other criteria.
- Jin, W., et al. (2019). *FoSCI* (cited above) — execution-trace functional cohesion.
- Mitchell, B. S., & Mancoridis, S. (2006). *Bunch* (cited above) — Modularization Quality (MQ) trade-off of inter- vs intra-cluster edges. 
- Nitin, V., et al. (2022). *CARGO* (cited above) — transaction-aware partitioning to avoid distributed transactions. 
- Salton, G., & Buckley, C. (1988). *Term-Weighting Approaches in Automatic Text Retrieval.* IPM 24(5), 513–523. DOI: https://doi.org/10.1016/0306-4573(88)90021-0. IDF foundation.

**Verdict: PARTIALLY NOVEL.** The individual components (cohesion, transaction integrity, data exclusivity) appear in Service Cutter / CARGO / Bunch. The novelty is the *positive* framing (coherence as reward, not penalty), IDF weighting of L3-tag matches (rare-tag agreement is more meaningful than common-tag agreement), and the joint inclusion of write-access patterns with cross-hierarchy alignment in a single score.

**Sharpening.** (1) Show L3-tag IDF weighting mitigates a known pathology of flat criteria (high-frequency tags dominating). (2) Validate that coherence and contamination are not redundant — they decouple under realistic perturbations. (3) Per-sub-component ablation.

**For-paper snippet.** “Bunch’s MQ [Mitchell & Mancoridis 2006] rewards intra-cluster edges; Service Cutter [Gysel et al. 2016] enumerates 16 coupling criteria; CARGO [Nitin et al. 2022] adds transaction awareness. Our coherence score unifies these into a positive-direction signal that IDF-weights rare L3-tag matches [following Salton & Buckley 1988] and rewards data-source exclusivity and write-access locality jointly.”

-----

### E10 — REDUNDANCY score with three-stage detection and four-path resolution including DDD-justified duplication

**Closest prior art.**

- Roy, C. K., Cordy, J. R., & Koschke, R. (2009). *Comparison and Evaluation of Code Clone Detection Techniques and Tools.* Science of Computer Programming 74(7), 470–495. DOI: https://doi.org/10.1016/j.scico.2009.02.007. Type-1/2/3/4 clone taxonomy.
- Sajnani, H., Saini, V., Svajlenko, J., Roy, C. K., & Lopes, C. V. (2016). *SourcererCC: Scaling Code Clone Detection to Big-Code.* ICSE 2016, pp. 1157–1168. DOI: https://doi.org/10.1145/2884781.2884877.
- White, M., Tufano, M., Vendome, C., & Poshyvanyk, D. (2016). *Deep Learning Code Fragments for Code Clone Detection.* ASE 2016, pp. 87–98. DOI: https://doi.org/10.1145/2970276.2970326. Embedding-based Type-4 detection.
- Evans, E. (2003). *Domain-Driven Design.* Addison-Wesley. ISBN 0-321-12521-5. Bounded Context and Anti-Corruption Layer. 
- Vernon, V. (2013). *Implementing Domain-Driven Design.* Addison-Wesley. ISBN 0-321-83457-7. ACL operational forms.
- Newman, S. (2015/2021). *Building Microservices.* O’Reilly. ISBN 978-1-491-95035-7 (1st) / 978-1-492-03402-5 (2nd). Endorses cross-context duplication.
- Marin, M., van Deursen, A., & Moonen, L. (2007). *Identifying Crosscutting Concerns Using Fan-in Analysis.* ACM TOSEM (cited above).

**Verdict: NOVEL** in combination. Three-stage detection (literal class ID → structured (action_verb, object) → semantic description-embedding cosine) maps cleanly onto Type-1 → structured Type-2/3 → Type-4. The four-path resolution — and especially the *whitelisted-reason* taxonomy for ACCEPT (DDD bounded-context replication, operational independence, anti-corruption layer, latency-critical) — is not present in published microservice-decomposition literature, which treats duplicates as unconditional refactoring targets.

**Sharpening.** (1) State explicitly this is the first decomposition method to formalize *intentional* duplication via a closed whitelist. (2) Tie each whitelisted reason to a citation (DDD bounded-context replication → Evans 2003; ACL → Evans 2003 / Vernon 2013; operational independence → Newman 2015; latency-critical → data-locality literature). (3) Provide an example where Lift-to-Shared would have hurt (e.g., a payment-idempotency check legitimately duplicated to keep checkout latency-critical).

**For-paper snippet.** “Clone detection is mature [Roy & Cordy 2009; Sajnani et al. 2016; White et al. 2016] and crosscutting-concern identification is well established [Marin et al. 2007]. Microservice decomposition methods, however, treat duplicates as unconditional candidates for promotion to a shared module. We instead allow ACCEPT-with-justified-reason — drawing on Evans’s bounded-context replication [Evans 2003], Vernon’s ACL forms [Vernon 2013], and Newman’s microservice-independence principle [Newman 2015] — operationalised as a closed-set whitelist of four reasons.”

-----

### E11 — Six-step iteration cycle (Detect → Identify → Search → Propose → Judge → Apply) with four operations (Move / Split / Merge / Lift-to-Shared)

**Closest prior art.**

- Mancoridis, S., Mitchell, B. S., Rorres, C., Chen, Y.-F., & Gansner, E. R. (1998). *Using Automatic Clustering to Produce High-Level System Organizations of Source Code.* IWPC 1998, pp. 45–52.  DOI: https://doi.org/10.1109/WPC.1998.693283.
- Mancoridis, S., Mitchell, B. S., Chen, Y.-F., & Gansner, E. R. (1999). *Bunch: A Clustering Tool for the Recovery and Maintenance of Software System Structures.* ICSM 1999, pp. 50–59.  DOI: https://doi.org/10.1109/ICSM.1999.792498.
- Mitchell, B. S., & Mancoridis, S. (2006). *Bunch — TSE version* (cited above).
- Mahdavi, K., Harman, M., & Hierons, R. M. (2003). *A Multiple Hill Climbing Approach to Software Module Clustering.* ICSM 2003, pp. 315–324. DOI: https://doi.org/10.1109/ICSM.2003.1235437.
- Tsantalis, N., & Chatzigeorgiou, A. (2009). *Identification of Move Method Refactoring Opportunities.* IEEE TSE 35(3), 347–367. DOI: https://doi.org/10.1109/TSE.2009.1 (JDeodorant).
- Praditwong, K., Harman, M., & Yao, X. (2011). *Software Module Clustering as a Multi-Objective Search Problem.* IEEE TSE 37(2), 264–282. DOI: https://doi.org/10.1109/TSE.2010.26.

**Verdict: PARTIALLY NOVEL.** Hill-climbing software clustering with Move-class is exactly Bunch;  JDeodorant adds Move-Method/Extract-Class. What is new: (a) the operation set including *Lift-to-Shared* (refactoring to cross-cutting / shared kernel rather than to a peer); (b) trie-lookup of LCA depth in the domain hierarchy as the *candidate generator*; (c) the deterministic-Propose → LLM-Judge → Apply discipline with whitelisted overrides and per-iteration budget.

**Sharpening.** (1) Frame as “hill-climbing with hierarchical neighborhood structure”; contrast against Bunch’s flat neighborhood. (2) Quantify that LCA-depth-bounded search prunes the move space by orders of magnitude vs. a flat neighborhood. (3) Make the per-iteration budget (K microservices, M moves, ≤1 split or merge) an explicit human-controllable knob.

**For-paper snippet.** “Bunch [Mancoridis et al. 1998, 1999; Mitchell & Mancoridis 2006] and multiple-hill-climbing variants [Mahdavi et al. 2003] perform local search over module assignments with Move operations and a flat neighborhood; JDeodorant [Tsantalis & Chatzigeorgiou 2009] adds Move-Method and Extract-Class. We extend this to four operations — including Lift-to-Shared — restrict the neighborhood to LCA-bounded paths in the domain hierarchy, and introduce a deterministic-Propose / LLM-Judge / Apply discipline that gives auditable provenance per move.”

-----

### E12 — Human-in-the-loop in the ITERATION ITSELF with three modes

**Closest prior art.**

- Bavota, G., Carnevale, F., De Lucia, A., Di Penta, M., & Oliveto, R. (2012). *Putting the Developer in-the-Loop: An Interactive GA for Software Re-Modularization.* SSBSE 2012, LNCS 7515, pp. 75–89.  DOI: https://doi.org/10.1007/978-3-642-33119-0_7.
- Wagstaff, K., Cardie, C., Rogers, S., & Schroedl, S. (2001). *Constrained K-means with Background Knowledge* (cited above).
- Settles, B. (2009). *Active Learning Literature Survey.* CS Tech Report 1648, University of Wisconsin–Madison. URL: http://burrsettles.com/pub/settles.activelearning.pdf.
- Amershi, S., Cakmak, M., Knox, W. B., & Kulesza, T. (2014). *Power to the People: The Role of Humans in Interactive Machine Learning.* AI Magazine 35(4), 105–120. DOI: https://doi.org/10.1609/aimag.v35i4.2513.
- Bae, J., et al. (2017). *A Method to Accelerate Human-in-the-Loop Clustering.* SIAM SDM 2017. Refine-and-lock interaction model. 
- Bae, J., et al. (2020). *Interactive Clustering: A Comprehensive Review.* ACM CSUR 53(1), Article 4. DOI: https://doi.org/10.1145/3340960.

**Verdict: PARTIALLY NOVEL.** Interactive software re-modularization (Bavota et al. 2012) and interactive clustering with must-link/cannot-link (Wagstaff et al. 2001) are precedents. The novelty is the *typology of human signals* tailored to microservice decomposition: forced-together, forced-apart, anchor data sources, ignored data sources, new domain hierarchy nodes, tag overrides, and *domain rules* (e.g., “all services touching customers_pii must live in customer/data-privacy”) — the last being *policy-as-constraint* not present in prior interactive clustering. The three-mode separation (passive review, active rule injection, escalation) is also a typology contribution.

**Sharpening.** (1) Cite Bavota’s interactive GA explicitly as the closest analogue and differentiate by the rule taxonomy. (2) Quantify reviewer burden management (delta-only views, time-boxing, auto-approve high-confidence) as a usability contribution. (3) Provide a concrete example where a single policy rule propagates across many components in one iteration.

**For-paper snippet.** “Interactive software clustering [Bavota et al. 2012] and human-in-the-loop clustering more broadly [Amershi et al. 2014; Wagstaff et al. 2001; Bae et al. 2020] support pairwise constraints and developer feedback. We extend this with (a) a three-mode interaction typology — passive per-iteration review, active inter-iteration rule injection, rare mid-iteration escalation — and (b) a rule taxonomy specific to microservice decomposition, including *policy-as-constraint* domain rules that propagate over many components in a single rule.”

-----

## PART B — OVERALL SYNTHESIS

### B1. Strongest 2–3 paper-anchor novelty claims

**Anchor 1 — Domain hierarchy as clustering skeleton with empty/multi-occupancy nodes, refined by deterministic triple-score (contamination + coherence + redundancy) iteration.**

*Why it’s strongest.* This is the structural commitment of the method: replacing both population-search optimization (Bunch GA; FoSCI uses a genetic algorithm per Kalia et al. 2021)  and opaque embedding clustering (MonoEmbed, MAGNET, CO-GCN) with a *single* skeleton-constrained clustering whose quality is measured by interpretable, deterministic scores. The combination — predefined hierarchical skeleton + interpretable triple scoring + single solution — is novel in the decomposition literature.

*What it supersedes.* Search-based modularization [Mitchell & Mancoridis 2006; Jin et al. 2019 — FoSCI; Praditwong, Harman & Yao 2011]; embedding-based decomposition [Sellami & Saied 2025 — MonoEmbed; Trabelsi et al. 2024 — MAGNET; Desai et al. 2021 — CO-GCN]; seeded hierarchical clustering [Shen et al. 2022 — HierSeed; Chatziafratis et al. 2018].

*Suggested phrasing.* “We propose a domain-hierarchy-anchored decomposition that replaces population search and opaque embedding clusters with a *single* skeleton-constrained partition refined by three deterministic, interpretable scores — contamination (tree-edit-distance penalty), coherence (cross-hierarchy reward), and redundancy (three-stage clone detection with justified-duplication whitelist).”

**Anchor 2 — Structured responsibility record + three-stage redundancy detection with whitelisted intentional duplication.**

*Why it’s strongest.* The most defensibly *new* scoring component, crossing three literatures (semantic web services, code clone detection, DDD) and combining them in a way no prior decomposition method does. The responsibility record also enables the LLM judge to operate on a fixed-schema input rather than free-form code, which is itself a methodological contribution.

*What it supersedes.* Code-clone literature [Roy & Cordy 2009; Sajnani et al. 2016; White et al. 2016] (no notion of intentional duplication); DDD canon [Evans 2003; Vernon 2013; Newman 2015] (endorses duplication but does not operationalise it); OWL-S / WSMO [Martin et al. 2004; Roman et al. 2005] (describes services but not for decomposition).

*Suggested phrasing.* “We introduce a structured responsibility record — (action_verb, object, description, inputs/outputs, data_sources_touched, tags) — that doubles as a fixed-schema LLM-judge input and as the second key of three-stage redundancy detection (literal class ID → structured (verb, object) → semantic embedding), with four-path resolution including ACCEPT-as-justified under a closed whitelist of DDD-, operational-, ACL-, and latency-grounded reasons.”

**Anchor 3 — Six-step iteration cycle with hierarchical-neighborhood search and deterministic-Propose / LLM-Judge separation.**

*Why it’s a strong anchor.* It makes the LLM’s role precise and auditable: deterministic math drives the proposal, the LLM judges (with the ability to override under a whitelisted reason or propose vocabulary refinements), and the human supervises through three modes. This is a contribution to LLM-in-SE methodology, not just to decomposition.

*What it supersedes.* LLM-as-judge SE work [He et al. 2025; Wang et al. 2025] (LLM as the primary scorer); Bunch hill-climbing [Mitchell & Mancoridis 2006] (flat neighborhood, no LLM); interactive re-modularization [Bavota et al. 2012] (no formalised propose/judge/apply split).

*Suggested phrasing.* “We separate concerns in iterative refactoring: deterministic math proposes moves (with LCA-depth-bounded trie lookup over the domain hierarchy), an LLM judge confirms or overrides them under a whitelisted-reason discipline, and a human supervises through three explicit interaction modes — yielding auditable per-move provenance unavailable to LLM-judge-centric or pure search-based methods.”

### B2. Weakest 2–3 contributions — present as competent reuse

**Reuse 1 — E1 (multi-trigger action-point primitive).** Reasonable engineering, no fundamental algorithmic novelty. *Citation pattern:* “Building on entry-point-based decomposition [Baresi et al. 2017; Kalia et al. 2021] and on uniform service descriptions in semantic-web services [Martin et al. 2004], we treat nine trigger families as siblings of a single action-point primitive.”

**Reuse 2 — E4 (hierarchical tagging on services AND data sources).** Hierarchical tagging is standard; only the cross-services-and-data-sources symmetry is fresh. *Citation pattern:* “Building on hierarchical service classification [Martin et al. 2004; Roman et al. 2005] and on Service Cutter’s coupling-criteria catalog [Gysel et al. 2016], we apply a symmetric L1/L2/L3 schema across services and data sources from one controlled inventory.”

**Reuse 3 — E8 (contamination math).** Depth-weighted tree distance is straight from the hierarchical-classification literature; the application as a clustering-quality score against a skeleton placement path is the only twist. *Citation pattern:* “Building on depth-weighted hierarchical penalties [Bertinetto et al. 2020; Silla & Freitas 2011; Cesa-Bianchi et al. 2006] and on tree-edit-distance [Tai 1979], we score per-component contamination against the microservice’s domain placement path.”

### B3. Missing-novelty-lever suggestions

**Lever 1 — A convergence / Lyapunov argument for the iteration cycle.** State and prove that contamination is monotonically non-increasing under deterministic proposals, with LLM-judge overrides allowed only when they do not increase total score. This converts E11 into a “provably-improving local-search-with-judge” contribution that ICSE/FSE reviewers will value. The analysis cost is small (essentially a fitness invariant proof in the style of Mitchell & Mancoridis 2006) but the reviewer signal is large.

**Lever 2 — Treat the controlled vocabularies (action_verb, object, service tags, data-source tags) as a *measured* artifact.** Report (a) vocabulary growth rate per iteration, (b) refinement reversion rate — how often the LLM adds a tag/term that is later removed, (c) inter-rater consistency between two LLM judges and one human across borderline judgements. This converts the responsibility-record + judge loop from a methodological claim into a *quantitative* contribution and pre-emptively answers the reviewer question “is the LLM doing anything reliable?”

### B4. Top 5 reviewer objections (ICSE/FSE/ASE/EMSE/TSE/TOSEM)

1. *“The LLM judge is unreliable; demoting it to tertiary use does not make it sound.”* — **Rebuttal:** We use the LLM only when deterministic math is tied or borderline; we log every override with a whitelisted reason; we ablate by replacing the judge with a coin flip and report degradation. The judge is auditable, not load-bearing — replacing it with a coin flip should produce graceful degradation, not collapse.
1. *“The domain skeleton is the user’s; you’ve just moved the hard problem to skeleton design.”* — **Rebuttal:** We support LLM-inferred skeletons as fallback [Shen et al. 2022; Meng et al. 2020]. Empirically, large organizations have skeletons in hand already — for example, the BIAN Service Landscape v13.0 (BIAN e.V., 2025) defines roughly 326 service domains organised in a three-level Business Area → Business Domain → Service Domain hierarchy with 250 Semantic APIs, and the ArchiMate® 3.2 Specification (The Open Group, Document C226, October 2022, ISBN 1-957866-02-4) formalises a Motivation layer (Driver, Goal, Outcome, Principle, Requirement, Constraint, Stakeholder) reusable as a skeleton. The skeleton is a forcing-function for stakeholder alignment, not a defect of the method.
1. *“You replaced a population (Pareto front) with a single solution — you lost diversity.”* — **Rebuttal:** The skeleton plus the budgeted iteration already explores a constrained Pareto-frontier surrogate via the three deterministic scores; the audit log and (optional) k-snapshot retention preserves trace diversity for post-hoc analysis. Single-clustering is the right trade for interpretability and human-in-the-loop review — Bavota et al. (2012) document the human cost of opaque GA solutions.
1. *“Triple scoring with three knobs (w, IDF, whitelist) is a hyperparameter zoo.”* — **Rebuttal:** w defaults to 3 and sensitivity is reported (E8 sharpening); IDF is parameter-free; the whitelist is a closed set of four named reasons each grounded in cited DDD/operational literature. These are interpretable design parameters, not numerical regularizers tuned per-dataset.
1. *“How do you validate against ground-truth decompositions?”* — **Rebuttal:** Use the standard benchmark set used by CARGO [Nitin et al. 2022] and Mono2Micro [Kalia et al. 2021] — verbatim from CARGO: *“Daytrader: A Java EE7 application built around the paradigm of an online stock trading system; Plants: a simple Java EE 6 application which uses CDI managed beans, Java Server Faces (JSF), and Java Server Pages (JSP); AcmeAir: a Java web application for a fictitious airline company; JPetStore: a Java web application for a pet store where users shop for pets online. They contain 109, 33, 66, 37 and 82 classes respectively.”*  Report BCP/ICP/SM/IFN/NED [Kalia et al. 2021], MoJoFM [Tzerpos & Holt 1999], and precision/recall vs. ground-truth as MAGNET does; show separately how human accept-rate of proposed moves evolves over iterations.

-----

## PART C — CITATION-READY REFERENCE PACK

### C.1 Microservice decomposition

- Kalia, A. K., Xiao, J., Krishna, R., Sinha, S., Vukovic, M., & Banerjee, D. (2021). Mono2Micro: A Practical and Effective Tool for Decomposing Monolithic Java Applications to Microservices. *Proc. 29th ACM Joint European Software Engineering Conf. and Symposium on the Foundations of Software Engineering (ESEC/FSE ’21)*, Athens, Greece, August 23–28, 2021,  pp. 1214–1224. DOI: https://doi.org/10.1145/3468264.3473915. arXiv: https://arxiv.org/abs/2107.09698.
- Jin, W., Liu, T., Cai, Y., Kazman, R., Mo, R., & Zheng, Q. (2019). Service Candidate Identification from Monolithic Systems Based on Execution Traces (FoSCI). *IEEE Transactions on Software Engineering*. DOI: https://doi.org/10.1109/TSE.2019.2910531.
- Mazlami, G., Cito, J., & Leitner, P. (2017). Extraction of Microservices from Monolithic Software Architectures. *Proc. IEEE Int’l Conf. on Web Services (ICWS 2017)*,  Honolulu, HI, USA, June 25–30, 2017, pp. 524–531. DOI: https://doi.org/10.1109/ICWS.2017.61.
- Gysel, M., Kölbener, L., Giersche, W., & Zimmermann, O. (2016). Service Cutter: A Systematic Approach to Service Decomposition. *Proc. 5th European Conf. on Service-Oriented and Cloud Computing (ESOCC 2016)*, LNCS 9846, Vienna, Austria, September 5–7, 2016,  pp. 185–200. DOI: https://doi.org/10.1007/978-3-319-44482-6_12.
- Baresi, L., Garriga, M., & De Renzis, A. (2017). Microservices Identification through Interface Analysis. *Proc. 6th European Conf. on Service-Oriented and Cloud Computing (ESOCC 2017)*, LNCS 10465, pp. 19–33. DOI: https://doi.org/10.1007/978-3-319-67262-5_2.
- Nitin, V., Asthana, S., Ray, B., & Krishna, R. (2022). CARGO: AI-Guided Dependency Analysis for Migrating Monolithic Applications to Microservices Architecture. *Proc. 37th IEEE/ACM Int’l Conf. on Automated Software Engineering (ASE ’22)*, Rochester, MI, USA, October 10–14, 2022, Article 20, 12 pp.  DOI: https://doi.org/10.1145/3551349.3556960. arXiv: https://arxiv.org/abs/2207.11784.
- Mathai, A., Bandyopadhyay, S., Desai, U., & Tamilselvam, S. G. (2022). Monolith to Microservices: Representing Application Software through Heterogeneous Graph Neural Network (CHGNN). *Proc. 31st Int’l Joint Conf. on Artificial Intelligence (IJCAI-22)*,  Vienna, Austria, July 23–29, 2022, pp. 3905–3911. DOI: https://doi.org/10.24963/ijcai.2022/542. arXiv: https://arxiv.org/abs/2112.01317.
- Desai, U., Bandyopadhyay, S., & Tamilselvam, S. G. (2021). Graph Neural Network to Dilute Outliers for Refactoring Monolith Application (CO-GCN). *Proc. AAAI Conf. on Artificial Intelligence*,  35(1), pp. 72–80. DOI: https://doi.org/10.1609/aaai.v35i1.16079.
- Sellami, K., & Saied, M. A. (2025). MonoEmbed: Enhancing LLM Representations for Monolith to Microservices Decomposition through Contrastive Learning. *Empirical Software Engineering* 31, Article 11.  DOI: https://doi.org/10.1007/s10664-025-10732-z. arXiv: https://arxiv.org/abs/2502.04604.
- Trabelsi, I., et al. (2024). MAGNET: Method-based Approach using Graph Neural Network for Microservices Identification. *Proc. IEEE Int’l Conf. on Software Architecture (ICSA 2024)*, Research Papers Track. 
- Sellami, K., et al. (2024). MicroDec: Leveraging Large Language Models for Microservice Decomposition. ResearchGate preprint. URL: https://www.researchgate.net/publication/386345028.
- Romani, Y., Tibermacine, O., & Tibermacine, C. (2022). Towards Migrating Legacy Software Systems to Microservice-based Architectures: A Data-Centric Process for Microservice Identification. *Proc. ICSA-C 2022*, pp. 15–19.
- Levcovitz, A., Terra, R., & Valente, M. T. (2016). Towards a Technique for Extracting Microservices from Monolithic Enterprise Systems. arXiv: https://arxiv.org/abs/1605.03175.
- Taibi, D., & Systä, K. (2019). From Monolithic Systems to Microservices: A Decomposition Framework based on Process Mining. *CLOSER 2019*. DOI: https://doi.org/10.5220/0007755901530164.
- Chen, R., Li, S., & Li, Z. (2017). From Monolith to Microservices: A Dataflow-Driven Approach. *Proc. APSEC 2017*, pp. 466–475. DOI: https://doi.org/10.1109/APSEC.2017.53.
- Kapferer, S., & Zimmermann, O. (2020). Domain-driven Service Design — Context Modeling, Model Refactoring and Contract Generation (Context Mapper / CML). *SummerSoC 2020*, CCIS 1310, pp. 189–208. DOI: https://doi.org/10.1007/978-3-030-64846-6_11.
- Agarwal, S., Sinha, R., Sridhara, G., Das, P., Desai, U., Tamilselvam, S., Singhee, A., & Nakamuro, H. (2021). Monolith to Microservice Candidates using Business Functionality Inference. *Proc. ICWS 2021*, pp. 758–763. DOI: https://doi.org/10.1109/ICWS53863.2021.00104.

### C.2 LLM for software engineering

- He, J., Shi, J., Zhuo, T. Y., Treude, C., Sun, J., Xing, Z., Du, X., & Lo, D. (2025). From Code to Courtroom: LLMs as the New Software Judges. arXiv: https://arxiv.org/abs/2503.02246.
- Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2025). Can LLMs Replace Human Evaluators? An Empirical Study of LLM-as-a-Judge in Software Engineering. arXiv: https://arxiv.org/abs/2502.06193.
- Iyer, S., Konstas, I., Cheung, A., & Zettlemoyer, L. (2016). Summarizing Source Code Using a Neural Attention Model. *Proc. ACL 2016*, pp. 2073–2083. DOI: https://doi.org/10.18653/v1/P16-1195.
- Hou, X., et al. (2024). Large Language Models for Software Engineering: A Systematic Literature Review. *ACM Transactions on Software Engineering and Methodology*. DOI: https://doi.org/10.1145/3695988.

### C.3 Search-based / evolutionary SE (for what we DON’T do)

- Mancoridis, S., Mitchell, B. S., Rorres, C., Chen, Y.-F., & Gansner, E. R. (1998). Using Automatic Clustering to Produce High-Level System Organizations of Source Code. *Proc. 6th Int’l Workshop on Program Comprehension (IWPC 1998)*, Ischia, Italy, pp. 45–52.  DOI: https://doi.org/10.1109/WPC.1998.693283.
- Mancoridis, S., Mitchell, B. S., Chen, Y.-F., & Gansner, E. R. (1999). Bunch: A Clustering Tool for the Recovery and Maintenance of Software System Structures. *Proc. ICSM 1999*, pp. 50–59.  DOI: https://doi.org/10.1109/ICSM.1999.792498.
- Mitchell, B. S., & Mancoridis, S. (2006). On the Automatic Modularization of Software Systems Using the Bunch Tool. *IEEE Transactions on Software Engineering* 32(3), 193–208.  DOI: https://doi.org/10.1109/TSE.2006.31.
- Mitchell, B. S., & Mancoridis, S. (2008). On the Evaluation of the Bunch Search-Based Software Modularization Algorithm. *Soft Computing* 12(1), 77–93.  DOI: https://doi.org/10.1007/s00500-007-0218-3.
- Mahdavi, K., Harman, M., & Hierons, R. M. (2003). A Multiple Hill Climbing Approach to Software Module Clustering. *Proc. ICSM 2003*, pp. 315–324. DOI: https://doi.org/10.1109/ICSM.2003.1235437.
- Harman, M., Hierons, R., & Proctor, M. (2002). A New Representation and Crossover Operator for Search-Based Optimization of Software Modularization. *Proc. GECCO 2002*, pp. 1351–1358.
- Praditwong, K., Harman, M., & Yao, X. (2011). Software Module Clustering as a Multi-Objective Search Problem. *IEEE Transactions on Software Engineering* 37(2), 264–282.  DOI: https://doi.org/10.1109/TSE.2010.26.

### C.4 Constrained / semi-supervised / hierarchical clustering

- Wagstaff, K., Cardie, C., Rogers, S., & Schroedl, S. (2001). Constrained K-means Clustering with Background Knowledge. *Proc. 18th Int’l Conf. on Machine Learning (ICML 2001)*, Williamstown, MA, June 28 – July 1, 2001, pp. 577–584. Morgan Kaufmann.   ACM DL: https://dl.acm.org/doi/10.5555/645530.655669.
- Basu, S., Banerjee, A., & Mooney, R. J. (2002). Semi-supervised Clustering by Seeding. *Proc. 19th Int’l Conf. on Machine Learning (ICML 2002)*, Sydney, Australia, July 8–12, 2002, pp. 19–26.  PDF: https://www.cs.utexas.edu/~ml/papers/semi-icml-02.pdf.
- Basu, S., Bilenko, M., & Mooney, R. J. (2004). A Probabilistic Framework for Semi-Supervised Clustering. *Proc. KDD 2004*, pp. 59–68.  DOI: https://doi.org/10.1145/1014052.1014062.
- Chatziafratis, V., Niazadeh, R., & Charikar, M. (2018). Hierarchical Clustering with Structural Constraints. *Proc. ICML 2018*, PMLR 80, pp. 774–783. arXiv: https://arxiv.org/abs/1805.09476.
- Ma, X., Dhulipala, L., & Konwar, K. (2018). Hierarchical Clustering with Prior Knowledge. arXiv: https://arxiv.org/abs/1806.03432.
- Shen, J., Wu, Z., Lei, D., Shang, J., Ren, X., & Han, J. (2022). Seeded Hierarchical Clustering for Expert-Crafted Taxonomies (HierSeed). arXiv: https://arxiv.org/abs/2205.11602.
- Meng, Y., Zhang, Y., Huang, J., Zhang, Y., Zhang, C., & Han, J. (2020). Hierarchical Topic Mining via Joint Spherical Tree and Text Embedding. *Proc. KDD 2020*, pp. 1908–1917. DOI: https://doi.org/10.1145/3394486.3403242.
- Davidson, I., & Ravi, S. S. (2005). Clustering With Constraints: Feasibility Issues and the K-Means Algorithm. *Proc. SDM 2005*. DOI: https://doi.org/10.1137/1.9781611972757.13.
- González-Almagro, G., et al. (2024). Semi-supervised Constrained Clustering: An In-depth Overview, Ranked Taxonomy and Future Research Directions. *Artificial Intelligence Review* 57.  DOI: https://doi.org/10.1007/s10462-024-11103-8.

### C.5 Tag / taxonomy / ontology code labeling and hierarchical loss

- Bertinetto, L., Mueller, R., Tertikas, K., Samangooei, S., & Lord, N. A. (2020). Making Better Mistakes: Leveraging Class Hierarchies with Deep Networks. *Proc. IEEE/CVF CVPR 2020*, pp. 12506–12515 (CVF Open Access).  DOI: https://doi.org/10.1109/CVPR42600.2020.01252. arXiv: https://arxiv.org/abs/1912.09393.
- Silla Jr., C. N., & Freitas, A. A. (2011). A Survey of Hierarchical Classification across Different Application Domains. *Data Mining and Knowledge Discovery* 22(1–2), 31–72. DOI: https://doi.org/10.1007/s10618-010-0175-9. 
- Kosmopoulos, A., Partalas, I., Gaussier, E., Paliouras, G., & Androutsopoulos, I. (2015). Evaluation Measures for Hierarchical Classification: A Unified View and Novel Approaches. *Data Mining and Knowledge Discovery* 29(3), 820–865. DOI: https://doi.org/10.1007/s10618-014-0382-x.
- Cesa-Bianchi, N., Gentile, C., & Zaniboni, L. (2006). Incremental Algorithms for Hierarchical Classification. *Journal of Machine Learning Research* 7, 31–54.
- Tai, K.-C. (1979). The Tree-to-Tree Correction Problem. *Journal of the ACM* 26(3), 422–433. DOI: https://doi.org/10.1145/322139.322143.
- Zhang, K., & Shasha, D. (1989). Simple Fast Algorithms for the Editing Distance between Trees and Related Problems. *SIAM Journal on Computing* 18(6), 1245–1262. DOI: https://doi.org/10.1137/0218082.
- Salton, G., & Buckley, C. (1988). Term-Weighting Approaches in Automatic Text Retrieval. *Information Processing & Management* 24(5), 513–523. DOI: https://doi.org/10.1016/0306-4573(88)90021-0.
- Martin, D., Burstein, M., Hobbs, J., Lassila, O., McDermott, D., McIlraith, S., Narayanan, S., Paolucci, M., Parsia, B., Payne, T., Sirin, E., Srinivasan, N., & Sycara, K. (2004). OWL-S: Semantic Markup for Web Services. W3C Member Submission, 22 November 2004. URL: https://www.w3.org/submissions/2004/SUBM-OWL-S-20041122/. 
- Roman, D., Keller, U., Lausen, H., de Bruijn, J., Lara, R., Stollberg, M., Polleres, A., Feier, C., Bussler, C., & Fensel, D. (2005). Web Service Modeling Ontology. *Applied Ontology* 1(1), 77–106.
- Mernik, M., Heering, J., & Sloane, A. M. (2005). When and How to Develop Domain-Specific Languages. *ACM Computing Surveys* 37(4), 316–344. DOI: https://doi.org/10.1145/1118890.1118892.
- Jacobson, I., Christerson, M., Jonsson, P., & Övergaard, G. (1992). *Object-Oriented Software Engineering: A Use Case Driven Approach.* ACM Press / Addison-Wesley. ISBN 0-201-54435-0.

### C.6 Cross-cutting concerns / aspect-oriented decomposition

- Marin, M., van Deursen, A., & Moonen, L. (2007). Identifying Crosscutting Concerns Using Fan-in Analysis. *ACM Transactions on Software Engineering and Methodology* 17(1), Article 3, 37 pp. DOI: https://doi.org/10.1145/1314493.1314496.
- Kiczales, G., Lamping, J., Mendhekar, A., Maeda, C., Lopes, C. V., Loingtier, J.-M., & Irwin, J. (1997). Aspect-Oriented Programming. *Proc. ECOOP 1997*, LNCS 1241, pp. 220–242. DOI: https://doi.org/10.1007/BFb0053381.
- Robillard, M. P., & Murphy, G. C. (2007). Representing Concerns in Source Code. *ACM TOSEM* 16(1), Article 3. DOI: https://doi.org/10.1145/1189748.1189751.
- Roy, C. K., Cordy, J. R., & Koschke, R. (2009). Comparison and Evaluation of Code Clone Detection Techniques and Tools: A Qualitative Approach. *Science of Computer Programming* 74(7), 470–495. DOI: https://doi.org/10.1016/j.scico.2009.02.007.
- Sajnani, H., Saini, V., Svajlenko, J., Roy, C. K., & Lopes, C. V. (2016). SourcererCC: Scaling Code Clone Detection to Big-Code. *Proc. ICSE 2016*, pp. 1157–1168. DOI: https://doi.org/10.1145/2884781.2884877.
- White, M., Tufano, M., Vendome, C., & Poshyvanyk, D. (2016). Deep Learning Code Fragments for Code Clone Detection. *Proc. ASE 2016*, pp. 87–98. DOI: https://doi.org/10.1145/2970276.2970326.
- Tsantalis, N., & Chatzigeorgiou, A. (2009). Identification of Move Method Refactoring Opportunities. *IEEE Transactions on Software Engineering* 35(3), 347–367. DOI: https://doi.org/10.1109/TSE.2009.1.

### C.7 Domain-Driven Design

- Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software.* Addison-Wesley. ISBN 0-321-12521-5.
- Vernon, V. (2013). *Implementing Domain-Driven Design.* Addison-Wesley. ISBN 0-321-83457-7.
- Vernon, V. (2016). *Domain-Driven Design Distilled.* Addison-Wesley. ISBN 0-13-443442-1.
- Newman, S. (2015 / 2021). *Building Microservices: Designing Fine-Grained Systems* (1st / 2nd ed.). O’Reilly. ISBN 978-1-491-95035-7 / 978-1-492-03402-5.
- Brandolini, A. (2018). *Introducing EventStorming.* Leanpub.

### C.8 Human-in-the-loop / interactive ML

- Bavota, G., Carnevale, F., De Lucia, A., Di Penta, M., & Oliveto, R. (2012). Putting the Developer in-the-Loop: An Interactive GA for Software Re-Modularization. *Proc. 4th Int’l Symp. on Search Based Software Engineering (SSBSE 2012)*, LNCS 7515, pp. 75–89.  DOI: https://doi.org/10.1007/978-3-642-33119-0_7.
- Settles, B. (2009). Active Learning Literature Survey. Computer Sciences Technical Report 1648, University of Wisconsin–Madison. URL: http://burrsettles.com/pub/settles.activelearning.pdf.
- Amershi, S., Cakmak, M., Knox, W. B., & Kulesza, T. (2014). Power to the People: The Role of Humans in Interactive Machine Learning. *AI Magazine* 35(4), 105–120. DOI: https://doi.org/10.1609/aimag.v35i4.2513.
- Bae, J., et al. (2017). A Method to Accelerate Human-in-the-Loop Clustering. *Proc. SIAM SDM 2017*. URL: https://research.ibm.com/publications/a-method-to-accelerate-human-in-the-loop-clustering.
- Vikram, S., & Dasgupta, S. (2016). Interactive Bayesian Hierarchical Clustering.  *Proc. 33rd ICML*, PMLR 48, pp. 2081–2090.
- Bae, J., et al. (2020). Interactive Clustering: A Comprehensive Review. *ACM Computing Surveys* 53(1), Article 4, 39 pp. DOI: https://doi.org/10.1145/3340960.
- Tzerpos, V., & Holt, R. C. (1999). MoJo: A Distance Metric for Software Clusterings. *Proc. 6th Working Conf. on Reverse Engineering (WCRE 1999)*, pp. 187–193. DOI: https://doi.org/10.1109/WCRE.1999.806959.

### C.9 Enterprise domain catalogs (for skeleton-design reuse)

- BIAN e.V. (2025). *BIAN Service Landscape v13.0.* Banking Industry Architecture Network. ~326 service domains in a three-level Business Area → Business Domain → Service Domain hierarchy, with 250 Semantic APIs.
- The Open Group. (2022). *ArchiMate® 3.2 Specification.* Document C226, October 2022. ISBN 1-957866-02-4. Motivation layer elements: Driver, Goal, Outcome, Principle, Requirement, Constraint, Stakeholder.

-----

*End of report.*