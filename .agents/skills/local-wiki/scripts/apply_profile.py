#!/usr/bin/env python3
"""Splice a knowledge profile's overlay into a generated local-wiki artifact.

Stdlib only.

    apply_profile.py --profile <file> --artifact <dir> [--vault <dir>]   apply
    apply_profile.py --artifact <dir> --remove                           back to base
    apply_profile.py --artifact <dir> --check                            what is applied

WHY A TOOL AND NOT PROSE: the overlay is applied at `init`, re-applied every time the artifact is
regenerated, swapped by `reshape`, and removed when a profile is dropped. An agent editing markdown
by hand through four different code paths will drift on the second one. This is a pure function of
(template, profile), so it is written once and run.

THE CONTRACT, in three parts:

  hooks     The TEMPLATE declares them - `<!-- profile-hook: update-classify -->` sitting at a
            decision point. Unfilled, a hook is an HTML comment and renders as nothing, which is
            what makes "no profile selected" byte-identical to the base template rather than
            merely similar to it.

  fragments The PROFILE fills them, under `### hook: <id>` in its `## Overlay` section. A profile
            fills only the hooks it changes; the rest stay bare.

  wrappers  Applied content is fenced by `<!-- profile:<name> start -->` / `<!-- ... end -->`, so
            re-applying REPLACES rather than appends, and `--remove` restores the base file byte
            for byte. Without the fence, the second `init`-then-regenerate cycle silently doubles
            every fragment.

A fragment naming a hook the artifact does not have is a hard error. A profile that only half
applies is worse than one that fails: the agent then follows a doctrine for placement and the base
rules for splitting, and nothing in the output says so.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# The hook contract. A profile may fill any subset; it may not invent new ones, because a hook that
# no template file declares is a fragment that would silently never be applied.
HOOKS = {
    "constitution": "SKILL.md",
    "placement-classify": "references/placement-rules.md",
    "placement-folder": "references/placement-rules.md",
    "split-decompose": "references/placement-rules.md",
    "update-classify": "references/modes/update.md",
    "intake-decompose": "references/modes/intake.md",
    "refactor-soundness": "references/modes/refactor.md",
    "audit-checks": "references/modes/audit.md",
    "note-shape": "references/note-shaping.md",
    "relation-types": "references/linking.md",
    "ask-routing": "references/modes/ask.md",
}

VAULT_PROFILE_NAME = "knowledge-profile.md"
HOOK_RE = re.compile(r"^<!-- profile-hook: (?P<id>[a-z][a-z0-9-]*) -->[ \t]*$", re.M)
FRAGMENT_RE = re.compile(r"^### hook: (?P<id>[a-z][a-z0-9-]*)[ \t]*$", re.M)


def wrapper(name: str) -> tuple[str, str]:
    return f"<!-- profile:{name} start -->", f"<!-- profile:{name} end -->"


def applied_re(name: str = r"[^\s>]+") -> re.Pattern:
    """Matches an applied block including the newline that precedes it."""
    return re.compile(
        rf"\n<!-- profile:(?P<name>{name}) start -->\n.*?\n<!-- profile:(?P=name) end -->",
        re.S,
    )


# --- reading a profile -------------------------------------------------------------------------

def split_sections(text: str, level: str = "## ") -> dict[str, str]:
    """Top-level sections of a markdown file, by heading text.

    Fenced code blocks are skipped. A profile's overlay fragments quote markdown at the reader -
    `## Related` inside a ```markdown fence is the commonest - and treating that as a section
    heading truncates the overlay silently, dropping every fragment after it.
    """
    out: dict[str, str] = {}
    current, buf, fence = None, [], None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is None and (stripped.startswith("```") or stripped.startswith("~~~")):
            fence = stripped[:3]
        elif fence is not None and stripped.startswith(fence):
            fence = None
        elif fence is None and line.startswith(level) and not line.startswith(level + "#"):
            if current is not None:
                out[current] = "\n".join(buf).strip("\n")
            current, buf = line[len(level):].strip(), []
            continue
        if current is not None:
            buf.append(line)
    if current is not None:
        out[current] = "\n".join(buf).strip("\n")
    return out


def read_profile(path: Path) -> dict:
    """Parse a profile into its name, doctrine, and hook fragments."""
    text = path.read_text(encoding="utf-8")
    name = path.stem
    sections = split_sections(text)

    missing = [s for s in ("Use when", "Doctrine", "Overlay") if s not in sections]
    if missing:
        raise ValueError(f"{path.name} is missing required section(s): {', '.join(missing)}")

    overlay = sections["Overlay"]
    fragments: dict[str, str] = {}
    marks = list(FRAGMENT_RE.finditer(overlay))
    for i, match in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(overlay)
        body = overlay[match.end():end].strip("\n")
        if body:
            fragments[match.group("id")] = body

    unknown = sorted(set(fragments) - set(HOOKS))
    if unknown:
        raise ValueError(
            f"{path.name} fills hook(s) that do not exist: {', '.join(unknown)}. "
            f"Known hooks: {', '.join(sorted(HOOKS))}"
        )

    # The doctrine is what the vault gets; keep its own heading so the copy reads as a document.
    doctrine = f"# {name.replace('-', ' ').title()} — knowledge profile\n\n"
    doctrine += ("<!-- Copied into this vault by `wiki init` or `reshape`. It is THIS VAULT'S copy:\n"
                 "     edit it here and the edit stands, because a doctrine its owner adjusted is\n"
                 "     that vault's doctrine now. Read before placement decisions, once per\n"
                 "     session. -->\n\n")
    # A leading HTML comment in `## Doctrine` is a note to whoever writes profiles - budget,
    # what belongs there - and it is not for the vault that receives the copy.
    body = re.sub(r"\A<!--.*?-->\s*", "", sections["Doctrine"], flags=re.S)
    doctrine += "## Use when\n\n" + sections["Use when"] + "\n\n" + body + "\n"
    if "Structure implications" in sections:
        doctrine += "\n## Structure implications\n\n" + sections["Structure implications"] + "\n"
    if "Relation types" in sections:
        doctrine += "\n## Relation types\n\n" + sections["Relation types"] + "\n"

    return {"name": name, "fragments": fragments, "doctrine": doctrine,
            "use_when": sections["Use when"].strip()}


# --- applying ----------------------------------------------------------------------------------

def strip_applied(text: str, name: str | None = None) -> str:
    pattern = applied_re(re.escape(name) if name else r"[^\s>]+")
    return pattern.sub("", text)


def replace_at_hook(text: str, marker: str, fragment: str, name: str) -> str:
    """Put `fragment` under `marker`, replacing whatever this hook already carried."""
    index = text.index(marker) + len(marker)
    head, tail = text[:index], text[index:]
    existing = applied_re().match(tail)
    if existing:
        tail = tail[existing.end():]
    start, end = wrapper(name)
    return f"{head}\n{start}\n{fragment}\n{end}{tail}"


def apply(artifact: Path, profile: dict, vault: Path | None) -> dict:
    touched: list[str] = []
    for hook_id, fragment in sorted(profile["fragments"].items()):
        rel = HOOKS[hook_id]
        target = artifact / rel
        if not target.exists():
            raise FileNotFoundError(f"hook `{hook_id}` targets {rel}, which is not in {artifact}")
        text = target.read_text(encoding="utf-8")
        marker = f"<!-- profile-hook: {hook_id} -->"
        if marker not in text:
            raise ValueError(
                f"{rel} does not declare hook `{hook_id}`. The template must carry "
                f"`{marker}` at the decision point this fragment belongs to."
            )
        # Replace only THIS hook's previous block, never every block in the file: three hooks
        # live in placement-rules.md, and stripping the file wholesale would delete the two
        # fragments this same run just wrote, leaving only the last one applied.
        text = replace_at_hook(text, marker, fragment, profile["name"])
        target.write_text(text, encoding="utf-8")
        if rel not in touched:
            touched.append(rel)

    written = None
    if vault is not None:
        wiki = vault / ".wiki"
        wiki.mkdir(parents=True, exist_ok=True)
        written = wiki / VAULT_PROFILE_NAME
        written.write_text(profile["doctrine"], encoding="utf-8")

    return {"profile": profile["name"], "hooks": sorted(profile["fragments"]),
            "files": touched, "doctrine": str(written) if written else None}


def remove(artifact: Path) -> dict:
    touched, name = [], None
    for rel in sorted(set(HOOKS.values())):
        target = artifact / rel
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8")
        found = applied_re().search(text)
        if not found:
            continue
        name = name or found.group("name")
        target.write_text(strip_applied(text), encoding="utf-8")
        touched.append(rel)
    return {"profile": name, "files": touched}


def check(artifact: Path) -> dict:
    found: dict[str, list[str]] = {}
    unfilled: list[str] = []
    for hook_id, rel in sorted(HOOKS.items()):
        target = artifact / rel
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8")
        marker = f"<!-- profile-hook: {hook_id} -->"
        if marker not in text:
            continue
        after = text.split(marker, 1)[1].lstrip("\n")
        match = re.match(r"<!-- profile:(?P<name>[^\s>]+) start -->", after)
        if match:
            found.setdefault(match.group("name"), []).append(hook_id)
        else:
            unfilled.append(hook_id)
    return {"applied": found, "unfilled": unfilled}


# --- cli ---------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply a knowledge profile's overlay to a generated local-wiki artifact.")
    parser.add_argument("--artifact", required=True,
                        help="the local-wiki directory (…/.agents/skills/local-wiki)")
    parser.add_argument("--profile", help="path to references/knowledge-profiles/<name>.md")
    parser.add_argument("--vault", help="vault root — writes .wiki/knowledge-profile.md")
    parser.add_argument("--remove", action="store_true", help="strip the overlay, restore base")
    parser.add_argument("--check", action="store_true", help="report what is applied")
    args = parser.parse_args(argv)

    artifact = Path(args.artifact).resolve()
    if not artifact.is_dir():
        print(f"error: {artifact} is not a directory", file=sys.stderr)
        return 2

    try:
        if args.check:
            state = check(artifact)
            if not state["applied"]:
                print(f"no profile applied ({len(state['unfilled'])} hook(s) available)")
                return 1
            for name, hooks in state["applied"].items():
                print(f"{name}: {len(hooks)} hook(s) — {', '.join(hooks)}")
            if state["unfilled"]:
                print(f"unfilled: {', '.join(state['unfilled'])}")
            return 0

        if args.remove:
            result = remove(artifact)
            if not result["files"]:
                print("no profile was applied; nothing to remove")
                return 1
            print(f"removed {result['profile']} from {len(result['files'])} file(s): "
                  f"{', '.join(result['files'])}")
            return 0

        if not args.profile:
            print("error: --profile is required unless --remove or --check", file=sys.stderr)
            return 2
        profile = read_profile(Path(args.profile).resolve())
        result = apply(artifact, profile, Path(args.vault).resolve() if args.vault else None)
        print(f"applied {result['profile']}: {len(result['hooks'])} hook(s) into "
              f"{len(result['files'])} file(s)")
        for rel in result["files"]:
            print(f"  {rel}")
        if result["doctrine"]:
            print(f"  doctrine -> {result['doctrine']}")
        return 0
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
