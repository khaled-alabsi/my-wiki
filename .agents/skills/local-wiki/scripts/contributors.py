#!/usr/bin/env python3
"""Who changed what in this vault, and when.

Stdlib only. Two subcommands:

    contributors.py record --user-id <email> --path <p> [--path <p> ...] --type added|edited
    contributors.py query  --path <p> --since-hours 24
    contributors.py query  --user-id <email> [--limit N]
    contributors.py query  --stats

Why a tool instead of the agent editing the JSON directly: `.wiki/contributors.json` is shared and
committed, several people write to it, and prose-driven edits to a shared file produce malformed
JSON and lost updates. The same reasoning the vault's `.rag` workspace applies to its own toolkit.

Two design rules that look like bugs if you don't know why:

  Repeats are kept.   The same user touching the same file twice appends a SECOND entry. A deduped
                      per-user set would be smaller and would destroy the recency signal that
                      `query --path --since-hours` exists to provide.

  Reads are bounded.  `query` answers a question and returns just that. The log grows without limit
                      across every contributor and every change, so the agent never reads the raw
                      file — that rule is only enforceable if every query is bounded here.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

STORE_NAME = "contributors.json"
LOCK_SUFFIX = ".lock"
LOCK_STALE_S = 5.0
LOCK_POLL_S = 0.05
LOCK_WAIT_S = 30.0
DEFAULT_LIMIT = 20
VALID_TYPES = ("added", "edited")


# --- paths -----------------------------------------------------------------------------------

def store_path(vault: Path) -> Path:
    return vault / ".wiki" / STORE_NAME


def relative_to_vault(vault: Path, raw: str) -> str:
    """A vault-relative POSIX path, or raise if it escapes the vault.

    Rejecting `../` and absolute outside paths matters because this file is committed and shared:
    an entry pointing outside the vault is either a bug or a path leaked from someone's machine.
    """
    vault = vault.resolve()
    candidate = Path(raw)
    absolute = (candidate if candidate.is_absolute() else vault / candidate)
    # No resolve() on the file itself — a note may not exist yet when it is recorded as `added`.
    normalized = Path(os.path.normpath(str(absolute)))
    try:
        return normalized.relative_to(vault).as_posix()
    except ValueError:
        raise ValueError(f"path is outside the vault: {raw}")


# --- storage ---------------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text: str) -> datetime | None:
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


class CorruptStore(Exception):
    """The store exists but is not readable as the expected JSON."""


def read_store(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "contributors": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise CorruptStore(str(exc)) from exc
    if not isinstance(data, dict) or not isinstance(data.get("contributors"), dict):
        raise CorruptStore("top-level shape is not {'version': .., 'contributors': {..}}")
    return data


def back_up_corrupt(path: Path) -> Path:
    """Move the unreadable file aside, keeping its bytes. Never overwrite a real log."""
    backup = path.with_name(f"{path.name}.corrupt-{time.strftime('%Y%m%dT%H%M%S')}")
    counter = 1
    while backup.exists():
        counter += 1
        backup = path.with_name(f"{path.name}.corrupt-{time.strftime('%Y%m%dT%H%M%S')}-{counter}")
    path.rename(backup)
    return backup


def write_store(path: Path, data: dict) -> None:
    """Write whole, atomically. Never append in place.

    A temp file in the same directory plus os.replace is atomic on POSIX and Windows, so a reader
    sees either the old file or the new one — never a half-written one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


class FileLock:
    """A cross-process lock around read-modify-write.

    os.replace makes a single write atomic, but this tool does read -> mutate -> write, and two
    processes interleaving there lose one of the two updates. The lock closes that window.

    A lock older than LOCK_STALE_S is broken: a crashed writer must not block the vault forever,
    and the write it was doing is at most one entry.
    """

    def __init__(self, target: Path) -> None:
        self.path = target.with_name(target.name + LOCK_SUFFIX)
        self.acquired = False

    def __enter__(self) -> "FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + LOCK_WAIT_S
        while True:
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self.acquired = True
                return self
            except FileExistsError:
                try:
                    age = time.time() - self.path.stat().st_mtime
                except OSError:
                    continue
                if age > LOCK_STALE_S:
                    try:
                        self.path.unlink()
                    except OSError:
                        pass
                    continue
                if time.monotonic() > deadline:
                    raise TimeoutError(f"could not acquire {self.path} within {LOCK_WAIT_S}s")
                time.sleep(LOCK_POLL_S)

    def __exit__(self, *_exc) -> None:
        if self.acquired:
            try:
                self.path.unlink()
            except OSError:
                pass


# --- record ----------------------------------------------------------------------------------

def cmd_record(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    path = store_path(vault)
    try:
        rel = [relative_to_vault(vault, raw) for raw in args.path]
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    stamp = now_iso()
    with FileLock(path):
        try:
            data = read_store(path)
        except CorruptStore as exc:
            backup = back_up_corrupt(path)
            print(f"error: {STORE_NAME} is corrupt ({exc}); original preserved at {backup.name}. "
                  f"Restore it from git, or delete it to start a new log.", file=sys.stderr)
            return 3
        entries = data["contributors"].setdefault(args.user_id, {"entries": []})["entries"]
        for item in rel:
            entries.append({"path": item, "type": args.type, "ts": stamp})
        write_store(path, data)

    print(f"recorded {len(rel)} change(s) for {args.user_id}")
    return 0


# --- query -----------------------------------------------------------------------------------

def _load_for_query(vault: Path) -> tuple[dict | None, int]:
    path = store_path(vault)
    if not path.exists():
        print("no contributor log yet", file=sys.stderr)
        return None, 1
    try:
        return read_store(path), 0
    except CorruptStore as exc:
        print(f"error: {STORE_NAME} is corrupt ({exc})", file=sys.stderr)
        return None, 3


def query_path(vault: Path, raw_path: str, since_hours: float) -> int:
    """Was this file touched within the window, and by whom.

    Exit 0 means yes and the answer is on stdout; exit 1 means no. The caller is a heads-up before
    writing, so "no" is the common, uninteresting case and must be cheap to detect.
    """
    data, code = _load_for_query(vault)
    if data is None:
        return code
    try:
        wanted = relative_to_vault(vault, raw_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    hits: list[tuple[datetime, str, str]] = []
    for user, record in data["contributors"].items():
        for entry in record.get("entries", []):
            if entry.get("path") != wanted:
                continue
            when = parse_iso(entry.get("ts", ""))
            if when is not None and when >= cutoff:
                hits.append((when, user, entry.get("type", "?")))
    if not hits:
        return 1

    hits.sort(reverse=True)
    when, user, kind = hits[0]
    others = {u for _, u, _ in hits}
    print(f"{wanted} was {kind} by {user} at {when.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    if len(others) > 1:
        print(f"  {len(hits)} changes in the last {since_hours:g}h by "
              f"{', '.join(sorted(others))}")
    return 0


def query_user(vault: Path, user_id: str, limit: int) -> int:
    data, code = _load_for_query(vault)
    if data is None:
        return code
    record = data["contributors"].get(user_id)
    if not record or not record.get("entries"):
        print(f"no entries for {user_id}", file=sys.stderr)
        return 1
    entries = record["entries"]
    recent = sorted(entries, key=lambda e: e.get("ts", ""), reverse=True)[:limit]
    print(f"{user_id}: {len(entries)} change(s), most recent {len(recent)}:")
    for entry in recent:
        print(f"  {entry.get('ts', '?')}  {entry.get('type', '?'):6}  {entry.get('path', '?')}")
    return 0


def query_stats(vault: Path) -> int:
    """Counts only — never the log itself."""
    data, code = _load_for_query(vault)
    if data is None:
        return code
    contributors = data["contributors"]
    total = sum(len(c.get("entries", [])) for c in contributors.values())
    files = {e.get("path") for c in contributors.values() for e in c.get("entries", [])}
    print(f"{len(contributors)} contributor(s), {total} change(s), {len(files)} file(s) touched")
    ranked = sorted(contributors.items(), key=lambda kv: -len(kv[1].get("entries", [])))
    for user, record in ranked[:10]:
        print(f"  {len(record.get('entries', [])):5}  {user}")
    if len(ranked) > 10:
        print(f"  ... and {len(ranked) - 10} more")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    if args.stats:
        return query_stats(vault)
    if args.path:
        return query_path(vault, args.path, args.since_hours)
    if args.user_id:
        return query_user(vault, args.user_id, args.limit)
    print("error: query needs one of --path, --user-id or --stats", file=sys.stderr)
    return 2


# --- cli -------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    # --vault is accepted on BOTH sides of the subcommand. The caller here is an agent following
    # prose, and `record --user-id x --path y --vault <p>` is what anyone writes naturally; a tool
    # that only accepts it before the subcommand fails with an unhelpful argparse usage dump.
    # SUPPRESS on the subparser copy is load-bearing: without it the subparser's own default (".")
    # overwrites a value given at the top level, silently pointing the tool at the wrong vault.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault", default=argparse.SUPPRESS,
                        help="vault root (default: current directory)")

    parser = argparse.ArgumentParser(
        description="Record and query who changed what in this vault.")
    parser.add_argument("--vault", default=".", help="vault root (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record", parents=[common], help="append change(s) for one user")
    record.add_argument("--user-id", required=True, help="the user's raw email address")
    record.add_argument("--path", required=True, action="append",
                        help="changed file, vault-relative; repeat for several")
    record.add_argument("--type", required=True, choices=VALID_TYPES)
    record.set_defaults(func=cmd_record)

    query = sub.add_parser("query", parents=[common],
                           help="ask one bounded question about the log")
    query.add_argument("--path", help="was this file touched recently, and by whom")
    query.add_argument("--since-hours", type=float, default=24.0,
                       help="window for --path (default: 24)")
    query.add_argument("--user-id", help="what has this user changed")
    query.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                       help=f"max entries for --user-id (default: {DEFAULT_LIMIT})")
    query.add_argument("--stats", action="store_true", help="counts only")
    query.set_defaults(func=cmd_query)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except TimeoutError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
