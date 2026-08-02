"""Index state: which files are known, their hashes, and which chunks they own.

This is what makes ``rag update`` cheap and ``rag index`` resumable. A killed run
leaves every already-committed file marked ``indexed``; the next run skips them
because their content hash still matches.
"""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    path         TEXT PRIMARY KEY,
    source       TEXT NOT NULL,
    rel_path     TEXT NOT NULL,
    size         INTEGER NOT NULL DEFAULT 0,
    mtime        REAL    NOT NULL DEFAULT 0,
    file_hash    TEXT    NOT NULL DEFAULT '',
    content_hash TEXT    NOT NULL DEFAULT '',
    n_chunks     INTEGER NOT NULL DEFAULT 0,
    extractor    TEXT    NOT NULL DEFAULT '',
    status       TEXT    NOT NULL DEFAULT 'pending',
    error        TEXT    NOT NULL DEFAULT '',
    indexed_at   REAL    NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS files_status ON files(status);
CREATE INDEX IF NOT EXISTS files_source ON files(source);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    path     TEXT NOT NULL,
    ordinal  INTEGER NOT NULL,
    hash     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_path ON chunks(path);

CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS runs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    kind     TEXT NOT NULL,
    started  REAL NOT NULL,
    finished REAL NOT NULL DEFAULT 0,
    stats    TEXT NOT NULL DEFAULT '{}'
);
"""


class IndexLockedError(RuntimeError):
    """Raised when another index run already holds the lock."""


class FileLock:
    """Refuse to run two heavy jobs against one .rag workspace."""

    def __init__(self, path: Path, stale_after: float = 6 * 3600) -> None:
        self.path = Path(path)
        self.stale_after = stale_after

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                held = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                held = {}
            pid, started = held.get("pid", 0), held.get("started", 0.0)
            if _pid_alive(pid) and time.time() - started < self.stale_after:
                raise IndexLockedError(
                    f"another run (pid {pid}) is already indexing this workspace. "
                    f"Wait for it, or remove {self.path} if you are certain it died."
                )
        self.path.write_text(
            json.dumps({"pid": os.getpid(), "started": time.time()}), encoding="utf-8"
        )

    def release(self) -> None:
        with contextlib.suppress(OSError):
            self.path.unlink()

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()


def _pid_alive(pid: int) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        return _windows_pid_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # it exists, it just is not ours to signal
    except OSError:
        return False
    return True


def _windows_pid_alive(pid: int) -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # type: ignore[attr-defined]
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
            return True
    except Exception:
        pass
    return False


class Manifest:
    """Thin sqlite wrapper. Commit after every file so a crash loses at most one."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        with contextlib.suppress(sqlite3.Error):
            self.conn.commit()
            self.conn.close()

    def __enter__(self) -> "Manifest":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ----------------------------------------------------------------- files

    def known_files(self, source: str | None = None) -> dict[str, dict[str, Any]]:
        sql = "SELECT * FROM files"
        args: tuple[Any, ...] = ()
        if source:
            sql += " WHERE source = ?"
            args = (source,)
        return {row["path"]: dict(row) for row in self.conn.execute(sql, args)}

    def get_file(self, path: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM files WHERE path = ?", (path,)).fetchone()
        return dict(row) if row else None

    def record_file(self, **row: Any) -> None:
        row.setdefault("indexed_at", time.time())
        cols = ", ".join(row)
        holes = ", ".join("?" for _ in row)
        updates = ", ".join(f"{c}=excluded.{c}" for c in row if c != "path")
        self.conn.execute(
            f"INSERT INTO files ({cols}) VALUES ({holes}) "
            f"ON CONFLICT(path) DO UPDATE SET {updates}",
            tuple(row.values()),
        )

    def forget_file(self, path: str) -> list[str]:
        """Drop a file and return the chunk ids that must be deleted from the store."""
        ids = self.chunk_ids(path)
        self.conn.execute("DELETE FROM chunks WHERE path = ?", (path,))
        self.conn.execute("DELETE FROM files WHERE path = ?", (path,))
        return ids

    # ---------------------------------------------------------------- chunks

    def chunk_ids(self, path: str) -> list[str]:
        rows = self.conn.execute("SELECT chunk_id FROM chunks WHERE path = ?", (path,))
        return [r["chunk_id"] for r in rows]

    def replace_chunks(self, path: str, chunks: Iterable[tuple[str, int, str]]) -> list[str]:
        """Swap a file's chunk rows. Returns the previous ids, for store deletion."""
        old = self.chunk_ids(path)
        self.conn.execute("DELETE FROM chunks WHERE path = ?", (path,))
        self.conn.executemany(
            "INSERT OR REPLACE INTO chunks (chunk_id, path, ordinal, hash) VALUES (?, ?, ?, ?)",
            [(cid, path, ordinal, chash) for cid, ordinal, chash in chunks],
        )
        return old

    def all_chunk_ids(self) -> set[str]:
        return {r["chunk_id"] for r in self.conn.execute("SELECT chunk_id FROM chunks")}

    # ------------------------------------------------------------ meta / runs

    def set_meta(self, key: str, value: Any) -> None:
        self.conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )
        self.conn.commit()

    def get_meta(self, key: str, default: Any = None) -> Any:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    @contextlib.contextmanager
    def run(self, kind: str) -> Iterator[dict[str, Any]]:
        cur = self.conn.execute(
            "INSERT INTO runs (kind, started) VALUES (?, ?)", (kind, time.time())
        )
        run_id, stats = cur.lastrowid, {}
        self.conn.commit()
        try:
            yield stats
        finally:
            self.conn.execute(
                "UPDATE runs SET finished = ?, stats = ? WHERE id = ?",
                (time.time(), json.dumps(stats), run_id),
            )
            self.conn.commit()

    def last_run(self) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return None
        out = dict(row)
        out["stats"] = json.loads(out["stats"] or "{}")
        return out

    def stats(self) -> dict[str, Any]:
        counts = {
            r["status"]: r["n"]
            for r in self.conn.execute("SELECT status, COUNT(*) AS n FROM files GROUP BY status")
        }
        totals = self.conn.execute(
            "SELECT COUNT(*) AS files, COALESCE(SUM(n_chunks), 0) AS chunks, "
            "COALESCE(SUM(size), 0) AS bytes FROM files"
        ).fetchone()
        return {
            "files": totals["files"],
            "chunks": totals["chunks"],
            "bytes": totals["bytes"],
            "by_status": counts,
            "last_run": self.last_run(),
        }
