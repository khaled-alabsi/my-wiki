"""Model registry — the single source of truth for every model id in this toolkit.

No other module hardcodes a model name. To adopt a newer model, edit an entry here,
then run ``rag doctor --models``: it loads each configured model, reports the real
embedding dimension, and rewrites the config if the published value was wrong.

The ``dimension`` values below are advisory. Nothing depends on them being right —
``embed.py`` reports the true dimension after loading and the store is created from
that. This keeps a stale registry from silently corrupting an index.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# fastembed and sentence-transformers reranking are optional extras; a tier that names
# one degrades to no reranking rather than failing, and doctor says so.


@dataclass(frozen=True)
class EmbeddingModel:
    id: str
    backend: str  # "fastembed" (ONNX, no torch) | "sentence-transformers" | "api"
    dimension: int  # advisory; confirmed at load time
    max_tokens: int
    multilingual: bool
    approx_download_mb: int
    query_prefix: str = ""
    document_prefix: str = ""
    normalize: bool = True
    trust_remote_code: bool = False
    notes: str = ""


@dataclass(frozen=True)
class RerankModel:
    id: str
    backend: str  # "fastembed" | "sentence-transformers" | "none"
    multilingual: bool
    approx_download_mb: int
    notes: str = ""


# --------------------------------------------------------------------------- registry

EMBEDDINGS: dict[str, EmbeddingModel] = {
    # --- ONNX / fastembed: no torch, installs in ~200 MB, CPU-fast, Windows-friendly
    "e5-small-multi": EmbeddingModel(
        id="intfloat/multilingual-e5-small", backend="fastembed", dimension=384,
        max_tokens=512, multilingual=True, approx_download_mb=470,
        query_prefix="query: ", document_prefix="passage: ",
        notes="Default light tier. The query/passage prefixes are required by the e5 family.",
    ),
    "bge-small-en": EmbeddingModel(
        id="BAAI/bge-small-en-v1.5", backend="fastembed", dimension=384,
        max_tokens=512, multilingual=False, approx_download_mb=130,
        query_prefix="Represent this sentence for searching relevant passages: ",
        notes="English-only, smallest sensible option. Query prefix applies to queries only.",
    ),
    "bge-base-en": EmbeddingModel(
        id="BAAI/bge-base-en-v1.5", backend="fastembed", dimension=768,
        max_tokens=512, multilingual=False, approx_download_mb=420,
        query_prefix="Represent this sentence for searching relevant passages: ",
        notes="English-only mid option when torch is unavailable.",
    ),
    # --- sentence-transformers / torch: needs an accelerator to be worth the install
    "e5-base-multi": EmbeddingModel(
        id="intfloat/multilingual-e5-base", backend="sentence-transformers", dimension=768,
        max_tokens=512, multilingual=True, approx_download_mb=1100,
        query_prefix="query: ", document_prefix="passage: ",
        notes="Default balanced tier. Strong multilingual quality at a modest size.",
    ),
    "e5-large-multi": EmbeddingModel(
        id="intfloat/multilingual-e5-large", backend="sentence-transformers", dimension=1024,
        max_tokens=512, multilingual=True, approx_download_mb=2200,
        query_prefix="query: ", document_prefix="passage: ",
        notes="Alternative large tier when bge-m3's long context is not needed.",
    ),
    "bge-m3": EmbeddingModel(
        id="BAAI/bge-m3", backend="sentence-transformers", dimension=1024,
        max_tokens=8192, multilingual=True, approx_download_mb=2300,
        notes="Default large tier. Long context suits whole-section and page chunks. No prefixes.",
    ),
    # --- hosted, opt-in only
    "openai-3-large": EmbeddingModel(
        id="text-embedding-3-large", backend="api", dimension=3072,
        max_tokens=8191, multilingual=True, approx_download_mb=0,
        notes="Needs OPENAI_API_KEY. Sends corpus text off the machine — never a default.",
    ),
}

RERANKERS: dict[str, RerankModel] = {
    "none": RerankModel(id="", backend="none", multilingual=True, approx_download_mb=0,
                        notes="Hybrid fusion only. Always available."),
    "ms-marco-mini": RerankModel(
        id="Xenova/ms-marco-MiniLM-L-6-v2", backend="fastembed", multilingual=False,
        approx_download_mb=90, notes="ONNX cross-encoder, English. Cheap quality win on CPU.",
    ),
    "bge-reranker-base": RerankModel(
        id="BAAI/bge-reranker-base", backend="sentence-transformers", multilingual=True,
        approx_download_mb=1100, notes="Multilingual cross-encoder for the balanced tier.",
    ),
    "bge-reranker-v2-m3": RerankModel(
        id="BAAI/bge-reranker-v2-m3", backend="sentence-transformers", multilingual=True,
        approx_download_mb=2300, notes="Strongest bundled reranker. Large tier only.",
    ),
}


@dataclass(frozen=True)
class Tier:
    name: str
    multilingual: str  # registry key
    english: str  # registry key
    reranker: str  # RERANKERS key
    fallback_reranker: str = "none"
    batch_size: int = 32


TIERS: dict[str, Tier] = {
    "large": Tier("large", multilingual="bge-m3", english="bge-m3",
                  reranker="bge-reranker-v2-m3", fallback_reranker="none", batch_size=16),
    "balanced": Tier("balanced", multilingual="e5-base-multi", english="bge-base-en",
                     reranker="bge-reranker-base", fallback_reranker="ms-marco-mini", batch_size=32),
    "light": Tier("light", multilingual="e5-small-multi", english="bge-small-en",
                  reranker="ms-marco-mini", fallback_reranker="none", batch_size=64),
    "api": Tier("api", multilingual="openai-3-large", english="openai-3-large",
                reranker="none", batch_size=128),
}

TIER_ORDER = ["light", "balanced", "large"]

# A corpus past this many estimated chunks steps the tier down one level: a stronger
# model is not worth a run measured in hours. Overridable with an explicit tier.
LARGE_CORPUS_CHUNKS = 200_000


# --------------------------------------------------------------------------- selection


def pick_tier(host: dict[str, Any], requested: str = "auto") -> tuple[str, str]:
    """Return ``(tier_name, reason)``."""
    if requested and requested != "auto":
        return requested, f"requested explicitly ({requested})"
    accel = host.get("accelerator", {})
    device, vram, ram = accel.get("device", "cpu"), accel.get("vram_gb", 0.0), host.get("ram_gb", 0.0)
    if device == "cuda" and vram >= 8:
        return "large", f"CUDA GPU with {vram} GB VRAM"
    if device == "mps" and ram >= 24:
        return "large", f"Apple Silicon with {ram} GB unified memory"
    if device in {"cuda", "mps"} and ram >= 16:
        return "balanced", f"{device} available with {ram} GB RAM"
    if device in {"cuda", "mps"}:
        return "light", f"{device} available but only {ram} GB RAM"
    return "light", "no GPU or MPS detected — ONNX on CPU is the right call here"


def step_down(tier: str) -> str:
    idx = TIER_ORDER.index(tier) if tier in TIER_ORDER else 0
    return TIER_ORDER[max(0, idx - 1)]


def pick_language(corpus: dict[str, Any] | None, requested: str = "auto") -> tuple[str, str]:
    if requested in {"en", "multi"}:
        return requested, f"requested explicitly ({requested})"
    guess = (corpus or {}).get("language_guess", "unknown")
    if guess == "en":
        return "en", "sampled text looks English-only"
    if guess in {"unknown", "mixed"}:
        return "multi", f"language sample was '{guess}' — multilingual is the safe default"
    return "multi", f"sampled text looks like '{guess}'"


def select(
    host: dict[str, Any],
    corpus: dict[str, Any] | None = None,
    tier: str = "auto",
    language: str = "auto",
    estimated_chunks: int = 0,
) -> dict[str, Any]:
    """Resolve host + corpus into concrete embedding/reranking settings."""
    tier_name, tier_reason = pick_tier(host, tier)
    lang, lang_reason = pick_language(corpus, language)
    notes = [tier_reason, lang_reason]

    if tier == "auto" and estimated_chunks > LARGE_CORPUS_CHUNKS and tier_name != "light":
        lowered = step_down(tier_name)
        notes.append(
            f"stepped {tier_name} down to {lowered}: ~{estimated_chunks:,} chunks would make the "
            f"stronger model's run time dominate the setup"
        )
        tier_name = lowered

    spec = TIERS.get(tier_name) or TIERS["balanced"]
    key = spec.english if lang == "en" else spec.multilingual
    model = EMBEDDINGS[key]
    reranker = RERANKERS[spec.reranker]
    if lang != "en" and not reranker.multilingual:
        reranker = RERANKERS[spec.fallback_reranker]
        notes.append(f"reranker swapped to '{reranker.backend or 'none'}' for multilingual content")

    return {
        "tier": tier_name,
        "language": lang,
        "embedding": {
            "tier": tier_name,
            "backend": model.backend,
            "model": model.id,
            "dimension": model.dimension,
            "batch_size": spec.batch_size,
            "query_prefix": model.query_prefix,
            "document_prefix": model.document_prefix,
            "normalize": model.normalize,
            "trust_remote_code": model.trust_remote_code,
        },
        "retrieval": {
            "rerank": reranker.backend != "none",
            "rerank_backend": reranker.backend,
            "rerank_model": reranker.id,
        },
        "download_mb": model.approx_download_mb + reranker.approx_download_mb,
        "notes": notes,
    }


def describe(key_or_id: str) -> EmbeddingModel | None:
    if key_or_id in EMBEDDINGS:
        return EMBEDDINGS[key_or_id]
    return next((m for m in EMBEDDINGS.values() if m.id == key_or_id), None)


def extras_for(backend: str, rerank_backend: str = "none") -> list[str]:
    """Which dependency extras a chosen backend pair needs."""
    extras = {"core"}
    for name in (backend, rerank_backend):
        if name == "fastembed":
            extras.add("onnx")
        elif name == "sentence-transformers":
            extras.add("torch")
        elif name == "api":
            extras.add("api")
    return sorted(extras)
