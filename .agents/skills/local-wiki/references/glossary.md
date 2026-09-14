# The Business Glossary

<!-- sync: local-wiki-glossary v1 -->

Every index carries a `## Business Glossary` — the vault's own vocabulary, so an agent reading the
index knows what `PIP`, `GEE` or `TaMrA` mean before it reads a single note. Without it, domain
terms in incoming material are unresolvable tokens, their misspellings are invisible, and the same
concept gets filed twice under two spellings.

The glossary is routing infrastructure, like the rest of the index: this skill generates it, owns
it, and repairs it. It is never a note.

## What earns an entry

A **business or domain term**: an acronym, an internal system name, or a domain word that a reader
outside the vault owner's context could not resolve. Admit a term when **any** of these holds:

- The vault defines it somewhere — an expansion, a bolded definition, a "X stands for Y" line
- It appears in **2+ notes**
- A running task hit it as an unknown term in incoming material

**Stoplist — never admitted**, however often they appear. These are universal vocabulary, not this
vault's:

```
API HTTP HTTPS JSON XML YAML SQL URL URI PDF CSV HTML CSS JS TS UI UX CLI IDE OS RAM CPU GPU
CI CD PR MR AI ML LLM RAG SDK NPM GIT SSH TLS SSL DNS IP VM K8S REST CRUD MVC ORM JWT OAuth
TODO FIXME NOTE OK ID UUID ISO UTC AM PM
TBD TBC WIP FAQ AKA ETA NA IMO FYI ASAP
```

**A plural is the same word.** `APIs`, `URLs`, `ID's` are stoplisted exactly as `API`, `URL` and
`ID` are — a list that only matches exactly has a hole in it the width of an `s`, and the terms
that fall through it are the most common tokens in the vault.

A term on the stoplist that the vault *does* define specially (a company's own `CD` meaning
something other than continuous delivery) is admitted — the definition is the evidence.

Also never admitted: a term that appears nowhere in the vault. The glossary describes this vault's
vocabulary, not a domain's.

## Entry grammar

One line per term, so entries stay scannable and appendable. Fixed order: term, aliases, expansion,
one-line meaning, source.

```
- **PIP** (aka PEP) — Product Information Paper. Pre-contractual product summary given to the client before purchase. → `Banking/COBA/pip.md`
- **GEE** — Geeignetheitserklärung. Written statement of why a recommendation suits the client. → `Banking/mifid-wphg.md`
- **TaMrA** — Target Market Assessment. (inferred from usage in 4 notes) → `Banking/mifid-wphg.md`
- **BPKN** — undefined in the vault; appears in `Banking/COBA/avd.md`, `Banking/COBA/filiale.md`.
```

- Terms are sorted alphabetically, case-insensitively.
- The source arrow points at the note that **defines** the term, or where it is most used. One
  target, never a list of five.
- Non-acronym terms are entered the same way, with the expansion field simply absent:
  `- **Themenblock** — Micro-frontend fragment mounted into a host page. → `Dev/frontend/tb.md``

## The three statuses

| Status | Written as | Means |
|---|---|---|
| defined | no marker | A note states the expansion or the meaning. The normal case. |
| inferred | `(inferred from usage in N notes)` | The vault never defines it; the meaning was derived from how the vault uses it. |
| undefined | `undefined in the vault; appears in ...` | Not derivable even from usage. The entry records where it appears. |

**Inferred entries are a to-do list, not a conclusion.** They are marked so the owner can check them
when they have time, and `audit` lists every one of them for exactly that review. Never quietly
promote an inferred entry to defined — only a note that actually states the meaning does that.

**A definition never comes from general knowledge.** If the vault does not say it and its usage does
not imply it, the entry is `undefined`. This is the same rule as "never state what the source
material didn't", applied to vocabulary.

## Aliases and the confidence ladder

The reason the glossary exists: incoming material says `PEP` where the vault says `PIP`. Resolving
that correctly is valuable; resolving it wrongly merges two real concepts and corrupts notes.

**Certain** — merge as an alias, and normalize on write (see below). Requires one of:
- Both forms expand to the same phrase somewhere in the vault
- One note uses both interchangeably for one thing ("the PIP (sometimes written PEP)")
- The user says so

**Likely** — record the alias with a `?` marker, normalize the **incoming material only**, leave
existing notes alone, and flag it in the report. Typical evidence: edit distance 1, same folder,
same surrounding entities, and no competing expansion anywhere.

```
- **PIP** (aka PEP?) — Product Information Paper. ... → `Banking/COBA/pip.md`
```

**Never merge** — the variant has any independent meaning, in this vault or in its domain. Keep two
entries, cross-reference them, and say so in the report.

> Worked counter-example. In a banking vault, `PEP` is a real, different term: **Politically Exposed
> Person**, a KYC/AML concept. Merging it into `PIP` would silently rewrite compliance notes into
> nonsense. Edit distance 1 is **not** evidence — a competing expansion is disqualifying, full stop.

When two entries are genuinely distinct but confusable, say so on both lines:

```
- **PEP** — Politically Exposed Person. KYC screening category. Not to be confused with PIP. → `Banking/kyc.md`
```

## Normalization: changing a term in note text

This is one of the two evidence-backed in-place edits allowed outside a refactor plan — the first
bounded exception to additive-only editing (`SKILL.md` → Constitution). It is narrow on purpose.

**What may happen**: replacing a variant token with its canonical form. Nothing else — no rewording,
no reflowing, no restructuring the sentence around it.

**Only when all of these hold:**

- The alias is at **certain** confidence
- The occurrence is in running prose or a heading — **never** inside a code fence, an inline
  `` `code span` ``, a URL, a file path, a frontmatter value, or a filename
- The note is one the **running task actually opened**. Never a file the task merely saw in a scan.

**Scope**: incoming material always; existing notes only within the set of files this task read. A
**vault-wide sweep is out of scope for this skill** — it changes many files at once and belongs
behind a restructuring approval gate. Report it (`audit` lists variant terms with per-file counts)
and leave it to a `wiki refactor` run. It is never a side effect of filing one note.

**Every occurrence changed is reported**, path and count:

```
Terms normalized (2):
- Banking/COBA/onboarding.md — PEP -> PIP (1 occurrence)
- (incoming material) — PEP -> PIP (3 occurrences)
```

If a normalization would touch more than ~10 occurrences in one existing note, stop: that is not a
typo, it is that note's own vocabulary. Report it as a glossary finding and leave the note alone.

## Where the glossary lives

- **Root `index.md`** — terms used across the vault: any term appearing in 2+ top-level folders,
  plus the terms of every folder the root indexes inline.
- **Per-folder `index.md`** (folders split out past the ~15-file threshold) — that folder's own
  terms, the ones that don't appear elsewhere. Its glossary is additional to the root's, never a
  copy of it.

Budget: **~50 lines per glossary section**. On overflow, folder-local terms move down into the
per-folder indexes and the root keeps terms by breadth of use — most folders first. State the count
that moved in the report. A glossary that would still overflow after that is a signal the stoplist
is being ignored.

Position in the index: after `## Conventions`, before `## Contents`
(`references/index-format.md` → Structure). Vocabulary comes before routing because the routing
lines use the vocabulary.

## Who maintains it

| Mode | Does |
|---|---|
| `indexing` | Builds it from the manifest's `glossary_candidates` plus what it read |
| `refresh` | Carries existing entries forward verbatim; adds terms from `NEW`/`CHANGED` files |
| `update`, `intake` | Adds terms the incoming material introduced; upgrades `inferred`/`undefined` to defined when the new material defines them; normalizes per above |
| `ask` | Expands the question's terms through the glossary; fixes an entry contradicted by a note it read |
| `audit` | Reports inferred entries for review, unresolved variants vault-wide, and terms missing from the glossary |
| `refactor` | Rebuilds it wholesale in phase 9, after the vault-wide normalization sweep in 5b |
| `where` | Reads it. Writes nothing, per its no-write contract. |

A glossary entry contradicted by a note that was just read is repaired on the spot, like any other
index conflict (`references/index-repair.md` → Glossary conflicts).
