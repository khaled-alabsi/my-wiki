"""The importable Python API — what notebooks, scripts, the web UI, and MCP all use.

    from rag_toolkit import Index

    with Index.find() as index:
        for hit in index.search("vendor onboarding", k=5):
            print(hit["citation"], hit["score"])

Models and the store load lazily on the first search, so constructing an ``Index`` is
cheap and importing this module costs nothing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from . import config as config_mod
from . import embed, rerank, retrieve, store as store_mod
from .index import Indexer
from .manifest import Manifest


class IndexNotBuiltError(RuntimeError):
    """The workspace exists but nothing has been indexed into it yet."""


class Index:
    """A handle on one ``.rag`` workspace."""

    def __init__(self, rag_dir: str | Path) -> None:
        self.rag_dir = Path(rag_dir).resolve()
        self.cfg = config_mod.load(self.rag_dir)
        self.paths = config_mod.layout(self.rag_dir, self.cfg)  # cfg first: it may relocate paths
        self._embedder: Any = None
        self._store: store_mod.BaseStore | None = None
        self._reranker: Any = None

    # ----------------------------------------------------------------- construction

    @classmethod
    def find(cls, start: str | Path | None = None) -> "Index":
        """Walk upward from *start* to the nearest ``.rag`` workspace."""
        found = config_mod.find_rag_dir(start)
        if found is None:
            raise FileNotFoundError(
                f"no .rag workspace at or above {Path(start or Path.cwd()).resolve()} — "
                "run 'rag init' there first"
            )
        return cls(found)

    @classmethod
    def at(cls, project_root: str | Path) -> "Index":
        return cls(config_mod.rag_dir_for(project_root))

    def __enter__(self) -> "Index":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        if self._store is not None:
            self._store.close()
            self._store = None

    # ----------------------------------------------------------------- lazy parts

    @property
    def embedder(self) -> Any:
        if self._embedder is None:
            self._embedder = embed.build(self.cfg, cache_dir=str(self.paths["cache"]))
        return self._embedder

    @property
    def store(self) -> store_mod.BaseStore:
        if self._store is None:
            if not self.paths["db"].exists():
                raise IndexNotBuiltError(
                    f"no index at {self.paths['db']} — run 'rag index' first"
                )
            self._store = store_mod.build(
                self.cfg, self.paths["db"], self.embedder.dimension, create=False
            )
        return self._store

    @property
    def reranker(self) -> Any:
        if self._reranker is None:
            self._reranker = rerank.build(self.cfg, cache_dir=str(self.paths["cache"]))
        return self._reranker

    # ----------------------------------------------------------------- reading

    def search_report(
        self,
        query: str,
        k: int = 0,
        path: str = "",
        ext: list[str] | str | None = None,
        source: str = "",
        since: str = "",
        rerank_results: bool | None = None,
        hybrid: bool | None = None,
    ) -> retrieve.SearchReport:
        """Full retrieval result, including what the pipeline actually did."""
        if isinstance(ext, str):
            ext = [e for e in ext.replace(",", " ").split() if e]
        filters = retrieve.Filters(
            path_glob=path, ext=list(ext or []), source=source, since=since
        )
        use_reranker = self.reranker if rerank_results is not False else None
        return retrieve.search(
            query, self.store, self.embedder, self.cfg,
            top_k=k, filters=filters, reranker=use_reranker, hybrid=hybrid,
        )

    def search(self, query: str, k: int = 0, max_chars: int = 0, **filters: Any) -> list[dict[str, Any]]:
        """Ranked hits as plain dicts — each one carries a citation."""
        report = self.search_report(query, k=k, **filters)
        return [retrieve.to_dict(hit, max_chars=max_chars) for hit in report.hits]

    def context_block(self, query: str, k: int = 8, max_chars: int = 1500) -> str:
        """Retrieved chunks formatted for pasting into a prompt, citations attached."""
        hits = self.search(query, k=k, max_chars=max_chars)
        if not hits:
            return f"No indexed content matched: {query}"
        parts = [f"# Retrieved for: {query}", ""]
        for number, hit in enumerate(hits, start=1):
            parts.append(f"## [{number}] {hit['citation']}  (score {hit['score']})")
            parts.append(hit["text"])
            parts.append("")
        return "\n".join(parts)

    def status(self) -> dict[str, Any]:
        """Index health without loading any model."""
        out: dict[str, Any] = {
            "rag_dir": str(self.rag_dir),
            "project_root": self.cfg.get("project", {}).get("root", ""),
            "sources": [
                {"name": s.get("name", ""), "path": s.get("path", "")}
                for s in self.cfg.get("sources", [])
            ],
            "embedding": self.cfg.get("embedding", {}),
            "store": self.cfg.get("store", {}),
            "retrieval": self.cfg.get("retrieval", {}),
            "indexed": False,
        }
        if not self.paths["manifest"].exists():
            out["message"] = "nothing indexed yet — run 'rag index'"
            return out
        with Manifest(self.paths["manifest"]) as manifest:
            out.update(manifest.stats())
            out["indexed"] = bool(out.get("chunks"))
            out["index_embedding"] = manifest.get_meta("embedding") or {}
            out["index_store"] = manifest.get_meta("store") or {}
        drift = out["index_embedding"].get("model")
        if drift and drift != out["embedding"].get("model"):
            out["warning"] = (
                f"config says '{out['embedding'].get('model')}' but the index was built with "
                f"'{drift}'. Searches will be wrong until you re-run 'rag index --full'."
            )
        return out

    def sources(self) -> list[dict[str, Any]]:
        return list(self.cfg.get("sources", []))

    def iter_documents(self) -> Iterator[dict[str, Any]]:
        with Manifest(self.paths["manifest"]) as manifest:
            yield from manifest.known_files().values()

    # ----------------------------------------------------------------- writing

    def build(self, full: bool = False, limit: int = 0, on_progress: Any = None) -> dict[str, Any]:
        """Run indexing in-process. This is the heavy call — it embeds the whole corpus."""
        self.close()
        indexer = Indexer(self.rag_dir, on_progress=on_progress)
        try:
            return indexer.run(full=full, limit=limit).as_dict()
        finally:
            indexer.close()

    def update(self, on_progress: Any = None) -> dict[str, Any]:
        return self.build(full=False, on_progress=on_progress)


def search(query: str, k: int = 10, start: str | Path | None = None, **filters: Any) -> list[dict[str, Any]]:
    """One-shot convenience: find the nearest workspace, search it, close it."""
    with Index.find(start) as index:
        return index.search(query, k=k, **filters)


def to_markdown(hits: list[dict[str, Any]], max_chars: int = 400) -> str:
    """Render hits as Markdown. Notebook-friendly: plain output, no widgets."""
    if not hits:
        return "_no matches_"
    lines: list[str] = []
    for number, hit in enumerate(hits, start=1):
        body = hit.get("text", "")
        if max_chars and len(body) > max_chars:
            body = body[:max_chars].rstrip() + "…"
        lines.append(f"**{number}. {hit['citation']}** — score `{hit['score']}` "
                     f"({hit['matched_by']})\n\n> " + body.replace("\n", "\n> ") + "\n")
    return "\n".join(lines)
