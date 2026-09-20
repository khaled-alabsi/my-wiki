# Ask mode

<!-- sync: local-wiki-modes v5 -->

Answers a question from this vault's own notes: understand the question, plan the search, search
twice, verify every claim, then deliver — in the reply, and in a file when the answer is big enough
to be worth keeping.

**Inputs**: the question, the vault root from `vault-profile.md`.
**Outputs**: an answer with file citations and an assumption ledger, plus — past the write gate in
step 10 — a file in `.wiki/answers/`. Writes no note content, but repairs index conflicts it trips
over, and logs an unanswerable question to `.wiki/wiki_gaps.md`.
**Reads**: `references/answering.md` for steps 2, 4, 5, 7, 8 and 9 — the reasoning inside them lives
there; this file is the order they run in.

## Workflow

1. **Session startup** — run `startup.py --vault <vault> check` and clear every `->` line until it
   prints `VERDICT: READY`, per `references/tracking.md`. Carry the token into the closeout. No git check — `ask` adds nothing. **Every other
   check still runs, before any search or note is read.** Only the git check is waived; `ask` is not
   exempt from registration, first-run setup, remote instructions or the reorg check, and an easy
   question is not a reason to answer first and run them never.

   **Load `.wiki/domain-context.md` first.** It carries the vault owner's standing knowledge about
   this domain — canonical terminology, which identifier is authoritative, rules that are always true
   here, how material in this domain should be handled. It is short by design and read in full.
   
   It changes decisions this step is about to make: which term the note is written in, whether two
   things are the same concept, which source wins when notes disagree. Reading it after placing the
   material is too late.
   
   Empty or absent → carry on, that is the normal state of a young vault.


<!-- profile-hook: ask-routing -->

2. **Classify the question** (`references/answering.md` → 1): its type (definition, process,
   comparison, impact, troubleshooting, inventory, history), its scope, and what would satisfy it.
   Write the "what would satisfy it" list down — step 9 walks it. Two questions in one are split
   here.

3. **Orienting search — cheap, to learn the vocabulary.** Expand the question's terms against the
   index's `## Business Glossary`: a question about `PEP` searches for `PIP` too. One `.rag` query
   with the question as a full sentence. The point is not the answer; it is finding out what this
   vault calls the thing. Resolve the question's subjects against the tag tree as well
   (`grep -iF "<word>" .wiki/tags.md`): a node that matches names a whole subject's notes.

   A question that is *only* "what does X mean" may be answerable from the glossary alone — say
   which status the entry carries, since an `(inferred)` definition is a guess the vault never
   confirmed, and cite the note. That question skips to step 10.

4. **Restate the question and log the assumptions** (`references/answering.md` → 2). The restated
   question in the vault's vocabulary, and every assumption with its ground named — a note, a
   glossary entry or a graph edge, never "it is obvious". An ungrounded assumption is dropped or
   asked about, and asked only when the two readings give materially different answers. The ledger
   goes in the answer; it is never kept in your head.

5. **Plan the extended search** (`references/answering.md` → 3): which terms, which folders the
   index routes to **and which it doesn't**, which graph relations this question type calls for,
   and what a complete answer would have to contain.

6. **Search — pass 1.** Route via the index (`Place here:` lines to narrow, `covers` lines to pick
   files, H2 sub-bullets to jump to sections), search directly for the expanded terms, and run the
   `.rag` query (`references/rag.md`). Every hit is a pointer to open, never the answer.

   **Then expand the shortlist one hop through the graph** — the step that answers what retrieval
   cannot. What mandates a thing, what replaced it, what it is part of are all one relation away,
   and no amount of semantic similarity reaches them:

   ```bash
   python3 .agents/skills/local-wiki/scripts/graph.py --vault <vault> query \
       --neighbors <hit> --depth 2 --json --limit 10 \
       --types requires,regulates,supersedes,superseded-by,part-of,implements
   ```

   Run it on the two or three strongest hits, not on everything; cap the shortlist at 6 notes.
   `--backlinks` finds notes that reference a topic without naming it, `--concept <TERM>` answers a
   question about a term, `--tag <node>` lists every note under a node of the tag tree (and
   `--tag-tree <node>` what it branches into when it is too wide; a shared tag is a pointer to
   open, never an answer, `references/tagging.md`), and `--path-between <a> <b>` returns the chain when the question is how
   two things relate (`references/graph.md`).

7. **Reason about the gap, then search again.** Against step 5's list: what is covered and by which
   note, what has nothing behind it, and what the results revealed that the plan could not have
   known — the vault's own term for the thing, the note that is clearly the hub. **Pass 2 searches
   for the uncovered parts only**, in the vocabulary pass 1 taught you. Stop when a pass adds no new
   note. This is where most of the quality comes from.

8. **Read the shortlisted notes and compose** (`references/answering.md` → 4), structured by the
   question's type, with supporting knowledge only where the answer needs it to be understood. A
   diagram only for a process, an exchange or a lifecycle. Where a note contradicts its index line,
   its sub-bullets, or a glossary entry, fix those now (`references/index-repair.md`).

9. **Verify** (`references/answering.md` → 5), before anything is shown: every claim traced to a
   note opened in this run, every part of step 2's list covered or declared uncovered,
   contradictions between notes reported rather than resolved, the ledger attached. A claim that
   fails is cut, not hedged.

10. **Answer, and log what's missing.** Direct answer first, then supporting detail, then citations
    — `path` and the `## section`. A file only past the write gate below. If the vault doesn't cover
    the question, or covers only part of it, append the unanswered part to `.wiki/wiki_gaps.md`:

    ```
    - [ ] 2026-08-13 — what is the escalation threshold for a PIP review? — asked by alice@example.com
    ```

    Check first that an equivalent question isn't already logged; if it is, leave it. This is a
    backlog entry, not note content.

## The write gate — when an answer becomes a file

**A file is written only when at least one is true:** the answer opened **3 or more notes**, it
draws on **2 or more folders**, it carries a **diagram**, or you were asked for one. Everything else
stays in the reply — a one-line lookup that creates a file is how a vault fills with restatements of
itself.

**Where**: `.wiki/answers/YYYY-MM-DD-<slug>.md`, with frontmatter carrying `question`, `asked_at`,
`sources`, `assumptions_ungrounded` and `gaps`.

**An answer file is not a note.** It lives in `.wiki/`, never in the notes tree; it is never
indexed, never linked from a note, and **never cited as a source by a later run** — it is derived
from notes that may since have changed. Content that deserves to be knowledge gets there through an
`update` run against the real notes, deliberately.

**Bounded at the moment of writing**: count the files in `.wiki/answers/`; past 50, move the oldest
into `.wiki/answers/archive/` until 50 remain. The archive is written and never read. No
`.wiki/answers/` folder yet (a vault set up before this existed) → create it on first use.

## Questions about the vault itself

`ask` also answers questions about the tracking data — "what's unvalidated?", "who last touched
this?", "what links here?", "what's not written down yet?" — by **querying the tools**, never by
reading their raw files:

| Question | How |
|---|---|
| Who changed this note, and when | `contributors.py query --path <p> --since-hours <n>` |
| What has this person contributed | `contributors.py query --user-id <email> --limit 20` |
| How active is this vault | `contributors.py query --stats` |
| What links to this note | `graph.py query --backlinks <p>` |
| What's related to this note | `graph.py query --neighbors <p> --depth 2` |
| What's disconnected | `graph.py query --orphans` |
| What links are broken | `graph.py query --broken` |
| What's unvalidated | Read `.wiki/todos_validations.md` — it is a human-facing checklist, small by design |
| What's missing | Read `.wiki/wiki_gaps.md`, same reason |

**Never read `contributors.json` or `graph.sqlite` directly.** Both grow without limit; the tools
answer a question and return just that. This is not a style preference — it is the only thing
keeping a multi-year change log out of the context window.

## Rules

- **The vault is the only source.** Never answer from general knowledge. If general knowledge would
  fill the gap, offer it explicitly labelled as outside the vault, after the sourced answer — never
  blended into it.
- **Don't quote the index as evidence.** It routes; cite the note it pointed to. Same for a `.rag`
  passage and a `graph.py` edge: both are pointers, and the citation is the note you opened.
- **`ask` writes no note content** — not even the two in-place edits `update` may make. Questions
  answered here are not written into notes. Index, glossary and `.wiki/wiki_gaps.md` are the exceptions,
  and they are infrastructure, not content.
- **Surface conflicts.** Two notes disagreeing is a finding worth reporting, not something to
  quietly resolve by picking the newer one. If one is unvalidated (`validated from:` blank), say so
  — that is usually the answer to which one to trust.
- **Don't pad.** No restating the question, no "based on your notes" preamble. The assumption
  ledger is not padding — it is the record of how the question was read — but it is short.
- **The pipeline scales to the question.** A definition answerable from the glossary runs steps 1–3
  and 10. Steps 4–9 are for questions that need them; running the full pipeline on "what does GEE
  mean" is its own kind of failure.

## Output shape

```
<direct answer, 1-3 sentences>

<supporting detail, only if it adds something>

Read as: <the restated question>            (omitted when the restatement changed nothing)
Assumptions: <one line each, ground named; UNGROUNDED ones first>

Sources:
- processes/onboarding.md  ## Compliance checks
- regulatory/kyc.md

Written to: .wiki/answers/2026-09-18-failed-appropriateness-check.md   (only past the gate)
```

If a gap was found: `Not in the vault: <what>.` plus one line saying it was logged to
`.wiki/wiki_gaps.md`. If index entries were repaired, that block goes last.

## Say how the answer was found

**Every answer ends with one `search` line**, before the closeout — what the semantic index was
asked and what came back, or, when it was not used, which exemption applied and why
(`references/rag.md` → Every answer says whether the index was used).

```
search ...... .rag, 2 queries ("how is a payment authorised", "cut-off"), 7 hits across 4 notes
```

This is the mode the rule exists for: an answer assembled from grep hits looks identical to one
assembled from retrieval, and only this line tells the difference. An `ask` run that reached for
grep because the index was dead, and did not say so, is the exact failure being prevented — the
user believes their vault answered them when it only answered from the words they happened to type.

## Closeout

End with the checklist (`SKILL.md` → Closeout checklist). `ask` writes no note content, so it is
short:

session startup (READY token) · **search stated (both passes)** · assumptions logged · verification
run · sources cited · gaps logged (or none) · answer file written (or below the gate) ·
index repairs (or none)

## Edge cases

- **Question needs an answer the notes only imply** — give it, labelled as inferred, and name the
  notes it came from.
- **Answer is spread across many notes** — synthesize it, cite each contributor. This is the case
  the write gate exists for.
- **Pass 2 finds nothing new** — normal, and worth one word in the report. It means pass 1's
  vocabulary was right, not that the step was skippable.
- **The question is really a filing request** ("what do I know about X — also add this") — run
  `update` first, then answer.
- **The answer comes from an unvalidated note** — answer, and say the content is awaiting validation
  with its `.wiki/todos_validations.md` entry. An answer whose source nobody has confirmed should not look
  as solid as one that has been.
- **`.rag` is present but never installed** (no `.venv`) — not this edge case. It is startup check 2,
  and `startup.py first-run` is the fix. Answering from grep instead leaves the gate half-run.
- **`.rag` was installed and is now broken** — `first-run` has already reported it. Fall back to grep
  and never let a search tool's failure block the answer.
