# HOW TO PLAN

A template and rules for writing implementation plans that a coding agent can execute without ambiguity.

-----

## Document Structure

Every plan has exactly two top-level sections in this order:

### Section 1 — Background & Goal

- What the project is
- Why it exists
- What it must achieve
- Nothing else

### Section 2 — Phases

The actual execution plan. Contains only phases, numbered Phase 1, Phase 2, Phase 3… sequentially from 1.

Phase numbers are independent of section numbers — Phase 1 is always “Phase 1”, never “Section 2.1” or “7. Phase 1”.

Everything the phase needs lives inside the phase:

- Repository structure it creates or depends on
- Metric formulas it implements
- Configuration defaults it uses
- Skill definitions for any sub-agent it spawns

-----

## Phase Template

Every phase must contain all of the following subsections in this order:

```
## Phase N — [Name]

**Paper §§:** [source document references]
**Goal:** [1–2 sentences. What this phase produces and why it matters.]

### Input AC
[Table or list of conditions that must ALL be true before this phase starts.
Each condition is checkable without running the phase:
a file exists, a count threshold is met, a test passes.
The Input AC of Phase N must be fully satisfied by the Output AC of Phase N-1.]

### Tasks
[Numbered list of concrete tasks. Each task specifies:
- What to build or run
- What inputs it reads
- What outputs it writes
- Which skill to spin up (if LLM involved), with full skill definition inline]

### Deliverables
[Exact list of files/artifacts this phase produces.
Every file listed here must appear in the Output AC.]

### Output AC
[Table of conditions that must ALL be true for this phase to be considered done.
Each condition is checkable: file exists, count ≥ N, test passes, format valid.
Must cover every deliverable listed above.
The Output AC of Phase N must fully imply the Input AC of Phase N+1.]
```

-----

## Skill Definition (inline in the Task that uses it)

When a task spawns a sub-agent, define the skill inline under that task:

```
**Skill: [skill_name]**
- Purpose: [one sentence]
- Determinism: temperature=0
- Input schema: [JSON]
- Output schema: [JSON — sub-agent returns this only, no preamble]
- Rules: [constraints the sub-agent must follow]
```

-----

## Rules

**Phase numbers:** Phase 1, Phase 2… never prefixed by section numbers.

**Sub-sections:** Phase N uses §N.1, §N.2 etc.

**Input AC:** Checkable without running the phase. References specific files, counts, or test results.

- Bad: “Phase 1 is complete”
- Good: “`components.json` exists and validates against schema for ≥ 3 apps”

**Output AC:** Checkable without running the next phase. Every deliverable must appear here.

**GO/NO-GO gates:** Any phase that can partially fail must specify what is fatal vs. recoverable in its Output AC.

**Tasks:** Specific enough that the agent makes no design decisions. Every LLM call names its skill and defines it inline.

-----

## Anti-patterns

|Anti-pattern                                           |Why wrong                               |
|-------------------------------------------------------|----------------------------------------|
|Phase numbered by document position (e.g. “7. Phase 1”)|Phase numbers must be stable            |
|“Run script X” without specifying what X does          |Agent has to invent it                  |
|Input AC says “previous phase complete”                |Not checkable                           |
|Output AC missing a deliverable                        |Agent cannot verify success             |
|Skill definitions outside the task that uses them      |Plan is not self-contained              |
|Metrics, config, repo structure in a separate section  |They belong in the phase that needs them|
|Phase that asks the user a question at runtime         |Decisions belong in the plan            |