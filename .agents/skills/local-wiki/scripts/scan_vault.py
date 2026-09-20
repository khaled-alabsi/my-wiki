#!/usr/bin/env python3
"""Scan a notes vault and emit a manifest the wiki skill uses to build or refresh index.md.

Stdlib only. One record per file: relative path, size, line count, mtime, H1, H2 headings,
heading slugs, outbound links, frontmatter keys, tags, the first non-frontmatter line, and glossary
candidates (acronyms used and term definitions stated). With --previous, each record is also
marked NEW, CHANGED, UNCHANGED or REMOVED so a refresh re-describes only what moved.

Vault-level, the manifest also carries `graph` (adjacency) and `backlinks` (its inverse), built
from the links found in the same pass. Link extraction lives here rather than in graph.py on
purpose: this walk already opens and reads every file, so a second walk would buy nothing. graph.py
consumes this manifest.

Each link carries a `rel_type` - what the relation IS, not just that it exists. `## Related` lines
may declare one with Dataview syntax (`- requires :: [sca.md](...) - why`); everything else is
`relates-to`. Notes may declare `valid_from` / `valid_until` in their frontmatter, so a fact that
was true in 2024 and superseded in 2026 stays queryable as history instead of being overwritten.

  python3 scan_vault.py --root ~/vault --out .wiki/manifest.json
  python3 scan_vault.py --root ~/vault --out .wiki/manifest.json \\
      --previous .wiki/manifest.json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

SKIP_DIRS = {
    # The vault's own machinery is never vault content. `.agents/` holds the generated local skill -
    # around twenty markdown reference files that, scanned as notes, pollute the glossary, fill the
    # index with routing rules about the skill itself, and appear as orphans in the graph (observed:
    # 22 bogus orphans in a real vault). `.wiki/` is config, personal memory and the vault's
    # trash (`.wiki/.trash/`) - equally not notes, and a trashed note must never come back
    # as an index entry or a search hit.
    # `.agents` is the standard location for a repo-local skill; `.agent` is kept because
    # vaults created before the rename still have one, and their skill files are no more
    # vault content than the new ones are.
    # `.input/` is the STAGING folder: material the user dropped for filing and that this skill
    # has not processed yet. Scanning it puts unfiled scraps in the manifest as though they were
    # notes - they land in the glossary, count toward the vault's size, show up as orphans in the
    # graph, and get counted by every check that asks "how big is this vault". Observed: a vault
    # with two scaffolding files and nine staged drafts reported eleven notes.
    ".git", ".agents", ".agent", ".wiki", ".input", ".obsidian", ".trash", ".rag",
    "node_modules", "vendor", "target", "dist", "build", "site", ".docusaurus",
    ".venv", "venv", "__pycache__", ".idea", ".vscode", ".next", ".cache",
}
TEXT_EXT = {".md", ".markdown", ".mdx", ".txt", ".org", ".rst"}
OTHER_EXT = {".canvas", ".pdf", ".csv", ".json", ".yml", ".yaml"}
MAX_HEADINGS = 40
MAX_READ_BYTES = 512 * 1024

# --- Glossary candidates ---------------------------------------------------
# The agent decides what actually earns a glossary entry (references/glossary.md);
# this only collects the raw evidence cheaply, in the pass that already reads each file.

MAX_ACRONYMS = 30
ACRONYM_RE = re.compile(r"\b[A-Z][A-Za-z0-9]{1,7}\b")
# Only tokens with at least two capitals look like domain acronyms (PIP, TaMrA, WpHG),
# which keeps ordinary sentence-initial words out.
TWO_CAPS_RE = re.compile(r"[A-Z].*[A-Z]")
CODE_SPAN_RE = re.compile(r"`[^`]*`")
LINK_TARGET_RE = re.compile(r"\]\([^)]*\)|https?://\S+")

# "Long Form (ACR)" / "ACR (Long Form)" / "**ACR** - meaning" / "ACR: meaning" / "ACR = meaning"
DEFINITION_RES = (
    re.compile(r"(?P<long>[A-Za-zÀ-ÿ][\w\-/ ]{3,60}?)\s*\((?P<term>[A-Z][A-Za-z0-9]{1,7})\)"),
    re.compile(r"\b(?P<term>[A-Z][A-Za-z0-9]{1,7})\s*\((?P<long>[A-Za-zÀ-ÿ][\w\-/ ]{3,60}?)\)"),
    re.compile(r"^\**(?P<term>[A-Z][A-Za-z0-9À-ÿ]{1,20})\**\s*[-–—=:]\s+(?P<long>\S.{3,80})$"),
)
# Universal vocabulary: never a business glossary term. Mirrors references/glossary.md.
STOPLIST = {
    "API", "HTTP", "HTTPS", "JSON", "XML", "YAML", "SQL", "URL", "URI", "PDF", "CSV", "HTML",
    "CSS", "JS", "TS", "UI", "UX", "CLI", "IDE", "OS", "RAM", "CPU", "GPU", "CI", "CD", "PR",
    "MR", "AI", "ML", "LLM", "RAG", "SDK", "NPM", "GIT", "SSH", "TLS", "SSL", "DNS", "IP", "VM",
    "K8S", "REST", "CRUD", "MVC", "ORM", "JWT", "OAuth", "TODO", "FIXME", "NOTE", "OK", "ID",
    "UUID", "ISO", "UTC", "AM", "PM", "README", "MIT", "GNU", "EU", "US", "UK",
    # Placeholders. They are the most common two-capital tokens in a half-written note and none of
    # them is anybody's business vocabulary.
    "TBD", "TBC", "WIP", "FAQ", "AKA", "ETA", "NA", "IMO", "FYI", "ASAP",
}
# A plural is the same word. The stoplist is exact-match, so `APIs`, `URLs` and `ID's` used to walk
# straight past it and land in the glossary as though they were domain terms.
PLURAL_RE = re.compile(r"(?:'s|s)$")


# --- Links ------------------------------------------------------------------------------------
# Only edges between notes. A URL, an image, or a mailto is not a relation, and a link inside a
# code fence is a code sample - the fence-tracking loop in describe() is what excludes those, so
# these patterns never see them.

# Not preceded by "!" (which would make it an image). Captures text, target, optional #anchor.
MD_LINK_RE = re.compile(r"(?<!!)\[(?P<text>[^\]\n]*)\]\((?P<target>[^)\s]+?)(?:#(?P<anchor>[^)\s]*))?\)")
EXTERNAL_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.I)
NOTE_EXT = {".md", ".markdown", ".mdx"}
MAX_LINKS = 200

# --- Relation types ---------------------------------------------------------------------------
# A relation carries a TYPE as well as a target: `- requires :: [sca.md](../payments/sca.md) - why`.
# The `::` form is Dataview syntax, which Obsidian renders natively and plain markdown ignores, so
# a typed line stays readable everywhere.
#
# The vocabulary is CLOSED on purpose. An open one is unqueryable noise: fifty one-off verbs mean
# no query can ask "what does this regulate" and get an answer. A vault that genuinely needs more
# adds them to `relation_types` in .wiki/wiki-config.json, which is a deliberate act by its owner.
#
# Only `## Related` sections and see-also.md carry types. An inline mention in prose is a mention,
# not a claim about how two things relate, and pretending otherwise fills the graph with edges
# nobody meant to assert.
DEFAULT_RELATION = "relates-to"
RELATION_TYPES = frozenset({
    DEFAULT_RELATION, "part-of", "requires", "regulates", "implements",
    "supersedes", "superseded-by", "contradicts", "example-of", "defined-in",
})
REL_TYPE_RE = re.compile(r"^[-*+]?\s*(?P<type>[a-z][a-z0-9-]{1,23})\s*::\s*")

# Frontmatter values worth keeping: a note can be valid only for a period, and knowledge that was
# right in 2024 and superseded in 2026 is not wrong - it is historical. Tags are kept too (below).
# Everything else in the frontmatter is recorded by key only, as before.
TEMPORAL_KEYS = ("valid_from", "valid_until")
FRONT_MATTER_MAX_LINES = 200

# --- Tags -------------------------------------------------------------------------------------
# A tag is a FULL PATH in the vault's tag tree, segments joined by `/` (Obsidian's nested form):
# `regulation/mifid/target-market`. A note tagged with a child is under every ancestor, so the
# ancestors are never written beside it. references/tagging.md owns the rules.
#
# This module only READS, and it reads every form a vault may already hold - an inline list, a
# block list, a comma scalar, a leading `#`, quotes - because `adopt` may not change a note. The
# one WRITER is tags.py, and it writes one form.
#
# Keeping tag values does not make the manifest a copy of the vault: a tag is a closed,
# inventory-bounded classification, capped per note and in length - routing metadata of the same
# kind as `valid_from`, never prose.
TAG_KEY = "tags"
TAG_SEPARATOR = "/"
TAG_SEGMENT_RE = re.compile(r"^[\w-]+$", re.UNICODE)
MAX_TAGS = 12
MAX_TAG_LEN = 80
TAG_INVENTORY_PARTS = (".wiki", "tags.md")
# One node per line: - `path/of/node` — meaning. (aka alias, alias)
TAG_INVENTORY_LINE_RE = re.compile(r"^- `(?P<path>[^`]+)`(?:\s+[—–-]\s+(?P<rest>.*))?\s*$")
TAG_AKA_RE = re.compile(r"\s*\(aka (?P<aka>[^)]*)\)\s*$")


def load_relation_types(root):
    """The closed vocabulary, plus whatever this vault added to its own config."""
    path = os.path.join(root, ".wiki", "wiki-config.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            extra = json.load(fh).get("relation_types") or []
    except (OSError, ValueError, AttributeError):
        return set(RELATION_TYPES)
    if not isinstance(extra, list):
        return set(RELATION_TYPES)
    return set(RELATION_TYPES) | {str(t).strip().lower() for t in extra if str(t).strip()}

# GitHub heading slugs: lowercase, drop everything that is not a word char, space or hyphen,
# then spaces to hyphens. `## Target Market (MiFID)` -> `target-market-mifid`.
SLUG_STRIP_RE = re.compile(r"[^\w\s-]", re.UNICODE)
SLUG_SPACE_RE = re.compile(r"[\s_]+")


def slugify(heading):
    """A GitHub-style anchor slug for a heading."""
    text = SLUG_STRIP_RE.sub("", heading.strip().lower())
    return SLUG_SPACE_RE.sub("-", text).strip("-")


def resolve_target(rel_path, target):
    """A link target as a vault-relative POSIX path, or None if it is not a note edge.

    Resolved relative to the LINKING FILE, not the vault root - `../rules/r.md` from `notes/a.md`
    means `rules/r.md`. Getting this wrong silently points every edge at the wrong node.
    """
    target = target.strip()
    if not target or EXTERNAL_RE.match(target):
        return None
    if not os.path.splitext(target)[1].lower() in NOTE_EXT:
        return None
    base = os.path.dirname(rel_path)
    joined = os.path.normpath(os.path.join(base, target)) if base else os.path.normpath(target)
    if joined.startswith(".."):
        return None
    return joined.replace(os.sep, "/")


def line_relation_type(line, kind, known, unknown):
    """The declared relation type for this line, or the default.

    Only relation sections carry types. An unrecognised type is NOT an error: it degrades to the
    default and is reported, because failing a whole scan over a typo in one note would make every
    other note's edges unavailable to fix it with.
    """
    if kind not in ("related", "see-also"):
        return DEFAULT_RELATION
    match = REL_TYPE_RE.match(line)
    if not match:
        return DEFAULT_RELATION
    declared = match.group("type").lower()
    if declared in known:
        return declared
    if unknown is not None and declared not in unknown:
        unknown.append(declared)
    return DEFAULT_RELATION


def collect_links(rel_path, line, kind, links, known_types=None, unknown=None):
    """Append every note-to-note link on this line."""
    rel_type = line_relation_type(line, kind, known_types or RELATION_TYPES, unknown)
    for match in MD_LINK_RE.finditer(line):
        if len(links) >= MAX_LINKS:
            return
        resolved = resolve_target(rel_path, match.group("target"))
        if resolved is None:
            continue
        links.append({
            "target": resolved,
            "anchor": (match.group("anchor") or "").strip(),
            "kind": kind,
            "rel_type": rel_type,
            "text": match.group("text").strip()[:80],
        })


def is_tag(tag):
    """Whether a string is a well-formed tag path: word-and-hyphen segments, none all digits."""

    if not tag or len(tag) > MAX_TAG_LEN:
        return False
    segments = tag.split(TAG_SEPARATOR)

    return all(TAG_SEGMENT_RE.match(s) and not s.isdigit() for s in segments)


def sort_tag_tokens(raw_tag_text):
    """Split the raw text of a `tags` value into (well-formed tags, malformed tokens).

    The raw text is the key's own value plus any continuation lines, so an inline list, a block
    list and a comma scalar all arrive here as one comma-separated string. Identity is the
    casefolded path, which is how Obsidian matches nested tags.
    """

    tags, bad_tags = [], []
    for token in raw_tag_text.replace("[", ",").replace("]", ",").split(","):
        tag = token.strip().strip("'\"").strip().lstrip("#").casefold()
        if not tag:
            continue
        if not is_tag(tag):
            if tag not in bad_tags:
                bad_tags.append(tag)
        elif tag not in tags and len(tags) < MAX_TAGS:
            tags.append(tag)

    return tags, bad_tags


def parse_front_matter_full(lines):
    """Return (keys, wanted values, index of the first line after the frontmatter block).

    Only TEMPORAL_KEYS and the tags are kept as values. Keeping every value would put arbitrary
    note content into the manifest, which is a routing artifact and not a copy of the vault.
    """
    if not lines or lines[0].strip() != "---":
        return [], {}, 0
    keys, values = [], {}
    current_key, raw_tag_text = "", ""
    for i in range(1, min(len(lines), FRONT_MATTER_MAX_LINES)):
        stripped = lines[i].strip()
        if stripped in ("---", "..."):
            values["tags"], values["bad_tags"] = sort_tag_tokens(raw_tag_text)
            return keys, values, i + 1
        if not stripped or stripped.startswith("#"):
            continue
        is_continuation = stripped.startswith("-") or lines[i].startswith((" ", "\t"))
        if is_continuation:
            # A block list (`- a`) or a wrapped flow list belongs to the key above it.
            if current_key == TAG_KEY:
                raw_tag_text += "," + stripped.lstrip("-")
        elif ":" in stripped:
            key, _, value = stripped.partition(":")
            current_key = key.strip()
            keys.append(current_key)
            if current_key in TEMPORAL_KEYS:
                values[current_key] = value.strip().strip("'\"")[:32]
            elif current_key == TAG_KEY:
                raw_tag_text = value
    return keys, {}, 0


def parse_front_matter(lines):
    """Return (frontmatter keys, index of the first line after the frontmatter block)."""
    keys, _values, body_start = parse_front_matter_full(lines)
    return keys, body_start


def parse_tags(lines):
    """Return (tags, malformed tokens) from a note's lines. No closed frontmatter means no tags."""

    _keys, values, _body_start = parse_front_matter_full(lines)
    tags = values.get("tags", [])
    bad_tags = values.get("bad_tags", [])

    return tags, bad_tags


def parse_tag_inventory(text):
    """The tag tree a vault's inventory lists: {path: {"meaning", "aka"}}, in file order."""

    inventory = {}
    for line in text.splitlines():
        match = TAG_INVENTORY_LINE_RE.match(line.rstrip())
        if not match:
            continue
        rest = match.group("rest") or ""
        aka_match = TAG_AKA_RE.search(rest)
        aka = []
        if aka_match:
            aka = [a.strip().casefold() for a in aka_match.group("aka").split(",") if a.strip()]
            rest = rest[:aka_match.start()]
        inventory[match.group("path").strip().casefold()] = {"meaning": rest.strip(), "aka": aka}

    return inventory


def locate_tag_inventory(root):
    """Where a vault keeps its tag tree. A fixed path, never a parameter."""

    return os.path.join(root, *TAG_INVENTORY_PARTS)


def load_tag_inventory(root):
    """The vault's tag tree, or an empty one when the vault has no inventory file yet."""

    text = read_text(locate_tag_inventory(root))

    return parse_tag_inventory(text) if text else {}


def is_term(token):
    """A glossary candidate looks like a domain acronym: 2+ capitals, not universal vocabulary.

    The token AND its singular are both checked, because `APIs` is `API` and a stoplist that only
    matches exactly is a stoplist with a hole in it exactly the width of the plural `s`.
    """
    if not TWO_CAPS_RE.search(token):
        return False
    singular = PLURAL_RE.sub("", token)
    return token not in STOPLIST and singular not in STOPLIST


def collect_terms(line, acronyms, definitions):
    """Accumulate acronym counts and stated definitions from one prose line."""
    clean = LINK_TARGET_RE.sub(" ", CODE_SPAN_RE.sub(" ", line)).strip()
    if not clean:
        return
    for token in ACRONYM_RE.findall(clean):
        if is_term(token):
            acronyms[token] = acronyms.get(token, 0) + 1
    for pattern in DEFINITION_RES:
        for match in pattern.finditer(clean.lstrip("#> -*")):
            term = match.group("term")
            if is_term(term) and term not in definitions:
                definitions[term] = " ".join(match.group("long").split())[:80]


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(MAX_READ_BYTES)
    except OSError:
        return None


def describe(path, rel, known_types=None):
    """Build one manifest record for a file."""
    try:
        stat = os.stat(path)
    except OSError:
        return None

    record = {
        "path": rel,
        "folder": os.path.dirname(rel) or ".",
        "ext": os.path.splitext(rel)[1].lower(),
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
        "lines": 0,
        "h1": "",
        "h2": [],
        "heading_slugs": [],
        "links": [],
        "frontmatter_keys": [],
        "valid_from": "",
        "valid_until": "",
        "tags": [],
        "bad_tags": [],
        "unknown_relation_types": [],
        "first_line": "",
        "acronyms": {},
        "definitions": {},
        "readable": False,
    }

    if record["ext"] not in TEXT_EXT:
        return record

    text = read_text(path)
    if text is None:
        return record

    record["readable"] = True
    lines = text.splitlines()
    record["lines"] = len(lines)
    fm_keys, fm_values, body_start = parse_front_matter_full(lines)
    record["frontmatter_keys"] = fm_keys
    record["valid_from"] = fm_values.get("valid_from", "")
    record["valid_until"] = fm_values.get("valid_until", "")
    record["tags"] = fm_values.get("tags", [])
    record["bad_tags"] = fm_values.get("bad_tags", [])

    in_fence = False
    acronyms, definitions = {}, {}
    links = []
    unknown_types = []
    known_types = known_types or RELATION_TYPES
    # A see-also.md is nothing but cross-references, so every link in it is that kind. Elsewhere,
    # `## Related` switches the kind for the rest of the file - it is conventionally the last
    # section, and a link under it is a recorded relation rather than a mention in prose.
    see_also = os.path.basename(rel).lower() == "see-also.md"
    link_kind = "see-also" if see_also else "inline"
    for line in lines[body_start:]:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        collect_terms(stripped, acronyms, definitions)
        collect_links(rel, stripped, link_kind, links, known_types, unknown_types)
        if stripped.startswith("# ") and not record["h1"]:
            record["h1"] = stripped[2:].strip()
            record["heading_slugs"].append(slugify(record["h1"]))
        elif stripped.startswith("## "):
            heading = stripped[3:].strip()
            if len(record["h2"]) < MAX_HEADINGS:
                record["h2"].append(heading)
            record["heading_slugs"].append(slugify(heading))
            if not see_also and heading.lower() == "related":
                link_kind = "related"
        elif stripped.startswith("### "):
            record["heading_slugs"].append(slugify(stripped[4:].strip()))
        elif stripped and not record["first_line"] and not stripped.startswith("#"):
            record["first_line"] = stripped[:200]

    record["links"] = links
    record["unknown_relation_types"] = sorted(unknown_types)

    top = sorted(acronyms.items(), key=lambda kv: (-kv[1], kv[0]))[:MAX_ACRONYMS]
    record["acronyms"] = dict(top)
    record["definitions"] = definitions

    return record


def keep_content_dirs(dirnames):
    """The subfolders worth descending into: never the vault's machinery or a build tree."""

    return sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".git"))


def read_head_lines(path):
    """The lines a frontmatter block can occupy, without reading the rest of the note."""

    head = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                head.append(line.rstrip("\n"))
                if len(head) >= FRONT_MATTER_MAX_LINES:
                    break
    except OSError:
        return []

    return head


def walk_tags(root):
    """Every note's tags, read live from the note heads, as two maps keyed by relative path.

    Returns (tags_by_note, bad_tags_by_note); a note with no malformed token has no entry in the
    second. For callers that must not be stale - the consistency check, a re-parent in the middle
    of a run - where the manifest and the graph still describe the vault as of the last scan.
    """

    tags_by_note, bad_tags_by_note = {}, {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = keep_content_dirs(dirnames)
        for name in sorted(filenames):
            if name.startswith(".") or os.path.splitext(name)[1].lower() not in NOTE_EXT:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            tags, bad_tags = parse_tags(read_head_lines(full))
            tags_by_note[rel] = tags
            if bad_tags:
                bad_tags_by_note[rel] = bad_tags

    return tags_by_note, bad_tags_by_note


def walk(root, known_types=None):
    """Yield manifest records for every indexable file under root."""
    records = []
    known_types = known_types or load_relation_types(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = keep_content_dirs(dirnames)
        for name in sorted(filenames):
            ext = os.path.splitext(name)[1].lower()
            if ext not in TEXT_EXT and ext not in OTHER_EXT:
                continue
            if name.startswith("."):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            record = describe(full, rel, known_types)
            if record is not None:
                records.append(record)
    return records


def load_previous(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return {r["path"]: r for r in data.get("files", []) if "path" in r}


def mark_changes(records, previous):
    """Tag each record NEW/CHANGED/UNCHANGED and return records for files that disappeared."""
    seen = set()
    for record in records:
        seen.add(record["path"])
        old = previous.get(record["path"])
        if old is None:
            record["status"] = "NEW"
        elif old.get("mtime") != record["mtime"] or old.get("size") != record["size"]:
            record["status"] = "CHANGED"
        else:
            record["status"] = "UNCHANGED"

    removed = []
    for path, old in previous.items():
        if path not in seen:
            entry = dict(old)
            entry["status"] = "REMOVED"
            removed.append(entry)
    return sorted(removed, key=lambda r: r["path"])


def folder_summary(records):
    """Per-folder file counts, so the index build can decide splits before writing."""
    counts = {}
    for record in records:
        if record.get("status") == "REMOVED":
            continue
        counts[record["folder"]] = counts.get(record["folder"], 0) + 1
    return dict(sorted(counts.items()))


def build_graph(records):
    """Adjacency and its inverse, from the links already collected.

    Deduped per (source, target) pair: three links from one note to another are one relation, and
    the graph answers "what is connected to what". How many times, and via which anchor, stays in
    each record's own `links` list.

    A note with no outbound links gets no `graph` entry, and one nothing points at gets no
    `backlinks` entry - so `graph.py query --orphans` is a set difference rather than a scan for
    empty lists.
    """
    graph = {}
    backlinks = {}
    for record in records:
        if record.get("status") == "REMOVED":
            continue
        source = record["path"]
        seen = set()
        for link in record.get("links", []):
            target = link.get("target")
            if not target or target == source or target in seen:
                continue
            seen.add(target)
            graph.setdefault(source, []).append(target)
            backlinks.setdefault(target, []).append(source)
    for mapping in (graph, backlinks):
        for key in mapping:
            mapping[key] = sorted(set(mapping[key]))
    return dict(sorted(graph.items())), dict(sorted(backlinks.items()))


def glossary_candidates(records):
    """Vault-wide term evidence: how many notes use a term, where it is defined, what it expands to.

    Raw evidence only. references/glossary.md decides which of these earn an entry.
    """
    candidates = {}
    for record in records:
        if record.get("status") == "REMOVED":
            continue
        for term in record.get("acronyms", {}):
            entry = candidates.setdefault(term, {"notes": 0, "uses": 0, "defined_in": [], "long": ""})
            entry["notes"] += 1
            entry["uses"] += record["acronyms"][term]
        for term, long_form in record.get("definitions", {}).items():
            entry = candidates.setdefault(term, {"notes": 0, "uses": 0, "defined_in": [], "long": ""})
            if record["path"] not in entry["defined_in"]:
                entry["defined_in"].append(record["path"])
            if not entry["long"]:
                entry["long"] = long_form
    # Defined terms first, then by how many notes use them: the admission order in glossary.md.
    ordered = sorted(
        candidates.items(),
        key=lambda kv: (not kv[1]["defined_in"], -kv[1]["notes"], kv[0].lower()),
    )
    return {term: data for term, data in ordered if data["defined_in"] or data["notes"] > 1}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scan a notes vault and emit a manifest for the wiki skill.",
    )
    parser.add_argument("--root", required=True, help="Vault root directory to scan")
    parser.add_argument("--out", required=True, help="Path to write the manifest JSON to")
    parser.add_argument(
        "--previous",
        help="Existing manifest to diff against; adds NEW/CHANGED/UNCHANGED/REMOVED status",
    )
    args = parser.parse_args(argv)

    root = os.path.abspath(os.path.expanduser(args.root))
    if not os.path.isdir(root):
        parser.error("--root is not a directory: %s" % root)

    records = walk(root)
    removed = []
    if args.previous:
        previous_path = os.path.abspath(os.path.expanduser(args.previous))
        previous = load_previous(previous_path)
        if previous:
            removed = mark_changes(records, previous)
        else:
            for record in records:
                record["status"] = "NEW"
    else:
        for record in records:
            record["status"] = "NEW"

    graph, backlinks = build_graph(records)
    manifest = {
        "root": root,
        "scanned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_count": len(records),
        "folders": folder_summary(records),
        "glossary_candidates": glossary_candidates(records),
        "tag_inventory": load_tag_inventory(root),
        "graph": graph,
        "backlinks": backlinks,
        "files": records + removed,
    }

    out_path = os.path.abspath(os.path.expanduser(args.out))
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    # Written whole, never appended: the manifest is valid JSON after every run.
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    counts = {}
    for record in manifest["files"]:
        status = record.get("status", "NEW")
        counts[status] = counts.get(status, 0) + 1
    summary = ", ".join("%s %s" % (v, k) for k, v in sorted(counts.items()))
    edges = sum(len(targets) for targets in graph.values())
    print("%d files in %d folders (%s), %d glossary candidates, %d links -> %s"
          % (len(records), len(manifest["folders"]), summary,
             len(manifest["glossary_candidates"]), edges, out_path))

    # Reported, never fatal. A typo in one note's relation type must not cost the whole scan -
    # but it must not pass silently either, or the edge is quietly filed as a generic relation.
    unknown = {}
    for record in records:
        for name in record.get("unknown_relation_types") or []:
            unknown.setdefault(name, []).append(record["path"])
    if unknown:
        print("unrecognised relation type(s), recorded as '%s':" % DEFAULT_RELATION)
        for name in sorted(unknown):
            where = ", ".join(unknown[name][:3])
            more = "" if len(unknown[name]) <= 3 else " (+%d more)" % (len(unknown[name]) - 3)
            print("  %s :: -- %s%s" % (name, where, more))

    # Same policy for tags: one malformed tag must not cost the scan, and must not pass silently.
    malformed = {}
    for record in records:
        for tag in record.get("bad_tags") or []:
            malformed.setdefault(tag, []).append(record["path"])
    if malformed:
        print("malformed tag(s), left out (references/tagging.md -> the grammar):")
        for tag in sorted(malformed):
            where = ", ".join(malformed[tag][:3])
            more = "" if len(malformed[tag]) <= 3 else " (+%d more)" % (len(malformed[tag]) - 3)
            print("  %s -- %s%s" % (tag, where, more))
    return 0


if __name__ == "__main__":
    sys.exit(main())
