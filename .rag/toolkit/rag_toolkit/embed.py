"""Embedding backends behind one interface.

Three backends, chosen by ``models.py`` and recorded in ``config.toml``:

``fastembed``              ONNX, no torch, ~200 MB, the right default on CPU and Windows.
``sentence-transformers``  torch, uses MPS or CUDA, needed for the large tier and rerankers.
``api``                    hosted, opt-in only — it sends corpus text off the machine.

Every backend reports its **real** dimension after loading. Nothing trusts the advisory
value in the registry, so a stale registry entry can never corrupt a store.
"""

from __future__ import annotations

import math
import os
from typing import Any, Iterable, Sequence

Vector = list[float]


def l2_normalize(vector: Vector) -> Vector:
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector] if norm else vector


class Embedder:
    """Base interface. ``dimension`` is only valid after ``load()``."""

    name = "base"

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.model_id: str = cfg.get("model", "")
        self.batch_size: int = int(cfg.get("batch_size", 32))
        self.query_prefix: str = cfg.get("query_prefix", "") or ""
        self.document_prefix: str = cfg.get("document_prefix", "") or ""
        self.normalize: bool = bool(cfg.get("normalize", True))
        self.device: str = cfg.get("device", "cpu")
        self.trust_remote_code: bool = bool(cfg.get("trust_remote_code", False))
        self.cache_dir: str = cfg.get("cache_dir", "") or ""
        self._dimension = 0

    @property
    def dimension(self) -> int:
        if not self._dimension:
            raise RuntimeError("call load() before reading dimension")
        return self._dimension

    def load(self) -> "Embedder":
        raise NotImplementedError

    def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        raise NotImplementedError

    def embed_query(self, text: str) -> Vector:
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {
            "backend": self.name,
            "model": self.model_id,
            "dimension": self._dimension,
            "device": self.device,
            "batch_size": self.batch_size,
            "query_prefix": self.query_prefix,
            "document_prefix": self.document_prefix,
        }


class FastEmbedEmbedder(Embedder):
    name = "fastembed"

    def load(self) -> "Embedder":
        from fastembed import TextEmbedding  # from the 'onnx' extra

        kwargs: dict[str, Any] = {"model_name": self.model_id}
        if self.cache_dir:
            kwargs["cache_dir"] = self.cache_dir
        self._model = TextEmbedding(**kwargs)
        probe = next(iter(self._model.embed(["dimension probe"])))
        self._dimension = len(probe)
        return self

    def _run(self, texts: Sequence[str]) -> list[Vector]:
        vectors = self._model.embed(list(texts), batch_size=self.batch_size)
        out = [[float(v) for v in vec] for vec in vectors]
        return [l2_normalize(v) for v in out] if self.normalize else out

    def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        return self._run([f"{self.document_prefix}{t}" for t in texts])

    def embed_query(self, text: str) -> Vector:
        return self._run([f"{self.query_prefix}{text}"])[0]


class SentenceTransformerEmbedder(Embedder):
    name = "sentence-transformers"

    def load(self) -> "Embedder":
        from sentence_transformers import SentenceTransformer  # from the 'torch' extra

        kwargs: dict[str, Any] = {"device": self.device or None}
        if self.cache_dir:
            kwargs["cache_folder"] = self.cache_dir
        if self.trust_remote_code:
            kwargs["trust_remote_code"] = True
        self._model = SentenceTransformer(self.model_id, **kwargs)
        self._dimension = int(self._model.get_sentence_embedding_dimension() or 0)
        if not self._dimension:  # some remote-code models only report after a forward pass
            self._dimension = len(self._model.encode("dimension probe"))
        return self

    def _run(self, texts: Sequence[str]) -> list[Vector]:
        vectors = self._model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [[float(v) for v in vec] for vec in vectors]

    def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        return self._run([f"{self.document_prefix}{t}" for t in texts])

    def embed_query(self, text: str) -> Vector:
        return self._run([f"{self.query_prefix}{text}"])[0]


class ApiEmbedder(Embedder):
    """OpenAI-compatible embeddings endpoint. Opt-in: this sends corpus text to a vendor."""

    name = "api"

    def load(self) -> "Embedder":
        import httpx  # from the 'api' extra

        self.base_url = os.environ.get("RAG_EMBED_BASE_URL", "https://api.openai.com/v1")
        key = os.environ.get("RAG_EMBED_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "the 'api' backend needs RAG_EMBED_API_KEY (or OPENAI_API_KEY) in the environment"
            )
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {key}"},
            timeout=120.0,
        )
        self._dimension = len(self._post(["dimension probe"])[0])
        return self

    def _post(self, texts: Sequence[str]) -> list[Vector]:
        response = self._client.post(
            "/embeddings", json={"model": self.model_id, "input": list(texts)}
        )
        response.raise_for_status()
        payload = response.json()
        rows = sorted(payload["data"], key=lambda row: row.get("index", 0))
        out = [[float(v) for v in row["embedding"]] for row in rows]
        return [l2_normalize(v) for v in out] if self.normalize else out

    def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        out: list[Vector] = []
        batch = max(1, self.batch_size)
        for at in range(0, len(texts), batch):
            out.extend(self._post([f"{self.document_prefix}{t}" for t in texts[at : at + batch]]))
        return out

    def embed_query(self, text: str) -> Vector:
        return self._post([f"{self.query_prefix}{text}"])[0]


BACKENDS: dict[str, type[Embedder]] = {
    "fastembed": FastEmbedEmbedder,
    "sentence-transformers": SentenceTransformerEmbedder,
    "api": ApiEmbedder,
}


def build(cfg: dict[str, Any], cache_dir: str = "", load: bool = True) -> Embedder:
    """Construct the embedder described by ``config['embedding']``."""
    section = dict(cfg.get("embedding", {}))
    if cache_dir:
        section.setdefault("cache_dir", cache_dir)
    backend = section.get("backend", "fastembed")
    if backend not in BACKENDS:
        raise ValueError(f"unknown embedding backend '{backend}' — expected one of {sorted(BACKENDS)}")
    if not section.get("model"):
        raise ValueError("config embedding.model is empty — run 'rag init' or set it explicitly")
    embedder = BACKENDS[backend](section)
    return embedder.load() if load else embedder


def batched(items: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for at in range(0, len(items), max(1, size)):
        yield items[at : at + size]
