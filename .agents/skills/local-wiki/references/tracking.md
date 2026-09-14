# Tracking — who you are, what's verified, what changed

Everything this skill records *about* the vault rather than *in* it: who is working, what has been
verified, who changed what, and what the vault still can't answer.

## Session startup routine

Four checks, once at the start of a session — not once per write.

### Run the gate, do not perform it from memory

```bash
python3 .agents/skills/local-wiki/scripts/startup.py --vault <vault> check
```

**This command is the routine.** It runs all four checks, prints the exact next command for each one
that is incomplete, and **exits 3 while any of them is.** Nothing else in the session starts until it
prints `VERDICT: READY`.

| It printed | Do |
|---|---|
| `VERDICT: READY` | carry on with the mode, quoting the token in the closeout |
| a `->` line | run exactly that command, then run `check` again |
| `startup.py register …` | ask for name and email as described below, then run it |
| `startup.py first-run` | run it. It installs, tests, and stamps the flag only if all of it passed |

**Only `startup.py first-run` may write `first_run: done`.** Setting it by hand, or deciding by eye
that the machine looks set up, is how a session with no retrieval reports a completed gate — the flag
is a claim about this machine, and the tool is the only thing that has checked.

**The four checks below are what the tool enforces**, written out so you can read what a `TODO` line
means and answer the questions the tool cannot ask on its own.

### 1. Is the user registered — and is the record complete?

`.wiki/memory_local.md` must exist and carry **all four** of `username`, `email`, `user_id` and
`first_run`. Checking only for `username` is not enough: a file with a name but no `user_id` passes
that check and then silently breaks attribution forever, because every `contributors.py record` call
needs a `user_id` to pass.

**A partial file is repaired, not ignored:**

| What is missing | Do |
|---|---|
| `user_id`, but `email` is present | `user_id` **is** the email, verbatim. Write it in and carry on — do not ask again |
| `email` (so no `user_id`) | Ask for it, per the rules below. Attribution does not work until it exists |
| `first_run` | Treat as not done, and run check 2 |
| the whole file | Register from scratch, below |

Never leave a field blank and continue as though registration succeeded. Every skipped write to the
contributors log is invisible at the time and unrecoverable afterwards — nobody can reconstruct who
wrote what a month later.

If the file is missing entirely, register them:

- **Name** — ask only if you don't already know it from your own memory or this conversation.
  **Never read the vault's notes to infer it.** A name that appears in a note is an author of that
  note, not necessarily the person sitting here.
- **Email** — ask, and **it is required. Never present it as optional.** It is not a nicety for
  attribution: it *becomes* `user_id`, and `.wiki/contributors.json` is keyed by it. Without it
  nothing can be recorded, the "someone else just edited this" warning cannot work, and "who wrote
  this?" has no answer. Offering it as optional gets it declined and quietly disables all of that.
  If the user refuses, do not fabricate one — a made-up id in a shared committed file is worse than
  none. Say what stops working, leave it unset, skip contributor recording, and ask again next
  session.
- **`user_id`** — the raw email address, **verbatim, no transformation**. Generated the moment
  `email` is first recorded, never regenerated. Unique by construction, since email is.
- **`role`** — set to `contributor` automatically. **Never ask.** A user may later set their own to
  `admin` by editing the file or asking this skill; nothing else grants it.

**Ask like a person, not like a form.** This is the first thing a new contributor ever sees, and
they have no idea what `.wiki/memory_local.md` is — **never name an internal file or path in the
question.** Ask both fields in one short message, say in one clause what they are for, and store
them without narrating where they went.

| Don't | Do |
|---|---|
| "What should I put in `.wiki/memory_local.md`?" | "Before we start — what's your name?" |
| "Email (optional — just so future contributions are attributed)" | "And your email? It's how your notes get attributed, and how I can tell you when someone else has edited the same note." |

On this first registration only, point them at `README.md` and give the current counts:

```
Welcome. This vault is documented in README.md.
Currently: 4 items awaiting validation (.wiki/todos_validations.md), 7 open questions (.wiki/wiki_gaps.md).
```

### 2. Is this the first run on this machine?

Is `first_run` recorded as done in the memory file?

If not — which is exactly what a fresh `git clone` looks like, since the memory file is git-ignored:

```bash
python3 .agents/skills/local-wiki/scripts/startup.py --vault <vault> first-run
```

which does, in order, and stops at the first failure:

1. Installs the RAG dependencies — `python3 .rag/toolkit/rag_toolkit/install.py`.
2. Runs a retrieval test against the vault's index. A venv directory is not evidence; an answer is.
3. Runs `scripts/test_contributors.py` and `scripts/test_graph.py`.
4. Sets `first_run: done` **only if all of the above passed.**

**Do this without asking first.**

**An uninstalled `.rag` is not a broken one.** No `.venv` means the install has never run here, and
that is this check, not the "search tool failed, fall back to grep" edge case. The fallback exists for
a workspace that was installed and has since stopped working; reaching for it before running the
install is how a session skips the gate while believing it handled it.

> **This deliberately overrides `rag`'s Constitution rule 1**, which states: *"Never launch indexing,
> embedding, model downloads, or dependency installs yourself. Print the exact command and stop. Run
> it only if the user explicitly says to run it in this conversation."*
>
> The override is scoped to **this one path**: a first run, on a fresh clone, gated solely by the
> `first_run` flag. The reasoning: a teammate who clones the repo and asks a question should get an
> answer, not a setup checklist — and the flag guarantees it happens exactly once per machine. Every
> other install in this package still follows `rag`'s rule, including `wiki init`, which prints its
> install command and waits.
>
> If the install fails, say so plainly, leave `first_run` unset so it retries next time, and fall
> back to grep. A failed setup must not leave the flag flipped.

### 3. Are there remote instructions to apply?

The admin may have left maintenance entries for every other contributor's agent in this skill's
`remote_instructions.md` — bump a tool, rebuild a cache, adopt a rename. Each is applied **once per
person per clone**, tracked in this file's `## Applied remote instructions` list.

Read both, work out what is pending, and follow `references/remote-instructions.md`: it carries the
classification of what may be applied automatically versus what must be asked about first, and the
rule that an entry can never grant itself permission.

Nothing pending, or no such file → say nothing and move on.

### 4. Is a reorganization overdue?

Read `.wiki/wiki-config.json`. Overdue on **either** signal, whichever comes first:

- `last_reorganized_at` more than `reorg_stale_days` (30) ago, **or**
- any folder holding more than `reorg_folder_notes` (25) `.md` files — computed live from
  `scan_vault.py`'s `folders` map, not from a stored count.

A fast-growing vault gets flagged sooner than a fixed monthly clock would catch it; a quiet vault
isn't pestered just because time passed.

**If overdue AND the current user's `role` is `admin`**, ask whether to run one. A non-admin is never
asked, even when it is overdue — it is still reported by `audit`, which anyone can run.

Accepting runs, in order: `audit` (reports what has grown or is split-worthy), then a
restructuring pass, then a reindex, then `last_reorganized_at` is updated. This skill does not
perform the restructuring itself — that is a `wiki refactor` run, behind its own accept gate. Say so.

Declining leaves the timestamp untouched and **does not ask again this session**. The next session
re-evaluates the same condition.

## The token is the evidence, and the closeout must quote it

Every `check` writes `.wiki/.startup-receipt.json` and prints a token — `2026-08-28-b894af19`. The
closeout's `session startup` line carries that token verbatim:

```
  [x] session startup .......... READY, token 2026-08-28-b894af19
```

A token nobody can produce is a gate nobody ran. `startup.py --vault <v> verify --token <t>` confirms
one, and refuses a token that is invented, stale, or attached to a `BLOCKED` verdict.

**Without a READY token the line is `[ ]`, whatever else the session achieved.** The mark is not a
description of how careful the session felt; it is a claim that four specific things were checked,
and it is checkable.

## The memory file — `.wiki/memory_local.md`

Personal, git-ignored, one copy per user per machine. **Never vault content**, and never derived from
the notes themselves.

```markdown
# Memory — local

username: Khaled
email: absi.box@gmail.com
user_id: absi.box@gmail.com
role: contributor
first_run: done

## Applied remote instructions
- RI-001 — 2026-08-13 — applied

## Preferences
- Prefers short answers; asks for detail when wanted.
- Files meeting notes under `processes/`, not `general/`.
- Wants the note path in the report, always.
```

- **Loaded on every invocation, every mode**, before acting. Not just at creation.
- **Updated continuously and additively.** When you notice how this user searches, adds, or shapes
  notes, record it in the same run — the same way the glossary grows. Never overwrite what is
  already there without cause.
- Markdown, not JSON, because it is expected to grow narrative preference notes rather than fixed
  fields.
- It is in `.gitignore` from the moment it is created. Check that it still is.

## Contributors — who changed what

Every run that changes the vault records it, by calling the tool — never by editing the JSON:

```bash
python3 scripts/contributors.py record \
  --user-id <user_id> --path <file> [--path <file> ...] --type added|edited --vault <vault>
```

Once per run, at the end, with every changed path. Not per file.

**This call is never skipped silently.** Two failure modes, both reported rather than swallowed:

- **No `user_id` to pass** → the memory file is incomplete. Repair it first (check 1 above) and then
  record. Do not shrug and move on: a run that writes to the vault and records nothing looks
  identical to a run that never happened.
- **The tool errors** → say so, with the command, in the report. The user's note is already safely
  written; a broken tool must not cost them the note, but it must not be hidden either.

If a run wrote to the vault and did not record, **the report says so explicitly.**

**Before writing to an existing note**, check whether someone else just touched it:

```bash
python3 scripts/contributors.py query --path <file> --since-hours 24 --vault <vault>
```

Exit 0 means yes — mention it in the report ("bob@example.com edited this 3h ago"). Exit 1 is the
normal case and needs no mention. The window comes from `recent_touch_hours` in the wiki config.

**Never read `.wiki/contributors.json` directly.** It is an append-only log across every contributor
and every change, and it grows without limit. `query` answers a question and returns just that,
which is the only thing making "don't read it" enforceable.

## Provenance on notes

**Every date comes from `date +%F`, never from memory.** A model's idea of today is unreliable and
is routinely a year stale — a real `init` run stamped `2025-08-13` on a day that was `2026-08-13`,
in five files at once. A wrong `created` is a note that sorts wrongly forever; a wrong
`last_changed` makes the recency signals in `audit` and the write heads-up meaningless. Run it once
per session and reuse the value.

Standard markdown frontmatter, on every note this skill creates or edits:

```yaml
---
author: alice@example.com
created: 2026-08-13
last_changed: 2026-08-14
last_changed_by: bob@example.com
---
```

- **On creation**: `author` and `created`.
- **On any later edit**: `last_changed` and `last_changed_by`, every touch — not just the first.
- `author` is never rewritten. The person who started a note keeps that.

## Validation gate

**Every time new content is added, ask whether the user is 100% sure it is correct.** Once per write
in `update`; once per batch in `intake`, not once per unit.

**If they are sure** — write it normally. Nothing else happens.

**If they are not** — two things, together:

1. A checkbox in `.wiki/todos_validations.md`:

   ```
   - [ ] 2026-08-13 — escalation threshold is 15,000 EUR → processes/escalation.md#thresholds
   ```

2. Two blank fields on the note or section itself:

   ```yaml
   validated from:
   validated at:
   ```

**The fields stay blank until someone validates that item.** Never fill them in on your own
initiative — the whole point is that nobody has checked yet.

**Marking something validated is conversational.** "I checked the escalation threshold, it's right"
is enough; there is no command. When it happens, do both halves in the same action:

- fill in `validated from: <their name>` and `validated at: <date>` on the note, and
- tick the corresponding box in `.wiki/todos_validations.md`.

Doing one without the other is how the two drift apart, and `audit` reports that drift as a finding.

## Knowledge gaps — `.wiki/wiki_gaps.md`

When `ask` cannot answer from the vault, the question is logged rather than forgotten:

```
- [ ] 2026-08-13 — what is the escalation threshold for a PIP review? — asked by alice@example.com
```

In `.wiki/`, same checkbox format as `.wiki/todos_validations.md`. This is the vault's backlog of
*what people actually asked and nobody has written down* — distinct from
`.wiki/todos_validations.md`, which is *written but unverified*.

**Check for a duplicate with `grep`, never by reading the file:**

```bash
grep -Fq "escalation threshold" .wiki/wiki_gaps.md && echo "already logged"
```

Both of these are **queues, not ledgers**: they are bounded by their *open* items, and a closed one
does not sit in the live file forever. Once a file passes ~100 lines, `audit` moves ticked and
answered lines older than 90 days into `.wiki/archive/<name>-<year>.md`. A file that only ever grows
becomes a file nobody opens, which defeats the point of writing the backlog down.

## `.input/` — the staging folder

- **Read-only to this skill.** Nothing in it is deleted, moved, renamed, or edited.
- Its contents are git-ignored; the folder itself is tracked via `.gitkeep`.
- **Once a batch is filed, actively ask the user to remove the processed files**, naming them. This
  is the one addition beyond ordinary staging-folder behavior: the content is safely in the vault,
  and leaving it means the next run re-reads material it has already filed. Ask; never delete.

## Where each file lives

| File | Shared? | In `.gitignore`? |
|---|---|---|
| `.wiki/memory_local.md` | Personal | **Yes** |
| `.wiki/manifest.json` | Derived | **Yes** |
| `.wiki/agent-memory/` | Shared | No — committed; the vault learns once for everyone |
| `.wiki/knowledge-profile.md` | Shared | No — committed; this vault's doctrine, never regenerated |
| `remote_instructions.md` (in this skill) | Shared | No — committed, admin-authored |
| `.wiki/graph.sqlite` | Derived | **Yes** |
| `.wiki/domain-context.md` | Shared | No — committed |
| `.wiki/wiki-config.json` | Shared | No — committed |
| `.wiki/contributors.json` | Shared | No — committed |
| `.wiki/structure-accepted.md` | Shared | No — committed |
| `.wiki/conflicts_ignored.md` | Shared | No — committed |
| `.wiki/todos_validations.md` | Shared | No — committed, vault root |
| `.wiki/wiki_gaps.md` | Shared | No — committed, vault root |
| `.input/` contents | Personal | **Yes** (except `.gitkeep`) |
