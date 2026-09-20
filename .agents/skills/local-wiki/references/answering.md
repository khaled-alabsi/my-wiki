# Answering a question from the vault

<!-- sync: local-wiki-answering v1 -->

`references/modes/ask.md` is the workflow — the order of the steps and what each one runs. This file
is the reasoning inside four of them: how a question is understood, how the search is planned and
re-planned, how an answer is composed, and how it is verified before anybody reads it.

The failure this exists to prevent is not a missing note. It is a fluent answer to a question
nobody asked, built from three notes that happened to match, with the part the vault never covered
quietly smoothed over.

## 1. Read the question before searching for it

Name three things, in one line each:

- **Type** — definition, process, comparison, impact ("what does X change for Y"), troubleshooting,
  inventory ("what do we have on X"), or history ("what did we decide about X"). The type picks the
  answer's structure in section 4 and the graph relations worth traversing.
- **Scope** — one note's worth, one folder's worth, or across the vault. A question whose scope is
  one note does not get a research pipeline.
- **What would satisfy it** — the shape of a good answer: a term and its meaning, an ordered
  process, a table of differences, a chain of cause and effect, a yes or no with its condition.

A question carrying two questions is split here and answered as two, each with its own sources.

## 2. The assumption ledger — the step that invents things if it is not bounded

Restating a question in the vault's own vocabulary is what makes the search work. It is also where
an agent quietly replaces the user's question with a more answerable one, answers that, and never
says so.

So every restatement is written down, and **every assumption in it carries its ground**:

```
Question as asked:  "how do we handle a client who fails the check?"
Question as read:   "what happens when a retail client fails the appropriateness check during
                     onboarding, per the escalation matrix?"

Assumptions
- "the check" = the appropriateness check ...... grounded: processes/onboarding.md ## Checks is the
                                                 only check in the onboarding path
- "we" = the onboarding process, not support ... grounded: glossary, "we" is used for the bank's
                                                 process in every note that defines it
- client type = retail ......................... UNGROUNDED
```

- **Grounded** means a note, a glossary entry or a graph edge says so, and it is named. Not "it is
  obvious", not "it usually means".
- **An ungrounded assumption is dropped or asked about.** Dropped means the answer covers both
  readings, or states that it covers one and which. Asked means one short question to the user —
  only when the two readings give materially different answers, which is the same bar as everywhere
  else in this skill.
- **The ledger is shown with the answer**, never kept in the agent's head. A reader who disagrees
  with a reading must be able to see it without asking.
- **Motivation is inferred only as far as the vault supports it**, and it is labelled as inference.
  "You are probably asking because of the PSD3 migration" is a guess about a person; "the vault
  links this to the PSD3 migration note" is a fact about the vault. Only the second is written.

## 3. Plan the search, then search twice

**The plan comes before the searching**, and it names what would count as missing:

- which terms, in the vault's vocabulary and the user's own
- which folders the index routes the question to, and which it does not — an answer that never
  looks outside the obvious folder is why cross-cutting questions get half-answered
- which graph relations matter for this question type: `requires`/`regulates` for an impact
  question, `supersedes`/`superseded-by` for a history one, `part-of`/`implements` for a process one
- which node of the tag tree the question's subject sits under. The notes under a node are a search
  axis that cuts across folders, and a node that is too wide names its own narrower children
  (`references/tagging.md`)
- **what a complete answer would need to contain**, listed before anything is retrieved. This list
  is what pass 2 is for

**Pass 1** runs that plan. **Then stop and reason about what came back**, against the list:

- which parts of the question are now covered, and by which note
- which parts have nothing behind them yet
- what the results *revealed* that the plan could not have known: a canonical term the vault uses,
  a note that is clearly the hub, a relation worth following

**Pass 2 searches for the gap only** — the uncovered parts, in the vocabulary pass 1 taught you.
This is where most of the quality comes from, and skipping it is the difference between an answer
about the vault and an answer about the first three notes that matched.

Two passes is the floor, not the ceiling; a third pass is warranted when pass 2 changes the
vocabulary again. Stop when a pass adds no new note.

## 4. Compose by question type

| Type | Structure |
|---|---|
| **Definition** | The term, its expansion, the meaning as the vault states it, an example, the note that defines it |
| **Process** | Ordered steps, one action each, plus a mermaid `flowchart TD` |
| **Comparison** | A table, one row per option, one column per criterion — and a sentence on what actually decides between them |
| **Impact** | What changes, what it changes it for, what stays the same, and the relation the vault records between them |
| **Troubleshooting** | Symptom → cause → what the vault says to do |
| **Inventory** | The list, grouped by where it lives, with a line on each |
| **History** | Dated, in order, with what superseded what |

Supporting knowledge is added **only when the answer needs it to be understood** — a term the
answer leans on, the rule that makes a step mandatory, the note that supersedes the one being
quoted. Each piece is cited like any other claim. Padding an answer with adjacent material the user
did not ask about is the same failure as a summary, in the other direction.

Diagrams follow `references/ingest-sources.md` → Diagrams: only for a process, an exchange between
actors, or a lifecycle, carrying only what the notes stated, and the validator runs on any file
written.

## 5. Verify before delivering

Mechanical, claim by claim, and it happens **before** the answer is shown, not as a disclaimer
after it:

1. **Every claim names the note it came from.** A claim with no note is cut, not softened, not
   hedged into "generally". The one exception is knowledge explicitly labelled as outside the vault,
   which is kept separate from the sourced answer and never mixed into it.
2. **Every citation is to a note actually opened in this run.** Not to a `.rag` passage, not to an
   index line, not to a note the graph merely named.
3. **Each part of the question is covered or declared uncovered.** Walk the section-1 "what would
   satisfy it" list; anything unanswered is stated plainly and logged to `.wiki/wiki_gaps.md`.
4. **Contradictions between notes are reported, not resolved.** Both notes, both claims, what
   differs. Picking the newer one silently is a decision the vault's owner never made.
5. **The assumption ledger is attached**, with any ungrounded entry visible.

A verification pass that finds nothing is normal. A verification pass that was not run is the reason
the answer cannot be trusted, and the reply must not claim it happened.
