# Domain context — engineering

<!-- Shared and committed. Every contributor's agent reads this before it writes anything, and
     before it answers a domain question. Written by whoever maintains this vault, by hand.
     `wiki enhance` never touches it. -->

Standing knowledge and instructions about **this vault's domain as it actually is here** — not the
textbook version. The agent reads this before placing material, shaping a note, or answering a
question, so anything recorded here changes how every future note is handled.

Empty is a valid state. Add to it when you notice the agent getting something wrong that a fact
about your domain would have prevented.

## What belongs here

Context the agent needs **before** it can handle knowledge correctly:

- **Who this vault is for and about** — the organisation, the product, the system. "This vault
  documents Bank X's retail platform" changes what a note about "the customer number" means.
- **Canonical terminology and identifiers** — which term wins when several exist, which identifier
  is authoritative, what an internal acronym expands to. *This is the highest-value thing in the
  file:* it is what stops the same concept being filed twice under two names.
- **Standing domain rules** — constraints that are always true here and would not be guessed.
  "Suitability applies to advisory business only, never execution-only." "We are on Basel III, not
  IV."
- **Authoritative sources** — which system, team or document wins when two notes disagree.
- **Scope boundaries** — what this vault deliberately does not cover, and where that lives instead.
- **Standing instructions for the agent** — how to handle material in this domain. "Always record
  the regulation reference alongside a rule." "Never write a client name into a note."

## What does not belong here

| Not this | It goes in |
|---|---|
| How *you personally* like to work | `.wiki/memory_local.md` — personal, git-ignored |
| A one-off maintenance job for everyone's agent | `remote_instructions.md` in the local skill |
| Where files go, the folder structure | `.wiki/structure-accepted.md` and `index.md` |
| **The vault's actual knowledge** | **A note.** That is what the vault is |

That last row is the one that matters. This file is **context for handling knowledge**, not a place
to store it. If you find yourself writing three paragraphs about how settlement works, that is a
note — write it as one and let the vault do its job. What belongs here is the sentence that would
change where that note goes or what it is called.

## Keep it short enough to be read every time

This file is loaded before **every** write and every domain question, so its length is a tax on
every operation. Aim for **under ~150 lines**.

The test for a line: **would the agent do something different because of it?** If not, it is
description, and description belongs in a note. When it outgrows the budget, the overflow is almost
always real content that should become notes with the index pointing at them.

---

## Organisation and scope

_Not filled in yet. Who is this vault for, what does it cover, what does it deliberately exclude?_

## Canonical terminology

_Not filled in yet. Which term wins, which identifier is authoritative, what the internal acronyms
mean. The glossary in `index.md` records what terms mean; this records which one to **use**._

## Standing domain rules

_Not filled in yet. What is always true here that an outsider would not assume._

## Authoritative sources

_Not filled in yet. Which system, team or document wins when notes disagree._

## Instructions for the agent

_Not filled in yet. How material in this domain should be handled, recorded or phrased._
