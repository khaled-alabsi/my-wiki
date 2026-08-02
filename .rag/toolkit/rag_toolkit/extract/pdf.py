"""PDF extraction via PyMuPDF — one block per page, so every hit cites a page number.

A PDF of scanned images yields almost no text. That is detected here and reported as
``meta['likely_scanned']`` rather than being passed off as a successful extraction;
``rag doctor --extract`` surfaces it and prints the OCR opt-in command.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import KIND_PAGED, Block, Document

# Below this many characters per page on average, the file is almost certainly scanned.
SCANNED_CHARS_PER_PAGE = 60

_OCR_ENGINE: Any = None


def _pymupdf() -> Any:
    """Import PyMuPDF under either of its two published module names."""
    try:
        import pymupdf  # 1.24+
        return pymupdf
    except ImportError:
        import fitz  # legacy name
        return fitz


def extract_pdf(path: Path, ocr: bool = False, max_pages: int = 5000, **_: Any) -> Document:
    pymupdf = _pymupdf()  # provided by the 'documents' extra

    doc = Document(path=str(path), kind=KIND_PAGED, title=path.stem)
    with pymupdf.open(path) as pdf:
        meta = pdf.metadata or {}
        doc.title = (meta.get("title") or "").strip() or path.stem
        doc.meta = {
            "page_count": pdf.page_count,
            "author": (meta.get("author") or "").strip(),
            "subject": (meta.get("subject") or "").strip(),
            "producer": (meta.get("producer") or "").strip(),
        }
        total_chars = 0
        for number, page in enumerate(pdf, start=1):
            if number > max_pages:
                doc.meta["truncated_at_page"] = max_pages
                break
            text = page.get_text("text").strip()
            if not text and ocr:
                text = _ocr_page(page)
            total_chars += len(text)
            if text:
                doc.blocks.append(Block(text=text, kind="page", anchor={"page": number}))

        pages = min(pdf.page_count, max_pages) or 1
        doc.meta["chars_per_page"] = round(total_chars / pages, 1)
        doc.meta["likely_scanned"] = total_chars / pages < SCANNED_CHARS_PER_PAGE
        doc.meta["ocr_used"] = bool(ocr)

    if doc.meta.get("likely_scanned") and not ocr:
        doc.error = (
            f"only {doc.meta['chars_per_page']} chars/page of extractable text — "
            "this PDF is probably scanned images. Enable OCR with corpus.ocr = true "
            "after installing the 'ocr' extra."
        )
    return doc


def _ocr_page(page: Any) -> str:
    """Rasterise one page and OCR it. Only called when corpus.ocr is enabled."""
    try:
        from rapidocr_onnxruntime import RapidOCR  # provided by the 'ocr' extra
    except ImportError:
        return ""

    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        _OCR_ENGINE = RapidOCR()
    pixmap = page.get_pixmap(dpi=200)
    result, _ = _OCR_ENGINE(pixmap.tobytes("png"))
    if not result:
        return ""
    return "\n".join(line[1] for line in result if len(line) > 1)
