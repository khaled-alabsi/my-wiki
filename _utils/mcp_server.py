#!/usr/bin/env python3
"""Lightweight coding MCP server for LM Studio.

Single-file stdio MCP server built on the official Python MCP SDK
(`mcp`, via `FastMCP`). Provides the small set of tools a coding agent
actually uses day to day: file I/O, search (ripgrep-backed with a
pure-Python fallback), basic code navigation, git, an allowlisted
terminal, and a couple of filesystem utilities.

Usage:
    python3 mcp_server.py [--tools=read-only|rw] [ALLOWED_ROOT ...]

If no allowed roots are given, the server's current working directory
is used. All file/search/git/terminal operations are restricted to
these roots.

--tools controls which tools are registered at all:
    read-only (default) - browsing, reading, search, git-read tools only.
    rw                   - adds write_file, replace_in_file, run_command,
                            the only tools that can mutate anything.
Can also be set via the MCP_TOOL_MODE env var (the --tools= flag wins).
"""

from __future__ import annotations

import fnmatch
import functools
import logging
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# --------------------------------------------------------------------------
# Logging (file only — stdout is reserved for the MCP JSON-RPC stream)
# --------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_PATH = SCRIPT_DIR / "mcp_server.log"

logger = logging.getLogger("dev-tools")
logger.setLevel(logging.INFO)
logger.propagate = False
_log_handler = RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
_log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_log_handler)


def _summarize(value: Any, limit: int = 300) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "...(truncated)"


def _logged(fn):
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info("CALL %s args=%s kwargs=%s", fn.__name__, _summarize(args), _summarize(kwargs))
        try:
            result = fn(*args, **kwargs)
        except Exception:
            logger.exception("EXCEPTION in %s", fn.__name__)
            raise
        logger.info("RESULT %s -> %s", fn.__name__, _summarize(result))
        return result
    return wrapper


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Directories whose contents are never listed / searched / read.
IGNORED_DIR_NAMES = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".cache", ".pytest_cache", ".mypy_cache",
    ".idea", ".vscode", "target", ".obsidian",
}

# Commands allowed to run via run_command. Override / extend with the
# MCP_ALLOWED_COMMANDS env var (comma-separated executable names).
DEFAULT_ALLOWED_COMMANDS = {
    "git", "ls", "pwd", "cat", "echo", "find", "grep", "rg", "wc",
    "python", "python3", "pip", "pip3", "pytest",
    "node", "npm", "npx", "yarn", "pnpm", "tsc", "eslint", "prettier",
    "go", "cargo", "rustc", "make", "mvn", "gradle", "gradlew", "dotnet",
    "black", "ruff", "mypy", "flake8", "diff",
}

MAX_READ_BYTES = 5 * 1024 * 1024  # 5 MB cap for whole-file reads
MAX_GREP_MATCHES = 500
MAX_TREE_ENTRIES = 2000
COMMAND_TIMEOUT_SECONDS = 30


def _allowed_commands() -> set[str]:
    override = os.environ.get("MCP_ALLOWED_COMMANDS")
    if not override:
        return set(DEFAULT_ALLOWED_COMMANDS)
    return {c.strip() for c in override.split(",") if c.strip()}


VALID_TOOL_MODES = {"read-only", "rw"}


def _tool_mode() -> str:
    mode = None
    for arg in sys.argv[1:]:
        if arg.startswith("--tools="):
            mode = arg.split("=", 1)[1].strip().lower()
            break
    if mode is None:
        mode = os.environ.get("MCP_TOOL_MODE", "read-only").strip().lower()
    if mode not in VALID_TOOL_MODES:
        raise SystemExit(
            f"Invalid tool mode {mode!r}; expected one of {sorted(VALID_TOOL_MODES)}"
        )
    return mode


def _allowed_roots() -> list[Path]:
    raw = [a for a in sys.argv[1:] if not a.startswith("--tools=")]
    if not raw:
        env = os.environ.get("MCP_ALLOWED_ROOTS")
        raw = [p for p in env.split(os.pathsep) if p] if env else []
    if not raw:
        raw = [os.getcwd()]
    return [Path(r).expanduser().resolve() for r in raw]


TOOL_MODE: str = _tool_mode()
ALLOWED_ROOTS: list[Path] = _allowed_roots()
ALLOWED_COMMANDS: set[str] = _allowed_commands()

RG_PATH = shutil.which("rg")
GIT_PATH = shutil.which("git")

mcp = FastMCP("dev-tools")


def read_tool(fn):
    """Register a tool that only ever reads/inspects state. Always available."""
    return mcp.tool()(_logged(fn))


def write_tool(fn):
    """Register a tool that can mutate files/processes. Only in --tools=rw mode."""
    if TOOL_MODE == "rw":
        return mcp.tool()(_logged(fn))
    return fn


# --------------------------------------------------------------------------
# Path safety helpers
# --------------------------------------------------------------------------

class PathAccessError(ValueError):
    """Raised when a requested path escapes the allowed roots."""


def resolve_path(raw_path: str) -> Path:
    """Resolve a user-supplied path against the allowed roots.

    Relative paths are resolved against the first allowed root.
    Absolute paths are accepted only if they fall inside one of the
    allowed roots. Raises PathAccessError otherwise.
    """
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = ALLOWED_ROOTS[0] / candidate

    # Resolve symlinks / '..' without requiring the path to exist yet.
    try:
        resolved = candidate.resolve()
    except OSError as exc:
        raise PathAccessError(f"Could not resolve path {raw_path!r}: {exc}") from exc

    for root in ALLOWED_ROOTS:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue

    roots_str = ", ".join(str(r) for r in ALLOWED_ROOTS)
    raise PathAccessError(
        f"Path {raw_path!r} resolves outside allowed roots ({roots_str})"
    )


def _is_ignored_dir(name: str) -> bool:
    return name in IGNORED_DIR_NAMES


def _iter_files(root: Path, recursive: bool):
    if recursive:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not _is_ignored_dir(d)]
            for name in filenames:
                yield Path(dirpath) / name
    else:
        if root.is_dir():
            for entry in root.iterdir():
                if entry.is_file():
                    yield entry


def _rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _error(message: str, **extra: Any) -> dict[str, Any]:
    return {"error": message, **extra}


# --------------------------------------------------------------------------
# Workspace tools
# --------------------------------------------------------------------------

@read_tool
def list_files(path: str = ".", recursive: bool = True) -> dict[str, Any]:
    """List files and directories under `path`.

    Args:
        path: Directory to list (relative to the workspace root, or absolute
              within an allowed root).
        recursive: If True, walk subdirectories; otherwise list only the
                   immediate contents of `path`.
    """
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not base.exists():
        return _error(f"Path does not exist: {path}")
    if not base.is_dir():
        return _error(f"Not a directory: {path}")

    entries: list[dict[str, Any]] = []
    if recursive:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if not _is_ignored_dir(d)]
            dir_path = Path(dirpath)
            for name in dirnames:
                p = dir_path / name
                entries.append({"path": _rel(p, base), "type": "dir"})
            for name in filenames:
                p = dir_path / name
                try:
                    size = p.stat().st_size
                except OSError:
                    size = None
                entries.append({"path": _rel(p, base), "type": "file", "size": size})
    else:
        for entry in sorted(base.iterdir()):
            if entry.is_dir():
                if _is_ignored_dir(entry.name):
                    continue
                entries.append({"path": entry.name, "type": "dir"})
            else:
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = None
                entries.append({"path": entry.name, "type": "file", "size": size})

    return {"path": str(base), "recursive": recursive, "count": len(entries), "entries": entries}


@read_tool
def tree(path: str = ".", max_depth: int = 4) -> dict[str, Any]:
    """Return a nested directory tree rooted at `path`.

    Args:
        path: Root directory for the tree.
        max_depth: Maximum depth to descend (default 4). Keeps output
                   bounded for large workspaces.
    """
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not base.exists():
        return _error(f"Path does not exist: {path}")
    if not base.is_dir():
        return _error(f"Not a directory: {path}")

    count = 0
    truncated = False

    def build(node: Path, depth: int) -> dict[str, Any]:
        nonlocal count, truncated
        entry: dict[str, Any] = {"name": node.name or str(node), "type": "dir", "children": []}
        if depth >= max_depth:
            entry["truncated"] = "max_depth"
            return entry
        try:
            children = sorted(node.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError as exc:
            entry["error"] = str(exc)
            return entry
        for child in children:
            if count >= MAX_TREE_ENTRIES:
                truncated = True
                break
            if child.is_dir():
                if _is_ignored_dir(child.name):
                    continue
                count += 1
                entry["children"].append(build(child, depth + 1))
            else:
                count += 1
                entry["children"].append({"name": child.name, "type": "file"})
        return entry

    result = build(base, 0)
    return {"path": str(base), "max_depth": max_depth, "truncated": truncated, "tree": result}


@read_tool
def find_files(pattern: str, path: str = ".") -> dict[str, Any]:
    """Find files whose relative path matches a glob pattern (e.g. '**/*.py').

    Args:
        pattern: Glob pattern, evaluated relative to `path` (fnmatch-style,
                 supports '*', '?', '**').
        path: Directory to search under.
    """
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not base.exists():
        return _error(f"Path does not exist: {path}")
    if not base.is_dir():
        return _error(f"Not a directory: {path}")

    matches: list[str] = []
    try:
        for p in base.glob(pattern):
            parts = p.relative_to(base).parts
            if any(_is_ignored_dir(part) for part in parts[:-1]):
                continue
            if p.is_file():
                matches.append(_rel(p, base))
    except (ValueError, NotImplementedError) as exc:
        return _error(f"Invalid glob pattern {pattern!r}: {exc}")

    matches.sort()
    return {"pattern": pattern, "path": str(base), "count": len(matches), "matches": matches}


# --------------------------------------------------------------------------
# File operation tools
# --------------------------------------------------------------------------

@read_tool
def read_file(path: str) -> str:
    """Read and return the full contents of a text file."""
    try:
        target = resolve_path(path)
    except PathAccessError as exc:
        return f"ERROR: {exc}"
    if not target.exists():
        return f"ERROR: Path does not exist: {path}"
    if not target.is_file():
        return f"ERROR: Not a file: {path}"
    try:
        size = target.stat().st_size
        if size > MAX_READ_BYTES:
            return (
                f"ERROR: File is {size} bytes, exceeds {MAX_READ_BYTES} byte limit. "
                "Use read_file_range instead."
            )
        return target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"ERROR: Could not read {path}: {exc}"


@read_tool
def read_file_range(path: str, start_line: int, end_line: int) -> dict[str, Any]:
    """Read a range of lines (1-indexed, inclusive) from a text file.

    Args:
        path: File to read.
        start_line: First line to include (1-indexed).
        end_line: Last line to include (1-indexed, inclusive).
    """
    try:
        target = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not target.exists():
        return _error(f"Path does not exist: {path}")
    if not target.is_file():
        return _error(f"Not a file: {path}")
    if start_line < 1 or end_line < start_line:
        return _error(f"Invalid range: start_line={start_line}, end_line={end_line}")

    try:
        with target.open("r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        return _error(f"Could not read {path}: {exc}")

    total = len(lines)
    selected = lines[start_line - 1 : end_line]
    return {
        "path": str(target),
        "start_line": start_line,
        "end_line": min(end_line, total),
        "total_lines": total,
        "content": "".join(selected),
    }


@write_tool
def write_file(path: str, content: str) -> dict[str, Any]:
    """Write `content` to a file, creating parent directories and overwriting if needed.

    Args:
        path: Destination file path.
        content: Full text content to write.
    """
    try:
        target = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))

    created = not target.exists()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        return _error(f"Could not write {path}: {exc}")

    return {"path": str(target), "bytes_written": len(content.encode("utf-8")), "created": created}


@write_tool
def replace_in_file(path: str, search: str, replace: str, count: int = -1) -> dict[str, Any]:
    """Replace literal occurrences of `search` with `replace` in a file.

    Args:
        path: File to modify.
        search: Exact literal text to find (not a regex).
        replace: Replacement text.
        count: Maximum number of occurrences to replace (-1 = all).
    """
    try:
        target = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not target.exists():
        return _error(f"Path does not exist: {path}")
    if not target.is_file():
        return _error(f"Not a file: {path}")

    try:
        original = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return _error(f"Could not read {path}: {exc}")

    occurrences = original.count(search)
    if occurrences == 0:
        return _error(f"Search text not found in {path}", occurrences=0)

    max_count = occurrences if count < 0 else min(count, occurrences)
    updated = original.replace(search, replace, max_count)

    try:
        target.write_text(updated, encoding="utf-8")
    except OSError as exc:
        return _error(f"Could not write {path}: {exc}")

    return {"path": str(target), "replacements": max_count}


# --------------------------------------------------------------------------
# Search tools
# --------------------------------------------------------------------------

@read_tool
def grep(pattern: str, path: str = ".", case_insensitive: bool = False) -> dict[str, Any]:
    """Search for a regex pattern in files under `path`.

    Uses ripgrep when available for speed and .gitignore awareness, and
    falls back to a pure-Python recursive scan otherwise.

    Args:
        pattern: Regular expression to search for.
        path: File or directory to search.
        case_insensitive: If True, match case-insensitively.
    """
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not base.exists():
        return _error(f"Path does not exist: {path}")

    if RG_PATH:
        return _grep_ripgrep(pattern, base, case_insensitive)
    return _grep_python(pattern, base, case_insensitive)


def _grep_ripgrep(pattern: str, base: Path, case_insensitive: bool) -> dict[str, Any]:
    cmd = [RG_PATH, "--line-number", "--no-heading", "--color=never"]
    if case_insensitive:
        cmd.append("--ignore-case")
    cmd += [pattern, str(base)]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=COMMAND_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        return _error("ripgrep timed out")
    except OSError as exc:
        return _error(f"Failed to run ripgrep: {exc}")

    if proc.returncode not in (0, 1):
        return _error(f"ripgrep failed: {proc.stderr.strip()}")

    matches: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        file_path, line_no, text = parts
        matches.append({"file": _rel(Path(file_path), base), "line": int(line_no), "text": text})
        if len(matches) >= MAX_GREP_MATCHES:
            break

    return {
        "pattern": pattern,
        "path": str(base),
        "engine": "ripgrep",
        "match_count": len(matches),
        "truncated": len(matches) >= MAX_GREP_MATCHES,
        "matches": matches,
    }


def _grep_python(pattern: str, base: Path, case_insensitive: bool) -> dict[str, Any]:
    try:
        regex = re.compile(pattern, re.IGNORECASE if case_insensitive else 0)
    except re.error as exc:
        return _error(f"Invalid regex {pattern!r}: {exc}")

    matches: list[dict[str, Any]] = []
    truncated = False
    files = [base] if base.is_file() else list(_iter_files(base, recursive=True))
    for f in files:
        if len(matches) >= MAX_GREP_MATCHES:
            truncated = True
            break
        try:
            with f.open("r", encoding="utf-8", errors="ignore") as fh:
                for line_no, text in enumerate(fh, start=1):
                    if regex.search(text):
                        matches.append(
                            {"file": _rel(f, base), "line": line_no, "text": text.rstrip("\n")}
                        )
                        if len(matches) >= MAX_GREP_MATCHES:
                            truncated = True
                            break
        except (OSError, UnicodeDecodeError):
            continue

    return {
        "pattern": pattern,
        "path": str(base),
        "engine": "python-fallback",
        "match_count": len(matches),
        "truncated": truncated,
        "matches": matches,
    }


@read_tool
def search_filename(pattern: str, path: str = ".") -> dict[str, Any]:
    """Search for files whose basename matches a pattern (case-insensitive substring or glob).

    Args:
        pattern: Substring or fnmatch-style glob (e.g. '*.test.ts') to match
                 against file basenames.
        path: Directory to search under.
    """
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not base.exists():
        return _error(f"Path does not exist: {path}")

    is_glob = any(ch in pattern for ch in "*?[")
    matches: list[str] = []
    for f in _iter_files(base, recursive=True):
        name = f.name
        hit = fnmatch.fnmatch(name.lower(), pattern.lower()) if is_glob else pattern.lower() in name.lower()
        if hit:
            matches.append(_rel(f, base))

    matches.sort()
    return {"pattern": pattern, "path": str(base), "count": len(matches), "matches": matches}


# --------------------------------------------------------------------------
# Code navigation tools
# --------------------------------------------------------------------------

_SYMBOL_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    ".py": [
        ("class", re.compile(r"^\s*class\s+(\w+)")),
        ("function", re.compile(r"^\s*(?:async\s+)?def\s+(\w+)")),
    ],
    ".js": [
        ("class", re.compile(r"^\s*(?:export\s+)?class\s+(\w+)")),
        ("function", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)")),
        ("const", re.compile(r"^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(")),
    ],
    ".jsx": [],  # filled in below (shares .js patterns)
    ".ts": [],   # filled in below
    ".tsx": [],  # filled in below
    ".java": [
        ("class", re.compile(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?class\s+(\w+)")),
        ("interface", re.compile(r"^\s*(?:public\s+)?interface\s+(\w+)")),
        ("method", re.compile(r"^\s*(?:public|private|protected)\s+[\w<>\[\],\s]+?\s(\w+)\s*\(")),
    ],
    ".kt": [
        ("class", re.compile(r"^\s*(?:data\s+|sealed\s+|abstract\s+)*class\s+(\w+)")),
        ("function", re.compile(r"^\s*fun\s+(\w+)")),
        ("object", re.compile(r"^\s*object\s+(\w+)")),
    ],
    ".go": [
        ("function", re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?(\w+)")),
        ("type", re.compile(r"^\s*type\s+(\w+)\s+struct")),
    ],
    ".rs": [
        ("function", re.compile(r"^\s*(?:pub\s+)?fn\s+(\w+)")),
        ("struct", re.compile(r"^\s*(?:pub\s+)?struct\s+(\w+)")),
        ("enum", re.compile(r"^\s*(?:pub\s+)?enum\s+(\w+)")),
    ],
}
_SYMBOL_PATTERNS[".jsx"] = _SYMBOL_PATTERNS[".js"]
_SYMBOL_PATTERNS[".ts"] = _SYMBOL_PATTERNS[".js"]
_SYMBOL_PATTERNS[".tsx"] = _SYMBOL_PATTERNS[".js"]


@read_tool
def list_symbols(path: str) -> dict[str, Any]:
    """List top-level classes/functions/methods found in a source file (regex-based, best effort).

    Args:
        path: Source file to scan.
    """
    try:
        target = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not target.exists():
        return _error(f"Path does not exist: {path}")
    if not target.is_file():
        return _error(f"Not a file: {path}")

    ext = target.suffix.lower()
    patterns = _SYMBOL_PATTERNS.get(ext)
    if not patterns:
        return _error(f"No symbol extraction rules for extension {ext!r}", path=str(target))

    try:
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return _error(f"Could not read {path}: {exc}")

    symbols: list[dict[str, Any]] = []
    for line_no, line in enumerate(lines, start=1):
        for kind, regex in patterns:
            m = regex.match(line)
            if m:
                symbols.append({"name": m.group(1), "kind": kind, "line": line_no})

    return {"path": str(target), "language": ext.lstrip("."), "symbol_count": len(symbols), "symbols": symbols}


_LANGUAGE_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
    ".kt": "Kotlin", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++",
    ".cs": "C#", ".swift": "Swift", ".m": "Objective-C", ".sh": "Shell",
    ".md": "Markdown", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".sql": "SQL",
}

_FRAMEWORK_MARKERS: list[tuple[str, str]] = [
    ("package.json", "Node.js"),
    ("requirements.txt", "Python (pip)"),
    ("pyproject.toml", "Python (pyproject)"),
    ("Pipfile", "Python (pipenv)"),
    ("pom.xml", "Java (Maven)"),
    ("build.gradle", "Java/Kotlin (Gradle)"),
    ("build.gradle.kts", "Kotlin (Gradle)"),
    ("Cargo.toml", "Rust (Cargo)"),
    ("go.mod", "Go modules"),
    ("Gemfile", "Ruby (Bundler)"),
    ("composer.json", "PHP (Composer)"),
    ("Dockerfile", "Docker"),
    ("docker-compose.yml", "Docker Compose"),
    (".csproj", "C# (.NET)"),
]

_IMPORTANT_FILE_NAMES = {
    "README.md", "README", "README.rst", "LICENSE", "LICENSE.md",
    "CHANGELOG.md", "CONTRIBUTING.md", ".gitignore", "Makefile",
    "Dockerfile", "docker-compose.yml", "package.json", "pyproject.toml",
    "requirements.txt", "go.mod", "Cargo.toml", "pom.xml",
}


@read_tool
def workspace_summary(path: str = ".") -> dict[str, Any]:
    """Summarize a workspace: detected languages, frameworks, and key files.

    Args:
        path: Directory to summarize.
    """
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not base.exists():
        return _error(f"Path does not exist: {path}")
    if not base.is_dir():
        return _error(f"Not a directory: {path}")

    language_counts: dict[str, int] = {}
    important_files: list[str] = []
    frameworks: set[str] = set()
    total_files = 0

    for f in _iter_files(base, recursive=True):
        total_files += 1
        lang = _LANGUAGE_EXTENSIONS.get(f.suffix.lower())
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1
        if f.name in _IMPORTANT_FILE_NAMES and f.parent == base:
            important_files.append(_rel(f, base))
        for marker, framework in _FRAMEWORK_MARKERS:
            if f.name == marker or f.name.endswith(marker):
                frameworks.add(framework)

    languages_sorted = dict(sorted(language_counts.items(), key=lambda kv: -kv[1]))

    return {
        "path": str(base),
        "total_files": total_files,
        "languages": languages_sorted,
        "frameworks": sorted(frameworks),
        "important_files": sorted(important_files),
    }


# --------------------------------------------------------------------------
# Git tools
# --------------------------------------------------------------------------

def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [GIT_PATH, *args], cwd=cwd, capture_output=True, text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


@read_tool
def git_status(path: str = ".") -> dict[str, Any]:
    """Show git status (branch, staged/unstaged/untracked files) for the repo at `path`."""
    if not GIT_PATH:
        return _error("git is not available on this system")
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))

    try:
        branch_proc = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], base)
        status_proc = _run_git(["status", "--porcelain=v1"], base)
    except subprocess.TimeoutExpired:
        return _error("git command timed out")
    except OSError as exc:
        return _error(f"Failed to run git: {exc}")

    if status_proc.returncode != 0:
        return _error(f"git status failed: {status_proc.stderr.strip()}")

    staged, unstaged, untracked = [], [], []
    for line in status_proc.stdout.splitlines():
        if not line:
            continue
        code, file_path = line[:2], line[3:]
        if code == "??":
            untracked.append(file_path)
            continue
        if code[0] not in (" ", "?"):
            staged.append(file_path)
        if code[1] not in (" ", "?"):
            unstaged.append(file_path)

    return {
        "path": str(base),
        "branch": branch_proc.stdout.strip() if branch_proc.returncode == 0 else None,
        "clean": not (staged or unstaged or untracked),
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
    }


@read_tool
def git_diff(path: str = ".", staged: bool = False) -> dict[str, Any]:
    """Show the git diff for the repo at `path`.

    Args:
        path: Repository (or file) path.
        staged: If True, show the staged (--cached) diff instead of the working tree diff.
    """
    if not GIT_PATH:
        return _error("git is not available on this system")
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))

    args = ["diff"]
    if staged:
        args.append("--cached")
    try:
        proc = _run_git(args, base)
    except subprocess.TimeoutExpired:
        return _error("git command timed out")
    except OSError as exc:
        return _error(f"Failed to run git: {exc}")

    if proc.returncode != 0:
        return _error(f"git diff failed: {proc.stderr.strip()}")

    return {"path": str(base), "staged": staged, "diff": proc.stdout}


@read_tool
def git_log(path: str = ".", limit: int = 10) -> dict[str, Any]:
    """Show recent commits for the repo at `path`.

    Args:
        path: Repository path.
        limit: Maximum number of commits to return.
    """
    if not GIT_PATH:
        return _error("git is not available on this system")
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))

    sep = "\x1f"
    fmt = sep.join(["%H", "%an", "%ad", "%s"])
    args = ["log", f"-n{max(1, limit)}", f"--pretty=format:{fmt}", "--date=iso-strict"]
    try:
        proc = _run_git(args, base)
    except subprocess.TimeoutExpired:
        return _error("git command timed out")
    except OSError as exc:
        return _error(f"Failed to run git: {exc}")

    if proc.returncode != 0:
        return _error(f"git log failed: {proc.stderr.strip()}")

    commits = []
    for line in proc.stdout.splitlines():
        parts = line.split(sep)
        if len(parts) != 4:
            continue
        commit_hash, author, date, message = parts
        commits.append({"hash": commit_hash, "author": author, "date": date, "message": message})

    return {"path": str(base), "limit": limit, "count": len(commits), "commits": commits}


# --------------------------------------------------------------------------
# Terminal tool
# --------------------------------------------------------------------------

@write_tool
def run_command(command: str, cwd: str = ".") -> dict[str, Any]:
    """Run an allowlisted shell command and return its output.

    Only executables in the allowlist may be run (default: common dev
    tools like git, python, npm, pytest; override with the
    MCP_ALLOWED_COMMANDS env var). Commands run without a shell, so
    piping/redirection is not supported.

    Args:
        command: Full command line, e.g. "git status" or "pytest -k foo".
        cwd: Working directory to run the command in.
    """
    try:
        work_dir = resolve_path(cwd)
    except PathAccessError as exc:
        return _error(str(exc))
    if not work_dir.is_dir():
        return _error(f"cwd is not a directory: {cwd}")

    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return _error(f"Could not parse command: {exc}")
    if not parts:
        return _error("Empty command")

    executable = os.path.basename(parts[0])
    if executable not in ALLOWED_COMMANDS:
        return _error(
            f"Command {executable!r} is not in the allowlist",
            allowed_commands=sorted(ALLOWED_COMMANDS),
        )

    try:
        proc = subprocess.run(
            parts, cwd=work_dir, capture_output=True, text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command, "cwd": str(work_dir), "exit_code": None,
            "stdout": exc.stdout or "", "stderr": (exc.stderr or "") + "\n[timed out]",
            "timed_out": True,
        }
    except OSError as exc:
        return _error(f"Failed to run command: {exc}")

    return {
        "command": command,
        "cwd": str(work_dir),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "timed_out": timed_out,
    }


# --------------------------------------------------------------------------
# Utility tools
# --------------------------------------------------------------------------

@read_tool
def file_info(path: str) -> dict[str, Any]:
    """Return metadata about a file or directory: size, type, timestamps, permissions."""
    try:
        target = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not target.exists():
        return {"path": str(target), "exists": False}

    try:
        st = target.stat()
    except OSError as exc:
        return _error(f"Could not stat {path}: {exc}")

    return {
        "path": str(target),
        "exists": True,
        "type": "dir" if target.is_dir() else ("file" if target.is_file() else "other"),
        "size_bytes": st.st_size,
        "modified": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime)),
        "created": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_ctime)),
        "permissions": stat.filemode(st.st_mode),
    }


@read_tool
def directory_size(path: str = ".") -> dict[str, Any]:
    """Recursively compute the total size, file count, and directory count under `path`."""
    try:
        base = resolve_path(path)
    except PathAccessError as exc:
        return _error(str(exc))
    if not base.exists():
        return _error(f"Path does not exist: {path}")
    if not base.is_dir():
        return _error(f"Not a directory: {path}")

    total_bytes = 0
    total_files = 0
    total_dirs = 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not _is_ignored_dir(d)]
        total_dirs += len(dirnames)
        for name in filenames:
            fp = Path(dirpath) / name
            try:
                total_bytes += fp.stat().st_size
                total_files += 1
            except OSError:
                continue

    return {
        "path": str(base),
        "total_bytes": total_bytes,
        "total_files": total_files,
        "total_dirs": total_dirs,
    }


# --------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info(
        "startup: tool_mode=%s allowed_roots=%s ripgrep=%s git=%s",
        TOOL_MODE, [str(r) for r in ALLOWED_ROOTS], RG_PATH, GIT_PATH,
    )
    mcp.run(transport="stdio")
