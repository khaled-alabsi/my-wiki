# Domain architecture — designing the vault's structure

<!-- sync: local-wiki-domain-architecture v1 -->

**This is the reasoning behind `init`'s structure proposal.** `init` step 2 runs it before writing a
single folder name, and step 3 turns its output into the proposal the user reviews.

## How this fits the rest of the skill

| File | Answers |
|---|---|
| **this file** | *What should this vault's architecture BE?* — run once, at `init`, and again whenever a reorganization is considered |
| `references/knowledge-organization.md` | *Where does THIS note go, given the architecture that exists?* — run on every write |
| `references/index-format.md` | How the architecture is written down as `index.md` routing lines |
| `references/modes/audit.md` | Detects when the architecture has stopped fitting the material |

The two doctrines are the same reasoning at different scales: this one designs the shelves, the
other one decides which shelf a book belongs on. Neither replaces the other.

## Conventions in this vault

The examples below use `Title-Case/` folders and `Note Names With Spaces.md`. **This vault uses
kebab-case for both** — `customer-and-party/`, `resolve-party-id-to-customer-number.md`. The
reasoning is what matters; the casing follows the vault.

Three more local specifics:

- **Links are standard markdown**, `[text](../relative/path.md)` — never `[[wikilinks]]`.
- **Where this file says "MOC" or "index note", this vault has `index.md`** — the root one, plus a
  per-folder `index.md` for folders past ~15 files. Its `Place here:` lines are exactly the curated
  navigation surface an MOC provides, so build them there rather than inventing a parallel file.
- **"Properties" are standard YAML frontmatter.** This vault already writes `author`, `created`,
  `last_changed`, `last_changed_by`. The `type:` and `status:` fields this file recommends are a
  genuine addition — adopt them when the domain has enough note kinds to make filtering useful, and
  say so in the proposal rather than adding them silently.

## Where `init` stops

This file describes designing an architecture *and* evolving one. At `init` time only the first
half applies — the vault has no notes yet, so there is nothing to restructure.

The "Structure Evolution" and "Existing Vault Behavior" sections govern a **later** reorganization,
which is a `refactor` run behind its own approval gate. `init` never moves anything, because there
is nothing there to move.

## The one hard limit

**The proposal is a proposal.** Everything this file reasons out ends up in
`wiki-structure-proposal.md` for the user to edit and accept. It is never created on disk first and
justified afterwards, however good the reasoning was.

---

# Role

You are a **Knowledge Architect, Domain Analyst, Information Architect, and Technical Documentation Designer** responsible for designing and maintaining a long-lived local Markdown knowledge base.

Your job is NOT merely to create folders.

Your job is to reason about a domain, discover the kinds of knowledge that will accumulate in it, predict how the user will retrieve that knowledge during real work, and create an architecture that remains useful as the vault grows from tens to thousands of notes.

The vault is primarily used by a technical professional who may work as:

- software engineer
- business analyst
- solution/software architect
- data scientist
- machine-learning engineer
- researcher

The architecture must therefore support both:

1. **understanding a domain**, and
2. **performing work inside that domain**.

---

# Core Principle

Never design a domain from a superficial list of obvious categories.

Bad example:

```text
banking/
├── products/
├── regulations/
├── apis/
└── notes/
```

This structure merely names a few categories. It does not model how banking knowledge is actually encountered or used.

Instead, reason from:

```text
Domain
→ subdomains
→ business capabilities
→ concepts/entities
→ actors
→ products
→ processes/workflows
→ use cases
→ systems
→ services
→ APIs/interfaces
→ data
→ rules
→ regulations
→ decisions
→ operational knowledge
→ troubleshooting
→ examples
→ tutorials
→ reference material
→ cross-domain relationships
```

Not every domain contains every dimension.

Determine which dimensions actually exist before creating the structure.

---

# Primary Objective

Given any domain such as:

- Banking
- Securities / Wertpapier
- Wealth Management
- Machine Learning
- Software Architecture
- Java
- Spring
- Personal Finance
- Research
- Mathematics
- Personal Knowledge
- a specific software system
- a company-specific business domain

design an architecture that answers three questions:

### 1. What exists in this domain?

Examples:

- concepts
- entities
- products
- actors
- capabilities
- systems
- algorithms
- regulations
- APIs
- technologies

### 2. What does someone DO in this domain?

Examples:

- retrieve a customer number
- determine products belonging to a party
- open a securities account
- validate suitability
- execute an order
- train a model
- evaluate a classifier
- deploy a model
- investigate model drift
- debug an API
- trace a business process

### 3. What does someone need to UNDERSTAND about this domain?

Examples:

- why settlement accounts exist
- relationship between customer, party, agreement and account
- why suitability checks are required
- difference between training and inference
- bias/variance tradeoff
- architectural boundaries between services

The final architecture must support all three.

---

# Mandatory Reasoning Process

Before creating folders, perform the following reasoning internally.

Do NOT immediately create a directory tree.

## Phase 1 — Identify the Domain Type

Determine whether the domain is primarily:

- business/domain knowledge
- software/technology
- machine learning/data science
- scientific/research
- personal knowledge
- project/system-specific
- regulatory/legal
- hybrid

A domain may belong to multiple categories.

Example:

```text
Banking
= business
+ regulatory
+ technical
+ operational
+ data
```

Machine Learning:

```text
Machine Learning
= mathematical
+ algorithmic
+ experimental
+ engineering
+ operational
+ research
```

Use this classification to decide which architectural dimensions are important.

---

# Phase 2 — Build a Domain Map

Determine the major subdomains.

Do not stop at 3–5 obvious categories.

Ask:

- What are the major branches of this field?
- What capabilities exist?
- What lifecycle exists?
- What entities exist?
- What systems support it?
- What tasks are repeatedly performed?
- What information would an experienced practitioner repeatedly look up?
- What terminology causes confusion?
- What relationships between concepts matter?
- What external rules constrain the domain?
- What failure modes or troubleshooting scenarios exist?

The domain map should aim for **coverage**, but not create meaningless empty folders.

---

# Phase 3 — Identify Knowledge Dimensions

Evaluate the following dimensions individually.

Use only those relevant to the domain.

## Domain and Conceptual Knowledge

```text
Concepts
Terminology
Entities
Actors
Roles
Relationships
Domain Models
Principles
Mental Models
Glossary
```

## Capability and Business Knowledge

```text
Capabilities
Business Functions
Products
Services
Processes
Workflows
Business Rules
Policies
Decisions
Events
States
Lifecycle
```

## Practical Work

```text
Use Cases
How-To
Procedures
Operations
Troubleshooting
Debugging
Investigations
Examples
Recipes
Playbooks
```

## Technical Knowledge

```text
Architecture
Systems
Applications
Components
Services
APIs
Interfaces
Events
Messaging
Data Models
Schemas
Databases
Integrations
Infrastructure
Security
Observability
```

## Governance

```text
Regulations
Compliance
Standards
Policies
Controls
Audit
Security
Privacy
Risk
```

## Learning

```text
Tutorials
Explanations
Examples
Exercises
Learning Paths
Cheat Sheets
```

## Research

```text
Papers
Methods
Experiments
Hypotheses
Results
Datasets
Literature
Open Questions
Ideas
```

## Operational / Temporal Knowledge

```text
Incidents
Known Issues
ADRs
Decisions
Changes
Migrations
Meeting Knowledge
Investigations
Lessons Learned
```

---

# Phase 4 — Model Retrieval Intent

The architecture must be designed around how the user will search for information later.

For every major domain, imagine questions such as:

```text
What is X?
Why does X exist?
How does X relate to Y?
How do I perform X?
Which system owns X?
Which service provides X?
Which API gives me X?
Where does this data originate?
Which identifier should I use?
What business rule controls X?
Which regulation requires X?
What happens after X?
What can fail during X?
How do I debug X?
Can I see a concrete example?
What decision did we make about X?
```

If the proposed structure makes these questions difficult to answer, redesign it.

---

# Phase 5 — Separate Knowledge by Purpose

Use the following four documentation modes as a reasoning tool.

## Explanation

Answers:

```text
What is this?
Why does it work this way?
How does it relate to something else?
```

Examples:

```text
Why securities require settlement
Difference between customer and party
How attention works in transformers
Why feature leakage occurs
```

## How-To / Use Case

Answers:

```text
How do I accomplish X?
```

Examples:

```text
How to retrieve the customer number
How to find products for a Party ID
How to determine the owner of an agreement
How to train XGBoost
How to diagnose model drift
```

## Reference

Answers:

```text
What are the exact facts/interfaces/options?
```

Examples:

```text
Customer API
Portfolio API
Database schema
Identifier reference
HTTP error codes
Model hyperparameters
Regulatory document types
```

## Tutorial

Provides an end-to-end learning experience.

Examples:

```text
Understanding securities settlement from order to custody
Build a classifier from dataset to deployment
Understanding a banking customer from party to account
```

Do not blindly create four folders named after these categories.

Use them to ensure that all four information needs can be represented somewhere in the architecture.

---

# Phase 6 — Design the Architecture

Use a hybrid architecture.

The hierarchy provides **stable navigation**.

Links provide **semantic relationships**.

`index.md` provides **alternative views** - the root routing map, and a per-folder `index.md` once a folder grows past ~15 files.

Properties provide **machine-readable classification**.

Do not attempt to encode every relationship into folders.

---

# Folder Design Rules

## Rule 1 — Organize folders by stable concepts

Good folder boundaries usually represent things that remain meaningful over many years:

```text
Customers
Accounts
Payments
Securities
Models
Data
Algorithms
Architecture
Regulation
```

Avoid organizing permanent knowledge primarily around temporary projects.

---

## Rule 2 — Prefer domain semantics over generic buckets

Bad:

```text
banking/
├── general/
├── technical/
├── other/
└── misc/
```

Better:

```text
banking/
├── customer-and-party/
├── accounts/
├── payments/
├── lending/
├── securities/
├── wealth-management/
├── regulatory-and-compliance/
└── banking-technology/
```

---

## Rule 3 — Do not over-nest

Folders should help navigation, not encode an ontology.

Prefer approximately 2–4 meaningful levels.

Avoid:

```text
banking/
  retail/
    customer/
      identification/
        technical/
          apis/
            rest/
              version-2/
```

Relationships deeper than this are usually better represented through links and metadata.

---

## Rule 4 — Use cross-links when knowledge belongs to multiple domains

Example:

`Suitability Assessment` belongs to:

- securities
- advisory
- customer profiling
- regulation
- MiFID

Do NOT duplicate the note five times.

Create one canonical note and link to it from the relevant folder indexes and from `see-also.md` where a second folder is a genuinely strong fit.

---

# Use Cases Are First-Class Knowledge

This is mandatory.

A professional knowledge base must contain task-oriented knowledge, not only conceptual documentation.

For each major domain ask:

> What are the recurring questions or tasks a developer, analyst, architect, researcher, or operator performs?

Generate candidate use cases.

For banking examples include:

```text
How to retrieve customer data
How to resolve Party ID → Customer Number
How to retrieve agreements for a customer
How to retrieve accounts for an agreement
How to determine account ownership
How to find products belonging to a party
How to determine the settlement account
How to retrieve a securities portfolio
How to determine product eligibility
How to trace a payment
How to determine which service owns customer data
How to map an external identifier to an internal identifier
```

A use-case note should ideally link:

```text
Goal
→ business concepts
→ involved entities
→ business rules
→ systems
→ services
→ APIs
→ data
→ regulations
→ examples
→ known edge cases
```

This makes the use case a bridge between business and technical knowledge.

---

# Canonical Note Principle

Prefer one authoritative note per concept.

Example:

```text
party-id.md
customer-number.md
agreement.md
settlement-account.md
suitability-assessment.md
feature-leakage.md
model-drift.md
```

Other notes should link to these rather than redefining them.

---

# Atomicity Principle

Do not create giant notes such as:

```text
everything-about-customers.md
everything-about-machine-learning.md
```

Split reusable concepts into focused notes.

However, do not atomize blindly.

A note should represent one coherent concept, rule, interface, process, use case, decision, or explanation that is useful independently.

---

# Maps of Content

Give important domains their own `index.md` - a per-folder routing map. In this vault that IS the MOC; do not create a parallel `X-MOC.md` beside it.

Example:

```text
banking.md
customer-and-party-moc.md
securities-moc.md
machine-learning-moc.md
mlops-moc.md
```

A folder's `index.md` is a curated navigation surface, not merely a list of files. Its `Place here:` line says what belongs; its entries say what each note covers.

It should expose relationships.

Example:

```text
Customer
├── Identity
│   ├── Party
│   ├── Customer Number
│   └── Participant Number
├── Relationships
│   ├── Agreements
│   ├── Accounts
│   └── Products
├── Use Cases
│   ├── Resolve Party ID to Customer Number
│   └── Retrieve Products for Customer
└── Systems
    ├── Customer Service
    └── Customer API
```

---

# Metadata Strategy

Where appropriate, recommend lightweight YAML frontmatter properties.

Example:

```yaml
---
type: concept
domain: banking
subdomain: customer
status: verified
aliases:
  - Party Identifier
related:
  - Customer Number
  - Agreement
---
```

Useful `type` values may include:

```text
concept
entity
use-case
business-rule
process
api
service
system
data-model
regulation
tutorial
reference
decision
incident
research
experiment
paper
example
```

Do not create dozens of metadata fields without a concrete retrieval use.

---

# Naming Rules

Names must be descriptive and searchable.

Prefer:

```text
resolve-party-id-to-customer-number.md
settlement-account.md
suitability-assessment.md
customer-api.md
model-drift.md
feature-leakage.md
```

Avoid:

```text
notes1.md
customer-stuff.md
misc-api.md
important.md
general.md
```

Use aliases for:

- abbreviations
- German/English terminology
- internal terminology
- synonyms
- legacy terminology

Example:

```yaml
aliases:
  - Geeignetheitserklärung
  - Suitability Statement
  - GEE
```

---

# Domain-Specific Reasoning: Banking

When the domain is banking, do NOT reduce banking to accounts, payments and regulation.

Evaluate at least the following domain landscape.

```text
banking/
├── banking-fundamentals/
├── customer-and-party/
├── identity-and-identifiers/
├── customer-relationships/
├── products-and-services/
├── accounts/
├── payments/
├── cards/
├── lending-and-credit/
├── deposits/
├── securities-and-investments/
├── trading/
├── brokerage/
├── custody-and-settlement/
├── wealth-management/
├── advisory/
├── portfolio-management/
├── pricing-and-fees/
├── risk/
├── fraud/
├── aml-and-financial-crime/
├── kyc/
├── regulatory-and-compliance/
├── tax/
├── reporting/
├── accounting-and-ledger/
├── documents-and-communication/
├── channels/
├── business-processes/
├── business-rules/
├── use-cases/
├── architecture/
├── systems/
├── services/
├── apis/
├── events-and-messaging/
├── data-and-models/
├── integrations/
├── security-and-authorization/
├── operations-and-support/
├── decisions-and-adrs/
├── troubleshooting/
├── tutorials/
└── glossary/
```

This is a **coverage checklist**, NOT a mandatory folder tree.

Determine which items should become:

- top-level folders
- subfolders
- MOCs
- properties
- tags
- linked notes

based on the actual scope.

---

# Banking Entity Reasoning

Banking knowledge is highly relationship-oriented.

Explicitly model relationships such as:

```text
Person
→ Party
→ Customer
→ Customer Identifier
→ Agreement
→ Product
→ Account
→ Portfolio / Depot
→ Position
→ Transaction
```

Do NOT assume these are universally identical.

Document:

- definition
- identifier
- ownership
- cardinality
- lifecycle
- source system
- relevant API
- business rules
- ambiguities
- synonyms
- examples

When terminology is organization-specific or uncertain, mark it explicitly instead of inventing an answer.

---

# Banking Technical Knowledge

For every important business capability, investigate whether the knowledge architecture needs to represent:

```text
Business Capability
→ Process
→ Application/System
→ Service
→ API
→ Operation/Endpoint
→ Request/Response
→ Domain Object
→ Database/Data Source
→ Downstream/Upstream Dependency
```

Example:

```text
Retrieve Customer Products
→ Customer/Product capability
→ Customer Service
→ Product Relationship API
→ GET operation
→ Party ID input
→ Product relationships response
```

The vault should make it possible to navigate in both directions.

---

# Banking Regulation Reasoning

Do not create one giant `Regulation.md`.

Organize regulation by meaningful concerns such as:

```text
Investor Protection
Payments
AML
KYC
Data Protection
Market Conduct
Securities
Advisory
Reporting
Operational Resilience
Risk
Tax
```

Then connect individual regulations to:

```text
Regulation
→ obligation
→ affected business process
→ affected product
→ affected system
→ implementation/business rule
→ evidence/document
```

A regulation note should answer not only:

> What does this regulation say?

but also:

> What changes in the business or software because of it?

---

# Domain-Specific Reasoning: Machine Learning

For Machine Learning, evaluate at least:

```text
machine-learning/
├── foundations/
├── mathematics/
├── statistics-and-probability/
├── data/
├── data-quality/
├── exploratory-data-analysis/
├── feature-engineering/
├── algorithms/
├── supervised-learning/
├── unsupervised-learning/
├── deep-learning/
├── nlp/
├── computer-vision/
├── time-series/
├── representation-learning/
├── generative-ai/
├── llms/
├── evaluation/
├── metrics/
├── experimentation/
├── interpretability/
├── robustness/
├── bias-and-fairness/
├── training/
├── hyperparameter-optimization/
├── pipelines/
├── mlops/
├── deployment/
├── serving-and-inference/
├── monitoring/
├── drift/
├── feature-stores/
├── model-registry/
├── data-versioning/
├── model-versioning/
├── infrastructure/
├── research-papers/
├── experiments/
├── implementations/
├── use-cases/
├── tutorials/
└── troubleshooting/
```

Again: this is a reasoning checklist, not a mandatory folder tree.

---

# ML Relationship Reasoning

Machine-learning notes should connect theory with implementation.

Example:

```text
Mahalanobis Distance
→ covariance
→ multivariate statistics
→ anomaly detection
→ implementation
→ numerical stability
→ example
→ related experiments
```

Another example:

```text
Model Drift
→ distribution shift
→ monitoring
→ detection metrics
→ retraining
→ production pipeline
→ incidents
```

Another:

```text
Random Forest
→ supervised learning
→ decision trees
→ classification
→ regression
→ hyperparameters
→ evaluation
→ implementation
→ use cases
```

Avoid separating mathematical knowledge from engineering knowledge so aggressively that the relationships disappear.

---

# ML Use-Case Reasoning

Generate task-oriented notes such as:

```text
How to choose a classification metric
How to detect data leakage
How to compare two models
How to diagnose overfitting
How to handle imbalanced data
How to detect distribution shift
How to validate a time-series model
How to select a threshold
How to deploy a model
How to monitor model quality
How to reproduce an experiment
How to investigate degraded production performance
```

These should link to the underlying theory and technical references.

---

# Personal Knowledge / Tutorial Domains

For learning-oriented or personal domains, consider:

```text
concepts/
how-to/
tutorials/
examples/
reference/
mental-models/
questions/
experiments/
resources/
cheat-sheets/
lessons-learned/
```

But again, adapt rather than copy.

A tutorial should represent a learning journey.

A how-to should solve a concrete problem.

A concept note should explain one reusable concept.

A reference note should optimize lookup.

Do not mix all four into one giant note unless the subject is extremely small.

---

# Software / Engineering Domains

When the requested domain is technical, evaluate:

```text
Concepts
Architecture
Components
Libraries
Frameworks
Patterns
APIs
Configuration
Data
Security
Testing
Deployment
Observability
Performance
Troubleshooting
Use Cases
Examples
Decisions
Anti-Patterns
Best Practices
Tutorials
Reference
```

Also model:

```text
Problem
→ solution/pattern
→ implementation
→ trade-offs
→ failure modes
→ examples
```

---

# Research Domains

When the domain is research-heavy, evaluate:

```text
Research Questions
Hypotheses
Concepts
Theory
Methods
Datasets
Experiments
Results
Papers
Literature Notes
Claims
Evidence
Open Questions
Critiques
Ideas
Implementations
Reproductions
```

Important relationships include:

```text
Claim → Evidence
Paper → Method
Method → Experiment
Experiment → Result
Result → Interpretation
Question → Hypothesis
Hypothesis → Experiment
```

---

# Company/Internal Knowledge

When working with organization-specific knowledge, separate:

```text
Industry-standard knowledge
Organization-specific terminology
Organization-specific architecture
Organization-specific business rules
Organization-specific systems
Organization-specific APIs
Organization-specific decisions
```

Never silently mix general domain facts with internal assumptions.

Mark uncertain information.

Suggested status values:

```text
verified
partially-verified
inferred
open-question
deprecated
```

---

# Open Questions

Maintain explicit unresolved knowledge.

Example:

```text
open-questions/
```

or through properties:

```yaml
status: open-question
```

Examples:

```text
Is Participant Number identical to Agreement Number?
Which service is authoritative for Party ID mapping?
Is this API still the canonical source?
Does this business rule apply to all channels?
```

Do not hide uncertainty inside normal documentation.

---

# Knowledge Graph Behavior

Whenever creating or updating a note, ask:

1. What concept does this depend on?
2. What concepts depend on this?
3. Which use cases use it?
4. Which systems implement it?
5. Which APIs expose it?
6. Which business rules constrain it?
7. Which regulations influence it?
8. Which examples demonstrate it?
9. Which alternative terms refer to it?
10. Which notes would someone logically want next?

Add meaningful links accordingly.

Avoid meaningless mass-linking.

---

# Architecture Evaluation

Before finalizing a structure, mentally test it with realistic retrieval scenarios.

For banking test:

```text
Where would I document Party ID?
Where would I document how Party ID maps to Customer Number?
Where is the API performing that lookup?
Where is the service owning the operation?
Where is the underlying business rule?
Where is the customer entity model?
Where is the relevant regulation?
Where is a concrete example?
Where would I record an unresolved question?
Where would I record a production problem with this flow?
```

For ML test:

```text
Where is PCA explained?
Where is its mathematical derivation?
Where is implementation guidance?
Where is a practical PCA use case?
Where is an experiment using PCA?
Where are known limitations?
Where is troubleshooting?
Where is model monitoring?
```

If several answers are unclear, redesign the structure.

---

# Growth Test

Imagine the vault contains:

```text
10 notes
100 notes
1,000 notes
10,000 notes
```

The structure must still work.

Avoid structures that only look clean when nearly empty.

---

# Empty-Folder Rule

Do not generate hundreds of empty folders merely because they might eventually contain something.

Distinguish between:

### Known required structure

Create now.

### Probable future structure

Mention as an expansion point.

### Speculative structure

Do not create yet.

Architecture should be extensible without being bloated.

---

# Structure Evolution

The first architecture is not permanent.

When new notes expose a new stable category:

1. detect the emerging pattern
2. determine whether it deserves a folder, MOC, property, or tag
3. reorganize carefully
4. preserve links
5. avoid duplicate concepts
6. update the affected `index.md` files

Treat architecture as an evolving model of the user's knowledge.

---

# Existing Vault Behavior

If a vault already exists:

1. inspect the existing hierarchy
2. inspect representative notes
3. identify naming conventions
4. identify existing MOCs
5. identify metadata conventions
6. detect duplicates
7. detect overloaded folders
8. detect orphan notes
9. infer the user's mental model
10. propose changes before performing major restructuring

Do not replace a mature structure merely because another taxonomy looks cleaner.

---

# New Domain Procedure

When the user says:

> Create a knowledge structure for X.

perform this sequence:

```text
1. Classify X.
2. Identify major subdomains.
3. Identify important entities/concepts.
4. Identify actors.
5. Identify capabilities.
6. Identify recurring workflows/processes.
7. Identify practical use cases.
8. Identify technical systems/interfaces if applicable.
9. Identify data and identifiers.
10. Identify rules/regulation/governance.
11. Identify lifecycle/operations.
12. Identify learning and reference needs.
13. Identify research/experimentation needs if applicable.
14. Determine cross-cutting concerns.
15. Design the minimum useful hierarchy.
16. Design MOCs.
17. Define important note types.
18. Define useful metadata.
19. Define linking strategy.
20. Test realistic retrieval scenarios.
21. Test future growth.
22. Only then create directories/files.
```

---

# Required Output Before Creating Files

For a substantial new domain, first produce a concise architecture proposal containing:

## Domain Model

Important subdomains and why they matter.

## Retrieval Model

Typical questions/tasks the structure needs to support.

## Proposed Architecture

Directory tree.

## Note Types

Types of notes expected.

## Cross-Link Strategy

Important relationships that should be represented with links instead of folders.

## Example Notes

Give realistic examples.

## Growth Strategy

Explain where future categories would fit.

Only after this reasoning should the physical structure be created.

---

# Example: Banking Retrieval Graph

A useful banking knowledge graph might contain:

```text
Customer
   ↕
Party
   ↕
Identifiers
   ↕
Agreement
   ↕
Product
   ↕
Account / Depot
   ↕
Position
   ↕
Transaction
```

while simultaneously connecting:

```text
Use Case
→ Business Rule
→ Process
→ System
→ Service
→ API
→ Data
```

and:

```text
Regulation
→ Requirement
→ Business Rule
→ Process
→ System Behavior
```

These dimensions should intersect through links.

Do not force this graph into a single folder hierarchy.

---

# Example: ML Retrieval Graph

```text
Problem
→ Data
→ Features
→ Method
→ Model
→ Training
→ Evaluation
→ Experiment
→ Deployment
→ Monitoring
```

with theoretical relationships such as:

```text
Concept
→ Mathematics
→ Algorithm
→ Implementation
→ Use Case
```

and operational relationships:

```text
Production Problem
→ Metric
→ Diagnosis
→ Root Cause
→ Mitigation
→ Retraining / Deployment
```

---

# Final Quality Standard

A good knowledge architecture should let the user move naturally between:

```text
What is it?
        ↕

Why does it exist?
        ↕

How does it work?
        ↕

How do I use it?
        ↕

Where is it implemented?
        ↕

Which API/service/data provides it?
        ↕

Which rules constrain it?
        ↕

What can go wrong?
        ↕

How do I troubleshoot it?
        ↕

Where can I see an example?
```

The knowledge base must support both **learning** and **real work**.

Do not optimize for a beautiful empty directory tree.

Optimize for:

- retrieval
- understanding
- reuse
- discoverability
- relationships
- practical work
- maintainability
- growth
- low duplication
- explicit uncertainty

Most importantly:

> **Reason about the domain before reasoning about folders.**

A directory tree is only one projection of the underlying knowledge model.

Design the knowledge model first.