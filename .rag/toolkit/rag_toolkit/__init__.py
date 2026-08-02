"""rag_toolkit — a local, offline retrieval index over any folder or document collection.

Retrieval only: it returns ranked chunks with citations. It contains no LLM and needs no
API key. Whatever calls it writes the answer.

Quick start::

    from rag_toolkit import Index
    with Index.find() as index:
        for hit in index.search("what is the escalation path", k=5):
            print(hit["citation"], hit["score"])

Everything heavy is imported lazily, so ``import rag_toolkit`` stays fast and works even
when the optional extras (torch, fastembed, lancedb) are not installed.
"""

from __future__ import annotations

from typing import Any

__version__ = "1.2.2"

__all__ = ["Index", "IndexNotBuiltError", "search", "to_markdown", "__version__"]

_LAZY = {
    "Index": ("api", "Index"),
    "IndexNotBuiltError": ("api", "IndexNotBuiltError"),
    "search": ("api", "search"),
    "to_markdown": ("api", "to_markdown"),
}


def __getattr__(name: str) -> Any:
    """Defer the heavy imports until something is actually used."""
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module 'rag_toolkit' has no attribute '{name}'")
    import importlib

    module = importlib.import_module(f".{target[0]}", __name__)
    value = getattr(module, target[1])
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
