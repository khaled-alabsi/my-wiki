# my-wiki - Index

> Navigation map for agents: match what you are looking for, or what you want to add, against the
> one-line descriptions below, then open that folder or file.
> Keep this current: run the `wiki` skill in `refresh` mode after adding, moving, or removing notes.
> A refresh only re-describes what changed.
> See `AGENTS.md` for vault hazards and working rules.

## How to use this index

- **Looking for something**: scan the descriptions for the closest topic match, then open that file.
  A file with sub-bullets lists its own sections — go straight to the right one.
- **Adding something new**: find the folder whose `Place here:` line fits the new content's topic,
  then check that folder's files for one that already covers it. Merge into an existing note before
  creating a new one. If no folder fits at all, that means a new folder is needed — not that the
  closest one should be forced.

## Conventions

- Links: `[[wikilinks]]`, resolved by note name. The vault has almost no note-to-note links.
- Tables of contents: markdown anchors — `[Section](#Section%20Name)`. Older notes still use
  `[[#Section|Section]]`; both work, new TOCs use the markdown form.
- Frontmatter: present in 3 files only (Kanban, Excalidraw). Do not assume it exists, do not add it.
- File naming: mixed — Title Case, numbered prefixes (`0000001`), kebab-case. Not normalised further.
- Dates: ISO format (`2026-08-01`) where present.
- Attachments: per-folder `resources/` subfolders; embedded inline with `![[...]]`.
- Not notes, never indexed: `_utils/` (MCP servers), `Dev/LLM/` (code sandbox),
  `Dev/languages/Python/*.py|.ipynb`, `.tmp/`, `.obsidian/`, `.wiki-index/`.

## Contents

- `Dev/` - software development across languages, frontend, infra, architecture and practices — see `Dev/index.md` for its 79 notes
- `AI/` - transformer architecture, LLM fine-tuning, PyTorch — see `AI/index.md` for its 14 notes
- `PhD/` - MSPC research: multivariate statistical process control and fault diagnosis
- `Banking/` - MiFID II/WpHG regulation, and Commerzbank-specific advisory domain knowledge
- `Mathematik/` - vector/matrix products, dot product, and machine-learning math foundations
- `Work-life/` - workplace diplomacy, feedback, boundaries, and self-help reflections
- `Quick note/` - Obsidian/LaTeX setup, benchmarks, macOS configs — see `Quick note/index.md` for its 6 notes
- `Excalidraw/` - Excalidraw drawings (plugin folder)
- `Kanban/` - Kanban board plans
- `Dairy/` - Obsidian daily-notes folder (currently empty)

## Dev/

- Place here: software development — programming languages, frontend frameworks, infrastructure and CI, architecture and decomposition research, and general engineering practice.
- `Dev/index.md` for its 79 notes across 5 groups.

## AI/

- Place here: AI and deep learning — transformer internals, LLM fine-tuning (LoRA/QLoRA), PyTorch, Hugging Face, tokenizers. Note that `Dev/LLM/` is a code sandbox, not an AI notes folder.
- `AI/index.md` for its 14 notes.

## PhD/

- Place here: **MSPC only** — multivariate statistical process control, fault diagnosis and attribution, PCA/T2/SPE methods, correlated-feature residual monitoring, noise handling, and framing this work for publication. Monolith-decomposition research does **not** belong here; it lives in `Dev/architecture/`.
- `PhD/correlated-feature-residual-monitoring.md` - correlated feature residual distribution monitoring; has its own table of contents with section anchors
- `PhD/hawkins-decomposition-t2-fault-diagnosis.md` - Hawkins T2 decomposition for fault diagnosis
- `PhD/myt-decomposition.md` - MYT decomposition method for fault diagnosis
- `PhD/Noise Handling in Statistical and Multivariate Process Monitoring_ A Literature Review.md` - literature review on noise handling in statistical and multivariate process monitoring
- `PhD/pca-t2-spe-attribution-methods.md` - PCA, T2 and SPE attribution methods in process monitoring
- `PhD/publishable methods framing guide.md` - academic positioning for five publication candidates from the TEP catalog: prior art, novelty deltas, readiness, and claim language

## Banking/

- Place here: **generic** banking and securities regulation — MiFID II, WpHG, BaFin, target market (TaMrA), suitability statements (GEE), advisory duties. Anything naming an internal system (`Tamara`, `CPMS`, `Sau`/`WBF-E-SAU`, `DocFamily`, `Filiale`, `FRÜHSTART`, `AVD`) or a bank-specific API goes in `Banking/COBA/` instead.
- `Banking/COBA/` - Commerzbank-specific domain knowledge
- `Banking/mifid-wphg-banking-notes.md` - MiFID II and WpHG concepts, the main advisory business processes, target market, GEE, BaFin registration, and a developer's view of it
  - `# MiFID II` - what the EU framework covers and its goals
  - `# WpHG vs MiFID II` - how the German act relates to the EU directive
  - `# Main MiFID Business Processes` - the core regulated advisory processes
  - `# Target Market (TaMrA)` - target market definition and matching
  - `# Geeignetheitserklärung (GEE)` - suitability statement obligations
  - `# BaFin Registration of Investment Advisors` - advisor registration duties
  - `# Typical End-to-End Advisory Flow` - the advisory journey start to finish
  - `# Developer Perspective` - what all this means when implementing it

### Banking/COBA/

- Place here: Commerzbank-specific banking knowledge — internal systems, APIs, product configurations and processes that only apply to this bank.
- `Banking/COBA/AVD/AV-ev.md` - sprint refinement extraction for the AVD (Altersvorsorge Depot) advisory and document lifecycle: product configuration, TIP/GE/Ex-Anton generation, DocFamily archiving, WBF-E-SAU handover, Contentful content, eligibility gating
- `Banking/COBA/AVD/knowledge.md` - business knowledge extraction for the AVD/FRÜHSTART early-retirement savings process: onboarding, suitability, recommendation via Tamara, PIP/GE generation via CPMS, external handover to Sau

## Mathematik/

- Place here: mathematics — vector and matrix operations, dot/cross/outer products, and the math foundations underlying machine learning (functions, graphing, polynomials, matrices, statistics, data analysis).
- `Mathematik/dot-product/` - dot product fundamentals: basics, notation, properties, applications
- `Mathematik/ml-foundations/` - machine learning math foundations: variables, functions, graphing, polynomials, matrices, statistics, data analysis
- `Mathematik/vector-products-notes.md` - vector and matrix multiplication in depth: dot, cross and outer products, matrix-times-vector, matrix-times-matrix, transpose products, and the universal shape and sum rules
  - `## 1. Three Common Vector Products` - dot, cross and outer compared
  - `## 2. Dot Product: Two Vectors Produce One Number` - definition and intuition
  - `## 3. Cross Product: Two 3D Vectors Produce a Perpendicular Vector` - geometry of the cross product
  - `## 4. Outer Product: Two Vectors Produce a Matrix` - building a matrix from two vectors
  - `## 5. Matrix Times Vector: Scale Columns, Then Add` - the column-scaling mental model
  - `## 7. Matrix Times Matrix: Many Matrix-Vector Multiplications` - matrix products decomposed
  - `## 11. The Universal Shape Rule` - how to predict output shapes
  - `## 12. The Universal Sum Rule` - what gets summed and when

### Mathematik/dot-product/

- Place here: dot product mathematics — definition, notation, algebraic and geometric properties, applications.
- `Mathematik/dot-product/1- Dot Product Basics.md` - definition of the dot product and its properties with worked examples
- `Mathematik/dot-product/2- Dot Product Applications.md` - practical applications of the dot product
- `Mathematik/dot-product/3- Dot Product Notation.md` - dot product notation conventions
- `Mathematik/dot-product/4- Dot Product Properties.md` - algebraic and geometric properties
- `Mathematik/dot-product/Topics.md` - dot product topic overview and subtopic listing

### Mathematik/ml-foundations/

- Place here: the school-level mathematics needed to follow machine learning — variables, functions, graphing, polynomials, matrices and determinants, statistics and probability, data analysis.
- `Mathematik/ml-foundations/1- Variables and Functions.md` - variables and functions fundamentals
- `Mathematik/ml-foundations/2- Graphing and Plotting Points.md` - graphing and plotting points
- `Mathematik/ml-foundations/3- Functions and Relations.md` - functions and relations
- `Mathematik/ml-foundations/4- Polynomials and Expressions.md` - polynomials and algebraic expressions
- `Mathematik/ml-foundations/5- Matrices and Determinants.md` - matrices and determinants
- `Mathematik/ml-foundations/6- Statistics and Probability.md` - statistics and probability fundamentals
- `Mathematik/ml-foundations/7- Data Analysis.md` - data analysis methods and concepts
- `Mathematik/ml-foundations/Topics.md` - machine learning math topic overview

## Work-life/

- Place here: workplace dynamics — diplomacy, handling feedback and criticism, assumptions, trigger situations, boundary communication, exit strategies, and self-help reflections on invalidation and exploitation at work.
- `Work-life/Angery adhs.md` - anger and ADHD in a work context
- `Work-life/Assumptions.md` - how assumptions form and distort workplace situations
- `Work-life/Diplomacy, Discipline and Presence_ A Field Guide to Being Effective and Well-Regarded at Work.md` - field guide to workplace diplomacy, discipline and presence
- `Work-life/Navigating Feedback From Criticism to Growth.md` - turning criticism into growth
- `Work-life/Public accusations or wrong assumptions.md` - handling public accusations and wrong assumptions
- `Work-life/Self-help report for unfair invalidation and perceived exploitation at work.md` - self-help report on unfair invalidation and perceived exploitation
- `Work-life/Stopping Revenge simulation.md` - stopping revenge-simulation thought loops
- `Work-life/Trigger-Situationen, Grenzkommunikation und Exit-Strategien für Softwareentwickler_ Recherche-Ergebnisse.md` - German: trigger situations, boundary communication and exit strategies for software developers
- `Work-life/Workplace diplomacy.md` - workplace diplomacy concepts and practices
- `Work-life/Workplace distress is often not “just being sensitive..md` - workplace distress versus "just being sensitive"
- `Work-life/exploited.md` - notes on feeling exploited at work

## Quick note/

- Place here: miscellaneous short notes — Obsidian and LaTeX setup, model benchmarks, file sync, macOS configuration.
- `Quick note/index.md` for its 6 notes.

## Excalidraw/

- Place here: Excalidraw drawings only. This is the Excalidraw plugin's configured folder — do not rename it.
- `Excalidraw/Drawing 2026-07-20 00.46.12.excalidraw.md` - Excalidraw drawing, 20 Jul 2026
- `Excalidraw/Drawing 2026-07-22 18.51.59.excalidraw.md` - Excalidraw drawing, 22 Jul 2026

## Kanban/

- Place here: Kanban board plans, in the obsidian-kanban plugin's format.
- `Kanban/PhD.md` - PhD kanban board: backlog, active, done
- `Kanban/Reorganise plan.md` - reorganisation plan board (currently empty)

## Dairy/

- Place here: nothing manually. This is the Obsidian daily-notes folder (`.obsidian/daily-notes.json`); Obsidian creates dated notes here. Currently empty. Never rename or remove it.
