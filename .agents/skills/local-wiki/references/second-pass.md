# The second pass — proving one source file actually landed

<!-- sync: local-wiki-second-pass v1 -->

**Read this when:** a source file's units have been written into the vault and the file is about to
be marked filed in `intake`. It is the gate on that mark — step 8 of `references/modes/intake.md`.

A first pass is where detail dies. It reads a source, decides what the material is *about*, writes
notes shaped by that decision, and reports itself finished — and the report is built from the same
thinned summary that dropped the detail, so nothing in it can show the loss. The second pass exists
because **a model cannot find what it never wrote down by re-reading what it wrote.** It re-reads
the source.

## The unit of work is one source file, start to finish

Extract it, file its units, prove it landed, mark it. Then the next file. Never extract five files
and verify at the end: by then the source that was thinnest is the one furthest out of context, and
the verification degrades into agreeing with the notes.

**A source file is not marked filed until its second pass closes** — the `[x]` in
`.wiki/intake-log.md`. A file whose second pass found gaps keeps its `[ ]` until they are written,
or explicitly declined with one of the four allowed reasons.

## Pass 1 — extract, then file

Per `references/ingest-sources.md`. Two things about it exist only to make pass 2 possible:

**Extract before you decide the structure.** Every meaningful unit gets written down first —
headings are containers, not content, and a structure decided early becomes the sieve that drops
everything not shaped like it.

```bash
python3 scripts/extract_units.py extract <source> --out .wiki/.second-pass/<source>.units.txt
```

It prints the unit count. **That count is the baseline**, and it is the only number in this flow
that is not the agent's own opinion of its work. The units file is written to disk and never read
whole by the agent — `cover` reads it.

Images, PDFs and anything else with no extractable text have no baseline; their second pass is the
re-read in pass 2b and the critique in 2c, and the report says the count was unavailable.

## Pass 2 — the four checks, in order, on that one file

### 2a. Gap analysis — what of the source has no home

```bash
python3 scripts/extract_units.py cover \
  --units .wiki/.second-pass/<source>.units.txt \
  --notes <every note this file wrote or edited> --limit 40
```

Each unit comes back `COVERED`, `WEAK` or `UNCOVERED`. Exit 1 means at least one unit is uncovered.

**It is a detector, not proof.** It matches numbers, acronyms, names and content words — so it
finds the losses that have a token to lose, and it cannot see a unit whose words are all present in
a note that says something else. Open every flagged unit and decide:

| Verdict | What it means | What you do |
|---|---|---|
| `UNCOVERED` | No note carries this unit's numbers, names or wording | Write it into the right note now, or record which of the four allowed drops applies (`references/ingest-sources.md` → Lose nothing) |
| `WEAK` | Some of its distinctive tokens are missing | Open the note and the unit side by side. A partially carried claim is the most common real loss: the sentence is there and the exception, the threshold or the qualifier is not |
| `COVERED` | Its tokens are all present somewhere in the notes | Not verified. 2b samples these |

**Never close a gap by editing the unit list.** The baseline is the source's, not yours.

### 2b. Double check — is the covered material actually carried, and is anything invented

Two directions, and the second one is the one that gets skipped:

**Source → notes.** Take every `WEAK` unit and a sample of `COVERED` ones — at least ten, or all of
them under ten — and read each against the note text it matched. A keyword hit is not
representation: "above a threshold" matches a unit about 15,000 EUR on every word but the number.

**Notes → source.** Read the notes this file produced and, for every claim in them, find the unit
it came from. A claim with no unit behind it was invented — by inference, by general knowledge, or
by tidying a hedge into a fact — and it is deleted or marked uncertain, per
`references/ingest-sources.md` → Transcribe, don't author. This direction has no script and finds
the errors that are worst to leave: a wrong fact reads exactly like a right one.

### 2c. Self-critique — read the notes as the reader who wasn't in the room

The five ways a first pass fails, each phrased as the question that catches it. Answer them about
the notes in front of you, in writing, before the file is marked:

1. **Did I write the structure and call it the content?** For each heading, is the substance under
   it, or only the heading's promise? "Six dimensions of X" with six one-line labels and no detail
   is a table of contents, not a note.
2. **Where are the numbers, dates, names, tools and identifiers?** List them from the source and
   find each one in a note. These are the first things a summarising pass drops and the first
   things a reader comes back for.
3. **Did the discussion get the same rigour as the presentation?** Questions and answers, side
   arguments, interruptions and corrections are where the exceptions and the real thresholds live.
   A file whose Q&A produced no notes had its most specific material dropped.
4. **What did the source qualify that my note states flatly?** "Not necessarily higher penalties,
   but stricter enforcement" is two claims and a contrast; "penalties increased" is neither.
5. **Would a reader finish this note and ask "but what about…?"** Write down each such question. If
   the source answers it, the answer is missing from the note — go and add it.

An examples-and-illustrations check belongs to (1): a source's own example is content, and it is
dropped by exactly the reasoning that keeps only the general rule.

### 2d. Open questions — what stays open, and what this pass opened

Run `references/open-questions.md` over the file again, now with the notes written. Three sources
of questions, all of which land in the same place:

- what the **source** left open — its `?`s, its `TBD`s, a question nobody answered
- what **transcription** could not resolve — a cut-off screenshot, a garbled number, a slide the
  speaker pointed at that you do not have
- what **this pass** could not settle — a `WEAK` unit whose note you could not reconcile, a claim
  whose source unit you could not find

Each is answered from the vault where the vault answers it, and otherwise stays open, verbatim.
Never invent the answer, and never close a question because the second pass is nearly over.

## Closing the file

Print this per source file, before marking it:

```
Second pass — eu-aml-recording.vtt
  baseline ................... 306 units
  cover ...................... 271 covered, 24 weak, 11 uncovered
  written this pass .......... 9 units added to 3 notes
  declined ................... 2 (chrome), 0 other
  double check ............... 24 weak + 12 sampled read against the notes; 1 invented claim removed
  critique ................... structure/substance ok; Q&A had no note, 4 added; 2 flattened qualifiers restored
  open questions ............. 3 open (2 from source, 1 from this pass), 1 answered from the vault
  verdict .................... closed
```

`verdict` is `closed` only when every uncovered unit is written or declined with one of the four
allowed reasons. Otherwise it is `open`, the intake log line stays `[ ]`, and the report says which
units are outstanding. **A file reported as filed with units outstanding is a failed filing**,
whatever else the run did well.

Then delete that file's units file: `rm .wiki/.second-pass/<source>.units.txt`. It is derived and
rebuildable from the source in one command; keeping it turns a working file into a second vault.

## What this costs, and where it is spent

A second pass is roughly the cost of the first one, and it is the cheapest verification available —
the alternative is a vault whose gaps are found by someone trusting it. Two rules keep it bounded:

- **It never re-reads the source more than once.** One sequential re-read in 2b, working from the
  units file and the notes for everything else.
- **Its outputs are bounded.** `cover` prints at most `--limit` flagged units; the critique is five
  answers, not an essay; the block above is the whole report.

## Constitution

- **The baseline comes from the source, mechanically.** An agent's own count of what it extracted
  is the same opinion that produced the notes.
- **The second pass runs on every source file**, not only on the ones that look complex. Depth
  scales with the file; the gate does not.
- **The pass that writes and the pass that verifies are separated by the source, not by time.**
  Verification means re-reading the material, never re-reading the notes.
- **`cover` failing is a finding, not an error.** Exit 1 is the normal state mid-pass.
- **Nothing here may edit, move or delete anything in the staging folder.** The source is read-only
  in every pass (`references/modes/intake.md` → The source folder is read-only).
- **A gap found is written in the same run, not queued.** A list of things the vault is missing,
  filed in the vault, is a knowledge base documenting its own incompleteness instead of fixing it.

## Edge cases

- **A source with no extractable text** (image, scan, binary) — no baseline. Run 2b as a re-read of
  the image against the note, plus 2c and 2d. Say in the report that the count was unavailable.
- **A source that legitimately yields few units** — a one-line scrap, a link. The pass is three
  questions and thirty seconds; it is not skipped, because "obviously complete" is the judgement
  that was wrong the last time.
- **`cover` flags a unit the vault already stated before this run** — that is Rule 0's `present`
  verdict, not a gap (`references/placement-rules.md` → Rule 0). Record it as declined under reason
  4, having opened the note and read the line.
- **The uncovered list is enormous** (a third or more of the baseline) — the first pass summarised
  rather than extracted. Do not patch it unit by unit: re-do the extraction and the placement for
  that file, then run the second pass again.
- **A unit belongs in a note another source owns** — write it there; the second pass is not limited
  to the notes this file happened to create.
- **The run is interrupted mid-second-pass** — the units file is still on disk and the intake log
  line is still `[ ]`. Resuming re-runs `cover`, which is idempotent.
