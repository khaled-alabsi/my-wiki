#!/usr/bin/env python3
"""Tests for apply_profile.py — splicing a knowledge profile into a generated artifact.

    python3 test_apply_profile.py

The assertions that matter are the ones about what must NOT change:

  no profile == base        `init` with no profile has to produce an artifact byte-identical to the
                            template. "Almost identical" means every vault silently carries an
                            empty wrapper, and the removal path can never be verified again.
  removal restores base     Byte for byte. `reshape` swaps profiles by removing and re-applying, so
                            a lossy removal corrupts the artifact on the first swap.
  idempotent                Applied at init, re-applied on every regeneration. A non-idempotent
                            splice doubles every fragment on the second `enhance`.
  three hooks in one file   placement-rules.md carries three. The first implementation stripped the
                            whole file before each insert and silently kept only the last one.
  fences are not headings   An overlay fragment quoting `## Related` inside a ```markdown fence
                            truncated the whole Overlay section, dropping every fragment after it.
  a bad hook id fails loud  A fragment that applies nowhere is a doctrine that half-applies, and
                            nothing downstream would ever say so.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "apply_profile.py"
TEMPLATE = HERE.parent / "assets/templates/local-skill"
PROFILE = HERE.parent / "references/knowledge-profiles/process-knowledge.md"

_failures: list[str] = []
_passed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _passed
    if condition:
        _passed += 1
        print(f"  ok    {name}")
    else:
        _failures.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True)


def fresh() -> tuple[Path, Path, Path]:
    """A pristine copy of the template, a working copy, and a vault root."""
    root = Path(tempfile.mkdtemp(prefix="profile-test-"))
    base, artifact, vault = root / "base", root / "artifact", root / "vault"
    shutil.copytree(TEMPLATE, base)
    shutil.copytree(TEMPLATE, artifact)
    vault.mkdir()
    return base, artifact, vault


def tree_diff(a: Path, b: Path) -> list[str]:
    out = []
    for src in sorted(a.rglob("*")):
        if not src.is_file() or "__pycache__" in src.parts:
            continue
        dst = b / src.relative_to(a)
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            out.append(str(src.relative_to(a)))
    return out


MINIMAL = """# Tiny

## Use when

A one-line profile used by the tests.

## Doctrine

<!-- an author note that must not reach the vault -->

### Rule

Classify before placing.

## Overlay

### hook: update-classify

Tiny says: classify first.
"""


def write_profile(root: Path, text: str, name: str = "tiny") -> Path:
    path = root / f"{name}.md"
    path.write_text(text, encoding="utf-8")
    return path


# --- the base case ---------------------------------------------------------------------------

def test_unapplied_template_is_untouched() -> None:
    """`init` with no profile must produce the template exactly — the hooks are invisible."""
    base, artifact, _ = fresh()
    check("80 an untouched artifact equals the template", tree_diff(base, artifact) == [],
          str(tree_diff(base, artifact)))
    result = run("--artifact", str(artifact), "--check")
    check("80 --check reports no profile", result.returncode == 1, result.stdout[:200])
    check("80 --check still lists the available hooks", "hook(s) available" in result.stdout,
          result.stdout[:200])


def test_hooks_render_as_nothing() -> None:
    """A bare hook is an HTML comment: it must not appear as visible text in any file."""
    _, artifact, _ = fresh()
    for path in artifact.rglob("*.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "profile-hook" in line:
                check(f"81 hook in {path.name} is a comment",
                      line.strip().startswith("<!--") and line.strip().endswith("-->"),
                      line[:80])
                break


# --- applying --------------------------------------------------------------------------------

def test_apply_fills_every_fragment() -> None:
    base, artifact, vault = fresh()
    result = run("--profile", str(PROFILE), "--artifact", str(artifact), "--vault", str(vault))
    check("82 apply succeeds", result.returncode == 0, result.stderr[:300])
    state = run("--artifact", str(artifact), "--check")
    check("82 --check names the profile", "process-knowledge" in state.stdout, state.stdout[:200])
    check("82 nothing is left unfilled", "unfilled:" not in state.stdout, state.stdout[:300])
    changed = tree_diff(base, artifact)
    check("82 only hooked files changed", len(changed) == 9, str(changed))
    check("82 an unhooked file is untouched", "references/glossary.md" not in changed, str(changed))


def test_three_hooks_in_one_file_all_survive() -> None:
    """The regression: stripping the whole file before each insert kept only the last hook."""
    _, artifact, vault = fresh()
    run("--profile", str(PROFILE), "--artifact", str(artifact), "--vault", str(vault))
    text = (artifact / "references/placement-rules.md").read_text(encoding="utf-8")
    check("83 all three placement hooks are filled", text.count("<!-- profile:process-knowledge start -->") == 3,
          f"{text.count('start -->')} block(s)")


def test_fragment_after_a_fenced_heading_survives() -> None:
    """The regression: `## Related` inside a fence truncated the Overlay section."""
    _, artifact, vault = fresh()
    run("--profile", str(PROFILE), "--artifact", str(artifact), "--vault", str(vault))
    text = (artifact / "references/modes/ask.md").read_text(encoding="utf-8")
    check("84 the fragment after the fenced one is applied",
          "<!-- profile:process-knowledge start -->" in text, "ask-routing missing")


def test_apply_is_idempotent() -> None:
    _, artifact, vault = fresh()
    run("--profile", str(PROFILE), "--artifact", str(artifact), "--vault", str(vault))
    once = (artifact / "SKILL.md").read_bytes()
    run("--profile", str(PROFILE), "--artifact", str(artifact), "--vault", str(vault))
    run("--profile", str(PROFILE), "--artifact", str(artifact), "--vault", str(vault))
    check("85 applying three times equals applying once",
          (artifact / "SKILL.md").read_bytes() == once, "content grew")


def test_remove_restores_the_base_exactly() -> None:
    base, artifact, vault = fresh()
    run("--profile", str(PROFILE), "--artifact", str(artifact), "--vault", str(vault))
    result = run("--artifact", str(artifact), "--remove")
    check("86 remove succeeds", result.returncode == 0, result.stderr[:200])
    check("86 the artifact is byte-identical to the template again",
          tree_diff(base, artifact) == [], str(tree_diff(base, artifact)))
    again = run("--artifact", str(artifact), "--remove")
    check("86 removing twice is not an error state", again.returncode == 1, again.stdout[:200])


def test_swapping_profiles_leaves_one_overlay() -> None:
    """What `reshape` does: remove one, apply another."""
    _, artifact, vault = fresh()
    tiny = write_profile(vault, MINIMAL)
    run("--profile", str(PROFILE), "--artifact", str(artifact), "--vault", str(vault))
    run("--artifact", str(artifact), "--remove")
    run("--profile", str(tiny), "--artifact", str(artifact), "--vault", str(vault))
    state = run("--artifact", str(artifact), "--check")
    check("87 only the new profile is applied",
          "tiny" in state.stdout and "process-knowledge" not in state.stdout, state.stdout[:200])
    text = (artifact / "references/modes/update.md").read_text(encoding="utf-8")
    check("87 the old fragment is gone", "Classify first" not in text, "stale fragment left")


# --- the doctrine copy -----------------------------------------------------------------------

def test_doctrine_is_written_to_the_vault() -> None:
    _, artifact, vault = fresh()
    run("--profile", str(PROFILE), "--artifact", str(artifact), "--vault", str(vault))
    doctrine = vault / ".wiki/knowledge-profile.md"
    check("88 the doctrine lands in .wiki/", doctrine.exists(), "not written")
    text = doctrine.read_text(encoding="utf-8")
    check("88 it carries the classification sequence", "Classification sequence" in text,
          text[:200])
    check("88 it carries the structure implications", "Structure implications" in text, text[:200])
    check("88 the overlay is NOT in it", "### hook:" not in text, "overlay leaked into the vault")
    check("88 it stays within its read-every-placement budget",
          len(text.splitlines()) <= 220, f"{len(text.splitlines())} lines")


def test_author_notes_do_not_reach_the_vault() -> None:
    _, artifact, vault = fresh()
    tiny = write_profile(vault, MINIMAL)
    run("--profile", str(tiny), "--artifact", str(artifact), "--vault", str(vault))
    text = (vault / ".wiki/knowledge-profile.md").read_text(encoding="utf-8")
    check("89 the author's note is stripped", "must not reach the vault" not in text, text[:300])
    check("89 the doctrine body survives", "Classify before placing" in text, text[:300])


def test_no_vault_means_no_doctrine_file() -> None:
    _, artifact, vault = fresh()
    run("--profile", str(PROFILE), "--artifact", str(artifact))
    check("90 without --vault nothing is written outside the artifact",
          not (vault / ".wiki/knowledge-profile.md").exists(), "wrote anyway")


# --- failures --------------------------------------------------------------------------------

def test_unknown_hook_id_fails() -> None:
    _, artifact, vault = fresh()
    bad = write_profile(vault, MINIMAL.replace("### hook: update-classify",
                                               "### hook: not-a-real-hook"), "bad")
    result = run("--profile", str(bad), "--artifact", str(artifact), "--vault", str(vault))
    check("91 an unknown hook id is a hard error", result.returncode == 2, result.stdout[:200])
    check("91 the error names the offending hook", "not-a-real-hook" in result.stderr,
          result.stderr[:200])
    check("91 nothing was applied", run("--artifact", str(artifact), "--check").returncode == 1,
          "partial application")


def test_missing_marker_fails() -> None:
    """A profile filling a hook the artifact does not declare must not pass silently."""
    _, artifact, vault = fresh()
    target = artifact / "references/modes/update.md"
    target.write_text(target.read_text(encoding="utf-8").replace(
        "<!-- profile-hook: update-classify -->", ""), encoding="utf-8")
    tiny = write_profile(vault, MINIMAL)
    result = run("--profile", str(tiny), "--artifact", str(artifact), "--vault", str(vault))
    check("92 a missing marker is a hard error", result.returncode == 2, result.stdout[:200])
    check("92 the error says which file and hook", "update.md" in result.stderr
          and "update-classify" in result.stderr, result.stderr[:300])


def test_malformed_profile_fails() -> None:
    _, artifact, vault = fresh()
    bad = write_profile(vault, "# No sections here\n\nnothing.\n", "empty")
    result = run("--profile", str(bad), "--artifact", str(artifact), "--vault", str(vault))
    check("93 a profile missing its sections is rejected", result.returncode == 2,
          result.stdout[:200])
    check("93 the error names what is missing", "Doctrine" in result.stderr, result.stderr[:200])


def main() -> int:
    if not TOOL.exists():
        print(f"missing: {TOOL}", file=sys.stderr)
        return 2
    # This file ships inside generated artifacts too, where `apply_profile.py` is needed by
    # `reshape` but the template and the profile library it tests against do not exist. Skipping
    # cleanly matters: the artifact runs its whole test suite on a fresh clone's first run, and a
    # hard error there reads as a broken vault rather than a test with nothing to test.
    if not TEMPLATE.exists() or not PROFILE.exists():
        print("apply_profile.py — skipped: no template or profile library here "
              "(this copy ships inside a vault, where those live in the `wiki` skill)")
        return 0
    print("apply_profile.py")
    for fn in (test_unapplied_template_is_untouched, test_hooks_render_as_nothing,
               test_apply_fills_every_fragment, test_three_hooks_in_one_file_all_survive,
               test_fragment_after_a_fenced_heading_survives, test_apply_is_idempotent,
               test_remove_restores_the_base_exactly, test_swapping_profiles_leaves_one_overlay,
               test_doctrine_is_written_to_the_vault, test_author_notes_do_not_reach_the_vault,
               test_no_vault_means_no_doctrine_file, test_unknown_hook_id_fails,
               test_missing_marker_fails, test_malformed_profile_fails):
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
