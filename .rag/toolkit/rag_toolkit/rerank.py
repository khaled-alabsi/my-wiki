"""Cross-encoder reranking.

Fusion decides which chunks are *candidates*; a cross-encoder decides which are actually
about the query, because it reads the query and the chunk together instead of comparing
two independently-produced vectors. It is usually the largest single quality gain
available, and it costs one model load plus a scoring pass over the candidates only.

Reranking is optional everywhere. A missing dependency degrades to fusion order and says
so — it never fails a search.
"""

from __future__ import annotations

from typing import Any, Sequence

from .store import Hit


class Reranker:
    name = "none"
    available = True

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.model_id: str = cfg.get("rerank_model", "") or ""
        self.cache_dir: str = cfg.get("cache_dir", "") or ""
        self.device: str = cfg.get("device", "cpu")
        self.reason: str = ""

    def load(self) -> "Reranker":
        return self

    def rerank(self, query: str, hits: Sequence[Hit], top_k: int) -> list[Hit]:
        return list(hits[:top_k])

    def describe(self) -> dict[str, Any]:
        return {"backend": self.name, "model": self.model_id,
                "available": self.available, "reason": self.reason}


class CrossEncoderReranker(Reranker):
    name = "sentence-transformers"

    def load(self) -> "Reranker":
        from . import models as models_mod

        models_mod.prime_offline(self.cache_dir, self.model_id)

        from sentence_transformers import CrossEncoder  # from the 'torch' extra

        kwargs: dict[str, Any] = {"device": self.device or None}
        if self.cache_dir:
            kwargs["cache_folder"] = self.cache_dir
        self._model = CrossEncoder(self.model_id, **kwargs)
        return self

    def rerank(self, query: str, hits: Sequence[Hit], top_k: int) -> list[Hit]:
        if not hits:
            return []
        pairs = [(query, _passage(hit)) for hit in hits]
        scores = self._model.predict(pairs, show_progress_bar=False)
        ranked = sorted(zip(hits, scores), key=lambda pair: float(pair[1]), reverse=True)
        return [
            Hit(hit.record, score=round(float(score), 6), source_of_match="rerank")
            for hit, score in ranked[:top_k]
        ]


class FastEmbedReranker(Reranker):
    name = "fastembed"

    def load(self) -> "Reranker":
        from . import models as models_mod

        models_mod.prime_offline(self.cache_dir, self.model_id)

        from fastembed.rerank.cross_encoder import TextCrossEncoder  # from the 'onnx' extra

        kwargs: dict[str, Any] = {"model_name": self.model_id}
        if self.cache_dir:
            kwargs["cache_dir"] = self.cache_dir
        self._model = TextCrossEncoder(**kwargs)
        return self

    def rerank(self, query: str, hits: Sequence[Hit], top_k: int) -> list[Hit]:
        if not hits:
            return []
        scores = list(self._model.rerank(query, [_passage(hit) for hit in hits]))
        ranked = sorted(zip(hits, scores), key=lambda pair: float(pair[1]), reverse=True)
        return [
            Hit(hit.record, score=round(float(score), 6), source_of_match="rerank")
            for hit, score in ranked[:top_k]
        ]


BACKENDS: dict[str, type[Reranker]] = {
    "none": Reranker,
    "sentence-transformers": CrossEncoderReranker,
    "fastembed": FastEmbedReranker,
}

# A cross-encoder reads the whole passage. Past this many characters the extra text costs
# more than it adds, and long passages blow up the scoring pass.
MAX_PASSAGE_CHARS = 4000


def _passage(hit: Hit) -> str:
    record = hit.record
    text = f"{record.prefix}\n{record.text}" if record.prefix else record.text
    return text[:MAX_PASSAGE_CHARS]


def build(cfg: dict[str, Any], cache_dir: str = "", load: bool = True) -> Reranker:
    """Build the configured reranker, degrading to pass-through if it cannot load."""
    section = dict(cfg.get("retrieval", {}))
    section.setdefault("cache_dir", cache_dir)
    section.setdefault("device", cfg.get("embedding", {}).get("device", "cpu"))

    if not section.get("rerank", False):
        disabled = Reranker(section)
        disabled.reason = "retrieval.rerank is false"
        return disabled

    backend = section.get("rerank_backend", "none")
    cls = BACKENDS.get(backend, Reranker)
    reranker = cls(section)
    if cls is Reranker:
        reranker.reason = f"no reranker backend configured (rerank_backend = '{backend}')"
        return reranker
    if not load:
        return reranker

    try:
        return reranker.load()
    except Exception as exc:
        fallback = Reranker(section)
        fallback.available = False
        fallback.model_id = section.get("rerank_model", "")
        fallback.reason = f"{type(exc).__name__}: {exc}"
        return fallback
