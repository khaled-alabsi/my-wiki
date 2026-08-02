# Novelty & Related-Work Analysis: 7 New Elements of the Monolith-to-Microservice Decomposition Method

This analysis extends the prior 22-method survey and prior novelty review. It focuses tightly on the 7 newly-added elements, assesses novelty against literature located through targeted searches (May 2026), and ends with paper-positioning synthesis.

-----

## Element 1 — Cascading anchor candidate with tag-coherence-driven depth

**Closest related work.**

- *Service Cutter* (Gysel, Kölbener, Giersche, Zimmermann, ESOCC 2016; DOI 10.1007/978-3-319-44482-6_12) — weighted-graph cut over 16 coupling criteria  mixed in one objective; the criteria are not applied as a cascade with different criteria per level.
- *TDHC top-down hierarchical clustering* (Rathee & Chhabra, J. UCS 24(12), 2018) and *metaheuristic hierarchical clustering for software modularisation* (Aghdasifam et al., *Complexity* 2020, DOI 10.1155/2020/1794947) — provide hierarchical structure  but use a single similarity metric throughout, not criterion-switching per level.
- *HierDec / HDBScan* (Sellami, Saied, Ouni, EASE 2022) — hierarchical density-based clustering producing a cluster hierarchy; the splitting criterion is a single structural+textual similarity  and depth is not driven by an external label-coherence signal.
- *CARGO* (Nitin, Kalia, Ray, FSE 2023; arXiv 2207.11784) — context- and flow-sensitive system dependency graph with label propagation;  closest spirit (entry-point-rooted analysis), but does not switch criteria per level.

**Verdict.** PARTIALLY NOVEL. The use of the *action-point’s package only* (controller/trigger/endpoint), and a cascade that *switches the splitting criterion at each level* (entry-point package → business-tier tags → data-source tags) with *adaptive depth driven by L1+L2 tag coherence*, is not present in any of the 22 surveyed methods or in the 2024–2026 LLM-based decomposition methods I located.

**Sharpening suggestions.**

1. Ablate the cascade vs. flatten the criteria into a single weighted objective; report ΔCHM/CHD/ICP plus a tag-purity metric to show the cascade is not a cosmetic rearrangement.
1. Formalise “tag-coherence-driven depth” as a gain function (e.g., expected reduction in L1 entropy minus a depth penalty) and pre-register the stopping threshold; turns the heuristic into a measurable contribution.
1. Compare against a “package-of-every-class” baseline (used by Mono2Micro- and Bunch-style methods) on ≥3 benchmarks (JPetStore, DayTrader, an industrial mainframe case), so the controller-package choice is empirically defended.

-----

## Element 2 — Tag-diversity threshold as the “too big” criterion

**Closest related work.**

- *Information-theoretic software clustering* (Andritsos & Tzerpos, IEEE TSE 31(2):150–165, 2005) — entropy of attribute distributions as a clustering criterion; conceptual ancestor, but a quality metric rather than a stopping criterion on a fixed semantic vocabulary.
- *Entropy-based criterion in categorical clustering* (Li, Ma, Ogihara, IBM Research) — entropy as cluster heterogeneity. 
- Microservice decomposition methods (CARGO, FoSCI, Mono2Micro, MonoEmbed, HDBScan) use size-style metrics (NED — Non-Extreme Distribution; class count; LOC). No microservice paper located uses *tag cardinality* over a hierarchical domain vocabulary as the size gate.

**Verdict.** PARTIALLY NOVEL. Entropy/heterogeneity stopping criteria are well-known in general clustering; their application as a *replacement* for LOC/class-count in microservice candidate sizing, parameterised by a *hierarchical domain vocabulary*, appears to be novel.

**Sharpening suggestions.**

1. Replace the implicit “more than N L1 tags or M L2 tags” rule with a normalised tag-entropy threshold (H_L1 < τ₁ ∧ H_L2 < τ₂); makes the criterion vocabulary-size-invariant and reviewer-defensible.
1. Empirically calibrate (τ₁, τ₂) against architect-labelled ground-truth decompositions on three projects; a single arbitrary “N=3” will be attacked.
1. Add an “anti-purity-collapse” safeguard: forbid splits where the children all have a single L1 tag *and* are smaller than k components — prevents fragmenting trivially-coherent clusters into singletons.

-----

## Element 3 — Graph extraction hardening: LLM revalidation + human review + noise filter

**Closest related work.**

- Venkatesh, Sabu, Mir, Reif, Lämmel, Mezini, “An empirical study of large language models for type and call graph analysis in Python and JavaScript,” EMSE 30, 2025 (DOI 10.1007/s10664-025-10704-3) — benchmarks LLMs vs. PyCG/Jelly/TAJS for call-graph generation; finds static tools beat LLMs on call-graph soundness, but LLMs help type inference.  
- *Interleaving Static Analysis and LLM Prompting* (SOAP 2024, PLDI workshop) — interleaves analyser calls with LLM queries  for error-spec inference in C; closest “loop” pattern, but no human-in-the-loop confidence gate and no “fix-the-extractor-configuration vs. patch-the-edge” distinction.
- *PredicateFix* (Tian et al., arXiv 2503.12205, 2025) — LLM+RAG repairs static-analysis alerts via CodeQL bridging predicates; spirit of “LLM proposes the fix that feeds the analyser,” but for vulnerability warnings, not call-graph completeness.
- *CARGO* (FSE 2023; arXiv 2207.11784) — flow- and context-sensitive system dependency graph with label propagation;  deterministic, no LLM revalidation.
- *Mono2Micro* (Kalia et al., ESEC/FSE 2021; arXiv 2107.09698) — dynamic-trace-based; no revalidation loop.

**Verdict.** PARTIALLY NOVEL. The unified pipeline — (a) LLM revalidation that *separates systemic “fix-the-extractor” patches from ad-hoc “hardcode-patch” edges*, (b) LLM-confidence-triaged human review (only flagged chains shown), and (c) explicit noise filter for legacy artefacts (tests, dead code, framework boilerplate, generated, cross-cutting, build) — was not found as a unified pipeline in any decomposition or LLM+static-analysis paper. The *systemic-vs-ad-hoc* split is the genuinely novel piece.

**Sharpening suggestions.**

1. Quantify the “fix-extractor wins”: how many LLM-proposed configuration patches generalise (one fix benefits N≥k chains) versus hardcode-patches that remain local. This ratio is the novelty signature and is easily interpretable.
1. Pre-define a confidence-calibration protocol (logistic regression of LLM-reported confidence vs. human-review outcome on a held-out set) — without it, “high-confidence auto-approved” will be challenged as ungrounded.
1. Open-source the noise-filter taxonomy as a reusable artefact (rule set per category: tests, dead code, framework, generated, cross-cutting, build) — becomes a citable side contribution and pre-empts the “ad hoc filtering” attack.

-----

## Element 4 — Three-level hierarchical tagging of DATA SOURCES with vocabulary aligned to mid-tier component tags

**Closest related work.**

- *CHGNN* (Desai, Mathai et al., IJCAI 2022) — heterogeneous graph with program nodes and *resource nodes* (tables/files),  tagged by relation type (READ/WRITE/INVOKE/EXTENDS); data sources are first-class, but tagging is structural, not a three-level *domain* hierarchy.
- *Knowledge-graph microservice extraction* (Yang et al., Information & Software Technology 2022; DOI 10.1016/j.infsof.2022.107033) — four entity types (modules, functions, domain entities, hardware resources) + four relation types, constrained Louvain.  Multi-type cross-layer entity model but no three-level domain hierarchy and no LLM.
- *ServiceMate* (Gandhi, Medicherla, Naik, ISEC 2025; DOI 10.1145/3717383.3717396) — architect-authored Domain Description Map maps classes (and implicitly data) to a single-level domain catalogue.
- Trabelsi, Cao, Heflin, “Matching Table Metadata with Business Glossaries Using LLMs” (arXiv 2309.11506, 2023) — LLM matches columns to glossary terms;  closest data-source-tagging-with-LLM ancestor, but outside decomposition context.
- *MonoEmbed* (Sellami & Saied, EMSE 31:11, 2026; DOI 10.1007/s10664-025-10732-z) — class-level embeddings  only; no data-source layer. 

**Verdict.** PARTIALLY NOVEL. Three-level (L1/L2/L3) domain-hierarchical tagging applied uniformly to *databases + mainframe connections + SOAP/REST endpoints + message queues*, drawn from a *vocabulary shared with mid-tier component tags so cross-layer matching is well-defined*, was not located in any monolith-decomposition paper. The shared-vocabulary aspect is the strongest novelty hook.

**Sharpening suggestions.**

1. Specify the vocabulary as a *controlled ontology* (e.g., 2-level industry taxonomies — BIAN for banking, ARTS for retail, ACORD for insurance) and demonstrate ≥X% LLM-tagger agreement with an architect on at least one such taxonomy. Reproducible, defensible against “the vocabulary is arbitrary.”
1. Report inter-rater agreement (Cohen’s κ between LLM-tagger and 2+ architects) for each layer (component vs. data source).
1. Handle endpoint-as-domain ambiguity: e.g., a SOAP service that internally aggregates customer + product data should receive *multiple* L2 tags; report whether your tagger supports multi-tags and how this affects downstream alignment scoring.

-----

## Element 5 — Cross-layer tag alignment as a scoring signal

**Closest related work.**

- *Multi-view clustering with consistency objectives* — MSCIB (Yang et al., *Knowledge-Based Systems* 2024; arXiv 2303.00002), MCoCo (*Expert Systems with Applications* 2024), BDCL (arXiv 2508.13499). Standard ML literature on cross-view representation consistency; not applied to software decomposition with explicit business-tier↔data-source matching.
- *Service Cutter* — “Semantic Proximity” / “Shared Owner” criteria  align some views implicitly, but coupling criteria are encoded as edge weights, not as explicit cross-layer tag-match bonuses.
- *CHGNN* — heterogeneous-graph joint embedding makes program-resource consistency implicit; it is *not* an explicit, interpretable score term.
- *ServiceMate* — DDM tags classes to domain services; the partitioner rewards keeping a class with its tagged domain — single-layer match, not three-tier cross-layer alignment.

**Verdict.** PARTIALLY NOVEL. Cross-artefact tag alignment as an *interpretable, additive scoring signal* with a defined penalty for L1/L2 mismatches across action-points ↔ business components ↔ data sources is novel in the microservice decomposition literature. The component idea (multi-view consistency) is well-established outside SE.

**Sharpening suggestions.**

1. Define the alignment term mathematically (A(s) = Σ w_layer · 𝟙[L1_a = L1_b] + α · 𝟙[L2_a = L2_b]) and report the weights you chose. Without an equation, the contribution is hard to claim.
1. Ablate (i) only structural cohesion vs. (ii) only within-layer tag-purity vs. (iii) full cross-layer alignment. Marginal contribution of cross-layer alignment = your novelty number.
1. Demonstrate interpretability: for one rejected candidate, show the alignment-term breakdown (“action-point=customer, components=customer, data-source=product → mismatch −0.4”).

-----

## Element 6 — Question-based LLM-judge rubric + configurable decomposition profiles + anchor/ignore data-source preferences

**Closest related work.**

- *Prometheus* (Seungone Kim et al., “Prometheus: Inducing Fine-grained Evaluation Capability in Language Models,” arXiv 2310.08491, ICLR 2024 Workshop) and *Prometheus 2* (Kim, Suk, Longpre et al., EMNLP 2024 pp. 4334–4353, DOI 10.18653/v1/2024.emnlp-main.248; arXiv 2405.01535) — foundational LLM-as-judge with rubric-conditioned scoring. 
- *MT-Bench / Chatbot Arena* (Zheng, Chiang, Sheng et al., “Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,” arXiv 2306.05685, NeurIPS 2023) — reports GPT-4 achieves “over 80% agreement” with human preferences (matching human-to-human agreement)  and explicitly examines position, verbosity, and self-enhancement biases. 
- *Quevedo, Abdelfattah, Rodriguez, Yero, Cerny*, SN Computer Science 5(4):422, 2024 — ChatGPT answering microservice-architecture questions from source code;  LLM reasoner over MSA, but does not score decompositions.
- *Hierarchical Evaluation of Software Design Capabilities of LLMs* (arXiv 2511.20933, 2025) — measures whether LLMs recognise cohesion/coupling;  foundation evidence that LLMs *can* judge cohesion/coupling, but not a deployed rubric judge for decompositions.
- *MicroPAD* (Mendes et al., arXiv 2603.23073, 2026) — LLM detects microservice infrastructure patterns;  precedent for LLM-as-pattern-judge in MSA.
- *Service Cutter* (Gysel et al. 2016) — closest profile-configurability ancestor: re-weights 16 coupling criteria  to favour team-oriented or data-oriented partitions; *no named profiles* like “around-the-mainframe”.
- *Rake* (Trabelsi, “Identifying Appropriately-Sized Services with Deep Reinforcement Learning,” arXiv 2512.20381, 2025) — deep-RL with a customisable objective balancing modularisation quality and business-capability alignment;  explicit warning that pure business-objective optimisation degrades quality on tightly coupled systems. 
- *Multi-objective MSD policies* — Watanabe et al., “Automated Microservice Decomposition Method as Multi-Objective Optimization,” IEEE 2022 (DOI 10.1109/9779847) — generates candidates “without weighting by using predefined MSD policies and fix operations”  mapped to “a vector space that consists of basis vectors formulated in accordance with the evaluation functions defined by the MSD policies.”  Closest to *named profiles* with predefined policy mode.
- *Constrained clustering* (Basu et al.; PMC4201489 PLOS One 2014; Pourbahrami et al. survey arXiv 2303.00522) — must-link / cannot-link constraints.  Standard primitive your forced-together/forced-apart constraints reuse.

**Verdict.** PARTIALLY NOVEL. LLM-as-judge with a rubric is well-established (Prometheus 2024, MT-Bench 2023); configurable multi-objective profiles exist (Watanabe 2022, Rake 2025, Service Cutter 2016). The combination that is novel: (a) the *legacy-modernisation-specific* profiles (“around-the-mainframe”, “extract-around-databases”, “extract-around-domains”, “extract-around-teams”) with explicit *anchor* and *ignore* data-source preferences — in particular the *ignore-external-REST-endpoints* rule that prevents external endpoints from spawning microservices because the goal is *decomposing the legacy system, not multiplying external boundaries* — and (b) DDD-aggregate-boundary and “name in 2–3 words” probes in the rubric. The “ignore-external-REST” primitive was not located, even implicitly, in any prior decomposition method I surveyed.

**Sharpening suggestions.**

1. Validate the LLM judge against architect rankings: collect pairwise architect preferences on N candidate decompositions; report Cohen’s κ / Kendall’s τ between architect and LLM-judge rankings. Without this, the rubric will be called hand-wavy.
1. Pre-register the four named profiles, run all of them on the same monolith, and demonstrate *qualitatively different* outputs. If “around-mainframe” and “around-domain” produce near-identical cuts, the profile system has not earned its keep.
1. Formalise the “anchor / ignore” data-source primitive as a parameterised constraint type ({anchor, ignore, neutral} × {db, mainframe, queue, external-REST}). The taxonomy itself becomes a citable contribution, separable from the LLM-judge.
1. Address LLM-judge bias risks explicitly (position bias, length bias, self-preference if the same LLM generates and judges); follow MT-Bench methodology (judge swap with two LLM families, randomised order).

-----

## Element 7 — Multi-strategy non-random initial population (~10–15 candidates)

**Closest related work.**

- *MSExtractor* (Sellami, Ouni, Saidani et al., 2019/2022; DOI 10.1007/978-3-030-33702-5_5; later DOI 10.1016/j.jss.2022.111419) — multi-objective IBEA with *random* initial population.
- *FoSCI* (Jin, Liu, Zheng, Cui, Cai, ICWS 2018 / TSE 2021) — genetic search on functional atoms with standard random init.
- *Search-based many-criteria identification of microservices* (Ribeiro & Lucena, GECCO 2020) — many-criteria search; random init.
- *Beyond Evolutionary Algorithms for SBSE* (Chen, Nair, Menzies, arXiv 1701.07950) — argues large initial population + recursive bi-clustering chop beats EA; closest precedent for “principled, larger initial population” but not multi-*strategy*.
- *MultiGA* (Isabelle Diana May-Xin Ng, Tharindu Cyril Weerasooriya, Haitao Zhu, Wei Wei, “MultiGA: Leveraging Multi-Source Seeding in Genetic Algorithms,” arXiv 2512.04097, 21 Nov 2025) — initialises GA population by sampling from multiple LLMs;  reports that “on three of four benchmarks, MultiGA seeded with a primarily open-source ensemble outperforms a GPT-4-only seeded variant.” Closest precedent for diverse-LLM-seeding, but in NL/reasoning tasks, not software clustering.
- *MAP-Elites / Multi-Emitter MAP-Elites* (Cully, GECCO 2021; arXiv 2007.05352) — quality-diversity with heterogeneous emitters; closest QD ancestor.
- *Population Initialization Techniques for Evolutionary Algorithms* (Borhan Kazimipour, Xiaodong Li, A. K. Qin, IEEE CEC 2014, pp. 2585–2592, DOI 10.1109/CEC.2014.6900618) — categorises initialisation across three axes: randomness, compositionality, generality. Reference survey.
- Service Cutter, ServiceMate, CARGO, Mono2Micro, MonoEmbed, MicroDec, ROMI (Ghlissi et al., ICSOC 2025), CHGNN, Mo2oM (Ziabakhsh et al., arXiv 2508.07486, 2025) — none publish a multi-strategy seeding catalog.

**Verdict.** PARTIALLY NOVEL. Principled non-random initialisation is established in EA (Kazimipour et al. CEC 2014) and in QD (MAP-Elites; Multi-Emitter MAP-Elites). Multi-LLM diverse seeding (MultiGA 2025) is a 2025 precedent in NL/reasoning. The *specific catalog* of 10–15 software-decomposition-tailored seeds — cascading anchor + L1-tag + L1+L2 + tag-frequency + per-data-source + anchor-data-source + action-point-tag + chain-overlap + Louvain/Leiden/spectral/HAC + LLM-perspective × 6 framings + existing-package + git-co-change + architect-sketch — is, based on my searches, not present in any microservice-decomposition paper. The *LLM-perspective seeding with 6 framing prompts* mirroring optimisation objectives is the most clearly novel sub-piece.

**Sharpening suggestions.**

1. Frame the catalog as a *Quality-Diversity emitter set* (each seed = one emitter, Cully GECCO 2021) and report archive coverage in a 2-D behavioural descriptor space (e.g., (coupling, business-alignment)). Borrowing QD vocabulary gives the contribution a methodological home and enables comparison against vanilla MAP-Elites.
1. Ablate per-seed contribution (drop-one-seed Pareto-front degradation table) — pre-empts “you only need 2 of these 15.”
1. Compare against MSExtractor / FoSCI / MultiGA at controlled evaluation budget to show your seeding reaches the Pareto frontier faster (in eval count), not just better-eventually.
1. Release the 6 LLM-framing-prompt seeds (low-coupling / data-ownership / business-domain / team-ownership / legacy-isolation / transactional-boundary) as a prompt catalog. Easy citable artefact, hard to attack.

-----

## (A) Overall Novelty Boundary — paper anchors vs. engineering-only parts

**Strongest novelty claims (paper anchors).**

1. **Three-level hierarchical domain tagging applied uniformly across code AND data sources with shared vocabulary, used as both a stopping criterion (Element 2) and a cross-layer alignment scoring term (Element 5).** No surveyed method does this triple combination; this should anchor the paper title.
1. **LLM-revalidated graph extraction with the systemic-vs-ad-hoc patch distinction and confidence-triaged human review (Element 3).** Methodologically novel: it produces *reusable analyser improvements* rather than per-graph patches, which is the cleanest engineering-research contribution.
1. **Configurable, named, legacy-modernisation-specific optimisation profiles with anchor/ignore data-source preferences — in particular the explicit “don’t spawn microservices for external REST endpoints” constraint (Element 6).** This is the contribution most clearly *missing from* the 22 surveyed methods and grounded in real legacy experience that academic methods consistently ignore.

**Weakest novelty claims (engineering-only — present as competent reuse, not contribution).**

1. **LLM-as-judge with a rubric (Element 6, core technique).** Prometheus, Prometheus 2 (Kim et al. 2024) and MT-Bench (Zheng et al., NeurIPS 2023) own this; reuse, cite, do not claim.
1. **Multi-strategy initial population for an evolutionary loop (Element 7, core technique).** MAP-Elites, Multi-Emitter MAP-Elites, MultiGA, Kazimipour et al. (CEC 2014) already establish multi-strategy seeding; the seed *catalog* is your contribution, the *idea* is not.
1. **Cascading hierarchical clustering with an entropy-like stopping criterion (Elements 1+2, core technique).** TDHC (Rathee & Chhabra 2018), Andritsos & Tzerpos (TSE 2005), HierDec own the family; *criterion-switching per level and the specific tag-coherence formulation* are your contribution.
1. **Must-link / cannot-link forced-together/apart constraints (Element 6).** Constrained-clustering literature (Basu; Pourbahrami et al., arXiv 2303.00522) owns this — frame as reuse.

-----

## (B) Missing-novelty-lever — concrete additions that sharpen the boundary

**Lever 1 — Add a “Tag-Anchored Louvain/Leiden” baseline (and beat it).**
Currently the graph-clustering seeds in Element 7 are *vanilla* Louvain/Leiden/spectral. Introduce a *Tag-Seeded Louvain* in which L1+L2 domain tags initialise the community labels and Louvain modularity is augmented with a tag-purity term (Q’ = Q + λ · TagPurity). Then (i) report Tag-Seeded Louvain as your own contribution and a separate variant in the seeding catalog; (ii) show empirically that it beats vanilla Louvain on tag-purity metrics on three benchmarks; (iii) show that, in the evolutionary loop, the *combination* of Tag-Seeded Louvain + cascading anchor (Element 1) Pareto-dominates either alone. This pulls Element 7 from “engineering-only seed catalog” into a *named algorithmic contribution* without bloating the method.

**Lever 2 — Bidirectional tag-graph alignment as a closed-loop contribution.**
Element 5 currently scores alignment statically. Promote it to an *iterative refinement signal*: after each evolutionary generation, identify the most-cross-layer-misaligned candidate and have the LLM revise *which* L2 tags it assigned, not which grouping it proposed. This separates *tag-vocabulary learning* from *grouping search* as two coupled optimisations and lets you report “tag-vocabulary stabilises after k iterations and decomposition quality monotonically improves.” A closed-loop refinement contribution that no surveyed method has, and it gives you defence against “tags are LLM-hallucinated and noisy.”

*(Optional Lever 3 — validate the tag vocabulary against a published industry ontology, e.g., BIAN for banking, to demonstrate domain hierarchies transfer beyond a single case study.)*

-----

## (C) Five most threatening reviewer objections + one-line rebuttal sketches

**Obj 1 — “LLM tags are unreliable / hallucinated; the whole method rests on a noisy oracle.”**
Rebuttal: report Cohen’s κ between LLM-tagger and two architects per layer; introduce a *tag-confidence gate* (low-confidence tags fall back to “L1 only” or “untagged”); show downstream decomposition quality is *monotonic in tag confidence* — the method degrades gracefully when tags are weak.

**Obj 2 — “Your evaluation is on one or two monoliths; the cascading-criterion and profile system is not shown to generalise.”**
Rebuttal: pre-commit to ≥3 benchmarks across two domains (e.g., JPetStore + DayTrader + an industrial mainframe banking case + an industrial mainframe insurance case); run *all four named profiles* on each and report a profile × benchmark grid with held-out architect rankings. Even partial coverage neutralises the objection.

**Obj 3 — “LLM-as-judge is biased / self-preferencing; the scores are circular.”**
Rebuttal: use two judge LLMs from different families (e.g., Claude + GPT-class + Llama), randomise candidate order, report judge-swap consistency, and validate against a human architect panel on a stratified sample (Zheng et al., NeurIPS 2023, arXiv 2306.05685 — protocol for position, verbosity, self-enhancement biases). Pre-register the rubric.

**Obj 4 — “The seed catalog has 10–15 strategies but no ablation; how do you know they aren’t redundant?”**
Rebuttal: provide a per-seed drop-one-seed contribution table reporting Pareto-front degradation; cluster the seeds in behavioural-descriptor space (à la MAP-Elites) and show each occupies a distinct region; concede and remove seeds that empirically duplicate (turn this into a strength: “the catalog was distilled by empirical pruning”).

**Obj 5 — “How does this beat CARGO + MonoEmbed + Mono2Micro on standard metrics (SM, IFN, ICP, NED, CHM, CHD)?”**
Rebuttal: include the exact metrics those papers report and the unified-evaluation framework of Weerasinghe, Kularathne, Madhushika, Lakshan, de Silva, Wijayasiri & Perera, “From Monolith to Microservices: A Comparative Evaluation of Decomposition Frameworks,” arXiv 2601.23141 (30 Jan 2026) — which benchmarks JPetStore, AcmeAir, DayTrader, and Plants using SM, IFN, ICP, NED  and finds that “hierarchical clustering-based methods, particularly HDBScan, produce the most consistently balanced decompositions across benchmarks.”  Add the *new* metrics your method legitimately introduces (tag-purity, cross-layer alignment, profile-fidelity); show non-inferiority on the standard metrics and dominance on the new ones; frame the contribution as “*configurable* decomposition for legacy systems with mainframe / external-REST asymmetries” rather than “we beat MonoEmbed on cohesion.” Do not fight on the opponent’s chosen ground.