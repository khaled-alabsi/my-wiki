"""Watch the sources and re-index what changed.

Deliberately conservative. Editors write temp files, rename over originals, and fire
several events per save, so raw events are not a reliable signal. This debounces a burst
into one incremental run, and it will not start a second run while one is going.

Watching is optional: without ``watchdog`` installed it falls back to a polling loop.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import Any

from . import config as config_mod
from .detect import is_private_name
from .index import run_index
from .manifest import IndexLockedError

IGNORED_SUFFIXES = (".tmp", ".swp", ".swx", ".part", ".crdownload", "~", ".lock")
POLL_SECONDS = 20.0


class Debouncer:
    """Collapse a burst of change events into one run after the corpus goes quiet."""

    def __init__(self, rag_dir: Path, delay: float) -> None:
        self.rag_dir = rag_dir
        self.delay = delay
        self.timer: threading.Timer | None = None
        self.lock = threading.Lock()
        self.pending: set[str] = set()
        self.running = False

    def note(self, path: str) -> None:
        if path.endswith(IGNORED_SUFFIXES) or is_private_name(Path(path).name):
            return
        with self.lock:
            self.pending.add(path)
            if self.timer is not None:
                self.timer.cancel()
            self.timer = threading.Timer(self.delay, self.fire)
            self.timer.daemon = True
            self.timer.start()

    def fire(self) -> None:
        with self.lock:
            if self.running or not self.pending:
                return
            count = len(self.pending)
            self.pending.clear()
            self.running = True
        try:
            print(f"[watch] {count} change(s) — updating…", flush=True)
            stats = run_index(self.rag_dir, full=False)
            print(f"[watch] indexed {stats.indexed}, removed {stats.removed}, "
                  f"unchanged {stats.skipped_unchanged} ({stats.seconds:.1f}s)", flush=True)
        except IndexLockedError as exc:
            print(f"[watch] skipped: {exc}", file=sys.stderr, flush=True)
        except Exception as exc:
            print(f"[watch] update failed: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        finally:
            with self.lock:
                self.running = False


def watch(rag_dir: Path, debounce: float = 3.0) -> int:
    rag_dir = Path(rag_dir).resolve()
    cfg = config_mod.load(rag_dir)
    roots = [Path(s["path"]) for s in cfg.get("sources", []) if Path(s["path"]).is_dir()]
    if not roots:
        print("no valid sources to watch — check config.toml", file=sys.stderr)
        return 2

    debouncer = Debouncer(rag_dir, debounce)
    print(f"watching {len(roots)} source(s), {debounce}s debounce  (ctrl-c to stop)")
    for root in roots:
        print(f"  {root}")

    try:
        return _watch_with_watchdog(roots, debouncer)
    except ImportError:
        print("\n'watchdog' is not installed — falling back to polling every "
              f"{POLL_SECONDS:.0f}s.\nInstall it for instant updates:\n"
              "  python3 .rag/toolkit/rag_toolkit/install.py --extras watch\n", flush=True)
        return _watch_by_polling(rag_dir, debouncer)


def _watch_with_watchdog(roots: list[Path], debouncer: Debouncer) -> int:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event: Any) -> None:
            if getattr(event, "is_directory", False):
                return
            if event.event_type in {"created", "modified", "deleted", "moved"}:
                debouncer.note(str(getattr(event, "dest_path", "") or event.src_path))

    observer = Observer()
    handler = Handler()
    for root in roots:
        observer.schedule(handler, str(root), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        observer.stop()
        observer.join()
    return 0


def _watch_by_polling(rag_dir: Path, debouncer: Debouncer) -> int:
    """Cheap fallback: the incremental indexer already skips unchanged files."""
    try:
        while True:
            debouncer.pending.add("poll")
            debouncer.fire()
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0
