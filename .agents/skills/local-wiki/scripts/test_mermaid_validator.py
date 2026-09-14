#!/usr/bin/env python3
"""Tests for mermaid_validator.py. Stdlib only, no framework — run it directly.

    python3 test_mermaid_validator.py

Every rule here corresponds to a diagram that actually failed to render, so each test is a
regression guard, not a style assertion. Two matter most and are the most likely to be "simplified"
away later:

  BRACE   an unquoted `{` in a label opens a diamond. Every REST path template has one, so this is
          the break this class of documentation produces almost by default.
  PAREN   `(` is a shape token everywhere in an unquoted label. Balanced pairs still break the
          parser, so a naive count-the-delimiters check passes the broken diagram.

The no-false-positive tests are as load-bearing as the rest: a checker that flags valid diagrams
gets ignored, and an ignored checker is worse than none.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "mermaid_validator.py"

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


def run(files: dict[str, str], *args: str) -> dict:
    root = Path(tempfile.mkdtemp(prefix="mermaid-test-"))
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(TOOL), str(root), "--json", *args],
        capture_output=True, text=True,
    )
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise AssertionError(f"non-JSON output (exit {result.returncode}): "
                             f"{result.stdout[:200]} {result.stderr[:300]}")


def rules_for(payload: dict, name_fragment: str = "") -> set[str]:
    out = set()
    for r in payload["results"]:
        if name_fragment and name_fragment not in r["file"]:
            continue
        out.update(f["rule"] for f in r["findings"])
    return out


def fence(body: str) -> str:
    return "# Doc\n\nIntro.\n\n```mermaid\n" + body.strip() + "\n```\n"


# --- the valid cases must stay silent --------------------------------------------------------

def test_valid_diagrams_produce_nothing() -> None:
    payload = run({"ok.md": fence("""
flowchart TD
    A(["GET /v1/{id}/x"]) --> B[Validate]
    B --> C{Allowed?}
    C -->|yes| D[(store)]
    C -->|no| E["reject()"]
""")})
    check("1 a correct flowchart yields no findings", payload["invalid"] == 0 and not payload["results"],
          str(payload["results"]))

    payload = run({"seq.md": fence("""
sequenceDiagram
    A->>B: request
    alt accepted
        B->>A: 200
    else rejected
        B->>A: 422
    end
""")})
    check("1 a correct sequenceDiagram yields no findings", payload["invalid"] == 0,
          str(payload["results"]))

    # a cylinder legitimately wraps its whole label in parens - must not trip PAREN
    payload = run({"cyl.md": fence("flowchart LR\n    A[(accounts table)] --> B[Read]")})
    check("1 a cylinder node is not a paren error", "PAREN" not in rules_for(payload),
          str(payload["results"]))


# --- each rule fires on its own break ---------------------------------------------------------

def test_brace() -> None:
    payload = run({"b.md": fence("flowchart TD\n    A([GET /v1/{id}/x]) --> B[Store]")})
    check("2 unquoted brace in a label is caught", "BRACE" in rules_for(payload),
          str(rules_for(payload)))


def test_paren_balanced_still_fails() -> None:
    payload = run({"p.md": fence("flowchart TD\n    E[fetchX() / fetchY()] --> F[Done]")})
    check("3 balanced parens in a square label are still caught", "PAREN" in rules_for(payload),
          "a count-based check passes this; the parser does not")
    check("3 balanced parens do not trip BALANCE", "BALANCE" not in rules_for(payload),
          "they are balanced - PAREN is the rule that must catch it")


def test_unbalanced_and_mismatched() -> None:
    payload = run({"u.md": fence("flowchart TD\n    A[Start] --> B[Wrapped label\n    C[End]")})
    check("4 a label wrapped onto a second line is caught", "BALANCE" in rules_for(payload))
    payload = run({"m.md": fence('flowchart TD\n    D{"choice"] --> E[Done]')})
    check("4 a mismatched closing delimiter is caught", "BALANCE" in rules_for(payload))


def test_dot_syntax() -> None:
    payload = run({"d.md": fence("flowchart LR {\n    node [shape=box]\n    A -> B\n}")})
    rules = rules_for(payload)
    check("5 DOT graph braces are caught", "DOT" in rules, str(rules))
    check("5 DOT arrows are caught", "ARROW" in rules, str(rules))


def test_brace_bodied_diagram_kinds_are_not_dot() -> None:
    """A bare `}` is DOT only in a flowchart. Three kinds use brace bodies legitimately.

    The DOT rule is a flowchart rule: `digraph { ... }` pasted into a mermaid fence renders as
    nothing. But erDiagram attribute blocks, classDiagram member blocks and stateDiagram-v2
    composite states all close on a bare `}` line, and flagging those tells the author to delete
    valid syntax. Every other flowchart-only rule guards on `d.kind`; this one must too.
    """
    payload = run({"er.md": fence("""
erDiagram
    PERSON ||--o{ AGREEMENT_ROLE : has

    PERSON {
        string partyId
    }

    AGREEMENT_ROLE {
        string customerId
        string role
    }
""")})
    check("5b erDiagram attribute blocks are not DOT", "DOT" not in rules_for(payload),
          str(payload["results"]))
    check("5b a valid erDiagram is valid", payload["invalid"] == 0, str(payload["results"]))

    payload = run({"cls.md": fence("""
classDiagram
    class CustomerAgreement {
        +String customerId
        +List~AgreementRole~ agreementRoles
    }
""")})
    check("5b classDiagram member blocks are not DOT", "DOT" not in rules_for(payload),
          str(payload["results"]))
    check("5b a valid classDiagram is valid", payload["invalid"] == 0, str(payload["results"]))

    payload = run({"st.md": fence("""
stateDiagram-v2
    [*] --> Advising
    state Advising {
        [*] --> Profiling
        Profiling --> Recommending
    }
    Advising --> [*]
""")})
    check("5b stateDiagram-v2 composite states are not DOT", "DOT" not in rules_for(payload),
          str(payload["results"]))
    check("5b a valid stateDiagram-v2 is valid", payload["invalid"] == 0, str(payload["results"]))

    # the guard must not blind the rule where it belongs: a flowchart still gets caught
    payload = run({"f.md": fence("flowchart LR {\n    A -> B\n}")})
    check("5b the DOT rule still fires on a flowchart", "DOT" in rules_for(payload),
          str(payload["results"]))


def test_sequence_fragments() -> None:
    payload = run({"s.md": fence("sequenceDiagram\n    A->>B: hi\n    alt yes\n        B->>A: ok\n    endend")})
    rules = rules_for(payload)
    check("6 concatenated endend is caught", "ENDEND" in rules, str(rules))
    check("6 an unclosed fragment is caught", "FRAGMENT" in rules, str(rules))


def test_angle_brackets() -> None:
    payload = run({"a.md": fence("flowchart TD\n    A[a <b> c] --> B[Done]")})
    check("7 a raw angle bracket in a label is caught", "ANGLE" in rules_for(payload))
    payload = run({"br.md": fence("flowchart TD\n    A[line one<br/>line two] --> B[Done]")})
    check("7 <br/> is allowed", "ANGLE" not in rules_for(payload), str(payload["results"]))


def test_empty_and_type() -> None:
    payload = run({"e.md": "# Doc\n\n```mermaid\n```\n"})
    check("8 an empty fence is caught", "EMPTY" in rules_for(payload))
    payload = run({"t.md": fence("flowchrt TD\n    A --> B")})
    check("8 an unknown diagram type is caught", "TYPE" in rules_for(payload))


# --- discovery and reporting ------------------------------------------------------------------

def test_mmd_files_and_line_numbers() -> None:
    payload = run({
        "sub/broken.mmd": "flowchart TD\n    A[Bad (x)] --> B[C\n",
        "doc.md": "# Doc\n\nfiller\nfiller\n\n```mermaid\nflowchart TD\n    A([GET /{id}]) --> B[x]\n```\n",
    })
    by_file = {Path(r["file"]).name: r for r in payload["results"]}
    check("9 a .mmd file is picked up", "broken.mmd" in by_file, str(list(by_file)))
    check("9 a fence inside markdown is picked up", "doc.md" in by_file, str(list(by_file)))
    if "doc.md" in by_file:
        r = by_file["doc.md"]
        check("9 the fence's own line number is reported", r["start_line"] == 6,
              f"start_line={r['start_line']}, expected 6")
        brace = [f for f in r["findings"] if f["rule"] == "BRACE"]
        check("9 the finding's line is absolute, not an offset into the block",
              brace and brace[0]["line"] == 8, str(brace))
    if "broken.mmd" in by_file:
        check("9 a .mmd diagram reports its line count",
              by_file["broken.mmd"]["lines"] == 2, str(by_file["broken.mmd"]["lines"]))


def test_size_is_advisory_only() -> None:
    body = "flowchart TD\n" + "\n".join(f"    N{i}[Step {i}] --> N{i+1}[Step {i+1}]"
                                        for i in range(20))
    payload = run({"big.md": fence(body)})
    check("10 an oversized diagram is reported", "SIZE" in rules_for(payload))
    check("10 size alone does not make it invalid",
          payload["invalid"] == 0, "SIZE is advisory; only --strict promotes it")
    strict = run({"big.md": fence(body)}, "--strict")
    check("10 --strict promotes size to a failure", strict["invalid"] == 1, str(strict["invalid"]))


def test_skips_noise_directories() -> None:
    payload = run({
        "node_modules/x.md": fence("flowchart LR {\n    A -> B\n}"),
        "real.md": fence("flowchart TD\n    A[ok] --> B[fine]"),
    })
    files = {Path(r["file"]).name for r in payload["results"]}
    check("11 node_modules is skipped", "x.md" not in files, str(files))


def main() -> int:
    if not TOOL.exists():
        print(f"mermaid_validator.py not found at {TOOL}", file=sys.stderr)
        return 2
    print("mermaid_validator.py")
    for fn in (test_valid_diagrams_produce_nothing, test_brace, test_paren_balanced_still_fails,
               test_unbalanced_and_mismatched, test_dot_syntax,
               test_brace_bodied_diagram_kinds_are_not_dot, test_sequence_fragments,
               test_angle_brackets, test_empty_and_type, test_mmd_files_and_line_numbers,
               test_size_is_advisory_only, test_skips_noise_directories):
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
