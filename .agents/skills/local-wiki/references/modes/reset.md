# `reset` — take the vault back to a fresh state

Removes note content and rebuilds everything derived from it. This is the one mode that makes the
vault know **less** than it did, so it is never inferred: the user asks for it by name, and it does
not run without a confirmed scope.

`refactor` rearranges knowledge. `reshape` changes what the vault is about. `reset` empties it.

## Scopes

| Scope | Removes | Use when |
|---|---|---|
| `sample` (default) | Notes whose frontmatter carries `status: sample` | Clearing seeded demo or test content off a vault that is about to hold real notes |
| `all` | Every note in the content folders | Starting over, or handing the vault to someone else empty |

The scope is decided by frontmatter, never by folder or filename. A note is sample content because it
says so in its own frontmatter — which is why every seeded note carries `status: sample` and no real
note ever should.

## Constitution

- **Nothing is deleted.** Notes are moved to `.wiki/.trash/<timestamp>/`, keeping their paths. The
  standing rule that a superseded note goes to the trash rather than to `rm` holds here too, and it
  holds most here.
- **Derived state IS deleted**, because it is rebuildable and rebuilding it is the point:
  `.wiki/graph.sqlite`, `.wiki/manifest.json`, `.rag/db/` and `.rag/state/`. Never trash these —
  a half-stale index is worse than no index.
- **Confirm the scope and the count before executing.** Show the user what the dry run listed and
  wait. A reset that surprises someone is not recoverable by them, even though the notes are in the
  trash, because they will not know to look.
- **Never reset because a prompt sounded like starting over.** "This is a mess" is `refactor`.
  "Let's begin again with the payments folder" is `refactor`. Only an explicit reset is a reset.
- **`.wiki/memory_local.md` is not touched by the script.** It is the user's own file. Offer to
  clear it separately when they say nobody has used the vault yet; never assume.
- **The accepted structure survives a reset.** The content folders stay, and so does
  `.wiki/structure-accepted.md`. A reset empties the shelves; it does not tear them out. Changing the
  structure is `reshape`.

## Steps

1. **Resolve the scope.** If the user did not say, ask — `sample` and `all` are not
   interchangeable and the difference is every real note in the vault.
2. **Dry run.** The script reports without `--yes`:

   ```bash
   python3 .agents/skills/local-wiki/scripts/reset_vault.py --vault {{VAULT_PATH}} --scope sample
   ```

3. **Show the count and the folder breakdown**, and wait for the user to confirm.
4. **Execute** with `--yes`.
5. **Rebuild**, in this order — each step depends on the one before:

   ```bash
   python3 .agents/skills/local-wiki/scripts/scan_vault.py --root {{VAULT_PATH}} --out .wiki/manifest.json
   python3 .agents/skills/local-wiki/scripts/graph.py scan --vault {{VAULT_PATH}}
   .rag/bin/rag update --quiet
   ```

6. **Settle the tag tree.** A reset of `all` has already emptied `.wiki/tags.md`: with no notes left
   there are no subjects to list. A reset of `sample` leaves the tree alone, because real notes
   remain and which nodes to let go is a decision:

   ```bash
   python3 .agents/skills/local-wiki/scripts/tags.py --vault <vault> check
   ```

   Every node it fails as `unused` was carried only by the notes that just left. Drop them, leaves
   first, with the `drop` command each line names (`references/tagging.md`).
7. **Rewrite `index.md`'s folder sections** back to `_No notes yet._`, and the Business Glossary back
   to its empty placeholder. The index is note content's map; leaving entries for notes that are now
   in the trash is the drift this skill exists to prevent.
8. **Report**, then the closeout checklist.

## Mandatory closeout lines for this mode

```
  [x] scope confirmed ........... sample, n notes, you confirmed
  [x] notes trashed ............. .wiki/.trash/<timestamp>/
  [x] derived state cleared ..... graph, manifest, .rag db + state
  [x] tracking reset ............ contributors, todos, gaps, observations, proposals
  [x] manifest rebuilt .......... n files
  [x] graph rescanned ........... n edges
  [x] tag tree settled .......... emptied (all) | n unused nodes dropped — tags check OK: ...
  [x] search ................... n/a for the reset itself; index rebuilt below
  [x] search index rebuilt ...... n files embedded
  [x] index.md emptied .......... 9 folder sections, glossary
  [-] memory_local.md ........... left alone, it is yours
```

## Edge cases

- **`--scope sample` finds nothing** — say so and stop. It means no note is marked as sample, which
  usually means the user meant `all` and should be asked rather than assumed.
- **The trash already holds an earlier reset** — each run writes its own timestamped folder, so they
  never collide. Do not clean the older ones; that is the user's call.
- **`.rag` rebuild fails** — the reset itself still succeeded. Report the failure, point at
  `bash .rag/bootstrap.sh`, and do not roll anything back.
