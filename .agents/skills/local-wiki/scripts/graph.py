#!/usr/bin/env python3
"""The vault's link graph: build it from the notes, then answer questions about it.

Stdlib only (sqlite3). Subcommands:

    graph.py scan   [--full | --since-manifest]
    graph.py query  --neighbors <path> [--depth 2] [--types requires,regulates]
    graph.py query  --backlinks <path> | --orphans | --hubs [--min-degree N] | --broken | --oneway
    graph.py query  --path-between <a> <b> [--max-hops 4] | --type <rel> [--from <path>]
    graph.py query  --concept <term> | --components
    graph.py query  ... [--json] [--limit 25] [--as-of YYYY-MM-DD]
    graph.py suggest --path <p> [-k 5]
    graph.py export --json <out|->
    graph.py render --html <out>

The HTTP server that used to live here is serve.py, which imports the payload builders below.

THE design rule: **the markdown is the source of truth and this database is a cache.** It is
rebuildable from the files at any moment and never holds an edge that is not in a file. A graph
store that drifts from the notes and starts answering with edges nobody wrote is the standard
failure in this space; `scan --full` reconstructing everything is the defence.

It is also why a schema change needs no migration code: when the stored SCHEMA_VERSION differs,
connect() drops the tables and the next `scan --full` refills them from the notes. Nothing is lost
because nothing here was ever the original.

Two kinds of edge, found two different ways:

  explicit  parsed out of the markdown by scan_vault.py. Deterministic, no model. A fact.
  implicit  `suggest` only - notes that look related but are not linked. Ranked from the vault's
            own .rag embeddings when it has an index, and from shared-term overlap when it does
            not. Never written anywhere: a suggestion becomes an edge only when an agent writes a
            real link into a real note, with a reason.

Edges are TYPED (`rel_type`: requires, regulates, superseded-by, ...) and may be TEMPORAL: a note
carrying valid_from/valid_until in its frontmatter bounds the edges that leave it, so `--as-of`
answers "what did this vault say in 2024" instead of only "what does it say now". Concepts - the
vault's own glossary terms - are nodes too, derived from the manifest, never authored here.

TWO AUDIENCES, deliberately separated:

  the agent  `query --json --limit` - bounded, machine-readable, one question per call. An agent
             must never pull an unbounded dump into its context, so every query is capped.
  the user   `serve` - a local dashboard with filters, search and a canvas. The agent never opens
             it; it is for a human looking at the shape of their vault.

Link extraction deliberately lives in scan_vault.py, not here: that walk already opens every file,
so a second walk would buy nothing. This tool consumes its manifest.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

DB_NAME = "graph.sqlite"
MANIFEST = Path(".wiki") / "manifest.json"
SCHEMA_VERSION = 2
DEFAULT_DEPTH = 2
DEFAULT_HUB_DEGREE = 8
DEFAULT_K = 5
DEFAULT_LIMIT = 25
DEFAULT_MAX_HOPS = 4
# Above this, the UI shows folder clusters instead of notes and drills down on click. The
# client layout is O(n^2) per step; handing it the whole vault is how a graph page becomes a hang.
CLUSTER_ABOVE = 400
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were", "has", "have",
    "not", "but", "its", "it's", "you", "your", "their", "our", "all", "any", "can", "will",
    "when", "which", "what", "who", "how", "why", "into", "than", "then", "them", "they", "there",
    "here", "about", "also", "more", "most", "some", "such", "only", "other", "over", "under",
}


# --- paths -----------------------------------------------------------------------------------

def db_path(vault: Path) -> Path:
    return vault / ".wiki" / DB_NAME


def manifest_path(vault: Path) -> Path:
    return vault / MANIFEST


SCHEMA = """
    CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS notes (
        path TEXT PRIMARY KEY,
        title TEXT,
        slugs TEXT,
        valid_from TEXT,
        valid_until TEXT
    );
    CREATE TABLE IF NOT EXISTS edges (
        source TEXT NOT NULL,
        target TEXT NOT NULL,
        anchor TEXT,
        kind TEXT,
        text TEXT,
        rel_type TEXT,
        valid_from TEXT,
        valid_until TEXT
    );
    CREATE TABLE IF NOT EXISTS concepts (
        term TEXT PRIMARY KEY,
        definition TEXT,
        status TEXT,
        defined_in TEXT
    );
    CREATE TABLE IF NOT EXISTS concept_edges (
        term TEXT NOT NULL,
        path TEXT NOT NULL,
        kind TEXT
    );
    CREATE INDEX IF NOT EXISTS edges_source ON edges(source);
    CREATE INDEX IF NOT EXISTS edges_target ON edges(target);
    CREATE INDEX IF NOT EXISTS edges_type ON edges(rel_type);
    CREATE INDEX IF NOT EXISTS concept_edges_term ON concept_edges(term);
    CREATE INDEX IF NOT EXISTS concept_edges_path ON concept_edges(path);
"""


def connect(vault: Path) -> sqlite3.Connection:
    path = db_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row

    # A schema change costs nothing here: this store is a cache of the markdown, so the old tables
    # are dropped and the next `scan --full` rebuilds them. Writing migration code would be
    # pretending the database holds something the notes do not.
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
        stored = int(row["value"]) if row else SCHEMA_VERSION
    except (sqlite3.DatabaseError, TypeError, ValueError):
        stored = 0
    if stored != SCHEMA_VERSION:
        for table in ("edges", "notes", "concepts", "concept_edges", "meta"):
            conn.execute(f"DROP TABLE IF EXISTS {table}")

    conn.executescript(SCHEMA)
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('schema_version', ?)",
                 (str(SCHEMA_VERSION),))
    conn.commit()
    return conn


# --- temporal --------------------------------------------------------------------------------

def in_window(row: sqlite3.Row | dict, as_of: str | None) -> bool:
    """Is this edge or note valid on `as_of`? No window means always valid.

    Dates are ISO strings and compare lexicographically, which is the whole reason to store them
    that way. A malformed date is treated as no bound rather than silently excluding the edge.
    """
    if not as_of:
        return True
    start = (row["valid_from"] if "valid_from" in row.keys() else "") or ""
    end = (row["valid_until"] if "valid_until" in row.keys() else "") or ""
    if start and as_of < start:
        return False
    if end and as_of >= end:
        return False
    return True


def temporal_sql(as_of: str | None, alias: str = "") -> str:
    """The same rule as in_window(), for queries that filter in SQL."""
    if not as_of:
        return ""
    p = f"{alias}." if alias else ""
    return (f" AND (COALESCE({p}valid_from,'') = '' OR COALESCE({p}valid_from,'') <= :as_of)"
            f" AND (COALESCE({p}valid_until,'') = '' OR COALESCE({p}valid_until,'') > :as_of)")


# --- scan ------------------------------------------------------------------------------------

def load_manifest(vault: Path) -> dict:
    path = manifest_path(vault)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run scan_vault.py first — this tool reads its manifest rather "
            f"than walking the vault a second time."
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc


def cmd_scan(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    try:
        manifest = load_manifest(vault)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    records = [r for r in manifest.get("files", []) if r.get("status") != "REMOVED"]
    removed = [r for r in manifest.get("files", []) if r.get("status") == "REMOVED"]

    conn = connect(vault)
    with conn:
        if args.since_manifest:
            # Only files the scan marked NEW or CHANGED. Everything else keeps the edges it has.
            touched = [r for r in records if r.get("status") in ("NEW", "CHANGED")]
            gone = [r["path"] for r in removed]
            for record in touched:
                conn.execute("DELETE FROM edges WHERE source = ?", (record["path"],))
            for path in gone:
                # A deleted note keeps no edges, in either direction. Leaving inbound edges would
                # be a node that exists only because something used to point at it.
                conn.execute("DELETE FROM edges WHERE source = ? OR target = ?", (path, path))
                conn.execute("DELETE FROM notes WHERE path = ?", (path,))
            scanned = touched
        else:
            conn.execute("DELETE FROM edges")
            conn.execute("DELETE FROM notes")
            scanned = records

        for record in scanned:
            insert_note(conn, record)
            for link in record.get("links") or []:
                conn.execute(
                    "INSERT INTO edges VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (record["path"], link.get("target", ""), link.get("anchor") or "",
                     link.get("kind") or "inline", (link.get("text") or "")[:80],
                     link.get("rel_type") or "relates-to",
                     # An edge inherits its source note's validity window: a note that stopped
                     # being true stopped asserting its relations at the same moment.
                     record.get("valid_from") or "", record.get("valid_until") or ""),
                )
        # A full scan registers every note, so nodes with no links still exist as orphans.
        if not args.since_manifest:
            for record in records:
                insert_note(conn, record)
        rebuild_concepts(conn, manifest, records)
        conn.execute("INSERT OR REPLACE INTO meta VALUES ('scanned_at', ?)",
                     (manifest.get("scanned_at", ""),))

    notes = conn.execute("SELECT COUNT(*) AS n FROM notes").fetchone()["n"]
    edges = conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"]
    terms = conn.execute("SELECT COUNT(*) AS n FROM concepts").fetchone()["n"]
    conn.close()
    mode = "incremental" if args.since_manifest else "full"
    print(f"{mode} scan: {notes} notes, {edges} links, {terms} concepts")
    return 0


def insert_note(conn: sqlite3.Connection, record: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO notes VALUES (?, ?, ?, ?, ?)",
        (record["path"], record.get("h1") or "",
         json.dumps(record.get("heading_slugs") or []),
         record.get("valid_from") or "", record.get("valid_until") or ""),
    )


def rebuild_concepts(conn: sqlite3.Connection, manifest: dict, records: list[dict]) -> None:
    """Concept nodes, derived from the vault's own vocabulary. Never authored here.

    The manifest already counts every acronym each note uses and every definition a note states -
    that is the entity list, and it was sitting unused. A concept is a node; a note that uses the
    term gets a `mentions` edge to it, and a note that defines it gets `defined-in`.

    Rebuilt whole on every scan, incremental or not, because a term's status depends on the WHOLE
    vault: a definition added in one note changes an `inferred` term into a `defined` one, and
    patching that incrementally would need the very cross-note view this recomputes anyway. It is
    cheap - the manifest is already in memory.
    """
    conn.execute("DELETE FROM concepts")
    conn.execute("DELETE FROM concept_edges")

    # The vault-wide view wins where it exists: `glossary_candidates` already reconciled which
    # note defines a term and what it expands to, across every note.
    candidates = manifest.get("glossary_candidates") or {}
    defined: dict[str, tuple[str, str]] = {}
    if isinstance(candidates, dict):
        for term, data in candidates.items():
            where = (data.get("defined_in") or [""])[0] if isinstance(data, dict) else ""
            long = data.get("long", "") if isinstance(data, dict) else ""
            defined[term] = (long, where)

    mentions: dict[str, set[str]] = {term: set() for term in defined}
    for record in records:
        path = record["path"]
        for term, definition in (record.get("definitions") or {}).items():
            if not defined.get(term, ("", ""))[0]:
                defined[term] = (definition, path)
        for term in (record.get("acronyms") or {}):
            mentions.setdefault(term, set()).add(path)

    for term in sorted(set(defined) | set(mentions)):
        definition, source = defined.get(term, ("", ""))
        conn.execute(
            "INSERT OR REPLACE INTO concepts VALUES (?, ?, ?, ?)",
            (term, definition, "defined" if definition else "inferred", source),
        )
        if source:
            conn.execute("INSERT INTO concept_edges VALUES (?, ?, ?)", (term, source, "defined-in"))
        for path in sorted(mentions.get(term, set())):
            if path != source:
                conn.execute("INSERT INTO concept_edges VALUES (?, ?, ?)", (term, path, "mentions"))


# --- query -----------------------------------------------------------------------------------

def require_scan(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT COUNT(*) AS n FROM notes").fetchone()["n"] > 0


def adjacent(conn: sqlite3.Connection, node: str, types: set[str] | None,
             as_of: str | None) -> list[str]:
    """Every note one hop away, in either direction. A relation is a relation whichever way
    it was written, so both directions count — but a type filter and a validity window narrow it.

    Under `--as-of`, BOTH the edge and the note it reaches must have been valid then. Filtering
    only the edge lets a 2020 query reach a note written in 2026, because the 2020 note's own
    "superseded-by" line points forward in time — which produces a neighbour that did not exist.
    """
    where = ""
    params: dict[str, object] = {"node": node}
    if types:
        names = {f"t{i}": t for i, t in enumerate(sorted(types))}
        params.update(names)
        where = " AND e.rel_type IN (%s)" % ",".join(f":{k}" for k in names)
    if as_of:
        params["as_of"] = as_of
    clause = where + temporal_sql(as_of, "e")
    other_valid = temporal_sql(as_of, "n")
    rows = conn.execute(
        f"SELECT e.target AS other FROM edges e LEFT JOIN notes n ON n.path = e.target "
        f"WHERE e.source = :node{clause}{other_valid} "
        f"UNION "
        f"SELECT e.source AS other FROM edges e LEFT JOIN notes n ON n.path = e.source "
        f"WHERE e.target = :node{clause}{other_valid}", params,
    ).fetchall()
    return [row["other"] for row in rows]


def neighbors(conn: sqlite3.Connection, start: str, depth: int, types: set[str] | None = None,
              as_of: str | None = None) -> dict[str, int]:
    """Breadth-first over both directions — a relation is a relation whichever way it was written."""
    seen: dict[str, int] = {}
    frontier = {start}
    for level in range(1, depth + 1):
        nxt: set[str] = set()
        for node in frontier:
            for other in adjacent(conn, node, types, as_of):
                if other != start and other not in seen:
                    seen[other] = level
                    nxt.add(other)
        frontier = nxt
        if not frontier:
            break
    return seen


# Every query returns the same shape: a headline for humans, structured rows for the agent, and a
# renderer that turns rows into prose. One implementation, two audiences, no chance of the JSON and
# the text disagreeing about what was found.
Query = dict


def q(name: str, args_: dict, headline: str, empty: str, results: list[dict],
      render) -> Query:
    return {"query": name, "args": args_, "headline": headline, "empty": empty,
            "results": results, "render": render}


def query_neighbors(conn, path: str, depth: int, types=None, as_of=None) -> Query:
    found = neighbors(conn, path, depth, types, as_of)
    rows = [{"path": node, "hops": level}
            for node, level in sorted(found.items(), key=lambda kv: (kv[1], kv[0]))]
    return q("neighbors", {"path": path, "depth": depth},
             f"{path}: {len(rows)} related note(s) within {depth} hop(s)",
             f"{path}: nothing linked within {depth} hop(s)", rows,
             lambda rs: [f"  {r['hops']}  {r['path']}" for r in rs])


def query_backlinks(conn, path: str, as_of=None) -> Query:
    params: dict[str, object] = {"path": path}
    if as_of:
        params["as_of"] = as_of
    rows = [dict(r) for r in conn.execute(
        "SELECT DISTINCT source, kind, rel_type, text FROM edges WHERE target = :path"
        + temporal_sql(as_of) + " ORDER BY source", params).fetchall()]
    return q("backlinks", {"path": path},
             f"{len(rows)} note(s) link to {path}:", f"nothing links to {path}", rows,
             lambda rs: [f"  {r['source']}  [{r['kind']}]"
                         + (f" — {r['text']}" if r["text"] else "") for r in rs])


def query_orphans(conn) -> Query:
    disconnected = conn.execute(
        "SELECT path FROM notes WHERE path NOT IN (SELECT target FROM edges) "
        "AND path NOT IN (SELECT source FROM edges) ORDER BY path"
    ).fetchall()
    inbound_only = conn.execute(
        "SELECT path FROM notes WHERE path NOT IN (SELECT target FROM edges) "
        "AND path IN (SELECT source FROM edges) ORDER BY path"
    ).fetchall()
    rows = ([{"path": r["path"], "group": "disconnected"} for r in disconnected]
            + [{"path": r["path"], "group": "unreachable"} for r in inbound_only])

    def render(rs: list[dict]) -> list[str]:
        out = []
        first = [r for r in rs if r["group"] == "disconnected"]
        second = [r for r in rs if r["group"] == "unreachable"]
        if first:
            out.append(f"{len(first)} fully disconnected note(s):")
            out += [f"  {r['path']}" for r in first]
        if second:
            out.append(f"{len(second)} note(s) nothing links TO "
                       f"(they link out, but are unreachable):")
            out += [f"  {r['path']}" for r in second]
        return out

    return q("orphans", {}, "", "no orphans: every note is connected in both directions",
             rows, render)


def query_hubs(conn, min_degree: int) -> Query:
    rows = [dict(r) for r in conn.execute(
        "SELECT path, ("
        "  (SELECT COUNT(DISTINCT target) FROM edges WHERE source = notes.path) +"
        "  (SELECT COUNT(DISTINCT source) FROM edges WHERE target = notes.path)"
        ") AS degree FROM notes WHERE degree >= ? ORDER BY degree DESC, path",
        (min_degree,)).fetchall()]
    return q("hubs", {"min_degree": min_degree},
             f"{len(rows)} hub(s) with degree >= {min_degree} — often a note worth splitting:",
             f"no note has degree >= {min_degree}", rows,
             lambda rs: [f"  {r['degree']:4}  {r['path']}" for r in rs])


def query_broken(conn, vault: Path) -> Query:
    """Dead targets and dead anchors.

    An anchor is only judged against a note whose slugs were actually recorded — a link into a file
    the scan never read is a missing target, not a wrong anchor, and saying otherwise would send
    someone hunting for a heading in a file that isn't there.
    """
    known = {row["path"]: set(json.loads(row["slugs"] or "[]"))
             for row in conn.execute("SELECT path, slugs FROM notes").fetchall()}
    rows: list[dict] = []
    for row in conn.execute("SELECT source, target, anchor FROM edges ORDER BY source").fetchall():
        target, anchor = row["target"], row["anchor"]
        if target not in known:
            if not (vault / target).exists():
                rows.append({"source": row["source"], "target": target,
                             "why": "target does not exist"})
            continue
        if anchor and anchor not in known[target]:
            rows.append({"source": row["source"], "target": f"{target}#{anchor}",
                         "why": "no such heading in the target"})
    return q("broken", {}, f"{len(rows)} broken link(s):", "no broken links", rows,
             lambda rs: [f"  {r['source']} -> {r['target']}  ({r['why']})" for r in rs])


def query_oneway(conn) -> Query:
    rows = [dict(r) for r in conn.execute(
        "SELECT DISTINCT e.source, e.target FROM edges e "
        "WHERE NOT EXISTS (SELECT 1 FROM edges r WHERE r.source = e.target AND r.target = e.source)"
        " AND e.target IN (SELECT path FROM notes) ORDER BY e.source, e.target").fetchall()]
    return q("oneway", {},
             f"{len(rows)} one-way link(s) — the target has no ## Related line back:",
             "every link is reciprocated", rows,
             lambda rs: [f"  {r['source']} -> {r['target']}" for r in rs])


def query_path_between(conn, start: str, end: str, max_hops: int, types=None,
                       as_of=None) -> Query:
    """How are these two notes connected? The associative-retrieval primitive.

    Breadth-first from `start`, keeping the parent of each node, so the FIRST path found is a
    shortest one. Returning any old path would answer "they are connected somehow", which is not
    the question anyone asks.
    """
    parents: dict[str, str] = {start: ""}
    frontier = [start]
    hops = 0
    while frontier and end not in parents and hops < max_hops:
        hops += 1
        nxt: list[str] = []
        for node in frontier:
            for other in adjacent(conn, node, types, as_of):
                if other not in parents:
                    parents[other] = node
                    nxt.append(other)
        frontier = nxt
    rows: list[dict] = []
    if end in parents and end != start:
        chain, node = [], end
        while node:
            chain.append(node)
            node = parents[node]
        chain.reverse()
        rows = [{"step": i, "path": p} for i, p in enumerate(chain)]
    return q("path-between", {"from": start, "to": end, "max_hops": max_hops},
             f"{len(rows) - 1} hop(s) from {start} to {end}:",
             f"no path from {start} to {end} within {max_hops} hop(s)", rows,
             lambda rs: [f"  {r['step']}  {r['path']}" for r in rs])


def query_by_type(conn, rel_type: str, source: str | None, as_of=None) -> Query:
    params: dict[str, object] = {"rel": rel_type}
    clause = ""
    if source:
        params["src"] = source
        clause = " AND source = :src"
    if as_of:
        params["as_of"] = as_of
    rows = [dict(r) for r in conn.execute(
        "SELECT DISTINCT source, target, rel_type, text FROM edges WHERE rel_type = :rel"
        + clause + temporal_sql(as_of) + " ORDER BY source, target", params).fetchall()]
    where = f" from {source}" if source else ""
    return q("type", {"rel_type": rel_type, "from": source},
             f"{len(rows)} `{rel_type}` relation(s){where}:",
             f"no `{rel_type}` relation{where}", rows,
             lambda rs: [f"  {r['source']} -> {r['target']}"
                         + (f"  — {r['text']}" if r["text"] else "") for r in rs])


def query_concept(conn, term: str) -> Query:
    row = conn.execute("SELECT * FROM concepts WHERE term = ? COLLATE NOCASE", (term,)).fetchone()
    rows = [dict(r) for r in conn.execute(
        "SELECT path, kind FROM concept_edges WHERE term = ? COLLATE NOCASE "
        "ORDER BY kind, path", (term,)).fetchall()]
    definition = (row["definition"] if row else "") or ""
    status = (row["status"] if row else "unknown")
    head = f"{term} ({status})" + (f" — {definition}" if definition else "")
    return q("concept", {"term": term, "definition": definition, "status": status},
             f"{head}\n{len(rows)} note(s):", f"{term}: not a concept this vault uses", rows,
             lambda rs: [f"  [{r['kind']}]  {r['path']}" for r in rs])


def query_components(conn, as_of=None) -> Query:
    """Disconnected islands. The real measure of whether a vault is navigable.

    An orphan count says how many notes are unreachable; a component count says whether the vault
    is one body of knowledge or five that never learned about each other.
    """
    # A note outside the window is not a one-note island in that year — it did not exist.
    nodes = [r["path"] for r in conn.execute(
        "SELECT path, valid_from, valid_until FROM notes ORDER BY path").fetchall()
        if in_window(r, as_of)]
    seen: set[str] = set()
    groups: list[list[str]] = []
    for node in nodes:
        if node in seen:
            continue
        stack, group = [node], []
        seen.add(node)
        while stack:
            current = stack.pop()
            group.append(current)
            for other in adjacent(conn, current, None, as_of):
                if other not in seen and other in set(nodes):
                    seen.add(other)
                    stack.append(other)
        groups.append(sorted(group))
    groups.sort(key=lambda g: (-len(g), g[0] if g else ""))
    rows = [{"component": i, "size": len(g), "notes": g[:5],
             "truncated_notes": max(0, len(g) - 5)} for i, g in enumerate(groups)]
    return q("components", {}, f"{len(rows)} connected component(s):",
             "no notes in the graph", rows,
             lambda rs: [f"  #{r['component']}  {r['size']:4} note(s)  e.g. "
                         + ", ".join(r["notes"]) for r in rs])


def emit(query: Query, as_json: bool, limit: int) -> int:
    """Print one query's answer, bounded. Exit 0 when something was found, 1 when nothing was.

    The limit is not a convenience: an agent that can pull an unbounded result set into its context
    will eventually do it, on the vault where it hurts. Every caller gets a cap and a flag saying
    whether it bit.
    """
    results = query["results"]
    truncated = limit > 0 and len(results) > limit
    shown = results[:limit] if limit > 0 else results
    if as_json:
        print(json.dumps({"query": query["query"], "args": query["args"],
                          "count": len(results), "truncated": truncated,
                          "results": shown}, ensure_ascii=False))
        return 0 if results else 1
    if not results:
        print(query["empty"])
        return 1
    if query["headline"]:
        print(query["headline"])
    for line in query["render"](shown):
        print(line)
    if truncated:
        print(f"  … {len(results) - len(shown)} more (limit {limit})")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    conn = connect(vault)
    try:
        if not require_scan(conn):
            print("graph is empty — run `graph.py scan --full` first", file=sys.stderr)
            return 2
        types = {t.strip() for t in (args.types or "").split(",") if t.strip()} or None
        as_of = args.as_of or None
        if args.neighbors:
            query = query_neighbors(conn, args.neighbors, args.depth, types, as_of)
        elif args.backlinks:
            query = query_backlinks(conn, args.backlinks, as_of)
        elif args.orphans:
            query = query_orphans(conn)
        elif args.hubs:
            query = query_hubs(conn, args.min_degree)
        elif args.broken:
            query = query_broken(conn, vault)
        elif args.oneway:
            query = query_oneway(conn)
        elif args.path_between:
            query = query_path_between(conn, args.path_between[0], args.path_between[1],
                                       args.max_hops, types, as_of)
        elif args.type:
            query = query_by_type(conn, args.type, getattr(args, "from_path", None), as_of)
        elif args.concept:
            query = query_concept(conn, args.concept)
        elif args.components:
            query = query_components(conn, as_of)
        else:
            print("error: query needs one of --neighbors, --backlinks, --orphans, --hubs, "
                  "--broken, --oneway, --path-between, --type, --concept, --components",
                  file=sys.stderr)
            return 2
        return emit(query, args.json, args.limit)
    finally:
        conn.close()


# --- suggest ---------------------------------------------------------------------------------

def rag_available(vault: Path) -> bool:
    launcher = vault / ".rag" / "bin" / "rag"
    return launcher.is_file() and os.access(launcher, os.X_OK)


def suggest_via_rag(vault: Path, path: Path, k: int) -> list[tuple[float, str, str]]:
    """Rank by the vault's own embeddings. No second model, no second index."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    # Full sentences: these indexes are built for prose, and a keyword bag retrieves badly.
    body = "\n".join(line for line in text.splitlines()
                     if line.strip() and not line.startswith(("#", "---", "|")))
    probe = " ".join(body.split()[:120])
    if not probe:
        return []
    try:
        result = subprocess.run(
            [str(vault / ".rag" / "bin" / "rag"), "--json", "search", probe, "-k", str(k + 3)],
            capture_output=True, text=True, timeout=180, cwd=str(vault),
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    try:
        payload = json.loads(result.stdout)
    except ValueError:
        return []
    hits = payload.get("results") or payload.get("hits") or []
    out: list[tuple[float, str, str]] = []
    for hit in hits:
        target = hit.get("path") or hit.get("file") or ""
        if not target:
            continue
        out.append((float(hit.get("score") or 0.0), target, "rag-embedding"))
    return out


def suggest_via_terms(manifest: dict, source: str, k: int) -> list[tuple[float, str, str]]:
    """Shared-term overlap — the fallback, and an explainable one.

    Weighted by how rare a term is across the vault: two notes sharing "MiFID" is evidence, two
    notes sharing "the" is not. This is a cheap idf, not a claim to be a retrieval engine.
    """
    records = {r["path"]: r for r in manifest.get("files", []) if r.get("status") != "REMOVED"}
    if source not in records:
        return []

    def terms(record: dict) -> Counter:
        bag = Counter({t.lower(): c for t, c in (record.get("acronyms") or {}).items()})
        for field in ("h1", "first_line"):
            for word in re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", record.get(field) or ""):
                low = word.lower()
                if low not in STOPWORDS:
                    bag[low] += 1
        for heading in record.get("h2") or []:
            for word in re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", heading):
                low = word.lower()
                if low not in STOPWORDS:
                    bag[low] += 1
        return bag

    bags = {path: terms(record) for path, record in records.items()}
    document_count = Counter()
    for bag in bags.values():
        document_count.update(set(bag))
    total = max(len(bags), 1)

    mine = bags[source]
    scored: list[tuple[float, str, str]] = []
    for path, bag in bags.items():
        if path == source:
            continue
        shared = set(mine) & set(bag)
        if not shared:
            continue
        score = sum(1.0 / document_count[term] for term in shared) * total / max(len(shared), 1)
        scored.append((score * len(shared), path, "shared-term"))
    scored.sort(reverse=True)
    return scored[:k]


def cmd_suggest(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    source = args.path.replace("\\", "/")
    conn = connect(vault)
    try:
        linked = {row["other"] for row in conn.execute(
            "SELECT target AS other FROM edges WHERE source = ? "
            "UNION SELECT source AS other FROM edges WHERE target = ?", (source, source)
        ).fetchall()}
    finally:
        conn.close()

    signal = "shared-term"
    ranked: list[tuple[float, str, str]] = []
    if rag_available(vault):
        ranked = suggest_via_rag(vault, vault / source, args.k)
        if ranked:
            signal = "rag-embedding"
    if not ranked:
        try:
            manifest = load_manifest(vault)
        except (FileNotFoundError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        ranked = suggest_via_terms(manifest, source, args.k + len(linked))

    fresh = [(score, target) for score, target, _ in ranked
             if target != source and target not in linked][: args.k]

    # Always say which signal produced this, and always exit 0: a vault whose index has not been
    # built yet must still be usable, and "no .rag index" is a normal state, not an error.
    if not fresh:
        print(f"no unlinked candidates found for {source} (signal: {signal})")
        return 0
    print(f"{len(fresh)} candidate relation(s) for {source} (signal: {signal}):")
    for score, target in fresh:
        print(f"  {score:7.3f}  {target}")
    print("\nThese are candidates, not edges. Open the note, decide whether the relation is real, "
          "and write the link with a reason.")
    return 0


# --- export and render -----------------------------------------------------------------------

def graph_payload(conn: sqlite3.Connection, folder: str = "", rel_type: str = "",
                  as_of: str | None = None, limit: int = 0) -> dict:
    """Nodes and edges, optionally filtered. Filtering happens HERE, in SQL, not in the browser.

    The client's layout is O(n^2); handing it every note in a large vault is how a graph page
    becomes a hang. The server decides what is small enough to draw.
    """
    params: dict[str, object] = {}
    where = ""
    if folder:
        params["folder"] = folder.rstrip("/") + "/%"
        where = " WHERE path LIKE :folder"
    rows = conn.execute(
        f"SELECT path, title, valid_from, valid_until FROM notes{where} ORDER BY path", params
    ).fetchall()
    rows = [r for r in rows if in_window(r, as_of)]
    total = len(rows)
    if limit > 0:
        rows = rows[:limit]
    nodes = [row["path"] for row in rows]
    known = set(nodes)

    edge_params: dict[str, object] = {}
    clause = ""
    if rel_type:
        edge_params["rel"] = rel_type
        clause = " WHERE rel_type = :rel"
    if as_of:
        edge_params["as_of"] = as_of
        clause = (clause or " WHERE 1=1") + temporal_sql(as_of)
    edges = [
        {"source": row["source"], "target": row["target"], "anchor": row["anchor"],
         "kind": row["kind"], "rel_type": row["rel_type"] or "relates-to",
         "text": row["text"] or ""}
        for row in conn.execute(
            "SELECT DISTINCT source, target, anchor, kind, rel_type, text FROM edges"
            + clause + " ORDER BY source, target", edge_params).fetchall()
        # Only edges between known notes: a link to a file that does not exist is a `--broken`
        # finding, not a node a visualizer should draw.
        if row["source"] in known and row["target"] in known
    ]
    titles = {row["path"]: row["title"] for row in rows}
    return {"nodes": nodes, "edges": edges, "titles": titles,
            "total": total, "truncated": total > len(nodes)}


def cmd_export(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    conn = connect(vault)
    try:
        payload = graph_payload(conn)
    finally:
        conn.close()
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.json == "-":
        sys.stdout.write(text)
    else:
        Path(args.json).write_text(text, encoding="utf-8")
        print(f"{len(payload['nodes'])} nodes, {len(payload['edges'])} edges -> {args.json}")
    return 0


HTML_TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
  :root { color-scheme: light dark; }
  body { margin:0; font:14px system-ui,sans-serif; background:#fbfbfc; color:#16181d; }
  @media (prefers-color-scheme: dark) { body { background:#14161a; color:#e8eaed; } }
  #meta { position:fixed; top:12px; left:14px; opacity:.75; }
  circle { fill:#4c6ef5; cursor:pointer; }
  line { stroke:#8a90a0; stroke-opacity:.45; }
  text { font-size:10px; fill:currentColor; pointer-events:none; }
</style>
<div id="meta"></div>
<svg id="g" width="100%" height="100vh"></svg>
<script>
const DATA = __DATA__;
const svg = document.getElementById("g");
const W = svg.clientWidth, H = svg.clientHeight;
const NS = "http://www.w3.org/2000/svg";
document.getElementById("meta").textContent =
  DATA.nodes.length + " notes, " + DATA.edges.length + " links";

const idx = new Map(DATA.nodes.map((n, i) => [n, i]));
const deg = new Map(DATA.nodes.map(n => [n, 0]));
DATA.edges.forEach(e => { deg.set(e.source, deg.get(e.source)+1); deg.set(e.target, deg.get(e.target)+1); });
const pos = DATA.nodes.map((n, i) => {
  const a = (i / DATA.nodes.length) * Math.PI * 2;
  return { x: W/2 + Math.cos(a) * Math.min(W,H) * 0.36, y: H/2 + Math.sin(a) * Math.min(W,H) * 0.36, vx:0, vy:0 };
});

// Small force layout: repulsion between all nodes, springs along edges. Deliberately plain -
// a CDN is unavailable offline and this file must open from disk with nothing installed.
for (let step = 0; step < 320; step++) {
  for (let i = 0; i < pos.length; i++) for (let j = i+1; j < pos.length; j++) {
    let dx = pos[j].x-pos[i].x, dy = pos[j].y-pos[i].y;
    let d2 = dx*dx + dy*dy + 0.01, f = 900 / d2, d = Math.sqrt(d2);
    const ux = dx/d*f, uy = dy/d*f;
    pos[i].vx -= ux; pos[i].vy -= uy; pos[j].vx += ux; pos[j].vy += uy;
  }
  DATA.edges.forEach(e => {
    const a = pos[idx.get(e.source)], b = pos[idx.get(e.target)];
    if (!a || !b) return;
    const dx = b.x-a.x, dy = b.y-a.y, d = Math.sqrt(dx*dx+dy*dy)+0.01;
    const f = (d - 110) * 0.012, ux = dx/d*f, uy = dy/d*f;
    a.vx += ux; a.vy += uy; b.vx -= ux; b.vy -= uy;
  });
  pos.forEach(p => {
    p.x += Math.max(-12, Math.min(12, p.vx)); p.y += Math.max(-12, Math.min(12, p.vy));
    p.vx *= 0.82; p.vy *= 0.82;
    p.x = Math.max(24, Math.min(W-24, p.x)); p.y = Math.max(24, Math.min(H-24, p.y));
  });
}

DATA.edges.forEach(e => {
  const a = pos[idx.get(e.source)], b = pos[idx.get(e.target)];
  if (!a || !b) return;
  const l = document.createElementNS(NS, "line");
  l.setAttribute("x1", a.x); l.setAttribute("y1", a.y);
  l.setAttribute("x2", b.x); l.setAttribute("y2", b.y);
  svg.appendChild(l);
});
DATA.nodes.forEach((n, i) => {
  const c = document.createElementNS(NS, "circle");
  c.setAttribute("cx", pos[i].x); c.setAttribute("cy", pos[i].y);
  c.setAttribute("r", Math.min(14, 4 + (deg.get(n)||0)));
  const t = document.createElementNS(NS, "title");
  t.textContent = n + " (" + (deg.get(n)||0) + " links)";
  c.appendChild(t); svg.appendChild(c);
  const label = document.createElementNS(NS, "text");
  label.setAttribute("x", pos[i].x + 10); label.setAttribute("y", pos[i].y + 3);
  label.textContent = (DATA.titles[n] || n.split("/").pop());
  svg.appendChild(label);
});
</script>
"""


def cmd_render(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    conn = connect(vault)
    try:
        payload = graph_payload(conn)
    finally:
        conn.close()
    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    html = html.replace("__TITLE__", f"{vault.name} — link graph")
    Path(args.html).write_text(html, encoding="utf-8")
    print(f"{len(payload['nodes'])} nodes, {len(payload['edges'])} edges -> {args.html}")
    return 0


# --- payload builders for the UI ---------------------------------------------------------------
# The HTTP server lives in serve.py; these are what it answers with, and they are also what the
# CLI prints. One implementation, two front doors.
#
# `path` is a KEY here, always. It is looked up in the notes table and never joined to a
# filesystem path - a function that will read whatever path it is handed is a file-disclosure
# hole wherever it is called from.


def serve_stats(conn: sqlite3.Connection) -> dict:
    def scalar(sql: str) -> int:
        return conn.execute(sql).fetchone()[0]
    types = [dict(r) for r in conn.execute(
        "SELECT COALESCE(rel_type,'relates-to') AS rel_type, COUNT(*) AS n FROM edges "
        "GROUP BY rel_type ORDER BY n DESC").fetchall()]
    folders = [dict(r) for r in conn.execute(
        "SELECT CASE WHEN INSTR(path,'/') = 0 THEN '.' "
        "ELSE SUBSTR(path, 1, INSTR(path,'/') - 1) END AS folder, COUNT(*) AS n "
        "FROM notes GROUP BY folder ORDER BY folder").fetchall()]
    return {
        "notes": scalar("SELECT COUNT(*) FROM notes"),
        "edges": scalar("SELECT COUNT(*) FROM edges"),
        "concepts": scalar("SELECT COUNT(*) FROM concepts"),
        "scanned_at": (conn.execute("SELECT value FROM meta WHERE key='scanned_at'").fetchone()
                       or [""])[0],
        "relation_types": types,
        "folders": folders,
        "cluster_above": CLUSTER_ABOVE,
    }


def serve_node(conn: sqlite3.Connection, path: str) -> dict:
    """One note's neighbourhood. `path` is validated against the notes table before it is used."""
    row = conn.execute("SELECT * FROM notes WHERE path = ?", (path,)).fetchone()
    if row is None:
        return {}
    out = [dict(r) for r in conn.execute(
        "SELECT target AS path, rel_type, text, 'out' AS direction FROM edges WHERE source = ? "
        "ORDER BY target", (path,)).fetchall()]
    inbound = [dict(r) for r in conn.execute(
        "SELECT source AS path, rel_type, text, 'in' AS direction FROM edges WHERE target = ? "
        "ORDER BY source", (path,)).fetchall()]
    terms = [r["term"] for r in conn.execute(
        "SELECT DISTINCT term FROM concept_edges WHERE path = ? ORDER BY term", (path,)).fetchall()]
    return {"path": row["path"], "title": row["title"], "valid_from": row["valid_from"],
            "valid_until": row["valid_until"], "relations": out + inbound, "concepts": terms}


def serve_search(conn: sqlite3.Connection, term: str, limit: int) -> list[dict]:
    """Title, path and concept match. SQLite only — the server stays dependency-free.

    Semantic search is `.rag`'s job and the agent's; this is a human typing three letters to find
    the note they already know exists.
    """
    like = f"%{term}%"
    notes = [dict(r) for r in conn.execute(
        "SELECT path, title, 'note' AS kind FROM notes WHERE path LIKE ? OR title LIKE ? "
        "ORDER BY path LIMIT ?", (like, like, limit)).fetchall()]
    concepts = [dict(r) for r in conn.execute(
        "SELECT term AS path, definition AS title, 'concept' AS kind FROM concepts "
        "WHERE term LIKE ? ORDER BY term LIMIT ?", (like, limit)).fetchall()]
    return notes + concepts


def api_query(conn: sqlite3.Connection, vault: Path, params: dict, limit: int,
              as_of: str | None) -> dict:
    """The same queries the CLI exposes, same JSON. One implementation, two front doors."""
    kind = params.get("kind", "")
    types = {t for t in (params.get("types") or "").split(",") if t} or None
    if kind == "orphans":
        query = query_orphans(conn)
    elif kind == "hubs":
        query = query_hubs(conn, int(params.get("min_degree") or DEFAULT_HUB_DEGREE))
    elif kind == "broken":
        query = query_broken(conn, vault)
    elif kind == "oneway":
        query = query_oneway(conn)
    elif kind == "components":
        query = query_components(conn, as_of)
    elif kind == "neighbors":
        query = query_neighbors(conn, params.get("path", ""),
                                int(params.get("depth") or DEFAULT_DEPTH), types, as_of)
    elif kind == "backlinks":
        query = query_backlinks(conn, params.get("path", ""), as_of)
    elif kind == "concept":
        query = query_concept(conn, params.get("term", ""))
    elif kind == "path-between":
        query = query_path_between(conn, params.get("from", ""), params.get("to", ""),
                                   int(params.get("max_hops") or DEFAULT_MAX_HOPS), types, as_of)
    elif kind == "type":
        query = query_by_type(conn, params.get("type", ""), params.get("from") or None, as_of)
    else:
        return {"error": f"unknown query kind: {kind or '(none)'}"}
    results = query["results"]
    return {"query": query["query"], "args": query["args"], "count": len(results),
            "truncated": len(results) > limit, "results": results[:limit],
            "headline": query["headline"] or query["empty"]}


# --- cli -------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault", default=argparse.SUPPRESS,
                        help="vault root (default: current directory)")

    parser = argparse.ArgumentParser(description="Build and query the vault's link graph.")
    parser.add_argument("--vault", default=".", help="vault root (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", parents=[common], help="rebuild edges from the manifest")
    group = scan.add_mutually_exclusive_group()
    group.add_argument("--full", action="store_true", help="rebuild everything (the default)")
    group.add_argument("--since-manifest", action="store_true",
                       help="only files the manifest marked NEW or CHANGED")
    scan.set_defaults(func=cmd_scan)

    query = sub.add_parser("query", parents=[common], help="ask one question about the graph")
    query.add_argument("--neighbors", help="notes related to this one")
    query.add_argument("--depth", type=int, default=DEFAULT_DEPTH,
                       help=f"hops for --neighbors (default: {DEFAULT_DEPTH})")
    query.add_argument("--backlinks", help="notes that link to this one")
    query.add_argument("--orphans", action="store_true", help="notes nothing links to")
    query.add_argument("--hubs", action="store_true", help="unusually well-connected notes")
    query.add_argument("--min-degree", type=int, default=DEFAULT_HUB_DEGREE,
                       help=f"threshold for --hubs (default: {DEFAULT_HUB_DEGREE})")
    query.add_argument("--broken", action="store_true", help="dead targets and dead anchors")
    query.add_argument("--oneway", action="store_true", help="links with no back-edge")
    query.add_argument("--path-between", nargs=2, metavar=("FROM", "TO"),
                       help="the shortest chain of relations connecting two notes")
    query.add_argument("--max-hops", type=int, default=DEFAULT_MAX_HOPS,
                       help=f"limit for --path-between (default: {DEFAULT_MAX_HOPS})")
    query.add_argument("--type", help="every relation of this type, e.g. requires")
    query.add_argument("--from", dest="from_path", help="restrict --type to one source note")
    query.add_argument("--concept", help="notes that define or mention a glossary term")
    query.add_argument("--components", action="store_true",
                       help="disconnected islands — is this one vault or five")
    query.add_argument("--types", help="comma-separated relation types to traverse")
    query.add_argument("--as-of", help="answer as the vault stood on this date (YYYY-MM-DD)")
    query.add_argument("--json", action="store_true",
                       help="machine-readable output — what an agent should use")
    query.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                       help=f"cap on results (default: {DEFAULT_LIMIT}, 0 for no cap)")
    query.set_defaults(func=cmd_query)

    suggest = sub.add_parser("suggest", parents=[common],
                             help="candidate relations that are not linked yet")
    suggest.add_argument("--path", required=True, help="the note to find relations for")
    suggest.add_argument("-k", type=int, default=DEFAULT_K, help=f"how many (default: {DEFAULT_K})")
    suggest.set_defaults(func=cmd_suggest)

    export = sub.add_parser("export", parents=[common], help="adjacency as JSON")
    export.add_argument("--json", required=True, help="output path, or - for stdout")
    export.set_defaults(func=cmd_export)

    render = sub.add_parser("render", parents=[common], help="a standalone graph page")
    render.add_argument("--html", required=True, help="output path")
    render.set_defaults(func=cmd_render)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
