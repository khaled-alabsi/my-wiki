"""Vector storage behind a two-method interface: upsert and search.

``lancedb``  a plain directory under ``.rag/db``. Upsert, delete-by-id, metadata filters,
             and full-text search in one embedded store — no server, no second index.
``numpy``    a fallback that keeps vectors in a single ``.npz`` and scans them. Correct at
             any size, fast enough to a few tens of thousands of chunks. It exists so a
             machine that cannot install lancedb is degraded, not blocked.

Both return the same ``Record`` shape, so nothing above this module knows which is in use.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

SCHEMA_FIELDS = (
    "chunk_id", "path", "rel_path", "source", "title", "ordinal", "text", "prefix",
    "heading_path", "anchor", "ext", "mtime",
)


@dataclass
class Record:
    chunk_id: str
    path: str
    rel_path: str
    source: str
    title: str
    ordinal: int
    text: str
    prefix: str = ""
    heading_path: str = ""  # " > " joined, kept as text so it is filterable and printable
    anchor: str = "{}"  # JSON, because vector stores dislike open-ended nested types
    ext: str = ""
    mtime: float = 0.0
    vector: list[float] = field(default_factory=list)

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        return data

    @property
    def anchor_dict(self) -> dict[str, Any]:
        try:
            return json.loads(self.anchor)
        except (ValueError, TypeError):
            return {}


@dataclass
class Hit:
    record: Record
    score: float
    source_of_match: str = "vector"  # "vector" | "text" | "hybrid" | "rerank"


class BaseStore:
    kind = "base"
    # True when the store applies a SQL `where` itself. When False, retrieve.py
    # over-fetches and post-filters in Python instead.
    supports_where = False

    def __init__(self, path: Path, dimension: int, table: str = "chunks") -> None:
        self.path = Path(path)
        self.dimension = dimension
        self.table = table

    def open(self, create: bool = True) -> "BaseStore":
        raise NotImplementedError

    def upsert(self, records: Sequence[Record]) -> int:
        raise NotImplementedError

    def delete(self, chunk_ids: Sequence[str]) -> int:
        raise NotImplementedError

    def delete_by_path(self, path: str) -> int:
        raise NotImplementedError

    def search_vector(self, vector: Sequence[float], k: int, where: str = "") -> list[Hit]:
        raise NotImplementedError

    def search_text(self, query: str, k: int, where: str = "") -> list[Hit]:
        return []

    def count(self) -> int:
        raise NotImplementedError

    def close(self) -> None:
        return None


# --------------------------------------------------------------------------- lancedb


class LanceStore(BaseStore):
    kind = "lancedb"
    supports_where = True

    def open(self, create: bool = True) -> "LanceStore":
        import lancedb
        import pyarrow as pa

        self.path.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(str(self.path))
        names = set(self._db.table_names())
        if self.table in names:
            self._table = self._db.open_table(self.table)
        elif create:
            schema = pa.schema([
                pa.field("chunk_id", pa.string()),
                pa.field("path", pa.string()),
                pa.field("rel_path", pa.string()),
                pa.field("source", pa.string()),
                pa.field("title", pa.string()),
                pa.field("ordinal", pa.int32()),
                pa.field("text", pa.string()),
                pa.field("prefix", pa.string()),
                pa.field("heading_path", pa.string()),
                pa.field("anchor", pa.string()),
                pa.field("ext", pa.string()),
                pa.field("mtime", pa.float64()),
                pa.field("vector", pa.list_(pa.float32(), self.dimension)),
            ])
            self._table = self._db.create_table(self.table, schema=schema)
        else:
            raise FileNotFoundError(f"no table '{self.table}' in {self.path}")
        return self

    def upsert(self, records: Sequence[Record]) -> int:
        if not records:
            return 0
        rows = [r.payload() for r in records]
        (
            self._table.merge_insert("chunk_id")
            .when_matched_update_all()
            .when_not_matched_insert_all()
            .execute(rows)
        )
        return len(rows)

    def delete(self, chunk_ids: Sequence[str]) -> int:
        if not chunk_ids:
            return 0
        for batch in _chunked(list(chunk_ids), 500):
            quoted = ", ".join(f"'{cid}'" for cid in batch)
            self._table.delete(f"chunk_id IN ({quoted})")
        return len(chunk_ids)

    def delete_by_path(self, path: str) -> int:
        self._table.delete(f"path = '{_escape(path)}'")
        return 1

    def search_vector(self, vector: Sequence[float], k: int, where: str = "") -> list[Hit]:
        query = self._table.search(list(vector), vector_column_name="vector").limit(k)
        if where:
            query = query.where(where, prefilter=True)
        return [
            Hit(_record_from(row), score=_distance_to_score(row.get("_distance")), source_of_match="vector")
            for row in query.to_list()
        ]

    def search_text(self, query: str, k: int, where: str = "") -> list[Hit]:
        try:
            search = self._table.search(query, query_type="fts").limit(k)
            if where:
                search = search.where(where, prefilter=True)
            rows = search.to_list()
        except Exception:
            return []  # no FTS index yet; hybrid degrades to dense-only and doctor says so
        return [
            Hit(_record_from(row), score=float(row.get("_score", 0.0)), source_of_match="text")
            for row in rows
        ]

    def ensure_fts(self, replace: bool = True) -> bool:
        """Build the full-text index. Without it, hybrid retrieval is dense-only.

        lancedb's native FTS indexes one column per index, so ``text`` and ``prefix``
        each get their own. A query with ``query_type="fts"`` that names no column
        still searches both, which is what the old single multi-column call meant.

        ``text`` carries the content and is what keyword retrieval depends on, so a
        failure there is a real failure. ``prefix`` holds the path and heading trail —
        useful for matching a heading by name, but a bonus rather than a requirement.
        """
        if not self._create_fts_column("text", replace):
            try:  # lancedb before 0.25 took every column in one call
                self._table.create_fts_index(["text", "prefix"], replace=replace)
                return True
            except Exception:
                return False
        self._create_fts_column("prefix", replace)
        return True

    def _create_fts_column(self, column: str, replace: bool) -> bool:
        """Create a single-column FTS index, tolerating the API rename in 0.25."""
        try:
            from lancedb.index import FTS

            self._table.create_index(column, config=FTS(), replace=replace)
            return True
        except Exception:
            pass
        try:  # deprecated since 0.25, still functional
            self._table.create_fts_index(column, replace=replace)
            return True
        except Exception:
            return False

    def ensure_vector_index(self, min_rows: int = 20_000) -> bool:
        """An ANN index only pays off past a few tens of thousands of rows."""
        if self.count() < min_rows:
            return False
        try:
            self._table.create_index(metric="cosine", replace=True)
            return True
        except Exception:
            return False

    def count(self) -> int:
        return int(self._table.count_rows())


def _distance_to_score(distance: Any) -> float:
    """LanceDB returns a cosine *distance*; callers everywhere expect similarity."""
    try:
        return round(1.0 - float(distance), 6)
    except (TypeError, ValueError):
        return 0.0


def _record_from(row: dict[str, Any]) -> Record:
    return Record(**{key: row.get(key, _DEFAULTS[key]) for key in SCHEMA_FIELDS})


_DEFAULTS: dict[str, Any] = {
    "chunk_id": "", "path": "", "rel_path": "", "source": "", "title": "", "ordinal": 0,
    "text": "", "prefix": "", "heading_path": "", "anchor": "{}", "ext": "", "mtime": 0.0,
}


def _escape(value: str) -> str:
    return value.replace("'", "''")


def _chunked(items: list[Any], size: int) -> Iterable[list[Any]]:
    for at in range(0, len(items), size):
        yield items[at : at + size]


# --------------------------------------------------------------------------- numpy fallback


class NumpyStore(BaseStore):
    """Flat cosine scan over an in-memory matrix, persisted as a pickle plus an .npy."""

    kind = "numpy"
    supports_where = False

    def open(self, create: bool = True) -> "NumpyStore":
        import numpy as np

        self._np = np
        self.path.mkdir(parents=True, exist_ok=True)
        self._meta_file = self.path / f"{self.table}.meta.pkl"
        self._vec_file = self.path / f"{self.table}.vectors.npy"
        if self._meta_file.exists() and self._vec_file.exists():
            with self._meta_file.open("rb") as handle:
                self._rows: list[dict[str, Any]] = pickle.load(handle)
            self._vectors = np.load(self._vec_file)
        elif create:
            self._rows, self._vectors = [], np.zeros((0, self.dimension), dtype="float32")
        else:
            raise FileNotFoundError(f"no store at {self._meta_file}")
        self._index = {row["chunk_id"]: at for at, row in enumerate(self._rows)}
        return self

    def upsert(self, records: Sequence[Record]) -> int:
        np = self._np
        keep = [r for r in records if r.chunk_id not in self._index]
        replace = [r for r in records if r.chunk_id in self._index]
        for record in replace:
            at = self._index[record.chunk_id]
            self._rows[at] = record.payload()
            self._vectors[at] = np.asarray(record.vector, dtype="float32")
        if keep:
            block = np.asarray([r.vector for r in keep], dtype="float32")
            self._vectors = np.vstack([self._vectors, block]) if len(self._vectors) else block
            for record in keep:
                self._index[record.chunk_id] = len(self._rows)
                self._rows.append(record.payload())
        return len(records)

    def delete(self, chunk_ids: Sequence[str]) -> int:
        drop = {self._index[cid] for cid in chunk_ids if cid in self._index}
        if not drop:
            return 0
        keep = [at for at in range(len(self._rows)) if at not in drop]
        self._rows = [self._rows[at] for at in keep]
        self._vectors = self._vectors[keep] if keep else self._np.zeros((0, self.dimension), "float32")
        self._index = {row["chunk_id"]: at for at, row in enumerate(self._rows)}
        return len(drop)

    def delete_by_path(self, path: str) -> int:
        return self.delete([row["chunk_id"] for row in self._rows if row.get("path") == path])

    def search_vector(self, vector: Sequence[float], k: int, where: str = "") -> list[Hit]:
        np = self._np
        if not len(self._vectors):
            return []
        query = np.asarray(vector, dtype="float32")
        norms = np.linalg.norm(self._vectors, axis=1) * (np.linalg.norm(query) or 1.0)
        scores = (self._vectors @ query) / np.where(norms == 0, 1.0, norms)
        order = np.argsort(-scores)[: max(k, 1)]
        return [
            Hit(Record(**{f: self._rows[at].get(f, _DEFAULTS[f]) for f in SCHEMA_FIELDS}),
                score=round(float(scores[at]), 6), source_of_match="vector")
            for at in order
        ]

    def search_text(self, query: str, k: int, where: str = "") -> list[Hit]:
        """Token-overlap scan. Crude next to BM25, but it keeps hybrid working."""
        terms = {t for t in query.lower().split() if len(t) > 2}
        if not terms:
            return []
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in self._rows:
            haystack = f"{row.get('prefix', '')} {row.get('text', '')}".lower()
            overlap = sum(1 for term in terms if term in haystack)
            if overlap:
                scored.append((overlap / len(terms), row))
        scored.sort(key=lambda pair: -pair[0])
        return [
            Hit(Record(**{f: row.get(f, _DEFAULTS[f]) for f in SCHEMA_FIELDS}),
                score=round(score, 6), source_of_match="text")
            for score, row in scored[:k]
        ]

    def count(self) -> int:
        return len(self._rows)

    def flush(self) -> None:
        with self._meta_file.open("wb") as handle:
            pickle.dump(self._rows, handle, protocol=pickle.HIGHEST_PROTOCOL)
        self._np.save(self._vec_file, self._vectors)

    def close(self) -> None:
        self.flush()


STORES: dict[str, type[BaseStore]] = {"lancedb": LanceStore, "numpy": NumpyStore}


def build(cfg: dict[str, Any], db_path: Path, dimension: int, create: bool = True) -> BaseStore:
    kind = cfg.get("store", {}).get("kind", "lancedb")
    table = cfg.get("store", {}).get("table", "chunks")
    if kind not in STORES:
        raise ValueError(f"unknown store kind '{kind}' — expected one of {sorted(STORES)}")
    if kind == "lancedb":
        try:
            return LanceStore(db_path, dimension, table).open(create=create)
        except ImportError:
            kind = "numpy"  # honest degradation; doctor reports which store is live
    return STORES[kind](db_path, dimension, table).open(create=create)
