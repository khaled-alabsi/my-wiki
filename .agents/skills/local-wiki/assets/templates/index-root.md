<!-- Authoring note, not output. This is the shape of a root index.md.
     Replace every ALL-CAPS placeholder. Delete sections marked optional when they don't apply.
     Nested bullet lists only - no markdown tables. -->

# VAULT NAME - Index

> Navigation map for agents: match what you are looking for, or what you want to add, against the
> one-line descriptions below, then open that folder or file.
> Keep this current: run the `wiki` skill in `refresh` mode after adding, moving, or removing notes.
> A refresh only re-describes what changed.

## How to use this index

- **Looking for something**: scan the descriptions for the closest topic match, then open that file.
  A file with sub-bullets lists its own sections — go straight to the right one.
- **Adding something new**: find the folder whose `Place here:` line fits the new content's topic,
  then check that folder's files for one that already covers it. Merge into an existing note before
  creating a new one. If no folder fits at all, that means a new folder is needed — not that the
  closest one should be forced.

## Conventions

<!-- Detected once from the vault itself, so later runs write notes that match what is already here. -->

- Links: LINK STYLE (for example `[[wikilinks]]`, or relative markdown links)
- Frontmatter: FIELDS PRESENT, or `none`
- File naming: NAMING STYLE (for example `kebab-case.md`, or `Title Case.md`)
- Dates: DATE FORMAT (for example `2026-08-01`)
- Attachments: WHERE IMAGES AND BINARIES LIVE, or `none`

## Business Glossary

<!-- This vault's own vocabulary: terms an outsider could not resolve. One line per term,
     alphabetical, ~50 lines max. Rules in references/glossary.md. -->

- **TERM** (aka ALIAS) — EXPANSION. ONE-LINE MEANING. → `path/to/defining-note.md`
- **TERM** — EXPANSION. ONE-LINE MEANING. (inferred from usage in N notes) → `path/to/note.md`
- **TERM** — undefined in the vault; appears in `path/a.md`, `path/b.md`.

<!-- A FOLDER WITH NO NOTES YET looks exactly like this - normal for a freshly created vault.
     The Place here: line, then `_No notes yet._`. Never an empty table, never a placeholder row.

     ## folder-name/

     Place here: what belongs in this folder.

     _No notes yet._
-->

## Contents

- `folder-a/` - one-line topic description - see "## folder-a/" below
- `folder-b/` - one-line topic description - see "## folder-b/" below
- `top-level-note.md` - what this note covers

## Recently changed

<!-- Optional: only on a refresh run. Delete this whole section on a fresh build. -->

- `folder-a/new-note.md` - NEW - what it covers
- `folder-b/edited-note.md` - CHANGED - what changed about its coverage
- `folder-c/gone.md` - REMOVED - no longer present, dropped from this index

## folder-a/

- Place here: WHAT KIND OF NEW CONTENT BELONGS IN THIS FOLDER.
- `folder-a/sub-folder/` - one-line topic description
  - `folder-a/sub-folder/note-1.md` - what this note covers
- `folder-a/big-note.md` - what this note covers
  - `## Section One` - what this section covers
  - `## Section Two` - what this section covers
- `folder-a/note-2.md` - what this note covers
- `folder-a/see-also.md` - cross-references to notes that live elsewhere but are relevant here
  <!-- Optional: only present once this folder has received a cross-reference. -->

## folder-b/

<!-- A folder that was split out because it exceeded the ~15 file threshold. -->

- Place here: WHAT KIND OF NEW CONTENT BELONGS IN THIS FOLDER.
- 34 notes. See `folder-b/index.md` for the full list.
