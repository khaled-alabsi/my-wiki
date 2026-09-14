#!/usr/bin/env python3
"""The session startup gate, as a tool rather than as prose.

Stdlib only. Four subcommands:

    startup.py --vault <v> check [--json]     the four checks, read-only; prints a verdict
    startup.py --vault <v> register --username X --email Y
    startup.py --vault <v> first-run          install, test, and ONLY then stamp first_run
    startup.py --vault <v> verify --token T   prove `check` returned READY this session

Why a tool and not four paragraphs an agent reads:

  A prose gate is self-reported.  Nothing distinguishes "I ran the four checks" from "I believed I
                                  had". The failure is invisible at the time and unrecoverable
                                  afterwards: a missed registration silently disables attribution
                                  forever, and a missed first-run silently disables retrieval for
                                  the whole session.

  A vague duty loses to a         `check` prints the exact next command for every incomplete gate.
  concrete escape.                The defect this tool was written for: the routine said "install
                                  the RAG dependencies" with no command, while an edge case nearby
                                  offered a well-formed "fall back to grep". The concrete
                                  instruction won, as it always will.

  `first_run` is a claim about    Only `first-run` may stamp it, and only after the install, the
  the machine, not a note.        retrieval test and both tool tests actually passed. A flag flipped
                                  by hand is a lie the next session cannot detect.

The receipt at `.wiki/.startup-receipt.json` is derived state: git-ignored, one object, overwritten
by every `check`. It exists so the closeout checklist can quote a token it did not invent.
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

RECEIPT_NAME = ".startup-receipt.json"
MEMORY_NAME = "memory_local.md"
CONFIG_NAME = "wiki-config.json"
ADMIN_ENTRY_MARKER = "<!-- Admins: add entries below"
REQUIRED_FIELDS = ("username", "email", "user_id", "first_run")

READY = "READY"
BLOCKED = "BLOCKED"

EXIT_OK = 0
EXIT_BLOCKED = 3
EXIT_ERROR = 4


# --------------------------------------------------------------------------- memory file


def memory_path(vault: Path) -> Path:
    return vault / ".wiki" / MEMORY_NAME


def read_memory(vault: Path) -> dict[str, str]:
    """Parse the `key: value` block. Absent file is `{}` — the unregistered case."""
    path = memory_path(vault)
    if not path.is_file():
        return {}
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or line.startswith("-"):
            continue
        match = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def write_memory_field(vault: Path, key: str, value: str) -> None:
    """Set one field in place, preserving everything else. Creates the file if absent."""
    path = memory_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        text = "# Memory — local\n\n\n## Applied remote instructions\n\n## Preferences\n"
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.M)
    if pattern.search(text):
        text = pattern.sub(f"{key}: {value}", text, count=1)
    else:
        text = text.replace("\n\n## Applied remote instructions",
                            f"\n{key}: {value}\n\n## Applied remote instructions", 1)
    path.write_text(text, encoding="utf-8")


def applied_instructions(vault: Path) -> set[str]:
    path = memory_path(vault)
    if not path.is_file():
        return set()
    body = path.read_text(encoding="utf-8")
    section = body.split("## Applied remote instructions", 1)
    if len(section) < 2:
        return set()
    tail = section[1].split("\n## ", 1)[0]
    return set(re.findall(r"\b(RI-\d+)\b", tail))


# --------------------------------------------------------------------------- the four checks


def check_registration(vault: Path) -> dict:
    """Check 1. Repairs a derivable `user_id`; blocks on a missing email."""
    fields = read_memory(vault)
    if not fields:
        return {"ok": False, "detail": "no memory file — unregistered",
                "action": "startup.py register --username <name> --email <email>"}
    missing = [f for f in REQUIRED_FIELDS if f not in fields]
    if "user_id" in missing and fields.get("email"):
        write_memory_field(vault, "user_id", fields["email"])
        missing.remove("user_id")
    if not fields.get("email"):
        return {"ok": False, "detail": "no email, so no user_id — attribution is disabled",
                "action": "ask the user for their email, then startup.py register"}
    if missing:
        return {"ok": False, "detail": f"incomplete: missing {', '.join(missing)}",
                "action": "startup.py register --username <name> --email <email>"}
    return {"ok": True, "detail": f"registered as {fields['user_id']}",
            "user_id": fields["user_id"]}


def rag_state(vault: Path) -> str:
    """`absent` (no workspace), `uninstalled` (no venv), `broken` (venv, dead), `ready`."""
    launcher = vault / ".rag" / "bin" / "rag"
    if not launcher.is_file():
        return "absent"
    if not (vault / ".rag" / ".venv" / "bin" / "python").is_file():
        return "uninstalled"
    try:
        proc = subprocess.run([str(launcher), "status"], cwd=vault,
                              capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return "broken"
    return "ready" if proc.returncode == 0 else "broken"


def check_first_run(vault: Path) -> dict:
    """Check 2. `first_run: done` is a claim about this machine — verify it, don't trust it."""
    fields = read_memory(vault)
    state = rag_state(vault)
    if fields.get("first_run") == "done":
        if state in ("ready", "absent"):
            return {"ok": True, "detail": f"first run done, .rag {state}", "rag": state}
        return {"ok": False, "rag": state,
                "detail": f"first_run says done but .rag is {state} — the flag is stale",
                "action": "startup.py first-run"}
    return {"ok": False, "rag": state,
            "detail": f"first run not done on this machine (.rag {state})",
            "action": "startup.py first-run"}


def check_remote_instructions(vault: Path, skill_dir: Path) -> dict:
    """Check 3. Pending = every `## RI-<n>` in the admin's file this clone has not applied."""
    path = skill_dir / "remote_instructions.md"
    if not path.is_file():
        return {"ok": True, "detail": "no remote instructions file"}
    # Only what follows the admins marker is an entry. Above it the file documents its own format
    # with a worked `## RI-003` example, and a parser that reads the whole file treats the manual
    # as an instruction — sending every contributor to apply a cache rebuild that was never issued.
    body = path.read_text(encoding="utf-8")
    entries = body.split(ADMIN_ENTRY_MARKER, 1)
    if len(entries) < 2:
        return {"ok": True, "detail": "no entry section — nothing issued"}
    issued = set(re.findall(r"^##\s+(RI-\d+)\b", entries[1], re.M))
    pending = sorted(issued - applied_instructions(vault))
    if pending:
        return {"ok": False, "detail": f"pending: {', '.join(pending)}", "pending": pending,
                "action": "apply per references/remote-instructions.md, then record the ids"}
    return {"ok": True, "detail": f"{len(issued)} issued, none pending"}


def check_reorg(vault: Path) -> dict:
    """Check 4. Overdue on age OR on any folder's live note count, whichever comes first.

    Never blocking: an overdue reorg is a question for an admin, not a gate on answering.
    """
    config_path = vault / ".wiki" / CONFIG_NAME
    if not config_path.is_file():
        return {"ok": True, "detail": "no wiki-config.json"}
    config = json.loads(config_path.read_text(encoding="utf-8"))
    stale_days = config.get("reorg_stale_days", 30)
    max_notes = config.get("reorg_folder_notes", 25)
    reasons = []
    last = config.get("last_reorganized_at")
    if last:
        age = (date.today() - date.fromisoformat(last)).days
        if age > stale_days:
            reasons.append(f"{age}d since last reorg (limit {stale_days})")
    for folder in sorted(p for p in vault.iterdir() if p.is_dir()):
        if folder.name.startswith("."):
            continue
        count = len(list(folder.rglob("*.md")))
        if count > max_notes:
            reasons.append(f"{folder.name}/ holds {count} notes (limit {max_notes})")
    if reasons:
        return {"ok": True, "overdue": True, "detail": "; ".join(reasons),
                "action": "ask the user IF their role is admin; otherwise report only"}
    return {"ok": True, "overdue": False, "detail": "not overdue"}


# --------------------------------------------------------------------------- first run


def run_first_run(vault: Path, skill_dir: Path) -> dict:
    """Check 2's remedy: install, index, prove retrieval answers, prove the tools work, then stamp.

    The stamp is last and conditional. A `first_run: done` written before the evidence is a claim
    the next session has no way to doubt, and it disables retrieval silently for everyone after.
    """
    steps: list[dict] = []

    # STEP 1: bring the .rag workspace's dependencies onto this machine
    state = rag_state(vault)
    if state == "absent":
        steps.append({"step": "install", "ok": True, "detail": "no .rag workspace — nothing to install"})
    elif state == "ready":
        steps.append({"step": "install", "ok": True, "detail": "already installed"})
    else:
        installer = vault / ".rag" / "toolkit" / "rag_toolkit" / "install.py"
        proc = subprocess.run([sys.executable, str(installer)], cwd=vault, capture_output=True, text=True)
        steps.append({"step": "install", "ok": proc.returncode == 0,
                      "detail": (proc.stderr or proc.stdout or "").strip().splitlines()[-1:] or ["no output"]})

    # STEP 2: build the index, because dependencies alone cannot answer anything
    launcher = vault / ".rag" / "bin" / "rag"
    if rag_state(vault) == "ready" and not (vault / ".rag" / "db").exists():
        proc = subprocess.run([str(launcher), "index"], cwd=vault, capture_output=True, text=True)
        steps.append({"step": "build index", "ok": proc.returncode == 0,
                      "detail": "index built" if proc.returncode == 0
                      else (proc.stderr or "").strip().splitlines()[-1:] or ["index failed"]})

    # STEP 3: prove retrieval actually ANSWERS. A venv directory is not evidence, and neither is an
    # index directory: a fresh clone reaches this point with both and still returns nothing.
    if rag_state(vault) == "ready":
        proc = subprocess.run([str(launcher), "search", "test", "-k", "1"],
                              cwd=vault, capture_output=True, text=True)
        steps.append({"step": "retrieval test", "ok": proc.returncode == 0,
                      "detail": "search answered" if proc.returncode == 0
                      else (proc.stderr or "").strip().splitlines()[-1:] or ["search failed"]})
    else:
        steps.append({"step": "retrieval test", "ok": rag_state(vault) == "absent",
                      "detail": f".rag is {rag_state(vault)}"})

    # STEP 4: prove this skill's own tools run on this interpreter
    for name in ("test_contributors.py", "test_graph.py"):
        proc = subprocess.run([sys.executable, str(skill_dir / "scripts" / name)],
                              cwd=vault, capture_output=True, text=True)
        steps.append({"step": name, "ok": proc.returncode == 0,
                      "detail": (proc.stdout or "").strip().splitlines()[-1:] or ["no output"]})

    # STEP 5: stamp the flag only when every step above earned it
    is_complete = all(step["ok"] for step in steps)
    if is_complete:
        write_memory_field(vault, "first_run", "done")
    return {"ok": is_complete, "steps": steps}


# --------------------------------------------------------------------------- receipt


def receipt_path(vault: Path) -> Path:
    return vault / ".wiki" / RECEIPT_NAME


def write_receipt(vault: Path, verdict: str, checks: dict) -> str:
    """Derived state, overwritten every `check`. The token is what the closeout must quote."""
    token = f"{date.today().isoformat()}-{secrets.token_hex(4)}"
    receipt_path(vault).write_text(json.dumps({
        "token": token,
        "verdict": verdict,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "checks": {name: result["ok"] for name, result in checks.items()},
    }, indent=2) + "\n", encoding="utf-8")
    return token


# --------------------------------------------------------------------------- commands


CHECK_LABELS = {
    "registration": "1 registration",
    "first_run": "2 first run",
    "remote_instructions": "3 remote instructions",
    "reorg": "4 reorg staleness",
}


def cmd_check(args) -> int:
    vault, skill_dir = Path(args.vault).resolve(), Path(__file__).resolve().parent.parent
    checks = {
        "registration": check_registration(vault),
        "first_run": check_first_run(vault),
        "remote_instructions": check_remote_instructions(vault, skill_dir),
        "reorg": check_reorg(vault),
    }
    verdict = READY if all(result["ok"] for result in checks.values()) else BLOCKED
    token = write_receipt(vault, verdict, checks)
    if args.json:
        print(json.dumps({"verdict": verdict, "token": token, "checks": checks}, indent=2))
    else:
        for name, result in checks.items():
            mark = "ok  " if result["ok"] else "TODO"
            print(f"  [{mark}] {CHECK_LABELS[name]:<24} {result['detail']}")
            if result.get("action"):
                print(f"         -> {result['action']}")
        print(f"\nVERDICT: {verdict}   token: {token}")
        if verdict == BLOCKED:
            print("Do the -> actions above, then run this again. Nothing else starts until READY.")
    return EXIT_OK if verdict == READY else EXIT_BLOCKED


def cmd_register(args) -> int:
    vault = Path(args.vault).resolve()
    for key, value in (("username", args.username), ("email", args.email),
                       ("user_id", args.email), ("role", "contributor")):
        write_memory_field(vault, key, value)
    if "first_run" not in read_memory(vault):
        write_memory_field(vault, "first_run", "")
    print(f"registered {args.email}. Next: startup.py --vault {args.vault} first-run")
    return EXIT_OK


def cmd_first_run(args) -> int:
    vault, skill_dir = Path(args.vault).resolve(), Path(__file__).resolve().parent.parent
    outcome = run_first_run(vault, skill_dir)
    for step in outcome["steps"]:
        print(f"  [{'ok  ' if step['ok'] else 'FAIL'}] {step['step']:<24} {step['detail']}")
    print("\nfirst_run: done" if outcome["ok"] else
          "\nfirst_run left UNSET so it retries next session. Report the failure; fall back to grep.")
    return EXIT_OK if outcome["ok"] else EXIT_BLOCKED


def cmd_verify(args) -> int:
    """Prove a READY verdict exists for today — the closeout's `[x]` needs evidence, not memory."""
    path = receipt_path(Path(args.vault).resolve())
    if not path.is_file():
        print("no receipt: `check` has never run in this vault", file=sys.stderr)
        return EXIT_BLOCKED
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt["token"] != args.token:
        print(f"token mismatch: receipt holds {receipt['token']}", file=sys.stderr)
        return EXIT_BLOCKED
    if receipt["verdict"] != READY:
        print(f"receipt verdict is {receipt['verdict']}, not {READY}", file=sys.stderr)
        return EXIT_BLOCKED
    print(f"verified {args.token} — {READY} at {receipt['at']}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", required=True, help="the vault root")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="run the four checks; exits 3 while any is incomplete")
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=cmd_check)

    register = sub.add_parser("register", help="write this contributor's identity")
    register.add_argument("--username", required=True)
    register.add_argument("--email", required=True, help="becomes user_id verbatim")
    register.set_defaults(func=cmd_register)

    first_run = sub.add_parser("first-run", help="install, test, and stamp first_run if all passed")
    first_run.set_defaults(func=cmd_first_run)

    verify = sub.add_parser("verify", help="prove a READY receipt exists for this token")
    verify.add_argument("--token", required=True)
    verify.set_defaults(func=cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
