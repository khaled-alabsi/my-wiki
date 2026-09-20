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

import importlib.util
import json
import sqlite3
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


# --- 36-46: the tag tree ------------------------------------------------------------------------
# A tag is a full path; a note under a child is under every ancestor. `reg_a` beside `regxa` is
# there on purpose: `_` is a legal tag character and a SQL LIKE wildcard, so a prefix match written
# with LIKE returns the wrong notes and nothing raises.

TAGGED = {
    ".wiki/tags.md": (
        "# Tags\n\n"
        "- `banking` — Running a bank.\n"
        "- `banking/mifid` — EU investor protection.\n"
        "- `banking/mifid/target-market`\n"
        "- `banking/payments` — Moving money.\n"
        "- `reg_a`\n"
        "- `reg_a/x`\n"
    ),
    "notes/a.md": "---\ntags: [banking/mifid/target-market]\n---\n\n# A\n",
    "notes/b.md": "---\ntags: [banking/mifid]\n---\n\n# B\n",
    "notes/c.md": "---\nvalid_from: 2025-01-01\ntags: [banking/payments]\n---\n\n# C\n",
    "notes/d.md": "---\ntags: [reg_a/x]\n---\n\n# D\n",
    "notes/e.md": "---\ntags: [regxa/y]\n---\n\n# E\n",
    "notes/f.md": "# F\n\nNo tags.\n",
}


def build_tagged_vault() -> Path:
    vault = make_vault(TAGGED)
    scan(vault, "--full")
    return vault


def load_graph_module():
    spec = importlib.util.spec_from_file_location("graph_under_test", GRAPH)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE))
    spec.loader.exec_module(module)
    return module


def tree_rows(vault: Path, *args: str) -> dict[str, dict]:
    return {row["tag"]: row for row in json_query(vault, "--tag-tree", *args)["results"]}


def test_tag_ancestors_are_nodes() -> None:
    vault = build_tagged_vault()
    conn = sqlite3.connect(str(vault / ".wiki" / "graph.sqlite"))
    parents = dict(conn.execute("SELECT path, parent FROM tags").fetchall())
    conn.close()
    check("36 every ancestor of a carried tag is a node",
          {"banking", "banking/mifid", "banking/mifid/target-market", "regxa"} <= set(parents),
          str(sorted(parents)))
    check("36 a node knows its parent, and a top-level node has none",
          parents.get("banking/mifid") == "banking" and parents.get("banking") == "", str(parents))


def test_tag_query_returns_descendants() -> None:
    vault = build_tagged_vault()
    wide = json_query(vault, "--tag", "banking")
    paths = [row["path"] for row in wide["results"]]
    check("37 a node returns the notes of everything under it, once each",
          paths == ["notes/a.md", "notes/b.md", "notes/c.md"], str(paths))
    check("37 each row says which tag put it there",
          wide["results"][0].get("tag") == "banking/mifid/target-market", str(wide["results"][0]))
    narrow = [row["path"] for row in json_query(vault, "--tag", "Banking/MiFID")["results"]]
    check("37 a deeper node is narrower, and case does not matter",
          narrow == ["notes/a.md", "notes/b.md"], str(narrow))


def test_underscore_in_a_tag_is_not_a_wildcard() -> None:
    vault = build_tagged_vault()
    paths = [row["path"] for row in json_query(vault, "--tag", "reg_a")["results"]]
    check("38 `reg_a` does not match `regxa`", paths == ["notes/d.md"], str(paths))


def test_unknown_tag_finds_nothing() -> None:
    vault = build_tagged_vault()
    result = run(vault, "query", "--tag", "nowhere")
    check("39 an unknown tag exits 1", result.returncode == 1, str(result.returncode))
    check("39 and says so", "nowhere" in result.stdout, result.stdout)


def test_tag_tree_is_one_level_with_counts() -> None:
    vault = build_tagged_vault()
    top = tree_rows(vault)
    check("40 the root lists top-level nodes only",
          sorted(top) == ["banking", "reg_a", "regxa"], str(sorted(top)))
    check("40 a node counts the distinct notes under it", top["banking"]["notes"] == 3
          and top["banking"]["direct"] == 0 and top["banking"]["children"] == 2, str(top["banking"]))
    under = tree_rows(vault, "banking")
    check("40 asking for a node lists its children",
          sorted(under) == ["banking/mifid", "banking/payments"], str(sorted(under)))
    check("40 a child counts its own and its subtree's notes",
          under["banking/mifid"]["notes"] == 2 and under["banking/mifid"]["direct"] == 1,
          str(under["banking/mifid"]))
    bounded = json_query(vault, "--tag-tree", "--limit", "1")
    check("40 the tree is bounded and says when the bound bit",
          len(bounded["results"]) == 1 and bounded["truncated"] is True, str(bounded))


def test_tag_meaning_comes_from_the_inventory() -> None:
    vault = build_tagged_vault()
    top = tree_rows(vault)
    check("41 a listed node carries its meaning", top["banking"]["meaning"] == "Running a bank."
          and top["banking"]["listed"] is True, str(top["banking"]))
    check("41 a node only the notes carry is marked unlisted", top["regxa"]["listed"] is False
          and top["regxa"]["meaning"] == "", str(top["regxa"]))


def test_incremental_scan_rebuilds_tags_whole() -> None:
    vault = build_tagged_vault()
    (vault / "notes" / "d.md").write_text("# D\n\nNo longer tagged, and longer.\n", encoding="utf-8")
    scan(vault, "--since-manifest")
    check("42 a tag taken off a note leaves the graph on an incremental scan",
          run(vault, "query", "--tag", "reg_a").returncode == 1,
          run(vault, "query", "--tag", "reg_a").stdout)
    check("42 the other notes keep theirs", json_query(vault, "--tag", "banking")["count"] == 3)


def test_tag_tables_survive_a_schema_upgrade() -> None:
    vault = build_tagged_vault()
    conn = sqlite3.connect(str(vault / ".wiki" / "graph.sqlite"))
    conn.execute("UPDATE meta SET value = '2' WHERE key = 'schema_version'")
    conn.execute("DROP TABLE tags")
    conn.commit()
    conn.close()
    result = run(vault, "query", "--tag", "banking")
    check("43 a store from before tags is rebuilt, not crashed on",
          "no such table" not in result.stderr, result.stderr[:300])
    scan(vault, "--full")
    check("43 a rescan refills the tags", json_query(vault, "--tag", "banking")["count"] == 3)


def test_tag_query_honours_as_of() -> None:
    vault = build_tagged_vault()
    paths = [row["path"] for row in
             json_query(vault, "--tag", "banking", "--as-of", "2024-06-01")["results"]]
    check("44 a note outside its window is not under the tag that year",
          paths == ["notes/a.md", "notes/b.md"], str(paths))


def test_suggest_uses_a_shared_tag() -> None:
    vault = make_vault({
        ".wiki/tags.md": "- `fruit`\n- `fruit/rare`\n",
        "notes/a.md": "---\ntags: [fruit/rare]\n---\n\n# Alpha\n\nApples.\n",
        "notes/b.md": "---\ntags: [fruit/rare]\n---\n\n# Beta\n\nBoats.\n",
        "notes/z.md": "# Zeta\n\nZebras.\n",
    })
    scan(vault, "--full")
    result = run(vault, "suggest", "--path", "notes/a.md", "-k", "5")
    check("45 two notes sharing nothing but a tag are candidates",
          "notes/b.md" in result.stdout and "notes/z.md" not in result.stdout, result.stdout[:300])


def test_tag_graph_payload() -> None:
    graph = load_graph_module()
    vault = build_tagged_vault()
    conn = graph.connect(vault)
    try:
        whole = graph.build_tag_graph_payload(conn)
        by_id = {node["id"]: node for node in whole["nodes"]}
        check("46 every tag node is in the tag graph, as a tag",
              {"banking", "banking/mifid", "reg_a/x", "regxa/y"} <= set(by_id)
              and all(node["kind"] == "tag" for node in whole["nodes"]), str(sorted(by_id)))
        check("46 a node's size is the notes under it", by_id["banking"]["notes"] == 3
              and by_id["banking/mifid/target-market"]["notes"] == 1, str(by_id["banking"]))
        check("46 a child hangs off its parent",
              {"source": "banking", "target": "banking/mifid", "rel_type": "parent-of"} in whole["edges"],
              str(whole["edges"][:4]))
        bounded = graph.build_tag_graph_payload(conn, limit=2)
        check("46 the limit bounds the nodes and says so",
              len(bounded["nodes"]) == 2 and bounded["truncated"] is True
              and bounded["total"] == len(whole["nodes"]), str(bounded))
        rooted = graph.build_tag_graph_payload(conn, root="banking/mifid", notes=True)
        kinds = {node["id"]: node["kind"] for node in rooted["nodes"]}
        check("46 a rooted graph holds that subtree and, when asked, its notes as leaves",
              kinds == {"banking/mifid": "tag", "banking/mifid/target-market": "tag",
                        "notes/a.md": "note", "notes/b.md": "note"}, str(kinds))
        check("46 a note leaf hangs off the tag it carries",
              {"source": "banking/mifid", "target": "notes/b.md", "rel_type": "tagged"} in rooted["edges"],
              str(rooted["edges"]))
    finally:
        conn.close()


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
               test_schema_upgrade_rebuilds_instead_of_migrating,
               test_tag_ancestors_are_nodes, test_tag_query_returns_descendants,
               test_underscore_in_a_tag_is_not_a_wildcard, test_unknown_tag_finds_nothing,
               test_tag_tree_is_one_level_with_counts, test_tag_meaning_comes_from_the_inventory,
               test_incremental_scan_rebuilds_tags_whole, test_tag_tables_survive_a_schema_upgrade,
               test_tag_query_honours_as_of, test_suggest_uses_a_shared_tag,
               test_tag_graph_payload):
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
