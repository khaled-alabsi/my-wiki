#!/usr/bin/env python3
"""Tests for reset_vault.py. Stdlib only; run directly."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "reset_vault.py"

SAMPLE = """---
author: someone
type: use-case
status: sample
---

# A sample note
"""

REAL = """---
author: someone
type: use-case
---

# A real note
"""


def run(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(vault), *args],
        capture_output=True, text=True,
    )


class ResetVaultTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / ".wiki" / "agent-memory").mkdir(parents=True)
        (self.tmp / ".wiki" / "contributors.json").write_text(
            '{"version": 1, "contributors": {"a@b.c": {"files": 3}}}')
        (self.tmp / ".wiki" / "wiki-config.json").write_text(
            json.dumps({"version": 1, "intake_wave": 7, "last_reorganized_at": "2020-01-01"}))
        (self.tmp / ".wiki" / "graph.sqlite").write_text("derived")
        (self.tmp / ".wiki" / "manifest.json").write_text("{}")
        (self.tmp / "use-cases").mkdir()
        (self.tmp / "processes" / "deep").mkdir(parents=True)
        (self.tmp / "use-cases" / "sample-one.md").write_text(SAMPLE)
        (self.tmp / "processes" / "deep" / "sample-two.md").write_text(SAMPLE)
        (self.tmp / "use-cases" / "real-one.md").write_text(REAL)

    def test_dry_run_moves_nothing(self) -> None:
        result = run(self.tmp, "--scope", "sample")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dry run", result.stdout)
        self.assertTrue((self.tmp / "use-cases" / "sample-one.md").exists())
        self.assertTrue((self.tmp / ".wiki" / "graph.sqlite").exists())

    def test_sample_scope_spares_unmarked_notes(self) -> None:
        result = run(self.tmp, "--scope", "sample", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.tmp / "use-cases" / "sample-one.md").exists())
        self.assertFalse((self.tmp / "processes" / "deep" / "sample-two.md").exists())
        self.assertTrue((self.tmp / "use-cases" / "real-one.md").exists(),
                        "a note without `status: sample` must survive a sample reset")

    def test_notes_are_trashed_not_deleted(self) -> None:
        run(self.tmp, "--scope", "sample", "--yes")
        trashed = list((self.tmp / ".wiki" / ".trash").rglob("sample-two.md"))
        self.assertEqual(len(trashed), 1, "the note must be recoverable from the trash")
        self.assertTrue(str(trashed[0]).endswith("processes/deep/sample-two.md"),
                        "the trashed copy keeps its original path")

    def test_derived_state_is_deleted_and_tracking_reset(self) -> None:
        run(self.tmp, "--scope", "sample", "--yes")
        self.assertFalse((self.tmp / ".wiki" / "graph.sqlite").exists())
        self.assertFalse((self.tmp / ".wiki" / "manifest.json").exists())
        self.assertEqual(json.loads((self.tmp / ".wiki" / "contributors.json").read_text()),
                         {"version": 1, "contributors": {}})
        config = json.loads((self.tmp / ".wiki" / "wiki-config.json").read_text())
        self.assertNotIn("intake_wave", config,
                         "the retired wave knob is dropped, never left reading as a live setting")
        self.assertNotEqual(config["last_reorganized_at"], "2020-01-01")

    def test_all_scope_takes_unmarked_notes_too(self) -> None:
        run(self.tmp, "--scope", "all", "--yes")
        self.assertFalse((self.tmp / "use-cases" / "real-one.md").exists())
        self.assertTrue((self.tmp / "use-cases").is_dir(),
                        "the accepted structure survives a reset")

    def test_emptied_subfolders_are_removed_but_not_the_structure(self) -> None:
        run(self.tmp, "--scope", "sample", "--yes")
        self.assertFalse((self.tmp / "processes" / "deep").exists())
        self.assertTrue((self.tmp / "processes").is_dir())

    def test_frontmatter_is_read_from_the_head_only(self) -> None:
        """A `status: sample` line below the frontmatter must not mark the note."""
        decoy = (self.tmp / "use-cases" / "decoy.md")
        decoy.write_text(REAL + "\n" + "filler\n" * 5000 + "status: sample\n")
        run(self.tmp, "--scope", "sample", "--yes")
        self.assertTrue(decoy.exists(),
                        "only frontmatter marks a note as sample, never body text")

    def test_frontmatter_check_reads_a_bounded_prefix(self) -> None:
        """The scan must not read whole notes to test one frontmatter line.

        Cost has to scale with frontmatter size, not vault size: an unbounded read
        here is a full pass over every note in the vault on every reset.
        """
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            import reset_vault
        finally:
            sys.path.pop(0)

        calls: list[object] = []
        real = (self.tmp / "use-cases" / "real-one.md")

        class RecordingHandle:
            def __init__(self, inner): self.inner = inner
            def read(self, size=-1):
                calls.append(size)
                return self.inner.read(size)
            def __enter__(self): return self
            def __exit__(self, *exc): self.inner.close(); return False

        class RecordingPath:
            def open(self, *args, **kwargs):
                return RecordingHandle(real.open(*args, **kwargs))

        reset_vault.has_sample_status(RecordingPath())
        self.assertTrue(calls, "the frontmatter check must read the file")
        self.assertTrue(all(isinstance(n, int) and 0 < n <= reset_vault.FRONTMATTER_BYTES
                            for n in calls),
                        f"every read must be bounded, got {calls}")

    def seed_tag_tree(self) -> Path:
        inventory = self.tmp / ".wiki" / "tags.md"
        inventory.write_text("# Tags\n\nOwner's own line.\n\n- `banking` — Running a bank.\n"
                             "- `banking/accounts`\n", encoding="utf-8")
        (self.tmp / ".wiki" / ".tag-run.json").write_text('{"scope": "", "done": ["use-cases"]}')
        return inventory

    def test_full_reset_empties_the_tag_tree(self) -> None:
        inventory = self.seed_tag_tree()
        result = run(self.tmp, "--scope", "all", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        text = inventory.read_text(encoding="utf-8")
        self.assertNotIn("- `", text, "a vault with no notes must list no tag nodes")
        self.assertIn("Owner's own line.", text, "the lines above the nodes are the owner's and stay")
        self.assertFalse((self.tmp / ".wiki" / ".tag-run.json").exists(),
                         "a retag receipt about notes that are gone is derived state")

    def test_sample_reset_keeps_the_tag_tree(self) -> None:
        inventory = self.seed_tag_tree()
        before = inventory.read_text(encoding="utf-8")
        result = run(self.tmp, "--scope", "sample", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(inventory.read_text(encoding="utf-8"), before,
                         "real notes remain, so which nodes to drop is a decision, not a reset")
        self.assertIn("tags.py", result.stdout, "the run must be told to check the tree afterwards")

    def test_refuses_a_directory_that_is_not_a_vault(self) -> None:
        result = run(self.tmp / "use-cases", "--scope", "all", "--yes")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
