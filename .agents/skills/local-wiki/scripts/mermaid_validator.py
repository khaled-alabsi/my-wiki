#!/usr/bin/env python3
"""Find every Mermaid diagram under a directory and report the broken ones.

Walks a tree, collects diagrams from two sources - whole `*.mmd` files and fenced ```mermaid blocks
inside Markdown - and checks each one against the parse failures that actually break rendering.
Reports the file, the line range, the size, and what is wrong.

    python3 validator.py <path>...              # human-readable report
    python3 validator.py <path> --json          # machine-readable
    python3 validator.py <path> --quiet         # only the failures
    python3 validator.py <path> --list-files    # just the paths, for piping

Exit codes: 0 clean, 1 at least one invalid diagram, 2 bad usage / nothing found.

Stdlib only, no Mermaid runtime. Every check below corresponds to a real observed break, not a
style preference - the rules and their histories are in `task.md`. It is deliberately conservative:
a diagram it passes may still fail to render for a reason nothing here models, so a clean result
means "none of the known breaks", never "guaranteed valid".
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field

# --- what counts as a diagram ------------------------------------------------------------------

MD_EXT = {".md", ".markdown", ".mdx"}
MMD_EXT = {".mmd", ".mermaid"}
SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".rag", ".wiki",
    ".agents", ".agent", "dist", "build", "site", ".next", ".cache", ".idea", ".vscode",
}
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*mermaid\s*$", re.I)
CLOSING = re.compile(r"^\s*(`{3,}|~{3,})\s*$")

KNOWN_TYPES = (
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
    "stateDiagram-v2", "erDiagram", "journey", "gantt", "pie", "gitGraph",
    "mindmap", "timeline", "quadrantChart", "requirementDiagram", "C4Context",
    "sankey-beta", "xychart-beta", "block-beta",
)

# --- parsing helpers ---------------------------------------------------------------------------

QUOTED = re.compile(r'"[^"]*"')
DELIMITERS = (("[", "]"), ("{", "}"), ("(", ")"))
DIAMOND_OPEN = re.compile(r"(?<![A-Za-z0-9_])\{")
SQUARE_LABEL = re.compile(r"\[([^\[\]]*)\]")
NODE_ID = re.compile(r"(?<![\w-])([A-Za-z][\w-]*)\s*[\[\({]")
DOT_ARROW = re.compile(r"(?<![-<>=|.])->(?!>)")
DOT_ATTRS = re.compile(r"\b(node|edge|graph)\s*\[")
ANGLE_IN_LABEL = re.compile(r"[<>]")

MAX_NODES = 15


@dataclass
class Diagram:
    path: str
    start_line: int          # 1-indexed line of the opening fence, or 1 for a .mmd file
    body: list[str]
    source: str              # "mmd" or "md-fence"

    @property
    def line_count(self) -> int:
        return len(self.body)

    @property
    def end_line(self) -> int:
        return self.start_line + len(self.body) + (1 if self.source == "md-fence" else 0)

    @property
    def kind(self) -> str:
        for line in self.body:
            stripped = line.strip()
            if stripped and not stripped.startswith("%%"):
                return stripped.split()[0] if stripped.split() else ""
        return ""


@dataclass
class Finding:
    rule: str
    message: str
    line: int | None = None


@dataclass
class Result:
    diagram: Diagram
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings


# --- collection --------------------------------------------------------------------------------

def read_lines(path: str) -> list[str] | None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def diagrams_in_markdown(path: str, lines: list[str]) -> list[Diagram]:
    """Every ```mermaid fence, with the real line number of its opening fence."""
    found, i = [], 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            i += 1
            continue
        marker = m.group(2)[0]
        body, j = [], i + 1
        while j < len(lines):
            close = CLOSING.match(lines[j])
            if close and close.group(1)[0] == marker:
                break
            body.append(lines[j])
            j += 1
        found.append(Diagram(path, i + 1, body, "md-fence"))
        i = j + 1
    return found


def collect(roots: list[str]) -> list[Diagram]:
    out: list[Diagram] = []
    for root in roots:
        if os.path.isfile(root):
            files = [root]
        else:
            files = []
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
                files += [os.path.join(dirpath, n) for n in sorted(filenames)]
        for path in files:
            ext = os.path.splitext(path)[1].lower()
            if ext in MMD_EXT:
                lines = read_lines(path)
                if lines is not None:
                    out.append(Diagram(path, 1, lines, "mmd"))
            elif ext in MD_EXT:
                lines = read_lines(path)
                if lines is not None:
                    out.extend(diagrams_in_markdown(path, lines))
    return out


# --- the checks ---------------------------------------------------------------------------------

def _real_lines(d: Diagram):
    """(absolute line number, text) for each non-blank, non-comment line."""
    offset = d.start_line + (1 if d.source == "md-fence" else 0)
    for n, line in enumerate(d.body):
        stripped = line.strip()
        if stripped and not stripped.startswith("%%"):
            yield offset + n, line


def check_empty(d: Diagram, add) -> None:
    if not any(line.strip() for line in d.body):
        add("EMPTY", "the mermaid block is empty")


def check_type(d: Diagram, add) -> None:
    kind = d.kind
    if not kind:
        return
    if not any(kind.startswith(k) for k in KNOWN_TYPES):
        add("TYPE", f"unknown diagram type {kind!r}; the first statement names the diagram kind "
                    f"(flowchart, sequenceDiagram, ...)")


def check_dot_syntax(d: Diagram, add) -> None:
    """Graphviz/DOT pasted into a mermaid fence. Renders as nothing.

    Flowcharts only. `erDiagram` attribute blocks, `classDiagram` member blocks and
    `stateDiagram-v2` composite states all legitimately close on a bare `}` line, so running the
    brace rule against them flags valid syntax and tells the author to delete it. A real DOT paste
    (`digraph G {`) is still caught: its declaration is not a mermaid kind, so TYPE fires instead.
    """
    if not d.kind.startswith(("flowchart", "graph")):
        return
    for n, line in _real_lines(d):
        stripped = line.strip()
        if re.match(r"^(flowchart|graph)\b.*\{\s*$", stripped):
            add("DOT", "DOT-style opening brace after the diagram declaration; mermaid has no "
                       "graph body braces", n)
        if DOT_ATTRS.search(stripped):
            add("DOT", f"DOT attribute block {stripped!r}; mermaid encodes shape per node", n)
        if stripped == "}":
            add("DOT", "a bare closing brace; mermaid diagrams have no graph-level braces", n)


def check_arrows(d: Diagram, add) -> None:
    if not d.kind.startswith(("flowchart", "graph")):
        return
    for n, line in _real_lines(d):
        if DOT_ARROW.search(QUOTED.sub("", line)):
            add("ARROW", "`->` is DOT syntax; mermaid flowcharts use `-->`", n)


def check_balance(d: Diagram, add) -> None:
    """Delimiters must close on the line that opened them, ignoring quoted spans."""
    if not d.kind.startswith(("flowchart", "graph")):
        return
    for n, line in _real_lines(d):
        if line.strip().startswith(("flowchart", "graph")):
            continue
        bare = QUOTED.sub("", line)
        for open_, close in DELIMITERS:
            if bare.count(open_) != bare.count(close):
                add("BALANCE",
                    f"line does not close what it opens ({open_}/{close}): {line.strip()!r} - a "
                    f"node label is one source line, and its closing delimiter matches its opening "
                    f"shape", n)
                break


def check_braces(d: Diagram, add) -> None:
    """An unquoted `{` opens a diamond, so `{id}` inside a label kills the diagram."""
    if not d.kind.startswith(("flowchart", "graph")):
        return
    for n, line in _real_lines(d):
        if line.strip().startswith(("flowchart", "graph")):
            continue
        if DIAMOND_OPEN.search(QUOTED.sub("", line)):
            add("BRACE",
                f"unquoted brace in a label: {line.strip()!r} - `{{` opens a diamond, so a path "
                f'parameter must be quoted: A(["GET /v1/{{id}}/x"]). Quote it; do not delete the '
                f"braces", n)


def check_parens(d: Diagram, add) -> None:
    """`(` is a shape token everywhere in an unquoted label, even balanced."""
    if not d.kind.startswith(("flowchart", "graph")):
        return
    for n, line in _real_lines(d):
        if line.strip().startswith(("flowchart", "graph")):
            continue
        for label in SQUARE_LABEL.findall(line):
            body = label.strip()
            if body.startswith('"') and body.endswith('"'):
                continue
            if body.startswith("(") and body.endswith(")"):   # cylinder id[(text)]
                continue
            if "(" in body or ")" in body:
                add("PAREN",
                    f"unquoted parentheses in a square-bracket label: {line.strip()!r} - quote the "
                    f'whole label: E["fetchX()"]', n)
                break


def check_angles(d: Diagram, add) -> None:
    if not d.kind.startswith(("flowchart", "graph")):
        return
    for n, line in _real_lines(d):
        for label in SQUARE_LABEL.findall(line):
            body = label.strip()
            if body.startswith('"') and body.endswith('"'):
                continue
            if ANGLE_IN_LABEL.search(body) and "<br/>" not in body and "<br>" not in body:
                add("ANGLE",
                    f"raw angle bracket in an unquoted label: {line.strip()!r} - quote it; `<br/>` "
                    f"is the only markup allowed", n)
                break


def check_sequence(d: Diagram, add) -> None:
    if not d.kind.startswith("sequenceDiagram"):
        return
    for n, line in _real_lines(d):
        if re.search(r"\bendend\b", line):
            add("ENDEND",
                "concatenated `endend`; each fragment terminator goes on its own line", n)
    opens = sum(1 for _, l in _real_lines(d)
                if re.match(r"^\s*(alt|opt|loop|par|critical|rect)\b", l))
    ends = sum(1 for _, l in _real_lines(d) if re.match(r"^\s*end\s*$", l))
    if opens > ends:
        add("FRAGMENT", f"{opens} fragment(s) opened, {ends} `end` line(s) - each alt/opt/loop "
                        f"closes with its own `end`")


def check_size(d: Diagram, add) -> None:
    if not d.kind.startswith(("flowchart", "graph")):
        return
    ids = set()
    for _, line in _real_lines(d):
        ids.update(NODE_ID.findall(QUOTED.sub('""', line)))
    if len(ids) > MAX_NODES:
        add("SIZE", f"{len(ids)} nodes; past about {MAX_NODES} a diagram stops being readable - "
                    f"split it rather than growing one overloaded picture")


CHECKS = (check_empty, check_type, check_dot_syntax, check_arrows, check_balance,
          check_braces, check_parens, check_angles, check_sequence, check_size)

# rules that are advisory rather than a parse failure
WARN_ONLY = {"SIZE"}


def validate(d: Diagram) -> Result:
    result = Result(d)

    def add(rule: str, message: str, line: int | None = None) -> None:
        result.findings.append(Finding(rule, message, line))

    for check in CHECKS:
        check(d, add)
    return result


# --- reporting ----------------------------------------------------------------------------------

def location(d: Diagram) -> str:
    if d.source == "mmd":
        return d.path
    return f"{d.path}:{d.start_line}"


def report_text(results: list[Result], quiet: bool, warnings_are_failures: bool) -> None:
    bad = [r for r in results
           if any(f.rule not in WARN_ONLY or warnings_are_failures for f in r.findings)]
    warned = [r for r in results if r not in bad and r.findings]

    if not quiet:
        print(f"{len(results)} diagram(s) in "
              f"{len({r.diagram.path for r in results})} file(s)\n")

    for r in bad:
        d = r.diagram
        print(f"{location(d)}  [{d.kind or 'unknown'}, {d.line_count} lines]")
        for f in r.findings:
            where = f"line {f.line}: " if f.line else ""
            print(f"    {f.rule:9} {where}{f.message}")
        print()

    if warned and not quiet:
        for r in warned:
            d = r.diagram
            print(f"{location(d)}  [{d.kind or 'unknown'}, {d.line_count} lines]  (advisory)")
            for f in r.findings:
                print(f"    {f.rule:9} {f.message}")
        print()

    ok = len(results) - len(bad) - len(warned)
    print(f"{ok} valid, {len(bad)} invalid" + (f", {len(warned)} advisory" if warned else ""))


def report_json(results: list[Result], warnings_are_failures: bool) -> None:
    payload = []
    for r in results:
        failing = [f for f in r.findings if f.rule not in WARN_ONLY or warnings_are_failures]
        if not r.findings:
            continue
        payload.append({
            "file": r.diagram.path,
            "start_line": r.diagram.start_line,
            "end_line": r.diagram.end_line,
            "lines": r.diagram.line_count,
            "type": r.diagram.kind,
            "source": r.diagram.source,
            "valid": not failing,
            "findings": [{"rule": f.rule, "line": f.line, "message": f.message}
                         for f in r.findings],
        })
    print(json.dumps({
        "diagrams": len(results),
        "files": len({r.diagram.path for r in results}),
        "invalid": sum(1 for p in payload if not p["valid"]),
        "results": payload,
    }, indent=2))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Find and validate Mermaid diagrams in .mmd files and markdown fences.")
    ap.add_argument("paths", nargs="+", help="directories or files to scan")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="only print failures")
    ap.add_argument("--list-files", action="store_true",
                    help="print only the paths of files containing an invalid diagram")
    ap.add_argument("--strict", action="store_true",
                    help="treat advisory findings (size) as failures too")
    args = ap.parse_args(argv)

    for p in args.paths:
        if not os.path.exists(p):
            print(f"error: no such path: {p}", file=sys.stderr)
            return 2

    diagrams = collect(args.paths)
    if not diagrams:
        print("no mermaid diagrams found", file=sys.stderr)
        return 2

    results = [validate(d) for d in diagrams]
    failing = [r for r in results
               if any(f.rule not in WARN_ONLY or args.strict for f in r.findings)]

    if args.list_files:
        for path in sorted({r.diagram.path for r in failing}):
            print(path)
    elif args.json:
        report_json(results, args.strict)
    else:
        report_text(results, args.quiet, args.strict)

    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
