#!/usr/bin/env python3
"""Tests for contributors.py. Stdlib only, no framework — run it directly.

    python3 test_contributors.py

Ships with the artifact on purpose: the local skill's first run on a fresh clone executes this
before anything writes to the shared contributors.json, so a broken tool is caught on the machine
it is broken on rather than by corrupting a file every contributor shares.

Case 2 and case 8 are the two that matter most and the two most likely to be "optimized" away by a
later edit:

  2  repeats are KEPT. Deduping destroys the recency signal the write heads-up depends on.
  8  concurrent writes both survive. A lost update here silently erases someone's history.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "contributors.py"
USER = "alice@example.com"
OTHER = "bob@example.com"

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
    return subprocess.run(
        [sys.executable, str(TOOL), *args, "--vault", str(vault)],
        capture_output=True, text=True,
    )


def load(vault: Path) -> dict:
    return json.loads((vault / ".wiki" / "contributors.json").read_text(encoding="utf-8"))


def entries(vault: Path, user: str = USER) -> list[dict]:
    return load(vault)["contributors"].get(user, {}).get("entries", [])


def new_vault() -> Path:
    vault = Path(tempfile.mkdtemp(prefix="contrib-test-"))
    (vault / ".wiki").mkdir()
    (vault / "notes").mkdir()
    (vault / "notes" / "a.md").write_text("# A\n", encoding="utf-8")
    (vault / "notes" / "b.md").write_text("# B\n", encoding="utf-8")
    return vault


def iso(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- 1: creates the file ---------------------------------------------------------------------

def test_record_creates_file() -> None:
    vault = new_vault()
    result = run(vault, "record", "--user-id", USER, "--path", "notes/a.md", "--type", "added")
    check("1 record on a missing file exits 0", result.returncode == 0, result.stderr[:200])
    data = load(vault)
    check("1 file is valid JSON with version", data.get("version") == 1)
    check("1 exactly one entry", len(entries(vault)) == 1, str(entries(vault)))
    check("1 entry has path/type/ts",
          set(entries(vault)[0]) >= {"path", "type", "ts"}, str(entries(vault)[0]))


# --- 2: repeats are kept, never deduped ------------------------------------------------------

def test_repeats_are_kept() -> None:
    vault = new_vault()
    run(vault, "record", "--user-id", USER, "--path", "notes/a.md", "--type", "added")
    run(vault, "record", "--user-id", USER, "--path", "notes/a.md", "--type", "edited")
    got = entries(vault)
    check("2 same user + same path twice appends a SECOND entry", len(got) == 2,
          f"expected 2, got {len(got)} — deduping breaks the recency heads-up")
    check("2 the two entries keep their distinct types",
          [e["type"] for e in got] == ["added", "edited"], str(got))


# --- 3: multiple paths in one call -----------------------------------------------------------

def test_multiple_paths() -> None:
    vault = new_vault()
    run(vault, "record", "--user-id", USER,
        "--path", "notes/a.md", "--path", "notes/b.md", "--path", "index.md", "--type", "added")
    got = entries(vault)
    check("3 three --path flags produce three entries", len(got) == 3, str(len(got)))
    check("3 each entry carries a timestamp", all(e.get("ts") for e in got))


# --- 4 and 5: the recency window -------------------------------------------------------------

def _seed(vault: Path, user: str, path: str, hours_ago: float) -> None:
    store = vault / ".wiki" / "contributors.json"
    data = json.loads(store.read_text(encoding="utf-8")) if store.exists() else {
        "version": 1, "contributors": {}}
    data["contributors"].setdefault(user, {"entries": []})["entries"].append(
        {"path": path, "type": "edited", "ts": iso(hours_ago)})
    store.write_text(json.dumps(data), encoding="utf-8")


def test_recent_touch_hit() -> None:
    vault = new_vault()
    _seed(vault, OTHER, "notes/a.md", hours_ago=2)
    result = run(vault, "query", "--path", "notes/a.md", "--since-hours", "24")
    check("4 a 2h-old touch is reported (exit 0)", result.returncode == 0, result.stderr[:200])
    check("4 the report names the user", OTHER in result.stdout, result.stdout[:200])


def test_recent_touch_miss() -> None:
    vault = new_vault()
    _seed(vault, OTHER, "notes/a.md", hours_ago=40)
    result = run(vault, "query", "--path", "notes/a.md", "--since-hours", "24")
    check("5 a 40h-old touch is NOT reported (exit 1)", result.returncode == 1,
          f"exit {result.returncode} — a stale touch must not raise a false heads-up")


# --- 6: output stays bounded on a large log --------------------------------------------------

def test_query_output_is_bounded() -> None:
    vault = new_vault()
    store = vault / ".wiki" / "contributors.json"
    big = {"version": 1, "contributors": {USER: {"entries": [
        {"path": f"notes/n{i}.md", "type": "edited", "ts": iso(1)} for i in range(50_000)]}}}
    store.write_text(json.dumps(big), encoding="utf-8")
    result = run(vault, "query", "--user-id", USER, "--limit", "5")
    check("6 a 50k-entry log does not dump the log", len(result.stdout) < 4000,
          f"{len(result.stdout)} chars of output — query must answer, not return the log")
    check("6 query on a large log still exits 0", result.returncode == 0, result.stderr[:200])
    stats = run(vault, "query", "--stats")
    check("6 --stats is bounded too", len(stats.stdout) < 2000, f"{len(stats.stdout)} chars")


# --- 7: corrupt JSON is preserved, never silently replaced -----------------------------------

def test_corrupt_json_is_backed_up() -> None:
    vault = new_vault()
    store = vault / ".wiki" / "contributors.json"
    store.write_text('{"version": 1, "contributors": {ohno', encoding="utf-8")
    result = run(vault, "record", "--user-id", USER, "--path", "notes/a.md", "--type", "added")
    check("7 corrupt JSON exits non-zero", result.returncode != 0, f"exit {result.returncode}")
    backups = list((vault / ".wiki").glob("contributors.json.corrupt-*"))
    check("7 the corrupt file is backed up", len(backups) == 1, str(backups))
    check("7 the backup keeps the original bytes",
          backups and "ohno" in backups[0].read_text(encoding="utf-8"))
    check("7 the failure is reported on stderr", "corrupt" in result.stderr.lower(),
          result.stderr[:200])


# --- 8: concurrent writers both survive ------------------------------------------------------

def test_concurrent_records() -> None:
    vault = new_vault()
    run(vault, "record", "--user-id", USER, "--path", "notes/seed.md", "--type", "added")
    procs = [
        subprocess.Popen(
            [sys.executable, str(TOOL), "record", "--user-id", u,
             "--path", f"notes/{u[0]}.md", "--type", "added", "--vault", str(vault)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for u in (USER, OTHER, "carol@example.com", "dave@example.com")
    ]
    for p in procs:
        p.wait(timeout=30)
    data = load(vault)
    total = sum(len(c["entries"]) for c in data["contributors"].values())
    check("8 four concurrent records all survive alongside the seed", total == 5,
          f"expected 5 entries, got {total} — a lost update erases someone's history")
    check("8 every writer got an entry", len(data["contributors"]) == 4,
          str(sorted(data["contributors"])))


# --- 9: unknown user is empty, not a crash ---------------------------------------------------

def test_unknown_user() -> None:
    vault = new_vault()
    run(vault, "record", "--user-id", USER, "--path", "notes/a.md", "--type", "added")
    result = run(vault, "query", "--user-id", "nobody@example.com")
    check("9 unknown user_id exits 1", result.returncode == 1, f"exit {result.returncode}")
    check("9 unknown user_id does not traceback", "Traceback" not in result.stderr,
          result.stderr[:200])


# --- 10: paths outside the vault are rejected ------------------------------------------------

def test_path_outside_vault() -> None:
    vault = new_vault()
    result = run(vault, "record", "--user-id", USER, "--path", "../outside.md", "--type", "added")
    check("10 a path escaping the vault is rejected", result.returncode != 0,
          f"exit {result.returncode}")
    result2 = run(vault, "record", "--user-id", USER, "--path", "/etc/passwd", "--type", "added")
    check("10 an absolute path outside the vault is rejected", result2.returncode != 0,
          f"exit {result2.returncode}")


def main() -> int:
    if not TOOL.exists():
        print(f"contributors.py not found at {TOOL}", file=sys.stderr)
        return 2
    print("contributors.py")
    for fn in (test_record_creates_file, test_repeats_are_kept, test_multiple_paths,
               test_recent_touch_hit, test_recent_touch_miss, test_query_output_is_bounded,
               test_corrupt_json_is_backed_up, test_concurrent_records, test_unknown_user,
               test_path_outside_vault):
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
