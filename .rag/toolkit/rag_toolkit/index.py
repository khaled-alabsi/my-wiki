"""The indexing pipeline: discover, extract, chunk, embed, store.

Resumability is a property of the data, not of a checkpoint file. Every file is committed
to the manifest immediately after its chunks land in the store, so a killed run loses at
most the file it was working on. Re-running skips anything whose content hash still
matches, which is also exactly what makes ``rag update`` cheap.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator

from . import chunk as chunker
from . import config as config_mod
from . import discover, embed, extract, store as store_mod
from .manifest import FileLock, Manifest

FLUSH_EVERY = 200  # files, for stores that persist on flush rather than on write


@dataclass
class IndexStats:
    scanned: int = 0
    indexed: int = 0
    skipped_unchanged: int = 0
    removed: int = 0
    failed: int = 0
    empty: int = 0
    chunks_written: int = 0
    chunks_deleted: int = 0
    bytes_read: int = 0
    seconds: float = 0.0
    failures: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        data = {k: v for k, v in self.__dict__.items() if k != "failures"}
        data["seconds"] = round(self.seconds, 1)
        data["failures"] = self.failures[:25]
        data["failure_count"] = len(self.failures)
        return data


def file_hash(path: Path, block: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(block):
            digest.update(chunk)
    return digest.hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Indexer:
    """One index run. Construct, call ``run()``, then ``close()``."""

    def __init__(
        self,
        rag_dir: Path,
        cfg: dict[str, Any] | None = None,
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.rag_dir = Path(rag_dir)
        self.cfg = cfg or config_mod.load(self.rag_dir)
        self.paths = config_mod.layout(self.rag_dir, self.cfg)  # cfg first: it may relocate paths
        self.on_progress = on_progress or (lambda event, data: None)
        self.stats = IndexStats()
        self.embedder: Any = None
        self.store: store_mod.BaseStore | None = None

    # ----------------------------------------------------------------- setup

    def prepare(self) -> None:
        self.embedder = embed.build(self.cfg, cache_dir=str(self.paths["cache"]))
        dimension = self.embedder.dimension
        recorded = int(self.cfg.get("embedding", {}).get("dimension", 0))
        if recorded != dimension:
            self.cfg.setdefault("embedding", {})["dimension"] = dimension
            config_mod.save(self.cfg, self.rag_dir)
            self.on_progress("dimension_corrected", {"was": recorded, "now": dimension})
        self.store = store_mod.build(self.cfg, self.paths["db"], dimension, create=True)

    def close(self) -> None:
        if self.store is not None:
            self.store.close()

    # ----------------------------------------------------------------- run

    def run(self, full: bool = False, limit: int = 0) -> IndexStats:
        started = time.time()
        with FileLock(self.paths["lock"]), Manifest(self.paths["manifest"]) as manifest:
            self._guard_model_change(manifest, full)
            self.prepare()
            assert self.store is not None

            with manifest.run("full" if full else "incremental") as run_stats:
                known = manifest.known_files()
                seen: set[str] = set()
                processed = 0

                for candidate in discover.iter_files(self.cfg, self.rag_dir):
                    key = str(candidate.path)
                    seen.add(key)
                    self.stats.scanned += 1
                    record = known.get(key)
                    if not full and self._unchanged(record, candidate):
                        self.stats.skipped_unchanged += 1
                        continue
                    self._index_one(candidate, manifest)
                    processed += 1
                    if processed % FLUSH_EVERY == 0:
                        self._flush()
                    if limit and processed >= limit:
                        self.on_progress("limit_reached", {"limit": limit})
                        break

                if not limit:
                    self._remove_missing(known, seen, manifest)

                manifest.set_meta("embedding", self.embedder.describe())
                manifest.set_meta("store", {"kind": self.store.kind, "count": self.store.count()})
                self._build_indexes()
                self._flush()
                self.stats.seconds = time.time() - started
                run_stats.update(self.stats.as_dict())

        return self.stats

    def _guard_model_change(self, manifest: Manifest, full: bool) -> None:
        """A different embedding model makes every stored vector meaningless."""
        previous = manifest.get_meta("embedding") or {}
        current = self.cfg.get("embedding", {})
        changed = previous and previous.get("model") and previous["model"] != current.get("model")
        if changed and not full:
            raise RuntimeError(
                f"the index was built with '{previous['model']}' but the config now says "
                f"'{current.get('model')}'. Vectors from two models are not comparable. "
                f"Re-run with --full to rebuild, or put the old model back in config.toml."
            )

    @staticmethod
    def _unchanged(record: dict[str, Any] | None, candidate: discover.Candidate) -> bool:
        if not record or record.get("status") not in {"indexed", "empty"}:
            return False
        return (
            int(record.get("size", -1)) == candidate.size
            and abs(float(record.get("mtime", 0)) - candidate.mtime) < 1e-6
        )

    # ----------------------------------------------------------------- one file

    def _index_one(self, candidate: discover.Candidate, manifest: Manifest) -> None:
        assert self.store is not None
        path = candidate.path
        base = {
            "path": str(path), "source": candidate.source, "rel_path": candidate.rel_path,
            "size": candidate.size, "mtime": candidate.mtime,
        }
        self.stats.bytes_read += candidate.size

        doc = extract.extract(path, ocr=bool(self.cfg.get("corpus", {}).get("ocr", False)))
        if doc.error and doc.is_empty:
            self.stats.failed += 1
            if len(self.stats.failures) < 200:
                self.stats.failures.append({"path": candidate.rel_path, "error": doc.error})
            self._drop_chunks(str(path), manifest)
            manifest.record_file(**base, status="failed", error=doc.error,
                                 extractor=doc.extractor, n_chunks=0, content_hash="")
            manifest.conn.commit()
            self.on_progress("failed", {"path": candidate.rel_path, "error": doc.error})
            return

        content = doc.text if doc.text else "\n\n".join(b.text for b in doc.blocks)
        digest = text_hash(content)
        chunks = chunker.chunk_document(doc, self.cfg, rel_path=candidate.rel_path)

        if not chunks:
            self.stats.empty += 1
            self._drop_chunks(str(path), manifest)
            manifest.record_file(**base, status="empty", error=doc.error, extractor=doc.extractor,
                                 n_chunks=0, content_hash=digest)
            manifest.conn.commit()
            return

        records = self._records(candidate, doc, chunks)
        # Embed exactly the text the chunk id was hashed from, so ids and vectors agree.
        vectors = self._embed([piece.embed_text for piece in chunks])
        for record, vector in zip(records, vectors):
            record.vector = vector

        stale = manifest.replace_chunks(
            str(path), chunker.chunk_hashes(chunks, str(path))
        )
        fresh = {r.chunk_id for r in records}
        removable = [cid for cid in stale if cid not in fresh]
        if removable:
            self.store.delete(removable)
            self.stats.chunks_deleted += len(removable)
        self.store.upsert(records)

        manifest.record_file(**base, status="indexed", error=doc.error or "",
                             extractor=doc.extractor, n_chunks=len(records), content_hash=digest)
        manifest.conn.commit()
        self.stats.indexed += 1
        self.stats.chunks_written += len(records)
        self.on_progress("indexed", {"path": candidate.rel_path, "chunks": len(records)})

    def _records(
        self, candidate: discover.Candidate, doc: extract.Document, chunks: list[chunker.Chunk]
    ) -> list[store_mod.Record]:
        return [
            store_mod.Record(
                chunk_id=piece.id_for(str(candidate.path)),
                path=str(candidate.path),
                rel_path=candidate.rel_path,
                source=candidate.source,
                title=doc.title,
                ordinal=piece.ordinal,
                text=piece.body,
                prefix=piece.prefix,
                heading_path=" > ".join(piece.heading_path),
                anchor=json.dumps(piece.anchor, ensure_ascii=False),
                ext=candidate.ext,
                mtime=candidate.mtime,
            )
            for piece in chunks
        ]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        batch = max(1, int(self.cfg.get("embedding", {}).get("batch_size", 32)))
        out: list[list[float]] = []
        for at in range(0, len(texts), batch):
            out.extend(self.embedder.embed_documents(texts[at : at + batch]))
        return out

    # ----------------------------------------------------------------- cleanup

    def _drop_chunks(self, path: str, manifest: Manifest) -> None:
        assert self.store is not None
        stale = manifest.chunk_ids(path)
        if stale:
            self.store.delete(stale)
            self.stats.chunks_deleted += len(stale)
        manifest.conn.execute("DELETE FROM chunks WHERE path = ?", (path,))

    def _remove_missing(self, known: dict[str, Any], seen: set[str], manifest: Manifest) -> None:
        for path in set(known) - seen:
            stale = manifest.forget_file(path)
            if stale and self.store is not None:
                self.store.delete(stale)
                self.stats.chunks_deleted += len(stale)
            self.stats.removed += 1
        manifest.conn.commit()

    def _build_indexes(self) -> None:
        if isinstance(self.store, store_mod.LanceStore):
            self.on_progress("fts_index", {"built": self.store.ensure_fts()})
            self.on_progress("ann_index", {"built": self.store.ensure_vector_index()})

    def _flush(self) -> None:
        flush = getattr(self.store, "flush", None)
        if callable(flush):
            flush()


def run_index(
    rag_dir: Path,
    full: bool = False,
    limit: int = 0,
    on_progress: Callable[[str, dict[str, Any]], None] | None = None,
) -> IndexStats:
    indexer = Indexer(rag_dir, on_progress=on_progress)
    try:
        return indexer.run(full=full, limit=limit)
    finally:
        indexer.close()


def iter_progress_lines(stats: IndexStats) -> Iterator[str]:
    yield f"scanned            {stats.scanned}"
    yield f"indexed            {stats.indexed}"
    yield f"unchanged          {stats.skipped_unchanged}"
    yield f"removed            {stats.removed}"
    yield f"empty              {stats.empty}"
    yield f"failed             {stats.failed}"
    yield f"chunks written     {stats.chunks_written}"
    yield f"chunks deleted     {stats.chunks_deleted}"
    yield f"elapsed            {stats.seconds:.1f}s"
