# Git safety — don't write against a stale checkout

A vault several people share is a vault where the local copy can be behind, ahead, or diverged from
the remote. Writing into a stale checkout creates a conflict underneath whoever is editing
concurrently, and the person who finds out is the one who tries to merge.

So: **once per session, before the first thing that adds content**, check that the checkout is in
step. Applies to `update` and `intake`, in both `wiki` and the generated local skill.

## When it runs

- **Once per session.** Not per note, not per unit, not per batch item.
- **Before the first add**, not at session start — a session that only answers questions never
  touches git.
- **Never in `where`, `ask`, or `audit`.** They write no content.
- Already run this session → skipped silently.

## The check

```bash
git -C <vault> rev-parse --is-inside-work-tree     # not a repo -> skip everything, no error
git -C <vault> rev-parse --abbrev-ref --symbolic-full-name @{u}   # no upstream -> skip
git -C <vault> fetch
git -C <vault> rev-list --left-right --count HEAD...@{u}
```

The last command prints two numbers: **commits ahead** and **commits behind**.

| Ahead | Behind | State | Do |
|---|---|---|---|
| 0 | 0 | In step | Proceed |
| n | 0 | Ahead — unpushed local work | Proceed. Mention it once; unpushed commits are normal |
| 0 | n | Behind | **Block.** The local copy is missing other people's work |
| n | n | **Diverged** | **Block.** This is the case that produces the merge nobody wants |

`git fetch` is the only git command this skill runs. It changes no working-tree file and no branch —
it updates remote-tracking refs so the comparison is against reality rather than a cached guess.

## What "block" means

**No content is added until the user resolves it.** A hard gate, not a warning that can be waved
past. The material they handed over is not lost — it stays in the conversation, and the write happens
once the checkout is clean.

Say what state it is in, and hand over the commands. **This skill does not run them.** Resolving
divergence rewrites history or produces merge commits, touching real file content — the same class
of action every other destructive operation in this package leaves to the user.

Behind:

```bash
git -C <vault> pull --ff-only
```

Diverged — the choice is theirs, and it matters, so present both:

```bash
# replay your local commits on top of theirs (linear history)
git -C <vault> pull --rebase

# or merge, keeping both histories
git -C <vault> pull --no-rebase
```

Then say: once that succeeds, ask again and the material gets filed.

If they ask for help resolving actual file conflicts, explain the steps and give the commands —
`git status` to see the conflicted files, edit them, `git add`, then `git rebase --continue` or
`git commit`. Never run them.

## What this does not do

- **It does not commit.** Nothing in this skill commits or pushes. Notes are written to the working
  tree, and committing them is the user's call — they may want to review, amend, or batch.
- **It does not check for uncommitted local changes.** Dirty working trees are the normal state of a
  vault someone is actively editing, and blocking on that would make the skill unusable.
- **It does not run on read-only modes.**

## Why this and the contributors heads-up both exist

They catch different windows:

| | Catches | When |
|---|---|---|
| `contributors.py query --path` | Someone edited this note recently, in this clone or a pulled one | Before each write, per file |
| Git safety | The clone as a whole is out of step with the remote | Once per session, before the first write |

The contributors check sees a same-session overlap the git check cannot — a colleague's change that
has been pulled but not noticed. The git check sees the stale clone the contributors log cannot,
because a log that hasn't been pulled yet says nothing. Neither replaces the other.

## Reporting

One line when it matters, nothing when it doesn't:

```
Git: in step with origin/main.
```

```
Git: 3 commits behind origin/main. Nothing was written.
Run: git -C ~/vaults/banking pull --ff-only
Then ask again and I'll file it.
```

A skipped check — not a repo, no upstream — is reported not at all. A vault that isn't version
controlled is a normal vault, not a deficiency.

## Edge cases

- **`git fetch` fails** (offline, no credentials, host down) — say so and **proceed**. An unreachable
  remote is not evidence of divergence, and blocking every write because someone is on a plane makes
  the skill useless. Report that the check couldn't run.
- **Detached HEAD** — no upstream to compare against. Skip, and say so; the user is mid-operation
  and knows it.
- **The vault is a subdirectory of a larger repo** — the check runs on the repo, which is correct:
  divergence is a property of the clone.
- **A submodule** — treat as its own repo. `git -C <vault>` already does.
- **The user says "just write it anyway"** — that is their call on their own repo. Write, and record
  in the report that the check was overridden. Do not silently drop the check on later sessions.
- **`fetch` takes a long time** on a large repo — expected once per session. Don't repeat it.
