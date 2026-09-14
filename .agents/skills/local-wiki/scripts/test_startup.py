#!/usr/bin/env python3
"""Tests for startup.py. Stdlib only, no framework — run it directly.

    python3 test_startup.py

Three cases carry the whole point of the tool and must never be "simplified" away:

  2  an uninstalled .rag BLOCKS. This is the defect the tool was written for: a session read
     "install the RAG dependencies", found no command, took the grep fallback that was written for
     a *broken* venv, and answered with the gate half-run.

  4  the RI example in the file's own manual is NOT an instruction. A parser that reads the whole
     file sends every contributor to apply a maintenance job nobody issued.

  6  a failed step never stamps first_run. A flag flipped before the evidence is a claim the next
     session cannot doubt, and it disables retrieval silently for everyone after.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "startup.py"
SKILL_REL = Path(".agents") / "skills" / "local-wiki"
EXIT_BLOCKED = 3

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


def run(vault: Path, *args: str) -> subprocess.CompletedProcess:
    """Invoke the COPY inside the fixture vault, never the one in this repo.

    The tool finds the admin's instructions file and its own sibling tests relative to `__file__`,
    which is right in production — the skill lives inside the vault it serves. A harness that ran
    the repo copy against a fixture vault would read this repo's real files and quietly assert
    nothing, which is how a fixture's planted entry gets reported as "none pending".
    """
    return subprocess.run([sys.executable, str(vault / SKILL_REL / "scripts" / "startup.py"),
                           "--vault", str(vault), *args], capture_output=True, text=True)


def make_vault(tmp: Path, memory: str | None = None, remote: str | None = None,
               sibling_exit: int = 0) -> Path:
    """A vault carrying its own copy of the skill, the way a real clone does. No .rag by default."""
    vault = tmp / "vault"
    (vault / ".wiki").mkdir(parents=True)
    (vault / ".wiki" / "wiki-config.json").write_text(json.dumps({
        "last_reorganized_at": date.today().isoformat(),
        "reorg_stale_days": 30, "reorg_folder_notes": 25}))
    if memory is not None:
        (vault / ".wiki" / "memory_local.md").write_text(memory)
    skill = vault / SKILL_REL
    (skill / "scripts").mkdir(parents=True)
    shutil.copy(TOOL, skill / "scripts" / "startup.py")
    for name in ("test_contributors.py", "test_graph.py"):
        (skill / "scripts" / name).write_text(f"import sys; sys.exit({sibling_exit})\n")
    (skill / "remote_instructions.md").write_text(
        remote if remote is not None else "# Remote instructions\n")
    return vault


REGISTERED = ("# Memory — local\n\nusername: A\nemail: a@example.com\nuser_id: a@example.com\n"
              "role: contributor\nfirst_run: done\n\n## Applied remote instructions\n")


def test_unregistered_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp))
        proc = run(vault, "check")
        check("1 no memory file blocks", proc.returncode == EXIT_BLOCKED, proc.stdout)
        check("1 names the register command", "register" in proc.stdout, proc.stdout)


def test_uninstalled_rag_blocks() -> None:
    """The original defect. `.rag` present, venv absent — that is uninstalled, not broken."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp), memory=REGISTERED)
        (vault / ".rag" / "bin").mkdir(parents=True)
        (vault / ".rag" / "bin" / "rag").write_text("#!/bin/sh\nexit 0\n")
        proc = run(vault, "check")
        check("2 uninstalled .rag blocks", proc.returncode == EXIT_BLOCKED, proc.stdout)
        check("2 says uninstalled, not broken", "uninstalled" in proc.stdout, proc.stdout)
        check("2 names first-run", "first-run" in proc.stdout, proc.stdout)


def test_absent_rag_is_ready() -> None:
    """A vault with no .rag workspace is the normal case, not a deficiency."""
    with tempfile.TemporaryDirectory() as tmp:
        proc = run(make_vault(Path(tmp), memory=REGISTERED), "check")
        check("3 no .rag workspace is READY", proc.returncode == 0, proc.stdout)


def test_manual_example_is_not_an_instruction() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp), memory=REGISTERED, remote=(
            "# Remote instructions\n\n## How to write one\n\n"
            "```markdown\n## RI-003 — regenerate the graph cache\n```\n\n"
            "<!-- Admins: add entries below. Newest last. -->\n\n_No instructions yet._\n"))
        proc = run(vault, "check")
        check("4 documented example is not pending", proc.returncode == 0, proc.stdout)
        check("4 reports none pending", "none pending" in proc.stdout, proc.stdout)


def test_real_entry_is_pending() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp), memory=REGISTERED, remote=(
            "# Remote instructions\n\n<!-- Admins: add entries below. Newest last. -->\n\n"
            "## RI-007 — rebuild the cache\n\n**Do:** something\n"))
        proc = run(vault, "check")
        check("5 a real entry blocks", proc.returncode == EXIT_BLOCKED, proc.stdout)
        check("5 names the id", "RI-007" in proc.stdout, proc.stdout)


def test_failed_step_leaves_flag_unset() -> None:
    """first-run must not stamp when a step failed — the flag would then lie forever.

    The failure is staged the way it actually arrives: a .rag workspace whose launcher is dead and
    whose installer is missing, plus sibling tool tests that exit non-zero.
    """
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp), memory=REGISTERED.replace("first_run: done", "first_run:"),
                           sibling_exit=1)
        (vault / ".rag" / "bin").mkdir(parents=True)
        (vault / ".rag" / "bin" / "rag").write_text("#!/bin/sh\nexit 1\n")
        (vault / ".rag" / ".venv" / "bin").mkdir(parents=True)
        (vault / ".rag" / ".venv" / "bin" / "python").write_text("#!/bin/sh\nexit 1\n")
        proc = run(vault, "first-run")
        memory = (vault / ".wiki" / "memory_local.md").read_text()
        check("6 failed step exits non-zero", proc.returncode == EXIT_BLOCKED, proc.stdout)
        check("6 first_run left unset", "first_run: done" not in memory, memory)
        check("6 says it will retry", "retries next session" in proc.stdout, proc.stdout)


def test_passing_steps_stamp_the_flag() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp), memory=REGISTERED.replace("first_run: done", "first_run:"))
        proc = run(vault, "first-run")
        memory = (vault / ".wiki" / "memory_local.md").read_text()
        check("7 all steps pass stamps the flag", "first_run: done" in memory, memory)
        check("7 exits zero", proc.returncode == 0, proc.stdout)


def test_missing_index_fails_the_retrieval_test() -> None:
    """Dependencies installed and no index is still no retrieval — it must not stamp the flag.

    A fresh clone reaches this exact state: the venv exists, `rag status` answers, and `rag search`
    returns "no index". Treating the venv as proof is how a session ends up with a `done` flag and
    a vault it cannot search.
    """
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp), memory=REGISTERED.replace("first_run: done", "first_run:"))
        (vault / ".rag" / "bin").mkdir(parents=True)
        # status answers, index and search do not — the shape a never-indexed workspace has
        (vault / ".rag" / "bin" / "rag").write_text(
            '#!/bin/sh\ncase "$1" in status) exit 0 ;; *) echo "no index" >&2; exit 1 ;; esac\n')
        (vault / ".rag" / "bin" / "rag").chmod(0o755)
        (vault / ".rag" / ".venv" / "bin").mkdir(parents=True)
        (vault / ".rag" / ".venv" / "bin" / "python").write_text("#!/bin/sh\nexit 0\n")
        proc = run(vault, "first-run")
        memory = (vault / ".wiki" / "memory_local.md").read_text()
        check("12 no index fails first-run", proc.returncode == EXIT_BLOCKED, proc.stdout)
        check("12 first_run left unset", "first_run: done" not in memory, memory)
        check("12 the index build is a step", "build index" in proc.stdout, proc.stdout)


def test_stale_flag_is_caught() -> None:
    """`first_run: done` with a dead .rag is a stale claim, not a pass."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp), memory=REGISTERED)
        (vault / ".rag" / "bin").mkdir(parents=True)
        (vault / ".rag" / "bin" / "rag").write_text("#!/bin/sh\nexit 0\n")
        proc = run(vault, "check")
        check("8 stale first_run blocks", proc.returncode == EXIT_BLOCKED, proc.stdout)
        check("8 says the flag is stale", "stale" in proc.stdout, proc.stdout)


def test_user_id_is_repaired_from_email() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp), memory=(
            "# Memory — local\n\nusername: A\nemail: a@example.com\nfirst_run: done\n"
            "\n## Applied remote instructions\n"))
        run(vault, "check")
        memory = (vault / ".wiki" / "memory_local.md").read_text()
        check("9 user_id derived from email", "user_id: a@example.com" in memory, memory)


def test_verify_rejects_an_invented_token() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp), memory=REGISTERED)
        run(vault, "check")
        token = json.loads((vault / ".wiki" / ".startup-receipt.json").read_text())["token"]
        check("10 the real token verifies", run(vault, "verify", "--token", token).returncode == 0)
        bad = run(vault, "verify", "--token", "2026-01-01-deadbeef")
        check("10 an invented token is rejected", bad.returncode == EXIT_BLOCKED, bad.stderr)


def test_verify_rejects_a_blocked_receipt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        vault = make_vault(Path(tmp))
        run(vault, "check")
        token = json.loads((vault / ".wiki" / ".startup-receipt.json").read_text())["token"]
        proc = run(vault, "verify", "--token", token)
        check("11 a BLOCKED receipt does not verify", proc.returncode == EXIT_BLOCKED, proc.stderr)


def main() -> int:
    print("startup.py")
    for fn in (test_unregistered_blocks, test_uninstalled_rag_blocks, test_absent_rag_is_ready,
               test_manual_example_is_not_an_instruction, test_real_entry_is_pending,
               test_failed_step_leaves_flag_unset, test_passing_steps_stamp_the_flag,
               test_missing_index_fails_the_retrieval_test,
               test_stale_flag_is_caught, test_user_id_is_repaired_from_email,
               test_verify_rejects_an_invented_token, test_verify_rejects_a_blocked_receipt):
        try:
            fn()
        except Exception as exc:  # a crash is a failure, not an abort
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
