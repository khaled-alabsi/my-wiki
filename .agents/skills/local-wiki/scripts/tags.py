#!/usr/bin/env python3
"""The one writer of a note's tags and of the vault's tag tree.

Stdlib only. The agent DECIDES which tags a note carries (references/tagging.md); this tool only
carries the decision out, and refuses the ones that would let the notes and the tree drift apart.

A tag is a full path in a tree - `regulation/mifid/target-market`. The tree lives in one file,
`.wiki/tags.md`, one node per line, sorted by segment. A note carries its tags in one frontmatter
line, `tags: [a/b, c]`. scan_vault.py reads every other form a vault may already hold; nothing but
this tool writes, and it writes that one form.

  python3 tags.py --vault ~/vault init
  python3 tags.py --vault ~/vault add regulation/mifid --meaning "EU investor protection." --aka mifid2
  python3 tags.py --vault ~/vault set regulation/rules.md --add regulation/mifid --remove regulation
  python3 tags.py --vault ~/vault move regulation/mifid regulation/eu/mifid
  python3 tags.py --vault ~/vault drop regulation/old
  python3 tags.py --vault ~/vault check [--json]
  python3 tags.py --vault ~/vault pending [--scope reg] [--limit 25] [--json] [--retag]
  python3 tags.py --vault ~/vault batch-done reg

Exit codes: 0 done, 1 `check` found drift, 2 refused (the message names the next command),
3 the tree is at its cap.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl                       # POSIX file locking. Absent on Windows, handled below.
except ImportError:
    fcntl = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scan_vault  # noqa: E402

EXIT_DRIFT = 1
EXIT_REFUSED = 2
EXIT_FULL = 3

MAX_PER_NOTE = 5                    # past this a note is tagged with everything, so with nothing
MAX_DEPTH = 4                       # a deeper path is a folder tree wearing a tag's name
DEFAULT_NODES_MAX = 300             # wiki-config.json -> tag_nodes_max
DEFAULT_BRANCH_NOTES = 25           # wiki-config.json -> tag_branch_notes
NEARLY_FULL = 0.9
MERGE_CANDIDATES_SHOWN = 5
DEFAULT_PENDING_LIMIT = 25
SKELETON_H2_SHOWN = 8

CONFIG_PARTS = (".wiki", "wiki-config.json")
MANIFEST_PARTS = (".wiki", "manifest.json")
RETAG_RECEIPT_PARTS = (".wiki", ".tag-run.json")
ROUTING_FILES = {"see-also.md"}     # plus the index file, which `pending --index` names
WORKING_FOLDER_PREFIXES = ("_", ".")

INVENTORY_HEADER = (
    "# Tags\n"
    "\n"
    "The tag tree of this vault: one node per line, a full path, sorted by segment.\n"
    "Written only through `scripts/tags.py` (`add`, `move`, `drop`), never by hand.\n"
    "The rules are in `references/tagging.md`.\n"
    "\n"
)

# --- one writer at a time -----------------------------------------------------------------------
# Every command here is a read-modify-write of one file: read the tree, change one node, write it
# back. An agent that fires several `add` calls in one block runs them AT ONCE, so without an
# exclusive lock the last writer wins and the others' nodes are gone - while every one of them
# prints `listed`. Measured without the lock: 12 parallel adds, 12 reported success, 10 landed.

LOCK_NAME = ".tags.lock"
_has_warned_about_locking = False


def _locate_lock(vault: Path) -> Path:
    """The lock file, beside the inventory so the two are on one filesystem."""

    return Path(scan_vault.locate_tag_inventory(str(vault))).parent / LOCK_NAME


@contextmanager
def _claim_tag_lock(vault: Path):
    """Hold the inventory's exclusive lock for one read-modify-write cycle.

    The lock file is created once and **never deleted**. Deleting it on release is what makes a
    lock stop locking: a process still waiting on the old inode and one arriving afterwards open
    two different files and both believe they hold it. It is an empty file, so leaving it costs
    nothing, and `test_tags.py` 19 asserts it survives.

    The lock BLOCKS rather than timing out. The critical section is one small read and one write,
    so the wait is milliseconds; a caller that gave up would lose the node it was asked to write,
    which is the whole defect this exists to prevent.
    """

    global _has_warned_about_locking
    if fcntl is None:
        # Nothing to lock with. Say so once - a tool that silently drops the guarantee it
        # advertises is worse than one that cannot offer it.
        if not _has_warned_about_locking:
            _has_warned_about_locking = True
            print(f"warning: no file locking on {sys.platform} - run one tags.py at a time",
                  file=sys.stderr)
        yield
        return

    path = _locate_lock(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield
    finally:
        os.close(handle)                  # closing releases the lock; the file stays


class Refusal(ValueError):
    """The tool will not do this. The message names what to run instead; the code says why."""

    def __init__(self,
                 message: str,
                 exit_code: int = EXIT_REFUSED) -> None:
        super().__init__(message)
        self.exit_code = exit_code


# --- small pure helpers -------------------------------------------------------------------------

def _split_segments(tag: str) -> tuple[str, ...]:
    """The sort key of a node. By segment, never by byte: `-` sorts below `/`."""

    return tuple(tag.split(scan_vault.TAG_SEPARATOR))


def _find_parent(tag: str) -> str:
    """The node one level up, or "" for a top-level node."""

    head, _sep, _leaf = tag.rpartition(scan_vault.TAG_SEPARATOR)

    return head


def _list_ancestors(tag: str) -> list[str]:
    """Every node above this one, top first."""

    parts = _split_segments(tag)

    return [scan_vault.TAG_SEPARATOR.join(parts[:i]) for i in range(1, len(parts))]


def _is_under(tag: str, node: str) -> bool:
    """Whether a tag is the node itself or one of its descendants."""

    return tag == node or tag.startswith(node + scan_vault.TAG_SEPARATOR)


def _clean_tag(raw: str) -> str:
    """One tag as it is compared and written: no `#`, no quotes, casefolded."""

    tag = raw.strip().strip("'\"").strip().lstrip("#").casefold()
    if not scan_vault.is_tag(tag):
        raise Refusal(f"`{raw}` is not a tag. A tag is segments of letters, digits, `_` and `-` "
                      f"joined by `/`, no segment all digits: regulation/mifid/target-market")

    return tag


def _render_command(vault: Path, *words: str) -> str:
    """The exact command to run next, for a refusal or a check line to name."""

    return "python3 %s --vault %s %s" % (Path(__file__).resolve(), vault, " ".join(words))


def _read_config_number(vault: Path,
                        key: str,
                        default: int) -> int:
    try:
        value = json.loads(vault.joinpath(*CONFIG_PARTS).read_text(encoding="utf-8")).get(key)
    except (OSError, ValueError, AttributeError):
        return default

    return value if isinstance(value, int) and value > 0 else default


def _write_whole(path: Path, text: str) -> None:
    """Replace a file in one step, bytes as given, so a kill never leaves half a note."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tags-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(temp_name, path)
    except OSError:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
        raise


def _read_note(path: Path) -> str:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


# --- the inventory file -------------------------------------------------------------------------

def _locate_inventory(vault: Path) -> Path:
    return Path(scan_vault.locate_tag_inventory(str(vault)))


def _read_inventory_file(vault: Path) -> tuple[list[str], list[str]]:
    """Return (the lines that are not nodes, every node path as listed - duplicates included)."""

    path = _locate_inventory(vault)
    if not path.exists():
        return INVENTORY_HEADER.splitlines(), []
    other_lines, listed_paths = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = scan_vault.TAG_INVENTORY_LINE_RE.match(line.rstrip())
        if match:
            listed_paths.append(match.group("path").strip().casefold())
        else:
            other_lines.append(line)

    return other_lines, listed_paths


def _render_node(tag: str, node: dict) -> str:
    line = f"- `{tag}`"
    aka = f"(aka {', '.join(node['aka'])})" if node.get("aka") else ""
    described = " ".join(part for part in (node.get("meaning", ""), aka) if part)

    return f"{line} — {described}" if described else line


def _write_inventory(vault: Path, inventory: dict) -> None:
    """The whole tree, sorted by segment, under whatever non-node lines the file already had."""

    other_lines, _listed = _read_inventory_file(vault)
    while other_lines and not other_lines[-1].strip():
        other_lines.pop()
    node_lines = [_render_node(tag, inventory[tag]) for tag in sorted(inventory, key=_split_segments)]
    text = "\n".join(other_lines + [""] + node_lines) + "\n"
    _write_whole(_locate_inventory(vault), text)


def _find_carriers(tags_by_note: dict, node: str) -> list[str]:
    """The notes carrying a node or any of its descendants."""

    return sorted(rel for rel, tags in tags_by_note.items() if any(_is_under(t, node) for t in tags))


def _list_cheapest_merges(vault: Path, inventory: dict) -> list[str]:
    """Commands that free a slot at the least cost: the leaves fewest notes carry, into their parent."""

    tags_by_note, _bad = scan_vault.walk_tags(str(vault))
    parents = {_find_parent(tag) for tag in inventory}
    leaves = [tag for tag in inventory if tag not in parents and _find_parent(tag)]
    ranked = sorted(leaves, key=lambda tag: (len(_find_carriers(tags_by_note, tag)), _split_segments(tag)))

    return [_render_command(vault, "move", tag, _find_parent(tag)) for tag in ranked[:MERGE_CANDIDATES_SHOWN]]


# --- notes --------------------------------------------------------------------------------------

def _resolve_note(vault: Path, raw: str) -> tuple[Path, str]:
    """Return (the note's real path, its vault-relative path), or refuse. Only a note is writable."""

    candidate = Path(raw).expanduser()
    full = candidate if candidate.is_absolute() else vault / candidate
    try:
        resolved = full.resolve()
        rel = resolved.relative_to(vault.resolve())
    except (OSError, ValueError):
        raise Refusal(f"{raw} is not inside the vault {vault}")
    if any(part in scan_vault.SKIP_DIRS or part.startswith(".") for part in rel.parts):
        raise Refusal(f"{rel} is the vault's machinery, not a note")
    if resolved.suffix.lower() not in scan_vault.NOTE_EXT:
        raise Refusal(f"{rel} is not a note ({', '.join(sorted(scan_vault.NOTE_EXT))})")
    if not resolved.is_file():
        raise Refusal(f"{rel} does not exist")

    return resolved, rel.as_posix()


def _find_tags_span(lines: list[str], close: int) -> tuple[int, int]:
    """The half-open line range the `tags` key occupies inside the block, or (-1, -1)."""

    for i in range(1, close):
        line = lines[i]
        stripped = line.strip()
        is_key_line = (stripped and not line.startswith((" ", "\t", "-", "#")) and ":" in stripped)
        if not is_key_line or stripped.partition(":")[0].strip() != scan_vault.TAG_KEY:
            continue
        end = i + 1
        while end < close and lines[end].strip() and lines[end].startswith((" ", "\t", "-")):
            end += 1

        return i, end

    return -1, -1


def _find_block_close(lines: list[str]) -> int:
    for i in range(1, min(len(lines), scan_vault.FRONT_MATTER_MAX_LINES)):
        if lines[i].strip() in ("---", "..."):
            return i
    raise ValueError("the frontmatter block is opened with `---` and never closed")


def _rewrite_note_tags(vault: Path,
                       rel: str,
                       tags: list[str]) -> bool:
    """Write a note's tags. Returns whether the file changed - an identical result is not a write."""

    path = vault / rel
    before = _read_note(path)
    after = with_tags(before, tags)
    if after == before:
        return False
    _write_whole(path, after)

    return True


# --- the work list ------------------------------------------------------------------------------

def _load_manifest_notes(vault: Path, index_name: str) -> list[dict]:
    """The notes worth tagging, from the last scan: no routing files, no working folders."""

    manifest_path = vault.joinpath(*MANIFEST_PARTS)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise Refusal("no manifest to list notes from. Scan first:\n  python3 %s --root %s --out %s"
                      % (Path(__file__).resolve().parent / "scan_vault.py", vault, manifest_path))
    routing_files = ROUTING_FILES | {index_name.lower()}
    notes = []
    for record in manifest.get("files", []):
        rel = str(record.get("path", "")).replace(os.sep, "/")
        parts = rel.split("/")
        if record.get("status") == "REMOVED" or record.get("ext") not in scan_vault.NOTE_EXT:
            continue
        if parts[-1].lower() in routing_files:
            continue
        if any(part.startswith(WORKING_FOLDER_PREFIXES) for part in parts[:-1]):
            continue
        notes.append({**record, "path": rel, "folder": "/".join(parts[:-1]) or "."})

    return sorted(notes, key=lambda note: note["path"])


def _build_skeleton(record: dict, live_tags: list[str]) -> dict:
    """What the agent tags from: the note's outline, never its text."""

    return {
        "path": record["path"],
        "folder": record["folder"],
        "h1": record.get("h1", ""),
        "h2": (record.get("h2") or [])[:SKELETON_H2_SHOWN],
        "first_line": record.get("first_line", ""),
        "acronyms": sorted(record.get("acronyms") or {}),
        "tags": live_tags,
    }


def _open_retag_receipt(vault: Path, scope: str) -> dict:
    """The retag's record of finished folders. A plain tag run needs none: an untagged note IS its
    own record. A revisited note left as it was looks exactly like one not visited yet."""

    path = vault.joinpath(*RETAG_RECEIPT_PARTS)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        receipt = {"scope": scope,
                   "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "done": []}
        _write_whole(path, json.dumps(receipt, indent=2) + "\n")

    return receipt


# --- public: what serve.py shares with the command line -------------------------------------------

def normalize(tags: list[str]) -> list[str]:
    """A note's tag list as it is written: casefolded, no duplicate, no ancestor beside its
    descendant (a child implies every node above it), sorted by segment."""

    cleaned = []
    for raw in tags:
        tag = _clean_tag(raw)
        if tag not in cleaned:
            cleaned.append(tag)
    specific = [tag for tag in cleaned
                if not any(other != tag and _is_under(other, tag) for other in cleaned)]

    return sorted(specific, key=_split_segments)


def with_tags(text: str, tags: list[str]) -> str:
    """The note's text with exactly these tags, and every other byte as it was.

    Touches only the `tags` key. Creates a frontmatter block when the note has none; removes the
    key when the list is empty, and the block with it when `tags` was all it held. Raises
    ValueError on a block that is opened and never closed - guessing where it ends would rewrite
    the body.
    """

    newline = "\r\n" if "\r\n" in text else "\n"
    tag_line = f"{scan_vault.TAG_KEY}: [{', '.join(tags)}]{newline}"
    lines = text.splitlines(keepends=True)
    has_block = bool(lines) and lines[0].strip() == "---"

    if not has_block:
        return f"---{newline}{tag_line}---{newline}{newline}{text}" if tags else text

    close = _find_block_close(lines)
    start, end = _find_tags_span(lines, close)
    replacement = [tag_line] if tags else []
    if start >= 0:
        lines[start:end] = replacement
    else:
        lines[close:close] = replacement
    close = _find_block_close(lines)
    is_block_empty = not any(line.strip() for line in lines[1:close])
    if is_block_empty:
        body_start = close + 1
        if body_start < len(lines) and not lines[body_start].strip():
            body_start += 1
        lines = lines[body_start:]

    return "".join(lines)


def add_node(vault: Path,
             tag: str,
             meaning: str = "",
             aka: tuple[str, ...] = ()) -> bool:
    """List one node in the tree. Returns whether it was added - a node already listed is left
    exactly as it is. Refuses a node whose parent is not listed, and a tree at its cap.

    The whole cycle - read, check, write - is held under the inventory's exclusive lock, so two
    `add` calls running at once cannot read the same tree and overwrite each other's node."""

    tag = _clean_tag(tag)

    with _claim_tag_lock(vault):
        inventory = scan_vault.load_tag_inventory(str(vault))
        if tag in inventory:
            return False  # already listed — idempotent under concurrency
        parent = _find_parent(tag)
        if parent and parent not in inventory:
            raise Refusal(f"`{tag}` has no parent in the tree. List the parent first:\n  "
                          + _render_command(vault, "add", parent, "--meaning", '"<what it covers>"'))
        nodes_max = _read_config_number(vault, "tag_nodes_max", DEFAULT_NODES_MAX)
        if len(inventory) >= nodes_max:
            merges = "\n  ".join(_list_cheapest_merges(vault, inventory))
            raise Refusal(f"the tag tree is full ({len(inventory)} of {nodes_max} nodes). Merge a leaf "
                          f"into its parent first - the cheapest, fewest notes first:\n  {merges}",
                          EXIT_FULL)
        inventory[tag] = {"meaning": " ".join(meaning.split()),
                          "aka": [a.strip().casefold() for a in aka if a.strip()]}
        _write_inventory(vault, inventory)

    return True


def clear_inventory(vault: Path) -> None:
    """Leave the tag tree with no nodes, creating the file when the vault has none. Whatever
    lines the owner keeps above the nodes stay: only the nodes are the tool's."""

    with _claim_tag_lock(vault):
        _write_inventory(vault, {})


# --- public: the commands -----------------------------------------------------------------------

def run_init(vault: Path, _args: argparse.Namespace) -> int:
    path = _locate_inventory(vault)
    if path.exists():
        print(f"{path}: already there")
        return 0
    clear_inventory(vault)
    print(f"{path}: created, empty")

    return 0


def run_add(vault: Path, args: argparse.Namespace) -> int:
    aka = tuple((args.aka or "").split(","))
    was_added = add_node(vault, args.tag, args.meaning or "", aka)
    print(f"{_clean_tag(args.tag)}: {'listed' if was_added else 'already listed, left as it is'}")

    return 0


def run_set(vault: Path, args: argparse.Namespace) -> int:
    _resolved, rel = _resolve_note(vault, args.note)
    current, bad_tags = scan_vault.parse_tags(_read_note(vault / rel).splitlines())
    removed = {_clean_tag(raw) for raw in args.remove or []}
    tags = normalize([tag for tag in current if tag not in removed] + list(args.add or []))
    if len(tags) > scan_vault.MAX_TAGS:
        raise Refusal(f"{rel}: {len(tags)} tags, and nothing reads past {scan_vault.MAX_TAGS}. "
                      f"A note carries {MAX_PER_NOTE} at most - keep the most specific.")

    with _claim_tag_lock(vault):
        inventory = scan_vault.load_tag_inventory(str(vault))
        unlisted = [tag for tag in tags if tag not in inventory]
        if unlisted:
            needed = []
            for tag in unlisted:
                needed += [node for node in _list_ancestors(tag) + [tag]
                           if node not in inventory and node not in needed]
            commands = "\n  ".join(_render_command(vault, "add", node, "--meaning", '"<what it covers>"')
                                   for node in needed)
            raise Refusal(f"{rel}: not in the tag tree yet: {', '.join(unlisted)}. List them first, "
                          f"parents first, then run this again:\n  {commands}")

    has_changed = _rewrite_note_tags(vault, rel, tags)
    dropped = f" (dropped malformed: {', '.join(bad_tags)})" if bad_tags and has_changed else ""
    print(f"{rel}: {'tags [' + ', '.join(tags) + ']' if has_changed else 'unchanged'}{dropped}")

    return 0


def run_move(vault: Path, args: argparse.Namespace) -> int:
    old, new = _clean_tag(args.old), _clean_tag(args.new)

    with _claim_tag_lock(vault):
        inventory = scan_vault.load_tag_inventory(str(vault))
        if old not in inventory:
            raise Refusal(f"`{old}` is not in the tag tree")
        if new != old and _is_under(new, old):
            raise Refusal(f"`{new}` is under `{old}` - a node cannot move inside itself")
        if _find_parent(new) and _find_parent(new) not in inventory:
            raise Refusal(f"`{new}` has no parent in the tree. List it first:\n  "
                          + _render_command(vault, "add", _find_parent(new), "--meaning", '"<what it covers>"'))
        if new == old:
            print(f"{old}: unchanged")
            return 0

        # STEP 1: move the node and everything under it in the tree; landing on a node is a merge
        moved = {tag: new + tag[len(old):] for tag in inventory if _is_under(tag, old)}
        for source, target in moved.items():
            node = inventory.pop(source)
            kept = inventory.get(target)
            if kept is None:
                inventory[target] = node
            else:
                kept["meaning"] = kept["meaning"] or node["meaning"]
                kept["aka"] = kept["aka"] + [a for a in node["aka"] if a not in kept["aka"]]
        _write_inventory(vault, inventory)

    # STEP 2: rewrite every note that carries one of them, found live - the graph is as of the last scan
    tags_by_note, _bad = scan_vault.walk_tags(str(vault))
    rewritten = 0
    for rel, tags in sorted(tags_by_note.items()):
        if not any(tag in moved for tag in tags):
            continue
        if _rewrite_note_tags(vault, rel, normalize([moved.get(tag, tag) for tag in tags])):
            rewritten += 1
    print(f"{old} -> {new}: {len(moved)} node(s) moved, {rewritten} note(s) rewritten")

    return 0


def run_drop(vault: Path, args: argparse.Namespace) -> int:
    tag = _clean_tag(args.tag)

    with _claim_tag_lock(vault):
        inventory = scan_vault.load_tag_inventory(str(vault))
        if tag not in inventory:
            raise Refusal(f"`{tag}` is not in the tag tree")
        children = [node for node in inventory if _find_parent(node) == tag]
        if children:
            raise Refusal(f"`{tag}` has children ({', '.join(children[:3])}). Only an empty leaf is dropped.")
        tags_by_note, _bad = scan_vault.walk_tags(str(vault))
        carriers = _find_carriers(tags_by_note, tag)
        if carriers:
            raise Refusal(f"`{tag}` is carried by {len(carriers)} note(s) ({', '.join(carriers[:3])}). "
                          f"Merge it instead:\n  " + _render_command(vault, "move", tag, _find_parent(tag) or "<node>"))
        del inventory[tag]
        _write_inventory(vault, inventory)
    print(f"{tag}: dropped")

    return 0


def run_check(vault: Path, args: argparse.Namespace) -> int:
    """Do the notes and the tree agree? Reads both live, so it has no scan to be behind."""

    _other, listed_paths = _read_inventory_file(vault) if _locate_inventory(vault).exists() else ([], [])
    inventory = scan_vault.load_tag_inventory(str(vault))
    tags_by_note, bad_tags_by_note = scan_vault.walk_tags(str(vault))
    branch_notes = _read_config_number(vault, "tag_branch_notes", DEFAULT_BRANCH_NOTES)
    nodes_max = _read_config_number(vault, "tag_nodes_max", DEFAULT_NODES_MAX)
    failures, warnings = [], []

    # STEP 1: drift between what the notes carry and what the tree lists - these fail
    carried = sorted({tag for tags in tags_by_note.values() for tag in tags}, key=_split_segments)
    covered = set(carried) | {node for tag in carried for node in _list_ancestors(tag)}
    for tag in carried:
        if tag not in inventory:
            notes = [rel for rel, tags in tags_by_note.items() if tag in tags]
            failures.append({"kind": "unlisted", "tag": tag, "notes": sorted(notes),
                             "fix": _render_command(vault, "add", tag, "--meaning", '"<what it covers>"')})
    for tag in sorted(inventory, key=_split_segments):
        if tag not in covered:
            failures.append({"kind": "unused", "tag": tag, "notes": [],
                             "fix": _render_command(vault, "drop", tag)})
        if _find_parent(tag) and _find_parent(tag) not in inventory:
            failures.append({"kind": "orphan", "tag": tag, "notes": [],
                             "fix": _render_command(vault, "add", _find_parent(tag), "--meaning",
                                             '"<what it covers>"')})
        if not scan_vault.is_tag(tag):
            failures.append({"kind": "malformed", "tag": tag, "notes": [],
                             "fix": "rewrite the line in .wiki/tags.md: " + tag})
    for rel, bad_tags in sorted(bad_tags_by_note.items()):
        for tag in bad_tags:
            failures.append({"kind": "malformed", "tag": tag, "notes": [rel],
                             "fix": _render_command(vault, "set", rel, "--add", "<a well-formed tag>")})
    for tag in sorted({path for path in listed_paths if listed_paths.count(path) > 1}):
        failures.append({"kind": "duplicate", "tag": tag, "notes": [],
                         "fix": "delete the second line for it in .wiki/tags.md"})

    # STEP 2: a tree drifting out of shape - these warn, and never fail
    for rel, tags in sorted(tags_by_note.items()):
        beside = [tag for tag in tags if any(other != tag and _is_under(other, tag) for other in tags)]
        if beside:
            warnings.append(f"{rel} carries {beside[0]} beside its descendant - the ancestor is implied")
        if len(tags) > MAX_PER_NOTE:
            warnings.append(f"{rel} carries {len(tags)} tags - {MAX_PER_NOTE} at most")
    leaf_parents = {}
    for tag in sorted(inventory, key=_split_segments):
        direct = sum(1 for tags in tags_by_note.values() if tag in tags)
        if direct > branch_notes:
            warnings.append(f"{tag} is carried directly by {direct} notes - split it into children")
        if len(_split_segments(tag)) > MAX_DEPTH:
            warnings.append(f"{tag} is {len(_split_segments(tag))} levels deep - {MAX_DEPTH} at most")
        if not inventory[tag]["meaning"]:
            warnings.append(f"{tag} has no meaning line yet")
        leaf_parents.setdefault(_split_segments(tag)[-1], []).append(tag)
    for leaf, nodes in sorted(leaf_parents.items()):
        if len(nodes) > 1:
            warnings.append(f"`{leaf}` sits under two parents: {', '.join(nodes)} - one subject, one node")
    if len(inventory) >= NEARLY_FULL * nodes_max:
        warnings.append(f"the tree holds {len(inventory)} of {nodes_max} nodes")

    # STEP 3: report - every failure names the command that clears it
    tagged = sum(1 for tags in tags_by_note.values() if tags)
    is_consistent = not failures
    if args.json:
        print(json.dumps({"ok": is_consistent, "nodes": len(inventory), "tagged_notes": tagged,
                          "notes": len(tags_by_note), "failures": failures, "warnings": warnings},
                         indent=2, ensure_ascii=False))
    else:
        for failure in failures:
            where = f"  ({', '.join(failure['notes'][:3])})" if failure["notes"] else ""
            print(f"FAIL  {failure['kind']:<10} {failure['tag']}{where}\n      -> {failure['fix']}")
        for warning in warnings:
            print(f"warn  {warning}")
        state = "OK" if is_consistent else "DRIFT"
        print(f"tags check {state}: {len(inventory)} nodes, {tagged} of {len(tags_by_note)} notes "
              f"tagged, {len(failures)} failure(s), {len(warnings)} warning(s)")

    return 0 if is_consistent else EXIT_DRIFT


def run_pending(vault: Path, args: argparse.Namespace) -> int:
    notes = _load_manifest_notes(vault, args.index)
    scope = (args.scope or "").strip("/")
    if scope:
        notes = [note for note in notes if _is_under(note["path"], scope) or note["folder"] == scope]

    done_folders = set(_open_retag_receipt(vault, scope)["done"]) if args.retag else set()
    pending = []
    for note in notes:
        live_tags, _bad = scan_vault.parse_tags(scan_vault.read_head_lines(str(vault / note["path"])))
        is_pending = note["folder"] not in done_folders if args.retag else not live_tags
        if is_pending:
            pending.append(_build_skeleton(note, live_tags))
    if args.retag and not pending:
        vault.joinpath(*RETAG_RECEIPT_PARTS).unlink(missing_ok=True)

    folders = {}
    for note in pending:
        folders[note["folder"]] = folders.get(note["folder"], 0) + 1
    shown = pending[:max(args.limit, 0)]
    if args.json:
        print(json.dumps({"total": len(pending), "folders": folders, "notes": shown},
                         indent=2, ensure_ascii=False))
        return 0
    print(f"{len(pending)} note(s) pending in {len(folders)} folder(s)")
    for folder, count in folders.items():
        print(f"  {count:>4}  {folder}")
    for note in shown:
        print(f"- {note['path']}  |  {note['h1']}  |  {'; '.join(note['h2'])}")

    return 0


def run_batch_done(vault: Path, args: argparse.Namespace) -> int:
    path = vault.joinpath(*RETAG_RECEIPT_PARTS)
    if not path.exists():
        raise Refusal("no retag is under way. Start one:\n  " + _render_command(vault, "pending", "--retag"))
    receipt = json.loads(path.read_text(encoding="utf-8"))
    folder = args.folder.strip("/") or "."
    if folder not in receipt["done"]:
        receipt["done"].append(folder)
        _write_whole(path, json.dumps(receipt, indent=2) + "\n")
    print(f"{folder}: done ({len(receipt['done'])} folder(s) finished in this retag)")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a note's tags and keep the vault's tag tree.")
    parser.add_argument("--vault", default=".", help="vault root (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create the empty tag tree if the vault has none").set_defaults(run=run_init)

    add = sub.add_parser("add", help="list one node in the tree")
    add.add_argument("tag")
    add.add_argument("--meaning", help="one line: what the node covers")
    add.add_argument("--aka", help="comma-separated other names for it")
    add.set_defaults(run=run_add)

    set_ = sub.add_parser("set", help="add or remove tags on one note")
    set_.add_argument("note")
    set_.add_argument("--add", action="append")
    set_.add_argument("--remove", action="append")
    set_.set_defaults(run=run_set)

    move = sub.add_parser("move", help="rename, re-parent or merge a node, and rewrite its notes")
    move.add_argument("old")
    move.add_argument("new")
    move.set_defaults(run=run_move)

    drop = sub.add_parser("drop", help="remove an empty leaf from the tree")
    drop.add_argument("tag")
    drop.set_defaults(run=run_drop)

    check = sub.add_parser("check", help="exit 1 when the notes and the tree disagree")
    check.add_argument("--json", action="store_true")
    check.set_defaults(run=run_check)

    pending = sub.add_parser("pending", help="the notes still to tag, as outlines")
    pending.add_argument("--scope", help="a subtree of the vault")
    pending.add_argument("--limit", type=int, default=DEFAULT_PENDING_LIMIT)
    pending.add_argument("--index", default="index.md", help="the vault's index file name")
    pending.add_argument("--json", action="store_true")
    pending.add_argument("--retag", action="store_true", help="revisit tagged notes too")
    pending.set_defaults(run=run_pending)

    batch_done = sub.add_parser("batch-done", help="mark one folder finished in a retag")
    batch_done.add_argument("folder")
    batch_done.set_defaults(run=run_batch_done)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"--vault is not a directory: {vault}", file=sys.stderr)
        return EXIT_REFUSED
    try:
        return args.run(vault, args)
    except Refusal as refusal:
        print(f"refused: {refusal}", file=sys.stderr)
        return refusal.exit_code
    except ValueError as error:
        print(f"refused: {error}", file=sys.stderr)
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
