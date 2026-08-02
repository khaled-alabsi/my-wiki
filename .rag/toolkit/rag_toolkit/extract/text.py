"""Text-family extractors: Markdown, plain text, source code, delimited data, notebooks.

All stdlib. These cover the large majority of files in a typical corpus, so they must
never need an optional dependency to work.
"""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import Any

from . import (
    KIND_CODE,
    KIND_MARKDOWN,
    KIND_NOTEBOOK,
    KIND_TABULAR,
    KIND_TEXT,
    Block,
    Document,
    read_text_file,
)

LANG_BY_EXT = {
    ".py": "python", ".java": "java", ".kt": "kotlin", ".cs": "csharp", ".js": "javascript",
    ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript", ".go": "go",
    ".rs": "rust", ".rb": "ruby", ".php": "php", ".c": "c", ".h": "c", ".cpp": "cpp",
    ".hpp": "cpp", ".cc": "cpp", ".scala": "scala", ".swift": "swift", ".sh": "shell",
    ".bash": "shell", ".zsh": "shell", ".ps1": "powershell", ".sql": "sql", ".r": "r",
    ".jl": "julia", ".lua": "lua", ".pl": "perl", ".vue": "vue", ".svelte": "svelte",
    ".gradle": "gradle", ".tf": "terraform", ".proto": "protobuf", ".graphql": "graphql",
    ".css": "css", ".scss": "scss", ".less": "less", ".dart": "dart", ".ex": "elixir",
}

WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
INLINE_TAG = re.compile(r"(?:^|\s)#([A-Za-z][\w/-]{1,60})")


# --------------------------------------------------------------------------- frontmatter


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse a leading ``---`` YAML block. Deliberately minimal: scalars and lists only."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current_key:
            meta.setdefault(current_key, [])
            if isinstance(meta[current_key], list):
                meta[current_key].append(stripped[2:].strip().strip("\"'"))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        current_key = key
        if not value:
            meta[key] = []
        elif value.startswith("[") and value.endswith("]"):
            meta[key] = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key] = value.strip("\"'")
    return meta, body


# --------------------------------------------------------------------------- extractors


def extract_markdown(path: Path, **_: Any) -> Document:
    raw = read_text_file(path)
    meta, body = split_frontmatter(raw)

    tags: list[str] = []
    for key in ("tags", "tag", "keywords"):
        value = meta.get(key)
        if isinstance(value, list):
            tags.extend(str(v) for v in value)
        elif isinstance(value, str):
            tags.extend(t.strip() for t in value.replace(",", " ").split() if t.strip())
    tags.extend(m.group(1) for m in INLINE_TAG.finditer(body))

    title = str(meta.get("title") or "").strip()
    if not title:
        heading = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = heading.group(1).strip() if heading else path.stem

    links = sorted({m.group(1) for m in WIKILINK.finditer(body)} |
                   {m.group(1) for m in MD_LINK.finditer(body) if not m.group(1).startswith("#")})

    return Document(
        path=str(path), kind=KIND_MARKDOWN, title=title, text=body,
        meta={"frontmatter": meta, "tags": sorted(set(tags))[:40], "links": links[:100]},
    )


def extract_text(path: Path, **_: Any) -> Document:
    return Document(path=str(path), kind=KIND_TEXT, title=path.stem, text=read_text_file(path))


def extract_code(path: Path, **_: Any) -> Document:
    language = LANG_BY_EXT.get(path.suffix.lower(), path.suffix.lstrip(".") or "text")
    return Document(
        path=str(path), kind=KIND_CODE, title=path.name, text=read_text_file(path),
        meta={"language": language},
    )


def extract_delimited(path: Path, rows_per_block: int = 40, **_: Any) -> Document:
    """CSV/TSV into row groups. The header is repeated in every block so each stands alone."""
    text = read_text_file(path, max_bytes=8 * 1024 * 1024)
    delimiter = "\t" if path.suffix.lower() == ".tsv" else _sniff_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        return Document(path=str(path), kind=KIND_TABULAR, title=path.stem)

    header_line = " | ".join(h.strip() for h in header)
    blocks: list[Block] = []
    batch: list[str] = []
    start = 2
    rows_seen = 0
    for number, row in enumerate(reader, start=2):
        batch.append(" | ".join(cell.strip() for cell in row))
        rows_seen += 1
        if len(batch) >= rows_per_block:
            blocks.append(_row_block(path, header_line, batch, start, number))
            batch, start = [], number + 1
    if batch:
        blocks.append(_row_block(path, header_line, batch, start, start + len(batch) - 1))

    return Document(
        path=str(path), kind=KIND_TABULAR, title=path.stem, blocks=blocks,
        meta={"columns": [h.strip() for h in header], "row_count": rows_seen},
    )


def _row_block(path: Path, header: str, rows: list[str], first: int, last: int) -> Block:
    body = f"{path.name} — columns: {header}\n" + "\n".join(rows)
    return Block(text=body, kind="rows", anchor={"line_start": first, "line_end": last})


def _sniff_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:20])
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def extract_notebook(path: Path, **_: Any) -> Document:
    """Jupyter notebooks: one block per cell, with short text outputs kept."""
    data = json.loads(read_text_file(path))
    blocks: list[Block] = []
    language = (
        data.get("metadata", {}).get("language_info", {}).get("name")
        or data.get("metadata", {}).get("kernelspec", {}).get("language")
        or "python"
    )
    for number, cell in enumerate(data.get("cells", []), start=1):
        source = "".join(cell.get("source", [])).strip()
        if not source:
            continue
        cell_type = cell.get("cell_type", "code")
        text = source if cell_type == "markdown" else f"```{language}\n{source}\n```"
        for output in cell.get("outputs", [])[:2]:
            captured = "".join(output.get("text", []))[:800]
            if captured.strip():
                text += f"\n\nOutput:\n{captured.strip()}"
        blocks.append(Block(text=text, kind=cell_type, anchor={"cell": number}))

    return Document(
        path=str(path), kind=KIND_NOTEBOOK, title=path.stem, blocks=blocks,
        meta={"language": language, "cell_count": len(blocks)},
    )
