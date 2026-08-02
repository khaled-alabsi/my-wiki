"""Retrieval: filters, hybrid fusion, reranking, and citation formatting.

The pipeline is dense search plus full-text search, fused with Reciprocal Rank Fusion,
then optionally reranked by a cross-encoder.

RRF is used rather than score addition on purpose: dense cosine similarity and BM25
scores live on different, non-comparable scales, and normalising them per query is
unstable. RRF only reads *ranks*, so it cannot be skewed by one retriever's score range.
"""

from __future__ import annotations

import datetime as _dt
import fnmatch
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from .store import BaseStore, Hit


@dataclass
class Filters:
    """Structured filters, translated per store — SQL for LanceDB, a predicate otherwise."""

    path_glob: str = ""
    ext: list[str] = field(default_factory=list)
    source: str = ""
    since: str = ""  # ISO date; matches file mtime

    def is_empty(self) -> bool:
        return not (self.path_glob or self.ext or self.source or self.since)

    def since_epoch(self) -> float:
        if not self.since:
            return 0.0
        try:
            return _dt.datetime.fromisoformat(self.since).timestamp()
        except ValueError:
            return 0.0

    def to_sql(self) -> str:
        clauses: list[str] = []
        if self.source:
            clauses.append(f"source = '{_q(self.source)}'")
        if self.ext:
            joined = ", ".join(f"'{_q(_dot(e))}'" for e in self.ext)
            clauses.append(f"ext IN ({joined})")
        if self.since_epoch():
            clauses.append(f"mtime >= {self.since_epoch()}")
        if self.path_glob:
            # LanceDB's filter dialect has LIKE but not glob; translate the common forms.
            like = self.path_glob.replace("*", "%").replace("?", "_")
            clauses.append(f"rel_path LIKE '{_q(like)}'")
        return " AND ".join(clauses)

    def to_predicate(self) -> Callable[[Hit], bool]:
        since = self.since_epoch()
        exts = {_dot(e) for e in self.ext}

        def predicate(hit: Hit) -> bool:
            record = hit.record
            if self.source and record.source != self.source:
                return False
            if exts and record.ext not in exts:
                return False
            if since and record.mtime < since:
                return False
            if self.path_glob and not fnmatch.fnmatch(record.rel_path, self.path_glob):
                return False
            return True

        return predicate


def _q(value: str) -> str:
    return value.replace("'", "''")


def _dot(ext: str) -> str:
    ext = ext.strip().lower()
    return ext if ext.startswith(".") or not ext else f".{ext}"


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[Hit]], k: int = 60, weights: Sequence[float] | None = None
) -> list[Hit]:
    """Fuse ranked lists by 1/(k + rank). Only order matters, never the raw scores."""
    weights = list(weights or [1.0] * len(rankings))
    fused: dict[str, float] = {}
    best: dict[str, Hit] = {}
    origin: dict[str, set[str]] = {}

    for ranking, weight in zip(rankings, weights):
        for rank, hit in enumerate(ranking, start=1):
            key = hit.record.chunk_id or f"{hit.record.path}#{hit.record.ordinal}"
            fused[key] = fused.get(key, 0.0) + weight / (k + rank)
            origin.setdefault(key, set()).add(hit.source_of_match)
            if key not in best:
                best[key] = hit

    out: list[Hit] = []
    for key, score in sorted(fused.items(), key=lambda kv: -kv[1]):
        hit = best[key]
        matched = origin.get(key, {hit.source_of_match})
        out.append(Hit(
            hit.record,
            score=round(score, 6),
            source_of_match="hybrid" if len(matched) > 1 else hit.source_of_match,
        ))
    return out


@dataclass
class SearchReport:
    hits: list[Hit]
    query: str
    dense_count: int = 0
    text_count: int = 0
    fused_count: int = 0
    reranked: bool = False
    notes: list[str] = field(default_factory=list)


def search(
    query: str,
    store: BaseStore,
    embedder: Any,
    cfg: dict[str, Any],
    top_k: int = 0,
    filters: Filters | None = None,
    reranker: Any = None,
    hybrid: bool | None = None,
) -> SearchReport:
    """Run the full retrieval pipeline and return hits plus what actually happened."""
    settings = cfg.get("retrieval", {})
    top_k = top_k or int(settings.get("top_k", 10))
    candidates = max(int(settings.get("candidates", 60)), top_k)
    use_hybrid = settings.get("hybrid", True) if hybrid is None else hybrid
    rrf_k = int(settings.get("rrf_k", 60))
    filters = filters or Filters()
    notes: list[str] = []

    where = ""
    post_filter: Callable[[Hit], bool] | None = None
    if not filters.is_empty():
        if store.supports_where:
            where = filters.to_sql()
        else:
            post_filter = filters.to_predicate()
            candidates *= 3  # over-fetch, because filtering happens after retrieval
            notes.append(f"{store.kind} store filters in Python after retrieval")

    vector = embedder.embed_query(query)
    dense = store.search_vector(vector, candidates, where)

    text: list[Hit] = []
    if use_hybrid:
        text = store.search_text(query, candidates, where)
        if not text:
            notes.append("full-text search returned nothing — check 'rag doctor' for the FTS index")

    if post_filter:
        dense = [hit for hit in dense if post_filter(hit)]
        text = [hit for hit in text if post_filter(hit)]

    fused = reciprocal_rank_fusion([dense, text], k=rrf_k) if text else dense
    report = SearchReport(
        hits=[], query=query, dense_count=len(dense), text_count=len(text),
        fused_count=len(fused), notes=notes,
    )

    active = reranker is not None and getattr(reranker, "name", "none") != "none"
    if active:
        pool = fused[: int(settings.get("rerank_candidates", 40))]
        report.hits = reranker.rerank(query, pool, top_k)
        report.reranked = True
    else:
        report.hits = fused[:top_k]
        reason = getattr(reranker, "reason", "") if reranker is not None else ""
        if reason:
            notes.append(f"reranking off: {reason}")

    return report


# --------------------------------------------------------------------------- citations


def citation(hit: Hit) -> str:
    """A short, copy-pasteable pointer at exactly where this text came from."""
    record = hit.record
    anchor = record.anchor_dict
    where = record.rel_path or record.path

    if "page" in anchor:
        where += f" p.{anchor['page']}"
    elif "slide" in anchor:
        where += f" slide {anchor['slide']}"
    elif "sheet" in anchor:
        rows = ""
        if "row_start" in anchor:
            rows = f" rows {anchor['row_start']}-{anchor.get('row_end', anchor['row_start'])}"
        where += f" [{anchor['sheet']}]{rows}"
    elif "cell" in anchor:
        where += f" cell {anchor['cell']}"
    elif "line_start" in anchor:
        start, end = anchor["line_start"], anchor.get("line_end", anchor["line_start"])
        where += f":{start}" + (f"-{end}" if end != start else "")

    if anchor.get("part"):
        where += f" (part {anchor['part']})"
    if record.heading_path:
        where += f" — {record.heading_path}"
    return where


def to_dict(hit: Hit, include_text: bool = True, max_chars: int = 0) -> dict[str, Any]:
    record = hit.record
    body = record.text
    if max_chars and len(body) > max_chars:
        body = body[:max_chars].rstrip() + "…"
    out: dict[str, Any] = {
        "chunk_id": record.chunk_id,
        "score": hit.score,
        "matched_by": hit.source_of_match,
        "citation": citation(hit),
        "path": record.path,
        "rel_path": record.rel_path,
        "source": record.source,
        "title": record.title,
        "heading_path": record.heading_path,
        "anchor": record.anchor_dict,
    }
    if include_text:
        out["text"] = body
    return out
