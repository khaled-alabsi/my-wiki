"""File discovery: walk the configured sources and decide what is indexable.

Ignore rules are applied in this order, first match wins:

1. ``DEFAULT_SKIP_DIRS`` — build output, caches, VCS internals.
2. ``is_private_name`` — any file or directory whose name starts with ``.`` or ``_``.
   Not configurable: private names are never indexed.
3. ``.rag/.ragignore`` — the user's own excludes, gitignore syntax.
4. each source's root ``.gitignore``, when ``corpus.use_gitignore`` is true.
5. ``sources[].include`` — if non-empty, an allowlist: nothing else is indexed.
6. size cap, binary sniff, and "is there an extractor for this".
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from . import extract
from .detect import DEFAULT_SKIP_DIRS, is_private_name


@dataclass
class Candidate:
    path: Path
    source: str
    rel_path: str
    size: int
    mtime: float
    ext: str


@dataclass
class Skipped:
    path: Path
    source: str
    reason: str


class IgnoreRules:
    """gitignore-style matching. Uses pathspec when available, fnmatch otherwise."""

    def __init__(self, patterns: list[str]) -> None:
        self.patterns = [p for p in patterns if p.strip() and not p.strip().startswith("#")]
        self._spec = None
        if self.patterns:
            try:
                import pathspec

                self._spec = pathspec.PathSpec.from_lines("gitwildmatch", self.patterns)
            except ImportError:
                self._spec = None

    def matches(self, rel_path: str, is_dir: bool = False) -> bool:
        if not self.patterns:
            return False
        probe = rel_path.replace(os.sep, "/")
        if self._spec is not None:
            return bool(self._spec.match_file(probe + ("/" if is_dir else "")))
        return self._fnmatch(probe, is_dir)

    def _fnmatch(self, probe: str, is_dir: bool) -> bool:
        """Fallback: handles the common gitignore forms, not the exotic ones."""
        name = probe.rsplit("/", 1)[-1]
        for raw in self.patterns:
            pattern = raw.strip().rstrip("/")
            dir_only = raw.strip().endswith("/")
            if dir_only and not is_dir:
                continue
            if pattern.startswith("/"):
                if fnmatch.fnmatch(probe, pattern.lstrip("/")):
                    return True
                continue
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(probe, pattern):
                return True
            if fnmatch.fnmatch(probe, f"*/{pattern}") or probe.startswith(f"{pattern}/"):
                return True
        return False

    @classmethod
    def from_files(cls, *paths: Path, extra: list[str] | None = None) -> "IgnoreRules":
        lines: list[str] = list(extra or [])
        for path in paths:
            if path and path.is_file():
                try:
                    lines.extend(path.read_text(encoding="utf-8", errors="ignore").splitlines())
                except OSError:
                    continue
        return cls(lines)


def rules_for(cfg: dict[str, Any], rag_dir: Path, source: dict[str, Any]) -> IgnoreRules:
    files = [rag_dir / ".ragignore"]
    if cfg.get("corpus", {}).get("use_gitignore", True):
        files.append(Path(source["path"]) / ".gitignore")
    return IgnoreRules.from_files(*files, extra=list(source.get("exclude") or []))


def iter_source(
    cfg: dict[str, Any],
    rag_dir: Path,
    source: dict[str, Any],
    collect_skips: bool = False,
) -> Iterator[Candidate | Skipped]:
    """Yield indexable ``Candidate`` files, plus ``Skipped`` rows when asked."""
    root = Path(source["path"]).resolve()
    name = source.get("name") or root.name
    if not root.is_dir():
        if collect_skips:
            yield Skipped(root, name, "source path is not a directory")
        return

    corpus = cfg.get("corpus", {})
    rules = rules_for(cfg, rag_dir, source)
    include = [p for p in (source.get("include") or []) if p.strip()]
    max_bytes = int(float(corpus.get("max_file_mb", 25)) * 1024 * 1024)
    follow = bool(corpus.get("follow_symlinks", False))

    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow):
        here = Path(dirpath)
        rel_dir = here.relative_to(root).as_posix()
        if rel_dir == ".":  # the source root itself — otherwise every path gains a './'
            rel_dir = ""
        keep: list[str] = []
        for directory in dirnames:
            rel = f"{rel_dir}/{directory}".lstrip("/")
            if directory in DEFAULT_SKIP_DIRS or is_private_name(directory):
                continue
            if rules.matches(rel, is_dir=True):
                continue
            keep.append(directory)
        dirnames[:] = keep

        for filename in sorted(filenames):
            path = here / filename
            rel = f"{rel_dir}/{filename}".lstrip("/")
            verdict = _judge(path, rel, rules, include, max_bytes)
            if verdict is None:
                try:
                    stat = path.stat()
                except OSError:
                    continue
                yield Candidate(path, name, rel, stat.st_size, stat.st_mtime, path.suffix.lower())
            elif collect_skips:
                yield Skipped(path, name, verdict)


def _judge(path: Path, rel: str, rules: IgnoreRules, include: list[str], max_bytes: int) -> str | None:
    """Return a skip reason, or None if the file should be indexed."""
    if is_private_name(path.name):
        return "private name (starts with '.' or '_')"
    if rules.matches(rel):
        return "ignored by .ragignore or .gitignore"
    if include and not any(fnmatch.fnmatch(rel, pattern) for pattern in include):
        return "not in the include allowlist"
    if not extract.is_supported(path):
        return f"no extractor for '{path.suffix.lower() or path.name}'"
    try:
        size = path.stat().st_size
    except OSError as exc:
        return f"unreadable: {exc}"
    if size == 0:
        return "empty file"
    if size > max_bytes:
        return f"larger than corpus.max_file_mb ({size / 1024**2:.1f} MB)"
    if path.suffix.lower() not in {".pdf", ".docx", ".pptx", ".xlsx", ".xlsm", ".epub"}:
        if extract.looks_binary(path):
            return "looks binary"
    return None


def iter_files(cfg: dict[str, Any], rag_dir: Path, source_name: str | None = None) -> Iterator[Candidate]:
    for source in cfg.get("sources", []):
        if source_name and source.get("name") != source_name:
            continue
        for item in iter_source(cfg, rag_dir, source):
            if isinstance(item, Candidate):
                yield item


# Fraction of a file's bytes that survives as indexable text. Container formats carry a
# lot of markup and compression, so their raw size badly overstates their text.
TEXT_YIELD = {
    ".pdf": 0.06, ".docx": 0.10, ".pptx": 0.03, ".xlsx": 0.08, ".xlsm": 0.08,
    ".epub": 0.25, ".html": 0.25, ".htm": 0.25, ".xhtml": 0.25, ".ipynb": 0.55,
}
DEFAULT_TEXT_YIELD = 0.95


def plan(cfg: dict[str, Any], rag_dir: Path, sample_skips: int = 25) -> dict[str, Any]:
    """Dry-run summary: what would be indexed, what would not, and a chunk estimate."""
    target = int(cfg.get("chunking", {}).get("target_chars", 1800))
    overlap = int(cfg.get("chunking", {}).get("overlap_chars", 220))
    stride = max(target - overlap, target // 2, 1)

    files = 0
    total_bytes = 0
    text_bytes = 0.0
    by_ext: dict[str, int] = {}
    by_source: dict[str, int] = {}
    skips: dict[str, int] = {}
    examples: list[str] = []

    for source in cfg.get("sources", []):
        for item in iter_source(cfg, rag_dir, source, collect_skips=True):
            if isinstance(item, Skipped):
                key = item.reason.split(" (")[0]
                skips[key] = skips.get(key, 0) + 1
                if len(examples) < sample_skips:
                    examples.append(f"{item.path.name}: {item.reason}")
                continue
            files += 1
            total_bytes += item.size
            text_bytes += item.size * TEXT_YIELD.get(item.ext, DEFAULT_TEXT_YIELD)
            by_ext[item.ext or "<none>"] = by_ext.get(item.ext or "<none>", 0) + 1
            by_source[item.source] = by_source.get(item.source, 0) + 1

    return {
        "files": files,
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / 1024**2, 1),
        "estimated_text_mb": round(text_bytes / 1024**2, 1),
        "estimated_chunks": max(files, int(text_bytes // stride)) if files else 0,
        "by_extension": dict(sorted(by_ext.items(), key=lambda kv: kv[1], reverse=True)[:30]),
        "by_source": by_source,
        "skipped": dict(sorted(skips.items(), key=lambda kv: kv[1], reverse=True)),
        "skip_examples": examples,
    }
