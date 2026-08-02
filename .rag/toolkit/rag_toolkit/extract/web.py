"""HTML and EPUB extraction.

HTML is converted to a light Markdown so headings survive into the chunker. Navigation,
script, and style content is dropped — indexing a site's nav bar once per page is the
classic way to poison a retrieval index with near-duplicate chunks.
"""

from __future__ import annotations

import html as html_mod
import re
import zipfile
from pathlib import Path
from typing import Any

from . import KIND_MARKDOWN, Document, read_text_file

DROP_TAGS = ("script", "style", "nav", "footer", "header", "noscript", "svg", "form", "aside")
BLOCK_END = re.compile(r"</(p|div|section|article|li|tr|h[1-6]|blockquote|pre)\s*>", re.I)
HEADING = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.I | re.S)
LIST_ITEM = re.compile(r"<li[^>]*>(.*?)</li>", re.I | re.S)
TAG = re.compile(r"<[^>]+>")
BLANKS = re.compile(r"\n{3,}")


def html_to_markdown(raw: str) -> tuple[str, str]:
    """Return ``(title, markdown)``. Uses selectolax when present, regex otherwise."""
    title = ""
    match = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    if match:
        title = html_mod.unescape(TAG.sub("", match.group(1))).strip()

    try:
        from selectolax.parser import HTMLParser  # from the 'web' extra

        tree = HTMLParser(raw)
        for tag in DROP_TAGS:
            for node in tree.css(tag):
                node.decompose()
        for level in range(1, 7):
            for node in tree.css(f"h{level}"):
                node.replace_with(f"\n\n{'#' * level} {node.text(strip=True)}\n\n")
        for node in tree.css("li"):
            node.replace_with(f"\n- {node.text(strip=True)}")
        body = tree.body.text(separator="\n") if tree.body else tree.text(separator="\n")
        if not title and tree.css_first("h1"):
            title = tree.css_first("h1").text(strip=True)
        return title, BLANKS.sub("\n\n", body).strip()
    except Exception:
        pass  # selectolax absent or the tree was malformed — the regex path handles both

    text = raw
    for tag in DROP_TAGS:
        text = re.sub(rf"<{tag}\b.*?</{tag}>", " ", text, flags=re.I | re.S)
    text = HEADING.sub(lambda m: f"\n\n{'#' * int(m.group(1))} {TAG.sub('', m.group(2)).strip()}\n\n", text)
    text = LIST_ITEM.sub(lambda m: f"\n- {TAG.sub('', m.group(1)).strip()}", text)
    text = BLOCK_END.sub("\n\n", text)
    text = html_mod.unescape(TAG.sub("", text))
    text = BLANKS.sub("\n\n", "\n".join(line.strip() for line in text.splitlines()))
    return title, text.strip()


def extract_html(path: Path, **_: Any) -> Document:
    title, markdown = html_to_markdown(read_text_file(path))
    return Document(
        path=str(path), kind=KIND_MARKDOWN, title=title or path.stem, text=markdown,
        meta={"format": "html"},
    )


def extract_epub(path: Path, max_documents: int = 400, **_: Any) -> Document:
    """EPUB is a zip of XHTML. Concatenate the content documents in spine-ish order."""
    parts: list[str] = []
    title = ""
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith((".xhtml", ".html", ".htm"))]
        for name in sorted(names)[:max_documents]:
            try:
                raw = archive.read(name).decode("utf-8", errors="replace")
            except (KeyError, OSError):
                continue
            doc_title, markdown = html_to_markdown(raw)
            if markdown.strip():
                title = title or doc_title
                parts.append(markdown)
        for meta_name in ("OEBPS/content.opf", "content.opf"):
            if meta_name in archive.namelist() and not title:
                blob = archive.read(meta_name).decode("utf-8", errors="replace")
                found = re.search(r"<dc:title[^>]*>(.*?)</dc:title>", blob, re.I | re.S)
                if found:
                    title = TAG.sub("", found.group(1)).strip()

    return Document(
        path=str(path), kind=KIND_MARKDOWN, title=title or path.stem,
        text="\n\n".join(parts), meta={"format": "epub", "documents": len(parts)},
    )
