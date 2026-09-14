#!/usr/bin/env python3
"""The agent's own memory: what it decided, how that turned out, and what it learned.

Stdlib only. Subcommands:

    memory.py record   --mode update --decision place --target <p> [--alternatives a,b]
                       [--rationale "..."] [--applied-rule RULE-017] [--user-id <email>]
    memory.py close    --id EP-238 --outcome confirmed|corrected [--correction <p>]
    memory.py query    --scope placement [--since 90d] [--limit 20] [--json]
    memory.py stats    [--scope placement] [--json]
    memory.py rules    [--scope placement] [--json]
    memory.py promote  [--dry-run] [--json]
    memory.py rotate

THE separation this exists to keep: the vault holds WORLD knowledge, this holds AGENT knowledge.
A note about how settlement works belongs in the vault. "I filed three notes about mechanisms in
the project folder and the user moved all three" belongs here, and must never leak into the notes -
that is how a knowledge base becomes a diary.

Three storage rules, each of which looks like over-engineering until the vault is two years old:

  episodes.jsonl is APPEND-ONLY and NEVER READ WHOLE. It grows with every decision ever made.
                 `stats` reads the rollup instead - a fixed-size file of counters - and `query`
                 reads a bounded tail. An agent that reads this file is one context window from
                 spending its whole budget on its own history.

  Closing an episode APPENDS a second record. Rewriting the original line would mean rewriting a
                 log that other processes are appending to, which is how logs get truncated.
                 Records are folded on read; the last one about an id wins.

  Rules COMPETE for a fixed number of slots. Eight per scope, so what the agent loads before a
                 decision stays about twelve lines whether the vault holds 16 notes or 5,000. A
                 rule set that grows without a ceiling ends up costing more than it saves.

Promotion is AUTOMATIC at a threshold, which is a deliberate trade: the agent gets better without
being asked, and in exchange every promotion and demotion must be announced in the run's report.
Silent behaviour change is the price of auto-promotion, and the announcement is what pays it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

MEMORY_DIR = Path(".wiki") / "agent-memory"
EPISODES = "episodes.jsonl"
ROLLUP = "episodes-rollup.json"
RULES_DIR = "rules"
RULES_INDEX = "index.md"
DEPRECATED_DIR = "deprecated"
ARCHIVE_DIR = "archive"

SCOPES = ("placement", "linking", "splitting", "glossary", "intake", "answering")
OUTCOMES = ("unknown", "confirmed", "corrected")
STATUSES = ("candidate", "supported", "validated", "canonical", "deprecated")
LOADED_STATUSES = ("validated", "canonical")

# The gate. Numbers, not judgement: a model asked "is this enough evidence" will answer yes.
TO_CANDIDATE_EPISODES = 2
TO_SUPPORTED_EPISODES = 3
TO_VALIDATED_EPISODES = 5
VALIDATION_QUIET_DAYS = 30

# Budgets. See the growth classes in references/agent-memory.md - every file here has one.
SLOTS_PER_SCOPE = 8
QUERY_TAIL_LINES = 500
ROTATE_ABOVE_LINES = 5000

LOCK_STALE_S = 5.0
LOCK_POLL_S = 0.05
LOCK_WAIT_S = 30.0


# --- paths -----------------------------------------------------------------------------------

def memory_dir(vault: Path) -> Path:
    return vault / MEMORY_DIR


def episodes_path(vault: Path) -> Path:
    return memory_dir(vault) / EPISODES


def rollup_path(vault: Path) -> Path:
    return memory_dir(vault) / ROLLUP


def rules_dir(vault: Path) -> Path:
    return memory_dir(vault) / RULES_DIR


def ensure_dirs(vault: Path) -> None:
    for path in (memory_dir(vault), rules_dir(vault), rules_dir(vault) / DEPRECATED_DIR,
                 memory_dir(vault) / ARCHIVE_DIR, memory_dir(vault) / "reflections"):
        path.mkdir(parents=True, exist_ok=True)


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- locking ---------------------------------------------------------------------------------

class FileLock:
    """A lock for the read-modify-write files. Two agents in one vault is a normal Tuesday."""

    def __init__(self, target: Path) -> None:
        self.path = target.with_suffix(target.suffix + ".lock")
        self.held = False

    def __enter__(self) -> "FileLock":
        deadline = time.time() + LOCK_WAIT_S
        while True:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self.held = True
                return self
            except FileExistsError:
                try:
                    age = time.time() - self.path.stat().st_mtime
                except OSError:
                    continue
                if age > LOCK_STALE_S:
                    # A crashed run must not lock the memory forever.
                    try:
                        self.path.unlink()
                    except OSError:
                        pass
                    continue
                if time.time() > deadline:
                    raise TimeoutError(f"could not acquire {self.path} after {LOCK_WAIT_S}s")
                time.sleep(LOCK_POLL_S)

    def __exit__(self, *_exc) -> None:
        if self.held:
            try:
                self.path.unlink()
            except OSError:
                pass


# --- the log ---------------------------------------------------------------------------------

def append_record(vault: Path, record: dict) -> None:
    """One line, opened in append mode. Never a rewrite of the file."""
    ensure_dirs(vault)
    with open(episodes_path(vault), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def tail_lines(path: Path, max_lines: int) -> list[str]:
    """The last N lines, without reading the file into memory.

    This is the only read path into the log, and it is bounded on purpose: the whole point of the
    rollup is that nothing has to scan the history to answer a normal question.
    """
    if not path.exists():
        return []
    if max_lines <= 0:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    block, data, size = 8192, b"", path.stat().st_size
    with open(path, "rb") as fh:
        while size > 0 and data.count(b"\n") <= max_lines:
            step = min(block, size)
            size -= step
            fh.seek(size)
            data = fh.read(step) + data
    return data.decode("utf-8", errors="replace").splitlines()[-max_lines:]


def fold(lines: list[str]) -> dict[str, dict]:
    """Episodes by id, with later `close` records applied over the original."""
    episodes: dict[str, dict] = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue  # a torn line from a killed process is not worth failing a query over
        eid = record.get("id")
        if not eid:
            continue
        if record.get("kind") == "close":
            if eid in episodes:
                episodes[eid].update({k: v for k, v in record.items()
                                      if k not in ("kind", "ts")})
                episodes[eid]["closed_at"] = record.get("ts", "")
        else:
            episodes[eid] = record
    return episodes


def next_id(vault: Path) -> str:
    """EP-N, from the rollup's counter — so it never depends on reading the log."""
    data = read_rollup(vault)
    return f"EP-{data.get('next_id', 1)}"


# --- the rollup ------------------------------------------------------------------------------

def blank_rollup() -> dict:
    return {"version": 1, "next_id": 1, "total": 0, "by_scope": {}, "by_outcome": {},
            "by_rule": {}, "first_ts": "", "last_ts": ""}


def read_rollup(vault: Path) -> dict:
    path = rollup_path(vault)
    if not path.exists():
        return blank_rollup()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return blank_rollup()
    base = blank_rollup()
    base.update(data if isinstance(data, dict) else {})
    return base


def write_rollup(vault: Path, data: dict) -> None:
    ensure_dirs(vault)
    path = rollup_path(vault)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def bump(data: dict, key: str, name: str, delta: int = 1) -> None:
    bucket = data.setdefault(key, {})
    bucket[name] = bucket.get(name, 0) + delta


# --- rules -----------------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_rule(path: Path) -> dict:
    """One rule file. A tiny YAML subset - scalars and inline lists - because a rule file is
    written by this tool and read by an agent, and adding a YAML dependency to a stdlib package
    to parse eight keys would be a poor trade."""
    text = path.read_text(encoding="utf-8", errors="replace")
    match = FRONTMATTER_RE.match(text)
    rule: dict = {"file": str(path), "body": text[match.end():].strip() if match else text.strip()}
    if not match:
        return rule
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith((" ", "\t", "#")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            rule[key] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        elif value in ("null", "~", ""):
            rule[key] = None
        else:
            rule[key] = value.strip("'\"")
    return rule


def load_rules(vault: Path) -> list[dict]:
    directory = rules_dir(vault)
    if not directory.exists():
        return []
    rules = []
    for path in sorted(directory.glob("RULE-*.md")):
        try:
            rules.append(parse_rule(path))
        except OSError:
            continue
    return rules


def write_rule(rule: dict) -> None:
    """Rewrite one rule file's frontmatter, keeping its body untouched.

    The body is the rule as a human wrote it. This tool changes status and evidence; it does not
    rephrase what the rule says, and a tool that edits prose it did not write is a tool nobody
    can trust with a rules directory.
    """
    order = ["id", "scope", "status", "confidence", "evidence", "negative_examples",
             "created_at", "last_validated", "superseded_by"]
    lines = ["---"]
    for key in order:
        if key not in rule:
            continue
        value = rule[key]
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    Path(rule["file"]).write_text("\n".join(lines) + "\n" + rule.get("body", "") + "\n",
                                  encoding="utf-8")


def rule_headline(rule: dict) -> str:
    """The rule as one line. A wrapped paragraph is joined, not truncated at the first newline —
    a rule cut mid-sentence reads as a different rule."""
    paragraph: list[str] = []
    for line in (rule.get("body") or "").splitlines():
        if not line.strip():
            if paragraph:
                break
            continue
        paragraph.append(line.strip())
    text = " ".join(paragraph)
    return (text[:157] + "…") if len(text) > 158 else (text or "(no text)")


def write_rules_index(vault: Path, rules: list[dict]) -> dict:
    """The file the agent loads before deciding. Grouped by scope, capped per scope.

    Loaded BY SCOPE, never whole: an `update` run reads placement and linking and nothing else.
    That is what keeps the cost of memory proportional to corrections rather than to vault size.
    """
    ensure_dirs(vault)
    loaded = [r for r in rules if r.get("status") in LOADED_STATUSES]
    by_scope: dict[str, list[dict]] = {}
    for rule in loaded:
        by_scope.setdefault(rule.get("scope") or "placement", []).append(rule)

    lines = ["# Learned rules — what the agent loads before deciding", "",
             "<!-- Generated by memory.py. Rules are promoted automatically at a threshold and",
             "     every promotion is announced in the run report. Edit a RULE-*.md file, not",
             f"     this index. Cap: {SLOTS_PER_SCOPE} rules per scope. -->", ""]
    evicted = []
    for scope in sorted(by_scope):
        entries = sorted(by_scope[scope],
                         key=lambda r: (-float(r.get("confidence") or 0), r.get("id") or ""))
        if len(entries) > SLOTS_PER_SCOPE:
            # Rules compete. The weakest loses its slot and drops back to `supported` - still
            # true, still evidenced, just no longer worth the tokens on every run.
            for loser in entries[SLOTS_PER_SCOPE:]:
                loser["status"] = "supported"
                write_rule(loser)
                evicted.append(loser["id"])
            entries = entries[:SLOTS_PER_SCOPE]
        lines.append(f"## {scope}")
        for rule in entries:
            lines.append(f"- **{rule['id']}** ({rule.get('confidence', '?')}) — {rule_headline(rule)}")
        lines.append("")
    if not by_scope:
        lines += ["_No rules have been validated yet. This is the normal state of a young vault._",
                  ""]
    (rules_dir(vault) / RULES_INDEX).write_text("\n".join(lines), encoding="utf-8")
    return {"scopes": len(by_scope), "loaded": sum(min(len(v), SLOTS_PER_SCOPE)
                                                   for v in by_scope.values()), "evicted": evicted}


# --- promotion -------------------------------------------------------------------------------

def rule_evidence(rule: dict, rollup: dict) -> tuple[int, int, str]:
    """(support, contradictions, last contradiction date) for one rule.

    Two sources, deliberately: what the tool observed (the rollup's per-rule counters, from runs
    where the rule actually fired) and what `learn` wrote into the file (episode ids it found the
    pattern in). A rule can be evidenced before it has ever been applied, which is the whole point
    of consolidation - otherwise nothing could ever reach the threshold to be used the first time.
    """
    counters = (rollup.get("by_rule") or {}).get(rule.get("id") or "", {})
    listed = len(rule.get("evidence") or [])
    negative = len(rule.get("negative_examples") or [])
    support = counters.get("confirmed", 0) + listed
    contradictions = counters.get("corrected", 0) + negative
    return support, contradictions, counters.get("last_corrected", "")


def days_since(stamp: str) -> float:
    if not stamp:
        return 1e9
    try:
        when = datetime.strptime(stamp[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return 1e9
    return (datetime.now(timezone.utc) - when).total_seconds() / 86400.0


def evaluate(rule: dict, rollup: dict) -> tuple[str, str]:
    """The gate, as arithmetic. Returns (new status, why)."""
    status = rule.get("status") or "candidate"
    if status in ("deprecated", "canonical"):
        return status, ""
    support, against, last_bad = rule_evidence(rule, rollup)

    # A correction is not a vote to be outweighed later in the same run: it stops the rule
    # influencing anything, immediately. Demotion is one level, not straight to the bin - a rule
    # with twenty supports and one correction is a rule to refine, not to throw away.
    if against and against >= support:
        return "deprecated", f"{against} contradiction(s) against {support} support(s)"
    if against and status in LOADED_STATUSES and days_since(last_bad) < VALIDATION_QUIET_DAYS:
        return "supported", f"contradicted {int(days_since(last_bad))} day(s) ago"

    if support >= TO_VALIDATED_EPISODES and (not against
                                             or days_since(last_bad) >= VALIDATION_QUIET_DAYS):
        return "validated", f"{support} supporting episode(s), no recent contradiction"
    if support >= TO_SUPPORTED_EPISODES and not against:
        return "supported", f"{support} supporting episode(s)"
    if support >= TO_CANDIDATE_EPISODES:
        return "candidate", f"{support} supporting episode(s)"
    return status, ""


def cmd_promote(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    rules = load_rules(vault)
    rollup = read_rollup(vault)
    changes = []
    for rule in rules:
        was = rule.get("status") or "candidate"
        now, why = evaluate(rule, rollup)
        if now == was:
            continue
        support, against, _ = rule_evidence(rule, rollup)
        confidence = round(support / max(support + against, 1), 2)
        changes.append({"id": rule.get("id"), "scope": rule.get("scope"), "from": was, "to": now,
                        "why": why, "confidence": confidence, "text": rule_headline(rule)})
        if not args.dry_run:
            rule["status"] = now
            rule["confidence"] = confidence
            rule["last_validated"] = today()
            write_rule(rule)
            if now == "deprecated":
                target = rules_dir(vault) / DEPRECATED_DIR / Path(rule["file"]).name
                target.parent.mkdir(parents=True, exist_ok=True)
                Path(rule["file"]).replace(target)
                rule["file"] = str(target)

    index = {"scopes": 0, "loaded": 0, "evicted": []}
    if not args.dry_run:
        index = write_rules_index(vault, load_rules(vault))
        for lost in index["evicted"]:
            changes.append({"id": lost, "from": "validated", "to": "supported",
                            "why": f"lost its slot ({SLOTS_PER_SCOPE} per scope)",
                            "confidence": None, "text": ""})

    payload = {"changed": changes, "rules": len(rules), "loaded": index["loaded"],
               "dry_run": bool(args.dry_run)}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    if not changes:
        print(f"no status changes ({len(rules)} rule(s), {index['loaded']} loaded)")
        return 1
    verb = "would change" if args.dry_run else "changed"
    print(f"{len(changes)} rule(s) {verb} — announce these in the run report:")
    for change in changes:
        print(f"  {change['id']}  {change['from']} -> {change['to']}  ({change['why']})")
        if change["text"]:
            print(f"      {change['text']}")
    return 0


# --- commands --------------------------------------------------------------------------------

def cmd_record(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    with FileLock(rollup_path(vault)):
        rollup = read_rollup(vault)
        eid = f"EP-{rollup.get('next_id', 1)}"
        record = {
            "id": eid, "ts": now_iso(), "mode": args.mode, "scope": args.scope,
            "decision": args.decision, "target": args.target,
            "alternatives": [a for a in (args.alternatives or "").split(",") if a],
            "rationale": (args.rationale or "")[:300], "applied_rule": args.applied_rule or "",
            "user_id": args.user_id or "", "outcome": "unknown",
        }
        append_record(vault, record)
        rollup["next_id"] = rollup.get("next_id", 1) + 1
        rollup["total"] = rollup.get("total", 0) + 1
        rollup["last_ts"] = record["ts"]
        rollup["first_ts"] = rollup.get("first_ts") or record["ts"]
        bump(rollup, "by_scope", args.scope)
        bump(rollup, "by_outcome", "unknown")
        if args.applied_rule:
            by_rule = rollup.setdefault("by_rule", {}).setdefault(args.applied_rule, {})
            by_rule["applied"] = by_rule.get("applied", 0) + 1
        write_rollup(vault, rollup)
    print(eid if args.quiet else f"recorded {eid}: {args.decision} -> {args.target}")
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    """Close an episode. The correction is the valuable half of the record, not the success."""
    vault = Path(args.vault).resolve()
    known = fold(tail_lines(episodes_path(vault), QUERY_TAIL_LINES))
    episode = known.get(args.id)
    rule = args.rule or (episode or {}).get("applied_rule") or ""
    with FileLock(rollup_path(vault)):
        append_record(vault, {"kind": "close", "id": args.id, "ts": now_iso(),
                              "outcome": args.outcome, "correction": args.correction or "",
                              "applied_rule": rule})
        rollup = read_rollup(vault)
        bump(rollup, "by_outcome", args.outcome)
        bump(rollup, "by_outcome", "unknown", -1)
        if rule:
            by_rule = rollup.setdefault("by_rule", {}).setdefault(rule, {})
            key = "corrected" if args.outcome == "corrected" else "confirmed"
            by_rule[key] = by_rule.get(key, 0) + 1
            if args.outcome == "corrected":
                by_rule["last_corrected"] = today()
        write_rollup(vault, rollup)
    if episode is None:
        print(f"closed {args.id} as {args.outcome} — note: it was not in the recent log, so no "
              f"rule could be credited unless --rule was given")
        return 0
    print(f"closed {args.id} as {args.outcome}" + (f" (rule {rule})" if rule else ""))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    vault = Path(args.vault).resolve()
    episodes = fold(tail_lines(episodes_path(vault), QUERY_TAIL_LINES))
    rows = list(episodes.values())
    if args.scope:
        rows = [r for r in rows if r.get("scope") == args.scope]
    if args.outcome:
        rows = [r for r in rows if r.get("outcome") == args.outcome]
    if args.rule:
        rows = [r for r in rows if r.get("applied_rule") == args.rule]
    if args.since:
        cutoff = parse_since(args.since)
        rows = [r for r in rows if (r.get("ts") or "") >= cutoff]
    rows.sort(key=lambda r: r.get("ts") or "")
    total = len(rows)
    rows = rows[-args.limit:] if args.limit > 0 else rows
    if args.json:
        print(json.dumps({"count": total, "truncated": total > len(rows), "results": rows,
                          "scanned_lines": QUERY_TAIL_LINES}, ensure_ascii=False))
        return 0 if rows else 1
    if not rows:
        print("no episodes match")
        return 1
    print(f"{total} episode(s), showing {len(rows)}:")
    for row in rows:
        mark = {"corrected": "✗", "confirmed": "✓"}.get(row.get("outcome"), "·")
        print(f"  {mark} {row['id']}  {row.get('decision')} -> {row.get('target')}")
        if row.get("outcome") == "corrected" and row.get("correction"):
            print(f"      corrected to {row['correction']}")
    return 0


def parse_since(text: str) -> str:
    match = re.match(r"^(\d+)([dwm])$", text.strip())
    if not match:
        return text[:10]
    count, unit = int(match.group(1)), match.group(2)
    days = count * {"d": 1, "w": 7, "m": 30}[unit]
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")


def cmd_stats(args: argparse.Namespace) -> int:
    """Counters only. This command must never open episodes.jsonl — that is the whole contract."""
    vault = Path(args.vault).resolve()
    rollup = read_rollup(vault)
    rules = load_rules(vault)
    by_status: dict[str, int] = {}
    for rule in rules:
        status = rule.get("status") or "candidate"
        by_status[status] = by_status.get(status, 0) + 1
    payload = {"episodes": rollup.get("total", 0), "by_scope": rollup.get("by_scope", {}),
               "by_outcome": rollup.get("by_outcome", {}), "by_rule": rollup.get("by_rule", {}),
               "rules": by_status, "first": rollup.get("first_ts", ""),
               "last": rollup.get("last_ts", "")}
    if args.scope:
        payload["by_scope"] = {args.scope: payload["by_scope"].get(args.scope, 0)}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    print(f"{payload['episodes']} episode(s) recorded")
    for name, count in sorted(payload["by_outcome"].items()):
        print(f"  {name:<10} {count}")
    if payload["by_scope"]:
        print("by scope: " + ", ".join(f"{k} {v}" for k, v in sorted(payload["by_scope"].items())))
    if by_status:
        print("rules: " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))
    return 0


def cmd_rules(args: argparse.Namespace) -> int:
    """What the agent loads before deciding — one scope at a time, never the whole set."""
    vault = Path(args.vault).resolve()
    rules = [r for r in load_rules(vault) if r.get("status") in LOADED_STATUSES]
    if args.scope:
        rules = [r for r in rules if (r.get("scope") or "placement") == args.scope]
    rules.sort(key=lambda r: (r.get("scope") or "", -float(r.get("confidence") or 0)))
    rules = rules[:SLOTS_PER_SCOPE] if args.scope else rules
    if args.json:
        print(json.dumps([{"id": r.get("id"), "scope": r.get("scope"),
                           "confidence": r.get("confidence"), "text": rule_headline(r)}
                          for r in rules], ensure_ascii=False))
        return 0
    if not rules:
        print("no rules loaded" + (f" for {args.scope}" if args.scope else ""))
        return 1
    for rule in rules:
        print(f"{rule['id']} ({rule.get('scope')}, {rule.get('confidence')}) — {rule_headline(rule)}")
    return 0


def cmd_rotate(args: argparse.Namespace) -> int:
    """Move closed history out of the live log, by quarter. The ledger's eviction rule."""
    vault = Path(args.vault).resolve()
    path = episodes_path(vault)
    if not path.exists():
        print("no episodes yet")
        return 1
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < ROTATE_ABOVE_LINES and not args.force:
        print(f"{len(lines)} line(s) — under the {ROTATE_ABOVE_LINES} threshold, nothing to do")
        return 1
    now = datetime.now(timezone.utc)
    current = f"{now.year}-Q{(now.month - 1) // 3 + 1}"
    keep, buckets = [], {}
    for line in lines:
        try:
            stamp = json.loads(line).get("ts") or ""
            year, month = int(stamp[:4]), int(stamp[5:7])
            quarter = f"{year}-Q{(month - 1) // 3 + 1}"
        except (ValueError, IndexError):
            keep.append(line)
            continue
        if quarter == current:
            keep.append(line)
        else:
            buckets.setdefault(quarter, []).append(line)
    with FileLock(rollup_path(vault)):
        for quarter, rows in buckets.items():
            archive = memory_dir(vault) / ARCHIVE_DIR / f"episodes-{quarter}.jsonl"
            archive.parent.mkdir(parents=True, exist_ok=True)
            with open(archive, "a", encoding="utf-8") as fh:
                fh.write("\n".join(rows) + "\n")
        path.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
    print(f"archived {sum(len(v) for v in buckets.values())} line(s) into "
          f"{len(buckets)} quarter file(s); {len(keep)} line(s) remain live")
    return 0


# --- cli -------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault", default=argparse.SUPPRESS, help="vault root")

    parser = argparse.ArgumentParser(description="The wiki agent's episodic and procedural memory.")
    parser.add_argument("--vault", default=".", help="vault root (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record", parents=[common], help="log one reversible decision")
    record.add_argument("--mode", required=True, help="the mode that made it, e.g. update")
    record.add_argument("--decision", required=True,
                        help="place | split | merge | link | dedupe-skip | new-folder")
    record.add_argument("--target", required=True, help="what it wrote, or would have")
    record.add_argument("--scope", default="placement", choices=SCOPES)
    record.add_argument("--alternatives", help="comma-separated paths it did not choose")
    record.add_argument("--rationale", help="one line: why this one")
    record.add_argument("--applied-rule", help="the learned rule that decided it, if any")
    record.add_argument("--user-id", help="who was running")
    record.add_argument("--quiet", action="store_true", help="print the id and nothing else")
    record.set_defaults(func=cmd_record)

    close = sub.add_parser("close", parents=[common], help="record how a decision turned out")
    close.add_argument("--id", required=True)
    close.add_argument("--outcome", required=True, choices=("confirmed", "corrected"))
    close.add_argument("--correction", help="where it should have gone")
    close.add_argument("--rule", help="credit a rule explicitly, if the episode has aged out")
    close.set_defaults(func=cmd_close)

    query = sub.add_parser("query", parents=[common], help="a bounded look at recent episodes")
    query.add_argument("--scope", choices=SCOPES)
    query.add_argument("--outcome", choices=OUTCOMES)
    query.add_argument("--rule", help="episodes where this rule fired")
    query.add_argument("--since", help="7d, 4w, 3m, or a date")
    query.add_argument("--limit", type=int, default=20)
    query.add_argument("--json", action="store_true")
    query.set_defaults(func=cmd_query)

    stats = sub.add_parser("stats", parents=[common], help="counters — never opens the log")
    stats.add_argument("--scope", choices=SCOPES)
    stats.add_argument("--json", action="store_true")
    stats.set_defaults(func=cmd_stats)

    rules = sub.add_parser("rules", parents=[common], help="the rules loaded for one scope")
    rules.add_argument("--scope", choices=SCOPES)
    rules.add_argument("--json", action="store_true")
    rules.set_defaults(func=cmd_rules)

    promote = sub.add_parser("promote", parents=[common],
                             help="apply the gate; run at the end of every writing run")
    promote.add_argument("--dry-run", action="store_true")
    promote.add_argument("--json", action="store_true")
    promote.set_defaults(func=cmd_promote)

    rotate = sub.add_parser("rotate", parents=[common], help="archive closed quarters")
    rotate.add_argument("--force", action="store_true", help="rotate below the threshold too")
    rotate.set_defaults(func=cmd_rotate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
