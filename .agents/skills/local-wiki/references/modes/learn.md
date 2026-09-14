# Learn mode — turn a pile of episodes into a few rules

<!-- sync: local-wiki-modes v5 -->

Periodic consolidation. Reads what the agent decided and how those decisions turned out, finds the
repeated shape, and writes it down as a candidate rule.

**Inputs**: nothing. Optionally `scope=<name>` to consolidate one area.
**Outputs**: a reflection file, zero or more new candidate rules, and a report. Writes no note
content — `learn` never touches the vault's own notes.

Approval is **not** this mode's job. Promotion happens automatically at a threshold
(`references/agent-memory.md` → The gate) and is announced by whichever run triggers it. What `learn`
does is *create the candidates* — without it, nothing ever reaches a threshold, because a rule has
to exist before episodes can support it.

Never inferred from a prompt shape. The user asks for it by name.

**Session startup first** (`references/tracking.md`) — no git check, `learn` writes no note content.

## When it is worth running

- After a batch of corrections — several notes moved, a placement argued about.
- Monthly, on an active vault.
- When `audit` reports a rising correction rate.

On a vault with fewer than ~10 closed episodes there is nothing to consolidate. Say so and stop;
inventing a rule from two data points is exactly the memory pollution the gate exists to prevent.

## Workflow

1. **Counters first.**

   ```bash
   python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> stats --json
   ```

   This reads the rollup, never the log. It tells you how much there is and where it is concentrated
   — which scope to look at, and whether it is worth looking at all.

2. **Read the corrections, bounded.**

   ```bash
   python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> query --outcome corrected --since 90d --limit 30 --json
   python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> query --outcome confirmed --since 90d --limit 30 --json
   ```

   **Corrections first, and they carry more weight.** One correction says more than ten silent
   successes: the successes may have been luck, the correction is a fact about what the owner wanted.

   Never widen this to the whole log. If 30 recent corrections do not show a pattern, the pattern is
   not there yet.

3. **Find the repeated shape.** A rule is worth writing when several corrections share a *reason*,
   not merely a folder. Three notes moved out of `general/` is a coincidence; three notes moved out
   of `general/` **because they described mechanisms rather than instances** is a rule.

   The test: could you state the condition without naming a specific note? If not, it is an
   observation — append it to `observations.md` and stop there.

4. **Check it against what is already known.**
   - Does an existing rule already say this? Add the evidence to that rule instead of writing a
     second one. Two rules saying the same thing split their evidence and neither reaches threshold.
   - Does it contradict `.wiki/domain-context.md`? The domain context wins — it is what the owner
     stated. Do not write the rule; report the conflict.
   - Does it contradict a `deprecated` rule? Then it is the corrected form of that rule: write it
     narrower, and set `superseded_by` on the old one.

5. **Write the candidate**, one file per rule, at `status: candidate`:

   ```markdown
   ---
   id: RULE-017
   scope: placement
   status: candidate
   confidence: 0.0
   evidence: [EP-238, EP-251, EP-266]
   negative_examples: []
   created_at: 2026-08-15
   last_validated: 2026-08-15
   superseded_by: null
   ---
   When a note describes a reusable mechanism rather than one project's implementation,
   prefer the conceptual domain folder over the project folder.
   ```

   - **The body is one imperative sentence**, plus at most a line on when it does not apply. Twenty
     lines is a design document, and the agent has to read this before every placement.
   - `evidence` lists the episode ids the pattern came from. That list *is* the support count until
     the rule starts firing on its own.
   - `id` is the next free `RULE-NNN`.

6. **Write the reflection** — `reflections/<YYYY-MM>.md`, appended:

   ```markdown
   ## 2026-08-15
   30 corrections in 90 days, 18 of them in `placement`.
   Pattern: mechanism-vs-instance confusion, 6 episodes → RULE-017 (candidate).
   Pattern: meeting notes filed by date rather than by process — 2 episodes, not enough. Observed.
   No pattern found in `linking` corrections; they look like one-offs.
   ```

   This is the ACE point: accumulate structured insight incrementally, never rewrite the whole
   thing. Repeated summarising loses the detail that made an insight useful.

7. **Run the gate and report.**

   ```bash
   python3 .agents/skills/local-wiki/scripts/memory.py --vault <vault> promote --json
   ```

## Report

```
Learn — 90 days, 47 episodes (30 corrected, 17 confirmed)

Candidates created
  RULE-017  placement  — mechanism notes belong in the domain folder, not the project folder
                         evidence: EP-238, EP-251, EP-266, EP-271, EP-280, EP-288

Promoted
  RULE-009  supported → validated  (5 supporting episodes, no contradiction in 30 days)
            a note answering "how do I" belongs beside the process it describes

Demoted
  RULE-004  validated → supported  (contradicted 2 days ago by EP-291)

Observed, not enough evidence
  meeting notes filed by date rather than by process — 2 episodes

Loaded after this run: 6 rules across 3 scopes (placement 4, linking 1, glossary 1)
```

Then the closeout checklist (`SKILL.md` → Closeout checklist). For `learn`:

```
Closeout
  [x] session startup .......... READY, token 2026-08-28-b894af19
  [x] counters read ............ 47 episodes, rollup only
  [x] corrections reviewed ..... 30, bounded query
  [x] candidates written ....... RULE-017
  [x] reflection written ....... reflections/2026-08.md
  [x] gate run ................. 1 promoted, 1 demoted — announced above
  [-] search ................... n/a, learn reads agent memory, never the notes
  [-] note content ............. n/a, learn never writes notes
```

## Edge cases

- **Every correction is a one-off** — the honest outcome, and worth saying. Report "no pattern
  found" rather than manufacturing a rule to have something to show.
- **A pattern spans two scopes** — write two narrow rules, not one broad one. A rule loaded for
  `placement` should not carry advice about linking that never applies there.
- **The same rule keeps being demoted** — it is wrong in a way nobody has named yet. Deprecate it,
  record what the corrections actually had in common, and leave it deprecated until that is clear.
- **A candidate is obviously right and the user says so** — it still needs its episodes. The gate is
  the protection against one convincing case becoming doctrine, and skipping it for a rule that
  feels obvious is exactly when it matters.
- **A rule turns out to be generic**, true of any vault rather than this one — that is a `canonical`
  candidate: it belongs in this skill's own reference files, via `enhance`, not only in one vault's
  memory.
