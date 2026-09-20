#!/usr/bin/env python3
"""Count what a source file actually says, and check the notes carry it.

Two subcommands, both deterministic and stdlib-only:
  extract   split one source file into numbered meaningful units
  cover     check each unit against the notes written from it
`cover` is a DETECTOR, not proof. A unit it calls UNCOVERED is a candidate the agent opens and
judges; a unit it calls COVERED can still be represented badly. It exists because a model that
thinned the material at extraction cannot notice the thinning by re-reading its own summary.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple

CUE_TIME = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}\s*-->")
CUE_ID = re.compile(r"^\s*(\d+|[0-9a-f-]{16,})\s*$", re.I)
SRT_TAGS = re.compile(r"</?[vc][^>]*>")
SPEAKER = re.compile(r"^\s*([A-Z][\w.'-]*(?:,? [A-Z][\w.'-]*){0,3})\s*:\s+")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")
FENCE = re.compile(r"^\s*(```|~~~)")
OWN_UNIT = re.compile(r"^(#{1,6}\s|[-*+]\s|\d+[.)]\s|\|)")
NUMBERED_UNIT = re.compile(r"^\s*(\d+)\s*\|\s?(.*)$")

NUMBER = re.compile(r"\d[\d.,%/:-]*")
ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{1,}\b")
PROPER = re.compile(r"\b[A-Z][a-z][\w'-]{2,}\b")

# A unit is dropped only when it carries no claim - "Yes.", "OK.", "Right, yeah." A LENGTH floor
# drops short facts too ("KYC effort rose."), which is the loss this whole file exists to prevent.
MIN_CONTENT_WORDS = 2
MIN_ACRONYM_CHARS = 3

COVERED_OVERLAP = 0.66
WEAK_OVERLAP = 0.40

STOP = set("""a an the and or but if then than that this these those of in on at to for from by with
without into over under about as is are was were be been being it its it's they them their there here
we you your our i he she his her not no yes do does did done can could should would may might must
will shall have has had so such also more most much many few some any each every other another same
which who whom whose what when where why how all both either neither because while during before after
above below up down out off again further once only just very too now still yet own per via one two
three""".split())


class UnitResult(NamedTuple):
    """One unit's standing against the notes. Plain data, one call, written to stdout and dropped."""

    number: int
    verdict: str
    overlap: float
    text: str


def normalize_text(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).lower()

    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def find_content_words(unit: str) -> set[str]:
    return {word for word in normalize_text(unit).split()
            if len(word) >= 4 and word not in STOP}


def find_distinctive_tokens(unit: str) -> set[str]:
    """The tokens a note cannot drop without losing the unit: numbers, acronyms, names."""
    tokens = {match.group(0).rstrip(".,") for match in NUMBER.finditer(unit)}
    tokens |= set(ACRONYM.findall(unit))
    # skip the first word: a sentence-initial capital is not evidence of a name
    tokens |= set(PROPER.findall(" ".join(unit.split()[1:])))

    return {token for token in tokens if len(token) >= 2}


def carries_a_claim(unit: str) -> bool:
    """Is there anything here to lose? A number, a real acronym, or two content words."""
    if NUMBER.search(unit):
        return True

    if any(len(acronym) >= MIN_ACRONYM_CHARS for acronym in ACRONYM.findall(unit)):
        return True

    return len(find_content_words(unit)) >= MIN_CONTENT_WORDS


def is_transcript(text: str,
                  source: Path) -> bool:
    if source.suffix.lower() in {".vtt", ".srt", ".sbv", ".ttml"}:
        return True
    head = "\n".join(text.splitlines()[:40])

    return head.lstrip().upper().startswith("WEBVTT") or bool(CUE_TIME.search(head))


def strip_speech_chrome(text: str,
                        transcript: bool) -> list[str]:
    """Cue ids, timestamps and speaker tags out; every spoken claim stays."""
    kept: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if transcript:
            if CUE_TIME.match(line) or CUE_ID.match(line):
                continue
            line = SRT_TAGS.sub("", line)
            line = SPEAKER.sub("", line)
        if line.strip().upper() == "WEBVTT":
            continue
        kept.append(line)

    return kept


def extract_units(text: str,
                  source: Path) -> list[str]:
    """One source file -> the list of meaningful units it contains."""
    lines = strip_speech_chrome(text, is_transcript(text, source))
    units: list[str] = []
    pending: list[str] = []
    inside_fence = False

    def flush_pending() -> None:
        joined = " ".join(part.strip() for part in pending if part.strip()).strip()
        pending.clear()
        if not joined:
            return
        for piece in SENTENCE_END.split(joined):
            candidate = piece.strip()
            if carries_a_claim(candidate):
                units.append(candidate)

    # 1. one pass over the cleaned lines, splitting prose into sentences
    for line in lines:
        if FENCE.match(line):
            if inside_fence:
                units.append(" ".join(pending).strip())
                pending.clear()
            inside_fence = not inside_fence
            continue
        if inside_fence:
            pending.append(line)
            continue
        stripped = line.strip()
        if not stripped:
            flush_pending()
            continue
        # a heading, a bullet, a table row or a numbered step is its own unit
        if OWN_UNIT.match(stripped):
            flush_pending()
            units.append(stripped)
            continue
        pending.append(stripped)
    flush_pending()

    # 2. a sentence the speaker restated is one unit, not two (Lose nothing, reason 2)
    seen: set[str] = set()
    deduped: list[str] = []
    for unit in units:
        key = normalize_text(unit)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(unit)

    return deduped


def judge_unit(unit: str,
               number: int,
               note_text: str,
               note_words: set[str]) -> UnitResult:
    tokens = find_distinctive_tokens(unit)
    words = find_content_words(unit)
    overlap = len(words & note_words) / len(words) if words else 1.0
    if tokens:
        missing = [token for token in tokens if token not in note_text]
        if not missing:
            return UnitResult(number, "COVERED", overlap, unit)
        verdict = "UNCOVERED" if len(missing) == len(tokens) else "WEAK"

        return UnitResult(number, verdict, overlap, unit)
    if overlap >= COVERED_OVERLAP:
        return UnitResult(number, "COVERED", overlap, unit)
    verdict = "WEAK" if overlap >= WEAK_OVERLAP else "UNCOVERED"

    return UnitResult(number, verdict, overlap, unit)


def judge_units(units: list[str],
                note_text: str) -> list[UnitResult]:
    note_words = set(normalize_text(note_text).split())

    return [judge_unit(unit, number, note_text, note_words)
            for number, unit in enumerate(units, 1)]


def rank_by_what_a_note_cannot_lose(result: UnitResult) -> tuple[int, float, int]:
    """--limit truncates, so what it truncates matters.

    A unit carrying a number, an acronym or a name is the one a note cannot afford to have dropped.
    Those print first, lowest overlap first, and the meeting chatter falls off the end instead.
    """
    return -len(find_distinctive_tokens(result.text)), result.overlap, result.number


def read_numbered_units(units_path: Path) -> list[str]:
    units = []
    for line in units_path.read_text(encoding="utf-8", errors="replace").splitlines():
        numbered = NUMBERED_UNIT.match(line)
        if numbered:
            units.append(numbered.group(2))

    return units


def run_extract(source: Path,
                out_path: Path) -> int:
    if not source.is_file():
        print(f"not a file: {source}", file=sys.stderr)

        return 2
    units = extract_units(source.read_text(encoding="utf-8", errors="replace"), source)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    numbered = "\n".join(f"{number:04d} | {unit}" for number, unit in enumerate(units, 1))
    out_path.write_text(numbered + "\n", encoding="utf-8")
    print(f"{len(units)} units -> {out_path}")

    return 0


def run_cover(units_path: Path,
              note_paths: list[Path],
              limit: int,
              show: str) -> int:
    units = read_numbered_units(units_path)
    if not units:
        print(f"no units in {units_path} — run `extract` first", file=sys.stderr)

        return 2
    absent = [note for note in note_paths if not note.is_file()]
    if absent:
        print("no such note: " + ", ".join(str(note) for note in absent), file=sys.stderr)

        return 2

    note_text = "\n".join(note.read_text(encoding="utf-8", errors="replace")
                          for note in note_paths)
    results = judge_units(units, note_text)
    counts = {"COVERED": 0, "WEAK": 0, "UNCOVERED": 0}
    for result in results:
        counts[result.verdict] += 1

    flagged = [r for r in results if r.verdict != "COVERED"] if show == "gaps" else list(results)
    flagged.sort(key=rank_by_what_a_note_cannot_lose)
    for result in flagged[:limit]:                      # ranked, so the ids are not sequential
        print(f"{result.number:04d} {result.verdict:<9} {result.overlap:.2f}  {result.text[:150]}")
    if len(flagged) > limit:
        print(f"... {len(flagged) - limit} more (raise --limit)")
    print(f"\n{len(results)} units — {counts['COVERED']} covered, "
          f"{counts['WEAK']} weak, {counts['UNCOVERED']} uncovered")

    return 1 if counts["UNCOVERED"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subcommands = parser.add_subparsers(dest="command", required=True)

    extract = subcommands.add_parser("extract", help="split one source file into numbered units")
    extract.add_argument("source", type=Path)
    extract.add_argument("--out", type=Path, required=True,
                         help="where the numbered units are written")

    cover = subcommands.add_parser("cover", help="check the units against the notes written from them")
    cover.add_argument("--units", type=Path, required=True)
    cover.add_argument("--notes", type=Path, nargs="+", required=True)
    cover.add_argument("--limit", type=int, default=40,
                       help="max flagged units printed (default 40)")
    cover.add_argument("--show", choices=["gaps", "all"], default="gaps")

    args = parser.parse_args()
    if args.command == "extract":
        return run_extract(args.source, args.out)

    return run_cover(args.units, args.notes, args.limit, args.show)


if __name__ == "__main__":
    raise SystemExit(main())
