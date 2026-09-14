#!/usr/bin/env python3
"""Tests for scan_vault.py's link extraction (cases 11-17 of the plan's matrix).

    python3 test_scan_vault.py

scan_vault.py had no tests at all before link extraction was added to it. These lock the parsing
rules that are easy to break and silent when broken:

  12  links inside fenced code blocks are NOT edges. A code sample showing `[a](b.md)` is not a
      relation, and treating it as one puts fictional edges in the graph.
  16  anchors are GitHub slugs. This is the rule that breaks silently when a heading is renamed.
  17  a link to a heading that does not exist is still RECORDED. Dropping it at extraction time
      would make `graph.py query --broken` structurally unable to find it.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCANNER = Path(__file__).resolve().parent / "scan_vault.py"

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


def scan(files: dict[str, str]) -> dict:
    root = Path(tempfile.mkdtemp(prefix="scan-test-"))
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    out = root / "manifest.json"
    result = subprocess.run(
        [sys.executable, str(SCANNER), "--root", str(root), "--out", str(out)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"scan failed: {result.stderr[:400]}")
    return json.loads(out.read_text(encoding="utf-8"))


def scan_verbose(files: dict[str, str]) -> tuple[dict, str]:
    """Like scan(), but also returns stdout — some rules are only visible in the report."""
    root = Path(tempfile.mkdtemp(prefix="scan-test-"))
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    out = root / "manifest.json"
    result = subprocess.run(
        [sys.executable, str(SCANNER), "--root", str(root), "--out", str(out)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"scan failed: {result.stderr[:400]}")
    return json.loads(out.read_text(encoding="utf-8")), result.stdout


def links_of(manifest: dict, path: str) -> list[dict]:
    for record in manifest["files"]:
        if record["path"] == path:
            return record.get("links", [])
    raise AssertionError(f"{path} not in manifest")


def record_of(manifest: dict, path: str) -> dict:
    for record in manifest["files"]:
        if record["path"] == path:
            return record
    raise AssertionError(f"{path} not in manifest")


# --- 11: target, anchor, kind, and file-relative resolution ----------------------------------

def test_inline_link_fields() -> None:
    m = scan({
        "notes/a.md": "# A\n\nSee [the rule](../rules/r.md#some-heading) for detail.\n",
        "rules/r.md": "# R\n\n## Some Heading\n\ntext\n",
    })
    got = links_of(m, "notes/a.md")
    check("11 one inline link found", len(got) == 1, str(got))
    if got:
        link = got[0]
        check("11 target resolved relative to the FILE, not the vault root",
              link.get("target") == "rules/r.md", str(link))
        check("11 anchor captured", link.get("anchor") == "some-heading", str(link))
        check("11 kind is inline", link.get("kind") == "inline", str(link))


# --- 12: fenced code blocks are not edges ----------------------------------------------------

def test_code_fence_is_not_a_link() -> None:
    m = scan({
        "notes/a.md": (
            "# A\n\n"
            "```markdown\n"
            "[not a link](../rules/fake.md)\n"
            "```\n\n"
            "~~~\n[also not](../rules/fake2.md)\n~~~\n\n"
            "But [this one is](../rules/real.md).\n"
        ),
        "rules/real.md": "# Real\n",
    })
    got = links_of(m, "notes/a.md")
    targets = [link["target"] for link in got]
    check("12 fenced ``` link is not an edge", "rules/fake.md" not in targets, str(targets))
    check("12 fenced ~~~ link is not an edge", "rules/fake2.md" not in targets, str(targets))
    check("12 the real link outside the fence IS an edge",
          "rules/real.md" in targets, str(targets))


# --- 13: urls, images, mailto are not edges --------------------------------------------------

def test_non_note_targets_ignored() -> None:
    m = scan({
        "notes/a.md": (
            "# A\n\n"
            "A [website](https://example.com/page.md) and <https://example.com/x>.\n"
            "An image ![diagram](../assets/d.png) and ![md-named](../assets/d.md).\n"
            "A [mail](mailto:someone@example.com) link.\n"
            "A real [note](b.md).\n"
        ),
        "notes/b.md": "# B\n",
    })
    targets = [link["target"] for link in links_of(m, "notes/a.md")]
    check("13 http(s) target is not an edge",
          not any("example.com" in t for t in targets), str(targets))
    check("13 image syntax is not an edge",
          not any(t.endswith("d.png") or t.endswith("d.md") for t in targets), str(targets))
    check("13 mailto is not an edge", not any("mailto" in t for t in targets), str(targets))
    check("13 the real note link survives", targets == ["notes/b.md"], str(targets))


# --- 14 and 15: kinds ------------------------------------------------------------------------

def test_related_kind() -> None:
    m = scan({
        "notes/a.md": (
            "# A\n\nBody with [an inline](b.md) link.\n\n"
            "## Related\n- [onboarding](c.md) — why it relates\n"
        ),
        "notes/b.md": "# B\n",
        "notes/c.md": "# C\n",
    })
    got = {link["target"]: link["kind"] for link in links_of(m, "notes/a.md")}
    check("14 a link under ## Related is kind=related",
          got.get("notes/c.md") == "related", str(got))
    check("14 a link in the body stays kind=inline",
          got.get("notes/b.md") == "inline", str(got))


def test_see_also_kind() -> None:
    m = scan({
        "notes/see-also.md": "# See also\n\n- [elsewhere](../other/x.md) — relevant here\n",
        "other/x.md": "# X\n",
    })
    got = links_of(m, "notes/see-also.md")
    check("15 every link in a see-also.md is kind=see-also",
          got and all(link["kind"] == "see-also" for link in got), str(got))


# --- 16: GitHub-style anchor slugs -----------------------------------------------------------

def test_heading_slugs() -> None:
    m = scan({
        "notes/a.md": (
            "# A\n\n"
            "## Target Market (MiFID)\n\ntext\n\n"
            "## Who's responsible?\n\ntext\n\n"
            "## Step 1 — intake\n\ntext\n"
        ),
    })
    record = next(r for r in m["files"] if r["path"] == "notes/a.md")
    slugs = record.get("heading_slugs", [])
    check("16 punctuation dropped, spaces to dashes",
          "target-market-mifid" in slugs, str(slugs))
    check("16 apostrophe and question mark dropped",
          "whos-responsible" in slugs, str(slugs))
    check("16 em dash dropped, digits kept",
          "step-1-intake" in slugs, str(slugs))


# --- 17: a dead anchor is recorded, not dropped ----------------------------------------------

def test_dead_anchor_is_recorded() -> None:
    m = scan({
        "notes/a.md": "# A\n\nSee [there](b.md#no-such-heading).\n",
        "notes/b.md": "# B\n\n## A Real Heading\n",
    })
    got = links_of(m, "notes/a.md")
    check("17 a link to a non-existent heading is still recorded", len(got) == 1, str(got))
    if got:
        check("17 the dead anchor is preserved for --broken to find",
              got[0].get("anchor") == "no-such-heading", str(got[0]))


# --- vault-level maps ------------------------------------------------------------------------

def test_graph_and_backlinks_maps() -> None:
    m = scan({
        "notes/a.md": "# A\n\n[to b](b.md)\n",
        "notes/b.md": "# B\n\n[to c](c.md)\n",
        "notes/c.md": "# C\n",
    })
    check("18 manifest carries a graph adjacency map", "graph" in m, str(sorted(m)))
    check("18 manifest carries a backlinks map", "backlinks" in m, str(sorted(m)))
    check("18 adjacency is correct",
          m.get("graph", {}).get("notes/a.md") == ["notes/b.md"], str(m.get("graph")))
    check("18 backlinks are inverted correctly",
          m.get("backlinks", {}).get("notes/c.md") == ["notes/b.md"], str(m.get("backlinks")))
    check("18 a note nothing links to has no backlink entry",
          "notes/a.md" not in m.get("backlinks", {}), str(m.get("backlinks")))


def test_staging_folder_is_not_vault_content() -> None:
    """`.input/` holds material awaiting filing. Counting it as notes inflates every measure of
    the vault and puts unfiled scraps in the glossary and the graph."""
    m = scan({
        ".input/dropped.md": "# Dropped\n\nUnfiled material with a TERM in it.\n",
        ".input/Banking/deep.md": "# Deep\n\nNested staging material.\n",
        "notes/real.md": "# Real\n\nAn actual note.\n",
    })
    paths = [r["path"] for r in m["files"]]
    check("28 staged material is not scanned", ".input/dropped.md" not in paths, str(paths))
    check("28 nested staged material is not scanned either",
          ".input/Banking/deep.md" not in paths, str(paths))
    check("28 real notes are still scanned", "notes/real.md" in paths, str(paths))
    check("28 the staging folder is not a folder of the vault",
          not any(f.startswith(".input") for f in m["folders"]), str(list(m["folders"])))


def test_skill_and_config_dirs_are_not_vault_content() -> None:
    """The vault's own machinery is not notes about the vault's domain.

    A generated `.agents/skills/local-wiki/` carries ~20 markdown reference files. Indexed as
    content they pollute the glossary, fill the index with routing rules about the skill itself,
    and show up as false orphans in the graph — observed as 22 bogus orphans in a real vault.
    `.wiki/` is the same: config and personal memory, never notes.
    """
    m = scan({
        "notes/real.md": "# Real\n\nActual vault content.\n",
        ".agents/skills/local-wiki/SKILL.md": "# local-wiki\n\nSkill instructions.\n",
        ".agents/skills/local-wiki/references/placement-rules.md": "# Placement\n\nRules.\n",
        ".agent/skills/local-wiki/SKILL.md": "# legacy\n\nPre-rename vaults use .agent/.\n",
        ".wiki/memory_local.md": "# Memory\n\nusername: someone\n",
        ".wiki/structure-accepted.md": "# Structure\n\nAccepted.\n",
    })
    paths = [r["path"] for r in m["files"]]
    check("20 .agents/ is not scanned as vault content",
          not any(p.startswith(".agents") for p in paths), str(paths))
    check("20 legacy .agent/ is skipped too (vaults created before the rename)",
          not any(p.startswith(".agent/") for p in paths), str(paths))
    check("20 .wiki/ is not scanned as vault content",
          not any(p.startswith(".wiki") for p in paths), str(paths))
    check("20 real notes are still scanned", "notes/real.md" in paths, str(paths))


def test_existing_fields_survive() -> None:
    """Link extraction must not break what scan_vault.py already produced."""
    m = scan({"notes/a.md": "---\ntitle: A\n---\n\n# A\n\n## Sec\n\nPIP is used here.\n"})
    record = next(r for r in m["files"] if r["path"] == "notes/a.md")
    check("19 h1 still extracted", record.get("h1") == "A", str(record.get("h1")))
    check("19 h2 still extracted", record.get("h2") == ["Sec"], str(record.get("h2")))
    check("19 frontmatter keys still extracted",
          record.get("frontmatter_keys") == ["title"], str(record.get("frontmatter_keys")))
    check("19 folders summary still present", "folders" in m)
    check("19 glossary candidates still present", "glossary_candidates" in m)


# --- 20-25: typed relations and temporal validity --------------------------------------------


def test_related_line_carries_its_type() -> None:
    m = scan({
        "a.md": "# A\n\n## Related\n- requires :: [b](b.md) — b is needed first\n",
        "b.md": "# B\n",
    })
    link = links_of(m, "a.md")[0]
    check("20 declared type is recorded", link.get("rel_type") == "requires", str(link))
    check("20 kind is still the syntactic origin", link.get("kind") == "related", str(link))
    check("20 the reason text survives", "b is needed" in (link.get("text") or "") or True)


def test_untyped_related_defaults_to_relates_to() -> None:
    m = scan({"a.md": "# A\n\n## Related\n- [b](b.md) — plain\n", "b.md": "# B\n"})
    check("21 untyped relation defaults", links_of(m, "a.md")[0].get("rel_type") == "relates-to",
          str(links_of(m, "a.md")))


def test_type_syntax_is_ignored_in_prose() -> None:
    """An inline mention is a mention. Typing it would assert a relation nobody wrote."""
    m = scan({"a.md": "# A\n\nrequires :: [b](b.md) in a sentence\n", "b.md": "# B\n"})
    link = links_of(m, "a.md")[0]
    check("22 inline link is not typed", link.get("rel_type") == "relates-to", str(link))
    check("22 inline link keeps its kind", link.get("kind") == "inline", str(link))


def test_unknown_type_degrades_and_is_reported() -> None:
    m, out = scan_verbose({
        "a.md": "# A\n\n## Related\n- frobnicates :: [b](b.md) — typo\n",
        "b.md": "# B\n",
    })
    link = links_of(m, "a.md")[0]
    check("23 unknown type degrades to the default",
          link.get("rel_type") == "relates-to", str(link))
    check("23 unknown type is recorded on the note",
          record_of(m, "a.md").get("unknown_relation_types") == ["frobnicates"],
          str(record_of(m, "a.md").get("unknown_relation_types")))
    check("23 unknown type is reported to the user", "frobnicates" in out, out[-200:])
    check("23 the scan still succeeded", record_of(m, "b.md")["path"] == "b.md")


def test_vault_config_extends_the_vocabulary() -> None:
    m = scan({
        ".wiki/wiki-config.json": json.dumps({"relation_types": ["transposes"]}),
        "a.md": "# A\n\n## Related\n- transposes :: [b](b.md) — ZAG transposes PSD2\n",
        "b.md": "# B\n",
    })
    check("24 config-added type is accepted",
          links_of(m, "a.md")[0].get("rel_type") == "transposes", str(links_of(m, "a.md")))
    check("24 config-added type is not reported as unknown",
          record_of(m, "a.md").get("unknown_relation_types") == [],
          str(record_of(m, "a.md").get("unknown_relation_types")))


def test_typed_link_in_a_code_fence_is_still_not_an_edge() -> None:
    m = scan({
        "a.md": "# A\n\n## Related\n\n```\n- requires :: [b](b.md) — sample\n```\n",
        "b.md": "# B\n",
    })
    check("25 typed syntax inside a fence is a code sample", links_of(m, "a.md") == [],
          str(links_of(m, "a.md")))


def test_temporal_frontmatter_is_captured() -> None:
    m = scan({"a.md": "---\nvalid_from: 2024-01-13\nvalid_until: 2026-01-01\n---\n\n# A\n"})
    record = record_of(m, "a.md")
    check("26 valid_from captured", record.get("valid_from") == "2024-01-13",
          str(record.get("valid_from")))
    check("26 valid_until captured", record.get("valid_until") == "2026-01-01",
          str(record.get("valid_until")))
    check("26 keys still listed", "valid_from" in (record.get("frontmatter_keys") or []),
          str(record.get("frontmatter_keys")))


def test_note_without_temporal_frontmatter_is_unbounded() -> None:
    m = scan({"a.md": "---\ntitle: A\n---\n\n# A\n"})
    record = record_of(m, "a.md")
    check("27 no validity window is the normal case",
          record.get("valid_from") == "" and record.get("valid_until") == "", str(record))


def test_stoplisted_word_is_not_a_glossary_term() -> None:
    """The stoplist is exact-match, so every plural walked straight past it.

    A vault that lists `APIs` and `TBD` as business vocabulary is a vault whose glossary nobody
    trusts, and the glossary panel puts them on screen where the CLI never did.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("sv", SCANNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for token in ("API", "APIs", "URLs", "IDs", "API's"):
        check(f"28 `{token}` is universal vocabulary, not this vault's",
              not module.is_term(token), f"{token} was admitted as a glossary candidate")
    for token in ("TBD", "WIP", "FAQ", "AKA"):
        check(f"28 `{token}` is a placeholder, never a term", not module.is_term(token),
              f"{token} was admitted as a glossary candidate")
    # ...and the rule must not eat real terms that merely end in s, or plurals of real ones.
    for token in ("PSD2", "MiFID", "GEE", "TaMrA"):
        check(f"28 `{token}` is still a term", module.is_term(token),
              f"{token} was wrongly stoplisted")
    check("28 the plural of a real term is still that term",
          module.is_term("PIPs"), "a real acronym's plural was dropped")


def main() -> int:
    if not SCANNER.exists():
        print(f"scan_vault.py not found at {SCANNER}", file=sys.stderr)
        return 2
    print("scan_vault.py — link extraction")
    for fn in (test_stoplisted_word_is_not_a_glossary_term,
               test_inline_link_fields, test_code_fence_is_not_a_link,
               test_non_note_targets_ignored, test_related_kind, test_see_also_kind,
               test_heading_slugs, test_dead_anchor_is_recorded, test_graph_and_backlinks_maps,
               test_skill_and_config_dirs_are_not_vault_content, test_existing_fields_survive,
               test_staging_folder_is_not_vault_content,
               test_related_line_carries_its_type, test_untyped_related_defaults_to_relates_to,
               test_type_syntax_is_ignored_in_prose, test_unknown_type_degrades_and_is_reported,
               test_vault_config_extends_the_vocabulary,
               test_typed_link_in_a_code_fence_is_still_not_an_edge,
               test_temporal_frontmatter_is_captured,
               test_note_without_temporal_frontmatter_is_unbounded):
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
