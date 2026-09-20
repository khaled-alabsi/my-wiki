#!/usr/bin/env python3
"""Tests for tags.py - the one writer of a note's tags and of the vault's tag tree.

    python3 test_tags.py

What these lock, because each is silent when broken:

  1-4   a tag write changes the `tags` line and NOTHING else in the note - not a byte of the body,
        not another frontmatter key, not the newline style.
  5     a tag missing from the inventory is refused, and the refusal names the command that lists
        it. That exit code is what keeps the inventory complete; a paragraph asking for it is not.
  9     the inventory is sorted by SEGMENT, not by byte. `-` sorts below `/`, so a bytewise sort
        lets `banking-ops` land in the middle of `banking`'s subtree and breaks every prefix slice.
  13-14 `check` exits non-zero on drift in either direction, and spares the lookalikes: an interior
        node carried only through its children, a note that spells a tag in another case.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "tags.py"
SCANNER = HERE / "scan_vault.py"

INVENTORY = (
    "# Tags\n\n"
    "- `banking` — Everything about running a bank.\n"
    "- `banking/accounts` — Opening and keeping accounts.\n"
    "- `banking/accounts/onboarding` — Taking on a new client. (aka kyc-intake)\n"
    "- `regulation` — Rules a bank must follow.\n"
    "- `regulation/mifid` — EU investor protection.\n"
)

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


def load_tool():
    spec = importlib.util.spec_from_file_location("tags_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE))
    spec.loader.exec_module(module)

    return module


def build_vault(files: dict[str, str], inventory: str | None = INVENTORY) -> Path:
    vault = Path(tempfile.mkdtemp(prefix="tags-test-"))
    for rel, text in files.items():
        path = vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    if inventory is not None:
        (vault / ".wiki").mkdir(exist_ok=True)
        (vault / ".wiki" / "tags.md").write_text(inventory, encoding="utf-8")

    return vault


def run(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), "--vault", str(vault), *args],
                          capture_output=True, text=True)


def scan(vault: Path) -> None:
    done = subprocess.run([sys.executable, str(SCANNER), "--root", str(vault),
                           "--out", str(vault / ".wiki" / "manifest.json")],
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError(f"scan failed: {done.stderr[:300]}")


def read(vault: Path, rel: str) -> str:
    return (vault / rel).read_bytes().decode("utf-8")


def read_inventory_paths(vault: Path) -> list[str]:
    lines = (vault / ".wiki" / "tags.md").read_text(encoding="utf-8").splitlines()

    return [line.split("`")[1] for line in lines if line.startswith("- `")]


# --- 1-4: the frontmatter writer ---------------------------------------------------------------

def test_set_creates_a_block_and_keeps_the_body() -> None:
    body = "# Note\n\nSome prose.\n\n## Related\n- [x](x.md) — why\n"
    vault = build_vault({"n.md": body})
    done = run(vault, "set", "n.md", "--add", "regulation/mifid")
    check("1 set on a note without frontmatter succeeds", done.returncode == 0, done.stdout + done.stderr)
    text = read(vault, "n.md")
    check("1 the block is created with the one written form",
          text.startswith("---\ntags: [regulation/mifid]\n---\n"), text[:80])
    check("1 the body is byte-identical", text.endswith(body) and text.count("# Note") == 1, text)


def test_set_inserts_one_line_and_keeps_the_rest() -> None:
    before = "---\r\ntitle: \"A: b\"\r\nvalid_from: 2024-01-13\r\n---\r\n\r\n# N\r\n"
    vault = build_vault({"n.md": before})
    run(vault, "set", "n.md", "--add", "banking/accounts")
    text = read(vault, "n.md")
    want = "---\r\ntitle: \"A: b\"\r\nvalid_from: 2024-01-13\r\ntags: [banking/accounts]\r\n---\r\n\r\n# N\r\n"
    check("2 one line is inserted, every other byte and the CRLF style kept", text == want, repr(text))


def test_set_replaces_a_block_list_with_the_inline_form() -> None:
    before = "---\ntitle: T\ntags:\n  - Banking/Accounts\n  - regulation\nstatus: draft\n---\n\n# N\n"
    vault = build_vault({"n.md": before})
    run(vault, "set", "n.md", "--add", "regulation/mifid")
    text = read(vault, "n.md")
    want = "---\ntitle: T\ntags: [banking/accounts, regulation/mifid]\nstatus: draft\n---\n\n# N\n"
    check("3 a block list becomes the inline form, in place", text == want, repr(text))


def test_removing_the_last_tag_removes_the_key() -> None:
    vault = build_vault({
        "keep.md": "---\ntitle: T\ntags: [regulation]\n---\n\n# N\n",
        "only.md": "# N\n\nBody.\n",
    })
    run(vault, "set", "keep.md", "--remove", "regulation")
    check("4 the key goes, the other keys stay",
          read(vault, "keep.md") == "---\ntitle: T\n---\n\n# N\n", repr(read(vault, "keep.md")))
    run(vault, "set", "only.md", "--add", "regulation")
    run(vault, "set", "only.md", "--remove", "regulation")
    check("4 a block that held only tags goes with them, and the note is as it was",
          read(vault, "only.md") == "# N\n\nBody.\n", repr(read(vault, "only.md")))


# --- 5-8: what `set` refuses and what it normalises ---------------------------------------------

def test_a_tag_outside_the_inventory_is_refused() -> None:
    before = "# N\n"
    vault = build_vault({"n.md": before})
    done = run(vault, "set", "n.md", "--add", "payments/sca")
    check("5 an unlisted tag exits 2", done.returncode == 2, str(done.returncode))
    check("5 the note is untouched", read(vault, "n.md") == before, read(vault, "n.md"))
    message = done.stdout + done.stderr
    check("5 the refusal names the command that lists it",
          "add payments/sca" in message, message)


def test_set_normalises_the_list() -> None:
    vault = build_vault({"n.md": "# N\n"})
    run(vault, "set", "n.md", "--add", "regulation", "--add", "Regulation/MiFID",
        "--add", "banking", "--add", "regulation/mifid")
    text = read(vault, "n.md")
    check("6 ancestors dropped, duplicates removed, sorted, lowercased",
          text.startswith("---\ntags: [banking, regulation/mifid]\n---\n"), text[:70])


def test_a_write_that_changes_nothing_is_not_a_write() -> None:
    vault = build_vault({"n.md": "---\ntags: [regulation/mifid]\n---\n\n# N\n"})
    path = vault / "n.md"
    os.utime(path, (1_000_000_000, 1_000_000_000))
    done = run(vault, "set", "n.md", "--add", "regulation/mifid")
    check("7 an unchanged result exits 0", done.returncode == 0, done.stdout + done.stderr)
    check("7 and leaves the mtime alone", int(path.stat().st_mtime) == 1_000_000_000,
          str(path.stat().st_mtime))
    check("7 and says so", "unchanged" in done.stdout, done.stdout)


def test_set_refuses_paths_that_are_not_notes() -> None:
    vault = build_vault({"n.md": "# N\n", "data.csv": "a,b\n", ".wiki/memo.md": "# M\n"})
    outside = Path(tempfile.mkdtemp(prefix="tags-outside-")) / "x.md"
    outside.write_text("# X\n", encoding="utf-8")
    for label, target in (("outside the vault", str(outside)), ("under .wiki", ".wiki/memo.md"),
                          ("not a note", "data.csv"), ("climbing out", "../x.md")):
        done = run(vault, "set", target, "--add", "regulation")
        check(f"8 a path {label} exits 2", done.returncode == 2, f"{done.returncode} {done.stderr}")
    check("8 the file outside the vault is untouched", outside.read_text() == "# X\n")


# --- 9-12: the tree -----------------------------------------------------------------------------

def test_add_keeps_the_tree_sorted_by_segment() -> None:
    vault = build_vault({"n.md": "# N\n"})
    check("9 a missing parent exits 2 and names the parent's add",
          run(vault, "add", "payments/sca").returncode == 2
          and "add payments" in (run(vault, "add", "payments/sca").stdout
                                 + run(vault, "add", "payments/sca").stderr))
    for bad in ("bad:colon", "has space", "2024", "a//b", "a/"):
        check(f"9 `{bad}` is not a tag", run(vault, "add", bad).returncode == 2)
    run(vault, "add", "banking-ops", "--meaning", "Back-office work.")
    run(vault, "add", "Banking/Cards", "--meaning", "Card products.", "--aka", "Plastic, debit")
    paths = read_inventory_paths(vault)
    check("9 `banking-ops` does not split `banking`'s subtree",
          paths == ["banking", "banking/accounts", "banking/accounts/onboarding", "banking/cards",
                    "banking-ops", "regulation", "regulation/mifid"], str(paths))
    text = (vault / ".wiki" / "tags.md").read_text(encoding="utf-8")
    check("9 the meaning and the aliases are written on the line",
          "- `banking/cards` — Card products. (aka plastic, debit)\n" in text, text)
    before = text
    done = run(vault, "add", "banking/cards", "--meaning", "Different words.")
    check("9 a node already listed exits 0 and changes nothing",
          done.returncode == 0 and (vault / ".wiki" / "tags.md").read_text(encoding="utf-8") == before,
          done.stdout)


def test_add_creates_the_inventory_when_there_is_none() -> None:
    vault = build_vault({"n.md": "# N\n"}, inventory=None)
    done = run(vault, "add", "banking", "--meaning", "Running a bank.")
    check("9 the first add creates the inventory", done.returncode == 0
          and read_inventory_paths(vault) == ["banking"], done.stdout + done.stderr)


def test_add_stops_at_the_cap() -> None:
    vault = build_vault({"a.md": "---\ntags: [regulation/mifid]\n---\n# A\n"})
    (vault / ".wiki" / "wiki-config.json").write_text(json.dumps({"tag_nodes_max": 5}))
    before = (vault / ".wiki" / "tags.md").read_text(encoding="utf-8")
    done = run(vault, "add", "payments")
    check("10 a full inventory exits 3", done.returncode == 3, f"{done.returncode} {done.stdout}")
    check("10 nothing is written",
          (vault / ".wiki" / "tags.md").read_text(encoding="utf-8") == before)
    check("10 the cheapest merges are named, carried leaves last",
          "move banking/accounts/onboarding banking/accounts" in done.stderr, done.stderr)


def test_move_renames_a_subtree_and_its_carriers() -> None:
    vault = build_vault({
        "a.md": "---\ntags: [banking/accounts/onboarding]\n---\n\n# A\n",
        "b.md": "---\ntitle: B\ntags: [banking/accounts, regulation/mifid]\n---\n\n# B\n",
        "c.md": "---\ntags: [regulation]\n---\n\n# C\n",
    })
    c_before = read(vault, "c.md")
    done = run(vault, "move", "banking/accounts", "banking/clients")
    check("11 a rename succeeds", done.returncode == 0, done.stdout + done.stderr)
    check("11 the node and its descendants move in the inventory",
          read_inventory_paths(vault) == ["banking", "banking/clients", "banking/clients/onboarding",
                                     "regulation", "regulation/mifid"], str(read_inventory_paths(vault)))
    check("11 a carrier of the node is rewritten",
          "tags: [banking/clients, regulation/mifid]" in read(vault, "b.md"), read(vault, "b.md"))
    check("11 a carrier of a descendant is rewritten",
          "tags: [banking/clients/onboarding]" in read(vault, "a.md"), read(vault, "a.md"))
    check("11 a note that carries neither is untouched", read(vault, "c.md") == c_before)
    text = (vault / ".wiki" / "tags.md").read_text(encoding="utf-8")
    check("11 meanings travel with their nodes",
          "- `banking/clients/onboarding` — Taking on a new client. (aka kyc-intake)" in text, text)

    merge = run(vault, "move", "banking/clients/onboarding", "banking/clients")
    check("11 moving a leaf onto its parent is a merge", merge.returncode == 0
          and "banking/clients/onboarding" not in read_inventory_paths(vault), merge.stdout + merge.stderr)
    check("11 the merged leaf's carriers now carry the parent",
          "tags: [banking/clients]" in read(vault, "a.md"), read(vault, "a.md"))
    check("11 a move under its own descendant exits 2",
          run(vault, "move", "regulation", "regulation/mifid/old").returncode == 2)
    check("11 a move under a missing parent exits 2",
          run(vault, "move", "regulation/mifid", "nowhere/mifid").returncode == 2)
    check("11 moving a node that is not listed exits 2",
          run(vault, "move", "ghost", "banking/ghost").returncode == 2)


def test_drop_only_takes_an_empty_leaf() -> None:
    vault = build_vault({"a.md": "---\ntags: [regulation/mifid]\n---\n\n# A\n"})
    check("12 a node with a carrier is not dropped", run(vault, "drop", "regulation/mifid").returncode == 2)
    check("12 a node with children is not dropped", run(vault, "drop", "banking").returncode == 2)
    done = run(vault, "drop", "banking/accounts/onboarding")
    check("12 an empty leaf is dropped", done.returncode == 0
          and "banking/accounts/onboarding" not in read_inventory_paths(vault), done.stdout + done.stderr)


# --- 13-14: the consistency command -------------------------------------------------------------

CONSISTENT = {
    "a.md": "---\ntags: [banking/accounts/onboarding]\n---\n\n# A\n",
    "b.md": "---\ntags: [Regulation/MiFID]\n---\n\n# B\n",
    "c.md": "# C\n\nNo tags at all.\n",
}


def test_check_passes_a_consistent_vault() -> None:
    vault = build_vault(CONSISTENT)
    done = run(vault, "check")
    check("13 a consistent vault exits 0", done.returncode == 0, done.stdout + done.stderr)
    check("13 an interior node carried only through its children is not an orphan",
          "banking/accounts" not in done.stdout.split("warn")[0], done.stdout)
    check("13 a tag in another case matches its node", "regulation/mifid" not in done.stdout
          or "FAIL" not in done.stdout, done.stdout)
    check("13 no vault at all to check is not an error either",
          run(build_vault({"n.md": "# N\n"}, inventory=None), "check").returncode == 0)


def assert_drift_fails(files: dict[str, str],
                       inventory: str,
                       kind: str,
                       needle: str) -> None:
    vault = build_vault(files, inventory)
    done = run(vault, "check")
    check(f"14 {kind} exits 1", done.returncode == 1, f"{done.returncode} {done.stdout}")
    check(f"14 {kind} names what to run", needle in done.stdout, done.stdout)
    report = json.loads(run(vault, "check", "--json").stdout)
    check(f"14 {kind} is a failure in --json too",
          report["ok"] is False and any(f["kind"] == kind for f in report["failures"]), str(report))


def test_check_fails_on_each_kind_of_drift() -> None:
    assert_drift_fails({**CONSISTENT, "d.md": "---\ntags: [payments/sca]\n---\n# D\n"}, INVENTORY,
                       "unlisted", "add payments/sca")
    assert_drift_fails(CONSISTENT, INVENTORY + "- `payments` — Moving money.\n", "unused", "drop payments")
    assert_drift_fails({**CONSISTENT, "d.md": "---\ntags: [payments/sca]\n---\n# D\n"},
            INVENTORY + "- `payments/sca` — Strong customer authentication.\n",
            "orphan", "add payments")
    assert_drift_fails({**CONSISTENT, "d.md": "---\ntags: [bad:colon]\n---\n# D\n"}, INVENTORY,
            "malformed", "bad:colon")
    assert_drift_fails(CONSISTENT, INVENTORY + "- `regulation/mifid` — Twice.\n", "duplicate", "regulation/mifid")


def test_check_warnings_never_fail() -> None:
    files = dict(CONSISTENT)
    files["d.md"] = "---\ntags: [regulation, regulation/mifid]\n---\n# D\n"
    vault = build_vault(files, INVENTORY.replace(" — EU investor protection.", ""))
    done = run(vault, "check")
    check("14 warnings alone exit 0", done.returncode == 0, done.stdout + done.stderr)
    check("14 a node carried beside its ancestor is a warning", "ancestor" in done.stdout, done.stdout)
    check("14 a node without a meaning is a warning", "meaning" in done.stdout, done.stdout)


# --- 15-16: the work list ------------------------------------------------------------------------

PENDING_FILES = {
    "index.md": "# Index\n",
    "reg/see-also.md": "# See also\n",
    "reg/mifid.md": "# MiFID\n\nInvestor protection.\n\n## Scope\n",
    "reg/psd2.md": "---\ntags: [regulation]\n---\n\n# PSD2\n",
    "bank/onboarding.md": "# Onboarding\n\nTaking on a client.\n",
    "_drafts/scrap.md": "# Scrap\n",
}


def test_pending_lists_untagged_notes_live() -> None:
    vault = build_vault(PENDING_FILES)
    check("15 pending without a manifest exits 2 and names the scan",
          run(vault, "pending").returncode == 2 and "scan_vault.py" in run(vault, "pending").stderr)
    scan(vault)
    report = json.loads(run(vault, "pending", "--json").stdout)
    paths = [note["path"] for note in report["notes"]]
    check("15 untagged notes are listed, routing files and working folders are not",
          paths == ["bank/onboarding.md", "reg/mifid.md"], str(paths))
    check("15 the folder counts head the list", report["folders"] == {"bank": 1, "reg": 1},
          str(report["folders"]))
    check("15 a record carries the note's skeleton, not its text",
          report["notes"][1].get("h1") == "MiFID" and report["notes"][1].get("h2") == ["Scope"]
          and "text" not in report["notes"][1], str(report["notes"][1]))
    scoped = json.loads(run(vault, "pending", "--scope", "reg", "--json").stdout)
    check("15 --scope narrows to a subtree", [n["path"] for n in scoped["notes"]] == ["reg/mifid.md"])
    limited = json.loads(run(vault, "pending", "--limit", "1", "--json").stdout)
    check("15 --limit bounds the records and keeps the true total",
          len(limited["notes"]) == 1 and limited["total"] == 2, str(limited))

    run(vault, "set", "reg/mifid.md", "--add", "regulation/mifid")
    after = json.loads(run(vault, "pending", "--json").stdout)
    check("15 a note tagged a moment ago leaves the list with no rescan",
          [n["path"] for n in after["notes"]] == ["bank/onboarding.md"], str(after["notes"]))


def test_retag_keeps_a_receipt_and_deletes_it_when_done() -> None:
    vault = build_vault(PENDING_FILES)
    scan(vault)
    receipt = vault / ".wiki" / ".tag-run.json"
    first = json.loads(run(vault, "pending", "--retag", "--json").stdout)
    check("16 a retag lists tagged notes too",
          [n["path"] for n in first["notes"]] == ["bank/onboarding.md", "reg/mifid.md", "reg/psd2.md"],
          str(first["notes"]))
    check("16 a retag opens a receipt", receipt.exists())
    check("16 batch-done without a retag under way exits 2",
          run(build_vault(PENDING_FILES), "batch-done", "reg").returncode == 2)
    run(vault, "batch-done", "reg")
    second = json.loads(run(vault, "pending", "--retag", "--json").stdout)
    check("16 a finished folder leaves the list",
          [n["path"] for n in second["notes"]] == ["bank/onboarding.md"], str(second["notes"]))
    run(vault, "batch-done", "bank")
    last = json.loads(run(vault, "pending", "--retag", "--json").stdout)
    check("16 nothing pending deletes the receipt", last["total"] == 0 and not receipt.exists(),
          f"{last} exists={receipt.exists()}")


# --- the pure functions the UI shares -----------------------------------------------------------

def test_with_tags_is_the_one_writer() -> None:
    tool = load_tool()
    text = "---\ntitle: T\n---\n\n# N\n"
    once = tool.with_tags(text, ["regulation/mifid"])
    check("1 with_tags adds the line", once == "---\ntitle: T\ntags: [regulation/mifid]\n---\n\n# N\n", once)
    check("4 with_tags round-trips to the original", tool.with_tags(once, []) == text,
          tool.with_tags(once, []))
    try:
        tool.with_tags("---\ntitle: never closed\n\n# N\n", ["regulation"])
        check("1 an unclosed frontmatter block is refused", False, "no error raised")
    except ValueError:
        check("1 an unclosed frontmatter block is refused", True)


# --- 17-18: one writer at a time ----------------------------------------------------------------
# An agent fires several `add` calls in one block, so they run AT ONCE. Each is a read-modify-write
# of one file, so with no exclusive lock the last writer wins and the others' nodes are gone - while
# every one of them prints `listed`. Two sequential calls in one process cannot see any of this:
# they pass against a tags.py with no locking at all, which is how the first attempt at a fix
# shipped broken.

def add_in_parallel(vault: Path, tags: list[str]) -> list[str]:
    """Run one `add` per tag, all at the same time, and return what each one said."""

    workers = [subprocess.Popen([sys.executable, str(TOOL), "--vault", str(vault),
                                 "add", tag, "--meaning", f"node {i}"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
               for i, tag in enumerate(tags)]

    return [worker.communicate()[0].strip() for worker in workers]


def test_parallel_adds_all_land() -> None:
    vault = build_vault({"n.md": "# N\n"}, inventory="# Tags\n\n- `root`\n")
    wanted = [f"root/n{i}" for i in range(12)]
    said = add_in_parallel(vault, wanted)
    listed = read_inventory_paths(vault)
    missing = [tag for tag in wanted if tag not in listed]
    check("17 every node of a parallel batch lands in the tree", not missing,
          f"lost {len(missing)}: {missing}")
    check("17 the tree gains exactly those nodes, none twice",
          sorted(listed) == sorted(["root"] + wanted), str(listed))
    check("17 and each process reported what it actually did",
          sum(1 for line in said if line.endswith(": listed")) == len(wanted), str(said))


def test_parallel_adds_of_one_node_make_one_line() -> None:
    vault = build_vault({"n.md": "# N\n"}, inventory="# Tags\n\n- `root`\n")
    said = add_in_parallel(vault, ["root/same"] * 8)
    listed = read_inventory_paths(vault)
    check("18 one node, however many processes raced for it",
          listed.count("root/same") == 1, str(listed))
    check("18 exactly one of them listed it; the rest found it already there",
          sum(1 for line in said if line.endswith(": listed")) == 1, str(said))


def test_the_lock_file_survives_its_own_release() -> None:
    """The deterministic half of 17-18, and the one that catches the exact defect.

    Deleting the lock file on release is what makes a lock stop locking: a process still waiting on
    the old inode and one arriving afterwards open two DIFFERENT files, and both believe they hold
    it. The parallel tests above only catch that when the timing happens to line up; this catches it
    every time. Measured with the deletion live: 12 parallel adds, 12 reported success, 10 landed."""

    tool = load_tool()
    vault = build_vault({"n.md": "# N\n"})
    path = tool._locate_lock(vault)
    with tool._claim_tag_lock(vault):
        check("19 the lock is a real file while it is held", path.exists(), str(path))
        held = path.stat().st_ino
    check("19 and releasing it leaves that same file in place",
          path.exists() and path.stat().st_ino == held,
          "the lock file was deleted on release, so the next process locks a different inode")


def main() -> int:
    if not TOOL.exists():
        print(f"tags.py not found at {TOOL}", file=sys.stderr)
        return 2
    print("tags.py - the tag writer and the tag tree")
    for fn in (test_set_creates_a_block_and_keeps_the_body, test_set_inserts_one_line_and_keeps_the_rest,
               test_set_replaces_a_block_list_with_the_inline_form,
               test_removing_the_last_tag_removes_the_key, test_with_tags_is_the_one_writer,
               test_a_tag_outside_the_inventory_is_refused, test_set_normalises_the_list,
               test_a_write_that_changes_nothing_is_not_a_write, test_set_refuses_paths_that_are_not_notes,
               test_add_keeps_the_tree_sorted_by_segment, test_add_creates_the_inventory_when_there_is_none,
               test_add_stops_at_the_cap, test_move_renames_a_subtree_and_its_carriers,
               test_drop_only_takes_an_empty_leaf, test_check_passes_a_consistent_vault,
               test_check_fails_on_each_kind_of_drift, test_check_warnings_never_fail,
               test_pending_lists_untagged_notes_live, test_retag_keeps_a_receipt_and_deletes_it_when_done,
               test_parallel_adds_all_land, test_parallel_adds_of_one_node_make_one_line,
               test_the_lock_file_survives_its_own_release):
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
