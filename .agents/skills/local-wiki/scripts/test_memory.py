#!/usr/bin/env python3
"""Tests for memory.py — the agent's episodic and procedural memory.

    python3 test_memory.py

What these lock down, and why each one is here rather than being obvious:

  the gate is arithmetic   Promotion is automatic, so the thresholds ARE the safety mechanism.
                           A rule that reaches `validated` one episode early starts changing where
                           notes go, silently, in every vault the fix ships to.
  a correction demotes     Immediately, and out of the loaded set. A rule the user just corrected
                           must not decide the next placement while it waits for a review.
  stats never opens the log  Asserted by deleting the log: `stats` has to keep working. The rule
                           "never read the unbounded file" is unenforceable by prose alone, so it
                           is enforced by making the tool structurally unable to need it.
  slots evict              Nine validated rules in a scope must leave eight loaded, or the thing
                           the agent reads before every decision grows without a ceiling.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEMORY = HERE / "memory.py"

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


def make_vault() -> Path:
    root = Path(tempfile.mkdtemp(prefix="memory-test-"))
    (root / ".wiki").mkdir()
    return root


def run(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(MEMORY), "--vault", str(vault), *args],
                          capture_output=True, text=True)


def run_json(vault: Path, *args: str):
    result = run(vault, *args, "--json")
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise AssertionError(f"not JSON ({exc}): {result.stdout[:200]} {result.stderr[:200]}")


RULE = """---
id: {id}
scope: {scope}
status: candidate
confidence: 0.0
evidence: []
negative_examples: []
created_at: 2026-08-15
last_validated: 2026-08-15
superseded_by: null
---
When a note describes a reusable mechanism rather than one project's implementation, prefer the
conceptual domain folder over the project folder.
"""


def write_rule(vault: Path, rule_id: str, scope: str = "placement", **fields: str) -> Path:
    directory = vault / ".wiki" / "agent-memory" / "rules"
    directory.mkdir(parents=True, exist_ok=True)
    text = RULE.format(id=rule_id, scope=scope)
    for key, value in fields.items():
        text = text.replace(f"{key}: candidate", f"{key}: {value}").replace(
            f"{key}: 0.0", f"{key}: {value}")
    path = directory / f"{rule_id}.md"
    path.write_text(text, encoding="utf-8")
    return path


def episodes(vault: Path, count: int, rule: str = "RULE-001") -> list[str]:
    ids = []
    for i in range(count):
        result = run(vault, "record", "--mode", "update", "--decision", "place",
                     "--target", f"domain/n{i}.md", "--applied-rule", rule, "--quiet")
        ids.append(result.stdout.strip())
    return ids


def read_rule(vault: Path, rule_id: str) -> str:
    for candidate in ((vault / ".wiki/agent-memory/rules" / f"{rule_id}.md"),
                      (vault / ".wiki/agent-memory/rules/deprecated" / f"{rule_id}.md")):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    return ""


# --- recording -------------------------------------------------------------------------------

def test_record_and_rollup_agree() -> None:
    vault = make_vault()
    ids = episodes(vault, 3)
    check("60 ids are sequential", ids == ["EP-1", "EP-2", "EP-3"], str(ids))
    stats = run_json(vault, "stats")
    check("60 the rollup counted them", stats["episodes"] == 3, str(stats))
    check("60 they are open until closed", stats["by_outcome"].get("unknown") == 3, str(stats))
    log = (vault / ".wiki/agent-memory/episodes.jsonl").read_text(encoding="utf-8")
    check("60 one line per episode", len(log.strip().splitlines()) == 3, log[:200])


def test_close_appends_and_never_rewrites() -> None:
    vault = make_vault()
    episodes(vault, 1)
    before = (vault / ".wiki/agent-memory/episodes.jsonl").read_text(encoding="utf-8")
    run(vault, "close", "--id", "EP-1", "--outcome", "corrected", "--correction", "projects/x.md")
    after = (vault / ".wiki/agent-memory/episodes.jsonl").read_text(encoding="utf-8")
    check("61 the original line is untouched", after.startswith(before), after[:200])
    check("61 closing appended a second record", len(after.strip().splitlines()) == 2, after[:200])
    folded = run_json(vault, "query")
    check("61 the two records fold into one episode", folded["count"] == 1, str(folded))
    check("61 the outcome is the closed one",
          folded["results"][0]["outcome"] == "corrected", str(folded["results"]))
    check("61 the correction is kept",
          folded["results"][0]["correction"] == "projects/x.md", str(folded["results"]))


def test_stats_never_opens_the_log() -> None:
    """The contract, asserted the only way prose cannot fake: delete the log and demand an answer."""
    vault = make_vault()
    episodes(vault, 4)
    run(vault, "close", "--id", "EP-1", "--outcome", "confirmed")
    (vault / ".wiki/agent-memory/episodes.jsonl").unlink()
    result = run(vault, "stats", "--json")
    check("62 stats works with no log at all", result.returncode == 0, result.stderr[:200])
    stats = json.loads(result.stdout)
    check("62 stats still knows the totals", stats["episodes"] == 4, str(stats))
    check("62 stats still knows the outcomes", stats["by_outcome"].get("confirmed") == 1,
          str(stats))


# --- the gate --------------------------------------------------------------------------------

def test_rule_is_not_promoted_early() -> None:
    vault = make_vault()
    write_rule(vault, "RULE-001")
    ids = episodes(vault, 4)
    for eid in ids:
        run(vault, "close", "--id", eid, "--outcome", "confirmed")
    payload = run_json(vault, "promote")
    check("63 four supports is one short of validated",
          all(c["to"] != "validated" for c in payload["changed"]), str(payload["changed"]))
    loaded = run(vault, "rules", "--scope", "placement")
    check("63 nothing is loaded yet", loaded.returncode == 1, loaded.stdout[:200])


def test_rule_auto_promotes_at_the_threshold() -> None:
    vault = make_vault()
    write_rule(vault, "RULE-001")
    for eid in episodes(vault, 5):
        run(vault, "close", "--id", eid, "--outcome", "confirmed")
    payload = run_json(vault, "promote")
    changed = [c for c in payload["changed"] if c["id"] == "RULE-001"]
    check("64 five supports promotes to validated",
          changed and changed[0]["to"] == "validated", str(payload["changed"]))
    check("64 the change is reportable — it names the rule and the reason",
          changed and changed[0]["why"] and changed[0]["text"], str(changed))
    loaded = run_json(vault, "rules", "--scope", "placement")
    check("64 the rule is now loaded for its scope",
          [r["id"] for r in loaded] == ["RULE-001"], str(loaded))
    check("64 confidence is computed, not guessed",
          "confidence: 1.0" in read_rule(vault, "RULE-001"), read_rule(vault, "RULE-001")[:200])


def test_a_correction_demotes_immediately() -> None:
    vault = make_vault()
    write_rule(vault, "RULE-001")
    for eid in episodes(vault, 5):
        run(vault, "close", "--id", eid, "--outcome", "confirmed")
    run_json(vault, "promote")
    run(vault, "record", "--mode", "update", "--decision", "place", "--target", "domain/n9.md",
        "--applied-rule", "RULE-001", "--quiet")
    run(vault, "close", "--id", "EP-6", "--outcome", "corrected", "--correction", "projects/n9.md")
    payload = run_json(vault, "promote")
    changed = [c for c in payload["changed"] if c["id"] == "RULE-001"]
    check("65 a correction demotes the rule", changed and changed[0]["to"] == "supported",
          str(payload["changed"]))
    loaded = run(vault, "rules", "--scope", "placement")
    check("65 the demoted rule stops influencing decisions", loaded.returncode == 1,
          loaded.stdout[:200])
    check("65 its evidence is not destroyed", "RULE-001" in read_rule(vault, "RULE-001"),
          "rule file lost")


def test_contradictions_outweighing_support_deprecate() -> None:
    vault = make_vault()
    write_rule(vault, "RULE-001")
    for eid in episodes(vault, 2):
        run(vault, "close", "--id", eid, "--outcome", "corrected")
    payload = run_json(vault, "promote")
    changed = [c for c in payload["changed"] if c["id"] == "RULE-001"]
    check("66 a rule that is mostly wrong is deprecated",
          changed and changed[0]["to"] == "deprecated", str(payload["changed"]))
    check("66 deprecated rules move aside, they are not deleted",
          (vault / ".wiki/agent-memory/rules/deprecated/RULE-001.md").exists(),
          "deprecated rule missing")


# --- budgets ---------------------------------------------------------------------------------

def test_rule_slots_evict_the_weakest() -> None:
    vault = make_vault()
    for i in range(1, 10):
        write_rule(vault, f"RULE-{i:03d}", status="validated",
                   confidence=str(round(0.5 + i / 100, 2)))
    run(vault, "promote")
    index = (vault / ".wiki/agent-memory/rules/index.md").read_text(encoding="utf-8")
    listed = [line for line in index.splitlines() if line.startswith("- **RULE-")]
    check("67 the index is capped at the slot count", len(listed) == 8, f"{len(listed)} listed")
    check("67 the weakest rule lost its slot", "RULE-001" not in index, index[:400])
    check("67 the strongest rule kept its slot", "RULE-009" in index, index[:400])
    loaded = run_json(vault, "rules")
    check("67 the evicted rule is no longer loaded",
          "RULE-001" not in [r["id"] for r in loaded], str(loaded))


def test_rules_are_loaded_by_scope() -> None:
    vault = make_vault()
    write_rule(vault, "RULE-001", scope="placement", status="validated", confidence="0.9")
    write_rule(vault, "RULE-002", scope="linking", status="validated", confidence="0.9")
    run(vault, "promote")
    placement = run_json(vault, "rules", "--scope", "placement")
    check("68 one scope loads only its own rules",
          [r["id"] for r in placement] == ["RULE-001"], str(placement))
    index = (vault / ".wiki/agent-memory/rules/index.md").read_text(encoding="utf-8")
    check("68 the index groups by scope",
          "## placement" in index and "## linking" in index, index[:300])


def test_query_is_bounded() -> None:
    vault = make_vault()
    episodes(vault, 30)
    payload = run_json(vault, "query", "--limit", "5")
    check("69 the limit caps what comes back", len(payload["results"]) == 5, str(payload["count"]))
    check("69 the real count is still reported", payload["count"] == 30, str(payload["count"]))
    check("69 the scan itself is bounded", payload["scanned_lines"] > 0, str(payload))


def test_rotation_archives_closed_quarters() -> None:
    vault = make_vault()
    episodes(vault, 3)
    log = vault / ".wiki/agent-memory/episodes.jsonl"
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    rows[0]["ts"] = "2024-02-01T00:00:00Z"
    rows[1]["ts"] = "2024-05-01T00:00:00Z"
    log.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    result = run(vault, "rotate", "--force")
    check("70 rotation reports what moved", result.returncode == 0, result.stdout[:200])
    remaining = log.read_text(encoding="utf-8").strip().splitlines()
    check("70 the current quarter stays live", len(remaining) == 1, str(remaining)[:200])
    archive = vault / ".wiki/agent-memory/archive"
    files = sorted(p.name for p in archive.glob("episodes-*.jsonl"))
    check("70 one file per closed quarter",
          files == ["episodes-2024-Q1.jsonl", "episodes-2024-Q2.jsonl"], str(files))
    check("70 rotation does not touch the counters",
          run_json(vault, "stats")["episodes"] == 3, "counters changed")


def test_no_memory_yet_is_a_normal_state() -> None:
    vault = make_vault()
    for args in (("stats",), ("rules",), ("query",), ("promote",)):
        result = run(vault, *args)
        check(f"71 `{args[0]}` on an empty vault does not crash",
              result.returncode in (0, 1), f"exit {result.returncode}: {result.stderr[:200]}")


def main() -> int:
    if not MEMORY.exists():
        print(f"memory.py not found at {MEMORY}", file=sys.stderr)
        return 2
    print("memory.py")
    for fn in (test_record_and_rollup_agree, test_close_appends_and_never_rewrites,
               test_stats_never_opens_the_log, test_rule_is_not_promoted_early,
               test_rule_auto_promotes_at_the_threshold, test_a_correction_demotes_immediately,
               test_contradictions_outweighing_support_deprecate,
               test_rule_slots_evict_the_weakest, test_rules_are_loaded_by_scope,
               test_query_is_bounded, test_rotation_archives_closed_quarters,
               test_no_memory_yet_is_a_normal_state):
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
