#!/usr/bin/env python3
"""Personal memory MCP server for LM Studio.

Single-file stdio MCP server (official `mcp` SDK / `FastMCP`) that gives a
coding/research agent long-term memory: structured "entities" (e.g. the
fields of an object you mentioned once), freeform topical "notes" (e.g.
what you've researched and already know about something), and short-term
"session" scratch memory shared across tool calls within one task.

Backend is SQLite (stdlib `sqlite3`, zero extra dependencies) with FTS5
full-text search when available, falling back to a LIKE-based search
otherwise.

Usage:
    python3 memory_server.py [--tools=read-only|rw] [--db=PATH]

--tools controls which tools are registered:
    read-only (default) - recall_entity, search_memory, list_memories,
                           session_recall.
    rw                   - adds remember_entity, remember_note, forget,
                            session_note (the tools that write).
Can also be set via MCP_TOOL_MODE / MCP_MEMORY_DB env vars (flags win).
"""

from __future__ import annotations

import functools
import json
import logging
import os
import re
import sqlite3
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# --------------------------------------------------------------------------
# Logging (file only — stdout is reserved for the MCP JSON-RPC stream)
# --------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_PATH = SCRIPT_DIR / "memory_server.log"

logger = logging.getLogger("memory")
logger.setLevel(logging.INFO)
logger.propagate = False
_log_handler = RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
_log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_log_handler)


def _summarize(value: Any, limit: int = 300) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "...(truncated)"


def _logged(fn):
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info("CALL %s args=%s kwargs=%s", fn.__name__, _summarize(args), _summarize(kwargs))
        try:
            result = fn(*args, **kwargs)
        except Exception:
            logger.exception("EXCEPTION in %s", fn.__name__)
            raise
        logger.info("RESULT %s -> %s", fn.__name__, _summarize(result))
        return result
    return wrapper


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

VALID_TOOL_MODES = {"read-only", "rw"}


def _tool_mode() -> str:
    mode = None
    for arg in sys.argv[1:]:
        if arg.startswith("--tools="):
            mode = arg.split("=", 1)[1].strip().lower()
            break
    if mode is None:
        mode = os.environ.get("MCP_TOOL_MODE", "read-only").strip().lower()
    if mode not in VALID_TOOL_MODES:
        raise SystemExit(f"Invalid tool mode {mode!r}; expected one of {sorted(VALID_TOOL_MODES)}")
    return mode


def _db_path() -> Path:
    db_arg = None
    for arg in sys.argv[1:]:
        if arg.startswith("--db="):
            db_arg = arg.split("=", 1)[1].strip()
            break
    if db_arg is None:
        db_arg = os.environ.get("MCP_MEMORY_DB", str(SCRIPT_DIR / "memory.db"))
    return Path(db_arg).expanduser().resolve()


TOOL_MODE: str = _tool_mode()
DB_PATH: Path = _db_path()

mcp = FastMCP("memory")


def read_tool(fn):
    """Register a tool that only ever reads memory. Always available."""
    return mcp.tool()(_logged(fn))


def write_tool(fn):
    """Register a tool that can create/modify/delete memory. Only in --tools=rw mode."""
    if TOOL_MODE == "rw":
        return mcp.tool()(_logged(fn))
    return fn


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL CHECK(kind IN ('entity', 'note')),
    key TEXT NOT NULL,
    entity_type TEXT,
    attributes TEXT,
    content TEXT,
    tags TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_entity_key
    ON memories(key) WHERE kind = 'entity';
CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind);

CREATE TABLE IF NOT EXISTS session_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_session_notes_session ON session_notes(session_id);
"""

FTS5_AVAILABLE = True


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    _ensure_fts(conn)
    return conn


def _ensure_fts(conn: sqlite3.Connection) -> None:
    global FTS5_AVAILABLE
    try:
        conn.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                key, entity_type, attributes, content, tags,
                content='memories', content_rowid='id'
            );
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, key, entity_type, attributes, content, tags)
                VALUES (new.id, new.key, new.entity_type, new.attributes, new.content, new.tags);
            END;
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, key, entity_type, attributes, content, tags)
                VALUES ('delete', old.id, old.key, old.entity_type, old.attributes, old.content, old.tags);
            END;
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, key, entity_type, attributes, content, tags)
                VALUES ('delete', old.id, old.key, old.entity_type, old.attributes, old.content, old.tags);
                INSERT INTO memories_fts(rowid, key, entity_type, attributes, content, tags)
                VALUES (new.id, new.key, new.entity_type, new.attributes, new.content, new.tags);
            END;
            """
        )
        conn.commit()
        FTS5_AVAILABLE = True
    except sqlite3.OperationalError:
        FTS5_AVAILABLE = False


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _error(message: str, **extra: Any) -> dict[str, Any]:
    return {"error": message, **extra}


def _row_to_memory(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "kind": row["kind"],
        "key": row["key"],
        "entity_type": row["entity_type"],
        "attributes": json.loads(row["attributes"]) if row["attributes"] else {},
        "content": row["content"] or "",
        "tags": [t for t in (row["tags"] or "").split(",") if t],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _fts_match_expr(query: str) -> str:
    tokens = re.findall(r"[\w\-]+", query)
    if not tokens:
        return '""'
    escaped = [t.replace('"', '""') for t in tokens]
    return " OR ".join(f'"{t}"' for t in escaped)


# --------------------------------------------------------------------------
# Entity tools
# --------------------------------------------------------------------------

@write_tool
def remember_entity(
    name: str,
    entity_type: str,
    attributes: dict[str, Any] | None = None,
    notes: str = "",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Create or update a structured entity memory (an object's fields, a user preference, etc).

    Calling this again for an existing `name` merges: new attribute keys are
    added, keys not mentioned this time keep their previous value, and `notes`
    (if given) is appended to the existing notes rather than replacing them.
    Use this for anything with a name and a set of known properties — e.g. a
    Python class's fields, or a user preference like entity_type="preference".

    Args:
        name: Unique identifier for this entity (e.g. a class name).
        entity_type: Freeform category, e.g. "python-class", "preference", "person".
        attributes: Known fields/properties as a JSON object.
        notes: Freeform notes to attach/append.
        tags: Tags for later filtering/search.
    """
    if not name.strip():
        return _error("name must not be empty")

    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM memories WHERE kind='entity' AND key=?", (name,)
        ).fetchone()
        now = _now()

        if row is None:
            conn.execute(
                "INSERT INTO memories (kind, key, entity_type, attributes, content, tags, created_at, updated_at) "
                "VALUES ('entity', ?, ?, ?, ?, ?, ?, ?)",
                (
                    name, entity_type, json.dumps(attributes or {}), notes,
                    ",".join(tags or []), now, now,
                ),
            )
            created = True
        else:
            existing_attrs = json.loads(row["attributes"]) if row["attributes"] else {}
            existing_attrs.update(attributes or {})
            existing_tags = [t for t in (row["tags"] or "").split(",") if t]
            merged_tags = existing_tags + [t for t in (tags or []) if t not in existing_tags]
            merged_content = row["content"] or ""
            if notes:
                merged_content = f"{merged_content}\n\n---[{now}]---\n{notes}".strip()
            conn.execute(
                "UPDATE memories SET entity_type=?, attributes=?, content=?, tags=?, updated_at=? WHERE id=?",
                (entity_type, json.dumps(existing_attrs), merged_content, ",".join(merged_tags), now, row["id"]),
            )
            created = False

        conn.commit()
        final = conn.execute("SELECT * FROM memories WHERE kind='entity' AND key=?", (name,)).fetchone()
        result = _row_to_memory(final)
        result["created"] = created
        return result
    finally:
        conn.close()


@read_tool
def recall_entity(name: str) -> dict[str, Any]:
    """Fetch a previously remembered entity by its exact name."""
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM memories WHERE kind='entity' AND key=?", (name,)).fetchone()
        if row is None:
            return _error(f"No entity remembered with name {name!r}")
        return _row_to_memory(row)
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Note tools
# --------------------------------------------------------------------------

@write_tool
def remember_note(topic: str, content: str, tags: list[str] | None = None) -> dict[str, Any]:
    """Save a freeform note under a topic (research findings, what the user already knows, etc).

    Unlike entities, notes are append-only: calling this again with the same
    topic adds a new, separate note rather than overwriting previous ones, so
    a history of what's been learned about a topic accumulates over time.

    Args:
        topic: Subject the note is about (does not need to be unique).
        content: The note text itself.
        tags: Tags for later filtering/search.
    """
    if not topic.strip():
        return _error("topic must not be empty")
    if not content.strip():
        return _error("content must not be empty")

    conn = _connect()
    try:
        now = _now()
        cur = conn.execute(
            "INSERT INTO memories (kind, key, entity_type, attributes, content, tags, created_at, updated_at) "
            "VALUES ('note', ?, NULL, NULL, ?, ?, ?, ?)",
            (topic, content, ",".join(tags or []), now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM memories WHERE id=?", (cur.lastrowid,)).fetchone()
        return _row_to_memory(row)
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Search / browse tools
# --------------------------------------------------------------------------

@read_tool
def search_memory(query: str, kind: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Full-text search across all remembered entities and notes.

    Args:
        query: Free-text search query (matched as OR across its words).
        kind: Optionally restrict to "entity" or "note".
        limit: Maximum number of results.
    """
    if kind is not None and kind not in ("entity", "note"):
        return _error("kind must be 'entity', 'note', or omitted")

    conn = _connect()
    try:
        if FTS5_AVAILABLE:
            match_expr = _fts_match_expr(query)
            sql = (
                "SELECT m.* FROM memories m "
                "JOIN memories_fts f ON m.id = f.rowid "
                "WHERE memories_fts MATCH ?"
            )
            params: list[Any] = [match_expr]
            if kind:
                sql += " AND m.kind = ?"
                params.append(kind)
            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
        else:
            tokens = re.findall(r"[\w\-]+", query) or [query]
            clauses = " OR ".join(
                "(key LIKE ? OR entity_type LIKE ? OR attributes LIKE ? OR content LIKE ? OR tags LIKE ?)"
                for _ in tokens
            )
            params = []
            for t in tokens:
                like = f"%{t}%"
                params.extend([like, like, like, like, like])
            sql = f"SELECT * FROM memories WHERE ({clauses})"
            if kind:
                sql += " AND kind = ?"
                params.append(kind)
            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()

        results = [_row_to_memory(r) for r in rows]
        return {
            "query": query, "kind": kind, "engine": "fts5" if FTS5_AVAILABLE else "like-fallback",
            "count": len(results), "results": results,
        }
    finally:
        conn.close()


@read_tool
def list_memories(kind: str | None = None, tag: str | None = None, limit: int = 100) -> dict[str, Any]:
    """Browse remembered entities/notes, most recently updated first.

    Args:
        kind: Optionally restrict to "entity" or "note".
        tag: Optionally restrict to memories carrying this tag.
        limit: Maximum number of results.
    """
    if kind is not None and kind not in ("entity", "note"):
        return _error("kind must be 'entity', 'note', or omitted")

    conn = _connect()
    try:
        sql = "SELECT * FROM memories WHERE 1=1"
        params: list[Any] = []
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        if tag:
            sql += " AND (',' || tags || ',') LIKE ?"
            params.append(f"%,{tag},%")
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        results = [_row_to_memory(r) for r in rows]
        return {"kind": kind, "tag": tag, "count": len(results), "results": results}
    finally:
        conn.close()


@write_tool
def forget(identifier: str) -> dict[str, Any]:
    """Delete a memory: pass a numeric id (any memory) or an entity name (kind='entity' only).

    Notes aren't uniquely keyed by topic, so deleting a specific note requires
    its numeric id (from search_memory/list_memories output), not its topic.
    """
    conn = _connect()
    try:
        if identifier.isdigit():
            cur = conn.execute("DELETE FROM memories WHERE id=?", (int(identifier),))
        else:
            cur = conn.execute("DELETE FROM memories WHERE kind='entity' AND key=?", (identifier,))
        conn.commit()
        if cur.rowcount == 0:
            return _error(
                f"No memory found for identifier {identifier!r} "
                "(notes must be deleted by numeric id, not topic)"
            )
        return {"deleted": cur.rowcount, "identifier": identifier}
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Session (short-term) memory tools
# --------------------------------------------------------------------------

@write_tool
def session_note(session_id: str, content: str) -> dict[str, Any]:
    """Append a scratch note to short-term memory scoped to `session_id`.

    Use this for working context within one ongoing task (e.g. intermediate
    findings while researching) that doesn't necessarily belong in long-term
    memory yet. Pick a stable session_id for the current conversation/task.
    """
    if not session_id.strip():
        return _error("session_id must not be empty")
    if not content.strip():
        return _error("content must not be empty")

    conn = _connect()
    try:
        now = _now()
        cur = conn.execute(
            "INSERT INTO session_notes (session_id, content, created_at) VALUES (?, ?, ?)",
            (session_id, content, now),
        )
        conn.commit()
        return {"id": cur.lastrowid, "session_id": session_id, "created_at": now}
    finally:
        conn.close()


@read_tool
def session_recall(session_id: str, limit: int = 50) -> dict[str, Any]:
    """Retrieve scratch notes previously saved under `session_id`, oldest first."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM session_notes WHERE session_id=? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        notes = [{"id": r["id"], "content": r["content"], "created_at": r["created_at"]} for r in rows]
        return {"session_id": session_id, "count": len(notes), "notes": notes}
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("startup: tool_mode=%s db_path=%s", TOOL_MODE, DB_PATH)
    mcp.run(transport="stdio")
