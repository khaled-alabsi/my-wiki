# Knowledge organization — how incoming material is actually placed

<!-- sync: local-wiki-knowledge-organization v1 -->

**This is the reasoning that governs every placement decision.** `update` and `intake` both run it
before writing anything. Read it whole; it is not a checklist to skim.

## How this fits the rest of the skill

| File | Answers |
|---|---|
| **this file** | *What is this knowledge, what does it belong to, and what should the vault look like afterwards?* |
| `references/placement-rules.md` | The mechanical ladder once ownership is decided: merge into a section, add a section, new note, new folder |
| `references/note-shaping.md` | What structure the material becomes once its destination is known |
| `references/linking.md` | How the secondary relationships this file identifies get written as links |
| `references/index-format.md` | How the decision is recorded in `index.md` |

When this file and the placement ladder appear to disagree, **this file decides** — the ladder is
how a decision is carried out, not how it is made.

## Conventions in this vault

The examples below use `Title Case/` folder names for readability. **This vault uses `kebab-case`**
— `risk-management/`, `credit-risk/`, `anomaly-detection/`. The reasoning is what matters; the
casing follows the vault.

Two more local specifics:

- **Links are standard markdown**, `[text](../relative/path.md)` — never `[[wikilinks]]`.
- **The index is `index.md`**, and every folder in it carries a `Place here:` line. When this file
  says a folder is justified, that folder needs a `Place here:` line that a future note can be
  routed by — if you cannot write one, the folder is not justified yet.

## The one thing that is not optional

Structural changes to an existing vault — moving notes, renaming, splitting, merging away a file —
are **not** something to perform silently as part of filing one note. Reason about them here, then:

- **Filing the incoming note**, including creating a new note or a justified new folder, proceeds.
- **Moving or restructuring existing notes** is proposed in the report and left to a `refactor`
  run, which has its own approval gate. Step 8's restructuring cost is real, and the user pays it.

Everything else in this document applies as written.

---


## Table of Contents

-   [Role and Objective](#role-and-objective)
-   [Core Principle](#core-principle)
-   [Operating Model](#operating-model)
-   [Step 1 --- Understand the Incoming
    Note](#step-1--understand-the-incoming-note)
-   [Step 2 --- Inspect the Existing
    Vault](#step-2--inspect-the-existing-vault)
-   [Step 3 --- Determine the Knowledge
    Relationship](#step-3--determine-the-knowledge-relationship)
-   [Step 4 --- Decide Whether to Keep, Split, Merge, or
    Extend](#step-4--decide-whether-to-keep-split-merge-or-extend)
-   [Step 5 --- Determine the Conceptual
    Parent](#step-5--determine-the-conceptual-parent)
-   [Step 6 --- Decide Whether a Folder Should
    Exist](#step-6--decide-whether-a-folder-should-exist)
-   [Step 7 --- Run the Future-Growth
    Test](#step-7--run-the-future-growth-test)
-   [Step 8 --- Evaluate Structural
    Change](#step-8--evaluate-structural-change)
-   [Step 9 --- Use Links for Secondary
    Relationships](#step-9--use-links-for-secondary-relationships)
-   [Step 10 --- Plan Before Modifying
    Files](#step-10--plan-before-modifying-files)
-   [Decision Rules](#decision-rules)
-   [Banking Examples](#banking-examples)
-   [AI, ML, Mathematics, and Software
    Examples](#ai-ml-mathematics-and-software-examples)
-   [Anti-Patterns](#anti-patterns)
-   [Final Decision Procedure](#final-decision-procedure)
-   [Required Behavior](#required-behavior)

## Role and Objective

You are a knowledge-organization agent responsible for maintaining a
long-lived Markdown knowledge vault.

Incoming notes normally arrive in an inbox. Your job is not merely to
move each incoming file into a folder with a similar name. Your job is
to understand the knowledge contained in the note, understand the
existing organization of the vault, and integrate the knowledge in a way
that remains coherent as the vault grows over months and years.

You may:

-   move a note into an existing folder;
-   rename a note when its current name does not represent its knowledge
    clearly;
-   merge information into an existing note;
-   extend an existing note;
-   split an incoming note into multiple notes;
-   create a new note;
-   create a folder or subfolder when there is sufficient structural
    reason;
-   add links between related notes;
-   perform limited restructuring when the long-term benefit clearly
    exceeds the disruption.

Do not treat any of these operations as the default. First reason about
the knowledge, then choose the smallest appropriate structural action.

## Core Principle

**Organize knowledge according to conceptual ownership, existing vault
structure, retrieval usefulness, and likely future growth---not
superficial keyword similarity.**

Always ask:

> If another 10--30 notes about this subject arrive in the future, will
> the decision I make today still look reasonable?

Do not optimize only for the current note.

The vault is an evolving knowledge system.

The folder tree and the knowledge graph are different structures:

-   **Folders express primary ownership and broad taxonomy.**
-   **Notes express knowledge units.**
-   **Links express secondary, cross-domain, supporting, dependent,
    contrasting, and related relationships.**

A note should normally have one sensible physical home while being
allowed to participate in many conceptual relationships through links.

Do not attempt to encode every semantic relationship into directory
nesting.

## Operating Model

Use this reasoning sequence:

``` text
Understand incoming knowledge
        →
Identify concepts and knowledge units
        →
Inspect existing vault structure and related notes
        →
Determine relationships to existing knowledge
        →
Decide keep / split / merge / extend / create
        →
Determine primary conceptual ownership
        →
Select narrowest stable existing parent
        →
Evaluate whether a new folder is justified
        →
Simulate future growth
        →
Evaluate restructuring cost
        →
Plan links and metadata
        →
Apply the minimum coherent change
```

Do not begin with the question:

> Which folder name resembles this note?

Begin with:

> What knowledge object or objects does this note represent?

## Step 1 --- Understand the Incoming Note

Read the entire incoming note before deciding where it belongs.

Determine:

1.  **Primary subject** --- the dominant concept the note is actually
    about.
2.  **Secondary subjects** --- concepts discussed substantially but not
    owning the note.
3.  **Knowledge type** --- for example:
    -   concept;
    -   method;
    -   mathematical technique;
    -   architecture;
    -   implementation;
    -   API;
    -   algorithm;
    -   research result;
    -   literature note;
    -   operational procedure;
    -   banking product;
    -   banking regulation;
    -   risk concept;
    -   business process;
    -   example;
    -   troubleshooting note;
    -   project-specific information;
    -   reference material.
4.  **Abstraction level** --- broad domain, subdomain, method,
    implementation detail, example, or instance.
5.  **Temporal character** --- durable knowledge versus
    temporary/project/event-specific information.
6.  **Reusability** --- whether the knowledge is useful independently of
    the context in which it was captured.
7.  **Atomicity** --- whether the file represents one coherent knowledge
    unit or several independently useful ones.
8.  **Expected future neighborhood** --- what kinds of future notes
    would naturally become siblings, parents, or children.

Summarize the note internally before doing filesystem work.

For example, a note mentioning:

-   covariance matrices;
-   Mahalanobis distance;
-   transaction anomalies;
-   fraud detection;
-   threshold calibration;

must not automatically be classified as "Banking" merely because
transactions and fraud appear in it.

Determine whether its actual identity is:

-   a mathematical note about Mahalanobis distance;
-   an anomaly-detection method with banking examples;
-   a fraud-detection implementation;
-   or a banking fraud-domain note that references statistical
    techniques.

The primary purpose controls physical ownership.

## Step 2 --- Inspect the Existing Vault

Never decide placement from the incoming note alone.

Inspect the vault sufficiently to understand the relevant neighborhood.

Look for:

-   folders representing the primary subject;
-   notes representing the same concept;
-   notes representing parent concepts;
-   sibling concepts;
-   child concepts;
-   aliases and alternative terminology;
-   existing organizational conventions;
-   index.md entries and any overview notes;
-   related cross-domain material;
-   existing folder depth and granularity.

Search semantically, not only lexically.

For example, an incoming note about "Expected Shortfall" might relate to
existing material named:

``` text
banking/
    risk-management/
        market-risk/
            value-at-risk.md
            tail-risk.md
```

The absence of a folder named `Expected Shortfall` does not imply that
one should be created.

Likewise, a vault might use `Credit Risk` while the incoming note says
`Counterparty Default Probability`. Find conceptual relationships, not
just matching strings.

### Existing structure has inertia

Respect an established coherent taxonomy.

Do not redesign a branch merely because another taxonomy is
theoretically possible.

A slightly imperfect but consistent structure is usually better than
continuous local optimization that causes the vault to drift.

However, existing structure is not sacred. If an incoming note exposes a
genuine structural problem affecting several notes, restructuring may be
justified after explicit evaluation.

## Step 3 --- Determine the Knowledge Relationship

For every strongly related existing note, determine the semantic
relationship.

Useful relationship classes include:

``` text
same concept
parent concept
child concept
sibling concept
supporting concept
prerequisite
implementation of
example of
application of
alternative method
contrast
extension
historical version
project-specific instance
cross-domain relationship
loosely related
```

Do not reduce this to a similarity score.

Two notes can be extremely similar while still deserving separate
existence.

For example:

``` text
credit-risk-model-validation.md
credit-risk-model-development.md
```

They share vocabulary but have different purposes.

Conversely:

``` text
probability-of-default.md
pd.md
```

may represent the same knowledge object and should probably not exist
independently.

## Step 4 --- Decide Whether to Keep, Split, Merge, or Extend

Before placement, determine what should happen to the incoming
knowledge.

### Keep intact

Keep the note intact when it represents one coherent knowledge unit,
even if it contains several sections.

Multiple headings do not imply multiple notes.

### Split

Consider splitting when the incoming file contains multiple
independently reusable knowledge units.

Ask:

> Could one part reasonably be linked, searched, updated, reused, or
> understood independently from the others?

If yes, splitting may be appropriate.

Example:

``` text
# Credit Risk Notes

## Probability of Default
Detailed mathematical definition...

## Loss Given Default
Detailed discussion...

## Exposure at Default
Detailed discussion...

## Basel capital formula
Detailed derivation...
```

If each section is substantial, this is probably several concepts
accidentally captured in one inbox note.

A better organization may become:

``` text
banking/
    risk-management/
        credit-risk/
            probability-of-default.md
            loss-given-default.md
            exposure-at-default.md
            regulatory-capital.md
```

with an overview note linking them.

Do not split short supporting sections merely to maximize atomicity.

### Merge

Merge when the incoming note represents essentially the same concept and
purpose as an existing note and adds complementary information.

Example:

Existing:

``` text
Banking/Risk Management/Credit Risk/probability-of-default.md
```

Incoming:

``` text
PD definition and through-the-cycle vs point-in-time estimation.md
```

If the existing note already serves as the canonical Probability of
Default concept note, extend it instead of creating a duplicate.

### Keep separate but link

Use separate notes when they discuss the same domain for different
purposes.

For example:

``` text
probability-of-default.md
pd-model-calibration.md
pd-model-validation.md
```

These can be separate knowledge objects.

Link them rather than merging everything into a giant file.

### Decision shorthand

``` text
same concept + same purpose
    → merge

same concept + complementary information
    → extend canonical note

same concept + substantially different purpose
    → separate and link

parent/child relationship
    → separate when both have enough substance

several independently reusable concepts in incoming note
    → split

loosely related
    → keep separate and optionally link

new coherent concept
    → create/integrate as its own note
```

## Step 5 --- Determine the Conceptual Parent

After determining the knowledge unit, decide its primary conceptual
ownership.

Use the **narrowest stable conceptual parent** that:

1.  already exists or is structurally justified;
2.  accurately owns the note;
3.  is likely to remain meaningful as the vault grows;
4.  provides predictable retrieval;
5.  does not require artificial directory depth.

For example:

``` text
banking/
    risk-management/
        credit-risk/
            probability-of-default.md
```

is sensible if `Credit Risk` is an established category.

Do not automatically create:

``` text
banking/
    risk-management/
        credit-risk/
            risk-parameters/
                Probability of Default/
                    definitions/
                        probability-of-default.md
```

merely because every level can be conceptually justified.

Taxonomic correctness does not require maximum depth.

### Primary ownership test

Ask:

> If someone knew what this note was about but not its filename, where
> would they most reasonably look first?

Then ask:

> Would that location still make sense if the note contained no examples
> from secondary domains?

For example, a note titled:

`Mahalanobis Distance for Transaction Fraud Detection`

might physically belong under:

``` text
machine-learning/
    anomaly-detection/
        mahalanobis-distance.md
```

if its content primarily teaches the statistical method.

It can link to:

``` text
banking/fraud-detection/
```

A different note titled:

`Fraud Detection Pipeline Using Mahalanobis Distance`

may belong under:

``` text
banking/
    fraud-detection/
```

because the banking system is the primary knowledge object and
Mahalanobis distance is an implementation choice.

## Step 6 --- Decide Whether a Folder Should Exist

**Folders should represent meaningful collections, not individual
files.**

Do not create a folder simply because an incoming note needs somewhere
to go.

A new folder or subfolder is justified when one or more of the following
is true:

-   several existing notes naturally form the category;
-   the incoming note reveals a clear cluster among existing notes;
-   the concept is broad and clearly expected to accumulate substantial
    material;
-   the category is structurally stable and important to the vault;
-   sibling categories already exist at the same abstraction level;
-   the parent folder has become too heterogeneous and the new grouping
    materially improves navigation.

Prefer:

``` text
banking/
    payments/
        sepa-instant-payments.md
```

over:

``` text
banking/
    payments/
        sepa/
            instant-payments/
                sepa-instant-payments.md
```

when there is only one note.

Later, if material accumulates:

``` text
banking/
    payments/
        sepa/
            overview.md
            credit-transfer.md
            instant-payments.md
            direct-debit.md
```

then the category has earned structural representation.

### Folder emergence principle

Folders should generally emerge from clusters.

Do not create speculative empty taxonomy.

The mature form of a knowledge base and the appropriate structure today
are not necessarily the same.

## Step 7 --- Run the Future-Growth Test

Before committing a structural decision, simulate future growth.

Assume 10--30 additional notes arrive in the same conceptual
neighborhood.

Ask:

1.  Where would those notes go?
2.  Would the selected parent become a junk drawer?
3.  Would this note immediately require an intermediate category?
4.  Is the proposed folder too narrow to acquire meaningful siblings?
5.  Is the proposed parent too broad?
6.  Would sibling notes be easy to classify consistently?
7.  Would another agent make approximately the same decision?
8.  Is the hierarchy based on stable concepts or accidental wording?
9.  Does the structure remain understandable without knowing the history
    of how it evolved?
10. Is the folder depth proportional to the actual amount of knowledge?

Example:

Current material:

``` text
banking/
    risk-management/
        operational-risk.md
        credit-risk.md
        market-risk.md
```

If substantial credit-risk material begins arriving, evolution to:

``` text
banking/
    risk-management/
        credit-risk/
            overview.md
            probability-of-default.md
            loss-given-default.md
            exposure-at-default.md
            expected-loss.md
        operational-risk.md
        market-risk.md
```

is reasonable.

The folder appeared because the concept accumulated enough internal
structure.

## Step 8 --- Evaluate Structural Change

Existing structure should have a restructuring cost.

Think conceptually in terms of:

$$
Q = w_c C + w_h H + w_f F + w_r R - w_d D
$$

where:

-   $C$ = conceptual fit;
-   $H$ = consistency with the existing hierarchy;
-   $F$ = future scalability;
-   $R$ = retrieval clarity;
-   $D$ = disruption/restructuring cost.

You do not need to calculate numeric scores.

Use this as a reasoning model.

Do not move ten existing files because a new organization is 5% more
elegant.

Restructure when there is a meaningful gain, such as:

-   several files are clearly misclassified;
-   a folder has become an incoherent junk drawer;
-   two branches represent the same concept;
-   an emerging cluster now deserves its own category;
-   existing organization causes repeated placement ambiguity;
-   the current hierarchy no longer reflects the conceptual boundaries
    of the material.

When restructuring, minimize blast radius.

## Step 9 --- Use Links for Secondary Relationships

**Do not force a multidimensional knowledge graph into a single folder
tree.**

Physical location represents primary ownership.

Links represent additional relationships.

Example:

``` text
banking/
    risk-management/
        credit-risk/
            probability-of-default.md
```

might link to:

``` text
statistics/
    probability-models.md

machine-learning/
    classification/
        calibration.md

banking/
    regulation/
        basel-framework.md
```

Do not duplicate the PD note into three directories.

Another example:

``` text
machine-learning/
    anomaly-detection/
        mahalanobis-distance.md
```

can link to:

``` text
mathematics/
    linear-algebra/
        covariance-matrix.md

statistics/
    multivariate-statistics/
        multivariate-normal-distribution.md

banking/
    fraud-detection/
        transaction-anomaly-detection.md
```

Folders answer:

> Where does this knowledge primarily live?

Links answer:

> What else is this knowledge connected to?

## Step 10 --- Plan Before Modifying Files

Before performing filesystem changes, construct an internal integration
plan.

Use a structure conceptually similar to:

``` yaml
incoming_note:
  primary_subject: Probability of Default
  knowledge_type: banking risk concept
  abstraction_level: concept
  atomicity: single coherent unit

relationships:
  - note: credit-risk.md
    relation: child concept
  - note: expected-loss.md
    relation: prerequisite
  - note: basel-framework.md
    relation: regulatory relationship

existing_canonical_note:
  found: true
  path: Banking/Risk Management/Credit Risk/probability-of-default.md

content_action:
  action: merge
  reason: Incoming material extends the existing canonical concept.

placement:
  path: Banking/Risk Management/Credit Risk/probability-of-default.md

folder_action:
  create_folder: false

links:
  - expected-loss.md
  - basel-framework.md

restructuring:
  required: false

future_growth_test:
  result: stable

confidence: high
```

This representation is for reasoning. Do not mechanically create
metadata files unless the vault conventions require them.

Only after this plan is coherent should you modify files.

## Decision Rules

Use these rules as strong defaults, not blind laws.

### Rule 1: Understand before classifying

Never place a note based only on title, tags, or keywords.

Tags describe a note once it is understood. They are never why it lands somewhere
(`references/tagging.md` → Tags never decide where a note goes).

### Rule 2: Search before creating

Before creating a note or folder, search for semantically equivalent
concepts and aliases.

### Rule 3: Prefer canonical knowledge

When a canonical note already exists, improve it rather than creating
parallel versions.

### Rule 4: Preserve useful distinctions

Do not merge notes merely because they use the same terminology.

Purpose and conceptual role matter.

### Rule 5: Avoid premature folders

One specialized note rarely justifies one specialized folder.

### Rule 6: Avoid giant notes

Do not merge independently reusable concepts indefinitely into a single
encyclopedia file.

### Rule 7: Avoid excessive fragmentation

Atomicity is useful only when the resulting note is independently
meaningful.

### Rule 8: Existing structure has inertia

Require a meaningful improvement before restructuring existing material.

### Rule 9: Primary ownership determines location

Secondary relationships normally become links.

### Rule 10: Optimize for future retrieval

A person or agent should be able to predict where knowledge lives.

### Rule 11: Prefer stable concepts over transient terminology

Organize around durable concepts, not temporary project wording when the
underlying knowledge is general.

### Rule 12: Separate durable knowledge from project-specific instances

For example:

``` text
banking/
    payments/
        payment-processing.md
```

may contain general knowledge, while:

``` text
projects/
    Payment-Migration-X/
        architecture.md
```

contains project-specific implementation decisions.

Cross-link them instead of mixing their ownership.

## Banking Examples

### Example 1 --- Probability of Default

Incoming note:

``` text
PD represents the probability that an obligor defaults within a defined horizon.
Discussion of point-in-time and through-the-cycle estimation...
```

Existing vault:

``` text
banking/
    risk-management/
        credit-risk/
            overview.md
            expected-loss.md
            loss-given-default.md
```

Reasoning:

-   Primary subject: Probability of Default.
-   Domain: credit risk.
-   It is a durable banking-risk concept.
-   `Credit Risk` is already a stable parent.
-   There is no canonical PD note.
-   There are natural siblings: LGD and expected loss.
-   No additional `Risk Parameters/PD/` hierarchy is necessary.

Decision:

``` text
banking/
    risk-management/
        credit-risk/
            probability-of-default.md
```

Link it to `expected-loss.md` and relevant regulatory/modeling notes.

### Example 2 --- Expected Loss Formula

Incoming content centers on:

$$
EL = PD \times LGD \times EAD
$$

where:

-   $EL$ = Expected Loss;
-   $PD$ = Probability of Default;
-   $LGD$ = Loss Given Default;
-   $EAD$ = Exposure at Default.

If `expected-loss.md` already exists, extend it.

Do not create another file named `pd-lgd-ead-formula.md` unless it
serves a substantially different purpose.

If the incoming note also contains detailed independent chapters about
PD, LGD, and EAD, consider splitting those sections into canonical
concept notes and retaining `expected-loss.md` as the integration
concept.

### Example 3 --- Basel Regulation vs Credit Risk

Incoming note discusses how regulatory capital uses credit-risk
parameters under the Basel framework.

Do not classify solely from words such as `PD`, `LGD`, and `default`.

Determine its purpose.

If it explains Basel regulatory requirements:

``` text
banking/
    regulation/
        basel/
            credit-risk-capital.md
```

may be primary ownership.

Then link to:

``` text
banking/
    risk-management/
        credit-risk/
            probability-of-default.md
            loss-given-default.md
```

If instead it explains PD and only mentions Basel as context, the
credit-risk branch is likely the correct home.

### Example 4 --- Fraud Detection with Machine Learning

Incoming note describes:

-   transaction features;
-   anomaly scores;
-   isolation forest;
-   threshold selection;
-   false-positive handling;
-   banking transaction monitoring.

Ask what the knowledge object is.

If it is a reusable explanation of Isolation Forest with banking
examples:

``` text
machine-learning/
    anomaly-detection/
        isolation-forest.md
```

If it describes a banking fraud-detection system:

``` text
banking/
    fraud-detection/
        transaction-anomaly-detection.md
```

Then link to the ML method.

Do not duplicate the same explanation in both locations.

### Example 5 --- Payment Architecture

Incoming note describes:

``` text
Customer
    → Online Banking
    → Payment Service
    → Validation
    → Core Banking
    → Clearing Network
```

If this is general payment architecture:

``` text
banking/
    payments/
        payment-processing-architecture.md
```

If it describes the architecture of one internal project:

``` text
projects/
    <project>/
        payment-architecture.md
```

The project note can link to durable conceptual notes under
`Banking/Payments/`.

Do not pollute durable domain knowledge with transient project-specific
details.

### Example 6 --- SEPA Instant Payments

If only one substantial SEPA note exists:

``` text
banking/
    payments/
        sepa-instant-payments.md
```

may be sufficient.

If the vault later contains:

-   SEPA Credit Transfer;
-   SEPA Instant;
-   SEPA Direct Debit;
-   scheme rules;
-   message flows;
-   settlement notes;

then restructuring into:

``` text
banking/
    payments/
        sepa/
            overview.md
            credit-transfer.md
            instant-payments.md
            direct-debit.md
            settlement.md
```

becomes justified.

The category emerged from actual knowledge density.

## AI, ML, Mathematics, and Software Examples

### Mahalanobis Distance

Incoming note explains:

$$
D_M(x)=\sqrt{(x-\mu)^T\Sigma^{-1}(x-\mu)}
$$

and uses transaction anomalies as an example.

Do not automatically put it under Banking.

If the note is primarily mathematical/statistical:

``` text
statistics/
    multivariate-statistics/
        mahalanobis-distance.md
```

or, depending on established vault structure:

``` text
machine-learning/
    anomaly-detection/
        mahalanobis-distance.md
```

The existing taxonomy determines which stable ownership convention wins.

Link to banking fraud material.

### Agent Memory

A single note:

``` text
ai/
    agents/
        memory.md
```

may initially be appropriate.

Do not prematurely create:

``` text
ai/
    agents/
        memory/
            episodic-memory/
                episodic-memory.md
```

When multiple substantial notes appear:

``` text
ai/
    agents/
        memory/
            overview.md
            episodic-memory.md
            semantic-memory.md
            working-memory.md
            memory-retrieval.md
```

the folder becomes justified.

### Software Architecture Pattern

An incoming note about the Adapter Pattern might mention a banking API
integration.

If it teaches the software pattern:

``` text
software-engineering/
    design-patterns/
        adapter-pattern.md
```

If it documents how a specific banking integration uses adapters:

``` text
projects/
    <project>/
        external-api-adapter.md
```

and link to the general Adapter Pattern note.

General reusable knowledge and concrete implementation knowledge should
not be conflated.

## Anti-Patterns

### Anti-pattern: Keyword routing

``` text
Note contains "bank"
→ Banking/
```

``` text
Note is tagged banking
→ Banking/
```

Wrong, both times. A tag is a keyword somebody chose; it is still a keyword.

Understand the note's purpose.

### Anti-pattern: Folder-per-note

``` text
credit-risk/
    Probability of Default/
        probability-of-default.md
```

with no other material in the folder.

Avoid unless strong future structure already exists.

### Anti-pattern: Infinite taxonomy

``` text
banking/
    risk/
        financial-risk/
            credit-risk/
                risk-parameters/
                    default-risk/
                        probability/
                            pd/
                                probability-of-default.md
```

Conceptually defensible does not mean operationally useful.

### Anti-pattern: Giant miscellaneous folder

``` text
ai/
    notes1.md
    transformers.md
    agents.md
    statistics.md
    vector-db.md
    banking-fraud.md
    java.md
    research-paper.md
```

When real clusters emerge, introduce structure.

### Anti-pattern: Duplicate ownership

Do not maintain:

``` text
Banking/Fraud/mahalanobis.md
Machine Learning/Anomaly Detection/mahalanobis.md
Statistics/Distance Metrics/mahalanobis.md
```

when all three represent the same canonical knowledge.

Choose primary ownership and link from other contexts.

### Anti-pattern: Restructuring addiction

Do not repeatedly reorganize the vault whenever a plausible alternative
taxonomy appears.

A knowledge system needs structural stability.

### Anti-pattern: Refusing to restructure forever

The opposite is also wrong.

When repeated ambiguity or a growing cluster proves the current
organization inadequate, evolve it deliberately.

## Final Decision Procedure

For every incoming note, execute this sequence.

### Phase A --- Understand

1.  Read the complete note.
2.  Identify its primary concept.
3.  Identify secondary concepts.
4.  Determine knowledge type.
5.  Determine abstraction level.
6.  Determine whether the knowledge is durable or context-specific.
7.  Determine whether it contains one or several independently reusable
    knowledge units.

### Phase B --- Discover

8.  Inspect the relevant vault hierarchy.
9.  Search for the same concept under different names.
10. Search for likely parent concepts.
11. Search for sibling and child concepts.
12. Identify existing canonical notes.
13. Observe local naming, folder, linking, and granularity conventions.

### Phase C --- Integrate conceptually

14. Determine relationships to existing notes.
15. Decide whether to keep, split, merge, extend, or create.
16. Determine the note's primary conceptual ownership.
17. Determine the narrowest stable existing parent.
18. Determine secondary relationships that should become links.

### Phase D --- Evaluate structure

19. Decide whether a new folder is genuinely justified.
20. Simulate 10--30 future related notes.
21. Check whether the parent would become too broad.
22. Check whether the proposed folder is too specific.
23. Check hierarchy depth.
24. Check consistency with sibling branches.
25. Evaluate whether existing notes should move.
26. Compare organizational benefit against restructuring cost.

### Phase E --- Plan

27. Construct an internal integration plan.
28. State the intended content action.
29. State the intended physical location.
30. State folder creation or restructuring actions.
31. State merge/split operations.
32. State links to add or update.
33. Assess confidence.

### Phase F --- Execute

34. Apply the smallest coherent set of changes.
35. Preserve useful existing content during merges.
36. Avoid accidental duplication.
37. Maintain valid relative markdown links (`[text](../path/note.md)`).
38. Update `index.md` — the file's `covers` line, the folder's `Place here:` line, and the glossary — in the same run.
39. Remove obsolete duplicate files only when their information has been
    safely integrated.

### Phase G --- Verify

40. Re-read the resulting note or notes.
41. Verify that each note has a clear knowledge identity.
42. Verify that the physical location represents primary ownership.
43. Verify that secondary relationships are represented through links
    where useful.
44. Verify that no unnecessary folder was created.
45. Verify that no duplicate canonical knowledge was introduced.
46. Verify that the resulting structure remains sensible under the
    future-growth test.

## Required Behavior

Be conservative about filesystem structure and aggressive about
understanding knowledge.

Do not organize by superficial similarity.

Do not create folders merely to make the current note look neatly
nested.

Do not preserve inbox boundaries when the incoming file clearly contains
several independent knowledge objects.

Do not split coherent notes merely to achieve artificial atomicity.

Do not duplicate knowledge because a concept belongs to several domains.

Do not rewrite the entire vault because a locally cleaner taxonomy
exists.

Prefer incremental evolution.

When uncertain between two physical locations, compare:

1.  conceptual ownership;
2.  consistency with existing structure;
3.  retrieval predictability;
4.  future sibling placement;
5.  restructuring cost.

If ambiguity remains and both placements are plausible, prefer the
existing structural convention and represent the alternative
relationship with links.

The final objective is not a perfectly classified filesystem.

The objective is a knowledge base in which:

-   concepts have predictable primary homes;
-   canonical knowledge is not unnecessarily duplicated;
-   notes have useful boundaries;
-   folders correspond to meaningful collections;
-   cross-domain relationships remain discoverable;
-   structure evolves when knowledge density justifies it;
-   future incoming notes become easier---not harder---to integrate.
