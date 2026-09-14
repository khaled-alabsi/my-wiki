# Ask mode

<!-- sync: local-wiki-modes v5 -->

Answers a question from this vault's own notes, using the index and the `.rag` workspace to get to
the right files fast.

**Inputs**: the question, the vault root from `vault-profile.md`.
**Outputs**: an answer with file citations. Writes no note content — but repairs index conflicts it
trips over, and logs an unanswerable question to `.wiki/wiki_gaps.md`.

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

2. **Expand the question's terms**, starting with the index's `## Business Glossary`: a question
   about `PEP` searches for `PIP` too. Then expand semantically. A question that is *only* "what
   does X mean" may be answerable from the glossary alone — but say which status the entry carries,
   since an `(inferred)` definition is a guess the vault never confirmed, and cite the note.

3. **Route via the index**: `Place here:` lines to narrow, `covers` lines to pick files, H2
   sub-bullets to jump to sections. Shortlist up to 4.

4. **Search directly too**, and **use the `.rag` index** — ask the user's question as a full
   sentence (`references/rag.md`). Every hit is a pointer to open in step 5, never the answer.

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
   question about a term, and `--path-between <a> <b>` returns the chain when the question is how
   two things relate (`references/graph.md`).

5. **Read the shortlisted notes.** Answer only from what they actually say. Where a note contradicts
   its index line, its sub-bullets, or a glossary entry, fix those now
   (`references/index-repair.md`).

6. **Answer**: direct answer first, then supporting detail, then citations — `path` and the
   `## section`.

7. **Say what's missing**, and log it. If the vault doesn't cover the question, or covers only part
   of it, append the unanswered part to `.wiki/wiki_gaps.md`:

   ```
   - [ ] 2026-08-13 — what is the escalation threshold for a PIP review? — asked by alice@example.com
   ```

   Check first that an equivalent question isn't already logged; if it is, leave it. This is the one
   thing `ask` writes, and it is a backlog entry, not note content.

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
- **Don't pad.** No restating the question, no "based on your notes" preamble.

## Output shape

```
<direct answer, 1-3 sentences>

<supporting detail, only if it adds something>

Sources:
- processes/onboarding.md  ## Compliance checks
- regulatory/kyc.md
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

session startup (READY token) · **search stated** · sources cited · gaps logged (or none) ·
index repairs (or none)

## Edge cases

- **Question needs an answer the notes only imply** — give it, labelled as inferred, and name the
  notes it came from.
- **Answer is spread across many notes** — synthesize it, cite each contributor.
- **The question is really a filing request** ("what do I know about X — also add this") — run
  `update` first, then answer.
- **The answer comes from an unvalidated note** — answer, and say the content is awaiting validation
  with its `.wiki/todos_validations.md` entry. An answer whose source nobody has confirmed should not look
  as solid as one that has been.
- **`.rag` is present but never installed** (no `.venv`) — not this edge case. It is startup check 2,
  and `startup.py first-run` is the fix. Answering from grep instead leaves the gate half-run.
- **`.rag` was installed and is now broken** — `first-run` has already reported it. Fall back to grep
  and never let a search tool's failure block the answer.
