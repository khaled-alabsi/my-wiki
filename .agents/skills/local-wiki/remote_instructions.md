# Remote instructions

<!-- NOT generated. `wiki enhance` never rewrites this file — it is the admin's, like a changelog. -->

Maintenance instructions from this vault's admin to **every other contributor's agent**. Committed
and shared: the admin adds an entry here, everyone else's local skill picks it up on its next
session and applies it once.

This exists because the admin can change the vault or the skill — bump a tool, rename a folder,
retire a convention — and every other clone needs the same change applied locally. Without it, each
contributor has to be told by hand, and the ones who miss it drift.

## How to write one (admins)

One `##` block per instruction. The **id is mandatory and permanent** — it is what every contributor's
memory file records as "done", so reusing or renumbering an id makes agents re-run work or skip it.

```markdown
## RI-003 — regenerate the graph cache

**Added:** 2026-08-13 by admin@example.com
**Do:** run `python3 .agents/skills/local-wiki/scripts/graph.py scan --full --vault .`
**Why:** link extraction changed; caches built before today miss `## Related` edges.
```

- **`## RI-<n>`** — sequential, never reused, never renumbered.
- **`Added:`** — date and who, so a contributor can ask the right person.
- **`Do:`** — the instruction. One action. Be specific: name the command or the exact change.
- **`Why:`** — why it is needed. An agent that has to ask the user for approval will show this, and
  a reason nobody can evaluate gets declined.
- Optional **`Applies to:`** — a condition, e.g. "only clones created before 2026-08-01". Omit it
  and the instruction applies to everyone.

**Never delete an entry.** A contributor who has not run it yet still needs it, and a deleted id
looks like an id that was never issued. Superseded entries get a new entry that says so.

## What contributors' agents do with it

Checked at the start of every session, before normal work. Each entry is applied **once per
person per clone**, tracked in that user's own `.wiki/memory_local.md` — so a fresh clone by the
same person applies them again, which is correct: the change is local.

Anything that reads as destructive, or that reaches outside this vault, is **never applied
automatically** — the agent shows the entry and asks. Full rules in
`references/remote-instructions.md`.

---

<!-- Admins: add entries below. Newest last. -->

_No instructions yet._
