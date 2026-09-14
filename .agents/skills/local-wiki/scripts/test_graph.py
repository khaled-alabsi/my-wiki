#!/usr/bin/env python3
"""Tests for graph.py (cases 18-25 of the plan's matrix).

    python3 test_graph.py

The two that carry the design:

  18/19  the graph is a pure function of the files. Scanning twice changes nothing; deleting a note
         removes its edges. A cache that accumulates state the markdown no longer supports is the
         standard failure in this space, and these are what stop it.
  23     suggest degrades when there is no .rag index instead of crashing. A vault whose index
         hasn't been built yet must still be usable.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "graph.py"
SCANNER = HERE / "scan_vault.py"

_failures: list[str] = []
_passed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _passed
    if condition:
        _passed += 1
        print(f"  ok    {name}")
    else:
        _failures.append(f"{name}: {detail}")
        print(f"  FAIL  {name}  {detail}")


def make_vault(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="graph-test-"))
    (root / ".wiki").mkdir()
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def run(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GRAPH), *args, "--vault", str(vault)],
                          capture_output=True, text=True)


def scan(vault: Path, *extra: str) -> subprocess.CompletedProcess:
    """The real two-step workflow: scan_vault.py writes the manifest, graph.py consumes it.

    graph.py deliberately does not walk the vault itself, so a test that skips this step is
    testing nothing that resembles how the tool is used.
    """
    manifest = vault / ".wiki" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(SCANNER), "--root", str(vault), "--out", str(manifest)]
    if manifest.exists():
        cmd += ["--previous", str(manifest)]
    scanned = subprocess.run(cmd, capture_output=True, text=True)
    if scanned.returncode != 0:
        raise AssertionError(f"scan_vault.py failed: {scanned.stderr[:400]}")
    return run(vault, "scan", *extra)


def snapshot(vault: Path) -> str:
    result = run(vault, "export", "--json", "-")
    return result.stdout


SIMPLE = {
    "notes/a.md": "# A\n\n[to b](b.md)\n",
    "notes/b.md": "# B\n\n## Related\n- [back to a](a.md) — reciprocal\n",
    "notes/c.md": "# C\n\nnothing links here\n",
}


# --- 18: scanning twice is idempotent --------------------------------------------------------

def test_scan_is_idempotent() -> None:
    vault = make_vault(SIMPLE)
    first = scan(vault, "--full")
    check("18 first scan exits 0", first.returncode == 0, first.stderr[:300])
    before = snapshot(vault)
    scan(vault, "--full")
    after = snapshot(vault)
    check("18 a second scan over unchanged files produces an identical graph",
          before == after and before.strip() != "", "the cache is not a pure function of the files")


# --- 19: deleting a note leaves no stale edges -----------------------------------------------

def test_delete_removes_edges() -> None:
    vault = make_vault(SIMPLE)
    scan(vault, "--full")
    (vault / "notes" / "b.md").unlink()
    scan(vault, "--full")
    data = json.loads(snapshot(vault))
    nodes = set(data.get("nodes", []))
    edges = [(e["source"], e["target"]) for e in data.get("edges", [])]
    check("19 the deleted note is gone from the graph", "notes/b.md" not in nodes, str(nodes))
    check("19 no edge still points at the deleted note",
          not any(t == "notes/b.md" for _, t in edges), str(edges))
    check("19 no edge still originates from it",
          not any(s == "notes/b.md" for s, _ in edges), str(edges))


# --- 20: oneway and backlinks ----------------------------------------------------------------

def test_oneway_and_backlinks() -> None:
    vault = make_vault({
        "notes/a.md": "# A\n\n[to b](b.md)\n",       # a -> b, no back-edge
        "notes/b.md": "# B\n",
    })
    scan(vault, "--full")
    oneway = run(vault, "query", "--oneway")
    check("20 --oneway names the unreciprocated pair",
          "notes/a.md" in oneway.stdout and "notes/b.md" in oneway.stdout, oneway.stdout[:200])
    back = run(vault, "query", "--backlinks", "notes/b.md")
    check("20 --backlinks b finds a", "notes/a.md" in back.stdout, back.stdout[:200])
    check("20 --backlinks exits 0 when there is one", back.returncode == 0, back.stderr[:200])


# --- 21: orphans -----------------------------------------------------------------------------

def test_orphans() -> None:
    vault = make_vault(SIMPLE)
    scan(vault, "--full")
    result = run(vault, "query", "--orphans")
    check("21 a note nothing links to is an orphan",
          "notes/c.md" in result.stdout, result.stdout[:200])
    check("21 a linked note is not an orphan",
          "notes/b.md" not in result.stdout, result.stdout[:200])


# --- 22: broken targets and dead anchors -----------------------------------------------------

def test_broken() -> None:
    vault = make_vault({
        "notes/a.md": "# A\n\n[dead anchor](b.md#gone-heading) and [dead file](missing.md)\n",
        "notes/b.md": "# B\n\n## Real Heading\n",
    })
    scan(vault, "--full")
    result = run(vault, "query", "--broken")
    check("22 a dead anchor is reported",
          "gone-heading" in result.stdout, result.stdout[:300])
    check("22 a missing target file is reported",
          "missing.md" in result.stdout, result.stdout[:300])
    check("22 the source of each broken link is named",
          "notes/a.md" in result.stdout, result.stdout[:300])
    check("22 a live anchor is NOT reported",
          "real-heading" not in result.stdout.lower(), result.stdout[:300])


# --- 23: suggest degrades without a .rag index -----------------------------------------------

def test_suggest_without_rag() -> None:
    vault = make_vault({
        "notes/a.md": "# A\n\nMiFID target market assessment and suitability rules.\n",
        "notes/b.md": "# B\n\nMiFID suitability and target market checks for advisors.\n",
        "notes/z.md": "# Z\n\nUnrelated content about catering invoices.\n",
    })
    scan(vault, "--full")
    result = run(vault, "suggest", "--path", "notes/a.md", "-k", "5")
    check("23 suggest exits 0 with no .rag index", result.returncode == 0,
          f"exit {result.returncode}: {result.stderr[:300]}")
    check("23 suggest says which signal it used",
          "shared-term" in (result.stdout + result.stderr).lower(),
          (result.stdout + result.stderr)[:300])
    check("23 the topically similar note is suggested",
          "notes/b.md" in result.stdout, result.stdout[:300])
    check("23 suggest does not propose the note itself",
          "notes/a.md" not in result.stdout.replace("notes/a.md ", "", 1), result.stdout[:200])


# --- 24: export is loadable ------------------------------------------------------------------

def test_export_json() -> None:
    vault = make_vault(SIMPLE)
    scan(vault, "--full")
    out = vault / "graph.json"
    result = run(vault, "export", "--json", str(out))
    check("24 export exits 0", result.returncode == 0, result.stderr[:200])
    data = json.loads(out.read_text(encoding="utf-8"))
    check("24 export has nodes and edges", {"nodes", "edges"} <= set(data), str(sorted(data)))
    check("24 edges carry source and target",
          all({"source", "target"} <= set(e) for e in data["edges"]), str(data["edges"][:2]))
    check("24 every edge endpoint is a known node",
          all(e["source"] in data["nodes"] and e["target"] in data["nodes"]
              for e in data["edges"]), "an edge points at a node not in the node list")


# --- 25: incremental scan touches only what changed ------------------------------------------

def test_incremental_scan() -> None:
    vault = make_vault(SIMPLE)
    scan(vault, "--full")
    (vault / "notes" / "c.md").write_text("# C\n\n[now links to a](a.md)\n", encoding="utf-8")
    result = scan(vault, "--since-manifest")
    check("25 incremental scan exits 0", result.returncode == 0, result.stderr[:300])
    data = json.loads(snapshot(vault))
    edges = {(e["source"], e["target"]) for e in data["edges"]}
    check("25 the edited file's new edge is picked up",
          ("notes/c.md", "notes/a.md") in edges, str(sorted(edges)))
    check("25 untouched files keep their edges",
          ("notes/a.md", "notes/b.md") in edges, str(sorted(edges)))


def test_neighbors_depth() -> None:
    vault = make_vault({
        "notes/a.md": "# A\n\n[b](b.md)\n",
        "notes/b.md": "# B\n\n[c](c.md)\n",
        "notes/c.md": "# C\n",
    })
    scan(vault, "--full")
    d1 = run(vault, "query", "--neighbors", "notes/a.md", "--depth", "1")
    check("26 depth 1 finds the direct neighbour",
          "notes/b.md" in d1.stdout, d1.stdout[:200])
    check("26 depth 1 does not reach two hops",
          "notes/c.md" not in d1.stdout, d1.stdout[:200])
    d2 = run(vault, "query", "--neighbors", "notes/a.md", "--depth", "2")
    check("26 depth 2 reaches two hops", "notes/c.md" in d2.stdout, d2.stdout[:200])


# --- 27-34: typed relations, temporal windows, the JSON API, concepts, components -------------

TYPED = {
    "reg/psd2.md": (
        "---\nvalid_from: 2018-01-13\nvalid_until: 2026-01-01\n---\n\n# PSD2\n\n"
        "PSD2 (Payment Services Directive 2) governs payments.\n\n"
        "## Related\n"
        "- regulates :: [sca](../pay/sca.md) — mandates strong customer authentication\n"
        "- superseded-by :: [psd3](psd3.md) — from 2026-01\n"
    ),
    "reg/psd3.md": "---\nvalid_from: 2026-01-01\n---\n\n# PSD3\n\n## Related\n"
                   "- supersedes :: [psd2](psd2.md) — replaces it\n",
    "pay/sca.md": "# SCA\n\nSCA is required.\n\n## Related\n"
                  "- part-of :: [checkout](checkout.md) — a step in the flow\n",
    "pay/checkout.md": "# Checkout\n",
    "orphan.md": "# Lonely island\n",
}


def typed_vault() -> Path:
    vault = make_vault(TYPED)
    scan(vault, "--full")
    return vault


def json_query(vault: Path, *args: str) -> dict:
    result = run(vault, "query", *args, "--json")
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise AssertionError(f"not JSON: {exc}: {result.stdout[:200]} {result.stderr[:200]}")


def test_typed_edges_are_queryable() -> None:
    vault = typed_vault()
    payload = json_query(vault, "--type", "regulates")
    check("27 --type finds the typed edge", payload["count"] == 1, str(payload))
    check("27 --type names source and target",
          payload["results"][0]["source"] == "reg/psd2.md"
          and payload["results"][0]["target"] == "pay/sca.md", str(payload["results"]))
    empty = json_query(vault, "--type", "implements")
    check("27 an unused type returns nothing, not everything", empty["count"] == 0, str(empty))


def test_types_filter_narrows_traversal() -> None:
    vault = typed_vault()
    everything = json_query(vault, "--neighbors", "reg/psd2.md", "--depth", "2")
    narrowed = json_query(vault, "--neighbors", "reg/psd2.md", "--depth", "2",
                          "--types", "regulates")
    check("28 unfiltered traversal reaches further", everything["count"] > narrowed["count"],
          f"{everything['count']} vs {narrowed['count']}")
    check("28 filtered traversal keeps only the typed hop",
          [r["path"] for r in narrowed["results"]] == ["pay/sca.md"], str(narrowed["results"]))


def test_as_of_hides_what_did_not_exist_yet() -> None:
    """The failure this locks: an edge valid in 2020 pointing at a note written in 2026."""
    vault = typed_vault()
    then = json_query(vault, "--neighbors", "reg/psd2.md", "--depth", "1", "--as-of", "2020-01-01")
    paths = [r["path"] for r in then["results"]]
    check("29 as-of keeps the relation that was live", "pay/sca.md" in paths, str(paths))
    check("29 as-of drops the note that did not exist yet", "reg/psd3.md" not in paths, str(paths))
    now = json_query(vault, "--neighbors", "reg/psd2.md", "--depth", "1")
    check("29 without as-of both are present", len(now["results"]) == 2, str(now["results"]))


def test_as_of_excludes_notes_outside_their_window() -> None:
    vault = typed_vault()
    then = json_query(vault, "--components", "--as-of", "2020-01-01")
    sizes = sorted(r["size"] for r in then["results"])
    check("30 a note not yet valid is not a one-note island", sizes == [1, 3], str(then["results"]))


def test_path_between_finds_the_shortest_chain() -> None:
    vault = typed_vault()
    payload = json_query(vault, "--path-between", "reg/psd2.md", "pay/checkout.md")
    steps = [r["path"] for r in payload["results"]]
    check("31 the chain starts and ends where asked",
          steps[:1] == ["reg/psd2.md"] and steps[-1:] == ["pay/checkout.md"], str(steps))
    check("31 the chain is the shortest one", steps == ["reg/psd2.md", "pay/sca.md",
                                                        "pay/checkout.md"], str(steps))
    none = json_query(vault, "--path-between", "orphan.md", "pay/sca.md")
    check("31 an unreachable pair returns no path", none["count"] == 0, str(none))


def test_components_finds_islands() -> None:
    vault = typed_vault()
    payload = json_query(vault, "--components")
    check("32 the island is found", payload["count"] == 2, str(payload["results"]))
    smallest = min(payload["results"], key=lambda r: r["size"])
    check("32 the island is the orphan", smallest["notes"] == ["orphan.md"], str(smallest))


def test_concepts_are_derived_from_the_vault() -> None:
    vault = typed_vault()
    payload = json_query(vault, "--concept", "PSD2")
    check("33 the term is a node", payload["count"] >= 1, str(payload))
    check("33 the definition came from the note that states it",
          "Payment Services" in (payload["args"].get("definition") or ""), str(payload["args"]))
    check("33 the defining note is linked",
          any(r["kind"] == "defined-in" for r in payload["results"]), str(payload["results"]))


def test_json_is_bounded() -> None:
    vault = typed_vault()
    capped = json_query(vault, "--neighbors", "reg/psd2.md", "--depth", "2", "--limit", "1")
    check("34 the limit caps the results", len(capped["results"]) == 1, str(capped))
    check("34 truncation is declared", capped["truncated"] is True, str(capped))
    check("34 the true count is still reported", capped["count"] > 1, str(capped))
    full = json_query(vault, "--neighbors", "reg/psd2.md", "--depth", "2", "--limit", "0")
    check("34 limit 0 means no cap", full["truncated"] is False, str(full))


def test_schema_upgrade_rebuilds_instead_of_migrating() -> None:
    """A v1 store must not survive as a v1 store — it is a cache, so it gets rebuilt."""
    import sqlite3
    vault = typed_vault()
    db = vault / ".wiki" / "graph.sqlite"
    conn = sqlite3.connect(str(db))
    conn.execute("UPDATE meta SET value = '1' WHERE key = 'schema_version'")
    conn.commit()
    conn.close()
    result = run(vault, "query", "--orphans")
    check("35 an old schema does not crash the tool", result.returncode in (0, 1, 2),
          result.stderr[:300])
    check("35 the old store was dropped, not migrated",
          "no such column" not in result.stderr, result.stderr[:300])
    scan(vault, "--full")
    payload = json_query(vault, "--type", "regulates")
    check("35 a rescan refills it", payload["count"] == 1, str(payload))


def main() -> int:
    for tool in (GRAPH, SCANNER):
        if not tool.exists():
            print(f"{tool.name} not found at {tool}", file=sys.stderr)
            return 2
    print("graph.py")
    for fn in (test_scan_is_idempotent, test_delete_removes_edges, test_oneway_and_backlinks,
               test_orphans, test_broken, test_suggest_without_rag, test_export_json,
               test_incremental_scan, test_neighbors_depth,
               test_typed_edges_are_queryable, test_types_filter_narrows_traversal,
               test_as_of_hides_what_did_not_exist_yet,
               test_as_of_excludes_notes_outside_their_window,
               test_path_between_finds_the_shortest_chain, test_components_finds_islands,
               test_concepts_are_derived_from_the_vault, test_json_is_bounded,
               test_schema_upgrade_rebuilds_instead_of_migrating):
        try:
            fn()
        except Exception as exc:
            _failures.append(f"{fn.__name__} raised {exc!r}")
            print(f"  ERROR {fn.__name__}: {exc!r}")
    print()
    if _failures:
        print(f"{len(_failures)} failed, {_passed} passed")
        for line in _failures:
            print(f"  - {line}")
        return 1
    print(f"all {_passed} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
