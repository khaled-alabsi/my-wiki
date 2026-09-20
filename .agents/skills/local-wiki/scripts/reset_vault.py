#!/usr/bin/env python3
"""Reset the vault to a fresh state.

Two scopes:

  --scope sample   remove only notes carrying `status: sample` in frontmatter,
                   then rebuild the derived state. The default.
  --scope all      remove every note in the content folders, then rebuild the
                   derived state. The vault comes back as it was at `init`.

Notes are never deleted: they are moved to `.wiki/.trash/<timestamp>/`, keeping
their folder paths, exactly as `refactor` does. Derived state -- the graph
database, the manifest and the .rag index -- IS deleted, because all three are
rebuildable from the markdown and rebuilding them is the point.

Dry run by default. Nothing moves without --yes.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tags as tag_tool  # noqa: E402

CONTENT_FOLDERS = [
    "processes", "sub-processes", "use-cases", "regulatory", "business-rules",
    "domain-model", "products", "systems", "technical",
]

# Rebuildable from the markdown. Removed, not trashed.
DERIVED = [
    ".wiki/graph.sqlite",
    ".wiki/manifest.json",
    ".wiki/.second-pass",
    ".wiki/.tag-run.json",          # a retag's record of folders done, about notes that are gone
    ".rag/db/chunks.lance",
    ".rag/state/manifest.sqlite",
]

# Tracking state that a fresh vault starts empty. Rewritten, not removed.
PRISTINE = {
    ".wiki/contributors.json": '{"version": 1, "contributors": {}}\n',
}

PLACEHOLDER = {
    ".wiki/todos_validations.md": "_No items yet._",
    ".wiki/wiki_gaps.md": "_No items yet._",
    ".wiki/agent-memory/observations.md": "_None yet._",
    ".wiki/agent-memory/proposals.md": "_None yet._",
}


# Frontmatter lives at the top of the file, so only the head is read. Reading whole
# notes to test one line is what makes this scale with vault size instead of with
# frontmatter size -- at 2,000 notes that is the difference between a scan and a stall.
FRONTMATTER_BYTES = 1024


def has_sample_status(path: Path) -> bool:
    """True when the note's YAML frontmatter carries `status: sample`.

    Reads at most FRONTMATTER_BYTES. A frontmatter block longer than that is not
    one -- it is a note whose author forgot the closing fence, and it is treated
    as unmarked rather than scanned further.
    """
    try:
        with path.open("r", encoding="utf-8") as handle:
            head = handle.read(FRONTMATTER_BYTES)
    except (OSError, UnicodeDecodeError):
        return False
    if not head.startswith("---\n"):
        return False
    end = head.find("\n---", 4)
    if end == -1:
        return False
    for line in head[4:end].splitlines():
        if line.strip().replace(" ", "") == "status:sample":
            return True
    return False


def collect_notes(vault: Path, scope: str) -> list[Path]:
    notes: list[Path] = []
    for folder in CONTENT_FOLDERS:
        root = vault / folder
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.md")):
            if scope == "all" or has_sample_status(path):
                notes.append(path)
    return notes


def truncate_after_marker(path: Path, marker: str, replacement: str) -> bool:
    """Replace everything after `marker` with `replacement`. Leaves the header."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    idx = text.find(marker)
    if idx == -1:
        return False
    keep = text[: idx + len(marker)]
    path.write_text(keep.rstrip("\n") + "\n\n" + replacement + "\n", encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", required=True, help="vault root")
    ap.add_argument("--scope", choices=("sample", "all"), default="sample")
    ap.add_argument("--yes", action="store_true", help="actually do it")
    ap.add_argument("--keep-index", action="store_true",
                    help="leave index.md alone instead of emptying its folder sections")
    args = ap.parse_args()

    vault = Path(args.vault).resolve()
    if not (vault / ".wiki").is_dir():
        print(f"not a vault (no .wiki/): {vault}", file=sys.stderr)
        return 2

    notes = collect_notes(vault, args.scope)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    trash = vault / ".wiki" / ".trash" / stamp

    verb = "would move" if not args.yes else "moving"
    print(f"scope: {args.scope}")
    print(f"{verb} {len(notes)} note(s) to .wiki/.trash/{stamp}/")
    for note in notes:
        print(f"  {note.relative_to(vault)}")

    print(f"\n{'would delete' if not args.yes else 'deleting'} derived state:")
    for rel in DERIVED:
        target = vault / rel
        print(f"  {rel}{'' if target.exists() else '   (absent)'}")

    print(f"\n{'would reset' if not args.yes else 'resetting'} tracking state:")
    for rel in list(PRISTINE) + list(PLACEHOLDER):
        print(f"  {rel}")

    if not args.yes:
        print("\nDry run. Re-run with --yes to apply.")
        return 0

    for note in notes:
        dest = trash / note.relative_to(vault)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(note), str(dest))

    # drop folders emptied by the move, but keep the accepted structure itself
    for folder in CONTENT_FOLDERS:
        root = vault / folder
        if not root.is_dir():
            continue
        for sub in sorted(root.rglob("*"), reverse=True):
            if sub.is_dir() and not any(sub.iterdir()):
                sub.rmdir()

    for rel in DERIVED:
        target = vault / rel
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()

    for rel, content in PRISTINE.items():
        (vault / rel).write_text(content, encoding="utf-8")

    for rel, placeholder in PLACEHOLDER.items():
        path = vault / rel
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        header = []
        for line in lines:
            header.append(line)
            if line.strip().endswith("-->"):
                break
        path.write_text("\n".join(header).rstrip("\n") + "\n\n" + placeholder + "\n",
                        encoding="utf-8")

    # The tag tree lists subjects that notes carry. With every note gone it lists none. After a
    # sample reset real notes remain, so which nodes are now unused is for `tags.py check` to say
    # and for whoever reads it to drop - a reset does not decide what the vault is about.
    inventory = vault / ".wiki" / "tags.md"
    if args.scope == "all" and inventory.exists():
        tag_tool.clear_inventory(vault)

    config_path = vault / ".wiki" / "wiki-config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config.pop("intake_wave", None)  # retired: intake files one unit at a time
        config["last_reorganized_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    print(f"\nDone. {len(notes)} note(s) in .wiki/.trash/{stamp}/")
    print("Next, from the vault root:")
    print("  python3 .agents/skills/local-wiki/scripts/scan_vault.py "
          f"--root {vault} --out .wiki/manifest.json")
    print(f"  python3 .agents/skills/local-wiki/scripts/graph.py scan --vault {vault}")
    print("  .rag/bin/rag update --quiet")
    if inventory.exists():
        print(f"  python3 .agents/skills/local-wiki/scripts/tags.py --vault {vault} check"
              "   # drop the nodes it lists as unused")
    if not args.keep_index:
        print("  then ask the local-wiki skill to refresh index.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
