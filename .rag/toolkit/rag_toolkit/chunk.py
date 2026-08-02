"""Chunking: turn a ``Document`` into embeddable spans that each carry a real citation.

Two rules drive every strategy here:

*Respect structure.* A chunk that stops mid-sentence or mid-function retrieves badly.
Split at headings, definitions, pages, and paragraphs before falling back to characters.

*Anchor honestly.* A chunk's anchor points at the span it was primarily built from, not
at the overlap borrowed from its neighbour. A citation that is off by a page is worse
than no citation.
"""

from __future__ import annotations

import bisect
import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from .extract import KIND_CODE, KIND_MARKDOWN, Document

SEPARATORS = ["\n\n\n", "\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]
FENCE = re.compile(r"^\s*(```|~~~)")
ATX_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

# A line that plausibly starts a new top-level unit of code. Deliberately broad: a false
# positive costs one extra split, a false negative costs a chunk that straddles two units.
DEFINITION = re.compile(
    r"^\s{0,4}("
    r"(?:@\w|\[\w)"                                            # decorator / attribute
    r"|(?:public|private|protected|internal|static|final|abstract|override|async|export|declare)\s"
    r"|(?:def|class|struct|enum|interface|trait|impl|module|namespace|record|type)\s"
    r"|(?:func|fn|function|sub|proc|method)\s"
    r"|(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?(?:function|\()"
    r"|(?:CREATE|ALTER)\s+(?:TABLE|VIEW|PROCEDURE|FUNCTION|INDEX)\s"
    r")"
)


@dataclass
class Chunk:
    body: str  # the human-readable span, shown in results
    ordinal: int
    anchor: dict[str, Any] = field(default_factory=dict)
    heading_path: list[str] = field(default_factory=list)
    prefix: str = ""  # context line prepended for embedding only

    @property
    def embed_text(self) -> str:
        return f"{self.prefix}\n{self.body}" if self.prefix else self.body

    @property
    def hash(self) -> str:
        return hashlib.sha256(self.embed_text.encode("utf-8")).hexdigest()[:32]

    def id_for(self, path: str) -> str:
        seed = f"{path}\x00{self.ordinal}\x00{self.hash}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


# --------------------------------------------------------------------------- helpers


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for index, char in enumerate(text):
        if char == "\n":
            starts.append(index + 1)
    return starts


def _line_of(starts: list[int], offset: int) -> int:
    return bisect.bisect_right(starts, offset)


def _pack(segments: list[tuple[str, int]], target: int, overlap: int, minimum: int
          ) -> list[tuple[str, int, int]]:
    """Greedily pack ``(text, offset)`` segments into ``(text, start, end)`` spans.

    Segments carry their own trailing separator, so joining is lossless. The overlap
    borrowed from the previous span is *not* counted in ``start`` — the anchor points at
    where this chunk's own content begins.
    """
    out: list[tuple[str, int, int]] = []
    buffer: list[str] = []
    buffered = 0
    start: int | None = None
    end = 0
    for text, offset in segments:
        if not text.strip():
            continue
        if buffer and buffered + len(text) > target:
            joined = "".join(buffer)
            out.append((joined, start if start is not None else offset, end))
            carry = joined[-overlap:] if overlap else ""
            buffer = [carry] if carry.strip() else []
            buffered = len(carry) if carry.strip() else 0
            start = None
        if start is None:
            start = offset
        buffer.append(text)
        buffered += len(text)
        end = offset + len(text)
    if buffer:
        joined = "".join(buffer)
        if out and len(joined.strip()) < minimum:  # fold an orphan tail into its neighbour
            prev_text, prev_start, _ = out[-1]
            out[-1] = (prev_text + joined, prev_start, end)
        else:
            out.append((joined, start if start is not None else 0, end))
    return out


def _split_keep(text: str, separator: str) -> list[str]:
    """Split while keeping each separator attached to the piece before it."""
    parts = text.split(separator)
    return [p + separator for p in parts[:-1]] + parts[-1:]


def _split_long(text: str, offset: int, target: int, overlap: int, minimum: int
                ) -> list[tuple[str, int, int]]:
    """Recursively split an oversized span at the coarsest separator that works."""
    if len(text) <= target:
        return [(text, offset, offset + len(text))]
    for separator in SEPARATORS:
        if separator not in text:
            continue
        segments: list[tuple[str, int]] = []
        cursor = 0
        for piece in _split_keep(text, separator):
            segments.append((piece, offset + cursor))
            cursor += len(piece)
        if len(segments) > 1:
            packed = _pack(segments, target, overlap, minimum)
            if all(len(body) <= target * 1.6 for body, _, _ in packed):
                return packed
            break
    stride = max(target - overlap, target // 2, 1)
    return [
        (text[at : at + target], offset + at, offset + min(at + target, len(text)))
        for at in range(0, len(text), stride)
    ]


# --------------------------------------------------------------------------- strategies


def _markdown_sections(text: str) -> list[tuple[str, int, list[str]]]:
    """Split at ATX headings, carrying the full heading path. Fenced code is protected."""
    lines = text.splitlines(keepends=True)
    sections: list[tuple[str, int, list[str]]] = []
    stack: list[tuple[int, str]] = []
    buffer: list[str] = []
    offset = start = 0
    in_fence = False

    def flush(path: list[str]) -> None:
        if buffer and "".join(buffer).strip():
            sections.append(("".join(buffer), start, path))

    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
        heading = None if in_fence else ATX_HEADING.match(line.rstrip("\n"))
        if heading:
            flush([title for _, title in stack])
            level, title = len(heading.group(1)), heading.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            buffer, start = [line], offset
        else:
            buffer.append(line)
        offset += len(line)
    flush([title for _, title in stack])
    return sections


def _code_units(text: str) -> list[tuple[str, int]]:
    """Group source lines into units that start at a plausible definition boundary."""
    lines = text.splitlines(keepends=True)
    units: list[tuple[str, int]] = []
    buffer: list[str] = []
    offset = start = 0
    for line in lines:
        if DEFINITION.match(line) and buffer and "".join(buffer).strip():
            units.append(("".join(buffer), start))
            buffer, start = [], offset
        buffer.append(line)
        offset += len(line)
    if buffer and "".join(buffer).strip():
        units.append(("".join(buffer), start))
    return units or [(text, 0)]


# --------------------------------------------------------------------------- entry point


def chunk_document(doc: Document, cfg: dict[str, Any], rel_path: str = "") -> list[Chunk]:
    """Chunk a document according to its kind and the configured budgets."""
    settings = cfg.get("chunking", {})
    strategy = settings.get("strategy", "auto")
    target = int(settings.get("target_chars", 1800))
    overlap = int(settings.get("overlap_chars", 220))
    minimum = int(settings.get("min_chars", 120))
    with_prefix = bool(settings.get("prefix_context", True))
    kind = doc.kind if strategy == "auto" else strategy
    label = rel_path or doc.path

    chunks: list[Chunk] = []
    if doc.blocks:
        chunks = _chunk_blocks(doc, target, overlap, minimum)
    elif kind == KIND_MARKDOWN:
        chunks = _chunk_markdown(doc, target, overlap, minimum)
    elif kind == KIND_CODE:
        chunks = _chunk_code(doc, target, overlap, minimum)
    else:
        chunks = _chunk_plain(doc, target, overlap, minimum)

    kept: list[Chunk] = []
    for chunk in chunks:
        if len(chunk.body.strip()) < minimum and kept:
            kept[-1].body = f"{kept[-1].body}\n{chunk.body}"
            continue
        if not chunk.body.strip():
            continue
        chunk.ordinal = len(kept)
        if with_prefix:
            chunk.prefix = _context_line(label, doc, chunk)
        kept.append(chunk)
    return kept


def _context_line(label: str, doc: Document, chunk: Chunk) -> str:
    parts = [label]
    if doc.title and doc.title not in label:
        parts.append(doc.title)
    parts.extend(chunk.heading_path)
    anchor = chunk.anchor
    for key, prose in (("page", "page"), ("slide", "slide"), ("sheet", "sheet"), ("cell", "cell")):
        if key in anchor:
            parts.append(f"{prose} {anchor[key]}")

    trail: list[str] = []
    for part in (str(p).strip() for p in parts):
        if part and (not trail or part.casefold() != trail[-1].casefold()):
            trail.append(part)
    return " > ".join(trail)


def _chunk_markdown(doc: Document, target: int, overlap: int, minimum: int) -> list[Chunk]:
    starts = _line_starts(doc.text)
    out: list[Chunk] = []
    for section, offset, path in _markdown_sections(doc.text):
        for body, begin, end in _split_long(section, offset, target, overlap, minimum):
            out.append(Chunk(
                body=body.strip("\n"), ordinal=0, heading_path=path,
                anchor={"line_start": _line_of(starts, begin), "line_end": _line_of(starts, max(end - 1, begin))},
            ))
    return out


def _chunk_code(doc: Document, target: int, overlap: int, minimum: int) -> list[Chunk]:
    starts = _line_starts(doc.text)
    segments: list[tuple[str, int]] = []
    for unit, offset in _code_units(doc.text):
        if len(unit) <= target:
            segments.append((unit, offset))
        else:
            segments.extend((body, begin) for body, begin, _ in _split_long(unit, offset, target, overlap, minimum))
    out: list[Chunk] = []
    for body, begin, end in _pack(segments, target, overlap, minimum):
        out.append(Chunk(
            body=body.strip("\n"), ordinal=0,
            anchor={
                "line_start": _line_of(starts, begin),
                "line_end": _line_of(starts, max(end - 1, begin)),
                "language": doc.meta.get("language", ""),
            },
        ))
    return out


def _chunk_plain(doc: Document, target: int, overlap: int, minimum: int) -> list[Chunk]:
    starts = _line_starts(doc.text)
    return [
        Chunk(
            body=body.strip("\n"), ordinal=0,
            anchor={"line_start": _line_of(starts, begin), "line_end": _line_of(starts, max(end - 1, begin))},
        )
        for body, begin, end in _split_long(doc.text, 0, target, overlap, minimum)
    ]


def _chunk_blocks(doc: Document, target: int, overlap: int, minimum: int) -> list[Chunk]:
    """Pre-segmented documents (pages, slides, sheets, cells) keep their own anchors."""
    out: list[Chunk] = []
    for block in doc.blocks:
        if not block.text.strip():
            continue
        if len(block.text) <= target * 1.35:
            out.append(Chunk(body=block.text.strip(), ordinal=0, anchor=dict(block.anchor)))
            continue
        for part, (body, _, _) in enumerate(
            _split_long(block.text, 0, target, overlap, minimum), start=1
        ):
            anchor = dict(block.anchor)
            anchor["part"] = part
            out.append(Chunk(body=body.strip(), ordinal=0, anchor=anchor))
    return out


def chunk_hashes(chunks: Iterable[Chunk], path: str) -> list[tuple[str, int, str]]:
    return [(c.id_for(path), c.ordinal, c.hash) for c in chunks]
