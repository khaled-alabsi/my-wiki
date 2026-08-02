"""Extraction: turn any supported file into a ``Document`` the chunker understands.

Every extractor returns the same shape, so ``chunk.py`` never branches on file type —
it branches on ``Document.kind``, which is a chunking strategy, not a format.

Optional dependencies degrade honestly: a missing extractor makes the file
``unsupported`` with a reason, never a silently empty document.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Chunking strategies a Document can ask for.
KIND_MARKDOWN = "markdown"  # heading-aware
KIND_CODE = "code"  # symbol/window-aware, line anchors
KIND_TEXT = "text"  # recursive paragraph split, line anchors
KIND_PAGED = "paged"  # one block per page/slide, page anchors
KIND_TABULAR = "tabular"  # row groups with a repeated header
KIND_NOTEBOOK = "notebook"  # cell blocks


@dataclass
class Block:
    """A pre-segmented span with its own citation anchor (a page, a sheet, a cell)."""

    text: str
    anchor: dict[str, Any] = field(default_factory=dict)
    kind: str = "block"


@dataclass
class Document:
    path: str
    kind: str = KIND_TEXT
    title: str = ""
    text: str = ""
    blocks: list[Block] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    extractor: str = ""
    error: str = ""

    @property
    def is_empty(self) -> bool:
        if self.blocks:
            return not any(b.text.strip() for b in self.blocks)
        return not self.text.strip()

    @property
    def char_count(self) -> int:
        return sum(len(b.text) for b in self.blocks) if self.blocks else len(self.text)


# ext -> (module suffix, function name, human name of the dependency it needs)
REGISTRY: dict[str, tuple[str, str, str]] = {}


def _register(exts: tuple[str, ...], module: str, func: str, dep: str = "") -> None:
    for ext in exts:
        REGISTRY[ext] = (module, func, dep)


_register((".md", ".markdown", ".mdx"), "text", "extract_markdown")
_register((".txt", ".text", ".rst", ".org", ".log", ".rtf"), "text", "extract_text")
_register((".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml", ".properties"),
          "text", "extract_text")
_register((".csv", ".tsv"), "text", "extract_delimited")
_register((".ipynb",), "text", "extract_notebook")
_register((".pdf",), "pdf", "extract_pdf", "pymupdf")
_register((".docx",), "office", "extract_docx", "python-docx")
_register((".pptx",), "office", "extract_pptx", "python-pptx")
_register((".xlsx", ".xlsm"), "office", "extract_xlsx", "openpyxl")
_register((".html", ".htm", ".xhtml"), "web", "extract_html", "selectolax")
_register((".epub",), "web", "extract_epub", "selectolax")

CODE_EXTENSIONS = {
    ".py", ".java", ".kt", ".kts", ".cs", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".go", ".rs", ".rb", ".php", ".c", ".h", ".cpp", ".hpp", ".cc", ".scala", ".swift",
    ".m", ".mm", ".sh", ".bash", ".zsh", ".ps1", ".sql", ".r", ".jl", ".lua", ".pl",
    ".vue", ".svelte", ".gradle", ".tf", ".proto", ".graphql", ".css", ".scss", ".less",
    ".dockerfile", ".make", ".cmake", ".vb", ".fs", ".ex", ".exs", ".erl", ".dart",
}
for _ext in CODE_EXTENSIONS:
    _register((_ext,), "text", "extract_code")

# Files with no extension that are worth reading anyway.
BARE_NAMES = {
    "readme", "license", "licence", "changelog", "contributing", "authors", "notice",
    "makefile", "dockerfile", "jenkinsfile", "procfile", "codeowners", "todo",
}


def supported_extensions() -> set[str]:
    return set(REGISTRY)


def is_supported(path: str | Path) -> bool:
    p = Path(path)
    if p.suffix.lower() in REGISTRY:
        return True
    return not p.suffix and p.name.lower() in BARE_NAMES


def dependency_for(path: str | Path) -> str:
    entry = REGISTRY.get(Path(path).suffix.lower())
    return entry[2] if entry else ""


def extract(path: str | Path, **options: Any) -> Document:
    """Dispatch on extension. Never raises for a bad file — returns ``Document.error``."""
    p = Path(path)
    ext = p.suffix.lower()
    if not ext and p.name.lower() in BARE_NAMES:
        entry = ("text", "extract_text", "")
    else:
        entry = REGISTRY.get(ext)  # type: ignore[assignment]
    if entry is None:
        return Document(path=str(p), error=f"no extractor for '{ext or p.name}'")

    module_name, func_name, dep = entry
    try:
        module = importlib.import_module(f".{module_name}", __package__)
        handler = getattr(module, func_name)
    except ImportError as exc:
        hint = f" (install the '{dep}' extra)" if dep else ""
        return Document(path=str(p), error=f"extractor unavailable: {exc}{hint}")

    try:
        doc = handler(p, **options)
    except Exception as exc:  # a corrupt file must not stop an index run
        return Document(path=str(p), extractor=f"{module_name}.{func_name}",
                        error=f"{type(exc).__name__}: {exc}")

    doc.extractor = doc.extractor or f"{module_name}.{func_name}"
    if not doc.title:
        doc.title = p.stem
    return doc


def read_text_file(path: Path, max_bytes: int = 0) -> str:
    """Decode a text file, trying the encodings that actually occur in the wild."""
    raw = path.read_bytes()
    if max_bytes and len(raw) > max_bytes:
        raw = raw[:max_bytes]
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def looks_binary(path: Path, probe: int = 4096) -> bool:
    try:
        with path.open("rb") as handle:
            sample = handle.read(probe)
    except OSError:
        return True
    if b"\x00" in sample:
        return True
    if not sample:
        return False
    printable = sum(1 for byte in sample if 32 <= byte < 127 or byte in (9, 10, 13))
    return printable / len(sample) < 0.75
