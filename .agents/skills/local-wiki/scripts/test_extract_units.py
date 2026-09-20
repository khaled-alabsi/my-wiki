#!/usr/bin/env python3
"""Tests for extract_units.py. Stdlib only, no framework — run it directly.

    python3 test_extract_units.py

Every case here is a way a second pass can lie. The two that matter most:

  NUMBER   a note that says "above a threshold" where the source said "above 15,000 EUR" must come
           back UNCOVERED. This is the exact loss the second pass exists to catch, and an overlap
           score alone passes it, because every other word in the sentence is present.
  QA       a transcript's question-and-answer stretch yields units like any other text. A checker
           that drops them silently reproduces the failure that prompted this file.

The no-false-positive cases are as load-bearing as the rest: a checker that flags material the note
genuinely carries gets ignored, and an ignored checker is worse than none.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "extract_units.py"

_failures: list[str] = []
_passed = 0


def check(name: str,
          condition: bool,
          detail: str = "") -> None:
    global _passed
    if condition:
        _passed += 1
        print(f"  ok    {name}")
    else:
        _failures.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], capture_output=True, text=True
    )


def extract_test_units(text: str,
                       filename: str = "source.md") -> list[str]:
    with tempfile.TemporaryDirectory() as workdir:
        source = Path(workdir) / filename
        source.write_text(text, encoding="utf-8")
        units_path = Path(workdir) / "units.txt"
        proc = run("extract", str(source), "--out", str(units_path))
        assert proc.returncode == 0, proc.stderr
        units = [line.split(" | ", 1)[1]
                 for line in units_path.read_text().splitlines() if " | " in line]

    return units


def cover_test_notes(source_text: str,
                     note_text: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as workdir:
        source = Path(workdir) / "source.md"
        source.write_text(source_text, encoding="utf-8")
        units_path = Path(workdir) / "units.txt"
        run("extract", str(source), "--out", str(units_path))
        note = Path(workdir) / "note.md"
        note.write_text(note_text, encoding="utf-8")
        proc = run("cover", "--units", str(units_path), "--notes", str(note))
        exit_code, printed = proc.returncode, proc.stdout

    return exit_code, printed


# --- extraction ------------------------------------------------------------


def test_sentences_become_units() -> None:
    units = extract_test_units("KYC effort rose. Outreach dropped from 10 years to 5 years.")
    check("SENTENCE two sentences, two units", len(units) == 2, f"got {units}")


def test_bullets_and_headings_are_their_own_units() -> None:
    units = extract_test_units("## Six dimensions\n\n- Politically exposed persons, e.g. a town mayor\n- Ultimate beneficial owners\n")
    check("BULLET heading plus two bullets = 3 units", len(units) == 3, f"got {units}")


def test_transcript_cues_and_speaker_tags_are_stripped() -> None:
    vtt = (
        "WEBVTT\n\n1\n00:00:08.059 --> 00:00:08.459\n<v Coric, Kristofor>The penalty regime is stricter.\n\n"
        "2\n00:00:09.000 --> 00:00:10.000\nNot necessarily higher penalties.\n"
    )
    units = extract_test_units(vtt, "rec.vtt")
    joined = " ".join(units)
    check("CUE no timestamps survive", "-->" not in joined, joined)
    check("CUE no speaker tag survives", "<v " not in joined and "Coric" not in joined, joined)
    check("CUE both claims survive", len(units) == 2, f"got {units}")


def test_short_noise_is_dropped_but_facts_are_not() -> None:
    units = extract_test_units("Yes.\nOK.\nThe off-boarding window shrank from 10 years to 5 years.")
    check("NOISE filler under the floor is dropped", len(units) == 1, f"got {units}")


def test_duplicate_sentences_collapse() -> None:
    units = extract_test_units("The mayor of a town is a PEP. The mayor of a town is a PEP.")
    check("DEDUPE a restated sentence is one unit", len(units) == 1, f"got {units}")


# --- coverage --------------------------------------------------------------


def test_dropped_number_is_uncovered() -> None:
    code, out = cover_test_notes(
        "Outreach was cut from 10 years to 5 years for existing customers.",
        "# Outreach\n\nOutreach for existing customers was cut.\n",
    )
    check("NUMBER a dropped threshold fails the check", code == 1, out)
    check("NUMBER the gap names the unit", "UNCOVERED" in out or "WEAK" in out, out)


def test_dropped_name_is_flagged() -> None:
    code, out = cover_test_notes(
        "The Schufa data is assumed fresh at the point of onboarding.",
        "# Onboarding\n\nExternal data is assumed fresh at onboarding.\n",
    )
    check("NAME a dropped proper noun is flagged", code == 1, out)


def test_fully_carried_unit_passes() -> None:
    code, out = cover_test_notes(
        "Outreach was cut from 10 years to 5 years for existing customers.",
        "# Outreach\n\nOutreach for existing customers was cut from 10 years to 5 years.\n",
    )
    check("CARRIED a fully represented unit passes", code == 0, out)
    check("CARRIED it is not reported as a gap", "UNCOVERED" not in out, out)


def test_qa_stretch_yields_units() -> None:
    vtt = (
        "WEBVTT\n\n1\n00:10:00.000 --> 00:10:04.000\nQuestion: what happens to non-German customers?\n\n"
        "2\n00:10:05.000 --> 00:10:09.000\nAnswer: they are handled through the obligation library.\n"
    )
    units = extract_test_units(vtt, "qa.vtt")
    check("QA both the question and the answer are units", len(units) == 2, f"got {units}")


def test_output_is_bounded() -> None:
    source = "\n".join(f"Fact {i} concerns instrument {i} and threshold {i}000 EUR." for i in range(60))
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "source.md"
        src.write_text(source, encoding="utf-8")
        out = Path(d) / "units.txt"
        run("extract", str(src), "--out", str(out))
        note = Path(d) / "note.md"
        note.write_text("# Nothing\n", encoding="utf-8")
        proc = run("cover", "--units", str(out), "--notes", str(note), "--limit", "5")
        printed = [ln for ln in proc.stdout.splitlines() if " UNCOVERED " in ln]
    check("BOUND --limit caps what is printed", len(printed) == 5, f"printed {len(printed)}")
    check("BOUND the rest is counted, not dumped", "more (raise --limit)" in proc.stdout, proc.stdout)


def test_flagged_units_are_ranked_before_the_limit_truncates() -> None:
    """The gap that matters must survive --limit, whatever order the source happened to be in."""
    source = (
        "So hello and welcome everybody today.\n"
        "Before we dive in, a few words about myself.\n"
        "Can everyone see the presentation alright?\n"
        "The outreach floor was cut to 5 years under AMLR Article 77.\n"
    )
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "source.md"
        src.write_text(source, encoding="utf-8")
        out = Path(d) / "units.txt"
        run("extract", str(src), "--out", str(out))
        note = Path(d) / "note.md"
        note.write_text("# Nothing relevant\n", encoding="utf-8")
        proc = run("cover", "--units", str(out), "--notes", str(note), "--limit", "1")
    printed = [ln for ln in proc.stdout.splitlines() if ln[:4].isdigit()]
    check("RANK the unit carrying the number and the acronym is printed first",
          printed and "AMLR" in printed[0], proc.stdout)


def test_missing_units_file_is_an_error_not_a_pass() -> None:
    with tempfile.TemporaryDirectory() as d:
        empty = Path(d) / "units.txt"
        empty.write_text("", encoding="utf-8")
        note = Path(d) / "note.md"
        note.write_text("x", encoding="utf-8")
        proc = run("cover", "--units", str(empty), "--notes", str(note))
    check("EMPTY an empty units file exits 2, never 0", proc.returncode == 2, proc.stderr)


def main() -> int:
    print(f"testing {TOOL.name}\n")
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception as exc:
            _failures.append(f"{fn.__name__} raised {exc!r}")
            print(f"  ERROR {fn.__name__}: {exc!r}")
    print()
    if _failures:
        print(f"{len(_failures)} failed, {_passed} passed")
        for line in _failures:
            print(f"  - {line}")
        return 1
    print(f"all {_passed} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
