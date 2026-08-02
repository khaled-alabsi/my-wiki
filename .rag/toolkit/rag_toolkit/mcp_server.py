"""MCP stdio server — exposes the index as tools any MCP-capable agent can call.

Register it with an agent by pointing at the workspace launcher::

    {"mcpServers": {"rag": {"command": "/abs/path/.rag/bin/rag", "args": ["serve", "--mcp"]}}}

Tools are read-only by design. Indexing is heavy and interactive; an agent should not be
able to kick off an hours-long embedding run as a side effect of answering a question.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MAX_K = 50
DEFAULT_SNIPPET_CHARS = 1200


def build_server(rag_dir: Path) -> Any:
    from mcp.server.fastmcp import FastMCP  # from the 'mcp' extra

    from .api import Index

    server = FastMCP("rag")
    state: dict[str, Any] = {"index": None}

    def index() -> Index:
        if state["index"] is None:
            state["index"] = Index(rag_dir)
        return state["index"]

    @server.tool()
    def rag_search(
        query: str,
        k: int = 8,
        path: str = "",
        ext: str = "",
        source: str = "",
        since: str = "",
        max_chars: int = DEFAULT_SNIPPET_CHARS,
    ) -> str:
        """Search the local index and return ranked passages with citations.

        Args:
            query: what to look for, in natural language.
            k: how many passages to return (capped at 50).
            path: optional glob against the path relative to its source, e.g. 'docs/*.md'.
            ext: optional comma-separated extensions, e.g. '.md,.pdf'.
            source: optional name of one configured source.
            since: optional ISO date; only files modified on or after it.
            max_chars: truncate each passage to this many characters.
        """
        hits = index().search(
            query, k=min(max(k, 1), MAX_K), max_chars=max_chars,
            path=path, ext=ext, source=source, since=since,
        )
        if not hits:
            return json.dumps({
                "query": query, "hits": [],
                "note": "no matches. The index may not cover this, or it may be stale — "
                        "call rag_status to check.",
            }, indent=2)
        return json.dumps({"query": query, "hits": hits}, indent=2, ensure_ascii=False)

    @server.tool()
    def rag_status() -> str:
        """Report what is indexed: sources, file and chunk counts, model, and any drift.

        Call this before trusting an empty search result — it distinguishes 'the corpus
        does not contain this' from 'the index was never built or is stale'.
        """
        return json.dumps(index().status(), indent=2, default=str)

    @server.tool()
    def rag_sources() -> str:
        """List the configured sources: their names and root paths."""
        return json.dumps(index().sources(), indent=2)

    @server.tool()
    def rag_context(query: str, k: int = 8, max_chars: int = DEFAULT_SNIPPET_CHARS) -> str:
        """Search and return the passages pre-formatted as a citation-carrying context block.

        Use this instead of rag_search when the passages are going straight into an answer.
        """
        return index().context_block(query, k=min(max(k, 1), MAX_K), max_chars=max_chars)

    return server


def serve(rag_dir: Path) -> int:
    """Run the stdio server. Blocks until the client disconnects."""
    try:
        server = build_server(Path(rag_dir))
    except ImportError:
        import sys

        print(
            "the MCP server needs the 'mcp' extra:\n"
            "  python3 .rag/toolkit/rag_toolkit/install.py --extras mcp",
            file=sys.stderr,
        )
        return 2
    server.run(transport="stdio")
    return 0


def registration_snippet(rag_dir: Path) -> dict[str, Any]:
    """The JSON an agent host needs to launch this server."""
    launcher = Path(rag_dir).resolve() / "bin" / "rag"
    return {
        "mcpServers": {
            "rag": {"command": str(launcher), "args": ["serve", "--mcp"]}
        }
    }
